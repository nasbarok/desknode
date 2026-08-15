#include "dn_asset.h"

#include <string.h>

#include "dn_pins.h"
#include "esp_log.h"
#include "esp_partition.h"
#include "esp_rom_crc.h"
#include "esp_timer.h"

static const char *TAG = "dn_asset";

#define DN_ASSET_PARTITION_LABEL "assets"
#define DN_ASSET_SUBTYPE 0x40

/*
 * ── LA BANDE-ANNONCE D'INTÉGRITÉ ────────────────────────────────────────────
 *
 * LE DÉFAUT QU'ELLE FERME, et pourquoi il était pire que « pas de checksum ».
 * Ce module refusait bruyamment une partition VIERGE — bonne intention — mais
 * il ne regardait que les 4 096 premiers pixels, soit 8 192 des 614 400 octets
 * de la charge : 1,3 %. Et la seule taille qu'il vérifiait était celle de la
 * PARTITION (1 MiB, fixée par partitions.csv), jamais celle de ce qui y avait
 * réellement été écrit. Conséquence : un binaire TRONQUÉ — flash de la voie A
 * interrompue, disque plein pendant la génération — présentait un début
 * parfaitement valide, passait le test du vierge, et `dn_asset_copy_to`
 * recopiait ensuite les 614 400 octets entiers dont la queue était de la flash
 * jamais écrite. En RGB565, 0xFFFF vaut BLANC : le bas de l'image virait au
 * blanc, en silence. C'est-à-dire EXACTEMENT l'« écran blanc silencieux » que
 * tout ce module se donne du mal à refuser, entré par la porte de derrière.
 *
 * Le générateur colle donc 16 octets après la charge utile (le format est
 * décrit des deux côtés — voir tools/gen_living_pcb.py) :
 *     +0   8 o   magie ASCII « DNASSET1 »
 *     +8   4 o   longueur de la charge utile, uint32 little-endian
 *     +12  4 o   CRC32 de la charge utile, uint32 little-endian
 *
 * ⚠️ VIERGE et CORROMPU sont deux problèmes d'opérateur DIFFÉRENTS, et les
 *    messages ne doivent pas les confondre : « vierge » veut dire « tu n'as
 *    pas flashé l'asset » (rejouer `idf.py flash`), « corrompu » veut dire « le
 *    flash a été fait mais il a mal fini » (le binaire source est peut-être
 *    tronqué lui aussi — regénérer AVANT de reflasher).
 *
 * Le CRC32 est celui de zlib (IEEE 802.3, réfléchi, polynôme 0xEDB88320).
 * `esp_rom_crc32_le()` en est la mise en œuvre exacte : elle inverse l'entrée
 * et la sortie en interne (esp_rom/linux/esp_rom_crc.c:166-173), donc
 * `esp_rom_crc32_le(0, buf, len)` == `zlib.crc32(buf)` sans aucun ajustement.
 */
#define DN_ASSET_MAGIC "DNASSET1"
#define DN_ASSET_MAGIC_LEN 8
#define DN_ASSET_TRAILER_LEN 16
#define DN_ASSET_MAPPED_BYTES (DN_FB_BYTES + (size_t)DN_ASSET_TRAILER_LEN)

static const uint16_t *s_pixels;
static esp_partition_mmap_handle_t s_map;
static int64_t s_last_copy_us = -1;

/* Un uint32 little-endian lu octet par octet : la bande-annonce n'est pas
 * alignée (elle commence à l'octet 614 400, qui n'est multiple que de 4 par
 * chance) et surtout on ne veut dépendre d'aucun boutisme implicite. */
static uint32_t lire_u32_le(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) |
           ((uint32_t)p[3] << 24);
}

/* Annule le mapping et repose l'état « pas d'asset ». Toutes les voies de
 * refus passent par ici : oublier le munmap laisserait une plage MMU réservée
 * pour rien, et un s_pixels non nul ferait croire à un asset utilisable. */
static void asset_refuser(void)
{
    esp_partition_munmap(s_map);
    s_pixels = NULL;
}

esp_err_t dn_asset_init(void)
{
    const esp_partition_t *part = esp_partition_find_first(
        ESP_PARTITION_TYPE_DATA, (esp_partition_subtype_t)DN_ASSET_SUBTYPE,
        DN_ASSET_PARTITION_LABEL);
    if (!part) {
        ESP_LOGE(TAG,
                 "partition « %s » introuvable — la table de partitions "
                 "flashée n'est pas celle de ce projet ?",
                 DN_ASSET_PARTITION_LABEL);
        return ESP_ERR_NOT_FOUND;
    }
    if (part->size < DN_ASSET_MAPPED_BYTES) {
        ESP_LOGE(TAG,
                 "partition « %s » trop petite : %lu o < %u o attendus "
                 "(%u de pixels + %u de bande-annonce)",
                 DN_ASSET_PARTITION_LABEL, (unsigned long)part->size,
                 (unsigned)DN_ASSET_MAPPED_BYTES, (unsigned)DN_FB_BYTES,
                 (unsigned)DN_ASSET_TRAILER_LEN);
        return ESP_ERR_INVALID_SIZE;
    }

    const void *ptr = NULL;
    esp_err_t err = esp_partition_mmap(part, 0, DN_ASSET_MAPPED_BYTES,
                                       ESP_PARTITION_MMAP_DATA, &ptr, &s_map);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "mmap de « %s » refusé : %s", DN_ASSET_PARTITION_LABEL,
                 esp_err_to_name(err));
        return err;
    }
    s_pixels = (const uint16_t *)ptr;

    /* Une partition jamais flashée est pleine de 0xFF. C'est indiscernable
     * d'un asset blanc à l'œil : on le dit ICI plutôt que de laisser l'owner
     * conclure « l'écran affiche du blanc, donc le driver marche ».
     *
     * ⚠️ CE SONDAGE N'EST PLUS LE CONTRÔLE D'INTÉGRITÉ, et c'est important :
     * 4 096 pixels sur 307 200, c'est 1,3 % de la charge, ça n'a jamais pu
     * prouver qu'un fichier était complet, et c'était pourtant tout ce que ce
     * module savait faire. L'intégrité est désormais établie plus bas par la
     * bande-annonce (magie + longueur + CRC32), qui couvre 100 % des octets.
     * Ce test-ci ne sert plus qu'à CLASSER la panne : sans lui, une partition
     * jamais flashée sortirait sous l'étiquette « corrompu » et enverrait
     * l'opérateur régénérer un binaire qui n'a rien. */
    bool vierge = true;
    for (int i = 0; i < 4096; i++) {
        if (s_pixels[i] != 0xFFFF) {
            vierge = false;
            break;
        }
    }
    if (vierge) {
        /* ⚠️ Et on REFUSE de l'utiliser. En RGB565, 0xFFFF vaut BLANC : afficher
         * une partition vierge donnerait un écran blanc plein — indiscernable
         * d'un asset blanc, et parfaitement silencieux. C'est exactement la
         * panne que la voie A produit quand on flashe l'app sans son asset, et
         * la plus coûteuse à diagnostiquer. En renvoyant une erreur ici, la
         * scène `asset` affiche à la place un panneau « ASSET ABSENT ». */
        ESP_LOGE(TAG,
                 "partition « %s » VIERGE (que des 0xFF sur les premiers "
                 "4096 pixels) : l'asset n'a pas été flashé. L'afficher "
                 "donnerait un ÉCRAN BLANC silencieux — refusé. Rejouer "
                 "`idf.py flash`, qui l'écrit via esptool_py_flash_to_partition, "
                 "ou flasher %s à l'offset 0x%06lx par la voie A.",
                 DN_ASSET_PARTITION_LABEL, "build/living_pcb_v0.bin",
                 (unsigned long)part->address);
        asset_refuser();
        return ESP_ERR_NOT_FOUND;
    }

    /* ── Intégrité : magie, longueur, CRC32 ─────────────────────────────────
     * L'ordre compte. Le test du vierge est passé AVANT, exprès : une
     * partition jamais flashée échouerait aussi ici, mais elle sortirait sous
     * l'étiquette « corrompu », ce qui enverrait l'opérateur régénérer un
     * binaire parfaitement sain au lieu de simplement le flasher. */
    const uint8_t *trailer = (const uint8_t *)ptr + DN_FB_BYTES;
    if (memcmp(trailer, DN_ASSET_MAGIC, DN_ASSET_MAGIC_LEN) != 0) {
        ESP_LOGE(TAG,
                 "asset CORROMPU (magie absente) : attendu « %s » à l'offset "
                 "%u, lu %02X %02X %02X %02X %02X %02X %02X %02X. Le binaire "
                 "flashé est TRONQUÉ, ou il a été produit par une version du "
                 "générateur antérieure à la bande-annonce. Regénérer "
                 "(tools/gen_living_pcb.py) PUIS reflasher — refusé plutôt "
                 "que d'afficher une image dont la queue serait du blanc.",
                 DN_ASSET_MAGIC, (unsigned)DN_FB_BYTES, trailer[0], trailer[1],
                 trailer[2], trailer[3], trailer[4], trailer[5], trailer[6],
                 trailer[7]);
        asset_refuser();
        return ESP_ERR_INVALID_CRC;
    }

    uint32_t len_annoncee = lire_u32_le(trailer + DN_ASSET_MAGIC_LEN);
    if (len_annoncee != (uint32_t)DN_FB_BYTES) {
        ESP_LOGE(TAG,
                 "asset CORROMPU (longueur) : la bande-annonce déclare %lu o "
                 "de pixels, le firmware en attend %u (480 x 640 x 2). "
                 "L'asset et le panneau ne parlent pas de la même géométrie.",
                 (unsigned long)len_annoncee, (unsigned)DN_FB_BYTES);
        asset_refuser();
        return ESP_ERR_INVALID_SIZE;
    }

    uint32_t crc_attendu = lire_u32_le(trailer + DN_ASSET_MAGIC_LEN + 4);
    int64_t t_crc = esp_timer_get_time();
    uint32_t crc_lu = esp_rom_crc32_le(0, (const uint8_t *)ptr, DN_FB_BYTES);
    t_crc = esp_timer_get_time() - t_crc;
    if (crc_lu != crc_attendu) {
        ESP_LOGE(TAG,
                 "asset CORROMPU (CRC32) : calculé 0x%08lX, annoncé 0x%08lX. "
                 "La magie et la longueur sont bonnes, donc le fichier a la "
                 "bonne TAILLE mais pas le bon CONTENU — écriture flash "
                 "partielle, ou secteur abîmé. Reflasher.",
                 (unsigned long)crc_lu, (unsigned long)crc_attendu);
        asset_refuser();
        return ESP_ERR_INVALID_CRC;
    }

    ESP_LOGI(TAG,
             "asset mappé : offset 0x%06lx, %u o utiles sur %lu o de partition, "
             "@ %p",
             (unsigned long)part->address, (unsigned)DN_FB_BYTES,
             (unsigned long)part->size, (const void *)s_pixels);
    /* Le temps du CRC est journalisé parce qu'il se paie AU BOOT, à chaque
     * démarrage, et qu'il lit les 614 400 octets à travers le cache flash : ce
     * chiffre est aussi une mesure du chemin flash->CPU, à comparer au
     * flash->PSRAM que `bw` produit. */
    ESP_LOGI(TAG,
             "intégrité VÉRIFIÉE : magie « %s », %lu o, CRC32 0x%08lX "
             "(calculé en %lld us)",
             DN_ASSET_MAGIC, (unsigned long)len_annoncee,
             (unsigned long)crc_lu, (long long)t_crc);
    return ESP_OK;
}

const uint16_t *dn_asset_pixels(void) { return s_pixels; }

esp_err_t dn_asset_copy_to(uint16_t *dst)
{
    if (!s_pixels || !dst) {
        return ESP_ERR_NOT_FOUND;
    }
    int64_t t0 = esp_timer_get_time();
    memcpy(dst, s_pixels, DN_FB_BYTES);
    s_last_copy_us = esp_timer_get_time() - t0;
    return ESP_OK;
}

int64_t dn_asset_last_copy_us(void) { return s_last_copy_us; }

void dn_asset_log(void)
{
    if (!s_pixels) {
        ESP_LOGW(TAG, "asset non mappé");
        return;
    }
    if (s_last_copy_us > 0) {
        /* 614 400 octets lus en flash + écrits en PSRAM. Le débit affiché est
         * celui du COUPLE flash->PSRAM, pas de la PSRAM seule : c'est un
         * plancher, pas la bande passante PSRAM pure. */
        double mo_s = (double)DN_FB_BYTES / (double)s_last_copy_us;
        ESP_LOGI(TAG,
                 "dernière copie de trame pleine : %lld us pour %u o "
                 "=> %.1f Mo/s (flash mmap -> PSRAM)",
                 (long long)s_last_copy_us, (unsigned)DN_FB_BYTES, mo_s);
        ESP_LOGI(TAG,
                 "  budget : tenir 37,40 Hz impose de redessiner une trame en "
                 "moins de 26,7 ms — ici %.1f ms.",
                 (double)s_last_copy_us / 1000.0);
    } else {
        ESP_LOGI(TAG, "asset mappé, aucune copie encore mesurée");
    }
}

#include "dn_asset.h"

#include <string.h>

#include "dn_pins.h"
#include "esp_log.h"
#include "esp_partition.h"
#include "esp_timer.h"

static const char *TAG = "dn_asset";

#define DN_ASSET_PARTITION_LABEL "assets"
#define DN_ASSET_SUBTYPE 0x40

static const uint16_t *s_pixels;
static esp_partition_mmap_handle_t s_map;
static int64_t s_last_copy_us = -1;

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
    if (part->size < DN_FB_BYTES) {
        ESP_LOGE(TAG, "partition « %s » trop petite : %lu o < %u o attendus",
                 DN_ASSET_PARTITION_LABEL, (unsigned long)part->size,
                 (unsigned)DN_FB_BYTES);
        return ESP_ERR_INVALID_SIZE;
    }

    const void *ptr = NULL;
    esp_err_t err = esp_partition_mmap(part, 0, DN_FB_BYTES,
                                       ESP_PARTITION_MMAP_DATA, &ptr, &s_map);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "mmap de « %s » refusé : %s", DN_ASSET_PARTITION_LABEL,
                 esp_err_to_name(err));
        return err;
    }
    s_pixels = (const uint16_t *)ptr;

    /* Une partition jamais flashée est pleine de 0xFF. C'est indiscernable
     * d'un asset blanc à l'œil : on le dit ICI plutôt que de laisser l'owner
     * conclure « l'écran affiche du blanc, donc le driver marche ». */
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
        esp_partition_munmap(s_map);
        s_pixels = NULL;
        return ESP_ERR_NOT_FOUND;
    }

    ESP_LOGI(TAG,
             "asset mappé : offset 0x%06lx, %u o utiles sur %lu o de partition, "
             "@ %p",
             (unsigned long)part->address, (unsigned)DN_FB_BYTES,
             (unsigned long)part->size, (const void *)s_pixels);
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

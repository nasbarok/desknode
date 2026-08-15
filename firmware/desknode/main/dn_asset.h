/*
 * DeskNode — l'asset Living PCB v0, lu depuis la partition `assets`.
 *
 * POURQUOI UNE PARTITION ET PAS `EMBED_FILES` (décision de Task 4.3) :
 *   `EMBED_FILES` place les 614 400 octets en `.rodata`. Or AC6 va activer
 *   CONFIG_SPIRAM_XIP_FROM_PSRAM, dont l'option `SPIRAM_RODATA` fait RECOPIER
 *   le .rodata en PSRAM au démarrage. On paierait donc 600 Ko de temps de boot
 *   et 600 Ko de PSRAM — et surtout on BROUILLERAIT la mesure XIP d'AC6, qui
 *   est justement censée chiffrer ce coût-là.
 *   Une partition de données `mmap`ée, elle, est lue directement depuis la
 *   flash à travers le cache : rien n'est recopié au boot.
 *
 * Le binaire est flashé automatiquement par `idf.py flash`, via
 * `esptool_py_flash_to_partition(flash "assets" ...)` dans le CMakeLists.
 * Il n'y a donc AUCUN offset à retenir ni à taper à la main.
 *
 * FORMAT DU BINAIRE : 614 400 octets de pixels RGB565 little-endian, SUIVIS
 * d'une bande-annonce de 16 octets (magie « DNASSET1 », longueur uint32 LE,
 * CRC32 uint32 LE de la charge utile). Le producteur est
 * tools/gen_living_pcb.py ; le format est décrit en entier des deux côtés, et
 * un asset qui ne le respecte pas est REFUSÉ — voir dn_asset.c.
 */
#pragma once

#include <stdint.h>

#include "esp_err.h"

/*
 * Mappe la partition ET vérifie l'asset. À appeler une fois, avant tout
 * dn_asset_copy_to(). Refuse, en distinguant les deux cas dans le log :
 *   - ESP_ERR_NOT_FOUND    : partition absente, ou VIERGE (jamais flashée) ;
 *   - ESP_ERR_INVALID_CRC  : présente mais CORROMPUE (magie ou CRC32 faux) ;
 *   - ESP_ERR_INVALID_SIZE : partition trop petite, ou longueur déclarée
 *                            incompatible avec la géométrie du panneau.
 * Dans tous ces cas s_pixels reste NULL et la scène `asset` affiche le panneau
 * « ASSET ABSENT » — jamais un écran blanc silencieux.
 */
esp_err_t dn_asset_init(void);

/* Pointeur direct sur les pixels mappés (NULL si absent). */
const uint16_t *dn_asset_pixels(void);

/* Copie l'asset dans `dst` (307 200 pixels). Renvoie ESP_ERR_NOT_FOUND si
 * dn_asset_init() a refusé l'asset — absent, vierge ou corrompu — plutôt que
 * de recopier une trame dont on ne sait rien. Jamais d'écran noir, ni blanc,
 * silencieux. */
esp_err_t dn_asset_copy_to(uint16_t *dst);

/* Durée de la dernière copie, en microsecondes. C'EST ICI que se prend le
 * premier chiffre de bande passante du projet (Task 4.4) — dn_display.h a un
 * temps annoncé le sien, dn_display_blit(), qui n'a jamais eu d'appelant et a
 * été supprimé. L'autre instrument de la Task est la commande `bw`, qui fait
 * son propre chronométrage sur les trois chemins de copie. */
int64_t dn_asset_last_copy_us(void);

void dn_asset_log(void);

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
 */
#pragma once

#include <stdint.h>

#include "esp_err.h"

/* Mappe la partition. À appeler une fois, avant tout dn_asset_copy_to(). */
esp_err_t dn_asset_init(void);

/* Pointeur direct sur les pixels mappés (NULL si absent). */
const uint16_t *dn_asset_pixels(void);

/* Copie l'asset dans `dst` (307 200 pixels). Renvoie ESP_ERR_NOT_FOUND si la
 * partition est absente ou vide — jamais un écran noir silencieux. */
esp_err_t dn_asset_copy_to(uint16_t *dst);

/* Durée de la dernière copie, en microsecondes (Task 4.4 : le premier chiffre
 * de bande passante PSRAM du projet). */
int64_t dn_asset_last_copy_us(void);

void dn_asset_log(void);

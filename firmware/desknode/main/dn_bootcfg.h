/*
 * DeskNode — configuration lue AU BOOT, modifiable depuis la console.
 *
 * Pourquoi ce détour par NVS plutôt qu'un #define ?
 *   AC4/AC5 demandent la MÊME mesure dans plusieurs configurations de
 *   framebuffer. Recompiler entre chaque variante donnerait des binaires
 *   différents — donc une variable de plus qu'on ne contrôle pas. Ici, un seul
 *   binaire, une valeur relue au boot : `set fbs 2` puis `reboot`, et le
 *   framebuffer est réalloué proprement à froid, sans fragmentation héritée de
 *   la configuration précédente.
 *
 * Ce qui NE passe PAS par ici, parce que c'est du Kconfig et que ça impose de
 * reconstruire : CONFIG_SPIRAM_XIP_FROM_PSRAM (AC6) et
 * CONFIG_LCD_RGB_RESTART_IN_VSYNC (AC5).
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include "esp_err.h"

typedef struct {
    int num_fbs;   /* 1, 2 ou 3 — `num_fbs` du panneau RGB */
    int bounce_px; /* 0 = pas de bounce buffer ; sinon taille en pixels */
} dn_bootcfg_t;

/* Charge la configuration depuis NVS. Toute valeur absente ou aberrante
 * retombe sur le défaut, et le fait est journalisé — un défaut silencieux
 * fausserait une mesure sans qu'on le sache. */
esp_err_t dn_bootcfg_load(dn_bootcfg_t *out);

esp_err_t dn_bootcfg_set_num_fbs(int num_fbs);
esp_err_t dn_bootcfg_set_bounce_px(int bounce_px);

/* Efface la configuration : le prochain boot repart sur les défauts. */
esp_err_t dn_bootcfg_reset(void);

void dn_bootcfg_log(const dn_bootcfg_t *cfg);

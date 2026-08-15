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
#include "dn_pins.h"
#include "esp_err.h"

typedef struct {
    int num_fbs;   /* 1, 2 ou 3 — `num_fbs` du panneau RGB */
    int bounce_px; /* 0 = pas de bounce buffer ; sinon taille en pixels */
} dn_bootcfg_t;

/*
 * PLAFOND du bounce buffer — et il est DUR, parce que le dépasser BRIQUE la
 * carte. Le mécanisme, de bout en bout :
 *   le driver RGB alloue DEUX bounce buffers de `bounce_px * 2` octets chacun,
 *   en MALLOC_CAP_INTERNAL|MALLOC_CAP_DMA. `set bounce 153600` passait tous les
 *   contrôles (positif, et diviseur exact des 307 200 pixels d'une trame) et
 *   réclamait donc ~614 Ko là où il reste ~348 Ko de RAM interne libre :
 *     ESP_ERR_NO_MEM -> ESP_ERROR_CHECK dans app_main -> panique -> et comme
 *     CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y, le CPU est HALTÉ.
 *   La console n'a alors JAMAIS démarré : plus une seule commande pour annuler
 *   la valeur fautive. Et dn_bootcfg_load() la relisait telle quelle au boot
 *   suivant — le piège se réarmait tout seul, jusqu'au reflash complet.
 *
 * Pourquoi 38 400 px : la plus grosse valeur réellement mesurée par la story
 * est 19 200 px ; 38 400 laisse le double de marge tout en plafonnant à
 * 2 × 76 800 o de RAM interne, ce que la carte a. C'est aussi le dernier
 * diviseur « utile » listé par l'aide de `set bounce` (80 lignes).
 */
#define DN_BOUNCE_PX_MAX (DN_LCD_TOTAL_PX / 8) /* 38 400 px = 76 800 o/tampon */

/* Charge la configuration depuis NVS. Toute valeur absente ou aberrante
 * retombe sur le défaut, et le fait est journalisé — un défaut silencieux
 * fausserait une mesure sans qu'on le sache. */
esp_err_t dn_bootcfg_load(dn_bootcfg_t *out);

esp_err_t dn_bootcfg_set_num_fbs(int num_fbs);
esp_err_t dn_bootcfg_set_bounce_px(int bounce_px);

/* Efface la configuration : le prochain boot repart sur les défauts. */
esp_err_t dn_bootcfg_reset(void);

void dn_bootcfg_log(const dn_bootcfg_t *cfg);

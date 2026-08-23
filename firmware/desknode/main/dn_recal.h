/*
 * DeskNode — recalage DMA déclenché par L'ÉVÉNEMENT de bascule (story dn1-3, AC5).
 *
 * ── LE PROBLÈME HÉRITÉ DE dn1-2, EN UNE PHRASE ───────────────────────────────
 * Sur ESP32-S3, `num_fbs=2` et `CONFIG_LCD_RGB_RESTART_IN_VSYNC=y` sont
 * INCOMPATIBLES : la relance par VBlank repart toujours du lien DMA soudé à
 * `dma_fb_links[0]` à l'init (esp_lcd_panel_rgb.c:1135 et :1187,
 * RGB_LCD_NEEDS_SEPARATE_RESTART_LINK vaut 1 sur S3), alors que `draw_bitmap` ne
 * réaccroche que la QUEUE des liens (:713). Résultat MESURÉ sur 7 scènes à
 * l'œil : toutes les bascules vers fb[0] échouent, toutes celles vers fb[1]
 * passent — et rien, côté logiciel, ne le signale (`draw_bitmap` rend ESP_OK).
 *
 * ── LES 6 PARADES DÉJÀ ÉLIMINÉES — ne pas les rejouer ────────────────────────
 * Toutes consignées au §4 bis de hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md.
 * La n°3 est celle qui compte : un `dma` manuel tapé PLUSIEURS SECONDES après la
 * bascule recale ET garde le bon tampon, dans les deux sens. La parade MARCHE ;
 * c'est le MOMENT de son déclenchement qui manquait. Un délai fixe de 30 ms
 * (parade n°5) ne suffisait pas.
 *
 * ── CE QUE CE MODULE FAIT ────────────────────────────────────────────────────
 * Il remplace le délai fixe par un COMPTAGE D'ÉVÉNEMENTS : après une bascule
 * réussie, attendre N retours verticaux, puis appeler
 * `esp_lcd_rgb_panel_restart()`. Une tâche dédiée, réveillée par sémaphore depuis
 * l'ISR vsync — JAMAIS de restart ni de log dans l'ISR (cache désactivé sous
 * CONFIG_LCD_RGB_ISR_IRAM_SAFE=y).
 *
 * ⚠️ POURQUOI PAS `on_frame_buf_complete`, qui semblerait plus juste : sur cette
 *    puce il ne signifie PAS « le tampon est libéré ». La sémantique de bascule
 *    de lien GDMA n'existe que sous SOC_AXI_GDMA_SUPPORTED, que l'ESP32-S3 ne
 *    définit pas ; ici le callback arrive du trans-EOF, et Espressif écrit dans
 *    cette branche même : « once the preload has already done, the buffer
 *    complete callback is not reliable ». Il peut être OBSERVÉ à titre de
 *    comparaison, il ne peut pas être le VERROU. Détail : dn_measure.h.
 *
 * 🔴 AMENDE LE 2026-08-24 (revue de code 3 couches, dn4-10) — « INERTE SOUS LA
 *    CONFIGURATION LIVREE » EST FAUX, ET C'EST UN RENVERSEMENT COMPLET.
 *    La configuration livree EST `n` depuis `4734d07`. `dn_recal` n'est plus une
 *    branche d'essai : il est devenu PORTEUR DE L'IMAGE DROITE AU BOOT — sans
 *    l'armement de `desknode_main.c:363`, l'image sort decalee en permanence.
 *    ⛔ MAIS C'EST UN ONE-SHOT : les deux autres appelants de `dn_recal_arm()`
 *    sont inatteignables a `num_fbs = 1` (`dn_display.c:715` sous `num_fbs > 1`,
 *    `dn_ui.c:1671` sous `s_direct_mode`). ⇒ aucune parade automatique au
 *    decalage PERMANENT. Decision owner du 2026-08-24 : la brancher sur la
 *    famine averee. ⛔ Le paragraphe ci-dessous n'est pas efface : il dit
 *    pourquoi le module a dormi jusqu'ici.
 *
 * ⚠️ INERTE SOUS LA CONFIGURATION LIVRÉE. `esp_lcd_rgb_panel_restart()` ne fait
 *    que poser `need_restart`, un bit que le driver ne LIT PAS quand
 *    CONFIG_LCD_RGB_RESTART_IN_VSYNC=y. Mesurer AC5 impose donc une BRANCHE
 *    D'ESSAI : rebâtir avec ce symbole à `n`. `dn_recal_log_etat()` le dit au
 *    boot plutôt que de laisser croire à un recalage qui n'a pas lieu.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"
#include "esp_lcd_types.h"

/* Nombre de VSYNC à laisser passer après la bascule avant de relancer la DMA.
 * 0 = recalage DÉSACTIVÉ. Le plafond est bas EXPRÈS : AC5 borne l'investigation
 * à la piste identifiée plus une variante de timing, pas à une spirale d'essais. */
#define DN_RECAL_VSYNCS_MAX 4
#define DN_RECAL_VSYNCS_DEFAUT 1

esp_err_t dn_recal_init(esp_lcd_panel_handle_t panel);

/* Signale qu'une bascule de framebuffer vient d'aboutir. Appelée depuis
 * dn_display_present(), et SEULEMENT quand num_fbs > 1 : à un seul framebuffer
 * il n'y a pas de bascule, donc rien à recaler. Ne bloque pas. */
void dn_recal_arm(void);

/* 0 désactive. Renvoie ESP_ERR_INVALID_ARG hors de [0, DN_RECAL_VSYNCS_MAX]. */
esp_err_t dn_recal_set_vsyncs(int vsyncs);
int dn_recal_get_vsyncs(void);

/* Compteurs 32 BITS — délibérément, pas 64 : le résiduel connu de dn1-2 est que
 * les compteurs 64 bits inter-cœurs ne sont pas atomiques sur Xtensa (`volatile`
 * ne découpe pas un int64), et qu'AUCUNE décision ne doit reposer dessus. Un
 * uint32 aligné, lui, se lit et s'écrit d'un seul accès. */
uint32_t dn_recal_count(void);      /* recalages effectivement joués */
uint32_t dn_recal_rate(void);       /* armements perdus (le précédent courait encore) */
uint32_t dn_recal_last_err(void);   /* esp_err_t du dernier restart, 0 = ESP_OK */

void dn_recal_log_etat(void);

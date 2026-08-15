/*
 * DeskNode — pipeline d'affichage : I²C -> TCA9554 -> 3-wire SPI -> ST7701S ->
 * panneau RGB -> framebuffer(s) PSRAM.
 *
 * L'ORDRE compte, et il n'est pas négociable :
 *   1. bus I²C            (sinon l'expander est injoignable)
 *   2. expander TCA9554   (sinon LCD_RST et LCD_CS n'existent pas)
 *   3. reset matériel de la dalle VIA l'expander
 *   4. bus 3-wire SPI (CS passe par l'expander)
 *   5. panneau ST7701S + RGB, avec la séquence VENDEUR
 *   6. remplissage du framebuffer
 *   7. ET SEULEMENT ALORS le rétroéclairage
 * Allumer le rétroéclairage avant l'étape 6 donne un flash blanc ou un champ de
 * bruit au boot — et on doute du driver alors que c'est l'ordre des opérations.
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "dn_bootcfg.h"
#include "esp_err.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_types.h"

/* Monte tout le pipeline SAUF le rétroéclairage. */
esp_err_t dn_display_init(const dn_bootcfg_t *cfg);

/* Rétroéclairage : GPIO direct, tout ou rien. La gradation est dn1-3. */
esp_err_t dn_display_backlight(bool on);
bool dn_display_backlight_state(void);

/*
 * Sortie d'affichage de la dalle : commande 0x29 / 0x28 sur le bus 3-wire.
 * ⚠️ NE PAS CONFONDRE AVEC LE RÉTROÉCLAIRAGE. Les deux éteignent l'écran, mais
 *    pas de la même façon :
 *      - rétroéclairage OFF  => dalle NOIRE ;
 *      - DISPON OFF          => dalle GRISE, uniformément éclairée, sans image.
 *    C'est le second cas qui a coûté le premier allumage de cette story.
 */
esp_err_t dn_display_disp_on(bool on);
bool dn_display_disp_state(void);

esp_lcd_panel_handle_t dn_display_panel(void);

/* Nombre de framebuffers RÉELLEMENT alloués par le driver. */
int dn_display_num_fbs(void);
size_t dn_display_bounce_px(void);

/*
 * Buffer dans lequel dessiner la prochaine image.
 *   - num_fbs == 1 : c'est le framebuffer VISIBLE. Écrire dedans pendant que la
 *     DMA le lit est exactement le témoin positif du tearing (AC5).
 *   - num_fbs >= 2 : c'est le framebuffer caché ; dn_display_present() le rend
 *     visible par simple bascule d'index, sans recopie.
 */
uint16_t *dn_display_draw_buffer(void);

/*
 * Rend visible ce qui vient d'être dessiné (bascule + synchronisation de
 * cache). Retourne la durée de l'opération en microsecondes.
 *
 * ⚠️ RETOURNE -1 SI LA BASCULE A ÉCHOUÉ, et dans ce cas l'index de dessin
 *    n'avance PAS : le buffer rendu par dn_display_draw_buffer() reste le même
 *    et la dalle garde la trame précédente. Une durée négative est impossible,
 *    donc un appelant qui imprime ce retour comme une mesure affiche un chiffre
 *    reconnaissable au lieu d'une valeur plausible mais fausse.
 */
int64_t dn_display_present(void);

/*
 * Relance la DMA du panneau (parade au décalage permanent quand elle décroche).
 *
 * ⚠️ RENVOIE ESP_ERR_NOT_SUPPORTED — SANS RIEN FAIRE — quand le firmware est
 *    bâti avec CONFIG_LCD_RGB_RESTART_IN_VSYNC=y, ce qui est le cas du
 *    sdkconfig retenu. Le bit posé par esp_lcd_rgb_panel_restart() n'est alors
 *    jamais lu par le driver, qui relance déjà à chaque VBlank. Le détail, avec
 *    les lignes d'ESP-IDF qui le prouvent, est dans dn_display.c.
 */
esp_err_t dn_display_restart(void);

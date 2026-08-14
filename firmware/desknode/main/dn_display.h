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

/* Rend visible ce qui vient d'être dessiné (bascule + synchronisation de
 * cache). Retourne la durée de l'opération en microsecondes. */
int64_t dn_display_present(void);

/* Recopie `src` (307 200 pixels RGB565) dans le buffer de dessin puis présente.
 * Retourne la durée de la COPIE seule, en microsecondes — c'est le premier
 * chiffre de bande passante PSRAM du projet (Task 4.4). */
int64_t dn_display_blit(const uint16_t *src);

/* Relance la DMA du panneau (parade au décalage permanent quand elle décroche). */
esp_err_t dn_display_restart(void);

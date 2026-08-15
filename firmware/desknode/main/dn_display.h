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
#include "driver/i2c_master.h"
#include "esp_err.h"
#include "esp_io_expander.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_types.h"

/* Monte tout le pipeline SAUF le rétroéclairage. */
esp_err_t dn_display_init(const dn_bootcfg_t *cfg);

/*
 * ── LES DEUX ACCESSEURS DE dn1-4, ET POURQUOI ILS EXISTENT ───────────────────
 *
 * ⛔ IL N'Y A QU'UN SEUL BUS I²C SUR CETTE CARTE, et il appartient à ce module.
 *    Le TCA9554 (0x20), le GT911 (0x5D/0x14), la RTC (0x51), l'IMU (0x6A/0x6B)
 *    et le header externe des 4 capteurs de dn2-1 sont TOUS dessus. Un second
 *    `i2c_new_master_bus()` sur I2C_NUM_0 échoue (ESP_ERR_INVALID_STATE) : le
 *    port est déjà pris. Tout module qui veut parler à un composant du bus
 *    demande le handle ICI.
 *
 * Rendent NULL tant que `dn_display_init()` n'a pas tourné — un appelant qui les
 * lit trop tôt obtient un pointeur nul franc, pas un handle à moitié construit.
 */
i2c_master_bus_handle_t dn_display_i2c_bus(void);
esp_io_expander_handle_t dn_display_expander(void);

/*
 * Séquence de reset du GT911, jouée SUR L'EXPANDER (TP_RST = bit 1).
 *
 * Elle vit ici et pas dans dn_touch parce que c'est ce module qui possède
 * l'expander, et parce que le bit d'à côté (bit 0) est LCD_RST : se tromper d'un
 * rang réinitialise la DALLE sans le moindre message d'erreur (piège n°2 du
 * projet). Un seul endroit écrit sur ces bits.
 *
 * ⚠️ CE QU'ELLE NE FAIT PAS : elle ne touche pas à TP_INT. Le niveau d'INT au
 *    RELÂCHEMENT de TP_RST est ce qui latche l'adresse I²C du GT911 (bas =>
 *    0x5D, haut => 0x14) — c'est donc l'appelant (dn_touch) qui tient INT au
 *    niveau voulu autour de cet appel. Découper autrement rendrait cette
 *    dépendance invisible, et l'adresse « aléatoire ».
 *
 * `bas_ms` / `haut_ms` sont exposés pour que la campagne de mesure puisse jouer
 * d'autres délais que ceux de la démo Waveshare (150/150) sans reflasher.
 */
esp_err_t dn_display_tp_reset(int bas_ms, int haut_ms);

/*
 * Rétroéclairage — GRADABLE depuis dn1-3 (AC7).
 *
 * GPIO6 est piloté par LEDC (canal 0, timer 0, LEDC_LOW_SPEED_MODE, 10 bits à
 * 24 kHz — PAS les 5 kHz du pattern d'Espressif : mesuré, à 5 kHz la carte
 * SIFFLE à duty bas, voir le bloc DN_BL_LEDC_FREQ_HZ dans dn_display.c). Ce
 * n'est plus un gpio_set_level : `bl 40` a un sens.
 *
 * ⚠️ CE QUI RESTE INCHANGÉ, ET QUI N'EST PAS NÉGOCIABLE : le duty vaut 0 dès
 *    l'init (la carte ne doit pas hériter de la luminosité du firmware
 *    précédent), et il ne monte qu'APRÈS que le framebuffer porte une image.
 *    L'inverse donne un flash blanc au boot — voir l'en-tête de ce fichier.
 *
 * ⚠️ L'ombre logicielle (`dn_display_backlight_pct_state`) ne suit le matériel
 *    qu'APRÈS confirmation. Un échec LEDC laisse l'état ANCIEN, pas l'état
 *    demandé : sinon la console annoncerait une luminosité que la dalle n'a
 *    jamais prise, et on irait chercher la panne du côté de la dalle.
 */
esp_err_t dn_display_backlight_pct(int pct); /* 0..100, bornes VALIDÉES */
int dn_display_backlight_pct_state(void);

/*
 * Rampe douce entre le niveau courant et `pct_cible`, en `duree_ms`.
 * Bloquante (elle appelle vTaskDelay) : c'est un GESTE D'OPÉRATEUR, joué depuis
 * la console pour le constat à l'œil d'AC7, pas un effet de fond.
 */
esp_err_t dn_display_backlight_ramp(int pct_cible, int duree_ms);

/*
 * Fréquence PWM du rétroéclairage, réglable À CHAUD.
 *
 * Elle existe parce que la valeur du pattern de référence d'Espressif — 5 kHz —
 * a été DÉMENTIE par l'oreille de l'owner le 2026-08-15 : à 3 % de duty, la
 * carte SIFFLE, et l'image papillote. Le commentaire d'origine annonçait
 * « sifflement inaudible en pratique » ; c'était une prédiction reprise d'un
 * BSP générique, pas une mesure sur CETTE carte.
 *
 * 5 kHz tombe en plein dans la bande où l'oreille est la plus sensible. Monter
 * au-dessus de ~18 kHz sort du spectre audible pour un adulte. Le plafond est
 * imposé par le produit (fréquence x 2^résolution) que l'horloge de la source
 * LEDC peut tenir : à 10 bits et 80 MHz d'APB, la limite théorique est ~78 kHz.
 * On borne bien en dessous, et le driver refuse de lui-même ce qu'il ne peut pas.
 */
esp_err_t dn_display_backlight_freq(int hz);
int dn_display_backlight_freq_state(void);

/* Façade booléenne héritée de dn1-2 : `false` -> 0 %, `true` -> 100 %.
 * Conservée parce que la discipline de boot et la commande `bl on|off` la
 * lisent — et parce qu'un appelant qui ne veut pas choisir un pourcentage ne
 * doit pas être forcé d'en inventer un. */
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

/*
 * DeskNode — séquence d'initialisation VENDEUR du ST7701S de cette dalle.
 *
 * ─── PROVENANCE (Task 0.1 de la story dn1-2) ──────────────────────────────
 *   Dépôt   : github.com/bundoon/Waveshare-ESP32-S3Touch-LCD-2.8B-Display-
 *             Working-with-ESPHome
 *   Fichier : working_st7701s_template.yaml, clé `init_sequence:`
 *   Révision: branche `main`, récupérée le 2026-08-14
 *   Origine amont revendiquée par ce dépôt : extraction du driver C Waveshare
 *             de cette carte exacte (ESP32-S3-Touch-LCD-2.8B, 480x640).
 *   Marqueur : la séquence commence par FF 77 01 00 00 13, la sélection de
 *             Command2 BK3 propre au ST7701S.
 *
 * ─── POURQUOI ON NE PREND PAS CELLE DU DRIVER ─────────────────────────────
 *   `esp_lcd_st7701` embarque un jeu d'init GÉNÉRIQUE (480x480). Le dépôt
 *   communautaire ci-dessus documente que c'est précisément là que tout le
 *   monde se casse les dents : « the core issue lies in finding the exact,
 *   vendor-specific initialization sequence required by the display panel ».
 *   On transcrit, on n'espère pas s'en passer.
 *
 * ─── CE QUE LE DRIVER ENVOIE AVANT CETTE TABLE ────────────────────────────
 *   `panel_st7701_send_init_cmds()` émet lui-même, AVANT de dérouler cette
 *   table : FF 77 01 00 00 00 (sortie de Command2), puis MADCTL (0x36) et
 *   COLMOD (0x3A) déduits de `rgb_ele_order` et `bits_per_pixel`.
 *   C'est pourquoi cette table ne contient ni 0x36 ni 0x3A — les y remettre
 *   ferait doublon et le driver les intercepterait.
 *
 * 45 commandes. Deux temporisations sont dans la séquence elle-même :
 * 200 ms après SLPOUT (0x11) et 150 ms au milieu du réglage E8 de BK3.
 */
#pragma once

#include <stdint.h>
#include "esp_lcd_st7701.h"

static const st7701_lcd_init_cmd_t dn_st7701_vendor_init[] = {
    /* ── Command2 BK3 : déverrouillage ──────────────────────────────────── */
    {0xFF, (uint8_t[]){0x77, 0x01, 0x00, 0x00, 0x13}, 5, 0},
    {0xEF, (uint8_t[]){0x08}, 1, 0},

    /* ── Command2 BK0 : résolution, sens de balayage, gamma ─────────────── */
    {0xFF, (uint8_t[]){0x77, 0x01, 0x00, 0x00, 0x10}, 5, 0},
    {0xC0, (uint8_t[]){0x4F, 0x00}, 2, 0}, /* LNESET : 0x4F+1 = 80 lignes x8 = 640 */
    {0xC1, (uint8_t[]){0x10, 0x02}, 2, 0}, /* PORCTRL : VBP / VFP */
    {0xC2, (uint8_t[]){0x07, 0x02}, 2, 0}, /* INVSEL */
    {0xCC, (uint8_t[]){0x10}, 1, 0},
    {0xB0,
     (uint8_t[]){0x00, 0x10, 0x17, 0x0D, 0x11, 0x06, 0x05, 0x08, 0x07, 0x1F,
                 0x04, 0x11, 0x0E, 0x29, 0x30, 0x1F},
     16, 0}, /* gamma positif */
    {0xB1,
     (uint8_t[]){0x00, 0x0D, 0x14, 0x0E, 0x11, 0x06, 0x04, 0x08, 0x08, 0x20,
                 0x05, 0x13, 0x13, 0x26, 0x30, 0x1F},
     16, 0}, /* gamma négatif */

    /* ── Command2 BK1 : tensions d'alimentation du panneau ──────────────── */
    {0xFF, (uint8_t[]){0x77, 0x01, 0x00, 0x00, 0x11}, 5, 0},
    {0xB0, (uint8_t[]){0x65}, 1, 0}, /* VOP */
    {0xB1, (uint8_t[]){0x71}, 1, 0}, /* VCOM */
    {0xB2, (uint8_t[]){0x82}, 1, 0}, /* VGH */
    {0xB3, (uint8_t[]){0x80}, 1, 0},
    {0xB5, (uint8_t[]){0x42}, 1, 0}, /* VGL */
    {0xB7, (uint8_t[]){0x85}, 1, 0}, /* PWCTRL1 */
    {0xB8, (uint8_t[]){0x20}, 1, 0}, /* PWCTRL2 */
    {0xC0, (uint8_t[]){0x09}, 1, 0},
    {0xC1, (uint8_t[]){0x78}, 1, 0},
    {0xC2, (uint8_t[]){0x78}, 1, 0},
    {0xD0, (uint8_t[]){0x88}, 1, 0},
    {0xEE, (uint8_t[]){0x42}, 1, 0},

    /* ── Réglages GIP (pilotage des grilles de la dalle) ────────────────── */
    {0xE0, (uint8_t[]){0x00, 0x00, 0x02}, 3, 0},
    {0xE1,
     (uint8_t[]){0x04, 0xA0, 0x06, 0xA0, 0x05, 0xA0, 0x07, 0xA0, 0x00, 0x44,
                 0x44},
     11, 0},
    {0xE2,
     (uint8_t[]){0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x00, 0x00},
     12, 0},
    {0xE3, (uint8_t[]){0x00, 0x00, 0x22, 0x22}, 4, 0},
    {0xE4, (uint8_t[]){0x44, 0x44}, 2, 0},
    {0xE5,
     (uint8_t[]){0x0C, 0x90, 0xA0, 0xA0, 0x0E, 0x92, 0xA0, 0xA0, 0x08, 0x8C,
                 0xA0, 0xA0, 0x0A, 0x8E, 0xA0, 0xA0},
     16, 0},
    {0xE6, (uint8_t[]){0x00, 0x00, 0x22, 0x22}, 4, 0},
    {0xE7, (uint8_t[]){0x44, 0x44}, 2, 0},
    {0xE8,
     (uint8_t[]){0x0D, 0x91, 0xA0, 0xA0, 0x0F, 0x93, 0xA0, 0xA0, 0x09, 0x8D,
                 0xA0, 0xA0, 0x0B, 0x8F, 0xA0, 0xA0},
     16, 0},
    {0xEB, (uint8_t[]){0x00, 0x00, 0xE4, 0xE4, 0x44, 0x00, 0x40}, 7, 0},
    {0xED,
     (uint8_t[]){0xFF, 0xF5, 0x47, 0x6F, 0x0B, 0xA1, 0xAB, 0xFF, 0xFF, 0xBA,
                 0x1A, 0xB0, 0xF6, 0x74, 0x5F, 0xFF},
     16, 0},
    {0xEF, (uint8_t[]){0x08, 0x08, 0x08, 0x40, 0x3F, 0x64}, 6, 0},

    /* ── Sortie de Command2, puis retour en BK3 pour la séquence de réveil ─ */
    {0xFF, (uint8_t[]){0x77, 0x01, 0x00, 0x00, 0x00}, 5, 0},
    {0xFF, (uint8_t[]){0x77, 0x01, 0x00, 0x00, 0x13}, 5, 0},
    {0xE6, (uint8_t[]){0x16, 0x7C}, 2, 0},
    {0xE8, (uint8_t[]){0x00, 0x0E}, 2, 0},
    {0xFF, (uint8_t[]){0x77, 0x01, 0x00, 0x00, 0x00}, 5, 0},

    /* ── Réveil ─────────────────────────────────────────────────────────── */
    /* ⚠️ Les 200 ms après SLPOUT ne sont pas décoratives : sans elles, la
     *    dalle reste sombre alors que tout le reste a l'air correct. */
    {0x11, NULL, 0, 200}, /* SLPOUT */
    {0xFF, (uint8_t[]){0x77, 0x01, 0x00, 0x00, 0x13}, 5, 0},
    {0xE8, (uint8_t[]){0x00, 0x0C}, 2, 150},
    {0xE8, (uint8_t[]){0x00, 0x00}, 2, 0},
    {0xFF, (uint8_t[]){0x77, 0x01, 0x00, 0x00, 0x00}, 5, 0},
    {0x35, (uint8_t[]){0x00}, 1, 0}, /* TEON — pas de broche TE câblée ici, mais
                                      * la séquence vendeur le fait ; on ne
                                      * retire rien qu'on n'ait pas mesuré. */
};

#define DN_ST7701_VENDOR_INIT_LEN \
    (sizeof(dn_st7701_vendor_init) / sizeof(dn_st7701_vendor_init[0]))

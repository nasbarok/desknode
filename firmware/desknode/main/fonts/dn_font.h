/*
 * DeskNode — les polices embarquées. GÉNÉRÉ PAR `tools/gen_font_dn.py`.
 * ⛔ NE PAS ÉDITER À LA MAIN : le prochain passage du générateur l'écrase.
 *
 * ── POURQUOI CES POLICES REMPLACENT LES BUILT-INS (dn3-1) ────────────────────
 *
 * `lv_font_montserrat_14/_28` sont générées avec `-r 0x20-0x7F,0xB0,0x2022`
 * (relu dans l'en-tête de leur `.c`, pas supposé) : ASCII + le signe degré + la
 * puce + les 61 symboles, ET RIEN D'AUTRE. « RÉSEAU », « HUMIDITÉ », « AOÛT » y
 * perdent leur lettre accentuée EN SILENCE — LVGL ne dessine pas un glyphe
 * absent et ne se plaint pas.
 *
 * `dn_font_14` / `dn_font_28` couvrent 0x20-0x7F,0xA0-0xFF,0x2022 :
 * ASCII + LATIN-1 COMPLET + la puce + les 61 symboles LV_SYMBOL_* + 7
 * icônes FontAwesome. Elles sont donc un SUR-ENSEMBLE STRICT des built-ins.
 *
 * ⚠️ `lv_font_montserrat_14` reste compilée : elle est aussi `LV_FONT_DEFAULT`
 *    (`CONFIG_LV_FONT_DEFAULT_MONTSERRAT_14=y`) et le Kconfig de LVGL 9.5
 *    n'offre AUCUN choix « police personnalisée » pour ce réglage (relu dans
 *    `Kconfig:991-1040`). La désactiver exigerait de patcher le composant managé,
 *    qui est gitignoré et régénéré : le correctif ne survivrait pas au premier
 *    `idf.py reconfigure`. On paie donc ses octets DÉLIBÉRÉMENT, et c'est écrit.
 * ⚠️ `lv_font_montserrat_28`, elle, est DÉSACTIVÉE : rien d'autre ne s'en sert.
 *
 * ── LES ICÔNES ───────────────────────────────────────────────────────────────
 * Aucun asset image : `dn_asset` ne gère QU'UN asset et la partition `assets`
 * n'a que ~434 Ko libres, que dn3-3 réclame déjà. Les icônes sont des GLYPHES,
 * pris dans le `FontAwesome5-Solid+Brands+Regular.woff` déjà présent dans
 * l'arbre — zéro asset, zéro dépendance neuve.
 *
 * 🔴 `0xF863` (`fan`) est ABSENT de ce `.woff` : il est arrivé en FontAwesome
 *    5.11, le fichier embarqué est antérieur. VÉRIFIÉ le 2026-08-17 en le
 *    convertissant seul (`lv_font_conv` échoue bruyamment sur un codepoint
 *    absent), pas déduit d'une table. Le substitut retenu pour VENTILOS est
 *    `sync-alt` — deux flèches en rotation, qui disent « ça tourne » là où
 *    `wind` (0xF72E) dit « ça souffle » et où `cogs` (0xF085) dit « engrenage ».
 *
 * Reproduction :  python3 tools/gen_font_dn.py
 * La ligne de commande exacte est dans l'en-tête de chaque `.c` généré.
 * Licences : `managed_components/lvgl__lvgl/scripts/built_in_font/font_license/`.
 */
#pragma once

#include "lvgl.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ASCII + latin-1 complet + puce + 61 symboles + icônes. */
LV_FONT_DECLARE(dn_font_14)
LV_FONT_DECLARE(dn_font_28)

/* Les icônes, en UTF-8 prêt à concaténer dans un littéral de chaîne.
 * GÉNÉRÉES depuis le même dictionnaire que la police : une macro ne peut pas
 * pointer un codepoint que la police n'aurait pas. */
#define DN_ICONE_TINT                "\xEF\x81\x83" /* U+F043 tint */
#define DN_ICONE_DESKTOP             "\xEF\x84\x88" /* U+F108 desktop */
#define DN_ICONE_THERMOMETER_HALF    "\xEF\x8B\x89" /* U+F2C9 thermometer-half */
#define DN_ICONE_MICROCHIP           "\xEF\x8B\x9B" /* U+F2DB microchip */
#define DN_ICONE_SYNC_ALT            "\xEF\x8B\xB1" /* U+F2F1 sync-alt */
#define DN_ICONE_MEMORY              "\xEF\x94\xB8" /* U+F538 memory */
#define DN_ICONE_NETWORK_WIRED       "\xEF\x9B\xBF" /* U+F6FF network-wired */

#ifdef __cplusplus
}
#endif

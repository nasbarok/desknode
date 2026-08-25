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
 * ASCII + LATIN-1 COMPLET + la puce + les 60 symboles LV_SYMBOL_* UNIQUES
 * + 11 icônes FontAwesome, dont 3 sont DÉJÀ des symboles ⇒
 * 8 codepoints neufs, et 68 au `-r` FontAwesome final. Elles sont
 * donc un SUR-ENSEMBLE STRICT des built-ins.
 * ⚠️ « 61 » est le nombre d'entrées BRUTES de la liste amont — elle contient un
 *    DOUBLON (61452 deux fois), d'où 60 uniques. Ces nombres sont
 *    CALCULÉS à la génération, plus récités : cinq endroits du dépôt en
 *    annonçaient trois valeurs différentes, aucune juste (revue du 2026-08-18).
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
 *    absent), pas déduit d'une table.
 *
 * 🔴 L'ICÔNE DE LA CASE 4 EST LA DISQUETTE `save` (0xF0C7), tranchée par DÉCISION
 *    OWNER le 2026-08-18 (« icône disquette ») EN MÊME TEMPS QUE LE RENOMMAGE
 *    `VENTILOS` -> `DISQUE` : la case a changé de métrique (tr/min -> Mo/s), donc
 *    d'icône. Elle est GRATUITE — 0xF0C7 est DÉJÀ l'un des 60 codepoints de
 *    symboles que `built_in_font_gen.py` injecte : union `-r` inchangée à 68
 *    glyphes, delta = 0, les deux `.c` de police BIT-IDENTIQUES.
 *    ⚠️ Vérifié DANS LES `.c` PRODUITS avec `codepoints_du_c()`, ⛔ jamais par un
 *    test de bornes — c'est ce test-là qui avait fait croire `fan` présent.
 *
 * 📜 HISTORIQUE DE CETTE LIGNE — ELLE A MENTI DEUX FOIS, ET C'EST LA MÊME CAUSE.
 *    · jusqu'au 2026-08-17 elle annonçait `sync-alt`, alors que le descripteur
 *      disait autre chose ;
 *    · corrigée en `cog` le 2026-08-18… et re-fausse le jour même, parce que la
 *      story dn4-1 a changé l'icône POUR `save` sans toucher `ENTETE_MODELE`.
 *    🔴 LA CAUSE N'EST PAS L'ÉTOURDERIE, C'EST L'ENDROIT : `dn_font.h` est
 *    GÉNÉRÉ, donc toute correction faite dans le `.h` est effacée à la
 *    régénération suivante. ⛔ CE TEXTE SE CORRIGE **ICI**, dans
 *    `tools/gen_font_dn.py`, JAMAIS dans `main/fonts/dn_font.h`.
 *    ⚠️ Et il décrit un CHOIX D'AFFICHAGE, qui vit dans `dn_ui.c` (`k_desc[].icone`)
 *    et dans `k_icones_alt[]` : ce fichier ne peut que le RECOPIER, donc il
 *    re-divergera. La seule vraie parade serait de ne pas le recopier du tout.
 *    (Relevé en revue de code le 2026-08-18, DEUXIÈME occurrence.)
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

/* ASCII + latin-1 complet + puce + 60 symboles + 11 icônes. */
LV_FONT_DECLARE(dn_font_14)
LV_FONT_DECLARE(dn_font_28)

/*
 * ── dn3-3 : LES DEUX POLICES DE LA VEILLE ────────────────────────────────────
 *
 * 🔴 PLAGE RÉDUITE `0x20-0x7F,0xB0` — ⛔ NI accents latin-1, NI puce, NI aucun
 *    des 61 symboles LVGL, NI aucune icône FontAwesome. En Ambient le titre,
 *    l'icône et le libellé de grandeur DISPARAISSENT (décision owner du
 *    2026-08-25) : il ne reste que des valeurs, donc des chiffres, des unités,
 *    le « -- » de l'absence et le signe degré.
 * ⛔ NE JAMAIS s'en servir pour du texte d'interface : un accent, une puce ou un
 *    `LV_SYMBOL_*` n'y est PAS, et LVGL ne dessinerait RIEN — sans un mot.
 *    `dn_font_14` / `dn_font_28` restent les polices de l'interface.
 *
 * 🔴 LES DEUX TAILLES SONT MESURÉES SUR LA CARTE, ⛔ PAS CHOISIES ROND
 *    (`widget largeur`, 2026-08-25, case de 225 px dont 201 utiles) :
 *      · `dn_font_33` — AVEC l'unité. Pire cas « 2999,9 Mb/s » = 168 px à
 *        28 px ⇒ plafond 33,5 px.
 *      · `dn_font_56` — SANS l'unité. Pire cas « 2999,9 » = 90 px à 28 px
 *        ⇒ plafond 62,5 px, ramené à 56 pour garder ~10 % de marge.
 *    ⚠️ Le pire cas THÉORIQUE de la table du firmware est « c.max 100,0 % » =
 *       197 px, ce qui plafonnerait à 28,6 px — mais il porte un LIBELLÉ, et
 *       les libellés disparaissent en Ambient. C'est CE fait qui débloque
 *       l'agrandissement.
 */
LV_FONT_DECLARE(dn_font_33)
LV_FONT_DECLARE(dn_font_56)

/* Les icônes, en UTF-8 prêt à concaténer dans un littéral de chaîne.
 * GÉNÉRÉES depuis le même dictionnaire que la police : une macro ne peut pas
 * pointer un codepoint que la police n'aurait pas. */
#define DN_ICONE_COG                 "\xEF\x80\x93" /* U+F013 cog */
#define DN_ICONE_TINT                "\xEF\x81\x83" /* U+F043 tint */
#define DN_ICONE_COGS                "\xEF\x82\x85" /* U+F085 cogs */
#define DN_ICONE_SAVE                "\xEF\x83\x87" /* U+F0C7 save */
#define DN_ICONE_DESKTOP             "\xEF\x84\x88" /* U+F108 desktop */
#define DN_ICONE_THERMOMETER_HALF    "\xEF\x8B\x89" /* U+F2C9 thermometer-half */
#define DN_ICONE_MICROCHIP           "\xEF\x8B\x9B" /* U+F2DB microchip */
#define DN_ICONE_SYNC_ALT            "\xEF\x8B\xB1" /* U+F2F1 sync-alt */
#define DN_ICONE_MEMORY              "\xEF\x94\xB8" /* U+F538 memory */
#define DN_ICONE_NETWORK_WIRED       "\xEF\x9B\xBF" /* U+F6FF network-wired */
#define DN_ICONE_WIND                "\xEF\x9C\xAE" /* U+F72E wind */

#ifdef __cplusplus
}
#endif

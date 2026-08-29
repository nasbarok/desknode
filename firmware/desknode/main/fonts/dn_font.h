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
 * + 14 icônes FontAwesome, dont 6 sont DÉJÀ des symboles ⇒
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
 * 🔴 DEUX CODEPOINTS SONT ABSENTS DE CE `.woff`, ET C'EST UN FAIT DE POLICE :
 *    `0xF863` (`fan`) et `0xF390` (`display`). Les deux sont arrivés en
 *    FontAwesome >= 5.11 ; le fichier embarqué est antérieur. VÉRIFIÉS en les
 *    convertissant SEULS (`lv_font_conv` échoue bruyamment sur un codepoint
 *    absent : « doesn't have any characters included in range … »), ⛔ jamais
 *    déduits d'une table.
 *    ⚠️ CES DEUX ÉCHECS SONT L'INSTRUMENT DE CONTRÔLE DU DÉPÔT : avant
 *    d'adopter un codepoint, on le convertit seul ET on re-tire l'un de ces
 *    deux-là. S'il ne rate pas, la sonde ne prouve rien. (LVGL ne dessine pas
 *    un glyphe absent et NE SE PLAINT PAS — c'est la classe de défaut
 *    « l'étiquette qui ment », transposée aux glyphes.)
 *
 * ⛔ CE FICHIER NE DIT PLUS QUELLE CASE PORTE QUELLE ICÔNE — dn4-14 / AC8.3.
 *    Ce `.h` DÉCRIT LA POLICE : ses plages, ses comptes CALCULÉS, et ce qui est
 *    absent du `.woff`. Il ne décrit PAS ce que `dn_ui.c` fait de ses glyphes.
 *    📜 POURQUOI CETTE RÈGLE EXISTE — CETTE PLACE A MENTI TROIS FOIS :
 *      · jusqu'au 2026-08-17 elle annonçait `sync-alt` quand le descripteur
 *        disait autre chose ;
 *      · corrigée en `cog` le 2026-08-18… et re-fausse LE JOUR MÊME, parce que
 *        dn4-1 a changé l'icône pour `save` sans toucher le modèle ;
 *      · et dn4-14 change TROIS choix d'icône d'un coup (la maison d'AMBIANCE,
 *        les six candidats GPU, le retrait des quatre morts) : la garder aurait
 *        fabriqué le mensonge une TROISIÈME fois, mécaniquement.
 *    🔴 LA CAUSE N'ÉTAIT PAS L'ÉTOURDERIE, C'ÉTAIT L'ENDROIT. Un choix
 *    d'affichage vit dans `dn_ui.c` (`k_desc[].icone`, `k_icones_alt[]`) ; ce
 *    fichier ne pouvait que le RECOPIER, sans qu'aucune compilation ne s'en
 *    plaigne, et la régénération le réimprimait tel quel. La seule vraie parade
 *    était de NE PAS LE RECOPIER DU TOUT — c'est fait.
 *    ⇒ Pour savoir quelle case porte quoi : `dn_ui.c`, ou `widget` à la console.
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

/* ASCII + latin-1 complet + puce + 60 symboles + 14 icônes. */
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
#define DN_ICONE_FILM                "\xEF\x80\x88" /* U+F008 film */
#define DN_ICONE_HOME                "\xEF\x80\x95" /* U+F015 home */
#define DN_ICONE_IMAGE               "\xEF\x80\xBE" /* U+F03E image */
#define DN_ICONE_TINT                "\xEF\x81\x83" /* U+F043 tint */
#define DN_ICONE_SAVE                "\xEF\x83\x87" /* U+F0C7 save */
#define DN_ICONE_BOLT                "\xEF\x83\xA7" /* U+F0E7 bolt */
#define DN_ICONE_DESKTOP             "\xEF\x84\x88" /* U+F108 desktop */
#define DN_ICONE_GAMEPAD             "\xEF\x84\x9B" /* U+F11B gamepad */
#define DN_ICONE_CUBE                "\xEF\x86\xB2" /* U+F1B2 cube */
#define DN_ICONE_THERMOMETER_HALF    "\xEF\x8B\x89" /* U+F2C9 thermometer-half */
#define DN_ICONE_MICROCHIP           "\xEF\x8B\x9B" /* U+F2DB microchip */
#define DN_ICONE_MEMORY              "\xEF\x94\xB8" /* U+F538 memory */
#define DN_ICONE_NETWORK_WIRED       "\xEF\x9B\xBF" /* U+F6FF network-wired */
#define DN_ICONE_VR_CARDBOARD        "\xEF\x9C\xA9" /* U+F729 vr-cardboard */

#ifdef __cplusplus
}
#endif

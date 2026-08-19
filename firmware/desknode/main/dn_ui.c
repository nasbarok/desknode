#include "dn_ui.h"

#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>

#include "dn_asset.h"
#include "dn_capteurs.h"
#include "dn_display.h"
#include "dn_link.h"
#include "dn_measure.h"
#include "dn_pins.h"
#include "dn_recal.h"
#include "dn_rtc.h"
#include "dn_touch.h"
#include "dn_widget.h"
#include "fonts/dn_font.h"
#include "esp_cache.h"
#include "esp_check.h"
#include "esp_heap_caps.h"
#include "esp_lcd_panel_ops.h"
#include "esp_log.h"
#include "esp_lvgl_port.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "dn_ui";

/* ── Géométrie du label vivant ────────────────────────────────────────────── */
/*
 * LARGEUR FIXE, et c'est une exigence d'AC2, pas une préférence esthétique.
 * `lv_label_set_text()` invalide la zone du label ; si cette zone changeait avec
 * la longueur du texte (« 9 s » puis « 10 s »), l'aire flushée mesurée par AC3
 * varierait pour une raison qui n'a rien à voir avec le rendu, et un texte plus
 * long pourrait déclencher un relayout du parent — donc une invalidation bien
 * plus grande, une fois sur dix. Largeur figée + LV_LABEL_LONG_MODE_CLIP :
 * l'aire invalidée est la même à chaque mise à jour, quoi qu'on écrive.
 */
#define DN_UI_LABEL_W 260
#define DN_UI_LABEL_H 44

/* Barre du stimulus adverse : verticale, pleine hauteur, qui balaie de gauche à
 * droite. Ce sens-là est choisi EXPRÈS : la dalle est balayée ligne par ligne du
 * haut vers le bas, donc un déchirement coupe la barre HORIZONTALEMENT et décale
 * les deux moitiés — un artefact que l'œil lit sans ambiguïté, contrairement à
 * un scintillement qu'on peut se raconter. */
#define DN_UI_BAR_W 24
#define DN_UI_ANIM_MS_MIN 200
#define DN_UI_ANIM_MS_MAX 10000
#define DN_UI_ANIM_MS_DEFAUT 2000

/* ── Géométrie des vues de dn1-4 — PROVISOIRE, ET ÉCRIT COMME TEL ─────────── */
/*
 * ⚠️ AUCUNE de ces valeurs n'est spécifiée nulle part. Le brief et son addendum
 *    figent la STRUCTURE (barre heure/date en haut, grille 2x3, bandeau MENU en
 *    bas) et la seule dimension connue est 480x640 portrait. Tout ce qui suit est
 *    DÉRIVÉ pour que dn1-4 ait des zones tactiles à éprouver — dn3-2 dessine la
 *    vraie grille et fera foi. Ne pas bâtir dessus.
 *
 * Ce qui n'est PAS arbitraire, en revanche : aucun élément ne fait la hauteur de
 * l'écran. Le verdict adverse mesuré en dn1-3 (§10.4) est que la synchro `vsync`
 * NE PROTÈGE PAS une zone sale pleine hauteur ; une case de 225x156 est très loin
 * de ce cas. La barre du haut est pleine LARGEUR, ce qui est sans rapport : le
 * balayage descend ligne par ligne.
 *
 *   0                                                              479
 *   +--------------------------------------------------------------+   0
 *   |  barre : heure (28 px) a gauche, date (14 px) a droite        |
 *   +--------------------------------------------------------------+  70
 *   |   +--------------------+    +--------------------+           |
 *   |   |  CPU               |    |  GPU               |           |
 *   |   +--------------------+    +--------------------+           |
 *   |   |  RAM               |    |  RESEAU            |           |
 *   |   +--------------------+    +--------------------+           |
 *   |   |  TEMP.             |    |  HUMIDITE          |           |
 *   |   +--------------------+    +--------------------+           |
 *   +--------------------------------------------------------------+ 580
 *   |  MENU (o)                                                    |
 *   +--------------------------------------------------------------+ 640
 */
/*
 * ── dn4-6 / AC4 + AC11 : LES DEUX BANDES DEVIENNENT COMMUTABLES ──────────────
 *
 * 🔴 CE SONT LES DÉFAUTS, ET ILS RESTENT LES DÉFAUTS. Les override `s_*`
 *    ci-dessous existent pour que les TROIS voies de dn4-6 se jouent DANS UN
 *    SEUL FIRMWARE — la méthode qui a tranché `poll`/`event` (dn1-4), l'icône
 *    `cog` (dn3-2), la disquette et la piste de jauge (dn4-1). ⛔ On ne retire
 *    pas un `const` et on ne réécrit pas un défaut : on ajoute un override.
 *
 *   BARRE_H  MENU_H   GRILLE_H   CASE_H   ce que c'est
 *   ------------------------------------------------------------------------
 *      70      60       510       156     le DÉFAUT (dn3-2), l'état des lieux
 *      60      51       529       163     D12 — décision owner acquise
 *      60       0       580       180     voie (a), le MENU quitte la maquette
 *
 * ⚠️ D12 EST ACQUISE MAIS SON MOTIF PEUT TOMBER (X10). Elle a été prise pour
 *    « trouver 13 px ». Si la voie (c) gagne, la place ne manque plus
 *    (`48 + 2 × 40 = 128 ≤ 156`) et D12 coûte alors, sans rien acheter :
 *    +4,5 % de surface par case (35 100 -> 36 675 px) sur un `duty` déjà à
 *    10,09 %, et TOUTES les coordonnées tactiles publiées périment
 *    (VENTILOS 506..516 de dn3-2, bande de jauge y = 340..350 de dn4-1).
 *    ⇒ C'est une QUESTION OWNER, pas un choix de dev. Voir AC11.
 */
/* 🔴 D12 EST LE DÉFAUT DEPUIS LE CONSTAT OWNER DU 2026-08-19. Ce n'est pas un
 *    réglage laissé sur une valeur : la voie « repli » a été RETENUE sur la
 *    dalle, et une voie retenue se grave. La laisser en override `widget voie`
 *    aurait fait repartir le module en 70/60 au premier reboot — c'est-à-dire
 *    dans un état où `CPU` et `GPU` DÉBORDENT (bas 163 > 156, journalisé).
 * ⚠️ Bornes RELUES du contenu : la barre à 60 contient l'heure (`dn_font_28` à
 *    y = 18, boîte 18..53) et la date (`dn_font_14` à y = 28, boîte 28..46) ;
 *    le MENU à 51 contient `dn_font_28` à y = 14 (boîte 14..49). ✅ Constat
 *    owner : « non c'est bon », les deux bandes ne serrent pas.
 * ⚠️ CONSÉQUENCE, ÉCRITE ET NON MASQUÉE : `CASE_H` passe de 156 à **163**, donc
 *    TOUTE COORDONNÉE TACTILE PUBLIÉE EST PÉRIMÉE (`VENTILOS 506..516` de
 *    dn3-2, bande de jauge `y = 340..350` de dn4-1) et la case gagne +4,5 % de
 *    surface (35 100 -> 36 675 px) sur un `duty` déjà à 10,09 %. */
#define DN_UI_BARRE_H_DEFAUT 60
#define DN_UI_MENU_H_DEFAUT 51
#define DN_UI_MARGE 10
#define DN_UI_GAP 10
#define DN_UI_CASE_W ((DN_LCD_H_RES - 2 * DN_UI_MARGE - DN_UI_GAP) / 2) /* 225 */

static int s_geo_barre_h = DN_UI_BARRE_H_DEFAUT;
static int s_geo_menu_h = DN_UI_MENU_H_DEFAUT;

/* ⚠️ DES FONCTIONS, PAS DES MACROS QUI LIRAIENT LES `s_*` : une macro qui
 *    dépend d'un statique mutable a l'air d'une constante au point d'usage, et
 *    c'est exactement ce qui fait qu'on la récite au lieu de la relire. */
static inline int ui_barre_h(void) { return s_geo_barre_h; }
static inline int ui_menu_h(void) { return s_geo_menu_h; }
static inline int ui_grille_y(void) { return s_geo_barre_h; }
static inline int ui_grille_h(void)
{
    return DN_LCD_V_RES - s_geo_barre_h - s_geo_menu_h;
}
static inline int ui_case_h(void)
{
    return (ui_grille_h() - 2 * DN_UI_MARGE - 2 * DN_UI_GAP) / 3;
}

/* Zone tactile du retour : généreuse par exigence d'AC4 (« pas juste le
 * glyphe »). 120x60 dans le coin haut-gauche, soit 24 fois l'aire du chevron. */
#define DN_UI_RETOUR_W 120
#define DN_UI_RETOUR_H 60

/*
 * ── LES LIBELLÉS SONT ACCENTUÉS DEPUIS dn3-1, ET C'EST UNE POLICE GÉNÉRÉE ────
 *
 * dn1-4 les écrivait SANS accent, et ce n'était pas une négligence : les
 * built-ins `lv_font_montserrat_14/_28` sont générées avec
 * `-r 0x20-0x7F,0xB0,0x2022` (relu dans l'en-tête de leur `.c`), donc ASCII + le
 * signe degré + la puce, ET RIEN D'AUTRE. « RÉSEAU », « HUMIDITÉ », « AOÛT » y
 * perdaient leur lettre EN SILENCE — LVGL ne dessine pas un glyphe absent et ne
 * se plaint pas.
 *
 * ✅ dn3-1 solde ce legs : `dn_font_14` / `dn_font_28` couvrent ASCII +
 *    LATIN-1 COMPLET + la puce + les 60 LV_SYMBOL_* uniques + 10 icônes
 *    FontAwesome (dont 2 déjà symboles ⇒ 8 codepoints neufs). ⚠️ Les comptes
 *    font foi dans `fonts/dn_font.h`, qui les CALCULE à la génération : cette
 *    ligne disait « 61 + 7 » et quatre autres endroits du dépôt disaient encore
 *    autre chose (revue du 2026-08-18).
 *    Voir `fonts/dn_font.h` et `tools/gen_font_dn.py`.
 *
 * ── LA GRILLE, AMENDÉE PAR D6 (2026-08-17) ───────────────────────────────────
 *
 *   idx 0 CPU        idx 1 GPU
 *   idx 2 RAM        idx 3 RÉSEAU
 *   idx 4 VENTILOS   idx 5 AMBIANCE      <- la dernière ligne, close par dn3-1
 *
 * D6 fusionne TEMP.+HUMIDITÉ en une seule case « AMBIANCE » à DEUX grandeurs, et
 * la place libérée reçoit la vitesse des ventilateurs. Le compte de six est
 * préservé.
 * ⚠️ CONSÉQUENCE ÉCRITE, PAS MASQUÉE : PC éteint, UNE SEULE case sur six reste
 *    vivante (Ambiance) au lieu de deux. Le différenciateur du brief tient, il se
 *    voit deux fois moins.
 *
 * 🔴 GPU / RAM / RÉSEAU RESTENT DES CASES NUES, ET CE N'EST PAS UNE PARESSE :
 *    c'est LE TÉMOIN NÉGATIF d'AC8 — la seule façon de chiffrer une case-widget
 *    contre une case nue sous le MÊME fps, le MÊME bounce, le MÊME draw buffer.
 *    Mais « nue » porte sur la FORME, pas sur l'honnêteté : leurs factices
 *    d'apparence réelle (« 37 % », « 12,4 Go », « 48 Mo/s ») sont SUPPRIMÉS.
 *    Aucune source ne les alimente ⇒ elles disent « -- », comme toute case sans
 *    source. Un chiffre plausible sans source est le mensonge d'interface que ce
 *    dépôt traque depuis dn1-3.
 */
/* Les index de case, DÉCLARÉS ICI parce que `k_widget[]` et `k_desc[]` s'en
 * servent comme initialiseurs désignés. ⚠️ D6 les a DÉPLACÉS : 4 était TEMP. et
 * 5 HUMIDITÉ jusqu'à dn2-1. */
#define DN_UI_CASE_CPU 0
#define DN_UI_CASE_GPU 1
#define DN_UI_CASE_RAM 2
#define DN_UI_CASE_RESEAU 3
/* 🔴 dn4-1 / D8 : l'index 4 n'est plus VENTILOS mais DISQUE. Le SYMBOLE et le
 * LIBELLÉ changent ; ⛔ les commentaires HISTORIQUES qui racontent pourquoi
 * VENTILOS a existé sont ANNOTÉS, pas réécrits — l'histoire d'un dépôt ne se
 * masque pas, et c'est elle qui explique pourquoi quatre glyphes de ventilateur
 * restent embarqués. Motif du changement : les RPM boîtier et CPU passent par le
 * Super I/O de LibreHardwareMonitor (driver kernel + admin), et D8 sort le Ring0
 * du périmètre V1. Une case qui ne peut pas être alimentée n'est pas une case. */
#define DN_UI_CASE_DISQUE 4
#define DN_UI_CASE_AMB 5

static const char *const k_nom[DN_UI_METRIQUES] = {
    "CPU", "GPU", "RAM", "RÉSEAU", "DISQUE", "AMBIANCE",
};

/*
 * Quelles cases reçoivent le MODÈLE de widget.
 * 🔴 dn3-2 : LES SIX. C'est la marche P7 — la grille cesse d'être « trois
 *    briques et trois trous ». ⚠️ `k_desc[]` était DÉJÀ dimensionnée à
 *    DN_UI_METRIQUES : le travail a été TROIS INITIALISEURS DÉSIGNÉS à ajouter,
 *    pas un redimensionnement ni un refactor.
 */
static const bool k_widget[DN_UI_METRIQUES] = {
    [DN_UI_CASE_CPU] = true,   [DN_UI_CASE_GPU] = true,
    [DN_UI_CASE_RAM] = true,   [DN_UI_CASE_RESEAU] = true,
    [DN_UI_CASE_DISQUE] = true, [DN_UI_CASE_AMB] = true,
};

/*
 * ── W11 — LE TÉMOIN NÉGATIF D'AC8 NE DOIT PAS QUITTER LE FIRMWARE ────────────
 *
 * 🔴 LE PROBLÈME, ÉCRIT AVANT LA SOLUTION. Jusqu'à dn3-1, GPU/RAM/RÉSEAU
 *    étaient NUES, et c'est CONTRE ELLES que tous les chiffres d'AC8 se
 *    comparaient : « une case-widget contre une case nue, sous le MÊME fps, le
 *    MÊME bounce, le MÊME draw buffer, dans le MÊME firmware ». Les six
 *    devenant des widgets, cette référence DISPARAÎT — et AC8 se retrouverait à
 *    comparer un firmware à un autre firmware, exactement ce que dn3-1 s'est
 *    interdit.
 *
 * ⇒ On peut rendre une case NUE À CHAUD (`widget nue <idx> on|off`). La
 *   référence reste donc mesurable dans le firmware des six widgets.
 *
 * ⚠️ CONTRAINTE DE FORME, ET ELLE N'EST PAS NÉGOCIABLE : `k_widget[]` est
 *    `const`, en `.rodata`, et la convention du dépôt (`k_*` const / `s_*`
 *    mutable) NE SE CASSE PAS. Le mécanisme est donc un tableau d'OVERRIDE
 *    `s_*` consulté par les lecteurs — ⛔ pas un `const` retiré.
 *
 * ⚠️ IL Y A SEPT LECTEURS, ET LES SEPT PASSENT PAR `case_est_widget()` :
 *      1  `dn_ui_desc`
 *      2  `dn_ui_case_est_widget`   (exposé pour la table de géométrie console)
 *      3  `dn_ui_est_widget`
 *      4  la boucle de `build_dashboard`
 *      5  `detail_reparametrer`
 *      6  `case_poser`
 *      7  `dn_ui_pc_maj`            <- AJOUTÉ PAR dn4-6, pour lire la PRÉCISION
 *    En oublier un rendrait une case dessinée nue mais mise à jour comme un
 *    widget — un pointeur `valeur[0]` lu là où le modèle attend une racine.
 * 🔴 dn4-1 EN A AJOUTÉ UN SANS METTRE À JOUR CE COMPTE (revue 2026-08-19), et
 *    l'écart avait SURVÉCU dans les étiquettes elles-mêmes : le fichier portait
 *    « LECTEUR 1/6 », « 2/5 », « 3/5 », « 4/6 », « 5/5 » — cinq numérotations
 *    pour une seule liste. La garde de complétude de W11 repose ENTIÈREMENT sur
 *    cette énumération : un compte récité là où une liste existe est le motif
 *    que dn4-1 corrige trois fois ailleurs.
 * ⇒ AJOUTER UN LECTEUR, C'EST L'AJOUTER ICI DANS LE MÊME GESTE, et renuméroter.
 */
static bool s_nue_force[DN_UI_METRIQUES];

static bool case_est_widget(int idx)
{
    return idx >= 0 && idx < DN_UI_METRIQUES && k_widget[idx] &&
           !s_nue_force[idx];
}

/*
 * ── dn4-6 / AC4 : LE NOMBRE DE GRANDEURS D'UNE CASE, RÉGLABLE À CHAUD ────────
 *
 * 🔴 SANS ÇA, LE REPLI PRÉ-AUTORISÉ N'EST PAS COMPARABLE. Le repli écrit
 *    d'avance est **`GPU` à TROIS** (`% · °C · W`), qui tient en police 28 avec
 *    D12 seule — et l'owner ne peut l'arbitrer contre (a) et (b) que s'il le
 *    voit SUR LA MÊME DALLE, DANS LE MÊME FIRMWARE. Le reflasher pour le
 *    montrer coûterait une observation, ce que ce dépôt refuse depuis dn3-2.
 * ⚠️ MÊME PATRON QUE `s_nue_force[]` ET `s_icone_alt[]` : `k_desc[]` est `const`
 *    en `.rodata` et le RESTE (⛔ on ne retire pas un `const`). L'override est
 *    un `s_*` consulté par les lecteurs.
 * ⚠️ `0` = PAS D'OVERRIDE, et c'est cohérent : un descripteur à zéro grandeur
 *    n'a aucun sens, donc zéro ne peut pas être une valeur demandée.
 * ⛔ IL Y A **TROIS** LECTEURS, et cette énumération FAIT PARTIE DE LA GARDE —
 *    même doctrine que W11, dont le compte avait divergé cinq fois :
 *      1  la boucle de `build_dashboard` (la copie locale du descripteur)
 *      2  `detail_reparametrer`
 *      3  `dn_ui_pc_maj`
 *    En oublier un afficherait N grandeurs et en formaterait un autre nombre.
 */
static uint8_t s_gr_force[DN_UI_METRIQUES];

/*
 * ── LES DESCRIPTEURS — LE SEUL POINT D'AJOUT D'UNE MÉTRIQUE ──────────────────
 *
 * C'est la promesse du brief rendue structurelle : « ajouter une métrique future
 * (SSD, ventilateurs, puissance, NAS, Bambu…) ne redessine pas l'UI ». Une ligne
 * ici, zéro ligne de dessin. Falsifiable à la demande : `widget demo on`.
 *
 * Les couleurs sont celles de la palette du mode Actif (addendum §1) : CPU
 * violet, VENTILOS cyan, AMBIANCE orange. ⚠️ dn3-1 les PORTE seulement — c'est
 * dn3-3 qui bascule Ambient/Actif et qui fait foi sur la palette. Elles sont
 * posées ici pour que le champ `couleur` ne soit pas un champ MORT que dn3-3
 * découvrirait non branché (leçon T4 de dn2-1 : ce qui n'est jamais appelé ne
 * prouve rien).
 */
static const dn_widget_desc_t k_desc[DN_UI_METRIQUES] = {
    [DN_UI_CASE_CPU] = {
        .icone = DN_ICONE_MICROCHIP,
        .titre = "CPU",
        .couleur = 0x9b6cff, /* violet */
        /* 🔴 D10 (dn4-1) : DEUX grandeurs — % et fréquence. ⚠️ La TEMPÉRATURE
         *    CPU que la maquette de l'addendum §1 dessinait (« CPU 54°C ») est
         *    INATTEIGNABLE sans Ring0, et D8 sort le Ring0 du périmètre V1 :
         *    c'est la FRÉQUENCE qui prend la place, parce qu'elle est libre de
         *    droits ET qu'elle bouge (mesuré sur la tour : 1,2 à 3,2 GHz).
         * ⚠️ Pas de jauge : un % de CPU n'en avait déjà pas, et à n = 2 la
         *    géométrie ne laisserait plus de place à la secondaire (contrat
         *    écrit dans `dn_widget.h`). */
        /*
         * 🔴 D11 (dn4-6) : TROISIÈME GRANDEUR — LE CŒUR LE PLUS CHARGÉ.
         *    Le motif est chiffré : sur 16 cœurs logiques, UN cœur saturé ne
         *    pèse que ~6 % de moyenne. La case disait donc « 6 % » d'un PC en
         *    train de ramer — vrai, et faux de ce qui compte.
         * ✅ ET LA CONCLUSION ÉCRITE DU LEDGER EST RÉFUTÉE : « le CPU n'aurait
         *    rien à mettre en troisième » est FAUX. `max(cpu_percent(percpu=True))`
         *    a été MESURÉ (n=29, 1 Hz) : étendue 25,0..73,9 %, texte changé
         *    28/28 (100 %), σ = 13,2 — et il coûte 0,07..0,10 ms parce que c'est
         *    LE MÊME APPEL `psutil` que le % moyen, pas un appel de plus.
         * ⛔ `len(pids())` est écarté DEUX FOIS par la mesure : 1/28 de
         *    changements (case morte) ET 8,4 ms par tir (0,84 % d'un cœur).
         *
         * 🔴 LE MARQUAGE EST UN LIVRABLE, PAS UN DÉTAIL (AC1). Deux
         *    pourcentages dans la même case, c'est deux lignes visuellement
         *    identiques dont l'une ment par omission. `prefixe = "c.max"` est
         *    le verbatim de la maquette (addendum §1) — et c'est un champ NOMMÉ,
         *    ⛔ pas le champ `icone` détourné.
         * ⚠️ Pas de jauge : un % de CPU n'en avait déjà pas, et à trois lignes
         *    la géométrie ne laisserait plus de place (contrat `dn_widget.h`).
         */
        .n_grandeurs = 3,
        .indicateur = false,
        .grandeurs = {{.unite = "%", .prec = DN_PREC_DIXIEME},
                      {.unite = "GHz", .prec = DN_PREC_DIXIEME},
                      {.unite = "%", .prefixe = "c.max", .prec = DN_PREC_DIXIEME}},
    },
    /*
     * ── LES TROIS NEUVES DE dn3-2 (W6, W10) ─────────────────────────────────
     *
     * W10 — les hex viennent de la palette du mode Actif (addendum §1) : GPU
     * CYAN, RAM VIOLET, RÉSEAU CYAN. ⚠️ dn3-2 les PORTE, dn3-3 FAIT FOI. Elles
     * sont posées ici pour la même raison que dn3-1 a posé les trois autres :
     * pour que le champ `couleur` ne soit pas un champ MORT que dn3-3
     * découvrirait non branché (leçon T4 de dn2-1 — ce qui n'est jamais appelé
     * ne prouve rien).
     *
     * Les icônes sont prises parmi les 10 FontAwesome DÉJÀ EMBARQUÉES par
     * dn3-1 — `memory` et `network-wired` y sont, ce qui n'est pas un hasard :
     * elles ont été embarquées EN PRÉVISION de ces cases. ⛔ Aucun glyphe neuf,
     * donc aucune régénération de police (elle exige un shim npm absent du
     * tableau des versions figées, et un clone neuf SANS RÉSEAU échouerait).
     * ⚠️ Un glyphe absent serait dessiné EN SILENCE — c'est pour ça qu'on ne
     *    pioche que dans la liste vérifiée de `fonts/dn_font.h`.
     */
    [DN_UI_CASE_GPU] = {
        /* `desktop` (U+F108) : le GPU est ce qui pilote l'écran. C'est le
         * moins mauvais des glyphes DISPONIBLES — `microchip` est déjà pris
         * par CPU, et un doublon rendrait les deux cases confusibles au coup
         * d'oeil, qui est le seul usage réel d'une icône de 28 px. */
        .icone = DN_ICONE_DESKTOP,
        .titre = "GPU",
        .couleur = 0x35d6e8, /* cyan — famille « données PC » */
        /*
         * 🔴 D10 (dn4-1) : DEUX grandeurs, et LA GRANDEUR 0 CHANGE DE NATURE —
         *    elle était la TEMPÉRATURE (le mock rampait de 38 à 72 « °C »), elle
         *    devient le POURCENTAGE D'UTILISATION, la °C passant en grandeur 1.
         *    C'est l'ordre de la maquette (« 46 % · 61°C ») et l'ordre de tout
         *    le reste du dashboard : la grandeur 0 est celle qui porterait la
         *    jauge et celle que le détail montre en premier.
         *
         * ✅ W1 EST FERMÉE PAR LA MESURE, ET DANS L'AUTRE SENS QUE PRÉVU. Le
         *    cadrage annonçait NVML — inapplicable, la tour est une AMD Radeon
         *    RX 6800 XT (contrôleur UNIQUE) — et pré-autorisait le repli « % seul,
         *    °C déclarée absente ». LE REPLI N'A PAS ÉTÉ NÉCESSAIRE : `atiadlxx.dll`
         *    (`ADL2_New_QueryPMLogData_Get`, ctypes, SANS élévation ni driver)
         *    rend le % ET la °C en UN appel, pour 0,5 ms de CPU.
         * ⚠️ Et le candidat que le cadrage nommait pour le % — les 720 instances
         *    WMI `GPUEngine` — a été MESURÉ à 342 ms de CPU par tir, soit 657x
         *    plus cher : à lui seul il faisait sauter le critère n°4 du brief
         *    (« < 1 % CPU ») et ne tenait même pas la cadence 1 Hz.
         * ⚠️ La 2ᵉ grandeur reste DÉCLARÉE même si une source future ne la donne
         *    pas : W10 fait afficher « -- » en gris sur CETTE ligne seulement.
         */
        /*
         * 🔴 D11 (dn4-6) : QUATRE GRANDEURS — % · °C · W · tr/min.
         *
         * ✅ ET ELLES SONT GRATUITES À LA SOURCE, C'EST MESURÉ : les six index
         *    ADL sortent du MÊME appel `ADL2_New_QueryPMLogData_Get` déjà payé
         *    (0,976 ms, sans élévation ni driver — D8 tenu). Le budget de cette
         *    story est LE PIXEL, pas le CPU.
         *      idx 23 `ASIC_POWER`  53 W, étendue 52..57, 12/29 changements (41,4 %)
         *      idx 14 `FAN_RPM`     604 tr/min — ⚠️ MOUVEMENT NON MESURÉ (X1/AC6)
         *    ⛔ `CLK_GFXCLK` (idx 1) reste ÉCARTÉ par la mesure : 6..499 MHz au
         *      repos, 29/29 changements ⇒ « 0,0 GHz » au repos et un saut par
         *      seconde. Une case qui clignote n'est pas une case qui informe.
         *
         * ⚠️ `FAN_RPM` ENTRE AVEC UNE DETTE DE MESURE EXPLICITE. Son critère de
         *    qualification (W2) est écrit et horodaté AVANT l'échantillonnage
         *    (AC6 : étendue ≥ 5 unités affichées, ≥ 10 % de changements DU
         *    TEXTE, σ ≥ 1). S'il échoue, le repli est ÉCRIT D'AVANCE et déjà
         *    mesuré : `ASIC_POWER` seul, donc `GPU` à trois.
         *
         * 🔴 AC9 — `W` ET `tr/min` SONT DES ENTIERS. « 212,0 W » et
         *    « 604,0 tr/min » inventent une décimale que la source ne porte pas :
         *    c'est un mensonge d'interface, la même famille que le « 34,3 Go »
         *    décimal affiché contre le « 31,9 » de Windows. Le FIL reste en
         *    dixièmes ; c'est l'AFFICHAGE qui arrondit.
         */
        /*
         * 🔴 TROIS, PAS QUATRE — DÉCISION OWNER DU 2026-08-19, PRISE SUR LA DALLE.
         *
         * ⚠️ ET CE N'EST PAS `FAN_RPM` QUI EST DISQUALIFIÉ : il a QUALIFIÉ, et
         *    largement. Session de 959 échantillons / 16 min à 1 Hz, critère
         *    écrit et HORODATÉ avant le tir : étendue **13 tr/min** (≥ 5),
         *    **55,2 %** de changements du TEXTE (≥ 10 %), **σ 2,02** (≥ 1).
         *    Les trois conditions de W2 sont tenues.
         * ⛔ CE QUI MANQUE EST LA PLACE, ET ELLE A ÉTÉ MESURÉE : à quatre
         *    grandeurs empilées en police 28, `48 + 3×40 + 35 = 203 > 163` — la
         *    4ᵉ valeur est ENTIÈREMENT hors case. Les deux seules voies qui la
         *    feraient tenir coûtent, l'une la barre MENU **et** un interligne de
         *    1 px (sous le critère écrit de D12), l'autre une 3ᵉ police à
         *    générer **et** des valeurs 21 % plus petites. L'owner a préféré
         *    trois grandeurs lisibles à quatre grandeurs serrées.
         * ⚠️ LE FIL, LUI, CONTINUE DE PORTER LES QUATRE (`k_metriques[]` déclare
         *    `n_grandeurs = 4` pour `gpu`) : la source est prouvée, l'agent la
         *    publie, seule la PLACE manque. C'est exactement le cas de `RAM`,
         *    qui reçoit deux valeurs et n'en affiche qu'une. ⛔ Ne pas « nettoyer »
         *    le protocole : le jour où la place existe, la grandeur est déjà là.
         * ⇒ AU LEDGER : « `FAN_RPM` qualifie et n'a pas de place » — c'est une
         *   dette de PLACE, pas une question ouverte de source.
         */
        .n_grandeurs = 3,
        .indicateur = false,
        .grandeurs = {{.unite = "%", .prec = DN_PREC_DIXIEME},
                      {.unite = "\xC2\xB0" "C", .prec = DN_PREC_DIXIEME},
                      {.unite = "W", .prec = DN_PREC_ENTIER},
                      {.unite = "tr/min", .prec = DN_PREC_ENTIER}},
    },
    [DN_UI_CASE_RAM] = {
        .icone = DN_ICONE_MEMORY,
        .titre = "RAM",
        .couleur = 0x9b6cff, /* violet */
        /*
         * 🔴 UNE SEULE GRANDEUR, ET C'EST LE PIÈGE N°1 DU MODÈLE QUI L'IMPOSE.
         *    L'addendum §1 demande « violet + JAUGE » ET une donnée secondaire
         *    « 12.1 / 32 Go ». Or `dn_widget.c:267` teste
         *    `if (desc->indicateur && n == 1)` : avec `n_grandeurs >= 2`, LA
         *    JAUGE N'EST JAMAIS CRÉÉE, EN SILENCE — et le champ `indicateur`
         *    est documenté SANS cette restriction (différé de la revue dn3-1).
         *    ⇒ « 12,1 / 32 Go » n'est PAS une seconde grandeur : c'est la
         *      DONNÉE SECONDAIRE (`etat.secondaire`), qui a son propre label et
         *      ne compte pas dans `n_grandeurs`. La jauge survit.
         * ⚠️ Vérifié dans le source AVANT de poser la jauge, pas découvert
         *    après coup sur une case sans barre.
         */
        .n_grandeurs = 1,
        .indicateur = true,
        .ind_min = 0,
        .ind_max = 100, /* % — la plage ANNONCÉE, et celle du mock */
        .grandeurs = {{.unite = "%", .prec = DN_PREC_DIXIEME}},
    },
    [DN_UI_CASE_RESEAU] = {
        .icone = DN_ICONE_NETWORK_WIRED,
        .titre = "RÉSEAU",
        .couleur = 0x35d6e8, /* cyan */
        /* Pas de jauge : un débit n'a pas de plein. `ind_max` devrait valoir la
         * capacité du lien, que le firmware ne connaît pas — une jauge dont
         * l'échelle est inventée est un mensonge d'interface silencieux. */
        /*
         * 🔴 DEUX GRANDEURS EMPILÉES — CONSTAT OWNER EN SÉANCE CARTE (2026-08-18) :
         *    « réseau, il faudrait mettre les 2 valeurs l'une au-dessus de l'autre,
         *    avec flèche vers le bas (reçoit) et vers le haut à côté ».
         *
         * ⚠️ CE QUE ÇA REMPLACE : le descendant vivait en grandeur 0 et le couple
         *    ↓/↑ en LIGNE SECONDAIRE (« ↓ 985 ↑ 48 », verbatim de l'addendum §1).
         *    L'owner l'a vu sur la dalle et préfère les deux montants à égalité.
         * ✅ AUCUNE BORNE N'EST TOUCHÉE : c'est EXACTEMENT le mécanisme
         *    `n_grandeurs` qu'AMBIANCE utilise déjà, icône par grandeur comprise.
         *    L'agent envoie déjà v1 (↓) et v2 (↑) — rien ne change côté trame.
         * ⚠️ `LV_SYMBOL_DOWN`/`UP` (U+F078/U+F077), ⛔ PAS les flèches Unicode
         *    U+2193/U+2191 : celles-ci sont HORS latin-1 et le glyphe absent
         *    serait dessiné EN SILENCE. Les deux codepoints FontAwesome sont
         *    VÉRIFIÉS présents dans les deux `.c` de police.
         * ⚠️ L'unité est portée par les DEUX lignes : elles sont indépendantes, et
         *    une valeur ABSENTE ne porte jamais son unité — la règle ne tiendrait
         *    plus si la seconde héritait de la première.
         */
        .n_grandeurs = 2,
        .indicateur = false,
        /*
         * 🔴 CONSTAT OWNER EN SÉANCE, 2026-08-19, VERBATIM : *« réseau, pour si
         *    valeur haute, convertir en Gb/s »*. Il répondait « oui, MAIS » à la
         *    question de lisibilité d'AC1 — donc AC1 n'était pas satisfaite.
         * ⚠️ ET LE CHIFFRE LUI DONNE RAISON : « ↓ 99999,9 Mb/s » mesure
         *    **202 px pour 201 utiles** (relu de `lv_text_get_size()`, AC5).
         *    Elle DÉBORDAIT déjà, et LVGL la clippait sans un mot.
         * ⚠️ SEUIL À 1000,0 Mb/s = 1 Gb/s, ⛔ pas un chiffre rond arbitraire :
         *    c'est l'endroit où l'unité change de nom. En dessous, « 999,9 Mb/s »
         *    tient ; au-dessus, « 100,0 Gb/s » est plus court ET plus lisible.
         * ⚠️ `DISQUE` a exactement la même forme (« 99999,9 Mo/s ») et le
         *    mécanisme est PRÊT pour elle — ⛔ il n'est PAS armé : l'owner a
         *    nommé RÉSEAU, et étendre en silence serait décider à sa place.
         *    Legs explicite, pas un oubli.
         */
        .grandeurs = {{.unite = "Mb/s", .icone = LV_SYMBOL_DOWN,
                       .prec = DN_PREC_DIXIEME, .seuil_haut = 10000,
                       .diviseur_haut = 1000, .unite_haute = "Gb/s"},
                      {.unite = "Mb/s", .icone = LV_SYMBOL_UP,
                       .prec = DN_PREC_DIXIEME, .seuil_haut = 10000,
                       .diviseur_haut = 1000, .unite_haute = "Gb/s"}},
    },
    [DN_UI_CASE_DISQUE] = {
        /*
         * ── HISTORIQUE, CONSERVÉ ET ANNOTÉ (dn4-1 / W11) ────────────────────
         * ⚠️ CE PARAGRAPHE DÉCRIT LA CASE **VENTILOS**, QUI OCCUPAIT CET INDEX
         *    JUSQU'À dn3-2. Il est gardé parce qu'il explique pourquoi quatre
         *    glyphes de ventilateur restent embarqués dans la police. ⛔ Il n'est
         *    PAS réécrit : l'histoire d'un dépôt ne se falsifie pas.
         *
         *   « W4 TRANCHÉ PAR CONSTAT OWNER, 2026-08-17, A/B joué sur la dalle.
         *     `fan` (0xF863) est ABSENT du FontAwesome du dépôt (arrivé en 5.11,
         *     le `.woff` est antérieur — vérifié en le convertissant SEUL, pas
         *     déduit d'une table). Quatre substituts embarqués et commutés à
         *     chaud (`widget icone`) : `sync-alt` « ne dit rien » (owner), `wind`
         *     écarté, `cog` RETENU — « un engrenage, ça dit pièce mécanique en
         *     rotation ». ET IL EST GRATUIT : 0xF013 est DÉJÀ l'un des
         *     codepoints de symboles que `built_in_font_gen.py` injecte. »
         *
         * ── CE QUE LA CASE EST AUJOURD'HUI (D8, 2026-08-18) ──────────────────
         * 🔴 DISQUE. Le ventilateur sort du périmètre V1 avec le Ring0 (D8).
         *
         * ✅ ICÔNE : la DISQUETTE `save` (U+F0C7), DÉCISION OWNER du 2026-08-18.
         *    Et elle coûte ZÉRO glyphe — MESURÉ avec `codepoints_du_c()` du
         *    dépôt (⛔ pas par un test de bornes, c'est ce test-là qui avait fait
         *    croire `fan` présent) : U+F0C7 est déjà l'un des 60 symboles amont,
         *    présent dans les DEUX `.c` (260 codepoints / 3 cmaps chacun),
         *    l'union `-r` reste à 68 et les `.c` sont BIT-IDENTIQUES (sha256).
         *
         * ✅ GRANDEUR : le DÉBIT, tranché PAR LA MESURE (W2), pas par la
         *    maquette. Critère écrit AVANT la mesure (« une case de six doit
         *    BOUGER », quantifié) puis session réelle de 16 min à 1 Hz sur la
         *    tour, les deux candidats échantillonnés ENSEMBLE à la MÊME
         *    résolution (le dixième d'unité affichée) :
         *      · débit I/O      : texte changé 93,3 % du temps, étendue 268,4 Mo/s
         *      · taux d'occupation : texte changé 0,0 % du temps, étendue NULLE
         *        (54,9 % du premier au dernier échantillon)
         *    ⇒ l'occupation est une CASE MORTE. W12 ne se pose donc pas.
         *
         * ⛔ PAS DE JAUGE, et c'est le MÊME motif écrit que pour RÉSEAU : un
         *    débit n'a pas de plein. `ind_max` devrait valoir la capacité du
         *    lien, que le firmware ne connaît pas — et une jauge dont l'échelle
         *    est inventée est un mensonge d'interface silencieux.
         *
         * ⚠️ COULEUR PROVISOIRE : le cyan est HÉRITÉ de VENTILOS (famille
         *    « données PC »). La teinte exacte est un LEGS EXPLICITE À dn3-3
         *    (décision owner : « dn4-1 stabilise, dn3-3 peaufine »). ⛔ Ne pas la
         *    présenter comme une décision.
         */
        .icone = DN_ICONE_SAVE,
        .titre = "DISQUE",
        .couleur = 0x35d6e8, /* cyan — PROVISOIRE, hérité de VENTILOS (legs dn3-3) */
        .n_grandeurs = 1,
        .indicateur = false,
        .grandeurs = {{.unite = "Mo/s", .prec = DN_PREC_DIXIEME}},
    },
    [DN_UI_CASE_AMB] = {
        .icone = DN_ICONE_THERMOMETER_HALF,
        .titre = "AMBIANCE",
        .couleur = 0xff9640, /* orange */
        .n_grandeurs = 2,    /* D6 — DANS LE MODÈLE, pas rustiné après */
        .indicateur = false,
        .grandeurs = {{.unite = "\xC2\xB0" "C", .prec = DN_PREC_DIXIEME},
                      {.unite = "%", .icone = DN_ICONE_TINT,
                       .prec = DN_PREC_DIXIEME}},
    },
};

/* 🔴 dn3-2 : LES SIX DESCRIPTEURS EXISTENT. Une case n'est plus NUE par absence
 * de descripteur, mais parce que `s_nue_force[]` le demande (W11) — le témoin
 * négatif d'AC8 est devenu un RÉGLAGE À CHAUD au lieu d'un trou dans la table.
 * C'est ce qui permet de mesurer la case nue et les six widgets DANS LE MÊME
 * FIRMWARE, ce qu'AC8 exige. */

/* Le nombre de grandeurs EFFECTIF d'une case — override compris.
 * ⚠️ DÉFINI ICI, après `k_desc[]` : le placer près de `s_gr_force[]` le
 *    référençait avant sa définition. */
static int desc_n(int idx)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES) {
        return 0;
    }
    return s_gr_force[idx] ? s_gr_force[idx] : k_desc[idx].n_grandeurs;
}

int dn_ui_case_grandeurs(int idx) { return desc_n(idx); }



const char *dn_ui_metrique_nom(int idx)
{
    return (idx >= 0 && idx < DN_UI_METRIQUES) ? k_nom[idx] : "?";
}

const dn_widget_desc_t *dn_ui_desc(int idx)
{
    /* LECTEUR 1/7 de l'override W11 — voir `case_est_widget()`. */
    return case_est_widget(idx) ? &k_desc[idx] : NULL;
}

/* Le descripteur BRUT — ⛔ SANS l'override W11 (revue 2026-08-19).
 * `dn_ui_desc()` rend NULL pour une case rendue NUE, ce qui est correct pour tout
 * ce qui DESSINE. Mais la table de géométrie de la console publie une colonne
 * « demandé par le descripteur » : elle doit lire ce que le descripteur DEMANDE,
 * pas ce que l'override RÉALISE. Sans ça, `widget nue 2 on` faisait annoncer
 * « (n=0) » et faisait disparaître « jauge demandee » pour une case dont le
 * descripteur demande n=1 AVEC jauge — deux chiffres faux dans la colonne dont
 * l'en-tête promet le contraire.
 * ⛔ NE PAS l'utiliser pour décider d'un rendu : c'est `dn_ui_desc()` qui fait foi. */
const dn_widget_desc_t *dn_ui_desc_brut(int idx)
{
    return (idx >= 0 && idx < DN_UI_METRIQUES) ? &k_desc[idx] : NULL;
}

/* Une case est-elle rendue NUE (override W11, `widget nue <idx> on`) ?
 * ⚠️ LECTEUR 2/7 de l'override, exposé pour que la table de géométrie ne présente pas
 * un `n_gr = 1` de case nue comme un abandon géométrique — c'était un faux
 * positif sur le chemin le plus utilisé d'une campagne AC8. */
bool dn_ui_case_est_widget(int idx)
{
    return case_est_widget(idx);
}

bool dn_ui_est_widget(int idx)
{
    /* LECTEUR 3/7 de l'override W11. */
    return case_est_widget(idx);
}

const char *dn_ui_vue_name(dn_ui_vue_t v)
{
    switch (v) {
    case DN_VUE_DASHBOARD:
        return "dashboard";
    case DN_VUE_DETAIL:
        return "detail";
    default:
        return "?";
    }
}

const char *dn_nav_model_name(dn_nav_model_t m)
{
    switch (m) {
    case DN_NAV_REBUILD:
        return "rebuild";
    case DN_NAV_SCREENS:
        return "screens";
    default:
        return "?";
    }
}

bool dn_nav_model_from_name(const char *nom, dn_nav_model_t *out)
{
    for (int i = 0; i < DN_NAV_COUNT; i++) {
        if (strcasecmp(nom, dn_nav_model_name((dn_nav_model_t)i)) == 0) {
            *out = (dn_nav_model_t)i;
            return true;
        }
    }
    return false;
}

/* ── État ─────────────────────────────────────────────────────────────────── */

static lv_display_t *s_disp;
/* W8/AC9 — le repeint en BANDES. INERTE par défaut (`widget bandes on`). */
static bool s_bandes;
static esp_lcd_panel_handle_t s_panel;
/*
 * DEUX slots pour le label vivant, un par vue — et ce n'est pas du zèle.
 * En modèle SCREENS les deux écrans existent en même temps, donc le label aussi.
 * Un pointeur unique finirait par désigner le label de l'écran NON affiché : le
 * timer 1 Hz écrirait dans le vide, l'écran visible se figerait, et on
 * chercherait la panne du côté du timer alors que c'est le pointeur qui aurait
 * changé de propriétaire. `label_courant()` est la seule façon d'y accéder.
 */
static lv_obj_t *s_label_dash;
static lv_obj_t *s_label_det;
static lv_obj_t *s_bar;
static lv_timer_t *s_timer;
static lv_image_dsc_t s_bg_dsc;
static uint16_t *s_bg_psram;      /* copie PSRAM du fond, NULL si mmap flash */
static esp_err_t s_asset_err = ESP_OK;

static dn_vsync_sub_t s_vsync_sub = -1;
static volatile dn_flush_sync_t s_sync = DN_FLUSH_SYNC_VSYNC;
static volatile dn_flush_path_t s_path = DN_FLUSH_PATH_BITMAP;
/*
 * Mode DIRECT : LVGL dessine dans les DEUX framebuffers du driver et on bascule.
 * Décidé au boot par num_fbs, jamais à chaud — les framebuffers sont alloués une
 * fois, et le mode de rendu de LVGL se fixe avec eux.
 */
static bool s_direct_mode;
static int s_affinity = -1;
static volatile bool s_first_frame;
/*
 * MASQUÉ PAR DÉFAUT depuis dn1-4, et c'est un changement de comportement assumé :
 * le label vivant est centré (géométrie gelée pour rester comparable à dn1-3) et
 * recouvrirait les cases RAM/RESEAU du dashboard. `ui label on` le rallume pour
 * rejouer le régime produit de dn1-3 à l'identique — c'est ce que fait AC6 pour
 * ré-observer l'artefact §10.5, qui a besoin d'un redessin périodique.
 */
static volatile bool s_label_shown;
static volatile bool s_anim_on;
static volatile bool s_active = true;
static int s_anim_ms = DN_UI_ANIM_MS_DEFAUT;

static int s_draw_lines;
static bool s_draw_psram;
static size_t s_int_avant, s_int_apres, s_psram_avant, s_psram_apres;

/* ── Navigation (dn1-4) ───────────────────────────────────────────────────── */
static dn_ui_vue_t s_vue = DN_VUE_DASHBOARD;
static int s_metrique;
/*
 * ── LE MODÈLE RETENU, ET LES CHIFFRES QUI L'ONT CHOISI (AC4, 2026-08-16) ─────
 *
 * 20 allers-retours scriptés (`nav ab 20`), latence clic -> dernier flush :
 *
 *   draw_lines   modèle    min      moy      max      tas LVGL utilisé
 *   ---------------------------------------------------------------------
 *      64        rebuild   293,9    307,7    320,7    12 016 o (20 %)
 *      64        SCREENS   267,1    267,9    293,9    20 064 o (33 %)
 *     128        rebuild   240,4    279,0    318,0    17 684 o (29 %)
 *     128        SCREENS   187,0    234,9    257,7    —
 *
 * SCREENS gagne 40 ms (13 %) sur rebuild, pour +8 048 o dans le tas LVGL (les
 * deux arbres vivent en permanence) sur 64 Ko dont 42 Ko restent libres.
 *
 * ⚠️ CE TABLEAU EST CELUI DE LA PREMIÈRE CAMPAGNE, ET IL EST FAUX SUR LE PRIX.
 *    Il a été relevé à `bounce_px = 0` (config déclarée « écran inutilisable »
 *    depuis) et surtout sur un A/B dont la bascule FUYAIT un arbre d'écran
 *    complet — corrigé dans build_scene(). Le tas y était donc gonflé.
 *
 * ── ✅ LA MESURE QUI FAIT FOI (session carte du 2026-08-16, firmware 0e7fe61) ──
 *
 *   Config de référence : num_fbs=1 · bounce_px=4800 · draw_lines=128 · poll
 *
 *   modèle     min      moy      max      n       tas LVGL utilisé
 *   ---------------------------------------------------------------
 *   SCREENS    285,0    307,0    320,8    40/40   15 216 o   (delta -12 o)
 *   rebuild    300,8    346,9    374,2    40/40   12 184 o   (delta   0 o)
 *
 * SCREENS gagne 39,9 ms (11,5 %) pour +3 032 o de tas — et NON +8 048 o : la
 * fuite surestimait son prix de 2,7x. L'écart entre modèles est remarquablement
 * STABLE (39,8 ms à bounce 0/lines 64, 39,9 ms ici) : le coût du modèle est un
 * coût de CONSTRUCTION D'ARBRE, indépendant du pipeline d'affichage.
 *
 * ⛔ NE PAS écrire ici que « SCREENS fait passer le budget » : le budget
 *    < 300 ms du brief N'EST PAS TENU (307,0 ms mesurés, 320,8 au pire — voir
 *    DN_DEFAULT_DRAW_LINES dans dn_bootcfg.c, qui fait foi). SCREENS est retenu
 *    parce qu'il est le moins cher des deux, pas parce qu'il tient une promesse.
 *
 * ⚠️ « AUCUN des deux modèles ne fuit » était prouvé par un instrument AVEUGLE :
 *    `nav ab` mesurait la RAM interne et la PSRAM, alors que le tas LVGL est un
 *    pool STATIQUE en .bss (LV_MEM_ADR=0) où aucun lv_obj_create ne passe par
 *    heap_caps_malloc. Un « delta 0 o » s'y affichait à l'identique avec ou sans
 *    fuite. `nav ab` encadre désormais la série par lv_mem_monitor(), et la
 *    non-fuite est prouvée : 5 bascules screens<->rebuild enchaînées laissent le
 *    tas plat (15 204 / 12 168 / 15 180 / 12 180 / 15 208 o).
 * ⚠️ CE QUE L'ARBITRAGE NE DIT PAS : le vrai plancher n'est pas le modèle. Une
 *    transition redessine l'écran entier, soit 640/draw_lines flushes qui
 *    attendent CHACUN une trame — 10 trames à 26,7 ms = 267 ms à 64 lignes. Le
 *    modèle joue sur le temps de CONSTRUCTION ; le nombre de flushes
 *    synchronisés joue sur le reste, et il pèse plus lourd (voir AC5).
 */
static dn_nav_model_t s_nav = DN_NAV_SCREENS;
static volatile uint32_t s_nav_count;
/* Modèle SCREENS : les deux racines vivent en permanence. NULL en REBUILD — et
 * c'est ce qui distingue les deux modèles à l'oeil dans `ui`. */
static lv_obj_t *s_scr_dash;
static lv_obj_t *s_scr_detail;
/* Les labels du détail que le modèle SCREENS RÉÉCRIT au lieu de reconstruire.
 * En REBUILD ils sont recréés à chaque transition et ces pointeurs ne servent
 * qu'à ne pas les chercher dans l'arbre. */
static lv_obj_t *s_det_titre, *s_det_valeur, *s_det_minmax, *s_det_sec;

/*
 * ── LA BARRE HEURE/DATE (dn3-2) — DEUX POINTEURS NUS DE PLUS ─────────────────
 *
 * 🔴 CE SONT EXACTEMENT LES POINTEURS QUE LA REVUE dn3-1 A TROUVÉS DANGEREUX.
 *    Le tableau `s_wobj[]` est couvert PAR CONSTRUCTION (les trois sites de
 *    démontage bouclent sur DN_UI_METRIQUES), mais un pointeur NU doit être
 *    remis à NULL EXPLICITEMENT, un par un, aux MÊMES trois sites — c'est la
 *    forme du défaut n°1 de la revue dn3-1 (`s_demo` oublié à un seul site ⇒
 *    pointeur pendant, puis `lv_obj_delete` dessus). Ils sont donc ajoutés à
 *    `build_scene()`, à la branche REBUILD de `nav_appliquer()` et à
 *    `dn_ui_set_nav_model()`.
 *    ⚠️ Le QUATRIÈME site (branche SCREENS de `nav_appliquer`) ne les traite
 *       PAS, et c'est CORRECT : il ne détruit que ce qu'il a explicitement
 *       détruit (`s_bar`, `s_demo`) — le dashboard, lui, SURVIT en SCREENS,
 *       donc ses labels aussi. Y mettre la barre à NULL la rendrait morte alors
 *       qu'elle est vivante et affichée. Vérifié, pas supposé.
 */
static lv_obj_t *s_barre_heure, *s_barre_date;

/*
 * ── CE QUE LA BARRE AFFICHE QUAND ELLE NE SAIT PAS (W9) ──────────────────────
 * ⛔ JAMAIS UNE HEURE FAUSSE. Une barre qui affiche « 03:47 » après une coupure
 *    est PIRE qu'une barre qui se tait : le mensonge est indétectable. Et un
 *    « --:-- » MUET à côté d'une date d'apparence normale serait ambigu à son
 *    tour — la ligne de date porte donc le MOTIF, pas une date inventée.
 * Ces deux chaînes sont l'ÉTAT RÉEL au boot (aucune lecture n'a encore eu lieu),
 * pas une valeur de remplissage : elles servent d'initialiseur ET de sortie du
 * composeur, par le même #define, pour qu'elles ne puissent pas diverger.
 */
#define DN_UI_HEURE_INCONNUE "--:--"
#define DN_UI_DATE_INCONNUE "HEURE NON POSÉE"

/* Le texte COURANT de la barre. Il vit en RAM et SURVIT au démontage, comme
 * `s_wetat[]` survit à `s_wobj[]` : une reconstruction de scène le repose au
 * lieu de repartir d'un placeholder. C'est la règle anti-mensonge soldée par
 * dn3-1 — « les labels naissent vides et sont remplis par le MÊME code que la
 * réouverture » — appliquée à la barre. */
static char s_barre_h[16] = DN_UI_HEURE_INCONNUE;
static char s_barre_d[24] = DN_UI_DATE_INCONNUE;
static bool s_barre_fiable;

/*
 * 🔴 LA CADENCE DE LA BARRE (W2 / AC4), COMMUTABLE À CHAUD.
 * `false` = HH:MM (le régime de la maquette du brief, qui n'affiche PAS les
 * secondes) · `true` = HH:MM:SS. ⚠️ LA DOC ET LE CODE DOIVENT DIRE LA MÊME
 * VALEUR PAR DÉFAUT : en dn3-1, le `.h` annonçait `false` là où le code valait
 * `true`, et QUI REJOUAIT L'A/B MESURAIT DEUX FOIS LA MÊME BRANCHE. Défaut
 * ici = false, et `dn_ui.h`, `rtc`, le README et hardware/ disent tous false.
 *
 * ⚠️ Le régime n'est QU'UN FORMAT : c'est la détection de changement de texte
 *    qui décide de la ré-invalidation. En « minute », le texte ne change qu'au
 *    changement de minute — le calage sur la minute qu'AC4 exige est donc
 *    STRUCTUREL, pas confié à un timer libre qui pourrait retarder de 59 s.
 */
static bool s_barre_secondes;

/*
 * ── HISTORIQUE DE CETTE ZONE, CONSERVÉ PARCE QU'IL EXPLIQUE LA FORME ─────────
 * dn2-2 n'avait qu'UNE case réelle (CPU) et la codait en `i == 0` dans
 * build_scene. dn2-1 en a ajouté DEUX (TEMP./HUMIDITÉ) et a REFUSÉ d'empiler un
 * second ternaire : elle a généralisé en tableaux indexés par NUMÉRO DE CASE,
 * ce qui permet à `build_dashboard` de rester UNE SEULE boucle. dn3-1 hérite de
 * cette forme et n'y touche pas — elle remplace seulement le triplet
 * (texte, validité, pointeur) par le couple (état, pointeurs), voir ci-dessous.
 */
/*
 * ── L'ÉTAT DES SIX CASES — SÉPARÉ DE LEURS POINTEURS, ET C'EST LA PARADE ─────
 *
 * `s_wetat[]` SURVIT au démontage de la scène ; `s_wobj[]` NON, et il est remis
 * à zéro aux TROIS sites de démontage. Un pointeur de label qui survit à son
 * label + une tâche asynchrone = use-after-free ; la revue dn1-3 en a trouvé un
 * exactement là.
 *
 * 🔴 LE RÉGIME PAR DÉFAUT EST `DN_VAL_ABSENTE`, ET IL VAUT 0 — donc un tableau
 *    statique naît ABSENT, pas RÉEL. C'est la forme TYPÉE de l'initialiseur
 *    « -- » que dn2-1 avait perdu (CR du 2026-08-17) : un tableau statique vaut
 *    `""`, `build_dashboard` le posait tel quel, et les cases restaient VIDES
 *    ~5 s au boot — DÉFINITIVEMENT si la source ne répondait pas, pendant que
 *    deux fichiers journalisaient « les cases resteront « -- » ».
 *    Ici l'ancien défaut ne peut plus revenir : ce n'est plus une CHAÎNE qu'il
 *    faut penser à initialiser, c'est un ÉNUMÉRÉ dont le zéro est l'aveu
 *    d'ignorance, et `composer()` rend « -- » pour tout état absent SANS lire le
 *    texte. Toute case dit « -- » dès la toute première trame.
 *
 * ⚠️ Les six cases ont un état, y compris celles qu'on rend NUES à chaud par
 *    `widget nue <idx>` : une case nue reste ABSENTE tant qu'aucune source ne
 *    parle, ce qui est exactement ce qu'AC3 lui demande de dire. Ce qui la
 *    distingue d'un widget est sa FORME, pas son honnêteté.
 * 🔴 dn3-2 : GPU/RAM/RÉSEAU NE SONT PLUS LES NUES — elles portent le modèle et
 *    un mock déclaré (SIMULÉE + badge). Le témoin négatif d'AC8 est l'override
 *    `s_nue_force[]`, pas une liste de cases en dur.
 * Écrits sous le verrou LVGL, lus sous le même verrou (build_dashboard).
 */
static dn_widget_etat_t s_wetat[DN_UI_METRIQUES];
static dn_widget_t s_wobj[DN_UI_METRIQUES];

/*
 * Le widget de DÉMO d'AC1 (la 7e métrique fictive). Il vit sur l'ÉCRAN ACTIF,
 * pas dans la grille — donc il partage le sort du stimulus `anim` : une
 * reconstruction de scène ou une bascule d'écran le détruit ou le laisse
 * accroché à l'écran qu'on quitte.
 * ⚠️ SON OMBRE DOIT SUIVRE LA RÉALITÉ. Un `s_demo_on` resté vrai ferait annoncer
 *    « démo affichée » par la console pour un widget que personne ne voit —
 *    « exactement le défaut que la revue de dn1-3 a corrigé 21 fois ».
 */
static dn_widget_t s_demo;
static bool s_demo_on;

/*
 * ── L'A/B D'ICÔNE (W4) — UN INSTRUMENT, PAS UN RÉGLAGE PRODUIT ───────────────
 * `fan` (0xF863) est ABSENT du FontAwesome du dépôt : il est arrivé en 5.11 et
 * le `.woff` embarqué est antérieur (vérifié en le convertissant seul, pas
 * déduit d'une table). Quatre substituts sont embarqués ENSEMBLE, et l'icône se
 * commute à chaud : le choix est un CONSTAT OWNER sur la dalle, pas une
 * intuition — et un A/B qui exigerait trois reflashs coûterait trois
 * observations à l'owner pour un rendement qui baisse.
 * NULL = on garde celle du descripteur. Indexé par case, sans nommer de
 * métrique : le mécanisme sert à n'importe quelle icône, pas au ventilateur.
 */
static const char *s_icone_alt[DN_UI_METRIQUES];

static const struct {
    const char *nom;
    const char *glyphe;
} k_icones_alt[] = {
    /* ⚠️ LES QUATRE PREMIERS SONT LES CANDIDATS VENTILATEUR DE dn3-1, ET ILS
     *    RESTENT. La case n'est plus VENTILOS (D8), mais les retirer coûterait
     *    une VRAIE régénération de police : MESURÉ le 2026-08-18, `cog` (0xF013)
     *    est déjà un symbole amont, donc le ménage n'économiserait que 3 glyphes
     *    tout en faisant passer l'union `-r` de 68 à 65. Hors périmètre dn4-1. */
    {"sync-alt (2 fleches en rotation)", DN_ICONE_SYNC_ALT},
    {"wind (lignes de souffle)", DN_ICONE_WIND},
    {"cogs (deux engrenages)", DN_ICONE_COGS},
    {"cog (un engrenage)", DN_ICONE_COG},
    /* dn4-1 : l'icône RETENUE pour DISQUE, dans la liste pour que l'A/B puisse
     * y revenir sans reflasher. Gratuite (déjà dans les deux `.c`). */
    {"save (la disquette) — DISQUE", DN_ICONE_SAVE},
};
#define DN_UI_ICONES_ALT (sizeof(k_icones_alt) / sizeof(k_icones_alt[0]))

/*
 * ── W9 TRANCHÉ : L'OPACITÉ DÉFINITIVE DU VOILE EST 90/255 (35 %) ─────────────
 * dn1-4 l'avait posée à LV_OPA_50 (127) en écrivant « dn3-1 tranchera la valeur
 * définitive avec le reste de l'esthétique ». C'est fait, par A/B sur la dalle
 * et CONSTAT OWNER le 2026-08-17 : à 35 % « le PCB respire mieux » et le texte
 * reste lisible partout — y compris sur les cases-widgets, plus chargées qu'une
 * case nue, qui étaient le risque nommé par AC9.
 * ⚠️ Le voile ne coûte RIEN en latence : la mesure d'AC9 montre que seule la
 *    bascule opaque/translucide des CASES compte (127 et 178 donnent 321,5 et
 *    321,8 ms, soit le même chiffre). Cette valeur-ci est donc un choix
 *    PUREMENT esthétique, et c'est écrit pour que personne ne l'optimise.
 * Reste réglable à chaud (`widget voile <n>`) : dn3-3 refait l'identité visuelle
 * et aura besoin de rejouer l'arbitrage sans reflasher.
 */
static uint8_t s_voile_opa = 90;

/* ── Le mock (AC3, GÉNÉRALISÉ EN dn3-2 / W5) — forme ANNONCÉE, pas devinée ───
 *
 * Rampe triangulaire min -> max -> min, pas de 1 s (le tick du timer LVGL
 * existant). ⚠️ La valeur DOIT varier : un mock figé serait indiscernable d'un
 * affichage bloqué, et AC3 exige qu'un observateur puisse faire la différence.
 * La cadence, la plage et la forme sont imprimées par `widget` — RELUES de ces
 * constantes, jamais récitées ailleurs.
 *
 * 🔴 W5 — POURQUOI UN MOCK ET PAS DE VRAIES SOURCES POUR GPU/RAM/RÉSEAU.
 *    `dn_link` NE PORTE QU'UNE SEULE VALEUR (`s_valeur`, la CPU). Publier trois
 *    grandeurs de plus demanderait de généraliser `dn_link`, de passer le
 *    protocole en `ver=2` (une trame v2 tombe aujourd'hui en `rejets_version`,
 *    comptée) ET d'étendre l'agent Windows — ⚠️ sachant que
 *    `DN_LINK_LIGNE_MAX = 63` et qu'une trame multi-métriques dépasse vite.
 *    L'epic assigne ce travail NOMMÉMENT à dn4-1 (« extension ADDITIVE du
 *    protocole `$DN` de dn2-2 — la story reste close »).
 *    ⇒ Ici, les trois cases vivent en mock DÉCLARÉ : régime SIMULEE, ambre,
 *      badge « SIMULÉ ». ⛔ Aucun chiffre plausible sans source — les factices
 *      d'apparence réelle de dn1-4 (« 37 % », « 12,4 Go ») ont déjà été
 *      supprimés une fois, on ne les réintroduit pas par la bande.
 *
 * ⚠️ TOUTES LES PÉRIODES SONT PAIRES ET >= 2, et ce n'est pas cosmétique : la
 *    forme du triangle n'est bornée QUE dans ce cas (différé connu de dn3-1 —
 *    `demi = periode / 2`, et une période impaire fait que `pos` ne remonte
 *    jamais exactement à `demi`, donc `max` n'est jamais atteint).
 * ⚠️ Elles sont aussi PREMIÈRES ENTRE ELLES DEUX À DEUX autant que possible
 *    (14, 20, 26, 34).
 *
 * 🔴 CE QUE CES PÉRIODES FONT, ET CE QU'ELLES NE FONT PAS — relevé en revue le
 *    2026-08-18, et ce paragraphe affirmait l'inverse. Elles façonnent la
 *    TRAJECTOIRE de la valeur ; elles ne décalent PAS l'instant de mise à jour.
 *    Les quatre mocks sont pilotés par L'UNIQUE timer 1 Hz (`label_tick`) :
 *    **ils battent à l'unisson, chaque seconde, dans le même cycle LVGL.**
 *    Le dédoublonnage plus bas ne les désynchronise pas non plus — à chaque pas
 *    de chaque rampe l'écart dépasse l'unité affichée (GPU 34/13 ≈ 2,6 ·
 *    RAM 60/17 ≈ 3,5 · RÉSEAU 980/7 = 140 · VENT 800/10 = 80), donc il ne se
 *    déclenche JAMAIS.
 * ⇒ La ligne « mock on » de la table de décomposition d'AC8 (§16.1) contient
 *   donc DÉJÀ quatre mises à jour par cycle. Ce n'est pas le régime désynchronisé
 *   qu'elle prétendait chiffrer, et il faut le lire ainsi.
 * ⚠️ Les périodes restent premières entre elles pour que les VALEURS ne se
 *    rephasent pas — c'est utile à l'œil, pas au coût.
 * ⛔ ON NE LES DÉPHASE PAS : décaler les ticks changerait le régime sur lequel
 *    tout §16 a été mesuré, et invaliderait des chiffres publiés pour corriger
 *    une étiquette. On corrige l'étiquette.
 * ⚠️ `widget rafale` garde son sens : il ajoute CPU, AMBIANCE et la barre au
 *    même cycle — les six, pas seulement les quatre mocks.
 */
/*
 * 🔴 dn4-1 : CES TROIS NOMBRES NE BOUGENT PAS, ET C'EST UN CHOIX MOTIVÉ.
 *    L'index 4 change de métrique (VENTILOS -> DISQUE, D8) et donc d'unité
 *    (tr/min -> Mo/s). La tentation était de recaler la rampe sur ce que la tour
 *    produit réellement (0 à 268 Mo/s, mesuré). ⛔ ON NE LE FAIT PAS :
 *      · la ligne « mock on / groupage on » de §16.1 EST la baseline d'AC7, et
 *        elle doit rester REJOUABLE à l'identique — même nombre de chiffres
 *        (4), même période (20 s), donc même géométrie de texte ;
 *      · 800 à 1 600 Mo/s reste PLAUSIBLE en Mo/s : c'est la plage d'un NVMe,
 *        et un mock doit être plausible sans être crédible — le badge
 *        « SIMULÉ » et l'ambre s'occupent du reste.
 *    ⚠️ Un mock est un INSTRUMENT. Le recaler « pour faire joli » aurait
 *       invalidé un chiffre publié afin d'améliorer une apparence.
 */
#define DN_MOCK_MIN 800
#define DN_MOCK_MAX 1600
#define DN_MOCK_PERIODE_S 20

/* Ce que la ligne secondaire d'un mock raconte. Nommé par INTENTION, pas par
 * index : la table reste lisible et le tick n'a aucun `if (i == RAM)`. */
typedef enum {
    DN_SEC_SIMULE = 0,  /* « valeur SIMULÉE — aucun capteur » */
    DN_SEC_RAM_GO,      /* « 12,1 / 32 Go » — verbatim addendum §1 */
    DN_SEC_RESEAU_DUPLEX, /* « v 985  ^ 48 » — verbatim addendum §1 */
} dn_sec_forme_t;

typedef struct {
    bool actif;            /* cette case a-t-elle un mock ? */
    int32_t min, max;      /* en UNITÉS AFFICHÉES, pas en dixièmes */
    uint32_t periode_s;    /* PAIRE et >= 2 — voir ci-dessus */
    dn_sec_forme_t sec;
} dn_mock_t;

/* ⚠️ CPU et AMBIANCE n'y sont PAS, et c'est structurel : elles ont des sources
 * RÉELLES (`dn_link`, `dn_capteurs`). Un mock sur une case réelle serait le
 * mensonge d'interface exact que D6 rend visible — « PC éteint, une seule case
 * sur six reste vivante » doit SE VOIR. */
static const dn_mock_t k_mock[DN_UI_METRIQUES] = {
    [DN_UI_CASE_GPU] = {true, 38, 72, 26, DN_SEC_SIMULE},
    [DN_UI_CASE_RAM] = {true, 18, 78, 34, DN_SEC_RAM_GO},
    [DN_UI_CASE_RESEAU] = {true, 5, 985, 14, DN_SEC_RESEAU_DUPLEX},
    [DN_UI_CASE_DISQUE] = {true, DN_MOCK_MIN, DN_MOCK_MAX, DN_MOCK_PERIODE_S,
                           DN_SEC_SIMULE},
};

/*
 * ── W7 TRANCHÉ (dn4-1) : LE MOCK EST COUPÉ PAR DÉFAUT, PAS SUPPRIMÉ ──────────
 *
 * 🔴 `false` DEPUIS dn4-1 — c'était `true` depuis dn3-1. Les quatre cases
 *    mockées ont désormais des sources RÉELLES ; laisser le générateur armé
 *    ferait cohabiter un chiffre inventé et une mesure sur le même dashboard,
 *    et le brief demande « ZÉRO badge SIMULÉ » en régime nominal.
 *
 * ⛔ MAIS ON NE LE SUPPRIME PAS, ET LE MOTIF EST CHIFFRÉ : la ligne
 *    « mock on / groupage on » de §16.1 (10,18 % CPU · 3,47 flush/cycle ·
 *    120 756 px/cycle · duty 6,7 %) est LA BASELINE à laquelle AC7 confronte le
 *    régime réel. Retirer le mock du firmware rendrait cette ligne INJOUABLE et
 *    la comparaison impossible — on aurait publié un chiffre sans pouvoir le
 *    confronter à celui qu'il remplace, exactement la faute que dn3-2 a payée
 *    trois fois. `widget mock on` reste donc la commande qui ARME l'instrument.
 *
 * ⚠️ CONSÉQUENCE NON DEMANDÉE, ÉCRITE D'AVANCE : PC éteint, l'écran passe de
 *    « quatre cases qui bougent » à CINQ cases sur six à « -- ». Ce n'est pas
 *    une régression, c'est l'honnêteté qui arrive AVANT son remède (dn4-3).
 *    Corollaire chiffré : au repos sans agent, la charge du module tombe de
 *    10,18 % à ~1,49 % (§16.1 ligne 2) — le mock coûtait sept fois le module
 *    qu'il décorait.
 */
static bool s_mock_on = false;
/* 🔴 D1 (revue 2026-08-18) : « cette case porte une POUSSÉE manuelle », donc le
 * tick du mock coupé ne doit pas la révoquer. Sans ce drapeau, chaque
 * `widget pousser 4` coûtait DEUX redessins au lieu d'un et polluait le cas (a′)
 * de §15.5 — le tick était un second écrivain sur la case mesurée.
 * ⚠️ dn3-2 : GÉNÉRALISÉ AUX SIX CASES. Le défaut était scopé à VENTILOS parce
 *    qu'elle était le seul mock ; avec quatre mocks, un drapeau unique
 *    laisserait les trois autres se faire révoquer — le même défaut, déplacé. */
static bool s_poussee[DN_UI_METRIQUES];

/* Le nombre de cases poussées par la dernière rafale d'AC8 — RELU, jamais récité.
 * ⛔ `s_rafale_cycles` A ÉTÉ SUPPRIMÉ le 2026-08-19 : voir `dn_ui_rafale()`, il ne
 *    pouvait rendre que sa valeur de succès. La fusion se prouve par `flush`. */
static uint32_t s_rafale_n;
/* Dernière zone touchée — la preuve d'AC3, lue par la console. */
static volatile int s_dernier_tap = DN_UI_ZONE_AUCUNE;
static volatile uint32_t s_taps;
static volatile uint32_t s_menu_taps;

/* Compteurs — 32 bits, écrits par la tâche LVGL, lus par le REPL. Voir dn_ui.h
 * pour ce que cette absence de verrou garantit et ce qu'elle ne garantit pas. */
static volatile uint32_t s_n_flush, s_n_cycles, s_px, s_copie_us, s_attente_us;
static volatile uint32_t s_max_px, s_max_copie_us, s_timeouts;
/* Flushes NO-OP du mode direct (early return : aire comptée, aucun µs). Compté
 * À PART (revue) : les inclure au dénominateur diluait les moyennes copie/attente
 * dans le mode même qui a servi à tester l'hypothèse 5 de §10.5. */
static volatile uint32_t s_n_noop;

/* ── Noms des modes ───────────────────────────────────────────────────────── */

const char *dn_flush_sync_name(dn_flush_sync_t m)
{
    switch (m) {
    case DN_FLUSH_SYNC_OFF:
        return "off";
    case DN_FLUSH_SYNC_VSYNC:
        return "vsync";
    case DN_FLUSH_SYNC_FBDONE:
        return "fbdone";
    default:
        return "?";
    }
}

bool dn_flush_sync_from_name(const char *nom, dn_flush_sync_t *out)
{
    for (int i = 0; i < DN_FLUSH_SYNC_COUNT; i++) {
        if (strcasecmp(nom, dn_flush_sync_name((dn_flush_sync_t)i)) == 0) {
            *out = (dn_flush_sync_t)i;
            return true;
        }
    }
    return false;
}

const char *dn_flush_path_name(dn_flush_path_t p)
{
    switch (p) {
    case DN_FLUSH_PATH_BITMAP:
        return "bitmap";
    case DN_FLUSH_PATH_DIRECT:
        return "direct";
    default:
        return "?";
    }
}

bool dn_flush_path_from_name(const char *nom, dn_flush_path_t *out)
{
    for (int i = 0; i < DN_FLUSH_PATH_COUNT; i++) {
        if (strcasecmp(nom, dn_flush_path_name((dn_flush_path_t)i)) == 0) {
            *out = (dn_flush_path_t)i;
            return true;
        }
    }
    return false;
}

dn_flush_path_t dn_ui_get_path(void) { return s_path; }

esp_err_t dn_ui_set_path(dn_flush_path_t p)
{
    if (p >= DN_FLUSH_PATH_COUNT) {
        return ESP_ERR_INVALID_ARG;
    }
    if (p == DN_FLUSH_PATH_DIRECT && dn_display_num_fbs() != 1) {
        /* Refus explicite plutôt que dessin dans le mauvais tampon : à plusieurs
         * framebuffers, le tampon de DESSIN n'est pas celui que la DMA lit, et
         * écrire dedans sans passer par la bascule du driver n'afficherait
         * simplement jamais rien. Un défaut silencieux de plus. */
        ESP_LOGE(TAG,
                 "chemin « direct » refusé : num_fbs=%d. Il n'a de sens qu'à UN "
                 "framebuffer, où le tampon de dessin EST le tampon visible.",
                 dn_display_num_fbs());
        return ESP_ERR_INVALID_STATE;
    }
    s_path = p;
    return ESP_OK;
}

/* ── Le flush ─────────────────────────────────────────────────────────────── */

/*
 * W8 — élargit CHAQUE aire invalidée à la pleine largeur de la dalle. Voir le
 * long commentaire à l'enregistrement, dans dn_ui_init().
 * ⚠️ INERTE par défaut : c'est un INSTRUMENT d'AC9, pas un réglage produit. Un
 *    levier non essayé doit rester non essayé tant qu'on n'a pas son chiffre.
 */
static void bandes_event_cb(lv_event_t *e)
{
    if (!s_bandes) {
        return;
    }
    lv_area_t *a = lv_event_get_invalidated_area(e);
    if (!a) {
        return;
    }
    a->x1 = 0;
    a->x2 = DN_LCD_H_RES - 1;
}

static void dn_ui_flush(lv_display_t *disp, const lv_area_t *area, uint8_t *px_map)
{
    uint32_t w = (uint32_t)(area->x2 - area->x1 + 1);
    uint32_t h = (uint32_t)(area->y2 - area->y1 + 1);

    /*
     * L'ATTENTE ET LA COPIE SONT CHRONOMÉTRÉES SÉPARÉMENT — sinon le coût annoncé
     * du flush inclurait le temps passé à ne rien faire, et « le rafraîchissement
     * partiel coûte 27 ms » se lirait comme un problème de bande passante alors
     * que ce serait la synchro qui attend sa trame. Deux chiffres, deux causes.
     */
    if (s_direct_mode && !lv_display_flush_is_last(disp)) {
        /*
         * EN MODE DIRECT, `px_map` EST L'UN DES DEUX FRAMEBUFFERS : LVGL y a
         * déjà écrit, il n'y a rien à recopier. Tant que ce n'est pas le dernier
         * appel du cycle, la seule chose à faire est de compter et de rendre la
         * main — la bascule ne se joue qu'une fois, quand tout est dessiné.
         * Rendre la trame à chaque zone sale afficherait un écran à moitié
         * rafraîchi, c'est-à-dire fabriquerait le déchirement qu'on vient
         * d'éliminer.
         */
        s_n_flush++;
        s_n_noop++;
        s_px += w * h;
        if (w * h > s_max_px) {
            s_max_px = w * h;
        }
        lv_display_flush_ready(disp);
        return;
    }

    int64_t t0 = esp_timer_get_time();
    switch (s_sync) {
    case DN_FLUSH_SYNC_VSYNC:
        /* On veut le PROCHAIN retour vertical : vider d'abord. Rien ici ne
         * provoque l'événement, donc l'idiome « vider puis attendre » est le bon
         * (celui de dn_measure_wait_vsync, pas celui de wait_frame_done). */
        dn_measure_vsync_flush(s_vsync_sub);
        if (!dn_measure_vsync_wait(s_vsync_sub, 100)) {
            s_timeouts++;
        }
        break;
    case DN_FLUSH_SYNC_FBDONE:
        dn_measure_arm_frame_done();
        if (!dn_measure_wait_frame_done(100)) {
            s_timeouts++;
        }
        break;
    case DN_FLUSH_SYNC_OFF:
    default:
        break;
    }
    int64_t t1 = esp_timer_get_time();

    if (s_direct_mode) {
        /*
         * LA BASCULE. `px_map` pointe dans l'un des framebuffers du driver, donc
         * `draw_bitmap` prend la branche « le draw buffer FAIT PARTIE du frame
         * buffer » : il ne recopie rien, il change `cur_fb_index` et réaccroche
         * la queue des liens DMA. Zéro octet copié — c'est TOUT l'intérêt du
         * double tampon, et c'est ce qui supprime l'écriture CPU dans le tampon
         * que la DMA balaie (la cause mesurée du clignotement à 1 FB).
         */
        esp_lcd_panel_draw_bitmap(s_panel, 0, 0, DN_LCD_H_RES, DN_LCD_V_RES,
                                  px_map);
        /* ⚠️ On arme le recalage NOUS-MÊMES : ce chemin court-circuite
         * `dn_display_present()`, qui est l'endroit où l'armement vit d'habitude.
         * L'oublier ici rendrait le double tampon inutilisable sous LVGL alors
         * qu'il vient d'être prouvé réparable — et le symptôme serait « ça
         * marche en `scene`, pas en LVGL », le plus trompeur qui soit. */
        dn_recal_arm();
    } else if (s_path == DN_FLUSH_PATH_DIRECT) {
        /*
         * Écriture DIRECTE dans le framebuffer visible, puis resynchronisation
         * des SEULES lignes salies. À num_fbs=1, `dn_display_draw_buffer()` rend
         * le tampon que la DMA lit : il n'y a pas de bascule à faire, donc rien
         * à demander au driver.
         *
         * Le gain visé n'est PAS la copie (elle est identique, mêmes octets)
         * mais le parcours de cache : h x 960 octets au lieu des 614 400 que
         * `draw_bitmap` resynchronise systématiquement.
         */
        uint16_t *fb = dn_display_draw_buffer();
        const uint16_t *src = (const uint16_t *)px_map;
        for (uint32_t y = 0; y < h; y++) {
            memcpy(fb + (size_t)(area->y1 + (int)y) * DN_LCD_H_RES + area->x1,
                   src + (size_t)y * w, (size_t)w * 2);
        }
        /* UNALIGNED : la première ligne sale ne tombe pas sur une frontière de
         * ligne de cache, et l'exiger ferait refuser l'appel avec
         * ESP_ERR_INVALID_ARG — le driver lui-même pose ce drapeau ici. */
        esp_cache_msync(fb + (size_t)area->y1 * DN_LCD_H_RES,
                        (size_t)h * DN_LCD_H_RES * 2,
                        ESP_CACHE_MSYNC_FLAG_DIR_C2M |
                            ESP_CACHE_MSYNC_FLAG_UNALIGNED);
    } else {
        /* ⚠️ `esp_lcd_panel_draw_bitmap` prend des bornes de fin EXCLUSIVES,
         * alors que `lv_area_t` a des bornes INCLUSIVES. Le +1 n'est pas une
         * marge : sans lui, la dernière colonne et la dernière ligne de chaque
         * zone sale ne seraient jamais recopiées, et le défaut se verrait comme
         * un liseré rémanent d'un pixel — le genre d'artefact qu'on attribue à
         * la dalle. */
        esp_lcd_panel_draw_bitmap(s_panel, area->x1, area->y1, area->x2 + 1,
                                  area->y2 + 1, px_map);
    }
    int64_t t2 = esp_timer_get_time();

    uint32_t px = w * h;
    uint32_t copie = (uint32_t)(t2 - t1);
    s_n_flush++;
    s_px += px;
    s_copie_us += copie;
    s_attente_us += (uint32_t)(t1 - t0);
    if (px > s_max_px) {
        s_max_px = px;
    }
    if (copie > s_max_copie_us) {
        s_max_copie_us = copie;
    }
    if (lv_display_flush_is_last(disp)) {
        s_n_cycles++;
        s_first_frame = true;
        /*
         * FIN DU CHRONOMÈTRE D'AC5. C'est ici, et pas ailleurs : le dernier flush
         * du cycle est le moment où la nouvelle vue est ENTIÈREMENT dans le
         * framebuffer. Un no-op quand rien n'est armé (un test sur un booléen),
         * pour ne rien coûter au chemin chaud des 37,40 trames par seconde.
         *
         * ⚠️ Ce que ce point d'arrêt N'INCLUT PAS : la trame qu'il reste à la DMA
         *    pour peindre ce qu'on vient d'écrire (jusqu'à 26,7 ms). Déclaré,
         *    jamais ajouté en douce à la mesure.
         */
        dn_touch_latence_stop();
    }

    lv_display_flush_ready(disp);
}

/* ── La scène ─────────────────────────────────────────────────────────────── */

/* Le label de la vue AFFICHÉE — le seul qu'il soit juste de mettre à jour. */
static lv_obj_t *label_courant(void)
{
    return s_vue == DN_VUE_DETAIL ? s_label_det : s_label_dash;
}

static void mock_tick_nolock(void);

static void label_tick(lv_timer_t *t)
{
    (void)t;
    /*
     * ── LE MOCK VENTILOS BAT ICI, ET C'EST UN CHOIX ÉCRIT (AC3) ──────────────
     * Pas de tâche dédiée : le patron `dn_link`/`dn_capteurs` en réclame une
     * quand le travail peut DORMIR (I²C, série). Produire un nombre ne dort pas.
     * Une tâche coûterait une pile, un handle et un point de défaillance de plus
     * au boot — pour rien.
     * ⚠️ ON EST DÉJÀ SOUS LE VERROU LVGL ici : le portage le prend autour de
     *    `lv_timer_handler()`. D'où l'appel à la variante `_nolock`, qui est le
     *    contrat de `dn_widget`. (Le mutex du portage est RÉCURSIF —
     *    `esp_lvgl_port.c:77` — donc un lock imbriqué serait sûr ; on ne s'appuie
     *    pas dessus, on l'écrit pour que personne n'ait à le redécouvrir.)
     * ⚠️ AVANT le retour anticipé ci-dessous : le label vivant est MASQUÉ par
     *    défaut depuis dn1-4 et son pointeur est NULL en REBUILD vue détail.
     *    Mettre le mock après aurait fait un mock qui s'arrête quand on ouvre un
     *    détail — un « affichage figé » fabriqué par l'instrumentation.
     */
    mock_tick_nolock();

    lv_obj_t *s_label = label_courant();
    if (!s_label) {
        return;
    }
    /*
     * TEMPS ABSOLU, jamais un compteur incrémenté. Un `s++` dans un timer de
     * 1 000 ms dérive de tout ce que le timer prend de retard — et il en prend,
     * puisque le cycle LVGL tourne à 33 ms et qu'un flush synchronisé peut
     * mordre dessus. Ici la valeur affichée est dérivée de l'horloge : elle est
     * juste même si le timer se réveille en retard, et elle reste confrontable au
     * battement `up N s` du log, qui est lui aussi une cadence indépendante.
     */
    uint32_t s = (uint32_t)(esp_timer_get_time() / 1000000);
    char buf[24];
    snprintf(buf, sizeof(buf), "%" PRIu32 " s", s);
    lv_label_set_text(s_label, buf);
}

static void bar_set_x(void *var, int32_t v)
{
    lv_obj_set_x((lv_obj_t *)var, v);
}

/* ── Le fond, commun aux deux vues ────────────────────────────────────────── */

/* Pose le fond (Living PCB ou panneau d'alerte) sur `scr`. Extrait de l'ancien
 * `build_scene()` sans changement de comportement : les deux vues de dn1-4 se
 * dessinent PAR-DESSUS ce fond, qui reste l'image de dn1-2. L'esthétique des
 * cases n'est pas un sujet de cette story (dn3-1 la portera). */
static void fond_poser(lv_obj_t *scr)
{
    lv_obj_set_style_bg_color(scr, lv_color_black(), 0);
    lv_obj_set_style_bg_opa(scr, LV_OPA_COVER, 0);
    /* Pas de barre de défilement sur un écran qui ne défile pas : sinon LVGL en
     * dessine une au moindre objet qui touche le bord, et elle s'invaliderait
     * avec lui. */
    lv_obj_set_scrollbar_mode(scr, LV_SCROLLBAR_MODE_OFF);
    lv_obj_clear_flag(scr, LV_OBJ_FLAG_SCROLLABLE);

    const uint16_t *px = s_bg_psram ? (const uint16_t *)s_bg_psram
                                    : dn_asset_pixels();
    if (px) {
        s_bg_dsc.header.magic = LV_IMAGE_HEADER_MAGIC;
        /* RGB565 NATIF, NON COMPRESSÉ : le format du framebuffer et celui de
         * l'asset sont les mêmes, donc chaque re-blit du fond sous le label est
         * une COPIE et non un décodage. C'est la condition qui rend le coût
         * d'AC3 prévisible. */
        s_bg_dsc.header.cf = LV_COLOR_FORMAT_RGB565;
        s_bg_dsc.header.w = DN_LCD_H_RES;
        s_bg_dsc.header.h = DN_LCD_V_RES;
        s_bg_dsc.header.stride = DN_LCD_H_RES * 2;
        s_bg_dsc.data_size = DN_FB_BYTES;
        s_bg_dsc.data = (const uint8_t *)px;

        /* LOCAL, et pas un statique (revue dn1-4) : l'image appartient à son
         * écran, qui la détruit avec lui. Le `s_img` global qu'on gardait était
         * écrit six fois et lu ZÉRO — en modèle SCREENS, `fond_poser()` étant
         * appelé pour les deux écrans, il finissait de toute façon par désigner
         * l'image de l'écran qu'on ne regarde pas. */
        lv_obj_t *img = lv_image_create(scr);
        lv_image_set_src(img, &s_bg_dsc);
        lv_obj_set_pos(img, 0, 0);

        /*
         * ── LE VOILE, demandé par l'owner le 2026-08-16 ──────────────────────
         * Constat : « le fond prend trop, il masque les détails (des cadres
         * aussi) ». Le Living PCB est une photo très contrastée, et du texte
         * blanc posé dessus se perd dans ses pistes claires.
         *
         * Un FLOU aurait été le réflexe, et il est écarté : LVGL n'en a pas qui
         * soit gratuit, et il faudrait le recalculer à chaque zone invalidée —
         * sur un budget de transition déjà à 267 ms. Un aplat noir translucide
         * fait le même travail perceptif (baisser le contraste du fond pour que
         * le premier plan ressorte) pour le prix d'un rectangle.
         *
         * ⚠️ NON CLIQUABLE : il couvre tout l'écran. Cliquable, il volerait
         *    chaque tap destiné aux cases — et « toute la case est la zone
         *    tactile » deviendrait faux à cause d'un élément décoratif.
         * ⚠️ L'opacité reste PARTIELLE : le PCB est l'identité visuelle du
         *    produit, on l'atténue, on ne l'efface pas.
         * ✅ dn3-1 a TRANCHÉ la valeur définitive (W9) et l'a rendue RÉGLABLE
         *    à chaud (`widget voile <0..255>`) pour que l'arbitrage soit un
         *    constat owner sur la dalle et non un choix sur le papier. La
         *    valeur retenue vit dans `s_voile_opa`, et la console la RELIT —
         *    elle ne la récite pas depuis une constante.
         */
        lv_obj_t *voile = lv_obj_create(scr);
        lv_obj_remove_style_all(voile);
        lv_obj_set_pos(voile, 0, 0);
        lv_obj_set_size(voile, DN_LCD_H_RES, DN_LCD_V_RES);
        lv_obj_clear_flag(voile, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_clear_flag(voile, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_set_style_bg_color(voile, lv_color_black(), 0);
        lv_obj_set_style_bg_opa(voile, s_voile_opa, 0);
    } else {
        /*
         * ── LE PANNEAU « ASSET ABSENT » SURVIT À L'INTÉGRATION (AC1) ─────────
         * Il existait en dn1-2, dessiné à la main dans le framebuffer par
         * dn_patterns. LVGL redessine l'écran entier au premier cycle : ce
         * panneau-là aurait été effacé sans bruit, et une partition d'assets
         * corrompue aurait produit un écran noir silencieux — exactement ce que
         * dn_asset.h promet de ne jamais faire. On le REDESSINE donc en LVGL.
         */
        lv_obj_set_style_bg_color(scr, lv_color_hex(0x7f0000), 0);
        lv_obj_t *t = lv_label_create(scr);
        lv_obj_set_style_text_font(t, &dn_font_28, 0);
        lv_obj_set_style_text_color(t, lv_color_white(), 0);
        lv_label_set_text(t, "ASSET ABSENT");
        lv_obj_align(t, LV_ALIGN_CENTER, 0, -30);

        lv_obj_t *r = lv_label_create(scr);
        lv_obj_set_style_text_color(r, lv_color_white(), 0);
        lv_label_set_text(r, esp_err_to_name(s_asset_err));
        lv_obj_align(r, LV_ALIGN_CENTER, 0, 20);
    }

}

/*
 * ── LE LABEL VIVANT DE dn1-3 SURVIT, INCHANGÉ, ET C'EST VOLONTAIRE ───────────
 *
 * Même géométrie (260x44), même police (montserrat 28), même place (centre),
 * même fond transparent. Ce n'est PAS un élément de la spec UI : c'est
 * l'INSTRUMENT qui a produit le régime de référence de dn1-3 (15 892 px par mise
 * à jour, 1,00 flush/cycle, 0,9 % de CPU). Le déplacer ou le redimensionner
 * rendrait les budgets d'AC8 incomparables à ceux de la marche du dessous — et
 * un budget qu'on ne peut pas comparer ne sert à rien.
 *
 * ⚠️ Il est donc MASQUÉ par défaut dès qu'une vue produit est affichée (il
 *    recouvrirait les cases RAM/RESEAU), et `ui label on` le rallume pour
 *    rejouer dn1-3 à l'identique. Le chevauchement assumé de ce moment-là est
 *    celui d'un instrument de campagne, pas d'un écran de produit.
 */
static void label_poser(lv_obj_t *scr, lv_obj_t **slot)
{
    lv_obj_t *s_label = lv_label_create(scr);
    *slot = s_label;
    lv_obj_set_style_text_font(s_label, &dn_font_28, 0);
    lv_obj_set_style_text_color(s_label, lv_color_white(), 0);
    /* Fond du label TRANSPARENT, délibérément. Un aplat opaque derrière le texte
     * supprimerait le re-blit du fond sous la zone invalidée — c'est-à-dire
     * exactement le travail qu'AC3 veut chiffrer et qu'AC2 veut voir ne pas
     * frémir. Le rendre opaque rendrait la mesure facile et fausse. */
    lv_obj_set_style_bg_opa(s_label, LV_OPA_TRANSP, 0);
    lv_obj_set_style_text_align(s_label, LV_TEXT_ALIGN_CENTER, 0);
    lv_label_set_long_mode(s_label, LV_LABEL_LONG_MODE_CLIP);
    lv_obj_set_size(s_label, DN_UI_LABEL_W, DN_UI_LABEL_H);
    lv_obj_align(s_label, LV_ALIGN_CENTER, 0, 0);
    lv_label_set_text(s_label, "0 s");
    /* Le label ne capte AUCUN toucher : sinon il volerait le tap destiné aux
     * cases qu'il recouvre quand on le rallume, et « toute la case est la zone
     * tactile » deviendrait faux par accident. */
    lv_obj_clear_flag(s_label, LV_OBJ_FLAG_CLICKABLE);
    if (!s_label_shown) {
        lv_obj_add_flag(s_label, LV_OBJ_FLAG_HIDDEN);
    }
}

/* ── Les zones tactiles ───────────────────────────────────────────────────── */

/*
 * Un conteneur cliquable, nu. C'est LA brique de dn1-4 : ni widget, ni style de
 * produit — une géométrie qui reçoit le doigt.
 *
 * ⚠️ LES DEUX DRAPEAUX QUI DÉCIDENT SI « TOUTE LA CASE » EST VRAIE :
 *    - CLICKABLE sur le CONTENEUR, et les labels enfants laissés NON cliquables :
 *      LVGL remonte alors au premier ancêtre cliquable, donc un tap sur le texte
 *      comme un tap dans un coin vide arrivent au même endroit.
 *    - SCROLLABLE RETIRÉ. `lv_obj_create()` le pose par défaut, et un conteneur
 *      scrollable AVALE le geste dès que le doigt bouge de quelques pixels : le
 *      tap marcherait au centre, en appuyant bien droit, et raterait au bord ou
 *      sur un doigt qui roule. C'est exactement le défaut que la preuve « aux
 *      coins » d'AC3 est censée attraper — autant ne pas le fabriquer.
 */
static lv_obj_t *zone_creer(lv_obj_t *parent, int x, int y, int w, int h,
                            lv_event_cb_t cb, void *user)
{
    /* 🔴 LE CORPS A DÉMÉNAGÉ DANS `dn_widget` (dn3-1), ET C'EST LE POINT.
     * Les deux drapeaux qui décident si « toute la case est la zone tactile »
     * est vraie — prouvée à 4 px du bord en dn1-4 — étaient DUPLIQUÉS entre
     * `zone_creer` et `panneau`. Le widget en aurait fait une troisième copie.
     * Ils n'ont plus qu'UNE définition, et c'est elle que toutes les zones
     * tactiles du firmware traversent : cases nues, MENU, retour.
     * L'aplat translucide suit le même chemin, pour que l'A/B d'opacité d'AC9
     * ne puisse pas oublier la moitié de l'écran. */
    return dn_widget_zone_creer(parent, x, y, w, h, cb, user);
}

/*
 * Le même aplat que `zone_creer`, mais SANS la zone tactile — pour porter du
 * texte, pas pour recevoir le doigt.
 *
 * Il existe parce que la première version du détail posait ses labels
 * DIRECTEMENT sur le fond : constat owner du 2026-08-16, « les titres et textes
 * en bas ne sont pas encore bien lisibles ». Les cases du dashboard, elles,
 * avaient leur aplat depuis le début — d'où la différence de lisibilité entre
 * les deux écrans, qui n'avait rien d'esthétique et tout de structurel.
 */
static lv_obj_t *panneau(lv_obj_t *parent, int x, int y, int w, int h)
{
    return dn_widget_panneau(parent, x, y, w, h);
}

static lv_obj_t *texte(lv_obj_t *parent, const char *s, const lv_font_t *font,
                       lv_color_t couleur, int x, int y)
{
    return dn_widget_texte(parent, s, font, couleur, x, y);
}

/* ── Navigation : les callbacks ───────────────────────────────────────────── */

/*
 * ⚠️ POURQUOI TOUTE TRANSITION PASSE PAR `lv_async_call()` ET JAMAIS DIRECTEMENT.
 *
 * Ces callbacks tournent DANS l'envoi d'événement LVGL, sur un objet qui
 * appartient à l'arbre que la transition va DÉTRUIRE (`lv_obj_clean`, ou le
 * chargement d'un autre écran). Supprimer l'objet qui est en train de recevoir
 * son propre événement est un use-after-free — le même genre que celui trouvé en
 * revue de dn1-3 sur `ui bg flash`. `lv_async_call()` diffère le travail au tour
 * de boucle suivant, hors du contexte d'événement : c'est la parade prévue par
 * LVGL, pas un contournement.
 *
 * Conséquence ASSUMÉE sur la mesure : le délai jusqu'au prochain tour de boucle
 * (jusqu'à ~33 ms) est DANS la latence d'AC5, parce qu'il est dans le vécu de
 * l'utilisateur.
 */
static bool nav_appliquer(int cible, int64_t t_clic);

/*
 * ── L'INSTANT DU CLIC VOYAGE AVEC SON CLIC (correctif de revue dn1-4) ────────
 *
 * Il tenait avant dans UN SEUL global, que tout tap suivant écrasait avant que
 * l'async du précédent ne s'exécute. Deux taps sur deux cases séparés de moins
 * d'un tour de boucle (~33 ms, la fenêtre même que lv_async_call assume) et la
 * PREMIÈRE transition était chronométrée depuis le SECOND clic : latence
 * sous-estimée, ou `dt < 0` et l'échantillon abandonné en silence. La moyenne
 * publiée par AC5 était donc calculée sur un échantillon biaisé vers le bas,
 * sans que rien dans la sortie ne permette de s'en apercevoir.
 *
 * LVGL ne transporte qu'un pointeur, et allouer un int64 par tap mettrait une
 * allocation dans le chemin chaud. On encode donc un NUMÉRO DE SLOT dans les
 * bits hauts du paramètre, et l'horodatage vit dans un petit anneau. Quatre
 * slots : lv_async_call n'exécute jamais plus d'un tour de retard, quatre taps
 * en vol simultanés n'arrivent pas au doigt.
 */
#define DN_NAV_PENDING 4
static volatile int64_t s_clic_ts[DN_NAV_PENDING];
static uint32_t s_clic_seq;
/* Asyncs refusées par LVGL (file pleine, tas saturé) : un tap qui n'ouvrira
 * jamais rien ne doit PAS être compté comme un tap — sinon `touch trace` valide
 * une zone tactile morte, et c'est la preuve d'AC3 qui ment. */
static volatile uint32_t s_async_refus;

/* Paramètre d'async : ((slot+1) << 8) | cible. Jamais NULL, ce qui garde
 * l'encodage lisible dans un log et distinguable d'un paramètre oublié. */
static void *nav_param(int cible, int64_t t_clic)
{
    uint32_t slot = s_clic_seq++ % DN_NAV_PENDING;
    s_clic_ts[slot] = t_clic;
    return (void *)(intptr_t)(((slot + 1) << 8) | (uint32_t)(cible & 0xFF));
}

static void nav_async(void *param)
{
    uintptr_t p = (uintptr_t)param;
    /* Encodage de la cible : 0 = retour au dashboard, 1..6 = métrique p-1. */
    int cible = (int)(p & 0xFF);
    int slot = (int)((p >> 8) & 0xFF) - 1;
    int64_t t_clic = (slot >= 0 && slot < DN_NAV_PENDING) ? s_clic_ts[slot]
                                                          : esp_timer_get_time();
    nav_appliquer(cible, t_clic);
}

static void on_case_clic(lv_event_t *e)
{
    int64_t t_clic = esp_timer_get_time();
    intptr_t idx = (intptr_t)lv_event_get_user_data(e);
    /* Le retour de lv_async_call était JETÉ : sur file pleine, le compteur de
     * taps montait quand même et la zone passait pour vivante. */
    if (lv_async_call(nav_async, nav_param((int)idx + 1, t_clic)) != LV_RESULT_OK) {
        s_async_refus++;
        return;
    }
    s_dernier_tap = (int)idx;
    s_taps++;
}

static void on_retour_clic(lv_event_t *e)
{
    (void)e;
    int64_t t_clic = esp_timer_get_time();
    if (lv_async_call(nav_async, nav_param(0, t_clic)) != LV_RESULT_OK) {
        s_async_refus++;
        return;
    }
    s_dernier_tap = DN_UI_ZONE_RETOUR;
    s_taps++;
}

/*
 * ── LE BANDEAU MENU : W3 EST TRANCHÉ — IL N'EST PLUS ACTIONNABLE (dn3-2) ─────
 *
 * HISTORIQUE, conservé parce qu'il explique la forme actuelle : dn1-4 le
 * DESSINAIT comme une 7e zone tactile, cliquable, dont le tap n'écrivait qu'un
 * compteur. C'était un no-op consigné — honnête envers l'instrumentation, mais
 * pas envers l'utilisateur.
 *
 * 🔴 DÉCISION OWNER DU 2026-08-18 (W3) : le bandeau CESSE de se présenter comme
 *    actionnable. Motif écrit : aucune destination ne lui est spécifiée — ni
 *    dans le brief, ni dans l'addendum §1 (qui ne dessine que « │ MENU ○ │ »),
 *    ni dans l'epic. Il n'y a AUCUNE spec à appliquer. Et « un bouton qui a
 *    l'air actionnable et ne fait rien EST un mensonge d'interface », du même
 *    genre que la case qui affiche un chiffre sans source — que ce dépôt traque
 *    depuis dn1-3. C'est la seule branche qui ne crée aucune dette de spec.
 *    ⛔ La bascule Ambient/Actif, seule destination plausible, est
 *       explicitement réservée à dn3-3 : la brancher ici déborderait le
 *       périmètre.
 *
 * ⇒ `on_menu_clic` est SUPPRIMÉE et la zone est créée avec un callback NULL,
 *   ce qui — par le contrat de `dn_widget_zone_creer` (dn_widget.c:149-166,
 *   « CLICKABLE est CONDITIONNÉ au callback ») — lui RETIRE le drapeau
 *   CLICKABLE au lieu de la laisser avaler le tap en silence.
 *   ⛔ Surtout PAS un callback vide : une zone cliquable sans handler devient
 *      `act_obj`, reçoit le CLICKED et l'absorbe — le pire des trois états.
 *
 * ⚠️ `s_menu_taps` et `dn_ui_menu_taps()` SURVIVENT, et ce n'est pas du code
 *    mort : ce compteur est désormais STRUCTURELLEMENT à zéro, et c'est lui la
 *    preuve chiffrée qu'AC6 demande. Un compteur retiré ne prouverait plus
 *    rien ; laissé en place, il ne peut plus monter, et `nav` le dit.
 *    La preuve POSITIVE, elle, vient de `touch trace` : un appui dans la bande
 *    y = 580..640 s'imprime avec ses coordonnées et SANS zone attribuée.
 */

/* ── La barre heure/date (dn3-2) ──────────────────────────────────────────── */

/*
 * Les libellés FRANÇAIS ET ACCENTUÉS. `dn_font_14` porte le latin-1 complet
 * depuis dn3-1 — ⚠️ un glyphe absent serait dessiné EN SILENCE, et c'est
 * exactement ce qui faisait perdre son Û à « AOÛT » avec les built-ins.
 *
 * Les mois sont ABRÉGÉS À 4-5 CARACTÈRES, et c'est de l'arithmétique, pas du
 * goût : la date est posée en x = 300, il reste 480 − 300 − 10 = 170 px utiles.
 * « VEN. 06 SEPTEMBRE » en 14 px n'y tiendrait pas de façon sûre.
 * ✅ Et l'abréviation REPRODUIT EXACTEMENT la maquette normative de
 *    l'addendum §1, qui écrit « VEN. 06 AOÛT » : août ne s'abrège pas.
 */
static const char *const k_jsem_court[7] = {"DIM.", "LUN.", "MAR.", "MER.",
                                            "JEU.", "VEN.", "SAM."};
static const char *const k_mois_court[12] = {
    "JANV.", "FÉVR.", "MARS", "AVR.", "MAI",  "JUIN",
    "JUIL.", "AOÛT",  "SEPT.", "OCT.", "NOV.", "DÉC."};

/*
 * Compose le texte de la barre dans `s_barre_h` / `s_barre_d`. Rend `true` si
 * quelque chose d'AFFICHÉ a changé — c'est ce booléen, et lui seul, qui décide
 * d'une invalidation. Une barre qui se réécrit à l'identique coûterait
 * 6 334 px (18 % d'une case) pour rien.
 * 🔴 CE CHIFFRE EST MESURÉ (§16.5, dn3-2) et il REMPLACE la prémisse « 480 x 70
 *    = 33 600 px, soit 96 % d'une case », qui était fausse D'UN FACTEUR 5,3 :
 *    LVGL n'invalide que la zone des LABELS, pas le rectangle de la barre.
 */
static bool s_barre_h_change, s_barre_d_change;

static bool barre_composer(const dn_rtc_heure_t *h, bool fiable)
{
    char nh[sizeof(s_barre_h)];
    char nd[sizeof(s_barre_d)];

    if (!fiable || !h) {
        snprintf(nh, sizeof(nh), "%s", DN_UI_HEURE_INCONNUE);
        snprintf(nd, sizeof(nd), "%s", DN_UI_DATE_INCONNUE);
    } else {
        if (s_barre_secondes) {
            snprintf(nh, sizeof(nh), "%02u:%02u:%02u", h->heure, h->minute,
                     h->seconde);
        } else {
            snprintf(nh, sizeof(nh), "%02u:%02u", h->heure, h->minute);
        }
        /* Bornes RELUES avant indexation : `dn_rtc` les garantit déjà, mais un
         * index hors tableau ici serait une lecture de .rodata arbitraire — et
         * la garde coûte deux comparaisons. */
        const char *js = (h->jsem < 7) ? k_jsem_court[h->jsem] : "???";
        const char *mo = (h->mois >= 1 && h->mois <= 12) ? k_mois_court[h->mois - 1]
                                                         : "???";
        snprintf(nd, sizeof(nd), "%s %02u %s", js, h->jour, mo);
    }

    /*
     * 🔴 LES DEUX LABELS SONT SUIVIS SÉPARÉMENT — DÉFAUT MESURÉ LE 2026-08-18.
     *    La première version rendait UN booléen « quelque chose a changé » et
     *    `barre_ecrire_nolock()` réécrivait LES DEUX labels. Or en régime 1 Hz
     *    l'heure change chaque seconde et la DATE ne change qu'une fois par
     *    jour : `lv_label_set_text` invalidant INCONDITIONNELLEMENT, la date
     *    coûtait une seconde zone sale par seconde, pour rien.
     *    ⚠️ MESURÉ, pas déduit : **2,0 flush par mise à jour de barre** au lieu
     *       de 1,0 — c'est-à-dire le DOUBLE, sur l'A/B même qui devait chiffrer
     *       la cadence. C'est le défaut que dn3-1 avait corrigé sur le mock
     *       (« ne rien poser si rien n'a changé »), réintroduit ici par une
     *       autre porte.
     * ⚠️ Un changement de FIABILITÉ touche les DEUX (la couleur des deux
     *    change), donc il force les deux drapeaux.
     */
    bool fiab_change = (fiable != s_barre_fiable);
    s_barre_h_change = fiab_change || strcmp(nh, s_barre_h) != 0;
    s_barre_d_change = fiab_change || strcmp(nd, s_barre_d) != 0;
    if (s_barre_h_change || s_barre_d_change) {
        memcpy(s_barre_h, nh, sizeof(nh));
        memcpy(s_barre_d, nd, sizeof(nd));
        s_barre_fiable = fiable;
        return true;
    }
    return false;
}

/*
 * Applique le texte courant aux deux labels. ⚠️ VERROU LVGL DÉJÀ PRIS —
 * même contrat que `case_poser` et que tout `dn_widget_*`.
 * ⚠️ Les DEUX labels sont écrits sous LE MÊME verrou : l'heure et la date
 *    séparées par deux verrous laisseraient une trame afficher « 00:03 » du
 *    jour neuf à côté de la date de la veille. C'est le motif n°1 du contrat
 *    de verrou inversé de dn3-1, transposé.
 */
static void barre_ecrire_nolock(void)
{
    lv_color_t c_h = s_barre_fiable ? lv_color_white() : lv_color_hex(0x9a9a9a);
    lv_color_t c_d =
        s_barre_fiable ? lv_color_hex(0xa0d8ff) : lv_color_hex(0x9a9a9a);
    /* ⚠️ CHAQUE LABEL N'EST ÉCRIT QUE SI SON PROPRE TEXTE A CHANGÉ — voir le
     *    long commentaire de `barre_composer`. Écrire les deux coûtait le DOUBLE
     *    de zones sales, mesuré. */
    if (s_barre_heure && s_barre_h_change) {
        lv_label_set_text(s_barre_heure, s_barre_h);
        lv_obj_set_style_text_color(s_barre_heure, c_h, 0);
    }
    if (s_barre_date && s_barre_d_change) {
        lv_label_set_text(s_barre_date, s_barre_d);
        lv_obj_set_style_text_color(s_barre_date, c_d, 0);
    }
}

/* La (re)construction, elle, doit poser LES DEUX inconditionnellement : les
 * labels viennent de naître et ne portent encore ni texte ni couleur. Confondre
 * les deux chemins, c'est le mensonge d'interface que dn3-1 a soldé — un label
 * neuf qui garde le placeholder d'un côté et l'état réel de l'autre. */
static void barre_ecrire_tout_nolock(void)
{
    s_barre_h_change = true;
    s_barre_d_change = true;
    barre_ecrire_nolock();
}

/* ── Les deux vues ────────────────────────────────────────────────────────── */

static void build_dashboard(lv_obj_t *scr)
{
    fond_poser(scr);

    /* Barre heure/date — VIVANTE depuis dn3-2 : la RTC PCF85063 (0x51) est
     * pilotée par `dn_rtc`, qualifiée par LECTURE DE REGISTRE et non par le
     * scan. Pleine largeur, 70 px de haut : elle n'est PAS un cas adverse au
     * sens de §10.4, qui parle de hauteur.
     * 🔴 CE QU'ELLE COÛTE EST MESURÉ, PAS DÉDUIT DE SON AIRE (§16.5, dn3-2) :
     *    **6 334 px par mise à jour**, soit 18 % d'une case (35 100 px) — et
     *    NON les 33 600 px (96 %) que son rectangle laisse croire. La prémisse
     *    « une barre à 1 Hz est une 7e case vivante » était fausse d'un facteur
     *    5,3 : LVGL n'invalide que la zone des LABELS. Le régime par défaut
     *    reste HH:MM, mais parce que la MAQUETTE n'affiche pas les secondes
     *    (addendum §1, « 21:46 »), pas parce que le 1 Hz coûterait cher. */
    lv_obj_t *barre = lv_obj_create(scr);
    lv_obj_remove_style_all(barre);
    lv_obj_set_pos(barre, 0, 0);
    lv_obj_set_size(barre, DN_LCD_H_RES, ui_barre_h());
    lv_obj_clear_flag(barre, LV_OBJ_FLAG_SCROLLABLE);
    /* NON cliquable, et c'est une exigence d'AC3 : un tap sur la barre ne doit
     * RIEN ouvrir. C'est l'une des deux zones mortes que le constat vérifie.
     * ⛔ LA RENDRE VIVANTE NE LA REND PAS TACTILE — prouvé deux fois (AC3 de
     *    dn1-4 : 13 appuis de (8,21) à (415,30) ; AC4 de dn3-1 : 17 appuis à
     *    y = 24..72), et re-prouvé par AC5 de cette story. */
    lv_obj_clear_flag(barre, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_set_style_bg_color(barre, lv_color_black(), 0);
    lv_obj_set_style_bg_opa(barre, LV_OPA_70, 0);
    /* 🔴 LES DEUX LABELS NAISSENT AVEC L'ÉTAT COURANT, PAS AVEC UN PLACEHOLDER.
     *    `texte()` reçoit `s_barre_h` / `s_barre_d`, qui portent déjà ce que la
     *    barre doit dire — et `barre_ecrire_nolock()` juste après pose AUSSI la
     *    couleur. C'est l'anti-mensonge soldé par dn3-1 : « les labels sont
     *    remplis par le MÊME code que la réouverture ». Un « 21:46 » en dur ici
     *    s'afficherait pendant une trame après chaque reconstruction. */
    s_barre_heure =
        texte(barre, s_barre_h, &dn_font_28, lv_color_white(), DN_UI_MARGE, 18);
    /* Accentué depuis dn3-1 : « AOÛT » a récupéré son Û. C'est le témoin le plus
     * simple que la police générée est bien celle qui est liée. */
    s_barre_date =
        texte(barre, s_barre_d, &dn_font_14, lv_color_hex(0xa0d8ff), 300, 28);
    barre_ecrire_tout_nolock();

    /*
     * La grille 2x3, TOUJOURS UNE SEULE BOUCLE (dn2-1 a explicitement refusé
     * d'empiler des ternaires ici, on ne le refait pas). Elle se ramifie sur la
     * FORME de la case — widget ou nue — et sur rien d'autre : aucune métrique
     * n'est nommée dans ce code. C'est ce qui rend vraie la promesse « ajouter
     * une métrique ne redessine pas l'UI ».
     */
    for (int i = 0; i < DN_UI_METRIQUES; i++) {
        int col = i % 2;
        int ligne = i / 2;
        int x = DN_UI_MARGE + col * (DN_UI_CASE_W + DN_UI_GAP);
        int y = ui_grille_y() + DN_UI_MARGE + ligne * (ui_case_h() + DN_UI_GAP);

        /* LECTEUR 4/7 de l'override W11. ⚠️ LA BOUCLE RESTE UNE BOUCLE : le
         * branchement porte sur la FORME de la case (widget ou nue) et sur rien
         * d'autre — aucune métrique n'est nommée. dn2-1 a explicitement refusé
         * d'y empiler un second ternaire, on ne le refait pas. */
        if (case_est_widget(i)) {
            /* Copie locale du descripteur pour appliquer l'éventuel
             * remplacement d'icône (A/B de W4). GÉNÉRIQUE — indexé par case,
             * sans nommer aucune métrique : un `if (i == VENTILOS)` ici aurait
             * remis un cas spécial dans la boucle que dn2-1 a explicitement
             * refusé de ramifier. */
            dn_widget_desc_t d = k_desc[i];
            if (s_icone_alt[i]) {
                d.icone = s_icone_alt[i];
            }
            /* LECTEUR 1/3 de l'override de grandeurs — voir `desc_n()`. */
            d.n_grandeurs = (uint8_t)desc_n(i);
            dn_widget_creer(scr, x, y, DN_UI_CASE_W, ui_case_h(), &d,
                            &s_wetat[i], on_case_clic, (void *)(intptr_t)i,
                            &s_wobj[i]);
            continue;
        }

        /* ── LA CASE NUE : le témoin négatif d'AC8 ────────────────────────────
         * Conteneur + titre + valeur, exactement la forme de dn1-4. Elle NE
         * reçoit PAS le modèle — c'est ce qui permet de chiffrer une
         * case-widget CONTRE une case nue sous le même fps, le même bounce et
         * le même draw buffer, dans le MÊME firmware.
         * ⚠️ Mais elle est HONNÊTE : son état est ABSENT (aucune source ne
         *    l'alimente), donc « -- » grisé. Les factices d'apparence réelle de
         *    dn1-4 (« 37 % », « 12,4 Go », « 48 Mo/s ») sont supprimés. */
        lv_obj_t *case_ = zone_creer(scr, x, y, DN_UI_CASE_W, ui_case_h(),
                                     on_case_clic, (void *)(intptr_t)i);
        texte(case_, k_nom[i], &dn_font_14, lv_color_hex(0xa0d8ff), 12, 10);
        s_wobj[i].racine = case_;
        /* Même convention qu'à la mise à jour, et par le MÊME appel : c'est la
         * duplication de ce ternaire (ici ET dans `case_poser`) qui avait rendu
         * SIMULÉE indiscernable d'ABSENTE sur les cases nues (revue 2026-08-18). */
        s_wobj[i].valeur[0] =
            texte(case_, s_wetat[i].txt[0][0] ? s_wetat[i].txt[0] : "--",
                  &dn_font_28, dn_val_regime_couleur(s_wetat[i].regime),
                  12, 60);
    }

    /* Le bandeau MENU — DESSINÉ mais NON ACTIONNABLE depuis dn3-2 (W3). Le
     * callback NULL lui retire CLICKABLE par le contrat de `zone_creer` ; le
     * long motif est au-dessus de l'ancienne `on_menu_clic`. C'est un bandeau,
     * plus un bouton : il reste au layout de la maquette, il ne promet rien.
     * ⚠️ Le texte perd aussi son chevron `LV_SYMBOL_LIST` : un glyphe de menu
     *    est une AFFORDANCE, et la garder ferait exactement ce que W3 supprime
     *    — annoncer une action qui n'existe pas. */
    /* 🔴 dn4-6 / voie (a) : À `menu_h = 0` LE BANDEAU N'EST PAS DESSINÉ DU TOUT.
     *    Le dessiner à hauteur nulle laisserait un conteneur de 0 px dans
     *    l'arbre LVGL — invisible, mais présent dans les parcours et dans les
     *    comptes d'objets, donc un écart entre ce que la scène EST et ce que la
     *    console en DIT. La voie (a) supprime la barre MENU de la maquette :
     *    elle doit la supprimer pour de bon. */
    if (ui_menu_h() > 0) {
        lv_obj_t *menu = zone_creer(scr, 0, DN_LCD_V_RES - ui_menu_h(),
                                    DN_LCD_H_RES, ui_menu_h(), NULL, NULL);
        texte(menu, "MENU", &dn_font_28, lv_color_hex(0x9a9a9a), DN_UI_MARGE + 6,
              14);
    }

    label_poser(scr, &s_label_dash);
}

/*
 * ── LE TEMPLATE DE DÉTAIL : UN SEUL SQUELETTE, PARAMÉTRÉ ─────────────────────
 * « On ne change que les données, jamais la structure » (addendum §1). Les six
 * métriques sont SIX APPELS de cette fonction, pas six écrans — et c'est
 * précisément ce que le modèle SCREENS exploite en réécrivant les labels au lieu
 * de reconstruire.
 */
static void detail_reparametrer(int idx);

static void build_detail(lv_obj_t *scr, int idx)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES) {
        idx = 0;
    }
    fond_poser(scr);

    /*
     * ── TOUT LE TEXTE VIT SUR UN APLAT ──────────────────────────────────────
     * Correctif du constat owner du 2026-08-16. Les labels étaient posés à même
     * le fond : le Living PCB est une photo très contrastée, et du texte blanc
     * dessus se perd — surtout dans le bas de l'image. Quatre panneaux portent
     * désormais les quatre blocs du template, exactement comme les cases du
     * dashboard portaient déjà les leurs.
     * La STRUCTURE du template ne change pas (addendum §1 : « on ne change que
     * les données, jamais la structure ») — seul le support du texte change.
     */

    /* Bandeau d'en-tête : le retour ET le titre, sur le même aplat. */
    lv_obj_t *entete = panneau(scr, 0, 0, DN_LCD_H_RES, 80);
    /* Retour : zone GÉNÉREUSE (120x60), pas le glyphe seul — exigence d'AC4.
     * Enfant du bandeau, donc cliquable par-dessus lui : le bandeau n'est pas
     * cliquable, il ne peut pas lui voler le tap. */
    lv_obj_t *retour = zone_creer(entete, DN_UI_MARGE, DN_UI_MARGE, DN_UI_RETOUR_W,
                                  DN_UI_RETOUR_H, on_retour_clic, NULL);
    texte(retour, LV_SYMBOL_LEFT, &dn_font_28, lv_color_white(), 16, 14);

    /* Titre de la métrique — c'est LUI qui rend la zone touchée identifiable
     * sans ambiguïté (AC3) : six instances du même template, un seul titre. */
    s_det_titre = texte(entete, k_nom[idx], &dn_font_28,
                        lv_color_hex(0xa0d8ff), DN_UI_MARGE + DN_UI_RETOUR_W + 20,
                        24);

    /* Grande valeur. « Grande » = dn_font_28, la plus grosse police embarquée.
     * 🔴 dn4-6 / AC10 : LE BLOC PASSE DE 62 À 97 px — DEUX LIGNES DE 35.
     *    `GPU` porte QUATRE grandeurs, et quatre ne tiennent pas sur une ligne
     *    de 446 px utiles (~632 px mesurés au pire cas contre ~410 pour trois).
     *    Sans cette hauteur, la deuxième ligne serait CLIPPÉE PAR LE PANNEAU —
     *    sans un mot, comme toujours avec LVGL.
     * ⚠️ LES 35 px SONT PRIS AU PLACEHOLDER DE COURBE, PAS À LA PAGE : le cadre
     *    descend de 170 à 205 et perd 35 px de hauteur, son BAS reste à 370, et
     *    le panneau du bas (385) NE BOUGE PAS. Le template reste UN template et
     *    garde ses quatre panneaux (addendum §1 : « on ne change que les
     *    données, jamais la structure »). Ce qui rétrécit est un cadre vide qui
     *    ne dessine aucune courbe — l'historique arrive en dn4-4. */
    lv_obj_t *bloc_valeur =
        panneau(scr, DN_UI_MARGE, 95, DN_LCD_H_RES - 2 * DN_UI_MARGE, 97);
    s_det_valeur = texte(bloc_valeur, "--", &dn_font_28, lv_color_white(), 14, 14);

    /* Placeholder de courbe : un cadre étiqueté, PAS une courbe. Les vraies
     * séries arrivent avec l'historique RAM-session (dn4-4). */
    lv_obj_t *cadre = panneau(scr, DN_UI_MARGE, 205, DN_LCD_H_RES - 2 * DN_UI_MARGE,
                              165);
    texte(cadre, "COURBE (dn4-4)", &dn_font_14,
          lv_color_hex(0x80a0b0), 12, 70);

    /* Données secondaires et MIN/MAX, sur un seul aplat de bas de page — c'est
     * celui-là que l'owner a signalé comme illisible le 2026-08-16. */
    lv_obj_t *bas = panneau(scr, DN_UI_MARGE, 385, DN_LCD_H_RES - 2 * DN_UI_MARGE,
                            200);
    s_det_sec = texte(bas, "", &dn_font_14, lv_color_hex(0xc0d8e8), 14, 16);
    s_det_minmax = texte(bas, "", &dn_font_28, lv_color_white(), 14, 130);

    /* 🔴 LES QUATRE LABELS DE DONNÉES NAISSENT VIDES ET SONT REMPLIS ICI, PAR
     *    LE MÊME CODE QUE LA RÉOUVERTURE. C'est le correctif d'AC5 : tant que
     *    `build_detail` posait des constantes et que `detail_reparametrer` en
     *    posait d'autres, il y avait DEUX sources de vérité pour un même écran,
     *    et c'est la première qui mentait (« 21,4 °C » en dur, capteur débranché
     *    compris, pendant que la tuile derrière disait honnêtement « -- »). */
    detail_reparametrer(idx);

    label_poser(scr, &s_label_det);
}

/*
 * ── LE DÉTAIL HÉRITE DE L'ÉTAT DE SA SOURCE (AC5, legs R1 du ledger) ─────────
 *
 * Réécrit les données du détail SANS reconstruire l'arbre — le raccourci du
 * modèle SCREENS. Ne touche à aucune position : la structure ne change jamais,
 * les 4 panneaux restent 4 panneaux (addendum §1).
 *
 * 🔴 CE QUE CETTE FONCTION CORRIGE. Elle posait `k_metriques[idx].valeur`, une
 *    CONSTANTE. Un tap sur TEMP. ouvrait donc un écran affichant « 21,4 °C » en
 *    dur — capteur débranché compris — PENDANT QUE la tuile derrière affichait
 *    honnêtement « -- ». Le mensonge d'interface que dn2-2 avait chassé du
 *    dashboard vivait un écran plus loin. Trois cases sur six étaient touchées.
 *
 * 🔴 ET LA CONTRAINTE VA PLUS LOIN QUE LA VALEUR : le détail hérite de l'ÉTAT
 *    de la source (`dn_link_etat()`, `dn_capt_etat()`), pas seulement de son
 *    chiffre — « sinon le même mensonge revient avec un vrai widget ». Un
 *    écran qui affiche la dernière valeur connue SANS dire que la source est
 *    morte ment exactement de la même façon, en plus poli.
 *
 * ⚠️ MIN/MAX : AUCUN historique n'existe (il arrive en dn3-2/dn4-1). On écrit
 *    donc « MIN --   ·   MAX -- ». Y remettre « MIN 12 % - MAX 91 % » parce que
 *    « le panneau a l'air vide » serait refaire le défaut qu'on solde.
 */
/* ⚠️ Le paramètre de sortie `vivante` a été RETIRÉ le 2026-08-18 (revue de
 * code) : il était écrit et JAMAIS lu — son unique appelant le déclarait puis
 * l'ignorait, ce que `-Wunused-but-set-variable` aurait fini par dire. Le nom
 * d'état rendu porte déjà l'information, et le régime la porte une seconde
 * fois. Un paramètre de sortie mort suggère un contrat qui n'existe pas. */
/*
 * ── LES DEUX TABLES CACHÉES, DÉSORMAIS DES TABLES (dn4-1 / AC6) ──────────────
 *
 * 🔴 CE SONT ELLES QUE dn4-1 AURAIT FAIT MENTIR. Le dépôt répète que « ajouter
 *    une métrique = une ligne de `k_desc[]`, aucun `if (idx == …)` dans le
 *    dessin ». C'est vrai du DESSIN. Ce n'était PAS vrai ici : `etat_source` et
 *    `nom_source` étaient deux cascades câblées PAR INDEX, qui rendaient
 *    « aucune » et « AUCUNE — pas encore branchée » pour GPU, RAM et RÉSEAU.
 *    Les laisser telles quelles aurait fait dire à la page de détail d'une case
 *    VIVANTE qu'elle n'a pas de source — l'étiquette qui ment, sur le SEUL écran
 *    qui prétend expliquer d'où vient le chiffre.
 *
 * ⇒ On les GÉNÉRALISE (une table, comme `k_desc[]`) au lieu d'y ajouter quatre
 *   branches de plus. Ajouter une métrique reste une LIGNE.
 *
 * ⚠️ Le nom rendu ici est RELU de `dn_link`/`dn_capteurs`, jamais récité : c'est
 *    l'état RÉEL de la source, métrique par métrique — ⛔ surtout pas le résumé
 *    global `dn_link_etat()`, qui déclarerait « VIVANTE » quatre cases mortes
 *    parce que la cinquième vit.
 */
typedef enum {
    DN_SRC_AUCUNE = 0, /* aucune source branchée — l'aveu d'ignorance par défaut */
    DN_SRC_LIEN_PC,    /* dn_link, métrique donnée par `metrique` */
    DN_SRC_CAPTEUR,    /* dn_capteurs (BME680) */
} dn_src_t;

static const struct {
    dn_src_t type;
    dn_link_metrique_t metrique; /* n'a de sens que si type == DN_SRC_LIEN_PC */
    const char *nom;
} k_source[DN_UI_METRIQUES] = {
    [DN_UI_CASE_CPU] = {DN_SRC_LIEN_PC, DN_LINK_M_CPU, "liaison PC (dn_link) — cpu"},
    [DN_UI_CASE_GPU] = {DN_SRC_LIEN_PC, DN_LINK_M_GPU, "liaison PC (dn_link) — gpu"},
    [DN_UI_CASE_RAM] = {DN_SRC_LIEN_PC, DN_LINK_M_RAM, "liaison PC (dn_link) — ram"},
    [DN_UI_CASE_RESEAU] = {DN_SRC_LIEN_PC, DN_LINK_M_NET, "liaison PC (dn_link) — net"},
    [DN_UI_CASE_DISQUE] = {DN_SRC_LIEN_PC, DN_LINK_M_DISK, "liaison PC (dn_link) — disk"},
    [DN_UI_CASE_AMB] = {DN_SRC_CAPTEUR, 0, "BME680 (dn_capteurs)"},
};

static const char *etat_source(int idx)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES) {
        return "?";
    }
    /* 🔴 LE MOCK PASSE AVANT LA SOURCE, ET C'EST LE SEUL ORDRE HONNÊTE. Quand
     *    le générateur est armé, c'est LUI qui alimente la case : annoncer
     *    l'état de la vraie source pendant qu'un chiffre inventé s'affiche
     *    serait un mensonge de plus, sur l'écran qui explique les chiffres.
     * ⚠️ Le mock n'a pas d'« état de source » : il EN EST une, et son régime le
     *    dit déjà. Le nommer « VIVANT » l'habillerait en mesure. */
    if (s_mock_on && k_mock[idx].actif) {
        return "générateur interne";
    }
    switch (k_source[idx].type) {
    case DN_SRC_LIEN_PC:
        return dn_link_etat_nom(dn_link_etat_metrique(k_source[idx].metrique));
    case DN_SRC_CAPTEUR:
        return dn_capt_etat_nom(dn_capt_etat());
    default:
        return "aucune";
    }
}

static const char *nom_source(int idx)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES) {
        return "?";
    }
    if (s_mock_on && k_mock[idx].actif) {
        return "MOCK dn3-1 (aucun capteur) — instrument ARMÉ";
    }
    if (k_source[idx].type == DN_SRC_AUCUNE) {
        return "AUCUNE — pas encore branchée";
    }
    return k_source[idx].nom;
}

static void detail_reparametrer(int idx)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES) {
        return;
    }
    if (s_det_titre) {
        lv_label_set_text(s_det_titre, k_nom[idx]);
    }

    const dn_widget_etat_t *e = &s_wetat[idx];
    /* LECTEUR 5/7 de l'override W11. */
    const dn_widget_desc_t *d = case_est_widget(idx) ? &k_desc[idx] : NULL;
    /*
     * 🔴 dn4-6 / AC10 — LE TAMPON EST DIMENSIONNÉ, PAS ESPÉRÉ. `snprintf`
     *    TRONQUE EN SILENCE (piège d'instrument n°14) : un `buf[96]` qui reçoit
     *    quatre grandeurs aurait coupé la dernière sans lever quoi que ce soit,
     *    sur l'écran qui prétend TOUT expliquer.
     *    Pire cas par grandeur : texte (`DN_WIDGET_TXT_MAX` = 16) + espace +
     *    unité (« tr/min » = 6) + préfixe (« c.max » = 5) + espace, plus le
     *    séparateur « \u00a0·\u00a0 » entre deux. On prend large ET on VÉRIFIE.
     */
    char buf[4 * (DN_WIDGET_TXT_MAX + 24) + 8];

    if (s_det_valeur) {
        /* La MÊME règle que la tuile : régime ABSENT ⇒ « -- » grisé, jamais un
         * chiffre. Et la couleur suit le régime, y compris l'ambre du simulé —
         * sinon le détail d'une case simulée présenterait son chiffre comme
         * réel, ce qu'AC5 interdit explicitement. */
        if (e->regime == DN_VAL_ABSENTE || e->txt[0][0] == '\0') {
            snprintf(buf, sizeof(buf), "--");
        } else {
            /*
             * 🔴 dn4-6 / AC10 — TOUTES LES GRANDEURS, ET AUCUNE TRONCATURE
             *    SILENCIEUSE. La version d'avant ne connaissait que `txt[0]` et
             *    `txt[1]` : à quatre grandeurs, la page qui explique la case en
             *    aurait caché la moitié — le mensonge par omission que dn4-1
             *    avait déjà chassé d'ici une fois (la condition
             *    `&& e->txt[1][0]` faisait retomber sur la branche mono).
             *
             * ⚠️ TROIS PAR LIGNE, ET C'EST ARITHMÉTIQUE, PAS ESTHÉTIQUE. Le
             *    panneau fait 460 px, le label est posé à x = 14 ⇒ 446 px
             *    utiles. Largeurs RELUES de la police liée (AC5) :
             *      3 grandeurs, pire cas  « 100,0 % · 150,0 °C · 350 W »  ~410 px  OK
             *      4 grandeurs, pire cas  + « · 3000 tr/min »             ~632 px  NON
             *    ⇒ au-delà de trois, on passe à la ligne. ⛔ Et LVGL clipperait
             *      sans un mot : « rien n'a planté » n'est pas « ça tient ».
             * ⚠️ « -- » ne porte JAMAIS son unité, ✅ mais garde son préfixe :
             *    c'est lui qui dit QUELLE grandeur manque (W10 jusque dans le
             *    détail — l'existence d'une grandeur ne se cache jamais).
             */
            /* LECTEUR 2/3 de l'override de grandeurs — voir `desc_n()`. Lire
             * `d->n_grandeurs` ici ferait detailler QUATRE grandeurs sur une
             * case qui n'en DESSINE que trois : la page qui explique la case
             * expliquerait autre chose que la case. */
            int n = d ? desc_n(idx) : 1;
            if (n < 1) {
                n = 1;
            }
            if (n > DN_WIDGET_GRANDEURS_MAX) {
                n = DN_WIDGET_GRANDEURS_MAX;
            }
            size_t p = 0;
            int ecrit = 0;
            for (int i = 0; i < n && p < sizeof(buf); i++) {
                const char *sep = (i == 0) ? "" : ((i % 3) == 0 ? "\n" : "   ·   ");
                bool connue = e->txt[i][0] != '\0';
                const char *px = d ? d->grandeurs[i].prefixe : NULL;
                /* 🔴 L'ÉCHELLE HAUTE VAUT ICI AUSSI. Sans ça, la tuile dirait
                 *    « ↓ 100,0 Gb/s » et le détail « 100,0 Mb/s » POUR LE MÊME
                 *    NOMBRE — deux vérités contradictoires à un tap d'écart,
                 *    dont l'une est fausse d'un facteur mille. C'est le
                 *    mensonge d'interface que dn4-1 a chassé du détail une
                 *    première fois (la valeur en dur « 21,4 °C »). */
                const char *u = connue ? dn_widget_unite(d, e, i) : NULL;
                ecrit = snprintf(buf + p, sizeof(buf) - p, "%s%s%s%s%s%s", sep,
                                 px ? px : "", px ? " " : "",
                                 connue ? e->txt[i] : "--", u ? " " : "",
                                 u ? u : "");
                if (ecrit < 0 || (size_t)ecrit >= sizeof(buf) - p) {
                    /* ⛔ LA TRONCATURE EST AUDIBLE, JAMAIS SUBIE. Elle est
                     * impossible avec le dimensionnement ci-dessus ; ce log
                     * existe pour que le jour où une unité s'allonge, on
                     * l'apprenne par la console et pas par un écran amputé. */
                    ESP_LOGE(TAG,
                             "detail « %s » : TAMPON TROP COURT a la grandeur %d "
                             "(%u octets) — texte TRONQUE.",
                             k_nom[idx], i, (unsigned)sizeof(buf));
                    break;
                }
                p += (size_t)ecrit;
            }
        }
        lv_label_set_text(s_det_valeur, buf);
        lv_obj_set_style_text_color(
            s_det_valeur,
            e->regime == DN_VAL_REELLE    ? lv_color_white()
            : e->regime == DN_VAL_SIMULEE ? lv_color_hex(0xffb020)
                                          : lv_color_hex(0x9a9a9a),
            0);
    }

    if (s_det_sec) {
        const char *etat = etat_source(idx);
        /* TROIS lignes, toutes RELUES de l'état réel : la source, son état, le
         * régime de la valeur. Aucune n'est une constante d'affichage. */
        snprintf(buf, sizeof(buf), "source : %s\nétat   : %s\nrégime : %s",
                 nom_source(idx), etat, dn_val_regime_nom(e->regime));
        lv_label_set_text(s_det_sec, buf);
    }

    if (s_det_minmax) {
        lv_label_set_text(s_det_minmax, "MIN --   ·   MAX --");
    }
}

/* ── build_scene : reconstruit la VUE COURANTE ────────────────────────────── */

/* Détruit et reconstruit toute la scène. Idempotent, et appelé aussi bien à
 * l'init qu'au changement de source de fond : reconstruire coûte quelques
 * millisecondes une fois, là où permuter le pointeur d'une image déjà posée
 * obligerait à raisonner sur le cache d'images de LVGL. Un geste d'opérateur ne
 * mérite pas cette subtilité-là. */
static void build_scene(void)
{
    /* ⚠️ L'ombre suit la réalité (revue dn1-3). La reconstruction détruit la
     * barre du stimulus ET son animation : laisser `s_anim_on` à vrai ferait
     * annoncer « stimulus EN COURS » par `ui`, `anim` et l'étiquette de `fps` —
     * une étiquette de mesure FAUSSE, la classe de défaut que ce firmware
     * traque. L'opérateur relance `anim on` s'il le veut. */
    if (s_anim_on) {
        s_anim_on = false;
        ESP_LOGW(TAG, "reconstruction de scène : le stimulus `anim` est ARRÊTÉ "
                      "(relancer `anim on` si besoin)");
    }
    /* Même règle pour la démo d'AC1 : elle est posée sur l'écran actif, la
     * reconstruction l'emporte avec lui. L'ombre suit, sinon la console
     * annoncerait une démo affichée qui n'existe plus. */
    if (s_demo_on) {
        s_demo_on = false;
        ESP_LOGW(TAG, "reconstruction de scène : la démo `widget demo` est "
                      "RETIRÉE (relancer `widget demo on` si besoin)");
    }
    dn_widget_oublier(&s_demo);
    s_label_dash = NULL;
    s_label_det = NULL;
    s_bar = NULL;
    s_det_titre = NULL;
    s_det_valeur = NULL;
    s_det_minmax = NULL;
    s_det_sec = NULL;
    /* SITE 1/3 — la barre heure/date (dn3-2). ⚠️ La tâche `dn_rtc` pousse à
     * 2 Hz : un pointeur laissé non-NULL ici survivrait à son label et elle
     * écrirait dans de la mémoire libérée dès la trame suivante. */
    s_barre_heure = NULL;
    s_barre_date = NULL;
    /* ⚠️ TOUTES les cases vivantes, pas seulement CPU : un pointeur oublié ici
     * survivrait à son label et la tâche capteur écrirait dans du vide libéré. */
    for (int i = 0; i < DN_UI_METRIQUES; i++) {
        dn_widget_oublier(&s_wobj[i]);
    }

    if (s_nav == DN_NAV_SCREENS) {
        /* Les deux racines sont (re)construites ensemble : un `ui bg psram` qui
         * ne referait qu'un seul des deux écrans laisserait l'autre blitter
         * l'ancienne source — et l'A/B des fonds mesurerait deux choses à la
         * fois. */
        lv_obj_t *ancien_dash = s_scr_dash;
        lv_obj_t *ancien_det = s_scr_detail;
        /*
         * ⚠️ L'ÉCRAN SORTANT N'EST PAS TOUJOURS L'UNE DES DEUX RACINES, et c'est
         *    la FUITE trouvée par la revue de dn1-4. Deux cas où il est un
         *    troisième objet que personne ne détruisait :
         *      - au boot, c'est l'écran par défaut créé par lv_display_create ;
         *      - en revenant de REBUILD, c'est celui que dn_ui_set_nav_model a
         *        créé pour héberger l'arbre reconstruit.
         *    `lv_screen_load()` est un `lv_screen_load_anim(..., auto_del=false)`
         *    : il ne détruit RIEN. Un aller-retour `screens -> rebuild ->
         *    screens` — exactement l'A/B que la console invite à faire pour
         *    arbitrer AC4 — abandonnait donc un arbre dashboard COMPLET (image,
         *    voile, barre, 6 cases, 14 labels, MENU, label vivant) dans les 64 Ko
         *    du tas LVGL. Et la « preuve de non-fuite » de `nav ab` ne pouvait
         *    pas le voir : elle mesure la RAM interne et la PSRAM, alors que ce
         *    tas est un pool STATIQUE en .bss (LV_MEM_ADR=0).
         */
        lv_obj_t *sortant = lv_screen_active();
        s_scr_dash = lv_obj_create(NULL);
        build_dashboard(s_scr_dash); /* remplit s_label_dash */
        s_scr_detail = lv_obj_create(NULL);
        build_detail(s_scr_detail, s_metrique); /* remplit s_label_det */
        lv_screen_load(s_vue == DN_VUE_DETAIL ? s_scr_detail : s_scr_dash);
        /* Supprimés APRÈS le chargement du nouvel écran : supprimer l'écran
         * actif avant d'en charger un autre laisserait LVGL sans écran courant
         * le temps d'une instruction. */
        if (ancien_dash) {
            lv_obj_delete(ancien_dash);
        }
        if (ancien_det) {
            lv_obj_delete(ancien_det);
        }
        if (sortant && sortant != ancien_dash && sortant != ancien_det &&
            sortant != s_scr_dash && sortant != s_scr_detail) {
            lv_obj_delete(sortant);
        }
        return;
    }

    /* REBUILD : un seul écran, celui de LVGL, vidé puis redessiné. */
    lv_obj_t *scr = lv_screen_active();
    lv_obj_clean(scr);
    if (s_vue == DN_VUE_DETAIL) {
        build_detail(scr, s_metrique);
    } else {
        build_dashboard(scr);
    }
}

/* ── Navigation : le travail ──────────────────────────────────────────────── */

/*
 * `cible` : 0 = dashboard, 1..6 = détail de la métrique cible-1.
 * `t_clic` : instant d'origine pour la latence (0 = celui du dernier clic).
 * Appelée DANS la tâche LVGL, hors contexte d'événement (via lv_async_call) ou
 * sous le verrou pris par l'appelant public. Ne prend pas le verrou elle-même.
 */
static bool nav_appliquer(int cible, int64_t t_clic)
{
    dn_ui_vue_t vue = cible == 0 ? DN_VUE_DASHBOARD : DN_VUE_DETAIL;
    int idx = cible == 0 ? s_metrique : cible - 1;

    /* Rien à faire : on DÉSARME plutôt que de laisser un chronomètre en vol.
     * Un double tap sur la même case empilerait deux transitions ; la seconde
     * n'a rien à redessiner, et un chrono armé sans redessin serait arrêté par
     * le premier flush venu — une latence inventée.
     * ⚠️ On rend FALSE (revue dn1-4) : l'appelant annonçait « détail ouvert » /
     * « retour au dashboard » pour une transition qui n'avait pas eu lieu, et
     * `nav ab` perdait silencieusement un échantillon quand la série démarrait
     * depuis un détail déjà affiché — `lat.n` valait 39 au lieu de 40, et
     * servait de dénominateur à la moyenne publiée par AC5. */
    if (vue == s_vue && (vue == DN_VUE_DASHBOARD || idx == s_metrique)) {
        return false;
    }

    s_vue = vue;
    s_metrique = idx;

    if (s_nav == DN_NAV_SCREENS && s_scr_dash && s_scr_detail) {
        /*
         * ⚠️ LE STIMULUS ADVERSE NE SURVIT PAS À UNE BASCULE D'ÉCRAN, et l'ombre
         *    doit le dire. En modèle SCREENS, rien n'est détruit : la barre
         *    d'`anim` reste accrochée à l'écran qu'on quitte, donc INVISIBLE,
         *    pendant que `s_anim_on` continuerait d'annoncer « stimulus EN
         *    COURS » à `ui`, `anim` et à l'étiquette de `fps`. Une mesure
         *    étiquetée « sous stimulus » sans stimulus à l'écran est exactement
         *    le défaut que la revue de dn1-3 a corrigé 21 fois.
         *    On l'arrête donc pour de bon, comme le fait la reconstruction.
         */
        if (s_bar) {
            lv_anim_delete(s_bar, bar_set_x);
            lv_obj_delete(s_bar);
            s_bar = NULL;
        }
        s_anim_on = false;
        /* Idem pour la démo d'AC1 : en SCREENS rien n'est détruit, elle
         * resterait accrochée à l'écran qu'on quitte — donc INVISIBLE, pendant
         * que l'ombre annoncerait « affichée ». On la retire pour de bon. */
        if (s_demo.racine) {
            lv_obj_delete(s_demo.racine);
            dn_widget_oublier(&s_demo);
        }
        s_demo_on = false;
        if (vue == DN_VUE_DETAIL) {
            detail_reparametrer(idx);
            lv_screen_load(s_scr_detail);
        } else {
            lv_screen_load(s_scr_dash);
        }
    } else {
        lv_obj_t *scr = lv_screen_active();
        lv_obj_clean(scr);
        s_label_dash = NULL;
        s_label_det = NULL;
        s_bar = NULL;
        s_det_titre = NULL;
        s_det_valeur = NULL;
        s_det_minmax = NULL;
        s_det_sec = NULL;
        /* SITE 2/3 — la barre heure/date (dn3-2). `lv_obj_clean` vient de
         * DÉTRUIRE ses deux labels avec tout l'écran. */
        s_barre_heure = NULL;
        s_barre_date = NULL;
        for (int i = 0; i < DN_UI_METRIQUES; i++) {
            dn_widget_oublier(&s_wobj[i]);
        }
        /*
         * 🔴 LA DÉMO MANQUAIT ICI, ET C'ÉTAIT LE DÉFAUT LE PLUS GRAVE DE dn3-1
         *    (revue du 2026-08-18, convergence des TROIS couches).
         *    `lv_obj_clean(scr)` DÉTRUIT la démo — elle est créée sur
         *    `lv_screen_active()`, qui EN MODÈLE REBUILD *est* ce `scr`. Le
         *    pointeur survivait à son objet, et `widget demo off` faisait alors
         *    un `lv_obj_delete()` sur de la mémoire libérée : le use-after-free
         *    que la revue dn1-3 avait déjà trouvé, et qu'AC1 cite NOMMÉMENT.
         *    ⚠️ La branche SCREENS ci-dessus le faisait, pas celle-ci — un
         *    invariant tenu dans une branche sur deux n'est pas un invariant.
         */
        if (s_demo_on) {
            s_demo_on = false;
            ESP_LOGW(TAG, "reconstruction (rebuild) : la démo `widget demo` est "
                          "RETIRÉE (relancer `widget demo on` si besoin)");
        }
        dn_widget_oublier(&s_demo);
        /* Même règle qu'en reconstruction complète : la barre du stimulus vient
         * d'être détruite, l'ombre le dit. Sans le log ici (il tomberait à chaque
         * transition), mais avec le même effet sur l'état annoncé. */
        s_anim_on = false;
        if (vue == DN_VUE_DETAIL) {
            build_detail(scr, idx);
        } else {
            build_dashboard(scr);
        }
    }

    s_nav_count++;
    /* Le chronomètre est armé ICI, la nouvelle vue étant posée : le prochain
     * cycle de rafraîchissement est CELUI de la transition. Voir dn_touch.h. */
    dn_touch_latence_arm(t_clic);
    return true;
}

dn_ui_vue_t dn_ui_vue(void) { return s_vue; }
int dn_ui_metrique(void) { return s_metrique; }
uint32_t dn_ui_nav_count(void) { return s_nav_count; }
int dn_ui_dernier_tap(void) { return s_dernier_tap; }
uint32_t dn_ui_taps(void) { return s_taps; }

const char *dn_ui_zone_nom(int zone)
{
    if (zone == DN_UI_ZONE_MENU) {
        return "MENU (zone morte — W3)";
    }
    if (zone == DN_UI_ZONE_RETOUR) {
        return "RETOUR";
    }
    if (zone >= 0 && zone < DN_UI_METRIQUES) {
        return k_nom[zone];
    }
    return "aucune";
}

uint32_t dn_ui_menu_taps(void) { return s_menu_taps; }
uint32_t dn_ui_async_refus(void) { return s_async_refus; }
dn_nav_model_t dn_ui_get_nav_model(void) { return s_nav; }

/*
 * Les compteurs de la couche UI n'avaient AUCUN reset (revue dn1-4), alors que
 * la console imprime elle-même « comparer proprement : `touch reset` puis
 * `nav ab 20` » au moment de basculer de modèle. `touch reset` ne remettait à
 * zéro que ceux de dn_touch : après une bascule, `nav` continuait d'afficher les
 * taps et le nombre de transitions du modèle PRÉCÉDENT, sous une bannière qui
 * annonçait le nouveau. Le compteur d'un modèle était publié comme celui de
 * l'autre.
 */
void dn_ui_reset_compteurs(void)
{
    s_taps = 0;
    s_menu_taps = 0;
    s_nav_count = 0;
    s_async_refus = 0;
    s_dernier_tap = DN_UI_ZONE_AUCUNE;
}

/*
 * ⚠️ ESP_ERR_INVALID_STATE = « la vue demandée était DÉJÀ l'active, rien n'a
 *    bougé ». Ce n'est pas une panne, c'est un no-op — mais l'appelant DOIT
 *    pouvoir le distinguer d'une transition réelle : la console annonçait
 *    « détail ouvert » et `nav ab` comptait une itération pour un écran qui
 *    n'avait pas changé, ce qui décalait le dénominateur de la latence d'AC5.
 */
esp_err_t dn_ui_nav_open(int idx)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!lvgl_port_lock(1000)) {
        return ESP_ERR_TIMEOUT;
    }
    bool fait = nav_appliquer(idx + 1, esp_timer_get_time());
    lvgl_port_unlock();
    return fait ? ESP_OK : ESP_ERR_INVALID_STATE;
}

esp_err_t dn_ui_nav_back(void)
{
    if (!lvgl_port_lock(1000)) {
        return ESP_ERR_TIMEOUT;
    }
    bool fait = nav_appliquer(0, esp_timer_get_time());
    lvgl_port_unlock();
    return fait ? ESP_OK : ESP_ERR_INVALID_STATE;
}

esp_err_t dn_ui_set_nav_model(dn_nav_model_t m)
{
    if (m >= DN_NAV_COUNT) {
        return ESP_ERR_INVALID_ARG;
    }
    if (m == s_nav) {
        return ESP_OK;
    }
    if (!lvgl_port_lock(2000)) {
        return ESP_ERR_TIMEOUT;
    }
    /*
     * On repart du DASHBOARD, toujours. Les deux modèles ne tiennent pas leur
     * état au même endroit (un écran vidé/reconstruit d'un côté, deux racines
     * permanentes de l'autre) : prétendre conserver la vue courante ferait mentir
     * l'un des deux, et la première mesure d'après bascule serait à jeter.
     */
    s_vue = DN_VUE_DASHBOARD;

    if (s_nav == DN_NAV_SCREENS) {
        /* On QUITTE screens : l'écran actif redevient celui de LVGL, et les deux
         * racines sont libérées. Ordre non négociable — charger d'abord, détruire
         * ensuite (voir build_scene). */
        lv_obj_t *neuf = lv_obj_create(NULL);
        lv_screen_load(neuf);
        if (s_scr_dash) {
            lv_obj_delete(s_scr_dash);
            s_scr_dash = NULL;
        }
        if (s_scr_detail) {
            lv_obj_delete(s_scr_detail);
            s_scr_detail = NULL;
        }
        /*
         * 🔴 TROISIÈME SITE DE DÉMONTAGE (AC1). Il ne remettait RIEN à NULL.
         *    `lv_obj_delete(s_scr_dash)` détruit tout l'arbre du dashboard, donc
         *    les six conteneurs et leurs labels — et `s_wobj[]` continuait de
         *    les désigner. `build_scene()` juste en dessous les réécrit, mais
         *    ENTRE les deux le verrou n'est pas relâché ; c'était donc une
         *    fenêtre étroite plutôt qu'un défaut ouvert. On la ferme quand même :
         *    l'invariant « un pointeur mort est mis à NULL AU MOMENT où son
         *    objet meurt » ne doit pas dépendre de ce qui suit. La revue dn1-3 a
         *    trouvé un use-after-free exactement sur ce raisonnement-là.
         */
        for (int i = 0; i < DN_UI_METRIQUES; i++) {
            dn_widget_oublier(&s_wobj[i]);
        }
        /*
         * 🔴 ET LA DÉMO AUSSI — elle manquait ici, et le commentaire ci-dessus
         *    s'appliquait à elle sans la traiter (revue de code du 2026-08-18,
         *    trouvée SÉPARÉMENT par les trois couches). Elle est posée sur
         *    `lv_screen_active()`, c'est-à-dire l'une des deux racines qu'on
         *    vient de détruire : `s_demo.racine` désignait donc de la mémoire
         *    libérée, et `dn_ui_demo_on()` (`s_demo_on && racine != NULL`)
         *    rendait VRAI ⇒ la console annonçait « AFFICHEE » pour un widget
         *    mort. `build_scene()` juste en dessous rattrapait — mais c'est
         *    exactement le « ce qui suit » dont l'invariant ne doit pas dépendre.
         */
        if (s_demo_on) {
            s_demo_on = false;
            ESP_LOGW(TAG, "bascule de modèle : la démo `widget demo` est "
                          "RETIRÉE (relancer `widget demo on` si besoin)");
        }
        dn_widget_oublier(&s_demo);
        s_det_titre = NULL;
        s_det_valeur = NULL;
        s_det_minmax = NULL;
        s_det_sec = NULL;
        /* SITE 3/3 — la barre heure/date (dn3-2). Les DEUX racines viennent
         * d'être détruites ; ses labels vivaient sur celle du dashboard. */
        s_barre_heure = NULL;
        s_barre_date = NULL;
        s_label_dash = NULL;
        s_label_det = NULL;
        s_bar = NULL;
    }
    s_nav = m;
    build_scene();
    lvgl_port_unlock();
    ESP_LOGI(TAG, "modèle de navigation : « %s »", dn_nav_model_name(m));
    return ESP_OK;
}

/* ── Init ─────────────────────────────────────────────────────────────────── */

/*
 * ── dn4-6 / AC9 : L'AUDIT DES DESCRIPTEURS, UNE FOIS, AU BOOT ────────────────
 *
 * 🔴 `DN_PREC_NON_RENSEIGNEE = 0` REND L'OUBLI DÉTECTABLE, ENCORE FAUT-IL LE
 *    DÉTECTER. Le repli silencieux vers le dixième est le comportement d'AVANT
 *    dn4-6 — donc invisible à l'œil, et c'est précisément ce qui en fait un
 *    piège : le jour où une grandeur sera ajoutée sans sa précision, elle
 *    affichera « 604,0 tr/min » et personne ne saura que c'était un oubli.
 * ⚠️ ICI ET PAS DANS `fmt_grandeur()` : le formatage tourne 5 fois par seconde,
 *    un log par appel noierait la console — et une console noyée est une console
 *    qu'on cesse de lire.
 * ⚠️ NON FATALE, comme l'audit du mock juste en dessous : un affichage trop
 *    précis n'est pas une raison de priver l'opérateur de son écran.
 * ⛔ ET ELLE PARCOURT `n_grandeurs`, PAS `GRANDEURS_MAX` : les entrées au-delà
 *    de ce que la case déclare ne sont jamais lues, et les signaler ferait
 *    hurler l'audit sur des champs qui n'existent pas.
 */
static void descripteurs_auditer(void)
{
    int trous = 0;
    for (int i = 0; i < DN_UI_METRIQUES; i++) {
        int n = k_desc[i].n_grandeurs;
        if (n > DN_WIDGET_GRANDEURS_MAX) {
            n = DN_WIDGET_GRANDEURS_MAX;
        }
        for (int g = 0; g < n; g++) {
            if (k_desc[i].grandeurs[g].prec == DN_PREC_NON_RENSEIGNEE) {
                ESP_LOGE(TAG,
                         "k_desc[%s].grandeurs[%d].prec NON RENSEIGNEE — "
                         "l'affichage retombe au DIXIEME (comportement d'avant "
                         "dn4-6). Une decimale que la source ne porte pas est un "
                         "mensonge d'interface : renseigner DN_PREC_ENTIER ou "
                         "DN_PREC_DIXIEME.",
                         k_nom[i], g);
                trous++;
            }
        }
    }
    if (trous == 0) {
        ESP_LOGI(TAG, "precision d'affichage : %d cases auditees, 0 trou (AC9)",
                 DN_UI_METRIQUES);
    }
}

esp_err_t dn_ui_init(const dn_bootcfg_t *cfg, esp_err_t asset_err)
{
    ESP_RETURN_ON_FALSE(cfg, ESP_ERR_INVALID_ARG, TAG, "cfg NULL");

    descripteurs_auditer();

    /*
     * 🔴 LA FORME DU MOCK EST VÉRIFIÉE AU BOOT, PAS SUPPOSÉE (différé de dn3-1
     *    soldé en dn3-2). La rampe triangulaire n'est bornée QUE pour une
     *    période PAIRE et >= 2 : `demi = periode / 2`, et sur une période
     *    impaire `pos` n'atteint jamais `demi`, donc `max` n'est jamais atteint
     *    — un mock qui n'atteint pas sa borne ANNONCÉE est une étiquette qui
     *    ment, et personne ne le verrait à l'œil.
     *    ⚠️ Le défaut n'existait pas tant qu'il n'y avait qu'UNE période écrite
     *       en dur (20). Avec quatre entrées de table, il devient une faute de
     *       frappe possible — donc une garde, pas un commentaire.
     * ⚠️ NON FATALE : elle JOURNALISE. Un mock mal borné n'est pas une raison de
     *    priver l'opérateur de l'écran qui le lui montrerait.
     */
    for (int i = 0; i < DN_UI_METRIQUES; i++) {
        if (!k_mock[i].actif) {
            continue;
        }
        if (k_mock[i].periode_s < 2 || (k_mock[i].periode_s % 2) != 0) {
            ESP_LOGE(TAG,
                     "🔴 mock case %d (%s) : période %u s INVALIDE (doit être "
                     "PAIRE et >= 2). La rampe n'atteindra JAMAIS son max "
                     "annoncé de %d — le chiffre affiché mentirait sur sa forme.",
                     i, k_nom[i], (unsigned)k_mock[i].periode_s,
                     (int)k_mock[i].max);
        }
        if (k_mock[i].max <= k_mock[i].min) {
            ESP_LOGE(TAG,
                     "🔴 mock case %d (%s) : max %d <= min %d — la valeur ne "
                     "VARIERAIT PAS, et un mock figé est indiscernable d'un "
                     "affichage bloqué (exigence d'AC3).",
                     i, k_nom[i], (int)k_mock[i].max, (int)k_mock[i].min);
        }
    }

    s_asset_err = asset_err;
    s_panel = dn_display_panel();
    ESP_RETURN_ON_FALSE(s_panel, ESP_ERR_INVALID_STATE, TAG,
                        "panneau absent — dn_display_init() n'a pas tourné");

    s_draw_lines = cfg->draw_lines;
    s_draw_psram = cfg->draw_psram != 0;
    /*
     * ── LE MODE DE RENDU SE DÉDUIT DE num_fbs, ET C'EST UN RÉSULTAT DE MESURE ──
     *
     * À UN framebuffer, LVGL rend en PARTIEL et notre flush recopie la zone sale
     * dans le tampon que la DMA est en train de balayer. MESURÉ le 2026-08-15 :
     * cette écriture-là fait décrocher la DMA et l'image entière se déplace le
     * temps d'une trame, à CHAQUE mise à jour du label. Trois hypothèses ont été
     * éliminées à l'œil, chacune avec son témoin (lecture flash du fond,
     * parcours de cache pleine plage de draw_bitmap, débit instantané de la
     * copie) : aucune n'y change rien, et LVGL en pause l'écran est parfaitement
     * stable. Ce n'est donc pas le VOLUME écrit, c'est le FAIT d'écrire.
     *
     * À DEUX framebuffers, LVGL rend en DIRECT : il dessine dans le tampon caché
     * et le flush ne fait QUE basculer — zéro octet recopié, aucune écriture
     * dans le tampon balayé. C'est la seule parade connue, et elle n'est
     * devenue disponible qu'une fois AC5 prouvé sur la carte (les bascules vers
     * fb[0] ET fb[1] atteignent la dalle sous recalage événementiel).
     *
     * ⚠️ CE MODE EXIGE LA BRANCHE RESTART_IN_VSYNC=n. Avec le symbole à `y`, le
     *    double tampon est cassé (dn1-2, §4 bis) et le recalage est inerte : on
     *    afficherait une bascule sur deux, en silence. dn_recal_log_etat() le
     *    dit au boot ; ici on ne peut pas le refuser, parce que c'est bien la
     *    configuration qu'on veut mesurer.
     */
    s_direct_mode = (cfg->num_fbs >= 2);

    s_int_avant = dn_measure_internal_free();
    s_psram_avant = dn_measure_psram_free();

    /* L'abonnement vsync doit exister AVANT le premier flush : la tâche LVGL
     * démarre dès lvgl_port_init(), et le premier cycle peut tomber tout de
     * suite. Un sub à -1 ferait silencieusement retomber la synchro en mode
     * « off » — donc une mesure d'AC4 étiquetée « vsync » sans aucune synchro. */
    s_vsync_sub = dn_measure_vsync_subscribe("flush");
    ESP_RETURN_ON_FALSE(s_vsync_sub >= 0, ESP_ERR_NO_MEM, TAG,
                        "abonnement vsync du flush refusé");

    lvgl_port_cfg_t port_cfg = ESP_LVGL_PORT_INIT_CONFIG();
    /*
     * ⚠️ L'AFFINITÉ DE LA TÂCHE LVGL EST UNE VARIABLE MESURÉE, pas un réglage de
     *    confort — et sa première valeur a été une régression que j'ai
     *    introduite.
     *
     * La tâche avait été épinglée au CŒUR 1, pour que `cpu` sépare le rendu des
     * tâches console qui vivent sur le cœur 0 et rende la charge d'AC8
     * attribuable. Raison honnête, conséquence non anticipée : le pipeline
     * d'affichage entier (init du panneau, ISR vsync, et le chemin brut de
     * dn1-2 qui ne montre AUCUN artefact) vit sur le cœur 0. Mettre le rendu en
     * face, sur l'autre cœur, fait travailler les deux cœurs SIMULTANÉMENT sur
     * la mémoire externe — là où dn1-2 n'avait jamais qu'un seul demandeur.
     *
     * Le témoin qui a rendu cette variable suspecte : le chemin brut écrit
     * 614 400 octets dans le framebuffer visible, six fois de suite, SANS aucun
     * artefact (constat owner) — alors qu'un flush LVGL de 31 784 octets, vingt
     * fois plus petit, déplace l'image entière. Un défaut qui empire quand on
     * écrit VINGT FOIS MOINS n'est pas un défaut de bande passante.
     *
     * L'affinité passe par NVS (`set core <-1|0|1>`) comme num_fbs et
     * draw_lines, et pour la même raison : l'A/B se rejoue sans reflasher, donc
     * sans ajouter le binaire comme deuxième variable. Elle ne peut pas changer
     * à chaud — `lvgl_port_init()` crée la tâche une fois.
     */
    port_cfg.task_affinity = cfg->lvgl_core;
    s_affinity = cfg->lvgl_core;
    ESP_RETURN_ON_ERROR(lvgl_port_init(&port_cfg), TAG, "lvgl_port_init");

    lvgl_port_display_cfg_t disp_cfg = {
        /* io_handle NULL : c'est le bus 3-wire d'INITIALISATION, il ne transporte
         * aucun pixel. Le portage ne le lit que dans lvgl_port_add_disp() (voie
         * SPI/I80), jamais dans la voie RGB. */
        .io_handle = NULL,
        .panel_handle = s_panel,
        .control_handle = NULL,
        /* En mode direct, le portage IGNORE cette valeur et la remplace par
         * hres x vres — les tampons sont les framebuffers eux-mêmes. On la pose
         * quand même à la bonne chose pour que le refus éventuel du portage
         * (« direct mode must using full buffer ») ne soit pas déclenché par
         * nous. */
        .buffer_size = s_direct_mode
                           ? (uint32_t)(DN_LCD_H_RES * DN_LCD_V_RES)
                           : (uint32_t)(DN_LCD_H_RES * s_draw_lines),
        /* Pas de second draw buffer : notre flush est SYNCHRONE (il rend la main
         * une fois la copie faite), donc LVGL n'aurait rien à rendre en parallèle
         * pendant qu'on copie. Le second tampon coûterait autant que le premier
         * pour zéro recouvrement. À reconsidérer seulement si le flush devient
         * asynchrone — ce qu'il n'est pas ici. */
        .double_buffer = false,
        .hres = DN_LCD_H_RES,
        .vres = DN_LCD_V_RES,
        .monochrome = false,
        .color_format = LV_COLOR_FORMAT_RGB565,
        .flags = {
            /* DMA seulement quand le tampon est en RAM interne : sur ESP32-S3 la
             * PSRAM n'est pas DMA-capable pour ce driver, et le portage refuse
             * explicitement la combinaison des deux. */
            .buff_dma = s_draw_psram ? 0 : 1,
            .buff_spiram = s_draw_psram ? 1 : 0,
            .sw_rotate = 0,
            /* Pas d'inversion d'octets : les pixels sont lus par la DMA depuis la
             * PSRAM en 16 bits natifs. `swap_bytes` est un réglage de bus SÉRIE
             * (SPI/I80) — le poser ici afficherait des couleurs permutées. */
            .swap_bytes = 0,
            .full_refresh = 0,
            .direct_mode = s_direct_mode ? 1 : 0,
        },
    };
    const lvgl_port_display_rgb_cfg_t rgb_cfg = {
        .flags = {
            /*
             * ⚠️ L'ÉTIQUETTE MENTAIT : elle disait « le bounce buffer est
             *    DISQUALIFIÉ (watchdog) — dn1-2 » alors que dn1-4 l'a
             *    RÉHABILITÉ et en fait le défaut de la carte
             *    (DN_DEFAULT_BOUNCE_PX = 4800). Au-delà de la phrase, `bb_mode`
             *    n'est pas décoratif : il décide quel callback le portage
             *    enregistre (on_bounce_frame_finish au lieu de on_vsync,
             *    esp_lvgl_port_disp.c) — un piège armé pour la première mesure
             *    en num_fbs=2.
             *
             * ⛔ ON NE LE MET PAS À 1 « PARCE QUE C'EST PLUS JUSTE » : le
             *    portage n'arme cette mécanique qu'avec avoid_tearing, donc
             *    num_fbs>=2, et basculer le callback du panneau sans témoin
             *    serait un changement de comportement non mesuré — exactement ce
             *    que l'arbitrage dn1-3 (AC6) interdit. On le fait donc SUIVRE la
             *    réalité, couplé à avoid_tearing : la valeur reste 0 aujourd'hui
             *    (num_fbs=1 => s_direct_mode faux), et elle sera juste d'office
             *    le jour où num_fbs=2 sera rejoué. Ce jour-là : témoin vsync
             *    obligatoire (dn_measure_vsync_alive), le callback change.
             */
            .bb_mode = (s_direct_mode && dn_display_bounce_px() > 0) ? 1 : 0,
            /* Le portage exige num_fbs>=2 pour cette option
             * (esp_lvgl_port_disp.c:367) : elle ne s'allume donc qu'avec le
             * double tampon. Ce qu'elle fait ici : donner à LVGL les DEUX
             * framebuffers du driver comme tampons de rendu, au lieu d'allouer
             * un draw buffer partiel. */
            .avoid_tearing = s_direct_mode ? 1 : 0,
        },
    };

    s_disp = lvgl_port_add_disp_rgb(&disp_cfg, &rgb_cfg);
    ESP_RETURN_ON_FALSE(s_disp, ESP_FAIL, TAG, "lvgl_port_add_disp_rgb");

    if (!lvgl_port_lock(1000)) {
        ESP_LOGE(TAG, "verrou LVGL non pris en 1 s");
        return ESP_ERR_TIMEOUT;
    }
    /*
     * ON REMPLACE LE FLUSH DU PORTAGE. Le sien, en mode partiel, appelle
     * draw_bitmap et rend la main sans attendre quoi que ce soit
     * (esp_lvgl_port_disp.c:758) — il n'y a donc RIEN à synchroniser dedans, et
     * rien à instrumenter. Le nôtre porte les deux.
     * ⚠️ Les autres branchements du portage (invalidation, réveil de tâche,
     *    changement de résolution) sont CONSERVÉS : on ne remplace que le flush.
     */
    lv_display_set_flush_cb(s_disp, dn_ui_flush);

    /*
     * ── W8 (AC9) — LE REPEINT EN BANDES, ET SON MÉCANISME EST LU, PAS SUPPOSÉ ──
     *
     * L'hypothèse de la story : deux cases d'une même ligne ne fusionnent pas
     * parce qu'elles ne se CONTIENNENT ni ne s'INTERSECTENT ; les aligner sur
     * des bandes PLEINE LARGEUR les ferait fusionner.
     *
     * ✅ Le mécanisme est CONFIRMÉ dans le source du composant managé —
     *    `lv_refr.c:321-328` : LVGL envoie `LV_EVENT_INVALIDATE_AREA` avec
     *    l'aire, PUIS dédoublonne par `lv_area_is_in(nouvelle, sauvegardée)`.
     *    Il ne fusionne JAMAIS : il JETTE une aire CONTENUE dans une autre.
     *    ⇒ deux cases d'une même ligne élargies à 0..479 deviennent IDENTIQUES,
     *      donc la seconde est contenue dans la première, donc jetée.
     *
     * 🔴 MAIS L'ARITHMÉTIQUE DU DRAW BUFFER S'Y OPPOSE, ET C'EST CE QUE LA
     *    MESURE DOIT TRANCHER : le buffer fait `480 x draw_lines` PIXELS. À
     *    225 px de large, il tient 61 440 / 225 = 273 lignes, donc une case de
     *    156 passe en UN flush. À 480 de large il ne tient que `draw_lines`
     *    lignes — 128 par défaut, soit MOINS que les 156 d'une case. Une bande
     *    devrait donc être rendue en DEUX passes.
     *    ⇒ Prédiction : 2 flushes par ligne au lieu de 2, pour 74 880 px au
     *      lieu de 70 200 — soit STRICTEMENT PIRE. ⚠️ C'est une PRÉDICTION.
     *      `widget bandes on|off` la met à l'épreuve sans reflasher, et
     *      `set lines 160` permet d'essayer la seule config où elle tomberait.
     */
    lv_display_add_event_cb(s_disp, bandes_event_cb, LV_EVENT_INVALIDATE_AREA,
                            NULL);
    build_scene();
    s_timer = lv_timer_create(label_tick, 1000, NULL);
    lvgl_port_unlock();

    s_int_apres = dn_measure_internal_free();
    s_psram_apres = dn_measure_psram_free();

    if (s_direct_mode) {
        ESP_LOGI(TAG,
                 "LVGL %d.%d.%d prêt : rendu DIRECT sur les %d framebuffers du "
                 "driver — le flush BASCULE, il ne recopie rien",
                 LVGL_VERSION_MAJOR, LVGL_VERSION_MINOR, LVGL_VERSION_PATCH,
                 dn_display_num_fbs());
        ESP_LOGI(TAG,
                 "  draw_lines=%d IGNORÉ dans ce mode : les tampons de rendu "
                 "SONT les framebuffers.",
                 s_draw_lines);
    } else {
        ESP_LOGI(TAG,
                 "LVGL %d.%d.%d prêt : rendu PARTIEL, draw buffer %d x %d px "
                 "(%d o) en %s",
                 LVGL_VERSION_MAJOR, LVGL_VERSION_MINOR, LVGL_VERSION_PATCH,
                 DN_LCD_H_RES, s_draw_lines, DN_LCD_H_RES * s_draw_lines * 2,
                 s_draw_psram ? "PSRAM" : "RAM interne DMA");
    }
    ESP_LOGI(TAG, "  flush : synchro « %s », chemin « %s »",
             dn_flush_sync_name(s_sync), dn_flush_path_name(s_path));
    ESP_LOGI(TAG,
             "  coût en tas : RAM interne %u -> %u o (%d), PSRAM %u -> %u o (%d)",
             (unsigned)s_int_avant, (unsigned)s_int_apres,
             (int)((long)s_int_avant - (long)s_int_apres),
             (unsigned)s_psram_avant, (unsigned)s_psram_apres,
             (int)((long)s_psram_avant - (long)s_psram_apres));
    ESP_LOGW(TAG,
             "  ⚠️ ce delta N'INCLUT PAS les %d Ko statiques du tas de LVGL "
             "(LV_MEM_SIZE_KILOBYTES, réservés dans le .bss au link). "
             "L'instrument de CE coût-là est `ui`, qui imprime lv_mem_monitor().",
             CONFIG_LV_MEM_SIZE_KILOBYTES);
    return ESP_OK;
}

/* ── Accès ────────────────────────────────────────────────────────────────── */

lv_display_t *dn_ui_display(void) { return s_disp; }

bool dn_ui_first_frame_done(void) { return s_first_frame; }

bool dn_ui_wait_first_frame(uint32_t timeout_ms)
{
    /*
     * Sondage à 5 ms plutôt qu'un sémaphore : c'est appelé UNE FOIS, au boot,
     * juste avant d'allumer le rétroéclairage. Un sémaphore de plus donné depuis
     * le flush coûterait un test dans le chemin chaud pour une attente qui a lieu
     * une seule fois dans la vie du firmware.
     */
    int64_t fin = esp_timer_get_time() + (int64_t)timeout_ms * 1000;
    while (!s_first_frame) {
        if (esp_timer_get_time() > fin) {
            return false;
        }
        vTaskDelay(pdMS_TO_TICKS(5));
    }
    return true;
}

void dn_ui_get_stats(dn_flush_stats_t *out)
{
    if (!out) {
        return;
    }
    out->flushes = s_n_flush;
    out->cycles = s_n_cycles;
    out->px = s_px;
    out->copie_us = s_copie_us;
    out->attente_us = s_attente_us;
    out->max_px = s_max_px;
    out->max_copie_us = s_max_copie_us;
    out->timeouts = s_timeouts;
    out->noops = s_n_noop;
}

void dn_ui_reset_stats(void)
{
    s_n_noop = 0;
    s_n_flush = 0;
    s_n_cycles = 0;
    s_px = 0;
    s_copie_us = 0;
    s_attente_us = 0;
    s_max_px = 0;
    s_max_copie_us = 0;
    s_timeouts = 0;
}

dn_flush_sync_t dn_ui_get_sync(void) { return s_sync; }
void dn_ui_set_sync(dn_flush_sync_t mode) { s_sync = mode; }

bool dn_ui_force_full_redraw(void)
{
    /* bool et non void (revue) : sur timeout du verrou, la première version ne
     * faisait RIEN en silence — et `flush full` publiait ensuite des compteurs
     * sous la bannière « redessin PLEIN ÉCRAN forcé » pour un redessin jamais
     * demandé. L'instrument de preuve négative d'AC3 mesurait autre chose sans
     * le dire. */
    if (!lvgl_port_lock(1000)) {
        ESP_LOGE(TAG, "verrou LVGL non pris — AUCUN redessin demandé");
        return false;
    }
    lv_obj_invalidate(lv_screen_active());
    lvgl_port_unlock();
    return true;
}

void dn_ui_label_show(bool on)
{
    if (!lvgl_port_lock(1000)) {
        ESP_LOGE(TAG, "verrou LVGL non pris");
        return;
    }
    s_label_shown = on;
    /* LES DEUX labels, pas seulement celui de la vue affichée : en modèle
     * SCREENS l'autre écran survit à la commande, et le retrouver visible à la
     * bascule suivante ferait mentir `ui` — qui annonce un seul état pour un
     * réglage qui en aurait eu deux. */
    lv_obj_t *labels[2] = {s_label_dash, s_label_det};
    for (int i = 0; i < 2; i++) {
        if (!labels[i]) {
            continue;
        }
        if (on) {
            lv_obj_clear_flag(labels[i], LV_OBJ_FLAG_HIDDEN);
        } else {
            lv_obj_add_flag(labels[i], LV_OBJ_FLAG_HIDDEN);
        }
    }
    lvgl_port_unlock();
}

/*
 * ── dn4-6 : LE PORTEUR DE VALEURS — UN SEUL, ⛔ PAS `t0`/`t1`/`t2`/`t3` ───────
 *
 * 🔴 EMPILER `t2` ET `t3` À CÔTÉ DE `t0`/`t1` AURAIT CRÉÉ QUATRE ENDROITS OÙ LA
 *    RÈGLE « une valeur ABSENTE ne porte JAMAIS son unité » PEUT DIVERGER. Ce
 *    fichier a déjà payé exactement ça : le ternaire de couleur dupliqué entre
 *    `build_dashboard` et `case_poser` avait rendu SIMULÉE indiscernable
 *    d'ABSENTE sur les cases nues.
 *
 * ⛔ PAS DE SENTINELLE ENTIÈRE. Le dépôt en porte DEUX conventions
 *    contradictoires (`-1` pour `dn_link`, `INT32_MIN` pour `dn_capteurs`) et
 *    elles ne doivent pas être uniformisées à l'aveugle. L'absence est portée
 *    par un texte VIDE — c'est déjà la convention de `dn_widget_etat_t.txt[]`,
 *    et W10 la lit telle quelle.
 * ⚠️ `n` est le nombre de valeurs FOURNIES par l'appelant, ⛔ pas
 *    `desc->n_grandeurs` : une source peut en donner moins que la case n'en
 *    déclare, et c'est précisément le cas W10 (« la °C manque, le % est là »).
 */
typedef struct {
    const char *txt[DN_WIDGET_GRANDEURS_MAX]; /* NULL ou "" = ABSENTE (W10) */
    /* ⚠️ QUELLE unité s'applique — posé par celui qui a FORMATÉ, parce qu'il
     *    est le seul à connaître le NOMBRE. Le lire du texte serait deviner. */
    bool haute[DN_WIDGET_GRANDEURS_MAX];
    uint8_t n;
} dn_valeurs_t;

/*
 * ── POSER L'ÉTAT D'UNE CASE ──────────────────────────────────────────────────
 *
 * Le verrou LVGL est DÉJÀ pris par l'appelant public. C'était déjà la
 * convention de `case_vive_poser` (dn2-1) ; dn3-1 la promeut de « exception
 * locale documentée » à CONTRAT DE MODULE, écrit dans `dn_widget.h` avec ses
 * deux motifs. Voir cet en-tête : le second motif (le groupage d'invalidation
 * d'AC8) est NEUF et rend le contrat non négociable.
 *
 * `pose` : ⚠️ `s_active` compte AUSSI (correctif de revue 2026-08-16). Quand
 * LVGL est arrêté (`ui off`, `scene <mire>`, `tear`), le mutex reste LIBRE et le
 * texte se pose sans erreur — mais rien n'atteint la dalle. Chronométrer cette
 * poussée, c'était mesurer un geste qui n'a pas eu lieu.
 */
static void case_poser(int idx, dn_val_regime_t regime, const dn_valeurs_t *v,
                       int32_t brut0, const char *sec, bool *pose)
{
    dn_widget_etat_t *e = &s_wetat[idx];
    e->regime = regime;
    /* 🔴 TOUTES LES GRANDEURS SONT ÉCRITES, Y COMPRIS CELLES QU'ON NE DONNE PAS.
     *    Un `txt[i]` laissé tel quel garderait la valeur du TOUR PRÉCÉDENT :
     *    une source qui cesse de publier sa 3ᵉ grandeur figerait le dernier
     *    chiffre connu, sans badge et sans gris — exactement le mensonge que
     *    dn2-2 a chassé du dashboard. ⇒ non fournie = VIDE = « -- » gris (W10). */
    for (int i = 0; i < DN_WIDGET_GRANDEURS_MAX; i++) {
        const char *t = (v && i < v->n) ? v->txt[i] : NULL;
        snprintf(e->txt[i], sizeof(e->txt[i]), "%s", t ? t : "");
        /* ⚠️ REMIS À FAUX QUAND LA VALEUR N'EST PAS FOURNIE : un drapeau qui
         *    survit à sa valeur ferait porter « Gb/s » au tour suivant à un
         *    nombre exprimé en Mb/s — un mensonge d'une unité entière, et
         *    invisible. Même motif que le texte, remis à vide juste au-dessus. */
        e->echelle_haute[i] = (v && i < v->n) ? v->haute[i] : false;
    }
    e->brut[0] = brut0;
    snprintf(e->secondaire, sizeof(e->secondaire), "%s", sec ? sec : "");

    /* En modèle SCREENS le dashboard survit en arrière-plan et son label est mis
     * à jour même quand le détail est affiché — LVGL l'accepte, c'est le cas
     * « écran non chargé » qu'AC6 exige de ne pas planter. En REBUILD vue
     * détail, `racine` est NULL, l'état conservé sera posé à la prochaine
     * (re)construction : rien n'est perdu, rien n'est touché. */
    if (s_wobj[idx].racine) {
        /* LECTEUR 6/7 de l'override W11. 🔴 Celui-ci est le plus dangereux à
         * oublier : appeler `dn_widget_maj` sur une case DESSINÉE nue lirait
         * `w->valeur[1]`, `w->jauge` et `w->badge` — des pointeurs que le
         * chemin « nue » ne renseigne jamais. */
        if (case_est_widget(idx)) {
            dn_widget_maj(&k_desc[idx], e, &s_wobj[idx]);
        } else if (s_wobj[idx].valeur[0]) {
            /* Case NUE : un seul label, pas de modèle. Elle n'est alimentée par
             * personne aujourd'hui — ce chemin existe pour que « nue » reste une
             * question de FORME et jamais d'honnêteté le jour où dn4-1 lui
             * branchera une source. */
            lv_label_set_text(s_wobj[idx].valeur[0], e->txt[0][0] ? e->txt[0]
                                                                 : "--");
            /* 🔴 LES TROIS RÉGIMES, PAS DEUX (revue 2026-08-18). Ce ternaire
             *    disait `REELLE ? blanc : gris` — donc SIMULÉE peinte comme
             *    ABSENTE, alors que `widget pousser <idx>` sur une case nue EST
             *    le chemin nominal de l'instrument d'AC8 : un chiffre inventé
             *    s'affichait dans le gris de « aucune source », sans badge,
             *    pendant que la console annonçait SIMULEE. Trois signaux
             *    contradictoires pour un seul état.
             *    La convention vit dans `dn_val_regime_couleur()` et nulle part
             *    ailleurs — la dupliquer ici est ce qui avait produit l'écart. */
            lv_obj_set_style_text_color(s_wobj[idx].valeur[0],
                                        dn_val_regime_couleur(regime), 0);
        }
        if (pose) {
            *pose = s_active;
        }
    }

    /*
     * 🔴 LE DÉTAIL SUIT, ET C'EST LA MOITIÉ D'AC5 QUE L'ENTRÉE DE LEDGER NE
     *    DEMANDAIT PAS. Corriger `build_detail` et `detail_reparametrer` rend le
     *    détail honnête À SON OUVERTURE. Mais si la source meurt PENDANT que le
     *    détail est affiché, l'écran garderait le dernier chiffre connu sans
     *    dire que la source est morte — c'est-à-dire exactement le mensonge
     *    qu'on solde, décalé dans le temps au lieu de l'être dans l'espace.
     *    On rafraîchit donc le détail affiché, sous le MÊME verrou.
     */
    if (s_vue == DN_VUE_DETAIL && s_metrique == idx) {
        detail_reparametrer(idx);
    }
}

/*
 * ── LE FORMATAGE DES DIXIÈMES, EN UN SEUL ENDROIT ───────────────────────────
 * Virgule française. ⚠️ L'unité n'est PAS dans le texte : elle vit dans le
 * descripteur (`grandeurs[i].unite`) et c'est le modèle qui la concatène —
 * c'est ce qui permet la règle « une valeur ABSENTE ne porte JAMAIS son unité »
 * (« -- % » suggérerait qu'on sait de quoi on parle).
 * 🔴 LE SIGNE NE VIT PAS DANS LES DIXIÈMES : la division entière tronque VERS
 *    ZÉRO, donc -5 dixièmes rendait « 0,5 » (CR dn2-1). On sépare signe et
 *    magnitude au lieu de déduire le signe d'un quotient. Aucune métrique PC
 *    n'est négative aujourd'hui — la garde est là pour le jour où.
 */
static void fmt_dixiemes(char *out, size_t n, int dixiemes)
{
    int mag = dixiemes < 0 ? -dixiemes : dixiemes;
    snprintf(out, n, "%s%d,%d", dixiemes < 0 ? "-" : "", mag / 10, mag % 10);
}

/*
 * ── dn4-6 / AC9 : LA PRÉCISION, PAR GRANDEUR ET EN UN SEUL ENDROIT ──────────
 *
 * ⚠️ L'ARRONDI EST AU PLUS PROCHE, LOIN DE ZÉRO — ⛔ pas une troncature. Une
 *    puissance de 52,6 W affichée « 52 W » perd systématiquement vers le bas :
 *    sur une grandeur qui ne bouge que de 5 unités (`ASIC_POWER` 52..57), un
 *    biais d'un demi-watt n'est pas cosmétique, il rétrécit l'étendue VISIBLE
 *    et fausserait le critère de mouvement d'AC6, qui porte sur le texte AFFICHÉ.
 * 🔴 ET LE SIGNE NE VIT PAS DANS LES DIXIÈMES : la division entière tronque VERS
 *    ZÉRO (-5 dixièmes rendait « 0,5 », CR dn2-1). On sépare signe et magnitude
 *    dans les DEUX branches. ⛔ Ne pas re-casser cette garde.
 * ⚠️ `NON_RENSEIGNEE` retombe sur le DIXIÈME, c'est-à-dire sur le comportement
 *    d'AVANT dn4-6 — et l'oubli est dit ailleurs, une fois, par l'audit de
 *    descripteurs du boot (`descripteurs_auditer`). Le journaliser ICI le
 *    répéterait 5 fois par seconde et noierait la console.
 */
static void fmt_grandeur(char *out, size_t n, int dixiemes, dn_prec_t prec)
{
    if (prec == DN_PREC_ENTIER) {
        int neg = dixiemes < 0;
        int mag = neg ? -dixiemes : dixiemes;
        snprintf(out, n, "%s%d", neg ? "-" : "", (mag + 5) / 10);
        return;
    }
    fmt_dixiemes(out, n, dixiemes);
}

/* La précision d'une grandeur d'une case — RELUE du descripteur, jamais
 * supposée. ⚠️ Une case NUE n'a pas de descripteur exploitable ici : le repli
 * dixième est le comportement historique. */
static dn_prec_t prec_de(const dn_widget_desc_t *d, int i)
{
    if (!d || i < 0 || i >= DN_WIDGET_GRANDEURS_MAX) {
        return DN_PREC_DIXIEME;
    }
    return d->grandeurs[i].prec;
}

/*
 * ── L'ÉCHELLE HAUTE — LE SEUL ENDROIT QUI DÉCIDE (constat owner 2026-08-19) ──
 *
 * Rend le texte ET dit quelle unité s'applique. ⛔ Les deux ENSEMBLE, par un
 * seul appel : les séparer laisserait un chemin où le nombre est converti et
 * l'unité ne l'est pas — et « 100,0 Mb/s » pour 99999,9 Mb/s est un mensonge
 * d'un facteur mille qui a l'air parfaitement normal.
 * ⚠️ L'ARRONDI EST AU PLUS PROCHE : 999 999 dixièmes de Mb/s ÷ 1000 = 999,999,
 *    qui doit rendre « 100,0 Gb/s » et non « 99,9 ». Tronquer perdrait un
 *    dixième à chaque conversion, systématiquement vers le bas.
 * ⚠️ LA BASCULE EST À SENS UNIQUE ET SANS HYSTÉRÉSIS. Une valeur qui oscille
 *    autour de 1000,0 Mb/s fera clignoter l'unité. ⛔ C'est ASSUMÉ et pas un
 *    oubli : une hystérésis rendrait l'unité affichée DÉPENDANTE DE L'HISTOIRE,
 *    donc deux modules côte à côte pourraient afficher deux unités pour la même
 *    valeur. Le clignotement est honnête ; la mémoire ne le serait pas.
 */
static bool fmt_echelle(char *out, size_t n, int dixiemes,
                        const dn_widget_desc_t *d, int i)
{
    dn_prec_t p = prec_de(d, i);
    if (d && i >= 0 && i < DN_WIDGET_GRANDEURS_MAX &&
        d->grandeurs[i].seuil_haut > 0 && d->grandeurs[i].diviseur_haut > 0 &&
        dixiemes >= d->grandeurs[i].seuil_haut) {
        int32_t q = d->grandeurs[i].diviseur_haut;
        fmt_grandeur(out, n, (dixiemes + q / 2) / q, p);
        return true;
    }
    fmt_grandeur(out, n, dixiemes, p);
    return false;
}

/*
 * ── dn4-1 : LA TABLE MÉTRIQUE -> CASE, ET LA FORME DE SA SECONDAIRE ─────────
 *
 * ⛔ C'est la SEULE correspondance entre les index de `dn_link` et ceux de
 *    `dn_ui`. Les deux énumérations sont indépendantes et doivent le rester :
 *    supposer qu'elles coïncident serait une quatrième table câblée par index,
 *    au moment précis où on en supprime trois.
 */
typedef enum {
    DN_SEC_PC_AUCUNE = 0,
    DN_SEC_PC_RAM_GO,     /* « 12,1 / 32,0 Go » — verbatim addendum §1 */
    DN_SEC_PC_NET_DUPLEX, /* « v 985  ^ 48 »   — verbatim addendum §1 */
} dn_sec_pc_t;

/* ⚠️ LA SENTINELLE EST `-1`, MAIS L'INITIALISEUR DÉSIGNÉ, LUI, REMPLIT DE ZÉROS.
 *    Une entrée OUBLIÉE vaudrait donc `{0, 0}` — et `DN_UI_CASE_CPU == 0` : la
 *    nouvelle métrique irait écrire dans la case CPU, EN SILENCE, à 1 Hz.
 *    C'est la quatrième table câblée par index, dans le fichier même où on en
 *    supprime trois ; le commentaire ci-dessus prévient que les deux énumérations
 *    « doivent rester indépendantes », mais rien ne le VÉRIFIAIT.
 * 🔴 LE CORRECTIF DE 2026-08-18 NE POUVAIT PAS MARCHER, ET LA REVUE DU 2026-08-19
 *    L'A REPRODUIT À LA COMPILATION. Il posait
 *    `_Static_assert(sizeof(k_pc)/sizeof(k_pc[0]) == DN_LINK_METRIQUES)` — or ce
 *    tableau est déclaré `k_pc[DN_LINK_METRIQUES]` : le quotient vaut
 *    `DN_LINK_METRIQUES` **PAR DÉCLARATION**, quel que soit le nombre
 *    d'initialiseurs désignés réellement écrits. L'assertion comparait `X == X`
 *    et le commentaire promettait qu'elle cesserait de compiler : elle n'aurait
 *    JAMAIS échoué. ⛔ Un instrument qui ne peut pas voir le défaut qu'il annonce
 *    exclure — le trap n°2 de la méthodo, introduit PAR le correctif censé le
 *    fermer.
 * ⇒ LA SENTINELLE EST DÉSORMAIS DÉTECTABLE : on stocke la case **DÉCALÉE DE 1**,
 *   donc `0` = « entrée jamais renseignée » et ce n'est plus confondable avec
 *   `DN_UI_CASE_CPU`. `dn_ui_case_de_metrique()` rend `-1` et JOURNALISE, au lieu
 *   d'écrire dans la case CPU en silence à 1 Hz.
 *   (Correctif de revue 2026-08-19 ; dn4-6 s'apprête à ajouter une métrique.) */
static const struct {
    int idx_p1;             /* la case de dn_ui, DÉCALÉE DE 1. ⛔ 0 = NON RENSEIGNÉE */
    dn_sec_pc_t sec;
} k_pc[DN_LINK_METRIQUES] = {
    [DN_LINK_M_CPU] = {DN_UI_CASE_CPU + 1, DN_SEC_PC_AUCUNE},
    [DN_LINK_M_GPU] = {DN_UI_CASE_GPU + 1, DN_SEC_PC_AUCUNE},
    [DN_LINK_M_RAM] = {DN_UI_CASE_RAM + 1, DN_SEC_PC_RAM_GO},
    /* ⚠️ PLUS DE LIGNE SECONDAIRE POUR RÉSEAU (constat owner 2026-08-18) : ↓ et ↑
     * sont devenues les DEUX GRANDEURS de la case. Les laisser AUSSI en
     * secondaire afficherait les mêmes deux nombres deux fois dans le même
     * rectangle — le genre de redondance qui finit par diverger. */
    [DN_LINK_M_NET] = {DN_UI_CASE_RESEAU + 1, DN_SEC_PC_AUCUNE},
    [DN_LINK_M_DISK] = {DN_UI_CASE_DISQUE + 1, DN_SEC_PC_AUCUNE},
};

/* ⚠️ CE QUE CET ASSERT VÉRIFIE, ET CE QU'IL NE PEUT PAS VÉRIFIER. Il garde la
 *    correspondance de TAILLE entre les deux énumérations — utile le jour où
 *    `DN_UI_METRIQUES` change. ⛔ Il ne peut PAS voir une entrée manquante de
 *    `k_pc[]` : aucune construction C ne compte les initialiseurs désignés d'un
 *    tableau à taille explicite. C'est le décalage de 1 ci-dessus qui rend
 *    l'oubli détectable, et `dn_ui_case_de_metrique()` qui le JOURNALISE.
 *    ⛔ Ne pas réécrire ici une assertion qui a l'air de garder l'exhaustivité :
 *    c'est exactement le mensonge que la revue du 2026-08-19 a trouvé. */
_Static_assert(DN_LINK_METRIQUES <= DN_UI_METRIQUES,
               "chaque metrique PC doit pouvoir viser une case de dn_ui");

/* Le nombre de cases RÉELLEMENT mockées — COMPTÉ dans `k_mock[]`, jamais récité.
 * `widget mock on` imprimait « 4 » en dur : ajouter ou retirer un mock aurait
 * fait mentir la commande sans erreur de compilation, dans le fichier même où
 * dn4-1 corrige trois fois ce motif. (Correctif de revue 2026-08-18.) */
int dn_ui_mocks_actifs(void)
{
    int n = 0;
    for (int i = 0; i < DN_UI_METRIQUES; i++) {
        if (k_mock[i].actif) {
            n++;
        }
    }
    return n;
}

int dn_ui_case_de_metrique(dn_link_metrique_t m)
{
    if (m < 0 || m >= DN_LINK_METRIQUES) {
        return -1;
    }
    /* 🔴 L'ENTRÉE NON RENSEIGNÉE EST DÉTECTÉE ICI, ET ELLE PARLE. `idx_p1 == 0`
     * ne peut venir que du remplissage de zéros de l'initialiseur désigné : une
     * métrique a été ajoutée à `dn_link_metrique_t` sans sa ligne dans `k_pc[]`.
     * ⛔ Avant le 2026-08-19 ce cas rendait `0` = la case CPU, et la nouvelle
     * métrique écrasait le CPU à 1 Hz sans un mot. */
    if (k_pc[m].idx_p1 == 0) {
        ESP_LOGE(TAG, "k_pc[%d] NON RENSEIGNEE — metrique ajoutee sans sa case. "
                      "Aucune case ne sera mise a jour pour cette metrique.", (int)m);
        return -1;
    }
    int idx = k_pc[m].idx_p1 - 1;
    return (idx >= 0 && idx < DN_UI_METRIQUES) ? idx : -1;
}

/*
 * ── L'ENTRÉE UNIQUE DES CINQ MÉTRIQUES PC (dn4-1) ───────────────────────────
 * Contrat, motifs et raison d'être : voir `dn_ui.h`. Ici, l'essentiel en trois
 * lignes : UN verrou, UN formatage, UN `case_poser()`.
 */
bool dn_ui_pc_maj(dn_link_metrique_t m, const dn_link_vue_t *vue,
                  bool *label_pose)
{
    if (label_pose) {
        *label_pose = false;
    }
    int idx = dn_ui_case_de_metrique(m);
    if (idx < 0 || !vue) {
        return true; /* rien à faire — ⛔ pas un échec de verrou */
    }
    if (!lvgl_port_lock(1000)) {
        /* Pas de log ici : l'appelant (tâche dn_link) retente 250 ms plus tard,
         * un LOGE par tentative sous charge noierait la console — le refus se
         * lit dans le retour, comme dn_ui_force_full_redraw. */
        return false;
    }

    /* 🔴 LE MOCK ARMÉ A LA PRIORITÉ, ET C'EST L'INSTRUMENT QUI L'EXIGE. Sans
     *    cette garde, une trame réelle écraserait la rampe entre deux ticks de
     *    mock : la ligne « mock on » de §16.1 deviendrait injouable dès qu'un
     *    agent tourne, et la campagne mesurerait un régime hybride sans le dire.
     *    ⚠️ C'est le pendant exact du drapeau `s_poussee[]` de dn3-2 : un
     *       instrument délibérément armé ne se fait pas révoquer en silence. */
    if (s_mock_on && k_mock[idx].actif) {
        lvgl_port_unlock();
        return true;
    }

    /* 🔴 N TEXTES, UN SEUL FORMATAGE, UN SEUL `case_poser()` — le contrat de
     *    `dn_ui.h`. ⛔ Pas de `t2`/`t3` empilés à côté de `t0`/`t1` : voir le
     *    motif écrit au-dessus de `dn_valeurs_t`. */
    char txt[DN_WIDGET_GRANDEURS_MAX][DN_WIDGET_TXT_MAX];
    bool haute[DN_WIDGET_GRANDEURS_MAX] = {false};
    char sec[DN_WIDGET_SEC_MAX];
    for (int i = 0; i < DN_WIDGET_GRANDEURS_MAX; i++) {
        txt[i][0] = '\0';
    }
    sec[0] = '\0';
    /* LECTEUR 7/7 de l'override W11 — ⚠️ ET IL EST AJOUTÉ ICI DANS LE MÊME
     * GESTE QUE SON ÉNUMÉRATION (`s_nue_force[]`, plus haut). L'énumération FAIT
     * PARTIE de la garde de complétude : dn4-1 en avait ajouté un sans mettre le
     * compte à jour, et la revue du 2026-08-19 l'a relevé. La précision d'une
     * case NUE n'a pas de descripteur — `prec_de(NULL, …)` retombe au dixième,
     * c'est-à-dire au comportement historique de la case nue. */
    const dn_widget_desc_t *dsc = case_est_widget(idx) ? &k_desc[idx] : NULL;

    /* Une valeur n'existe QUE si la métrique est VIVANTE. Morte ou jamais vue :
     * la case le DIT au lieu de figer un chiffre qui n'a plus cours (AC7 de
     * dn2-2 — le différenciateur du brief en miniature, et il ne se renégocie
     * pas). ⚠️ `dn_link` borne déjà par métrique ; ce test-ci est la garde de
     * l'AFFICHAGE, redondante et assumée. */
    bool ok = (vue->etat == DN_LINK_VIVANTE) && vue->n > 0 && vue->v[0] >= 0;
    int32_t brut0 = 0;

    if (ok) {
        brut0 = vue->v[0] / 10; /* la jauge travaille en UNITÉS AFFICHÉES */

        /*
         * 🔴 W10 SURVIT À N GRANDEURS, ET C'EST UNE BOUCLE, PAS QUATRE `if`.
         *    Une grandeur non portée par la trame laisse son texte VIDE, et le
         *    modèle écrit « -- » EN GRIS sur CETTE LIGNE-LÀ uniquement : la case
         *    reste RÉELLE. ⛔ Jamais un tout-ou-rien — les grandeurs d'une case
         *    PC ont des sources INDÉPENDANTES (le % GPU ne meurt pas parce que
         *    le ventilateur se tait), contrairement à AMBIANCE dont les deux
         *    viennent d'un seul capteur.
         * ⚠️ `vue->n` EST LE COMPTE DU FIL, `dsc->n_grandeurs` CELUI DE LA CASE,
         *    ET ILS NE SONT PAS FORCÉMENT ÉGAUX. `RAM` en est la preuve vivante :
         *    elle reçoit DEUX valeurs (%, TOTAL Go) et n'affiche qu'UNE grandeur,
         *    le total partant en ligne secondaire. ⇒ La correspondance
         *    « valeur i du fil = grandeur i de la case » n'est PAS universelle ;
         *    elle est bornée ici par les DEUX comptes, et la secondaire lit le
         *    fil directement.
         */
        /* LECTEUR 3/3 de l'override de grandeurs — voir `desc_n()`. */
        int n_aff = (int)vue->n;
        if (dsc && desc_n(idx) < n_aff) {
            n_aff = desc_n(idx);
        }
        if (n_aff > DN_WIDGET_GRANDEURS_MAX) {
            n_aff = DN_WIDGET_GRANDEURS_MAX;
        }
        for (int i = 0; i < n_aff; i++) {
            if (vue->connue[i]) {
                haute[i] = fmt_echelle(txt[i], sizeof(txt[i]), vue->v[i], dsc, i);
            }
        }

        switch (k_pc[m].sec) {
        case DN_SEC_PC_RAM_GO:
            /* 🔴 LA SECONDAIRE EST CALCULÉE DEPUIS LE POURCENTAGE, ELLE N'EST PAS
             *    UNE SECONDE MESURE — c'est le motif écrit du mock de dn3-2, et
             *    il vaut PLUS ENCORE pour du réel : « 66,4 % » à côté de
             *    « 22,7 / 34,2 Go » doivent se répondre. Deux nombres échantillonnés
             *    séparément afficheraient tôt ou tard deux vérités contradictoires
             *    dans le même rectangle.
             * ⇒ L'agent envoie le TOTAL (v2, constant), le firmware en déduit
             *   l'utilisé : utilisé = % x total / 100. La cohérence est alors
             *   STRUCTURELLE, pas une discipline d'échantillonnage. */
            if (vue->n > 1 && vue->connue[1]) {
                int utilise = (int)((int64_t)vue->v[0] * vue->v[1] / 1000);
                char a[DN_WIDGET_TXT_MAX], b[DN_WIDGET_TXT_MAX];
                fmt_dixiemes(a, sizeof(a), utilise);
                fmt_dixiemes(b, sizeof(b), vue->v[1]);
                snprintf(sec, sizeof(sec), "%s / %s Go", a, b);
            } else {
                /* 🔴 W10 S'APPLIQUE AUSSI À LA SECONDAIRE (revue 2026-08-18).
                 * Sans ce `else`, `sec` restait VIDE et la ligne « 22,7 / 34,2 Go »
                 * DISPARAISSAIT au lieu de dire qu'elle ne sait pas — alors que le
                 * bloc dix lignes plus haut applique correctement la règle à la
                 * GRANDEUR (« -- » en gris, case RÉELLE). Deux traitements opposés
                 * pour la même absence, dans la même case.
                 * ⚠️ Non atteignable depuis l'agent courant (il envoie toujours v2),
                 *    mais LE PROTOCOLE L'AUTORISE : c'est le mécanisme même de W10,
                 *    celui par lequel la °C GPU peut manquer seule. */
                snprintf(sec, sizeof(sec), "-- / -- Go");
            }
            break;
        case DN_SEC_PC_NET_DUPLEX:
            /* ⛔ BRANCHE MORTE DEPUIS LA SÉANCE DU 2026-08-18, ET C'EST DÉLIBÉRÉ :
             * `k_pc[DN_LINK_M_NET].sec` vaut `DN_SEC_PC_AUCUNE` — ↓ et ↑ sont
             * devenues les DEUX GRANDEURS de la case, les remettre en secondaire
             * afficherait les mêmes deux nombres deux fois. AUCUNE métrique ne
             * sélectionne donc plus ce cas.
             * ⚠️ Le code est CONSERVÉ (le duplex peut revenir sur une autre case),
             * mais il ne s'exécute pas : ⛔ ne pas lire la justification ci-dessous
             * comme la description d'un chemin exercé. Relevé en revue 2026-08-18 —
             * l'arithmétique du commentaire est d'ailleurs fausse d'un octet
             * (3+1+15+2+3+1+15 = 40 oublie le NUL terminal, il en faut 41), et ça
             * ne s'est jamais vu PRÉCISÉMENT parce que le code est mort. */
            /* ⚠️ `LV_SYMBOL_DOWN`/`UP` (U+F078/U+F077), PAS les flèches Unicode
             *    U+2193/U+2191 : celles-ci sont HORS latin-1 et le glyphe absent
             *    serait dessiné EN SILENCE. Les deux codepoints FontAwesome ont
             *    été VÉRIFIÉS présents dans les `.c` de police. */
            if (vue->n > 1 && vue->connue[1]) {
                char a[DN_WIDGET_TXT_MAX], b[DN_WIDGET_TXT_MAX];
                fmt_dixiemes(a, sizeof(a), vue->v[0]);
                fmt_dixiemes(b, sizeof(b), vue->v[1]);
                /* ⚠️ PRÉCISION EXPLICITE `%.12s` : sans elle, GCC refuse de
                 *    prouver que 3+1+15+2+3+1+15 = 40 tient dans les 40 octets
                 *    de `DN_WIDGET_SEC_MAX` (-Werror=format-truncation). Les
                 *    bornes de `k_metriques[]` plafonnent en fait le texte à
                 *    8 caractères (« 100000,0 ») : la précision ne peut PAS
                 *    tronquer une valeur réelle — c'est une ceinture, pas un
                 *    écrêtage silencieux. */
                snprintf(sec, sizeof(sec),
                         LV_SYMBOL_DOWN " %.12s  " LV_SYMBOL_UP " %.12s", a, b);
            }
            break;
        case DN_SEC_PC_AUCUNE:
        default:
            break;
        }
    }

    dn_valeurs_t val = {.n = DN_WIDGET_GRANDEURS_MAX};
    for (int i = 0; i < DN_WIDGET_GRANDEURS_MAX; i++) {
        val.txt[i] = txt[i];
        val.haute[i] = haute[i];
    }
    case_poser(idx, ok ? DN_VAL_REELLE : DN_VAL_ABSENTE, &val, brut0, sec,
               label_pose);
    lvgl_port_unlock();
    return true;
}

/*
 * ── LE POINT D'ENTRÉE HISTORIQUE DE dn2-2 ────────────────────────────────────
 * ⛔ CE PARAGRAPHE AFFIRMAIT « Il SURVIT, et ce n'est pas un doublon : il garde
 *    exécutable le témoin de non-régression v1 d'AC2 ». C'EST FAUX — le bloc
 *    ci-dessous le démontre, et les deux ont cohabité à trois lignes d'écart,
 *    l'affirmation AVANT sa réfutation, jusqu'à la revue du 2026-08-19. `dn_ui.h`
 *    avait été corrigé ; ce fichier, non. Retiré : ce qui reste vrai est écrit
 *    ci-dessous, et une seule fois.
 */
/* 🔴 ELLE N'A AUCUN APPELANT DANS LE FIRMWARE — constaté par grep en revue le
 * 2026-08-18, et sa justification publiée était FAUSSE. `dn_ui.h` écrivait
 * « conservé pour que le témoin de non-régression v1 reste exécutable » : le
 * témoin v1 d'AC2 passe en réalité par `dn_link_ingest_ligne` -> `pousser_metrique`
 * -> `dn_ui_pc_maj`, jamais par ici. ⇒ Ce qui n'est jamais appelé ne prouve rien
 * (leçon T4, citée trois fois dans ce dépôt).
 * ⚠️ ELLE EST CONSERVÉE comme point d'entrée mono-métrique, mais son piège est
 * désormais fermé : `.age_us = 0` injectait un échantillon de latence à **0 µs**
 * dans `s_lat_min/somme/n` à chaque appel, écrasant le minimum et tirant la
 * moyenne vers le bas SANS AUCUN SIGNAL. `-1` veut dire « pas d'horodatage », et
 * `pousser_metrique` sait ne pas chronométrer ce cas. */
bool dn_ui_cpu_maj(int dixiemes, bool valide, bool *label_pose)
{
    dn_link_vue_t v = {
        .etat = valide ? DN_LINK_VIVANTE : DN_LINK_MORTE,
        .v = {(valide && dixiemes >= 0 && dixiemes <= 1000) ? dixiemes : -1},
        .connue = {true},
        .n = 1,
        .age_us = -1,  /* ⛔ PAS 0 : « inconnu », pas « instantané » */
        .recu_us = -1, /* ⛔ idem — le champ ajouté le 2026-08-19 vaudrait 0 par
                        * défaut, soit « reçue à l'instant du boot », ce qui
                        * injecterait des latences absurdes chez un futur appelant */
        .seq = 0,
    };
    return dn_ui_pc_maj(DN_LINK_M_CPU, &v, label_pose);
}

/* AC5 — RELU des pointeurs LVGL réellement construits, jamais récité du
 * descripteur. Voir `dn_ui.h` pour le motif. */
/* 🔴 `idx == DN_UI_METRIQUES` DÉSIGNE LE WIDGET DE DÉMO — et c'est le correctif
 * de revue du 2026-08-18. Cette fonction ne lisait que `s_wobj[0..5]`, or le
 * widget de démo (`s_demo`) est LE SEUL objet du firmware à combiner
 * `n_grandeurs = 2` ET `indicateur = true`, donc le SEUL à déclencher l'abandon
 * de la ligne secondaire que la commande `widget` prétend rapporter. Aucune des
 * six cases réelles ne peut produire « secondaire non » (CPU/GPU/RÉSEAU n=2 sans
 * jauge -> 148 ≤ 156 ; RAM n=1 avec jauge -> 128 ≤ 156) : la colonne était donc
 * CONSTANTE PAR CONSTRUCTION. ⛔ Un instrument qui ne peut pas voir le cas qu'il
 * a été construit pour prouver est une gate décorative. */
/* L'unité RÉELLEMENT affichée par une case, échelle haute comprise — exposée
 * pour que la console cesse d'en avoir sa PROPRE copie. Voir `dn_widget_unite`. */
const char *dn_ui_case_unite(int idx, int grandeur)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES || !case_est_widget(idx)) {
        return NULL;
    }
    return dn_widget_unite(&k_desc[idx], &s_wetat[idx], grandeur);
}

/*
 * ── dn4-6 / AC10 : CE QUE LE DÉTAIL A RÉELLEMENT POSÉ ────────────────────────
 *
 * 🔴 CONSTAT OWNER DU 2026-08-19 : *« la 3ᵉ grandeur est tronquée »*. Or la
 *    ligne complète mesure **396 px pour 446 utiles** — elle DEVRAIT tenir.
 *    ⛔ On ne corrige pas un défaut qu'on n'a pas expliqué : « mettre deux par
 *    ligne » ferait peut-être disparaître le symptôme sans toucher la cause, et
 *    le même défaut reviendrait à la 4ᵉ grandeur.
 * ⇒ Cet accesseur RELIT le label construit : son texte, sa largeur RÉELLE, et
 *   celle de son parent. Trois nombres qui suffisent à trancher entre « le
 *   texte est trop large », « le panneau est trop étroit » et « le texte n'est
 *   pas celui qu'on croit ».
 * ⚠️ Il rend `false` si le détail n'est PAS affiché : en vue dashboard les
 *    pointeurs sont NULL, et répondre quand même inventerait une géométrie.
 */
bool dn_ui_detail_label(const char **txt, int *w, int *w_parent, int *x)
{
    if (s_vue != DN_VUE_DETAIL || !s_det_valeur) {
        return false;
    }
    if (!lvgl_port_lock(1000)) {
        return false;
    }
    if (txt) {
        *txt = lv_label_get_text(s_det_valeur);
    }
    if (w) {
        *w = (int)lv_obj_get_width(s_det_valeur);
    }
    if (x) {
        *x = (int)lv_obj_get_x(s_det_valeur);
    }
    if (w_parent) {
        lv_obj_t *p = lv_obj_get_parent(s_det_valeur);
        *w_parent = p ? (int)lv_obj_get_width(p) : -1;
    }
    lvgl_port_unlock();
    return true;
}

bool dn_ui_widget_pointeurs(int idx, int *n_grandeurs, bool *jauge, bool *sec)
{
    const dn_widget_t *o = NULL;
    if (idx >= 0 && idx < DN_UI_METRIQUES) {
        o = &s_wobj[idx];
    } else if (idx == DN_UI_METRIQUES) {
        o = &s_demo;
    }
    if (!o || !o->racine) {
        return false;
    }
    if (n_grandeurs) {
        int n = 0;
        for (int i = 0; i < DN_WIDGET_GRANDEURS_MAX; i++) {
            if (o->valeur[i]) {
                n++;
            }
        }
        *n_grandeurs = n;
    }
    if (jauge) {
        *jauge = o->jauge != NULL;
    }
    if (sec) {
        *sec = o->sec != NULL;
    }
    return true;
}

/*
 * ── LA VARIANTE MULTI-GRANDEURS (D6) — UNE CASE, DEUX GRANDEURS ──────────────
 *
 * Jusqu'à dn2-1 c'étaient DEUX cases (TEMP. idx 4, HUMIDITÉ idx 5) écrites sous
 * UN SEUL verrou. D6 les fusionne en UNE case « AMBIANCE » (idx 5) à deux
 * grandeurs, et la place libérée (idx 4) reçoit VENTILOS.
 *
 * 🔴 L'EXIGENCE DU VERROU UNIQUE NE DISPARAÎT PAS, ELLE SE RENFORCE. Elle
 *    portait sur deux cases voisines ; elle porte maintenant sur deux valeurs de
 *    la MÊME case. Les poser sous deux verrous laisserait une trame afficher une
 *    température neuve à côté d'une humidité périmée — dans un seul rectangle,
 *    ce qui serait encore plus difficile à lire comme une incohérence.
 * 🔴 `valide == false` GRISE LES DEUX ENSEMBLE : un capteur muet l'est pour ses
 *    deux grandeurs, « il n'y a pas de demi-silence ». C'est structurel ici, et
 *    non plus une discipline : le RÉGIME est porté par la case, pas par la
 *    grandeur. On ne PEUT plus griser une moitié.
 */
bool dn_ui_ambiance_maj(int temp_dixiemes, int hum_dixiemes, bool valide,
                        bool *label_pose)
{
    if (label_pose) {
        *label_pose = false;
    }
    if (!lvgl_port_lock(1000)) {
        return false;
    }
    char t_txt[DN_WIDGET_TXT_MAX];
    char h_txt[DN_WIDGET_TXT_MAX];
    /* ⚠️ CE SONT LES BORNES PHYSIQUES DU BME680, LES MÊMES QUE dn_capteurs —
     * corrigé le 2026-08-17. Le commentaire qui vivait ici affirmait qu'elles
     * étaient « DIFFÉRENTES » et gardaient « l'affichage, pas la plausibilité » :
     * c'était faux, les quatre chiffres sont identiques à ceux de dn_capteurs.c.
     * Un commentaire qui affirme un invariant que le code ne tient pas est pire
     * que pas de commentaire. Ici, elles sont un GARDE-FOU REDONDANT : la valeur
     * est déjà bornée en amont, cette couche protège contre un appelant futur.
     * ⚠️ La température peut être NÉGATIVE — « -400 <= x » n'est pas « 0 <= x ». */
    bool ok_t = valide && temp_dixiemes >= -400 && temp_dixiemes <= 850;
    bool ok_h = valide && hum_dixiemes >= 0 && hum_dixiemes <= 1000;
    /* UN SEUL régime pour la case : les deux grandeurs vivent ou se taisent
     * ensemble. Si l'une des deux est hors bornes alors que `valide` est vrai,
     * c'est la case entière qui devient ABSENTE — un capteur qui rend une
     * grandeur aberrante n'est pas à moitié crédible. */
    bool ok = ok_t && ok_h;
    if (ok) {
        /*
         * 🔴 LE SIGNE NE VIT PAS DANS LES DIXIÈMES — CR du 2026-08-17.
         * L'ancien code faisait `e = temp/10` puis redressait le seul chiffre des
         * dixièmes. Or la division entière TRONQUE VERS ZÉRO : pour −5 dixièmes,
         * `e` vaut 0, pas « -0 » — et la case affichait « 0,5 °C » pour −0,5 °C.
         * Le correctif d'origine ne traitait que |x| >= 10, pas la bande
         * −0,1..−0,9 où le signe disparaît ENTIÈREMENT. On sépare donc le signe
         * de la magnitude au lieu de le déduire d'un quotient.
         */
        int mag = temp_dixiemes < 0 ? -temp_dixiemes : temp_dixiemes;
        snprintf(t_txt, sizeof(t_txt), "%s%d,%d", temp_dixiemes < 0 ? "-" : "",
                 mag / 10, mag % 10);
        snprintf(h_txt, sizeof(h_txt), "%d,%d", hum_dixiemes / 10,
                 hum_dixiemes % 10);
    } else {
        t_txt[0] = '\0';
        h_txt[0] = '\0';
    }
    /* Un seul appel, donc un seul verrou, donc une seule trame : le motif de
     * `case_vive_poser` est désormais tenu par la STRUCTURE et non par la
     * discipline de l'appelant. */
    dn_valeurs_t val = {.txt = {t_txt, h_txt}, .n = 2};
    case_poser(DN_UI_CASE_AMB, ok ? DN_VAL_REELLE : DN_VAL_ABSENTE, &val, 0, NULL,
               label_pose);
    lvgl_port_unlock();
    return true;
}

/*
 * ── LA BARRE HEURE/DATE (dn3-2, AC3/AC4) ────────────────────────────────────
 *
 * Appelée par la tâche `dn_rtc` à 2 Hz. Même contrat que les autres entrées
 * publiques : elle prend le verrou LVGL elle-même, et `false` signifie « verrou
 * non pris ⇒ RIEN n'a été modifié », charge à l'appelant de retenter.
 *
 * 🔴 L'INVALIDATION EST CONDITIONNÉE AU CHANGEMENT DE TEXTE, ET C'EST TOUT LE
 *    MÉCANISME D'AC4. La barre fait 480 x 70 = 33 600 px, soit 96 % d'une case :
 *    la réécrire à chaque appel coûterait une 7e case vivante à 2 Hz. En régime
 *    HH:MM le texte ne bouge qu'au CHANGEMENT DE MINUTE ⇒ le calage sur la
 *    minute qu'AC4 exige est structurel, et non confié à un timer libre qui
 *    pourrait retarder jusqu'à 59 s.
 * ⚠️ `barre_composer` compare AUSSI `fiable` : une bascule FIABLE -> NON FIABLE
 *    change la COULEUR sans forcément changer le texte (« --:-- » reste
 *    « --:-- »). Sans ce troisième terme, une horloge qui meurt garderait ses
 *    couleurs de vivante.
 */
bool dn_ui_heure_maj(const dn_rtc_heure_t *h, bool fiable, bool *label_pose)
{
    if (label_pose) {
        *label_pose = false;
    }
    if (!lvgl_port_lock(1000)) {
        return false;
    }
    if (barre_composer(h, fiable)) {
        barre_ecrire_nolock();
        if (label_pose) {
            /* ⚠️ `s_active` compte AUSSI : après `ui off`, `scene` ou `tear`, le
             * verrou reste libre et le texte se pose sans erreur — mais rien
             * n'atteint la dalle. Annoncer « posé » serait mesurer un geste qui
             * n'a pas eu lieu (correctif de revue 2026-08-16). */
            *label_pose = s_active;
        }
    }
    lvgl_port_unlock();
    return true;
}

void dn_ui_barre_secondes_set(bool on)
{
    if (on == s_barre_secondes) {
        return;
    }
    s_barre_secondes = on;
    /* Repose immédiatement : sans ça, en régime HH:MM, le passage à HH:MM:SS ne
     * se verrait qu'à la prochaine minute — et l'A/B mesurerait la mauvaise
     * branche pendant jusqu'à 59 s. C'est exactement le défaut d'A/B que dn3-1
     * a payé sur le groupage (`.h` et code en désaccord). */
    dn_rtc_heure_t h;
    bool fiable = dn_rtc_lire(&h);
    if (lvgl_port_lock(1000)) {
        if (barre_composer(&h, fiable)) {
            barre_ecrire_nolock();
        }
        lvgl_port_unlock();
    }
    ESP_LOGI(TAG, "cadence de la barre : %s",
             on ? "HH:MM:SS (1 Hz)" : "HH:MM (au changement de minute)");
}

bool dn_ui_barre_secondes(void) { return s_barre_secondes; }

/* W8/AC9 — le repeint en BANDES. ⚠️ Aucune reconstruction : le drapeau agit sur
 * la PROCHAINE invalidation, donc l'A/B se joue sans perdre la scène ni la
 * fenêtre de mesure. C'est ce qui le distingue de `widget nue`. */
void dn_ui_bandes_set(bool on)
{
    if (on == s_bandes) {
        return;
    }
    s_bandes = on;
    ESP_LOGW(TAG, "repeint en BANDES %s — INSTRUMENT d'AC9 (W8), pas un réglage "
                  "produit. ⚠️ une bande fait 480 x %d px : si draw_lines (%d) "
                  "est INFÉRIEUR à la hauteur d'une case, LVGL la rendra en "
                  "PLUSIEURS passes et le levier sera contre-productif.",
             on ? "ARMÉ" : "coupé", ui_case_h(), s_draw_lines);
}

bool dn_ui_bandes(void) { return s_bandes; }

/*
 * 🔴 COPIE SOUS VERROU, PAS DE POINTEUR NU — correctif de revue (2026-08-18).
 *    Les deux getters rendaient `s_barre_h` / `s_barre_d` tels quels, et la
 *    console les passait à `printf` depuis SA tâche, sans verrou, pendant que
 *    la tâche RTC les réécrivait par `memcpy` à 2 Hz. Aux transitions de
 *    longueur (« HEURE NON POSÉE » -> « VEN. 06 AOÛT ») une lecture déchirée
 *    rendait une chaîne épissée dans un DIAGNOSTIC — au milieu d'une campagne
 *    où l'opérateur lit justement ces lignes pour trancher.
 * ⚠️ Rien à l'écran n'était affecté : les labels LVGL, eux, sont écrits sous
 *    verrou. C'est l'instrument qui mentait, pas la barre.
 */
bool dn_ui_barre_txt(char *heure, size_t n_heure, char *date, size_t n_date)
{
    if (heure && n_heure) {
        heure[0] = '\0';
    }
    if (date && n_date) {
        date[0] = '\0';
    }
    if (!lvgl_port_lock(200)) {
        return false;
    }
    if (heure && n_heure) {
        snprintf(heure, n_heure, "%s", s_barre_h);
    }
    if (date && n_date) {
        snprintf(date, n_date, "%s", s_barre_d);
    }
    lvgl_port_unlock();
    return true;
}

bool dn_ui_barre_dessinee(void)
{
    /* RELU de l'état réel, pas récité : les labels peuvent être NULL entre un
     * démontage et la reconstruction, et `s_active` peut être faux.
     * 🔴 ET L'ÉCRAN CHARGÉ EST CROISÉ — correctif de revue (2026-08-18). En
     *    `DN_NAV_SCREENS` la transition détail ne détruit que `s_bar` et
     *    `s_demo` : le dashboard et ses deux labels SURVIVENT, donc la fonction
     *    répondait « DESSINEE » pendant que l'écran de détail était sur la
     *    dalle — quand le MÊME état visuel répond « PAS dessinee » en REBUILD.
     *    Un instrument dont la réponse dépend du mode de nav et pas de ce qu'on
     *    voit ne mesure pas ce qu'il annonce. */
    if (s_barre_heure == NULL || s_barre_date == NULL || !s_active) {
        return false;
    }
    return s_scr_dash != NULL && lv_screen_active() == s_scr_dash;
}

/*
 * ── LE MOCK VENTILOS (AC3) — ET IL NE PEUT PAS SE FAIRE PASSER POUR DU RÉEL ──
 *
 * Appelée depuis le tick 1 Hz de LVGL, où le verrou est DÉJÀ détenu par le
 * portage. D'où le suffixe `_nolock` : c'est le contrat de `dn_widget`, et le
 * nom le dit pour qu'aucun appelant futur ne se trompe.
 *
 * ⛔ PAS DE TÂCHE DÉDIÉE, PAS DE SOMMEIL. Le REPL EST le transport PC (dn2-2) :
 *    une commande console qui dort couperait la liaison. Et un mock qui produit
 *    un nombre n'a aucun travail long à faire — lui donner une tâche serait du
 *    coût sans contrepartie.
 *
 * La FORME est annoncée et vérifiable : rampe triangulaire DN_MOCK_MIN ->
 * DN_MOCK_MAX -> DN_MOCK_MIN, période DN_MOCK_PERIODE_S, dérivée du TEMPS
 * ABSOLU (jamais d'un compteur incrémenté : un `++` dans un timer de 1 000 ms
 * dérive de tout le retard que le timer prend, et il en prend).
 */
static void mock_tick_nolock(void)
{
    /*
     * 🔴 NE RIEN POSER SI RIEN N'A CHANGÉ — DÉFAUT MESURÉ LE 2026-08-17.
     *
     * La première version posait l'état à CHAQUE tick, mock coupé compris. Or
     * `lv_label_set_text` invalide INCONDITIONNELLEMENT, même avec un texte
     * identique : la case VENTILOS se repeignait donc 1 fois par seconde en
     * affichant « -- », pour rien.
     *
     * Ce n'est pas qu'un gaspillage : c'est un INSTRUMENT FAUSSÉ. Le témoin
     * d'AC8 (« 0 poussée pendant 20 s ») a compté 24 cycles de redessin là où
     * le capteur seul, à 5 s, n'en justifie que 4 — 20 fantômes, exactement le
     * nombre de ticks. La contribution parasite qu'on croyait quantifier était
     * donc à 83 % fabriquée par la mesure elle-même. Trouvé en REGARDANT le
     * chiffre du témoin plutôt qu'en le notant : 24 ≠ 4 n'a pas d'explication
     * innocente.
     */
    uint32_t s = (uint32_t)(esp_timer_get_time() / 1000000);

    /* ⚠️ UNE BOUCLE SUR LES CASES, et le branchement porte sur la TABLE
     * (`k_mock[i].actif`), jamais sur un index nommé. Même règle que
     * `build_dashboard` : ajouter ou retirer un mock est une ligne de table. */
    for (int i = 0; i < DN_UI_METRIQUES; i++) {
        if (!k_mock[i].actif) {
            continue;
        }

        if (!s_mock_on) {
            /*
             * 🔴 DÉCISION D1 DE LA REVUE DU 2026-08-18 — LE TICK ÉTAIT UN SECOND
             *    ÉCRIVAIN SUR LA CASE QUE LA CAMPAGNE AC8 MESURAIT.
             *
             *    Le protocole publié dit « mock isolé », c'est-à-dire
             *    `widget mock off` — et c'est EXACTEMENT ce réglage qui armait
             *    le défaut : après chaque `widget pousser <i>`, le régime valait
             *    SIMULEE, ce tick voyait `!= ABSENTE` et REPOSAIT ABSENTE. Soit
             *    UN REDESSIN DE PLUS PAR POUSSÉE, jamais compté comme une
             *    poussée, dans le dénominateur de la mesure la plus
             *    spectaculaire de la story.
             *
             *    ⇒ Une poussée est un acte DÉLIBÉRÉ de l'opérateur ; le mock
             *    coupé n'a aucune raison de la révoquer. `widget mock on` puis
             *    `off` rend la case au régime naturel (drapeau levé plus bas).
             * ⚠️ dn3-2 : le drapeau est PAR CASE. Un drapeau unique aurait
             *    laissé les trois autres mocks se faire révoquer — le même
             *    défaut, simplement déplacé d'une case aux trois autres.
             */
            /*
             * 🔴 dn4-1 — LE TICK ÉTAIT UN SECOND ÉCRIVAIN SUR DES CASES QUI ONT
             *    MAINTENANT UNE SOURCE RÉELLE, ET ÇA SE VOYAIT.
             *
             *    Le test était `regime != DN_VAL_ABSENTE`. Il a été écrit quand
             *    GPU/RAM/RÉSEAU/VENTILOS n'avaient AUCUNE source : « pas ABSENTE »
             *    y voulait dire « le mock l'a peinte », et la remettre à ABSENTE
             *    était juste. dn4-1 leur donne une source ⇒ leur régime devient
             *    RÉELLE, et ce tick les REPEIGNAIT EN GRIS UNE FOIS PAR SECONDE,
             *    juste avant que `dn_link` ne les repose. Deux écrivains qui se
             *    battent sur la même case, à 1 Hz.
             *
             *    ⚠️ SYMPTÔME VISIBLE : les quatre cases clignotent « -- » gris.
             *    ⚠️ SYMPTÔME MESURÉ, et c'est LUI qui a trouvé le défaut : le
             *       régime réel rendait **408 flushes** là où 223 poussées de
             *       métrique + 9 d'AMBIANCE en justifiaient **232**. L'écart,
             *       176, vaut 4 cases x 45 s. La prédiction d'AC7 avait nommé
             *       « le nombre de cycles/s » comme ce qu'elle ne couvrait pas —
             *       il a doublé (2,19 au lieu de ~1,2), et c'est ce qui a fait
             *       ouvrir le dossier au lieu de publier le chiffre.
             *
             * ⇒ LE TICK NE RÉVOQUE QUE CE QU'IL A LUI-MÊME PEINT : `SIMULEE`.
             *   Une case RÉELLE ne lui appartient pas ; une case ABSENTE n'a
             *   rien à recevoir (et la reposer coûterait un redessin pour rien —
             *   c'est le défaut mesuré du 2026-08-17, 24 cycles pour 4).
             */
            if (!s_poussee[i] && s_wetat[i].regime == DN_VAL_SIMULEE) {
                case_poser(i, DN_VAL_ABSENTE, NULL, 0, NULL, NULL);
            }
            continue;
        }

        /* Le mock reprend la main : il EST la source de cette case, sa poussée
         * manuelle n'a plus cours. */
        s_poussee[i] = false;

        uint32_t periode = k_mock[i].periode_s;
        /* 🔴 LA GARDE DÉSARME, elle ne se contente plus de journaliser
         *    (revue 2026-08-18). `dn_ui_init` détecte bien une période < 2 mais
         *    ne l'empêchait pas d'arriver ici, où `periode / 2` vaut 0 : la
         *    division entière par zéro lève une exception, et ce build a
         *    `CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y` — « ni console, ni flash,
         *    RESET physique ». La garde avait été ajoutée POUR cette classe de
         *    faute de frappe et laissait passer le seul cas qui brique la carte. */
        if (periode < 2) {
            continue;
        }
        uint32_t phase = s % periode;
        uint32_t demi = periode / 2;
        /* Triangle : on monte sur la première moitié, on descend sur la
         * seconde. ⚠️ Ne tient QUE pour une période PAIRE >= 2 — c'est pour ça
         * que la table les impose, et le boot le vérifie (la boucle de
         * validation de `dn_ui_init`). ⚠️ La garde ci-dessus DÉSARME l'entrée
         * fautive ; le boot, lui, se contente de la JOURNALISER. */
        uint32_t pos = phase < demi ? phase : (periode - phase);
        int32_t v = k_mock[i].min +
                    (int32_t)((k_mock[i].max - k_mock[i].min) * pos / demi);

        char txt[DN_WIDGET_TXT_MAX];
        snprintf(txt, sizeof(txt), "%d", (int)v);

        /*
         * Ne pas reposer un texte identique : `lv_label_set_text` invalide
         * INCONDITIONNELLEMENT, même à texte égal, et ce redessin-là ne
         * montrerait rien de neuf.
         * ⚠️ CE COMMENTAIRE AFFIRMAIT UN INVARIANT FAUX jusqu'au 2026-08-18 : il
         *    disait que `pos` « vaut deux secondes de suite la même chose au
         *    sommet et au creux de la rampe ». À période 20 (donc `demi` = 10),
         *    `pos` suit 0,1,…,9,10,9,…,1 puis reboucle sur 0 — deux valeurs
         *    consécutives ne sont JAMAIS égales. Ce garde rattrape en fait un
         *    second tick LVGL dans la MÊME seconde. Utile, mais pour une autre
         *    raison. « Un commentaire qui affirme un invariant que le code ne
         *    tient pas est pire que pas de commentaire. »
         * 🔴 dn3-2, CORRIGÉ EN REVUE (2026-08-18) : ce paragraphe annonçait
         *    « RAM : 60 % sur 34 pas ⇒ des paliers » et concluait que le garde
         *    rendait « les quatre mocks NON synchrones même à tick commun ».
         *    LES DEUX SONT FAUX. `demi` vaut 17 pour RAM, donc le pas est
         *    60/17 ≈ 3,5 unités : aucun palier. Idem pour les trois autres
         *    (GPU ≈ 2,6 · RÉSEAU 140 · VENT 80). Le garde NE SE DÉCLENCHE
         *    JAMAIS sur les rampes actuelles, et les quatre mocks battent bien
         *    à l'unisson chaque seconde. Il ne rattrape donc toujours que le
         *    cas d'un second tick LVGL dans la MÊME seconde — utile, mais pour
         *    la raison d'origine.
         */
        if (s_wetat[i].regime == DN_VAL_SIMULEE &&
            strcmp(s_wetat[i].txt[0], txt) == 0) {
            continue;
        }

        /* La ligne secondaire DIT ce qu'est la valeur, en toutes lettres et sans
         * qu'il faille lire le code — c'est l'exigence d'AC3. Le badge
         * « SIMULÉ » et la couleur ambre le disent déjà à l'œil ; ceci le dit AU
         * MOT, pour que le régime ne dépende pas d'une convention de couleur que
         * dn3-3 pourrait réattribuer. */
        char sec[DN_WIDGET_SEC_MAX];
        switch (k_mock[i].sec) {
        case DN_SEC_RAM_GO: {
            /* 🔴 LA SECONDAIRE EST CALCULÉE DEPUIS LE POURCENTAGE, PAS TIRÉE
             *    D'UN SECOND GÉNÉRATEUR. « 38 % » à côté de « 12,1 / 32 Go »
             *    doivent se répondre : deux mocks indépendants afficheraient
             *    deux vérités contradictoires dans le même rectangle, ce qui est
             *    précisément le mensonge d'interface qu'on traque.
             *    32 Go x v% en DIXIÈMES de Go : v * 320 / 100.
             *    Contrôle : v = 38 -> 121 -> « 12,1 / 32 Go », soit exactement
             *    l'exemple verbatim de l'addendum §1. */
            int32_t dx = v * 320 / 100;
            snprintf(sec, sizeof(sec), "%d,%d / 32 Go", (int)(dx / 10),
                     (int)(dx % 10));
            break;
        }
        case DN_SEC_RESEAU_DUPLEX:
            /* ⚠️ `LV_SYMBOL_DOWN`/`UP` (U+F078/U+F077), PAS les flèches Unicode
             *    U+2193/U+2191 : celles-ci sont HORS latin-1 et le glyphe absent
             *    serait dessiné EN SILENCE. Les deux codepoints FontAwesome ont
             *    été VÉRIFIÉS présents dans `fonts/dn_font_14.c`. */
            /* ⚠️ /20,5 et non /20 : l'addendum §1 écrit « ↓ 985 ↑ 48 », et
             *    985/20 donne 49. Le verbatim de la maquette fait foi — le
             *    diviseur est choisi POUR le reproduire au pic du mock
             *    (985 * 2 / 41 = 48). Relevé en revue le 2026-08-18. */
            snprintf(sec, sizeof(sec), LV_SYMBOL_DOWN " %d  " LV_SYMBOL_UP " %d",
                     (int)v, (int)(v * 2 / 41));
            break;
        case DN_SEC_SIMULE:
        default:
            snprintf(sec, sizeof(sec), "valeur SIMULÉE — aucun capteur");
            break;
        }
        {
            dn_valeurs_t val = {.txt = {txt}, .n = 1};
            case_poser(i, DN_VAL_SIMULEE, &val, v, sec, NULL);
        }
    }
}

/*
 * ── L'INJECTEUR DE POUSSÉE (AC8) — POURQUOI IL EXISTE ────────────────────────
 *
 * AC8 demande d'isoler TROIS coûts dans le MÊME firmware : une case-widget
 * mono-grandeur, une case-widget bi-grandeurs, et une CASE NUE VIVANTE. Or une
 * case rendue nue n'a plus AUCUNE source — le témoin négatif d'AC8 serait donc
 * indémontrable, et les deux widgets seraient confondus par leurs cadences
 * différentes (mock 1 Hz, capteur 5 s).
 * ⚠️ dn3-2 : il n'y a plus de « trois cases nues » permanentes. Les six portent
 *    le modèle ; c'est `widget nue <idx> on` qui en rend une nue À CHAUD, le
 *    temps du relevé.
 *
 * Cette fonction pose UNE mise à jour synthétique sur UNE case, à la demande.
 * L'agent en enchaîne N depuis le PC, ce qui donne N cycles de redessin
 * attribuables à UNE SEULE case.
 *
 * ⛔ UNE POUSSÉE PAR APPEL, ET C'EST STRUCTUREL — PAS UNE PARESSE. Une boucle
 *    de N poussées DANS la commande serait une non-mesure : les N invalidations
 *    tomberaient dans le MÊME cycle LVGL (33 ms) et LVGL les fusionnerait en un
 *    seul redessin. On mesurerait 1 flush pour N mises à jour et on conclurait
 *    que grouper est gratuit. Séparer les poussées dans le TEMPS est la seule
 *    façon que chacune ait son cycle.
 * ⛔ Et aucun sommeil : le REPL EST le transport PC (dn2-2).
 *
 * 🔴 LE RÉGIME POSÉ EST `SIMULEE`, JAMAIS `REELLE`. Un injecteur de mesure qui
 *    poserait des valeurs d'apparence réelle serait le mensonge d'interface
 *    qu'AC3 interdit, introduit par l'instrument censé le vérifier.
 */
/* Le CORPS de la poussée. ⚠️ VERROU DÉJÀ PRIS — extrait en dn3-2 pour que la
 * rafale d'AC8 puisse en enchaîner N sous UN SEUL verrou sans dupliquer la
 * fabrication des valeurs. Deux fabricants pour un même instrument, c'est deux
 * façons de mesurer, donc deux résultats. */
static uint32_t s_pousse_seq;

static bool pousser_nolock(int idx)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES) {
        return false;
    }
    s_pousse_seq++;
    char t0[DN_WIDGET_TXT_MAX];
    char t1[DN_WIDGET_TXT_MAX];
    /* Une valeur qui CHANGE à chaque poussée : `lv_label_set_text` avec un texte
     * identique invalide quand même, mais une série de textes identiques rendrait
     * la mesure indiscernable d'un affichage figé pour qui la relit. */
    snprintf(t0, sizeof(t0), "%u,%u", (unsigned)(s_pousse_seq % 100),
             (unsigned)(s_pousse_seq % 10));
    snprintf(t1, sizeof(t1), "%u,%u", (unsigned)((s_pousse_seq * 7) % 100),
             (unsigned)((s_pousse_seq * 3) % 10));
    /* 🔴 BRUT MIS À L'ÉCHELLE DE LA CASE — correctif de revue (2026-08-18).
     *    La valeur était figée à 800..1599 pour TOUTE case, quelle que soit la
     *    plage annoncée de sa jauge. RAM, jauge NEUVE de dn3-2, borne à
     *    `ind_max = 100` : `lv_bar_set_value` clampait ⇒ la jauge se clouait au
     *    plein dès la 1re poussée et ne bougeait plus des 24 suivantes. Elle ne
     *    salissait donc AUCUN pixel pendant la campagne, et le px/mise-à-jour
     *    publié pour RAM en est systématiquement bas. VENTILOS (ind_max = 2000)
     *    n'était pas touchée — d'où l'absence du défaut en dn3-1, où RAM était
     *    encore une case nue. ⚠️ §16.4 est à re-relever pour la ligne RAM. */
    const dn_widget_desc_t *d_pou = &k_desc[idx];
    int32_t plage = d_pou->ind_max - d_pou->ind_min;
    int32_t brut = (plage > 0)
                       ? (int32_t)(d_pou->ind_min + (s_pousse_seq * 37) % (uint32_t)(plage + 1))
                       : (int32_t)(DN_MOCK_MIN +
                                   (s_pousse_seq * 37) % (DN_MOCK_MAX - DN_MOCK_MIN));
    dn_valeurs_t val = {.txt = {t0, t1}, .n = 2};
    case_poser(idx, DN_VAL_SIMULEE, &val, brut, "POUSSÉE de mesure (AC8)",
               NULL);
    /* 🔴 DÉCISION D1 (revue 2026-08-18) : marquer la case comme POUSSÉE, pour
     *    que le tick du mock cesse de la reprendre. Voir `mock_tick_nolock`.
     * ⚠️ dn3-2 : plus de `if (idx == VENTILOS)`. Le drapeau est posé pour
     *    TOUTE case — quatre cases portent un mock désormais, et la garder
     *    scopée à une seule aurait reproduit le défaut sur les trois autres.
     *    C'est exactement la forme du piège « gate scopée à UNE fonction ». */
    s_poussee[idx] = true;
    return true;
}

uint32_t dn_ui_pousser(int idx)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES) {
        return 0;
    }
    if (!lvgl_port_lock(1000)) {
        return 0;
    }
    bool ok = pousser_nolock(idx);
    uint32_t seq = s_pousse_seq;
    lvgl_port_unlock();
    return ok ? seq : 0;
}

/*
 * ── LA RAFALE (AC8) — LE CAS « TOUTES DANS LE MÊME CYCLE », PROVOQUÉ ─────────
 *
 * 🔴 POURQUOI ELLE EXISTE, ET POURQUOI ELLE CONTREDIT DÉLIBÉRÉMENT
 *    `dn_ui_pousser`. L'en-tête de `dn_ui_pousser` interdit N poussées dans un
 *    même appel, parce qu'elles tomberaient dans le MÊME cycle LVGL et seraient
 *    fusionnées : on mesurerait 1 flush pour N mises à jour et on conclurait à
 *    tort que grouper est gratuit.
 *
 *    Or l'extrapolation d'AC8 porte précisément sur le cas « six widgets qui se
 *    mettent à jour dans le MÊME cycle » (6 x 35 100 = 210 600 px, 69 % d'un
 *    plein écran). Et ce cas NE SE PRODUIT PAS naturellement : les six sources
 *    ne sont pas synchronisées (liaison ~1 s, capteur 5 s, mocks 14/20/26/34 s,
 *    barre à la minute). L'instrument existant l'INTERDIT PAR CONCEPTION, et le
 *    seul appelant est le REPL, qui attend l'invite entre deux commandes.
 *
 * ⇒ Cette fonction est l'exception NOMMÉE : elle pose les N cases sous UN SEUL
 *   verrou, donc dans UN SEUL cycle LVGL. Ce n'est pas un comportement produit,
 *   c'est un INSTRUMENT — au même titre que le mock, et il se déclare comme tel
 *   quand on publie son chiffre.
 * 🔴 CETTE FONCTION N'A PLUS DE TÉMOIN DE FUSION, ET C'EST UNE DÉCISION OWNER
 *    (2026-08-19). L'instrument en était à son TROISIÈME état successif — « cycles
 *    intercalés » (dn3-2), puis « valeur de succès 0 » (revue dn3-2), puis
 *    « valeur de succès 1 » (séance dn4-1) — et il n'a JAMAIS pu voir ce qu'il
 *    annonçait exclure : la boucle d'attente sortait au PREMIER incrément de
 *    `s_n_cycles`, donc le delta valait 1 quoi qu'il se soit passé. Obtenir 2
 *    aurait demandé deux cycles complets dans un seul `vTaskDelay(5 ms)`,
 *    impossible à 26,7 ms/cycle. Les « quatre rejeux, quatre fois 1 » de la séance
 *    sont la signature d'un témoin CONSTANT, pas d'une validation.
 * ⇒ LA FUSION SE PROUVE PAR `flush`, ET PAR LUI SEUL : « 6 flushes / 1 cycle /
 *   210 600 px » dans la même passe. C'est une mesure indépendante de cette
 *   fonction, et c'est elle qui porte le chiffre d'AC7 régime (c).
 * ⛔ NE PAS RÉINTRODUIRE UN TÉMOIN ICI sans démontrer d'abord, par une mesure,
 *   qu'il PEUT rendre autre chose que sa valeur de succès. Trois tours suffisent.
 * ✅ Effet de bord voulu : cette fonction NE DORT PLUS. Le docblock de `cmd_widget`
 *   affirme « Aucune ne DORT » — il redevient vrai (l'attente de 500 ms bloquait
 *   le REPL, donc le transport PC, plus longtemps que les cinq « RECONSTRUIT »).
 */
uint32_t dn_ui_rafale(void)
{
    if (!lvgl_port_lock(1000)) {
        return 0;
    }
    uint32_t n = 0;
    for (int i = 0; i < DN_UI_METRIQUES; i++) {
        if (pousser_nolock(i)) {
            n++;
        }
    }
    s_rafale_n = n;
    lvgl_port_unlock();
    return n;
}

uint32_t dn_ui_rafale_n(void) { return s_rafale_n; }

esp_err_t dn_ui_mock_set(bool on)
{
    /* 🔴 RENDAIT `void` — l'échec de verrou était AVALÉ (revue 2026-08-18), et
     *    la console annonçait « mock ARME » inconditionnellement, donc sur un
     *    `s_mock_on` inchangé. Les trois autres sous-commandes à verrou
     *    (`demo`, `opa`, `voile`) rendaient déjà un `esp_err_t` : celle-ci était
     *    la seule qui ne POUVAIT PAS dire qu'elle n'avait rien fait. */
    if (!lvgl_port_lock(1000)) {
        return ESP_ERR_TIMEOUT;
    }
    s_mock_on = on;
    mock_tick_nolock();
    lvgl_port_unlock();
    return ESP_OK;
}

bool dn_ui_mock_on(void) { return s_mock_on; }

bool dn_ui_mock_forme(int idx, int *min, int *max, int *periode_s)
{
    /* RELU de la table qui pilote réellement le mock — la console ne récite
     * rien. « Une étiquette qui ment est un défaut à part entière ».
     * ⚠️ dn3-2 : la signature prend un INDEX. Elle rendait `void` et ne
     *    décrivait QUE VENTILOS ; avec quatre mocks de formes différentes, une
     *    console qui aurait continué à imprimer la seule rampe 800-1600 aurait
     *    décrit trois cases par les chiffres d'une quatrième. */
    if (idx < 0 || idx >= DN_UI_METRIQUES || !k_mock[idx].actif) {
        return false;
    }
    if (min) {
        *min = k_mock[idx].min;
    }
    if (max) {
        *max = k_mock[idx].max;
    }
    if (periode_s) {
        *periode_s = (int)k_mock[idx].periode_s;
    }
    return true;
}

/*
 * ── W11 — RENDRE UNE CASE NUE À CHAUD, ET LA LUI RENDRE ─────────────────────
 * Le témoin négatif d'AC8. Voir `case_est_widget()` pour le motif complet.
 * ⚠️ Il FAUT reconstruire : la forme d'une case est décidée à la CONSTRUCTION
 *    (`build_dashboard`), pas à la mise à jour. Changer le seul drapeau
 *    laisserait un widget dessiné mis à jour par le chemin « nue ».
 * ⚠️ Et c'est cher : `build_scene()` coûte 307-322 ms verrou tenu, plus qu'une
 *    transition. C'est assumé pour un INSTRUMENT qu'on actionne entre deux
 *    relevés — ⛔ mais ça reste la raison pour laquelle aucune commande de
 *    régime courant ne doit déclencher `build_scene()`.
 */
esp_err_t dn_ui_nue_set(int idx, bool nue)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!k_widget[idx]) {
        /* Elle n'a jamais eu le modèle : la rendre « nue » n'a pas de sens, et
         * acquitter donnerait à croire qu'on a fait quelque chose.
         * ⚠️ BRANCHE MORTE DEPUIS dn3-2 (relevé en revue le 2026-08-18) : les
         *    SIX entrées de `k_widget[]` sont vraies. Elle est conservée parce
         *    qu'elle redeviendrait vivante si une 7e case arrivait sans modèle
         *    — mais aucun message console ne doit la présenter comme un cas
         *    qu'un opérateur peut rencontrer aujourd'hui. */
        return ESP_ERR_INVALID_STATE;
    }
    if (s_nue_force[idx] == nue) {
        return ESP_OK;
    }
    if (!lvgl_port_lock(2000)) {
        return ESP_ERR_TIMEOUT;
    }
    s_nue_force[idx] = nue;
    build_scene();
    lvgl_port_unlock();
    ESP_LOGW(TAG, "case %d (%s) : forme %s — TÉMOIN d'AC8, pas un réglage produit",
             idx, k_nom[idx], nue ? "NUE" : "WIDGET");
    return ESP_OK;
}

bool dn_ui_nue(int idx)
{
    return (idx >= 0 && idx < DN_UI_METRIQUES) ? s_nue_force[idx] : false;
}

/*
 * ── `widget oublier <idx>` — RENDRE UNE CASE À SON RÉGIME NATUREL ───────────
 *
 * 🔴 ENTRÉE DE LEDGER `deferred-work.md:1019-1023`, DEVENUE ACTIVE EN dn3-2 :
 *    « une case NUE n'a aucune source, donc elle reste SIMULÉE jusqu'au reboot
 *    […] SI dn3-2 EN FAIT UN USAGE COURANT, ajouter un `widget oublier <idx>`
 *    qui rend la case à son régime naturel serait moins piégeux que "rebooter
 *    avant tout constat owner". »
 *    LA CONDITION EST DÉCLENCHÉE : AC8 fait de `widget pousser` l'instrument
 *    central (25 poussées par relevé, table à 4 lignes) et ajoute la rafale.
 *    ⇒ Sans cette commande, tout constat owner d'AC11 lancé après une campagne
 *      verrait des badges « SIMULÉ » RÉSIDUELS et pourrait les lire comme une
 *      régression — un faux positif fabriqué par l'instrument.
 *
 * « Régime naturel » = celui que la SOURCE de la case impose, relu d'elle :
 *   · une case à mock  -> le mock la reprendra au prochain tick ;
 *   · une case réelle  -> ABSENTE, et sa source la repeindra quand elle parlera ;
 *   · une case sans source -> ABSENTE, définitivement, et c'est la vérité.
 */
esp_err_t dn_ui_oublier(int idx)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!lvgl_port_lock(1000)) {
        return ESP_ERR_TIMEOUT;
    }
    s_poussee[idx] = false;
    /* ABSENTE, pas « la dernière valeur connue » : on vient d'effacer la seule
     * source qu'avait cette case. Prétendre autre chose serait inventer. */
    case_poser(idx, DN_VAL_ABSENTE, NULL, 0, NULL, NULL);
    /* Le mock reprend AU PROCHAIN TICK s'il est armé — on ne l'appelle pas ici :
     * ce serait un second redessin dans le même verrou, donc un chiffre de plus
     * dans une campagne qui compte les cycles. */
    lvgl_port_unlock();
    return ESP_OK;
}

dn_val_regime_t dn_ui_regime(int idx)
{
    return (idx >= 0 && idx < DN_UI_METRIQUES) ? s_wetat[idx].regime
                                               : DN_VAL_ABSENTE;
}

const char *dn_ui_valeur_txt(int idx, int grandeur)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES || grandeur < 0 ||
        grandeur >= DN_WIDGET_GRANDEURS_MAX) {
        return "";
    }
    return s_wetat[idx].txt[grandeur];
}

/* ── AC9 : les deux opacités ──────────────────────────────────────────────────
 * Elles ne s'appliquent qu'aux objets CRÉÉS ensuite : LVGL a déjà résolu le
 * style des objets existants. On reconstruit donc la scène, et la console le
 * DIT — un réglage qui « ne fait rien » sans l'annoncer est la classe de défaut
 * que `dma` (inerte dans ce build) a values au dépôt. */
esp_err_t dn_ui_set_voile_opa(uint8_t opa)
{
    if (!lvgl_port_lock(2000)) {
        return ESP_ERR_TIMEOUT;
    }
    s_voile_opa = opa;
    build_scene();
    lvgl_port_unlock();
    return ESP_OK;
}

uint8_t dn_ui_voile_opa(void) { return s_voile_opa; }

/*
 * ── LA TROISIÈME TABLE CACHÉE, GÉNÉRALISÉE (dn4-1 / AC6) ────────────────────
 *
 * 🔴 `dn_ui_set_icone_vent()` écrivait `s_icone_alt[DN_UI_CASE_VENT]` EN DUR.
 *    L'A/B d'icône visait donc l'ancienne case ventilateur — et aurait continué
 *    de la viser après le renommage, en silence : `widget icone 2` aurait
 *    annoncé un changement en le posant au bon endroit par pur hasard d'index.
 *    Le mécanisme est générique DEPUIS SA NAISSANCE (« indexé par case, sans
 *    nommer de métrique », dn3-1) — seul son point d'entrée ne l'était pas.
 * ⇒ La CASE devient un paramètre. Ajouter une métrique ne touche plus rien ici.
 */
int dn_ui_icones_alt_n(void) { return (int)DN_UI_ICONES_ALT; }

const char *dn_ui_icone_alt_nom(int n)
{
    return (n >= 0 && n < (int)DN_UI_ICONES_ALT) ? k_icones_alt[n].nom : "?";
}

int dn_ui_icone_alt(int idx)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES) {
        return -1;
    }
    for (int i = 0; i < (int)DN_UI_ICONES_ALT; i++) {
        /* RELU du pointeur réellement posé, pas d'un index mémorisé à part : un
         * index et un glyphe qui divergent, c'est l'étiquette qui ment. */
        const char *actif = s_icone_alt[idx] ? s_icone_alt[idx]
                                             : k_desc[idx].icone;
        if (actif == k_icones_alt[i].glyphe) {
            return i;
        }
    }
    return -1;
}

esp_err_t dn_ui_set_icone_alt(int idx, int n)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES || n < 0 || n >= (int)DN_UI_ICONES_ALT) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!lvgl_port_lock(2000)) {
        return ESP_ERR_TIMEOUT;
    }
    s_icone_alt[idx] = k_icones_alt[n].glyphe;
    build_scene();
    lvgl_port_unlock();
    return ESP_OK;
}

/* La piste de la jauge — même contrat que `dn_ui_set_case_opa` : le style est
 * résolu à la CRÉATION des objets, donc on reconstruit la scène, et la console
 * le DIT. Un réglage qui « ne fait rien » sans l'annoncer est la classe de
 * défaut que `dma` (inerte dans ce build) a coûtée au dépôt. */
esp_err_t dn_ui_set_piste(uint32_t rgb)
{
    if (!lvgl_port_lock(2000)) {
        return ESP_ERR_TIMEOUT;
    }
    dn_widget_set_piste(rgb);
    build_scene();
    lvgl_port_unlock();
    return ESP_OK;
}

esp_err_t dn_ui_set_case_opa(uint8_t opa)
{
    if (!lvgl_port_lock(2000)) {
        return ESP_ERR_TIMEOUT;
    }
    dn_widget_set_opa(opa);
    build_scene();
    lvgl_port_unlock();
    return ESP_OK;
}

/* Le groupage passe par ici — et PAS par un appel nu à `dn_widget_set_groupage()`
 * depuis le REPL, comme c'était le cas jusqu'au 2026-08-18 (revue de code).
 * `dn_widget.h` écrit que ses fonctions EXIGENT le verrou déjà pris, et que les
 * seuls appelants légitimes sont les publiques de `dn_ui` et les callbacks de
 * timer LVGL. ⚠️ Aucun effet mesurable manquant — `grouper` est latché en local
 * dans `dn_widget_maj` — mais un contrat qui souffre une exception silencieuse
 * n'en est plus un, et c'est la seule qui restait.
 * ⛔ PAS de `build_scene()` ici : changer de branche d'A/B ne redessine rien, et
 *    reconstruire fausserait le relevé qui suit. */
esp_err_t dn_ui_set_groupage(bool on)
{
    if (!lvgl_port_lock(1000)) {
        return ESP_ERR_TIMEOUT;
    }
    dn_widget_set_groupage(on);
    lvgl_port_unlock();
    return ESP_OK;
}

/* La géométrie d'une case, pour que la console cesse de réciter « 225x156 =
 * 35 100 px » alors que dn3-2 la refait (§15.2). */
void dn_ui_case_dim(int *w, int *h)
{
    if (w) {
        *w = DN_UI_CASE_W;
    }
    if (h) {
        *h = ui_case_h(); /* ⚠️ CALCULÉ de l'override, ⛔ plus une macro figée */
    }
}

/*
 * ── dn4-6 / AC4 + AC11 : LES DEUX BANDES, RÉGLABLES ET RELUES ────────────────
 * ⚠️ RECONSTRUIT LA SCÈNE — `case_h` change, donc toutes les cases. L'appelant
 *    (la console) DOIT l'annoncer AVANT : `build_scene()` bloque le REPL ~350 ms,
 *    et sur la branche A le REPL EST le transport PC.
 */
static void build_scene(void);

esp_err_t dn_ui_set_bandes(int barre_h, int menu_h)
{
    /* Bornes : la barre doit contenir l'heure (`dn_font_28` à y = 18, boîte
     * 18..53) et la date (`dn_font_14` à y = 28, boîte 28..46) ⇒ 53 est le
     * plancher RELU du code, ⛔ pas un chiffre rond. Le MENU porte
     * `dn_font_28` à y = 14 ⇒ boîte 14..49, plancher 49 — ou ZÉRO, qui est la
     * voie (a) et signifie « pas de bandeau du tout ». */
    esp_err_t eb = dn_ui_bandes_valider(barre_h, menu_h);
    if (eb != ESP_OK) {
        return eb;
    }
    if (!lvgl_port_lock(2000)) {
        return ESP_ERR_TIMEOUT; /* ⛔ RIEN n'a bougé — ne pas annoncer la bascule */
    }
    s_geo_barre_h = barre_h;
    s_geo_menu_h = menu_h;
    build_scene();
    lvgl_port_unlock();
    return ESP_OK;
}

/*
 * ── dn4-6 : LA VOIE S'APPLIQUE EN **UN SEUL** GESTE, ET C'EST UN CORRECTIF ───
 *
 * 🔴 `widget voie` enchaînait `dn_ui_set_bandes()` PUIS `dn_ui_set_widget_geom()`,
 *    donc DEUX reconstructions — et la PREMIÈRE dessinait la NOUVELLE hauteur de
 *    case avec l'ANCIENNE géométrie interne. Elle produisait donc de vrais
 *    débordements, comptés et journalisés, POUR UNE COMBINAISON QUE PERSONNE NE
 *    DEMANDE. La voie (a) ressortait à « 1 débordement » alors qu'elle tient
 *    (179 ≤ 180) : l'instrument accusait la voie du défaut de son propre chemin
 *    d'application.
 * ⛔ C'est la classe de défaut que ce dépôt traque : un compteur qui compte
 *    autre chose que ce que son nom dit. Et il aurait fait écarter une voie à
 *    l'arbitrage.
 * ⇒ UN verrou, UN `build_scene()`, donc UN état mesuré. ⚠️ Effet de bord voulu :
 *   la commande ne bloque plus le REPL ~700 ms mais ~350 ms.
 */
esp_err_t dn_ui_set_case_grandeurs(int idx, int n)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES || n < 0 ||
        n > DN_WIDGET_GRANDEURS_MAX) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!lvgl_port_lock(2000)) {
        return ESP_ERR_TIMEOUT; /* ⛔ RIEN n'a bougé */
    }
    s_gr_force[idx] = (uint8_t)n; /* 0 = rendre la case a son descripteur */
    dn_widget_chevauchements_reset();
    dn_widget_debordements_reset();
    build_scene();
    lvgl_port_unlock();
    return ESP_OK;
}

esp_err_t dn_ui_set_voie(int barre_h, int menu_h, const dn_widget_geom_t *g)
{
    if (!g) {
        return ESP_ERR_INVALID_ARG;
    }
    esp_err_t e = dn_ui_bandes_valider(barre_h, menu_h);
    if (e != ESP_OK) {
        return e;
    }
    e = dn_ui_geom_valider(g);
    if (e != ESP_OK) {
        return e;
    }
    if (!lvgl_port_lock(2000)) {
        return ESP_ERR_TIMEOUT; /* ⛔ RIEN n'a bougé */
    }
    s_geo_barre_h = barre_h;
    s_geo_menu_h = menu_h;
    dn_widget_set_geom(g);
    /* Les compteurs sont remis à zéro SOUS LE VERROU, juste avant l'unique
     * reconstruction : ce qui sera compté est donc EXACTEMENT ce que la voie
     * retenue produit, ⛔ jamais un résidu de l'état précédent. */
    dn_widget_chevauchements_reset();
    dn_widget_debordements_reset();
    build_scene();
    lvgl_port_unlock();
    return ESP_OK;
}

/* Les deux validations, EXTRAITES pour que `dn_ui_set_voie` puisse refuser
 * AVANT de prendre le verrou — ⛔ et surtout avant d'avoir bougé la moitié des
 * réglages, ce qui laisserait la scène dans un état que personne n'a demandé. */
esp_err_t dn_ui_bandes_valider(int barre_h, int menu_h)
{
    if (barre_h < 53 || barre_h > 120) {
        return ESP_ERR_INVALID_ARG;
    }
    if (menu_h != 0 && (menu_h < 49 || menu_h > 120)) {
        return ESP_ERR_INVALID_ARG;
    }
    return ESP_OK;
}

esp_err_t dn_ui_geom_valider(const dn_widget_geom_t *g)
{
    if (!g) {
        return ESP_ERR_INVALID_ARG;
    }
    if (g->val_y < 14 || g->val_y > 200 || g->val_pas < 18 || g->val_pas > 80) {
        return ESP_ERR_INVALID_ARG;
    }
    if (g->dispo < 0 || g->dispo >= DN_DISPO_COUNT) {
        return ESP_ERR_INVALID_ARG;
    }
    if (g->entete < 0 || g->entete >= DN_ENTETE_COUNT) {
        return ESP_ERR_INVALID_ARG;
    }
    return ESP_OK;
}

esp_err_t dn_ui_set_widget_geom(const dn_widget_geom_t *g)
{
    if (!g) {
        return ESP_ERR_INVALID_ARG;
    }
    /* Bornes RELUES de ce que la case peut porter, ⛔ pas des chiffres ronds :
     * `val_y` sous le bas de l'en-tête NORMAL (43) est LÉGAL mais doit avoir
     * été constaté à l'œil (AC3) — on ne l'interdit donc pas, on ne descend
     * simplement pas sous le haut de la boîte du badge (14). */
    esp_err_t ev = dn_ui_geom_valider(g);
    if (ev != ESP_OK) {
        return ev;
    }
    if (!lvgl_port_lock(2000)) {
        return ESP_ERR_TIMEOUT;
    }
    dn_widget_set_geom(g);
    build_scene();
    lvgl_port_unlock();
    return ESP_OK;
}

/* Les DÉFAUTS, relus des macros — ⛔ jamais récités par l'appelant. C'est le
 * même motif que `dn_widget_geom_defaut()` : un défaut recopié ailleurs cesse
 * d'être le défaut au premier changement, et personne ne le voit. */
void dn_ui_geom_bandes_defaut(int *barre_h, int *menu_h)
{
    if (barre_h) {
        *barre_h = DN_UI_BARRE_H_DEFAUT;
    }
    if (menu_h) {
        *menu_h = DN_UI_MENU_H_DEFAUT;
    }
}

void dn_ui_geom_bandes(int *barre_h, int *menu_h, int *grille_h, int *case_h)
{
    if (barre_h) {
        *barre_h = ui_barre_h();
    }
    if (menu_h) {
        *menu_h = ui_menu_h();
    }
    if (grille_h) {
        *grille_h = ui_grille_h();
    }
    if (case_h) {
        *case_h = ui_case_h();
    }
}

/*
 * ── AC1 : LA PREUVE D'UNICITÉ, ET ELLE EST FALSIFIABLE ───────────────────────
 *
 * Une 7e métrique FICTIVE, produite par le MÊME `dn_widget_creer` que les trois
 * autres, à partir d'un descripteur et de rien d'autre. AUCUNE ligne de code de
 * dessin n'a été ajoutée pour elle — c'est tout l'enjeu : le brief promet
 * qu'« ajouter une métrique future (SSD, ventilateurs, puissance, NAS, Bambu…)
 * ne redessine pas l'UI », et cette commande transforme la promesse en
 * expérience qu'on peut rater.
 *
 * ⚠️ Elle se pose PAR-DESSUS le dashboard, au centre, et recouvre des cases.
 *    C'est assumé : c'est un INSTRUMENT, comme `ui label on` l'est depuis dn1-4,
 *    pas un élément de produit. `widget demo off` la retire.
 * ⚠️ Le descripteur est BI-GRANDEURS et porte un indicateur : il exerce donc en
 *    une fois les deux mécanismes qu'AC2 demande de prouver GÉNÉRIQUES, sur une
 *    métrique qui n'est ni Ambiance ni Ventilos. Une variante multi-grandeurs
 *    qui ne marcherait que pour « Ambiance » serait un cas spécial déguisé.
 */
/*
 * ── LA 7ᵉ MÉTRIQUE FICTIVE — ET dn4-1 LUI DONNE UN SECOND RÔLE ───────────────
 *
 * Elle prouvait déjà « ajouter une métrique = une ligne de descripteur ».
 * 🔴 dn4-1 EN FAIT AUSSI LE TÉMOIN D'AC5, et c'est un ajout NÉCESSAIRE : après
 *    le correctif W5, AUCUNE des six cases réelles ne combine deux grandeurs ET
 *    une jauge (CPU et GPU n'en demandent pas, RAM est à n = 1). Le correctif
 *    serait donc VRAI et JAMAIS EXERCÉ — c'est-à-dire invérifiable autrement
 *    qu'en relisant le source, exactement la situation dans laquelle le défaut a
 *    dormi depuis la revue dn3-1.
 * ⇒ `.n_grandeurs = 2` ET `.indicateur = true`. `widget demo on` construit donc
 *   le cas EXACT que `if (desc->indicateur && n == 1)` faisait échouer en
 *   silence, et l'on VOIT la jauge. C'est le stimulus prouvé qu'exige la
 *   méthodo (« un test négatif ne vaut que si le stimulus est prouvé »).
 * ⚠️ ET IL MONTRE AUSSI LE PRIX : à n = 2 avec jauge, y_bas vaut 148 et
 *    148 + 20 = 168 > 156 ⇒ la ligne secondaire NE TIENT PAS. Elle est
 *    abandonnée — et JOURNALISÉE (ESP_LOGW dans `dn_widget_creer`). La démo
 *    fabrique donc aussi la preuve que l'abandon n'est plus silencieux.
 */
static const dn_widget_desc_t k_demo_desc = {
    .icone = DN_ICONE_NETWORK_WIRED,
    .titre = "DÉMO 2+JAUGE",
    .couleur = 0x35d6e8,
    .n_grandeurs = 2,
    .indicateur = true,
    .ind_min = 0,
    .ind_max = 100, /* % — et la plage COUVRE la source (piège d'instrument n°7 :
                     * une jauge bornée écrête EN SILENCE, et la jauge RAM avait
                     * été clouée au plein par un injecteur hors plage) */
    /* ⚠️ QUATRE GRANDEURS SONT DÉCLARÉES ICI POUR DEUX POSÉES PAR DÉFAUT, et ce
     * n'est pas du remplissage : `widget demo on <n>` fait varier `n` à chaud
     * (voir `s_demo_n`), et une grandeur sans unité ni précision rendrait le
     * témoin d'AC2 illisible au moment précis où on le regarde. */
    .grandeurs = {{.unite = "%", .prec = DN_PREC_DIXIEME},
                  {.unite = "Mo/s", .icone = DN_ICONE_DESKTOP,
                   .prec = DN_PREC_DIXIEME},
                  {.unite = "W", .prefixe = "d3", .prec = DN_PREC_ENTIER},
                  {.unite = "tr/min", .prefixe = "d4", .prec = DN_PREC_ENTIER}},
};

/*
 * ── dn4-6 / AC2 : LE NOMBRE DE GRANDEURS DE LA DÉMO EST RÉGLABLE À CHAUD ─────
 *
 * 🔴 SANS ÇA, LES DEUX PREUVES D'AC2 SONT INATTEIGNABLES. Aucune des six cases
 *    réelles ne peut déclencher les cas à prouver :
 *      · l'abandon de la JAUGE exige n ≥ 3 AVEC jauge — seule la démo a une
 *        jauge en plus d'une grandeur multiple ;
 *      · le CLAMP de dn4-1 exige un descripteur à n > `GRANDEURS_MAX`, soit 5
 *        sur un firmware à 4 — aucun descripteur figé ne le fera jamais.
 *    ⛔ « Un instrument qui ne peut pas voir le cas qu'il a été construit pour
 *      prouver est une gate décorative » — le dépôt l'a payé sur la colonne
 *      « secondaire » de la table `widget`, constante par construction.
 *
 * ⚠️ LE DÉFAUT RESTE 2, et c'est délibéré : `DEMO 2 OUI non` est le témoin de
 *    non-régression de dn4-1, cité tel quel dans la baseline T0. Le changer
 *    ferait échouer une comparaison avant/après pour une raison sans rapport.
 * ⚠️ La borne haute est 6, ⛔ pas `DN_WIDGET_GRANDEURS_MAX` : il FAUT pouvoir
 *    demander plus que le maximum, sinon le clamp devient injoignable.
 */
#define DN_UI_DEMO_N_MAX 6
static int s_demo_n = 2;

int dn_ui_demo_n(void) { return s_demo_n; }

esp_err_t dn_ui_set_demo_n(int n)
{
    if (n < 1 || n > DN_UI_DEMO_N_MAX) {
        return ESP_ERR_INVALID_ARG;
    }
    s_demo_n = n;
    return ESP_OK;
}

/* Le descripteur du widget de DÉMO — pour que la table de géométrie puisse
 * confronter ce qu'il DEMANDE (n = 2 + jauge) à ce qu'il a OBTENU. C'est le seul
 * descripteur du firmware à armer l'abandon de la secondaire (168 > 156).
 * ⚠️ DÉFINI ICI, après `k_demo_desc` : le placer près de `dn_ui_desc()` le
 *    référençait 3 500 lignes avant sa définition. */
const dn_widget_desc_t *dn_ui_demo_desc(void)
{
    /* 🔴 LE `n` RÉGLABLE DOIT SE VOIR DANS LA COLONNE « DEMANDÉ » DE `widget`.
     *    Rendre `&k_demo_desc` tel quel annoncerait « n=2 » pendant qu'une démo
     *    à n=5 est posée — la colonne dont l'en-tête promet de dire ce que LE
     *    DESCRIPTEUR demande mentirait sur le seul chemin qui prouve le clamp.
     *    C'est exactement le défaut relevé en revue le 2026-08-19, un cran plus
     *    loin. ⇒ copie statique, rafraîchie à chaque lecture. */
    static dn_widget_desc_t d;
    d = k_demo_desc;
    d.n_grandeurs = (uint8_t)s_demo_n;
    return &d;
}

esp_err_t dn_ui_demo_set(bool on)
{
    if (!lvgl_port_lock(1000)) {
        return ESP_ERR_TIMEOUT;
    }
    if (on) {
        if (!s_demo.racine) {
            /* Un état fabriqué, DÉCLARÉ SIMULÉ : la démo ne doit pas être le
             * seul endroit du firmware où un chiffre inventé se présente sans
             * badge. */
            static dn_widget_etat_t etat;
            etat.regime = DN_VAL_SIMULEE;
            snprintf(etat.txt[0], sizeof(etat.txt[0]), "62,0");
            snprintf(etat.txt[1], sizeof(etat.txt[1]), "48,0");
            /* ⚠️ DANS LA PLAGE DE LA JAUGE (0..100), et pas au-delà : une jauge
             * bornée écrête EN SILENCE, et un témoin cloué au plein ne prouve
             * pas que la jauge se remplit — il prouve qu'elle existe, ce qui
             * n'est pas la même chose. */
            etat.brut[0] = 62;
            /* Elle sera ABANDONNÉE (168 > 156) — c'est le second témoin : le
             * log doit apparaître, et `widget` doit afficher « secondaire non ». */
            snprintf(etat.secondaire, sizeof(etat.secondaire), "7e métrique FICTIVE");
            /* Copie locale pour appliquer le `n` réglable — MÊME PATRON que
             * l'override d'icône de `build_dashboard` : le descripteur `const`
             * ne bouge pas, l'override est local et explicite. */
            dn_widget_desc_t d = k_demo_desc;
            d.n_grandeurs = (uint8_t)s_demo_n;
            /* Des textes pour TOUTES les grandeurs demandées : une démo à n = 4
             * qui n'aurait que deux textes afficherait « -- » sur les deux
             * dernières, et on lirait le témoin de W10 là où on veut lire celui
             * de la géométrie. Deux instruments dans le même relevé. */
            snprintf(etat.txt[2], sizeof(etat.txt[2]), "212");
            snprintf(etat.txt[3], sizeof(etat.txt[3]), "604");
            dn_widget_creer(lv_screen_active(), 120, 240, DN_UI_CASE_W,
                            ui_case_h(), &d, &etat, NULL, NULL, &s_demo);
        }
    } else if (s_demo.racine) {
        lv_obj_delete(s_demo.racine);
        dn_widget_oublier(&s_demo);
    }
    s_demo_on = on;
    lvgl_port_unlock();
    return ESP_OK;
}

bool dn_ui_demo_on(void) { return s_demo_on && s_demo.racine != NULL; }

bool dn_ui_case_dessinee(int idx)
{
    /* Le pointeur RACINE, pas une supposition sur le modèle de navigation : en
     * REBUILD vue détail, le dashboard n'existe pas et la case n'est dessinée
     * nulle part. La console doit pouvoir le DIRE plutôt que de laisser croire
     * qu'un texte posé a atteint la dalle.
     * 🔴 ET `s_active` COMPTE AUSSI (revue du 2026-08-18) : c'est la leçon que
     *    `case_poser` a apprise 400 lignes plus haut le 2026-08-16, et qui
     *    n'avait pas été reportée ici. Quand LVGL est arrêté (`ui off`,
     *    `scene <mire>`, `tear`), le mutex reste LIBRE et les racines restent
     *    non-NULL : cette fonction annonçait donc « dessinee = oui » pour six
     *    cases dont RIEN n'atteignait la dalle — pendant que le texte imprimé
     *    par la commande explique que « NON » veut dire exactement ça. */
    return idx >= 0 && idx < DN_UI_METRIQUES && s_active &&
           s_wobj[idx].racine != NULL;
}

bool dn_ui_label_shown(void) { return s_label_shown; }

esp_err_t dn_ui_anim(bool on, int periode_ms)
{
    if (on) {
        if (periode_ms < DN_UI_ANIM_MS_MIN || periode_ms > DN_UI_ANIM_MS_MAX) {
            return ESP_ERR_INVALID_ARG;
        }
    }
    if (!lvgl_port_lock(1000)) {
        return ESP_ERR_TIMEOUT;
    }
    if (on) {
        if (!s_bar) {
            s_bar = lv_obj_create(lv_screen_active());
            lv_obj_remove_style_all(s_bar);
            lv_obj_set_size(s_bar, DN_UI_BAR_W, DN_LCD_V_RES);
            lv_obj_set_style_bg_color(s_bar, lv_color_hex(0xffffff), 0);
            lv_obj_set_style_bg_opa(s_bar, LV_OPA_COVER, 0);
            lv_obj_set_pos(s_bar, 0, 0);
        }
        lv_anim_t a;
        lv_anim_init(&a);
        lv_anim_set_var(&a, s_bar);
        lv_anim_set_exec_cb(&a, bar_set_x);
        lv_anim_set_values(&a, 0, DN_LCD_H_RES - DN_UI_BAR_W);
        lv_anim_set_duration(&a, (uint32_t)periode_ms);
        /* Aller-retour : un retour instantané au bord gauche produirait un saut
         * dont l'artefact ressemble à un déchirement. On ne veut pas fabriquer le
         * symptôme qu'on cherche à observer. */
        lv_anim_set_reverse_duration(&a, (uint32_t)periode_ms);
        lv_anim_set_repeat_count(&a, LV_ANIM_REPEAT_INFINITE);
        lv_anim_start(&a);
        s_anim_ms = periode_ms;
        s_anim_on = true;
    } else {
        if (s_bar) {
            lv_anim_delete(s_bar, bar_set_x);
            lv_obj_delete(s_bar);
            s_bar = NULL;
            /* La barre supprimée laisse une zone sale : sans invalidation
             * explicite, la dernière position resterait imprimée dans le
             * framebuffer, et on la prendrait pour un artefact de rémanence. */
            lv_obj_invalidate(lv_screen_active());
        }
        s_anim_on = false;
    }
    lvgl_port_unlock();
    return ESP_OK;
}

bool dn_ui_anim_running(void) { return s_anim_on; }

esp_err_t dn_ui_bg_psram(bool on)
{
    uint16_t *buf = NULL; /* portée fonction : le chemin d'échec du verrou le libère */
    if (on == (s_bg_psram != NULL)) {
        return ESP_OK;
    }
    if (on) {
        const uint16_t *src = dn_asset_pixels();
        if (!src) {
            ESP_LOGE(TAG, "pas d'asset à copier — la source reste inchangée");
            return ESP_ERR_NOT_FOUND;
        }
        buf = heap_caps_malloc(DN_FB_BYTES, MALLOC_CAP_SPIRAM);
        if (!buf) {
            ESP_LOGE(TAG, "PSRAM insuffisante pour %u o", (unsigned)DN_FB_BYTES);
            return ESP_ERR_NO_MEM;
        }
        int64_t t0 = esp_timer_get_time();
        memcpy(buf, src, DN_FB_BYTES);
        int64_t dt = esp_timer_get_time() - t0;
        ESP_LOGI(TAG, "fond copié flash -> PSRAM : %u o en %lld us (%.2f Mo/s)",
                 (unsigned)DN_FB_BYTES, (long long)dt,
                 dt > 0 ? (double)DN_FB_BYTES / (double)dt : 0.0);
        /* PAS de `s_bg_psram = buf` ici : la publication n'a lieu qu'après la
         * reconstruction réussie, sous verrou, plus bas. */
    } else {
        /*
         * ⚠️ ORDRE NON NÉGOCIABLE (correctif de revue — c'était un use-after-free) :
         * la scène est reconstruite AVANT la libération, et la libération n'a
         * lieu QUE si la reconstruction a eu lieu. La première version libérait
         * `old` même quand le verrou expirait : `build_scene()` n'avait pas
         * tourné, `s_bg_dsc.data` pointait toujours sur le bloc rendu, et la
         * tâche LVGL re-blittait de la PSRAM LIBÉRÉE à chaque invalidation —
         * en rendant ESP_OK par-dessus. Déclencheur réaliste : un plein écran
         * à `lines 8` tient le verrou ~2,1 s > le timeout de 1 s.
         */
        if (!lvgl_port_lock(1000)) {
            ESP_LOGE(TAG, "verrou LVGL non pris — la source du fond reste PSRAM, "
                          "rien n'est libéré. Réessayer.");
            return ESP_ERR_TIMEOUT;
        }
        uint16_t *old = s_bg_psram;
        s_bg_psram = NULL;
        build_scene();
        lvgl_port_unlock();
        heap_caps_free(old);
        return ESP_OK;
    }

    /* Même règle au chemin ALLER (revue) : `s_bg_psram` n'est publié qu'APRÈS
     * la reconstruction réussie. La première version l'assignait avant le
     * verrou : sur timeout, l'état disait « PSRAM » pendant que la scène
     * blittait la flash, et tout retry court-circuitait en no-op ESP_OK —
     * l'A/B de T3 coincé sous une étiquette fausse jusqu'au reboot. */
    if (!lvgl_port_lock(1000)) {
        ESP_LOGE(TAG, "verrou LVGL non pris — copie PSRAM libérée, la source "
                      "reste la flash. Réessayer.");
        heap_caps_free(buf);
        return ESP_ERR_TIMEOUT;
    }
    s_bg_psram = buf;
    build_scene();
    lvgl_port_unlock();
    return ESP_OK;
}

bool dn_ui_bg_is_psram(void) { return s_bg_psram != NULL; }

esp_err_t dn_ui_pause(void)
{
    /* Idempotent (revue) : un second `ui off` est un no-op, pas une panne.
     * Sans ce garde, lvgl_port_stop() sur un tick déjà arrêté rend
     * ESP_ERR_INVALID_STATE et la console imprime « refusé » pour rien —
     * l'opérateur part chercher une panne LVGL qui n'existe pas. */
    if (!s_active) {
        return ESP_OK;
    }
    esp_err_t err = lvgl_port_stop();
    if (err == ESP_OK) {
        s_active = false;
        /*
         * ⚠️ LE CHRONOMÈTRE DE LATENCE EST DÉSARMÉ (correctif de revue dn1-4).
         *    `nav open 3` puis `ui off` dans les ~300 ms qui suivent laissait un
         *    chrono en vol ; `dn_ui_resume()` fait un redessin complet dont le
         *    dernier flush appelait `dn_touch_latence_stop()` — la DURÉE DE LA
         *    PAUSE entrait alors dans le min/moy/max publié par AC5. Un
         *    échantillon gouverné par l'opérateur, dans la mesure même que
         *    `nav_bloque_par_pause` existe pour protéger.
         */
        dn_touch_latence_desarm();
        /*
         * ⚠️ DRAINER LE CYCLE EN VOL (correctif de revue). `lvgl_port_stop()` ne
         * fait que geler le tick : il ne joint pas la tâche, qui peut être AU
         * MILIEU de `lv_timer_handler()` — jusqu'à ~176 ms de flushes restants
         * en plein écran `vsync`. Rendre la main tout de suite laissait `scene`
         * écrire le framebuffer pendant que le dernier cycle le flushait encore
         * — la contamination exacte que la pause doit exclure, atteignable en
         * usage scripté (dn_console.py enchaîne les commandes).
         * La tâche du portage tient `lvgl_port_lock` pendant tout son cycle
         * (esp_lvgl_port.c, boucle de tâche) : prendre puis rendre le verrou
         * garantit que le cycle en vol est FINI. 2 000 ms couvrent le pire
         * plein écran à `lines 8` (~80 flushes x ~27 ms).
         */
        if (lvgl_port_lock(2000)) {
            lvgl_port_unlock();
        } else {
            ESP_LOGW(TAG, "pause : le cycle en vol n'a pas rendu la main en "
                          "2 s — un flush LVGL peut encore toucher le "
                          "framebuffer, attendre avant `scene`/`tear`.");
        }
    }
    return err;
}

esp_err_t dn_ui_resume(void)
{
    /* Idempotent (revue) — même raison que dn_ui_pause. Évite aussi le demi-état
     * du portage : lvgl_port_resume() fait lv_timer_enable(true) AVANT de
     * démarrer l'esp_timer, donc un échec le laissait à moitié appliqué. */
    if (s_active) {
        return ESP_OK;
    }
    /*
     * ── L'ÉTAT TACTILE EST VIDÉ *AVANT* DE REPRENDRE ─────────────────────────
     * Trois correctifs de la revue dn1-4, sur un drainage qui n'empêchait pas ce
     * qu'il annonçait :
     *
     * 1. ORDRE. Il était fait APRÈS `lvgl_port_resume()`, donc après que le
     *    timer et la tâche LVGL (priorité 4) sont réarmés : la tâche pouvait
     *    préempter le REPL et lire l'indev pendant que le drain faisait encore
     *    sa transaction I²C bloquante. La première lecture pouvait donc précéder
     *    le drainage. On draine d'abord, on reprend ensuite.
     * 2. VERROU. `esp_lcd_touch_read_data()` n'a aucun verrou interne et le
     *    drain tournait depuis la tâche REPL, concurremment à `dn_touch_read()`
     *    dans la tâche LVGL, sur un `s_appuye` volatile mais non atomique.
     * 3. CE QUI PRODUIT LE CLIC. Le clic ne naît pas de `s_appuye` mais de la
     *    machine d'état de l'INDEV LVGL (`pointer.act_obj` + transition
     *    PRESSED->RELEASED). Jeter une lecture ne la touchait pas : un doigt
     *    relâché pendant `ui off` laissait `act_obj` armé, et la première
     *    lecture après reprise rendait RELEASED — donc un CLICKED, donc
     *    l'ouverture d'un détail que personne n'a demandé, exactement ce que le
     *    commentaire promettait d'exclure. `dn_touch_drain()` fait désormais le
     *    `lv_indev_reset()` qui manquait.
     */
    dn_touch_drain(); /* prend le verrou lui-même — règle du dépôt */
    esp_err_t err = lvgl_port_resume();
    if (err == ESP_OK) {
        s_active = true;
        /* Le framebuffer a pu être réécrit pendant la pause (c'est même le seul
         * intérêt de la pause). On redessine tout, sinon LVGL croirait l'écran
         * conforme à son arbre d'objets et ne réparerait jamais. */
        dn_ui_force_full_redraw();
    }
    return err;
}

bool dn_ui_active(void) { return s_active; }

/*
 * Octets UTILISÉS du tas LVGL. C'est le SEUL instrument capable de voir une
 * fuite d'objets LVGL : le tas est un pool statique en .bss (LV_MEM_ADR=0), donc
 * aucun lv_obj_create ne passe par heap_caps_malloc et la RAM interne / la PSRAM
 * n'en disent RIEN. La « preuve de non-fuite » d'AC4 mesurait exactement ces
 * deux tas-là, et affichait « delta 0 o » avec ou sans fuite (revue dn1-4).
 * Rend 0 si le verrou n'a pas été pris — l'appelant doit le dire plutôt que de
 * publier un zéro qui ressemble à une bonne nouvelle.
 */
size_t dn_ui_lvgl_used(void)
{
    lv_mem_monitor_t mon;
    if (!lvgl_port_lock(1000)) {
        return 0;
    }
    lv_mem_monitor(&mon);
    lvgl_port_unlock();
    return (size_t)(mon.total_size - mon.free_size);
}

void dn_ui_log_mem(void)
{
    lv_mem_monitor_t mon;
    if (!lvgl_port_lock(1000)) {
        printf("verrou LVGL non pris\n");
        return;
    }
    lv_mem_monitor(&mon);
    lvgl_port_unlock();
    printf("tas LVGL (LV_MEM_SIZE_KILOBYTES = %d Ko, STATIQUE en .bss) :\n",
           CONFIG_LV_MEM_SIZE_KILOBYTES);
    printf("  total %" PRIu32 " o · utilisé %" PRIu32 " o (%u %%) · libre %" PRIu32
           " o\n",
           (uint32_t)mon.total_size, (uint32_t)(mon.total_size - mon.free_size),
           (unsigned)mon.used_pct, (uint32_t)mon.free_size);
    printf("  plus gros bloc libre %" PRIu32 " o · fragmentation %u %%\n",
           (uint32_t)mon.free_biggest_size, (unsigned)mon.frag_pct);
    printf("⚠️ ces octets-là sont réservés au LINK : ils n'apparaissent PAS dans\n");
    printf("   l'avant/après de `mem`. C'est le seul endroit où ils se voient.\n");
}

void dn_ui_get_cout(size_t *interne_avant, size_t *interne_apres,
                    size_t *psram_avant, size_t *psram_apres)
{
    if (interne_avant) {
        *interne_avant = s_int_avant;
    }
    if (interne_apres) {
        *interne_apres = s_int_apres;
    }
    if (psram_avant) {
        *psram_avant = s_psram_avant;
    }
    if (psram_apres) {
        *psram_apres = s_psram_apres;
    }
}

int dn_ui_draw_lines(void) { return s_draw_lines; }
bool dn_ui_draw_in_psram(void) { return s_draw_psram; }
bool dn_ui_direct_mode(void) { return s_direct_mode; }
int dn_ui_affinity(void) { return s_affinity; }

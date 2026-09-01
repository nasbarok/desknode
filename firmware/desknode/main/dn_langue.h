/*
 * DeskNode — `dn_langue` : L'ÉCRAN PARLE DEUX LANGUES, ET UNE SEULE TABLE LE DIT.
 * Né de `dn4-42`. Demande owner relayée par le `[CC]` du 2026-08-31.
 *
 * ══════════════════════════════════════════════════════════════════════════
 * 🔴 CE QUE CE FICHIER PORTE — ET CE QU'IL NE PORTE PAS
 * ══════════════════════════════════════════════════════════════════════════
 *
 * ✅ IL PORTE **TOUT CE QUE LA DALLE AFFICHE**. Une chaîne dessinée sur l'écran
 *    a sa clé ici, et **une seule définition**.
 *
 * ⛔ IL NE PORTE **PAS** LA CONSOLE. `dn_console.c` fait ~12 000 lignes de
 *    diagnostic écrites POUR L'AUTEUR ; l'agent est Windows-seul et le produit
 *    se règle AU DOIGT (`dn4-41`). ⇒ **la console reste en français**, et c'est
 *    une DÉCISION OWNER du 2026-09-01, ⛔ pas un oubli. Le README le dit.
 *
 * ⛔ IL NE PORTE PAS LES `ESP_LOG*`. Même motif.
 *
 * ══════════════════════════════════════════════════════════════════════════
 * 🔴 POURQUOI UNE X-MACRO, ET ⛔ PAS DEUX TABLEAUX CÔTE À CÔTE
 * ══════════════════════════════════════════════════════════════════════════
 *
 * Deux tableaux `k_fr[]` / `k_en[]` remplis séparément auraient EXACTEMENT le
 * défaut que cette story existe pour supprimer : **une clé peut y manquer d'un
 * côté, et le trou est SILENCIEUX** (un `[DN_T_X] = …` oublié laisse un `NULL`
 * que rien ne signale avant l'écran).
 *
 * ⇒ Ici, **une ligne = une clé = TOUTES ses traductions**. Le préprocesseur
 *   déplie la même liste pour l'énumération et pour chaque colonne :
 *   **oublier une traduction est une ERREUR DE COMPILATION**, ⛔ pas un trou
 *   qu'une gate doit rattraper. C'est la même doctrine que les
 *   `_Static_assert` du budget vertical de `dn4-41` : *« un commentaire qui
 *   additionne se périme au premier panneau déplacé »*.
 *
 * ✅ **AJOUTER UNE 3ᵉ LANGUE COÛTE UNE COLONNE** : un argument de plus à `X(…)`
 *    et un `k_xx[]` de plus dans le `.c`. ⛔ Aucune chasse dans 11 000 lignes.
 *    (La story ne LIVRE pas de 3ᵉ langue — elle la rend POSSIBLE.)
 *
 * ══════════════════════════════════════════════════════════════════════════
 * 🔴 LES DEUX PIÈGES DE POLICE, MESURÉS LE 2026-09-01 — ⛔ PAS SUPPOSÉS
 * ══════════════════════════════════════════════════════════════════════════
 *
 * (1) **`dn_font_33` et `dn_font_56` N'ONT AUCUN LATIN-1.** Leurs cmaps portent
 *     `32..126` **et le seul `°` (176)** — relu dans les `.c`. Ce sont les
 *     polices des VALEURS, donc celles des **unités** et des **préfixes**.
 *     ⇒ ⛔ Une unité accentuée y disparaîtrait. Les unités d'ici sont donc
 *       ASCII (+ `°`), et **la gate le contrôle en LISANT les cmaps**.
 *     ⚠️ AC4.4 de la story écrivait *« aucune chaîne traduisible ne passe par
 *        `dn_font_33`/`56` »*. **La mesure l'amende** : AC1.4 EXIGE que les
 *        unités soient dans la table, et les unités PASSENT par ces polices
 *        (`dn_widget.c`, `composer()` → `font_val()`). La propriété tenable
 *        n'est donc pas « aucune » mais **« aucune qui n'y soit rendable »**,
 *        et c'est ce que la gate vérifie. ⇒ ÉCART DÉCLARÉ.
 *
 * (2) **`⛔ ⚠ 🔴 ✅ → —` NE SONT DANS AUCUNE POLICE.** La 3ᵉ cmap est SPARSE et
 *     ne porte que `•` + les icônes FontAwesome (U+F001..U+F8A2). Un glyphe
 *     absent n'est pas « invisible » : `LV_USE_FONT_PLACEHOLDER=y` fait
 *     dessiner **une boîte** de `line_height/2 + 2` px, **sans un mot au
 *     journal**.
 *     🔴 **ET LE TIRET CADRATIN `—` (U+2014) EST DANS CE CAS.** Il était dans
 *        `k_source[].nom` — c'est-à-dire sur **TOUTES** les pages de détail,
 *        depuis toujours. ⇒ ⛔ **AUCUNE chaîne de cette table ne porte de
 *        glyphe absent**, et la gate le contrôle CONTRE LES CMAPS.
 *
 * ══════════════════════════════════════════════════════════════════════════
 * 🔴 CE QUI RESTE HORS TABLE, ET POURQUOI — ⛔ CE N'EST PAS UN OUBLI
 * ══════════════════════════════════════════════════════════════════════════
 *
 * · **`dn_console.c`, `cmd_hist` (la 4ᵉ liste des noms de case).** Elle porte
 *   **HUIT séries** (`RESEAU v` et `RESEAU ^` sont deux SENS), ⛔ pas six cases.
 *   Elle ne décrit donc pas la même chose, et la « ranger » ici ferait diverger
 *   deux comptes. Elle est FRANÇAISE, et elle le reste avec la console.
 * · **Le libellé du sélecteur lui-même (`FR` / `EN`).** ⛔ Il NE SE TRADUIT PAS
 *   (AC2.4) : écrire « Langue » à quelqu'un qui ne lit que l'anglais est
 *   exactement le défaut qu'on corrige. Ce sont des littéraux dans `dn_ui.c`.
 * · **Les `ESP_LOG*` et les messages de refus de la console.**
 */
#pragma once

#include <stdbool.h>

#include "esp_err.h"

/* ══════════════════════════════════════════════════════════════════════════
 * LES LANGUES. ⚠️ L'ANGLAIS EST **L'INDEX 0**, et ce n'est pas de l'ordre
 * alphabétique : c'est LE DÉFAUT (AC3.1, exigence owner). Une NVS vide rend
 * donc l'anglais SANS qu'aucune ligne n'ait à le dire.
 * ══════════════════════════════════════════════════════════════════════════ */
typedef enum {
    DN_LANGUE_EN = 0,
    DN_LANGUE_FR,
    DN_LANGUE_N,
} dn_langue_t;

/* ══════════════════════════════════════════════════════════════════════════
 * LA TABLE. UNE LIGNE = UNE CLÉ = TOUTES SES TRADUCTIONS.
 *
 *   X(nom, en, fr)
 *
 * ⚠️ L'ORDRE DES COLONNES SUIT `dn_langue_t` : **anglais d'abord**. Les
 *    inverser ferait afficher du français par défaut sans qu'aucun test ne
 *    bronche — c'est pourquoi la gate confronte l'ordre de l'enum à celui des
 *    tableaux du `.c`.
 * ══════════════════════════════════════════════════════════════════════════ */

/* clang-format off */
#define DN_TXT_LISTE(X)                                                        \
    /* ── LES SIX CASES ─────────────────────────────────────────────────── */ \
    /* 🔴 UNE SEULE DÉFINITION (AC1.2). `k_nom[]` et `k_desc[].titre`        */ \
    /*    énonçaient les MÊMES six noms : les traduire séparément en aurait  */ \
    /*    fait DOUZE. `k_nom[]` a DISPARU, `k_desc[].titre_cle` pointe ici.  */ \
    X(CASE_CPU,        "CPU",                      "CPU")                      \
    X(CASE_GPU,        "GPU",                      "GPU")                      \
    X(CASE_RAM,        "RAM",                      "RAM")                      \
    X(CASE_RESEAU,     "NETWORK",                  "RÉSEAU")                   \
    X(CASE_DISQUE,     "DISK",                     "DISQUE")                   \
    X(CASE_AMB,        "AMBIENT",                  "AMBIANCE")                 \
    /* Le 7e nom est celui de la DÉMO (`widget demo`) — un INSTRUMENT, mais  */ \
    /* il est DESSINÉ SUR LA DALLE, donc il est ici comme les autres.        */ \
    X(CASE_DEMO,       "DEMO 2+GAUGE",             "DÉMO 2+JAUGE")             \
                                                                               \
    /* ── LES UNITÉS ────────────────────────────────────────────────────── */ \
    /* ⚠️ DESSINÉES EN `dn_font_33`/`56` EN VEILLE (`composer()` →           */ \
    /*    `font_val()`) ⇒ **ASCII + `°` SEULEMENT**. Voir le piège (1).      */ \
    /* 🔴 TROIS bougent, et le tracker en avait compté ZÉRO.                 */ \
    X(U_PCT,           "%",                        "%")                        \
    X(U_GHZ,           "GHz",                      "GHz")                      \
    X(U_DEGC,          "\xC2\xB0" "C",             "\xC2\xB0" "C")             \
    X(U_W,             "W",                        "W")                        \
    X(U_RPM,           "rpm",                      "tr/min")                   \
    X(U_MBPS,          "Mb/s",                     "Mb/s")                     \
    X(U_GBPS,          "Gb/s",                     "Gb/s")                     \
    X(U_MOS,           "MB/s",                     "Mo/s")                     \
    X(U_GOS,           "GB/s",                     "Go/s")                     \
    X(U_GO,            "GB",                       "Go")                       \
                                                                               \
    /* ── LES PRÉFIXES DE GRANDEUR ──────────────────────────────────────── */ \
    /* ⚠️ MÊMES POLICES QUE LES UNITÉS ⇒ mêmes contraintes.                  */ \
    /* ⚠️ `boitier` = UN tachy pour DEUX ventilateurs chaînés : le nom le    */ \
    /*    dit honnêtement (`dn_link.c`), et sa traduction aussi.             */ \
    X(P_CMAX,          "c.max",                    "c.max")                    \
    X(P_EXTR_MOY,      "exh.avg",                  "extr.moy")                 \
    X(P_VENTIRAD,      "cpu fan",                  "ventirad")                 \
    X(P_BOITIER,       "case fan",                 "boitier")                  \
    X(P_D3,            "d3",                       "d3")                       \
    X(P_D4,            "d4",                       "d4")                       \
                                                                               \
    /* ── LA BARRE HEURE / DATE ─────────────────────────────────────────── */ \
    /* ⚠️ La date est posée en x = 300 : il reste 170 px utiles. Les mois    */ \
    /*    sont ABRÉGÉS des DEUX côtés, et c'est de l'arithmétique.           */ \
    X(DATE_INCONNUE,   "CLOCK NOT SET",            "HEURE NON POSÉE")          \
    X(JOUR_DIM,        "SUN.",                     "DIM.")                     \
    X(JOUR_LUN,        "MON.",                     "LUN.")                     \
    X(JOUR_MAR,        "TUE.",                     "MAR.")                     \
    X(JOUR_MER,        "WED.",                     "MER.")                     \
    X(JOUR_JEU,        "THU.",                     "JEU.")                     \
    X(JOUR_VEN,        "FRI.",                     "VEN.")                     \
    X(JOUR_SAM,        "SAT.",                     "SAM.")                     \
    X(MOIS_01,         "JAN.",                     "JANV.")                    \
    X(MOIS_02,         "FEB.",                     "FÉVR.")                    \
    X(MOIS_03,         "MAR.",                     "MARS")                     \
    X(MOIS_04,         "APR.",                     "AVR.")                     \
    X(MOIS_05,         "MAY",                      "MAI")                      \
    X(MOIS_06,         "JUN.",                     "JUIN")                     \
    X(MOIS_07,         "JUL.",                     "JUIL.")                    \
    X(MOIS_08,         "AUG.",                     "AOÛT")                     \
    X(MOIS_09,         "SEP.",                     "SEPT.")                    \
    X(MOIS_10,         "OCT.",                     "OCT.")                     \
    X(MOIS_11,         "NOV.",                     "NOV.")                     \
    X(MOIS_12,         "DEC.",                     "DÉC.")                     \
                                                                               \
    /* ── LE MENU ───────────────────────────────────────────────────────── */ \
    X(MENU_TITRE,      "MENU",                     "MENU")                     \
    X(MENU_VEILLE,     "SLEEP",                    "VEILLE")                   \
    X(MENU_ON,         "ON",                       "ON")                       \
    X(MENU_OFF,        "OFF",                      "OFF")                      \
    X(MENU_DELAI,      "SLEEP AFTER",              "DELAI AVANT VEILLE")       \
    X(MENU_MIN,        "min",                      "min")                      \
    X(MENU_LUM,        "BRIGHTNESS",               "LUMINOSITE")               \
    X(MENU_AUTO,       "AUTO",                     "AUTO")                     \
    /* ⛔ PAS « 0 % » : `0` est un duty LÉGITIME (noir). « Non choisi » et    */ \
    /*    « noir » sont deux états — la faute que `DN_CAPT_DX_ABSENT` a       */ \
    /*    coûtée deux fois à la console.                                     */ \
    X(MENU_NON_CHOISI, "-- %",                     "-- %")                     \
                                                                               \
    /* ── L'ÉTAT DE LA VEILLE, DANS LE PANNEAU LUMINOSITE ───────────────── */ \
    X(ET_MODE,         "mode",                     "mode")                     \
    X(ET_VEILLES,      "sleep(s)",                 "veille(s)")                \
    X(ET_REVEILS,      "wake(s)",                  "reveil(s)")                \
    X(ET_DELAI,        "delay",                    "delai")                    \
    X(ET_INACTIVITE,   "idle",                     "inactivite")               \
    X(ET_LUM_ABSENT,   "light sensor ABSENT",      "capteur lumiere ABSENT")   \
    X(ET_AUTO_ARME,    "auto ARMED",               "auto ARME")                \
    X(ET_AUTO_DESARME, "auto DISARMED",            "auto DESARME")             \
    X(ET_PROCHAIN,     "next level",               "prochain niveau")          \
    /* ⚠️ UNE SEULE LIGNE, à sens constant : le budget vertical du panneau   */ \
    /*    est de CINQ lignes (`_Static_assert` de `dn4-41`), et la 5e est    */ \
    /*    l'échec NVS. ⇒ ⛔ ne pas la rallonger.                             */ \
    X(ET_PEDAGO,       "a tap that wakes only RELIGHTS, it opens nothing.",    \
                       "le tap qui reveille RALLUME, il n'ouvre rien.")        \
    X(ET_NON_ENR,      "NOT SAVED",                "NON ENREGISTRE")           \
    /* ⚠️ Le nom du MODE de veille. `dn_veille.c` garde le SIEN (francais,      */ \
    /*    pour la console et les gates) — ⛔ il ne depend NI de LVGL NI d'ici,  */ \
    /*    et c'est ce qui permet a `verif_veille_dn33.py` de l'EXECUTER sur     */ \
    /*    l'hote. La traduction se fait donc DANS `dn_ui.c`, ⛔ pas la-bas.     */ \
    X(MODE_ACTIF,      "ACTIVE",                   "ACTIF")                    \
    X(MODE_AMBIENT,    "AMBIENT",                  "AMBIENT")                  \
                                                                               \
    /* ── CE QUE LE MENU NOMME QUAND LA NVS REFUSE ──────────────────────── */ \
    /* 🔴 COURTS, ET C'EST MESURÉ : la ligne d'échec vaut                    */ \
    /*    `! <nom> <NON ENREGISTRE> (<code>)`, le code pouvant aller jusqu'à */ \
    /*    `NVS_KEYS_NOT_INITIALIZED` (24 signes, le plus long des            */ \
    /*    `ESP_ERR_NVS_*` de l'IDF). Elle doit tenir dans 432 px utiles en   */ \
    /*    `dn_font_14`. ⛔ Des noms longs la feraient CLIPPER, et le clip     */ \
    /*    mangerait le CODE — c'est-à-dire le diagnostic (AC4.2).            */ \
    X(NVS_VEILLE_ON,   "sleep ON",                 "veille ON")                \
    X(NVS_VEILLE_OFF,  "sleep OFF",                "veille OFF")               \
    X(NVS_DELAI,       "delay",                    "delai")                    \
    X(NVS_BL_AUTO,     "auto bright.",             "auto lum.")                \
    X(NVS_BL_NIVEAU,   "bright. level",            "niv. lum.")                \
    X(NVS_LANGUE,      "language",                 "langue")                   \
                                                                               \
    /* ── LA PAGE DE DÉTAIL ─────────────────────────────────────────────── */ \
    /* ⚠️ Les trois premiers sont ALIGNÉS À LA MAIN sur la même colonne :    */ \
    /*    ils sont suivis de « : » dans un texte à chasse variable, donc     */ \
    /*    l'alignement est APPROCHÉ, ⛔ pas garanti. Il l'était déjà.        */ \
    X(DET_SOURCE,      "source",                   "source")                   \
    X(DET_ETAT,        "state ",                   "état  ")                   \
    X(DET_REGIME,      "regime",                   "régime")                   \
    X(DET_SUR,         "over",                     "sur")                      \
    X(DET_2COURBES,    " (BOTH curves)",           " (les DEUX courbes)")      \
    X(DET_COURBE_EN,   " (the %s curve)",          " (la courbe en %s)")       \
    X(DET_COURBE_1RE,  " (1st curve)",             " (la 1re courbe)")         \
    /* ⛔ « 0 s » se lirait comme une mesure. Aucun seau n'a vu de réel : la  */ \
    /*    fenêtre N'EXISTE PAS, elle ne vaut pas zéro.                       */ \
    X(DET_AUCUN_REEL,  "-- (no real data)",        "-- (aucun réel)")          \
    X(DET_MINMAX_VIDE, "MIN --   \xC2\xB7   MAX --",                           \
                       "MIN --   \xC2\xB7   MAX --")                           \
    X(DUREE_H,         "h",                        "h")                        \
    X(DUREE_MIN,       "min",                      "min")                      \
    X(DUREE_S,         "s",                        "s")                        \
                                                                               \
    /* ── LES SOURCES ET LEURS ÉTATS ────────────────────────────────────── */ \
    /* 🔴 LE `—` (U+2014) A DISPARU DE CES LIGNES, ET C'EST UN CORRECTIF :   */ \
    /*    il n'est dans AUCUNE police du dépôt. Il était dessiné en boîte    */ \
    /*    sur TOUTES les pages de détail. ⇒ `-` (ASCII), qui, lui, existe.   */ \
    X(SRC_MOCK,        "MOCK dn3-1 (no sensor) - instrument ARMED",            \
                       "MOCK dn3-1 (aucun capteur) - instrument ARMÉ")         \
    X(SRC_AUCUNE,      "NONE - not wired yet",     "AUCUNE - pas encore branchée") \
    X(SRC_LIEN_PC,     "PC link (dn_link)",        "liaison PC (dn_link)")     \
    X(SRC_BME680,      "BME680 (dn_capteurs)",     "BME680 (dn_capteurs)")     \
    X(ETS_GENERATEUR,  "internal generator",       "générateur interne")       \
    X(ETS_AUCUNE,      "none",                     "aucune")                   \
    X(LIEN_JAMAIS,     "never received",           "jamais recue")             \
    X(LIEN_VIVANTE,    "ALIVE",                    "VIVANTE")                  \
    X(LIEN_MORTE,      "DEAD",                     "MORTE")                    \
    X(CAPT_JAMAIS,     "never read",               "jamais lu")                \
    X(CAPT_VIVANT,     "ALIVE",                    "VIVANT")                   \
    X(CAPT_MUET,       "MUTE",                     "MUET")                     \
    X(CAPT_ABSENT,     "ABSENT",                   "ABSENT")                   \
    X(REG_ABSENTE,     "ABSENT",                   "ABSENTE")                  \
    X(REG_REELLE,      "REAL",                     "RÉELLE")                   \
    X(REG_SIMULEE,     "SIMULATED",                "SIMULÉE")                  \
    /* Le « ? » des bornes relues — il ne se traduit pas, mais il a sa clé   */ \
    /* pour qu'AUCUN littéral affiché ne reste hors table.                   */ \
    X(INCONNU,         "?",                        "?")                        \
                                                                               \
    /* ── LE WIDGET ET LA PANNE ─────────────────────────────────────────── */ \
    /* 🔴 `SIM.` EN ANGLAIS, ET C'EST UNE CONTRAINTE DE PLACE MESURÉE :      */ \
    /*    la réserve du badge fait `W_BADGE_DE_DROITE` = 66 px.              */ \
    /*    « SIMULÉ » = 54 px ✅ · « SIMULATED » = 91 px 🔴 ⇒ « SIM. » = 29.  */ \
    X(BADGE_SIMULE,    "SIM.",                     "SIMULÉ")                   \
    X(SEC_SIMULE,      "SIMULATED value - no sensor",                          \
                       "valeur SIMULÉE - aucun capteur")                       \
    X(ASSET_ABSENT,    "ASSET MISSING",            "ASSET ABSENT")

/* clang-format on */

/*
 * L'ÉNUMÉRATION DES CLÉS, DÉPLIÉE DE LA MÊME LISTE.
 *
 * 🔴 `DN_T_AUCUN = 0` EST UNE SENTINELLE, ⛔ PAS UNE CHAÎNE. Elle vaut « rien
 *    à dire » et `dn_t()` rend **NULL** dessus. C'est ce qui permet aux champs
 *    optionnels des descripteurs (`unite`, `prefixe`, `unite_haute`) de rester
 *    testables par `if (u)` exactement comme quand ils étaient des `char *` :
 *    ⛔ pas un `""` qui se serait affiché comme un espace.
 */
typedef enum {
    DN_T_AUCUN = 0,
#define X(nom, en, fr) DN_T_##nom,
    DN_TXT_LISTE(X)
#undef X
    DN_T_N
} dn_txt_t;

/* ── L'API ───────────────────────────────────────────────────────────────── */

/* La chaîne dans la langue COURANTE. Rend NULL sur `DN_T_AUCUN` ou hors bornes. */
const char *dn_t(dn_txt_t cle);

/*
 * La chaîne dans UNE langue nommée.
 *
 * 🔴 C'EST PAR ELLE QUE LA CONSOLE RESTE FRANÇAISE. Les journaux et le REPL
 *    appellent `dn_t_fr()` : ils lisent la MÊME définition que la dalle, donc
 *    rien ne peut diverger, et pourtant ils ne bougent pas quand l'écran change
 *    de langue. ⇒ **une seule définition, deux lecteurs.**
 */
const char *dn_t_l(dn_langue_t l, dn_txt_t cle);
const char *dn_t_fr(dn_txt_t cle);

dn_langue_t dn_langue(void);

/*
 * Pose la langue COURANTE. ⛔ Ne redessine RIEN et ⛔ n'écrit RIEN en NVS :
 * c'est l'appelant qui décide des deux (`dn_ui` pour le repeint, `dn_reglage`
 * pour la persistance). Séparer les trois est ce qui permet à `dn_reglage_init()`
 * de poser la langue AVANT que la moindre scène n'existe.
 */
void dn_langue_set(dn_langue_t l);

/* Le code court NON TRADUIT du sélecteur — « EN », « FR ». AC2.4 : ⛔ il ne se
 * traduit pas. Rend NULL hors bornes. */
const char *dn_langue_code(dn_langue_t l);

/* Le code court -> la langue. Rend `DN_LANGUE_N` si le code est inconnu. */
dn_langue_t dn_langue_de_code(const char *code);

/*
 * L'AUDIT DE LA TABLE, JOUÉ UNE FOIS AU BOOT.
 *
 * ⚠️ La X-macro rend un trou IMPOSSIBLE À COMPILER — cet audit ne cherche donc
 *    pas des trous. Il cherche ce que le compilateur ne voit pas : une
 *    traduction VIDE (`""`), qui compile parfaitement et n'affiche rien.
 * Rend le nombre de défauts trouvés (0 = tout va bien) et les NOMME au journal.
 */
int dn_langue_audit(void);

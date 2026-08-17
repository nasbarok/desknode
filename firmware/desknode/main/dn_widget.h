/*
 * dn_widget — LE MODÈLE DE CASE DU DASHBOARD (dn3-1, marche P6)
 *
 * ════════════════════════════════════════════════════════════════════════════
 * CE QUE CE MODULE EST
 * ════════════════════════════════════════════════════════════════════════════
 *
 * Une BRIQUE DE DESSIN paramétrée. Elle produit une case complète — icône,
 * titre, valeur(s), unité, couleur d'accent, indicateur optionnel, données
 * secondaires — à partir d'un DESCRIPTEUR et d'un ÉTAT, en UN seul appel.
 *
 * Le brief le demande mot pour mot : « Un modèle de widget unique
 * (SystemMetricWidget : icône, titre, valeur, unité, couleur, indicateur
 * optionnel, données secondaires, page détail) — ajouter une métrique future
 * (SSD, ventilateurs, puissance, NAS, Bambu…) ne redessine pas l'UI. »
 *
 * ⇒ LE POINT D'AJOUT D'UNE MÉTRIQUE EST UNE LIGNE DE `dn_widget_desc_t`.
 *   Aucune fonction de dessin ne se touche. C'est falsifiable, et c'est
 *   falsifié à la demande : `widget demo on` construit une 7e métrique fictive
 *   depuis un descripteur, `widget demo off` la retire (AC1).
 *
 * ════════════════════════════════════════════════════════════════════════════
 * CE QUE CE MODULE N'EST PAS
 * ════════════════════════════════════════════════════════════════════════════
 *
 * - Il n'a NI TÂCHE, NI ÉTAT PROPRE, NI PÉREMPTION. Ce n'est pas un module du
 *   patron `dn_link`/`dn_capteurs` : il ne va chercher aucune donnée. On lui
 *   DONNE un état ; il le dessine. La péremption, les compteurs par cause et
 *   la cadence restent chez les sources.
 * - Il ne connaît PAS la grille. Position et dimensions sont des paramètres :
 *   la géométrie fait foi ailleurs (dn1-4 l'a dérivée, dn3-2 la fige).
 * - Il ne prend PAS le verrou LVGL. Voir le contrat ci-dessous.
 * - Il n'est PAS un cas spécial « Ambiance ». La variante multi-grandeurs de
 *   D6 est un MÉCANISME UNIFORME (`n_grandeurs`), pas une branche.
 *
 * ════════════════════════════════════════════════════════════════════════════
 * 🔴 LE CONTRAT DE VERROU — LE SENS EST INVERSÉ, ET C'EST DÉLIBÉRÉ
 * ════════════════════════════════════════════════════════════════════════════
 *
 * RÈGLE DU DÉPÔT : une fonction PUBLIQUE prend le verrou LVGL elle-même,
 * l'appelant JAMAIS (`dn_ui_cpu_maj`, `dn_ui_nav_open`, `dn_ui_label_show`…).
 *
 * `dn_widget_*` FAIT L'INVERSE : elle EXIGE que `lvgl_port_lock()` soit DÉJÀ
 * pris par l'appelant, et ne le prend pas. Deux motifs, tous deux mesurables —
 * ce n'est pas une commodité :
 *
 *  1. LE MOTIF DE `case_vive_poser`, GÉNÉRALISÉ (dn2-1). Un widget
 *     bi-grandeurs écrit DEUX valeurs. Les poser sous deux verrous successifs
 *     laisserait une trame afficher une température neuve à côté d'une
 *     humidité périmée. « Il n'y a pas de demi-silence » : un capteur muet
 *     l'est pour ses deux grandeurs, et ça doit se voir en UNE fois.
 *
 *  2. LE MOTIF D'AC8, QUI EST NEUF. Le groupage d'invalidation coupe
 *     `lv_display_enable_invalidation()`, écrit TOUS les enfants, la rétablit,
 *     puis invalide le conteneur. Ce triptyque n'a de sens que sous un verrou
 *     UNIQUE : le relâcher au milieu laisserait un cycle LVGL passer avec
 *     l'invalidation coupée — c'est-à-dire un écran FIGÉ sans erreur.
 *
 * ⇒ Les seuls appelants légitimes sont donc les fonctions publiques de `dn_ui`
 *   (qui prennent le verrou) et les callbacks de timer LVGL (où le portage le
 *   détient déjà — son mutex est RÉCURSIF, `esp_lvgl_port.c:77`, donc même un
 *   `lvgl_port_lock()` imbriqué serait sûr ; on ne s'appuie pas dessus, on
 *   l'écrit pour que personne ne le redécoute).
 *
 * ════════════════════════════════════════════════════════════════════════════
 * DESCRIPTEUR STATIQUE vs ÉTAT DYNAMIQUE vs POINTEURS — TROIS CHOSES SÉPARÉES
 * ════════════════════════════════════════════════════════════════════════════
 *
 *   `dn_widget_desc_t`  const, en .rodata   ce que la métrique EST
 *   `dn_widget_etat_t`  en RAM, PERSISTANT  ce qu'elle VAUT en ce moment
 *   `dn_widget_t`       pointeurs LVGL      où elle est DESSINÉE
 *
 * 🔴 CETTE SÉPARATION EST LA PARADE AU USE-AFTER-FREE DE dn1-3. Ce qui SURVIT
 *    au démontage de la scène (l'état) n'est jamais un pointeur ; ce qui est un
 *    pointeur (`dn_widget_t`) est remis à zéro par `dn_widget_oublier()` aux
 *    TROIS sites de démontage. Un pointeur de label qui survit à son label,
 *    écrit par une tâche asynchrone, c'est exactement le défaut que la revue de
 *    dn1-3 a trouvé.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "lvgl.h"

#ifdef __cplusplus
extern "C" {
#endif

/* D6 en admet 2 (Ambiance). Le mécanisme est générique ; cette borne n'est
 * qu'une taille de tableau, et l'élargir ne touche aucune fonction de dessin. */
#define DN_WIDGET_GRANDEURS_MAX 2

/* Longueurs : un texte formaté (« -1234,5 » + marge) et une ligne secondaire. */
#define DN_WIDGET_TXT_MAX 16
#define DN_WIDGET_SEC_MAX 40

/*
 * ── LES TROIS RÉGIMES DE VALEUR, DANS LE TYPE ────────────────────────────────
 *
 * Ils ne vivent PAS dans des booléens épars. Un `bool valide` seul ne sait pas
 * dire « cette valeur est fabriquée » : il ne connaît que vrai/faux, et un mock
 * s'y présente exactement comme une mesure. C'est le mensonge d'interface
 * qu'AC3 interdit — « en plus discret » qu'un CPU figé à 47 %.
 *
 * 🔴 `ABSENTE` VAUT 0 DÉLIBÉRÉMENT. Un `dn_widget_etat_t` statique naît donc
 *    ABSENT, jamais RÉEL. Même raisonnement que l'initialiseur `= "--"` de
 *    `s_vive_texte[]` (perdu une fois, CR du 2026-08-17) : la valeur par défaut
 *    d'un état statique doit être L'AVEU D'IGNORANCE, jamais une affirmation.
 */
typedef enum {
    DN_VAL_ABSENTE = 0, /* aucune source, ou source morte  -> « -- » grisé */
    DN_VAL_REELLE,      /* mesurée par une source réelle   -> blanc */
    DN_VAL_SIMULEE,     /* produite par un mock            -> ambre + « SIMULÉ » */
    DN_VAL_REGIME_COUNT,
} dn_val_regime_t;

/* Nom lisible. ⚠️ RELU de l'énumération, jamais récité d'ailleurs : la console
 * imprime ceci, et une étiquette qui ment est un défaut à part entière. */
const char *dn_val_regime_nom(dn_val_regime_t r);

/* Une grandeur du widget. `unite` peut être NULL (aucune unité affichée). */
typedef struct {
    const char *unite;  /* « % », « °C », « tr/min » — affichée après la valeur */
    const char *icone;  /* glyphe UTF-8 en ligne, NULL = aucun (voir dn_font.h) */
} dn_widget_grandeur_t;

/*
 * LE DESCRIPTEUR — const, en .rodata. AJOUTER UNE MÉTRIQUE, C'EST AJOUTER UNE
 * LIGNE ICI. Rien d'autre.
 */
typedef struct {
    const char *icone;   /* icône de la case, en UTF-8 (dn_font.h). AC7 l'exige. */
    const char *titre;   /* « CPU », « AMBIANCE » — accentué, la police suit */
    uint32_t couleur;    /* 0xRRGGBB, accent. dn3-1 le PORTE ; dn3-3 l'exploite. */
    uint8_t n_grandeurs; /* 1..DN_WIDGET_GRANDEURS_MAX */
    bool indicateur;     /* jauge horizontale sur la grandeur 0 */
    int32_t ind_min;     /* bornes de la jauge, dans l'unité BRUTE de l'état */
    int32_t ind_max;
    dn_widget_grandeur_t grandeurs[DN_WIDGET_GRANDEURS_MAX];
} dn_widget_desc_t;

/*
 * L'ÉTAT — en RAM, et il SURVIT au démontage de la scène.
 * C'est lui qui garantit qu'une bascule d'écran ne rend pas les cases à un
 * factice : le texte conservé est reposé à la (re)construction.
 */
typedef struct {
    dn_val_regime_t regime;
    char txt[DN_WIDGET_GRANDEURS_MAX][DN_WIDGET_TXT_MAX];
    int32_t brut[DN_WIDGET_GRANDEURS_MAX]; /* pour la jauge, unité du descripteur */
    char secondaire[DN_WIDGET_SEC_MAX];    /* ligne libre, "" = rien à dire */
} dn_widget_etat_t;

/* LES POINTEURS LVGL. Jamais persistés au-delà de la vie de la scène. */
typedef struct {
    lv_obj_t *racine; /* le conteneur CLIQUABLE — c'est lui la zone tactile */
    lv_obj_t *valeur[DN_WIDGET_GRANDEURS_MAX];
    lv_obj_t *jauge;  /* NULL si le descripteur n'a pas d'indicateur */
    lv_obj_t *sec;    /* NULL si aucune donnée secondaire n'est prévue */
    lv_obj_t *badge;  /* la marque « SIMULÉ », créée mais masquée si non simulé */
} dn_widget_t;

/*
 * ── LA BRIQUE TACTILE, UNE SEULE DÉFINITION ──────────────────────────────────
 *
 * 🔴 ELLE VIT ICI ET NULLE PART AILLEURS, et c'est la raison n°1 pour laquelle
 *    ce module existe plutôt qu'un bloc de plus dans `dn_ui.c`. Les deux
 *    drapeaux qui rendent vraie la propriété « toute la case est la zone
 *    tactile » — prouvée à 4 px du bord en dn1-4 — étaient déjà DUPLIQUÉS entre
 *    `zone_creer()` et `panneau()`. Les dupliquer une troisième fois dans le
 *    widget aurait doublé le nombre d'endroits où AC4 peut se casser EN SILENCE.
 *
 *  1. `CLICKABLE` sur le CONTENEUR, enfants laissés NON cliquables : LVGL
 *     remonte au premier ancêtre cliquable, donc un tap sur le texte comme dans
 *     un coin vide arrive au même endroit.
 *  2. `SCROLLABLE` RETIRÉ : `lv_obj_create()` le pose par défaut
 *     (`lv_obj.c:584-593`) et un conteneur scrollable AVALE le geste dès que le
 *     doigt roule de quelques pixels — ça marche au centre, ça rate au bord.
 */
lv_obj_t *dn_widget_zone_creer(lv_obj_t *parent, int x, int y, int w, int h,
                               lv_event_cb_t cb, void *user);

/* Le même aplat, mais NON cliquable — pour porter du texte (panneaux du détail). */
lv_obj_t *dn_widget_panneau(lv_obj_t *parent, int x, int y, int w, int h);

/*
 * Un label. RETIRE `CLICKABLE` explicitement.
 * ⚠️ `lv_label` le retire déjà de lui-même (`lv_label.c:762`) — on le refait
 *    quand même, parce que la garantie doit être LOCALE : le jour où ce helper
 *    servira à autre chose qu'un label, l'oubli serait silencieux.
 */
lv_obj_t *dn_widget_texte(lv_obj_t *parent, const char *s, const lv_font_t *font,
                          lv_color_t couleur, int x, int y);

/*
 * ── CONSTRUIRE ───────────────────────────────────────────────────────────────
 * Dessine la case complète et remplit `out`. `etat` peut être NULL (la case
 * naît alors ABSENTE, donc « -- » grisé — jamais un chiffre d'apparence réelle).
 * ⚠️ VERROU LVGL DÉJÀ PRIS PAR L'APPELANT.
 */
void dn_widget_creer(lv_obj_t *parent, int x, int y, int w, int h,
                     const dn_widget_desc_t *desc, const dn_widget_etat_t *etat,
                     lv_event_cb_t cb, void *user, dn_widget_t *out);

/*
 * ── METTRE À JOUR ────────────────────────────────────────────────────────────
 * Applique `etat` aux objets de `w`. No-op sûr si `w->racine` est NULL (modèle
 * REBUILD en vue détail : le dashboard n'existe pas, l'état est conservé et
 * sera reposé à la construction suivante — rien n'est perdu, rien n'est touché).
 * ⚠️ VERROU LVGL DÉJÀ PRIS PAR L'APPELANT.
 */
void dn_widget_maj(const dn_widget_desc_t *desc, const dn_widget_etat_t *etat,
                   dn_widget_t *w);

/* Remet TOUS les pointeurs à NULL. À appeler aux trois sites de démontage. */
void dn_widget_oublier(dn_widget_t *w);

/*
 * ── AC8 : LE GROUPAGE D'INVALIDATION, ET C'EST UN A/B, PAS UN RÉGLAGE ────────
 *
 * `false` (défaut) : chaque enfant modifié produit SA zone sale. LVGL NE FUSIONNE
 *   PAS — mesuré en dn2-1 : deux cases côte à côte dans la MÊME bande de 128
 *   lignes du draw buffer coûtent 2,0 flushes, pas 1,0. Un widget à N enfants
 *   qui changent coûterait donc N flushes, chacun attendant sa trame.
 * `true` : l'invalidation est coupée le temps d'écrire les enfants, puis le
 *   CONTENEUR est invalidé une fois — une seule zone sale de 225 x 156 px.
 *
 * ⚠️ CE N'EST PAS UNE OPTIMISATION ACQUISE : c'est l'hypothèse qu'AC8 doit
 *    FALSIFIER, et le dépôt a déjà vu une prédiction démentie d'un facteur 10
 *    (T9 de dn2-1). Les deux branches restent vivantes — une élimination sans
 *    son témoin n'est pas une élimination.
 */
void dn_widget_set_groupage(bool on);
bool dn_widget_groupage(void);

/*
 * ── AC9 : L'OPACITÉ, ET C'EST AUSSI UN A/B ───────────────────────────────────
 * Opacité des CASES (conteneurs). `LV_OPA_COVER` (255) supprime le re-blit du
 * fond sous chaque case — gratuit en mémoire, coûteux en esthétique : le Living
 * PCB ne transparaîtrait plus DANS les cases. `LV_OPA_70` (179) est l'état des
 * lieux, monté de 40 % après le constat owner « les pistes claires mangeaient
 * le texte blanc » (2026-08-16).
 * ⚠️ Ne s'applique qu'aux conteneurs CRÉÉS APRÈS l'appel : il faut reconstruire
 *    la scène pour la voir. La console le fait, et le dit.
 */
void dn_widget_set_opa(uint8_t opa);
uint8_t dn_widget_opa(void);

#ifdef __cplusplus
}
#endif

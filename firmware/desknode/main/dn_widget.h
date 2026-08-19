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

/*
 * ── dn4-6 / D11 : LA BORNE PASSE DE 2 À 4, ET PAS AVANT SES DEUX CORRECTIFS ──
 *
 * D6 en admettait 2 (Ambiance). D11 demande `CPU` à TROIS grandeurs
 * (% · GHz · cœur le plus chargé) et `GPU` à QUATRE (% · °C · W · tr/min).
 *
 * 🔴 L'ORDRE EST UN LIVRABLE, PAS UNE PRÉCAUTION DE STYLE. Élargir cette borne
 *    AVANT de borner la jauge aurait rendu ATTEIGNABLE un défaut jusque-là
 *    théorique : à n ≥ 3 empilé avec jauge, `y_bas` vaut 168 puis 208, et la
 *    jauge était posée à `y_bas + 6` SANS AUCUN TEST contre `h`. Elle serait
 *    donc sortie de la case, EN SILENCE — 3ᵉ occurrence de la même famille.
 *    ⇒ La borne ne monte qu'APRÈS le correctif, et le correctif a son témoin
 *      (`widget demo` à n ≥ 3 + jauge, log capturé).
 *
 * ⚠️ CE QUE L'ÉLARGISSEMENT COÛTE EN RAM, ET IL SE LIT, IL NE SE SUPPOSE PAS :
 *    `txt[N][16]` + `brut[N]` par état de case, × 6 cases + la démo. Le chiffre
 *    RÉEL est dans la table de non-régression d'AC13 (`mem` avant/après).
 */
#define DN_WIDGET_GRANDEURS_MAX 4

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

/* LA couleur d'un régime — UNE seule définition pour tout le firmware.
 * 🔴 Exposée le 2026-08-18 (revue de code) : les cases NUES peignaient
 * `regime == REELLE ? blanc : gris`, ce qui rendait SIMULÉE **à l'identique**
 * d'ABSENTE — or `widget pousser <idx>` sur une case nue est le chemin NOMINAL
 * de l'instrument d'AC8. Un chiffre inventé s'affichait donc dans le gris que ce
 * dépôt réserve à « aucune source », pendant que la console annonçait SIMULEE.
 * AC3 exige trois régimes DISTINGUÉS : la convention ne doit exister qu'ICI. */
lv_color_t dn_val_regime_couleur(dn_val_regime_t r);

/*
 * ── dn4-6 / AC9 : LA PRÉCISION EST UNE PROPRIÉTÉ DE LA GRANDEUR ──────────────
 *
 * 🔴 `fmt_dixiemes()` était GLOBAL et rendait TOUJOURS un dixième. « 604,0 tr/min »
 *    pour un ventilateur et « 212,0 W » pour une puissance : la source ne porte
 *    PAS cette décimale, et l'inventer est un mensonge d'interface — la même
 *    famille que le « 34,3 Go » décimal affiché contre le « 31,9 » de Windows.
 *
 * ⚠️ `NON_RENSEIGNEE` VAUT 0 DÉLIBÉRÉMENT, ET C'EST LE MÊME MOTIF QUE
 *    `DN_VAL_ABSENTE = 0`. Un champ ajouté à une table d'initialiseurs désignés
 *    naît à zéro : si `0` avait voulu dire « entier », TOUTES les grandeurs
 *    existantes seraient passées de « 46,0 % » à « 46 % » EN SILENCE, au premier
 *    build, sans qu'une ligne de descripteur ait bougé. Ici l'oubli est
 *    DÉTECTABLE : `dn_prec_dixiemes()` journalise et retombe sur le dixième,
 *    c'est-à-dire sur le comportement d'AVANT. C'est le patron de la sentinelle
 *    décalée de `k_pc[]`, appliqué à un champ au lieu d'un index.
 * ⛔ Le FIL reste en ENTIERS (dixièmes) dans les deux sens : c'est l'AFFICHAGE
 *    qui porte la précision, jamais le transport (doctrine `parse_entier`).
 */
typedef enum {
    DN_PREC_NON_RENSEIGNEE = 0, /* ⛔ oubli de descripteur — journalisé */
    DN_PREC_ENTIER,             /* « 212 W », « 604 tr/min » */
    DN_PREC_DIXIEME,            /* « 46,0 % », « 61,0 °C », « 4,7 GHz » */
} dn_prec_t;

/* Une grandeur du widget. `unite` peut être NULL (aucune unité affichée). */
typedef struct {
    const char *unite;  /* « % », « °C », « tr/min » — affichée après la valeur */
    const char *icone;  /* glyphe UTF-8 en ligne, NULL = aucun (voir dn_font.h) */
    /*
     * ── dn4-6 / AC1 : LE MARQUAGE, ET C'EST UN CHAMP À LUI, PAS UN DÉTOURNEMENT ─
     *
     * 🔴 `CPU` porte DEUX POURCENTAGES : la moyenne (« 54 % ») et le cœur le plus
     *    chargé (« 88 % »). Deux lignes visuellement identiques dont l'une ment par
     *    omission — c'est précisément ce que D11 veut faire cesser (un cœur saturé
     *    sur 16 logiques ne pèse que ~6 % de moyenne).
     * ⚠️ La maquette écrit « c.max 88 % ». Le champ `icone` accepte n'importe quel
     *    préfixe UTF-8 et aurait « marché » — ⛔ mais il s'appelle `icone` et sa
     *    doc dit « glyphe ». Détourner un champ en silence, c'est fabriquer la
     *    prochaine divergence `.h`/code, et ce dépôt en a déjà payé trois.
     * ⇒ Un champ NOMMÉ. `icone` reste un glyphe, `prefixe` est du texte.
     * ⚠️ Le préfixe est CONSERVÉ quand la valeur est ABSENTE (« c.max -- ») :
     *    l'unité disparaît parce qu'elle affirmerait qu'on sait de quoi on parle,
     *    le préfixe reste parce qu'il DÉSIGNE la grandeur qui manque. Cacher le
     *    préfixe cacherait l'existence même de la grandeur — ce que W10 interdit.
     */
    const char *prefixe;
    dn_prec_t prec;     /* AC9 — ⛔ 0 = NON RENSEIGNÉE, journalisée */
    /*
     * ── L'ÉCHELLE HAUTE — CONSTAT OWNER EN SÉANCE, 2026-08-19 ────────────────
     *
     * 🔴 VERBATIM : *« réseau, pour si valeur haute, convertir en Gb/s »*.
     *    `RÉSEAU` porte les deux chaînes les plus longues du dashboard :
     *    « ↓ 99999,9 Mb/s » mesure **202 px pour 201 utiles** — elle DÉBORDE
     *    déjà, et LVGL la clipperait sans un mot.
     *
     * ⚠️ ET ÇA NE CASSE PAS « L'UNITÉ VIT DANS LE DESCRIPTEUR ». C'est la règle
     *    qui permet *« une valeur ABSENTE ne porte JAMAIS son unité »*, et elle
     *    tient : les DEUX unités sont ici, en `.rodata`. Ce qui varie n'est pas
     *    l'endroit où l'unité vit, c'est LAQUELLE des deux s'applique — et le
     *    choix est porté par l'ÉTAT (`echelle_haute`), là où vivent déjà le
     *    régime et le texte.
     * ⛔ Le seuil et le diviseur sont DEUX champs, ⛔ pas un seul déduit de
     *    l'autre : « bascule à 1000 » et « divise par 1000 » coïncident pour
     *    Mb/s → Gb/s et ne coïncideront pas pour la prochaine paire. Déduire
     *    l'un de l'autre serait une hypothèse cachée dans une table.
     * ⚠️ `seuil_haut = 0` ⇒ AUCUNE bascule. C'est le défaut, et c'est le cas de
     *    cinq grandeurs sur sept : une unité qui change toute seule est un
     *    comportement, pas une commodité — il se DEMANDE.
     */
    int32_t seuil_haut;      /* en dixièmes de `unite`. 0 = pas de bascule */
    int32_t diviseur_haut;   /* dixièmes de `unite` par dixième de `unite_haute` */
    const char *unite_haute; /* « Gb/s » — ⛔ NULL si `seuil_haut` est nul */
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
    /*
     * ── LA JAUGE, ET LE CONTRAT GÉOMÉTRIQUE QU'ELLE IMPOSE (W5) ─────────────
     *
     * Jauge horizontale sur la grandeur 0. ⚠️ ELLE N'EST PLUS CONDITIONNÉE À
     * `n_grandeurs == 1` : jusqu'à dn3-2 le code testait
     * `if (desc->indicateur && n == 1)`, si bien qu'un descripteur bi-grandeurs
     * avec `indicateur = true` PERDAIT SA JAUGE SANS ERREUR NI LOG, alors que ce
     * champ était documenté ici SANS restriction. Corrigé en dn4-1 : le champ
     * fait ce qu'il dit.
     *
     * 🔴 ET dn4-6 FERME LA MOITIÉ QUI RESTAIT OUVERTE — 3ᵉ OCCURRENCE. dn4-1
     *    avait rendu AUDIBLE l'abandon de la ligne secondaire, et laissé la
     *    JAUGE posée à `y_bas + 6` SANS AUCUN TEST contre `h` (`dn_widget.c`,
     *    `lv_obj_set_pos(out->jauge, …)`). Tant que le maximum était 2, aucune
     *    case ne pouvait sortir de la boîte ; à 3 et 4 grandeurs empilées, si.
     *    ⚠️ Et le défaut ne se serait PAS VU comme une erreur : LVGL clippe au
     *       parent sans un mot. Une jauge à moitié dehors ressemble à une jauge.
     *
     * ── LA RÈGLE DE PRIORITÉ, ÉCRITE ET NON SUBIE ────────────────────────────
     *
     *        VALEURS  >  JAUGE  >  SECONDAIRE
     *
     * · Les VALEURS d'abord : elles sont la raison d'être de la case, et leur
     *   nombre est déclaré par `n_grandeurs`. Une valeur qui ne tient pas est
     *   déjà écrêtée ET journalisée par le clamp de `GRANDEURS_MAX` (dn4-1).
     * · La JAUGE ensuite : elle est demandée par un CHAMP EXPLICITE du
     *   descripteur (`indicateur`), c'est-à-dire par une intention écrite.
     * · La SECONDAIRE en dernier : c'est une ligne LIBRE que l'état peut laisser
     *   vide de toute façon — l'abandonner ne contredit aucune déclaration.
     *
     * ⛔ ET CHAQUE ABANDON EST AUDIBLE (`ESP_LOGW` dans `dn_widget_creer`), pour
     *    la jauge comme pour la secondaire. Un abandon silencieux était LE défaut.
     *
     * ── L'ARITHMÉTIQUE, POSÉE AVANT LE CODE ET RELUE DANS `dn_widget.c` ───────
     * (h = 156, `val_y` = 48, `val_pas` = 40, `W_JAUGE_H` = 10, `W_SEC_H` = 20 ;
     *  la jauge consomme `W_JAUGE_H + 10` = 20 px, pas 26 ; `y_bas` est calculé
     *  sur le nombre de LIGNES, qui n'est le nombre de grandeurs qu'en EMPILÉ.)
     *
     *   lignes  jauge   y_bas   + jauge        + secondaire
     *   -----------------------------------------------------------------
     *     1     non      88        —           108 <= 156   sec OUI
     *     1     oui      88      108           128 <= 156   sec OUI     (RAM)
     *     2     non     128        —           148 <= 156   sec OUI
     *     2     oui     128      148           168 >  156   sec NON  (journalisé)
     *     3     oui     168   188 > 156        🔴 JAUGE HORS CASE  <- dn4-6
     *     4     oui     208   228 > 156        🔴 JAUGE HORS CASE  <- dn4-6
     *
     * ⚠️ AUCUNE DES SIX CASES NE DÉCLENCHE LE DÉFAUT AUJOURD'HUI : `RAM` est la
     *    seule à `indicateur = true` et elle est à une ligne. C'est EXACTEMENT ce
     *    qui l'a laissé passer deux fois. Le témoin se PROVOQUE (`widget demo`,
     *    descripteur à n ≥ 3 AVEC jauge), il ne s'observe pas en régime.
     *
     * ⚠️ CE QUE ÇA NE CHANGE PAS, ET QUI SE VÉRIFIE : `RAM` GARDE sa jauge ET son
     *    « 12,1 / 32 Go ». Vérifié par `widget` (`RAM 1 OUI OUI`), pas supposé.
     *
     * ⛔ RESSERRER LA GÉOMÉTRIE (`val_pas`, `W_JAUGE_H`) POUR FAIRE TENIR LES
     *    TROIS reste écarté : il faudrait descendre `val_pas` à 34, ce qui change
     *    la lisibilité des SIX cases pour le besoin d'une seule.
     */
    bool indicateur;
    int32_t ind_min;     /* bornes de la jauge, dans l'unité BRUTE de l'état */
    int32_t ind_max;
    dn_widget_grandeur_t grandeurs[DN_WIDGET_GRANDEURS_MAX];
} dn_widget_desc_t;

/*
 * L'ÉTAT — en RAM, et il SURVIT au démontage de la scène.
 * C'est lui qui garantit qu'une bascule d'écran ne rend pas les cases à un
 * factice : le texte conservé est reposé à la (re)construction.
 */
/*
 * ── W10 (dn4-1) : UNE CASE RÉELLE DONT UNE SEULE GRANDEUR EST ABSENTE ────────
 *
 * Le cas exact : le GPU rend son % mais pas sa °C (source de température
 * indisponible sur une carte donnée). Faut-il taire les deux ?
 *
 * 🔴 NON — ET C'EST UN ÉCART ASSUMÉ AVEC `dn_ui_ambiance_maj`, PAS UN OUBLI.
 *    AMBIANCE grise ses deux grandeurs ensemble (« il n'y a pas de demi-
 *    silence ») parce qu'elles viennent d'UN SEUL capteur : si le BME680 se
 *    tait, il se tait pour les deux, et en afficher une seule serait affirmer
 *    qu'on sait quelque chose du capteur. Ici les deux grandeurs ont des
 *    sources INDÉPENDANTES : taire le % GPU parce que la °C manque
 *    supprimerait une information VRAIE et disponible.
 *
 * ⇒ RÈGLE : le RÉGIME reste porté par la CASE (le motif du verrou unique —
 *   cohérence de trame — est intact), et une grandeur dont le texte est VIDE
 *   s'affiche « -- » DANS LA COULEUR D'ABSENCE, quelle que soit la couleur du
 *   régime de la case. Une case RÉELLE peut donc porter une ligne grise.
 * ⛔ Ce qui reste interdit et ne se renégocie pas : inventer la grandeur
 *   manquante, l'emprunter à une autre, ou recopier celle du CPU.
 */
typedef struct {
    dn_val_regime_t regime;
    /* ⚠️ Un `txt[i]` VIDE n'est PAS « zéro » : c'est « cette grandeur-là est
     * absente » (W10). Le modèle l'affiche « -- » en gris, sans unité. */
    char txt[DN_WIDGET_GRANDEURS_MAX][DN_WIDGET_TXT_MAX];
    /* Valeur brute, pour la jauge — unité du descripteur.
     * ⚠️ SEUL `brut[0]` est écrit et lu aujourd'hui (relevé en revue le
     *    2026-08-18) : `case_poser` ne prend qu'un `brut0`, et l'indicateur ne
     *    porte que sur la grandeur 0 (voir `indicateur` ci-dessous). Le tableau
     *    est dimensionné pour N par cohérence avec `txt[]` et `valeur[]` — il
     *    est PRÊT, pas mort, mais ne pas croire qu'il est alimenté. */
    int32_t brut[DN_WIDGET_GRANDEURS_MAX];
    /* ⚠️ QUELLE unité s'applique à `txt[i]` — un bit par grandeur. Posé par
     *    celui qui a FORMATÉ (il seul connaît le nombre), lu par celui qui
     *    CONCATÈNE. ⛔ Ne jamais le déduire du texte : « 99,9 » ne dit pas s'il
     *    s'agit de Mb/s ou de Gb/s, et le deviner serait un mensonge d'une
     *    unité entière. */
    bool echelle_haute[DN_WIDGET_GRANDEURS_MAX];
    char secondaire[DN_WIDGET_SEC_MAX];    /* ligne libre, "" = rien à dire */
} dn_widget_etat_t;

/* LES POINTEURS LVGL. Jamais persistés au-delà de la vie de la scène. */
typedef struct {
    lv_obj_t *racine; /* le conteneur CLIQUABLE — c'est lui la zone tactile */
    lv_obj_t *valeur[DN_WIDGET_GRANDEURS_MAX];
    lv_obj_t *jauge;  /* NULL si le descripteur n'a pas d'indicateur */
    lv_obj_t *sec;    /* NULL si aucune donnée secondaire n'est prévue */
    lv_obj_t *badge;  /* la marque « SIMULÉ », créée mais masquée si non simulé */
    /* ⚠️ dn4-6 : `n` et `w` sont MÉMORISÉS À LA CONSTRUCTION, ⛔ pas relus du
     *    descripteur à la mise à jour. Le descripteur peut demander 5 grandeurs
     *    et n'en obtenir que 4 (clamp journalisé) ; repositionner sur `n = 5`
     *    calerait la colonne droite d'une ligne qui n'existe pas. Ce qui a été
     *    POSÉ fait foi — même doctrine que `dn_ui_widget_pointeurs()`, qui relit
     *    les pointeurs et jamais la demande. */
    uint8_t n;        /* grandeurs RÉELLEMENT posées */
    int16_t w;        /* largeur de la case, pour le calage à droite */
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

/* ── La PISTE de la jauge (le fond, la part NON remplie) ─────────────────────
 * Constat owner du 2026-08-18 : la piste sombre d'origine (`0x203040`) se lit
 * verdâtre contre le PCB du fond et n'aide pas l'indicateur violet à ressortir.
 * Réglable à chaud (`widget piste <0xRRGGBB>`) — même patron que `opa`/`voile` :
 * l'arbitrage est un CONSTAT OWNER sur la dalle, pas une intuition.
 * ⚠️ N'affecte que les jauges CRÉÉES ensuite ⇒ l'appelant reconstruit la scène. */
void dn_widget_set_piste(uint32_t rgb);
uint32_t dn_widget_piste(void);

/*
 * ── AC8 : LE GROUPAGE D'INVALIDATION, ET C'EST UN A/B, PAS UN RÉGLAGE ────────
 *
 * ⚠️ LE DÉFAUT EST `true` DEPUIS QUE W7 A ÉTÉ TRANCHÉ PAR LA MESURE. Cet en-tête
 *    a annoncé `false` jusqu'au 2026-08-18 — il décrivait l'état d'AVANT l'A/B,
 *    dans le document qu'AC1 désigne comme le contrat du module. Quelqu'un qui
 *    rejouait la campagne en croyant partir de la branche fine mesurait DEUX
 *    FOIS la même branche. Relevé en revue de code.
 *
 * `false` : chaque enfant modifié produit SA zone sale. LVGL NE FUSIONNE
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
 * ── AC9/W8 : L'OPACITÉ DES CASES — A/B JOUÉ, ET L'OWNER A TRANCHÉ ────────────
 * `LV_OPA_COVER` (255) supprime le re-blit du fond sous chaque case.
 * MESURÉ le 2026-08-17, `nav ab 20` de chaque côté, n=40 :
 *     translucide 178 -> 321,8 ms de moyenne (293,8 / 369,9)
 *     OPAQUE  255 -> 299,9 ms de moyenne (267,0 / 343,2)   soit -21,9 ms (-6,8 %)
 *     translucide 127 -> 321,5 ms — IDENTIQUE à 178 : ce n'est pas la VALEUR
 *     d'opacité qui coûte, c'est le fait de n'être pas opaque. Le re-blit du
 *     fond est tout ou rien.
 * 🔴 VERDICT OWNER : TRANSLUCIDE. « C'était mieux avant. » Les 21,9 ms sont
 *    RENDUES délibérément — le Living PCB est l'identité du produit, et un
 *    dashboard qui l'efface de ses six cases n'est plus le même objet.
 *    Ce n'est donc PAS une optimisation en attente : c'est un arbitrage fermé,
 *    esthétique CONTRE latence, et l'esthétique a gagné avec son chiffre en
 *    face. `LV_OPA_70` (178, relu de lv_color.h:49) est l'état des lieux, monté
 *    de 40 % après le constat owner « les pistes claires mangeaient le texte
 *    blanc » (2026-08-16), et il RESTE le défaut.
 * ⚠️ Ne s'applique qu'aux conteneurs CRÉÉS APRÈS l'appel : il faut reconstruire
 *    la scène pour la voir. La console le fait, et le dit.
 */
void dn_widget_set_opa(uint8_t opa);
uint8_t dn_widget_opa(void);

/*
 * ════════════════════════════════════════════════════════════════════════════
 * dn4-6 / AC4 — LA GÉOMÉTRIE ET LA MISE EN FORME DEVIENNENT COMMUTABLES
 * ════════════════════════════════════════════════════════════════════════════
 *
 * 🔴 LA QUESTION QUE dn4-6 FERME N'EST PAS « FAUT-IL » MAIS « PAR QUELLE VOIE ».
 *    Quatre valeurs dans une case de 225 px, ça ne se décide pas au papier — et
 *    un A/B qui exigerait trois reflashs coûterait trois observations à l'owner
 *    pour un rendement qui baisse. Le patron est celui de `widget opa`,
 *    `widget piste` et `widget icone` : un `s_*` réglable, `build_scene()`, et
 *    LA CONSOLE LE DIT.
 * ⛔ ON NE RETIRE PAS UN `const` : les `#define` restent LES DÉFAUTS, ce bloc
 *    est un OVERRIDE (patron `s_nue_force[]`).
 * ⚠️ N'affecte que les cases CRÉÉES ENSUITE ⇒ l'appelant reconstruit la scène,
 *    et la reconstruction bloque le REPL ~350 ms — donc le TRANSPORT PC. La
 *    commande doit l'annoncer AVANT, pas le laisser découvrir.
 */

/*
 * LA MISE EN FORME DES GRANDEURS.
 *
 * ⛔ `EMPILE` EST ET RESTE LE DÉFAUT, tant que rien ne l'a battu SUR LA DALLE.
 *    C'est aussi la valeur 0 : un état statique naît empilé, jamais dans une
 *    disposition qu'aucun constat owner n'a retenue.
 *
 * ⚠️ `COTE` N'EST PAS ACQUISE : `dn_widget.c` porte depuis dn3-1 une estimation
 *    qui l'écartait (« 205 px pour 201 utiles »). Cette estimation est
 *    CONFRONTÉE À LA MESURE en dn4-6 (AC5, `widget largeur`) — ⛔ et un texte
 *    trop large ne se voit PAS comme une erreur, LVGL clippe au parent sans un
 *    mot. C'est pourquoi le chevauchement est DÉTECTÉ ET JOURNALISÉ ici.
 */
typedef enum {
    DN_DISPO_EMPILE = 0, /* N lignes de 1 — LE DÉFAUT (D6, dn3-1) */
    DN_DISPO_COTE,       /* 2 par ligne : (0,1) puis (2,3) */
    DN_DISPO_MIXTE,      /* ligne 1 = grandeurs 0+1 côte à côte, puis 1 par ligne */
    DN_DISPO_COUNT,
} dn_widget_dispo_t;

const char *dn_widget_dispo_nom(dn_widget_dispo_t d);

/*
 * L'EN-TÊTE. 🔴 CE RÉGLAGE EXISTE PARCE QUE LA TABLE DE D12 SUPPOSE
 * `val_y = 36` ET QUE LE CODE POSE 48 — personne ne l'avait écrit, et ça change
 * les verdicts (AC3). Le plancher réel de l'en-tête, relu du code :
 *
 *   NORMAL   icône `dn_font_28` @ y=8  -> boîte  8..43   <- le plancher
 *            titre `dn_font_14` @ y=22 -> boîte 22..40
 *            badge `dn_font_14` @ y=14 -> boîte 14..32
 *            ⇒ bas de l'en-tête = 43, et `val_y = 48` laisse 5 px.
 *
 *   COMPACT  les TROIS en `dn_font_14` @ y=8 -> boîtes 8..26
 *            ⇒ bas de l'en-tête = 26, `val_y = 36` laisse 10 px.
 *
 * ⚠️ CE QUE LA TABLE DE D12 NE DIT PAS, ET QU'IL FAUT DIRE AVANT L'A/B :
 *    compacter l'en-tête N'EST PAS « rétrécir l'icône ». À `val_y = 36`, la
 *    boîte du TITRE (22..40) déborde aussi de 4 px. Les trois éléments montent
 *    ensemble, ou rien ne monte.
 * 🔴 ET C'EST UNE DÉCISION OWNER, PAS UN CHOIX DE DEV : elle change les SIX
 *    cases, et l'icône est le SEUL endroit où le champ `couleur` du descripteur
 *    est EXERCÉ (dn3-1 l'y a posé pour qu'il ne soit pas un champ mort).
 */
typedef enum {
    DN_ENTETE_NORMAL = 0, /* icône 28 px — LE DÉFAUT, bas d'en-tête à 43 */
    DN_ENTETE_COMPACT,    /* les trois en 14 px — bas d'en-tête à 26 */
    DN_ENTETE_COUNT,
} dn_widget_entete_t;

const char *dn_widget_entete_nom(dn_widget_entete_t e);

typedef struct {
    int16_t val_y;             /* y de la 1ʳᵉ valeur (défaut W_VAL_Y = 48) */
    int16_t val_pas;           /* pas vertical entre lignes (défaut 40) */
    dn_widget_dispo_t dispo;   /* défaut EMPILE */
    dn_widget_entete_t entete; /* défaut NORMAL */
    const lv_font_t *font_val; /* police des valeurs (défaut `dn_font_28`) */
} dn_widget_geom_t;

void dn_widget_geom(dn_widget_geom_t *out);       /* l'état COURANT, relu */
void dn_widget_geom_defaut(dn_widget_geom_t *out); /* les `#define`, jamais récités */
void dn_widget_set_geom(const dn_widget_geom_t *g);

/* Le nombre de LIGNES qu'occupent `n` grandeurs dans une disposition donnée.
 * ⚠️ Ce n'est `n` qu'en EMPILÉ — et c'est LUI qui gouverne `y_bas`, donc la
 *    jauge et la secondaire. Exposé pour que la console CALCULE au lieu de
 *    réciter (le dépôt a payé « 156 px » en dur trois cents lignes plus loin). */
int dn_widget_lignes(dn_widget_dispo_t dispo, int n);

/*
 * ── AC5 : L'INSTRUMENT DE LARGEUR — LVGL, PAS UNE RÈGLE DE TROIS ─────────────
 *
 * Rend la largeur RÉELLE d'une chaîne dans la police RÉELLEMENT LIÉE, kerning
 * compris, par `lv_text_get_size()`. ⛔ Jamais un produit
 * `nb_caractères × largeur_moyenne` : c'est cette extrapolation-là
 * (« ~15,8 px/caractère ») qui a servi à écarter le côte à côte en dn3-1, et si
 * elle est fausse, c'est une décision qui reposait sur du vent.
 * ⚠️ NE PREND PAS le verrou LVGL — même contrat inversé que le reste du module.
 */
int dn_widget_largeur(const char *txt, const lv_font_t *font);

/* La largeur UTILE d'une case de `w` px : `w - 2 * W_PAD`. Relue, pas récitée. */
int dn_widget_largeur_utile(int w);

/* La gouttière minimale entre deux colonnes en côte à côte. */
int dn_widget_gouttiere(void);

/* Combien de chevauchements côte à côte ont été DÉTECTÉS depuis le dernier
 * `dn_widget_chevauchements_reset()`. ⚠️ Un chevauchement est journalisé ET
 * compté : LVGL clipperait sans un mot, et « rien n'a planté » n'est pas
 * « ça tient » (piège d'instrument n°13). */
uint32_t dn_widget_chevauchements(void);
void dn_widget_chevauchements_reset(void);

/*
 * ── LE DÉBORDEMENT VERTICAL — LE PENDANT EXACT DU CHEVAUCHEMENT ──────────────
 *
 * 🔴 CE COMPTEUR EXISTE PARCE QUE dn4-6 A FAILLI REFAIRE SON PROPRE DÉFAUT.
 *    La story borne la JAUGE et journalise l'abandon de la SECONDAIRE ; à 3 et
 *    4 grandeurs EMPILÉES dans une case de 156 px, ce sont les **VALEURS**
 *    elles-mêmes qui sortent : la 3ᵉ déborde de 7 px, la 4ᵉ est ENTIÈREMENT
 *    hors case. Et LVGL les clippe SANS UN MOT — donc la case affiche trois
 *    lignes là où le descripteur en demande quatre, sans que rien ne le dise.
 * ⛔ Le clamp de `GRANDEURS_MAX` ne voit PAS ce cas : il compte les grandeurs
 *    DEMANDÉES, pas celles qui TIENNENT. Deux gardes, deux questions.
 * ⚠️ La règle de priorité (VALEURS > jauge > secondaire) dit que les valeurs
 *    gagnent — elle ne dit pas qu'elles TIENNENT. Quand elles ne tiennent pas,
 *    il n'y a plus rien à sacrifier : ⇒ on les pose quand même (tronquer serait
 *    remplacer un défaut visible par un défaut muet) et **ON LE DIT**.
 */
uint32_t dn_widget_debordements(void);
void dn_widget_debordements_reset(void);

/* ── INSTRUMENT DE BISSECTION — voir le motif dans `dn_widget.c` ─────────────
 * `off` supprime `valeur_placer()` du chemin de MISE À JOUR : `dn_widget_maj`
 * redevient alors, ligne pour ligne, celui de `dn4-1`.
 * ⛔ Légitime UNIQUEMENT en `EMPILE` : en côte à côte la colonne droite resterait
 *    à la place de la valeur précédente. ⚠️ INSTRUMENT, pas réglage produit. */
void dn_widget_set_replacer(bool on);
bool dn_widget_replacer(void);

/*
 * ── L'UNITÉ QUI S'APPLIQUE — UNE SEULE DÉFINITION, ET C'EST UN CORRECTIF ─────
 *
 * 🔴 L'UNITÉ ÉTAIT CONCATÉNÉE À **TROIS** ENDROITS : `composer()` ici, le
 *    détail dans `dn_ui.c`, et la table de `widget` dans `dn_console.c`. Tant
 *    qu'il n'y avait qu'UNE unité par grandeur, les trois disaient la même
 *    chose et personne ne pouvait le voir. La bascule `Mb/s → Gb/s` (constat
 *    owner du 2026-08-19) l'a rendue visible **à la première mesure** : la
 *    console imprimait « 100,0 Mb/s » pour une valeur convertie en Gb/s —
 *    fausse **d'un facteur mille**, dans l'instrument qui sert à vérifier.
 * ⇒ La règle vit ICI et nulle part ailleurs. C'est exactement le motif de
 *   `dn_val_regime_couleur()`, dont la duplication avait rendu SIMULÉE
 *   indiscernable d'ABSENTE.
 * ⚠️ Rend `NULL` si la grandeur n'a pas d'unité — ⛔ pas `""` : l'appelant doit
 *    pouvoir distinguer « pas d'unité » de « une unité vide ».
 */
const char *dn_widget_unite(const dn_widget_desc_t *d,
                            const dn_widget_etat_t *e, int i);

#ifdef __cplusplus
}
#endif

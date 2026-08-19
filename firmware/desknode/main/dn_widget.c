/*
 * dn_widget — la brique de case du dashboard. Voir dn_widget.h pour le contrat,
 * le sens du verrou et ce que ce module n'est pas.
 *
 * ── LA MISE EN PAGE, ET POURQUOI ELLE EST CELLE-LÀ ───────────────────────────
 *
 * Une case fait 225 x 156. Le brief demande « toujours beaucoup d'espace ».
 *
 *   +-------------------------------+  0
 *   | [icone]  TITRE                |  8    icône 28 px, titre 14 px
 *   |                               |
 *   |  VALEUR       unité           |  48   valeur 28 px, unité 14 px
 *   |  [======= jauge =======]      |  94   (si indicateur, mono-grandeur)
 *   |  données secondaires          |  116  14 px
 *   +-------------------------------+  156
 *
 * Bi-grandeurs (D6, « AMBIANCE ») : les valeurs sont EMPILÉES, 40 px de pas.
 *
 *   ⚠️ « CÔTE À CÔTE A ÉTÉ ÉCARTÉ PAR L'ARITHMÉTIQUE » — ET L'ARITHMÉTIQUE
 *      ÉTAIT UNE ESTIMATION, QUE dn4-6 CONFRONTE À LA MESURE.
 *
 *      CE QUI ÉTAIT ÉCRIT ICI DEPUIS dn3-1, conservé mot pour mot :
 *        « À 28 px, "25,5 °C" mesure ~110 px et "52,4 %" ~95 px : 205 px pour
 *          201 px utiles (225 moins deux marges de 12). Ça ne rentre pas […]
 *          Le côte à côte n'aurait tenu qu'en descendant la police. »
 *
 *      🔴 CE N'ÉTAIT PAS UNE MESURE. C'était ~15,8 px par caractère, extrapolé
 *         — exactement le « produit nb_caractères × largeur_moyenne » que ce
 *         dépôt s'interdit ailleurs. Et une décision de conception REPOSAIT
 *         dessus.
 *      ⇒ `widget largeur` (dn4-6 / AC5) relit la largeur RÉELLE de
 *        `lv_text_get_size()` — la police RÉELLEMENT LIÉE, KERNING COMPRIS — et
 *        publie l'écart. ⛔ Le verdict est CE RELEVÉ-LÀ, pas ce paragraphe.
 *      ⚠️ Recalcul hors carte depuis les tables de `dn_font_28.c` (`adv_w` +
 *         classes de kerning) : « 25,5 °C » ~94 px et « 52,4 % » ~88 px, soit
 *         ~182 px — l'estimation serait haute de ~12 %, et le couple TIENDRAIT.
 *         ⛔ CE CHIFFRE N'EST PAS LA MESURE NON PLUS : il vient des mêmes tables
 *         que LVGL, mais pas de LVGL. Il dit seulement qu'il FALLAIT mesurer.
 *      ⚠️ Ce que ça ne change pas : à QUATRE grandeurs, les couples s'allongent
 *         (« 350 W » + « 3000 tr/min »), et c'est là que le mur se déplace.
 *         Le relevé couvre le PIRE CAS de chaque couple, pas un cas nominal.
 *      ⛔ EN REVANCHE « principale + secondaire » RESTE écarté, et pour une
 *      raison que la largeur ne touche pas : il HIÉRARCHISE. Or température et humidité sont deux mesures du même
 *      capteur, de même dignité ; en reléguer une en petit dirait le contraire.
 *   ⇒ EMPILÉES **PAR DÉFAUT**, et c'est le mécanisme GÉNÉRIQUE. ⚠️ dn4-6 :
 *     « N grandeurs = N lignes » n'est plus vrai qu'en `DN_DISPO_EMPILE` — le
 *     nombre de LIGNES se calcule par `dn_widget_lignes()`, et c'est LUI qui
 *     gouverne `y_bas`, donc la jauge et la secondaire.
 *
 * ── CE QUI FAIT LE RÉGIME VISIBLE (AC3) ──────────────────────────────────────
 * RÉELLE  : valeur blanche.
 * SIMULÉE : valeur AMBRE + un badge « SIMULÉ » en haut à droite.
 * ABSENTE : « -- » gris 0x9a9a9a.
 * ⚠️ DEUX signaux pour SIMULÉE, pas un. Une couleur seule serait ambiguë le
 *    jour où dn3-3 posera la palette de l'état Actif : l'ambre deviendrait « la
 *    couleur d'une métrique » et le mock redeviendrait indiscernable. Le MOT,
 *    lui, ne peut pas être confondu avec de la décoration.
 */

#include "dn_widget.h"

#include <stdio.h>
#include <string.h>

#include "esp_log.h"

#include "fonts/dn_font.h"

static const char *TAG = "dn_widget";

/* ── Géométrie interne de la case — CE SONT LES DÉFAUTS ───────────────────── */
#define W_PAD 12
#define W_TITRE_Y 14
#define W_ICONE_Y 8
#define W_VAL_Y 48
#define W_VAL_PAS 40
#define W_JAUGE_H 10
#define W_SEC_H 20
/* Gouttière minimale entre deux colonnes en côte à côte. En dessous, deux
 * nombres se lisent comme un seul — et « ça tient » deviendrait « ça touche ». */
#define W_GOUTTIERE 12
/* Largeur du sillon réservé à l'icône de la case, par taille de police. */
#define W_ICONE_AV_28 40
#define W_ICONE_AV_14 22

/*
 * ── dn4-6 / AC4 : L'OVERRIDE DE GÉOMÉTRIE ────────────────────────────────────
 * Les `#define` ci-dessus restent LES DÉFAUTS et ne bougent pas (convention du
 * dépôt : `k_*` const, `s_*` mutable, ⛔ on ne retire pas un `const`). Ce bloc
 * est l'override, et `dn_widget_geom_defaut()` RELIT les macros au lieu de les
 * réciter — c'est la seule façon que « le défaut » ne diverge pas du défaut.
 */
static dn_widget_geom_t s_geom = {
    .val_y = W_VAL_Y,
    .val_pas = W_VAL_PAS,
    .dispo = DN_DISPO_EMPILE,
    .entete = DN_ENTETE_NORMAL,
    .font_val = NULL, /* NULL = `dn_font_28` — résolu à l'usage, voir font_val() */
};

/* ⚠️ RÉSOLU À L'USAGE, PAS À L'INITIALISATION : `&dn_font_28` n'est pas une
 *    constante d'initialiseur portable ici, et surtout un `NULL` explicite rend
 *    lisible « personne n'a choisi » au lieu de figer un pointeur dans un
 *    statique que la console imprimerait comme un réglage. */
static const lv_font_t *font_val(void)
{
    return s_geom.font_val ? s_geom.font_val : &dn_font_28;
}

static const lv_font_t *font_entete(void)
{
    return s_geom.entete == DN_ENTETE_COMPACT ? &dn_font_14 : &dn_font_28;
}

/* Le y des trois éléments d'en-tête. En COMPACT ils montent ENSEMBLE : le titre
 * déborde de `val_y = 36` tout autant que l'icône (boîte 22..40), et ne monter
 * que l'icône aurait laissé le défaut à moitié corrigé — sans le dire. */
static int entete_y_icone(void) { return W_ICONE_Y; }
static int entete_y_titre(void)
{
    return s_geom.entete == DN_ENTETE_COMPACT ? W_ICONE_Y : W_TITRE_Y + 8;
}
static int entete_y_badge(void)
{
    return s_geom.entete == DN_ENTETE_COMPACT ? W_ICONE_Y : W_TITRE_Y;
}

/* Les deux compteurs de « ça ne tient pas » — voir `dn_widget.h`.
 * ⚠️ DEUX compteurs et non un : un chevauchement HORIZONTAL et un débordement
 *    VERTICAL ne se corrigent pas par le même levier (la largeur d'une chaîne
 *    contre la hauteur de la case), et les additionner rendrait le diagnostic
 *    ambigu au moment précis où on arbitre entre trois voies. */
static uint32_t s_chevauchements;
static uint32_t s_debordements;

uint32_t dn_widget_chevauchements(void) { return s_chevauchements; }
void dn_widget_chevauchements_reset(void) { s_chevauchements = 0; }
uint32_t dn_widget_debordements(void) { return s_debordements; }
void dn_widget_debordements_reset(void) { s_debordements = 0; }

int dn_widget_gouttiere(void) { return W_GOUTTIERE; }
int dn_widget_largeur_utile(int w) { return w - 2 * W_PAD; }

const char *dn_widget_dispo_nom(dn_widget_dispo_t d)
{
    switch (d) {
    case DN_DISPO_EMPILE:
        return "EMPILE";
    case DN_DISPO_COTE:
        return "COTE-A-COTE";
    case DN_DISPO_MIXTE:
        return "MIXTE";
    default:
        return "?";
    }
}

const char *dn_widget_entete_nom(dn_widget_entete_t e)
{
    switch (e) {
    case DN_ENTETE_NORMAL:
        return "NORMAL (icone 28, bas d'en-tete 43)";
    case DN_ENTETE_COMPACT:
        return "COMPACT (les trois en 14, bas d'en-tete 26)";
    default:
        return "?";
    }
}

void dn_widget_geom(dn_widget_geom_t *out)
{
    if (out) {
        *out = s_geom;
        out->font_val = font_val(); /* ⛔ jamais NULL vers l'extérieur */
    }
}

void dn_widget_geom_defaut(dn_widget_geom_t *out)
{
    if (out) {
        out->val_y = W_VAL_Y;
        out->val_pas = W_VAL_PAS;
        out->dispo = DN_DISPO_EMPILE;
        out->entete = DN_ENTETE_NORMAL;
        out->font_val = &dn_font_28;
    }
}

void dn_widget_set_geom(const dn_widget_geom_t *g)
{
    if (g) {
        s_geom = *g;
    }
}

/*
 * ── LE PLACEMENT D'UNE GRANDEUR — UNE SEULE DÉFINITION ───────────────────────
 *
 * Rend la LIGNE et la COLONNE de la grandeur `i`, et combien de colonnes cette
 * ligne-là porte. ⚠️ Le nombre de colonnes de la DERNIÈRE ligne n'est pas
 * toujours 2 (n impair) : une grandeur seule sur sa ligne prend toute la
 * largeur, et la traiter en demi-colonne l'écrêterait sans raison.
 */
static void place(dn_widget_dispo_t dispo, int n, int i, int *ligne, int *col,
                  int *cols)
{
    int l = i, c = 0, k = 1;
    switch (dispo) {
    case DN_DISPO_COTE:
        l = i / 2;
        c = i % 2;
        k = (n - 2 * l) >= 2 ? 2 : 1;
        break;
    case DN_DISPO_MIXTE:
        if (i < 2) {
            l = 0;
            c = i;
            k = n >= 2 ? 2 : 1;
        } else {
            l = i - 1;
            c = 0;
            k = 1;
        }
        break;
    case DN_DISPO_EMPILE:
    default:
        break;
    }
    if (ligne) {
        *ligne = l;
    }
    if (col) {
        *col = c;
    }
    if (cols) {
        *cols = k;
    }
}

int dn_widget_lignes(dn_widget_dispo_t dispo, int n)
{
    if (n < 1) {
        return 0;
    }
    switch (dispo) {
    case DN_DISPO_COTE:
        return (n + 1) / 2;
    case DN_DISPO_MIXTE:
        return n <= 2 ? 1 : n - 1;
    case DN_DISPO_EMPILE:
    default:
        return n;
    }
}

int dn_widget_largeur(const char *txt, const lv_font_t *font)
{
    if (!txt || !font) {
        return 0;
    }
    lv_point_t p;
    /* ⚠️ `LV_COORD_MAX` en `max_width` : sans ça LVGL casserait les lignes et
     *    rendrait la largeur du CONTENEUR, pas celle du TEXTE — l'instrument
     *    mesurerait alors ce qu'on lui impose au lieu de ce qu'il coûte. */
    lv_text_get_size(&p, txt, font, 0, 0, LV_COORD_MAX, LV_TEXT_FLAG_NONE);
    return (int)p.x;
}

/* ── Couleurs des régimes ─────────────────────────────────────────────────── */
#define W_COL_ABSENTE 0x9a9a9a
#define W_COL_REELLE 0xffffff
#define W_COL_SIMULEE 0xffb020
#define W_COL_TITRE 0xa0d8ff
#define W_COL_BORDURE 0x50c0ff
#define W_COL_SEC 0xc0d8e8

/* Opacité des conteneurs — A/B d'AC9. LV_OPA_70 = 178 (relu de
 * lv_color.h:49 : 70 % de 255 fait 178,5 et LVGL tronque). C'est l'état des lieux,
 * monté de 40 % le 2026-08-16 après le constat owner « les pistes claires
 * mangeaient le texte blanc ». */
/*
 * ── LA PISTE DE LA JAUGE — RÉGLABLE À CHAUD (constat owner, 2026-08-18) ──────
 *
 * 🔴 CONSTAT OWNER EN SÉANCE CARTE : « la barre de vide apparaît en vert,
 *    pourrait être plus claire pour faire ressortir la violette ».
 *    ⚠️ Le code ne posait PAS de vert : `0x203040` est un bleu-gris FONCÉ. Ce
 *       qui se voit est très probablement le PCB vert du fond qui joue par
 *       contraste simultané autour d'une piste sombre. ⛔ On ne « corrige » donc
 *       pas une couleur qu'on n'a pas posée : on ÉCLAIRCIT la piste pour que le
 *       violet de l'indicateur tranche, et on laisse l'œil arbitrer.
 *
 * ⚠️ RÉGLABLE À CHAUD, ET C'EST LE PATRON DU FICHIER (`widget opa`,
 *    `widget voile`, `widget icone`) : « un A/B qui exigerait trois reflashs
 *    coûterait trois observations à l'owner pour un rendement qui baisse ».
 * ⚠️ dn3-3 refait l'identité visuelle et rejouera cet arbitrage — ce défaut-ci
 *    est corrigé sur demande owner explicite, ⛔ ce n'est PAS la passe de
 *    palette, qui reste à dn3-3.
 */
#define W_COL_PISTE_DEFAUT 0x5a5f6a
static uint32_t s_piste = W_COL_PISTE_DEFAUT;

void dn_widget_set_piste(uint32_t rgb) { s_piste = rgb & 0xFFFFFF; }
uint32_t dn_widget_piste(void) { return s_piste; }

static uint8_t s_opa = LV_OPA_70;
/*
 * ── W7 TRANCHÉ PAR LA MESURE : LE GROUPAGE EST LE DÉFAUT (AC8) ───────────────
 *
 * 🔴 CES CHIFFRES SONT LES REJOUÉS. La première campagne (2026-08-17,
 *    firmware e2cb5ba+) a été JETÉE : un second écrivain — le tick 1 Hz du mock
 *    reposant `ABSENTE` après chaque poussée — gonflait le dénominateur de
 *    cycles. Les valeurs pré-rejeu (2,08 f/cyc · 10 591 px · « −39 à −64 % » ·
 *    aire ×3,4) survivaient encore ICI le 2026-08-18, dans la SOURCE que le dev
 *    lit, alors que le ledger avait été corrigé. §15.5 de `hardware/` fait foi.
 *
 * MESURÉ le 2026-08-18, firmware `9699adb`, 25 poussées par relevé espacées de
 * 120 ms, mock COUPÉ, `flush reset` avant chacun, `timeouts` = `noops` = 0 :
 *
 *   cas                                  fine (N zones)        groupée (1 zone)
 *   ------------------------------------------------------------------------
 *   widget MONO sans jauge  (CPU)    2,00 f/cyc · 10 749 px   1,00 · 35 100 px
 *   widget MONO avec jauge  (VENT)   3,12 f/cyc · 16 577 px   1,00 · 35 100 px
 *   widget BI-grandeurs     (AMB)    2,12 f/cyc · 17 536 px   1,00 · 35 100 px
 *   case NUE (témoin)       (GPU)    1,00 f/cyc ·  3 321 px   1,00 ·  3 356 px
 *
 * Temps par cycle = flushes x (copie + attente) :
 *   MONO sans jauge  30,0 ms -> 16,1 ms   (-46 %)
 *   MONO avec jauge  55,5 ms -> 15,8 ms   (-71 %)   [passe 2 : 53,6 -> 17,2]
 *   BI-grandeurs     31,0 ms -> 17,6 ms   (-43 %)
 *
 * 🔴 LE REJEU CHANGE LE CHIFFRE-TITRE DANS LE SENS QUI DÉRANGE : il n'était pas
 *    trop optimiste, il était trop TIMIDE (−68 à −71 % contre −64 % publiés).
 *    ⚠️ L'AIRE, elle, était JUSTE à 0,02 % près — le défaut d'instrument
 *    touchait le compte de flushes et de cycles, jamais la surface. C'est ce
 *    qu'un relevé publiant ses grandeurs SÉPARÉMENT permet de dire.
 *
 * 🔴 LA PRÉDICTION EST CONFIRMÉE DANS SON SENS, DÉMENTIE DANS SON AMPLEUR.
 *    La story prédisait que l'attente domine la copie « d'un facteur ~50 ».
 *    MESURÉ : copie groupée 2,9-3,6 ms contre attente 13-15 ms, soit un facteur
 *    ~5, pas ~50. Le groupage gagne quand même — parce qu'il SUPPRIME UN FLUSH
 *    ENTIER (~16 ms) pour 2,7 ms de copie en plus, soit un retour de ~6 pour 1.
 *    Écrit ici parce qu'une prédiction démentie est plus instructive qu'une
 *    prédiction tenue, et que le dépôt a déjà vu un facteur 10 d'écart (T9).
 *
 * 🔴 ET IL GAGNE EN TEMPS MURAL TOUT EN PERDANT EN CPU — dn3-2, §16.2 : le
 *    groupage coûte **+2,52 points de CPU**, parce qu'il copie beaucoup plus de
 *    pixels pour attendre une trame de moins. « Le groupage gagne » sans cette
 *    qualification est une demi-vérité : il gagne du TEMPS, il dépense du CPU.
 *
 * ⚠️ ET CE QUE LE GROUPAGE NE FAIT PAS : il n'économise AUCUN pixel, il en
 *    MULTIPLIE le nombre par 2,0 à 3,3 selon la case (10 749 -> 35 100 pour la
 *    mono sans jauge). Ce n'est pas une optimisation d'aire, c'est un échange —
 *    beaucoup de pixels contre une attente de trame. Le jour où la copie
 *    deviendra le goulot (plus de cases vivantes, ou une copie plus lente),
 *    l'arbitrage devra être REJOUÉ : c'est pour ça que la branche fine reste
 *    vivante et rejouable sans reflasher.
 * ⚠️ LE TÉMOIN NÉGATIF EST INTACT : la case NUE mesure quasiment pareil dans
 *    les deux branches (3 321 -> 3 356 px, elle ne traverse pas le modèle).
 *    ⚠️ dn3-2 : il n'y a plus de case nue PERMANENTE — les six portent le
 *       modèle. Le témoin se PROVOQUE par `widget nue <idx> on`, à chaud, pour
 *       que la comparaison reste DANS LE MÊME FIRMWARE. C'est ce qui prouve
 *    que la différence vient bien du groupage et non d'un effet de bord.
 */
static bool s_groupage = true;

const char *dn_val_regime_nom(dn_val_regime_t r)
{
    switch (r) {
    case DN_VAL_ABSENTE:
        return "ABSENTE";
    case DN_VAL_REELLE:
        return "RÉELLE";
    case DN_VAL_SIMULEE:
        return "SIMULÉE";
    default:
        return "?";
    }
}

void dn_widget_set_groupage(bool on) { s_groupage = on; }
bool dn_widget_groupage(void) { return s_groupage; }
void dn_widget_set_opa(uint8_t opa) { s_opa = opa; }
uint8_t dn_widget_opa(void) { return s_opa; }

/* Le fond commun aux conteneurs : aplat sombre + liseré. Un seul endroit, pour
 * que l'A/B d'opacité d'AC9 ne puisse pas oublier une moitié de l'écran. */
static void aplat(lv_obj_t *o)
{
    lv_obj_set_style_bg_color(o, lv_color_black(), 0);
    lv_obj_set_style_bg_opa(o, s_opa, 0);
    lv_obj_set_style_border_color(o, lv_color_hex(W_COL_BORDURE), 0);
    lv_obj_set_style_border_width(o, 1, 0);
    lv_obj_set_style_border_opa(o, LV_OPA_60, 0);
}

lv_obj_t *dn_widget_zone_creer(lv_obj_t *parent, int x, int y, int w, int h,
                               lv_event_cb_t cb, void *user)
{
    lv_obj_t *z = lv_obj_create(parent);
    lv_obj_remove_style_all(z);
    lv_obj_set_pos(z, x, y);
    lv_obj_set_size(z, w, h);
    /* LES DEUX DRAPEAUX D'AC4 — voir dn_widget.h. Ils ne vivent qu'ici. */
    lv_obj_clear_flag(z, LV_OBJ_FLAG_SCROLLABLE);
    aplat(z);
    if (cb) {
        lv_obj_add_flag(z, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_event_cb(z, cb, LV_EVENT_CLICKED, user);
    } else {
        /*
         * 🔴 CLICKABLE EST CONDITIONNÉ AU CALLBACK (revue du 2026-08-18).
         *    Il était posé INCONDITIONNELLEMENT, et une zone cliquable SANS
         *    handler ni `EVENT_BUBBLE` devient `act_obj`, reçoit le CLICKED, et
         *    l'AVALE : le tap ne remonte nulle part, `s_taps` ne bouge pas, et
         *    rien ne le signale.
         *    Vu sur la démo d'AC1 (`widget demo`, cb = NULL) : posée en
         *    (120, 240) sur 225 x 156, elle recouvre une partie des cases RAM et
         *    RÉSEAU — une campagne `touch trace` ou `nav ab` lancée démo armée
         *    mesurait donc une propriété AC4 FAUSSE, sans un mot.
         *    ⚠️ Ne PAS « corriger » en ajoutant EVENT_BUBBLE : un widget sans
         *    callback n'a pas de destination, et le faire remonter au parent
         *    ferait ouvrir le détail d'une case qu'il ne fait que recouvrir.
         */
        lv_obj_clear_flag(z, LV_OBJ_FLAG_CLICKABLE);
    }
    return z;
}

lv_obj_t *dn_widget_panneau(lv_obj_t *parent, int x, int y, int w, int h)
{
    lv_obj_t *p = lv_obj_create(parent);
    lv_obj_remove_style_all(p);
    lv_obj_set_pos(p, x, y);
    lv_obj_set_size(p, w, h);
    lv_obj_clear_flag(p, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_clear_flag(p, LV_OBJ_FLAG_CLICKABLE);
    aplat(p);
    return p;
}

lv_obj_t *dn_widget_texte(lv_obj_t *parent, const char *s, const lv_font_t *font,
                          lv_color_t couleur, int x, int y)
{
    lv_obj_t *l = lv_label_create(parent);
    lv_obj_set_style_text_font(l, font, 0);
    lv_obj_set_style_text_color(l, couleur, 0);
    lv_obj_set_style_bg_opa(l, LV_OPA_TRANSP, 0);
    lv_label_set_text(l, s);
    lv_obj_set_pos(l, x, y);
    lv_obj_clear_flag(l, LV_OBJ_FLAG_CLICKABLE);
    return l;
}

lv_color_t dn_val_regime_couleur(dn_val_regime_t r)
{
    switch (r) {
    case DN_VAL_REELLE:
        return lv_color_hex(W_COL_REELLE);
    case DN_VAL_SIMULEE:
        return lv_color_hex(W_COL_SIMULEE);
    default:
        return lv_color_hex(W_COL_ABSENTE);
    }
}

/*
 * Le texte d'une grandeur : [icône ][préfixe ]valeur[ unité].
 *
 * ⛔ Une valeur ABSENTE ne porte JAMAIS son unité (« -- % » suggérerait qu'on
 *    sait de quoi on parle) — ✅ mais elle GARDE son préfixe : « c.max -- » dit
 *    QUELLE grandeur manque, et taire le préfixe cacherait l'existence même de
 *    la grandeur, ce que W10 interdit explicitement.
 */
static void composer(const dn_widget_desc_t *d, const dn_widget_etat_t *e, int i,
                     char *out, size_t n)
{
    const char *ic = d->grandeurs[i].icone;
    const char *px = d->grandeurs[i].prefixe;
    if (!e || e->regime == DN_VAL_ABSENTE || e->txt[i][0] == '\0') {
        snprintf(out, n, "%s%s%s%s--", ic ? ic : "", ic ? " " : "",
                 px ? px : "", px ? " " : "");
        return;
    }
    const char *u = d->grandeurs[i].unite;
    snprintf(out, n, "%s%s%s%s%s%s%s", ic ? ic : "", ic ? " " : "",
             px ? px : "", px ? " " : "", e->txt[i], u ? " " : "", u ? u : "");
}

/*
 * ── POSER UNE VALEUR À SA PLACE, ET DÉTECTER LE CHEVAUCHEMENT ────────────────
 *
 * 🔴 CETTE FONCTION EXISTE POUR UNE RAISON PRÉCISE : en côte à côte, un texte
 *    trop large NE SE VOIT PAS comme une erreur. LVGL clippe au parent SANS UN
 *    MOT (piège d'instrument n°13 du dépôt). « Rien n'a planté » n'est donc pas
 *    « ça tient » — il faut MESURER et DIRE.
 *
 * Colonne 0 : calée à gauche, à `W_PAD`.
 * Colonne 1 : calée à DROITE, à `w - W_PAD - largeur`. ⚠️ Pas une demi-case
 *   fixe : un partage à 50/50 écrêterait « 100,0 % » (mesuré à ~103 px pour
 *   100 px de demi-largeur) alors que le couple entier tient. Le calage à droite
 *   rend la CONTRAINTE RÉELLE — « les deux plus la gouttière tiennent-ils dans
 *   les 201 px utiles ? » — au lieu d'en fabriquer une plus dure.
 */
static void valeur_placer(lv_obj_t *lbl, int i, int n, int w, int fin_gauche,
                          const dn_widget_desc_t *desc, int *fin_gauche_out)
{
    int ligne = 0, col = 0, cols = 1;
    place(s_geom.dispo, n, i, &ligne, &col, &cols);
    int y = s_geom.val_y + ligne * s_geom.val_pas;

    if (cols < 2 || col == 0) {
        lv_obj_set_pos(lbl, W_PAD, y);
        if (fin_gauche_out) {
            *fin_gauche_out = W_PAD + dn_widget_largeur(lv_label_get_text(lbl),
                                                        font_val());
        }
        return;
    }

    int lw = dn_widget_largeur(lv_label_get_text(lbl), font_val());
    int x = w - W_PAD - lw;
    if (x < fin_gauche + W_GOUTTIERE) {
        s_chevauchements++;
        /* ⚠️ LE MESSAGE NOMME LES DEUX COLONNES SEPAREMENT — il disait
         *    « "<texte DROIT>" finit a <fin de la colonne GAUCHE> », ce qui
         *    attribuait au texte de droite une coordonnee qui est celle de
         *    gauche. Un log qui melange ses deux termes envoie chercher le
         *    defaut du mauvais cote. */
        ESP_LOGW(TAG,
                 "« %s » grandeur %d : CHEVAUCHEMENT cote a cote — la colonne "
                 "GAUCHE finit a %d px, et « %s » (%d px, calee a DROITE) "
                 "commencerait a %d px : il manque %d px (gouttiere %d, utile "
                 "%d px). LVGL clipperait SANS un mot.",
                 desc && desc->titre ? desc->titre : "?", i, fin_gauche,
                 lv_label_get_text(lbl), lw, x, fin_gauche + W_GOUTTIERE - x,
                 W_GOUTTIERE, dn_widget_largeur_utile(w));
        /* ⛔ On pose QUAND MÊME, à la place demandée : masquer la valeur ou la
         *    tronquer serait remplacer un défaut visible par un défaut muet.
         *    Le log et le compteur sont l'instrument ; l'œil de l'owner tranche. */
    }
    lv_obj_set_pos(lbl, x, y);
}

void dn_widget_creer(lv_obj_t *parent, int x, int y, int w, int h,
                     const dn_widget_desc_t *desc, const dn_widget_etat_t *etat,
                     lv_event_cb_t cb, void *user, dn_widget_t *out)
{
    memset(out, 0, sizeof(*out));
    out->racine = dn_widget_zone_creer(parent, x, y, w, h, cb, user);

    out->w = (int16_t)w;

    int tx = W_PAD;
    if (desc->icone) {
        /* L'icône porte la COULEUR D'ACCENT du descripteur : c'est le seul
         * endroit où dn3-1 EXERCE le champ `couleur`, pour qu'il ne soit pas un
         * champ mort que dn3-3 découvrirait non branché.
         * ⚠️ dn4-6 / AC3 : en en-tête COMPACT elle descend en `dn_font_14`, et
         *    c'est LA décision owner de l'A/B — pas un réglage de dev. */
        dn_widget_texte(out->racine, desc->icone, font_entete(),
                        lv_color_hex(desc->couleur), tx, entete_y_icone());
        tx += (s_geom.entete == DN_ENTETE_COMPACT) ? W_ICONE_AV_14 : W_ICONE_AV_28;
    }
    dn_widget_texte(out->racine, desc->titre, &dn_font_14,
                    lv_color_hex(W_COL_TITRE), tx, entete_y_titre());

    /* Le badge de régime — CRÉÉ TOUJOURS, masqué quand il ne s'applique pas.
     * Le créer à la demande obligerait `dn_widget_maj` à construire des objets
     * LVGL, donc à allouer, sous le verrou et depuis une tâche de source. Un
     * `lv_obj_add_flag(HIDDEN)` ne peut pas échouer ; un `lv_label_create` si. */
    out->badge = dn_widget_texte(out->racine, "SIMULÉ", &dn_font_14,
                                 lv_color_hex(W_COL_SIMULEE), w - 66,
                                 entete_y_badge());
    lv_obj_add_flag(out->badge, LV_OBJ_FLAG_HIDDEN);

    /* 🔴 L'ÉCRÊTAGE DU NOMBRE DE GRANDEURS EST JOURNALISÉ — correctif de revue
     * 2026-08-18. Il était MUET des deux côtés, dix lignes au-dessus du correctif
     * W5 qui vient précisément de rendre AUDIBLE l'abandon de la ligne secondaire.
     * Une grandeur demandée et jamais dessinée disparaissait sans un mot : c'est
     * la classe de défaut que cette story traque, laissée en place à trois lignes
     * de sa correction.
     * ⚠️ ET C'EST UN PRÉREQUIS DE dn4-6, qui va élargir `DN_WIDGET_GRANDEURS_MAX` :
     *    sans ce log, un descripteur à n = 3 sur un firmware encore à 2 perdrait
     *    sa troisième grandeur en silence. */
    int n = desc->n_grandeurs;
    if (n < 1) {
        ESP_LOGW(TAG, "« %s » : %d grandeur(s) demandee(s) — plancher a 1",
                 desc->titre ? desc->titre : "?", desc->n_grandeurs);
        n = 1;
    }
    if (n > DN_WIDGET_GRANDEURS_MAX) {
        ESP_LOGW(TAG, "« %s » : %d grandeurs demandees, %d posees — %d PERDUE(S)",
                 desc->titre ? desc->titre : "?", desc->n_grandeurs,
                 DN_WIDGET_GRANDEURS_MAX, desc->n_grandeurs - DN_WIDGET_GRANDEURS_MAX);
        n = DN_WIDGET_GRANDEURS_MAX;
    }
    out->n = (uint8_t)n;

    char buf[DN_WIDGET_TXT_MAX + 32];
    int fin_gauche = W_PAD;
    int lh_val = (int)lv_font_get_line_height(font_val());
    int hors = 0, dernier_bas = 0;
    for (int i = 0; i < n; i++) {
        composer(desc, etat, i, buf, sizeof(buf));
        out->valeur[i] = dn_widget_texte(
            out->racine, buf, font_val(),
            dn_val_regime_couleur(etat ? etat->regime : DN_VAL_ABSENTE), W_PAD,
            s_geom.val_y);
        valeur_placer(out->valeur[i], i, n, w, fin_gauche, desc, &fin_gauche);
        /* 🔴 LA VALEUR QUI NE TIENT PAS EN HAUTEUR — voir `dn_widget.h`.
         *    Le bas de la BOÎTE, ⛔ pas le `y` posé : un texte posé à 128 dans
         *    une case de 156 « a l'air » dedans et déborde de 7 px. */
        int ligne = 0;
        place(s_geom.dispo, n, i, &ligne, NULL, NULL);
        int bas = s_geom.val_y + ligne * s_geom.val_pas + lh_val;
        if (bas > h) {
            hors++;
            dernier_bas = bas;
        }
    }
    if (hors > 0) {
        s_debordements += (uint32_t)hors;
        ESP_LOGW(TAG,
                 "« %s » : %d valeur(s) sur %d DEBORDENT la case — bas %d > h=%d "
                 "(%d ligne(s) x pas %d, police lh %d, val_y %d, disposition %s). "
                 "LVGL les CLIPPE sans un mot : la case en montre moins qu'elle "
                 "n'en declare.",
                 desc->titre ? desc->titre : "?", hors, n, dernier_bas, h,
                 dn_widget_lignes(s_geom.dispo, n), s_geom.val_pas, lh_val,
                 s_geom.val_y, dn_widget_dispo_nom(s_geom.dispo));
    }

    /* 🔴 `y_bas` SE CALCULE SUR LES LIGNES, PAS SUR LES GRANDEURS. En côte à
     *    côte quatre grandeurs tiennent en DEUX lignes — et confondre les deux
     *    ferait abandonner une jauge qui a la place, ou en poser une qui ne l'a
     *    pas. C'est le même nombre qui gouverne la jauge et la secondaire. */
    int n_lignes = dn_widget_lignes(s_geom.dispo, n);
    int y_bas = s_geom.val_y + n_lignes * s_geom.val_pas;
    /*
     * 🔴 dn4-1 / W5 : LE `&& n == 1` A ÉTÉ RETIRÉ. Il faisait disparaître la
     *    jauge d'un descripteur bi-grandeurs SANS ERREUR NI LOG, alors que
     *    `dn_widget.h` documentait `indicateur` sans aucune restriction — le
     *    ledger le portait 🟠 latent depuis la revue dn3-1, avec la note
     *    « dn3-2 est la story qui instancie six descripteurs, c'est là que ça
     *    se paiera ». Ça ne s'est pas payé en dn3-2 parce qu'aucune case
     *    bi-grandeurs n'avait de jauge ; D10 change ça.
     *    ⚠️ La conséquence géométrique est traitée juste après, et JOURNALISÉE :
     *       corriger ceci SEUL aurait déplacé la panne silencieuse de la jauge
     *       vers la ligne secondaire.
     */
    /*
     * 🔴 dn4-6 / AC2 — LA JAUGE EST BORNÉE. 3ᵉ OCCURRENCE DE LA MÊME FAMILLE.
     *
     *    dn4-1 avait retiré le `&& n == 1` (la jauge d'un descripteur
     *    bi-grandeurs disparaissait sans un mot) PUIS rendu audible l'abandon de
     *    la ligne secondaire. Il restait la jauge elle-même : `lv_obj_set_pos`
     *    la posait à `y_bas + 6` SANS AUCUN TEST contre `h`. À n ≤ 2 aucune case
     *    ne pouvait sortir ; à 3 et 4 grandeurs EMPILÉES, `y_bas` vaut 168 puis
     *    208 et la jauge part HORS CASE — clippée en silence par LVGL.
     *    ⇒ Le test est écrit AVANT d'élargir `GRANDEURS_MAX` (l'ordre est un
     *      livrable, AC2), et l'abandon est JOURNALISÉ comme celui de la
     *      secondaire — la règle de priorité de `dn_widget.h` est appliquée ici,
     *      pas subie ailleurs.
     * ⚠️ La jauge consomme `W_JAUGE_H + 10` = 20 px : 6 px de garde au-dessus,
     *    `W_JAUGE_H` de barre, 4 px en dessous. Le test porte sur le BAS RÉEL de
     *    la barre (`y_bas + 6 + W_JAUGE_H`), ⛔ pas sur les 20 px de l'avance —
     *    deux chiffres publiés par dn4-1 étaient faux de +6 sur cette ligne.
     */
    bool jauge_place = (y_bas + 6 + W_JAUGE_H) <= h;
    if (desc->indicateur && !jauge_place) {
        ESP_LOGW(TAG,
                 "« %s » : pas de place pour la JAUGE (y_bas=%d + 6 + %d > h=%d) "
                 "— %d grandeur(s) sur %d ligne(s), disposition %s. La jauge est "
                 "ABANDONNEE (contrat dn_widget.h / W5 : valeurs > jauge > "
                 "secondaire).",
                 desc->titre ? desc->titre : "?", y_bas, W_JAUGE_H, h, n,
                 n_lignes, dn_widget_dispo_nom(s_geom.dispo));
    }
    if (desc->indicateur && jauge_place) {
        /*
         * 🔴 `lv_bar` EST CLIQUABLE PAR DÉFAUT — `lv_bar.c:341` le CONSERVE là
         *    où `lv_label.c:762` le retire. Sans la ligne ci-dessous, la jauge
         *    VOLE le tap sur son propre rectangle et « toute la case est la zone
         *    tactile » — prouvée à 4 px du bord en dn1-4 — devient FAUSSE EN
         *    SILENCE, sur la seule bande où l'utilisateur a le plus de chances
         *    de poser le doigt. Et ça ne se voit PAS au compteur de taps si on
         *    vise le centre de la case : la preuve d'AC4 exige de viser LA
         *    JAUGE.
         *    Idem pour SCROLLABLE : `lv_bar` le retire déjà, on le refait pour
         *    que la garantie soit locale.
         */
        out->jauge = lv_bar_create(out->racine);
        lv_obj_clear_flag(out->jauge, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_clear_flag(out->jauge, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_set_pos(out->jauge, W_PAD, y_bas + 6);
        lv_obj_set_size(out->jauge, w - 2 * W_PAD, W_JAUGE_H);
        lv_bar_set_range(out->jauge, desc->ind_min, desc->ind_max);
        lv_obj_set_style_bg_color(out->jauge, lv_color_hex(s_piste), 0);
        lv_obj_set_style_bg_opa(out->jauge, LV_OPA_COVER, 0);
        lv_obj_set_style_bg_color(out->jauge, lv_color_hex(desc->couleur),
                                  LV_PART_INDICATOR);
        lv_obj_set_style_bg_opa(out->jauge, LV_OPA_COVER, LV_PART_INDICATOR);
        lv_bar_set_value(out->jauge, etat ? etat->brut[0] : desc->ind_min,
                         LV_ANIM_OFF);
        y_bas += W_JAUGE_H + 10;
    }

    if (y_bas + W_SEC_H <= h) {
        out->sec = dn_widget_texte(out->racine,
                                   (etat && etat->secondaire[0]) ? etat->secondaire
                                                                 : "",
                                   &dn_font_14, lv_color_hex(W_COL_SEC), W_PAD,
                                   y_bas + 2);
    } else {
        /*
         * 🔴 dn4-1 / W5 — L'ABANDON DE LA SECONDAIRE NE PEUT PLUS ÊTRE
         *    SILENCIEUX. C'est le PIÈGE que le correctif de la jauge arme :
         *    à n = 2 AVEC jauge, y_bas vaut 148 et 148 + 20 = 168 > 156, donc
         *    `out->sec` reste NULL et `dn_widget_maj` saute le bloc — exactement
         *    la même panne muette, un cran plus loin, et pas plus visible.
         *    La règle de priorité est écrite dans `dn_widget.h` (la jauge gagne,
         *    parce qu'elle est demandée par un champ explicite du descripteur) ;
         *    ici on la REND AUDIBLE. Un descripteur qui perd sa ligne secondaire
         *    doit le dire à qui lit les logs, pas se taire.
         * ⚠️ Ce log est rare PAR CONSTRUCTION : aucune des six cases de dn4-1 ne
         *    demande jauge + secondaire sur deux grandeurs. S'il apparaît en
         *    rafale, c'est qu'un descripteur a changé — et c'est le signal.
         */
        ESP_LOGW(TAG,
                 "« %s » : pas de place pour la ligne secondaire "
                 "(y_bas=%d + %d > h=%d) — %d grandeur(s) sur %d ligne(s), "
                 "disposition %s%s. La jauge est prioritaire "
                 "(contrat dn_widget.h / W5).",
                 desc->titre ? desc->titre : "?", y_bas, W_SEC_H, h, n, n_lignes,
                 dn_widget_dispo_nom(s_geom.dispo),
                 (desc->indicateur && jauge_place) ? " + jauge" : "");
    }

    /* Poser l'état une fois de plus : c'est LUI qui décide de la visibilité du
     * badge et de la couleur, et le refaire ici garantit qu'une case construite
     * et une case mise à jour passent EXACTEMENT par le même code. Deux chemins
     * de rendu pour un même état, c'est deux endroits où ils divergent. */
    dn_widget_maj(desc, etat, out);
}

void dn_widget_maj(const dn_widget_desc_t *desc, const dn_widget_etat_t *etat,
                   dn_widget_t *w)
{
    if (!w || !w->racine) {
        /* Modèle REBUILD en vue détail : le dashboard n'existe pas. L'état est
         * conservé par l'appelant et sera posé à la (re)construction. */
        return;
    }

    lv_display_t *disp = lv_display_get_default();
    bool grouper = s_groupage && disp != NULL;
    if (grouper) {
        /* ⚠️ De cette ligne jusqu'au rétablissement, AUCUNE invalidation n'est
         *    enregistrée. On ne fait donc RIEN d'autre que d'écrire les enfants
         *    de CE widget — et surtout on ne relâche pas le verrou (voir le
         *    contrat dans dn_widget.h). */
        lv_display_enable_invalidation(disp, false);
    }

    dn_val_regime_t r = etat ? etat->regime : DN_VAL_ABSENTE;
    lv_color_t c = dn_val_regime_couleur(r);
    char buf[DN_WIDGET_TXT_MAX + 32];
    int fin_gauche = W_PAD;
    for (int i = 0; i < DN_WIDGET_GRANDEURS_MAX; i++) {
        if (!w->valeur[i]) {
            continue;
        }
        composer(desc, etat, i, buf, sizeof(buf));
        lv_label_set_text(w->valeur[i], buf);
        /* 🔴 LA POSITION SE RECALCULE À CHAQUE MISE À JOUR EN CÔTE À CÔTE, ET
         *    CE N'EST PAS UN LUXE : la colonne droite est calée à DROITE, donc
         *    son x DÉPEND de la largeur du texte. « 9,9 % » et « 100,0 % » ne
         *    commencent pas au même endroit. Ne pas repositionner laisserait la
         *    valeur à la place de la PRÉCÉDENTE — un décalage qui grandit avec
         *    le nombre de chiffres, et que rien ne signalerait.
         * ⚠️ En EMPILÉ (le défaut) `valeur_placer` repose au même x et le coût
         *    est un `lv_obj_set_pos` par grandeur ; en côte à côte il s'y ajoute
         *    UN `lv_text_get_size` par colonne droite. Le budget est mesuré en
         *    AC12, ⛔ pas supposé négligeable. */
        valeur_placer(w->valeur[i], i, w->n ? w->n : 1, w->w ? w->w : 225,
                      fin_gauche, desc, &fin_gauche);
        /*
         * 🔴 dn4-1 / W10 — UNE GRANDEUR ABSENTE SE PEINT EN GRIS, MÊME DANS UNE
         *    CASE RÉELLE. `composer()` rend déjà « -- » sans unité pour un texte
         *    vide ; sans cette ligne, ce « -- » sortait dans le BLANC du régime
         *    RÉEL — un tiret présenté comme une mesure. Le motif complet est
         *    dans `dn_widget.h` : ici les deux grandeurs ont des sources
         *    INDÉPENDANTES (GPU % ≠ GPU °C), contrairement à AMBIANCE dont les
         *    deux viennent d'un seul capteur.
         * ⚠️ Aucun effet sur l'existant : CPU (n=1), AMBIANCE (les deux textes
         *    posés ensemble) et les mocks ne produisent jamais un seul texte vide.
         */
        bool grandeur_vide = !etat || etat->txt[i][0] == '\0';
        lv_obj_set_style_text_color(
            w->valeur[i],
            grandeur_vide ? dn_val_regime_couleur(DN_VAL_ABSENTE) : c, 0);
    }
    if (w->jauge) {
        /* Une valeur ABSENTE ou SIMULÉE remplit quand même la jauge : elle
         * représente la valeur AFFICHÉE, et la couleur du texte dit déjà d'où
         * elle vient. Une jauge figée à zéro sur une valeur absente se lirait
         * « 0 tr/min », c'est-à-dire un chiffre — donc un mensonge de plus. */
        lv_bar_set_value(w->jauge,
                         (r == DN_VAL_ABSENTE || !etat) ? desc->ind_min
                                                        : etat->brut[0],
                         LV_ANIM_OFF);
    }
    if (w->sec) {
        lv_label_set_text(w->sec, (etat && etat->secondaire[0]) ? etat->secondaire
                                                                : "");
    }
    if (w->badge) {
        if (r == DN_VAL_SIMULEE) {
            lv_obj_clear_flag(w->badge, LV_OBJ_FLAG_HIDDEN);
        } else {
            lv_obj_add_flag(w->badge, LV_OBJ_FLAG_HIDDEN);
        }
    }

    if (grouper) {
        lv_display_enable_invalidation(disp, true);
        /* UNE seule zone sale : le conteneur entier. C'est la branche B d'AC8. */
        lv_obj_invalidate(w->racine);
    }
}

void dn_widget_oublier(dn_widget_t *w)
{
    if (w) {
        memset(w, 0, sizeof(*w));
    }
}

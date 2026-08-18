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
 *   🔴 « CÔTE À CÔTE » A ÉTÉ ÉCARTÉ PAR L'ARITHMÉTIQUE, PAS PAR GOÛT.
 *      À 28 px, « 25,5 °C » mesure ~110 px et « 52,4 % » ~95 px : 205 px pour
 *      201 px utiles (225 moins deux marges de 12). Ça ne rentre pas, et ça ne
 *      rentrerait pas davantage avec une température négative à deux chiffres
 *      (« -12,3 °C »). Le côte à côte n'aurait tenu qu'en descendant la police,
 *      c'est-à-dire en rendant la case principale MOINS lisible que les autres
 *      — l'inverse de « lisible à ~50 cm ».
 *      « principale + secondaire » a été écarté pour une autre raison : il
 *      HIÉRARCHISE. Or température et humidité sont deux mesures du même
 *      capteur, de même dignité ; en reléguer une en petit dirait le contraire.
 *   ⇒ EMPILÉES. Et c'est le mécanisme GÉNÉRIQUE : N grandeurs = N lignes.
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

/* ── Géométrie interne de la case ─────────────────────────────────────────── */
#define W_PAD 12
#define W_TITRE_Y 14
#define W_ICONE_Y 8
#define W_VAL_Y 48
#define W_VAL_PAS 40
#define W_JAUGE_H 10
#define W_SEC_H 20

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

/* Le texte d'une grandeur, unité comprise. Une valeur ABSENTE ne porte JAMAIS
 * son unité : « -- % » suggérerait qu'on sait de quoi on parle. */
static void composer(const dn_widget_desc_t *d, const dn_widget_etat_t *e, int i,
                     char *out, size_t n)
{
    const char *ic = d->grandeurs[i].icone;
    if (!e || e->regime == DN_VAL_ABSENTE || e->txt[i][0] == '\0') {
        snprintf(out, n, "%s%s", ic ? ic : "", ic ? " --" : "--");
        return;
    }
    const char *u = d->grandeurs[i].unite;
    snprintf(out, n, "%s%s%s%s%s", ic ? ic : "", ic ? " " : "", e->txt[i],
             u ? " " : "", u ? u : "");
}

void dn_widget_creer(lv_obj_t *parent, int x, int y, int w, int h,
                     const dn_widget_desc_t *desc, const dn_widget_etat_t *etat,
                     lv_event_cb_t cb, void *user, dn_widget_t *out)
{
    memset(out, 0, sizeof(*out));
    out->racine = dn_widget_zone_creer(parent, x, y, w, h, cb, user);

    int tx = W_PAD;
    if (desc->icone) {
        /* L'icône porte la COULEUR D'ACCENT du descripteur : c'est le seul
         * endroit où dn3-1 EXERCE le champ `couleur`, pour qu'il ne soit pas un
         * champ mort que dn3-3 découvrirait non branché. */
        dn_widget_texte(out->racine, desc->icone, &dn_font_28,
                        lv_color_hex(desc->couleur), tx, W_ICONE_Y);
        tx += 40;
    }
    dn_widget_texte(out->racine, desc->titre, &dn_font_14,
                    lv_color_hex(W_COL_TITRE), tx, W_TITRE_Y + 8);

    /* Le badge de régime — CRÉÉ TOUJOURS, masqué quand il ne s'applique pas.
     * Le créer à la demande obligerait `dn_widget_maj` à construire des objets
     * LVGL, donc à allouer, sous le verrou et depuis une tâche de source. Un
     * `lv_obj_add_flag(HIDDEN)` ne peut pas échouer ; un `lv_label_create` si. */
    out->badge = dn_widget_texte(out->racine, "SIMULÉ", &dn_font_14,
                                 lv_color_hex(W_COL_SIMULEE), w - 66, W_TITRE_Y);
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
    char buf[DN_WIDGET_TXT_MAX + 24];
    for (int i = 0; i < n; i++) {
        composer(desc, etat, i, buf, sizeof(buf));
        out->valeur[i] = dn_widget_texte(
            out->racine, buf, &dn_font_28,
            dn_val_regime_couleur(etat ? etat->regime : DN_VAL_ABSENTE), W_PAD,
            W_VAL_Y + i * W_VAL_PAS);
    }

    int y_bas = W_VAL_Y + n * W_VAL_PAS;
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
    if (desc->indicateur) {
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
                 "(y_bas=%d + %d > h=%d) — %d grandeur(s)%s. La jauge est "
                 "prioritaire (contrat dn_widget.h / W5).",
                 desc->titre ? desc->titre : "?", y_bas, W_SEC_H, h, n,
                 desc->indicateur ? " + jauge" : "");
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
    char buf[DN_WIDGET_TXT_MAX + 24];
    for (int i = 0; i < DN_WIDGET_GRANDEURS_MAX; i++) {
        if (!w->valeur[i]) {
            continue;
        }
        composer(desc, etat, i, buf, sizeof(buf));
        lv_label_set_text(w->valeur[i], buf);
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

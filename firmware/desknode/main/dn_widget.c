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
/* dn4-10 : pour `lv_obj_get_ext_draw_size()`. ⚠️ EN-TÊTE PRIVÉ DE LVGL, inclus
 * en connaissance de cause — la fonction était publique en 9.1 (voir le mapping
 * `lv_api_map_v9_1.h:73`) et a été déplacée en 9.2. La DEVINER serait pire :
 * sans elle, une ombre ou une bordure déborderait de la zone unie et laisserait
 * exactement la trace qu'on cherche à supprimer. Si LVGL la déplace encore, la
 * compilation CASSERA — c'est le comportement voulu, ⛔ pas un silence. */
#include "core/lv_obj_draw_private.h"

static const char *TAG = "dn_widget";

/* ── Géométrie interne de la case — CE SONT LES DÉFAUTS ───────────────────── */
#define W_PAD 12
#define W_TITRE_Y 14
#define W_ICONE_Y 8
#define W_VAL_Y 48
#define W_VAL_PAS 40
#define W_JAUGE_H 10
/*
 * 🔴 dn4-14-2 / REVUE DU 2026-08-30 — LA RÉSERVE DE LA LIGNE SECONDAIRE SE
 *    CALCULE, ⛔ ELLE NE S'ÉCRIT PLUS. `W_SEC_H` valait `W_SEC_Y_OFF +
 *    lh(dn_font_14)`
 *    = 2 + 18, et c'était juste tant que la ligne secondaire était en 14 px
 *    EN DUR. Depuis que `dn_widget_font_libelle()` SUIT LE TITRE
 *    (`s_titre_suit` = `true` par verdict owner ⇒ `dn_font_18`, `lh` 23), le
 *    libellé occupe **25 px** pour une réserve de **20** : la garde
 *    `y_bas + W_SEC_H <= h` passait pendant que LVGL clippait, et la branche
 *    `else` — celle qui DIT que la secondaire est abandonnée — n'était JAMAIS
 *    atteinte. ⇒ La panne muette que W5 avait rendue audible, RÉARMÉE par un
 *    changement de police, dans la story qui change les polices.
 * ⇒ La réserve est désormais RELUE de la police réellement posée : `sec_h()`.
 * ⛔ **`W_SEC_H` A ÉTÉ SUPPRIMÉ**, il n'est pas laissé « pour mémoire » : une
 *    constante que plus rien ne lit est exactement le nombre qui dérive sans
 *    que personne ne le voie. Seul le DÉCALAGE sous `y_bas` reste une
 *    constante, parce qu'il ne dépend d'aucune police.
 */
#define W_SEC_Y_OFF 2
/* Gouttière minimale entre deux colonnes en côte à côte. En dessous, deux
 * nombres se lisent comme un seul — et « ça tient » deviendrait « ça touche ». */
#define W_GOUTTIERE 12
/* Largeur du sillon réservé à l'icône de la case, par taille de police. */
#define W_ICONE_AV_28 40
#define W_ICONE_AV_14 22
/*
 * 🔴 dn4-14-2 / AC2 — LE RETRAIT DU BADGE « SIMULÉ » DEPUIS LE BORD DROIT.
 *    Il était écrit `w - 66` EN DUR au site de création, et c'est LUI qui borne
 *    le TITRE : le titre commence en `W_PAD + W_ICONE_AV_*` et le badge finit
 *    l'espace disponible. ⇒ 52..159 sur une case de 225, soit **107 px**, et ce
 *    nombre n'était calculable nulle part.
 * 🔴 **REVUE DU 2026-08-30 — CE MUR N'EST PAS UN MUR DE CLIP, ET LE DIRE FAUX
 *    A COÛTÉ UN DIAGNOSTIC.** Ce commentaire écrivait *« LVGL clippe au parent
 *    SANS UN MOT … il se coupe »*. C'est FAUX à cet endroit précis, et voici
 *    pourquoi, relu du code :
 *      · le label de titre est créé par `dn_widget_texte()` **SANS largeur
 *        posée** ⇒ il se dimensionne au contenu ;
 *      · son parent est la ZONE de case, large de `DN_UI_CASE_W` = **225** px ;
 *      · ⇒ LVGL ne le clippe qu'à `x = 225`, soit **173 px** de titre depuis
 *        `x = 52`. ⛔ PAS à 107.
 *    Et le badge « SIMULÉ » est créé **HIDDEN** et n'est démasqué que sur une
 *    case **SIMULÉE**. ⇒ Dans la bande **107..173 px** il n'y a AUCUN clip :
 *    il y a un **CHEVAUCHEMENT de la réserve du badge**, visible seulement si
 *    le badge l'est. Au-delà de 173, c'est un vrai clip.
 * ⚠️ Ce que ça change pour le relevé du 2026-08-29 : « DÉMO 2+JAUGE » = 114 px
 *    finit à `x = 166 < 225` et la case de démo ne passe jamais en SIMULÉE ⇒
 *    **rien n'était clippé, et rien ne se superposait**. Le défaut trouvé est
 *    réel — c'était une **ABSENCE DE GARDE** —, ⛔ pas un artefact visible, et
 *    les « 7 px » sont `166 − 159`, la morsure dans la réserve.
 * ✅ **VERDICT OWNER DU 2026-08-30 — LE SEUIL RESTE 107.** On garde la réserve
 *    du badge comme critère, parce qu'un titre qui la mord est un titre qui
 *    casse dès que la case passe SIMULÉE, et que le régime d'une case n'est pas
 *    une propriété de sa géométrie. ⚠️ **ÉCART ASSUMÉ** : le compteur monte
 *    aussi quand le badge est masqué, donc sur des cases où rien ne se voit.
 */
#define W_BADGE_DE_DROITE 66

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
    .font_titre = NULL, /* NULL = LE DÉFAUT — résolu à l'usage, voir font_titre() */
};

/* ⚠️ RÉSOLU À L'USAGE, PAS À L'INITIALISATION : `&dn_font_28` n'est pas une
 *    constante d'initialiseur portable ici, et surtout un `NULL` explicite rend
 *    lisible « personne n'a choisi » au lieu de figer un pointeur dans un
 *    statique que la console imprimerait comme un réglage. */
/*
 * ══ dn3-3 : L'IDENTITÉ VISUELLE D'AMBIENT — DÉCISION OWNER DU 2026-08-25 ═════
 *
 * Verbatim : *« je veux que tout passe en nuance de noir blanc, titre et icônes
 * disparaissent, chiffres agrandis, et blanc sur fond noir et sur fond gris
 * foncé »*.
 *
 * ⇒ En Ambient la case ne porte plus QUE ses valeurs : le titre, l'icône, le
 *   badge « SIMULÉ » et le PRÉFIXE de grandeur disparaissent, l'aplat passe au
 *   gris très foncé OPAQUE sur un écran noir, et la valeur monte d'une police.
 *
 * 🔴 LE PRÉFIXE COMPTE AUTANT QUE LE TITRE, ET C'EST LUI QUI DÉBLOQUE LA TAILLE.
 *    Mesuré sur la carte (`widget largeur`, case de 225 px dont 201 utiles) :
 *      · « c.max 100,0 % » = 197 px  ⇒ plafond 28,6 px : AUCUN agrandissement
 *      · « 2999,9 Mb/s »   = 168 px  ⇒ plafond 33,5 px  (avec l'unité)
 *      · « 2999,9 »        =  90 px  ⇒ plafond 62,5 px  (sans l'unité)
 *    ⇒ Tant que le préfixe reste, « chiffres agrandis » est ARITHMÉTIQUEMENT
 *      IMPOSSIBLE. Le retirer — ce que la demande owner implique — fait passer
 *      le plafond de 28,6 à 33,5 px.
 * ⚠️ Et « LVGL clippe au parent SANS un mot » : ⛔ ne pas remonter ces tailles
 *    sans re-mesurer, le débordement serait MUET.
 */
static bool s_ambient;
/* L'unité reste-t-elle affichée ? ⚠️ CE DRAPEAU CHOISIT LA POLICE : avec unité
 * on plafonne à 33 px, sans unité on monte à 56. A/B à chaud (`veille unite`) —
 * l'œil tranche sur la dalle, ⛔ pas un reflash par essai. */
static bool s_amb_unite = true;
/* La jauge survit-elle à la veille ? Constat owner attendu (`veille jauge`). */
static bool s_amb_jauge = true;

/*
 * 🔴 LA POLICE DE LA VALEUR EST CONSCIENTE DU MODE, ET ELLE DÉPEND DE L'UNITÉ.
 * ⚠️ En Ambient elle IGNORE `s_geom.font_val` (l'override d'opérateur) : les
 *    deux polices de veille sont les seules dont la taille a été MESURÉE contre
 *    la largeur utile. Laisser l'override passer aurait permis de poser une
 *    police dont personne n'a vérifié qu'elle tient.
 * ⚠️ Les polices de veille ne portent NI accents NI symboles (plage réduite) :
 *    ⛔ ne jamais les utiliser pour du texte d'interface. En Ambient il n'y a
 *    plus de texte d'interface — c'est précisément ce qui les rend légitimes.
 */
/*
 * 🔴 LA POLICE DU MODE **ACTIF**, ET ELLE EXISTE SÉPARÉMENT POUR UNE RAISON.
 *    `dn_widget_geom()` est lue en LECTURE-MODIFICATION-ÉCRITURE (`widget
 *    dispo`, `widget replacer`…). Si elle rendait la police d'AMBIENT, un
 *    `widget dispo empile` tapé PENDANT la veille graverait `dn_font_33` comme
 *    override PERMANENT — et les titres perdraient leurs accents au retour en
 *    Actif, EN SILENCE, parce que les polices de veille n'ont pas le latin-1.
 * ⛔ Ne jamais fusionner ces deux fonctions.
 */
static const lv_font_t *font_val_actif(void)
{
    return s_geom.font_val ? s_geom.font_val : &dn_font_28;
}

static const lv_font_t *font_val(void)
{
    if (s_ambient) {
        return s_amb_unite ? &dn_font_33 : &dn_font_56;
    }
    return font_val_actif();
}

/*
 * Le `y` de la première valeur et le pas entre lignes, CONSCIENTS DU MODE.
 * En Ambient le titre et l'icône ont disparu : la valeur remonte occuper la
 * place libérée, et le pas suit la hauteur de ligne RELUE de la police
 * (⛔ pas une constante recopiée — changer de police sans changer le pas
 * ferait chevaucher deux grandeurs, et LVGL ne dirait rien).
 */
#define W_AMB_VAL_Y 26
static int val_y_courant(void)
{
    return s_ambient ? W_AMB_VAL_Y : s_geom.val_y;
}

static int val_pas_courant(void)
{
    if (!s_ambient) {
        return s_geom.val_pas;
    }
    return (int)lv_font_get_line_height(font_val()) + 6;
}

static const lv_font_t *font_entete(void)
{
    return s_geom.entete == DN_ENTETE_COMPACT ? &dn_font_14 : &dn_font_28;
}

/*
 * 🔴 dn4-14-2 / AC4.1 — LA POLICE DU TITRE, RÉSOLUE À L'USAGE.
 *
 * ⚠️ ELLE N'A **PAS** DE VARIANTE D'AMBIENT, ET C'EST DÉLIBÉRÉ : en Ambient le
 *    titre DISPARAÎT (`masquables[]`, décision owner du 2026-08-25). Une
 *    « police de titre en veille » désignerait donc un objet qui n'est pas
 *    dessiné — et surtout, elle ouvrirait la porte que `font_val` a dû fermer :
 *    `dn_widget_geom()` étant lue en lecture-modification-écriture, un
 *    `widget dispo` tapé pendant la veille graverait cette police-là comme
 *    override PERMANENT, et « RÉSEAU » perdrait son É au retour en Actif.
 * ⇒ 🔴 IL N'Y A QU'UNE FONCTION ICI, ET IL NE FAUT PAS EN AJOUTER UNE SECONDE.
 *   L'absence de couple `_actif()` / `_ambient()` EST la garde d'AC4.2.
 */
/*
 * 🔴 LE DÉFAUT EST **18**, ET C'EST UN VERDICT OWNER DU 2026-08-30, ⛔ PAS UN
 *    CHOIX DE DEV. Verbatim du 2026-08-29 : *« les ecriture sont trop petites
 *    elles devrais etre agrandit un peu (cpu, gpu etc..) »* ; A/B joué sur la
 *    dalle en mode ACTIF, avec l'agent réel, et tranché : *« C'est ça, on garde
 *    18 »*.
 * ⚠️ 18 EST LE PLAFOND, ET IL EST HORIZONTAL — ⛔ pas vertical. MESURÉ sur la
 *    carte : « AMBIANCE » fait **103 px pour 107 utiles**. À 20 elle en fait
 *    **113** et se ferait CLIPPER par le badge, SANS UN MOT.
 *    ⇒ ⛔ NE PAS REMONTER CETTE VALEUR SANS RE-MESURER (`widget largeur mur`),
 *      et ⛔ ne pas se fier au plafond VERTICAL de `dn_widget.h` (qui dit 20) :
 *      il ne regarde qu'une dimension.
 */
static const lv_font_t *font_titre(void)
{
    return s_geom.font_titre ? s_geom.font_titre : &dn_font_18;
}

/* 🔴 dn4-14-2 / AC8.3 — `true` PAR VERDICT OWNER DU 2026-08-30.
 *    La question a été posée SUR LA DALLE, les deux variantes commutables :
 *    *« On les garde comme ça ? »* ⇒ *« Oui — tout le chrome en 18 »*.
 * ⚠️ Ce n'était PAS déductible du verbatim : *« cpu, gpu »* sont des TITRES, et
 *    rien ne disait si `c.max` / `extr.moy` suivaient. ⛔ Le cadrage a
 *    explicitement refusé de trancher à sa place — c'est l'œil qui l'a fait. */
static bool s_titre_suit = true;

bool dn_widget_titre_suit(void) { return s_titre_suit; }
void dn_widget_set_titre_suit(bool suit) { s_titre_suit = suit; }

const lv_font_t *dn_widget_font_libelle(void)
{
    return s_titre_suit ? font_titre() : &dn_font_14;
}

/* La HAUTEUR que la ligne secondaire consomme réellement, police comprise —
 * `W_SEC_Y_OFF` de décalage sous `y_bas`, puis l'interligne de la police que
 * `dn_widget_font_libelle()` vient de rendre. En `dn_font_14` il rend 20 —
 * l'ancien `W_SEC_H` —, en `dn_font_18` il rend 25. */
static int sec_h(void)
{
    return W_SEC_Y_OFF + (int)lv_font_get_line_height(dn_widget_font_libelle());
}

/* ⚠️ `&dn_font_14` reste le « non » de ce ternaire, ⛔ pas le défaut du titre :
 *    `widget titre suit off` doit rendre les libellés à leur ANCIENNE taille,
 *    pas à la nouvelle. Un `font_titre()` des deux côtés ferait de ce réglage
 *    une commande qui ne fait rien — et qui ne le dirait pas. */

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
/* ⚠️ La largeur en colonne UNIQUE — voir le motif dans `dn_widget.h`. Séparé de
 * `s_chevauchements` À DESSEIN : « deux colonnes se marchent dessus » et « une
 * valeur seule dépasse la case » sont deux diagnostics DIFFÉRENTS, et ce dépôt
 * a déjà payé d'avoir mis deux causes opposées dans le même seau (`tronquee` /
 * `trop_longue`, dn_link.h). */
static uint32_t s_trop_larges;

uint32_t dn_widget_chevauchements(void) { return s_chevauchements; }
void dn_widget_chevauchements_reset(void) { s_chevauchements = 0; }
uint32_t dn_widget_debordements(void) { return s_debordements; }
void dn_widget_debordements_reset(void) { s_debordements = 0; }
uint32_t dn_widget_trop_larges(void) { return s_trop_larges; }
void dn_widget_trop_larges_reset(void) { s_trop_larges = 0; }

int dn_widget_gouttiere(void) { return W_GOUTTIERE; }
int dn_widget_largeur_utile(int w) { return w - 2 * W_PAD; }

/*
 * ── dn4-14-2 / AC2 : LE SLOT DU TITRE, RELU — ⛔ PAS RÉCITÉ ──────────────────
 *
 * Le titre part après le sillon d'icône et s'arrête au badge. Les deux bornes
 * viennent des MÊMES macros que `dn_widget_creer()` emploie, et la largeur du
 * sillon DÉPEND DU RÉGIME D'EN-TÊTE (`W_ICONE_AV_28` en NORMAL, `_14` en
 * COMPACT) : un instrument qui figerait 40 px se tromperait de 18 px dès qu'on
 * bascule en COMPACT, et se tromperait EN SILENCE.
 * ⚠️ `avec_icone` est un paramètre parce que `desc->icone` peut être NULL : une
 *    case sans icône donne son sillon au titre. ⛔ Ne pas le supposer.
 */
/*
 * 🔴 dn4-14-2 / REVUE DU 2026-08-30 — LE BAS DU TITRE A ENFIN UNE FABRIQUE.
 *    `dn_widget.h` publiait le plancher d'en-tête dans un TABLEAU et concluait
 *    « 20 px est le plafond VERTICAL du titre ; 22 est RÉFUTÉ » — et **rien ne
 *    le faisait respecter**. `dn_ui_geom_valider()` refusait une police de
 *    VEILLE et acceptait `dn_font_28` (`lh` 35) : titre 22..57 contre
 *    `val_y = 48`, soit **9 px de recouvrement** avec la première ligne de
 *    valeur — sans log, sans compteur, sans refus. Un plafond publié que
 *    personne n'exécute n'est pas un plafond.
 * ⚠️ Le `y` du titre dépend de l'EN-TÊTE (22 en NORMAL, 8 en COMPACT), d'où le
 *    paramètre : valider avec le mauvais en-tête refuserait COMPACT à tort.
 * ⛔ `NULL` se résout ici comme partout ailleurs : « personne n'a choisi ».
 */
int dn_widget_titre_bas(const lv_font_t *font_titre, dn_widget_entete_t entete)
{
    const lv_font_t *f = font_titre ? font_titre : &dn_font_18;
    int y = (entete == DN_ENTETE_COMPACT) ? W_ICONE_Y : W_TITRE_Y + 8;
    return y + (int)lv_font_get_line_height(f);
}

int dn_widget_titre_x(bool avec_icone)
{
    if (!avec_icone) {
        return W_PAD;
    }
    return W_PAD + ((s_geom.entete == DN_ENTETE_COMPACT) ? W_ICONE_AV_14
                                                         : W_ICONE_AV_28);
}

int dn_widget_titre_utile(int w, bool avec_icone)
{
    int utile = (w - W_BADGE_DE_DROITE) - dn_widget_titre_x(avec_icone);
    return utile > 0 ? utile : 0;
}

/*
 * ══ dn4-14-2 / AC2.1 + AC4.2 — LE REGISTRE DES POLICES, EN **UNE SEULE** PLACE ═
 *
 * 🔴 IL VIT ICI, ⛔ PAS DANS `dn_console.c`, PARCE QUE LE VALIDATEUR EN A BESOIN.
 *    `dn_ui_geom_valider()` doit pouvoir REFUSER une police de veille dans
 *    `font_titre` (AC4.2). Si la console gardait sa propre table, il y aurait
 *    DEUX listes — et le dépôt sait exactement où ça mène : `dn_font.h` a
 *    recopié un choix d'icône et a menti TROIS fois.
 *
 * ⚠️ LA TABLE EST DÉVELOPPÉE DEPUIS `DN_FONT_LISTE`, que `gen_font_dn.py`
 *    construit depuis `TAILLES`. Ajouter une taille la remplit, en retirer une
 *    la vide — ⛔ personne n'a à y penser, et aucun `printf` n'énumère plus.
 * ⚠️ `line_height` n'est PAS stockée : elle se relit de l'objet. Une taille
 *    recopiée ici se périmerait à la régénération suivante, sans un mot.
 */
static const struct {
    const char *nom;
    const lv_font_t *font;
    bool interface_;
} k_polices[] = {
#define DN_POLICE_X(taille, symbole, itf) {#taille, &symbole, (itf) != 0},
    DN_FONT_LISTE(DN_POLICE_X)
#undef DN_POLICE_X
};

int dn_widget_polices_nb(void)
{
    return (int)(sizeof(k_polices) / sizeof(k_polices[0]));
}

bool dn_widget_police_at(int i, const char **nom, const lv_font_t **font,
                         bool *interface_)
{
    if (i < 0 || i >= dn_widget_polices_nb()) {
        return false;
    }
    if (nom) {
        *nom = k_polices[i].nom;
    }
    if (font) {
        *font = k_polices[i].font;
    }
    if (interface_) {
        *interface_ = k_polices[i].interface_;
    }
    return true;
}

/* ⛔ AUCUNE correspondance partielle : « 1 » ne doit pas tomber sur « 14 ».
 *    Un opérateur qui se trompe doit LE SAVOIR. */
const lv_font_t *dn_widget_police_par_nom(const char *nom)
{
    if (!nom) {
        return NULL;
    }
    for (int i = 0; i < dn_widget_polices_nb(); i++) {
        if (strcmp(k_polices[i].nom, nom) == 0) {
            return k_polices[i].font;
        }
    }
    return NULL;
}

/* Le nom retrouvé par ADRESSE. ⛔ Jamais déduit d'une `line_height` : deux
 * polices pourraient partager la leur. */
const char *dn_widget_police_nom(const lv_font_t *f)
{
    for (int i = 0; i < dn_widget_polices_nb(); i++) {
        if (k_polices[i].font == f) {
            return k_polices[i].nom;
        }
    }
    return "?";
}

/*
 * 🔴 LA GARDE D'AC4.2, ET ELLE EST **FERMÉE PAR DÉFAUT**.
 *    Une police inconnue de la table rend `false` : mieux vaut refuser un
 *    pointeur qu'on ne sait pas qualifier que le laisser passer. Les polices de
 *    veille n'ont pas le latin-1 ⇒ y pointer un texte d'interface ferait
 *    disparaître le É de « RÉSEAU » **sans un mot**.
 */
bool dn_widget_police_interface(const lv_font_t *f)
{
    for (int i = 0; i < dn_widget_polices_nb(); i++) {
        if (k_polices[i].font == f) {
            return k_polices[i].interface_;
        }
    }
    return false;
}

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
        /* 🔴 LA POLICE **D'ACTIF**, ⛔ PAS `font_val()` (correctif dn3-3).
         *    Cette fonction est lue en LECTURE-MODIFICATION-ÉCRITURE : rendre
         *    la police d'Ambient ferait graver `dn_font_33` comme override
         *    permanent au premier `widget dispo` tapé pendant la veille, et les
         *    titres perdraient leurs accents EN SILENCE au retour en Actif.
         * ⚠️ Pour savoir ce qui S'APPLIQUE réellement, c'est
         *    `dn_widget_geom_appliquee()` — et elle, on ne la réécrit pas. */
        out->font_val = font_val_actif(); /* ⛔ jamais NULL vers l'extérieur */
        out->font_titre = font_titre();   /* idem — et elle n'a pas de variante
                                           * d'Ambient, donc rien à démêler */
    }
}

/*
 * 🔴 CE QUI S'APPLIQUE VRAIMENT — ⛔ EN LECTURE SEULE, ET C'EST LE POINT.
 *
 *    `dn_widget_geom()` rend l'OVERRIDE, parce qu'elle est relue puis réécrite.
 *    Celle-ci rend ce que le rendu utilise à cet instant, mode compris. La
 *    console imprime CELLE-CI : jusqu'au 2026-08-25 elle publiait `val_y 48 ·
 *    val_pas 40` pendant qu'Ambient appliquait 26 / 47 — une étiquette qui ment,
 *    et c'est exactement la classe de défaut que ce dépôt traque.
 * ⛔ NE JAMAIS la passer à `dn_widget_set_geom()` : elle graverait les valeurs
 *    d'Ambient comme override permanent.
 */
void dn_widget_geom_appliquee(dn_widget_geom_t *out)
{
    if (out) {
        *out = s_geom;
        out->val_y = val_y_courant();
        out->val_pas = val_pas_courant();
        out->font_val = font_val();
        /* 🔴 AC4.2 — ELLE REND LA MÊME QU'EN ACTIF, ET C'EST LA GARDE.
         *    `font_val` doit distinguer les deux modes (les polices de veille
         *    sont les seules dont la taille ait été MESURÉE contre la largeur
         *    utile) ; le TITRE, lui, n'est pas dessiné en Ambient. ⇒ repasser
         *    cette structure à `set_geom()` ne peut PAS graver une police de
         *    veille dans `font_titre` — il n'y en a jamais eu une dedans.
         * ⛔ Ça n'autorise pas à la repasser : `val_y` / `val_pas` / `font_val`
         *    restent ceux d'Ambient. Le contrat du docblock TIENT. */
        out->font_titre = font_titre();
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
        out->font_titre = &dn_font_18; /* verdict owner du 2026-08-30 */
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
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * 🔴 LE JOUR EST ARRIVÉ — LE DÉFAUT BASCULE À `false` LE 2026-08-23 (dn4-10)
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * ⛔ TOUT CE QUI PRÉCÈDE RESTE VRAI ET N'EST PAS EFFACÉ. En particulier
 *    l'avertissement ci-dessus, qui a écrit LA CONDITION DE SA PROPRE
 *    RÉOUVERTURE, mot pour mot :
 *      « Le jour où la copie deviendra le goulot (plus de cases vivantes, ou
 *        une copie plus lente), l'arbitrage devra être REJOUÉ. »
 *    LES DEUX BRANCHES DE LA CONDITION SONT REMPLIES, ET MESURÉES :
 *      - « plus de cases vivantes » : 4 -> 6 depuis dn4-1 / dn4-8 / dn4-9 ;
 *      - « la copie devenue le goulot » : 3 059 us par flush en groupé, contre
 *        350 us en fin. C'est un facteur 8,7, et c'est LE goulot.
 *
 * 🔴 CE QUE LE GROUPAGE FABRIQUAIT, ET QU'AUCUN INSTRUMENT NE VOYAIT AVANT :
 *    la FAMINE DMA DU BOUNCE. En multipliant les pixels copiés par 2 à 3,3, il
 *    monopolisait la PSRAM pendant que l'ISR du panneau essayait d'y lire de
 *    quoi remplir le bounce buffer. Résultat à l'écran, dans les mots de
 *    l'owner : « un glissement de quelques pixels vers le bas, ça s'abaisse
 *    puis revient, quasiment toutes les secondes ».
 *
 * 🎯 LES CHIFFRES DE LA BASCULE — compteur de dn4-10, fenêtres de 180 s,
 *    stimulus identique, DEUX passes en ordre inversé :
 *
 *      grandeur                      groupé      FIN        rapport
 *      aire par flush                36 675 px   6 746 px   -82 %
 *      pixels par CYCLE              73 350      31 948     -56 %
 *      copie par flush                3 059 us     350 us   / 8,7
 *      déficit de phase PIRE            961 us     145 us   (seuil 620 us)
 *      corruptions par seconde        0,329       0,008     / 41
 *      -> et 0 sur une fenêtre de 200 s, image « stable et propre » (owner)
 *
 * ⚠️ CE QUE LA BASCULE COÛTE, ET IL FAUT LE LIRE AVANT DE LA DÉFAIRE :
 *    exactement ce que §16.2 annonçait — le temps mural. Les flushes par cycle
 *    passent de 2,0 à 4,7, donc une mise à jour de case arrive ~2,7 trames plus
 *    tard, soit ~72 ms. À la cadence du produit (1 Hz), ce n'est pas visible :
 *    l'owner a regardé 200 s et n'a rien vu. Et la navigation ne bouge pas —
 *    `nav ab 40` : 336,8 -> 337,4 ms (n=80), soit +0,6 ms, très en dessous de
 *    la dispersion des campagnes publiées. `fps 15` reste à 37,40 Hz exacts.
 *    ⛔ La navigation ne bouge pas PARCE QUE le groupage ne la concernait pas :
 *      un changement d'écran est une RECONSTRUCTION, pas une mise à jour de
 *      valeur. Le levier n'agit que sur le chemin qui posait problème.
 *
 * ⚠️ ET CE QU'IL NE FAUT PAS EN CONCLURE : la bascule ne SUPPRIME pas le
 *    mécanisme, elle le fait passer sous le seuil. Le déficit pire mesuré en
 *    fin est de 145 us pour un seuil de 620 — il reste 76 % de marge, ⛔ pas
 *    l'infini. Si le produit se charge encore, la question se rouvrira, et
 *    l'instrument de dn4-10 (`flush`, bloc « glissement de trame ») est là pour
 *    la trancher au chiffre.
 *
 * ✅ LA BRANCHE GROUPÉE RESTE VIVANTE ET REJOUABLE À CHAUD : `widget groupe on`.
 *    C'est ce qui a permis cet A/B SANS REFLASHER, et c'est ce qui permettra le
 *    prochain. ⛔ Ne pas la supprimer.
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * 🔴 ET LE DÉFAUT REVIENT À `true` LE 2026-08-23 — L'AGENT RÉEL A RÉFUTÉ LA
 *    BASCULE. ⛔ TOUT CE QUI PRÉCÈDE RESTE, C'EST L'HISTOIRE DU DOSSIER.
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * 🔴 CE QUI ÉTAIT FAUX, ET POURQUOI. Les chiffres du bloc ci-dessus (« / 41 »,
 *    « 0 sur 200 s », « stable et propre ») ont TOUS été pris sous
 *    `dn_injecteur.py --jeu reel` — dont la table émet des valeurs **FIXES**.
 *    Les cases ne changeaient donc quasiment pas ⇒ presque pas de dessin.
 *    ⚠️ C'est L'OWNER qui l'a vu, en regardant la dalle : « à part la temp les
 *      valeurs ne bougent pas, normal ? ». ⛔ Pas la mesure.
 *
 * 🎯 SOUS AGENT RÉEL DE LA TOUR — 180 s, même compteur, même bounce, l'œil de
 *    l'owner à chaque fenêtre :
 *
 *      mode                  taux           déficit pire   ce que l'owner voit
 *      `on`   (groupé)       0,94 /s (173)     744 us      AUCUN artefact
 *      `off`  (fin)          0,54 /s (100)     772 us      restes de chiffres
 *                                                          + bande de fond
 *      `union`               0,97 /s (180)   1 337 us      micro-rectangles
 *      `off` + cases opaques 0,86 /s (159)     715 us      artefacts RÉDUITS,
 *                                                          « ligne verte » au
 *                                                          moment du décalage
 *
 *    ⇒ Le gain réel du fin est **−42 %**, ⛔ PAS « / 41 », ⛔ PAS une suppression.
 *      L'injecteur sous-estimait la charge de dessin d'un facteur mesuré à 108.
 *
 * ⛔ ET IL COÛTE UN DÉFAUT VISUEL. Les artefacts DISPARAISSENT en `groupe on` :
 *    causalité établie par A/B à chaud, ⛔ pas supposée. Décision owner du
 *    2026-08-23 : on ne livre pas une régression visuelle certaine contre −42 %
 *    sur un défaut qui reste visible de toute façon.
 *
 * 🎯 CE QUE LA SÉANCE A QUAND MÊME ÉTABLI, ET QUI NE SE REPERD PAS :
 *    - LE GROUPAGE N'EST PAS QU'UNE AFFAIRE D'AIRE, C'EST UNE **ATOMICITÉ**.
 *      Une case = UNE zone = UN flush, et le flush attend un vsync. En fin,
 *      4,7 flushes au lieu de 2,0 ⇒ la case s'affiche en PLUSIEURS trames et
 *      l'œil voit l'état intermédiaire. Ni dn3-1 ni dn3-2 ne l'avaient nommé.
 *    - LA TRANSPARENCE EST **UNE** DES CAUSES des artefacts, pas la seule :
 *      cases opaques ⇒ artefacts « réduits », ⛔ pas supprimés.
 *    - 🎯 LA « LIGNE VERTE » EST UNE SIGNATURE, ⛔ PAS UN DÉTAIL. En RGB565 le
 *      vert occupe les bits 5-10, donc À CHEVAL sur les deux octets d'un pixel :
 *      un décalage du flux DMA d'un nombre IMPAIR d'octets recombine le poids
 *      fort d'un pixel avec le poids faible du suivant ⇒ dominante VERTE.
 *      ⇒ Elle confirme le mécanisme du driver AU NIVEAU DE L'OCTET, et elle
 *        distingue à l'œil le GLISSEMENT (ligne verte) d'un artefact
 *        d'invalidation (restes de dessin).
 *
 * ✅ LES TROIS MODES RESTENT VIVANTS ET REJOUABLES À CHAUD :
 *    `widget groupe on|off|union`. C'est ce qui a permis TOUS les A/B de cette
 *    séance sans reflasher. ⛔ Ne pas les supprimer — un mode effacé, c'est une
 *    mesure qu'il faudra refaire.
 */
static bool s_groupage = true;

/*
 * ─── dn4-10, TROISIÈME MODE : `union` ───────────────────────────────────────
 *
 * 🔴 POURQUOI IL EXISTE. La bascule `groupé -> fin` a divisé l'aire par 5,4 et
 *    le glissement par 1,7 sous agent RÉEL (0,94 -> 0,54 corruption/s), mais
 *    elle a INTRODUIT des artefacts que l'owner voit : « restes de chiffres
 *    superposés » ET « bande de fond mal repeinte », sur les DEUX cases du
 *    haut — CPU et GPU, les seules à trois grandeurs.
 *
 * 🎯 CE QUE LE GROUPAGE APPORTAIT ET QUE PERSONNE N'AVAIT NOMMÉ : L'ATOMICITÉ.
 *    Une case = UNE zone sale = UN flush, et le flush est synchronisé au vsync.
 *    En fin, la même mise à jour fait 4,7 flushes au lieu de 2,0 : la case
 *    s'affiche donc en PLUSIEURS trames, et l'oeil voit l'état intermédiaire —
 *    d'anciens chiffres à côté des nouveaux, un fond pas encore recomposé.
 *    ⛔ Ce n'est donc PAS un résidu à corriger, c'est le PRIX de la finesse.
 *
 * ⇒ Le mode `union` garde l'ATOMICITÉ (une seule zone, donc un seul flush) mais
 *   ne salit QUE la bande réellement occupée par les valeurs, au lieu du
 *   conteneur entier (36 675 px mesurés).
 *
 * ⚠️ LE PIÈGE, ET IL EST DANS L'API : `lv_obj_invalidate_area()` tronque à
 *    l'objet mais ⛔ N'AJOUTE PAS `ext_draw_size`, contrairement à
 *    `lv_obj_invalidate()` (lv_obj_pos.c:1104-1109). Une ombre ou une bordure
 *    déborderait donc de la zone et laisserait exactement la trace qu'on veut
 *    supprimer. ⇒ on ajoute l'extension de CHAQUE label, à la main.
 *
 * ⚠️ ET ON UNIT AVANT **ET** APRÈS L'ÉCRITURE : un texte qui RACCOURCIT libère
 *    de la place, et cette place-là n'est dans aucune des coordonnées d'après.
 *
 * ⛔ AUCUN DES TROIS MODES N'EST SUPPRIMÉ : `widget groupe on|off|union` reste
 *    rejouable À CHAUD. C'est ce qui a permis tous les A/B de cette séance sans
 *    reflasher, et c'est ce qui permettra le prochain.
 */
static bool s_groupe_union = false;

void dn_widget_set_groupe_union(bool on) { s_groupe_union = on; }
bool dn_widget_groupe_union(void) { return s_groupe_union; }

/* Étend `zone` pour couvrir `o`, extension de dessin comprise. `vide` est mis à
 * false dès qu'un objet a été pris en compte. ⛔ Ne PAS remplacer par
 * `lv_area_join` sans les `ext` : voir le piège ci-dessus. */
static void zone_prendre(lv_area_t *zone, bool *vide, lv_obj_t *o)
{
    if (!o || lv_obj_has_flag(o, LV_OBJ_FLAG_HIDDEN)) {
        return;
    }
    lv_area_t a;
    lv_obj_get_coords(o, &a);
    /* ⚠️ L'EXTENSION DE DESSIN EST OBLIGATOIRE, et c'est le piège de l'API :
     *    `lv_obj_invalidate()` l'ajoute (lv_obj_pos.c:1104-1109),
     *    `lv_obj_invalidate_area()` ⛔ NE L'AJOUTE PAS. Une ombre ou une bordure
     *    déborderait donc de la zone et laisserait EXACTEMENT la trace qu'on
     *    cherche à supprimer.
     * ⚠️ `lv_obj_get_ext_draw_size()` vit dans `core/lv_obj_draw_private.h`
     *    depuis LVGL 9.2 (elle était publique en 9.1 — voir le mapping de
     *    compatibilité `lv_api_map_v9_1.h:73`). On l'inclut en connaissance de
     *    cause : la DEVINER serait pire. Si un jour LVGL la déplace encore, la
     *    compilation CASSERA — c'est le comportement voulu, ⛔ pas un silence. */
    int32_t ext = lv_obj_get_ext_draw_size(o);
    a.x1 -= ext;
    a.y1 -= ext;
    a.x2 += ext;
    a.y2 += ext;
    if (*vide) {
        *zone = a;
        *vide = false;
        return;
    }
    /* Union à la main : `lv_area_join()` est privée elle aussi, et pour un
     * min/max sur quatre entiers la dépendance ne se justifie pas. */
    if (a.x1 < zone->x1) {
        zone->x1 = a.x1;
    }
    if (a.y1 < zone->y1) {
        zone->y1 = a.y1;
    }
    if (a.x2 > zone->x2) {
        zone->x2 = a.x2;
    }
    if (a.y2 > zone->y2) {
        zone->y2 = a.y2;
    }
}

/*
 * ── L'INTERRUPTEUR DE BISSECTION DU TRESSAUTEMENT (constat owner 2026-08-19) ──
 *
 * 🔴 A/B ÉTABLI, ET IL ACCUSE dn4-6 : même stimulus (5 trames/s), même carte,
 *    même géométrie remise à 156 px — le firmware de `dn4-1` (`cfd1a54`) NE
 *    tressaute PAS, celui de `dn4-6` SI. La géométrie est donc innocentée
 *    (`widget grille 70 60` ne change rien), et le delta est dans LE CODE.
 *
 * ⇒ Le SEUL travail que `dn4-6` a ajouté au chemin de MISE À JOUR est
 *   `valeur_placer()`. `off` le supprime entièrement : `dn_widget_maj` redevient
 *   alors, ligne pour ligne, celui de `dn4-1` (texte + couleur, rien d'autre).
 *
 * ⚠️ CE QUE `off` CASSE, ET IL FAUT LE SAVOIR AVANT DE L'UTILISER : en
 *    `COTE-A-COTE` la colonne droite est calée à DROITE, donc son `x` dépend de
 *    la largeur du texte. Sans repositionnement elle resterait à la place de la
 *    valeur PRÉCÉDENTE. ⛔ `off` n'est légitime qu'en `EMPILE` — c'est un
 *    INSTRUMENT de bissection, pas un réglage produit.
 * ⛔ Le défaut est `on` : la voie livrée est `EMPILE`, où `off` et `on` doivent
 *    être visuellement IDENTIQUES. S'ils ne le sont pas, c'est le résultat.
 */
static bool s_replacer = true;

void dn_widget_set_replacer(bool on) { s_replacer = on; }
bool dn_widget_replacer(void) { return s_replacer; }

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

/*
 * ── dn3-3 : LE MODE D'AMBIANCE, ET LES TROIS TONS D'AMBIENT ─────────────────
 *
 * Motif complet dans `dn_widget.h`. En deux lignes : `W_COL_ABSENTE` recyclé
 * pour les valeurs RÉELLES en veille rendrait « vivant » indiscernable de
 * « mort » — le défaut du 2026-08-18, qui avait demandé une revue pour être vu.
 *
 * ⚠️ VALEURS D'AMORÇAGE POUR L'A/B D'AC9.3, ⛔ pas des couleurs tranchées.
 *    Elles sont choisies pour être ORDONNÉES EN LUMINANCE et séparées, ce que
 *    `tools/verif_veille_dn33.py` VÉRIFIE — l'œil de l'owner tranchera ensuite
 *    la teinte, et la valeur retenue se gravera ici avec son constat.
 *      RÉELLE  0xffffff : BLANC. Décision owner du 2026-08-25, verbatim —
 *                         « blanc sur fond noir et sur fond gris foncé ».
 *      SIMULÉE 0xa4a4a4 : gris moyen. ⛔ PLUS de teinte ambrée : l'owner a
 *                         demandé « TOUT en nuances de noir et blanc », et une
 *                         seule tache de couleur sur un écran monochrome est le
 *                         premier point que l'œil accroche.
 *      ABSENTE 0x585858 : gris sombre, nettement SOUS le vivant.
 *
 * 🔴 CES DEUX VALEURS ONT ÉTÉ CORRIGÉES EN REVUE DE CODE LE 2026-08-28 — ELLES
 *    DISAIENT `0xa0a0a0` ET `0x565656` ALORS QUE LE TABLEAU JUSTE EN DESSOUS
 *    PORTE `0xa4a4a4` ET `0x585858` DEPUIS LE CORRECTIF RGB565-NEUTRE.
 *    Le tableau porte son propre motif (« `0x58` et ⛔ PAS `0x56` ») ; c'est ce
 *    bloc-ci qui n'avait pas suivi. ⚠️ Et il est LE bloc qu'on lit avant de
 *    lancer une campagne AC9.3 : on y aurait calculé une marge sur des chiffres
 *    faux, en croyant vérifier le code.
 *
 * 🔴 LES TROIS RESTENT DISTINCTS, ET C'EST NON NÉGOCIABLE. Luminances 255 /
 *    **164** / **88** : écarts de **91** et **76** pour un seuil de gate à 24.
 *    ⚠️ Ce bloc annonçait « 160 / 86, écarts 95 et 74 » — les deux chiffres ET
 *    les deux écarts étaient faux, du même correctif non répercuté. Un Ambient
 *    « tout blanc » aurait rendu SIMULÉE indiscernable de RÉELLE — le défaut
 *    du 2026-08-18, remis en place par la porte du monochrome.
 * ⚠️ ET LE BADGE « SIMULÉ » EST MASQUÉ EN AMBIENT : le gris est donc le SEUL
 *    signal qui distingue un chiffre inventé d'une mesure. Raison de plus pour
 *    ne pas les rapprocher.
 */
void dn_widget_set_amb_unite(bool on) { s_amb_unite = on; }
bool dn_widget_amb_unite(void) { return s_amb_unite; }
void dn_widget_set_amb_jauge(bool on) { s_amb_jauge = on; }
bool dn_widget_amb_jauge(void) { return s_amb_jauge; }
static uint32_t s_gris_amb[DN_VAL_REGIME_COUNT] = {
    /* 🔴 `0x58` et ⛔ PAS `0x56` : RGB565-NEUTRE (ecart vert -1 au lieu de +3). */
    [DN_VAL_ABSENTE] = 0x585858,
    [DN_VAL_REELLE] = 0xffffff,
    /* `0xa4` et ⛔ pas `0xa0` : RGB565-neutre (+1 au lieu de -3). */
    [DN_VAL_SIMULEE] = 0xa4a4a4,
};

void dn_widget_set_ambient(bool on) { s_ambient = on; }
bool dn_widget_ambient(void) { return s_ambient; }

bool dn_widget_set_gris_amb(int regime, uint32_t rgb)
{
    if (regime < 0 || regime >= DN_VAL_REGIME_COUNT) {
        return false;
    }
    s_gris_amb[regime] = rgb & 0xFFFFFFu;
    return true;
}

uint32_t dn_widget_gris_amb(int regime)
{
    if (regime < 0 || regime >= DN_VAL_REGIME_COUNT) {
        return 0;
    }
    return s_gris_amb[regime];
}

/*
 * ── dn3-3 : L'ACCENT SELON LE MODE ──────────────────────────────────────────
 * Motif complet dans `dn_widget.h`. Défaut 100 % = gris pur, c'est l'intention
 * owner verbatim du 2026-08-25 (« un état nuance de gris ») ; AC9.4 laisse
 * l'œil le descendre.
 */
/*
 * 🔴 DÉFAUT **95**, ET C'EST UNE MESURE, ⛔ PAS UN NOMBRE ROND.
 *    À 100 % (gris PUR), DEUX ACCENTS SE CONFONDENT EXACTEMENT : le cyan de
 *    `GPU` (0x22d3ee) et le rose de `RAM` (0xf472b6) rendent TOUS LES DEUX
 *    la luminance 160/255. Mesuré, ⛔ pas supposé.
 *    ⇒ Les six couleurs que l'owner vient d'arbitrer en dn4-4 puis dn4-13
 *      redeviendraient CINQ en veille — c'est-à-dire le piège n°6 de cette
 *      story (« rendre deux choses indiscernables ») appliqué aux accents.
 *    ⇒ À 95 %, l'écart chromatique minimal remonte à 7/255 et les SEPT accents
 *      (les six cases + l'humidité d'`AMBIANCE`) redeviennent distincts. 7/255
 *      de teinte résiduelle ne se voit pas : ça reste « un état nuance de gris »
 *      au sens de la demande owner du 2026-08-25, sans détruire d'information.
 * ⚠️ `veille accents 100` reste disponible et RESTE le gris pur — la console DIT
 *    quelle paire il confond, calculé à l'exécution. AC9.4 tranche à l'œil.
 */
static int s_accent_amb_pct = 95;

bool dn_widget_set_accent_amb(int pct)
{
    if (pct < 0 || pct > 100) {
        return false;
    }
    s_accent_amb_pct = pct;
    return true;
}

int dn_widget_accent_amb(void) { return s_accent_amb_pct; }

/*
 * 🔴 L'ARITHMÉTIQUE EST **SÉPARÉE** DE LVGL, ET C'EST DÉLIBÉRÉ.
 *    Cette fonction ne prend ni ne rend de `lv_color_t` : elle est donc
 *    EXTRACTIBLE ET APPELABLE sur l'hôte par `tools/verif_veille_dn33.py`, qui
 *    la sort de CE fichier et la compile telle quelle. Si elle mélangeait du
 *    LVGL, la gate devrait fournir une coquille de `lv_color_hex` — et
 *    validerait alors un accord avec sa propre coquille.
 * ⛔ NE PAS la fusionner dans `dn_widget_accent_couleur()` : la gate cesserait
 *    de pouvoir l'exécuter et redeviendrait décorative.
 */
uint32_t dn_widget_desaturer(uint32_t rgb, int pct)
{
    if (pct <= 0) {
        return rgb & 0xFFFFFFu;
    }
    if (pct > 100) {
        pct = 100;
    }
    uint32_t r = (rgb >> 16) & 0xFFu, g = (rgb >> 8) & 0xFFu, b = rgb & 0xFFu;
    /*
     * ⚠️ ITU-R BT.601 (77/150/29 sur 256), ⛔ pas une moyenne des trois canaux.
     *    ⇒ LE MOTIF EST PERCEPTUEL, ET C'EST LE SEUL : BT.601 pondère les
     *      canaux comme l'œil les voit (le vert compte pour 59 %, le bleu pour
     *      11 %), une moyenne non. Un gris « juste » est celui qui garde la
     *      clarté RELATIVE des sept accents, ⛔ pas celui qui maximise le
     *      nombre de valeurs distinctes.
     * 🔴 ⛔ NE PAS RÉÉCRIRE ICI « ET D'AILLEURS LA MOYENNE CONFOND X » : CE
     *    COMMENTAIRE S'EST TROMPÉ DEUX FOIS SUR CE POINT PRÉCIS, ET LE COMPTAGE
     *    EST TENU AILLEURS.
     *    · 1ʳᵉ fois — il affirmait que la moyenne confondait `GPU`/`RAM` et que
     *      BT.601 les séparait : c'était L'INVERSE, corrigé le 2026-08-25.
     *    · 2ᵉ fois — il affirmait alors « les deux mappings confondent
     *      EXACTEMENT UNE PAIRE chacun … moyenne : `CPU`/humidité, tous deux à
     *      166 ». MESURÉ EN REVUE LE 2026-08-29 : `moy(CPU 0xa855f7) = 166`
     *      mais `moy(humidité 0x67e8f9) = 194`. Le 166 ne tombait juste qu'avec
     *      `0x35d6e8`, **la teinte de la métrique FICTIVE de démo** — le défaut
     *      AC6.1/AC6.2 exactement, laissé ici pendant qu'AC6.3 le corrigeait
     *      dans `dn_ui.c`. Sur le jeu RÉELLEMENT PEINT (6 cases + humidité), la
     *      moyenne ne confond RIEN et BT.601 confond `GPU`/`RAM` à 160.
     *    ⇒ LA PROPRIÉTÉ EST ÉPINGLÉE PAR `tools/verif_veille_dn33.py`
     *      (`bloc_accents`), qui la RE-MESURE à chaque passage. C'est LUI qui
     *      fait foi, ⛔ pas une phrase recopiée ici — « un motif faux dans un
     *      commentaire est un défaut au même titre qu'un chiffre faux », et
     *      celui-ci l'a prouvé deux fois.
     */
    uint32_t y = (r * 77u + g * 150u + b * 29u) >> 8;
    if (y > 255u) {
        y = 255u;
    }
    uint32_t k = (uint32_t)pct;
    /* Mélange linéaire vers le gris de luminance. L'arrondi est fait en entier
     * (`+ 50`) : sans lui, 100 % ne rendrait pas exactement `y` sur les canaux
     * les plus sombres, et le « gris pur » du défaut aurait gardé une teinte
     * résiduelle invisible en console mais présente à l'écran. */
    uint32_t rr = (r * (100u - k) + y * k + 50u) / 100u;
    uint32_t gg = (g * (100u - k) + y * k + 50u) / 100u;
    uint32_t bb = (b * (100u - k) + y * k + 50u) / 100u;
    return (rr << 16) | (gg << 8) | bb;
}

lv_color_t dn_widget_accent_couleur(uint32_t rgb)
{
    return lv_color_hex(
        dn_widget_desaturer(rgb, s_ambient ? s_accent_amb_pct : 0));
}

/*
 * ── dn3-3 : L'APLAT DE LA CASE EN AMBIENT ───────────────────────────────────
 * Gris TRÈS foncé, OPAQUE, sur un écran que le voile a passé au noir.
 * ⚠️ OPAQUE et pas translucide : en Actif l'aplat laisse voir le Living PCB
 *    (c'est l'identité du produit) ; en veille l'owner demande explicitement
 *    « blanc sur fond noir et sur fond gris foncé » — laisser le PCB
 *    transparaître donnerait un gris SALE au lieu d'un gris franc.
 * ⚠️ La bordure descend elle aussi : à `W_COL_BORDURE` (bleu clair) elle
 *    serait le seul élément coloré d'un écran monochrome, donc le premier que
 *    l'œil accroche — exactement l'inverse de ce qu'on veut en veille.
 */
/*
 * 🔴 **NOIR PUR**, ET C'EST UN CONSTAT OWNER SUR LA DALLE — ⛔ PAS UN CHOIX.
 *
 *    L'aplat est passé par TROIS valeurs avant celle-ci, et les deux premières
 *    ont été REJETÉES PAR L'ŒIL :
 *      `1E1E1E` ⇒ « les 6 cases sont pleines en VERT sur fond noir »
 *      `202020` ⇒ « vert plus foncé »   (pourtant |G8-R8| = 1)
 *      `000000` ⇒ ✅ « enfin propre — blanc sur noir, lisible »
 *
 * 🎯 CE QUE ÇA A APPRIS, ET QUI VAUT AU-DELÀ DE CETTE STORY : sur CETTE dalle,
 *    en RGB565, **AUCUN GRIS N'EST NEUTRE**. `scene gray`, écrite DIRECTEMENT
 *    dans le framebuffer (donc hors de tout code d'interface), le montre :
 *    constat owner du 2026-08-25, *« vert vers les tons sombres, violet vers le
 *    milieu et les tons clairs »* — ce que `dn_mire` annonce déjà comme le
 *    comportement NORMAL du RGB565 (le vert a 6 bits, le rouge et le bleu 5 :
 *    il prend puis rend son avance à chaque pas de la rampe).
 *
 * ⛔ LE CRITÈRE « |G8 - R8| <= 1 » NE SUFFIT DONC PAS, ET IL A ÉTÉ ESSAYÉ :
 *    `202020` le satisfait et tire quand même. Les SEULES valeurs vraiment
 *    neutres sont les extrémités — le noir (0,0,0) et le blanc (255,255,255).
 * ⇒ Un APLAT PLEIN d'Ambient se prend donc dans ces deux-là, et c'est le noir.
 *    La tuile est délimitée par sa BORDURE, pas par son remplissage.
 * ⚠️ CE QUI RESTE TEINTÉ, ET C'EST ASSUMÉ : les gris de TEXTE (`SIMULÉE`,
 *    `ABSENTE`) tirent aussi. Mais un trait fin ne teinte pas comme une surface
 *    pleine, et le constat owner sur ce rendu-ci est « lisible ». ⛔ Les
 *    ramener au blanc rendrait les trois régimes indiscernables — le défaut du
 *    2026-08-18. On garde les trois niveaux, et on DIT que c'est un compromis.
 */
#define W_AMB_CASE_BG 0x000000
#define W_AMB_CASE_BORD 0x3a3a3a

/*
 * ══ 🔴 LES GRIS NE SONT PAS NEUTRES EN RGB565 — MESURÉ SUR LA DALLE ═════════
 *
 * CONSTAT OWNER DU 2026-08-25, verbatim : *« les 6 cases sont pleines en VERT
 * sur fond noir »* — alors que l'instrument lisait `opa 255 · couleur 1E1E1E`
 * sur la racine de chaque case, et disait VRAI.
 *
 * 🔬 CE QUI L'A TRANCHÉ : poser du ROUGE PUR sur l'aplat. Les cases sont
 *    devenues rouges ⇒ le style atteint bien le rendu ⇒ `1E1E1E` ÉTAIT posé,
 *    et c'est LUI qui s'affiche vert.
 *
 * 🎯 LA CAUSE EST ARITHMÉTIQUE, ⛔ PAS UN BUG DE RENDU. En RGB565 le canal VERT
 *    porte **6 bits** quand le rouge et le bleu n'en portent que **5**. Un gris
 *    `R = G = B` ne survit donc pas à la quantification :
 *
 *      0x1E1E1E -> r=3  g=7   -> R 24  G 28  B 24   ecart vert **+4**
 *      0x565656 -> r=10 g=21  -> R 82  G 85  B 82   ecart vert **+3**
 *      0xFFFFFF -> r=31 g=63  -> R255  G255  B255   ecart **0**
 *
 * ⚠️ ET L'ŒIL AMPLIFIE PRÉCISÉMENT CET ÉCART-LÀ : la luminance BT.601 pèse le
 *    vert à **59 %**. Un résidu de +4/255 sur le canal le plus visible, dans les
 *    noirs profonds et à rétroéclairage réduit, ne se voit pas « un peu » : il
 *    se voit VERT.
 *
 * ⇒ TOUT GRIS D'AMBIENT SE CHOISIT PARMI LES VALEURS **RGB565-NEUTRES**
 *   (|G8 - R8| <= 1). `tools/verif_veille_dn33.py` le VÉRIFIE, et
 *   `veille gris` / `veille case` AVERTISSENT quand la valeur demandée ne l'est
 *   pas — ⛔ sans la refuser : c'est un instrument d'A/B, pas un garde-fou.
 * ⛔ NE PAS « arrondir au plus proche » en silence : l'owner doit voir la
 *    couleur qu'il tape, et savoir qu'elle tirera.
 */
/* 🔴 RÉGLABLE À CHAUD — né du constat owner du 2026-08-25 : « les 6 cases sont
 *    pleines en VERT sur fond noir », alors que l'instrument lit `opa 255 ·
 *    couleur 1E1E1E` sur la racine de chaque case. Un GRIS ne peut pas devenir
 *    vert (R=G=B est invariant par permutation de canaux) ⇒ ce qui est MESURÉ
 *    n'est pas ce qui est DESSINÉ, et il faut une couleur FRANCHE pour trancher.
 * ⚠️ C'est un instrument de bissection AVANT d'être un réglage. */
static uint32_t s_amb_case_bg = W_AMB_CASE_BG;

void dn_widget_set_amb_case_bg(uint32_t rgb) { s_amb_case_bg = rgb & 0xFFFFFFu; }
uint32_t dn_widget_amb_case_bg(void) { return s_amb_case_bg; }

void dn_widget_veille_appliquer(const dn_widget_desc_t *desc, dn_widget_t *w)
{
    (void)desc;
    if (!w || !w->racine) {
        return;
    }
    if (s_ambient) {
        lv_obj_set_style_bg_color(w->racine, lv_color_hex(s_amb_case_bg), 0);
        lv_obj_set_style_bg_opa(w->racine, LV_OPA_COVER, 0);
        lv_obj_set_style_border_color(w->racine, lv_color_hex(W_AMB_CASE_BORD),
                                      0);
    } else {
        /* ⛔ ON REPASSE PAR `aplat()`, ⛔ on ne recopie pas ses trois lignes :
         *    c'est LA définition de l'aplat, et la dupliquer ici ferait diverger
         *    le retour d'Ambient de la construction normale au premier
         *    `widget opa`. */
        aplat(w->racine);
    }

    /* Titre, icône et badge DISPARAISSENT en Ambient (décision owner). */
    lv_obj_t *const masquables[] = {w->titre, w->icone, w->badge};
    for (unsigned i = 0; i < sizeof(masquables) / sizeof(masquables[0]); i++) {
        if (!masquables[i]) {
            continue;
        }
        if (s_ambient) {
            lv_obj_add_flag(masquables[i], LV_OBJ_FLAG_HIDDEN);
        } else {
            lv_obj_clear_flag(masquables[i], LV_OBJ_FLAG_HIDDEN);
        }
    }
    /* ⚠️ LE BADGE EST UN CAS À PART AU RETOUR : il n'est visible que si la case
     *    est SIMULÉE. Le démasquer inconditionnellement ici afficherait
     *    « SIMULÉ » sur une case réelle. On le laisse à `dn_widget_maj()`, qui
     *    est le seul à connaître le régime — d'où le re-masquage immédiat. */
    if (!s_ambient && w->badge) {
        lv_obj_add_flag(w->badge, LV_OBJ_FLAG_HIDDEN);
    }

    if (w->jauge) {
        /* La jauge survit à la veille SI l'owner le veut (`veille jauge`). */
        if (s_ambient && !s_amb_jauge) {
            lv_obj_add_flag(w->jauge, LV_OBJ_FLAG_HIDDEN);
        } else {
            lv_obj_clear_flag(w->jauge, LV_OBJ_FLAG_HIDDEN);
        }
    }

}



/*
 * ── dn3-3 : LA GARDE DE TENUE, REJOUÉE APRÈS UNE BASCULE DE MODE ────────────
 *
 * 🔴 POURQUOI ELLE EXISTE. La garde d'origine ne tourne qu'à la CRÉATION — son
 *    coût (un `lv_text_get_size()` par grandeur) l'interdit dans le chemin
 *    chaud, qui passe 15 fois par seconde. Or la veille CHANGE LA POLICE SANS
 *    RECONSTRUIRE : sans ce rappel, un débordement d'Ambient serait **MUET**,
 *    et « 0 en HAUTEUR » se lirait comme une preuve alors que la garde n'aurait
 *    simplement jamais tourné.
 *
 * 🔴 ET ELLE S'APPELLE **APRÈS** `dn_widget_maj()`, ⛔ JAMAIS AVANT.
 *    Première version : elle tournait dans `dn_widget_veille_appliquer()`,
 *    c'est-à-dire AVANT la recomposition des textes. Elle mesurait donc le
 *    texte D'AVANT et publiait un verdict sur l'état D'APRÈS — sur `veille
 *    unite off` elle a accusé « 4,4 Mb/s » de faire 243 px alors que la valeur
 *    venait de perdre son « Mb/s ». Un instrument qui mesure l'ancien état et
 *    conclut sur le nouveau est exactement la classe de défaut que ce dépôt
 *    traque, et il l'a trouvé sur la carte le 2026-08-25.
 *
 * ⚠️ UNE FOIS PAR BASCULE, ⛔ pas 15 fois par seconde.
 */
void dn_widget_controler_tenue(const dn_widget_desc_t *desc, dn_widget_t *w)
{
    if (!w || !w->racine) {
        return;
    }
    int h = lv_obj_get_height(w->racine);
    int lignes = dn_widget_lignes(s_geom.dispo, w->n);
    int lh = (int)lv_font_get_line_height(font_val());
    int bas = val_y_courant() + (lignes > 0 ? lignes - 1 : 0) * val_pas_courant()
              + lh;
    if (h > 0 && bas > h) {
        s_debordements++;
        ESP_LOGW(TAG,
                 "« %s » : la bascule de mode fait DEBORDER la case — bas %d > "
                 "h=%d (%d ligne(s) x pas %d, police lh %d, val_y %d). LVGL "
                 "CLIPPE sans un mot : la case montrera moins qu'elle ne "
                 "declare. ⇒ `veille unite on` remet la police a 33 px.",
                 desc && desc->titre ? desc->titre : "?", bas, h, lignes,
                 val_pas_courant(), lh, val_y_courant());
    }
    for (int i = 0; i < DN_WIDGET_GRANDEURS_MAX; i++) {
        if (!w->valeur[i]) {
            continue;
        }
        int lw = dn_widget_largeur(lv_label_get_text(w->valeur[i]), font_val());
        int utile = dn_widget_largeur_utile(w->w);
        if (lw > utile) {
            s_trop_larges++;
            ESP_LOGW(TAG,
                     "« %s » rang %d : la bascule de mode le rend TROP LARGE — "
                     "« %s » mesure %d px pour %d utiles, il manque %d px. LVGL "
                     "le CLIPPE sans un mot.",
                     desc && desc->titre ? desc->titre : "?", i,
                     lv_label_get_text(w->valeur[i]), lw, utile, lw - utile);
        }
    }
}

void dn_widget_repeindre_accents(const dn_widget_desc_t *desc, dn_widget_t *w)
{
    if (!desc || !w) {
        return;
    }
    lv_color_t c = dn_widget_accent_couleur(desc->couleur);
    if (w->icone) {
        lv_obj_set_style_text_color(w->icone, c, 0);
    }
    if (w->jauge) {
        lv_obj_set_style_bg_color(w->jauge, c, LV_PART_INDICATOR);
    }
}

lv_color_t dn_val_regime_couleur(dn_val_regime_t r)
{
    /* ⚠️ LE MODE EST TESTÉ D'ABORD, MAIS LES TROIS RÉGIMES RESTENT TROIS DANS
     *    LES DEUX MODES. Un `if (ambient) return gris_unique;` aurait été plus
     *    court d'une ligne et aurait REFAIT le défaut du 2026-08-18. */
    if (s_ambient) {
        switch (r) {
        case DN_VAL_REELLE:
            return lv_color_hex(s_gris_amb[DN_VAL_REELLE]);
        case DN_VAL_SIMULEE:
            return lv_color_hex(s_gris_amb[DN_VAL_SIMULEE]);
        default:
            return lv_color_hex(s_gris_amb[DN_VAL_ABSENTE]);
        }
    }
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
 * L'UNITÉ QUI S'APPLIQUE — voir `dn_widget.h` pour le motif (elle était
 * concaténée à TROIS endroits, et la bascule Mb/s → Gb/s a rendu la divergence
 * visible à la première mesure).
 * ⚠️ Si `unite_haute` manque là où le drapeau est posé, on retombe sur l'unité
 *    de BASE plutôt que sur RIEN : une valeur convertie SANS unité serait pire
 *    que non convertie.
 */
const char *dn_widget_unite(const dn_widget_desc_t *d,
                            const dn_widget_etat_t *e, int i)
{
    if (!d || i < 0 || i >= DN_WIDGET_GRANDEURS_MAX) {
        return NULL;
    }
    if (e && e->echelle_haute[i] && d->grandeurs[i].unite_haute) {
        return d->grandeurs[i].unite_haute;
    }
    return d->grandeurs[i].unite;
}

/*
 * Le texte d'une grandeur : [icône ][préfixe ]valeur[ unité].
 *
 * ⛔ Une valeur ABSENTE ne porte JAMAIS son unité (« -- % » suggérerait qu'on
 *    sait de quoi on parle) — ✅ mais elle GARDE son préfixe : « c.max -- » dit
 *    QUELLE grandeur manque, et taire le préfixe cacherait l'existence même de
 *    la grandeur, ce que W10 interdit explicitement.
 */
/* 🔴 dn4-9 : `g` EST UN **INDEX DE GRANDEUR**, ⛔ PLUS UN RANG D'AFFICHAGE.
 *    Les deux coïncidaient jusqu'ici ; la sélection les sépare. Le paramètre a
 *    été RENOMMÉ (`i` -> `g`) exprès : un nom qui ment est ce qui fait écrire
 *    `etat->txt[rang]` six mois plus tard. `grandeurs[g]` et `etat->txt[g]`
 *    décrivent la MÊME grandeur — c'est l'invariant du mécanisme. */
static void composer(const dn_widget_desc_t *d, const dn_widget_etat_t *e, int g,
                     char *out, size_t n)
{
    if (g < 0 || g >= DN_WIDGET_GRANDEURS_MAX) {
        snprintf(out, n, "--");
        return;
    }
    /*
     * 🔴 dn3-3 — EN AMBIENT, LA CASE NE PORTE PLUS QUE SA VALEUR.
     *    Ni icône, ni PRÉFIXE de grandeur : décision owner du 2026-08-25
     *    (« titre et icônes disparaissent, chiffres agrandis »). Le préfixe
     *    n'est pas un détail cosmétique — c'est LUI qui plafonnait
     *    l'agrandissement à +2 % (« c.max 100,0 % » = 197 px pour 201 utiles).
     * ⚠️ L'ABSENCE reste « -- », ⛔ jamais vide : une case vide se lit
     *    « l'écran est mort », un « -- » se lit « la source ne dit rien ».
     */
    if (s_ambient) {
        const char *ua = s_amb_unite ? dn_widget_unite(d, e, g) : NULL;
        if (!e || e->regime == DN_VAL_ABSENTE || e->txt[g][0] == '\0') {
            snprintf(out, n, "--");
        } else {
            snprintf(out, n, "%s%s%s", e->txt[g], ua ? " " : "", ua ? ua : "");
        }
        return;
    }
    const char *ic = d->grandeurs[g].icone;
    /* 🔴 dn4-9 : `false` = la CASE. Un préfixe marqué `prefixe_detail_seul` n'y
     *    est PAS affiché — il n'y tient pas (MESURÉ : 315 px pour 201) et il n'y
     *    est pas nécessaire (une seule grandeur de cette unité y est montrée).
     *    Voir `dn_widget_prefixe()`. */
    const char *px = dn_widget_prefixe(d, g, false);
    if (!e || e->regime == DN_VAL_ABSENTE || e->txt[g][0] == '\0') {
        snprintf(out, n, "%s%s%s%s--", ic ? ic : "", ic ? " " : "",
                 px ? px : "", px ? " " : "");
        return;
    }
    const char *u = dn_widget_unite(d, e, g);
    snprintf(out, n, "%s%s%s%s%s%s%s", ic ? ic : "", ic ? " " : "",
             px ? px : "", px ? " " : "", e->txt[g], u ? " " : "", u ? u : "");
}

/*
 * ── dn4-9 : LA SEULE TRADUCTION RANG -> INDEX ────────────────────────────────
 * Voir `dn_widget.h` pour le motif et la convention du décalage de 1.
 */
int dn_widget_sel(const dn_widget_desc_t *d, int rang)
{
    if (!d || rang < 0 || rang >= DN_WIDGET_GRANDEURS_MAX) {
        return -1;
    }
    uint8_t p1 = d->sel_p1[rang];
    if (p1 == 0 || p1 > DN_WIDGET_GRANDEURS_MAX) {
        /* 0 = non déclaré ⇒ identité (le défaut, cinq cases sur six).
         * Hors bornes ⇒ identité AUSSI, et c'est l'audit de boot de `dn_ui.c`
         * qui le NOMME : ici on est sur le chemin chaud (15 passages/s). */
        return rang;
    }
    return (int)p1 - 1;
}

int dn_widget_n_detail(const dn_widget_desc_t *d)
{
    if (!d) {
        return 0;
    }
    return d->n_detail ? (int)d->n_detail : (int)d->n_grandeurs;
}

int dn_widget_detail_cols(const dn_widget_desc_t *d)
{
    if (!d || d->detail_cols < 1) {
        return 2; /* le défaut posé par dn4-6 */
    }
    return (d->detail_cols > 2) ? 2 : (int)d->detail_cols;
}

const char *dn_widget_prefixe(const dn_widget_desc_t *d, int g, bool detail)
{
    if (!d || g < 0 || g >= DN_WIDGET_GRANDEURS_MAX) {
        return NULL;
    }
    if (!detail && d->grandeurs[g].prefixe_detail_seul) {
        return NULL;
    }
    return d->grandeurs[g].prefixe;
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
/* ⚠️ dn4-9 : `i` est le **RANG** (c'est lui qui décide la position), et `g`
 *    l'index de grandeur — utilisé UNIQUEMENT par le log, pour qu'il envoie
 *    chercher le défaut dans la bonne entrée de `k_desc[]`. */
static void valeur_placer(lv_obj_t *lbl, int i, int g, int n, int w,
                          int fin_gauche, const dn_widget_desc_t *desc,
                          int *fin_gauche_out)
{
    int ligne = 0, col = 0, cols = 1;
    place(s_geom.dispo, n, i, &ligne, &col, &cols);
    int y = val_y_courant() + ligne * val_pas_courant();

    /*
     * 🔴 ON NE REPOSE LA POSITION QUE SI ELLE CHANGE — CONSTAT OWNER DU
     *    2026-08-19 : *« l'image tressaute à chaque seconde »*.
     *
     *    `dn_widget_maj` appelait `lv_obj_set_pos()` sur CHAQUE grandeur à
     *    CHAQUE mise à jour, y compris en `EMPILE` où le `x` ne bouge JAMAIS —
     *    soit 15 repositionnements par seconde en régime (5 trames/s × 3
     *    grandeurs) qui ne déplacent rien.
     * ⚠️ ET CE N'EST PAS GRATUIT : `lv_obj_set_pos()` marque la disposition du
     *    parent comme SALE. La passe de layout qui en résulte tourne **hors** du
     *    bloc où l'invalidation est coupée (le groupage d'AC8), donc ses propres
     *    invalidations échappent à la zone unique que le groupage prépare.
     * ⛔ C'EST NEUF DANS dn4-6 : jusqu'ici aucune mise à jour ne repositionnait
     *    un label. Le côte à côte l'exige (la colonne droite est calée à droite,
     *    donc son `x` dépend de la largeur du texte) — mais SEULEMENT le côte à
     *    côte, et seulement quand le texte change de largeur.
     * ⚠️ HYPOTHÈSE, pas certitude : elle se falsifie à l'œil, et la voie est
     *    commutable (`widget dispo`). Si le tressautement persiste en `EMPILE`
     *    avec ce correctif, la cause est AILLEURS et il faudra le dire.
     */
    if (cols < 2 || col == 0) {
        if (lv_obj_get_x(lbl) != W_PAD || lv_obj_get_y(lbl) != y) {
            lv_obj_set_pos(lbl, W_PAD, y);
        }
        /* 🔴 LA LARGEUR N'EST MESURÉE QUE S'IL Y A UNE COLONNE DROITE À CALER.
         *    Elle l'était pour CHAQUE grandeur, y compris en `EMPILE` où
         *    personne ne la lit — soit **15 `lv_text_get_size()` par seconde**
         *    en régime, sous le verrou LVGL, pour rien. `lv_text_get_size()`
         *    parcourt la chaîne, cherche chaque glyphe dans les cmaps (dont une
         *    SPARSE) et applique le crénage : ce n'est pas une lecture de champ.
         * ⚠️ `cols >= 2 && col == 0` est la SEULE situation où `fin_gauche`
         *    servira : la grandeur suivante est sur la même ligne, à droite.
         * 🔴 ⛔ ET CE RETOUR SEC EST EXACTEMENT CE QUI LAISSAIT LA DISPOSITION
         *    LIVRÉE SANS INSTRUMENT DE LARGEUR (revue 2026-08-19) : en `EMPILE`
         *    on passe toujours ici, donc `s_chevauchements` restait à zéro quoi
         *    qu'il arrive. La détection existe désormais, mais À LA CONSTRUCTION
         *    (`dn_widget_creer`, compteur `s_trop_larges`) — ⛔ surtout pas ici,
         *    où elle rendrait au chemin chaud le coût qu'on vient d'en retirer. */
        if (fin_gauche_out && cols >= 2) {
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
                 "« %s » rang %d (grandeur %d) : CHEVAUCHEMENT cote a cote — "
                 "la colonne GAUCHE finit a %d px, et « %s » (%d px, calee a "
                 "DROITE) commencerait a %d px : il manque %d px (gouttiere %d, "
                 "utile %d px). LVGL clipperait SANS un mot.",
                 desc && desc->titre ? desc->titre : "?", i, g, fin_gauche,
                 lv_label_get_text(lbl), lw, x, fin_gauche + W_GOUTTIERE - x,
                 W_GOUTTIERE, dn_widget_largeur_utile(w));
        /* ⛔ On pose QUAND MÊME, à la place demandée : masquer la valeur ou la
         *    tronquer serait remplacer un défaut visible par un défaut muet.
         *    Le log et le compteur sont l'instrument ; l'œil de l'owner tranche. */
    }
    if (lv_obj_get_x(lbl) != x || lv_obj_get_y(lbl) != y) {
        lv_obj_set_pos(lbl, x, y);
    }
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
        /* 🔴 dn3-3 : RETENUE (pour l'A/B à chaud d'AC9.4) et posée avec la
         *    couleur DU MODE COURANT, ⛔ pas `lv_color_hex(desc->couleur)` en
         *    dur. Une reconstruction PENDANT la veille (`widget opa`, `nav
         *    model`…) aurait sinon reposé les six accents en COULEURS sur un
         *    module endormi, sans qu'aucune bascule n'ait eu lieu. */
        out->icone = dn_widget_texte(out->racine, desc->icone, font_entete(),
                                     dn_widget_accent_couleur(desc->couleur),
                                     tx, entete_y_icone());
        tx += (s_geom.entete == DN_ENTETE_COMPACT) ? W_ICONE_AV_14 : W_ICONE_AV_28;
    }
    /* 🔴 dn3-3 : RETENU, pour pouvoir DISPARAÎTRE en Ambient sans reconstruire
     *    la scène (307-322 ms verrou tenu). Même motif que `out->icone`. */
    out->titre = dn_widget_texte(out->racine, desc->titre, font_titre(),
                                 lv_color_hex(W_COL_TITRE), tx, entete_y_titre());
    /*
     * 🔴 dn4-14-2 / AC5.3 — LE TITRE EST ENFIN CONTRÔLÉ, ET IL NE L'ÉTAIT PAS.
     *    MESURÉ le 2026-08-29 sur le firmware d'AVANT : « DÉMO 2+JAUGE » occupe
     *    **114 px pour 107 utiles** et **déborde de 7 px dans la réserve du
     *    badge** — avec les TROIS compteurs à **ZÉRO**. ⛔ *« se fait clipper de
     *    7 px »* était écrit ici et c'est FAUX : LVGL ne clippe qu'au bord de la
     *    zone, à 173 px (voir `W_BADGE_DE_DROITE`). Le défaut trouvé est une
     *    **absence de GARDE**, ⛔ pas un artefact visible sur ce stimulus-là. `dn_widget_controler_tenue()` teste « le texte de
     *    VALEUR sort-il de la case » et **ne regarde pas le titre**. Un
     *    compteur à zéro n'était donc pas une absence d'histoire : c'était une
     *    absence de GARDE.
     * ⛔ ON POSE QUAND MÊME, à la place demandée — même doctrine que la valeur
     *    trop large : masquer ou tronquer remplacerait un défaut VISIBLE par un
     *    défaut MUET. Le log et le compteur sont l'instrument ; l'œil tranche.
     * ⚠️ IL RÉUTILISE `trop_larges`, ⛔ il n'ajoute PAS un quatrième compteur :
     *    « un texte plus large que son emplacement » est exactement ce que ce
     *    compteur nomme, et les trois restent trois.
     */
    {
        int t_utile = dn_widget_titre_utile(w, desc->icone != NULL);
        int t_px = dn_widget_largeur(desc->titre, font_titre());
        if (t_px > t_utile) {
            s_trop_larges++;
            ESP_LOGW(TAG,
                     "TITRE trop large : « %s » = %d px pour %d utiles "
                     "(x %d, badge a %d) — CHEVAUCHE LA RESERVE DU BADGE "
                     "(visible seulement si la case est SIMULEE ; LVGL ne "
                     "clippe qu'au bord de zone, a %d px)",
                     desc->titre ? desc->titre : "?", t_px, t_utile, tx,
                     w - W_BADGE_DE_DROITE, w - dn_widget_titre_x(desc->icone != NULL));
        }
    }

    /* Le badge de régime — CRÉÉ TOUJOURS, masqué quand il ne s'applique pas.
     * Le créer à la demande obligerait `dn_widget_maj` à construire des objets
     * LVGL, donc à allouer, sous le verrou et depuis une tâche de source. Un
     * `lv_obj_add_flag(HIDDEN)` ne peut pas échouer ; un `lv_label_create` si. */
    out->badge = dn_widget_texte(out->racine, "SIMULÉ", &dn_font_14,
                                 lv_color_hex(W_COL_SIMULEE),
                                 w - W_BADGE_DE_DROITE, entete_y_badge());
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
        /* 🔴 dn4-9 : `i` est le RANG, `g` la GRANDEUR. Ils ne coïncident plus.
         *    ⛔ La MÊME traduction doit être appliquée dans `dn_widget_maj`,
         *    sans quoi la mise à jour recomposerait une autre grandeur que celle
         *    qui vient d'être créée — et rien ne le dirait, parce que le
         *    garde-fou de `maj` est le POINTEUR `valeur[i]`, pas le compte. */
        int g = dn_widget_sel(desc, i);
        composer(desc, etat, g, buf, sizeof(buf));
        out->valeur[i] = dn_widget_texte(
            out->racine, buf, font_val(),
            dn_val_regime_couleur(etat ? etat->regime : DN_VAL_ABSENTE), W_PAD,
            val_y_courant());
        valeur_placer(out->valeur[i], i, g, n, w, fin_gauche, desc, &fin_gauche);
        /* 🔴 LA VALEUR QUI NE TIENT PAS EN HAUTEUR — voir `dn_widget.h`.
         *    Le bas de la BOÎTE, ⛔ pas le `y` posé : un texte posé à 128 dans
         *    une case de 156 « a l'air » dedans et déborde de 7 px. */
        int ligne = 0, col = 0, cols = 1;
        place(s_geom.dispo, n, i, &ligne, &col, &cols);
        int bas = val_y_courant() + ligne * val_pas_courant() + lh_val;
        if (bas > h) {
            hors++;
            dernier_bas = bas;
        }
        /* 🔴 ET LA VALEUR QUI NE TIENT PAS EN LARGEUR **SEULE** — le trou que le
         *    côte à côte cachait (revue de code du 2026-08-19). `valeur_placer()`
         *    ne mesure la largeur que s'il y a une colonne DROITE à caler ; en
         *    `EMPILE`, la disposition LIVRÉE, il n'y en a aucune, donc rien
         *    n'était mesuré — et `dn_widget_chevauchements()` promettait pourtant
         *    de compter « ça ne tient pas en LARGEUR ». La marge est mince et
         *    MESURÉE : « c.max 100,0 % » = 197 px pour 201 utiles.
         * ⚠️ ICI ET PAS DANS `dn_widget_maj` : à la construction, la mesure est
         *    payée une fois par reconstruction ; dans la MAJ elle rajouterait les
         *    15 `lv_text_get_size()` par seconde sous le verrou que dn4-6 vient
         *    justement de retirer du chemin chaud. */
        if (cols < 2) {
            int lw_val = dn_widget_largeur(buf, font_val());
            int utile = dn_widget_largeur_utile(w);
            if (lw_val > utile) {
                s_trop_larges++;
                ESP_LOGW(TAG,
                         "« %s » rang %d (grandeur %d) : TROP LARGE en colonne "
                         "unique — « %s » mesure %d px pour %d utiles (case %d, "
                         "marges 2x%d) : il manque %d px. LVGL la CLIPPE sans un "
                         "mot.",
                         desc->titre ? desc->titre : "?", i, g, buf, lw_val, utile,
                         w, W_PAD, lw_val - utile);
            }
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
                 dn_widget_lignes(s_geom.dispo, n), val_pas_courant(), lh_val,
                 val_y_courant(), dn_widget_dispo_nom(s_geom.dispo));
    }

    /* 🔴 `y_bas` SE CALCULE SUR LES LIGNES, PAS SUR LES GRANDEURS. En côte à
     *    côte quatre grandeurs tiennent en DEUX lignes — et confondre les deux
     *    ferait abandonner une jauge qui a la place, ou en poser une qui ne l'a
     *    pas. C'est le même nombre qui gouverne la jauge et la secondaire. */
    int n_lignes = dn_widget_lignes(s_geom.dispo, n);
    int y_bas = val_y_courant() + n_lignes * val_pas_courant();
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
        /* dn3-3 : même règle que l'icône — la couleur DU MODE, ⛔ pas la
         * couleur brute du descripteur. */
        lv_obj_set_style_bg_color(out->jauge,
                                  dn_widget_accent_couleur(desc->couleur),
                                  LV_PART_INDICATOR);
        lv_obj_set_style_bg_opa(out->jauge, LV_OPA_COVER, LV_PART_INDICATOR);
        lv_bar_set_value(out->jauge, etat ? etat->brut[0] : desc->ind_min,
                         LV_ANIM_OFF);
        y_bas += W_JAUGE_H + 10;
    }

    if (y_bas + sec_h() <= h) {
        out->sec = dn_widget_texte(out->racine,
                                   (etat && etat->secondaire[0]) ? etat->secondaire
                                                                 : "",
                                   dn_widget_font_libelle(),
                                   lv_color_hex(W_COL_SEC), W_PAD,
                                   y_bas + W_SEC_Y_OFF);
    } else {
        /*
         * 🔴 dn4-1 / W5 — L'ABANDON DE LA SECONDAIRE NE PEUT PLUS ÊTRE
         *    SILENCIEUX. C'est le PIÈGE que le correctif de la jauge arme :
         *    à n = 2 AVEC jauge, y_bas vaut 148 et 148 + 20 = 168 > 163, donc
         *    `out->sec` reste NULL et `dn_widget_maj` saute le bloc — exactement
         *    la même panne muette, un cran plus loin, et pas plus visible.
         *    La règle de priorité est écrite dans `dn_widget.h` (la jauge gagne,
         *    parce qu'elle est demandée par un champ explicite du descripteur) ;
         *    ici on la REND AUDIBLE. Un descripteur qui perd sa ligne secondaire
         *    doit le dire à qui lit les logs, pas se taire.
         *
         * 🔴 ⚠️ CE LOG N'EST PLUS INCONDITIONNEL — REVUE DE CODE DU 2026-08-19.
         *    Il disait de lui-même : *« rare PAR CONSTRUCTION ; s'il apparaît en
         *    rafale, c'est qu'un descripteur a changé — et c'est le signal »*.
         *    LE DESCRIPTEUR A CHANGÉ : à trois grandeurs dans une case de 163,
         *    `y_bas` vaut 168 et **`CPU` comme `GPU` tombent ici à CHAQUE
         *    reconstruction**, alors qu'aucune des deux ne demande de secondaire.
         *    Le signal était devenu l'état nominal, c'est-à-dire du bruit — et
         *    une garde qu'on apprend à ignorer ne garde plus rien (c'est la
         *    doctrine que `1a31a9d` venait d'appliquer au détail).
         * ⇒ On journalise ici **la place refusée à une secondaire RÉELLEMENT
         *    DEMANDÉE**, et `dn_widget_maj` journalise, une seule fois par
         *    widget, **le texte réellement PERDU** quand il arrive plus tard.
         *    Deux moments, deux messages, aucun bruit de fond.
         */
        if (etat && etat->secondaire[0]) {
            ESP_LOGW(TAG,
                     "« %s » : pas de place pour la ligne secondaire "
                     "(y_bas=%d + %d > h=%d) — %d grandeur(s) sur %d ligne(s), "
                     "disposition %s%s. La jauge est prioritaire "
                     "(contrat dn_widget.h / W5). Texte PERDU : « %s ».",
                     desc->titre ? desc->titre : "?", y_bas, sec_h(), h, n,
                     n_lignes, dn_widget_dispo_nom(s_geom.dispo),
                     (desc->indicateur && jauge_place) ? " + jauge" : "",
                     etat->secondaire);
            out->sec_perdue_dite = true;
        } else {
            ESP_LOGD(TAG,
                     "« %s » : aucune ligne secondaire posee (y_bas=%d + %d > "
                     "h=%d) — et le descripteur n'en demande pas.",
                     desc->titre ? desc->titre : "?", y_bas, sec_h(), h);
        }
    }

    /* Poser l'état une fois de plus : c'est LUI qui décide de la visibilité du
     * badge et de la couleur, et le refaire ici garantit qu'une case construite
     * et une case mise à jour passent EXACTEMENT par le même code. Deux chemins
     * de rendu pour un même état, c'est deux endroits où ils divergent. */
    dn_widget_maj(desc, etat, out);
}

/*
 * TOUS LES ENFANTS QUE `dn_widget_maj()` ECRIT — ⛔ pas seulement les valeurs.
 * Pose le 2026-08-27 : la liste etait implicite et INCOMPLETE aux deux passes
 * de l'union (jauge et badge manquaient). L'avoir en UN SEUL endroit est ce qui
 * empeche les deux passes de diverger, et ce qui rend l'oubli visible le jour
 * ou `dn_widget_maj()` gagnera un enfant.
 * ⚠️ CE QUE CA COUTE, ET IL FAUT LE DIRE : la zone d'union s'approche desormais
 *    du conteneur entier, puisqu'elle englobe la jauge (en bas) et le badge (en
 *    haut). Le gain d'aire du mode `union` sur le mode `on` est donc PLUS PETIT
 *    qu'avant — mais avant, il etait obtenu en NE REPEIGNANT PAS des enfants
 *    qu'on venait d'ecrire. ⛔ Une aire plus petite obtenue en perdant des
 *    pixels n'est pas un gain, c'est un defaut.
 */
static void zone_widget_prendre(const dn_widget_t *w, lv_area_t *zone, bool *vide)
{
    for (int i = 0; i < DN_WIDGET_GRANDEURS_MAX; i++) {
        zone_prendre(zone, vide, w->valeur[i]);
    }
    zone_prendre(zone, vide, w->jauge);
    zone_prendre(zone, vide, w->sec);
    zone_prendre(zone, vide, w->badge);
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
    /* dn4-10 : `union` coupe l'invalidation comme `on` — la différence est
     * UNIQUEMENT dans la zone qu'on salit à la sortie. */
    bool grouper = (s_groupage || s_groupe_union) && disp != NULL;
    lv_area_t zone_union;
    bool zone_vide = true;
    if (grouper && s_groupe_union) {
        /*
         * AVANT écriture : la boîte que les enfants OCCUPENT ENCORE. Un texte
         * qui raccourcit, une jauge qui recule, un badge qui va disparaître
         * laissent leur trace ICI et nulle part ailleurs.
         *
         * 🔴 CORRIGÉ LE 2026-08-27 (2ᵉ revue de code) — ⛔ CETTE BOUCLE NE
         *    PRENAIT QUE `w->valeur[i]`. Entre les deux passes, la fonction
         *    écrit AUSSI `lv_bar_set_value(w->jauge, …)` et bascule
         *    `w->badge` — pendant que `lv_display_enable_invalidation(disp,
         *    false)` court. Géométrie relue : la jauge est posée à `y_bas + 6`
         *    et le badge à `entete_y_badge()`, TOUS DEUX HORS de la boîte des
         *    valeurs. ⛔ Et contrairement aux labels, ni `lv_bar` ni le drapeau
         *    `HIDDEN` n'ont de filet différé : `lv_bar_set_value(…, LV_ANIM_OFF)`
         *    n'émet qu'un `lv_obj_invalidate(obj)` (lv_bar.c:748) et
         *    `lv_obj_add_flag(HIDDEN)` de même (lv_obj.c:262) — tous deux
         *    AVALÉS. ⇒ la jauge GELAIT à sa dernière valeur peinte et le badge
         *    « SIMULÉ » restait ou ne venait pas. Cas vivant : `DN_UI_CASE_RAM`
         *    (`dn_ui.c`, `.indicateur = true`).
         * 🔴 ET ÇA INVALIDE UNE CONCLUSION PUBLIÉE : `union` a été mesuré à
         *    0,97 /s puis déclaré « voie morte » (§20.7.19) — DANS CET ÉTAT
         *    CASSÉ. ⛔ Le chiffre ne vaut plus ; il est à reprendre sur la carte.
         */
        zone_widget_prendre(w, &zone_union, &zone_vide);
    }
    if (grouper) {
        if (s_groupe_union) {
            /*
             * 🔴 REMONTÉ ICI LE 2026-08-27 (3e revue) — ⛔ IL ÉTAIT DANS LA
             *    FENÊTRE COUPÉE, ET IL Y MANGEAIT LES RÉPARATIONS DES AUTRES.
             *    `lv_obj_update_layout()` ne travaille PAS sur `w->racine` : il
             *    remonte à l'ÉCRAN (lv_obj_pos.c:388) et envoie
             *    `LV_EVENT_UPDATE_LAYOUT_COMPLETED` **AU DISPLAY**. Or CHAQUE
             *    label de l'écran qui a un `need_refr_text` en attente s'y est
             *    abonné (lv_label.c:1071) ; son callback SE DÉSABONNE
             *    (lv_label.c:1081) puis appelle `lv_label_refr_text()`, qui
             *    finit par `lv_obj_invalidate()` (lv_label.c:1354).
             *    ⇒ appelé DANS la fenêtre coupée, il consommait — et AVALAIT —
             *    la réparation différée de labels qui n'appartiennent PAS à ce
             *    widget, DÉFINITIVEMENT, puisqu'ils venaient de se désabonner.
             *    Cibles vivantes : la barre heure/date et la vue DÉTAIL.
             * 🔴 ET ÇA RENVERSAIT UNE RÉFUTATION DE LA REVUE DU 2026-08-24, qui
             *    avait écarté « `w->sec` est perdu en `union` » au motif que les
             *    labels « s'auto-réparent HORS de la fenêtre coupée ». Le
             *    correctif du 2026-08-27 avait déplacé le déclencheur DEDANS.
             * 🎯 CE QUE LE DÉPLACEMENT COÛTE, ET C'EST ASSUMÉ : la géométrie est
             *    forcée AVANT la coupure, donc les invalidations que le layout
             *    déclenche pour CE widget ne sont plus avalées — une zone sale
             *    de plus, au pire. ⛔ En échange, la seconde passe lit bien les
             *    NOUVELLES coordonnées (c'était la raison d'être du correctif)
             *    ET les labels des autres gardent leur réparation.
             */
            lv_obj_update_layout(w->racine);
        }
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
        /* 🔴 dn4-9 — LE POINT LE PLUS FACILE À RATER DE TOUT LE MÉCANISME.
         *    Cette boucle ⛔ NE parcourt PAS `0..n-1` : elle parcourt les QUATRE
         *    slots et filtre par le POINTEUR. Son `i` est donc un RANG (le slot
         *    n'existe que si `dn_widget_creer` l'a créé), et il faut lui
         *    appliquer LA MÊME traduction qu'à la création. Sans elle, la case
         *    afficherait la bonne grandeur à la construction puis une AUTRE dès
         *    la première mise à jour — 5 fois par seconde, sans un log.
         * ⚠️ Cadence MESURÉE le 2026-08-24 (dn4-4/AC3) : 5,0 poussées/s pour les
         *    CINQ métriques. ⛔ Ne pas la transposer à `detail_reparametrer()`,
         *    qui ne sert QUE la métrique affichée et tourne à 1,0/s. */
        int g = dn_widget_sel(desc, i);
        composer(desc, etat, g, buf, sizeof(buf));
        /* 🔴 dn3-3 : LA POLICE EST REPOSÉE SI LE MODE L'A CHANGÉE. Elle n'est
         *    fixée qu'À LA CRÉATION, et la veille en change (28 -> 33 ou 56).
         * ⚠️ CONDITIONNÉ À L'ÉCART, ⛔ pas écrit à chaque passage : ce chemin
         *    tourne 5 fois par seconde en régime (mesuré le 2026-08-24), et
         *    `lv_obj_set_style_text_font` invalide le label à chaque appel. */
        if (lv_obj_get_style_text_font(w->valeur[i], 0) != font_val()) {
            lv_obj_set_style_text_font(w->valeur[i], font_val(), 0);
        }
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
        /* ⛔ `w->w` N'EST PLUS REMPLACÉ PAR UN 225 RÉCITÉ (revue 2026-08-19) :
         *    le dépôt écrit « toute valeur affichée est RELUE de l'état réel,
         *    jamais récitée d'une constante », et ce module vient de purger les
         *    siennes. Un widget sans largeur mémorisée n'a pas été construit par
         *    `dn_widget_creer` — le caler sur une largeur DEVINÉE placerait la
         *    colonne droite au mauvais endroit sans que rien ne le dise. On ne
         *    repositionne pas : ce qui a été POSÉ fait foi. */
        if (s_replacer && w->w > 0) {
            valeur_placer(w->valeur[i], i, g, w->n ? w->n : 1, w->w, fin_gauche,
                          desc, &fin_gauche);
        }
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
        /* ⚠️ dn4-9 : `txt[g]`, ⛔ pas `txt[i]` — l'état est indexé par GRANDEUR.
         *    Lire au rang aurait grisé la mauvaise ligne sur `CPU` : son rang 2
         *    est la grandeur 3, et `txt[2]` (le `c.max`, qui reste alimenté)
         *    n'est jamais vide ⇒ une °C absente se serait peinte en BLANC,
         *    c'est-à-dire présentée comme une mesure. */
        bool grandeur_vide = !etat || g < 0 || etat->txt[g][0] == '\0';
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
    } else if (etat && etat->secondaire[0] && !w->sec_perdue_dite) {
        /* 🔴 LA PERTE EST DITE LÀ OÙ ELLE A LIEU (revue 2026-08-19). Sans ce
         *    bloc, un texte secondaire qui arrive APRÈS la construction sur une
         *    case dont la géométrie n'a pas gardé la ligne disparaissait sans un
         *    mot — la panne muette que le log de `dn_widget_creer` existe pour
         *    fermer, déplacée d'un cran. ⚠️ UNE SEULE FOIS par widget : en régime
         *    ce chemin est parcouru 5 fois par seconde (cadence MESURÉE le
         *    2026-08-24, dn4-4/AC3 — les CINQ métriques), et le port série EST le
         *    transport. */
        w->sec_perdue_dite = true;
        ESP_LOGW(TAG,
                 "« %s » : texte secondaire PERDU — la geometrie n'a pas garde "
                 "la ligne (voir le log de construction). Texte : « %s ». "
                 "⚠️ Ce message ne sortira qu'UNE fois pour cette case.",
                 desc && desc->titre ? desc->titre : "?", etat->secondaire);
    }
    if (w->badge) {
        if (r == DN_VAL_SIMULEE) {
            lv_obj_clear_flag(w->badge, LV_OBJ_FLAG_HIDDEN);
        } else {
            lv_obj_add_flag(w->badge, LV_OBJ_FLAG_HIDDEN);
        }
    }

    if (grouper) {
        if (s_groupe_union) {
            /*
             * APRÈS écriture : la zone d'ARRIVÉE des mêmes enfants.
             *
             * 🔴 CORRIGÉ LE 2026-08-27 (2ᵉ revue de code) — ⛔ CETTE PASSE LISAIT
             *    DEUX FOIS LES MÊMES COORDONNÉES, ET LE COMMENTAIRE QUI LA
             *    JUSTIFIAIT DÉCRIVAIT UN MÉCANISME IMPOSSIBLE.
             *    `lv_obj_get_coords()` est une copie de struct nue
             *    (lv_obj_pos.c:566-571). `lv_label_set_text` finit par
             *    `lv_obj_refresh_self_size` → `lv_obj_mark_layout_as_dirty`, qui
             *    ne fait que poser `layout_inv` et poster `LV_EVENT_REFR_REQUEST`
             *    (lv_obj_pos.c:368-379) : LA GÉOMÉTRIE EST DIFFÉRÉE.
             *    `lv_obj_set_pos` de `valeur_placer` l'est aussi. Et ce fichier
             *    n'appelait NULLE PART `lv_obj_update_layout` (grep : vide).
             *    ⇒ la seconde boucle unissait des rectangles IDENTIQUES à la
             *      première, et l'élargissement n'était JAMAIS couvert. Le
             *      rétrécissement l'était par accident (l'union garde l'ancienne
             *      boîte, plus large) — soit l'INVERSE de ce que le commentaire
             *      d'origine affirmait.
             * 🔴 ET ÇA RÉFUTE L'EXPLICATION PUBLIÉE en §20.7.19 pt 3 : « les
             *    textes changent de largeur ⇒ l'union s'élargit à chaque mise à
             *    jour » est MÉCANIQUEMENT IMPOSSIBLE — aucune des deux passes ne
             *    voyait jamais la nouvelle largeur. La mesure de 0,97 /s est
             *    réelle ; l'explication qu'on lui a attachée, non.
             * ⚠️ ET L'ATOMICITÉ N'AVAIT JAMAIS EXISTÉ : l'auto-réparation
             *    différée des labels tombait APRÈS le rétablissement de
             *    l'invalidation ⇒ chaque label ajoutait UNE zone sale de plus,
             *    c'est-à-dire exactement ce que le mode existe pour supprimer.
             *    🔍 LE MÉCANISME, RELU LIGNE À LIGNE DANS LVGL 9.5.0 VENDORISÉ
             *    (2026-08-27) — ⛔ et la citation d'origine (« lv_label.c:1354 »)
             *    désignait la FIN de la chaîne, pas son crochet, donc elle
             *    n'était pas vérifiable telle quelle. La chaîne complète :
             *      `lv_label_mark_need_refr_text()` (lv_label.c:1059) abonne
             *      `update_layout_completed_cb` au DISPLAY sur
             *      `LV_EVENT_UPDATE_LAYOUT_COMPLETED` (**:1071**) ; ce callback
             *      (**:1075-1085**) se DÉSABONNE puis appelle
             *      `lv_label_refr_text()`, qui finit par `lv_obj_invalidate()`
             *      (**:1354**). C'est cette dernière invalidation qui arrivait
             *      trop tard.
             * 🎯 LE CORRECTIF, ET IL FERME LES DEUX : on force la géométrie ICI,
             *    ⛔ AVANT de rétablir l'invalidation. Les invalidations que
             *    `lv_obj_update_layout` déclenche sont donc AVALÉES comme les
             *    autres, la seconde passe lit enfin les NOUVELLES coordonnées,
             *    et il ne reste bien qu'UNE zone sale à la sortie.
             *    ✅ Et le désabonnement du callback (`:1081`) garantit que le
             *    label ne se réparera PAS une seconde fois après coup : sa zone
             *    est prise ici, une fois, et c'est tout.
             *
             * ⚠️ CE QUE CET APPEL COÛTE, ET ⛔ ON NE LE SUPPOSE PAS NÉGLIGEABLE.
             *    `lv_obj_update_layout()` ne travaille PAS sur `w->racine` : il
             *    remonte à l'ÉCRAN (`lv_obj_get_screen`, lv_obj_pos.c:390) et
             *    boucle tant que `scr_layout_inv` est posé. En pratique le
             *    premier widget de la salve fait le travail et éteint le
             *    drapeau ; les suivants ne paient plus que l'ENVOI DE
             *    L'ÉVÉNEMENT display. ⛔ Mais c'est UNE HYPOTHÈSE DE LECTURE :
             *    ce mode n'est PAS le régime livré (`on` l'est), et son coût
             *    réel est à MESURER sur la carte en même temps que son taux —
             *    le `0,97 /s` de §20.7.19 est de toute façon à reprendre.
             */
            /* ⛔ L'APPEL A `lv_obj_update_layout()` N'EST PLUS ICI — il a été
             *    remonté AVANT `lv_display_enable_invalidation(disp, false)`.
             *    Voir la justification complète à ce nouvel emplacement : dans
             *    la fenêtre coupée, il consommait les réparations différées des
             *    labels de TOUT l'écran, et leur désabonnement rendait la perte
             *    définitive. La géométrie est donc déjà à jour quand on arrive
             *    ici, et la seconde passe lit bien les nouvelles coordonnées. */
            zone_widget_prendre(w, &zone_union, &zone_vide);
        }
        lv_display_enable_invalidation(disp, true);
        if (s_groupe_union && !zone_vide) {
            /* UNE seule zone sale — donc UN seul flush, donc l'atomicité — mais
             * bornée aux valeurs au lieu du conteneur entier.
             * ⚠️ `lv_obj_invalidate_area` TRONQUE à `racine` : si un label
             *    débordait de son conteneur, la partie dehors ne serait pas
             *    reprise. Elle ne le peut pas ici (les labels sont ses enfants
             *    et le conteneur ne rogne pas), mais ⛔ ne pas l'oublier si la
             *    géométrie change un jour. */
            lv_obj_invalidate_area(w->racine, &zone_union);
        } else {
            /* UNE seule zone sale : le conteneur entier. C'est la branche B
             * d'AC8 — et le repli quand l'union est vide (aucun label). */
            lv_obj_invalidate(w->racine);
        }
    }
}

void dn_widget_oublier(dn_widget_t *w)
{
    if (w) {
        memset(w, 0, sizeof(*w));
    }
}

#include "dn_veille.h"

#include <string.h>

#include "esp_log.h"
#include "esp_timer.h"
#include "nvs.h"

static const char *TAG = "dn_veille";

/*
 * ⚠️ MÊME NAMESPACE QUE `dn_bootcfg`, CLÉS DISTINCTES (AC7.1/AC7.2). Le motif
 *    complet est dans `dn_veille.h` : `dn_bootcfg` est BOOT-ONLY par contrat
 *    écrit, ces deux réglages-ci s'appliquent à chaud.
 * ⚠️ Les clés NVS sont bornées à 15 caractères par ESP-IDF. Les deux ci-dessous
 *    font 9 et 10 : elles tiennent, et on ne les rallonge pas.
 */
#define DN_NVS_NAMESPACE "desknode"
#define DN_KEY_ARMEE "veille_on"
#define DN_KEY_CRAN "veille_dly"

/*
 * ── LES QUATRE CRANS — LA TABLE VIT ICI ET NULLE PART AILLEURS ──────────────
 * Le MENU, la console et la NVS la lisent tous d'ici. La dupliquer est
 * exactement ce qui avait rendu SIMULÉE indiscernable d'ABSENTE (revue
 * 2026-08-18) : deux conventions pour une seule vérité.
 */
static const int k_crans_min[DN_VEILLE_CRANS] = {1, 3, 5, 10};

int dn_veille_cran_min(int idx)
{
    if (idx < 0 || idx >= DN_VEILLE_CRANS) {
        return -1;
    }
    return k_crans_min[idx];
}

int dn_veille_cran_index(int minutes)
{
    for (int i = 0; i < DN_VEILLE_CRANS; i++) {
        if (k_crans_min[i] == minutes) {
            return i;
        }
    }
    return -1;
}

const char *dn_veille_mode_nom(dn_veille_mode_t m)
{
    switch (m) {
    case DN_VEILLE_ACTIF:
        return "ACTIF";
    case DN_VEILLE_AMBIENT:
        return "AMBIENT";
    default:
        return "?";
    }
}

const char *dn_veille_origine_nom(dn_veille_origine_t o)
{
    switch (o) {
    case DN_VEILLE_ORIG_DOIGT:
        return "doigt";
    case DN_VEILLE_ORIG_CONSOLE:
        return "console";
    case DN_VEILLE_ORIG_MENU:
        return "MENU";
    default:
        return "aucun";
    }
}

/*
 * ── L'ÉTAT ──────────────────────────────────────────────────────────────────
 *
 * 🔴 LES DÉFAUTS D'USINE, ET LEURS MOTIFS — DÉCISION OWNER DU 2026-08-25 (D-8).
 *    ⛔ Ce ne sont pas des nombres ronds posés au jugé, et ⛔ ils ne se
 *    re-litigent pas en séance.
 *
 *    `veille = ON`. Le critère n°1 du brief est « une semaine H24 … EN AMBIENT
 *    LA MAJORITÉ DU TEMPS ». Un défaut `OFF` rendrait ce critère FAUX À LA
 *    SORTIE DE BOÎTE : le module passerait sa semaine en Actif, et le critère
 *    ne serait jamais exercé par personne qui n'aurait pas d'abord lu la doc.
 *
 *    `délai = 3 min`, c'est-à-dire le 2ᵉ des quatre crans. ⛔ Ni le piège du
 *    `1 min` — le module s'endort pendant qu'on le REGARDE, et l'owner conclut
 *    que la veille est cassée — ⛔ ni celui du `10 min` : une journée de travail
 *    devant la tour ne verrait JAMAIS Ambient, donc le critère n°1 ne serait
 *    jamais exercé non plus, par l'autre bout.
 */
static bool s_armee = DN_VEILLE_ARMEE_DEFAUT;
static int s_cran = DN_VEILLE_CRAN_DEFAUT;
static dn_veille_mode_t s_mode = DN_VEILLE_ACTIF;

/*
 * ─── dn4-5 / AC3.2 : LE TEMPS PASSÉ DANS CHAQUE MODE ────────────────────────
 *
 * 🔴 POURQUOI CE CUMUL EXISTE, ET POURQUOI IL NE COMPTE PAS DES TICKS.
 *    Le brief exige « en Ambient LA MAJORITÉ DU TEMPS », donc **> 50 %** est un
 *    SEUIL, ⛔ pas une figure de style — et il n'existait AUCUN cumul pour le
 *    trancher. La tentation était de compter les ticks (`s_secondes_vues`) :
 *    ⛔ C'EST FAUX, et le dépôt le dit lui-même. `dn_ui.c` documente qu'un
 *    `veille now` d'opérateur passe DÉLIBÉRÉMENT à côté de `dn_veille_tick()`
 *    (« un geste d'opérateur ne doit pas faire avancer une horloge
 *    d'observation »). Un dénominateur en ticks aurait donc des TROUS, et sur
 *    7 jours il rendrait un pourcentage plausible et faux.
 *
 * 🎯 ON CUMULE DONC DU TEMPS MURAL, pris sur `esp_timer_get_time()` (int64,
 *    aucun enroulement avant ~292 000 ans — voir l'audit de dn4-5/AC1.1). Le
 *    cumul est exact QUEL QUE SOIT le chemin qui change le mode, parce que
 *    TOUS passent par `veille_poser_mode()` : c'est la seule écriture de
 *    `s_mode` du fichier, et c'est vérifié par gate.
 *
 * ⛔ EN RAM, ET RIEN QU'EN RAM (D4). Une semaine H24 est très exactement le
 *    régime où une écriture périodique se paierait — mesuré : sous écriture
 *    flash, « l'image défile ». Le cumul ne survit donc pas au reboot, et c'est
 *    VOULU : un reboot casse la fenêtre du soak de toute façon (AC3.6).
 */
static int64_t s_cumul_us[2];  /* [DN_VEILLE_ACTIF], [DN_VEILLE_AMBIENT] */
static int64_t s_t_mode_us;    /* instant d'entrée dans le mode COURANT */

static uint32_t s_inactivite_ms;
static uint32_t s_inactivite_max_ms;
static uint32_t s_bascules;
static uint32_t s_reveils;
static uint32_t s_rebases;
static uint32_t s_annulations;
static uint32_t s_secondes_vues;
/*
 * 🔴 AJOUTÉS EN REVUE DE CODE LE 2026-08-28 — LE DIAGNOSTIC D'APPUI FANTÔME
 *    (AC8.2) ÉTAIT AVEUGLE AU SEUL CAS QUI L'ATTEINT, ET C'EST DÉMONTRABLE.
 *
 * L'ANCIENNE GARDE DISAIT : « si `s_bascules > 0`, plus jamais de soupçon ».
 * ⇒ Elle n'était donc armée QU'ENTRE LE BOOT ET LA PREMIÈRE BASCULE.
 *
 * 🎯 OR LA PANNE QU'ELLE VISE NE PEUT PAS SURVENIR DANS CETTE FENÊTRE. Un
 *    `PRESSED` fantôme du GT911 se latche via `s_consommer` (`dn_touch.c`), qui
 *    n'est posé QU'EN AMBIENT — c'est-à-dire **APRÈS au moins une bascule**.
 *    Le détecteur s'éteignait donc exactement au moment où il devenait utile.
 * ⚠️ Et il suffisait d'UN SEUL `veille now` pour l'éteindre, alors que
 *    `dn_veille_forcer_dormir()` jure au-dessus d'elle-même d'éviter
 *    `dn_veille_tick()` POUR NE PAS fausser ce diagnostic : elle épargnait
 *    l'horloge d'observation et empoisonnait l'AUTRE entrée du même calcul.
 *
 * ⇒ LA FENÊTRE D'OBSERVATION EST DÉSORMAIS « DEPUIS LE DERNIER RÉVEIL »,
 *   ⛔ plus « depuis le boot », et seules les bascules AUTOMATIQUES comptent.
 *   C'est la question à laquelle AC8.2 veut répondre : *« la garde a-t-elle
 *   cédé depuis qu'on est éveillé ? »* — ⛔ pas *« quelqu'un a-t-il déjà tapé
 *   une commande depuis le boot ? »*.
 */
static uint32_t s_bascules_forcees;
static uint32_t s_bascules_auto_depuis_reveil;
static uint32_t s_secondes_depuis_reveil;
static uint32_t s_inact_max_depuis_reveil_ms;

static void veille_poser_mode(dn_veille_mode_t m)
{
    int64_t now = esp_timer_get_time();
    int idx = (s_mode == DN_VEILLE_AMBIENT) ? 1 : 0;
    if (now > s_t_mode_us) {
        s_cumul_us[idx] += now - s_t_mode_us;
    }
    s_t_mode_us = now;
    s_mode = m;
}

void dn_veille_cumul(int64_t *out_actif_us, int64_t *out_ambient_us)
{
    /* ⚠️ ON AJOUTE L'INTERVALLE EN COURS. Sans lui, un module en Ambient depuis
     *    six jours publierait le cumul de la DERNIÈRE BASCULE et rendrait « 0 %
     *    d'Ambient » — le pire cas possible : faux, plausible, et dans le sens
     *    qui fait échouer un critère qui est en réalité tenu. */
    int64_t c[2] = {s_cumul_us[0], s_cumul_us[1]};
    int64_t now = esp_timer_get_time();
    int idx = (s_mode == DN_VEILLE_AMBIENT) ? 1 : 0;
    if (now > s_t_mode_us) {
        c[idx] += now - s_t_mode_us;
    }
    if (out_actif_us) {
        *out_actif_us = c[0];
    }
    if (out_ambient_us) {
        *out_ambient_us = c[1];
    }
}
/*
 * 🔴 L'INSTRUMENT D'AC3.3, ET IL N'EXISTAIT PAS — TROUVÉ EN SÉANCE LE 2026-08-25.
 *
 *    AC3.3 demande « l'écart entre le dernier contact et la bascule », dans la
 *    fenêtre **[délai ; délai + 1 s]**. ⛔ AUCUN SONDAGE DEPUIS L'HÔTE NE PEUT
 *    L'ÉTABLIR : la latence série et le pas d'interrogation ajoutent leur propre
 *    seconde, et on publierait une dispersion d'INSTRUMENT en croyant publier
 *    celle du produit. Le seul endroit qui connaît le chiffre exact est le tick
 *    qui bascule.
 * ⚠️ `s_inactivite_ms` NE PEUT PAS SERVIR : le tick continue de tourner en
 *    Ambient et l'ÉCRASE à la seconde suivante. Il faut un champ qui LATCHE.
 * ⚠️ UN ANNEAU DE QUATRE, parce qu'AC3.3 exige **trois** relevés : les lire un
 *    par un obligerait à réveiller entre chaque, et un `veille reset` entre
 *    deux relevés effacerait le précédent. Les trois se lisent d'un coup.
 */
#define DN_VEILLE_BASCULES_GARDEES 4
static uint32_t s_inact_bascule_ms[DN_VEILLE_BASCULES_GARDEES];
/*
 * 🔴 SÉANCE DU 2026-08-25 — L'ÉCART SEUL NE SE JUGE PAS, ET LA CONSOLE LE
 *    JUGEAIT QUAND MÊME.
 * LE DÉFAUT, MESURÉ SUR LA CARTE : `dn_console.c` comparait chaque écart latché
 * au délai **en vigueur À LA LECTURE**. Un écart de 60 400 ms, parfaitement
 * dans [60 000 ; 61 000] au moment du latch, s'affichait « 🔴 HORS » dès que le
 * cran passait à 10 min entre la bascule et le `veille`. ⇒ Une étiquette qui
 * ment, sur l'instrument même qui SOLDE AC3.3.
 * ⇒ Chaque échantillon porte maintenant LE DÉLAI QUI ÉTAIT ARMÉ QUAND IL A ÉTÉ
 *   LATCHÉ, et le jugement se fait contre CELUI-LÀ, ⛔ jamais contre le courant.
 */
static uint32_t s_inact_bascule_delai_ms[DN_VEILLE_BASCULES_GARDEES];
/*
 * 🔴 ET CERTAINS ÉCHANTILLONS NE SONT PAS JUGEABLES DU TOUT — MESURÉ AUSSI.
 * Si la garde est armée (ou le cran abaissé, ou les compteurs remis à zéro)
 * ALORS QUE l'inactivité dépasse DÉJÀ le délai, le tout premier tick bascule
 * immédiatement et latche l'inactivité VRAIE — **178 270 ms relevés en séance
 * pour un cran de 1 min**. La bascule est CORRECTE ; c'est la fenêtre
 * [délai ; délai+1 s] qui ne s'applique pas, faute d'avoir JAMAIS vu d'état
 * SOUS le seuil.
 * ⇒ On garde l'échantillon et on DIT qu'il n'est pas jugeable — même contrat
 *   que `veille lat`, qui ENREGISTRE les réveils console et les EXCLUT de la
 *   statistique, ⛔ sans les jeter en silence.
 */
static bool s_inact_bascule_jugeable[DN_VEILLE_BASCULES_GARDEES];
/* La garde a-t-elle vu au moins un tick SOUS le seuil depuis son armement ? */
static bool s_garde_amorcee;
static uint32_t s_inact_bascule_w;
static dn_veille_origine_t s_origine = DN_VEILLE_ORIG_AUCUNE;

/*
 * Le rétroéclairage d'Ambient.
 * ✅ **AC9.1 EST TRANCHÉ — CONSTAT OWNER DU 2026-08-25 SUR LA DALLE** :
 *    *« la luminosité de la veille est bien »*. La valeur reste **10 %**, et
 *    ce n'est plus une valeur d'amorçage : c'est un constat.
 * ⚠️ Elle reste réglable à chaud (`veille pct`) — un constat owner n'est pas un
 *    verrou, et le prochain qui la déplacera devra le faire à l'œil, comme
 *    celui-ci.
 * Les deux bornes qui l'encadraient, et qui restent vraies :
 *   - 3 % est le plancher de LISIBILITÉ de dn1-3 / AC7 (« le Living PCB et le
 *     label s'y distinguent encore, TOUT JUSTE ») — donc trop bas pour un état
 *     de repos qu'on doit pouvoir consulter d'un coup d'œil ;
 *   - `DN_ENV_BL_PCT_MIN = 8` est le plancher de la LOI d'asservissement au
 *     lux, constat owner « c'est ça » — un autre chiffre pour un autre usage.
 * ⛔ Ne pas graver 8 par recopie : ce n'est pas le même arbitrage.
 *
 * ══ 🔴 `dn4-19`, 2026-08-27 — CE CHIFFRE A CHANGÉ DE RÔLE ════════════════════
 * ⛔ **CE N'EST PLUS LE NIVEAU D'AMBIENT.** Le niveau d'Ambient est désormais
 *    une **fonction du lux** (`dn_env_bl_loi_regime()`), et c'est tout l'objet
 *    de la story : cette constante était **F1**, la première des trois causes.
 * ⛔ **ET LE CONSTAT DU 2026-08-25 N'EST PAS INVALIDÉ — IL LUI MANQUAIT SA
 *    CONDITION D'ÉCLAIRAGE.** *« La luminosité de la veille est bien »* a été
 *    dit **RIDEAU FERMÉ**, où 10 % coïncide à deux points près avec
 *    `DN_ENV_BL_PCT_MIN = 8`. Le constat du 2026-08-27 (*« en veille, avec la
 *    lumière, l'écran n'est pas assez rétroéclairé »*) a été fait **EN PLEINE
 *    LUMIÈRE**. **Les deux sont COMPATIBLES**, et ce qui était faux, c'est
 *    qu'un chiffre a été consigné sans dire sous quelle lumière il valait.
 *    ⇒ *« Une mesure porte la date de son binaire »* — et sa condition.
 * ✅ CE QUE `s_pct` DEVIENT : le niveau d'Ambient de **DERNIER RECOURS**, posé
 *    par la bascule **quand la loi ne peut pas parler** (capteur muet, jamais
 *    lu, ou périmé) — et **journalisé quand il sert**, parce qu'un repli
 *    silencieux serait exactement le défaut que cette story ferme.
 */
static int s_pct = 10;

/* ── NVS ─────────────────────────────────────────────────────────────────── */

/*
 * 🔴 LE COÛT DE LA PERSISTANCE EST **MESURÉ**, PARCE QU'IL EST PAYÉ DANS LA
 *    TÂCHE LVGL.
 *
 *    Un tap sur un réglage du MENU écrit la NVS depuis le callback d'événement,
 *    c'est-à-dire depuis la tâche de rendu, sous son verrou. Une écriture flash
 *    coupe le cache : la tâche qui l'exécute STALLE pendant toute l'opération,
 *    et ce sont des trames perdues. ⛔ Ce n'est pas une raison de ne pas
 *    persister — un réglage qui ne survit pas au reboot serait un mensonge — ni
 *    de le cacher. On le CHRONOMÈTRE, et `veille` le publie.
 * ⚠️ Le chemin CONSOLE (`veille on`, `veille delai`) paie le même coût depuis la
 *    tâche REPL, où il ne gêne personne. C'est le chemin MENU qui est à
 *    surveiller, et c'est pour ça que le chiffre est publié plutôt que supposé
 *    négligeable.
 */
static uint32_t s_persist_us;
static uint32_t s_persist_n;

uint32_t dn_veille_persist_us(void) { return s_persist_us; }
uint32_t dn_veille_persist_n(void) { return s_persist_n; }

static esp_err_t nvs_ecrire_i32(const char *cle, int32_t v)
{
    int64_t t0 = esp_timer_get_time();
    nvs_handle_t h;
    esp_err_t err = nvs_open(DN_NVS_NAMESPACE, NVS_READWRITE, &h);
    if (err != ESP_OK) {
        ESP_LOGE(TAG,
                 "nvs_open(« %s ») a echoue : %s — le reglage s'applique A "
                 "CHAUD mais NE SURVIVRA PAS au reboot.",
                 DN_NVS_NAMESPACE, esp_err_to_name(err));
        /* ⚠️ On horodate MÊME SUR ÉCHEC : sans ça, `veille` publierait le coût de
         *    l'écriture PRÉCÉDENTE sous une tentative qui n'a rien écrit. */
        s_persist_us = (uint32_t)(esp_timer_get_time() - t0);
        s_persist_n++;
        return err;
    }
    err = nvs_set_i32(h, cle, v);
    if (err == ESP_OK) {
        err = nvs_commit(h);
    }
    if (err != ESP_OK) {
        ESP_LOGE(TAG,
                 "ecriture NVS « %s » = %ld refusee : %s — le reglage NE "
                 "SURVIVRA PAS au reboot.",
                 cle, (long)v, esp_err_to_name(err));
    }
    nvs_close(h);
    s_persist_us = (uint32_t)(esp_timer_get_time() - t0);
    s_persist_n++;
    return err;
}

void dn_veille_init(void)
{
    nvs_handle_t h;
    esp_err_t err = nvs_open(DN_NVS_NAMESPACE, NVS_READONLY, &h);
    if (err != ESP_OK) {
        /* Namespace jamais écrit : c'est le cas NOMINAL d'un clone neuf, ⛔ pas
         * une panne. On le dit quand même — un défaut silencieux fausserait une
         * mesure sans qu'on le sache. */
        ESP_LOGW(TAG,
                 "aucun reglage de veille en NVS (%s) : DEFAUTS D'USINE — "
                 "veille %s, delai %d min. (%s)",
                 DN_NVS_NAMESPACE, DN_VEILLE_ARMEE_DEFAUT ? "ON" : "OFF",
                 dn_veille_cran_min(DN_VEILLE_CRAN_DEFAUT),
                 esp_err_to_name(err));
        return;
    }

    /*
     * 🔴 REVUE DE CODE DU 2026-08-28 — AC7.4 N'ÉTAIT PAS TENUE POUR LE CAS
     *    « ABSENT », ET LE NAMESPACE PARTAGÉ EN FAISAIT LE CAS **NOMINAL**.
     *    Le seul journal « aucun réglage en NVS » est celui du `nvs_open`
     *    ci-dessus. Or `DN_NVS_NAMESPACE` vaut `"desknode"` — **le même que
     *    `dn_bootcfg`** — donc sur toute carte ayant déjà écrit une config de
     *    boot, `nvs_open` RÉUSSIT, les deux clés rendent `ESP_ERR_NVS_NOT_FOUND`
     *    et l'ancienne branche `else if (err != ESP_ERR_NVS_NOT_FOUND)` ne
     *    journalisait RIEN. ⇒ le défaut s'appliquait EN SILENCE, exactement ce
     *    qu'AC7.4 interdit (« un défaut silencieux fausserait une mesure sans
     *    qu'on le sache »).
     * ⚠️ Le cas ABERRANT, lui, était bien traité — c'est le cas ABSENT qui
     *    tombait dans le trou, et c'est le plus fréquent des deux.
     */
    int32_t v = 0;
    err = nvs_get_i32(h, DN_KEY_ARMEE, &v);
    if (err == ESP_OK) {
        /* ⚠️ TOUT CE QUI N'EST NI 0 NI 1 EST ABERRANT, et retombe sur le défaut
         *    EN LE DISANT (AC7.4). Un `!= 0` silencieux ferait passer un 42
         *    corrompu pour un « ON » délibéré. */
        if (v == 0 || v == 1) {
            s_armee = (v != 0);
        } else {
            ESP_LOGW(TAG,
                     "cle « %s » ABERRANTE (%ld) : defaut %s applique et "
                     "JOURNALISE.",
                     DN_KEY_ARMEE, (long)v,
                     DN_VEILLE_ARMEE_DEFAUT ? "ON" : "OFF");
        }
    } else if (err == ESP_ERR_NVS_NOT_FOUND) {
        ESP_LOGW(TAG,
                 "cle « %s » ABSENTE : defaut %s applique et JOURNALISE (AC7.4). "
                 "⚠️ Le namespace « %s » est PARTAGE avec `dn_bootcfg` — son "
                 "ouverture reussit donc meme quand AUCUN reglage de veille n'y "
                 "a jamais ete ecrit.",
                 DN_KEY_ARMEE, DN_VEILLE_ARMEE_DEFAUT ? "ON" : "OFF",
                 DN_NVS_NAMESPACE);
    } else {
        ESP_LOGW(TAG, "lecture « %s » : %s — defaut applique.", DN_KEY_ARMEE,
                 esp_err_to_name(err));
    }

    err = nvs_get_i32(h, DN_KEY_CRAN, &v);
    if (err == ESP_OK) {
        if (v >= 0 && v < DN_VEILLE_CRANS) {
            s_cran = (int)v;
        } else {
            ESP_LOGW(TAG,
                     "cle « %s » ABERRANTE (%ld, hors 0..%d) : defaut %d min "
                     "applique et JOURNALISE.",
                     DN_KEY_CRAN, (long)v, DN_VEILLE_CRANS - 1,
                     dn_veille_cran_min(DN_VEILLE_CRAN_DEFAUT));
        }
    } else if (err == ESP_ERR_NVS_NOT_FOUND) {
        ESP_LOGW(TAG,
                 "cle « %s » ABSENTE : defaut %d min applique et JOURNALISE "
                 "(AC7.4).",
                 DN_KEY_CRAN, dn_veille_cran_min(DN_VEILLE_CRAN_DEFAUT));
    } else {
        ESP_LOGW(TAG, "lecture « %s » : %s — defaut applique.", DN_KEY_CRAN,
                 esp_err_to_name(err));
    }

    nvs_close(h);
    ESP_LOGI(TAG, "veille %s · delai %d min (%lu ms)", s_armee ? "ON" : "OFF",
             dn_veille_cran_min(s_cran), (unsigned long)dn_veille_delai_ms());
}

/* ── Les deux réglages ───────────────────────────────────────────────────── */

bool dn_veille_armee(void) { return s_armee; }

esp_err_t dn_veille_set_armee(bool on)
{
    s_armee = on;
    /* ⚠️ ARMER DÉSAMORCE LA GARDE : l'inactivité peut DÉJÀ dépasser le délai, et
     *    le premier tick basculerait alors sans que la garde ait jamais vu
     *    d'état sous le seuil. L'écart serait latché — et il ne serait pas
     *    jugeable. Voir `s_inact_bascule_jugeable`. */
    s_garde_amorcee = false;
    return nvs_ecrire_i32(DN_KEY_ARMEE, on ? 1 : 0);
}

int dn_veille_cran(void) { return s_cran; }

esp_err_t dn_veille_set_cran(int idx)
{
    if (idx < 0 || idx >= DN_VEILLE_CRANS) {
        /* ⛔ Le dépôt REFUSE et EXPLIQUE, il n'écrête pas en silence. */
        return ESP_ERR_INVALID_ARG;
    }
    s_cran = idx;
    /* ⚠️ MÊME MOTIF QU'À L'ARMEMENT : baisser le cran sous l'inactivité courante
     *    fait basculer au tick suivant, et cet écart-là ne se juge pas contre
     *    [délai ; délai+1 s]. */
    s_garde_amorcee = false;
    return nvs_ecrire_i32(DN_KEY_CRAN, idx);
}

uint32_t dn_veille_delai_ms(void)
{
    int m = dn_veille_cran_min(s_cran);
    if (m <= 0) {
        /* Ne peut arriver que si `s_cran` a été corrompu hors de ce module. On
         * retombe sur le défaut d'usine plutôt que de rendre 0 — un délai nul
         * ferait basculer en Ambient au premier tick, ce qui se lirait comme
         * une panne de bascule alors que c'est une panne d'état. */
        m = dn_veille_cran_min(DN_VEILLE_CRAN_DEFAUT);
    }
    return (uint32_t)m * 60u * 1000u;
}

dn_veille_mode_t dn_veille_mode(void) { return s_mode; }

/* ── LA GARDE ────────────────────────────────────────────────────────────── */

bool dn_veille_doit_dormir(bool armee, dn_veille_mode_t mode,
                           uint32_t inactivite_ms, uint32_t delai_ms)
{
    if (!armee) {
        return false;
    }
    if (mode != DN_VEILLE_ACTIF) {
        return false;
    }
    if (delai_ms == 0) {
        /* Voir `dn_veille_delai_ms()` : un délai nul n'est pas un réglage, c'est
         * un état corrompu. On ne dort pas dessus. */
        return false;
    }
    return inactivite_ms >= delai_ms;
}

dn_veille_action_t dn_veille_tick(uint32_t inactivite_ms)
{
    s_secondes_vues++;
    s_inactivite_ms = inactivite_ms;
    if (inactivite_ms > s_inactivite_max_ms) {
        s_inactivite_max_ms = inactivite_ms;
    }
    /* La fenêtre d'observation UTILE au diagnostic d'AC8.2 : depuis le dernier
     * réveil, ⛔ pas depuis le boot. Voir le bloc de `s_bascules_forcees`. */
    s_secondes_depuis_reveil++;
    if (inactivite_ms > s_inact_max_depuis_reveil_ms) {
        s_inact_max_depuis_reveil_ms = inactivite_ms;
    }

    uint32_t delai = dn_veille_delai_ms();
    if (!dn_veille_doit_dormir(s_armee, s_mode, inactivite_ms, delai)) {
        /*
         * 🎯 L'AMORÇAGE DE LA GARDE — LE SEUL ENDROIT QUI PEUT L'ÉTABLIR.
         * Un tick ARMÉ, en ACTIF, et SOUS le seuil : à partir de maintenant, un
         * franchissement est un VRAI franchissement, et son écart se juge
         * contre [délai ; délai+1 s]. Sans cet état, on ne saurait pas
         * distinguer « la veille est tombée au bout du délai » de « la veille
         * est tombée au premier tick parce qu'on venait de l'armer ».
         */
        if (s_armee && s_mode == DN_VEILLE_ACTIF && inactivite_ms < delai) {
            s_garde_amorcee = true;
        }
        return DN_VEILLE_ACTION_RIEN;
    }

    /* L'état bascule ICI, et l'appelant fait le travail visuel ensuite. S'il
     * n'y parvient pas, il DOIT appeler `dn_veille_annuler_bascule()` — sans
     * quoi la console annoncerait AMBIENT sur un écran resté en couleurs. */
    veille_poser_mode(DN_VEILLE_AMBIENT);
    s_bascules++;
    s_bascules_auto_depuis_reveil++;
    /* L'écart d'AC3.3, LATCHÉ à l'instant exact où la garde a cédé — AVEC LE
     * DÉLAI QUI ÉTAIT ARMÉ À CET INSTANT, et avec le fait de savoir s'il est
     * jugeable. ⛔ Un écart nu ne se juge pas : voir `s_inact_bascule_delai_ms`. */
    {
        uint32_t i = s_inact_bascule_w % DN_VEILLE_BASCULES_GARDEES;
        s_inact_bascule_ms[i] = inactivite_ms;
        s_inact_bascule_delai_ms[i] = delai;
        s_inact_bascule_jugeable[i] = s_garde_amorcee;
    }
    s_inact_bascule_w++;
    /* La garde se re-amorcera au premier tick sous le seuil après le réveil. */
    s_garde_amorcee = false;
    return DN_VEILLE_ACTION_DORMIR;
}

/*
 * Bascule FORCÉE (geste d'opérateur : `veille now`, ou le MENU).
 * ⚠️ ⛔ ELLE NE PASSE PAS PAR `dn_veille_tick()`, ET C'EST LE POINT : le tick
 *    incrémente `secondes_vues`, qui est l'UPTIME OBSERVÉ et sert de condition
 *    au diagnostic d'appui fantôme. Un geste d'opérateur qui ferait avancer une
 *    horloge d'observation fausserait ce diagnostic — discrètement, et d'autant
 *    plus qu'on tape la commande souvent.
 * ⚠️ Elle RESPECTE l'armement : ⛔ on ne contourne pas le réglage de
 *    l'utilisateur. Rend `false` si la veille est désarmée ou si on dort déjà.
 */
bool dn_veille_forcer_dormir(void)
{
    if (!s_armee || s_mode != DN_VEILLE_ACTIF) {
        return false;
    }
    veille_poser_mode(DN_VEILLE_AMBIENT);
    s_bascules++;
    /* 🔴 REVUE DE CODE DU 2026-08-28 — ⛔ ON N'INCRÉMENTE **PAS**
     *    `s_bascules_auto_depuis_reveil` ICI, ET C'EST TOUT LE POINT.
     *    Cette fonction épargnait déjà `s_secondes_vues` pour ne pas fausser le
     *    diagnostic d'appui fantôme ; elle empoisonnait pourtant son AUTRE
     *    entrée en faisant monter le compteur que la garde interrogeait. Un
     *    seul `veille now` éteignait le détecteur DÉFINITIVEMENT.
     * ⚠️ `s_bascules` monte quand même : c'est le compteur PUBLIÉ, et une
     *    bascule forcée EST une bascule. `s_bascules_forcees` dit laquelle,
     *    pour que la console puisse expliquer l'écart avec l'anneau d'AC3.3 —
     *    une bascule forcée ne latche AUCUN échantillon, par construction. */
    s_bascules_forcees++;
    return true;
}

void dn_veille_annuler_bascule(void)
{
    if (s_mode != DN_VEILLE_AMBIENT) {
        return;
    }
    veille_poser_mode(DN_VEILLE_ACTIF);
    if (s_bascules > 0) {
        s_bascules--;
    }
    /* ⚠️ ET L'ÉCHANTILLON D'AC3.3 EST RETIRÉ AVEC ELLE : une bascule ANNULÉE
     *    n'a pas eu lieu, son écart n'est donc pas un écart de bascule. Le
     *    laisser aurait mis, dans les trois relevés publiés, une mesure qui ne
     *    correspond à aucun changement d'écran. */
    if (s_inact_bascule_w > 0) {
        s_inact_bascule_w--;
        uint32_t i = s_inact_bascule_w % DN_VEILLE_BASCULES_GARDEES;
        bool etait_jugeable = s_inact_bascule_jugeable[i];
        s_inact_bascule_ms[i] = 0;
        s_inact_bascule_delai_ms[i] = 0;
        s_inact_bascule_jugeable[i] = false;
        /* ⚠️ LA GARDE REPREND SON ÉTAT D'AVANT LA BASCULE ANNULÉE. Sans ça, la
         *    tentative suivante serait marquée « non jugeable » alors qu'elle
         *    l'est : une annulation n'est PAS un ré-armement. */
        s_garde_amorcee = etait_jugeable;
    }
    s_annulations++;
    ESP_LOGW(TAG,
             "bascule vers Ambient ANNULEE : LVGL a refuse l'async (file "
             "pleine ou tas sature). L'ecran RESTE en couleurs, et l'etat le "
             "dit — ⛔ pas d'etiquette AMBIENT sur un ecran Actif.");
}

bool dn_veille_reveiller(dn_veille_origine_t origine)
{
    if (s_mode != DN_VEILLE_AMBIENT) {
        return false;
    }
    veille_poser_mode(DN_VEILLE_ACTIF);
    s_reveils++;
    s_origine = origine;
    /* 🔴 LE RÉVEIL ROUVRE LA FENÊTRE D'OBSERVATION D'AC8.2 (revue du
     *    2026-08-28). À partir d'ici, la question redevient : « la garde
     *    va-t-elle céder ? » — et si elle ne cède pas alors que le module est
     *    armé et que le temps passe, c'est précisément le soupçon à lever. */
    s_bascules_auto_depuis_reveil = 0;
    s_secondes_depuis_reveil = 0;
    s_inact_max_depuis_reveil_ms = 0;
    return true;
}

void dn_veille_note_rebase(void)
{
    s_rebases++;
    ESP_LOGW(TAG,
             "horloge d'inactivite REBASEE a la reprise de LVGL : pendant "
             "`ui off` le tick 1 Hz ne tourne pas mais `lv_tick` continue, "
             "donc l'inactivite a grossi SANS ETRE VECUE. Sans ce rebase, une "
             "coupure plus longue que le delai ferait basculer en Ambient "
             "INSTANTANEMENT a `ui on` — et ca se lirait comme un bug de "
             "bascule. (rebases : %lu)",
             (unsigned long)s_rebases);
}

void dn_veille_compteurs(dn_veille_compteurs_t *out)
{
    if (!out) {
        return;
    }
    out->mode = s_mode;
    out->armee = s_armee;
    out->cran = s_cran;
    out->delai_ms = dn_veille_delai_ms();
    out->inactivite_ms = s_inactivite_ms;
    out->inactivite_max_ms = s_inactivite_max_ms;
    out->bascules = s_bascules;
    out->reveils = s_reveils;
    out->rebases = s_rebases;
    out->annulations = s_annulations;
    out->secondes_vues = s_secondes_vues;
    out->bascules_forcees = s_bascules_forcees;
    out->bascules_auto_depuis_reveil = s_bascules_auto_depuis_reveil;
    out->secondes_depuis_reveil = s_secondes_depuis_reveil;
    out->inact_max_depuis_reveil_ms = s_inact_max_depuis_reveil_ms;
    out->origine = s_origine;
}

uint32_t dn_veille_bascule_ecart_ms(int rang)
{
    if (rang < 0 || rang >= DN_VEILLE_BASCULES_GARDEES ||
        (uint32_t)rang >= s_inact_bascule_w) {
        return 0; /* ⛔ « pas d'échantillon », l'appelant DOIT le distinguer */
    }
    /* rang 0 = la PLUS RÉCENTE. */
    uint32_t i = (s_inact_bascule_w - 1u - (uint32_t)rang) %
                 DN_VEILLE_BASCULES_GARDEES;
    return s_inact_bascule_ms[i];
}

uint32_t dn_veille_bascule_delai_ms(int rang)
{
    if (rang < 0 || rang >= DN_VEILLE_BASCULES_GARDEES ||
        (uint32_t)rang >= s_inact_bascule_w) {
        return 0; /* ⛔ « pas d'échantillon », l'appelant DOIT le distinguer */
    }
    uint32_t i = (s_inact_bascule_w - 1u - (uint32_t)rang) %
                 DN_VEILLE_BASCULES_GARDEES;
    return s_inact_bascule_delai_ms[i];
}

bool dn_veille_bascule_jugeable(int rang)
{
    if (rang < 0 || rang >= DN_VEILLE_BASCULES_GARDEES ||
        (uint32_t)rang >= s_inact_bascule_w) {
        return false;
    }
    uint32_t i = (s_inact_bascule_w - 1u - (uint32_t)rang) %
                 DN_VEILLE_BASCULES_GARDEES;
    return s_inact_bascule_jugeable[i];
}

uint32_t dn_veille_bascule_ecarts_n(void)
{
    return s_inact_bascule_w < DN_VEILLE_BASCULES_GARDEES
               ? s_inact_bascule_w
               : DN_VEILLE_BASCULES_GARDEES;
}

/*
 * 🔴 LE SNAPSHOT DE DIAGNOSTIC — UN SEUL COUP, ⛔ PLUS SEPT LECTURES ÉPARSES.
 *    Motif complet dans `dn_veille.h`. Appelé sous le verrou LVGL par
 *    `dn_ui_veille_diag()` : ⛔ ne pas l'appeler directement depuis le REPL.
 */
void dn_veille_diag(dn_veille_diag_t *out)
{
    if (!out) {
        return;
    }
    memset(out, 0, sizeof(*out));
    uint32_t n = dn_veille_bascule_ecarts_n();
    if (n > DN_VEILLE_BASCULES_GARDEES) {
        n = DN_VEILLE_BASCULES_GARDEES;
    }
    out->n = n;
    for (uint32_t i = 0; i < n; i++) {
        /* ⚠️ LES TROIS CHAMPS DU MÊME RANG SONT LUS DANS LA MÊME ITÉRATION, ET
         *    L'ENSEMBLE SOUS UN SEUL VERROU : c'est CE couplage-là qui manquait,
         *    ⛔ pas la justesse de chaque accesseur pris isolément. */
        out->ecart_ms[i] = dn_veille_bascule_ecart_ms((int)i);
        out->delai_ms[i] = dn_veille_bascule_delai_ms((int)i);
        out->jugeable[i] = dn_veille_bascule_jugeable((int)i);
    }
    out->persist_us = s_persist_us;
    out->persist_n = s_persist_n;
    out->soupcon_appui_fantome = dn_veille_soupcon_appui_fantome();
}

void dn_veille_reset(void)
{
    s_inactivite_ms = 0;
    s_inactivite_max_ms = 0;
    s_bascules = 0;
    s_reveils = 0;
    s_rebases = 0;
    s_annulations = 0;
    s_secondes_vues = 0;
    s_origine = DN_VEILLE_ORIG_AUCUNE;
    memset(s_inact_bascule_ms, 0, sizeof(s_inact_bascule_ms));
    memset(s_inact_bascule_delai_ms, 0, sizeof(s_inact_bascule_delai_ms));
    memset(s_inact_bascule_jugeable, 0, sizeof(s_inact_bascule_jugeable));
    s_inact_bascule_w = 0;
    /* ⚠️ REMETTRE LES COMPTEURS À ZÉRO DÉSAMORCE LA GARDE : l'inactivité, elle,
     *    n'est pas remise à zéro (c'est LVGL qui la tient, et aucun contact n'a
     *    eu lieu). Le premier tick d'après peut donc basculer aussitôt, et cet
     *    écart-là n'est pas jugeable. MESURÉ : 178 270 ms pour un cran de 1 min. */
    s_garde_amorcee = false;
    /* 🔴 AC8.3 — « TOUS les compteurs se remettent à zéro par `veille reset` ».
     *    `s_persist_n` y échappait : la sortie mélangeait alors des compteurs
     *    remis à zéro et un compteur CUMULATIF, et le dépôt a déjà payé
     *    exactement ça sur `*cris` en dn4-13. */
    s_persist_us = 0;
    s_persist_n = 0;
    /* Les compteurs de la revue du 2026-08-28 suivent le même reset : ils sont
     * des MESURES, pas des réglages. */
    s_bascules_forcees = 0;
    s_bascules_auto_depuis_reveil = 0;
    s_secondes_depuis_reveil = 0;
    s_inact_max_depuis_reveil_ms = 0;
    /*
     * 🔴 REVUE DE CODE DU 2026-08-28 — `s_cumul_us[]` / `s_t_mode_us` NE SONT
     *    **PAS** REMIS À ZÉRO ICI, ET LE MOTIF EST PLUS FORT QU'AC8.3.
     *
     * AC8.3 dit « TOUS les compteurs se remettent à zéro par `veille reset` »,
     * et le cumul mural est bien un compteur — la revue a raison de le relever.
     * ⛔ MAIS CE CUMUL N'APPARTIENT PAS À `dn3-3` : c'est **la fenêtre de soak
     *    de `dn4-5`**, qui dure UNE SEMAINE. Le zéroter ici donnerait à une
     *    commande de diagnostic tapée machinalement le pouvoir de DÉTRUIRE sept
     *    jours de mesure, en une frappe et sans confirmation. Le remède serait
     *    pire que le défaut.
     * ⇒ ON L'ÉPARGNE, ET C'EST **LA SORTIE DE CONSOLE QUI CESSE DE MENTIR** :
     *   `veille reset` ne dit plus « compteurs et latences a ZERO » tout court,
     *   il NOMME ce qu'il n'a pas touché (`dn_console.c`). Une étiquette juste
     *   sur un périmètre assumé, ⛔ plutôt qu'une promesse trop large.
     * ⚠️ Le cumul porte déjà son étiquette honnête à la lecture : « temps MURAL
     *   par mode DEPUIS LE BOOT ». Il ne ment pas sur lui-même.
     */
    /* ⛔ `s_armee`, `s_cran`, `s_mode` et `s_pct` NE SONT PAS TOUCHÉS : ce sont
     *    des réglages et un état, pas des mesures. Remettre le mode à ACTIF ici
     *    ferait diverger l'état annoncé de l'écran réel. */
}

bool dn_veille_soupcon_appui_fantome(void)
{
    if (!s_armee) {
        return false;
    }
    /* 🔴 RÉÉCRITE EN REVUE DE CODE LE 2026-08-28 — VOIR LE BLOC DE
     *    `s_bascules_forcees` POUR LA DÉMONSTRATION COMPLÈTE.
     *    Ce qui a changé, en une phrase : la fenêtre est **DEPUIS LE DERNIER
     *    RÉVEIL**, ⛔ plus « depuis le boot », et seules les bascules
     *    **AUTOMATIQUES** l'invalident. Sans ça, le détecteur s'éteignait à la
     *    première bascule — c'est-à-dire AVANT que la panne qu'il vise puisse
     *    seulement survenir, puisque `s_consommer` ne se pose qu'en Ambient. */
    if (s_mode != DN_VEILLE_ACTIF) {
        /* On DORT : la garde a cédé, il n'y a rien à soupçonner. ⛔ Ce n'est
         * pas la même chose que « aucune bascule » — c'est plus fort. */
        return false;
    }
    if (s_bascules_auto_depuis_reveil > 0) {
        return false;
    }
    uint32_t delai = dn_veille_delai_ms();
    if (s_inact_max_depuis_reveil_ms >= delai) {
        /* L'inactivité A atteint le délai depuis le réveil : si la bascule n'a
         * pas eu lieu, ce n'est pas un doigt collé — c'est autre chose, et ce
         * détecteur-là n'est pas le bon instrument pour le dire. */
        return false;
    }
    /* ⚠️ LA CONDITION D'OBSERVATION. `s_secondes_depuis_reveil` compte les ticks
     *    1 Hz RÉELLEMENT joués — donc l'uptime OBSERVÉ, `ui off` exclu. Sans
     *    elle, l'alerte sortirait après chaque réveil pendant les `délai`
     *    premières secondes, c'est-à-dire exactement quand tout est normal.
     * 🔴 ET LA COMPARAISON SE FAIT EN **SECONDES**, ⛔ PLUS EN MILLISECONDES.
     *    L'ancienne écriture `s_secondes_vues * 1000u` débordait un `uint32_t`
     *    à **4 294 967 s ≈ 49,7 jours** : passé ce cap, la condition
     *    d'observation redevenait FAUSSE et le détecteur s'éteignait puis se
     *    rallumait tout seul, EN SILENCE — le compteur brut publié restant
     *    juste, l'incohérence était invisible à la relecture. Sur un module
     *    dont le critère n°1 est « une semaine H24 », ⛔ ce n'était pas
     *    théorique. Ici les deux membres tiennent largement : le délai plafonne
     *    à 10 min et la marge à quelques secondes. */
    uint32_t seuil_s = (delai / 1000u) + (uint32_t)DN_VEILLE_MARGE_SOUPCON_S;
    return s_secondes_depuis_reveil > seuil_s;
}

/* ── Les leviers d'AC9 ───────────────────────────────────────────────────── */

int dn_veille_pct(void) { return s_pct; }

esp_err_t dn_veille_set_pct(int pct)
{
    if (pct < DN_VEILLE_PCT_MIN || pct > DN_VEILLE_PCT_MAX) {
        return ESP_ERR_INVALID_ARG;
    }
    s_pct = pct;
    return ESP_OK;
}

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

static uint32_t s_inactivite_ms;
static uint32_t s_inactivite_max_ms;
static uint32_t s_bascules;
static uint32_t s_reveils;
static uint32_t s_rebases;
static uint32_t s_annulations;
static uint32_t s_secondes_vues;
static dn_veille_origine_t s_origine = DN_VEILLE_ORIG_AUCUNE;

/*
 * Le rétroéclairage d'Ambient. ⚠️ VALEUR D'AMORÇAGE, ⛔ PAS UNE VALEUR
 * TRANCHÉE : AC9.1 la fait balayer de 3 à 20 sur la dalle et l'œil décide.
 * 10 % est choisi pour DÉMARRER LE BALAYAGE, sur deux bornes mesurées :
 *   - 3 % est le plancher de LISIBILITÉ de dn1-3 / AC7 (« le Living PCB et le
 *     label s'y distinguent encore, TOUT JUSTE ») — donc trop bas pour un état
 *     de repos qu'on doit pouvoir consulter d'un coup d'œil ;
 *   - `DN_ENV_BL_PCT_MIN = 8` est le plancher de la LOI d'asservissement au
 *     lux, constat owner « c'est ça » — un autre chiffre pour un autre usage.
 * ⛔ Ne pas graver 8 par recopie : ce n'est pas le même arbitrage.
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
    } else if (err != ESP_ERR_NVS_NOT_FOUND) {
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
    } else if (err != ESP_ERR_NVS_NOT_FOUND) {
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

    if (!dn_veille_doit_dormir(s_armee, s_mode, inactivite_ms,
                               dn_veille_delai_ms())) {
        return DN_VEILLE_ACTION_RIEN;
    }

    /* L'état bascule ICI, et l'appelant fait le travail visuel ensuite. S'il
     * n'y parvient pas, il DOIT appeler `dn_veille_annuler_bascule()` — sans
     * quoi la console annoncerait AMBIENT sur un écran resté en couleurs. */
    s_mode = DN_VEILLE_AMBIENT;
    s_bascules++;
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
    s_mode = DN_VEILLE_AMBIENT;
    s_bascules++;
    return true;
}

void dn_veille_annuler_bascule(void)
{
    if (s_mode != DN_VEILLE_AMBIENT) {
        return;
    }
    s_mode = DN_VEILLE_ACTIF;
    if (s_bascules > 0) {
        s_bascules--;
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
    s_mode = DN_VEILLE_ACTIF;
    s_reveils++;
    s_origine = origine;
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
    out->origine = s_origine;
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
    /* ⛔ `s_armee`, `s_cran`, `s_mode` et `s_pct` NE SONT PAS TOUCHÉS : ce sont
     *    des réglages et un état, pas des mesures. Remettre le mode à ACTIF ici
     *    ferait diverger l'état annoncé de l'écran réel. */
}

bool dn_veille_soupcon_appui_fantome(void)
{
    if (!s_armee) {
        return false;
    }
    if (s_bascules > 0) {
        return false;
    }
    uint32_t delai = dn_veille_delai_ms();
    if (s_inactivite_max_ms >= delai) {
        return false;
    }
    /* ⚠️ LA CONDITION D'OBSERVATION. `s_secondes_vues` compte les ticks 1 Hz
     *    RÉELLEMENT joués — donc l'uptime OBSERVÉ, `ui off` exclu. Sans elle,
     *    l'alerte sortirait à chaque boot pendant les `délai` premières
     *    secondes, c'est-à-dire exactement quand tout est normal. */
    uint32_t observe_ms = s_secondes_vues * 1000u;
    return observe_ms > delai + (uint32_t)DN_VEILLE_MARGE_SOUPCON_S * 1000u;
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

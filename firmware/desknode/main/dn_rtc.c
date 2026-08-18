/*
 * dn_rtc — l'heure du module. Voir dn_rtc.h pour ce qui a été MESURÉ avant
 * d'écrire ce fichier, et pour le motif de W1 (driver maison).
 */

#include "dn_rtc.h"

#include "dn_display.h"
#include "dn_pins.h"
#include "dn_ui.h"

#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include <string.h>

static const char *TAG = "dn_rtc";

static i2c_master_dev_handle_t s_dev;
static TaskHandle_t s_tache;

static portMUX_TYPE s_mux = portMUX_INITIALIZER_UNLOCKED;

/* Dernière lecture VALIDE (BCD légal). ⚠️ « valide » ne veut PAS dire
 * « fiable » : une heure peut être parfaitement bien formée et n'avoir aucun
 * sens si OS=1. Les deux notions sont séparées, et c'est tout le sujet. */
static dn_rtc_heure_t s_heure;
static int64_t s_lu_us = -1;
static bool s_os = true; /* pessimiste au boot : tant qu'on n'a pas LU, on ment
                          * si on prétend le contraire */

static uint8_t s_ctrl1_init;
static uint8_t s_ctrl1_lu;
static uint8_t s_temoin_lu;
static bool s_temoin_dispo;
/* 🔴 GÉNÉRATION — correctif de revue (2026-08-18). `tache_rtc` échantillonne
 * l'heure HORS section critique puis l'applique DEDANS. Si `dn_rtc_poser`
 * commite entre les deux, la tâche réécrivait le snapshot PRÉ-POSE : OS=1,
 * 2000-01-01, et `s_lu_us` qui RECULE. Observable : `rtc set` annonçait
 * « posee et RELUE … FIABLE » pendant que la barre retombait à « --:-- » un
 * cycle entier, et `os_vus` s'incrémentait APRÈS une pose réussie.
 * La tâche jette désormais son snapshot si la génération a bougé. */
static uint32_t s_generation;
/* 🔴 Le témoin tel qu'il a été RELU AU BOOT, AVANT toute écriture. C'est LUI
 * qui porte le verdict CROSS-BOOT ; `s_temoin_lu` ne porte que le RUNTIME. */
static uint8_t s_temoin_boot;
static bool s_temoin_boot_dispo;

static dn_rtc_compteurs_t s_cpt;

/* ── BCD ──────────────────────────────────────────────────────────────────── */

/* 🔴 VALIDE AVANT DE CONVERTIR. `bcdToDec` naïf (celui du composant Waveshare :
 * `(val >> 4) * 10 + (val & 0x0F)`) rend 95 pour 0x5F — un nombre plausible,
 * tiré d'un octet illégal. C'est exactement le mensonge que ce dépôt traque : la
 * conversion doit REFUSER, pas arrondir vers le crédible. */
static bool bcd_vers_dec(uint8_t v, uint8_t *out)
{
    uint8_t bas = v & 0x0F;
    uint8_t haut = (uint8_t)(v >> 4);
    if (bas > 9 || haut > 9) {
        return false;
    }
    *out = (uint8_t)(haut * 10 + bas);
    return true;
}

static uint8_t dec_vers_bcd(uint8_t v)
{
    return (uint8_t)(((v / 10) << 4) | (v % 10));
}

/*
 * Jour de semaine CALCULÉ depuis la date (algorithme de Sakamoto), 0 = dimanche.
 * 🔴 Il est calculé et non demandé parce que la puce NE LE DÉDUIT PAS : elle
 * compte son propre registre indépendamment de la date. Laisser l'appelant le
 * fournir, c'est se donner deux sources de vérité pour une même information —
 * et c'est toujours la première qui ment.
 * Vérifié à la main sur la date que la carte affichait au premier allumage :
 * 2000-01-01 -> 6 (samedi), ce qui est exact.
 */
static uint8_t jour_semaine(int annee, int mois, int jour)
{
    static const int k_dec[12] = {0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4};
    int a = annee;
    if (mois < 3) {
        a -= 1;
    }
    int r = (a + a / 4 - a / 100 + a / 400 + k_dec[mois - 1] + jour) % 7;
    return (uint8_t)((r + 7) % 7);
}

static bool date_plausible(const dn_rtc_heure_t *h)
{
    static const uint8_t k_jours[12] = {31, 29, 31, 30, 31, 30,
                                        31, 31, 30, 31, 30, 31};
    if (h->mois < 1 || h->mois > 12 || h->jour < 1) {
        return false;
    }
    if (h->jour > k_jours[h->mois - 1]) {
        return false;
    }
    /* Février non bissextile. 2000..2099 : seul 2100 ferait exception, et il est
     * hors de l'époque du driver. */
    if (h->mois == 2 && h->jour == 29 && (h->annee % 4) != 0) {
        return false;
    }
    return h->heure <= 23 && h->minute <= 59 && h->seconde <= 59;
}

/* ── Transport ────────────────────────────────────────────────────────────── */

static bool lire_regs(uint8_t reg, uint8_t *out, size_t n)
{
    if (!s_dev) {
        return false;
    }
    return i2c_master_transmit_receive(s_dev, &reg, 1, out, n, 200) == ESP_OK;
}

static bool ecrire_regs(uint8_t reg, const uint8_t *src, size_t n)
{
    if (!s_dev || n > 12) {
        return false;
    }
    uint8_t buf[13];
    buf[0] = reg;
    memcpy(&buf[1], src, n);
    return i2c_master_transmit(s_dev, buf, n + 1, 200) == ESP_OK;
}

/*
 * ── LE TÉMOIN ANTI-FANTÔME, ET POURQUOI CE REGISTRE-LÀ ──────────────────────
 *
 * Le patron vient du BME680 (§13.6 bis) : « relire un registre de
 * config/identité À CHAQUE CYCLE et le comparer à celui constaté à l'init ».
 * Transposé bêtement ici, il serait DÉCORATIF — et c'est le piège n°2 de la
 * méthodologie : « cet instrument PEUT-IL voir le défaut qu'il prétend
 * exclure ? »
 *
 * 🔴 CONTROL_1 NE PEUT PAS. Sa valeur de sortie de reset est 0x00, et 0x00 est
 *    EXACTEMENT ce qu'on a mesuré sur la carte. Une puce qui perdrait son
 *    alimentation et redémarrerait relirait donc… 0x00, soit précisément la
 *    référence. Une garde sur Control_1 serait VERTE pendant le défaut qu'elle
 *    prétend détecter.
 *
 * ✅ RAM_byte (0x03) LE PEUT. C'est un octet de RAM libre du variant A, sans
 *    aucun effet sur la marche de l'horloge, et sa valeur de sortie de reset
 *    est 0x00. On y écrit DN_RTC_TEMOIN (0xD7) une fois, à l'init :
 *      · on relit 0xD7   -> la puce n'a pas redémarré depuis notre init ;
 *      · on relit 0x00   -> elle a perdu son alimentation, et l'heure avec ;
 *      · on relit autre  -> quelqu'un d'autre écrit sur ce bus.
 *    La référence n'est plus une valeur qu'on CONSTATE, c'est une valeur qu'on
 *    IMPOSE — et c'est ce qui la rend discriminante.
 *
 * 🔴 ET IL RÉPOND À LA QUESTION DE LA RÉTENTION (AC3) — MAIS SEULEMENT DEPUIS
 *    LE CORRECTIF DU 2026-08-18, QUI LE LIT AVANT DE L'ÉCRIRE.
 *    ⚠️ CETTE LIGNE A MENTI : la première version écrivait sans relire, donc
 *       après toute coupure — et le reboot qui la suit — le témoin valait
 *       `0xD7` quoi qu'il se soit passé. AVEUGLE au cas cross-boot, c'est-à-dire
 *       exactement celui de la rétention. Piège n°2 retourné contre le garde.
 *    ⇒ CORRIGÉ : `temoin_poser()` RELIT d'abord, journalise le verdict, PUIS
 *      écrit. Le témoin porte désormais DEUX verdicts distincts —
 *      `dn_rtc_temoin_boot()` (cross-boot : l'alimentation a-t-elle été coupée
 *      depuis le dernier démarrage ?) et `dn_rtc_temoin_lu()` (runtime : la puce
 *      a-t-elle redémarré PENDANT que le firmware tourne ?).
 *
 * ✅ RÉSULTAT DE LA MESURE DU 2026-08-18 : **CETTE CARTE N'A AUCUNE SAUVEGARDE.**
 *    Coupure USB de 30 s ⇒ au rebranchement, `OS = 1` et l'heure lue vaut
 *    `2000-01-01 00:00:54` — la valeur de sortie de reset, qui a recompté depuis
 *    zéro. ⇒ D5 (« pas de batterie ») ne disait rien d'une cellule de backup du
 *    RTC : il n'y en a pas. L'heure doit être re-posée après toute coupure
 *    secteur, et la barre affiche « --:-- HEURE NON POSÉE » en attendant — ce
 *    qui a été VU sur la dalle, pas déduit.
 *
 * ⚠️ Sur le variant TP, 0x03 est le registre des MINUTES : écrire 0xD7 y serait
 *    destructeur. Le variant A a été CONFIRMÉ PAR LA MESURE avant d'écrire ceci
 *    (0x02/0x03 immobiles pendant que 0x04/0x05 comptent) — voir dn_rtc.h.
 */
static void temoin_poser(void)
{
    /*
     * 🔴 ON LIT AVANT D'ÉCRIRE — CORRECTIF DU 2026-08-18, ET C'EST LA MESURE DE
     *    RÉTENTION QUI L'A EXIGÉ.
     *
     * La première version écrivait `0xD7` sans rien lire. Conséquence : après
     * TOUTE coupure d'alimentation — donc après le reboot qui la suit — le
     * témoin valait `0xD7` quoi qu'il se soit passé, et `rtc` annonçait
     * tranquillement « la puce n'a pas redémarré ». VRAI au sens strict (depuis
     * l'init), et TROMPEUR pour qui cherchait à savoir si l'heure avait survécu.
     *
     * ⚠️ C'était le piège n°2 retourné contre le garde lui-même : « cet
     *    instrument PEUT-IL voir le défaut qu'il prétend exclure ? » — le témoin
     *    voyait très bien un reset de puce EN COURS DE ROUTE (compteur
     *    `temoins_perdus`), et était AVEUGLE au cas cross-boot, qui est
     *    justement celui de la rétention.
     *
     * ⇒ La lecture PRÉALABLE le rend cross-boot : toute coupure future, même
     *   accidentelle, donnera son verdict GRATUITEMENT dans le log de boot.
     *   Le 2026-08-18 c'est `OS` qui a tranché (OS=1 + 2000-01-01 00:00:54) —
     *   il fallait deux témoins, on n'en avait qu'un et demi.
     */
    uint8_t avant = 0;
    if (lire_regs(DN_RTC_REG_RAM, &avant, 1)) {
        s_temoin_boot = avant;
        s_temoin_boot_dispo = true;
        if (avant == DN_RTC_TEMOIN) {
            ESP_LOGI(TAG,
                     "temoin RELU AVANT ecriture = 0x%02X : la puce a GARDE son "
                     "alimentation depuis le dernier boot",
                     avant);
        } else {
            ESP_LOGW(TAG,
                     "🔴 temoin RELU AVANT ecriture = 0x%02X (attendu 0x%02X) : "
                     "la puce a PERDU SON ALIMENTATION depuis le dernier boot "
                     "— OU ce firmware n'a JAMAIS tourne sur cette carte "
                     "(premier boot apres flash : 0x03 vaut alors ce qu'il "
                     "veut). DEUX causes indiscernables, meme consequence : "
                     "l'heure portee ne vaut rien. OS tranche, pas ce temoin.",
                     avant, DN_RTC_TEMOIN);
        }
    } else {
        ESP_LOGW(TAG, "temoin ILLISIBLE avant ecriture — verdict cross-boot "
                      "INDISPONIBLE, et `rtc` le dira");
    }

    uint8_t v = DN_RTC_TEMOIN;
    if (!ecrire_regs(DN_RTC_REG_RAM, &v, 1)) {
        s_temoin_dispo = false;
        ESP_LOGW(TAG, "temoin anti-fantome NON POSE — la garde restera INERTE, "
                      "et `rtc` le dira (« indisponible », pas « conforme »)");
        return;
    }
    uint8_t relu = 0;
    if (!lire_regs(DN_RTC_REG_RAM, &relu, 1) || relu != DN_RTC_TEMOIN) {
        s_temoin_dispo = false;
        ESP_LOGW(TAG,
                 "temoin ecrit mais RELU 0x%02X au lieu de 0x%02X — 0x03 ne se "
                 "comporte pas comme un octet de RAM libre. Garde INERTE.",
                 relu, DN_RTC_TEMOIN);
        return;
    }
    s_temoin_dispo = true;
    s_temoin_lu = relu;
    ESP_LOGI(TAG, "temoin anti-fantome pose en 0x%02X = 0x%02X (relu)",
             DN_RTC_REG_RAM, DN_RTC_TEMOIN);
}

/* ── Le cycle ─────────────────────────────────────────────────────────────── */

/*
 * Lit les 7 registres de temps d'un coup (0x04..0x0A, auto-incrément).
 *
 * ⚠️ GARDE DE BASCULE, ET ELLE EST POSÉE PAR PRÉCAUTION, PAS PAR MESURE. Rien
 *    dans ce dépôt ne prouve que la puce fige ses registres de temps pendant une
 *    lecture, et la règle §13 interdit de le croire sur parole d'une datasheet.
 *    Sans garantie, un burst qui chevauche un passage 59 -> 00 pourrait rendre
 *    les seconds neufs à côté des minutes anciennes. On relit donc les secondes
 *    APRÈS le burst : si elles ont changé, le burst est jeté et retenté au
 *    cycle suivant. Coût : un octet. ⚠️ Ce n'est PAS un fait mesuré, c'est une
 *    garde — ne pas la publier comme un comportement constaté de la puce.
 */
/* 🔴 TRI-ÉTAT — correctif de revue (2026-08-18). Un `bool` ne pouvait pas
 * distinguer les TROIS sorties de cette fonction, et l'appelant rangeait les
 * trois dans `err_bcd`, que `rtc` documente à l'opérateur comme « elle répond
 * mais rend un quartet > 9 ». Un rejet de bascule — qui n'est NI une erreur NI
 * une donnée, comme le dit son propre commentaire — envoyait donc chercher une
 * panne de puce qui n'existe pas. « Deux diagnostics opposés, deux seaux »
 * était écrit dans le code sans y être tenu. */
typedef enum {
    LIRE_OK = 0,      /* heure valide, applicable */
    LIRE_I2C,         /* le transport a échoué */
    LIRE_BASCULE,     /* la seconde a tourné pendant le burst — on retente */
    LIRE_BCD,         /* elle répond, mais le temps ne se décode pas */
} lire_res_t;

static lire_res_t lire_heure(dn_rtc_heure_t *out, bool *os_out)
{
    uint8_t b[7];
    if (!lire_regs(DN_RTC_REG_SECONDES, b, sizeof(b))) {
        return LIRE_I2C;
    }
    uint8_t sec_relu = 0;
    if (!lire_regs(DN_RTC_REG_SECONDES, &sec_relu, 1)) {
        return LIRE_I2C;
    }
    if (sec_relu != b[0]) {
        return LIRE_BASCULE; /* bascule pendant le burst : ni erreur, ni donnée */
    }

    *os_out = (b[0] & DN_RTC_BIT_OS) != 0;

    uint8_t sec, min, heu, jou, jse, moi, ann;
    if (!bcd_vers_dec(b[0] & 0x7F, &sec) || !bcd_vers_dec(b[1] & 0x7F, &min) ||
        !bcd_vers_dec(b[2] & 0x3F, &heu) || !bcd_vers_dec(b[3] & 0x3F, &jou) ||
        !bcd_vers_dec(b[4] & 0x07, &jse) || !bcd_vers_dec(b[5] & 0x1F, &moi) ||
        !bcd_vers_dec(b[6], &ann)) {
        return LIRE_BCD;
    }
    out->seconde = sec;
    out->minute = min;
    out->heure = heu;
    out->jour = jou;
    out->jsem = jse;
    out->mois = moi;
    out->annee = (uint16_t)(DN_RTC_ANNEE_BASE + ann);
    return date_plausible(out) ? LIRE_OK : LIRE_BCD;
}

static void tache_rtc(void *arg)
{
    (void)arg;
    TickType_t reveil = xTaskGetTickCount();

    while (1) {
        /* Cadence en TEMPS ABSOLU : `vTaskDelayUntil` ne dérive pas, là où un
         * `vTaskDelay` ajouterait la durée de la transaction à chaque tour. Sur
         * une HORLOGE, une cadence qui dérive serait particulièrement mal
         * venue — même si ce qui dérive ici est le SONDAGE, pas l'heure. */
        vTaskDelayUntil(&reveil, pdMS_TO_TICKS(DN_RTC_PERIODE_MS));

        if (!s_dev) {
            continue;
        }

        /* La garde anti-fantôme, à chaque cycle — pas seulement quand ça va
         * mal. Un défaut qu'on ne cherche que sur suspicion n'est jamais
         * trouvé. */
        uint8_t ctrl1 = 0, temoin = 0;
        bool garde_ok = lire_regs(DN_RTC_REG_CTRL1, &ctrl1, 1) &&
                        lire_regs(DN_RTC_REG_RAM, &temoin, 1);

        /* 🔴 GÉNÉRATION RELUE AVANT la lecture : si `rtc set` commite pendant
         *    le cycle, le snapshot ci-dessous est PÉRIMÉ et ne doit pas
         *    écraser l'heure fraîchement posée. */
        portENTER_CRITICAL(&s_mux);
        uint32_t gen_avant = s_generation;
        portEXIT_CRITICAL(&s_mux);

        dn_rtc_heure_t h;
        bool os = true;
        lire_res_t res = lire_heure(&h, &os);

        int64_t maintenant = esp_timer_get_time();
        dn_rtc_etat_t avant = dn_rtc_etat();

        portENTER_CRITICAL(&s_mux);
        if (garde_ok) {
            s_ctrl1_lu = ctrl1;
            s_temoin_lu = temoin;
        }
        bool perime = (s_generation != gen_avant);
        if (res == LIRE_OK && !perime) {
            s_heure = h;
            s_lu_us = maintenant;
            s_os = os;
            s_cpt.lectures++;
            if (os) {
                s_cpt.os_vus++;
            }
        } else if (res == LIRE_I2C) {
            s_cpt.err_i2c++;
        } else if (res == LIRE_BASCULE) {
            /* NI erreur, NI donnée : la seconde a tourné entre le burst et sa
             * relecture. Son propre seau — le confondre avec `err_bcd` faisait
             * chercher « un quartet > 9 » sur une puce parfaitement saine. */
            s_cpt.bascules++;
        } else if (res == LIRE_BCD) {
            /* Elle répond (la garde vient de lire deux registres) mais le temps
             * ne se décode pas : c'est une DONNÉE illégale, pas un transport
             * cassé. Deux diagnostics opposés, deux seaux. */
            s_cpt.err_bcd++;
        }
        bool perdu = s_temoin_dispo && garde_ok && temoin != DN_RTC_TEMOIN;
        if (perdu) {
            s_cpt.temoins_perdus++;
        }
        portEXIT_CRITICAL(&s_mux);

        if (perdu) {
            ESP_LOGE(TAG,
                     "🔴 TEMOIN PERDU : 0x03 vaut 0x%02X au lieu de 0x%02X — "
                     "l'horloge a REDEMARRE sous nos pieds (coupure, reset). "
                     "L'heure qu'elle affiche n'a plus de garantie.",
                     temoin, DN_RTC_TEMOIN);
            /* On le repose : sans ça, l'erreur se répéterait à 2 Hz et noierait
             * le log. Le COMPTEUR garde la trace, lui.
             * 🔴 ET LA RÉ-POSE EST VÉRIFIÉE (revue 2026-08-18) : si 0x03 est
             *    lisible mais NON INSCRIPTIBLE, la ré-pose échouait en silence
             *    et c'est justement le noyage qu'elle prétend éviter qui se
             *    produisait — ESP_LOGE à 2 Hz sur la console qui EST le
             *    transport, et `temoins_perdus` montant de 2/s. La garde se
             *    déclare alors INERTE, ce que `rtc` sait déjà dire. */
            uint8_t v = DN_RTC_TEMOIN;
            if (!ecrire_regs(DN_RTC_REG_RAM, &v, 1)) {
                portENTER_CRITICAL(&s_mux);
                s_temoin_dispo = false;
                portEXIT_CRITICAL(&s_mux);
                ESP_LOGE(TAG, "  ré-pose du temoin IMPOSSIBLE — 0x03 n'est pas "
                              "inscriptible. Garde anti-fantome INERTE.");
            }
        }

        dn_rtc_etat_t apres = dn_rtc_etat();
        if (apres == DN_RTC_VIVANT && avant != DN_RTC_VIVANT) {
            portENTER_CRITICAL(&s_mux);
            s_cpt.reprises++;
            portEXIT_CRITICAL(&s_mux);
        }

        /* Snapshot sous le verrou : `h` est indéfini quand la lecture a échoué,
         * et c'est la DERNIÈRE heure valide connue qu'on veut pousser — pas
         * celle du cycle raté. */
        dn_rtc_heure_t vue;
        portENTER_CRITICAL(&s_mux);
        vue = s_heure;
        portEXIT_CRITICAL(&s_mux);

        /* Pousse vers la barre. `dn_ui_heure_maj` prend le verrou LVGL
         * elle-même (contrat des entrées publiques de dn_ui) et ne redessine
         * QUE si le texte affiché change — c'est ce qui rend la cadence de la
         * barre observable en flush/cycle (AC4). */
        /* 🔴 LE RETOUR EST LU (revue 2026-08-18). `false` = verrou LVGL non
         *    pris ⇒ la poussée est PERDUE et la barre garde son texte. Les deux
         *    modules frères le comptent déjà ; le jeter ici rendait une barre
         *    figée par contention (p. ex. `widget nue`, 307-322 ms)
         *    indiscernable d'une barre à jour. Pas de retry immédiat : le cycle
         *    suivant est à 500 ms et repousse la même vue — c'est le compteur
         *    qui manquait, pas la reprise. */
        if (!dn_ui_heure_maj(&vue, apres == DN_RTC_VIVANT, NULL)) {
            portENTER_CRITICAL(&s_mux);
            s_cpt.poussees_perdues++;
            portEXIT_CRITICAL(&s_mux);
        }
    }
}

/* ── API ──────────────────────────────────────────────────────────────────── */

const char *dn_rtc_etat_nom(dn_rtc_etat_t e)
{
    switch (e) {
    case DN_RTC_JAMAIS:
        return "JAMAIS LUE";
    case DN_RTC_VIVANT:
        return "FIABLE";
    case DN_RTC_MUET:
        return "MUETTE";
    case DN_RTC_NON_FIABLE:
        return "NON FIABLE (OS=1)";
    default:
        return "?";
    }
}

dn_rtc_etat_t dn_rtc_etat(void)
{
    portENTER_CRITICAL(&s_mux);
    int64_t lu = s_lu_us;
    bool os = s_os;
    portEXIT_CRITICAL(&s_mux);

    if (lu < 0) {
        return DN_RTC_JAMAIS;
    }
    if ((esp_timer_get_time() - lu) >= DN_RTC_PEREMPTION_US) {
        return DN_RTC_MUET;
    }
    /* 🔴 L'ORDRE COMPTE : la péremption d'abord, OS ensuite. Une puce muette
     * dont la dernière lecture disait OS=0 ne doit pas passer pour fiable. */
    return os ? DN_RTC_NON_FIABLE : DN_RTC_VIVANT;
}

bool dn_rtc_lire(dn_rtc_heure_t *out)
{
    if (!out) {
        return false;
    }
    portENTER_CRITICAL(&s_mux);
    *out = s_heure;
    portEXIT_CRITICAL(&s_mux);
    return dn_rtc_etat() == DN_RTC_VIVANT;
}

int64_t dn_rtc_age_us(void)
{
    portENTER_CRITICAL(&s_mux);
    int64_t lu = s_lu_us;
    portEXIT_CRITICAL(&s_mux);
    return (lu < 0) ? -1 : esp_timer_get_time() - lu;
}

esp_err_t dn_rtc_poser(const dn_rtc_heure_t *h)
{
    if (!h) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_dev) {
        return ESP_ERR_INVALID_STATE;
    }
    dn_rtc_heure_t v = *h;
    if (v.annee < DN_RTC_ANNEE_BASE || v.annee > DN_RTC_ANNEE_BASE + 99) {
        return ESP_ERR_INVALID_ARG;
    }
    /* 🔴 L'ORDRE EST UN CORRECTIF DE REVUE (2026-08-18) : `jour_semaine()`
     *    indexe `k_dec[mois - 1]` sans borne. L'appeler AVANT `date_plausible`
     *    faisait lire hors tableau pour tout mois invalide venu de la console
     *    (`rtc set 2026-13-01 …` -> k_dec[12] ; `2026-0-01` -> k_dec[-1]). La
     *    valeur était ensuite jetée, mais c'est de l'UB — et `barre_composer`
     *    fait explicitement l'inverse, avec le commentaire qui l'exige. */
    if (!date_plausible(&v)) {
        return ESP_ERR_INVALID_ARG;
    }
    v.jsem = jour_semaine(v.annee, v.mois, v.jour);

    /* 🔴 LES SECONDES SONT ÉCRITES SANS LE BIT OS, ET C'EST LE GESTE ENTIER :
     * écrire ce registre est ce qui REMET OS À 0 côté puce. C'est la seule
     * façon de faire passer l'heure de « non fiable » à « fiable », et il n'y a
     * pas d'autre chemin — d'où l'absence de tout `dn_rtc_clear_os()`, qui
     * laisserait croire qu'on peut déclarer fiable une heure qu'on n'a pas
     * posée. */
    uint8_t b[7] = {
        dec_vers_bcd(v.seconde), dec_vers_bcd(v.minute), dec_vers_bcd(v.heure),
        dec_vers_bcd(v.jour),    dec_vers_bcd(v.jsem),   dec_vers_bcd(v.mois),
        dec_vers_bcd((uint8_t)(v.annee - DN_RTC_ANNEE_BASE)),
    };
    if (!ecrire_regs(DN_RTC_REG_SECONDES, b, sizeof(b))) {
        return ESP_FAIL;
    }

    /* RELIRE, pas supposer : c'est la règle du dépôt (« ce qui est affiché doit
     * être RELU de l'état réel »), et ici elle a un effet concret — si OS ne
     * retombe pas, la pose a ÉCHOUÉ même si l'I²C a acquitté. */
    /* 🔴 LES SEPT REGISTRES SONT RELUS ET COMPARÉS (revue 2026-08-18).
     *    La version précédente ne relisait QUE le registre des secondes et n'y
     *    testait QUE le bit OS : minutes, heures, jour, jsem, mois, année et la
     *    VALEUR des secondes n'étaient jamais vérifiées. Une puce qui acquitte
     *    l'écriture et range autre chose passait le contrôle, et la console
     *    affirmait pourtant « l'ecriture est RELUE : un ESP_OK d'I2C ne prouve
     *    rien ». C'est le mensonge d'instrument que ce dépôt traque.
     * ⚠️ La seconde a le droit d'avoir AVANCÉ entre l'écriture et la relecture
     *    (l'oscillateur tourne) : on tolère un écart de 0 ou 1 sur ce seul
     *    champ, et on refuse tout le reste. */
    uint8_t r[7] = {0};
    if (!lire_regs(DN_RTC_REG_SECONDES, r, sizeof(r))) {
        return ESP_FAIL;
    }
    if (r[0] & DN_RTC_BIT_OS) {
        ESP_LOGE(TAG, "heure ecrite mais OS RESTE A 1 — la pose n'a PAS pris");
        return ESP_FAIL;
    }
    uint8_t sec_relu = 0;
    if (!bcd_vers_dec(r[0] & 0x7F, &sec_relu)) {
        ESP_LOGE(TAG, "relecture : secondes non BCD (0x%02X) — pose REFUSEE", r[0]);
        return ESP_FAIL;
    }
    uint8_t ecart = (uint8_t)((sec_relu >= v.seconde) ? (sec_relu - v.seconde)
                                                      : (60 + sec_relu - v.seconde));
    if (ecart > 1 || r[1] != b[1] || r[2] != b[2] || r[3] != b[3] ||
        r[4] != b[4] || r[5] != b[5] || r[6] != b[6]) {
        ESP_LOGE(TAG,
                 "🔴 RELECTURE DIVERGENTE — ecrit %02X %02X %02X %02X %02X %02X %02X, "
                 "relu %02X %02X %02X %02X %02X %02X %02X. La puce a ACQUITTE et "
                 "range autre chose : pose REFUSEE.",
                 b[0], b[1], b[2], b[3], b[4], b[5], b[6],
                 r[0], r[1], r[2], r[3], r[4], r[5], r[6]);
        return ESP_FAIL;
    }
    v.seconde = sec_relu; /* ce que la PUCE porte, pas ce qu'on a tapé */

    portENTER_CRITICAL(&s_mux);
    s_heure = v;
    s_lu_us = esp_timer_get_time();
    s_os = false;
    s_cpt.poses++;
    s_generation++; /* invalide tout snapshot de cycle en vol */
    portEXIT_CRITICAL(&s_mux);

    ESP_LOGI(TAG, "heure posee : %04u-%02u-%02u %02u:%02u:%02u (jsem %u) — OS retombe a 0",
             v.annee, v.mois, v.jour, v.heure, v.minute, v.seconde, v.jsem);
    return ESP_OK;
}

void dn_rtc_compteurs(dn_rtc_compteurs_t *out)
{
    if (!out) {
        return;
    }
    portENTER_CRITICAL(&s_mux);
    *out = s_cpt;
    portEXIT_CRITICAL(&s_mux);
}

void dn_rtc_reset_compteurs(void)
{
    portENTER_CRITICAL(&s_mux);
    memset(&s_cpt, 0, sizeof(s_cpt));
    portEXIT_CRITICAL(&s_mux);
}

esp_err_t dn_rtc_registres(uint8_t *out, uint8_t n)
{
    if (!out || n == 0 || n > DN_RTC_REG_MAX) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_dev) {
        return ESP_ERR_INVALID_STATE;
    }
    return lire_regs(0x00, out, n) ? ESP_OK : ESP_FAIL;
}

bool dn_rtc_arme(void) { return s_dev != NULL; }

bool dn_rtc_os(void)
{
    portENTER_CRITICAL(&s_mux);
    bool os = s_os;
    portEXIT_CRITICAL(&s_mux);
    return os;
}

uint8_t dn_rtc_ctrl1_init(void) { return s_ctrl1_init; }
uint8_t dn_rtc_ctrl1_lu(void) { return s_ctrl1_lu; }
uint8_t dn_rtc_temoin_lu(void) { return s_temoin_lu; }
bool dn_rtc_temoin_dispo(void) { return s_temoin_dispo; }

bool dn_rtc_temoin_boot(uint8_t *out)
{
    if (out) {
        *out = s_temoin_boot;
    }
    return s_temoin_boot_dispo;
}

uint32_t dn_rtc_pile_libre(void)
{
    /* `uxTaskGetStackHighWaterMark` rend un nombre de MOTS, pas d'octets — la
     * confusion est classique et donnerait un chiffre 4 fois trop petit. */
    return s_tache ? (uint32_t)uxTaskGetStackHighWaterMark(s_tache) *
                         sizeof(StackType_t)
                   : 0;
}

esp_err_t dn_rtc_init(void)
{
    i2c_master_bus_handle_t bus = dn_display_i2c_bus();
    if (!bus) {
        ESP_LOGE(TAG, "bus I2C absent — dn_display_init() n'a pas tourne");
        return ESP_ERR_INVALID_STATE;
    }

    /* ⚠️ LA FRÉQUENCE SE POSE PAR DEVICE, jamais par bus :
     * `i2c_master_bus_config_t` n'a AUCUN champ d'horloge en IDF 5.x.
     * ⚠️ Le type est `i2c_device_config_t`, PAS `i2c_master_dev_config_t` (qui
     *    n'existe pas) — piège de compilation consigné par dn2-1, dont l'erreur
     *    ne sort qu'en aval sur un « incompatible pointer type ». */
    i2c_device_config_t cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = DN_RTC_ADDR,
        .scl_speed_hz = DN_I2C_FREQ_HZ,
    };
    if (i2c_master_bus_add_device(bus, &cfg, &s_dev) != ESP_OK) {
        ESP_LOGE(TAG, "device I2C 0x%02X non cree — la barre affichera « --:-- »",
                 DN_RTC_ADDR);
        s_dev = NULL;
        return ESP_ERR_NOT_FOUND;
    }

    /* Identité : la puce n'a AUCUN registre de type « chip id » (contrairement
     * au BME680 et à ses 0xD0/0xF0). Ce qu'on relève à la place, c'est l'état
     * de contrôle constaté — il sert de référence imprimable, PAS de garde
     * (voir `temoin_poser` : Control_1 ne peut pas voir un redémarrage). */
    if (!lire_regs(DN_RTC_REG_CTRL1, &s_ctrl1_init, 1)) {
        ESP_LOGE(TAG,
                 "0x%02X repond au scan mais Control_1 est ILLISIBLE — module "
                 "DESARME (la barre dira « --:-- », et `rtc` dira pourquoi)",
                 DN_RTC_ADDR);
        i2c_master_bus_rm_device(s_dev);
        s_dev = NULL;
        return ESP_ERR_NOT_FOUND;
    }
    s_ctrl1_lu = s_ctrl1_init;

    ESP_LOGI(TAG,
             "PCF85063A @ 0x%02X — Control_1 = 0x%02X : %s, format %s, quartz %s",
             DN_RTC_ADDR, s_ctrl1_init,
             (s_ctrl1_init & DN_RTC_BIT_STOP) ? "ARRETEE (STOP=1)" : "tourne",
             (s_ctrl1_init & 0x02) ? "12 h" : "24 h",
             (s_ctrl1_init & 0x01) ? "12,5 pF" : "7 pF");
    ESP_LOGW(TAG, "  ⚠️ CAP_SEL n'est PAS verifie : rien sur cette carte ne dit "
                  "quel quartz est soude. Un mauvais reglage se paie en DERIVE, "
                  "pas en panne. Laisse tel quel, consigne comme INCONNU.");

    /*
     * 🔴 CONTROL_1 ÉTAIT LU, AFFICHÉ, ET JAMAIS APPLIQUÉ — correctif de revue
     *    (2026-08-18). Deux bits gouvernent la validité de tout ce que ce
     *    module rend, et aucun des deux n'était traité :
     *
     *    · STOP=1  — les compteurs GÈLENT, mais OS reste 0, le BCD reste légal
     *                et `date_plausible` passe. `dn_rtc_etat()` rendait donc
     *                VIVANT et la barre affichait une heure FIGÉE en blanc
     *                « fiable », indéfiniment. `rtc set` ne pouvait pas la
     *                récupérer (il n'écrit que 0x04..0x0A) et rapportait un
     *                succès, puisque OS retombe bien à 0.
     *    · 12_24=1 — le bit 5 de l'octet heures devient AM/PM au lieu du
     *                dizaine d'heures. `lire_heure` décode inconditionnellement
     *                en 24 h (`b[2] & 0x3F`) ⇒ heure PLAUSIBLE ET FAUSSE, qui
     *                passe le BCD, OS et la péremption.
     *
     *    Les deux violent frontalement AC3 : « ⛔ Jamais une heure fausse ».
     * ⚠️ Probabilité MESURÉE nulle sur cette carte (Control_1 relevé à 0x00,
     *    §13.15) — c'est un trou de conception qu'on ferme, pas un défaut
     *    constaté. On CORRIGE puis on RELIT ; si la correction ne prend pas, on
     *    DÉSARME, parce qu'une horloge dont on ne maîtrise pas le mode est
     *    exactement ce que la barre ne doit pas relayer.
     * ⛔ Ce qui reste NON couvert : un oscillateur qui s'arrête tout seul
     *    (quartz mort) avec STOP=0. Il faudrait un détecteur de VIVACITÉ — les
     *    secondes avancent-elles ? — qui est du périmètre neuf : porté au
     *    ledger, pas improvisé ici.
     */
    if (s_ctrl1_init & (DN_RTC_BIT_STOP | DN_RTC_BIT_1224)) {
        uint8_t corrige = (uint8_t)(s_ctrl1_init & ~(DN_RTC_BIT_STOP | DN_RTC_BIT_1224));
        ESP_LOGW(TAG,
                 "🔴 Control_1 = 0x%02X : %s%s— CORRECTION vers 0x%02X",
                 s_ctrl1_init,
                 (s_ctrl1_init & DN_RTC_BIT_STOP) ? "horloge ARRETEE " : "",
                 (s_ctrl1_init & DN_RTC_BIT_1224) ? "format 12 h " : "", corrige);
        uint8_t relu = 0xFF;
        if (!ecrire_regs(DN_RTC_REG_CTRL1, &corrige, 1) ||
            !lire_regs(DN_RTC_REG_CTRL1, &relu, 1) ||
            (relu & (DN_RTC_BIT_STOP | DN_RTC_BIT_1224))) {
            ESP_LOGE(TAG,
                     "🔴 CORRECTION REFUSEE (Control_1 relu 0x%02X) — module "
                     "DESARME. Une heure figee ou en 12 h serait PLAUSIBLE ET "
                     "FAUSSE, et la barre doit se taire plutot que la relayer.",
                     relu);
            i2c_master_bus_rm_device(s_dev);
            s_dev = NULL;
            return ESP_ERR_INVALID_STATE;
        }
        s_ctrl1_init = relu;
        s_ctrl1_lu = relu;
        ESP_LOGI(TAG, "  Control_1 corrige et RELU = 0x%02X : tourne, format 24 h",
                 relu);
    }

    temoin_poser();

    /* Première lecture SYNCHRONE : le bandeau de boot doit pouvoir dire l'état
     * de l'heure, et pas « on verra dans 500 ms ». */
    dn_rtc_heure_t h;
    bool os = true;
    if (lire_heure(&h, &os) == LIRE_OK) {
        portENTER_CRITICAL(&s_mux);
        s_heure = h;
        s_lu_us = esp_timer_get_time();
        s_os = os;
        s_cpt.lectures++;
        if (os) {
            s_cpt.os_vus++;
        }
        portEXIT_CRITICAL(&s_mux);

        if (os) {
            ESP_LOGW(TAG,
                     "🔴 OS = 1 — l'oscillateur s'est ARRETE : l'heure lue "
                     "(%04u-%02u-%02u %02u:%02u:%02u) N'EST PAS FIABLE. La barre "
                     "affichera « --:-- HEURE NON POSEE ». `rtc set` pour la poser.",
                     h.annee, h.mois, h.jour, h.heure, h.minute, h.seconde);
        } else {
            ESP_LOGI(TAG, "heure FIABLE : %04u-%02u-%02u %02u:%02u:%02u",
                     h.annee, h.mois, h.jour, h.heure, h.minute, h.seconde);
        }
    } else {
        ESP_LOGE(TAG, "premiere lecture de l'heure ECHOUEE — etat JAMAIS LUE");
    }

    /* 🔴 4 096 o DE PILE, ET ILS VIENNENT DE LA RAM INTERNE — la ressource même
     * qui a tué la branche WiFi en dn2-2 (53 480 o de .bss, 6 407 o libres
     * après init). Même taille et même priorité que `dn_capt` et `dn_link`, pour
     * que les trois modules de données restent comparables. Le high-water mark
     * est exposé par `dn_rtc_pile_libre()` : réduire cette valeur demandera une
     * MESURE, pas une intuition. */
    BaseType_t ok = xTaskCreate(tache_rtc, "dn_rtc", 4096, NULL, 3, &s_tache);
    if (ok != pdPASS) {
        /* Même ménage que dn_capteurs : sans tâche, aucune lecture n'aura lieu.
         * Laisser `s_dev` non-NULL ferait répondre « armé » à la console pour un
         * module qui ne tournera jamais. */
        ESP_LOGE(TAG, "xTaskCreate a echoue — RAM interne insuffisante. Le module "
                      "se DESARME entierement.");
        i2c_master_bus_rm_device(s_dev);
        s_dev = NULL;
        s_tache = NULL;
        return ESP_ERR_NO_MEM;
    }
    return ESP_OK;
}

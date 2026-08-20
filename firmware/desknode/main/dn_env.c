/*
 * dn_env — lecture EN RÉGIME des trois capteurs d'environnement (dn4-3, P9.3).
 * Contrat, arbitrages et loi du rétroéclairage : dn_env.h. Mesures : §13.19.
 *
 * 🔴 RÈGLE ABSOLUE DE CE FICHIER : ⛔ AUCUN `ESP_ERROR_CHECK` sur une
 * transaction I²C. C'est exactement ce qui briquait la carte
 * (`bme680.c:432` — 6 briquages sur 7 avant la parade). Ici, TOUT retour est
 * testé et TOUTE erreur est comptée, jamais fatale.
 */
#include "dn_env.h"

#include <stdlib.h>
#include <string.h>

#include "driver/i2c_master.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"

#include "dn_capteurs.h"
#include "dn_display.h"
#include "dn_pins.h"

static const char *TAG = "dn_env";

/* 🔴 La cadence de ce module EST celle de la tâche qui l'appelle. Si quelqu'un
 * change DN_CAPT_PERIODE_MS sans toucher ici, la péremption et le backoff
 * deviendraient faux EN SILENCE. Le compilateur le refuse maintenant. */
_Static_assert(DN_ENV_PERIODE_MS == DN_CAPT_PERIODE_MS,
               "dn_env est cadence par la tache dn_capt : les deux periodes "
               "doivent etre identiques, sinon peremption et backoff mentent");

/* ── Opcodes et registres, TOUS QUALIFIÉS SUR LA CARTE avant d'être écrits ici
 *    (§13.19.5) — ⛔ aucun recopié d'un article. */

/* BH1750 : ⛔ AUCUN registre, que des OPCODES. Le composant ne sait pas lire un
 * index : on lui envoie un octet, il obéit ; on lit deux octets, il rend sa
 * dernière conversion. C'est tout le protocole. */
#define BH1750_OP_POWER_ON   0x01
#define BH1750_OP_CONT_HRES  0x10 /* 1 lx, 120 ms typique, 180 ms au pire */
/* ⚠️ MESURÉ EN DIRECT : après l'opcode, la PREMIÈRE lecture rend 00 00. Une
 * lecture unique aurait déclaré mort un capteur qui fonctionne. */
#define BH1750_CONV_MAX_US   (180 * 1000)

/* INA219 — registres TI SBOS448G §8.6.2 */
/* ⚠️ SEULS `CONFIG` ET `CALIB` SONT ENCORE UTILISÉS (par `configurer()`, UNE fois
 * au boot). Les quatre registres de VALEUR ci-dessous ne sont plus lus depuis le
 * correct-course du 2026-08-20 — ils sont CONSERVÉS À DESSEIN, avec leur
 * datasheet, pour que remettre le composant en service ne demande pas de
 * re-fouiller TI SBOS448G. ⛔ Deadness DÉCLARÉE, pas silencieuse : c'est le
 * défaut « macros mortes » que la revue `dn4-2` a déjà relevé une fois. */
#define INA219_REG_CONFIG    0x00 /* reset 0x399F, VÉRIFIÉ sur la carte — UTILISÉ */
#define INA219_REG_CALIB     0x05 /* reset 0x0000, VÉRIFIÉ sur la carte — UTILISÉ */
#define INA219_REG_SHUNT     0x01 /* signé, LSB 10 µV                  — non lu */
#define INA219_REG_BUS       0x02 /* bits 15:3, LSB 4 mV ; b1 CNVR ; b0 OVF — non lu */
#define INA219_REG_POWER     0x03 /*                                    — non lu */
#define INA219_REG_CURRENT   0x04 /* signé                              — non lu */
#define INA219_CONFIG_VOULU  0x399Fu

/*
 * 🔴 LA CALIBRATION EST À LA FOIS LA CONFIG *ET* LE TÉMOIN ANTI-FANTÔME.
 *
 * Shunt du breakout CJMCU : R100 = 0,1 Ω, courant max 3,2 A (sérigraphie +
 * §13.16.6). TI SBOS448G §8.5.1 :
 *     Current_LSB = I_max / 32768 = 3,2 / 32768 = 97,66 µA  -> arrondi à 100 µA
 *     Cal = trunc(0,04096 / (Current_LSB × R_shunt))
 *         = trunc(0,04096 / (0,0001 × 0,1)) = 4096 = 0x1000
 * ⇒ Current_LSB = 0,1 mA  et  Power_LSB = 20 × Current_LSB = 2 mW.
 *
 * ⚠️ §13.16.6 avait éprouvé le témoin avec la valeur ARBITRAIRE `0xD7A4`. On
 * garde le PATRON (registre inscriptible, relisible, reset 0x0000 ≠ valeur
 * imposée) et on remplace la valeur arbitraire par la valeur UTILE : un témoin
 * qui est aussi la configuration ne peut pas être oublié au prochain refactor.
 * ⛔ Le patron §13.15.4 est respecté : 0x1000 ≠ 0x0000.
 */
#define INA219_CALIB_VOULU   0x1000u
/* ⚠️ Non utilisés depuis le correct-course du 2026-08-20 — conservés avec leur
 * dérivation (§8.5.1) pour une remise en service sans recalcul. */
#define INA219_CURRENT_LSB_DIXIEME_MA 1 /* Current_LSB = 0,1 mA -> le registre PORTE les dixièmes */
#define INA219_POWER_LSB_MW  2          /* Power_LSB = 20 x Current_LSB = 2 mW */

/* VL6180X — registres PUBLICS, index sur 16 BITS, MSB d'abord */
#define VL_REG_MODEL_ID      0x0000u /* = 0xB4 */
#define VL_REG_FRESH_RESET   0x0016u /* 0x01 au power-on ; inscriptible/relisible */
#define VL_REG_ALS_START     0x0038u
#define VL_REG_ALS_GAIN      0x003Fu /* reset 0x06 ; on impose 0x46 (gain 1,0×) */
#define VL_REG_ALS_INTEG_HI  0x0040u
#define VL_REG_ALS_INTEG_LO  0x0041u /* on impose 0x63 = 99 -> 100 ms */
#define VL_REG_INT_CONFIG    0x0014u /* reset 0x00 ; on impose 0x20 (ALS ready) */
#define VL_MODEL_ID_ATTENDU  0xB4u
#define VL_GAIN_VOULU        0x46u
#define VL_INTEG_LO_VOULU    0x63u
#define VL_INT_CONFIG_VOULU  0x20u

/*
 * ── 🔴 LES BORNES PHYSIQUES, ET LEUR SOURCE — sans elles `err_bornes` n'a rien
 *    à comparer, et AC1 le dit : « un seau qui n'a rien à comparer est un
 *    compteur décoratif ».
 *
 * BH1750 (ROHM BH1750FVI-TR, « Measurement range 1 – 65535 lx », résolution
 *   1 lx, lux = brut / 1,2 au MTreg par défaut 69) :
 *   ⚠️ le brut est un `uint16` : il NE PEUT PAS sortir de 0..65535, donc borner
 *      la VALEUR serait un compteur inatteignable. La seule borne ATTEIGNABLE
 *      et signifiante est le PLAFOND du convertisseur : 0xFFFF n'est plus une
 *      mesure, c'est « au moins 54 612 lx ».
 *   ⚠️ Et 0x0000 est une valeur LÉGITIME (obscurité complète) : la main posée
 *      sur le capteur a mesuré brut = 2, pas 0. ⛔ Ne pas le compter en bornes.
 *
 * INA219 (TI SBOS448G) :
 *   · Bus, §8.6.2.3 : bits 15:3, LSB 4 mV, BRNG=1 ⇒ pleine échelle 32 760 mV.
 *     Le bit 0 est OVF (Math Overflow) : c'est le SEUL dépassement que la puce
 *     sache signaler elle-même. ⇒ c'est lui qu'on compte.
 *   · Shunt, §8.6.2.2 : signé, LSB 10 µV, PGA ÷8 ⇒ pleine échelle ±320 mV. Le
 *     registre 16 bits signé peut porter ±327 680 µV : la bande 320 001..327 680
 *     est donc ATTEIGNABLE et signale un écrêtage du PGA.
 */
#define BH1750_BRUT_SATURE   0xFFFFu
/* ⛔ Les bornes physiques de l'INA219 ont été RETIRÉES avec ses grandeurs
 * (correct-course 2026-08-20). Sources à ressortir si le shunt est un jour
 * câblé : TI SBOS448G §8.5.1 (calibration) et §8.6.2 (registres). */

/* ── État ─────────────────────────────────────────────────────────────────── */

/* portMUX, ⛔ pas un mutex : les `int64` sont DÉCHIRABLES sur Xtensa, et ce
 * module est lu depuis le REPL pendant que la tâche dn_capt écrit. */
static portMUX_TYPE s_mux = portMUX_INITIALIZER_UNLOCKED;

typedef struct {
    i2c_master_dev_handle_t dev;
    dn_env_compteurs_t cnt;
    int64_t derniere_us;   /* esp_timer de la dernière lecture VALIDE, -1 sinon */
    bool degrade;          /* une erreur est survenue depuis la dernière valide */
    bool a_deja_lu;
    int cycles_avant_reinit;
    int64_t config_us;     /* instant de la dernière (re)configuration RÉUSSIE */
    /* 🔴 AJOUTÉ EN REVUE DE CODE LE 2026-08-20 — voir `cycle_un()`. Sans ce
     * drapeau, un capteur dont la configuration ÉCHOUE au boot n'est JAMAIS
     * reconfiguré : `dev` n'est jamais remis à NULL, et la garde de conformité
     * du BH1750 rend `CONF_OK` en dur. */
    bool config_posee;
} env_capteur_t;

static env_capteur_t s_c[DN_ENV_NB];

static int s_lux = DN_ENV_ABSENT;
static int s_lux_brut = DN_ENV_ABSENT;

static uint32_t s_cycles;
static int64_t s_duree_cycle_us;
static bool s_init_faite;

/* Rétroéclairage automatique */
static bool s_bl_auto = DN_ENV_BL_AUTO_DEFAUT;
static int s_bl_lux_bas = DN_ENV_BL_LUX_BAS;
static int s_bl_lux_haut = DN_ENV_BL_LUX_HAUT;
static int s_bl_pas = DN_ENV_BL_PAS_MAX;
static int s_bl_pct_min = DN_ENV_BL_PCT_MIN;
static int s_bl_dernier_pct = -1;  /* -1 = la loi n'a encore rien appliqué */
static int s_bl_dernier_lux = DN_ENV_ABSENT;
static bool s_bl_muet_dit;         /* le « capteur muet » n'est journalisé qu'une fois */

static const char *k_nom[DN_ENV_NB] = { "BH1750", "INA219", "VL6180X" };
static const uint8_t k_addr[DN_ENV_NB] = {
    DN_BH1750_ADDR, DN_INA219_ADDR, DN_VL6180X_ADDR,
};

/* ── Primitives I²C — retour TESTÉ partout, ⛔ jamais enveloppé ────────────── */

static esp_err_t ecrire(dn_env_id_t id, const uint8_t *o, size_t n)
{
    if (!s_c[id].dev) {
        return ESP_ERR_INVALID_STATE;
    }
    return i2c_master_transmit(s_c[id].dev, o, n,
                               pdMS_TO_TICKS(DN_ENV_I2C_TIMEOUT_MS));
}

/* Lecture NUE (sans index) — le protocole du BH1750, et de lui seul. */
static esp_err_t lire_nu(dn_env_id_t id, uint8_t *buf, size_t n)
{
    if (!s_c[id].dev) {
        return ESP_ERR_INVALID_STATE;
    }
    return i2c_master_receive(s_c[id].dev, buf, n,
                              pdMS_TO_TICKS(DN_ENV_I2C_TIMEOUT_MS));
}

/* Index de registre sur 8 bits — l'INA219. */
static esp_err_t lire_reg8(dn_env_id_t id, uint8_t reg, uint8_t *buf, size_t n)
{
    if (!s_c[id].dev) {
        return ESP_ERR_INVALID_STATE;
    }
    return i2c_master_transmit_receive(s_c[id].dev, &reg, 1, buf, n,
                                       pdMS_TO_TICKS(DN_ENV_I2C_TIMEOUT_MS));
}

/* Index de registre sur 16 bits, MSB d'abord — le VL6180X.
 * ⚠️ C'est exactement ce qui distingue cette puce d'un VL53L0X, et ce qui a
 *    permis de REFUTER l'étiquette « VL53L0X » (§13.16.7). */
static esp_err_t lire_reg16(dn_env_id_t id, uint16_t reg, uint8_t *buf, size_t n)
{
    if (!s_c[id].dev) {
        return ESP_ERR_INVALID_STATE;
    }
    const uint8_t idx[2] = { (uint8_t)(reg >> 8), (uint8_t)(reg & 0xFF) };
    return i2c_master_transmit_receive(s_c[id].dev, idx, 2, buf, n,
                                       pdMS_TO_TICKS(DN_ENV_I2C_TIMEOUT_MS));
}

static esp_err_t ecrire_reg16(dn_env_id_t id, uint16_t reg, uint8_t val)
{
    const uint8_t o[3] = { (uint8_t)(reg >> 8), (uint8_t)(reg & 0xFF), val };
    return ecrire(id, o, sizeof o);
}

static esp_err_t ecrire_reg8_16b(dn_env_id_t id, uint8_t reg, uint16_t val)
{
    const uint8_t o[3] = { reg, (uint8_t)(val >> 8), (uint8_t)(val & 0xFF) };
    return ecrire(id, o, sizeof o);
}

/* ── Comptage ─────────────────────────────────────────────────────────────── */

static void compter_i2c(dn_env_id_t id)
{
    portENTER_CRITICAL(&s_mux);
    s_c[id].cnt.err_i2c++;
    portEXIT_CRITICAL(&s_mux);
    s_c[id].degrade = true;
}

static void compter_donnee(dn_env_id_t id)
{
    portENTER_CRITICAL(&s_mux);
    s_c[id].cnt.err_donnee++;
    portEXIT_CRITICAL(&s_mux);
    s_c[id].degrade = true;
}

static void compter_bornes(dn_env_id_t id)
{
    portENTER_CRITICAL(&s_mux);
    s_c[id].cnt.err_bornes++;
    portEXIT_CRITICAL(&s_mux);
    s_c[id].degrade = true;
}

/* Une lecture VALIDE vient d'aboutir : horodate, compte, et détecte la reprise. */
static void marquer_valide(dn_env_id_t id)
{
    bool reprise = s_c[id].degrade && s_c[id].a_deja_lu;
    s_c[id].degrade = false;
    s_c[id].a_deja_lu = true;
    portENTER_CRITICAL(&s_mux);
    s_c[id].cnt.lectures++;
    if (reprise) {
        s_c[id].cnt.reprises++;
    }
    s_c[id].derniere_us = esp_timer_get_time();
    portEXIT_CRITICAL(&s_mux);
}

/* ── Ouverture et configuration ───────────────────────────────────────────── */

static esp_err_t ouvrir(dn_env_id_t id)
{
    i2c_master_bus_handle_t bus = dn_display_i2c_bus();
    if (!bus) {
        return ESP_ERR_INVALID_STATE;
    }
    const i2c_device_config_t cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = k_addr[id],
        .scl_speed_hz = DN_I2C_FREQ_HZ,
    };
    i2c_master_dev_handle_t dev = NULL;
    esp_err_t e = i2c_master_bus_add_device(bus, &cfg, &dev);
    if (e != ESP_OK) {
        return e;
    }
    s_c[id].dev = dev;
    return ESP_OK;
}

/* Pose la configuration du capteur. Rend ESP_OK si TOUTE la séquence a été
 * acquittée. ⚠️ « acquittée » ne veut pas dire « obéie » : c'est la RELECTURE de
 * conformité du cycle suivant qui le prouve — patron `config LUE (conforme)` du
 * BME680, et c'est aussi la garde anti-fantôme (voir plus bas). */
static esp_err_t configurer(dn_env_id_t id)
{
    esp_err_t e = ESP_OK;
    /* 🔴 On DÉSARME d'abord : tant que cette séquence n'a pas abouti, la
     * configuration N'EST PAS POSÉE, et `cycle_un()` doit la reposer. */
    s_c[id].config_posee = false;
    switch (id) {
    case DN_ENV_LUM: {
        /* Deux opcodes, dans cet ordre, et RIEN d'autre : le BH1750 n'a pas de
         * registre. Après le second, la première conversion demande 120 ms
         * typiques, 180 au pire — d'où l'horodatage `config_us`. */
        const uint8_t on = BH1750_OP_POWER_ON;
        const uint8_t mode = BH1750_OP_CONT_HRES;
        e = ecrire(id, &on, 1);
        if (e == ESP_OK) {
            e = ecrire(id, &mode, 1);
        }
        break;
    }
    case DN_ENV_ALIM:
        e = ecrire_reg8_16b(id, INA219_REG_CONFIG, INA219_CONFIG_VOULU);
        if (e == ESP_OK) {
            e = ecrire_reg8_16b(id, INA219_REG_CALIB, INA219_CALIB_VOULU);
        }
        break;
    case DN_ENV_TOF:
        /* ⛔ On ne touche PAS à SYSTEM__FRESH_OUT_OF_RESET : sa valeur est un
         * FAIT sur l'historique de la puce, et l'écraser détruirait
         * l'information. Les trois registres ci-dessous suffisent au témoin :
         * chacun a une valeur de reset DIFFÉRENTE de celle qu'on impose. */
        e = ecrire_reg16(id, VL_REG_INT_CONFIG, VL_INT_CONFIG_VOULU);
        if (e == ESP_OK) {
            e = ecrire_reg16(id, VL_REG_ALS_GAIN, VL_GAIN_VOULU);
        }
        if (e == ESP_OK) {
            e = ecrire_reg16(id, VL_REG_ALS_INTEG_HI, 0x00);
        }
        if (e == ESP_OK) {
            e = ecrire_reg16(id, VL_REG_ALS_INTEG_LO, VL_INTEG_LO_VOULU);
        }
        break;
    default:
        return ESP_ERR_INVALID_ARG;
    }
    if (e == ESP_OK) {
        s_c[id].config_us = esp_timer_get_time();
        s_c[id].config_posee = true;
    }
    return e;
}

/*
 * 🔴 LA GARDE ANTI-FANTÔME DE RÉGIME (AC10), ET SA CADENCE EST DÉCLARÉE ICI.
 *
 * Mécanisme visé (§13.10) : VCC retiré, le composant reste alimenté PARASITEMENT
 * par les tirages du bus à travers ses diodes ESD — assez pour ACQUITTER, pas
 * assez pour TENIR SA CONFIGURATION. Troisième état : présent, bavard, 5/5,
 * valeurs fausses ET plausibles.
 *
 * ⚠️ CADENCE : **UNE LECTURE PAR CYCLE (5 s), ⛔ AUCUNE ÉCRITURE EN RÉGIME.**
 *   C'est délibéré et c'est la contrainte d'AC10 : le seul témoin qu'on avait
 *   hérité était une ÉCRITURE (`D7A4` en 05h), et écrire un registre toutes les
 *   5 s ajouterait un AGRESSEUR PERMANENT sur un bus que le GT911 pole ~30×/s et
 *   qui se dégrade à froid — alors que l'entrée de ledger `:1363` a été fermée
 *   sur l'hypothèse de LECTURES. ⇒ on écrit UNE FOIS à la configuration, et on
 *   RELIT à chaque cycle. Le pouvoir discriminant est identique (un fantôme ne
 *   tient pas la valeur), le coût sur le bus est celui d'une lecture.
 *
 * ⚠️ La réparation est une RE-CONFIGURATION, comptée en `conformite` (les
 *   DÉTECTIONS, pas les réparations réussies — patron `reconfigs` du BME680).
 *
 * 🔴 BH1750 : rend toujours `true`. Il n'a AUCUN registre relisible — son seul
 *   registre écrivable est le MTreg, et il est NON RELISIBLE. L'absence de
 *   témoin est DÉCLARÉE, ⛔ pas passée sous silence : `env` l'imprime.
 */
/*
 * 🔴 TRI-ÉTAT, ⛔ PAS UN BOOLÉEN — CORRIGÉ EN REVUE DE CODE LE 2026-08-20.
 *
 * Cette fonction rendait `false` AUSSI BIEN quand le registre portait la
 * mauvaise valeur QUE quand la transaction I²C avait échoué. `cycle_un()` ne
 * pouvait donc pas distinguer les deux, et **un seul NACK produisait** :
 *   · `err_i2c++` ET `conformite++`  -> deux seaux pour UN événement ;
 *   · un ESP_LOGW de 4 lignes affirmant « le composant a redemarre sous nos
 *     pieds (alimentation parasite par les diodes ESD) » -> une CAUSE affirmée
 *     sans la moindre preuve ;
 *   · 2 (INA219) à 4 (VL6180X) ÉCRITURES de registre — au moment précis où le
 *     bus se dégrade, et en contradiction directe avec le contrat déclaré vingt
 *     lignes plus haut, avec le texte imprimé par `env`, et avec le README.
 * ⚠️ Ce n'était pas théorique : la campagne de `dn4-3` a compté « 4 err_i2c +
 *   5 pertes de configuration » sur le VL6180X à froid — donc jusqu'à CINQ
 *   séquences d'écriture réellement jouées sur un bus dégradé.
 * ⇒ Désormais : seule une VALEUR NON CONFORME conclut à un fantôme. Un défaut de
 *   transport se compte en `err_i2c`, ne conclut RIEN, et n'écrit RIEN.
 */
typedef enum {
    CONF_OK,        /* la configuration est là, relue et conforme */
    CONF_PERDUE,    /* le composant répond, et il a perdu ses registres */
    CONF_TRANSPORT, /* on n'a pas pu lui parler — ⛔ AUCUNE conclusion */
} conf_t;

static conf_t conformite_verifier(dn_env_id_t id)
{
    uint8_t b[2];
    switch (id) {
    case DN_ENV_LUM:
        /* Aucun témoin possible — DÉCLARÉ, voir `env`. Le seul registre
         * écrivable du BH1750 est le MTreg, et il est NON RELISIBLE. */
        return CONF_OK;

    case DN_ENV_ALIM:
        /* ⚠️ BRANCHE ACTUELLEMENT INATTEIGNABLE, et c'est DÉCLARÉ : `cycle_un()`
         * n'est plus appelée pour DN_ENV_ALIM depuis le correct-course du
         * 2026-08-20. Elle est CONSERVÉE parce qu'elle est le pendant exact de
         * `configurer()`, qui tourne toujours au boot — les retirer séparément
         * ferait diverger les deux. ⛔ Deadness déclarée, pas silencieuse. */
        if (lire_reg8(id, INA219_REG_CALIB, b, 2) != ESP_OK) {
            compter_i2c(id);
            return CONF_TRANSPORT;
        }
        return (((uint16_t)(b[0] << 8 | b[1])) == INA219_CALIB_VOULU)
                   ? CONF_OK
                   : CONF_PERDUE;

    case DN_ENV_TOF: {
        if (lire_reg16(id, VL_REG_ALS_GAIN, b, 1) != ESP_OK) {
            compter_i2c(id);
            return CONF_TRANSPORT;
        }
        if (b[0] != VL_GAIN_VOULU) {
            return CONF_PERDUE;
        }
        if (lire_reg16(id, VL_REG_ALS_INTEG_LO, b, 1) != ESP_OK) {
            compter_i2c(id);
            return CONF_TRANSPORT;
        }
        return (b[0] == VL_INTEG_LO_VOULU) ? CONF_OK : CONF_PERDUE;
    }
    default:
        return CONF_TRANSPORT;
    }
}

/* ── Lecture, capteur par capteur ─────────────────────────────────────────── */

static void lire_bh1750(void)
{
    const dn_env_id_t id = DN_ENV_LUM;
    uint8_t b[2];
    if (lire_nu(id, b, 2) != ESP_OK) {
        compter_i2c(id);
        return;
    }
    uint16_t brut = (uint16_t)(b[0] << 8 | b[1]);

    /* ⚠️ LE PIÈGE DE CADENCE, ET IL S'EST DÉJÀ DÉCLENCHÉ EN DIRECT : juste après
     * l'opcode de mode, la première lecture rend 00 00 parce que la conversion
     * n'est pas finie (120 ms typiques, 180 au pire). ⛔ Ce n'est PAS un capteur
     * mort, et c'est le seul cas où `err_donnee` a un sens ici : il répond, la
     * conversion n'est pas prête. Hors de cette fenêtre, 0 est une valeur
     * LÉGITIME (obscurité) et se publie telle quelle. */
    if (brut == 0 &&
        (esp_timer_get_time() - s_c[id].config_us) < BH1750_CONV_MAX_US) {
        compter_donnee(id);
        return;
    }

    if (brut == BH1750_BRUT_SATURE) {
        /* Le convertisseur est au plafond : « au moins 54 612 lx ». Ce n'est
         * plus une mesure, et la publier comme telle mentirait. */
        compter_bornes(id);
        return;
    }

    /* 🔴 lux = brut / 1,2 au MTreg par défaut (69), dixième TRONQUÉ.
     * ⛔ NE JAMAIS republier la variante « dixièmes » : `(brut * 10) / 12` EST
     *   déjà la valeur en LUX ENTIERS. L'avoir imprimée comme des dixièmes a
     *   publié « 4 614,8 » pour 46 148, TROIS FOIS, parce que le chiffre était
     *   PLAUSIBLE (`8e009f6`). */
    int lux = (int)(((uint32_t)brut * 10u) / 12u);

    portENTER_CRITICAL(&s_mux);
    s_lux = lux;
    s_lux_brut = (int)brut;
    portEXIT_CRITICAL(&s_mux);
    marquer_valide(id);

    /* 🔴 W2 — ÉCHANTILLONNÉ ICI, DEPUIS UNE LECTURE FRAÎCHE, ⛔ PLUS DEPUIS
     * `dn_env_cycle()` — CORRIGÉ EN REVUE DE CODE LE 2026-08-20.
     * L'ancienne garde était `dn_env_etat(DN_ENV_LUM) == DN_ENV_VIVANT`, qui
     * veut dire « pas encore périmé » (15 s = 3 cycles), ⛔ PAS « lu ce
     * cycle-ci ». Une panne d'un ou deux cycles poussait donc la MÊME valeur
     * deux fois de plus, comptées comme des NON-CHANGEMENTS : `n` gonflait et le
     * taux baissait. Les quatre autres pistes (pression ×2, température, gaz)
     * ne sont alimentées que depuis une lecture fraîche — et `dn_env.h` pose que
     * « comparer le lux et la pression avec deux instruments différents ne
     * prouverait rien ». ⇒ même instrument pour tout le monde, désormais. */
    dn_w2_echantillon(DN_W2_LUX, lux);
}

/*
 * 🔴 L'INA219 NE SE LIT PLUS EN RÉGIME — correct-course du 2026-08-20.
 *
 * `lire_ina219()` a été RETIRÉE ici, et ce n'est pas un nettoyage : c'est une
 * décision owner, motivée par la mesure.
 *   · `Vin+`/`Vin−` ne sont PAS câblés (`dn4-2` a tranché « bus seulement »),
 *     donc le shunt R100 n'est traversé par AUCUN courant. La puce mesurait donc
 *     du BRUIT sur une entrée flottante : `bus 904 mV · shunt −30 µV ·
 *     −0,3 mA · 0 mW`, relevé sur `1b2adca`. `dn4-3` a confirmé X3 = NON par A/B.
 *   · Elle coûtait pour ça **5 transactions I²C sur les 9 du cycle (56 %)** —
 *     1 conformité + BUS/SHUNT/CURRENT/POWER — sur le bus que §11.4 nomme
 *     « le PREMIER AGRESSEUR CONNU » de la famine DMA, et qui se dégrade à froid.
 *
 * ⛔ CE QUI N'A PAS ÉTÉ FAIT, ET POURQUOI : le composant n'est PAS dessoudé
 *   (D9 — montage fini, le dessoudage est un risque sur le bus pour ZÉRO gain),
 *   et son `id` n'a PAS été retiré de `dn_env_id_t`. Il reste OUVERT et
 *   CONFIGURÉ au boot, et `env` le montre comme INERTE en disant pourquoi.
 *   ⚠️ Un composant soudé qui DISPARAÎT de la console est un composant qu'on
 *   redécouvrira au prochain scan en se demandant ce que c'est.
 *
 * ✅ POUR LE REMETTRE EN SERVICE : il faut d'abord que du courant traverse son
 *   shunt — le bornier à vis 2 points est DÉJÀ SOUDÉ, donc `Vin+`/`Vin−` sont
 *   accessibles SANS FER. ⚠️ Vérifier d'abord AU MULTIMÈTRE que le bornier est
 *   bien relié à `Vin+`/`Vin−` : c'est le câblage standard CJMCU, mais ce dépôt
 *   ne l'a JAMAIS mesuré. ⛔ Et `Vin+`/`Vin−` NE SONT PAS une alimentation : y
 *   poser 5 V et la masse court-circuiterait le shunt de 0,1 Ω.
 */

/* 🔴 Le VL6180X ne publie AUCUNE grandeur : son ALS rend une réponse binaire
 * sans le chargement de registres privés de ST (§13.19.5). Ce qu'on lit ici est
 * son IDENTITÉ — la seule chose qui le qualifie vraiment — et c'est ce qui rend
 * son état VIVANT ou MUET. ⚠️ Un module qui compterait des lectures sans rien
 * en tirer serait un instrument décoratif ; celui-ci répond à une question
 * précise : « le capteur est-il toujours là, et est-il toujours lui ? ». */
static void lire_vl6180x(void)
{
    const dn_env_id_t id = DN_ENV_TOF;
    uint8_t b[1];
    if (lire_reg16(id, VL_REG_MODEL_ID, b, 1) != ESP_OK) {
        compter_i2c(id);
        return;
    }
    if (b[0] != VL_MODEL_ID_ATTENDU) {
        /* Il répond, mais ce n'est pas lui : ni un défaut de transport, ni une
         * valeur hors bornes. C'est exactement `err_donnee`. */
        compter_donnee(id);
        return;
    }
    marquer_valide(id);
}

/* ── Le cycle ─────────────────────────────────────────────────────────────── */

/*
 * 🔴 LA LISTE DES CAPTEURS RÉELLEMENT CADENCÉS — UN SEUL ENDROIT.
 * `dn_env_cycle()` et `dn_env_init()` doivent s'accorder : un capteur qu'on
 * n'appelle pas dans le cycle ne doit pas non plus être ouvert ni configuré au
 * boot, sinon le bandeau promet une reprise que rien ne viendra faire.
 * ⛔ Ne pas dupliquer ce test : le faire diverger est précisément ce qui a
 *   produit une étiquette menteuse le 2026-08-21.
 */
static bool cadence(dn_env_id_t id)
{
    /* DN_ENV_ALIM (INA219) : sorti du régime au correct-course du 2026-08-20,
     * puis RETIRÉ PHYSIQUEMENT du bus par l'owner le 2026-08-21.
     * ✅ Côté `dn_env_cycle()`, la garantie est encore plus forte : la fonction
     *   `lire_ina219()` a été SUPPRIMÉE, donc le cadencer ne COMPILERAIT PAS.
     *   Ce prédicat existe pour `dn_env_init()`, qui n'a pas cette protection. */
    return id != DN_ENV_ALIM;
}

static void cycle_un(dn_env_id_t id, void (*lire)(void))
{
    /* Backoff : device jamais ouvert, ou ouverture perdue. Une tentative par
     * minute — ⛔ pas à chaque cycle : le bus est déjà chargé. */
    if (!s_c[id].dev) {
        if (--s_c[id].cycles_avant_reinit > 0) {
            return;
        }
        s_c[id].cycles_avant_reinit = DN_ENV_REINIT_CYCLES;
        if (ouvrir(id) != ESP_OK) {
            return;
        }
        if (configurer(id) != ESP_OK) {
            compter_i2c(id);
            return;
        }
        ESP_LOGI(TAG, "%s @ 0x%02X : device (re)ouvert et configure",
                 k_nom[id], k_addr[id]);
        /* ⛔ On ne lit PAS dans le cycle qui vient de configurer : le BH1750
         * n'a pas fini sa première conversion, et l'INA219 non plus. La lecture
         * a lieu au cycle suivant, dans 5 s. C'est déclaré, pas subi. */
        return;
    }

    /*
     * 🔴 UNE CONFIGURATION QUI A ÉCHOUÉ DOIT ÊTRE REPOSÉE — AJOUTÉ EN REVUE DE
     *   CODE LE 2026-08-20, ET C'EST LE DÉFAUT LE PLUS GRAVE QU'ELLE AIT TROUVÉ.
     *
     * `dn_env_init()` journalisait « configuration refusee au boot — ATTENDU a
     * froid, LA GARDE DE CONFORMITE LA REPOSERA ». **Elle ne la reposait pas**,
     * et pour le BH1750 elle ne le POUVAIT pas :
     *   · `conformite_verifier(DN_ENV_LUM)` rend `CONF_OK` en dur (aucun
     *     registre relisible) -> la branche de réparation ci-dessous lui est
     *     structurellement inatteignable ;
     *   · `s_c[id].dev` n'est JAMAIS remis à NULL -> la branche de ré-ouverture
     *     ci-dessus lui est inatteignable aussi.
     * ⇒ un BH1750 resté en power-down ACQUITTE et rend `00 00`. Et comme
     *   `config_us` restait à 0, la garde des 180 ms ne pouvait plus tirer : le
     *   zéro tombait dans le chemin normal et se publiait comme `0 lx` VIVANT,
     *   à vie, sans qu'AUCUN compteur ne bouge — avec `bl auto on` clouant la
     *   dalle au plancher en pleine lumière.
     * ⚠️ Même état d'arrivée par un `i2c ecrire 23 00` tapé à la console.
     */
    if (!s_c[id].config_posee) {
        if (--s_c[id].cycles_avant_reinit > 0) {
            return;
        }
        s_c[id].cycles_avant_reinit = DN_ENV_REINIT_CYCLES;
        if (configurer(id) != ESP_OK) {
            compter_i2c(id);
            return;
        }
        ESP_LOGI(TAG, "%s @ 0x%02X : configuration REPOSEE (elle avait echoue)",
                 k_nom[id], k_addr[id]);
        /* ⛔ Toujours pas de lecture dans le cycle qui vient de configurer. */
        return;
    }

    /* La garde anti-fantôme passe AVANT la valeur : croire une valeur d'un
     * capteur dont on n'a pas vérifié la configuration, c'est exactement le
     * troisième état de §13.10 — plausible et faux. */
    conf_t conf = conformite_verifier(id);
    if (conf == CONF_TRANSPORT) {
        /* ⛔ ON NE CONCLUT RIEN. `err_i2c` est déjà compté par la primitive ;
         * affirmer ici une perte de configuration serait affirmer une CAUSE
         * (l'alimentation parasite par les diodes ESD) sur la foi d'un simple
         * NACK — et déclencher des écritures sur un bus déjà en train de se
         * dégrader. Le capteur sera re-sondé au cycle suivant. */
        return;
    }
    if (conf == CONF_PERDUE) {
        portENTER_CRITICAL(&s_mux);
        s_c[id].cnt.conformite++;
        portEXIT_CRITICAL(&s_mux);
        s_c[id].degrade = true;
        ESP_LOGW(TAG,
                 "%s @ 0x%02X : CONFIGURATION PERDUE — le composant REPOND mais "
                 "ses registres ne portent plus ce qu'on y a ecrit. Le cycle est "
                 "declare invalide et la configuration est reposee. Cause "
                 "connue : le composant a redemarre sous nos pieds (alimentation "
                 "parasite par les diodes ESD, §13.10).",
                 k_nom[id], k_addr[id]);
        if (configurer(id) != ESP_OK) {
            compter_i2c(id);
        }
        return;
    }

    lire();
}

void dn_env_cycle(void)
{
    if (!s_init_faite) {
        return;
    }
    int64_t t0 = esp_timer_get_time();

    cycle_un(DN_ENV_LUM, lire_bh1750);
    /* ⛔ DN_ENV_ALIM (INA219) n'est PAS cadencé, et la garantie est plus forte
     * qu'un test : `lire_ina219()` N'EXISTE PLUS. Le cadencer ne compilerait
     * pas. `cadence()` porte la même liste pour `dn_env_init()`, qui n'a pas
     * cette protection-là. */
    cycle_un(DN_ENV_TOF, lire_vl6180x);

    int64_t duree = esp_timer_get_time() - t0;
    portENTER_CRITICAL(&s_mux);
    s_cycles++;
    s_duree_cycle_us = duree;
    portEXIT_CRITICAL(&s_mux);

    /* ⛔ L'ÉCHANTILLONNAGE W2 DU LUX A ÉTÉ DÉPLACÉ DANS `lire_bh1750()`, dans le
     * chemin de succès — revue de code du 2026-08-20. Il vivait ici, gardé par
     * `dn_env_etat(...) == DN_ENV_VIVANT`, ce qui veut dire « pas encore
     * périmé », ⛔ PAS « lu ce cycle-ci » : une valeur périmée était rejouée
     * jusqu'à deux fois de plus et comptée comme un NON-CHANGEMENT. */

    /* Le rétroéclairage est asservi APRÈS les lectures, dans le même cycle :
     * ⛔ pas de tâche de plus, ⛔ pas de `vTaskDelay`. */
    if (s_bl_auto) {
        int lux;
        dn_env_etat_t e = dn_env_etat(DN_ENV_LUM);
        portENTER_CRITICAL(&s_mux);
        lux = s_lux;
        portEXIT_CRITICAL(&s_mux);

        if (e != DN_ENV_VIVANT || lux == DN_ENV_ABSENT) {
            /* ⛔ Capteur muet : LE DUTY NE BOUGE PAS. Journalisé UNE fois. */
            if (!s_bl_muet_dit) {
                s_bl_muet_dit = true;
                ESP_LOGW(TAG, "retroeclairage auto : capteur MUET — le duty est "
                              "GELE au dernier applique. Il ne repartira qu'a la "
                              "reprise du BH1750.");
            }
        } else {
            s_bl_muet_dit = false;
            int cible = dn_env_bl_loi(lux);
            /* 🔴 `dn_display_backlight_pct_state()` rend `-1` quand LEDC n'est
             * pas encore monté : c'est un ÉTAT, ⛔ pas un pourcentage. Le repli
             * était appliqué SANS être re-testé, et `cible = courant + pas`
             * pouvait donc se calculer contre une NON-VALEUR (revue de code du
             * 2026-08-20). */
            int courant = s_bl_dernier_pct;
            if (courant < 0) {
                courant = dn_display_backlight_pct_state();
            }
            if (courant < 0) {
                /* LEDC pas encore monté : la discipline de boot dit que le duty
                 * ne monte qu'après la première trame. On ne calcule rien. */
                s_bl_dernier_lux = lux;
                return;
            }
            int ecart = cible - courant;
            if (ecart <= -DN_ENV_BL_HYST || ecart >= DN_ENV_BL_HYST) {
                if (ecart > s_bl_pas) {
                    cible = courant + s_bl_pas;
                } else if (ecart < -s_bl_pas) {
                    cible = courant - s_bl_pas;
                }
                /* ✅ L'ombre logicielle de dn_display est HONNÊTE : elle n'est
                 * écrite qu'APRÈS confirmation. On ne mémorise donc notre
                 * « dernier applique » que si l'appel a réussi — sinon on
                 * annoncerait une luminosité que la dalle n'a pas prise. */
                if (dn_display_backlight_pct(cible) == ESP_OK) {
                    s_bl_dernier_pct = cible;
                }
            }
            s_bl_dernier_lux = lux;
        }
    }
}

/* ── Init ─────────────────────────────────────────────────────────────────── */

esp_err_t dn_env_init(void)
{
    for (int i = 0; i < DN_ENV_NB; i++) {
        s_c[i].dev = NULL;
        s_c[i].derniere_us = -1;
        s_c[i].degrade = false;
        s_c[i].a_deja_lu = false;
        s_c[i].cycles_avant_reinit = DN_ENV_REINIT_CYCLES;
        s_c[i].config_us = 0;
        s_c[i].config_posee = false;
        memset(&s_c[i].cnt, 0, sizeof s_c[i].cnt);
    }

    i2c_master_bus_handle_t bus = dn_display_i2c_bus();
    if (!bus) {
        /* ⚠️ NON FATAL, et ce n'est pas un détail : ce module est OPTIONNEL, et
         * avec CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y un abort donnerait « ni
         * console ni flash, RESET physique obligatoire ». */
        ESP_LOGE(TAG, "bus I2C indisponible — dn_env reste DESARME. "
                      "`dn_display_init()` a-t-elle tourne ?");
        return ESP_ERR_INVALID_STATE;
    }

    int ouverts = 0;
    for (int i = 0; i < DN_ENV_NB; i++) {
        /* 🔴 UN CAPTEUR NON CADENCÉ NE S'OUVRE PAS, ET NE SE CONFIGURE PAS.
         *
         * Ajouté le 2026-08-21, après le RETRAIT PHYSIQUE de l'INA219 (owner).
         * Sans ce test, l'init tentait d'ouvrir puis de configurer un composant
         * qui n'est plus sur le bus : `configurer()` échouait, `compter_i2c()`
         * posait un `err_i2c 1` définitif — et surtout le bandeau promettait
         * « elle sera REPOSEE par `cycle_un()` dans 60 s ».
         * ⛔ CETTE PROMESSE ÉTAIT FAUSSE : `cycle_un()` n'est plus appelée pour
         *   DN_ENV_ALIM depuis le correct-course. RIEN ne l'aurait reposée.
         * ⚠️ C'est EXACTEMENT le défaut corrigé sur le BH1750 en revue de code
         *   le 2026-08-20 (« la garde de conformité la reposera » — elle ne le
         *   pouvait pas), réintroduit par un AUTRE chemin quelques heures plus
         *   tard. Un log qui promet une reprise doit être gardé par ce qui la
         *   rend possible, pas par l'intention. */
        if (!cadence((dn_env_id_t)i)) {
            ESP_LOGI(TAG, "%s @ 0x%02X : NON CADENCE — ni ouvert ni configure. "
                          "Voir `env` pour le motif.",
                     k_nom[i], k_addr[i]);
            continue;
        }
        if (ouvrir((dn_env_id_t)i) != ESP_OK) {
            ESP_LOGW(TAG, "%s @ 0x%02X : ouverture refusee au boot — nouvelle "
                          "tentative dans %d s",
                     k_nom[i], k_addr[i],
                     (DN_ENV_REINIT_CYCLES * DN_ENV_PERIODE_MS) / 1000);
            continue;
        }
        if (configurer((dn_env_id_t)i) != ESP_OK) {
            /* ⚠️ ÉCHEC ATTENDU au démarrage à FROID : le bus entier se dégrade
             * ~40 s (55,5 % d'erreurs mesurées sur le GT911) et se rétablit
             * SEUL. Le device reste ouvert, la configuration sera reposée par
             * la garde de conformité dès que le bus redevient sain. */
            ESP_LOGW(TAG, "%s @ 0x%02X : configuration refusee au boot — ATTENDU "
                          "a froid, elle sera REPOSEE par `cycle_un()` dans %d s",
                     k_nom[i], k_addr[i],
                     (DN_ENV_REINIT_CYCLES * DN_ENV_PERIODE_MS) / 1000);
            compter_i2c((dn_env_id_t)i);
        }
        ouverts++;
    }

    s_init_faite = true;
    ESP_LOGI(TAG,
             "dn_env pret — %d/%d devices ouverts, cadence %d ms (portee par la "
             "tache dn_capt), peremption %lld ms, timeout I2C %d ms",
             ouverts, DN_ENV_NB, DN_ENV_PERIODE_MS,
             (long long)(DN_ENV_PEREMPTION_US / 1000), DN_ENV_I2C_TIMEOUT_MS);
    ESP_LOGI(TAG,
             "  retroeclairage auto : %s par defaut — la loi est %d%% a %d lx, "
             "%d%% a %d lx, bande morte %d pts, pas max %d pts/cycle. "
             "`bl auto on` pour l'armer.",
             DN_ENV_BL_AUTO_DEFAUT ? "ARME" : "DESARME",
             s_bl_pct_min, DN_ENV_BL_LUX_BAS,
             DN_ENV_BL_PCT_MAX, DN_ENV_BL_LUX_HAUT,
             DN_ENV_BL_HYST, DN_ENV_BL_PAS_MAX);
    return ESP_OK;
}

/* ── Accesseurs ───────────────────────────────────────────────────────────── */

#define LIRE_ATOMIQUE(champ)                 \
    do {                                     \
        int v;                               \
        portENTER_CRITICAL(&s_mux);          \
        v = (champ);                         \
        portEXIT_CRITICAL(&s_mux);           \
        return v;                            \
    } while (0)

int dn_env_lux(void) { LIRE_ATOMIQUE(s_lux); }
int dn_env_lux_brut(void) { LIRE_ATOMIQUE(s_lux_brut); }
/* ⛔ Les quatre accesseurs de l'INA219 ont été RETIRÉS — correct-course du
 * 2026-08-20 : ils ne pouvaient rendre que du bruit sur une entrée flottante.
 * Voir le bloc de motifs au-dessus de `lire_vl6180x()`. */

/* 🔴 LECTURE GROUPÉE — AJOUTÉE EN REVUE DE CODE LE 2026-08-20.
 * Le cycle publie `s_lux` et `s_lux_brut` sous UN SEUL verrou ; les lire une par
 * une prenait deux sections critiques et pouvait imprimer un tuple qui n'a
 * jamais existé — « 411 lx (brut 500) ». C'est le défaut « CR dn4-2 — LECTURE
 * ATOMIQUE », réintroduit pour ce module.
 * ⛔ La variante INA219 a été retirée avec ses grandeurs (correct-course
 *   2026-08-20). */
void dn_env_lux_lire(int *lux, int *brut)
{
    portENTER_CRITICAL(&s_mux);
    if (lux)  { *lux = s_lux; }
    if (brut) { *brut = s_lux_brut; }
    portEXIT_CRITICAL(&s_mux);
}


dn_env_etat_t dn_env_etat(dn_env_id_t id)
{
    if (id < 0 || id >= DN_ENV_NB) {
        return DN_ENV_JAMAIS;
    }
    int64_t derniere;
    portENTER_CRITICAL(&s_mux);
    derniere = s_c[id].derniere_us;
    portEXIT_CRITICAL(&s_mux);
    if (derniere < 0) {
        return DN_ENV_JAMAIS;
    }
    return (esp_timer_get_time() - derniere) <= DN_ENV_PEREMPTION_US
               ? DN_ENV_VIVANT
               : DN_ENV_MUET;
}

const char *dn_env_etat_nom(dn_env_etat_t e)
{
    switch (e) {
    case DN_ENV_JAMAIS: return "JAMAIS";
    case DN_ENV_VIVANT: return "VIVANT";
    case DN_ENV_MUET:   return "MUET";
    default:            return "?";
    }
}

const char *dn_env_nom(dn_env_id_t id)
{
    return (id >= 0 && id < DN_ENV_NB) ? k_nom[id] : "?";
}

uint8_t dn_env_adresse(dn_env_id_t id)
{
    return (id >= 0 && id < DN_ENV_NB) ? k_addr[id] : 0;
}

bool dn_env_present(dn_env_id_t id)
{
    return (id >= 0 && id < DN_ENV_NB) && s_c[id].dev != NULL;
}

int64_t dn_env_age_us(dn_env_id_t id)
{
    if (id < 0 || id >= DN_ENV_NB) {
        return -1;
    }
    int64_t derniere;
    portENTER_CRITICAL(&s_mux);
    derniere = s_c[id].derniere_us;
    portEXIT_CRITICAL(&s_mux);
    return (derniere < 0) ? -1 : (esp_timer_get_time() - derniere);
}

int64_t dn_env_duree_cycle_us(void)
{
    int64_t v;
    portENTER_CRITICAL(&s_mux);
    v = s_duree_cycle_us;
    portEXIT_CRITICAL(&s_mux);
    return v;
}

uint32_t dn_env_cycles(void)
{
    uint32_t v;
    portENTER_CRITICAL(&s_mux);
    v = s_cycles;
    portEXIT_CRITICAL(&s_mux);
    return v;
}

void dn_env_compteurs(dn_env_id_t id, dn_env_compteurs_t *out)
{
    if (!out) {
        return;
    }
    if (id < 0 || id >= DN_ENV_NB) {
        memset(out, 0, sizeof *out);
        return;
    }
    portENTER_CRITICAL(&s_mux);
    *out = s_c[id].cnt;
    portEXIT_CRITICAL(&s_mux);
}

void dn_env_compteurs_reset(void)
{
    portENTER_CRITICAL(&s_mux);
    for (int i = 0; i < DN_ENV_NB; i++) {
        memset(&s_c[i].cnt, 0, sizeof s_c[i].cnt);
        /* 🔴 `degrade` TOMBE AVEC LES COMPTEURS — corrigé en revue de code le
         * 2026-08-20. Le laisser armé faisait compter `reprises = 1` sur un
         * compteur fraîchement remis à zéro, à la première lecture valide :
         * une reprise d'AVANT le reset attribuée à la fenêtre d'APRÈS, alors
         * que la commande annonce « compteurs remis a zero ». */
        s_c[i].degrade = false;
    }
    portEXIT_CRITICAL(&s_mux);
}

/* ── La loi du rétroéclairage ─────────────────────────────────────────────── */

int dn_env_bl_loi(int lux)
{
    if (lux == DN_ENV_ABSENT) {
        return s_bl_pct_min;
    }
    if (lux <= s_bl_lux_bas) {
        return s_bl_pct_min;
    }
    if (lux >= s_bl_lux_haut) {
        return DN_ENV_BL_PCT_MAX;
    }
    /* Interpolation linéaire, en entiers, arrondie — comme le duty LEDC de
     * dn_display (`(pct * 1023 + 50) / 100`), pour la même raison : AC7 de
     * dn1-3 cherchait le PLANCHER lisible, et une troncature l'aurait raté. */
    int span_lux = s_bl_lux_haut - s_bl_lux_bas;
    int span_pct = DN_ENV_BL_PCT_MAX - s_bl_pct_min;
    return s_bl_pct_min +
           (((lux - s_bl_lux_bas) * span_pct) + span_lux / 2) / span_lux;
}

esp_err_t dn_env_bl_plancher_set(int pct)
{
    /* ⛔ Ce dépôt REFUSE, il n'écrête pas. La borne haute est DN_ENV_BL_PCT_MAX
     * moins la bande morte : un plancher au ras du plafond rendrait la loi
     * inerte SANS le dire, ce qui est pire qu'un refus. */
    if (pct < 0 || pct > DN_ENV_BL_PCT_MAX - DN_ENV_BL_HYST) {
        return ESP_ERR_INVALID_ARG;
    }
    s_bl_pct_min = pct;
    return ESP_OK;
}

int dn_env_bl_plancher(void) { return s_bl_pct_min; }

bool dn_env_bl_auto(void) { return s_bl_auto; }

void dn_env_bl_auto_set(bool on)
{
    s_bl_auto = on;
    if (on) {
        /* 🔴 CORRIGÉ EN REVUE DE CODE LE 2026-08-20 : cette fonction posait
         * `s_bl_dernier_pct = dn_display_backlight_pct_state()`, ce qui ÉCRASAIT
         * la sentinelle « la loi n'a encore RIEN appliqué ». `bl` prenait alors
         * `dpct >= 0` pour « la loi a appliqué ça » et imprimait
         * « applique : 100 % (sur 0 lx) » juste après un `bl auto on` — un duty
         * que la loi n'avait jamais calculé, sur un lux jamais lu.
         * ⛔ La sentinelle RESTE. La boucle repart de l'état RÉEL de la dalle
         *   toute seule, par le repli de `dn_env_cycle()` : c'est le même effet,
         *   sans le mensonge. */
        s_bl_dernier_pct = -1;
        s_bl_dernier_lux = DN_ENV_ABSENT;
        s_bl_muet_dit = false;
    }
}

bool dn_env_bl_auto_desarmer(const char *par_qui)
{
    if (!s_bl_auto) {
        return false;
    }
    s_bl_auto = false;
    ESP_LOGW(TAG, "retroeclairage auto DESARME par « %s » — deux ecrivains sur "
                  "LEDC ne s'arbitrent pas tout seuls, et une commande ecrasee "
                  "au cycle suivant serait un instrument qui ment.",
             par_qui ? par_qui : "?");
    return true;
}

esp_err_t dn_env_bl_bornes_set(int lux_bas, int lux_haut)
{
    /* ⛔ Le dépôt REFUSE, il n'écrête pas — et il explique. */
    if (lux_bas < 0 || lux_haut <= lux_bas) {
        return ESP_ERR_INVALID_ARG;
    }
    /* 🔴 54 611, ⛔ PAS 54 612 — corrigé en revue de code le 2026-08-20. Le brut
     * `0xFFFF` est REJETÉ comme saturation du convertisseur, donc le plus grand
     * brut publiable est `0xFFFE`, soit `lux = (65534 × 10) / 12 = 54 611`.
     * Accepter 54 612 rendait la branche `lux >= s_bl_lux_haut` INATTEIGNABLE :
     * la loi ne pouvait alors jamais saturer à 100 %, silencieusement — et ce
     * dépôt REFUSE, il n'écrête pas et il n'accepte pas une borne inerte. */
    if (lux_haut > 54611) {
        return ESP_ERR_INVALID_ARG;
    }
    s_bl_lux_bas = lux_bas;
    s_bl_lux_haut = lux_haut;
    return ESP_OK;
}

esp_err_t dn_env_bl_pas_set(int pas)
{
    /*
     * 🔴 LE PAS NE PEUT PAS ÊTRE PLUS PETIT QUE LA BANDE MORTE — corrigé en
     *   revue de code le 2026-08-20, et c'est un VERROU MORTEL qu'il retire.
     *
     * Avec `pas < DN_ENV_BL_HYST`, la boucle peut ENTRER (|écart| ≥ HYST) mais
     * ne bouger que de `pas` points, ce qui laisse |écart| < HYST : elle se
     * fige à mi-chemin, DANS LES DEUX SENS, pour TOUS les lux.
     * Exemple mesuré au papier : `bl auto plancher 97` + `bl auto pas 1`, depuis
     * 100 % — écart −3 ⇒ on entre, le limiteur ramène le mouvement à 1 ⇒ 99 %.
     * Cycle suivant : écart −2 < 3 ⇒ GELÉ. En pleine lumière, écart +1 ⇒ GELÉ.
     * Le duty se gare à 99 et ne bouge plus jamais, pendant que `bl auto`
     * annonce une « course complète » qui ne peut pas s'achever.
     * ⛔ Les deux setters validaient chacun dans son coin et ne se croisaient
     *   jamais — c'est exactement l'inertie silencieuse que
     *   `dn_env_bl_plancher_set()` refuse dix lignes plus bas.
     */
    if (pas < DN_ENV_BL_HYST || pas > 100) {
        return ESP_ERR_INVALID_ARG;
    }
    s_bl_pas = pas;
    return ESP_OK;
}

void dn_env_bl_etat(int *lux_bas, int *lux_haut, int *pas, int *hyst,
                    int *dernier_pct, int *dernier_lux)
{
    if (lux_bas)     { *lux_bas = s_bl_lux_bas; }
    if (lux_haut)    { *lux_haut = s_bl_lux_haut; }
    if (pas)         { *pas = s_bl_pas; }
    if (hyst)        { *hyst = DN_ENV_BL_HYST; }
    if (dernier_pct) { *dernier_pct = s_bl_dernier_pct; }
    if (dernier_lux) { *dernier_lux = s_bl_dernier_lux; }
}

/* ── W2 — l'accumulateur du critère « une case doit bouger » ──────────────── */

static dn_w2_t s_w2[DN_W2_NB];
static int32_t s_w2_prec[DN_W2_NB];
static bool s_w2_amorce[DN_W2_NB];

static const char *k_w2_nom[DN_W2_NB] = {
    "lux (entier)",
    "pression (hPa entier)",
    "pression (hPa dixieme)",
    "temperature (dixieme) [CONTROLE]",
    "gaz MOX (kOhm) [gaz on requis]",
};

const char *dn_w2_nom(dn_w2_id_t id)
{
    return (id >= 0 && id < DN_W2_NB) ? k_w2_nom[id] : "?";
}

void dn_w2_echantillon(dn_w2_id_t id, int32_t v)
{
    if (id < 0 || id >= DN_W2_NB) {
        return;
    }
    portENTER_CRITICAL(&s_mux);
    dn_w2_t *w = &s_w2[id];
    if (w->n == 0) {
        w->min = w->max = v;
    } else {
        if (v < w->min) { w->min = v; }
        if (v > w->max) { w->max = v; }
        /* 🔴 « taux de changement du TEXTE » : deux valeurs identiques rendent
         * le MÊME texte, donc ce n'est pas un changement. C'est bien la valeur
         * AFFICHÉE qu'on compare, ⛔ pas la source. */
        if (s_w2_amorce[id] && v != s_w2_prec[id]) {
            w->changements++;
        }
    }
    w->n++;
    w->somme += v;
    w->somme_carres += (int64_t)v * (int64_t)v;
    s_w2_prec[id] = v;
    s_w2_amorce[id] = true;
    portEXIT_CRITICAL(&s_mux);
}

void dn_w2_lire(dn_w2_id_t id, dn_w2_t *out)
{
    if (!out) {
        return;
    }
    if (id < 0 || id >= DN_W2_NB) {
        memset(out, 0, sizeof *out);
        return;
    }
    portENTER_CRITICAL(&s_mux);
    *out = s_w2[id];
    portEXIT_CRITICAL(&s_mux);
}

void dn_w2_reset(void)
{
    portENTER_CRITICAL(&s_mux);
    memset(s_w2, 0, sizeof s_w2);
    memset(s_w2_prec, 0, sizeof s_w2_prec);
    memset(s_w2_amorce, 0, sizeof s_w2_amorce);
    portEXIT_CRITICAL(&s_mux);
}

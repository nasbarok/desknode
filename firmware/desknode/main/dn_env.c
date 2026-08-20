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
#define INA219_REG_CONFIG    0x00 /* reset 0x399F, VÉRIFIÉ sur la carte */
#define INA219_REG_SHUNT     0x01 /* signé, LSB 10 µV */
#define INA219_REG_BUS       0x02 /* bits 15:3 = valeur, LSB 4 mV ; b1 CNVR ; b0 OVF */
#define INA219_REG_POWER     0x03
#define INA219_REG_CURRENT   0x04 /* signé */
#define INA219_REG_CALIB     0x05 /* reset 0x0000, VÉRIFIÉ sur la carte */
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
#define INA219_CURRENT_LSB_DIXIEME_MA 1 /* 0,1 mA -> courant_ma = brut / 10 */
#define INA219_POWER_LSB_MW  2

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
#define INA219_BUS_MAX_MV    32760
#define INA219_SHUNT_MAX_UV  320000

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
    int64_t config_us;     /* instant de la dernière (re)configuration */
} env_capteur_t;

static env_capteur_t s_c[DN_ENV_NB];

static int s_lux = DN_ENV_ABSENT;
static int s_lux_brut = DN_ENV_ABSENT;
static int s_bus_mv = DN_ENV_ABSENT;
static int s_shunt_uv = DN_ENV_ABSENT;
static int s_courant_ma = DN_ENV_ABSENT;
static int s_puissance_mw = DN_ENV_ABSENT;

static uint32_t s_cycles;
static int64_t s_duree_cycle_us;
static bool s_init_faite;

/* Rétroéclairage automatique */
static bool s_bl_auto = DN_ENV_BL_AUTO_DEFAUT;
static int s_bl_lux_bas = DN_ENV_BL_LUX_BAS;
static int s_bl_lux_haut = DN_ENV_BL_LUX_HAUT;
static int s_bl_pas = DN_ENV_BL_PAS_MAX;
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
static bool conformite_ok(dn_env_id_t id)
{
    uint8_t b[2];
    switch (id) {
    case DN_ENV_LUM:
        return true; /* aucun témoin possible — DÉCLARÉ, voir `env` */

    case DN_ENV_ALIM:
        if (lire_reg8(id, INA219_REG_CALIB, b, 2) != ESP_OK) {
            compter_i2c(id);
            return false;
        }
        return ((uint16_t)(b[0] << 8 | b[1])) == INA219_CALIB_VOULU;

    case DN_ENV_TOF: {
        if (lire_reg16(id, VL_REG_ALS_GAIN, b, 1) != ESP_OK) {
            compter_i2c(id);
            return false;
        }
        if (b[0] != VL_GAIN_VOULU) {
            return false;
        }
        if (lire_reg16(id, VL_REG_ALS_INTEG_LO, b, 1) != ESP_OK) {
            compter_i2c(id);
            return false;
        }
        return b[0] == VL_INTEG_LO_VOULU;
    }
    default:
        return false;
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
}

static void lire_ina219(void)
{
    const dn_env_id_t id = DN_ENV_ALIM;
    uint8_t b[2];

    if (lire_reg8(id, INA219_REG_BUS, b, 2) != ESP_OK) {
        compter_i2c(id);
        return;
    }
    uint16_t bus_raw = (uint16_t)(b[0] << 8 | b[1]);
    /* TI SBOS448G §8.6.2.3 : b1 = CNVR (conversion ready), b0 = OVF (math
     * overflow). ⇒ CNVR à 0 = « il répond, la donnée n'est pas prête ». */
    if ((bus_raw & 0x0002u) == 0) {
        compter_donnee(id);
        return;
    }
    if ((bus_raw & 0x0001u) != 0) {
        compter_bornes(id); /* OVF : le seul dépassement que la puce signale */
        return;
    }
    int bus_mv = (int)((bus_raw >> 3) * 4u);
    if (bus_mv < 0 || bus_mv > INA219_BUS_MAX_MV) {
        compter_bornes(id);
        return;
    }

    if (lire_reg8(id, INA219_REG_SHUNT, b, 2) != ESP_OK) {
        compter_i2c(id);
        return;
    }
    int shunt_uv = (int)(int16_t)(b[0] << 8 | b[1]) * 10;
    if (shunt_uv > INA219_SHUNT_MAX_UV || shunt_uv < -INA219_SHUNT_MAX_UV) {
        compter_bornes(id); /* écrêtage du PGA ÷8 (±320 mV) */
        return;
    }

    if (lire_reg8(id, INA219_REG_CURRENT, b, 2) != ESP_OK) {
        compter_i2c(id);
        return;
    }
    /* Current_LSB = 0,1 mA ⇒ mA = brut / 10, en gardant le SIGNE. */
    int courant_ma = (int)(int16_t)(b[0] << 8 | b[1]) / 10;

    if (lire_reg8(id, INA219_REG_POWER, b, 2) != ESP_OK) {
        compter_i2c(id);
        return;
    }
    int puissance_mw = (int)(uint16_t)(b[0] << 8 | b[1]) * INA219_POWER_LSB_MW;

    portENTER_CRITICAL(&s_mux);
    s_bus_mv = bus_mv;
    s_shunt_uv = shunt_uv;
    s_courant_ma = courant_ma;
    s_puissance_mw = puissance_mw;
    portEXIT_CRITICAL(&s_mux);
    marquer_valide(id);
}

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

    /* La garde anti-fantôme passe AVANT la valeur : croire une valeur d'un
     * capteur dont on n'a pas vérifié la configuration, c'est exactement le
     * troisième état de §13.10 — plausible et faux. */
    if (!conformite_ok(id)) {
        portENTER_CRITICAL(&s_mux);
        s_c[id].cnt.conformite++;
        portEXIT_CRITICAL(&s_mux);
        s_c[id].degrade = true;
        ESP_LOGW(TAG,
                 "%s @ 0x%02X : CONFIGURATION PERDUE — le cycle est declare "
                 "invalide et la configuration est reposee. Cause connue : le "
                 "composant a redemarre sous nos pieds (alimentation parasite "
                 "par les diodes ESD, §13.10).",
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
    cycle_un(DN_ENV_ALIM, lire_ina219);
    cycle_un(DN_ENV_TOF, lire_vl6180x);

    int64_t duree = esp_timer_get_time() - t0;
    portENTER_CRITICAL(&s_mux);
    s_cycles++;
    s_duree_cycle_us = duree;
    portEXIT_CRITICAL(&s_mux);

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
            int courant = (s_bl_dernier_pct >= 0) ? s_bl_dernier_pct
                                                  : dn_display_backlight_pct_state();
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
            ESP_LOGW(TAG, "%s @ 0x%02X : configuration refusee au boot — "
                          "ATTENDU a froid, la garde de conformite la reposera",
                     k_nom[i], k_addr[i]);
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
             DN_ENV_BL_PCT_MIN, DN_ENV_BL_LUX_BAS,
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
int dn_env_bus_mv(void) { LIRE_ATOMIQUE(s_bus_mv); }
int dn_env_shunt_uv(void) { LIRE_ATOMIQUE(s_shunt_uv); }
int dn_env_courant_ma(void) { LIRE_ATOMIQUE(s_courant_ma); }
int dn_env_puissance_mw(void) { LIRE_ATOMIQUE(s_puissance_mw); }

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
    }
    portEXIT_CRITICAL(&s_mux);
}

/* ── La loi du rétroéclairage ─────────────────────────────────────────────── */

int dn_env_bl_loi(int lux)
{
    if (lux == DN_ENV_ABSENT) {
        return DN_ENV_BL_PCT_MIN;
    }
    if (lux <= s_bl_lux_bas) {
        return DN_ENV_BL_PCT_MIN;
    }
    if (lux >= s_bl_lux_haut) {
        return DN_ENV_BL_PCT_MAX;
    }
    /* Interpolation linéaire, en entiers, arrondie — comme le duty LEDC de
     * dn_display (`(pct * 1023 + 50) / 100`), pour la même raison : AC7 de
     * dn1-3 cherchait le PLANCHER lisible, et une troncature l'aurait raté. */
    int span_lux = s_bl_lux_haut - s_bl_lux_bas;
    int span_pct = DN_ENV_BL_PCT_MAX - DN_ENV_BL_PCT_MIN;
    return DN_ENV_BL_PCT_MIN +
           (((lux - s_bl_lux_bas) * span_pct) + span_lux / 2) / span_lux;
}

bool dn_env_bl_auto(void) { return s_bl_auto; }

void dn_env_bl_auto_set(bool on)
{
    s_bl_auto = on;
    if (on) {
        /* On repart de l'état RÉEL de la dalle, pas d'un souvenir : sinon le
         * premier pas serait calculé contre une valeur périmée. */
        s_bl_dernier_pct = dn_display_backlight_pct_state();
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
    if (lux_haut > 54612) { /* plafond physique du BH1750 au MTreg 69 */
        return ESP_ERR_INVALID_ARG;
    }
    s_bl_lux_bas = lux_bas;
    s_bl_lux_haut = lux_haut;
    return ESP_OK;
}

esp_err_t dn_env_bl_pas_set(int pas)
{
    if (pas < 1 || pas > 100) {
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

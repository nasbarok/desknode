/*
 * dn_capteurs — lecture du BME680 sur le bus I²C partagé (dn2-1, P4).
 * Le POURQUOI de chaque choix est dans dn_capteurs.h ; ici, le COMMENT.
 */
#include "dn_capteurs.h"

#include <math.h>
#include <string.h>

#include "bme680.h"
#include "dn_display.h"
#include "dn_pins.h"
#include "dn_ui.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "dn_capt";

/* ⚠️ portMUX et non un mutex : ces champs sont lus par la console (cœur 0) et
 * écrits par la tâche de lecture. Les int64 sont DÉCHIRABLES sur Xtensa (deux
 * stockages 32 bits) — `volatile` n'y change rien. Leçon du ledger dn1-2. */
static portMUX_TYPE s_mux = portMUX_INITIALIZER_UNLOCKED;

static bme680_handle_t s_dev;
static uint8_t s_chip_id;
static uint8_t s_variant;
static bool s_gaz = DN_CAPT_GAZ_DEFAUT;
static bool s_gaz_demande = DN_CAPT_GAZ_DEFAUT;

static int s_temp_dx = -1; /* dixièmes de °C */
static int s_hum_dx = -1;  /* dixièmes de %RH */
static int64_t s_lu_us = -1;
static int64_t s_cycle_us = -1;
static dn_capt_compteurs_t s_cnt;
static bool s_a_deja_lu; /* au moins une valeur valide publiée depuis le boot */
static bool s_degrade;   /* on ne publie plus de valeur valide */
/* Les trois registres de config RELUS dans le capteur, et ce que l'init y a posé.
 * L'écart entre les deux est le seul moyen de voir qu'il a redémarré. */
static uint8_t s_reg_hum, s_reg_meas, s_reg_cfg;
static uint8_t s_att_hum, s_att_meas, s_att_cfg;
static bool s_conforme;
static i2c_master_dev_handle_t s_brut; /* accès registre nu, hors driver */
/*
 * 🔴 LE SUIVI DE REPRISE NE DOIT PAS DÉPENDRE DE L'HORODATAGE — correctif du
 * 2026-08-17, trouvé en jouant l'AC7 sur la carte.
 *
 * La première version déduisait « on était muet » de `dn_capt_etat()`, qui se
 * calcule à partir de `s_lu_us`. Or la réparation d'un capteur qui a perdu sa
 * config EFFACE `s_lu_us` (c'est ce qui fait passer les cases à « -- »). L'état
 * tombait donc à JAMAIS et non à MUET, et la reprise n'était JAMAIS comptée :
 * **le code de réparation aveuglait le compteur censé prouver qu'il répare.**
 * Constat qui l'a révélé : reprise vue à l'écran, `reprises : 0` au compteur.
 *
 * Deux drapeaux indépendants, écrits uniquement par la tâche :
 */
static dn_capt_faute_t s_faute;
static int s_faute_restants;

/*
 * Bornes de PLAUSIBILITÉ PHYSIQUE, pas de confort.
 *
 * Le BME680 est spécifié −40..+85 °C et 0..100 %RH. Une valeur hors de là n'est
 * pas « une pièce inhabituelle » : c'est une lecture corrompue, un capteur qui
 * n'a pas fini sa conversion, ou un octet perdu sur le bus. On la REJETTE avec
 * son compteur plutôt que de l'afficher — une case qui montre −273 °C envoie
 * chercher la panne dans l'UI alors qu'elle est sur le fil.
 */
#define DN_CAPT_TEMP_MIN_DX (-400)
#define DN_CAPT_TEMP_MAX_DX 850
#define DN_CAPT_HUM_MIN_DX 0
#define DN_CAPT_HUM_MAX_DX 1000

const char *dn_capt_etat_nom(dn_capt_etat_t e)
{
    switch (e) {
    case DN_CAPT_JAMAIS:
        return "jamais lu";
    case DN_CAPT_VIVANT:
        return "VIVANT";
    case DN_CAPT_MUET:
        return "MUET";
    default:
        return "?";
    }
}

static int64_t lu_us(void)
{
    portENTER_CRITICAL(&s_mux);
    int64_t v = s_lu_us;
    portEXIT_CRITICAL(&s_mux);
    return v;
}

dn_capt_etat_t dn_capt_etat(void)
{
    int64_t lu = lu_us();
    if (lu < 0) {
        /* ⚠️ « jamais lu » et « on lisait, on ne lit plus » sont DEUX diagnostics
         * opposés — l'un envoie chercher un cablage, l'autre une panne apparue en
         * route. L'invalidation d'une valeur fausse efface l'horodatage (c'est ce
         * qui fait passer les cases a « -- »), donc `lu < 0` ne suffit PLUS a
         * conclure « jamais ». Constat du 2026-08-17 : la console annonçait
         * « jamais lu » apres 157 lectures reussies. `s_a_deja_lu` tranche. */
        return s_a_deja_lu ? DN_CAPT_MUET : DN_CAPT_JAMAIS;
    }
    return (esp_timer_get_time() - lu) < DN_CAPT_PEREMPTION_US ? DN_CAPT_VIVANT
                                                               : DN_CAPT_MUET;
}

int dn_capt_temperature_dixiemes(void)
{
    portENTER_CRITICAL(&s_mux);
    int v = s_temp_dx;
    portEXIT_CRITICAL(&s_mux);
    return v;
}

int dn_capt_humidite_dixiemes(void)
{
    portENTER_CRITICAL(&s_mux);
    int v = s_hum_dx;
    portEXIT_CRITICAL(&s_mux);
    return v;
}

int64_t dn_capt_age_us(void)
{
    int64_t lu = lu_us();
    return (lu < 0) ? -1 : esp_timer_get_time() - lu;
}

int64_t dn_capt_duree_cycle_us(void)
{
    portENTER_CRITICAL(&s_mux);
    int64_t v = s_cycle_us;
    portEXIT_CRITICAL(&s_mux);
    return v;
}

void dn_capt_compteurs(dn_capt_compteurs_t *out)
{
    portENTER_CRITICAL(&s_mux);
    *out = s_cnt;
    portEXIT_CRITICAL(&s_mux);
}

void dn_capt_reset_compteurs(void)
{
    /* ⚠️ On garde la VALEUR et son horodatage : remettre les compteurs à zéro ne
     * doit pas tuer la lecture en cours. Correctif de revue dn2-2 transposé
     * (`pc reset` avait le défaut inverse et sabotait ses propres campagnes). */
    portENTER_CRITICAL(&s_mux);
    memset(&s_cnt, 0, sizeof(s_cnt));
    portEXIT_CRITICAL(&s_mux);
}

const char *dn_capt_faute_nom(dn_capt_faute_t f)
{
    switch (f) {
    case DN_CAPT_FAUTE_MUET:
        return "MUET (le capteur ne repond plus)";
    case DN_CAPT_FAUTE_BORNES:
        return "BORNES (valeur hors plage physique)";
    case DN_CAPT_FAUTE_CONFIG:
        return "CONFIG (capteur fantome : repond mais a perdu sa config)";
    default:
        return "aucune";
    }
}

dn_capt_faute_t dn_capt_faute_active(void) { return s_faute; }
int dn_capt_faute_restants(void) { return s_faute_restants; }

esp_err_t dn_capt_simuler(dn_capt_faute_t f, int cycles)
{
    if (cycles < 0 || cycles > 600) {
        return ESP_ERR_INVALID_ARG;
    }
    if (f == DN_CAPT_FAUTE_AUCUNE || cycles == 0) {
        s_faute_restants = 0;
        s_faute = DN_CAPT_FAUTE_AUCUNE;
        return ESP_OK;
    }
    s_faute = f;
    s_faute_restants = cycles;
    return ESP_OK;
}

uint8_t dn_capt_reg_ctrl_hum(void) { return s_reg_hum; }
uint8_t dn_capt_reg_ctrl_meas(void) { return s_reg_meas; }
uint8_t dn_capt_reg_config(void) { return s_reg_cfg; }
bool dn_capt_config_conforme(void) { return s_conforme; }

uint8_t dn_capt_chip_id(void) { return s_chip_id; }
uint8_t dn_capt_variant(void) { return s_variant; }
bool dn_capt_gaz_actif(void) { return s_gaz; }

esp_err_t dn_capt_set_gaz(bool actif)
{
    if (!s_dev) {
        return ESP_ERR_INVALID_STATE;
    }
    s_gaz_demande = actif;
    return ESP_OK;
}

/*
 * La configuration, ligne par ligne — même discipline qu'une ligne de
 * sdkconfig.defaults : une ligne, une raison.
 */
static bme680_config_t config_voulue(bool gaz)
{
    bme680_config_t c = {
        .i2c_address = DN_BME680_ADDR,
        /* ⚠️ 400 kHz et non les 100 kHz par défaut du composant : une
         * transaction 4× plus courte occupe 4× moins longtemps un bus dont la
         * DMA du panneau se dispute déjà le SoC (§11.4). Et c'est la fréquence
         * que NOS autres devices demandent (dn_pins.h). */
        .i2c_clock_speed = DN_I2C_FREQ_HZ,
        /* FORCED : une mesure, puis retour en sommeil. C'est le mode qui
         * consomme et chauffe le MOINS — les deux comptent ici (§ DN_CAPT_GAZ). */
        .power_mode = BME680_POWER_MODE_FORCED,
        /* IIR sur 3 échantillons : lisse le bruit de conversion sans retarder
         * une vraie variation d'ambiance. ⚠️ Ce n'est PAS le « lissage » que le
         * brief demande (moyenne d'affichage) — celui-là reste explicitement
         * absent, comme en dn2-2, et se solde en dn4-1. */
        .iir_filter = BME680_IIR_FILTER_3,
        .standby_time = BME680_STANDBY_TIME_NONE, /* sans objet en FORCED */
        /* La pression n'est PAS au dashboard (brief : six widgets figés). On ne
         * la SAUTE pas pour autant : la compensation de température du BME680
         * s'appuie sur la chaîne de mesure complète, et 1× coûte le minimum. */
        .pressure_oversampling = BME680_PRESSURE_OVERSAMPLING_1X,
        /* 8× sur les deux grandeurs AFFICHÉES : c'est là qu'on paie pour de la
         * stabilité, et nulle part ailleurs. */
        .temperature_oversampling = BME680_TEMPERATURE_OVERSAMPLING_8X,
        .humidity_oversampling = BME680_HUMIDITY_OVERSAMPLING_8X,
        .gas_enabled = gaz,
        /* Sans objet quand gas_enabled=false, mais posés : si l'A/B de T9
         * rallume le gaz, il doit le faire dans les conditions du DÉFAUT du
         * composant (300 °C / 300 ms), sinon on comparerait deux choses
         * différentes et le delta ne voudrait rien dire. */
        .heater_temperature = 300,
        .heater_duration = 300,
        .heater_profile_size = 1,
    };
    return c;
}

/*
 * Lit les deux registres d'identité SANS le driver, par le bus nu.
 *
 * Pourquoi avant `bme680_init()` : ce dernier refuse si chip_id != 0x61, mais il
 * ne dit pas CE QU'IL A LU. Or « 0x60 » (BME280) et « 0x58 » (BMP280) sont des
 * diagnostics précis — un module vendu « BME680 » qui n'en est pas. Un refus
 * muet enverrait chercher la panne du côté du câblage, qu'on vient justement de
 * prouver bon.
 */
static void relever_identite(i2c_master_bus_handle_t bus)
{
    i2c_device_config_t cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = DN_BME680_ADDR,
        .scl_speed_hz = DN_I2C_FREQ_HZ,
    };
    i2c_master_dev_handle_t dev = NULL;
    if (i2c_master_bus_add_device(bus, &cfg, &dev) != ESP_OK) {
        return;
    }
    uint8_t reg = DN_BME680_REG_CHIP_ID;
    if (i2c_master_transmit_receive(dev, &reg, 1, &s_chip_id, 1, 200) != ESP_OK) {
        s_chip_id = 0;
    }
    reg = DN_BME680_REG_VARIANT;
    if (i2c_master_transmit_receive(dev, &reg, 1, &s_variant, 1, 200) != ESP_OK) {
        s_variant = 0;
    }
    i2c_master_bus_rm_device(dev);
}

static void journaliser_identite(void)
{
    const char *quoi = s_chip_id == DN_BME680_CHIP_ID
                           ? (s_variant == DN_BME680_VARIANT_688 ? "BME688" : "BME680")
                       : s_chip_id == 0x60 ? "BME280 — PAS de gaz"
                       : s_chip_id == 0x58 ? "BMP280 — NI gaz NI humidite"
                                           : "INCONNU";
    if (s_chip_id == DN_BME680_CHIP_ID) {
        ESP_LOGI(TAG, "identite : chip id 0x%02X, variant 0x%02X => %s @ 0x%02X",
                 s_chip_id, s_variant, quoi, DN_BME680_ADDR);
    } else {
        ESP_LOGE(TAG,
                 "identite INATTENDUE : chip id 0x%02X (attendu 0x%02X) => %s. "
                 "Le cablage n'est PAS en cause si le scan `i2c` voit 0x%02X.",
                 s_chip_id, DN_BME680_CHIP_ID, quoi, DN_BME680_ADDR);
    }
}

/* Applique la valeur aux cases 4 (TEMP.) et 5 (HUMIDITE) du dashboard.
 * ⚠️ dn_ui prend le verrou LVGL LUI-MÊME ; on ne le prend jamais ici. */
static void pousser_ui(void)
{
    dn_capt_etat_t e = dn_capt_etat();
    bool valide = (e == DN_CAPT_VIVANT);
    dn_ui_ambiance_maj(dn_capt_temperature_dixiemes(), dn_capt_humidite_dixiemes(),
                       valide, NULL);
}

/* Lit un registre par le bus NU. Le driver n'expose pas de lecture générique et
 * ses getters décodent en champs de bits — or ici on veut l'OCTET BRUT, celui
 * qu'on peut comparer et imprimer sans interprétation. */
static bool lire_reg(uint8_t reg, uint8_t *out)
{
    if (!s_brut) {
        return false;
    }
    return i2c_master_transmit_receive(s_brut, &reg, 1, out, 1, 200) == ESP_OK;
}

/*
 * 🔴 LE CAPTEUR PEUT REDÉMARRER SOUS NOS PIEDS — MESURÉ LE 2026-08-17.
 *
 * Couper son 3V3 quelques secondes remet les trois registres de configuration à
 * 0x00 : suréchantillonnages SKIPPED, mode SLEEP, filtre OFF. Le handle logiciel,
 * lui, survit intact — et `bme680_get_data()` continue de RÉUSSIR. La compensation
 * Bosch, alimentée par des ADC non configurés, produit alors **32,8 °C et 100 %RH**.
 *
 * ⚠️ CE QUI REND CE DÉFAUT MÉCHANT, ET POURQUOI AUCUNE GARDE EXISTANTE NE L'ATTRAPE :
 *   · ce n'est PAS une erreur de transport — le capteur répond parfaitement ;
 *   · ce n'est PAS une valeur aberrante — 32,8 °C et 100 %RH sont physiquement
 *     plausibles, donc les bornes les acceptent ;
 *   · ce n'est PAS un silence — l'état reste VIVANT, la péremption ne se déclenche
 *     jamais, et `reprises` reste à 0.
 * L'AC7 protège contre « le capteur se tait et la case fige ». Le vrai mode de
 * panne est « le capteur répond avec du n'importe quoi », et il fallait le geste
 * physique de l'owner pour le faire apparaître.
 *
 * ⇒ On RELIT la config à chaque cycle et on la RÉ-APPLIQUE si elle a disparu.
 *   Le cycle de la reconfiguration est déclaré INVALIDE : la première conversion
 *   qui suit part d'un capteur qu'on vient de reprogrammer.
 */
static bool config_verifier_et_reparer(void)
{
    uint8_t h = 0, m = 0, c = 0;
    if (!lire_reg(0x72, &h) || !lire_reg(0x74, &m) || !lire_reg(0x75, &c)) {
        return true; /* le bus a échoué : c'est err_i2c qui parlera, pas ici */
    }
    /* ⚠️ Les 2 bits de POIDS FAIBLE de 0x74 sont le MODE, que le driver change à
     * chaque mesure forcée (sleep -> forced -> sleep). Les comparer ferait crier
     * la garde à chaque cycle. On ne compare que les suréchantillonnages. */
    s_reg_hum = h;
    s_reg_meas = m;
    s_reg_cfg = c;
    s_conforme = ((h & 0x07) == (s_att_hum & 0x07)) &&
                 ((m & 0xFC) == (s_att_meas & 0xFC)) &&
                 ((c & 0x1C) == (s_att_cfg & 0x1C));
    if (s_faute == DN_CAPT_FAUTE_CONFIG && s_faute_restants > 0) {
        /* On ment sur le VERDICT, pas sur la lecture : les octets imprimés par
         * `capteurs` restent les vrais. Sinon l'injecteur fabriquerait aussi le
         * diagnostic, et on ne testerait plus rien. */
        s_conforme = false;
    }
    if (s_conforme) {
        return true;
    }

    ESP_LOGE(TAG,
             "🔴 LE CAPTEUR A PERDU SA CONFIGURATION (0x72=%02X 0x74=%02X 0x75=%02X, "
             "attendu %02X/%02X/%02X) — il a redemarre. Ses valeurs etaient FAUSSES "
             "et PLAUSIBLES. Reconfiguration.",
             h, m, c, s_att_hum, s_att_meas, s_att_cfg);

    bme680_config_t cfg = config_voulue(s_gaz);
    bme680_handle_t neuf = NULL;
    if (bme680_init(dn_display_i2c_bus(), &cfg, &neuf) != ESP_OK || !neuf) {
        s_degrade = true;
        ESP_LOGE(TAG, "reconfiguration ECHOUEE — les cases vont passer a « -- »");
        return false;
    }
    if (s_dev) {
        bme680_delete(s_dev); /* ⚠️ sinon on fuit un device sur le bus a chaque reset */
    }
    s_dev = neuf;
    s_degrade = true;
    portENTER_CRITICAL(&s_mux);
    s_cnt.reconfigs++;
    /* 🔴 ON INVALIDE LA VALEUR COURANTE. Elle a été produite par un capteur non
     * configuré : la garder affichée le temps d'un cycle de plus serait exactement
     * le mensonge d'interface que l'AC7 interdit. Les cases passent a « -- ». */
    s_temp_dx = -1;
    s_hum_dx = -1;
    s_lu_us = -1;
    portEXIT_CRITICAL(&s_mux);
    return false;
}

static void tache_capteurs(void *arg)
{
    (void)arg;
    TickType_t reveil = xTaskGetTickCount();

    while (1) {
        /* Cadence en TEMPS ABSOLU : vTaskDelayUntil ne dérive pas, contrairement
         * à un vTaskDelay qui ajouterait la durée de la mesure à chaque tour —
         * et la mesure dure des centaines de millisecondes. */
        vTaskDelayUntil(&reveil, pdMS_TO_TICKS(DN_CAPT_PERIODE_MS));

        /* Bascule du gaz demandée à chaud (A/B de T9) : appliquée ICI, entre
         * deux cycles, jamais au milieu d'une conversion. */
        if (s_gaz_demande != s_gaz && s_dev) {
            /*
             * ⚠️ LE GAZ TIENT DANS DEUX REGISTRES, PAS UN — et les deux comptent :
             *   · gas0 (0x70) porte `heater_disabled` — la plaque chauffante ;
             *   · gas1 (0x71) porte `gas_conversion_enabled` — la conversion.
             * Couper la conversion en laissant le chauffeur allumé chaufferait le
             * die pour RIEN, ce qui est exactement le biais qu'on cherche à
             * supprimer. Les deux se posent ensemble.
             *
             * ⚠️ LECTURE-MODIFICATION-ÉCRITURE, jamais une écriture sèche : ces
             * registres portent AUSSI `heater_setpoint` et le MSB du standby.
             * Écrire une union construite à la main les remettrait à zéro en
             * silence — le genre d'effet de bord qu'on ne voit que trois mesures
             * plus tard.
             */
            bme680_control_gas0_register_t g0;
            bme680_control_gas1_register_t g1;
            esp_err_t e0 = bme680_get_control_gas0_register(s_dev, &g0);
            esp_err_t e1 = bme680_get_control_gas1_register(s_dev, &g1);
            if (e0 == ESP_OK && e1 == ESP_OK) {
                g0.bits.heater_disabled = !s_gaz_demande;
                g1.bits.gas_conversion_enabled = s_gaz_demande;
                e0 = bme680_set_control_gas0_register(s_dev, g0);
                e1 = bme680_set_control_gas1_register(s_dev, g1);
            }
            if (e0 == ESP_OK && e1 == ESP_OK) {
                s_gaz = s_gaz_demande;
                ESP_LOGW(TAG,
                         "chauffage gaz %s — ⚠️ la temperature met du temps a se "
                         "stabiliser : ne pas lire le delta sur le cycle suivant",
                         s_gaz ? "ACTIVE (le die chauffe)" : "coupe");
            } else {
                s_gaz_demande = s_gaz; /* échec : on ne ment pas sur l'état */
                ESP_LOGE(TAG, "bascule du chauffage gaz REFUSEE par le capteur "
                              "(gas0 %s, gas1 %s)",
                         esp_err_to_name(e0), esp_err_to_name(e1));
            }
        }

        if (!s_dev) {
            continue;
        }

        /* Faute injectée : elle emprunte EXACTEMENT les chemins d'erreur réels,
         * compteurs compris. Décrémentée ici, une fois par cycle. */
        if (s_faute_restants > 0) {
            dn_capt_faute_t f = s_faute;
            if (--s_faute_restants == 0) {
                ESP_LOGW(TAG, "faute simulee « %s » TERMINEE", dn_capt_faute_nom(f));
                s_faute = DN_CAPT_FAUTE_AUCUNE;
            }
            if (f == DN_CAPT_FAUTE_MUET) {
                s_degrade = true;
                portENTER_CRITICAL(&s_mux);
                s_cnt.err_i2c++;
                portEXIT_CRITICAL(&s_mux);
                pousser_ui();
                continue;
            }
            if (f == DN_CAPT_FAUTE_BORNES) {
                s_degrade = true;
                portENTER_CRITICAL(&s_mux);
                s_cnt.err_bornes++;
                portEXIT_CRITICAL(&s_mux);
                pousser_ui();
                continue;
            }
        }

        /* AVANT de croire la moindre valeur : le capteur est-il toujours celui
         * qu'on a configuré ? (voir l'en-tête de config_verifier_et_reparer) */
        if (!config_verifier_et_reparer()) {
            pousser_ui(); /* les cases disent « -- » : on ne publie pas du faux */
            continue;
        }

        int64_t t0 = esp_timer_get_time();
        bme680_data_t d;
        esp_err_t err = bme680_get_data(s_dev, &d);
        int64_t duree = esp_timer_get_time() - t0;

        if (err != ESP_OK) {
            s_degrade = true;
            /* ⚠️ DEUX SEAUX, PAS UN. Un échec de transport (NACK, timeout : le
             * capteur ne répond plus — fil, soudure) et un échec de donnée (il
             * répond mais la conversion n'est pas prête) sont des diagnostics
             * OPPOSÉS. dn2-2 a payé pour l'avoir appris sur « tronquée » vs
             * « trop longue ». */
            portENTER_CRITICAL(&s_mux);
            if (err == ESP_ERR_TIMEOUT || err == ESP_ERR_INVALID_STATE ||
                err == ESP_FAIL) {
                s_cnt.err_i2c++;
            } else {
                s_cnt.err_donnee++;
            }
            portEXIT_CRITICAL(&s_mux);
            pousser_ui(); /* la péremption peut être passée : les cases doivent le dire */
            continue;
        }

        int t_dx = (int)lroundf(d.air_temperature * 10.0f);
        int h_dx = (int)lroundf(d.relative_humidity * 10.0f);

        if (t_dx < DN_CAPT_TEMP_MIN_DX || t_dx > DN_CAPT_TEMP_MAX_DX ||
            h_dx < DN_CAPT_HUM_MIN_DX || h_dx > DN_CAPT_HUM_MAX_DX) {
            s_degrade = true;
            portENTER_CRITICAL(&s_mux);
            s_cnt.err_bornes++;
            portEXIT_CRITICAL(&s_mux);
            ESP_LOGW(TAG, "valeurs hors plage physique : %d,%d C / %d,%d %% — rejetees",
                     t_dx / 10, abs(t_dx % 10), h_dx / 10, h_dx % 10);
            pousser_ui();
            continue;
        }

        /* Une valeur valide part d'ici. Si on était dégradé ET qu'on avait déjà
         * lu au moins une fois, c'est une REPRISE — quelle qu'ait été la cause
         * (silence, valeur hors bornes, ou perte de configuration). */
        bool reprise = s_degrade && s_a_deja_lu;
        s_degrade = false;
        s_a_deja_lu = true;

        portENTER_CRITICAL(&s_mux);
        s_temp_dx = t_dx;
        s_hum_dx = h_dx;
        s_lu_us = esp_timer_get_time();
        s_cycle_us = duree;
        s_cnt.lectures++;
        if (reprise) {
            s_cnt.reprises++;
        }
        portEXIT_CRITICAL(&s_mux);

        pousser_ui();
    }
}

esp_err_t dn_capteurs_init(void)
{
    i2c_master_bus_handle_t bus = dn_display_i2c_bus();
    if (!bus) {
        ESP_LOGE(TAG, "bus I2C absent — dn_display_init() n'a pas tourne");
        return ESP_ERR_INVALID_STATE;
    }

    relever_identite(bus);
    journaliser_identite();

    bme680_config_t cfg = config_voulue(DN_CAPT_GAZ_DEFAUT);
    esp_err_t err = bme680_init(bus, &cfg, &s_dev);
    if (err != ESP_OK || !s_dev) {
        /* ⚠️ NON FATAL, et la tâche démarre QUAND MÊME : elle publiera « jamais
         * lu », et `capteurs` dira pourquoi. Un capteur muet ne doit pas priver
         * l'opérateur de l'outil qui explique son silence. */
        ESP_LOGE(TAG, "bme680_init a echoue (%s) — les cases resteront « -- »",
                 esp_err_to_name(err));
        s_dev = NULL;
    } else {
        ESP_LOGI(TAG,
                 "BME680 pret @ 0x%02X — FORCED, T/H 8x, P 1x, IIR 3, gaz %s, "
                 "cadence %d ms, peremption %lld ms",
                 DN_BME680_ADDR, DN_CAPT_GAZ_DEFAUT ? "ACTIF" : "coupe",
                 DN_CAPT_PERIODE_MS, (long long)(DN_CAPT_PEREMPTION_US / 1000));
        if (!DN_CAPT_GAZ_DEFAUT) {
            ESP_LOGI(TAG,
                     "  (gaz coupe DELIBEREMENT : sa plaque a 300 C chaufferait le "
                     "die qui porte le thermometre, pour une donnee hors des 6 "
                     "widgets du brief. A/B jouable a chaud : `capteurs gaz on`)");
        }
    }

    /* Handle NU, gardé ouvert : il sert à relire les registres de config sans
     * passer par le driver, et il doit survivre à une reconstruction de s_dev. */
    i2c_device_config_t brut = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = DN_BME680_ADDR,
        .scl_speed_hz = DN_I2C_FREQ_HZ,
    };
    if (i2c_master_bus_add_device(bus, &brut, &s_brut) != ESP_OK) {
        ESP_LOGW(TAG, "acces registre nu indisponible — la garde de "
                      "reconfiguration sera INERTE, et elle le dira");
        s_brut = NULL;
    }
    /* La configuration ATTENDUE, relue dans le capteur JUSTE APRÈS que le driver
     * l'a posée : on n'invente pas la valeur de référence, on la CONSTATE. C'est
     * ce qui rend la comparaison de chaque cycle honnête. */
    if (s_dev && s_brut) {
        lire_reg(0x72, &s_att_hum);
        lire_reg(0x74, &s_att_meas);
        lire_reg(0x75, &s_att_cfg);
        s_reg_hum = s_att_hum;
        s_reg_meas = s_att_meas;
        s_reg_cfg = s_att_cfg;
        s_conforme = true;
        ESP_LOGI(TAG, "config relue dans le capteur : 0x72=%02X 0x74=%02X 0x75=%02X",
                 s_att_hum, s_att_meas, s_att_cfg);
    }

    BaseType_t ok = xTaskCreate(tache_capteurs, "dn_capt", 4096, NULL, 3, NULL);
    if (ok != pdPASS) {
        ESP_LOGE(TAG, "xTaskCreate a echoue — RAM interne insuffisante");
        return ESP_ERR_NO_MEM;
    }
    return ESP_OK;
}

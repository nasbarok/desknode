#include "dn_touch.h"

#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>

#include "dn_display.h"
#include "dn_pins.h"
#include "driver/gpio.h"
#include "esp_check.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_touch_gt911.h"
#include "esp_log.h"
#include "esp_lvgl_port.h"
#include "esp_rom_sys.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "dn_touch";

/*
 * ── LES DÉLAIS DE LA SÉQUENCE DE RESET ───────────────────────────────────────
 *
 * Repris de la démo officielle Waveshare (Touch_Driver/GT911.c), qui fait
 * tourner CETTE dalle : INT en sortie basse 150 ms, TP_RST bas 150 ms, TP_RST
 * haut 50 ms, puis INT relâché en entrée. Ce sont donc des valeurs VUES MARCHER
 * sur ce matériel, pas une recommandation générique — le datasheet Goodix, lui,
 * ne demande que quelques millisecondes.
 *
 * ⚠️ Ils coûtent 350 ms de boot. C'est assumé : ils ne sont joués qu'une fois, et
 *    les raccourcir serait la première chose à soupçonner si l'adresse latchée
 *    devenait instable. Réglables sans reflasher par `touch reset <bas> <haut>`.
 */
#define DN_TP_INT_LOW_MS 150
#define DN_TP_RST_LOW_MS 150
#define DN_TP_RST_HIGH_MS 50

/*
 * ── LE MODE DE LECTURE PAR DÉFAUT AU BOOT ────────────────────────────────────
 *
 * POLL, et c'est un choix de SÛRETÉ avant d'être un arbitrage : un tactile qui
 * marche moins bien se mesure, un tactile muet-en-silence ne se mesure pas. Le
 * mode EVENT dépend d'un INT dont le brochage lui-même était un écart
 * documentaire à l'ouverture de dn1-4 (§1.2 muet, wiki et stories disant GPIO16).
 * On démarre donc sur le mode qui ne peut PAS être muet, et `touch mode event`
 * fait l'A/B à chaud, avec le compteur d'IRQ comme témoin.
 *
 * ⚠️ Cette valeur est le point de départ de la campagne AC2. Si la mesure retient
 *    EVENT, c'est ICI qu'on l'écrit — et le commentaire dit alors pourquoi.
 */
#define DN_TOUCH_MODE_DEFAUT DN_TOUCH_MODE_POLL

/* Registres du GT911 qu'on LIT (jamais qu'on écrit). Adresses 16 bits, le
 * composant esp_lcd les transporte via `lcd_cmd_bits = 16`. */
#define DN_GT911_REG_PRODUCT_ID 0x8140 /* 4 octets ASCII + 2 octets de version FW */
#define DN_GT911_REG_CONFIG 0x8047     /* version de config, puis résolution, puis modes */

/* ── État ─────────────────────────────────────────────────────────────────── */

static esp_lcd_panel_io_handle_t s_io;
static esp_lcd_touch_handle_t s_tp;
static lv_indev_t *s_indev;

static uint8_t s_addr;       /* adresse à laquelle il a RÉPONDU (0 = jamais) */
static uint8_t s_addr_visee; /* adresse que la séquence visait */
static uint8_t s_addr_avant; /* adresse vue AVANT notre séquence (0 = muet) */
static esp_err_t s_probe_avant = ESP_ERR_INVALID_STATE;
static esp_err_t s_probe_apres = ESP_ERR_INVALID_STATE;
static dn_touch_cfg_t s_cfg;
static int s_rst_bas_ms = DN_TP_RST_LOW_MS;
static int s_rst_haut_ms = DN_TP_RST_HIGH_MS;

static volatile dn_touch_mode_t s_mode = DN_TOUCH_MODE_DEFAUT;

/* Compteurs — 32 bits (voir dn_touch.h). `s_irq` est écrit par l'ISR. */
static volatile uint32_t s_irq, s_lectures, s_appuis, s_relaches, s_err_i2c;
static volatile uint32_t s_x, s_y, s_brut_x, s_brut_y;
static volatile bool s_appuye;

/* Latence tap -> écran flushé (AC5). Écrite et lue dans la tâche LVGL. */
static volatile bool s_lat_armee;
static int64_t s_lat_t0;
static volatile uint32_t s_lat_n, s_lat_min_us = UINT32_MAX, s_lat_max_us;
static volatile uint32_t s_lat_total_us, s_lat_dernier_us;

/* ── Noms ─────────────────────────────────────────────────────────────────── */

const char *dn_touch_mode_name(dn_touch_mode_t m)
{
    switch (m) {
    case DN_TOUCH_MODE_EVENT:
        return "event";
    case DN_TOUCH_MODE_POLL:
        return "poll";
    default:
        return "?";
    }
}

bool dn_touch_mode_from_name(const char *nom, dn_touch_mode_t *out)
{
    for (int i = 0; i < DN_TOUCH_MODE_COUNT; i++) {
        if (strcasecmp(nom, dn_touch_mode_name((dn_touch_mode_t)i)) == 0) {
            *out = (dn_touch_mode_t)i;
            return true;
        }
    }
    return false;
}

/* ── Le témoin physique de l'INT ──────────────────────────────────────────── */

int dn_touch_int_level(void) { return gpio_get_level(DN_PIN_TP_INT); }

uint32_t dn_touch_int_scan(int duree_ms, int *niveau_final)
{
    if (duree_ms < 1) {
        duree_ms = 1;
    }
    if (duree_ms > 5000) {
        duree_ms = 5000;
    }
    /*
     * ⚠️ CE QUE CET INSTRUMENT NE VOIT PAS, et qui est déclaré plutôt que caché :
     *    il échantillonne toutes les ~100 µs et RESPIRE un tick toutes les 20 ms
     *    (sans quoi la tâche IDLE du cœur ne serait jamais servie et le watchdog
     *    de tâche s'en mêlerait). Une impulsion plus courte que la respiration
     *    peut donc être manquée. Il répond à « la broche bouge-t-elle du tout »,
     *    pas à « combien de fronts exactement » — le compteur d'IRQ répond à
     *    celle-là, et c'est précisément parce qu'on ne peut pas lui faire
     *    confiance a priori que ce témoin-ci existe.
     */
    int niveau = gpio_get_level(DN_PIN_TP_INT);
    uint32_t transitions = 0;
    int64_t fin = esp_timer_get_time() + (int64_t)duree_ms * 1000;
    int64_t prochaine_respiration = esp_timer_get_time() + 20000;
    while (esp_timer_get_time() < fin) {
        int n = gpio_get_level(DN_PIN_TP_INT);
        if (n != niveau) {
            transitions++;
            niveau = n;
        }
        esp_rom_delay_us(100);
        if (esp_timer_get_time() >= prochaine_respiration) {
            vTaskDelay(1);
            prochaine_respiration = esp_timer_get_time() + 20000;
        }
    }
    if (niveau_final) {
        *niveau_final = niveau;
    }
    return transitions;
}

/* ── L'ISR ────────────────────────────────────────────────────────────────── */

/*
 * ⚠️ PAS D'IRAM_ATTR, ET C'EST DÉLIBÉRÉ (contrairement au callback du portage,
 *    qui le porte). Cette fonction appelle `lvgl_port_task_wake()`, qui vit en
 *    FLASH : marquer l'ISR IRAM_ATTR annoncerait « je survis au cache désactivé »
 *    alors qu'elle sauterait droit dans la flash à l'instant où le cache est
 *    coupé — une étiquette qui ment, avec une panne à la clé le jour où le
 *    stimulus `flash` tourne. Le service ISR GPIO est installé par
 *    `esp_lcd_touch` avec des flags nuls (pas d'ESP_INTR_FLAG_IRAM) : l'interruption
 *    est donc masquée pendant les opérations flash, ce qui est exactement le
 *    comportement voulu.
 *
 * ⚠️ ELLE REMPLACE CELLE DU PORTAGE, en connaissance de cause. `lvgl_port_add_touch()`
 *    enregistre la sienne (esp_lvgl_port_touch.c:60-64) et
 *    `esp_lcd_touch_register_interrupt_callback()` ASSIGNE — le dernier inscrit
 *    gagne, en silence (le trap n°1 de ce dépôt, déjà payé sur les callbacks
 *    vsync). On s'inscrit donc APRÈS, et on REPRODUIT son effet exact : réveiller
 *    la tâche LVGL avec l'indev en paramètre. Le seul ajout est le compteur.
 */
static void dn_touch_isr(esp_lcd_touch_handle_t tp)
{
    (void)tp;
    s_irq++;
    /* En polling, réveiller la tâche à chaque front ne servirait à rien — et
     * fausserait la charge CPU attribuée au mode POLL, qui est justement ce
     * qu'AC2 compare. */
    if (s_mode == DN_TOUCH_MODE_EVENT && s_indev) {
        lvgl_port_task_wake(LVGL_PORT_EVENT_TOUCH, s_indev);
    }
}

/* ── Les coordonnées BRUTES ───────────────────────────────────────────────── */

/*
 * `esp_lcd_touch` appelle ce callback APRÈS la lecture du contrôleur et AVANT
 * d'appliquer swap/mirror (esp_lcd_touch.c:79-107). C'est donc le seul point où
 * le brut existe encore — et sans lui, la campagne des 4 coins ne pourrait pas
 * distinguer « la dalle rapporte autre chose que ce qu'on croit » de « nos flags
 * sont à l'envers ».
 */
static void dn_touch_brut(esp_lcd_touch_handle_t tp, uint16_t *x, uint16_t *y,
                          uint16_t *strength, uint8_t *point_num,
                          uint8_t max_point_num)
{
    (void)tp;
    (void)strength;
    (void)max_point_num;
    if (point_num && *point_num > 0 && x && y) {
        s_brut_x = x[0];
        s_brut_y = y[0];
    }
}

/* ── Notre read_cb ────────────────────────────────────────────────────────── */

/*
 * ── POURQUOI ON REMPLACE CELUI DU PORTAGE (même geste que le flush de dn_ui) ──
 *
 * 1. IL PANIQUE SUR UNE ERREUR I²C. `lvgl_port_touchpad_read()` fait
 *    `ESP_ERROR_CHECK(esp_lcd_touch_read_data(...))` (esp_lvgl_port_touch.c:125) :
 *    un NACK sur un bus partagé avec quatre autres composants ferait ABORT le
 *    firmware, depuis la tâche LVGL, sans rien avoir mesuré. Une transaction
 *    ratée doit être COMPTÉE, pas fatale.
 * 2. IL NE COMPTE RIEN. Le coût du polling (une transaction I²C par cycle), le
 *    nombre d'appuis, le dernier point : rien de tout cela n'existe chez lui, et
 *    ce dépôt n'accepte pas une couche sans son instrument.
 *
 * Le reste de `lvgl_port_add_touch()` est CONSERVÉ : création de l'indev, mode
 * EVENT, ISR. On ne remplace que la lecture.
 *
 * ⚠️ Tourne DANS la tâche LVGL, sous son verrou : pas de verrou à prendre ici, et
 *    pas de travail long non plus.
 */
static void dn_touch_read(lv_indev_t *indev, lv_indev_data_t *data)
{
    (void)indev;
    s_lectures++;

    esp_err_t err = esp_lcd_touch_read_data(s_tp);
    if (err != ESP_OK) {
        s_err_i2c++;
        /*
         * ÉTAT PRÉCÉDENT RÉPÉTÉ, jamais « relâché ». Forcer le relâchement sur
         * une erreur fabriquerait un clic (LVGL valide un CLICKED sur
         * appui->relâchement au même endroit) : une transaction I²C perdue
         * ouvrirait un écran de détail. Répéter l'état ne fabrique rien.
         */
        data->state = s_appuye ? LV_INDEV_STATE_PRESSED : LV_INDEV_STATE_RELEASED;
        data->point.x = (int32_t)s_x;
        data->point.y = (int32_t)s_y;
        return;
    }

    /* `esp_lcd_touch_get_data` et non `…_get_coordinates` : la seconde est
     * DÉPRÉCIÉE depuis esp_lcd_touch 1.2 (retrait annoncé en 2.0.0) et le
     * compilateur le dit. Les deux passent par le même chemin —
     * `process_coordinates` puis swap/mirror (esp_lcd_touch.c:131-152) — donc la
     * capture du brut et les flags d'orientation gardent exactement le même sens.
     * ⚠️ `n` est initialisé à 0 ICI : quand rien n'est touché, la fonction rend
     *    ESP_OK sans forcément y toucher. */
    esp_lcd_touch_point_data_t pts[CONFIG_ESP_LCD_TOUCH_MAX_POINTS] = {0};
    uint8_t n = 0;
    esp_err_t lu = esp_lcd_touch_get_data(s_tp, pts, &n,
                                          CONFIG_ESP_LCD_TOUCH_MAX_POINTS);

    if (lu == ESP_OK && n > 0) {
        s_x = pts[0].x;
        s_y = pts[0].y;
        data->point.x = (int32_t)pts[0].x;
        data->point.y = (int32_t)pts[0].y;
        data->state = LV_INDEV_STATE_PRESSED;
        if (!s_appuye) {
            s_appuye = true;
            s_appuis++;
        }
    } else {
        data->point.x = (int32_t)s_x;
        data->point.y = (int32_t)s_y;
        data->state = LV_INDEV_STATE_RELEASED;
        if (s_appuye) {
            s_appuye = false;
            s_relaches++;
        }
    }
}

/* ── Lecture de la config du GT911 ────────────────────────────────────────── */

static void gt911_lire_config(void)
{
    memset(&s_cfg, 0, sizeof(s_cfg));
    if (!s_io) {
        return;
    }

    uint8_t id[6] = {0};
    if (esp_lcd_panel_io_rx_param(s_io, DN_GT911_REG_PRODUCT_ID, id, sizeof(id)) !=
        ESP_OK) {
        ESP_LOGW(TAG, "identité GT911 illisible — les champs restent nuls");
        return;
    }
    /* Les 4 premiers octets sont de l'ASCII (« 911 » + 0) ; on ne fait confiance
     * à rien et on force le terminateur. */
    /* Le 4e octet vaut 0 sur ce GT911 (mesuré : 0x39 0x31 0x31 0x00 = « 911 »).
     * On COUPE au premier octet non imprimable au lieu de le remplacer par un
     * caractère : « 911? » se lit comme une référence produit inconnue, alors que
     * c'est juste le terminateur. Une étiquette approximative sur une identité de
     * composant envoie chercher la panne au mauvais endroit. */
    memset(s_cfg.product_id, 0, sizeof(s_cfg.product_id));
    for (int i = 0; i < 4; i++) {
        if (id[i] < 0x20 || id[i] > 0x7e) {
            break;
        }
        s_cfg.product_id[i] = (char)id[i];
    }
    s_cfg.fw_version = (uint16_t)id[4] | ((uint16_t)id[5] << 8);

    /* 0x8047 .. 0x804D : version de config, X max, Y max, nb de points, modes. */
    uint8_t c[7] = {0};
    if (esp_lcd_panel_io_rx_param(s_io, DN_GT911_REG_CONFIG, c, sizeof(c)) !=
        ESP_OK) {
        ESP_LOGW(TAG, "config GT911 illisible — les champs restent nuls");
        return;
    }
    s_cfg.cfg_version = c[0];
    s_cfg.x_res = (uint16_t)c[1] | ((uint16_t)c[2] << 8);
    s_cfg.y_res = (uint16_t)c[3] | ((uint16_t)c[4] << 8);
    s_cfg.touch_max = c[5] & 0x0f;
    s_cfg.trig_mode = c[6] & 0x03;
    s_cfg.lue = true;
}

/* Nom lisible du mode de déclenchement de l'INT (0x804D bits 1-0). */
static const char *trig_name(uint8_t m)
{
    switch (m & 0x03) {
    case 0:
        return "front MONTANT";
    case 1:
        return "front DESCENDANT";
    case 2:
        return "niveau BAS";
    case 3:
        return "niveau HAUT";
    default:
        return "?";
    }
}

/* ── Bring-up ─────────────────────────────────────────────────────────────── */

static esp_err_t probe_deux_adresses(i2c_master_bus_handle_t bus, uint8_t *trouve)
{
    esp_err_t e5d = i2c_master_probe(bus, DN_GT911_ADDR, 100);
    if (e5d == ESP_OK) {
        *trouve = DN_GT911_ADDR;
        return ESP_OK;
    }
    esp_err_t e14 = i2c_master_probe(bus, DN_GT911_ADDR_BACKUP, 100);
    if (e14 == ESP_OK) {
        *trouve = DN_GT911_ADDR_BACKUP;
        return ESP_OK;
    }
    *trouve = 0;
    /* On rend l'erreur de l'adresse VISÉE : c'est celle qui informe. */
    return e5d;
}

esp_err_t dn_touch_init(void)
{
    i2c_master_bus_handle_t bus = dn_display_i2c_bus();
    ESP_RETURN_ON_FALSE(bus, ESP_ERR_INVALID_STATE, TAG,
                        "bus I2C absent — dn_display_init() n'a pas tourné");

    s_addr_visee = DN_GT911_ADDR;

    /*
     * ── LE PROBE AVANT LA SÉQUENCE — ET CE QUE LA CARTE EN A DIT ─────────────
     *
     * La story l'annonçait comme un TÉMOIN NÉGATIF : « un scan I²C avant le reset
     * tactile ne voit PAS le GT911 (il ne sort de reset qu'après la séquence
     * EXIO2) ». MESURÉ le 2026-08-16 sur cette carte : c'est FAUX. Il répond
     * DÉJÀ, avant toute intervention de notre part.
     *
     * Ce que ça établit : TP_RST n'est PAS maintenu bas quand l'expander le laisse
     * en entrée haute impédance — un tirage de la carte le tient haut, donc le
     * GT911 est sorti de reset tout seul à la mise sous tension, et il a latché
     * son adresse à ce moment-là, sur le niveau d'INT du démarrage.
     *
     * Ce que ça NE retire PAS à la séquence : elle reste indispensable, parce
     * qu'elle est la seule chose qui rende l'adresse DÉTERMINISTE. Sans elle,
     * l'adresse dépend d'un niveau qu'on ne contrôle pas.
     *
     * ⚠️ CONSÉQUENCE MÉTHODOLOGIQUE : ce probe-ci n'est pas un témoin négatif sur
     *    cette carte. Le témoin qui prouve la causalité est ailleurs — c'est
     *    `touch addr`, qui fait varier INT et regarde l'adresse suivre.
     */
    uint8_t trouve_avant = 0;
    s_probe_avant = probe_deux_adresses(bus, &trouve_avant);
    if (trouve_avant) {
        ESP_LOGW(TAG,
                 "probe AVANT reset : il répond DÉJÀ à 0x%02X — TP_RST n'est donc "
                 "pas maintenu bas par l'expander en entrée (la story attendait "
                 "l'inverse). La séquence reste utile : elle rend l'adresse "
                 "DÉTERMINISTE.",
                 trouve_avant);
    } else {
        ESP_LOGI(TAG,
                 "probe AVANT reset : %s — muet, comme attendu d'un contrôleur "
                 "encore en reset",
                 esp_err_to_name(s_probe_avant));
    }
    s_addr_avant = trouve_avant;

    /*
     * ── LA SÉQUENCE, ET LE SEUL FAIT QUI COMPTE DEDANS ───────────────────────
     * Le GT911 échantillonne INT au RELÂCHEMENT de RST. On tient donc INT en
     * sortie BASSE pendant TOUT le reset, et on ne le relâche qu'après.
     * INT bas au relâchement => adresse 0x5D.
     */
    gpio_config_t int_out = {
        .mode = GPIO_MODE_OUTPUT,
        .intr_type = GPIO_INTR_DISABLE,
        .pin_bit_mask = BIT64(DN_PIN_TP_INT),
    };
    ESP_RETURN_ON_ERROR(gpio_config(&int_out), TAG, "TP_INT en sortie refusé");
    ESP_RETURN_ON_ERROR(gpio_set_level(DN_PIN_TP_INT, 0), TAG, "TP_INT bas refusé");
    vTaskDelay(pdMS_TO_TICKS(DN_TP_INT_LOW_MS));

    esp_err_t err = dn_display_tp_reset(s_rst_bas_ms, s_rst_haut_ms);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "séquence de reset refusée : %s", esp_err_to_name(err));
        return err;
    }

    /* INT relâché en ENTRÉE : l'adresse est latchée, la broche redevient une
     * sortie du GT911. La laisser en sortie ici mettrait deux drivers face à
     * face sur le même fil. */
    gpio_config_t int_in = {
        .mode = GPIO_MODE_INPUT,
        .intr_type = GPIO_INTR_DISABLE,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .pin_bit_mask = BIT64(DN_PIN_TP_INT),
    };
    ESP_RETURN_ON_ERROR(gpio_config(&int_in), TAG, "TP_INT en entrée refusé");

    uint8_t trouve = 0;
    s_probe_apres = probe_deux_adresses(bus, &trouve);
    s_addr = trouve;
    ESP_LOGI(TAG, "probe APRÈS reset : %s — adresse RÉELLE 0x%02X (visée 0x%02X)",
             esp_err_to_name(s_probe_apres), s_addr, s_addr_visee);
    if (s_addr && s_addr != s_addr_visee) {
        ESP_LOGW(TAG,
                 "⚠️ il répond à l'adresse de REPLI : INT n'était pas bas au "
                 "relâchement de TP_RST (fil absent, pull-up qui gagne, ou "
                 "GPIO%d n'est pas TP_INT)",
                 DN_PIN_TP_INT);
    }
    ESP_RETURN_ON_FALSE(s_addr, s_probe_apres, TAG,
                        "GT911 muet aux DEUX adresses après la séquence");

    /* ── Le bus du composant, sur le maître EXISTANT ─────────────────────── */
    esp_lcd_panel_io_i2c_config_t io_cfg = ESP_LCD_TOUCH_IO_I2C_GT911_CONFIG();
    io_cfg.dev_addr = s_addr; /* l'adresse MESURÉE, pas celle du gabarit */
    /*
     * Le gabarit du composant pose 100 kHz. On demande les 400 kHz du reste du
     * bus : la lecture tactile est dans le chemin de la latence d'AC5, et une
     * transaction de ~10 octets passe de ~250 µs à ~65 µs. Le TCA9554 tourne
     * déjà à 400 kHz sur ce même bus depuis P1 sans un seul NACK — ce n'est donc
     * pas un pari. Si le GT911 devait broncher, le symptôme serait des
     * `err_i2c` non nuls dans `touch`, et le repli est cette ligne.
     */
    io_cfg.scl_speed_hz = DN_I2C_FREQ_HZ;
    ESP_RETURN_ON_ERROR(esp_lcd_new_panel_io_i2c_v2(bus, &io_cfg, &s_io), TAG,
                        "bus I2C du GT911 refusé");

    /* ── La config du contrôleur, LUE avant de créer le driver ──────────── */
    /* Elle est lue ici et pas après, parce que le mode de déclenchement de l'INT
     * (0x804D) détermine le front sur lequel l'ISR doit s'armer — et ce front-là
     * est un champ de la config qu'on s'apprête à passer au driver. Le déduire
     * après coup obligerait à recréer le driver. */
    gt911_lire_config();
    if (s_cfg.lue) {
        ESP_LOGI(TAG,
                 "GT911 « %s » fw 0x%04X · config v%u · résolution native "
                 "%ux%u · %u points · INT sur %s",
                 s_cfg.product_id, s_cfg.fw_version, s_cfg.cfg_version,
                 s_cfg.x_res, s_cfg.y_res, s_cfg.touch_max,
                 trig_name(s_cfg.trig_mode));
        if (s_cfg.x_res != DN_LCD_H_RES || s_cfg.y_res != DN_LCD_V_RES) {
            ESP_LOGW(TAG,
                     "⚠️ la résolution CONFIGURÉE dans le GT911 (%ux%u) diffère "
                     "de la dalle (%dx%d) — les coordonnées brutes sont dans SON "
                     "repère, pas dans celui de l'écran. C'est ce que la campagne "
                     "des 4 coins doit trancher.",
                     s_cfg.x_res, s_cfg.y_res, DN_LCD_H_RES, DN_LCD_V_RES);
        }
    }

    /* ── Le driver ──────────────────────────────────────────────────────── */
    esp_lcd_touch_config_t tp_cfg = {
        /*
         * x_max/y_max sont l'AXE DE SYMÉTRIE des miroirs, pas une mise à
         * l'échelle : `esp_lcd_touch` calcule `x = x_max - x`. On y pose la
         * géométrie de la DALLE (480x640 portrait) et non les 640x480 inversés
         * de la démo Waveshare — elle embarque un fork local du driver et LVGL
         * 8.2, sa valeur ne se transpose pas. Ce que rapportent réellement les
         * quatre coins est le sujet d'AC2.
         */
        .x_max = DN_LCD_H_RES,
        .y_max = DN_LCD_V_RES,
        .rst_gpio_num = GPIO_NUM_NC, /* TP_RST est derrière l'expander */
        .int_gpio_num = DN_PIN_TP_INT,
        .levels = {
            .reset = 0,
            /*
             * Niveau ACTIF de l'INT, tel que le GT911 le DÉCLARE dans sa propre
             * config — pas tel qu'on l'espère. Le driver en déduit POSEDGE ou
             * NEGEDGE (esp_lcd_touch_gt911.c:155). Se tromper ici donne
             * exactement le défaut interdit : une ISR armée sur le front que la
             * dalle ne produit jamais, donc un mode EVENT muet en silence.
             * Repli quand la config n'a pas pu être lue : front descendant,
             * qui est le comportement le plus répandu des GT9xx.
             */
            .interrupt = s_cfg.lue ? ((s_cfg.trig_mode == 0 || s_cfg.trig_mode == 3) ? 1 : 0) : 0,
        },
        .flags = {
            /* Tous à zéro AU DÉPART : la campagne des 4 coins doit voir ce que
             * la dalle rapporte, pas ce qu'on lui a fait dire. `touch axes`
             * les pose ensuite, et le résultat retenu s'écrit ici. */
            .swap_xy = 0,
            .mirror_x = 0,
            .mirror_y = 0,
        },
        .process_coordinates = dn_touch_brut,
        .interrupt_callback = NULL, /* posé après lvgl_port_add_touch — voir dn_touch_isr */
    };
    esp_lcd_touch_io_gt911_config_t gt911_cfg = {.dev_addr = s_addr};
    tp_cfg.driver_data = &gt911_cfg;
    /*
     * ⚠️ `driver_data` n'est utile au composant que si rst ET int sont tous deux
     *    définis (esp_lcd_touch_gt911.c:108) — ce qui n'est PAS notre cas, rst
     *    valant NC. Il est passé quand même pour que le jour où quelqu'un
     *    rebranche un rst en GPIO, l'adresse suive. Aujourd'hui, c'est
     *    `io_cfg.dev_addr` qui décide, et lui seul.
     */

    err = esp_lcd_touch_new_i2c_gt911(s_io, &tp_cfg, &s_tp);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "création du GT911 refusée : %s", esp_err_to_name(err));
        return err;
    }
    ESP_LOGI(TAG, "GT911 prêt à 0x%02X — TP_INT=GPIO%d, TP_RST=expander bit1",
             s_addr, DN_PIN_TP_INT);
    return ESP_OK;
}

esp_err_t dn_touch_attach_lvgl(lv_display_t *disp)
{
    ESP_RETURN_ON_FALSE(s_tp, ESP_ERR_INVALID_STATE, TAG,
                        "pas de GT911 — dn_touch_init() a échoué");
    ESP_RETURN_ON_FALSE(disp, ESP_ERR_INVALID_ARG, TAG, "display NULL");

    lvgl_port_touch_cfg_t cfg = {
        .disp = disp,
        .handle = s_tp,
        /* scale à 0 => le portage met 1 : pas de mise à l'échelle. La dalle
         * tactile et la dalle d'affichage ont la même géométrie. */
        .scale = {.x = 0, .y = 0},
    };
    s_indev = lvgl_port_add_touch(&cfg);
    ESP_RETURN_ON_FALSE(s_indev, ESP_FAIL, TAG, "lvgl_port_add_touch");

    /* Notre lecture remplace la sienne — les deux raisons sont en tête de
     * dn_touch_read(). Tout le reste de l'indev (type, display, mode) est celui
     * du portage. */
    if (!lvgl_port_lock(1000)) {
        ESP_LOGE(TAG, "verrou LVGL non pris — l'indev garde la lecture du portage "
                      "(celle qui ABORT sur erreur I2C)");
        return ESP_ERR_TIMEOUT;
    }
    lv_indev_set_read_cb(s_indev, dn_touch_read);
    lvgl_port_unlock();

    /* Notre ISR remplace la sienne — voir dn_touch_isr. Après, jamais avant. */
    esp_err_t err = esp_lcd_touch_register_interrupt_callback(s_tp, dn_touch_isr);
    if (err != ESP_OK) {
        ESP_LOGW(TAG,
                 "⚠️ ISR tactile non enregistrée (%s) : le compteur d'IRQ restera "
                 "à ZÉRO, et un zéro sans instrument ne prouve RIEN sur l'INT",
                 esp_err_to_name(err));
    }

    esp_err_t m = dn_touch_set_mode(DN_TOUCH_MODE_DEFAUT);
    ESP_LOGI(TAG, "indev LVGL branché — mode « %s »%s",
             dn_touch_mode_name(s_mode),
             m == ESP_OK ? "" : " (bascule refusée)");
    return ESP_OK;
}

/* ── Accès ────────────────────────────────────────────────────────────────── */

bool dn_touch_ready(void) { return s_tp != NULL; }
esp_lcd_touch_handle_t dn_touch_handle(void) { return s_tp; }
uint8_t dn_touch_addr(void) { return s_addr; }
uint8_t dn_touch_addr_visee(void) { return s_addr_visee; }
uint8_t dn_touch_addr_avant(void) { return s_addr_avant; }
esp_err_t dn_touch_probe_avant(void) { return s_probe_avant; }
esp_err_t dn_touch_probe_apres(void) { return s_probe_apres; }

void dn_touch_get_cfg(dn_touch_cfg_t *out)
{
    if (out) {
        *out = s_cfg;
    }
}

void dn_touch_get_stats(dn_touch_stats_t *out)
{
    if (!out) {
        return;
    }
    out->irq = s_irq;
    out->lectures = s_lectures;
    out->appuis = s_appuis;
    out->relaches = s_relaches;
    out->x = s_x;
    out->y = s_y;
    out->brut_x = s_brut_x;
    out->brut_y = s_brut_y;
    out->appuye = s_appuye;
}

uint32_t dn_touch_err_i2c(void) { return s_err_i2c; }

void dn_touch_reset_stats(void)
{
    s_irq = 0;
    s_lectures = 0;
    s_appuis = 0;
    s_relaches = 0;
    s_err_i2c = 0;
}

dn_touch_mode_t dn_touch_get_mode(void) { return s_mode; }

esp_err_t dn_touch_set_mode(dn_touch_mode_t m)
{
    if (m >= DN_TOUCH_MODE_COUNT) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_indev) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!lvgl_port_lock(1000)) {
        return ESP_ERR_TIMEOUT;
    }
    /* L'ordre compte : `s_mode` est lu par l'ISR. On le pose AVANT de changer le
     * mode de l'indev en passant à EVENT (pour qu'un front arrivé entre les deux
     * réveille bien la tâche) et APRÈS en passant à POLL (pour ne pas laisser un
     * réveil orphelin sur un indev déjà en timer). */
    if (m == DN_TOUCH_MODE_EVENT) {
        s_mode = m;
        lv_indev_set_mode(s_indev, LV_INDEV_MODE_EVENT);
    } else {
        lv_indev_set_mode(s_indev, LV_INDEV_MODE_TIMER);
        s_mode = m;
    }
    lvgl_port_unlock();
    return ESP_OK;
}

esp_err_t dn_touch_set_axes(bool swap_xy, bool mirror_x, bool mirror_y)
{
    ESP_RETURN_ON_FALSE(s_tp, ESP_ERR_INVALID_STATE, TAG, "pas de GT911");
    ESP_RETURN_ON_ERROR(esp_lcd_touch_set_swap_xy(s_tp, swap_xy), TAG, "swap_xy");
    ESP_RETURN_ON_ERROR(esp_lcd_touch_set_mirror_x(s_tp, mirror_x), TAG, "mirror_x");
    ESP_RETURN_ON_ERROR(esp_lcd_touch_set_mirror_y(s_tp, mirror_y), TAG, "mirror_y");
    return ESP_OK;
}

void dn_touch_get_axes(bool *swap_xy, bool *mirror_x, bool *mirror_y)
{
    bool s = false, mx = false, my = false;
    if (s_tp) {
        esp_lcd_touch_get_swap_xy(s_tp, &s);
        esp_lcd_touch_get_mirror_x(s_tp, &mx);
        esp_lcd_touch_get_mirror_y(s_tp, &my);
    }
    if (swap_xy) {
        *swap_xy = s;
    }
    if (mirror_x) {
        *mirror_x = mx;
    }
    if (mirror_y) {
        *mirror_y = my;
    }
}

void dn_touch_drain(void)
{
    if (!s_tp) {
        return;
    }
    /* Une lecture jetée : elle vide le registre de points du GT911 (le driver
     * réécrit 0 dans 0x814E après chaque lecture) et remet notre état d'appui à
     * plat. Sans ça, un doigt posé pendant `ui off` produirait un
     * appui->relâchement au retour, donc un CLIC que personne n'a voulu. */
    esp_lcd_touch_read_data(s_tp);
    s_appuye = false;
}

/* ── Latence ──────────────────────────────────────────────────────────────── */

void dn_touch_latence_arm(int64_t t0_us)
{
    s_lat_t0 = t0_us > 0 ? t0_us : esp_timer_get_time();
    s_lat_armee = true;
}

void dn_touch_latence_stop(void)
{
    if (!s_lat_armee) {
        return;
    }
    s_lat_armee = false;
    int64_t dt = esp_timer_get_time() - s_lat_t0;
    if (dt < 0) {
        return;
    }
    uint32_t us = (uint32_t)dt;
    s_lat_dernier_us = us;
    s_lat_total_us += us;
    s_lat_n++;
    if (us < s_lat_min_us) {
        s_lat_min_us = us;
    }
    if (us > s_lat_max_us) {
        s_lat_max_us = us;
    }
}

void dn_touch_get_latence(dn_touch_latence_t *out)
{
    if (!out) {
        return;
    }
    out->n = s_lat_n;
    out->min_us = s_lat_n ? s_lat_min_us : 0;
    out->max_us = s_lat_max_us;
    out->total_us = s_lat_total_us;
    out->dernier_us = s_lat_dernier_us;
}

void dn_touch_reset_latence(void)
{
    s_lat_n = 0;
    s_lat_min_us = UINT32_MAX;
    s_lat_max_us = 0;
    s_lat_total_us = 0;
    s_lat_dernier_us = 0;
    s_lat_armee = false;
}

/* ── L'essai d'adresse : la preuve causale de TP_INT ──────────────────────── */

esp_err_t dn_touch_essai_adresse(bool int_haut, uint8_t *trouvee)
{
    i2c_master_bus_handle_t bus = dn_display_i2c_bus();
    ESP_RETURN_ON_FALSE(bus, ESP_ERR_INVALID_STATE, TAG, "bus I2C absent");
    if (trouvee) {
        *trouvee = 0;
    }

    /*
     * L'ISR est retirée AVANT de reconfigurer la broche en sortie. Sans ça,
     * `gpio_config()` désarmerait l'interruption dans le dos du driver, qui
     * continuerait de croire son ISR active : le compteur d'IRQ resterait à zéro
     * après l'essai, et on conclurait « l'INT ne bat pas » sur un instrument
     * qu'on a soi-même débranché.
     */
    bool avait_isr = (s_tp != NULL);
    if (avait_isr) {
        esp_lcd_touch_register_interrupt_callback(s_tp, NULL);
    }

    gpio_config_t out = {
        .mode = GPIO_MODE_OUTPUT,
        .intr_type = GPIO_INTR_DISABLE,
        .pin_bit_mask = BIT64(DN_PIN_TP_INT),
    };
    esp_err_t err = gpio_config(&out);
    if (err == ESP_OK) {
        err = gpio_set_level(DN_PIN_TP_INT, int_haut ? 1 : 0);
    }
    if (err == ESP_OK) {
        vTaskDelay(pdMS_TO_TICKS(DN_TP_INT_LOW_MS));
        err = dn_display_tp_reset(s_rst_bas_ms, s_rst_haut_ms);
    }

    gpio_config_t in = {
        .mode = GPIO_MODE_INPUT,
        .intr_type = GPIO_INTR_DISABLE,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .pin_bit_mask = BIT64(DN_PIN_TP_INT),
    };
    gpio_config(&in);

    uint8_t vue = 0;
    esp_err_t probe = probe_deux_adresses(bus, &vue);
    if (trouvee) {
        *trouvee = vue;
    }

    /* L'ISR revient, et avec elle le mode de trigger que le driver avait posé
     * (`gpio_config` du composant, refait par le register). */
    if (avait_isr) {
        gpio_config_t re = {
            .mode = GPIO_MODE_INPUT,
            .intr_type = s_tp->config.levels.interrupt ? GPIO_INTR_POSEDGE
                                                       : GPIO_INTR_NEGEDGE,
            .pin_bit_mask = BIT64(DN_PIN_TP_INT),
        };
        gpio_config(&re);
        esp_lcd_touch_register_interrupt_callback(s_tp, dn_touch_isr);
    }
    /* Le contrôleur sort de reset avec ses registres à plat : on jette une
     * lecture pour que l'état d'appui local ne reste pas collé. */
    dn_touch_drain();

    return err != ESP_OK ? err : probe;
}

esp_err_t dn_touch_set_delais(int bas_ms, int haut_ms)
{
    if (bas_ms < 1 || bas_ms > 2000 || haut_ms < 1 || haut_ms > 2000) {
        return ESP_ERR_INVALID_ARG;
    }
    s_rst_bas_ms = bas_ms;
    s_rst_haut_ms = haut_ms;
    return ESP_OK;
}

void dn_touch_get_delais(int *bas_ms, int *haut_ms)
{
    if (bas_ms) {
        *bas_ms = s_rst_bas_ms;
    }
    if (haut_ms) {
        *haut_ms = s_rst_haut_ms;
    }
}

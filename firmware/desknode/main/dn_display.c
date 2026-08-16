#include "dn_display.h"

#include "sdkconfig.h" /* CONFIG_LCD_RGB_RESTART_IN_VSYNC, lu par dn_display_restart() */

#include "dn_measure.h"
#include "dn_pins.h"
#include "dn_recal.h"
#include "dn_st7701_init.h"
#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "driver/ledc.h"
#include "esp_check.h"
#include "esp_io_expander_tca9554.h"
#include "esp_lcd_panel_io_additions.h"
#include "esp_lcd_panel_rgb.h"
#include "esp_lcd_panel_vendor.h"
#include "esp_lcd_st7701.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "dn_disp";

/*
 * Faut-il envoyer un SWRESET (esp_lcd_panel_reset) avant l'init ?
 *
 * LCD_RST étant derrière l'expander, le driver ne peut pas faire le reset
 * MATÉRIEL lui-même (il ne sait piloter qu'un GPIO). On le fait donc à la main
 * en amont, et `esp_lcd_panel_reset()` retombe alors sur le SWRESET logiciel
 * (0x01) via le bus 3-wire.
 *
 * On le garde à 1 : c'est ce que fait l'exemple officiel, et la séquence
 * vendeur repart de toute façon d'une sélection Command2 complète. Si la dalle
 * devait rester noire à cause de lui, basculer à 0 ET NOTER LE SYMPTÔME (AC8) —
 * une élimination sans symptôme n'est pas une élimination.
 */
#define DN_SEND_SWRESET 1

static i2c_master_bus_handle_t s_i2c;
static esp_io_expander_handle_t s_expander;
static esp_lcd_panel_io_handle_t s_panel_io;
static esp_lcd_panel_handle_t s_panel;

static uint16_t *s_fbs[3];
static int s_num_fbs;
static size_t s_bounce_px;
static int s_draw_index; /* index du framebuffer où l'on dessine */
static int s_backlight_pct = -1; /* -1 = LEDC pas encore monté */
static int s_backlight_freq;
static bool s_disp_on;

/*
 * ── Rétroéclairage LEDC (dn1-3, AC7) ─────────────────────────────────────────
 *
 * Les quatre valeurs ci-dessous viennent du pattern de référence d'Espressif
 * (`esp_bsp_generic.c`), et chacune a une raison qu'on ne veut pas redécouvrir :
 *
 *   LOW_SPEED_MODE : sur ESP32-S3 il n'y a QUE le mode basse vitesse (pas de
 *       high-speed comme sur l'ESP32 d'origine). Écrire HIGH_SPEED_MODE ne
 *       compilerait même pas ici.
 *   10 bits        : 1 024 crans. Assez fin pour que la rampe d'AC7 n'ait pas de
 *       palier visible, et assez grossier pour tenir à 5 kHz — le produit
 *       (2^bits x freq) est plafonné par l'horloge de la source LEDC.
 *   5 kHz          : au-dessus de ~200 Hz l'œil ne voit plus le papillotement ;
 *       5 kHz est le standard de facto et met le sifflement éventuel de la
 *       bobine du boost au-dessus de la plage la plus sensible de l'oreille.
 *       ⚠️ « Inaudible » est une PRÉDICTION, pas une mesure : AC7 demande
 *          explicitement de tendre l'oreille à duty bas.
 *   AUTO_CLK       : laisse le driver choisir une source qui atteint le couple
 *       (fréquence, résolution) demandé ; un choix figé échouerait si l'horloge
 *       change (DFS, sommeil léger).
 */
#define DN_BL_LEDC_MODE LEDC_LOW_SPEED_MODE
#define DN_BL_LEDC_TIMER LEDC_TIMER_0
#define DN_BL_LEDC_CHANNEL LEDC_CHANNEL_0
#define DN_BL_LEDC_RES LEDC_TIMER_10_BIT
/*
 * ⚠️ 24 kHz, ET C'EST UN RENVERSEMENT DU PATTERN DE RÉFÉRENCE.
 *
 * `esp_bsp_generic.c` d'Espressif pose 5 kHz, et notre première version l'a
 * repris tel quel en écrivant « sifflement inaudible en pratique ». MESURÉ FAUX
 * SUR CETTE CARTE le 2026-08-15 : à 3 % de duty, l'owner ENTEND distinctement
 * un sifflement, oreille approchée. La phrase venait d'un BSP générique, pas de
 * ce matériel — c'était une prédiction déguisée en acquis.
 *
 * A/B joué à luminosité STRICTEMENT constante (3 %), une seule variable, avec
 * `ledc_set_freq` qui reprogramme le diviseur sans toucher au duty :
 *      5 000 Hz -> sifflement AUDIBLE
 *     24 000 Hz -> plus rien à l'oreille
 * 24 kHz est au-dessus de la limite haute de l'audition adulte (~18 kHz) et
 * laisse de la marge sous le plafond du couple (fréquence x 1 024 crans).
 *
 * ⚠️ CE QUE CE CHANGEMENT NE CORRIGE PAS, et qu'il ne faut pas lui attribuer :
 *    le PAPILLOTEMENT vu à 3 % subsiste à 24 kHz. Témoin : LVGL mis en pause à
 *    luminosité identique, l'image est parfaitement stable. Ce papillotement-là
 *    n'est donc PAS un défaut du rétroéclairage — c'est l'artefact de redessin
 *    LVGL documenté en tête de dn_ui.c, que la basse luminosité rend seulement
 *    plus visible.
 */
#define DN_BL_LEDC_FREQ_HZ 24000
#define DN_BL_FREQ_MIN 200   /* en dessous, l'œil voit le papillotement */
#define DN_BL_FREQ_MAX 40000 /* 40 kHz x 1024 crans = 40,96 MHz, tenable sur APB 80 MHz */
#define DN_BL_DUTY_MAX ((1u << 10) - 1u) /* 1023 */

/* ────────────────────────────────────────────────────────────────────────── */

static esp_err_t i2c_bring_up(void)
{
    i2c_master_bus_config_t bus_cfg = {
        .i2c_port = DN_I2C_PORT,
        .sda_io_num = DN_PIN_I2C_SDA,
        .scl_io_num = DN_PIN_I2C_SCL,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    ESP_RETURN_ON_ERROR(i2c_new_master_bus(&bus_cfg, &s_i2c), TAG,
                        "bus I2C (SDA=%d SCL=%d) refusé", DN_PIN_I2C_SDA,
                        DN_PIN_I2C_SCL);
    /*
     * ⚠️ ÉTIQUETTE CORRIGÉE (dn1-4). Cette ligne annonçait « @ 400000 Hz »
     *    comme si le BUS portait une fréquence. En API `i2c_master` d'IDF 5.x,
     *    `i2c_master_bus_config_t` n'a AUCUN champ d'horloge : la fréquence se
     *    pose PAR DEVICE, dans `i2c_master_dev_config_t.scl_speed_hz`, et deux
     *    devices du même bus peuvent tourner à deux vitesses différentes.
     *    L'ancienne ligne était donc une étiquette non tenue par ce qu'elle
     *    décrit — exactement la classe de défaut que ce firmware traque.
     *
     *    Ce que le bus porte réellement : les broches, la source d'horloge, le
     *    filtre de glitch et les tirages internes. Les 400 kHz sont posés par
     *    chaque device : le TCA9554 le fait dans son propre driver
     *    (esp_io_expander_tca9554.c:18, I2C_CLK_SPEED = 400000 — lu dans le
     *    source, pas supposé) et dn_touch le fait pour le GT911 avec
     *    DN_I2C_FREQ_HZ.
     */
    ESP_LOGI(TAG,
             "bus I2C monté : SDA=GPIO%d SCL=GPIO%d, tirages internes ON — "
             "l'horloge est posée PAR DEVICE (%d Hz visés), pas par le bus",
             DN_PIN_I2C_SDA, DN_PIN_I2C_SCL, DN_I2C_FREQ_HZ);
    return ESP_OK;
}

i2c_master_bus_handle_t dn_display_i2c_bus(void) { return s_i2c; }
esp_err_t dn_display_tp_reset(int bas_ms, int haut_ms)
{
    ESP_RETURN_ON_FALSE(s_expander, ESP_ERR_INVALID_STATE, TAG,
                        "expander absent — dn_display_init() n'a pas tourné");
    ESP_RETURN_ON_FALSE(bas_ms > 0 && bas_ms <= 2000 && haut_ms > 0 &&
                            haut_ms <= 2000,
                        ESP_ERR_INVALID_ARG, TAG,
                        "délais hors bornes (1..2000 ms) : %d/%d", bas_ms,
                        haut_ms);

    /*
     * TP_RST passe en SORTIE ICI, et c'est le changement d'état stationnaire que
     * dn1-2 avait annoncé (« dn1-4 part d'un TP_RST non piloté, pas d'un TP_RST
     * haut »). Avant cet appel il est en ENTRÉE haute impédance, tel que le
     * TCA9554 le laisse à sa mise sous tension.
     *
     * ⚠️ `esp_io_expander_set_dir` sur le SEUL bit 1 : le masque ne contient pas
     *    LCD_RST (bit 0). Un masque trop large remettrait la dalle en reset, et
     *    le symptôme serait un écran gris sans le moindre message — la panne la
     *    plus coûteuse de dn1-2.
     */
    ESP_RETURN_ON_ERROR(esp_io_expander_set_dir(s_expander, DN_EXIO_TP_RST,
                                                IO_EXPANDER_OUTPUT),
                        TAG, "TP_RST en sortie refusé");
    ESP_RETURN_ON_ERROR(esp_io_expander_set_level(s_expander, DN_EXIO_TP_RST, 0),
                        TAG, "TP_RST bas refusé");
    vTaskDelay(pdMS_TO_TICKS(bas_ms));
    ESP_RETURN_ON_ERROR(esp_io_expander_set_level(s_expander, DN_EXIO_TP_RST, 1),
                        TAG, "TP_RST haut refusé");
    vTaskDelay(pdMS_TO_TICKS(haut_ms));
    ESP_LOGI(TAG,
             "reset tactile joué via l'expander bit1/EXIO2 (%d ms bas, %d ms de "
             "repos) — TP_RST reste désormais en SORTIE HAUTE",
             bas_ms, haut_ms);
    return ESP_OK;
}

static esp_err_t expander_bring_up(void)
{
    /* Sonde ciblée : on vérifie que 0x20 répond AVANT de créer le driver.
     * Sinon un échec plus loin (écran noir) laisserait planer le doute sur la
     * dalle alors que c'est l'expander qui manque. Ce n'est PAS un scan de bus :
     * une seule adresse est interrogée, celle qu'on attend. */
    esp_err_t probe = i2c_master_probe(s_i2c, DN_TCA9554_ADDR, 100);
    ESP_LOGI(TAG, "sonde I2C 0x%02X (TCA9554) : %s", DN_TCA9554_ADDR,
             probe == ESP_OK ? "répond" : esp_err_to_name(probe));
    ESP_RETURN_ON_ERROR(probe, TAG, "TCA9554 muet à 0x%02X", DN_TCA9554_ADDR);

    ESP_RETURN_ON_ERROR(
        esp_io_expander_new_i2c_tca9554(s_i2c, DN_TCA9554_ADDR, &s_expander),
        TAG, "création du TCA9554 refusée");

    /* Les deux broches qui nous concernent, en SORTIE. */
    ESP_RETURN_ON_ERROR(esp_io_expander_set_dir(s_expander,
                                                DN_EXIO_LCD_RST | DN_EXIO_LCD_CS,
                                                IO_EXPANDER_OUTPUT),
                        TAG, "direction LCD_RST/LCD_CS refusée");
    /* CS au repos = haut. */
    ESP_RETURN_ON_ERROR(esp_io_expander_set_level(s_expander, DN_EXIO_LCD_CS, 1),
                        TAG, "CS haut refusé");

    /* ⚠️ TP_RST (bit 1) : ce module le laisse DÉLIBÉRÉMENT dans son état de mise
     * sous tension du TCA9554, c'est-à-dire en ENTRÉE haute impédance. C'était un
     * livrable de P1, et ça le reste : le niveau qui compte pour le GT911 est
     * celui du RELÂCHEMENT du reset, en même temps qu'INT — donc la séquence
     * appartient à celui qui tient INT.
     * dn1-4 la joue via `dn_display_tp_reset()` (plus bas dans ce fichier), après
     * le boot de l'affichage : à partir de là TP_RST est en SORTIE HAUTE, et
     * c'est le nouvel état stationnaire. Ici, rien ne change. */
    ESP_LOGI(TAG,
             "TCA9554 prêt : LCD_RST=bit0 et LCD_CS=bit2 en SORTIE ; "
             "TP_RST=bit1 laissé en ENTRÉE (état de reset de l'expander) — "
             "dn_touch le prendra en main");
    return ESP_OK;
}

static esp_err_t panel_hw_reset(void)
{
    /* Reset MATÉRIEL de la dalle, via l'expander : le driver ne sait pas le
     * faire (il n'attaque qu'un GPIO), donc c'est à nous. */
    ESP_RETURN_ON_ERROR(esp_io_expander_set_level(s_expander, DN_EXIO_LCD_RST, 0),
                        TAG, "LCD_RST bas refusé");
    vTaskDelay(pdMS_TO_TICKS(20));
    ESP_RETURN_ON_ERROR(esp_io_expander_set_level(s_expander, DN_EXIO_LCD_RST, 1),
                        TAG, "LCD_RST haut refusé");
    vTaskDelay(pdMS_TO_TICKS(150));
    ESP_LOGI(TAG, "reset matériel de la dalle joué via l'expander (20 ms bas, 150 ms de repos)");
    return ESP_OK;
}

static esp_err_t spi3wire_bring_up(void)
{
    spi_line_config_t line = {
        .cs_io_type = IO_TYPE_EXPANDER,
        .cs_expander_pin = DN_EXIO_LCD_CS,
        .scl_io_type = IO_TYPE_GPIO,
        .scl_gpio_num = DN_PIN_LCD_SCL,
        .sda_io_type = IO_TYPE_GPIO,
        .sda_gpio_num = DN_PIN_LCD_SDA,
        .io_expander = s_expander,
    };
    esp_lcd_panel_io_3wire_spi_config_t io_cfg =
        ST7701_PANEL_IO_3WIRE_SPI_CONFIG(line, 0);

    /* ⚠️ CORRECTION D'UNE HYPOTHÈSE DE LA STORY : le tableau de brochage
     * annonçait « 3-wire SPI, data_rate 80 MHz bit-bangé », repris du champ
     * `data_rate: 80MHz` du YAML ESPHome. Ce champ-là décrit le bus RGB, pas
     * celui-ci. Le bus d'initialisation est bit-bangé PAR LOGICIEL et le
     * composant le plafonne à PANEL_IO_3WIRE_SPI_CLK_MAX = 500 kHz
     * (esp_lcd_panel_io_additions.h). 80 MHz n'y a jamais été atteignable. */
    ESP_RETURN_ON_ERROR(esp_lcd_new_panel_io_3wire_spi(&io_cfg, &s_panel_io), TAG,
                        "bus 3-wire SPI refusé");
    ESP_LOGI(TAG,
             "3-wire SPI : SDA=GPIO%d SCL=GPIO%d, CS via expander bit2, "
             "horloge visée %lu Hz (plafond logiciel du composant)",
             DN_PIN_LCD_SDA, DN_PIN_LCD_SCL,
             (unsigned long)PANEL_IO_3WIRE_SPI_CLK_MAX);
    return ESP_OK;
}

static esp_err_t panel_bring_up(const dn_bootcfg_t *cfg)
{
    const int data_gpios[] = DN_RGB_DATA_GPIOS;

    esp_lcd_rgb_panel_config_t rgb_cfg = {
        .clk_src = LCD_CLK_SRC_DEFAULT,
        .timings =
            {
                .pclk_hz = DN_PCLK_HZ,
                .h_res = DN_LCD_H_RES,
                .v_res = DN_LCD_V_RES,
                .hsync_pulse_width = DN_HSYNC_PULSE,
                .hsync_back_porch = DN_HSYNC_BACK_PORCH,
                .hsync_front_porch = DN_HSYNC_FRONT_PORCH,
                .vsync_pulse_width = DN_VSYNC_PULSE,
                .vsync_back_porch = DN_VSYNC_BACK_PORCH,
                .vsync_front_porch = DN_VSYNC_FRONT_PORCH,
                .flags.pclk_active_neg = false,
            },
        .data_width = 16,
        .bits_per_pixel = 16,
        .num_fbs = cfg->num_fbs,
        .bounce_buffer_size_px = (size_t)cfg->bounce_px,
        .dma_burst_size = 64,
        .hsync_gpio_num = DN_PIN_HSYNC,
        .vsync_gpio_num = DN_PIN_VSYNC,
        .de_gpio_num = DN_PIN_DE,
        .pclk_gpio_num = DN_PIN_PCLK,
        .disp_gpio_num = -1,
        .flags.fb_in_psram = 1,
    };
    for (int i = 0; i < 16; i++) {
        rgb_cfg.data_gpio_nums[i] = data_gpios[i];
    }

    st7701_vendor_config_t vendor_cfg = {
        .init_cmds = dn_st7701_vendor_init,
        .init_cmds_size = DN_ST7701_VENDOR_INIT_LEN,
        .rgb_config = &rgb_cfg,
        .flags =
            {
                .mirror_by_cmd = 0,
                /* 0 : les broches du 3-wire SPI (GPIO1/2) ne sont PAS partagées
                 * avec le bus RGB, donc rien n'oblige à détruire le bus après
                 * l'init. Le garder vivant permet d'y renvoyer une commande
                 * pour diagnostiquer. */
                .enable_io_multiplex = 0,
            },
    };

    esp_lcd_panel_dev_config_t dev_cfg = {
        /* -1 : le reset est MATÉRIEL et passe par l'expander (fait plus haut),
         * pas par un GPIO que le driver saurait piloter. */
        .reset_gpio_num = -1,
        .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB,
        .bits_per_pixel = 16,
        .vendor_config = &vendor_cfg,
    };

    size_t psram_avant = dn_measure_psram_free();
    ESP_RETURN_ON_ERROR(esp_lcd_new_panel_st7701(s_panel_io, &dev_cfg, &s_panel),
                        TAG, "création du panneau ST7701 refusée");

#if DN_SEND_SWRESET
    ESP_RETURN_ON_ERROR(esp_lcd_panel_reset(s_panel), TAG, "reset du panneau refusé");
#endif
    ESP_RETURN_ON_ERROR(esp_lcd_panel_init(s_panel), TAG,
                        "init du panneau refusée (%u commandes vendeur)",
                        (unsigned)DN_ST7701_VENDOR_INIT_LEN);

    /*
     * ⚠️ LE DÉFAUT QUI A COÛTÉ LE PREMIER ALLUMAGE — à ne jamais réintroduire.
     *
     * SYMPTÔME OBSERVÉ : dalle nettement rétroéclairée, UNIFORMÉMENT GRISE,
     * aucune image ; et pourtant le compteur vsync tournait à 37,40 Hz exacts,
     * l'expander répondait en I2C, et aucune fonction ne renvoyait d'erreur.
     * Autrement dit : tous les voyants au vert, écran vide.
     *
     * CAUSE : la séquence vendeur reprise du YAML ESPHome s'arrête à 0x35
     * (TEON) et NE CONTIENT PAS 0x29 (DISPON) — ESPHome envoie DISPON de son
     * côté, hors de la clé `init_sequence`. Or `esp_lcd_panel_init()` ne
     * l'envoie pas non plus : dans esp_lcd_st7701, DISPON est la DERNIÈRE
     * entrée du jeu d'init PAR DÉFAUT (esp_lcd_st7701_rgb.c:199) — celui-là
     * même qu'on remplace. En fournissant `init_cmds`, on hérite donc du trou.
     *
     * PARADE : appeler explicitement disp_on_off. Comme disp_gpio_num vaut -1,
     * le driver le traduit en commande 0x29 sur le bus 3-wire.
     */
    ESP_RETURN_ON_ERROR(esp_lcd_panel_disp_on_off(s_panel, true), TAG,
                        "DISPON (0x29) refusé");
    s_disp_on = true;
    ESP_LOGI(TAG,
             "DISPON (0x29) envoyé explicitement — la séquence vendeur ne le "
             "contient pas, et esp_lcd_panel_init() non plus");

    size_t psram_apres = dn_measure_psram_free();

    s_num_fbs = cfg->num_fbs;
    s_bounce_px = (size_t)cfg->bounce_px;
    void *fb0 = NULL, *fb1 = NULL, *fb2 = NULL;
    esp_err_t err;
    if (s_num_fbs >= 3) {
        err = esp_lcd_rgb_panel_get_frame_buffer(s_panel, 3, &fb0, &fb1, &fb2);
    } else if (s_num_fbs == 2) {
        err = esp_lcd_rgb_panel_get_frame_buffer(s_panel, 2, &fb0, &fb1);
    } else {
        err = esp_lcd_rgb_panel_get_frame_buffer(s_panel, 1, &fb0);
    }
    ESP_RETURN_ON_ERROR(err, TAG, "récupération des framebuffers refusée");
    s_fbs[0] = (uint16_t *)fb0;
    s_fbs[1] = (uint16_t *)fb1;
    s_fbs[2] = (uint16_t *)fb2;
    /* On dessine dans le DERNIER framebuffer, donc dans le caché quand il y en
     * a plusieurs (le driver démarre sur l'index 0). */
    s_draw_index = s_num_fbs - 1;

    dn_measure_note_psram(psram_avant, psram_apres);
    ESP_LOGI(TAG,
             "panneau RGB prêt : %dx%d @ %d Hz pclk, num_fbs=%d, bounce=%u px",
             DN_LCD_H_RES, DN_LCD_V_RES, DN_PCLK_HZ, s_num_fbs,
             (unsigned)s_bounce_px);
    for (int i = 0; i < s_num_fbs; i++) {
        ESP_LOGI(TAG, "  fb[%d] @ %p", i, (void *)s_fbs[i]);
    }
    ESP_LOGI(TAG, "PSRAM libre : %u o avant les framebuffers, %u o après (delta %d o)",
             (unsigned)psram_avant, (unsigned)psram_apres,
             (int)((long)psram_avant - (long)psram_apres));
    return ESP_OK;
}

static esp_err_t backlight_bring_up(void)
{
    /*
     * ⚠️ ORDRE IMPOSÉ, et il n'est pas cosmétique : le timer AVANT le canal.
     *    `ledc_channel_config()` accroche le canal à un timer qui doit déjà
     *    exister ; l'inverse rend ESP_ERR_INVALID_ARG, et on chercherait un
     *    problème de brochage alors que c'est un ordre d'appel.
     *
     * ⚠️ Et surtout : `.duty = 0` DANS la config du canal, pas un
     *    `ledc_set_duty()` juste après. Entre les deux, la broche serait pilotée
     *    à une valeur non choisie pendant quelques microsecondes — assez pour un
     *    flash à l'allumage, et impossible à attribuer ensuite.
     */
    ledc_timer_config_t timer = {
        .speed_mode = DN_BL_LEDC_MODE,
        .timer_num = DN_BL_LEDC_TIMER,
        .duty_resolution = DN_BL_LEDC_RES,
        .freq_hz = DN_BL_LEDC_FREQ_HZ,
        .clk_cfg = LEDC_AUTO_CLK,
    };
    ESP_RETURN_ON_ERROR(ledc_timer_config(&timer), TAG,
                        "timer LEDC du rétroéclairage refusé (%d bits @ %d Hz)",
                        (int)DN_BL_LEDC_RES, DN_BL_LEDC_FREQ_HZ);

    ledc_channel_config_t chan = {
        .gpio_num = DN_PIN_BACKLIGHT,
        .speed_mode = DN_BL_LEDC_MODE,
        .channel = DN_BL_LEDC_CHANNEL,
        .intr_type = LEDC_INTR_DISABLE,
        .timer_sel = DN_BL_LEDC_TIMER,
        .duty = 0, /* ÉTEINT dès la première impulsion d'horloge */
        .hpoint = 0,
    };
    ESP_RETURN_ON_ERROR(ledc_channel_config(&chan), TAG,
                        "canal LEDC du rétroéclairage (GPIO%d) refusé",
                        DN_PIN_BACKLIGHT);
    s_backlight_pct = 0;
    s_backlight_freq = DN_BL_LEDC_FREQ_HZ;
    ESP_LOGI(TAG,
             "rétroéclairage en LEDC : GPIO%d, %d bits (%u crans) @ %d Hz "
             "(24 kHz et non les 5 kHz du BSP : mesuré, à 5 kHz la carte "
             "SIFFLE à duty bas), duty 0 — il ne montera qu'après le "
             "remplissage du framebuffer",
             DN_PIN_BACKLIGHT, 10, (unsigned)(DN_BL_DUTY_MAX + 1),
             DN_BL_LEDC_FREQ_HZ);
    return ESP_OK;
}

esp_err_t dn_display_init(const dn_bootcfg_t *cfg)
{
    /* Rétroéclairage : configuré ÉTEINT tout de suite, pour ne pas hériter de
     * l'état laissé par le firmware précédent. Il ne s'allumera qu'une fois le
     * framebuffer rempli. */
    ESP_RETURN_ON_ERROR(backlight_bring_up(), TAG, "étape 0/5");

    ESP_RETURN_ON_ERROR(i2c_bring_up(), TAG, "étape 1/5");
    ESP_RETURN_ON_ERROR(expander_bring_up(), TAG, "étape 2/5");
    ESP_RETURN_ON_ERROR(panel_hw_reset(), TAG, "étape 3/5");
    ESP_RETURN_ON_ERROR(spi3wire_bring_up(), TAG, "étape 4/5");
    ESP_RETURN_ON_ERROR(panel_bring_up(cfg), TAG, "étape 5/5");
    return ESP_OK;
}

esp_err_t dn_display_backlight_pct(int pct)
{
    if (s_backlight_pct < 0) {
        /* Appelé avant dn_display_init() : LEDC n'existe pas encore. On refuse
         * plutôt que de laisser le driver rendre une erreur obscure — et surtout
         * plutôt que de « réussir » sans rien piloter. */
        ESP_LOGE(TAG, "rétroéclairage : LEDC pas encore monté (dn_display_init "
                      "n'a pas été appelé)");
        return ESP_ERR_INVALID_STATE;
    }
    if (pct < 0 || pct > 100) {
        /* Leçon dn1-2 (`bl 1` éteignait, `set bounce 153600` briquait) : les
         * bornes se posent AVANT de toucher le matériel, et le refus se dit. */
        ESP_LOGE(TAG, "rétroéclairage : %d %% hors de [0, 100] — rien touché", pct);
        return ESP_ERR_INVALID_ARG;
    }

    /*
     * Arrondi au cran le plus proche, pas troncature : sans le +50, `bl 1`
     * donnerait duty = 10 (1 x 1023 / 100 = 10,23 tronqué) et `bl 100` donnerait
     * bien 1023, mais les valeurs intermédiaires perdraient systématiquement un
     * demi-cran. Sur 1 024 crans c'est invisible ; sur le PLANCHER que cherche
     * AC7 (« le duty minimal où la dalle reste lisible »), un cran compte.
     */
    uint32_t duty = ((uint32_t)pct * DN_BL_DUTY_MAX + 50u) / 100u;

    esp_err_t err = ledc_set_duty(DN_BL_LEDC_MODE, DN_BL_LEDC_CHANNEL, duty);
    if (err == ESP_OK) {
        err = ledc_update_duty(DN_BL_LEDC_MODE, DN_BL_LEDC_CHANNEL);
    }

    /* ⚠️ L'ÉTAT FANTÔME (leçon dn1-2, conservée telle quelle). L'ombre logicielle
     * ne suit le matériel qu'APRÈS confirmation. Une version qui posait l'état
     * AVANT l'appel annonçait une luminosité que la dalle n'avait pas prise, et
     * on allait chercher un écran noir du côté de la dalle. */
    if (err == ESP_OK) {
        s_backlight_pct = pct;
    } else {
        ESP_LOGE(TAG,
                 "rétroéclairage (GPIO%d -> %d %%, duty %u) refusé : %s — état "
                 "inchangé (%d %%)",
                 DN_PIN_BACKLIGHT, pct, (unsigned)duty, esp_err_to_name(err),
                 s_backlight_pct);
    }
    return err;
}

int dn_display_backlight_pct_state(void) { return s_backlight_pct; }

esp_err_t dn_display_backlight_freq(int hz)
{
    if (s_backlight_pct < 0) {
        return ESP_ERR_INVALID_STATE;
    }
    if (hz < DN_BL_FREQ_MIN || hz > DN_BL_FREQ_MAX) {
        ESP_LOGE(TAG, "fréquence %d Hz hors de [%d, %d] — rien touché", hz,
                 DN_BL_FREQ_MIN, DN_BL_FREQ_MAX);
        return ESP_ERR_INVALID_ARG;
    }
    /* `ledc_set_freq` reprogramme le diviseur du timer SANS toucher au duty du
     * canal : la luminosité ne saute pas pendant l'essai, et l'oreille compare
     * deux fréquences à luminosité CONSTANTE — une seule variable. */
    esp_err_t err = ledc_set_freq(DN_BL_LEDC_MODE, DN_BL_LEDC_TIMER, (uint32_t)hz);
    if (err == ESP_OK) {
        s_backlight_freq = hz;
    } else {
        ESP_LOGE(TAG,
                 "fréquence %d Hz refusée : %s — l'horloge de la source LEDC ne "
                 "tient pas le produit (fréquence x %u crans). État inchangé "
                 "(%d Hz).",
                 hz, esp_err_to_name(err), (unsigned)(DN_BL_DUTY_MAX + 1),
                 s_backlight_freq);
    }
    return err;
}

int dn_display_backlight_freq_state(void) { return s_backlight_freq; }

esp_err_t dn_display_backlight_ramp(int pct_cible, int duree_ms)
{
    if (s_backlight_pct < 0) {
        return ESP_ERR_INVALID_STATE;
    }
    if (pct_cible < 0 || pct_cible > 100) {
        return ESP_ERR_INVALID_ARG;
    }
    if (duree_ms < 0) {
        return ESP_ERR_INVALID_ARG;
    }

    int depart = s_backlight_pct;
    int delta = pct_cible - depart;
    if (delta == 0) {
        return ESP_OK;
    }
    int pas = delta > 0 ? delta : -delta; /* un cran de POURCENT par étape */

    /*
     * Cadence en TEMPS ABSOLU (`vTaskDelayUntil`), jamais en délai relatif : un
     * `vTaskDelay(x)` dans une boucle dérive de tout le temps passé à calculer,
     * et la rampe qu'on montre à l'œil durerait plus longtemps que ce que la
     * console annonce. C'est la règle de méthode héritée de dn1-1/dn1-2 (« la
     * cadence est absolue »), et elle vaut aussi pour un geste de démonstration.
     */
    /*
     * Le pas de temps est recalculé à CHAQUE étape sur la cible absolue
     * (duree_ms * i / pas), et non figé une fois par division entière (revue) :
     * `bl ramp 100 199` depuis 0 % donnait periode = 199/100 = 1 ms, soit une
     * rampe réelle de ~100 ms pour 199 annoncées — jusqu'à 2x plus courte, et
     * le constat AC7 encore dû se serait fait sous une étiquette de durée
     * fausse. Ici le reliquat est distribué : la somme des pas vaut duree_ms
     * à ±1 tick près.
     */
    TickType_t reveil = xTaskGetTickCount();
    TickType_t ecoule = 0;
    for (int i = 1; i <= pas; i++) {
        int pct = depart + (delta > 0 ? i : -i);
        esp_err_t err = dn_display_backlight_pct(pct);
        if (err != ESP_OK) {
            /* On s'arrête où on en est, et on le dit : une rampe interrompue à
             * mi-chemin qui rendrait ESP_OK laisserait croire à un défaut de la
             * dalle plutôt qu'à un refus du driver. */
            ESP_LOGE(TAG, "rampe interrompue à %d %% : %s", s_backlight_pct,
                     esp_err_to_name(err));
            return err;
        }
        TickType_t cible = pdMS_TO_TICKS(((int64_t)duree_ms * i) / pas);
        TickType_t periode = cible > ecoule ? cible - ecoule : 1;
        ecoule += periode;
        vTaskDelayUntil(&reveil, periode);
    }
    return ESP_OK;
}

esp_err_t dn_display_backlight(bool on)
{
    return dn_display_backlight_pct(on ? 100 : 0);
}

bool dn_display_backlight_state(void) { return s_backlight_pct > 0; }

esp_err_t dn_display_disp_on(bool on)
{
    esp_err_t err = esp_lcd_panel_disp_on_off(s_panel, on);
    if (err == ESP_OK) {
        s_disp_on = on;
    }
    return err;
}

bool dn_display_disp_state(void) { return s_disp_on; }

esp_lcd_panel_handle_t dn_display_panel(void) { return s_panel; }

int dn_display_num_fbs(void) { return s_num_fbs; }

size_t dn_display_bounce_px(void) { return s_bounce_px; }

uint16_t *dn_display_draw_buffer(void) { return s_fbs[s_draw_index]; }

int64_t dn_display_present(void)
{
    int64_t t0 = esp_timer_get_time();
    uint16_t *buf = s_fbs[s_draw_index];
    /* Le buffer EST l'un des framebuffers du driver : `draw_bitmap` bascule
     * l'index sans recopier, et synchronise le cache vers la PSRAM. */
    esp_err_t err =
        esp_lcd_panel_draw_bitmap(s_panel, 0, 0, DN_LCD_H_RES, DN_LCD_V_RES, buf);
    int64_t dt = esp_timer_get_time() - t0;

    if (err != ESP_OK) {
        /* ⚠️ NE JAMAIS AVANCER L'INDEX SUR UN ÉCHEC — le défaut que ce test
         * ferme. Le retour de draw_bitmap était jeté et l'index avançait quand
         * même. Conséquence, en silence : la dalle continuait d'afficher la
         * trame PRÉCÉDENTE pendant que le code croyait les buffers permutés,
         * donc tous les dessins suivants visaient le framebuffer VISIBLE.
         * Autrement dit, une configuration num_fbs=2 se transformait toute
         * seule en la configuration num_fbs=1 — celle qui sert précisément de
         * TÉMOIN POSITIF de déchirement (AC5). L'instrument serait devenu le
         * défaut, et le fps mesuré ensuite aurait porté une étiquette fausse.
         *
         * -1 plutôt que la durée : les appelants impriment ce retour comme une
         * MESURE (« présentation : %lld us »). Une durée négative est
         * impossible, donc reconnaissable au premier coup d'œil dans un log. */
        ESP_LOGE(TAG,
                 "draw_bitmap refusé : %s — index de dessin NON avancé, fb[%d] "
                 "reste le buffer de dessin et la dalle garde la trame "
                 "précédente",
                 esp_err_to_name(err), s_draw_index);
        return -1;
    }

    if (s_num_fbs > 1) {
        s_draw_index = (s_draw_index + 1) % s_num_fbs;
        /* La bascule a RÉUSSI : c'est l'événement — et le seul — sur lequel
         * AC5 veut accrocher le recalage de la DMA. Non bloquant : on réveille
         * une tâche, qui comptera les vsyncs et relancera. Jamais ici : ce
         * chemin-ci est appelé depuis la console ET depuis le boot, et il ne
         * doit pas attendre une trame. */
        dn_recal_arm();
    }
    return dt;
}

/*
 * ⚠️ CETTE FONCTION EST INERTE SOUS LA CONFIGURATION RETENUE — et elle le dit.
 *
 * `esp_lcd_rgb_panel_restart()` (esp_lcd_panel_rgb.c:464-475) ne fait qu'UNE
 * chose : poser `panel->flags.need_restart = true`. Ce bit n'est lu qu'à un
 * seul endroit, `lcd_rgb_panel_try_restart_transmission()`
 * (esp_lcd_panel_rgb.c:1149-1165), et il n'y est lu que dans la branche
 * `#else` :
 *
 *     #if CONFIG_LCD_RGB_RESTART_IN_VSYNC
 *         do_restart = true;            <- inconditionnel, need_restart IGNORÉ
 *     #else
 *         if (panel->flags.need_restart) { ... }
 *     #endif
 *
 * Or le sdkconfig retenu pose CONFIG_LCD_RGB_RESTART_IN_VSYNC=y : la DMA est
 * déjà relancée à CHAQUE VBlank, et le seul bit que la commande `dma` sait
 * poser n'est jamais consulté. L'appel ne ferait donc rien, et renverrait
 * ESP_OK — le pire des retours, celui qui a l'air d'une réussite.
 *
 * POURQUOI ÇA COMPTE POUR LA TRAÇABILITÉ : la preuve d'origine (« un restart
 * manuel rattrape l'image décalée ») a été faite avec RESTART_IN_VSYNC=n, et
 * elle RESTE VALIDE dans ce contexte-là. Mais sous la configuration livrée,
 * toute observation du type « la commande `dma` a corrigé le décalage » est
 * MAL ATTRIBUÉE : ce qui a corrigé, c'est le restart automatique par VBlank,
 * qui aurait eu lieu de toute façon.
 *
 * On refuse donc l'appel plutôt que de le jouer pour rien, et on renvoie
 * ESP_ERR_NOT_SUPPORTED — que l'appelant imprime déjà via esp_err_to_name(),
 * ce qui rend la sortie console honnête sans avoir à toucher dn_console.c.
 */
esp_err_t dn_display_restart(void)
{
#if CONFIG_LCD_RGB_RESTART_IN_VSYNC
    ESP_LOGW(TAG,
             "relance DMA SANS EFFET : CONFIG_LCD_RGB_RESTART_IN_VSYNC=y, la "
             "DMA est déjà relancée à chaque VBlank et le bit `need_restart` "
             "posé par esp_lcd_rgb_panel_restart() n'est jamais lu "
             "(esp_lcd_panel_rgb.c:1149-1165).");
    ESP_LOGW(TAG,
             "  => si une image décalée se recale « après un `dma` », ce n'est "
             "PAS la commande : c'est le restart automatique du VBlank. Pour "
             "éprouver la relance MANUELLE, il faut rebâtir avec "
             "CONFIG_LCD_RGB_RESTART_IN_VSYNC=n.");
    return ESP_ERR_NOT_SUPPORTED;
#else
    ESP_LOGI(TAG,
             "relance DMA manuelle demandée (RESTART_IN_VSYNC=n : le bit "
             "`need_restart` est bien consulté au prochain VSYNC_END)");
    return esp_lcd_rgb_panel_restart(s_panel);
#endif
}

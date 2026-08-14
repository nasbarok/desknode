#include "dn_display.h"

#include <string.h>

#include "dn_measure.h"
#include "dn_pins.h"
#include "dn_st7701_init.h"
#include "driver/gpio.h"
#include "driver/i2c_master.h"
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
static bool s_backlight_on;
static bool s_disp_on;

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
    ESP_LOGI(TAG, "bus I2C monté : SDA=GPIO%d SCL=GPIO%d @ %d Hz",
             DN_PIN_I2C_SDA, DN_PIN_I2C_SCL, DN_I2C_FREQ_HZ);
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

    /* ⚠️ TP_RST (bit 1) : on le laisse DÉLIBÉRÉMENT dans son état de mise sous
     * tension du TCA9554, c'est-à-dire en ENTRÉE haute impédance. On ne le
     * pilote pas — le GT911 est le sujet de dn1-4, et le mettre en sortie ici
     * lui imposerait un niveau qu'on n'a pas mesuré. Cet état est un livrable
     * de P1 : dn1-4 en dépend. */
    ESP_LOGI(TAG,
             "TCA9554 prêt : LCD_RST=bit0 et LCD_CS=bit2 en SORTIE ; "
             "TP_RST=bit1 laissé en ENTRÉE (état de reset de l'expander)");
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

esp_err_t dn_display_init(const dn_bootcfg_t *cfg)
{
    /* Rétroéclairage : configuré ÉTEINT tout de suite, pour ne pas hériter de
     * l'état laissé par le firmware précédent. Il ne s'allumera qu'une fois le
     * framebuffer rempli. */
    gpio_config_t bl = {
        .pin_bit_mask = 1ULL << DN_PIN_BACKLIGHT,
        .mode = GPIO_MODE_OUTPUT,
    };
    ESP_RETURN_ON_ERROR(gpio_config(&bl), TAG, "GPIO rétroéclairage refusé");
    gpio_set_level(DN_PIN_BACKLIGHT, 0);
    s_backlight_on = false;

    ESP_RETURN_ON_ERROR(i2c_bring_up(), TAG, "étape 1/5");
    ESP_RETURN_ON_ERROR(expander_bring_up(), TAG, "étape 2/5");
    ESP_RETURN_ON_ERROR(panel_hw_reset(), TAG, "étape 3/5");
    ESP_RETURN_ON_ERROR(spi3wire_bring_up(), TAG, "étape 4/5");
    ESP_RETURN_ON_ERROR(panel_bring_up(cfg), TAG, "étape 5/5");
    return ESP_OK;
}

esp_err_t dn_display_backlight(bool on)
{
    s_backlight_on = on;
    return gpio_set_level(DN_PIN_BACKLIGHT, on ? 1 : 0);
}

bool dn_display_backlight_state(void) { return s_backlight_on; }

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
    esp_lcd_panel_draw_bitmap(s_panel, 0, 0, DN_LCD_H_RES, DN_LCD_V_RES, buf);
    if (s_num_fbs > 1) {
        s_draw_index = (s_draw_index + 1) % s_num_fbs;
    }
    return esp_timer_get_time() - t0;
}

int64_t dn_display_blit(const uint16_t *src)
{
    uint16_t *dst = s_fbs[s_draw_index];
    int64_t t0 = esp_timer_get_time();
    memcpy(dst, src, DN_FB_BYTES);
    int64_t dt = esp_timer_get_time() - t0;
    dn_display_present();
    return dt;
}

esp_err_t dn_display_restart(void) { return esp_lcd_rgb_panel_restart(s_panel); }

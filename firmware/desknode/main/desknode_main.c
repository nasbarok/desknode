/*
 * DeskNode — P1 « Living PCB statique plein écran » (story dn1-2).
 *
 * Ce que ce firmware fait, dans cet ordre EXACT :
 *   1. lit la configuration de boot (num_fbs, bounce) en NVS ;
 *   2. monte le pipeline d'affichage, rétroéclairage ÉTEINT ;
 *   3. branche le compteur vsync ;
 *   4. mappe l'asset Living PCB et le copie dans le framebuffer ;
 *   5. ALLUME le rétroéclairage — et seulement là ;
 *   6. ouvre la console de mesure.
 *
 * L'étape 5 après l'étape 4 n'est pas un détail de style : l'inverse donne un
 * flash blanc ou un champ de bruit au démarrage, et on passe une heure à
 * douter du driver alors que c'est l'ordre des opérations.
 */

#include <inttypes.h>

#include "dn_asset.h"
#include "dn_bootcfg.h"
#include "dn_console.h"
#include "dn_display.h"
#include "dn_measure.h"
#include "dn_patterns.h"
#include "dn_pins.h"
#include "esp_chip_info.h"
#include "esp_err.h"
#include "esp_flash.h"
#include "esp_log.h"
#include "esp_psram.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs_flash.h"
#include "spi_flash_mmap.h"

static const char *TAG = "desknode";

static void log_socle(void)
{
    /* Ce bloc existe pour AC2 : il rend LISIBLE dans le log applicatif ce que
     * le bandeau de bootloader annonce en passant. Deux sources indépendantes
     * qui disent la même chose valent mieux qu'une. */
    uint32_t flash_size = 0;
    esp_err_t err = esp_flash_get_physical_size(NULL, &flash_size);
    ESP_LOGI(TAG, "──── socle ────────────────────────────────────────────");
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "flash physique détectée : %" PRIu32 " o (%.0f MB)",
                 flash_size, (double)flash_size / (1024.0 * 1024.0));
    } else {
        ESP_LOGW(TAG, "taille de flash indisponible : %s", esp_err_to_name(err));
    }

#if CONFIG_SPIRAM
    ESP_LOGI(TAG, "PSRAM : %u o détectés, mode %s, %s",
             (unsigned)esp_psram_get_size(),
#if CONFIG_SPIRAM_MODE_OCT
             "OCTAL",
#else
             "QUAD (⚠️ inattendu sur cette carte)",
#endif
#if CONFIG_SPIRAM_SPEED_80M
             "80 MHz"
#elif CONFIG_SPIRAM_SPEED_120M
             "120 MHz (⛔ INTERDIT ici — voir sdkconfig.defaults)"
#else
             "40 MHz (⚠️ le défaut IDF : le refill DMA va manquer)"
#endif
    );
#else
    ESP_LOGE(TAG, "PSRAM DÉSACTIVÉE — aucun framebuffer possible");
#endif

#if CONFIG_SPIRAM_XIP_FROM_PSRAM
    ESP_LOGI(TAG, "XIP depuis la PSRAM : ACTIVÉ (mesure A/B d'AC6, branche « avec »)");
#else
    ESP_LOGI(TAG, "XIP depuis la PSRAM : désactivé (branche « sans » d'AC6)");
#endif
#if CONFIG_LCD_RGB_RESTART_IN_VSYNC
    ESP_LOGI(TAG, "LCD_RGB_RESTART_IN_VSYNC : activé");
#else
    ESP_LOGI(TAG, "LCD_RGB_RESTART_IN_VSYNC : désactivé (défaut IDF)");
#endif
#if CONFIG_LCD_RGB_ISR_IRAM_SAFE
    ESP_LOGI(TAG, "LCD_RGB_ISR_IRAM_SAFE : activé — le compteur vsync continue "
                  "de compter PENDANT les écritures flash");
#else
    ESP_LOGW(TAG, "LCD_RGB_ISR_IRAM_SAFE : désactivé — le compteur vsync sera "
                  "AVEUGLE pendant le stimulus d'AC6");
#endif
    ESP_LOGI(TAG, "──────────────────────────────────────────────────────");
}

void app_main(void)
{
    int64_t t_boot = esp_timer_get_time();

    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);

    log_socle();

    dn_bootcfg_t cfg;
    ESP_ERROR_CHECK(dn_bootcfg_load(&cfg));
    dn_bootcfg_log(&cfg);

    /* 2. Pipeline d'affichage, rétroéclairage encore éteint. */
    ESP_ERROR_CHECK(dn_display_init(&cfg));

    /* 3. Instrumentation, avant tout dessin : on veut compter dès la première
     *    trame, y compris celles qui précèdent l'image. */
    ESP_ERROR_CHECK(dn_measure_attach(dn_display_panel()));

    /* 4. L'asset. Un échec ici n'est PAS fatal : la mire de cadrage reste
     *    affichable, et c'est elle qui prouve le pipeline. On le dit fort. */
    if (dn_asset_init() != ESP_OK) {
        ESP_LOGW(TAG,
                 "asset indisponible — la scène « asset » affichera un panneau "
                 "d'alerte plutôt qu'un écran noir trompeur");
    }
    uint16_t *fb = dn_display_draw_buffer();
    dn_pattern_draw(fb, DN_SCENE_ASSET);
    dn_display_present();
    dn_asset_log();

    /* 5. ET SEULEMENT MAINTENANT le rétroéclairage. */
    ESP_ERROR_CHECK(dn_display_backlight(true));
    ESP_LOGI(TAG,
             "rétroéclairage ON FIXE (GPIO%d). ⚠️ il ne clignote plus : le "
             "clignotement était le signe de vie de P0, ce n'est plus un "
             "symptôme valide en P1.",
             DN_PIN_BACKLIGHT);

    ESP_LOGI(TAG, "prêt en %lld ms depuis app_main",
             (long long)((esp_timer_get_time() - t_boot) / 1000));

    /* 6. La console. */
    ESP_ERROR_CHECK(dn_console_start());
    dn_console_banner();

    /* Battement de cœur : il prouve que l'application vit encore, même quand
     * l'écran est figé sur une mire statique. Sans lui, un firmware planté et
     * un firmware qui affiche correctement se ressemblent trait pour trait. */
    uint32_t s = 0;
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(10000));
        s += 10;
        ESP_LOGI(TAG, "up %" PRIu32 " s — vsync=%" PRIu32 " — PSRAM libre %u o",
                 s, dn_measure_vsync_count(), (unsigned)dn_measure_psram_free());
    }
}

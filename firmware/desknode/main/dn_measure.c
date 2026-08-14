#include "dn_measure.h"

#include <math.h>

#include "dn_pins.h"
#include "esp_attr.h"
#include "esp_check.h"
#include "esp_heap_caps.h"
#include "esp_lcd_panel_rgb.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"

static const char *TAG = "dn_mes";

/*
 * ⚠️ CE COMPTEUR EST TOUCHÉ SOUS ISR.
 *    - `volatile`, sinon le compilateur peut garder la valeur en registre ;
 *    - en RAM INTERNE (.bss), jamais en PSRAM : avec
 *      CONFIG_LCD_RGB_ISR_IRAM_SAFE=y l'ISR tourne cache désactivé, et un accès
 *      PSRAM y planterait la puce ;
 *    - AUCUN ESP_LOGx dans le callback, pour la même raison.
 */
static volatile uint32_t s_vsync_count;

/* Sémaphore de rendez-vous avec le retour vertical. Donné DEPUIS L'ISR :
 * `xSemaphoreGiveFromISR` est en IRAM par défaut dans ESP-IDF (FreeRTOS n'est
 * déplacé en flash que si CONFIG_FREERTOS_PLACE_FUNCTIONS_INTO_FLASH est
 * activé, ce qu'on ne fait pas) — indispensable, puisque l'ISR tourne cache
 * désactivé pendant les écritures flash d'AC6. */
static SemaphoreHandle_t s_vsync_sem;

/* Rendez-vous avec « ce framebuffer-là n'est plus lu par la DMA ».
 * C'est un signal DIFFÉRENT du VSYNC, et c'est le bon pour le double
 * tampon : le VSYNC dit « une trame commence », pas « l'ancien tampon est
 * libéré ». Entre les deux il y a la préextraction de la GDMA. */
static SemaphoreHandle_t s_fbdone_sem;

static size_t s_psram_avant;
static size_t s_psram_apres;

static IRAM_ATTR bool on_vsync(esp_lcd_panel_handle_t panel,
                               const esp_lcd_rgb_panel_event_data_t *edata,
                               void *user_ctx)
{
    (void)panel;
    (void)edata;
    (void)user_ctx;
    s_vsync_count++;
    BaseType_t hp = pdFALSE;
    if (s_vsync_sem) {
        xSemaphoreGiveFromISR(s_vsync_sem, &hp);
    }
    return hp == pdTRUE; /* true => réveiller une tâche de plus haute priorité */
}

static IRAM_ATTR bool on_frame_buf_complete(esp_lcd_panel_handle_t panel,
                                            const esp_lcd_rgb_panel_event_data_t *edata,
                                            void *user_ctx)
{
    (void)panel;
    (void)edata;
    (void)user_ctx;
    BaseType_t hp = pdFALSE;
    if (s_fbdone_sem) {
        xSemaphoreGiveFromISR(s_fbdone_sem, &hp);
    }
    return hp == pdTRUE;
}

bool dn_measure_wait_frame_done(uint32_t timeout_ms)
{
    if (!s_fbdone_sem) {
        return false;
    }
    xSemaphoreTake(s_fbdone_sem, 0);
    return xSemaphoreTake(s_fbdone_sem, pdMS_TO_TICKS(timeout_ms)) == pdTRUE;
}

bool dn_measure_wait_vsync(uint32_t timeout_ms)
{
    if (!s_vsync_sem) {
        return false;
    }
    /* On vide d'abord le sémaphore : sinon on repartirait sur un VSYNC déjà
     * passé, et la bascule tomberait au milieu du balayage — exactement ce
     * qu'on cherche à éviter. */
    xSemaphoreTake(s_vsync_sem, 0);
    return xSemaphoreTake(s_vsync_sem, pdMS_TO_TICKS(timeout_ms)) == pdTRUE;
}

esp_err_t dn_measure_attach(esp_lcd_panel_handle_t panel)
{
    s_vsync_sem = xSemaphoreCreateBinary();
    s_fbdone_sem = xSemaphoreCreateBinary();
    ESP_RETURN_ON_FALSE(s_vsync_sem && s_fbdone_sem, ESP_ERR_NO_MEM, TAG,
                        "sémaphores vsync/frame_buf non alloués");
    esp_lcd_rgb_panel_event_callbacks_t cbs = {
        .on_vsync = on_vsync,
        .on_frame_buf_complete = on_frame_buf_complete,
    };
    ESP_RETURN_ON_ERROR(
        esp_lcd_rgb_panel_register_event_callbacks(panel, &cbs, NULL), TAG,
        "branchement du callback vsync refusé");
    ESP_LOGI(TAG, "compteur vsync branché (ISR en IRAM, compteur en RAM interne)");
    return ESP_OK;
}

uint32_t dn_measure_vsync_count(void) { return s_vsync_count; }

double dn_measure_fps(int seconds, uint32_t *out_frames, int64_t *out_elapsed_us)
{
    if (seconds < 1) {
        seconds = 1;
    }
    uint32_t c0 = s_vsync_count;
    int64_t t0 = esp_timer_get_time();
    vTaskDelay(pdMS_TO_TICKS(seconds * 1000));
    uint32_t c1 = s_vsync_count;
    int64_t t1 = esp_timer_get_time();

    uint32_t frames = c1 - c0; /* non signé : l'enroulement se gère tout seul */
    int64_t elapsed = t1 - t0;
    if (out_frames) {
        *out_frames = frames;
    }
    if (out_elapsed_us) {
        *out_elapsed_us = elapsed;
    }
    if (elapsed <= 0) {
        return 0.0;
    }
    return (double)frames * 1000000.0 / (double)elapsed;
}

size_t dn_measure_psram_free(void)
{
    return heap_caps_get_free_size(MALLOC_CAP_SPIRAM);
}

size_t dn_measure_internal_free(void)
{
    return heap_caps_get_free_size(MALLOC_CAP_INTERNAL);
}

void dn_measure_note_psram(size_t avant, size_t apres)
{
    s_psram_avant = avant;
    s_psram_apres = apres;
}

void dn_measure_get_psram_note(size_t *avant, size_t *apres)
{
    if (avant) {
        *avant = s_psram_avant;
    }
    if (apres) {
        *apres = s_psram_apres;
    }
}

void dn_measure_report_fps(const char *etiquette, int seconds)
{
    uint32_t frames = 0;
    int64_t elapsed = 0;

    ESP_LOGI(TAG, "[%s] mesure fps en cours sur %d s…", etiquette, seconds);
    double fps = dn_measure_fps(seconds, &frames, &elapsed);
    double theo = DN_FPS_THEORIQUE;
    double ecart = theo > 0.0 ? (fps - theo) / theo * 100.0 : 0.0;

    /* Le calcul est RÉÉCRIT dans la trace : AC4 exige que la mesure se
     * confronte à la théorie sans qu'on ait à ouvrir un autre document. */
    ESP_LOGI(TAG, "[%s] --- fps ---------------------------------------", etiquette);
    ESP_LOGI(TAG, "[%s]   trames comptées : %lu en %lld us", etiquette,
             (unsigned long)frames, (long long)elapsed);
    ESP_LOGI(TAG, "[%s]   fps MESURÉ      : %.2f Hz", etiquette, fps);
    ESP_LOGI(TAG,
             "[%s]   fps THÉORIQUE   : %.2f Hz  = pclk / (htotal x vtotal)",
             etiquette, theo);
    ESP_LOGI(TAG,
             "[%s]                     = %d / ((%d+%d+%d+%d) x (%d+%d+%d+%d))",
             etiquette, DN_PCLK_HZ, DN_LCD_H_RES, DN_HSYNC_PULSE,
             DN_HSYNC_BACK_PORCH, DN_HSYNC_FRONT_PORCH, DN_LCD_V_RES,
             DN_VSYNC_PULSE, DN_VSYNC_BACK_PORCH, DN_VSYNC_FRONT_PORCH);
    ESP_LOGI(TAG, "[%s]                     = %d / (%d x %d) = %d px/trame",
             etiquette, DN_PCLK_HZ,
             DN_LCD_H_RES + DN_HSYNC_PULSE + DN_HSYNC_BACK_PORCH +
                 DN_HSYNC_FRONT_PORCH,
             DN_LCD_V_RES + DN_VSYNC_PULSE + DN_VSYNC_BACK_PORCH +
                 DN_VSYNC_FRONT_PORCH,
             (DN_LCD_H_RES + DN_HSYNC_PULSE + DN_HSYNC_BACK_PORCH +
              DN_HSYNC_FRONT_PORCH) *
                 (DN_LCD_V_RES + DN_VSYNC_PULSE + DN_VSYNC_BACK_PORCH +
                  DN_VSYNC_FRONT_PORCH));
    ESP_LOGI(TAG, "[%s]   ÉCART           : %+.2f %% %s", etiquette, ecart,
             fabs(ecart) > 5.0 ? "<<< AU-DELÀ DES 5 % : à expliquer par une "
                                 "cause OBSERVÉE, pas par une hypothèse"
                               : "(dans les 5 %)");
    ESP_LOGI(TAG,
             "[%s]   rappel : un compteur vsync tourne MÊME écran noir. Ce "
             "chiffre qualifie le pipeline, pas l'image.",
             etiquette);
    ESP_LOGI(TAG, "[%s] ------------------------------------------------", etiquette);
}

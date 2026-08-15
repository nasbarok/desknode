#include "dn_recal.h"

#include "sdkconfig.h" /* CONFIG_LCD_RGB_RESTART_IN_VSYNC */

#include "dn_measure.h"
#include "esp_check.h"
#include "esp_lcd_panel_rgb.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"

static const char *TAG = "dn_recal";

static esp_lcd_panel_handle_t s_panel;
static SemaphoreHandle_t s_arm_sem;     /* bascule -> tâche */
static dn_vsync_sub_t s_vsync_sub = -1; /* abonnement DÉDIÉ, voir dn_measure.h */
static volatile int s_vsyncs = DN_RECAL_VSYNCS_DEFAUT;

static volatile uint32_t s_count;
static volatile uint32_t s_rate;
static volatile uint32_t s_last_err;
static volatile bool s_en_cours;

/*
 * La tâche de recalage. Elle ne fait RIEN d'autre : pas de log dans la boucle
 * chaude au-delà du strict nécessaire, pas d'allocation, pas d'accès au
 * framebuffer. Sa seule raison d'exister est de sortir `esp_lcd_rgb_panel_restart()`
 * de l'ISR — appeler le driver depuis un contexte d'interruption, cache
 * désactivé, serait la panne suivante et pas la parade.
 */
static void recal_task(void *arg)
{
    (void)arg;
    while (1) {
        /* Attente indéfinie : la tâche ne consomme rien tant qu'aucune bascule
         * n'a lieu. À un seul framebuffer, elle dort pour toujours. */
        if (xSemaphoreTake(s_arm_sem, portMAX_DELAY) != pdTRUE) {
            continue;
        }
        int n = s_vsyncs;
        if (n <= 0) {
            s_en_cours = false;
            continue;
        }

        /* On veut les N PROCHAINS retours verticaux, pas ceux déjà passés : on
         * vide d'abord. C'est le même idiome que `dn_measure_wait_vsync()`, et
         * il est CORRECT ici pour la même raison — l'événement attendu n'est pas
         * provoqué par l'appelant, il arrive tout seul à chaque trame. */
        dn_measure_vsync_flush(s_vsync_sub);
        bool ok = true;
        for (int i = 0; i < n; i++) {
            /* 100 ms = ~3,7 périodes de trame : large, et borné. Sans borne, une
             * DMA arrêtée bloquerait la tâche pour toujours et le compteur de
             * recalages resterait à 0 sans qu'on sache pourquoi. */
            if (!dn_measure_vsync_wait(s_vsync_sub, 100)) {
                ESP_LOGW(TAG,
                         "recalage ABANDONNÉ : aucun vsync en 100 ms (attendu "
                         "%d/%d). La DMA est-elle arrêtée ?",
                         i + 1, n);
                ok = false;
                break;
            }
        }

        if (ok) {
            esp_err_t err = esp_lcd_rgb_panel_restart(s_panel);
            s_last_err = (uint32_t)err;
            s_count++;
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "esp_lcd_rgb_panel_restart() : %s",
                         esp_err_to_name(err));
            }
        }
        s_en_cours = false;
    }
}

esp_err_t dn_recal_init(esp_lcd_panel_handle_t panel)
{
    ESP_RETURN_ON_FALSE(panel, ESP_ERR_INVALID_ARG, TAG, "panneau NULL");
    s_panel = panel;

    s_arm_sem = xSemaphoreCreateBinary();
    ESP_RETURN_ON_FALSE(s_arm_sem, ESP_ERR_NO_MEM, TAG, "sémaphore d'armement");

    s_vsync_sub = dn_measure_vsync_subscribe("recal");
    ESP_RETURN_ON_FALSE(s_vsync_sub >= 0, ESP_ERR_NO_MEM, TAG,
                        "abonnement vsync refusé");

    /*
     * Priorité 5 : au-dessus de la tâche LVGL (4) et du REPL, pour que le
     * recalage tombe à la trame VOULUE et pas deux trames plus tard — c'est
     * précisément le TIMING qu'AC5 met à l'épreuve, il ne doit pas dépendre de
     * la charge du moment. La tâche ne fait que compter et poser un bit : elle
     * ne peut pas affamer quoi que ce soit.
     * Pile 3072 : elle n'appelle que le driver et ESP_LOG.
     */
    BaseType_t ok = xTaskCreate(recal_task, "dn_recal", 3072, NULL, 5, NULL);
    ESP_RETURN_ON_FALSE(ok == pdPASS, ESP_ERR_NO_MEM, TAG, "tâche de recalage");
    return ESP_OK;
}

void dn_recal_arm(void)
{
    if (!s_arm_sem || s_vsyncs <= 0) {
        return;
    }
    if (s_en_cours) {
        /* Une bascule est arrivée pendant qu'on attendait les vsyncs de la
         * PRÉCÉDENTE. On ne réarme pas — on COMPTE l'armement perdu. Un
         * compteur visible vaut mieux qu'un silence : si `recal` affiche
         * beaucoup de perdus, c'est que la cadence de bascule dépasse la
         * fenêtre de recalage, et cette information change la conclusion d'AC5. */
        s_rate++;
        return;
    }
    s_en_cours = true;
    xSemaphoreGive(s_arm_sem);
}

esp_err_t dn_recal_set_vsyncs(int vsyncs)
{
    if (vsyncs < 0 || vsyncs > DN_RECAL_VSYNCS_MAX) {
        return ESP_ERR_INVALID_ARG;
    }
    s_vsyncs = vsyncs;
    return ESP_OK;
}

int dn_recal_get_vsyncs(void) { return s_vsyncs; }
uint32_t dn_recal_count(void) { return s_count; }
uint32_t dn_recal_rate(void) { return s_rate; }
uint32_t dn_recal_last_err(void) { return s_last_err; }

void dn_recal_log_etat(void)
{
#if CONFIG_LCD_RGB_RESTART_IN_VSYNC
    ESP_LOGW(TAG,
             "recalage sur événement : INERTE dans ce build. "
             "CONFIG_LCD_RGB_RESTART_IN_VSYNC=y ⇒ le driver relance déjà à "
             "chaque VBlank et ne lit JAMAIS le bit posé par "
             "esp_lcd_rgb_panel_restart() (esp_lcd_panel_rgb.c:1149-1165).");
    ESP_LOGW(TAG,
             "  => mesurer AC5 impose une BRANCHE D'ESSAI : poser "
             "CONFIG_LCD_RGB_RESTART_IN_VSYNC=n dans sdkconfig.defaults, puis "
             "`rm sdkconfig && idf.py build`. Sans ça, tout « le recalage n'a "
             "rien changé » serait une non-mesure.");
#else
    ESP_LOGI(TAG,
             "recalage sur événement ACTIF : %d vsync(s) après chaque bascule "
             "(RESTART_IN_VSYNC=n, le bit `need_restart` est bien consulté).",
             s_vsyncs);
#endif
}

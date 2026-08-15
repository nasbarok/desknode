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

/* Rendez-vous avec `on_frame_buf_complete`.
 * ⚠️ Le nom du callback ment SUR CETTE PUCE, et ce commentaire mentait avec
 *    lui : il annonçait « ce framebuffer-là n'est plus lu par la DMA ». Cette
 *    garantie-là exige l'événement de bascule de lien GDMA, compilé sous le
 *    seul `SOC_AXI_GDMA_SUPPORTED` — que l'ESP32-S3 ne définit pas
 *    (soc_caps.h:33 : `SOC_AHB_GDMA_SUPPORTED` uniquement). Ici le callback
 *    arrive du trans-EOF de la DMA. C'est donc un POINT DE PHASE différent du
 *    VSYNC dans la trame, et rien de plus. Le gain mesuré tient, l'explication
 *    d'origine non — le détail et les références exactes sont dans
 *    dn_measure.h, au-dessus de `dn_measure_arm_frame_done()`. */
static SemaphoreHandle_t s_fbdone_sem;

/*
 * Les abonnements au vsync (dn1-3). Tableau de taille FIXE, alloué une fois pour
 * toutes : l'ISR le parcourt cache désactivé, donc il doit vivre en RAM interne
 * (.bss) et ne jamais être réalloué. Le compteur d'abonnés n'est écrit que depuis
 * `dn_measure_vsync_subscribe()`, avant que le panneau ne tourne pour de bon —
 * mais il est lu par l'ISR, d'où le `volatile`.
 */
/* `volatile` sur le TABLEAU aussi (revue) : le commentaire ci-dessus promettait
 * « publié en dernier », mais un store ordinaire suivi d'un store volatile n'a
 * AUCUNE garantie d'ordre en C — l'invariant était fourni par chance. Avec les
 * deux volatiles, le compilateur ne peut pas réordonner les deux écritures. */
static SemaphoreHandle_t volatile s_vsync_subs[DN_VSYNC_SUBS_MAX];
static volatile int s_vsync_subs_n;
static const char *s_vsync_subs_nom[DN_VSYNC_SUBS_MAX];

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
    /* Chaque abonné reçoit SON jeton. Pas de boucle non bornée, pas
     * d'allocation, pas de log : on est sous ISR, cache potentiellement
     * désactivé. `xSemaphoreGiveFromISR` est en IRAM par défaut dans ESP-IDF. */
    int n = s_vsync_subs_n;
    for (int i = 0; i < n; i++) {
        if (s_vsync_subs[i]) {
            BaseType_t hp_i = pdFALSE;
            xSemaphoreGiveFromISR(s_vsync_subs[i], &hp_i);
            if (hp_i == pdTRUE) {
                hp = pdTRUE;
            }
        }
    }
    return hp == pdTRUE; /* true => réveiller une tâche de plus haute priorité */
}

/* ⚠️ Nom trompeur sur l'ESP32-S3 : ce qui nous appelle ici, c'est
 *    `lcd_rgb_panel_eof_handler()` sur le trans-EOF de la DMA — pas la bascule
 *    de lien GDMA qui, elle, donnerait vraiment « le tampon est libéré ». Voir
 *    le commentaire de `s_fbdone_sem` ci-dessus. */
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

void dn_measure_arm_frame_done(void)
{
    if (!s_fbdone_sem) {
        return;
    }
    /* Vider AVANT la bascule, JAMAIS après : après, on jette l'événement que la
     * bascule vient elle-même de provoquer, et l'attente qui suit part pour une
     * trame de plus ou expire. Symptôme observé côté mesure : une latence
     * supplémentaire non déterministe sur les modes synchronisés. */
    xSemaphoreTake(s_fbdone_sem, 0);
}

bool dn_measure_wait_frame_done(uint32_t timeout_ms)
{
    if (!s_fbdone_sem) {
        return false;
    }
    /* AUCUN vidage ici, et c'est le correctif : c'est
     * `dn_measure_arm_frame_done()`, appelé avant `dn_display_present()`, qui
     * s'en charge. Ne pas « symétriser » avec `dn_measure_wait_vsync()`
     * ci-dessous : les deux besoins sont opposés (voir dn_measure.h). */
    return xSemaphoreTake(s_fbdone_sem, pdMS_TO_TICKS(timeout_ms)) == pdTRUE;
}

bool dn_measure_wait_vsync(uint32_t timeout_ms)
{
    if (!s_vsync_sem) {
        return false;
    }
    /* On vide d'abord le sémaphore : sinon on repartirait sur un VSYNC déjà
     * passé, et la bascule tomberait au milieu du balayage — exactement ce
     * qu'on cherche à éviter.
     * ⚠️ Ce vidage-ci est CORRECT et doit rester où il est : on veut le
     *    PROCHAIN retour vertical, et aucun appelant ne provoque le VSYNC. Ce
     *    n'est pas le cas de `wait_frame_done`, dont l'appelant provoque
     *    lui-même l'événement — d'où l'armement séparé, plus haut. */
    xSemaphoreTake(s_vsync_sem, 0);
    return xSemaphoreTake(s_vsync_sem, pdMS_TO_TICKS(timeout_ms)) == pdTRUE;
}

dn_vsync_sub_t dn_measure_vsync_subscribe(const char *nom)
{
    if (s_vsync_subs_n >= DN_VSYNC_SUBS_MAX) {
        ESP_LOGE(TAG,
                 "abonnement vsync « %s » REFUSÉ : les %d slots sont pris. "
                 "Aucun repli silencieux — un abonné qui partagerait le "
                 "sémaphore d'un autre lui volerait ses événements.",
                 nom ? nom : "?", DN_VSYNC_SUBS_MAX);
        return -1;
    }
    SemaphoreHandle_t sem = xSemaphoreCreateBinary();
    if (!sem) {
        ESP_LOGE(TAG, "abonnement vsync « %s » : sémaphore non alloué",
                 nom ? nom : "?");
        return -1;
    }
    int slot = s_vsync_subs_n;
    s_vsync_subs[slot] = sem;
    s_vsync_subs_nom[slot] = nom;
    /* Publié EN DERNIER : l'ISR lit `s_vsync_subs_n` pour borner sa boucle, donc
     * le sémaphore doit déjà être en place quand le compteur l'inclut. */
    s_vsync_subs_n = slot + 1;
    ESP_LOGI(TAG, "abonnement vsync #%d : « %s »", slot, nom ? nom : "?");
    return slot;
}

void dn_measure_vsync_flush(dn_vsync_sub_t sub)
{
    if (sub < 0 || sub >= s_vsync_subs_n || !s_vsync_subs[sub]) {
        return;
    }
    xSemaphoreTake(s_vsync_subs[sub], 0);
}

bool dn_measure_vsync_wait(dn_vsync_sub_t sub, uint32_t timeout_ms)
{
    if (sub < 0 || sub >= s_vsync_subs_n || !s_vsync_subs[sub]) {
        return false;
    }
    return xSemaphoreTake(s_vsync_subs[sub], pdMS_TO_TICKS(timeout_ms)) == pdTRUE;
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
    /*
     * ⚠️ CE MODULE EST LE POINT D'ENREGISTREMENT UNIQUE — et « unique » est le
     *    mot important. `esp_lcd_rgb_panel_register_event_callbacks()` ne fusionne
     *    RIEN : il ASSIGNE les quatre pointeurs et `user_ctx`
     *    (esp_lcd_panel_rgb.c:444-448). Le dernier appelant efface le précédent,
     *    en silence, et rend ESP_OK.
     *
     *    Or `lvgl_port_add_disp_rgb()` enregistre lui aussi `on_vsync`
     *    (esp_lvgl_port_disp.c:219, inconditionnel). Les deux sont donc en
     *    collision directe. Le choix de dn1-3, écrit ici pour qu'on ne le
     *    « corrige » pas plus tard :
     *      -> dn_measure_attach() est appelé APRÈS lvgl_port_add_disp_rgb(),
     *         et gagne. Le callback du portage n'alimente qu'un sémaphore que le
     *         portage n'attend QUE dans ses modes direct/full — modes qu'on
     *         n'utilise pas (rendu PARTIEL, num_fbs=1). Le perdre ne coûte rien.
     *      -> la synchronisation du flush passe par un abonnement vsync de
     *         dn_measure (dn_ui.c), pas par la mécanique interne du portage.
     *
     *    Si l'ordre s'inversait un jour, le symptôme serait MUET : `fps` et
     *    l'abonnement vsync compteraient 0, la mesure de déchirement mesurerait
     *    du vide — exactement le genre de défaut silencieux que dn1-2 a payé
     *    cher. D'où le contrôle actif ci-dessous, au boot.
     */
    ESP_RETURN_ON_ERROR(
        esp_lcd_rgb_panel_register_event_callbacks(panel, &cbs, NULL), TAG,
        "branchement du callback vsync refusé");
    ESP_LOGI(TAG, "compteur vsync branché (ISR en IRAM, compteur en RAM interne)");
    ESP_LOGI(TAG,
             "  ⚠️ enregistrement EXCLUSIF : il vient d'écraser tout callback "
             "posé avant lui (esp_lcd rgb ASSIGNE, ne fusionne pas). C'est "
             "voulu — voir le commentaire au-dessus.");
    return ESP_OK;
}

uint32_t dn_measure_vsync_count(void) { return s_vsync_count; }

bool dn_measure_vsync_alive(uint32_t ms)
{
    uint32_t c0 = s_vsync_count;
    vTaskDelay(pdMS_TO_TICKS(ms));
    uint32_t vues = s_vsync_count - c0; /* non signé : l'enroulement se gère seul */
    if (vues == 0) {
        ESP_LOGE(TAG,
                 "TÉMOIN VSYNC MORT : 0 trame comptée en %lu ms (~%.1f "
                 "attendues). Le callback a été DÉBRANCHÉ par un "
                 "enregistrement ultérieur, ou le panneau ne tourne pas.",
                 (unsigned long)ms, (double)ms / 1000.0 * DN_FPS_THEORIQUE);
        ESP_LOGE(TAG,
                 "  => toute mesure faite maintenant (fps, déchirement, "
                 "cadence) porterait une étiquette FAUSSE. Ne rien conclure.");
        return false;
    }
    ESP_LOGI(TAG, "témoin vsync : %lu trames en %lu ms — le compteur est vivant",
             (unsigned long)vues, (unsigned long)ms);
    return true;
}

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

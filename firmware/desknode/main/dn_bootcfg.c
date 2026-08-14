#include "dn_bootcfg.h"

#include "dn_pins.h"
#include "esp_log.h"
#include "nvs.h"
#include "nvs_flash.h"

static const char *TAG = "dn_cfg";

#define DN_NVS_NAMESPACE "desknode"
#define DN_KEY_NUM_FBS "num_fbs"
#define DN_KEY_BOUNCE "bounce_px"

/*
 * Défauts = LA CONFIGURATION DE RÉFÉRENCE retenue par la story dn1-2, pour
 * qu'un clone neuf démarre dessus sans rien régler.
 *
 *   num_fbs = 2   : le double tampon ne supprime pas le déchirement à lui seul
 *                   (mesuré), mais il est le socle de la seule configuration
 *                   qui l'atténue — bascule attendue sur on_frame_buf_complete.
 *   bounce  = 0   : le bounce buffer a été ÉLIMINÉ, avec deux symptômes.
 *                   Avec CONFIG_LCD_RGB_ISR_IRAM_SAFE=y il provoque un
 *                   redémarrage watchdog (`rst:0x8 TG1WDT_SYS_RST`) dès la
 *                   première seconde d'écriture flash ; sans lui, l'image
 *                   défile ET garde un décalage VERTICAL permanent que
 *                   esp_lcd_rgb_panel_restart() ne rattrape pas.
 */
#define DN_DEFAULT_NUM_FBS 2
#define DN_DEFAULT_BOUNCE_PX 0

static esp_err_t open_nvs(nvs_open_mode_t mode, nvs_handle_t *out)
{
    esp_err_t err = nvs_open(DN_NVS_NAMESPACE, mode, out);
    if (err != ESP_OK && err != ESP_ERR_NVS_NOT_FOUND) {
        ESP_LOGW(TAG, "nvs_open(%d) a échoué : %s", mode, esp_err_to_name(err));
    }
    return err;
}

esp_err_t dn_bootcfg_load(dn_bootcfg_t *out)
{
    if (!out) {
        return ESP_ERR_INVALID_ARG;
    }
    out->num_fbs = DN_DEFAULT_NUM_FBS;
    out->bounce_px = DN_DEFAULT_BOUNCE_PX;

    nvs_handle_t h;
    if (open_nvs(NVS_READONLY, &h) != ESP_OK) {
        ESP_LOGI(TAG, "aucune config en NVS — défauts appliqués");
        return ESP_OK;
    }

    int32_t v;
    if (nvs_get_i32(h, DN_KEY_NUM_FBS, &v) == ESP_OK) {
        if (v >= 1 && v <= 3) {
            out->num_fbs = (int)v;
        } else {
            ESP_LOGW(TAG, "num_fbs=%ld hors de [1,3] : défaut %d appliqué", (long)v,
                     DN_DEFAULT_NUM_FBS);
        }
    }
    if (nvs_get_i32(h, DN_KEY_BOUNCE, &v) == ESP_OK) {
        /* Le driver RGB exige que la taille du bounce buffer divise le nombre
         * de pixels de la trame — sinon la DMA se décale d'un reliquat à chaque
         * trame. On refuse ici plutôt que de laisser le driver échouer plus
         * loin avec un message obscur. */
        if (v == 0 || (v > 0 && ((size_t)DN_LCD_TOTAL_PX % (size_t)v) == 0)) {
            out->bounce_px = (int)v;
        } else {
            ESP_LOGW(TAG,
                     "bounce_px=%ld ne divise pas %d pixels de trame : ignoré",
                     (long)v, DN_LCD_TOTAL_PX);
        }
    }
    nvs_close(h);
    return ESP_OK;
}

static esp_err_t set_i32(const char *key, int32_t value)
{
    nvs_handle_t h;
    esp_err_t err = nvs_open(DN_NVS_NAMESPACE, NVS_READWRITE, &h);
    if (err != ESP_OK) {
        return err;
    }
    err = nvs_set_i32(h, key, value);
    if (err == ESP_OK) {
        err = nvs_commit(h);
    }
    nvs_close(h);
    return err;
}

esp_err_t dn_bootcfg_set_num_fbs(int num_fbs)
{
    if (num_fbs < 1 || num_fbs > 3) {
        return ESP_ERR_INVALID_ARG;
    }
    return set_i32(DN_KEY_NUM_FBS, num_fbs);
}

esp_err_t dn_bootcfg_set_bounce_px(int bounce_px)
{
    if (bounce_px < 0) {
        return ESP_ERR_INVALID_ARG;
    }
    if (bounce_px != 0 && ((size_t)DN_LCD_TOTAL_PX % (size_t)bounce_px) != 0) {
        return ESP_ERR_INVALID_ARG;
    }
    return set_i32(DN_KEY_BOUNCE, bounce_px);
}

esp_err_t dn_bootcfg_reset(void)
{
    nvs_handle_t h;
    esp_err_t err = nvs_open(DN_NVS_NAMESPACE, NVS_READWRITE, &h);
    if (err != ESP_OK) {
        return err;
    }
    err = nvs_erase_all(h);
    if (err == ESP_OK) {
        err = nvs_commit(h);
    }
    nvs_close(h);
    return err;
}

void dn_bootcfg_log(const dn_bootcfg_t *cfg)
{
    ESP_LOGI(TAG, "config de boot : num_fbs=%d  bounce_px=%d", cfg->num_fbs,
             cfg->bounce_px);
}

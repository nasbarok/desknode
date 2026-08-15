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
 *   num_fbs = 1   : ARBITRÉ le 2026-08-15, après mesure — et c'est un
 *                   RENVERSEMENT du défaut d'origine, qui valait 2.
 *                   Le double tampon est IMPOSSIBLE sur cette puce tant que
 *                   CONFIG_LCD_RGB_RESTART_IN_VSYNC est activé — et il l'est,
 *                   parce que sans lui l'image reste décalée en permanence.
 *                   Mécanisme : RGB_LCD_NEEDS_SEPARATE_RESTART_LINK vaut 1 sur
 *                   S3, `dma_restart_link` est soudé à `dma_fb_links[0]` une
 *                   seule fois à l'init (esp_lcd_panel_rgb.c:1135) et jamais
 *                   re-pointé, alors que la relance par VBlank repart toujours
 *                   de là. Conséquence MESURÉE : la dalle n'affichait jamais
 *                   fb[0], une présentation sur deux était perdue EN SILENCE
 *                   (draw_bitmap rendait ESP_OK), et les 614 400 o du second
 *                   framebuffer étaient payés pour rien.
 *                   ⇒ Repasser à 1 récupère 614 312 o de PSRAM (mesuré) et
 *                   rend TOUTES les présentations visibles. Vérifié à l'œil.
 *                   ⚠️ Ce n'est PAS un renoncement définitif au double tampon :
 *                   la piste d'un recalage déclenché sur l'événement de bascule
 *                   effective reste ouverte, et dn1-3 en a besoin. Détail et
 *                   les 6 parades déjà éliminées : §4 bis du fichier hardware/.
 *   bounce  = 0   : le bounce buffer a été ÉLIMINÉ, avec deux symptômes.
 *                   Avec CONFIG_LCD_RGB_ISR_IRAM_SAFE=y il provoque un
 *                   redémarrage watchdog (`rst:0x8 TG1WDT_SYS_RST`) dès la
 *                   première seconde d'écriture flash ; sans lui, l'image
 *                   défile ET garde un décalage VERTICAL permanent que
 *                   esp_lcd_rgb_panel_restart() ne rattrape pas.
 */
#define DN_DEFAULT_NUM_FBS 1
#define DN_DEFAULT_BOUNCE_PX 0

static esp_err_t open_nvs(nvs_open_mode_t mode, nvs_handle_t *out)
{
    esp_err_t err = nvs_open(DN_NVS_NAMESPACE, mode, out);
    if (err != ESP_OK && err != ESP_ERR_NVS_NOT_FOUND) {
        ESP_LOGW(TAG, "nvs_open(%d) a échoué : %s", mode, esp_err_to_name(err));
    }
    return err;
}

/*
 * Validation UNIQUE de bounce_px, partagée par l'écriture (`set bounce`) et par
 * la relecture au boot. C'est le point important : tant que les deux chemins ne
 * partageaient pas la même règle, une valeur pouvait être refusée à l'écriture
 * et acceptée au boot — ou l'inverse — et le piège du plafond (cf.
 * DN_BOUNCE_PX_MAX) survivait à sa propre correction, puisque dn_bootcfg_load()
 * réacceptait à chaque démarrage la valeur qui halte le CPU.
 *
 * Renvoie NULL si la valeur est acceptable, sinon la RAISON du refus, en clair.
 */
static const char *bounce_px_refus(int32_t v)
{
    if (v < 0) {
        return "valeur négative";
    }
    if (v > DN_BOUNCE_PX_MAX) {
        /* Deux tampons de v*2 octets en RAM INTERNE + DMA : au-delà du plafond
         * c'est ESP_ERR_NO_MEM au boot, donc panique, donc CPU halté par
         * CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y, donc AUCUNE console pour
         * revenir en arrière. */
        return "au-dessus du plafond de RAM interne (carte non démarrable)";
    }
    if (v != 0 && ((size_t)DN_LCD_TOTAL_PX % (size_t)v) != 0) {
        /* Le driver RGB exige que la taille du bounce buffer divise le nombre
         * de pixels de la trame — sinon la DMA se décale d'un reliquat à chaque
         * trame. On refuse ici plutôt que de laisser le driver échouer plus
         * loin avec un message obscur. */
        return "ne divise pas les pixels d'une trame";
    }
    return NULL;
}

/* Une clé peut être PRÉSENTE et illisible : mauvais type ou mauvaise longueur
 * (ESP_ERR_NVS_TYPE_MISMATCH, ESP_ERR_NVS_INVALID_LENGTH). Ne traiter que
 * ESP_OK faisait retomber sur le défaut EN SILENCE — exactement ce que
 * dn_bootcfg.h promet de ne jamais faire. ESP_ERR_NVS_NOT_FOUND, lui, est le
 * cas NORMAL d'un clone neuf : il ne mérite pas un avertissement. */
static void log_lecture_refusee(const char *cle, esp_err_t err, int defaut)
{
    if (err == ESP_OK || err == ESP_ERR_NVS_NOT_FOUND) {
        return;
    }
    ESP_LOGW(TAG, "lecture de « %s » refusée (%s) : défaut %d appliqué", cle,
             esp_err_to_name(err), defaut);
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
    esp_err_t err = nvs_get_i32(h, DN_KEY_NUM_FBS, &v);
    if (err == ESP_OK) {
        if (v >= 1 && v <= 3) {
            out->num_fbs = (int)v;
        } else {
            ESP_LOGW(TAG, "num_fbs=%ld hors de [1,3] : défaut %d appliqué", (long)v,
                     DN_DEFAULT_NUM_FBS);
        }
    } else {
        log_lecture_refusee(DN_KEY_NUM_FBS, err, DN_DEFAULT_NUM_FBS);
    }

    err = nvs_get_i32(h, DN_KEY_BOUNCE, &v);
    if (err == ESP_OK) {
        const char *refus = bounce_px_refus(v);
        if (!refus) {
            out->bounce_px = (int)v;
        } else {
            ESP_LOGW(TAG, "bounce_px=%ld refusé (%s) : défaut %d appliqué",
                     (long)v, refus, DN_DEFAULT_BOUNCE_PX);
            ESP_LOGW(TAG, "  plafond = %d px, diviseur exact de %d px de trame",
                     DN_BOUNCE_PX_MAX, DN_LCD_TOTAL_PX);
        }
    } else {
        log_lecture_refusee(DN_KEY_BOUNCE, err, DN_DEFAULT_BOUNCE_PX);
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
    const char *refus = bounce_px_refus((int32_t)bounce_px);
    if (refus) {
        ESP_LOGW(TAG, "bounce_px=%d refusé : %s", bounce_px, refus);
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

#include "dn_stimulus.h"

#include <string.h>

#include "dn_display.h"
#include "dn_measure.h"
#include "dn_patterns.h"
#include "dn_pins.h"
#include "esp_log.h"
#include "esp_partition.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "dn_stim";

/* ═══════════════════════════════════════════════════════════════════════════
 * Stimulus de TEARING (AC5)
 * ═══════════════════════════════════════════════════════════════════════════
 * Deux images maximalement contrastées, basculées aussi vite que possible.
 * DEUX MODES, et le premier a été éliminé comme instrument principal :
 *
 *   `flip` — bascule NOIR plein / BLANC plein, la lecture littérale de l'AC.
 *     ⛔ ÉLIMINÉ comme instrument principal, avec son symptôme : à 33,6 Hz de
 *     bascule contre 37,40 Hz de rafraîchissement, l'écran « clignote
 *     violemment » et le papillotement MASQUE le déchirement qu'on cherche.
 *     L'observation rendue a été « je distingue une barre qui descend mais pas
 *     uniforme » — c'est-à-dire du tearing, mais noyé. Un instrument dont le
 *     bruit propre couvre le signal ne se garde pas. Il reste disponible parce
 *     qu'il correspond au texte de l'AC, et parce qu'il charge le pipeline de
 *     la même façon.
 *
 *   `on` (RETENU) — BARRE VERTICALE de 64 px qui balaie horizontalement, sur
 *     fond noir. C'est le test canonique du déchirement : quand la DMA change
 *     de contenu en cours de balayage, l'arête verticale de la barre se brise
 *     en TRANCHES horizontales décalées les unes des autres — un escalier, pas
 *     une barre. Le fond restant noir, il n'y a aucun papillotement plein
 *     écran pour masquer l'observation. La trame entière est redessinée à
 *     chaque pas, donc la charge sur le pipeline est la même.
 * ═══════════════════════════════════════════════════════════════════════════ */

static volatile bool s_tear_run;
static volatile dn_tear_mode_t s_tear_mode;
static TaskHandle_t s_tear_task;
static volatile double s_tear_hz;
static volatile int64_t s_tear_frame_us;

#define DN_TEAR_BAR_W 64
#define DN_TEAR_STEP 27 /* px par trame ; premier avec 480 -> pas de battement */

static void tear_task(void *arg)
{
    (void)arg;
    /* Deux compteurs distincts, et ce n'est pas du zèle : `frames` est remis à
     * zéro à chaque fenêtre d'une seconde pour calculer la cadence. S'en servir
     * aussi comme position ferait SAUTER la barre une fois par seconde — un
     * artefact de l'instrument qu'on prendrait pour une trame perdue. */
    uint32_t frames = 0; /* fenêtre de mesure de cadence */
    uint32_t step = 0;   /* position, monotone depuis le démarrage */
    int64_t t_window = esp_timer_get_time();

    while (s_tear_run) {
        int64_t t0 = esp_timer_get_time();
        uint16_t *buf = dn_display_draw_buffer();

        if (s_tear_mode == DN_TEAR_FLIP) {
            uint16_t fond = (step & 1) ? 0xFFFF : 0x0000;
            uint16_t barre = (step & 1) ? 0x0000 : 0xFFFF;
            dn_pattern_fill(buf, fond);
            int y = (int)((step * 23) % (DN_LCD_V_RES - 48));
            for (int yy = y; yy < y + 48; yy++) {
                uint16_t *row = buf + (size_t)yy * DN_LCD_H_RES;
                for (int xx = 0; xx < DN_LCD_H_RES; xx++) {
                    row[xx] = barre;
                }
            }
        } else {
            /* Barre VERTICALE blanche qui balaie sur fond noir. L'arête
             * verticale est le détecteur : brisée en tranches => tearing. */
            int x0 = (int)((step * DN_TEAR_STEP) % DN_LCD_H_RES);
            dn_pattern_fill(buf, 0x0000);
            for (int yy = 0; yy < DN_LCD_V_RES; yy++) {
                uint16_t *row = buf + (size_t)yy * DN_LCD_H_RES;
                for (int k = 0; k < DN_TEAR_BAR_W; k++) {
                    row[(x0 + k) % DN_LCD_H_RES] = 0xFFFF;
                }
            }
        }

        /* DEUX rendez-vous, et il faut LES DEUX — chacun pris seul laisse un
         * escalier résiduel, mesuré :
         *   - VSYNC seul  : escalier sur la moitié de la barre ;
         *   - fb_complete seul : escalier sur les 15 % du haut.
         * 1. attendre le VSYNC place la bascule DANS le retour vertical, quand
         *    la dalle n'affiche rien — sinon le lien DMA change au milieu du
         *    balayage, `draw_bitmap` ne différant rien ;
         * 2. attendre ensuite `on_frame_buf_complete` garantit que la boucle ne
         *    repart pas dessiner dans un tampon que la DMA lit encore. */
        if (s_tear_mode == DN_TEAR_SYNC_VSYNC || s_tear_mode == DN_TEAR_SYNC_BOTH) {
            dn_measure_wait_vsync(100);
        }
        dn_display_present();
        if (s_tear_mode == DN_TEAR_SYNC_FBDONE || s_tear_mode == DN_TEAR_SYNC_BOTH) {
            dn_measure_wait_frame_done(100);
        }
        s_tear_frame_us = esp_timer_get_time() - t0;
        step++;
        frames++;

        int64_t now = esp_timer_get_time();
        if (now - t_window >= 1000000) {
            s_tear_hz = (double)frames * 1000000.0 / (double)(now - t_window);
            frames = 0;
            t_window = now;
        }
        /* Un yield de 1 tick (1 ms à CONFIG_FREERTOS_HZ=1000) : sans lui, la
         * tâche affamerait le watchdog de son cœur. C'est le seul frein — la
         * cadence reste dominée par le temps de remplissage. */
        vTaskDelay(1);
    }
    s_tear_task = NULL;
    vTaskDelete(NULL);
}

esp_err_t dn_stim_tear_start(dn_tear_mode_t mode)
{
    if (s_tear_run) {
        return ESP_ERR_INVALID_STATE;
    }
    s_tear_run = true;
    s_tear_mode = mode;
    s_tear_hz = 0.0;
    if (xTaskCreatePinnedToCore(tear_task, "dn_tear", 4096, NULL, 4, &s_tear_task,
                                1) != pdPASS) {
        s_tear_run = false;
        return ESP_ERR_NO_MEM;
    }
    ESP_LOGI(TAG,
             "stimulus TEARING démarré (num_fbs=%d). Écrire dans le "
             "framebuffer VISIBLE (num_fbs=1) est le TÉMOIN POSITIF : le "
             "déchirement DOIT s'y voir, sinon l'instrument est invalide.",
             dn_display_num_fbs());
    return ESP_OK;
}

void dn_stim_tear_stop(void)
{
    if (!s_tear_run) {
        return;
    }
    s_tear_run = false;
    /* Attendre la sortie de la tâche : sinon un `scene x` juste après
     * écraserait l'écran pendant que la tâche dessine encore. */
    for (int i = 0; i < 200 && s_tear_task; i++) {
        vTaskDelay(pdMS_TO_TICKS(5));
    }
    ESP_LOGI(TAG, "stimulus TEARING arrêté (cadence atteinte : %.1f Hz)", s_tear_hz);
}

bool dn_stim_tear_running(void) { return s_tear_run; }

void dn_stim_tear_stats(double *out_hz, int64_t *out_frame_us)
{
    if (out_hz) {
        *out_hz = s_tear_hz;
    }
    if (out_frame_us) {
        *out_frame_us = s_tear_frame_us;
    }
}

/* ═══════════════════════════════════════════════════════════════════════════
 * Stimulus d'ÉCRITURE FLASH (AC6)
 * ═══════════════════════════════════════════════════════════════════════════
 * Flash et PSRAM partagent le contrôleur : toute écriture flash suspend le
 * cache, donc le refill de la DMA d'affichage. C'est le mécanisme annoncé du
 * scintillement.
 *
 * ⛔ On écrit EXCLUSIVEMENT dans la partition `stimulus`, sous-type 0x41,
 *    prévue pour être sacrifiée. Ni `nvs` (dont la corruption coûterait un
 *    reflash complet), ni `factory`.
 * ═══════════════════════════════════════════════════════════════════════════ */

static volatile bool s_flash_run;
static TaskHandle_t s_flash_task;
static volatile uint32_t s_flash_sectors;
static volatile uint64_t s_flash_bytes;
static volatile double s_flash_rate;

#define DN_STIM_SECTOR 4096

static void flash_task(void *arg)
{
    (void)arg;
    const esp_partition_t *part = esp_partition_find_first(
        ESP_PARTITION_TYPE_DATA, (esp_partition_subtype_t)0x41, "stimulus");
    if (!part) {
        ESP_LOGE(TAG, "partition « stimulus » introuvable — stimulus flash annulé");
        s_flash_run = false;
        s_flash_task = NULL;
        vTaskDelete(NULL);
        return;
    }

    static uint8_t motif[DN_STIM_SECTOR];
    for (int i = 0; i < DN_STIM_SECTOR; i++) {
        motif[i] = (uint8_t)(i * 7 + 3);
    }

    size_t offset = 0;
    int64_t t_window = esp_timer_get_time();
    uint64_t bytes_window = 0;

    ESP_LOGI(TAG,
             "stimulus FLASH démarré : effacement+écriture de secteurs de "
             "%d o, en boucle, sur la partition « stimulus » (%lu o à "
             "0x%06lx), sans pause entre deux secteurs.",
             DN_STIM_SECTOR, (unsigned long)part->size,
             (unsigned long)part->address);

    while (s_flash_run) {
        esp_err_t err = esp_partition_erase_range(part, offset, DN_STIM_SECTOR);
        if (err == ESP_OK) {
            err = esp_partition_write(part, offset, motif, DN_STIM_SECTOR);
        }
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "écriture flash à 0x%x refusée : %s", (unsigned)offset,
                     esp_err_to_name(err));
            break;
        }
        s_flash_sectors++;
        s_flash_bytes += DN_STIM_SECTOR;
        bytes_window += DN_STIM_SECTOR;

        offset += DN_STIM_SECTOR;
        if (offset + DN_STIM_SECTOR > part->size) {
            offset = 0;
        }

        int64_t now = esp_timer_get_time();
        if (now - t_window >= 1000000) {
            s_flash_rate = (double)bytes_window * 1000000.0 / (double)(now - t_window);
            bytes_window = 0;
            t_window = now;
        }
        /* 1 tick de répit : les tâches de moindre priorité doivent pouvoir
         * tourner, sinon c'est le watchdog qui interrompt la mesure. */
        vTaskDelay(1);
    }
    s_flash_task = NULL;
    vTaskDelete(NULL);
}

esp_err_t dn_stim_flash_start(void)
{
    if (s_flash_run) {
        return ESP_ERR_INVALID_STATE;
    }
    s_flash_run = true;
    s_flash_sectors = 0;
    s_flash_bytes = 0;
    s_flash_rate = 0.0;
    if (xTaskCreatePinnedToCore(flash_task, "dn_flash", 4096, NULL, 3,
                                &s_flash_task, 0) != pdPASS) {
        s_flash_run = false;
        return ESP_ERR_NO_MEM;
    }
    return ESP_OK;
}

void dn_stim_flash_stop(void)
{
    if (!s_flash_run) {
        return;
    }
    s_flash_run = false;
    for (int i = 0; i < 200 && s_flash_task; i++) {
        vTaskDelay(pdMS_TO_TICKS(5));
    }
    ESP_LOGI(TAG,
             "stimulus FLASH arrêté : %lu secteurs, %llu o écrits, "
             "débit soutenu %.0f o/s",
             (unsigned long)s_flash_sectors, (unsigned long long)s_flash_bytes,
             s_flash_rate);
}

bool dn_stim_flash_running(void) { return s_flash_run; }

void dn_stim_flash_stats(uint32_t *out_sectors, uint64_t *out_bytes,
                         double *out_bytes_per_s)
{
    if (out_sectors) {
        *out_sectors = s_flash_sectors;
    }
    if (out_bytes) {
        *out_bytes = s_flash_bytes;
    }
    if (out_bytes_per_s) {
        *out_bytes_per_s = s_flash_rate;
    }
}

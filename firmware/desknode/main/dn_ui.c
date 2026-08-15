#include "dn_ui.h"

#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>

#include "dn_asset.h"
#include "dn_display.h"
#include "dn_measure.h"
#include "dn_pins.h"
#include "esp_check.h"
#include "esp_heap_caps.h"
#include "esp_lcd_panel_ops.h"
#include "esp_log.h"
#include "esp_lvgl_port.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "dn_ui";

/* ── Géométrie du label vivant ────────────────────────────────────────────── */
/*
 * LARGEUR FIXE, et c'est une exigence d'AC2, pas une préférence esthétique.
 * `lv_label_set_text()` invalide la zone du label ; si cette zone changeait avec
 * la longueur du texte (« 9 s » puis « 10 s »), l'aire flushée mesurée par AC3
 * varierait pour une raison qui n'a rien à voir avec le rendu, et un texte plus
 * long pourrait déclencher un relayout du parent — donc une invalidation bien
 * plus grande, une fois sur dix. Largeur figée + LV_LABEL_LONG_MODE_CLIP :
 * l'aire invalidée est la même à chaque mise à jour, quoi qu'on écrive.
 */
#define DN_UI_LABEL_W 260
#define DN_UI_LABEL_H 44

/* Barre du stimulus adverse : verticale, pleine hauteur, qui balaie de gauche à
 * droite. Ce sens-là est choisi EXPRÈS : la dalle est balayée ligne par ligne du
 * haut vers le bas, donc un déchirement coupe la barre HORIZONTALEMENT et décale
 * les deux moitiés — un artefact que l'œil lit sans ambiguïté, contrairement à
 * un scintillement qu'on peut se raconter. */
#define DN_UI_BAR_W 24
#define DN_UI_ANIM_MS_MIN 200
#define DN_UI_ANIM_MS_MAX 10000
#define DN_UI_ANIM_MS_DEFAUT 2000

/* ── État ─────────────────────────────────────────────────────────────────── */

static lv_display_t *s_disp;
static esp_lcd_panel_handle_t s_panel;
static lv_obj_t *s_img;
static lv_obj_t *s_label;
static lv_obj_t *s_bar;
static lv_timer_t *s_timer;
static lv_image_dsc_t s_bg_dsc;
static uint16_t *s_bg_psram;      /* copie PSRAM du fond, NULL si mmap flash */
static esp_err_t s_asset_err = ESP_OK;

static dn_vsync_sub_t s_vsync_sub = -1;
static volatile dn_flush_sync_t s_sync = DN_FLUSH_SYNC_VSYNC;
static volatile bool s_first_frame;
static volatile bool s_label_shown = true;
static volatile bool s_anim_on;
static volatile bool s_active = true;
static int s_anim_ms = DN_UI_ANIM_MS_DEFAUT;

static int s_draw_lines;
static bool s_draw_psram;
static size_t s_int_avant, s_int_apres, s_psram_avant, s_psram_apres;

/* Compteurs — 32 bits, écrits par la tâche LVGL, lus par le REPL. Voir dn_ui.h
 * pour ce que cette absence de verrou garantit et ce qu'elle ne garantit pas. */
static volatile uint32_t s_n_flush, s_n_cycles, s_px, s_copie_us, s_attente_us;
static volatile uint32_t s_max_px, s_max_copie_us, s_timeouts;

/* ── Noms des modes ───────────────────────────────────────────────────────── */

const char *dn_flush_sync_name(dn_flush_sync_t m)
{
    switch (m) {
    case DN_FLUSH_SYNC_OFF:
        return "off";
    case DN_FLUSH_SYNC_VSYNC:
        return "vsync";
    case DN_FLUSH_SYNC_FBDONE:
        return "fbdone";
    default:
        return "?";
    }
}

bool dn_flush_sync_from_name(const char *nom, dn_flush_sync_t *out)
{
    for (int i = 0; i < DN_FLUSH_SYNC_COUNT; i++) {
        if (strcasecmp(nom, dn_flush_sync_name((dn_flush_sync_t)i)) == 0) {
            *out = (dn_flush_sync_t)i;
            return true;
        }
    }
    return false;
}

/* ── Le flush ─────────────────────────────────────────────────────────────── */

static void dn_ui_flush(lv_display_t *disp, const lv_area_t *area, uint8_t *px_map)
{
    uint32_t w = (uint32_t)(area->x2 - area->x1 + 1);
    uint32_t h = (uint32_t)(area->y2 - area->y1 + 1);

    /*
     * L'ATTENTE ET LA COPIE SONT CHRONOMÉTRÉES SÉPARÉMENT — sinon le coût annoncé
     * du flush inclurait le temps passé à ne rien faire, et « le rafraîchissement
     * partiel coûte 27 ms » se lirait comme un problème de bande passante alors
     * que ce serait la synchro qui attend sa trame. Deux chiffres, deux causes.
     */
    int64_t t0 = esp_timer_get_time();
    switch (s_sync) {
    case DN_FLUSH_SYNC_VSYNC:
        /* On veut le PROCHAIN retour vertical : vider d'abord. Rien ici ne
         * provoque l'événement, donc l'idiome « vider puis attendre » est le bon
         * (celui de dn_measure_wait_vsync, pas celui de wait_frame_done). */
        dn_measure_vsync_flush(s_vsync_sub);
        if (!dn_measure_vsync_wait(s_vsync_sub, 100)) {
            s_timeouts++;
        }
        break;
    case DN_FLUSH_SYNC_FBDONE:
        dn_measure_arm_frame_done();
        if (!dn_measure_wait_frame_done(100)) {
            s_timeouts++;
        }
        break;
    case DN_FLUSH_SYNC_OFF:
    default:
        break;
    }
    int64_t t1 = esp_timer_get_time();

    /* ⚠️ `esp_lcd_panel_draw_bitmap` prend des bornes de fin EXCLUSIVES, alors
     * que `lv_area_t` a des bornes INCLUSIVES. Le +1 n'est pas une marge : sans
     * lui, la dernière colonne et la dernière ligne de chaque zone sale ne
     * seraient jamais recopiées, et le défaut se verrait comme un liseré rémanent
     * d'un pixel — le genre d'artefact qu'on attribue à la dalle. */
    esp_lcd_panel_draw_bitmap(s_panel, area->x1, area->y1, area->x2 + 1,
                              area->y2 + 1, px_map);
    int64_t t2 = esp_timer_get_time();

    uint32_t px = w * h;
    uint32_t copie = (uint32_t)(t2 - t1);
    s_n_flush++;
    s_px += px;
    s_copie_us += copie;
    s_attente_us += (uint32_t)(t1 - t0);
    if (px > s_max_px) {
        s_max_px = px;
    }
    if (copie > s_max_copie_us) {
        s_max_copie_us = copie;
    }
    if (lv_display_flush_is_last(disp)) {
        s_n_cycles++;
        s_first_frame = true;
    }

    lv_display_flush_ready(disp);
}

/* ── La scène ─────────────────────────────────────────────────────────────── */

static void label_tick(lv_timer_t *t)
{
    (void)t;
    if (!s_label) {
        return;
    }
    /*
     * TEMPS ABSOLU, jamais un compteur incrémenté. Un `s++` dans un timer de
     * 1 000 ms dérive de tout ce que le timer prend de retard — et il en prend,
     * puisque le cycle LVGL tourne à 33 ms et qu'un flush synchronisé peut
     * mordre dessus. Ici la valeur affichée est dérivée de l'horloge : elle est
     * juste même si le timer se réveille en retard, et elle reste confrontable au
     * battement `up N s` du log, qui est lui aussi une cadence indépendante.
     */
    uint32_t s = (uint32_t)(esp_timer_get_time() / 1000000);
    char buf[24];
    snprintf(buf, sizeof(buf), "%" PRIu32 " s", s);
    lv_label_set_text(s_label, buf);
}

static void bar_set_x(void *var, int32_t v)
{
    lv_obj_set_x((lv_obj_t *)var, v);
}

/* Détruit et reconstruit toute la scène. Idempotent, et appelé aussi bien à
 * l'init qu'au changement de source de fond : reconstruire coûte quelques
 * millisecondes une fois, là où permuter le pointeur d'une image déjà posée
 * obligerait à raisonner sur le cache d'images de LVGL. Un geste d'opérateur ne
 * mérite pas cette subtilité-là. */
static void build_scene(void)
{
    lv_obj_t *scr = lv_screen_active();
    lv_obj_clean(scr);
    s_img = NULL;
    s_label = NULL;
    s_bar = NULL;

    lv_obj_set_style_bg_color(scr, lv_color_black(), 0);
    lv_obj_set_style_bg_opa(scr, LV_OPA_COVER, 0);
    /* Pas de barre de défilement sur un écran qui ne défile pas : sinon LVGL en
     * dessine une au moindre objet qui touche le bord, et elle s'invaliderait
     * avec lui. */
    lv_obj_set_scrollbar_mode(scr, LV_SCROLLBAR_MODE_OFF);
    lv_obj_clear_flag(scr, LV_OBJ_FLAG_SCROLLABLE);

    const uint16_t *px = s_bg_psram ? (const uint16_t *)s_bg_psram
                                    : dn_asset_pixels();
    if (px) {
        s_bg_dsc.header.magic = LV_IMAGE_HEADER_MAGIC;
        /* RGB565 NATIF, NON COMPRESSÉ : le format du framebuffer et celui de
         * l'asset sont les mêmes, donc chaque re-blit du fond sous le label est
         * une COPIE et non un décodage. C'est la condition qui rend le coût
         * d'AC3 prévisible. */
        s_bg_dsc.header.cf = LV_COLOR_FORMAT_RGB565;
        s_bg_dsc.header.w = DN_LCD_H_RES;
        s_bg_dsc.header.h = DN_LCD_V_RES;
        s_bg_dsc.header.stride = DN_LCD_H_RES * 2;
        s_bg_dsc.data_size = DN_FB_BYTES;
        s_bg_dsc.data = (const uint8_t *)px;

        s_img = lv_image_create(scr);
        lv_image_set_src(s_img, &s_bg_dsc);
        lv_obj_set_pos(s_img, 0, 0);
    } else {
        /*
         * ── LE PANNEAU « ASSET ABSENT » SURVIT À L'INTÉGRATION (AC1) ─────────
         * Il existait en dn1-2, dessiné à la main dans le framebuffer par
         * dn_patterns. LVGL redessine l'écran entier au premier cycle : ce
         * panneau-là aurait été effacé sans bruit, et une partition d'assets
         * corrompue aurait produit un écran noir silencieux — exactement ce que
         * dn_asset.h promet de ne jamais faire. On le REDESSINE donc en LVGL.
         */
        lv_obj_set_style_bg_color(scr, lv_color_hex(0x7f0000), 0);
        lv_obj_t *t = lv_label_create(scr);
        lv_obj_set_style_text_font(t, &lv_font_montserrat_28, 0);
        lv_obj_set_style_text_color(t, lv_color_white(), 0);
        lv_label_set_text(t, "ASSET ABSENT");
        lv_obj_align(t, LV_ALIGN_CENTER, 0, -30);

        lv_obj_t *r = lv_label_create(scr);
        lv_obj_set_style_text_color(r, lv_color_white(), 0);
        lv_label_set_text(r, esp_err_to_name(s_asset_err));
        lv_obj_align(r, LV_ALIGN_CENTER, 0, 20);
    }

    /* Le label vivant, PAR-DESSUS le fond. */
    s_label = lv_label_create(scr);
    lv_obj_set_style_text_font(s_label, &lv_font_montserrat_28, 0);
    lv_obj_set_style_text_color(s_label, lv_color_white(), 0);
    /* Fond du label TRANSPARENT, délibérément. Un aplat opaque derrière le texte
     * supprimerait le re-blit du fond sous la zone invalidée — c'est-à-dire
     * exactement le travail qu'AC3 veut chiffrer et qu'AC2 veut voir ne pas
     * frémir. Le rendre opaque rendrait la mesure facile et fausse. */
    lv_obj_set_style_bg_opa(s_label, LV_OPA_TRANSP, 0);
    lv_obj_set_style_text_align(s_label, LV_TEXT_ALIGN_CENTER, 0);
    lv_label_set_long_mode(s_label, LV_LABEL_LONG_MODE_CLIP);
    lv_obj_set_size(s_label, DN_UI_LABEL_W, DN_UI_LABEL_H);
    lv_obj_align(s_label, LV_ALIGN_CENTER, 0, 0);
    lv_label_set_text(s_label, "0 s");
    if (!s_label_shown) {
        lv_obj_add_flag(s_label, LV_OBJ_FLAG_HIDDEN);
    }
}

/* ── Init ─────────────────────────────────────────────────────────────────── */

esp_err_t dn_ui_init(const dn_bootcfg_t *cfg, esp_err_t asset_err)
{
    ESP_RETURN_ON_FALSE(cfg, ESP_ERR_INVALID_ARG, TAG, "cfg NULL");
    s_asset_err = asset_err;
    s_panel = dn_display_panel();
    ESP_RETURN_ON_FALSE(s_panel, ESP_ERR_INVALID_STATE, TAG,
                        "panneau absent — dn_display_init() n'a pas tourné");

    s_draw_lines = cfg->draw_lines;
    s_draw_psram = cfg->draw_psram != 0;

    s_int_avant = dn_measure_internal_free();
    s_psram_avant = dn_measure_psram_free();

    /* L'abonnement vsync doit exister AVANT le premier flush : la tâche LVGL
     * démarre dès lvgl_port_init(), et le premier cycle peut tomber tout de
     * suite. Un sub à -1 ferait silencieusement retomber la synchro en mode
     * « off » — donc une mesure d'AC4 étiquetée « vsync » sans aucune synchro. */
    s_vsync_sub = dn_measure_vsync_subscribe("flush");
    ESP_RETURN_ON_FALSE(s_vsync_sub >= 0, ESP_ERR_NO_MEM, TAG,
                        "abonnement vsync du flush refusé");

    lvgl_port_cfg_t port_cfg = ESP_LVGL_PORT_INIT_CONFIG();
    /* Défauts du portage conservés (prio 4, pile 7168, tick 5 ms), à UNE
     * exception près : la tâche est épinglée au CŒUR 1. Raison : le REPL, la
     * console USB et les tâches de mesure vivent sur le cœur 0 ; y ajouter le
     * rendu ferait que `cpu` mesurerait la somme des deux sur un seul cœur et
     * qu'une commande tapée pendant une mesure la décalerait. Séparer les deux
     * rend la charge d'AC8 attribuable. */
    port_cfg.task_affinity = 1;
    ESP_RETURN_ON_ERROR(lvgl_port_init(&port_cfg), TAG, "lvgl_port_init");

    lvgl_port_display_cfg_t disp_cfg = {
        /* io_handle NULL : c'est le bus 3-wire d'INITIALISATION, il ne transporte
         * aucun pixel. Le portage ne le lit que dans lvgl_port_add_disp() (voie
         * SPI/I80), jamais dans la voie RGB. */
        .io_handle = NULL,
        .panel_handle = s_panel,
        .control_handle = NULL,
        .buffer_size = (uint32_t)(DN_LCD_H_RES * s_draw_lines),
        /* Pas de second draw buffer : notre flush est SYNCHRONE (il rend la main
         * une fois la copie faite), donc LVGL n'aurait rien à rendre en parallèle
         * pendant qu'on copie. Le second tampon coûterait autant que le premier
         * pour zéro recouvrement. À reconsidérer seulement si le flush devient
         * asynchrone — ce qu'il n'est pas ici. */
        .double_buffer = false,
        .hres = DN_LCD_H_RES,
        .vres = DN_LCD_V_RES,
        .monochrome = false,
        .color_format = LV_COLOR_FORMAT_RGB565,
        .flags = {
            /* DMA seulement quand le tampon est en RAM interne : sur ESP32-S3 la
             * PSRAM n'est pas DMA-capable pour ce driver, et le portage refuse
             * explicitement la combinaison des deux. */
            .buff_dma = s_draw_psram ? 0 : 1,
            .buff_spiram = s_draw_psram ? 1 : 0,
            .sw_rotate = 0,
            /* Pas d'inversion d'octets : les pixels sont lus par la DMA depuis la
             * PSRAM en 16 bits natifs. `swap_bytes` est un réglage de bus SÉRIE
             * (SPI/I80) — le poser ici afficherait des couleurs permutées. */
            .swap_bytes = 0,
            .full_refresh = 0,
            .direct_mode = 0,
        },
    };
    const lvgl_port_display_rgb_cfg_t rgb_cfg = {
        .flags = {
            .bb_mode = 0, /* le bounce buffer est DISQUALIFIÉ (watchdog) — dn1-2 */
            /* 0 IMPOSÉ : le portage exige num_fbs>=2 pour cette option
             * (esp_lvgl_port_disp.c:367) et la config arbitrée est num_fbs=1. */
            .avoid_tearing = 0,
        },
    };

    s_disp = lvgl_port_add_disp_rgb(&disp_cfg, &rgb_cfg);
    ESP_RETURN_ON_FALSE(s_disp, ESP_FAIL, TAG, "lvgl_port_add_disp_rgb");

    if (!lvgl_port_lock(1000)) {
        ESP_LOGE(TAG, "verrou LVGL non pris en 1 s");
        return ESP_ERR_TIMEOUT;
    }
    /*
     * ON REMPLACE LE FLUSH DU PORTAGE. Le sien, en mode partiel, appelle
     * draw_bitmap et rend la main sans attendre quoi que ce soit
     * (esp_lvgl_port_disp.c:758) — il n'y a donc RIEN à synchroniser dedans, et
     * rien à instrumenter. Le nôtre porte les deux.
     * ⚠️ Les autres branchements du portage (invalidation, réveil de tâche,
     *    changement de résolution) sont CONSERVÉS : on ne remplace que le flush.
     */
    lv_display_set_flush_cb(s_disp, dn_ui_flush);
    build_scene();
    s_timer = lv_timer_create(label_tick, 1000, NULL);
    lvgl_port_unlock();

    s_int_apres = dn_measure_internal_free();
    s_psram_apres = dn_measure_psram_free();

    ESP_LOGI(TAG,
             "LVGL %d.%d.%d prêt : rendu PARTIEL, draw buffer %d x %d px "
             "(%d o) en %s",
             LVGL_VERSION_MAJOR, LVGL_VERSION_MINOR, LVGL_VERSION_PATCH,
             DN_LCD_H_RES, s_draw_lines, DN_LCD_H_RES * s_draw_lines * 2,
             s_draw_psram ? "PSRAM" : "RAM interne DMA");
    ESP_LOGI(TAG, "  synchro du flush : %s", dn_flush_sync_name(s_sync));
    ESP_LOGI(TAG,
             "  coût en tas : RAM interne %u -> %u o (%d), PSRAM %u -> %u o (%d)",
             (unsigned)s_int_avant, (unsigned)s_int_apres,
             (int)((long)s_int_avant - (long)s_int_apres),
             (unsigned)s_psram_avant, (unsigned)s_psram_apres,
             (int)((long)s_psram_avant - (long)s_psram_apres));
    ESP_LOGW(TAG,
             "  ⚠️ ce delta N'INCLUT PAS les %d Ko statiques du tas de LVGL "
             "(LV_MEM_SIZE_KILOBYTES, réservés dans le .bss au link). "
             "L'instrument de CE coût-là est `ui`, qui imprime lv_mem_monitor().",
             CONFIG_LV_MEM_SIZE_KILOBYTES);
    return ESP_OK;
}

/* ── Accès ────────────────────────────────────────────────────────────────── */

bool dn_ui_first_frame_done(void) { return s_first_frame; }

bool dn_ui_wait_first_frame(uint32_t timeout_ms)
{
    /*
     * Sondage à 5 ms plutôt qu'un sémaphore : c'est appelé UNE FOIS, au boot,
     * juste avant d'allumer le rétroéclairage. Un sémaphore de plus donné depuis
     * le flush coûterait un test dans le chemin chaud pour une attente qui a lieu
     * une seule fois dans la vie du firmware.
     */
    int64_t fin = esp_timer_get_time() + (int64_t)timeout_ms * 1000;
    while (!s_first_frame) {
        if (esp_timer_get_time() > fin) {
            return false;
        }
        vTaskDelay(pdMS_TO_TICKS(5));
    }
    return true;
}

void dn_ui_get_stats(dn_flush_stats_t *out)
{
    if (!out) {
        return;
    }
    out->flushes = s_n_flush;
    out->cycles = s_n_cycles;
    out->px = s_px;
    out->copie_us = s_copie_us;
    out->attente_us = s_attente_us;
    out->max_px = s_max_px;
    out->max_copie_us = s_max_copie_us;
    out->timeouts = s_timeouts;
}

void dn_ui_reset_stats(void)
{
    s_n_flush = 0;
    s_n_cycles = 0;
    s_px = 0;
    s_copie_us = 0;
    s_attente_us = 0;
    s_max_px = 0;
    s_max_copie_us = 0;
    s_timeouts = 0;
}

dn_flush_sync_t dn_ui_get_sync(void) { return s_sync; }
void dn_ui_set_sync(dn_flush_sync_t mode) { s_sync = mode; }

void dn_ui_force_full_redraw(void)
{
    if (!lvgl_port_lock(1000)) {
        ESP_LOGE(TAG, "verrou LVGL non pris");
        return;
    }
    lv_obj_invalidate(lv_screen_active());
    lvgl_port_unlock();
}

void dn_ui_label_show(bool on)
{
    if (!lvgl_port_lock(1000)) {
        ESP_LOGE(TAG, "verrou LVGL non pris");
        return;
    }
    s_label_shown = on;
    if (s_label) {
        if (on) {
            lv_obj_clear_flag(s_label, LV_OBJ_FLAG_HIDDEN);
        } else {
            lv_obj_add_flag(s_label, LV_OBJ_FLAG_HIDDEN);
        }
    }
    lvgl_port_unlock();
}

bool dn_ui_label_shown(void) { return s_label_shown; }

esp_err_t dn_ui_anim(bool on, int periode_ms)
{
    if (on) {
        if (periode_ms < DN_UI_ANIM_MS_MIN || periode_ms > DN_UI_ANIM_MS_MAX) {
            return ESP_ERR_INVALID_ARG;
        }
    }
    if (!lvgl_port_lock(1000)) {
        return ESP_ERR_TIMEOUT;
    }
    if (on) {
        if (!s_bar) {
            s_bar = lv_obj_create(lv_screen_active());
            lv_obj_remove_style_all(s_bar);
            lv_obj_set_size(s_bar, DN_UI_BAR_W, DN_LCD_V_RES);
            lv_obj_set_style_bg_color(s_bar, lv_color_hex(0xffffff), 0);
            lv_obj_set_style_bg_opa(s_bar, LV_OPA_COVER, 0);
            lv_obj_set_pos(s_bar, 0, 0);
        }
        lv_anim_t a;
        lv_anim_init(&a);
        lv_anim_set_var(&a, s_bar);
        lv_anim_set_exec_cb(&a, bar_set_x);
        lv_anim_set_values(&a, 0, DN_LCD_H_RES - DN_UI_BAR_W);
        lv_anim_set_duration(&a, (uint32_t)periode_ms);
        /* Aller-retour : un retour instantané au bord gauche produirait un saut
         * dont l'artefact ressemble à un déchirement. On ne veut pas fabriquer le
         * symptôme qu'on cherche à observer. */
        lv_anim_set_reverse_duration(&a, (uint32_t)periode_ms);
        lv_anim_set_repeat_count(&a, LV_ANIM_REPEAT_INFINITE);
        lv_anim_start(&a);
        s_anim_ms = periode_ms;
        s_anim_on = true;
    } else {
        if (s_bar) {
            lv_anim_delete(s_bar, bar_set_x);
            lv_obj_delete(s_bar);
            s_bar = NULL;
            /* La barre supprimée laisse une zone sale : sans invalidation
             * explicite, la dernière position resterait imprimée dans le
             * framebuffer, et on la prendrait pour un artefact de rémanence. */
            lv_obj_invalidate(lv_screen_active());
        }
        s_anim_on = false;
    }
    lvgl_port_unlock();
    return ESP_OK;
}

bool dn_ui_anim_running(void) { return s_anim_on; }

esp_err_t dn_ui_bg_psram(bool on)
{
    if (on == (s_bg_psram != NULL)) {
        return ESP_OK;
    }
    if (on) {
        const uint16_t *src = dn_asset_pixels();
        if (!src) {
            ESP_LOGE(TAG, "pas d'asset à copier — la source reste inchangée");
            return ESP_ERR_NOT_FOUND;
        }
        uint16_t *buf = heap_caps_malloc(DN_FB_BYTES, MALLOC_CAP_SPIRAM);
        if (!buf) {
            ESP_LOGE(TAG, "PSRAM insuffisante pour %u o", (unsigned)DN_FB_BYTES);
            return ESP_ERR_NO_MEM;
        }
        int64_t t0 = esp_timer_get_time();
        memcpy(buf, src, DN_FB_BYTES);
        int64_t dt = esp_timer_get_time() - t0;
        ESP_LOGI(TAG, "fond copié flash -> PSRAM : %u o en %lld us (%.2f Mo/s)",
                 (unsigned)DN_FB_BYTES, (long long)dt,
                 dt > 0 ? (double)DN_FB_BYTES / (double)dt : 0.0);
        s_bg_psram = buf;
    } else {
        uint16_t *old = s_bg_psram;
        s_bg_psram = NULL;
        /* La scène est reconstruite AVANT la libération, sinon LVGL garderait un
         * instant un descripteur pointant sur de la mémoire rendue. */
        if (lvgl_port_lock(1000)) {
            build_scene();
            lvgl_port_unlock();
        }
        heap_caps_free(old);
        return ESP_OK;
    }

    if (!lvgl_port_lock(1000)) {
        return ESP_ERR_TIMEOUT;
    }
    build_scene();
    lvgl_port_unlock();
    return ESP_OK;
}

bool dn_ui_bg_is_psram(void) { return s_bg_psram != NULL; }

esp_err_t dn_ui_pause(void)
{
    esp_err_t err = lvgl_port_stop();
    if (err == ESP_OK) {
        s_active = false;
    }
    return err;
}

esp_err_t dn_ui_resume(void)
{
    esp_err_t err = lvgl_port_resume();
    if (err == ESP_OK) {
        s_active = true;
        /* Le framebuffer a pu être réécrit pendant la pause (c'est même le seul
         * intérêt de la pause). On redessine tout, sinon LVGL croirait l'écran
         * conforme à son arbre d'objets et ne réparerait jamais. */
        dn_ui_force_full_redraw();
    }
    return err;
}

bool dn_ui_active(void) { return s_active; }

void dn_ui_log_mem(void)
{
    lv_mem_monitor_t mon;
    if (!lvgl_port_lock(1000)) {
        printf("verrou LVGL non pris\n");
        return;
    }
    lv_mem_monitor(&mon);
    lvgl_port_unlock();
    printf("tas LVGL (LV_MEM_SIZE_KILOBYTES = %d Ko, STATIQUE en .bss) :\n",
           CONFIG_LV_MEM_SIZE_KILOBYTES);
    printf("  total %" PRIu32 " o · utilisé %" PRIu32 " o (%u %%) · libre %" PRIu32
           " o\n",
           (uint32_t)mon.total_size, (uint32_t)(mon.total_size - mon.free_size),
           (unsigned)mon.used_pct, (uint32_t)mon.free_size);
    printf("  plus gros bloc libre %" PRIu32 " o · fragmentation %u %%\n",
           (uint32_t)mon.free_biggest_size, (unsigned)mon.frag_pct);
    printf("⚠️ ces octets-là sont réservés au LINK : ils n'apparaissent PAS dans\n");
    printf("   l'avant/après de `mem`. C'est le seul endroit où ils se voient.\n");
}

void dn_ui_get_cout(size_t *interne_avant, size_t *interne_apres,
                    size_t *psram_avant, size_t *psram_apres)
{
    if (interne_avant) {
        *interne_avant = s_int_avant;
    }
    if (interne_apres) {
        *interne_apres = s_int_apres;
    }
    if (psram_avant) {
        *psram_avant = s_psram_avant;
    }
    if (psram_apres) {
        *psram_apres = s_psram_apres;
    }
}

int dn_ui_draw_lines(void) { return s_draw_lines; }
bool dn_ui_draw_in_psram(void) { return s_draw_psram; }

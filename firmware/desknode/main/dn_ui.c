#include "dn_ui.h"

#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>

#include "dn_asset.h"
#include "dn_display.h"
#include "dn_measure.h"
#include "dn_pins.h"
#include "dn_recal.h"
#include "esp_cache.h"
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
static volatile dn_flush_path_t s_path = DN_FLUSH_PATH_BITMAP;
/*
 * Mode DIRECT : LVGL dessine dans les DEUX framebuffers du driver et on bascule.
 * Décidé au boot par num_fbs, jamais à chaud — les framebuffers sont alloués une
 * fois, et le mode de rendu de LVGL se fixe avec eux.
 */
static bool s_direct_mode;
static int s_affinity = -1;
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
/* Flushes NO-OP du mode direct (early return : aire comptée, aucun µs). Compté
 * À PART (revue) : les inclure au dénominateur diluait les moyennes copie/attente
 * dans le mode même qui a servi à tester l'hypothèse 5 de §10.5. */
static volatile uint32_t s_n_noop;

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

const char *dn_flush_path_name(dn_flush_path_t p)
{
    switch (p) {
    case DN_FLUSH_PATH_BITMAP:
        return "bitmap";
    case DN_FLUSH_PATH_DIRECT:
        return "direct";
    default:
        return "?";
    }
}

bool dn_flush_path_from_name(const char *nom, dn_flush_path_t *out)
{
    for (int i = 0; i < DN_FLUSH_PATH_COUNT; i++) {
        if (strcasecmp(nom, dn_flush_path_name((dn_flush_path_t)i)) == 0) {
            *out = (dn_flush_path_t)i;
            return true;
        }
    }
    return false;
}

dn_flush_path_t dn_ui_get_path(void) { return s_path; }

esp_err_t dn_ui_set_path(dn_flush_path_t p)
{
    if (p >= DN_FLUSH_PATH_COUNT) {
        return ESP_ERR_INVALID_ARG;
    }
    if (p == DN_FLUSH_PATH_DIRECT && dn_display_num_fbs() != 1) {
        /* Refus explicite plutôt que dessin dans le mauvais tampon : à plusieurs
         * framebuffers, le tampon de DESSIN n'est pas celui que la DMA lit, et
         * écrire dedans sans passer par la bascule du driver n'afficherait
         * simplement jamais rien. Un défaut silencieux de plus. */
        ESP_LOGE(TAG,
                 "chemin « direct » refusé : num_fbs=%d. Il n'a de sens qu'à UN "
                 "framebuffer, où le tampon de dessin EST le tampon visible.",
                 dn_display_num_fbs());
        return ESP_ERR_INVALID_STATE;
    }
    s_path = p;
    return ESP_OK;
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
    if (s_direct_mode && !lv_display_flush_is_last(disp)) {
        /*
         * EN MODE DIRECT, `px_map` EST L'UN DES DEUX FRAMEBUFFERS : LVGL y a
         * déjà écrit, il n'y a rien à recopier. Tant que ce n'est pas le dernier
         * appel du cycle, la seule chose à faire est de compter et de rendre la
         * main — la bascule ne se joue qu'une fois, quand tout est dessiné.
         * Rendre la trame à chaque zone sale afficherait un écran à moitié
         * rafraîchi, c'est-à-dire fabriquerait le déchirement qu'on vient
         * d'éliminer.
         */
        s_n_flush++;
        s_n_noop++;
        s_px += w * h;
        if (w * h > s_max_px) {
            s_max_px = w * h;
        }
        lv_display_flush_ready(disp);
        return;
    }

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

    if (s_direct_mode) {
        /*
         * LA BASCULE. `px_map` pointe dans l'un des framebuffers du driver, donc
         * `draw_bitmap` prend la branche « le draw buffer FAIT PARTIE du frame
         * buffer » : il ne recopie rien, il change `cur_fb_index` et réaccroche
         * la queue des liens DMA. Zéro octet copié — c'est TOUT l'intérêt du
         * double tampon, et c'est ce qui supprime l'écriture CPU dans le tampon
         * que la DMA balaie (la cause mesurée du clignotement à 1 FB).
         */
        esp_lcd_panel_draw_bitmap(s_panel, 0, 0, DN_LCD_H_RES, DN_LCD_V_RES,
                                  px_map);
        /* ⚠️ On arme le recalage NOUS-MÊMES : ce chemin court-circuite
         * `dn_display_present()`, qui est l'endroit où l'armement vit d'habitude.
         * L'oublier ici rendrait le double tampon inutilisable sous LVGL alors
         * qu'il vient d'être prouvé réparable — et le symptôme serait « ça
         * marche en `scene`, pas en LVGL », le plus trompeur qui soit. */
        dn_recal_arm();
    } else if (s_path == DN_FLUSH_PATH_DIRECT) {
        /*
         * Écriture DIRECTE dans le framebuffer visible, puis resynchronisation
         * des SEULES lignes salies. À num_fbs=1, `dn_display_draw_buffer()` rend
         * le tampon que la DMA lit : il n'y a pas de bascule à faire, donc rien
         * à demander au driver.
         *
         * Le gain visé n'est PAS la copie (elle est identique, mêmes octets)
         * mais le parcours de cache : h x 960 octets au lieu des 614 400 que
         * `draw_bitmap` resynchronise systématiquement.
         */
        uint16_t *fb = dn_display_draw_buffer();
        const uint16_t *src = (const uint16_t *)px_map;
        for (uint32_t y = 0; y < h; y++) {
            memcpy(fb + (size_t)(area->y1 + (int)y) * DN_LCD_H_RES + area->x1,
                   src + (size_t)y * w, (size_t)w * 2);
        }
        /* UNALIGNED : la première ligne sale ne tombe pas sur une frontière de
         * ligne de cache, et l'exiger ferait refuser l'appel avec
         * ESP_ERR_INVALID_ARG — le driver lui-même pose ce drapeau ici. */
        esp_cache_msync(fb + (size_t)area->y1 * DN_LCD_H_RES,
                        (size_t)h * DN_LCD_H_RES * 2,
                        ESP_CACHE_MSYNC_FLAG_DIR_C2M |
                            ESP_CACHE_MSYNC_FLAG_UNALIGNED);
    } else {
        /* ⚠️ `esp_lcd_panel_draw_bitmap` prend des bornes de fin EXCLUSIVES,
         * alors que `lv_area_t` a des bornes INCLUSIVES. Le +1 n'est pas une
         * marge : sans lui, la dernière colonne et la dernière ligne de chaque
         * zone sale ne seraient jamais recopiées, et le défaut se verrait comme
         * un liseré rémanent d'un pixel — le genre d'artefact qu'on attribue à
         * la dalle. */
        esp_lcd_panel_draw_bitmap(s_panel, area->x1, area->y1, area->x2 + 1,
                                  area->y2 + 1, px_map);
    }
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
    /* ⚠️ L'ombre suit la réalité (revue). `lv_obj_clean` vient de détruire la
     * barre ET son animation : laisser `s_anim_on` à vrai ferait annoncer
     * « stimulus EN COURS » par `ui`, `anim` et l'étiquette de `fps` — une
     * étiquette de mesure FAUSSE, la classe de défaut que ce firmware traque.
     * L'opérateur relance `anim on` s'il le veut ; on ne recrée pas la barre
     * dans son dos. */
    if (s_anim_on) {
        s_anim_on = false;
        ESP_LOGW(TAG, "reconstruction de scène : le stimulus `anim` est ARRÊTÉ "
                      "(relancer `anim on` si besoin)");
    }

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
    /*
     * ── LE MODE DE RENDU SE DÉDUIT DE num_fbs, ET C'EST UN RÉSULTAT DE MESURE ──
     *
     * À UN framebuffer, LVGL rend en PARTIEL et notre flush recopie la zone sale
     * dans le tampon que la DMA est en train de balayer. MESURÉ le 2026-08-15 :
     * cette écriture-là fait décrocher la DMA et l'image entière se déplace le
     * temps d'une trame, à CHAQUE mise à jour du label. Trois hypothèses ont été
     * éliminées à l'œil, chacune avec son témoin (lecture flash du fond,
     * parcours de cache pleine plage de draw_bitmap, débit instantané de la
     * copie) : aucune n'y change rien, et LVGL en pause l'écran est parfaitement
     * stable. Ce n'est donc pas le VOLUME écrit, c'est le FAIT d'écrire.
     *
     * À DEUX framebuffers, LVGL rend en DIRECT : il dessine dans le tampon caché
     * et le flush ne fait QUE basculer — zéro octet recopié, aucune écriture
     * dans le tampon balayé. C'est la seule parade connue, et elle n'est
     * devenue disponible qu'une fois AC5 prouvé sur la carte (les bascules vers
     * fb[0] ET fb[1] atteignent la dalle sous recalage événementiel).
     *
     * ⚠️ CE MODE EXIGE LA BRANCHE RESTART_IN_VSYNC=n. Avec le symbole à `y`, le
     *    double tampon est cassé (dn1-2, §4 bis) et le recalage est inerte : on
     *    afficherait une bascule sur deux, en silence. dn_recal_log_etat() le
     *    dit au boot ; ici on ne peut pas le refuser, parce que c'est bien la
     *    configuration qu'on veut mesurer.
     */
    s_direct_mode = (cfg->num_fbs >= 2);

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
    /*
     * ⚠️ L'AFFINITÉ DE LA TÂCHE LVGL EST UNE VARIABLE MESURÉE, pas un réglage de
     *    confort — et sa première valeur a été une régression que j'ai
     *    introduite.
     *
     * La tâche avait été épinglée au CŒUR 1, pour que `cpu` sépare le rendu des
     * tâches console qui vivent sur le cœur 0 et rende la charge d'AC8
     * attribuable. Raison honnête, conséquence non anticipée : le pipeline
     * d'affichage entier (init du panneau, ISR vsync, et le chemin brut de
     * dn1-2 qui ne montre AUCUN artefact) vit sur le cœur 0. Mettre le rendu en
     * face, sur l'autre cœur, fait travailler les deux cœurs SIMULTANÉMENT sur
     * la mémoire externe — là où dn1-2 n'avait jamais qu'un seul demandeur.
     *
     * Le témoin qui a rendu cette variable suspecte : le chemin brut écrit
     * 614 400 octets dans le framebuffer visible, six fois de suite, SANS aucun
     * artefact (constat owner) — alors qu'un flush LVGL de 31 784 octets, vingt
     * fois plus petit, déplace l'image entière. Un défaut qui empire quand on
     * écrit VINGT FOIS MOINS n'est pas un défaut de bande passante.
     *
     * L'affinité passe par NVS (`set core <-1|0|1>`) comme num_fbs et
     * draw_lines, et pour la même raison : l'A/B se rejoue sans reflasher, donc
     * sans ajouter le binaire comme deuxième variable. Elle ne peut pas changer
     * à chaud — `lvgl_port_init()` crée la tâche une fois.
     */
    port_cfg.task_affinity = cfg->lvgl_core;
    s_affinity = cfg->lvgl_core;
    ESP_RETURN_ON_ERROR(lvgl_port_init(&port_cfg), TAG, "lvgl_port_init");

    lvgl_port_display_cfg_t disp_cfg = {
        /* io_handle NULL : c'est le bus 3-wire d'INITIALISATION, il ne transporte
         * aucun pixel. Le portage ne le lit que dans lvgl_port_add_disp() (voie
         * SPI/I80), jamais dans la voie RGB. */
        .io_handle = NULL,
        .panel_handle = s_panel,
        .control_handle = NULL,
        /* En mode direct, le portage IGNORE cette valeur et la remplace par
         * hres x vres — les tampons sont les framebuffers eux-mêmes. On la pose
         * quand même à la bonne chose pour que le refus éventuel du portage
         * (« direct mode must using full buffer ») ne soit pas déclenché par
         * nous. */
        .buffer_size = s_direct_mode
                           ? (uint32_t)(DN_LCD_H_RES * DN_LCD_V_RES)
                           : (uint32_t)(DN_LCD_H_RES * s_draw_lines),
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
            .direct_mode = s_direct_mode ? 1 : 0,
        },
    };
    const lvgl_port_display_rgb_cfg_t rgb_cfg = {
        .flags = {
            .bb_mode = 0, /* le bounce buffer est DISQUALIFIÉ (watchdog) — dn1-2 */
            /* Le portage exige num_fbs>=2 pour cette option
             * (esp_lvgl_port_disp.c:367) : elle ne s'allume donc qu'avec le
             * double tampon. Ce qu'elle fait ici : donner à LVGL les DEUX
             * framebuffers du driver comme tampons de rendu, au lieu d'allouer
             * un draw buffer partiel. */
            .avoid_tearing = s_direct_mode ? 1 : 0,
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

    if (s_direct_mode) {
        ESP_LOGI(TAG,
                 "LVGL %d.%d.%d prêt : rendu DIRECT sur les %d framebuffers du "
                 "driver — le flush BASCULE, il ne recopie rien",
                 LVGL_VERSION_MAJOR, LVGL_VERSION_MINOR, LVGL_VERSION_PATCH,
                 dn_display_num_fbs());
        ESP_LOGI(TAG,
                 "  draw_lines=%d IGNORÉ dans ce mode : les tampons de rendu "
                 "SONT les framebuffers.",
                 s_draw_lines);
    } else {
        ESP_LOGI(TAG,
                 "LVGL %d.%d.%d prêt : rendu PARTIEL, draw buffer %d x %d px "
                 "(%d o) en %s",
                 LVGL_VERSION_MAJOR, LVGL_VERSION_MINOR, LVGL_VERSION_PATCH,
                 DN_LCD_H_RES, s_draw_lines, DN_LCD_H_RES * s_draw_lines * 2,
                 s_draw_psram ? "PSRAM" : "RAM interne DMA");
    }
    ESP_LOGI(TAG, "  flush : synchro « %s », chemin « %s »",
             dn_flush_sync_name(s_sync), dn_flush_path_name(s_path));
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
    out->noops = s_n_noop;
}

void dn_ui_reset_stats(void)
{
    s_n_noop = 0;
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

bool dn_ui_force_full_redraw(void)
{
    /* bool et non void (revue) : sur timeout du verrou, la première version ne
     * faisait RIEN en silence — et `flush full` publiait ensuite des compteurs
     * sous la bannière « redessin PLEIN ÉCRAN forcé » pour un redessin jamais
     * demandé. L'instrument de preuve négative d'AC3 mesurait autre chose sans
     * le dire. */
    if (!lvgl_port_lock(1000)) {
        ESP_LOGE(TAG, "verrou LVGL non pris — AUCUN redessin demandé");
        return false;
    }
    lv_obj_invalidate(lv_screen_active());
    lvgl_port_unlock();
    return true;
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
    uint16_t *buf = NULL; /* portée fonction : le chemin d'échec du verrou le libère */
    if (on == (s_bg_psram != NULL)) {
        return ESP_OK;
    }
    if (on) {
        const uint16_t *src = dn_asset_pixels();
        if (!src) {
            ESP_LOGE(TAG, "pas d'asset à copier — la source reste inchangée");
            return ESP_ERR_NOT_FOUND;
        }
        buf = heap_caps_malloc(DN_FB_BYTES, MALLOC_CAP_SPIRAM);
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
        /* PAS de `s_bg_psram = buf` ici : la publication n'a lieu qu'après la
         * reconstruction réussie, sous verrou, plus bas. */
    } else {
        /*
         * ⚠️ ORDRE NON NÉGOCIABLE (correctif de revue — c'était un use-after-free) :
         * la scène est reconstruite AVANT la libération, et la libération n'a
         * lieu QUE si la reconstruction a eu lieu. La première version libérait
         * `old` même quand le verrou expirait : `build_scene()` n'avait pas
         * tourné, `s_bg_dsc.data` pointait toujours sur le bloc rendu, et la
         * tâche LVGL re-blittait de la PSRAM LIBÉRÉE à chaque invalidation —
         * en rendant ESP_OK par-dessus. Déclencheur réaliste : un plein écran
         * à `lines 8` tient le verrou ~2,1 s > le timeout de 1 s.
         */
        if (!lvgl_port_lock(1000)) {
            ESP_LOGE(TAG, "verrou LVGL non pris — la source du fond reste PSRAM, "
                          "rien n'est libéré. Réessayer.");
            return ESP_ERR_TIMEOUT;
        }
        uint16_t *old = s_bg_psram;
        s_bg_psram = NULL;
        build_scene();
        lvgl_port_unlock();
        heap_caps_free(old);
        return ESP_OK;
    }

    /* Même règle au chemin ALLER (revue) : `s_bg_psram` n'est publié qu'APRÈS
     * la reconstruction réussie. La première version l'assignait avant le
     * verrou : sur timeout, l'état disait « PSRAM » pendant que la scène
     * blittait la flash, et tout retry court-circuitait en no-op ESP_OK —
     * l'A/B de T3 coincé sous une étiquette fausse jusqu'au reboot. */
    if (!lvgl_port_lock(1000)) {
        ESP_LOGE(TAG, "verrou LVGL non pris — copie PSRAM libérée, la source "
                      "reste la flash. Réessayer.");
        heap_caps_free(buf);
        return ESP_ERR_TIMEOUT;
    }
    s_bg_psram = buf;
    build_scene();
    lvgl_port_unlock();
    return ESP_OK;
}

bool dn_ui_bg_is_psram(void) { return s_bg_psram != NULL; }

esp_err_t dn_ui_pause(void)
{
    /* Idempotent (revue) : un second `ui off` est un no-op, pas une panne.
     * Sans ce garde, lvgl_port_stop() sur un tick déjà arrêté rend
     * ESP_ERR_INVALID_STATE et la console imprime « refusé » pour rien —
     * l'opérateur part chercher une panne LVGL qui n'existe pas. */
    if (!s_active) {
        return ESP_OK;
    }
    esp_err_t err = lvgl_port_stop();
    if (err == ESP_OK) {
        s_active = false;
        /*
         * ⚠️ DRAINER LE CYCLE EN VOL (correctif de revue). `lvgl_port_stop()` ne
         * fait que geler le tick : il ne joint pas la tâche, qui peut être AU
         * MILIEU de `lv_timer_handler()` — jusqu'à ~176 ms de flushes restants
         * en plein écran `vsync`. Rendre la main tout de suite laissait `scene`
         * écrire le framebuffer pendant que le dernier cycle le flushait encore
         * — la contamination exacte que la pause doit exclure, atteignable en
         * usage scripté (dn_console.py enchaîne les commandes).
         * La tâche du portage tient `lvgl_port_lock` pendant tout son cycle
         * (esp_lvgl_port.c, boucle de tâche) : prendre puis rendre le verrou
         * garantit que le cycle en vol est FINI. 2 000 ms couvrent le pire
         * plein écran à `lines 8` (~80 flushes x ~27 ms).
         */
        if (lvgl_port_lock(2000)) {
            lvgl_port_unlock();
        } else {
            ESP_LOGW(TAG, "pause : le cycle en vol n'a pas rendu la main en "
                          "2 s — un flush LVGL peut encore toucher le "
                          "framebuffer, attendre avant `scene`/`tear`.");
        }
    }
    return err;
}

esp_err_t dn_ui_resume(void)
{
    /* Idempotent (revue) — même raison que dn_ui_pause. Évite aussi le demi-état
     * du portage : lvgl_port_resume() fait lv_timer_enable(true) AVANT de
     * démarrer l'esp_timer, donc un échec le laissait à moitié appliqué. */
    if (s_active) {
        return ESP_OK;
    }
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
bool dn_ui_direct_mode(void) { return s_direct_mode; }
int dn_ui_affinity(void) { return s_affinity; }

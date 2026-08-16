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
#include "dn_touch.h"
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

/* ── Géométrie des vues de dn1-4 — PROVISOIRE, ET ÉCRIT COMME TEL ─────────── */
/*
 * ⚠️ AUCUNE de ces valeurs n'est spécifiée nulle part. Le brief et son addendum
 *    figent la STRUCTURE (barre heure/date en haut, grille 2x3, bandeau MENU en
 *    bas) et la seule dimension connue est 480x640 portrait. Tout ce qui suit est
 *    DÉRIVÉ pour que dn1-4 ait des zones tactiles à éprouver — dn3-2 dessine la
 *    vraie grille et fera foi. Ne pas bâtir dessus.
 *
 * Ce qui n'est PAS arbitraire, en revanche : aucun élément ne fait la hauteur de
 * l'écran. Le verdict adverse mesuré en dn1-3 (§10.4) est que la synchro `vsync`
 * NE PROTÈGE PAS une zone sale pleine hauteur ; une case de 225x156 est très loin
 * de ce cas. La barre du haut est pleine LARGEUR, ce qui est sans rapport : le
 * balayage descend ligne par ligne.
 *
 *   0                                                              479
 *   +--------------------------------------------------------------+   0
 *   |  barre : heure (28 px) a gauche, date (14 px) a droite        |
 *   +--------------------------------------------------------------+  70
 *   |   +--------------------+    +--------------------+           |
 *   |   |  CPU               |    |  GPU               |           |
 *   |   +--------------------+    +--------------------+           |
 *   |   |  RAM               |    |  RESEAU            |           |
 *   |   +--------------------+    +--------------------+           |
 *   |   |  TEMP.             |    |  HUMIDITE          |           |
 *   |   +--------------------+    +--------------------+           |
 *   +--------------------------------------------------------------+ 580
 *   |  MENU (o)                                                    |
 *   +--------------------------------------------------------------+ 640
 */
#define DN_UI_BARRE_H 70
#define DN_UI_MENU_H 60
#define DN_UI_MARGE 10
#define DN_UI_GAP 10
#define DN_UI_CASE_W ((DN_LCD_H_RES - 2 * DN_UI_MARGE - DN_UI_GAP) / 2) /* 225 */
#define DN_UI_GRILLE_Y DN_UI_BARRE_H                                    /* 70 */
#define DN_UI_GRILLE_H (DN_LCD_V_RES - DN_UI_BARRE_H - DN_UI_MENU_H)    /* 510 */
#define DN_UI_CASE_H ((DN_UI_GRILLE_H - 2 * DN_UI_MARGE - 2 * DN_UI_GAP) / 3) /* 156 */

/* Zone tactile du retour : généreuse par exigence d'AC4 (« pas juste le
 * glyphe »). 120x60 dans le coin haut-gauche, soit 24 fois l'aire du chevron. */
#define DN_UI_RETOUR_W 120
#define DN_UI_RETOUR_H 60

/*
 * ── LES LIBELLÉS SONT SANS ACCENT, ET CE N'EST PAS UNE NÉGLIGENCE ────────────
 *
 * MESURÉ dans le source de la police, pas supposé : `lv_font_montserrat_14.c`
 * et `_28.c` sont générés avec `-r 0x20-0x7F,0xB0,0x2022` (première ligne du
 * fichier). La plage couvre l'ASCII imprimable, le SIGNE DEGRÉ (0xB0) et la
 * puce — et RIEN d'autre. « RÉSEAU », « HUMIDITÉ » ou « AOÛT » y perdraient
 * leur lettre accentuée, silencieusement : LVGL ne dessine pas le glyphe absent
 * et ne se plaint pas.
 *
 * 🔴 LEGS POUR dn3-1 : afficher du français accentué sur cette dalle EXIGE une
 *    police générée avec la plage latine étendue (lv_font_conv), donc du binaire
 *    en plus. Ce n'est pas un choix esthétique reportable — c'est une contrainte
 *    d'outillage, à budgéter quand le SystemMetricWidget naîtra.
 * Le « °C » de la température, lui, passe : 0xB0 est dans la plage.
 */
static const struct {
    const char *nom;
    const char *valeur; /* FACTICE — dn2/dn4-1 apporteront les vraies */
} k_metriques[DN_UI_METRIQUES] = {
    {"CPU", "42 %"},      {"GPU", "37 %"},       {"RAM", "12,4 Go"},
    {"RESEAU", "48 Mo/s"}, {"TEMP.", "21,4 " "\xC2\xB0" "C"}, {"HUMIDITE", "47 %"},
};

const char *dn_ui_metrique_nom(int idx)
{
    return (idx >= 0 && idx < DN_UI_METRIQUES) ? k_metriques[idx].nom : "?";
}

const char *dn_ui_vue_name(dn_ui_vue_t v)
{
    switch (v) {
    case DN_VUE_DASHBOARD:
        return "dashboard";
    case DN_VUE_DETAIL:
        return "detail";
    default:
        return "?";
    }
}

const char *dn_nav_model_name(dn_nav_model_t m)
{
    switch (m) {
    case DN_NAV_REBUILD:
        return "rebuild";
    case DN_NAV_SCREENS:
        return "screens";
    default:
        return "?";
    }
}

bool dn_nav_model_from_name(const char *nom, dn_nav_model_t *out)
{
    for (int i = 0; i < DN_NAV_COUNT; i++) {
        if (strcasecmp(nom, dn_nav_model_name((dn_nav_model_t)i)) == 0) {
            *out = (dn_nav_model_t)i;
            return true;
        }
    }
    return false;
}

/* ── État ─────────────────────────────────────────────────────────────────── */

static lv_display_t *s_disp;
static esp_lcd_panel_handle_t s_panel;
/*
 * DEUX slots pour le label vivant, un par vue — et ce n'est pas du zèle.
 * En modèle SCREENS les deux écrans existent en même temps, donc le label aussi.
 * Un pointeur unique finirait par désigner le label de l'écran NON affiché : le
 * timer 1 Hz écrirait dans le vide, l'écran visible se figerait, et on
 * chercherait la panne du côté du timer alors que c'est le pointeur qui aurait
 * changé de propriétaire. `label_courant()` est la seule façon d'y accéder.
 */
static lv_obj_t *s_label_dash;
static lv_obj_t *s_label_det;
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
/*
 * MASQUÉ PAR DÉFAUT depuis dn1-4, et c'est un changement de comportement assumé :
 * le label vivant est centré (géométrie gelée pour rester comparable à dn1-3) et
 * recouvrirait les cases RAM/RESEAU du dashboard. `ui label on` le rallume pour
 * rejouer le régime produit de dn1-3 à l'identique — c'est ce que fait AC6 pour
 * ré-observer l'artefact §10.5, qui a besoin d'un redessin périodique.
 */
static volatile bool s_label_shown;
static volatile bool s_anim_on;
static volatile bool s_active = true;
static int s_anim_ms = DN_UI_ANIM_MS_DEFAUT;

static int s_draw_lines;
static bool s_draw_psram;
static size_t s_int_avant, s_int_apres, s_psram_avant, s_psram_apres;

/* ── Navigation (dn1-4) ───────────────────────────────────────────────────── */
static dn_ui_vue_t s_vue = DN_VUE_DASHBOARD;
static int s_metrique;
/*
 * ── LE MODÈLE RETENU, ET LES CHIFFRES QUI L'ONT CHOISI (AC4, 2026-08-16) ─────
 *
 * 20 allers-retours scriptés (`nav ab 20`), latence clic -> dernier flush :
 *
 *   draw_lines   modèle    min      moy      max      tas LVGL utilisé
 *   ---------------------------------------------------------------------
 *      64        rebuild   293,9    307,7    320,7    12 016 o (20 %)
 *      64        SCREENS   267,1    267,9    293,9    20 064 o (33 %)
 *     128        rebuild   240,4    279,0    318,0    17 684 o (29 %)
 *     128        SCREENS   187,0    234,9    257,7    —
 *
 * SCREENS gagne 40 ms (13 %) sur rebuild, pour +8 048 o dans le tas LVGL (les
 * deux arbres vivent en permanence) sur 64 Ko dont 42 Ko restent libres.
 *
 * ⚠️ CE TABLEAU EST CELUI DE LA PREMIÈRE CAMPAGNE, ET IL EST FAUX SUR LE PRIX.
 *    Il a été relevé à `bounce_px = 0` (config déclarée « écran inutilisable »
 *    depuis) et surtout sur un A/B dont la bascule FUYAIT un arbre d'écran
 *    complet — corrigé dans build_scene(). Le tas y était donc gonflé.
 *
 * ── ✅ LA MESURE QUI FAIT FOI (session carte du 2026-08-16, firmware 0e7fe61) ──
 *
 *   Config de référence : num_fbs=1 · bounce_px=4800 · draw_lines=128 · poll
 *
 *   modèle     min      moy      max      n       tas LVGL utilisé
 *   ---------------------------------------------------------------
 *   SCREENS    285,0    307,0    320,8    40/40   15 216 o   (delta -12 o)
 *   rebuild    300,8    346,9    374,2    40/40   12 184 o   (delta   0 o)
 *
 * SCREENS gagne 39,9 ms (11,5 %) pour +3 032 o de tas — et NON +8 048 o : la
 * fuite surestimait son prix de 2,7x. L'écart entre modèles est remarquablement
 * STABLE (39,8 ms à bounce 0/lines 64, 39,9 ms ici) : le coût du modèle est un
 * coût de CONSTRUCTION D'ARBRE, indépendant du pipeline d'affichage.
 *
 * ⛔ NE PAS écrire ici que « SCREENS fait passer le budget » : le budget
 *    < 300 ms du brief N'EST PAS TENU (307,0 ms mesurés, 320,8 au pire — voir
 *    DN_DEFAULT_DRAW_LINES dans dn_bootcfg.c, qui fait foi). SCREENS est retenu
 *    parce qu'il est le moins cher des deux, pas parce qu'il tient une promesse.
 *
 * ⚠️ « AUCUN des deux modèles ne fuit » était prouvé par un instrument AVEUGLE :
 *    `nav ab` mesurait la RAM interne et la PSRAM, alors que le tas LVGL est un
 *    pool STATIQUE en .bss (LV_MEM_ADR=0) où aucun lv_obj_create ne passe par
 *    heap_caps_malloc. Un « delta 0 o » s'y affichait à l'identique avec ou sans
 *    fuite. `nav ab` encadre désormais la série par lv_mem_monitor(), et la
 *    non-fuite est prouvée : 5 bascules screens<->rebuild enchaînées laissent le
 *    tas plat (15 204 / 12 168 / 15 180 / 12 180 / 15 208 o).
 * ⚠️ CE QUE L'ARBITRAGE NE DIT PAS : le vrai plancher n'est pas le modèle. Une
 *    transition redessine l'écran entier, soit 640/draw_lines flushes qui
 *    attendent CHACUN une trame — 10 trames à 26,7 ms = 267 ms à 64 lignes. Le
 *    modèle joue sur le temps de CONSTRUCTION ; le nombre de flushes
 *    synchronisés joue sur le reste, et il pèse plus lourd (voir AC5).
 */
static dn_nav_model_t s_nav = DN_NAV_SCREENS;
static volatile uint32_t s_nav_count;
/* Modèle SCREENS : les deux racines vivent en permanence. NULL en REBUILD — et
 * c'est ce qui distingue les deux modèles à l'oeil dans `ui`. */
static lv_obj_t *s_scr_dash;
static lv_obj_t *s_scr_detail;
/* Les labels du détail que le modèle SCREENS RÉÉCRIT au lieu de reconstruire.
 * En REBUILD ils sont recréés à chaque transition et ces pointeurs ne servent
 * qu'à ne pas les chercher dans l'arbre. */
static lv_obj_t *s_det_titre, *s_det_valeur, *s_det_minmax, *s_det_sec;
/* ── La case CPU vit (dn2-2) ──────────────────────────────────────────────────
 * Le label de VALEUR de la case haut-gauche, seul de la grille à recevoir une
 * vraie donnée ici (les 5 autres gardent leur factice — dn3-1 fera le modèle).
 * NULL quand le dashboard n'existe pas (REBUILD en vue détail) — et remis à
 * NULL partout où les autres pointeurs de labels le sont déjà. */
static lv_obj_t *s_case_cpu_valeur;
/* Le texte et la validité COURANTS de la case CPU, conservés pour que toute
 * (re)construction du dashboard repose l'état RÉEL de la liaison au lieu du
 * « 42 % » factice de dn1-4. Écrits sous le verrou LVGL (dn_ui_cpu_maj), lus
 * sous le même verrou (build_dashboard). */
static char s_cpu_texte[16] = "--";
static bool s_cpu_valide;
/* Dernière zone touchée — la preuve d'AC3, lue par la console. */
static volatile int s_dernier_tap = DN_UI_ZONE_AUCUNE;
static volatile uint32_t s_taps;
static volatile uint32_t s_menu_taps;

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
        /*
         * FIN DU CHRONOMÈTRE D'AC5. C'est ici, et pas ailleurs : le dernier flush
         * du cycle est le moment où la nouvelle vue est ENTIÈREMENT dans le
         * framebuffer. Un no-op quand rien n'est armé (un test sur un booléen),
         * pour ne rien coûter au chemin chaud des 37,40 trames par seconde.
         *
         * ⚠️ Ce que ce point d'arrêt N'INCLUT PAS : la trame qu'il reste à la DMA
         *    pour peindre ce qu'on vient d'écrire (jusqu'à 26,7 ms). Déclaré,
         *    jamais ajouté en douce à la mesure.
         */
        dn_touch_latence_stop();
    }

    lv_display_flush_ready(disp);
}

/* ── La scène ─────────────────────────────────────────────────────────────── */

/* Le label de la vue AFFICHÉE — le seul qu'il soit juste de mettre à jour. */
static lv_obj_t *label_courant(void)
{
    return s_vue == DN_VUE_DETAIL ? s_label_det : s_label_dash;
}

static void label_tick(lv_timer_t *t)
{
    (void)t;
    lv_obj_t *s_label = label_courant();
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

/* ── Le fond, commun aux deux vues ────────────────────────────────────────── */

/* Pose le fond (Living PCB ou panneau d'alerte) sur `scr`. Extrait de l'ancien
 * `build_scene()` sans changement de comportement : les deux vues de dn1-4 se
 * dessinent PAR-DESSUS ce fond, qui reste l'image de dn1-2. L'esthétique des
 * cases n'est pas un sujet de cette story (dn3-1 la portera). */
static void fond_poser(lv_obj_t *scr)
{
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

        /* LOCAL, et pas un statique (revue dn1-4) : l'image appartient à son
         * écran, qui la détruit avec lui. Le `s_img` global qu'on gardait était
         * écrit six fois et lu ZÉRO — en modèle SCREENS, `fond_poser()` étant
         * appelé pour les deux écrans, il finissait de toute façon par désigner
         * l'image de l'écran qu'on ne regarde pas. */
        lv_obj_t *img = lv_image_create(scr);
        lv_image_set_src(img, &s_bg_dsc);
        lv_obj_set_pos(img, 0, 0);

        /*
         * ── LE VOILE, demandé par l'owner le 2026-08-16 ──────────────────────
         * Constat : « le fond prend trop, il masque les détails (des cadres
         * aussi) ». Le Living PCB est une photo très contrastée, et du texte
         * blanc posé dessus se perd dans ses pistes claires.
         *
         * Un FLOU aurait été le réflexe, et il est écarté : LVGL n'en a pas qui
         * soit gratuit, et il faudrait le recalculer à chaque zone invalidée —
         * sur un budget de transition déjà à 267 ms. Un aplat noir translucide
         * fait le même travail perceptif (baisser le contraste du fond pour que
         * le premier plan ressorte) pour le prix d'un rectangle.
         *
         * ⚠️ NON CLIQUABLE : il couvre tout l'écran. Cliquable, il volerait
         *    chaque tap destiné aux cases — et « toute la case est la zone
         *    tactile » deviendrait faux à cause d'un élément décoratif.
         * ⚠️ L'opacité reste PARTIELLE : le PCB est l'identité visuelle du
         *    produit, on l'atténue, on ne l'efface pas. dn3-1 tranchera la valeur
         *    définitive avec le reste de l'esthétique.
         */
        lv_obj_t *voile = lv_obj_create(scr);
        lv_obj_remove_style_all(voile);
        lv_obj_set_pos(voile, 0, 0);
        lv_obj_set_size(voile, DN_LCD_H_RES, DN_LCD_V_RES);
        lv_obj_clear_flag(voile, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_clear_flag(voile, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_set_style_bg_color(voile, lv_color_black(), 0);
        lv_obj_set_style_bg_opa(voile, LV_OPA_50, 0);
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

}

/*
 * ── LE LABEL VIVANT DE dn1-3 SURVIT, INCHANGÉ, ET C'EST VOLONTAIRE ───────────
 *
 * Même géométrie (260x44), même police (montserrat 28), même place (centre),
 * même fond transparent. Ce n'est PAS un élément de la spec UI : c'est
 * l'INSTRUMENT qui a produit le régime de référence de dn1-3 (15 892 px par mise
 * à jour, 1,00 flush/cycle, 0,9 % de CPU). Le déplacer ou le redimensionner
 * rendrait les budgets d'AC8 incomparables à ceux de la marche du dessous — et
 * un budget qu'on ne peut pas comparer ne sert à rien.
 *
 * ⚠️ Il est donc MASQUÉ par défaut dès qu'une vue produit est affichée (il
 *    recouvrirait les cases RAM/RESEAU), et `ui label on` le rallume pour
 *    rejouer dn1-3 à l'identique. Le chevauchement assumé de ce moment-là est
 *    celui d'un instrument de campagne, pas d'un écran de produit.
 */
static void label_poser(lv_obj_t *scr, lv_obj_t **slot)
{
    lv_obj_t *s_label = lv_label_create(scr);
    *slot = s_label;
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
    /* Le label ne capte AUCUN toucher : sinon il volerait le tap destiné aux
     * cases qu'il recouvre quand on le rallume, et « toute la case est la zone
     * tactile » deviendrait faux par accident. */
    lv_obj_clear_flag(s_label, LV_OBJ_FLAG_CLICKABLE);
    if (!s_label_shown) {
        lv_obj_add_flag(s_label, LV_OBJ_FLAG_HIDDEN);
    }
}

/* ── Les zones tactiles ───────────────────────────────────────────────────── */

/*
 * Un conteneur cliquable, nu. C'est LA brique de dn1-4 : ni widget, ni style de
 * produit — une géométrie qui reçoit le doigt.
 *
 * ⚠️ LES DEUX DRAPEAUX QUI DÉCIDENT SI « TOUTE LA CASE » EST VRAIE :
 *    - CLICKABLE sur le CONTENEUR, et les labels enfants laissés NON cliquables :
 *      LVGL remonte alors au premier ancêtre cliquable, donc un tap sur le texte
 *      comme un tap dans un coin vide arrivent au même endroit.
 *    - SCROLLABLE RETIRÉ. `lv_obj_create()` le pose par défaut, et un conteneur
 *      scrollable AVALE le geste dès que le doigt bouge de quelques pixels : le
 *      tap marcherait au centre, en appuyant bien droit, et raterait au bord ou
 *      sur un doigt qui roule. C'est exactement le défaut que la preuve « aux
 *      coins » d'AC3 est censée attraper — autant ne pas le fabriquer.
 */
static lv_obj_t *zone_creer(lv_obj_t *parent, int x, int y, int w, int h,
                            lv_event_cb_t cb, void *user)
{
    lv_obj_t *z = lv_obj_create(parent);
    lv_obj_remove_style_all(z);
    lv_obj_set_pos(z, x, y);
    lv_obj_set_size(z, w, h);
    lv_obj_clear_flag(z, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_flag(z, LV_OBJ_FLAG_CLICKABLE);
    /* Un aplat sombre translucide : assez pour que la case se VOIE (l'owner doit
     * savoir où viser pour le constat « au coin »), assez peu pour que le Living
     * PCB reste le fond. Bordure fine, pas de radius : rien à défendre ici. */
    lv_obj_set_style_bg_color(z, lv_color_black(), 0);
    /* 70 % et non 40 % : à 40 % les pistes claires du Living PCB passaient au
     * travers et mangeaient le texte blanc (constat owner). Le fond reste
     * perceptible — c'est l'identité du produit — mais il ne concourt plus. */
    lv_obj_set_style_bg_opa(z, LV_OPA_70, 0);
    lv_obj_set_style_border_color(z, lv_color_hex(0x50c0ff), 0);
    lv_obj_set_style_border_width(z, 1, 0);
    lv_obj_set_style_border_opa(z, LV_OPA_60, 0);
    if (cb) {
        lv_obj_add_event_cb(z, cb, LV_EVENT_CLICKED, user);
    }
    return z;
}

/*
 * Le même aplat que `zone_creer`, mais SANS la zone tactile — pour porter du
 * texte, pas pour recevoir le doigt.
 *
 * Il existe parce que la première version du détail posait ses labels
 * DIRECTEMENT sur le fond : constat owner du 2026-08-16, « les titres et textes
 * en bas ne sont pas encore bien lisibles ». Les cases du dashboard, elles,
 * avaient leur aplat depuis le début — d'où la différence de lisibilité entre
 * les deux écrans, qui n'avait rien d'esthétique et tout de structurel.
 */
static lv_obj_t *panneau(lv_obj_t *parent, int x, int y, int w, int h)
{
    lv_obj_t *p = lv_obj_create(parent);
    lv_obj_remove_style_all(p);
    lv_obj_set_pos(p, x, y);
    lv_obj_set_size(p, w, h);
    lv_obj_clear_flag(p, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_clear_flag(p, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_set_style_bg_color(p, lv_color_black(), 0);
    lv_obj_set_style_bg_opa(p, LV_OPA_70, 0);
    lv_obj_set_style_border_color(p, lv_color_hex(0x50c0ff), 0);
    lv_obj_set_style_border_width(p, 1, 0);
    lv_obj_set_style_border_opa(p, LV_OPA_60, 0);
    return p;
}

static lv_obj_t *texte(lv_obj_t *parent, const char *s, const lv_font_t *font,
                       lv_color_t couleur, int x, int y)
{
    lv_obj_t *l = lv_label_create(parent);
    lv_obj_set_style_text_font(l, font, 0);
    lv_obj_set_style_text_color(l, couleur, 0);
    lv_obj_set_style_bg_opa(l, LV_OPA_TRANSP, 0);
    lv_label_set_text(l, s);
    lv_obj_set_pos(l, x, y);
    /* Les labels ne captent rien : c'est le conteneur qui est la zone. */
    lv_obj_clear_flag(l, LV_OBJ_FLAG_CLICKABLE);
    return l;
}

/* ── Navigation : les callbacks ───────────────────────────────────────────── */

/*
 * ⚠️ POURQUOI TOUTE TRANSITION PASSE PAR `lv_async_call()` ET JAMAIS DIRECTEMENT.
 *
 * Ces callbacks tournent DANS l'envoi d'événement LVGL, sur un objet qui
 * appartient à l'arbre que la transition va DÉTRUIRE (`lv_obj_clean`, ou le
 * chargement d'un autre écran). Supprimer l'objet qui est en train de recevoir
 * son propre événement est un use-after-free — le même genre que celui trouvé en
 * revue de dn1-3 sur `ui bg flash`. `lv_async_call()` diffère le travail au tour
 * de boucle suivant, hors du contexte d'événement : c'est la parade prévue par
 * LVGL, pas un contournement.
 *
 * Conséquence ASSUMÉE sur la mesure : le délai jusqu'au prochain tour de boucle
 * (jusqu'à ~33 ms) est DANS la latence d'AC5, parce qu'il est dans le vécu de
 * l'utilisateur.
 */
static bool nav_appliquer(int cible, int64_t t_clic);

/*
 * ── L'INSTANT DU CLIC VOYAGE AVEC SON CLIC (correctif de revue dn1-4) ────────
 *
 * Il tenait avant dans UN SEUL global, que tout tap suivant écrasait avant que
 * l'async du précédent ne s'exécute. Deux taps sur deux cases séparés de moins
 * d'un tour de boucle (~33 ms, la fenêtre même que lv_async_call assume) et la
 * PREMIÈRE transition était chronométrée depuis le SECOND clic : latence
 * sous-estimée, ou `dt < 0` et l'échantillon abandonné en silence. La moyenne
 * publiée par AC5 était donc calculée sur un échantillon biaisé vers le bas,
 * sans que rien dans la sortie ne permette de s'en apercevoir.
 *
 * LVGL ne transporte qu'un pointeur, et allouer un int64 par tap mettrait une
 * allocation dans le chemin chaud. On encode donc un NUMÉRO DE SLOT dans les
 * bits hauts du paramètre, et l'horodatage vit dans un petit anneau. Quatre
 * slots : lv_async_call n'exécute jamais plus d'un tour de retard, quatre taps
 * en vol simultanés n'arrivent pas au doigt.
 */
#define DN_NAV_PENDING 4
static volatile int64_t s_clic_ts[DN_NAV_PENDING];
static uint32_t s_clic_seq;
/* Asyncs refusées par LVGL (file pleine, tas saturé) : un tap qui n'ouvrira
 * jamais rien ne doit PAS être compté comme un tap — sinon `touch trace` valide
 * une zone tactile morte, et c'est la preuve d'AC3 qui ment. */
static volatile uint32_t s_async_refus;

/* Paramètre d'async : ((slot+1) << 8) | cible. Jamais NULL, ce qui garde
 * l'encodage lisible dans un log et distinguable d'un paramètre oublié. */
static void *nav_param(int cible, int64_t t_clic)
{
    uint32_t slot = s_clic_seq++ % DN_NAV_PENDING;
    s_clic_ts[slot] = t_clic;
    return (void *)(intptr_t)(((slot + 1) << 8) | (uint32_t)(cible & 0xFF));
}

static void nav_async(void *param)
{
    uintptr_t p = (uintptr_t)param;
    /* Encodage de la cible : 0 = retour au dashboard, 1..6 = métrique p-1. */
    int cible = (int)(p & 0xFF);
    int slot = (int)((p >> 8) & 0xFF) - 1;
    int64_t t_clic = (slot >= 0 && slot < DN_NAV_PENDING) ? s_clic_ts[slot]
                                                          : esp_timer_get_time();
    nav_appliquer(cible, t_clic);
}

static void on_case_clic(lv_event_t *e)
{
    int64_t t_clic = esp_timer_get_time();
    intptr_t idx = (intptr_t)lv_event_get_user_data(e);
    /* Le retour de lv_async_call était JETÉ : sur file pleine, le compteur de
     * taps montait quand même et la zone passait pour vivante. */
    if (lv_async_call(nav_async, nav_param((int)idx + 1, t_clic)) != LV_RESULT_OK) {
        s_async_refus++;
        return;
    }
    s_dernier_tap = (int)idx;
    s_taps++;
}

static void on_retour_clic(lv_event_t *e)
{
    (void)e;
    int64_t t_clic = esp_timer_get_time();
    if (lv_async_call(nav_async, nav_param(0, t_clic)) != LV_RESULT_OK) {
        s_async_refus++;
        return;
    }
    s_dernier_tap = DN_UI_ZONE_RETOUR;
    s_taps++;
}

/*
 * ── LE BANDEAU MENU : UN NO-OP CONSIGNÉ, PAS UN OUBLI ────────────────────────
 * Aucune destination ne lui est spécifiée — ni dans le brief, ni dans son
 * addendum, ni dans l'epic. dn1-4 le DESSINE (fidélité au layout, et c'est une
 * 7e zone tactile à instrumenter) et son tap écrit une ligne de log. C'est une
 * décision de story, renversable par l'owner, et elle est écrite plutôt que
 * subie : un bouton muet SANS trace serait indiscernable d'une zone tactile qui
 * ne marche pas.
 */
static void on_menu_clic(lv_event_t *e)
{
    (void)e;
    /* ENREGISTRÉ, pas loggé — voir dn_ui.h : un printf ici bloquerait la tâche
     * LVGL sur le lien USB. `touch trace` et `nav` le restituent, et c'est bien
     * une trace VISIBLE, ce qu'exige AC3 pour distinguer un no-op d'une zone
     * tactile morte. */
    s_dernier_tap = DN_UI_ZONE_MENU;
    s_taps++;
    s_menu_taps++;
}

/* ── Les deux vues ────────────────────────────────────────────────────────── */

static void build_dashboard(lv_obj_t *scr)
{
    fond_poser(scr);

    /* Barre heure/date — statique et FACTICE : la RTC PCF85063 est sur le bus
     * mais n'est pas initialisée ici (dn2). Pleine largeur, 70 px de haut : elle
     * n'est PAS un cas adverse au sens de §10.4, qui parle de hauteur. */
    lv_obj_t *barre = lv_obj_create(scr);
    lv_obj_remove_style_all(barre);
    lv_obj_set_pos(barre, 0, 0);
    lv_obj_set_size(barre, DN_LCD_H_RES, DN_UI_BARRE_H);
    lv_obj_clear_flag(barre, LV_OBJ_FLAG_SCROLLABLE);
    /* NON cliquable, et c'est une exigence d'AC3 : un tap sur la barre ne doit
     * RIEN ouvrir. C'est l'une des deux zones mortes que le constat vérifie. */
    lv_obj_clear_flag(barre, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_set_style_bg_color(barre, lv_color_black(), 0);
    lv_obj_set_style_bg_opa(barre, LV_OPA_70, 0);
    texte(barre, "21:46", &lv_font_montserrat_28, lv_color_white(), DN_UI_MARGE, 18);
    texte(barre, "VEN. 06 AOUT", &lv_font_montserrat_14,
          lv_color_hex(0xa0d8ff), 300, 28);

    /* La grille 2x3. `zone_creer` fait toute la zone tactile. */
    for (int i = 0; i < DN_UI_METRIQUES; i++) {
        int col = i % 2;
        int ligne = i / 2;
        int x = DN_UI_MARGE + col * (DN_UI_CASE_W + DN_UI_GAP);
        int y = DN_UI_GRILLE_Y + DN_UI_MARGE + ligne * (DN_UI_CASE_H + DN_UI_GAP);
        lv_obj_t *case_ = zone_creer(scr, x, y, DN_UI_CASE_W, DN_UI_CASE_H,
                                     on_case_clic, (void *)(intptr_t)i);
        texte(case_, k_metriques[i].nom, &lv_font_montserrat_14,
              lv_color_hex(0xa0d8ff), 12, 10);
        /* La case CPU (i == 0) affiche l'état RÉEL de la liaison PC (dn2-2) :
         * sa valeur courante si la liaison vit, « -- » grisé sinon. Les cinq
         * autres gardent leur factice de dn1-4 jusqu'à dn3-1/dn4-1. */
        lv_obj_t *val =
            texte(case_, (i == 0) ? s_cpu_texte : k_metriques[i].valeur,
                  &lv_font_montserrat_28,
                  (i == 0 && !s_cpu_valide) ? lv_color_hex(0x9a9a9a)
                                            : lv_color_white(),
                  12, 60);
        if (i == 0) {
            s_case_cpu_valeur = val;
        }
    }

    /* Le bandeau MENU — 7e zone, cliquable, no-op consigné. */
    lv_obj_t *menu = zone_creer(scr, 0, DN_LCD_V_RES - DN_UI_MENU_H, DN_LCD_H_RES,
                                DN_UI_MENU_H, on_menu_clic, NULL);
    texte(menu, "MENU  " LV_SYMBOL_LIST, &lv_font_montserrat_28, lv_color_white(),
          DN_UI_MARGE + 6, 14);

    label_poser(scr, &s_label_dash);
}

/*
 * ── LE TEMPLATE DE DÉTAIL : UN SEUL SQUELETTE, PARAMÉTRÉ ─────────────────────
 * « On ne change que les données, jamais la structure » (addendum §1). Les six
 * métriques sont SIX APPELS de cette fonction, pas six écrans — et c'est
 * précisément ce que le modèle SCREENS exploite en réécrivant les labels au lieu
 * de reconstruire.
 */
static void build_detail(lv_obj_t *scr, int idx)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES) {
        idx = 0;
    }
    fond_poser(scr);

    /*
     * ── TOUT LE TEXTE VIT SUR UN APLAT ──────────────────────────────────────
     * Correctif du constat owner du 2026-08-16. Les labels étaient posés à même
     * le fond : le Living PCB est une photo très contrastée, et du texte blanc
     * dessus se perd — surtout dans le bas de l'image. Quatre panneaux portent
     * désormais les quatre blocs du template, exactement comme les cases du
     * dashboard portaient déjà les leurs.
     * La STRUCTURE du template ne change pas (addendum §1 : « on ne change que
     * les données, jamais la structure ») — seul le support du texte change.
     */

    /* Bandeau d'en-tête : le retour ET le titre, sur le même aplat. */
    lv_obj_t *entete = panneau(scr, 0, 0, DN_LCD_H_RES, 80);
    /* Retour : zone GÉNÉREUSE (120x60), pas le glyphe seul — exigence d'AC4.
     * Enfant du bandeau, donc cliquable par-dessus lui : le bandeau n'est pas
     * cliquable, il ne peut pas lui voler le tap. */
    lv_obj_t *retour = zone_creer(entete, DN_UI_MARGE, DN_UI_MARGE, DN_UI_RETOUR_W,
                                  DN_UI_RETOUR_H, on_retour_clic, NULL);
    texte(retour, LV_SYMBOL_LEFT, &lv_font_montserrat_28, lv_color_white(), 16, 14);

    /* Titre de la métrique — c'est LUI qui rend la zone touchée identifiable
     * sans ambiguïté (AC3) : six instances du même template, un seul titre. */
    s_det_titre = texte(entete, k_metriques[idx].nom, &lv_font_montserrat_28,
                        lv_color_hex(0xa0d8ff), DN_UI_MARGE + DN_UI_RETOUR_W + 20,
                        24);

    /* Grande valeur. « Grande » = montserrat 28, la plus grosse police DÉJÀ
     * embarquée : en ajouter une coûterait du binaire pour un écran factice. */
    lv_obj_t *bloc_valeur =
        panneau(scr, DN_UI_MARGE, 95, DN_LCD_H_RES - 2 * DN_UI_MARGE, 62);
    s_det_valeur = texte(bloc_valeur, k_metriques[idx].valeur,
                         &lv_font_montserrat_28, lv_color_white(), 14, 14);

    /* Placeholder de courbe : un cadre étiqueté, PAS une courbe. Les vraies
     * séries arrivent avec l'historique RAM-session (dn2/dn4-1). */
    lv_obj_t *cadre = panneau(scr, DN_UI_MARGE, 170, DN_LCD_H_RES - 2 * DN_UI_MARGE,
                              200);
    texte(cadre, "COURBE (dn2 / dn4-1)", &lv_font_montserrat_14,
          lv_color_hex(0x80a0b0), 12, 88);

    /* Données secondaires et MIN/MAX, factices, sur un seul aplat de bas de
     * page — c'est celui-là que l'owner a signalé comme illisible. */
    lv_obj_t *bas = panneau(scr, DN_UI_MARGE, 385, DN_LCD_H_RES - 2 * DN_UI_MARGE,
                            200);
    s_det_sec = texte(bas, "moy. 5 min : 38 %\ncharge : moderee\nsource : factice",
                      &lv_font_montserrat_14, lv_color_hex(0xc0d8e8), 14, 16);
    s_det_minmax = texte(bas, "MIN 12 %   -   MAX 91 %", &lv_font_montserrat_28,
                         lv_color_white(), 14, 130);

    label_poser(scr, &s_label_det);
}

/* Réécrit les données du détail SANS reconstruire l'arbre — le raccourci du
 * modèle SCREENS. Ne touche à aucune position : la structure ne change jamais. */
static void detail_reparametrer(int idx)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES) {
        return;
    }
    if (s_det_titre) {
        lv_label_set_text(s_det_titre, k_metriques[idx].nom);
    }
    if (s_det_valeur) {
        lv_label_set_text(s_det_valeur, k_metriques[idx].valeur);
    }
}

/* ── build_scene : reconstruit la VUE COURANTE ────────────────────────────── */

/* Détruit et reconstruit toute la scène. Idempotent, et appelé aussi bien à
 * l'init qu'au changement de source de fond : reconstruire coûte quelques
 * millisecondes une fois, là où permuter le pointeur d'une image déjà posée
 * obligerait à raisonner sur le cache d'images de LVGL. Un geste d'opérateur ne
 * mérite pas cette subtilité-là. */
static void build_scene(void)
{
    /* ⚠️ L'ombre suit la réalité (revue dn1-3). La reconstruction détruit la
     * barre du stimulus ET son animation : laisser `s_anim_on` à vrai ferait
     * annoncer « stimulus EN COURS » par `ui`, `anim` et l'étiquette de `fps` —
     * une étiquette de mesure FAUSSE, la classe de défaut que ce firmware
     * traque. L'opérateur relance `anim on` s'il le veut. */
    if (s_anim_on) {
        s_anim_on = false;
        ESP_LOGW(TAG, "reconstruction de scène : le stimulus `anim` est ARRÊTÉ "
                      "(relancer `anim on` si besoin)");
    }
    s_label_dash = NULL;
    s_label_det = NULL;
    s_bar = NULL;
    s_det_titre = NULL;
    s_det_valeur = NULL;
    s_det_minmax = NULL;
    s_det_sec = NULL;
    s_case_cpu_valeur = NULL;

    if (s_nav == DN_NAV_SCREENS) {
        /* Les deux racines sont (re)construites ensemble : un `ui bg psram` qui
         * ne referait qu'un seul des deux écrans laisserait l'autre blitter
         * l'ancienne source — et l'A/B des fonds mesurerait deux choses à la
         * fois. */
        lv_obj_t *ancien_dash = s_scr_dash;
        lv_obj_t *ancien_det = s_scr_detail;
        /*
         * ⚠️ L'ÉCRAN SORTANT N'EST PAS TOUJOURS L'UNE DES DEUX RACINES, et c'est
         *    la FUITE trouvée par la revue de dn1-4. Deux cas où il est un
         *    troisième objet que personne ne détruisait :
         *      - au boot, c'est l'écran par défaut créé par lv_display_create ;
         *      - en revenant de REBUILD, c'est celui que dn_ui_set_nav_model a
         *        créé pour héberger l'arbre reconstruit.
         *    `lv_screen_load()` est un `lv_screen_load_anim(..., auto_del=false)`
         *    : il ne détruit RIEN. Un aller-retour `screens -> rebuild ->
         *    screens` — exactement l'A/B que la console invite à faire pour
         *    arbitrer AC4 — abandonnait donc un arbre dashboard COMPLET (image,
         *    voile, barre, 6 cases, 14 labels, MENU, label vivant) dans les 64 Ko
         *    du tas LVGL. Et la « preuve de non-fuite » de `nav ab` ne pouvait
         *    pas le voir : elle mesure la RAM interne et la PSRAM, alors que ce
         *    tas est un pool STATIQUE en .bss (LV_MEM_ADR=0).
         */
        lv_obj_t *sortant = lv_screen_active();
        s_scr_dash = lv_obj_create(NULL);
        build_dashboard(s_scr_dash); /* remplit s_label_dash */
        s_scr_detail = lv_obj_create(NULL);
        build_detail(s_scr_detail, s_metrique); /* remplit s_label_det */
        lv_screen_load(s_vue == DN_VUE_DETAIL ? s_scr_detail : s_scr_dash);
        /* Supprimés APRÈS le chargement du nouvel écran : supprimer l'écran
         * actif avant d'en charger un autre laisserait LVGL sans écran courant
         * le temps d'une instruction. */
        if (ancien_dash) {
            lv_obj_delete(ancien_dash);
        }
        if (ancien_det) {
            lv_obj_delete(ancien_det);
        }
        if (sortant && sortant != ancien_dash && sortant != ancien_det &&
            sortant != s_scr_dash && sortant != s_scr_detail) {
            lv_obj_delete(sortant);
        }
        return;
    }

    /* REBUILD : un seul écran, celui de LVGL, vidé puis redessiné. */
    lv_obj_t *scr = lv_screen_active();
    lv_obj_clean(scr);
    if (s_vue == DN_VUE_DETAIL) {
        build_detail(scr, s_metrique);
    } else {
        build_dashboard(scr);
    }
}

/* ── Navigation : le travail ──────────────────────────────────────────────── */

/*
 * `cible` : 0 = dashboard, 1..6 = détail de la métrique cible-1.
 * `t_clic` : instant d'origine pour la latence (0 = celui du dernier clic).
 * Appelée DANS la tâche LVGL, hors contexte d'événement (via lv_async_call) ou
 * sous le verrou pris par l'appelant public. Ne prend pas le verrou elle-même.
 */
static bool nav_appliquer(int cible, int64_t t_clic)
{
    dn_ui_vue_t vue = cible == 0 ? DN_VUE_DASHBOARD : DN_VUE_DETAIL;
    int idx = cible == 0 ? s_metrique : cible - 1;

    /* Rien à faire : on DÉSARME plutôt que de laisser un chronomètre en vol.
     * Un double tap sur la même case empilerait deux transitions ; la seconde
     * n'a rien à redessiner, et un chrono armé sans redessin serait arrêté par
     * le premier flush venu — une latence inventée.
     * ⚠️ On rend FALSE (revue dn1-4) : l'appelant annonçait « détail ouvert » /
     * « retour au dashboard » pour une transition qui n'avait pas eu lieu, et
     * `nav ab` perdait silencieusement un échantillon quand la série démarrait
     * depuis un détail déjà affiché — `lat.n` valait 39 au lieu de 40, et
     * servait de dénominateur à la moyenne publiée par AC5. */
    if (vue == s_vue && (vue == DN_VUE_DASHBOARD || idx == s_metrique)) {
        return false;
    }

    s_vue = vue;
    s_metrique = idx;

    if (s_nav == DN_NAV_SCREENS && s_scr_dash && s_scr_detail) {
        /*
         * ⚠️ LE STIMULUS ADVERSE NE SURVIT PAS À UNE BASCULE D'ÉCRAN, et l'ombre
         *    doit le dire. En modèle SCREENS, rien n'est détruit : la barre
         *    d'`anim` reste accrochée à l'écran qu'on quitte, donc INVISIBLE,
         *    pendant que `s_anim_on` continuerait d'annoncer « stimulus EN
         *    COURS » à `ui`, `anim` et à l'étiquette de `fps`. Une mesure
         *    étiquetée « sous stimulus » sans stimulus à l'écran est exactement
         *    le défaut que la revue de dn1-3 a corrigé 21 fois.
         *    On l'arrête donc pour de bon, comme le fait la reconstruction.
         */
        if (s_bar) {
            lv_anim_delete(s_bar, bar_set_x);
            lv_obj_delete(s_bar);
            s_bar = NULL;
        }
        s_anim_on = false;
        if (vue == DN_VUE_DETAIL) {
            detail_reparametrer(idx);
            lv_screen_load(s_scr_detail);
        } else {
            lv_screen_load(s_scr_dash);
        }
    } else {
        lv_obj_t *scr = lv_screen_active();
        lv_obj_clean(scr);
        s_label_dash = NULL;
        s_label_det = NULL;
        s_bar = NULL;
        s_det_titre = NULL;
        s_det_valeur = NULL;
        s_det_minmax = NULL;
        s_det_sec = NULL;
        s_case_cpu_valeur = NULL;
        /* Même règle qu'en reconstruction complète : la barre du stimulus vient
         * d'être détruite, l'ombre le dit. Sans le log ici (il tomberait à chaque
         * transition), mais avec le même effet sur l'état annoncé. */
        s_anim_on = false;
        if (vue == DN_VUE_DETAIL) {
            build_detail(scr, idx);
        } else {
            build_dashboard(scr);
        }
    }

    s_nav_count++;
    /* Le chronomètre est armé ICI, la nouvelle vue étant posée : le prochain
     * cycle de rafraîchissement est CELUI de la transition. Voir dn_touch.h. */
    dn_touch_latence_arm(t_clic);
    return true;
}

dn_ui_vue_t dn_ui_vue(void) { return s_vue; }
int dn_ui_metrique(void) { return s_metrique; }
uint32_t dn_ui_nav_count(void) { return s_nav_count; }
int dn_ui_dernier_tap(void) { return s_dernier_tap; }
uint32_t dn_ui_taps(void) { return s_taps; }

const char *dn_ui_zone_nom(int zone)
{
    if (zone == DN_UI_ZONE_MENU) {
        return "MENU (no-op)";
    }
    if (zone == DN_UI_ZONE_RETOUR) {
        return "RETOUR";
    }
    if (zone >= 0 && zone < DN_UI_METRIQUES) {
        return k_metriques[zone].nom;
    }
    return "aucune";
}

uint32_t dn_ui_menu_taps(void) { return s_menu_taps; }
uint32_t dn_ui_async_refus(void) { return s_async_refus; }
dn_nav_model_t dn_ui_get_nav_model(void) { return s_nav; }

/*
 * Les compteurs de la couche UI n'avaient AUCUN reset (revue dn1-4), alors que
 * la console imprime elle-même « comparer proprement : `touch reset` puis
 * `nav ab 20` » au moment de basculer de modèle. `touch reset` ne remettait à
 * zéro que ceux de dn_touch : après une bascule, `nav` continuait d'afficher les
 * taps et le nombre de transitions du modèle PRÉCÉDENT, sous une bannière qui
 * annonçait le nouveau. Le compteur d'un modèle était publié comme celui de
 * l'autre.
 */
void dn_ui_reset_compteurs(void)
{
    s_taps = 0;
    s_menu_taps = 0;
    s_nav_count = 0;
    s_async_refus = 0;
    s_dernier_tap = DN_UI_ZONE_AUCUNE;
}

/*
 * ⚠️ ESP_ERR_INVALID_STATE = « la vue demandée était DÉJÀ l'active, rien n'a
 *    bougé ». Ce n'est pas une panne, c'est un no-op — mais l'appelant DOIT
 *    pouvoir le distinguer d'une transition réelle : la console annonçait
 *    « détail ouvert » et `nav ab` comptait une itération pour un écran qui
 *    n'avait pas changé, ce qui décalait le dénominateur de la latence d'AC5.
 */
esp_err_t dn_ui_nav_open(int idx)
{
    if (idx < 0 || idx >= DN_UI_METRIQUES) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!lvgl_port_lock(1000)) {
        return ESP_ERR_TIMEOUT;
    }
    bool fait = nav_appliquer(idx + 1, esp_timer_get_time());
    lvgl_port_unlock();
    return fait ? ESP_OK : ESP_ERR_INVALID_STATE;
}

esp_err_t dn_ui_nav_back(void)
{
    if (!lvgl_port_lock(1000)) {
        return ESP_ERR_TIMEOUT;
    }
    bool fait = nav_appliquer(0, esp_timer_get_time());
    lvgl_port_unlock();
    return fait ? ESP_OK : ESP_ERR_INVALID_STATE;
}

esp_err_t dn_ui_set_nav_model(dn_nav_model_t m)
{
    if (m >= DN_NAV_COUNT) {
        return ESP_ERR_INVALID_ARG;
    }
    if (m == s_nav) {
        return ESP_OK;
    }
    if (!lvgl_port_lock(2000)) {
        return ESP_ERR_TIMEOUT;
    }
    /*
     * On repart du DASHBOARD, toujours. Les deux modèles ne tiennent pas leur
     * état au même endroit (un écran vidé/reconstruit d'un côté, deux racines
     * permanentes de l'autre) : prétendre conserver la vue courante ferait mentir
     * l'un des deux, et la première mesure d'après bascule serait à jeter.
     */
    s_vue = DN_VUE_DASHBOARD;

    if (s_nav == DN_NAV_SCREENS) {
        /* On QUITTE screens : l'écran actif redevient celui de LVGL, et les deux
         * racines sont libérées. Ordre non négociable — charger d'abord, détruire
         * ensuite (voir build_scene). */
        lv_obj_t *neuf = lv_obj_create(NULL);
        lv_screen_load(neuf);
        if (s_scr_dash) {
            lv_obj_delete(s_scr_dash);
            s_scr_dash = NULL;
        }
        if (s_scr_detail) {
            lv_obj_delete(s_scr_detail);
            s_scr_detail = NULL;
        }
    }
    s_nav = m;
    build_scene();
    lvgl_port_unlock();
    ESP_LOGI(TAG, "modèle de navigation : « %s »", dn_nav_model_name(m));
    return ESP_OK;
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
            /*
             * ⚠️ L'ÉTIQUETTE MENTAIT : elle disait « le bounce buffer est
             *    DISQUALIFIÉ (watchdog) — dn1-2 » alors que dn1-4 l'a
             *    RÉHABILITÉ et en fait le défaut de la carte
             *    (DN_DEFAULT_BOUNCE_PX = 4800). Au-delà de la phrase, `bb_mode`
             *    n'est pas décoratif : il décide quel callback le portage
             *    enregistre (on_bounce_frame_finish au lieu de on_vsync,
             *    esp_lvgl_port_disp.c) — un piège armé pour la première mesure
             *    en num_fbs=2.
             *
             * ⛔ ON NE LE MET PAS À 1 « PARCE QUE C'EST PLUS JUSTE » : le
             *    portage n'arme cette mécanique qu'avec avoid_tearing, donc
             *    num_fbs>=2, et basculer le callback du panneau sans témoin
             *    serait un changement de comportement non mesuré — exactement ce
             *    que l'arbitrage dn1-3 (AC6) interdit. On le fait donc SUIVRE la
             *    réalité, couplé à avoid_tearing : la valeur reste 0 aujourd'hui
             *    (num_fbs=1 => s_direct_mode faux), et elle sera juste d'office
             *    le jour où num_fbs=2 sera rejoué. Ce jour-là : témoin vsync
             *    obligatoire (dn_measure_vsync_alive), le callback change.
             */
            .bb_mode = (s_direct_mode && dn_display_bounce_px() > 0) ? 1 : 0,
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

lv_display_t *dn_ui_display(void) { return s_disp; }

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
    /* LES DEUX labels, pas seulement celui de la vue affichée : en modèle
     * SCREENS l'autre écran survit à la commande, et le retrouver visible à la
     * bascule suivante ferait mentir `ui` — qui annonce un seul état pour un
     * réglage qui en aurait eu deux. */
    lv_obj_t *labels[2] = {s_label_dash, s_label_det};
    for (int i = 0; i < 2; i++) {
        if (!labels[i]) {
            continue;
        }
        if (on) {
            lv_obj_clear_flag(labels[i], LV_OBJ_FLAG_HIDDEN);
        } else {
            lv_obj_add_flag(labels[i], LV_OBJ_FLAG_HIDDEN);
        }
    }
    lvgl_port_unlock();
}

bool dn_ui_cpu_maj(int dixiemes, bool valide, bool *label_pose)
{
    if (label_pose) {
        *label_pose = false;
    }
    if (!lvgl_port_lock(1000)) {
        /* Pas de log ici : l'appelant (tâche dn_link) retente 250 ms plus tard,
         * un LOGE par tentative sous charge noierait la console — le refus se
         * lit dans le retour, comme dn_ui_force_full_redraw. */
        return false;
    }
    s_cpu_valide = valide && dixiemes >= 0 && dixiemes <= 1000;
    if (s_cpu_valide) {
        /* Virgule française, comme les factices (« 12,4 Go »). Pas d'accent :
         * la police montserrat n'a que la plage de base (legs dn3-1). */
        snprintf(s_cpu_texte, sizeof(s_cpu_texte), "%d,%d %%", dixiemes / 10,
                 dixiemes % 10);
    } else {
        /* Liaison morte ou jamais vue : la case le DIT au lieu de figer un
         * chiffre qui n'a plus cours (AC7 — le différenciateur du brief en
         * miniature). Le rendu exact est libre, le principe ne l'est pas. */
        snprintf(s_cpu_texte, sizeof(s_cpu_texte), "--");
    }
    /* En modèle SCREENS le dashboard survit en arrière-plan et son label est
     * mis à jour même quand le détail est affiché — LVGL l'accepte, c'est le
     * cas « écran non chargé » qu'AC6 exige de ne pas planter. En REBUILD vue
     * détail, le pointeur est NULL et le texte conservé sera posé à la
     * prochaine (re)construction : rien n'est perdu, rien n'est touché. */
    if (s_case_cpu_valeur) {
        lv_label_set_text(s_case_cpu_valeur, s_cpu_texte);
        lv_obj_set_style_text_color(s_case_cpu_valeur,
                                    s_cpu_valide ? lv_color_white()
                                                 : lv_color_hex(0x9a9a9a),
                                    0);
        /* ⚠️ `s_active` compte AUSSI (correctif de revue 2026-08-16). Quand LVGL
         * est arrêté (`ui off`, `scene <mire>`, `tear`), le mutex reste LIBRE et le
         * texte se pose sans erreur — mais rien n'atteint la dalle. Chronométrer
         * cette poussée, c'était mesurer un geste qui n'a pas eu lieu : le Trap n°2
         * de la story appliqué à sa propre instrumentation. */
        if (label_pose) {
            *label_pose = s_active;
        }
    }
    lvgl_port_unlock();
    return true;
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
         * ⚠️ LE CHRONOMÈTRE DE LATENCE EST DÉSARMÉ (correctif de revue dn1-4).
         *    `nav open 3` puis `ui off` dans les ~300 ms qui suivent laissait un
         *    chrono en vol ; `dn_ui_resume()` fait un redessin complet dont le
         *    dernier flush appelait `dn_touch_latence_stop()` — la DURÉE DE LA
         *    PAUSE entrait alors dans le min/moy/max publié par AC5. Un
         *    échantillon gouverné par l'opérateur, dans la mesure même que
         *    `nav_bloque_par_pause` existe pour protéger.
         */
        dn_touch_latence_desarm();
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
    /*
     * ── L'ÉTAT TACTILE EST VIDÉ *AVANT* DE REPRENDRE ─────────────────────────
     * Trois correctifs de la revue dn1-4, sur un drainage qui n'empêchait pas ce
     * qu'il annonçait :
     *
     * 1. ORDRE. Il était fait APRÈS `lvgl_port_resume()`, donc après que le
     *    timer et la tâche LVGL (priorité 4) sont réarmés : la tâche pouvait
     *    préempter le REPL et lire l'indev pendant que le drain faisait encore
     *    sa transaction I²C bloquante. La première lecture pouvait donc précéder
     *    le drainage. On draine d'abord, on reprend ensuite.
     * 2. VERROU. `esp_lcd_touch_read_data()` n'a aucun verrou interne et le
     *    drain tournait depuis la tâche REPL, concurremment à `dn_touch_read()`
     *    dans la tâche LVGL, sur un `s_appuye` volatile mais non atomique.
     * 3. CE QUI PRODUIT LE CLIC. Le clic ne naît pas de `s_appuye` mais de la
     *    machine d'état de l'INDEV LVGL (`pointer.act_obj` + transition
     *    PRESSED->RELEASED). Jeter une lecture ne la touchait pas : un doigt
     *    relâché pendant `ui off` laissait `act_obj` armé, et la première
     *    lecture après reprise rendait RELEASED — donc un CLICKED, donc
     *    l'ouverture d'un détail que personne n'a demandé, exactement ce que le
     *    commentaire promettait d'exclure. `dn_touch_drain()` fait désormais le
     *    `lv_indev_reset()` qui manquait.
     */
    dn_touch_drain(); /* prend le verrou lui-même — règle du dépôt */
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

/*
 * Octets UTILISÉS du tas LVGL. C'est le SEUL instrument capable de voir une
 * fuite d'objets LVGL : le tas est un pool statique en .bss (LV_MEM_ADR=0), donc
 * aucun lv_obj_create ne passe par heap_caps_malloc et la RAM interne / la PSRAM
 * n'en disent RIEN. La « preuve de non-fuite » d'AC4 mesurait exactement ces
 * deux tas-là, et affichait « delta 0 o » avec ou sans fuite (revue dn1-4).
 * Rend 0 si le verrou n'a pas été pris — l'appelant doit le dire plutôt que de
 * publier un zéro qui ressemble à une bonne nouvelle.
 */
size_t dn_ui_lvgl_used(void)
{
    lv_mem_monitor_t mon;
    if (!lvgl_port_lock(1000)) {
        return 0;
    }
    lv_mem_monitor(&mon);
    lvgl_port_unlock();
    return (size_t)(mon.total_size - mon.free_size);
}

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

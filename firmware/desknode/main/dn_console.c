#include "dn_console.h"

#include <errno.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

#include "dn_asset.h"
#include "dn_bootcfg.h"
#include "dn_display.h"
#include "dn_measure.h"
#include "dn_patterns.h"
#include "dn_pins.h"
#include "dn_recal.h"
#include "dn_stimulus.h"
#include "dn_ui.h"
#include "esp_console.h"
#include "esp_log.h"
#include "esp_partition.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "dn_cli";

/*
 * La scène courante n'est PLUS suivie ici, et c'est un correctif de CR.
 *
 * `app_main` dessine l'asset au boot en appelant `dn_pattern_draw()` DIRECTEMENT,
 * sans passer par `show_scene()` — le seul endroit qui écrivait la copie locale.
 * Conséquence mesurée : de l'allumage jusqu'à la première commande `scene`, le
 * bandeau annonçait « scène "-" » et la PREMIÈRE trace `fps` était étiquetée
 * `scene=-`, alors que le Living PCB était bel et bien à l'écran. Or c'est
 * précisément cette première mesure qu'AC4 veut voir se suffire à elle-même.
 *
 * `dn_pattern_draw()` enregistre désormais ce qu'il dessine quel que soit
 * l'appelant, et `dn_pattern_last_scene()` le restitue : une seule source de
 * vérité, celle du module qui sait réellement ce qui a été tracé.
 */
static const char *scene_courante(void)
{
    dn_scene_t s = dn_pattern_last_scene();
    return s < DN_SCENE_COUNT ? dn_scene_name(s) : "-";
}

/* ── Analyse d'arguments ──────────────────────────────────────────────────── */
/*
 * Trois commandes se contentaient de `strcmp(argv[1], "on") == 0` : tout ce qui
 * n'était pas exactement « on » valait OFF, EN SILENCE. `bl 1`, `disp ON`, ou
 * la moindre faute de frappe éteignaient donc l'écran en répondant « OFF » sans
 * jamais dire que l'argument n'avait pas été compris. Sur `disp`, cela
 * reproduit à la demande la DALLE GRISE qui a coûté le premier allumage de
 * cette story — et l'opérateur croit avoir tapé une commande valide.
 *
 * On exige donc un mot connu, et on ne touche au matériel qu'APRÈS.
 */
static bool parse_on_off(const char *mot, bool *out_on)
{
    if (strcasecmp(mot, "on") == 0) {
        *out_on = true;
        return true;
    }
    if (strcasecmp(mot, "off") == 0) {
        *out_on = false;
        return true;
    }
    return false;
}

/*
 * `atoi` ne sait pas dire « ce n'est pas un nombre » : il rend 0. Deux dégâts
 * MESURÉS, tous deux silencieux :
 *   - `set bounce x` -> 0, or 0 est une valeur PARFAITEMENT LÉGALE de
 *     bounce_px. La commande répondait « écrit en NVS » et l'opérateur repartait
 *     convaincu d'avoir configuré un bounce buffer qui n'existe pas ;
 *   - `fps 3000000` -> `seconds * 1000` déborde l'int (comportement indéfini),
 *     puis pdMS_TO_TICKS caste vers un TickType_t NON SIGNÉ : la tâche du REPL
 *     se bloque jusqu'à ~49 jours, sans aucun moyen d'annuler.
 * `strtol` + `endptr` refuse ce que `atoi` avalait.
 */
static bool parse_entier(const char *texte, long *out)
{
    char *fin = NULL;
    errno = 0;
    long v = strtol(texte, &fin, 10);
    if (fin == texte || *fin != '\0' || errno == ERANGE) {
        return false;
    }
    *out = v;
    return true;
}

/*
 * Verrou des commandes de MESURE contre le stimulus de tearing.
 *
 * La tâche de tearing tourne sur le cœur 1 en priorité 4 et redessine une trame
 * entière en boucle. Une commande de mesure lancée depuis le REPL (cœur 0)
 * pendant ce temps entre en collision de deux façons :
 *   - `dn_display_present()` fait `s_draw_index = (s_draw_index + 1) % n`, une
 *     lecture-modification-écriture NON protégée, exécutée simultanément par
 *     deux cœurs ;
 *   - les deux memset/memcpy de 614 400 o visent le buffer rendu par
 *     `dn_display_draw_buffer()`, et `draw_bitmap` peut se voir remettre celui
 *     que la DMA est en train de balayer.
 * Le chiffre publié serait donc contaminé par un redessin plein écran
 * concurrent — c'est-à-dire faux, sans que rien ne le signale.
 *
 * Renvoie true (et explique) si la commande doit être refusée.
 */
static bool tearing_bloque(const char *commande)
{
    if (!dn_stim_tear_running()) {
        return false;
    }
    printf("refusé : le stimulus de tearing tourne — `tear off` d'abord.\n");
    printf("   `%s` et la tâche de tearing écrivent dans le MÊME framebuffer :\n",
           commande);
    printf("   la mesure serait contaminée par un redessin plein écran.\n");
    return true;
}

/*
 * Verrou des commandes qui écrivent DIRECTEMENT dans le framebuffer, face à
 * LVGL (dn1-3).
 *
 * `scene` et `tear` viennent de dn1-2 : elles dessinent une trame entière à la
 * main puis appellent `dn_display_present()`. LVGL, lui, croit que le
 * framebuffer reflète son arbre d'objets et ne redessine que ce qu'il a
 * invalidé. Les laisser tourner ensemble donne deux écrivains sur le même
 * tampon, et surtout un écran dont on ne peut plus dire QUI a produit ce qu'on
 * voit — c'est-à-dire une observation à l'œil inutilisable.
 *
 * AC5 a précisément besoin du chemin BRUT (les scènes alternées de dn1-2) : la
 * sortie est `ui off`, pas une fusion des deux.
 *
 * Renvoie true (et explique) si la commande doit être refusée.
 */
static bool ui_bloque(const char *commande)
{
    if (!dn_ui_active()) {
        return false;
    }
    printf("refusé : LVGL tient l'écran — `ui off` d'abord.\n");
    printf("   `%s` dessine une trame ENTIÈRE à la main, LVGL ne redessine que\n",
           commande);
    printf("   ses zones invalidées : les deux ensemble donnent un écran dont on\n");
    printf("   ne peut plus attribuer ce qu'on voit. `ui on` pour revenir.\n");
    return true;
}

/* ────────────────────────────────────────────────────────────────────────── */

static void show_scene(dn_scene_t scene)
{
    if (dn_stim_tear_running()) {
        ESP_LOGW(TAG, "le stimulus de tearing tourne — `tear off` d'abord");
        return;
    }
    uint16_t *buf = dn_display_draw_buffer();
    dn_pattern_draw(buf, scene);
    int64_t present_us = dn_display_present();
    if (present_us < 0) {
        /* `dn_display_present()` rend -1 quand `draw_bitmap` a refusé : la dalle
         * garde alors la trame précédente. Ne pas présenter ce -1 comme une
         * durée mesurée — c'est exactement le genre de chiffre qu'on retrouve
         * ensuite dans un tableau en croyant l'avoir mesuré. */
        ESP_LOGE(TAG, "scène « %s » NON présentée — la bascule a échoué",
                 dn_scene_name(scene));
        return;
    }
    ESP_LOGI(TAG, "scène « %s » affichée (présentation : %lld us)",
             dn_scene_name(scene), (long long)present_us);
    dn_pattern_explain(scene);
    if (scene == DN_SCENE_ASSET) {
        dn_asset_log();
    }
}

static int cmd_scene(int argc, char **argv)
{
    if (argc >= 2 && ui_bloque("scene")) {
        return 1;
    }
    if (argc < 2) {
        printf("scènes : ");
        for (int i = 0; i < DN_SCENE_COUNT; i++) {
            printf("%s%s", dn_scene_name((dn_scene_t)i),
                   i + 1 < DN_SCENE_COUNT ? " " : "\n");
        }
        printf("scène courante : %s\n",
               dn_pattern_last_scene() < DN_SCENE_COUNT ? scene_courante()
                                                        : "(aucune)");
        return 0;
    }
    dn_scene_t s = dn_scene_from_name(argv[1]);
    if (s >= DN_SCENE_COUNT) {
        printf("scène inconnue : %s\n", argv[1]);
        return 1;
    }
    show_scene(s);
    return 0;
}

#define DN_FPS_MIN_S 10 /* AC4 : au moins 10 s */
/* Plafond : au-delà, `seconds * 1000` déborde l'int et pdMS_TO_TICKS bloque le
 * REPL pour des semaines, sans commande pour l'interrompre. 600 s (10 min)
 * dépassent déjà de loin toute mesure de fps utile. */
#define DN_FPS_MAX_S 600

static int cmd_fps(int argc, char **argv)
{
    long seconds = DN_FPS_MIN_S;
    if (argc >= 2) {
        if (!parse_entier(argv[1], &seconds)) {
            printf("usage : fps [secondes] — « %s » n'est pas un nombre.\n",
                   argv[1]);
            return 1;
        }
        if (seconds < DN_FPS_MIN_S) {
            printf("⚠️ AC4 exige au moins %d s ; %ld s demandées, on corrige à %d.\n",
                   DN_FPS_MIN_S, seconds, DN_FPS_MIN_S);
            seconds = DN_FPS_MIN_S;
        } else if (seconds > DN_FPS_MAX_S) {
            printf("⚠️ %ld s dépasse le plafond de %d s — au-delà, l'attente\n",
                   seconds, DN_FPS_MAX_S);
            printf("   déborde et bloque la console sans retour. On corrige à %d.\n",
                   DN_FPS_MAX_S);
            seconds = DN_FPS_MAX_S;
        }
    }
    /*
     * ⚠️ L'ÉTIQUETTE DOIT DIRE QUI DESSINE — c'est une correction de dn1-2 qu'il
     *    ne faut pas perdre. À l'époque, la trace annonçait « scene=- » alors
     *    qu'une image était bel et bien affichée, parce que le dessin du boot ne
     *    passait pas par show_scene(). Depuis dn1-3, c'est LVGL qui dessine et
     *    plus aucune scène brute n'est tracée au boot : sans cette distinction,
     *    la première ligne `fps` repartirait exactement dans le même mensonge,
     *    sous une autre forme.
     */
    char etiquette[80];
    if (dn_ui_active()) {
        snprintf(etiquette, sizeof(etiquette),
                 "num_fbs=%d bounce=%u LVGL(%s, label %s)",
                 dn_display_num_fbs(), (unsigned)dn_display_bounce_px(),
                 dn_ui_anim_running() ? "stimulus" : "repos",
                 dn_ui_label_shown() ? "on" : "off");
    } else {
        snprintf(etiquette, sizeof(etiquette), "num_fbs=%d bounce=%u scene=%s",
                 dn_display_num_fbs(), (unsigned)dn_display_bounce_px(),
                 scene_courante());
    }
    dn_measure_report_fps(etiquette, (int)seconds);
    return 0;
}

static int cmd_mem(int argc, char **argv)
{
    (void)argc;
    (void)argv;
    size_t avant = 0, apres = 0;
    dn_measure_get_psram_note(&avant, &apres);
    printf("PSRAM libre maintenant : %u o\n", (unsigned)dn_measure_psram_free());
    printf("RAM interne libre      : %u o\n",
           (unsigned)dn_measure_internal_free());
    printf("PSRAM avant framebuffers : %u o\n", (unsigned)avant);
    printf("PSRAM après framebuffers : %u o\n", (unsigned)apres);
    printf("=> consommée par %d framebuffer(s) : %d o (théorie : %u o)\n",
           dn_display_num_fbs(), (int)((long)avant - (long)apres),
           (unsigned)(DN_FB_BYTES * dn_display_num_fbs()));
    printf("bounce buffer : %u px (alloué en RAM INTERNE, pas en PSRAM)\n",
           (unsigned)dn_display_bounce_px());
    return 0;
}

/*
 * Bande passante réelle des trois chemins qui comptent. Ils sont mesurés
 * SÉPARÉMENT parce qu'ils n'ont pas le même goulot, et qu'un seul chiffre
 * global induirait en erreur la marche qui devra tenir un budget (dn3-2) :
 *   - remplissage       : écriture PSRAM pure, le cas d'un aplat ;
 *   - PSRAM -> PSRAM    : lecture + écriture PSRAM, le cas d'un blit ;
 *   - flash -> PSRAM    : dominé par la LECTURE FLASH, pas par la PSRAM —
 *                         c'est le chemin de l'asset au boot, et c'est le plus
 *                         lent des trois d'un facteur ~2.
 * Rappel du budget : tenir 37,40 Hz impose de produire une trame en moins de
 * 26,7 ms.
 */
static int cmd_bw(int argc, char **argv)
{
    (void)argc;
    (void)argv;
    if (tearing_bloque("bw")) {
        return 1;
    }
    uint16_t *fb = dn_display_draw_buffer();
    const int passes = 5;

    int64_t best_fill = INT64_MAX;
    for (int i = 0; i < passes; i++) {
        int64_t t0 = esp_timer_get_time();
        memset(fb, (i & 1) ? 0xFF : 0x00, DN_FB_BYTES);
        int64_t dt = esp_timer_get_time() - t0;
        if (dt < best_fill) {
            best_fill = dt;
        }
    }
    printf("remplissage PSRAM (memset %u o) : %lld us => %.1f Mo/s\n",
           (unsigned)DN_FB_BYTES, (long long)best_fill,
           (double)DN_FB_BYTES / (double)best_fill);

    if (dn_display_num_fbs() >= 2) {
        /* On lit l'AUTRE framebuffer : deux zones PSRAM distinctes, donc un
         * vrai aller-retour, pas une copie sur soi-même. */
        dn_display_present();
        uint16_t *autre = dn_display_draw_buffer();
        int64_t best_blit = INT64_MAX;
        for (int i = 0; i < passes; i++) {
            int64_t t0 = esp_timer_get_time();
            memcpy(autre, fb, DN_FB_BYTES);
            int64_t dt = esp_timer_get_time() - t0;
            if (dt < best_blit) {
                best_blit = dt;
            }
        }
        printf("PSRAM -> PSRAM (memcpy %u o)    : %lld us => %.1f Mo/s\n",
               (unsigned)DN_FB_BYTES, (long long)best_blit,
               (double)DN_FB_BYTES / (double)best_blit);
    } else {
        printf("PSRAM -> PSRAM : non mesuré (il faut num_fbs >= 2)\n");
    }

    if (dn_asset_pixels()) {
        int64_t best_asset = INT64_MAX;
        for (int i = 0; i < 3; i++) {
            dn_asset_copy_to(dn_display_draw_buffer());
            int64_t dt = dn_asset_last_copy_us();
            if (dt < best_asset) {
                best_asset = dt;
            }
        }
        printf("flash mmap -> PSRAM (%u o)      : %lld us => %.1f Mo/s\n",
               (unsigned)DN_FB_BYTES, (long long)best_asset,
               (double)DN_FB_BYTES / (double)best_asset);
    }
    printf("budget d'une trame à 37,40 Hz : 26,7 ms.\n");

    /*
     * `bw` laissait l'écran NOIR, et sans un mot. Le chemin exact : à num_fbs>=2
     * la dernière passe de remplissage est un memset 0x00 (passes=5, donc i=4 au
     * dernier tour, donc pair, donc `(i & 1) ? 0xFF : 0x00` vaut 0x00), ce noir
     * est ensuite recopié dans l'AUTRE framebuffer par la boucle de blit, et si
     * la partition `assets` est vide la branche
     * dn_asset_pixels() est sautée — le dn_display_present() final présentait
     * donc du noir sur du noir.
     * C'est précisément l'« écran noir trompeur » que tout ce module existe pour
     * empêcher : on ne peut pas distinguer « mesure terminée » de « le driver
     * est mort ». On redessine donc une scène VISIBLE avant de rendre la main :
     * celle qui était affichée, ou à défaut la mire de cadrage.
     */
    dn_scene_t precedente = dn_pattern_last_scene();
    dn_scene_t restaurer =
        (precedente < DN_SCENE_COUNT) ? precedente : DN_SCENE_FRAME;
    dn_pattern_draw(dn_display_draw_buffer(), restaurer);
    dn_display_present();
    printf("scène « %s » restaurée (sans quoi `bw` finit sur un écran noir).\n",
           dn_scene_name(restaurer));
    return 0;
}

static int cmd_cfg(int argc, char **argv)
{
    /*
     * `cfg reset` — la SORTIE DE SECOURS. dn_bootcfg_reset() existait, était
     * déclarée, et n'était appelée de NULLE PART : aucune entrée de k_cmds[] ne
     * menait jusqu'à elle, donc depuis la carte il n'existait aucun moyen de
     * revenir aux défauts sans reflasher. C'est le pendant indispensable du
     * plafond de bounce_px : quand une valeur persistée empêche de démarrer, il
     * faut pouvoir l'effacer, pas seulement l'avoir refusée à l'écriture.
     */
    if (argc >= 2 && strcmp(argv[1], "reset") == 0) {
        esp_err_t err = dn_bootcfg_reset();
        if (err != ESP_OK) {
            printf("effacement refusé : %s\n", esp_err_to_name(err));
            return 1;
        }
        printf("config NVS effacée. `reboot` pour repartir sur les défauts.\n");
        return 0;
    }
    if (argc >= 2) {
        printf("usage : cfg | cfg reset\n");
        return 1;
    }
    dn_bootcfg_t cfg;
    dn_bootcfg_load(&cfg);
    printf("config de boot (NVS) : num_fbs=%d bounce_px=%d draw_lines=%d "
           "draw_psram=%d lvgl_core=%d\n",
           cfg.num_fbs, cfg.bounce_px, cfg.draw_lines, cfg.draw_psram,
           cfg.lvgl_core);
    printf("config ACTIVE        : num_fbs=%d bounce_px=%u draw_lines=%d "
           "draw_psram=%d lvgl_core=%d\n",
           dn_display_num_fbs(), (unsigned)dn_display_bounce_px(),
           dn_ui_draw_lines(), dn_ui_draw_in_psram() ? 1 : 0,
           dn_ui_affinity());
    printf("⚠️ un `set` ne prend effet qu'au `reboot` : les framebuffers sont\n");
    printf("   alloués une fois, au démarrage. C'est voulu — réallouer à chaud\n");
    printf("   laisserait une PSRAM fragmentée et fausserait la mesure suivante.\n");
    printf("`cfg reset` efface la config NVS et rend les défauts au prochain boot.\n");
    return 0;
}

static int cmd_set(int argc, char **argv)
{
    if (argc < 3) {
        printf("usage : set fbs <1|2|3> | set bounce <px> | set lines <%d..%d> "
               "| set drawmem <0|1> "
               "| set core <-1|0|1>\n",
               DN_DRAW_LINES_MIN, DN_DRAW_LINES_MAX);
        return 1;
    }
    bool cle_fbs = (strcmp(argv[1], "fbs") == 0);
    bool cle_bounce = (strcmp(argv[1], "bounce") == 0);
    bool cle_lines = (strcmp(argv[1], "lines") == 0);
    bool cle_drawmem = (strcmp(argv[1], "drawmem") == 0);
    bool cle_core = (strcmp(argv[1], "core") == 0);
    if (!cle_fbs && !cle_bounce && !cle_lines && !cle_drawmem && !cle_core) {
        /* La clé est vérifiée AVANT la valeur : sinon `set foo bar` reprocherait
         * « bar » à l'opérateur alors que la faute est sur « foo ». */
        printf("clé inconnue : %s\n", argv[1]);
        printf("usage : set fbs <1|2|3> | set bounce <px> | set lines <%d..%d> "
               "| set drawmem <0|1> "
               "| set core <-1|0|1>\n",
               DN_DRAW_LINES_MIN, DN_DRAW_LINES_MAX);
        return 1;
    }
    /* Toute valeur passe par parse_entier : `atoi` rendait 0 sur une saisie non
     * numérique, et 0 est une valeur LÉGALE de bounce_px — `set bounce x`
     * répondait donc « écrit en NVS » pour une commande jamais comprise. Sur
     * `fbs`, 0 tombait déjà hors de [1,3], mais on valide les deux de la même
     * façon pour qu'aucune des deux clés ne redevienne silencieuse. */
    long valeur = 0;
    if (!parse_entier(argv[2], &valeur)) {
        printf("« %s » n'est pas un nombre. usage : set fbs <1|2|3> | "
               "set bounce <px>\n",
               argv[2]);
        return 1;
    }
    /* Pas de contrôle de plage i32 supplémentaire : `long` fait 32 bits sur
     * xtensa, donc le ERANGE de strtol couvre exactement ce que NVS stocke. */
    esp_err_t err;
    if (cle_fbs) {
        err = dn_bootcfg_set_num_fbs((int)valeur);
    } else if (cle_lines) {
        err = dn_bootcfg_set_draw_lines((int)valeur);
        if (err == ESP_ERR_INVALID_ARG) {
            printf("⚠️ %ld hors de [%d, %d] lignes.\n", valeur, DN_DRAW_LINES_MIN,
                   DN_DRAW_LINES_MAX);
            printf("   Sous le plancher, ce n'est PAS la copie qui coûte (elle\n");
            printf("   suit l'aire, mesuré) mais l'ATTENTE DE SYNCHRO : un plein\n");
            printf("   écran demande 640/lignes retours verticaux — 433 ms à 32\n");
            printf("   lignes, ~2,1 s à 8. Au-dessus du plafond, %ld lignes font\n",
                   valeur);
            printf("   %ld o de RAM interne — la carte ne démarrerait pas.\n",
                   (long)DN_LCD_H_RES * valeur * 2);
        }
    } else if (cle_drawmem) {
        err = dn_bootcfg_set_draw_psram((int)valeur);
        if (err == ESP_ERR_INVALID_ARG) {
            printf("⚠️ attendu 0 (RAM interne DMA) ou 1 (PSRAM).\n");
        }
    } else if (cle_core) {
        err = dn_bootcfg_set_lvgl_core((int)valeur);
        if (err == ESP_ERR_INVALID_ARG) {
            printf("⚠️ attendu -1 (aucune affinité), 0 ou 1.\n");
        } else if (err == ESP_OK) {
            printf("⚠️ Ce n'est PAS un réglage de confort : tout le pipeline\n");
            printf("   d'affichage (init du panneau, ISR vsync, chemin brut de\n");
            printf("   dn1-2) vit sur le cœur 0. Mettre le rendu EN FACE fait\n");
            printf("   travailler les deux cœurs simultanément sur la mémoire\n");
            printf("   externe — ce que dn1-2 n'a jamais eu.\n");
        }
    } else {
        int px = (int)valeur;
        err = dn_bootcfg_set_bounce_px(px);
        if (err == ESP_ERR_INVALID_ARG && px < 0) {
            printf("⚠️ un bounce buffer négatif n'a pas de sens. 0 = pas de "
                   "bounce buffer.\n");
        } else if (err == ESP_ERR_INVALID_ARG && px > DN_BOUNCE_PX_MAX) {
            printf("⚠️ %d px dépasse le plafond de %d px. Le driver RGB alloue\n",
                   px, DN_BOUNCE_PX_MAX);
            printf("   DEUX tampons de %lld o en RAM INTERNE : au-delà, c'est\n",
                   (long long)px * 2);
            printf("   ESP_ERR_NO_MEM au boot, donc panique, donc CPU HALTÉ par\n");
            printf("   CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT — et plus AUCUNE console\n");
            printf("   pour annuler la valeur, à chaque boot, jusqu'au reflash.\n");
        } else if (err == ESP_ERR_INVALID_ARG && px != 0) {
            printf("⚠️ %d ne divise pas les %d pixels d'une trame : la DMA se\n",
                   px, DN_LCD_TOTAL_PX);
            printf("   décalerait d'un reliquat à chaque trame. Diviseurs utiles :\n");
            printf("   480 (1 ligne), 4800 (10 lignes), 9600 (20), 19200 (40),\n");
            printf("   38400 (80 lignes, le plafond).\n");
        }
    }
    if (err != ESP_OK) {
        printf("refusé : %s\n", esp_err_to_name(err));
        return 1;
    }
    printf("écrit en NVS. `reboot` pour l'appliquer.\n");
    return 0;
}

static int cmd_reboot(int argc, char **argv)
{
    (void)argc;
    (void)argv;
    /*
     * On ARRÊTE les deux stimuli avant de redémarrer, et dans cet ordre-là :
     *   - le stimulus flash peut être au milieu d'un esp_partition_erase_range().
     *     Couper le courant du CPU là-dedans laisse un secteur À MOITIÉ EFFACÉ
     *     dans la partition `stimulus` ; la mesure suivante partirait d'un état
     *     de flash inconnu, ce qui n'est pas rejouable ;
     *   - le stimulus de tearing peut être dans draw_bitmap(), donc en train de
     *     reconfigurer le lien DMA du panneau.
     * dn_stim_*_stop() attendent la fin propre de la boucle en cours — c'est
     * pour cela qu'ils sont appelés AVANT le délai de 100 ms, pas à la place.
     */
    esp_err_t stop_err = dn_stim_tear_stop();
    if (stop_err != ESP_OK) {
        /* On redémarre quand même — c'est ce que l'utilisateur a demandé — mais
         * on le dit : un `esp_restart()` pendant que la tâche dessine encore
         * n'est pas la même chose qu'un redémarrage propre. */
        printf("⚠️ la tâche de tearing n'a pas rendu la main (%s) — "
               "redémarrage forcé par-dessus.\n",
               esp_err_to_name(stop_err));
    }
    dn_stim_flash_stop();
    printf("redémarrage…\n");
    fflush(stdout);
    vTaskDelay(pdMS_TO_TICKS(100));
    esp_restart();
    return 0;
}

static int cmd_tear(int argc, char **argv)
{
    if (argc < 2) {
        double hz = 0;
        int64_t frame_us = 0;
        dn_stim_tear_stats(&hz, &frame_us);
        printf("stimulus tearing : %s — cadence %.1f Hz, dernière trame %lld us\n",
               dn_stim_tear_running() ? "EN COURS" : "arrêté", hz,
               (long long)frame_us);
        /* Les rendez-vous manqués DISQUALIFIENT l'A/B : sur timeout, le mode
         * synchronisé retombe en mode libre pour cette trame-là. Sans ce
         * compteur, `tear sync` et `tear on` peuvent comparer « pas de synchro »
         * à « pas de synchro » en s'annonçant différents. */
        uint32_t miss_vsync = 0, miss_fbdone = 0;
        dn_stim_tear_misses(&miss_vsync, &miss_fbdone);
        if (miss_vsync || miss_fbdone) {
            printf("⚠️ rendez-vous MANQUÉS : %lu vsync, %lu fb_complete — la "
                   "comparaison A/B est à refaire.\n",
                   (unsigned long)miss_vsync, (unsigned long)miss_fbdone);
        }
        return 0;
    }
    static const struct {
        const char *nom;
        dn_tear_mode_t mode;
        const char *attendu;
    } modes[] = {
        {"on", DN_TEAR_SWEEP, "aucune synchronisation — le témoin"},
        {"flip", DN_TEAR_FLIP, "bascule noir/blanc, papillotement qui MASQUE"},
        {"vsync", DN_TEAR_SYNC_VSYNC, "mesuré : escalier sur la moitié de la barre"},
        {"sync", DN_TEAR_SYNC_FBDONE, "RETENU — mesuré : résiduel sur les 15 % du haut"},
        {"both", DN_TEAR_SYNC_BOTH, "mesuré PIRE que `sync` seul — gardé comme réfutation"},
    };
    int mi = -1;
    for (size_t k = 0; k < sizeof(modes) / sizeof(modes[0]); k++) {
        if (strcmp(argv[1], modes[k].nom) == 0) {
            mi = (int)k;
            break;
        }
    }
    if (mi >= 0) {
        if (ui_bloque("tear")) {
            return 1;
        }
        bool flip = (modes[mi].mode == DN_TEAR_FLIP);
        bool sync = (modes[mi].mode != DN_TEAR_SWEEP && !flip);
        printf("mode « %s » : %s\n", modes[mi].nom, modes[mi].attendu);
        esp_err_t err = dn_stim_tear_start(modes[mi].mode);
        if (err != ESP_OK) {
            printf("refusé : %s\n", esp_err_to_name(err));
            return 1;
        }
        if (flip) {
            printf("mode `flip` : bascule noir/blanc plein écran.\n");
            printf("⚠️ son papillotement MASQUE le déchirement — il est là pour\n");
            printf("   la charge, pas pour l'observation. Préférer `tear on`.\n");
        } else if (sync) {
            printf("BARRE VERTICALE, avec bascule SYNCHRONISÉE sur le VSYNC.\n");
            printf("La moitié manquante de « double framebuffer + VSYNC » :\n");
            printf("`draw_bitmap` seul bascule le lien DMA immédiatement, donc\n");
            printf("au milieu du balayage. Ici on attend le retour vertical.\n");
            if (dn_display_num_fbs() < 2) {
                printf("⚠️ num_fbs=%d : sans second framebuffer, se synchroniser ne\n",
                       dn_display_num_fbs());
                printf("   sert à rien — on écrit toujours dans l'image visible.\n");
            }
        } else {
            printf("BARRE VERTICALE blanche qui balaie sur fond noir.\n");
            printf("Regarder l'ARÊTE VERTICALE de la barre :\n");
            printf("  brisée en tranches horizontales décalées => TEARING ;\n");
            printf("  arête droite et franche                   => pas de déchirement VU ;\n");
            printf("  barre nette mais qui saute                => trame perdue.\n");
        }
        if (dn_display_num_fbs() == 1) {
            printf("⚠️ num_fbs=1 : on écrit DANS le framebuffer visible, c'est le\n");
            printf("   TÉMOIN POSITIF. Si rien ne déchire ICI, l'instrument est\n");
            printf("   invalide — ne pas conclure « pas de tearing ».\n");
        }
        return 0;
    }
    if (strcmp(argv[1], "off") == 0) {
        /* `dn_stim_tear_stop()` rend ESP_ERR_TIMEOUT quand la tâche n'est PAS
         * morte dans le budget. Annoncer « arrêté » dans ce cas est ce qui
         * permettait à deux tâches de tearing de coexister : la suivante passait
         * la garde, et plus personne ne savait laquelle dessinait. */
        esp_err_t err = dn_stim_tear_stop();
        double hz = 0;
        dn_stim_tear_stats(&hz, NULL);
        if (err != ESP_OK) {
            printf("⚠️ ARRÊT INCOMPLET (%s) : la tâche de tearing tourne "
                   "encore. Ne rien relancer — attendre, puis re-tenter "
                   "`tear off`.\n",
                   esp_err_to_name(err));
            return 1;
        }
        printf("arrêté. Cadence atteinte : %.1f Hz\n", hz);
        uint32_t miss_vsync = 0, miss_fbdone = 0;
        dn_stim_tear_misses(&miss_vsync, &miss_fbdone);
        if (miss_vsync || miss_fbdone) {
            printf("⚠️ %lu vsync et %lu fb_complete MANQUÉS pendant la course : "
                   "cette cadence ne vaut pas pour l'A/B.\n",
                   (unsigned long)miss_vsync, (unsigned long)miss_fbdone);
        }
        return 0;
    }
    printf("usage : tear [on|vsync|sync|both|flip|off]\n");
    return 1;
}

static int cmd_flash(int argc, char **argv)
{
    if (argc < 2) {
        uint32_t sec = 0;
        uint64_t bytes = 0;
        double rate = 0;
        dn_stim_flash_stats(&sec, &bytes, &rate);
        printf("stimulus flash : %s — %lu secteurs, %llu o, %.0f o/s\n",
               dn_stim_flash_running() ? "EN COURS" : "arrêté",
               (unsigned long)sec, (unsigned long long)bytes, rate);
        /* Distinguer « arrêté » de « arrêté PARCE QUE la flash a refusé ». Sans
         * cela, le compteur de secteurs gelé et un statut rassurant faisaient
         * pointer le garde-fou de la méthode dans le mauvais sens — c'est le
         * piège qui avait déjà produit une conclusion à retirer en AC6. */
        esp_err_t ferr = dn_stim_flash_error();
        if (ferr != ESP_OK) {
            printf("⚠️ le stimulus s'est arrêté SUR ERREUR (%s) : les secteurs "
                   "ci-dessus ne montent plus. Toute observation faite depuis "
                   "est sans stimulus.\n",
                   esp_err_to_name(ferr));
        }
        return 0;
    }
    bool on = false;
    if (!parse_on_off(argv[1], &on)) {
        printf("usage : flash [on|off] — « %s » n'est ni l'un ni l'autre.\n",
               argv[1]);
        return 1;
    }
    if (on) {
        /* `flash on` reste refusé tant que le tearing tourne : les deux stimuli
         * chargent la même PSRAM et le même cache, et on ne saurait plus dire
         * lequel a produit ce qu'on voit. `flash off` et `flash` (les stats),
         * eux, restent TOUJOURS joignables — sinon on ne pourrait plus rien
         * arrêter. */
        if (tearing_bloque("flash on")) {
            return 1;
        }
        /*
         * On cherche la partition ICI, avant d'annoncer quoi que ce soit.
         * dn_stim_flash_start() rend ESP_OK dès que la TÂCHE est créée ; c'est
         * la tâche, ensuite, qui découvre l'absence de la partition et se
         * suicide en journalisant. La console imprimait donc « stimulus flash
         * lancé » puis demandait à l'opérateur de décrire ce qu'il voit — alors
         * qu'il n'y a rigoureusement RIEN à voir. Une invite d'observation
         * devant un stimulus mort, c'est de l'observation fabriquée.
         */
        const esp_partition_t *part = esp_partition_find_first(
            ESP_PARTITION_TYPE_DATA, (esp_partition_subtype_t)0x41, "stimulus");
        if (!part) {
            printf("refusé : partition « stimulus » introuvable.\n");
            printf("   Vérifier `partitions.csv` (type data, sous-type 0x41,\n");
            printf("   étiquette « stimulus ») puis reflasher la table.\n");
            return 1;
        }
        esp_err_t err = dn_stim_flash_start();
        if (err != ESP_OK) {
            printf("refusé : %s\n", esp_err_to_name(err));
            return 1;
        }
        printf("stimulus flash lancé sur « stimulus » (%lu o à 0x%06lx).\n",
               (unsigned long)part->size, (unsigned long)part->address);
        printf("Décrire ce qu'on VOIT, précisément :\n");
        printf("  rien ? une ligne ? un flash de toute la dalle ?\n");
        printf("  une image décalée EN PERMANENCE (la DMA a décroché) ?\n");
        return 0;
    }
    dn_stim_flash_stop();
    return 0;
}

#define DN_BL_RAMPE_MS_MIN 100
#define DN_BL_RAMPE_MS_MAX 10000
#define DN_BL_RAMPE_MS_DEFAUT 1500

static void bl_usage(void)
{
    printf("usage : bl                  — état\n");
    printf("        bl <0..100>         — luminosité en %%\n");
    printf("        bl on | off         — 100 %% / 0 %% (rétrocompat dn1-2)\n");
    printf("        bl ramp <0..100> [ms] — rampe douce (constat AC7)\n");
    printf("        bl freq <200..40000>  — fréquence PWM (le sifflement)\n");
}

static int cmd_bl(int argc, char **argv)
{
    if (argc < 2) {
        printf("rétroéclairage : %d %% à %d Hz (%s)\n",
               dn_display_backlight_pct_state(),
               dn_display_backlight_freq_state(),
               dn_display_backlight_state() ? "allumé" : "ÉTEINT");
        printf("⚠️ `bl 0` éteint le RÉTROÉCLAIRAGE : dalle NOIRE.\n");
        printf("   `disp off` éteint la SORTIE de la dalle : dalle GRISE éclairée.\n");
        printf("   Les deux donnent « plus d'image », par deux mécanismes "
               "différents.\n");
        return 0;
    }

    /* ── bl ramp <pct> [ms] ── */
    if (strcmp(argv[1], "ramp") == 0) {
        if (argc < 3) {
            bl_usage();
            return 1;
        }
        long cible = 0;
        if (!parse_entier(argv[2], &cible)) {
            printf("« %s » n'est pas un nombre.\n", argv[2]);
            return 1;
        }
        long ms = DN_BL_RAMPE_MS_DEFAUT;
        if (argc >= 4 && !parse_entier(argv[3], &ms)) {
            printf("« %s » n'est pas un nombre.\n", argv[3]);
            return 1;
        }
        if (cible < 0 || cible > 100) {
            printf("⚠️ %ld %% hors de [0, 100] — rien touché.\n", cible);
            return 1;
        }
        if (ms < DN_BL_RAMPE_MS_MIN || ms > DN_BL_RAMPE_MS_MAX) {
            /* Bornée comme `fps` et `cpu`, et pour la même raison : la rampe est
             * BLOQUANTE (elle tient la tâche du REPL). Une durée non bornée
             * rendrait la console injoignable sans aucun moyen d'annuler. */
            printf("⚠️ durée hors de [%d, %d] ms — la rampe bloque la console\n",
                   DN_BL_RAMPE_MS_MIN, DN_BL_RAMPE_MS_MAX);
            printf("   pendant tout ce temps, sans commande pour l'interrompre.\n");
            return 1;
        }
        int depart = dn_display_backlight_pct_state();
        printf("rampe %d %% -> %ld %% en %ld ms (la console ne répond pas "
               "pendant ce temps)…\n",
               depart, cible, ms);
        esp_err_t err = dn_display_backlight_ramp((int)cible, (int)ms);
        printf("rampe terminée à %d %% : %s\n", dn_display_backlight_pct_state(),
               esp_err_to_name(err));
        return (err == ESP_OK) ? 0 : 1;
    }

    /* ── bl freq <hz> ── */
    if (strcmp(argv[1], "freq") == 0) {
        if (argc < 3) {
            printf("fréquence PWM : %d Hz\n", dn_display_backlight_freq_state());
            bl_usage();
            return 1;
        }
        long hz = 0;
        if (!parse_entier(argv[2], &hz)) {
            printf("« %s » n'est pas un nombre.\n", argv[2]);
            return 1;
        }
        esp_err_t err = dn_display_backlight_freq((int)hz);
        if (err != ESP_OK) {
            printf("refusé : %s\n", esp_err_to_name(err));
            return 1;
        }
        printf("fréquence PWM : %ld Hz (luminosité inchangée à %d %%)\n", hz,
               dn_display_backlight_pct_state());
        printf("⚠️ 5 000 Hz était le défaut, repris d'un BSP générique avec la\n");
        printf("   mention « inaudible en pratique ». MESURÉ FAUX sur cette\n");
        printf("   carte : à 3 %% de duty, ça siffle ET ça papillote.\n");
        return 0;
    }

    /* ── bl on | off (rétrocompatibilité dn1-2) ── */
    bool on = false;
    if (parse_on_off(argv[1], &on)) {
        esp_err_t err = dn_display_backlight(on);
        printf("rétroéclairage %s (%d %%) : %s\n", on ? "ON" : "OFF",
               dn_display_backlight_pct_state(), esp_err_to_name(err));
        return (err == ESP_OK) ? 0 : 1;
    }

    /* ── bl <0..100> ── */
    long pct = 0;
    if (!parse_entier(argv[1], &pct)) {
        /* Ni « on », ni « off », ni un nombre : on ne touche à RIEN. Leçon
         * dn1-2 — l'ancien code prenait tout ce qui n'était pas « on » pour un
         * « off » et éteignait l'écran sur une faute de frappe. */
        printf("« %s » n'est ni on, ni off, ni un nombre — rien n'a été touché.\n",
               argv[1]);
        bl_usage();
        return 1;
    }
    if (pct < 0 || pct > 100) {
        printf("⚠️ %ld %% hors de [0, 100] — rien n'a été touché.\n", pct);
        return 1;
    }
    esp_err_t err = dn_display_backlight_pct((int)pct);
    printf("rétroéclairage %ld %% : %s\n", pct, esp_err_to_name(err));
    if (err == ESP_OK && pct > 0 && pct <= 5) {
        printf("   (duty bas : c'est ICI qu'on cherche le plancher lisible "
               "d'AC7, le flicker à l'œil et le sifflement à l'oreille.)\n");
    }
    return (err == ESP_OK) ? 0 : 1;
}

/*
 * `flush` — L'INSTRUMENT D'AC3, celui qui transforme « le rafraîchissement est
 * partiel » d'une croyance en un chiffre.
 *
 * Il répond à deux questions que le mot « partiel » confond :
 *   - COMBIEN de pixels sont recopiés par mise à jour ? (l'aire, à comparer aux
 *     307 200 px de l'écran) ;
 *   - COMBIEN DE TEMPS ça prend ? — et la réponse n'est PAS proportionnelle à
 *     l'aire, parce que le driver RGB resynchronise 614 400 o de cache à chaque
 *     appel, quelle que soit la zone (voir dn_ui.h, contrainte 3).
 * Les deux colonnes sont donc lues ensemble, jamais l'une pour l'autre.
 */
static void flush_usage(void)
{
    printf("usage : flush                   — compteurs\n");
    printf("        flush reset             — remet les compteurs à zéro\n");
    printf("        flush sync off|vsync|fbdone — synchronisation du flush\n");
    printf("        flush path bitmap|direct    — par où la zone sale entre\n");
    printf("        flush full              — invalide TOUT l'écran (preuve "
           "négative)\n");
}

static int cmd_flush(int argc, char **argv)
{
    if (argc >= 2 && strcmp(argv[1], "reset") == 0) {
        dn_ui_reset_stats();
        printf("compteurs de flush remis à zéro.\n");
        return 0;
    }
    if (argc >= 2 && strcmp(argv[1], "full") == 0) {
        if (!dn_ui_active()) {
            printf("refusé : LVGL est en pause (`ui on` d'abord).\n");
            return 1;
        }
        dn_ui_reset_stats();
        dn_ui_force_full_redraw();
        /* On laisse le cycle se terminer avant de lire : sans cette attente, on
         * imprimerait les compteurs d'un redessin encore en cours et le chiffre
         * publié serait un instantané au milieu du travail. Un plein écran fait
         * 640/draw_lines flushes ; à 1 vsync l'un en mode `vsync`, c'est au pire
         * ~10 x 27 ms. 2 000 ms couvrent largement. */
        vTaskDelay(pdMS_TO_TICKS(2000));
        printf("redessin PLEIN ÉCRAN forcé — compteurs ci-dessous :\n");
        /* et on continue vers l'affichage */
    } else if (argc >= 2 && strcmp(argv[1], "sync") == 0) {
        if (argc < 3) {
            flush_usage();
            return 1;
        }
        dn_flush_sync_t m;
        if (!dn_flush_sync_from_name(argv[2], &m)) {
            printf("mode inconnu : %s (off | vsync | fbdone)\n", argv[2]);
            return 1;
        }
        dn_ui_set_sync(m);
        dn_ui_reset_stats();
        printf("synchro du flush : %s (compteurs remis à zéro)\n",
               dn_flush_sync_name(m));
        if (m == DN_FLUSH_SYNC_OFF) {
            printf("⚠️ mode TÉMOIN : la copie part à n'importe quel moment du\n");
            printf("   balayage. C'est LUI qui doit produire un déchirement\n");
            printf("   VISIBLE sous `anim on`. S'il n'en produit pas, ce n'est\n");
            printf("   pas que le système est propre — c'est que l'instrument\n");
            printf("   (l'œil + le stimulus) ne sait pas voir, et aucune\n");
            printf("   conclusion « pas de tearing » n'est recevable.\n");
        }
        return 0;
    } else if (argc >= 2 && strcmp(argv[1], "path") == 0) {
        if (argc < 3) {
            flush_usage();
            return 1;
        }
        dn_flush_path_t p;
        if (!dn_flush_path_from_name(argv[2], &p)) {
            printf("chemin inconnu : %s (bitmap | direct)\n", argv[2]);
            return 1;
        }
        esp_err_t err = dn_ui_set_path(p);
        if (err != ESP_OK) {
            printf("refusé : %s\n", esp_err_to_name(err));
            return 1;
        }
        dn_ui_reset_stats();
        printf("chemin du flush : %s (compteurs remis à zéro)\n",
               dn_flush_path_name(p));
        if (p == DN_FLUSH_PATH_BITMAP) {
            printf("`draw_bitmap` resynchronise 614 400 o de cache À CHAQUE\n");
            printf("flush, quelle que soit la zone sale. C'est le chemin qui a\n");
            printf("fait « clignoter l'image comme un déplacement rapide » à\n");
            printf("chaque incrémentation du label, le 2026-08-15.\n");
        } else {
            printf("On écrit les lignes sales dans le framebuffer visible et on\n");
            printf("ne resynchronise QUE ces lignes-là (~15x moins de parcours\n");
            printf("de cache). Même travail utile, même nombre d'octets copiés.\n");
        }
        return 0;
    } else if (argc >= 2) {
        flush_usage();
        return 1;
    }

    dn_flush_stats_t st;
    dn_ui_get_stats(&st);
    if (dn_ui_direct_mode()) {
        printf("rendu : DIRECT sur %d framebuffers — le flush BASCULE, il ne "
               "recopie rien\n",
               dn_display_num_fbs());
        printf("synchro : %s · (chemin et draw buffer sans objet dans ce mode)\n",
               dn_flush_sync_name(dn_ui_get_sync()));
    } else {
        printf("rendu : PARTIEL · synchro : %s · chemin : %s\n",
               dn_flush_sync_name(dn_ui_get_sync()),
               dn_flush_path_name(dn_ui_get_path()));
        printf("draw buffer : %d x %d px (%d o) en %s\n", DN_LCD_H_RES,
               dn_ui_draw_lines(), DN_LCD_H_RES * dn_ui_draw_lines() * 2,
               dn_ui_draw_in_psram() ? "PSRAM" : "RAM interne DMA");
    }
    printf("flushes            : %lu\n", (unsigned long)st.flushes);
    printf("cycles de redessin : %lu\n", (unsigned long)st.cycles);
    if (st.flushes == 0) {
        printf("aucun flush depuis le reset — rien à conclure.\n");
        return 0;
    }
    printf("aire cumulée       : %lu px\n", (unsigned long)st.px);
    printf("  => %lu px par flush en moyenne (écran plein = %d px, soit %.2f %%)\n",
           (unsigned long)(st.px / st.flushes), DN_LCD_TOTAL_PX,
           (double)(st.px / st.flushes) * 100.0 / (double)DN_LCD_TOTAL_PX);
    if (st.cycles > 0) {
        printf("  => %lu px et %.1f flush(es) par CYCLE de redessin\n",
               (unsigned long)(st.px / st.cycles),
               (double)st.flushes / (double)st.cycles);
        printf("     (le CYCLE est l'unité qui compte : c'est ce qu'une mise à\n");
        printf("      jour du label coûte réellement, flushes multiples inclus.)\n");
    }
    printf("plus grande aire   : %lu px\n", (unsigned long)st.max_px);
    printf("copie              : %lu us cumulés, %lu us/flush en moyenne, "
           "%lu us au pire\n",
           (unsigned long)st.copie_us,
           (unsigned long)(st.copie_us / st.flushes),
           (unsigned long)st.max_copie_us);
    printf("attente de synchro : %lu us cumulés, %lu us/flush en moyenne\n",
           (unsigned long)st.attente_us,
           (unsigned long)(st.attente_us / st.flushes));
    printf("   (comptée À PART de la copie : sinon « le flush coûte 27 ms » se\n");
    printf("    lirait comme un problème de bande passante alors que c'est la\n");
    printf("    synchro qui attend sa trame — 26,7 ms de période.)\n");
    if (st.timeouts) {
        printf("⚠️ %lu synchro(s) EXPIRÉE(S) : pour ces flushes-là, le mode\n",
               (unsigned long)st.timeouts);
        printf("   annoncé n'a PAS été appliqué. Toute comparaison A/B qui les\n");
        printf("   inclut compare partiellement « rien » à « rien ».\n");
    }
    printf("rappel : redessiner l'écran ENTIER coûte 36,8 ms de memcpy PSRAM "
           "(§5.4),\n");
    printf("   pour 26,7 ms de période de trame — 1,4x TROP LENT. Les zones\n");
    printf("   sales ne sont pas une élégance, c'est la seule voie qui tient.\n");
    return 0;
}

static int cmd_anim(int argc, char **argv)
{
    if (argc < 2) {
        printf("stimulus adverse LVGL : %s\n",
               dn_ui_anim_running() ? "EN COURS" : "arrêté");
        printf("usage : anim on [periode_ms] | anim off\n");
        printf("Une barre verticale de %d px balaie l'écran de gauche à droite.\n",
               24);
        printf("Le sens est choisi EXPRÈS : la dalle balaie du HAUT vers le BAS,\n");
        printf("donc un déchirement coupe la barre HORIZONTALEMENT et décale les\n");
        printf("deux moitiés — un artefact que l'œil lit sans ambiguïté.\n");
        return 0;
    }
    bool on = false;
    if (!parse_on_off(argv[1], &on)) {
        printf("usage : anim on [periode_ms] | anim off\n");
        return 1;
    }
    long ms = 2000;
    if (on && argc >= 3 && !parse_entier(argv[2], &ms)) {
        printf("« %s » n'est pas un nombre.\n", argv[2]);
        return 1;
    }
    if (!dn_ui_active()) {
        printf("refusé : LVGL est en pause (`ui on` d'abord).\n");
        return 1;
    }
    esp_err_t err = dn_ui_anim(on, (int)ms);
    if (err != ESP_OK) {
        printf("refusé : %s (période attendue entre 200 et 10000 ms)\n",
               esp_err_to_name(err));
        return 1;
    }
    printf("stimulus adverse %s%s\n", on ? "LANCÉ" : "arrêté", on ? " :" : ".");
    if (on) {
        printf("  période %ld ms, synchro du flush : %s\n", ms,
               dn_flush_sync_name(dn_ui_get_sync()));
        printf("  PROTOCOLE AC4 — le témoin positif D'ABORD :\n");
        printf("   1. `flush sync off` puis regarder : la barre DOIT se couper.\n");
        printf("      Si elle ne se coupe pas, l'instrument ne sait pas voir et\n");
        printf("      rien ne peut être conclu ensuite.\n");
        printf("   2. `flush sync vsync`, puis `fbdone` : verdicts SÉPARÉS.\n");
        printf("   3. `anim off` + label seul : le régime PRODUIT, noté à part.\n");
    }
    return 0;
}

static int cmd_ui(int argc, char **argv)
{
    if (argc < 2) {
        printf("LVGL : %s · label %s · stimulus %s · fond depuis %s\n",
               dn_ui_active() ? "ACTIF" : "EN PAUSE",
               dn_ui_label_shown() ? "visible" : "masqué",
               dn_ui_anim_running() ? "EN COURS" : "arrêté",
               dn_ui_bg_is_psram() ? "PSRAM (copie)" : "flash (mmap)");
        size_t ia = 0, ip = 0, pa = 0, pp = 0;
        dn_ui_get_cout(&ia, &ip, &pa, &pp);
        printf("coût en tas de l'init LVGL :\n");
        printf("  RAM interne %u -> %u o  (%d o)\n", (unsigned)ia, (unsigned)ip,
               (int)((long)ia - (long)ip));
        printf("  PSRAM       %u -> %u o  (%d o)\n", (unsigned)pa, (unsigned)pp,
               (int)((long)pa - (long)pp));
        dn_ui_log_mem();
        printf("usage : ui on|off | ui label on|off | ui bg flash|psram\n");
        return 0;
    }

    if (strcmp(argv[1], "label") == 0) {
        bool on = false;
        if (argc < 3 || !parse_on_off(argv[2], &on)) {
            printf("usage : ui label on|off\n");
            return 1;
        }
        dn_ui_label_show(on);
        printf("label %s.\n", on ? "visible" : "masqué");
        return 0;
    }

    if (strcmp(argv[1], "bg") == 0) {
        if (argc < 3) {
            printf("usage : ui bg flash|psram\n");
            return 1;
        }
        bool psram;
        if (strcmp(argv[2], "psram") == 0) {
            psram = true;
        } else if (strcmp(argv[2], "flash") == 0) {
            psram = false;
        } else {
            printf("usage : ui bg flash|psram\n");
            return 1;
        }
        esp_err_t err = dn_ui_bg_psram(psram);
        if (err != ESP_OK) {
            printf("refusé : %s\n", esp_err_to_name(err));
            return 1;
        }
        printf("fond lu depuis %s.\n",
               psram ? "une COPIE PSRAM (+614 400 o)" : "la flash mmap-ée (0 o)");
        printf("⚠️ la source ne change RIEN au coût du flush lui-même : elle\n");
        printf("   change le coût du RE-BLIT du fond sous la zone sale, que LVGL\n");
        printf("   refait à chaque mise à jour du label. `flush reset` puis\n");
        printf("   attendre 60 s pour comparer proprement.\n");
        return 0;
    }

    bool on = false;
    if (!parse_on_off(argv[1], &on)) {
        printf("usage : ui on|off | ui label on|off | ui bg flash|psram\n");
        return 1;
    }
    esp_err_t err = on ? dn_ui_resume() : dn_ui_pause();
    if (err != ESP_OK) {
        printf("refusé : %s\n", esp_err_to_name(err));
        return 1;
    }
    printf("LVGL %s.\n", on ? "repris (redessin complet demandé)" : "mis en PAUSE");
    if (!on) {
        printf("L'écran garde ce que LVGL y avait laissé, et `scene`/`tear`\n");
        printf("peuvent désormais écrire dans le framebuffer (chemin de dn1-2,\n");
        printf("celui dont AC5 a besoin pour les scènes alternées).\n");
    }
    return 0;
}

static int cmd_recal(int argc, char **argv)
{
    if (argc < 2) {
        printf("recalage DMA sur événement de bascule : %d vsync(s) après la "
               "bascule%s\n",
               dn_recal_get_vsyncs(),
               dn_recal_get_vsyncs() == 0 ? " (DÉSACTIVÉ)" : "");
        printf("  recalages joués : %lu · armements perdus : %lu · dernier "
               "retour : %s\n",
               (unsigned long)dn_recal_count(), (unsigned long)dn_recal_rate(),
               esp_err_to_name((esp_err_t)dn_recal_last_err()));
        printf("  num_fbs actif : %d%s\n", dn_display_num_fbs(),
               dn_display_num_fbs() > 1
                   ? ""
                   : " — à UN framebuffer il n'y a pas de bascule, donc jamais "
                     "d'armement");
#if CONFIG_LCD_RGB_RESTART_IN_VSYNC
        printf("⚠️ INERTE dans ce build : CONFIG_LCD_RGB_RESTART_IN_VSYNC=y, le\n");
        printf("   bit posé par esp_lcd_rgb_panel_restart() n'est JAMAIS lu\n");
        printf("   (esp_lcd_panel_rgb.c:1149-1165). Mesurer AC5 impose de\n");
        printf("   rebâtir avec ce symbole à `n`.\n");
#endif
        printf("usage : recal <0..%d>  (0 = désactivé)\n", DN_RECAL_VSYNCS_MAX);
        return 0;
    }
    long n = 0;
    if (!parse_entier(argv[1], &n)) {
        printf("usage : recal <0..%d>\n", DN_RECAL_VSYNCS_MAX);
        return 1;
    }
    esp_err_t err = dn_recal_set_vsyncs((int)n);
    if (err != ESP_OK) {
        printf("refusé : %s — bornes [0, %d]. AC5 borne l'investigation à la\n",
               esp_err_to_name(err), DN_RECAL_VSYNCS_MAX);
        printf("   piste identifiée plus une variante de timing, pas à une\n");
        printf("   spirale d'essais.\n");
        return 1;
    }
    printf("recalage : %ld vsync(s) après chaque bascule.\n", n);
    return 0;
}

static int cmd_disp(int argc, char **argv)
{
    if (argc < 2) {
        printf("sortie d'affichage de la dalle (0x29/0x28) : %s\n",
               dn_display_disp_state() ? "ON" : "OFF");
        printf("⚠️ à ne pas confondre avec `bl` : DISPON OFF donne une dalle\n");
        printf("   GRISE et éclairée, `bl off` donne une dalle NOIRE.\n");
        return 0;
    }
    bool on = false;
    if (!parse_on_off(argv[1], &on)) {
        /* Le cas le plus coûteux du lot : `disp <faute de frappe>` envoyait 0x28
         * et rendait la dalle GRISE — le symptôme exact qui a coûté le premier
         * allumage. On ne touche pas au bus 3-wire tant que le mot n'est pas
         * l'un des deux attendus. */
        printf("usage : disp [on|off] — « %s » n'est ni l'un ni l'autre.\n",
               argv[1]);
        printf("   (rien n'a été envoyé à la dalle : un mot non reconnu valait\n");
        printf("   « off », donc DISPON OFF, donc l'écran GRIS du premier "
               "allumage.)\n");
        return 1;
    }
    esp_err_t err = dn_display_disp_on(on);
    printf("DISPON(%s) : %s\n", on ? "true" : "false", esp_err_to_name(err));
    if (!on) {
        printf("témoin : l'écran doit virer au GRIS uniforme, rétroéclairage\n");
        printf("toujours allumé. C'est exactement le symptôme du premier\n");
        printf("allumage, quand 0x29 n'était pas envoyé.\n");
    }
    return 0;
}

static int cmd_restart_dma(int argc, char **argv)
{
    (void)argc;
    (void)argv;
    /* Relancer la DMA pendant que la tâche de tearing est dans draw_bitmap()
     * reconfigure le lien sous ses pieds : on exige `tear off` d'abord. */
    if (tearing_bloque("dma")) {
        return 1;
    }
    esp_err_t err = dn_display_restart();
    printf("esp_lcd_rgb_panel_restart() : %s\n", esp_err_to_name(err));
    printf("(à essayer si l'image est décalée EN PERMANENCE — la DMA a décroché)\n");
    return 0;
}

/*
 * `cpu` — l'instrument de CHARGE PROCESSEUR d'AC6, jusqu'ici absent.
 *
 * Sans lui, « la configuration d'affichage retenue coûte peu » est une opinion :
 * on ne sait pas ce que consomment le refill DMA, le callback vsync et la
 * recopie de trame, donc on ne sait pas ce qu'il reste pour la marche suivante.
 *
 * DEUX formes, et la fenêtrée est la bonne :
 *   `cpu [secondes]` mesure sur une FENÊTRE. C'est ce qu'on veut : les
 *      compteurs de FreeRTOS sont cumulés depuis le boot, donc une carte allumée
 *      depuis vingt minutes noie la charge du moment dans sa moyenne. Pire, le
 *      compteur de run-time est un esp_timer en µs tronqué à 32 bits : il
 *      REBOUCLE toutes les ~71 minutes, et les pourcentages cumulés deviennent
 *      alors du bruit. Une différence entre deux relevés, elle, reste juste au
 *      travers du rebouclage (soustraction non signée).
 *   `cpu brut` imprime quand même la table cumulée de vTaskGetRunTimeStats(),
 *      pour comparer avec ce que produisent les exemples d'Espressif.
 *
 * Les pourcentages sont rapportés à la SOMME des temps de toutes les tâches sur
 * la fenêtre, pas au compteur total : sur un bicœur, la somme vaut ~2× le temps
 * mural, et rapporter à autre chose donnerait des « 200 % » incompréhensibles.
 * Rapportée à la somme, la ligne IDLE se lit directement comme la RÉSERVE.
 */
#if CONFIG_FREERTOS_GENERATE_RUN_TIME_STATS

#define DN_CPU_WINDOW_MIN_S 1
#define DN_CPU_WINDOW_MAX_S 60

static int cpu_table_cumulee(void)
{
    /* ~40 o par tâche d'après la doc FreeRTOS ; 64 o et quelques tâches de
     * marge, parce qu'un débordement ici écrase le tas sans rien dire. */
    UBaseType_t n = uxTaskGetNumberOfTasks() + 8;
    size_t taille = (size_t)n * 64;
    char *table = malloc(taille);
    if (!table) {
        printf("pas assez de RAM pour la table (%u o demandés)\n",
               (unsigned)taille);
        return 1;
    }
    table[0] = '\0';
    vTaskGetRunTimeStats(table);
    printf("temps CPU CUMULÉ depuis le boot (tâche / ticks / %%) :\n");
    printf("%s", table);
    printf("⚠️ cumulé depuis le boot, et le compteur reboucle toutes les "
           "~71 min.\n");
    printf("   Pour chiffrer la charge ACTUELLE, utiliser `cpu [secondes]`.\n");
    free(table);
    return 0;
}

static int cmd_cpu(int argc, char **argv)
{
    if (argc >= 2 && strcmp(argv[1], "brut") == 0) {
        return cpu_table_cumulee();
    }

    long fenetre = 5;
    if (argc >= 2) {
        if (!parse_entier(argv[1], &fenetre)) {
            printf("usage : cpu [secondes] | cpu brut\n");
            return 1;
        }
        if (fenetre < DN_CPU_WINDOW_MIN_S) {
            fenetre = DN_CPU_WINDOW_MIN_S;
        } else if (fenetre > DN_CPU_WINDOW_MAX_S) {
            fenetre = DN_CPU_WINDOW_MAX_S;
        }
    }

    UBaseType_t capacite = uxTaskGetNumberOfTasks() + 8;
    TaskStatus_t *avant = calloc(capacite, sizeof(TaskStatus_t));
    TaskStatus_t *apres = calloc(capacite, sizeof(TaskStatus_t));
    if (!avant || !apres) {
        free(avant);
        free(apres);
        printf("pas assez de RAM pour deux relevés de %u tâches\n",
               (unsigned)capacite);
        return 1;
    }

    configRUN_TIME_COUNTER_TYPE c0 = 0, c1 = 0;
    UBaseType_t n_avant = uxTaskGetSystemState(avant, capacite, &c0);
    int64_t t0 = esp_timer_get_time();
    vTaskDelay(pdMS_TO_TICKS(fenetre * 1000));
    int64_t mural_us = esp_timer_get_time() - t0;
    UBaseType_t n_apres = uxTaskGetSystemState(apres, capacite, &c1);

    /* Somme des deltas = temps CPU réellement distribué sur la fenêtre, tous
     * cœurs confondus. La soustraction se fait dans le type NON SIGNÉ du
     * compteur : elle reste juste même si celui-ci a rebouclé pendant la
     * fenêtre. */
    unsigned long long somme = 0;
    for (UBaseType_t i = 0; i < n_apres; i++) {
        configRUN_TIME_COUNTER_TYPE base = 0;
        for (UBaseType_t j = 0; j < n_avant; j++) {
            if (avant[j].xHandle == apres[i].xHandle) {
                base = avant[j].ulRunTimeCounter;
                break;
            }
        }
        /* base reste 0 pour une tâche née PENDANT la fenêtre : son compteur
         * entier est alors exactement son temps sur la fenêtre. */
        somme += (unsigned long long)(configRUN_TIME_COUNTER_TYPE)(
            apres[i].ulRunTimeCounter - base);
    }

    printf("charge CPU sur %ld s (fenêtre mesurée : %lld ms, %u tâches)\n",
           fenetre, (long long)(mural_us / 1000), (unsigned)n_apres);
    if (somme == 0) {
        printf("⚠️ somme des temps CPU nulle — les compteurs de run-time ne\n");
        printf("   tournent pas. Instrument invalide, ne rien conclure.\n");
        free(avant);
        free(apres);
        return 1;
    }

    double reserve = 0.0;
    /* En-tête écrit à la main, aligné sur le « %-16s %7.1f » des lignes :
     * « tâche » porte un accent, et un %-Ns paddé par OCTETS le décalerait
     * d'une colonne (même défaut que celui corrigé dans la bannière). */
    printf("  tâche               part\n");
    for (UBaseType_t i = 0; i < n_apres; i++) {
        configRUN_TIME_COUNTER_TYPE base = 0;
        for (UBaseType_t j = 0; j < n_avant; j++) {
            if (avant[j].xHandle == apres[i].xHandle) {
                base = avant[j].ulRunTimeCounter;
                break;
            }
        }
        unsigned long long delta = (unsigned long long)(
            configRUN_TIME_COUNTER_TYPE)(apres[i].ulRunTimeCounter - base);
        double part = (double)delta * 100.0 / (double)somme;
        bool oisive = (strncmp(apres[i].pcTaskName, "IDLE", 4) == 0);
        if (oisive) {
            reserve += part;
        }
        /* On n'imprime pas les tâches à 0,0 % : elles noieraient la ligne qui
         * compte sous vingt lignes de bruit. */
        if (part >= 0.05 || oisive) {
            printf("  %-16s %7.1f %%%s\n", apres[i].pcTaskName, part,
                   oisive ? "   <= réserve" : "");
        }
    }
    printf("=> RÉSERVE (tâches IDLE) : %.1f %%  —  CHARGE : %.1f %%\n", reserve,
           100.0 - reserve);
    printf("   Rapporté au temps CPU total des %d cœurs sur la fenêtre.\n",
           configNUMBER_OF_CORES);
    printf("   compteur de run-time : %llu -> %llu\n", (unsigned long long)c0,
           (unsigned long long)c1);

    free(avant);
    free(apres);
    return 0;
}

#else /* !CONFIG_FREERTOS_GENERATE_RUN_TIME_STATS */

static int cmd_cpu(int argc, char **argv)
{
    (void)argc;
    (void)argv;
    /* Le fichier doit compiler MÊME SANS l'option : sinon un `sdkconfig` hérité
     * (qui gagne en silence sur sdkconfig.defaults, cf. l'avertissement en tête
     * de ce fichier-là) casserait le build au lieu de dégrader la commande. */
    printf("mesure de charge CPU indisponible : ce binaire est construit sans\n");
    printf("CONFIG_FREERTOS_GENERATE_RUN_TIME_STATS.\n");
    printf("Poser `CONFIG_FREERTOS_GENERATE_RUN_TIME_STATS=y` dans\n");
    printf("sdkconfig.defaults, puis `rm sdkconfig && idf.py build`.\n");
    return 1;
}

#endif /* CONFIG_FREERTOS_GENERATE_RUN_TIME_STATS */

static int cmd_help(int argc, char **argv);

#define DN_CMD(name, helptext, fn) \
    {.command = (name), .help = (helptext), .hint = NULL, .func = (fn)}

static const esp_console_cmd_t k_cmds[] = {
    DN_CMD("scene",
           "affiche une mire : bits|nbits|rgb|red|green|blue|white|black|frame|gray|asset",
           cmd_scene),
    DN_CMD("fps", "mesure le fps sur N secondes (>= 10) et le confronte à la théorie",
           cmd_fps),
    DN_CMD("mem", "PSRAM et RAM interne, avant/après framebuffers", cmd_mem),
    DN_CMD("cpu", "cpu [secondes] | cpu brut — charge processeur (AC6)", cmd_cpu),
    DN_CMD("bw", "bande passante mesurée des 3 chemins de copie", cmd_bw),
    DN_CMD("cfg", "cfg | cfg reset — config de boot (NVS), active, ou effacée",
           cmd_cfg),
    DN_CMD("set", "set fbs | bounce | lines | drawmem | core <-1|0|1>",
           cmd_set),
    DN_CMD("reboot", "redémarre pour appliquer un `set`", cmd_reboot),
    DN_CMD("tear", "tear on|vsync|sync|both|flip|off — déchirement BRUT (dn1-2)",
           cmd_tear),
    DN_CMD("flash", "flash on|off — stimulus d'écriture flash", cmd_flash),
    DN_CMD("ui", "ui [on|off] | ui label on|off | ui bg flash|psram — LVGL", cmd_ui),
    DN_CMD("flush",
           "flush | reset | sync off|vsync|fbdone | path bitmap|direct | full",
           cmd_flush),
    DN_CMD("anim", "anim on [ms] | off — stimulus adverse LVGL (témoin de tearing)",
           cmd_anim),
    DN_CMD("recal", "recal <0..4> — recalage DMA N vsyncs après la bascule (AC5)",
           cmd_recal),
    DN_CMD("bl", "bl [0..100|on|off|ramp <pct> [ms]] — rétroéclairage gradable",
           cmd_bl),
    DN_CMD("disp", "disp on|off — sortie d'affichage de la dalle (0x29/0x28)",
           cmd_disp),
    DN_CMD("dma", "relance la DMA du panneau (décalage permanent)", cmd_restart_dma),
    DN_CMD("aide", "cette aide", cmd_help),
};

static int cmd_help(int argc, char **argv)
{
    (void)argc;
    (void)argv;
    dn_console_banner();
    return 0;
}

/*
 * Bannière — DEUX COLONNES, plus de cadre. C'est un choix, pas un renoncement.
 *
 * L'ancien cadre faisait `printf("│ %-7s %-53s│\n", commande, aide)`. Or `%-53s`
 * remplit en OCTETS, pas en colonnes d'affichage : chaque accent d'une aide
 * (« é », « — », « ⚠ ») pèse 2 ou 3 octets pour 1 colonne, donc la barre de
 * droite reculait d'autant. Et l'aide de `scene` fait 76 caractères, soit 23 de
 * plus que le champ : elle crevait le cadre de part en part. C'était la
 * PREMIÈRE chose imprimée au boot, et la sortie de `aide`.
 *
 * Réparer le cadre demandait de compter les octets de continuation UTF-8
 * ((c & 0xC0) != 0x80) puis de tronquer ou replier les aides trop longues —
 * c'est-à-dire de mutiler le texte pour sauver un décor. Le format à deux
 * colonnes n'a aucun bord droit : la seule colonne paddée est le NOM de la
 * commande, qui est ASCII pur, donc `%-7s` y est exact par construction. Les
 * aides gardent leur longueur et se replient toutes seules dans le terminal.
 */
void dn_console_banner(void)
{
    printf("\n");
    printf("── DeskNode P2 — console de mesure ──\n");
    for (size_t i = 0; i < sizeof(k_cmds) / sizeof(k_cmds[0]); i++) {
        printf("  %-7s %s\n", k_cmds[i].command, k_cmds[i].help);
    }
    printf("\n");
    printf("état : num_fbs=%d bounce=%u px · rétroéclairage %d %% · LVGL %s\n",
           dn_display_num_fbs(), (unsigned)dn_display_bounce_px(),
           dn_display_backlight_pct_state(),
           dn_ui_active() ? "ACTIF" : "en pause");
    printf("       draw buffer %d x %d px en %s · synchro flush « %s »\n",
           DN_LCD_H_RES, dn_ui_draw_lines(),
           dn_ui_draw_in_psram() ? "PSRAM" : "RAM interne DMA",
           dn_flush_sync_name(dn_ui_get_sync()));
    if (!dn_ui_active()) {
        printf("       scène brute « %s » (chemin dn1-2)\n", scene_courante());
    }
    printf("\n");
}

esp_err_t dn_console_start(void)
{
    esp_console_repl_t *repl = NULL;
    esp_console_repl_config_t repl_cfg = ESP_CONSOLE_REPL_CONFIG_DEFAULT();
    repl_cfg.prompt = "desknode>";
    repl_cfg.max_cmdline_length = 128;
    /* 4096 par défaut ; les commandes dessinent une trame entière et
     * journalisent beaucoup. 8192 coûte 4 Ko de RAM interne et évite un
     * débordement de pile qui ressemblerait à un bug d'affichage. */
    repl_cfg.task_stack_size = 8192;

    /*
     * Le repli documenté doit VRAIMENT se construire.
     *
     * sdkconfig.defaults et le README annoncent tous deux la parade « remplacer
     * CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y par CONFIG_ESP_CONSOLE_UART_DEFAULT=y,
     * on perd la console interactive mais pas le log ». Sauf que ce fichier
     * appelait ESP_CONSOLE_DEV_USB_SERIAL_JTAG_CONFIG_DEFAULT() et
     * esp_console_new_repl_usb_serial_jtag() SANS GARDE, alors que les deux sont
     * déclarés dans esp_console.h derrière #if CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG.
     * Suivre la documentation donnait donc deux -Wimplicit-function-declaration
     * puis une erreur d'édition de liens : une porte de sortie qui n'ouvre pas.
     *
     * Le #error final est là pour qu'un troisième choix de console (USB CDC,
     * UART_CUSTOM, ou « aucune ») échoue À LA COMPILATION, avec le nom des deux
     * options soutenues — pas au boot, sur un silence.
     */
#if CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG
    esp_console_dev_usb_serial_jtag_config_t dev_cfg =
        ESP_CONSOLE_DEV_USB_SERIAL_JTAG_CONFIG_DEFAULT();
    esp_err_t err =
        esp_console_new_repl_usb_serial_jtag(&dev_cfg, &repl_cfg, &repl);
    const char *voie = "USB-Serial/JTAG";
#elif CONFIG_ESP_CONSOLE_UART_DEFAULT
    esp_console_dev_uart_config_t dev_cfg = ESP_CONSOLE_DEV_UART_CONFIG_DEFAULT();
    esp_err_t err = esp_console_new_repl_uart(&dev_cfg, &repl_cfg, &repl);
    const char *voie = "UART";
#else
#error "Console non soutenue : poser CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y (voie \
nominale) ou CONFIG_ESP_CONSOLE_UART_DEFAULT=y (repli documenté) dans \
sdkconfig.defaults, puis `rm sdkconfig && idf.py build`."
#endif
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "console %s refusée : %s", voie, esp_err_to_name(err));
        return err;
    }
    ESP_LOGI(TAG, "console sur %s", voie);
    for (size_t i = 0; i < sizeof(k_cmds) / sizeof(k_cmds[0]); i++) {
        ESP_ERROR_CHECK(esp_console_cmd_register(&k_cmds[i]));
    }
    ESP_ERROR_CHECK(esp_console_start_repl(repl));
    return ESP_OK;
}

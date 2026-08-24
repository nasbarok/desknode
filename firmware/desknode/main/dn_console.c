#include "dn_console.h"

#include <ctype.h>
#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

#include "dn_asset.h"
#include "dn_bootcfg.h"
#include "dn_capteurs.h"
#include "dn_env.h"
#include "dn_display.h"
#include "dn_link.h"
#include "dn_measure.h"
#include "dn_patterns.h"
#include "dn_pins.h"
#include "dn_recal.h"
#include "dn_rtc.h"
#include "dn_stimulus.h"
#include "dn_touch.h"
#include "fonts/dn_font.h"
#include "dn_hist.h"
#include "dn_ui.h"
#include "dn_wifi.h"
#include "driver/i2c_master.h"
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
 * Adresse I²C 7 bits, écrite comme on la lit dans une datasheet : `0x76`, `76`,
 * `0X76`. Même discipline que `parse_entier` (⛔ jamais `atoi` : il ne distingue
 * pas 0 d'une erreur), mais en base 16 — parce qu'une adresse I²C ne s'écrit
 * jamais en décimal et que forcer « 118 » pour dire 0x76 fabriquerait des fautes
 * de frappe indétectables.
 *
 * ⚠️ Les bornes ne sont pas cosmétiques : 0x00-0x07 et 0x78-0x7F sont RÉSERVÉES
 *    par la spécification I²C (appel général, adressage 10 bits…). Les sonder
 *    n'apprend rien et peut déclencher des comportements de mode spécial sur des
 *    composants tiers. La commande les refuse au lieu de les écrêter en silence
 *    — leçon `touch int` (revue dn1-4), qui écrêtait sans le dire puis imprimait
 *    un verdict FAUX.
 */
/* ⚠️ CR dn4-2 du 2026-08-24 — LA BANNIERE INTERDISAIT « 0x », LES PARSEURS
 * L'ACCEPTAIENT EN SILENCE. `strtol(..., 16)` avale le prefixe `0x`, l'espace
 * initial et le `+` ; la revue du 2026-08-20 avait rendu la banniere PLUS
 * categorique et n'avait touche AUCUN parseur. Critere n°4 d'AC4 : « bornes
 * annoncees ET TENUES ». Ce filtre les tient — un seul endroit, les quatre
 * sous-commandes le partagent. */
static bool parse_hex_strict(const char *texte, long *out)
{
    if (texte[0] == '\0') {
        return false;
    }
    for (const char *c = texte; *c; c++) {
        if (!isxdigit((unsigned char)*c)) {
            return false; /* refuse « 0x… », l'espace initial, « + » et « - » */
        }
    }
    char *fin = NULL;
    errno = 0;
    long v = strtol(texte, &fin, 16);
    if (fin == texte || *fin != '\0' || errno == ERANGE) {
        return false;
    }
    *out = v;
    return true;
}

static bool parse_adresse_i2c(const char *texte, uint8_t *out)
{
    long v = 0;
    if (!parse_hex_strict(texte, &v)) {
        return false;
    }
    if (v < 0x08 || v > 0x77) {
        return false;
    }
    *out = (uint8_t)v;
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
    /* Correctif de revue : `bw` fait cinq memset de 614 400 o sur le framebuffer
     * et un present() à 2 FB — la garde `ui_bloque` posée sur `scene` et `tear`
     * l'avait OUBLIÉ, alors que c'est la commande de routine héritée de dn1-2
     * qu'on tape le plus naturellement avec l'UI active. LVGL n'aurait jamais
     * réparé l'écran (rien d'invalidé de son point de vue). */
    if (ui_bloque("bw")) {
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
    /*
     * ── LE GARDE-FOU COMBINÉ, AVANT TOUTE ÉCRITURE (revue dn1-4) ────────────
     *
     * `bounce_px` et `draw_lines` mangent la MÊME RAM interne, et leurs bornes
     * respectives ne se sont jamais parlé. `set bounce 38400` — la valeur que
     * l'aide de cette commande présentait comme « le plafond, un diviseur
     * utile » — passait les DEUX contrôles et rendait la carte non démarrable
     * depuis que dn1-4 a fait passer draw_lines à 128. Panique au boot, CPU
     * halté, plus de console, donc plus de `cfg reset` : le brick que ces bornes
     * existaient pour empêcher. `set lines 160` + `set bounce 19200` faisait
     * pareil.
     *
     * On confronte donc le COUPLE prospectif (la valeur qu'on écrit + celle qui
     * est déjà en NVS pour l'autre clé) à la RAM interne réellement disponible.
     */
    if (cle_bounce || cle_lines) {
        dn_bootcfg_t cfg_nvs;
        if (dn_bootcfg_load(&cfg_nvs) == ESP_OK) {
            int b = cle_lines ? cfg_nvs.bounce_px : (int)valeur;
            int l = cle_lines ? (int)valeur : cfg_nvs.draw_lines;
            size_t demande = 0, dispo = 0;
            const char *refus = dn_bootcfg_budget_refus(b, l, &demande, &dispo);
            if (refus) {
                printf("refusé : %s\n", refus);
                printf("  couple demandé : bounce_px=%d + draw_lines=%d\n", b, l);
                /*
                 * 🔴 CORRIGÉ LE 2026-08-23 (dn4-10) : ce bloc disait « marge de
                 *    sécurité DÉDUITE » alors qu'elle ne l'est PAS. `*dispo` rend
                 *    `libre + rendu` BRUT (dn_bootcfg.c:552-558), et la garde
                 *    compare `veut + DN_BUDGET_MARGE_O > peut` (l.560). Le lecteur
                 *    voyait donc « 199 680 demandés pour 234 895 disponibles →
                 *    REFUSÉ » et en concluait, légitimement, que la garde était
                 *    cassée. Elle ne l'était pas : le message mentait. C'est
                 *    exactement le « chiffre faux mais PLAUSIBLE » que ce dépôt
                 *    traque — pire qu'un chiffre absurde, parce qu'on le croit.
                 *    ⇒ On imprime désormais LA COMPARAISON RÉELLEMENT FAITE.
                 */
                printf("  soit %u o de RAM interne, + %u o de marge de sécurité\n",
                       (unsigned)demande, (unsigned)dn_bootcfg_budget_marge_o());
                printf("  = %u o à trouver, pour %u o disponibles au prochain\n",
                       (unsigned)(demande + dn_bootcfg_budget_marge_o()), (unsigned)dispo);
                printf("  boot (libre maintenant + ce que les tampons actuels\n");
                printf("  rendront). ⚠️ Le chiffre « disponibles » est BRUT : la\n");
                printf("  marge n'en est PAS retranchée, elle s'ajoute à la\n");
                printf("  demande. C'est la ligne du dessus qui décide.\n");
                printf("⚠️ Ce refus REMPLACE un brick : au-delà, c'est\n");
                printf("   ESP_ERR_NO_MEM au boot, donc panique, donc CPU HALTÉ\n");
                printf("   par CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT — et plus\n");
                printf("   AUCUNE console pour annuler la valeur, à chaque boot,\n");
                printf("   jusqu'au reflash.\n");
                printf("   Baisser l'autre clé d'abord (`cfg` montre les deux).\n");
                return 1;
            }
        } else {
            printf("⚠️ config NVS illisible : le budget RAM combiné n'a PAS pu\n");
            printf("   être vérifié. `cfg` avant de continuer.\n");
        }
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
            printf("   480 (1 ligne), 4800 (10 lignes — le DÉFAUT), 9600 (20).\n");
            printf("⚠️ 19200 et 38400 divisent bien la trame, mais ne tiennent\n");
            printf("   PLUS en RAM interne avec draw_lines=128 : le budget\n");
            printf("   combiné les refusera. Ce ne sont plus des « diviseurs\n");
            printf("   utiles », c'est le plafond d'une époque où LVGL n'était\n");
            printf("   pas encore dans le binaire.\n");
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
         * ── AVERTISSEMENT « BOUNCE + FLASH », UNE COMBINAISON JAMAIS JOUÉE ───
         *
         * §5.3 et §11.4 du fichier d'autorité l'écrivent noir sur blanc : « la
         * branche bounce 4 800, ISR_IRAM_SAFE=n, stimulus flash n'a PAS été
         * jouée — elle reste une question ouverte », et « D4 reste en vigueur ».
         * Avant dn1-4 la combinaison était INATTEIGNABLE (bounce_px valait 0) ;
         * dn1-4 la rend atteignable PAR DÉFAUT, et `flash on` restait joignable
         * sans un mot, là où le dépôt met un garde-fou partout ailleurs.
         *
         * Le mécanisme est concret : avec un bounce buffer, c'est une ISR du
         * panneau qui recopie la PSRAM vers la RAM interne ; avec
         * CONFIG_LCD_RGB_ISR_IRAM_SAFE=n, cette interruption est MASQUÉE pendant
         * l'effacement d'un secteur (le raisonnement que dn_touch.c applique
         * déjà à l'ISR GPIO). Bounce non réalimenté ⇒ image corrompue, qu'on
         * attribuerait à la dalle.
         *
         * On n'INTERDIT pas : c'est justement la mesure qui manque, et
         * l'interdire empêcherait de la faire. On prévient, et on nomme le
         * symptôme à surveiller — sans quoi il serait pris pour une découverte.
         */
        if (dn_display_bounce_px() > 0) {
            printf("⚠️ COMBINAISON JAMAIS MESURÉE : bounce_px=%u + stimulus "
                   "flash.\n",
                   (unsigned)dn_display_bounce_px());
            printf("   L'ISR qui réalimente le bounce buffer est MASQUÉE pendant\n");
            printf("   l'effacement de secteur (ISR_IRAM_SAFE=n). Si l'image se\n");
            printf("   corrompt, c'est CE couplage — pas la dalle, et pas la\n");
            printf("   famine DMA de §11.4, qui est un autre régime.\n");
            printf("   §5.3 : question OUVERTE, D4 en vigueur. Consigner le\n");
            printf("   constat, quel qu'il soit. `set bounce 0` + `reboot` pour\n");
            printf("   retrouver le régime de dn1-3.\n");
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
    printf("        bl auto on|off      — asservissement au BH1750 (dn4-3, AC5)\n");
    printf("        bl auto bornes <lux_bas> <lux_haut>  — la loi, à chaud\n");
    printf("        bl auto pas <1..100>  — pas maximal par cycle de 5 s\n");
    printf("        bl auto plancher <n>  — le %% en piece SOMBRE (constat oeil)\n");
}

/* 🔴 DEUX ÉCRIVAINS SUR LEDC, ET RIEN NE LES ARBITRAIT.
 * `dn_display_backlight_pct()` n'a AUCUN verrou et `s_backlight_pct` est un `int`
 * nu ; ses deux appelants d'origine (boot, REPL) ne coexistaient jamais. L'auto
 * de dn4-3 en ajoute un TROISIÈME, périodique. Sans ce désarmement, un `bl 50`
 * tapé en séance serait ÉCRASÉ au cycle suivant SANS UN MOT, et le constat owner
 * mesurerait la boucle en croyant mesurer la commande. */
static void bl_desarmer_si_besoin(const char *geste)
{
    if (dn_env_bl_auto_desarmer(geste)) {
        printf("⚠️ l'asservissement automatique était ARMÉ : il vient d'être "
               "DÉSARMÉ par « %s ».\n", geste);
        printf("   Sinon la valeur que vous venez de poser aurait été écrasée "
               "au prochain cycle (5 s), sans un mot.\n");
        printf("   `bl auto on` pour le réarmer.\n");
    }
}

/* Imprime l'état de l'asservissement. Appelé par `bl` nu ET par `bl auto`. */
static void bl_auto_etat(void)
{
    int lux_bas = 0, lux_haut = 0, pas = 0, hyst = 0, dpct = 0, dlux = 0;
    dn_env_bl_etat(&lux_bas, &lux_haut, &pas, &hyst, &dpct, &dlux);
    printf("asservissement BH1750 : %s\n", dn_env_bl_auto() ? "ARMÉ" : "DÉSARMÉ");
    printf("  loi      : %d %% à <= %d lx · %d %% à >= %d lx · linéaire entre "
           "les deux\n",
           dn_env_bl_plancher(), lux_bas, DN_ENV_BL_PCT_MAX, lux_haut);
    printf("  garde    : bande morte %d pts · pas max %d pts par cycle de %d ms "
           "(course complète en %d cycles)\n",
           hyst, pas, DN_ENV_PERIODE_MS,
           (DN_ENV_BL_PCT_MAX - dn_env_bl_plancher() + pas - 1) / pas);
    /* 🔴 « jamais lu » et « noir complet » ne s'impriment PLUS à l'identique —
     * corrigé en revue de code le 2026-08-20. `0 lx` est une valeur MESURÉE
     * légitime sur ce capteur (la main posée a rendu `brut = 0` deux fois en
     * séance, et c'est publié comme tel) : rendre la sentinelle d'absence par
     * un `0` littéral affirmait l'obscurité totale là où rien n'avait été lu. */
    if (dpct < 0) {
        printf("  applique : AUCUNE application depuis le boot\n");
    } else if (dlux == DN_ENV_ABSENT) {
        printf("  applique : %d %% (sur un lux JAMAIS LU — ⛔ pas « 0 lx »)\n",
               dpct);
    } else {
        printf("  applique : %d %% (sur %d lx)\n", dpct, dlux);
    }
    printf("  ⚠️ `bl <n>`, `bl on|off` et `bl ramp` DÉSARMENT l'auto et le "
           "DISENT.\n");
    printf("  ⛔ `bl ramp` est BLOQUANTE : elle n'est JAMAIS appelée par "
           "l'asservissement.\n");
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
        bl_auto_etat();
        return 0;
    }

    /* ── bl auto [on|off|bornes …|pas …] ── */
    if (strcmp(argv[1], "auto") == 0) {
        if (argc < 3) {
            bl_auto_etat();
            return 0;
        }
        if (strcmp(argv[2], "bornes") == 0) {
            long bas = 0, haut = 0;
            /* ⛔ `argc != 5`, PAS `argc < 5` — un token tapé de travers passait
             * pour une commande réussie (revue de code 2026-08-20). */
            if (argc != 5 || !parse_entier(argv[3], &bas) ||
                !parse_entier(argv[4], &haut)) {
                printf("usage : bl auto bornes <lux_bas> <lux_haut>\n");
                return 1;
            }
            esp_err_t e = dn_env_bl_bornes_set((int)bas, (int)haut);
            if (e != ESP_OK) {
                /* ⛔ Ce dépôt REFUSE, il n'écrête pas — et il explique. */
                printf("refusé : bornes invalides. Il faut 0 <= bas < haut, et "
                       "haut <= 54611 lx — le plus grand lux PUBLIABLE : 0xFFFF "
                       "est rejeté comme saturation du convertisseur, donc le "
                       "plus grand brut est 0xFFFE, soit 65534 / 1,2 = 54611. "
                       "Au-delà, la loi ne pourrait JAMAIS saturer à 100 %%. "
                       "Rien n'a été touché.\n");
                return 1;
            }
            bl_auto_etat();
            return 0;
        }
        if (strcmp(argv[2], "plancher") == 0) {
            long pct = 0;
            if (argc != 4 || !parse_entier(argv[3], &pct)) {
                printf("usage : bl auto plancher <0..%d>\n",
                       DN_ENV_BL_PCT_MAX - DN_ENV_BL_HYST);
                return 1;
            }
            if (dn_env_bl_plancher_set((int)pct) != ESP_OK) {
                printf("refusé : le plancher doit être dans [0, %d] — au-delà, "
                       "la bande morte rendrait la loi INERTE sans le dire, ce "
                       "qui est pire qu'un refus. Rien n'a été touché.\n",
                       DN_ENV_BL_PCT_MAX - DN_ENV_BL_HYST);
                return 1;
            }
            bl_auto_etat();
            return 0;
        }
        if (strcmp(argv[2], "pas") == 0) {
            long pas = 0;
            if (argc != 4 || !parse_entier(argv[3], &pas)) {
                printf("usage : bl auto pas <%d..100>\n", DN_ENV_BL_HYST);
                return 1;
            }
            if (dn_env_bl_pas_set((int)pas) != ESP_OK) {
                /* 🔴 La borne basse est la BANDE MORTE, ⛔ pas 1 — corrigé en
                 * revue de code le 2026-08-20 : un pas plus petit que la bande
                 * morte fige la loi à mi-chemin, DANS LES DEUX SENS. */
                printf("refusé : le pas doit être dans [%d, 100] points. Un pas "
                       "PLUS PETIT que la bande morte (%d) figerait la loi à "
                       "mi-chemin sans le dire : elle entrerait (écart >= %d) "
                       "mais ne bougerait que de `pas`, laissant un écart < %d "
                       "⇒ gelée, dans les deux sens, pour tous les lux. "
                       "Rien n'a été touché.\n",
                       DN_ENV_BL_HYST, DN_ENV_BL_HYST, DN_ENV_BL_HYST,
                       DN_ENV_BL_HYST);
                return 1;
            }
            bl_auto_etat();
            return 0;
        }
        bool on_auto = false;
        if (argc != 3) {
            printf("usage : bl auto on|off — rien n'a été touché.\n");
            return 1;
        }
        if (!parse_on_off(argv[2], &on_auto)) {
            printf("« %s » n'est ni on, ni off — rien n'a été touché.\n", argv[2]);
            bl_usage();
            return 1;
        }
        if (on_auto && dn_env_etat(DN_ENV_LUM) != DN_ENV_VIVANT) {
            /* ⚠️ On ARME quand même : refuser sur un capteur momentanément muet
             * empêcherait d'armer pendant les 40 s de bus dégradé à froid. Mais
             * on le DIT, sinon l'owner croirait la loi inerte. */
            printf("⚠️ le BH1750 est « %s » : l'asservissement est ARMÉ mais le "
                   "duty ne bougera qu'à la première lecture valide.\n",
                   dn_env_etat_nom(dn_env_etat(DN_ENV_LUM)));
        }
        dn_env_bl_auto_set(on_auto);
        bl_auto_etat();
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
        bl_desarmer_si_besoin("bl ramp");
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
        bl_desarmer_si_besoin(on ? "bl on" : "bl off");
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
    bl_desarmer_si_besoin("bl <n>");
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
    printf("usage : flush                   — compteurs, glissement en tête\n");
    printf("        flush reset             — remet les compteurs à zéro\n");
    printf("                                  (glissement dn4-10 compris)\n");
    printf("        flush sync off|vsync|fbdone — synchronisation du flush\n");
    printf("        flush path bitmap|direct    — par où la zone sale entre\n");
    printf("        flush full              — invalide TOUT l'écran (preuve "
           "négative)\n");
}

static int cmd_flush(int argc, char **argv)
{
    if (argc >= 2 && strcmp(argv[1], "reset") == 0) {
        dn_ui_reset_stats();
        dn_measure_bounce_reset();
        printf("compteurs de flush remis à zéro.\n");
        printf("compteurs de GLISSEMENT (dn4-10) armés : la remise à zéro est\n");
        printf("   consommée par l'ISR au prochain vsync (<= 27 ms), pas ici.\n");
        return 0;
    }
    if (argc >= 2 && strcmp(argv[1], "full") == 0) {
        if (!dn_ui_active()) {
            printf("refusé : LVGL est en pause (`ui on` d'abord).\n");
            return 1;
        }
        /* Revue : `anim` polluerait la mesure — ses cycles tomberaient dans la
         * fenêtre d'attente et seraient publiés comme « coût du plein écran ». */
        if (dn_ui_anim_running()) {
            printf("refusé : le stimulus `anim` tourne — `anim off` d'abord.\n");
            printf("   Ses cycles se mélangeraient aux compteurs du redessin\n");
            printf("   plein écran, et le chiffre publié mesurerait les deux.\n");
            return 1;
        }
        dn_ui_reset_stats();
        if (!dn_ui_force_full_redraw()) {
            /* Revue : la première version publiait les compteurs même quand le
             * redessin n'avait PAS été demandé (verrou non pris) — la preuve
             * négative d'AC3 mesurait autre chose sans le dire. */
            printf("refusé : verrou LVGL non pris, AUCUN redessin demandé.\n");
            return 1;
        }
        /*
         * On attend la QUIESCENCE au lieu d'un délai fixe (revue) : 2 000 ms
         * figées étaient trop courtes à `lines 8` (~80 flushes x ~27 ms ≈ 2,1 s)
         * et publiaient un instantané au milieu du travail. Fini = au moins un
         * cycle complet ET plus aucun flush pendant 200 ms. Plafond 6 s.
         * ⚠️ Le label 1 Hz peut ajouter SES cycles pendant l'attente : ils
         * étaient déjà inclus avant, et le message le dit désormais.
         */
        dn_flush_stats_t q;
        uint32_t stable = 0;
        int64_t fin = esp_timer_get_time() + 6000000;
        dn_ui_get_stats(&q);
        uint32_t prev = q.flushes;
        while (esp_timer_get_time() < fin) {
            vTaskDelay(pdMS_TO_TICKS(200));
            dn_ui_get_stats(&q);
            if (q.cycles >= 1 && q.flushes == prev) {
                stable++;
                if (stable >= 1) {
                    break;
                }
            } else {
                stable = 0;
            }
            prev = q.flushes;
        }
        printf("redessin PLEIN ÉCRAN forcé — compteurs ci-dessous%s :\n",
               dn_ui_label_shown()
                   ? " (label 1 Hz visible : ses cycles éventuels sont inclus)"
                   : "");
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
        if (!dn_ui_active()) {
            /* Revue : accepté mais différé — le dire, sinon le réglage semble agir. */
            printf("⚠️ LVGL est en PAUSE : ce réglage ne prendra effet qu'au "
                   "`ui on`.\n");
        }
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
        if (dn_ui_direct_mode()) {
            /* Revue : en mode direct le chemin n'est JAMAIS lu — l'explication
             * qui suivait laissait croire qu'il s'appliquait. */
            printf("⚠️ SANS OBJET en rendu DIRECT (num_fbs=%d) : le flush ne fait\n",
                   dn_display_num_fbs());
            printf("   que basculer, aucun chemin de copie n'est emprunté.\n");
            return 0;
        }
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

    /* ─── dn4-10 : le glissement de trame, PUBLIE EN PREMIER ──────────────
     * ⚠️ Place AVANT tout `return` de cette fonction, et c'est deliberé : le
     *    rapport de flush sort tot quand `flushes == 0`, et l'instrument
     *    serait alors MUET exactement dans le cas ou le chemin de flush est au
     *    repos — c'est-a-dire le TEMOIN au repos d'AC1. Un instrument aveugle
     *    a son propre cas de reference est le defaut que ce depot a deja paye. */
    {
        dn_bounce_stats_t b;
        dn_measure_bounce_get(&b);
        uint32_t per = dn_measure_periode_us();
        uint32_t bp = dn_measure_back_porch_us();
        uint32_t vb = dn_measure_vblank_us();
        printf("─── glissement de trame (dn4-10) — fenêtre %lu ms ───\n",
               (unsigned long)b.fenetre_ms);
        if (b.raz_en_attente) {
            printf("⚠️ remise à zéro ARMÉE mais PAS ENCORE CONSOMMÉE (aucun vsync\n");
            printf("   depuis) : les chiffres ci-dessous sont ceux d'AVANT.\n");
        }
        printf("  trames (vsync)   : %lu · enroulements : %lu\n",
               (unsigned long)b.trames, (unsigned long)b.wraps);
        printf("  trames SANS enroulement : %lu · à deux ou plus : %lu\n",
               (unsigned long)b.manques, (unsigned long)b.doubles);
        if (b.intervalles == 0) {
            printf("  aucun intervalle mesuré — rien à conclure.\n");
        } else {
            printf("  intervalle vsync→vsync : n=%lu · min %lu · moy %lu · "
                   "MAX %lu us\n",
                   (unsigned long)b.intervalles, (unsigned long)b.inter_min_us,
                   (unsigned long)(b.inter_somme_us / b.intervalles),
                   (unsigned long)b.inter_max_us);
            printf("     (période théorique %lu us = %d x %d / %d Hz)\n",
                   (unsigned long)per, DN_LCD_H_RES + DN_HSYNC_PULSE +
                   DN_HSYNC_BACK_PORCH + DN_HSYNC_FRONT_PORCH,
                   DN_LCD_V_RES + DN_VSYNC_PULSE + DN_VSYNC_BACK_PORCH +
                   DN_VSYNC_FRONT_PORCH, DN_PCLK_HZ);
            if (b.inter_max_us > per) {
                printf("     retard PIRE observé : +%lu us sur la période\n",
                       (unsigned long)(b.inter_max_us - per));
            }
            printf("  ISR en retard de plus de : +100 us %lu · +%lu us (back "
                   "porch) %lu · +%lu us (VBlank) %lu · une trame %lu\n",
                   (unsigned long)b.retards_100, (unsigned long)bp,
                   (unsigned long)b.retards_bp, (unsigned long)vb,
                   (unsigned long)b.retards_vb,
                   (unsigned long)b.retards_trame);
        }
        if (b.ph_n == 0) {
            printf("  phase enroulement→vsync : aucun échantillon compté (%lu "
                   "écartés au dégrossissage)\n", (unsigned long)b.ph_ecarte);
        } else {
            printf("  🎯 phase enroulement→VSYNC_END : n=%lu (+%lu dégrossis) · "
                   "min %lu · moy %lu · MAX %lu us\n",
                   (unsigned long)b.ph_n, (unsigned long)b.ph_ecarte,
                   (unsigned long)b.ph_min_us,
                   (unsigned long)(b.ph_somme_us / b.ph_n),
                   (unsigned long)b.ph_max_us);
            printf("     une phase COURTE = l'enroulement EN RETARD = le "
                   "remplissage du bounce qui décroche.\n");
            printf("     🔴 DÉFICIT PIRE sous le max : %lu us, pour un "
                   "demi-bounce qui s'écoule en %lu us\n",
                   (unsigned long)b.ph_deficit_max_us, (unsigned long)b.t_demi_us);
            if (b.t_demi_us && b.ph_deficit_max_us > b.t_demi_us) {
                printf("        ⇒ DÉPASSÉ de %lu us : la DMA a lu un tampon PAS "
                       "ENCORE REMPLI. C'est le décalage visible.\n",
                       (unsigned long)(b.ph_deficit_max_us - b.t_demi_us));
            } else if (b.t_demi_us) {
                printf("        ⇒ sous le seuil, il restait %lu us de marge "
                       "(%lu %% du demi-bounce)\n",
                       (unsigned long)(b.t_demi_us - b.ph_deficit_max_us),
                       (unsigned long)((b.t_demi_us - b.ph_deficit_max_us) * 100u /
                                       b.t_demi_us));
            }
            printf("     trames dont le déficit dépasse : 10 %% %lu · 25 %% %lu · "
                   "50 %% %lu · 🔴 100 %% (CORRUPTION) %lu\n",
                   (unsigned long)b.ph_10pc, (unsigned long)b.ph_25pc,
                   (unsigned long)b.ph_50pc, (unsigned long)b.ph_100pc);
            printf("     ⚠️ PLANCHER : la microseconde, soit 16 px. ⛔ « 0 » ici ne "
                   "veut PAS dire « 0 pixel ».\n");
            printf("     ⚠️ L'horodatage de référence vient LUI AUSSI d'une ISR : "
                   "un retard COMMUN aux deux s'annule et reste invisible.\n");
        }
        printf("  ce que ça veut dire : le driver RGB remet la DMA à zéro à\n");
        printf("     CHAQUE VBlank (RESTART_IN_VSYNC=y) et écrit lui-même que\n");
        printf("     « si cette interruption est ASSEZ EN RETARD, l'image se\n");
        printf("     DÉCALE » (esp_lcd_panel_rgb.c:1142-1148). Le budget réel\n");
        printf("     est le back porch, %lu us — pas le VBlank entier (%lu us),\n",
               (unsigned long)bp, (unsigned long)vb);
        printf("     car VSYNC_END tombe à la FIN de l'impulsion.\n");
        printf("  ⛔ un compteur à zéro ne prouve RIEN tant que le témoin ne\n");
        printf("     l'a pas fait bouger, et la correspondance avec l'œil est\n");
        printf("     un RÉSULTAT à établir, pas une hypothèse. ⛔ `fps` reste\n");
        printf("     aveugle à ce défaut : il MOYENNE, et la gigue s'y efface.\n");
        printf("────────────────────────────────────────────────────────────\n");
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
    /* Revue : les flushes NO-OP du mode direct (aire comptée, zéro µs) sortent
     * du dénominateur des moyennes temporelles — les inclure les diluait. */
    uint32_t reels = st.flushes - st.noops;
    if (st.noops) {
        printf("dont no-op (direct): %lu — exclus des moyennes de temps\n",
               (unsigned long)st.noops);
    }
    if (reels == 0) {
        printf("copie / attente    : aucun flush effectif (que des no-op).\n");
        return 0;
    }
    printf("copie              : %lu us cumulés, %lu us/flush en moyenne, "
           "%lu us au pire\n",
           (unsigned long)st.copie_us,
           (unsigned long)(st.copie_us / reels),
           (unsigned long)st.max_copie_us);
    printf("attente de synchro : %lu us cumulés, %lu us/flush en moyenne\n",
           (unsigned long)st.attente_us,
           (unsigned long)(st.attente_us / reels));
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
    if (err == ESP_ERR_INVALID_ARG) {
        printf("refusé : %s — période attendue entre 200 et 10000 ms.\n",
               esp_err_to_name(err));
        return 1;
    }
    if (err != ESP_OK) {
        /* Revue : un timeout de verrou était annoncé comme une erreur de bornes
         * — l'opérateur corrigeait un argument qui n'avait rien. */
        printf("refusé : %s — le verrou LVGL n'a pas été pris, la période "
               "n'y est pour rien. Réessayer.\n",
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
    /* Correctif de revue : le verrou était UNIDIRECTIONNEL. `tear` est refusé
     * quand l'UI est active, mais `ui on` était accepté pendant que la tâche de
     * tearing tournait — deux écrivains à pleine cadence sur le même
     * framebuffer, avec le RMW non protégé de `s_draw_index` depuis deux cœurs. */
    if (on && dn_stim_tear_running()) {
        printf("refusé : le stimulus de tearing tourne — `tear off` d'abord.\n");
        printf("   `ui on` relancerait LVGL PENDANT que la tâche de tearing\n");
        printf("   redessine des trames entières : deux écrivains, deux cœurs,\n");
        printf("   écran inattribuable.\n");
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

/* ── Le tactile (dn1-4) ───────────────────────────────────────────────────── */

static void touch_usage(void)
{
    printf("usage : touch                      etat, config lue, compteurs\n");
    printf("        touch reset                remet les compteurs a zero\n");
    printf("        touch mode event|poll      mode de lecture de l'indev\n");
    printf("        touch axes <swap> <mx> <my>  0|1 chacun (orientation)\n");
    printf("        touch trace [ms]           imprime chaque appui + sa zone\n");
    printf("        touch int [ms]             temoin PHYSIQUE de TP_INT\n");
    printf("        touch addr                 PREUVE CAUSALE : INT haut/bas\n");
    printf("                                   -> adresse latchee 0x14/0x5D\n");
    printf("        touch delais <bas> <haut>  delais de la sequence de reset\n");
    printf("                                   (1..2000 ms) ; `touch addr` pour\n");
    printf("                                   les APPLIQUER en rejouant\n");
}

static void touch_etat(void)
{
    dn_touch_stats_t st;
    dn_touch_cfg_t cfg;
    dn_touch_get_stats(&st);
    dn_touch_get_cfg(&cfg);
    bool swap = false, mx = false, my = false;
    dn_touch_get_axes(&swap, &mx, &my);
    int bas = 0, haut = 0;
    dn_touch_get_delais(&bas, &haut);

    printf("GT911 : %s\n", dn_touch_ready() ? "PRET" : "ABSENT");
    printf("  adresse REELLE 0x%02X (visee 0x%02X)%s\n", dn_touch_addr(),
           dn_touch_addr_visee(),
           dn_touch_addr() && dn_touch_addr() != dn_touch_addr_visee()
               ? "  <- REPLI : INT n'etait pas bas au relachement"
               : "");
    if (dn_touch_addr_avant()) {
        printf("  probe AVANT reset : REPOND DEJA a 0x%02X\n",
               dn_touch_addr_avant());
        printf("     => TP_RST n'est PAS maintenu bas quand l'expander le laisse\n");
        printf("        en entree : le GT911 sort de reset seul a la mise sous\n");
        printf("        tension. La story attendait l'inverse — MESURE le\n");
        printf("        2026-08-16. La sequence reste utile : elle rend l'adresse\n");
        printf("        DETERMINISTE. Le temoin de causalite est `touch addr`.\n");
    } else {
        printf("  probe AVANT reset : %s (muet — controleur encore en reset)\n",
               esp_err_to_name(dn_touch_probe_avant()));
    }
    printf("  probe APRES reset : %s\n", esp_err_to_name(dn_touch_probe_apres()));
    printf("  sequence : INT bas, TP_RST %d ms bas / %d ms de repos (expander bit1)\n",
           bas, haut);
    if (cfg.lue) {
        printf("  identite : « %s » fw 0x%04X · config v%u · %u point(s) max\n",
               cfg.product_id, cfg.fw_version, cfg.cfg_version, cfg.touch_max);
        printf("  resolution CONFIGUREE dans le GT911 : %u x %u  (dalle %d x %d)\n",
               cfg.x_res, cfg.y_res, DN_LCD_H_RES, DN_LCD_V_RES);
        /* Table décodée par dn_touch, SOURCE UNIQUE : elle était réécrite ici à
         * la main. Deux décodages du seul registre qui décide du front
         * d'armement de l'ISR, c'est un bandeau de boot et un `touch` qui
         * peuvent se contredire sur la cause d'un mode `event` muet. */
        printf("  INT declenche sur : %s (registre 0x804D bits 1-0 = %u)\n",
               dn_touch_trig_name(cfg.trig_mode), cfg.trig_mode);
    } else {
        printf("  identite/config : NON LUES\n");
    }
    printf("  mode de lecture : %s · axes swap=%d mirror_x=%d mirror_y=%d\n",
           dn_touch_mode_name(dn_touch_get_mode()), swap, mx, my);
    printf("  TP_INT = GPIO%d, niveau instantane %d\n", DN_PIN_TP_INT,
           dn_touch_int_level());
    printf("compteurs :\n");
    printf("  IRQ %" PRIu32 " · lectures %" PRIu32 " · appuis %" PRIu32
           " · relaches %" PRIu32 " · erreurs I2C %" PRIu32 "\n",
           st.irq, st.lectures, st.appuis, st.relaches, dn_touch_err_i2c());
    printf("  dernier point : (%" PRIu32 ", %" PRIu32 ")  brut (%" PRIu32
           ", %" PRIu32 ")  etat %s\n",
           st.x, st.y, st.brut_x, st.brut_y, st.appuye ? "APPUYE" : "relache");
    if (st.irq == 0 && st.appuis > 0) {
        printf("⚠️ des appuis SANS aucune IRQ : en mode `event` le tactile serait\n");
        printf("   MUET. C'est le polling qui les a vus. Verifier TP_INT avec\n");
        printf("   `touch int 3000` avant de retenir `event`.\n");
    }

    dn_touch_latence_t lat;
    dn_touch_get_latence(&lat);
    printf("latence tap -> ecran flushe (AC5) :\n");
    if (lat.n == 0) {
        printf("  aucune transition mesuree — toucher une case, ou `nav open 0`\n");
    } else {
        printf("  n=%" PRIu32 " · min %" PRIu32 " us · moy %" PRIu32
               " us · max %" PRIu32 " us · dernier %" PRIu32 " us\n",
               lat.n, lat.min_us, lat.total_us / lat.n, lat.max_us,
               lat.dernier_us);
        printf("  soit min %.1f ms · moy %.1f ms · max %.1f ms\n",
               lat.min_us / 1000.0, (lat.total_us / lat.n) / 1000.0,
               lat.max_us / 1000.0);
        printf("  ⚠️ BORNES DE LA MESURE : du clic LVGL a la fin du dernier flush\n");
        printf("     du cycle. N'INCLUT PAS le delai doigt -> lecture (jusqu'a\n");
        printf("     33 ms en polling) ni le flush -> photon (jusqu'a 26,7 ms).\n");
    }
    /* Les échantillons ABANDONNÉS (armement postérieur au flush) étaient jetés
     * sans laisser de trace : `n` divergeait du nombre réel de transitions et
     * la moyenne se calculait sur un échantillon biaisé vers le bas. */
    if (lat.rejets) {
        printf("🔴 %" PRIu32 " echantillon(s) ABANDONNE(s) (dt < 0) : la campagne\n",
               lat.rejets);
        printf("   ci-dessus est INVALIDE — `touch reset` puis rejouer.\n");
    }
    uint32_t refus = dn_ui_async_refus();
    if (refus) {
        printf("🔴 %" PRIu32 " tap(s) REFUSE(s) par LVGL (file d'async pleine ou\n",
               refus);
        printf("   tas sature) : ils n'ont ouvert aucun ecran et ne sont PAS\n");
        printf("   comptes dans les taps. Regarder `mem` et le tas LVGL.\n");
    }
}

static int cmd_touch(int argc, char **argv)
{
    if (argc < 2) {
        touch_etat();
        touch_usage();
        return 0;
    }

    if (strcmp(argv[1], "reset") == 0) {
        /*
         * ⚠️ `reset` ne prend AUCUN argument, et il faut le dire (revue dn1-4).
         *    Trois commentaires du firmware annonçaient `touch reset <bas>
         *    <haut>` pour régler les délais de la séquence ; la commande les
         *    ignorait SILENCIEUSEMENT et effaçait les compteurs. L'opérateur
         *    croyait avoir changé la séquence de reset, et venait d'effacer les
         *    chiffres qu'il s'apprêtait à lire. Les délais ont désormais leur
         *    propre sous-commande, `touch delais`.
         */
        if (argc > 2) {
            printf("`touch reset` ne prend pas d'argument — il remet les\n");
            printf("compteurs a zero. Pour les delais de la sequence de reset :\n");
            printf("   touch delais <bas_ms> <haut_ms>\n");
            printf("(rien n'a ete modifie)\n");
            return 1;
        }
        dn_touch_reset_stats();
        dn_touch_reset_latence();
        /* Les compteurs de la couche UI n'avaient aucun reset : après une
         * bascule de modèle, `nav` publiait ceux du modèle précédent sous la
         * bannière du nouveau — et c'est cette console qui imprime le protocole
         * « `touch reset` puis `nav ab 20` ». */
        dn_ui_reset_compteurs();
        printf("compteurs tactiles, latences et compteurs UI remis a zero.\n");
        return 0;
    }

    if (strcmp(argv[1], "delais") == 0) {
        long bas = 0, haut = 0;
        if (argc < 4 || !parse_entier(argv[2], &bas) ||
            !parse_entier(argv[3], &haut)) {
            printf("usage : touch delais <bas_ms> <haut_ms>   (1..2000 chacun)\n");
            printf("Les valeurs par defaut (150/50) viennent de la demo\n");
            printf("Waveshare et sont VUES MARCHER sur cette dalle.\n");
            return 1;
        }
        esp_err_t err = dn_touch_set_delais((int)bas, (int)haut);
        if (err != ESP_OK) {
            printf("refuse : %s — chaque delai doit tenir dans 1..2000 ms.\n",
                   esp_err_to_name(err));
            return 1;
        }
        printf("delais poses : %ld ms bas / %ld ms de repos.\n", bas, haut);
        printf("⚠️ PAS ENCORE APPLIQUES : ils ne servent qu'a la PROCHAINE\n");
        printf("   sequence. `touch addr` la rejoue. Ils ne survivent pas au\n");
        printf("   reboot (pas de NVS) : c'est un reglage de campagne.\n");
        return 0;
    }

    if (strcmp(argv[1], "mode") == 0) {
        dn_touch_mode_t m;
        if (argc < 3 || !dn_touch_mode_from_name(argv[2], &m)) {
            printf("usage : touch mode event|poll\n");
            return 1;
        }
        esp_err_t err = dn_touch_set_mode(m);
        if (err != ESP_OK) {
            printf("refuse : %s%s\n", esp_err_to_name(err),
                   err == ESP_ERR_INVALID_STATE
                       ? " — pas d'indev (le tactile n'est pas branche a LVGL)"
                       : "");
            return 1;
        }
        printf("mode de lecture : %s\n", dn_touch_mode_name(m));
        if (m == DN_TOUCH_MODE_EVENT) {
            printf("⚠️ PROTOCOLE — le mode `event` est MUET EN SILENCE si l'INT ne\n");
            printf("   bat pas : `touch reset`, toucher l'ecran, puis `touch` et\n");
            printf("   REGARDER le compteur IRQ. Un compteur a zero apres un vrai\n");
            printf("   toucher condamne ce mode, quoi qu'affiche l'ecran.\n");
        }
        return 0;
    }

    if (strcmp(argv[1], "axes") == 0) {
        long s = 0, mx = 0, my = 0;
        if (argc < 5 || !parse_entier(argv[2], &s) || !parse_entier(argv[3], &mx) ||
            !parse_entier(argv[4], &my)) {
            printf("usage : touch axes <swap> <mirror_x> <mirror_y>  (0 ou 1)\n");
            return 1;
        }
        if (s < 0 || s > 1 || mx < 0 || mx > 1 || my < 0 || my > 1) {
            printf("refuse : chaque drapeau vaut 0 ou 1.\n");
            return 1;
        }
        esp_err_t err = dn_touch_set_axes(s != 0, mx != 0, my != 0);
        if (err != ESP_OK) {
            printf("refuse : %s\n", esp_err_to_name(err));
            return 1;
        }
        printf("axes : swap=%ld mirror_x=%ld mirror_y=%ld\n", s, mx, my);
        printf("⚠️ les miroirs se replient sur x_max=%d / y_max=%d : un miroir sans\n",
               DN_LCD_H_RES, DN_LCD_V_RES);
        printf("   son max donne des coordonnees repliees sur le mauvais bord.\n");
        printf("⚠️ swap=1 est REFUSE sur cette carte : x_max/y_max sont figes a\n");
        printf("   %d/%d et un echange d'axes projetterait un intervalle de %d\n",
               DN_LCD_H_RES, DN_LCD_V_RES, DN_LCD_V_RES);
        printf("   sur un axe large de %d — les %d dernieres lignes (bandeau\n",
               DN_LCD_H_RES, DN_LCD_V_RES - DN_LCD_H_RES);
        printf("   MENU compris) deviendraient injoignables. AC2 a mesure que\n");
        printf("   cette dalle ne demande AUCUNE transformation.\n");
        return 0;
    }

    if (strcmp(argv[1], "trace") == 0) {
        long ms = 20000;
        if (argc >= 3 && !parse_entier(argv[2], &ms)) {
            printf("« %s » n'est pas un nombre.\n", argv[2]);
            return 1;
        }
        if (ms < 1000 || ms > 120000) {
            printf("refuse : entre 1000 et 120000 ms.\n");
            return 1;
        }
        /*
         * La trace est produite ICI, dans la tâche du REPL, en OBSERVANT les
         * compteurs — jamais depuis un callback LVGL. Un printf dans le chemin
         * de rendu bloquerait la tâche LVGL sur le lien USB, et l'instrument de
         * la preuve d'AC3 fausserait la latence qu'AC5 mesure au même instant.
         */
        printf("trace pendant %ld ms — TOUCHER MAINTENANT.\n", ms);
        printf("APPUI = contact detecte · TAP = zone activee (au RELACHEMENT)\n");
        /*
         * ⚠️ DEUX ÉVÉNEMENTS DISTINCTS, ET LES CONFONDRE FAIT MENTIR LA TRACE.
         *
         * Le contact est vu par l'indev à l'APPUI ; LVGL, lui, ne valide un
         * CLICKED qu'au RELÂCHEMENT. Une première version imprimait une seule
         * ligne par appui, en y accolant `dn_ui_dernier_tap()` — c'est-à-dire la
         * DERNIÈRE zone touchée, pas celle de cet appui-là. Résultat mesuré le
         * 2026-08-16 : un tap au CENTRE de l'écran (237, 322), qui tombe dans
         * l'espace entre deux cases et n'active donc RIEN, s'est affiché
         * « MENU (no-op) » — la zone du tap précédent. L'instrument censé prouver
         * « toute la case est la zone tactile » attribuait des taps à des zones
         * qu'ils n'avaient pas touchées.
         *
         * On imprime donc les deux événements SÉPARÉMENT, chacun quand il
         * survient. Un appui sans TAP qui suit est un appui HORS ZONE, et ça se
         * lit directement.
         */
        dn_touch_stats_t st;
        dn_touch_get_stats(&st);
        uint32_t vus = st.appuis;
        uint32_t taps_vus = dn_ui_taps();
        int64_t fin = esp_timer_get_time() + (int64_t)ms * 1000;
        /*
         * ⚠️ ON COMPTE LE DELTA, PAS « UN PAR TOUR » (revue dn1-4). Les deux
         *    compteurs s'incrémentaient de 1 quel que soit l'écart : deux appuis
         *    tombés dans la même fenêtre de 10 ms n'en comptaient qu'un, et le
         *    bilan « appui(s) HORS ZONE » — qui se calcule par SOUSTRACTION —
         *    fabriquait un hors-zone à chaque fois. C'est la mauvaise
         *    attribution que le commentaire ci-dessus dit avoir corrigée,
         *    remontée d'un cran : corrigée entre événements, elle survivait dans
         *    le total.
         */
        uint32_t n_appuis = 0, n_taps = 0, n_groupes = 0;
        while (esp_timer_get_time() < fin) {
            dn_touch_get_stats(&st);
            uint32_t taps = dn_ui_taps();
            if (st.appuis != vus) {
                uint32_t d = st.appuis - vus;
                vus = st.appuis;
                printf("  APPUI %3" PRIu32 " · (%3" PRIu32 ", %3" PRIu32
                       ") · brut (%3" PRIu32 ", %3" PRIu32 ")%s\n",
                       st.appuis, st.x, st.y, st.brut_x, st.brut_y,
                       d > 1 ? "  <- plusieurs appuis dans la meme fenetre de "
                               "10 ms, seul le DERNIER point est affiche"
                             : "");
                n_appuis += d;
                n_groupes++;
            }
            if (taps != taps_vus) {
                uint32_t d = taps - taps_vus;
                taps_vus = taps;
                printf("        -> TAP sur %s%s\n",
                       dn_ui_zone_nom(dn_ui_dernier_tap()),
                       d > 1 ? "  <- plusieurs taps groupes, seule la DERNIERE "
                               "zone est affichee"
                             : "");
                n_taps += d;
            }
            vTaskDelay(pdMS_TO_TICKS(10));
        }
        /*
         * ⚠️ SURSIS DE 400 ms. Le TAP est émis par LVGL au RELÂCHEMENT, et une
         *    transition d'écran occupe la tâche LVGL ~300 ms : un appui posé
         *    dans les dernières centaines de millisecondes voyait son tap tomber
         *    HORS de la fenêtre, et le bilan le déclarait « HORS ZONE » alors
         *    qu'il avait parfaitement ouvert son détail.
         */
        int64_t sursis = esp_timer_get_time() + 400000;
        while (esp_timer_get_time() < sursis) {
            uint32_t taps = dn_ui_taps();
            if (taps != taps_vus) {
                uint32_t d = taps - taps_vus;
                taps_vus = taps;
                printf("        -> TAP sur %s  (pendant le sursis de fin)\n",
                       dn_ui_zone_nom(dn_ui_dernier_tap()));
                n_taps += d;
            }
            vTaskDelay(pdMS_TO_TICKS(10));
        }
        printf("fin de trace : %" PRIu32 " appui(s), %" PRIu32 " tap(s) sur zone.\n",
               n_appuis, n_taps);
        if (n_appuis != n_groupes) {
            printf("⚠️ %" PRIu32 " appui(s) ont ete GROUPES par l'echantillonnage\n",
                   n_appuis - n_groupes);
            printf("   a 10 ms : leurs coordonnees individuelles sont perdues.\n");
        }
        if (n_appuis > n_taps) {
            printf("  (%" PRIu32 " appui(s) HORS ZONE — barre heure/date, espace\n",
                   n_appuis - n_taps);
            printf("   entre cases, ou marge : c'est ce qu'AC3 attend de ces\n");
            printf("   endroits.)\n");
        }
        if (n_taps > n_appuis) {
            printf("⚠️ PLUS de taps que d'appuis : des taps de la trace\n");
            printf("   PRECEDENTE sont arrives pendant celle-ci. Rejouer.\n");
        }
        if (n_appuis == 0) {
            printf("⚠️ AUCUN appui vu. Si l'ecran a bien ete touche, c'est le\n");
            printf("   TACTILE qui ne remonte rien : `touch` (compteur IRQ,\n");
            printf("   erreurs I2C) puis `touch int 3000` pour trancher.\n");
        }
        return 0;
    }

    if (strcmp(argv[1], "int") == 0) {
        long ms = 3000;
        if (argc >= 3 && !parse_entier(argv[2], &ms)) {
            printf("« %s » n'est pas un nombre.\n", argv[2]);
            return 1;
        }
        /*
         * ⚠️ BORNÉ ICI, AVEC UN REFUS EXPLIQUÉ (revue dn1-4) — comme `touch
         *    trace` dix lignes plus haut, qui le faisait déjà. La commande
         *    acceptait n'importe quel entier, ANNONÇAIT la valeur brute, puis
         *    `dn_touch_int_scan()` écrêtait en silence à [1, 5000].
         *    `touch int 30000` imprimait donc « echantillonnage pendant 30000 ms
         *    — TOUCHER L'ECRAN MAINTENANT », rendait la main au bout de 5 s, et
         *    si l'operateur touchait à t = 8 s le verdict imprimé était « la
         *    broche N'A PAS BOUGE […] GPIO16 n'est pas TP_INT ». Une conclusion
         *    FAUSSE sur le témoin physique qui sert à établir l'identité de la
         *    broche, fabriquée par l'écart entre ce qu'on annonce et ce qu'on
         *    fait. `touch int -5` annonçait « -5 ms » et scannait 1 ms.
         */
        if (ms < 1 || ms > 5000) {
            printf("refuse : entre 1 et 5000 ms.\n");
            printf("Au-dela, le scan monopoliserait le coeur : il echantillonne\n");
            printf("toutes les ~100 us et ne respire qu'un tick toutes les 20 ms.\n");
            printf("Pour observer plus longtemps, c'est `touch trace` qu'il faut\n");
            printf("(jusqu'a 120000 ms), ou plusieurs `touch int` de suite.\n");
            return 1;
        }
        printf("echantillonnage de GPIO%d pendant %ld ms — TOUCHER L'ECRAN "
               "MAINTENANT.\n",
               DN_PIN_TP_INT, ms);
        int fin = 0;
        uint32_t t = dn_touch_int_scan((int)ms, &fin);
        printf("transitions vues : %" PRIu32 " · niveau final %d\n", t, fin);
        if (t == 0) {
            printf("=> la broche N'A PAS BOUGE. Soit rien n'a ete touche, soit\n");
            printf("   GPIO%d n'est pas TP_INT. `touch addr` tranche : si changer\n",
                   DN_PIN_TP_INT);
            printf("   son niveau change l'adresse latchee, c'est bien elle.\n");
        } else {
            printf("=> la broche BAT. Si le compteur IRQ de `touch` reste a zero,\n");
            printf("   le probleme est l'ARMEMENT de l'ISR (front attendu), pas le\n");
            printf("   cablage.\n");
        }
        printf("⚠️ echantillonne a ~100 us avec une respiration d'1 tick toutes les\n");
        printf("   20 ms : une impulsion plus courte que le trou peut etre manquee.\n");
        return 0;
    }

    if (strcmp(argv[1], "addr") == 0) {
        printf("PREUVE CAUSALE de TP_INT — deux resets, deux niveaux d'INT.\n");
        printf("Le GT911 echantillonne INT au relachement de RST : bas => 0x5D,\n");
        printf("haut => 0x14. Si GPIO%d commande ce choix, c'est LUI.\n",
               DN_PIN_TP_INT);
        uint8_t a_haut = 0, a_bas = 0;
        esp_err_t e1 = dn_touch_essai_adresse(true, &a_haut);
        printf("  INT tenu HAUT au relachement -> repond a 0x%02X  (%s)\n", a_haut,
               esp_err_to_name(e1));
        esp_err_t e2 = dn_touch_essai_adresse(false, &a_bas);
        printf("  INT tenu BAS  au relachement -> repond a 0x%02X  (%s)\n", a_bas,
               esp_err_to_name(e2));
        if (a_haut == DN_GT911_ADDR_BACKUP && a_bas == DN_GT911_ADDR) {
            printf("=> ETABLI : GPIO%d EST TP_INT. Aucune autre broche du SoC ne\n",
                   DN_PIN_TP_INT);
            printf("   peut changer l'adresse que le GT911 echantillonne.\n");
        } else if (a_haut == a_bas && a_bas != 0) {
            printf("=> INFIRME : l'adresse ne suit PAS GPIO%d. Soit la broche n'est\n",
                   DN_PIN_TP_INT);
            printf("   pas TP_INT, soit un tirage externe impose le niveau.\n");
        } else {
            printf("=> INCONCLUANT : le contrôleur n'a pas repondu a l'un des deux\n");
            printf("   essais. Relancer, ou verifier `touch` d'abord.\n");
        }
        printf("l'etat NOMINAL (INT bas => 0x%02X) vient d'etre restaure : le\n",
               DN_GT911_ADDR);
        printf("driver parle a 0x%02X et doit y retrouver le contrôleur.\n",
               dn_touch_addr());
        if (a_bas != dn_touch_addr()) {
            printf("⚠️ ce n'est PAS le cas ici : le tactile restera MUET jusqu'au\n");
            printf("   prochain `reboot`.\n");
        }
        return 0;
    }

    touch_usage();
    return 1;
}

/* ── La navigation (dn1-4) ────────────────────────────────────────────────── */

/*
 * Verrou des transitions contre la PAUSE de LVGL.
 *
 * Ce n'est pas de la politesse : la transition arme le chronomètre de latence
 * (AC5) et compte sur le cycle de rafraîchissement suivant pour l'arrêter. LVGL
 * en pause, ce cycle n'arrive JAMAIS — le chronomètre reste en vol, et c'est le
 * premier flush d'après `ui on` qui l'arrêterait. La latence publiée serait alors
 * la durée de la pause, c'est-à-dire un chiffre gouverné par l'opérateur et pas
 * par la carte. On refuse, et on explique.
 *
 * ⚠️ CETTE GARDE NE COUVRE PAS LE DOIGT, ET LA RAISON QU'ON EN DONNAIT ÉTAIT
 *    FAUSSE (revue dn1-4). On écrivait ici « le chemin du DOIGT n'a pas besoin de
 *    cette garde : en pause, l'indev n'est pas lu, donc aucun clic n'est
 *    produit ». C'est vrai en mode `poll` (l'indev est en LV_INDEV_MODE_TIMER, et
 *    `lvgl_port_stop()` coupe le timer) — et FAUX en mode `event` :
 *    `lvgl_port_stop()` ne fait que `lv_timer_enable(false)`, la tâche LVGL
 *    continue de tourner et lit l'indev sur la branche ÉVÉNEMENTIELLE, avant et
 *    indépendamment de `lv_timer_handler()`. Un tap pendant `ui off` en mode
 *    `event` produit donc bien un CLICKED, et des transactions I²C au beau
 *    milieu de la mesure que la pause existe pour isoler.
 *    C'est l'un des trois symptômes qui font retenir `poll` comme mode de
 *    référence (verdict AC2, voir DN_TOUCH_MODE_DEFAUT dans dn_touch.c).
 *    Le chronomètre, lui, est désormais désarmé par `dn_ui_pause()` : même si un
 *    clic passe, il ne publiera pas la durée de la pause.
 */
static bool nav_bloque_par_pause(const char *commande)
{
    if (dn_ui_active()) {
        return false;
    }
    printf("refusé : LVGL est en pause — `ui on` d'abord.\n");
    printf("   `%s` armerait le chronomètre de latence sur un cycle de\n", commande);
    printf("   rafraîchissement qui n'aura pas lieu : la mesure publierait la\n");
    printf("   durée de la PAUSE au lieu de celle de la transition.\n");
    return true;
}

static void nav_usage(void)
{
    printf("usage : nav                        vue courante et compteurs\n");
    printf("        nav open <0..%d>            ouvre le detail d'une metrique\n",
           DN_UI_METRIQUES - 1);
    printf("        nav back                   retour au dashboard\n");
    printf("        nav model rebuild|screens  MODELE de navigation (A/B d'AC4)\n");
    printf("        nav ab <n>                 n allers-retours, chronometres\n");
}

static int cmd_nav(int argc, char **argv)
{
    if (argc < 2) {
        printf("vue : %s", dn_ui_vue_name(dn_ui_vue()));
        if (dn_ui_vue() == DN_VUE_DETAIL) {
            printf(" « %s »", dn_ui_metrique_nom(dn_ui_metrique()));
        }
        printf(" · modele « %s » · %" PRIu32 " transitions depuis le boot\n",
               dn_nav_model_name(dn_ui_get_nav_model()), dn_ui_nav_count());
        printf("taps sur zone : %" PRIu32 " (dont %" PRIu32
               " sur MENU) · derniere zone touchee : %s\n",
               dn_ui_taps(), dn_ui_menu_taps(),
               dn_ui_zone_nom(dn_ui_dernier_tap()));
        printf("metriques : ");
        for (int i = 0; i < DN_UI_METRIQUES; i++) {
            printf("%d=%s ", i, dn_ui_metrique_nom(i));
        }
        printf("\n");
        dn_ui_log_mem();
        nav_usage();
        return 0;
    }

    if (strcmp(argv[1], "open") == 0) {
        long idx = 0;
        if (argc < 3 || !parse_entier(argv[2], &idx)) {
            printf("usage : nav open <0..%d>\n", DN_UI_METRIQUES - 1);
            return 1;
        }
        if (nav_bloque_par_pause("nav open")) {
            return 1;
        }
        esp_err_t err = dn_ui_nav_open((int)idx);
        /* ⚠️ On ANNONÇAIT « detail ouvert » pour une transition qui n'avait pas
         * eu lieu : dn_ui_nav_open rendait ESP_OK même quand la vue demandée
         * était déjà l'active. Aucun écran n'avait changé, aucun chronomètre
         * n'était armé — et la ligne imprimée disait le contraire. */
        if (err == ESP_ERR_INVALID_STATE) {
            printf("rien a faire : le detail « %s » est DEJA affiche.\n",
                   dn_ui_metrique_nom((int)idx));
            printf("(aucune transition, aucun chronometre arme)\n");
            return 0;
        }
        if (err != ESP_OK) {
            printf("refuse : %s\n", esp_err_to_name(err));
            return 1;
        }
        printf("detail « %s » ouvert.\n", dn_ui_metrique_nom((int)idx));
        return 0;
    }

    if (strcmp(argv[1], "back") == 0) {
        if (nav_bloque_par_pause("nav back")) {
            return 1;
        }
        esp_err_t err = dn_ui_nav_back();
        if (err == ESP_ERR_INVALID_STATE) {
            printf("rien a faire : le dashboard est DEJA affiche.\n");
            printf("(aucune transition, aucun chronometre arme)\n");
            return 0;
        }
        if (err != ESP_OK) {
            printf("refuse : %s\n", esp_err_to_name(err));
            return 1;
        }
        printf("retour au dashboard.\n");
        return 0;
    }

    if (strcmp(argv[1], "model") == 0) {
        dn_nav_model_t m;
        if (argc < 3 || !dn_nav_model_from_name(argv[2], &m)) {
            printf("usage : nav model rebuild|screens\n");
            printf("  rebuild : lv_obj_clean + reconstruction (pattern historique)\n");
            printf("  screens : deux racines permanentes + lv_screen_load\n");
            return 1;
        }
        esp_err_t err = dn_ui_set_nav_model(m);
        if (err != ESP_OK) {
            printf("refuse : %s\n", esp_err_to_name(err));
            return 1;
        }
        printf("modele « %s » — la vue est revenue au dashboard (les deux modeles\n",
               dn_nav_model_name(m));
        printf("ne tiennent pas leur etat au meme endroit).\n");
        printf("⚠️ comparer proprement : `touch reset` puis `nav ab 20`, sans\n");
        printf("   toucher la dalle pendant la serie.\n");
        printf("arbitrage AC4, re-mesure le 2026-08-16 dans CETTE config :\n");
        printf("   screens 307,0 ms moy (285,0/320,8) · tas 15 216 o\n");
        printf("   rebuild 346,9 ms moy (300,8/374,2) · tas 12 184 o\n");
        printf("   => screens gagne 39,9 ms (11,5 %%) pour +3 032 o de tas.\n");
        return 0;
    }

    if (strcmp(argv[1], "ab") == 0) {
        long n = 10;
        if (argc >= 3 && !parse_entier(argv[2], &n)) {
            printf("« %s » n'est pas un nombre.\n", argv[2]);
            return 1;
        }
        if (n < 1 || n > 200) {
            printf("refuse : entre 1 et 200 allers-retours.\n");
            return 1;
        }
        if (!dn_ui_active()) {
            printf("refuse : LVGL est en pause (`ui on` d'abord).\n");
            return 1;
        }
        /*
         * ── LA PREUVE DE NON-FUITE ÉTAIT AVEUGLE (correctif de revue dn1-4) ──
         *
         * Elle n'encadrait la série que par `dn_measure_internal_free()` et
         * `dn_measure_psram_free()`. Or LVGL n'alloue dans NI L'UN NI L'AUTRE :
         * `CONFIG_LV_MEM_ADR=0` + `LV_MEM_SIZE_KILOBYTES=64` lui donnent un pool
         * STATIQUE en .bss, et aucun `lv_obj_create` ne passe par
         * heap_caps_malloc. Le firmware le disait lui-même dans `dn_ui_log_mem`
         * (« ces octets-là sont réservés au LINK : ils n'apparaissent PAS dans
         * l'avant/après de `mem` ») — et publiait quand même « delta ZÉRO
         * octet » comme preuve d'AC4. Ce zéro se serait affiché à l'identique
         * avec une fuite d'un écran complet par transition, ce qui était
         * précisément le cas (voir build_scene).
         *
         * `lv_mem_monitor` est le seul instrument qui voit ce tas-là, et l'AC4
         * le demandait nommément : « lv_mem_monitor + RAM interne stables
         * (chiffres avant/après consignés) ». Il n'était appelé qu'APRÈS.
         */
        size_t interne_avant = dn_measure_internal_free();
        size_t psram_avant = dn_measure_psram_free();
        size_t lvgl_avant = dn_ui_lvgl_used();
        /* Témoin du DOIGT : rien n'empêche un tap de s'intercaler pendant les
         * ~100 s que peut durer la série, avec son propre chronomètre. Les
         * échantillons du doigt et du script se mélangeraient alors dans le
         * min/moy/max qui sert d'arbitrage à AC4. On ne peut pas l'interdire
         * sans mentir sur ce qu'est la carte — on le DÉTECTE et on le dit. */
        uint32_t taps_avant = dn_ui_taps();
        dn_touch_reset_latence();
        printf("%ld allers-retours en modele « %s »…\n", n,
               dn_nav_model_name(dn_ui_get_nav_model()));
        printf("⚠️ NE PAS TOUCHER LA DALLE pendant la serie.\n");
        uint32_t transitions = 0;
        for (long i = 0; i < n; i++) {
            esp_err_t e1 = dn_ui_nav_open((int)(i % DN_UI_METRIQUES));
            /* Laisser le cycle de rafraîchissement ABOUTIR avant de repartir :
             * sans cette pause, la seconde transition arriverait pendant le
             * redessin de la première et la latence mesurée serait celle d'un
             * régime que le doigt ne produit jamais.
             * ⚠️ 250 ms NE COUVRENT PAS le pire cas : la story a mesuré des
             * transitions à 307 ms (et jusqu'à 480 ms au doigt) — le « ~176 ms »
             * qui justifiait cette valeur a été corrigé en 267 ms par la mesure
             * du même commit. Le délai reste néanmoins suffisant parce que
             * `dn_ui_nav_back()` BLOQUE sur `lvgl_port_lock` jusqu'à la fin du
             * cycle en cours : c'est le mutex qui sérialise, pas ce delay. La
             * valeur est donc une marge de confort, et elle est dite comme
             * telle (revue dn1-4). */
            vTaskDelay(pdMS_TO_TICKS(250));
            esp_err_t e2 = dn_ui_nav_back();
            vTaskDelay(pdMS_TO_TICKS(250));
            /* ESP_ERR_INVALID_STATE = la vue était déjà la bonne : AUCUNE
             * transition n'a eu lieu. On ne le comptait pas, et `lat.n` sortait
             * alors plus petit que 2*n sans que rien ne l'explique. */
            if (e1 == ESP_OK) {
                transitions++;
            }
            if (e2 == ESP_OK) {
                transitions++;
            }
            if ((e1 != ESP_OK && e1 != ESP_ERR_INVALID_STATE) ||
                (e2 != ESP_OK && e2 != ESP_ERR_INVALID_STATE)) {
                printf("interrompu au tour %ld : %s / %s\n", i + 1,
                       esp_err_to_name(e1), esp_err_to_name(e2));
                break;
            }
        }
        size_t interne_apres = dn_measure_internal_free();
        size_t psram_apres = dn_measure_psram_free();
        size_t lvgl_apres = dn_ui_lvgl_used();
        uint32_t taps_pendant = dn_ui_taps() - taps_avant;
        printf("--- non-fuite (AC4) ---------------------------------------\n");
        printf("  tas LVGL    %u -> %u o   (delta %d o)  <- LE tas des ecrans\n",
               (unsigned)lvgl_avant, (unsigned)lvgl_apres,
               (int)((long)lvgl_apres - (long)lvgl_avant));
        printf("  RAM interne %u -> %u o   (delta %d o)\n",
               (unsigned)interne_avant, (unsigned)interne_apres,
               (int)((long)interne_avant - (long)interne_apres));
        printf("  PSRAM       %u -> %u o   (delta %d o)\n", (unsigned)psram_avant,
               (unsigned)psram_apres,
               (int)((long)psram_avant - (long)psram_apres));
        printf("  ⚠️ SEUL le delta du tas LVGL prouve quoi que ce soit ici : les\n");
        printf("     objets LVGL vivent dans un pool STATIQUE en .bss, invisible\n");
        printf("     pour la RAM interne et la PSRAM.\n");
        if (lvgl_avant == 0 || lvgl_apres == 0) {
            printf("🔴 relevé du tas LVGL INDISPONIBLE (verrou non pris) : ce\n");
            printf("   n'est pas « zero utilise », c'est « pas mesure ».\n");
        }
        dn_ui_log_mem();
        dn_touch_latence_t lat;
        dn_touch_get_latence(&lat);
        printf("  transitions REELLES : %" PRIu32 " (demandees : %ld)\n",
               transitions, n * 2);
        if (lat.n) {
            printf("  latence : n=%" PRIu32 " min %" PRIu32 " us · moy %" PRIu32
                   " us · max %" PRIu32 " us\n",
                   lat.n, lat.min_us, lat.total_us / lat.n, lat.max_us);
        }
        if (lat.n != transitions) {
            printf("🔴 n=%" PRIu32 " pour %" PRIu32 " transitions : l'echantillon\n",
                   lat.n, transitions);
            printf("   est INCOMPLET. rejets (dt<0) : %" PRIu32 ".\n", lat.rejets);
        }
        if (taps_pendant) {
            printf("🔴 %" PRIu32 " tap(s) au DOIGT pendant la serie : leurs\n",
                   taps_pendant);
            printf("   chronometres se sont melanges a ceux du script. Les\n");
            printf("   chiffres ci-dessus ne valent RIEN pour un arbitrage —\n");
            printf("   `touch reset` et rejouer sans toucher la dalle.\n");
        }
        printf("-----------------------------------------------------------\n");
        return 0;
    }

    nav_usage();
    return 1;
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

/*
 * 🔴 dn3-2 — `vTaskGetRunTimeStats()` EST RETIRÉE, PARCE QU'ELLE REND DU VIDE
 *    EN SILENCE, ET QUE CET INSTRUMENT EST CELUI D'AC8.
 *
 * MESURÉ le 2026-08-18, deux fois pendant la campagne AC8 : l'en-tête
 * « temps CPU CUMULÉ… » s'imprimait, PUIS RIEN — zéro ligne de tâche — puis
 * l'invite revenait. Ce n'était donc NI une troncature série (l'invite est
 * arrivée), NI un port volé : la fonction a réellement produit une chaîne vide.
 *
 * En cause, sa structure même (FreeRTOS `tasks.c`) : elle fait son PROPRE
 * `pvPortMalloc`, puis `if (ulTotalTime > 0)` après `ulTotalTime /= 100`, et
 * elle N'A AUCUN CHEMIN pour signaler qu'elle n'a rien écrit. Les deux causes
 * possibles — allocation ratée, compteur global inexploitable — sortent
 * EXACTEMENT du même silence, et l'appelant ne peut pas les distinguer.
 *
 * ⚠️ La conséquence en campagne est pire que la panne : une ligne de table
 *    manquante ressemble à une erreur de capture, on la rejoue, et on ne
 *    cherche jamais plus loin. Un relevé perdu au milieu d'une fenêtre de
 *    mesure fait perdre la fenêtre, pas seulement la ligne.
 *
 * ⇒ On passe par `uxTaskGetSystemState()`, exactement comme `cpu [secondes]` un
 *   peu plus bas : MÊME source, MÊME allocation vérifiée, et un message quand
 *   ça rate. « Un instrument qui rend du vide en silence est pire qu'un
 *   instrument en panne. »
 * ⚠️ Le FORMAT de sortie est conservé (`nom \t ticks \t %`) pour que les
 *    dépouillements écrits pour les campagnes dn2/dn3-1 continuent de parser.
 */
static int cpu_table_cumulee(void)
{
    UBaseType_t capacite = uxTaskGetNumberOfTasks() + 8;
    TaskStatus_t *etat = calloc(capacite, sizeof(TaskStatus_t));
    if (!etat) {
        printf("pas assez de RAM pour %u tâches — AUCUNE table produite\n",
               (unsigned)capacite);
        return 1;
    }
    configRUN_TIME_COUNTER_TYPE total = 0;
    UBaseType_t n = uxTaskGetSystemState(etat, capacite, &total);
    if (n == 0) {
        /* Le cas que `vTaskGetRunTimeStats` taisait. Il devient un DIAGNOSTIC :
         * `uxTaskGetSystemState` ne rend 0 que si le tableau est trop petit,
         * c'est-à-dire si des tâches sont nées entre le comptage et l'appel. */
        printf("🔴 uxTaskGetSystemState a rendu 0 tâche pour une capacité de %u "
               "— des tâches sont nées entre le comptage et l'appel. RIEN n'est "
               "publiable, REJOUER.\n",
               (unsigned)capacite);
        free(etat);
        return 1;
    }
    /*
     * 🔴 LE REBOUCLAGE REND LA TABLE IRRECEVABLE, ET C'EST DÉTECTÉ — correctif
     *    de revue (2026-08-18). `configRUN_TIME_COUNTER_TYPE` est un `uint32_t`
     *    alimenté par `esp_timer_get_time()` en µs
     *    (CONFIG_FREERTOS_RUN_TIME_STATS_USING_ESP_TIMER=y) : `total` ET chaque
     *    `ulRunTimeCounter` rebouclent toutes les ~71,6 min, À DES INSTANTS
     *    DIFFÉRENTS. Passé ce seuil, `t > total` est le cas NORMAL et le calcul
     *    sortait des « 400000 % » sans clamp ni marqueur.
     * ⚠️ dn3-2 a corrigé cet instrument parce qu'il rendait du VIDE en silence.
     *    Le remplacement rendait du FAUX en silence dans un autre régime — et
     *    `cpu brut` est l'instrument DÉSIGNÉ d'AC8. On refuse plutôt que de
     *    publier.
     */
    bool reboucle = false;
    for (UBaseType_t i = 0; i < n; i++) {
        if ((unsigned long long)etat[i].ulRunTimeCounter >
            (unsigned long long)total) {
            reboucle = true;
        }
    }
    if (reboucle) {
        printf("🔴 COMPTEUR REBOUCLE (~71,6 min d'uptime) — au moins une tache\n");
        printf("   cumule PLUS que le total. `total` et les compteurs de tache\n");
        printf("   rebouclent a des instants DIFFERENTS : aucun pourcentage\n");
        printf("   n'est calculable. TABLE IRRECEVABLE — `reboot` avant de\n");
        printf("   publier un chiffre d'AC8, ou utiliser `cpu [secondes]`.\n");
        printf("uptime     : %llu s\n",
               (unsigned long long)(esp_timer_get_time() / 1000000));
        free(etat);
        return 1;
    }
    printf("temps CPU CUMULÉ depuis le boot (tâche / ticks / %%) :\n");
    for (UBaseType_t i = 0; i < n; i++) {
        unsigned long long t = (unsigned long long)etat[i].ulRunTimeCounter;
        /* Le pourcentage est calculé ICI, sur le total RELU — et non récité
         * d'un « <1% » que FreeRTOS produisait sans dire par rapport à quoi. */
        unsigned pct = total ? (unsigned)((t * 100ULL) / (unsigned long long)total)
                             : 0;
        printf("%-15s\t%llu\t\t%u%%\n", etat[i].pcTaskName, t, pct);
    }
    printf("total          \t%llu\n", (unsigned long long)total);
    free(etat);
    printf("⚠️ cumulé depuis le boot, et le compteur reboucle toutes les "
           "~71 min.\n");
    printf("   Pour chiffrer la charge ACTUELLE, utiliser `cpu [secondes]`.\n");
    /* 🔴 LA LÉGENDE DISAIT L'INVERSE DE SON DÉNOMINATEUR (revue 2026-08-18).
     *    `uxTaskGetSystemState` pose `total = portGET_RUN_TIME_COUNTER_VALUE()`,
     *    une durée ÉCOULÉE — donc MONO-cœur — pendant que chaque
     *    `ulRunTimeCounter` cumule sur LES DEUX cœurs. La colonne somme donc à
     *    ~200 %, pas à 100 %. L'ancien texte (« le %% est par rapport au total
     *    DEUX CŒURS ») faisait diviser par deux un chiffre déjà rapporté à un
     *    seul cœur — et son propre exemple ne tenait qu'avec le dénominateur
     *    mono. */
    printf("⚠️ Le %% est rapporte a UN cœur (le total est une duree ECOULEE).\n");
    printf("   Sur un biprocesseur la colonne somme donc vers ~200 %%, pas 100 %% :\n");
    printf("   deux IDLE a 99 %% et 85 %% = 184 %%, soit 92 %% d'un bi-cœur au repos.\n");
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

/*
 * ── `pc` : la liaison PC (dn2-2) ─────────────────────────────────────────────
 *
 * TROIS visages, et le deuxième est le cœur de la branche A :
 *   `pc`            l'état : liaison, valeur + âge, compteurs, latence.
 *   `pc $DN,…`      UNE TRAME. C'est le dialecte de l'agent en USB série — il
 *                   parle au REPL comme un humain, la trame est l'argument.
 *                   Aucun octet n'est imprimé quand la trame est acceptée : le
 *                   bruit ajouté au flux console se limite à l'écho de la ligne
 *                   et au re-rendu de l'invite (chiffré en AC3). C'est AUSSI
 *                   l'injecteur de la campagne de bruit d'AC2, depuis
 *                   dn_console.py, sans agent.
 *   `pc reset`      compteurs et latence à zéro (les campagnes s'encadrent).
 */
static int cmd_pc(int argc, char **argv)
{
    if (argc >= 2 && strncmp(argv[1], "$DN,", 4) == 0) {
        if (argc != 2) {
            /* Une trame contenant un espace a DÉJÀ été coupée par le REPL :
             * la juger « valide » morceau par morceau serait un mensonge.
             * ⚠️ ET IL FAUT LA COMPTER (correctif de revue 2026-08-16) : ce
             * chemin rendait la main sans incrémenter quoi que ce soit, alors que
             * dn_link.h affirme « chaque cas est COMPTÉ ». Un seul octet corrompu
             * en 0x20 sur le fil suffisait à faire disparaître des trames pendant
             * que `pc` affichait 0 valide / 0 rejet. */
            dn_link_compter_rejet(DN_LINK_REJET_FORMAT);
            printf("trame en %d morceaux — un espace l'a coupee, rejetee\n",
                   argc - 1);
            return 1;
        }
        if (!dn_link_ingest_ligne(argv[1])) {
            printf("trame rejetee (le compteur dit pourquoi : `pc`)\n");
            return 1;
        }
        return 0;
    }
    /* Un « $DN » MUTILÉ avant sa virgule (première moitié d'une trame coupée en
     * deux, ou octet perdu) : ce n'est plus une trame pour le test ci-dessus, mais
     * ce n'en est pas moins du bruit de liaison — il tombait dans le message
     * d'usage, sans compteur (correctif de revue 2026-08-16). */
    if (argc >= 2 && argv[1][0] == '$') {
        dn_link_compter_rejet(DN_LINK_REJET_TRONQUEE);
        printf("debut de trame mutile (« %s ») — tronquee, rejetee\n", argv[1]);
        return 1;
    }
    if (argc == 2 && strcmp(argv[1], "reset") == 0) {
        dn_link_reset_compteurs();
        printf("compteurs de liaison remis a zero\n");
        return 0;
    }
    /* W4 — l'A/B de poussee, dans le MEME firmware (AC8). */
    if (argc == 3 && strcmp(argv[1], "pousse") == 0) {
        bool etale;
        if (strcmp(argv[2], "groupe") == 0) {
            etale = false;
        } else if (strcmp(argv[2], "etale") == 0) {
            etale = true;
        } else {
            printf("usage : pc pousse groupe|etale\n");
            return 1;
        }
        dn_link_set_etalement(etale);
        printf("poussee : %s\n",
               etale ? "ETALEE — au plus UNE metrique par reveil de 250 ms"
                     : "GROUPEE — tout ce qui a change part dans le MEME reveil");
        if (etale) {
            /* 🔴 CE BLOC PUBLIAIT UNE PREMISSE QUE LA MESURE A DEMENTIE (§17.4).
             * Il annoncait « ca ne reduit pas le travail total, ca reduit le
             * PIC » ; le travail total BAISSE, et il baisse parce que l'etale
             * JETTE des mises a jour. Un operateur qui rejouait l'A/B lisait donc
             * une baisse de flush/s comme un GAIN. Corrige en revue 2026-08-18 :
             * l'instrument doit dire ce que la mesure a trouve, pas ce que la
             * prediction esperait. */
            printf("🔴 MESURE (§17.4) — LA PREMISSE ECRITE D'AVANCE EST DEMENTIE :\n");
            printf("   le travail total BAISSE (5,20 -> 4,21 flush/s), mais il\n");
            printf("   baisse parce que l'etale JETTE 18,1 %% des mises a jour\n");
            printf("   (185 poussees atteignent l'ecran sur 226 trames recues :\n");
            printf("   41 jetees / 226 = 18,1 %%). ⛔ PAS UN GAIN, UNE PERTE.\n");
            printf("⚠️ PRIX 1 : latence max MULTIPLIEE PAR 4 (301 -> 1204 ms).\n");
            printf("⚠️ PRIX 2 : une metrique est rafraichie toutes les ~1,25 s au\n");
            printf("   lieu de ~1 s, et un passage VIVANTE->MORTE met jusqu'a\n");
            printf("   1,25 s de plus a s'afficher sur les cinq cases.\n");
            printf("⛔ LEVIER NON ADOPTE pour ces raisons. Ne pas lire une baisse\n");
            printf("   de flush/s comme un progres sur cette branche.\n");
        }
        printf("⚠️ `flush reset` MAINTENANT, puis attendre >= 3 cycles de source\n");
        printf("   avant `flush` : sinon la mesure melange les deux branches.\n");
        return 0;
    }
    if (argc != 1) {
        printf("usage : pc | pc reset | pc pousse groupe|etale\n");
        printf("        pc $DN,<ver>,<seq>,<t_ms>,<metrique>,<v1>[,<v2>]*<CK>\n");
        printf("        v1 = 6 champs, metrique « cpu » UNIQUEMENT.\n");
        printf("        v2 = 5 metriques, 2e grandeur OPTIONNELLE (son absence\n");
        printf("             est une donnee : « je ne connais pas v2 »).\n");
        return 1;
    }

    dn_link_etat_t etat = dn_link_etat();
    printf("liaison PC : %s (RESUME GLOBAL : VIVANTE des qu'UNE metrique l'est)\n",
           dn_link_etat_nom(etat));
    if (etat != DN_LINK_JAMAIS) {
        printf("             derniere trame toutes metriques : age %lld ms · "
               "seq %u · t_ms agent %u\n",
               (long long)(dn_link_age_us() / 1000),
               (unsigned)dn_link_derniere_seq(), (unsigned)dn_link_dernier_t_ms());
    }
    /*
     * 🔴 LES CINQ METRIQUES, UNE PAR UNE, RELUES DE dn_link — et c'est le seul
     *    endroit qui puisse montrer qu'une source meurt SEULE. Le resume global
     *    ci-dessus dirait « VIVANTE » avec quatre cases mortes.
     */
    printf("metriques  : (peremption %lld ms, par metrique)\n",
           (long long)(DN_LINK_PEREMPTION_US / 1000));
    for (int i = 0; i < DN_LINK_METRIQUES; i++) {
        dn_link_vue_t v;
        if (!dn_link_vue((dn_link_metrique_t)i, &v)) {
            continue;
        }
        int idx = dn_ui_case_de_metrique((dn_link_metrique_t)i);
        printf("  %-5s -> case %d %-9s %-12s", dn_link_metrique_nom(i), idx,
               idx >= 0 ? dn_ui_metrique_nom(idx) : "(aucune)",
               dn_link_etat_nom(v.etat));
        if (v.etat == DN_LINK_JAMAIS) {
            printf("  --\n");
            continue;
        }
        /* 🔴 dn4-6 : LA BOUCLE VA JUSQU'AU COMPTE DECLARE PAR LA METRIQUE, pas
         *    jusqu'a ce que la trame a porte. C'est ce qui permet de DIRE
         *    « attendue mais absente » — un silence tres different de « pas de
         *    grandeur la », et les confondre effacerait l'information que la
         *    source ne publie pas sa °C (ou son tr/min).
         * ⚠️ La valeur est imprimee en DIXIEMES ici, quelle que soit la
         *    precision d'AFFICHAGE du descripteur : la console est un
         *    instrument, elle montre ce qui circule SUR LE FIL. La precision de
         *    l'ecran vit dans `k_desc[]` et se lit par `widget`. */
        /* 🔴 dn4-9 — LE PRÉFIXE D'ÉCRAN EST AJOUTÉ **EN PLUS**, ET ÇA SOLDE UN
         *    RÉSIDUEL DE REVUE DE dn4-8 : *« `pc` ne peut plus nommer QUEL
         *    ventilateur est muet »*. `disk` porte TROIS « tr/min »
         *    byte-identiques dans `k_metriques[].unite`, donc LHM éteint la
         *    console imprimait trois fois exactement la même ligne
         *    « -- (tr/min ATTENDUE, non publiee par la source) ».
         *    ⚠️ Et c'est cette console que `regime_reel_dn48.py` et
         *       `campagne_bruit_dn48.py` LISENT.
         * ⛔ JAMAIS EN TOUCHANT `k_metriques[].unite` : le fil est positionnel,
         *    et le changer casserait les témoins de non-régression v1 et v3.
         * ⚠️ Le commentaire ci-dessus dit que cette commande montre LE FIL, et
         *    ça reste vrai : le préfixe est un nom d'ÉCRAN affiché à côté,
         *    ⛔ pas une réécriture de l'unité du fil. Il vient de `k_desc[]` par
         *    un accesseur, ⛔ pas d'une copie locale. */
        int ng = dn_link_metrique_grandeurs((dn_link_metrique_t)i);
        for (int g = 0; g < ng; g++) {
            const char *u = dn_link_metrique_unite((dn_link_metrique_t)i, g);
            const char *px = (idx >= 0) ? dn_ui_case_prefixe(idx, g) : NULL;
            if (g > 0) {
                printf(" ·");
            }
            if (g < (int)v.n && v.connue[g]) {
                printf(" %s%s%d,%d %s", px ? px : "", px ? " " : "", v.v[g] / 10,
                       v.v[g] % 10, u ? u : "");
            } else {
                printf(" %s%s-- (%s ATTENDUE, non publiee par la source)",
                       px ? px : "", px ? " " : "", u ? u : "?");
            }
        }
        printf("  · age %lld ms · seq %u\n", (long long)(v.age_us / 1000),
               (unsigned)v.seq);
    }
    printf("poussee    : %s\n",
           dn_link_etalement() ? "ETALEE (A/B W4)" : "GROUPEE (defaut)");
    printf("peremption : %lld ms, en temps absolu de RECEPTION — la cadence de\n",
           (long long)(DN_LINK_PEREMPTION_US / 1000));
    printf("             l'agent ne fait jamais foi (AC7)\n");

    dn_link_compteurs_t c;
    dn_link_compteurs(&c);
    printf("trames     : %u valides · %u doublons · %u pertes seq · %u resynchros"
           " · %u reprises\n",
           (unsigned)c.recues, (unsigned)c.doublons, (unsigned)c.pertes_seq,
           (unsigned)c.resynchros, (unsigned)c.reprises);
    printf("rejets     : tronquee %u · trop longue %u · checksum %u · version %u · "
           "format %u · bornes %u\n",
           (unsigned)c.rejets_tronquee, (unsigned)c.rejets_trop_longue,
           (unsigned)c.rejets_checksum, (unsigned)c.rejets_version,
           (unsigned)c.rejets_format, (unsigned)c.rejets_bornes);
    printf("             tronquee = la fin de ligne est PERDUE · trop longue = la\n");
    printf("             ligne est COMPLETE mais depasse %d o (emetteur elargi)\n",
           DN_LINK_LIGNE_MAX);
    printf("             ⚠️ bande « trop longue » ATTEIGNABLE : le REPL delivre\n");
    printf("             %d caracteres de trame au parseur (MESURE, dn4-1) —\n",
           DN_LINK_REPL_LIGNE_MESUREE);
    printf("             la bande %d..%d est donc large de %d o. Un compteur\n",
           DN_LINK_LIGNE_MAX + 1, DN_LINK_REPL_LIGNE_MESUREE,
           DN_LINK_REPL_LIGNE_MESUREE - DN_LINK_LIGNE_MAX);
    printf("             inatteignable serait un instrument qui ment.\n");
    printf("             resynchros = saut de seq non credible (agent redemarre,\n");
    printf("             seq fabrique) : trame APPLIQUEE, pas comptee en pertes\n");

    uint32_t n;
    int64_t lmin, lmoy, lmax;
    dn_link_latence(&n, &lmin, &lmoy, &lmax);
    if (n > 0) {
        printf("latence acceptation->label : n=%u · min %lld ms · moy %lld ms · "
               "max %lld ms\n",
               (unsigned)n, (long long)(lmin / 1000), (long long)(lmoy / 1000),
               (long long)(lmax / 1000));
    } else {
        printf("latence acceptation->label : aucune poussee encore\n");
    }
    printf("  (NON instrumente ici : echantillonnage cote PC, vol dans le\n");
    printf("   transport, et le flush LVGL suivant — <= 1 cycle, ~27 ms)\n");
    printf("transport  : wifi %s", dn_wifi_etat_nom(dn_wifi_etat()));
    if (dn_wifi_etat() == DN_WIFI_CONNECTEE) {
        printf(" ip %s rssi %d dBm", dn_wifi_ip(), dn_wifi_rssi());
    }
    printf(" · ws %s (%u messages, %u connexions)\n",
           dn_wifi_ws_actif() ? "ACTIF" : "off", (unsigned)dn_wifi_ws_messages(),
           (unsigned)dn_wifi_ws_connexions());
    printf("             branche A = cette console : l'agent envoie `pc $DN,...`\n");
    return 0;
}

/*
 * ── `wifi` : la maquette branche B (dn2-2) ──────────────────────────────────
 * Le SSID ne peut pas contenir d'espace ici : le REPL coupe sur les espaces,
 * et un guillemet mentirait (esp_console ne les fusionne pas). Refusé, pas
 * deviné — le SSID de la maison n'en a pas.
 */
/*
 * ── `widget` — L'INSTRUMENT DU MODÈLE (dn3-1) ────────────────────────────────
 *
 * Il fait QUATORZE choses. Aucune ne DORT — la console EST le transport PC depuis
 * dn2-2, et une commande qui dort couperait la liaison qu'elle prétend observer
 * (c'est le défaut mesuré de `cpu N`). Mais CINQ d'entre elles font un travail
 * LONG, et c'est écrit ci-dessous plutôt que nié.
 *
 *   widget                  l'état des 6 cases : régime, valeurs, forme du mock
 *   widget groupe on|off    A/B d'AC8 — N zones sales fines vs 1 englobante
 *   widget opa <0..255>     A/B d'AC9 — opacité des CASES        ⚠️ RECONSTRUIT
 *   widget voile <0..255>   AC9 — opacité du voile plein écran   ⚠️ RECONSTRUIT
 *   widget icone <case> <n> W4 — A/B de glyphe sur UNE case      ⚠️ RECONSTRUIT
 *   widget mock on|off      coupe le mock : la case redevient « -- » (témoin)
 *   widget demo on|off [n]  AC1 — la 7e métrique FICTIVE, sans code de dessin
 *                           ⚠️ `n` (1..6) est le SEUL chemin vers les deux
 *                           témoins d'AC2 de dn4-6 : abandon de jauge (n ≥ 3)
 *                           et clamp de `GRANDEURS_MAX` (n = 5)
 *   widget pousser <idx>    AC8 — UNE mise à jour synthétique, une par appel
 *   widget oublier <idx>    rend la case à son régime NATUREL après une poussée
 *   widget rafale           AC8 — les 6 poussées sous UN SEUL verrou (1 cycle)
 *   widget nue <idx> on|off W11 — le témoin négatif d'AC8, à chaud ⚠️ RECONSTRUIT
 *   widget barre 1hz|minute W2/AC4 — la cadence de la barre heure/date
 *   widget bandes on|off    W8/AC9 — le repeint en BANDES pleine largeur
 *   widget piste <0xRRGGBB> le fond de la jauge, part NON remplie ⚠️ RECONSTRUIT
 *
 *   ── dn4-6 / AC4 : LES TROIS VOIES, COMMUTÉES À CHAUD ────────────────────
 *   widget voie defaut|a|b|c|c2   applique une voie ENTIÈRE et IMPRIME SON PRIX
 *                                 avant le constat owner       ⚠️ RECONSTRUIT ×2
 *   widget voie repli               le REPLI pré-autorisé : D12 seule, police
 *                                   28 INCHANGÉE, en-tête INTACT ⚠️ RECONSTRUIT
 *   widget grandeurs <case> <n>     le nombre de grandeurs d'UNE case, à chaud
 *                                   (0 = rendre la case à son descripteur) —
 *                                   le SEUL moyen de comparer le repli aux
 *                                   trois voies dans le MÊME firmware
 *                                                                ⚠️ RECONSTRUIT
 *   widget replacer on|off          INSTRUMENT de bissection : `off` ramène le
 *                                   chemin de MISE À JOUR à celui de dn4-1
 *   widget dispo empile|cote|mixte  la mise en forme des grandeurs ⚠️ RECONSTRUIT
 *   widget entete normal|compact    l'en-tête (icône 28 -> 14)    ⚠️ RECONSTRUIT
 *   widget val <y> <pas>            `val_y` / `val_pas`, interligne ⚠️ RECONSTRUIT
 *   widget police 14|28             la police des VALEURS         ⚠️ RECONSTRUIT
 *   widget grille <barre> <menu>    D12 (60 51) / voie (a) (60 0) ⚠️ RECONSTRUIT
 *   ── dn4-6 / AC5 : LA LARGEUR, MESURÉE ───────────────────────────────────
 *   widget detail           ce que la GRANDE VALEUR du détail a POSÉ : texte,
 *                           largeur réelle, panneau — ⛔ relu, jamais recomposé
 *   widget largeur          la table des couples, RELUE de `lv_text_get_size()`
 *   widget largeur <texte>  la largeur d'UNE chaîne dans la police liée
 *   widget largeur reset    remet à zéro le compteur de CHEVAUCHEMENTS détectés
 *
 * 🔴 LES **DOUZE** « RECONSTRUIT » BLOQUENT LE REPL, DONC LE TRANSPORT PC (relevé
 *    en revue le 2026-08-18 : ce docblock affirmait qu'AUCUNE sous-commande
 *    n'était un travail long, trois lignes au-dessus de trois qui le sont — puis
 *    dn3-2 en a ajouté CINQ sans les lister, dont `nue`, qui reconstruit AUSSI
 *    et qui est l'instrument CENTRAL du témoin négatif d'AC8 ; puis la séance du
 *    2026-08-18 a ajouté `piste`, qui reconstruit AUSSI, et le compte est reparti
 *    de « trois » à « quatre » sans jamais atteindre CINQ. ⛔ Ce compte est
 *    manifestement un point de rupture : il se corrige ICI **et** dans le
 *    « Jeu complet » du README **dans le même geste**, jamais dans un seul des
 *    deux).
 *
 * 🔴 ET IL A ROMPU UNE TROISIÈME FOIS — REVUE DE CODE DU 2026-08-19. dn4-6 avait
 *    écrit ici « dn4-6 en a ajouté HUIT … le compte passe à TREIZE » en n'en
 *    listant que SEPT, pendant que le README publiait « de CINQ à ONZE ».
 *    **Trois textes, trois valeurs, aucune juste**, et corrigés dans le MÊME
 *    commit — la règle « dans le même geste » avait donc été tenue à la lettre
 *    et manquée sur le fond.
 *    LA LISTE, RELUE DU CODE, EST CELLE-CI — 5 anciennes + 7 de dn4-6 = **12** :
 *      anciennes : `opa` · `voile` · `icone` · `nue` · `piste`
 *      dn4-6     : `voie` · `grandeurs` · `dispo` · `entete` · `val` · `police`
 *                  · `grille`
 *    ⛔ `replacer`, `largeur` et `detail` NE reconstruisent PAS : ne pas les y
 *       ajouter « pour faire le compte ».
 *    ⚠️ `widget voie` ne reconstruit plus qu'**UNE SEULE FOIS** (~350 ms) depuis
 *       `ce41caf` : `dn_ui_set_voie()` prend un verrou et appelle un seul
 *       `build_scene()`. Le texte qui annonçait « DEUX FOIS, ~700 ms » décrivait
 *       le DÉFAUT corrigé, pas le produit.
 *    Elles
 *    prennent `lvgl_port_lock(2000)` puis appellent `build_scene()`, qui détruit
 *    et reconstruit LES DEUX racines — plus lourd qu'une transition, que §15.6
 *    chiffre à 307-322 ms avec un plancher de rendu LVGL ~230 ms. Comparaison :
 *    `i2c` bloque ~26 ms et le README le signale.
 *    ⇒ NE PAS les appeler pendant une campagne de mesure de la liaison. Elles
 *    sont faites pour un A/B à l'œil, entre deux campagnes, pas pendant.
 *
 * 🔴 TOUT CE QU'IL IMPRIME EST RELU DE L'ÉTAT RÉEL. Le régime vient de
 *    `dn_ui_regime()`, la forme du mock de `dn_ui_mock_forme()`, l'opacité de
 *    `dn_widget_opa()`. Rien n'est récité depuis une constante d'affichage —
 *    c'est la classe de défaut que ce dépôt traque depuis dn1-3 (« 5 kHz » pour
 *    un PWM à 24 kHz, « FORCED T/H 8x » sur des registres à 0x00), et dn2-1 l'a
 *    re-commise UNE LIGNE sous son propre correctif.
 */
/*
 * Imprime `s` puis le rembourrage pour atteindre `largeur` COLONNES D'AFFICHAGE.
 * En UTF-8, un octet de continuation vaut `10xxxxxx` : il appartient au
 * caractère précédent et n'occupe aucune colonne. Compter les octets — ce que
 * fait `%-Ns` — décale toute ligne portant un accent, et depuis dn3-1 les
 * libellés en portent.
 * ⚠️ Vrai pour le latin-1 en UTF-8 (1 codepoint = 1 colonne). Ne conviendrait
 *    pas à du CJK (2 colonnes par glyphe) — hors sujet ici, mais autant que la
 *    limite soit écrite plutôt que découverte.
 */
static void colonnes(const char *s, int largeur)
{
    int cols = 0;
    for (const unsigned char *p = (const unsigned char *)s; *p; p++) {
        if ((*p & 0xC0) != 0x80) {
            cols++;
        }
    }
    printf("%s", s);
    for (int i = cols; i < largeur; i++) {
        printf(" ");
    }
}

/*
 * ── dn4-9 : LES INDICES QUE LA CASE DESSINE, RELUS ───────────────────────────
 *
 * 🔴 UN COMPTE NE SUFFIT PLUS. Depuis que la CASE et le DÉTAIL montrent des
 *    sous-ensembles différents, « CPU : 3 grandeurs » ne dit pas LESQUELLES —
 *    et c'est exactement la question qu'on vient poser à la console : la case
 *    montre-t-elle [0, 1, 3] (ce que D13 demande) ou [0, 1, 2] (l'ancien
 *    mécanisme) ? Les deux comptent TROIS.
 * ⚠️ RELU de `dn_ui_case_indices()`, ⛔ jamais recomposé ici : la console a
 *    déjà eu sa PROPRE copie d'une règle d'affichage, et elle imprimait
 *    « Mb/s » sur une valeur convertie en Gb/s (revue 2026-08-19).
 */
static void widget_indices_imprimer(int idx)
{
    uint8_t sel[DN_WIDGET_GRANDEURS_MAX];
    int n = dn_ui_case_indices(idx, sel, DN_WIDGET_GRANDEURS_MAX);
    printf("[");
    for (int r = 0; r < n; r++) {
        printf("%s%d", r ? ", " : "", (int)sel[r]);
    }
    printf("]");
}

static int cmd_widget(int argc, char **argv)
{
    if (argc == 3 && strcmp(argv[1], "groupe") == 0) {
        /* dn4-10 : TROISIÈME mode. `union` gagne l'atomicité du groupé (UNE
         * zone sale, donc UN flush) sans salir le conteneur entier. ⛔ Il est
         * posé pour être ÉPROUVÉ à chaud, pas annoncé comme un correctif. */
        if (strcmp(argv[2], "union") == 0) {
            if (dn_ui_set_groupe_union() != ESP_OK) {
                printf("verrou LVGL non pris — RIEN n'a change\n");
                return 1;
            }
            printf("invalidation : UNION — 1 zone sale par widget, bornee aux "
                   "VALEURS\n");
            printf("   atomicite du groupe (1 zone = 1 flush = pas d'etat\n");
            printf("   intermediaire visible), aire du fin.\n");
            printf("⚠️ NON MESURE a l'ecriture : c'est une TROISIEME branche a\n");
            printf("   eprouver contre `on` et `off`, pas un correctif annonce.\n");
            printf("⚠️ `flush reset` MAINTENANT, puis attendre >= 3 cycles de "
                   "source\n");
            printf("   avant `flush` : sinon la mesure melange les branches.\n");
            return 0;
        }
        bool on;
        if (!parse_on_off(argv[2], &on)) {
            printf("usage : widget groupe on|off|union\n");
            return 1;
        }
        /* ⚠️ PASSE PAR `dn_ui`, QUI PREND LE VERROU (revue 2026-08-18).
         *    `dn_widget_set_groupage()` était appelée NUE depuis le REPL, alors
         *    que `dn_widget.h` écrit que « les seuls appelants légitimes sont
         *    les fonctions publiques de `dn_ui` et les callbacks de timer LVGL ».
         *    C'était la seule exception non marquée du module. */
        if (dn_ui_set_groupage(on) != ESP_OK) {
            printf("verrou LVGL non pris — RIEN n'a change\n");
            return 1;
        }
        /* Géométrie RELUE, pas récitée : « 225x156 = 35 100 px » était écrit en
         * dur, alors que dn3-2 refait la géométrie (§15.2). */
        printf("invalidation : %s\n",
               on ? "GROUPEE — 1 zone sale par widget (le conteneur)"
                  : "FINE — LVGL fait SES zones, une par enfant modifie");
        if (on) {
            int cw = 0, ch = 0;
            dn_ui_case_dim(&cw, &ch);
            printf("   soit %d x %d = %d px par mise a jour\n", cw, ch, cw * ch);
        }
        printf("⚠️ `flush reset` MAINTENANT, puis attendre >= 3 cycles de source\n");
        printf("   avant `flush` : sinon la mesure melange les deux branches.\n");
        return 0;
    }
    /* ⚠️ dn4-1 : LA CASE EST DEVENUE UN ARGUMENT. `widget icone <n>` écrivait
     *    l'icône de la case 4 EN DUR — après le renommage VENTILOS -> DISQUE
     *    (D8), l'A/B aurait continué de viser « l'ancienne case ventilateur »
     *    par pur hasard d'index, en l'annonçant comme un choix. La forme est
     *    donc `widget icone <case> <n>`. */
    /* La PISTE de la jauge — constat owner du 2026-08-18. Même patron que
     * `opa`/`voile` : l'arbitrage de teinte est un CONSTAT OWNER sur la dalle,
     * et il ne doit pas coûter un reflash par essai. */
    /*
     * ════════════════════════════════════════════════════════════════════════
     * dn4-6 / AC4 — LES TROIS VOIES, COMMUTEES A CHAUD
     * ════════════════════════════════════════════════════════════════════════
     * ⛔ RIEN N'EST TRANCHE SUR LE PAPIER. Le verdict est un CONSTAT OWNER
     *    verbatim sur la dalle. Ce que la console doit faire, c'est rendre les
     *    trois JOUABLES sans reflasher, et ANNONCER LE PRIX DE CHACUNE AVANT le
     *    constat — un A/B dont une branche est deja refutee par l'arithmetique
     *    sans qu'on l'ait dit n'est pas un A/B.
     */
    if (argc == 3 && strcmp(argv[1], "voie") == 0) {
        dn_widget_geom_t g;
        dn_widget_geom(&g);
        int bh = 0, mh = 0;
        dn_ui_geom_bandes_defaut(&bh, &mh); /* ⛔ RELUS, jamais recites */
        const char *quoi = argv[2];
        bool connue = true;

        if (strcmp(quoi, "defaut") == 0) {
            /* ⚠️ « defaut » = LES DÉFAUTS DU FIRMWARE, relus des macros — donc
             *    D12 (60/51, case 163) depuis que la voie retenue est gravée,
             *    ⛔ PAS l'état d'avant-D12. L'aide affirmait « barre 70/menu 60 »
             *    alors que ce chemin applique 60/51 (revue 2026-08-19). */
            dn_widget_geom_defaut(&g);
        } else if (strcmp(quoi, "avantd12") == 0) {
            /* 🔴 LA RÉFÉRENCE D'AVANT-D12, REDEVENUE ATTEIGNABLE PAR `voie`.
             *    La ligne « défaut (avant D12) 225x156 » de la table §18.1 ne se
             *    rejouait plus que par `widget grille 70 60` — un chemin qui ne
             *    remettait pas les compteurs à zéro, donc qui additionnait le
             *    résidu de l'état précédent. Une table de voies dont une ligne
             *    n'est pas reproductible n'arbitre rien. */
            bh = 70;
            mh = 60;
            dn_widget_geom_defaut(&g);
        } else if (strcmp(quoi, "a") == 0) {
            /* (a) police 28, MENU SUPPRIME. case_h = 180. */
            bh = 60;
            mh = 0;
            dn_widget_geom_defaut(&g);
            g.entete = DN_ENTETE_COMPACT;
            g.val_y = 36;
            g.val_pas = 36; /* interligne 1 px — 36 + 4x36 = 180 PILE */
        } else if (strcmp(quoi, "b") == 0) {
            /* (b) 3e police + D12. ⚠️ LA 3e POLICE N'EST PAS EMBARQUEE : voir
             * le prix imprime ci-dessous. On joue la branche avec la police 14
             * pour que la GEOMETRIE soit constatable, ⛔ et on le DIT. */
            bh = 60;
            mh = 51;
            dn_widget_geom_defaut(&g);
            g.entete = DN_ENTETE_COMPACT;
            g.val_y = 36;
            g.font_val = &dn_font_14;
            g.val_pas = 30;
        } else if (strcmp(quoi, "c") == 0) {
            /* (c) cote a cote. ⛔ NE TOUCHE NI LA POLICE, NI LE CHROME, NI
             * L'EN-TETE, NI LES BANDES. C'est son argument principal. */
            dn_widget_geom_defaut(&g);
            g.dispo = DN_DISPO_COTE;
        } else if (strcmp(quoi, "c2") == 0) {
            /* (c) variante MIXTE : ligne 1 cote a cote, le reste empile.
             * ⚠️ A 4 grandeurs elle fait TROIS lignes (y_bas 168) : elle ne
             *    tient QUE sur une case de 180, donc avec (a). C'est une
             *    variante, pas une voie — et elle est nommee pour ca. */
            bh = 60;
            mh = 0;
            dn_widget_geom_defaut(&g);
            g.dispo = DN_DISPO_MIXTE;
        } else if (strcmp(quoi, "repli") == 0) {
            /* LE REPLI PRE-AUTORISE, ECRIT D'AVANCE DANS LA STORY : `GPU` a
             * TROIS (% · °C · W) + D12, police 28 INCHANGEE, en-tete INTACT.
             * Arithmetique : derniere valeur a 48 + 2x40 = 128, bas de boite
             * 128 + 35 = 163 <= 163 PILE, interligne 40 - 35 = 5 px — le
             * critere ecrit de D12, tenu a l'unite pres. */
            bh = 60;
            mh = 51;
            dn_widget_geom_defaut(&g);
        } else {
            connue = false;
        }
        if (!connue) {
            printf("usage : widget voie defaut|avantd12|a|b|c|c2|repli\n");
            printf("  defaut   LES DEFAUTS DU FIRMWARE, relus : empile, 28 px,\n");
            printf("           barre 60/menu 51 (D12) ⇒ case 163. C'est la VOIE\n");
            printf("           RETENUE, pas l'etat d'avant-D12.\n");
            printf("  avantd12 la reference §18.1 : barre 70/menu 60 ⇒ case 156,\n");
            printf("           compteurs remis a zero — c'est la ligne « defaut\n");
            printf("           (avant D12) » de la table des voies.\n");
            printf("  a       28 px, MENU SUPPRIME (case 180), en-tete COMPACT\n");
            printf("  b       3e police + D12 (case 163), en-tete COMPACT\n");
            printf("  c       COTE A COTE, geometrie INCHANGEE\n");
            printf("  c2      MIXTE (l1 cote a cote) — exige la case de 180\n");
            printf("  repli   D12 seule, police 28 INCHANGEE, en-tete INTACT\n");
            printf("          ⚠️ elle exige `widget grandeurs 1 3` (GPU a TROIS) :\n");
            printf("             c'est le repli PRE-AUTORISE de la story, et il\n");
            printf("             ne peut pas se juger sans etre APPLIQUE.\n");
            return 1;
        }

        /* ⚠️ UN SEUL APPEL, DONC UNE SEULE RECONSTRUCTION. Enchainer les deux
         *    setters produisait une scene INTERMEDIAIRE (nouvelle hauteur,
         *    ancienne geometrie interne) dont les debordements etaient comptes
         *    et attribues a la voie — l'instrument accusait la voie du defaut
         *    de son propre chemin d'application. Voir `dn_ui_set_voie`. */
        esp_err_t e1 = dn_ui_set_voie(bh, mh, &g);
        if (e1 != ESP_OK) {
            printf("voie refusee (%s) — RIEN n'a change\n", esp_err_to_name(e1));
            return 1;
        }

        int cw = 0, ch = 0;
        dn_ui_case_dim(&cw, &ch);
        int lh = (int)lv_font_get_line_height(g.font_val ? g.font_val
                                                         : &dn_font_28);
        printf("VOIE « %s » APPLIQUEE — scene reconstruite UNE fois.\n", quoi);
        printf("  case %dx%d · val_y %d · val_pas %d · interligne %d px\n", cw, ch,
               g.val_y, g.val_pas, g.val_pas - lh);
        printf("  %s · %s\n", dn_widget_dispo_nom(g.dispo),
               dn_widget_entete_nom(g.entete));
        printf("\n⚠️ CE QU'ELLE COUTE — A LIRE AVANT DE REGARDER LA DALLE :\n");
        if (strcmp(quoi, "a") == 0) {
            printf("  · la barre MENU QUITTE LA MAQUETTE (addendum §1 a amender)\n");
            printf("  · interligne 1 px : LES VALEURS SE TOUCHENT — le critere\n");
            printf("    ecrit de D12 est « jamais sous 5 px »\n");
            printf("  · l'en-tete est COMPACTE : les SIX icones passent de 28 a\n");
            printf("    14 px, et l'icone est le SEUL endroit ou le champ\n");
            printf("    `couleur` du descripteur est EXERCE. C'est une DECISION\n");
            printf("    OWNER, pas un reglage de dev.\n");
            printf("  🔴 SANS l'en-tete compacte, (a) EST REFUTEE PAR L'ARITHMETIQUE :\n");
            printf("     l'icone 28 descend a 43 px, et 44 + 4x35 = 184 > 180.\n");
        } else if (strcmp(quoi, "b") == 0) {
            printf("  🔴 LA 3e POLICE (~22) N'EST PAS EMBARQUEE. Ce qui est joue\n");
            printf("     ici est la police 14 — la geometrie est representative,\n");
            printf("     LA LISIBILITE NE L'EST PAS (14 px contre ~22 vises).\n");
            printf("     ⛔ Ne pas conclure « illisible » de cette branche : le\n");
            printf("        verdict de (b) exige de GENERER la police (T10), ce\n");
            printf("        qui coute npm + reseau et ~19 Ko EXTRAPOLES.\n");
            printf("  · D12 applique : toutes les coordonnees tactiles publiees\n");
            printf("    PERIMENT (VENTILOS 506..516, jauge y=340..350)\n");
            printf("  · +4,5%% de surface par case (35 100 -> 36 675 px)\n");
            printf("  · en-tete COMPACTE — meme decision owner que (a)\n");
        } else if (strcmp(quoi, "c") == 0 || strcmp(quoi, "c2") == 0) {
            printf("  · LE MUR PASSE SUR LA LARGEUR : `widget largeur` MESURE,\n");
            printf("    ⛔ ne pas conclure « ca tient » parce que rien n'a plante\n");
            printf("    — LVGL clippe au parent SANS un mot.\n");
            printf("  · `y_bas` BAISSE ⇒ le contrat W5 de dn_widget.h est a\n");
            printf("    REECRIRE : l'arbitrage jauge/secondaire n'avait de sens\n");
            printf("    que parce que l'empilement mangeait la hauteur.\n");
            if (strcmp(quoi, "c") == 0) {
                printf("  ✅ ELLE NE TOUCHE NI LA POLICE, NI LE CHROME, NI L'EN-TETE,\n");
                printf("     NI LES BANDES — et elle rend D12 NON NECESSAIRE a la\n");
                printf("     tenue (48 + 2x40 = 128 <= 156). Le MOTIF de D12 tombe ;\n");
                printf("     D12 reste une decision owner. ⇒ question OWNER (X10).\n");
            } else {
                printf("  ⚠️ c2 exige la case de 180 (donc le MENU supprime) : a 4\n");
                printf("     grandeurs elle fait TROIS lignes, y_bas = 168.\n");
            }
        } else if (strcmp(quoi, "repli") == 0) {
            printf("  · `GPU` DESCEND A TROIS : le tr/min est ABANDONNE. C'est le\n");
            printf("    prix, et il est ecrit d'avance dans la story.\n");
            printf("    ⇒ `widget grandeurs 1 3` pour l'appliquer, sinon la case\n");
            printf("      GPU DEBORDE encore et le compteur le dira.\n");
            printf("  · D12 : toutes les coordonnees tactiles publiees PERIMENT,\n");
            printf("    +4,5%% de surface par case sur un duty deja a 10,09 %%\n");
            printf("  ✅ EN ECHANGE : police 28 INCHANGEE, en-tete INTACT (l'icone\n");
            printf("     garde ses 28 px et le champ `couleur` reste exerce),\n");
            printf("     interligne 5 px = le critere ecrit de D12, AUCUNE\n");
            printf("     regeneration de police, AUCUNE npm, AUCUN reseau.\n");
        } else {
            printf("  (aucun — c'est l'etat des lieux mesure en §17.10)\n");
        }
        printf("\n  ⇒ « ca ne tient pas » SUR CETTE VOIE : %u chevauchement(s) "
               "cote a cote · %u trop large(s) en colonne unique · %u en HAUTEUR\n",
               (unsigned)dn_widget_chevauchements(),
               (unsigned)dn_widget_trop_larges(),
               (unsigned)dn_widget_debordements());
        printf("     (compteurs remis a zero SOUS LE VERROU juste avant la\n");
        printf("      reconstruction : c'est bien CETTE voie qui est comptee)\n");
        printf("\n⚠️ La reconstruction a retire le stimulus `anim` et la demo.\n");
        printf("⚠️ Elle a bloque le REPL ~350 ms — donc le TRANSPORT PC.\n");
        printf("   Les trames emises pendant ce temps sont PERDUES : attendre\n");
        printf("   3 s avant tout releve (`flush reset` ne vide pas la file).\n");
        return 0;
    }

    if (argc == 4 && strcmp(argv[1], "grandeurs") == 0) {
        char *f1 = NULL, *f2 = NULL;
        long idx = strtol(argv[2], &f1, 0);
        long n = strtol(argv[3], &f2, 0);
        if (f1 == argv[2] || *f1 != '\0' || f2 == argv[3] || *f2 != '\0' ||
            idx < 0 || idx >= DN_UI_METRIQUES) {
            printf("usage : widget grandeurs <0..%d> <n>   (n = 0 rend la case a "
                   "son descripteur)\n", DN_UI_METRIQUES - 1);
            /* 🔴 dn4-9 : LES **DEUX** COMPTES ET LES **DEUX** LISTES. Un seul
             *    compte ne peut plus decrire une case depuis que la CASE et le
             *    DETAIL montrent des sous-ensembles differents — et sans les
             *    INDICES, on ne sait pas trancher entre « le mecanisme se
             *    trompe » et « le descripteur dit ca ».
             * ⚠️ `n` de `widget grandeurs` reste le compte de la CASE : il ne
             *    deplace PLUS le detail avec elle (AC6). */
            for (int i = 0; i < DN_UI_METRIQUES; i++) {
                const dn_widget_desc_t *dd = dn_ui_desc_brut(i);
                printf("   %d ", i);
                colonnes(dn_ui_metrique_nom(i), 10);
                printf(" case %d ", dn_ui_case_grandeurs(i));
                widget_indices_imprimer(i);
                printf("  (descripteur %d) · detail %d [0..%d]\n",
                       dd ? dd->n_grandeurs : 0, dn_ui_detail_grandeurs(i),
                       dn_ui_detail_grandeurs(i) - 1);
            }
            printf("🔴 C'est le SEUL moyen de comparer le REPLI pre-autorise\n");
            printf("   (« GPU a trois ») aux trois voies SUR LA MEME DALLE et\n");
            printf("   DANS LE MEME FIRMWARE.\n");
            return 1;
        }
        esp_err_t e = dn_ui_set_case_grandeurs((int)idx, (int)n);
        if (e != ESP_OK) {
            printf("refuse (%s) — RIEN n'a change\n", esp_err_to_name(e));
            return 1;
        }
        printf("« %s » : %d grandeur(s) ", dn_ui_metrique_nom((int)idx),
               dn_ui_case_grandeurs((int)idx));
        widget_indices_imprimer((int)idx);
        printf(" — SCENE RECONSTRUITE\n");
        printf("  « ca ne tient pas » : %u chevauchement(s) · %u trop large(s) "
               "en colonne unique · %u en HAUTEUR\n",
               (unsigned)dn_widget_chevauchements(),
               (unsigned)dn_widget_trop_larges(),
               (unsigned)dn_widget_debordements());
        if (n == 0) {
            printf("  (override RETIRE — la case suit de nouveau son descripteur)\n");
        }
        return 0;
    }

    if (argc == 2 && strcmp(argv[1], "detail") == 0) {
        /* 🔴 LE TEXTE EST COPIE SOUS LE VERROU — revue du 2026-08-19. On
         *    imprimait ici un `const char *` vers le tampon INTERNE du label,
         *    rendu APRES le deverrouillage, pendant que `detail_reparametrer()`
         *    le `lv_realloc` ~~5 fois par seconde~~ en regime.
         * 🔴 CHIFFRE CORRIGE LE 2026-08-24 (dn4-4/AC3), SUR MESURE — ⛔ PAS
         *    EFFACE : 100 trames acceptees ⇒ 100 poussees en 20,5 s, soit
         *    5,0 poussees/s TOUTES METRIQUES, donc **1,0/s par metrique**.
         *    `detail_reparametrer()` ne sert QUE la metrique affichee ⇒ ~1 Hz,
         *    plafond 4 Hz (periode de `tache_lien`, 250 ms).
         * ⚠️ La copie reste NECESSAIRE : a 1 Hz comme a 5 Hz le tampon est
         *    reallouable sous le nez d'un lecteur hors verrou. */
        /* 🔴 dn4-9 : ⛔ PLUS `DN_WIDGET_TXT_MAX * 4 + 64` (= 128 o). Le
         *    producteur en écrit jusqu'à 168 : l'instrument tronquait EN
         *    SILENCE le texte qu'il prétend relire, et aurait accusé un produit
         *    sain. UNE seule définition, dans `dn_ui.h`. */
        char t[DN_UI_DETAIL_TXT_MAX] = {0};
        int w = 0, wp = 0, x = 0, h = 0, hp = 0, y = 0;
        bool resolue = false;
        if (!dn_ui_detail_label(t, sizeof(t), &w, &wp, &x, &h, &hp, &y,
                                &resolue)) {
            printf("le detail n'est PAS affiche (ou le verrou LVGL n'est pas "
                   "pris) — `nav open <idx>` d'abord.\n");
            printf("⛔ Repondre quand meme inventerait une geometrie.\n");
            return 1;
        }
        printf("GRANDE VALEUR du detail — RELUE des objets LVGL :\n");
        printf("  texte    : « %s »\n", t);
        printf("  largeur  : %d px   posee a x = %d\n", w, x);
        /* 🔴 dn4-9 : LA HAUTEUR, ET ELLE MANQUAIT — a QUATRE lignes c'est ELLE
         *    qui deborde, pas la largeur. Un instrument aveugle a une dimension
         *    sur deux donne l'illusion d'etre couvert. */
        printf("  hauteur  : %d px   posee a y = %d   (panneau %d px)\n", h, y,
               hp);
        if (hp > 0 && y >= 0) {
            if (y + h > hp) {
                printf("  ⛔ %d + %d = %d > %d : la DERNIERE LIGNE est CLIPPEE "
                       "de %d px, SANS un mot.\n", y, h, y + h, hp, y + h - hp);
            } else {
                printf("  ✅ %d + %d = %d <= %d : le bloc TIENT en hauteur "
                       "(marge %d px).\n", y, h, y + h, hp, hp - (y + h));
            }
        }
        if (!resolue) {
            /* ⛔ MEME GARDE QUE `detail_reparametrer` (1a31a9d) : sans elle,
             *    `wp = -1` faisait calculer `utile = -1 - 2x` et crier « LE
             *    TEXTE SORT DU PANNEAU » — un faux positif fabrique par
             *    l'instrument. Une garde qui crie au loup ne garde rien. */
            printf("  panneau  : NON RESOLU (parent %d px, x %d)\n", wp, x);
            printf("  ⏳ La scene n'a pas encore ete disposee : ⛔ AUCUN verdict\n");
            printf("     de largeur ici. Relancer apres un cycle d'affichage.\n");
            return 0;
        }
        int utile = wp - 2 * x;
        printf("  panneau  : %d px   ⇒ utile = %d - 2x%d = %d px\n", wp, wp, x,
               utile);
        if (w + x > wp) {
            printf("  🔴 %d + %d = %d > %d : LE TEXTE SORT DU PANNEAU et LVGL le\n",
                   w, x, w + x, wp);
            printf("     CLIPPE sans un mot.\n");
        } else {
            printf("  ✅ %d + %d = %d <= %d : le texte TIENT dans le panneau.\n",
                   w, x, w + x, wp);
            printf("  ⚠️ Si l'oeil voit une troncature malgre ca, la cause n'est\n");
            printf("     PAS la largeur — chercher la HAUTEUR du panneau ou le\n");
            printf("     retour a la ligne du label.\n");
        }
        return 0;
    }

    /*
     * ── dn4-4 / AC9 : `widget jauge [<case>]` — LE RECTANGLE RÉEL, RELU ──────
     *
     * 🔴 IL TRANCHE UN DÉSACCORD PUBLIÉ, ⛔ il ne l'arbitre pas au jugé.
     *    `dn4-2` publie la bande tactile de la jauge `RAM` à `y = 337..347` /
     *    `x = 22..223` — CALCULÉE. La visée du 2026-08-20, cible RENDUE VISIBLE
     *    (`widget piste 0xFF2020`), a produit 9 taps à `y = 350..371` : aucun
     *    dans la bande publiée. Ni l'une ni l'autre n'avait été relue de l'objet.
     * ⇒ Cette commande imprime, côte à côte, LA FORMULE et CE QUE LVGL A POSÉ.
     *   Quand les deux coïncident, c'est la VISÉE qui est en cause ; quand elles
     *   divergent, c'est la formule. ⛔ Aucun autre chiffre ne tranche.
     */
    if ((argc == 2 || argc == 3) && strcmp(argv[1], "jauge") == 0) {
        long idx = 2; /* RAM — la case du desaccord publie */
        if (argc == 3 && (!parse_entier(argv[2], &idx) || idx < 0 ||
                          idx > DN_UI_METRIQUES)) {
            printf("usage : widget jauge [<0..%d>]   (defaut 2 = RAM)\n",
                   DN_UI_METRIQUES);
            return 1;
        }
        int x = 0, y = 0, w = 0, h = 0;
        bool existe = false, resolue = false;
        if (!dn_ui_widget_jauge_rect((int)idx, &x, &y, &w, &h, &existe,
                                     &resolue)) {
            if (!existe) {
                printf("case %ld (%s) : AUCUNE JAUGE construite.\n", idx,
                       dn_ui_metrique_nom((int)idx));
                printf("⛔ Ce n'est pas « 0,0 » : c'est « rien a mesurer ».\n");
                printf("   `widget` dit quelles cases en portent une.\n");
            } else {
                printf("verrou LVGL non pris — ⛔ « pas mesure », pas « zero ».\n");
            }
            return 1;
        }
        printf("JAUGE de la case %ld (%s) — RELUE des coordonnees LVGL :\n", idx,
               dn_ui_metrique_nom((int)idx));
        if (!resolue) {
            printf("  ⏳ GEOMETRIE NON RESOLUE (x=%d y=%d w=%d h=%d).\n", x, y, w,
                   h);
            printf("  ⛔ AUCUN verdict ici : relancer apres un cycle d'affichage.\n");
            return 0;
        }
        printf("  rectangle : x = %d..%d  (%d px)\n", x, x + w - 1, w);
        printf("              y = %d..%d  (%d px)\n", y, y + h - 1, h);
        printf("  ⚠️ bornes INCLUSIVES cote LVGL — le +1 est fait ici.\n");
        /*
         * 🔴 dn4-13 / AC6.4 — LA FORMULE DE CASE EST **REFUSEE** POUR LA DEMO.
         *    `widget jauge 6` vise `s_demo`, qui n'est PAS une case du tableau
         *    de bord : `dn_ui_case_rect(6, ...)` rend la SENTINELLE
         *    `x = -1, y = -1 (0x0)`. La version precedente l'imprimait telle
         *    quelle, puis calculait « ecart : dx = x - (-1) » — un ecart
         *    FABRIQUE contre une sentinelle, DANS LE BLOC DONT TOUT LE PROPOS
         *    EST DE TRANCHER UN DESACCORD DE COORDONNEES.
         * ⛔ Un instrument ne compare pas a une valeur qui veut dire
         *    « je ne sais pas ». Il le DIT.
         */
        if (idx >= DN_UI_METRIQUES) {
            printf("  ── la formule de case : ⛔ SANS OBJET POUR LA DEMO ──\n");
            printf("     `widget jauge %ld` vise `s_demo`, qui n'est PAS une case\n",
                   idx);
            printf("     du tableau de bord : elle n'a AUCUNE origine calculee.\n");
            printf("     ⛔ Aucun « ecart » n'est publie ici — il serait calcule\n");
            printf("        contre la sentinelle -1 de `dn_ui_case_rect()`,\n");
            printf("        c'est-a-dire FABRIQUE.\n");
        } else {
            int case_x = 0, case_y = 0, case_w = 0, case_h = 0;
            dn_ui_case_rect((int)idx, &case_x, &case_y, &case_w, &case_h);
            printf("  ── la MEME bande, telle que la FORMULE la calcule ──\n");
            printf("     case  : x = %d  y = %d  (%dx%d)\n", case_x, case_y,
                   case_w, case_h);
            printf("     ecart : dx = %d px   dy = %d px\n", x - case_x,
                   y - case_y);
        }
        printf("  🔴 C'EST CE RECTANGLE-CI QU'IL FAUT VISER, ⛔ pas un chiffre\n");
        printf("     publie. `widget piste 0xFF2020` le rend VISIBLE, puis\n");
        printf("     `touch trace` compare la visee au tir.\n");
        return 0;
    }

    /*
     * ── dn4-4 / AC4 : `widget courbe` — LA PLACE DONT LA COURBE DISPOSE ──────
     * ⛔ ELLE NE SE CALCULE PAS. `dn4-9` a payé exactement ce piege sur le bloc
     *    de valeurs : son arithmetique avait oublie le `y = 14` du label, et
     *    c'est la CARTE qui l'a corrigee une fois l'instrument capable de voir
     *    la HAUTEUR. Un instrument aveugle a une dimension sur deux donne
     *    l'illusion d'etre couvert.
     */
    if (argc == 2 && strcmp(argv[1], "courbe") == 0) {
        int x = 0, y = 0, w = 0, h = 0, wc = 0, hc = 0;
        bool existe = false, resolue = false;
        if (!dn_ui_detail_courbe_rect(&x, &y, &w, &h, &wc, &hc, &existe,
                                      &resolue)) {
            printf("aucune courbe a mesurer : le detail n'est pas affiche, ou\n");
            printf("le verrou LVGL n'est pas pris. `nav open <idx>` d'abord.\n");
            printf("⛔ Repondre quand meme inventerait une geometrie.\n");
            return 1;
        }
        printf("COURBE du detail « %s » — RELUE des coordonnees LVGL :\n",
               dn_ui_metrique_nom(dn_ui_metrique()));
        if (!resolue) {
            printf("  ⏳ GEOMETRIE NON RESOLUE (x=%d y=%d w=%d h=%d cadre %dx%d).\n",
                   x, y, w, h, wc, hc);
            printf("  ⛔ AUCUN verdict : relancer apres un cycle d'affichage.\n");
            return 0;
        }
        printf("  courbe : x = %d..%d (%d px)   y = %d..%d (%d px)\n", x,
               x + w - 1, w, y, y + h - 1, h);
        printf("  cadre  : %d x %d px\n", wc, hc);
        printf("  ⚠️ bornes INCLUSIVES cote LVGL — le +1 est fait ici.\n");
        /* 🔴 CE QUE LA GARDE A VU, ⛔ PAS CE QUE L'INSTRUMENT RELIT APRES COUP.
         *    C'est toute la difference : l'instrument tourne dans la tache
         *    console, APRES une passe de layout ; la garde tourne DANS
         *    `detail_reparametrer`, juste apres `lv_label_set_text`. */
        {
            uint32_t np = 0, ncris = 0;
            int ghp = 0, ghl = 0, gyl = 0;
            bool gres = false;
            /* 🔴 dn4-13 / AC1.2 — « PAS MESURE » EST UNE TROISIEME REPONSE.
             *    Sans ce booleen, un verrou non pris rendait six zeros, et le
             *    bloc de verdict plus bas les lisait comme « ZERO PASSAGE : la
             *    garde n'est pas ATTEINTE » — un diagnostic FABRIQUE, sur une
             *    garde qui pouvait avoir crie trois fois. */
            bool gcri = false;
            bool gmes = dn_ui_garde_hauteur(&np, &ncris, &ghp, &ghl, &gyl, &gres,
                                            &gcri);
            {
            int a0=0,b0=0,a1=0,b1=0,ns=0; uint32_t c0=0,c1=0;
            bool p0=false, p1=false;
            if (dn_ui_detail_courbe_axes(&a0,&b0,&a1,&b1,&c0,&c1,&ns,&p0,&p1)) {
                printf("  ── les SERIES et leurs PLAGES Y (⛔ pas recalculees) ──\n");
                printf("     series : %d\n", ns);
                /* 🔴 dn4-13 / AC4.3 — « PAS POSE » EST UNE REPONSE, ⛔ pas `0..0`.
                 *    Temoin : boot → `nav open 0` (CPU borne) → `nav open 3`
                 *    AVANT toute trame `net` ⇒ cette ligne ne doit PAS imprimer
                 *    `0 .. 1000` sous le titre RESEAU. */
                if (p0) {
                    printf("     axe PRIMAIRE   : %ld .. %ld (dixiemes) · couleur 0x%06lX\n",
                           (long)a0, (long)b0, (unsigned long)c0);
                } else {
                    printf("     axe PRIMAIRE   : ⛔ PAS POSE (aucun point reel sur"
                           " cette page) · couleur 0x%06lX\n", (unsigned long)c0);
                }
                if (ns == 2) {
                    if (p1) {
                        printf("     axe SECONDAIRE : %ld .. %ld (dixiemes) · couleur 0x%06lX\n",
                               (long)a1, (long)b1, (unsigned long)c1);
                    } else {
                        printf("     axe SECONDAIRE : ⛔ PAS POSE · couleur 0x%06lX\n",
                               (unsigned long)c1);
                    }
                }
                if (ns == 2 && p0 && p1) {
                    if (a0 == a1 && b0 == b1) {
                        printf("     ✅ ECHELLE COMMUNE : les deux axes portent la MEME\n");
                        printf("        plage — decision owner n°5 du 2026-08-24. ⚠️ Le\n");
                        printf("        prix est ACQUIS : la petite serie s'ecrase en\n");
                        printf("        trait plat en bas de boite, et ce n'est PAS un\n");
                        printf("        defaut a corriger.\n");
                    }
                    else {
                        /* 🔴 DEUX AXES AUTO-CALES CENTRENT CHACUN LEUR SERIE. Deux
                         *    series PLATES se retrouvent donc AU MEME ENDROIT dans
                         *    les 92 px — indiscernables MALGRE deux couleurs. */
                        long e0 = (long)b0 - a0, e1 = (long)b1 - a1;
                        printf("     etendue : primaire %ld · secondaire %ld\n", e0, e1);
                        printf("     🔴 DEUX AXES AUTO-CALES CENTRENT CHACUN LEUR SERIE :\n");
                        printf("        si les DEUX sont plates, elles se SUPERPOSENT\n");
                        printf("        dans les 92 px, ⛔ malgre deux couleurs.\n");
                    }
                }
            }
        }
        {
            /* 🔴 dn4-13 / AC5.3 — LE GAIN SE CHIFFRE ICI, ⛔ il ne se raconte pas.
             *    L'invalidation du cadre (460 x 108 px) tournait
             *    INCONDITIONNELLEMENT, jusqu'a 5 fois par seconde, y compris sur
             *    une serie 100 % TROUS. ⚠️ Les deux compteurs sont CUMULATIFS
             *    depuis le dernier `touch reset` : pour mesurer un regime, on
             *    remet a zero, on laisse tourner, on relit. */
            uint32_t ca = 0, cr = 0;
            dn_ui_courbe_compteurs(&ca, &cr);
            printf("  ── le DESSIN sur le chemin chaud (dn4-13 / AC5) ──\n");
            printf("     reparametrages demandes : %lu · REDESSINS reels : %lu\n",
                   (unsigned long)ca, (unsigned long)cr);
            if (ca > 0) {
                printf("     ⇒ %lu %% des demandes N'ONT PRODUIT AUCUN appel LVGL\n",
                       (unsigned long)((ca - cr) * 100u / ca));
            } else {
                printf("     (aucune demande depuis le dernier `touch reset`)\n");
            }
            printf("     ⚠️ CUMULATIFS depuis `touch reset` (⛔ c'est bien LUI qui\n");
            printf("        remet les compteurs UI a zero, ⛔ pas `widget`).\n");
            printf("        regime : remettre a zero, laisser tourner, relire.\n");
        }
        printf("  ── la GARDE DE HAUTEUR, ce qu'ELLE a vu au dernier passage ──\n");
            printf("     passages : %lu   cris : %lu\n", (unsigned long)np,
                   (unsigned long)ncris);
            printf("     geom_resolue = %s · panneau %d · label %d pose a y = %d\n",
                   gres ? "true" : "false", ghp, ghl, gyl);
            if (!gmes) {
                printf("     ⛔ VERROU LVGL NON PRIS — « pas mesure », ⛔ pas\n");
                printf("        « zero passage ». AUCUN verdict ici.\n");
            } else if (np == 0) {
                printf("     🔴 ZERO PASSAGE : la garde n'est pas ATTEINTE.\n");
            } else if (!gres) {
                printf("     🔴 `geom_resolue` FAUX : la garde est atteinte mais\n");
                printf("        elle se COUPE elle-meme.\n");
            } else if (ghl + gyl > ghp && !gcri) {
                printf("     🔴 CONDITION VRAIE ET AUCUN CRI AU DERNIER PASSAGE :\n");
                printf("        la garde est CASSEE.\n");
            } else if (!gcri) {
                printf("     ✅ silence LEGITIME au DERNIER passage : %d + %d = %d <= %d.\n",
                       gyl, ghl, gyl + ghl, ghp);
                if (ncris > 0) {
                    printf("        (elle avait crie %lu fois depuis le dernier\n",
                           (unsigned long)ncris);
                    printf("         `widget detpan` — ⛔ ce total NE TRANCHE PAS)\n");
                }
            } else {
                printf("     ✅ elle a CRIE AU DERNIER PASSAGE — le temoin negatif\n");
                printf("        est concluant (%lu cri(s) sur %lu passage(s)).\n",
                       (unsigned long)ncris, (unsigned long)np);
            }
            /* 🔴 dn4-13 / AC6.1 — LE VERDICT PORTE SUR LE **DERNIER PASSAGE**.
             *    `ncris` est CUMULATIF : apres un retour au produit il faisait
             *    imprimer « ✅ elle a CRIE » sur une garde MUETTE, et il rendait
             *    la branche « la garde est CASSEE » INJOIGNABLE des le premier
             *    cri. Il reste PUBLIE (il dit combien de fois), ⛔ il ne tranche
             *    plus. Et `widget detpan` remet les compteurs a zero : c'est ce
             *    qui rend le temoin negatif REJOUABLE dans la seance. */
        }
        /* 🔴 L'INVARIANT DU TEMPLATE, VERIFIE ET NON RECITE. Le bas du cadre est
         *    a 370 depuis dn4-6 (205+165) puis dn4-9 (262+108), et le panneau du
         *    bas est a 385. `dn_ui.c` demande de LE VERIFIER a chaque fois qu'on
         *    touche ces deux nombres — voila l'instrument qui le fait. */
        {
            int bas_cadre = 262 + hc;
            printf("  ── l'invariant du template ──\n");
            printf("     bas du cadre de courbe : 262 + %d = %d", hc, bas_cadre);
            if (bas_cadre == 370) {
                printf("   ✅ INCHANGE (370)\n");
            } else {
                printf("   🔴 A CHANGE (attendu 370)\n");
                printf("     ⇒ Le DIRE et REECRIRE l'invariant, ⛔ pas le casser\n");
                printf("       en silence. Le panneau du bas est a 385.\n");
            }
            printf("     ecart au panneau du bas (385) : %d px\n",
                   385 - bas_cadre);
        }
        return 0;
    }

    /*
     * ── dn4-4 / AC4.3 : `widget detpan <h>` — LE TEMOIN NEGATIF DE LA GARDE ──
     * 🔴 ⛔ CE N'EST PAS UN REGLAGE. C'est le seul stimulus qui fasse CRIER la
     *    garde de hauteur du detail : au pire cas LIVRE le bloc tient EXACTEMENT
     *    (14 + 140 = 154 <= 154, marge ZERO), donc aucune donnee reelle ne peut
     *    la declencher. « La garde existe » n'est pas « la garde marche ».
     */
    /* ── dn4-4 / AC7 : `widget fond on|off` — LA BORNE HAUTE DE L'OPTION N°2 ── */
    if (argc == 3 && strcmp(argv[1], "fond") == 0) {
        bool on;
        if (!parse_on_off(argv[2], &on)) {
            printf("usage : widget fond on|off   (actuel : %s)\n",
                   dn_ui_fond() ? "on" : "off");
            return 1;
        }
        if (dn_ui_set_fond(on) != ESP_OK) {
            printf("refuse : verrou LVGL non pris — ⛔ RIEN n'a change.\n");
            return 1;
        }
        printf("fond %s — SCENE RECONSTRUITE.\n", on ? "POSE" : "RETIRE");
        printf("🔴 INSTRUMENT DE BISSECTION (AC7), ⛔ PAS UN REGLAGE.\n");
        printf("   En modele SCREENS, `fond_poser()` pose une `lv_image` de\n");
        printf("   480x640 RGB565 (614 400 o) sur CHACUN des deux ecrans, et\n");
        printf("   `lv_screen_load()` invalide tout — alors que LE FOND EST\n");
        printf("   IDENTIQUE d'un ecran a l'autre. « L'option n°2 » du ledger\n");
        printf("   consisterait a ne pas le repayer.\n");
        printf("   ⇒ `off` mesure LE MEILLEUR CAS que cette option pourrait\n");
        printf("     atteindre. Si le meilleur cas ne gagne rien, l'option est\n");
        printf("     MORTE — et elle meurt AVEC SON CHIFFRE.\n");
        printf("⚠️ Protocole : `touch reset` puis `nav ab 20`, dalle non touchee.\n");
        return 0;
    }

    if (argc == 3 && strcmp(argv[1], "detpan") == 0) {
        long h = 0;
        if (!parse_entier(argv[2], &h)) {
            printf("usage : widget detpan <0|40..167>   (actuel : %d px)\n",
                   dn_ui_detail_panh());
            return 1;
        }
        esp_err_t e = dn_ui_set_detail_panh((int)h);
        if (e != ESP_OK) {
            printf("refuse : %s — ⛔ RIEN n'a change.\n", esp_err_to_name(e));
            printf("  `0` rend le panneau a sa valeur de produit (154 px).\n");
            printf("  ⛔ Hors plage, on REFUSE : un ecretage silencieux ferait\n");
            printf("     mesurer une hauteur qu'on n'a pas demandee.\n");
            return 1;
        }
        printf("panneau de valeurs du detail = %d px — SCENE RECONSTRUITE.\n",
               dn_ui_detail_panh());
        printf("🔴 TEMOIN NEGATIF (AC4.3) : ouvrir DISQUE au PIRE CAS\n");
        printf("   (`dn_injecteur.py --jeu pire`, puis `nav open 4`). Le bloc\n");
        printf("   mesure 14 + 140 = 154 px : sous 154, la garde DOIT emettre\n");
        printf("   « le bloc de valeurs DEBORDE EN HAUTEUR ». Si elle se TAIT,\n");
        printf("   c'est LA GARDE qui est cassee, ⛔ pas le stimulus.\n");
        printf("⚠️ `widget detpan 0` remet le produit. Le cadre de courbe (262)\n");
        printf("   et le panneau du bas (385) n'ont PAS bouge : ce stimulus casse\n");
        printf("   l'AJUSTEMENT, ⛔ pas le template.\n");
        printf("🔴 dn4-13 / AC6.5 — LA BORNE HAUTE EST 167 (= 262 - 95), ⛔ plus\n");
        printf("   200. Au-dela, le bloc CHEVAUCHE le cadre de courbe (95 + 200\n");
        printf("   = 295 > 262) — ET LA GARDE NE LE VOIT PAS : elle compare le\n");
        printf("   label a SON panneau, pas le panneau a son voisin. Elle\n");
        printf("   concluait « ✅ silence LEGITIME » sur un ecran CASSE.\n");
        printf("🔴 dn4-13 / AC6.1 — cette commande REMET LES COMPTEURS DE LA GARDE\n");
        printf("   A ZERO. C'est ce qui rend le temoin negatif REJOUABLE : arme\n");
        printf("   ⇒ elle crie · `detpan 0` ⇒ elle se tait ET la console le DIT.\n");
        printf("   Sans ca, un seul cri suffisait a faire annoncer « elle a CRIE »\n");
        printf("   pour le reste de la session.\n");
        return 0;
    }

    if (argc == 3 && strcmp(argv[1], "replacer") == 0) {
        bool on;
        if (!parse_on_off(argv[2], &on)) {
            printf("usage : widget replacer on|off   (actuel : %s)\n",
                   dn_widget_replacer() ? "on" : "off");
            printf("🔴 INSTRUMENT DE BISSECTION DU TRESSAUTEMENT, ⛔ pas un reglage.\n");
            printf("   `off` supprime `valeur_placer()` du chemin de MISE A JOUR :\n");
            printf("   `dn_widget_maj` redevient LIGNE POUR LIGNE celui de dn4-1.\n");
            printf("⛔ Legitime UNIQUEMENT en EMPILE. En cote a cote la colonne\n");
            printf("   droite resterait a la place de la valeur PRECEDENTE.\n");
            return 1;
        }
        dn_widget_set_replacer(on);
        printf("replacer = %s — ⛔ AUCUNE reconstruction : le changement porte sur\n",
               on ? "on" : "off");
        printf("les MISES A JOUR suivantes, pas sur la scene actuelle.\n");
        dn_widget_geom_t g;
        dn_widget_geom(&g);
        if (g.dispo != DN_DISPO_EMPILE && !on) {
            printf("🔴 ATTENTION : la disposition est %s, PAS empilee. `off` va\n",
                   dn_widget_dispo_nom(g.dispo));
            printf("   figer la colonne droite a sa position precedente.\n");
        } else if (on) {
            printf("⚠️ En EMPILE, `on` et `off` doivent etre VISUELLEMENT\n");
            printf("   IDENTIQUES. S'ils ne le sont pas, c'est le resultat.\n");
        }
        return 0;
    }

    if (argc == 3 && strcmp(argv[1], "dispo") == 0) {
        dn_widget_geom_t g;
        dn_widget_geom(&g);
        if (strcmp(argv[2], "empile") == 0) {
            g.dispo = DN_DISPO_EMPILE;
        } else if (strcmp(argv[2], "cote") == 0) {
            g.dispo = DN_DISPO_COTE;
        } else if (strcmp(argv[2], "mixte") == 0) {
            g.dispo = DN_DISPO_MIXTE;
        } else {
            printf("usage : widget dispo empile|cote|mixte   (actuelle : %s)\n",
                   dn_widget_dispo_nom(g.dispo));
            printf("⛔ EMPILE est et reste LE DEFAUT tant que rien ne l'a battu\n");
            printf("   SUR LA DALLE (addendum §1).\n");
            return 1;
        }
        esp_err_t e = dn_ui_set_widget_geom(&g);
        if (e != ESP_OK) {
            printf("refuse (%s) — RIEN n'a change\n", esp_err_to_name(e));
            return 1;
        }
        printf("disposition = %s — SCENE RECONSTRUITE\n",
               dn_widget_dispo_nom(g.dispo));
        printf("⚠️ `widget largeur` MESURE si les couples tiennent. Un texte trop\n");
        printf("   large ne se voit PAS comme une erreur.\n");
        return 0;
    }

    if (argc == 3 && strcmp(argv[1], "entete") == 0) {
        dn_widget_geom_t g;
        dn_widget_geom(&g);
        if (strcmp(argv[2], "normal") == 0) {
            g.entete = DN_ENTETE_NORMAL;
        } else if (strcmp(argv[2], "compact") == 0) {
            g.entete = DN_ENTETE_COMPACT;
        } else {
            printf("usage : widget entete normal|compact   (actuel : %s)\n",
                   dn_widget_entete_nom(g.entete));
            printf("🔴 COMPACT change les SIX cases et l'icone est le SEUL endroit\n");
            printf("   ou le champ `couleur` du descripteur est EXERCE.\n");
            printf("   ⇒ DECISION OWNER (AC3 / X7), pas un reglage de dev.\n");
            return 1;
        }
        esp_err_t e = dn_ui_set_widget_geom(&g);
        if (e != ESP_OK) {
            printf("refuse (%s) — RIEN n'a change\n", esp_err_to_name(e));
            return 1;
        }
        printf("en-tete = %s — SCENE RECONSTRUITE\n", dn_widget_entete_nom(g.entete));
        printf("⚠️ Le bas de l'en-tete passe a %d px. `widget val <y> <pas>` doit "
               "suivre :\n",
               g.entete == DN_ENTETE_COMPACT ? 26 : 43);
        printf("   le laisser a %d laisserait %d px de garde au lieu de 5.\n",
               g.val_y, g.val_y - (g.entete == DN_ENTETE_COMPACT ? 26 : 43));
        return 0;
    }

    if (argc == 4 && strcmp(argv[1], "val") == 0) {
        dn_widget_geom_t g;
        dn_widget_geom(&g);
        char *f1 = NULL, *f2 = NULL;
        long y = strtol(argv[2], &f1, 0);
        long pas = strtol(argv[3], &f2, 0);
        if (f1 == argv[2] || *f1 != '\0' || f2 == argv[3] || *f2 != '\0') {
            printf("usage : widget val <y> <pas>   (actuels : %d %d)\n", g.val_y,
                   g.val_pas);
            return 1;
        }
        /* 🔴 LA PLAGE EST TESTEE SUR LE `long`, **AVANT** LA TRONCATURE —
         *    revue de code du 2026-08-19. `(int16_t)y` d'abord, validation
         *    ensuite : `widget val 65572 40` devenait `65572 & 0xFFFF = 36`,
         *    que `dn_ui_geom_valider` (14..200) ACCEPTAIT, et la console
         *    imprimait « val_y = 36 — SCENE RECONSTRUITE » comme si c'etait ce
         *    qui avait ete demande. ⛔ C'est mot pour mot le defaut que
         *    `bounce_px_refus()` vient de fermer : un reglage REFUSE est une
         *    gene, un reglage ACCEPTE qui applique autre chose est un defaut. */
        if (y < INT16_MIN || y > INT16_MAX || pas < INT16_MIN || pas > INT16_MAX) {
            printf("refuse : %ld / %ld hors de la plage d'un int16 — RIEN n'a "
                   "change.\n", y, pas);
            printf("⛔ Tronquer d'abord et valider ensuite appliquerait une AUTRE\n");
            printf("   valeur que celle demandee, sans le dire.\n");
            return 1;
        }
        g.val_y = (int16_t)y;
        g.val_pas = (int16_t)pas;
        esp_err_t e = dn_ui_set_widget_geom(&g);
        if (e != ESP_OK) {
            printf("refuse (%s) — RIEN n'a change\n", esp_err_to_name(e));
            return 1;
        }
        int lh = (int)lv_font_get_line_height(g.font_val ? g.font_val
                                                         : &dn_font_28);
        int ch = 0;
        dn_ui_case_dim(NULL, &ch);
        printf("val_y = %d · val_pas = %d — SCENE RECONSTRUITE\n", g.val_y,
               g.val_pas);
        printf("  interligne = %d - %d = %d px", g.val_pas, lh, g.val_pas - lh);
        if (g.val_pas - lh < 5) {
            printf("   🔴 SOUS LE CRITERE ECRIT DE D12 (>= 5 px)");
        }
        printf("\n  garde sous l'en-tete = %d - %d = %d px\n", g.val_y,
               g.entete == DN_ENTETE_COMPACT ? 26 : 43,
               g.val_y - (g.entete == DN_ENTETE_COMPACT ? 26 : 43));
        printf("  4 grandeurs empilees : y_bas = %d + 4 x %d = %d (case %d)%s\n",
               g.val_y, g.val_pas, g.val_y + 4 * g.val_pas, ch,
               g.val_y + 4 * g.val_pas > ch ? "  🔴 DEBORDE" : "");
        return 0;
    }

    if (argc == 3 && strcmp(argv[1], "police") == 0) {
        dn_widget_geom_t g;
        dn_widget_geom(&g);
        if (strcmp(argv[2], "28") == 0) {
            g.font_val = &dn_font_28;
        } else if (strcmp(argv[2], "14") == 0) {
            g.font_val = &dn_font_14;
        } else {
            printf("usage : widget police 14|28   (actuelle : line_height %d)\n",
                   (int)lv_font_get_line_height(g.font_val));
            printf("⚠️ IL N'Y A QUE DEUX POLICES EMBARQUEES. La voie (b) vise ~22,\n");
            printf("   qui EXIGE une regeneration (`tools/gen_font_dn.py`, npm +\n");
            printf("   reseau, ~19 Ko EXTRAPOLES — a confirmer PAR UN BUILD).\n");
            printf("⛔ Ne pas conclure sur (b) depuis la police 14.\n");
            return 1;
        }
        esp_err_t e = dn_ui_set_widget_geom(&g);
        if (e != ESP_OK) {
            printf("refuse (%s) — RIEN n'a change\n", esp_err_to_name(e));
            return 1;
        }
        printf("police des valeurs : line_height %d — SCENE RECONSTRUITE\n",
               (int)lv_font_get_line_height(g.font_val));
        return 0;
    }

    if (argc == 4 && strcmp(argv[1], "grille") == 0) {
        char *f1 = NULL, *f2 = NULL;
        long bh = strtol(argv[2], &f1, 0);
        long mh = strtol(argv[3], &f2, 0);
        if (f1 == argv[2] || *f1 != '\0' || f2 == argv[3] || *f2 != '\0') {
            int b = 0, m = 0, gh = 0, ch = 0;
            dn_ui_geom_bandes(&b, &m, &gh, &ch);
            printf("usage : widget grille <barre_h> <menu_h>   (actuels : %d %d)\n",
                   b, m);
            printf("  70 60 = l'etat des lieux (case 156)\n");
            printf("  60 51 = D12                (case 163)\n");
            printf("  60  0 = voie (a), MENU supprime (case 180)\n");
            printf("⚠️ Bornes RELUES du contenu : barre >= 53 (heure dn_font_28 a\n");
            printf("   y=18, boite 18..53), menu >= 49 (dn_font_28 a y=14) ou 0.\n");
            return 1;
        }
        esp_err_t e = dn_ui_set_bandes((int)bh, (int)mh);
        if (e != ESP_OK) {
            printf("refuse (%s) — RIEN n'a change\n", esp_err_to_name(e));
            return 1;
        }
        int b = 0, m = 0, gh = 0, ch = 0, cw = 0;
        dn_ui_geom_bandes(&b, &m, &gh, &ch);
        dn_ui_case_dim(&cw, NULL);
        printf("barre %d · menu %d · grille %d · case %dx%d — SCENE RECONSTRUITE\n",
               b, m, gh, cw, ch);
        printf("🔴 TOUTE COORDONNEE TACTILE PUBLIEE EST DESORMAIS PERIMEE :\n");
        printf("   VENTILOS y=506..516 (dn3-2), bande de jauge y=340..350 (dn4-1).\n");
        printf("   ⇒ recalculer ET controler la formule contre un releve deja\n");
        printf("     publie AVANT de faire viser quoi que ce soit (AC11).\n");
        printf("⚠️ surface d'une case : %d px (etait 35 100 a 156)\n", cw * ch);
        return 0;
    }

    /*
     * ════════════════════════════════════════════════════════════════════════
     * dn4-6 / AC5 — LA LARGEUR EST MESUREE, PAS ESTIMEE
     * ════════════════════════════════════════════════════════════════════════
     * ⛔ JAMAIS UN PRODUIT `nb_caracteres x largeur_moyenne`. C'est cette
     *    extrapolation (~15,8 px/car.) qui a servi a ECARTER le cote a cote en
     *    dn3-1 : « a 28 px, 25,5 °C mesure ~110 px et 52,4 % ~95 px : 205 px
     *    pour 201 utiles ». Si elle est fausse, c'est une decision qui reposait
     *    sur du vent. On la CONFRONTE.
     * ⚠️ La largeur est relue de `lv_text_get_size()` — la POLICE REELLEMENT
     *    LIEE, kerning compris.
     */
    if (argc == 3 && strcmp(argv[1], "largeur") == 0 &&
        strcmp(argv[2], "reset") == 0) {
        /* ⚠️ AVANT la mesure d'une chaine libre : sinon « reset » serait MESURE
         *    comme un texte et le compteur ne bougerait jamais — une commande
         *    qui a l'air de marcher et ne fait rien. */
        dn_widget_chevauchements_reset();
        dn_widget_debordements_reset();
        dn_widget_trop_larges_reset();
        printf("compteurs remis a 0 : chevauchement (cote a cote), debordement\n");
        printf("(hauteur) ET trop-large (colonne unique — le trou que le cote a\n");
        printf("cote cachait, revue 2026-08-19)\n");
        return 0;
    }
    if ((argc == 2 || argc == 3) && strcmp(argv[1], "largeur") == 0) {
        dn_widget_geom_t g;
        dn_widget_geom(&g);
        int cw = 0;
        dn_ui_case_dim(&cw, NULL); /* ⛔ RELUE, jamais recitee */
        int utile = dn_widget_largeur_utile(cw);
        int gout = dn_widget_gouttiere();

        if (argc == 3) {
            /* Mesure d'UNE chaine donnee — pour que l'operateur puisse poser sa
             * propre question sans recompiler. */
            int w = dn_widget_largeur(argv[2], g.font_val);
            printf("« %s » = %d px   (utile %d, gouttiere %d)\n", argv[2], w,
                   utile, gout);
            return 0;
        }

        printf("LARGEURS RELUES DE LVGL — police line_height %d, case %d px,\n",
               (int)lv_font_get_line_height(g.font_val), cw);
        printf("utile = %d - 2x12 = %d px · gouttiere minimale = %d px\n\n", cw,
               utile, gout);

        /* 🔴 LE TEMOIN HISTORIQUE D'ABORD : c'est LUI qui a ecarte le cote a
         *    cote, et c'est LUI qu'il faut confronter. */
        {
            const char *a = "25,5 \xC2\xB0" "C";
            const char *b = "52,4 %";
            int wa = dn_widget_largeur(a, g.font_val);
            int wb = dn_widget_largeur(b, g.font_val);
            printf("TEMOIN dn3-1 (dn_widget.c:19-29) — l'estimation qui a ECARTE\n");
            printf("le cote a cote :\n");
            printf("  estime  « %s » ~110 px + « %s » ~95 px = 205 px\n", a, b);
            printf("  MESURE  « %s »  %3d px + « %s »  %3d px = %d px\n", a, wa, b,
                   wb, wa + wb);
            /* 🔴 DEUX PROPOSITIONS, DEUX VERDICTS — REVUE DU 2026-08-19.
             *    Cette ligne testait « le couple tient-il ? » et annonçait
             *    « l'estimation etait fausse » : une estimation haute de 10 %
             *    qui n'aurait pas changé la conclusion aurait été proclamee
             *    « CONFIRMEE ». Sur l'instrument dont §18.2 tire la refutation
             *    de (c), c'est exactement le genre de raccourci qui fait
             *    conclure juste pour une raison fausse. */
            int ecart = (wa + wb) - 205;
            printf("  ecart %+d px  ⇒  l'ESTIMATION est %s\n", ecart,
                   (ecart > 5 || ecart < -5)
                       ? "FAUSSE (plus de 5 px)"
                       : "EXACTE a 5 px pres");
            printf("  et le COUPLE, lui, %s (%d + %d = %d <= %d ?)\n",
                   (wa + wb + gout) <= utile ? "🔴 TIENT" : "NE TIENT PAS",
                   wa + wb, gout, wa + wb + gout, utile);
            printf("  ⛔ Les deux questions sont DISTINCTES : dn3-1 s'est trompee\n");
            printf("     d'arithmetique ET a conclu juste — sur le PIRE CAS, pas\n");
            printf("     sur ce couple-ci.\n");
        }

        printf("\nPIRE CAS DE CHAQUE COUPLE (AC5) — « tient » = a + b + %d <= %d :\n",
               gout, utile);
        static const struct {
            const char *quoi;
            const char *a;
            const char *b;
        } k_couples[] = {
            {"CPU  G0+G1 plausible", "100,0 %", "5,7 GHz"},
            {"CPU  G0+G1 grammatical", "100,0 %", "100,0 GHz"},
            {"CPU  G2 seule", "c.max 100,0 %", NULL},
            {"GPU  G0+G1 plausible", "100,0 %", "95,0 \xC2\xB0" "C"},
            {"GPU  G0+G1 grammatical", "100,0 %", "150,0 \xC2\xB0" "C"},
            {"GPU  G2+G3 dixiemes", "350,0 W", "3000,0 tr/min"},
            {"GPU  G2+G3 ENTIERS (AC9)", "350 W", "3000 tr/min"},
            {"GPU  G2+G3 entiers + rpm", "350 W", "3000 rpm"},
            {"GPU  G2+G3 mesures reels", "53 W", "604 tr/min"},
            {"AMB  G0+G1 plausible", "-12,3 \xC2\xB0" "C", "100,0 %"},
            /* ⚠️ LES DEUX ECHELLES, ET C'EST LE CONSTAT OWNER DU 2026-08-19 :
             *    « Mb/s » au pire cas DEBORDE (202 px pour 201 utiles), et
             *    c'est pour ca que RESEAU bascule en « Gb/s » au-dela de
             *    1000,0 Mb/s. Les deux lignes sont la pour que la bascule se
             *    JUSTIFIE par un chiffre, pas par une preference. */
            {"NET  Mb/s AVANT bascule", LV_SYMBOL_DOWN " 999,9 Mb/s",
             LV_SYMBOL_UP " 999,9 Mb/s"},
            {"NET  Gb/s APRES bascule", LV_SYMBOL_DOWN " 100,0 Gb/s",
             LV_SYMBOL_UP " 100,0 Gb/s"},
            {"NET  Mb/s SANS bascule (avant)", LV_SYMBOL_DOWN " 99999,9 Mb/s",
             NULL},
        };
        for (size_t i = 0; i < sizeof(k_couples) / sizeof(k_couples[0]); i++) {
            int wa = dn_widget_largeur(k_couples[i].a, g.font_val);
            int wb = k_couples[i].b ? dn_widget_largeur(k_couples[i].b, g.font_val)
                                    : 0;
            int tot = wa + wb + (k_couples[i].b ? gout : 0);
            printf("  ");
            colonnes(k_couples[i].quoi, 26);
            printf(" %3d + %3d + %2d = %3d  %s\n", wa, wb,
                   k_couples[i].b ? gout : 0, tot,
                   tot <= utile ? "OK" : "🔴 NE TIENT PAS");
        }
        printf("\n⛔ « Rien n'a plante » n'est PAS « ca tient » : LVGL clippe au\n");
        printf("   parent SANS un mot. Chevauchements DETECTES a ce jour : %u\n",
               (unsigned)dn_widget_chevauchements());
        printf("   (`widget largeur reset` remet le compteur a zero)\n");
        return 0;
    }
    if (argc == 3 && strcmp(argv[1], "piste") == 0) {
        char *fin = NULL;
        long v = strtol(argv[2], &fin, 0);   /* accepte 0x… et le décimal */
        if (fin == argv[2] || *fin != '\0' || v < 0 || v > 0xFFFFFF) {
            printf("usage : widget piste <0xRRGGBB>   (actuelle : 0x%06X)\n",
                   (unsigned)dn_widget_piste());
            printf("   la PISTE est le fond de la jauge, la part NON remplie.\n");
            printf("   ⚠️ le code n'a JAMAIS pose de vert : 0x203040 (l'origine)\n");
            printf("      est un bleu-gris FONCE. Ce qui se voit verdatre est le\n");
            printf("      PCB du fond, par contraste simultane.\n");
            return 1;
        }
        esp_err_t err = dn_ui_set_piste((uint32_t)v);
        if (err == ESP_ERR_TIMEOUT) {
            printf("verrou LVGL non pris — RIEN n'a change (reessayer)\n");
            return 1;
        }
        printf("piste de jauge = 0x%06X — SCENE RECONSTRUITE\n", (unsigned)v);
        printf("⚠️ seule RAM porte une jauge aujourd'hui : c'est la seule case ou\n");
        printf("   le changement se voit.\n");
        printf("⚠️ la reconstruction a retire le stimulus `anim` et la demo.\n");
        printf("⛔ dn3-3 refait l'identite visuelle et rejouera cet arbitrage :\n");
        printf("   ceci n'est PAS la passe de palette.\n");
        return 0;
    }
    if (argc == 4 && strcmp(argv[1], "icone") == 0) {
        char *fin = NULL;
        long idx = strtol(argv[2], &fin, 0);
        bool ok_idx = (fin != argv[2] && *fin == '\0');
        long n = strtol(argv[3], &fin, 0);
        /* ⚠️ `fin == argv[i]` : la CHAÎNE VIDE passait (revue 2026-08-18).
         *    `!fin` est toujours faux — `strtol` renseigne TOUJOURS `endptr` —
         *    et pour "" l'endptr vaut nptr avec `*fin == '\0'`. `widget icone ""`
         *    basculait donc le glyphe et reconstruisait la scène. La convention
         *    du fichier est celle-ci (`:94`, `:120`, `:2920`). */
        if (!ok_idx || fin == argv[3] || *fin != '\0') {
            printf("usage : widget icone <case 0..%d> <glyphe 0..%d>\n",
                   DN_UI_METRIQUES - 1, dn_ui_icones_alt_n() - 1);
            for (int i = 0; i < dn_ui_icones_alt_n(); i++) {
                printf("   %d = %s\n", i, dn_ui_icone_alt_nom(i));
            }
            printf("⚠️ `fan` (0xF863) est ABSENT du FontAwesome du depot —\n");
            printf("   VERIFIE en le convertissant seul, pas deduit d'une table.\n");
            printf("   Il est arrive en FontAwesome 5.11, le .woff est anterieur.\n");
            printf("   (les 4 premiers glyphes sont ses substituts, gardes : les\n");
            printf("    retirer changerait l'union -r de 68 a 65 — vraie regen.)\n");
            return 1;
        }
        /* 🔴 UN ÉCHEC DE VERROU N'EST PAS UNE ERREUR D'ARGUMENT (revue
         *    2026-08-18) : les deux tombaient dans la même branche, et
         *    l'opérateur lisait « usage : widget icone <0..3> » pour une
         *    commande correctement tapée dont le seul tort était que LVGL était
         *    occupé. Les sous-commandes voisines distinguent déjà les deux. */
        esp_err_t err = dn_ui_set_icone_alt((int)idx, (int)n);
        if (err == ESP_ERR_TIMEOUT) {
            printf("verrou LVGL non pris — RIEN n'a change (reessayer)\n");
            return 1;
        }
        if (err != ESP_OK) {
            printf("index hors plage : widget icone <case 0..%d> <glyphe 0..%d>\n",
                   DN_UI_METRIQUES - 1, dn_ui_icones_alt_n() - 1);
            return 1;
        }
        printf("icone de la case %d (%s) = %s — SCENE RECONSTRUITE\n",
               (int)idx, dn_ui_metrique_nom((int)idx),
               dn_ui_icone_alt_nom((int)n));
        printf("⚠️ la reconstruction a retire le stimulus `anim` et la demo.\n");
        return 0;
    }
    if (argc == 3 && strcmp(argv[1], "pousser") == 0) {
        char *fin = NULL;
        long idx = strtol(argv[2], &fin, 0);
        if (fin == argv[2] || *fin != '\0' || idx < 0 ||
            idx >= DN_UI_METRIQUES) {
            printf("usage : widget pousser <0..%d>\n", DN_UI_METRIQUES - 1);
            return 1;
        }
        /* 🔴 L'AVERTISSEMENT EST SUR LE CHEMIN NOMINAL depuis le 2026-08-18.
         *    Il ne vivait QUE dans la branche d'erreur ci-dessus : celui qui
         *    tape la commande CORRECTEMENT — donc tous ceux qui l'exécutent en
         *    campagne — ne le voyait jamais. Or c'est lui qui gouverne la
         *    validité du constat owner suivant.
         *    ⚠️ Imprimé UNE SEULE FOIS par session : cette commande est appelée
         *    des dizaines de fois de suite, et chaque octet sur le lien série
         *    est du temps pendant lequel une source peut glisser un cycle
         *    parasite dans la fenêtre de mesure. */
        static bool s_pousser_dit;
        if (!s_pousser_dit) {
            s_pousser_dit = true;
            printf("⚠️ `pousser` NE SE RETIRE PAS TOUT SEUL : la case reste SIMULEE\n");
            printf("   jusqu'a ce que sa vraie source reparle. Une case NUE n'a\n");
            printf("   aucune source : elle y resterait.\n");
            printf("   ⇒ `widget oublier <idx>` la rend a son regime naturel (dn3-2,\n");
            printf("     entree de ledger soldee). ⛔ Ne plus rebooter pour ca : un\n");
            printf("     reboot rejoue le boot entier et perd la fenetre de mesure.\n");
            /* ⚠️ DEUX ECRIVAINS SUR LA MEME CASE (revue 2026-08-19). `dn_ui_pc_maj`
             * ne consulte PAS `s_poussee[]` — seul le tick du mock le fait. Avec
             * l'agent en marche (le regime nominal depuis dn4-1), les cinq cases PC
             * sont reecrites en <= 250 ms : la poussee, son badge SIMULE et sa ligne
             * de mesure disparaissent, et le denominateur de cycles de la campagne
             * est pollue par 5 poussees/s etrangeres. Le README le disait pour
             * `pc pousse` ; ni `pousser` ni `rafale` ne le disaient. */
            printf("⚠️ ARRETER L'AGENT PC D'ABORD : sur les 5 cases PC, la poussee\n");
            printf("   est ECRASEE en <= 250 ms par la trame reelle suivante, et le\n");
            printf("   compte de cycles de la campagne est pollue.\n");
            printf("   (avertissement imprime une seule fois par session)\n");
        }
        uint32_t seq = dn_ui_pousser((int)idx);
        if (seq == 0) {
            printf("verrou LVGL non pris — AUCUNE poussee\n");
            return 1;
        }
        /* Sortie MINIMALE : cette commande est appelee des dizaines de fois de
         * suite par le pilote, et chaque octet imprime est du temps passe sur le
         * lien serie — donc du temps pendant lequel le capteur peut glisser un
         * cycle parasite dans la fenetre de mesure. */
        printf("p%u\n", (unsigned)seq);
        return 0;
    }
    /*
     * ── `widget oublier <idx>` — dn3-2, entree de ledger :1019-1023 SOLDEE ───
     * Sa condition (« si dn3-2 en fait un usage courant ») est DECLENCHEE : AC8
     * fait de `pousser` l'instrument central. Sans elle, un constat owner lance
     * apres une campagne verrait des badges « SIMULE » RESIDUELS et pourrait les
     * lire comme une regression.
     */
    if (argc == 3 && strcmp(argv[1], "oublier") == 0) {
        long idx = 0;
        if (!parse_entier(argv[2], &idx) || idx < 0 || idx >= DN_UI_METRIQUES) {
            printf("usage : widget oublier <0..%d>\n", DN_UI_METRIQUES - 1);
            return 1;
        }
        if (dn_ui_oublier((int)idx) != ESP_OK) {
            printf("verrou LVGL non pris — RIEN n'a change\n");
            return 1;
        }
        printf("case %ld (%s) rendue a son REGIME NATUREL : ABSENTE (« -- »).\n",
               idx, dn_ui_metrique_nom((int)idx));
        printf("  · si elle a un mock ARME, il la reprend au prochain tick ;\n");
        printf("  · si elle a une source REELLE, celle-ci la repeindra ;\n");
        printf("  · sinon elle reste « -- », et c'est la VERITE.\n");
        return 0;
    }
    /*
     * ── `widget rafale` — AC8, le cas « toutes dans le MEME cycle » ──────────
     * ⛔ CONTREDIT DELIBEREMENT l'interdit de `pousser` (une poussee par appel).
     *    C'est l'INSTRUMENT qui produit le seul cas que l'extrapolation d'AC8
     *    predit et que le regime reel ne produit jamais.
     */
    if (argc == 2 && strcmp(argv[1], "rafale") == 0) {
        uint32_t n = dn_ui_rafale();
        if (n == 0) {
            printf("verrou LVGL non pris — AUCUNE poussee\n");
            return 1;
        }
        printf("RAFALE : %u cases poussees sous UN SEUL verrou\n", (unsigned)n);
        /* ⚠️ DEUX ECRIVAINS SUR LA MEME CASE (revue 2026-08-19). Le tick du mock
         * respecte `s_poussee[]` ; le chemin PC (`dn_ui_pc_maj`) ne le consulte
         * PAS. Avec l'agent en marche — le regime nominal depuis dn4-1 — les cinq
         * cases PC sont reecrites en <= 250 ms et le denominateur de cycles d'une
         * campagne est pollue par 5 poussees/s etrangeres. */
        printf("⚠️ ARRETER L'AGENT PC D'ABORD : sinon les 5 cases PC sont reecrites\n");
        printf("   en <= 250 ms et le compte de cycles de la campagne est pollue.\n");
        /* 🔴 IL N'Y A PLUS DE VERDICT ICI — DECISION OWNER DU 2026-08-19.
         * `dn_ui_rafale_cycles()` a ete SUPPRIME : il en etait a sa TROISIEME
         * semantique (« cycles intercales », puis « 0 = succes », puis « 1 =
         * succes ») pour un chiffre qui ne pouvait rendre QUE sa valeur de succes.
         * Sous le verrou, le compteur ne bougeait pas ; apres la relache, la boucle
         * d'attente sortait au PREMIER cycle. Les « quatre rejeux, quatre fois 1 »
         * de la seance sont la signature d'un temoin CONSTANT.
         * ⇒ LA FUSION SE PROUVE PAR `flush`, ET PAR LUI SEUL. On le DIT ici plutot
         *   que d'imprimer un verdict que l'instrument ne peut pas rendre. */
        printf("⛔ CETTE COMMANDE NE CONCLUT PAS SEULE. Pour prouver la fusion :\n");
        printf("   `flush` AVANT et APRES ce tir — la fusion est demontree si le\n");
        printf("   delta vaut %u flushes pour UN SEUL cycle (et %u x 35 100 px).\n",
               (unsigned)n, (unsigned)n);
        printf("   C'est la mesure qui porte AC7 regime (c) ; ce tir ne fait que\n");
        printf("   PROVOQUER le cas.\n");
        printf("⚠️ INSTRUMENT, pas un regime : les six sources reelles ne sont PAS\n");
        printf("   synchronisees (liaison ~1 s, capteur 5 s, mocks 14/20/26/34 s,\n");
        printf("   barre a la minute). Le dire en publiant le chiffre.\n");
        return 0;
    }
    /*
     * ── `widget nue <idx> on|off` — W11, le TEMOIN NEGATIF d'AC8 ─────────────
     */
    if (argc == 4 && strcmp(argv[1], "nue") == 0) {
        long idx = 0;
        bool on;
        if (!parse_entier(argv[2], &idx) || idx < 0 || idx >= DN_UI_METRIQUES ||
            !parse_on_off(argv[3], &on)) {
            printf("usage : widget nue <0..%d> on|off\n", DN_UI_METRIQUES - 1);
            return 1;
        }
        bool deja = (dn_ui_nue((int)idx) == on);
        esp_err_t e = dn_ui_nue_set((int)idx, on);
        if (e == ESP_ERR_INVALID_STATE) {
            /* ⚠️ Inatteignable depuis dn3-2 : les SIX cases portent le modele.
             *    Conserve parce qu'une 7e case sans modele le rendrait vivant. */
            printf("case %ld n'a JAMAIS porte le modele — rien a rendre.\n", idx);
            return 1;
        }
        if (e != ESP_OK) {
            printf("verrou LVGL non pris — RIEN n'a change\n");
            return 1;
        }
        printf("case %ld (%s) : forme %s%s\n", idx, dn_ui_metrique_nom((int)idx),
               on ? "NUE" : "WIDGET", deja ? " (INCHANGEE)" : "");
        if (deja) {
            /* 🔴 Correctif de revue (2026-08-18) : `dn_ui_nue_set` sort en
             *    ESP_OK AVANT le verrou quand la forme ne change pas, mais ce
             *    bloc annoncait la reconstruction INCONDITIONNELLEMENT. Deux
             *    `widget nue 2 on` de suite faisaient donc annoncer 307-322 ms
             *    qui n'avaient pas eu lieu — au milieu d'une campagne qui
             *    compte les cycles. */
            printf("⚠️ AUCUNE reconstruction : la case avait DEJA cette forme.\n");
        } else {
            printf("⚠️ La scene a ete RECONSTRUITE (307-322 ms, verrou tenu) : la forme\n");
            printf("   d'une case se decide a la CONSTRUCTION, pas a la mise a jour.\n");
        }
        printf("⚠️ C'est le TEMOIN NEGATIF d'AC8, pas un reglage produit. Il existe\n");
        printf("   pour que la case nue et les six widgets se mesurent DANS LE MEME\n");
        printf("   FIRMWARE — sinon AC8 comparerait deux firmwares.\n");
        return 0;
    }
    /*
     * ── `widget bandes on|off` — W8/AC9, le levier n°2 ──────────────────────
     */
    /*
     * ── `widget bandes on|off` — W8 / AC9, le levier n°2 ─────────────────────
     */
    if (argc == 3 && strcmp(argv[1], "bandes") == 0) {
        bool on;
        if (!parse_on_off(argv[2], &on)) {
            printf("usage : widget bandes on|off\n");
            return 1;
        }
        dn_ui_bandes_set(on);
        int w = 0, h = 0;
        dn_ui_case_dim(&w, &h);
        printf("repeint en BANDES %s\n", dn_ui_bandes() ? "ARME" : "coupe");
        printf("  mecanisme LU dans lv_refr.c:321-328 : LVGL dedoublonne par\n");
        printf("  `lv_area_is_in(nouvelle, sauvegardee)` — il JETTE une aire\n");
        printf("  CONTENUE dans une autre, il ne FUSIONNE jamais. Deux cases\n");
        printf("  d'une meme ligne elargies a 0..%d deviennent identiques.\n",
               DN_LCD_H_RES - 1);
        printf("⚠️ MAIS le draw buffer fait %d x %d px : a %d de large il ne\n",
               DN_LCD_H_RES, dn_ui_draw_lines(), DN_LCD_H_RES);
        printf("   tient que %d lignes, contre %d pour une case.\n",
               dn_ui_draw_lines(), h);
        if (dn_ui_draw_lines() < h) {
            printf("   🔴 %d < %d ⇒ une bande sera rendue en PLUSIEURS passes.\n",
                   dn_ui_draw_lines(), h);
            printf("      Prediction : MEME compte de flushes, +%d px par ligne.\n",
                   DN_LCD_H_RES * h - 2 * w * h);
            printf("      `set lines 160` + `reboot` est la SEULE config ou le\n");
            printf("      levier peut tomber. C'est la mesure qui tranche.\n");
        } else {
            printf("   ✅ %d >= %d ⇒ une bande tient en UNE passe : c'est LA\n",
                   dn_ui_draw_lines(), h);
            printf("      configuration ou le levier peut gagner.\n");
        }
        printf("⚠️ INSTRUMENT d'AC9, pas un reglage produit. Aucune scene n'a ete\n");
        printf("   reconstruite : le drapeau agit sur la PROCHAINE invalidation.\n");
        return 0;
    }
    if (argc == 3 && strcmp(argv[1], "barre") == 0) {
        bool sec;
        if (strcasecmp(argv[2], "1hz") == 0) {
            sec = true;
        } else if (strcasecmp(argv[2], "minute") == 0) {
            sec = false;
        } else {
            printf("usage : widget barre 1hz|minute\n");
            return 1;
        }
        dn_ui_barre_secondes_set(sec);
        printf("cadence de la barre : %s\n",
               dn_ui_barre_secondes() ? "HH:MM:SS — invalidee CHAQUE SECONDE"
                                      : "HH:MM — invalidee au CHANGEMENT DE MINUTE");
        printf("🔴 MESURE (§16.5) : la barre coute 6 334 px par mise a jour,\n");
        printf("   soit 18 %% d'une case (35 100 px) — PAS les 33 600 px que son\n");
        printf("   rectangle 480 x 70 laisse croire. LVGL n'invalide que la zone\n");
        printf("   des LABELS. La premisse « 7e case vivante » etait fausse d'un\n");
        printf("   facteur 5,3, et ce message la recitait pendant l'A/B meme.\n");
        printf("⚠️ La maquette normative (addendum §1) ecrit « 21:46 » : elle\n");
        printf("   n'affiche PAS les secondes. Defaut = minute.\n");
        return 0;
    }
    if (argc == 3 && strcmp(argv[1], "mock") == 0) {
        bool on;
        if (!parse_on_off(argv[2], &on)) {
            printf("usage : widget mock on|off\n");
            return 1;
        }
        /* 🔴 L'ÉCHEC DE VERROU EST DIT (revue 2026-08-18) : `dn_ui_mock_set`
         *    rendait `void` et avalait le timeout, pendant que ce `printf`
         *    annonçait la bascule inconditionnellement — sur un `s_mock_on`
         *    inchangé. Seule des quatre sous-commandes à verrou à mentir. */
        if (dn_ui_mock_set(on) != ESP_OK) {
            printf("verrou LVGL non pris — RIEN n'a change\n");
            return 1;
        }
        /* 🔴 dn4-1 : LA SORTIE ANNONCE QUE C'EST UN INSTRUMENT QU'ON ARME.
         *    Le mock est COUPE PAR DEFAUT depuis dn4-1 (les quatre cases ont des
         *    sources reelles) ; `on` fait donc apparaitre des badges « SIMULE »
         *    sur un dashboard qui n'en porte plus. Quelqu'un qui trouve l'ambre
         *    sans savoir qu'il l'a arme lira une regression. */
        /* ⛔ COMPTE, NE RECITE PAS. C'est le motif que dn4-1 corrige trois fois
         * ailleurs (`widget icone`, `etat_source`, `nom_source`) : une constante
         * la ou une table existe. Ajouter ou retirer un mock faisait mentir cette
         * ligne SANS erreur de compilation. Corrige en revue 2026-08-18. */
        printf("mock %s — les %d cases mockees passent en %s\n",
               on ? "ARME" : "COUPE", dn_ui_mocks_actifs(),
               on ? "SIMULEE" : "ABSENTE (« -- » grise)");
        if (on) {
            printf("⚠️ INSTRUMENT ARME, PAS UN REGLAGE. Il REJOUE la ligne\n");
            printf("   « mock on / groupage on » de §16.1 (la baseline d'AC7 :\n");
            printf("   10,18 %% CPU · 3,47 flush/cycle · 120 756 px/cycle · 6,7 %%).\n");
            printf("   Tant qu'il tourne, les trames reelles de dn_link sont\n");
            printf("   IGNOREES sur ces cases — sinon la ligne serait injouable.\n");
            printf("   ⛔ Le regime nominal de dn4-1 est `off` : ZERO badge SIMULE.\n");
        } else {
            printf("⚠️ une case POUSSEE (`widget pousser 4`) n'est PAS reprise :\n");
            printf("   le tick ne revoque pas un acte delibere de l'operateur.\n");
            printf("   Les cases a source reelle repartent des la prochaine trame.\n");
            /* 🔴 `mock off` A CHANGE DE SENS AVEC dn4-1, ET LE PROTOCOLE §15.5 LE
             * SUPPOSE ENCORE. Jusqu'a dn3-2, « mock isole » voulait dire SILENCE
             * sur les cases. Depuis dn4-1, `off` est le REGIME NOMINAL avec cinq
             * sources reelles qui ecrivent a 1 Hz. C'est le meme piege « deux
             * ecrivains sur la meme case » que §17.3 vient de corriger, deplace
             * du tick de mock vers le chemin d'instrument. (Revue 2026-08-18.) */
            printf("🔴 `mock off` N'EST PLUS UNE CONDITION D'ISOLEMENT depuis\n");
            printf("   dn4-1 : c'est le REGIME NOMINAL, et si l'agent tourne les\n");
            printf("   cinq cases PC sont reecrites a 1 Hz. ⛔ Une campagne AC8\n");
            printf("   (`widget pousser` / `rafale`) exige d'ARRETER L'AGENT :\n");
            printf("   sinon la poussee est ecrasee en <= 250 ms et le denominateur\n");
            printf("   de cycles est pollue par 5 poussees/s qui ne sont pas les\n");
            printf("   siennes. Le protocole de §15.5 disait « mock isole » quand\n");
            printf("   cela suffisait — ce n'est plus le cas.\n");
        }
        return 0;
    }
    if ((argc == 3 || argc == 4) && strcmp(argv[1], "demo") == 0) {
        bool on;
        if (!parse_on_off(argv[2], &on)) {
            printf("usage : widget demo on|off [n]\n");
            printf("   `n` = nombre de grandeurs du descripteur de demo (1..6).\n");
            printf("   ⛔ IL PEUT DEPASSER DN_WIDGET_GRANDEURS_MAX (4), ET C'EST\n");
            printf("      LE POINT : le clamp de dn4-1 n'est ATTEIGNABLE que par\n");
            printf("      un descripteur a n = 5. Aucune case figee ne le fera.\n");
            return 1;
        }
        if (argc == 4) {
            char *fin = NULL;
            long n = strtol(argv[3], &fin, 0);
            if (fin == argv[3] || *fin != '\0' ||
                dn_ui_set_demo_n((int)n) != ESP_OK) {
                printf("n hors bornes (1..6) — RIEN n'a change\n");
                return 1;
            }
        }
        if (dn_ui_demo_set(on) != ESP_OK) {
            printf("verrou LVGL non pris — RIEN n'a change\n");
            return 1;
        }
        printf("7e metrique FICTIVE %s — n = %d grandeur(s) demandee(s).\n",
               on ? "AFFICHEE" : "retiree", dn_ui_demo_n());
        if (on) {
            /* 🔴 LES DEUX TEMOINS D'AC2 SE PROVOQUENT ICI, ET NULLE PART
             *    AILLEURS. Le dire au moment ou l'operateur arme l'instrument
             *    evite qu'il cherche le log au mauvais endroit. */
            /* ⚠️ LES TROIS LIGNES SONT CALCULEES, PLUS RECITEES. Elles
             *    portaient « 156 » EN DUR — juste tant que personne ne touchait
             *    aux bandes, FAUX depuis que D12 est le defaut (163). Un texte
             *    d'aide qui recite une geometrie devenue variable est la meme
             *    faute que « 225x156 = 35 100 px » que dn3-2 a corrigee. */
            dn_widget_geom_t gd;
            dn_widget_geom(&gd);
            int chh = 0;
            dn_ui_case_dim(NULL, &chh);
            /* 🔴 LE NOMBRE DE LIGNES VIENT DE `dn_widget_lignes()`, PAS DE `n`
             *    — revue de code du 2026-08-19. Ces deux lignes multipliaient
             *    `val_pas` par le nombre de GRANDEURS, ce qui n'est vrai qu'en
             *    `EMPILE`. Sous `widget dispo cote`, n=2 fait UNE ligne et n=3
             *    en fait DEUX : les deux verdicts imprimes etaient faux, au
             *    moment precis ou l'operateur arme le temoin. Et le commentaire
             *    trois lignes plus haut se felicitait de CALCULER au lieu de
             *    reciter, pendant que `dn_widget_lignes()` — exporte EXPRES
             *    « pour que la console calcule » — n'etait pas appele. */
            int yb2 = gd.val_y + dn_widget_lignes(gd.dispo, 2) * gd.val_pas;
            int yb3 = gd.val_y + dn_widget_lignes(gd.dispo, 3) * gd.val_pas;
            printf("⚠️ CE QUE CE `n` PROUVE (AC2 de dn4-6), sur la geometrie "
                   "COURANTE (case %d px, disposition %s) :\n", chh,
                   dn_widget_dispo_nom(gd.dispo));
            printf("     n=2  (%d ligne(s))  SECONDAIRE abandonnee si y_bas %d + "
                   "20 > %d : %s\n",
                   dn_widget_lignes(gd.dispo, 2), yb2, chh,
                   (yb2 + 20 > chh) ? "OUI" : "non (elle tient)");
            printf("     n=3  (%d ligne(s))  JAUGE abandonnee si y_bas %d + 6 + "
                   "10 > %d : %s\n",
                   dn_widget_lignes(gd.dispo, 3), yb3, chh,
                   (yb3 + 16 > chh) ? "OUI" : "non (elle tient)");
            printf("     n=5  le CLAMP journalise « 1 PERDUE(S) » (MAX = %d)\n",
                   DN_WIDGET_GRANDEURS_MAX);
            printf("   Chaque abandon est un ESP_LOGW, et `widget` le RELIT des\n");
            printf("   pointeurs — ⛔ pas du descripteur.\n");
            printf("  Elle est produite par le MEME `dn_widget_creer` que les\n");
            printf("  trois autres, depuis un descripteur et RIEN D'AUTRE :\n");
            printf("  aucune ligne de code de dessin n'existe pour elle.\n");
            printf("  Elle est BI-GRANDEURS et n'est ni Ambiance ni Disque —\n");
            printf("  donc la variante D6 n'est pas un cas special deguise.\n");
            printf("⚠️ Elle recouvre des cases : c'est un INSTRUMENT, comme\n");
            printf("   `ui label on`. `widget demo off` la retire.\n");
            printf("⚠️ Une reconstruction de scene (`ui bg`, `nav model`, `widget\n");
            printf("   opa`) la RETIRE et le dit : l'ombre suit la realite.\n");
        }
        return 0;
    }
    if (argc == 3 &&
        (strcmp(argv[1], "opa") == 0 || strcmp(argv[1], "voile") == 0)) {
        char *fin = NULL;
        long v = strtol(argv[2], &fin, 0);
        /* ⚠️ `fin == argv[2]` : la CHAÎNE VIDE passait pour 0 (revue
         *    2026-08-18) ⇒ `widget opa ""` mettait l'opacité des cases à ZÉRO et
         *    reconstruisait la scène en annonçant « 0/255 (0 %) ». `!fin` ne
         *    teste rien : `strtol` renseigne toujours `endptr`. */
        if (fin == argv[2] || *fin != '\0' || v < 0 || v > 255) {
            /* BORNER ET REFUSER, jamais ecreter en silence : la regle du depot
             * (`touch int 30000` refuse au lieu d'annoncer 30 s et d'en scanner
             * 5). Un reglage ecrete rend une mesure etiquetee faux. */
            printf("usage : widget %s <0..255>  (refuse hors bornes, jamais "
                   "ecrete)\n",
                   argv[1]);
            return 1;
        }
        esp_err_t e = (strcmp(argv[1], "opa") == 0)
                          ? dn_ui_set_case_opa((uint8_t)v)
                          : dn_ui_set_voile_opa((uint8_t)v);
        if (e != ESP_OK) {
            printf("verrou LVGL non pris — RIEN n'a change\n");
            return 1;
        }
        printf("opacite %s = %ld/255 (%ld %%) — SCENE RECONSTRUITE\n",
               strcmp(argv[1], "opa") == 0 ? "des CASES" : "du VOILE", v,
               v * 100 / 255);
        printf("⚠️ la reconstruction a RETIRE le stimulus `anim` et la demo,\n");
        printf("   et elle remet la vue au dashboard. Re-armer si besoin.\n");
        /* Valeurs RELUES de lv_color.h:47-53, pas arrondies de tete : 70 % de
         * 255 fait 178,5 et LVGL tronque a 178 ; 50 % fait 127,5 et donne 127.
         * Annoncer 179 et 128 « parce que c'est le pourcentage » serait une
         * etiquette fausse d'un cran — donc une etiquette fausse. */
        printf("⚠️ Reperes : 255 = LV_OPA_COVER (opaque, supprime le re-blit du\n");
        printf("   fond) · 178 = LV_OPA_70 (l'etat des lieux) · 127 = LV_OPA_50.\n");
        return 0;
    }
    if (argc != 1) {
        printf("usage : widget | groupe on|off|union | opa <0..255> | voile <0..255>\n");
        printf("        | piste <0xRRGGBB>  (fond de la jauge)\n");
        printf("        | mock on|off | demo on|off [n] | pousser <idx>\n");
        printf("        | icone <case> <0..%d>  (A/B de glyphe sur une case, W4)\n",
               dn_ui_icones_alt_n() - 1);
        /* ⚠️ AJOUTE PAR LA REVUE DU 2026-08-19 : les dix sous-commandes de dn4-6
         *    n'etaient NI ici, NI dans `DN_CMD`, NI dans la liste de secours du
         *    rejet — tout l'outillage de la story etait donc introuvable depuis
         *    la carte, alors qu'AC14 exige `aide` ET le README dans le meme
         *    geste (dn2-1 avait oublie `capteurs`, exactement pareil). */
        printf("      dn4-6 — la geometrie et la forme, COMMUTABLES A CHAUD :\n");
        printf("        | voie defaut|avantd12|a|b|c|c2|repli   ⚠️ RECONSTRUIT\n");
        printf("        | grandeurs <case> <n>                  ⚠️ RECONSTRUIT\n");
        printf("        | dispo empile|cote|mixte               ⚠️ RECONSTRUIT\n");
        printf("        | entete normal|compact                 ⚠️ RECONSTRUIT\n");
        printf("        | val <y> <pas>                         ⚠️ RECONSTRUIT\n");
        printf("        | police 14|28                          ⚠️ RECONSTRUIT\n");
        printf("        | grille <barre> <menu>                 ⚠️ RECONSTRUIT\n");
        printf("      dn4-6 — les instruments (ne reconstruisent PAS) :\n");
        printf("        | largeur [<texte>|reset] | detail | replacer on|off\n"
           "        | jauge [<case>]   (dn4-4/AC9 : le rectangle REEL de la barre)\n"
           "        | courbe           (dn4-4/AC4 : la place REELLE de la courbe)\n"
           "        | detpan <0|40..167>  (dn4-4/AC4.3 : TEMOIN NEGATIF de la garde)\n"
           "        | fond on|off      (dn4-4/AC7 : borne haute de « l'option n°2 »)\n");
        return 1;
    }

    /* 🔴 COMPTÉ, PAS RÉCITÉ (revue 2026-08-18). Cette ligne disait « 3 cases sur
     *    6 » en dur, TROIS lignes sous le docblock qui jure que tout est relu de
     *    l'état réel — et le compte est disponible par la fonction que la boucle
     *    ci-dessous appelle déjà. Ajouter la ligne de `k_desc[]` que ce module
     *    présente comme LE point d'ajout d'une métrique faisait mentir la
     *    première ligne de son propre instrument. */
    int n_widgets = 0;
    for (int i = 0; i < DN_UI_METRIQUES; i++) {
        if (dn_ui_est_widget(i)) {
            n_widgets++;
        }
    }
    printf("modele de widget (dn3-1) — %d cases sur %d le portent\n", n_widgets,
           DN_UI_METRIQUES);
    {
        /* 🔴 dn4-6 / AC4 : LA GEOMETRIE COURANTE EST RELUE, ⛔ JAMAIS RECITEE.
         *    La table ci-dessous imprimait « 156 px » EN DUR — un chiffre juste
         *    tant que personne ne touchait aux bandes, et FAUX a la premiere
         *    bascule de voie. C'est exactement le motif que dn4-1 corrige trois
         *    fois ailleurs. */
        dn_widget_geom_t g;
        dn_widget_geom(&g);
        int bh = 0, mh = 0, gh = 0, ch = 0;
        dn_ui_geom_bandes(&bh, &mh, &gh, &ch);
        int cw0 = 0;
        dn_ui_case_dim(&cw0, NULL);
        printf("geometrie    : barre %d · menu %d · grille %d · case %dx%d\n", bh,
               mh, gh, cw0, ch);
        printf("               val_y %d · val_pas %d (interligne %d px) · %s · %s\n",
               g.val_y, g.val_pas, g.val_pas - (int)lv_font_get_line_height(g.font_val),
               dn_widget_dispo_nom(g.dispo), dn_widget_entete_nom(g.entete));
        printf("               « ca ne tient pas » DETECTES : %u en LARGEUR "
               "(chevauchement) · %u en HAUTEUR (debordement)\n",
               (unsigned)dn_widget_chevauchements(),
               (unsigned)dn_widget_debordements());
        if (dn_widget_chevauchements() || dn_widget_debordements()) {
            printf("               🔴 LVGL CLIPPE SANS UN MOT : « rien n'a plante »\n");
            printf("                  n'est pas « ca tient ». Voir les ESP_LOGW —\n");
            printf("                  ils nomment la case et le nombre de px.\n");
            printf("               ⚠️ LARGEUR et HAUTEUR sont comptees A PART : elles\n");
            printf("                  ne se corrigent pas par le meme levier.\n");
        }
    }
    /* 🔴 CORRIGÉ LE 2026-08-23 : cette ligne ne connaissait que DEUX modes et
     *    annonçait « FINE » pendant qu'`union` tournait — relevé par l'owner sur
     *    la sortie même du test. C'est la RÉCIDIVE EXACTE du défaut que dn3-2
     *    AC9 a payé (la doc et le code qui disent deux valeurs différentes),
     *    commise ici en ajoutant un troisième mode sans toucher à la source de
     *    vérité. ⇒ Elle lit désormais LES DEUX drapeaux, dans l'ordre
     *    d'exclusivité que `dn_ui_set_groupe_union()` garantit. */
    printf("invalidation : %s\n",
           dn_widget_groupe_union()
               ? "UNION (1 zone par widget, bornee aux VALEURS)"
               : dn_widget_groupage() ? "GROUPEE (1 zone englobante par widget)"
                                      : "FINE (N zones, LVGL decide)");
    printf("opacite      : cases %u/255 · voile %u/255\n", dn_widget_opa(),
           dn_ui_voile_opa());
    printf("piste jauge  : 0x%06X   (le fond de la barre, part NON remplie —\n",
           (unsigned)dn_widget_piste());
    printf("               `widget piste <0xRRGGBB>`, arbitrage a l'oeil)\n");
    printf("demo 7e metrique : %s\n", dn_ui_demo_on() ? "AFFICHEE" : "retiree");

    /* 🔴 dn3-2 : QUATRE mocks, donc QUATRE formes imprimées. L'ancienne version
     * n'en décrivait qu'une (VENTILOS) — la garder aurait décrit trois cases
     * par les chiffres d'une quatrieme, ce qui est une etiquette qui ment. */
    printf("mock : %s — les formes sont RELUES de la table qui les pilote\n",
           dn_ui_mock_on() ? "ARME" : "COUPE");
    for (int i = 0; i < DN_UI_METRIQUES; i++) {
        int mn = 0, mx = 0, per = 0;
        if (!dn_ui_mock_forme(i, &mn, &mx, &per)) {
            continue;
        }
        /* ⚠️ `colonnes()` IMPRIME, elle ne rend rien — `%-9s` compterait en
         * OCTETS et « RÉSEAU » (7 octets pour 6 colonnes) décalerait la sienne. */
        printf("   ");
        colonnes(dn_ui_metrique_nom(i), 9);
        const dn_widget_desc_t *dm = dn_ui_desc(i);
        printf(" rampe TRIANGULAIRE %d -> %d %s · periode %d s · pas 1 s\n", mn,
               mx, (dm && dm->grandeurs[0].unite) ? dm->grandeurs[0].unite : "",
               per);
    }
    printf("   (une valeur qui VARIE : un mock fige serait indiscernable d'un\n");
    printf("    affichage bloque. CPU et AMBIANCE n'ont PAS de mock — elles ont\n");
    printf("    des sources REELLES, et D6 veut que ca se voie.)\n");
    /*
     * 🔴 dn4-1 / AC5 — CE QUE CHAQUE CASE A REELLEMENT CONSTRUIT, RELU DES
     *    POINTEURS LVGL. ⛔ Pas recite du descripteur : c'est TOUT l'objet du
     *    correctif W5. Un descripteur peut DEMANDER une jauge et une secondaire
     *    et n'obtenir que la jauge — la geometrie ne permet pas les deux a deux
     *    grandeurs (y_bas 148 + 20 = 168 > 156). Sans cette lecture, on ne
     *    pourrait le CONSTATER qu'en lisant le source, et c'est exactement
     *    comme ca que le defaut a dormi depuis dn3-1.
     */
    printf("geometrie des cases — RELUE des pointeurs, pas du descripteur :\n");
    printf("        case      n_gr  jauge  secondaire   (demande par le descripteur)\n");
    /* 🔴 LA BOUCLE VA JUSQU'A DN_UI_METRIQUES **INCLUS** : la derniere ligne est
     * le widget de DEMO, et c'est le seul du firmware a demander DEUX grandeurs
     * ET une jauge — donc le seul a pouvoir afficher « secondaire : non ». Sans
     * lui, cette colonne etait constante par construction et l'instrument ne
     * pouvait pas voir le cas qu'il pretend prouver (revue 2026-08-18).
     * ⚠️ ET UNE CASE NON CONSTRUITE LE DIT, au lieu d'etre sautee en silence :
     * en modele REBUILD avec la vue detail ouverte, ou apres `ui off`, les six
     * racines sont NULL et la table sortait VIDE sous son en-tete — impossible de
     * distinguer « rien a dire » de « rien de construit ». */
    for (int i = 0; i <= DN_UI_METRIQUES; i++) {
        bool demo = (i == DN_UI_METRIQUES);
        const char *nom = demo ? "DEMO" : dn_ui_metrique_nom(i);
        int ng = 0;
        bool jauge = false, sec = false;
        if (!dn_ui_widget_pointeurs(i, &ng, &jauge, &sec)) {
            printf("   ");
            colonnes(nom, 10);
            printf("  —     —      —           (non dessinee%s)\n",
                   demo ? " — `widget demo on` pour l'armer" : "");
            continue;
        }
        bool nue = (!demo && !dn_ui_case_est_widget(i));
        /* 🔴 LA COLONNE « DEMANDE » LIT LE DESCRIPTEUR BRUT, PAS `dn_ui_desc()`
         * (revue 2026-08-19). `dn_ui_desc()` rend NULL pour une case NUE — c'est
         * l'override W11 — et les deux colonnes retombaient alors sur `0` et sur
         * « pas de jauge ». Sur `widget nue 2 on` (RAM, descripteur n=1 AVEC
         * jauge), la table annoncait donc « (n=0) » sans « jauge demandee » : DEUX
         * CHIFFRES FAUX dans la colonne dont l'en-tete promet de dire ce que LE
         * DESCRIPTEUR demande — sur le chemin le plus actionne d'une campagne AC8.
         * ⚠️ L'override porte sur le RENDU, jamais sur la demande. */
        dn_widget_desc_t dbuf;
        bool a_desc;
        if (demo) {
            a_desc = dn_ui_demo_desc(&dbuf); /* PAR VALEUR — voir `dn_ui.h` */
        } else {
            const dn_widget_desc_t *db = dn_ui_desc_brut(i);
            a_desc = (db != NULL);
            if (a_desc) {
                dbuf = *db;
            }
        }
        printf("   ");
        colonnes(nom, 10);
        printf("  %d     %-5s  %-10s  (n=%d%s)%s\n", ng, jauge ? "OUI" : "non",
               sec ? "OUI" : "non", a_desc ? dbuf.n_grandeurs : 0,
               (a_desc && dbuf.indicateur) ? ", jauge demandee" : "",
               nue ? "  ⚠️ CASE NUE (override W11), pas un abandon" : "");
    }
    {
        /* 🔴 « 156 px » ETAIT ECRIT EN DUR ICI (dn_console.c:3213, releve par le
         *    cadrage de dn4-6). La hauteur de case est desormais un REGLAGE
         *    (voie (a) : 180, D12 : 163) : le chiffre en dur serait devenu FAUX
         *    a la premiere bascule, dans la phrase meme qui explique la regle. */
        int ch = 0;
        dn_ui_case_dim(NULL, &ch);
        printf("   ⚠️ REGLE ECRITE (dn_widget.h) : VALEURS > JAUGE > SECONDAIRE.\n");
        printf("      Quand tout ne tient pas dans les %d px de la case, on\n", ch);
        printf("      abandonne dans CET ordre, et CHAQUE abandon est JOURNALISE\n");
        printf("      (ESP_LOGW). Un abandon silencieux etait le defaut — la\n");
        printf("      jauge l'etait encore jusqu'a dn4-6 (3e occurrence).\n");
    }
    /* ⚠️ L'index de la case est RELU de la table métrique->case, ⛔ pas écrit en
     *    dur : c'est exactement le défaut que dn4-1 corrige trois fois ailleurs. */
    {
        int i_disque = dn_ui_case_de_metrique(DN_LINK_M_DISK);
        printf("icone DISQUE : %s   (W4 — `fan` 0xF863 est ABSENT du .woff ;\n",
               dn_ui_icone_alt_nom(dn_ui_icone_alt(i_disque)));
        printf("               « ? » = celle du descripteur, non commutee)\n");
    }

    printf("\n  idx nom        forme   regime   dessinee  valeur(s)\n");
    for (int i = 0; i < DN_UI_METRIQUES; i++) {
        const dn_widget_desc_t *d = dn_ui_desc(i);
        /* 🔴 `%-10s` REMPLIT EN OCTETS, PAS EN COLONNES D'AFFICHAGE — et c'est
         * EXACTEMENT le défaut que l'en-tête de `dn_console_banner()` explique
         * quelques centaines de lignes plus bas, commis à nouveau ici et attrapé
         * à la première exécution : « RÉSEAU » pèse 7 octets pour 6 colonnes, et
         * sa ligne se décalait d'un caractère vers la gauche. Depuis dn3-1 les
         * libellés sont ACCENTUÉS, donc tout `%-Ns` sur un nom de métrique est
         * faux. On paie donc les colonnes à la main. */
        printf("  %2d  ", i);
        colonnes(dn_ui_metrique_nom(i), 11);
        printf("%-7s ", d ? "WIDGET" : "nue");
        /* ⚠️ ET LE RÉGIME AUSSI passe par `colonnes()` depuis le 2026-08-18 :
         *    il était en `%-8s`, or « RÉELLE » et « SIMULÉE » sont ACCENTUÉS
         *    depuis la même revue — 7 et 8 octets pour 6 et 7 colonnes. Le
         *    défaut que le commentaire ci-dessus décrit, re-commis une ligne
         *    plus bas que sa propre mise en garde. */
        colonnes(dn_val_regime_nom(dn_ui_regime(i)), 9);
        printf("%-9s", dn_ui_case_dessinee(i) ? "oui" : "NON");
        /* 🔴 CONSOMMATEUR DE `dn_ui_case_grandeurs()` — voir la propriété
         *    vérifiable écrite au-dessus de `s_gr_force[]` dans `dn_ui.c`.
         *    Cette ligne lisait `d->n_grandeurs`, c'est-à-dire le descripteur
         *    BRUT : après `widget grandeurs 1 4` la case DESSINAIT 4 valeurs et
         *    la table en imprimait 3 ; après `widget grandeurs 0 1`, l'inverse,
         *    avec deux « -- » inventés. L'instrument qui sert à arbitrer le
         *    repli se désynchronisait du sujet de l'arbitrage (revue 2026-08-19). */
        /* ⚠️ `d == NULL` = case NUE (override W11) : elle n'a qu'un `valeur[0]`,
         *    et lui demander N textes en inventerait N-1 en « -- ». */
        /* 🔴 dn4-9 : LA BOUCLE VA SUR LES **RANGS** ET LIT L'**INDICE** — sans
         *    la traduction, la table imprimerait « c.max » pendant que la case
         *    dessine une °C, c'est-à-dire l'instrument désynchronisé du sujet,
         *    exactement le défaut corrigé ci-dessus sous une autre forme. */
        uint8_t selw[DN_WIDGET_GRANDEURS_MAX] = {0, 1, 2, 3};
        int n = d ? dn_ui_case_indices(i, selw, DN_WIDGET_GRANDEURS_MAX) : 1;
        if (n < 1) {
            n = 1;
        }
        for (int r = 0; r < n; r++) {
            int g = (int)selw[r];
            const char *t = dn_ui_valeur_txt(i, g);
            /* 🔴 L'UNITE VIENT DE LA DEFINITION UNIQUE. Cette ligne relisait
             *    `d->grandeurs[g].unite` et imprimait donc « 100,0 Mb/s » pour
             *    une valeur convertie en Gb/s — fausse d'un FACTEUR MILLE, dans
             *    l'instrument qui sert a verifier. Troisieme copie de la meme
             *    regle ; il n'en reste qu'une (`dn_widget_unite`). */
            const char *u0 = dn_ui_case_unite(i, g);
            const char *u = u0 ? u0 : "";
            printf(" %s%s%s", (t && t[0]) ? t : "--", (t && t[0]) ? " " : "",
                   (t && t[0]) ? u : "");
        }
        /* Les DEUX comptes, sur la même ligne que la case qu'ils décrivent. */
        printf("   | case ");
        widget_indices_imprimer(i);
        printf(" · detail %d\n", dn_ui_detail_grandeurs(i));
    }
    /*
     * ── dn4-9 : LES **TROIS** COMPTEURS DE GÉOMÉTRIE, SANS RIEN DÉTRUIRE ─────
     *
     * 🔴 « AVANT / APRÈS » N'ÉTAIT PAS EXÉCUTABLE, ET C'EST UN DÉFAUT
     *    D'INSTRUMENT, ⛔ pas de protocole : `widget largeur` n'imprime que
     *    `chevauchements` ; les TROIS ne sortaient que de `widget voie` et
     *    `widget grandeurs <c> <n>`, **qui reconstruisent (~350 ms) et remettent
     *    les compteurs à zéro juste avant** (`compteurs_geom_reset()`).
     *    ⇒ Lire « avant » DÉTRUISAIT ce qu'on relève.
     * ✅ Ici : lecture pure. `widget` nu ne reconstruit rien, ne remet rien à
     *    zéro, et ne bloque pas le REPL — donc pas le transport PC.
     * ⛔ LES TROIS NE S'ADDITIONNENT JAMAIS : ce sont trois diagnostics
     *    distincts (côte à côte / colonne unique / hauteur).
     * ⚠️ `trop larges` ne mesure QU'À LA CONSTRUCTION (`dn_widget.h`) : une
     *    valeur qui devient trop large ENTRE deux reconstructions n'est vue par
     *    personne. Forcer le pire cas par `dn_injecteur.py --jeu pire`, qui
     *    reconstruit avec les plafonds.
     */
    printf("geometrie  : %u chevauchement(s) · %u trop large(s) en colonne "
           "unique · %u en HAUTEUR\n",
           (unsigned)dn_widget_chevauchements(),
           (unsigned)dn_widget_trop_larges(),
           (unsigned)dn_widget_debordements());
    printf("             (cumul depuis le dernier `widget largeur reset` — "
           "LECTURE PURE, rien n'a ete reconstruit ni remis a zero)\n");
    /*
     * 🔴 REJET DE SOUS-COMMANDE INCONNUE (revue 2026-08-18). Toute invocation
     *    mal tapee traversait TOUTES les branches jusqu'ici, imprimait ce dump
     *    d'etat parfaitement plausible et rendait 0. `widget rafalle`,
     *    `widget rafale on`, `widget bande on` : l'operateur croyait avoir
     *    lance l'instrument. Pire, `dn_ui_rafale_cycles()` etant un statique
     *    COLLANT, le dump reaffichait le verdict de la rafale PRECEDENTE.
     *    ⚠️ Ce verdict n'existe plus (revue 2026-08-19, temoin enterre) ; le rejet
     *    de sous-commande inconnue, lui, reste indispensable.
     * ⚠️ `widget` NU reste legitime : c'est le dump d'etat.
     */
    if (argc > 1) {
        /* 🔴 « INCONNUE » CONTRE « MAL COMPTEE » — REVUE DU 2026-08-19.
         *    Ce rejet se declenche sur tout `argc > 1` non consomme, y compris
         *    quand la sous-commande EXISTE et que seul le nombre d'arguments est
         *    faux : `widget voie`, `widget grandeurs 1`, `widget grille 60`
         *    ressortaient « sous-commande INCONNUE : "voie" », ce qui est
         *    factuellement faux et envoie chercher au mauvais endroit.
         * ⚠️ La liste de secours, elle, avait douze entrees de retard : `piste`
         *    manquait DEJA, et les dix de dn4-6 n'y ont jamais ete ajoutees.
         *    C'est le grief exact du README (« une commande qu'on ne trouve que
         *    depuis la carte n'est pas documentee »), deplace du README vers le
         *    chemin d'erreur. */
        static const char *const k_connues[] = {
            "groupe", "opa",   "voile",     "icone",   "mock",    "demo",
            "pousser", "oublier", "rafale",  "nue",     "barre",   "bandes",
            "piste",  "voie",  "grandeurs", "dispo",   "entete",  "val",
            "police", "grille", "largeur",  "detail",  "replacer",
        };
        bool connue_mais_arite = false;
        for (size_t k = 0; k < sizeof(k_connues) / sizeof(k_connues[0]); k++) {
            if (strcmp(argv[1], k_connues[k]) == 0) {
                connue_mais_arite = true;
                break;
            }
        }
        if (connue_mais_arite) {
            printf("🔴 « %s » EXISTE, mais pas avec %d argument(s).", argv[1],
                   argc - 2);
            printf("\n   RIEN n'a ete execute. `aide` donne la forme exacte.\n");
        } else {
            printf("🔴 sous-commande INCONNUE : « %s »", argv[1]);
            for (int i = 2; i < argc; i++) {
                printf(" %s", argv[i]);
            }
            printf("\n   RIEN n'a ete execute. `aide` liste le jeu complet.\n");
        }
        printf("   Sous-commandes : groupe · opa · voile · icone · piste ·\n");
        printf("   mock · demo · pousser · oublier · rafale · nue · barre ·\n");
        printf("   bandes · voie · grandeurs · dispo · entete · val · police ·\n");
        printf("   grille · largeur · detail · replacer\n");
        return 1;
    }
    printf("\nLES TROIS REGIMES, ET POURQUOI ILS SONT TROIS :\n");
    printf("  REELLE  = mesuree par une source            -> valeur BLANCHE\n");
    printf("  SIMULEE = fabriquee par un mock             -> AMBRE + badge "
           "« SIMULÉ »\n");
    printf("  ABSENTE = aucune source, ou source morte    -> « -- » GRISE\n");
    printf("⚠️ Un `bool valide` seul ne sait pas dire « cette valeur est\n");
    printf("   fabriquee » : un mock s'y presenterait exactement comme une\n");
    printf("   mesure. C'est le meme mensonge d'interface qu'un CPU fige a\n");
    printf("   47 %% pendant que la tour dort — en plus discret.\n");
    printf("⚠️ « dessinee = NON » : la case n'est sur AUCUN ecran en ce moment\n");
    printf("   (modele REBUILD en vue detail), OU LVGL est arrete (`ui off`,\n");
    printf("   `scene`, `tear`). L'etat est CONSERVE et sera pose a la prochaine\n");
    printf("   construction — mais rien n'atteint la dalle.\n");
    /* 🔴 LA LISTE DES CASES NUES EST RELUE (revue 2026-08-18) : « GPU/RAM/RESEAU »
     *    était écrit en dur, dans la commande dont le docblock jure que rien
     *    n'est récité. Une ligne de `k_widget[]` qui bascule, et la phrase ment. */
    printf("\nCases NUES (temoin negatif d'AC8) :");
    int n_nues = 0;
    for (int i = 0; i < DN_UI_METRIQUES; i++) {
        if (!dn_ui_est_widget(i)) {
            printf(" %s", dn_ui_metrique_nom(i));
            n_nues++;
        }
    }
    if (n_nues == 0) {
        /* 🔴 UNE LISTE VIDE DOIT SE DIRE (revue 2026-08-18) : depuis dn3-2 les
         *    SIX cases portent le modele, donc ce dump sortait une liste vide
         *    suivie d'un paragraphe expliquant que c'est « la seule facon de
         *    chiffrer ». Un operateur pouvait le lire comme un etat des lieux
         *    au lieu d'un mode d'emploi. */
        printf(" AUCUNE");
        printf("\n⚠️ Les SIX cases portent le modele — c'est l'etat NORMAL depuis\n");
        printf("   dn3-2. Le temoin negatif d'AC8 ne vit plus dans des cases\n");
        printf("   nues permanentes : il se PROVOQUE, par `widget nue <idx> on`,\n");
        printf("   le temps d'un releve, puis se rend par `off`.\n");
    } else {
        printf("\nElles n'ont pas le modele — c'est la seule facon de chiffrer une\n");
        printf("case-widget contre une case nue sous le meme fps/bounce/draw buffer.\n");
        printf("Aucune source ne les alimente, et elles le DISENT.\n");
    }
    return 0;
}

static int cmd_wifi(int argc, char **argv)
{
    if (argc >= 2 && strcmp(argv[1], "on") == 0) {
        if (argc != 4) {
            printf("usage : wifi on <ssid> <mdp>  (ssid/mdp SANS espace — le REPL "
                   "coupe dessus)\n");
            return 1;
        }
        return dn_wifi_on(argv[2], argv[3]) == ESP_OK ? 0 : 1;
    }
    if (argc == 2 && strcmp(argv[1], "off") == 0) {
        return dn_wifi_off() == ESP_OK ? 0 : 1;
    }
    if (argc == 3 && strcmp(argv[1], "ws") == 0) {
        bool on;
        if (!parse_on_off(argv[2], &on)) {
            printf("usage : wifi ws on|off\n");
            return 1;
        }
        return (on ? dn_wifi_ws_on() : dn_wifi_ws_off()) == ESP_OK ? 0 : 1;
    }
    if (argc == 1 || (argc == 2 && strcmp(argv[1], "info") == 0)) {
        printf("wifi : %s", dn_wifi_etat_nom(dn_wifi_etat()));
        if (dn_wifi_etat() == DN_WIFI_CONNECTEE) {
            printf(" · ip %s · rssi %d dBm", dn_wifi_ip(), dn_wifi_rssi());
        }
        printf(" · %u reconnexions (retente IMMEDIATEMENT, sans backoff — "
               "dn4-1)\n",
               (unsigned)dn_wifi_reconnexions());
        printf("ws   : %s · %u messages · %u connexions\n",
               dn_wifi_ws_actif() ? "ACTIF ws://…:80/dn" : "off",
               (unsigned)dn_wifi_ws_messages(), (unsigned)dn_wifi_ws_connexions());
        return 0;
    }
    printf("usage : wifi [info] | on <ssid> <mdp> | off | ws on|off\n");
    return 1;
}

/*
 * ── `i2c` : le bus VU DE SES ADRESSES (dn2-1) ────────────────────────────────
 *
 * L'INSTRUMENT AVANT LE DRIVER. dn2-1 pose le premier composant EXTERNE sur un
 * bus qui porte déjà la dalle (TCA9554) et le tactile (GT911). Avant de se
 * demander si un driver de capteur marche, il faut savoir si le capteur RÉPOND :
 * un scan sépare deux questions qu'un driver seul confond, et il répond à la
 * seconde sans qu'une ligne de driver existe.
 *
 * ✅ TÉMOIN POSITIF INTÉGRÉ, et il n'est pas décoratif : le scan CONCLUT lui-même
 *    sur la présence de 0x20 et 0x5D. Un scan qui ne voit pas les deux occupants
 *    connus est un instrument CASSÉ, et aucune conclusion sur un composant neuf
 *    n'est alors recevable. Le verdict est imprimé plutôt que laissé à la
 *    sagacité du lecteur — c'est la doctrine du dépôt : l'instrument dit s'il est
 *    crédible.
 *
 * ✅ TÉMOIN NÉGATIF, côté opérateur : débrancher le composant (carte hors
 *    tension) et rescanner. Son adresse doit DISPARAÎTRE. Sans ça, « l'adresse
 *    est là » ne prouve pas qu'elle vient de lui.
 *
 * 🔴 UN SCAN À UNE SEULE PASSE FABRIQUE DES FAUX POSITIFS — MESURÉ LE 2026-08-16,
 *    SUR CETTE CARTE, AVANT QU'AUCUN CAPTEUR NE SOIT BRANCHÉ. Quatre passes
 *    consécutives, bus strictement inchangé, ont donné :
 *      passe 0 : 0x20 0x51 0x5D 0x6B + 0x6F   (+ 1 timeout)
 *      passe 1 : 0x20 0x51 0x5D 0x6B
 *      passe 2 : 0x20 0x51 0x5D 0x6B
 *      passe 3 : 0x20 0x51 0x5D 0x6B + 0x58
 *    Quatre adresses stables, et une CINQUIÈME QUI CHANGE DE VALEUR — 0x6F, puis
 *    rien, rien, 0x58. Ce ne sont pas des composants : c'est le sondage qui
 *    acquitte à tort, très probablement en concurrence avec le polling du GT911
 *    (~30 transactions/s) sur le même bus.
 *
 *    ⇒ CHAQUE ADRESSE TROUVÉE EST RE-SONDÉE, et le résultat est publié « n/N ».
 *    Sans ça, un capteur intermittent et un faux positif produisent exactement
 *    la même trace, et rien dans la sortie ne permet de les distinguer. C'est le
 *    Trap n°2 de la story appliqué à cet outil : *cet instrument peut-il voir ce
 *    qu'il prétend exclure ?* — la réponse était NON, et le premier scan de la
 *    session l'a démontré.
 *
 *    🔴 IL PRODUIT AUSSI DES FAUX NÉGATIFS — MESURÉ LE 2026-08-17, ET C'EST LA
 *    MOITIÉ QUI MANQUAIT. Trois composants SOUDÉS ont raté une confirmation au
 *    cours de la séance : 0x6B (IMU), 0x5D (GT911) et 0x77 (BME680 une fois
 *    soudé), une fois chacun. Le BME680 est même sorti ABSENT d'une passe sur
 *    six alors que sa soudure était bonne.
 *    ⇒ **`n/N < N` NE PROUVE RIEN, dans un sens comme dans l'autre.** Ce sondage
 *    sert à DÉCOUVRIR ; seule `i2c lire <addr> <reg>` QUALIFIE — c'est une vraie
 *    transaction, et 10 lectures sur 10 ont réussi là où le scan hésitait.
 *    Croire le scan aurait fait rejeter une soudure correcte.
 *    ⚠️ Le corollaire vaut aussi dans l'autre sens : un faux positif n'a aucun
 *    registre à rendre. Dans les deux cas, l'arbitre est la lecture.
 *
 * ⚠️ CE SCAN EST UNE RAFALE I²C, donc du même régime que le stimulus de §11.4 —
 *    mais il dure ~25 ms **quand tout acquitte**, et une perturbation de 25 ms
 *    n'est PAS observable à l'œil. **Ce n'est donc pas un test de §11.4**, et il
 *    ne faut pas le publier comme tel. Le vrai test est la cadence EN RÉGIME.
 *
 * ⚠️ IL BLOQUE LE REPL PENDANT SA DURÉE, et sur la branche A retenue en dn2-2
 *    **le REPL EST le transport PC** : les trames de l'agent restent dans le
 *    tampon USB tant que le scan tourne. Même piège que `cpu N`, trouvé en
 *    session de validation dn2-2.
 *    🔴 **Et « ~25 ms » est le cas SAIN, pas la borne** (CR 2026-08-17) : 112
 *    sondages à 50 ms de timeout + les confirmations donnent un pire cas de
 *    **~9 s**. La plage bornée n'y suffisait pas ⇒ voir DN_I2C_SCAN_BUDGET_MS,
 *    et l'abandon **s'imprime** au lieu de tronquer en silence.
 *
 * ⚠️ `i2c_master_probe()` NE SPAMME PAS le log sur NACK — vérifié dans le source
 *    d'ESP-IDF v5.5.5 (`i2c_master.c:1374`, `bus_handle->bypass_nack_log = true`),
 *    pas supposé. C'est ce qui rend un scan de 112 adresses lisible.
 */
/* Sondages par adresse retenue. 5 est un compromis : assez pour qu'un faux
 * positif isolé tombe (aucun des trois observés ne s'est répété), assez peu pour
 * que le scan reste sous la centaine de millisecondes. */
#define DN_I2C_SCAN_CONFIRMATIONS 5
/* ⚠️ 50 ms et non 20 : `i2c_master_probe` prend le VERROU DE BUS, que le polling
 * du GT911 tient ~30 fois par seconde. À 20 ms (= 2 ticks à 100 Hz), la première
 * passe de la session a produit un `probe device timeout` — une adresse jamais
 * sondée, comptée nulle part, dans une liste qui se lisait comme exhaustive. */
#define DN_I2C_SCAN_TIMEOUT_MS 50
/* Un bus sain en porte 4 ; 16 laisse la place aux 4 capteurs de dn4-2 et à leurs
 * surprises. Au-delà, ce n'est plus un bus chargé, c'est un bus qui acquitte
 * n'importe quoi — et la commande le DIT au lieu de tronquer en silence. */
#define DN_I2C_SCAN_MAX_TROUVES 16
/*
 * 🔴 CR 2026-08-17 — LE SCAN POUVAIT BLOQUER LE TRANSPORT PC ~9 SECONDES.
 *
 * L'en-tete ci-dessus annonce « ~25 ms » et le README « ~26 ms » : c'est le cas
 * SAIN, celui ou tout acquitte tout de suite. Le pire cas reel, lui, se calcule :
 * 112 sondages × 50 ms de timeout, plus 16 candidats × 4 confirmations — soit
 * ~9 s pendant lesquelles le REPL, donc LE TRANSPORT PC (branche A), n'ingere
 * plus rien. ⚠️ CR dn4-2 du 2026-08-24 : ~9 s est le pire cas AVANT ce budget.
 * APRES lui, le pire cas est ~2 500 ms (decouverte, BORNEE) + jusqu'a 16 × 4 ×
 * 50 ms = 3 200 ms (confirmation, HORS budget) ≈ 5,7 s — et il n'est donc PAS
 * « borne par DN_I2C_SCAN_BUDGET_MS », contrairement a ce que le README et
 * §13.6 ont publie jusqu'a cette date. Le budget borne la DECOUVERTE, pas la
 * commande. C'est exactement le defaut de `cpu N` trouve en validation dn2-2,
 * a une echelle pire.
 * ⇒ Un budget est pose, et son DEPASSEMENT S'IMPRIME. Un scan tronque qui se
 *   tairait serait un instrument qui ment par omission — la faute meme que le
 *   compteur de timeouts existe pour eviter.
 */
#define DN_I2C_SCAN_BUDGET_MS 2500
static const char *i2c_nom_connu(uint8_t addr)
{
    switch (addr) {
    case DN_TCA9554_ADDR:
        return "TCA9554 — expander (LCD_RST/TP_RST/LCD_CS)  [temoin]";
    case DN_GT911_ADDR:
        return "GT911 — tactile                             [temoin]";
    case DN_GT911_ADDR_BACKUP:
        return "GT911 — adresse de REPLI (INT haut au reset)";
    case DN_RTC_ADDR:
        return "PCF85063A — RTC, PILOTEE par dn_rtc (dn3-2)";
    /* ⚠️ CR dn4-2 du 2026-08-24 : 0x6A et 0x6B rendaient le MEME nom, alors que
     * le depot a TRANCHE 0x6B par la mesure. Un device reel a 0x6A aurait donc
     * ete nomme faux — et ce switch est ce que le scan affiche. */
    case 0x6B:
        return "QMI8658 — IMU (hors V1) — L'ADRESSE MESUREE";
    case 0x6A:
        return "0x6A — ⚠️ PAS l'IMU : celle-ci est MESUREE a 0x6B. Adresse INCONNUE";
    case DN_BME680_ADDR:
        return "BME680 — temperature/humidite (dn2-1) — L'ADRESSE MESUREE";
    /* 🔴 0x76 EST L'AUTRE ADRESSE POSSIBLE DU BME680, ET C'EST AUSSI CELLE DU
     * FAUX POSITIF QUI A OUVERT CETTE STORY — §13.2 : il est sorti a vide,
     * AUCUN capteur branche, et aurait envoye la seance chercher un driver
     * pendant des heures. L'etiqueter « BME680 » comme si de rien n'etait
     * rearmait le piege que cette commande existe pour desamorcer
     * (CR 2026-08-17). Notre module ne repond PAS la : son SDO est tire haut. */
    case 0x76:
        return "0x76 — ⚠️ PAS notre BME680 (il est a 0x77, SDO haut). C'est "
               "l'adresse du FAUX POSITIF de §13.2 : verifier par `i2c lire 76 D0` "
               "AVANT d'en conclure quoi que ce soit";
    /* 🔴 TROIS ETIQUETTES CORRIGEES EN dn4-2 (2026-08-19), ET L'UNE ETAIT
     * DOUBLEMENT FAUSSE.
     *  (a) « (dn4-1) » : le correct-course du 2026-08-18 a rendu
     *      `dn4-1-tout-branche-tenue-h24` SUPERSEDED et reassigne le cablage a
     *      `dn4-2`. Un lecteur qui suivait ce pointeur arrivait sur une story
     *      close qui ne parle pas de capteurs.
     *  (b) 🔴 « VL53L0X » : REFUTE PAR L'INVENTAIRE PHYSIQUE. Le module est un
     *      `TOF050C-VL6180X`, lu DEUX fois — sur l'etiquette du sachet et sur la
     *      serigraphie de la carte (9 photos EXIF 2026-08-19 17:18-17:20,
     *      docs/cablage/, §13.0 et §13.4 bis). L'addendum du brief §3 avait POSE
     *      la question le 2026-08-14 (« noter la ref reelle du breakout a
     *      l'inventaire ») et personne ne l'avait fermee pendant cinq jours.
     *      ⛔ Et « meme famille ToF » est FAUX sur les trois points qui comptent :
     *      index de registre 16 bits (pas 8), identite 0x0000 -> 0xB4 (pas
     *      0xC0 -> 0xEE), portee GARANTIE 100 mm (pas 2 m). */
    case DN_BH1750_ADDR:
        return "BH1750 — luminosite (dn4-2) — ⛔ AUCUN registre : "
               "`i2c lire` le PILOTE au lieu de le lire (opcodes). "
               "Le qualifier par STIMULUS, voir `i2c ecrire`/`i2c brut`";
    case DN_VL6180X_ADDR:
        return "TOF050C-VL6180X — distance (dn4-2) — ⛔ index de registre sur "
               "16 BITS : `i2c lire` ne peut pas le qualifier, utiliser "
               "`i2c lire16 29 0000` (attendu B4)";
    case DN_INA219_ADDR:
        return "INA219 — tension/courant (dn4-2) — ✅ `i2c lire 40 00 2` "
               "doit rendre 39 9F (reset du registre Configuration)";
    default:
        return "INCONNU — a identifier avant d'en tirer quoi que ce soit";
    }
}

/* Lecture registre : ajoute un device TEMPORAIRE, lit, le retire.
 * ⚠️ PREMIER `i2c_master_bus_add_device()` DU DÉPÔT — le TCA9554 et le GT911
 *    passent tous deux par leur composant, qui le fait en interne. Le RETRAIT
 *    est TENTE sur tous les chemins de sortie : en laisser fuir un à chaque
 *    appel épuiserait la table du bus, et l'échec arriverait bien plus tard,
 *    ailleurs, sans rapport visible avec cette commande.
 * 🔴 CR dn4-2 du 2026-08-24 — « SE RETIRE » ETAIT FAUX, ET LA CARTE L'A PROUVE
 *    (1 refus sur 13, §13.17.3). `i2c_master_bus_rm_device` peut REFUSER, et
 *    l'IDF place son `ESP_RETURN_ON_FALSE(status > I2C_STATUS_START)` AVANT le
 *    `SLIST_REMOVE` (esp_driver_i2c/i2c_master.c:1216) : le device reste alors
 *    dans `device_list`. ⇒ On TENTE et on DIT quand ça rate. ⛔ On ne promet pas. */
/* Ouverture du device TEMPORAIRE, factorisee en dn4-2 : les QUATRE primitives
 * (`lire`, `lire16`, `ecrire`, `brut`) partagent exactement ce geste, et le
 * dupliquer trois fois de plus multiplierait par quatre les chemins de sortie
 * ou un device peut FUIR. Rend ESP_OK et pose *dev, ou imprime son refus.
 * ⛔ Le retrait est TENTE sur tous les chemins de sortie de l'appelant — et
 *    ANNONCE quand il echoue (CR du 2026-08-24 : il peut echouer pour de vrai). */
static esp_err_t i2c_dev_ouvrir(uint8_t addr, i2c_master_dev_handle_t *dev)
{
    *dev = NULL;
    i2c_master_bus_handle_t bus = dn_display_i2c_bus();
    if (!bus) {
        printf("bus I2C absent — dn_display_init() n'a pas tourne\n");
        return ESP_ERR_INVALID_STATE;
    }
    /* ⚠️ Le type est `i2c_device_config_t`, PAS `i2c_master_dev_config_t` — le
     * second n'existe pas, et le compilateur ne le dit qu'en aval, sur un
     * « passing argument 2 … from incompatible pointer type (int *) » qui envoie
     * chercher au mauvais endroit. Struct lue dans
     * components/esp_driver_i2c/include/driver/i2c_master.h:47-55. */
    i2c_device_config_t cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = addr,
        /* La frequence se pose PAR DEVICE (dn_pins.h) : on demande celle de nos
         * autres devices, pas un defaut de composant tiers.
         * 🔴 dn4-7 : SAUF le VL6180X, ralenti deliberement — sinon `i2c lire16 29`
         * parlerait plus vite que `dn_env`, et les deux chemins ne mesureraient
         * plus la meme chose. Motif complet dans dn_pins.h. */
        .scl_speed_hz = (addr == DN_VL6180X_ADDR) ? DN_I2C_FREQ_TOF_HZ
                                                  : DN_I2C_FREQ_HZ,
    };
    esp_err_t err = i2c_master_bus_add_device(bus, &cfg, dev);
    if (err != ESP_OK) {
        printf("ajout du device 0x%02X refuse : %s\n", addr, esp_err_to_name(err));
        *dev = NULL;
    }
    return err;
}

/* 🔴 CR dn4-2 — LE RETRAIT PEUT REFUSER, ET PERSONNE NE LE LISAIT.
 * `i2c_master_bus_rm_device()` fait
 *   ESP_RETURN_ON_FALSE(atomic_load(&bus->status) > I2C_STATUS_START, …)
 * (esp_driver_i2c/i2c_master.c:1216) et rend ESP_ERR_INVALID_STATE SANS liberer
 * le device NI le retirer de `device_list`. ⛔ Ce test precede la prise de
 * `bus_lock_mux`, et `status` est PAR BUS : le GT911 sonde le meme bus ~30x/s, la
 * tache capteurs toutes les 5 s, la RTC aussi. La course existe donc, et sur la
 * mauvaise carte le handle FUIT definitivement et en SILENCE.
 * ⚠️ Le docblock promettait « retire sur TOUS les chemins de sortie » et §13.6
 *    quater en fait le critere eliminatoire n°2 : la promesse etait tenue par
 *    l'APPEL, pas par la VERIFICATION.
 * 🔴 CR du 2026-08-24 — ELLE N'EST TENUE PAR AUCUN DES DEUX, ET LE COMMENTAIRE
 *    PRECEDENT (« elle l'est maintenant par les deux ») ETAIT FAUX. Cette
 *    fonction DIT la fuite ; elle ne la REPARE pas, et elle rend `void`, donc
 *    l'appelant ne peut meme pas retenter. ⚠️ La condition qui provoque le refus
 *    (`bus->status <= I2C_STATUS_START`) est TRANSITOIRE : une reprise bornee
 *    l'eliminerait. Entree au ledger — le meme defaut vit sur QUATRE autres
 *    sites non verifies (dn_capteurs.c, dn_rtc.c x3). */
static void i2c_dev_fermer(i2c_master_dev_handle_t dev)
{
    esp_err_t rm = i2c_master_bus_rm_device(dev);
    if (rm != ESP_OK) {
        printf("⚠️ RETRAIT DU DEVICE REFUSE (%s) — un device FANTOME reste sur le\n",
               esp_err_to_name(rm));
        printf("   bus et deux allocations ont fui. Course connue avec le sondage\n");
        printf("   du GT911 (~30/s). ⛔ Le resultat de la commande — imprime\n");
        printf("   JUSTE APRES ce bloc, pas avant — reste VALIDE ; c'est\n");
        printf("   le menage qui a rate. Un `reboot` remet la table du bus a plat.\n");
    }
}

static bool i2c_addr_est_occupee_par_le_firmware(uint8_t addr); /* def. plus bas */
static void i2c_dire_la_cause(esp_err_t err);                  /* def. plus bas */

static int i2c_lire_registre(uint8_t addr, uint8_t reg, int n)
{
    /* 🔴 CR dn4-2 du 2026-08-24 — ELLE ECRIT AVANT DE LIRE, ET C'ETAIT LA SEULE
     * DES QUATRE PRIMITIVES A NE TESTER AUCUNE ADRESSE.
     * `transmit_receive(dev, &reg, 1, ...)` emet l'octet d'index SUR LE FIL. Sur
     * un composant SANS registre, cet octet est une COMMANDE :
     *   - `i2c lire 23 00` = POWER DOWN du BH1750, `23 07` = RESET. La sortie est
     *     STRICTEMENT identique a une lecture reussie, et le `i2c brut 23 2`
     *     suivant rend 00 00 => on declare mort un capteur VIVANT. C'est le faux
     *     negatif qui envoie au fer, et le fer est IRREVERSIBLE.
     *   - sur un occupant du firmware, elle DOUBLE le pilote — meme risque que
     *     `i2c ecrire`, qui lui avertissait deja.
     *   - sur le VL6180X, l'index est sur 16 BITS : un index d'UN octet est une
     *     violation de protocole dont l'echec RESSEMBLE a une mauvaise soudure.
     * ⚠️ On NE BLOQUE PAS : c'est une console de diagnostic, et interdire une
     *    adresse serait retirer un instrument. On NOMME le risque AVANT de le
     *    prendre — la regle du depot est « ecrit, jamais masque ». */
    if (addr == DN_BH1750_ADDR) {
        printf("🔴 0x%02X N'A AUCUN REGISTRE : l'octet 0x%02X part comme un\n",
               addr, reg);
        printf("   OPCODE, pas comme un index. `i2c lire` le PILOTE au lieu de le\n");
        printf("   lire (00 = power down, 07 = reset), et la sortie ressemble a\n");
        printf("   une lecture reussie.\n");
        printf("   ⇒ UTILISER `i2c brut %02X 2`.\n", DN_BH1750_ADDR);
        if (reg == 0x00 || reg == 0x07) {
            printf("   ⛔ CET OCTET-LA VIENT D'ETEINDRE OU DE RESETTER LE CAPTEUR :\n");
            printf("      `i2c ecrire %02X 01` puis `i2c ecrire %02X 10` le\n",
                   DN_BH1750_ADDR, DN_BH1750_ADDR);
            printf("      rallument. ⛔ NE PAS conclure « capteur mort » ici.\n");
        }
    } else if (i2c_addr_est_occupee_par_le_firmware(addr)) {
        printf("🔴 0x%02X EST PILOTE PAR LE FIRMWARE : %s\n", addr,
               i2c_nom_connu(addr));
        printf("   ⚠️ `i2c lire` ECRIT l'octet d'index 0x%02X avant de lire — ce\n", reg);
        printf("      n'est PAS une lecture passive. Meme risque que `i2c ecrire`\n");
        printf("      sur cette adresse.\n");
    } else if (addr == DN_VL6180X_ADDR) {
        printf("⚠️ 0x%02X indexe ses registres sur 16 BITS : un index d'UN octet\n",
               addr);
        printf("   est une violation de protocole, et son echec RESSEMBLE a une\n");
        printf("   mauvaise soudure. ⇒ UTILISER `i2c lire16 %02X 00%02X`.\n",
               addr, reg);
    }
    i2c_master_dev_handle_t dev = NULL;
    if (i2c_dev_ouvrir(addr, &dev) != ESP_OK) {
        return 1;
    }
    esp_err_t err;
    uint8_t rx[16] = {0};
    err = i2c_master_transmit_receive(dev, &reg, 1, rx, (size_t)n, 200);
    i2c_dev_fermer(dev);
    if (err != ESP_OK) {
        printf("lecture 0x%02X reg 0x%02X : ECHEC (%s)\n", addr, reg,
               esp_err_to_name(err));
        i2c_dire_la_cause(err);
        return 1;
    }
    printf("0x%02X reg 0x%02X :", addr, reg);
    for (int i = 0; i < n; i++) {
        printf(" %02X", rx[i]);
    }
    printf("\n");
    /* Les deux registres d'identite que dn2-1 doit lire, interpretes ICI : les
     * relire de tete a chaque session est exactement la ou naissent les erreurs
     * de transcription. */
    /* 🔴 CR dn4-2 du 2026-08-24 — LE VERDICT EST DESORMAIS GARDE PAR L'ADRESSE.
     * Il ne tenait qu'a `reg`, donc `i2c lire 29 D0` / `40 D0` / `51 F0`
     * imprimaient « ce n'est pas un BME/BMP » ou « variant 0x00 = BME680 » sur un
     * composant qui n'a JAMAIS ete un BME — un verdict faux ET plausible, qui
     * escalade. ⚠️ Le commentaire de `lire16` enumerait les fonctions qui testent
     * l'adresse et OUBLIAIT celle-ci : c'est la « gate scopee a UNE fonction »
     * que ce depot a deja nommee. */
    if (addr == DN_BME680_ADDR && reg == 0xD0 && n >= 1) {
        const char *quoi = rx[0] == 0x61   ? "BME680 ou BME688 (0xF0 tranche)"
                           : rx[0] == 0x60 ? "BME280 — PAS de gaz"
                           : rx[0] == 0x58 ? "BMP280 — NI gaz NI humidite"
                                           : "INCONNU — ce n'est pas un BME/BMP";
        printf("  => chip id 0x%02X = %s\n", rx[0], quoi);
    }
    if (addr == DN_BME680_ADDR && reg == 0xF0 && n >= 1) {
        printf("  => variant 0x%02X = %s\n", rx[0],
               rx[0] == 0x00   ? "BME680"
               : rx[0] == 0x01 ? "BME688"
                               : "INCONNU");
    }
    return 0;
}

/* ════════════════════════════════════════════════════════════════════════════
 * dn4-2 (2026-08-19) — LES QUATRE SOUS-COMMANDES NEUVES QUE LES DATASHEETS IMPOSENT.
 *
 * 🔴 LE CONSTAT QUI LES REND NECESSAIRES, ET CE N'EST PAS UNE OPINION DE
 *    CONCEPTION : `i2c lire` fait `transmit_receive(dev, &reg, 1, …)` — elle
 *    ECRIT UN octet d'index PUIS lit. Or, sur les trois capteurs que dn4-2
 *    branche, elle n'en qualifie qu'UN :
 *
 *      · BH1750 (0x23)  — AUCUN registre. L'octet « registre » EST UNE COMMANDE.
 *        `i2c lire 23 00` le met en POWER DOWN, `23 07` RESET son registre de
 *        donnee, 0x08..0x0F sont INDEFINIS, 0x40..0x7F reprogramment le MTreg.
 *        ⇒ l'utiliser ne le qualifie pas : ça le PILOTE AU HASARD, et les deux
 *        octets rendus se liraient comme une identite alors que ce sont des lux.
 *      · VL6180X (0x29) — index de registre sur 16 BITS, MSB d'abord. Envoyer UN
 *        octet puis un restart-read est une VIOLATION DE PROTOCOLE : le resultat
 *        n'est ni 0xB4 ni reproductible. ⛔ Et un echec ici ressemblerait
 *        EXACTEMENT a une mauvaise soudure — la confusion qui a coute une seance
 *        entiere a dn2-1 (§13.5).
 *      · INA219 (0x40) — registres 16 bits DERRIERE un index 8 bits ⇒ `i2c lire
 *        40 00 2` rend 39 9F. ✅ Le seul des trois que l'instrument couvrait.
 *
 * ⛔ POURQUOI TROIS COMMANDES ET NON UN DRAPEAU SUR `i2c lire` : celle-ci
 *    INTERPRETE DEJA l'octet elle-meme pour le BME680 (0xD0 -> chip id,
 *    0xF0 -> variant, en dur). Deux semantiques d'index dans une meme commande
 *    est exactement l'ambiguite qui produit un chiffre FAUX ET PLAUSIBLE — et
 *    « un chiffre faux mais plausible est plus dangereux qu'un chiffre absurde ».
 *
 * ⛔ AUCUNE DES TROIS PRIMITIVES DE LECTURE/ECRITURE ne boucle ni ne dort : le
 *    REPL EST le transport PC. Cout en regime : ZERO — ni tache, ni timer, ni
 *    allocation permanente.
 * 🔴 CR dn4-2 — LA REGLE CI-DESSUS A ETE ECRITE POUR « LES TROIS », ET LA
 *    QUATRIEME S'Y SOUSTRAYAIT EN SILENCE. `i2c rafale` EST une boucle de 30 s
 *    qui bloque le transport : c'est SON METIER (AC9), et c'est assume — mais le
 *    critere n°3 de §13.6 quater etait cadre de façon a ne pas la voir. C'est le
 *    motif « gate scopee a UNE fonction », deja corrige deux fois sur `widget`.
 *    ⇒ La regle exacte est : aucune sous-commande ne coute quoi que ce soit EN
 *      REGIME (ni tache, ni timer, ni allocation permanente) ; `rafale` bloque le
 *      REPL PENDANT SA FENETRE, bornee, annoncee, et desormais tenue PAR ADRESSE.
 * ════════════════════════════════════════════════════════════════════════════
 */

/* ── `i2c ecrire <addr> <o1> [o2..o8]` — ECRITURE NUE, aucune lecture ────────
 * ⚠️ ELLE PEUT CASSER UN COMPOSANT SAIN : sur le BH1750, `00` = power down et
 *    `07` = reset du registre de donnee. La sortie DIT CE QU'ELLE A ENVOYE,
 *    pour qu'un « le capteur ne repond plus » se rattache a son geste. */
/* 🔴 CR dn4-2 — L'AVERTISSEMENT DE DANGER N'ETAIT IMPRIME QUE SI L'INVOCATION
 * ETAIT MALFORMEE : le bloc « elle peut casser un composant sain » vivait dans la
 * branche `if (n < 1 || n > 8)`, donc une commande BIEN FORMEE n'affichait rien
 * avant d'executer. Et `parse_adresse_i2c` accepte tout 0x08..0x77 : rien
 * n'empechait `i2c ecrire 20 01 00` d'ecrire sur le TCA9554, qui porte LCD_RST,
 * TP_RST et LCD_CS — ecran noir et tactile mort jusqu'au reboot, avec le registre
 * ombre du composant esp_io_expander DESYNCHRONISE et rien pour le reecrire.
 * ⛔ La table qui identifie ces occupants existe DANS CE FICHIER (i2c_nom_connu)
 *    et la commande neuve ne la consultait pas.
 * ⚠️ On NE BLOQUE PAS : c'est une console de diagnostic, et interdire une adresse
 *    serait retirer un instrument. On NOMME le risque AVANT de le prendre — la
 *    regle du depot est « ecrit, jamais masque ». */
static bool i2c_addr_est_occupee_par_le_firmware(uint8_t addr)
{
    /* ⚠️ CR dn4-2 du 2026-08-24 — DN_GT911_ADDR_BACKUP MANQUAIT. `i2c_nom_connu`
     * porte 0x14 (« adresse de REPLI, INT haut au reset ») et le scan le traite a
     * EGALITE avec 0x5D ; cette garde, elle, l'ignorait. Sur une carte partie en
     * repli, `i2c ecrire 14 ...` ecrivait dans le controleur tactile PILOTE sans
     * un mot, la ou 0x5D imprime sept lignes. La consultation de la table etait
     * INCOMPLETE, alors que le commentaire du correctif disait le contraire. */
    return addr == DN_TCA9554_ADDR || addr == DN_GT911_ADDR ||
           addr == DN_GT911_ADDR_BACKUP ||
           addr == DN_RTC_ADDR || addr == DN_BME680_ADDR;
}

/* ⚠️ CR dn4-2 du 2026-08-24 — TIMEOUT ET NACK NE SE CONFONDENT PLUS DANS AUCUN
 * DES QUATRE LECTEURS. La triage avait ete posee dans `i2c_ecrire_nu` SEULEMENT,
 * en ecrivant que les confondre « envoyait chercher la SOUDURE alors que le bus
 * etait simplement occupe — et la soudure est irreversible ». Trois fonctions du
 * meme fichier gardaient le defaut nomme : `i2c lire` affirmait « un NACK ici »
 * INCONDITIONNELLEMENT, `i2c brut` ne disait RIEN, et `lire16` ne donnait que le
 * conseil XSHUT. ⚠️ Et la probabilite du timeout MONTE avec dn4-2 :
 * `config_verifier_et_reparer()` ajoute deux transactions a 200 ms sur le chemin
 * degrade, a la cadence de 5 s. */
static void i2c_dire_la_cause(esp_err_t err)
{
    if (err == ESP_ERR_TIMEOUT) {
        printf("  ⛔ TIMEOUT, pas un NACK : le verrou du bus n'a pas ete obtenu —\n");
        printf("     la tache capteurs (5 s), la RTC ou le GT911 (~30/s) le\n");
        printf("     tenaient. RIEN n'est parti sur le fil.\n");
        printf("     ⇒ NE PAS accuser la soudure. Reessayer.\n");
    } else if (err == ESP_ERR_NOT_FOUND) {
        printf("  un NACK : le composant n'a pas acquitte son ADRESSE. Le scan\n");
        printf("  peut l'avoir vu et le composant ne plus repondre — contact\n");
        printf("  intermittent, ou adresse partagee.\n");
    } else {
        printf("  ⚠️ cause NON CLASSEE ici — lire le code d'erreur tel quel,\n");
        printf("     ⛔ ne rien conclure sur le composant NI sur la soudure.\n");
    }
}

static int i2c_ecrire_nu(uint8_t addr, const uint8_t *o, int n)
{
    /* 🔴 CR dn4-2 du 2026-08-24 — L'AVERTISSEMENT DESTRUCTEUR N'AVAIT JAMAIS
     * QUITTE LA BRANCHE MALFORMEE, ET UN COMMENTAIRE DE CORRECTIF AFFIRMAIT LE
     * CONTRAIRE. Le bloc « ELLE PEUT CASSER UN COMPOSANT SAIN » vit dans le
     * `if (n < 1 || n > 8)` de `cmd_i2c` : il ne sort donc QUE si la commande est
     * MAL FORMEE. Ce qui avait ete ajoute sur le chemin nominal est l'autre
     * avertissement, celui des occupants du firmware — gate sur {20, 5D, 51, 77},
     * qui EXCLUT 0x23. Resultat : `i2c ecrire 23 00`, l'exemple exact que le
     * docblock donne comme destructeur, s'executait SANS UN MOT.
     * ⚠️ La verification carte de §13.17.2 avait ete faite avec `i2c ecrire 77 D0`,
     *    une adresse DANS la liste : elle confirmait la branche neuve, pas la
     *    promesse du commit. */
    if (addr == DN_BH1750_ADDR && n >= 1 && (o[0] == 0x00 || o[0] == 0x07)) {
        printf("🔴 CET OCTET EST DESTRUCTEUR SUR LE BH1750 : 0x%02X = %s.\n",
               o[0], o[0] == 0x00 ? "POWER DOWN" : "RESET du registre de donnee");
        /* 🔴 SEANCE CARTE DU 2026-08-24 — CE TEXTE DISAIT « rendra 00 00 », ET LA
         * CARTE L'A REFUTE. Le POWER DOWN n'efface PAS le registre de donnee :
         * seul 0x07 le fait. Mesure : apres `i2c lire 23 00`, trois lectures
         * consecutives ont rendu 211, 211, 211 — la DERNIERE MESURE, FIGEE — puis
         * 250, 280, 389 apres rallumage. ⇒ Le symptome n'est pas un zero, c'est
         * une VALEUR PLAUSIBLE QUI NE BOUGE PLUS, ce qui est BIEN PIRE : elle
         * passe pour une mesure. */
        if (o[0] == 0x00) {
            printf("   ⚠️ Apres lui, `i2c brut %02X 2` NE rendra PAS 00 00 : le\n",
                   DN_BH1750_ADDR);
            printf("      registre de donnee GARDE la derniere mesure (seul 0x07\n");
            printf("      le vide). ⛔ Tu liras donc une VALEUR PLAUSIBLE QUI NE\n");
            printf("      BOUGE PLUS — mesure du 2026-08-24 : 211, 211, 211.\n");
            printf("      C'est pire qu'un zero : ça passe pour une mesure.\n");
        } else {
            /* 🔴 SEANCE DU 2026-08-24, 2e REFUTATION DANS LA MEME HEURE — LE RESET
             * N'EST PAS ACCEPTE EN POWER DOWN (datasheet ROHM). Mesure : capteur
             * eteint + `i2c ecrire 23 07` -> la lecture rend TOUJOURS 209, figee.
             * Capteur ALIMENTE + 0x07 -> 00 00. La puce ACQUITTE dans les deux
             * cas : l'acquittement ne dit RIEN de l'obeissance, ce que la ligne
             * « acquitte ne veut pas dire a obei » annonçait deja. */
            printf("   ⚠️ Apres lui, `i2c brut %02X 2` rendra 00 00 — MAIS SEULEMENT\n",
                   DN_BH1750_ADDR);
            printf("      SI LE CAPTEUR EST ALIMENTE : le reset n'est PAS accepte\n");
            printf("      en power down (datasheet ROHM), et la puce ACQUITTE quand\n");
            printf("      meme. Mesure du 2026-08-24 : eteint + 0x07 -> 209 figee ;\n");
            printf("      alimente + 0x07 -> 00 00.\n");
            printf("      ⇒ En cas de doute : `i2c ecrire %02X 01` D'ABORD.\n",
                   DN_BH1750_ADDR);
        }
        printf("   ⇒ Pour le rallumer : `i2c ecrire %02X 01` puis `i2c ecrire %02X 10`.\n",
               DN_BH1750_ADDR, DN_BH1750_ADDR);
        printf("   ⚠️ L'ecriture est FAITE QUAND MEME — console de diagnostic.\n");
    }
    if (i2c_addr_est_occupee_par_le_firmware(addr)) {
        printf("🔴 0x%02X EST PILOTE PAR LE FIRMWARE : %s\n", addr,
               i2c_nom_connu(addr));
        printf("   ⛔ Une ecriture nue ici ne « teste » rien : elle DOUBLE le\n");
        printf("      pilote, qui garde son registre ombre inchange et ne le\n");
        printf("      reecrira pas. Exemples MESURABLES : 0x%02X porte LCD_RST,\n",
               DN_TCA9554_ADDR);
        printf("      TP_RST et LCD_CS (ecran noir + tactile mort jusqu'au\n");
        printf("      reboot) ; 0x%02X est la RTC dont dn3-2 depend.\n",
               DN_RTC_ADDR);
        printf("   ⚠️ On NE BLOQUE PAS — console de diagnostic, pas\n");
        printf("      garde-barriere.\n");
    }
    i2c_master_dev_handle_t dev = NULL;
    if (i2c_dev_ouvrir(addr, &dev) != ESP_OK) {
        return 1;
    }
    /* ⚠️ CR dn4-2 du 2026-08-24 — « L'ECRITURE EST FAITE QUAND MEME » ET « C'EST
     * CETTE COMMANDE » ETAIENT IMPRIMES AVANT MEME QUE L'OUVERTURE SOIT TENTEE.
     * Si `i2c_master_bus_add_device` refuse (tas interne epuise), la console avait
     * deja impute a cette commande une ecriture qui n'a JAMAIS eu lieu — soit
     * exactement la mauvaise attribution que ce bloc existe pour rendre possible.
     * ⇒ L'imputation ne sort qu'une fois le device REELLEMENT ouvert. */
    if (i2c_addr_est_occupee_par_le_firmware(addr)) {
        printf("   ⚠️ L'ecriture PART MAINTENANT sur une adresse pilotee : si\n");
        printf("      l'ecran ou le tactile meurent dans les secondes qui\n");
        printf("      suivent, C'EST CETTE COMMANDE.\n");
    }
    esp_err_t err = i2c_master_transmit(dev, o, (size_t)n, 200);
    i2c_dev_fermer(dev);

    /* 🔴 CR dn4-2 — « ENVOYE(S) » ETAIT IMPRIME AVANT DE SAVOIR SI ÇA L'ETAIT.
     * Sur ESP_ERR_TIMEOUT (verrou de bus tenu par la tache capteurs) RIEN n'est
     * parti sur le fil, et la console annonçait quand meme « 2 octet(s)
     * ENVOYE(S) ». Un `grep` sur une capture comptait donc une ecriture qui
     * n'avait pas eu lieu. Le verbe suit desormais le resultat. */
    printf("0x%02X <-", addr);
    for (int i = 0; i < n; i++) {
        printf(" %02X", o[i]);
    }
    printf("  (%d octet(s) %s)\n", n, err == ESP_OK ? "ENVOYE(S)" : "NON ENVOYE(S)");

    if (err != ESP_OK) {
        printf("ECHEC : %s\n", esp_err_to_name(err));
        /* ⚠️ CR dn4-2 : les causes ne se confondent plus — et depuis le
         * 2026-08-24 la triage est FACTORISEE, donc les QUATRE lecteurs en
         * beneficient, pas ce seul chemin. */
        i2c_dire_la_cause(err);
        return 1;
    }
    printf("  => ACQUITTE. ⚠️ « acquitte » ne veut pas dire « a obei » : rien\n");
    printf("     ne relit ce qui vient d'etre ecrit. Seule la LECTURE qui suit\n");
    printf("     (ou un stimulus physique) le prouve.\n");
    if (addr == DN_BH1750_ADDR && n == 1) {
        /* 🔴 CR dn4-2 du 2026-08-24 — LA TABLE IGNORAIT LE MODE2 ET LE MTreg, ET
         * L'AVERTISSEMENT DES 180 ms NE COUVRAIT QUE DEUX OPCODES SUR QUATRE.
         * Datasheet ROHM BH1750FVI : lux = brut / 1,2 x (69 / MTreg), et ENCORE
         * DIVISE PAR 2 en H-resolution Mode2. Or `i2c brut` applique
         * `brut x 100 / 12` INCONDITIONNELLEMENT. Deux familles d'opcodes
         * tombaient dans « NON REPERTORIE », donc SANS avertissement :
         *   - 0x11 / 0x21 (Mode2)            => valeur imprimee x2 TROP HAUTE ;
         *   - 0x40..0x47 et 0x60..0x7F (MTreg 31..254) => x2,2 a /3,7.
         * ⚠️ Et le pire etait le bloc des 180 ms, garde sur `0x10 || 0x20` : 0x11
         *    et 0x21 ont EXACTEMENT le meme temps d'integration et ne le
         *    declenchaient pas => `i2c ecrire 23 11` puis `i2c brut 23 2` dans le
         *    meme lot rend 00 00 => « capteur mort ». C'est le faux negatif que ce
         *    bloc existe pour empecher, atteignable a UN CARACTERE de l'opcode
         *    nominal. */
        bool h_res = (o[0] == 0x10 || o[0] == 0x11 ||
                      o[0] == 0x20 || o[0] == 0x21);
        bool mode2 = (o[0] == 0x11 || o[0] == 0x21);
        bool mtreg = ((o[0] & 0xE0) == 0x40) || ((o[0] & 0xE0) == 0x60);
        const char *quoi = o[0] == 0x00   ? "POWER DOWN"
                           : o[0] == 0x01 ? "POWER ON (attend une commande)"
                           : o[0] == 0x07 ? "RESET du registre de donnee"
                           : o[0] == 0x10 ? "mesure CONTINUE haute resolution "
                                            "(1 lx) — 120 ms typiques, JUSQU'A "
                                            "180 ms"
                           : o[0] == 0x11 ? "mesure CONTINUE haute resolution "
                                            "MODE2 (0,5 lx) — 120 ms typiques, "
                                            "JUSQU'A 180 ms"
                           : o[0] == 0x13 ? "mesure CONTINUE basse resolution "
                                            "(4 lx) — 16 ms typiques"
                           : o[0] == 0x20 ? "mesure ONE-SHOT haute resolution — "
                                            "120 ms typiques, JUSQU'A 180 ms"
                           : o[0] == 0x21 ? "mesure ONE-SHOT haute resolution "
                                            "MODE2 (0,5 lx) — 120 ms typiques, "
                                            "JUSQU'A 180 ms"
                           : o[0] == 0x23 ? "mesure ONE-SHOT basse resolution "
                                            "(4 lx) — 16 ms typiques"
                           : mtreg        ? "CHANGEMENT DE MTreg (temps de mesure)"
                                          : "opcode NON REPERTORIE ici";
        printf("  => BH1750, opcode 0x%02X = %s\n", o[0], quoi);
        if (mode2) {
            printf("  🔴 MODE2 : la resolution passe a 0,5 lx, donc la vraie\n");
            printf("     conversion est `brut / 1,2 / 2`. ⛔ `i2c brut %02X 2`\n",
                   DN_BH1750_ADDR);
            printf("     N'EN SAIT RIEN et publiera une valeur DEUX FOIS TROP\n");
            printf("     HAUTE — la diviser par 2 a la main.\n");
        }
        if (mtreg) {
            printf("  🔴 MTreg MODIFIE : la conversion est `brut / 1,2 x (69 /\n");
            printf("     MTreg)`, MTreg allant de 31 a 254. ⛔ `i2c brut %02X 2`\n",
                   DN_BH1750_ADDR);
            printf("     suppose TOUJOURS 69 et se trompera de x2,2 a /3,7.\n");
            printf("     ⇒ Revenir au defaut avant toute mesure publiee : 0x07\n");
            printf("        (reset) puis 0x01 puis 0x10.\n");
        }
        if (h_res) {
            printf("  🔴 NE PAS enchainer `i2c brut 23 2` DANS LE MEME LOT : le\n");
            printf("     pilote envoie le lot en quelques DIZAINES de ms, la\n");
            printf("     mesure en demande jusqu'a 180. La lecture rendrait 00 00\n");
            printf("     ou la mesure PRECEDENTE, et le capteur serait declare\n");
            printf("     mort alors qu'il fonctionne. ⇒ DEUX INVOCATIONS SEPAREES.\n");
        }
    }
    return 0;
}

/* ── `i2c brut <addr> [n]` — LECTURE SANS INDEX ─────────────────────────────
 * Le BH1750 rend sa mesure sur 2 octets SANS qu'on lui envoie quoi que ce soit ;
 * `i2c lire` ecrirait un index et le REPILOTERAIT a chaque lecture. */
static int i2c_lire_brut(uint8_t addr, int n)
{
    i2c_master_dev_handle_t dev = NULL;
    if (i2c_dev_ouvrir(addr, &dev) != ESP_OK) {
        return 1;
    }
    uint8_t rx[16] = {0};
    esp_err_t err = i2c_master_receive(dev, rx, (size_t)n, 200);
    i2c_dev_fermer(dev);
    if (err != ESP_OK) {
        printf("lecture BRUTE 0x%02X (%d o) : ECHEC (%s)\n", addr, n,
               esp_err_to_name(err));
        i2c_dire_la_cause(err);
        return 1;
    }
    printf("0x%02X brut (%d o, SANS index) :", addr, n);
    for (int i = 0; i < n; i++) {
        printf(" %02X", rx[i]);
    }
    printf("\n");
    /* Interpretation BH1750 : elle est ICI parce que la relire de tete a chaque
     * session est exactement la ou naissent les erreurs de transcription — meme
     * motif que 0xD0/0xF0 pour le BME680 ci-dessus. */
    if (addr == DN_BH1750_ADDR && n != 2) {
        /* 🔴 CR dn4-2 : avec le n par defaut (1), l'interpretation ET
         * l'avertissement « 0000 ne prouve pas un capteur mort » disparaissaient
         * en silence — or cet avertissement EST le discriminant sur lequel toute
         * la qualification par stimulus repose. */
        printf("  ⚠️ le BH1750 rend sa mesure sur DEUX octets : `i2c brut %02X 2`.\n",
               DN_BH1750_ADDR);
        printf("     Avec %d octet(s), l'interpretation en lux n'est PAS faite —\n", n);
        printf("     ⛔ ne rien conclure de ce qui precede.\n");
    }
    if (addr == DN_BH1750_ADDR && n == 2) {
        unsigned brut = ((unsigned)rx[0] << 8) | rx[1];
        /* 🔴 CR dn4-2 (2026-08-20) — CETTE CONVERSION ETAIT FAUSSE D'UN FACTEUR 10,
         * ET LE CHIFFRE ETAIT PLAUSIBLE, DONC PIRE QU'ABSURDE.
         * `(brut * 10) / 12` EST DEJA la valeur en lux ENTIERS (c'est litteralement
         * `brut / 1,2`) — elle etait ensuite imprimee comme des DIXIEMES. Mesure
         * du 2026-08-20 : `brut 55 378` a ete publie « 4 614,8 lx » dans §13.16.8
         * ET dans le README, alors que la vraie valeur est 46 148 lx. De meme
         * 1,9 pour 19,1 et 2,3 pour 23,3.
         * ⚠️ CR du 2026-08-24 : ce commentaire ecrivait « 19,2 », que l'expression
         *    ci-dessous NE PEUT PAS produire — (23 x 100) / 12 = 191 => « 19.1 ».
         *    19,2 est l'ARRONDI de 19,166..., et la ligne imprimee dit elle-meme
         *    que le dixieme est TRONQUE. Meme classe de defaut que celle que ce
         *    bloc corrige : un commentaire qui decrit une sortie que son
         *    expression ne produit pas.
         * ⚠️ AC6 tient quand meme — le stimulus qualifie par le RAPPORT, et les
         *    rapports etaient justes — mais « 4 614,8 lx sous une lampe de
         *    telephone » est exactement le chiffre faux ET plausible que ce depot
         *    dit plus dangereux qu'un chiffre absurde.
         * ⇒ Pour des DIXIEMES il faut 100 au numerateur : lux x 10 = brut x 100/12.
         *   Borne : brut <= 65 535 ⇒ 6 553 500, tient largement dans un unsigned. */
        unsigned lux10 = (brut * 100u) / 12u;
        printf("  => BH1750 : brut %u => %u.%u lx (lux = brut / 1,2 au MTreg\n",
               brut, lux10 / 10u, lux10 % 10u);
        printf("     par defaut de 69 ; le dixieme est TRONQUE, pas arrondi)\n");
        /* 🔴 CR dn4-2 du 2026-08-24 — LA LIGNE CI-DESSUS EST UNE HYPOTHESE, PAS UNE
         * MESURE INCONDITIONNELLE, ET ELLE N'EN ANNONCAIT QU'UNE SUR DEUX.
         * Aucun etat n'est conserve entre `i2c ecrire 23 <opcode>` et `i2c brut
         * 23 2` — et la doc IMPOSE justement deux invocations separees. La
         * commande ne PEUT donc pas savoir dans quel mode le capteur est. On
         * nomme les deux hypotheses au lieu d'en taire une. */
        printf("     ⚠️ SUPPOSE H-resolution Mode1 (0x10/0x20) ET MTreg = 69.\n");
        printf("        En MODE2 (0x11/0x21) la vraie valeur est la MOITIE ;\n");
        printf("        MTreg modifie (0x40..0x7F) la decale de x2,2 a /3,7.\n");
        printf("        ⛔ La commande ne conserve AUCUN etat entre invocations :\n");
        printf("           elle ne peut pas le savoir. C'est a toi de le savoir.\n");
        /* 🔴 SEANCE CARTE DU 2026-08-24 — LA TROISIEME CAUSE ETAIT FAUSSE, ET LE
         * CRITERE DE PREUVE DU DOSSIER TOMBE AVEC ELLE.
         * Ce bloc citait « un capteur en POWER DOWN » comme cause d'un 0000 :
         * MESURE, C'EST FAUX. Le power down (0x00) ne vide PAS le registre de
         * donnee — seul le reset (0x07) le fait. Un capteur eteint rend donc la
         * DERNIERE MESURE, FIGEE (211, 211, 211 en seance), c'est-a-dire une
         * valeur PLAUSIBLE. ⛔ CONSEQUENCE LOURDE : le critere de preuve de
         * §13.16.8 — « 3 lectures, identiques » — NE DISCRIMINE PAS. Il est
         * satisfait par un capteur eteint, et aussi par un bus qui lit des uns
         * (voir la garde FFFF ci-dessous). Le seul discriminant est une valeur
         * qui CHANGE. */
        printf("  ⚠️ 0000 ne prouve PAS un capteur mort : c'est aussi ce que rend\n");
        printf("     une mesure PAS ENCORE PRETE (jusqu'a 180 ms), ou un registre\n");
        printf("     VIDE par un reset 0x07, ou un capteur jamais demarre.\n");
        printf("  🔴 ET L'INVERSE EST PIRE : un capteur en POWER DOWN ne rend PAS\n");
        printf("     00 00 — il rend la DERNIERE MESURE, FIGEE (mesure du\n");
        printf("     2026-08-24 : 211, 211, 211). ⛔ « TROIS LECTURES IDENTIQUES »\n");
        printf("     N'EST DONC PAS UNE PREUVE DE VIE : un capteur eteint la\n");
        printf("     satisfait, un bus qui lit des uns aussi.\n");
        printf("     ⇒ Le SEUL discriminant est une valeur qui CHANGE quand on\n");
        printf("        masque le capteur ou qu'on l'eclaire.\n");
        /* 🔴 CR dn4-2 du 2026-08-24 — LE POLE BAS ETAIT GARDE EN SIX LIGNES, LE
         * POLE HAUT PAS DU TOUT. `FFFF` est ce que rend un bus qui lit des UNS
         * (SDA relache, module debranche a chaud), et il sort « 54612.5 lx » AVEC
         * UN DIXIEME : trois lectures consecutives IDENTIQUES, ce qui satisfait
         * LITTERALEMENT le critere de preuve du dossier (« 3, identiques »,
         * §13.16.8) et se lit comme du plein soleil. Le pole haut est atteignable
         * pour de vrai : la lampe de telephone a deja mesure 55 378, soit 84 % de
         * l'echelle. */
        if (brut == 0xFFFFu) {
            printf("  🔴 FFFF EST LE PLAFOND DE L'ECHELLE, ET C'EST AUSSI CE QUE\n");
            printf("     REND UN BUS QUI LIT DES UNS (SDA relache, module\n");
            printf("     debranche). ⛔ NE PAS lire « plein soleil » : la valeur\n");
            printf("     ci-dessus serait IDENTIQUE a chaque lecture, donc le\n");
            printf("     critere « 3 lectures identiques » ne discrimine PAS ici.\n");
            printf("     ⇒ Le discriminant reste le STIMULUS : masquer le capteur\n");
            printf("        DOIT faire chuter la valeur. Si elle reste FFFF, c'est\n");
            printf("        le BUS, pas la lumiere.\n");
        }
    }
    return 0;
}

/* ── `i2c rafale <ms>` — SATURATION DU BUS, l'instrument d'AC9 (dn4-2) ──────
 *
 * 🔴 POURQUOI IL EXISTE : D9 a soude les capteurs, donc AC7 (a) de dn2-1 — le
 *    tactile pendant une perturbation ELECTRIQUE du bus — ne peut plus se
 *    rejouer en debranchant un fil. La variante logicielle (saturer le bus de
 *    sondages pendant que l'owner appuie) « n'est plus l'information marginale
 *    qu'elle etait le 17/08 : c'est la seule voie restante ».
 *
 * ⛔ POURQUOI CE N'EST PAS `i2c` DANS UNE BOUCLE HOTE : `i2c` est une passe
 *    UNIQUE et BLOQUANTE qui IMPRIME. Une boucle cote `dn_console.py` ferait
 *    passer chaque passe par le REPL — donc par le transport — et noierait la
 *    capture. Pire : T0 de dn4-2 a mesure que le pilote PERD DES LIGNES quand on
 *    lui passe plusieurs commandes (6 captures sur 20, §13.16.2). L'instrument
 *    d'AC9 ne pouvait donc pas etre une boucle hote.
 *
 * ⚠️ ELLE BLOQUE LE REPL PENDANT TOUTE SA FENETRE, et c'est VOULU : l'owner
 *    appuie sur la dalle, il ne tape pas. La fenetre est BORNEE et ANNONCEE, et
 *    l'appelant doit passer `--timeout` en consequence — sinon le pilote annonce
 *    une carte muette sur une carte qui va parfaitement bien (piege mesure en
 *    dn2-2 avec `cpu 30`).
 *
 * ⚠️ AUCUNE ECRITURE DE DONNEE : `i2c_master_probe()` n'emet qu'une adresse et
 *    lit l'acquittement, borne a 0x08..0x77 donc hors adresses reservees. Aucun
 *    risque electrique ni thermique — c'est ecrit pour que personne n'ait a le
 *    re-etablir en seance.
 *
 * 🔴 CR dn4-2 — CE N'EST PAS 400 kHz, C'EST 100 kHz, ET LES CADENCES PUBLIEES
 *    D'AC9 DECRIVENT ÇA. `i2c_master_probe()` REPROGRAMME le timing du bus a
 *    100 000 Hz a chaque appel, inconditionnellement (esp_driver_i2c/
 *    i2c_master.c:1391, commente « I2C probe does not have i2c device module »).
 *    ⚠️ Sans effet DURABLE — chaque transaction de device reapplique son propre
 *    `scl_speed_hz` (:703, verifie) — mais le sondage est TOUT ce que cette
 *    commande fait. Le depot connaissait deja la distinction : dn_capteurs.c dit
 *    « 400 kHz et non les 100 kHz par defaut du composant ».
 *
 * ⛔ CR dn4-2 — « ELLE N'IMPRIME RIEN AVANT LA FIN » ETAIT FAUX : le driver IDF
 *    emet lui-meme un ESP_LOGE(« probe device timeout … ») PAR SONDAGE EXPIRE
 *    (i2c_master.c:1404), plus « I2C software/hardware timeout ». Sur un bus
 *    perturbe — la condition meme que la rafale cree — ça NOIE la capture.
 *
 * ⛔ ELLE N'IMPRIME RIEN ELLE-MEME AVANT LA FIN : imprimer par passe noierait la
 *    capture et changerait la cadence qu'on pretend mesurer. ⚠️ Le DRIVER, lui,
 *    imprime — voir ci-dessus — et c'est pour ça que les timeouts sont COMPTES.
 */
#define DN_I2C_RAFALE_MS_MIN 1000
#define DN_I2C_RAFALE_MS_MAX 30000
static int i2c_rafale(int duree_ms)
{
    i2c_master_bus_handle_t bus = dn_display_i2c_bus();
    if (!bus) {
        printf("bus I2C absent — dn_display_init() n'a pas tourne\n");
        return 1;
    }
    printf("rafale de sondages sur 0x08..0x77 pendant %d ms — le REPL est BLOQUE\n",
           duree_ms);
    printf("⚠️ APPUYER SUR LA DALLE MAINTENANT. Aucune ecriture de donnee n'est\n");
    printf("   emise : que des adresses. ⛔ A 100 kHz, PAS 400 : le sondage IDF\n");
    printf("   reprogramme le bus a 100 kHz (i2c_master.c:1391). CR dn4-2.\n");

    int64_t t0 = esp_timer_get_time();
    int64_t fin = t0 + (int64_t)duree_ms * 1000;
    uint32_t passes = 0, sondages = 0, acquits = 0, timeouts = 0;
    /* 🔴 CR dn4-2 — TEMOIN POSITIF, SUR LE MODELE DU SCAN.
     * Sans lui, un bus coince rendait « sondages eleve, acquits 0, timeouts 0 »
     * et le rapport se lisait comme une campagne complete a haute cadence : la
     * CADENCE publiee — le seul nombre sur lequel AC9 tourne — aurait ete une
     * cadence de NACKs. Le scan, lui, se declare instrument casse quand 0x20 et
     * 0x5D manquent ; la rafale n'attendait RIEN de personne. */
    uint32_t vus_tca = 0, vus_gt911 = 0;
    /* 🔴 CR dn4-2 — LA BUTEE EST TESTEE PAR ADRESSE, PAS PAR PASSE.
     * Elle ne l'etait qu'entre passes completes : une passe entamee a une
     * microseconde de la fin allait jusqu'au bout, soit 112 sondages a
     * DN_I2C_SCAN_TIMEOUT_MS chacun. Le depassement grandit EXACTEMENT quand les
     * sondages expirent, c'est-a-dire dans la condition de bus perturbe que la
     * rafale existe pour creer — et l'operateur avait dimensionne `--timeout` sur
     * la fenetre ANNONCEE. Le scan voisin a ce garde-fou depuis le CR de dn2-1
     * (DN_I2C_SCAN_BUDGET_MS) ; la rafale l'avait perdu en bloquant 12x plus
     * longtemps. ⚠️ La passe interrompue est COMPTEE COMME PARTIELLE, pas comme
     * complete : une passe tronquee qui compterait pour une entiere fausserait
     * la cadence, et une cadence fausse est le nombre qu'AC9 publie. */
    /* 🔴 CR dn4-2 du 2026-08-24 — LE TEMOIN COMPTAIT LA PASSE TRONQUEE AU
     * NUMERATEUR ET L'EXCLUAIT DU DENOMINATEUR. `vus_tca`/`vus_gt911`
     * s'incrementaient DANS la boucle d'adresses, donc aussi pendant la passe
     * interrompue, alors que `passes++` etait saute par le `break`. Le temoin
     * pouvait donc imprimer « 0x20 vu 1301/1300 » — numerateur > denominateur —
     * et `vus_tca < passes` devenait faux, ce qui MASQUAIT un manque par temoin
     * sur la fenetre. Verifiable sur le releve publie : 147 922 = 1320 x 112 + 82,
     * et la passe tronquee a balaye 0x08..0x59, qui CONTIENT 0x20 mais PAS 0x5D
     * => les deux taux de faux negatifs de §13.17.6 reposaient sur des bases
     * differentes. Le commentaire du correctif avait traite ce cas pour la
     * CADENCE et pas pour les deux compteurs ajoutes dans le meme commit.
     * ⇒ On accumule par passe, et on ne COMMET que si la passe est COMPLETE.
     * ⛔ Distinct du defaut deja declare (« le temoin exige 100 % ») : ici c'est
     *   le DECOMPTE, pas le seuil. */
    bool coupe_en_passe = false;
    while (esp_timer_get_time() < fin) {
        bool vu_tca_passe = false;
        bool vu_gt911_passe = false;
        for (uint8_t a = 0x08; a <= 0x77; a++) {
            if (esp_timer_get_time() >= fin) {
                coupe_en_passe = true;
                break;
            }
            esp_err_t e = i2c_master_probe(bus, a, DN_I2C_SCAN_TIMEOUT_MS);
            sondages++;
            if (e == ESP_OK) {
                acquits++;
                if (a == DN_TCA9554_ADDR) {
                    vu_tca_passe = true;
                    /* ⚠️ CR du 2026-08-24 — le temoin ignorait DN_GT911_ADDR_BACKUP
                     * alors que le scan voisin le traite a EGALITE. Sur une carte
                     * partie INT haut, il rendait 0/N et declarait « AUCUNE
                     * conclusion d'AC9 recevable » SUR UN BUS PARFAITEMENT SAIN. */
                } else if (a == DN_GT911_ADDR || a == DN_GT911_ADDR_BACKUP) {
                    vu_gt911_passe = true;
                }
            } else if (e == ESP_ERR_TIMEOUT) {
                timeouts++;
            }
        }
        if (coupe_en_passe) {
            break;
        }
        if (vu_tca_passe) {
            vus_tca++;
        }
        if (vu_gt911_passe) {
            vus_gt911++;
        }
        passes++;
    }
    int64_t reel_us = esp_timer_get_time() - t0;
    int64_t reel_ms = reel_us / 1000;

    printf("--- rafale ------------------------------------------------\n");
    printf("  duree DEMANDEE  : %d ms\n", duree_ms);
    printf("  duree REELLE    : %lld ms\n", (long long)reel_ms);
    printf("  passes completes: %lu\n", (unsigned long)passes);
    printf("  sondages emis   : %lu\n", (unsigned long)sondages);
    if (reel_ms > 0) {
        printf("  CADENCE         : %lld sondages/s  (%lld passes/s)\n",
               (long long)((int64_t)sondages * 1000 / reel_ms),
               (long long)((int64_t)passes * 1000 / reel_ms));
    }
    printf("  acquittements   : %lu\n", (unsigned long)acquits);
    printf("  timeouts        : %lu\n", (unsigned long)timeouts);
    if (coupe_en_passe) {
        printf("  ⚠️  derniere passe INTERROMPUE par la butee — elle n'est PAS\n");
        printf("     comptee dans « passes completes ». C'est voulu : une passe\n");
        printf("     tronquee comptee entiere fausserait la CADENCE.\n");
        printf("     ⇒ Ses acquittements ne comptent PAS non plus dans le temoin\n");
        printf("        ci-dessous (CR du 2026-08-24 : ils y comptaient, ce qui\n");
        printf("        pouvait rendre un temoin a 1301/1300 et masquer un manque).\n");
    }
    /* Le temoin positif se lit AVANT toute conclusion, comme pour le scan. */
    printf("  temoin positif  : 0x%02X vu %lu/%lu passes · 0x%02X vu %lu/%lu\n",
           DN_TCA9554_ADDR, (unsigned long)vus_tca, (unsigned long)passes,
           DN_GT911_ADDR, (unsigned long)vus_gt911, (unsigned long)passes);
    if (passes == 0 || vus_tca < passes || vus_gt911 < passes) {
        printf("🔴 TEMOIN POSITIF EN ECHEC — les deux devices SOUDES auraient du\n");
        printf("   acquitter a CHAQUE passe. ⛔ AUCUNE conclusion d'AC9 n'est\n");
        printf("   recevable sur cette fenetre : la cadence ci-dessus pourrait\n");
        printf("   etre une cadence de NACKs sur un bus coince.\n");
        printf("   ⚠️ Verifier d'abord que le compteur de timeouts est alimente\n");
        printf("      (piege d'instrument deja mesure) avant d'accuser le bus.\n");
    }
    printf("⚠️ ces compteurs decrivent la RAFALE, pas le tactile. Le verdict\n");
    printf("   d'AC9 se lit dans `touch` AVANT et APRES — et dans ce que\n");
    printf("   l'owner RESSENT : un compteur ne peut pas repondre a « le\n");
    printf("   tactile est-il fache ».\n");
    printf("-----------------------------------------------------------\n");
    return 0;
}

/* ── `i2c lire16 <addr> <reg16> [n]` — INDEX DE REGISTRE SUR 2 OCTETS ───────
 * MSB d'abord, comme l'exige le VL6180X (ST, IDENTIFICATION__MODEL_ID). */
static int i2c_lire_registre16(uint8_t addr, uint16_t reg, int n)
{
    i2c_master_dev_handle_t dev = NULL;
    if (i2c_dev_ouvrir(addr, &dev) != ESP_OK) {
        return 1;
    }
    uint8_t idx[2] = {(uint8_t)(reg >> 8), (uint8_t)(reg & 0xFF)};
    uint8_t rx[16] = {0};
    esp_err_t err = i2c_master_transmit_receive(dev, idx, 2, rx, (size_t)n, 200);
    i2c_dev_fermer(dev);
    if (err != ESP_OK) {
        printf("lecture 0x%02X reg16 0x%04X : ECHEC (%s)\n", addr, reg,
               esp_err_to_name(err));
        /* 🔴 CR dn4-2 — LE CONSEIL EST GARDE PAR L'ADRESSE. Il partait pour
         * N'IMPORTE QUELLE adresse, et conseillait donc « verifier XSHUT » a
         * propos d'un INA219.
         * ⚠️ CR du 2026-08-24 — CE COMMENTAIRE ENUMERAIT FAUX. Il disait
         *    « `i2c ecrire` et `i2c brut` testent tous deux addr == 0x23 ;
         *    lire16 etait la seule a ne rien tester » : il OUBLIAIT
         *    `i2c_lire_registre`, qui ne testait rien NON PLUS — et c'est
         *    justement la plus dangereuse, puisqu'elle ECRIT un octet d'index.
         *    Les quatre testent desormais l'adresse.
         * ⚠️ Et le conseil XSHUT partait aussi sur un TIMEOUT de verrou : la
         *    cause est nommee AVANT, par le helper commun. */
        i2c_dire_la_cause(err);
        if (addr == DN_VL6180X_ADDR && err != ESP_ERR_TIMEOUT) {
            printf("  ⚠️ AVANT d'accuser la soudure : sur un VL6180X, `XSHUT` bas ou\n");
            printf("     FLOTTANT laisse la puce en SHUTDOWN — elle N'ACQUITTE PAS,\n");
            printf("     et c'est le symptome EXACT d'une mauvaise soudure.\n");
        }
        return 1;
    }
    printf("0x%02X reg16 0x%04X :", addr, reg);
    for (int i = 0; i < n; i++) {
        printf(" %02X", rx[i]);
    }
    printf("\n");
    /* 🔴 CR dn4-2 — LE VERDICT EST GARDE PAR L'ADRESSE. Sans ce test, l'octet
     * rendu par un device qui n'a JAMAIS ete un ToF etait etiquete
     * « IDENTIFICATION__MODEL_ID … ⛔ PAS un VL6180X … REMONTEE OWNER » :
     * un verdict faux ET plausible, qui escalade. C'est exactement ce que
     * l'en-tete de cette section dit que la separation en commandes evite. */
    if (addr == DN_VL6180X_ADDR && reg == 0x0000 && n >= 1) {
        printf("  => IDENTIFICATION__MODEL_ID = 0x%02X = %s\n", rx[0],
               rx[0] == 0xB4 ? "✅ VL6180X — c'est bien le TOF050C-VL6180X"
                             : "⛔ PAS un VL6180X (attendu B4). Temoin negatif : "
                               "`i2c lire 29 C0` — s'il rend EE de facon "
                               "REPRODUCTIBLE, c'est un VL53L0X et le sachet ment "
                               "=> REMONTEE OWNER, pas un choix de dev");
    }
    return 0;
}

static int cmd_i2c(int argc, char **argv)
{
    if (argc >= 2 && strcmp(argv[1], "lire") == 0) {
        if (argc != 4 && argc != 5) {
            printf("usage : i2c lire <addr hex> <registre hex> [n=1..16]\n");
            printf("        ex. : i2c lire 76 D0   (chip id)\n");
            printf("              i2c lire 76 F0   (variant BME680/BME688)\n");
            return 1;
        }
        uint8_t addr, reg;
        if (!parse_adresse_i2c(argv[2], &addr)) {
            printf("adresse « %s » refusee : hexa, entre 08 et 77 (0x00-0x07 et\n",
                   argv[2]);
            printf("0x78-0x7F sont RESERVEES par la specification I2C)\n");
            return 1;
        }
        long r = 0;
        if (!parse_hex_strict(argv[3], &r) || r < 0 || r > 0xFF) {
            printf("registre « %s » refuse : hexa SANS « 0x », entre 00 et FF\n",
                   argv[3]);
            return 1;
        }
        reg = (uint8_t)r;
        long n = 1;
        if (argc == 5 && (!parse_entier(argv[4], &n) || n < 1 || n > 16)) {
            printf("nombre d'octets « %s » refuse : entre 1 et 16\n", argv[4]);
            return 1;
        }
        return i2c_lire_registre(addr, reg, (int)n);
    }

    /* ── `i2c lire16 <addr> <reg16 hex> [n]` — index sur 2 octets (VL6180X) ── */
    if (argc >= 2 && strcmp(argv[1], "lire16") == 0) {
        if (argc != 4 && argc != 5) {
            printf("usage : i2c lire16 <addr hex> <registre hex 0000..FFFF> "
                   "[n=1..16]\n");
            printf("        ex. : i2c lire16 29 0000   (VL6180X : attendu B4)\n");
            return 1;
        }
        uint8_t addr;
        if (!parse_adresse_i2c(argv[2], &addr)) {
            printf("adresse « %s » refusee : hexa, entre 08 et 77 (0x00-0x07 et\n",
                   argv[2]);
            printf("0x78-0x7F sont RESERVEES par la specification I2C)\n");
            return 1;
        }
        long r = 0;
        if (!parse_hex_strict(argv[3], &r) || r < 0 || r > 0xFFFF) {
            printf("registre « %s » refuse : hexa SANS « 0x », entre 0000 et FFFF\n",
                   argv[3]);
            return 1;
        }
        long n = 1;
        if (argc == 5 && (!parse_entier(argv[4], &n) || n < 1 || n > 16)) {
            printf("nombre d'octets « %s » refuse : entre 1 et 16\n", argv[4]);
            return 1;
        }
        return i2c_lire_registre16(addr, (uint16_t)r, (int)n);
    }

    /* ── `i2c brut <addr> [n]` — lecture SANS index (BH1750) ───────────────── */
    if (argc >= 2 && strcmp(argv[1], "brut") == 0) {
        if (argc != 3 && argc != 4) {
            printf("usage : i2c brut <addr hex> [n=1..16]\n");
            printf("        ex. : i2c brut 23 2   (BH1750 : 2 octets de mesure)\n");
            return 1;
        }
        uint8_t addr;
        if (!parse_adresse_i2c(argv[2], &addr)) {
            printf("adresse « %s » refusee : hexa, entre 08 et 77 (0x00-0x07 et\n",
                   argv[2]);
            printf("0x78-0x7F sont RESERVEES par la specification I2C)\n");
            return 1;
        }
        long n = 1;
        if (argc == 4 && (!parse_entier(argv[3], &n) || n < 1 || n > 16)) {
            printf("nombre d'octets « %s » refuse : entre 1 et 16\n", argv[3]);
            return 1;
        }
        return i2c_lire_brut(addr, (int)n);
    }

    /* ── `i2c ecrire <addr> <o1> [o2..o8]` — ECRITURE NUE ──────────────────── */
    if (argc >= 2 && strcmp(argv[1], "ecrire") == 0) {
        /* argv[0]=i2c argv[1]=ecrire argv[2]=addr argv[3..]=octets */
        int n = argc - 3;
        if (n < 1 || n > 8) {
            printf("usage : i2c ecrire <addr hex> <o1 hex> [o2..o8]\n");
            printf("        ex. : i2c ecrire 23 01   (BH1750 : power on)\n");
            printf("              i2c ecrire 23 10   (BH1750 : continu H-res)\n");
            printf("⚠️ ELLE ECRIT SANS LIRE, et elle PEUT CASSER UN COMPOSANT\n");
            printf("   SAIN : sur le BH1750, 00 = power down et 07 = reset.\n");
            printf("de 1 a 8 octets — « %d » refuse\n", n < 1 ? 0 : n);
            return 1;
        }
        uint8_t addr;
        if (!parse_adresse_i2c(argv[2], &addr)) {
            printf("adresse « %s » refusee : hexa, entre 08 et 77 (0x00-0x07 et\n",
                   argv[2]);
            printf("0x78-0x7F sont RESERVEES par la specification I2C)\n");
            return 1;
        }
        uint8_t o[8] = {0};
        for (int i = 0; i < n; i++) {
            long v = 0;
            if (!parse_hex_strict(argv[3 + i], &v) || v < 0 || v > 0xFF) {
                printf("octet n°%d « %s » refuse : hexa SANS « 0x », entre 00 et FF\n",
                       i + 1, argv[3 + i]);
                printf("⛔ RIEN N'A ETE ENVOYE — la commande refuse AVANT d'ecrire,\n");
                printf("   parce qu'une ecriture partielle sur un capteur laisse\n");
                printf("   un etat qu'on ne sait pas nommer.\n");
                return 1;
            }
            o[i] = (uint8_t)v;
        }
        return i2c_ecrire_nu(addr, o, n);
    }

    /* ── `i2c rafale <ms>` — saturation du bus (AC9 de dn4-2) ─────────────── */
    if (argc >= 2 && strcmp(argv[1], "rafale") == 0) {
        long ms = 0;
        if (argc != 3 || !parse_entier(argv[2], &ms) || ms < DN_I2C_RAFALE_MS_MIN ||
            ms > DN_I2C_RAFALE_MS_MAX) {
            printf("usage : i2c rafale <ms=%d..%d>\n", DN_I2C_RAFALE_MS_MIN,
                   DN_I2C_RAFALE_MS_MAX);
            printf("        ex. : i2c rafale 20000   (20 s de sondages en rafale)\n");
            printf("⚠️ elle BLOQUE le REPL pendant toute sa fenetre — c'est voulu,\n");
            printf("   l'owner appuie sur la dalle. Passer `--timeout` en\n");
            printf("   consequence, sinon le pilote annonce une carte muette sur\n");
            printf("   une carte qui va parfaitement bien.\n");
            printf("⛔ borne HAUTE a %d ms : au-dela, le transport PC serait coupe\n",
                   DN_I2C_RAFALE_MS_MAX);
            printf("   trop longtemps. Enchainer plusieurs fenetres si besoin.\n");
            return 1;
        }
        return i2c_rafale((int)ms);
    }

    if (argc != 1) {
        printf("usage : i2c\n");
        printf("        i2c lire   <addr> <registre>       [n=1..16]  index 8 bits\n");
        printf("        i2c lire16 <addr> <registre 16 b>  [n=1..16]  index 16 bits\n");
        printf("        i2c brut   <addr>                  [n=1..16]  SANS index\n");
        printf("        i2c ecrire <addr> <o1> [o2..o8]               SANS lecture\n");
        printf("        i2c rafale <ms=1000..30000>        saturation du bus (AC9)\n");
        printf("⚠️ ADRESSES, REGISTRES et OCTETS en HEXA, sans « 0x » — et\n");
        printf("   les parseurs le REFUSENT desormais (CR du 2026-08-24 : ils\n");
        printf("   l'acceptaient en silence sous une banniere qui l'interdit).\n");
        printf("⛔ mais `n` et `ms` sont en DECIMAL — CR dn4-2 : la banniere\n");
        printf("   disait « tout est en HEXA », et `i2c brut 23 12` lit 12\n");
        printf("   octets, pas 18. Les deux lectures tombant dans les bornes,\n");
        printf("   RIEN ne le signalait.\n");
        printf("🔴 le scan DECOUVRE, seule une transaction de DONNEE QUALIFIE.\n");
        return 1;
    }

    i2c_master_bus_handle_t bus = dn_display_i2c_bus();
    if (!bus) {
        printf("bus I2C absent — dn_display_init() n'a pas tourne\n");
        return 1;
    }

    printf("scan du bus I2C UNIQUE (SDA=GPIO%d, SCL=GPIO%d), adresses 0x08..0x77\n",
           DN_PIN_I2C_SDA, DN_PIN_I2C_SCL);
    printf("chaque adresse trouvee est RE-SONDEE %d fois — voir l'en-tete du\n",
           DN_I2C_SCAN_CONFIRMATIONS);
    printf("code : un scan a une seule passe fabrique des FAUX POSITIFS.\n");
    printf("⚠️ le REPL est bloque pendant le scan : sur la branche A, c'est le\n");
    printf("   transport PC qui attend.\n");

    int64_t t0 = esp_timer_get_time();
    uint8_t candidats[DN_I2C_SCAN_MAX_TROUVES];
    int n_cand = 0;
    int timeouts = 0, deborde = 0;
    uint8_t abandon_a = 0; /* 0 = le balayage est alle au bout */

    for (uint8_t a = 0x08; a <= 0x77; a++) {
        if ((esp_timer_get_time() - t0) / 1000 > DN_I2C_SCAN_BUDGET_MS) {
            abandon_a = a; /* voir DN_I2C_SCAN_BUDGET_MS : on le DIT, plus bas */
            break;
        }
        esp_err_t e = i2c_master_probe(bus, a, DN_I2C_SCAN_TIMEOUT_MS);
        if (e == ESP_ERR_TIMEOUT) {
            /* ⚠️ UNE ADRESSE NON SONDEE N'EST PAS UNE ADRESSE ABSENTE. Sans ce
             * compteur, la liste se lit comme exhaustive alors qu'elle a des
             * trous — l'instrument mentirait par omission. */
            timeouts++;
            continue;
        }
        if (e != ESP_OK) {
            continue;
        }
        if (n_cand >= DN_I2C_SCAN_MAX_TROUVES) {
            deborde++;
            continue;
        }
        candidats[n_cand++] = a;
    }

    bool vu_expander = false, vu_gt911 = false;
    int stables = 0, instables = 0;
    for (int i = 0; i < n_cand; i++) {
        uint8_t a = candidats[i];
        int oks = 1; /* la detection initiale compte pour une */
        for (int k = 1; k < DN_I2C_SCAN_CONFIRMATIONS; k++) {
            /* 🔴 CR 2026-08-17 — LES TIMEOUTS DE CETTE BOUCLE ETAIENT INVISIBLES.
             * Seul `ESP_OK` etait compte ; un ESP_ERR_TIMEOUT etait fondu dans
             * « non confirme » et n'atteignait JAMAIS le compteur `timeouts`, qui
             * n'etait alimente que par la passe de decouverte. Scenario reel : la
             * tache capteur tient le bus dans sa boucle de 1 500 ms, le scan sort
             * 0x5D en « 2/5 INSTABLE », le verdict imprime « TEMOIN POSITIF EN
             * ECHEC — le BUS est en cause »… et le bloc qui aurait explique
             * pourquoi reste MUET, parce que `timeouts == 0` le conditionne. La
             * phrase « une adresse absente ne prouve rien tant que ce compteur
             * n'est pas a 0 » se lisait alors comme un feu vert. */
            esp_err_t ec = i2c_master_probe(bus, a, DN_I2C_SCAN_TIMEOUT_MS);
            if (ec == ESP_OK) {
                oks++;
            } else if (ec == ESP_ERR_TIMEOUT) {
                timeouts++;
            }
        }
        bool stable = (oks == DN_I2C_SCAN_CONFIRMATIONS);
        if (stable) {
            stables++;
            if (a == DN_TCA9554_ADDR) {
                vu_expander = true;
            }
            if (a == DN_GT911_ADDR || a == DN_GT911_ADDR_BACKUP) {
                vu_gt911 = true;
            }
        } else {
            instables++;
        }
        printf("  0x%02X  %d/%d  %s%s\n", a, oks, DN_I2C_SCAN_CONFIRMATIONS,
               stable ? "" : "⚠️ INSTABLE — ", i2c_nom_connu(a));
    }
    int64_t duree_ms = (esp_timer_get_time() - t0) / 1000;
    printf("%d stable(s), %d instable(s) en %lld ms\n", stables, instables,
           (long long)duree_ms);

    if (timeouts > 0) {
        printf("🔴 %d sondage(s) N'ONT PAS ABOUTI (timeout du verrou de bus, %d ms),\n",
               timeouts, DN_I2C_SCAN_TIMEOUT_MS);
        printf("   decouverte ET confirmations confondues. La liste ci-dessus a des\n");
        printf("   TROUS : une adresse absente ne prouve rien, et un « n/%d » bas\n",
               DN_I2C_SCAN_CONFIRMATIONS);
        printf("   peut n'etre qu'un bus occupe — pas un mauvais contact. Le bus est\n");
        printf("   partage : le GT911 le prend ~30x/s et la tache capteur peut le\n");
        printf("   tenir jusqu'a 1 500 ms. Reessayer, puis `i2c lire <addr> D0`.\n");
    }
    if (abandon_a != 0) {
        printf("🔴 SCAN INTERROMPU a 0x%02X : budget de %d ms depasse. Les adresses\n",
               abandon_a, DN_I2C_SCAN_BUDGET_MS);
        printf("   0x%02X..0x77 N'ONT PAS ETE SONDEES — elles ne sont pas « absentes »,\n",
               abandon_a);
        printf("   elles n'ont pas ete regardees. Le REPL est le transport PC : le\n");
        printf("   bloquer plus longtemps couperait la liaison (lecon `cpu N`).\n");
    }
    if (deborde > 0) {
        printf("🔴 %d adresse(s) au-dela de %d IGNOREES — table pleine. Ce n'est\n",
               deborde, DN_I2C_SCAN_MAX_TROUVES);
        printf("   pas un bus charge, c'est un bus qui acquitte n'importe quoi.\n");
    }
    if (instables > 0) {
        printf("⚠️ une adresse INSTABLE est soit un FAUX POSITIF du sondage, soit\n");
        printf("   un composant au CONTACT INTERMITTENT (fil mal enfonce, broche\n");
        printf("   non soudee). Les deux se ressemblent ICI ; ce qui les separe,\n");
        printf("   c'est `i2c lire <addr> D0` : un faux positif n'a aucun registre.\n");
    }

    /* LE VERDICT SUR L'INSTRUMENT LUI-MEME. Sans lui, une liste vide se lit
     * « aucun capteur » alors qu'elle peut dire « le bus est mort ». */
    if (vu_expander && vu_gt911) {
        printf("✅ temoin positif OK : l'expander ET le tactile repondent de\n");
        printf("   maniere STABLE — le scan est credible, ce qu'il montre compte.\n");
    } else {
        printf("🔴 TEMOIN POSITIF EN ECHEC : expander %s · tactile %s.\n",
               vu_expander ? "stable" : "ABSENT ou INSTABLE",
               vu_gt911 ? "stable" : "ABSENT ou INSTABLE");
        printf("   Le BUS est en cause, pas un capteur. AUCUNE conclusion sur un\n");
        printf("   composant neuf n'est recevable. Debrancher ce qui vient d'etre\n");
        printf("   ajoute, puis `reboot`.\n");
    }
    return 0;
}


/*
 * ══════════════════════════════════════════════════════════════════════════════
 *  `tof` — L'INSTRUMENT DE dn4-7 (P9.3b). SR03, LE BALAYAGE, ET LA PORTEE.
 * ══════════════════════════════════════════════════════════════════════════════
 *
 * 🔴 POURQUOI UN INSTRUMENT PLUTOT QUE ~40 COMMANDES TAPEES — le choix est
 *    exige par AC1 « avec son motif », le voici :
 *
 *   1. La sequence fait 40 ecritures. Et ST ecrit (AN4545 §1.3, Note) :
 *      « This procedure must be repeated if the VL6180X has been power cycled ».
 *      Une campagne de portee, c'est des dizaines de cycles d'alimentation ⇒
 *      des CENTAINES de lignes tapees, sur un bus dont §13.17.1 a MESURE qu'il
 *      lache les transferts multi-octets a froid. L'instrument deviendrait la
 *      premiere source d'erreur de la mesure.
 *   2. `i2c ecrire16` NE REGLE PAS ça : il raccourcit chaque ligne, il n'en
 *      supprime aucune. C'est la mauvaise granularite.
 *   3. Une table DANS LE SOURCE porte sa citation et se relit en revue. Une
 *      sequence tapee ne laisse aucune trace verifiable.
 *   4. Elle reste HORS du chemin de regime : `dn_env` n'est pas touche tant que
 *      T1 n'a pas reussi (Dev Notes de la story). Si T1 echoue, ce bloc part
 *      d'un seul tenant.
 *
 * ⚠️ POURQUOI ICI ET PAS DANS UN MODULE NEUF : `i2c_dev_fermer()` porte le
 *    correctif de revue dn4-2 sur la course avec le sondage GT911 (~30/s). Un
 *    module separe devrait le dupliquer ⇒ deux sources de verite sur exactement
 *    ce qui venait d'etre durci. On reutilise, on ne recopie pas.
 *
 * ── LES SOURCES, CITEES AVEC LEUR DATE (AC1) ─────────────────────────────────
 *
 *  [AN] AN4545 « VL6180X basic ranging application note », STMicroelectronics,
 *       DocID026571 Rev 1, juin 2014, §9 « SR03 settings », p. 24-25.
 *  [DS] VL6180X « Proximity and ambient light sensing (ALS) module », datasheet
 *       STMicroelectronics, DocID026171 Rev 7, mars 2016.
 *
 * 🔴 PROVENANCE — ECRITE PARCE QU'ELLE N'EST PAS BANALE : `st.com` est
 *    INJOIGNABLE depuis ce poste (deja constate en dn4-3). La cause est
 *    maintenant NOMMEE : ce n'est pas une panne reseau — le handshake TLS
 *    ABOUTIT, puis le serveur casse le flux (`HTTP/2 stream 1 was not closed
 *    cleanly: INTERNAL_ERROR`), et en HTTP/1.1 force il expire sans un octet.
 *    Le meme appel depuis Windows (hors WSL) expire aussi ⇒ ⛔ ce n'est PAS WSL.
 *    Les deux documents viennent donc de MIROIRS, et leur identite est
 *    VERIFIEE, pas supposee :
 *      · [AN] telecharge DEUX FOIS depuis deux hebergeurs independants
 *        (cdn.sparkfun.com et pololu.com) ⇒ sha256 IDENTIQUE
 *        091291adc9812852e4206f4bf33a6a1646a51c1c9d92bf5c4b00d1ee5efabbab.
 *        Metadonnees PDF : Author=STMICROELECTRONICS, Keywords porte « 026571 ».
 *      · [DS] pololu.com, sha256 87e1b09668160d71…, Author=STMICROELECTRONICS,
 *        Keywords porte « 026171 », 87 pages.
 * ⚠️ ET UN PIEGE RENCONTRE, ECRIT POUR QU'IL NE SE REJOUE PAS : deux autres
 *    URL Pololu rendaient un PDF ST authentique en HTTP 200… du VL53L0X. Le
 *    code 200 et le nom de fichier MENTAIENT tous les deux ; seule la lecture
 *    du titre l'a vu. C'est exactement la confusion que §13.16.7 avait deja
 *    tranchee une fois.
 */

/* ── Registres [DS] §6.2 / Table 28, ⛔ AUCUN de memoire ────────────────────── */
#define TOF_REG_MODEL_ID     0x0000u /* [DS] 6.2.1  — attendu 0xB4              */
#define TOF_REG_INT_CONFIG   0x0014u /* [DS] 6.2.12 SYSTEM__INTERRUPT_CONFIG    */
#define TOF_REG_INT_CLEAR    0x0015u /* [DS] 6.2.13 [2:0] b0 range b1 als b2 err*/
#define TOF_REG_FRESH_RESET  0x0016u /* [DS] 6.2.14 — ⛔ LU, JAMAIS ECRIT       */
#define TOF_REG_RANGE_START  0x0018u /* [DS] 6.2.16 b0 startstop b1 mode        */
#define TOF_REG_MAX_CONV     0x001Cu /* [DS] 6.2.20 [5:0] 1..63 ms, reset 0x31  */
#define TOF_REG_ALS_START    0x0038u /* [DS] 6.2.31                             */
#define TOF_REG_ALS_GAIN     0x003Fu /* [DS] 6.2.35                             */
#define TOF_REG_ALS_INTEG_HI 0x0040u /* [DS] 6.2.36 — registre 16 b, champ [8:0]*/
#define TOF_REG_ALS_INTEG_LO 0x0041u
#define TOF_REG_RANGE_STATUS 0x004Du /* [DS] 6.2.37 [7:4] code d'erreur         */
#define TOF_REG_INT_STATUS   0x004Fu /* [DS] 6.2.39 [2:0] range, [5:3] als      */
#define TOF_REG_ALS_VAL      0x0050u /* [DS] 6.2.40 — 16 bits                   */
#define TOF_REG_RANGE_VAL    0x0062u /* [DS] 6.2.42 — 🔴 [7:0], UNITE mm        */
#define TOF_REG_RANGE_RETURN_RATE 0x0066u /* [DS] 6.2.44 — 16 bits              */

#define TOF_INT_NEW_SAMPLE   4u      /* [DS] 6.2.39 : « New Sample Ready »      */
#define TOF_MODEL_ID_ATTENDU 0xB4u
/*
 * 🔴 REVU LE 2026-08-21 APRES MESURE — 600 ms A 2 ms DE PAS, C'ETAIT ~300
 *    TRANSACTIONS PAR TIR, pour un budget de convergence de 49 ms ([DS] §6.2.20,
 *    0x001C = 0x31 au reset). Douze fois le budget, et un martelage du bus qui
 *    coincide EXACTEMENT avec le motif d'echec mesure : un tir sur deux echoue,
 *    IMMEDIATEMENT (1-2 ms), et c'est TOUJOURS celui qui suit un sondage long.
 * ⚠️ La piste est PLAUSIBLE, ⛔ PAS PROUVEE : ce changement est un ESSAI, et il
 *    doit etre juge sur le taux d'echec AVANT/APRES, pas sur son bon sens.
 *    AVANT (firmware e162f56) : 4 LECTURE KO sur 8 tirs.
 */
#define TOF_POLL_MS_MAX      250     /* 5x le budget de convergence, ⛔ plus 12x */
#define TOF_POLL_PAS_MS      5       /* ⛔ plus 2 ms : ~50 sondages/tir, pas 300 */
#define TOF_N_MAX            200     /* borne haute de `tof range <n>`          */

typedef struct {
    uint16_t reg;
    uint8_t  val;
} tof_ecr_t;

/* ⛔ Ces commandes n'ouvrent PLUS de device : elles empruntent celui de
 * `dn_env`. Elles doivent donc verifier qu'il EST ouvert — sinon toute lecture
 * rendrait ESP_ERR_INVALID_STATE et on relirait un « capteur muet » qui n'est
 * qu'un module pas encore initialise. */
static bool tof_pret(void)
{
    if (dn_env_present(DN_ENV_TOF)) {
        return true;
    }
    printf("🔴 le device VL6180X de `dn_env` n'est PAS OUVERT.\n");
    printf("   ⛔ Ces commandes passent par SON handle persistant, et c'est\n");
    printf("      DELIBERE : le chemin « ouvre-ferme » a fabrique un faux\n");
    printf("      diagnostic d'intermittence (§13.21.12).\n");
    printf("   ⚠️ Si `env` dit JAMAIS/MUET : `dn_env` retente UNE fois par\n");
    printf("      minute. Attendre, ou `reboot`. ⛔ RIEN n'a ete tente ici.\n");
    return false;
}

/*
 * 🔴 [AN] §9, bloc « Mandatory : private registers » — RECOPIE VERBATIM,
 *    dans l'ordre, 31 ecritures. ⛔ Aucune n'est documentee dans [DS] : ce sont
 *    des registres PRIVES. C'est precisement pour ça qu'on ne peut pas les
 *    deviner, et que leur absence est la cause candidate n°1 de la refutation
 *    de l'ALS en §13.19.5.
 */
static const tof_ecr_t k_sr03_prive[] = {
    {0x0207, 0x01}, {0x0208, 0x01}, {0x0096, 0x00}, {0x0097, 0xFD},
    {0x00E3, 0x00}, {0x00E4, 0x04}, {0x00E5, 0x02}, {0x00E6, 0x01},
    {0x00E7, 0x03}, {0x00F5, 0x02}, {0x00D9, 0x05}, {0x00DB, 0xCE},
    {0x00DC, 0x03}, {0x00DD, 0xF8}, {0x009F, 0x00}, {0x00A3, 0x3C},
    {0x00B7, 0x00}, {0x00BB, 0x3C}, {0x00B2, 0x09}, {0x00CA, 0x09},
    {0x0198, 0x01}, {0x01B0, 0x17}, {0x01AD, 0x00}, {0x00FF, 0x05},
    {0x0100, 0x05}, {0x0199, 0x05}, {0x01A6, 0x1B}, {0x01AC, 0x3E},
    {0x01A7, 0x1F}, {0x0030, 0x00},
};

/*
 * [AN] §9, bloc « Recommended : Public registers » — avec UN ECART, ET IL EST
 * DECLARE ICI PLUTOT QUE JOUE EN SILENCE :
 *
 * 🔴 [AN] ecrit `WriteByte(0x0040, 0x63)` en commentant « Set ALS integration
 *    time to 100ms ». Or [DS] §6.2.36 definit SYSALS__INTEGRATION_PERIOD comme
 *    un registre de 16 BITS a l'offset 0x040, champ utile [8:0], « 1 code =
 *    1 ms (0 = 1 ms). Recommended setting is 100 ms (0x63) ».
 *    ⇒ 0x63 est la valeur du CHAMP, donc l'octet de POIDS FAIBLE (0x0041).
 *      L'ecriture de [AN] pose 0x63 dans l'octet de POIDS FORT et deborde le
 *      champ. Les deux documents ST se CONTREDISENT ; [DS] fait foi sur la
 *      carte des registres.
 * ✅ Consequence heureuse : dn4-3 avait deja ecrit 0x0040=0x00 / 0x0041=0x63.
 *    C'est dn4-3 QUI A RAISON, et [AN] qui est bancal. ⛔ Ne pas inverser ce
 *    verdict — et la garde anti-fantome de `dn_env` (qui relit 0x0041 == 0x63)
 *    reste conforme APRES le passage de SR03, ce qui n'aurait pas ete le cas en
 *    jouant [AN] a la lettre.
 *
 * 🔴 LE BLOC « Optional » DE [AN] §9 — ET J'AI EU FAUX SUR 0x0014, MESURE A
 *    L'APPUI (2026-08-21, firmware 98baeb4).
 *
 *    Premiere version de ce fichier : les TROIS registres optionnels etaient
 *    ecartes, au motif ecrit que « 0x0014 = 0x24 ECRASERAIT le 0x20 pose par
 *    `dn_env_configurer()`, dont le temoin de conformite depend ».
 *    ⛔ CE MOTIF ETAIT FAUX. `conformite_verifier()` (dn_env.c) relit 0x003F et
 *      0x0041, et RIEN D'AUTRE : 0x0014 est ECRIT par `configurer()` mais
 *      JAMAIS RELU par la garde. J'ai affirme une dependance qui n'existait pas
 *      dans le code que je venais de lire.
 *
 *    ET CE N'ETAIT PAS SANS CONSEQUENCE — c'est ce qui a fait passer le
 *    telemetre pour MORT. [DS] §6.2.12 : 0x014 porte als_int_mode en [5:3] et
 *    range_int_mode en [2:0]. Le 0x20 de dn4-3 vaut donc :
 *        [5:3] = 4  « New sample ready » pour l'ALS   ✅
 *        [2:0] = 0  « Disabled »        pour la PORTEE 🔴
 *    => l'interruption de portee etait DESACTIVEE, la puce ne pouvait
 *       PHYSIQUEMENT pas signaler sa mesure, et les 10 premiers tirs ont tous
 *       expire sur « PAS DE New Sample Ready » a 601 ms.
 *    ⇒ 0x0014 = 0x24 EST DONC JOUE : [5:3]=4 (ALS) ET [2:0]=4 (portee).
 *
 * ⛔ Les deux AUTRES optionnels restent ecartes, et CE motif-la tient : 0x001B
 *    et 0x003E reglent des periodes d'INTER-MESURE du MODE CONTINU, que cette
 *    campagne n'utilise pas — elle tire coup par coup ([DS] §6.2.16, bit 1 = 0).
 */
static const tof_ecr_t k_sr03_public[] = {
    {0x0011, 0x10}, /* [AN] polling de « New Sample ready » en fin de mesure   */
    {0x010A, 0x30}, /* [AN] READOUT__AVERAGING_SAMPLE_PERIOD                   */
    {0x003F, 0x46}, /* [AN] gains clair/sombre — IDENTIQUE a ce que dn4-3 pose */
    {0x0031, 0xFF}, /* [AN] SYSRANGE__VHV_REPEAT_RATE                          */
    {0x0040, 0x00}, /* 🔴 ECART DECLARE ci-dessus — [DS] §6.2.36, poids fort   */
    {0x0041, 0x63}, /* 🔴 ECART DECLARE ci-dessus — [DS] §6.2.36, poids faible */
    {0x002E, 0x01}, /* [AN] une calibration de temperature du telemetre        */
    /* 🔴 [AN] §9 bloc « Optional » — LE SEUL DES TROIS QUI EST JOUE, et sans lui
     * le telemetre ne signale JAMAIS sa mesure. Voir le pave ci-dessus. */
    {0x0014, 0x24}, /* [DS] §6.2.12 : [5:3]=4 ALS + [2:0]=4 PORTEE, New sample  */
};

/* 🔴 REGISTRES AUTO-EFFAÇANTS — ILS NE SE RELISENT PAS, ET C'EST NORMAL.
 * Les compter comme des ecarts fabriquerait un defaut sur un comportement
 * CONFORME. C'est arrive : la premiere version de `tof sr03` a sorti un 🔴 sur
 * 0x002E relu 0x00, alors que [DS] §6.2.29 ecrit noir sur blanc, pour
 * sysrange__vhv_recalibrate : « FW clears bit after operation carried out ».
 * ⇒ relire 0x00 est le signal de SUCCES : le firmware a mene la recalibration
 *   VHV a son terme, et bit[1] (vhv_status) a 0 dit « FW has finished autoVHV ».
 */
static bool tof_reg_auto_effacant(uint16_t reg)
{
    return reg == 0x002Eu; /* SYSRANGE__VHV_RECALIBRATE, [DS] §6.2.29 */
}

/* ── Primitives 16 bits, sur un device DEJA ouvert ────────────────────────── */

/*
 * 🔴 CORRIGE LE 2026-08-21 — CES DEUX PRIMITIVES OUVRAIENT UN DEVICE A LA VOLEE,
 *    ET CE CHEMIN A FABRIQUE UN DIAGNOSTIC DE PANNE MATERIELLE QUI ETAIT FAUX.
 *
 * A/B mesure, MEME capteur, MEME instant (§13.21.12) :
 *   · `dn_env`, handle PERSISTANT, 3 transactions / 5 s : 22 lectures, i2c 0
 *   · console, ajout/retrait de device A CHAQUE APPEL   : 2 reussites / 15
 * J'avais conclu « le ToF est intermittent » et je l'ai annonce a l'owner. FAUX :
 * le capteur etait stable tout du long, c'est MON chemin d'acces qui s'effondrait
 * sous la repetition rapide.
 * ⚠️ Le retrait de device n'etait PAS en cause (« RETRAIT DU DEVICE REFUSE »
 *    compte 0 fois sur 15) : le mecanisme exact RESTE OUVERT. Ce qui est etabli,
 *    c'est l'A/B — et il suffit a choisir le chemin.
 * ⇒ TOUT passe desormais par le handle de `dn_env`, celui qui ne rate jamais.
 * ⛔ NE PAS reintroduire d'`i2c_dev_ouvrir()` ici.
 */
static esp_err_t tof_lire(uint16_t reg, uint8_t *b, size_t n)
{
    return dn_env_tof_lire(reg, b, n);
}

static esp_err_t tof_ecrire(uint16_t reg, uint8_t v)
{
    return dn_env_tof_ecrire(reg, v);
}

/* [DS] Table 12 « Range error codes » — le decodage, ⛔ pas un numero nu. */
static const char *tof_erreur_nom(uint8_t code)
{
    switch (code) {
    case 0x0: return "aucune erreur";
    case 0x1: return "VCSEL Continuity Test";
    case 0x2: return "VCSEL Watchdog Test";
    case 0x3: return "VCSEL Watchdog";
    case 0x4: return "PLL1 Lock";
    case 0x5: return "PLL2 Lock";
    case 0x6: return "Early Convergence Estimate";
    case 0x7: return "Max Convergence (pas converge dans le budget 0x001C)";
    case 0x8: return "No Target Ignore";
    case 0xB: return "Max Signal To Noise Ratio";
    case 0xC: return "Raw Ranging Algo Underflow (cible < 0)";
    case 0xD: return "Range overflow — cible VUE mais > ~200 mm ([DS] Table 12)";
    case 0xE: return "Raw Ranging Algo Overflow";
    case 0xF: return "Range overflow — cible VUE mais > ~200 mm ([DS] Table 12)";
    default:  return "code non documente par [DS]";
    }
}

/* Sonde le registre d'interruption jusqu'a « New Sample Ready » ou expiration.
 * ⚠️ Rend le temps reellement attendu : une mesure qui prend 400 ms n'est pas
 *    la meme information qu'une mesure qui prend 8 ms, et la moyenne des deux
 *    ne veut rien dire. */
static esp_err_t tof_attendre(bool als, int *attendu_ms)
{
    const int64_t t0 = esp_timer_get_time();
    for (;;) {
        uint8_t s;
        esp_err_t e = tof_lire(TOF_REG_INT_STATUS, &s, 1);
        if (e != ESP_OK) {
            *attendu_ms = (int)((esp_timer_get_time() - t0) / 1000);
            return e;
        }
        const uint8_t champ = als ? (uint8_t)((s >> 3) & 0x07u)
                                  : (uint8_t)(s & 0x07u);
        if (champ == TOF_INT_NEW_SAMPLE) {
            *attendu_ms = (int)((esp_timer_get_time() - t0) / 1000);
            return ESP_OK;
        }
        if (((esp_timer_get_time() - t0) / 1000) > TOF_POLL_MS_MAX) {
            *attendu_ms = (int)((esp_timer_get_time() - t0) / 1000);
            return ESP_ERR_TIMEOUT;
        }
        vTaskDelay(pdMS_TO_TICKS(TOF_POLL_PAS_MS));
    }
}

/* ── `tof sr03` — LE POINT D'ARRET DE dn4-7 ─────────────────────────────────── */
static int tof_cmd_sr03(void)
{
    if (!tof_pret()) {
        return 1;
    }

    uint8_t id = 0;
    if (tof_lire(TOF_REG_MODEL_ID, &id, 1) != ESP_OK) {
        printf("🔴 pas de reponse a 0x%02X — RIEN n'a ete ecrit.\n", DN_VL6180X_ADDR);
        return 1;
    }
    if (id != TOF_MODEL_ID_ATTENDU) {
        printf("🔴 MODEL_ID = 0x%02X, attendu 0x%02X. Ce n'est pas le VL6180X.\n",
               id, TOF_MODEL_ID_ATTENDU);
        printf("   ⛔ RIEN n'a ete ecrit : jouer SR03 sur une autre puce serait\n");
        printf("      ecrire 37 registres au hasard chez un inconnu.\n");
        return 1;
    }

    /* ⛔ ON LIT 0x0016, ON NE L'ECRIT PAS. Sa valeur est un FAIT sur l'historique
     * de la puce ; [AN] §1.3 etape 4 classe d'ailleurs son ecriture
     * « (Optional) ». La lecture, elle, est l'etape 1 de la meme procedure. */
    uint8_t fresh = 0xFF;
    const esp_err_t e_fresh = tof_lire(TOF_REG_FRESH_RESET, &fresh, 1);
    printf("MODEL_ID 0x%02X ✅ · FRESH_OUT_OF_RESET = ", id);
    if (e_fresh == ESP_OK) {
        printf("0x%02X (%s)\n", fresh,
               fresh == 0x01 ? "frais — SR03 est A JOUER"
                             : "deja initialise depuis sa mise sous tension");
    } else {
        printf("ILLISIBLE (%s)\n", esp_err_to_name(e_fresh));
    }
    if (e_fresh == ESP_OK && fresh != 0x01) {
        printf("⚠️ [AN] §1.3 : la sequence se joue APRES la mise sous tension, et\n");
        printf("   « must be repeated if the VL6180X has been power cycled ». Ici\n");
        printf("   0x0016 ne vaut pas 0x01 ⇒ elle a DEJA ete jouee, ou quelqu'un a\n");
        printf("   ecrit ce registre. On la rejoue quand meme (elle est idempotente\n");
        printf("   par construction : ce sont des ecritures de valeurs fixes), mais\n");
        printf("   ⛔ le resultat ne prouve alors RIEN sur un demarrage a froid.\n");
    }

    printf("\n[AN] AN4545 DocID026571 Rev 1 (juin 2014) §9 — %d prives + %d publics\n",
           (int)(sizeof k_sr03_prive / sizeof k_sr03_prive[0]),
           (int)(sizeof k_sr03_public / sizeof k_sr03_public[0]));

    int ko = 0;
    int n_prive = (int)(sizeof k_sr03_prive / sizeof k_sr03_prive[0]);
    for (int i = 0; i < n_prive; i++) {
        esp_err_t e = tof_ecrire(k_sr03_prive[i].reg, k_sr03_prive[i].val);
        if (e != ESP_OK) {
            ko++;
            printf("  🔴 prive[%02d] 0x%04X <- 0x%02X  ECHEC : %s\n", i,
                   k_sr03_prive[i].reg, k_sr03_prive[i].val, esp_err_to_name(e));
        }
    }
    int n_pub = (int)(sizeof k_sr03_public / sizeof k_sr03_public[0]);
    for (int i = 0; i < n_pub; i++) {
        esp_err_t e = tof_ecrire(k_sr03_public[i].reg, k_sr03_public[i].val);
        if (e != ESP_OK) {
            ko++;
            printf("  🔴 public[%02d] 0x%04X <- 0x%02X  ECHEC : %s\n", i,
                   k_sr03_public[i].reg, k_sr03_public[i].val, esp_err_to_name(e));
        }
    }
    printf("%d ecriture(s), %d en ECHEC\n", n_prive + n_pub, ko);

    /* 🔴 LA RELECTURE — et elle ne vaut QUE pour les registres PUBLICS.
     * Les prives ne sont pas documentes : ST ne promet nulle part qu'ils se
     * relisent, et un ecart de relecture sur l'un d'eux ne prouverait donc
     * RIEN. On imprime ce qu'ils rendent comme une DONNEE, ⛔ pas comme un
     * verdict. C'est le seul traitement honnete d'un registre non documente. */
    printf("\nrelecture des PUBLICS (les seuls dont [DS] promette la carte) :\n");
    int pub_ko = 0;
    for (int i = 0; i < n_pub; i++) {
        uint8_t v = 0;
        esp_err_t e = tof_lire(k_sr03_public[i].reg, &v, 1);
        const bool auto_eff = tof_reg_auto_effacant(k_sr03_public[i].reg);
        /* ⛔ Un auto-effaçant ne se juge PAS sur l'egalite : il se juge sur le
         * fait qu'il s'est EFFACE, ce qui prouve que l'operation a eu lieu. */
        const bool ok = (e == ESP_OK) &&
                        (auto_eff ? (v == 0x00) : (v == k_sr03_public[i].val));
        if (!ok) {
            pub_ko++;
        }
        printf("  %s 0x%04X : ecrit 0x%02X, relu ", ok ? "✅" : "🔴",
               k_sr03_public[i].reg, k_sr03_public[i].val);
        if (e == ESP_OK) {
            printf("0x%02X", v);
        } else {
            printf("ILLISIBLE (%s)", esp_err_to_name(e));
        }
        if (auto_eff) {
            printf("  (AUTO-EFFAÇANT, [DS] §6.2.29 : 0x00 = la recalibration"
                   " VHV a ETE MENEE)");
        }
        printf("\n");
    }

    printf("\ntemoin des PRIVES (donnee BRUTE — ⛔ AUCUN verdict, non documentes) :\n");
    for (int i = 0; i < n_prive; i++) {
        uint8_t v = 0;
        if (tof_lire(k_sr03_prive[i].reg, &v, 1) == ESP_OK) {
            printf("  0x%04X ecrit 0x%02X relu 0x%02X%s", k_sr03_prive[i].reg,
                   k_sr03_prive[i].val, v,
                   ((i % 3) == 2) ? "\n" : "   ");
        } else {
            printf("  0x%04X ecrit 0x%02X relu  ??  %s", k_sr03_prive[i].reg,
                   k_sr03_prive[i].val, ((i % 3) == 2) ? "\n" : "   ");
        }
    }
    printf("\n");


    if (ko > 0) {
        printf("\n🔴 %d ECRITURE(S) N'ONT PAS ABOUTI. ⛔ NE PAS CONCLURE que SR03\n", ko);
        printf("   « ne marche pas » : §13.17.1 a MESURE que ce bus lache les\n");
        printf("   transferts multi-octets dans les ~40 s d'un demarrage a froid,\n");
        printf("   et le VL6180X est LE capteur qui en souffre le plus (seul index\n");
        printf("   de registre sur 16 bits). ⇒ attendre, `env` pour lire err_i2c,\n");
        printf("   puis rejouer. C'est le BUS ou SR03 : les distinguer est le\n");
        printf("   travail, pas un detail.\n");
        return 1;
    }
    if (pub_ko > 0) {
        printf("\n🔴 %d registre(s) PUBLIC(S) ne se relisent pas conformes alors que\n",
               pub_ko);
        printf("   toutes les ecritures ont abouti. C'est un fantome (§13.10) ou une\n");
        printf("   puce qui refuse le reglage, ⛔ pas un probleme de transport.\n");
        return 1;
    }
    printf("\n✅ SR03 POSE ET RELU CONFORME. ⛔ Cela ne prouve PAS encore que la\n");
    printf("   puce MESURE : AC1 exige la PROPORTIONNALITE. ⇒ `tof balayage`.\n");
    return 0;
}

/* ── `tof als <ms>` — UNE mesure ALS a integration imposee ───────────────────── */
static int tof_als_un(int ms, bool entete)
{
    /* [DS] §6.2.36 : « 1 code = 1 ms (0 = 1 ms) » ⇒ le code vaut ms - 1. */
    const uint16_t code = (uint16_t)((ms > 0 ? ms : 1) - 1);
    if (entete) {
        printf("  ms  code    0x0050    decimal  attendu_ms  statut\n");
    }
    esp_err_t e = tof_ecrire(TOF_REG_ALS_INTEG_HI, (uint8_t)(code >> 8));
    if (e == ESP_OK) {
        e = tof_ecrire(TOF_REG_ALS_INTEG_LO, (uint8_t)(code & 0xFFu));
    }
    if (e == ESP_OK) {
        e = tof_ecrire(TOF_REG_INT_CLEAR, 0x07);
    }
    if (e == ESP_OK) {
        e = tof_ecrire(TOF_REG_ALS_START, 0x01);
    }
    if (e != ESP_OK) {
        printf("%4d  %04X    --        --       --          ECRITURE KO (%s)\n",
               ms, code, esp_err_to_name(e));
        return 1;
    }
    int attendu = 0;
    const esp_err_t ea = tof_attendre(true, &attendu);
    uint8_t b[2] = {0, 0};
    const esp_err_t el = tof_lire(TOF_REG_ALS_VAL, b, 2);
    const uint16_t val = (uint16_t)((b[0] << 8) | b[1]);
    tof_ecrire(TOF_REG_INT_CLEAR, 0x07);

    printf("%4d  %04X    %02X%02X      %5u    %4d       %s\n", ms, code, b[0],
           b[1], val, attendu,
           (el != ESP_OK)       ? "LECTURE KO"
           : (ea == ESP_ERR_TIMEOUT) ? "⚠️ PAS DE New Sample Ready"
           : (ea != ESP_OK)     ? "SONDAGE KO"
                                : "ok");
    return 0;
}

/* ── `tof balayage` — 🔴 LE CRITERE D'AC1, REJOUE A L'IDENTIQUE ─────────────── */
static int tof_cmd_balayage(void)
{
    /* 🔴 LES HUIT POINTS DE §13.19.5, DANS LE MEME ORDRE. Le point a 1 ms est
     * OBLIGATOIRE (AC1) : c'est lui qui a dementi la conclusion la plus
     * dangereuse de dn4-3 (« l'integration n'agit pas »). */
    static const int k_ms[] = {1, 2, 3, 5, 10, 20, 50, 100};

    if (!tof_pret()) {
        return 1;
    }
    uint8_t gain = 0;
    if (tof_lire(TOF_REG_ALS_GAIN, &gain, 1) != ESP_OK) {
        printf("🔴 gain illisible — le balayage n'aurait pas de condition connue.\n");
        return 1;
    }
    printf("BALAYAGE D'INTEGRATION — rejeu a l'identique de §13.19.5\n");
    printf("ALS_GAIN (0x003F) = 0x%02X %s\n", gain,
           gain == 0x46 ? "(gain 1,0x — la condition de §13.19.5)"
                        : "⚠️ ⛔ PAS 0x46 : la condition DIFFERE de §13.19.5");
    printf("🔴 le critere n'est PAS « ça rend un nombre » : c'est que la reponse\n");
    printf("   VARIE AVEC LA DUREE. Une colonne constante = comparateur sature.\n\n");

    int ko = 0;
    for (int i = 0; i < (int)(sizeof k_ms / sizeof k_ms[0]); i++) {
        ko += tof_als_un(k_ms[i], i == 0);
    }
    printf("\n⚠️ VERDICT A LA MAIN, ⛔ pas par la console : comparer la colonne\n");
    printf("   « decimal » a celle de §13.19.5 (0000 0000 FFFF FFFF FFFF FFFF\n");
    printf("   FFFF FFFF). Si elle est encore binaire, SR03 n'a rien change et\n");
    printf("   Z1 se solde PAR LA NEGATIVE — c'est un RESULTAT.\n");
    return ko > 0 ? 1 : 0;
}

/* Racine entiere — ⛔ pas de <math.h> ajoute pour un seul appel, et l'ecart-type
 * se rend en DIXIEMES de mm : `sqrt(variance x 100)` est exact a l'entier pres,
 * ce qui est plus fin que le pas de quantification du capteur (1 mm). */
static uint32_t tof_racine(uint32_t x)
{
    if (x == 0) {
        return 0;
    }
    uint32_t r = x, p = 0;
    while (r != p) {
        p = r;
        r = (r + x / r) / 2;
    }
    return r;
}

/* ── `tof range [n]` — LA PORTEE, AVEC SES TROIS ETATS (AC2/AC4) ───────────── */
static int tof_cmd_range(int n)
{
    if (!tof_pret()) {
        return 1;
    }
    uint8_t conv = 0;
    tof_lire(TOF_REG_MAX_CONV, &conv, 1);

    printf("TELEMETRIE — n = %d, budget de convergence 0x001C = 0x%02X (%u ms)\n",
           n, conv, (unsigned)(conv & 0x3Fu));
    printf("🔴 PLAFOND STRUCTUREL : [DS] §6.2.42 definit RESULT__RANGE_VAL comme\n");
    printf("   un champ [7:0] en MILLIMETRES ⇒ 255 mm est le MAXIMUM REPRESENTABLE.\n");
    printf("   ⛔ Aucun reglage ne peut faire tenir 2 m dans un octet.\n");
    printf("⚠️ ET LE PIEGE D'AC2 EST DOCUMENTE PAR ST : [DS] Table 12 erreur 16\n");
    printf("   « Ranging_Filtered » ne sort QU'AVEC l'API ST (absente ici). Sans\n");
    printf("   elle, une cible TRES REFLECHISSANTE entre 600 mm et 1,2 m peut\n");
    printf("   rendre une valeur PROCHE ET PLAUSIBLE, sans aucun code d'erreur.\n");
    printf("   ⇒ TOUJOURS croiser avec la distance MESUREE AU METRE.\n\n");

    printf("  #   0x0062   status  err  retour  ms   lecture\n");

    uint32_t somme = 0, n_ok = 0;
    /* ⚠️ `static` DELIBERE : 200 x uint32 = 800 o, et la tache console n'a pas
     * une pile a gaspiller. Le REPL est mono-thread, aucune reentrance. */
    static uint32_t vals[TOF_N_MAX];
    uint32_t n_err_puce = 0, n_transport = 0, n_pas_pret = 0;

    for (int i = 0; i < n; i++) {
        esp_err_t e = tof_ecrire(TOF_REG_INT_CLEAR, 0x07);
        if (e == ESP_OK) {
            e = tof_ecrire(TOF_REG_RANGE_START, 0x01); /* [DS] 6.2.16 : coup par coup */
        }
        if (e != ESP_OK) {
            n_transport++;
            printf("%3d   --       --      --   --      --   DEMARRAGE KO (%s)\n",
                   i, esp_err_to_name(e));
            continue;
        }
        /* ⚠️ Respiration APRES le declenchement, AVANT le premier sondage : la
         * mesure ne peut pas etre prete en moins d'une convergence, donc sonder
         * immediatement ne fait qu'ajouter des transactions inutiles sur le bus
         * au moment le plus charge. ⛔ Ce n'est PAS une temporisation magique :
         * elle est bornee par le budget de convergence, pas devinee. */
        vTaskDelay(pdMS_TO_TICKS(TOF_POLL_PAS_MS));
        int attendu = 0;
        const esp_err_t ea = tof_attendre(false, &attendu);
        uint8_t v = 0, st = 0, rr[2] = {0, 0};
        const esp_err_t e1 = tof_lire(TOF_REG_RANGE_VAL, &v, 1);
        const esp_err_t e2 = tof_lire(TOF_REG_RANGE_STATUS, &st, 1);
        tof_lire(TOF_REG_RANGE_RETURN_RATE, rr, 2);
        tof_ecrire(TOF_REG_INT_CLEAR, 0x07);

        if (e1 != ESP_OK || e2 != ESP_OK) {
            n_transport++;
            printf("%3d   --       --      --   --      %3d  LECTURE KO\n", i, attendu);
            continue;
        }
        const uint8_t err = (uint8_t)(st >> 4);
        const uint16_t retour = (uint16_t)((rr[0] << 8) | rr[1]);
        printf("%3d   %3u mm   0x%02X    %X    %5u  %3d  %s\n", i, v, st, err,
               retour, attendu,
               (ea == ESP_ERR_TIMEOUT) ? "⚠️ PAS DE New Sample Ready" : "ok");
        /* 🔴 CORRIGE LE 2026-08-21, ET C'ETAIT UN CHIFFRE FABRIQUE.
         * Cette branche testait `err == 0` SEUL. Or `err` est le code d'erreur
         * de la DERNIERE mesure : quand l'attente EXPIRE, aucune mesure neuve
         * n'a eu lieu, `err` vaut donc 0, et la commande annonçait
         * « 10/10 mesures VALIDES · taux de detection 100,0 % · moyenne 0,0 mm »
         * sur DIX tirs qui n'avaient JAMAIS abouti. Un instrument qui compte des
         * mesures inexistantes est pire qu'un instrument absent — c'est
         * exactement la famille « la console fabrique des nombres plausibles ».
         * ⇒ UNE MESURE QUI N'A PAS SIGNALE « New Sample Ready » N'EST PAS UNE
         *   MESURE, quel que soit ce que rendent les registres de resultat. */
        if (ea != ESP_OK) {
            n_pas_pret++;
        } else if (err == 0) {
            if (n_ok < TOF_N_MAX) {
                vals[n_ok] = v;
            }
            n_ok++;
            somme += v;
        } else {
            n_err_puce++;
        }
    }

    printf("\n🔴 LES TROIS ETATS D'AC2, ⛔ PAS DEUX :\n");
    printf("  1. mesure VALIDE (err = 0)          : %lu / %d\n",
           (unsigned long)n_ok, n);
    printf("  2. la PUCE DIT qu'elle a echoue     : %lu / %d\n",
           (unsigned long)n_err_puce, n);
    printf("  3. valeur PLAUSIBLE MAIS FAUSSE     : ⛔ LA CONSOLE NE PEUT PAS LE\n");
    printf("     DIRE. Il faut la distance PHYSIQUE au metre. C'est l'etat\n");
    printf("     DANGEREUX (famille du fantome §13.10) — c'est l'owner qui tranche.\n");
    printf("  · transport I2C en echec            : %lu / %d\n",
           (unsigned long)n_transport, n);
    printf("  · AUCUNE MESURE (pas de New Sample)  : %lu / %d\n",
           (unsigned long)n_pas_pret, n);

    if (n_pas_pret > 0) {
        printf("\n🔴 %lu TIR(S) N'ONT JAMAIS ABOUTI — ⛔ ce ne sont PAS des mesures a\n",
               (unsigned long)n_pas_pret);
        printf("   0 mm, ce sont des NON-MESURES, et elles ne comptent NULLE PART.\n");
        printf("   ⚠️ PREMIERE CHOSE A REGARDER : `tof etat`, registre 0x0014.\n");
        printf("      [DS] §6.2.12 — [2:0] range_int_mode. S'il vaut 0, la portee\n");
        printf("      est « Disabled » et la puce ne PEUT PAS signaler sa mesure.\n");
        printf("      Il doit valoir 4 ⇒ 0x0014 = 0x24. `tof sr03` le pose.\n");
    }
    if (n > 0) {
        printf("\ntaux de detection : %lu/%d = %d,%d %%", (unsigned long)n_ok, n,
               (int)((n_ok * 100) / (uint32_t)n),
               (int)(((n_ok * 1000) / (uint32_t)n) % 10));
        printf("   (denominateur = TIRS DEMANDES, ⛔ pas mesures abouties)\n");
    }
    if (n_ok > 0) {
        const uint32_t nb = (n_ok < TOF_N_MAX) ? n_ok : TOF_N_MAX;
        const uint32_t moy10 = (somme * 10u) / n_ok;
        /* ⛔ NE PAS diviser chaque terme par nb : la troncature entiere ferait
         * disparaitre tout ecart inferieur a sqrt(nb) dixiemes, et publierait
         * « ecart-type 0,0 mm » sur des valeurs qui bougent. On somme, PUIS on
         * divise, sur 64 bits. */
        uint64_t somme_carres = 0;
        for (uint32_t i = 0; i < nb; i++) {
            const int64_t d10 = (int64_t)(vals[i] * 10u) - (int64_t)moy10;
            somme_carres += (uint64_t)(d10 * d10);
        }
        const uint32_t et10 = tof_racine((uint32_t)(somme_carres / nb));
        printf("moyenne des VALIDES : %lu,%lu mm · ecart-type : %lu,%lu mm (n=%lu)\n",
               (unsigned long)(moy10 / 10), (unsigned long)(moy10 % 10),
               (unsigned long)(et10 / 10), (unsigned long)(et10 % 10),
               (unsigned long)nb);
        printf("⚠️ 🔴 UNE PORTEE ATTEINTE 1 FOIS SUR 5 N'EST PAS UNE PORTEE (AC4).\n");
        printf("   C'est le TAUX ci-dessus qui est le livrable, ⛔ pas un maximum\n");
        printf("   atteint une fois.\n");
    } else {
        printf("⛔ AUCUNE mesure valide : pas de moyenne, pas d'ecart-type. Publier\n");
        printf("   une statistique sur zero echantillon fabriquerait un chiffre.\n");
    }
    return 0;
}

/* ── `tof etat` — CE QUE LA PUCE PORTE, SANS RIEN ECRIRE ────────────────────── */
static int tof_cmd_etat(void)
{
    if (!tof_pret()) {
        return 1;
    }
    static const struct {
        uint16_t reg;
        const char *nom;
    } k_vue[] = {
        {TOF_REG_MODEL_ID,     "MODEL_ID              (attendu B4)"},
        {TOF_REG_INT_CONFIG,   "INT_CONFIG_GPIO       (dn4-3 pose 20)"},
        {TOF_REG_FRESH_RESET,  "FRESH_OUT_OF_RESET    (01 = frais)"},
        {TOF_REG_MAX_CONV,     "MAX_CONVERGENCE_TIME  (reset 31, [5:0] ms)"},
        {TOF_REG_ALS_GAIN,     "ALS_ANALOGUE_GAIN     (dn4-3 pose 46)"},
        {TOF_REG_ALS_INTEG_HI, "ALS_INTEGRATION hi    (attendu 00)"},
        {TOF_REG_ALS_INTEG_LO, "ALS_INTEGRATION lo    (attendu 63)"},
        {TOF_REG_RANGE_STATUS, "RANGE_STATUS          ([7:4] = erreur)"},
        {TOF_REG_INT_STATUS,   "INTERRUPT_STATUS_GPIO"},
        {TOF_REG_RANGE_VAL,    "RANGE_VAL             (mm, plafond 255)"},
    };
    printf("VL6180X @ 0x%02X — LECTURE SEULE, ⛔ aucune ecriture\n", DN_VL6180X_ADDR);
    for (int i = 0; i < (int)(sizeof k_vue / sizeof k_vue[0]); i++) {
        uint8_t v = 0;
        const esp_err_t e = tof_lire(k_vue[i].reg, &v, 1);
        if (e == ESP_OK) {
            printf("  0x%04X  %02X   %s\n", k_vue[i].reg, v, k_vue[i].nom);
        } else {
            printf("  0x%04X  --   %s  (%s)\n", k_vue[i].reg, k_vue[i].nom,
                   esp_err_to_name(e));
        }
    }
    uint8_t st = 0;
    if (tof_lire(TOF_REG_RANGE_STATUS, &st, 1) == ESP_OK) {
        printf("dernier code d'erreur de portee : %X — %s\n", st >> 4,
               tof_erreur_nom((uint8_t)(st >> 4)));
    }
    return 0;
}

static void tof_usage(void)
{
    printf("usage : tof etat                 registres, LECTURE SEULE\n");
    printf("        tof sr03                 joue [AN] AN4545 Rev 1 §9 (37 ecritures)\n");
    printf("        tof balayage             rejeu de §13.19.5 — LE critere d'AC1\n");
    printf("        tof als <ms=1..500>      une mesure ALS a integration imposee\n");
    printf("        tof range [n=1..%d]     telemetrie + les TROIS etats\n", TOF_N_MAX);
    printf("🔴 ORDRE IMPOSE PAR LA STORY : `sr03` PUIS `balayage`. Si le balayage\n");
    printf("   n'est pas PROPORTIONNEL, Z1 se solde par la negative et dn4-7\n");
    printf("   S'ARRETE — ⛔ on ne mesure pas une portee avec une puce non\n");
    printf("   initialisee : elle rendrait des distances FAUSSES ET PLAUSIBLES.\n");
    printf("⚠️ ⛔ NE RIEN MESURER DANS LES ~40 PREMIERES SECONDES d'un demarrage a\n");
    printf("   FROID : §13.17.1 a mesure que le bus s'y degrade et que LE SCAN NE\n");
    printf("   LE VOIT PAS. Une campagne lancee la mesurerait le BUS, pas le ToF.\n");
}

static int cmd_tof(int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "etat") == 0) {
        return tof_cmd_etat();
    }
    if (argc == 2 && strcmp(argv[1], "sr03") == 0) {
        return tof_cmd_sr03();
    }
    if (argc == 2 && strcmp(argv[1], "balayage") == 0) {
        return tof_cmd_balayage();
    }
    if (argc == 3 && strcmp(argv[1], "als") == 0) {
        char *fin = NULL;
        const long ms = strtol(argv[2], &fin, 10);
        if (!fin || *fin != '\0' || ms < 1 || ms > 500) {
            printf("⛔ <ms> en DECIMAL, 1..500. [DS] §6.2.36 : champ [8:0], donc\n");
            printf("   511 ms est la borne haute du registre ; on s'arrete a 500.\n");
            return 1;
        }
        if (!tof_pret()) {
            return 1;
        }
        const int r = tof_als_un((int)ms, true);
        return r;
    }
    if (argc >= 2 && strcmp(argv[1], "range") == 0) {
        long n = 10;
        if (argc == 3) {
            char *fin = NULL;
            n = strtol(argv[2], &fin, 10);
            if (!fin || *fin != '\0' || n < 1 || n > TOF_N_MAX) {
                printf("⛔ <n> en DECIMAL, 1..%d.\n", TOF_N_MAX);
                return 1;
            }
        }
        return tof_cmd_range((int)n);
    }
    tof_usage();
    return argc == 1 ? 0 : 1;
}

/*
 * ── `capteurs` : l'ambiance, telle que la tâche l'a publiée (dn2-1) ──────────
 *
 * ⛔ ELLE NE DÉCLENCHE AUCUNE MESURE, et c'est structurel : `bme680_get_data()`
 *    boucle jusqu'à 1 500 ms, or sur la branche A retenue en dn2-2 **le REPL EST
 *    le transport PC**. Une commande qui mesure bloquerait la liaison pendant
 *    tout ce temps — exactement le défaut de `cpu N`, qui décrivait le dashboard
 *    au repos quel que soit le trafic parce qu'il bloquait ce qu'il mesurait.
 *    Ici on LIT ce que la tâche a publié. `pc` est le modèle.
 */
static int cmd_capteurs(int argc, char **argv)
{
    if (argc == 3 && strcmp(argv[1], "gaz") == 0) {
        bool on;
        if (!parse_on_off(argv[2], &on)) {
            printf("usage : capteurs gaz on|off\n");
            return 1;
        }
        if (dn_capt_set_gaz(on) != ESP_OK) {
            printf("capteur indisponible — bascule refusee\n");
            return 1;
        }
        printf("chauffage gaz %s au prochain cycle (%d ms).\n",
               on ? "DEMANDE" : "coupe", DN_CAPT_PERIODE_MS);
        printf("⚠️ le die met du temps a se stabiliser : ne PAS lire le delta de\n");
        printf("   temperature sur le cycle suivant — c'est l'A/B de T9.\n");
        return 0;
    }
    if (argc == 2 && strcmp(argv[1], "reset") == 0) {
        dn_capt_reset_compteurs();
        printf("compteurs capteurs remis a zero (valeur et horodatage CONSERVES)\n");
        return 0;
    }
    /* 🔴 `simuler` existe pour NE PLUS DEBRANCHER DE FIL. Un Dupont n'est donne
     * que pour quelques dizaines d'insertions : rejouer l'AC7 a la main degrade
     * le montage qu'on teste. Constat owner du 2026-08-17. */
    if (argc >= 2 && strcmp(argv[1], "simuler") == 0) {
        if (argc == 3 && strcmp(argv[2], "off") == 0) {
            dn_capt_simuler(DN_CAPT_FAUTE_AUCUNE, 0);
            printf("faute simulee DESARMEE\n");
            return 0;
        }
        if (argc != 4) {
            printf("usage : capteurs simuler muet|bornes|config <cycles 1..600>\n");
            printf("        capteurs simuler off\n");
            printf("  muet   = le capteur ne repond plus (transport)\n");
            printf("  bornes = valeur hors plage physique\n");
            printf("  config = capteur FANTOME : il repond, mais a perdu sa config\n");
            printf("           (le cas mesure le 2026-08-17 : 32,8 C et 100 %%RH,\n");
            printf("            faux ET plausibles, qu'aucune borne ne peut voir)\n");
            printf("  ⚠️ un cycle = %d ms\n", DN_CAPT_PERIODE_MS);
            return 1;
        }
        dn_capt_faute_t f = strcmp(argv[2], "muet") == 0     ? DN_CAPT_FAUTE_MUET
                            : strcmp(argv[2], "bornes") == 0 ? DN_CAPT_FAUTE_BORNES
                            : strcmp(argv[2], "config") == 0 ? DN_CAPT_FAUTE_CONFIG
                                                             : DN_CAPT_FAUTE_AUCUNE;
        if (f == DN_CAPT_FAUTE_AUCUNE) {
            printf("cause « %s » inconnue : muet | bornes | config\n", argv[2]);
            return 1;
        }
        long n;
        if (!parse_entier(argv[3], &n) || n < 1 || n > 600) {
            printf("nombre de cycles « %s » refuse : entre 1 et 600\n", argv[3]);
            return 1;
        }
        if (dn_capt_simuler(f, (int)n) != ESP_OK) {
            printf("injection refusee\n");
            return 1;
        }
        printf("faute « %s » armee pour %ld cycle(s), soit ~%ld s\n",
               dn_capt_faute_nom(f), n, n * DN_CAPT_PERIODE_MS / 1000);
        /* 🔴 CR 2026-08-17 : la duree MINIMALE UTILE etait laissee a deviner.
         * `muet` et `bornes` ne font passer les cases a « -- » qu'au-dela de la
         * peremption (3 cycles) : l'operateur qui armait 1 cycle voyait l'ecran
         * rester valide et concluait que la garde AC7 etait cassee. Le
         * comportement est CORRECT, c'est son annonce qui manquait. */
        if (f != DN_CAPT_FAUTE_CONFIG && n < DN_CAPT_CYCLES_AVANT_PEREMPTION) {
            printf("⚠️ %ld cycle(s) NE SUFFIT PAS a faire passer les cases a « -- » :\n",
                   n);
            printf("   la peremption est de %d cycles. Le compteur bougera, l'ecran\n",
                   DN_CAPT_CYCLES_AVANT_PEREMPTION);
            printf("   restera VALIDE — et c'est correct. Pour voir « -- », armer au\n");
            printf("   moins %d cycles. (`config`, lui, agit des le 1er cycle.)\n",
                   DN_CAPT_CYCLES_AVANT_PEREMPTION + 1);
        }
        printf("⚠️ elle teste le CHEMIN DE CODE, pas le materiel — elle ne peut pas\n");
        printf("   decouvrir un mode de panne qu'on n'a pas imagine. Vaut pour la\n");
        printf("   NON-REGRESSION, apres la campagne physique du 2026-08-17.\n");
        return 0;
    }
    if (argc != 1) {
        printf("usage : capteurs | reset | gaz on|off | simuler <cause> <cycles>\n");
        return 1;
    }

    dn_capt_etat_t e = dn_capt_etat();
    printf("BME680 @ 0x%02X : %s", DN_BME680_ADDR, dn_capt_etat_nom(e));
    /* ⚠️ LA GARDE PORTE SUR LA VALEUR, PAS SUR L'ÉTAT — correctif du 2026-08-17.
     * Elle testait `e != DN_CAPT_JAMAIS`. Le jour où l'état MUET a cessé d'être
     * synonyme de « valeur presente » (une valeur fausse est INVALIDÉE tout en
     * laissant l'etat a MUET), cette garde a laissé passer la sentinelle : la
     * console imprimait « 0,1 C · 0,-1 % · age 0 ms ».
     * Une sentinelle formatée comme une mesure est une valeur inventée.
     *
     * 🔴 PUIS LE CORRECTIF LUI-MÊME A ÉTÉ TROUVÉ FAUX — CR du 2026-08-17. Il
     * testait `t >= 0`, ce qui REFUSAIT TOUTE TEMPERATURE NEGATIVE : a -5,0 C
     * l'etat imprimait VIVANT, le dashboard affichait « -5,0 °C », et cette
     * meme ligne disait « aucune valeur courante ». Deux sorties du meme module
     * qui se contredisent. La cause etait plus profonde que la garde : la
     * sentinelle `-1` valait AUSSI -0,1 C, donc aucun test sur la valeur ne
     * pouvait etre correct. La sentinelle est sortie de la plage physique
     * (DN_CAPT_DX_ABSENT) ; la garde la teste, elle, et plus un signe. */
    int t = dn_capt_temperature_dixiemes();
    int h = dn_capt_humidite_dixiemes();
    int64_t age = dn_capt_age_us();
    if (t != DN_CAPT_DX_ABSENT && h != DN_CAPT_DX_ABSENT && age >= 0) {
        int tm = t < 0 ? -t : t; /* le signe se pose, il ne se deduit pas d'une
                                  * division entiere — elle tronque vers zero */
        printf(" — %s%d,%d C · %d,%d %% · age %lld ms", t < 0 ? "-" : "", tm / 10,
               tm % 10, h / 10, h % 10, (long long)(age / 1000));
    } else {
        printf(" — aucune valeur courante");
    }
    printf("\n");
    /* 🔴 dn4-3 — LA PRESSION, MESUREE DEPUIS dn2-1 ET JETEE JUSQU'ICI.
     * Publiee pour que X2 (la 6e case) se tranche sur des chiffres et pas sur
     * un pronostic. ⛔ Elle n'est PAS affichee dans une case, et elle n'a donc
     * PAS de seau d'erreur a elle : hors plage physique (300..1100 hPa, Bosch),
     * elle devient ABSENTE toute seule, sans faire tomber T et RH. */
    int pr = dn_capt_pression_dixiemes();
    int pr_brut = dn_capt_pression_brut_dixiemes();
    dn_capt_p_unite_t p_u = dn_capt_pression_unite();
    /* 🔴 LE SIGNE SE POSE, IL NE SE DEDUIT PAS D'UNE DIVISION ENTIERE — elle
     * tronque VERS ZERO — corrige en revue de code le 2026-08-20. Le patron
     * correct est vingt lignes plus haut (temperature), et `dn_capteurs.c` a
     * DEJA paye ce defaut sur l'humidite (« -5,-5 % »). La branche « LUE mais
     * NON PUBLIEE » ci-dessous est PRECISEMENT celle des valeurs aberrantes,
     * negatives comprises : elle imprimait « 0,-5 » ou « -1013,-2 ». */
    int pr_m = pr < 0 ? -pr : pr;
    int prb_m = pr_brut < 0 ? -pr_brut : pr_brut;
    const char *pr_s = pr < 0 ? "-" : "";
    const char *prb_s = pr_brut < 0 ? "-" : "";
    /* 🔴 L'AGE, comme T et RH sur la ligne du dessus — la pression et le gaz
     * s'imprimaient SANS age et SANS re-test de peremption : deux grandeurs du
     * MEME capteur, dans la MEME sortie, avec des semantiques de fraicheur
     * opposees et rien qui le dise. */
    int64_t p_age = dn_capt_age_us();
    /* 🔴 TROIS ETATS, TROIS PHRASES. Le message d'origine disait « hors plage
     * OU jamais lue » — DEUX DIAGNOSTICS OPPOSES DANS UNE SEULE PHRASE, la
     * faute exacte que `tronquee`/`trop_longue` a deja coutee a ce depot. */
    if (pr != DN_CAPT_DX_ABSENT) {
        printf("pression   : %s%d,%d hPa — MESUREE, PAS AFFICHEE (candidate a la 6e\n",
               pr_s, pr_m / 10, pr_m % 10);
        printf("             case, X2). brute driver %s%d,%d · unite %s · age %lld ms\n",
               prb_s, prb_m / 10, prb_m % 10, dn_capt_pression_unite_nom(p_u),
               (long long)(p_age / 1000));
        printf("             Bornes 300..1100 hPa (Bosch). Instrumentee par `w2`\n");
        printf("             dans SES DEUX formatages possibles.\n");
    } else if (pr_brut != DN_CAPT_DX_ABSENT) {
        printf("pression   : LUE mais NON PUBLIEE — brute driver %s%d,%d, unite %s\n",
               prb_s, prb_m / 10, prb_m % 10, dn_capt_pression_unite_nom(p_u));
        printf("             ⛔ Elle ne tombe ni dans 300..1100 (hPa) ni dans\n");
        printf("             30000..110000 (Pa). Rien n'est converti au juge.\n");
    } else {
        printf("pression   : JAMAIS LUE — aucune lecture BME680 valide depuis le\n");
        printf("             boot (ou depuis la derniere reconfiguration).\n");
    }
    /* 🔴 dn4-3 — LA RESISTANCE DE GAZ, sur DEMANDE OWNER. ⛔ CE N'EST PAS UN
     * INDICE DE QUALITE D'AIR : c'est la resistance BRUTE du capteur MOX, qui
     * BAISSE en presence de composes organiques volatils, et qui depend AUSSI
     * de la temperature, de l'humidite et de l'historique du capteur. */
    int g_ohms = dn_capt_gaz_ohms();
    if (g_ohms != DN_CAPT_DX_ABSENT) {
        printf("gaz (MOX)  : %d ohms (%d kOhm) — ⛔ RESISTANCE BRUTE, PAS un indice\n",
               g_ohms, g_ohms / 1000);
        printf("             de qualite d'air. Elle BAISSE quand des COV sont\n");
        printf("             presents. Instrumentee par `w2`.\n");
        printf("             iaq_score du composant : %d — ⛔ INUTILISABLE, TROIS\n",
               dn_capt_iaq_brut());
        printf("             defauts LUS AU SOURCE : (1) le header annonce 0..500,\n");
        printf("             la formule somme 6,5+6,5+52 => MAX REEL 65 ;\n");
        printf("             (2) `bme680.c:733` teste `gas>=13500 && gas>9000`, le\n");
        printf("             second est IMPLIQUE par le premier => la bande\n");
        printf("             9000..13500 ohms ne recoit AUCUN score et garde une\n");
        printf("             valeur RESIDUELLE ; (3) le score de temperature tombe\n");
        printf("             a 0 au-dessus de 26 C, or ce capteur lit ~28 C a cause\n");
        printf("             de son PROPRE auto-echauffement (+2,1 C mesure) => 6,5\n");
        printf("             points perdus par un artefact de MONTAGE.\n");
        printf("             ⇒ un vrai IAQ demande BSEC (binaire proprietaire).\n");
        printf("⚠️ LE CHAUFFEUR TOURNE : il coute +0,3 C et -2 points de RH sur les\n");
        printf("   deux grandeurs que la case affiche (§13.9). `capteurs gaz off`.\n");
    } else if (dn_capt_gaz_en_attente()) {
        /* 🔴 LE TROISIEME ETAT — ajoute en revue de code le 2026-08-20. Ce bloc
         * affirmait « chauffeur COUPE » pour TOUTE valeur absente, y compris
         * juste apres un `capteurs gaz on` : l'inverse exact de ce que
         * l'operateur venait de commander, sans aucun moyen de distinguer les
         * deux. `s_gaz_ohms` est ABSENT dans TROIS cas — coupe, jamais lu, et
         * « il chauffe mais la mesure n'est pas encore utilisable ». */
        printf("gaz (MOX)  : ⏳ LE CHAUFFEUR TOURNE, mais la mesure n'est PAS encore\n");
        printf("             utilisable : le composant rend `gas_valid` ou\n");
        printf("             `heater_stable` a faux. ⛔ RIEN n'est publie, et rien\n");
        printf("             n'entre dans `w2` — au premier cycle la plaque n'est\n");
        printf("             pas a 300 C, `adc_gas` vaut ~0, et la compensation\n");
        printf("             rend ~12,9 MOhm : un artefact qui fixerait le min/max\n");
        printf("             de toute la fenetre W2.\n");
    } else if (dn_capt_gaz_actif()) {
        printf("gaz (MOX)  : chauffeur DEMANDE, mais AUCUNE lecture BME680 valide\n");
        printf("             depuis le boot (ou depuis la derniere\n");
        printf("             reconfiguration). ⛔ Ce n'est PAS « chauffeur coupe ».\n");
    } else {
        printf("gaz (MOX)  : chauffeur COUPE (defaut) — aucune resistance publiee.\n");
        printf("             ⛔ ABSENT et non 0 : zero ohm serait une valeur\n");
        printf("             PHYSIQUE (un court-circuit), donc un mensonge\n");
        printf("             plausible. `capteurs gaz on` pour un A/B DECLARE.\n");
    }
    /* 🔴 CR dn4-2 — LECTURE ATOMIQUE. Les deux appels independants laissaient
     * la console observer un etat A DEMI mis a jour (le chemin d'echec ecrit
     * `s_chip_id = 0` PUIS `s_id_lue = false`) et imprimer « chip id 0x00 …
     * A REPONDU, mais ce n'est PAS un BME680 » — la phrase exacte que le
     * correctif d'origine existe pour rendre impossible. */
    bool id_tentee = false, id_lue = false, var_lu = false;
    uint8_t cid = 0, cvar = 0;
    dn_capt_identite_snapshot(&id_tentee, &id_lue, &cid, &var_lu, &cvar);
    if (!id_tentee) {
        /* 🔴 CR dn4-2 : le 3e etat. « aucune lecture tentee » n'est pas « la
         * lecture a echoue » — envoyer verifier une adresse quand rien n'a ete
         * demande, c'est encore affirmer sur un capteur muet. */
        printf("identite   : ⛔ NON RELEVEE — AUCUNE transaction n'a ete TENTEE\n");
        printf("             (bus I2C absent, ou ouverture du device refusee).\n");
        printf("             Ce n'est ni « il a repondu 0x00 » ni « il n'a pas\n");
        printf("             repondu » : on n'a rien demande.\n");
    } else if (!id_lue) {
        /* 🔴 dn4-2 : TROISIEME CAS. « chip id 0x00 » etait une AFFIRMATION SUR LE
         * CAPTEUR alors qu'il n'avait rien dit — mesure du 2026-08-20, ou le
         * bandeau annoncait 0x00 pendant que `i2c lire 77 D0` rendait 61. */
        printf("identite   : ⛔ NON LUE — la transaction I2C a ECHOUE. Ce n'est PAS\n");
        printf("             « il a repondu 0x00 » : il n'a RIEN repondu. Trancher\n");
        printf("             par `i2c` puis `i2c lire %02X D0` (attendu 0x%02X).\n",
               DN_BME680_ADDR, DN_BME680_CHIP_ID);
    } else if (cid != DN_BME680_CHIP_ID) {
        printf("identite   : chip id 0x%02X => A REPONDU, mais ce n'est PAS un "
               "BME680\n", cid);
    } else if (!var_lu) {
        /* 🔴 CR dn4-2 : le variant ne s'affirme que s'il a ete LU. 0x00 est la
         * valeur LEGITIME du BME680 — un variant rate se lisait donc comme un
         * verdict, et un BME688 passait pour un BME680. */
        printf("identite   : chip id 0x%02X · variant ⛔ NON LU => BME680 ou "
               "BME688\n", cid);
        printf("             ⚠️ 0x00 est la valeur LEGITIME du BME680 : la valeur\n");
        printf("             seule ne peut pas porter l'echec. Trancher par\n");
        printf("             `i2c lire %02X F0`.\n", DN_BME680_ADDR);
    } else {
        printf("identite   : chip id 0x%02X · variant 0x%02X => %s\n", cid, cvar,
               cvar == DN_BME680_VARIANT_688 ? "BME688" : "BME680");
    }
    /* 🔴 LES REGISTRES RELUS, PAS LA CONFIG DEMANDEE. Cette ligne a MENTI le
     * 2026-08-17 : elle annonçait « FORCED · T/H 8x · P 1x · IIR 3 » pendant que
     * le capteur etait a 0x00 partout, remis a ses defauts par une coupure de son
     * 3V3. Une ombre logicielle qui ne suit pas le materiel est un defaut — la
     * regle existait deja a cote (dn_display_backlight_pct_state). */
    /* 🔴 « NON CONFORME » et « pas de verdict » sont DEUX choses — CR 2026-08-17.
     * Les confondre faisait imprimer `0x72=00 0x74=00 0x75=00 🔴 NON CONFORME`
     * puis « le capteur a REDEMARRE et perdu sa config » sur une carte demarree
     * capteur DEBRANCHE — pour une puce qui n'a jamais ete la et n'a jamais rien
     * publie. L'init promettait pourtant que la garde « sera INERTE, ET ELLE LE
     * DIRA » : elle ne le disait pas. */
    if (!dn_capt_config_verdict_dispo()) {
        printf("config LUE : indisponible — la reference n'a pas pu etre lue a\n");
        printf("             l'init (capteur absent, ou transaction perdue). La\n");
        printf("             garde de reconfiguration est INERTE : ce n'est PAS un\n");
        printf("             verdict « non conforme », c'est une ABSENCE de verdict.\n");
    } else {
        printf("config LUE : 0x72=%02X · 0x74=%02X · 0x75=%02X %s\n",
               dn_capt_reg_ctrl_hum(), dn_capt_reg_ctrl_meas(),
               dn_capt_reg_config(),
               dn_capt_config_conforme() ? "(conforme)" : "🔴 NON CONFORME");
        if (!dn_capt_config_conforme()) {
            printf("             => le capteur a REDEMARRE et perdu sa config. Ses\n");
            printf("                valeurs sont FAUSSES *et* plausibles — aucune "
                   "borne\n");
            printf("                physique ne peut les voir. Reconfiguration au "
                   "cycle\n");
            printf("                suivant ; les cases passent a « -- » "
                   "entre-temps.\n");
        }
    }
    /* ⚠️ Les libelles viennent de dn_capteurs (DN_CAPT_*_TXT), plus d'un litteral
     * code en dur ici — CR 2026-08-17. Toute la correction de §13.10 consistait a
     * interdire a une ombre logicielle de faire autorite ; la ligne « config LUE »
     * avait ete corrigee, et ce litteral-la garde UNE LIGNE PLUS BAS. Changer un
     * surechantillonnage dans config_voulue() faisait diverger les deux lignes
     * sans raison visible. */
    printf("demande    : %s · T/H %s · P %s · IIR %s · gaz %s\n", DN_CAPT_MODE_TXT,
           DN_CAPT_OSR_TH_TXT, DN_CAPT_OSR_P_TXT, DN_CAPT_IIR_TXT,
           dn_capt_gaz_actif() ? "ACTIF (le die chauffe — biaise la temperature)"
                               : "coupe");
    printf("cadence    : %d ms nominale · peremption %lld ms, en temps absolu\n",
           DN_CAPT_PERIODE_MS, (long long)(DN_CAPT_PEREMPTION_US / 1000));
    /* AC7 demande la cadence EFFECTIVE, pas la constante de compilation : une
     * tache qui derive ou qui saute des cycles doit pouvoir se voir. */
    int64_t cad = dn_capt_cadence_reelle_us();
    if (cad >= 0) {
        printf("             %lld ms MESURES entre les deux dernieres lectures "
               "valides\n",
               (long long)(cad / 1000));
    }
    int64_t cyc = dn_capt_duree_cycle_us();
    if (cyc >= 0) {
        printf("cycle      : %lld ms MESURES pour la derniere lecture reussie\n",
               (long long)(cyc / 1000));
    }
    if (dn_capt_faute_active() != DN_CAPT_FAUTE_AUCUNE) {
        printf("🔴 FAUTE SIMULEE ACTIVE : %s — %d cycle(s) restant(s).\n",
               dn_capt_faute_nom(dn_capt_faute_active()), dn_capt_faute_restants());
        printf("             AUCUN chiffre releve maintenant n'est un chiffre REEL.\n");
    }
    dn_capt_compteurs_t c;
    dn_capt_compteurs(&c);
    printf("compteurs  : %u lectures · %u reprises · %u reconfigurations\n",
           (unsigned)c.lectures, (unsigned)c.reprises, (unsigned)c.reconfigs);
    if (c.reconfigs > 0) {
        printf("             reconfigurations = le capteur a redemarre sous nos\n");
        printf("             pieds (coupure d'alim). NI une erreur de transport, NI\n");
        printf("             une valeur aberrante, NI un silence : son propre seau.\n");
    }
    printf("erreurs    : i2c %u · donnee %u · bornes %u\n", (unsigned)c.err_i2c,
           (unsigned)c.err_donnee, (unsigned)c.err_bornes);
    printf("             i2c = le capteur ne repond plus (fil, soudure) · donnee =\n");
    printf("             il repond mais la conversion n'arrive JAMAIS — DEUX\n");
    printf("             diagnostics opposes, deux seaux (lecon dn2-2). ⚠️ Le\n");
    printf("             discriminant est la DUREE : seule la boucle « data ready »\n");
    printf("             du composant peut consommer ses 1 500 ms (CR 2026-08-17 —\n");
    printf("             les deux tombaient dans `i2c`, et `donnee` ne pouvait pas\n");
    printf("             quitter 0).\n");
    if (c.pousses_ratees > 0) {
        printf("ecran      : 🔴 %u poussee(s) PERDUE(S) — verrou LVGL indisponible\n",
               (unsigned)c.pousses_ratees);
        printf("             (2 tentatives). La valeur etait BONNE, l'ecran est\n");
        printf("             reste sur le cycle precedent. Ce n'est PAS une erreur\n");
        printf("             de capteur : son propre seau, hors des 3 causes d'AC7.\n");
    }
    return 0;
}

#define DN_CMD(name, helptext, fn) \
    {.command = (name), .help = (helptext), .hint = NULL, .func = (fn)}

/*
 * ── `rtc` — L'HEURE, ET SURTOUT SON HONNETETE (dn3-2, AC3) ───────────────────
 *
 * ⚠️ Elle RELIT les registres a chaque appel au lieu de reciter l'etat cache :
 *    une commande qui reciterait ne pourrait pas voir une horloge qui vient de
 *    mourir. Cout : une transaction I2C (~1 ms), acceptable pour le REPL —
 *    ⛔ contrairement a `build_scene()`, qui coute 307-322 ms et que AUCUNE
 *      commande ne doit declencher (le REPL EST le transport PC).
 */
static void rtc_usage(void)
{
    printf("usage : rtc                        etat, registres bruts, compteurs\n");
    printf("        rtc set <AAAA-MM-JJ> <HH:MM[:SS]>   pose l'heure (remet OS a 0)\n");
    printf("        rtc reset                  remet les compteurs a zero\n");
}

static int cmd_rtc(int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "reset") == 0) {
        dn_rtc_reset_compteurs();
        printf("compteurs de l'horloge remis a zero.\n");
        return 0;
    }

    if (argc >= 3 && strcmp(argv[1], "set") == 0) {
        dn_rtc_heure_t h = {0};
        unsigned a = 0, mo = 0, j = 0, hh = 0, mi = 0, ss = 0;
        int n = 0;
        if (argc == 4) {
            n = sscanf(argv[2], "%u-%u-%u", &a, &mo, &j);
            n += sscanf(argv[3], "%u:%u:%u", &hh, &mi, &ss);
        }
        /* 3 champs de date + AU MOINS 2 de temps (les secondes sont
         * optionnelles : la maquette ne les affiche pas, les taper serait une
         * precision qu'on n'a pas). */
        if (argc != 4 || n < 5) {
            rtc_usage();
            return 1;
        }
        /* 🔴 BORNÉ SUR LES `unsigned`, AVANT LES CASTS — correctif de revue
         *    (2026-08-18). Les champs étaient narcissés en uint8_t/uint16_t
         *    d'abord : `rtc set 2026-08-18 256:00` donnait hh = 0 et posait
         *    00:00 EN RAPPORTANT UN SUCCES, pour une heure jamais tapee. Idem
         *    « 10:256 » (minute -> 0) et « 67536-08-18 » (annee tronquee a
         *    exactement 2000, donc DANS l'epoque, donc acceptee). Ecreter une
         *    saisie en silence est le meme defaut qu'afficher un chiffre sans
         *    source : ce depot refuse, il REFUSE. */
        if (a > 9999 || mo > 12 || j > 31 || hh > 23 || mi > 59 || ss > 59) {
            printf("valeur HORS PLAGE — refusee, pas ecretee.\n");
            printf("   annee 0..9999 · mois 1..12 · jour 1..31 · %s\n",
                   "heure 0..23 · minute 0..59 · seconde 0..59");
            return 1;
        }
        h.annee = (uint16_t)a;
        h.mois = (uint8_t)mo;
        h.jour = (uint8_t)j;
        h.heure = (uint8_t)hh;
        h.minute = (uint8_t)mi;
        h.seconde = (uint8_t)ss;
        esp_err_t e = dn_rtc_poser(&h);
        if (e == ESP_ERR_INVALID_STATE) {
            printf("horloge NON ARMEE — rien a poser. `rtc` dira pourquoi.\n");
            return 1;
        }
        if (e == ESP_ERR_INVALID_ARG) {
            printf("date ou heure INVALIDE. Epoque du driver : %d..%d.\n",
                   DN_RTC_ANNEE_BASE, DN_RTC_ANNEE_BASE + 99);
            printf("⚠️ Le jour de semaine n'est PAS demande : il est CALCULE de la\n");
            printf("   date. La puce ne le deduit pas, elle le compte a part —\n");
            printf("   le laisser saisir ferait deux sources de verite.\n");
            return 1;
        }
        if (e != ESP_OK) {
            printf("🔴 ECRITURE REFUSEE ou OS RESTE A 1 — la pose n'a PAS pris.\n");
            printf("   (l'ecriture est RELUE : un ESP_OK d'I2C ne prouve rien.)\n");
            return 1;
        }
        dn_rtc_heure_t relu;
        bool fiable = dn_rtc_lire(&relu);
        /* ⚠️ CE QUI EST RELU, ET CE QUI NE L'EST PAS (revue 2026-08-18). Cette
         *    ligne affiche le CACHE du module, donc ce que la pose vient d'y
         *    écrire. La vraie relecture est faite DANS `dn_rtc_poser`, qui
         *    compare désormais LES SEPT registres à ce qu'il a écrit — avant,
         *    il ne relisait que le bit OS du registre des secondes, et cette
         *    ligne ré-affichait la saisie de l'operateur en l'annoncant
         *    « RELUE ». */
        printf("heure posee : %04u-%02u-%02u %02u:%02u:%02u — etat %s\n",
               relu.annee, relu.mois, relu.jour, relu.heure, relu.minute,
               relu.seconde, dn_rtc_etat_nom(dn_rtc_etat()));
        printf("   (les 7 registres ont ete RELUS et COMPARES a l'ecriture ;\n");
        printf("    la seconde affichee est celle que la PUCE porte.)\n");
        printf("OS est retombe a 0 : la barre passe de « --:-- HEURE NON POSEE »\n");
        printf("a l'heure reelle%s.\n", fiable ? "" : " (des le prochain cycle)");
        return 0;
    }

    if (argc != 1) {
        rtc_usage();
        return 1;
    }

    dn_rtc_etat_t etat = dn_rtc_etat();
    printf("horloge PCF85063A @ 0x%02X : %s\n", DN_RTC_ADDR,
           dn_rtc_arme() ? dn_rtc_etat_nom(etat) : "NON ARMEE");
    if (!dn_rtc_arme()) {
        printf("  le device I2C n'existe pas : soit le bus etait absent au boot,\n");
        printf("  soit Control_1 etait illisible, soit xTaskCreate a echoue.\n");
        printf("  ⇒ la barre affiche « --:-- HEURE NON POSEE », et c'est CORRECT.\n");
        return 0;
    }

    dn_rtc_heure_t h;
    bool fiable = dn_rtc_lire(&h);
    int64_t age = dn_rtc_age_us();
    /* 🔴 LA VALEUR ET SA RECEVABILITE SONT IMPRIMEES ENSEMBLE. `dn_rtc_lire()`
     *    rend le VERDICT D'HONNETETE, pas un code d'erreur de transport :
     *    imprimer l'heure sans lui, c'est exactement le mensonge que la barre a
     *    interdiction de commettre — sur l'autre surface de rendu. */
    printf("lue        : %04u-%02u-%02u %02u:%02u:%02u (jour de semaine %u) — %s\n",
           h.annee, h.mois, h.jour, h.heure, h.minute, h.seconde, h.jsem,
           fiable ? "AFFICHABLE" : "⛔ NON AFFICHABLE (la barre ne la montrera pas)");
    printf("age        : ");
    if (age < 0) {
        printf("aucune lecture valide depuis le boot\n");
    } else {
        printf("%lld ms (peremption %lld ms, en temps absolu)\n",
               (long long)(age / 1000), (long long)(DN_RTC_PEREMPTION_US / 1000));
    }

    /*
     * 🔴 LE BIT OS EST LE TEMOIN D'HONNETETE, ET IL EST IMPRIME EN CLAIR.
     */
    printf("bit OS     : %d — %s\n", dn_rtc_os() ? 1 : 0,
           dn_rtc_os() ? "🔴 L'OSCILLATEUR S'EST ARRETE : l'heure lue NE VAUT RIEN"
                       : "✅ l'oscillateur n'a pas decroche depuis la derniere pose");
    if (dn_rtc_os()) {
        printf("  Deux causes indiscernables, meme consequence : l'heure n'a JAMAIS\n");
        printf("  ete posee, ou elle a ete PERDUE (coupure). `rtc set` la pose.\n");
        printf("  ⛔ La barre n'affichera JAMAIS cette heure-la : une barre qui dit\n");
        printf("     « 03:47 » apres une coupure est PIRE qu'une barre qui se tait.\n");
    }

    /*
     * Le temoin anti-fantome. Voir `temoin_poser()` dans dn_rtc.c pour le motif
     * du choix de registre — Control_1 NE POUVAIT PAS voir un redemarrage,
     * puisque sa valeur de sortie de reset est exactement celle qu'on mesure.
     */
    /*
     * 🔴 LE VERDICT CROSS-BOOT D'ABORD — c'est celui qui repond a la RETENTION,
     *    et c'est celui qui MANQUAIT le 2026-08-18 : le temoin etait reecrit a
     *    chaque init, donc il valait 0xD7 apres toute coupure et `rtc` annoncait
     *    « la puce n'a pas redemarre » precisement quand elle venait de le faire.
     */
    uint8_t tb = 0;
    printf("retention  : ");
    if (!dn_rtc_temoin_boot(&tb)) {
        printf("INDISPONIBLE — le temoin n'a pas pu etre relu au boot\n");
    } else if (tb == DN_RTC_TEMOIN) {
        printf("0x%02X relu AU BOOT = attendu ⇒ ✅ la puce a GARDE son "
               "alimentation\n             depuis le dernier demarrage\n",
               tb);
    } else {
        printf("0x%02X relu AU BOOT (attendu 0x%02X) ⇒ 🔴 ELLE A PERDU SON\n"
               "             ALIMENTATION depuis le dernier demarrage — l'heure\n"
               "             qu'elle portait est morte avec.\n",
               tb, DN_RTC_TEMOIN);
        printf("             📌 MESURE DU 2026-08-18 : cette carte N'A AUCUNE\n");
        printf("             SAUVEGARDE. Coupure USB de 30 s ⇒ OS=1 et\n");
        printf("             2000-01-01 00:00:54. D5 (« pas de batterie ») ne\n");
        printf("             disait rien d'une cellule de backup du RTC : il n'y\n");
        printf("             en a pas. `rtc set` apres chaque coupure secteur.\n");
    }

    printf("temoin     : ");
    if (!dn_rtc_temoin_dispo()) {
        printf("INDISPONIBLE — la garde est INERTE (et le dit, au lieu de\n");
        printf("             se declarer « conforme » sans rien verifier)\n");
    } else {
        uint8_t t = dn_rtc_temoin_lu();
        printf("0x%02X en 0x%02X (attendu 0x%02X) — %s\n", t, DN_RTC_REG_RAM,
               DN_RTC_TEMOIN,
               t == DN_RTC_TEMOIN
                   ? "✅ pas de redemarrage EN COURS DE ROUTE (verdict RUNTIME)"
                   : "🔴 ELLE A REDEMARRE SOUS NOS PIEDS");
    }
    printf("Control_1  : 0x%02X a l'init, 0x%02X maintenant%s\n",
           dn_rtc_ctrl1_init(), dn_rtc_ctrl1_lu(),
           dn_rtc_ctrl1_init() == dn_rtc_ctrl1_lu() ? "" : "  ⚠️ IL A CHANGE");
    printf("             STOP=%d · format %s · quartz %s\n",
           (dn_rtc_ctrl1_lu() & DN_RTC_BIT_STOP) ? 1 : 0,
           (dn_rtc_ctrl1_lu() & 0x02) ? "12 h" : "24 h",
           (dn_rtc_ctrl1_lu() & 0x01) ? "12,5 pF" : "7 pF");
    printf("             ⚠️ CAP_SEL n'est PAS verifie : rien sur cette carte ne dit\n");
    printf("                quel quartz est soude. Mauvais reglage = DERIVE, pas panne.\n");

    uint8_t regs[DN_RTC_REG_MAX];
    if (dn_rtc_registres(regs, sizeof(regs)) == ESP_OK) {
        printf("registres 0x00..0x%02X (RELUS a l'instant) :\n", DN_RTC_REG_MAX - 1);
        printf("  ");
        for (unsigned i = 0; i < sizeof(regs); i++) {
            printf("%02X ", regs[i]);
        }
        printf("\n");
    } else {
        printf("registres  : LECTURE ECHOUEE a l'instant\n");
    }

    dn_rtc_compteurs_t c;
    dn_rtc_compteurs(&c);
    printf("compteurs  : %u lectures · %u reprises · %u poses\n",
           (unsigned)c.lectures, (unsigned)c.reprises, (unsigned)c.poses);
    printf("erreurs    : i2c %u · bcd %u\n", (unsigned)c.err_i2c,
           (unsigned)c.err_bcd);
    printf("             i2c = elle ne repond plus · bcd = elle repond mais rend\n");
    printf("             un quartet > 9. DEUX diagnostics opposes, deux seaux\n");
    printf("             (lecon dn2-2 : les confondre envoie chercher la panne du\n");
    printf("             cote du cablage, qu'on vient de prouver bon).\n");
    printf("rejets     : bascule %u · poussee perdue %u\n", (unsigned)c.bascules,
           (unsigned)c.poussees_perdues);
    printf("             🔴 DEUX SEAUX AJOUTES EN REVUE (2026-08-18). Avant, la\n");
    printf("             BASCULE — la seconde a tourne entre le burst et sa\n");
    printf("             relecture, « ni erreur ni donnee » — tombait dans `bcd`\n");
    printf("             et faisait chercher un quartet > 9 sur une puce SAINE.\n");
    printf("             POUSSEE PERDUE = le verrou LVGL n'a pas ete pris, la\n");
    printf("             barre garde son texte ; sans ce compteur une barre\n");
    printf("             figee par contention etait indiscernable d'une barre\n");
    printf("             a jour. Les deux sont NORMAUX en petit nombre.\n");
    printf("etats      : OS vu %u fois · temoin perdu %u fois\n", (unsigned)c.os_vus,
           (unsigned)c.temoins_perdus);
    printf("pile tache : %u o libres sur 4096 (high-water mark RELU)\n",
           (unsigned)dn_rtc_pile_libre());
    printf("             ⚠️ RAM INTERNE — la ressource meme qui a tue la branche\n");
    printf("             WiFi en dn2-2. Reduire cette pile demandera CE chiffre.\n");
    char bh[24] = "?", bd[32] = "?";
    dn_ui_barre_txt(bh, sizeof(bh), bd, sizeof(bd));
    /* 🔴 dn4-13 / AC1 — TROIS ETATS. Un verrou non pris n'est PAS « pas
     *    dessinee » : c'est « je n'ai pas pu regarder ». */
    bool bdess = false;
    bool bdess_mesuree = dn_ui_barre_dessinee(&bdess);
    printf("barre      : %s · « %s » / « %s » · %s\n",
           dn_ui_barre_secondes() ? "HH:MM:SS (1 Hz)" : "HH:MM (au changement de minute)",
           bh, bd,
           !bdess_mesuree ? "PAS MESUREE (verrou LVGL non pris)"
                          : (bdess ? "DESSINEE"
                                   : "PAS dessinee (ui off / scene / tear / vue detail)"));
    printf("epoque     : %d..%d — CHOIX du driver, pas de la puce : le PCF85063A\n",
           DN_RTC_ANNEE_BASE, DN_RTC_ANNEE_BASE + 99);
    printf("             porte l'annee sur 0..99 et n'a AUCUN bit de siecle.\n");
    return 0;
}

/*
 * `env` — LES TROIS CAPTEURS D'ENVIRONNEMENT LOCAUX (dn4-3, AC1).
 *
 * ⚠️ Comme `capteurs`, elle NE DÉCLENCHE AUCUNE MESURE : elle lit ce que le
 *    cycle a publié. Le seul chiffre qu'elle produit elle-même est l'âge.
 * ⛔ Commande DÉDIÉE, et pas une extension de `capteurs` : celle-ci est le
 *    module BME680 par conception assumée (dn_capteurs.h:8-10), et deux modules
 *    sous une seule commande rendraient illisible lequel est muet.
 */
static void env_ligne_compteurs(dn_env_id_t id)
{
    dn_env_compteurs_t c;
    dn_env_compteurs(id, &c);
    printf("  compteurs : %lu lectures · %lu reprises\n",
           (unsigned long)c.lectures, (unsigned long)c.reprises);
    printf("  erreurs   : i2c %lu · donnee %lu · bornes %lu · conformite %lu\n",
           (unsigned long)c.err_i2c, (unsigned long)c.err_donnee,
           (unsigned long)c.err_bornes, (unsigned long)c.conformite);
}

static void env_entete(dn_env_id_t id, const char *valeurs)
{
    int64_t age = dn_env_age_us(id);
    printf("\n%-7s @ 0x%02X : %s", dn_env_nom(id), dn_env_adresse(id),
           dn_env_etat_nom(dn_env_etat(id)));
    if (valeurs && valeurs[0]) {
        printf(" — %s", valeurs);
    }
    if (age >= 0) {
        printf(" · age %lld ms", (long long)(age / 1000));
    } else {
        printf(" · JAMAIS LU");
    }
    if (!dn_env_present(id)) {
        printf(" · ⛔ DEVICE NON OUVERT");
    }
    printf("\n");
}

static int cmd_env(int argc, char **argv)
{
    /* ⛔ `argc != 2`, PAS `argc >= 2` : `env reset extra` remettait les
     * compteurs a zero en ignorant le token de trop (revue de code 2026-08-20). */
    if (argc == 2 && strcmp(argv[1], "reset") == 0) {
        dn_env_compteurs_reset();
        printf("compteurs de dn_env remis a zero (et l'etat `degrade` avec —\n");
        printf("sinon la premiere lecture valide comptait une reprise d'AVANT\n");
        printf("le reset dans la fenetre d'APRES).\n");
        return 0;
    }
    if (argc >= 2) {
        printf("usage : env | env reset — rien n'a ete touche.\n");
        return 1;
    }

    uint32_t cycles = dn_env_cycles();
    printf("capteurs d'environnement locaux (dn4-3) — AUCUNE tache propre :\n");
    printf("ils sont cadences par la tache `dn_capt`, toutes les %d ms, et\n",
           DN_ENV_PERIODE_MS);
    printf("l'appel est place AVANT toute branche de sa boucle (sinon il serait\n");
    printf("saute a chaque erreur du BME680 — voir §13.19.4).\n");
    if (cycles == 0) {
        /* 🔴 DEUX CAUSES OPPOSEES, DEUX PHRASES — corrige en revue de code le
         * 2026-08-20. Ce bloc accusait la tache `dn_capt` et renvoyait vers
         * `capteurs`, qui aurait montre une tache en PARFAITE SANTE si la vraie
         * cause etait l'echec de `dn_env_init()` (bus indisponible) : le cycle
         * retourne alors tot sur `!s_init_faite` et n'incremente jamais
         * `s_cycles`. C'est la faute meme que « TROIS ETATS, TROIS PHRASES »
         * (cmd_capteurs) a ete ecrit pour eliminer. */
        printf("\n🔴 JAMAIS CADENCE : aucun cycle depuis le boot.\n");
        if (!dn_env_present(DN_ENV_LUM) && !dn_env_present(DN_ENV_ALIM) &&
            !dn_env_present(DN_ENV_TOF)) {
            printf("   AUCUN device n'est ouvert ⇒ `dn_env_init()` a echoue (bus\n");
            printf("   I2C indisponible), OU les trois ouvertures ont ete\n");
            printf("   refusees. ⛔ Ce n'est PAS un diagnostic sur `dn_capt` :\n");
            printf("   le bandeau de boot porte la ligne `dn_env`.\n");
        } else {
            printf("   Des devices SONT ouverts, donc `dn_env_init()` a tourne :\n");
            printf("   c'est la cadence qui manque ⇒ la tache `dn_capt` n'a pas\n");
            printf("   demarre — `capteurs` dira pourquoi (mode d'echec\n");
            printf("   realiste : xTaskCreate, donc penurie de RAM interne).\n");
        }
        printf("   ⛔ Tout ce qui suit serait du vide.\n");
    } else {
        printf("cycles     : %lu · dernier cycle %lld us MESURES\n",
               (unsigned long)cycles, (long long)dn_env_duree_cycle_us());
    }
    printf("peremption : %lld ms (3 cycles) — MEME convention que dn_capteurs,\n",
           (long long)(DN_ENV_PEREMPTION_US / 1000));
    printf("             ⛔ pas les 3 s de dn_link. timeout I2C %d ms.\n",
           DN_ENV_I2C_TIMEOUT_MS);
    printf("garde anti-fantome : UNE LECTURE par cycle, ⛔ AUCUNE ECRITURE en\n");
    printf("             regime. La config est ecrite UNE FOIS a l'ouverture et\n");
    printf("             RELUE ensuite : meme pouvoir discriminant qu'une\n");
    printf("             ecriture (un fantome ne tient pas la valeur), sans\n");
    printf("             ajouter un agresseur permanent sur le bus.\n");

    /* ── BH1750 ── */
    {
        char v[64] = "";
        /* 🔴 LECTURE ATOMIQUE (CR dn4-2) — corrigee en revue de code le
         * 2026-08-20 : deux appels separes prenaient DEUX sections critiques et
         * pouvaient imprimer « 411 lx (brut 500) », un couple qui n'a jamais
         * existe. Le cycle publie les deux sous UN seul verrou. */
        int lux = DN_ENV_ABSENT, lux_brut = DN_ENV_ABSENT;
        dn_env_lux_lire(&lux, &lux_brut);
        if (lux != DN_ENV_ABSENT) {
            snprintf(v, sizeof v, "%d lx (brut %d)", lux, lux_brut);
        }
        env_entete(DN_ENV_LUM, v);
        env_ligne_compteurs(DN_ENV_LUM);
        printf("  garde     : 🔴 AUCUNE, et c'est DECLARE. Le BH1750 n'a AUCUN\n");
        printf("              registre relisible : son seul registre ecrivable\n");
        printf("              est le MTreg, et il est NON RELISIBLE (piste\n");
        printf("              tentee, NON REPRODUITE). Sa qualification la plus\n");
        printf("              forte reste le STIMULUS (main posee), qui demande\n");
        printf("              un geste owner : ⛔ ce n'est donc PAS une garde de\n");
        printf("              regime. `conformite` reste a 0 A VIE ici.\n");
        printf("  bornes    : 0xFFFF compte en `bornes` — c'est le PLAFOND du\n");
        printf("              convertisseur (au moins 54612 lx), plus une mesure.\n");
        printf("              ⚠️ brut 0 est LEGITIME (obscurite) : la main posee a\n");
        printf("              mesure brut 2, pas 0. `donnee` ne compte que le 0\n");
        printf("              lu dans les 180 ms d'une (re)configuration — ⛔ et\n");
        printf("              ce seau reste donc a 0 SAUF si une configuration a\n");
        printf("              echoue puis ete REPOSEE : tout appel a configurer()\n");
        printf("              est suivi d'un `return`, la lecture suivante arrive\n");
        printf("              5000 ms plus tard. DECLARE en revue de code.\n");
        printf("              Source : ROHM BH1750FVI-TR, plage 1-65535 lx,\n");
        printf("              lux = brut / 1,2 au MTreg par defaut (69).\n");
        printf("  ⛔ NE JAMAIS republier des lux DIVISES PAR DIX : (brut*10)/12\n");
        printf("     EST deja la valeur en lux ENTIERS. L'imprimer comme des\n");
        printf("     dixiemes a publie « 4 614,8 » pour 46 148, TROIS FOIS.\n");
    }

    /* ── INA219 — INERTE DEPUIS LE CORRECT-COURSE DU 2026-08-20 ── */
    {
        env_entete(DN_ENV_ALIM, "⛔ INERTE — plus lu en regime");
        env_ligne_compteurs(DN_ENV_ALIM);
        printf("  🔴 CE COMPOSANT N'EST PLUS LU, ET C'EST UNE DECISION OWNER\n");
        printf("     (correct-course du 2026-08-20), pas une panne.\n");
        printf("  pourquoi   : `Vin+`/`Vin-` NE SONT PAS CABLES — `dn4-2` a\n");
        printf("               tranche « bus seulement ». Le shunt R100 (0,1 ohm)\n");
        printf("               n'est traverse par AUCUN courant, donc la puce ne\n");
        printf("               mesurait QUE DU BRUIT sur une entree flottante :\n");
        printf("               bus 904 mV, shunt -30 uV, -0,3 mA, 0 mW (mesure le\n");
        printf("               2026-08-20). X3 a ete tranche NON par A/B.\n");
        printf("  ce que ca  : 5 transactions I2C sur les 9 du cycle (56 %%) sont\n");
        printf("  rend       : rendues au bus — celui que §11.4 nomme « le PREMIER\n");
        printf("               AGRESSEUR CONNU » de la famine DMA, et qui se\n");
        printf("               degrade ~40 s a froid.\n");
        printf("  etat reel  : SOUDE et OUVERT, configure UNE FOIS au boot. ⛔ Il\n");
        printf("               n'est PAS dessoude (D9 : montage fini, le\n");
        printf("               dessoudage est un risque sur le bus pour ZERO\n");
        printf("               gain). Ses compteurs restent donc a zero A VIE.\n");
        printf("  ⚠️ POUR LE REMETTRE EN SERVICE, il faut du COURANT dans son\n");
        printf("     shunt. Le bornier a vis 2 points est DEJA SOUDE, donc\n");
        printf("     `Vin+`/`Vin-` sont accessibles SANS FER — mais VERIFIER\n");
        printf("     D'ABORD AU MULTIMETRE que le bornier est bien relie a\n");
        printf("     `Vin+`/`Vin-` : c'est le cablage standard CJMCU, et ce depot\n");
        printf("     ne l'a JAMAIS mesure.\n");
        printf("  ⛔ `Vin+`/`Vin-` NE SONT PAS UNE ALIMENTATION : y poser 5 V et\n");
        printf("     la masse court-circuiterait le shunt de 0,1 ohm. « Le miroir\n");
        printf("     tue » — c'est le piege nomme par dn4-2.\n");
        printf("  identite   : `i2c lire 40 00 2` rend `39 9F` (reset du registre\n");
        printf("               Configuration) — il repond toujours.\n");
    }

    /* ── VL6180X ── */
    {
        env_entete(DN_ENV_TOF, "presence et conformite SEULEMENT");
        env_ligne_compteurs(DN_ENV_TOF);
        printf("  garde     : ✅ FORTE — 003F (gain, reset 0x06 -> impose 0x46) et\n");
        printf("              0041 (integration, reset 0x00 -> impose 0x63),\n");
        printf("              RELUS a chaque cycle. `lectures` compte les\n");
        printf("              identites 0xB4 confirmees ; une autre valeur va en\n");
        printf("              `donnee` (il repond, mais ce n'est pas lui).\n");
        /* 🔴 CORRIGE LE 2026-08-21 — CE TEXTE AFFIRMAIT UNE CAUSE REFUTEE, ET
         * IL LE FAISAIT DEPUIS LE PRODUIT QUI TOURNE. Il disait « comparateur
         * sature » et « cause nommee : ST impose un chargement de registres
         * PRIVES ». LES DEUX SONT FAUX, mesures a l'appui (§13.21) :
         *   · SR03 SE CHARGE (38/38 ecritures, 30 registres prives relus
         *     EXACTEMENT) et le balayage d'integration est IDENTIQUE avant et
         *     apres ⇒ SR03 N'A JAMAIS ETE LA CAUSE ;
         *   · et ce n'est pas une saturation : l'ALS ne bouge pas sur 2 280x de
         *     lumiere (5 lx -> 11 418 lx, BH1750 en CONTROLE au meme instant) ni
         *     sur 40x de gain. Sa sortie ne depend QUE de la duree
         *     d'integration ⇒ un compteur sans signal photodiode.
         * ⛔ Une etiquette qui affirme une cause fausse est PIRE qu'une absence
         *    d'explication : elle envoie chercher au mauvais endroit. */
        printf("  🔴 AUCUNE GRANDEUR PUBLIEE, et voici pourquoi (AC8) : CE\n");
        printf("     COMPOSANT EST MORT COTE ANALOGIQUE. Son ALS ne reagit NI a\n");
        printf("     2 280x de lumiere (5 lx -> 11 418 lx, BH1750 en CONTROLE au\n");
        printf("     meme instant), NI a 40x de gain, NI a un cycle\n");
        printf("     d'alimentation. Sa sortie ne depend QUE de la duree\n");
        printf("     d'integration. Telemetrie : 0 sur 200 tirs, zero photon\n");
        printf("     jusque sur le canal de REFERENCE INTERNE.\n");
        printf("  ⛔ ET SR03 N'EST PAS LA CAUSE — ce texte l'a affirme jusqu'au\n");
        printf("     2026-08-21, A TORT : la sequence SE CHARGE (38/38, les 30\n");
        printf("     registres prives relus EXACTEMENT) et NE CHANGE RIEN.\n");
        printf("     Dossier complet : hardware/…-capteurs-i2c.md §13.20-§13.21.\n");
        printf("  ⚠️ 0x0016 (FRESH_OUT_OF_RESET) est un TEMOIN VALIDE lui aussi\n");
        printf("     (mesure : 0x01 au power-on, impose 0x00, relu 0x00) mais ce\n");
        printf("     module N'Y TOUCHE PAS : sa valeur est un FAIT sur\n");
        printf("     l'historique de la puce, et l'ecraser detruirait\n");
        printf("     l'information. `i2c lire16 29 0016 1` pour la lire.\n");
    }

    /* 🔴 ETIQUETTE PERIMEE, CORRIGEE EN SEANCE CARTE LE 2026-08-20 : cette
     * ligne affirmait « X2 n'est pas tranche » alors que X2 EST TRANCHE depuis
     * la seance du meme jour — c'est meme le resultat central de la story. Une
     * commande qui nie une decision owner est exactement l'etiquette qui ment
     * que ce depot traque, et elle etait dans le module que la revue venait
     * d'auditer. ⛔ Trouvee en LISANT LA SORTIE, pas le code. */
    printf("\n⛔ AUCUN de ces trois capteurs n'alimente une case, et c'est une\n");
    printf("   DECISION, pas un provisoire : X2 est TRANCHE — « AUCUNE 3e\n");
    printf("   grandeur, la case AMBIANCE reste a deux » (decision owner du\n");
    printf("   2026-08-20). Les QUATRE candidats ont ete mesures au MEME\n");
    printf("   instrument (`w2`) : pression 1 hPa d'etendue en 17 min, ALS\n");
    printf("   binaire, gaz sans reponse a deux bouffees, et le lux qualifie a\n");
    printf("   10-70x la reference — ce qui est justement l'argument CONTRE\n");
    printf("   (W2 est un seuil PLANCHER, pas un optimum).\n");
    printf("   ⇒ `env` est donc le SEUL endroit ou ces trois se lisent, et le\n");
    printf("     BH1750 a un SECOND emploi : il pilote le retroeclairage (`bl`).\n");
    return 0;
}

/*
 * `w2` — LE CRITÈRE « UNE CASE DE SIX DOIT BOUGER », MESURÉ (AC6).
 *
 * Patron `FAN_RPM` de dn4-6, jugé sur la valeur AFFICHÉE : étendue >= 5,
 * taux de changement du TEXTE >= 10 %, sigma >= 1.
 * ⛔ Ce n'est pas un avis sur la donnée, c'est un seuil écrit AVANT le tir.
 */
#define DN_W2_SEUIL_ETENDUE 5
#define DN_W2_SEUIL_TAUX_PCT 10
#define DN_W2_SEUIL_SIGMA_MILLI 1000 /* sigma >= 1,000 */

static int cmd_w2(int argc, char **argv)
{
    /* ⛔ `argc != 2`, PAS `argc >= 2` : `w2 reset extra` remettait TOUTES les
     * pistes a zero en ignorant le token de trop — et W2 est l'instrument qui
     * tranche X2 (revue de code 2026-08-20). */
    if (argc == 2 && strcmp(argv[1], "reset") == 0) {
        dn_w2_reset();
        printf("accumulateurs W2 remis a zero (LES CINQ PISTES).\n");
        return 0;
    }
    if (argc >= 2) {
        printf("usage : w2 | w2 reset — rien n'a ete touche.\n");
        return 1;
    }

    printf("W2 — « une case de six doit BOUGER », juge sur la valeur AFFICHEE\n");
    printf("seuils ECRITS AVANT le tir : etendue >= %d · taux de changement du\n",
           DN_W2_SEUIL_ETENDUE);
    printf("TEXTE >= %d %% · sigma >= 1,000\n", DN_W2_SEUIL_TAUX_PCT);
    printf("reference dn4-6 : FAN_RPM 13 / 55,2 %% / 2,02 (n=959) QUALIFIE ·\n");
    printf("                  ASIC_POWER 3 / 57,9 %% / 0,75 NE QUALIFIE PAS\n");
    printf("⚠️ echantillonne DANS LE FIRMWARE, un point par cycle de %d ms :\n",
           DN_ENV_PERIODE_MS);
    printf("   `dn_console.py` PERD DES LIGNES, et un taux calcule sur un\n");
    printf("   echantillonnage qui perd des points est faux d'un biais qu'on\n");
    printf("   ne sait pas borner.\n");
    printf("⛔ Seules les valeurs VALIDES sont echantillonnees : compter une\n");
    printf("   absence comme un changement gonflerait le taux d'un capteur MUET.\n\n");

    printf("%-34s %6s %8s %8s %9s %8s %8s  %s\n", "piste", "n", "min", "max",
           "etendue", "taux %", "sigma", "verdict");
    for (int i = 0; i < DN_W2_NB; i++) {
        dn_w2_t w;
        dn_w2_lire((dn_w2_id_t)i, &w);
        if (w.n == 0) {
            printf("%-34s %6d %8s %8s %9s %8s %8s  %s\n", dn_w2_nom((dn_w2_id_t)i),
                   0, "-", "-", "-", "-", "-", "AUCUN ECHANTILLON");
            continue;
        }
        int32_t etendue = w.max - w.min;
        /* Taux sur les TRANSITIONS observees, donc n-1 : le premier echantillon
         * n'a pas de precedent auquel se comparer. ⛔ Diviser par n gonflerait
         * les petits echantillons. */
        uint32_t transitions = (w.n > 1) ? (w.n - 1) : 1;
        uint32_t taux = (w.changements * 100u) / transitions;
        /* sigma en MILLIEMES, en entiers : variance = E[x²] - E[x]².
         * ⛔ Aucun flottant : le depot les interdit sur le fil, et une racine
         *    entiere par Newton suffit largement ici.
         *
         * 🔴 DEUX DEFAUTS CORRIGES EN REVUE DE CODE LE 2026-08-20 :
         *
         * (1) LA TRONCATURE ETAIT DU MEME ORDRE QUE LE SEUIL. `e_x2` etait
         *     tronque de pres de 1 AVANT d'etre multiplie par 1e6 : jusqu'a 1e6
         *     de variance jetee, alors que le seuil DN_W2_SEUIL_SIGMA_MILLI vaut
         *     1000, soit var = 1e6 tout rond. Mesure au papier : sigma vrai
         *     1,633 rendu 1,414 (-13 %) ; 0,748 rendu 0,600 (-20 %) ; 0,748
         *     rendu 0,000 (-100 %). Le biais allait TOUJOURS vers « NE QUALIFIE
         *     PAS ». ⇒ on multiplie AVANT de diviser. Le `if (var < 0)` d'avant
         *     etait la trace de ce defaut, platree au lieu d'etre corrigee.
         *     🔴 ET LE PREMIER JET DE CE CORRECTIF DEBORDAIT — trouve en
         *     preparant la seance carte, AVANT le flash, ⛔ pas sur la carte.
         *     Ecrire `(somme_carres * 1000000) / n` fait le PRODUIT D'ABORD :
         *     sur la piste lux (54 611 max, carre 2,98e9), int64 deborde a
         *     ~3 092 echantillons — soit **4,3 h** a 5 s, et `dn4-5` est un soak
         *     d'UNE SEMAINE. ⇒ on scinde en QUOTIENT + RESTE, ce qui garde la
         *     precision SANS jamais former le grand produit :
         *         E[x²]x1e6 = (S2/n)*1e6 + ((S2%n)*1e6)/n
         *     Marges : (S2/n)*1e6 <= 2,98e15 · (S2%n)*1e6 < n*1e6 <= 4,3e15
         *     (n est un uint32) · moy_x1000² <= 2,98e15. ⛔ Aucun ne s'approche
         *     de 9,22e18.
         *
         * (2) 🔴 LA RACINE NE TERMINAIT PAS. `while (r != prev)` sur une
         *     iteration de Newton ENTIERE entre dans un cycle de periode 2
         *     (a -> a+1 -> a -> …) pour toute valeur de la forme k²-1. Verifie
         *     par force brute : 446 valeurs piegent la boucle dans 1..199999.
         *     Cas ATTEIGNABLE : lux {0,0,0,3,3} (piece rideau ferme, l'owner a
         *     mesure 2 lx) donne var = 1 560 000 = 1249²-1, et r oscille
         *     1248 <-> 1249 POUR TOUJOURS. ⇒ la tache REPL part a 100 %, la
         *     console est perdue, le TWDT tombe, et avec PANIC_PRINT_HALT c'est
         *     « ni console ni flash, RESET physique obligatoire » — exactement
         *     ce que ce module est ecrit pour empecher.
         *     ⇒ `while (r < prev)`, le patron standard, + une borne d'iterations
         *       comme ceinture. */
        int64_t n64 = (int64_t)w.n;
        int64_t moy_x1000 = (w.somme * 1000) / n64;
        int64_t e_x2_x1e6 = (w.somme_carres / n64) * 1000000 +
                            ((w.somme_carres % n64) * 1000000) / n64;
        int64_t var_x1e6 = e_x2_x1e6 - moy_x1000 * moy_x1000;
        if (var_x1e6 < 0) {
            var_x1e6 = 0; /* arrondi entier residuel : la variance est >= 0 */
        }
        int64_t sigma_milli = 0;
        if (var_x1e6 > 0) {
            int64_t r = var_x1e6, prev = 0;
            /* Amorce : r = var, et on descend. La borne d'iterations est une
             * CEINTURE — Newton converge en O(log n), 64 tours sont un plafond
             * qu'aucune valeur d'int64 n'atteint. */
            for (int garde = 0; garde < 64; garde++) {
                prev = r;
                r = (r + var_x1e6 / r) / 2;
                if (r >= prev) {
                    r = prev;
                    break;
                }
            }
            sigma_milli = r;
        }
        bool ok_e = etendue >= DN_W2_SEUIL_ETENDUE;
        bool ok_t = taux >= (uint32_t)DN_W2_SEUIL_TAUX_PCT;
        bool ok_s = sigma_milli >= DN_W2_SEUIL_SIGMA_MILLI;
        char verdict[64];
        if (ok_e && ok_t && ok_s) {
            snprintf(verdict, sizeof verdict, "QUALIFIE");
        } else {
            snprintf(verdict, sizeof verdict, "NE QUALIFIE PAS (%s%s%s)",
                     ok_e ? "" : "etendue ", ok_t ? "" : "taux ",
                     ok_s ? "" : "sigma");
        }
        printf("%-34s %6lu %8ld %8ld %9ld %8lu %4lld,%03lld  %s\n",
               dn_w2_nom((dn_w2_id_t)i), (unsigned long)w.n, (long)w.min,
               (long)w.max, (long)etendue, (unsigned long)taux,
               (long long)(sigma_milli / 1000), (long long)(sigma_milli % 1000),
               verdict);
    }
    printf("\n⚠️ La duree de la fenetre est n x %d ms. Un verdict sur une fenetre\n",
           DN_ENV_PERIODE_MS);
    printf("   trop courte ne vaut rien : une pression atmospherique bouge sur\n");
    printf("   des HEURES, un lux de bureau sur des SECONDES. ⛔ Comparer deux\n");
    printf("   pistes exige la MEME fenetre, et c'est le cas ici : elles sont\n");
    printf("   remises a zero ensemble par `w2 reset`.\n");
    return 0;
}

/*
 * ── dn4-4 / AC5.6 : `hist` — LE COUT DE L'HISTORIQUE, ET SON HONNETETE ───────
 *
 * 🔴 IL PUBLIE LES TROUS AUTANT QUE LES POINTS. Une courbe qui « a l'air
 *    remplie » sans qu'on sache combien de ses points sont reels est
 *    exactement le genre de dessin auquel ce depot ne fait pas confiance :
 *    `reels` / `trous` sont donc COMPTES, par serie.
 * ⚠️ LE COUT EN RAM SE LIT ICI **ET** DANS `mem`. Ces octets vivent en `.bss`
 *    interne : ils apparaissent donc bien dans « RAM interne libre », ⛔ pas dans
 *    le tas LVGL (qui, lui, ne voit QUE les objets `lv_chart`).
 * 🔴 CHIFFRE CORRIGE LE 2026-08-24 (revue de code) — ⛔ PAS EFFACE : le
 *    commentaire disait « ~~les 3 360 o~~ », chiffre de **7 series sans seaux**.
 *    Le module pese aujourd'hui **~5 609 o** : 3 840 (points, 8 x 120 x 4)
 *    + 768 (`s_smin`) + 768 (`s_smax`) + 192 (`s_svu`) + 32 (`s_w`) + 9.
 * 🔴 ~~ET `dn_hist_octets()` NE REND QUE `sizeof(s_pts)` = 3 840 o : ce que cette
 *    commande imprime SOUS-DECLARE le cout de ~1 769 o (~32 %)~~ — **CORRIGE LE
 *    2026-08-25, dn4-13 / AC2.1**. Le bloc est CONSERVE BARRE : il dit pourquoi
 *    tout chiffre de cout publie AVANT cette date vaut 3 840 et pas 5 609, et
 *    c'est ce qui rend le releve d'AC5.6 non comparable au releve d'aujourd'hui.
 * ⚠️ LES TROIS TERMES SONT IMPRIMES SEPAREMENT. Un total seul ne se confronte pas
 *    au `.map` : c'est en voyant « points 3 840 / seaux 1 728 / index 41 » qu'on
 *    peut dire LEQUEL a bouge quand le total bouge.
 */
static int cmd_hist(int argc, char **argv)
{
    (void)argc;
    (void)argv;
    static const char *k_nom[DN_HIST_N_SERIES] = {
        "CPU", "GPU", "RAM", "RESEAU v", "DISQUE", "AMBIANCE T", "AMBIANCE RH",
        "RESEAU ^",
    };
    printf("historique de session (dn4-4) — EN RAM, ⛔ AUCUNE ecriture NVS/flash (D4)\n");
    {
        size_t hp = 0, hb = 0, hi = 0;
        size_t tot = dn_hist_octets_detail(&hp, &hb, &hi);
        printf("  cout .bss REEL du module : %u o\n", (unsigned)tot);
        printf("     points %d x %d x 4 = %u o\n", DN_HIST_N_SERIES,
               DN_HIST_N_POINTS, (unsigned)hp);
        printf("     seaux  s_smin + s_smax + s_svu = %u o\n", (unsigned)hb);
        printf("     index  s_w + s_pret + s_seau_courant = %u o\n", (unsigned)hi);
        printf("  ⚠️ CE TOTAL EST CELUI DU MODULE, ⛔ plus `sizeof(s_pts)` seul.\n");
        printf("     Jusqu'au 2026-08-25 cette ligne imprimait %u o : tout cout\n",
               (unsigned)hp);
        printf("     publie AVANT cette date sous-declare de %u o (%u %%).\n",
               (unsigned)(tot - hp),
               (unsigned)((tot - hp) * 100u / (tot ? tot : 1u)));
    }
    printf("  cadence : %d ms — une HORLOGE, ⛔ pas la cadence des trames\n",
           DN_HIST_PERIODE_MS);
    {
        /* 🔴 dn4-13 / AC3.1 — LE RATTRAPAGE SE DIT. Un comblement silencieux
         *    serait une reparation invisible, donc invérifiable : c'est ce
         *    compteur qui rend le temoin d'AC3.3 (`ui off` >= 60 s) LISIBLE
         *    autrement qu'a l'oeil. */
        uint32_t re = 0, rt = 0;
        dn_hist_rattrapages(&re, &rt);
        printf("  rattrapage : %lu coupure(s), %lu point(s) de trou comble(s)\n",
               (unsigned long)re, (unsigned long)rt);
        if (re == 0) {
            printf("     (aucune coupure depuis l'init — regime nominal)\n");
        } else {
            printf("     ⇒ l'anneau a AVANCE pendant la pause : la courbe ne relie\n");
            printf("       PAS les deux bords. ⛔ Sans ca, 60 s de `ui off` se\n");
            printf("       dessinaient comme UNE seconde.\n");
        }
    }
    printf("  profondeur : %d points a 1 Hz = %d s de session\n",
           DN_HIST_N_POINTS, DN_HIST_N_POINTS * DN_HIST_PERIODE_MS / 1000);
    /* 🔴 LA FENETRE LONGUE EST PUBLIEE AVEC SA COUVERTURE **REELLE**. Sans
     *    elle, « MIN/MAX sur 24 h » serait une etiquette, ⛔ pas une mesure —
     *    et la carte ne survit pas a un reboot (D4 : aucune ecriture NVS). */
    {
        printf("  fenetre LONGUE : %lu seau(x) d'1 h — couverture **PAR SERIE**\n",
               (unsigned long)DN_HIST_SEAUX);
        printf("  🔴 dn4-13 / AC2.2 : la couverture n'est PLUS l'uptime. Jusqu'au\n");
        printf("     2026-08-25 elle rendait min(uptime, 24 h) — carte allumee 1 h\n");
        printf("     SANS source PC, la page annoncait « MIN/MAX sur : 1 h » a cote\n");
        printf("     de « MIN -- · MAX -- ». Elle compte desormais les seaux QUI ONT\n");
        printf("     VU DU REEL, et rend 0 quand il n'y en a aucun.\n");
        printf("  ⛔ « 24 h » N'EST VRAI QUE SI LA CARTE A TOURNE 24 h : D4\n");
        printf("     interdit toute ecriture flash/NVS, donc ceci NE SURVIT PAS\n");
        printf("     a un reboot. La page affiche la fenetre REELLE, pas 24 h.\n");
    }
    /*
     * 🔴 dn4-13 / AC6.3 — « JAMAIS ECRIT » N'EST PAS « TROU », ET LES DEUX
     *    COLONNES EXISTENT MAINTENANT.
     *    Cette table imprimait « reels 10 · trous 110 » a t = 10 s, alors que
     *    110 cases N'AVAIENT JAMAIS ETE ATTEINTES. Un trou est une SECONDE OU LA
     *    SOURCE S'EST TUE — c'est une information ; une case jamais atteinte
     *    n'en est pas une. L'en-tete de cette commande revendiquait pourtant
     *    exactement cette distinction, deux ecrans plus haut.
     * 🔴 ET L'ETIQUETTE `min(2min)` ETAIT DU MEME BOIS : la fenetre courte ne
     *    vaut 2 min QUE si 120 positions ont ete ecrites. Elle est desormais
     *    `min(court)`, et la colonne `ecrits` DIT combien de secondes elle
     *    couvre reellement (1 position = 1 s, l'horloge est a 1 Hz).
     */
    printf("\n  serie        ecrits reels trous jamais couv(s)  min(court) max(court)  min(long) max(long)\n");
    for (int i = 0; i < DN_HIST_N_SERIES; i++) {
        int r = dn_hist_reels(i);
        int ec = dn_hist_ecrits(i);
        int32_t mn = 0, mx = 0, lm = 0, lx = 0;
        bool lok = dn_hist_minmax_long(i, &lm, &lx);
        printf("   %-12s %5d %5d %5d %6d %7lu", k_nom[i], ec, r, ec - r,
               DN_HIST_N_POINTS - ec,
               (unsigned long)dn_hist_couverture_s(i));
        (void)lok;
        if (dn_hist_minmax(i, &mn, &mx)) {
            /* ⚠️ EN DIXIEMES, ET C'EST DIT : cet instrument ne connait ni les
             *    unites ni les echelles hautes — c'est la PAGE qui les porte.
             *    Publier « 1000 » sans dire « dixiemes » aurait fabrique un
             *    facteur 10 dans un dossier de mesure. */
            printf("  %9ld  %9ld", (long)mn, (long)mx);
        } else {
            printf("         --         --");
        }
        if (lok) {
            printf("  %9ld  %9ld\n", (long)lm, (long)lx);
        } else {
            printf("         --         --\n");
        }
    }
    printf("  (toutes les valeurs en DIXIEMES — cet instrument ne connait ni\n");
    printf("   les unites ni les echelles hautes, c'est la PAGE qui les porte)\n");
    printf("  🔴 `trous` = positions ECRITES dont la source s'etait tue.\n");
    printf("     `jamais` = positions JAMAIS ATTEINTES depuis l'init — ⛔ ce ne\n");
    printf("     sont PAS des trous, et les compter comme tels a fait publier\n");
    printf("     « trous 110 » a t = 10 s. `min(court)` porte donc sur `ecrits`\n");
    printf("     secondes, ⛔ pas sur « 2 min » par principe.\n");
    printf("\n⛔ UN TROU N'EST PAS UN ZERO. Une valeur absente, perimee, ou\n");
    printf("   SIMULEE (mock, `widget pousser`) n'entre PAS dans une serie\n");
    printf("   presentee comme reelle : elle y creuse un trou, que `lv_chart`\n");
    printf("   SAUTE au trace. C'est la regle W10/AC5 de dn4-1, portee au temps.\n");
    return 0;
}

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
           "flush | reset | sync off|vsync|fbdone | path bitmap|direct | full — "
           "chemin de flush, ET le compteur de GLISSEMENT de trame (dn4-10)",
           cmd_flush),
    DN_CMD("anim", "anim on [ms] | off — stimulus adverse LVGL (témoin de tearing)",
           cmd_anim),
    /* ⚠️ `trace` et `delais` MANQUAIENT ici (revue dn1-4). Le README pose la
     * règle « c'est `aide` qui fait foi, pas cette liste » — et `touch trace`
     * est l'instrument de la preuve d'AC3, documenté au README mais introuvable
     * depuis la carte : il n'apparaissait que dans `touch_usage()`, imprimé
     * seulement par `touch` nu ou par une sous-commande invalide. */
    DN_CMD("touch",
           "touch | reset | mode | axes | trace | int | addr | delais — GT911 "
           "(dn1-4)",
           cmd_touch),
    DN_CMD("nav", "nav | open <n> | back | model | ab <n> — navigation (dn1-4)",
           cmd_nav),
    DN_CMD("recal", "recal <0..4> — recalage DMA N vsyncs après la bascule (AC5)",
           cmd_recal),
    DN_CMD("bl",
           "bl [0..100|on|off|ramp <pct> [ms]|freq <hz>|auto on|off|auto bornes "
           "<bas> <haut>|auto pas <n>|auto plancher <n>] — rétroéclairage "
           "gradable et asservi (dn1-3/dn4-3)",
           cmd_bl),
    DN_CMD("disp", "disp on|off — sortie d'affichage de la dalle (0x29/0x28)",
           cmd_disp),
    DN_CMD("dma", "relance la DMA du panneau (décalage permanent)", cmd_restart_dma),
    DN_CMD("capteurs",
           "capteurs | reset | gaz on|off | simuler <cause> <n> — BME680 "
           "(dn2-1) + la pression, mesuree et publiee par dn4-3",
           cmd_capteurs),
    /* ⚠️ INSCRITE ICI **ET** DANS LE « Jeu complet » DU README dans le MÊME
     * geste — dn2-1 avait oublié `capteurs` au README, et « une commande qu'on
     * ne trouve que depuis la carte n'est pas documentée ». */
    DN_CMD("env",
           "env | reset — BH1750 et VL6180X, les capteurs locaux CADENCES "
           "(dn4-3). INA219 : RETIRE DU BUS le 2026-08-21, `env` dit pourquoi",
           cmd_env),
    DN_CMD("w2",
           "w2 | reset — le critere « une case doit BOUGER » mesure sur les "
           "candidats de la 6e case (dn4-3/AC6)",
           cmd_w2),
    /* ⚠️ INSCRITE ICI **ET** DANS LE « Jeu complet » DU README dans le même
     * geste — dn2-1 avait oublié `capteurs` au README. Les QUATRE sous-commandes
     * ajoutées en dn4-2 (`lire16`, `brut`, `ecrire` + `rafale`) y sont entrées
     * avec cette ligne. ⚠️ CR du 2026-08-24 : ce commentaire disait « les trois
     * primitives » — 4e site du compte périmé « TROIS pour QUATRE ». */
    DN_CMD("i2c",
           "i2c | lire <addr> <reg> [n] | lire16 <addr> <reg16> [n] | brut "
           "<addr> [n] | ecrire <addr> <o1..o8> | rafale <ms> — scan, "
           "transactions et saturation (dn2-1/dn4-2)",
           cmd_i2c),
    /* ⚠️ INSCRITE ICI **ET** DANS LE « Jeu complet » DU README dans le MÊME
     * geste — dn2-1 avait oublié `capteurs` au README, et « une commande qu'on
     * ne trouve que depuis la carte n'est pas documentée ».
     * 🔴 dn4-7 : instrument de QUALIFICATION, ⛔ hors du chemin de régime.
     *    `dn_env` n'est pas touché tant que le balayage d'AC1 n'a pas prouvé la
     *    PROPORTIONNALITÉ. */
    DN_CMD("tof",
           "tof | etat | sr03 | balayage | als <ms> | range [n] — VL6180X : "
           "séquence SR03 (AN4545 Rev 1 §9), rejeu du balayage §13.19.5 et "
           "télémétrie à trois états (dn4-7)",
           cmd_tof),
    DN_CMD("pc",
           "pc | reset | $DN,<trame> — liaison PC : état, compteurs, injection "
           "(dn2-2)",
           cmd_pc),
    DN_CMD("wifi", "wifi [info] | on <ssid> <mdp> | off | ws on|off — branche B "
                   "(dn2-2)",
           cmd_wifi),
    /* ⚠️ INSCRITE ICI **ET** DANS LE README dans le même geste — dn2-1 avait
     * oublié `capteurs` au README, et une commande qu'on ne trouve que depuis
     * la carte n'est pas documentée. */
    DN_CMD("hist",
           "historique de session (dn4-4) : coût RAM, points réels et TROUS par "
           "série",
           cmd_hist),
    /* ⚠️ INSCRITE ICI **ET** DANS LE « Jeu complet » DU README dans le même
     * geste : dn2-1 avait oublié `capteurs` dans le README, et une commande
     * qu'on ne trouve que depuis la carte n'est pas documentée. */
    DN_CMD("widget",
           "widget | groupe on|off|union | opa <n> | voile <n> | mock on|off | demo "
           "on|off [n] | pousser <n> | oublier <n> | rafale | nue <n> on|off | "
           "barre 1hz|minute | bandes on|off | icone <case> <n> | piste "
           "<0xRRGGBB> | voie defaut|avantd12|a|b|c|c2|repli | grandeurs <case> "
           "<n> | dispo empile|cote|mixte | entete normal|compact | val <y> <pas> "
           "| police 14|28 | grille <barre> <menu> | largeur [texte|reset] | "
           "detail | replacer on|off — modèle de case (dn3-1/dn3-2/dn4-1/dn4-6)",
           cmd_widget),
    /* ⚠️ INSCRITE ICI **ET** DANS LE « Jeu complet » DU README dans le même
     * geste — dn2-1 avait oublié `capteurs` au README, et une commande qu'on ne
     * trouve que depuis la carte n'est pas documentée. */
    DN_CMD("rtc",
           "rtc | set <AAAA-MM-JJ> <HH:MM[:SS]> | reset — horloge PCF85063A "
           "(dn3-2)",
           cmd_rtc),
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
    printf("── DeskNode P7 — console de mesure ──\n");
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
    /* Le tactile est LU, pas récité : l'adresse imprimée ici est celle à laquelle
     * le GT911 a répondu au boot. Un bandeau qui annoncerait 0x5D par principe
     * enseignerait un fait qu'on n'a pas mesuré — la leçon du « 5 kHz » de dn1-3. */
    if (dn_touch_ready()) {
        printf("       tactile GT911 @ 0x%02X · lecture « %s » · vue « %s »\n",
               dn_touch_addr(), dn_touch_mode_name(dn_touch_get_mode()),
               dn_ui_vue_name(dn_ui_vue()));
    } else {
        printf("       tactile ABSENT — probe apres reset : %s ⚠️ aucune zone ne "
               "repondra\n",
               esp_err_to_name(dn_touch_probe_apres()));
    }
    if (!dn_ui_active()) {
        printf("       scène brute « %s » (chemin dn1-2)\n", scene_courante());
    }
    /* Le modèle de widget, RELU — pas récité. Le bandeau est l'endroit où le
     * dépôt a déjà menti trois fois (« 5 kHz » pour 24 kHz, « FORCED T/H 8x »
     * sur des registres à 0x00, un checksum d'exemple faux) : chaque chiffre
     * ici vient de la fonction qui détient l'état. */
    /* ⚠️ BOUCLE, pas six appels déroulés à la main (revue 2026-08-18) : le
     *    numérateur était écrit `est_widget(0) + … + est_widget(5)` face à un
     *    dénominateur `DN_UI_METRIQUES`. Porter DN_UI_METRIQUES à 7 ou 8 — ce
     *    que le modèle PROMET — aurait affiché « 3/8 » en ignorant les cases au
     *    delà de 5, sans la moindre erreur de compilation. */
    int n_widgets = 0;
    for (int i = 0; i < DN_UI_METRIQUES; i++) {
        if (dn_ui_est_widget(i)) {
            n_widgets++;
        }
    }
    printf("       widgets : %d/%d cases · invalidation « %s » · opa cases %u, "
           "voile %u\n",
           n_widgets, DN_UI_METRIQUES,
           dn_widget_groupage() ? "groupée" : "fine", dn_widget_opa(),
           dn_ui_voile_opa());
    /* La barre heure/date (dn3-2) — RELUE, comme tout le reste de ce bandeau.
     * ⚠️ On imprime l'ÉTAT DE L'HORLOGE, pas seulement le texte : « --:-- » sans
     *    son motif ne dirait pas si l'horloge est muette, jamais posée, ou si
     *    OS=1. Trois causes, trois conduites à tenir. */
    char bh2[24] = "?", bd2[32] = "?";
    dn_ui_barre_txt(bh2, sizeof(bh2), bd2, sizeof(bd2));
    printf("       barre : « %s  %s » · %s · horloge %s\n",
           bh2, bd2,
           dn_ui_barre_secondes() ? "HH:MM:SS (1 Hz)" : "HH:MM (au chgt de minute)",
           dn_rtc_arme() ? dn_rtc_etat_nom(dn_rtc_etat()) : "NON ARMEE");
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

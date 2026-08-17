#include "dn_console.h"

#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

#include "dn_asset.h"
#include "dn_bootcfg.h"
#include "dn_capteurs.h"
#include "dn_display.h"
#include "dn_link.h"
#include "dn_measure.h"
#include "dn_patterns.h"
#include "dn_pins.h"
#include "dn_recal.h"
#include "dn_stimulus.h"
#include "dn_touch.h"
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
static bool parse_adresse_i2c(const char *texte, uint8_t *out)
{
    char *fin = NULL;
    errno = 0;
    long v = strtol(texte, &fin, 16);
    if (fin == texte || *fin != '\0' || errno == ERANGE) {
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
                printf("  soit %u o de RAM interne, pour %u o disponibles au\n",
                       (unsigned)demande, (unsigned)dispo);
                printf("  prochain boot (libre maintenant + ce que les tampons\n");
                printf("  actuels rendront), marge de sécurité déduite.\n");
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
    if (argc != 1) {
        printf("usage : pc | pc reset | pc $DN,<ver>,<seq>,<t_ms>,cpu,<dixiemes>*<CK>\n");
        return 1;
    }

    dn_link_etat_t etat = dn_link_etat();
    printf("liaison PC : %s", dn_link_etat_nom(etat));
    if (etat != DN_LINK_JAMAIS) {
        int v = dn_link_valeur_dixiemes();
        int64_t age = dn_link_age_us();
        printf(" — derniere valeur %d,%d %% · age %lld ms · seq %u · t_ms agent %u",
               v / 10, v % 10, (long long)(age / 1000),
               (unsigned)dn_link_derniere_seq(), (unsigned)dn_link_dernier_t_ms());
    }
    printf("\n");
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
 * Il fait quatre choses, et AUCUNE n'est un travail long : la console EST le
 * transport PC depuis dn2-2, une commande qui dort couperait la liaison qu'elle
 * prétend observer (c'est le défaut mesuré de `cpu N`).
 *
 *   widget                  l'état des 6 cases : régime, valeurs, forme du mock
 *   widget groupe on|off    A/B d'AC8 — N zones sales fines vs 1 englobante
 *   widget opa <0..255>     A/B d'AC9 — opacité des CASES (reconstruit la scène)
 *   widget voile <0..255>   AC9 — opacité du voile plein écran
 *   widget mock on|off      coupe le mock : la case redevient « -- » (témoin)
 *   widget demo on|off      AC1 — la 7e métrique FICTIVE, sans code de dessin
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

static int cmd_widget(int argc, char **argv)
{
    if (argc == 3 && strcmp(argv[1], "groupe") == 0) {
        bool on;
        if (!parse_on_off(argv[2], &on)) {
            printf("usage : widget groupe on|off\n");
            return 1;
        }
        dn_widget_set_groupage(on);
        printf("invalidation : %s\n",
               on ? "GROUPEE — 1 zone sale par widget (le conteneur, 225x156 = "
                    "35 100 px)"
                  : "FINE — LVGL fait SES zones, une par enfant modifie");
        printf("⚠️ `flush reset` MAINTENANT, puis attendre >= 3 cycles de source\n");
        printf("   avant `flush` : sinon la mesure melange les deux branches.\n");
        return 0;
    }
    if (argc == 3 && strcmp(argv[1], "pousser") == 0) {
        char *fin = NULL;
        long idx = strtol(argv[2], &fin, 0);
        if (!fin || *fin != '\0' || idx < 0 || idx >= DN_UI_METRIQUES) {
            printf("usage : widget pousser <0..%d>\n", DN_UI_METRIQUES - 1);
            return 1;
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
    if (argc == 3 && strcmp(argv[1], "mock") == 0) {
        bool on;
        if (!parse_on_off(argv[2], &on)) {
            printf("usage : widget mock on|off\n");
            return 1;
        }
        dn_ui_mock_set(on);
        printf("mock VENTILOS %s — la case passe en %s\n", on ? "ARME" : "COUPE",
               on ? "SIMULEE" : "ABSENTE (« -- » grise)");
        return 0;
    }
    if (argc == 3 && strcmp(argv[1], "demo") == 0) {
        bool on;
        if (!parse_on_off(argv[2], &on)) {
            printf("usage : widget demo on|off\n");
            return 1;
        }
        if (dn_ui_demo_set(on) != ESP_OK) {
            printf("verrou LVGL non pris — RIEN n'a change\n");
            return 1;
        }
        printf("7e metrique FICTIVE %s.\n", on ? "AFFICHEE" : "retiree");
        if (on) {
            printf("  Elle est produite par le MEME `dn_widget_creer` que les\n");
            printf("  trois autres, depuis un descripteur et RIEN D'AUTRE :\n");
            printf("  aucune ligne de code de dessin n'existe pour elle.\n");
            printf("  Elle est BI-GRANDEURS et n'est ni Ambiance ni Ventilos —\n");
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
        if (!fin || *fin != '\0' || v < 0 || v > 255) {
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
        printf("usage : widget | groupe on|off | opa <0..255> | voile <0..255>\n");
        printf("        | mock on|off | demo on|off | pousser <idx>\n");
        return 1;
    }

    printf("modele de widget (dn3-1) — 3 cases sur 6 le portent\n");
    printf("invalidation : %s\n",
           dn_widget_groupage() ? "GROUPEE (1 zone englobante par widget)"
                                : "FINE (N zones, LVGL decide)");
    printf("opacite      : cases %u/255 · voile %u/255\n", dn_widget_opa(),
           dn_ui_voile_opa());
    printf("demo 7e metrique : %s\n", dn_ui_demo_on() ? "AFFICHEE" : "retiree");

    int mn = 0, mx = 0, per = 0;
    dn_ui_mock_forme(&mn, &mx, &per);
    printf("mock VENTILOS : %s · rampe TRIANGULAIRE %d -> %d tr/min · periode "
           "%d s · pas 1 s\n",
           dn_ui_mock_on() ? "ARME" : "COUPE", mn, mx, per);
    printf("   (forme RELUE des constantes qui le pilotent. La valeur VARIE :\n");
    printf("    un mock fige serait indiscernable d'un affichage bloque.)\n");

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
        printf("%-7s %-8s %-9s", d ? "WIDGET" : "nue",
               dn_val_regime_nom(dn_ui_regime(i)),
               dn_ui_case_dessinee(i) ? "oui" : "NON");
        int n = d ? d->n_grandeurs : 1;
        for (int g = 0; g < n; g++) {
            const char *t = dn_ui_valeur_txt(i, g);
            const char *u = (d && d->grandeurs[g].unite) ? d->grandeurs[g].unite
                                                         : "";
            printf(" %s%s%s", (t && t[0]) ? t : "--", (t && t[0]) ? " " : "",
                   (t && t[0]) ? u : "");
        }
        printf("\n");
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
    printf("   (modele REBUILD en vue detail). L'etat est CONSERVE et sera pose\n");
    printf("   a la prochaine construction — mais rien n'atteint la dalle.\n");
    printf("\nGPU/RAM/RESEAU sont NUES : elles n'ont pas le modele, et c'est le\n");
    printf("TEMOIN NEGATIF d'AC8 — la seule facon de chiffrer une case-widget\n");
    printf("contre une case nue sous le meme fps/bounce/draw buffer. Leur\n");
    printf("regime est ABSENTE : aucune source ne les alimente, elles le DISENT.\n");
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
/* Un bus sain en porte 4 ; 16 laisse la place aux 4 capteurs de dn4-1 et à leurs
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
 * plus rien. C'est exactement le defaut de `cpu N` trouve en validation dn2-2,
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
    case 0x51:
        return "PCF85063 — RTC (pas encore pilotee, dn3-2)";
    case 0x6A:
    case 0x6B:
        return "QMI8658 — IMU (hors V1)";
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
    case 0x23:
        return "BH1750 — luminosite (dn4-1)";
    case 0x29:
        return "VL53L0X — distance (dn4-1)";
    case 0x40:
        return "INA219 — tension/courant (dn4-1)";
    default:
        return "INCONNU — a identifier avant d'en tirer quoi que ce soit";
    }
}

/* Lecture registre : ajoute un device TEMPORAIRE, lit, le retire.
 * ⚠️ PREMIER `i2c_master_bus_add_device()` DU DÉPÔT — le TCA9554 et le GT911
 *    passent tous deux par leur composant, qui le fait en interne. Le device est
 *    retiré sur TOUS les chemins de sortie : en laisser fuir un à chaque appel
 *    épuiserait la table du bus, et l'échec arriverait bien plus tard, ailleurs,
 *    sans rapport visible avec cette commande. */
static int i2c_lire_registre(uint8_t addr, uint8_t reg, int n)
{
    i2c_master_bus_handle_t bus = dn_display_i2c_bus();
    if (!bus) {
        printf("bus I2C absent — dn_display_init() n'a pas tourne\n");
        return 1;
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
         * autres devices, pas un defaut de composant tiers. */
        .scl_speed_hz = DN_I2C_FREQ_HZ,
    };
    i2c_master_dev_handle_t dev = NULL;
    esp_err_t err = i2c_master_bus_add_device(bus, &cfg, &dev);
    if (err != ESP_OK) {
        printf("ajout du device 0x%02X refuse : %s\n", addr, esp_err_to_name(err));
        return 1;
    }
    uint8_t rx[16] = {0};
    err = i2c_master_transmit_receive(dev, &reg, 1, rx, (size_t)n, 200);
    i2c_master_bus_rm_device(dev);
    if (err != ESP_OK) {
        printf("lecture 0x%02X reg 0x%02X : ECHEC (%s)\n", addr, reg,
               esp_err_to_name(err));
        printf("  un NACK ici veut dire que le composant ne repond PLUS, meme si\n");
        printf("  le scan l'a vu — contact intermittent, ou adresse partagee.\n");
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
    if (reg == 0xD0 && n >= 1) {
        const char *quoi = rx[0] == 0x61   ? "BME680 ou BME688 (0xF0 tranche)"
                           : rx[0] == 0x60 ? "BME280 — PAS de gaz"
                           : rx[0] == 0x58 ? "BMP280 — NI gaz NI humidite"
                                           : "INCONNU — ce n'est pas un BME/BMP";
        printf("  => chip id 0x%02X = %s\n", rx[0], quoi);
    }
    if (reg == 0xF0 && n >= 1) {
        printf("  => variant 0x%02X = %s\n", rx[0],
               rx[0] == 0x00   ? "BME680"
               : rx[0] == 0x01 ? "BME688"
                               : "INCONNU");
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
        char *fin = NULL;
        errno = 0;
        long r = strtol(argv[3], &fin, 16);
        if (fin == argv[3] || *fin != '\0' || errno == ERANGE || r < 0 || r > 0xFF) {
            printf("registre « %s » refuse : hexa, entre 00 et FF\n", argv[3]);
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
    if (argc != 1) {
        printf("usage : i2c | i2c lire <addr> <registre> [n]\n");
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
    uint8_t cid = dn_capt_chip_id();
    printf("identite   : chip id 0x%02X · variant 0x%02X => %s\n", cid,
           dn_capt_variant(),
           cid != DN_BME680_CHIP_ID ? "PAS un BME680 — le cablage n'est pas en cause"
           : dn_capt_variant() == DN_BME680_VARIANT_688 ? "BME688"
                                                        : "BME680");
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
    DN_CMD("bl", "bl [0..100|on|off|ramp <pct> [ms]] — rétroéclairage gradable",
           cmd_bl),
    DN_CMD("disp", "disp on|off — sortie d'affichage de la dalle (0x29/0x28)",
           cmd_disp),
    DN_CMD("dma", "relance la DMA du panneau (décalage permanent)", cmd_restart_dma),
    DN_CMD("capteurs",
           "capteurs | reset | gaz on|off | simuler <cause> <n> — BME680 (dn2-1)",
           cmd_capteurs),
    DN_CMD("i2c",
           "i2c | lire <addr> <registre> [n] — scan du bus et lecture registre "
           "(dn2-1)",
           cmd_i2c),
    DN_CMD("pc",
           "pc | reset | $DN,<trame> — liaison PC : état, compteurs, injection "
           "(dn2-2)",
           cmd_pc),
    DN_CMD("wifi", "wifi [info] | on <ssid> <mdp> | off | ws on|off — branche B "
                   "(dn2-2)",
           cmd_wifi),
    /* ⚠️ INSCRITE ICI **ET** DANS LE « Jeu complet » DU README dans le même
     * geste : dn2-1 avait oublié `capteurs` dans le README, et une commande
     * qu'on ne trouve que depuis la carte n'est pas documentée. */
    DN_CMD("widget",
           "widget | groupe on|off | opa <n> | voile <n> | mock on|off | demo "
           "on|off | pousser <n> — modèle de case (dn3-1)",
           cmd_widget),
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
    printf("── DeskNode P6 — console de mesure ──\n");
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
    printf("       widgets : %d/%d cases · invalidation « %s » · opa cases %u, "
           "voile %u\n",
           (dn_ui_est_widget(0) ? 1 : 0) + (dn_ui_est_widget(1) ? 1 : 0) +
               (dn_ui_est_widget(2) ? 1 : 0) + (dn_ui_est_widget(3) ? 1 : 0) +
               (dn_ui_est_widget(4) ? 1 : 0) + (dn_ui_est_widget(5) ? 1 : 0),
           DN_UI_METRIQUES,
           dn_widget_groupage() ? "groupée" : "fine", dn_widget_opa(),
           dn_ui_voile_opa());
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

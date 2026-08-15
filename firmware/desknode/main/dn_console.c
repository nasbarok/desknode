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
#include "dn_stimulus.h"
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
    char etiquette[64];
    snprintf(etiquette, sizeof(etiquette), "num_fbs=%d bounce=%u scene=%s",
             dn_display_num_fbs(), (unsigned)dn_display_bounce_px(),
             scene_courante());
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
    printf("config de boot (NVS) : num_fbs=%d bounce_px=%d\n", cfg.num_fbs,
           cfg.bounce_px);
    printf("config ACTIVE        : num_fbs=%d bounce_px=%u\n",
           dn_display_num_fbs(), (unsigned)dn_display_bounce_px());
    printf("⚠️ un `set` ne prend effet qu'au `reboot` : les framebuffers sont\n");
    printf("   alloués une fois, au démarrage. C'est voulu — réallouer à chaud\n");
    printf("   laisserait une PSRAM fragmentée et fausserait la mesure suivante.\n");
    printf("`cfg reset` efface la config NVS et rend les défauts au prochain boot.\n");
    return 0;
}

static int cmd_set(int argc, char **argv)
{
    if (argc < 3) {
        printf("usage : set fbs <1|2|3> | set bounce <px>\n");
        return 1;
    }
    bool cle_fbs = (strcmp(argv[1], "fbs") == 0);
    bool cle_bounce = (strcmp(argv[1], "bounce") == 0);
    if (!cle_fbs && !cle_bounce) {
        /* La clé est vérifiée AVANT la valeur : sinon `set foo bar` reprocherait
         * « bar » à l'opérateur alors que la faute est sur « foo ». */
        printf("clé inconnue : %s\n", argv[1]);
        printf("usage : set fbs <1|2|3> | set bounce <px>\n");
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

static int cmd_bl(int argc, char **argv)
{
    if (argc < 2) {
        printf("rétroéclairage : %s\n", dn_display_backlight_state() ? "ON" : "OFF");
        return 0;
    }
    bool on = false;
    if (!parse_on_off(argv[1], &on)) {
        printf("usage : bl [on|off] — « %s » n'est ni l'un ni l'autre.\n", argv[1]);
        printf("   (rien n'a été touché : l'ancien code aurait éteint l'écran.)\n");
        return 1;
    }
    /* Le retour de dn_display_backlight() était JETÉ : un échec de GPIO se
     * serait annoncé « rétroéclairage ON » avec un écran resté noir. */
    esp_err_t err = dn_display_backlight(on);
    printf("rétroéclairage %s : %s\n", on ? "ON" : "OFF", esp_err_to_name(err));
    return (err == ESP_OK) ? 0 : 1;
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
    DN_CMD("set", "set fbs <1|2|3> | set bounce <px>", cmd_set),
    DN_CMD("reboot", "redémarre pour appliquer un `set`", cmd_reboot),
    DN_CMD("tear", "tear on|vsync|sync|both|flip|off — déchirement (AC5)", cmd_tear),
    DN_CMD("flash", "flash on|off — stimulus d'écriture flash (AC6)", cmd_flash),
    DN_CMD("bl", "bl on|off — rétroéclairage", cmd_bl),
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
    printf("── DeskNode P1 — console de mesure ──\n");
    for (size_t i = 0; i < sizeof(k_cmds) / sizeof(k_cmds[0]); i++) {
        printf("  %-7s %s\n", k_cmds[i].command, k_cmds[i].help);
    }
    printf("\n");
    printf("état : num_fbs=%d bounce=%u px, rétroéclairage %s, scène « %s »\n",
           dn_display_num_fbs(), (unsigned)dn_display_bounce_px(),
           dn_display_backlight_state() ? "ON" : "OFF", scene_courante());
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

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
 * ══ dn4-23 / AC2.1 — LA CONSOLE COMPTE CE QU'ELLE EMET ══════════════════════
 *
 * 🔴 LE DEFAUT, MESURE, ⛔ PAS SUPPOSE. `tools/dn_console.py` PERD DES LIGNES :
 *    **6 captures sur 20 en lot** violaient l'invariant `N == X + Y` du scan
 *    I2C — dont une ou le temoin positif `0x5D` etait ABSENT de la liste sous
 *    un verdict « ✅ temoin positif OK » que le firmware ne peut imprimer QUE
 *    s'il l'a vu. Et **1 sur 7 en invocation SOLO** : la parade « solo +
 *    invariant » de `dn4-2` est donc INSUFFISANTE.
 *    ⇒ Une ligne perdue produit « l'adresse 0x23 n'est pas la » sur un capteur
 *      QUI REPOND, juste avant qu'on decide de dessouder.
 *
 * ⛔ CE COMPTEUR NE SUPPRIME PAS LA PERTE — IL LA REND VISIBLE. La cause reste
 *    NON INSTRUITE : **2 A/B et 30 passes de controle** (15 avec `--capture`,
 *    15 sans) n'ont RIEN reproduit, et les deux mecanismes candidats
 *    (`ser.reset_input_buffer()` avant l'ecriture · `nettoyer()` qui coupe
 *    « jusqu'a la premiere ligne qui se termine par la commande ») sont
 *    toujours en place, DELIBEREMENT : le premier garantit que la sortie rendue
 *    appartient a LA commande envoyee. ⛔ Ne pas inventer un mecanisme pour
 *    clore l'entree.
 *
 * ⚠️ POURQUOI UN COMPTEUR ET PAS UNE SOMME DE CONTROLE : le scan I2C avait deja
 *    son invariant arithmetique PAR CAPTURE (`N == stables + instables`), et
 *    c'est LUI qui a attrape les six. On generalise la meme forme a TOUTE
 *    commande — un invariant qu'un tampon ampute ne peut pas satisfaire.
 *
 * ⚠️ CE QUE LE COMPTEUR NE COMPTE PAS, ET C'EST VOULU : les logs ASYNCHRONES des
 *    autres taches (`ESP_LOGx`, qui ne passe pas par `printf`). L'hote en
 *    recevra donc parfois PLUS que le compte annonce — c'est le signe de lignes
 *    ETRANGERES, ⛔ pas d'une perte. Les deux sens se distinguent chez l'hote,
 *    et seul « recu < annonce » est une PERTE.
 *
 * 🎯 LE COMPTAGE EST POSE PAR UNE MACRO `printf`, ⛔ pas commande par commande :
 *    une instrumentation a poser sur 32 branches serait oubliee sur la 33e —
 *    c'est la these de `dn4-16`, et ce depot l'a payee. Ici, TOUT `printf` de ce
 *    fichier compte, y compris ceux des fonctions auxiliaires.
 */
#include <stdarg.h>
#include <stdio.h>

static uint32_t s_lignes_cmd;        /* lignes emises depuis le debut de la commande */
static bool s_fin_de_ligne = true;   /* la derniere sortie finissait-elle par '\n' ? */
static bool s_compte_fiable = true;  /* ⛔ une sortie tronquee rend le compte FAUX */

/* ⚠️ Le format est verifie par le compilateur (`format(printf, 1, 2)`) : sans
 *    ca, la macro ci-dessous DESARMERAIT `-Wformat` sur les ~1 000 sites de ce
 *    fichier — un correctif d'instrument qui aveugle un autre instrument. */
static int dn_console_printf(const char *fmt, ...) __attribute__((format(printf, 1, 2)));

static int dn_console_printf(const char *fmt, ...)
{
    char pile[256];
    va_list ap;
    va_start(ap, fmt);
    int n = vsnprintf(pile, sizeof(pile), fmt, ap);
    va_end(ap);
    if (n < 0) {
        /* ⛔ On ne tait pas un echec de formatage : le compte devient faux. */
        s_compte_fiable = false;
        return n;
    }
    const char *txt = pile;
    char *tas = NULL;
    if ((size_t)n >= sizeof(pile)) {
        tas = malloc((size_t)n + 1);
        if (tas) {
            va_start(ap, fmt);
            vsnprintf(tas, (size_t)n + 1, fmt, ap);
            va_end(ap);
            txt = tas;
        } else {
            /* ⛔ Mieux vaut une ligne TRONQUEE qu'un silence — mais le compte
             *    ne vaut plus rien et il le DIT. */
            s_compte_fiable = false;
            n = (int)strlen(pile);
        }
    }
    for (const char *q = txt; *q; q++) {
        if (*q == '\n') {
            s_lignes_cmd++;
        }
    }
    if (n > 0) {
        s_fin_de_ligne = (txt[n - 1] == '\n');
    }
    fputs(txt, stdout);
    free(tas);
    return n;
}

/* ⛔ APRES la definition : sinon `dn_console_printf` s'appellerait lui-meme. */
#define printf dn_console_printf

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

/*
 * ══ dn4-14-2 / AC2.1 — LES POLICES, RELUES DU REGISTRE DE `dn_widget` ═══════
 *
 * 🔴 LA TABLE N'EST **PAS** ICI, ET C'EST LE POINT. Elle vit dans `dn_widget.c`,
 *    développée depuis `DN_FONT_LISTE` (que `gen_font_dn.py` construit depuis
 *    `TAILLES`), parce que `dn_ui_geom_valider()` en a besoin AUSSI pour
 *    refuser une police de veille sur le titre. Deux tables auraient divergé —
 *    `dn_font.h` a recopié un choix d'icône et a menti TROIS fois.
 * ⚠️ `widget police` en est la preuve vivante : il annonce « IL N'Y A QUE DEUX
 *    POLICES EMBARQUEES » dans un `printf`, une phrase que rien ne re-vérifiait.
 */
static void polices_imprimer(void)
{
    printf("polices LIEES (%d) — RELUES du registre, ⛔ pas d'un printf :\n",
           dn_widget_polices_nb());
    for (int i = 0; i < dn_widget_polices_nb(); i++) {
        const char *nom = NULL;
        const lv_font_t *f = NULL;
        bool itf = false;
        if (!dn_widget_police_at(i, &nom, &f, &itf)) {
            continue;
        }
        printf("  %-4s line_height %2d  %s\n", nom,
               (int)lv_font_get_line_height(f),
               itf ? "INTERFACE (latin-1 complet)"
                   : "VEILLE — ⛔ ni accent ni symbole, texte d'interface MUET");
    }
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

/*
 * 🔴 UNE VALEUR NON RELUE NE S'IMPRIME PAS COMME UNE MESURE — 3e revue du
 *    2026-08-27. `demande_px`/`retenu_px` valaient 0 quand la cle NVS n'avait
 *    pas pu etre lue, et 0 est un `bounce_px` LEGAL : « la NVS demandait 0 px »
 *    etait indiscernable d'un vrai repli de `bounce 0`. On imprime desormais ce
 *    qu'on sait, ⛔ pas un nombre par defaut.
 */
static void imprimer_px_repli(const char *etiquette, int px)
{
    if (px == DN_REPLI_NON_RELU) {
        printf("   %s : ⛔ VALEUR NON RELUE (la clé NVS n'a pas répondu)\n",
               etiquette);
    } else {
        printf("   %s : %d px\n", etiquette, px);
    }
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
        /*
         * 🔴 CORRIGE LE 2026-08-27 (3e revue) — CETTE COMMANDE AFFIRMAIT LE
         *    CONTRAIRE DE CE QUE LE FIRMWARE VENAIT DE JOURNALISER. Elle
         *    imprimait « le TÉMOIN DE REPLI, lui, est CONSERVÉ » de maniere
         *    INCONDITIONNELLE des que l'effacement rendait ESP_OK — y compris
         *    (a) quand la repose du temoin avait echoue, une ligne apres un
         *    `ESP_LOGE` disant « le TEMOIN DE REPLI a ete PERDU », et (b) quand
         *    il n'y avait AUCUN temoin a conserver, sur une carte vierge.
         *    ⛔ C'est mot pour mot la classe du constat #948 (`recal` affirmait
         *    « jamais d'armement » deux lignes sous « recalages joués : 1 »),
         *    que la seance du 2026-08-27 declarait soldee.
         * ⇒ On ne dit plus que ce que `dn_bootcfg_reset_ex()` a MESURE.
         */
        esp_err_t repose = DN_REPOSE_SANS_OBJET;
        esp_err_t err = dn_bootcfg_reset_ex(&repose);
        if (err != ESP_OK) {
            printf("effacement refusé : %s\n", esp_err_to_name(err));
            return 1;
        }
        printf("config NVS effacée. `reboot` pour repartir sur les défauts.\n");
        if (repose == DN_REPOSE_SANS_OBJET) {
            printf("⚠️ aucun TÉMOIN DE REPLI n'était en NVS : il n'y avait rien "
                   "à conserver.\n");
            printf("   ⛔ Ça ne veut PAS dire qu'il n'y a jamais eu de repli — "
                   "voir `cfg repli`.\n");
        } else if (repose == ESP_OK) {
            printf("✅ le TÉMOIN DE REPLI a été RELU, effacé et REPOSÉ — "
                   "délibérément :\n");
            printf("   `cfg reset` est précisément ce qu'on tape pour sortir "
                   "d'une valeur fautive.\n");
            printf("   `cfg repli clear` l'efface. ⚠️ C'est le seul geste "
                   "d'OPÉRATEUR qui l'efface :\n");
            printf("   un `nvs_flash_erase()` au boot (NVS corrompue ou "
                   "nouvelle version) l'emporte aussi.\n");
        } else {
            printf("🔴 le TÉMOIN DE REPLI est PERDU (%s) — la seule trace est "
                   "la ligne de log\n", esp_err_to_name(repose));
            printf("   émise juste au-dessus. ⛔ La NVS n'en garde AUCUN "
                   "reliquat : rien à relire.\n");
        }
        return 0;
    }
    /*
     * 🔴 `cfg repli` — LE TÉMOIN DE REPLI, décision owner du 2026-08-27.
     *    Le filet de boot DÉTRUIT le réglage de l'opérateur quand la valeur ne
     *    s'alloue pas. C'est voulu. ⛔ Mais jusqu'ici il le détruisait EN
     *    SILENCE : la seule trace était une ligne de log qui défile, et il
     *    n'existait AUCUNE clé interrogeable après coup.
     */
    if (argc >= 2 && strcmp(argv[1], "repli") == 0) {
        if (argc >= 3 && strcmp(argv[2], "clear") == 0) {
            esp_err_t err = dn_bootcfg_clear_repli();
            if (err != ESP_OK) {
                printf("effacement du témoin refusé : %s\n",
                       esp_err_to_name(err));
                return 1;
            }
            printf("témoin de repli EFFACÉ.\n");
            return 0;
        }
        dn_bootcfg_repli_t t;
        /* 🔴 3e revue du 2026-08-27 : « aucun repli » ETAIT UNE AFFIRMATION NON
         *    ETABLIE. `dn_bootcfg_get_repli()` rendait `void` : quand la NVS ne
         *    s'ouvrait pas, on sortait avec `present == false` et on l'imprimait
         *    comme un fait. ⛔ Un instrument qui ne peut pas echouer ne mesure
         *    rien — c'est la leçon du témoin `widget rafale` (2026-08-19). */
        esp_err_t err_lu = dn_bootcfg_get_repli(&t);
        if (err_lu != ESP_OK) {
            printf("⛔ TÉMOIN DE REPLI ILLISIBLE : %s\n",
                   esp_err_to_name(err_lu));
            printf("   ⚠️ Ce n'est PAS « aucun repli » — c'est « je n'ai pas pu "
                   "lire ». La question\n");
            printf("   reste OUVERTE, et aucun chiffre n'est publié ici.\n");
            return 1;
        }
        if (!t.present) {
            printf("aucun repli de bounce noté depuis le dernier effacement.\n");
            printf("   (clé NVS LUE, et elle répond « rien » — ⛔ pas « je ne "
                   "sais pas ».)\n");
            printf("⛔ Ça ne veut PAS dire qu'il n'y en a jamais eu : le témoin "
                   "date du 2026-08-27,\n");
            printf("   les replis d'avant n'ont laissé qu'une ligne de log.\n");
            return 0;
        }
        printf("🔴 REPLI DE BOUNCE SURVENU — %d fois depuis le dernier "
               "effacement\n", t.occurrences);
        imprimer_px_repli("la NVS demandait  ", t.demande_px);
        if (t.demande_px != DN_REPLI_NON_RELU) {
            printf("      ⛔ CETTE VALEUR EST PERDUE\n");
        }
        imprimer_px_repli("le filet a retenu ", t.retenu_px);
        if (t.occurrences > 1) {
            printf("   ⚠️ %d replis, mais UNE SEULE paire de valeurs est "
                   "gardée : c'est la DERNIÈRE.\n", t.occurrences);
            printf("      ⛔ Ne PAS lire « les %d replis demandaient cette "
                   "valeur-là ».\n", t.occurrences);
        }
        if (t.retenu_px == DN_BOUNCE_PX_PLANCHER) {
            printf("   🔴 C'EST LE PLANCHER, et il a un DÉFAUT VISIBLE CONNU : "
                   "à %d px\n", DN_BOUNCE_PX_PLANCHER);
            printf("      l'image GLISSE sous trafic série + repeint (§18.9). "
                   "⛔ Ne pas laisser\n");
            printf("      le produit ici — `set bounce %d` puis `reboot`.\n",
                   dn_bootcfg_defaut_bounce_px());
        }
        printf("⚠️ Le témoin SURVIT à `cfg reset`. `cfg repli clear` pour "
               "l'effacer,\n");
        printf("   et c'est un geste EXPLICITE : personne ne l'efface par "
               "effet de bord.\n");
        return 0;
    }
    if (argc >= 2) {
        printf("usage : cfg | cfg reset | cfg repli [clear]\n");
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
    /* 🔴 LE TÉMOIN SORT ICI, DANS `cfg` NU — ⛔ pas seulement dans un
     *    sous-verbe qu'il faut connaître. Un témoin qu'il faut savoir demander
     *    ne prévient personne : c'est exactement le silence qu'il ferme. */
    {
        dn_bootcfg_repli_t t;
        esp_err_t err_lu = dn_bootcfg_get_repli(&t);
        if (err_lu != ESP_OK) {
            /* ⛔ LE SILENCE N'EST PLUS UNE OPTION : se taire ici se lirait
             *    « aucun repli », et c'est justement ce qu'on ne sait pas. */
            printf("\n⛔ TÉMOIN DE REPLI ILLISIBLE (%s) — ⚠️ ce n'est PAS "
                   "« aucun repli ».\n", esp_err_to_name(err_lu));
        } else if (t.present) {
            printf("\n🔴 UN REPLI DE BOUNCE A EU LIEU (%d fois).\n",
                   t.occurrences);
            imprimer_px_repli("la NVS demandait  ", t.demande_px);
            imprimer_px_repli("le filet a retenu ", t.retenu_px);
            printf("   ⛔ La valeur demandée est PERDUE. `cfg repli` pour le "
                   "détail, `cfg repli clear` pour effacer le témoin.\n");
        }
    }
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
    /* 🟢 dn4-20/AC9.3 — ~~`<1..100>`~~ ⇒ **`<%d..100>`**, LU DANS LA CONSTANTE.
     *   Entree de differe soldee : `dn_env_bl_pas_set()` REFUSE `pas < HYST`
     *   (verrou mortel : sous la bande morte la loi se fige a mi-chemin), et
     *   cette ligne d'aide annoncait `1` depuis. La branche `bl auto pas`
     *   vingt lignes plus bas imprimait DEJA la bonne borne : deux etiquettes
     *   pour un seul setter, et c'est la plus visible qui mentait. */
    printf("        bl auto pas <%d..100>  — pas maximal par cycle de 5 s\n",
           DN_ENV_BL_HYST);
    printf("        bl auto plancher <n>  — le %% en piece SOMBRE (constat oeil)\n");
    printf("        bl auto plafond <n>   — le %% en PLEINE LUMIERE (dn4-20/AC4.6)\n");
    printf("        bl auto ambiant <0..100>        — %% de la loi applique en AMBIENT (dn4-19)\n");
    printf("        bl auto ambiant plancher <n>    — le plancher du RENDU D'AMBIENT (dn4-19)\n");
    printf("        bl auto courbe log|lineaire     — la FORME de la loi (dn4-19/AC6.3)\n");
    /* ⚠️ `bl loi` est en DERNIER, et separee : ce n'est pas un `bl auto …`, c'est
     * une LECTURE. La ranger au milieu des reglages (revue du 2026-08-27) cassait
     * le regroupement et laissait croire qu'elle pose quelque chose. */
    printf("        bl loi [lux]        — ce que la loi RENDRAIT, ⛔ SANS rien appliquer NI desarmer\n");
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
    printf("  loi      : %d %% à <= %d lx · %d %% à >= %d lx · courbe %s entre "
           "les deux\n",
           /* 🔴 dn4-20/AC4.7 — LE PLAFOND COURANT, ⛔ PLUS LE MACRO. `bl` est
            *   la sortie qui sert d'INSTRUMENT a toute la seance d'A/B :
            *   publier 100 pendant que la loi sature a 80 aurait fausse
            *   chaque lecture de la seance qu'elle sert a conduire. */
           dn_env_bl_plancher(), lux_bas, dn_env_bl_plafond(), lux_haut,
           dn_env_bl_courbe_nom(dn_env_bl_courbe()));
    if (dn_env_bl_courbe() == DN_ENV_BL_COURBE_LOG) {
        printf("           (dn4-19/AC6.3 : l'œil ET le lux sont logarithmiques. "
               "Constat owner du 2026-08-27, A/B en ACTIF à 245 lx : « 75 %% — "
               "nettement plus », là où la loi LINÉAIRE rendait 44 %%. "
               "⛔ Les deux bornes n'ont PAS bougé. `bl auto courbe lineaire` "
               "pour revenir à la loi de dn4-3 et refaire l'A/B.)\n");
    }
    printf("  garde    : bande morte %d pts · pas max %d pts par cycle de %d ms "
           "(course complète en %d cycles)\n",
           hyst, pas, DN_ENV_PERIODE_MS,
           /* meme motif : la course annoncee doit etre celle que la loi
            * PARCOURT REELLEMENT (dn4-20/AC4.7). */
           (dn_env_bl_plafond() - dn_env_bl_plancher() + pas - 1) / pas);
    /* 🔴 « jamais lu » et « noir complet » ne s'impriment PLUS à l'identique —
     * corrigé en revue de code le 2026-08-20. `0 lx` est une valeur MESURÉE
     * légitime sur ce capteur (la main posée a rendu `brut = 0` deux fois en
     * séance, et c'est publié comme tel) : rendre la sentinelle d'absence par
     * un `0` littéral affirmait l'obscurité totale là où rien n'avait été lu. */
    if (dpct < 0) {
        /* 🔴 CORRIGÉ EN REVUE DE CODE LE 2026-08-27 — cette ligne disait
         * « depuis le BOOT » et se retrouvait, **six lignes plus bas et dans la
         * même sortie**, à côté de `applications : 15 mouvements de duty depuis
         * le boot`. Capturé sur la carte (`mesures/dn4-19/T4-temoins.txt`).
         * ⇒ Les DEUX chiffres étaient justes, sous **deux définitions
         * différentes** : `dn_env_bl_auto_set(true)` remet la sentinelle
         * d'affichage à `-1` (voulu — cf. `dn_env.c`) mais **pas** le compteur.
         * ⛔ On ne « répare » donc AUCUN des deux : **on dit lequel est lequel.** */
        printf("  applique : AUCUNE application depuis LE DERNIER ARMEMENT "
               "(`bl auto on` remet ce temoin a zero — ⛔ pas le compteur "
               "`applications` ci-dessous, qui lui compte depuis le BOOT)\n");
    } else if (dlux == DN_ENV_ABSENT) {
        printf("  applique : %d %% (sur un lux JAMAIS LU — ⛔ pas « 0 lx »)\n",
               dpct);
    } else {
        printf("  applique : %d %% (sur %d lx)\n", dpct, dlux);
    }
    /* 🔴 dn4-19 — LE RÉGIME EST LA MOITIÉ DE L'ÉTAT. Sans lui, `applique : N %%`
     * ne dit pas SUR QUOI la loi asservit, et c'est exactement l'aveuglement qui
     * a laissé « l'asservissement n'a jamais tourné » invisible pendant des
     * semaines : la sortie était juste, elle ne disait simplement pas assez. */
    bool amb = (dn_env_bl_regime() == DN_ENV_BL_REGIME_AMBIENT);
    printf("  régime   : %s%s\n", amb ? "AMBIENT" : "ACTIF",
           amb ? "  (la loi est mise à l'échelle, voir ci-dessous)" : "");
    printf("  ambiant  : échelle %d %% de la loi · plancher %d %%\n",
           dn_env_bl_amb_echelle(), dn_env_bl_amb_plancher());
    /* 🔴 CORRIGÉ EN REVUE DE CODE LE 2026-08-27 — cette ligne annonçait
     * « ⛔ JAMAIS mesuré à l'œil » **à côté de `plancher 16 %`**, alors que le 16
     * VIENT d'un balayage à l'œil du même jour. Le docblock de `dn_env.h` avait
     * été corrigé, ⛔ pas cette chaîne — **troisième étiquette qui ment née du
     * correctif**, et capturée telle quelle sur le binaire livré
     * (`mesures/dn4-19/T9-final.txt`, `T11-etat-final.txt`).
     * ⛔ *« Une étiquette qui ment se relit à chaque boot »* — celle-ci se
     * relisait à chaque `bl`, et la séance suivante aurait re-mesuré. */
    printf("           ⚠️ ce plancher est un TROISIÈME contenu (gros chiffres sur "
           "noir), MESURÉ À L'ŒIL le 2026-08-27 dans le noir (« 8 %% c'est trop "
           "bas, 16 c'est bien ») : ⛔ ne pas le confondre avec les %d %% du "
           "dashboard ni avec les %d %% du Living PCB — trois CONTENUS, trois "
           "chiffres.\n",
           DN_ENV_BL_PCT_MIN, DN_VEILLE_PCT_MIN);
    printf("  applications : %u mouvements de duty depuis le BOOT "
           "(⛔ jamais remis, meme par `bl auto on`)\n",
           (unsigned)dn_env_bl_applications());
    printf("           (dn4-19/AC8 : deux relevés espacés mesurent le POMPAGE de "
           "la bande morte — la loi vit H24 depuis que l'auto est armée par "
           "défaut.)\n");
    printf("  ⚠️ `bl <n>`, `bl on|off` et `bl ramp` DÉSARMENT l'auto et le "
           "DISENT.\n");
    printf("  ⛔ `bl ramp` est BLOQUANTE : elle n'est JAMAIS appelée par "
           "l'asservissement.\n");
    printf("  ⛔ La VEILLE ne désarme PLUS (dn4-19) : elle POSE le niveau du "
           "régime EN UNE FOIS, et la loi le maintient ensuite.\n");
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
            /* 🔴 AJOUTÉ EN REVUE DE CODE LE 2026-08-27 — `bl auto ambiant` et
             * `bl auto courbe` rafraîchissaient la dalle, ⛔ pas ceux-ci : deux
             * leviers voisins, deux latences (0 s contre 5 s), **sans que rien
             * ne le dise**. Or `s_bl_lux_bas`/`_haut` entrent dans la loi, donc
             * dans le régime Ambient aussi. ⇒ même service sur tous les leviers. */
            dn_ui_veille_bl_rafraichir();
            bl_auto_etat();
            return 0;
        }
        if (strcmp(argv[2], "plancher") == 0) {
            long pct = 0;
            if (argc != 4 || !parse_entier(argv[3], &pct)) {
                printf("usage : bl auto plancher <0..%d>\n",
                       dn_env_bl_plafond() - DN_ENV_BL_HYST);
                return 1;
            }
            if (dn_env_bl_plancher_set((int)pct) != ESP_OK) {
                printf("refusé : le plancher doit être dans [0, %d] — au-delà, "
                       "la bande morte rendrait la loi INERTE sans le dire, ce "
                       "qui est pire qu'un refus. Rien n'a été touché.\n",
                       dn_env_bl_plafond() - DN_ENV_BL_HYST);
                return 1;
            }
            /* 🔴 AJOUTÉ EN REVUE DE CODE LE 2026-08-27 — voir `bornes` ci-dessus :
             * `s_bl_pct_min` entre dans `dn_env_bl_loi()`, donc dans le régime
             * Ambient aussi. La dichotomie du plancher se conduisait à l'aveugle
             * pendant 5 s alors que celle du plancher d'Ambient répondait au doigt. */
            dn_ui_veille_bl_rafraichir();
            bl_auto_etat();
            return 0;
        }
        /* ── bl auto plafond <n> ── 🔴 `dn4-20`/AC4.6 ─────────────────────────
         * LE PENDANT HAUT DE `plancher`, ET IL MANQUAIT. Le candidat « PLATEAU »
         * d'AC4.1 EST un deplacement de plafond (100 -> 80) : sans cette
         * sous-commande, l'arbitrer a l'oeil aurait coute UN REFLASH PAR VALEUR,
         * et *« un parametre qu'on ne peut pas bouger en seance n'est pas
         * arbitrable en seance »* (§13.19.7 d, deja paye sur le plancher).
         * ⛔ IL REFUSE, IL N'ECRETE PAS — memes gardes que le plancher, par
         *   l'autre bout. */
        if (strcmp(argv[2], "plafond") == 0) {
            long pct = 0;
            if (argc != 4 || !parse_entier(argv[3], &pct)) {
                printf("usage : bl auto plafond <%d..%d>   (actuel : %d %%)\n",
                       dn_env_bl_plancher() + DN_ENV_BL_HYST, DN_ENV_BL_PCT_ABS_MAX,
                       dn_env_bl_plafond());
                return 1;
            }
            if (dn_env_bl_plafond_set((int)pct) != ESP_OK) {
                printf("refusé : le plafond doit être dans [%d, %d]. "
                       "Au-dessous de plancher+%d la loi serait INERTE sans le "
                       "dire ; au-dessus de %d la dalle refuserait le duty et la "
                       "loi viserait une cible jamais prise. Rien n'a été "
                       "touché.\n",
                       dn_env_bl_plancher() + DN_ENV_BL_HYST, DN_ENV_BL_PCT_ABS_MAX,
                       DN_ENV_BL_HYST, DN_ENV_BL_PCT_ABS_MAX);
                return 1;
            }
            /* ⚠️ `bl <n>` reste atteignable jusqu'a 100 : le plafond borne LA LOI,
             *    ⛔ pas la dalle. On le DIT, sinon le prochain `bl 100` passera
             *    pour un bug. */
            printf("⚠️ le plafond borne LA LOI, ⛔ pas la dalle : `bl 100` reste "
                   "un geste d'opérateur (il désarme l'auto et le dit).\n");
            /* 🔴 LE 6e ECRIVAIN DE LEDC — `dn_ui_veille_bl_rafraichir()`. Sans
             *   cet appel, l'oeil attendrait UN CYCLE DE 5 s pour voir l'effet,
             *   et un A/B ou l'effet arrive en retard est EXACTEMENT le protocole
             *   que l'owner a recuse le 2026-08-27. Il a deja ete oublie une fois
             *   (trouve en revue le meme jour, sur `bornes` et `plancher`). */
            dn_ui_veille_bl_rafraichir();
            bl_auto_etat();
            return 0;
        }
        /* ── bl auto courbe log|lineaire ──
         * 🔴 dn4-19/AC6.3 : la FORME de la loi, réfutable À CHAUD. C'est ce qui
         * garde l'ancienne loi de `dn4-3` atteignable pour un A/B contradictoire,
         * ⛔ sans reflash.
         * ⚠️ CORRIGÉ EN REVUE LE 2026-08-27 : ce commentaire portait le texte de
         * la branche `ambiant` (« les DEUX réglages du régime Ambient »), qui est
         * vingt lignes plus bas. Un en-tête de section qui décrit la branche
         * SUIVANTE envoie le lecteur au mauvais endroit. */
        if (strcmp(argv[2], "courbe") == 0) {
            if (argc != 4) {
                printf("usage : bl auto courbe log|lineaire   (actuelle : %s)\n",
                       dn_env_bl_courbe_nom(dn_env_bl_courbe()));
                return 1;
            }
            if (strcmp(argv[3], "log") == 0) {
                dn_env_bl_courbe_set(DN_ENV_BL_COURBE_LOG);
            } else if (strcmp(argv[3], "lineaire") == 0) {
                dn_env_bl_courbe_set(DN_ENV_BL_COURBE_LINEAIRE);
            } else {
                printf("« %s » n'est ni `log` ni `lineaire` — rien n'a été "
                       "touché.\n", argv[3]);
                return 1;
            }
            /* L'œil doit voir l'effet MAINTENANT si on dort ; en Actif, la
             * boucle rattrape au prochain cycle (5 s). */
            dn_ui_veille_bl_rafraichir();
            bl_auto_etat();
            return 0;
        }
        /* ── bl auto ambiant <0..100> | bl auto ambiant plancher <n> ──
         * dn4-19/AC3.2 + AC3.4 : les DEUX réglages du régime Ambient se
         * tranchent SUR LA DALLE, à l'œil, dans UNE séance — ⛔ pas au papier,
         * et ⛔ pas au prix de trois reflashs. */
        if (strcmp(argv[2], "ambiant") == 0) {
            if (argc == 5 && strcmp(argv[3], "plancher") == 0) {
                long pct = 0;
                if (!parse_entier(argv[4], &pct)) {
                    printf("usage : bl auto ambiant plancher <0..%d>\n",
                           dn_env_bl_plafond() - DN_ENV_BL_HYST);
                    return 1;
                }
                if (dn_env_bl_amb_plancher_set((int)pct) != ESP_OK) {
                    printf("refusé : le plancher d'Ambient doit être dans "
                           "[0, %d] — au-delà, la bande morte rendrait la loi "
                           "INERTE sans le dire. Rien n'a été touché.\n",
                           dn_env_bl_plafond() - DN_ENV_BL_HYST);
                    return 1;
                }
                dn_ui_veille_bl_rafraichir();
                bl_auto_etat();
                return 0;
            }
            long pct = 0;
            if (argc != 4 || !parse_entier(argv[3], &pct)) {
                printf("usage : bl auto ambiant <0..100>            (l'échelle)\n");
                printf("        bl auto ambiant plancher <0..%d>   (le plancher)\n",
                       dn_env_bl_plafond() - DN_ENV_BL_HYST);
                return 1;
            }
            if (dn_env_bl_amb_echelle_set((int)pct) != ESP_OK) {
                printf("refusé : l'échelle d'Ambient doit être dans [0, 100] %% "
                       "de la loi. Rien n'a été touché.\n");
                return 1;
            }
            /* L'œil doit voir l'effet MAINTENANT, pas au prochain cycle de 5 s. */
            dn_ui_veille_bl_rafraichir();
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

    /* ── bl loi [lux] ──────────────────────────────────────────────────────
     * 🔴 dn4-19 — L'INSTRUMENT DE PRÉDICTION EXISTAIT ET N'AVAIT AUCUN APPELANT.
     *   `dn_env_bl_loi()` est exposée dans `dn_env.h` avec le commentaire
     *   « exposé pour que la console puisse imprimer la loi sans l'appliquer »…
     *   et rien ne l'appelait. ⚠️ Depuis la revue du 2026-08-27, cette commande
     *   passe par `dn_env_bl_loi_regime()` / `dn_env_bl_loi_simule()` — il lui
     *   faut les DEUX régimes et les DEUX courbes, ⛔ sans rien muter. Résultat MESURÉ : la prédiction « 61 % » de la
     *   séance du 2026-08-27 a été calculée À LA MAIN, hors de la carte — alors
     *   que la règle du dépôt est *« s'en servir pour tout chiffre annoncé
     *   d'avance, ⛔ pas recalculer à la main dans un coin »*.
     * ⛔ N'APPLIQUE RIEN et NE DÉSARME RIEN : c'est une lecture. */
    if (strcmp(argv[1], "loi") == 0) {
        long lux = 0;
        /* 🔴 CORRIGÉ EN REVUE DE CODE LE 2026-08-27 — ~~`argc >= 3`~~ ⇒ les
         * arguments surnuméraires étaient **silencieusement jetés** : `bl loi 300
         * 600`, tapé en croyant donner deux bornes, rendait un chiffre pour
         * 300 lx et **passait pour une commande réussie**. ⛔ TOUTE autre
         * sous-commande de ce fichier refuse (`argc != 5` / `!= 4` / `!= 3`), et
         * le motif est gravé vingt lignes plus haut : *« ⛔ `argc != 5`, PAS
         * `argc < 5` — un token tapé de travers passait pour une commande
         * réussie (revue de code 2026-08-20) »*. Le même défaut, re-livré. */
        if (argc > 3) {
            printf("⛔ `bl loi` prend AU PLUS un argument. « %s » est en trop — "
                   "rien n'a été calculé.\n", argv[3]);
            printf("usage : bl loi [lux]   — sans argument, le lux COURANT\n");
            return 1;
        }
        bool fourni = (argc == 3);
        if (fourni && !parse_entier(argv[2], &lux)) {
            printf("« %s » n'est pas un nombre.\n", argv[2]);
            printf("usage : bl loi [lux]   — sans argument, le lux COURANT\n");
            return 1;
        }
        if (!fourni) {
            int courant = dn_env_lux();
            if (courant == DN_ENV_ABSENT ||
                dn_env_etat(DN_ENV_LUM) != DN_ENV_VIVANT) {
                /* ⛔ On ne fabrique PAS un « 0 lx » : « jamais lu » et « noir
                 * complet » ne s'impriment pas à l'identique — corrigé en revue
                 * de code le 2026-08-20, ⛔ ne pas le ré-introduire ici. */
                printf("⛔ pas de lux exploitable en ce moment : le BH1750 est "
                       "« %s ». Donner un lux explicitement : `bl loi <lux>`.\n",
                       dn_env_etat_nom(dn_env_etat(DN_ENV_LUM)));
                return 1;
            }
            lux = courant;
        }
        if (lux < 0) {
            printf("⚠️ un lux négatif n'existe pas — rien n'a été calculé.\n");
            return 1;
        }
        int actif = dn_env_bl_loi_regime((int)lux, DN_ENV_BL_REGIME_ACTIF);
        int ambi  = dn_env_bl_loi_regime((int)lux, DN_ENV_BL_REGIME_AMBIENT);
        /* 🔴 dn4-19 — ON IMPRIME AUSSI L'AUTRE FORME, ⛔ sans la poser : c'est ce
         * qui rend l'A/B d'AC6.3 CONTRADICTOIRE au lieu d'être une affirmation.
         * L'A/B a coûté deux séances au dépôt faute d'avoir les deux chiffres
         * côte à côte.
         * 🔴 CORRIGÉ EN REVUE DE CODE LE 2026-08-27 — ~~on basculait `s_bl_courbe`
         *   puis on le remettait~~. C'était une **mutation d'état global depuis la
         *   tâche REPL**, pendant que `dn_env_cycle()` tourne dans `dn_capt`, sur
         *   un S3 **bi-cœur sans affinité** : un cycle tombé dans la fenêtre
         *   appliquait la MAUVAISE loi — **44 % au lieu de 76 % à 245 lx**, la
         *   dalle chutant de 32 points pour 5 s — pendant que la ligne finale
         *   affirmait `⛔ RIEN N'A ÉTÉ APPLIQUÉ`. ⚠️ Et 76/44 est **exactement
         *   l'écart que l'A/B d'AC6.3 mesure** : la pollution tombait sur la
         *   mesure que cette commande sert à préparer.
         * ✅ `dn_env_bl_loi_simule()` prend la courbe **en paramètre**, comme le
         *   régime l'était déjà. ⇒ **une prédiction n'écrit plus l'état qu'elle
         *   lit**, et l'affirmation ci-dessous devient vraie SANS condition. */
        dn_env_bl_courbe_t c0 = dn_env_bl_courbe();
        dn_env_bl_courbe_t c_autre = (c0 == DN_ENV_BL_COURBE_LOG)
                                         ? DN_ENV_BL_COURBE_LINEAIRE
                                         : DN_ENV_BL_COURBE_LOG;
        int autre = dn_env_bl_loi_simule((int)lux, DN_ENV_BL_REGIME_ACTIF, c_autre);
        const char *autre_nom = dn_env_bl_courbe_nom(c_autre);
        printf("loi à %ld lx%s   ·   courbe : %s\n", lux,
               fourni ? "" : "  (lux COURANT, lu)", dn_env_bl_courbe_nom(c0));
        printf("  ACTIF   : %d %%\n", actif);
        printf("  AMBIENT : %d %%   (échelle %d %% · plancher %d %%)\n", ambi,
               dn_env_bl_amb_echelle(), dn_env_bl_amb_plancher());
        printf("  duty POSÉ en ce moment : %d %%   ·   régime : %s\n",
               dn_display_backlight_pct_state(),
               dn_env_bl_regime() == DN_ENV_BL_REGIME_AMBIENT ? "AMBIENT"
                                                              : "ACTIF");
        printf("  pour comparaison, courbe %s : %d %% en ACTIF\n", autre_nom,
               autre);
        printf("⛔ RIEN N'A ÉTÉ APPLIQUÉ, RIEN N'A ÉTÉ DÉSARMÉ ET LA COURBE EST "
               "REMISE : c'est une lecture.\n");
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
    printf("                                  ① plus longue SÉRIE de trames\n");
    printf("                                    consécutives non saines (dn4-12)\n");
    printf("                                  ② DISTRIBUTION des 4 seaux\n");
    printf("                                  ③ DÉPASSEMENT du seuil + sa\n");
    printf("                                    RÉFUTATION (c'est un MAX)\n");
    printf("        flush reset             — remet les compteurs à zéro\n");
    printf("                                  (glissement dn4-10 ET série dn4-12)\n");
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
        /*
         * 🔴 CORRIGE LE 2026-08-27 (3e revue) — LE TROISIEME SITE DU DEFAUT
         *    #780, ET LE SEUL QUI IMPRIME LES DEUX FENETRES DANS UNE SEULE
         *    COMMANDE. La correction du 2026-08-27 avait pose
         *    `dn_measure_bounce_reset()` sur `flush sync` et `flush path` — les
         *    deux sous-commandes qui rendent la main AVANT le bloc de
         *    glissement, donc les deux qui ne pouvaient PAS produire une sortie
         *    melangee. `flush full`, lui, tombe dans ce bloc par son chemin
         *    NOMINAL (le « et on continue vers l'affichage » plus bas) : il
         *    remettait les compteurs de FLUSH a zero puis imprimait la fenetre
         *    de GLISSEMENT d'avant, sans le dire. ⛔ Et le commentaire du bloc
         *    de glissement NOMMAIT deja « le chemin nominal de `flush full` » :
         *    la retombee etait VUE, la gate etait scopee a deux sites.
         * ⚠️ `flush full` est l'instrument de la « preuve NEGATIVE d'AC3 » —
         *    c'est donc la sortie qui portait un verdict d'acceptation qui
         *    etait contaminee.
         */
        dn_measure_bounce_reset();
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
        /* 🔴 2026-08-27 (revue de code) — `dn_measure_bounce_reset()` MANQUAIT.
         *    `flush sync` remettait à zéro les stats de flush et PAS celles du
         *    glissement : le `flush` suivant imprimait DEUX FENÊTRES DIFFÉRENTES
         *    CÔTE À CÔTE, sans le dire. Même défaut sur `flush path`. */
        dn_measure_bounce_reset();
        printf("synchro du flush : %s (compteurs remis à zéro, GLISSEMENT "
               "compris)\n",
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
        dn_measure_bounce_reset(); /* voir le correctif de `flush sync` ci-dessus */
        printf("chemin du flush : %s (compteurs remis à zéro, GLISSEMENT "
               "compris)\n",
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
     *    a son propre cas de reference est le defaut que ce depot a deja paye.
     * 🔴 CORRIGE LE 2026-08-27 (revue de code) — « AVANT TOUT `return` DE CETTE
     *    FONCTION » ETAIT FAUX, ET C'EST UN COMMENTAIRE QUI MENTAIT SUR SON
     *    PROPRE FICHIER. QUATRE sous-commandes rendent la main AVANT d'arriver
     *    ici : `flush reset`, `flush sync`, `flush path` et le refus de
     *    `flush full`. Ce bloc n'est donc atteint que par `flush` NU et par le
     *    chemin nominal de `flush full`.
     *    ⇒ CE QUI EST VRAI : il est place avant le `return` du RAPPORT, donc
     *      avant la sortie anticipee sur `flushes == 0` — ce qui suffit a tenir
     *      la raison d'etre ci-dessus. Et les deux sous-commandes qui remettaient
     *      les stats de flush a zero SANS toucher au glissement (`sync`, `path`)
     *      appellent desormais `dn_measure_bounce_reset()`, sinon le `flush`
     *      suivant collait deux fenetres differentes l'une a cote de l'autre. */
    {
        dn_bounce_stats_t b;
        dn_measure_bounce_get(&b);
        uint32_t per = dn_measure_periode_us();
        uint32_t bp = dn_measure_back_porch_us();
        uint32_t vb = dn_measure_vblank_us();
        printf("─── glissement de trame (dn4-10) — fenêtre %llu ms ───\n",
               (unsigned long long)b.fenetre_ms);
        /*
         * 🔴 dn4-5 / AC1.2 — LE CRI, ET IL PORTE SA PROPRE CONTRE-ÉPREUVE.
         *    Ce dénominateur rebouclait toutes les 71,58 min et publiait une
         *    fenêtre fausse À EXIT 0. Il est désormais en base int64 ; quand la
         *    fenêtre dépasse le seuil, on imprime CE QUE L'INSTRUMENT D'AVANT
         *    AURAIT DIT, à côté de la valeur juste. La démonstration est donc
         *    LUE sur la sortie, ⛔ pas déduite d'une relecture du code.
         * ⚠️ Le patron est celui de `cpu brut`, qui refuse sa table dans le
         *    même cas (correctif de revue du 2026-08-18) — à une différence
         *    près, et elle est délibérée : `cpu brut` REFUSE parce que ses
         *    compteurs rebouclent à des instants DIFFÉRENTS et qu'aucun
         *    pourcentage n'est récupérable. Ici l'origine est reconstruite,
         *    donc la fenêtre est JUSTE : refuser reviendrait à jeter un chiffre
         *    correct. On publie, et on dit ce qui aurait été faux.
         */
        if (b.fenetre_deborde) {
            printf("⚠️ FENÊTRE AU-DELÀ DE 71,58 min (2^32 µs) — l'instrument\n");
            printf("   d'AVANT dn4-5 aurait publié %lu ms ici, soit %llu ms de\n",
                   (unsigned long)b.fenetre_ms_32,
                   (unsigned long long)(b.fenetre_ms -
                                        (unsigned long long)b.fenetre_ms_32));
            printf("   MOINS que la réalité.\n");
            /*
             * ⚠️ CE QUE CETTE FENÊTRE EST, ET CE QU'ELLE N'EST PAS — vérifié
             *    au `grep` sur les deux dépôts le 2026-08-26, et ça DÉMENT le
             *    cadrage de dn4-5, qui la nommait « LE DÉNOMINATEUR des taux
             *    que flush publie ». Elle ne l'est pas : les taux ci-dessous
             *    se divisent par `intervalles`, `ph_n` et `t_demi_us`, jamais
             *    par elle, et AUCUN outil de tools/ ni de agent/ ne la lit.
             *    Le défaut reste entier — elle est le SEUL chiffre qui dise
             *    sur quelle durée les compteurs ci-dessous ont été cumulés, et
             *    c'est un humain qui fait la division. Une fenêtre fausse rend
             *    donc tout ce bloc INEXPLOITABLE, en ayant l'air correct.
             */
            printf("   ⚠️ cette fenêtre n'est PAS un dénominateur de calcul :\n");
            printf("      c'est la DURÉE DE CUMUL des compteurs ci-dessous, et\n");
            printf("      c'est le lecteur qui divise. Fausse, elle ne rend rien\n");
            printf("      d'absurde — elle rend tout PLAUSIBLE et inexploitable.\n");
        }
        if (b.raz_en_attente) {
            printf("⚠️ remise à zéro ARMÉE mais PAS ENCORE CONSOMMÉE (aucun vsync\n");
            printf("   depuis) : les chiffres ci-dessous sont ceux d'AVANT.\n");
        }
        if (b.lecture_dechiree) {
            /* 🔴 2026-08-27 : la garde de lecture n'a pas convergé en trois
             *    essais. Avant elle, ce cas sortait un `trames ≈ 4,29 x 10^9`
             *    sans un mot (RAZ consommée entre le compteur et sa base) ou
             *    une somme décalée de 2^32 µs. On le DIT. */
            printf("🔴 LECTURE DÉCHIRÉE : une remise à zéro ou une retenue 64\n");
            printf("   bits est tombée pendant la copie, 3 essais n'ont pas\n");
            printf("   convergé. ⛔ NE RIEN CONCLURE de ce bloc — retaper `flush`.\n");
        }
        /*
         * ══════════════════════════════════════════════════════════════════
         *  dn4-12 / AC2 — LE TRIPLET DE TÊTE : CE QUI SUIT L'ŒIL
         * ══════════════════════════════════════════════════════════════════
         *
         * 🔴 CE QU'ON RÉPARE ICI EST UN DÉFAUT DE PRÉSENTATION RÉEL : le
         *    DÉPASSEMENT du seuil était enterré en SOUS-LIGNE du « DÉFICIT
         *    PIRE », lui-même perdu au milieu du bloc, pendant que le COMPTE de
         *    corruptions — qui NE SUIT PLUS L'ŒIL depuis `4734d07` — sortait en
         *    évidence. §20bis.5 : 143 corruptions AVANT COMME APRÈS le correctif
         *    du 2026-08-23, pendant que l'œil passait de « ça descend et remonte
         *    toutes les secondes » à « plus de glissement ».
         *
         * 🔴 MAIS LA GRANDEUR DE TÊTE EST UN **TRIPLET**, ⛔ PAS LE MAX NU —
         *    DÉCISION OWNER D3 DU 2026-08-28. L'entrée de backlog demandait de
         *    publier le dépassement SEUL, sur la foi du tableau
         *    `+720 / +176 / +221 µs` du 2026-08-23. Or ce tableau COMPARE TROIS
         *    `ph_deficit_max_us` ENTRE EUX — ce que ce fichier interdit en
         *    toutes lettres quelques lignes plus bas — et dn4-22 l'a RÉFUTÉ PAR
         *    LA MESURE cinq jours plus tard : ARM 5 rend 1 300 µs de déficit
         *    pire pour UNE corruption, contre 896 µs pour 245 chez `f7be23c`.
         *    ⇒ le MAX n'est pas un discriminateur : UN SEUL POINT ABERRANT LE
         *      DÉPLACE. L'esprit du livrable est tenu (le dépassement monte en
         *      tête), la lettre est amendée (il n'y monte pas SEUL).
         *
         * ⛔ ON RÉORDONNE ET ON AJOUTE, ON N'EFFACE PAS : la distribution des
         *    quatre seaux et le bloc « DÉFICIT PIRE » ont été DÉPLACÉS ici
         *    depuis le bas du bloc, ⛔ pas dupliqués. Le titre du bloc ne change
         *    pas — il porte encore `dn4-10`, et c'est juste : c'est son bloc.
         */
        printf("  🎯 CE QUI SUIT L'ŒIL — LE TRIPLET DE TÊTE (dn4-12)\n");
        /* ── ① LA PLUS LONGUE SÉRIE ─────────────────────────────────────── */
        if (b.t_demi_us == 0u) {
            /* 🔴 AC1.8 — DÉSARMEMENT. À `bounce_px < 480` le demi-bounce vaut
             *    0 µs : la classe A ne peut PLUS EXISTER (aucune trame ne
             *    franchit un seuil qui n'existe pas). ⛔ On refuse la grandeur
             *    plutôt que de l'imprimer à zéro — « un zéro se lirait "aucune
             *    corruption" ». Et on DIT LAQUELLE DES TROIS EST PERDUE : ⛔ on
             *    ne se contente pas de se taire. */
            printf("   ① 🔴 PLUS LONGUE SÉRIE : DÉSARMÉE — bounce_px < %d px ⇒ "
                   "demi-bounce = 0 µs ⇒ LA CLASSE A (déficit franchi) N'EXISTE "
                   "PLUS.\n", DN_LCD_H_RES);
            printf("        ⇒ `set bounce %d` puis `reboot` pour réarmer.\n",
                   dn_bootcfg_defaut_bounce_px());
            printf("        ⚠️ les classes C (hors borne de sanité) et D (sans "
                   "enroulement) ⛔ NE DÉPENDENT PAS de ce seuil : elles restent "
                   "comptables. La série ci-dessous est donc PARTIELLE.\n");
            printf("        série PARTIELLE (C+D seulement) : %lu trames · "
                   "C %lu · D %lu · %lu série(s) · en cours %lu\n",
                   (unsigned long)b.ser_max, (unsigned long)b.ser_max_c,
                   (unsigned long)b.ser_max_d, (unsigned long)b.ser_n,
                   (unsigned long)b.ser_courante);
        } else {
            /* 🔴 D1 — LA CONVERSION EN MILLISECONDES SE FAIT **ICI**, ⛔ JAMAIS
             *    DANS L'ISR. La grandeur stockée est un COMPTE DE TRAMES, donc
             *    immunisée au rebouclage `esp_timer` de 71,58 min : 2^32 trames
             *    valent ~3,6 ans à 37,40 Hz. `periode_ns` est EXACTE
             *    (26 737 500 ns), la division n'arrive qu'ici. */
            printf("   ① PLUS LONGUE SÉRIE de trames CONSÉCUTIVES NON SAINES : "
                   "%lu trames ≈ %llu ms\n",
                   (unsigned long)b.ser_max,
                   (unsigned long long)((uint64_t)b.ser_max *
                                        (uint64_t)b.periode_ns / 1000000ULL));
            printf("        composition : %lu déficit franchi (A) · %lu hors "
                   "borne de sanité (C) · %lu sans enroulement (D)\n",
                   (unsigned long)b.ser_max_a, (unsigned long)b.ser_max_c,
                   (unsigned long)b.ser_max_d);
            printf("        commencée à la trame #%lu depuis la RAZ · %lu "
                   "série(s) au total\n",
                   (unsigned long)b.ser_max_debut, (unsigned long)b.ser_n);
            if (b.ser_courante) {
                /* ⚠️ SANS CETTE LIGNE, UN LECTEUR NE SAIT PAS SI LE MAXIMUM EST
                 *    ENCORE EN TRAIN DE CROÎTRE. Le maximum l'inclut DÉJÀ : il
                 *    est mis à jour à chaque trame en défaut, ⛔ pas à la
                 *    fermeture de la série. */
                printf("        🔴 SÉRIE EN COURS : %lu trames ≈ %llu ms — LE "
                       "MAXIMUM CI-DESSUS PEUT ENCORE CROÎTRE (il l'inclut "
                       "déjà).\n",
                       (unsigned long)b.ser_courante,
                       (unsigned long long)((uint64_t)b.ser_courante *
                                            (uint64_t)b.periode_ns / 1000000ULL));
            } else {
                printf("        série en cours : aucune (la dernière trame était "
                       "SAINE ou INDÉTERMINÉE).\n");
            }
            /* 🔴 AC1.4 — C'EST UN MINORANT, ET LA CONSOLE L'ÉCRIT. */
            printf("        ⚠️ MINORANT : %lu série(s) rompue(s) par une trame "
                   "INDÉTERMINÉE (horodatage postérieur · paire déchirée · 2+ "
                   "enroulements) — une série vraie a pu être COUPÉE EN DEUX.\n",
                   (unsigned long)b.ser_rompues_indet);
            printf("           ⛔ ce nombre NE SE SOUSTRAIT PAS et NE SE "
                   "RECOMPOSE PAS : il BORNE la confiance, il ne corrige rien.\n");
            printf("        ⚠️ la classe A ne peut pas commencer avant la %lue "
                   "trame (dégrossissage) : avant, aucun déficit n'est "
                   "calculable. C et D, elles, comptent dès la 1re.\n",
                   (unsigned long)b.ph_degrossi_n);
            if (b.ser_max == 0u) {
                printf("        ⛔ ZÉRO NE PROUVE RIEN tant que le témoin ne l'a "
                       "pas fait bouger : `flash on` doit rendre plusieurs "
                       "CENTAINES de trames, dominées par la classe D.\n");
            }
        }
        /* ── ② LA DISTRIBUTION — 🎯 LE SIGNAL JUGÉ FIABLE PAR dn4-22 ─────── */
        if (b.ph_n == 0) {
            printf("   ② ⛔ DISTRIBUTION : aucun échantillon de phase compté "
                   "(%lu écartés au dégrossissage) — ② et ③ n'ont RIEN "
                   "mesuré.\n", (unsigned long)b.ph_ecarte);
        } else if (b.t_demi_us == 0u) {
            /* 🔴 LE COMPTEUR DÉCORATIF, FERMÉ LE 2026-08-27 et DÉPLACÉ ICI le
             *    2026-08-28. À `bounce_px < 480` l'ISR saute tout le bloc de
             *    seuils, et cette ligne imprimait « 🔴 100 % (CORRUPTION) 0 » :
             *    quatre zéros qui se lisent « aucune corruption » alors que RIEN
             *    n'a été mesuré. On refuse la ligne au lieu de la remplir de
             *    zéros. */
            printf("   ② 🔴 SEUILS DÉSARMÉS : bounce_px < %d px ⇒ demi-bounce = "
                   "0 µs ⇒ les quatre compteurs de déficit N'ONT RIEN MESURÉ. "
                   "⛔ Aucun chiffre n'est publié ici : un zéro se lirait "
                   "« aucune corruption ».\n", DN_LCD_H_RES);
            printf("        ⇒ `set bounce %d` puis `reboot` pour réarmer.\n",
                   dn_bootcfg_defaut_bounce_px());
        } else {
            printf("   ② DISTRIBUTION des déficits (sur n=%lu trames comptées) : "
                   "10 %% %lu · 25 %% %lu · 50 %% %lu · 🔴 100 %% (CORRUPTION) "
                   "%lu\n",
                   (unsigned long)b.ph_n,
                   (unsigned long)b.ph_10pc, (unsigned long)b.ph_25pc,
                   (unsigned long)b.ph_50pc, (unsigned long)b.ph_100pc);
            /* 🔴 2026-08-27 : ces quatre seaux sont EMBOÎTÉS, et la sortie les
             *    présentait comme des paliers distincts. Un déficit > 100 %
             *    incrémente aussi 50, 25 et 10 % : un lecteur qui sommait les
             *    quatre comptait les pires JUSQU'À QUATRE FOIS. */
            printf("        ⛔ CUMULS EMBOÎTÉS, ⛔ pas des paliers disjoints : un "
                   "déficit > 100 %% compte dans LES QUATRE. Ne pas les "
                   "sommer.\n");
            printf("        🎯 c'est la DISTRIBUTION qui est le signal FIABLE "
                   "(dn4-22), ⛔ pas le maximum de ③.\n");
        }
        /* ── ③ LE DÉPASSEMENT DU SEUIL, **AVEC SA RÉFUTATION** ───────────── */
        if (b.t_demi_us == 0u) {
            printf("   ③ 🔴 DÉFICIT PIRE sous la référence : %lu µs — ⛔ et le "
                   "seuil de comparaison est INDISPONIBLE (demi-bounce = 0 µs), "
                   "voir ②.\n", (unsigned long)b.ph_deficit_max_us);
        } else {
            printf("   ③ 🔴 DÉFICIT PIRE sous la référence : %lu µs, pour un "
                   "demi-bounce qui s'écoule en %lu µs\n",
                   (unsigned long)b.ph_deficit_max_us,
                   (unsigned long)b.t_demi_us);
            if (b.ph_deficit_max_us > b.t_demi_us) {
                printf("        ⇒ DÉPASSÉ de %lu µs : la DMA a lu un tampon PAS "
                       "ENCORE REMPLI. C'est le décalage visible.\n",
                       (unsigned long)(b.ph_deficit_max_us - b.t_demi_us));
            } else {
                printf("        ⇒ sous le seuil, il restait %lu µs de marge "
                       "(%lu %% du demi-bounce)\n",
                       (unsigned long)(b.t_demi_us - b.ph_deficit_max_us),
                       (unsigned long)((b.t_demi_us - b.ph_deficit_max_us) *
                                       100u / b.t_demi_us));
            }
            /*
             * 🔴 AC2.3 — LA RÉFUTATION EST IMPRIMÉE, ⛔ PAS SEULEMENT CONNUE.
             *    Un opérateur qui lit ③ sans elle en fera un discriminateur
             *    entre deux fenêtres, ce que la mesure INTERDIT. Le chiffre qui
             *    l'établit est donné, ⛔ pas résumé.
             */
            printf("        ⛔ RÉFUTATION, ET ELLE EST MESURÉE : c'est un MAX — "
                   "UN SEUL POINT ABERRANT LE DÉPLACE. dn4-22/ARM 5 rend "
                   "1 300 µs pour UNE corruption, contre 896 µs pour 245 chez "
                   "`f7be23c`.\n");
            printf("           ⇒ à lire comme un ORDRE DE GRANDEUR, ⛔ PAS comme "
                   "un discriminateur entre deux fenêtres. Le signal, c'est ②.\n");
        }
        /* ── LE COMPTE, EN SECOND, AVEC SA RÉSERVE (AC2.4) ───────────────── */
        if (b.t_demi_us != 0u) {
            printf("  ── LE COMPTE, EN SECOND ─────────────────────────────\n");
            printf("  corruptions (déficit > 100 %% du demi-bounce) : %lu\n",
                   (unsigned long)b.ph_100pc);
            /* ⛔ ON NE DUPLIQUE PAS la phrase du bloc `#else` en fin de rapport
             *    (« CE COMPTEUR MESURE DONC LA FAMINE, PAS LE GLISSEMENT ») :
             *    on la RÉFÉRENCE, et on ajoute le CHIFFRE qui l'établit, qui
             *    lui n'était écrit nulle part dans la sortie. */
            printf("     ⚠️ RÉSERVE — voir « CE COMPTEUR MESURE DONC LA FAMINE, "
                   "PAS LE GLISSEMENT » en fin de bloc. Le chiffre qui "
                   "l'établit : 143 corruptions AVANT COMME APRÈS le correctif "
                   "du 2026-08-23,\n");
            printf("        pendant que l'œil passait de « ça glisse » à « plus "
                   "de glissement ». ⇒ ce compte NE SUIT PLUS L'ŒIL ; ① et ② "
                   "sont là pour ça.\n");
        }
        /*
         * ── LES CINQ CHIFFRES DE COMPARABILITÉ + L'INSTANT DE LA RAZ ───────
         * Règle dn4-22/AC3.2 : deux fenêtres ne se comparent que si ces cinq-là
         * sont dans le MÊME bloc que les chiffres qu'on compare. Ils sont
         * détaillés plus bas avec leurs contre-épreuves ; ici ils sont
         * RASSEMBLÉS, pour qu'une capture de tête se suffise à elle-même.
         */
        printf("  ── COMPARABILITÉ (les cinq chiffres, dn4-22/AC3.2) ──\n");
        printf("     ph_ref %lu µs · ph_max %lu µs · ph_n %lu · dégrossissage "
               "%lu trames · demi-bounce %lu µs\n",
               (unsigned long)b.ph_ref_us, (unsigned long)b.ph_max_us,
               (unsigned long)b.ph_n, (unsigned long)b.ph_degrossi_n,
               (unsigned long)b.t_demi_us);
        if (b.raz_gen == 0u) {
            /*
             * 🔴 « UN COMPTEUR VIDE N'EST PAS UNE ABSENCE D'HISTOIRE » — et ici
             *    ce n'est pas une formule : `flush` est remis à zéro par
             *    `flush reset` ET par TOUT REDÉMARRAGE DE LA PUCE. Une référence
             *    SEMÉE AU BOOT est PATHOLOGIQUE 1 FOIS SUR 4 (étendue 100 µs
             *    contre 1 µs pour un `flush reset` en régime ; le seau 10 %
             *    passe de 4,5 % à 99,98 % des trames). ⇒ ce n'est pas une
             *    précaution, c'est LA CONDITION DE COMPARABILITÉ.
             */
            printf("     ⛔ AUCUN `flush reset` : référence SEMÉE AU BOOT — 1 "
                   "semis sur 4 est PATHOLOGIQUE (symptôme : le seau 10 %% vaut "
                   "presque `n`).\n");
            printf("        ⇒ une fenêtre à référence pathologique reste "
                   "CONCLUANTE si elle rend une série COURTE (le biais "
                   "SUR-compte, le court tient a fortiori). ⛔ LA RÉCIPROQUE EST "
                   "FAUSSE.\n");
        } else {
            printf("     dernière RAZ : %lu consommée(s) depuis le boot · la "
                   "fenêtre ci-dessus (%llu ms) court depuis la dernière.\n",
                   (unsigned long)b.raz_gen,
                   (unsigned long long)b.fenetre_ms);
        }
        printf("  ─────────────────────────────────────────────────────\n");
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
            printf("     (période théorique %lu,%03lu us = %d x %d / %d Hz)\n",
                   (unsigned long)(b.periode_ns / 1000u),
                   (unsigned long)(b.periode_ns % 1000u),
                   DN_LCD_H_RES + DN_HSYNC_PULSE +
                   DN_HSYNC_BACK_PORCH + DN_HSYNC_FRONT_PORCH,
                   DN_LCD_V_RES + DN_VSYNC_PULSE + DN_VSYNC_BACK_PORCH +
                   DN_VSYNC_FRONT_PORCH, DN_PCLK_HZ);
            /* 🔴 2026-08-27 : la période était TRONQUÉE (26 737 au lieu de
             *    26 737,5), et la ligne « retard PIRE observé : +1 us »
             *    ci-dessous sortait donc SUR UNE TRAME PARFAITEMENT À L'HEURE —
             *    à comparer aux « +16 us » publiés comme résultat au repos. Elle
             *    est arrondie au plus proche, et la valeur EXACTE est imprimée
             *    en ns juste au-dessus. */
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
        /* ─── LES ÉCHANTILLONS QUE L'INSTRUMENT A JETÉS ────────────────────
         * 🔴 PUBLIÉS DEPUIS LE 2026-08-27 (revue de code). Aucun des trois
         *    n'était compté nulle part, et le premier est le plus grave : la
         *    borne de sanité écarte EXACTEMENT le glissement recherché.
         * ⛔ UN « 0 » SUR LES QUATRE SEUILS NE VAUT QUE SI CES TROIS-LÀ SONT À
         *    ZÉRO. Sinon la bonne lecture n'est pas « pas de corruption », c'est
         *    « des retards trop gros, trop doubles ou trop déchirés pour moi ». */
        if (b.ph_rejete || b.ph_doubles_ecartes || b.ph_dechire || b.ph_futur) {
            printf("  🔴 ÉCHANTILLONS DE PHASE JETÉS : %lu hors borne de sanité "
                   "(>= 2 périodes) · %lu trames à 2+ enroulements · %lu paires "
                   "(wraps,t_wrap) déchirées · %lu horodatages POSTÉRIEURS\n",
                   (unsigned long)b.ph_rejete,
                   (unsigned long)b.ph_doubles_ecartes,
                   (unsigned long)b.ph_dechire,
                   (unsigned long)b.ph_futur);
            if (b.ph_rejete) {
                printf("     ⛔ les « hors borne » SONT LES PIRES RETARDS : un "
                       "zéro plus bas ne veut pas dire « aucune corruption ».\n");
            }
            if (b.ph_futur) {
                /* 🔴 3e revue du 2026-08-27. Ces échantillons-là tombaient dans
                 *    `ph_rejete`, donc sous la phrase ci-dessus, qui AFFIRMAIT
                 *    une cause fausse pour eux. ⛔ Ils ne mesurent aucun retard :
                 *    ils mesurent que les deux ISR se sont croisées. */
                printf("     ⚠️ les « horodatages POSTÉRIEURS » ne sont ⛔ PAS "
                       "des retards : les deux ISR se sont croisées entre la "
                       "prise de `t_us` et la lecture de `wraps`.\n");
                printf("        Ils ne pèsent sur AUCUN seuil. C'est un coût "
                       "d'instrument, et il est ici pour être VU, pas pour être "
                       "interprété.\n");
            }
        }
        if (b.ph_n == 0) {
            printf("  phase enroulement→vsync : aucun échantillon compté (%lu "
                   "écartés au dégrossissage)\n", (unsigned long)b.ph_ecarte);
        } else {
            printf("  🎯 phase enroulement→VSYNC_END : n=%lu · min %lu · moy %lu "
                   "· MAX %lu us   (+%lu trames de dégrossissage, ⛔ HORS de ces "
                   "trois statistiques)\n",
                   (unsigned long)b.ph_n,
                   (unsigned long)b.ph_min_us,
                   (unsigned long)(b.ph_somme_us / b.ph_n),
                   (unsigned long)b.ph_max_us, (unsigned long)b.ph_ecarte);
            /* 🔴 2026-08-27 : `min`/`MAX` intégraient les 32 trames de
             *    dégrossissage, `moy` non — et la ligne présentait les trois
             *    comme issues du même `n`. Les chiffres publiés en §20.7.5
             *    (`min 1915 · moy 1961 · MAX 1978`) mélangeaient donc deux
             *    échantillons. Les trois portent désormais sur la MÊME
             *    population, et le dégrossissage est annoncé à part. */
            printf("     une phase COURTE = l'enroulement EN RETARD = le "
                   "remplissage du bounce qui décroche.\n");
            printf("     référence des déficits (FIGÉE après dégrossissage) : "
                   "%lu us · 1 ligne = %lu us\n",
                   (unsigned long)b.ph_ref_us, (unsigned long)b.us_par_ligne);
            /*
             * 🔴 LA CONTRE-EPREUVE ETAIT UNILATERALE — TROUVE PAR LA CARTE LE
             *    2026-08-27, ⛔ PAS PAR LA LECTURE. Elle ne testait que
             *    `MAX > reference` (reference trop BASSE => sous-comptage).
             *    Le cas SYMETRIQUE existe et il est PIRE : si le degrossissage
             *    tombe pendant le BOOT, quand rien ne dessine, la phase y est
             *    LONGUE => la reference est posee AU-DESSUS DE TOUTE LA
             *    POPULATION => TOUTES les trames affichent un deficit.
             *    MESURE sur la carte : `10 % 9372` sur `n=9372` — 100 % des
             *    trames — avec `MAX 2292` pour une reference de ~2452.
             *    ⛔ Et l'ancienne contre-epreuve etait MUETTE dans ce cas, parce
             *    que `MAX > ref` est FAUX quand la reference est trop haute.
             * ⇒ Les deux sens sont dits, et le second nomme son symptome
             *   (« le seau 10 % vaut ~n ») pour qu'il se reconnaisse a l'oeil.
             */
            if (b.ph_ref_us > b.ph_max_us) {
                printf("     🔴 RÉFÉRENCE (%lu) AU-DESSUS DU MAX (%lu) : le "
                       "dégrossissage est tombé dans un régime où la phase "
                       "était PLUS LONGUE qu'en régime (typiquement le BOOT) "
                       "⇒ les déficits ci-dessous sont SUR-comptés de %lu us "
                       "sur TOUTES les trames.\n",
                       (unsigned long)b.ph_ref_us, (unsigned long)b.ph_max_us,
                       (unsigned long)(b.ph_ref_us - b.ph_max_us));
                printf("        ⛔ SYMPTÔME À RECONNAÎTRE : le seau 10 %% vaut "
                       "presque `n`. Refaire `flush reset` EN RÉGIME, ⛔ pas au "
                       "boot.\n");
            } else if (b.ph_max_us > b.ph_ref_us) {
                /*
                 * La contre-épreuve de la référence figée : si la population
                 * comptée dépasse la référence, le dégrossissage a été pris
                 * dans un régime déjà dégradé et les déficits sont SOUS-comptés.
                 *
                 * 🔴 CETTE BRANCHE EST QUASI-CERTAINE, ET ELLE NE VAUT DONC PAS
                 *    VALIDATION — déclaré le 2026-08-27 (3e revue), décision
                 *    owner : ⛔ on NOTE, on ne refond pas.
                 *    `ph_ref_us` est le MAX de DN_PHASE_DEGROSSI (32) trames ;
                 *    `ph_max_us` est le MAX de la population comptée, qui se
                 *    chiffre en MILLIERS. Par statistique d'ordre, le max d'un
                 *    grand échantillon dépasse celui d'un petit tiré de la même
                 *    loi : `MAX > référence` est le résultat ATTENDU dès que
                 *    `n >> 32`, ⛔ pas un signal.
                 *    MESURÉ : les TROIS points de §20bis.10 la déclenchent
                 *    (2298/2258 · 1988/1963 · 1562/1520), et ces trois points
                 *    ont été pris AU REPOS — c'est-à-dire que le remède imprimé
                 *    ci-dessous était DÉJÀ la condition de la mesure.
                 * 🎯 CE QUE ÇA CHANGE, ET ⛔ CE QUE ÇA NE CHANGE PAS :
                 *    le biais SOUS-compte ⇒ le déficit vrai est SUPÉRIEUR à
                 *    celui publié ⇒ un franchissement du seuil `t_demi` est un
                 *    MINORANT et il tient A FORTIORI. En revanche tout RAPPORT
                 *    entre deux déficits (repos vs charge) est indéfendable :
                 *    les deux termes portent le même biais, dans des
                 *    proportions inconnues.
                 */
                printf("     ⚠️ MAX (%lu) > référence (%lu) : les déficits "
                       "ci-dessous sont SOUS-comptés de %lu us.\n",
                       (unsigned long)b.ph_max_us, (unsigned long)b.ph_ref_us,
                       (unsigned long)(b.ph_max_us - b.ph_ref_us));
                printf("        ⛔ CETTE LIGNE EST QUASI-CERTAINE, ce n'est PAS "
                       "un signal : la référence est le MAX de %lu trames, le "
                       "MAX porte sur %lu. Un `flush reset` au repos ne la "
                       "lèvera pas.\n",
                       (unsigned long)b.ph_degrossi_n, (unsigned long)b.ph_n);
                printf("        🎯 CE QU'ELLE AUTORISE : un seuil FRANCHI l'est "
                       "a fortiori (le vrai déficit est plus grand). ⛔ CE "
                       "QU'ELLE INTERDIT : comparer deux déficits entre eux — "
                       "ils portent le même biais.\n");
            }
            /*
             * ⛔ RÉORDONNÉ LE 2026-08-28 (dn4-12 / AC2.1), ⛔ PAS SUPPRIMÉ.
             *    QUATRE blocs vivaient ICI et ont été DÉPLACÉS EN TÊTE DE CE
             *    MÊME BLOC, ⛔ pas dupliqués :
             *      - « 🔴 DÉFICIT PIRE sous la référence »        ⇒ ③
             *      - « ⇒ DÉPASSÉ de N us » / « ⇒ sous le seuil »  ⇒ ③
             *      - « 🔴 SEUILS DÉSARMÉS » (bounce_px < 480)     ⇒ ②
             *      - la distribution 10/25/50/100 % + « CUMULS EMBOÎTÉS » ⇒ ②
             *    MOTIF : le DÉPASSEMENT était enterré en SOUS-LIGNE du déficit
             *    pire, lui-même au milieu du bloc, pendant que le COMPTE — qui
             *    NE SUIT PLUS L'ŒIL depuis `4734d07` — sortait en évidence.
             *    ⚠️ La ligne « 🔴 3e revue du 2026-08-27 : cette ligne imprimait
             *       "pour un demi-bounce qui s'écoule en 0 us" » a suivi son
             *       bloc en tête : le garde-fou y arrive toujours AVANT le
             *       chiffre qu'il existe pour taire.
             *    ⇒ Ce qui RESTE ici est le DÉTAIL de la phase et ses
             *      contre-épreuves : c'est leur place, ils qualifient les
             *      chiffres de tête sans les répéter.
             */
            printf("     ⚠️ PLANCHER : la microseconde, soit 16 px. ⛔ « 0 » ici ne "
                   "veut PAS dire « 0 pixel ».\n");
            printf("     ⚠️ L'horodatage de référence vient LUI AUSSI d'une ISR : "
                   "un retard COMMUN aux deux s'annule et reste invisible.\n");
        }
        /*
         * 🔴 CORRIGÉ LE 2026-08-27 (revue de code) — CES LIGNES SORTAIENT
         *    INCONDITIONNELLEMENT, ET ELLES SONT FAUSSES DEPUIS `4734d07`.
         *    Vérifié : aucune directive `#if` n'encadrait ce bloc, ce n'était
         *    donc pas une branche compilée mais un `printf` qui sortait à tous
         *    les coups. ⛔ Et ce n'est pas un commentaire de code : c'est LA
         *    SORTIE DE L'INSTRUMENT, celui dont on lit les corruptions. Un
         *    opérateur qui mesure lisait une explication décrivant LA
         *    CONFIGURATION OPPOSÉE à celle qu'il exécutait — troisième récidive
         *    de la classe de défaut que dn3-2 AC9 a payée.
         */
#if CONFIG_LCD_RGB_RESTART_IN_VSYNC
        printf("  ce que ça veut dire : le driver RGB remet la DMA à zéro à\n");
        printf("     CHAQUE VBlank (RESTART_IN_VSYNC=y) et écrit lui-même que\n");
        printf("     « si cette interruption est ASSEZ EN RETARD, l'image se\n");
        printf("     DÉCALE » (esp_lcd_panel_rgb.c:1142-1148). Le budget réel\n");
        printf("     est le back porch, %lu us — pas le VBlank entier (%lu us),\n",
               (unsigned long)bp, (unsigned long)vb);
        printf("     car VSYNC_END tombe à la FIN de l'impulsion.\n");
#else
        printf("  ce que ça veut dire : RESTART_IN_VSYNC=**n** dans CE binaire.\n");
        printf("     Le driver ne remet PLUS la DMA à zéro à chaque VBlank — et\n");
        printf("     c'est ce reset-là, quand l'ISR était en retard, qui\n");
        printf("     DÉCALAIT l'image (esp_lcd_panel_rgb.c:1142-1148). Le\n");
        printf("     glissement périodique est fermé par là (`4734d07`).\n");
        printf("     ⛔ CE COMPTEUR MESURE DONC LA FAMINE, PAS LE GLISSEMENT :\n");
        printf("     à `n` c'est le DÉPASSEMENT du seuil qui suit l'œil, pas le\n");
        printf("     compte.\n");
        /*
         * 🔴 AMENDÉ LE 2026-08-28 (dn4-12 / D3) — ⛔ LA LIGNE CI-DESSUS RESTE,
         *    PARCE QU'ELLE ÉTAIT JUSTE POUR SA DATE, MAIS ELLE EST DEVENUE
         *    INCOMPLÈTE. Elle a été écrite le 2026-08-23 sur la foi du tableau
         *    `+720 / +176 / +221 µs`, qui COMPARE TROIS `ph_deficit_max_us`
         *    ENTRE EUX — ce que le bloc « CE QU'ELLE INTERDIT » plus haut
         *    interdit en toutes lettres. dn4-22 l'a réfuté PAR LA MESURE cinq
         *    jours plus tard. ⛔ On annote, on n'efface pas.
         */
        printf("     ⚠️ AMENDÉ le 2026-08-28 (dn4-12/D3) : le dépassement seul\n");
        printf("     NE SUFFIT PAS — c'est un MAX, qu'UN SEUL point aberrant\n");
        printf("     déplace (dn4-22 : 1 300 us pour UNE corruption contre 896\n");
        printf("     pour 245). La tête de bloc est un TRIPLET : ① la plus\n");
        printf("     longue SÉRIE · ② la DISTRIBUTION · ③ le dépassement AVEC\n");
        printf("     sa réfutation. Le compte descend en second, avec sa réserve.\n");
        printf("     Le budget de l'ISR reste le back porch, %lu us —\n",
               (unsigned long)bp);
        printf("     pas le VBlank entier (%lu us), car VSYNC_END tombe à la FIN\n",
               (unsigned long)vb);
        printf("     de l'impulsion.\n");
        printf("     ⚠️ le driver garde SA propre relance sur famine avérée\n");
        printf("     (esp_lcd_panel_rgb.c:1153-1163), compilée dans ce binaire.\n");
#endif
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
    /* 🔴 CORRECTIF DE REVUE 2026-08-28 — LES ENROULEMENTS SE DISENT.
     *    Ces trois cumuls rebouclaient en SILENCE (px ~6,48 h, attente ~13,18 h,
     *    copie ~3,78 j) sur un dénominateur qui, lui, ne reboucle pas : les
     *    moyennes sortaient plausibles et fausses. Elles sont désormais
     *    COMPOSÉES sur 64 bits — mais le compte est publié quand même, parce
     *    qu'un lecteur qui compare ce bloc à une capture ANCIENNE doit savoir
     *    que l'ancienne était tronquée. */
    if (st.px_enr || st.copie_enr || st.attente_enr) {
        printf("⚠️ ENROULEMENTS 32 bits ABSORBÉS : px x%lu · copie x%lu · "
               "attente x%lu — les cumuls ci-dessous sont COMPOSÉS sur 64 bits "
               "et JUSTES. ⛔ Une capture d'avant le 2026-08-28 les publiait "
               "TRONQUÉS.\n",
               (unsigned long)st.px_enr, (unsigned long)st.copie_enr,
               (unsigned long)st.attente_enr);
    }
    printf("aire cumulée       : %llu px\n", (unsigned long long)st.px);
    printf("  => %llu px par flush en moyenne (écran plein = %d px, soit %.2f %%)\n",
           (unsigned long long)(st.px / st.flushes), DN_LCD_TOTAL_PX,
           (double)(st.px / st.flushes) * 100.0 / (double)DN_LCD_TOTAL_PX);
    if (st.cycles > 0) {
        printf("  => %llu px et %.1f flush(es) par CYCLE de redessin\n",
               (unsigned long long)(st.px / st.cycles),
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
    printf("copie              : %llu us cumulés, %llu us/flush en moyenne, "
           "%lu us au pire\n",
           (unsigned long long)st.copie_us,
           (unsigned long long)(st.copie_us / reels),
           (unsigned long)st.max_copie_us);
    printf("attente de synchro : %llu us cumulés, %llu us/flush en moyenne\n",
           (unsigned long long)st.attente_us,
           (unsigned long long)(st.attente_us / reels));
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
        /* 🔴 dn4-23 / AC6.3 — `dn_touch_reset_stats()` pose
         *    `s_base_consommes = s_consommes`, c'est-a-dire qu'il REMET A ZERO
         *    un compteur que CETTE commande ne publie PAS : `dn_touch_consommes()`
         *    n'a qu'UN SEUL lecteur dans tout l'arbre — la commande `veille`.
         *    Sans ce mot, une campagne de veille imprime « reveils : 3 » a cote
         *    de « taps CONSOMMES par un reveil : 0 », EXACTEMENT la
         *    contradiction que le mecanisme existe pour supprimer.
         * ⚠️ Le sens INVERSE est deja traite dans `dn_touch.h` (« ⛔ NE PAS
         *    appeler `dn_touch_reset_stats()` depuis `veille` ») ; celui-ci ne
         *    l'etait pas.
         * ⇒ UNE LIGNE D'AVERTISSEMENT, ⛔ pas un refus : l'occurrence est faible
         *   et le geste reste legitime. */
        printf("⚠️ ET AUSSI `s_base_consommes` : le compteur « taps CONSOMMES par\n");
        printf("   un reveil », que SEULE la commande `veille` publie. Une\n");
        printf("   campagne de veille lancee apres ce reset imprimera\n");
        printf("   « reveils : N » a cote de « taps CONSOMMES : 0 ».\n");
        printf("   ⇒ Pour une campagne de veille, relever AVANT, ou utiliser\n");
        printf("     `veille reset` (qui, lui, epargne les compteurs de `touch`).\n");
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
    printf("        nav menu                   ouvre la vue MENU (dn3-3)\n");
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
        /* 🔴 dn3-3 : LES TRANSITIONS PROVOQUEES PAR LA VEILLE SONT NOMMEES.
         *    Elles SONT dans le total (elles sont reelles) mais elles ne
         *    naissent d'aucun geste et leur chronometre n'est pas arme. Les
         *    laisser anonymes aurait fait grossir un denominateur avec des
         *    transitions d'origine HORLOGE, sans que rien ne le dise. */
        if (dn_ui_nav_veille_count() > 0) {
            printf("   dont %" PRIu32 " provoquee(s) par LA VEILLE (retour auto au"
                   " dashboard,\n", dn_ui_nav_veille_count());
            printf("   AC3.5) — comptees, mais SANS chronometre.\n");
        }
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

    if (strcmp(argv[1], "menu") == 0) {
        if (nav_bloque_par_pause("nav menu")) {
            return 1;
        }
        esp_err_t err = dn_ui_nav_menu();
        if (err == ESP_ERR_INVALID_STATE) {
            printf("rien a faire : le MENU est DEJA affiche.\n");
            printf("(aucune transition, aucun chronometre arme)\n");
            return 0;
        }
        if (err != ESP_OK) {
            printf("refuse : %s\n", esp_err_to_name(err));
            return 1;
        }
        printf("vue MENU ouverte.\n");
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
        /* 🔴 CORRIGÉ LE 2026-08-27 (revue de code) — CETTE LIGNE SE
         *    CONTREDISAIT AVEC CELLE JUSTE AU-DESSUS. Elle affirmait « jamais
         *    d'armement » à `num_fbs = 1`, deux lignes sous « recalages joués :
         *    1 ». Or `desknode_main.c` arme PRÉCISÉMENT à `num_fbs = 1` depuis
         *    `4734d07` : c'est le recalage d'AMORÇAGE, et sans lui l'image sort
         *    décalée en permanence. ⚠️ Aggravant : le log de boot envoie
         *    explicitement l'opérateur sur cette commande. */
        printf("  num_fbs actif : %d%s\n", dn_display_num_fbs(),
               dn_display_num_fbs() > 1
                   ? " — le recalage de BASCULE est actif"
                   : " — pas de bascule, donc pas de recalage de bascule ; mais "
                     "le recalage d'AMORÇAGE est armé UNE FOIS au boot par "
                     "desknode_main (⛔ un one-shot, aucune parade automatique "
                     "ensuite)");
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

/*
 * ══ dn4-23 / AC4 — `cpu` MESURE SANS BLOQUER LE TRANSPORT QU'IL MESURE ══════
 *
 * 🔴 LE DEFAUT, ET IL EST STRUCTUREL : `cpu N` fait `vTaskDelay(N * 1000 ms)`
 *    ENTRE ses deux `uxTaskGetSystemState()`. La tache qui dort EST la tache du
 *    REPL — c'est-a-dire LE TRANSPORT de la campagne. Pendant toute la fenetre,
 *    la console ne lit rien, ne repond rien, et l'agent PC qui pousse ses
 *    trames par `pc $DN,...` n'est plus servi.
 *    ⇒ MESURE : `cpu 20` publiait **0,8 % sous trafic** contre **0,9 % au
 *      repos** — la commande decrivait le dashboard AU REPOS, quel que soit le
 *      trafic, parce qu'elle avait ELLE-MEME arrete le trafic.
 *
 * ✅ LA PARADE : le delta ENCADRE. `cpu depart` pose un point ; l'operateur
 *    mene sa session (injection, navigation, ce qu'il veut) ; `cpu delta` lit
 *    le second point. ⛔ AUCUN `vTaskDelay` dans la tache du REPL : entre les
 *    deux, la console est VIVANTE et le transport aussi.
 *
 * ⚠️ LE REBOUCLAGE EST **GARDE**, ⛔ PAS COMMENTE. `configRUN_TIME_COUNTER_TYPE`
 *    est un `uint32_t` de microsecondes (RUN_TIME_STATS_USING_ESP_TIMER) : il
 *    reboucle a 2^32 us = **4 294,967 s, soit ~71,58 min**. La soustraction en
 *    non signe reste JUSTE tant que la fenetre est plus courte que ca ; a un
 *    tour complet elle devient ambigue et rendrait un chiffre FAUX ET
 *    PLAUSIBLE. ⇒ au-dela, la commande **REFUSE DE PUBLIER**.
 *    ⛔ C'est la meme doctrine que `cpu brut`, qui refuse deja sa table quand
 *      un compteur a reboucle : on refuse plutot que de publier.
 */
#define DN_CPU_DELTA_HORIZON_US 4294967296LL /* 2^32 us — le tour complet */

static TaskStatus_t *s_cpu_dep;          /* instantane de `cpu depart` */
static UBaseType_t s_cpu_dep_cap;
static UBaseType_t s_cpu_dep_n;
static int64_t s_cpu_dep_us = -1;        /* -1 = aucun point de depart pose */

static int cpu_depart(void)
{
    free(s_cpu_dep);
    s_cpu_dep = NULL;
    s_cpu_dep_us = -1;
    UBaseType_t capacite = uxTaskGetNumberOfTasks() + 8;
    s_cpu_dep = calloc(capacite, sizeof(TaskStatus_t));
    if (!s_cpu_dep) {
        printf("pas assez de RAM pour un releve de %u taches — AUCUN point pose\n",
               (unsigned)capacite);
        return 1;
    }
    configRUN_TIME_COUNTER_TYPE tot = 0;
    UBaseType_t n = uxTaskGetSystemState(s_cpu_dep, capacite, &tot);
    if (n == 0) {
        printf("🔴 uxTaskGetSystemState a rendu 0 tache pour une capacite de %u —\n",
               (unsigned)capacite);
        printf("   des taches sont nees entre le comptage et l'appel. AUCUN point\n");
        printf("   n'est pose, REJOUER.\n");
        free(s_cpu_dep);
        s_cpu_dep = NULL;
        return 1;
    }
    s_cpu_dep_cap = capacite;
    s_cpu_dep_n = n;
    s_cpu_dep_us = esp_timer_get_time();
    printf("point de depart POSE : %u taches, uptime %lld s\n", (unsigned)n,
           (long long)(s_cpu_dep_us / 1000000));
    printf("⇒ menez la session, PUIS `cpu delta`. ⛔ AUCUN sommeil ici : le REPL\n");
    printf("  reste vivant, donc le TRANSPORT aussi. C'est tout l'objet de cette\n");
    printf("  paire — `cpu N` dort dans la tache du REPL et mesure le repos\n");
    printf("  qu'elle vient de creer (0,8 %% sous trafic contre 0,9 %% au repos).\n");
    printf("⚠️ FENETRE MAXIMALE %lld s (~%lld min) : au-dela le compteur de\n",
           (long long)(DN_CPU_DELTA_HORIZON_US / 1000000),
           (long long)(DN_CPU_DELTA_HORIZON_US / 60000000));
    printf("  run-time a fait UN TOUR et le delta devient ambigu — `cpu delta`\n");
    printf("  REFUSERA de publier plutot que de rendre un chiffre plausible.\n");
    return 0;
}

static int cpu_delta(void)
{
    if (!s_cpu_dep || s_cpu_dep_us < 0) {
        printf("refuse : aucun point de depart. Poser `cpu depart` D'ABORD.\n");
        printf("⛔ Un delta sans origine n'est pas une mesure.\n");
        return 1;
    }
    int64_t maintenant = esp_timer_get_time();
    int64_t mural_us = maintenant - s_cpu_dep_us;
    if (mural_us <= 0) {
        printf("refuse : horloge non monotone entre les deux points (%lld us).\n",
               (long long)mural_us);
        return 1;
    }
    if (mural_us >= DN_CPU_DELTA_HORIZON_US) {
        printf("🔴 REFUS DE PUBLIER : la fenetre fait %lld s, l'horizon est %lld s\n",
               (long long)(mural_us / 1000000),
               (long long)(DN_CPU_DELTA_HORIZON_US / 1000000));
        printf("   (2^32 us, ~%lld min). Le compteur de run-time a fait AU MOINS\n",
               (long long)(DN_CPU_DELTA_HORIZON_US / 60000000));
        printf("   un tour : la soustraction en non signe ne distingue plus\n");
        printf("   « 10 s de CPU » de « 10 s + 71 min ». ⛔ Aucun pourcentage\n");
        printf("   n'est calculable. Reposer `cpu depart` et refaire une fenetre\n");
        printf("   plus courte.\n");
        return 1;
    }

    UBaseType_t capacite = uxTaskGetNumberOfTasks() + 8;
    TaskStatus_t *apres = calloc(capacite, sizeof(TaskStatus_t));
    if (!apres) {
        printf("pas assez de RAM pour un releve de %u taches\n", (unsigned)capacite);
        return 1;
    }
    configRUN_TIME_COUNTER_TYPE tot = 0;
    UBaseType_t n_apres = uxTaskGetSystemState(apres, capacite, &tot);
    if (n_apres == 0) {
        printf("🔴 uxTaskGetSystemState a rendu 0 tache — RIEN n'est publiable,\n");
        printf("   REJOUER (le point de depart, lui, reste pose).\n");
        free(apres);
        return 1;
    }

    unsigned long long somme = 0;
    for (UBaseType_t i = 0; i < n_apres; i++) {
        configRUN_TIME_COUNTER_TYPE base = 0;
        for (UBaseType_t j = 0; j < s_cpu_dep_n; j++) {
            if (s_cpu_dep[j].xHandle == apres[i].xHandle) {
                base = s_cpu_dep[j].ulRunTimeCounter;
                break;
            }
        }
        somme += (unsigned long long)(configRUN_TIME_COUNTER_TYPE)(
            apres[i].ulRunTimeCounter - base);
    }

    /* ⚠️ LES TACHES MORTES PENDANT LA SESSION SONT COMPTEES ET DITES : leur temps
     *    CPU sort du denominateur, donc les parts publiees sont legerement
     *    HAUTES. Un instrument qui tait ce biais rend un chiffre invendable. */
    int disparues = 0;
    for (UBaseType_t j = 0; j < s_cpu_dep_n; j++) {
        bool vue = false;
        for (UBaseType_t i = 0; i < n_apres; i++) {
            if (apres[i].xHandle == s_cpu_dep[j].xHandle) {
                vue = true;
                break;
            }
        }
        if (!vue) {
            disparues++;
        }
    }

    printf("charge CPU sur la SESSION (fenêtre mesurée : %lld ms, %u tâches)\n",
           (long long)(mural_us / 1000), (unsigned)n_apres);
    if (somme == 0) {
        printf("⚠️ somme des temps CPU nulle — les compteurs de run-time ne\n");
        printf("   tournent pas. Instrument invalide, ne rien conclure.\n");
        free(apres);
        return 1;
    }
    double reserve = 0.0;
    printf("  tâche               part\n");
    for (UBaseType_t i = 0; i < n_apres; i++) {
        configRUN_TIME_COUNTER_TYPE base = 0;
        for (UBaseType_t j = 0; j < s_cpu_dep_n; j++) {
            if (s_cpu_dep[j].xHandle == apres[i].xHandle) {
                base = s_cpu_dep[j].ulRunTimeCounter;
                break;
            }
        }
        unsigned long long d = (unsigned long long)(
            configRUN_TIME_COUNTER_TYPE)(apres[i].ulRunTimeCounter - base);
        double part = (double)d * 100.0 / (double)somme;
        bool oisive = (strncmp(apres[i].pcTaskName, "IDLE", 4) == 0);
        if (oisive) {
            reserve += part;
        }
        if (part >= 0.05 || oisive) {
            printf("  %-16s %7.1f %%%s\n", apres[i].pcTaskName, part,
                   oisive ? "   <= réserve" : "");
        }
    }
    printf("=> RÉSERVE (tâches IDLE) : %.1f %%  —  CHARGE : %.1f %%\n", reserve,
           100.0 - reserve);
    printf("   Rapporté au temps CPU total des %d cœurs sur la fenêtre.\n",
           configNUMBER_OF_CORES);
    if (disparues > 0) {
        printf("⚠️ %d tâche(s) du point de départ ont DISPARU : leur temps CPU\n",
               disparues);
        printf("   sort du dénominateur ⇒ les parts ci-dessus sont légèrement\n");
        printf("   HAUTES. ⛔ Le dire plutôt que de publier un total qui ment.\n");
    }
    printf("✅ AUCUN sommeil n'a eu lieu dans le REPL entre les deux points : le\n");
    printf("   transport est resté vivant, donc CETTE mesure-ci décrit bien le\n");
    printf("   régime que la session a produit.\n");
    free(apres);
    return 0;
}

static int cmd_cpu(int argc, char **argv)
{
    if (argc >= 2 && strcmp(argv[1], "brut") == 0) {
        return cpu_table_cumulee();
    }
    if (argc == 2 && strcmp(argv[1], "depart") == 0) {
        return cpu_depart();
    }
    if (argc == 2 && strcmp(argv[1], "delta") == 0) {
        return cpu_delta();
    }

    long fenetre = 5;
    if (argc >= 2) {
        if (!parse_entier(argv[1], &fenetre)) {
            printf("usage : cpu [secondes] | cpu brut | cpu depart | cpu delta\n");
            printf("  `depart`/`delta` = la mesure SANS BLOQUER le REPL (dn4-23).\n");
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

    /* 🔴 dn4-23 / AC4.3 — CETTE COMMANDE DIT CE QU'ELLE NE PEUT PAS MESURER,
     *    ET ELLE LE DIT **AVANT** DE DORMIR : imprimee apres la fenetre, la
     *    phrase arriverait quand l'operateur a deja son chiffre. */
    printf("⛔ CETTE COMMANDE BLOQUE LE REPL PENDANT %ld s — et si le REPL est\n",
           fenetre);
    printf("   votre transport (console de mesure, agent qui pousse `pc $DN,...`),\n");
    printf("   elle DECRIT LE DASHBOARD AU REPOS, quel que soit le trafic.\n");
    printf("   MESURE : 0,8 %% sous trafic contre 0,9 %% au repos — le trafic\n");
    printf("   avait ete arrete PAR LA MESURE ELLE-MEME.\n");
    printf("   ⇒ Pour chiffrer un regime SOUS trafic : `cpu depart` … session …\n");
    printf("     `cpu delta` (dn4-23/AC4, aucun sommeil dans le REPL).\n");

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
 * Il porte **30 sous-commandes** (plus `widget` nu, qui est une LECTURE pure).
 * ⚠️ « QUATORZE » était écrit ici et n'a jamais été re-compté depuis dn3-1 —
 *    corrigé par dn4-14-2, et désormais VÉRIFIÉ PAR LA GATE
 *    (`verif_veille_dn33.py`, `bloc_reconstruit`), qui RECOMPTE depuis le code
 *    à chaque passage. ⛔ Un compte écrit ne se re-vérifie jamais tout seul.
 * Aucune ne DORT — la console EST le transport PC depuis
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
 *   widget couleur <case> <0xRRGGBB>  dn4-14 — LA COULEUR D'UNE CASE, à chaud :
 *                           accent de tuile + chevron + série 0. `0` rend la
 *                           main au descripteur. ⛔ aucun état livré
 *                                                            ⚠️ RECONSTRUIT
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
 *   widget police <taille>          la police des VALEURS         ⚠️ RECONSTRUIT
 *                                   ⛔ « 14|28 » était écrit ici : la liste se
 *                                   RELIT de `DN_FONT_LISTE` (revue 2026-08-30)
 *   widget grille <barre> <menu>    D12 (60 51) / voie (a) (60 0) ⚠️ RECONSTRUIT
 *   ── dn4-14-2 : LES DEUX A/B DE POLICE DE TEXTE ──────────────────────────
 *   widget titre <police>|defaut    la police du TITRE de case — l'A/B du
 *                                   constat owner « cpu, gpu … trop petites ».
 *                                   ⛔ `widget entete` ne pouvait PAS le faire :
 *                                   il change l'ICÔNE, pas le libellé
 *                                                                ⚠️ RECONSTRUIT
 *   widget titre suit on|off        les libellés SECONDAIRES (grandeur, titre de
 *                                   la case NUE) suivent-ils ? 🔴 QUESTION OWNER
 *                                                                ⚠️ RECONSTRUIT
 *   widget date <police>|defaut     la police de la DATE de barre. ⛔ NE
 *                                   RECONSTRUIT PAS — le label est repeint en
 *                                   place, parce qu'une reconstruction PENDANT
 *                                   la veille pose la jauge 27 px trop haut
 *   ── dn4-6 / AC5 : LA LARGEUR, MESURÉE ───────────────────────────────────
 *   widget detail           ce que la GRANDE VALEUR du détail a POSÉ : texte,
 *                           largeur réelle, panneau — ⛔ relu, jamais recomposé
 *   widget largeur          la table des couples, RELUE de `lv_text_get_size()`
 *   widget largeur <texte>  la largeur d'UNE chaîne dans `font_val`
 *   widget largeur <txt> <police>   dn4-14-2 — la même, dans une police NOMMÉE.
 *                           ⚠️ Sans ça l'instrument mesure `font_val` (28) et
 *                           ne peut voir NI le mur de la date NI celui du titre,
 *                           tous deux en `dn_font_14`. La liste des polices est
 *                           RELUE de `DN_FONT_LISTE` (générée depuis `TAILLES`)
 *                           🔴 ⛔ ELLE NE PEUT PAS PORTER D'ACCENT : le REPL
 *                           SUPPRIME tout octet ≥ 0x80 (MESURÉ le 2026-08-29 —
 *                           « AÉB » rend 21 px, comme « AB » ; « °C » rend
 *                           « C »). Un jeton fait QUE d'accents devient vide et
 *                           DISPARAÎT, décalant les arguments. ⇒ pour les
 *                           chaînes accentuées : `widget largeur mur`, dont les
 *                           chaînes sont COMPILÉES.
 *   widget largeur mur      dn4-14-2 — LE TABLEAU DU MUR HORIZONTAL : les slots
 *                           RELUS du rendu (date, heure, titre), les chaînes
 *                           nommées d'AC2.2 dans CHAQUE police d'interface, et
 *                           le pire cas de date BALAYÉ sur toutes les formes
 *                           RÉELLES (le compte est IMPRIMÉ, ⛔ plus écrit ici :
 *                           « 7 × 12 × 32 » y était faux, et le code balayait
 *                           des jours qui n'existent pas dans leur mois)
 *                           — ⛔ pas supposé « MER. 06 SEPT. »
 *   widget largeur reset    remet à zéro les QUATRE compteurs de « ça ne tient
 *                           pas » — le 4ᵉ est le clip ACCEPTÉ de la date de
 *                           barre, ajouté par la revue du 2026-08-30
 *   widget titre [<police>|defaut]   dn4-14-2 / AC4 — la police du TITRE de case.
 *                           Nu, il RELIT et imprime l'état + le verdict de
 *                           largeur. ⚠️ RECONSTRUIT
 *   widget titre suit on|off  les libellés SECONDAIRES suivent le titre (`on`
 *                           par verdict owner du 2026-08-30). Nu, il dit
 *                           l'état. ⚠️ RECONSTRUIT
 *   widget date [<police>|defaut]    dn4-14-2 / AC4 — la police de la DATE de
 *                           barre. ⛔ NE reconstruit PAS (le label est repeint
 *                           en place). Nu, il RELIT et imprime les deux
 *                           verdicts, horizontal ET vertical.
 *
 * 🔴 LES **16** « RECONSTRUIT » BLOQUENT LE REPL, DONC LE TRANSPORT PC (relevé
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
 * 🔴 ET UNE QUATRIÈME FOIS — REVUE DE CODE DU 2026-08-29. `dn4-14` a ajouté
 *    `widget couleur`, qui appelle `build_scene()` comme les autres, et l'a
 *    correctement marquée « ⚠️ RECONSTRUIT » vingt-huit lignes plus haut… en
 *    laissant **DOUZE** ici et dans le README. Le point de rupture annoncé par
 *    ce bloc a donc rompu **une fois de plus, sur la story qui l'avait lu**.
 *
 * 🔴🔴 ET UNE **CINQUIÈME**, PIRE QUE LES QUATRE AUTRES — dn4-14-2, 2026-08-29.
 *    Les quatre premières ruptures étaient des ARRIÉRÉS : un compte qui n'avait
 *    pas suivi. Celle-ci est différente — **le TREIZE était FAUX AU MOMENT OÙ ON
 *    L'ÉCRIVAIT**, et le README en portait la preuve. Recompté DEPUIS LE CODE
 *    (chaque appel à `build_scene()` rattaché à sa fonction, chaque fonction à
 *    sa sous-commande) : la liste de TREIZE **omettait `detpan` et `fond`**, que
 *    le README lui-même décrivait « ⚠️ reconstruit la scène ». Le même README
 *    écrivait donc, sur la MÊME ligne, *« est passé à TREIZE »* **et** *« le
 *    compte passe de DOUZE à QUATORZE »*. Deux valeurs, une ligne, et **aucune
 *    des deux n'était le nombre**.
 *    ⚠️ `courbe`, lui, ne reconstruit PAS : `dn_ui_detail_courbe_axes()` est un
 *      LECTEUR. Une analyse trop grossière l'avait compté — vérifié à la main.
 *
 *    LA LISTE, RECOMPTÉE DU CODE — **16** :
 *      anciennes : `opa` · `voile` · `icone` · `nue` · `piste`
 *      dn4-6     : `voie` · `grandeurs` · `dispo` · `entete` · `val` · `police`
 *                  · `grille`
 *      jamais comptées : `detpan` · `fond`
 *      dn4-14    : `couleur`
 *      dn4-14-2  : `titre`   (⛔ `date`, non : le label est repeint EN PLACE)
 *
 * 🎯 ET LA PARADE N'EST PLUS « FAIRE ATTENTION », PARCE QUE ÇA A ÉCHOUÉ CINQ
 *    FOIS. `verif_veille_dn33.py` (`bloc_reconstruit`) **RECOMPTE** ce nombre
 *    depuis `dn_console.c` + `dn_ui.c` et le CONFRONTE à ce que ce docblock ET
 *    le README publient. Un sixième oubli ROUGIT la gate. ⛔ Ne pas corriger le
 *    texte sans relancer la gate : c'est elle qui fait foi, pas cette liste.
 *
 *    ⛔ `replacer`, `largeur`, `detail` et `courbe` NE reconstruisent PAS : ne pas les y
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
    /*
     * 🔴 dn4-23 / AC5.1 — ELLE TRONQUE DESORMAIS, ET C'EST LE DEFAUT QU'ELLE
     *    EXISTE POUR FERMER. La boucle de rembourrage ci-dessous NE TOURNE PAS
     *    quand `cols > largeur` : aucune coupe n'avait lieu, et un libelle trop
     *    long DECALAIT toute la fin de la ligne — exactement le symptome de
     *    `%-Ns` que cette fonction remplace. Une colonne qui ne borne que par le
     *    BAS n'est pas une colonne.
     * ⛔ LA COUPE EST EN COLONNES D'AFFICHAGE, ⛔ jamais en octets : couper au
     *    milieu d'une sequence UTF-8 produirait un octet orphelin que le
     *    terminal rend en « ï¿½ » — un defaut PIRE que le decalage.
     * ⚠️ ET LA COUPE SE VOIT : le dernier caractere devient « > ». Tronquer en
     *    silence remplacerait un mensonge d'alignement par un mensonge de
     *    contenu, et ce depot refuse les deux.
     */
    int cols = 0;
    const unsigned char *coupe = NULL;
    for (const unsigned char *p = (const unsigned char *)s; *p; p++) {
        if ((*p & 0xC0) != 0x80) {          /* octet de TETE d'un caractere */
            if (largeur >= 1 && cols == largeur - 1 && coupe == NULL) {
                coupe = p;                   /* debut du caractere n° largeur-1 */
            }
            cols++;
        }
    }
    if (coupe != NULL && cols > largeur) {
        printf("%.*s>", (int)(coupe - (const unsigned char *)s), s);
        return;                              /* DEJA `largeur` colonnes */
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
/*
 * ══ dn4-23 / AC5.3 — `widget largeur` DIT QUAND LE TEXTE RECU N'EST PAS CELUI
 *    QUI A ETE TAPE ═══════════════════════════════════════════════════════════
 *
 * 🔴 MESURE : `widget largeur RÉSEAU 18` mesure **`RSEAU`**. Le REPL retire
 *    tout octet >= 0x80 ; ici DEUX octets sautent (le `É` en UTF-8), le jeton
 *    ne se VIDE pas, `argc` reste a 4, et la commande rendait un verdict de
 *    largeur **sans un mot**. La garde de `dn4-14-2` ne couvre que le cas
 *    TOTALEMENT accentue — celui ou le jeton disparait et `argc` tombe a 3.
 *
 * ⛔ ON NE CHANGE PAS LE REPL. L'entree de ledger le dit elle-meme : « limite
 *    PREEXISTANTE du REPL, ⛔ pas de cet instrument ». On leve UN DRAPEAU.
 *
 * 🎯 COMMENT ON PEUT LE SAVOIR SANS LES OCTETS PERDUS : on ne devine pas, on
 *    COMPARE. Le produit connait son propre vocabulaire accentue — les noms de
 *    metriques et les formes de date de la barre. Si le jeton recu est
 *    EXACTEMENT l'une de ces chaines privee de ses octets >= 0x80, la
 *    mutilation est nommee ET son original aussi.
 * ⚠️ Et hors de ce vocabulaire, la LIMITE est imprimee quand meme : un operateur
 *    ne doit pas avoir a se souvenir de la regle pour ne pas etre trompe.
 */
static void ascii_seul(const char *src, char *out, size_t n_out)
{
    size_t k = 0;
    for (const unsigned char *p = (const unsigned char *)src; *p; p++) {
        if (*p < 0x80 && k + 1 < n_out) {
            out[k++] = (char)*p;
        }
    }
    if (n_out > 0) {
        out[k] = '\0';
    }
}

static int cols_de(const char *s)
{
    int n = 0;
    for (const unsigned char *p = (const unsigned char *)s; *p; p++) {
        if ((*p & 0xC0) != 0x80) {
            n++;
        }
    }
    return n;
}

static bool largeur_original_probable(const char *recu, char *out, size_t n_out)
{
    char red[64];
    for (int i = 0; i < DN_UI_METRIQUES; i++) {
        const char *nom = dn_ui_metrique_nom(i);
        ascii_seul(nom, red, sizeof(red));
        if (strcmp(red, nom) != 0 && strcmp(red, recu) == 0) {
            snprintf(out, n_out, "%s", nom);
            return true;
        }
    }
    /* Les formes de date de la barre — `AOÛT`, `FÉVR.`, `MER.` … Elles sont
     * ENGENDREES par la meme fabrique que l'ecran (`dn_ui_barre_date_forme`),
     * ⛔ pas recopiees ici : une table locale se perimerait au premier mois
     * renomme. */
    for (int js = 0; js <= 7; js++) {
        for (int mo = 0; mo <= 12; mo++) {
            if ((js == 7) != (mo == 0)) {
                continue;
            }
            for (int jr = 1; jr <= 31; jr++) {
                char d[24];
                if (!dn_ui_barre_date_forme(js, jr, mo, d, sizeof(d))) {
                    continue;
                }
                ascii_seul(d, red, sizeof(red));
                if (strcmp(red, d) != 0 && strcmp(red, recu) == 0) {
                    snprintf(out, n_out, "%s", d);
                    return true;
                }
            }
        }
    }
    return false;
}

static void largeur_drapeau_repl(const char *recu)
{
    char orig[32];
    if (largeur_original_probable(recu, orig, sizeof(orig))) {
        printf("🔴 LE TEXTE MESURE N'EST PAS CELUI QUI A ETE TAPE — DRAPEAU LEVE.\n");
        printf("   « %s » est EXACTEMENT « %s » prive de ses octets >= 0x80, et\n",
               recu, orig);
        printf("   « %s » est une chaine que CE PRODUIT AFFICHE. Le REPL les\n", orig);
        printf("   retire SANS UN MOT : %d caractere(s) manquent a la mesure\n",
               cols_de(orig) - cols_de(recu));
        printf("   ci-dessus, et `argc` n'a PAS bronche (la mutilation est\n");
        printf("   PARTIELLE, le jeton ne s'est pas vide).\n");
        printf("   ⛔ NE PAS CONCLURE SUR CE CHIFFRE. ⇒ `widget largeur mur`,\n");
        printf("     dont les chaines sont COMPILEES, ⛔ pas tapees.\n");
        return;
    }
    printf("⚠️ %d octet(s) / %d colonne(s) — et le REPL RETIRE tout octet\n",
           (int)strlen(recu), cols_de(recu));
    printf("   >= 0x80 avant d'arriver ici (mesure du 2026-08-29 : « AEB » rend\n");
    printf("   21 px comme « AB »). Si un accent a ete tape, la chaine MESUREE\n");
    printf("   n'est pas celle qui a ete TAPEE — et `argc` ne bronche pas quand\n");
    printf("   la mutilation est PARTIELLE. ⇒ pour de l'accentue :\n");
    printf("   `widget largeur mur`, dont les chaines sont COMPILEES.\n");
}

/*
 * ══ dn4-23 / AC6.2 — LE VERDICT DE CONTRASTE DES LEVIERS A CHAUD ════════════
 *
 * 🔴 LE CAS N'EST PLUS HYPOTHETIQUE. `W_COL_PISTE_DEFAUT` vaut `0x141820`
 *    depuis `dn4-29` ⇒ `veille case 141820` pose l'aplat EXACTEMENT sur la
 *    piste : ecart NUL, **la jauge disparait integralement**, et la console
 *    imprimait « applique MAINTENANT » sans un mot. Trois leviers peuvent la
 *    noyer — `veille case`, `widget opa`, `widget couleur` — et aucun n'avait
 *    de verdict.
 *
 * ⛔ LE GARDE-FOU EXISTANT NE SUFFIT PAS : `veille_dire_si_pas_neutre()` ne
 *    teste que `R == G == B`. C'est une garde de NEUTRALITE RGB565, ⛔ pas de
 *    contraste — un `0x141820` n'est pas un gris, elle se tait.
 *
 * ⚠️ ON AVERTIT, ⛔ ON NE REFUSE PAS. Doctrine explicite de ces commandes :
 *    « c'est un instrument d'A/B, l'owner doit voir la couleur qu'il tape ».
 *
 * 🔴 LE SEUIL EST UN **REPERE EMPRUNTE**, ET C'EST ECRIT PLUTOT QUE TU.
 *    `bloc_gris` (`tools/verif_veille_dn33.py`) exige `>= 24` — mais il
 *    gouverne LES TROIS GRIS DE REGIME ENTRE EUX, et `dn_widget.c` interdit
 *    nommement de le transposer : « la paire piste<->fond n'a jamais eu de
 *    seuil ». ⇒ ici, 24 n'est PAS un verdict, c'est LE SEUL REPERE CHIFFRE DONT
 *    CE DEPOT DISPOSE. Trois bandes, et une seule est une certitude :
 *      · ecart NUL      ⇒ 🔴 CERTITUDE ARITHMETIQUE : les deux surfaces sont la
 *                          MEME couleur, il n'y a plus de frontiere. ⛔ Aucun
 *                          oeil n'est requis pour trancher ca.
 *      · 0 < ecart < 24 ⇒ ⚠️ A VERIFIER A L'OEIL — ⛔ pas un verdict.
 *      · ecart >= 24    ⇒ au-dessus du repere. ⛔ Toujours pas une preuve : la
 *                          preuve est le constat owner sur la dalle.
 *
 * ⚠️ LES SIX DESCRIPTEURS LIVRES SONT HORS DE DANGER (Δ >= 97) : le risque est
 *    LE LEVIER A CHAUD, ⛔ pas la palette livree. ⛔ Ceci n'est PAS la passe de
 *    palette — c'est `dn4-29`, et elle s'arbitre A L'OEIL, PAR L'OWNER.
 */
#define DN_CONTRASTE_REPERE 24 /* ⚠️ REPERE emprunte a `bloc_gris`, ⛔ pas un seuil */

/* Luminance ITU-R BT.601 (77/150/29 sur 256) — la MEME que `dn_widget_desaturer`.
 * ⚠️ Le motif est PERCEPTUEL : le vert pese 59 %, le bleu 11 %. Une moyenne des
 *    trois canaux ne dit pas ce que l'oeil voit. */
static int lum601(uint32_t rgb)
{
    unsigned r = (rgb >> 16) & 0xFFu, g = (rgb >> 8) & 0xFFu, b = rgb & 0xFFu;
    unsigned y = (r * 77u + g * 150u + b * 29u) >> 8;
    return (int)(y > 255u ? 255u : y);
}

static const char *contraste_bande(int ecart)
{
    if (ecart == 0) {
        return "🔴 ECART NUL — LA JAUGE DISPARAIT";
    }
    if (ecart < DN_CONTRASTE_REPERE) {
        return "⚠️ FAIBLE — a verifier A L'OEIL";
    }
    return "au-dessus du repere";
}

static void verdict_contraste(void)
{
    /* ⛔ TOUT EST RELU. Une copie locale de la piste ou de l'aplat rendrait un
     *    verdict sur une valeur que l'ecran n'a pas. */
    uint32_t piste = dn_widget_piste();
    uint32_t fond_amb = dn_widget_amb_case_bg();
    uint8_t opa = dn_widget_opa();
    bool ambient = (dn_veille_mode() == DN_VEILLE_AMBIENT);
    int lp = lum601(piste);
    int lf = lum601(fond_amb);

    printf("── VERDICT DE CONTRASTE (dn4-23/AC6.2) — luminance BT.601, 0..255 ──\n");
    printf("  piste de jauge       %06lX  lum %3d\n", (unsigned long)piste, lp);
    printf("  aplat de case AMBIENT %06lX  lum %3d   ecart %3d  %s\n",
           (unsigned long)fond_amb, lf, lp > lf ? lp - lf : lf - lp,
           contraste_bande(lp > lf ? lp - lf : lf - lp));
    /* ⚠️ EN ACTIF L'ECART N'EST PAS CALCULABLE, ET ON NE FAIT PAS SEMBLANT :
     *    l'aplat est du NOIR a `s_opa`, donc l'artwork du Living PCB traverse a
     *    (255 - opa)/255. Le fond effectif ne peut qu'ETRE PLUS CLAIR que le
     *    noir ⇒ l'ecart calcule ci-dessous est un PLAFOND, pas la mesure.
     *    ⚠️ Et c'est un cas REEL, ecrit dans `dn_widget.c` : le cuivre sous
     *      l'aplat rend 24 la ou la piste rend 23. */
    printf("  aplat de case ACTIF   noir a %u/255 sur l'artwork ⇒ %u %% du Living\n",
           (unsigned)opa, (unsigned)((255u - opa) * 100u / 255u));
    printf("     PCB traverse. ecart <= %3d (PLAFOND, fond noir pur) — ⛔ la\n", lp);
    printf("     valeur REELLE depend de l'ARTWORK sous la case et n'est PAS\n");
    printf("     calculable ici (le cuivre rend 24 la ou la piste rend %d).\n", lp);

    printf("  indicateur ↔ piste, mode %s%s :\n", ambient ? "AMBIENT" : "ACTIF",
           ambient ? " (accents desatures)" : "");
    int pire = 255;
    for (int i = 0; i < DN_UI_METRIQUES; i++) {
        if (!dn_ui_desc(i)) {
            continue; /* case rendue NUE : aucun accent peint */
        }
        /* ⛔ RELU par la MEME fonction que l'ecran (`dn_widget_desaturer`), avec
         *    le MEME taux : un rapport calcule sur une copie de la formule
         *    mesurerait l'accord de la copie avec elle-meme. */
        uint32_t acc = dn_widget_desaturer(dn_ui_case_couleur(i),
                                           ambient ? dn_widget_accent_amb() : 0);
        int la = lum601(acc);
        int e = la > lp ? la - lp : lp - la;
        if (e < pire) {
            pire = e;
        }
        printf("    ");
        colonnes(dn_ui_metrique_nom(i), 10);
        printf("%06lX  lum %3d   ecart %3d  %s\n", (unsigned long)acc, la, e,
               contraste_bande(e));
    }
    if (pire == 255) {
        printf("    (aucune case n'est un widget : rien a comparer)\n");
    }
    printf("⚠️ ON AVERTIT, ⛔ ON NE REFUSE PAS : c'est un instrument d'A/B, et\n");
    printf("   l'owner doit voir la couleur qu'il tape.\n");
    printf("⛔ Le repere %d vient de `bloc_gris`, qui gouverne LES TROIS GRIS DE\n",
           DN_CONTRASTE_REPERE);
    printf("   REGIME entre eux. La paire piste↔fond n'a JAMAIS eu de seuil ⇒\n");
    printf("   au-dessus du repere n'est PAS une preuve. Seul l'ecart NUL est une\n");
    printf("   certitude, et c'est de l'arithmetique : meme couleur, plus de\n");
    printf("   frontiere.\n");
    printf("⛔ CECI N'EST PAS LA PASSE DE PALETTE — c'est `dn4-29`, et elle\n");
    printf("   s'arbitre A L'OEIL, PAR L'OWNER.\n");
}

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

/*
 * 🔴 dn4-14-2 / REVUE DU 2026-08-30 — LE BALAYAGE DE DATE ÉTAIT ÉCRIT TROIS FOIS,
 *    ET LES TROIS COPIES MENTAIENT SUR LEUR DOMAINE. Les docblocs annonçaient
 *    « 7 × 12 × 32 » pendant que les boucles faisaient `jr = 1..31`, et le
 *    dossier publiait « 7 × 12 × 31 = 2 604 » : trois textes, trois valeurs,
 *    aucune juste — et surtout, le balayage mesurait « MER. 31 FÉVR. », une
 *    chaîne que le produit ne rend JAMAIS.
 * ⇒ UNE fabrique, et elle REND son compte : `dn_ui_barre_date_forme()` filtre
 *   désormais les jours qui n'existent pas dans leur mois, et l'appelant
 *   IMPRIME `n`. ⛔ Le nombre ne s'écrit plus nulle part.
 * ⚠️ ET LE PIRE CAS N'EST PAS QUE DANS LE CALENDRIER : `dn_rtc.c` masque le
 *    registre du jour de semaine en `0x07`, donc **7 est atteignable**, et le
 *    composeur émet alors `"???"`. La forme DÉGRADÉE (`jsem = 7`, `mois = 0`)
 *    est donc tirée elle aussi — elle ne sortait d'aucune des trois copies.
 */
static int date_pire_cas(const lv_font_t *f, char *out, size_t n_out, int *n_formes)
{
    int pire_w = -1;
    int n = 0;
    if (out && n_out) {
        out[0] = '\0';
    }
    for (int js = 0; js <= 7; js++) {
        for (int mo = 0; mo <= 12; mo++) {
            /* ⚠️ On ne tire la ligne dégradée QUE dans sa combinaison réelle :
             * `jsem = 7` et `mois = 0` sont les deux valeurs que le composeur
             * traduit en `"???"`. Les mélanger à des mois valides fabriquerait
             * des formes que le RTC ne produit pas. */
            if ((js == 7) != (mo == 0)) {
                continue;
            }
            for (int jr = 1; jr <= 31; jr++) {
                char d[24];
                if (!dn_ui_barre_date_forme(js, jr, mo, d, sizeof(d))) {
                    continue;
                }
                n++;
                int w = dn_widget_largeur(d, f);
                if (w > pire_w) {
                    pire_w = w;
                    if (out && n_out) {
                        snprintf(out, n_out, "%s", d);
                    }
                }
            }
        }
    }
    if (n_formes) {
        *n_formes = n;
    }
    return pire_w;
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
            /* dn4-15 / AC5 — ⛔ AUCUN NOMBRE ICI, ET C'EST LE POINT.
             * Cette ligne imprimait DEUX COORDONNEES EN DUR — la bande
             * `VENTILOS` de dn3-2 et la bande de jauge `RAM` de dn4-1 —
             * toutes deux MORTES, et enseignees a un humain EN SEANCE.
             * ⛔ Elles ne sont pas recopiees ici : un nombre mort cite dans
             *    un commentaire se re-propage aussi bien que dans un printf.
             *    Le git les garde ; ce fichier ne les enseigne plus.
             * ⛔ INTERDIT d'y substituer `337..347` : `ui_case_origine()` et le
             *    docblock de `widget jauge` (~170 l. plus bas) etablissent que
             *    c'est le nombre publie par `dn4-2` SANS qu'aucun instrument ne
             *    puisse le confronter. Remplacer un nombre mort par un nombre
             *    NON CONFRONTE refait l'erreur que `dn4-4/AC9` a reparee.
             * ⇒ Le renvoi va a l'INSTRUMENT, pas a une valeur. */
            printf("  · D12 applique : toutes les coordonnees tactiles publiees\n");
            printf("    PERIMENT — ⛔ AUCUN NOMBRE ICI : `widget jauge [<case>]`\n");
            printf("    RELIT le rectangle REEL pose par LVGL (dn4-4/AC9).\n");
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
            /* dn4-15 / AC5.3 — TROISIEME SITE, RATTRAPE PAR LA REVUE DU
             * 2026-08-30. Il AFFIRME la peremption comme les deux autres, mais
             * il etait le seul a ne renvoyer a AUCUN instrument : l'ancien
             * controle de la gate comptait `widget jauge` SUR TOUT LE FICHIER
             * (seuil >= 2, deja atteint par la commande elle-meme), donc il ne
             * pouvait pas voir ce trou. ⛔ Toujours AUCUN NOMBRE ici. */
            printf("    ⇒ ⛔ AUCUN NOMBRE : `widget jauge [<case>]` RELIT le\n");
            printf("      rectangle REEL pose par LVGL (dn4-4/AC9).\n");
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
               "en colonne unique · %u en HAUTEUR · %u date de barre\n",
               (unsigned)dn_widget_chevauchements(),
               (unsigned)dn_widget_trop_larges(),
               (unsigned)dn_widget_debordements(),
               (unsigned)dn_ui_barre_date_trop_large());
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
            bool cok = dn_ui_courbe_compteurs(&ca, &cr);
            printf("  ── le DESSIN sur le chemin chaud (dn4-13 / AC5) ──\n");
            if (!cok) {
                printf("     ⛔ PAS MESURE — verrou LVGL non pris en 1000 ms.\n");
                printf("        (⛔ ce n'est PAS « zero » : ne rien publier d'ici.)\n");
            } else {
            printf("     reparametrages demandes : %lu · REDESSINS reels : %lu\n",
                   (unsigned long)ca, (unsigned long)cr);
            /* 🔴 REVUE 2026-08-25 — `cr > ca` DEBORDAIT EN NON SIGNE et
             *    imprimait « 1431655732 % ». Les deux compteurs se lisent
             *    desormais sous verrou, donc le cas ne doit plus survenir : s'il
             *    survient, on le DIT, ⛔ on ne fabrique pas un pourcentage. */
            if (cr > ca) {
                printf("     ⛔ INCOHERENT : redessins > demandes — ⛔ aucun ratio publie.\n");
            } else if (ca > 0) {
                printf("     ⇒ %lu %% des demandes N'ONT PRODUIT AUCUN appel LVGL\n",
                       (unsigned long)((ca - cr) * 100u / ca));
            } else {
                printf("     (aucune demande depuis le dernier `touch reset`)\n");
            }
            }
            printf("     ⚠️ CUMULATIFS. Pour mesurer un REGIME : `touch reset`,\n");
            printf("        laisser tourner, relire. ⛔ C'est bien `touch reset`\n");
            printf("        qui remet les compteurs UI a zero, ⛔ pas `widget`.\n");
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
        printf("🔴 dn4-13 / AC9 — `off` LAISSE DESORMAIS L'ECRAN **VRAIMENT NOIR**.\n");
        printf("   Jusqu'au 2026-08-25, `fond_poser()` ecrasait deux etats l'un\n");
        printf("   sur l'autre : `off` tombait dans la branche `ASSET ABSENT` et\n");
        printf("   peignait un ecran ROUGE 0x7f0000 AVEC DEUX LABELS. Le\n");
        printf("   commentaire promettait pourtant « l'ecran reste NOIR ».\n");
        printf("   ⇒ TROIS etats : `off` = noir nu · `on` + asset absent =\n");
        printf("     panneau ASSET ABSENT (la vraie panne de dn1-2, CONSERVEE) ·\n");
        printf("     `on` + asset = image + voile.\n");
        printf("🔴 CONSEQUENCE SUR UN CHIFFRE DEJA PUBLIE : la borne haute de\n");
        printf("   « l'option n°2 » (139,5 ms) a ete relevee contre un\n");
        printf("   remplissage plat + DEUX LABELS, alors qu'AC7 de dn4-4\n");
        printf("   promettait « UNE SEULE VARIABLE : le fond, et rien d'autre ».\n");
        printf("   ⛔ Ce chiffre N'EST PAS COMPARABLE a ce que cette commande\n");
        printf("      mesure maintenant. Il se RE-TIRE (dn4-13 / AC11.1).\n");
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
        /*
         * 🔴 dn4-14-2 / AC7.1 — CE MESSAGE MENTAIT SUR TROIS POINTS À LA FOIS,
         *    ET AUCUN N'ÉTAIT RE-VÉRIFIÉ PAR QUOI QUE CE SOIT :
         *      · « IL N'Y A QUE DEUX POLICES EMBARQUEES » — faux depuis
         *        dn4-14-2 : il y en a autant que `TAILLES` en porte, et la
         *        liste se RELIT désormais du registre (`polices_imprimer`).
         *      · « npm + reseau » — RÉFUTÉ par dn4-14 : `lv_font_conv` 1.5.3
         *        répond depuis un shim local, onze conversions tirées.
         *      · « ~19 Ko EXTRAPOLES » pour la police 22 — FAUX D'UN FACTEUR ~2 :
         *        MESURÉ le 2026-08-29, 39 250 o d'objet (39 173 o de données de
         *        police). ⚠️ Et le coût qui fait foi reste le DELTA DE BINAIRE :
         *        les quatre candidats 16+18+20+22 ont coûté **+134 832 o** de
         *        binaire pour 126 756 o d'objets — le reste est du CODE.
         *        🔴 **REVUE DU 2026-08-30 — CETTE LIGNE DISAIT « +134 304 »**,
         *        contre « +134 832 » dans `hardware/…affichage.md` §29.7. Écart
         *        de **528 o**, et c'est 134 832 qui est juste : il est le seul
         *        cohérent avec 1 322 848 − 1 188 016, et avec la somme
         *        37 424 (net) + 97 408 (rendus par le ménage).
         * ⛔ La liste des tailles acceptées n'est plus écrite ici : elle vient
         *   de `DN_FONT_LISTE`, générée depuis `TAILLES`.
         */
        const lv_font_t *nf = dn_widget_police_par_nom(argv[2]);
        if (nf && dn_widget_police_interface(nf)) {
            g.font_val = nf;
        } else {
            printf("usage : widget police <taille>   (actuelle : dn_font_%s, "
                   "line_height %d)\n",
                   dn_widget_police_nom(g.font_val),
                   (int)lv_font_get_line_height(g.font_val));
            polices_imprimer();
            if (nf) {
                printf("⛔ « %s » est une police de VEILLE : plage reduite, ni\n",
                       argv[2]);
                printf("   accent ni symbole. La valeur « 25,5 °C » y perdrait\n");
                printf("   son degre SANS UN MOT. Refusee.\n");
            }
            printf("⚠️ Le cout d'une police se MESURE au delta de BINAIRE, ⛔ pas\n");
            printf("   au plancher `octets_police` (il sous-estime), et surtout\n");
            printf("   ⛔ pas a une extrapolation par l'aire.\n");
            /* 🔴 REVUE DU 2026-08-30 — AC7.1 EXIGE QUE CE MESSAGE **DISE** LE
             *    CHIFFRE ET LE FAIT. Ils vivaient dans le commentaire C
             *    ci-dessus, jamais imprimes : l'operateur sur la dalle ne
             *    recevait ni l'un ni l'autre, c'est-a-dire exactement la moitie
             *    de l'AC. */
            printf("   MESURE le 2026-08-29 : la police 22 fait 39 250 o d'objet\n");
            printf("   (39 173 o de donnees) — le « ~19 Ko extrapoles » publie\n");
            printf("   etait FAUX D'UN FACTEUR ~2. Les 4 candidats 16+18+20+22\n");
            printf("   ont coute +134 832 o de BINAIRE.\n");
            printf("⚠️ Et « npm + reseau » est REFUTE : la chaine REPOND depuis un\n");
            printf("   shim local (lv_font_conv 1.5.3).\n");
            return 1;
        }
        esp_err_t e = dn_ui_set_widget_geom(&g);
        if (e != ESP_OK) {
            printf("refuse (%s) — RIEN n'a change\n", esp_err_to_name(e));
            return 1;
        }
        /* 🔴 REVUE DU 2026-08-30 — CE MESSAGE IMPRIMAIT LA COPIE **ENVOYEE**.
         *    Il lisait `g.font_val`, la copie locale passee au setter, ⛔ pas un
         *    `dn_widget_geom()` RELU — contrairement a `widget titre` et
         *    `widget date`, qui relisent tous les deux. Et le NOM de la police
         *    n'etait pas imprime du tout. AC4.4 dit « imprimant ce qui est
         *    reellement pose ». */
        dn_widget_geom_t apres;
        dn_widget_geom(&apres);
        printf("police des valeurs : dn_font_%s (line_height %d) — SCENE "
               "RECONSTRUITE\n",
               dn_widget_police_nom(apres.font_val),
               (int)lv_font_get_line_height(apres.font_val));
        return 0;
    }

    /*
     * ════════════════════════════════════════════════════════════════════════
     * dn4-14-2 / AC4 — LES DEUX A/B, COMMUTÉS À CHAUD
     * ════════════════════════════════════════════════════════════════════════
     * 🔴 IL EN FAUT **DEUX**, ET ILS NE SE FUSIONNENT PAS. Le titre vit dans
     *    `dn_widget_geom_t` (c'est un élément de CASE) ; la date vit dans
     *    `dn_ui.c` (la barre N'EST PAS un widget). Les faire passer par la même
     *    commande « parce que c'est plus court » mettrait un réglage de barre
     *    sous le contrat de `dn_widget_geom_appliquee()`.
     * ⚠️ ⛔ `widget entete` NE SUFFISAIT PAS : il gouverne l'ICÔNE et le BADGE,
     *    ⛔ pas le titre, qui était `&dn_font_14` EN DUR.
     */
    /*
     * 🔴 LES FORMES NUES DISENT L'ETAT — DEFAUT TROUVE EN SEANCE, 2026-08-30.
     *    `widget titre` sans argument tombait sur l'usage GENERIQUE (perime :
     *    il annonce « police 14|28 » et ne nommait AUCUNE des trois commandes
     *    de cette story), et `widget date` sans argument NE DISAIT RIEN DU
     *    TOUT — une commande MUETTE, exactement la classe de defaut que ce
     *    depot traque. ⇒ Les deux RELISENT et IMPRIMENT.
     * ⛔ Trouve en relisant l'ETAT REEL apres le flash de livraison, ⛔ pas en
     *   relisant la commande envoyee.
     * 🔴 **REVUE DE CODE DU 2026-08-30 — LE CONSTAT AVAIT ETE FAIT ICI ET LA
     *    CHAINE D'AIDE LAISSEE EN PLACE.** Ce commentaire ecrivait que l'usage
     *    generique « annonce police 14|28 et ne nomme AUCUNE des trois
     *    commandes » ; les formes nues ont ete corrigees, mais l'`aide`
     *    ENREGISTREE (`DN_CMD("widget", …)`) et le docblock du haut disaient
     *    encore `police 14|28`, et le « Jeu complet » du README ne nommait pas
     *    `widget titre`. ⇒ Les TROIS sont corriges — dans le meme geste, comme
     *    la regle inscrite au-dessus de `DN_CMD` l'exige depuis dn2-1.
     * 🔴 ET LA TROISIEME FORME NUE MANQUAIT : `widget titre suit` sans `on|off`
     *    tombait lui aussi sur l'usage generique. Traite plus bas.
     */
    if (argc == 2 && strcmp(argv[1], "titre") == 0) {
        dn_widget_geom_t g;
        dn_widget_geom(&g);
        int cw = 0;
        dn_ui_case_dim(&cw, NULL);
        int t_utile = dn_widget_titre_utile(cw, true);
        printf("police du TITRE : dn_font_%s (line_height %d)\n",
               dn_widget_police_nom(g.font_titre),
               (int)lv_font_get_line_height(g.font_titre));
        printf("libelles secondaires (grandeur, case NUE) : %s\n",
               dn_widget_titre_suit() ? "SUIVENT le titre" : "restent en 14");
        printf("  police effective des libelles : dn_font_%s\n",
               dn_widget_police_nom(dn_widget_font_libelle()));
        printf("slot du titre : x = %d, %d px utiles (case %d, badge a %d)\n",
               dn_widget_titre_x(true), t_utile, cw,
               dn_widget_titre_x(true) + t_utile);
        for (int i = 0; i <= DN_UI_METRIQUES; i++) {
            const char *t = dn_ui_case_titre(i);
            if (!t) {
                continue;
            }
            int w = dn_widget_largeur(t, g.font_titre);
            printf("  %-14s %3d px%s\n", t, w,
                   w > t_utile ? "  🔴 CLIPPE — LVGL ne dira RIEN" : "");
        }
        printf("⚠️ %u trop-large(s) depuis le dernier `widget largeur reset`.\n",
               (unsigned)dn_widget_trop_larges());
        printf("usage : widget titre <police>|defaut · widget titre suit on|off\n");
        return 0;
    }

    if (argc == 2 && strcmp(argv[1], "date") == 0) {
        const lv_font_t *f = dn_ui_barre_date_font();
        int date_x = 0, date_utile = 0;
        dn_ui_barre_slots(NULL, &date_x, &date_utile);
        printf("police de la DATE : dn_font_%s (line_height %d)\n",
               dn_widget_police_nom(f), (int)lv_font_get_line_height(f));
        printf("slot : x = %d, %d px utiles\n", date_x, date_utile);
        char pire[24] = "";
        int n_formes = 0;
        int pire_w = date_pire_cas(f, pire, sizeof(pire), &n_formes);
        int w0 = dn_widget_largeur(dn_ui_date_inconnue(), f);
        printf("  pire DATE reelle (BALAYEE sur %d formes) « %s » %d px  %s\n",
               n_formes, pire, pire_w,
               pire_w <= date_utile ? "TIENT" : "🔴 NE TIENT PAS");
        printf("  pire cas du SLOT  « %s » %d px  %s\n", dn_ui_date_inconnue(),
               w0, w0 <= date_utile
                       ? "TIENT"
                       : "🔴 CLIPPE — ecart DECLARE, verdict owner 2026-08-30");
        printf("usage : widget date <police>|defaut\n");
        return 0;
    }

    if (argc == 3 && strcmp(argv[1], "titre") == 0 &&
        strcmp(argv[2], "suit") != 0) {
        dn_widget_geom_t g;
        dn_widget_geom(&g);
        const lv_font_t *f = dn_widget_police_par_nom(argv[2]);
        if (!f && strcmp(argv[2], "defaut") != 0) {
            printf("usage : widget titre <police>|defaut|suit on|off\n");
            printf("  actuelle : dn_font_%s (line_height %d)\n",
                   dn_widget_police_nom(g.font_titre),
                   (int)lv_font_get_line_height(g.font_titre));
            polices_imprimer();
            printf("⛔ Une police de VEILLE est REFUSEE ici : « RESEAU »\n");
            printf("   perdrait son E sans un mot (plage reduite).\n");
            return 1;
        }
        g.font_titre = f; /* `defaut` ⇒ NULL ⇒ resolu a l'usage */
        esp_err_t e = dn_ui_set_widget_geom(&g);
        if (e != ESP_OK) {
            printf("refuse (%s) — RIEN n'a change\n", esp_err_to_name(e));
            if (e == ESP_ERR_INVALID_ARG) {
                printf("⛔ police de VEILLE sur un texte d'interface : le\n");
                printf("   validateur la REFUSE (dn_ui_geom_valider).\n");
            }
            return 1;
        }
        /* ⛔ RELU DE L'ETAT REEL, jamais de `argv` : c'est la difference entre
         *    « j'ai envoye » et « c'est pose ». */
        dn_widget_geom_t apres;
        dn_widget_geom(&apres);
        int cw = 0;
        dn_ui_case_dim(&cw, NULL);
        printf("police du TITRE : dn_font_%s (line_height %d) — SCENE RECONSTRUITE\n",
               dn_widget_police_nom(apres.font_titre),
               (int)lv_font_get_line_height(apres.font_titre));
        printf("libelles secondaires (grandeur, case NUE) : %s\n",
               dn_widget_titre_suit() ? "SUIVENT" : "restent en 14");
        /* Le verdict de largeur, TOUT DE SUITE — ⛔ pas au prochain relevé.
         * LVGL clippe SANS UN MOT : si on ne le dit pas ici, personne ne le
         * saura avant d'avoir pense a relire un compteur. */
        int t_utile = dn_widget_titre_utile(cw, true);
        printf("slot du titre : %d px utiles (case %d)\n", t_utile, cw);
        for (int i = 0; i <= DN_UI_METRIQUES; i++) {
            const char *t = dn_ui_case_titre(i);
            if (!t) {
                continue;
            }
            int w = dn_widget_largeur(t, apres.font_titre);
            if (w > t_utile) {
                printf("  🔴 « %s » = %d px > %d — CLIPPE de %d px\n", t, w,
                       t_utile, w - t_utile);
            }
        }
        printf("⚠️ %u trop-large(s) comptes depuis le dernier reset.\n",
               (unsigned)dn_widget_trop_larges());
        /* 🔴 REVUE DU 2026-08-30 — DEUX NOUVELLES PORTES VERS UN DANGER QUE
         *    CE MEME COMMIT NOMME AILLEURS. Le frere `widget date` a ete
         *    concu pour NE PAS reconstruire et IMPRIME pourquoi ; ces deux
         *    commandes-ci reconstruisent et ne disaient rien. Meme
         *    avertissement que `widget couleur`, ⛔ pas un refus : le mode
         *    n'est pas interrogeable d'ici, et refuser a l'aveugle
         *    bloquerait un reglage legitime en mode ACTIF. */
        printf("⛔ SI LA CARTE EST EN VEILLE : `veille off` D'ABORD. Une scene\n");
        printf("   reconstruite en Ambient pose la jauge 27 px TROP HAUT, et\n");
        printf("   AUCUN compteur ne le dit (ledger, 2026-08-29).\n");
        return 0;
    }

    /*
     * 🔴 REVUE DU 2026-08-30 — LA TROISIEME FORME NUE MANQUAIT.
     *    Le commit qui a corrige `widget titre` et `widget date` nus a laisse
     *    `widget titre suit` tomber sur l'usage GENERIQUE : la branche
     *    `argc == 3` s'exclut explicitement de `suit`, et la branche dediee
     *    exige `argc == 4`. ⇒ La forme nue ne disait pas l'etat, exactement la
     *    classe de defaut que les deux autres venaient de fermer.
     * ⛔ Elle NE RECONSTRUIT PAS : c'est une lecture pure.
     */
    if (argc == 3 && strcmp(argv[1], "titre") == 0 &&
        strcmp(argv[2], "suit") == 0) {
        printf("libelles secondaires : %s\n",
               dn_widget_titre_suit() ? "SUIVENT le titre"
                                      : "restent en dn_font_14");
        printf("  police effective des libelles : dn_font_%s (line_height %d)\n",
               dn_widget_police_nom(dn_widget_font_libelle()),
               (int)lv_font_get_line_height(dn_widget_font_libelle()));
        printf("  reserve verticale qui en decoule : %d px\n",
               2 + (int)lv_font_get_line_height(dn_widget_font_libelle()));
        printf("usage : widget titre suit on|off\n");
        return 0;
    }

    if (argc == 4 && strcmp(argv[1], "titre") == 0 &&
        strcmp(argv[2], "suit") == 0) {
        bool on = false;
        if (!parse_on_off(argv[3], &on)) {
            printf("usage : widget titre suit on|off   (actuel : %s)\n",
                   dn_widget_titre_suit() ? "on" : "off");
            printf("⚠️ `on` = le LIBELLE DE GRANDEUR (`c.max`, `extr.moy`) et le\n");
            printf("   titre de la case NUE prennent la police du TITRE.\n");
            printf("🔴 C'EST UNE QUESTION OWNER : le verbatim dit « les ecriture\n");
            printf("   sont trop petites (cpu, gpu etc..) » — « cpu, gpu » sont\n");
            printf("   des TITRES. Rien ne dit si ces deux-la suivent.\n");
            return 1;
        }
        dn_widget_set_titre_suit(on);
        /* ⚠️ RECONSTRUCTION OBLIGATOIRE : un label LVGL naît avec sa police, et
         *    `dn_widget_font_libelle()` n'est lue qu'à la création. Poser le
         *    drapeau sans reconstruire serait « un réglage qui ne fait rien
         *    sans l'annoncer » — la classe de défaut que `dma` a coûtée. */
        dn_widget_geom_t g;
        dn_widget_geom(&g);
        esp_err_t e = dn_ui_set_widget_geom(&g);
        if (e != ESP_OK) {
            printf("refuse (%s)\n", esp_err_to_name(e));
            return 1;
        }
        printf("libelles secondaires : %s — SCENE RECONSTRUITE\n",
               dn_widget_titre_suit() ? "SUIVENT le titre" : "restent en dn_font_14");
        printf("  police effective des libelles : dn_font_%s (line_height %d)\n",
               dn_widget_police_nom(dn_widget_font_libelle()),
               (int)lv_font_get_line_height(dn_widget_font_libelle()));
        /* 🔴 REVUE DU 2026-08-30 — DEUX NOUVELLES PORTES VERS UN DANGER QUE
         *    CE MEME COMMIT NOMME AILLEURS. Le frere `widget date` a ete
         *    concu pour NE PAS reconstruire et IMPRIME pourquoi ; ces deux
         *    commandes-ci reconstruisent et ne disaient rien. Meme
         *    avertissement que `widget couleur`, ⛔ pas un refus : le mode
         *    n'est pas interrogeable d'ici, et refuser a l'aveugle
         *    bloquerait un reglage legitime en mode ACTIF. */
        printf("⛔ SI LA CARTE EST EN VEILLE : `veille off` D'ABORD. Une scene\n");
        printf("   reconstruite en Ambient pose la jauge 27 px TROP HAUT, et\n");
        printf("   AUCUN compteur ne le dit (ledger, 2026-08-29).\n");
        return 0;
    }

    if (argc == 3 && strcmp(argv[1], "date") == 0) {
        const lv_font_t *f = dn_widget_police_par_nom(argv[2]);
        if (!f && strcmp(argv[2], "defaut") != 0) {
            printf("usage : widget date <police>|defaut\n");
            printf("  actuelle : dn_font_%s (line_height %d)\n",
                   dn_widget_police_nom(dn_ui_barre_date_font()),
                   (int)lv_font_get_line_height(dn_ui_barre_date_font()));
            polices_imprimer();
            printf("⛔ Police de VEILLE REFUSEE : la date porte « AOUT »,\n");
            printf("   « DEC. » et « FEVR. » — le E sauterait sans un mot.\n");
            return 1;
        }
        esp_err_t e = dn_ui_set_barre_date_font(f);
        if (e != ESP_OK) {
            printf("refuse (%s) — RIEN n'a change\n", esp_err_to_name(e));
            return 1;
        }
        const lv_font_t *pose = dn_ui_barre_date_font(); /* ⛔ RELU */
        int date_x = 0, date_utile = 0;
        dn_ui_barre_slots(NULL, &date_x, &date_utile);
        printf("police de la DATE : dn_font_%s (line_height %d)\n",
               dn_widget_police_nom(pose), (int)lv_font_get_line_height(pose));
        printf("⛔ PAS de reconstruction de scene — le label est repeint en\n");
        printf("   place. (Une reconstruction PENDANT la veille poserait la\n");
        printf("   jauge 27 px trop haut, et aucune garde ne le voit.)\n");
        printf("slot : x = %d, %d px utiles. Verdict sur les pires cas :\n",
               date_x, date_utile);
        {
            /* ⛔ RELUE, jamais recitee. (Revue du 2026-08-30 : c'etait un
             * tableau `k[2]` dont la seconde case n'etait JAMAIS lue.) */
            const char *non_pose = dn_ui_date_inconnue();
            /* Le pire cas REEL est BALAYE, ⛔ pas suppose — MEME fabrique que
             * `widget largeur mur`, desormais partagee. */
            char pire[24] = "";
            int n_formes = 0;
            int pire_w = date_pire_cas(pose, pire, sizeof(pire), &n_formes);
            int w0 = dn_widget_largeur(non_pose, pose);
            printf("  pire DATE reelle   « %s » %d px  (%d formes)  %s\n", pire,
                   pire_w, n_formes,
                   pire_w <= date_utile ? "TIENT" : "🔴 NE TIENT PAS");
            printf("  pire cas du SLOT   « %s » %d px  %s\n", non_pose, w0,
                   w0 <= date_utile ? "TIENT"
                                    : "🔴 NE TIENT PAS — etat de BOOT et de coupure RTC");
            /* 🔴 REVUE DU 2026-08-30 — LA HAUTEUR N'ETAIT MESUREE NULLE PART.
             *    Cette commande n'imprimait que le verdict HORIZONTAL pendant
             *    que `widget date 28` posait une boite 28..63 dans une barre de
             *    60. Le plancher est desormais RELU, et il est REFUSE avant
             *    d'arriver ici — on l'imprime pour que le refus soit lisible. */
            /* 🔴 dn4-24 / AC2.1 — LE PLANCHER PEUT ETRE INDISPONIBLE depuis
             *    qu'il se relit SOUS LE VERROU LVGL. ⛔ Ne pas imprimer la
             *    sentinelle comme si c'etait une hauteur : « plancher =
             *    2147483647 px » serait un nombre FAUX presente comme une
             *    mesure, et ce depot en solde deja une famille. */
            int plancher = dn_ui_barre_plancher();
            if (plancher == DN_UI_BARRE_PLANCHER_INDISPONIBLE) {
                printf("  hauteur : boite 28..%d, plancher de barre "
                       "🔴 INDISPONIBLE (verrou LVGL non obtenu)\n",
                       28 + (int)lv_font_get_line_height(pose));
            } else {
                printf("  hauteur : boite 28..%d, plancher de barre RELU = %d px\n",
                       28 + (int)lv_font_get_line_height(pose), plancher);
            }
        }
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
            /* 🔴 REVUE DE CODE DU 2026-08-31 — CE MESSAGE RECITAIT « 53 »
             *    EN DUR EN L'ANNONCANT « RELU ». `dn4-14-2` avait retire ce
             *    meme 53 du validateur parce qu'il MENTAIT : le plancher MONTE
             *    des que `widget date` pose une police plus haute (jusqu'a 63).
             *    Le nombre ecrit avait survecu ICI, dans le seul endroit que
             *    l'operateur LIT. ⛔ Un nombre ecrit presente comme une mesure :
             *    la famille exacte pour laquelle l'ecart 3 a ete ouvert. */
            int plancher_b = dn_ui_barre_plancher();
            if (plancher_b == DN_UI_BARRE_PLANCHER_INDISPONIBLE) {
                printf("⚠️ Bornes du contenu : barre >= 🔴 INDISPONIBLE (verrou\n");
                printf("   LVGL non obtenu), menu >= 49 (dn_font_28 a y=14) ou 0.\n");
            } else {
                printf("⚠️ Bornes RELUES du contenu : barre >= %d (heure dn_font_28\n",
                       plancher_b);
                printf("   a y=18 ; la date MONTE ce plancher selon SA police),\n");
                printf("   menu >= 49 (dn_font_28 a y=14) ou 0.\n");
            }
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
        /* dn4-15 / AC5 — MEME TRAITEMENT, MEME RENVOI QUE `widget voie b`.
         * Cette sortie citait la bande `VENTILOS` de dn3-2 et la bande de
         * jauge `RAM` de dn4-1 : l'AVERTISSEMENT etait juste, les DEUX
         * NOMBRES etaient morts. ⛔ Ils ne sont pas recopies ici.
         * ⛔ On ne leur substitue AUCUNE autre valeur (⛔ pas `337..347`) :
         *    une coordonnee que rien ne confronte finit par etre recitee. */
        printf("🔴 TOUTE COORDONNEE TACTILE PUBLIEE EST DESORMAIS PERIMEE.\n");
        printf("   ⛔ AUCUN NOMBRE N'EST DONNE ICI, ET C'EST VOULU : la seule\n");
        printf("     valeur qui fasse foi se RELIT — `widget jauge [<case>]`\n");
        printf("     rend le rectangle REEL pose par LVGL (dn4-4/AC9).\n");
        printf("   ⇒ MESURER avec lui, PUIS controler la formule, AVANT de\n");
        printf("     faire viser quoi que ce soit (AC11).\n");
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
    /*
     * ════════════════════════════════════════════════════════════════════════
     * dn4-14-2 / AC2 — LE MUR HORIZONTAL, MESURÉ DANS CHAQUE POLICE LIÉE
     * ════════════════════════════════════════════════════════════════════════
     * 🔴 CE QUE `widget largeur` NE POUVAIT PAS FAIRE, ET POURQUOI ÇA COMPTE.
     *    Il mesurait TOUT dans `g.font_val` (28 px, la police des VALEURS). Or
     *    les deux murs de dn4-14-2 sont ailleurs : la DATE de barre est en
     *    `dn_font_14`, le TITRE de case aussi. L'instrument ne pouvait donc
     *    VOIR ni l'un ni l'autre — il répondait juste, à une autre question.
     * 🔴 ET LES BUDGETS SONT RELUS, ⛔ PAS ÉCRITS ICI. `dn_ui_barre_slots()` et
     *    `dn_widget_titre_utile()` les calculent depuis les MÊMES symboles que
     *    le rendu pose. Un verdict « tient » contre un budget récité dans ce
     *    `printf` survivrait à un déplacement du slot sans broncher.
     * ⚠️ « Rien n'a planté » n'est PAS « ça tient » : LVGL clippe au parent
     *    SANS UN MOT. C'est pour ça que ce tableau existe.
     */
    if (argc == 3 && strcmp(argv[1], "largeur") == 0 &&
        strcmp(argv[2], "mur") == 0) {
        int heure_x = 0, date_x = 0, date_utile = 0;
        dn_ui_barre_slots(&heure_x, &date_x, &date_utile);
        int cw = 0;
        dn_ui_case_dim(&cw, NULL);
        int titre_x = dn_widget_titre_x(true);
        int titre_utile = dn_widget_titre_utile(cw, true);
        int heure_utile = date_x - heure_x;

        printf("SLOTS RELUS DU RENDU — ⛔ aucun de ces nombres n'est ecrit ici :\n");
        printf("  DATE de barre  x = %d  utile = %d px  (dalle %d - x - marge)\n",
               date_x, date_utile, (int)DN_LCD_H_RES);
        printf("  HEURE de barre x = %d  utile = %d px  (jusqu'a la date)\n",
               heure_x, heure_utile);
        printf("  TITRE de case  x = %d  utile = %d px  (case %d, badge a %d)\n",
               titre_x, titre_utile, cw, titre_x + titre_utile);
        printf("\n");
        polices_imprimer();

        /* Les chaînes NOMMÉES d'AC2.2. ⚠️ Les deux premières ne sont PAS
         * recopiées : elles viennent du `#define` qui sert d'initialiseur au
         * composeur. La maquette normative, elle, EST une citation de
         * l'addendum §1 — et c'est légitime : c'est un document, pas un état. */
        struct {
            const char *quoi;
            const char *txt;   /* NULL quand `balaye` : le texte varie par police */
            int budget;
            int balaye;        /* 0 = texte fixe · 1 = cases reelles · 2 = + demo */
        } k_mur[] = {
            {"DATE  pire cas du SLOT (boot)", dn_ui_date_inconnue(), date_utile, 0},
            {"DATE  maquette (addendum §1)", "VEN. 06 AO\xC3\x9B""T", date_utile, 0},
            {"HEURE sans secondes", "01:17", heure_utile, 0},
            {"HEURE avec secondes", "01:17:33", heure_utile, 0},
            {"HEURE non posee", dn_ui_heure_inconnue(), heure_utile, 0},
            /*
             * 🔴 REVUE DU 2026-08-30 — LES DEUX LIGNES DE TITRE RECITAIENT LEUR
             *    TEXTE. Elles etaient ecrites `"AMBIANCE"` et `"DEMO 2+JAUGE"`
             *    en litteraux, dans un bloc dont le commentaire d'a cote dit
             *    qu'un instrument qui recite cesse de mesurer au premier
             *    renommage. ⇒ Les deux sont RELUES de `dn_ui_case_titre()`.
             * 🔴 ET LE « BALAYE » CHOISISSAIT SON GAGNANT DANS `&dn_font_14`
             *    ECRIT EN DUR, puis l'imprimait sous CHAQUE colonne de police —
             *    dans un instrument dont la premisse est justement que « le plus
             *    long » et « le plus large » sont deux questions. ⇒ Le gagnant
             *    est desormais cherche COLONNE PAR COLONNE, dans la police de
             *    la colonne.
             */
            {"TITRE le plus large — cases REELLES", NULL, titre_utile, 1},
            {"TITRE le plus large — DEMO incluse", NULL, titre_utile, 2},
        };

        printf("\nCHAINES NOMMEES x POLICES D'INTERFACE — px, et le verdict :\n");
        printf("  %-33s %-18s", "quoi", "texte");
        for (int p = 0; p < dn_widget_polices_nb(); p++) {
            const char *nom = NULL;
            bool itf = false;
            dn_widget_police_at(p, &nom, NULL, &itf);
            if (itf) {
                printf("%7s", nom);
            }
        }
        printf("   budget\n");
        for (size_t i = 0; i < sizeof(k_mur) / sizeof(k_mur[0]); i++) {
            printf("  ");
            colonnes(k_mur[i].quoi, 33);
            printf(" ");
            colonnes(k_mur[i].txt ? k_mur[i].txt : "(varie par police)", 18);
            for (int p = 0; p < dn_widget_polices_nb(); p++) {
                const lv_font_t *f = NULL;
                bool itf = false;
                dn_widget_police_at(p, NULL, &f, &itf);
                if (!itf) {
                    continue;
                }
                int w;
                if (k_mur[i].balaye) {
                    /* ⛔ LE GAGNANT SE CHERCHE DANS LA POLICE DE LA COLONNE.
                     * `<` s'arrete aux six cases REELLES, `<=` prend la DEMO. */
                    int borne = (k_mur[i].balaye == 2) ? DN_UI_METRIQUES
                                                       : DN_UI_METRIQUES - 1;
                    w = 0;
                    for (int c = 0; c <= borne; c++) {
                        const char *t = dn_ui_case_titre(c);
                        if (!t) {
                            continue;
                        }
                        int wc = dn_widget_largeur(t, f);
                        if (wc > w) {
                            w = wc;
                        }
                    }
                } else {
                    w = dn_widget_largeur(k_mur[i].txt ? k_mur[i].txt : "", f);
                }
                printf("%5d%s", w, w <= k_mur[i].budget ? "  " : "🔴");
            }
            printf("   %d\n", k_mur[i].budget);
        }
        /* Le NOM du gagnant, police par police — la colonne du tableau ne rend
         * qu'un nombre, et « lequel » est la question qu'on se pose ensuite. */
        printf("  titres gagnants (DEMO incluse), police par police :");
        for (int p = 0; p < dn_widget_polices_nb(); p++) {
            const char *nom = NULL;
            const lv_font_t *f = NULL;
            bool itf = false;
            dn_widget_police_at(p, &nom, &f, &itf);
            if (!itf) {
                continue;
            }
            const char *gagnant = "-";
            int meilleur = -1;
            for (int c = 0; c <= DN_UI_METRIQUES; c++) {
                const char *t = dn_ui_case_titre(c);
                if (!t) {
                    continue;
                }
                int wc = dn_widget_largeur(t, f);
                if (wc > meilleur) {
                    meilleur = wc;
                    gagnant = t;
                }
            }
            printf("  %s = « %s »", nom, gagnant);
        }
        printf("\n");

        /*
         * 🔴 ET LE PIRE CAS DE DATE EST UN RÉSULTAT, ⛔ PAS UNE SUPPOSITION.
         *    « MER. 06 SEPT. » est la plus LONGUE en caractères ; la plus LARGE
         *    en pixels est une autre question, et c'est celle-ci qui décide.
         * ⚠️ **REVUE DU 2026-08-30** : ce bloc écrivait « 7 x 12 x 32 » dans son
         *    commentaire et « 7 jsem x 12 mois x 31 jours » dans sa ligne
         *    imprimée, TROIS LIGNES PLUS BAS — et il balayait des jours qui
         *    n'existent pas dans leur mois. ⇒ Le balayage est une fabrique
         *    PARTAGÉE (`date_pire_cas()`), et le compte est IMPRIMÉ, ⛔ plus
         *    écrit.
         */
        printf("\nPIRE CAS DE DATE — BALAYE, ⛔ pas suppose. Le composeur REEL\n");
        printf("est appele pour chaque forme, la ligne DEGRADEE (« ??? ») incluse :\n");
        for (int p = 0; p < dn_widget_polices_nb(); p++) {
            const char *p_nom = NULL;
            const lv_font_t *p_f = NULL;
            bool p_itf = false;
            dn_widget_police_at(p, &p_nom, &p_f, &p_itf);
            if (!p_itf) {
                continue;
            }
            char pire[24] = "";
            int n = 0;
            int pire_w = date_pire_cas(p_f, pire, sizeof(pire), &n);
            printf("  police %-4s  n = %4d  pire = « %s » %d px   budget %d  %s\n",
                   p_nom, n, pire, pire_w, date_utile,
                   pire_w <= date_utile ? "TIENT" : "🔴 NE TIENT PAS");
        }
        printf("\n⚠️ Un DEPASSEMENT ici ne se verra PAS a l'oeil comme une erreur :\n");
        printf("   LVGL clippe au parent SANS UN MOT. Le verdict est CE tableau.\n");
        printf("⚠️ Le TITRE, lui, ne se fait PAS clipper entre %d et %d px : il\n",
               titre_utile, cw - titre_x);
        printf("   CHEVAUCHE la reserve du badge « SIMULE », visible seulement\n");
        printf("   si la case est SIMULEE. Au-dela, c'est un vrai clip de zone.\n");
        return 0;
    }

    /*
     * dn4-14-2 / AC2.1 — UNE CHAÎNE, DANS UNE POLICE NOMMÉE.
     * ⚠️ `reset` et `mur` sont REFUSÉS comme texte : ils sont interceptés plus
     *    haut à `argc == 3`, et les laisser passer ici mesurerait la largeur du
     *    mot « reset » — une commande qui a l'air de marcher et ne fait pas ce
     *    qu'on croit. Le dépôt a déjà payé exactement ce piège.
     */
    if (argc == 4 && strcmp(argv[1], "largeur") == 0) {
        if (strcmp(argv[2], "reset") == 0 || strcmp(argv[2], "mur") == 0) {
            printf("refuse : « %s » est une SOUS-COMMANDE, pas un texte.\n",
                   argv[2]);
            printf("  `widget largeur %s` (sans 3e mot) fait ce que vous voulez ;\n",
                   argv[2]);
            printf("  pour mesurer le MOT « %s », passez-le autrement.\n", argv[2]);
            return 1;
        }
        const lv_font_t *pf = dn_widget_police_par_nom(argv[3]);
        if (!pf) {
            printf("police « %s » inconnue.\n", argv[3]);
            polices_imprimer();
            return 1;
        }
        bool itf = dn_widget_police_interface(pf);
        int w = dn_widget_largeur(argv[2], pf);
        printf("« %s » = %d px   dans dn_font_%s (line_height %d)%s\n", argv[2],
               w, dn_widget_police_nom(pf), (int)lv_font_get_line_height(pf),
               itf ? "" : "   ⚠️ POLICE DE VEILLE");
        if (!itf) {
            printf("⛔ PLAGE REDUITE : ni accent, ni puce, ni symbole. Un glyphe\n");
            printf("   absent est LARGE DE ZERO et n'est PAS dessine — la mesure\n");
            printf("   ci-dessus est donc VRAIE et le rendu serait MUTILE.\n");
        }
        largeur_drapeau_repl(argv[2]); /* dn4-23/AC5.3 — le jeton PARTIEL */
        return 0;
    }

    if (argc == 3 && strcmp(argv[1], "largeur") == 0 &&
        strcmp(argv[2], "reset") == 0) {
        /* ⚠️ AVANT la mesure d'une chaine libre : sinon « reset » serait MESURE
         *    comme un texte et le compteur ne bougerait jamais — une commande
         *    qui a l'air de marcher et ne fait rien. */
        dn_widget_chevauchements_reset();
        dn_widget_debordements_reset();
        dn_widget_trop_larges_reset();
        /* 🔴 REVUE DU 2026-08-30 — LE 4e COMPTEUR. Le clip ACCEPTE de la date de
         *    barre n'avait AUCUN instrument : `widget largeur reset` puis
         *    `widget` rendait « 0 trop-large(s) » pendant que « HEURE NON POSEE »
         *    (184 px pour 170) etait clippee a l'ecran. ⛔ Compteur SEPARE : les
         *    trois autres comptent des textes de CASE. */
        dn_ui_barre_date_trop_large_reset();
        printf("compteurs remis a 0 : chevauchement (cote a cote), debordement\n");
        printf("(hauteur), trop-large (colonne unique — le trou que le cote a\n");
        printf("cote cachait, revue 2026-08-19) ET date de barre trop large\n");
        printf("(le clip ACCEPTE de l'etat NON POSE, revue 2026-08-30)\n");
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
            /*
             * 🔴 dn4-14-2 — LA GARDE DU JETON AVALE, ET ELLE VIENT D'UNE MESURE.
             *    Le REPL SUPPRIME tout octet >= 0x80 (mesure du 2026-08-29 :
             *    « AEB » rend 21 px comme « AB », « °C » rend « C »). Un jeton
             *    fait UNIQUEMENT d'accents devient VIDE et DISPARAIT : `argc`
             *    tombe de 4 a 3, les arguments se decalent, et
             *    `widget largeur <accents> 14` mesure LE MOT « 14 » — une
             *    reponse juste a une autre question, sans un mot.
             * ⇒ Si le seul argument restant EST un nom de police, on le DIT.
             *   ⛔ On ne refuse pas : mesurer la chaine « 14 » est une question
             *     legitime. On enleve juste l'ambiguite.
             */
            if (dn_widget_police_par_nom(argv[2])) {
                printf("⚠️ « %s » est AUSSI un nom de police. Si vous vouliez\n",
                       argv[2]);
                printf("   `widget largeur <texte> %s` avec un texte ACCENTUE :\n",
                       argv[2]);
                printf("   LE REPL A AVALE LE TEXTE (il supprime tout octet\n");
                printf("   >= 0x80). ⇒ pour les chaines accentuees, utiliser\n");
                printf("   `widget largeur mur`, dont les chaines sont COMPILEES.\n");
            }
            largeur_drapeau_repl(argv[2]); /* dn4-23/AC5.3 — le jeton PARTIEL */
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
        /* 🔴 dn4-23 / AC6.1 — CETTE COMMANDE ETAIT LA SEULE DES QUATRE A
         *    RECONSTRUIRE **ET** A TOUCHER LA JAUGE **SANS** AVERTIR. Ses trois
         *    voisines (`widget titre`, `widget titre suit`, `widget couleur`)
         *    impriment ce bloc depuis dn4-14. C'est PRECISEMENT le geste de
         *    l'A/B du 2026-08-30 : tapee en veille, elle reconstruit et decale
         *    la jauge de 27 px sans un mot. */
        printf("⛔ SI LA CARTE EST EN VEILLE : `veille off` D'ABORD. Une scene\n");
        printf("   reconstruite en Ambient pose la jauge 27 px TROP HAUT, et\n");
        printf("   AUCUN compteur ne le dit (ledger, 2026-08-29).\n");
        /* 🔴 dn4-23 / AC6.1 — LE RENVOI ETAIT MORT. Il designait `dn3-3`,
         *    `done` depuis le 2026-08-25, qui n'a JAMAIS rejoue cet arbitrage.
         *    Le porteur VIVANT de la passe de palette est `dn4-29` (backlog au
         *    tracker, statut VERIFIE avant d'ecrire cette cle — c'est le defaut
         *    meme que cette story repare, le commettre ici serait une faute de
         *    famille). */
        printf("⛔ CECI N'EST PAS LA PASSE DE PALETTE : son porteur vivant est\n");
        printf("   `dn4-29`, et elle s'arbitre A L'OEIL, PAR L'OWNER.\n");
        verdict_contraste(); /* dn4-23/AC6.2 — la piste vient de bouger */
        return 0;
    }
    if (argc == 4 && strcmp(argv[1], "couleur") == 0) {
        char *fin = NULL;
        long idx = strtol(argv[2], &fin, 0);
        bool ok_idx = (fin != argv[2] && *fin == '\0' && idx >= 0 &&
                       idx < DN_UI_METRIQUES);
        long v = strtol(argv[3], &fin, 0);   /* accepte 0x… et le decimal */
        /* ⚠️ `fin == argv[i]` : la CHAINE VIDE passe sinon — `strtol` renseigne
         *    TOUJOURS `endptr`, et pour "" il vaut nptr avec `*fin == '\0'`.
         *    C'est la convention du fichier (`:94`, `:120`, `:2920`), et le
         *    defaut a deja ete commis une fois sur `widget icone`. */
        if (!ok_idx || fin == argv[3] || *fin != '\0' || v < 0 || v > 0xFFFFFF) {
            printf("usage : widget couleur <case 0..%d> <0xRRGGBB>\n",
                   DN_UI_METRIQUES - 1);
            printf("   (0 = RENDRE LA MAIN au descripteur)\n");
            for (int i = 0; i < DN_UI_METRIQUES; i++) {
                uint32_t eff = dn_ui_case_couleur(i);
                const dn_widget_desc_t *b = dn_ui_desc_brut(i);
                /* 🔴 `%-9s` REMPLIT EN OCTETS, ⛔ PAS EN COLONNES — et c'est
                 *    le defaut que `dn_console_banner()` documente, commis a
                 *    nouveau ici et attrape A L'OEIL PAR L'OWNER en seance le
                 *    2026-08-29 : « RESEAU » pese 7 octets pour 6 colonnes,
                 *    donc sa ligne se decalait d'un caractere. Depuis dn3-1
                 *    les libelles sont ACCENTUES : tout `%-Ns` sur un nom de
                 *    metrique est faux. On paie les colonnes a la main. */
                printf("   %d = ", i);
                colonnes(dn_ui_metrique_nom(i), 10);
                printf("0x%06X%s\n", (unsigned)eff,
                       (b && eff != b->couleur) ? "  ⚠️ FORCEE (descr. differe)"
                                                : "");
            }
            printf("⚠️ LA COULEUR D'UNE CASE PEINT TROIS CHOSES : l'accent de la\n");
            printf("   tuile (icone + indicateur de jauge), le CHEVRON de la page\n");
            printf("   de detail, et la SERIE 0 de sa courbe. C'est voulu — une\n");
            printf("   metrique, une couleur, partout.\n");
            printf("⚠️ EN AMBIENT l'icone est MASQUEE : seule LA JAUGE porte\n");
            printf("   encore l'accent, desature. ⇒ juger DANS LES DEUX MODES.\n");
            printf("⛔ AUCUN ETAT LIVRE : au boot le descripteur fait foi.\n");
            return 1;
        }
        esp_err_t err = dn_ui_set_couleur((int)idx, (uint32_t)v);
        if (err == ESP_ERR_TIMEOUT) {
            printf("verrou LVGL non pris — RIEN n'a change (reessayer)\n");
            return 1;
        }
        if (err != ESP_OK) {
            /* ⚠️ REVUE DU 2026-08-29 — `dn_ui_set_couleur()` rend
             *    `ESP_ERR_INVALID_ARG` pour DEUX causes (index hors plage ET
             *    `rgb > 0xFFFFFF`), et ce message n'en nommait qu'une. Masque
             *    aujourd'hui par la pre-validation ci-dessus, il nommerait la
             *    mauvaise cause au premier appel de l'API depuis ailleurs. */
            printf("REFUSE : index hors plage (0..%d) OU couleur > 0xFFFFFF.\n",
                   DN_UI_METRIQUES - 1);
            printf("   usage : widget couleur <case 0..%d> <0xRRGGBB>\n",
                   DN_UI_METRIQUES - 1);
            return 1;
        }
        if (v == 0) {
            printf("couleur de la case %d (%s) = RENDUE AU DESCRIPTEUR "
                   "(0x%06X) — SCENE RECONSTRUITE\n",
                   (int)idx, dn_ui_metrique_nom((int)idx),
                   (unsigned)dn_ui_case_couleur((int)idx));
        } else {
            printf("couleur de la case %d (%s) = 0x%06X — SCENE RECONSTRUITE\n",
                   (int)idx, dn_ui_metrique_nom((int)idx), (unsigned)v);
        }
        /* 🔴 REVUE DU 2026-08-29 — CETTE LIGNE ANNONCAIT TROIS OBJETS SANS
         *    CONDITION, ET DEUX POUVAIENT NE PAS EXISTER.
         *    · le CHEVRON n'est peint que si la case a DEUX series
         *      (`chevron_couleur()` rend 0 sinon) ⇒ RIEN sur CPU/GPU/RAM/DISQUE,
         *      y compris sur `RAM`, la case que la seance du 2026-08-29 a
         *      reellement pilotee ;
         *    · l'ACCENT DE TUILE n'existe pas sur une case rendue NUE.
         *    ⇒ Les deux se DEMANDENT, ⛔ ne se recitent pas. */
        int s0 = -1, s1 = -1;
        bool a_chevron = (dn_hist_series_de_case((int)idx, &s0, &s1) == 2);
        bool est_widget = dn_ui_case_est_widget((int)idx);
        printf("   ⇒ %s%s serie 0 de la courbe.\n",
               est_widget ? "accent de tuile +" : "",
               a_chevron ? " chevron +" : "");
        if (!est_widget) {
            printf("⚠️ CETTE CASE EST RENDUE **NUE** : aucun accent de tuile n'est\n");
            printf("   peint. La couleur est POSEE et servira des que la case\n");
            printf("   redeviendra un widget (`widget nue %d off`).\n", (int)idx);
        }
        if (!a_chevron) {
            printf("⚠️ PAS DE CHEVRON sur cette case : il n'est dessine que sur\n");
            printf("   les cases a DEUX series. ⛔ ne pas le chercher a l'oeil.\n");
        }
        printf("⚠️ la reconstruction a retire le stimulus `anim` et la demo.\n");
        /* ⚠️ dn4-14 / revue : cette commande RECONSTRUIT LA SCENE, et une scene
         *    reconstruite PENDANT LA VEILLE pose la jauge 27 px trop haut
         *    (defaut hors perimetre, verse au ledger le 2026-08-29 — la garde
         *    `dn_widget_controler_tenue()` ne le voit pas, elle teste la
         *    LARGEUR du texte, ⛔ pas la position de la jauge). */
        printf("⛔ SI LA CARTE EST EN VEILLE : `veille off` D'ABORD. Une scene\n");
        printf("   reconstruite en Ambient pose la jauge 27 px TROP HAUT, et\n");
        printf("   AUCUN compteur ne le dit (ledger, 2026-08-29).\n");
        verdict_contraste(); /* dn4-23/AC6.2 — l'accent vient de bouger */
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
            printf("usage : widget icone <case 0..%d> <glyphe -1..%d>\n",
                   DN_UI_METRIQUES - 1, dn_ui_icones_alt_n() - 1);
            printf("   (-1 = RENDRE LA MAIN a l'icone du descripteur)\n");
            /* 🔴 REVUE DU 2026-08-29 — LE MARQUEUR « EN PLACE » EST DERIVE, ⛔
             *    PLUS ECRIT DANS LE LIBELLE. Le rang 0 s'appelait « desktop —
             *    GPU AUJOURD'HUI » ET LE MESSAGE CI-DESSOUS LE REPETAIT, alors
             *    que l'owner avait tranche « on garde gamepad » : `desktop`
             *    etait devenu le candidat REJETE, et `dn_ui_icone_alt(GPU)`
             *    rendait 1. On demande donc a la SOURCE, case par case. */
            for (int i = 0; i < dn_ui_icones_alt_n(); i++) {
                printf("   %d = %s", i, dn_ui_icone_alt_nom(i));
                for (int cse = 0; cse < DN_UI_METRIQUES; cse++) {
                    if (dn_ui_icone_alt(cse) == i) {
                        printf("   ← EN PLACE sur `%s`", dn_ui_metrique_nom(cse));
                    }
                }
                printf("\n");
            }
            /* 🔴 dn4-14 / AC7.3 — LE TEXTE SUIT LA TABLE. Il recitait « les 4
             *    premiers glyphes sont les substituts de `fan`, gardes : les
             *    retirer changerait l'union -r de 68 a 65 — vraie regen ».
             *    Ces quatre candidats ventilateur N'EXISTENT PLUS : la vraie
             *    regeneration a ete payee le 2026-08-29 par le `GPU`, et le
             *    menage est parti avec. Une explication qui survit a ce qu'elle
             *    explique est la meme classe de defaut que le « ? » ci-dessus. */
            printf("⚠️ LA TABLE GARDE `desktop`, L'ANCIENNE ICONE DE `GPU` :\n");
            printf("   un A/B qui ne garde pas de quoi revenir en arriere n'est\n");
            printf("   pas un A/B. ⛔ AUCUN rang n'est « celui en place » par\n");
            printf("   nature : la marque ci-dessus est LUE de l'etat courant.\n");
            printf("⚠️ Une case dont l'icone n'est PAS dans la table (CPU, RAM,\n");
            printf("   RESEAU) n'affiche aucune marque : `-1` l'y ramene.\n");
            printf("⚠️ EN AMBIENT L'ICONE EST MASQUEE (titre + icone + badge).\n");
            printf("   ⇒ juger un glyphe se fait EN MODE ACTIF, sinon on regarde\n");
            printf("     une case ou il n'y a pas d'icone.\n");
            printf("⛔ `microchip` n'est pas candidat : il est deja `CPU`, et un\n");
            printf("   doublon rendrait les deux cases confusibles au coup d'oeil.\n");
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
            printf("index hors plage : widget icone <case 0..%d> "
                   "<glyphe -1..%d>\n",
                   DN_UI_METRIQUES - 1, dn_ui_icones_alt_n() - 1);
            return 1;
        }
        if (n < 0) {
            printf("icone de la case %d (%s) = RENDUE AU DESCRIPTEUR "
                   "— SCENE RECONSTRUITE\n",
                   (int)idx, dn_ui_metrique_nom((int)idx));
        } else {
            printf("icone de la case %d (%s) = %s — SCENE RECONSTRUITE\n",
                   (int)idx, dn_ui_metrique_nom((int)idx),
                   dn_ui_icone_alt_nom((int)n));
        }
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
        /* 🔴 dn4-23 / AC5.2 — L'AIRE EST **RELUE**, ⛔ PLUS RECITEE. Ce message
         *    envoyait chercher « 6 x 35 100 px » sur une aire livree de
         *    36 675 : un operateur qui suivait la consigne concluait que sa
         *    mesure etait FAUSSE alors qu'elle etait JUSTE.
         * ⛔ ET 36 675 N'EST PAS DAVANTAGE ECRIVABLE : `ui_case_h()` depend de
         *   `s_geo_barre_h`/`s_geo_menu_h`, REGLABLES A CHAUD (`widget bandes`).
         *   L'aire n'est pas une constante — elle se DEMANDE. Le patron existe
         *   deja dans ce fichier : `surface d'une case : %d px (etait 35 100 a
         *   156)`. */
        int cw_r = 0, ch_r = 0;
        dn_ui_case_dim(&cw_r, &ch_r);
        printf("⛔ CETTE COMMANDE NE CONCLUT PAS SEULE. Pour prouver la fusion :\n");
        printf("   `flush` AVANT et APRES ce tir — la fusion est demontree si le\n");
        printf("   delta vaut %u flushes pour UN SEUL cycle (et %u x %d px,\n",
               (unsigned)n, (unsigned)n, cw_r * ch_r);
        printf("   l'aire d'une case RELUE — etait 35 100 a 156).\n");
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
        /* 🔴 dn4-23 / AC5.2 — LE DENOMINATEUR ETAIT PERIME, ET LE POURCENTAGE
         *    AVEC. « 18 %% d'une case (35 100 px) » : sur l'aire LIVREE le
         *    rapport vaut 17,3 %%. L'entree de ledger `l.2847` n'accusait que
         *    `widget rafale` — une gate scopee a UNE fonction epingle vert le
         *    meme defaut ailleurs, et c'est EXACTEMENT ce qui s'est passe ici.
         * ⇒ aire RELUE, pourcentage CALCULE. ⛔ Aucune constante de geometrie
         *   dans une consigne D'ACTION. */
        int cw_b = 0, ch_b = 0;
        dn_ui_case_dim(&cw_b, &ch_b);
        int aire_b = cw_b * ch_b;
        int pmille = aire_b > 0
                         ? (int)((6334LL * 1000 + aire_b / 2) / aire_b)
                         : 0;
        printf("🔴 MESURE (§16.5) : la barre coute 6 334 px par mise a jour,\n");
        printf("   soit %d,%d %% d'une case (%d px, aire RELUE — etait 35 100 a\n",
               pmille / 10, pmille % 10, aire_b);
        printf("   156) — ⛔ PAS les 33 600 px que son rectangle 480 x 70\n");
        printf("   laisse croire. LVGL n'invalide que la zone\n");
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
        verdict_contraste(); /* dn4-23/AC6.2 — l'aplat vient de bouger */
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
        printf("        | police <taille>                       ⚠️ RECONSTRUIT\n");
        printf("        | grille <barre> <menu>                 ⚠️ RECONSTRUIT\n");
        printf("      dn4-14-2 — les DEUX A/B de police de TEXTE :\n");
        printf("        | titre [<police>|defaut]               ⚠️ RECONSTRUIT\n");
        printf("        | titre suit on|off                     ⚠️ RECONSTRUIT\n");
        printf("        | date  [<police>|defaut]   (⛔ ne reconstruit PAS)\n");
        printf("      dn4-6 — les instruments (ne reconstruisent PAS) :\n");
        printf("        | largeur [<texte> [<police>]|mur|reset] | detail\n"
               "        | replacer on|off\n"
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
        /* 🔴 dn3-3 : LA GEOMETRIE **APPLIQUEE**, ⛔ PLUS L'OVERRIDE.
         *    Jusqu'au 2026-08-25 cette ligne imprimait `val_y 48 · val_pas 40`
         *    PENDANT que la veille appliquait 26 / 47 — une etiquette qui ment,
         *    trouvee en preparant la fenetre d'observation de l'owner.
         * ⛔ `dn_widget_geom_appliquee()` est en LECTURE SEULE : ne jamais la
         *    repasser a `dn_widget_set_geom()`, elle graverait les valeurs
         *    d'Ambient comme override permanent. */
        dn_widget_geom_t g;
        dn_widget_geom_appliquee(&g);
        int bh = 0, mh = 0, gh = 0, ch = 0;
        dn_ui_geom_bandes(&bh, &mh, &gh, &ch);
        int cw0 = 0;
        dn_ui_case_dim(&cw0, NULL);
        printf("geometrie    : barre %d · menu %d · grille %d · case %dx%d\n", bh,
               mh, gh, cw0, ch);
        printf("               val_y %d · val_pas %d (interligne %d px) · %s · %s"
               "%s\n",
               g.val_y, g.val_pas, g.val_pas - (int)lv_font_get_line_height(g.font_val),
               dn_widget_dispo_nom(g.dispo), dn_widget_entete_nom(g.entete),
               dn_veille_mode() == DN_VEILLE_AMBIENT
                   ? "  ⚠️ VALEURS D'AMBIENT (police de veille)" : "");
        /* ⚠️ HAUTEUR DE LIGNE, ⛔ pas « taille de police » : `dn_font_33` a une
         *    line height de 36. Confondre les deux ferait chercher une police
         *    « 36 px » qui n'existe pas. */
        printf("               valeur : interligne %d px%s\n",
               (int)lv_font_get_line_height(g.font_val),
               dn_veille_mode() == DN_VEILLE_AMBIENT
                   ? (dn_widget_amb_unite() ? " (veille, AVEC unite)"
                                            : " (veille, SANS unite)")
                   : " (actif)");
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
        printf("icone DISQUE : %s\n",
               dn_ui_icone_alt_nom(dn_ui_icone_alt(i_disque)));
        /* 🔴 dn4-14 / AC7.2 — CE MESSAGE ETAIT FAUX, ET IL L'ETAIT DEJA AVANT
         *    CETTE STORY. Il ecrivait « « ? » = celle du descripteur, non
         *    commutee » — or `save` EST une entree de `k_icones_alt[]`, donc
         *    l'icone du descripteur de DISQUE se RETROUVE dans la table et rend
         *    son nom, jamais « ? ». `?` ne peut donc PAS vouloir dire « non
         *    commutee » : il veut dire que LA CORRESPONDANCE A ECHOUE, c.-a-d.
         *    que le glyphe pose ne figure dans AUCUN candidat. Le message dit
         *    desormais ce que le symptome VEUT DIRE. */
        printf("               (« ? » = le glyphe pose ne figure dans AUCUN\n");
        printf("                candidat de `widget icone` — ⛔ ce n'est PAS\n");
        printf("                « non commutee » : l'icone du descripteur EST\n");
        printf("                dans la table et rend son nom.)\n");
    }

    /* 🔴 REVUE DU 2026-08-29 — LA PAGE D'ETAT NE MONTRAIT AUCUNE TRACE D'UN
     *    OVERRIDE DE COULEUR. `widget couleur` est conserve au produit (AC5.5)
     *    « pour rejouer l'arbitrage sans reflasher » — mais le SEUL moyen de
     *    savoir quelles cases etaient forcees etait de TAPER LA COMMANDE DE
     *    TRAVERS, le listing ne vivant que dans sa branche d'argument invalide.
     *    Un operateur qui reprend une seance lisait donc une page qui pretend
     *    « relire l'etat reel » en omettant l'etat que dn4-14 a ajoute.
     * ⚠️ LE FORCAGE EST DETECTE PAR SA PRESENCE, ⛔ pas en comparant la valeur
     *    effective au descripteur : un override pose EXACTEMENT a la valeur du
     *    descripteur est bien pose, et l'ancien test `eff != d->couleur` le
     *    declarait non force. */
    {
        int forcees = 0;
        for (int i = 0; i < DN_UI_METRIQUES; i++) {
            uint32_t eff = dn_ui_case_couleur(i);
            const dn_widget_desc_t *b = dn_ui_desc_brut(i);
            if (b && eff != b->couleur) {
                if (forcees == 0) {
                    printf("couleurs FORCEES (⛔ aucun etat livre : au boot le "
                           "descripteur fait foi) :\n");
                }
                forcees++;
                printf("   ");
                colonnes(dn_ui_metrique_nom(i), 10);
                printf("0x%06X   (descripteur : 0x%06X)\n",
                       (unsigned)eff, (unsigned)b->couleur);
            }
        }
        if (forcees == 0) {
            printf("couleurs de case : AUCUN override — les six descripteurs "
                   "font foi.\n");
        }
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
    /* 🔴 REVUE DU 2026-08-30 — LE 4e COMPTEUR EST LU ICI AUSSI, sinon
     *    l'instrument qui sert de tableau de bord continuerait a rendre « 0 »
     *    pendant que la date de barre est clippee. ⛔ Il ne s'ADDITIONNE pas aux
     *    trois autres : quatre causes, quatre compteurs. */
    printf("barre      : %u date(s) trop large(s) — le clip ACCEPTE de l'etat "
           "NON POSE (« %s »)\n",
           (unsigned)dn_ui_barre_date_trop_large(), dn_ui_date_inconnue());
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
            /* 🔴 REVUE DU 2026-08-29 — `couleur` MANQUAIT, et c'etait la 13e
             *    entree de retard de cette liste. `widget couleur` ou
             *    `widget couleur 2` (arite fausse) repondaient donc
             *    « sous-commande INCONNUE : "couleur" » — les mots exacts que
             *    le commentaire ci-dessus qualifie de « factuellement faux »,
             *    dix lignes plus haut. ⚠️ Aggravant : le listing des couleurs
             *    par case ne vit QUE dans la branche d'argument invalide. */
            "couleur",
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
        printf("   couleur ·\n");
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
    /* dn4-5/AC6.1 — LE RETARD EST DIT ICI AUSSI, parce que c'est ICI qu'on
     * regarde la valeur. ⛔ La phrase n'est PAS recopiee : elle est rendue par
     * `dn_capteurs.c`, qui la definit une seule fois. */
    printf("  ⚠️ %s\n", dn_capt_retard_txt());
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

/*
 * ─── `gel` — LA CONTRE-EPREUVE DE LA TRIADE (dn4-5 / AC2.2) ──────────────────
 *
 * 🔴 CE QU'ELLE REPOND. Le verdict de cette story est « 0 gel sur 7 jours ». Or
 *    « un uptime de 7 jours ne prouve PAS l'absence de gel » : la tache LVGL
 *    peut etre bloquee pendant que `up` continue d'avancer, et le watchdog de
 *    tache NE REDEMARRE RIEN dans ce build (CONFIG_ESP_TASK_WDT_PANIC non pose).
 *    Le seul instrument qui separe les deux cas est la TRIADE du battement,
 *    parce que ses trois compteurs viennent de sources INDEPENDANTES :
 *      · `up`             tache `app_main`   -> l'application vit
 *      · `vsync`          ISR du panneau RGB -> la DMA balaie la dalle
 *      · `flush`/`cycles` tache LVGL         -> quelque chose est DESSINE
 *    Cette commande PROVOQUE le cas a discriminer et montre l'instrument crier.
 *
 * ⚠️ LA DUREE PAR DEFAUT EST DE 12 s, ET LE CHIFFRE N'EST PAS ARBITRAIRE : il
 *    doit depasser (a) les 10 s du battement, sans quoi aucune ligne `up` ne
 *    sortirait PENDANT le gel et la preuve la plus lisible manquerait, et (b)
 *    les 5 s de CONFIG_ESP_TASK_WDT_TIMEOUT_S, pour que le comportement du
 *    watchdog soit observe lui aussi.
 *
 * ⛔ CE QUE CETTE COMMANDE NE PROUVE PAS : que la carte ne gelera pas. Elle
 *    prouve que SI elle gele, l'instrument le VERRA. C'est tout, et c'est
 *    exactement ce qui manquait.
 */
static int cmd_gel(int argc, char **argv)
{
    uint32_t ms = 12000;
    if (argc >= 2) {
        int v = atoi(argv[1]);
        if (v < 1 || v > 60) {
            printf("gel [secondes] — 1..60, defaut 12 (> battement 10 s ET > "
                   "TWDT 5 s)\n");
            return 1;
        }
        ms = (uint32_t)v * 1000u;
    }
    printf("─── gel PROVOQUE (dn4-5/AC2.2) — LVGL bloquee %lu ms ───\n",
           (unsigned long)ms);
    printf("  ⚠️ REGARDER LE LOG PENDANT LE GEL : la ligne de battement doit\n");
    printf("     continuer de sortir, avec `up` QUI AVANCE et `flush=` FIGE.\n");
    /*
     * 🔴 CE QUE CETTE COMMANDE COUPE, ET QUI N'ETAIT DIT NULLE PART — CONSTAT DE
     *    REVUE DU 2026-08-28. `cmd_gel` s'execute SUR LA TACHE DU REPL, et le
     *    REPL **EST** le transport de la telemetrie : l'agent envoie chaque
     *    trame comme une commande console (`pc $DN,…`). Pendant le gel, la tache
     *    REPL est dans `vTaskDelay()` et NE LIT PLUS LE PORT ; l'anneau RX
     *    USB-Serial/JTAG sature, le peripherique NAK, et le `write()` de l'hote
     *    expire a `write_timeout = 2 s` ⇒ PORT PERDU cote agent, puis
     *    close/open, plusieurs fois pendant un gel de 12 s.
     *    ⇒ TROIS CONSEQUENCES : (a) la contre-epreuve d'AC2.2 INJECTE elle-meme
     *      les evenements de liaison qu'AC2.3 demande de distinguer d'une vraie
     *      panne ; (b) le close/open du port est la sequence dont le depot ecrit
     *      qu'elle REBOOTAIT la carte, sur une story dont le verdict est
     *      « 0 reboot non commande » ; (c) rien ne le disait.
     */
    printf("  🔴 CE GEL COUPE LE FIL, ET C'EST STRUCTUREL : cette commande\n");
    printf("     tourne SUR LA TACHE DU REPL, et le REPL EST le transport de\n");
    printf("     la telemetrie (l'agent envoie `pc $DN,…`). Pendant le gel le\n");
    printf("     port n'est plus lu ⇒ l'agent va voir PORT PERDU puis rouvrir,\n");
    printf("     plusieurs fois. ⛔ Ces evenements sont des ARTEFACTS DE CETTE\n");
    printf("     COMMANDE, ⛔ pas une panne de liaison (AC2.3).\n");
    printf("  ⛔ NE PAS LA JOUER PENDANT LE SOAK : un close/open de port a deja\n");
    printf("     ete vu REBOOTER la carte, et le verdict du soak est « 0 reboot\n");
    printf("     non commande ». La tirer AVANT de demarrer le compteur.\n");
    printf("  ⛔ NI PRES D'UNE ECHEANCE DE VEILLE : le tick LVGL est fige\n");
    printf("     pendant le gel alors que l'inactivite suit l'horloge murale ⇒\n");
    printf("     le releve d'AC3.3 qui suit porte `jugeable` et il MENT. Jeter\n");
    printf("     tout releve AC3.3 pris dans les 60 s qui suivent.\n");
    /*
     * 🔴 LE RELEVE D'AVANT N'EST PLUS PRIS ICI — corrige sur la carte le
     *    2026-08-26. Pris ici, il l'etait HORS DU VERROU : entre lui et la
     *    prise du verrou, la tache LVGL finissait un cycle, et cette commande
     *    publiait `flush +1` sur un gel parfaitement reel, puis REFUSAIT de
     *    conclure. Le refus etait juste ; le defaut etait le sien.
     * ⇒ Les DEUX relevés sont desormais pris dans `dn_ui_geler_ms()`, verrou
     *   en main.
     */
    fflush(stdout);

    dn_ui_gel_pt_t av, ap;
    if (!dn_ui_geler_ms(ms, &av, &ap)) {
        printf("🔴 verrou LVGL NON PRIS en 2 s — ⛔ « pas mesure », PAS « pas de "
               "gel ». Rejouer.\n");
        return 1;
    }
    double dt_s = (double)(ap.us - av.us) / 1000000.0;
    uint32_t d_vs = ap.vsync - av.vsync;
    uint32_t d_fl = ap.st.flushes - av.st.flushes;
    uint32_t d_cy = ap.st.cycles - av.st.cycles;
    printf("  AVANT : mural %lld s · vsync=%lu · flush=%lu cycles=%lu\n",
           (long long)(av.us / 1000000), (unsigned long)av.vsync,
           (unsigned long)av.st.flushes, (unsigned long)av.st.cycles);
    printf("  APRES : mural %lld s · vsync=%lu · flush=%lu cycles=%lu\n",
           (long long)(ap.us / 1000000), (unsigned long)ap.vsync,
           (unsigned long)ap.st.flushes, (unsigned long)ap.st.cycles);
    printf("  ─ Δ sur %.1f s, LES DEUX RELEVES PRIS SOUS LE VERROU ─\n", dt_s);
    printf("    mural  (tache app_main / horloge) : %+.1f s   %s\n", dt_s,
           dt_s > 0.5 ? "✅ VIVANT" : "🔴 FIGE");
    printf("    vsync  (ISR du panneau RGB)       : +%lu      %s "
           "(attendu ~%.0f a 37,40 Hz)\n",
           (unsigned long)d_vs, d_vs > 0 ? "✅ VIVANT" : "🔴 FIGE", dt_s * 37.40);
    printf("    flush  (tache LVGL)               : +%lu      %s\n",
           (unsigned long)d_fl, d_fl == 0 ? "🔴 FIGE (attendu)" : "⚠️ A BOUGE");
    printf("    cycles (tache LVGL)               : +%lu      %s\n",
           (unsigned long)d_cy, d_cy == 0 ? "🔴 FIGE (attendu)" : "⚠️ A BOUGE");
    if (d_fl == 0 && d_cy == 0 && d_vs > 0 && dt_s > 0.5) {
        printf("  ⇒ ✅ L'INSTRUMENT SAIT VOIR UN GEL D'IMAGE SUR UNE APPLICATION\n");
        printf("       VIVANTE. C'est la contre-epreuve d'AC2.2 : l'ecart entre\n");
        printf("       `up`/`vsync` et `flush`/`cycles` EST la signature du gel.\n");
    } else {
        printf("  ⇒ 🔴 LE STIMULUS N'A PAS PRODUIT LA SIGNATURE ATTENDUE. ⛔ Ne\n");
        printf("       PAS conclure « pas de gel » : conclure que CETTE MESURE\n");
        printf("       est a jeter, et chercher pourquoi.\n");
    }
    printf("  ⚠️ CE QUE CE TEMOIN NE MONTRE PAS : `vsync` ne descend PAS jusqu'a\n");
    printf("     l'oeil. Une dalle qui balaie un framebuffer FIGE compte des\n");
    printf("     vsyncs comme une dalle vivante. Le constat owner reste requis.\n");
    printf("────────────────────────────────────────────────────────────\n");
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
        /*
         * 🔴 dn3-3, 2026-08-27 — LE COMPTE EST **RELU DE L'ENUM**, ⛔ PLUS ÉCRIT
         *    EN TOUTES LETTRES.
         *    Cette ligne a annoncé « LES CINQ PISTES » pendant toute la vie de
         *    la SIXIÈME : c'est `dn3-3` elle-même qui a ajouté `DN_W2_CPU_DIX`
         *    sans amender le message. ⚠️ Le reset, lui, a **toujours** couvert
         *    les six — `dn_w2_reset()` fait un `memset` sur des tableaux
         *    dimensionnés `DN_W2_NB` — donc L'INSTRUMENT ÉTAIT JUSTE ET SON
         *    ÉTIQUETTE MENTAIT, ce que ce dépôt traite comme un défaut à part
         *    entière (`dn_widget.h:165`).
         * ⛔ Écrire « SIX » ne ferait que DÉPLACER la date de péremption : une
         *    7ᵉ piste rouvrirait exactement le même trou. Le compte se RELIT.
         *    Trouvé au `grep` de l'angle mort d'AC10.4, ⛔ pas à l'œil.
         */
        printf("accumulateurs W2 remis a zero (LES %d PISTES).\n", (int)DN_W2_NB);
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
    printf("⚠️ echantillonne DANS LE FIRMWARE. 🔴 LA CADENCE EST **PAR PISTE**\n");
    printf("   DEPUIS dn3-3, ⛔ PLUS GLOBALE : les cinq pistes capteurs battent a\n");
    printf("   %d ms, la piste CPU a %d ms. Chaque nom la porte (`@5s`, `@1s`).\n",
           DN_ENV_PERIODE_MS, DN_W2_CADENCE_CPU_MS);
    printf("   ⛔ LA FENETRE D'UNE PISTE VAUT n x SA CADENCE : ⛔ ne pas comparer\n");
    printf("      deux taux de cadences differentes sans le dire.\n");
    printf("   `dn_console.py` PERD DES LIGNES, et un taux calcule sur un\n");
    printf("   echantillonnage qui perd des points est faux d'un biais qu'on\n");
    printf("   ne sait pas borner.\n");
    printf("⛔ Seules les valeurs VALIDES sont echantillonnees : compter une\n");
    printf("   absence comme un changement gonflerait le taux d'un capteur MUET.\n");
    printf("⚠️ `rup` = CHAINES BRISEES (sortie d'Ambient, ou valeur invalide).\n");
    printf("   L'echantillon qui SUIT une rupture n'a pas de predecesseur\n");
    printf("   legitime : les ruptures sont RETIREES DU DENOMINATEUR du taux,\n");
    printf("   qui vaut donc n - 1 - rup. ⛔ Sans ce retrait le biais irait\n");
    printf("   TOUJOURS vers « NE QUALIFIE PAS ».\n");
    printf("🔴 dn3-3 / AC2.1 : la piste CPU n'accumule QU'EN AMBIENT, donc tout\n");
    printf("   echantillon qu'elle porte EST un echantillon d'Ambient — sous\n");
    printf("   agent reel il n'y a plus de console pour delimiter la fenetre.\n");
    printf("   AC2.1 demande 60 s : c'est n >= %d sur cette piste.\n\n",
           (int)(60000 / DN_W2_CADENCE_CPU_MS));

    printf("%-38s %6s %5s %8s %8s %9s %8s %8s  %s\n", "piste", "n", "rup",
           "min", "max", "etendue", "taux %", "sigma", "verdict");
    for (int i = 0; i < DN_W2_NB; i++) {
        dn_w2_t w;
        dn_w2_lire((dn_w2_id_t)i, &w);
        if (w.n == 0) {
            printf("%-38s %6d %5s %8s %8s %9s %8s %8s  %s\n",
                   dn_w2_nom((dn_w2_id_t)i), 0, "-", "-", "-", "-", "-", "-",
                   "AUCUN ECHANTILLON");
            continue;
        }
        int32_t etendue = w.max - w.min;
        /* Taux sur les TRANSITIONS observees, donc n-1 : le premier echantillon
         * n'a pas de precedent auquel se comparer. ⛔ Diviser par n gonflerait
         * les petits echantillons.
         * 🔴 dn3-3 — ET ON RETIRE LES RUPTURES. Une chaine brisee (sortie
         *    d'Ambient, valeur invalide) laisse un echantillon SANS predecesseur
         *    legitime : il n'est ni un changement, ni une transition. Le laisser
         *    au denominateur diluerait le taux, TOUJOURS vers « NE QUALIFIE
         *    PAS » — le meme sens que les deux troncatures corrigees le
         *    2026-08-20. */
        /* 🔴 CORRIGE EN REVUE DE CODE LE 2026-08-28 — ON RETRANCHAIT **UNE
         *    RUPTURE DE TROP** DANS LE CAS NORMAL. `ruptures` est TERMINALE
         *    (`dn_w2_desamorcer`), donc le nombre d'EPISODES vaut
         *    `ruptures + 1` seulement tant que le dernier est ENCORE OUVERT.
         *    Motif complet et temoin chiffre dans `dn_env.h`, champ `amorce`. */
        uint32_t episodes = w.ruptures + (w.amorce ? 1u : 0u);
        uint32_t transitions = (w.n > episodes) ? (w.n - episodes) : 0u;
        uint32_t taux = transitions ? (w.changements * 100u) / transitions : 0u;
        /* ⚠️ UN TAUX > 100 % EST ARITHMETIQUEMENT IMPOSSIBLE : `changements` est
         *    un sous-ensemble des transitions. S'il sort, c'est que la
         *    comptabilite des episodes a decroche — et ⛔ on le DIT plutot que
         *    de publier un nombre qui ne peut pas exister. */
        if (taux > 100u) {
            printf("🔴 « %s » : taux %lu %% — ARITHMETIQUEMENT IMPOSSIBLE "
                   "(changements %lu > transitions %lu).\n",
                   dn_w2_nom((dn_w2_id_t)i), (unsigned long)taux,
                   (unsigned long)w.changements, (unsigned long)transitions);
            printf("   ⛔ Ne rien conclure de ce chiffre : la comptabilite des "
                   "episodes a decroche.\n");
            taux = 100u;
        }
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
        printf("%-38s %6lu %5lu %8ld %8ld %9ld %8lu %4lld,%03lld  %s\n",
               dn_w2_nom((dn_w2_id_t)i), (unsigned long)w.n,
               (unsigned long)w.ruptures, (long)w.min,
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
 *    Le module pese aujourd'hui **5 657 o** : 3 840 (points, 8 x 120 x 4)
 *    + 768 (`s_smin`) + 768 (`s_smax`) + 192 (`s_svu`) + **89** (`s_w`,
 *    `s_ecrits`, `s_pret`, `s_seau_abs`, l'horodatage et les DEUX compteurs de
 *    rattrapage).
 * 🔴 CORRIGE UNE SECONDE FOIS LE 2026-08-25 (revue de code) : ce bloc publiait
 *    **~5 609 o** et un exemple **« index 41 »** pendant que la commande qu'il
 *    documente imprimait `5657 o` et `index … = 89 o`. Le total etait juste, le
 *    LIBELLE etait faux — et aucune des 7 gates ne relit un libelle.
 * 🔴 ~~ET `dn_hist_octets()` NE REND QUE `sizeof(s_pts)` = 3 840 o : ce que cette
 *    commande imprime SOUS-DECLARE le cout de ~1 817 o (~32 %)~~ — **CORRIGE LE
 *    2026-08-25, dn4-13 / AC2.1**. Le bloc est CONSERVE BARRE : il dit pourquoi
 *    tout chiffre de cout publie AVANT cette date vaut 3 840 et pas 5 657, et
 *    c'est ce qui rend le releve d'AC5.6 non comparable au releve d'aujourd'hui.
 * ⚠️ LES TROIS TERMES SONT IMPRIMES SEPAREMENT. Un total seul ne se confronte pas
 *    au `.map` : c'est en voyant « points 3 840 / seaux 1 728 / index 89 » qu'on
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
        printf("     index  s_w + s_ecrits + s_pret + s_seau_abs + horodatage\n");
        printf("            + 2 compteurs de rattrapage = %u o\n", (unsigned)hi);
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

/*
 * ══ dn3-3 : LA FAMILLE `veille` ═════════════════════════════════════════════
 *
 * Elle PILOTE la veille (les deux réglages, les deux bascules) ET elle la
 * MESURE (les deux latences, le délai, les compteurs, la preuve de layout).
 * ⛔ Le dépôt REFUSE et EXPLIQUE, il n'écrête pas en silence : `veille delai 7`
 *    est un refus chiffré, ⛔ jamais un arrondi vers 5.
 */

/* Le recompte de la partition `assets` (AC1.4). ⚠️ RELU des constantes du
 * firmware, ⛔ pas recopié depuis la story : un chiffre récité ne se confronte
 * à rien. */
#define VEILLE_ASSETS_PART_O 0x100000u /* partitions.csv : `assets`, 1 MiB */

static void veille_usage(void)
{
    printf("usage : veille                       etat, compteurs, diagnostics\n");
    printf("        veille on | off              ARME / DESARME (persiste en NVS)\n");
    printf("        veille delai <1|3|5|10>      le delai, en MINUTES (persiste)\n");
    printf("        veille now                   bascule en Ambient MAINTENANT\n");
    printf("        veille wake                  reveille MAINTENANT (origine console)\n");
    printf("        veille lat                   les DEUX latences de reveil (AC4)\n");
    printf("        veille geom                  la preuve que le layout NE BOUGE PAS\n");
    printf("        veille assets                le recompte de la partition (AC1.4)\n");
    printf("        veille fond                  voiles et aplats RELUS DES OBJETS LVGL\n");
    printf("        veille reset                 compteurs ET latences a zero\n");
    printf("  --- leviers A/B, a chaud, ⛔ NON persistes (ce sont des instruments) ---\n");
    printf("        veille pct <%d..%d>           niveau d'Ambient de DERNIER RECOURS\n",
           DN_VEILLE_PCT_MIN, DN_VEILLE_PCT_MAX);
    printf("        veille voile <0..255>        opacite du voile en Ambient\n");
    printf("        veille gris <reel|simule|absent> <rrggbb>\n");
    printf("        veille accents <0..100>      desaturation des accents (0=teinte, 100=gris)\n");
    printf("        veille unite on|off          l'unite reste-t-elle ? ⚠️ CHOISIT LA POLICE\n");
    printf("                                     (on ⇒ 33 px · off ⇒ 56 px, tailles MESUREES)\n");
    printf("        veille jauge on|off          la barre de remplissage en veille\n");
    printf("        veille case <rrggbb>         l'aplat de case en Ambient\n");
    printf("⚠️ La ligne de resume de `help` a OMIS `fond`, `unite`, `jauge` et\n");
    printf("   `case` jusqu'au 2026-08-28 — corrige. `veille fond` est l'outil de\n");
    printf("   bissection qui a tranche le constat owner « au lieu d'un noir/gris\n");
    printf("   sombre c'est un vert » : il etait invisible pour qui part de `help`.\n");
}

static void veille_imprimer_etat(void)
{
    dn_veille_compteurs_t c;
    if (!dn_ui_veille_compteurs(&c)) {
        /* 🔴 « PAS MESURE », ⛔ JAMAIS « ZERO ». Ces champs sont ecrits par la
         *    tache LVGL ; imprimer des zeros sur un verrou non pris ferait
         *    publier « 0 bascule » pour « on n'a pas pu lire ». */
        printf("⛔ PAS MESURE : le verrou LVGL n'a pas ete pris en 500 ms.\n");
        printf("   ⛔ Ne rien conclure de cette absence — ce n'est PAS « zero ».\n");
        return;
    }

    /*
     * 🔴 REVUE DE CODE DU 2026-08-28 — TOUT CE BLOC LISAIT `dn_veille` **HORS
     *    VERROU**, EN SEPT APPELS SEPARES. Le scenario chiffre est dans
     *    `dn_veille.h` : une bascule qui tombe pendant l'impression faisait
     *    imprimer l'ecart de la bascule A avec le delai de la bascule B, donc un
     *    « 🔴 HORS » sur un comportement CORRECT — le defaut meme que
     *    `s_inact_bascule_delai_ms` avait ferme cote CONTENU, rouvert cote
     *    LECTURE. ⇒ UN SEUL SNAPSHOT, sous le verrou LVGL.
     */
    dn_veille_diag_t dg;
    if (!dn_ui_veille_diag(&dg)) {
        printf("⛔ PAS MESURE : le verrou LVGL n'a pas ete pris en 500 ms pour "
               "le bloc de DIAGNOSTIC.\n");
        printf("   ⛔ Ne rien conclure de cette absence — ce n'est PAS « zero ».\n");
        return;
    }

    printf("mode : %s · veille %s · delai %d min (%lu ms)\n",
           dn_veille_mode_nom(c.mode), c.armee ? "ARMEE" : "DESARMEE",
           dn_veille_cran_min(c.cran), (unsigned long)c.delai_ms);
    printf("inactivite : %lu ms (max vue depuis le reset : %lu ms)\n",
           (unsigned long)c.inactivite_ms, (unsigned long)c.inactivite_max_ms);
    printf("bascules -> Ambient : %lu · reveils : %lu · dernier reveil par : %s\n",
           (unsigned long)c.bascules, (unsigned long)c.reveils,
           dn_veille_origine_nom(c.origine));
    printf("secondes OBSERVEES : %lu (⚠️ ⛔ PAS l'uptime : le tick 1 Hz ne bat\n",
           (unsigned long)c.secondes_vues);
    printf("   pas pendant `ui off`, donc la veille y est AVEUGLE)\n");
    /*
     * ─── dn4-5 / AC3.2 : LE SEUIL « EN AMBIANT LA MAJORITE DU TEMPS » ───────
     *
     * 🔴 Le brief exige « en Ambient la majorite du temps » : **> 50 %** est un
     *    SEUIL, ⛔ pas une figure de style, et il n'avait AUCUN instrument.
     * ⛔ CE CUMUL NE COMPTE PAS DES TICKS. La ligne juste au-dessus dit
     *    elle-meme que le tick 1 Hz ne bat pas pendant `ui off` : un
     *    denominateur en ticks aurait des TROUS et rendrait, sur 7 jours, un
     *    pourcentage plausible et faux. On cumule du TEMPS MURAL, canalise par
     *    l'unique poseur de mode de dn_veille.c.
     */
    {
        int64_t ua = 0, ub = 0;
        dn_veille_cumul(&ua, &ub);
        int64_t tot = ua + ub;
        printf("─── temps MURAL par mode depuis le boot (dn4-5/AC3.2) ───\n");
        printf("  Actif   : %8lld s\n", (long long)(ua / 1000000));
        printf("  Ambient : %8lld s\n", (long long)(ub / 1000000));
        if (tot > 0) {
            /* Le pourcentage est calcule ICI, sur le total RELU — ⛔ jamais
             * recite d'une valeur rangee ailleurs. */
            int pct = (int)((ub * 100) / tot);
            printf("  total   : %8lld s  ⇒ Ambient = %d %%  %s\n",
                   (long long)(tot / 1000000), pct,
                   pct > 50 ? "✅ MAJORITE (seuil > 50 %)"
                            : "🔴 SOUS LE SEUIL de 50 %");
        } else {
            printf("  ⛔ aucun temps cumule — rien a conclure.\n");
        }
        printf("  ⚠️ CE QUE CE CUMUL NE VOIT PAS : il dit dans quel MODE le\n");
        printf("     module se croit, ⛔ pas que la dalle est effectivement\n");
        printf("     sombre. Le constat owner reste requis. Et pendant un\n");
        printf("     `ui off`, le temps est impute au mode COURANT — sans\n");
        printf("     consequence en regime, ou le port est tenu par l'agent.\n");
        printf("  ⛔ EN RAM (D4) : un reboot le remet a zero, et il rompt la\n");
        printf("     fenetre du soak de toute facon (AC3.6).\n");
    }
    printf("rebases d'horloge a `ui on` : %lu · bascules ANNULEES (async refusee) : %lu\n",
           (unsigned long)c.rebases, (unsigned long)c.annulations);
    /* 🔴 LE COUT DE LA PERSISTANCE EST PUBLIE, PARCE QU'IL EST PAYE DANS LA
     *    TACHE LVGL au tap MENU : une ecriture flash coupe le cache, la tache
     *    de rendu STALLE, ce sont des trames perdues. ⛔ Ni une raison de ne pas
     *    persister, ni une raison de le taire. */
    if (dg.persist_n > 0) {
        printf("derniere ecriture NVS : %lu us (%lu au total)\n",
               (unsigned long)dg.persist_us, (unsigned long)dg.persist_n);
        printf("   ⚠️ payee DANS LA TACHE LVGL quand elle vient d'un tap MENU :\n");
        printf("   le cache flash est coupe pendant ce temps-la.\n");
    } else {
        /* ⚠️ « depuis le boot » etait FAUX des qu'un `veille reset` avait eu
         *    lieu : il remet ce compteur a zero (AC8.3). L'etiquette nomme
         *    donc les DEUX origines possibles. */
        printf("aucune ecriture NVS depuis le boot ou le dernier `veille reset`\n");
        printf("   (les deux reglages sont ceux qui etaient deja en vigueur).\n");
    }
    /* 🔴 AC3.3 — L'ECART DERNIER CONTACT -> BASCULE, LATCHE PAR LE TICK QUI A
     *    BASCULE. ⛔ Un sondage depuis l'hote ne peut PAS l'etablir : sa propre
     *    latence ajouterait une seconde a une fenetre qui n'en fait qu'une. */
    {
        uint32_t ne = dg.n;
        if (ne == 0) {
            printf("ecarts contact->bascule : AUCUN ECHANTILLON\n");
            printf("   ⛔ « pas mesure », ⛔ PAS « 0 ms ».\n");
        } else {
            /* 🔴 CHAQUE ECHANTILLON EST JUGE CONTRE LE DELAI QUI ETAIT ARME
             *    QUAND IL A ETE LATCHE, ⛔ JAMAIS CONTRE LE DELAI COURANT.
             *    DEFAUT MESURE SUR LA CARTE LE 2026-08-25 : 60 400 ms latches a
             *    1 min s'affichaient « 🔴 HORS » apres un passage a 10 min. */
            printf("ecarts contact->bascule (le plus recent d'abord) :\n");
            for (uint32_t i = 0; i < ne; i++) {
                uint32_t e = dg.ecart_ms[i];
                uint32_t dl = dg.delai_ms[i];
                if (!dg.jugeable[i]) {
                    /* ⛔ ENREGISTRE, EXCLU, ET DIT — jamais jete en silence, et
                     *    surtout jamais marque en rouge : la bascule est
                     *    CORRECTE, c'est la fenetre qui ne s'applique pas. */
                    printf("   #%lu  %8lu ms  (delai arme %lu ms)  ⚪ NON "
                           "JUGEABLE\n",
                           (unsigned long)i + 1u, (unsigned long)e,
                           (unsigned long)dl);
                    printf("        1er tick apres armement / changement de "
                           "cran / `veille reset` :\n");
                    printf("        la garde n'avait JAMAIS vu d'etat sous le "
                           "seuil. La bascule est CORRECTE,\n");
                    printf("        mais [delai ; delai+1 s] ne s'y applique "
                           "pas. ⛔ Ce n'est PAS un defaut.\n");
                    continue;
                }
                long d = (long)e - (long)dl;
                bool dans = (e >= dl && e < dl + 1000u);
                printf("   #%lu  %8lu ms  (delai arme %lu ms, %+ld ms)  %s\n",
                       (unsigned long)i + 1u, (unsigned long)e,
                       (unsigned long)dl, d,
                       dans ? "✅ dans [delai ; delai+1 s]"
                            : "🔴 HORS de [delai ; delai+1 s]");
            }
            /* 🔴 revue du 2026-08-28 — L'ECART ENTRE `bascules` ET LE NOMBRE
             *    D'ECHANTILLONS N'ETAIT EXPLIQUE NULLE PART. Une bascule FORCEE
             *    (`veille now`, le MENU) monte le compteur et ne latche AUCUN
             *    echantillon, PAR CONSTRUCTION : trois `veille now` donnaient
             *    « bascules : 3 » a cote de « AUCUN ECHANTILLON », a trois
             *    lignes d'ecart et sans un mot. */
            if (c.bascules_forcees > 0) {
                printf("   ⚠️ %lu des %lu bascules sont FORCEES (`veille now` / "
                       "MENU) :\n",
                       (unsigned long)c.bascules_forcees,
                       (unsigned long)c.bascules);
                printf("   elles ne latchent AUCUN ecart, par construction — "
                       "aucune garde n'a cede.\n");
            }
            printf("   ⚠️ la fenetre fait UNE seconde parce que la detection est\n");
            printf("   cadencee a 1 Hz (`label_tick`). ⛔ Ce n'est pas « environ\n");
            printf("   le delai » : c'est [delai ; delai+1 s], et c'est verifie.\n");
        }
    }
    printf("taps CONSOMMES par un reveil : %lu · taps de reglage dans le MENU : %lu\n",
           (unsigned long)dn_touch_consommes(),
           (unsigned long)dn_ui_menu_reglages());
    /* 🔴 TROIS COMPTEURS NES DE LA REVUE DU 2026-08-28. Chacun nomme une panne
     *    qui, avant lui, se serait produite EN SILENCE. */
    printf("contacts consommes EXPIRES (bus illisible) : %lu · bascules dont "
           "l'async a ete ABANDONNEE : %lu\n",
           (unsigned long)dn_touch_conso_expirees(),
           (unsigned long)dn_ui_veille_async_abandons());
    if (dn_touch_conso_expirees() > 0) {
        printf("   ⚠️ un contact consomme a ete abandonne faute de pouvoir lire "
               "le doigt (32 lectures\n");
        printf("   I2C ratees d'affilee). AVANT ce garde-fou, l'horloge "
               "d'inactivite restait EPINGLEE\n");
        printf("   a zero et LA VEILLE NE RETOMBAIT PLUS JAMAIS. Lire `touch` / "
               "`err_i2c`.\n");
    }
    if (dn_ui_veille_async_abandons() > 0) {
        printf("   ⚠️ un reveil s'est intercale entre l'enfilage de l'async de "
               "bascule et son execution.\n");
        printf("   L'ecran reste celui du reveil — ⛔ AVANT, il finissait "
               "« palette ACTIF a la\n");
        printf("   luminosite d'Ambient », et rien ne le disait.\n");
    }
    printf("transitions provoquees PAR LA VEILLE : %lu (dans `nav`, mais SANS\n",
           (unsigned long)dn_ui_nav_veille_count());
    printf("   chronometre : elles ne naissent d'aucun geste)\n");

    /*
     * 🔴 LE DIAGNOSTIC D'APPUI FANTOME (AC8.2).
     *    Si le GT911 verrouille un `PRESSED` fantome,
     *    `lv_display_get_inactive_time()` reste collee a ~0 et la veille ne
     *    tombe JAMAIS, EN SILENCE. Ce n'est pas theorique : le bus se degrade
     *    ~40 s au demarrage a froid avec 55,5 % d'erreurs GT911, et LE SCAN NE
     *    LE VOIT PAS — l'instrument est `touch` / `err_i2c`.
     */
    if (dg.soupcon_appui_fantome) {
        printf("\n🔴 SOUPCON D'APPUI FANTOME — LA VEILLE NE TOMBE PAS, ET VOICI POURQUOI\n");
        printf("   La veille est ARMEE, %lu s ont ete OBSERVEES (soit plus que le\n",
               (unsigned long)c.secondes_vues);
        printf("   delai + %d s de marge), AUCUNE bascule n'a eu lieu, et\n",
               DN_VEILLE_MARGE_SOUPCON_S);
        printf("   l'inactivite MAXIMALE vue est restee a %lu ms, SOUS les %lu ms\n",
               (unsigned long)c.inactivite_max_ms, (unsigned long)c.delai_ms);
        printf("   du delai. Un doigt POSE remet l'horloge a zero en permanence —\n");
        printf("   et LVGL la remet a zero TANT QUE l'etat est PRESSED, ⛔ pas\n");
        printf("   seulement au front.\n");
        printf("   ⇒ INSTRUMENT : `touch` (err_i2c, appuis, relaches). ⛔ PAS le\n");
        printf("     scan I2C, qui ne voit pas cette degradation-la.\n");
    } else if (c.armee && c.bascules == 0) {
        printf("\n(aucune bascule pour l'instant — l'inactivite max vue est %lu ms\n",
               (unsigned long)c.inactivite_max_ms);
        printf(" pour un delai de %lu ms : rien d'anormal a ce stade)\n",
               (unsigned long)c.delai_ms);
    }

    printf("\n⚠️ PROTOCOLE DE LA GATE `menu_taps` (AC5.6) — A LIRE AVANT DE LA TIRER\n");
    printf("   Le bandeau MENU n'existe QUE sur le dashboard : une fois la vue\n");
    printf("   MENU ouverte, les appuis suivants au meme endroit ne tombent sur\n");
    {
        /* ⚠️ LES BORNES SONT **RELUES** DE LA FABRIQUE DE GEOMETRIE, ⛔ jamais
         *    recitees depuis une constante : `widget voie` deplace les deux
         *    bandes a chaud, et une bande recitee aurait envoye l'owner appuyer
         *    a cote pendant que la console affirmait le contraire. C'est la
         *    lecon de la bande de jauge `RAM` (§22.3). */
        int bh = 0, mh = 0, gh = 0, ch = 0;
        dn_ui_geom_bandes(&bh, &mh, &gh, &ch);
        (void)gh;
        (void)ch;
        if (mh > 0) {
            printf("   AUCUNE zone. La serie est donc 8 ALLERS-RETOURS : appui dans\n");
            printf("   la bande y = %d..%d, puis `←` (ou `nav back`), huit fois.\n",
                   DN_LCD_V_RES - mh, DN_LCD_V_RES - 1);
            printf("   ⛔ Huit appuis d'affilee rendraient 1, ⛔ pas 8 — et ce ne\n");
            printf("     serait PAS une zone morte.\n");
        } else {
            /* 🔴 AC5.8 — LA VOIE (a) REND LE MENU INJOIGNABLE, ET ON LE DIT. */
            printf("   🔴 `menu_h = 0` : LE BANDEAU N'EST PAS DESSINE DU TOUT. La\n");
            printf("     gate d'AC5.6 est INTIRABLE dans cette configuration, et\n");
            printf("     les deux reglages sont INATTEIGNABLES AU DOIGT.\n");
            printf("     `veille …` reste le seul acces. `widget voie` pour revenir.\n");
        }
        printf("   TEMOIN NEGATIF : >= 5 appuis dans la BARRE DU HAUT (y = 0..%d)\n",
               bh - 1);
        printf("   doivent rendre 0 tap — elle, elle reste morte.\n");
    }
}

static void veille_imprimer_latences(void)
{
    uint32_t n = 0, a = 0, b = 0, c = 0, d = 0, e = 0, f = 0;
    if (!dn_ui_veille_latences(&n, &a, &b, &c, &d, &e, &f)) {
        printf("⛔ PAS MESURE : verrou LVGL non pris. ⛔ Ce n'est PAS « zero ».\n");
        return;
    }
    printf("LES DEUX LATENCES DE REVEIL — ⛔ JAMAIS UNE MOYENNE DES DEUX\n");
    printf("  t1 = contact -> RETROECLAIRAGE remonte (« l'ecran s'allume »)\n");
    printf("  t2 = contact -> PALETTE Actif complete posee\n");
    if (n == 0) {
        printf("\n  aucun reveil AU DOIGT depuis le reset ⇒ RIEN A PUBLIER.\n");
        printf("  ⛔ « 0 us » serait un chiffre ; « pas d'echantillon » n'en est\n");
        printf("     pas un. Toucher la dalle en Ambient, puis relire.\n");
        return;
    }
    printf("\n  n = %lu reveils AU DOIGT\n", (unsigned long)n);
    printf("  t1 : min %lu us · med %lu us · max %lu us\n", (unsigned long)a,
           (unsigned long)b, (unsigned long)c);
    printf("  t2 : min %lu us · med %lu us · max %lu us\n", (unsigned long)d,
           (unsigned long)e, (unsigned long)f);
    printf("\n⚠️ CE QUE t1 N'INCLUT PAS, ET IL FAUT LE DIRE : l'origine du\n");
    printf("   chronometre est l'instant ou le `read_cb` VOIT le front, ⛔ pas\n");
    printf("   l'instant du contact PHYSIQUE. Le trajet GT911 -> IRQ -> reveil de\n");
    printf("   la tache LVGL -> transaction I2C est EN AMONT et n'est pas\n");
    printf("   instrumente. Publier t1 comme « latence au doigt » sans cette\n");
    printf("   phrase fabriquerait un chiffre plus flatteur que le vecu.\n");
    printf("⚠️ SEULS LES REVEILS AU DOIGT entrent ici. Un `veille wake` tape au\n");
    printf("   clavier n'a pas le meme chemin d'entree ; il est ENREGISTRE mais\n");
    printf("   EXCLU de la statistique, ⛔ pas jete en silence.\n");
    printf("⛔ NE PAS CONFONDRE AVEC LE CRITERE BRIEF « < 300 ms », qui porte sur\n");
    printf("   la NAVIGATION et qui est DEJA NON COCHE (337,6 ms au `nav ab`,\n");
    printf("   361,8 ms au doigt — dn4-4, decision owner du 2026-08-24).\n");
}

static void veille_imprimer_geom(void)
{
    /*
     * 🔴 AC1.3 — LE LAYOUT EST STRICTEMENT IDENTIQUE, ET C'EST CHIFFRE.
     *    ⛔ Pas un constat a l'oeil : on imprime les quatre nombres de chacune
     *    des six cases POUR LE MODE COURANT, plus un condense FNV-1a des 28
     *    nombres. Deux modes qui rendent le meme condense n'ont pas bouge d'un
     *    pixel.
     * 🔴 CORRIGE EN REVUE DE CODE LE 2026-08-28 — CE COMMENTAIRE DISAIT « DANS
     *    LES DEUX MODES », CE QUE CETTE FONCTION N'A JAMAIS FAIT : elle
     *    n'imprime QUE le mode ou l'on se trouve. Ce sont les DEUX RELEVES du
     *    protocole ci-dessous qui couvrent les deux modes.
     */
    uint32_t h = 0;
    if (!dn_ui_geom_signature(&h)) {
        printf("⛔ PAS MESURE : verrou LVGL non pris.\n");
        return;
    }
    printf("GEOMETRIE — mode courant : %s\n",
           dn_veille_mode_nom(dn_veille_mode()));
    printf("  case  x    y    w    h\n");
    for (int i = 0; i < DN_UI_METRIQUES; i++) {
        int x = 0, y = 0, w = 0, ht = 0;
        dn_ui_case_rect(i, &x, &y, &w, &ht);
        printf("   %-9s %4d %4d %4d %4d\n", dn_ui_metrique_nom(i), x, y, w, ht);
    }
    int bh = 0, mh = 0, gh = 0, ch = 0;
    dn_ui_geom_bandes(&bh, &mh, &gh, &ch);
    printf("  bandes : barre %d · menu %d · grille %d · case %d\n", bh, mh, gh,
           ch);
    printf("  SIGNATURE FNV-1a des 28 nombres : 0x%08lX\n", (unsigned long)h);
    printf("\n⚠️ LE PROTOCOLE FAIT DEUX RELEVES : `veille geom`, puis\n");
    printf("   `veille now`, puis `veille geom` a nouveau. Les deux signatures\n");
    printf("   DOIVENT etre identiques. ⛔ Un seul releve ne prouve rien.\n");
    printf("🔴 ET CE QU'IL PROUVE EST BORNE — DIT EN REVUE DE CODE LE 2026-08-28.\n");
    printf("   `dn_ui_case_rect()` et `dn_ui_geom_bandes()` NE CONSULTENT JAMAIS\n");
    printf("   le mode : les deux signatures sont donc identiques PAR\n");
    printf("   CONSTRUCTION, et ce releve est une GARDE DE NON-REGRESSION,\n");
    printf("   ⛔ pas une mesure qui pourrait echouer aujourd'hui.\n");
    printf("   ⚠️ CE QUE LA VEILLE DEPLACE VIT AILLEURS ET N'EST **PAS** COUVERT\n");
    printf("   ICI : l'ordonnee de la valeur (48 -> 26), le pas entre lignes\n");
    printf("   (40 -> 47) et la police (28 -> 33 ou 56). AC1.3 porte sur les\n");
    printf("   CASES et les BANDES — ⛔ ne pas lire ce condense comme une preuve\n");
    printf("   que rien ne bouge dans une case.\n");
    printf("⚠️ FNV-1a et ⛔ pas une somme : une somme aurait rendu le MEME\n");
    printf("   condense pour une case deplacee de +1 en x et -1 en y.\n");
}

static void veille_imprimer_assets(void)
{
    /*
     * 🔴 AC1.4 — LE RECOMPTE, PUBLIE PAR LE FIRMWARE LUI-MEME.
     *    ⛔ Ne pas se contenter de citer le ledger : il ecrivait « trois
     *    declinaisons ne tiennent pas », et LE VRAI CHIFFRE COMMENCE A « DEUX ».
     */
    unsigned part = VEILLE_ASSETS_PART_O;
    unsigned asset = (unsigned)DN_FB_BYTES + 16u; /* + la bande-annonce */
    printf("POURQUOI AMBIENT N'AJOUTE PAS UN SEUL OCTET D'ASSET (AC1)\n");
    printf("  partition `assets`        = %u o (0x%X, partitions.csv)\n", part,
           part);
    printf("  Living PCB v0 + pied      = %u o (%u px x 2 + 16 o)\n", asset,
           (unsigned)(DN_FB_BYTES / 2));
    printf("  libre                     = %u o\n", part - asset);
    printf("  une 2e declinaison coute  = %u o  >  %u o libres  ⇒ ❌\n", asset,
           part - asset);
    printf("  DEUX declinaisons         = %u o  >  %u o  ⇒ ❌ (depassement %u o)\n",
           2u * asset, part, 2u * asset - part);
    printf("  TROIS declinaisons        = %u o  >  %u o  ⇒ ❌ (facteur %u,%02u)\n",
           3u * asset, part, (3u * asset) / part,
           (((3u * asset) * 100u) / part) % 100u);
    printf("\n  ⚠️ LE CHIFFRE « DEUX » DE LA STORY EST FAUX DE 16 o : elle ecrit\n");
    printf("     1 228 816 (UN seul pied pour deux assets) alors qu'elle compte\n");
    printf("     bien TROIS pieds pour trois (1 843 248). Chaque asset porte SA\n");
    printf("     bande-annonce ⇒ deux coutent %u o. Le verdict ne change pas,\n",
           2u * asset);
    printf("     mais un chiffre publie se relit.\n");
    printf("\n  ⚠️ ET `dn_asset` NE GERE QU'UN SEUL ASSET : offset fixe, une magie,\n");
    printf("     un CRC (`dn_asset.h`). Meme si la place existait, il faudrait le\n");
    printf("     generaliser.\n");
    printf("  ⇒ VOIE RETENUE : (b) UNE SEULE IMAGE + transformation a l'affichage.\n");
    printf("    1. l'arithmetique ci-dessus elimine (a) et (c) SANS MESURE ;\n");
    printf("    2. le voile translucide EXISTE DEJA et fait exactement ca ;\n");
    printf("    3. la partition ne bouge pas ⇒ AUCUN risque de brick au reflash.\n");
    printf("  ⛔ `partitions.csv` est INCHANGE (AC1.1) — `git diff --stat` le dit.\n");
    printf("  🔴 ECART DECLARE : le commentaire de `partitions.csv` annonce que\n");
    printf("     « la marge accueille les 3 declinaisons de dn3-3 ». C'EST FAUX,\n");
    printf("     et ce recompte le prouve. ⛔ Il n'est PAS corrige ici : AC1.1\n");
    printf("     exige que le fichier n'apparaisse pas au `git diff --stat`.\n");
    printf("     Le verbatim est au dossier, pour `dn4-16`.\n");
}

/*
 * 🔴 QUELLES PAIRES D'ACCENTS LE TAUX COURANT CONFOND — **CALCULE**, ⛔ PAS RECITE.
 *
 * Ce n'est pas une precaution theorique : a 100 % (gris PUR) le cyan de `GPU`
 * (0x22d3ee) et le rose de `RAM` (0xf472b6) rendent TOUS LES DEUX la luminance
 * 160/255. Les six couleurs que l'owner vient d'arbitrer en dn4-4 puis dn4-13
 * redeviendraient CINQ en veille — le piege n°6 de dn3-3 applique aux accents.
 * ⇒ Le defaut est 95 : l'ecart chromatique minimal des SEPT accents (les six
 *   cases + l'humidite d'AMBIANCE) y remonte a 7/255, invisible a l'oeil, et
 *   l'information est gardee.
 * ⛔ La console ne recite AUCUN de ces nombres : elle relit les couleurs des
 *   descripteurs et APPELLE `dn_widget_desaturer()`, la meme fonction que
 *   l'ecran. Un rapport calcule sur une copie de la formule mesurerait l'accord
 *   de la copie avec elle-meme.
 */
static void veille_accents_collisions(void)
{
    int pct = dn_widget_accent_amb();
    /* 🔴 REVUE DE CODE DU 2026-08-28 — LE TABLEAU FAISAIT SIX ET LE DEFAUT `95`
     *    EST ETABLI SUR **SEPT**. Le motif ecrit juste au-dessus dit « les six
     *    cases + l'humidite d'AMBIANCE » ; la boucle, elle, s'arretait aux
     *    cases. ⇒ `veille accents 60` pouvait faire entrer l'accent d'humidite
     *    en collision pendant que l'instrument imprimait « ✅ … restent
     *    DISTINCTS deux a deux ». Une gate scopee plus etroit que la propriete
     *    qu'elle annonce. */
    uint32_t c[DN_UI_METRIQUES + 1];
    int idx[DN_UI_METRIQUES + 1];
    const char *nom7 = "AMBIANCE (humidite)";
    int n = 0;
    for (int i = 0; i < DN_UI_METRIQUES; i++) {
        /* ⚠️ LA COULEUR EST RELUE, ⛔ pas recopiee ici. `dn_ui_desc()` rend NULL
         *    pour une case rendue NUE — elle n'a pas d'accent, elle ne
         *    participe donc pas au compte.
         * 🔴 dn4-14 — MAIS LA VALEUR VIENT DE `dn_ui_case_couleur()`, ⛔ PLUS DE
         *    `d->couleur`. Ce pointeur vise `k_desc[]`, qui est `const` : il
         *    IGNORE l'override a chaud. Cet instrument aurait donc rendu son
         *    verdict de collision sur L'ANCIENNE PALETTE pendant que la dalle
         *    affichait la nouvelle — et c'est PRECISEMENT pendant l'arbitrage
         *    de couleur qu'on s'en sert. La story ne recensait que TROIS
         *    consommateurs de `k_desc[].couleur` ; celui-ci est le QUATRIEME,
         *    trouve en cherchant les autres. */
        const dn_widget_desc_t *d = dn_ui_desc(i);
        if (d) {
            idx[n] = i;
            c[n] = dn_widget_desaturer(dn_ui_case_couleur(i), pct);
            n++;
        }
    }
    /* La 7e : relue de `dn_ui_accent_hum()`, ⛔ pas recopiee ici. */
    idx[n] = -1;
    c[n] = dn_widget_desaturer(dn_ui_accent_hum(), pct);
    n++;

    int paires = 0;
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) {
            if (c[i] == c[j]) {
                if (paires == 0) {
                    printf("🔴 A %d %%, DES ACCENTS SE CONFONDENT :\n", pct);
                }
                paires++;
                printf("   « %s » et « %s » rendent tous deux %06lX\n",
                       idx[i] < 0 ? nom7 : dn_ui_metrique_nom(idx[i]),
                       idx[j] < 0 ? nom7 : dn_ui_metrique_nom(idx[j]),
                       (unsigned long)c[i]);
            }
        }
    }
    if (paires == 0) {
        printf("✅ a %d %%, les %d accents restent DISTINCTS deux a deux "
               "(les cases + l'humidite d'AMBIANCE).\n",
               pct, n);
    } else {
        /* 🔴 REVUE DU 2026-08-29 — L'ECART EST CALCULE ICI, ⛔ PLUS RECITE.
         *    Cette ligne ecrivait « 7/255 » : c'etait la mesure d'AVANT la
         *    seance, et la palette retenue (DISQUE = 0xe2e8f0) la porte a 10.
         *    Un nombre recopie derive a la premiere couleur qui bouge — et
         *    celui-ci l'a fait dans la story meme qui deplacait la couleur. */
        uint32_t d95[DN_UI_METRIQUES + 1];
        int n95 = 0;
        for (int i = 0; i < DN_UI_METRIQUES; i++) {
            if (dn_ui_desc(i)) {
                d95[n95++] = dn_widget_desaturer(dn_ui_case_couleur(i), 95);
            }
        }
        d95[n95++] = dn_widget_desaturer(dn_ui_accent_hum(), 95);
        int mini = 255;
        for (int i = 0; i < n95; i++) {
            for (int j = i + 1; j < n95; j++) {
                int dr = (int)((d95[i] >> 16) & 0xFFu) - (int)((d95[j] >> 16) & 0xFFu);
                int dg = (int)((d95[i] >> 8) & 0xFFu) - (int)((d95[j] >> 8) & 0xFFu);
                int db = (int)(d95[i] & 0xFFu) - (int)(d95[j] & 0xFFu);
                if (dr < 0) { dr = -dr; }
                if (dg < 0) { dg = -dg; }
                if (db < 0) { db = -db; }
                int dm = dr > dg ? dr : dg;
                if (db > dm) { dm = db; }
                if (dm < mini) { mini = dm; }
            }
        }
        printf("   ⇒ `veille accents 95` les separe (ecart chromatique %d/255,\n",
               mini);
        printf("     invisible a l'oeil). ⛔ Rendre deux choses indiscernables est\n");
        printf("     le defaut que ce depot a deja paye le 2026-08-18.\n");
    }
    printf("⚠️ La luminance est celle d'ITU-R BT.601 (77/150/29). Le motif est\n");
    printf("   PERCEPTUEL : le vert pese 59 %%, le bleu 11 %%, et une moyenne des\n");
    printf("   trois canaux ne dit pas ce que l'oeil voit.\n");
    /* 🔴 REVUE DU 2026-08-29 — CE QUI ETAIT IMPRIME ICI ETAIT REFUTE.
     *    Le texte affirmait « MESURE, les deux mappings confondent UNE paire
     *    chacun, simplement pas la meme ». Sur le jeu REELLEMENT PEINT (les 6
     *    cases + l'humidite), la moyenne n'en confond AUCUNE : la paire qu'on
     *    lui attribuait etait `CPU` / la metrique FICTIVE de demo. ⛔ On ne
     *    remplace pas un chiffre faux par un autre chiffre recite — le compte
     *    est TENU par `tools/verif_veille_dn33.py`, qui le RE-MESURE. */
    printf("⛔ Le compte des collisions par mapping n'est PAS recite ici :\n");
    printf("   `tools/verif_veille_dn33.py` le RE-MESURE a chaque passage.\n");
}

/*
 * 🔴 UN GRIS N'EST PAS NEUTRE EN RGB565, ET LA CONSOLE LE DIT.
 *
 *    Le canal VERT porte 6 bits, le rouge et le bleu 5. Un `R = G = B` ne
 *    survit donc pas a la quantification : `0x1E1E1E` sort en R24 G28 B24,
 *    soit +4 de vert sur le canal que l'oeil pese a 59 %. Constat owner du
 *    2026-08-25 : « les 6 cases sont pleines en VERT sur fond noir ».
 * ⛔ ON AVERTIT, ON NE REFUSE PAS et ⛔ on n'arrondit pas en silence : c'est un
 *    instrument d'A/B, l'owner doit voir la couleur qu'il tape et savoir
 *    qu'elle tirera.
 */
static void veille_dire_si_pas_neutre(uint32_t rgb)
{
    int r8 = (int)((rgb >> 16) & 0xFF);
    int g8 = (int)((rgb >> 8) & 0xFF);
    int b8 = (int)(rgb & 0xFF);
    if (r8 != g8 || g8 != b8) {
        return; /* ce n'est pas un gris : la question ne se pose pas */
    }
    int r5 = r8 >> 3, g6 = g8 >> 2;
    int R = (r5 << 3) | (r5 >> 2);
    int G = (g6 << 2) | (g6 >> 4);
    int d = G - R;
    if (d >= -1 && d <= 1) {
        printf("✅ %06lX est RGB565-NEUTRE (rendu R%d G%d B%d, ecart %+d).\n",
               (unsigned long)rgb, R, G, R, d);
        return;
    }
    printf("🔴 %06lX N'EST PAS RGB565-NEUTRE : il sortira R%d G%d B%d, soit un\n",
           (unsigned long)rgb, R, G, R);
    printf("   ecart de %+d sur le VERT — le canal que l'oeil pese a 59 %%.\n", d);
    printf("   En RGB565 le vert a 6 bits, le rouge et le bleu 5 : un gris\n");
    printf("   R=G=B ne survit pas a la quantification.\n");
    /* Le voisin neutre le plus proche, CALCULE — ⛔ pas une table recitee. */
    for (int k = 1; k <= 8; k++) {
        for (int sgn = -1; sgn <= 1; sgn += 2) {
            int v = r8 + sgn * k;
            if (v < 0 || v > 255) {
                continue;
            }
            int vr = v >> 3, vg = v >> 2;
            int VR = (vr << 3) | (vr >> 2);
            int VG = (vg << 2) | (vg >> 4);
            if (VG - VR >= -1 && VG - VR <= 1) {
                printf("   ⇒ le neutre le plus proche est %02X%02X%02X "
                       "(ecart %+d).\n", v, v, v, VG - VR);
                return;
            }
        }
    }
    (void)b8;
}

static int cmd_veille(int argc, char **argv)
{
    if (argc < 2) {
        veille_imprimer_etat();
        printf("\n");
        veille_usage();
        return 0;
    }

    if (strcmp(argv[1], "on") == 0 || strcmp(argv[1], "off") == 0) {
        if (argc != 2) {
            printf("usage : veille on | veille off\n");
            return 1;
        }
        bool on = (strcmp(argv[1], "on") == 0);
        esp_err_t err = dn_ui_veille_set_armee(on, DN_VEILLE_ORIG_CONSOLE);
        printf("veille %s.\n", on ? "ARMEE" : "DESARMEE");
        if (!on) {
            printf("⇒ la bascule vers Ambient n'arrivera PLUS. Si on dormait, on\n");
            printf("  vient d'etre REVEILLE : un ecran gris qu'aucune bascule ne\n");
            printf("  peut plus lever serait un mensonge d'interface.\n");
        }
        if (err != ESP_OK) {
            /* ⛔ NE JAMAIS ANNONCER « ENREGISTRE » SUR UN ECHEC NVS. */
            printf("⚠️ ECRITURE NVS REFUSEE (%s) : le reglage s'applique A CHAUD\n",
                   esp_err_to_name(err));
            printf("   mais NE SURVIVRA PAS au reboot.\n");
            return 1;
        }
        return 0;
    }

    if (strcmp(argv[1], "delai") == 0) {
        long m = 0;
        if (argc != 3 || !parse_entier(argv[2], &m)) {
            printf("usage : veille delai <1|3|5|10>   (en MINUTES)\n");
            return 1;
        }
        int idx = dn_veille_cran_index((int)m);
        if (idx < 0) {
            /* ⛔ REFUSER ET EXPLIQUER, ⛔ pas ecreter vers le cran voisin. */
            printf("refuse : %ld min n'est pas un cran. Les QUATRE crans sont :",
                   m);
            for (int i = 0; i < DN_VEILLE_CRANS; i++) {
                printf(" %d", dn_veille_cran_min(i));
            }
            printf(" min.\n");
            printf("(decision owner du 2026-08-25 — quatre crans discrets, ⛔ pas\n");
            printf(" de valeur libre. Un arrondi silencieux vers le cran voisin\n");
            printf(" ferait mesurer un delai que personne n'a demande.)\n");
            return 1;
        }
        esp_err_t err = dn_ui_veille_set_cran(idx);
        printf("delai : %d min (%lu ms).\n", dn_veille_cran_min(idx),
               (unsigned long)dn_veille_delai_ms());
        printf("⚠️ la detection est cadencee a 1 Hz (`label_tick`) : l'ecart\n");
        printf("   MESURE entre le dernier contact et la bascule tombe donc dans\n");
        printf("   [%d ; %d] s, ⛔ pas « environ %d min ».\n",
               dn_veille_cran_min(idx) * 60, dn_veille_cran_min(idx) * 60 + 1,
               dn_veille_cran_min(idx));
        if (err != ESP_OK) {
            printf("⚠️ ECRITURE NVS REFUSEE (%s) : ne survivra pas au reboot.\n",
                   esp_err_to_name(err));
            return 1;
        }
        return 0;
    }

    if (strcmp(argv[1], "now") == 0) {
        if (argc != 2) {
            printf("usage : veille now\n");
            return 1;
        }
        esp_err_t err = dn_ui_veille_dormir();
        if (err == ESP_ERR_INVALID_STATE) {
            if (dn_veille_mode() == DN_VEILLE_AMBIENT) {
                printf("rien a faire : on est DEJA en Ambient.\n");
            } else {
                printf("refuse : la veille est DESARMEE (`veille on` d'abord).\n");
                printf("⛔ On ne contourne pas le reglage de l'utilisateur.\n");
            }
            return 0;
        }
        if (err != ESP_OK) {
            printf("refuse : %s\n", esp_err_to_name(err));
            return 1;
        }
        printf("Ambient. Le retroeclairage est a %d %%, le voile a %u.\n",
               dn_display_backlight_pct_state(), (unsigned)dn_ui_veille_voile());
        /* 🔴 dn4-19 — CETTE LIGNE IMPRIMAIT `dn_veille_pct()`, C'EST-A-DIRE UN
         *   REGLAGE, EN ANNONCANT L'ETAT DE LA DALLE. Tant qu'Ambient valait la
         *   constante, les deux coincidaient ; depuis que le niveau suit le lux,
         *   c'etait devenu un instrument qui ment. On lit desormais LEDC. */
        printf("⚠️ LES DONNEES RESTENT VIVANTES : `hist` continue d'echantillonner,\n");
        printf("   l'heure avance, les six cases changent. Veille ≠ fige.\n");
        return 0;
    }

    if (strcmp(argv[1], "wake") == 0) {
        if (argc != 2) {
            printf("usage : veille wake\n");
            return 1;
        }
        esp_err_t err = dn_ui_veille_reveiller(DN_VEILLE_ORIG_CONSOLE);
        if (err == ESP_ERR_INVALID_STATE) {
            printf("rien a faire : on est DEJA en Actif.\n");
            return 0;
        }
        if (err != ESP_OK) {
            printf("refuse : %s\n", esp_err_to_name(err));
            return 1;
        }
        printf("Actif.\n");
        printf("⚠️ CET ECHANTILLON EST EXCLU de la statistique de `veille lat` :\n");
        printf("   il n'a pas le chemin d'entree du DOIGT. Il est enregistre et\n");
        printf("   compte, ⛔ pas jete en silence.\n");
        return 0;
    }

    if (strcmp(argv[1], "lat") == 0) {
        veille_imprimer_latences();
        return 0;
    }

    if (strcmp(argv[1], "geom") == 0) {
        veille_imprimer_geom();
        return 0;
    }

    if (strcmp(argv[1], "fond") == 0) {
        /* 🔴 CE QUI EST POSE SUR LES OBJETS, ⛔ PAS CE QUE LES VARIABLES DISENT.
         *    Constat owner du 2026-08-25 : « au lieu d'un noir/gris sombre c'est
         *    un vert ». `veille now` annoncait « voile a 255 » pendant que le
         *    Living PCB restait visible — une variable ne peut pas trancher. */
        int nv = 0;
        uint8_t opas[8] = {0};
        uint32_t couls[8] = {0};
        uint8_t copa = 0;
        uint32_t ccoul = 0;
        if (!dn_ui_veille_voiles_etat(&nv, opas, couls, 8, &copa, &ccoul)) {
            printf("⛔ PAS MESURE : verrou LVGL non pris.\n");
            return 1;
        }
        printf("LE FOND, RELU DES OBJETS LVGL — ⛔ pas des variables\n");
        printf("  mode : %s\n", dn_veille_mode_nom(dn_veille_mode()));
        printf("  voiles VIVANTS : %d\n", nv);
        if (nv == 0) {
            printf("  🔴 AUCUN VOILE RETENU : la bascule de veille n'a RIEN a\n");
            printf("     ecrire, et le Living PCB reste visible quoi que\n");
            printf("     `veille` annonce. C'est LE defaut a chercher.\n");
        }
        for (int i = 0; i < nv && i < 8; i++) {
            printf("    voile %d : opa %3u · couleur %06lX%s\n", i,
                   (unsigned)opas[i], (unsigned long)couls[i],
                   couls[i] == 0xFFFFFFFFu ? "  🔴 POINTEUR NUL" : "");
        }
        printf("  aplat de case : opa %u · couleur %06lX\n", (unsigned)copa,
               (unsigned long)ccoul);
        printf("  ce que les VARIABLES annoncent : voile Ambient %u · voile "
               "Actif %u\n",
               (unsigned)dn_ui_veille_voile(), (unsigned)dn_ui_voile_opa());
        printf("⚠️ UN ECART entre les deux blocs EST le defaut. Les objets font\n");
        printf("   foi : c'est eux que la dalle dessine.\n");

        /* 🔴 …ENCORE FAUT-IL MESURER LE BON ECRAN. */
        int qui = -9, nc = 0;
        int op[12] = {0}, lw[12] = {0}, lh[12] = {0};
        if (dn_ui_veille_ecran_actif(&qui, &nc, op, lw, lh, 12)) {
            static const char *k_qui[] = {"dashboard", "detail", "MENU"};
            printf("\nL'ECRAN ACTIF — celui que la dalle dessine VRAIMENT\n");
            if (qui >= 0 && qui <= 2) {
                printf("  c'est la racine « %s » ✅\n", k_qui[qui]);
            } else if (qui == -2) {
                printf("  🔴 AUCUN ECRAN ACTIF.\n");
            } else {
                printf("  🔴 **ORPHELIN** — ce n'est AUCUNE des trois racines !\n");
                printf("     Son voile n'est donc PAS dans `s_voiles[]`, donc la\n");
                printf("     veille ne le pousse JAMAIS a 255 : le Living PCB\n");
                printf("     reste visible pendant que tout annonce du noir.\n");
                printf("     ⚠️ Precedent connu : revue dn1-4, « l'ecran sortant\n");
                printf("     n'est pas toujours l'une des racines ».\n");
            }
            printf("  %d enfant(s) — opacite de fond et taille, RELUES :\n", nc);
            for (int i = 0; i < nc && i < 12; i++) {
                /* ⚠️ Un objet MASQUE reste enfant et garde son style : sans
                 *    cette distinction, l'instrument listait un bandeau MENU
                 *    masque exactement comme un bandeau visible. */
                if (op[i] <= -1000) {
                    printf("    #%d : 🔴 POINTEUR NUL\n", i);
                } else if (op[i] < 0) {
                    printf("    #%d : opa %3d · %d x %d  🚫 MASQUE (HIDDEN)%s\n",
                           i, -1 - op[i], lw[i], lh[i],
                           (lw[i] == DN_LCD_H_RES && lh[i] == DN_LCD_V_RES)
                               ? "  <- plein ecran" : "");
                } else {
                    printf("    #%d : opa %3d · %d x %d%s\n", i, op[i], lw[i],
                           lh[i],
                           (lw[i] == DN_LCD_H_RES && lh[i] == DN_LCD_V_RES)
                               ? "  <- plein ecran" : "");
                }
            }
        } else {
            printf("\n⛔ ECRAN ACTIF : PAS MESURE (verrou non pris).\n");
        }
        return 0;
    }

    if (strcmp(argv[1], "assets") == 0) {
        veille_imprimer_assets();
        return 0;
    }

    if (strcmp(argv[1], "reset") == 0) {
        if (argc != 2) {
            printf("usage : veille reset\n");
            return 1;
        }
        /* 🔴 REVUE DE CODE DU 2026-08-28 — LES TROIS RESETS PASSENT DESORMAIS
         *    SOUS **UN SEUL VERROU**, ET LE SUCCES SE LIT. Avant, `dn_veille_reset()`
         *    et `dn_touch_consommes_rebaser()` ecrivaient depuis la tache REPL
         *    en concurrence du tick 1 Hz, et le succes etait annonce meme quand
         *    le verrou n'avait pas ete pris. Motifs dans `dn_ui.h`. */
        if (!dn_ui_veille_reset_tout()) {
            printf("⛔ PAS FAIT : le verrou LVGL n'a pas ete pris en 500 ms.\n");
            printf("   RIEN n'a ete remis a zero — ⛔ ne pas lire la sortie "
                   "suivante comme un etat neuf.\n");
            printf("   ⚠️ `build_scene()` tient le verrou 307-322 ms (mesure) : "
                   "reessayer suffit en general.\n");
            return 1;
        }
        /* 🔴 AC8.3 — CE COMPTEUR-LA SURVIVAIT AU RESET, ET LA SORTIE SE
         *    CONTREDISAIT : « reveils 0 » a cote de « taps CONSOMMES par un
         *    reveil : 1 », dans le meme bloc. Mesure le 2026-08-25.
         * ⛔ Surtout pas `dn_touch_reset_stats()` : il zeroterait aussi IRQ,
         *    lectures, appuis, relachements et erreurs I2C, que `touch`
         *    publie et que `veille` ne publie pas. */
        printf("compteurs et latences a ZERO.\n");
        printf("⛔ Les deux REGLAGES ne sont pas touches : ce sont des reglages,\n");
        printf("   pas des mesures. Le MODE non plus — le remettre a ACTIF ici\n");
        printf("   ferait diverger l'etat annonce de l'ecran reel.\n");
        /* 🔴 REVUE DE CODE DU 2026-08-28 — AC8.3 DIT « TOUS LES COMPTEURS », ET
         *    IL Y EN A UN QU'ON EPARGNE **DELIBEREMENT**. Le taire aurait laisse
         *    « compteurs a ZERO » decrire un bloc qui, lui, ne bouge pas — la
         *    forme exacte du defaut que cette story a deja corrige deux fois
         *    (`s_persist_n`, `dn_touch_consommes`). */
        printf("⛔ LE TEMPS MURAL PAR MODE (« depuis le boot ») N'EST PAS "
               "REMIS A ZERO :\n");
        printf("   c'est la FENETRE DE SOAK de `dn4-5`, qui dure UNE SEMAINE. "
               "La zeroter ici\n");
        printf("   donnerait a une commande de diagnostic le pouvoir de "
               "detruire sept jours de\n");
        printf("   mesure en une frappe. Son etiquette, elle, reste juste : "
               "« depuis le boot ».\n");
        return 0;
    }

    if (strcmp(argv[1], "pct") == 0) {
        long v = 0;
        if (argc != 3 || !parse_entier(argv[2], &v)) {
            printf("usage : veille pct <%d..%d>\n", DN_VEILLE_PCT_MIN,
                   DN_VEILLE_PCT_MAX);
            return 1;
        }
        if (dn_ui_veille_set_pct((int)v) != ESP_OK) {
            printf("refuse : %ld hors [%d ; %d].\n", v, DN_VEILLE_PCT_MIN,
                   DN_VEILLE_PCT_MAX);
            printf("  %d %% est le plancher de LISIBILITE mesure en dn1-3/AC7\n",
                   DN_VEILLE_PCT_MIN);
            printf("  (« le Living PCB et le label s'y distinguent encore, TOUT\n");
            printf("  JUSTE »). ⛔ Ne pas confondre avec `DN_ENV_BL_PCT_MIN = %d`,\n",
                   DN_ENV_BL_PCT_MIN);
            printf("  qui est le plancher de la LOI d'asservissement au lux —\n");
            printf("  un autre chiffre pour un autre usage.\n");
            /* 🔴 AJOUTÉ EN REVUE DE CODE LE 2026-08-27 — ce refus n'expliquait
             * que DEUX planchers sur TROIS, et il omettait justement celui qui
             * porte sur le rendu d'Ambient, c'est-a-dire **le seul qui concerne
             * ce que cette borne garde depuis que le levier a change de nature**. */
            printf("  ⚠️ ET IL Y EN A UN TROISIEME, dn4-19 : %d %% — le plancher\n",
                   dn_env_bl_amb_plancher());
            printf("  du RENDU D'AMBIENT (gros chiffres blancs sur noir),\n");
            printf("  mesure a l'oeil dans le noir le 2026-08-27. C'est LUI qui\n");
            printf("  borne desormais le dernier recours. TROIS contenus, TROIS\n");
            printf("  chiffres — ⛔ ne pas les fusionner par reflexe.\n");
            printf("  ⚠️ dn4-19 : la borne HAUTE est passee de 40 a %d. Le 40\n",
                   DN_VEILLE_PCT_MAX);
            printf("  disait « Ambient est un etat SOMBRE » ; ce chiffre est\n");
            printf("  desormais le DERNIER RECOURS, donc il s'applique a\n");
            printf("  n'importe quel eclairage — un plafond a 40 y serait faux\n");
            printf("  pour la meme raison que le 10 %% l'etait.\n");
            return 1;
        }
        /* 🔴 dn4-19 — CE LEVIER A CHANGE DE NATURE, ET LA CONSOLE DOIT LE DIRE.
         *   Le laisser s'annoncer « retroeclairage d'Ambient » serait une
         *   etiquette qui ment, et *« une etiquette qui ment se relit a chaque
         *   boot »* est exactement le defaut que ce depot traque. */
        /* 🔴 RÉTABLI EN REVUE DE CODE LE 2026-08-27 — la version d'avant `dn4-19`
         * imprimait « (applique MAINTENANT) » ou « (a la prochaine veille) », et
         * `dn4-19` l'a PERDU en conditionnant l'effet immédiat. ⇒ l'owner ne
         * pouvait plus savoir, depuis la sortie, si sa valeur pilotait la dalle —
         * **sur le levier même dont la story venait de changer la nature**.
         * ⚠️ La condition n'est plus « on dort », c'est « on dort ET la loi se
         * tait » : c'est ça qu'il faut dire, ⛔ pas l'ancienne. */
        bool pilote = (dn_veille_mode() == DN_VEILLE_AMBIENT) &&
                      (!dn_env_bl_auto() || dn_env_bl_cible() < 0);
        printf("niveau d'Ambient de DERNIER RECOURS : %d %%%s\n", dn_veille_pct(),
               pilote ? "   ⇒ APPLIQUE MAINTENANT (la loi se tait, c'est bien lui "
                        "qui pilote la dalle)"
                      : "   ⇒ ⛔ IL NE PILOTE RIEN EN CE MOMENT (il ne servira "
                        "qu'au prochain repli)");
        printf("⛔ CE N'EST PLUS le niveau d'Ambient (dn4-19) : en regime normal,\n");
        printf("   Ambient suit LE LUX (`bl loi` pour voir ce que la loi rendrait).\n");
        printf("   Cette valeur ne sert QUE si la loi ne peut pas parler :\n");
        printf("   BH1750 muet / jamais lu, ou `bl auto` DESARME par un geste.\n");
        printf("   Elle est JOURNALISEE quand elle sert — un repli silencieux\n");
        printf("   serait exactement le defaut que dn4-19 ferme.\n");
        printf("✅ Pour regler le niveau d'Ambient NORMAL, c'est :\n");
        printf("     `bl auto ambiant <0..100>`          l'echelle de la loi\n");
        printf("     `bl auto ambiant plancher <n>`      le plancher du RENDU d'Ambient\n");
        return 0;
    }

    if (strcmp(argv[1], "voile") == 0) {
        long v = 0;
        if (argc != 3 || !parse_entier(argv[2], &v) || v < 0 || v > 255) {
            printf("usage : veille voile <0..255>   (defaut Ambient : %u ;\n",
                   (unsigned)dn_ui_veille_voile());
            printf("        defaut ACTIF : %u, constat owner du 2026-08-17)\n",
                   (unsigned)dn_ui_voile_opa());
            return 1;
        }
        /* 🔴 REVUE DE CODE DU 2026-08-28 — CE RETOUR ETAIT JETE, ET LA LIGNE
         *    SUIVANTE ANNONCAIT « (applique MAINTENANT) ». ``dn_ui_veille_set_voile()`` ecrit sous
         *    `lvgl_port_lock(2000)` et rend `ESP_ERR_TIMEOUT` sinon : tapee
         *    pendant un `build_scene()` (307-322 ms verrou tenu, MESURE)
         *    enchaine a une ecriture NVS, la commande n'ecrivait RIEN et la
         *    console disait le contraire. ⇒ l'A/B d'AC9 tranchait A L'OEIL sur
         *    une valeur JAMAIS POSEE. Les trois voisines (`veille on`,
         *    `veille delai`, `veille unite`) testaient deja leur retour. */
        esp_err_t evo = dn_ui_veille_set_voile((uint8_t)v);
        if (evo != ESP_OK) {
            printf("⛔ NON APPLIQUE : %s — le verrou LVGL n'a pas ete pris.\n",
                   esp_err_to_name(evo));
            printf("   ⛔ Ne rien conclure a l'oeil : la valeur n'est PAS posee.\n");
            return 1;
        }
        printf("voile d'Ambient : %ld%s\n", v,
               dn_veille_mode() == DN_VEILLE_AMBIENT ? " (applique MAINTENANT)"
                                                     : " (a la prochaine veille)");
        printf("⛔ AUCUNE reconstruction de scene : les voiles sont RETENUS, on\n");
        printf("   n'ecrit que leur style. C'est ce qui rend cet A/B jouable sans\n");
        printf("   payer 307-322 ms par essai.\n");
        return 0;
    }

    if (strcmp(argv[1], "gris") == 0) {
        long rgb = 0;
        int reg = -1;
        if (argc == 4) {
            if (strcmp(argv[2], "reel") == 0) {
                reg = DN_VAL_REELLE;
            } else if (strcmp(argv[2], "simule") == 0) {
                reg = DN_VAL_SIMULEE;
            } else if (strcmp(argv[2], "absent") == 0) {
                reg = DN_VAL_ABSENTE;
            }
        }
        if (reg < 0 || !parse_hex_strict(argv[3], &rgb) || rgb < 0 ||
            rgb > 0xFFFFFF) {
            printf("usage : veille gris <reel|simule|absent> <rrggbb>\n");
            printf("  actuels : reel %06lX · simule %06lX · absent %06lX\n",
                   (unsigned long)dn_widget_gris_amb(DN_VAL_REELLE),
                   (unsigned long)dn_widget_gris_amb(DN_VAL_SIMULEE),
                   (unsigned long)dn_widget_gris_amb(DN_VAL_ABSENTE));
            printf("🔴 ILS SONT TROIS, ET C'EST LE PIEGE NOMME D'AVANCE :\n");
            printf("   `W_COL_ABSENTE = 9a9a9a` est tentant et GRATUIT. S'en\n");
            printf("   servir pour les valeurs REELLES en Ambient rendrait\n");
            printf("   « vivant » indiscernable de « mort » — exactement le\n");
            printf("   defaut du 2026-08-18 (SIMULEE indiscernable d'ABSENTE),\n");
            printf("   qui avait demande une revue de code pour etre vu.\n");
            return 1;
        }
        /* 🔴 REVUE DE CODE DU 2026-08-28 — CE RETOUR ETAIT JETE, ET LA LIGNE
         *    SUIVANTE ANNONCAIT « (applique MAINTENANT) ». ``dn_ui_veille_set_gris()`` ecrit sous
         *    `lvgl_port_lock(2000)` et rend `ESP_ERR_TIMEOUT` sinon : tapee
         *    pendant un `build_scene()` (307-322 ms verrou tenu, MESURE)
         *    enchaine a une ecriture NVS, la commande n'ecrivait RIEN et la
         *    console disait le contraire. ⇒ l'A/B d'AC9 tranchait A L'OEIL sur
         *    une valeur JAMAIS POSEE. Les trois voisines (`veille on`,
         *    `veille delai`, `veille unite`) testaient deja leur retour. */
        esp_err_t egr = dn_ui_veille_set_gris(reg, (uint32_t)rgb);
        if (egr != ESP_OK) {
            printf("⛔ NON APPLIQUE : %s — le verrou LVGL n'a pas ete pris.\n",
                   esp_err_to_name(egr));
            printf("   ⛔ Ne rien conclure a l'oeil : la valeur n'est PAS posee.\n");
            return 1;
        }
        veille_dire_si_pas_neutre((uint32_t)rgb);
        printf("gris d'Ambient « %s » : %06lX%s\n", argv[2], (unsigned long)rgb,
               dn_veille_mode() == DN_VEILLE_AMBIENT ? " (applique MAINTENANT)"
                                                     : "");
        return 0;
    }

    if (strcmp(argv[1], "case") == 0) {
        long rgb = 0;
        if (argc != 3 || !parse_hex_strict(argv[2], &rgb) || rgb < 0 ||
            rgb > 0xFFFFFF) {
            printf("usage : veille case <rrggbb>   (actuel : %06lX)\n",
                   (unsigned long)dn_widget_amb_case_bg());
            printf("🔬 INSTRUMENT DE BISSECTION avant d'etre un reglage :\n");
            printf("   constat owner du 2026-08-25 « les 6 cases sont pleines en\n");
            printf("   VERT sur fond noir », alors que l'instrument lit\n");
            printf("   `opa 255 · couleur 1E1E1E` sur la racine de chaque case.\n");
            printf("   ⛔ Un GRIS ne peut pas devenir vert (R=G=B est invariant\n");
            printf("   par permutation de canaux) ⇒ ce qui est MESURE n'est pas\n");
            printf("   ce qui est DESSINE. Poser une couleur FRANCHE tranche.\n");
            return 1;
        }
        /* 🔴 REVUE DE CODE DU 2026-08-28 — CE RETOUR ETAIT JETE, ET LA LIGNE
         *    SUIVANTE ANNONCAIT « (applique MAINTENANT) ». ``dn_ui_veille_set_case_bg()`` ecrit sous
         *    `lvgl_port_lock(2000)` et rend `ESP_ERR_TIMEOUT` sinon : tapee
         *    pendant un `build_scene()` (307-322 ms verrou tenu, MESURE)
         *    enchaine a une ecriture NVS, la commande n'ecrivait RIEN et la
         *    console disait le contraire. ⇒ l'A/B d'AC9 tranchait A L'OEIL sur
         *    une valeur JAMAIS POSEE. Les trois voisines (`veille on`,
         *    `veille delai`, `veille unite`) testaient deja leur retour. */
        esp_err_t eca = dn_ui_veille_set_case_bg((uint32_t)rgb);
        if (eca != ESP_OK) {
            printf("⛔ NON APPLIQUE : %s — le verrou LVGL n'a pas ete pris.\n",
                   esp_err_to_name(eca));
            printf("   ⛔ Ne rien conclure a l'oeil : la valeur n'est PAS posee.\n");
            return 1;
        }
        veille_dire_si_pas_neutre((uint32_t)rgb);
        printf("aplat de case en Ambient : %06lX%s\n", (unsigned long)rgb,
               dn_veille_mode() == DN_VEILLE_AMBIENT ? " (applique MAINTENANT)"
                                                     : " (a la prochaine veille)");
        /* 🔴 dn4-23 / AC6.2 — `veille case 141820` pose l'aplat EXACTEMENT sur
         *    la piste par defaut : ecart NUL, jauge disparue, et cette ligne
         *    imprimait « applique MAINTENANT » sans un mot. */
        verdict_contraste();
        return 0;
    }

    if (strcmp(argv[1], "unite") == 0 || strcmp(argv[1], "jauge") == 0) {
        bool jauge = (strcmp(argv[1], "jauge") == 0);
        if (argc != 3 ||
            (strcmp(argv[2], "on") != 0 && strcmp(argv[2], "off") != 0)) {
            printf("usage : veille %s on|off   (actuel : %s)\n", argv[1],
                   (jauge ? dn_widget_amb_jauge() : dn_widget_amb_unite())
                       ? "on" : "off");
            if (!jauge) {
                printf("🔴 `unite` NE CHOISIT PAS QU'UN TEXTE, IL CHOISIT LA POLICE.\n");
                printf("   MESURE sur cette carte (`widget largeur`, case de\n");
                printf("   225 px dont 201 utiles) :\n");
                printf("     on  ⇒ pire cas « 2999,9 Mb/s » 168 px ⇒ police 33 px\n");
                printf("     off ⇒ pire cas « 2999,9 »       90 px ⇒ police 56 px\n");
                printf("   ⛔ Ces tailles sont MESUREES, pas choisies rond : au-dela\n");
                printf("     LVGL clipperait au parent SANS UN MOT.\n");
            }
            return 1;
        }
        bool on = (strcmp(argv[2], "on") == 0);
        esp_err_t err = jauge ? dn_ui_veille_set_jauge(on)
                              : dn_ui_veille_set_unite(on);
        if (err != ESP_OK) {
            printf("refuse : %s\n", esp_err_to_name(err));
            return 1;
        }
        printf("veille %s : %s%s\n", argv[1], on ? "ON" : "OFF",
               dn_veille_mode() == DN_VEILLE_AMBIENT ? " (applique MAINTENANT)"
                                                     : " (a la prochaine veille)");
        if (!jauge) {
            printf("⇒ police de veille : %d px\n", on ? 33 : 56);
        }
        return 0;
    }

    if (strcmp(argv[1], "accents") == 0) {
        long v = 0;
        if (argc != 3 || !parse_entier(argv[2], &v)) {
            printf("usage : veille accents <0..100>   (actuel : %d)\n",
                   dn_widget_accent_amb());
            printf("  0   = teinte INTACTE (l'accent reste l'identite de la case)\n");
            printf("  100 = gris PUR (« un etat nuance de gris », owner 2026-08-25)\n");
            veille_accents_collisions();
            return 1;
        }
        if (dn_ui_veille_set_accent((int)v) != ESP_OK) {
            printf("refuse : %ld hors [0 ; 100].\n", v);
            return 1;
        }
        printf("desaturation des accents en Ambient : %d %%%s\n",
               dn_widget_accent_amb(),
               dn_veille_mode() == DN_VEILLE_AMBIENT ? " (applique MAINTENANT)"
                                                     : "");
        veille_accents_collisions();
        return 0;
    }

    printf("sous-commande « %s » inconnue.\n", argv[1]);
    veille_usage();
    return 1;
}

static const esp_console_cmd_t k_cmds[] = {
    DN_CMD("scene",
           "affiche une mire : bits|nbits|rgb|red|green|blue|white|black|frame|gray|asset",
           cmd_scene),
    DN_CMD("fps", "mesure le fps sur N secondes (>= 10) et le confronte à la théorie",
           cmd_fps),
    DN_CMD("mem", "PSRAM et RAM interne, avant/après framebuffers", cmd_mem),
    DN_CMD("cpu",
           "cpu [secondes] | cpu brut | cpu depart | cpu delta — charge "
           "processeur (AC6). ⚠️ `cpu N` BLOQUE le REPL (donc le transport) ; "
           "`depart`/`delta` encadrent une session SANS dormir (dn4-23)",
           cmd_cpu),
    DN_CMD("bw", "bande passante mesurée des 3 chemins de copie", cmd_bw),
    DN_CMD("cfg",
           "cfg | cfg reset | cfg repli [clear] — config de boot (NVS), "
           "active, effacée, ou le TÉMOIN DE REPLI",
           cmd_cfg),
    DN_CMD("set", "set fbs | bounce | lines | drawmem | core <-1|0|1>",
           cmd_set),
    DN_CMD("reboot", "redémarre pour appliquer un `set`", cmd_reboot),
    /* dn3-3 : la VEILLE (`Ambient`) — pilotage ET mesure. */
    DN_CMD("veille",
           /* 🔴 revue du 2026-08-28 — `fond`, `unite`, `jauge` et `case`
            *    MANQUAIENT ici alors que `veille_usage()` les documente. C'est
            *    cette ligne que `help` imprime : `veille fond`, l'outil de
            *    bissection qui a tranche « au lieu d'un noir/gris sombre c'est
            *    un vert », etait INVISIBLE pour qui part de `help`. */
           "veille | on|off | delai <1|3|5|10> | now | wake | lat | geom | "
           "assets | reset | pct | voile | gris | accents | fond | unite | "
           "jauge | case — la VEILLE (dn3-3)",
           cmd_veille),
    DN_CMD("tear", "tear on|vsync|sync|both|flip|off — déchirement BRUT (dn1-2)",
           cmd_tear),
    DN_CMD("flash", "flash on|off — stimulus d'écriture flash", cmd_flash),
    DN_CMD("ui", "ui [on|off] | ui label on|off | ui bg flash|psram — LVGL", cmd_ui),
    DN_CMD("flush",
           "flush | reset | sync off|vsync|fbdone | path bitmap|direct | full — "
           "chemin de flush, le compteur de GLISSEMENT de trame (dn4-10) ET la "
           "PLUS LONGUE SÉRIE de trames consécutives non saines (dn4-12)",
           cmd_flush),
    DN_CMD("anim", "anim on [ms] | off — stimulus adverse LVGL (témoin de tearing)",
           cmd_anim),
    /* dn4-5/AC2.2 : la CONTRE-ÉPREUVE de la triade du battement. */
    DN_CMD("gel",
           "gel [secondes] — BLOQUE LVGL (défaut 12 s) et montre `up`/`vsync` "
           "qui avancent pendant que `flush`/`cycles` sont FIGÉS (dn4-5)",
           cmd_gel),
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
           "<bas> <haut>|auto pas <n>|auto plancher <n>|auto ambiant "
           "<0..100>|auto ambiant plancher <n>|auto courbe log|lineaire|"
           "loi [lux]] — rétroéclairage "
           "gradable et asservi (dn1-3/dn4-3), la loi vit en Ambient (dn4-19)",
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
           "| police <taille> | grille <barre> <menu> "
           "| titre [<police>|defaut] | titre suit on|off | date [<police>|defaut] "
           "| largeur [<texte> [<police>]|mur|reset] | "
           "detail | replacer on|off — modèle de case "
           "(dn3-1/dn3-2/dn4-1/dn4-6/dn4-14-2)",
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
           /* 🔴 CORRIGÉ LE 2026-08-27 (revue) — le bandeau annonçait « fine »
            *    sous `widget groupe union`. Le diff de `c9ac2c1` avait corrigé
            *    UN des deux lecteurs du mode (l'autre est dans `cmd_widget`) et
            *    laissé celui-ci. Grep sur tout l'arbre : exactement deux sites.
            *    ⛔ Et le commentaire posé juste au-dessus de ce bandeau écrit
            *    « chaque chiffre ici vient de la fonction qui détient l'état ». */
           dn_widget_groupe_union() ? "union"
                                    : dn_widget_groupage() ? "groupée" : "fine",
           dn_widget_opa(),
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

/*
 * ══ dn4-23 / AC2.1 — LE COMPTEUR EST POSE PAR UN SHIM, ⛔ PAS BRANCHE PAR BRANCHE
 *
 * `esp_console_cmd_t` ne porte AUCUN contexte utilisateur : un shim unique ne
 * saurait pas QUELLE commande il enveloppe. On genere donc un shim par INDICE,
 * et `dn_console_start()` remplace `.func` a l'enregistrement. Ainsi :
 *   · aucune des 32 branches n'est editee — donc aucune ne peut etre OUBLIEE ;
 *   · une commande AJOUTEE demain est instrumentee sans un geste ;
 *   · `_Static_assert` fait echouer A LA COMPILATION si la table depasse
 *     `DN_CMD_MAX` — ⛔ pas au boot, sur un silence.
 *
 * ⚠️ `help` peut etre enregistree par le REPL LUI-MEME (hors `k_cmds[]`) selon
 *    la version d'ESP-IDF : elle n'aura donc PAS de compteur. L'hote traite
 *    l'absence de compteur comme « SANS COMPTEUR », ⛔ jamais comme « 0 perte ».
 */
#define DN_CMD_MAX 40
static int (*s_cmd_reelle[DN_CMD_MAX])(int, char **);

static int dn_cmd_tracer(int i, int argc, char **argv)
{
    s_lignes_cmd = 0;
    s_fin_de_ligne = true;
    s_compte_fiable = true;
    int rc = s_cmd_reelle[i](argc, argv);
    if (!s_fin_de_ligne) {
        /* Une commande qui finit sans passage a la ligne collerait sa derniere
         * ligne au compteur. On la CLOT — et cette ligne-la compte. */
        printf("\n");
    }
    uint32_t n = s_lignes_cmd; /* ⛔ LU AVANT : le compteur s'imprime lui-meme. */
    printf("--- fin : %u lignes emises%s ---\n", (unsigned)n,
           s_compte_fiable ? "" : " (COMPTE NON FIABLE : sortie tronquee)");
    return rc;
}

#define DN_SHIM(n) \
    static int dn_shim_##n(int argc, char **argv) { return dn_cmd_tracer(n, argc, argv); }
DN_SHIM(0) DN_SHIM(1) DN_SHIM(2) DN_SHIM(3) DN_SHIM(4) DN_SHIM(5) DN_SHIM(6) DN_SHIM(7)
DN_SHIM(8) DN_SHIM(9) DN_SHIM(10) DN_SHIM(11) DN_SHIM(12) DN_SHIM(13) DN_SHIM(14) DN_SHIM(15)
DN_SHIM(16) DN_SHIM(17) DN_SHIM(18) DN_SHIM(19) DN_SHIM(20) DN_SHIM(21) DN_SHIM(22) DN_SHIM(23)
DN_SHIM(24) DN_SHIM(25) DN_SHIM(26) DN_SHIM(27) DN_SHIM(28) DN_SHIM(29) DN_SHIM(30) DN_SHIM(31)
DN_SHIM(32) DN_SHIM(33) DN_SHIM(34) DN_SHIM(35) DN_SHIM(36) DN_SHIM(37) DN_SHIM(38) DN_SHIM(39)
#undef DN_SHIM

static int (*const s_shims[DN_CMD_MAX])(int, char **) = {
dn_shim_0, dn_shim_1, dn_shim_2, dn_shim_3, dn_shim_4, dn_shim_5, dn_shim_6, dn_shim_7,
dn_shim_8, dn_shim_9, dn_shim_10, dn_shim_11, dn_shim_12, dn_shim_13, dn_shim_14, dn_shim_15,
dn_shim_16, dn_shim_17, dn_shim_18, dn_shim_19, dn_shim_20, dn_shim_21, dn_shim_22, dn_shim_23,
dn_shim_24, dn_shim_25, dn_shim_26, dn_shim_27, dn_shim_28, dn_shim_29, dn_shim_30, dn_shim_31,
dn_shim_32, dn_shim_33, dn_shim_34, dn_shim_35, dn_shim_36, dn_shim_37, dn_shim_38, dn_shim_39
};

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
    _Static_assert(sizeof(k_cmds) / sizeof(k_cmds[0]) <= DN_CMD_MAX,
                   "k_cmds[] depasse DN_CMD_MAX : ajouter des DN_SHIM(n) et "
                   "des entrees a s_shims[]. ⛔ Une commande sans shim n'aurait "
                   "PAS de compteur de lignes (dn4-23/AC2.1).");
    for (size_t i = 0; i < sizeof(k_cmds) / sizeof(k_cmds[0]); i++) {
        /* dn4-23/AC2.1 : la commande REELLE est mise de cote, le REPL appelle
         * le shim qui compte les lignes et publie l'invariant. */
        esp_console_cmd_t c = k_cmds[i];
        s_cmd_reelle[i] = c.func;
        c.func = s_shims[i];
        ESP_ERROR_CHECK(esp_console_cmd_register(&c));
    }
    ESP_ERROR_CHECK(esp_console_start_repl(repl));
    return ESP_OK;
}

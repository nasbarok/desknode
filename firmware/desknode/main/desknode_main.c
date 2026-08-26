/*
 * DeskNode — P2 « label vivant + backlight piloté » (story dn1-3), sur le socle
 * P1 « Living PCB statique plein écran » (dn1-2).
 *
 * Ce que ce firmware fait, dans cet ordre EXACT :
 *   1. lit la configuration de boot (num_fbs, bounce, draw buffer) en NVS ;
 *   2. monte le pipeline d'affichage, rétroéclairage à DUTY 0 ;
 *   3. mappe l'asset Living PCB (vérifié par CRC) ;
 *   4. monte LVGL dessus et construit la scène (fond + label) ;
 *   5. branche le compteur vsync — APRÈS LVGL, et c'est un piège documenté ;
 *   6. attend la PREMIÈRE trame LVGL réellement flushée ;
 *   7. ALLUME le rétroéclairage — et seulement là ;
 *   8. ouvre la console de mesure.
 *
 * ⚠️ L'ÉTAPE 7 APRÈS L'ÉTAPE 6 n'est pas un détail de style, et dn1-3 ne fait
 *    que la TRANSPOSER : en dn1-2 la condition était « le framebuffer est
 *    rempli », elle est maintenant « LVGL a fini son premier cycle ». L'inverse
 *    donne un flash blanc ou un champ de bruit au démarrage, et on passe une
 *    heure à douter du driver alors que c'est l'ordre des opérations.
 *
 * ⚠️ L'ÉTAPE 5 APRÈS L'ÉTAPE 4 est le PIÈGE N°1 de cette story.
 *    `esp_lcd_rgb_panel_register_event_callbacks()` ASSIGNE les callbacks, il ne
 *    les fusionne pas (esp_lcd_panel_rgb.c:444-448) : le dernier appelant efface
 *    le précédent, en silence, en rendant ESP_OK. Or `lvgl_port_add_disp_rgb()`
 *    enregistre son propre `on_vsync`. Si dn_measure_attach() passait AVANT, le
 *    compteur vsync serait débranché et `fps`, la synchro du flush et toute la
 *    mesure de déchirement mesureraient du VIDE, sans un mot dans le log.
 *    D'où l'ordre, et d'où le témoin actif juste après.
 */

#include <inttypes.h>

#include "dn_asset.h"
#include "dn_bootcfg.h"
#include "dn_capteurs.h"
#include "dn_env.h"
#include "dn_console.h"
#include "dn_display.h"
#include "dn_link.h"
#include "dn_measure.h"
#include "dn_patterns.h"
#include "dn_pins.h"
#include "dn_recal.h"
#include "dn_rtc.h"
#include "dn_touch.h"
#include "dn_ui.h"
#include "esp_err.h"
#include "esp_flash.h"
#include "esp_log.h"
#include "esp_psram.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs_flash.h"

static const char *TAG = "desknode";

/*
 * ─── dn4-5 / AC1.5 : POURQUOI LA CARTE A DÉMARRÉ ────────────────────────────
 *
 * 🔴 CE QUI MANQUAIT. `esp_reset_reason()` n'était appelé NULLE PART dans
 *    `firmware/desknode/main/` (grep du 2026-08-26 : 0 occurrence) — sur une
 *    story dont le verdict est « 0 reboot non commandé ». Un uptime qui repart
 *    à zéro sans dire pourquoi ne se distingue pas d'un débranchement, d'une
 *    panique, ni d'un watchdog : les trois se ressemblent trait pour trait dans
 *    le journal, et le soak de 7 jours n'a que ce journal pour boîte noire
 *    (CONFIG_ESP_COREDUMP_ENABLE_TO_NONE=y — aucun post-mortem).
 *
 * ⚠️ CE QUE CET INSTRUMENT NE PEUT PAS VOIR, et il faut le savoir en lisant :
 *    avec CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y une panique HALTE la puce au
 *    lieu de redémarrer. Elle ne produit donc JAMAIS de `ESP_RST_PANIC` au boot
 *    suivant — puisqu'il n'y a pas de boot suivant. `ESP_RST_PANIC` ne se verra
 *    que si quelqu'un débranche après coup, et le reset sera alors `POWERON`.
 *    ⇒ la panique haltée se détecte par l'ABSENCE de battement, ⛔ pas ici.
 *    De même, un TWDT ne redémarre rien dans ce build
 *    (CONFIG_ESP_TASK_WDT_PANIC non posé) : `ESP_RST_TASK_WDT` restera muet.
 */
static const char *raison_reset_clair(esp_reset_reason_t r)
{
    switch (r) {
    case ESP_RST_POWERON:  return "POWERON (mise sous tension / débranchement)";
    case ESP_RST_EXT:      return "EXT (broche de reset externe)";
    case ESP_RST_SW:       return "SW (esp_restart — commande `reboot`)";
    case ESP_RST_PANIC:    return "PANIC (exception) ⚠️ inattendu : PANIC_PRINT_HALT=y HALTE";
    case ESP_RST_INT_WDT:  return "INT_WDT (watchdog d'interruption, 800 ms)";
    case ESP_RST_TASK_WDT: return "TASK_WDT ⚠️ inattendu : TASK_WDT_PANIC non posé";
    case ESP_RST_WDT:      return "WDT (autre watchdog)";
    case ESP_RST_DEEPSLEEP:return "DEEPSLEEP (réveil de sommeil profond)";
    case ESP_RST_BROWNOUT: return "BROWNOUT 🔴 CHUTE D'ALIMENTATION";
    case ESP_RST_SDIO:     return "SDIO";
    case ESP_RST_USB:      return "USB (reset par le périphérique USB — replug/JTAG)";
    case ESP_RST_JTAG:     return "JTAG";
    case ESP_RST_EFUSE:    return "EFUSE (erreur d'eFuse)";
    case ESP_RST_PWR_GLITCH: return "PWR_GLITCH 🔴 GLITCH D'ALIMENTATION";
    case ESP_RST_CPU_LOCKUP: return "CPU_LOCKUP";
    case ESP_RST_UNKNOWN:  return "UNKNOWN (le chip ne sait pas)";
    default:               return "??? (valeur non couverte par ce firmware)";
    }
}

static void log_socle(void)
{
    /*
     * Ce bloc existe pour AC2 : il rend LISIBLE dans le log applicatif ce que
     * le bandeau de bootloader annonce en passant.
     *
     * ⚠️ CE QU'IL NE FAUT PLUS LUI FAIRE DIRE. Ce commentaire annonçait « deux
     * sources indépendantes qui disent la même chose valent mieux qu'une ».
     * C'était vrai de la taille de flash et de la taille de PSRAM, et FAUX de
     * tout le reste : le mode et la vitesse de la PSRAM n'étaient pas
     * OBSERVÉS, ils étaient RÉIMPRIMÉS depuis les symboles Kconfig qui les ont
     * configurés (CONFIG_SPIRAM_MODE_OCT -> « OCTAL »,
     * CONFIG_SPIRAM_SPEED_80M -> « 80 MHz »). Une ligne pareille ne peut pas
     * contredire la configuration : elle EST la configuration, recopiée. La
     * présenter comme une preuve d'AC2 revenait à se citer soi-même.
     *
     * On sépare donc les deux registres, et l'étiquette le dit à chaque ligne :
     *   « mesuré : » ce que le silicium a répondu à l'exécution ;
     *   « config : » ce que le build a demandé, qui reste utile à voir mais ne
     *                prouve RIEN sur ce que la carte fait vraiment.
     * esp_psram n'expose aucune API publique de mode ni de vitesse (esp_psram.h
     * ne déclare que init/is_initialized/get_size/ptr_is_no_enc), et on refuse
     * d'aller lire des registres SPI0 non documentés pour fabriquer une
     * observation de façade. Le seul instrument qui peut réellement CONTREDIRE
     * la configuration PSRAM est la bande passante mesurée — commande `bw`.
     */
    uint32_t flash_size = 0;
    esp_err_t err = esp_flash_get_physical_size(NULL, &flash_size);
    ESP_LOGI(TAG, "──── socle ────────────────────────────────────────────");
    /* dn4-5 / AC1.5 — EN PREMIER, parce que c'est la seule ligne qui explique
     * pourquoi ce bandeau est en train d'être réimprimé. */
    ESP_LOGI(TAG, "mesuré : raison du démarrage = %s",
             raison_reset_clair(esp_reset_reason()));
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "mesuré : flash physique %" PRIu32 " o (%.0f MB)",
                 flash_size, (double)flash_size / (1024.0 * 1024.0));
    } else {
        ESP_LOGW(TAG, "taille de flash indisponible : %s", esp_err_to_name(err));
    }

#if CONFIG_SPIRAM
    /* La SEULE observation d'exécution de ce bloc PSRAM : la taille détectée
     * par le driver au démarrage. Elle peut démentir la configuration (une
     * puce absente ou plus petite se voit ici), les deux lignes suivantes non. */
    ESP_LOGI(TAG, "mesuré : PSRAM %u o détectés au démarrage",
             (unsigned)esp_psram_get_size());
    ESP_LOGI(TAG, "config : PSRAM en mode %s",
#if CONFIG_SPIRAM_MODE_OCT
             "OCTAL"
#else
             "QUAD (⚠️ inattendu sur cette carte)"
#endif
    );
    ESP_LOGI(TAG, "config : horloge PSRAM %s",
#if CONFIG_SPIRAM_SPEED_80M
             "80 MHz"
#elif CONFIG_SPIRAM_SPEED_120M
             "120 MHz (⛔ INTERDIT ici — voir sdkconfig.defaults)"
#else
             "40 MHz (⚠️ le défaut IDF : le refill DMA va manquer)"
#endif
    );
    ESP_LOGI(TAG,
             "  ⚠️ « config : » = relu du sdkconfig, PAS observé. Ces deux "
             "lignes ne peuvent pas démentir le build. Pour éprouver "
             "réellement le mode et l'horloge, mesurer le débit : `bw`.");
#else
    ESP_LOGE(TAG, "PSRAM DÉSACTIVÉE — aucun framebuffer possible");
#endif

#if CONFIG_SPIRAM_XIP_FROM_PSRAM
    ESP_LOGI(TAG, "config : XIP depuis la PSRAM ACTIVÉ (mesure A/B d'AC6, branche « avec »)");
#else
    ESP_LOGI(TAG, "config : XIP depuis la PSRAM désactivé (branche « sans » d'AC6)");
#endif
#if CONFIG_LCD_RGB_RESTART_IN_VSYNC
    ESP_LOGI(TAG, "config : LCD_RGB_RESTART_IN_VSYNC activé — la DMA est "
                  "relancée à CHAQUE VBlank, automatiquement.");
    ESP_LOGW(TAG, "  => la commande `dma` est INERTE dans ce build : le bit "
                  "qu'elle pose n'est jamais lu. Un décalage qui se recale "
                  "« après un `dma` » a en fait été rattrapé par le VBlank.");
#else
    ESP_LOGI(TAG, "config : LCD_RGB_RESTART_IN_VSYNC désactivé (défaut IDF) — "
                  "la commande `dma` agit réellement dans ce build.");
#endif
#if CONFIG_LCD_RGB_ISR_IRAM_SAFE
    /*
     * ⚠️ CLAIM RÉTROGRADÉ PAR LA MESURE, décision owner. Cette ligne a
     * longtemps enseigné : « le compteur vsync continue de compter PENDANT les
     * écritures flash ». Les mesures de la story l'ont RÉFUTÉE : le compteur
     * est AVEUGLE au défaut qu'il était censé attraper — 37,33 Hz avant le
     * stimulus, 37,45 Hz pendant. Il n'y avait rien à voir pour lui, donc son
     * mérite supposé ne s'est jamais manifesté. L'option est CONSERVÉE, mais
     * comme une précaution assumée, pas comme un acquis démontré : aucune
     * branche testée ne l'isole, celles qui s'en passaient portaient aussi un
     * bounce buffer de 19 200 px, et on ne sait donc pas à qui attribuer quoi.
     * Un bandeau de boot qui enseigne une explication réfutée est pire qu'un
     * bandeau muet — il se relit à chaque démarrage.
     */
    ESP_LOGI(TAG, "config : LCD_RGB_ISR_IRAM_SAFE activé — CONSERVÉ PAR "
                  "PRÉCAUTION, effet propre NON MESURÉ.");
    ESP_LOGI(TAG, "  (mesuré : 37,33 Hz avant le stimulus flash, 37,45 Hz "
                  "pendant — le compteur ne voit pas le défaut. Les seules "
                  "branches sans cette option portaient aussi un bounce "
                  "buffer de 19 200 px : rien n'est attribuable.)");
#else
    ESP_LOGW(TAG, "config : LCD_RGB_ISR_IRAM_SAFE désactivé — l'ISR vsync peut "
                  "être suspendue pendant une écriture flash. À noter si le "
                  "fps mesuré pendant le stimulus d'AC6 devient bizarre.");
#endif
    ESP_LOGI(TAG, "──────────────────────────────────────────────────────");
}

void app_main(void)
{
    int64_t t_boot = esp_timer_get_time();

    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);

    log_socle();

    dn_bootcfg_t cfg;
    ESP_ERROR_CHECK(dn_bootcfg_load(&cfg));
    dn_bootcfg_log(&cfg);

    /* 2. Pipeline d'affichage, rétroéclairage encore éteint (duty LEDC = 0). */
    ESP_ERROR_CHECK(dn_display_init(&cfg));

    /*
     * ─── LE REPLI DE BOUNCE SE PERSISTE, SINON IL SE REJOUE À CHAQUE BOOT ────
     * (dn4-10, 2026-08-23)
     *
     * `dn_display_init()` sait désormais REPLIER sur le `bounce_px` par défaut
     * quand la valeur de la NVS ne s'alloue pas (voir le filet, dn_display.c).
     * Sans ce bloc-ci, la carte démarrerait — mais la valeur fautive resterait
     * en NVS et le repli se rejouerait indéfiniment, avec un `cfg` qui
     * annoncerait une chose et un matériel qui en porterait une autre.
     *
     * ⚠️ On écrit en NVS PARCE QUE le boot vient de prouver, par la mesure, que
     *    la valeur ne tient pas. Ce n'est pas une préférence, c'est un CONSTAT.
     * ⛔ Et un échec d'écriture n'est PAS fatal : la carte tourne, on le dit,
     *    et le repli se rejouera au boot suivant — bruyamment.
     */
    if (dn_display_bounce_px() != (size_t)cfg.bounce_px) {
        ESP_LOGE(TAG,
                 "🔴 REPLI DE BOUNCE AU BOOT : la NVS demandait %d px, le "
                 "matériel porte %u px. La valeur demandée NE S'ALLOUE PAS dans "
                 "ce binaire.",
                 cfg.bounce_px, (unsigned)dn_display_bounce_px());
        esp_err_t err_nvs = dn_bootcfg_set_bounce_px((int)dn_display_bounce_px());
        if (err_nvs == ESP_OK) {
            ESP_LOGW(TAG,
                     "   ✅ NVS corrigée à %u px : le prochain boot sera propre. "
                     "⚠️ La valeur demandée est PERDUE — c'est voulu, elle "
                     "briquait la carte.",
                     (unsigned)dn_display_bounce_px());
        } else {
            ESP_LOGE(TAG,
                     "   ⚠️ NVS NON corrigée (%s) : le repli se REJOUERA au "
                     "prochain boot. La carte tourne, mais `cfg` mentira sur la "
                     "config de boot tant que ce n'est pas réglé à la main.",
                     esp_err_to_name(err_nvs));
        }
    }

    /* 3. L'asset. Un échec ici n'est PAS fatal : LVGL affichera le panneau
     *    « ASSET ABSENT » avec la raison exacte du refus, jamais un écran noir
     *    silencieux. On garde le verdict pour le lui passer. */
    esp_err_t asset_err = dn_asset_init();
    if (asset_err != ESP_OK) {
        ESP_LOGW(TAG,
                 "asset indisponible (%s) — la scène affichera un panneau "
                 "d'alerte plutôt qu'un écran noir trompeur",
                 esp_err_to_name(asset_err));
    }
    dn_asset_log();

    /*
     * 3 bis. LE TACTILE, AVANT LVGL — et pas par élégance.
     *
     * Le bring-up du GT911 n'a besoin que du bus I²C et de l'expander, tous deux
     * montés à l'étape 2. Le faire ICI, avant que LVGL n'existe, donne deux
     * choses : le diagnostic du tactile ne dépend pas de la bonne santé de l'UI
     * (une carte qui affiche mais ne répond pas au doigt se distingue d'une carte
     * qui ne fait ni l'un ni l'autre), et l'indev n'a plus qu'à se brancher sur
     * un contrôleur DÉJÀ prouvé vivant.
     *
     * ⚠️ NON FATAL, délibérément. Un GT911 muet ne doit pas empêcher l'écran de
     *    s'allumer : c'est justement l'écran allumé qui permettra de le
     *    diagnostiquer. La console dit alors pourquoi (`touch`).
     * ⚠️ COÛT DE BOOT : ~350 ms de délais de reset (150+150+50), fidèles à la
     *    démo Waveshare. Le rétroéclairage ne monte qu'après la première trame,
     *    donc ce retard-là ne se voit pas — il s'ajoute au « prêt en N ms ».
     */
    esp_err_t touch_err = dn_touch_init();
    if (touch_err != ESP_OK) {
        ESP_LOGE(TAG,
                 "tactile INDISPONIBLE (%s) — l'écran s'allume quand même, mais "
                 "aucune zone ne répondra. `touch` dit où la séquence a échoué.",
                 esp_err_to_name(touch_err));
    }

    /* 4. LVGL par-dessus le socle. C'est lui qui dessine désormais : le
     *    dn_pattern_draw() + present() du boot de dn1-2 a disparu d'ici, parce
     *    que le premier cycle LVGL l'aurait recouvert de toute façon. Les mires
     *    restent accessibles par la console (`ui off` puis `scene …`), ce dont
     *    AC5 a besoin. */
    ESP_ERROR_CHECK(dn_ui_init(&cfg, asset_err));

    /* 4 bis. L'indev tactile sur l'afficheur LVGL. Après dn_ui_init (il faut un
     *    `lv_display_t`), et seulement si le contrôleur a répondu. */
    if (touch_err == ESP_OK) {
        esp_err_t indev_err = dn_touch_attach_lvgl(dn_ui_display());
        if (indev_err != ESP_OK) {
            ESP_LOGE(TAG,
                     "indev tactile non branché (%s) — le GT911 vit, mais LVGL "
                     "ne le lit pas : le doigt ne fera rien.",
                     esp_err_to_name(indev_err));
        }
    }

    /* 5. Instrumentation — APRÈS LVGL (voir l'avertissement en tête de fichier). */
    ESP_ERROR_CHECK(dn_measure_attach(dn_display_panel()));
    ESP_ERROR_CHECK(dn_recal_init(dn_display_panel()));
    dn_recal_log_etat();

    /* ⚠️ TÉMOIN ACTIF, et il n'est pas décoratif : c'est la seule chose qui
     *    puisse démentir l'ordre d'enregistrement ci-dessus. Un compteur mort
     *    ici veut dire que quelque chose s'est branché après nous. */
    if (!dn_measure_vsync_alive(100)) {
        ESP_LOGE(TAG,
                 "=> le firmware continue, mais AUCUNE mesure de cette session "
                 "n'est recevable tant que ce témoin est rouge.");
    }

    /* 6. La première trame LVGL doit avoir ATTEINT la dalle avant qu'on allume.
     *    Le délai est PROPORTIONNÉ à la config (revue) : un plein écran fait
     *    640/draw_lines flushes, et chaque flush synchronisé attend jusqu'à une
     *    trame (~27 ms). Le 1 000 ms fixe de la première version était « très
     *    large » à 64 lignes… et FAUX à `lines 8` (80 flushes ≈ 1,1-2,2 s) :
     *    le boot loggeait « aucun flush LVGL » et allumait en plein dessin,
     *    pour une config NVS parfaitement légale. Plancher 1 000 ms conservé.
     *    Si le délai expire, on le DIT et on allume quand même : un écran noir
     *    muet serait pire qu'un écran qui montre le problème. */
    uint32_t ff_timeout_ms = 500 + (640u / (uint32_t)cfg.draw_lines) * 30u;
    if (ff_timeout_ms < 1000) {
        ff_timeout_ms = 1000;
    }
    if (!dn_ui_wait_first_frame(ff_timeout_ms)) {
        ESP_LOGE(TAG,
                 "aucun flush LVGL en %" PRIu32 " ms — ce qui va s'allumer "
                 "n'est PAS la scène attendue. Chercher du côté du flush, pas "
                 "de la dalle.",
                 ff_timeout_ms);
    }

    /* 7. ET SEULEMENT MAINTENANT le rétroéclairage.
     * La fréquence est LUE, pas récitée (revue) : la première version disait
     * « 5 kHz » en dur alors que le défaut compilé était passé à 24 kHz — le
     * bandeau contredisait LE résultat-titre d'AC7. Un bandeau qui enseigne un
     * fait réfuté est pire qu'un bandeau muet : il se relit à chaque boot. */
    ESP_ERROR_CHECK(dn_display_backlight_pct(100));
    ESP_LOGI(TAG,
             "rétroéclairage à %d %% (GPIO%d en LEDC 10 bits @ %d Hz). "
             "⚠️ il ne clignote pas : le clignotement était le signe de vie de "
             "P0, ce n'est plus un symptôme valide depuis P1.",
             dn_display_backlight_pct_state(), DN_PIN_BACKLIGHT,
             dn_display_backlight_freq_state());

    ESP_LOGI(TAG, "prêt en %lld ms depuis app_main",
             (long long)((esp_timer_get_time() - t_boot) / 1000));

    /*
     * ─── RECALAGE D'AMORÇAGE (2026-08-23, branche d'essai RESTART_IN_VSYNC=n) ──
     *
     * 🔴 SANS CE BLOC, L'IMAGE SORT DÉCALÉE EN PERMANENCE. C'est mesuré, et
     *    c'est le seul défaut que `CONFIG_LCD_RGB_RESTART_IN_VSYNC=y` corrigeait
     *    réellement : un décrochage de la DMA AU DÉMARRAGE — « l'image sort avec
     *    les bonnes couleurs mais coupée en deux, la partie de droite revenant
     *    sur la gauche » (affichage.md:595-598).
     *
     * ✅ ET IL SE CORRIGE PAR UN SEUL APPEL, c'est déjà prouvé : « dans cette
     *    configuration `RESTART_IN_VSYNC=n`, un appel manuel à
     *    `esp_lcd_rgb_panel_restart()` remet l'image en place D'UN COUP »
     *    (affichage.md:598-601). `dn_recal` sait le déclencher sur comptage de
     *    vsync, et dn1-3 a mesuré que **1 vsync suffit** (affichage.md:541).
     *
     * ⚠️ POURQUOI ICI, ET PAS DANS `dn_display_init()` : `dn_recal_arm()` réveille
     *    une tâche qui compte des VSYNC. Elle a besoin que le panneau TOURNE et
     *    que l'abonnement vsync de `dn_recal_init()` (étape 7) soit posé. On est
     *    donc au premier endroit où c'est vrai. ⛔ Le mettre plus tôt armerait
     *    dans le vide, sans que rien ne le dise.
     *
     * ⚠️ POURQUOI IL NE PASSE PAS PAR `dn_display_present()` COMME LES AUTRES :
     *    ce chemin-là garde l'armement derrière `num_fbs > 1` (dn_display.c:708),
     *    et nous sommes à UN framebuffer. Le recalage de bascule n'a plus lieu
     *    d'être ; celui d'AMORÇAGE, si. Ce sont deux besoins différents qui
     *    partagent un mécanisme — ⛔ ne pas « unifier » sans relire ceci.
     *
     * ⛔ CE QUE CE BLOC NE FAIT PAS : il ne rejoue rien. UN amorçage, une fois.
     *    Si l'image reste décalée, le filet est la commande console `dma`, qui
     *    REDEVIENT opérante à `n` — et `recal` publie les compteurs.
     */
    if (dn_recal_get_vsyncs() > 0) {
        dn_recal_arm();
        ESP_LOGI(TAG,
                 "recalage d'AMORÇAGE armé (%d vsync) — RESTART_IN_VSYNC=n, la "
                 "DMA n'est plus relancée à chaque VBlank",
                 dn_recal_get_vsyncs());
        ESP_LOGI(TAG,
                 "  ⚠️ si l'image sort DÉCALÉE malgré ça : `recal` pour les "
                 "compteurs, `dma` pour recaler à la main (opérante à `n`).");
    } else {
        /* ⛔ Un amorçage silencieusement désactivé livrerait une image décalée
         *    en permanence sans que rien ne dise pourquoi. */
        ESP_LOGE(TAG,
                 "🔴 recalage d'AMORÇAGE DÉSACTIVÉ (`recal 0`) alors que "
                 "RESTART_IN_VSYNC=n : l'image VA sortir décalée. `recal 1`.");
    }

    /* 8. La liaison PC (dn2-2). APRÈS dn_ui_init : sa tâche pousse l'état vers
     * les cinq cases PC par dn_ui_pc_maj(), qui prend le verrou LVGL elle-même
     * (⚠️ corrigé en revue 2026-08-18 : `dn_ui_cpu_maj` n'est plus appelée). Le
     * premier tour affiche « -- » (liaison jamais vue) — la case CPU cesse de
     * mentir dès le boot, les 5 autres restent factices jusqu'à dn3/dn4-1.
     * ⚠️ Le WiFi (branche B) ne démarre PAS ici : `wifi on` à la console — la
     * calibration PHY écrit en NVS (verrou 3), ce geste reste un choix, pas un
     * effet de bord du boot.
     *
     * 🔴 NON FATAL, ET C'EST DÉLIBÉRÉ (correctif de revue 2026-08-16). C'était un
     * ESP_ERROR_CHECK, AVANT le démarrage de la console. Or le seul mode d'échec
     * réaliste de dn_link_init est l'échec de xTaskCreate, c'est-à-dire la pénurie
     * de RAM interne — le sujet même de cette story. Avec
     * CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y, l'abort produisait EXACTEMENT le
     * « troisième état » que cette story vient d'ajouter au README : ni console,
     * ni flash, RESET physique obligatoire. Un module optionnel (une case du
     * dashboard) ne doit pas pouvoir briquer le seul outil de diagnostic. */
    esp_err_t err_link = dn_link_init();
    if (err_link != ESP_OK) {
        ESP_LOGE(TAG, "⛔ liaison PC ABSENTE (%s) — la case CPU restera « -- ». "
                      "Le reste du firmware et la console démarrent normalement.",
                 esp_err_to_name(err_link));
    }

    /* 8 bis. Les capteurs environnementaux (dn2-1). APRÈS dn_ui_init : la tâche
     * pousse vers les cases TEMP./HUMIDITE par dn_ui_ambiance_maj(), qui prend
     * le verrou LVGL elle-même. Le bus I²C, lui, existe depuis l'étape 2.
     * ⚠️ PLACÉE ICI ET PAS AVANT L'AFFICHAGE, délibérément : l'init du BME680
     * dort ~50 ms (power-up + commandes) et un capteur muet doit se diagnostiquer
     * ÉCRAN ALLUMÉ. Retarder la première image pour un module optionnel serait
     * le mauvais arbitrage — dn1-4 mesurait « prêt en 2 194 ms ».
     * 🔴 NON FATAL, même raison que dn_link_init : le seul mode d'échec réaliste
     * est xTaskCreate, c'est-à-dire la pénurie de RAM interne. Avec
     * CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y, un abort donnerait « ni console ni
     * flash, RESET physique » — un module optionnel ne doit pas pouvoir briquer
     * le seul outil de diagnostic. */
    esp_err_t err_capt = dn_capteurs_init();
    if (err_capt != ESP_OK) {
        ESP_LOGE(TAG, "⛔ capteurs ABSENTS (%s) — les cases TEMP./HUMIDITE "
                      "resteront « -- ». Le reste du firmware demarre normalement.",
                 esp_err_to_name(err_capt));
    }

    /* 8 bis (suite). Les TROIS capteurs d'environnement locaux (dn4-3) : BH1750,
     * INA219, VL6180X. APRÈS dn_capteurs_init(), et c'est une DÉPENDANCE, pas un
     * ordre arbitraire : dn_env n'a AUCUNE tâche à lui, il est cadencé par celle
     * que dn_capteurs vient de créer (voie C, §13.19.4).
     * ⚠️ L'ordre inverse serait sans conséquence — `dn_env_cycle()` se garde par
     *    `s_init_faite` — mais l'écrire dans cet ordre dit la dépendance.
     * 🔴 NON FATALE, comme les autres modules optionnels : avec
     *    CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y, un abort donnerait « ni console ni
     *    flash, RESET physique ». Trois capteurs de confort ne doivent pas
     *    pouvoir briquer le seul outil de diagnostic. */
    esp_err_t err_env = dn_env_init();
    if (err_env != ESP_OK) {
        ESP_LOGE(TAG, "⛔ dn_env DESARME (%s) — luminosite, tension et courant "
                      "resteront muets. `env` dira pourquoi.",
                 esp_err_to_name(err_env));
    }

    /* 8 ter. L'heure (dn3-2). APRÈS dn_display_init (étape 2) : le RTC est sur
     * l'UNIQUE bus I²C de la carte, et `dn_display_i2c_bus()` rend NULL tant que
     * la dalle ne l'a pas créé. APRÈS dn_ui_init aussi : la tâche pousse vers la
     * barre par `dn_ui_heure_maj()`, qui prend le verrou LVGL elle-même.
     * ⚠️ Placée ICI et pas avant l'affichage, même arbitrage que les capteurs :
     *    une horloge qui ne répond pas doit se diagnostiquer ÉCRAN ALLUMÉ.
     * 🔴 NON FATALE, exactement comme dn_link_init et dn_capteurs_init : le seul
     *    mode d'échec réaliste est xTaskCreate, c'est-à-dire la pénurie de RAM
     *    interne. Avec CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y, un abort donnerait
     *    « ni console ni flash, RESET physique » — une BARRE ne doit pas pouvoir
     *    briquer le seul outil de diagnostic. */
    esp_err_t err_rtc = dn_rtc_init();
    if (err_rtc != ESP_OK) {
        ESP_LOGE(TAG, "⛔ horloge ABSENTE (%s) — la barre affichera « --:-- "
                      "HEURE NON POSEE ». Le reste du firmware demarre "
                      "normalement, et `rtc` dira pourquoi.",
                 esp_err_to_name(err_rtc));
    }

    /* 9. La console. */
    ESP_ERROR_CHECK(dn_console_start());
    dn_console_banner();

    /* Battement de cœur : il prouve que l'application vit encore, même quand
     * l'écran est figé sur une mire statique. Sans lui, un firmware planté et
     * un firmware qui affiche correctement se ressemblent trait pour trait. */
    /*
     * ⚠️ CADENCE DE 10 s CONSERVÉE À L'IDENTIQUE, et ce n'est pas de la timidité :
     *    la recette « carte muette » du README a une durée d'écoute calibrée
     *    dessus (< 12 s d'écoute = faux positif). Changer ce chiffre ici sans
     *    changer le README rendrait la recette de survie fausse — le genre de
     *    régression qu'on ne découvre que le jour où on en a besoin.
     *
     * La ligne, elle, s'enrichit : le compteur de flushes permet de confronter
     * la cadence du label (AC2) à une source INDÉPENDANTE de LVGL. Deux horloges
     * qui disent la même chose valent mieux qu'une qui se cite elle-même.
     */
    /*
     * ─── dn4-5 / AC1.4 : `up` N'EST PAS L'UPTIME, ET ÇA SE VOIT MAINTENANT ───
     *
     * 🔴 CE QUE `s` COMPTE VRAIMENT : des TOURS DE BOUCLE × 10, ⛔ pas des
     *    secondes murales. `vTaskDelay()` est un délai RELATIF — il garantit
     *    « au moins 10 000 ms », jamais « exactement ». Tout retard de
     *    planification, toute préemption longue, tout blocage de la tâche
     *    s'AJOUTE au temps réel sans que `s` en sache rien, et l'écart
     *    s'ACCUMULE : il ne se rattrape jamais.
     *
     * ⚠️ ANODIN SUR 45 s DE CAMPAGNE, PAS SUR 604 800 s. Et `up` est très
     *    exactement le chiffre que le critère n°1 du brief exige (« une semaine
     *    H24 sans reboot »). On publie donc l'horloge murale À CÔTÉ, ⛔ pas à
     *    la place : c'est l'ÉCART entre les deux qui est le signal — il mesure
     *    la famine de planification cumulée de la tâche `app_main`.
     *
     * ⛔ LA CADENCE DE 10 s EST INCHANGÉE, et le format de la ligne n'est
     *    ENRICHI QU'EN QUEUE : la recette « carte muette » du README a sa durée
     *    d'écoute calibrée sur 10 s (< 12 s = faux positif), et tout parseur qui
     *    ancre sur le préfixe `up N s — vsync=…` continue de fonctionner.
     */
    uint32_t s = 0;
    const char *raison = raison_reset_clair(esp_reset_reason());
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(10000));
        s += 10;
        dn_flush_stats_t st;
        dn_ui_get_stats(&st);
        /* int64 : `esp_timer_get_time()` ne déborde qu'après ~292 000 ans. */
        int64_t mural_s = esp_timer_get_time() / 1000000;
        long long ecart = (long long)mural_s - (long long)s;
        ESP_LOGI(TAG,
                 "up %" PRIu32 " s — vsync=%" PRIu32 " — flush=%" PRIu32
                 " cycles=%" PRIu32 " — PSRAM libre %u o — mural %lld s "
                 "(écart %+lld s) — reset: %s",
                 s, dn_measure_vsync_count(), st.flushes, st.cycles,
                 (unsigned)dn_measure_psram_free(), (long long)mural_s, ecart,
                 raison);
    }
}

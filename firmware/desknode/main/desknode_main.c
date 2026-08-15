/*
 * DeskNode — P1 « Living PCB statique plein écran » (story dn1-2).
 *
 * Ce que ce firmware fait, dans cet ordre EXACT :
 *   1. lit la configuration de boot (num_fbs, bounce) en NVS ;
 *   2. monte le pipeline d'affichage, rétroéclairage ÉTEINT ;
 *   3. branche le compteur vsync ;
 *   4. mappe l'asset Living PCB et le copie dans le framebuffer ;
 *   5. ALLUME le rétroéclairage — et seulement là ;
 *   6. ouvre la console de mesure.
 *
 * L'étape 5 après l'étape 4 n'est pas un détail de style : l'inverse donne un
 * flash blanc ou un champ de bruit au démarrage, et on passe une heure à
 * douter du driver alors que c'est l'ordre des opérations.
 */

#include <inttypes.h>

#include "dn_asset.h"
#include "dn_bootcfg.h"
#include "dn_console.h"
#include "dn_display.h"
#include "dn_measure.h"
#include "dn_patterns.h"
#include "dn_pins.h"
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

    /* 2. Pipeline d'affichage, rétroéclairage encore éteint. */
    ESP_ERROR_CHECK(dn_display_init(&cfg));

    /* 3. Instrumentation, avant tout dessin : on veut compter dès la première
     *    trame, y compris celles qui précèdent l'image. */
    ESP_ERROR_CHECK(dn_measure_attach(dn_display_panel()));

    /* 4. L'asset. Un échec ici n'est PAS fatal : la mire de cadrage reste
     *    affichable, et c'est elle qui prouve le pipeline. On le dit fort. */
    if (dn_asset_init() != ESP_OK) {
        ESP_LOGW(TAG,
                 "asset indisponible — la scène « asset » affichera un panneau "
                 "d'alerte plutôt qu'un écran noir trompeur");
    }
    uint16_t *fb = dn_display_draw_buffer();
    /* ⚠️ Ce dessin-ci ne passe PAS par le show_scene() de la console — c'est
     * voulu, la console n'existe pas encore. Mais c'est aussi ce qui laissait
     * la trace d'AC4 mentir : jusqu'à la première commande `scene`, le bandeau
     * annonçait « scène « - » » et la première ligne `fps` sortait étiquetée
     * `scene=-`, alors qu'une image était affichée depuis le boot. C'est
     * désormais dn_pattern_draw() lui-même qui enregistre la scène, et
     * dn_pattern_last_scene() la restitue à qui affiche l'état. */
    dn_pattern_draw(fb, DN_SCENE_ASSET);
    int64_t present_us = dn_display_present();
    if (present_us < 0) {
        /* La bascule a échoué : la dalle affiche donc encore le contenu
         * d'origine du framebuffer. Allumer le rétroéclairage juste après
         * montrerait n'importe quoi — on le DIT, plutôt que de laisser
         * conclure à une panne de dalle. */
        ESP_LOGE(TAG,
                 "la première présentation a ÉCHOUÉ — ce qui va s'allumer "
                 "n'est PAS la scène « %s ». Voir le refus de draw_bitmap "
                 "juste au-dessus.",
                 dn_scene_name(DN_SCENE_ASSET));
    } else {
        ESP_LOGI(TAG, "scène « %s » présentée au boot (%lld us)",
                 dn_scene_name(dn_pattern_last_scene()), (long long)present_us);
    }
    dn_asset_log();

    /* 5. ET SEULEMENT MAINTENANT le rétroéclairage. */
    ESP_ERROR_CHECK(dn_display_backlight(true));
    ESP_LOGI(TAG,
             "rétroéclairage ON FIXE (GPIO%d). ⚠️ il ne clignote plus : le "
             "clignotement était le signe de vie de P0, ce n'est plus un "
             "symptôme valide en P1.",
             DN_PIN_BACKLIGHT);

    ESP_LOGI(TAG, "prêt en %lld ms depuis app_main",
             (long long)((esp_timer_get_time() - t_boot) / 1000));

    /* 6. La console. */
    ESP_ERROR_CHECK(dn_console_start());
    dn_console_banner();

    /* Battement de cœur : il prouve que l'application vit encore, même quand
     * l'écran est figé sur une mire statique. Sans lui, un firmware planté et
     * un firmware qui affiche correctement se ressemblent trait pour trait. */
    uint32_t s = 0;
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(10000));
        s += 10;
        ESP_LOGI(TAG, "up %" PRIu32 " s — vsync=%" PRIu32 " — PSRAM libre %u o",
                 s, dn_measure_vsync_count(), (unsigned)dn_measure_psram_free());
    }
}

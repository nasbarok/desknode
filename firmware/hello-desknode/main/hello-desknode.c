/*
 * DeskNode — P0 « hello » : la preuve que la chaîne build → flash → log série tient.
 *
 * Deux preuves, volontairement de natures différentes :
 *   1. une ligne de log applicative périodique (le CPU exécute NOTRE code) ;
 *   2. un effet PHYSIQUEMENT observable : le rétroéclairage clignote (AC5).
 *
 * Le rétroéclairage est sur GPIO6, un GPIO direct — contrairement au buzzer,
 * qui est sur EXIO8, derrière l'expander I²C TCA9554 et donc hors périmètre P0.
 *
 * Rien d'autre n'est initialisé ici : ni l'écran (ST7701S), ni le tactile
 * (GT911), ni le bus I²C. C'est le travail de dn1-2 et des marches suivantes.
 */

#include <inttypes.h>
#include <stdbool.h>

#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

/* Marqueur d'identité : c'est lui qu'on cherche dans le log pour distinguer
 * notre firmware du firmware d'usine (« RAM Test », « PCF85063 is running »). */
static const char *TAG = "desknode";

/* Waveshare ESP32-S3-Touch-LCD-2.8B — rétroéclairage de la dalle. */
#define GPIO_RETROECLAIRAGE GPIO_NUM_6

/* Demi-période du clignotement. 1 s : assez lent pour être vu sans ambiguïté,
 * assez rapide pour ne pas faire douter que ça tourne. */
#define DEMI_PERIODE_MS 1000

void app_main(void)
{
    const gpio_config_t cfg = {
        .pin_bit_mask = 1ULL << GPIO_RETROECLAIRAGE,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&cfg));

    ESP_LOGI(TAG, "DeskNode P0 - demarrage - retroeclairage sur GPIO%d", GPIO_RETROECLAIRAGE);

    bool allume = true;

    /* Cadence ABSOLUE (vTaskDelayUntil), pas relative (vTaskDelay) : un délai
     * relatif se rajoute au temps passé dans gpio_set_level + ESP_LOGI, si bien
     * que la période dérive et que le compteur de secondes finit par SAUTER une
     * valeur. Or ce compteur est justement le test de vivacité d'AC4 : il doit
     * pouvoir se vérifier « sans trou » sur une longue fenêtre, pas seulement
     * sur les vingt premières secondes. */
    TickType_t derniere_bascule = xTaskGetTickCount();

    while (true) {
        gpio_set_level(GPIO_RETROECLAIRAGE, allume ? 1 : 0);

        /* Secondes depuis le boot : le compteur DOIT s'incrémenter dans le log,
         * sinon on lit un tampon figé et non un firmware vivant (AC4). */
        const int64_t up_s = esp_timer_get_time() / 1000000;

        ESP_LOGI(TAG, "DeskNode P0 - up %" PRId64 " s - retroeclairage %s",
                 up_s, allume ? "ON" : "OFF");

        allume = !allume;
        vTaskDelayUntil(&derniere_bascule, pdMS_TO_TICKS(DEMI_PERIODE_MS));
    }
}

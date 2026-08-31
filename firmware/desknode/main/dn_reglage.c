/* DeskNode — `dn_reglage` : implémentation. Motifs complets dans `dn_reglage.h`. */

#include "dn_reglage.h"

#include <string.h>

#include "dn_env.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "nvs.h"

static const char *TAG = "dn_reglage";

/* ⚠️ LE MÊME NAMESPACE QUE `dn_veille` — `"desknode"`. ⛔ Pas un second espace :
 * `cfg reset` efface l'espace ENTIER, et deux espaces auraient produit un
 * « reset » qui n'en efface qu'un, c'est-à-dire un instrument qui ment. */
#define DN_NVS_NAMESPACE "desknode"
#define DN_KEY_BL_MANUEL "bl_manuel"
#define DN_KEY_BL_AUTO "bl_auto"

/* -1 = AUCUN niveau choisi. ⛔ Pas 0 : `bl 0` est un duty LÉGITIME (noir). */
static int s_bl_manuel = -1;
static bool s_bl_auto_voulu = DN_ENV_BL_AUTO_DEFAUT;

/* L'instrument de D4 (AC9.1 de `dn4-5`, transposé). */
static uint32_t s_ecritures;
static uint32_t s_derniere_us;

uint32_t dn_reglage_ecritures(void) { return s_ecritures; }
uint32_t dn_reglage_derniere_us(void) { return s_derniere_us; }

int dn_reglage_bl_cran(int i)
{
    if (i < 0 || i >= DN_REGLAGE_BL_CRANS) {
        return -1; /* ⛔ un ÉTAT, pas un pourcentage — le dépôt REFUSE */
    }
    /*
     * Répartition ENTIÈRE et ARRONDIE entre le plancher de lisibilité et le
     * maximum physique. ⚠️ ARRONDIE, ⛔ pas tronquée : AC7 de `dn1-3` cherchait
     * un PLANCHER lisible et une troncature l'aurait raté — même convention que
     * la mise à l'échelle d'Ambient.
     * ⇒ Avec 20 et 100 : 20 / 47 / 73 / 100.
     */
    const int bas = DN_ENV_BL_PCT_MIN;
    const int haut = DN_ENV_BL_PCT_ABS_MAX;
    return bas + ((haut - bas) * i + (DN_REGLAGE_BL_CRANS - 1) / 2)
                     / (DN_REGLAGE_BL_CRANS - 1);
}

static esp_err_t ecrire_i32(const char *cle, int32_t v)
{
    int64_t t0 = esp_timer_get_time();
    nvs_handle_t h;
    esp_err_t err = nvs_open(DN_NVS_NAMESPACE, NVS_READWRITE, &h);
    if (err != ESP_OK) {
        ESP_LOGE(TAG,
                 "nvs_open(« %s ») a echoue : %s — le reglage s'applique A "
                 "CHAUD mais NE SURVIVRA PAS au reboot.",
                 DN_NVS_NAMESPACE, esp_err_to_name(err));
        /* ⚠️ On horodate MÊME SUR ÉCHEC — sinon l'instrument publierait le coût
         *    de l'écriture PRÉCÉDENTE sous une tentative qui n'a rien écrit
         *    (patron `dn_veille`, corrigé là-bas en revue). */
        s_derniere_us = (uint32_t)(esp_timer_get_time() - t0);
        s_ecritures++;
        return err;
    }
    err = nvs_set_i32(h, cle, v);
    if (err == ESP_OK) {
        err = nvs_commit(h);
    }
    if (err != ESP_OK) {
        ESP_LOGE(TAG,
                 "ecriture NVS « %s » = %ld refusee : %s — le reglage NE "
                 "SURVIVRA PAS au reboot.",
                 cle, (long)v, esp_err_to_name(err));
    }
    nvs_close(h);
    s_derniere_us = (uint32_t)(esp_timer_get_time() - t0);
    s_ecritures++;
    return err;
}

void dn_reglage_init(void)
{
    nvs_handle_t h;
    esp_err_t err = nvs_open(DN_NVS_NAMESPACE, NVS_READONLY, &h);
    if (err != ESP_OK) {
        /* ⚠️ NORMAL AU PREMIER BOOT : l'espace n'existe pas encore. ⛔ Ce n'est
         *    pas une erreur, et le dire comme telle enverrait chercher une
         *    panne. Les défauts s'appliquent, et ils sont NOMMÉS. */
        ESP_LOGI(TAG,
                 "aucun reglage en NVS (%s) — defauts : niveau manuel NON CHOISI, "
                 "auto %s.",
                 esp_err_to_name(err), DN_ENV_BL_AUTO_DEFAUT ? "ARME" : "DESARME");
        return;
    }
    int32_t v = 0;
    if (nvs_get_i32(h, DN_KEY_BL_MANUEL, &v) == ESP_OK) {
        /* ⛔ ON REFUSE UNE VALEUR HORS BORNES PLUTÔT QUE DE L'ÉCRÊTER : une NVS
         * écrite par un binaire plus ancien (ou par `nvs` à la main) ne doit pas
         * pouvoir poser un duty que le code courant n'accepterait pas. */
        if (v >= 0 && v <= DN_ENV_BL_PCT_ABS_MAX) {
            s_bl_manuel = (int)v;
        } else {
            ESP_LOGW(TAG,
                     "« %s » = %ld est HORS BORNES [0 ; %d] — IGNORE (⛔ pas "
                     "ecrete). Le niveau reste NON CHOISI.",
                     DN_KEY_BL_MANUEL, (long)v, DN_ENV_BL_PCT_ABS_MAX);
        }
    }
    if (nvs_get_i32(h, DN_KEY_BL_AUTO, &v) == ESP_OK) {
        s_bl_auto_voulu = (v != 0);
    }
    nvs_close(h);
    ESP_LOGI(TAG, "reglages relus — niveau manuel %d %% (⛔ -1 = non choisi) · "
                  "auto VOULU %s",
             s_bl_manuel, s_bl_auto_voulu ? "ARME" : "DESARME");
}

int dn_reglage_bl_manuel(void) { return s_bl_manuel; }

esp_err_t dn_reglage_bl_manuel_ecrire(int pct)
{
    /* ⛔ LE DÉPÔT REFUSE, IL N'ÉCRÊTE PAS. */
    if (pct < 0 || pct > DN_ENV_BL_PCT_ABS_MAX) {
        return ESP_ERR_INVALID_ARG;
    }
    s_bl_manuel = pct;
    return ecrire_i32(DN_KEY_BL_MANUEL, pct);
}

bool dn_reglage_bl_auto_voulu(void) { return s_bl_auto_voulu; }

esp_err_t dn_reglage_bl_auto_ecrire(bool on)
{
    s_bl_auto_voulu = on;
    return ecrire_i32(DN_KEY_BL_AUTO, on ? 1 : 0);
}

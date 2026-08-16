/*
 * dn_wifi — maquette branche B (dn2-2). Voir dn_wifi.h pour le sens de la
 * connexion (ESP serveur) et ce que le module s'interdit de cacher.
 */

#include "dn_wifi.h"

/* Tout ce fichier ne vit que si la maquette B est compilée — verdict T5 dans
 * dn_wifi.h. Hors maquette, les stubs inline de l'en-tête répondent. */
#if CONFIG_HTTPD_WS_SUPPORT

#include <string.h>

#include "esp_event.h"
#include "esp_heap_caps.h"
#include "esp_http_server.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_wifi.h"

#include "dn_link.h"

static const char *TAG = "dn_wifi";

static dn_wifi_etat_t s_etat = DN_WIFI_OFF;
static esp_netif_t *s_netif;
static httpd_handle_t s_serveur;
static char s_ip[16] = "0.0.0.0";
static volatile uint32_t s_reconnexions;
static volatile uint32_t s_ws_messages;
static volatile uint32_t s_ws_connexions;
/* L'event loop par défaut ne se détruit pas proprement une fois des composants
 * abonnés : créé UNE fois, gardé pour la vie du firmware. Son coût est donc
 * dans le delta du PREMIER `wifi on`, et il ne revient pas au `wifi off` —
 * imprimé comme tel, pas maquillé. */
static bool s_event_loop_cree;

static void imprimer_mem(const char *etiquette, size_t *out_int, size_t *out_psram)
{
    size_t interne = heap_caps_get_free_size(MALLOC_CAP_INTERNAL);
    size_t psram = heap_caps_get_free_size(MALLOC_CAP_SPIRAM);
    printf("[verrou 1] %s : RAM interne %u o · PSRAM %u o\n", etiquette,
           (unsigned)interne, (unsigned)psram);
    if (out_int) {
        *out_int = interne;
    }
    if (out_psram) {
        *out_psram = psram;
    }
}

static void sur_evenement(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    (void)arg;
    if (base == WIFI_EVENT && id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (base == WIFI_EVENT && id == WIFI_EVENT_STA_DISCONNECTED) {
        wifi_event_sta_disconnected_t *d = (wifi_event_sta_disconnected_t *)data;
        strlcpy(s_ip, "0.0.0.0", sizeof(s_ip));
        if (s_etat != DN_WIFI_OFF) {
            s_etat = DN_WIFI_CONNEXION;
            /* Le minimum honnête : on retente TOUT DE SUITE, on compte, on ne
             * temporise pas — le backoff propre est un livrable dn4-1. */
            s_reconnexions++;
            ESP_LOGW(TAG, "deconnecte (raison %d), reconnexion n0%u", (int)d->reason,
                     (unsigned)s_reconnexions);
            esp_wifi_connect();
        }
    } else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *e = (ip_event_got_ip_t *)data;
        snprintf(s_ip, sizeof(s_ip), IPSTR, IP2STR(&e->ip_info.ip));
        s_etat = DN_WIFI_CONNECTEE;
        ESP_LOGI(TAG, "IP obtenue : %s", s_ip);
    }
}

esp_err_t dn_wifi_on(const char *ssid, const char *mdp)
{
    if (s_etat != DN_WIFI_OFF) {
        printf("wifi deja monte (%s) — `wifi off` d'abord\n",
               dn_wifi_etat_nom(s_etat));
        return ESP_ERR_INVALID_STATE;
    }
    if (strlen(ssid) >= sizeof(((wifi_config_t *)0)->sta.ssid) ||
        strlen(mdp) >= sizeof(((wifi_config_t *)0)->sta.password)) {
        printf("ssid (max 31) ou mot de passe (max 63) trop long\n");
        return ESP_ERR_INVALID_ARG;
    }

    size_t int_avant, psram_avant;
    imprimer_mem("avant pile WiFi", &int_avant, &psram_avant);

    esp_err_t err = esp_netif_init();
    if (err != ESP_OK) {
        return err;
    }
    if (!s_event_loop_cree) {
        err = esp_event_loop_create_default();
        if (err != ESP_OK) {
            return err;
        }
        s_event_loop_cree = true;
    }
    /* ⚠️ MESURÉ (2026-08-16) : un netif ORPHELIN d'un échec précédent fait
     * ASSERT esp_netif_create_default_wifi_sta (« duplicate key ») — panique,
     * carte haltée, plus de console. Chaque chemin d'erreur ci-dessous nettoie
     * donc TOUT ce qu'il a monté, et ce garde-fou solde un résidu éventuel. */
    if (s_netif) {
        esp_netif_destroy_default_wifi(s_netif);
        s_netif = NULL;
    }
    s_netif = esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    err = esp_wifi_init(&cfg);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "esp_wifi_init : %s", esp_err_to_name(err));
        esp_netif_destroy_default_wifi(s_netif);
        s_netif = NULL;
        return err;
    }
    /* Config (SSID/mdp) en RAM UNIQUEMENT : rien en NVS. La calibration PHY,
     * elle, écrira quand même — verrou 3, constaté séparément. */
    ESP_ERROR_CHECK(esp_wifi_set_storage(WIFI_STORAGE_RAM));

    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID,
                                               sur_evenement, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP,
                                               sur_evenement, NULL));

    wifi_config_t wc = {0};
    strlcpy((char *)wc.sta.ssid, ssid, sizeof(wc.sta.ssid));
    strlcpy((char *)wc.sta.password, mdp, sizeof(wc.sta.password));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wc));

    s_etat = DN_WIFI_CONNEXION;
    err = esp_wifi_start(); /* ⚠️ c'est ICI que la calibration PHY se joue */
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "esp_wifi_start : %s", esp_err_to_name(err));
        s_etat = DN_WIFI_OFF;
        esp_event_handler_unregister(WIFI_EVENT, ESP_EVENT_ANY_ID, sur_evenement);
        esp_event_handler_unregister(IP_EVENT, IP_EVENT_STA_GOT_IP, sur_evenement);
        esp_wifi_deinit();
        esp_netif_destroy_default_wifi(s_netif);
        s_netif = NULL;
        return err;
    }

    size_t int_apres, psram_apres;
    imprimer_mem("apres esp_wifi_start", &int_apres, &psram_apres);
    printf("[verrou 1] delta pile WiFi : RAM interne -%d o · PSRAM -%d o\n",
           (int)(int_avant - int_apres), (int)(psram_avant - psram_apres));
    printf("           (la connexion continue en fond — `wifi info` pour l'IP,\n");
    printf("            re-`mem` une fois CONNECTEE : les tampons RX vivent aussi)\n");
    return ESP_OK;
}

esp_err_t dn_wifi_off(void)
{
    if (s_etat == DN_WIFI_OFF) {
        printf("wifi deja arrete\n");
        return ESP_ERR_INVALID_STATE;
    }
    size_t int_avant, psram_avant;
    imprimer_mem("avant demontage", &int_avant, &psram_avant);

    dn_wifi_ws_off();
    s_etat = DN_WIFI_OFF; /* AVANT disconnect : le handler ne doit pas retenter */
    esp_wifi_disconnect();
    esp_wifi_stop();
    esp_event_handler_unregister(WIFI_EVENT, ESP_EVENT_ANY_ID, sur_evenement);
    esp_event_handler_unregister(IP_EVENT, IP_EVENT_STA_GOT_IP, sur_evenement);
    esp_wifi_deinit();
    if (s_netif) {
        esp_netif_destroy_default_wifi(s_netif);
        s_netif = NULL;
    }
    strlcpy(s_ip, "0.0.0.0", sizeof(s_ip));

    size_t int_apres, psram_apres;
    imprimer_mem("apres demontage", &int_apres, &psram_apres);
    printf("[verrou 1] rendu par `wifi off` : RAM interne +%d o · PSRAM +%d o\n",
           (int)(int_apres - int_avant), (int)(psram_apres - psram_avant));
    printf("           (event loop et esp_netif_init ne se rendent pas — assume)\n");
    return ESP_OK;
}

/* ── Le serveur WebSocket ────────────────────────────────────────────────── */

static esp_err_t ws_handler(httpd_req_t *req)
{
    if (req->method == HTTP_GET) {
        /* La poignée de main vient d'aboutir : un client de plus. */
        s_ws_connexions++;
        ESP_LOGI(TAG, "client WebSocket connecte (n0%u)", (unsigned)s_ws_connexions);
        return ESP_OK;
    }
    httpd_ws_frame_t trame = {0};
    trame.type = HTTPD_WS_TYPE_TEXT;
    esp_err_t err = httpd_ws_recv_frame(req, &trame, 0); /* longueur d'abord */
    if (err != ESP_OK) {
        return err;
    }
    /* Un message v1 fait ~30 octets. 127 = déjà du bruit, mais on le LIT pour
     * le compter (dn_link le classera) ; au-delà, refuser ferme la connexion —
     * un flot pareil n'est pas une trame coupée, c'est un autre protocole. */
    char tampon[128];
    if (trame.len >= sizeof(tampon)) {
        ESP_LOGW(TAG, "message WS de %u o refuse (max %u)", (unsigned)trame.len,
                 (unsigned)(sizeof(tampon) - 1));
        return ESP_ERR_INVALID_SIZE;
    }
    trame.payload = (uint8_t *)tampon;
    err = httpd_ws_recv_frame(req, &trame, sizeof(tampon) - 1);
    if (err != ESP_OK) {
        return err;
    }
    tampon[trame.len] = '\0';
    /* L'agent termine ses lignes par '\n' quel que soit le transport : on
     * l'ôte, dn_link juge la ligne nue. */
    for (size_t i = trame.len; i > 0 && (tampon[i - 1] == '\n' || tampon[i - 1] == '\r');
         i--) {
        tampon[i - 1] = '\0';
    }
    s_ws_messages++;
    dn_link_ingest_ligne(tampon);
    return ESP_OK;
}

esp_err_t dn_wifi_ws_on(void)
{
    if (s_etat == DN_WIFI_OFF) {
        printf("pas de WiFi — `wifi on <ssid> <mdp>` d'abord\n");
        return ESP_ERR_INVALID_STATE;
    }
    if (s_serveur) {
        printf("serveur WebSocket deja lance\n");
        return ESP_ERR_INVALID_STATE;
    }
    size_t int_avant;
    imprimer_mem("avant serveur WS", &int_avant, NULL);

    httpd_config_t cfg = HTTPD_DEFAULT_CONFIG();
    cfg.server_port = 80;
    cfg.max_uri_handlers = 1;
    /* MESURÉ (2026-08-16) : sans purge, les sockets d'un client TUÉ NET restent
     * ouvertes côté serveur, les poignées de main suivantes tombent en
     * « timed out during handshake » et la RAM interne fond (6 407 → 3 795 o).
     * La reprise après coupure brutale — AC7 — était IMPOSSIBLE. La purge LRU
     * ferme la plus ancienne session quand une nouvelle frappe à guichet plein. */
    cfg.lru_purge_enable = true;
    esp_err_t err = httpd_start(&s_serveur, &cfg);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "httpd_start : %s", esp_err_to_name(err));
        s_serveur = NULL;
        return err;
    }
    static const httpd_uri_t uri_dn = {
        .uri = "/dn",
        .method = HTTP_GET,
        .handler = ws_handler,
        .is_websocket = true,
    };
    ESP_ERROR_CHECK(httpd_register_uri_handler(s_serveur, &uri_dn));

    size_t int_apres;
    imprimer_mem("apres serveur WS", &int_apres, NULL);
    printf("[verrou 1] delta serveur WS : RAM interne -%d o — ws://%s:80/dn\n",
           (int)(int_avant - int_apres), s_ip);
    return ESP_OK;
}

esp_err_t dn_wifi_ws_off(void)
{
    if (!s_serveur) {
        return ESP_ERR_INVALID_STATE;
    }
    httpd_stop(s_serveur);
    s_serveur = NULL;
    printf("serveur WebSocket arrete\n");
    return ESP_OK;
}

bool dn_wifi_ws_actif(void) { return s_serveur != NULL; }

/* ── Accesseurs ──────────────────────────────────────────────────────────── */

dn_wifi_etat_t dn_wifi_etat(void) { return s_etat; }

const char *dn_wifi_etat_nom(dn_wifi_etat_t e)
{
    switch (e) {
    case DN_WIFI_OFF:
        return "off";
    case DN_WIFI_CONNEXION:
        return "connexion...";
    case DN_WIFI_CONNECTEE:
        return "CONNECTEE";
    default:
        return "?";
    }
}

const char *dn_wifi_ip(void) { return s_ip; }

int dn_wifi_rssi(void)
{
    if (s_etat != DN_WIFI_CONNECTEE) {
        return 0;
    }
    wifi_ap_record_t ap;
    if (esp_wifi_sta_get_ap_info(&ap) != ESP_OK) {
        return 0;
    }
    return ap.rssi;
}

uint32_t dn_wifi_reconnexions(void) { return s_reconnexions; }
uint32_t dn_wifi_ws_messages(void) { return s_ws_messages; }
uint32_t dn_wifi_ws_connexions(void) { return s_ws_connexions; }

#endif /* CONFIG_HTTPD_WS_SUPPORT */

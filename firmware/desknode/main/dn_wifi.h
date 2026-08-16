#pragma once
/*
 * dn_wifi — la MAQUETTE de la branche B (dn2-2) : WiFi STA + serveur WebSocket.
 *
 * ── LE SENS DE LA CONNEXION : l'ESP est SERVEUR, l'agent Windows est CLIENT ──
 * Décision d'architecture de la story (§8) : un port en écoute sur Windows,
 * atteint depuis le LAN, demanderait une règle de pare-feu entrante ; le
 * SORTANT est autorisé par défaut. Et la tour a TROIS tunnels (Surfshark
 * WireGuard en profil Public, OpenVPN DCO, Tailscale) : « l'IP du PC » est une
 * hypothèse, celle de l'ESP sur le LAN 2,4 GHz n'en est pas une.
 * Bonus : ESP serveur = esp_http_server DÉJÀ dans l'IDF (CONFIG_HTTPD_WS_SUPPORT),
 * zéro composant du registre — le chemin le moins coûteux en dépendances.
 *
 * ── CE QUE CE MODULE NE CACHE PAS ────────────────────────────────────────────
 * · `dn_wifi_on()` imprime la RAM interne et la PSRAM AVANT et APRÈS : c'est le
 *   VERROU 1 de la fourche (117 995 o de RAM interne au départ), mesuré au
 *   moment où il se joue, pas reconstitué après coup.
 * · La config WiFi est posée en RAM (esp_wifi_set_storage(WIFI_STORAGE_RAM)) :
 *   ni le SSID ni le mot de passe ne touchent la NVS. ⚠️ La calibration PHY,
 *   ELLE, écrit en NVS au premier esp_wifi_start() (phy_init.c:853/861) — c'est
 *   le VERROU 3, constaté puis arbitré par la story, pas contourné en douce.
 * · Reconnexion = le minimum honnête de dn2-2 : un esp_wifi_connect() immédiat
 *   à chaque déconnexion, compté. Pas de backoff — c'est écrit, et c'est dn4-1.
 *
 * Le serveur WebSocket se démarre SÉPARÉMENT (dn_wifi_ws_on) : le verrou 1
 * mesure d'abord la pile WiFi seule, puis le coût du serveur — une variable à
 * la fois.
 */

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include "esp_err.h"
#include "sdkconfig.h"

typedef enum {
    DN_WIFI_OFF,       /* pile non initialisée — l'état du boot */
    DN_WIFI_CONNEXION, /* start/connect lancés, pas encore d'IP */
    DN_WIFI_CONNECTEE, /* IP obtenue */
} dn_wifi_etat_t;

/*
 * 🔴 VERDICT T5 (2026-08-16) : LA MAQUETTE B N'EST PLUS COMPILÉE PAR DÉFAUT.
 * La fourche transport est tranchée USB série (branche A) sur BLOCAGE MESURÉ du
 * verrou 1 : en config par défaut la pile laissait 6 407 o de RAM interne
 * (3 795 sous churn de reconnexion — réserve DMA 32 768 o violée) ; en variante
 * SPIRAM_TRY_ALLOCATE_WIFI_LWIP, `esp_wifi_init : ESP_ERR_NO_MEM` (« Expected
 * to init 16 rx buffer, actual is 4 ») — la pile ne DÉMARRE pas. Le simple
 * LINK coûtait déjà 53 480 o de .bss interne et 583 664 o de flash.
 * POUR RE-MESURER (renverser la décision) : re-ajouter esp_wifi/esp_netif/
 * esp_event/esp_http_server aux REQUIRES du CMakeLists et CONFIG_HTTPD_WS_SUPPORT=y
 * aux defaults (`rm sdkconfig && idf.py build`). Chiffres : hardware/ §12.
 */
#if !CONFIG_HTTPD_WS_SUPPORT

static inline esp_err_t dn_wifi_on(const char *ssid, const char *mdp)
{
    (void)ssid;
    (void)mdp;
    printf("maquette B (WiFi) NON COMPILEE — ecartee par la fourche T5 (verrou 1 :\n"
           "6 407 o restants en defaut, ESP_ERR_NO_MEM en variante SPIRAM).\n"
           "Re-mesure : REQUIRES esp_wifi/esp_netif/esp_event/esp_http_server +\n"
           "CONFIG_HTTPD_WS_SUPPORT=y, `rm sdkconfig && idf.py build` (hardware/ §12).\n");
    return ESP_ERR_NOT_SUPPORTED;
}
static inline esp_err_t dn_wifi_off(void) { return ESP_ERR_NOT_SUPPORTED; }
static inline esp_err_t dn_wifi_ws_on(void) { return dn_wifi_on("", ""); }
static inline esp_err_t dn_wifi_ws_off(void) { return ESP_ERR_NOT_SUPPORTED; }
static inline bool dn_wifi_ws_actif(void) { return false; }
static inline dn_wifi_etat_t dn_wifi_etat(void) { return DN_WIFI_OFF; }
static inline const char *dn_wifi_etat_nom(dn_wifi_etat_t e)
{
    (void)e;
    return "non compilee (maquette B ecartee — fourche T5)";
}
static inline const char *dn_wifi_ip(void) { return "0.0.0.0"; }
static inline int dn_wifi_rssi(void) { return 0; }
static inline uint32_t dn_wifi_reconnexions(void) { return 0; }
static inline uint32_t dn_wifi_ws_messages(void) { return 0; }
static inline uint32_t dn_wifi_ws_connexions(void) { return 0; }

#else /* CONFIG_HTTPD_WS_SUPPORT — la maquette B est compilée (re-mesure) */

/* Monte la pile (netif + event loop + esp_wifi), config en RAM, connecte au
 * SSID. Imprime les deltas mémoire. Refuse si déjà montée. */
esp_err_t dn_wifi_on(const char *ssid, const char *mdp);
/* Arrête tout (serveur WS compris), démonte la pile, imprime ce qui revient. */
esp_err_t dn_wifi_off(void);

/* Serveur WebSocket sur /dn, port 80. Chaque message TEXTE est une ligne de
 * trame passée à dn_link_ingest_ligne(). Refuse si le WiFi n'est pas monté. */
esp_err_t dn_wifi_ws_on(void);
esp_err_t dn_wifi_ws_off(void);
bool dn_wifi_ws_actif(void);

dn_wifi_etat_t dn_wifi_etat(void);
const char *dn_wifi_etat_nom(dn_wifi_etat_t e);
/* IP courante en texte (« 0.0.0.0 » tant que DN_WIFI_CONNECTEE n'est pas là). */
const char *dn_wifi_ip(void);
/* RSSI de l'AP courant en dBm, 0 si non connecté. */
int dn_wifi_rssi(void);
uint32_t dn_wifi_reconnexions(void);
uint32_t dn_wifi_ws_messages(void);
uint32_t dn_wifi_ws_connexions(void);

#endif /* CONFIG_HTTPD_WS_SUPPORT */

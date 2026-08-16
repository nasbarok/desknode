#pragma once
/*
 * dn_link — la liaison PC de DeskNode (dn2-2) : réception, parsing, horodatage,
 * compteurs, état de liaison. Le TRANSPORT n'habite pas ici : la branche A (USB
 * série) entre par la commande console `pc $DN,…` (l'agent parle le dialecte du
 * REPL), la branche B (WiFi WebSocket) entre par dn_wifi qui appelle
 * dn_link_ingest_ligne() à chaque message. dn_link ne sait pas d'où vient la
 * trame — et c'est voulu : la fourche transport (AC5) se tranche sans le réécrire.
 *
 * ── LE PROTOCOLE DE TRAME, VERSION 1 — fait foi avec agent/dn_agent.py ────────
 *
 *      $DN,<ver>,<seq>,<t_ms>,cpu,<dixiemes>*<CK>
 *
 *  $DN         marqueur de début. Une ligne qui ne commence pas par « $DN, »
 *              n'atteint jamais ce module (le REPL la traite en commande, le
 *              WebSocket la compte en rejet de format).
 *  <ver>       version du protocole, entier décimal. Ici : 1. Toute autre
 *              version ⇒ trame REJETÉE et comptée — JAMAIS interprétée à moitié.
 *  <seq>       compteur de trames de l'agent, uint32 croissant. Un seq égal au
 *              précédent = trame DOUBLÉE : comptée, valeur NON appliquée. Un
 *              trou = pertes comptées (diagnostic ; la cadence ne fait pas foi).
 *  <t_ms>      horodatage de l'AGENT (ms depuis son démarrage, uint32). Purement
 *              diagnostique : les horloges PC/carte ne sont pas synchronisées,
 *              c'est l'HORODATAGE DE RÉCEPTION (esp_timer_get_time) qui fait
 *              foi pour l'état de la liaison (AC2/AC7).
 *  cpu         nom de la métrique. dn2-2 n'en publie qu'une ; tout autre nom est
 *              un rejet de format (dn4-1 étendra la version, pas le silence).
 *  <dixiemes>  valeur en DIXIÈMES de % : entier 0..1000 (« 153 » = 15,3 %).
 *              Entier sur le fil pour rester dans la doctrine parse_entier —
 *              pas de float à parser. Hors bornes ⇒ rejet compté.
 *  *<CK>       XOR de tous les octets entre '$' (exclu) et '*' (exclu), deux
 *              chiffres hexadécimaux MAJUSCULES. Absent ou faux ⇒ rejet compté.
 *
 *  Exemple valide : $DN,1,42,123456,cpu,153*29
 *
 * ── COMPORTEMENT FACE AU BRUIT (AC2 — chaque cas est COMPTÉ, jamais deviné) ──
 *  · tronquée (pas de « *CK » en queue)         → rejets_tronquee
 *  · checksum faux                              → rejets_checksum
 *  · version inconnue                           → rejets_version
 *  · champ absent / en trop / non numérique /
 *    métrique inconnue / hex de checksum cassé  → rejets_format
 *  · valeur hors bornes (> 1000)                → rejets_bornes
 *  · seq identique au précédent (doublon)       → doublons (valeur IGNORÉE)
 *  Une trame coupée en deux fait DEUX lignes : la première tombe en tronquée,
 *  la seconde (sans « $DN, ») en format ici — ou en « commande inconnue » du
 *  REPL côté branche A, et c'est documenté comme tel.
 *
 * ── L'ÉTAT DE LIAISON (AC7) ──────────────────────────────────────────────────
 *  Le firmware ne suppose JAMAIS la cadence de l'agent. Une seule règle, en
 *  temps absolu : âge = maintenant − horodatage de réception de la dernière
 *  trame VALIDE. Au-delà de DN_LINK_PEREMPTION_US, la liaison est MORTE et la
 *  case CPU l'affiche (« -- » grisé), au lieu de figer un chiffre qui n'a plus
 *  cours. La reprise est le chemin inverse, sans reboot.
 */

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "esp_err.h"

#define DN_LINK_PROTO_VERSION 1
/* 3 périodes nominales de l'agent (~1 Hz). Choisi court pour que l'état menteur
 * dure peu, assez long pour survivre à un hoquet d'ordonnanceur Windows. */
#define DN_LINK_PEREMPTION_US 3000000LL
/* Une trame v1 fait ~30 octets ; 63 laisse de la marge sans accepter n'importe
 * quoi. Au-delà : tronquée (le flux a perdu sa fin de ligne quelque part). */
#define DN_LINK_LIGNE_MAX 63

typedef enum {
    DN_LINK_JAMAIS,  /* aucune trame valide depuis le boot */
    DN_LINK_VIVANTE, /* dernière trame valide plus récente que la péremption */
    DN_LINK_MORTE,   /* la péremption est passée — la case doit le dire */
} dn_link_etat_t;

typedef struct {
    uint32_t recues;          /* trames VALIDES appliquées */
    uint32_t doublons;        /* seq répété — valeur ignorée */
    uint32_t pertes_seq;      /* trous de seq cumulés (diagnostic) */
    uint32_t rejets_tronquee; /* pas de « *CK » ou ligne trop longue */
    uint32_t rejets_checksum;
    uint32_t rejets_version;
    uint32_t rejets_format;   /* structure, champ absent/illisible, métrique */
    uint32_t rejets_bornes;   /* dixiemes > 1000 */
    uint32_t reprises;        /* transitions MORTE→VIVANTE (AC7) */
} dn_link_compteurs_t;

/* Démarre la tâche de poussée vers l'UI (période 250 ms, cadence en temps
 * absolu). À appeler après dn_ui_init() : la tâche parle à dn_ui par ses
 * fonctions publiques, qui prennent le verrou LVGL ELLES-MÊMES (règle du dépôt). */
esp_err_t dn_link_init(void);

/* Ingestion d'UNE ligne (sans '\n'), quelle qu'en soit la provenance.
 * Renvoie true si la trame a été acceptée et appliquée. Thread-safe au niveau
 * des compteurs (uint32, écrivain unique par transport actif). */
bool dn_link_ingest_ligne(const char *ligne);

dn_link_etat_t dn_link_etat(void);
const char *dn_link_etat_nom(dn_link_etat_t e);
/* Dernière valeur VALIDE en dixièmes de % (0..1000). -1 si jamais reçue. */
int dn_link_valeur_dixiemes(void);
/* Âge de la dernière trame valide en µs (esp_timer). -1 si jamais reçue. */
int64_t dn_link_age_us(void);
/* seq et t_ms de la dernière trame valide (diagnostic). */
uint32_t dn_link_derniere_seq(void);
uint32_t dn_link_dernier_t_ms(void);

void dn_link_compteurs(dn_link_compteurs_t *out);
void dn_link_reset_compteurs(void);

/* Latence ingestion→label posé (µs), en temps absolu — le patron de
 * dn_touch_latence transposé. Ce qu'elle NE couvre PAS est déclaré dans `pc` :
 * l'échantillonnage côté PC, le vol dans le transport, et le flush LVGL suivant
 * (≤ 1 cycle, ~27 ms) ne sont pas instrumentés ici. */
void dn_link_latence(uint32_t *n, int64_t *min_us, int64_t *moy_us, int64_t *max_us);

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
 *  Exemple valide : $DN,1,42,123456,cpu,153*47
 *  ⚠️ CE CHECKSUM ÉTAIT FAUX (« *29 ») dans les TROIS endroits qui le publiaient
 *  — cet en-tête, la docstring de l'agent et §12.5 du fichier liaison-pc — jusqu'au
 *  correctif de revue du 2026-08-16. L'« exemple valide » du dépôt était donc la
 *  seule trame que le firmware REFUSE : quiconque le copiait pour tester obtenait
 *  `rejets_checksum` et concluait à une liaison cassée. Vérification :
 *  XOR(« DN,1,42,123456,cpu,153 ») = 0x47.
 *
 * ── COMPORTEMENT FACE AU BRUIT (AC2 — chaque cas est COMPTÉ, jamais deviné) ──
 *  · tronquée (pas de « *CK » en queue)         → rejets_tronquee
 *  · ligne COMPLÈTE mais trop longue            → rejets_trop_longue
 *  · checksum faux                              → rejets_checksum
 *  · version inconnue                           → rejets_version
 *  · champ absent / en trop / non numérique /
 *    métrique inconnue / hex de checksum cassé  → rejets_format
 *  · valeur hors bornes (> 1000)                → rejets_bornes
 *  · seq identique au précédent (doublon)       → doublons (valeur IGNORÉE)
 *  · saut de seq non crédible (> SAUT_MAX,
 *    y compris ARRIÈRE : agent redémarré)      → resynchros (valeur APPLIQUÉE)
 *
 *  ⚠️ CORRECTIF DE REVUE (2026-08-16) — DEUX CAUSES OPPOSÉES ÉTAIENT DANS LE MÊME
 *  SEAU. « tronquée » (le flux a perdu sa fin) et « trop longue » (l'émetteur
 *  envoie un format plus large : v2, métrique en plus) sont des diagnostics
 *  CONTRAIRES : le premier envoie chercher une perte dans le transport, le second
 *  un émetteur qui a changé. Le REPL laisse passer 128 caractères (`max_cmdline_length`)
 *  quand DN_LINK_LIGNE_MAX vaut 63 : la plage 64..128 est atteignable et arrivait
 *  en « tronquée ». Deux compteurs désormais.
 *
 *  ⚠️ CORRECTIF DE REVUE (2026-08-16) — LES REJETS D'AVANT dn_link SONT COMPTÉS AUSSI.
 *  Sur la branche A, le REPL découpe la ligne AVANT que dn_link la voie : une trame
 *  contenant un espace (un octet corrompu en 0x20) arrive en plusieurs argv, et un
 *  « $DN » tronqué avant sa virgule ne ressemble plus à une trame. Ces chemins
 *  rendaient la main sans incrémenter QUOI QUE CE SOIT — « chaque cas est compté »
 *  était donc une étiquette qui ment. dn_console appelle maintenant
 *  dn_link_compter_rejet() sur ces chemins. Reste hors compteur, et c'est écrit :
 *  la SECONDE moitié d'une trame coupée en deux, qui ne commence pas par « $DN » et
 *  tombe en « commande inconnue » du REPL — le REPL, lui, la signale bruyamment.
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
 * quoi. Au-delà : la ligne est COMPLÈTE mais trop longue (rejets_trop_longue),
 * ce qui n'est PAS le même symptôme qu'une fin de ligne perdue (rejets_tronquee). */
#define DN_LINK_LIGNE_MAX 63
/* Plafond d'un trou de seq CRÉDIBLE. Au-delà, ce n'est pas une perte : c'est un
 * émetteur qui a redémarré (seq revenu à 1, donc saut ARRIÈRE), un seq fabriqué,
 * ou du bruit. La trame reste APPLIQUÉE — son checksum, sa version et ses bornes
 * sont bons, et la refuser condamnerait la reprise sans reboot d'AC7 — mais l'écart
 * va dans `resynchros`, pas dans `pertes_seq` : compter ~4 milliards de pertes sur
 * UNE trame injectée rendait le compteur illisible (correctif de revue 2026-08-16).
 * À 1 Hz, 3 600 trous = une heure de silence : au-delà, c'est l'état de liaison qui
 * diagnostique, pas ce compteur. */
#define DN_LINK_SAUT_MAX 3600u

typedef enum {
    DN_LINK_JAMAIS,  /* aucune trame valide depuis le boot */
    DN_LINK_VIVANTE, /* dernière trame valide plus récente que la péremption */
    DN_LINK_MORTE,   /* la péremption est passée — la case doit le dire */
} dn_link_etat_t;

typedef struct {
    uint32_t recues;            /* trames VALIDES appliquées */
    uint32_t doublons;          /* seq répété — valeur ignorée */
    uint32_t pertes_seq;        /* trous de seq cumulés (diagnostic), bornés */
    uint32_t resynchros;        /* saut de seq non crédible (> DN_LINK_SAUT_MAX) :
                                 * émetteur redémarré ou seq fabriqué. La trame est
                                 * APPLIQUÉE (elle est valide), mais l'écart n'est
                                 * PAS compté en pertes — sinon une trame injectée
                                 * ferait bondir pertes_seq de ~4 milliards. */
    uint32_t rejets_tronquee;   /* pas de « *CK » en queue : la fin est perdue */
    uint32_t rejets_trop_longue;/* ligne COMPLÈTE, mais > DN_LINK_LIGNE_MAX */
    uint32_t rejets_checksum;
    uint32_t rejets_version;
    uint32_t rejets_format;     /* structure, champ absent/illisible, métrique,
                                 * saut de seq aberrant, et les rejets d'AVANT
                                 * dn_link signalés par dn_console (voir en-tête) */
    uint32_t rejets_bornes;     /* dixiemes > 1000 */
    uint32_t reprises;          /* transitions MORTE→VIVANTE (AC7) */
} dn_link_compteurs_t;

/* Cause d'un rejet constaté EN AMONT de dn_link (le REPL a déjà mutilé la ligne).
 * Existe pour que « chaque cas est compté » soit vrai sur la branche A. */
typedef enum {
    DN_LINK_REJET_FORMAT,
    DN_LINK_REJET_TRONQUEE,
} dn_link_rejet_t;

/* Démarre la tâche de poussée vers l'UI (période 250 ms, cadence en temps
 * absolu). À appeler après dn_ui_init() : la tâche parle à dn_ui par ses
 * fonctions publiques, qui prennent le verrou LVGL ELLES-MÊMES (règle du dépôt). */
esp_err_t dn_link_init(void);

/* Ingestion d'UNE ligne (sans '\n'), quelle qu'en soit la provenance.
 * Renvoie true si la trame a été acceptée et appliquée. Thread-safe au niveau
 * des compteurs (uint32, écrivain unique par transport actif). */
bool dn_link_ingest_ligne(const char *ligne);

/* Compte un rejet constaté AVANT dn_link (dn_console, quand le REPL a découpé ou
 * mutilé la ligne au point qu'elle ne peut plus être ingérée). Sans cet appel, ces
 * chemins ne laissaient AUCUNE trace et le compteur mentait par omission. */
void dn_link_compter_rejet(dn_link_rejet_t cause);

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
/* Remet à zéro compteurs et latence, et OUBLIE le seq de la dernière trame.
 * ⚠️ L'oubli du seq est un correctif de revue (2026-08-16), pas un détail : une
 * campagne encadrée par `pc reset` puis relancée avec la trame d'exemple du dépôt
 * (`$DN,1,42,…`) mesurait DU VIDE si s_seq valait déjà 42 — la trame tombait en
 * doublon et la valeur était jetée. L'outil de preuve du projet se sabotait
 * lui-même. La VALEUR et son horodatage sont conservés : `pc reset` remet les
 * compteurs à zéro, il ne tue pas la liaison en cours. */
void dn_link_reset_compteurs(void);

/* Latence ingestion→label posé (µs), en temps absolu — le patron de
 * dn_touch_latence transposé. Ce qu'elle NE couvre PAS est déclaré dans `pc` :
 * l'échantillonnage côté PC, le vol dans le transport, et le flush LVGL suivant
 * (≤ 1 cycle, ~27 ms) ne sont pas instrumentés ici.
 * ⚠️ CORRECTIF DE REVUE (2026-08-16) — L'INSTRUMENT NE POUVAIT PAS VOIR CE QU'IL
 * MESURAIT. Un échantillon n'est retenu que si dn_ui_cpu_maj a RÉELLEMENT posé le
 * texte sur un label vivant. Avant, la poussée était comptée même quand le label
 * n'existait pas (modèle REBUILD, vue détail ouverte ⇒ pointeur NULL) ou quand
 * LVGL était arrêté (`ui off`, `scene`, `tear`) : on chronométrait un geste qui
 * n'avait pas eu lieu. C'est le Trap n°2 de la story appliqué à sa propre mesure. */
void dn_link_latence(uint32_t *n, int64_t *min_us, int64_t *moy_us, int64_t *max_us);

#pragma once
/*
 * dn_link — la liaison PC de DeskNode (dn2-2) : réception, parsing, horodatage,
 * compteurs, état de liaison. Le TRANSPORT n'habite pas ici : la branche A (USB
 * série) entre par la commande console `pc $DN,…` (l'agent parle le dialecte du
 * REPL), la branche B (WiFi WebSocket) entre par dn_wifi qui appelle
 * dn_link_ingest_ligne() à chaque message. dn_link ne sait pas d'où vient la
 * trame — et c'est voulu : la fourche transport (AC5) se tranche sans le réécrire.
 *
 * ════════════════════════════════════════════════════════════════════════════
 * ── LE PROTOCOLE DE TRAME — CE FICHIER FAIT FOI (dn4-1 : v2) ─────────────────
 * ════════════════════════════════════════════════════════════════════════════
 *
 * ⛔ NE PAS RECOPIER CETTE GRAMMAIRE AILLEURS SANS RENVOI. Le dépôt a déjà
 *    publié un checksum FAUX dans TROIS fichiers d'autorité à la fois, et
 *    l'« exemple valide » du projet était la seule trame que le firmware
 *    REFUSE. `agent/dn_agent.py`, `hardware/…-liaison-pc.md` et le README
 *    RENVOIENT ici ; ils ne redéfinissent rien.
 *
 *      v1 (dn2-2, TOUJOURS ACCEPTÉE) :
 *          $DN,1,<seq>,<t_ms>,cpu,<dixiemes>*<CK>        — 6 champs, EXACTEMENT
 *
 *      v2 (dn4-1) :
 *          $DN,2,<seq>,<t_ms>,<metrique>,<v1>[,<v2>]*<CK>  — 6 OU 7 champs
 *
 * 🔴 L'EXTENSION EST ADDITIVE, ET C'EST UNE PROPRIÉTÉ TESTABLE, PAS UNE
 *    INTENTION : l'agent de dn2-2, NON MODIFIÉ, doit continuer de faire vivre
 *    la case CPU, avec `rejets_version` à ZÉRO. C'est le témoin de
 *    non-régression d'AC2 de dn4-1, et sans lui « additive » n'est qu'un mot.
 *
 * ── LES CINQ MÉTRIQUES DE v2, ET LEUR UNITÉ (toujours en DIXIÈMES) ───────────
 *
 *   nom     v1 (grandeur 0)              v2 (grandeur 1)          v2 attendue ?
 *   ─────   ──────────────────────────   ──────────────────────   ─────────────
 *   cpu     % d'utilisation   (0..1000)  GHz              (0..1000)   oui
 *   gpu     % d'utilisation   (0..1000)  °C               (0..1500)   oui
 *   ram     % d'occupation    (0..1000)  Go TOTAUX    (0..40000)      oui
 *   net     Mb/s descendant (0..1000000) Mb/s montant (0..1000000)    oui
 *   disk    Mo/s (débit total) (0..1000000)  —                          non
 *
 * 🔴 `ram` ENVOIE LE **TOTAL**, ET C'EST STRUCTUREL. L'écran affiche « 22,7 /
 *    34,2 Go », mais l'utilisé n'est PAS transmis : le firmware le DÉRIVE du
 *    pourcentage (`utilisé = v1 × v2 / 1000`, dn_ui.c). Deux nombres échantillonnés
 *    séparément afficheraient tôt ou tard deux vérités contradictoires dans le
 *    même rectangle ; ici la cohérence est structurelle, pas une discipline.
 *    ⚠️ Le total est en **GIO BINAIRES** (2^30) étiquetés « Go », comme Windows :
 *    l'écran disait 34,3 quand le Gestionnaire des tâches disait 31,9 (AC10,
 *    2026-08-18). ⛔ Ne pas « corriger » l'étiquette — voir dn_agent.py.
 *    ⚠️ Cette ligne annonçait « Go utilisés » jusqu'à la revue du 2026-08-18 :
 *    l'AUTORITÉ contredisait le code, pendant que les documents DÉRIVÉS
 *    (liaison-pc.md, README, docstring de l'agent) étaient justes. C'est
 *    exactement le dispositif « une seule source de vérité » retourné.
 *
 * 🔴 UNE TRAME PAR MÉTRIQUE, ET C'EST W3 TRANCHÉE (dn4-1) — trois raisons, dans
 *    cet ordre :
 *      1. CHAQUE MÉTRIQUE A SON PROPRE HORODATAGE DE RÉCEPTION, donc sa propre
 *         péremption, GRATUITEMENT. Une source qui meurt seule (la °C d'un GPU
 *         dont le pilote ne l'expose pas) meurt seule et honnêtement. Avec une
 *         trame unique il aurait fallu UNE horloge + un jeton « inconnu » par
 *         champ, donc une règle de grammaire de plus — et `parse_u32_strict`
 *         REFUSE un champ vide (« champ VIDE ≠ zéro », délibéré).
 *      2. LA LIGNE RESTE COURTE. Pire cas v2 mesuré au gabarit :
 *         « $DN,2,4294967295,4294967295,disk,1000000,1000000*FF » = 51 octets.
 *         `DN_LINK_LIGNE_MAX` peut donc RESTER À 63 — voir sa définition.
 *      3. UNE 10ᵉ GRANDEUR RENTRERA ENCORE. Une trame tout-en-un faisait
 *         ~96 octets et saturait la ligne pour rien.
 *    ⚠️ LE PRIX EST RÉEL ET SE MESURE : ×5 sur l'écho console de la branche A
 *       (instrument d'AC3 de dn2-2 : octets/s et lignes/s).
 *
 * 🔴 CE QUE LA FORME DE TRAME NE FAIT PAS : elle ne décorrèle RIEN. La tâche de
 *    poussée agrège ce qui est arrivé depuis son dernier réveil ; cinq trames
 *    dans la même fenêtre de 250 ms produisent UNE salve de poussées, donc UN
 *    cycle LVGL. Décorréler est un acte DÉLIBÉRÉ côté poussée
 *    (`dn_link_set_etalement`), pas une conséquence du transport.
 *
 * ── LA 2ᵉ GRANDEUR EST OPTIONNELLE, ET SON ABSENCE EST UNE DONNÉE (W10) ──────
 *
 * Une trame v2 à 6 champs dit « je connais v1, je ne connais PAS v2 ». Ce n'est
 * pas un défaut de format : c'est le seul moyen honnête de publier un GPU dont
 * le % est lisible et la température non. ⛔ Et c'est pour ça qu'il n'y a PAS de
 * jeton « inconnu » : un champ absent est absent, il ne se code pas.
 * ⇒ Côté UI, la case reste RÉELLE et la seule grandeur manquante s'affiche
 *   « -- » en gris (contrat écrit dans `dn_widget.h`).
 *
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
 *  · valeur hors bornes (plafond PAR MÉTRIQUE)  → rejets_bornes
 *  · seq identique au précédent (doublon)       → doublons (valeur IGNORÉE)
 *  · saut de seq non crédible (> SAUT_MAX,
 *    y compris ARRIÈRE : agent redémarré)      → resynchros (valeur APPLIQUÉE)
 *
 *  ⚠️ CORRECTIF DE REVUE (2026-08-16) — DEUX CAUSES OPPOSÉES ÉTAIENT DANS LE MÊME
 *  SEAU. « tronquée » (le flux a perdu sa fin) et « trop longue » (l'émetteur
 *  envoie un format plus large : v2, métrique en plus) sont des diagnostics
 *  CONTRAIRES : le premier envoie chercher une perte dans le transport, le second
 *  un émetteur qui a changé. Le REPL délivre au parseur 124 caractères de trame
 *  (MESURÉ en dn4-1, voir DN_LINK_LIGNE_MAX) quand DN_LINK_LIGNE_MAX vaut 63 : la
 *  plage 64..124 est atteignable et arrivait en « tronquée ». Deux compteurs désormais.
 *
 *  🔴 ⚠️ ILS NE SONT CONTRAIRES QUE JUSQU'À 124 — CORRECTIF DE REVUE 2026-08-19.
 *  Au-delà, LES DEUX SE CONFONDENT : une ligne émise à 125 o ou plus arrive
 *  AMPUTÉE DE SA FIN (le REPL tronque à 124), donc avec le symptôme « tronquée »,
 *  mais avec `len = 124 > DN_LINK_LIGNE_MAX` elle est comptée `rejets_trop_longue`.
 *  ⇒ **la plage réellement DISCRIMINANTE est 64..124** ; au-delà,
 *  `rejets_trop_longue` ne prouve PLUS que l'émetteur a envoyé large — il peut
 *  aussi dire que le transport a coupé. ⛔ Un opérateur qui voit ce compteur monter
 *  et va chercher une régression côté agent cherche peut-être au mauvais endroit.
 *  ⚠️ Cette réserve était écrite dans `dn_link.c:157-172` et PAS ici : l'AUTORITÉ
 *  contredisait le code pendant que le code était juste — l'inverse exact du
 *  dispositif « une seule source de vérité » sur lequel AC2 repose, et le motif
 *  que dn4-1 venait de corriger pour la ligne `ram`.
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
 * ── L'ÉTAT DE LIAISON (AC7) — UNE HORLOGE PAR MÉTRIQUE (dn4-1 / W8) ──────────
 *  Le firmware ne suppose JAMAIS la cadence de l'agent. Une seule règle, en
 *  temps absolu : âge = maintenant − horodatage de réception de la dernière
 *  trame VALIDE **de cette métrique**. Au-delà de DN_LINK_PEREMPTION_US, elle est
 *  MORTE et sa case l'affiche (« -- » grisé), au lieu de figer un chiffre qui n'a
 *  plus cours. La reprise est le chemin inverse, sans reboot.
 *
 *  🔴 CINQ HORLOGES, PAS UNE — et ça ne coûte rien parce que la trame est déjà
 *     par métrique (W3). Une source qui s'arrête seule s'éteint seule : c'est le
 *     différenciateur du brief appliqué À L'INTÉRIEUR des données PC.
 *  ⚠️ `dn_link_etat()` (sans métrique) reste le RÉSUMÉ GLOBAL, et il est défini :
 *     VIVANTE si AU MOINS UNE métrique est fraîche, MORTE si au moins une a déjà
 *     été reçue mais qu'aucune ne l'est plus, JAMAIS sinon. Il sert à `pc` et à
 *     rien d'autre — ⛔ une CASE ne se juge JAMAIS dessus, sinon quatre cases
 *     mentiraient parce que la cinquième vit.
 *
 *  ── LE SEQ EST GLOBAL, PAS PAR MÉTRIQUE, ET C'EST DÉLIBÉRÉ ──────────────────
 *  `seq` numérote les trames de L'AGENT, qui est un émetteur unique. Le suivre
 *  par métrique compterait 4 « pertes » à chaque tour de cinq trames : le
 *  compteur `pertes_seq` deviendrait un générateur de bruit au lieu d'un
 *  diagnostic. Doublons, pertes et resynchros restent donc GLOBAUX ; seuls la
 *  valeur et son horodatage sont par métrique.
 */

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "esp_err.h"

/* La version que l'agent COURANT émet, et la plus haute que ce parseur accepte.
 * ⚠️ Les DEUX sont acceptées : voir `dn_link_version_connue()`. Une v1 reste une
 * v1 — 6 champs, métrique « cpu », rien d'autre. */
#define DN_LINK_PROTO_VERSION 2
#define DN_LINK_PROTO_VERSION_MIN 1
/* 3 périodes nominales de l'agent (~1 Hz). Choisi court pour que l'état menteur
 * dure peu, assez long pour survivre à un hoquet d'ordonnanceur Windows. */
#define DN_LINK_PEREMPTION_US 3000000LL
/*
 * ── 63 EST CONSERVÉ, ET MAINTENANT C'EST MESURÉ (dn4-1 / AC2) ────────────────
 *
 * Deux nombres, et il faut les deux :
 *  · PIRE CAS D'UNE TRAME v2, au gabarit : 51 octets
 *    (« $DN,2,4294967295,4294967295,disk,1000000,1000000*FF »). 63 laisse donc
 *    12 octets de marge à la forme la plus large que la grammaire autorise.
 *  · CE QUE LE REPL DÉLIVRE RÉELLEMENT AU PARSEUR : **124 caractères de trame**
 *    (127 pour la ligne entière, « pc » + espace compris). MESURÉ le 2026-08-18
 *    en envoyant des lignes de longueur croissante et en lisant ce que le
 *    firmware RE-IMPRIME de son `argv[1]` — ⛔ PAS l'écho, qui renvoie les octets
 *    à mesure qu'ils arrivent, DONC AVANT le plafond du tampon, et qui rendait
 *    « intact » jusqu'à 127. L'instrument qui ne peut pas voir le défaut ne
 *    tranche rien.
 *
 * ⇒ La bande « ligne COMPLÈTE mais trop longue » est donc **64..124**, large de
 *   61 octets, et elle reste ATTEIGNABLE. C'est la condition pour que
 *   `rejets_trop_longue` ne devienne pas un compteur décoratif — et un compteur
 *   décoratif est un instrument qui ment.
 */
#define DN_LINK_LIGNE_MAX 63
/* Ce que le REPL délivre au parseur, MESURÉ (voir ci-dessus). Publié ici pour que
 * la bande « trop longue » se relise sans refaire la mesure. */
#define DN_LINK_REPL_LIGNE_MESUREE 124
/* ⛔ BLOC ORPHELIN SUPPRIMÉ ICI (revue 2026-08-19). Il documentait
 * `DN_LINK_SAUT_MAX`, qui a été DÉPLACÉ plus bas et redéfini en
 * `(3600u * DN_LINK_METRIQUES)` avec son propre commentaire à jour. Le paragraphe
 * était resté sur place, accroché à l'énumération ci-dessous qui n'a aucun rapport,
 * et il publiait encore « À 1 Hz, 3 600 trous = une heure de silence » — la valeur
 * que le déplacement corrigeait. Deux paragraphes contradictoires sur le même seuil
 * dans le même en-tête. ⇒ voir la définition de `DN_LINK_SAUT_MAX` plus bas. */
typedef enum {
    DN_LINK_JAMAIS,  /* aucune trame valide depuis le boot */
    DN_LINK_VIVANTE, /* dernière trame valide plus récente que la péremption */
    DN_LINK_MORTE,   /* la péremption est passée — la case doit le dire */
} dn_link_etat_t;

/*
 * ── LES MÉTRIQUES DE v2 ──────────────────────────────────────────────────────
 * ⚠️ L'ORDRE DE CETTE ÉNUMÉRATION EST UN CONTRAT INTERNE À dn_link : il ne
 *    correspond PAS aux index de case de `dn_ui` et ne doit jamais être supposé
 *    tel. La correspondance vit dans `dn_ui.c`, dans une TABLE, explicitement.
 *    (Le dépôt a déjà payé trois tables « câblées par index » qui mentaient.)
 */
typedef enum {
    DN_LINK_M_CPU = 0,
    DN_LINK_M_GPU,
    DN_LINK_M_RAM,
    DN_LINK_M_NET,
    DN_LINK_M_DISK,
    DN_LINK_METRIQUES,
} dn_link_metrique_t;

/* ⚠️ CE SEUIL EST EN **TRAMES**, ET LA CADENCE A ÉTÉ ×5 PAR W3 (revue 2026-08-18).
 * 3600 valait ~60 min quand dn2-2 émettait 1 trame/s. dn4-1 émet CINQ trames par
 * seconde (une par métrique, `seq` étant GLOBAL) ⇒ le même 3600 ne couvrait plus
 * que **~12 min**. Un trou plus long basculait donc de `resynchros` vers
 * `pertes_seq` bien plus tôt qu'avant : le diagnostic changeait de sens sans le
 * dire. ⇒ Exprimé en trames À LA CADENCE RÉELLE, pour que « ~1 h » reste « ~1 h ».
 * ⚠️ IL EST DÉFINI **APRÈS** l'énumération, et c'est délibéré : il s'appuie sur
 *    `DN_LINK_METRIQUES`. Le placer avant compilait (une macro s'expanse au point
 *    d'usage) mais aurait cassé au premier usage intra-en-tête. */
#define DN_LINK_SAUT_MAX (3600u * DN_LINK_METRIQUES)

/* L'instantané d'UNE métrique, pris sous le verrou en UNE fois — c'est le point.
 * Lire la valeur puis l'horodatage par deux appels laisserait afficher une
 * valeur neuve avec un âge périmé, ou l'inverse. */
typedef struct {
    dn_link_etat_t etat;
    int v1;          /* dixièmes, -1 si jamais reçue */
    int v2;          /* dixièmes, valable seulement si `v2_connue` */
    bool v2_connue;  /* W10 : la trame portait-elle une 2ᵉ grandeur ? */
    int64_t age_us;  /* -1 si jamais reçue */
    /* 🔴 L'INSTANT DE RÉCEPTION EN ABSOLU — ajouté par la revue du 2026-08-19.
     * `age_us` est un ÂGE, calculé à l'intérieur de `dn_link_vue()` : le
     * reconstruire chez l'appelant (`t_pris_avant − age_us`) décalait l'origine de
     * tout le temps passé DANS `dn_link_vue()` — spin sur le verrou, et surtout
     * toute préemption par la tâche LVGL, de priorité supérieure, qui peut rendre
     * un cycle complet (~26,7 ms) voire un `build_scene()` (307-322 ms). La
     * latence publiée valait donc `vraie + δ`, avec δ NON BORNÉ par le haut : une
     * préemption au mauvais endroit fabriquait un maximum imputé au verrou LVGL
     * alors que le verrou n'y était pour rien — dans l'instrument même dont AC7
     * fait dépendre l'attribution de §13.11.4.
     * ⇒ On rend l'origine, pas un âge. ⛔ Ne pas la recalculer chez l'appelant. */
    int64_t recu_us;  /* -1 si jamais reçue */
    uint32_t seq;    /* seq de la trame qui a posé cette valeur (diagnostic) */
} dn_link_vue_t;

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
    uint32_t rejets_trop_longue;/* ligne > DN_LINK_LIGNE_MAX. ⚠️ « COMPLÈTE » n'est
                                 * garanti que jusqu'à 124 o : au-delà le REPL a
                                 * tronqué, et ce compteur se confond avec
                                 * `rejets_tronquee` (revue 2026-08-19). */
    uint32_t rejets_checksum;
    uint32_t rejets_version;
    uint32_t rejets_format;     /* structure, champ absent/illisible, métrique,
                                 * saut de seq aberrant, et les rejets d'AVANT
                                 * dn_link signalés par dn_console (voir en-tête) */
    uint32_t rejets_bornes;     /* hors du plafond de SA metrique (k_metriques[]) :
                                 * 1000 pour un %, 1500 pour une °C, 40000 pour
                                 * les Go, 1000000 pour Mb/s et Mo/s. ⛔ PAS un
                                 * seuil unique a 1000 — corrige en revue 2026-08-18,
                                 * le commentaire datait de la v1 mono-metrique. */
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

/* Le RÉSUMÉ GLOBAL — VIVANTE si au moins UNE métrique est fraîche. ⛔ Ne jamais
 * en juger une CASE : quatre cases mentiraient parce que la cinquième vit. */
dn_link_etat_t dn_link_etat(void);
const char *dn_link_etat_nom(dn_link_etat_t e);
/* L'état d'UNE métrique — c'est CELUI-CI qu'une case doit lire. */
dn_link_etat_t dn_link_etat_metrique(dn_link_metrique_t m);
/* Le nom de la métrique tel qu'il circule SUR LE FIL. RELU de la table du
 * parseur, jamais récité : c'est elle qui fait foi, ici comme dans la console. */
const char *dn_link_metrique_nom(dn_link_metrique_t m);
/* L'unité affichable de chaque grandeur (diagnostic console). NULL si aucune. */
const char *dn_link_metrique_unite(dn_link_metrique_t m, int grandeur);
/* Une 2ᵉ grandeur est-elle ATTENDUE pour cette métrique ? Sert à distinguer
 * « elle n'existe pas » (disk) de « elle existe mais la source ne la donne pas »
 * (gpu sans °C) — deux silences très différents. */
bool dn_link_metrique_v2_attendue(dn_link_metrique_t m);
/* L'instantané cohérent d'une métrique. Rend false si `m` est hors bornes. */
bool dn_link_vue(dn_link_metrique_t m, dn_link_vue_t *out);

/* Dernière valeur VALIDE du % CPU en dixièmes (0..1000). -1 si jamais reçue.
 * ⚠️ CONSERVÉE POUR CE QU'ELLE EST : le raccourci de dn2-2 vers la métrique CPU.
 *    Un nouvel appelant passe par `dn_link_vue()`. */
int dn_link_valeur_dixiemes(void);
/* Âge de la dernière trame valide TOUTES MÉTRIQUES CONFONDUES, en µs. -1 si
 * jamais reçue. Diagnostic global (`pc`) — pas un critère de case. */
int64_t dn_link_age_us(void);
/* seq et t_ms de la dernière trame valide, toutes métriques (diagnostic). */
uint32_t dn_link_derniere_seq(void);
uint32_t dn_link_dernier_t_ms(void);

/*
 * ── W4 : CORRÉLER OU DÉCORRÉLER LES POUSSÉES — UN A/B, DANS LE MÊME FIRMWARE ─
 *
 * `false` (défaut, « groupé ») : à chaque réveil de 250 ms, TOUTES les métriques
 *   qui ont changé sont poussées, dans le MÊME réveil de la tâche `dn_link`.
 * 🔴 ⚠️ « GROUPÉ » NE VEUT **PAS** DIRE « DANS UN SEUL CYCLE LVGL » — corrigé en
 *    revue le 2026-08-18, ce paragraphe affirmait le contraire. Chaque poussée
 *    passe par `dn_ui_pc_maj()`, qui prend **ET REND** le verrou LVGL (dn_ui.c).
 *    Cinq poussées = **CINQ verrous**, et entre deux la tâche LVGL — de priorité
 *    supérieure à la priorité 3 de `dn_link` — reprend le mutex et rend un cycle
 *    complet. ⇒ les cinq métriques se répartissent en pratique sur ~2 cycles.
 * 🔴 **C'EST LA CAUSE MÉCANIQUE DE L'ÉCART QUE §17.2 CLASSAIT « NON COUVERT »** :
 *    cycles/s mesuré à **2,05** contre **~1,2** prédit, et flush/cycle à **2,52**
 *    au lieu de 4,4 — la signature de cinq poussées étalées sur deux cycles.
 * ⚠️ Le vrai groupage (les cinq sous UN verrou, comme `widget rafale`) est une
 *    OPTION NON ADOPTÉE, renvoyée à `dn4-4` avec son A/B : il allongerait la
 *    fenêtre bloquante, donc le **PIC** — précisément ce que W4 voulait réduire.
 *    ⛔ Ne pas l'adopter par principe. Voir `deferred-work.md`.
 * `true` (« étalé ») : AU PLUS UNE métrique poussée par réveil, en tourniquet.
 *   ⇒ les cases se répartissent sur plusieurs cycles LVGL.
 *
 * 🔴 ⚠️ CE PARAGRAPHE ANNONÇAIT « ça ne réduit PAS le travail total (mêmes pixels,
 *    mêmes redessins), ça réduit le PIC ». **LA MESURE L'A DÉMENTI** (§17.4, et
 *    c'était une prémisse écrite d'avance) : le travail total **BAISSE**,
 *    **5,20 → 4,21 flush/s** — mais il baisse parce que l'étalé **JETTE 18,1 % DES
 *    MISES À JOUR** (185 poussées atteignent l'écran sur **226** trames reçues, soit
 *    **41 jetées / 226 = 18,1 %**). ⛔ **Ce n'est pas un gain, c'est une perte de
 *    données**, et la latence max est **multipliée par 4** (301 → 1 204 ms).
 *    ⚠️ Ce chiffre a été publié « 19 % » aux trois endroits jusqu'au 2026-08-19 :
 *    18,86 % est le rapport 185 sur **228** — le dénominateur de l'AUTRE branche.
 * ⛔ NE PAS LIRE UNE BAISSE DE flush/s COMME UN GAIN SUR CETTE BRANCHE.
 *    Le levier est **NON ADOPTÉ** pour cette raison. (Corrigé en revue 2026-08-18 :
 *    l'en-tête et la console publiaient encore la prémisse que §17.4 réfutait.)
 * ⚠️ CE QUE ÇA COÛTE, ÉCRIT D'AVANCE : en étalé, une métrique est rafraîchie
 *    toutes les ~1,25 s (5 métriques × 250 ms) au lieu de ~1 s, et un passage
 *    VIVANTE→MORTE met jusqu'à 1,25 s de plus à s'afficher sur les cinq cases.
 *    C'est pour ça que le DÉFAUT est « groupé » : la mesure d'AC6 se fait sur le
 *    régime nominal, pas sur une branche d'A/B.
 */
void dn_link_set_etalement(bool etale);
bool dn_link_etalement(void);

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

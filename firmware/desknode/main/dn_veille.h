/*
 * DeskNode — LA VEILLE (`Ambient`), son horloge, ses réglages et ses compteurs.
 *
 * ── CE QUE CE MODULE EST, ET SURTOUT CE QU'IL N'EST PAS ──────────────────────
 *
 * 🔴 IL NE TOUCHE NI LVGL, NI LA DALLE, NI LE RÉTROÉCLAIRAGE. Il ne fait que
 *    TENIR L'ÉTAT et DÉCIDER. Le travail visuel appartient à `dn_ui`, qui
 *    l'appelle depuis `label_tick` (l'horloge 1 Hz déjà existante dans la tâche
 *    LVGL) et agit ensuite lui-même.
 *
 *    Ce n'est pas un scrupule d'architecture : c'est ce qui rend ce fichier
 *    COMPILABLE ET APPELABLE SUR L'HÔTE. `tools/verif_veille_dn33.py` compile
 *    `dn_veille.c` sous WSL, sans carte, et APPELLE la garde de bascule — puis
 *    la MUTE et exige de la voir rougir. Un module qui appellerait `lv_*` ou
 *    `dn_display_*` ne se prêterait pas à ça, et la gate se réduirait à relire
 *    du source (« un harnais qui REJOUE au lieu d'EXTRAIRE+APPELER est une gate
 *    décorative »).
 *
 * ⛔ AUCUNE TÂCHE NEUVE. La cadence est celle de `label_tick` — 1 Hz, dans la
 *    tâche LVGL, sous le verrou. La granularité de la détection est donc de
 *    1 s, et c'est DIT : le délai mesuré tombe dans `[délai ; délai + 1 s]`,
 *    ⛔ jamais « environ ».
 *
 * ── POURQUOI PAS `dn_bootcfg` POUR LA PERSISTANCE (AC7.2) ────────────────────
 *
 * `dn_bootcfg` partage le namespace NVS « desknode », et on garde le même ici.
 * Mais son contrat écrit est « configuration lue AU BOOT » : tout ce qu'il
 * porte exige un `reboot` pour s'appliquer. Les deux réglages de veille
 * s'appliquent À CHAUD, au tap suivant. Les mélanger ferait croire qu'un
 * `veille delai 3` demande un redémarrage — et le dépôt tient qu'une étiquette
 * qui ment est un défaut à part entière.
 * ⇒ Même partition, même namespace, CLÉS DISTINCTES, module séparé.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ── Les deux états ──────────────────────────────────────────────────────── */
typedef enum {
    DN_VEILLE_ACTIF = 0, /* couleurs, rétroéclairage nominal */
    DN_VEILLE_AMBIENT,   /* nuances de gris, luminosité réduite, DONNÉES VIVES */
} dn_veille_mode_t;

const char *dn_veille_mode_nom(dn_veille_mode_t m);

/*
 * Ce que le tick demande à `dn_ui` de FAIRE. ⛔ Ce module n'agit pas lui-même.
 */
typedef enum {
    DN_VEILLE_ACTION_RIEN = 0,
    DN_VEILLE_ACTION_DORMIR, /* Actif -> Ambient, sur inactivité */
} dn_veille_action_t;

/*
 * D'où vient le dernier réveil. ⚠️ `AUCUNE` vaut 0 DÉLIBÉRÉMENT, même doctrine
 * que `DN_VAL_ABSENTE = 0` : la valeur par défaut d'un état statique doit être
 * L'AVEU D'IGNORANCE, jamais une affirmation.
 */
typedef enum {
    DN_VEILLE_ORIG_AUCUNE = 0,
    DN_VEILLE_ORIG_DOIGT,
    DN_VEILLE_ORIG_CONSOLE,
    DN_VEILLE_ORIG_MENU,
} dn_veille_origine_t;

const char *dn_veille_origine_nom(dn_veille_origine_t o);

/* ── Les quatre crans, et rien d'autre (D-5 / AC3.2) ─────────────────────── */
#define DN_VEILLE_CRANS 4

/*
 * 🔴 LES DÉFAUTS D'USINE SONT UNE DÉCISION OWNER DU 2026-08-25 (D-8), ⛔ PAS
 *    DES NOMBRES RONDS POSÉS AU JUGÉ. Leurs motifs sont écrits en toutes
 *    lettres dans `dn_veille.c`, là où ils s'appliquent.
 */
#define DN_VEILLE_ARMEE_DEFAUT true
#define DN_VEILLE_CRAN_DEFAUT 1 /* index 1 des crans -> 3 min */

/* Le cran `idx` en MINUTES, ou -1 hors bornes. LA table vit dans le `.c` et
 * nulle part ailleurs : le MENU, la console et la NVS la lisent tous d'ici. */
int dn_veille_cran_min(int idx);
/* L'index du cran valant `minutes`, ou -1 si ce n'est pas un cran.
 * ⛔ Le dépôt REFUSE et EXPLIQUE, il n'écrête pas : `veille delai 7` est un
 *    refus chiffré, jamais un arrondi silencieux vers 5. */
int dn_veille_cran_index(int minutes);

/* ── Cycle de vie ────────────────────────────────────────────────────────── */

/*
 * Relit les deux réglages en NVS. Une valeur ABSENTE ou ABERRANTE retombe sur
 * le défaut ET LE JOURNALISE (AC7.4) — « un défaut silencieux fausserait une
 * mesure sans qu'on le sache », exactement comme `dn_bootcfg_load()`.
 * Sûre à appeler avant `nvs_flash_init()` : elle journalise et garde les
 * défauts.
 */
void dn_veille_init(void);

/* ── Les DEUX réglages, et rien d'autre (AC6.6) ──────────────────────────── */
bool dn_veille_armee(void);
/* Persiste immédiatement. Un échec NVS est journalisé et RENDU : le réglage
 * s'applique quand même à chaud, mais l'appelant doit pouvoir dire qu'il ne
 * survivra pas au reboot. ⛔ Ne jamais annoncer « enregistré » sur un échec. */
esp_err_t dn_veille_set_armee(bool on);

int dn_veille_cran(void);
esp_err_t dn_veille_set_cran(int idx);

uint32_t dn_veille_delai_ms(void);

/* ── L'état courant ──────────────────────────────────────────────────────── */
dn_veille_mode_t dn_veille_mode(void);

/*
 * 🔴 LA GARDE, PURE ET SANS ÉTAT GLOBAL — C'EST ELLE QUE LA GATE MUTE.
 *
 * Elle est exposée exprès : `tools/verif_veille_dn33.py` la compile, l'appelle
 * sur les bornes (délai-1, délai, délai+1), puis la MUTE (`>=` -> `>`) et exige
 * de voir le test rougir. Une garde dont on n'a pas vu l'absence faire échouer
 * quelque chose ne prouve rien.
 *
 * ⚠️ `>=` ET PAS `>`, ET C'EST L'ARITHMÉTIQUE D'AC3.3 : `label_tick` bat à
 *    1 Hz, donc l'inactivité n'est lue qu'à des multiples de ~1 s. Avec `>`, le
 *    cran 1 min basculerait au tick où l'inactivité vaut 60 001 ms — soit
 *    61 s au lieu de 60. La fenêtre attendue est [60 ; 61] s ; `>` la
 *    décalerait à [61 ; 62] s et le chiffre publié serait faux d'une seconde
 *    entière sans que rien ne le dise.
 */
bool dn_veille_doit_dormir(bool armee, dn_veille_mode_t mode,
                           uint32_t inactivite_ms, uint32_t delai_ms);

/*
 * LE TICK 1 Hz. `inactivite_ms` vient de `lv_display_get_inactive_time(NULL)`.
 * Met à jour l'observation (secondes vues, inactivité maximale), décide, et
 * BASCULE l'état si la décision est DORMIR — l'appelant fait ensuite le travail
 * LVGL et le rétroéclairage.
 * ⚠️ Si l'appelant ne parvient PAS à programmer la transition (file
 *    `lv_async_call` pleine), il DOIT appeler `dn_veille_annuler_bascule()` :
 *    un état qui annonce AMBIENT sur un écran resté en couleurs est exactement
 *    la classe d'étiquette fausse que ce dépôt traque.
 */
dn_veille_action_t dn_veille_tick(uint32_t inactivite_ms);
void dn_veille_annuler_bascule(void);

/*
 * Bascule FORCÉE (geste d'opérateur ou MENU). ⛔ Ne passe PAS par le tick : lui
 * incrémente `secondes_vues`, l'uptime OBSERVÉ qui conditionne le diagnostic
 * d'appui fantôme. Un geste d'opérateur ne doit pas faire avancer une horloge
 * d'observation. Respecte l'armement ; rend `false` si désarmée ou déjà en
 * Ambient.
 */
bool dn_veille_forcer_dormir(void);

/* Durée de la DERNIÈRE écriture NVS, en µs, et leur nombre. Publié parce qu'un
 * tap de réglage dans le MENU écrit la flash DEPUIS LA TÂCHE LVGL : le cache est
 * coupé, la tâche stalle, ce sont des trames perdues. ⛔ Ni une raison de ne pas
 * persister, ni une raison de le taire. */
uint32_t dn_veille_persist_us(void);
uint32_t dn_veille_persist_n(void);

/*
 * Le réveil. Rend `true` si l'état a réellement changé (on était en Ambient),
 * `false` sinon — l'appelant NE DOIT PAS annoncer un réveil qui n'a pas eu
 * lieu, ni chronométrer une latence pour rien. Même contrat que
 * `dn_ui_nav_open()` et son `ESP_ERR_INVALID_STATE`.
 */
bool dn_veille_reveiller(dn_veille_origine_t origine);

/*
 * 🔴 AC8.5 — LE REBASE D'HORLOGE APRÈS UN `ui off`, COMPTÉ POUR ÊTRE DIT.
 *    `dn_ui_pause()` gèle `label_tick` mais PAS `lv_tick` : l'inactivité
 *    continue de croître pendant toute la pause. À `ui on`, une coupure plus
 *    longue que le délai ferait basculer INSTANTANÉMENT en Ambient, et
 *    l'opérateur lirait ça comme un bug de bascule. `dn_ui_resume()` appelle
 *    donc `lv_display_trigger_activity()` — et le compte ICI, parce qu'un
 *    rebase silencieux masquerait le seul cas où l'inactivité MESURÉE n'est pas
 *    l'inactivité VÉCUE. Le cas est mesuré, ⛔ pas imaginé : `dn4-13` a relevé
 *    un `ui off` de 135 s.
 */
void dn_veille_note_rebase(void);

typedef struct {
    dn_veille_mode_t mode;
    bool armee;
    int cran;              /* index 0..3 */
    uint32_t delai_ms;
    uint32_t inactivite_ms;     /* dernière lue par le tick */
    uint32_t inactivite_max_ms; /* la plus grande vue depuis le reset */
    uint32_t bascules;          /* Actif -> Ambient */
    uint32_t reveils;           /* Ambient -> Actif */
    uint32_t rebases;           /* `ui on` ayant rebasé l'horloge */
    uint32_t annulations;       /* bascules programmées puis REFUSÉES par LVGL */
    uint32_t secondes_vues;     /* ticks depuis le reset — l'uptime OBSERVÉ */
    dn_veille_origine_t origine;
} dn_veille_compteurs_t;

void dn_veille_compteurs(dn_veille_compteurs_t *out);

/*
 * 🔴 L'INSTRUMENT D'AC3.3 : L'ÉCART **DERNIER CONTACT → BASCULE**, LATCHÉ PAR LE
 *    TICK QUI A BASCULÉ.
 *
 * ⛔ AUCUN SONDAGE DEPUIS L'HÔTE NE PEUT L'ÉTABLIR : la latence série et le pas
 *    d'interrogation ajoutent leur propre seconde, et on publierait la
 *    dispersion de l'INSTRUMENT en croyant publier celle du produit. AC3.3
 *    demande la fenêtre [délai ; délai + 1 s] — elle n'est pas tranchable
 *    autrement que depuis l'intérieur.
 * ⚠️ `rang` 0 = la bascule la PLUS RÉCENTE. Rend **0** quand il n'y a pas
 *    d'échantillon à ce rang : l'appelant DOIT distinguer « pas mesuré » de
 *    « zéro milliseconde ». `dn_veille_bascule_ecarts_n()` donne le nombre
 *    d'échantillons réellement disponibles.
 * ⚠️ Une bascule ANNULÉE (async refusée) RETIRE son échantillon : elle n'a pas
 *    eu lieu, son écart n'est donc pas un écart de bascule.
 */
uint32_t dn_veille_bascule_ecart_ms(int rang);
uint32_t dn_veille_bascule_ecarts_n(void);

/*
 * 🔴 UN ÉCART NU NE SE JUGE PAS — DÉFAUT MESURÉ SUR LA CARTE LE 2026-08-25.
 *
 * La console comparait chaque écart au délai **en vigueur À LA LECTURE**. Un
 * écart de 60 400 ms, latché alors que le cran était à 1 min, s'affichait donc
 * « 🔴 HORS de [délai ; délai+1 s] » dès que le cran passait à 10 min entre la
 * bascule et le `veille`. ⇒ **Une étiquette qui ment, sur l'instrument qui
 * SOLDE AC3.3** — et le dépôt tient qu'une étiquette fausse est un défaut au
 * même titre qu'un chiffre faux (`dn_widget.h`).
 *
 * ⇒ `dn_veille_bascule_delai_ms(rang)` rend LE DÉLAI QUI ÉTAIT ARMÉ quand
 *   l'échantillon a été latché. C'est contre CELUI-LÀ qu'il se juge.
 */
uint32_t dn_veille_bascule_delai_ms(int rang);

/*
 * 🔴 ET CERTAINS ÉCHANTILLONS NE SE JUGENT PAS DU TOUT.
 *
 * Armer la veille — ou baisser le cran, ou faire `veille reset` — alors que
 * l'inactivité DÉPASSE DÉJÀ le délai fait basculer au tout premier tick, qui
 * latche l'inactivité VRAIE : **178 270 ms relevés en séance pour un cran de
 * 1 min**. La bascule est CORRECTE ; c'est la fenêtre [délai ; délai+1 s] qui
 * ne s'applique pas, faute d'avoir jamais vu d'état SOUS le seuil.
 *
 * Rend `false` pour ces échantillons-là. L'appelant DOIT les afficher comme
 * ENREGISTRÉS ET EXCLUS, avec le motif — ⛔ jamais les jeter en silence, et
 * ⛔ surtout jamais leur coller un 🔴 sur un comportement correct. C'est le
 * même contrat que `veille lat`, qui exclut les réveils console en le disant.
 */
bool dn_veille_bascule_jugeable(int rang);

/*
 * 🔴 TOUT SE REMET À ZÉRO — ⛔ un compteur CUMULATIF ne tranche pas. Le dépôt a
 *    déjà payé cette leçon sur `s_gardeh_cris` (dn4-4) puis sur `*cris`
 *    (dn4-13). ⛔ Ne remet PAS à zéro les deux RÉGLAGES : ce sont des réglages,
 *    pas des mesures.
 */
void dn_veille_reset(void);

/*
 * 🔴 LE COMPTEUR QUI ATTRAPE L'APPUI FANTÔME (AC8.2).
 *
 * Si le GT911 verrouille un `PRESSED` fantôme, `lv_display_get_inactive_time()`
 * reste collée à ~0 — elle est remise à zéro TANT QUE l'état de l'indev est
 * `PRESSED`, ⛔ pas seulement au front (`lv_indev.c:264-268`). La veille ne
 * tombe alors JAMAIS, EN SILENCE. Ce n'est pas théorique : le bus I²C se
 * dégrade ~40 s au démarrage à froid avec 55,5 % d'erreurs GT911, et le scan ne
 * le voit pas.
 *
 * Rend `true` quand la veille est ARMÉE, qu'AUCUNE bascule n'a eu lieu, que
 * l'inactivité maximale observée est restée SOUS le délai, ET qu'on a observé
 * assez longtemps pour que ce soit anormal.
 * ⚠️ LA DERNIÈRE CONDITION N'EST PAS UN DÉTAIL : sans elle, l'alerte crierait
 *    au loup à chaque boot, pendant les `délai` premières secondes — c'est-à-dire
 *    exactement quand tout est normal. « Une garde qui crie au loup à chaque
 *    passage est pire que pas de garde. »
 */
bool dn_veille_soupcon_appui_fantome(void);
/* La marge d'observation au-delà du délai avant de crier, en secondes. */
#define DN_VEILLE_MARGE_SOUPCON_S 5

/* ── Les leviers d'AC9 : réglables À CHAUD, ⛔ NON persistés ──────────────── */

/*
 * Ils ne vont PAS en NVS, et c'est un choix écrit. Ce sont des INSTRUMENTS de
 * l'A/B d'AC9 (« un A/B qui exigerait trois reflashs coûterait trois
 * observations à l'owner pour un rendement qui baisse »). Une fois l'œil passé,
 * la valeur retenue se GRAVE dans le source AVEC SON MOTIF — elle ne survit pas
 * en NVS sur une carte et pas sur une autre. Et ça garde la NVS à EXACTEMENT
 * les deux clés qu'AC7.1 décrit.
 */
int dn_veille_pct(void); /* rétroéclairage d'Ambient, en % */
esp_err_t dn_veille_set_pct(int pct);

/*
 * 🔴 LE PLANCHER DE LISIBILITÉ EST MESURÉ, ⛔ PAS DEVINÉ. 3 % est le plancher
 *    où « le Living PCB et le label s'y distinguent encore, TOUT JUSTE »
 *    (dn1-3 / AC7). `DN_ENV_BL_PCT_MIN = 8` est le plancher de la LOI
 *    d'asservissement, un autre chiffre pour un autre usage — ⛔ ne pas le
 *    recopier ici par réflexe. AC9.1 balaye 3 -> 20 et l'œil tranche.
 */
#define DN_VEILLE_PCT_MIN 3
#define DN_VEILLE_PCT_MAX 40

#ifdef __cplusplus
}
#endif

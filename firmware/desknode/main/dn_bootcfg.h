/*
 * DeskNode — configuration lue AU BOOT, modifiable depuis la console.
 *
 * Pourquoi ce détour par NVS plutôt qu'un #define ?
 *   AC4/AC5 demandent la MÊME mesure dans plusieurs configurations de
 *   framebuffer. Recompiler entre chaque variante donnerait des binaires
 *   différents — donc une variable de plus qu'on ne contrôle pas. Ici, un seul
 *   binaire, une valeur relue au boot : `set fbs 2` puis `reboot`, et le
 *   framebuffer est réalloué proprement à froid, sans fragmentation héritée de
 *   la configuration précédente.
 *
 * Ce qui NE passe PAS par ici, parce que c'est du Kconfig et que ça impose de
 * reconstruire : CONFIG_SPIRAM_XIP_FROM_PSRAM (AC6) et
 * CONFIG_LCD_RGB_RESTART_IN_VSYNC (AC5).
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include "dn_pins.h"
#include "esp_err.h"

typedef struct {
    int num_fbs;   /* 1, 2 ou 3 — `num_fbs` du panneau RGB */
    int bounce_px; /* 0 = pas de bounce buffer ; sinon taille en pixels */
    /* dn1-3 : le draw buffer de LVGL, en LIGNES d'écran (480 px de large).
     * Deux variables, donc deux clés — AC3 demande un A/B « une seule variable à
     * la fois », et un A/B qui exige un reflash en ajoute une troisième
     * (le binaire). */
    int draw_lines; /* hauteur du draw buffer LVGL, en lignes */
    int draw_psram; /* 0 = RAM interne DMA, 1 = PSRAM */
    /* Cœur d'exécution de la tâche LVGL : -1 (pas d'affinité), 0 ou 1.
     * ⚠️ Ce n'est PAS un réglage de confort. Le pipeline d'affichage entier
     *    (init du panneau, ISR vsync, chemin brut de dn1-2) vit sur le cœur 0 ;
     *    mettre le rendu en face fait travailler les deux cœurs simultanément
     *    sur la mémoire externe, ce que dn1-2 n'a jamais eu. C'est une VARIABLE
     *    DE MESURE, d'où la clé NVS. */
    int lvgl_core;
} dn_bootcfg_t;

/*
 * PLAFOND du bounce buffer — et il est DUR, parce que le dépasser BRIQUE la
 * carte. Le mécanisme, de bout en bout :
 *   le driver RGB alloue DEUX bounce buffers de `bounce_px * 2` octets chacun,
 *   en MALLOC_CAP_INTERNAL|MALLOC_CAP_DMA. `set bounce 153600` passait tous les
 *   contrôles (positif, et diviseur exact des 307 200 pixels d'une trame) et
 *   réclamait donc ~614 Ko là où il reste ~348 Ko de RAM interne libre :
 *     ESP_ERR_NO_MEM -> ESP_ERROR_CHECK dans app_main -> panique -> et comme
 *     CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y, le CPU est HALTÉ.
 *   La console n'a alors JAMAIS démarré : plus une seule commande pour annuler
 *   la valeur fautive. Et dn_bootcfg_load() la relisait telle quelle au boot
 *   suivant — le piège se réarmait tout seul, jusqu'au reflash complet.
 *
 * Pourquoi 38 400 px : la plus grosse valeur réellement mesurée par la story
 * est 19 200 px ; 38 400 laisse le double de marge tout en plafonnant à
 * 2 × 76 800 o de RAM interne, ce que la carte a. C'est aussi le dernier
 * diviseur « utile » listé par l'aide de `set bounce` (80 lignes).
 */
#define DN_BOUNCE_PX_MAX (DN_LCD_TOTAL_PX / 8) /* 38 400 px = 76 800 o/tampon */

/*
 * ─── LE PLANCHER DU FILET DE BOOT (dn4-10, decision owner du 2026-08-24) ─────
 *
 * 🔴 POURQUOI IL EXISTE. Le filet de `dn_display.c` ne s'armait QUE si la valeur
 *    demandee differait du defaut. Or `DN_DEFAULT_BOUNCE_PX` est passe a 9 600
 *    le 2026-08-23 (`1adf259`) et la NVS de la carte porte 9 600 : la condition
 *    devenait FAUSSE, donc AUCUN repli, donc panique -> CPU halte -> brick.
 *    ⚠️ AVANT ce changement, cette meme NVS ETAIT protegee — le defaut a monte
 *    d'un cran et a emporte le filet avec lui, en silence.
 *    Releve par la 2e revue de code 3 couches du 2026-08-24.
 *
 * 🎯 CE QUE LE PLANCHER GARANTIT : il y a TOUJOURS une marche SOUS la valeur
 *    demandee, y compris quand celle-ci EST le defaut.
 *
 * ⛔ POURQUOI 4 800 ET PAS AUTRE CHOSE — le choix se justifie, il ne se devine
 *    pas :
 *      1. C'est une valeur LEGALE : 4 800 = 480 x 10 lignes, et
 *         307 200 % 4 800 == 0. Les douze admissibles sont enumerees en §18.9.
 *      2. C'est la derniere marche SOUS 7 680 : « aucune n'est admissible entre
 *         4 800 et 7 680 » (README, dn4-6). Descendre plus bas serait gratuit.
 *      3. 🔴 ELLE DEMARRE, ET CE N'EST PAS UNE SUPPOSITION : c'etait le defaut
 *         du produit du 2026-08-16 au 2026-08-19, sur des jours de mesure.
 *      4. Elle coute 19 200 o de RAM interne contre 38 400 pour 9 600 — la
 *         MOITIE. Un filet dont la cible coute presque autant que ce qui vient
 *         d'echouer ne rattrape rien.
 *
 * ⚠️ ET ELLE A UN DEFAUT CONNU, ASSUME : 4 800 est l'etat qui GLISSE sous trafic
 *    serie + repeint (famine DMA, §18.9). ⛔ Le filet ne promet PAS une belle
 *    image : il promet UNE CARTE QUI DEMARRE ET UNE CONSOLE JOIGNABLE. Une
 *    image qui saute se corrige a la console ; un CPU halte, non.
 */
#define DN_BOUNCE_PX_PLANCHER 4800

/*
 * ─── LE SEUIL D'ALERTE AU BOOT, DECOUPLE DU DEFAUT (revue du 2026-08-27) ─────
 *
 * 🔴 CE QU'IL CORRIGE. La garde de lecture NVS s'ecrivait
 *    `if (v > 0 && v < DN_DEFAULT_BOUNCE_PX)` et journalisait « *c'est la valeur
 *    sous laquelle l'image GLISSE d'un cran sous trafic serie + repeint* ».
 *    Remonter le defaut a 9 600 le 2026-08-23 a fait tomber **7 680 dedans** :
 *    toute carte configuree avant ce commit criait A CHAQUE BOOT une alerte de
 *    GLISSEMENT pour une valeur que le MEME commit mesure comme fonctionnelle
 *    (« petite ligne », dn_bootcfg.c) et que le MEME fichier appelle « la plus
 *    petite valeur LEGITIME qui tienne ». UN SEUIL UNIQUE PORTAIT DEUX SENS :
 *    4 800 (reellement dangereux) et 7 680 (seulement sous-optimal) recevaient
 *    le meme message.
 *
 * 🎯 CE QUI EST VRAI, ET C'EST MESURE :
 *      - SOUS 7 680  : l'image GLISSE sous trafic serie + repeint (§18.9). Ce
 *                      fut le defaut du produit jusqu'au 2026-08-19, et c'est
 *                      pour ca qu'il a ete quitte.
 *      - 7 680       : fonctionnel, mais SOUS l'optimum mesure a
 *                      `RESTART_IN_VSYNC=n` (§20bis.6). Ce n'est pas une alerte
 *                      de defaut, c'est une alerte de reglage.
 *      - 9 600       : l'optimum mesure, et le defaut depuis `1adf259`.
 *                      ⛔ 15 360 est PIRE (« une bande qui couvre les % »).
 * ⇒ Deux seuils, deux messages. Et ce seuil-ci ne bouge PAS quand le defaut
 *   bouge : c'est tout l'objet du decouplage.
 */
#define DN_BOUNCE_PX_ALERTE 7680

/*
 * BORNES du draw buffer LVGL — mêmes raisons que le bounce buffer, mêmes dégâts
 * si on les oublie : la RAM interne est la ressource rare, et un échec
 * d'allocation au boot passe par ESP_ERROR_CHECK, donc par la panique, donc par
 * un CPU HALTÉ sans console pour revenir en arrière.
 *
 *   plancher 8 lignes  : ce qui coûte, en dessous, n'est PAS la copie — mesuré :
 *                        elle est proportionnelle à l'aire et le coût fixe par
 *                        flush est indétectable (§ dn_ui.h, contrainte 3). C'est
 *                        l'ATTENTE DE SYNCHRO : chaque flush attend son retour
 *                        vertical, donc un plein écran coûte 640/lignes trames.
 *                        À 32 lignes c'est déjà 433 ms (mesuré) ; à 8 lignes ce
 *                        serait 80 trames, soit ~2,1 s pour redessiner l'écran.
 *   plafond 160 lignes : 480 x 160 x 2 = 153 600 o. Il restait 212 015 o de RAM
 *                        interne libre juste après l'init LVGL (mesuré) : 160
 *                        lignes tiennent, mais sans marge confortable. Au-delà,
 *                        viser la PSRAM (`set drawmem 1`) — qui n'a pas cette
 *                        contrainte mais copie 1,70x plus lentement (mesuré).
 * La recommandation d'esp_lvgl_port est « au moins 1/10 d'écran », soit 64
 * lignes ici : c'est le défaut, et il est DANS les bornes, pas à leur bord.
 */
#define DN_DRAW_LINES_MIN 8
#define DN_DRAW_LINES_MAX 160

/* Charge la configuration depuis NVS. Toute valeur absente ou aberrante
 * retombe sur le défaut, et le fait est journalisé — un défaut silencieux
 * fausserait une mesure sans qu'on le sache. */
esp_err_t dn_bootcfg_load(dn_bootcfg_t *out);

esp_err_t dn_bootcfg_set_num_fbs(int num_fbs);
esp_err_t dn_bootcfg_set_bounce_px(int bounce_px);
esp_err_t dn_bootcfg_set_draw_lines(int lines);
esp_err_t dn_bootcfg_set_draw_psram(int psram);
esp_err_t dn_bootcfg_set_lvgl_core(int core);

/* Efface la configuration : le prochain boot repart sur les défauts.
 * ⛔ REMPLACEE PAR `dn_bootcfg_reset_ex()` LE 2026-08-27 (3e revue) — voir sa
 *    justification plus bas, avec le témoin de repli. L'ancienne signature ne
 *    pouvait PAS dire ce qu'il était advenu du témoin, et l'appelant l'affirmait
 *    quand même. Elle n'a plus aucun appelant. */

/*
 * ─── LE TEMOIN DE REPLI (decision owner du 2026-08-27) ──────────────────────
 *
 * 🔴 LE DEFAUT QU'IL FERME, ET IL ETAIT DECLARE DEPUIS LA 1re REVUE DE CODE.
 *    Quand le filet de `dn_display.c` replie, `desknode_main.c` REECRIT la NVS
 *    avec la valeur retenue. C'est voulu — sans ca le repli se rejoue a chaque
 *    boot et `cfg` ment. ⛔ MAIS le reglage de l'operateur etait alors DETRUIT
 *    POUR TOUJOURS, avec pour seule trace une ligne de log qui defile. Il
 *    n'existait AUCUNE cle NVS interrogeable apres coup : trois jours plus
 *    tard, personne ne pouvait dire qu'un repli avait eu lieu.
 * ⚠️ ET C'EST DEVENU PLUS MORDANT LE 2026-08-24 : avec l'ECHELLE, le repli peut
 *    atterrir sur `DN_BOUNCE_PX_PLANCHER = 4 800`, une valeur au DEFAUT VISIBLE
 *    CONNU (l'image glisse, §18.9). La carte demarre, l'image saute, et rien
 *    n'explique pourquoi.
 *
 * 🎯 DECISION OWNER, 2026-08-27 : ON GARDE LA PERSISTANCE, ET ON POSE LE
 *    TEMOIN. Le reglage n'est plus detruit EN SILENCE : il est detruit ET
 *    TRACE. `cfg` lit le temoin et le CRIE tant qu'il est la.
 *
 * ⛔ IL SURVIT A `cfg reset` — DELIBEREMENT. `cfg reset` est precisement ce
 *    qu'on tape pour sortir d'une valeur fautive, c'est-a-dire le moment ou on
 *    a le PLUS besoin de savoir qu'un repli a eu lieu. Il ne s'efface que par
 *    un geste EXPLICITE : `cfg repli clear`.
 */
/* 🔴 SENTINELLE D'ABSENCE, POSEE LE 2026-08-27 (3e revue). `0` ne peut PAS
 *    servir de « pas de valeur » : `bounce_px = 0` est une valeur ACCEPTEE par
 *    `bounce_px_refus()` — le depot l'ecrit lui-meme (« les douze valeurs, plus
 *    le zero ») — et elle desactive le tampon de bounce, c'est-a-dire qu'elle
 *    FABRIQUE le glissement. Un champ laisse a 0 parce que la cle etait
 *    illisible se lisait donc « la NVS demandait 0 px », indiscernable d'un vrai
 *    repli. ⛔ Une sentinelle qui a la forme d'une mesure n'est pas une
 *    sentinelle. `-1` est impossible pour `bounce_px` (`v < 0` est refuse). */
#define DN_REPLI_NON_RELU (-1)

typedef struct {
    bool present;     /* un repli a ete note en NVS */
    int demande_px;   /* la valeur que l'operateur avait posee, et qui est PERDUE
                       * ⚠️ vaut DN_REPLI_NON_RELU si la cle n'a pas pu etre lue */
    int retenu_px;    /* celle que le filet a retenue a sa place
                       * ⚠️ vaut DN_REPLI_NON_RELU si la cle n'a pas pu etre lue */
    int occurrences;  /* combien de replis ont ete notes depuis le dernier clear */
} dn_bootcfg_repli_t;

/* Note un repli. Appelee par `desknode_main` AVANT de reecrire `bounce_px`.
 * ⛔ Ne remplace PAS la persistance : elle la rend interrogeable. */
esp_err_t dn_bootcfg_note_repli(int demande_px, int retenu_px);

/*
 * Lit le temoin. `out->present == false` si aucun repli n'a ete note.
 *
 * 🔴 REND DESORMAIS UN `esp_err_t` — 3e revue du 2026-08-27. Le retour etait
 *    `void` : quand la NVS ne s'ouvrait pas, on sortait avec `present == false`
 *    et la console AFFIRMAIT « aucun repli de bounce note » pour un temoin
 *    qu'elle n'avait JAMAIS REUSSI A LIRE. ⛔ C'est le defaut que ce depot
 *    traque depuis dn4-6 : un compteur qui reste a zero ne prouve rien tant
 *    qu'on n'a pas montre qu'il pouvait bouger — et ici on ne l'avait meme pas
 *    interroge. `ESP_OK` = la reponse vaut ; toute autre valeur = « ILLISIBLE »,
 *    ⛔ pas « aucun ».
 */
esp_err_t dn_bootcfg_get_repli(dn_bootcfg_repli_t *out);

/* Efface le temoin. ⛔ GESTE EXPLICITE UNIQUEMENT — voir ci-dessus.
 * ⚠️ « SEUL geste qui l'efface » est vrai pour l'OPERATEUR, ⛔ pas pour le
 *    firmware : `nvs_flash_erase()` dans `desknode_main.c` (NVS corrompue ou
 *    nouvelle version de la partition) l'emporte avec tout le reste. Ce
 *    troisieme chemin est declare la-bas et dans le README depuis la 3e revue. */
esp_err_t dn_bootcfg_clear_repli(void);

/*
 * 🔴 `dn_bootcfg_reset()` AVEC LE VERDICT DE LA REPOSE — 3e revue du 2026-08-27.
 *    `dn_bootcfg_reset()` ne rendait que le statut de l'EFFACEMENT ; l'echec de
 *    la repose du temoin etait journalise puis JETE. La console voyait `ESP_OK`
 *    et imprimait « le TEMOIN DE REPLI, lui, est CONSERVE » — dans la meme
 *    sortie que le `ESP_LOGE` disant qu'il etait PERDU. ⛔ Deux sorties
 *    normatives en desaccord, sur le sujet meme que ce temoin existe pour
 *    fermer, et c'est mot pour mot la classe du constat #948.
 * ⇒ `repose` rend ce qui s'est reellement passe. `*repose` peut valoir :
 *     DN_REPOSE_SANS_OBJET : il n'y avait aucun temoin a conserver
 *     DN_REPOSE_OK         : le temoin a ete relu, efface et repose
 *     autre                : l'`esp_err_t` de l'echec — le temoin est PERDU
 *   `repose` peut etre NULL si l'appelant ne veut pas le savoir. ⛔ Mais alors
 *   il n'a PAS le droit d'affirmer quoi que ce soit sur le temoin.
 */
#define DN_REPOSE_OK          ESP_OK
#define DN_REPOSE_SANS_OBJET  ESP_ERR_NOT_FOUND
esp_err_t dn_bootcfg_reset_ex(esp_err_t *repose);

/*
 * ── LE BUDGET COMBINÉ, ET POURQUOI IL A FALLU L'AJOUTER (revue dn1-4) ────────
 *
 * `bounce_px` et `draw_lines` mangent la MÊME RAM interne, et leurs deux bornes
 * (DN_BOUNCE_PX_MAX, DN_DRAW_LINES_MAX) étaient indépendantes, calibrées à deux
 * époques différentes. DN_BOUNCE_PX_MAX = 38 400 px a été justifié en dn1-2 par
 * « il reste ~348 Ko de RAM interne libre » — c'est-à-dire AVANT LVGL. dn1-4 a
 * ensuite fait passer draw_lines de 64 à 128, soit +61 440 o, et mesuré 118 379 o
 * libres. Le « plafond » que l'aide de `set bounce` présentait comme un diviseur
 * UTILE réclame 2 × 76 800 o : il ne démarre plus.
 *
 * Et c'est le pire des refus manqués : ESP_ERR_NO_MEM au boot => ESP_ERROR_CHECK
 * => panique => CPU HALTÉ par CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT. Plus de
 * console, donc plus de `cfg reset`, à chaque boot, jusqu'au reflash. Exactement
 * le brick que ces bornes existaient pour empêcher.
 *
 * On ne remplace pas un chiffre gravé par un autre chiffre gravé : le budget est
 * évalué CONTRE LA RAM RÉELLEMENT LIBRE au moment de l'écriture, à laquelle on
 * rajoute ce que les buffers actuels rendront au reboot. Auto-calibré, donc
 * juste après n'importe quelle évolution du binaire.
 */
size_t dn_bootcfg_cout_interne(int bounce_px, int draw_lines);
/* NULL si le couple tient, sinon la RAISON en clair. `demande` et `dispo`
 * (optionnels) rendent les deux chiffres pour que le refus soit chiffré. */
const char *dn_bootcfg_budget_refus(int bounce_px, int draw_lines, size_t *demande,
                                    size_t *dispo);

/* La marge de sécurité du budget RAM interne, en octets.
 * ⚠️ Elle s'AJOUTE à la demande, elle n'est PAS retranchée du disponible que
 *    `dn_bootcfg_budget_refus()` rend par `*dispo` — la comparaison faite est
 *    `demande + marge > dispo`. Le message de la console le disait à l'envers
 *    jusqu'au 2026-08-23 (dn4-10), et un refus légitime y ressemblait à un bug. */
size_t dn_bootcfg_budget_marge_o(void);

/* La valeur de `bounce_px` par défaut, en pixels. Publiée pour le filet de
 * sécurité au boot de `dn_display.c` (dn4-10) : c'est la valeur sur laquelle il
 * REPLIE quand celle de la NVS ne s'alloue pas. */
int dn_bootcfg_defaut_bounce_px(void);

void dn_bootcfg_log(const dn_bootcfg_t *cfg);

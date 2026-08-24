/*
 * ── dn_hist — L'HISTORIQUE DE SESSION, EN RAM (dn4-4 / AC5) ──────────────────
 *
 * La courbe de la page de détail est une SÉRIE TEMPORELLE. Elle a besoin d'une
 * mémoire, et cette mémoire est ici : bornée, chiffrée, et **en RAM**.
 *
 * ══ LE DIMENSIONNEMENT — ÉCRIT AVANT LE CODE, ET JUSTIFIÉ ═══════════════════
 *
 * | Choix                  | Valeur      | Motif                               |
 * |------------------------|-------------|-------------------------------------|
 * | séries                 | **8**       | une par page (6) + la 2ᵉ d'`AMBIANCE`|
 *                        |             | + la 2ᵉ de `RÉSEAU` (owner 2026-08-24)|
 * |                        |             | (addendum §1, exception 1 : la seule |
 * |                        |             | page à DEUX courbes)                 |
 * | points par série       | **120**     | à 1 Hz ⇒ **2 minutes** de session    |
 * | cadence                | **1 Hz**    | ⚠️ ⛔ PAS UN CHOIX DE CONFORT : c'est |
 * |                        |             | la cadence de poussée **MESURÉE** le |
 * |                        |             | 2026-08-24 (100 trames ⇒ 100 poussées|
 * |                        |             | en 20,5 s = 5,0/s pour CINQ métriques|
 * |                        |             | ⇒ **1,0/s par métrique**).           |
 * | octets par point       | **4**       | `int32_t` — **imposé** par           |
 * |                        |             | `lv_chart_set_series_ext_y_array()`  |
 * | points seuls           | **3 840 o** | 8 x 120 x 4 (7 -> 8 : `RÉSEAU` montant)|
 * | **TOTAL `.bss` MODULE**| **~5 609 o**| + seaux 1 728 + index. 🔴 C'est CE      |
 * |                        |             | total que `dn_hist_octets()` rend      |
 * |                        |             | DEPUIS dn4-13 ; la ligne du dessus n'a |
 * |                        |             | jamais été le coût du module, et c'est |
 * |                        |             | le défaut qu'AC2.1 solde.              |
 * | où il vit              | **`.bss`**  | voir ci-dessous                      |
 * |                        | **interne** |                                      |
 *
 * ⚠️ **PRÉDICTION, À CONFRONTER AU RELEVÉ (AC5.6)** : Δ RAM interne libre
 *    ≈ **−3 400 à −3 500 o** (les 3 360 o de points + les index et compteurs).
 * 🔴 **⛔ CETTE PRÉDICTION N'EST PAS RÉÉCRITE — ON NE RÉÉCRIT PAS UNE PRÉDICTION
 *    POUR QU'ELLE TOMBE JUSTE.** Elle était JUSTE quand elle a été écrite :
 *    `DN_HIST_N_SERIES` valait alors **7** (7 x 120 x 4 = 3 360 o) et **les 24
 *    seaux n'existaient pas encore**. Le relevé qui la confronte dans
 *    `affichage.md` §22.5 (**−3 512 o**) date du MÊME état (commit `8cf16a9`).
 * 🔴 **DEPUIS, LE MODULE A GROSSI DE ~2 200 o ET LE RELEVÉ N'A PAS ÉTÉ REFAIT** :
 *    `ffff6d2` a ajouté les seaux (+1 512 o à 7 séries), `08d4d2b` la 8ᵉ série
 *    `DN_HIST_S_NET_UP` (+700 o). Le `.bss` réel du module vaut aujourd'hui
 *    **~5 609 o** (3 840 points + 768 s_smin + 768 s_smax + 192 s_svu + 32 s_w
 *    + 9). ⇒ **AC5.6 EST À RE-TIRER SUR LE FIRMWARE LIVRÉ** — écart déclaré,
 *    porté par `dn4-13`. [Revue de code du 2026-08-24]
 *    Δ tas LVGL : **NON PRÉDIT** — c'est le coût des objets `lv_chart`, et une
 *    prédiction sans instrument ne coûte rien à celui qui l'écrit (leçon L18).
 *
 * 🔴 **POURQUOI `.bss` INTERNE, ⛔ NI LE POOL LVGL NI LA PSRAM** :
 *    · ⛔ **pas le pool LVGL** — il est STATIQUE et petit (64 Ko, **20 692 o
 *      déjà occupés**), et il est INVISIBLE pour `mem`. Or
 *      `lv_chart_set_series_ext_y_array()` existe précisément pour que les
 *      points **ne soient PAS copiés dedans** : les y mettre annulerait le seul
 *      bénéfice de l'API choisie.
 *    · ⛔ **pas la PSRAM** — ~~3 360 o~~ **3 840 o** (chiffre corrigé le
 *      2026-08-24, revue de code : 8 séries, ⛔ plus 7) ne la justifient pas, et
 *      le rendu du chart relit ces octets à CHAQUE redessin. La PSRAM est le
 *      goulot MESURÉ de ce dépôt (~23 Mo/s en continu) ; y poser une donnée
 *      relue en boucle serait payer une latence pour économiser ~~3 Ko~~
 *      **5,6 Ko** (points + seaux) sur 81 Ko libres.
 *
 * ══ CE QUE L'HISTORIQUE NE FAIT PAS ════════════════════════════════════════
 *
 * ⛔ **AUCUNE écriture flash / NVS / TF** (D4). L'historique meurt avec la
 *    session, et le brief l'autorise explicitement (*« La V1 peut vivre avec
 *    RAM seule »*). ⛔ Ne pas « améliorer » ça sans décision owner.
 *
 * ══ 🔴 L'HISTORIQUE NE MENT PAS ════════════════════════════════════════════
 *
 * 1. **UNE VALEUR ABSENTE OU PÉRIMÉE EST UN TROU**, ⛔ jamais un `0`, ⛔ jamais
 *    une interpolation. Le trou est `LV_CHART_POINT_NONE`, la valeur que
 *    `lv_chart` SAUTE au tracé. Un `0` dessinerait une chute à zéro là où la
 *    source s'est simplement tue — le mensonge d'interface que `dn2-2` a chassé
 *    du dashboard, transposé au temps.
 * 2. **UNE VALEUR `SIMULÉE` N'ENTRE PAS.** Un mock armé produit des **TROUS**,
 *    ⛔ pas des points. C'est la règle W10/AC5 de `dn4-1` portée au temps : une
 *    série présentée comme réelle ne contient que du réel. ⚠️ Et c'est
 *    STRUCTUREL, ⛔ pas une discipline : l'échantillonneur lit le RÉGIME.
 * 3. **L'AXE DES TEMPS A UN SENS.** L'anneau avance sur une horloge à 1 Hz,
 *    ⛔ pas à la cadence des trames : sinon un injecteur à 4 Hz et un agent à
 *    1 Hz produiraient deux axes différents sous le même dessin.
 *    ⇒ C'est aussi pourquoi l'alimentation N'EST PAS branchée sur `case_poser` :
 *      ce chemin est « le plus chaud de la vue détail » et sa cadence VARIE.
 *      **Écart assumé avec la lettre de T6, avec son motif.**
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DN_HIST_N_SERIES 8
#define DN_HIST_N_POINTS 120
#define DN_HIST_PERIODE_MS 1000

/* ⚠️ LA MÊME VALEUR QUE `LV_CHART_POINT_NONE` — vérifiée à la compilation dans
 *    `dn_hist.c`. On ne la recopie pas « au cas où » : on l'ASSERTE. */
#define DN_HIST_TROU INT32_MAX

/* Les **HUIT** séries (~~sept~~ — corrigé le 2026-08-24, revue de code : la 8ᵉ
 * est `DN_HIST_S_NET_UP`, ajoutée par `08d4d2b`).
 * ⚠️ L'ORDRE EST UN CONTRAT : `dn_hist_serie_de_case()` en
 *    dépend, et l'audit de `dn_hist_init()` le vérifie. */
typedef enum {
    DN_HIST_S_CPU = 0,
    DN_HIST_S_GPU,
    DN_HIST_S_RAM,
    DN_HIST_S_NET,
    DN_HIST_S_DISK,
    DN_HIST_S_AMB_T, /* AMBIANCE — température */
    DN_HIST_S_AMB_H, /* AMBIANCE — humidité : LA SECONDE COURBE (addendum §1) */
    /* 🔴 DEMANDE OWNER DU 2026-08-24 : *« pour network ajouter le upload aussi
     *    en 2e courbe d'une autre couleur »*. `RÉSEAU` devient donc la SECONDE
     *    page à deux courbes — l'addendum §1 n'en prévoyait qu'une (`AMBIANCE`).
     *    ⚠️ AJOUTÉE EN FIN D'ÉNUMÉRATION, ⛔ pas insérée après `DN_HIST_S_NET` :
     *       renuméroter aurait décalé `k_s0[]`/`k_s1[]` en silence. */
    DN_HIST_S_NET_UP,
} dn_hist_serie_t;

void dn_hist_init(void);

/*
 * 🔴 dn4-13 / AC3.1 — À APPELER **UNE FOIS PAR TICK D'HORLOGE, AVANT LES POSES**.
 * Comble de TROUS les périodes de 1 Hz qui n'ont PAS été échantillonnées (un
 * `ui off`, une pause LVGL, une tâche préemptée longtemps). Sans elle, l'anneau
 * recolle les deux bords de la pause et `lv_chart` relie deux instants distants
 * par un segment qui vaut UNE seconde à l'écran : un mensonge sur la DURÉE,
 * ⛔ pas sur la valeur — donc plus difficile à voir.
 * ⚠️ Elle lit `esp_timer_get_time()`, ⛔ PAS le tick LVGL : `lvgl_port_pause()`
 *    arrête le tick, donc la pause est INVISIBLE pour LVGL. Rend le nombre de
 *    points comblés (0 en régime : une gigue de timer n'est pas une coupure).
 */
int dn_hist_rattraper(void);

/* Ce que le rattrapage a fait depuis l'init — pour que `hist` le DISE. Un
 * comblement silencieux serait une réparation invisible, donc invérifiable. */
void dn_hist_rattrapages(uint32_t *evenements, uint32_t *trous);

/* Pose UN échantillon. `connue == false` ⇒ **TROU**, ⛔ pas zéro.
 * ⚠️ `dixiemes` est la valeur DU FIL, en dixièmes — ⛔ pas l'unité affichée
 *    (`brut[0]`, lui, est en unités affichées pour la jauge : les confondre
 *    diviserait la courbe par 10 sans que rien ne le dise). */
void dn_hist_poser(int serie, int32_t dixiemes, bool connue);

/* Le tableau LINÉAIRE que `lv_chart_set_series_ext_y_array()` lira DIRECTEMENT.
 * ⛔ Ne jamais le recopier : c'est tout l'intérêt de l'API externe. */
int32_t *dn_hist_points(int serie);

/* L'index du point le PLUS ANCIEN — à passer à `lv_chart_set_x_start_point()`.
 * ⚠️ C'est ainsi qu'un ANNEAU se rend sans être recopié à chaque tour. */
uint32_t dn_hist_debut(int serie);

/*
 * ── dn4-4 / DEMANDE OWNER DU 2026-08-24 : LE MIN/MAX **LONG** ────────────────
 *
 * Verbatim : *« pourrait-on systématiquement avoir le min max sur 24 h +
 * quelques minutes de graphe ? »*
 *
 * ⚠️ **CE N'EST PAS LE MIN/MAX DE LA COURBE.** La courbe montre 120 points à
 *    1 Hz = **2 minutes** ; ce MIN/MAX-ci couvre jusqu'à **24 heures**. Les deux
 *    coexistent délibérément, et c'est exactement ce que l'owner a demandé.
 *
 * ⚠️ **24 SEAUX D'UNE HEURE, EN ANNEAU** — ⛔ pas un min/max « depuis le boot ».
 *    Un min/max cumulé depuis le démarrage ne s'oublie JAMAIS : un pic à 100 %
 *    survenu il y a trois jours serait encore affiché comme le maximum, sur une
 *    page qui prétend parler des 24 dernières heures. Le seau d'une heure qu'on
 *    ré-atteint est **remis à vide**, donc la fenêtre GLISSE.
 *
 * 🔴 **LA LIMITE, ET ELLE EST DITE À L'ÉCRAN, ⛔ PAS SEULEMENT ICI** : D4
 *    interdit toute écriture flash/NVS en régime, donc **ceci ne survit pas à un
 *    reboot**. « 24 h » n'est vrai QUE si la carte a tourné 24 h.
 *    ⇒ `dn_hist_couverture_s()` rend la fenêtre **RÉELLEMENT** couverte, et la
 *      page l'affiche. ⛔ Écrire « 24 h » sur douze minutes de données serait
 *      exactement le mensonge d'interface que ce dépôt chasse depuis `dn2-2`.
 *
 * Coût : ~~8 x 24 x 2 x 4 o = 1 536 o~~ ⇒ **1 728 o** — chiffre corrigé le
 * 2026-08-24 (revue de code) : `s_smin` 768 + `s_smax` 768 **+ `s_svu[8][24]`
 * = 192 o**, le drapeau « ce seau a vu du réel », que la formule à deux
 * tableaux ne comptait pas. En `.bss` interne, comme les points.
 * ⚠️ `affichage.md` §22.9 publiait `7 x 24 x 2 x 4 = 1 344 o` : **deux fautes
 *    cumulées** (7 séries au lieu de 8, et `s_svu` oublié). Amendé là-bas aussi.
 */
#define DN_HIST_SEAUX 24
#define DN_HIST_SEAU_S 3600

/* Le MIN/MAX sur la fenêtre LONGUE (jusqu'à 24 h). Rend `false` si aucun seau
 * ne porte de valeur réelle. */
bool dn_hist_minmax_long(int serie, int32_t *min, int32_t *max);

/* La durée RÉELLEMENT couverte par les seaux DE CETTE SÉRIE, en secondes.
 * ⛔ Ce n'est pas `24 x 3600` par principe, ⛔ et ce n'est PAS l'uptime.
 * 🔴 dn4-13 / AC2.2 — jusqu'au 2026-08-25 elle rendait `min(uptime, 24 h)` sous
 *    un commentaire qui promettait l'inverse. Carte allumée 1 h sans source PC,
 *    la page annonçait « MIN/MAX sur : 1 h » à côté de « MIN -- · MAX -- ».
 *    Elle compte désormais les seaux qui ONT VU DU RÉEL, et rend **0** quand il
 *    n'y en a aucun. Elle prend une SÉRIE : deux séries d'une même page peuvent
 *    avoir commencé à des instants différents. */
uint32_t dn_hist_couverture_s(int serie);

/* Le MIN/MAX de la série, **sur les seuls points réels**. Rend `false` si la
 * série ne contient QUE des trous — auquel cas la page doit dire « -- », ⛔ pas
 * inventer une plage. */
bool dn_hist_minmax(int serie, int32_t *min, int32_t *max);

/* Combien de points RÉELS (⛔ pas de trous) la série contient — l'instrument qui
 * permet de dire « la courbe est vide » sans le deviner. */
int dn_hist_reels(int serie);

/* La série tracée par la page `case`, et sa seconde série s'il y en a une.
 * Rend le nombre de séries (1, ou **2 pour AMBIANCE**). */
int dn_hist_series_de_case(int case_idx, int *s0, int *s1);

/* Le coût `.bss` **RÉEL** du module, en octets — points **+ seaux + index**.
 * 🔴 dn4-13 / AC2.1 — elle rendait `sizeof(s_pts)` SEUL (3 840 o) pour un module
 *    qui en occupe ~5 600 : ~32 % de sous-déclaration, sur l'instrument même qui
 *    devait solder AC5.6. Le détail sort par `dn_hist_octets_detail()` pour que
 *    `hist` publie les trois termes, ⛔ pas un total invérifiable. */
size_t dn_hist_octets(void);
size_t dn_hist_octets_detail(size_t *points, size_t *seaux, size_t *index);

#ifdef __cplusplus
}
#endif

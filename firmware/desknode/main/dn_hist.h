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
 * | séries                 | **7**       | une par page (6) + la 2ᵉ d'`AMBIANCE`|
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
 * | **TOTAL**              | **3 360 o** | 7 x 120 x 4                          |
 * | où il vit              | **`.bss`**  | voir ci-dessous                      |
 * |                        | **interne** |                                      |
 *
 * ⚠️ **PRÉDICTION, À CONFRONTER AU RELEVÉ (AC5.6)** : Δ RAM interne libre
 *    ≈ **−3 400 à −3 500 o** (les 3 360 o de points + les index et compteurs).
 *    Δ tas LVGL : **NON PRÉDIT** — c'est le coût des objets `lv_chart`, et une
 *    prédiction sans instrument ne coûte rien à celui qui l'écrit (leçon L18).
 *
 * 🔴 **POURQUOI `.bss` INTERNE, ⛔ NI LE POOL LVGL NI LA PSRAM** :
 *    · ⛔ **pas le pool LVGL** — il est STATIQUE et petit (64 Ko, **20 692 o
 *      déjà occupés**), et il est INVISIBLE pour `mem`. Or
 *      `lv_chart_set_series_ext_y_array()` existe précisément pour que les
 *      points **ne soient PAS copiés dedans** : les y mettre annulerait le seul
 *      bénéfice de l'API choisie.
 *    · ⛔ **pas la PSRAM** — 3 360 o ne la justifient pas, et le rendu du chart
 *      relit ces octets à CHAQUE redessin. La PSRAM est le goulot MESURÉ de ce
 *      dépôt (~23 Mo/s en continu) ; y poser une donnée relue en boucle serait
 *      payer une latence pour économiser 3 Ko sur 81 Ko libres.
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

#define DN_HIST_N_SERIES 7
#define DN_HIST_N_POINTS 120
#define DN_HIST_PERIODE_MS 1000

/* ⚠️ LA MÊME VALEUR QUE `LV_CHART_POINT_NONE` — vérifiée à la compilation dans
 *    `dn_hist.c`. On ne la recopie pas « au cas où » : on l'ASSERTE. */
#define DN_HIST_TROU INT32_MAX

/* Les sept séries. ⚠️ L'ORDRE EST UN CONTRAT : `dn_hist_serie_de_case()` en
 *    dépend, et l'audit de `dn_hist_init()` le vérifie. */
typedef enum {
    DN_HIST_S_CPU = 0,
    DN_HIST_S_GPU,
    DN_HIST_S_RAM,
    DN_HIST_S_NET,
    DN_HIST_S_DISK,
    DN_HIST_S_AMB_T, /* AMBIANCE — température */
    DN_HIST_S_AMB_H, /* AMBIANCE — humidité : LA SECONDE COURBE (addendum §1) */
} dn_hist_serie_t;

void dn_hist_init(void);

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

/* Le coût, en octets, du stockage des points — pour que `mem` puisse être
 * confronté à la prédiction au lieu d'être commenté. */
size_t dn_hist_octets(void);

#ifdef __cplusplus
}
#endif

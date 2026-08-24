/* Voir `dn_hist.h` : le dimensionnement, les motifs, et les trois règles
 * d'honnêteté y sont écrits AVANT ce code. */
#include "dn_hist.h"

#include <string.h>

#include "lvgl.h"

/* 🔴 ON N'A PAS RECOPIÉ LA SENTINELLE DE LVGL « au cas où » : ON L'ASSERTE.
 *    Une constante dupliquée qui dérive d'une version à l'autre dessinerait des
 *    trous comme des valeurs — c'est-à-dire un pic à 2 147 483 647 dans une
 *    courbe présentée comme réelle. */
_Static_assert(DN_HIST_TROU == LV_CHART_POINT_NONE,
               "DN_HIST_TROU doit valoir LV_CHART_POINT_NONE");

/* 🔴 LE STOCKAGE. `.bss` interne — voir le motif dans `dn_hist.h`.
 * ⚠️ NON `static`ement initialisé à zéro : `0` serait une VALEUR. L'init pose
 *    des TROUS partout, et c'est `dn_hist_init()` qui le fait. */
static int32_t s_pts[DN_HIST_N_SERIES][DN_HIST_N_POINTS];

/* Position d'écriture = index du point le PLUS ANCIEN une fois l'anneau plein.
 * C'est exactement ce que `lv_chart_set_x_start_point()` attend. */
static uint32_t s_w[DN_HIST_N_SERIES];

static bool s_pret;

void dn_hist_init(void)
{
    for (int s = 0; s < DN_HIST_N_SERIES; s++) {
        for (int i = 0; i < DN_HIST_N_POINTS; i++) {
            s_pts[s][i] = DN_HIST_TROU;
        }
        s_w[s] = 0;
    }
    s_pret = true;
}

void dn_hist_poser(int serie, int32_t dixiemes, bool connue)
{
    if (!s_pret || serie < 0 || serie >= DN_HIST_N_SERIES) {
        return;
    }
    /* ⚠️ UNE VALEUR RÉELLE QUI VAUDRAIT LA SENTINELLE SERAIT INDISCERNABLE D'UN
     *    TROU. Aucune grandeur du protocole ne peut l'atteindre (les plafonds de
     *    `k_metriques[]` sont à 1 000 000 de dixièmes au plus), mais un plafond
     *    qui change un jour ne doit pas transformer une valeur en trou EN
     *    SILENCE. On la décale d'un dixième plutôt que de mentir sur sa nature.
     * ⛔ Ne pas « simplifier » en retirant ce test : c'est un pixel de dessin
     *    contre un trou invisible. */
    if (connue && dixiemes == DN_HIST_TROU) {
        dixiemes = DN_HIST_TROU - 1;
    }
    s_pts[serie][s_w[serie]] = connue ? dixiemes : DN_HIST_TROU;
    s_w[serie] = (s_w[serie] + 1u) % DN_HIST_N_POINTS;
}

int32_t *dn_hist_points(int serie)
{
    if (serie < 0 || serie >= DN_HIST_N_SERIES) {
        return NULL;
    }
    return s_pts[serie];
}

uint32_t dn_hist_debut(int serie)
{
    if (serie < 0 || serie >= DN_HIST_N_SERIES) {
        return 0;
    }
    return s_w[serie];
}

bool dn_hist_minmax(int serie, int32_t *min, int32_t *max)
{
    if (serie < 0 || serie >= DN_HIST_N_SERIES) {
        return false;
    }
    bool vu = false;
    int32_t mn = 0, mx = 0;
    for (int i = 0; i < DN_HIST_N_POINTS; i++) {
        int32_t v = s_pts[serie][i];
        if (v == DN_HIST_TROU) {
            continue; /* ⛔ un trou n'est pas un minimum de zéro */
        }
        if (!vu || v < mn) {
            mn = v;
        }
        if (!vu || v > mx) {
            mx = v;
        }
        vu = true;
    }
    if (!vu) {
        return false; /* ⛔ « pas de plage », ⛔ pas « plage 0..0 » */
    }
    if (min) {
        *min = mn;
    }
    if (max) {
        *max = mx;
    }
    return true;
}

int dn_hist_reels(int serie)
{
    if (serie < 0 || serie >= DN_HIST_N_SERIES) {
        return 0;
    }
    int n = 0;
    for (int i = 0; i < DN_HIST_N_POINTS; i++) {
        if (s_pts[serie][i] != DN_HIST_TROU) {
            n++;
        }
    }
    return n;
}

int dn_hist_series_de_case(int case_idx, int *s0, int *s1)
{
    /* ⚠️ LA TABLE EST EXPLICITE, ⛔ PAS UN `case_idx` PASSÉ TEL QUEL. L'identité
     *    tient AUJOURD'HUI (case 0 = CPU … case 5 = AMBIANCE) ; l'écrire la rend
     *    vérifiable, et surtout elle porte l'EXCEPTION d'`AMBIANCE`. */
    static const int8_t k_s0[6] = {
        DN_HIST_S_CPU, DN_HIST_S_GPU, DN_HIST_S_RAM,
        DN_HIST_S_NET, DN_HIST_S_DISK, DN_HIST_S_AMB_T,
    };
    /* 🔴 `AMBIANCE` EST LA SEULE PAGE À DEUX COURBES — addendum §1, exception 1.
     *    ⛔ Ne pas généraliser : empiler quatre séries d'unités différentes sur
     *    une échelle commune n'aurait aucun sens (`DISQUE` porte `Mo/s` ET trois
     *    `tr/min` ; `CPU` porte `%`, `GHz`, `%` et `°C`). */
    static const int8_t k_s1[6] = {-1, -1, -1, -1, -1, DN_HIST_S_AMB_H};

    if (case_idx < 0 || case_idx >= 6) {
        if (s0) { *s0 = -1; }
        if (s1) { *s1 = -1; }
        return 0;
    }
    if (s0) { *s0 = k_s0[case_idx]; }
    if (s1) { *s1 = k_s1[case_idx]; }
    return k_s1[case_idx] >= 0 ? 2 : 1;
}

size_t dn_hist_octets(void) { return sizeof(s_pts); }

/* Voir `dn_hist.h` : le dimensionnement, les motifs, et les trois règles
 * d'honnêteté y sont écrits AVANT ce code. */
#include "dn_hist.h"

#include <string.h>

#include "esp_timer.h"
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

/* Les 24 seaux d'une heure — voir `dn_hist.h` pour le motif de l'anneau. */
static int32_t s_smin[DN_HIST_N_SERIES][DN_HIST_SEAUX];
static int32_t s_smax[DN_HIST_N_SERIES][DN_HIST_SEAUX];
static bool s_svu[DN_HIST_N_SERIES][DN_HIST_SEAUX];
static int s_seau_courant = -1;
/* ⚠️ Combien de seaux DISTINCTS ont été ouverts — borné à 24. C'est LUI qui
 *    donne la couverture réelle, ⛔ pas une constante. */
static uint32_t s_seaux_ouverts;

void dn_hist_init(void)
{
    for (int s = 0; s < DN_HIST_N_SERIES; s++) {
        for (int i = 0; i < DN_HIST_N_POINTS; i++) {
            s_pts[s][i] = DN_HIST_TROU;
        }
        s_w[s] = 0;
    }
    for (int s = 0; s < DN_HIST_N_SERIES; s++) {
        for (int b = 0; b < DN_HIST_SEAUX; b++) {
            s_svu[s][b] = false;
        }
    }
    s_seau_courant = -1;
    s_seaux_ouverts = 0;
    s_pret = true;
}

/* Ouvre (et VIDE) le seau de l'heure courante quand on y entre. ⛔ Sans ce
 * vidage, la fenêtre ne glisserait pas : elle deviendrait « depuis le boot ». */
static void seau_suivre(void)
{
    int64_t up_s = esp_timer_get_time() / 1000000;
    int b = (int)((up_s / DN_HIST_SEAU_S) % DN_HIST_SEAUX);
    if (b == s_seau_courant) {
        return;
    }
    s_seau_courant = b;
    for (int s = 0; s < DN_HIST_N_SERIES; s++) {
        s_svu[s][b] = false;
    }
    if (s_seaux_ouverts < DN_HIST_SEAUX) {
        s_seaux_ouverts++;
    }
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

    /* ⚠️ LE SEAU NE REÇOIT QUE DU RÉEL, comme l'anneau. Un trou n'abaisse aucun
     *    minimum et ne relève aucun maximum : il n'existe simplement pas. */
    seau_suivre();
    if (!connue || s_seau_courant < 0) {
        return;
    }
    int b = s_seau_courant;
    if (!s_svu[serie][b]) {
        s_smin[serie][b] = dixiemes;
        s_smax[serie][b] = dixiemes;
        s_svu[serie][b] = true;
    } else {
        if (dixiemes < s_smin[serie][b]) {
            s_smin[serie][b] = dixiemes;
        }
        if (dixiemes > s_smax[serie][b]) {
            s_smax[serie][b] = dixiemes;
        }
    }
}

bool dn_hist_minmax_long(int serie, int32_t *min, int32_t *max)
{
    if (serie < 0 || serie >= DN_HIST_N_SERIES) {
        return false;
    }
    bool vu = false;
    int32_t mn = 0, mx = 0;
    for (int b = 0; b < DN_HIST_SEAUX; b++) {
        if (!s_svu[serie][b]) {
            continue;
        }
        if (!vu || s_smin[serie][b] < mn) {
            mn = s_smin[serie][b];
        }
        if (!vu || s_smax[serie][b] > mx) {
            mx = s_smax[serie][b];
        }
        vu = true;
    }
    if (!vu) {
        return false; /* ⛔ « pas de plage », ⛔ pas « 0..0 » */
    }
    if (min) { *min = mn; }
    if (max) { *max = mx; }
    return true;
}

uint32_t dn_hist_couverture_s(void)
{
    /* 🔴 CE QUI A VRAIMENT ÉTÉ OBSERVÉ, ⛔ PAS `24 x 3600`. L'uptime borne la
     *    couverture tant qu'on n'a pas fait un tour complet des seaux ; au-delà,
     *    c'est la fenêtre glissante de 24 h. */
    int64_t up_s = esp_timer_get_time() / 1000000;
    uint32_t plafond = (uint32_t)DN_HIST_SEAUX * DN_HIST_SEAU_S;
    if (up_s < 0) {
        return 0;
    }
    return (uint32_t)up_s < plafond ? (uint32_t)up_s : plafond;
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
    /* 🔴 DEUX pages portent une seconde courbe depuis le 2026-08-24 :
     *    `RÉSEAU` (descendant + MONTANT, demande owner) et `AMBIANCE`
     *    (température + humidité, addendum §1). ⛔ Ne pas généraliser aux
     *    autres : empiler des unités différentes sur une échelle commune n'a
     *    aucun sens (`DISQUE` porte `Mo/s` ET trois `tr/min`). */
    static const int8_t k_s1[6] = {-1, -1, -1, DN_HIST_S_NET_UP, -1,
                                   DN_HIST_S_AMB_H};

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

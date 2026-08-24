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

/*
 * 🔴 dn4-13 / AC6.3 — COMBIEN DE POSITIONS ONT ÉTÉ **ÉCRITES UNE FOIS**, par
 *    série (saturant à `DN_HIST_N_POINTS`).
 *
 * ⚠️ SANS LUI, « JAMAIS ÉCRIT » ET « TROU » SONT LE MÊME OCTET. `dn_hist_init()`
 *    remplit l'anneau de `DN_HIST_TROU` : à t = 10 s, `hist` affichait donc
 *    *« reels 10 · trous 110 »* alors que **110 cases n'avaient jamais été
 *    atteintes**. Ce ne sont pas des trous — un trou est une SECONDE OÙ LA
 *    SOURCE S'EST TUE, et c'est une information ; une case jamais atteinte n'en
 *    est pas une. L'en-tête de la commande revendiquait pourtant exactement
 *    cette distinction.
 * ⚠️ Et ce compteur donne AUSSI la fenêtre courte réelle : `n` positions écrites
 *    à 1 Hz = `n` secondes, ⛔ pas « 2 min » par principe.
 */
static uint32_t s_ecrits[DN_HIST_N_SERIES];

/* Les 24 seaux d'une heure — voir `dn_hist.h` pour le motif de l'anneau. */
static int32_t s_smin[DN_HIST_N_SERIES][DN_HIST_SEAUX];
static int32_t s_smax[DN_HIST_N_SERIES][DN_HIST_SEAUX];
static bool s_svu[DN_HIST_N_SERIES][DN_HIST_SEAUX];
/*
 * 🔴 dn4-13 / AC3.2 — L'INDEX DU SEAU EST **ABSOLU**, ⛔ PLUS L'INDEX D'ANNEAU.
 *    `seau_suivre()` comparait `b == s_seau_courant` sur un index modulo 24. Deux
 *    conséquences, toutes deux mesurées :
 *    · SAUT. Passer de l'heure 3 à l'heure 6 (une pause, une horloge qui
 *      remonte, un `ui off` long) ne vidait QUE le seau 6 : les seaux 4 et 5
 *      gardaient leurs valeurs DU TOUR PRÉCÉDENT DE 24 h, et la fenêtre ne
 *      glissait plus — elle redevenait « depuis le boot », ce que `dn_hist.h`
 *      interdit explicitement.
 *    · IDENTITÉ FAUSSE. Au bout de 24 h, l'heure 27 a le MÊME index d'anneau
 *      que l'heure 3 : `b == s_seau_courant` répondait « même seau » sur deux
 *      instants distants d'une journée, et le vidage n'avait jamais lieu.
 *    L'index absolu ne peut faire ni l'un ni l'autre : il est monotone.
 */
static int64_t s_seau_abs = -1;
/*
 * 🔴 dn4-13 / AC2.2 — `s_seaux_ouverts` A ÉTÉ SUPPRIMÉ, ET SON COMMENTAIRE AVEC.
 *    Il portait : « C'est LUI qui donne la couverture réelle, ⛔ pas une
 *    constante ». C'ÉTAIT FAUX DEUX FOIS.
 *    1. Il n'était JAMAIS LU (3 écritures, 0 lecture — revue du 2026-08-24) :
 *       il ne donnait donc rien du tout.
 *    2. Même branché, il n'aurait pas donné « la couverture réelle » : il compte
 *       les seaux TRAVERSÉS PAR L'HORLOGE, qu'ils aient vu du réel ou non.
 *       C'est de l'UPTIME déguisé en observation — exactement le mensonge que
 *       `dn_hist.h` interdit trois paragraphes plus haut.
 *    ⇒ La couverture se lit désormais sur `s_svu[]`, le seul tableau qui sache
 *      qu'un seau A VU DU RÉEL. Voir `dn_hist_couverture_s()`.
 */

/*
 * 🔴 dn4-13 / AC3.1 — L'HORODATAGE DU DERNIER ÉCHANTILLONNAGE, EN TEMPS **RÉEL**.
 * ⚠️ `esp_timer_get_time()`, ⛔ PAS le tick LVGL : `lvgl_port_pause()` arrête le
 *    tick, donc un `ui off` de 60 s est INVISIBLE pour LVGL — c'est précisément
 *    ce qui permettait à la courbe de recoller les deux bords de la pause. Le
 *    seul temps qui ne ment pas ici est celui de la puce.
 */
static int64_t s_tick_us = -1;
static uint32_t s_rattr_evts;  /* combien de fois on a comblé */
static uint32_t s_rattr_trous; /* combien de points de trou comblés en tout */

void dn_hist_init(void)
{
    for (int s = 0; s < DN_HIST_N_SERIES; s++) {
        for (int i = 0; i < DN_HIST_N_POINTS; i++) {
            s_pts[s][i] = DN_HIST_TROU;
        }
        s_w[s] = 0;
        s_ecrits[s] = 0;
    }
    for (int s = 0; s < DN_HIST_N_SERIES; s++) {
        for (int b = 0; b < DN_HIST_SEAUX; b++) {
            s_svu[s][b] = false;
        }
    }
    s_seau_abs = -1;
    s_tick_us = -1;
    s_rattr_evts = 0;
    s_rattr_trous = 0;
    s_pret = true;
}

/* Ouvre (et VIDE) le seau de l'heure courante quand on y entre. ⛔ Sans ce
 * vidage, la fenêtre ne glisserait pas : elle deviendrait « depuis le boot ».
 *
 * 🔴 dn4-13 / AC3.2 — **TOUS** LES SEAUX TRAVERSÉS SONT VIDÉS, ⛔ PLUS SEULEMENT
 *    CELUI D'ARRIVÉE. Entre deux appels il peut s'écouler plus d'une heure — un
 *    `ui off` long, une carte qui dort, un échantillonneur arrêté. Les seaux
 *    sautés gardaient alors les valeurs du TOUR PRÉCÉDENT DE 24 h : la fenêtre
 *    « glissante » recollait un morceau d'avant-hier au milieu d'aujourd'hui,
 *    et rien ne le disait. */
static void seau_suivre(void)
{
    int64_t up_s = esp_timer_get_time() / 1000000;
    if (up_s < 0) {
        return;
    }
    int64_t abs_b = up_s / DN_HIST_SEAU_S;
    if (abs_b == s_seau_abs) {
        return;
    }
    /* Combien de seaux ENTRÉS depuis le dernier passage. Au premier appel, un
     * seul (celui où l'on naît). Borné à 24 : au-delà, tout l'anneau est neuf. */
    int64_t entres = (s_seau_abs < 0) ? 1 : (abs_b - s_seau_abs);
    if (entres > DN_HIST_SEAUX) {
        entres = DN_HIST_SEAUX;
    }
    if (entres < 1) {
        entres = 1; /* horloge qui recule : on ne réécrit rien en arrière */
    }
    for (int64_t k = 0; k < entres; k++) {
        int b = (int)((abs_b - k) % DN_HIST_SEAUX);
        for (int s = 0; s < DN_HIST_N_SERIES; s++) {
            s_svu[s][b] = false;
        }
    }
    s_seau_abs = abs_b;
}

/*
 * 🔴 dn4-13 / AC3.1 — L'ANNEAU RATTRAPE LE TEMPS QU'IL N'A PAS ÉCHANTILLONNÉ,
 *    EN CREUSANT DES TROUS.
 *
 * LE DÉFAUT, TEL QU'IL SE PRODUISAIT : `ui off` met LVGL en pause, donc
 * `hist_tick` ne tourne plus, donc l'anneau n'avance plus. Au `ui on`, le point
 * suivant s'écrivait **JUSTE À CÔTÉ** du dernier point d'avant la pause.
 * `lv_chart` reliait alors deux instants séparés de 60 s par un segment qui, à
 * l'écran, en vaut UNE. ⛔ La courbe ne mentait pas sur la valeur : elle mentait
 * sur la DURÉE — et `dn_hist.h` écrit lui-même que c'est *« un mensonge plus
 * difficile à voir »*.
 *
 * ⚠️ ON NE COMBLE QU'AU-DELÀ D'UNE PÉRIODE ENTIÈRE DE RETARD. Un timer à 1 Hz
 *    qui tire à 1 040 ms est le régime NORMAL ; creuser un trou à chaque gigue
 *    fabriquerait une courbe en pointillés sur une carte parfaitement saine.
 * ⚠️ BORNÉ À `DN_HIST_N_POINTS` : au-delà, tout l'anneau est du trou de toute
 *    façon, et boucler 86 400 fois sous le verrou LVGL serait pire que le mal.
 *
 * Rend le nombre de points de trou comblés (0 en régime).
 */
int dn_hist_rattraper(void)
{
    if (!s_pret) {
        return 0;
    }
    int64_t now = esp_timer_get_time();
    if (s_tick_us < 0 || now < s_tick_us) {
        s_tick_us = now;
        return 0;
    }
    int64_t dt_ms = (now - s_tick_us) / 1000;
    s_tick_us = now;
    int64_t manques = dt_ms / DN_HIST_PERIODE_MS - 1;
    if (manques <= 0) {
        return 0;
    }
    if (manques > DN_HIST_N_POINTS) {
        manques = DN_HIST_N_POINTS;
    }
    for (int64_t k = 0; k < manques; k++) {
        for (int s = 0; s < DN_HIST_N_SERIES; s++) {
            s_pts[s][s_w[s]] = DN_HIST_TROU;
            s_w[s] = (s_w[s] + 1u) % DN_HIST_N_POINTS;
            if (s_ecrits[s] < DN_HIST_N_POINTS) {
                s_ecrits[s]++;
            }
        }
    }
    s_rattr_evts++;
    s_rattr_trous += (uint32_t)manques;
    return (int)manques;
}

void dn_hist_rattrapages(uint32_t *evenements, uint32_t *trous)
{
    if (evenements) { *evenements = s_rattr_evts; }
    if (trous) { *trous = s_rattr_trous; }
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
    if (s_ecrits[serie] < DN_HIST_N_POINTS) {
        s_ecrits[serie]++;
    }

    /* ⚠️ LE SEAU NE REÇOIT QUE DU RÉEL, comme l'anneau. Un trou n'abaisse aucun
     *    minimum et ne relève aucun maximum : il n'existe simplement pas. */
    seau_suivre();
    if (!connue || s_seau_abs < 0) {
        return;
    }
    int b = (int)(s_seau_abs % DN_HIST_SEAUX);
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
    if (!s_pret || serie < 0 || serie >= DN_HIST_N_SERIES) {
        return false; /* dn4-13 / AC2.3 — voir `dn_hist_points()` */
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

uint32_t dn_hist_couverture_s(int serie)
{
    /*
     * 🔴 dn4-13 / AC2.2 — CE QUI A ÉTÉ **OBSERVÉ**, ⛔ PLUS L'UPTIME.
     *
     * ⚠️ LA VERSION PRÉCÉDENTE RENDAIT `min(uptime, 24 h)` SOUS UN COMMENTAIRE
     *    QUI PROMETTAIT « CE QUI A VRAIMENT ÉTÉ OBSERVÉ ». Le témoin qui le
     *    démontre est trivial et n'avait jamais été tiré : carte allumée > 1 h,
     *    AUCUNE source PC branchée ⇒ la page annonçait « MIN/MAX sur : 1 h »
     *    juste à côté de « MIN -- · MAX -- ». Une fenêtre d'observation d'une
     *    heure sur ZÉRO observation.
     *
     * ⇒ La couverture est celle des SEAUX QUI PORTENT DU RÉEL, et elle est
     *   **PAR SÉRIE** : deux séries de la même page peuvent avoir commencé à
     *   des instants différents (`RÉSEAU` ↓ et ↑ arrivent ensemble, mais
     *   `AMBIANCE` T et H peuvent diverger si un capteur se tait).
     *
     * Calcul : l'âge, en seaux, du PLUS ANCIEN seau qui a vu du réel, plus le
     * temps déjà écoulé dans le seau courant. Borné par l'uptime — sinon un
     * seau ouvert il y a 40 s annoncerait « 1 h » par le seul fait d'être le
     * seau d'une heure.
     * ⛔ Aucun seau réel ⇒ **0**, ⛔ jamais l'uptime.
     */
    if (!s_pret || serie < 0 || serie >= DN_HIST_N_SERIES) {
        return 0;
    }
    int64_t up_s = esp_timer_get_time() / 1000000;
    if (up_s < 0) {
        return 0;
    }
    int cur = (int)((up_s / DN_HIST_SEAU_S) % DN_HIST_SEAUX);
    int age_max = -1;
    for (int b = 0; b < DN_HIST_SEAUX; b++) {
        if (!s_svu[serie][b]) {
            continue;
        }
        int age = (cur - b + DN_HIST_SEAUX) % DN_HIST_SEAUX;
        if (age > age_max) {
            age_max = age;
        }
    }
    if (age_max < 0) {
        return 0;
    }
    uint32_t couv = (uint32_t)age_max * (uint32_t)DN_HIST_SEAU_S +
                    (uint32_t)(up_s % DN_HIST_SEAU_S);
    return (uint32_t)up_s < couv ? (uint32_t)up_s : couv;
}

int32_t *dn_hist_points(int serie)
{
    /*
     * 🔴 dn4-13 / AC2.3 — `s_pret` GARDE LES SIX LECTEURS, ⛔ PLUS LE SEUL
     *    ÉCRIVAIN.
     *    Avant init, `s_pts[][]` est le `.bss`, donc ZÉRO — et zéro est une
     *    VALEUR. `dn_hist_minmax()` comptait ces 120 zéros comme RÉELS et
     *    rendait une plage `0..0` que `dn_hist.h:18-19` déclare interdite ;
     *    `lv_chart` aurait tracé une ligne plate à zéro sur deux minutes de
     *    données qui n'existent pas. Le trou se code `INT32_MAX`, ⛔ pas 0 :
     *    l'état `.bss` n'est donc PAS un état neutre, c'est un état MENTEUR.
     * ⚠️ Et ce n'était pas théorique : `dn_hist_init()` était appelée APRÈS
     *    `build_scene()`, qui reparamètre déjà la courbe. Corrigé aussi.
     */
    if (!s_pret || serie < 0 || serie >= DN_HIST_N_SERIES) {
        return NULL;
    }
    return s_pts[serie];
}

uint32_t dn_hist_debut(int serie)
{
    /* dn4-13 / AC2.3 — voir `dn_hist_points()`. Le `0` rendu ici n'est pas un
     * verdict : c'est un index, et il est INEXPLOITABLE sans le tableau, que
     * `dn_hist_points()` refuse au même instant. */
    if (!s_pret || serie < 0 || serie >= DN_HIST_N_SERIES) {
        return 0;
    }
    return s_w[serie];
}

bool dn_hist_minmax(int serie, int32_t *min, int32_t *max)
{
    if (!s_pret || serie < 0 || serie >= DN_HIST_N_SERIES) {
        return false; /* dn4-13 / AC2.3 — ⛔ « pas de plage », ⛔ pas `0..0` */
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

int dn_hist_ecrits(int serie)
{
    /* dn4-13 / AC6.3 — même garde `s_pret` que les autres lecteurs : avant
     * l'init, « 0 position écrite » est la vérité, et c'est ce qu'on rend. */
    if (!s_pret || serie < 0 || serie >= DN_HIST_N_SERIES) {
        return 0;
    }
    return (int)s_ecrits[serie];
}

int dn_hist_reels(int serie)
{
    /* dn4-13 / AC2.3 — avant init, « 0 point réel » est la VÉRITÉ, et c'est
     * aussi ce que ce garde rend. Il est là quand même : sans lui, la boucle
     * ci-dessous lirait 120 zéros du `.bss` et en compterait 120 RÉELS. */
    if (!s_pret || serie < 0 || serie >= DN_HIST_N_SERIES) {
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
    /* 🔴 ~~`AMBIANCE` EST LA SEULE PAGE À DEUX COURBES~~ — addendum §1,
     *    exception 1. **PÉRIMÉ LE 2026-08-24** (demande owner : `RÉSEAU` en
     *    porte deux aussi). ⛔ Bloc conservé BARRÉ, ⛔ pas effacé — il dit d'où
     *    vient la règle. Le bloc ci-dessous est celui qui fait foi.
     *    ⚠️ Constat de la revue de code du 2026-08-24 : ce bloc était resté
     *       DEBOUT au-dessus de celui qui le corrige, donc un lecteur pressé
     *       repartait avec l'affirmation fausse. */
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

/*
 * 🔴 dn4-13 / AC2.1 — LE COÛT **RÉEL** DU MODULE, ⛔ PLUS `sizeof(s_pts)` SEUL.
 *
 * L'ancienne version rendait 3 840 o — les points, et rien d'autre — alors que
 * le module en occupe ~5 600. Sous-déclaration de ~32 %, ET C'ÉTAIT
 * L'INSTRUMENT CENSÉ SOLDER AC5.6 : le chiffre qu'on confrontait à la
 * prédiction n'était pas le chiffre du module.
 * ⚠️ On ne l'écrit pas « de tête » : chaque terme est un `sizeof` du symbole
 *    réel, donc il suit automatiquement `DN_HIST_N_SERIES` et `DN_HIST_SEAUX`.
 *    C'est la seule forme qui ne puisse pas périmer en silence — les trois
 *    chiffres publiés (1 344 / 1 536 / 1 728) ont tous péri de l'être.
 * ⚠️ `s_pret` et `s_seau_courant` sont comptés : ils sont du `.bss` du module.
 *    Le compilateur peut les aligner ou les fusionner autrement — la confrontation
 *    au `.map` (gate `verif_hist_dn413.py`) est là pour dire l'écart, pas pour
 *    être contournée.
 */
size_t dn_hist_octets_detail(size_t *points, size_t *seaux, size_t *index)
{
    size_t p = sizeof(s_pts);
    size_t b = sizeof(s_smin) + sizeof(s_smax) + sizeof(s_svu);
    size_t i = sizeof(s_w) + sizeof(s_ecrits) + sizeof(s_pret) +
               sizeof(s_seau_abs) + sizeof(s_tick_us) + sizeof(s_rattr_evts) +
               sizeof(s_rattr_trous);
    if (points) { *points = p; }
    if (seaux) { *seaux = b; }
    if (index) { *index = i; }
    return p + b + i;
}

size_t dn_hist_octets(void) { return dn_hist_octets_detail(NULL, NULL, NULL); }

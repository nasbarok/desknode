/*
 * DeskNode — `dn_demarrage` : LA DÉCISION, ET RIEN D'AUTRE.
 *
 * ⛔ AUCUN `#include` DU FRAMEWORK. Le motif est écrit en tête de
 *    `dn_demarrage.h` : c'est ce qui permet à `verif_demarrage_dn443.py` de
 *    COMPILER ce fichier et d'APPELER ses fonctions — au lieu de les lire au
 *    `grep`. Une gate qui lit ne prouve pas ; une gate qui exécute, si.
 * ⚠️ Le journal appartient à `dn_ui.c`, qui a le contexte (et la console
 *    publie les compteurs). ⛔ Y faire entrer `esp_log.h` obligerait la gate à
 *    porter un shim, et un shim dérive.
 */
#include "dn_demarrage.h"

/* ── L'ÉTAT. Un seul état de démarrage par vie de firmware, et c'est le
 *    point (AC1.4). ─────────────────────────────────────────────────────── */

static bool s_arme;
static bool s_tactile_present;
static dn_dem_verdict_t s_verdict = DN_DEM_EN_COURS;

static uint32_t s_t0_ms;    /* instant de l'armement */
static uint32_t s_duree_ms; /* FIGÉE à la conclusion */

/* La fenêtre d'observation COURANTE — elle repart à chaque erreur nouvelle. */
static uint32_t s_fen_t0_ms;
static uint32_t s_fen_err0;
static uint32_t s_fen_lect0;

/* Les instruments. ⛔ Aucun n'est décoratif : `dn4-41` a payé *« un instrument
 * qu'on ne peut pas LIRE ne disculpe personne »*. */
static uint32_t s_err_vues;
static uint32_t s_lectures_vues;
static uint32_t s_fen_cassees;
static uint32_t s_rearm_refuses;

const char *dn_dem_verdict_nom(dn_dem_verdict_t v)
{
    switch (v) {
    case DN_DEM_EN_COURS:
        return "EN COURS";
    case DN_DEM_FIN_PROPRE:
        return "PROPRE";
    case DN_DEM_FIN_SANS_TACTILE:
        return "SANS TACTILE";
    case DN_DEM_FIN_PLAFOND:
        return "PLAFOND";
    case DN_DEM_FIN_RECONSTRUCTION:
        return "RECONSTRUCTION";
    default:
        /* ⛔ NE PAS ENLEVER : un verdict neuf ajouté à l'enum sans branche ici
         *    doit rendre « ? », ⛔ pas le mot du verdict d'à côté. C'est la
         *    règle que `veille_mode_nom_ui()` applique déjà dans `dn_ui.c`. */
        return "?";
    }
}

void dn_dem_armer(uint32_t t_ms, bool tactile_present, uint32_t err_i2c,
                  uint32_t lectures)
{
    /*
     * 🔴 AC1.4 — **IL NE SE RÉ-ARME JAMAIS.** `build_scene()` est appelée par
     *    des commandes console et par un changement de langue : un état de
     *    démarrage qui reparaîtrait alors serait un instrument qui MENT sur ce
     *    qu'il mesure — il annoncerait « premier démarrage » sur une carte qui
     *    tourne depuis une heure.
     * ⚠️ Le refus est COMPTÉ, ⛔ pas silencieux.
     */
    if (s_verdict != DN_DEM_EN_COURS) {
        s_rearm_refuses++;
        return;
    }
    if (s_arme) {
        s_rearm_refuses++;
        return;
    }
    s_arme = true;
    s_tactile_present = tactile_present;
    s_t0_ms = t_ms;
    s_duree_ms = 0;
    s_fen_t0_ms = t_ms;
    s_fen_err0 = err_i2c;
    s_fen_lect0 = lectures;
    s_err_vues = 0;
    s_lectures_vues = 0;
    s_fen_cassees = 0;
}

static void conclure(uint32_t t_ms, dn_dem_verdict_t v)
{
    s_duree_ms = t_ms - s_t0_ms;
    s_verdict = v;
}

dn_dem_verdict_t dn_dem_tick(uint32_t t_ms, uint32_t err_i2c, uint32_t lectures)
{
    if (s_verdict != DN_DEM_EN_COURS) {
        return s_verdict; /* idempotente : une fin est définitive */
    }
    if (!s_arme) {
        /* Le timer LVGL existe avant l'armement (il est créé par `dn_ui_init`,
         * l'armement vient de `app_main` APRÈS le branchement de l'indev).
         * ⛔ Ne rien conclure ici : les compteurs ne sont pas encore lisibles. */
        return DN_DEM_EN_COURS;
    }

    s_duree_ms = t_ms - s_t0_ms;

    /*
     * ⚠️ LE CAS « PAS DE TACTILE » EST TRAITÉ **EN PREMIER**, ET C'EST DÉLIBÉRÉ.
     *    Sans indev, `lectures` et `err_i2c` restent figés à 0 : la fenêtre
     *    serait « propre » sur des compteurs IMMOBILES — c'est-à-dire qu'elle
     *    mesurerait du vide, et l'écran annoncerait « prêt » sur une carte qui
     *    ne répondra JAMAIS au doigt.
     */
    if (!s_tactile_present) {
        conclure(t_ms, DN_DEM_FIN_SANS_TACTILE);
        return s_verdict;
    }

    /*
     * 🔴 LA FENÊTRE SE CASSE À LA PREMIÈRE ERREUR NOUVELLE — c'est LE critère.
     * ⚠️ ET ELLE SE CASSE AUSSI SI UN COMPTEUR RECULE. `touch reset` remet les
     *    compteurs à zéro depuis la console : sans ce test, la soustraction
     *    `lectures - s_fen_lect0` déborderait par le bas et rendrait ~4
     *    milliards — c'est-à-dire que le garde-fou du vide serait franchi PAR
     *    L'UNDERFLOW, sur des compteurs qui viennent d'être effacés. Un geste
     *    d'opérateur ne doit pas pouvoir conclure une observation à sa place.
     */
    if (err_i2c > s_fen_err0) {
        s_err_vues += err_i2c - s_fen_err0;
    }
    if (err_i2c != s_fen_err0 || lectures < s_fen_lect0) {
        s_fen_t0_ms = t_ms;
        s_fen_err0 = err_i2c;
        s_fen_lect0 = lectures;
        s_fen_cassees++;
        return DN_DEM_EN_COURS;
    }

    s_lectures_vues = lectures - s_fen_lect0;

    /*
     * ✅ LE CRITÈRE RELU PASSE **AVANT** LE PLAFOND, et l'ordre est le fond du
     *    sujet : si la fenêtre vient de se conclure au même tick que le
     *    plafond, c'est l'ÉTAT qui décide, ⛔ pas le minuteur. Inverser ces deux
     *    blocs ferait annoncer `PLAFOND` sur une carte rétablie — et une mesure
     *    lirait « on a cessé d'attendre » là où il fallait lire « c'est propre ».
     */
    if ((uint32_t)(t_ms - s_fen_t0_ms) >= DN_DEM_FENETRE_MS
        && s_lectures_vues >= DN_DEM_LECTURES_MIN) {
        conclure(t_ms, DN_DEM_FIN_PROPRE);
        return s_verdict;
    }

    if ((uint32_t)(t_ms - s_t0_ms) >= DN_DEM_PLAFOND_MS) {
        conclure(t_ms, DN_DEM_FIN_PLAFOND);
        return s_verdict;
    }

    return DN_DEM_EN_COURS;
}

void dn_dem_conclure(uint32_t t_ms, dn_dem_verdict_t v)
{
    if (!s_arme || s_verdict != DN_DEM_EN_COURS) {
        return;
    }
    conclure(t_ms, v);
}

dn_dem_verdict_t dn_dem_verdict(void) { return s_verdict; }
bool dn_dem_arme(void) { return s_arme; }
bool dn_dem_en_cours(void) { return s_arme && s_verdict == DN_DEM_EN_COURS; }
uint32_t dn_dem_duree_ms(void) { return s_duree_ms; }
uint32_t dn_dem_err_vues(void) { return s_err_vues; }
uint32_t dn_dem_fenetres_cassees(void) { return s_fen_cassees; }
uint32_t dn_dem_lectures_vues(void) { return s_lectures_vues; }
uint32_t dn_dem_rearmements_refuses(void) { return s_rearm_refuses; }

void dn_dem_reset_pour_gate(void)
{
    s_arme = false;
    s_tactile_present = false;
    s_verdict = DN_DEM_EN_COURS;
    s_t0_ms = 0;
    s_duree_ms = 0;
    s_fen_t0_ms = 0;
    s_fen_err0 = 0;
    s_fen_lect0 = 0;
    s_err_vues = 0;
    s_lectures_vues = 0;
    s_fen_cassees = 0;
    s_rearm_refuses = 0;
}

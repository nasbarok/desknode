/*
 * DeskNode — `dn_demarrage` : LE PREMIER DÉMARRAGE SE DIT, ET IL SE TERMINE SUR
 *                             UN CRITÈRE RELU.
 * Né de `dn4-43`. Origine d'exigence : PRFAQ, angle mort I4, arbitrage owner du
 * 2026-08-31 ; voie UI tranchée par l'owner le 2026-09-01.
 *
 * ══════════════════════════════════════════════════════════════════════════
 * 🔴 LE DÉFAUT QUE CE MODULE EXISTE POUR LEVER — ⛔ CE N'EST PAS « L'ÉCRAN NE
 *    MONTRE RIEN », C'EST L'INVERSE
 * ══════════════════════════════════════════════════════════════════════════
 *
 * L'ordre du boot (relu de `desknode_main.c`) allume le rétroéclairage à
 * l'étape **7**, c'est-à-dire APRÈS que la 1ʳᵉ trame LVGL a atteint la dalle
 * (étape 6) et **AVANT** que `dn_link`, `dn_capteurs`, `dn_env` et le RTC
 * n'existent (étapes 8, 8 bis, 8 ter).
 *
 * ⇒ **QUAND L'ÉCRAN S'ALLUME, LE DASHBOARD EST DÉJÀ COMPLET — ET AUCUNE SOURCE
 *   N'A ÉTÉ LUE.** Six cases, six titres, la barre… et `--` partout.
 *   L'inconnu ne voit pas un écran vide : il voit **une application FINIE ET
 *   PLAUSIBLE qui ne répond pas au doigt**. C'est un signal *pire* qu'un écran
 *   noir — rien ne dit que quelque chose est en cours.
 *
 * ⚠️ ET ÇA SE PRODUIT SUR UNE CARTE QUI VA BIEN. Sur celle qui va mal
 *    (§13.17.1 : **1 cycle sur 6**), s'ajoutent **~40 s à 55,5 % d'erreurs
 *    GT911** pendant lesquelles le doigt ne fait RIEN.
 *
 * ══════════════════════════════════════════════════════════════════════════
 * 🔴 POURQUOI CE MODULE N'INCLUT **NI LVGL, NI ESP-IDF** — ⛔ CE N'EST PAS UNE
 *    COQUETTERIE
 * ══════════════════════════════════════════════════════════════════════════
 *
 * `dn_veille.c` est **compilable et appelable SUR L'HÔTE**, et c'est la seule
 * raison pour laquelle `tools/verif_veille_dn33.py` peut EXÉCUTER la décision
 * au lieu de la lire au `grep`. Le CMakeLists le dit en toutes lettres : y
 * faire entrer une dépendance de plus *« ferait cesser cette gate de pouvoir
 * l'exécuter — et elle redeviendrait décorative »*.
 *
 * ⇒ La **DÉCISION** vit ici, sans un seul `#include` du framework :
 *   `tools/verif_demarrage_dn443.py` la compile en `.so` et l'appelle en
 *   `ctypes`, avec de VRAIS chiffres. ⛔ Aucun shim à écrire, donc aucun shim
 *   à laisser dériver.
 * ⇒ Le **DESSIN** et la **LECTURE des compteurs** vivent dans `dn_ui.c`, qui a
 *   LVGL et `dn_touch.h`. ⛔ Ce module ne lit rien de lui-même : on lui PASSE
 *   l'état relu. C'est exactement ce qui le rend éprouvable.
 *
 * ══════════════════════════════════════════════════════════════════════════
 * 🔴 LE CRITÈRE DE FIN — ⛔ PAS UN MINUTEUR, ET C'EST DE L'ARITHMÉTIQUE
 * ══════════════════════════════════════════════════════════════════════════
 *
 * Un `vTaskDelay(40000)` serait faux **dans les deux sens** : trop long **5
 * fois sur 6** (la fenêtre froide n'existe pas), trop court si le bus met plus
 * longtemps. ⇒ le critère se RELIT de l'état réel.
 *
 * ✅ **CE QUI EST MESURÉ** (`hardware/…-capteurs-i2c.md` §13.17.1, cycle 1) :
 *      · `dn_touch_err_i2c()` : **950 erreurs sur 1 713 lectures = 55,5 %**
 *      · puis **950 à T0, 950 à T+35 s** pendant que les lectures passaient de
 *        2 606 à 3 468 — **+862 lectures, ZÉRO erreur nouvelle** (≈ 25 lect./s)
 *      · reprise complète vers **T+~60 s**
 *
 * ⇒ **LE SIGNAL DE FIN EST « `err_i2c` A CESSÉ DE MONTER »**, et il est
 *   DISCRIMINANT : à 55,5 % d'échec et ≈ 25 lectures/s, une fenêtre propre de
 *   `DN_DEM_FENETRE_MS` (≈ 37 lectures) a une probabilité de
 *   `0,445 ^ 37 ≈ 9,8·10⁻¹⁴` d'arriver par hasard. ⛔ Ce n'est pas un minuteur
 *   déguisé.
 *
 * ⛔ **`dn_capt_etat()` EST DISQUALIFIÉ COMME CRITÈRE**, et c'est mesuré : il
 *    vaut `DN_CAPT_JAMAIS` **à TOUT boot**, sain compris, pendant jusqu'à
 *    `DN_CAPT_PERIODE_MS` = **5 000 ms**. L'attendre ajouterait **5 s d'attente
 *    à une carte qui va bien** — c'est-à-dire exactement ce qu'AC1.3 interdit.
 *
 * ⛔ **LE SCAN `i2c` EST DISQUALIFIÉ AUSSI**, et c'est le résultat-titre de
 *    §13.17.1 : il disait *« 8 stables, 0 instable »*, témoin positif **vert**,
 *    **pendant qu'une transaction de donnée sur deux échouait**.
 *    *Le scan DÉCOUVRE, seule une transaction de DONNÉE QUALIFIE.*
 *
 * ══════════════════════════════════════════════════════════════════════════
 * 🔴 LE PIÈGE DU VIDE — UNE FENÊTRE SANS LECTURES NE MESURE **RIEN**
 * ══════════════════════════════════════════════════════════════════════════
 *
 * Un compteur d'erreurs immobile a DEUX causes : le bus s'est rétabli, ou
 * **plus personne ne lit**. Les deux sont indiscernables sur le seul `err_i2c`.
 * ⇒ La fenêtre exige AUSSI que `lectures` ait progressé d'au moins
 *   `DN_DEM_LECTURES_MIN`. Sans ça, un tactile mort (compteurs figés à 0)
 *   sortirait de l'état de démarrage **par un compteur immobile**, c'est-à-dire
 *   en mesurant du vide — et l'écran annoncerait « prêt » sur une carte qui ne
 *   répondra JAMAIS au doigt.
 * ⇒ Le cas « tactile INDISPONIBLE » est donc traité **EXPLICITEMENT**
 *   (`DN_DEM_FIN_SANS_TACTILE`), ⛔ pas par accident.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

/* ══════════════════════════════════════════════════════════════════════════
 * LE BUDGET TEMPOREL, ET IL EST GARDÉ PAR LE COMPILATEUR
 * ══════════════════════════════════════════════════════════════════════════ */

/*
 * La fenêtre d'observation propre. **1 500 ms**, et c'est calculé, ⛔ pas rond :
 * à ≈ 25 lectures/s (mesuré), elle porte ≈ 37 lectures ⇒ `0,445 ^ 37 ≈ 9,8·10⁻¹⁴`
 * de chance de passer par hasard sous le régime dégradé.
 * ⚠️ C'est AUSSI ce que dure l'état de démarrage sur un boot SAIN (AC1.3) — les
 *    5 cas sur 6 où la fenêtre froide n'existe pas. ⛔ La rallonger ajouterait
 *    une attente à une carte qui va bien.
 */
#define DN_DEM_FENETRE_MS 1500u

/*
 * ⛔ LE GARDE-FOU DU VIDE. Une fenêtre qui ne porte pas AU MOINS ce nombre de
 * lectures n'a rien observé, et ⛔ ne conclut pas.
 */
#define DN_DEM_LECTURES_MIN 20u

/*
 * 🔴 LE PLANCHER DE CADENCE, **MESURÉ**, ⛔ PAS SUPPOSÉ : 862 lectures en 35 s
 *    = 24,6/s au cycle 1 de §13.17.1, et 353..659 par cycle sur les boots
 *    sains. On retient **20/s**, en dessous du pire relevé.
 * ⚠️ Il ne sert qu'à l'arithmétique du `_Static_assert` ci-dessous : le code,
 *    lui, ⛔ ne suppose AUCUNE cadence — il COMPTE les lectures réelles.
 */
#define DN_DEM_LECTURES_PAR_S_PLANCHER 20u

/*
 * ⚠️ **LE PLAFOND DE TEMPS EST DÉCLARÉ, ET IL EST « EN PLUS », ⛔ PAS « À LA
 *    PLACE »** (AC1.2). **90 s** : les 950 erreurs du cycle 1 se sont TOUTES
 *    produites dans les ~40 premières secondes et la reprise complète tombe
 *    vers T+~60 s (§13.17.1) ⇒ 90 s = le pire mesuré + ~50 % de marge.
 * 🔴 CE QU'IL SIGNIFIE QUAND IL TOMBE : ⛔ **PAS** « la carte est prête ». Il
 *    dit *« on a cessé d'attendre »*, et `DN_DEM_FIN_PLAFOND` le NOMME — pour
 *    qu'une mesure ne puisse pas confondre les deux fins.
 */
#define DN_DEM_PLAFOND_MS 90000u

/*
 * 🔴 LE BUDGET EST GARDÉ PAR LE COMPILATEUR, comme `dn4-41` et `dn4-42` l'ont
 *    fait pour la géométrie. ⛔ Un commentaire qui additionne se périme au
 *    premier nombre déplacé.
 */
_Static_assert(DN_DEM_FENETRE_MS < DN_DEM_PLAFOND_MS,
               "dn4-43 : la fenetre d'observation depasse le plafond — le "
               "critere RELU ne pourrait JAMAIS conclure avant le minuteur, "
               "c'est-a-dire que le plafond serait « a la place » et non « en "
               "plus » (AC1.2).");
_Static_assert(DN_DEM_LECTURES_MIN * 1000u
                   <= DN_DEM_FENETRE_MS * DN_DEM_LECTURES_PAR_S_PLANCHER,
               "dn4-43 : la fenetre est trop COURTE pour porter "
               "DN_DEM_LECTURES_MIN lectures a la cadence PLANCHER MESUREE. "
               "Elle ne pourrait se conclure qu'au plafond, sur toutes les "
               "cartes — refaire l'arithmetique de §13.17.1.");
_Static_assert(DN_DEM_LECTURES_MIN > 0u,
               "dn4-43 : une fenetre a ZERO lecture exigee ne mesure RIEN — "
               "c'est exactement le piege du vide que ce module documente.");

/* ══════════════════════════════════════════════════════════════════════════
 * LE VERDICT — QUATRE FINS, ET ELLES NE SE CONFONDENT PAS
 * ══════════════════════════════════════════════════════════════════════════ */

typedef enum {
    /* L'état de démarrage est à l'écran. */
    DN_DEM_EN_COURS = 0,
    /* ✅ Le critère RELU est tombé : `err_i2c` figé sur une fenêtre PEUPLÉE. */
    DN_DEM_FIN_PROPRE,
    /* ⚠️ Le GT911 n'a pas répondu au bring-up, ou l'indev n'est pas branché.
     * ⛔ CE N'EST PAS « la carte est prête » : c'est « l'observation est
     * IMPOSSIBLE ». Le dashboard ne répondra pas au doigt, et la console dit
     * pourquoi (`touch`). Le faire durer n'y changerait rien. */
    DN_DEM_FIN_SANS_TACTILE,
    /* ⚠️ Le plafond. ⛔ PAS un verdict de santé — voir DN_DEM_PLAFOND_MS. */
    DN_DEM_FIN_PLAFOND,
    /* ⚠️ La scène a été reconstruite sous l'état de démarrage (commande
     * console, changement de langue). C'est un geste d'OPÉRATEUR, ⛔ pas le
     * parcours de l'inconnu. ⇒ l'état se termine, et il ⛔ NE SE RÉ-AFFICHE
     * PAS (AC1.4). */
    DN_DEM_FIN_RECONSTRUCTION,
} dn_dem_verdict_t;

/* Le nom du verdict. ⛔ Ne rend JAMAIS NULL — un `default` couvre les valeurs
 * hors enum, pour qu'un verdict neuf non traité rende « ? » et ⛔ pas le mot
 * d'un autre. */
const char *dn_dem_verdict_nom(dn_dem_verdict_t v);

/* ══════════════════════════════════════════════════════════════════════════
 * L'API — DEUX APPELS, ET UNE MACHINE QUI NE SE RÉ-ARME JAMAIS
 * ══════════════════════════════════════════════════════════════════════════ */

/*
 * Arme l'observation. `t_ms` est une base de temps monotone en millisecondes,
 * `err_i2c` et `lectures` les compteurs cumulatifs RELUS À CET INSTANT.
 *
 * 🔴 ELLE EST APPELÉE **APRÈS** LE BRANCHEMENT DE L'INDEV, ⛔ PAS AVANT, et
 *    c'est une course réelle : armée trop tôt, `tactile_present` serait faux
 *    parce que `dn_touch_attach_lvgl()` n'a pas encore tourné, et l'état de
 *    démarrage se terminerait aussitôt sur `SANS_TACTILE` — sur une carte
 *    parfaitement saine.
 *
 * ⛔ **UN SECOND APPEL APRÈS UNE FIN NE RÉ-ARME RIEN** (AC1.4). Il est ignoré,
 *    et `dn_dem_rearmements_refuses()` le COMPTE : un refus muet ne se
 *    diagnostique pas.
 */
void dn_dem_armer(uint32_t t_ms, bool tactile_present, uint32_t err_i2c,
                  uint32_t lectures);

/*
 * Fait avancer la machine avec l'état RELU. Rend le verdict courant.
 * Idempotente une fois conclue : elle rend la même fin indéfiniment.
 */
dn_dem_verdict_t dn_dem_tick(uint32_t t_ms, uint32_t err_i2c, uint32_t lectures);

/*
 * Conclut de l'extérieur — le SEUL cas est la reconstruction de scène.
 * ⛔ Sans effet si la machine est déjà conclue, ou pas encore armée.
 */
void dn_dem_conclure(uint32_t t_ms, dn_dem_verdict_t v);

/* ── Ce que la machine SAIT, et que la console et la gate LISENT ──────────── */

dn_dem_verdict_t dn_dem_verdict(void);
bool dn_dem_arme(void);
/* Vrai tant que l'état de démarrage doit rester à l'écran. */
bool dn_dem_en_cours(void);
/* Durée de l'état de démarrage, en ms. FIGÉE à la conclusion. */
uint32_t dn_dem_duree_ms(void);
/*
 * 🎯 LES ERREURS I²C CONSTATÉES **PENDANT** L'ÉTAT DE DÉMARRAGE.
 * C'est ce chiffre — et ⛔ pas un minuteur — qui décide si l'écran nomme le
 * tactile (AC3.4, arbitrage owner « en deux temps » du 2026-09-01) : sur les
 * 5 boots sains sur 6 il vaut **0**, et l'inconnu ne lit alors AUCUN
 * avertissement qui ne le concerne pas.
 */
uint32_t dn_dem_err_vues(void);
/* Combien de fois la fenêtre d'observation a dû être RELANCÉE. Non nul = le bus
 * a vraiment raté pendant l'attente. ⛔ Un 0 ne prouve rien à lui seul : il faut
 * le lire AVEC `dn_dem_lectures_vues()`.
 * 🎯 REVUE `dn4-43` — c'est le SEUL des instruments d'AC1.4 qui puisse bouger
 *    sur la carte sans geste de gate : `dn_dem_rearmements_refuses()`, lui, est
 *    structurellement mort côté firmware (voir son docbloc). */
uint32_t dn_dem_fenetres_cassees(void);
/*
 * Lectures tactiles portées par la fenêtre d'observation **COURANTE**.
 * 🔴 REVUE `dn4-43` (2026-09-01) — ⛔ CE N'EST PAS « pendant l'état », ET LE
 *    DOCBLOC LE DISAIT. Deux conséquences, écrites plutôt que tues :
 *    · sur une conclusion `DN_DEM_FIN_PROPRE` il vaut ≥ `DN_DEM_LECTURES_MIN`
 *      **par construction** ⇒ ⛔ il ne peut RIEN démentir là-bas, ce serait un
 *      contrôle auto-réalisateur. Le piège du vide est fermé par le test lui-
 *      même, ⛔ pas par la relecture de ce compteur ;
 *    · il est remis à **0** dès qu'une fenêtre se casse — sinon il publierait
 *      le compte d'une fenêtre DÉTRUITE.
 * ⇒ Là où il PARLE, c'est sur une fin `PLAFOND` ou `SANS_TACTILE` : un 0 y dit
 *   que la dernière fenêtre n'avait rien observé.
 */
uint32_t dn_dem_lectures_vues(void);
/*
 * Combien d'appels à `dn_dem_armer()` ont été REFUSÉS après une fin (AC1.4).
 * ⚠️ REVUE `dn4-43` (2026-09-01) — ⛔ **CE COMPTEUR NE PEUT PAS BOUGER SUR LA
 *    CARTE, ET IL NE FAUT PAS LIRE SON 0 COMME UNE PREUVE.** Aucun chemin du
 *    firmware n'appelle `dn_dem_armer()` deux fois : `app_main` l'appelle une
 *    fois, à l'étape 4 ter. Un 0 en séance carte dit donc *« le second appel n'a
 *    pas eu lieu »*, ⛔ pas *« le refus fonctionne »*.
 * ⇒ Le refus n'est exercé que par `verif_demarrage_dn443.py`, qui rejoue
 *   plusieurs armements dans un même `.so`. La propriété AC1.4 tient **par
 *   construction** ; ce compteur est là pour le jour où un appelant neuf
 *   naîtrait — et ce jour-là il parlera.
 */
uint32_t dn_dem_rearmements_refuses(void);

/*
 * ⛔ **AUCUN APPELANT DANS LE FIRMWARE — ET LA GATE LE CONTRÔLE.**
 * Elle n'existe que pour que `tools/verif_demarrage_dn443.py` puisse rejouer
 * plusieurs scénarios dans un même `.so`. Un appel depuis le firmware
 * ré-ouvrirait exactement la porte qu'AC1.4 ferme.
 */
void dn_dem_reset_pour_gate(void);

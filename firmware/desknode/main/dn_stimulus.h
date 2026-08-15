/*
 * DeskNode — les deux STIMULI, sans lesquels AC5 et AC6 mesurent du vide.
 *
 *   AC5 : « une image statique ne peut pas déchirer — il n'y a rien à
 *          déchirer ». Le stimulus bascule plein écran entre deux images très
 *          contrastées, aussi vite que la carte tient.
 *   AC6 : le scintillement annoncé vient d'une écriture FLASH qui stalle le
 *          refill PSRAM. Sans écriture flash, rien à voir. Le stimulus efface
 *          et réécrit des secteurs de la partition `stimulus` — jamais de nvs,
 *          jamais de factory.
 *
 * MÉTHODE DU TÉMOIN POSITIF (imposée par dn1-1) : avant de conclure « rien ne
 * s'est passé », on prouve que l'instrument aurait su le voir. Ici, le témoin
 * positif du tearing est la configuration num_fbs=1, où l'on écrit DANS le
 * framebuffer que la DMA est en train de lire : le déchirement DOIT s'y voir.
 * S'il ne s'y voit pas, ce n'est pas « pas de tearing », c'est un instrument
 * invalide — et il faut le dire.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"

/* ── Stimulus de tearing ─────────────────────────────────────────────────── */
/*
 * Les CINQ branches de l'A/B d'AC5, gardées dans le code pour être rejouables.
 * Résultat MESURÉ le 2026-08-14, à num_fbs=2 sauf SWEEP qui sert de témoin :
 *
 *   SWEEP        num_fbs=1 : escalier franc, tranches inégales.
 *                => TÉMOIN POSITIF : l'instrument voit bien le déchirement.
 *   SWEEP        num_fbs=2 : INCHANGÉ. La parade annoncée (« double
 *                framebuffer + VSYNC ») ne marche pas avec le seul double
 *                tampon : `draw_bitmap` bascule le lien DMA immédiatement.
 *   SYNC_VSYNC   escalier réduit à la moitié de la barre.
 *   SYNC_FBDONE  escalier résiduel confiné aux ~15 % du haut.  <== RETENU
 *   SYNC_BOTH    RÉGRESSION : retour au niveau de SYNC_VSYNC.
 *
 * ⚠️ Ces chiffres valent pour un stimulus ADVERSE : trame pleine redessinée
 *    (614 400 o) à la cadence maximale, soit ~30 ms par trame contre 26,7 ms
 *    de période d'affichage. Une UI réelle redessine des rectangles sales, pas
 *    la trame entière — le résiduel des 15 % est mesuré sous une charge que le
 *    produit ne verra pas.
 *
 * ⚠️⚠️ CE QUI EST À REJOUER, ET POURQUOI. Les VERDICTS ci-dessus sont des
 *    observations directes de l'owner et restent ce qui a été VU. Les CHIFFRES
 *    de cadence qui les accompagnent, eux, ont été relevés avec un instrument
 *    qui portait deux défauts depuis corrigés :
 *      - le générateur de trame était le goulot, pas le pipeline (remplissage
 *        pixel par pixel + un modulo par pixel ; voir le bloc « Générateur de
 *        trame » dans dn_stimulus.c). Le « ~30 ms par trame » ci-dessus mesure
 *        donc cette boucle-là, pas la dalle ;
 *      - l'attente de fin de trame jetait l'événement qu'elle attendait, d'où
 *        une trame de latence en trop, non déterministe, sur les modes FBDONE
 *        et BOTH (voir dn_measure.h).
 *    ⇒ Les conditions de l'A/B ont changé : la campagne AC5 est à REJOUER sur
 *      la carte avant de citer une cadence. Action owner ouverte.
 */
typedef enum {
    DN_TEAR_SWEEP = 0,   /* barre verticale balayante, aucune synchronisation */
    DN_TEAR_FLIP,        /* bascule noir/blanc plein écran — littéral, mais son
                          * papillotement masque le déchirement */
    DN_TEAR_SYNC_VSYNC,  /* bascule après le VSYNC */
    DN_TEAR_SYNC_FBDONE, /* attente de on_frame_buf_complete — RETENU */
    DN_TEAR_SYNC_BOTH,   /* les deux — mesuré PIRE que FBDONE seul */
} dn_tear_mode_t;

/* Refuse de démarrer tant qu'une tâche de tearing vit ENCORE — y compris
 * pendant l'extinction d'une précédente : deux tâches dessinant le même
 * framebuffer rendaient toute cadence mesurée absurde. */
esp_err_t dn_stim_tear_start(dn_tear_mode_t mode);

/*
 * Demande l'arrêt ET attend la sortie effective de la tâche.
 * ⚠️ RENVOIE UN CODE, ET IL FAUT LE REGARDER : ESP_ERR_TIMEOUT signifie que la
 *    tâche n'est PAS sortie dans le budget d'attente — donc qu'elle dessine
 *    peut-être encore. Cette fonction rendait la main en journalisant
 *    « arrêté » sans jamais tester l'attente ; un `scene x` qui suivait se
 *    faisait alors écraser par une tâche censée morte.
 */
esp_err_t dn_stim_tear_stop(void);

/* ⚠️ « en cours » = la TÂCHE VIT (y compris pendant l'extinction), pas « on a
 *    demandé le démarrage ». C'est ce que doit tester quiconque veut dessiner
 *    à l'écran. */
bool dn_stim_tear_running(void);
/* Cadence réellement atteinte (bascules par seconde) et durée moyenne d'une
 * trame complète, en microsecondes. */
void dn_stim_tear_stats(double *out_hz, int64_t *out_frame_us);

/*
 * Rendez-vous MANQUÉS depuis le démarrage : attentes de VSYNC et de fin de
 * trame qui ont expiré (100 ms).
 *
 * ⚠️ À AFFICHER AVEC LA CADENCE, jamais séparément. Un rendez-vous manqué fait
 *    passer la trame SANS synchronisation : un `tear sync` qui en accumule se
 *    comporte comme un `tear on`, et l'A/B compare alors « pas de sync » à
 *    « pas de sync » avec deux étiquettes différentes. Ces trames-là étaient
 *    jetées en silence — sans compteur, sans trace, sans effet sur la cadence
 *    annoncée. Un compteur non nul DISQUALIFIE la comparaison.
 */
void dn_stim_tear_misses(uint32_t *out_vsync, uint32_t *out_fbdone);

/* ── Stimulus d'écriture flash ───────────────────────────────────────────── */
esp_err_t dn_stim_flash_start(void);
void dn_stim_flash_stop(void);
/* Même convention que côté tearing : « en cours » = la TÂCHE VIT. */
bool dn_stim_flash_running(void);
/* Volume écrit et nombre de secteurs effacés depuis le démarrage du stimulus —
 * sans eux, le résultat n'est pas rejouable. */
void dn_stim_flash_stats(uint32_t *out_sectors, uint64_t *out_bytes,
                         double *out_bytes_per_s);

/*
 * Cause du DERNIER arrêt : ESP_OK si le stimulus s'est arrêté sur demande,
 * sinon l'erreur qui l'a tué (effacement ou écriture refusés, partition
 * absente).
 *
 * ⚠️ À AFFICHER DANS LA LIGNE D'ÉTAT : « arrêté » et « arrêté PARCE QUE la
 *    flash a refusé » ne se valent pas. Le second veut dire que tout ce qui a
 *    été observé depuis l'a été SANS écriture flash — c'est-à-dire sans le
 *    stimulus d'AC6, en croyant l'avoir. Le piège méthodologique que la story a
 *    déjà consigné une fois : conclure pendant qu'un stimulus supposé actif ne
 *    tournait pas.
 */
esp_err_t dn_stim_flash_error(void);

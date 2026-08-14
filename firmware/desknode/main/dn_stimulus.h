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
 */
typedef enum {
    DN_TEAR_SWEEP = 0,   /* barre verticale balayante, aucune synchronisation */
    DN_TEAR_FLIP,        /* bascule noir/blanc plein écran — littéral, mais son
                          * papillotement masque le déchirement */
    DN_TEAR_SYNC_VSYNC,  /* bascule après le VSYNC */
    DN_TEAR_SYNC_FBDONE, /* attente de on_frame_buf_complete — RETENU */
    DN_TEAR_SYNC_BOTH,   /* les deux — mesuré PIRE que FBDONE seul */
} dn_tear_mode_t;

esp_err_t dn_stim_tear_start(dn_tear_mode_t mode);
void dn_stim_tear_stop(void);
bool dn_stim_tear_running(void);
/* Cadence réellement atteinte (bascules par seconde) et durée moyenne d'une
 * trame complète, en microsecondes. */
void dn_stim_tear_stats(double *out_hz, int64_t *out_frame_us);

/* ── Stimulus d'écriture flash ───────────────────────────────────────────── */
esp_err_t dn_stim_flash_start(void);
void dn_stim_flash_stop(void);
bool dn_stim_flash_running(void);
/* Volume écrit et nombre de secteurs effacés depuis le démarrage du stimulus —
 * sans eux, le résultat n'est pas rejouable. */
void dn_stim_flash_stats(uint32_t *out_sectors, uint64_t *out_bytes,
                         double *out_bytes_per_s);

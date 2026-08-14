/*
 * DeskNode — l'instrumentation (AC4).
 *
 * ⚠️ AVERTISSEMENT QUI VAUT POUR TOUT CE FICHIER :
 *    un compteur vsync qui tourne NE PROUVE PAS que l'écran affiche quoi que
 *    ce soit. La DMA émet le signal même si la dalle n'a jamais été
 *    initialisée, même écran noir, même dalle débranchée. Le fps mesuré ici
 *    qualifie le PIPELINE, pas l'IMAGE. La preuve d'affichage, c'est l'œil de
 *    l'owner sur les mires (AC1/AC3). Ne jamais présenter un fps vert comme
 *    preuve d'image.
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "esp_err.h"
#include "esp_lcd_types.h"

/* Branche le callback on_vsync sur le panneau. */
esp_err_t dn_measure_attach(esp_lcd_panel_handle_t panel);

/* Compteur brut de vsync depuis le boot. Lu depuis une tâche, jamais écrit
 * ailleurs que dans l'ISR. */
uint32_t dn_measure_vsync_count(void);

/*
 * Bloque jusqu'au prochain VSYNC, ou jusqu'au délai. Renvoie true si un VSYNC
 * est bien arrivé.
 *
 * C'est la brique qui manque au double framebuffer pour supprimer le
 * déchirement : `esp_lcd_panel_draw_bitmap()` bascule le lien DMA TOUT DE
 * SUITE, pas à la prochaine trame. Basculer juste après un VSYNC, c'est le
 * faire pendant le retour vertical, quand la dalle n'affiche rien.
 */
bool dn_measure_wait_vsync(uint32_t timeout_ms);

/*
 * Bloque jusqu'à ce que le framebuffer qui vient d'être remplacé soit
 * RÉELLEMENT libéré par la DMA (`on_frame_buf_complete`).
 *
 * ⚠️ Ce n'est PAS le VSYNC, et la différence est exactement ce qui reste de
 *    déchirement quand on se synchronise sur le mauvais signal : le VSYNC dit
 *    « une trame commence », il ne dit pas « l'ancien tampon a fini d'être
 *    lu ». Entre les deux il y a la préextraction de la GDMA — d'où un
 *    escalier résiduel sur une partie de l'image.
 */
bool dn_measure_wait_frame_done(uint32_t timeout_ms);

/*
 * Échantillonne le fps sur `seconds` secondes (>= 10 exigé par AC4).
 * Renvoie le fps réel, et remplit `out_frames` / `out_elapsed_us` si fournis.
 */
double dn_measure_fps(int seconds, uint32_t *out_frames, int64_t *out_elapsed_us);

/* PSRAM libre, en octets. */
size_t dn_measure_psram_free(void);
size_t dn_measure_internal_free(void);

/* Mémorise le couple avant/après allocation des framebuffers, pour que la
 * commande `mem` puisse le redonner sans qu'on ait à relire le log de boot. */
void dn_measure_note_psram(size_t avant, size_t apres);
void dn_measure_get_psram_note(size_t *avant, size_t *apres);

/* Journalise le fps mesuré, le fps théorique, l'écart, et RÉÉCRIT le calcul —
 * la trace doit se suffire à elle-même (AC4). */
void dn_measure_report_fps(const char *etiquette, int seconds);

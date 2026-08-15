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
 * TÉMOIN ACTIF : le compteur avance-t-il encore ?
 *
 * Il existe parce qu'un défaut RÉEL et SILENCIEUX le guette : le driver RGB
 * ASSIGNE ses callbacks au lieu de les fusionner, donc n'importe quel appel
 * ultérieur à `esp_lcd_rgb_panel_register_event_callbacks()` — celui
 * d'esp_lvgl_port, par exemple — débranche ce compteur sans rien dire, en
 * rendant ESP_OK. Tout ce qui se mesure ensuite (fps, déchirement, cadence)
 * mesurerait alors du vide, à l'étiquette près.
 *
 * À appeler une fois au boot, APRÈS que toutes les couches se soient branchées.
 * `ms` doit couvrir plusieurs trames (26,7 ms l'une) : 100 ms en couvrent ~3.
 */
bool dn_measure_vsync_alive(uint32_t ms);

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
 * ── ABONNEMENT AU VSYNC (dn1-3) ──────────────────────────────────────────────
 *
 * POURQUOI CE MÉCANISME EXISTE, et ce qu'il empêche. `dn_measure_wait_vsync()`
 * ci-dessus s'appuie sur UN sémaphore binaire, donc sur UN consommateur. dn1-3
 * en ajoute deux qui attendent le même événement pour des raisons différentes :
 *   - le flush de LVGL, qui synchronise sa copie sur le retour vertical (AC4) ;
 *   - la tâche de recalage du double tampon, qui compte les vsyncs après une
 *     bascule (AC5).
 * Les faire partager le sémaphore historique donnerait un VOL D'ÉVÉNEMENT : le
 * premier réveillé consomme le jeton, l'autre repart pour une trame entière ou
 * expire. Et ce défaut-là serait SILENCIEUX — il ne se verrait que comme « la
 * synchro ne sert à rien », c'est-à-dire comme une conclusion de mesure fausse.
 *
 * Chaque abonné a donc son propre sémaphore, tous donnés par la même ISR.
 * Le jeton est valide pour toute la vie du firmware : personne ne se désabonne.
 */
#define DN_VSYNC_SUBS_MAX 3
typedef int dn_vsync_sub_t; /* < 0 = abonnement refusé (plus de slot) */

dn_vsync_sub_t dn_measure_vsync_subscribe(const char *nom);

/* Jette les événements déjà en attente. À appeler JUSTE AVANT d'attendre quand
 * on veut « le PROCHAIN vsync » (et pas celui qui vient de passer). */
void dn_measure_vsync_flush(dn_vsync_sub_t sub);

/* Attend un vsync sur cet abonnement. Ne vide RIEN de lui-même : c'est
 * l'appelant qui décide s'il veut le prochain (flush d'abord) ou simplement le
 * suivant non consommé (compter N vsyncs). Les deux besoins existent ici, et
 * c'est exactement l'erreur qu'avait faite `wait_frame_done` avant correction. */
bool dn_measure_vsync_wait(dn_vsync_sub_t sub, uint32_t timeout_ms);

/*
 * Rendez-vous avec `on_frame_buf_complete`, en DEUX temps qu'il faut appeler
 * DANS CET ORDRE :
 *
 *     dn_measure_arm_frame_done();      // vide le sémaphore
 *     dn_display_present();             // la bascule qui PROVOQUE l'événement
 *     dn_measure_wait_frame_done(100);  // n'attend plus que lui
 *
 * ⚠️ POURQUOI L'ARMEMENT EST UNE FONCTION SÉPARÉE, et pourquoi ce n'est pas du
 *    zèle. La version précédente vidait le sémaphore À L'INTÉRIEUR de
 *    l'attente, donc APRÈS la bascule. Or l'événement qu'on attend est
 *    exactement celui que la bascule vient de provoquer : s'il tombe dans la
 *    fenêtre entre le retour de `dn_display_present()` et le vidage, le vidage
 *    JETTE l'événement même qu'on attend. L'attente repart alors pour une trame
 *    entière — ou expire au bout des 100 ms. C'est-à-dire une latence
 *    supplémentaire NON DÉTERMINISTE, dans l'instrument qui a produit la
 *    colonne « cadence » du tableau AC5 (les lignes à 18,2 Hz et 12,5 Hz).
 *    ⇒ Les cadences déjà consignées ont été mesurées AVEC ce défaut : elles
 *      sont à REJOUER sur la carte.
 *
 *    Ce n'est PAS le cas de `dn_measure_wait_vsync()`, qui vide bien juste
 *    avant d'attendre : là on veut le PROCHAIN retour vertical, peu importe
 *    celui qui vient de passer. Les deux idiomes sont différents PARCE QUE les
 *    deux besoins le sont — ne pas « harmoniser ».
 *
 *    Course résiduelle assumée : un événement qui tomberait entre l'armement et
 *    la bascule serait pris pour celui de la bascule. Cette fenêtre-là fait
 *    quelques microsecondes, contre ~26,7 ms de période de trame — et contre
 *    toute la durée d'un `present()` dans l'ancienne version.
 *
 * ⚠️ CE QUE CET ÉVÉNEMENT SIGNIFIE RÉELLEMENT SUR CETTE PUCE. Ce bloc affirmait
 *    « le framebuffer remplacé a RÉELLEMENT fini d'être lu par la DMA », par
 *    opposition au VSYNC qui ne dirait que « une trame commence ». C'EST FAUX
 *    SUR L'ESP32-S3, et la vérification tient en deux lignes de l'IDF :
 *      - cette sémantique-là vient de l'événement de bascule de lien GDMA, qui
 *        n'est compilé que sous `SOC_AXI_GDMA_SUPPORTED`
 *        (components/esp_lcd/rgb/esp_lcd_panel_rgb.c:52-57) ;
 *      - l'ESP32-S3 ne définit que `SOC_AHB_GDMA_SUPPORTED`
 *        (components/soc/esp32s3/include/soc/soc_caps.h:33).
 *    Le callback nous arrive donc de `lcd_rgb_panel_eof_handler()`
 *    (esp_lcd_panel_rgb.c:961-967), sur le trans-EOF de la DMA — et Espressif y
 *    écrit lui-même, dans la branche exacte qui nous appelle : « Once the
 *    preload has already done, the buffer complete callback is not reliable. »
 *    (En mode bounce buffer — `bounce_px != 0`, pas notre défaut — le même
 *    callback arrive d'un troisième endroit encore, l'enroulement de la
 *    préextraction ; le raisonnement ci-dessous ne change pas.)
 *
 *    Autrement dit : ce rendez-vous est un AUTRE POINT DE PHASE dans la trame
 *    que le VSYNC, pas une garantie de liberté du tampon.
 *    ⇒ Le GAIN, lui, est réel et OBSERVÉ par l'owner (SYNC_FBDONE : escalier
 *      confiné aux ~15 % du haut, contre la moitié de la barre pour
 *      SYNC_VSYNC). C'est le MÉCANISME annoncé qui était faux, pas le
 *      résultat. On ne change donc PAS ce qu'on attend — on corrige
 *      l'explication. Un décalage de phase qui marche sans qu'on sache dire
 *      pourquoi reste un décalage de phase qui marche ; il ne devient pas une
 *      garantie pour autant, et rien ne doit être construit dessus.
 */
void dn_measure_arm_frame_done(void);
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

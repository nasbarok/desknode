/*
 * DeskNode — la couche UI : LVGL 9.5.0 posé sur le socle d'affichage de dn1-2.
 *
 * ── CE QUE CE MODULE N'EST PAS ───────────────────────────────────────────────
 * Ce n'est pas un remplacement de `dn_display`. Le bring-up (I²C -> TCA9554 ->
 * 3-wire SPI -> ST7701S -> RGB -> framebuffer PSRAM) reste entièrement à
 * `dn_display`, et LVGL reçoit les handles esp_lcd DÉJÀ créés. `dn_ui` n'alloue
 * ni framebuffer, ni panneau, ni bus.
 *
 * ── LES TROIS CONTRAINTES QUI EXPLIQUENT SA FORME ────────────────────────────
 *
 * 1. `avoid_tearing` d'esp_lvgl_port est INUTILISABLE ICI. Le portage appelle
 *    `esp_lcd_rgb_panel_get_frame_buffer(panel, 2, ...)` et exige donc num_fbs≥2
 *    (esp_lvgl_port_disp.c:367), alors que dn1-2 a ARBITRÉ num_fbs=1 — le double
 *    tampon n'est pas affichable sur cette puce sous RESTART_IN_VSYNC=y. On est
 *    donc en rendu PARTIEL sur un framebuffer unique.
 *
 * 2. EN RENDU PARTIEL, LE PORTAGE NE SYNCHRONISE RIEN — et c'est la découverte
 *    qui a fait écrire notre propre flush. Son `lvgl_port_flush_callback()`
 *    n'attend `trans_sem` que dans la branche `direct_mode || full_refresh`
 *    (esp_lvgl_port_disp.c:748-756) ; en mode partiel il tombe dans le `else`,
 *    qui appelle `draw_bitmap` et rend la main SANS AUCUNE ATTENTE (:758).
 *    Le callback `on_vsync` qu'il enregistre alimente donc un sémaphore que
 *    PERSONNE n'attend dans notre configuration.
 *    ⇒ `dn_ui_flush()` remplace le flush du portage (`lv_display_set_flush_cb`)
 *      et porte lui-même la synchronisation, son instrument, et son interrupteur.
 *
 * 3. LE COÛT D'UN FLUSH EST PROPORTIONNEL À L'AIRE — et cette ligne-ci a
 *    d'abord dit le CONTRAIRE, sur la foi du source, avant que la carte ne la
 *    corrige. On garde les deux versions, parce que l'erreur est instructive.
 *
 *    CE QUE DIT LE SOURCE : dans le chemin « recopier le draw buffer vers le
 *    framebuffer », le driver RGB fait `bytes_to_flush = v_res * bytes_per_line`
 *    puis `esp_cache_msync()` depuis le DÉBUT du framebuffer
 *    (esp_lcd_panel_rgb.c, branche `draw_buf_copy_to_fb`) : 614 400 octets de
 *    resynchronisation de cache à CHAQUE appel, que la zone sale fasse 8 000
 *    pixels ou 300 000. On en avait conclu un coût FIXE dominant par flush.
 *
 *    CE QUE DIT LA CARTE (2026-08-15, draw buffer en RAM interne, redessin plein
 *    écran de 323 092 px identique dans les trois branches) :
 *      32 lignes  -> 22 flushes, 22 794 us de copie cumulée
 *      64 lignes  -> 11 flushes, 23 989 us   (rejeu : 23 950 us, +0,16 %)
 *     128 lignes  ->  6 flushes, 24 892 us
 *    Le nombre de flushes varie d'un facteur 3,7 et le temps total ne bouge que
 *    de 9 % — dans le mauvais sens, en plus. Un coût fixe par flush ajusté sur
 *    ces points sort NÉGATIF : il est donc SOUS LE SEUIL DE DÉTECTION (< ~0,1 ms),
 *    pas dominant. Un `esp_cache_msync` en écriture parcourt des LIGNES DE CACHE,
 *    il ne recopie pas 614 400 octets ; c'est la lecture du source qui avait
 *    confondu une plage d'adresses avec un volume transféré.
 *    Débit de copie observé : ~27-29 Mo/s, RAM interne -> framebuffer PSRAM.
 *
 *    ⇒ Ce qui varie VRAIMENT avec la taille du draw buffer, c'est l'ATTENTE DE
 *      SYNCHRO : chaque flush attend sa trame, donc un plein écran coûte
 *      640/lignes retours verticaux (433 ms à 32 lignes, 176 ms à 64, 67 ms à
 *      128 — mesurés). C'est cette colonne-là qui arbitre, pas la copie.
 *    ⇒ Compter les flushes ET l'aire séparément reste juste : c'est ce qui a
 *      permis de départager les deux explications.
 *
 * ── DISCIPLINE D'APPEL ───────────────────────────────────────────────────────
 * Tout appel LVGL fait hors de la tâche du portage passe sous
 * `lvgl_port_lock()`/`unlock()`. Les fonctions publiques ci-dessous prennent le
 * verrou elles-mêmes : un appelant (console, app_main) n'a JAMAIS à le faire.
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "dn_bootcfg.h"
#include "esp_err.h"

/*
 * Mode de synchronisation du flush. C'est l'interrupteur d'AC4 : sans un mode
 * qui DÉCHIRE, aucune conclusion « ça ne déchire pas » n'est recevable.
 *
 *   OFF    : la copie part quand LVGL le décide, à n'importe quel moment du
 *            balayage. C'est le TÉMOIN POSITIF candidat.
 *   VSYNC  : la copie part juste après un retour vertical. Fenêtre de course
 *            réduite, PAS de garantie formelle — le balayage repart au même
 *            instant, et une zone sale proche du haut de l'écran est justement
 *            celle que le faisceau atteint en premier.
 *   FBDONE : la copie part sur `on_frame_buf_complete`, c'est-à-dire un AUTRE
 *            point de phase dans la trame (trans-EOF de la DMA sur cette puce,
 *            PAS une garantie de tampon libre — voir dn_measure.h). dn1-2 avait
 *            OBSERVÉ qu'il confinait l'artefact aux ~15 % du haut là où VSYNC en
 *            laissait la moitié ; ce constat est à REJOUER ici, l'instrument de
 *            l'époque ayant été invalidé.
 */
typedef enum {
    DN_FLUSH_SYNC_OFF = 0,
    DN_FLUSH_SYNC_VSYNC,
    DN_FLUSH_SYNC_FBDONE,
    DN_FLUSH_SYNC_COUNT,
} dn_flush_sync_t;

const char *dn_flush_sync_name(dn_flush_sync_t m);
bool dn_flush_sync_from_name(const char *nom, dn_flush_sync_t *out);

/*
 * ── PAR OÙ LA ZONE SALE ENTRE DANS LE FRAMEBUFFER ────────────────────────────
 *
 * Ce commutateur existe parce que l'œil de l'owner a démenti la première
 * version, le 2026-08-15 : en `BITMAP` + synchro `vsync`, chaque incrémentation
 * du label faisait « clignoter l'image, comme un déplacement rapide » — un
 * artefact PLEIN ÉCRAN, alors que la zone sale fait 5,17 % de la dalle.
 *
 * Ce que cette observation ÉLIMINE : ce n'est pas un problème de phase. La
 * synchro fonctionne (attente moyenne mesurée à 12,7 ms, soit la moitié de la
 * période de trame), et au moment de la copie le faisceau est vers la ligne 0
 * alors que le label est vers la ligne 300. Il n'y a pas de course entre les
 * deux. Le flush PERTURBE l'affichage par un autre chemin que le sien.
 *
 *   BITMAP : `esp_lcd_panel_draw_bitmap()`. Le driver recopie la zone puis
 *            resynchronise le cache avec `bytes_to_flush = v_res * bytes_per_line`
 *            depuis le DÉBUT du framebuffer — 614 400 octets de parcours de
 *            cache à chaque appel, pour 42 240 octets réellement salis. C'est le
 *            suspect : ce parcours martèle le bus PSRAM que la DMA de la dalle
 *            lit déjà à 23,0 Mo/s en continu, et §5.3 a établi qu'il n'existe
 *            AUCUNE parade logicielle à cette contention.
 *   DIRECT : on écrit nous-mêmes les lignes sales dans le framebuffer (qui EST
 *            le tampon visible à num_fbs=1) et on ne resynchronise QUE ces
 *            lignes-là. Même travail utile, ~15x moins de parcours de cache.
 *            ⚠️ N'a de sens qu'à num_fbs == 1 : au-delà, la bascule d'index
 *               appartient au driver et le contourner casserait le double
 *               tampon. dn_ui_set_path() refuse alors, plutôt que de dessiner
 *               dans le mauvais tampon en silence.
 *
 * Les deux chemins sont GARDÉS après l'arbitrage : l'un est la réfutation de
 * l'autre, et une élimination sans son témoin n'est pas une élimination.
 */
typedef enum {
    DN_FLUSH_PATH_BITMAP = 0,
    DN_FLUSH_PATH_DIRECT,
    DN_FLUSH_PATH_COUNT,
} dn_flush_path_t;

const char *dn_flush_path_name(dn_flush_path_t p);
bool dn_flush_path_from_name(const char *nom, dn_flush_path_t *out);
dn_flush_path_t dn_ui_get_path(void);
esp_err_t dn_ui_set_path(dn_flush_path_t p);

/*
 * Compteurs du flush — TOUS EN 32 BITS, délibérément.
 *
 * Le résiduel connu de dn1-2 est qu'un compteur 64 bits partagé entre deux cœurs
 * n'est pas atomique sur Xtensa (`volatile` ne découpe pas un int64), et
 * qu'AUCUNE décision ne doit reposer dessus. Ici l'écrivain est la tâche LVGL et
 * le lecteur est le REPL : deux cœurs possibles. Un uint32 aligné se lit d'un
 * seul accès, donc chaque champ pris isolément est juste.
 *
 * ⚠️ CE QUI RESTE VRAI MALGRÉ ÇA, et qu'il faut savoir en lisant : les champs
 *    ne sont pas cohérents ENTRE EUX (le relevé peut tomber entre l'incrément de
 *    `flushes` et celui de `px`). L'écart maximal est d'un flush. Aucune
 *    conclusion ne doit tenir à un flush près ; si c'était le cas, il faudrait
 *    un verrou, et on l'écrirait.
 *
 * ⚠️ ENROULEMENTS, écrits parce qu'un compteur qui reboucle en silence est un
 *    chiffre faux : `px` reboucle à 4 294 967 296 px, soit ~13 981 écrans
 *    pleins ; `copie_us` et `attente_us` rebouclent à ~4 295 s de temps CUMULÉ
 *    dans la fonction. La commande `flush reset` remet tout à zéro : toute
 *    mesure publiée part d'un reset.
 */
typedef struct {
    uint32_t flushes;     /* appels au flush */
    uint32_t cycles;      /* cycles de rafraîchissement (flush marqué « dernier ») */
    uint32_t px;          /* aire cumulée, en pixels */
    uint32_t copie_us;    /* temps cumulé DANS draw_bitmap */
    uint32_t attente_us;  /* temps cumulé à attendre la synchro */
    uint32_t max_px;      /* plus grande aire vue en un flush */
    uint32_t max_copie_us;/* plus longue copie vue */
    uint32_t timeouts;    /* synchros expirées (instrument suspect si non nul) */
} dn_flush_stats_t;

/*
 * Monte LVGL sur le socle. `asset_err` est le verdict de `dn_asset_init()` :
 * il est passé plutôt que redevine, pour que la scène « ASSET ABSENT » puisse
 * DIRE la raison exacte du refus au lieu d'un écran silencieux (AC1).
 *
 * ⚠️ À appeler AVANT `dn_measure_attach()`. Le portage enregistre son propre
 *    `on_vsync` et `esp_lcd_rgb_panel_register_event_callbacks()` ASSIGNE au lieu
 *    de fusionner : celui qui parle en dernier gagne, en silence. Le point
 *    d'enregistrement retenu est dn_measure — voir son commentaire.
 */
esp_err_t dn_ui_init(const dn_bootcfg_t *cfg, esp_err_t asset_err);

/* True dès que le premier cycle de rafraîchissement LVGL a atteint la dalle.
 * C'est la condition de la montée du rétroéclairage (discipline
 * « framebuffer rempli PUIS allumage », transposée à LVGL). */
bool dn_ui_first_frame_done(void);
bool dn_ui_wait_first_frame(uint32_t timeout_ms);

void dn_ui_get_stats(dn_flush_stats_t *out);
void dn_ui_reset_stats(void);

dn_flush_sync_t dn_ui_get_sync(void);
void dn_ui_set_sync(dn_flush_sync_t mode);

/* Invalide l'écran entier : le prochain cycle redessine tout. C'est la PREUVE
 * NÉGATIVE d'AC3 — ce que coûterait un mode plein écran. */
void dn_ui_force_full_redraw(void);

/* Le label vivant. Visible par défaut ; on peut l'éteindre pour isoler le coût
 * du stimulus adverse. */
void dn_ui_label_show(bool on);
bool dn_ui_label_shown(void);

/* Stimulus adverse d'AC4 : une barre verticale qui balaie l'écran. */
esp_err_t dn_ui_anim(bool on, int periode_ms);
bool dn_ui_anim_running(void);

/* Source du fond : mmap flash (défaut, 0 octet de PSRAM) ou copie PSRAM
 * (614 400 o). À trancher par la mesure — T3. */
esp_err_t dn_ui_bg_psram(bool on);
bool dn_ui_bg_is_psram(void);

/*
 * Suspend / reprend la tâche LVGL. Indispensable pour AC5 : la mesure du double
 * tampon passe par le chemin BRUT (`scene` -> dn_pattern_draw -> present), qui
 * écrit dans le même framebuffer que LVGL. Les laisser tourner ensemble
 * contaminerait les deux.
 */
esp_err_t dn_ui_pause(void);
esp_err_t dn_ui_resume(void);
bool dn_ui_active(void);

/* État du tas de LVGL. C'est le SEUL instrument honnête de son coût mémoire :
 * les 64 Ko de `LV_MEM_SIZE_KILOBYTES` sont statiques (.bss), donc invisibles à
 * un avant/après `heap_caps_get_free_size()`. */
void dn_ui_log_mem(void);

/* Ce que LVGL a réellement coûté en tas système, mesuré autour de dn_ui_init(). */
void dn_ui_get_cout(size_t *interne_avant, size_t *interne_apres,
                    size_t *psram_avant, size_t *psram_apres);

/* Taille et emplacement du draw buffer effectivement retenus.
 * ⚠️ Sans objet en mode DIRECT : les tampons de rendu sont alors les
 *    framebuffers eux-mêmes, et draw_lines n'est pas lu. */
int dn_ui_draw_lines(void);
bool dn_ui_draw_in_psram(void);

/*
 * True quand LVGL rend en DIRECT sur les deux framebuffers du driver (num_fbs>=2)
 * plutôt qu'en PARTIEL sur un draw buffer (num_fbs==1). Ce n'est pas un réglage
 * : c'est déduit de num_fbs au boot, et c'est la parade MESURÉE au clignotement
 * décrit en tête de dn_ui.c — à un framebuffer, le seul FAIT d'écrire dans le
 * tampon que la DMA balaie décroche l'image pour une trame.
 */
bool dn_ui_direct_mode(void);

/* Cœur sur lequel la tâche LVGL a été épinglée (-1 = pas d'affinité). */
int dn_ui_affinity(void);

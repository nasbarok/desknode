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
#include "dn_link.h"
/* dn3-2 : `dn_ui_heure_maj()` prend un `dn_rtc_heure_t`. La dépendance va dans
 * CE sens seulement — `dn_rtc.h` n'inclut PAS `dn_ui.h` (c'est le `.c` qui le
 * fait), donc pas de cycle. Passer les 7 champs en scalaires aurait donné une
 * signature à huit paramètres, où une inversion jour/mois serait silencieuse. */
#include "dn_rtc.h"
#include "dn_widget.h"
#include "esp_err.h"
#include "lvgl.h"

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
    uint32_t noops;       /* flushes NO-OP du mode direct : aire comptée, zéro µs
                           * de copie/attente. À SOUSTRAIRE du dénominateur des
                           * moyennes temporelles (revue : les inclure les diluait). */
} dn_flush_stats_t;

/*
 * ── LES DEUX VUES DE dn1-4, ET CE QU'ELLES NE SONT PAS ───────────────────────
 *
 * Elles sont FACTICES et JETABLES. Les cases sont des zones géométriques nues
 * (conteneur + titre + valeur statique) : le `SystemMetricWidget` naît en dn3-1,
 * la vraie grille en dn3-2, les vraies données en dn2/dn4-1. Ce que dn1-4 livre
 * ici, c'est la GÉOMÉTRIE TACTILE et le MODÈLE DE NAVIGATION — pas un écran de
 * produit.
 *
 * ⚠️ Aucune dimension n'est figée par la planification (seulement 480x640
 *    portrait) : celles de dn_ui.c sont DÉRIVÉES et consignées comme
 *    PROVISOIRES. dn3-2 fera foi.
 */
typedef enum {
    DN_VUE_DASHBOARD = 0,
    DN_VUE_DETAIL,
    DN_VUE_COUNT,
} dn_ui_vue_t;

const char *dn_ui_vue_name(dn_ui_vue_t v);

/* Les six métriques du brief. Ordre de la grille 2x3 :
 *   CPU | GPU / RAM | RÉSEAU / TEMP. | HUMIDITÉ */
#define DN_UI_METRIQUES 6
const char *dn_ui_metrique_nom(int idx);

/*
 * ── LE MODÈLE DE NAVIGATION — C'EST LE LIVRABLE QUE dn3 HÉRITE ───────────────
 *
 * Les DEUX sont implémentés, et ils le restent après l'arbitrage : l'un est la
 * réfutation de l'autre, et une élimination sans son témoin n'est pas une
 * élimination (même discipline que `flush path bitmap|direct`).
 *
 *   REBUILD : le pattern historique de ce fichier — `lv_obj_clean()` sur l'écran
 *             actif puis reconstruction complète. Un seul écran vit à la fois,
 *             donc zéro mémoire dormante ; en échange, chaque transition
 *             reconstruit tout l'arbre (et re-décode le fond).
 *   SCREENS : deux racines `lv_obj_create(NULL)` créées UNE FOIS, permutées par
 *             `lv_screen_load()`. Le détail n'est pas reconstruit : ses labels
 *             sont réécrits. Transition plus courte, mémoire des deux arbres
 *             tenue en permanence.
 *
 * Ce que la mesure d'AC4 doit départager : latence de transition, tas LVGL, et
 * stabilité sur N allers-retours.
 */
typedef enum {
    DN_NAV_REBUILD = 0,
    DN_NAV_SCREENS,
    DN_NAV_COUNT,
} dn_nav_model_t;

const char *dn_nav_model_name(dn_nav_model_t m);
bool dn_nav_model_from_name(const char *nom, dn_nav_model_t *out);
dn_nav_model_t dn_ui_get_nav_model(void);
/* Bascule à chaud. Repose la vue courante à zéro (dashboard) : les deux modèles
 * ne tiennent pas leur état au même endroit, et prétendre conserver la vue
 * ferait mentir l'un des deux. */
esp_err_t dn_ui_set_nav_model(dn_nav_model_t m);

dn_ui_vue_t dn_ui_vue(void);
int dn_ui_metrique(void);
/* Nombre de transitions jouées depuis le boot (aller ET retour). */
uint32_t dn_ui_nav_count(void);

/*
 * ── QUELLE ZONE A REÇU LE DERNIER TAP (preuve d'AC3) ─────────────────────────
 *   0..5 = la case de la métrique · DN_UI_ZONE_MENU · DN_UI_ZONE_RETOUR
 *   DN_UI_ZONE_AUCUNE = aucun tap n'a encore atteint une zone.
 *
 * ⚠️ C'est un ENREGISTREMENT, pas un log. Écrire sur la console depuis un
 *    callback LVGL bloquerait la tâche de rendu sur le lien USB — c'est-à-dire
 *    que l'instrument de la preuve fausserait la latence qu'AC5 mesure au même
 *    moment. La console lit cette valeur quand ELLE le décide.
 */
#define DN_UI_ZONE_AUCUNE (-1)
#define DN_UI_ZONE_MENU (-2)
#define DN_UI_ZONE_RETOUR (-3)
int dn_ui_dernier_tap(void);
uint32_t dn_ui_taps(void);
const char *dn_ui_zone_nom(int zone);
/* Taps sur le bandeau MENU.
 * 🔴 STRUCTURELLEMENT ZÉRO DEPUIS dn3-2, ET C'EST LE RÉSULTAT DE W3 — pas une
 *    panne. Le bandeau n'a plus de callback, donc `dn_widget_zone_creer` ne lui
 *    pose plus LV_OBJ_FLAG_CLICKABLE : ce n'est plus une zone, et aucun site
 *    n'incrémente ce compteur. Il reste exposé parce qu'un `touch trace` doit
 *    pouvoir montrer le ZÉRO plutôt que de ne rien dire.
 * ⛔ NE PAS le lire comme « le no-op est un CHOIX » : le no-op — un bouton qui
 *    prend le tap et ne fait rien — est précisément la forme que W3 a
 *    SUPPRIMÉE. La preuve de la zone morte est faite par `touch trace`
 *    (16 appuis, 0 tap, AC5/AC6), pas par ce compteur. */
uint32_t dn_ui_menu_taps(void);
/* Taps REFUSÉS par LVGL (lv_async_call sur file pleine ou tas saturé). Un tap
 * refusé n'est pas compté dans dn_ui_taps() : sans ce tri, `touch trace`
 * affichait « TAP sur CPU » pour un tap qui n'avait ouvert aucun écran, et la
 * preuve d'AC3 validait une zone tactile morte. Un compteur non nul ici est un
 * SYMPTÔME, pas une statistique. */
uint32_t dn_ui_async_refus(void);

/* Remet à zéro taps / menu_taps / nav_count / refus / dernière zone.
 * Appelée par `touch reset`, qui ne remettait à zéro que les compteurs de
 * dn_touch : après une bascule de modèle, `nav` publiait les compteurs du
 * modèle précédent sous la bannière du nouveau. */
void dn_ui_reset_compteurs(void);

/* 🔴 dn4-13 / AC5.3 — COMBIEN DE FOIS ON A DEMANDÉ DE REPARAMÉTRER LA COURBE, ET
 * COMBIEN DE FOIS ÇA A PRODUIT UN REDESSIN. Leur RAPPORT est le chiffre d'AC5 :
 * l'invalidation du cadre (460 x 108 px) tournait INCONDITIONNELLEMENT, jusqu'à
 * 5 fois par seconde, y compris sur une série 100 % trous. ⛔ « C'est mieux »
 * sans ces deux nombres ne vaut rien. Remis à zéro par `dn_ui_reset_compteurs()`. */
/* dn4-13 / AC5.3 · REVUE 2026-08-25 — lit les deux compteurs SOUS VERROU.
 * Rend **false** si le verrou n'a pas été pris ⇒ « pas mesuré », ⛔ pas « zéro » :
 * l'appelant NE DOIT PAS publier de ratio dans ce cas. */
bool dn_ui_courbe_compteurs(uint32_t *appels, uint32_t *redessins);

/* Octets UTILISÉS du tas LVGL — le SEUL instrument qui voit une fuite d'objets
 * LVGL. La RAM interne et la PSRAM n'en disent rien : ce tas est un pool
 * STATIQUE en .bss (LV_MEM_ADR=0). 0 = verrou non pris, pas « rien d'utilisé ». */
size_t dn_ui_lvgl_used(void);

/* Navigation depuis la CONSOLE (prennent le verrou LVGL elles-mêmes).
 * `idx` dans 0..DN_UI_METRIQUES-1. Le chemin du DOIGT passe par les mêmes
 * fonctions internes : un tap et un `nav open 2` produisent la même transition,
 * sinon la latence mesurée au clavier ne dirait rien de celle du doigt.
 *
 * ⚠️ ESP_ERR_INVALID_STATE = la vue demandée était DÉJÀ l'active : rien n'a
 *    changé, aucun chronomètre n'a été armé. Ce n'est pas une panne, mais
 *    l'appelant NE DOIT PAS l'annoncer comme une transition — `nav ab` comptait
 *    une itération de plus que la réalité quand la série démarrait depuis un
 *    détail, et ce nombre sert de dénominateur à la moyenne publiée par AC5. */
esp_err_t dn_ui_nav_open(int idx);
esp_err_t dn_ui_nav_back(void);

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

/* L'afficheur LVGL, pour y brancher l'indev tactile. NULL avant dn_ui_init().
 * Exposé plutôt que de laisser dn_ui appeler dn_touch lui-même : l'ordre de
 * branchement des couches se lit alors dans app_main, là où le trap n°1 (« les
 * callbacks s'ASSIGNENT ») se surveille déjà. */
lv_display_t *dn_ui_display(void);

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
 * NÉGATIVE d'AC3 — ce que coûterait un mode plein écran.
 * Renvoie false si le verrou LVGL n'a pas pu être pris : AUCUN redessin n'a
 * alors été demandé, et l'appelant ne doit pas publier de compteurs. */
bool dn_ui_force_full_redraw(void);

/* Le label vivant. ⚠️ MASQUÉ par défaut DEPUIS dn1-4 (l'en-tête annonçait encore
 * « visible par défaut », que le .c dément : le drapeau a perdu son
 * initialiseur `= true` dans le même commit). Il est centré, géométrie gelée
 * pour rester comparable à dn1-3, et recouvrirait les cases RAM/RÉSEAU du
 * dashboard. `ui label on` le rallume pour rejouer le régime produit de dn1-3 à
 * l'identique — c'est ce que fait AC6 pour ré-observer l'artefact §10.5, qui a
 * besoin d'un redessin périodique. Un `dn_ui_label_shown() == false` au
 * démarrage est donc NORMAL, pas une panne. */
void dn_ui_label_show(bool on);
bool dn_ui_label_shown(void);

/* ── La case CPU vit (dn2-2) ──────────────────────────────────────────────────
 * Pose la valeur de la case CPU du dashboard (haut-gauche de la grille 2x3).
 * `dixiemes` : 0..1000 = dixièmes de % (« 153 » -> « 15,3 % »).
 * `valide == false` (liaison morte ou jamais vue) : la case affiche « -- »
 * grisé — un chiffre périmé qui reste affiché est un mensonge d'interface (AC7).
 * Prend le verrou LVGL ELLE-MÊME (règle du dépôt : l'appelant JAMAIS) ; renvoie
 * false si le verrou n'a pas pu être pris — RIEN n'a alors été modifié et
 * l'appelant doit retenter. Sûre quel que soit l'écran chargé : en SCREENS le
 * label du dashboard est mis à jour même sous la vue détail ; en REBUILD le
 * texte est conservé et posé à la prochaine construction.
 *
 * `label_pose` (optionnel, peut être NULL) rend true UNIQUEMENT si le texte a
 * atteint un label VIVANT sur une UI qui tourne. ⚠️ Il est distinct de la valeur
 * de retour, et c'est un correctif de revue (2026-08-16) : la valeur de retour
 * pilote le RETRY de l'appelant (false = verrou occupé, réessayer), `label_pose`
 * pilote la MESURE (n'a-t-on chronométré qu'un geste réellement accompli ?).
 * Les confondre donnait soit une latence mesurée sur des poussées sans label
 * (REBUILD vue détail ⇒ pointeur NULL, ou LVGL arrêté par `ui off`/`scene`/`tear`),
 * soit une boucle qui retente sans fin et sur-compte les reprises. */
bool dn_ui_cpu_maj(int dixiemes, bool valide, bool *label_pose);

/*
 * ── dn4-1 : L'ENTRÉE UNIQUE DES CINQ MÉTRIQUES PC ────────────────────────────
 *
 * ⛔ IL N'Y A PAS CINQ `dn_ui_xxx_maj()` COPIÉES LES UNES DES AUTRES, ET C'EST
 *    DÉLIBÉRÉ. Ce seraient cinq endroits où le contrat de verrou, le format des
 *    dixièmes et la règle « une valeur ABSENTE ne porte jamais son unité »
 *    peuvent diverger. Ce fichier a déjà payé exactement ça (trois divergences
 *    .h/code, un A/B mesuré deux fois sur la même branche).
 *
 * ⇒ UN SEUL CHEMIN : verrou pris ici, formatage centralisé, `case_poser()` en
 *   sortie, `label_pose` rendu à part de la valeur de retour. La correspondance
 *   métrique → case et la forme de la ligne secondaire vivent dans UNE TABLE de
 *   `dn_ui.c`, pas dans des `if (m == …)`.
 *
 * ⚠️ `dn_ui_cpu_maj` SURVIT comme point d'entrée mono-métrique historique de
 *    dn2-2, et elle délègue au même chemin.
 * 🔴 ⛔ MAIS ELLE N'A **AUCUN APPELANT** DANS LE FIRMWARE (grep exhaustif, revue
 *    du 2026-08-18), ET LA RAISON QUI ÉTAIT ÉCRITE ICI ÉTAIT FAUSSE : ce
 *    paragraphe disait « conservé pour que le témoin de non-régression v1 reste
 *    exécutable ». Le témoin v1 d'AC2 passe par `dn_link_ingest_ligne` ->
 *    `pousser_metrique` -> `dn_ui_pc_maj`. Il ne l'a jamais traversée.
 *    ⇒ Ce qui n'est jamais appelé ne prouve rien. Si un appelant revient, il
 *    doit savoir que la vue fabriquée porte `age_us = -1` (« pas d'horodatage ») :
 *    c'était `0`, ce qui injectait des latences à 0 µs dans la statistique.
 *
 * `vue` porte l'état, les N grandeurs et leurs drapeaux `connue[]` (W10) : une grandeur
 * absente laisse la case RÉELLE et n'écrit « -- » que sur SA ligne.
 *
 * ── 🔴 dn4-9 : CHANGEMENT DE CONTRAT, ET IL S'ÉCRIT ICI ──────────────────────
 *
 * AVANT : cette fonction ne formatait que les `desc_n(idx)` premières grandeurs
 *   — le compte de la **CASE**. ⇒ pour `CPU` (case à 3, fil à 4), la °C du fil
 *   n'était **JAMAIS écrite** dans `s_wetat[CPU].txt[3]`.
 * APRÈS : elle formate **toutes les grandeurs que le descripteur PEUPLE**,
 *   bornées par ce que la trame porte. L'état d'une case n'est plus « ce que la
 *   case dessine » mais **« ce que la métrique sait »** — c'est la condition
 *   pour que la CASE et le DÉTAIL en montrent des sous-ensembles différents.
 *
 * ⚠️ CE QUE ÇA COÛTE, ET C'EST BORNÉ : au plus `DN_WIDGET_GRANDEURS_MAX`
 *    formatages par trame au lieu de `n_grandeurs`, soit +1 pour `CPU` et
 *    `GPU`, +3 pour `DISQUE`, 0 pour les trois autres. Mesuré en AC9.
 * ⛔ LA BORNE N'EST PAS `DN_WIDGET_GRANDEURS_MAX` : formater au-delà des
 *    entrées peuplées ferait retomber le format au DIXIÈME par repli silencieux
 *    (`prec` non renseignée) — une décimale que la source ne porte pas. `RAM` le
 *    prouve : deux valeurs sur le fil, UNE seule entrée peuplée.
 */
bool dn_ui_pc_maj(dn_link_metrique_t m, const dn_link_vue_t *vue,
                  bool *label_pose);

/* L'index de case d'une métrique PC — RELU de la table, pour la console.
 * Rend -1 si la métrique n'a pas de case. */
int dn_ui_case_de_metrique(dn_link_metrique_t m);

/* Le nombre de cases mockées — COMPTÉ dans `k_mock[]`, pour que la console
 * n'ait pas à le réciter. ⛔ Une constante là où une table existe est le défaut
 * que ce fichier corrige trois fois par ailleurs. */
int dn_ui_mocks_actifs(void);

/*
 * ── AC5 : CE QUE LA CASE A RÉELLEMENT CONSTRUIT, RELU DES POINTEURS ──────────
 * ⚠️ RELU, jamais récité du descripteur : c'est tout l'objet du correctif W5.
 *    Un descripteur qui DEMANDE une jauge et une secondaire peut n'obtenir que
 *    la jauge (la géométrie ne permet pas les deux à n = 2) — et c'est
 *    précisément ce qu'il faut pouvoir CONSTATER sans lire le source.
 * 🔴 `idx == DN_UI_METRIQUES` DÉSIGNE LE WIDGET DE DÉMO (`widget demo on`), et
 *    c'est OBLIGATOIRE pour que cet instrument serve à quelque chose (correctif
 *    de revue 2026-08-18). Il est le SEUL objet du firmware à demander
 *    `n_grandeurs = 2` ET `indicateur = true`, donc le seul à déclencher
 *    l'abandon de la secondaire. Les six cases réelles ne peuvent PAS le
 *    produire — la colonne « secondaire » était constante par construction, et
 *    l'instrument ne pouvait pas voir le cas qu'il prétendait prouver.
 * Rend false si `idx` est hors bornes (0..DN_UI_METRIQUES inclus) ou si l'objet
 * n'est pas dessiné.
 */
bool dn_ui_widget_pointeurs(int idx, int *n_grandeurs, bool *jauge, bool *sec);

/*
 * ── dn4-4 / AC9 : LE RECTANGLE RÉEL DE LA JAUGE, RELU DE L'OBJET LVGL ────────
 *
 * 🔴 POURQUOI CETTE FONCTION EXISTE. `dn4-2` a publié la bande tactile de la
 *    jauge `RAM` à `y = 337..347` / `x = 22..223` — un chiffre CALCULÉ depuis la
 *    formule (`ui_grille_y() + MARGE + ligne x (case_h + GAP)`, puis
 *    `y_bas + 6` côté `dn_widget.c`). La campagne de visée du 2026-08-20, cible
 *    RENDUE VISIBLE (`widget piste 0xFF2020`), a produit **9 taps à
 *    `y = 350..371`** : ⛔ AUCUN dans la bande publiée, tous 13 à 24 px DESSOUS.
 *    ⇒ Deux lectures s'opposaient, et **aucune n'était relue de l'objet**.
 *
 * ⛔ CE QU'ON NE FAIT PAS : corriger la bande au jugé. Un décalage « corrigé »
 *    de 13 px sans savoir LEQUEL des deux nombres est faux déplacerait
 *    simplement l'erreur.
 * ✅ CE QU'ON FAIT : on demande à LVGL **où il a VRAIMENT posé la barre**, en
 *    coordonnées ÉCRAN, exactement comme `dn_ui_detail_label()` relit le texte du
 *    label au lieu de le recomposer. C'est le seul chiffre qui tranche.
 *
 * ⚠️ `lv_obj_get_coords()` rend des bornes **INCLUSIVES** : la hauteur est
 *    `y2 - y1 + 1`. Le dépôt a déjà payé ce `+1` une fois (voir `dn_ui_flush`).
 * ⚠️ La géométrie n'est exploitable qu'APRÈS une passe de layout. `*resolue`
 *    dit si elle l'est ; l'appelant refuse de conclure sinon — même contrat que
 *    `dn_ui_detail_label()`.
 *
 * Rend `false` si l'index est hors bornes, si la case n'est pas construite, si
 * elle n'a PAS de jauge (`*existe = false`), ou si le verrou LVGL n'est pas pris.
 */
bool dn_ui_widget_jauge_rect(int idx, int *x, int *y, int *w, int *h,
                             bool *existe, bool *resolue);

/*
 * dn4-4 / AC4 — LE RECTANGLE RÉEL DE LA COURBE, dans son cadre de 108 px.
 * ⛔ MÊME DOCTRINE QUE `dn_ui_widget_jauge_rect()` : la hauteur dont la courbe
 *    DISPOSE ne se calcule pas de tête, elle se RELIT. `dn4-9` a payé exactement
 *    ça sur le bloc de valeurs — son arithmétique avait oublié le `y = 14` du
 *    label, et c'est la carte qui l'a corrigée une fois l'instrument capable de
 *    voir la hauteur.
 * `*existe` = la courbe est construite ; `*resolue` = la géométrie l'est.
 */
bool dn_ui_detail_courbe_rect(int *x, int *y, int *w, int *h, int *w_cadre,
                              int *h_cadre, bool *existe, bool *resolue);

/* dn4-4 — LES PLAGES Y RÉELLEMENT APPLIQUÉES AUX DEUX AXES, et la couleur de
 * chaque série. ⛔ Relues des objets, pas recalculées : c'est le seul moyen de
 * savoir OÙ une série est dessinée dans les 92 px, et donc si deux séries se
 * SUPERPOSENT. `*n_series` vaut 0, 1 ou 2. */
/* 🔴 dn4-13 / AC4.3 — `*pose0` / `*pose1` disent si l'axe a ÉTÉ POSÉ pour la
 * page courante. ⛔ Sans eux, « pas posé » sortait en `0 .. 0`, indiscernable
 * d'une plage réelle nulle — et pire : les drapeaux survivaient à une transition
 * de page, donc `widget courbe` publiait `0 .. 1000` (la plage bornée du CPU)
 * sous le titre `RÉSEAU`. Chemin NOMINAL, pas exotique. */
bool dn_ui_detail_courbe_axes(int *y0_min, int *y0_max, int *y1_min, int *y1_max,
                              uint32_t *coul0, uint32_t *coul1, int *n_series,
                              bool *pose0, bool *pose1);

/*
 * dn4-4 / AC4.3 — LE TÉMOIN NÉGATIF de la garde de hauteur du détail.
 * ⚠️ Au pire cas LIVRÉ le bloc tient EXACTEMENT (`14 + 140 = 154 ≤ 154`) : il
 *    n'existe donc AUCUN stimulus naturel qui fasse crier cette garde. Sans un
 *    tel stimulus, « la garde existe » n'est pas « la garde marche ».
 * `h = 0` rend le panneau à sa valeur de produit (154) ; 40..200 sinon.
 * ⛔ Hors plage ⇒ `ESP_ERR_INVALID_ARG`, ⛔ jamais un écrêtage silencieux.
 * ⚠️ RECONSTRUIT la scène.
 */
/* dn4-4 / AC7 — LA BORNE HAUTE DE « L'OPTION N°2 » DU LEDGER (*ne pas invalider
 * le fond à la transition*), non essayée depuis `dn3-2`. `off` RETIRE le fond :
 * c'est le MEILLEUR CAS que l'option pourrait atteindre. ⛔ Pas un mode de
 * production. ⚠️ RECONSTRUIT la scène.
 * 🔴 dn4-13 / AC9 — `off` LAISSE L'ÉCRAN **VRAIMENT NOIR** (décision owner n°2).
 *    Il tombait dans la branche `ASSET ABSENT` et peignait un fond ROUGE avec
 *    deux labels ⇒ les **139,5 ms** publiées comme borne haute mesuraient un
 *    remplissage plat **+ deux labels**, ⛔ pas « le fond et rien d'autre ».
 *    Le chiffre se RE-TIRE avec cet instrument-ci (AC11.1). */
esp_err_t dn_ui_set_fond(bool on);
bool dn_ui_fond(void);

/* 🔴 dn4-13 / AC6.5 — BORNÉ À **167** (= 262 − 95), ⛔ plus 200. Au-delà, le bloc
 * de valeurs CHEVAUCHE le cadre de courbe — et la garde de hauteur NE LE VOIT
 * PAS (elle compare le label à SON panneau, pas le panneau à son voisin) : elle
 * concluait « ✅ silence LÉGITIME » sur un écran cassé. ⚠️ Remet AUSSI les
 * compteurs de la garde à zéro : c'est ce qui rend le témoin négatif REJOUABLE. */
esp_err_t dn_ui_set_detail_panh(int h);
int dn_ui_detail_panh(void);

/* dn4-4 / AC4.3 — CE QUE LA GARDE DE HAUTEUR A VU AU DERNIER PASSAGE.
 * ⛔ Une garde qui se tait peut se taire pour TROIS raisons : elle n'est pas
 *    atteinte, `geom_resolue` la coupe, ou sa condition est fausse. Sans ces
 *    compteurs on les confond — et ce dépôt a déjà paye ça (« un test peut être
 *    VERT sans ATTEINDRE la garde qu'il prétend couvrir »). */
/* 🔴 dn4-13 / AC1.2 — rend `false` si le verrou LVGL n'a pas été pris (sorties
 * remises à zéro). Les six champs sont écrits par la tâche LVGL : sans verrou le
 * tuple pouvait MÉLANGER DEUX PASSAGES, et le verdict de `widget courbe` compare
 * justement trois de ces six nombres entre eux. */
/* 🔴 dn4-13 / AC6.1 — `*cri_dernier` = la garde a-t-elle crié AU DERNIER
 * PASSAGE. ⛔ `*cris` est CUMULATIF et ne peut pas trancher : après un retour au
 * produit, il faisait annoncer « ✅ elle a CRIÉ » sur une garde MUETTE, et il
 * rendait la branche « la garde est CASSÉE » INJOIGNABLE dès le premier cri.
 * Les compteurs sont remis à zéro par `dn_ui_set_detail_panh()` — un témoin se
 * remet à zéro, ou il n'est pas un témoin. */
bool dn_ui_garde_hauteur(uint32_t *passages, uint32_t *cris, int *hp, int *hl,
                         int *yl, bool *resolue, bool *cri_dernier);

/* ── LA CASE « AMBIANCE » : DEUX GRANDEURS DANS UNE CASE (D6, dn3-1) ──────────
 * Jusqu'à dn2-1 c'étaient DEUX cases (TEMP. idx 4, HUMIDITÉ idx 5). D6 les
 * fusionne en UNE case bi-grandeurs (idx 5) et libère idx 4 pour VENTILOS.
 * Mêmes règles que dn_ui_cpu_maj, à trois différences près qui comptent :
 *  · elle pose les DEUX grandeurs sous UN SEUL verrou — sinon la case pourrait
 *    afficher une température neuve à côté d'une humidité périmée le temps
 *    d'une trame. L'exigence n'a pas disparu avec la fusion : elle s'est
 *    RENFORCÉE (les deux valeurs sont maintenant dans le même rectangle, où une
 *    incohérence serait encore plus difficile à lire) ;
 *  · `valide == false` grise les DEUX ensemble : un capteur muet l'est pour ses
 *    deux grandeurs, il n'y a pas de demi-silence. ⚠️ C'est désormais
 *    STRUCTUREL : le régime est porté par la CASE, pas par la grandeur — on ne
 *    PEUT plus en griser une moitié, même par erreur ;
 *  · la température accepte le NÉGATIF (bornes -40,0 à +85,0 °C, la plage du
 *    BME680 — les MÊMES qu'en amont, garde-fou redondant assumé) : « 0 <= x »
 *    aurait mangé les valeurs sous zéro. ⚠️ Et le signe se pose explicitement,
 *    il ne se déduit PAS du quotient : la division entière tronque vers zéro,
 *    donc -5 dixièmes donnait « 0,5 °C » (CR 2026-08-17).
 * ⚠️ L'UNITÉ N'EST PLUS DANS LE TEXTE : elle vit dans le descripteur du widget
 *    (`dn_widget_desc_t.grandeurs[].unite`) et c'est le modèle qui la
 *    concatène — ce qui permet la règle « une valeur ABSENTE ne porte jamais son
 *    unité » (« -- % » suggérerait qu'on sait de quoi on parle). */
bool dn_ui_ambiance_maj(int temp_dixiemes, int hum_dixiemes, bool valide,
                        bool *label_pose);

/* ── La barre heure/date (dn3-2, AC3/AC4) ─────────────────────────────────────
 *
 * Poussée par la tâche `dn_rtc` à 2 Hz. Mêmes règles que `dn_ui_cpu_maj` :
 * le verrou LVGL est pris ICI, `false` = verrou non pris ⇒ RIEN n'a bougé.
 *
 * 🔴 `fiable` EST LE VERDICT D'HONNÊTETÉ, PAS UN CODE D'ERREUR. À `false`, la
 *    barre affiche « --:-- » gris et « HEURE NON POSÉE » — jamais l'heure
 *    contenue dans `h`, même si elle a l'air normale. Une barre qui affiche
 *    « 03:47 » après une coupure est PIRE qu'une barre qui se tait, et le
 *    PCF85063 a un bit dédié pour le dire (OS, Seconds bit 7).
 *    ⇒ `h` peut être NULL quand `fiable` est faux.
 *
 * ⚠️ L'invalidation n'a lieu QUE si le texte affiché (ou la fiabilité) change.
 * 🔴 CE QU'ELLE COÛTE EST MESURÉ (§16.5, dn3-2) : **6 334 px par mise à jour**,
 *    soit 18 % d'une case. ⛔ NE PAS déduire son coût de son aire — la prémisse
 *    « 480 x 70 = 33 600 px, donc 96 % d'une case, donc une 7e case vivante »
 *    est FAUSSE D'UN FACTEUR 5,3 : LVGL n'invalide que la zone des LABELS, pas
 *    le rectangle de la barre. Elle a survécu à toute la rédaction de dn3-2 et
 *    a été récitée jusque dans la sortie console de l'A/B qui la réfutait.
 */
bool dn_ui_heure_maj(const dn_rtc_heure_t *h, bool fiable, bool *label_pose);

/*
 * La CADENCE de la barre — l'A/B de W2/AC4, commutable à chaud, sans reflasher.
 * 🔴 DÉFAUT = `false`, c'est-à-dire HH:MM SANS LES SECONDES, parce que la
 *    maquette normative du brief (addendum §1) écrit « 21:46 » et n'affiche PAS
 *    les secondes.
 * ⚠️ CETTE VALEUR PAR DÉFAUT EST RÉPÉTÉE DANS `dn_ui.c`, `rtc`, le README et
 *    hardware/ — elle doit être la MÊME partout. En dn3-1, le `.h` du groupage
 *    annonçait `false` là où le code valait `true`, et QUI REJOUAIT L'A/B
 *    MESURAIT DEUX FOIS LA MÊME BRANCHE.
 * ⚠️ Le régime n'est qu'un FORMAT : c'est la détection de changement de texte
 *    qui déclenche l'invalidation. En HH:MM, le texte ne bouge qu'au changement
 *    de minute ⇒ le calage sur la minute est structurel.
 */
void dn_ui_barre_secondes_set(bool on);
bool dn_ui_barre_secondes(void);

/* ── W8 / AC9 : LE REPEINT EN BANDES ──────────────────────────────────────────
 * Élargit chaque aire invalidée à la pleine largeur de la dalle.
 * ✅ Mécanisme LU dans `lv_refr.c:321-328` : LVGL dédoublonne par
 *    `lv_area_is_in(nouvelle, sauvegardée)` — il JETTE une aire CONTENUE dans
 *    une autre, il ne FUSIONNE jamais. Deux cases d'une même ligne élargies à
 *    0..479 deviennent identiques ⇒ la seconde est jetée.
 * 🔴 Mais le draw buffer fait `480 x draw_lines` PIXELS : à 480 de large il ne
 *    tient que `draw_lines` lignes (128 par défaut) contre 156 pour une case.
 *    Une bande devrait donc être rendue en DEUX passes ⇒ même compte de
 *    flushes, +6,7 % de pixels. ⚠️ PRÉDICTION, pas fait : c'est la mesure qui
 *    tranche, et `set lines 160` permet d'essayer la config où elle tomberait.
 * ⚠️ INERTE par défaut. INSTRUMENT, pas un réglage produit. */
void dn_ui_bandes_set(bool on);
bool dn_ui_bandes(void);

/* Ce que la barre affiche EN CE MOMENT, relu de l'état réel — pour que `rtc`
 * n'ait pas à reformater de son côté (deux formateurs = deux vérités). */
/* 🔴 COPIE SOUS VERROU, PAS DE POINTEUR NU (revue 2026-08-18). Les anciens
 * `dn_ui_barre_heure_txt()` / `_date_txt()` rendaient les buffers statiques tels
 * quels, et la console les passait à `printf` depuis SA tâche pendant que la
 * tâche RTC les réécrivait à 2 Hz — lecture déchirée possible aux transitions de
 * longueur. Rend `false` si le verrou n'a pas été pris (les buffers sont alors
 * vidés, jamais laissés indéterminés). */
bool dn_ui_barre_txt(char *heure, size_t n_heure, char *date, size_t n_date);
/* ⚠️ Tient compte de `s_active` : après `ui off` / `scene` / `tear`, les labels
 * existent mais rien n'atteint la dalle. Annoncer « dessinée » mentirait.
 * 🔴 dn4-13 / AC1 — TROIS RÉPONSES, PAS DEUX. Le retour dit « J'AI PU MESURER »
 *    (verrou LVGL pris) ; la réponse elle-même sort par `*dessinee`. Rendre
 *    `false` sur un verrou non pris aurait publié « PAS dessinée », un verdict
 *    fabriqué — la famille de défauts que cette story solde. */
bool dn_ui_barre_dessinee(bool *dessinee);

/* ── Le modèle de widget (dn3-1, généralisé en dn3-2) ─────────────────────────
 * Descripteur d'une case, ou NULL si la case est NUE.
 * 🔴 DEPUIS dn3-2, LES SIX CASES PORTENT LE MODÈLE — `k_widget[]` est vrai
 *    partout. GPU/RAM/RÉSEAU ne sont plus les nues : elles sont SIMULÉE, avec
 *    badge et couleur ambre. Le témoin négatif d'AC8 vit désormais dans
 *    l'override `s_nue_force[]`, posé À CHAUD par `widget nue <idx> on|off` —
 *    c'est ce qui permet de mesurer une case nue et six widgets DANS LE MÊME
 *    FIRMWARE. Ce commentaire décrivait encore le monde de dn3-1 (revue
 *    2026-08-18) : c'est la divergence .h/code que dn3-1 avait déjà payée une
 *    fois, quand un A/B mesurait deux fois la même branche. */
const dn_widget_desc_t *dn_ui_desc(int idx);

/* Le descripteur BRUT, ⛔ SANS l'override W11 — pour les INSTRUMENTS qui publient
 * ce que le descripteur DEMANDE (table de géométrie de la console), jamais pour
 * décider d'un rendu. Voir `dn_ui_desc()`, qui fait foi côté dessin.
 * (Correctif de revue 2026-08-19 : la colonne « demandé » d'une case NUE annonçait
 *  « n=0 » et perdait « jauge demandee ».) */
const dn_widget_desc_t *dn_ui_desc_brut(int idx);

/* Le descripteur du widget de DÉMO (`widget demo on`) — le SEUL du firmware à
 * demander deux grandeurs ET une jauge, donc le seul à armer l'abandon de la
 * ligne secondaire. La table de géométrie d'AC5 en a besoin pour confronter
 * demandé/obtenu ; sans lui, la colonne « secondaire » ne peut valoir que OUI.
 * ⚠️ RENDU PAR VALEUR (revue 2026-08-19) : la version précédente rendait
 *    l'adresse d'un statique de fonction réécrit à chaque appel, donc un pointeur
 *    dont la stabilité promise par `const dn_widget_desc_t *` n'existait pas.
 * Rend `false` si `out` est NULL. */
bool dn_ui_demo_desc(dn_widget_desc_t *out);

/* La case `idx` est-elle rendue en WIDGET (true) ou NUE (false, override W11) ?
 * ⛔ Une case nue n'a qu'un `valeur[0]` : sans cette lecture, la table de
 * géométrie affiche « n_gr = 1 (n=2) » et ça se lit comme un abandon. */
bool dn_ui_case_est_widget(int idx);
bool dn_ui_est_widget(int idx);

/* Le RÉGIME de la valeur d'une case, RELU de l'état réel. C'est ce que la
 * console imprime : jamais une constante, jamais une déduction. */
dn_val_regime_t dn_ui_regime(int idx);
/* 🔴 dn4-9 — CE QUE `grandeur` SIGNIFIE EST **TRANCHÉ ET ÉCRIT** : c'est un
 *    **INDEX DE GRANDEUR** (l'entrée de `k_desc[].grandeurs[]` et le slot
 *    d'état, qui sont le même nombre), ⛔ **PAS un rang d'affichage**.
 *    Les deux coïncidaient avant dn4-9 ; depuis, `CPU` dessine [0, 1, 3] et son
 *    rang 2 est la grandeur 3. ⇒ Un appelant qui veut « la 3ᵉ LIGNE de la case »
 *    doit d'abord traduire par `dn_ui_case_indices()`. Vaut aussi pour
 *    `dn_ui_case_unite()` et `dn_ui_case_prefixe()`. */
const char *dn_ui_valeur_txt(int idx, int grandeur);
/* La case est-elle DESSINÉE en ce moment ? (false en REBUILD vue détail : le
 * dashboard n'existe pas, l'état est conservé mais rien n'atteint la dalle.) */
bool dn_ui_case_dessinee(int idx);

/* ── Le mock (AC3) — GÉNÉRALISÉ À QUATRE CASES EN dn3-2 (W5) ──────────────────
 * Il bat sur le tick 1 Hz de LVGL (pas de tâche : produire un nombre ne dort
 * pas). Sa FORME est annoncée et relue, pas récitée : rampe triangulaire
 * min -> max -> min, période fixe et PAIRE, dérivée du TEMPS ABSOLU.
 * `dn_ui_mock_set(false)` le coupe : les cases redeviennent ABSENTES (« -- »),
 * ce qui est le témoin que le mock EST leur seule source.
 * 🔴 GPU, RAM, RÉSEAU et VENTILOS ont un mock ; CPU et AMBIANCE n'en ont PAS —
 *    elles ont des sources RÉELLES (`dn_link`, `dn_capteurs`). C'est la
 *    conséquence écrite de D6 : PC éteint, UNE SEULE case sur six est vivante,
 *    et ça doit SE VOIR. */
/* A/B d'AC8 : bascule le groupage d'invalidation. C'est `dn_ui` qui prend le
 * verrou, jamais l'appelant — `dn_widget_*` EXIGE qu'il soit déjà pris. */
esp_err_t dn_ui_set_groupage(bool on);
/* dn4-10 : le TROISIÈME mode d'invalidation — une seule zone, bornée aux
 * valeurs. ⛔ Exclusif des deux autres, garanti par le setter. */
esp_err_t dn_ui_set_groupe_union(void);

/* Dimensions d'une case du dashboard, en px. Une zone GROUPÉE vaut exactement
 * `w * h` pixels sales. Relu, pas récité. */
void dn_ui_case_dim(int *w, int *h);

/* Rend `ESP_ERR_TIMEOUT` si le verrou LVGL n'a pas été pris — RIEN n'a alors
 * changé, et l'appelant ne doit PAS annoncer la bascule (revue 2026-08-18 : la
 * fonction rendait `void` et la console mentait sur son propre effet). */
esp_err_t dn_ui_mock_set(bool on);
bool dn_ui_mock_on(void);
/* Rend `false` si la case `idx` n'a PAS de mock — ⚠️ signature changée en
 * dn3-2 : elle rendait `void` et décrivait uniquement VENTILOS. Avec quatre
 * mocks de formes différentes, une console qui aurait gardé l'ancienne aurait
 * décrit trois cases par les chiffres d'une quatrième. */
bool dn_ui_mock_forme(int idx, int *min, int *max, int *periode_s);

/* ── AC8 : l'injecteur de poussée ─────────────────────────────────────────────
 * Pose UNE mise à jour synthétique (régime SIMULÉE) sur la case `idx`, et rend
 * le numéro de séquence. C'est ce qui permet d'isoler le coût de redessin d'UNE
 * case — y compris une case NUE, qu'aucune source n'alimente et dont le coût
 * serait sinon indémontrable.
 * ⛔ UNE poussée par appel : N poussées dans un même appel tomberaient dans le
 *    MÊME cycle LVGL et seraient fusionnées — on mesurerait 1 flush pour N mises
 *    à jour, et on conclurait que grouper est gratuit. C'est l'appelant PC qui
 *    les espace. */
uint32_t dn_ui_pousser(int idx);

/* ── AC8 : LA RAFALE — le cas « toutes dans le MÊME cycle », PROVOQUÉ ─────────
 *
 * 🔴 ELLE CONTREDIT DÉLIBÉRÉMENT L'INTERDIT CI-DESSUS, et c'est pour ça qu'elle
 *    porte un autre nom. L'extrapolation d'AC8 porte sur « six widgets qui se
 *    mettent à jour dans le MÊME cycle » (6 x 35 100 = 210 600 px, 69 % d'un
 *    plein écran) — un cas qui NE SE PRODUIT PAS naturellement, puisque les six
 *    sources ne sont pas synchronisées (liaison ~1 s, capteur 5 s, mocks
 *    14/20/26/34 s, barre à la minute) et que le seul appelant est le REPL, qui
 *    attend l'invite entre deux commandes.
 *    Sans elle, ce cas devrait être DÉCLARÉ NON MESURÉ. Avec elle, il se
 *    mesure — mais il se publie comme un INSTRUMENT, jamais comme un régime.
 *
 * Rend le nombre de cases poussées, et RIEN D'AUTRE.
 *
 * 🔴 IL N'Y A PLUS DE TÉMOIN DE FUSION — DÉCISION OWNER DU 2026-08-19. Ce contrat
 *    a énoncé TROIS sémantiques successives (« cycles intercalés », puis « 0 =
 *    succès », puis « 1 = succès ») pour un chiffre qui, à chaque fois, ne pouvait
 *    rendre QUE sa valeur de succès : sous le verrou le compteur ne bougeait pas ;
 *    après la relâche, la boucle d'attente sortait au PREMIER cycle observé, donc
 *    le delta valait 1 quoi qu'il se soit passé pendant la rafale.
 * ⇒ LA FUSION SE PROUVE PAR `flush`, ET PAR LUI SEUL — « 6 flushes / 1 cycle /
 *   210 600 px » dans la même passe, mesure indépendante de cette fonction. C'est
 *   elle qui porte le chiffre d'AC7 régime (c), et c'est elle qu'on publie.
 * ⛔ NE PAS RÉINTRODUIRE `dn_ui_rafale_cycles()` sans démontrer PAR LA MESURE que
 *   le nouveau témoin peut rendre autre chose que sa valeur de succès. Trois
 *   tours d'un instrument aveugle suffisent.
 * ✅ Conséquence : la rafale NE DORT PLUS (`DN_UI_RAFALE_ATTENTE_MS` supprimé), ce
 *   qui rétablit l'invariant « aucune sous-commande de `widget` ne DORT » — il
 *   était faux depuis que l'attente de 500 ms bloquait le REPL, donc le transport.
 */
uint32_t dn_ui_rafale(void);
uint32_t dn_ui_rafale_n(void);

/* ── W11 : le TÉMOIN NÉGATIF d'AC8, commutable à chaud ────────────────────────
 *
 * Jusqu'à dn3-1, GPU/RAM/RÉSEAU étaient NUES et servaient de référence à tous
 * les chiffres d'AC8. Les six devenant des widgets (dn3-2), cette référence
 * quitterait le firmware — et AC8 se retrouverait à comparer un firmware à un
 * AUTRE firmware, exactement ce que dn3-1 s'est interdit en mesurant « dans le
 * même firmware ».
 * ⚠️ RECONSTRUIT LA SCÈNE (307-322 ms, verrou tenu) : la forme d'une case est
 *    décidée à la CONSTRUCTION, pas à la mise à jour. C'est cher, et c'est
 *    assumé pour un instrument qu'on actionne ENTRE deux relevés.
 * ⚠️ `ESP_ERR_INVALID_STATE` si la case n'a jamais eu le modèle : acquitter
 *    donnerait à croire qu'on a fait quelque chose.
 */
esp_err_t dn_ui_nue_set(int idx, bool nue);
bool dn_ui_nue(int idx);

/* ── `widget oublier <idx>` — rendre une case à son RÉGIME NATUREL ────────────
 *
 * 🔴 Entrée de ledger `deferred-work.md:1019-1023`, dont la condition est
 *    DÉCLENCHÉE par dn3-2 : « une case NUE n'a aucune source, donc elle reste
 *    SIMULÉE jusqu'au reboot […] SI dn3-2 en fait un usage courant, ajouter un
 *    `widget oublier <idx>` serait moins piégeux que "rebooter avant tout
 *    constat owner" ». AC8 fait de `widget pousser` l'instrument central.
 *    ⇒ Sans elle, un constat owner lancé après une campagne verrait des badges
 *      « SIMULÉ » résiduels et pourrait les lire comme une RÉGRESSION.
 * Pose ABSENTE et lève le drapeau de poussée : le mock, s'il est armé,
 * reprendra la case au prochain tick ; une source réelle la repeindra quand
 * elle parlera ; une case sans source restera « -- », et c'est la vérité.
 */
esp_err_t dn_ui_oublier(int idx);

/* ── AC9 : l'opacité du voile plein écran ─────────────────────────────────────
 * Reconstruit la scène (le voile est créé au dessin). 0..255. */
esp_err_t dn_ui_set_voile_opa(uint8_t opa);
uint8_t dn_ui_voile_opa(void);

/* ── L'A/B D'ICÔNE, SUR N'IMPORTE QUELLE CASE (W4 dn3-1, généralisé dn4-1) ────
 * Des glyphes embarqués ensemble et commutables à chaud, pour qu'un choix
 * d'icône soit un CONSTAT OWNER sur la dalle et non une intuition — un A/B qui
 * exigerait un reflash par candidat coûterait une observation par candidat.
 * Reconstruit la scène.
 * ⚠️ dn4-1 : la CASE est devenue un paramètre. `dn_ui_set_icone_vent(n)` écrivait
 *    `s_icone_alt[DN_UI_CASE_VENT]` en dur — après le renommage D8, l'A/B aurait
 *    continué de viser l'ancienne case ventilateur SANS RIEN DIRE. C'était l'une
 *    des trois tables « câblées par index » que dn4-1 aurait fait mentir.
 * `dn_ui_icone_alt(idx)` rend -1 si l'icône active n'est aucun des candidats
 * (cas nominal : la case porte celle de son descripteur). */
int dn_ui_icones_alt_n(void);
const char *dn_ui_icone_alt_nom(int n);
int dn_ui_icone_alt(int idx);
esp_err_t dn_ui_set_icone_alt(int idx, int n);

/* ── La PISTE de la jauge (constat owner 2026-08-18) ──────────────────────────
 * Passe par dn_widget (une seule définition) et reconstruit la scène. */
esp_err_t dn_ui_set_piste(uint32_t rgb);

/* ── AC9 : l'opacité des CASES ────────────────────────────────────────────────
 * Passe par dn_widget (une seule définition de l'aplat) et reconstruit la scène. */
esp_err_t dn_ui_set_case_opa(uint8_t opa);

/*
 * ════════════════════════════════════════════════════════════════════════════
 * dn4-6 / AC4 — LES TROIS VOIES, COMMUTABLES DANS UN SEUL FIRMWARE
 * ════════════════════════════════════════════════════════════════════════════
 * ⚠️ LES TROIS RECONSTRUISENT LA SCÈNE. `build_scene()` coûte 307-322 ms verrou
 *    tenu — et sur la branche A LE REPL EST LE TRANSPORT PC. La console DOIT
 *    l'annoncer AVANT, ⛔ pas le laisser découvrir par une trame perdue.
 * ⚠️ Verrou non pris ⇒ `ESP_ERR_TIMEOUT` et RIEN n'a bougé. ⛔ Ne jamais
 *    annoncer une bascule qui n'a pas eu lieu.
 */

/* Les deux bandes (voie (a) : `menu_h = 0` ; D12 : 60 / 51).
 * Bornes RELUES du contenu, ⛔ pas rondes : barre ≥ 53 (heure `dn_font_28` à
 * y = 18), MENU ≥ 49 (`dn_font_28` à y = 14) ou 0 = pas de bandeau. */
esp_err_t dn_ui_set_bandes(int barre_h, int menu_h);
/* dn4-4 / AC9 — le rectangle COMPLET d'une case (origine + dimensions), rendu
 * par LA fabrique que `build_dashboard()` utilise elle-même. ⛔ Toute
 * coordonnée tactile publiée doit venir d'ici, jamais d'une expression recopiée :
 * c'est ainsi que la bande de la jauge `RAM` a pu etre publiee sans etre
 * confrontable. Hors bornes ⇒ `x = y = -1`, `w = h = 0`. */
void dn_ui_case_rect(int idx, int *x, int *y, int *w, int *h);

void dn_ui_geom_bandes(int *barre_h, int *menu_h, int *grille_h, int *case_h);
void dn_ui_geom_bandes_defaut(int *barre_h, int *menu_h);

/* La géométrie interne de la case (voie (b) : la police ; voie (c) : `dispo`).
 * ⚠️ Enveloppe de `dn_widget_set_geom()` : elle prend le verrou et RECONSTRUIT.
 *    Appeler `dn_widget_set_geom()` nu changerait le réglage sans redessiner —
 *    « un réglage qui ne fait rien sans l'annoncer » est la classe de défaut
 *    que `dma` (inerte dans ce build) a coûtée au dépôt.
 * 🔴 AMENDE LE 2026-08-24 : « (inerte dans ce build) » est PERIME — `dma` est
 *    OPERANTE depuis `4734d07`. La lecon citee reste exacte. */
esp_err_t dn_ui_set_widget_geom(const dn_widget_geom_t *g);

/* Les DEUX ensemble, en UN seul `build_scene()`. 🔴 Enchaîner les deux setters
 * produisait une reconstruction INTERMÉDIAIRE — nouvelle hauteur de case,
 * ANCIENNE géométrie interne — dont les débordements étaient comptés et
 * attribués à la voie. L'instrument accusait la voie du défaut de son propre
 * chemin d'application, et la voie (a) ressortait à « 1 débordement » alors
 * qu'elle tient. Les compteurs sont remis à zéro SOUS LE VERROU juste avant
 * l'unique reconstruction. */
esp_err_t dn_ui_set_voie(int barre_h, int menu_h, const dn_widget_geom_t *g);

/* Le nombre de grandeurs d'UNE case, réglable à chaud (0 = rendre la case à son
 * descripteur). 🔴 C'est le SEUL moyen de comparer le REPLI pré-autorisé
 * (« `GPU` à trois ») aux trois voies SUR LA MÊME DALLE et DANS LE MÊME
 * FIRMWARE — le reflasher pour le montrer coûterait une observation owner.
 * ⚠️ RECONSTRUIT LA SCÈNE. */
int dn_ui_case_grandeurs(int idx);

/* ── dn4-9 : LE SECOND COMPTE, ET LES INDICES ────────────────────────────────
 * `dn_ui_detail_grandeurs()` : ce que le DÉTAIL montre. ⛔ Pas d'override à
 *   chaud (voir AC6 : `widget grandeurs` ne déplace plus que la CASE).
 * `dn_ui_case_indices()` : la liste ORDONNÉE des index de grandeur que la case
 *   DESSINE, override compris. `out` doit faire au moins
 *   `DN_WIDGET_GRANDEURS_MAX`. Rend le compte, 0 si l'appel est invalide.
 *   ⚠️ Les indices du DÉTAIL, eux, sont `0..dn_ui_detail_grandeurs()-1` DANS
 *      L'ORDRE — il n'y a pas de sélection côté détail, et le motif est dans
 *      `dn_widget.h`. ⛔ Ne pas inventer un accesseur qui rendrait une plage.
 * `dn_ui_case_prefixe()` : le préfixe d'écran d'une grandeur (« c.max »,
 *   « ventirad »…), ou NULL. 🔴 Il existe pour que `pc` puisse NOMMER quel
 *   ventilateur est muet : la console imprime `dn_link_metrique_unite()`,
 *   c'est-à-dire l'unité du FIL — et `disk` y porte TROIS « tr/min »
 *   byte-identiques. ⛔ JAMAIS en modifiant `k_metriques[].unite`, qui casserait
 *   les témoins de non-régression v1 et v3. */
int dn_ui_detail_grandeurs(int idx);
int dn_ui_case_indices(int idx, uint8_t *out, int out_n);
const char *dn_ui_case_prefixe(int idx, int grandeur);

/* L'unité RÉELLEMENT affichée, échelle haute comprise. ⛔ La console ne doit
 * PAS relire `desc->grandeurs[g].unite` : elle imprimait « Mb/s » sur une
 * valeur convertie en Gb/s, fausse d'un facteur mille, dans l'instrument
 * qui sert précisément à vérifier. */
const char *dn_ui_case_unite(int idx, int grandeur);

/*
 * ── dn4-9 : LA TAILLE DU TEXTE DU DÉTAIL, **UNE SEULE DÉFINITION** ───────────
 *
 * 🔴 L'INSTRUMENT ÉTAIT PLUS PETIT QUE CE QU'IL DEVAIT RELIRE, ET IL AURAIT
 *    MENTI EN SILENCE — relevé au cadrage de dn4-9, ⛔ pas à l'exécution :
 *      · producteur (`detail_reparametrer`) : `4 * (TXT_MAX + 24) + 8` = 168 o,
 *        avec un `ESP_LOGE` si ça tronque ;
 *      · instrument (`cmd_widget`, `widget detail`) : `TXT_MAX * 4 + 64` = 128 o,
 *        **AUCUNE garde**, et `dn_ui_detail_label()` faisait
 *        `snprintf(txt, txt_n, "%s", src)` sans tester le retour.
 *    ⇒ 128 < 168. À quatre grandeurs AVEC préfixes, le pire cas dépasse : le
 *      seul instrument capable de PROUVER qu'une ligne tient aurait tronqué le
 *      texte qu'il prétend relire, pendant que le produit, lui, va bien.
 *    🎯 « Un instrument faux accuse le sujet sain. »
 * ⇒ UNE constante, les DEUX côtés la prennent, et la troncature est AUDIBLE.
 * ⚠️ Le `28` = icône + espace + préfixe + espace + unité + espace, au pire cas.
 *    Un préfixe plus long que « ventirad » (8) + « tr/min » (6) + 3 espaces +
 *    une icône (3 o UTF-8) demande de le relever ICI, ⛔ pas de rogner le texte.
 * 🔴 PORTÉ DE 24 À 28 EN 2e REVUE (2026-08-24), AVEC LE MOTIF : la vue DÉTAIL
 *    dessine désormais l'ICÔNE (décision owner). Un glyphe `LV_SYMBOL_*` pèse
 *    **3 octets UTF-8** et son espace 1 : +4 par grandeur, +16 au total.
 *    ⛔ Ne PAS laisser la troncature « se voir au log » ici : le log existe pour
 *      l'imprévu, ⛔ pas pour un dépassement qu'on sait poser à l'avance.
 */
#define DN_UI_DETAIL_TXT_MAX (4 * (DN_WIDGET_TXT_MAX + 28) + 8)

/* Ce que la GRANDE VALEUR du détail a réellement posé : son texte, sa largeur,
 * celle de son parent, son x. ⛔ Relu des objets LVGL, jamais recomposé — c'est
 * la seule façon de distinguer « le texte est trop large » de « le panneau est
 * trop étroit » de « le texte n'est pas celui qu'on croit ».
 * Rend `false` si le détail n'est pas affiché.
 *
 * 🔴 LE TEXTE EST **COPIÉ** DANS `txt` SOUS LE VERROU LVGL (revue 2026-08-19) —
 *    ⛔ plus un `const char *` vers le tampon interne du label rendu APRÈS le
 *    déverrouillage : `detail_reparametrer()` `lv_realloc` ce tampon 5 fois par
 *    seconde en régime, et l'appelant l'imprimait hors verrou.
 * ⚠️ `resolue` dit si `w_parent`/`x` sont exploitables. Quand la scène est en
 *    cours de construction, le parent est NULL et l'ancienne API rendait
 *    `w_parent = -1` ⇒ l'appelant calculait `utile = -1 - 2*x` et criait « LE
 *    TEXTE SORT DU PANNEAU ». ⛔ Ne rien conclure de la largeur si `resolue`
 *    est `false` — c'est la même garde que dans `detail_reparametrer`.
 * 🔴 dn4-9 : `txt_n` DOIT valoir `DN_UI_DETAIL_TXT_MAX`. Si la copie tronque,
 *    la fonction `ESP_LOGE` en NOMMANT les deux tailles et rend `false` — ⛔ un
 *    instrument tronqué ne rend plus « true » avec un texte amputé. */
/* 🔴 dn4-9 (2026-08-22) : `h` ET `h_parent` SONT AJOUTÉS, ET C'EST UN CORRECTIF
 *    D'INSTRUMENT, ⛔ pas un confort. Cet accesseur ne rendait QUE la largeur —
 *    il ne pouvait donc PAS voir le défaut qu'il prétend exclure dès que le
 *    détail passe à QUATRE lignes : le label est posé à `y = 14` dans son
 *    panneau, et 4 x 35 = 140 px de texte dans 140 px de panneau DÉBORDENT de
 *    14 px, clippés EN SILENCE par LVGL. C'est la règle n°5 du dépôt, et elle
 *    a déjà été payée six fois. */
bool dn_ui_detail_label(char *txt, size_t txt_n, int *w, int *w_parent, int *x,
                        int *h, int *h_parent, int *y, bool *resolue);
esp_err_t dn_ui_set_case_grandeurs(int idx, int n);
esp_err_t dn_ui_bandes_valider(int barre_h, int menu_h);
esp_err_t dn_ui_geom_valider(const dn_widget_geom_t *g);

/* Le `n` de la démo — le SEUL moyen d'atteindre les deux témoins d'AC2 (abandon
 * de jauge à n ≥ 3, clamp à n > `DN_WIDGET_GRANDEURS_MAX`). Défaut 2, borne 6. */
int dn_ui_demo_n(void);
esp_err_t dn_ui_set_demo_n(int n);

/* ── AC1 : la preuve d'unicité, rendue falsifiable ────────────────────────────
 * Construit une 7e métrique FICTIVE depuis un descripteur, SANS aucune ligne de
 * code de dessin neuve, et la retire. C'est la promesse du brief (« ajouter une
 * métrique future ne redessine pas l'UI ») transformée en expérience. */
esp_err_t dn_ui_demo_set(bool on);
bool dn_ui_demo_on(void);

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

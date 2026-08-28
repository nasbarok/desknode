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
 *    🔴 AMENDÉ LE 2026-08-22 (dn4-10), ⛔ PAS EFFACÉ. La parenthèse ci-dessus
 *    dit « `bounce_px != 0`, PAS NOTRE DÉFAUT ». Elle était juste quand elle a
 *    été écrite (`bounce_px` valait 0) ; elle est FAUSSE depuis le 2026-08-16 :
 *    `bounce_px` vaut 7 680 et le mode bounce buffer est EXACTEMENT notre cas.
 *    ⇒ Ce n'est donc PAS la branche `else` de `lcd_rgb_panel_eof_handler()`
 *      qui nous appelle (celle qui tire à CHAQUE trans-EOF), mais
 *      `lcd_rgb_panel_fill_bounce_buffer()` à l'ENROULEMENT de
 *      `bounce_pos_px` (esp_lcd_panel_rgb.c:925-932, IDF v5.5.5).
 *    ⇒ Conséquence MESURABLE, et c'est ce qui fonde le compteur de dn4-10 :
 *      l'événement tombe **UNE FOIS PAR TRAME**, pas 40 fois. Un `wraps` qui
 *      ne suivrait pas `trames` 1 pour 1 est donc un DÉFAUT, pas du bruit.
 *    ⚠️ Et la citation d'Espressif « the buffer complete callback is not
 *      reliable » appartient à la branche `else`, celle qui ne nous concerne
 *      PLUS. On ne l'efface pas — elle redeviendrait vraie à `bounce_px = 0`.
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

/*
 * ═══════════════════════════════════════════════════════════════════════════
 * dn4-10 — LE COMPTEUR DE GLISSEMENT DE TRAME (la « famine DMA » du bounce)
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * 🔴 POURQUOI IL EXISTE. Le défaut « l'image glisse d'un coup puis se recale »
 *    en est à sa QUATRIÈME occurrence (2026-08-16 x2, 2026-08-19, 2026-08-22) et
 *    AUCUN instrument de ce firmware ne sait le voir : `fps` rend 37,40 Hz
 *    PENDANT que l'image saute, `flush` mesure le chemin de flush et pas le
 *    panneau, `dn_recal` est inerte sous CONFIG_LCD_RGB_RESTART_IN_VSYNC=y.
 *    🔴 AMENDE LE 2026-08-24 : cette derniere clause est PERIMEE — le symbole
 *    vaut `n` depuis `4734d07` et `dn_recal` n'est plus inerte. ⛔ Le constat
 *    d'ensemble, lui, TIENT : aucun instrument du firmware ne voit le
 *    glissement, et c'est toujours la raison d'etre de ce bloc.
 *    dn4-6 a donc payé sa bissection en ONZE constats owner à l'œil, et la
 *    séance dn4-9 en a payé CINQ de plus. Ce bloc existe pour arrêter de payer.
 *
 * 🔴 CE QUE LE DRIVER DIT DU MÉCANISME — LU, ⛔ PAS SUPPOSÉ.
 *    esp_lcd_panel_rgb.c:1142-1148 (IDF v5.5.5), au-dessus de
 *    `lcd_rgb_panel_try_restart_transmission()` :
 *      « reset the GDMA channel every VBlank to stop permanent desyncs […]
 *        if this interrupt is LATE ENOUGH, the display will SHIFT as the LCD
 *        controller already read out the first data bytes, and resetting DMA
 *        will re-send those. […] It's also not super-likely as this interrupt
 *        has the entirety of the VBlank time to reset DMA. »
 *    ⇒ Le glissement N'EST PAS un octet manquant : c'est L'ISR DE VSYNC_END QUI
 *      ARRIVE TROP TARD. Elle a un budget, et ce budget se CALCULE.
 *
 * ⛔ CE QUI A ÉTÉ ÉCARTÉ, ET POURQUOI — pour qu'on ne le re-propose pas.
 *    - `on_bounce_empty` : la story dn4-10 le désignait comme LE crochet. Il ne
 *      peut PAS servir ici. `lcd_rgb_panel_fill_bounce_buffer()` ne l'appelle
 *      que sous `if (unlikely(panel->num_fbs == 0))` (esp_lcd_panel_rgb.c:902).
 *      Nous sommes à `num_fbs = 1` ⇒ il ne sera JAMAIS appelé. Et l'enregistrer
 *      à `num_fbs = 0` reviendrait à REMPLACER la copie du driver par la nôtre,
 *      pas à l'observer.
 *    - L'interruption d'underrun MATÉRIELLE (`LCD_LL_EVENT_UNDERRUN`) :
 *      définie pour l'ESP32-P4 SEULEMENT (hal/esp32p4/include/hal/lcd_ll.h:31).
 *      L'ESP32-S3 ne l'a pas. Voie fermée, mesurée, ⛔ à ne pas rouvrir.
 *    - `bb_eof_count < expect_eof_count`, la détection de famine du driver
 *      lui-même : elle est compilée dans le `#else` de
 *      CONFIG_LCD_RGB_RESTART_IN_VSYNC (esp_lcd_panel_rgb.c:1153-1166). Nous
 *      sommes à `=y` ⇒ ce test N'EXISTE PAS dans notre binaire, et le compteur
 *      qu'il consulte n'est jamais remis à zéro. Rien à lire de ce côté.
 *      🔴 AMENDÉ LE 2026-08-27 : « NOUS SOMMES À `=y` » EST PÉRIMÉ — le symbole
 *      vaut `n` depuis `4734d07`, donc cette détection EST dans le binaire et
 *      le driver relance la DMA lui-même sur famine avérée
 *      (esp_lcd_panel_rgb.c:1153-1163). ⛔ Ce n'est PAS une voie à instrumenter
 *      pour autant : elle utilise le MÊME bit que `dn_recal`, et le trou réel
 *      (« la relance ÉCHOUE parfois, et ça DURE ») demande une mesure de DURÉE
 *      qui est le sujet de `dn4-12`, ⛔ pas de celle-ci.
 *
 * 🎯 CE QUE CE COMPTEUR MESURE, ET POURQUOI `fps` NE POUVAIT PAS LE VOIR.
 *    `fps` compte 561 vsync sur 15 s et DIVISE : la moyenne efface la gigue.
 *    Or toute l'information est DANS la gigue. Ici on garde la DISTRIBUTION des
 *    intervalles vsync→vsync, mesurés à l'entrée de l'ISR :
 *      - période théorique : htotal x vtotal / pclk = 620 x 690 / 16 MHz
 *      - budget de l'ISR   : le BACK PORCH vertical qui suit VSYNC_END, soit
 *                            htotal x vbp / pclk = 620 x 20 / 16 MHz = 775 us.
 *                            ⚠️ Le commentaire d'Espressif dit « the entirety
 *                            of the VBlank » (1 937 us) ; c'est OPTIMISTE :
 *                            VSYNC_END tombe à la FIN de l'impulsion, donc il
 *                            ne reste que le back porch avant que le contrôleur
 *                            ne redemande des pixels. Les deux seuils sont
 *                            publiés — ⛔ on ne choisit pas à la place du
 *                            lecteur.
 *    Et en second observable, la comptabilité des enroulements :
 *      - `wraps` doit valoir `trames`, UN pour UN (voir l'amendement plus haut).
 *        `manques` = trames sans enroulement, `doubles` = trames à deux.
 *
 * ⚠️ CE QU'IL NE MESURE PAS, ET IL FAUT LE DIRE.
 *    Un intervalle long PROUVE que l'ISR est arrivée tard ; il ne prouve pas
 *    que l'œil a vu l'image glisser. La correspondance compteur <-> œil est un
 *    RÉSULTAT À ÉTABLIR (AC2 de dn4-10), ⛔ pas une hypothèse de conception.
 *    Et l'inverse vaut aussi : un compteur à zéro pendant que l'image saute
 *    voudrait dire que l'instrument regarde le mauvais événement.
 *
 * ⚠️ SÛRETÉ DE CONCURRENCE — la règle tenue ici : CHAQUE variable mutable n'est
 *    écrite QUE PAR UNE SEULE ISR. `s_bnc_wraps` / `s_bnc_t_wrap_us` par l'ISR
 *    d'enroulement ; tout le reste par l'ISR de vsync. La remise à zéro
 *    demandée depuis la console ne touche RIEN : elle pose un drapeau que l'ISR
 *    de vsync consomme elle-même, au prochain retour vertical (<= 27 ms). Donc
 *    ⛔ aucun verrou sur le chemin chaud — on mesure une famine, on ne va pas
 *    la fabriquer.
 *    Les horodatages sont en `uint32_t` de microsecondes (32 bits = lecture
 *    atomique sur cette puce ; l'enroulement à 4 295 s se gère par la
 *    soustraction non signée).
 */
typedef struct {
    uint32_t trames;       /* vsync comptés dans la fenêtre */
    uint32_t wraps;        /* enroulements `on_frame_buf_complete` dans la fenêtre */
    uint32_t manques;      /* trames SANS enroulement */
    uint32_t doubles;      /* trames à 2 enroulements ou plus */

    uint32_t intervalles;  /* échantillons d'intervalle vsync -> vsync */
    uint32_t inter_min_us;
    uint32_t inter_max_us;
    uint64_t inter_somme_us;

    uint32_t retards_100;   /* intervalle > période +  100 us */
    uint32_t retards_bp;    /* > période + back porch (775 us) — LE BUDGET */
    uint32_t retards_vb;    /* > période + VBlank entier (1 937 us) */
    uint32_t retards_trame; /* > 2 périodes — une trame ENTIÈRE de retard */

    /* ── dn4-10, DEUXIÈME PASSE : LA PHASE `enroulement -> VSYNC_END` ─────────
     * 🔴 Ajoutée le 2026-08-23 parce que l'ŒIL A PRIS LES COMPTEURS CI-DESSUS EN
     *    DÉFAUT : sous l'agent RÉEL, 180 s, `manques = 0` et gigue max +16 µs,
     *    pendant que l'owner voyait « quelques pixels vers le bas, ça s'abaisse
     *    puis revient, quasiment toutes les secondes ».
     * 🎯 L'échelle vient de sa phrase : à 16 MHz, UN PIXEL DURE 62,5 ns, donc les
     *    seuils ci-dessus (100 µs = 1 600 px) ne pouvaient PAS voir « quelques
     *    pixels ». La phase mesure le retard ABSOLU de l'ISR de VSYNC_END, pas sa
     *    gigue relative — et c'est ce retard-là que le driver rend responsable du
     *    décalage.
     * ⚠️ Plancher de l'instrument : la MICROSECONDE, soit 16 pixels.
     *    ⛔ « 0 dépassement » ne veut donc PAS dire « 0 pixel ».
     * ⚠️ Les seuils se comptent contre le MINIMUM de la fenêtre (la phase « à
     *    l'heure »), et les `ph_ecarte` premières trames servent à l'établir.
     * 🔴 AMENDÉ LE 2026-08-27 (revue de code) — ⛔ CETTE LIGNE EST FAUSSE DEPUIS
     *    LE 2026-08-23, et elle vivait à SIX LIGNES du bloc qui la corrige
     *    (« LES SEUILS SE COMPTENT CONTRE LE MAXIMUM », juste en dessous).
     *    `3cc7412` avait corrigé un commentaire sur deux. ⛔ On annote, on
     *    n'efface pas. Ce qui est vrai : la référence est le MAXIMUM des
     *    `ph_ecarte` trames de dégrossissage, et elle est FIGÉE (`ph_ref_us`). */
    uint32_t ph_n;         /* échantillons COMPTÉS (dégrossissage exclu) */
    uint32_t ph_ecarte;    /* échantillons du dégrossissage, ⛔ non comptés */
    /*
     * 🔴 LES TROIS FAÇONS DONT L'INSTRUMENT JETTE UN ÉCHANTILLON — publiées
     *    depuis le 2026-08-27 (revue de code). Aucune n'était comptée nulle
     *    part, et c'est le pire des trois défauts de comptage : la console ne
     *    pouvait pas distinguer « aucun retard » de « des retards que je ne
     *    sais pas mesurer ».
     *  - `ph_rejete`  : phase >= 2 périodes ⇒ hors borne de sanité. ⛔ C'est
     *                   EXACTEMENT le glissement recherché qui tombe là.
     *  - `ph_doubles_ecartes` : trame à DEUX enroulements ou plus. Avant, elles
     *                   alimentaient la phase contre le SECOND enroulement ⇒
     *                   phase très courte ⇒ déficit maximal ⇒ une corruption
     *                   FABRIQUÉE par la comptabilité.
     *  - `ph_dechire` : la paire (`wraps`, `t_wrap`) a été lue incohérente —
     *                   l'ISR d'enroulement a préempté celle de vsync. Voir
     *                   l'invariant de concurrence dans dn_measure.c.
     * ⛔ UN « 0 » SUR LES QUATRE SEUILS NE VAUT QUE SI CES TROIS-LÀ SONT À ZÉRO.
     */
    uint32_t ph_rejete;
    uint32_t ph_doubles_ecartes;
    uint32_t ph_dechire;
    /*  - `ph_futur` : l'horodatage d'enroulement est POSTERIEUR a l'entree de
     *    l'ISR de vsync. ⛔ CE N'EST PAS UN RETARD, c'est un entrelacement des
     *    deux ISR : `t_us` est pris en tete de `on_vsync` et le compteur
     *    d'enroulements est lu ~40 lignes plus loin ; si l'ISR d'enroulement
     *    tombe entre les deux, la paire est NEUVE et COHERENTE (la garde de
     *    dechirure se tait, a juste titre) mais `tw > t_us`. La soustraction non
     *    signee debordait alors a ~4,29e9 et franchissait la borne de sanite :
     *    l'evenement etait compte dans `ph_rejete`, et la console AFFIRMAIT que
     *    les « hors borne » SONT LES PIRES RETARDS. ⛔ Faux pour ce chemin-la.
     *    3e revue du 2026-08-27 : les deux causes sont desormais SEPAREES, et
     *    aucune des deux n'est presentee comme l'autre. */
    uint32_t ph_futur;
    /*  - `ph_degrossi_n` : la TAILLE de la population qui a servi à figer
     *    `ph_ref_us`. ⛔ PUBLIÉE, ⛔ pas récitée par la console : c'est elle qui
     *    dit pourquoi la contre-épreuve `MAX > référence` est quasi-certaine
     *    (max de ~32 trames contre max de milliers). Un lecteur qui la voit à
     *    côté de `ph_n` n'a plus besoin de lire le code pour le savoir. */
    uint32_t ph_degrossi_n;
    uint32_t ph_min_us;
    uint32_t ph_max_us;
    /* La référence des déficits, FIGÉE à la fin du dégrossissage (2026-08-27).
     * ⚠️ `ph_max_us > ph_ref_us` ⇒ le dégrossissage a raté la phase « à
     *    l'heure » et les déficits sont SOUS-comptés. La console le dit. */
    uint32_t ph_ref_us;
    uint64_t ph_somme_us;
    /* 🔴 LES SEUILS SE COMPTENT CONTRE LE **MAXIMUM**, ⛔ pas contre le minimum.
     *    Corrigé le 2026-08-23, DANS LA SÉANCE, par la mesure :
     *      repos  180 s : min 1915 · moy 1961 · MAX 1978  (étendue  63 µs)
     *      trafic 180 s : min 1249 · moy 1955 · MAX 1990  (étendue 741 µs)
     *    Le mode est EN HAUT, les écarts vont vers le BAS. Référencer au minimum
     *    comptait 6 660 trames sur 6 725 sous trafic et 0 au repos : ça ne
     *    discrimine rien. C'est la phase COURTE qui est le signal — un
     *    enroulement EN RETARD (le remplissage qui décroche) la raccourcit.
     * 🎯 Et le seuil n'est PAS arbitraire : `t_demi_us` est la durée
     *    d'écoulement d'un DEMI-BOUNCE. Au-delà, la DMA a forcément lu un tampon
     *    pas encore rempli — c'est le décalage que l'œil voit. */
    uint32_t ph_10pc;      /* déficit sous le max > 10 % du demi-bounce */
    uint32_t ph_25pc;      /* > 25 % */
    uint32_t ph_50pc;      /* > 50 % */
    uint32_t ph_100pc;     /* > 100 % — 🔴 LE SEUIL DE CORRUPTION */
    uint32_t ph_deficit_max_us; /* le pire déficit observé */
    uint32_t t_demi_us;    /* écoulement d'un demi-bounce, lu sur le panneau
                            * RÉELLEMENT monté (⛔ pas sur la NVS) */
    /* ⚠️ « publiée pour que la sortie se suffise à elle-même » était FAUX
     *    jusqu'au 2026-08-27 : ce champ était rempli et AUCUN `printf` de
     *    dn_console.c ne l'imprimait — un champ mort, documenté comme publié.
     *    Il l'est désormais, dans le bloc de phase de `flush`. */
    uint32_t us_par_ligne; /* la durée d'une ligne, ARRONDIE à la µs (38,75 → 39) */
    /* La période de trame en NANOSECONDES, donc EXACTE (62,5 ns par pixel).
     * `dn_measure_periode_us()` l'arrondit ; la console imprime les deux, parce
     * que la troncature entière d'avant le 2026-08-27 fabriquait un « retard
     * PIRE observé : +1 µs » sur une trame parfaitement à l'heure. */
    uint32_t periode_ns;

    /* ── dn4-12 : LA PLUS LONGUE SÉRIE DE TRAMES CONSÉCUTIVES NON SAINES ────
     *
     * 🔴 LE TROU QUE ÇA FERME. Tous les compteurs ci-dessus comptent des TRAMES
     *    au-dessus d'un seuil ; AUCUN ne compte leur CONSÉCUTIVITÉ. Ils ne
     *    peuvent donc ni confirmer ni infirmer le constat de l'owner du
     *    2026-08-23 — « parfois ça reste dans un état glissé […] ensuite ça
     *    reglisse ». Le driver nomme ce cas « permanent desync » et n'a plus
     *    AUCUNE parade automatique depuis `4734d07` (RESTART_IN_VSYNC=n).
     *
     * 🔴 L'UNITÉ EST LA TRAME, ⛔ PAS LA MICROSECONDE (décision D1). `esp_timer`
     *    reboucle à 2^32 µs = 71,58 min — le défaut que dn4-5/AC1.2 vient de
     *    fermer sur `fenetre_ms`. Un compte de trames ne reboucle qu'à ~3,6 ans
     *    à 37,40 Hz : la grandeur survit à une nuit et à une semaine PAR
     *    CONSTRUCTION. La conversion en ms se fait CÔTÉ CONSOLE, depuis
     *    `periode_ns` (26 737 500 ns, EXACTE) — ⛔ jamais dans l'ISR.
     *
     * ⚠️ C'EST UN MINORANT, ET `ser_rompues_indet` LE BORNE. Les trois classes
     *    INDÉTERMINÉES (horodatage postérieur, paire déchirée, deux
     *    enroulements) ROMPENT la série : on ne sait pas si la trame était
     *    saine, et la faire continuer FABRIQUERAIT de la durée. Une série vraie
     *    a donc pu être COUPÉE EN DEUX. ⛔ Ce nombre NE SE SOUSTRAIT PAS et NE
     *    SE RECOMPOSE PAS — il borne la confiance, il ne corrige rien.
     *
     * ⛔ AUCUN PLAFOND, AUCUN ÉCRETAGE (précédent dn4-13 : `dn_hist_rattraper()`
     *    écrêtait à 120 AVANT de compter, et `ui off` de 10 min et de 1 h
     *    imprimaient EXACTEMENT la même phrase). Deux durées différentes
     *    rendent deux nombres différents, quelle que soit leur longueur.
     *
     * ⛔ CE QUE CES CHAMPS NE MESURENT PAS : le nombre de relances réellement
     *    jouées par le driver, INOBSERVABLE à `=n` (il relance en interne sans
     *    passer par `need_restart`, esp_lcd_panel_rgb.c:1153-1163). On mesure la
     *    PERSISTANCE DE L'ÉTAT, ⛔ jamais l'échec de relance.
     *
     * La table des HUIT classes de trame et le motif de chaque verdict sont
     * dans `dn_measure_serie.h` — ils vivent AVEC la logique, pas ici.
     */
    uint32_t ser_max;             /* 🔴 LA PLUS LONGUE SÉRIE, en TRAMES */
    uint32_t ser_max_a;           /* sa composition : classe A (déficit franchi) */
    uint32_t ser_max_c;           /*                  classe C (hors borne de sanité) */
    uint32_t ser_max_d;           /*                  classe D (aucun enroulement) */
    uint32_t ser_max_debut;       /* index de trame DEPUIS LA RAZ où elle a commencé */
    uint32_t ser_n;               /* nombre TOTAL de séries (celle en cours comprise) */
    uint32_t ser_rompues_indet;   /* ⚠️ séries rompues par une trame INDÉTERMINÉE */
    uint32_t ser_courante;        /* la série EN COURS à l'instant de la lecture —
                                   * sans elle, un lecteur ne sait pas si le
                                   * maximum est encore en train de CROÎTRE */
    /* Le compteur de RAZ consommées. ⚠️ « un compteur vide n'est pas une absence
     * d'histoire » : `flush` est remis par `flush reset` ET par tout redémarrage
     * de la puce. À 0, la console écrit « ⛔ AUCUN flush reset : référence SEMÉE
     * AU BOOT » — et ce n'est pas cosmétique : une référence semée au boot est
     * PATHOLOGIQUE 1 fois sur 4 (étendue 100 µs contre 1 µs en régime, le seau
     * 10 % passant de 4,5 % à 99,98 % des trames). */
    uint32_t raz_gen;

    /*
     * 🔴 dn4-5 / AC1.2 — CE CHAMP REBOUCLAIT, ET IL DIT SUR QUELLE DURÉE TOUT
     *    LE BLOC A ÉTÉ CUMULÉ. Il valait `(uint32_t - uint32_t) / 1000` en µs : juste
     *    jusqu'à 2^32 µs = **4 294,967 s = 71,58 min**, faux modulo cette durée
     *    au-delà — sans un mot, et à exit 0. Il est désormais calculé en base
     *    `int64_t` (`esp_timer_get_time()` ne déborde qu'après ~292 000 ans) et
     *    publié sur 64 bits : plus aucun horizon avant 5,8 × 10^8 ans.
     * ⚠️ ⛔ CE N'EST PAS « le dénominateur des taux que `flush` publie », comme
     *    le disait le cadrage de dn4-5 : vérifié au `grep` sur les deux dépôts
     *    le 2026-08-26, les taux se divisent par `intervalles`, `ph_n` et
     *    `t_demi_us`, et aucun outil de `tools/` ni de `agent/` ne lit ce
     *    champ. La gravité est ailleurs, et elle est intacte : c'est le SEUL
     *    chiffre qui dise sur quelle durée les compteurs ont été cumulés, et
     *    c'est un HUMAIN qui fait la division.
     * ⚠️ La reconstruction de l'origine sur 64 bits est faite CÔTÉ TÂCHE
     *    CONSOLE, ⛔ pas dans l'ISR — voir le commentaire de `s_bnc_arme_us64`
     *    dans dn_measure.c. L'invariant « aucun verrou sur le chemin chaud »
     *    tient sans exception.
     */
    uint64_t fenetre_ms;    /* durée écoulée depuis la remise à zéro */
    /*
     * LA CONTRE-ÉPREUVE, PUBLIÉE À CÔTÉ DE LA VALEUR JUSTE. C'est très
     * exactement ce que l'instrument d'AVANT dn4-5 aurait imprimé. Tant que
     * `fenetre_deborde` est faux les deux coïncident (au ms près) ; dès qu'il
     * est vrai, l'écart EST la démonstration du défaut, lisible sur la sortie
     * elle-même — ⛔ pas déduite d'une relecture du code.
     */
    uint32_t fenetre_ms_32; /* la même fenêtre, calculée à l'ancienne (32 bits) */
    bool fenetre_deborde;   /* ⚠️ la fenêtre dépasse 71,58 min : `fenetre_ms_32` MENT */
    bool raz_en_attente;    /* la RAZ n'a pas encore été consommée par l'ISR */
    /*
     * 🔴 2026-08-27 (revue de code) — L'EN-TÊTE PROMETTAIT « INSTANTANÉ
     *    COHÉRENT » PENDANT QUE LE `.c` DÉCLARAIT « NON ATOMIQUE, ET C'EST
     *    ASSUMÉ ». Deux textes normatifs en désaccord, sur la fonction qui
     *    produit TOUS les chiffres de la séance. Et l'excuse du `.c` (« une
     *    incohérence porterait sur UNE trame ») était fausse pour les deux
     *    sommes 64 bits : lues en deux mots sur un CPU 32 bits, une retenue
     *    entre les deux les décale de 2^32 µs.
     * ⇒ La lecture est désormais GARDÉE (encadrement par `s_bnc_raz_gen` +
     *   double lecture des sommes, côté tâche uniquement, ⛔ aucun verrou sur
     *   le chemin chaud). Ce drapeau dit quand la garde n'a pas convergé —
     *   auquel cas le bloc reste imprimé mais il est ÉTIQUETÉ.
     */
    bool lecture_dechiree;
} dn_bounce_stats_t;

/* Arme la remise à zéro. ⚠️ Elle prend effet AU PROCHAIN VSYNC (<= 27 ms), pas
 * au retour de l'appel : c'est ce report qui rend la mise à zéro sûre sans
 * verrou. `raz_en_attente` le dit à qui lit trop vite. */
void dn_measure_bounce_reset(void);

/* Instantané des compteurs. Appelable depuis une TÂCHE uniquement.
 * ⚠️ « Cohérent » sans réserve était FAUX (revue du 2026-08-27) : voir
 *    `lecture_dechiree` ci-dessus. Ce qui est garanti : chaque champ 32 bits
 *    est lu d'un seul accès ; les deux sommes 64 bits et la paire
 *    (compteur, base) sont protégées par une garde côté lecteur, et l'échec de
 *    cette garde est PUBLIÉ au lieu d'être tu. */
void dn_measure_bounce_get(dn_bounce_stats_t *out);

/* Les trois grandeurs de référence, en microsecondes, calculées depuis les
 * timings de dn_pins.h — publiées pour que la sortie console se suffise à
 * elle-même et qu'aucun seuil ne soit un nombre magique. */
uint32_t dn_measure_periode_us(void);
uint32_t dn_measure_back_porch_us(void);
uint32_t dn_measure_vblank_us(void);

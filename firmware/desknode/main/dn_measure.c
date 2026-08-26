#include "dn_measure.h"

#include <math.h>

#include "dn_bootcfg.h"
#include "dn_display.h"
#include "dn_pins.h"
#include "esp_attr.h"
#include "esp_check.h"
#include "esp_heap_caps.h"
#include "esp_lcd_panel_rgb.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"

static const char *TAG = "dn_mes";

/*
 * ⚠️ CE COMPTEUR EST TOUCHÉ SOUS ISR.
 *    - `volatile`, sinon le compilateur peut garder la valeur en registre ;
 *    - en RAM INTERNE (.bss), jamais en PSRAM : avec
 *      CONFIG_LCD_RGB_ISR_IRAM_SAFE=y l'ISR tourne cache désactivé, et un accès
 *      PSRAM y planterait la puce ;
 *    - AUCUN ESP_LOGx dans le callback, pour la même raison.
 */
static volatile uint32_t s_vsync_count;

/* Sémaphore de rendez-vous avec le retour vertical. Donné DEPUIS L'ISR :
 * `xSemaphoreGiveFromISR` est en IRAM par défaut dans ESP-IDF (FreeRTOS n'est
 * déplacé en flash que si CONFIG_FREERTOS_PLACE_FUNCTIONS_INTO_FLASH est
 * activé, ce qu'on ne fait pas) — indispensable, puisque l'ISR tourne cache
 * désactivé pendant les écritures flash d'AC6. */
static SemaphoreHandle_t s_vsync_sem;

/* Rendez-vous avec `on_frame_buf_complete`.
 * ⚠️ Le nom du callback ment SUR CETTE PUCE, et ce commentaire mentait avec
 *    lui : il annonçait « ce framebuffer-là n'est plus lu par la DMA ». Cette
 *    garantie-là exige l'événement de bascule de lien GDMA, compilé sous le
 *    seul `SOC_AXI_GDMA_SUPPORTED` — que l'ESP32-S3 ne définit pas
 *    (soc_caps.h:33 : `SOC_AHB_GDMA_SUPPORTED` uniquement). Ici le callback
 *    arrive du trans-EOF de la DMA. C'est donc un POINT DE PHASE différent du
 *    VSYNC dans la trame, et rien de plus. Le gain mesuré tient, l'explication
 *    d'origine non — le détail et les références exactes sont dans
 *    dn_measure.h, au-dessus de `dn_measure_arm_frame_done()`. */
static SemaphoreHandle_t s_fbdone_sem;

/*
 * Les abonnements au vsync (dn1-3). Tableau de taille FIXE, alloué une fois pour
 * toutes : l'ISR le parcourt cache désactivé, donc il doit vivre en RAM interne
 * (.bss) et ne jamais être réalloué. Le compteur d'abonnés n'est écrit que depuis
 * `dn_measure_vsync_subscribe()`, avant que le panneau ne tourne pour de bon —
 * mais il est lu par l'ISR, d'où le `volatile`.
 */
/* `volatile` sur le TABLEAU aussi (revue) : le commentaire ci-dessus promettait
 * « publié en dernier », mais un store ordinaire suivi d'un store volatile n'a
 * AUCUNE garantie d'ordre en C — l'invariant était fourni par chance. Avec les
 * deux volatiles, le compilateur ne peut pas réordonner les deux écritures. */
static SemaphoreHandle_t volatile s_vsync_subs[DN_VSYNC_SUBS_MAX];
static volatile int s_vsync_subs_n;
static const char *s_vsync_subs_nom[DN_VSYNC_SUBS_MAX];

static size_t s_psram_avant;
static size_t s_psram_apres;

/*
 * ─── dn4-10 : LE COMPTEUR DE GLISSEMENT DE TRAME ────────────────────────────
 * La justification complete, les voies ECARTEES et la regle de concurrence
 * sont dans dn_measure.h, au-dessus de `dn_bounce_stats_t`. Ici, seulement
 * l'invariant qui doit tenir a la relecture :
 *
 *   PROPRIETAIRE UNIQUE PAR VARIABLE.
 *     ecrites par l'ISR d'enroulement (`on_frame_buf_complete`) :
 *        s_bnc_wraps, s_bnc_t_wrap_us
 *     ecrites par l'ISR de vsync (`on_vsync`) :
 *        tout le reste, Y COMPRIS la consommation de la RAZ.
 *     ecrite par la tache console :
 *        s_bnc_raz, et RIEN d'autre.
 *     ecrite par la TACHE DE BOOT, une fois, AVANT tout enregistrement de
 *     callback (donc avant que la moindre ISR ne puisse la lire) :
 *        s_bnc_t_demi_us      <-- 🔴 AJOUTEE LE 2026-08-27 : elle etait
 *        PARTAGEE tache -> ISR, NON `volatile`, et ne figurait dans AUCUN
 *        des trois jeux ci-dessus. L'enumeration se disait exhaustive.
 *   => aucun verrou, aucune section critique, sur un chemin qui tire
 *      37,40 fois par seconde et dont on mesure justement le retard.
 *
 * 🔴 CE QUE CET INVARIANT NE GARANTIT PAS, ET C'EST VERIFIE PAR LECTURE DE
 *    L'IDF LE 2026-08-27 (revue de code). Le fichier affirmait ailleurs que
 *    « les deux ISR sont sur le meme coeur au meme niveau de priorite, donc
 *    elles ne se preemptent pas ». C'EST UNE HYPOTHESE, PAS UN FAIT :
 *      - `on_vsync` <- `rgb_lcd_default_isr_handler` (esp_lcd_panel_rgb.c:1247),
 *        interruption du peripherique LCD, allouee :362 avec
 *        `LCD_RGB_INTR_ALLOC_FLAGS | ESP_INTR_FLAG_SHARED | ESP_INTR_FLAG_LOWMED` ;
 *      - `on_frame_buf_complete` <- `lcd_rgb_panel_eof_handler` (:948), callback
 *        GDMA enregistre :1029, dont l'ISR est allouee dans gdma.c:962 avec
 *        `ESP_INTR_FLAG_INTRDISABLED | ESP_INTR_FLAG_LOWMED | ESP_INTR_FLAG_SHARED`.
 *    `ESP_INTR_FLAG_LOWMED` couvre les NIVEAUX 1, 2 ET 3, et l'allocateur prend
 *    le vecteur libre le mieux place (intr_alloc.c:395-425). RIEN, dans aucun
 *    des deux pilotes, n'impose aux deux le MEME niveau. A niveaux differents,
 *    l'ISR d'enroulement PEUT preempter celle de vsync.
 *    ⇒ La seule paire exposee est (s_bnc_wraps, s_bnc_t_wrap_us), ecrite en
 *      deux stores et lue en deux temps. Elle est desormais protegee par une
 *      GARDE DE DECHIRURE dans `on_vsync` (relecture de `s_bnc_wraps` apres
 *      l'horodatage), et les echantillons jetes sont comptes (`ph_dechire`).
 *      ⛔ Toujours aucun verrou : on mesure une famine, on ne la fabrique pas.
 *
 * ⛔ AUCUN ESP_LOGx ici : le port serie EST le transport de la mesure, et
 *    journaliser depuis l'ISR a la frequence du defaut le FABRIQUERAIT.
 */

/* Bornes calculees depuis les timings de dn_pins.h. `#define` et non
 * `static const` : constant-folded a la compilation, donc AUCUN acces memoire
 * depuis l'ISR — la .rodata vit en flash, et l'ISR peut tourner cache coupe
 * pendant une ecriture flash (stimulus `flash on`). */
#define DN_HTOTAL_PX                                                          \
    (DN_LCD_H_RES + DN_HSYNC_PULSE + DN_HSYNC_BACK_PORCH + DN_HSYNC_FRONT_PORCH)
#define DN_VTOTAL_LI                                                          \
    (DN_LCD_V_RES + DN_VSYNC_PULSE + DN_VSYNC_BACK_PORCH + DN_VSYNC_FRONT_PORCH)
/* 🔴 CORRIGE LE 2026-08-27 (revue de code, constat « troncature entiere ») —
 *    ⛔ CE N'ETAIT PAS UN ARRONDI SANS CONSEQUENCE, C'ETAIT UN COMPTEUR QUI
 *    FABRIQUAIT DU RETARD. `620 x n / 16` n'est entier que si `n = 0 [4]` :
 *    la periode valait 26 737 us au lieu de 26 737,5 => `flush` imprimait
 *    « retard PIRE observe : +1 us » SUR UNE TRAME PARFAITEMENT A L'HEURE,
 *    a comparer aux « +16 us » publies comme resultat au repos. Et
 *    `t_demi_us` etait sous-estime de ~2 % pour bounce_px = 480, 960, 2400 et
 *    4800 — dont DEUX des six points du balayage de §20.7.6, donc un
 *    SUR-COMPTAGE des franchissements precisement la.
 * ⇒ On calcule en NANOSECONDES (exact : 62,5 ns par pixel a 16 MHz, donc
 *   tout multiple de 2 pixels tombe juste) et on arrondit AU PLUS PROCHE pour
 *   la vue en microsecondes. La valeur exacte reste publiee a cote, en ns :
 *   la sortie console dit desormais 26 737,500 us, ⛔ pas 26 737. */
#define DN_NS_POUR_LIGNES(n)                                                  \
    ((uint32_t)(((uint64_t)DN_HTOTAL_PX * (uint64_t)(n) * 1000000000ULL) /     \
                (uint64_t)DN_PCLK_HZ))
#define DN_US_POUR_LIGNES(n) ((uint32_t)((DN_NS_POUR_LIGNES(n) + 500u) / 1000u))

/* 620 x 690 / 16 MHz = 26 737,5 us — arrondi a 26 738, exact en ns. */
#define DN_PERIODE_US DN_US_POUR_LIGNES(DN_VTOTAL_LI)
#define DN_PERIODE_NS DN_NS_POUR_LIGNES(DN_VTOTAL_LI)
/* 620 x 20 / 16 MHz = 775 us — le budget REEL de l'ISR : VSYNC_END tombe a la
 * FIN de l'impulsion, il ne reste que le back porch avant que le controleur ne
 * redemande des pixels. */
#define DN_BACK_PORCH_US DN_US_POUR_LIGNES(DN_VSYNC_BACK_PORCH)
/* 620 x 50 / 16 MHz = 1 937 us — le VBlank ENTIER, le chiffre optimiste du
 * commentaire d'Espressif. Publie a cote, ⛔ pas a la place. */
#define DN_VBLANK_US DN_US_POUR_LIGNES(DN_VTOTAL_LI - DN_LCD_V_RES)

/* ── ecrites par l'ISR d'enroulement UNIQUEMENT ── */
static volatile uint32_t s_bnc_wraps;      /* monotone depuis le boot */
static volatile uint32_t s_bnc_t_wrap_us;  /* horodatage du dernier enroulement */

/* ── ecrites par l'ISR de vsync UNIQUEMENT ── */
static volatile uint32_t s_bnc_wraps_vus;  /* valeur de s_bnc_wraps au vsync precedent */
static volatile uint32_t s_bnc_base_wraps; /* references posees a la RAZ */
static volatile uint32_t s_bnc_base_vsync;
static volatile uint32_t s_bnc_t0_us;
/* dn4-5 / AC1.2 : +1 a CHAQUE RAZ CONSOMMEE. Il vit dans la branche RAZ,
 * donc il ne coute RIEN sur les 37,40 trames/s du regime normal. C'est lui
 * qui dit a la tache console qu'une NOUVELLE origine a ete posee — se fier
 * a un changement de VALEUR de s_bnc_t0_us raterait le cas (improbable mais
 * pas impossible) de deux RAZ separees d'exactement 2^32 us. */
static volatile uint32_t s_bnc_raz_gen;
static volatile uint32_t s_bnc_t_vsync_us; /* horodatage du vsync precedent */
static volatile bool s_bnc_arme;           /* un intervalle est-il mesurable ? */
static volatile uint32_t s_bnc_manques;
static volatile uint32_t s_bnc_doubles;
static volatile uint32_t s_bnc_inter_n;
static volatile uint32_t s_bnc_inter_min;
static volatile uint32_t s_bnc_inter_max;
static volatile uint64_t s_bnc_inter_somme;
static volatile uint32_t s_bnc_ret_100;
static volatile uint32_t s_bnc_ret_bp;
static volatile uint32_t s_bnc_ret_vb;
static volatile uint32_t s_bnc_ret_trame;

/* ── dn4-10, DEUXIEME PASSE — LA PHASE, ecrite par l'ISR de vsync UNIQUEMENT ──
 *
 * 🔴 POURQUOI ELLE EXISTE : la premiere passe a ete PRISE EN DEFAUT PAR L'OEIL,
 *    le 2026-08-23. Sous l'agent REEL, 180 s, `bounce_px = 7680` : les compteurs
 *    rendaient `manques = 0` et une gigue vsync->vsync de +16 us AU PIRE, pendant
 *    que l'owner voyait « un glissement de quelques pixels vers le BAS, ca
 *    s'abaisse puis revient, quasiment toutes les secondes ». C'est la DEUXIEME
 *    issue prevue par AC2 : compteur a zero, oeil qui voit => l'instrument ne
 *    regardait pas le bon evenement. On ne l'efface pas, on lui en ajoute un.
 *
 * 🔴 CE QUE LA DESCRIPTION DE L'OWNER A APPRIS, et qui fixe l'echelle :
 *    « quelques pixels » — pas une ligne, pas une trame. A pclk = 16 MHz,
 *    UN PIXEL DURE 62,5 ns. Les seuils de la premiere passe (100 us, 775 us)
 *    sont donc TROIS ORDRES DE GRANDEUR trop gros : 100 us = 1 600 pixels.
 *    Un compteur qui ne se declenche qu'a 1 600 pixels de retard ne pouvait pas
 *    voir un decalage de quelques-uns. Il ne mentait pas — il ne regardait pas.
 *
 * 🎯 CE QU'ON MESURE MAINTENANT : la PHASE `enroulement -> VSYNC_END`.
 *    L'enroulement de `bounce_pos_px` tombe a un point FIXE du balayage (la DMA
 *    avance a cadence materielle, elle ne derive pas). Le VSYNC_END, lui, est
 *    servi par une ISR qui PEUT etre retardee. L'ecart entre les deux est donc
 *    le RETARD ABSOLU de l'ISR de VSYNC_END, a un offset constant pres — et
 *    c'est exactement la grandeur que le driver rend responsable du decalage.
 *
 * ⚠️ CE QUE CETTE MESURE NE SAIT PAS FAIRE, et il faut le lire avant de conclure :
 *    - l'horodatage de l'enroulement vient LUI AUSSI d'une ISR (le trans-EOF).
 *      Un retard COMMUN aux deux s'annule et reste invisible. Les deux ISR sont
 *      sur le meme coeur au meme niveau de priorite, donc elles ne se preemptent
 *      pas ; mais un tiers qui les retarderait ENSEMBLE passerait au travers.
 *      🔴 AMENDE LE 2026-08-27 : « AU MEME NIVEAU DE PRIORITE » N'EST PAS
 *      GARANTI — les deux sources sont allouees en `ESP_INTR_FLAG_LOWMED`
 *      (niveaux 1|2|3) sans contrainte d'egalite. Detail et references exactes
 *      dans l'invariant en tete de fichier. La preemption est desormais
 *      DETECTEE, ⛔ plus supposee absente.
 *    - la resolution est la MICROSECONDE (`esp_timer`), soit 16 pixels. Un
 *      decalage de moins de 16 px reste sous le plancher de l'instrument.
 *      ⛔ Donc « 0 depassement » ne veut PAS dire « 0 pixel ».
 *
 * ⚠️ REFERENCE AUTO-CALIBREE, ⛔ AUCUN NOMBRE MAGIQUE : les seuils se comptent
 *    par rapport au MINIMUM observe dans la fenetre — la phase « a l'heure ».
 *    Les 32 premieres trames servent a l'etablir et ne sont PAS comptees ; sans
 *    ce degrossissage, un minimum encore haut ferait passer les premiers
 *    echantillons pour des retards. Le nombre de trames ecartees est PUBLIE.
 * 🔴 AMENDE LE 2026-08-27 (revue de code) — ⛔ « PAR RAPPORT AU MINIMUM » EST
 *    FAUX DEPUIS LE 2026-08-23, ET CE PARAGRAPHE LE DISAIT ENCORE A SIX LIGNES
 *    DE SON PROPRE CORRECTIF (le bloc « SEUILS REFERENCES AU MAXIMUM » juste
 *    en dessous). `3cc7412` avait corrige UN commentaire sur DEUX. C'est
 *    litteralement le defaut « doc et code en desaccord » que dn3-2 AC9 a paye.
 *    ⛔ ON ANNOTE, ON N'EFFACE PAS : ce texte reste pour dire ce qu'on croyait.
 * ⇒ CE QUI EST VRAI AUJOURD'HUI : les seuils se comptent contre une REFERENCE
 *   FIGEE, egale au MAXIMUM des trames de degrossissage — ⛔ ni le minimum, ni
 *   un maximum glissant. Voir `s_bnc_ph_ref_us`. */
#define DN_PHASE_DEGROSSI 32u
/* 1 px = 1/16 MHz = 62,5 ns ; 1 ligne = htotal px = 620/16 MHz = 38,75 us. */
#define DN_US_PAR_LIGNE DN_US_POUR_LIGNES(1)
static volatile uint32_t s_bnc_ph_n;
static volatile uint32_t s_bnc_ph_min;
static volatile uint32_t s_bnc_ph_max;
static volatile uint64_t s_bnc_ph_somme;
/* 🔴 SEUILS REFERENCES AU **MAXIMUM**, ⛔ PLUS AU MINIMUM — corrige le
 *    2026-08-23, dans la seance meme, par la MESURE :
 *      repos    180 s : phase min 1915 · moy 1961 · MAX 1978   (etendue   63 us)
 *      trafic   180 s : phase min 1249 · moy 1955 · MAX 1990   (etendue  741 us)
 *    Le MODE est en HAUT et les ecarts vont vers le BAS. Referencer au minimum
 *    comptait donc « presque toutes les trames » sous trafic et rien au repos :
 *    un seau qui rend 6 660/6 725 ne discrimine rien. La phase COURTE est le
 *    signal, parce que `phase = t_vsync - t_enroulement` : un enroulement en
 *    RETARD (le remplissage qui decroche) RACCOURCIT la phase.
 *
 * 🎯 ET LE SEUIL QUI COMPTE N'EST PAS ARBITRAIRE : c'est la duree d'ecoulement
 *    d'un DEMI-BOUNCE. Au-dela, la DMA a forcement lu un tampon pas encore
 *    rempli. A `bounce_px = 7680` elle vaut 620 us — et le deficit mesure sous
 *    trafic est de 741 us, soit 121 us AU-DELA. C'est le decalage que l'owner
 *    voit. */
/* 🔴 `volatile` DEPUIS LE 2026-08-27 (revue) — ⛔ ELLE NE L'ETAIT PAS, ET ELLE
 *    EST PARTAGEE TACHE -> ISR. Elle est ecrite UNE FOIS par `dn_measure_attach()`
 *    (tache de boot) et lue a CHAQUE trame par l'ISR de vsync. Sans `volatile`
 *    le compilateur avait le droit de la garder en registre ; et elle
 *    n'apparaissait dans AUCUN des trois jeux de l'invariant en tete de fichier.
 *    ⇒ elle y est nommee desormais : ECRITE PAR LA TACHE DE BOOT, AVANT que le
 *    moindre callback ne soit enregistre — voir `dn_measure_attach()`. */
static volatile uint32_t s_bnc_t_demi_us; /* ecoulement d'un demi-bounce, pose a l'attache */

/* 🔴 LA REFERENCE DE PHASE EST FIGEE, ⛔ CE N'EST PLUS UN MAXIMUM GLISSANT —
 *    corrige le 2026-08-27 (revue de code, constat « reference a cliquet »).
 *    AVANT : `s_bnc_ph_max` etait mis a jour avec l'echantillon COURANT puis
 *    servait de reference au deficit de CE MEME echantillon, et ne redescendait
 *    JAMAIS. Consequences MESURABLES sur les chiffres deja publies :
 *      - UN SEUL retard ponctuel (la borne de sanite en laisse passer jusqu'a
 *        27 x la phase nominale) saturait « CORRUPTION » a 37,4/s pour TOUT LE
 *        RESTE de la fenetre ;
 *      - le meme jeu de valeurs dans l'ORDRE INVERSE rendait un `ph_100pc`
 *        DIFFERENT — un instrument qui depend de l'ordre n'est pas un instrument ;
 *      - et le protocole A/B qui a justifie la bascule du groupage ne remet pas
 *        les compteurs a zero entre les bras : le bras 1 fixait la reference, le
 *        bras 2 en HERITAIT.
 * ⇒ La reference est desormais le maximum des `DN_PHASE_DEGROSSI` trames de
 *   degrossissage, POSE UNE FOIS puis FIGE jusqu'a la prochaine RAZ.
 * ⚠️ CE QUE CA COUTE, ET IL FAUT LE SAVOIR : la reference se decide sur 32
 *    trames, soit ~0,86 s. Si le degrossissage tombe dans un regime DEJA
 *    degrade, la reference est trop BASSE et les deficits sont SOUS-comptes.
 *    C'est pourquoi `ph_max` (le maximum sur la population COMPTEE) est publie
 *    A COTE : `ph_max > ph_ref` est le signe que le degrossissage a rate la
 *    phase « a l'heure », et la console le DIT. */
static volatile uint32_t s_bnc_ph_ref_us;   /* reference FIGEE apres degrossissage */
static volatile uint32_t s_bnc_ph_ref_seed; /* maximum vu PENDANT le degrossissage */
/* 🔴 LES ECHANTILLONS QUE L'INSTRUMENT JETTE SONT DESORMAIS COMPTES — c'est le
 *    constat le plus court de la revue et le plus embarrassant : la borne de
 *    sanite (`ph >= 2 x DN_PERIODE_US`) ecarte EXACTEMENT le glissement recherche
 *    et ne l'incrementait NULLE PART. La console ne pouvait donc pas distinguer
 *    « aucun retard » de « des retards trop gros pour l'instrument ». */
static volatile uint32_t s_bnc_ph_rejete;   /* hors borne de sanite — LES PIRES */
static volatile uint32_t s_bnc_ph_doubles_ec; /* trames a >= 2 enroulements, ecartees */
static volatile uint32_t s_bnc_ph_dechire;  /* paire (wraps, t_wrap) lue DECHIREE */
static volatile uint32_t s_bnc_ph_10pc;  /* deficit sous la reference > 10 % du demi-bounce */
static volatile uint32_t s_bnc_ph_25pc;  /* > 25 % */
static volatile uint32_t s_bnc_ph_50pc;  /* > 50 % */
static volatile uint32_t s_bnc_ph_100pc; /* > 100 % — 🔴 LE SEUIL DE CORRUPTION */
static volatile uint32_t s_bnc_ph_deficit_max; /* le pire deficit, en us */
static volatile uint32_t s_bnc_ph_ecarte; /* echantillons du degrossissage */

/* ── ecrite par la tache console UNIQUEMENT ── */
static volatile bool s_bnc_raz;

/* ── dn4-5 / AC1.2 : LA FENETRE PASSE EN BASE 64 BITS ───────────────────────
 *
 * 🔴 LE DEFAUT QU'ON FERME, ET POURQUOI C'EST LE PIRE DES CINQ.
 *    `fenetre_ms` valait `(t_us - s_bnc_t0_us) / 1000`, DEUX `uint32_t` en us.
 *    La soustraction non signee absorbe UN enroulement, pas deux : au-dela de
 *    2^32 us = 4 294,967 s = 71,58 min, la fenetre publiee repart de zero, SANS
 *    UN MOT et A EXIT 0. Sur les 604 800 s d'un soak de 7 jours, cela fait
 *    140 rebouclages.
 *
 * ⚠️ ET LE MOTIF DE GRAVITE DU CADRAGE DE dn4-5 EST FAUX — verifie au `grep`
 *    sur les deux depots le 2026-08-26. Il annoncait « c'est LE DENOMINATEUR
 *    des taux que flush publie ». Elle ne l'est pas : dans dn_console.c les
 *    taux se divisent par `intervalles`, `ph_n` et `t_demi_us`, jamais par
 *    elle, et aucun outil de tools/ ni de agent/ ne la lit. Le defaut reste
 *    entier, mais sa gravite est AILLEURS : `fenetre_ms` est le SEUL chiffre
 *    qui dise sur quelle duree les compteurs du bloc ont ete cumules, et c'est
 *    un HUMAIN qui fait la division. Fausse, elle ne rend rien d'absurde — elle
 *    rend le bloc entier inexploitable en ayant l'air correct.
 *
 * ⛔ ON NE MET AUCUN VERROU ET ON NE TOUCHE PAS AU CHEMIN CHAUD DE L'ISR.
 *    « On mesure une famine, on ne va pas la fabriquer. » L'origine continue
 *    d'etre posee par l'ISR de vsync en 32 bits — un store aligne, un seul
 *    acces. Ce qu'on ajoute est ENTIEREMENT du cote de la tache console :
 *    `dn_measure_bounce_reset()` et `dn_measure_bounce_get()` sont toutes deux
 *    appelees depuis le REPL, donc ces trois variables ont UN SEUL ECRIVAIN ET
 *    UN SEUL LECTEUR, qui sont la meme tache. L'invariant du fichier tient.
 *
 * 🎯 L'ANCRE DE RECONSTRUCTION EST L'INSTANT D'ARMEMENT, ⛔ PAS L'INSTANT
 *    COURANT — et c'est la seule subtilite du correctif. L'ISR consomme la RAZ
 *    au vsync suivant, soit au plus 26,7 ms apres l'armement : les bits hauts
 *    de l'origine sont donc ceux de l'armement, ou ceux de l'armement + 1 si un
 *    enroulement 32 bits tombe entre les deux. Ancrer sur l'instant courant
 *    serait faux des que personne ne relit pendant 71,6 min — c'est-a-dire
 *    EXACTEMENT le regime d'un soak, ou l'on pose une RAZ puis on ne revient
 *    que des jours plus tard.
 *
 * ⚠️ AU BOOT LES TROIS VALENT 0, ET C'EST JUSTE : `esp_timer` part de 0 et
 *    `s_bnc_t0_us` vaut 0 tant qu'aucune RAZ n'a eu lieu. La fenetre initiale
 *    est donc l'uptime — ce qu'elle a toujours ete.
 */
static int64_t s_bnc_arme_us64;   /* instant d'ARMEMENT de la derniere RAZ */
static int64_t s_bnc_t0_us64;     /* origine EFFECTIVE, reconstruite sur 64 bits */
static uint32_t s_bnc_raz_gen_vu; /* generation de RAZ deja reconstruite */

static IRAM_ATTR bool on_vsync(esp_lcd_panel_handle_t panel,
                               const esp_lcd_rgb_panel_event_data_t *edata,
                               void *user_ctx)
{
    (void)panel;
    (void)edata;
    (void)user_ctx;
    s_vsync_count++;

    /* ── dn4-10 : la gigue de CETTE ISR est le defaut qu'on cherche ────────
     * Horodate EN PREMIER, avant tout autre travail : ce qu'on veut mesurer,
     * c'est l'instant ou l'ISR a REELLEMENT pris la main — latence d'interruption
     * comprise. Tout ce qu'on ferait avant s'ajouterait au chiffre.
     * `esp_timer_get_time()` est en IRAM (CONFIG_ESP_TIMER_IN_IRAM=y, verifie
     * dans sdkconfig le 2026-08-22) : appelable ici meme cache coupe. */
    uint32_t t_us = (uint32_t)esp_timer_get_time();

    if (s_bnc_raz) {
        /* La RAZ est CONSOMMEE ICI, et nulle part ailleurs : c'est ce report
         * qui rend la mise a zero sure sans verrou. La trame courante est
         * ecartee — sa fenetre serait tronquee. */
        s_bnc_raz = false;
        s_bnc_raz_gen++; /* dn4-5/AC1.2 : une origine NEUVE vient d'etre posee */
        s_bnc_base_wraps = s_bnc_wraps;
        s_bnc_base_vsync = s_vsync_count;
        s_bnc_wraps_vus = s_bnc_wraps;
        s_bnc_t0_us = t_us;
        s_bnc_t_vsync_us = t_us;
        s_bnc_arme = false; /* pas d'intervalle a cheval sur la RAZ */
        s_bnc_manques = 0;
        s_bnc_doubles = 0;
        s_bnc_inter_n = 0;
        s_bnc_inter_min = 0;
        s_bnc_inter_max = 0;
        s_bnc_inter_somme = 0;
        s_bnc_ret_100 = 0;
        s_bnc_ret_bp = 0;
        s_bnc_ret_vb = 0;
        s_bnc_ret_trame = 0;
        s_bnc_ph_n = 0;
        s_bnc_ph_min = 0;
        s_bnc_ph_max = 0;
        s_bnc_ph_somme = 0;
        s_bnc_ph_10pc = 0;
        s_bnc_ph_25pc = 0;
        s_bnc_ph_50pc = 0;
        s_bnc_ph_100pc = 0;
        s_bnc_ph_deficit_max = 0;
        s_bnc_ph_ecarte = 0;
        s_bnc_ph_ref_us = 0;
        s_bnc_ph_ref_seed = 0;
        s_bnc_ph_rejete = 0;
        s_bnc_ph_doubles_ec = 0;
        s_bnc_ph_dechire = 0;
    } else {
        /* (a) comptabilite des enroulements : `wraps` doit suivre `trames` UN
         *     pour UN. La soustraction non signee absorbe l'enroulement 32 bits. */
        uint32_t w = s_bnc_wraps;
        uint32_t n = w - s_bnc_wraps_vus;
        s_bnc_wraps_vus = w;
        if (n == 0) {
            s_bnc_manques++;
        } else if (n >= 2) {
            s_bnc_doubles++;
        }

        /* (a bis) LA PHASE — le retard ABSOLU de CETTE ISR. Seulement quand un
         * enroulement a bien eu lieu dans la trame : sinon l'horodatage de
         * reference appartient a une trame anterieure et la phase mesurerait
         * une periode entiere de plus. */
        /* 🔴 `n == 1`, ⛔ PLUS `n >= 1` — corrige le 2026-08-27 (revue).
         *    A DEUX enroulements dans la trame, `s_bnc_t_wrap_us` est celui du
         *    SECOND : la phase mesuree est tres courte, donc le deficit est
         *    MAXIMAL, donc `ph_100pc++`. Une corruption FABRIQUEE par la
         *    comptabilite. Ces trames sont desormais ECARTEES et COMPTEES
         *    (`ph_doubles_ec`), en regard de `doubles` qui existait deja mais
         *    qu'aucune sortie ne croisait avec la phase. */
        if (n == 1) {
            /* ⚠️ GARDE DE DECHIRURE SUR LA PAIRE (wraps, t_wrap) — posee le
             *    2026-08-27 apres verification PAR LECTURE de l'IDF. L'invariant
             *    du fichier disait « les deux ISR sont sur le meme coeur au meme
             *    niveau de priorite, donc elles ne se preemptent pas » : cette
             *    affirmation N'EST PAS GARANTIE PAR CONSTRUCTION. `on_vsync` est
             *    servi par `rgb_lcd_default_isr_handler` (esp_lcd_panel_rgb.c:1247,
             *    alloue :362 avec `ESP_INTR_FLAG_LOWMED | ESP_INTR_FLAG_SHARED`)
             *    et `on_frame_buf_complete` par `lcd_rgb_panel_eof_handler`
             *    (:948, callback GDMA enregistre :1029, alloue dans gdma.c:962
             *    avec les MEMES drapeaux). `ESP_INTR_FLAG_LOWMED` = niveaux
             *    1|2|3, et l'allocateur choisit le vecteur LIBRE le mieux place
             *    (intr_alloc.c:395-425) : RIEN n'impose aux deux le meme niveau.
             *    A niveaux differents, l'ISR d'enroulement PEUT preempter celle
             *    de vsync entre les deux stores l.373-374 — et on lirait alors
             *    l'horodatage d'un enroulement avec le compte d'un autre.
             * ⇒ On relit `s_bnc_wraps` APRES l'horodatage. S'il a bouge, la
             *   paire est incoherente : on jette l'echantillon et ON LE COMPTE.
             *   Cout : deux chargements et une comparaison, 37,40 fois par
             *   seconde. ⛔ On ne prend pas de verrou sur le chemin qu'on mesure. */
            uint32_t tw = s_bnc_t_wrap_us;
            uint32_t w2 = s_bnc_wraps;
            if (w2 != w) {
                s_bnc_ph_dechire++;
            } else {
                uint32_t ph = t_us - tw;
                if (ph >= 2u * DN_PERIODE_US) {
                    /* 🔴 LA BORNE DE SANITE ECARTE EXACTEMENT LE GLISSEMENT
                     *    RECHERCHE — et jusqu'au 2026-08-27 elle le jetait SANS
                     *    RIEN INCREMENTER. Un « 0 » de la console pouvait donc
                     *    vouloir dire « aucun retard » OU « des retards trop gros
                     *    pour l'instrument », sans qu'on puisse les distinguer. */
                    s_bnc_ph_rejete++;
                } else if (s_bnc_ph_ecarte < DN_PHASE_DEGROSSI) {
                    /* Degrossissage : on etablit la REFERENCE (la phase « a
                     * l'heure »), on ne compte pas. ⛔ Et on ne touche NI
                     * `ph_min` NI `ph_max` : ces deux-la portent desormais sur
                     * LA MEME population que `moy`, ce qui n'etait pas le cas
                     * avant le 2026-08-27 (les 32 trames de degrossissage
                     * entraient dans min/MAX mais pas dans somme/n, et la ligne
                     * console presentait les trois comme issues du meme `n`). */
                    if (ph > s_bnc_ph_ref_seed) {
                        s_bnc_ph_ref_seed = ph;
                    }
                    s_bnc_ph_ecarte++;
                    if (s_bnc_ph_ecarte == DN_PHASE_DEGROSSI) {
                        s_bnc_ph_ref_us = s_bnc_ph_ref_seed; /* FIGEE ici, et plus touchee */
                    }
                } else {
                    if (s_bnc_ph_n == 0 || ph < s_bnc_ph_min) {
                        s_bnc_ph_min = ph;
                    }
                    if (ph > s_bnc_ph_max) {
                        s_bnc_ph_max = ph;
                    }
                    s_bnc_ph_somme += ph;
                    s_bnc_ph_n++;
                    /* LE DEFICIT : de combien cette trame est-elle EN DESSOUS de
                     * la phase a l'heure. Zero si elle est au-dessus.
                     * ⛔ Contre la REFERENCE FIGEE, plus contre un max courant. */
                    uint32_t ref = s_bnc_ph_ref_us;
                    uint32_t deficit = (ph < ref) ? (ref - ph) : 0u;
                    if (deficit > s_bnc_ph_deficit_max) {
                        s_bnc_ph_deficit_max = deficit;
                    }
                    uint32_t d = s_bnc_t_demi_us;
                    if (d > 0u) {
                        /* ⚠️ LES QUATRE SEAUX SONT EMBOITES, ⛔ PAS DISJOINTS :
                         *    un deficit > 100 % incremente AUSSI 50, 25 et 10 %.
                         *    La console le dit desormais — un lecteur qui les
                         *    sommait comptait les pires JUSQU'A QUATRE FOIS. */
                        if (deficit * 10u > d) {
                            s_bnc_ph_10pc++;
                        }
                        if (deficit * 4u > d) {
                            s_bnc_ph_25pc++;
                        }
                        if (deficit * 2u > d) {
                            s_bnc_ph_50pc++;
                        }
                        if (deficit > d) {
                            s_bnc_ph_100pc++;
                        }
                    }
                }
            }
        } else if (n >= 2) {
            s_bnc_ph_doubles_ec++;
        }

        /* (b) LA GIGUE. `fps` moyenne 561 trames et efface exactement ca. */
        if (s_bnc_arme) {
            uint32_t dt = t_us - s_bnc_t_vsync_us;
            s_bnc_inter_n++;
            if (s_bnc_inter_min == 0 || dt < s_bnc_inter_min) {
                s_bnc_inter_min = dt;
            }
            if (dt > s_bnc_inter_max) {
                s_bnc_inter_max = dt;
            }
            s_bnc_inter_somme += dt;
            if (dt > DN_PERIODE_US + 100u) {
                s_bnc_ret_100++;
            }
            if (dt > DN_PERIODE_US + DN_BACK_PORCH_US) {
                s_bnc_ret_bp++;
            }
            if (dt > DN_PERIODE_US + DN_VBLANK_US) {
                s_bnc_ret_vb++;
            }
            if (dt > 2u * DN_PERIODE_US) {
                s_bnc_ret_trame++;
            }
        }
        s_bnc_t_vsync_us = t_us;
        s_bnc_arme = true;
    }

    BaseType_t hp = pdFALSE;
    if (s_vsync_sem) {
        xSemaphoreGiveFromISR(s_vsync_sem, &hp);
    }
    /* Chaque abonné reçoit SON jeton. Pas de boucle non bornée, pas
     * d'allocation, pas de log : on est sous ISR, cache potentiellement
     * désactivé. `xSemaphoreGiveFromISR` est en IRAM par défaut dans ESP-IDF. */
    int n = s_vsync_subs_n;
    for (int i = 0; i < n; i++) {
        if (s_vsync_subs[i]) {
            BaseType_t hp_i = pdFALSE;
            xSemaphoreGiveFromISR(s_vsync_subs[i], &hp_i);
            if (hp_i == pdTRUE) {
                hp = pdTRUE;
            }
        }
    }
    return hp == pdTRUE; /* true => réveiller une tâche de plus haute priorité */
}

/* ⚠️ Nom trompeur sur l'ESP32-S3 : ce qui nous appelle ici, c'est
 *    `lcd_rgb_panel_eof_handler()` sur le trans-EOF de la DMA — pas la bascule
 *    de lien GDMA qui, elle, donnerait vraiment « le tampon est libéré ». Voir
 *    le commentaire de `s_fbdone_sem` ci-dessus. */
static IRAM_ATTR bool on_frame_buf_complete(esp_lcd_panel_handle_t panel,
                                            const esp_lcd_rgb_panel_event_data_t *edata,
                                            void *user_ctx)
{
    (void)panel;
    (void)edata;
    (void)user_ctx;
    /* dn4-10 : les DEUX SEULES variables que cette ISR-ci ecrit. En mode bounce
     * buffer (`bounce_px != 0`, notre cas depuis le 2026-08-16) cet evenement
     * tombe UNE FOIS PAR TRAME, a l'enroulement de `bounce_pos_px` — voir
     * l'amendement du 2026-08-22 dans dn_measure.h. */
    s_bnc_wraps++;
    s_bnc_t_wrap_us = (uint32_t)esp_timer_get_time();

    BaseType_t hp = pdFALSE;
    if (s_fbdone_sem) {
        xSemaphoreGiveFromISR(s_fbdone_sem, &hp);
    }
    return hp == pdTRUE;
}

void dn_measure_arm_frame_done(void)
{
    if (!s_fbdone_sem) {
        return;
    }
    /* Vider AVANT la bascule, JAMAIS après : après, on jette l'événement que la
     * bascule vient elle-même de provoquer, et l'attente qui suit part pour une
     * trame de plus ou expire. Symptôme observé côté mesure : une latence
     * supplémentaire non déterministe sur les modes synchronisés. */
    xSemaphoreTake(s_fbdone_sem, 0);
}

bool dn_measure_wait_frame_done(uint32_t timeout_ms)
{
    if (!s_fbdone_sem) {
        return false;
    }
    /* AUCUN vidage ici, et c'est le correctif : c'est
     * `dn_measure_arm_frame_done()`, appelé avant `dn_display_present()`, qui
     * s'en charge. Ne pas « symétriser » avec `dn_measure_wait_vsync()`
     * ci-dessous : les deux besoins sont opposés (voir dn_measure.h). */
    return xSemaphoreTake(s_fbdone_sem, pdMS_TO_TICKS(timeout_ms)) == pdTRUE;
}

bool dn_measure_wait_vsync(uint32_t timeout_ms)
{
    if (!s_vsync_sem) {
        return false;
    }
    /* On vide d'abord le sémaphore : sinon on repartirait sur un VSYNC déjà
     * passé, et la bascule tomberait au milieu du balayage — exactement ce
     * qu'on cherche à éviter.
     * ⚠️ Ce vidage-ci est CORRECT et doit rester où il est : on veut le
     *    PROCHAIN retour vertical, et aucun appelant ne provoque le VSYNC. Ce
     *    n'est pas le cas de `wait_frame_done`, dont l'appelant provoque
     *    lui-même l'événement — d'où l'armement séparé, plus haut. */
    xSemaphoreTake(s_vsync_sem, 0);
    return xSemaphoreTake(s_vsync_sem, pdMS_TO_TICKS(timeout_ms)) == pdTRUE;
}

dn_vsync_sub_t dn_measure_vsync_subscribe(const char *nom)
{
    if (s_vsync_subs_n >= DN_VSYNC_SUBS_MAX) {
        ESP_LOGE(TAG,
                 "abonnement vsync « %s » REFUSÉ : les %d slots sont pris. "
                 "Aucun repli silencieux — un abonné qui partagerait le "
                 "sémaphore d'un autre lui volerait ses événements.",
                 nom ? nom : "?", DN_VSYNC_SUBS_MAX);
        return -1;
    }
    SemaphoreHandle_t sem = xSemaphoreCreateBinary();
    if (!sem) {
        ESP_LOGE(TAG, "abonnement vsync « %s » : sémaphore non alloué",
                 nom ? nom : "?");
        return -1;
    }
    int slot = s_vsync_subs_n;
    s_vsync_subs[slot] = sem;
    s_vsync_subs_nom[slot] = nom;
    /* Publié EN DERNIER : l'ISR lit `s_vsync_subs_n` pour borner sa boucle, donc
     * le sémaphore doit déjà être en place quand le compteur l'inclut. */
    s_vsync_subs_n = slot + 1;
    ESP_LOGI(TAG, "abonnement vsync #%d : « %s »", slot, nom ? nom : "?");
    return slot;
}

void dn_measure_vsync_flush(dn_vsync_sub_t sub)
{
    if (sub < 0 || sub >= s_vsync_subs_n || !s_vsync_subs[sub]) {
        return;
    }
    xSemaphoreTake(s_vsync_subs[sub], 0);
}

bool dn_measure_vsync_wait(dn_vsync_sub_t sub, uint32_t timeout_ms)
{
    if (sub < 0 || sub >= s_vsync_subs_n || !s_vsync_subs[sub]) {
        return false;
    }
    return xSemaphoreTake(s_vsync_subs[sub], pdMS_TO_TICKS(timeout_ms)) == pdTRUE;
}

esp_err_t dn_measure_attach(esp_lcd_panel_handle_t panel)
{
    s_vsync_sem = xSemaphoreCreateBinary();
    s_fbdone_sem = xSemaphoreCreateBinary();
    ESP_RETURN_ON_FALSE(s_vsync_sem && s_fbdone_sem, ESP_ERR_NO_MEM, TAG,
                        "sémaphores vsync/frame_buf non alloués");
    esp_lcd_rgb_panel_event_callbacks_t cbs = {
        .on_vsync = on_vsync,
        .on_frame_buf_complete = on_frame_buf_complete,
    };
    /*
     * ⚠️ CE MODULE EST LE POINT D'ENREGISTREMENT UNIQUE — et « unique » est le
     *    mot important. `esp_lcd_rgb_panel_register_event_callbacks()` ne fusionne
     *    RIEN : il ASSIGNE les quatre pointeurs et `user_ctx`
     *    (esp_lcd_panel_rgb.c:444-448). Le dernier appelant efface le précédent,
     *    en silence, et rend ESP_OK.
     *
     *    Or `lvgl_port_add_disp_rgb()` enregistre lui aussi `on_vsync`
     *    (esp_lvgl_port_disp.c:219, inconditionnel). Les deux sont donc en
     *    collision directe. Le choix de dn1-3, écrit ici pour qu'on ne le
     *    « corrige » pas plus tard :
     *      -> dn_measure_attach() est appelé APRÈS lvgl_port_add_disp_rgb(),
     *         et gagne. Le callback du portage n'alimente qu'un sémaphore que le
     *         portage n'attend QUE dans ses modes direct/full — modes qu'on
     *         n'utilise pas (rendu PARTIEL, num_fbs=1). Le perdre ne coûte rien.
     *      -> la synchronisation du flush passe par un abonnement vsync de
     *         dn_measure (dn_ui.c), pas par la mécanique interne du portage.
     *
     *    Si l'ordre s'inversait un jour, le symptôme serait MUET : `fps` et
     *    l'abonnement vsync compteraient 0, la mesure de déchirement mesurerait
     *    du vide — exactement le genre de défaut silencieux que dn1-2 a payé
     *    cher. D'où le contrôle actif ci-dessous, au boot.
     */
    /* dn4-10 : la duree d'ecoulement d'un DEMI-BOUNCE, posee une fois. C'est le
     * seuil au-dela duquel la DMA a forcement lu un tampon pas encore rempli.
     * Lue depuis le panneau REELLEMENT monte, ⛔ pas depuis la NVS : un `set`
     * sans `reboot` ne change pas le materiel.
     * 🔴 POSEE **AVANT** L'ENREGISTREMENT DES CALLBACKS — corrige le 2026-08-27
     *    (revue de code). Elle etait posee APRES. Or le panneau BALAIE DEJA
     *    quand `dn_measure_attach()` s'execute (desknode_main.c, etape 5, la
     *    dalle tourne depuis l'etape 2) : toute trame qui tombait entre
     *    l'enregistrement et cette affectation etait traitee avec `d == 0`,
     *    donc SANS AUCUN SEUIL, EN SILENCE. Deux lignes inversees, et la
     *    fenetre disparait : quand la premiere ISR arrive, le seuil est deja la. */
    s_bnc_t_demi_us = DN_US_POUR_LIGNES(dn_display_bounce_px() / DN_LCD_H_RES);
    ESP_RETURN_ON_ERROR(
        esp_lcd_rgb_panel_register_event_callbacks(panel, &cbs, NULL), TAG,
        "branchement du callback vsync refusé");
    ESP_LOGI(TAG,
             "dn4-10 : seuil de corruption = %lu us (ecoulement d'un demi-bounce "
             "de %u px, soit %u ligne(s))",
             (unsigned long)s_bnc_t_demi_us, (unsigned)dn_display_bounce_px(),
             (unsigned)(dn_display_bounce_px() / DN_LCD_H_RES));
    if (s_bnc_t_demi_us == 0u) {
        /* 🔴 LE COMPTEUR DECORATIF QUE CE DEPOT TRAQUE — ferme le 2026-08-27.
         *    `bounce_px = 0` est une valeur LEGALE (`bounce_px_refus()` l'accepte,
         *    dn_bootcfg.c : `v != 0 && ...`), et tout `bounce_px < 480` donne
         *    `0 / 480 = 0` donc `t_demi_us = 0` donc l'ISR saute TOUT le bloc de
         *    seuils (`if (d > 0u)`). Les quatre compteurs restaient a zero et la
         *    console imprimait « 🔴 100 % (CORRUPTION) 0 » : quatre zeros qui se
         *    lisent « aucune corruption » alors que RIEN n'a ete mesure.
         *    ⇒ On le CRIE au boot, et `flush` refuse desormais d'imprimer la
         *      ligne des quatre seuils dans cet etat. */
        ESP_LOGE(TAG,
                 "🔴 SEUILS DE CORRUPTION DESARMES : bounce_px=%u px (< %d px = "
                 "une ligne) ⇒ demi-bounce = 0 us ⇒ les quatre compteurs de "
                 "deficit NE MESURENT RIEN.",
                 (unsigned)dn_display_bounce_px(), DN_LCD_H_RES);
        ESP_LOGE(TAG,
                 "   ⛔ Un « 0 » de `flush` ne voudra PAS dire « aucune "
                 "corruption » : il voudra dire « aucune mesure ». `set bounce "
                 "%d` puis `reboot` pour rearmer l'instrument.",
                 dn_bootcfg_defaut_bounce_px());
    }
    ESP_LOGI(TAG, "compteur vsync branché (ISR en IRAM, compteur en RAM interne)");
    ESP_LOGI(TAG,
             "  ⚠️ enregistrement EXCLUSIF : il vient d'écraser tout callback "
             "posé avant lui (esp_lcd rgb ASSIGNE, ne fusionne pas). C'est "
             "voulu — voir le commentaire au-dessus.");
    return ESP_OK;
}

uint32_t dn_measure_vsync_count(void) { return s_vsync_count; }

bool dn_measure_vsync_alive(uint32_t ms)
{
    uint32_t c0 = s_vsync_count;
    vTaskDelay(pdMS_TO_TICKS(ms));
    uint32_t vues = s_vsync_count - c0; /* non signé : l'enroulement se gère seul */
    if (vues == 0) {
        ESP_LOGE(TAG,
                 "TÉMOIN VSYNC MORT : 0 trame comptée en %lu ms (~%.1f "
                 "attendues). Le callback a été DÉBRANCHÉ par un "
                 "enregistrement ultérieur, ou le panneau ne tourne pas.",
                 (unsigned long)ms, (double)ms / 1000.0 * DN_FPS_THEORIQUE);
        ESP_LOGE(TAG,
                 "  => toute mesure faite maintenant (fps, déchirement, "
                 "cadence) porterait une étiquette FAUSSE. Ne rien conclure.");
        return false;
    }
    ESP_LOGI(TAG, "témoin vsync : %lu trames en %lu ms — le compteur est vivant",
             (unsigned long)vues, (unsigned long)ms);
    return true;
}

double dn_measure_fps(int seconds, uint32_t *out_frames, int64_t *out_elapsed_us)
{
    if (seconds < 1) {
        seconds = 1;
    }
    uint32_t c0 = s_vsync_count;
    int64_t t0 = esp_timer_get_time();
    vTaskDelay(pdMS_TO_TICKS(seconds * 1000));
    uint32_t c1 = s_vsync_count;
    int64_t t1 = esp_timer_get_time();

    uint32_t frames = c1 - c0; /* non signé : l'enroulement se gère tout seul */
    int64_t elapsed = t1 - t0;
    if (out_frames) {
        *out_frames = frames;
    }
    if (out_elapsed_us) {
        *out_elapsed_us = elapsed;
    }
    if (elapsed <= 0) {
        return 0.0;
    }
    return (double)frames * 1000000.0 / (double)elapsed;
}

uint32_t dn_measure_periode_us(void) { return DN_PERIODE_US; }
uint32_t dn_measure_back_porch_us(void) { return DN_BACK_PORCH_US; }
uint32_t dn_measure_vblank_us(void) { return DN_VBLANK_US; }

void dn_measure_bounce_reset(void)
{
    /* On ne touche AUCUN compteur ici — voir l'invariant en tete de fichier.
     * L'ISR de vsync consomme le drapeau au prochain retour vertical. */
    /* ⚠️ L'ANCRE EST POSEE AVANT LE DRAPEAU, et l'ordre compte (dn4-5/AC1.2) :
     *    dans l'autre sens, l'ISR pourrait consommer la RAZ avant que l'ancre
     *    n'existe, et la reconstruction 64 bits s'appuierait sur l'ancre de la
     *    RAZ PRECEDENTE — soit une fenetre fausse d'un multiple de 71,58 min,
     *    c'est-a-dire le defaut qu'on est en train de fermer. */
    s_bnc_arme_us64 = esp_timer_get_time();
    s_bnc_raz = true;
}

void dn_measure_bounce_get(dn_bounce_stats_t *out)
{
    if (!out) {
        return;
    }
    /*
     * 🔴 L'INSTANTANE EST DESORMAIS GARDE — corrige le 2026-08-27 (revue de code).
     *
     * ⛔ CE QUI ETAIT ECRIT ICI, ET QUI ETAIT FAUX : « une incoherence porterait
     *    sur UNE trame ». C'est vrai des compteurs 32 bits ; ce l'est PAS des
     *    deux sommes 64 bits, lues en DEUX MOTS sur un CPU 32 bits. Une retenue
     *    qui tombe entre les deux mots decale la somme de 2^32 us — pas d'une
     *    trame. Franchissement a ~71 min pour `inter_somme` (elle cumule ~26 738
     *    us par trame a 37,40 trames/s) et ~16 h pour `ph_somme`. Et l'en-tete
     *    promettait « Instantane coherent » pendant que ce commentaire-ci
     *    declarait le contraire : DEUX TEXTES NORMATIFS EN DESACCORD.
     *
     * ⛔ ET UN SECOND CHEMIN, PIRE PARCE QU'IL SORT UN CHIFFRE ABSURDE : si l'ISR
     *    consomme la RAZ ENTRE le chargement de `s_vsync_count` et celui de
     *    `s_bnc_base_vsync`, la base devient PLUS GRANDE que le compte et la
     *    soustraction non signee rend ~4,29 x 10^9 trames. Il suffisait de taper
     *    `flush` dans les <= 27 ms qui suivent `flush reset`.
     *
     * 🎯 LA PARADE, ET ELLE NE PREND AUCUN VERROU : `s_bnc_raz_gen` (pose par
     *    dn4-5) est deja incremente a CHAQUE RAZ consommee. On l'encadre — un
     *    seqlock de pauvre, cote lecteur seulement. Si la generation a bouge
     *    pendant la copie, on recommence ; au-dela de trois essais on PUBLIE LE
     *    DRAPEAU plutot que de boucler sur le chemin qu'on mesure. Les deux
     *    sommes 64 bits sont lues deux fois et comparees : elles ne peuvent pas
     *    se dechirer IDENTIQUEMENT deux fois de suite (la retenue de bit 32 tombe
     *    une fois par 71 min, la relecture est a quelques ns).
     * ⛔ TOUT EST DU COTE DE LA TACHE CONSOLE. L'ISR n'a pas gagne une seule
     *    instruction, et l'invariant « aucun verrou sur le chemin chaud » tient.
     */
    int64_t maintenant = 0;
    uint32_t t_us = 0;
    uint32_t gen = 0, gen_fin = 0;
    bool sommes_stables = true;
    for (int essai = 0; essai < 3; essai++) {
        sommes_stables = true;
        gen = s_bnc_raz_gen;
        /* UNE SEULE lecture d'horloge, deux vues : la vue 64 bits (juste) et la
         * vue 32 bits (celle de l'instrument d'avant dn4-5, publiee comme
         * contre-epreuve). Les derivees d'une meme lecture, elles sont forcement
         * coherentes entre elles — deux appels ne le seraient pas. */
        maintenant = esp_timer_get_time();
        t_us = (uint32_t)maintenant;
        uint32_t base_vsync = s_bnc_base_vsync;
        uint32_t base_wraps = s_bnc_base_wraps;
        out->trames = s_vsync_count - base_vsync;
        out->wraps = s_bnc_wraps - base_wraps;
        out->manques = s_bnc_manques;
        out->doubles = s_bnc_doubles;
        out->intervalles = s_bnc_inter_n;
        out->inter_min_us = s_bnc_inter_min;
        out->inter_max_us = s_bnc_inter_max;
        {
            uint64_t a = s_bnc_inter_somme;
            uint64_t b = s_bnc_inter_somme;
            if (a != b) {
                sommes_stables = false;
            }
            out->inter_somme_us = b;
        }
        out->retards_100 = s_bnc_ret_100;
        out->retards_bp = s_bnc_ret_bp;
        out->retards_vb = s_bnc_ret_vb;
        out->retards_trame = s_bnc_ret_trame;
        /* 🔴 `ph_n` EST DESORMAIS LE COMPTE DIRECT DES ECHANTILLONS COMPTES.
         *    Avant le 2026-08-27, `s_bnc_ph_n` cumulait degrossissage ET
         *    population comptee, et on soustrayait ici. Les deux compteurs sont
         *    maintenant DISJOINTS dans l'ISR : plus de soustraction, plus de
         *    plancher a zero pour rattraper une soustraction qui pourrait passer
         *    sous zero pendant une RAZ. */
        out->ph_n = s_bnc_ph_n;
        out->ph_ecarte = s_bnc_ph_ecarte;
        out->ph_rejete = s_bnc_ph_rejete;
        out->ph_doubles_ecartes = s_bnc_ph_doubles_ec;
        out->ph_dechire = s_bnc_ph_dechire;
        out->ph_min_us = s_bnc_ph_min;
        out->ph_max_us = s_bnc_ph_max;
        out->ph_ref_us = s_bnc_ph_ref_us;
        {
            uint64_t a = s_bnc_ph_somme;
            uint64_t b = s_bnc_ph_somme;
            if (a != b) {
                sommes_stables = false;
            }
            out->ph_somme_us = b;
        }
        out->ph_10pc = s_bnc_ph_10pc;
        out->ph_25pc = s_bnc_ph_25pc;
        out->ph_50pc = s_bnc_ph_50pc;
        out->ph_100pc = s_bnc_ph_100pc;
        out->ph_deficit_max_us = s_bnc_ph_deficit_max;
        out->t_demi_us = s_bnc_t_demi_us;
        out->us_par_ligne = DN_US_PAR_LIGNE;
        out->periode_ns = DN_PERIODE_NS;
        gen_fin = s_bnc_raz_gen;
        if (gen == gen_fin && sommes_stables) {
            break;
        }
    }
    /* ⛔ ON NE TAIT PAS L'ECHEC : trois essais qui n'ont pas convergé veulent
     *    dire que la RAZ est tombee en plein dedans, ou qu'une somme se dechire
     *    a repetition. Le bloc reste imprime — mais il est ETIQUETE. */
    out->lecture_dechiree = (gen != gen_fin) || !sommes_stables;
    /* ── dn4-5 / AC1.2 : LA FENETRE, RECONSTRUITE SUR 64 BITS ───────────── */
    /* ⚠️ C'est la generation la PLUS RECENTE qui fait foi ici : si la boucle
     *    ci-dessus n'a pas converge, `gen_fin` est la seule valeur dont on
     *    sache qu'elle a ete lue APRES la copie. */
    gen = gen_fin;
    if (gen != s_bnc_raz_gen_vu) {
        /* Une origine NEUVE a ete posee par l'ISR depuis notre derniere
         * lecture : on la releve sur 64 bits, ancree sur l'ARMEMENT. */
        s_bnc_raz_gen_vu = gen;
        int64_t cand = (s_bnc_arme_us64 & ~0xFFFFFFFFLL) | (int64_t)s_bnc_t0_us;
        if (cand < s_bnc_arme_us64) {
            /* l'ISR a franchi l'enroulement 32 bits entre l'armement et la
             * consommation : les bits hauts sont ceux de l'armement + 1. */
            cand += 0x100000000LL;
        }
        s_bnc_t0_us64 = cand;
    }
    int64_t fen_us = maintenant - s_bnc_t0_us64;
    if (fen_us < 0) {
        /* Injoignable par construction ; on ne publie pas un negatif plutot que
         * de le convertir en un enorme non signe. */
        fen_us = 0;
    }
    out->fenetre_ms = (uint64_t)fen_us / 1000u;
    /* LE CRI, ET IL PORTE SA PROPRE CONTRE-EPREUVE : au-dela de 2^32 us
     * l'instrument d'avant dn4-5 publiait une fenetre fausse modulo 71,58 min.
     * On publie CE QU'IL AURAIT DIT a cote de la valeur juste, pour que la
     * sortie se suffise a elle-meme et que l'ecart soit LU, pas deduit. */
    out->fenetre_deborde = (fen_us >= 4294967296LL);
    out->fenetre_ms_32 = (t_us - s_bnc_t0_us) / 1000u;
    out->raz_en_attente = s_bnc_raz;
}

size_t dn_measure_psram_free(void)
{
    return heap_caps_get_free_size(MALLOC_CAP_SPIRAM);
}

size_t dn_measure_internal_free(void)
{
    return heap_caps_get_free_size(MALLOC_CAP_INTERNAL);
}

void dn_measure_note_psram(size_t avant, size_t apres)
{
    s_psram_avant = avant;
    s_psram_apres = apres;
}

void dn_measure_get_psram_note(size_t *avant, size_t *apres)
{
    if (avant) {
        *avant = s_psram_avant;
    }
    if (apres) {
        *apres = s_psram_apres;
    }
}

void dn_measure_report_fps(const char *etiquette, int seconds)
{
    uint32_t frames = 0;
    int64_t elapsed = 0;

    ESP_LOGI(TAG, "[%s] mesure fps en cours sur %d s…", etiquette, seconds);
    double fps = dn_measure_fps(seconds, &frames, &elapsed);
    double theo = DN_FPS_THEORIQUE;
    double ecart = theo > 0.0 ? (fps - theo) / theo * 100.0 : 0.0;

    /* Le calcul est RÉÉCRIT dans la trace : AC4 exige que la mesure se
     * confronte à la théorie sans qu'on ait à ouvrir un autre document. */
    ESP_LOGI(TAG, "[%s] --- fps ---------------------------------------", etiquette);
    ESP_LOGI(TAG, "[%s]   trames comptées : %lu en %lld us", etiquette,
             (unsigned long)frames, (long long)elapsed);
    ESP_LOGI(TAG, "[%s]   fps MESURÉ      : %.2f Hz", etiquette, fps);
    ESP_LOGI(TAG,
             "[%s]   fps THÉORIQUE   : %.2f Hz  = pclk / (htotal x vtotal)",
             etiquette, theo);
    ESP_LOGI(TAG,
             "[%s]                     = %d / ((%d+%d+%d+%d) x (%d+%d+%d+%d))",
             etiquette, DN_PCLK_HZ, DN_LCD_H_RES, DN_HSYNC_PULSE,
             DN_HSYNC_BACK_PORCH, DN_HSYNC_FRONT_PORCH, DN_LCD_V_RES,
             DN_VSYNC_PULSE, DN_VSYNC_BACK_PORCH, DN_VSYNC_FRONT_PORCH);
    ESP_LOGI(TAG, "[%s]                     = %d / (%d x %d) = %d px/trame",
             etiquette, DN_PCLK_HZ,
             DN_LCD_H_RES + DN_HSYNC_PULSE + DN_HSYNC_BACK_PORCH +
                 DN_HSYNC_FRONT_PORCH,
             DN_LCD_V_RES + DN_VSYNC_PULSE + DN_VSYNC_BACK_PORCH +
                 DN_VSYNC_FRONT_PORCH,
             (DN_LCD_H_RES + DN_HSYNC_PULSE + DN_HSYNC_BACK_PORCH +
              DN_HSYNC_FRONT_PORCH) *
                 (DN_LCD_V_RES + DN_VSYNC_PULSE + DN_VSYNC_BACK_PORCH +
                  DN_VSYNC_FRONT_PORCH));
    ESP_LOGI(TAG, "[%s]   ÉCART           : %+.2f %% %s", etiquette, ecart,
             fabs(ecart) > 5.0 ? "<<< AU-DELÀ DES 5 % : à expliquer par une "
                                 "cause OBSERVÉE, pas par une hypothèse"
                               : "(dans les 5 %)");
    ESP_LOGI(TAG,
             "[%s]   rappel : un compteur vsync tourne MÊME écran noir. Ce "
             "chiffre qualifie le pipeline, pas l'image.",
             etiquette);
    ESP_LOGI(TAG, "[%s] ------------------------------------------------", etiquette);
}

#include "dn_bootcfg.h"

#include "dn_display.h"
#include "dn_pins.h"
#include "dn_ui.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "nvs.h"
#include "nvs_flash.h"

static const char *TAG = "dn_cfg";

#define DN_NVS_NAMESPACE "desknode"
#define DN_KEY_NUM_FBS "num_fbs"
#define DN_KEY_BOUNCE "bounce_px"
#define DN_KEY_DRAW_LINES "draw_lines"
#define DN_KEY_DRAW_PSRAM "draw_psram"
#define DN_KEY_LVGL_CORE "lvgl_core"
/* ── Le TEMOIN DE REPLI (decision owner du 2026-08-27) ──────────────────────
 * ⚠️ Les cles NVS sont bornees a 15 caracteres : ces trois-la tiennent.
 * ⛔ Elles ne sont PAS de la configuration de boot : `dn_bootcfg_load()` ne les
 *    lit pas, et `bootcfg_t` ne les porte pas. Ce sont des TRACES. */
#define DN_KEY_REPLI_DEM "repli_dem"
#define DN_KEY_REPLI_RET "repli_ret"
#define DN_KEY_REPLI_N   "repli_n"

/*
 * Défauts = LA CONFIGURATION DE RÉFÉRENCE retenue par la story dn1-2, pour
 * qu'un clone neuf démarre dessus sans rien régler.
 *
 *   num_fbs = 1   : ARBITRÉ le 2026-08-15, après mesure — et c'est un
 *                   RENVERSEMENT du défaut d'origine, qui valait 2.
 *                   Le double tampon est IMPOSSIBLE sur cette puce tant que
 *                   CONFIG_LCD_RGB_RESTART_IN_VSYNC est activé — et il l'est,
 *                   parce que sans lui l'image reste décalée en permanence.
 *                   🔴 AMENDE LE 2026-08-24 : « ET IL L'EST » EST FAUX depuis
 *                   `4734d07` — le symbole vaut `n`. ⛔ Le raisonnement au-dessus
 *                   RESTE VRAI et n'est pas efface : c'est bien pourquoi `num_fbs`
 *                   est reste a 1 quand `y` etait livre. ⚠️ Ce qui n'est PAS
 *                   retabli pour autant : `num_fbs = 2` n'a pas ete re-mesure a
 *                   `n`, donc rien n'autorise a le rouvrir sans mesure.
 *                   Mécanisme : RGB_LCD_NEEDS_SEPARATE_RESTART_LINK vaut 1 sur
 *                   S3, `dma_restart_link` est soudé à `dma_fb_links[0]` une
 *                   seule fois à l'init (esp_lcd_panel_rgb.c:1135) et jamais
 *                   re-pointé, alors que la relance par VBlank repart toujours
 *                   de là. Conséquence MESURÉE : la dalle n'affichait jamais
 *                   fb[0], une présentation sur deux était perdue EN SILENCE
 *                   (draw_bitmap rendait ESP_OK), et les 614 400 o du second
 *                   framebuffer étaient payés pour rien.
 *                   ⇒ Repasser à 1 récupère 614 312 o de PSRAM (mesuré) et
 *                   rend TOUTES les présentations visibles. Vérifié à l'œil.
 *                   ⚠️ Ce n'est PAS un renoncement définitif au double tampon :
 *                   la piste d'un recalage déclenché sur l'événement de bascule
 *                   effective reste ouverte, et dn1-3 en a besoin. Détail et
 *                   les 6 parades déjà éliminées : §4 bis du fichier hardware/.
 *   bounce  = 0   : le bounce buffer a été ÉLIMINÉ, avec deux symptômes.
 *                   Avec CONFIG_LCD_RGB_ISR_IRAM_SAFE=y il provoque un
 *                   redémarrage watchdog (`rst:0x8 TG1WDT_SYS_RST`) dès la
 *                   première seconde d'écriture flash ; sans lui, l'image
 *                   défile ET garde un décalage VERTICAL permanent que
 *                   esp_lcd_rgb_panel_restart() ne rattrape pas.
 *   draw_lines = 64 : hauteur du draw buffer LVGL. 480 x 64 x 2 = 61 440 o.
 *                   C'est EXACTEMENT la recommandation d'esp_lvgl_port (« au
 *                   moins 1/10 d'écran » : 307 200 / 10 = 30 720 px = 64 lignes).
 *                   ⚠️ C'était un POINT DE DÉPART ; l'A/B a été JOUÉ le
 *                   2026-08-15 (32 / 64 / 128 lignes, même redessin de
 *                   323 092 px). Ce qui l'arbitre n'est pas la copie — constante
 *                   à ±9 % pour un nombre de flushes qui varie d'un facteur
 *                   3,7 — mais deux choses :
 *                     · le régime PRODUIT (label 1 Hz) tient en UN SEUL flush à
 *                       64 lignes : 15 892 px, soit 5,17 % de l'écran ;
 *                     · l'attente de synchro d'un plein écran vaut 640/lignes
 *                       trames : 433 ms à 32 lignes, 176 ms à 64, 67 ms à 128.
 *                   128 lignes ne gagneraient que sur le plein écran — qui n'est
 *                   pas le régime de ce produit — pour le DOUBLE de RAM interne.
 *                   La clé NVS reste : elle permet de rejouer l'A/B sans
 *                   reflasher, donc sans ajouter le binaire comme variable.
 *   draw_psram = 0 : draw buffer en RAM INTERNE, capable DMA. L'hypothèse était
 *                   que la PSRAM, déjà saturée à ~23,0 Mo/s en continu par le
 *                   seul refill de la dalle (§5.4), ferait passer chaque flush
 *                   deux fois par le même goulot. MESURÉ le 2026-08-15, à aire
 *                   strictement identique (323 092 px) :
 *                     RAM interne -> 2 180 us par flush de 61 440 o
 *                     PSRAM       -> 3 709 us pour le même flush  (1,70x)
 *                   Recoupement : le plein écran depuis la PSRAM donne 37,1 ms,
 *                   à 0,8 % du memcpy PSRAM->PSRAM de §5.4 (36,8 ms). Deux
 *                   instruments indépendants, le même chiffre.
 */
/*
 * ── bounce_px : 0 -> 4800, ET C'EST LA CORRECTION CENTRALE DE dn1-4 ──────────
 *
 * Le bounce buffer était « DISQUALIFIÉ (watchdog) » depuis dn1-2. La mesure du
 * 2026-08-16 le RÉHABILITE, et sur un symptôme que personne n'avait pu voir
 * avant : dn1-4 est la première story à faire de l'I2C PENDANT que la dalle
 * affiche (le TCA9554 ne sert qu'au boot).
 *
 * LE DÉFAUT, constaté par l'owner : dès qu'une transaction I2C a lieu, l'image
 * DÉFILE à toute vitesse. Permanent en lecture tactile `poll` (30 transactions
 * par seconde), présent seulement pendant le contact du doigt en `event`, absent
 * au repos. La bande du haut restait stable pendant que le bas défilait — ce qui
 * DISQUALIFIE le décrochage global : la DMA repart bien juste à chaque VBlank
 * (RESTART_IN_VSYNC), puis prend du retard EN COURS DE TRAME.
 *
 * LE MÉCANISME : sur ESP32-S3, la flash et la PSRAM partagent le contrôleur
 * SPI0. La DMA du panneau lit le framebuffer PSRAM à 23,0 Mo/s en continu ; du
 * code exécuté depuis la flash (le driver I2C) provoque des défauts de cache qui
 * lui volent ce bus, et elle est affamée. Le bounce buffer la découple : elle lit
 * désormais 10 lignes en RAM INTERNE, que le CPU remplit.
 *
 * 🔴 CE QUE ÇA SOLDE EN PLUS : l'artefact §10.5 de dn1-3 — « l'image entière
 *    clignote, comme un déplacement rapide, à chaque mise à jour du label » —
 *    DISPARAÎT aussi (constat owner, témoin = le label 1 Hz rallumé). Les deux
 *    symptômes n'en faisaient qu'un. Les SEPT hypothèses éliminées en dn1-3
 *    cherchaient dans le contenu, la phase et le volume écrit ; la cause était
 *    la contention du bus, qu'aucune ne testait.
 *
 * ⚠️ CONDITION NON NÉGOCIABLE : CONFIG_LCD_RGB_ISR_IRAM_SAFE=n. Avec =y, le
 *    bounce PANIQUE au boot — « Cache disabled but cached memory region
 *    accessed » — parce qu'une ISR IRAM-safe ne peut pas recopier depuis un
 *    framebuffer PSRAM. C'est très probablement ce qui avait fait conclure au
 *    « watchdog » de dn1-2 : les deux options étaient nouées, et changées
 *    ensemble. Voir le bloc correspondant de sdkconfig.defaults.
 *
 * Pourquoi 4800 px (10 lignes) et pas plus : c'est la plus petite taille essayée,
 * elle suffit, et elle coûte 2 x 9 600 o de RAM interne. Les 19 200 px des
 * branches de dn1-2 n'ont pas été rejoués — inutile tant que 4800 tient.
 *
 * COÛT MESURÉ — et l'attribution a dû être corrigée en cours de route :
 *   - AU REPOS (aucun redessin) : RIEN de mesurable. 0,8 % de charge avant comme
 *     après le bounce. Le remplissage ne passe pas par une tâche FreeRTOS, et il
 *     ne creuse pas non plus les compteurs IDLE.
 *   - EN REDESSIN (label 1 Hz, le régime de référence de dn1-3) : 0,9 % -> 2,0 %,
 *     soit +1,1 point. C'est là que le surcoût se paie.
 *   - fps INCHANGÉ : 37,40 Hz (+0,01 %).
 *   - LATENCE de transition : +160 ms, le vrai prix (voir DN_DEFAULT_DRAW_LINES).
 * ⚠️ Un relevé intermédiaire annonçait « 0,8 % -> 2,7 % » et attribuait tout au
 *    bounce : il avait été pris avec le label 1 Hz ALLUMÉ, donc deux variables à
 *    la fois. Corrigé par un A/B propre.
 */
#define DN_DEFAULT_NUM_FBS 1
/*
 * 🔴 4800 -> 7680 LE 2026-08-19 (dn4-6) — CORRECTION DE DÉFAUT, ⛔ pas confort.
 *
 * SYMPTÔME, constat owner verbatim : *« l'image entière glisse d'un cran et se
 * recale vers le bas, ensuite tous les chiffres clignotent une fois, et
 * rebelote »*, **une fois par seconde**, dès que des données PC arrivent à
 * 5 trames/s ET que les cases se repeignent.
 *
 * ⚠️ TROISIÈME OCCURRENCE DE §11.4 — LA FAMINE DMA — ET L'AGRESSEUR EST NEUF.
 *    Le dépôt l'avait vue sous **I²C** (le bounce y met fin) et sous **écriture
 *    flash** (le bounce y perd, D4 en est motivé). **L'USB n'avait JAMAIS été
 *    testé.**
 *
 * 🔴 CE N'EST PAS UN COUPABLE, C'EST UN SEUIL. Onze tests à UNE variable :
 *    le dessin seul ne le produit pas (mock 1 Hz sur 4 cases : rien) ; le
 *    trafic seul non plus (mêmes trames à checksum FAUX, donc zéro dessin :
 *    rien) ; la géométrie est innocentée (`widget grille 70 60` remet
 *    35 100 px : ça glisse quand même) ; le nombre de labels aussi (2
 *    grandeurs : ça glisse) ; le volume d'octets aussi (trames v2 : ça glisse).
 *    Et le firmware **`cfd1a54` (dn4-1) sous le MÊME stimulus ne glisse pas**.
 *    ⇒ dn4-6 a franchi le seuil **par ACCUMULATION**, et c'est exactement pour
 *      ça qu'aucun test à une variable ne le supprimait. Le remède est la MARGE.
 *
 * ⚠️ 7 680 EST LA PLUS PETITE VALEUR *LÉGITIME* QUI TIENNE, et les deux mots
 *    comptent : 4 800 glisse, 7 680 tient, et il n'existe **AUCUNE** valeur
 *    admissible entre les deux (voir `bounce_px_refus` : 5120, 6144 et 6400
 *    divisent bien la trame mais ne font pas un compte entier de lignes).
 *    Prix : **+11 520 o** de RAM interne, contre +19 200 pour 9 600.
 * ⛔ Ce n'est PAS gratuit : §11.5 impute au bounce buffer +160 ms de latence.
 *    Le relevé avant/après est en §18 du fichier d'affichage.
 */
/*
 * ═══════════════════════════════════════════════════════════════════════════
 * 🔴 7 680 → 9 600 LE 2026-08-23 — L'OPTIMUM EST MESURÉ, ⛔ PAS CHOISI
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * ⛔ Le motif de 7 680 (juste au-dessus / §18.9) RESTE VRAI et n'est pas effacé :
 *    il a été posé le 2026-08-19 contre la troisième occurrence de la famine.
 *
 * 🔴 CE QUI A CHANGÉ : `CONFIG_LCD_RGB_RESTART_IN_VSYNC` est passé à `n`
 *    (2026-08-23). La DMA n'est plus remise à zéro à chaque VBlank, donc une
 *    famine ne DÉCALE plus toute l'image — elle salit les lignes du demi-bounce
 *    en cours. ⇒ **L'ARBITRAGE N'EST PLUS LE MÊME** : ce qu'on optimise n'est
 *    plus « éviter la famine » mais « limiter la SURFACE du dégât quand elle
 *    arrive ».
 *
 * 🎯 ET IL Y A UN OPTIMUM, PARCE QUE LES DEUX EFFETS S'OPPOSENT :
 *      - un tampon PLUS GROS laisse plus de temps au remplissage (le seuil monte) ;
 *      - mais quand ça rate quand même, c'est un demi-bounce ENTIER qui est
 *        faux — donc PLUS DE LIGNES.
 *    Mesuré sous AGENT RÉEL, 180 s, œil de l'owner à chaque fenêtre :
 *
 *      bounce_px   demi-bounce   dépassement du seuil   ce que l'owner voit
 *        7 680      16 lignes         +720 us           « petite ligne »
 *      → 9 600      20 lignes      +176 a +182 us       « bien mieux, plus stable »
 *       15 360      32 lignes         +221 us           « pire, une bande qui
 *                                                         couvre les % »
 *
 *    ⇒ **9 600 est le minimum sur les DEUX instruments à la fois.**
 *
 * 🔴 AMENDE LE 2026-08-24 (revue de code 3 couches, dn4-10) — DEUX CHIFFRES DE CE
 *    BLOC ETAIENT A REPRENDRE. ⛔ Le texte d'origine n'est pas efface.
 *    1. LE DEPASSEMENT A 9 600 EST UNE FOURCHETTE. La source
 *       (investigations/glissement-dma-restart-in-vsync-investigation.md:159)
 *       publie 951-957 us, soit +176 A +182 us, sur DEUX fenetres. Ce fichier
 *       avait retenu 182, affichage.md 176, le ledger 176 — chacun une borne
 *       differente, EN SILENCE. La table ci-dessus porte desormais la fourchette.
 *    2. 🔴 « −7 024 o » EST 656 o SOUS LE MINIMUM QUE L'ALLOCATION EXIGE.
 *       `dn_bootcfg_cout_interne()` (l.565-568 de ce fichier) calcule
 *       `bounce = bounce_px * 2u * 2u` ⇒ Δ = (9 600 − 7 680) × 4 = 7 680 o.
 *       Confirme par le driver (bb_size = bounce_px * bpp / 8, x2 tampons) ET par
 *       le commentaire de la l.156 ci-dessus (« +11 520 o … contre +19 200 pour
 *       9 600 » ⇒ 19 200 − 11 520 = 7 680). ⛔ Un releve brut de tas libre ne peut
 *       pas rendre MOINS que ce que les tampons occupent. ⚠️ L'origine du 7 024
 *       est introuvable : §20.7.17 atteste que les releves bruts ne sont consignes
 *       dans AUCUN des deux depots. ⇒ Chiffre a retenir : le theorique, −7 680 o.
 *
 * ⚠️ COÛT, MESURÉ EN dn4-10 : −7 024 o de RAM interne (⚠️ voir l'amendement
 *    ci-dessus : le minimum arithmetique est 7 680 o), et **ZÉRO** ailleurs —
 *    `fps 15` reste à 37,40 Hz (+0,00 %), le boot ne bouge pas de façon
 *    discriminante, `nav ab 40` fait −0,3 ms sur n=80.
 *
 * ⛔ ET LE CRAN SUIVANT EST FERMÉ, PAS SEULEMENT MAUVAIS : `15 360` a été refusé
 *    par `dn_bootcfg_budget_refus()` le 2026-08-23 quand le tas était chargé,
 *    puis accepté sur un tas frais. ⚠️ Le verdict de la garde DÉPEND DONC DE
 *    L'INSTANT où on la consulte — à ne pas lire comme une propriété stable.
 */
#define DN_DEFAULT_BOUNCE_PX 9600
/*
 * ── draw_lines : 64 -> 128, décision owner du 2026-08-16 ─────────────────────
 *
 * Le commentaire ci-dessus reste vrai pour le régime qu'il décrivait : à 64
 * lignes, une mise à jour du label tient en UN seul flush, et 128 ne gagnaient
 * « que sur le plein écran — qui n'est pas le régime de ce produit ».
 *
 * Ce qui a changé : le régime de ce produit EST le plein écran. dn1-4 a introduit
 * la navigation, et une transition dashboard <-> détail redessine tout l'écran.
 * Le label 1 Hz était l'instrument de dn1-3 ; la transition est le geste de dn3.
 *
 * Et le bounce buffer (voir DN_DEFAULT_BOUNCE_PX) a rendu l'arbitrage pressant :
 * il coûte +160 ms de latence de transition. MESURÉ, 20 allers-retours par ligne :
 *
 *   bounce 4800 · 64 lignes  -> 427,7 ms moy (480,6 max) · RAM interne libre 180,0 Ko
 *   bounce 4800 · 128 lignes -> 307,1 ms moy (320,7 max) · RAM interne libre 118,9 Ko
 *   bounce 4800 · 160 lignes -> 307,7 ms moy (320,8 max) · le levier SATURE
 *
 * 128 récupère 120 des 160 ms perdus, pour 61 440 o de RAM interne. 160 ne donne
 * plus rien : au-delà de 5 flushes, le plancher n'est plus l'attente de synchro
 * mais le RENDU lui-même. On s'arrête donc à 128 — payer 30 Ko de plus pour
 * 0,6 ms serait acheter du bruit de mesure.
 *
 * ⚠️ Le budget < 300 ms du brief n'est toujours PAS tenu (307,1 ms). Il l'est de
 *    7 ms au lieu de 128 : le dépassement devient un sujet de réglage fin pour
 *    dn3-2/dn4-1, au lieu d'un mur. Options chiffrées en §11.5 de hardware/.
 */
#define DN_DEFAULT_DRAW_LINES 128
#define DN_DEFAULT_DRAW_PSRAM 0
/*
 *   lvgl_core = 0 : la tâche LVGL sur le CŒUR 0, avec le reste du pipeline
 *                   d'affichage. Le premier choix avait été le cœur 1, pour que
 *                   `cpu` sépare le rendu des tâches console — raison honnête,
 *                   conséquence non anticipée : les deux cœurs se sont mis à
 *                   travailler simultanément sur la mémoire externe, ce que
 *                   dn1-2 n'avait jamais eu. Variable de mesure, pas de confort.
 */
#define DN_DEFAULT_LVGL_CORE 0

static esp_err_t open_nvs(nvs_open_mode_t mode, nvs_handle_t *out)
{
    esp_err_t err = nvs_open(DN_NVS_NAMESPACE, mode, out);
    if (err != ESP_OK && err != ESP_ERR_NVS_NOT_FOUND) {
        ESP_LOGW(TAG, "nvs_open(%d) a échoué : %s", mode, esp_err_to_name(err));
    }
    return err;
}

/*
 * Validation UNIQUE de bounce_px, partagée par l'écriture (`set bounce`) et par
 * la relecture au boot. C'est le point important : tant que les deux chemins ne
 * partageaient pas la même règle, une valeur pouvait être refusée à l'écriture
 * et acceptée au boot — ou l'inverse — et le piège du plafond (cf.
 * DN_BOUNCE_PX_MAX) survivait à sa propre correction, puisque dn_bootcfg_load()
 * réacceptait à chaque démarrage la valeur qui halte le CPU.
 *
 * Renvoie NULL si la valeur est acceptable, sinon la RAISON du refus, en clair.
 */
static const char *bounce_px_refus(int32_t v)
{
    if (v < 0) {
        return "valeur négative";
    }
    if (v > DN_BOUNCE_PX_MAX) {
        /* Deux tampons de v*2 octets en RAM INTERNE + DMA : au-delà du plafond
         * c'est ESP_ERR_NO_MEM au boot, donc panique, donc CPU halté par
         * CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y, donc AUCUNE console pour
         * revenir en arrière. */
        return "au-dessus du plafond de RAM interne (carte non démarrable)";
    }
    if (v != 0 && ((size_t)DN_LCD_TOTAL_PX % (size_t)v) != 0) {
        /* Le driver RGB exige que la taille du bounce buffer divise le nombre
         * de pixels de la trame — sinon la DMA se décale d'un reliquat à chaque
         * trame. On refuse ici plutôt que de laisser le driver échouer plus
         * loin avec un message obscur. */
        return "ne divise pas les pixels d'une trame";
    }
    /*
     * 🔴 LA GARDE VÉRIFIAIT LE MAUVAIS INVARIANT, ET L'ŒIL DE L'OWNER L'A
     *    ATTRAPÉE (2026-08-19, dn4-6). « Diviser les pixels d'une trame » ne
     *    suffit pas : il faut un nombre **ENTIER DE LIGNES**. Sinon chaque
     *    morceau de bounce se termine AU MILIEU d'une ligne, et l'image sort
     *    **décalée horizontalement** — constat verbatim sur `bounce_px = 6400`
     *    (13,33 lignes) : *« image décentrée sur la droite »*.
     *
     * ⚠️ SUR LES VALEURS QUE CETTE GARDE ACCEPTAIT, DIX CASSAIENT L'IMAGE :
     *    2560, 3072, 3200, 4096, 5120, 6144, 6400, 10240, 12288, 12800.
     *
     * 🔴 ⛔ ET L'ÉNUMÉRATION DE CE COMMENTAIRE ÉTAIT FAUSSE — REVUE DE CODE DU
     *    2026-08-19. Elle annonçait « il n'en reste que SEPT ». **IL EN RESTE
     *    DOUZE**, plus le zéro. La garde combinée est
     *    `v <= DN_BOUNCE_PX_MAX` ET `DN_LCD_TOTAL_PX % v == 0` ET
     *    `v % DN_LCD_H_RES == 0`, c'est-à-dire `v = 480 x k` avec `k` diviseur
     *    de 640 et `k <= 80` :
     *        480, 960, 1920, 2400, 3840, 4800, 7680, 9600, 15360, 19200,
     *        30720, 38400   (soit 1, 2, 4, 5, 8, 10, 16, 20, 32, 40, 64 et
     *                        80 lignes)
     *    Les cinq oubliées — 480, 960, 1920, 30720, 38400 — sont acceptées par
     *    le code et n'apparaissaient nulle part. ⛔ Un commentaire qui présente
     *    une liste comme EXHAUSTIVE et ne l'est pas est un instrument qui ment,
     *    exactement comme le compteur décoratif de `dn_link.h`.
     * ✅ EN REVANCHE LA SOUS-AFFIRMATION TIENT, ET ELLE EST LA SEULE QUI COMPTE
     *    POUR §18.9 : **aucune valeur admissible entre 4 800 et 7 680** —
     *    5 760 = 480 x 12 et 12 ne divise pas 640. 7 680 est donc bien la plus
     *    petite valeur LÉGITIME qui tienne.
     * ⛔ LE PIÈGE ÉTAIT ARMÉ POUR QUICONQUE RÉGLERAIT CE PARAMÈTRE, et il s'est
     *    déclenché à la PREMIÈRE tentative de le régler. Un réglage refusé est
     *    une gêne ; un réglage ACCEPTÉ qui casse l'image en silence est un
     *    défaut — et rien, dans la console, ne l'aurait dit.
     * ⚠️ Le commentaire ci-dessus disait déjà « sinon la DMA se décale d'un
     *    reliquat à chaque trame » : il DÉCRIVAIT le mécanisme et le test ne le
     *    couvrait qu'à moitié.
     */
    if (v != 0 && ((size_t)v % (size_t)DN_LCD_H_RES) != 0) {
        return "n'est pas un nombre ENTIER de lignes (l'image sortirait décalée)";
    }
    return NULL;
}

/* Même règle partagée écriture/relecture que pour `bounce_px`, et pour la même
 * raison : tant que les deux chemins ne valident pas identiquement, une valeur
 * refusée à l'écriture peut être acceptée au boot (ou l'inverse), et la borne
 * qui protège la RAM interne cesse de protéger quoi que ce soit. */
static const char *draw_lines_refus(int32_t v)
{
    if (v < DN_DRAW_LINES_MIN) {
        return "en dessous du plancher (l'attente de synchro exploserait)";
    }
    if (v > DN_DRAW_LINES_MAX) {
        return "au-dessus du plafond de RAM interne (carte non démarrable)";
    }
    return NULL;
}

/* Une clé peut être PRÉSENTE et illisible : mauvais type ou mauvaise longueur
 * (ESP_ERR_NVS_TYPE_MISMATCH, ESP_ERR_NVS_INVALID_LENGTH). Ne traiter que
 * ESP_OK faisait retomber sur le défaut EN SILENCE — exactement ce que
 * dn_bootcfg.h promet de ne jamais faire. ESP_ERR_NVS_NOT_FOUND, lui, est le
 * cas NORMAL d'un clone neuf : il ne mérite pas un avertissement. */
static void log_lecture_refusee(const char *cle, esp_err_t err, int defaut)
{
    if (err == ESP_OK || err == ESP_ERR_NVS_NOT_FOUND) {
        return;
    }
    ESP_LOGW(TAG, "lecture de « %s » refusée (%s) : défaut %d appliqué", cle,
             esp_err_to_name(err), defaut);
}

esp_err_t dn_bootcfg_load(dn_bootcfg_t *out)
{
    if (!out) {
        return ESP_ERR_INVALID_ARG;
    }
    out->num_fbs = DN_DEFAULT_NUM_FBS;
    out->bounce_px = DN_DEFAULT_BOUNCE_PX;
    out->draw_lines = DN_DEFAULT_DRAW_LINES;
    out->draw_psram = DN_DEFAULT_DRAW_PSRAM;
    out->lvgl_core = DN_DEFAULT_LVGL_CORE;

    nvs_handle_t h;
    if (open_nvs(NVS_READONLY, &h) != ESP_OK) {
        ESP_LOGI(TAG, "aucune config en NVS — défauts appliqués");
        return ESP_OK;
    }

    int32_t v;
    esp_err_t err = nvs_get_i32(h, DN_KEY_NUM_FBS, &v);
    if (err == ESP_OK) {
        if (v >= 1 && v <= 3) {
            out->num_fbs = (int)v;
        } else {
            ESP_LOGW(TAG, "num_fbs=%ld hors de [1,3] : défaut %d appliqué", (long)v,
                     DN_DEFAULT_NUM_FBS);
        }
    } else {
        log_lecture_refusee(DN_KEY_NUM_FBS, err, DN_DEFAULT_NUM_FBS);
    }

    err = nvs_get_i32(h, DN_KEY_BOUNCE, &v);
    if (err == ESP_OK) {
        const char *refus = bounce_px_refus(v);
        if (!refus) {
            out->bounce_px = (int)v;
            /*
             * 🔴 UNE VALEUR STOCKÉE SOUS LE SEUIL MESURÉ SÛR EST **DITE** —
             *    REVUE DE CODE DU 2026-08-19.
             *    Élever le DÉFAUT à 7 680 ne touche pas une clé NVS déjà écrite,
             *    et 4 800 reste parfaitement légal sous la garde durcie
             *    (4800 % 480 == 0, 307200 % 4800 == 0). Une carte sur laquelle
             *    un `set bounce 4800` a été posé — et §18.9 documente une séance
             *    où l'owner RÉGLAIT ce paramètre — redémarrait donc **dans l'état
             *    qui glisse**, avec un log de boot qui disait seulement
             *    « bounce_px=4800 ».
             * ⛔ ON NE FORCE PAS LA VALEUR : un réglage explicite de l'opérateur
             *    n'est pas une erreur, et l'écraser en silence serait le défaut
             *    symétrique. On le REND AUDIBLE, et il se corrige par
             *    `cfg reset` (vérifié : rend bien 7 680) ou `set bounce 7680`.
             */
            /*
             * 🔴 DEUX SEUILS DEPUIS LE 2026-08-27, ⛔ PLUS UN SEUL — revue de
             *    code. Le test etait `v < DN_DEFAULT_BOUNCE_PX` : remonter le
             *    defaut a 9 600 a fait tomber 7 680 dans une alerte de
             *    GLISSEMENT, alors que 7 680 est fonctionnel et seulement
             *    sous-optimal. La justification complete est dans dn_bootcfg.h,
             *    au-dessus de `DN_BOUNCE_PX_ALERTE`.
             */
            if (v > 0 && v < DN_BOUNCE_PX_ALERTE) {
                ESP_LOGW(TAG,
                         "bounce_px=%ld vient de la NVS et est SOUS le seuil "
                         "MESURE SUR (%d px = %d lignes).",
                         (long)v, DN_BOUNCE_PX_ALERTE,
                         DN_BOUNCE_PX_ALERTE / DN_LCD_H_RES);
                ESP_LOGW(TAG,
                         "  🔴 C'est la zone ou l'image GLISSE d'un cran sous "
                         "trafic serie + repeint (famine DMA, §18.9). "
                         "`cfg reset` ou `set bounce %d` pour revenir au defaut.",
                         DN_DEFAULT_BOUNCE_PX);
            } else if (v > 0 && v < DN_DEFAULT_BOUNCE_PX) {
                ESP_LOGW(TAG,
                         "bounce_px=%ld vient de la NVS : FONCTIONNEL (>= %d px, "
                         "le seuil mesure sur) mais SOUS l'optimum mesure de "
                         "%d px.",
                         (long)v, DN_BOUNCE_PX_ALERTE, DN_DEFAULT_BOUNCE_PX);
                ESP_LOGW(TAG,
                         "  ⚠️ Ce n'est PAS une alerte de defaut, c'est une "
                         "alerte de reglage : `set bounce %d` gagne la marge "
                         "mesuree en §20bis.6. ⛔ Ne PAS monter au-dela — 15 360 "
                         "est PIRE (constat owner : une bande sur les %%).",
                         DN_DEFAULT_BOUNCE_PX);
            }
        } else {
            ESP_LOGW(TAG, "bounce_px=%ld refusé (%s) : défaut %d appliqué",
                     (long)v, refus, DN_DEFAULT_BOUNCE_PX);
            ESP_LOGW(TAG, "  plafond = %d px, diviseur exact de %d px de trame",
                     DN_BOUNCE_PX_MAX, DN_LCD_TOTAL_PX);
        }
    } else {
        log_lecture_refusee(DN_KEY_BOUNCE, err, DN_DEFAULT_BOUNCE_PX);
    }

    err = nvs_get_i32(h, DN_KEY_DRAW_LINES, &v);
    if (err == ESP_OK) {
        const char *refus = draw_lines_refus(v);
        if (!refus) {
            out->draw_lines = (int)v;
        } else {
            ESP_LOGW(TAG, "draw_lines=%ld refusé (%s) : défaut %d appliqué",
                     (long)v, refus, DN_DEFAULT_DRAW_LINES);
            ESP_LOGW(TAG, "  bornes = [%d, %d] lignes", DN_DRAW_LINES_MIN,
                     DN_DRAW_LINES_MAX);
        }
    } else {
        log_lecture_refusee(DN_KEY_DRAW_LINES, err, DN_DEFAULT_DRAW_LINES);
    }

    err = nvs_get_i32(h, DN_KEY_DRAW_PSRAM, &v);
    if (err == ESP_OK) {
        if (v == 0 || v == 1) {
            out->draw_psram = (int)v;
        } else {
            ESP_LOGW(TAG, "draw_psram=%ld hors de {0,1} : défaut %d appliqué",
                     (long)v, DN_DEFAULT_DRAW_PSRAM);
        }
    } else {
        log_lecture_refusee(DN_KEY_DRAW_PSRAM, err, DN_DEFAULT_DRAW_PSRAM);
    }

    err = nvs_get_i32(h, DN_KEY_LVGL_CORE, &v);
    if (err == ESP_OK) {
        if (v >= -1 && v <= 1) {
            out->lvgl_core = (int)v;
        } else {
            ESP_LOGW(TAG, "lvgl_core=%ld hors de [-1, 1] : défaut %d appliqué",
                     (long)v, DN_DEFAULT_LVGL_CORE);
        }
    } else {
        log_lecture_refusee(DN_KEY_LVGL_CORE, err, DN_DEFAULT_LVGL_CORE);
    }

    nvs_close(h);
    return ESP_OK;
}

static esp_err_t set_i32(const char *key, int32_t value)
{
    nvs_handle_t h;
    esp_err_t err = nvs_open(DN_NVS_NAMESPACE, NVS_READWRITE, &h);
    if (err != ESP_OK) {
        return err;
    }
    err = nvs_set_i32(h, key, value);
    if (err == ESP_OK) {
        err = nvs_commit(h);
    }
    nvs_close(h);
    return err;
}

esp_err_t dn_bootcfg_set_num_fbs(int num_fbs)
{
    if (num_fbs < 1 || num_fbs > 3) {
        return ESP_ERR_INVALID_ARG;
    }
    return set_i32(DN_KEY_NUM_FBS, num_fbs);
}

esp_err_t dn_bootcfg_set_bounce_px(int bounce_px)
{
    const char *refus = bounce_px_refus((int32_t)bounce_px);
    if (refus) {
        ESP_LOGW(TAG, "bounce_px=%d refusé : %s", bounce_px, refus);
        return ESP_ERR_INVALID_ARG;
    }
    return set_i32(DN_KEY_BOUNCE, bounce_px);
}

esp_err_t dn_bootcfg_set_draw_lines(int lines)
{
    const char *refus = draw_lines_refus((int32_t)lines);
    if (refus) {
        ESP_LOGW(TAG, "draw_lines=%d refusé : %s", lines, refus);
        return ESP_ERR_INVALID_ARG;
    }
    return set_i32(DN_KEY_DRAW_LINES, lines);
}

esp_err_t dn_bootcfg_set_draw_psram(int psram)
{
    if (psram != 0 && psram != 1) {
        return ESP_ERR_INVALID_ARG;
    }
    return set_i32(DN_KEY_DRAW_PSRAM, psram);
}

esp_err_t dn_bootcfg_set_lvgl_core(int core)
{
    if (core < -1 || core > 1) {
        return ESP_ERR_INVALID_ARG;
    }
    return set_i32(DN_KEY_LVGL_CORE, core);
}

/* ── LE TEMOIN DE REPLI ─────────────────────────────────────────────────────
 * La justification complete est dans dn_bootcfg.h, au-dessus de
 * `dn_bootcfg_repli_t`. Ici, seulement ce qui doit tenir a la relecture :
 *   - le temoin est ECRIT depuis `desknode_main`, au boot, une seule tache ;
 *   - il est LU depuis la console ;
 *   - il n'entre JAMAIS dans `dn_bootcfg_t` : ce n'est pas de la config, et le
 *     confondre avec de la config le ferait appliquer au lieu d'etre lu. */
void dn_bootcfg_get_repli(dn_bootcfg_repli_t *out)
{
    if (!out) {
        return;
    }
    out->present = false;
    out->demande_px = 0;
    out->retenu_px = 0;
    out->occurrences = 0;

    nvs_handle_t h;
    if (open_nvs(NVS_READONLY, &h) != ESP_OK) {
        return;
    }
    int32_t n = 0;
    if (nvs_get_i32(h, DN_KEY_REPLI_N, &n) == ESP_OK && n > 0) {
        int32_t v = 0;
        out->present = true;
        out->occurrences = (int)n;
        if (nvs_get_i32(h, DN_KEY_REPLI_DEM, &v) == ESP_OK) {
            out->demande_px = (int)v;
        }
        if (nvs_get_i32(h, DN_KEY_REPLI_RET, &v) == ESP_OK) {
            out->retenu_px = (int)v;
        }
    }
    nvs_close(h);
}

esp_err_t dn_bootcfg_note_repli(int demande_px, int retenu_px)
{
    nvs_handle_t h;
    esp_err_t err = nvs_open(DN_NVS_NAMESPACE, NVS_READWRITE, &h);
    if (err != ESP_OK) {
        return err;
    }
    int32_t n = 0;
    /* ⚠️ Une cle absente rend ESP_ERR_NVS_NOT_FOUND et laisse `n` a 0 : c'est
     *    le premier repli. ⛔ On ne traite pas cette erreur comme un echec. */
    (void)nvs_get_i32(h, DN_KEY_REPLI_N, &n);
    if (n < 0) {
        n = 0;
    }
    err = nvs_set_i32(h, DN_KEY_REPLI_DEM, (int32_t)demande_px);
    if (err == ESP_OK) {
        err = nvs_set_i32(h, DN_KEY_REPLI_RET, (int32_t)retenu_px);
    }
    if (err == ESP_OK) {
        err = nvs_set_i32(h, DN_KEY_REPLI_N, n + 1);
    }
    if (err == ESP_OK) {
        err = nvs_commit(h);
    }
    nvs_close(h);
    return err;
}

esp_err_t dn_bootcfg_clear_repli(void)
{
    nvs_handle_t h;
    esp_err_t err = nvs_open(DN_NVS_NAMESPACE, NVS_READWRITE, &h);
    if (err != ESP_OK) {
        return err;
    }
    /* ⚠️ Effacer une cle absente rend ESP_ERR_NVS_NOT_FOUND : ce n'est PAS une
     *    erreur ici, c'est le cas nominal quand il n'y a rien a effacer. */
    (void)nvs_erase_key(h, DN_KEY_REPLI_DEM);
    (void)nvs_erase_key(h, DN_KEY_REPLI_RET);
    (void)nvs_erase_key(h, DN_KEY_REPLI_N);
    err = nvs_commit(h);
    nvs_close(h);
    return err;
}

esp_err_t dn_bootcfg_reset(void)
{
    /*
     * 🔴 LE TEMOIN DE REPLI SURVIT A `cfg reset` — ET C'EST DELIBERE
     *    (decision owner du 2026-08-27). `nvs_erase_all()` l'emportait avec le
     *    reste. Or `cfg reset` est PRECISEMENT ce qu'on tape pour sortir d'une
     *    valeur fautive : c'est le moment ou l'on a le PLUS besoin de savoir
     *    qu'un repli a eu lieu, et lequel. ⇒ on le releve, on efface, on le
     *    repose. Il ne s'efface que par `cfg repli clear`.
     * ⚠️ Si la repose echoue, on le DIT : perdre la trace en silence serait
     *    exactement le defaut que ce temoin existe pour fermer.
     */
    dn_bootcfg_repli_t t;
    dn_bootcfg_get_repli(&t);

    nvs_handle_t h;
    esp_err_t err = nvs_open(DN_NVS_NAMESPACE, NVS_READWRITE, &h);
    if (err != ESP_OK) {
        return err;
    }
    err = nvs_erase_all(h);
    if (err == ESP_OK) {
        err = nvs_commit(h);
    }
    nvs_close(h);
    if (err == ESP_OK && t.present) {
        esp_err_t err_t = ESP_OK;
        for (int i = 0; i < t.occurrences && err_t == ESP_OK; i++) {
            err_t = dn_bootcfg_note_repli(t.demande_px, t.retenu_px);
        }
        if (err_t == ESP_OK) {
            ESP_LOGW(TAG,
                     "cfg reset : le TEMOIN DE REPLI est CONSERVE (%d repli(s), "
                     "%d px demandes -> %d px retenus). `cfg repli clear` pour "
                     "l'effacer.",
                     t.occurrences, t.demande_px, t.retenu_px);
        } else {
            ESP_LOGE(TAG,
                     "🔴 cfg reset : le TEMOIN DE REPLI a ete PERDU (%s). Il "
                     "disait : %d repli(s), %d px demandes -> %d px retenus. "
                     "⛔ Cette ligne de log est desormais la seule trace.",
                     esp_err_to_name(err_t), t.occurrences, t.demande_px,
                     t.retenu_px);
        }
    }
    return err;
}

void dn_bootcfg_log(const dn_bootcfg_t *cfg)
{
    ESP_LOGI(TAG, "config de boot : num_fbs=%d  bounce_px=%d", cfg->num_fbs,
             cfg->bounce_px);
    ESP_LOGI(TAG,
             "                draw_lines=%d (%d o) en %s", cfg->draw_lines,
             (int)(DN_LCD_H_RES * cfg->draw_lines * 2),
             cfg->draw_psram ? "PSRAM" : "RAM interne DMA");
    ESP_LOGI(TAG, "                tâche LVGL sur %s",
             cfg->lvgl_core < 0 ? "aucun cœur imposé" :
             cfg->lvgl_core == 0 ? "le cœur 0 (avec le pipeline d'affichage)"
                                 : "le cœur 1 (en face du pipeline)");
}

/* ── Le budget combiné RAM interne (revue dn1-4) ───────────────────────────── */

/*
 * Marge laissée libre au-dessus de la demande. Elle n'est pas décorative : le
 * driver RGB alloue ses tampons en blocs CONTIGUS et DMA-capables, et le tas
 * interne est fragmenté par tout ce qui a démarré avant (pilotes, tâches, pile
 * réseau absente ici mais NVS et console présentes). Une demande qui tient tout
 * juste dans le total libre peut échouer faute d'un bloc d'un seul tenant — et
 * cet échec-là, au boot, halte le CPU.
 *
 * 48 Ko : de l'ordre du plus gros bloc que le boot alloue après ces tampons,
 * doublé. Ce n'est pas une mesure, c'est une marge déclarée — et elle sera
 * révisée par la mesure le jour où un refus paraîtra trop sévère.
 */
#define DN_BUDGET_MARGE_O (48 * 1024)

size_t dn_bootcfg_cout_interne(int bounce_px, int draw_lines)
{
    /* Le driver RGB alloue DEUX bounce buffers de bounce_px pixels 16 bits. */
    size_t bounce = (size_t)(bounce_px > 0 ? bounce_px : 0) * 2u * 2u;
    /* Le draw buffer de LVGL : une bande de la largeur de la dalle.
     * ⚠️ Compté ici même si `draw_psram` est à 1 (il vivrait alors en PSRAM) :
     *    ce budget est le PIRE cas, et se tromper du côté sévère coûte un refus,
     *    tandis que se tromper de l'autre côté coûte une carte qui ne démarre
     *    plus sans console pour la récupérer. */
    size_t draw = (size_t)DN_LCD_H_RES * (size_t)(draw_lines > 0 ? draw_lines : 0) * 2u;
    return bounce + draw;
}

/* PUBLIÉE depuis dn4-10 : la console imprime la comparaison RÉELLEMENT faite
 * (`veut + marge > peut`), et pour ça il lui faut la marge. Elle ne peut plus
 * rester privée sans que le message ait à la deviner — c'est cette devinette
 * qui avait produit le « marge de sécurité déduite » FAUX. */
size_t dn_bootcfg_budget_marge_o(void) { return DN_BUDGET_MARGE_O; }

/* PUBLIÉE depuis dn4-10 : `dn_display.c` en a besoin pour son FILET DE
 * SÉCURITÉ au boot — replier sur le défaut quand la valeur de la NVS ne
 * s'alloue pas. Sans accessseur il aurait fallu recopier le nombre, et un
 * nombre recopié finit toujours par diverger de son original. */
int dn_bootcfg_defaut_bounce_px(void) { return DN_DEFAULT_BOUNCE_PX; }

const char *dn_bootcfg_budget_refus(int bounce_px, int draw_lines, size_t *demande,
                                    size_t *dispo)
{
    size_t veut = dn_bootcfg_cout_interne(bounce_px, draw_lines);
    /*
     * Ce qui sera disponible AU PROCHAIN BOOT pour ces deux tampons : ce qui est
     * libre maintenant, PLUS ce que les tampons actuels rendront. On mesure donc
     * contre la carte telle qu'elle est, pas contre un chiffre gravé en dn1-2
     * quand LVGL n'existait pas encore dans ce binaire.
     */
    size_t libre = heap_caps_get_free_size(MALLOC_CAP_INTERNAL | MALLOC_CAP_DMA);
    size_t rendu = dn_bootcfg_cout_interne(dn_display_bounce_px(), dn_ui_draw_lines());
    size_t peut = libre + rendu;

    if (demande) {
        *demande = veut;
    }
    if (dispo) {
        *dispo = peut;
    }
    if (veut + DN_BUDGET_MARGE_O > peut) {
        return "le couple bounce_px + draw_lines ne tient pas en RAM interne "
               "(la carte ne redémarrerait pas)";
    }
    return NULL;
}

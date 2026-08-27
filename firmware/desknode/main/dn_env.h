#pragma once
/*
 * dn_env — les TROIS capteurs d'environnement LOCAUX de DeskNode (dn4-3, P9.3).
 *
 *   · BH1750       @ 0x23 — luminosité de la pièce
 *   · INA219       @ 0x40 — tension / courant / puissance
 *   · TOF050C-VL6180X @ 0x29 — présence et conformité SEULEMENT (voir plus bas)
 *
 * ── 🔴 POURQUOI UN MODULE À CÔTÉ DE `dn_capteurs`, ET PAS `dn_capteurs` ÉTENDU
 *
 * X4 tranché en hardware/…-capteurs-i2c.md §13.19.4, voie (C). En deux phrases :
 *  · `dn_capteurs` est le module BME680, PAR CONCEPTION ASSUMÉE (dn_capteurs.h:8-10)
 *    et son API entière est mono-capteur. Le généraliser reviendrait à refactorer
 *    la SEULE case vivante aujourd'hui — `AMBIANCE` — pour y ajouter trois
 *    capteurs qui n'ont ni son protocole ni son garde-fou d'identité.
 *  · Un second module AVEC SA TÂCHE mettrait DEUX réveils sur un bus que le GT911
 *    pole déjà ~30×/s, sur une carte dont la marge DMA est « franchie, pas
 *    confortable » et dont le bus se dégrade 40 s à froid.
 *
 * ⇒ Module séparé (API `dn_env_*`, état propre, seaux propres), mais **AUCUNE
 *   TÂCHE** : `dn_env_cycle()` est appelée par la tâche `dn_capt` existante.
 *
 * 🔴 ET LE POINT D'ACCROCHE EST CONTRAINT PAR LE CODE, PAS PAR LE GOÛT : le corps
 * de `tache_capteurs()` est truffé de `continue` sur chaque chemin d'erreur du
 * BME680. Un appel en FIN de boucle serait SAUTÉ à chaque erreur — c'est-à-dire
 * précisément pendant la dégradation à froid, le seul moment où la tolérance
 * d'AC3 se mesure. ⇒ l'appel est IMMÉDIATEMENT APRÈS `vTaskDelayUntil()`.
 *
 * ⚠️ LA LIMITE DE CE CHOIX EST DÉCLARÉE, PAS CACHÉE : si `xTaskCreate` échoue
 * dans `dn_capteurs_init()`, aucune tâche ne tourne et `dn_env` n'est JAMAIS
 * cadencé. ⇒ il compte ses cycles, et `env` affiche « JAMAIS CADENCE » tant
 * qu'aucun n'est arrivé. ⛔ Un module optionnel n'acquitte pas dans le vide.
 *
 * ── 🔴 DRIVERS MAISON POUR LES TROIS — arbitré, ⛔ pas préféré (§13.19.2/.4)
 *
 * Critères écrits et horodatés AVANT toute lecture de source (2026-08-20 15:11).
 * Ce qui a tranché, dans l'ordre :
 *  · `dn_console.c` parle DÉJÀ aux trois en `i2c_master_transmit_receive` nu avec
 *    retour testé. Pour le BH1750, le pilote entier tient en TROIS transactions.
 *  · Aucun composant tiers ⇒ le compte de 103 `ESP_ERROR_CHECK` dans
 *    `managed_components/` (dont 26 dans un module OPTIONNEL) n'augmente pas, et
 *    l'obligation de ré-audit — MANUELLE, sans mécanisme, sur un répertoire
 *    GITIGNORÉ — ne s'étend pas.
 *  · `espressif/bh1750` 2.0.0 (7 147 téléch., Apache-2.0, esp-bsp) — le candidat
 *    que l'adoption désignait — bloque **1 000 ms par transaction**. Sur CETTE
 *    carte, c'est disqualifiant. ⚠️ Ce n'est pas un défaut du composant.
 *  · Il n'existe AUCUN composant VL6180X au registre (404 vérifié) ⇒ un driver
 *    maison était de toute façon obligatoire pour ce capteur-là.
 * ⏳ PLAN B NOMMÉ : si la conversion maison du BH1750 se révélait fausse, repli
 *    sur `espressif/bh1750` 2.0.0 — sa conversion est `brut / 1.2`, la nôtre
 *    aussi — en acceptant son 1 000 ms.
 *
 * ── ⛔ CE QUE CE MODULE NE FAIT PAS, ET POURQUOI
 *
 * 🔴 L'ALS DU VL6180X N'EST PAS EXPLOITÉ COMME MESURE DE LUMIÈRE. Qualifié à la
 * console AVANT toute ligne de driver (AC8), il rend une réponse STRICTEMENT
 * BINAIRE sur sept points d'intégration : 0x0000 à ≤ 2 ms, 0xFFFF à ≥ 3 ms, au
 * gain minimal 1,0×. ⇒ ce n'est pas une intégration, c'est un comparateur saturé.
 * La cause est nommée : ST impose un chargement de registres PRIVÉS (« SR03
 * settings ») après SYSTEM__FRESH_OUT_OF_RESET, et ⛔ le dépôt interdit de
 * recopier des adresses de registre de mémoire ou depuis un article.
 * ⇒ le VL6180X est LU EN RÉGIME pour sa PRÉSENCE et sa CONFORMITÉ, rien d'autre.
 * ⚠️ Détail complet et recette de reprise : §13.19.5.
 */

#include <stdbool.h>
#include <stdint.h>
#include "esp_err.h"

/* ── Cadence et péremption ────────────────────────────────────────────────────
 * ⚠️ La cadence N'EST PAS un réglage de ce module : elle est celle de la tâche
 * qui l'appelle (`dn_capt`, DN_CAPT_PERIODE_MS = 5 000 ms). La constante ci-
 * dessous ne SERT QU'À la péremption et au backoff, et un `_Static_assert` dans
 * le .c la cloue à celle de dn_capteurs pour qu'elles ne puissent pas diverger. */
#define DN_ENV_PERIODE_MS 5000

/* 3 périodes — MÊME CONVENTION que dn_capteurs (15 s), ⛔ PAS les 3 s de dn_link. */
#define DN_ENV_PEREMPTION_US (3LL * DN_ENV_PERIODE_MS * 1000)

/* Une tentative de ré-ouverture par MINUTE quand un device est absent.
 * ⛔ Ne pas sonder plus souvent : le GT911 pole déjà le bus ~30×/s, et
 * `i2c_master_probe()` a un taux de FAUX POSITIFS mesuré à 1,744 % à 8 devices. */
#define DN_ENV_REINIT_CYCLES 12

/* Timeout par transaction. 100 ms = la valeur du plus propre des candidats tiers
 * lus en §13.19.4, et ~1 000× la durée théorique d'une transaction de 3 octets à
 * 400 kHz. ⛔ PAS 1 000 ms : ce module tourne dans la tâche qui porte AUSSI le
 * BME680, et l'I²C est le PREMIER AGRESSEUR CONNU de la famine DMA (§11.4). */
#define DN_ENV_I2C_TIMEOUT_MS 100

/* 🔴 SENTINELLE « PAS DE VALEUR » — INT32_MIN, la MÊME que dn_capteurs.
 * ⛔ Surtout PAS -1 : c'est une puissance négative parfaitement légitime sur
 * l'INA219 (courant qui repart vers la source). La leçon est écrite en toutes
 * lettres dans dn_capteurs.h:217, elle a coûté deux défauts de console. */
#define DN_ENV_ABSENT INT32_MIN

typedef enum {
    DN_ENV_LUM = 0,  /* BH1750  @ 0x23 */
    DN_ENV_ALIM,     /* INA219  @ 0x40 */
    DN_ENV_TOF,      /* VL6180X @ 0x29 — présence/conformité seulement */
    DN_ENV_NB,
} dn_env_id_t;

typedef enum {
    DN_ENV_JAMAIS, /* aucune lecture valide depuis le boot */
    DN_ENV_VIVANT, /* dernière lecture plus récente que la péremption */
    DN_ENV_MUET,   /* la péremption est passée */
} dn_env_etat_t;

/* Les MÊMES seaux que dn_capteurs, au même vocabulaire — c'est délibéré : deux
 * modules qui comptent la même chose sous deux noms sont deux instruments qu'on
 * ne peut pas comparer. ⛔ Pas de `pousses_ratees` ici : dn_env ne pousse rien
 * vers l'UI tant que X2 n'a pas tranché la 6ᵉ case (AC6). Un compteur qui ne
 * peut pas bouger est un instrument qui ment. */
typedef struct {
    uint32_t lectures;   /* lectures VALIDES appliquées */
    uint32_t err_i2c;    /* le transport a échoué (NACK, bus occupé, timeout) */
    uint32_t err_donnee; /* il répond, mais la donnée n'est pas exploitable.
                          * 🔴 TOUJOURS 0 POUR LE BH1750, et c'est DÉCLARÉ
                          * (revue de code 2026-08-20) : sa seule condition est
                          * « 0 lu dans les 180 ms d'une (re)configuration », or
                          * TOUT appel à `configurer()` est suivi d'un `return`
                          * explicite — la lecture suivante arrive ≥ 5 000 ms
                          * plus tard. ⛔ Hors de cette fenêtre, 0 lx est une
                          * valeur LÉGITIME. Le seau reste pour le VL6180X
                          * (identité qui répond mais n'est pas la bonne) et
                          * l'INA219 (CNVR à 0). */
    uint32_t err_bornes; /* valeur hors plage physique — voir dn_env.c pour les
                          * bornes ET LEUR SOURCE (datasheet), par capteur.
                          * 🔴 TOUJOURS 0 POUR LE VL6180X, et c'est DÉCLARÉ
                          * (revue de code 2026-08-20) : il ne publie AUCUNE
                          * grandeur — on n'y lit que son identité — donc il n'a
                          * rien à borner. ⛔ Un seau qui ne peut pas bouger sans
                          * que ce soit écrit est un compteur décoratif (AC1). */
    uint32_t reprises;   /* transitions MUET -> VIVANT */
    uint32_t conformite; /* DÉTECTIONS d'une configuration perdue = la garde
                          * anti-fantôme. ⛔ Compte les détections, pas les
                          * réparations. Toujours 0 pour le BH1750 : il n'a AUCUN
                          * registre relisible, et cette absence est DÉCLARÉE. */
} dn_env_compteurs_t;

/*
 * ── 🔴 LA LOI DU RÉTROÉCLAIRAGE AUTOMATIQUE (AC5 / X1) — ÉCRITE AVANT LA MESURE
 *
 * Entrée : le lux du BH1750. Sortie : `dn_display_backlight_pct()`.
 * ⛔ JAMAIS `dn_display_backlight_ramp()` : son docblock dit qu'elle est un GESTE
 *   D'OPÉRATEUR, et elle appelle `vTaskDelay` — une boucle périodique qui
 *   l'appellerait ferait dormir la tâche qui porte AUSSI le BME680.
 *
 *   lux <= DN_ENV_BL_LUX_BAS   ->  DN_ENV_BL_PCT_MIN
 *   lux >= DN_ENV_BL_LUX_HAUT  ->  DN_ENV_BL_PCT_MAX
 *   entre les deux             ->  interpolation LINÉAIRE
 *
 * 🔴 LES QUATRE BORNES SONT ANCRÉES SUR DES MESURES DE CE DÉPÔT, ⛔ PAS SUR UNE
 *    NORME RECOPIÉE — c'est la condition qu'AC5 pose (« aucun pct en dur non
 *    motivé ») :
 *
 *  · PCT_MIN = 3 — 🎯 `dn1-3` AC7, CONSTAT OWNER : « 3 % = la limite. Le Living
 *    PCB et le label s'y distinguent encore, TOUT JUSTE. C'est le plancher du
 *    futur mode Ambient. » ⛔ En dessous, la dalle n'est plus lisible : ce n'est
 *    pas une préférence, c'est un plancher mesuré à l'œil.
 *  · PCT_MAX = 100 — l'état actuel au boot (desknode_main.c étape 7).
 *  · LUX_BAS = 20 — au-dessous, on est déjà dans le noir utile : la main posée
 *    sur le capteur a MESURÉ 1,6 lx (§13.17.4), très en dessous.
 *  · LUX_HAUT = 400 — l'éclairage de bureau MESURÉ SUR CETTE CARTE le
 *    2026-08-20 : brut 494 ⇒ 411 lx (§13.19.5). ⛔ Pas les « 500 lx » d'une
 *    norme de poste de travail, que personne n'a mesurée ici.
 *
 * ⚠️ HYSTÉRÉSIS — c'est une BANDE MORTE, pas deux seuils : le duty ne bouge que
 *    si l'écart au duty APPLIQUÉ atteint DN_ENV_BL_HYST points. 3 points = 31
 *    crans LEDC sur 1 023, et c'est aussi la valeur du plancher lisible : en
 *    dessous, l'œil ne peut pas voir la correction, donc la faire serait
 *    dépenser des transactions pour rien.
 *
 * ⚠️ PAS MAXIMAL — la course complète (3 -> 100) prend 5 cycles = 25 s. C'est ce
 *    qui remplace la rampe interdite : progressif, sans aucun `vTaskDelay`.
 *    🔴 Et c'est le chiffre le plus susceptible d'être DÉMENTI par l'œil de
 *    l'owner ⇒ il est RÉGLABLE À CHAUD (`bl auto pas <n>`), comme les bornes.
 *
 * ⚠️ CAPTEUR MUET : ⛔ le duty NE BOUGE PAS. On garde le dernier appliqué. Un
 *    capteur silencieux ne doit ni éteindre l'écran ni le mettre à fond.
 *
 * ~~🔴 DÉSARMÉ PAR DÉFAUT, et c'est le repli pré-autorisé d'AC5 qui devient
 *    l'état de départ : la discipline de boot (duty 0 à l'init, il ne monte
 *    qu'après la première trame) reste INTOUCHÉE, et l'A/B se joue dans UN SEUL
 *    FIRMWARE.~~
 * 🔴 BARRÉ PAR `dn4-19` LE 2026-08-27, ⛔ PAS EFFACÉ — LE MOTIF ÉTAIT L'A/B DE
 *    `dn4-3`, ET L'A/B EST FINI. Ce `false` a eu une conséquence que personne
 *    n'avait mesurée : **l'asservissement n'a JAMAIS TOURNÉ**. Carte à
 *    `up 3820 s`, 68 % du temps en Ambient, `bl` rend `applique : AUCUNE
 *    application depuis le boot`, et le duty reste cloué à 10 % pendant que le
 *    BH1750 lit 357 lx à dix centimètres. ⇒ `true`, et le coût est NUL sur les
 *    trois lignes qui coûtent : **0 écriture NVS en régime** (D4 de `dn4-5`
 *    tient), **0 clé NVS de plus** (les deux d'aujourd'hui suffisent), et
 *    `dn_env.c` **reste hors de la table** de `tools/verif_d4_nvs_dn45.py`.
 * ✅ ET LE RETOUR À L'ÉTAT SAIN RESTE GRATUIT : `bl auto off` ne survit pas au
 *    reboot, donc un module qu'un geste a laissé dans un état bancal se répare
 *    en le redémarrant. C'est ce que la persistance NVS aurait coûté : un
 *    `bl auto off` qui survit, c'est un module qui peut rester cassé.
 */

/*
 * ══ 🔴 LA RÈGLE DE PRIORITÉ DES ÉCRIVAINS DE LEDC — `dn4-19`/AC2.1 ═══════════
 *
 * ⛔ IL Y A SIX ÉCRIVAINS ET AUCUN VERROU. Énumérer les six sans dire qui
 *    l'emporte n'est PAS un arbitrage : c'est ce que ce fichier faisait, et le
 *    résultat est que la VEILLE désarmait l'asservissement pour se protéger.
 *
 * ✅ LA RÈGLE, EN UNE PHRASE :
 *
 *      **Le dernier GESTE D'OPÉRATEUR l'emporte sur tout — il désarme
 *      l'asservissement et il le DIT ; sinon la BASCULE d'état pose le niveau
 *      du nouveau régime EN UNE FOIS, et l'ASSERVISSEMENT le maintient ensuite,
 *      par pas de `DN_ENV_BL_PAS_MAX` points.**
 *
 * ✅ ET LE POURQUOI, PARCE QU'UNE RÈGLE SANS MOTIF SE FAIT DÉFAIRE :
 *    · un humain qui tape une valeur veut **la voir tenir** — sinon l'instrument
 *      ment (`bl 50` écrasé au cycle suivant, sans un mot) ;
 *    · une **transition** doit être instantanée à l'œil — `dn3-3`/AC4 publie
 *      t₁ = 107 µs, et la porter par le pas de 20 pts/5 s la ferait passer à
 *      ~20 s, soit **quatre ordres de grandeur** ;
 *    · un **régime** doit suivre la pièce — c'est tout le sujet de `dn4-19`.
 *
 * ⇒ 🔴 L'INVARIANT QUI EN DÉCOULE, ET IL EST TESTABLE :
 *      *l'asservissement fixe le NIVEAU DE RÉGIME de chaque état ;
 *       il ne porte JAMAIS la transition entre les deux.*
 *
 * Les six écrivains, et ce que la règle leur donne :
 *   1. le **boot** (`desknode_main.c:411`, 100 %, une fois) — c'est la première
 *      bascule vers ACTIF ; l'asservissement le ramène ensuite au régime.
 *      ⚠️ `dn3-3` cite encore `desknode_main.c:321` : **périmé**, c'est `:411`.
 *   2. le **REPL** (`bl <n>`, `bl on|off`, `bl ramp`) — geste d'opérateur, il
 *      GAGNE, et il désarme en le disant (`dn_console.c`).
 *   3. l'**asservissement** (`dn_env_cycle()`, toutes les `DN_ENV_PERIODE_MS`).
 *   4. la **VEILLE** (`dn_ui.c`, `veille_bl_descendre` / `veille_bl_remonter`) —
 *      elle pose le niveau du régime EN UNE FOIS, ⛔ elle ne désarme plus.
 *   5. `veille pct` (`dn_ui_veille_set_pct`) — ⛔ ce n'est PLUS le niveau
 *      d'Ambient : c'est le niveau de **DERNIER RECOURS**, celui que la veille
 *      pose quand la loi ne peut pas parler (capteur muet). Voir `dn_veille.h`.
 *   6. 🔴 **`dn_ui_veille_bl_rafraichir()`** (`dn_ui.c`) — **AJOUTÉ PAR
 *      `dn4-19` LUI-MÊME, ET IL MANQUAIT À CETTE LISTE** (trouvé en revue de
 *      code le 2026-08-27). Il est déclenché **DEPUIS LA CONSOLE** — `bl auto
 *      ambiant`, `bl auto ambiant plancher`, `bl auto courbe` — pour que l'œil
 *      voie l'effet du réglage SANS attendre un cycle de 5 s.
 *      ⚠️ **Ce n'est PAS un geste d'opérateur au sens de la règle** : il ne
 *      désarme rien et ne gagne rien. Il **re-pose le niveau du RÉGIME**, donc
 *      il relève de la même clause que la bascule (n° 4) — il pose EN UNE FOIS,
 *      et l'asservissement maintient ensuite. C'est pourquoi il **sort sans
 *      rien faire hors Ambient** : en Actif, c'est l'asservissement qui mène.
 *      ⛔ **La leçon de l'oubli, et elle vaut pour la prochaine story** : cette
 *      énumération EST l'arbitrage (AC2.1). Un écrivain qu'on ajoute sans
 *      l'y inscrire rend la règle fausse **au commit qui l'écrit** — c'est
 *      exactement ce qui s'est passé ici. ⇒ **`rtk proxy grep -rn
 *      'dn_display_backlight_pct(' main/` avant de refermer une story qui
 *      touche au rétroéclairage.**
 */
/*
 * 🔴 DEUX DE CES QUATRE BORNES ONT ÉTÉ DÉPLACÉES PAR L'ŒIL DE L'OWNER LE
 *    2026-08-20, ET LEURS ANCIENNES VALEURS SONT CONSERVÉES ICI (§13.19.7).
 *
 * · PCT_MIN : 3 -> 8. Le 3 % venait d'AC7 de `dn1-3`, où il était le PLANCHER
 *   LISIBLE — mais mesuré sur le **Living PCB et son label**, une image de fond
 *   contrastée. Rejoué sur le **dashboard à six cases** (du texte fin), constat
 *   owner : *« casiement plus lisible super sombre »*. La dichotomie 10 / 6 / 8,
 *   conduite RIDEAU FERMÉ (capteur à 2 lx, la condition où le plancher
 *   s'applique), a rendu : 10 % *« un peu trop lumineux »*, 6 % *« lisible, un
 *   poil trop sombre »*, **8 % *« c'est bien »***.
 *   ⇒ ⛔ **Le 3 % de `dn1-3` n'est PAS invalidé : il ne portait simplement pas
 *     sur ce contenu-là.** Un plancher de lisibilité est une propriété du
 *     COUPLE duty × contenu, pas du duty seul.
 *
 * · LUX_HAUT : 400 -> 1500 -> 600. Le 400 venait d'UNE mesure (411 lx). La séance en a
 *   relevé bien d'autres dans la même pièce : **2 lx rideau fermé** jusqu'à
 *   **2 262 lx** en journée. À 400 lx de plafond, la loi saturait à 100 % dès un
 *   éclairage artificiel modeste — elle *« ne modulait quasiment jamais »*.
 *   ⚠️ **Ce diagnostic-là a lui-même dû être corrigé** : il s'appuyait d'abord
 *   sur un « rideaux fermés = 1 296 lx » qui était en fait un rideau **pas
 *   encore fermé**. C'est l'owner qui l'a dit, ⛔ pas une déduction.
 *   🔴 **PUIS 1500 -> 600, ENCORE PAR L'ŒIL** : à 1 500 lx de plafond, une pièce
 *   éclairée à 170 lx ne recevait que **17 %**, et le constat owner a été
 *   *« un peu plus lumineux »*. À 600 lx, la même pièce reçoit **32 %**, et le
 *   constat est **« c'est ça »**. ⚠️ **Une réponse intermédiaire de l'owner était
 *   AMBIGUË** (*« ok pas mal pour être un peu plus »*) — plus RAPIDE ou plus
 *   LUMINEUX se corrigent à deux endroits opposés de la loi. ⛔ Elle n'a PAS été
 *   tranchée au jugé : la question a été reposée en distinguant les deux.
 *
 * 🔴 ET LE PLANCHER EST DÉSORMAIS RÉGLABLE À CHAUD, parce que la séance a prouvé
 *    qu'il en avait besoin : j'avais rendu les bornes en LUX ajustables et laissé
 *    le plancher en % figé à la compilation — or c'est précisément lui que l'œil
 *    a déplacé. *« L'arbitrage se tranche sur la dalle »* vaut pour les deux.
 */
#define DN_ENV_BL_PCT_MIN      8
#define DN_ENV_BL_PCT_MAX      100
#define DN_ENV_BL_LUX_BAS      20
#define DN_ENV_BL_LUX_HAUT     600
#define DN_ENV_BL_HYST         3
/*
 * 🔴 `dn4-19`, 2026-08-27 — ~~20~~ ⇒ **50**, PAR CONSTAT OWNER À L'ŒIL.
 *    Question posée SÉPARÉMENT de « plus lumineux » (⛔ elles se corrigent à
 *    deux endroits opposés de la loi, et ce dépôt s'est déjà fait piéger là) :
 *    *« trop lent — j'aimerais plus réactif »*, puis, main posée devant le
 *    capteur et retirée, **verbatim : « on voit bien les 2 se déclencher c'est
 *    good »**. Course complète en **2 cycles (~10 s)** au lieu de 5 (~25 s).
 * ⛔ LA CADENCE DE 5 s N'A PAS BOUGÉ, et ⛔ elle ne doit pas : elle cadence LES
 *    CINQ PISTES CAPTEURS, pas seulement le rétroéclairage.
 * ⚠️ Le verrou `pas >= DN_ENV_BL_HYST` reste (`dn_env_bl_pas_set`) : sous la
 *    bande morte, la loi se fige à mi-chemin, dans les DEUX sens, pour TOUS les
 *    lux.
 */
#define DN_ENV_BL_PAS_MAX      50
#define DN_ENV_BL_AUTO_DEFAUT  true   /* dn4-19 : ⛔ était `false` — voir ci-dessus */

/*
 * 🔴 LE RÉGIME D'AMBIENT — `dn4-19`/AC3.2, ET LE CADRAGE N'EN TRANCHE AUCUN.
 *
 * L'échelle dit quel pourcentage de la loi s'applique en AMBIENT. `100` = la
 * MÊME loi dans les deux états — candidat (a) du tableau d'AC3.2, et c'est la
 * SEULE valeur qui porte un constat owner : *« j'ai bien vu 10 -> 30 -> 50 ->
 * 61 % et 61 c'est bien mieux »*, à 363 lx, où la loi rend exactement 61.
 * ⚠️ Elle coûte la propriété D-1 de `dn3-3` (*« Ambient est plus sombre
 *    qu'Actif »*), et c'est DÉLIBÉRÉ : l'owner a validé 61 % en Ambient ET
 *    trouvé 61 % un peu faible en Actif, dans la même séance — donc si les deux
 *    états doivent différer, c'est ACTIF qui doit monter, ⛔ pas Ambient qui
 *    doit descendre. C'est AC6 qui le tranche, PAR LA MESURE, ⛔ pas ce bloc.
 * ⇒ RÉGLABLE À CHAUD (`bl auto ambiant <n>`) : l'arbitrage se tranche SUR LA
 *   DALLE, et une seule séance suffit au lieu de trois reflashs.
 */
#define DN_ENV_BL_AMB_ECHELLE_DEFAUT 100

/*
 * ~~🔴 LE PLANCHER D'AMBIENT EST UN TROISIÈME CONTENU, ET IL N'A JAMAIS ÉTÉ~~
 * ~~   MESURÉ — dn4-19/AC3.4. ⛔ CE `8` EST UN POINT DE DÉPART, PAS UN CONSTAT.~~
 * ~~⇒ Il est RÉGLABLE À CHAUD (`bl auto ambiant plancher <n>`) et la séance~~
 * ~~  d'AC7.1 le tranche À L'ŒIL, rideau fermé.~~
 *
 * 🔴 **BARRÉ EN REVUE DE CODE LE 2026-08-27, ⛔ PAS EFFACÉ** — ce bloc était le
 *    cadrage AVANT la séance : il annonçait `8` (la valeur n'existe plus, c'est
 *    **16**) et affirmait *« JAMAIS MESURÉ SUR CE CONTENU-LÀ »* (il l'a été le
 *    jour même). Il était resté **EN TÊTE, ni barré ni effacé, DEVANT le bloc
 *    qui le contredit** — alors que ce même commit barre proprement `~~20~~ ⇒
 *    50`, `~~DÉSARMÉ PAR DÉFAUT~~` et `~~PCT_MAX 40~~`. ⇒ un lecteur qui
 *    s'arrêtait au premier bloc repartait avec le chiffre d'avant.
 * ✅ **CE QUI RESTE VRAI DU BLOC BARRÉ, ET QUI NE SE RÉ-OUVRE PAS** : les trois
 *    planchers ne sont **PAS interchangeables**, parce que *« un plancher de
 *    lisibilité est une propriété du COUPLE duty × contenu, pas du duty seul »*
 *    — c'est écrit vingt lignes plus haut, et c'est exactement pourquoi le 3 %
 *    de `dn1-3` n'a pas été invalidé quand le 8 % l'a remplacé. Le détail des
 *    trois est repris tel quel dans le bloc ci-dessous.
 */
/*
 * ✅ `dn4-19`, 2026-08-27 — **MESURÉ, ⛔ PLUS UN POINT DE DÉPART.**
 *    Balayage 3 / 6 / 8 / 12 / 16 % conduit **DANS LE NOIR** (BH1750 à **0 lx**,
 *    `brut 0`), **sur le rendu d'Ambient**, avec le plancher de la loi abaissé à
 *    3 % le temps de la manœuvre pour que CE plancher-ci soit celui qui mord.
 *    **Verbatim owner : « 8 % c'est trop bas, 16 c'est bien ».**
 * 🔴 C'EST DONC BIEN UN **TROISIÈME CHIFFRE**, et il est **PLUS HAUT** que les
 *    deux autres — ⛔ à rebours de l'intuition « gros chiffres blancs sur noir,
 *    donc ça se lit plus bas ». Les trois planchers du dépôt :
 *      · `DN_VEILLE_PCT_MIN`   = 3 %  — le Living PCB et son label (dn1-3/AC7)
 *      · `DN_ENV_BL_PCT_MIN`   = 8 %  — le dashboard à six cases, texte fin
 *      · celui-ci              = 16 % — le rendu d'AMBIENT
 * ⛔ AUCUN DES DEUX AUTRES N'EST INVALIDÉ : ils ne portent pas sur ce contenu.
 *    *« Un plancher de lisibilité est une propriété du COUPLE duty × contenu. »*
 */
#define DN_ENV_BL_AMB_PCT_MIN_DEFAUT 16

/* ⛔ LES BORNES PHYSIQUES DE L'INA219 SONT RETIRÉES — correct-course du
 * 2026-08-20. Elles n'avaient de sens que pour un seau `err_bornes` sur des
 * grandeurs qu'on ne publie plus. Elles restent consultables dans l'historique
 * (`git log -S DN_ENV_INA219_BUS_MAX_MV`) et leurs sources sont TI SBOS448G
 * §8.5.1 / §8.6.2 — à ressortir telles quelles si le shunt est un jour câblé. */

/*
 * Ouvre les trois devices et pose leur configuration. NON FATALE.
 *
 * 🔴 ORDRE D'APPEL — CORRIGÉ EN REVUE DE CODE LE 2026-08-20, PAR AJOUT.
 *   ⛔ Ce docblock disait « à appeler APRÈS `dn_console_start()` — même contrat
 *   que `dn_capteurs_init()` ». **LES DEUX MOITIÉS ÉTAIENT FAUSSES** : le boot
 *   appelle `dn_capteurs_init()` en `desknode_main.c:331` et `dn_env_init()` en
 *   `:348`, tous deux **AVANT** `dn_console_start()` (`:375`).
 *   ✅ **L'ordre RÉEL fait autorité — décision owner du 2026-08-20** (*« on fait
 *   confiance au code testé qui marche »*) : `dn_env_init()` s'appelle **APRÈS
 *   `dn_display_init()`** (elle a besoin du bus I²C) et **APRÈS
 *   `dn_capteurs_init()`** (c'est `dn_capt` qui la cadence), **AVANT**
 *   `dn_console_start()`.
 *   ⚠️ Ce qui compte vraiment, et qui EST tenu : **l'init est NON FATALE**, donc
 *   la console démarre quoi qu'il arrive — c'est la propriété qu'AC2 visait.
 *   ⛔ Un contrat que le boot dément est un instrument qui ment : il se corrige
 *   ici, pas dans le boot.
 * ⚠️ Les devices sont ouverts UNE FOIS et GARDÉS. ⛔ Surtout pas le patron
 *   « ajouter/retirer à chaque lecture » de la console : ce serait ~5
 *   `i2c_master_bus_rm_device()` par cycle, et ce retrait A REFUSÉ POUR DE VRAI,
 *   1 fois sur 13, sur cette carte (§13.17.3).
 * Rend toujours ESP_OK sauf si le bus lui-même est indisponible : un capteur
 * absent au boot est un état NORMAL, retenté toutes les minutes.
 */
esp_err_t dn_env_init(void);

/*
 * UN cycle de lecture des trois capteurs. Appelée par la tâche `dn_capt`.
 * ⛔ Ne contient AUCUN `vTaskDelay`.
 *
 * 🔴 COÛT DE BLOCAGE — RECOMPTÉ EN REVUE DE CODE LE 2026-08-20.
 *   ⛔ Ce docblock annonçait « jamais plus de 3 × DN_ENV_I2C_TIMEOUT_MS par
 *   capteur » (300 ms). **C'ÉTAIT FAUX, et le site d'appel le recopiait.**
 *   Compte RÉEL des transactions, pire cas, chacune bornée par
 *   DN_ENV_I2C_TIMEOUT_MS :
 *     · BH1750  : 1 lecture nue                              -> 1 ×
 *     · INA219  : 1 conformité + 4 registres (BUS/SHUNT/I/P) -> 5 ×
 *     · VL6180X : 2 conformité + 1 identité                  -> 3 ×
 *       … et sur conformité PERDUE, + 4 écritures de reconfiguration -> 6 ×
 *   ⇒ **pire cas par capteur : 6 × DN_ENV_I2C_TIMEOUT_MS**, et **pire cas par
 *     cycle : ~12 ×**, soit ~1,2 s de la période de 5 s de `dn_capt`.
 *   ⚠️ Ce pire cas ne se présente qu'à FROID (timeouts plutôt que NACK), sur le
 *   bus que le dépôt nomme « le PREMIER AGRESSEUR CONNU » de la famine DMA, et
 *   par-dessus un BME680 qui peut bloquer 1 500 ms. ⛔ **La famine DMA d'AC12 a
 *   été rejouée sur un bus SAIN : ce pire cas n'a PAS été exercé.**
 */
void dn_env_cycle(void);

/* ── Lecture de l'état publié ─────────────────────────────────────────────────
 * Toutes ces fonctions rendent DN_ENV_ABSENT tant qu'aucune valeur valide n'a
 * été publiée. ⛔ Le transport reste en ENTIERS : c'est l'AFFICHAGE qui porte la
 * précision, jamais le fil. */

/* BH1750 — lux ENTIERS (411 = 411 lx). Conversion : lux = brut / 1,2 au MTreg
 * par défaut (69), dixième TRONQUÉ. ⛔ NE JAMAIS republier des « lux » divisés
 * par dix : `lux10 = (brut * 10) / 12` EST déjà la valeur en lux entiers, et
 * l'avoir imprimée comme des dixièmes a publié « 4 614,8 » pour 46 148, TROIS
 * FOIS, parce que le chiffre était PLAUSIBLE. */
int dn_env_lux(void);
int dn_env_lux_brut(void); /* le compte 16 bits nu, pour le diagnostic */

/* INA219 — la tension de BUS en mV, la tension de SHUNT en µV (SIGNÉE), le
 * courant en mA (SIGNÉ) et la puissance en mW.
 * 🔴 CE QU'ILS MESURENT AUJOURD'HUI EST NOMMÉ, et ce n'est PAS le rail du
 *    module : `Vin+`/`Vin-` NE SONT PAS CÂBLÉS (README.md:916). Voir dn_env.c. */
/* ⛔ LES QUATRE ACCESSEURS DE L'INA219 SONT RETIRÉS — correct-course du
 * 2026-08-20, décision owner. `Vin+`/`Vin−` ne sont pas câblés ⇒ ils ne
 * pouvaient rendre que du BRUIT sur une entrée flottante, pour 5 transactions
 * I²C sur les 9 du cycle (56 %). Le composant reste SOUDÉ et OUVERT, il n'est
 * plus LU. Motifs complets dans `dn_env.c`, au-dessus de `lire_vl6180x()`. */

/* 🔴 LECTURE GROUPÉE — le cycle publie `lux` et `brut` sous UN SEUL verrou ; un
 * lecteur qui prend deux sections critiques peut imprimer un tuple qui n'a jamais
 * existé (`411 lx (brut 500)`). C'est le défaut « CR dn4-2 — LECTURE ATOMIQUE »,
 * réintroduit pour ce module et corrigé en revue de code le 2026-08-20. */
void dn_env_lux_lire(int *lux, int *brut);

dn_env_etat_t dn_env_etat(dn_env_id_t id);
const char *dn_env_etat_nom(dn_env_etat_t e);
const char *dn_env_nom(dn_env_id_t id);
uint8_t dn_env_adresse(dn_env_id_t id);
bool dn_env_present(dn_env_id_t id); /* le device est OUVERT (≠ il répond) */

/*
 * ── 🔴 ACCÈS AU VL6180X PAR LE HANDLE **PERSISTANT** (dn4-7, 2026-08-21) ─────
 *
 * ⛔ NE PAS ouvrir un device à la volée pour parler au ToF. MESURÉ le
 *    2026-08-21, A/B sur le MÊME capteur au MÊME instant :
 *      · `dn_env` (ce handle-ci, ouvert une fois)      : 22 lectures, i2c 0
 *      · console (ajout/retrait de device à CHAQUE appel) : 2 réussites / 15
 *    ⇒ le chemin « ouvre-ferme » s'effondre sous la répétition rapide, et il a
 *      FABRIQUÉ un diagnostic d'intermittence matérielle qui était faux
 *      (§13.21.12). ⚠️ Le mécanisme exact reste OUVERT ; l'A/B, lui, est établi.
 *
 * ⚠️ ENTRELACEMENT : la tâche `dn_capt` lit ce même device toutes les 5 s. C'est
 *    SANS DANGER pour une campagne de portée parce que `dn_env` ne fait que des
 *    LECTURES sur le ToF — il n'écrit rien en régime, donc il ne peut ni
 *    effacer une interruption (seul `0x015` le fait) ni changer un réglage.
 *    ⛔ Si un jour `dn_env` se met à ÉCRIRE en régime, cette garantie tombe.
 */
esp_err_t dn_env_tof_lire(uint16_t reg, uint8_t *buf, size_t n);
esp_err_t dn_env_tof_ecrire(uint16_t reg, uint8_t val);

/* Âge de la dernière lecture valide, en µs. -1 si jamais lue. */
int64_t dn_env_age_us(dn_env_id_t id);

/* Durée MESURÉE du dernier cycle complet (les trois capteurs), en µs. */
int64_t dn_env_duree_cycle_us(void);

/* Nombre de cycles reçus depuis le boot. 🔴 ZÉRO = « JAMAIS CADENCÉ » : la tâche
 * `dn_capt` n'a pas démarré, et ce module ne peut RIEN dire. */
uint32_t dn_env_cycles(void);

void dn_env_compteurs(dn_env_id_t id, dn_env_compteurs_t *out);
void dn_env_compteurs_reset(void);

/* ── Rétroéclairage automatique (AC5) ─────────────────────────────────────────
 * 🔴 `dn_display_backlight_pct()` n'a AUCUN VERROU et `s_backlight_pct` est un
 * `int` nu. Les deux appelants d'aujourd'hui (boot, REPL) ne coexistent jamais ;
 * l'auto en ajoute un TROISIÈME. ⇒ `bl <n>` et `bl ramp` DÉSARMENT l'auto et le
 * DISENT, sinon un `bl 50` tapé en séance serait écrasé au cycle suivant SANS UN
 * MOT, et le constat owner mesurerait la boucle en croyant mesurer la commande. */
bool dn_env_bl_auto(void);
void dn_env_bl_auto_set(bool on);
/* Désarme l'auto SI elle était armée, et rend true dans ce cas — pour que
 * l'appelant puisse le DIRE. */
bool dn_env_bl_auto_desarmer(const char *par_qui);
/* Réglages à chaud : la story exige que l'arbitrage se tranche SUR LA DALLE. */
esp_err_t dn_env_bl_bornes_set(int lux_bas, int lux_haut);
esp_err_t dn_env_bl_pas_set(int pas);
/* 🔴 Le plancher est réglable À CHAUD — voir le bloc de motifs ci-dessus : la
 * séance du 2026-08-20 a prouvé que c'est LUI que l'œil déplace, pas les lux. */
esp_err_t dn_env_bl_plancher_set(int pct);
int dn_env_bl_plancher(void);
void dn_env_bl_etat(int *lux_bas, int *lux_haut, int *pas, int *hyst,
                    int *dernier_pct, int *dernier_lux);
/* Le pct que la loi rendrait POUR CE LUX — exposé pour que la console puisse
 * imprimer la loi sans l'appliquer.
 * ⚠️ `dn4-19` : cette fonction était exposée EXPRÈS pour ça et n'avait AUCUN
 *    APPELANT — la prédiction « 61 % » de la séance du 2026-08-27 a donc été
 *    calculée À LA MAIN, ce que les règles du dépôt interdisent. `bl loi [lux]`
 *    est son appelant, livré par `dn4-19`.
 * 🔴 **RECTIFIÉ EN REVUE DE CODE LE 2026-08-27, ⛔ PAS EFFACÉ** : la phrase
 *    ci-dessus **n'est plus exacte**. `bl loi` passe par `dn_env_bl_loi_regime()`
 *    et `dn_env_bl_loi_simule()` — il doit imprimer les DEUX régimes et les DEUX
 *    courbes, ce que cette entrée-ci ne sait pas faire. Elle n'a donc, à nouveau,
 *    **aucun appelant hors de `dn_env.c`**.
 * ✅ ELLE EST GARDÉE DÉLIBÉRÉMENT, et voici pourquoi — ⛔ ne pas la supprimer au
 *    prochain ménage : c'est **le nom stable de la loi** (régime ACTIF, courbe
 *    courante, ⛔ sans mise à l'échelle), cité par le `README`, par
 *    `hardware/…-capteurs-i2c.md` et par `dn4-3`. La retirer casserait ces
 *    renvois pour une économie de trois lignes.
 * ⚠️ ⛔ **CE QUE LA REVUE RETIENT DE CET ÉPISODE** : le commit qui a livré
 *    `bl loi` a écrit ici *« voici son appelant »* — une étiquette juste **le
 *    jour même**, fausse **six jours plus tard**. Une ligne de docblock qui
 *    nomme un appelant se périme au premier refactor ⇒ **dire ce que la
 *    fonction EST, ⛔ pas qui l'appelle.** */
int dn_env_bl_loi(int lux);

/* ── 🔴 LA FORME DE LA LOI (`dn4-19`/AC6.3) ───────────────────────────────────
 * Le ledger portait l'entrée *« LE DUTY LEDC N'EST PAS LINÉAIRE EN LUMINOSITÉ
 * PERÇUE — mesuré par l'œil de l'owner »*, avec **deux** leviers nommés et la
 * consigne *« ne rien changer sans un besoin exprimé »*. Le besoin a été
 * exprimé le 2026-08-27 : **A/B en ACTIF, ≥ 3 niveaux, lux relevé à chaque
 * point ⇒ verbatim « 75 % — nettement plus »**, là où la loi linéaire rendait
 * **44 %** (à 245 lx).
 *
 * 🎯 DES DEUX LEVIERS, LE LOGARITHME GAGNE, ET ⛔ PAS PAR GOÛT :
 *   · un **gamma** aurait dû être CALÉ sur le point de l'owner (γ ≈ 3,0), et il
 *     produisait alors un **coude brutal** juste au-dessus de `LUX_BAS` :
 *     8 % à 20 lx puis **27 % à 25 lx**, un saut que personne n'a validé ;
 *   · la **loi logarithmique n'a AUCUN paramètre à caler** et retombe sur le
 *     constat : `8 + 92 × ln(245/20)/ln(600/20)` = **76 %**, pour un owner qui a
 *     dit **75 %**. Et son motif était déjà écrit au ledger : *« l'œil et le lux
 *     sont tous deux logarithmiques »*.
 *
 * ⚠️ LES DEUX BORNES SONT PRÉSERVÉES À L'IDENTIQUE : `PCT_MIN` à `LUX_BAS`,
 *    `PCT_MAX` à `LUX_HAUT`. ⛔ Aucune des quatre valeurs réglées à l'œil
 *    (8 %, 20 lx, 600 lx, 3 pts) n'est déplacée — c'est la FORME entre les deux
 *    qui change, ⛔ pas les bornes. C'est exactement ce qu'AC6.3 autorise.
 * ✅ ET ELLE RESTE RÉFUTABLE : `bl auto courbe lineaire|log` rebascule À CHAUD,
 *   donc l'ancienne loi reste atteignable sans reflash pour un A/B contradictoire.
 */
typedef enum {
    DN_ENV_BL_COURBE_LOG = 0,   /* défaut dn4-19 */
    DN_ENV_BL_COURBE_LINEAIRE,  /* la loi d'origine, dn4-3 */
} dn_env_bl_courbe_t;

void dn_env_bl_courbe_set(dn_env_bl_courbe_t c);
dn_env_bl_courbe_t dn_env_bl_courbe(void);
const char *dn_env_bl_courbe_nom(dn_env_bl_courbe_t c);

/* ── 🔴 LE RÉGIME (`dn4-19`) ──────────────────────────────────────────────────
 * L'asservissement doit savoir DANS QUEL ÉTAT est la dalle, sinon il asservit
 * Ambient au niveau d'Actif. ⛔ C'est un PUSH, pas un PULL : `dn_ui` le DIT à
 * `dn_env`, et `dn_env` n'appelle JAMAIS `dn_veille` — sans quoi le harnais
 * hôte de `dn3-3` (`tools/verif_veille_dn33.py`, qui compile `dn_veille.c` sur
 * l'hôte) tomberait, et elle est `in-progress`. */
typedef enum {
    DN_ENV_BL_REGIME_ACTIF = 0,
    DN_ENV_BL_REGIME_AMBIENT,
} dn_env_bl_regime_t;

/* ⛔ NE POSE RIEN sur LEDC : dit seulement quel régime vise l'asservissement.
 * C'est l'appelant (la bascule) qui pose le niveau, EN UNE FOIS. */
void dn_env_bl_regime_set(dn_env_bl_regime_t regime);
dn_env_bl_regime_t dn_env_bl_regime(void);

/* La loi, MISE À L'ÉCHELLE DU RÉGIME et bornée par le plancher du régime.
 * ⛔ N'applique rien. */
int dn_env_bl_loi_regime(int lux, dn_env_bl_regime_t regime);

/* 🔴 LA MÊME, POUR UNE COURBE **DONNÉE** — `dn4-19`, revue de code du 2026-08-27.
 * ⛔ N'applique rien ET N'ÉCRIT RIEN : c'est le point. `bl loi` imprimait l'autre
 *   forme en **basculant `s_bl_courbe` puis en le remettant**, depuis la tâche
 *   REPL, pendant que `dn_env_cycle()` tourne dans `dn_capt` sur un S3 bi-cœur
 *   sans affinité — un cycle tombé dans la fenêtre appliquait la MAUVAISE loi
 *   (44 % au lieu de 76 % à 245 lx) pendant que la commande affirmait
 *   `⛔ RIEN N'A ÉTÉ APPLIQUÉ`. ⇒ **une prédiction ne doit JAMAIS écrire l'état
 *   qu'elle lit.** Si une commande veut comparer deux courbes, elle les DEMANDE
 *   toutes les deux ici, ⛔ elle ne bascule pas le module sous les pieds de la
 *   tâche capteurs. */
int dn_env_bl_loi_simule(int lux, dn_env_bl_regime_t regime,
                         dn_env_bl_courbe_t courbe);

/* Le duty de RÉGIME pour le lux COURANT, ⛔ sans l'appliquer.
 * 🔴 Rend `-1` quand la loi NE PEUT PAS PARLER (capteur muet ou périmé) — et
 *    `-1` est un ÉTAT, ⛔ pas un pourcentage : l'appelant doit le tester. C'est
 *    le même piège que `dn_display_backlight_pct_state()`, déjà payé une fois
 *    en revue de code le 2026-08-20. */
int dn_env_bl_cible(void);

/* L'échelle et le plancher du régime AMBIENT, réglables à chaud (AC3.2/AC3.4).
 * ⛔ Le dépôt REFUSE, il n'écrête pas. */
esp_err_t dn_env_bl_amb_echelle_set(int pct);
int dn_env_bl_amb_echelle(void);
esp_err_t dn_env_bl_amb_plancher_set(int pct);
int dn_env_bl_amb_plancher(void);

/* 🔴 LE COMPTEUR D'APPLICATIONS — `dn4-19`/AC8.
 * Avant cette story la loi tournait RAREMENT (désarmée par défaut, désarmée par
 * la veille). Après, elle tourne H24 sous éclairage domestique : le pompage de
 * la bande morte, déclaré « JAMAIS EXERCÉ » au ledger, DEVIENT EXERÇABLE. Ce
 * compteur le rend mesurable sur une fenêtre longue au lieu d'être jugé à
 * l'œil : deux relevés espacés donnent le nombre de mouvements de duty. */
uint32_t dn_env_bl_applications(void);

/* 🔴 LE DERNIER DUTY QUE LA LOI A **PHYSIQUEMENT POSÉ** — `dn4-19`, revue du
 *   2026-08-27. ⛔ **CE N'EST PAS** le `dernier_pct` de `dn_env_bl_etat()** : ce
 *   dernier est une SENTINELLE D'AFFICHAGE que `bl auto on` remet à `-1` exprès
 *   (pour que `bl` ne prétende pas « la loi a appliqué ça » juste après un
 *   armement — corrigé en revue le 2026-08-20, et ça RESTE).
 * ⇒ Celle-ci suit **LA DALLE**, ⛔ pas l'armement, et elle n'est **jamais
 *   remise**. C'est ce qu'il faut pour répondre à *« ce duty, est-ce la loi qui
 *   l'a mis, ou un doigt ? »* — la question du garde-fou du réveil (AC2.4).
 *   S'appuyer sur la sentinelle produisait DEUX fausses accusations : `bl auto
 *   off` (qui ne touche pas le duty) et `bl auto on` (qui efface la sentinelle).
 * 🔴 Rend `-1` tant que la loi n'a rien posé depuis le boot : un ÉTAT, ⛔ pas un
 *   pourcentage. L'appelant DOIT le tester. */
int dn_env_bl_dernier_pose(void);

/*
 * ── 🔴 W2 — LE CRITÈRE « UNE CASE DE SIX DOIT BOUGER », MESURÉ DANS LE FIRMWARE
 *
 * Patron `FAN_RPM` de `dn4-6`, jugé sur la **valeur AFFICHÉE**, ⛔ jamais sur la
 * source : **étendue >= 5** · **taux de changement du TEXTE >= 10 %** · **σ >= 1**.
 * Référence : `FAN_RPM` 13 / 55,2 % / 2,02 (n=959) QUALIFIE ; son témoin de
 * contrôle `ASIC_POWER` 3 / 57,9 % / 0,75 NE QUALIFIE PAS.
 *
 * ⚠️ POURQUOI DANS LE FIRMWARE ET PAS PAR ÉCHANTILLONNAGE DEPUIS WSL :
 *   `tools/dn_console.py` PERD DES LIGNES (mesuré, y compris en invocation solo,
 *   et deux captures ENTIÈREMENT VIDES le 2026-08-20). Un taux de changement
 *   calculé sur un échantillonnage qui perd des points est **faux**, et faux
 *   d'un biais qu'on ne sait pas borner. L'accumulateur, lui, voit TOUS les
 *   cycles.
 *
 * 🔴 ET IL Y A PLUSIEURS PISTES, PAS DEUX, PARCE QUE X2 EST UN CHOIX ENTRE DEUX
 *    CANDIDATS : comparer le lux et la pression avec deux instruments différents
 *    ne prouverait rien. Et pour la pression, la PRÉCISION est justement ce qui
 *    est en jeu (AC11 : ⛔ aucune décimale que la source ne porte) ⇒ les deux
 *    formatages sont accumulés SÉPARÉMENT, et le choix se fait sur les chiffres.
 * ⚠️ CE BLOC A DIT « QUATRE PISTES » JUSQU'AU 2026-08-25 ALORS QU'IL Y EN AVAIT
 *    CINQ (le gaz MOX est arrivé après), et six depuis `dn3-3`. ⛔ On ne grave
 *    plus le compte dans la prose : `DN_W2_NB` fait foi.
 *
 * 🔴 LA CADENCE EST **PAR PISTE** DEPUIS `dn3-3`, ⛔ PLUS GLOBALE.
 *    Les cinq pistes capteurs battent à `DN_ENV_PERIODE_MS` (5 s) ; la piste
 *    `DN_W2_CPU_DIX` bat à `DN_W2_CADENCE_CPU_MS` (1 s). ⇒ **la fenêtre d'une
 *    piste vaut n × SA cadence**, et deux taux de cadences différentes ne se
 *    comparent pas sans le dire. `dn_w2_cadence_ms()` la publie.
 */

/* La cadence de la piste CPU : le tick 1 Hz de `dn_ui.c` (`hist_tick`). */
#define DN_W2_CADENCE_CPU_MS 1000
typedef enum {
    DN_W2_LUX = 0,          /* BH1750, en lux ENTIERS (sa seule précision utile) */
    DN_W2_PRESSION_ENT,     /* BME680, en hPa ENTIERS      (« 1013 hPa »)        */
    DN_W2_PRESSION_DIX,     /* BME680, en DIXIÈMES de hPa  (« 1013,2 hPa »)      */
    DN_W2_TEMPERATURE_DIX,  /* témoin de CONTRÔLE : une grandeur DÉJÀ affichée   */
    DN_W2_GAZ_KOHM,         /* BME680 MOX, en kOhm — ⚠️ seulement `capteurs gaz on` */
    /*
     * 🔴 dn3-3 / AC2.1 — LA SIXIÈME PISTE, ET LA SEULE QUI PORTE UNE CASE
     *    NOURRIE PAR LE PC. Elle existe parce que **AC2.1 N'AVAIT AUCUN
     *    INSTRUMENT** : la story et `hardware/` §24.13 nommaient `w2`, alors que
     *    ses cinq appelants étaient TOUS des capteurs locaux. Constat du
     *    2026-08-25, relu dans le source.
     *
     * Valeur échantillonnée : `s_dx[CPU][0]`, c'est-à-dire **le nombre que le
     * texte montre** — la grandeur 0 de `CPU` est déclarée `DN_PREC_DIXIEME`,
     * donc le dixième EST l'affichage. ⛔ Jamais la source.
     *
     * 🔴 TROIS DÉCISIONS DE CONCEPTION, ET CHACUNE A SON MOTIF ÉCRIT :
     *
     * 1. **1 Hz, ⛔ pas 5 s.** AC2.1 juge sur **60 s**. À 5 s ça ne fait que
     *    **12 échantillons, donc 11 transitions** — et le seuil de taux vaut
     *    **10 %** quand le PAS du dénominateur vaut **9,1 %** : un seuil plus
     *    fin que le pas de son dénominateur n'est pas tranchable. À 1 Hz :
     *    60 échantillons, 59 transitions, pas de **1,7 %**.
     *
     * 2. **AMBIENT SEULEMENT.** AC2.1 dit « en Ambient ». Or pendant un tir sous
     *    agent réel **il n'y a PAS de console** (branche A : le REPL EST le
     *    transport PC), donc ⛔ **aucun `w2 reset` ne peut délimiter la fenêtre
     *    depuis l'extérieur**. En n'accumulant qu'en Ambient, la piste est
     *    self-délimitée : tout échantillon qu'elle porte est un échantillon
     *    d'Ambient, quelle que soit l'heure de lecture.
     *    ⚠️ Conséquence à dire : cette piste **ne peut pas** servir à comparer
     *    Actif et Ambient. Ce n'est pas ce qu'AC2.1 demande.
     *
     * 3. **LES ÉPISODES SONT SÉPARÉS PAR UNE RUPTURE.** La veille tombe et se
     *    lève des dizaines de fois par nuit ; concaténer les épisodes ferait
     *    compter comme « changement de texte » un saut qui n'est qu'une reprise.
     *    ⇒ `dn_w2_desamorcer()` à chaque sortie d'Ambient (et sur toute valeur
     *    invalide), et les ruptures sont **RETIRÉES DU DÉNOMINATEUR**.
     */
    DN_W2_CPU_DIX,
    DN_W2_NB,
} dn_w2_id_t;

typedef struct {
    uint32_t n;          /* échantillons */
    int32_t min, max;    /* de la valeur AFFICHÉE */
    uint32_t changements;/* nb d'échantillons dont le TEXTE diffère du précédent */
    /*
     * 🔴 dn3-3 — CHAÎNES BRISÉES : fin d'un épisode Ambient, ou valeur invalide.
     * L'échantillon qui SUIT une rupture n'a **pas de prédécesseur légitime** :
     * il ne peut donc être ni un changement, ni une transition. ⇒ le
     * dénominateur du taux vaut `n - 1 - ruptures`, ⛔ pas `n - 1`.
     * ⚠️ Sans ce retrait, le biais irait TOUJOURS vers « NE QUALIFIE PAS »
     *    (dénominateur gonflé) — c'est-à-dire vers le même sens que les deux
     *    défauts de troncature corrigés le 2026-08-20.
     */
    uint32_t ruptures;
    int64_t somme;
    int64_t somme_carres;
} dn_w2_t;

/* Un échantillon de la valeur telle qu'elle SERAIT AFFICHÉE. */
void dn_w2_echantillon(dn_w2_id_t id, int32_t valeur_affichee);

/*
 * 🔴 BRISE LA CHAÎNE : l'échantillon SUIVANT n'aura pas de prédécesseur.
 * Appelée à chaque sortie d'Ambient et sur toute valeur invalide. ⛔ Elle ne
 * jette AUCUN échantillon déjà pris — elle empêche seulement d'inventer une
 * transition entre deux instants que rien ne relie.
 * ⚠️ IDEMPOTENTE : deux appels d'affilée ne comptent qu'UNE rupture. Sinon un
 *    module en Actif pendant huit heures gonflerait `ruptures` de 28 800 et
 *    rendrait le dénominateur négatif.
 */
void dn_w2_desamorcer(dn_w2_id_t id);

/* La cadence de CETTE piste, en ms. ⛔ Elle n'est plus globale : voir le bloc
 * de tête. La fenêtre d'une piste vaut `n × dn_w2_cadence_ms(id)`. */
uint32_t dn_w2_cadence_ms(dn_w2_id_t id);
void dn_w2_lire(dn_w2_id_t id, dn_w2_t *out);
void dn_w2_reset(void);
const char *dn_w2_nom(dn_w2_id_t id);

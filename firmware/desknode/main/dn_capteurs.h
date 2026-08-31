#pragma once
/*
 * dn_capteurs — les capteurs environnementaux de DeskNode (dn2-1, P4).
 *
 * Aujourd'hui : UN capteur, le BME680 (température + humidité). Le nom est celui
 * de la FONCTION, pas de la puce — comme dn_touch, dn_link, dn_display — parce
 * que dn4-2 a ajouté BH1750, TOF050C-VL6180X et INA219 sur le même bus
 * (⚠️ « dn4-1 » et « VL53L0X » étaient DEUX étiquettes fausses — cf. dn_pins.h). ⚠️ Il n'est pour
 * autant PAS généralisé d'avance : une abstraction écrite pour trois capteurs
 * qu'on n'a pas encore vus serait une supposition, pas une conception.
 *
 * ── CE QUE LE MATÉRIEL IMPOSE, ET QUI EST MESURÉ (hardware/…-capteurs-i2c.md §13)
 *
 *  · Adresse **0x77** — MESURÉE, pas supposée : le breakout tire SDO à VCC.
 *    (0x76 est l'autre possibilité du BME680 ; ce module n'y répond pas.)
 *  · Identité vérifiée à l'init : chip id (0xD0) = 0x61, variant (0xF0) = 0x00.
 *    ⚠️ 0x61 seul ne suffit PAS : il vaut aussi pour le BME688. Et un module
 *    vendu « BME680 » peut porter un BME280 (0x60) ou un BMP280 (0x58), qui
 *    n'ont pas de capteur de gaz — voire pas d'humidité du tout.
 *  · Le bus est PARTAGÉ avec la dalle (TCA9554 0x20), le tactile (GT911 0x5D,
 *    polé ~30 Hz), la RTC (0x51) et l'IMU (0x6B). ⛔ Le handle vient de
 *    dn_display_i2c_bus() ; jamais un second i2c_new_master_bus().
 *
 * ── 🔴 POURQUOI UNE TÂCHE DÉDIÉE, ET PAS UN APPEL DEPUIS LA CONSOLE ──────────
 *
 * `bme680_get_data()` du composant retenu BOUCLE jusqu'à **1 500 ms** en
 * attendant que la mesure soit prête (BME680_DATA_POLL_TIMEOUT_MS), et chaque
 * transaction I²C a 500 ms de timeout propre. Or, depuis dn2-2, **le REPL EST le
 * transport PC** (branche A) : une commande console qui dort bloque la liaison
 * pendant toute sa durée. C'est exactement le défaut de `cpu N`, trouvé en
 * session de validation dn2-2 — il mesurait le dashboard au repos quel que soit
 * le trafic, parce qu'il bloquait le transport qu'il prétendait mesurer.
 * ⇒ La lecture vit ICI, dans sa tâche. La commande `capteurs` ne fait que LIRE
 *   ce que cette tâche a publié — elle ne déclenche jamais une mesure.
 * ⛔ Et jamais depuis la tâche LVGL non plus : dn_ui prend le verrou lui-même,
 *   l'appelant JAMAIS (règle du dépôt).
 *
 * ── L'ÉTAT (la doctrine AC7 de dn2-2, transposée) ────────────────────────────
 *
 * Le firmware ne suppose JAMAIS que la lecture a réussi. Une seule règle, en
 * temps absolu : âge = maintenant − horodatage de la dernière lecture VALIDE.
 * Au-delà de DN_CAPT_PEREMPTION_US, l'état est MUET et les cases affichent
 * « -- » au lieu de figer un chiffre qui n'a plus cours. Un capteur débranché
 * qui laisserait 21,4 °C à l'écran est un mensonge d'interface.
 */

#include <stdbool.h>
#include <stdint.h>
#include "esp_err.h"

/* Adresse et registres d'identité : voir dn_pins.h (DN_BME680_ADDR), qui est LA
 * source unique du brochage et porte le constat qui l'établit. */
#define DN_BME680_REG_CHIP_ID 0xD0
#define DN_BME680_REG_VARIANT 0xF0
#define DN_BME680_CHIP_ID 0x61    /* BME680 ET BME688 — le variant tranche */
#define DN_BME680_VARIANT_680 0x00
#define DN_BME680_VARIANT_688 0x01

/*
 * ⚠️ CADENCE — 5 s, et c'est un ARBITRAGE À TROIS ENTRÉES, pas un chiffre rond.
 *
 *  1. FIDÉLITÉ : une pièce ne change pas à 1 Hz. Le brief demande « ~1 mesure/s »
 *     pour les métriques PC ; l'ambiance n'en a aucun besoin.
 *  2. AUTO-ÉCHAUFFEMENT : chaque cycle chauffe le die (voir DN_CAPT_GAZ). Moins
 *     souvent = moins chaud. C'est la variable qui coûte des DEGRÉS sur le
 *     livrable même de la story.
 *  3. BUDGET DE REDESSIN : dn2-2 a mesuré **+0,53 point de CPU par case vivante
 *     et par redessin**. La cadence n'est donc pas qu'une question de capteur,
 *     c'est une dépense d'affichage — et deux cases à 5 s coûtent ~10× moins
 *     qu'à 1 Hz. Chiffre à confronter en T10, legs pour dn3-2.
 */
#define DN_CAPT_PERIODE_MS 5000

/*
 * dn4-5 / AC6.1 — LA PHRASE DU RETARD, RENDUE PAR LE MODULE LUI-MÊME.
 * ⛔ Ne pas la recopier côté console : c'est très exactement comme ça qu'on
 *    obtient deux vérités qui divergent. Elle est définie UNE FOIS dans
 *    `dn_capteurs.c` (`DN_CAPT_RETARD_TXT`), citée par le docblock du même
 *    fichier, et une gate refuse que les deux s'écartent.
 */
const char *dn_capt_retard_txt(void);
/* 3 périodes, comme dn_link prend 3 périodes de l'agent. Assez court pour que
 * l'état menteur dure peu, assez long pour survivre à une lecture ratée isolée. */
#define DN_CAPT_PEREMPTION_US (3LL * DN_CAPT_PERIODE_MS * 1000)

/*
 * 🔴 CHAUFFAGE DU GAZ — DÉSACTIVÉ, ET C'EST LE CHOIX LE PLUS LOURD DU MODULE.
 *
 * Le BME680 mesure les COV en portant une plaque à 200-400 °C pendant 100-300 ms
 * par cycle. Cette énergie chauffe le die — donc le capteur de TEMPÉRATURE, qui
 * est sur le même silicium. Le défaut du composant retenu est `gas_enabled=true`
 * à 300 °C / 300 ms.
 *
 * Or le gaz/IAQ n'est PAS au dashboard : le brief fige SIX widgets, et aucun
 * n'est un indice de qualité d'air. Allumer une plaque chauffante à côté du
 * thermomètre pour une donnée qu'on n'affiche pas serait payer des degrés pour
 * rien.
 * ⚠️ C'est un choix ARBITRÉ, pas un défaut subi — et il se MESURE : l'A/B
 *    gaz ON contre gaz OFF, à cadence identique, est le T9 de la story. Ce
 *    drapeau existe pour que l'A/B soit jouable sans reflasher deux firmwares.
 */
#define DN_CAPT_GAZ_DEFAUT false

/*
 * Les libellés de la configuration DEMANDÉE, à côté des constantes qu'ils
 * décrivent — c'est `capteurs` qui les imprime.
 * ⚠️ Ils vivaient en littéral codé en dur DANS la console, une ligne sous
 *    « config LUE », c'est-à-dire l'ombre logicielle que §13.10 venait
 *    d'interdire, remise juste en dessous de son correctif (CR 2026-08-17).
 *    Ici, changer `config_voulue()` sans changer le libellé se voit.
 */
#define DN_CAPT_MODE_TXT "FORCED"
#define DN_CAPT_OSR_TH_TXT "8x"
#define DN_CAPT_OSR_P_TXT "1x"
#define DN_CAPT_IIR_TXT "3"

typedef enum {
    DN_CAPT_JAMAIS, /* aucune lecture valide depuis le boot */
    DN_CAPT_VIVANT, /* dernière lecture plus récente que la péremption */
    DN_CAPT_MUET,   /* la péremption est passée — les cases doivent le dire */
    /* 🔴 `dn4-41` — LE 4ᵉ ÉTAT. « JAMAIS SOUDÉ » ⛔ N'EST PAS « MUET ».
     * `DN_CAPT_ABSENT_SEUIL` ré-ouvertures CONSÉCUTIVES ont échoué, chacune sur
     * une **lecture de registre d'IDENTITÉ** (`relever_identite()`) — donc une
     * transaction de DONNÉE, ⛔ jamais un scan ni `i2c_master_probe()`.
     * ⚠️ MÊME MOT que `DN_ENV_ABSENT`, et c'est délibéré : *« deux modules qui
     *    comptent la même chose sous deux noms sont deux instruments qu'on ne
     *    peut pas comparer »* (docblock de `dn_env_compteurs_t`). */
    DN_CAPT_ABSENT,
} dn_capt_etat_t;

/*
 * 🔴 `dn4-41` / AC2.1 — LE SEUIL, ET IL EST CONTRAINT PAR LA MESURE.
 * Au démarrage à FROID la lecture d'identité **échoue TOUJOURS**, et le bus
 * entier se dégrade ~40 s avant de se rétablir SEUL vers T+~60 s (§13.17.1).
 *   seuil × DN_CAPT_REINIT_CYCLES × DN_CAPT_PERIODE_MS = 2 × 12 × 5 000
 *   = **120 s**, soit 2× la fenêtre froide.
 * ⚠️ La tentative du BOOT (`dn_capteurs_init()`) ⛔ NE COMPTE PAS.
 * ⛔ Le miroir de `DN_ENV_ABSENT_SEUIL` : les deux modules doivent rendre le même
 *   verdict au même moment, et `tools/verif_paliers_dn441.py` le garde.
 */
#define DN_CAPT_ABSENT_SEUIL 2

typedef struct {
    uint32_t lectures;      /* lectures VALIDES appliquées */
    uint32_t err_i2c;       /* le transport a échoué (NACK, bus occupé) */
    uint32_t err_donnee;    /* il répond, mais la conversion n'est jamais prête */
    uint32_t err_bornes;    /* valeur hors plage physique du capteur */
    uint32_t reprises;      /* transitions MUET -> VIVANT */
    /* 🔴 `dn4-41` / AC2.4 — LES ENTRÉES EN ABSENCE. ⛔ Les TRANSITIONS vers
     * `DN_CAPT_ABSENT`, pas les cycles passés dedans. Miroir exact de
     * `dn_env_compteurs_t.absences` — même nom, même sens, même unité. */
    uint32_t absences;
    /* 🔴 Poussées vers l'UI PERDUES faute d'avoir pu prendre le verrou LVGL.
     * Ajouté par la revue du 2026-08-17 : la valeur était jetée en silence, donc
     * un écran périmé d'un cycle entier n'avait AUCUNE trace. Ce n'est pas une
     * erreur de capteur — d'où son propre seau, hors des trois causes d'AC7. */
    uint32_t pousses_ratees;
    /* 🔴 Le capteur a PERDU SA CONFIGURATION — compte les DÉTECTIONS, pas les
     * réparations réussies (la réparation peut échouer, et au-delà de trois
     * échecs consécutifs on cesse d'insister : voir DN_CAPT_RECONF_ECHECS_MAX).
     * Compté séparément parce que ce n'est NI une erreur de transport (il
     * répond très bien) NI une valeur aberrante (elle est plausible) : c'est un
     * capteur qui a redémarré sous nos pieds. Mesuré le 2026-08-17 en coupant
     * son 3V3 à chaud : les trois registres de config repassent à 0x00, la
     * compensation Bosch se met à produire 32,8 °C et 100 %RH — des valeurs
     * PARFAITEMENT PLAUSIBLES, donc invisibles à toute borne physique. */
    uint32_t reconfigs;
} dn_capt_compteurs_t;

/*
 * Démarre la tâche de lecture. NON FATALE côté appelant, et c'est délibéré :
 * le seul mode d'échec réaliste est xTaskCreate, c'est-à-dire la pénurie de RAM
 * interne. Avec CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y, un abort donnerait « ni
 * console ni flash, RESET physique obligatoire » — un module optionnel ne doit
 * pas pouvoir briquer le seul outil de diagnostic (leçon dn2-2, correctif de
 * revue sur dn_link_init).
 *
 * ⚠️ À appeler APRÈS dn_ui_init() : la tâche pousse vers les cases par les
 *    fonctions publiques de dn_ui, qui prennent le verrou LVGL elles-mêmes.
 * ⚠️ Une identité de puce inattendue N'EMPÊCHE PAS le démarrage : elle est
 *    JOURNALISÉE et l'état reste JAMAIS. Refuser de démarrer priverait
 *    l'opérateur de `capteurs`, qui est justement ce qui explique pourquoi.
 */
esp_err_t dn_capteurs_init(void);

/*
 * ── 🔴 INJECTEUR DE FAUTES — pour ne PLUS toucher au connecteur ──────────────
 *
 * L'AC7 a été prouvée en débranchant physiquement le fil 3V3 du breakout. Ça a
 * marché, et ça a trouvé trois défauts réels. Mais **un Dupont n'est donné que
 * pour quelques dizaines d'insertions** : chaque cycle desserre ses lamelles, et
 * on dégrade le montage précisément en testant sa robustesse. Constat owner du
 * 2026-08-17, et il est juste.
 *
 * ⇒ Les fautes se rejouent désormais EN LOGICIEL. Chaque cause a son injecteur,
 *   et chacune exerce le VRAI chemin de code, pas une branche parallèle.
 *
 * ⚠️ CE QUE L'INJECTEUR NE PROUVE PAS, ET QUI DOIT RESTER ÉCRIT : il teste le
 *    CHEMIN DE CODE, pas le matériel. Il ne peut pas découvrir un mode de panne
 *    qu'on n'a pas imaginé — l'alimentation fantôme par les diodes ESD, par
 *    exemple, personne ne l'aurait injectée parce que personne ne la soupçonnait.
 *    Il vaut pour la NON-RÉGRESSION, après qu'une campagne physique a établi la
 *    liste des fautes réelles. Cette liste-là a été établie le 2026-08-17.
 */
typedef enum {
    DN_CAPT_FAUTE_AUCUNE,
    DN_CAPT_FAUTE_MUET,   /* le capteur cesse de répondre (transport) */
    DN_CAPT_FAUTE_BORNES, /* valeur hors plage physique */
    DN_CAPT_FAUTE_CONFIG, /* config perdue — le cas « capteur fantôme » */
} dn_capt_faute_t;

/*
 * Arme une faute pour les `cycles` prochains cycles (1..600 ; 0 = désarmer).
 *
 * ⚠️ **`muet` et `bornes` ne font PASSER LES CASES À « -- » qu'au-delà de la
 *    péremption**, c'est-à-dire après DN_CAPT_PEREMPTION_US / DN_CAPT_PERIODE_MS
 *    = **3 cycles**. En dessous, l'injection incrémente bien son compteur mais
 *    l'écran reste légitimement valide — et l'opérateur qui armait 1 cycle pour
 *    « voir les cases passer à -- » concluait que la garde AC7 était cassée.
 *    C'est un comportement CORRECT mal annoncé : `capteurs` le dit maintenant.
 *    (Constat de la revue du 2026-08-17.)
 * ⚠️ `config`, lui, agit **dès le premier cycle** : la perte de configuration
 *    invalide la valeur immédiatement, elle n'attend pas la péremption.
 */
esp_err_t dn_capt_simuler(dn_capt_faute_t f, int cycles);
/* Nombre de cycles au-delà duquel `muet`/`bornes` deviennent VISIBLES à l'écran.
 * Exposé pour que la console l'annonce au lieu de le laisser deviner. */
#define DN_CAPT_CYCLES_AVANT_PEREMPTION \
    (int)(DN_CAPT_PEREMPTION_US / (1000LL * DN_CAPT_PERIODE_MS))
dn_capt_faute_t dn_capt_faute_active(void);
int dn_capt_faute_restants(void);
const char *dn_capt_faute_nom(dn_capt_faute_t f);

dn_capt_etat_t dn_capt_etat(void);
const char *dn_capt_etat_nom(dn_capt_etat_t e);
/* 🔴 `dn4-41` — le compte d'échecs qui PORTE le verdict, pour que la console
 * imprime `ABSENT (n tentatives échouées)` (AC2.6) au lieu de le déduire.
 * ⛔ Non remis par `capteurs reset` : c'est l'état du verdict, pas un seau. */
uint32_t dn_capt_reouv_echecs(void);

/* 🔴 `dn4-41` / AC9.2 — TÉMOIN D'INHIBITION LOGICIELLE, à coût NUL.
 * ⛔ SA LIMITE EST ÉCRITE au-dessus de `s_inhibe` dans `dn_capteurs.c` : ni
 * NACK, ni timeout, ni condition de bus. Il exerce LE CODE, ⛔ pas le matériel.
 * ⚠️ L'armer FERME le driver — sans quoi la lecture de donnée continuerait
 *    d'aboutir et le verdict ne tomberait jamais. */
void dn_capt_inhiber(bool on);
bool dn_capt_inhibe(void);

/* 🔴 `dn4-41` — LE DÉLAI MINIMUM AVANT QU'UN VERDICT « ABSENT » PUISSE TOMBER,
 * en secondes. ⛔ Une FONCTION, pas un macro recopié : `DN_CAPT_REINIT_CYCLES`
 * vit dans `dn_capteurs.c` et doit y RESTER — un second exemplaire dans un
 * en-tête est un chiffre qui se périmera le jour où le backoff bougera, c'est-
 * à-dire le jour où il compte. Le dépôt a déjà payé ce motif (les 22 gates
 * énumérées à la main contre 21 réelles). */
uint32_t dn_capt_absent_delai_s(void);

/*
 * 🔴 SENTINELLE « PAS DE VALEUR » — et pourquoi ce n'est PLUS `-1`.
 *
 * `-1` dixième, c'est **−0,1 °C** : une température parfaitement légitime, dans
 * les bornes physiques du capteur (−40 °C). Tant que la sentinelle vivait dans
 * la plage utile, AUCUNE garde sur la valeur ne pouvait être correcte — et la
 * console en a fait les frais deux fois : d'abord en imprimant « 0,1 C · 0,-1 % »
 * (sentinelle formatée comme une mesure), puis, une fois « corrigée » par un test
 * `t >= 0`, en refusant d'afficher **toute température négative** sous le libellé
 * « aucune valeur courante », pendant que le dashboard, lui, l'affichait.
 * ⇒ La sentinelle sort de la plage physique pour de bon. Constat de la revue de
 *   code du 2026-08-17.
 */
#define DN_CAPT_DX_ABSENT INT32_MIN

/*
 * 🔴 dn4-3 — LES BORNES DE LA PRESSION, ET LEUR SOURCE.
 * Bosch BME680, plage de mesure **300..1100 hPa**. Sans bornes écrites, aucun
 * seau ne pourrait rien comparer (AC1 : « un seau qui n'a rien à comparer est un
 * compteur décoratif »).
 * ⛔ Hors plage, SEULE la pression devient absente : T et RH restent publiées.
 *    Une grandeur qu'on ne fait qu'INSTRUIRE ne doit pas pouvoir éteindre la
 *    seule case vivante de la grille.
 */
#define DN_CAPT_PRESSION_MIN_HPA 300.0f
#define DN_CAPT_PRESSION_MAX_HPA 1100.0f

/*
 * 🔴 ET L'ÉTIQUETTE DU DRIVER MENT SUR L'UNITÉ — MESURÉ, PAS SUPPOSÉ.
 *
 * `bme680_data_t.barometric_pressure` est documenté *« barometric pressure in
 * hecto-pascal »* (`bme680.h:363`). Or `bme680_compensate_pressure()`
 * (`bme680.c:289-300`) est la formule flottante CANONIQUE de Bosch, qui rend des
 * **PASCALS**. La première lecture est sortie HORS de [300, 1100] hPa, ce qui a
 * ouvert la question.
 * ⇒ ⛔ On ne corrige PAS en divisant par 100 « parce que c'est sûrement des Pa ».
 *   On PUBLIE LA VALEUR BRUTE, on détermine l'unité PAR SA MAGNITUDE au premier
 *   relevé valide, et on l'ANNONCE UNE FOIS dans le log. Une unité déduite en
 *   silence est exactement ce qui a publié « 4 614,8 lx » pour 46 148.
 */
typedef enum {
    DN_CAPT_P_UNITE_INCONNUE = 0, /* aucune lecture exploitable encore */
    DN_CAPT_P_UNITE_HPA,          /* le driver tient sa promesse */
    DN_CAPT_P_UNITE_PA,           /* l'étiquette ment, c'est du Pascal */
    DN_CAPT_P_UNITE_ABERRANTE,    /* ni l'un ni l'autre — on ne publie RIEN */
} dn_capt_p_unite_t;

dn_capt_p_unite_t dn_capt_pression_unite(void);
const char *dn_capt_pression_unite_nom(dn_capt_p_unite_t u);
/* La valeur BRUTE rendue par le driver, en dixièmes de SON unité, sans aucune
 * conversion ni borne. `DN_CAPT_DX_ABSENT` si jamais lue. ⛔ C'est l'instrument
 * qui permet de dire « lue mais aberrante » plutôt que « aucune valeur ». */
int dn_capt_pression_brut_dixiemes(void);

/*
 * 🔴 dn4-3 — LA RÉSISTANCE DE GAZ, EN OHMS. Publiée sur DEMANDE DE L'OWNER
 * (2026-08-20 : *« pas hPa mais au moins un statut de qualité de l'air — je fume
 * dans la pièce, ça devrait être facile de tester »*).
 *
 * ⛔ CE N'EST PAS UN INDICE DE QUALITÉ D'AIR, ET IL NE FAUT PAS L'AFFICHER COMME
 *    TEL. Ce qu'on publie est la RÉSISTANCE BRUTE du capteur MOX, en ohms : elle
 *    BAISSE quand des composés organiques volatils sont présents. Elle dépend
 *    aussi de la température, de l'humidité et de l'historique du capteur.
 *
 * 🔴 ET L'`iaq_score` DU COMPOSANT EST INUTILISABLE — TROIS DÉFAUTS LUS AU SOURCE :
 *  1. `bme680.h:369` l'annonce **0..500** ; la formule (`bme680.c:737`) somme
 *     6,5 + 6,5 + 52 ⇒ **maximum réel 65**. Étiquette fausse.
 *  2. `bme680.c:733` écrit `else if (gas >= 13500 && gas > 9000)` — le second
 *     test est IMPLIQUÉ par le premier. L'intention était `>= 9000 && < 13500`.
 *     ⇒ **la bande 9 000..13 500 Ω ne reçoit AUCUN score**, la cascade la
 *     traverse sans rien assigner et `gas_score` garde une valeur RÉSIDUELLE.
 *  3. Le score de température tombe à **0 au-dessus de 26 °C** (`bme680.c:725`).
 *     Or notre capteur lit ~28 °C À CAUSE DE SON PROPRE AUTO-ÉCHAUFFEMENT
 *     (+2,1 °C mesuré, §13.19.8) ⇒ **6,5 points perdus en permanence par un
 *     artefact de montage**, pas par la qualité de l'air.
 * ⇒ un vrai IAQ demande **BSEC** (binaire propriétaire de Bosch), ⛔ pas ceci.
 *
 * ⚠️ ET LE GAZ RESTE COUPÉ PAR DÉFAUT : sa plaque à 300 °C coûte **+0,3 °C et
 *    −2 points de RH** (§13.9, A/B avec témoin négatif) sur les deux seules
 *    grandeurs que la case affiche. `capteurs gaz on` pour un A/B DÉCLARÉ.
 *
 * `DN_CAPT_DX_ABSENT` si le gaz est coupé, ou si aucune lecture valide.
 */
int dn_capt_gaz_ohms(void);
int dn_capt_iaq_brut(void); /* le score du composant, AVEC ses trois défauts */
/* 🔴 TROIS ÉTATS, ⛔ PAS DEUX (revue de code 2026-08-20) : `dn_capt_gaz_ohms()`
 * rend ABSENT quand le chauffeur est coupé, quand aucune lecture valide n'a
 * jamais eu lieu, ET quand le chauffeur tourne sans être encore stable. Ce
 * prédicat isole le troisième cas — sans lui, la console affirmait « chauffeur
 * COUPE » à un opérateur qui venait de l'allumer. */
bool dn_capt_gaz_en_attente(void);

/* Dernières valeurs VALIDES, en DIXIÈMES (233 = 23,3 °C · 471 = 47,1 %).
 * Entiers pour rester dans la doctrine du dépôt côté affichage ; le driver rend
 * des float, la conversion est faite ici, une fois.
 * `DN_CAPT_DX_ABSENT` si aucune valeur valide n'est publiée. */
int dn_capt_temperature_dixiemes(void);
int dn_capt_humidite_dixiemes(void);

/* 🔴 dn4-3 : la pression, en DIXIÈMES de hPa (10132 = 1013,2 hPa).
 * Mesurée par le BME680 depuis dn2-1 et JETÉE jusqu'ici. Publiée pour que X2
 * (la 6ᵉ case) se tranche sur des chiffres, ⛔ pas sur un pronostic.
 * `DN_CAPT_DX_ABSENT` si hors plage physique ou si aucune lecture valide. */
int dn_capt_pression_dixiemes(void);

/* Âge de la dernière lecture valide en µs (esp_timer). -1 si jamais lue. */
int64_t dn_capt_age_us(void);

/* Durée du dernier cycle de mesure réussi, en µs — le « combien coûte une
 * lecture » que T10 doit chiffrer, mesuré et non repris de la datasheet. */
int64_t dn_capt_duree_cycle_us(void);

void dn_capt_compteurs(dn_capt_compteurs_t *out);
void dn_capt_reset_compteurs(void);

/*
 * 🔴 LA CONFIGURATION RELUE DANS LE CAPTEUR — pas celle qu'on lui a demandée.
 *
 * `capteurs` a menti une fois : il annonçait « FORCED · T/H 8x · P 1x · IIR 3 »
 * pendant que les registres du composant étaient à 0x00 d'un bout à l'autre,
 * parce qu'une coupure de son 3V3 l'avait remis à ses défauts d'usine. C'est
 * exactement l'étiquette-qui-ment que ce dépôt traque depuis dn1-3, et la
 * parade existait déjà à côté : `dn_display_backlight_pct_state` ne suit le
 * matériel qu'APRÈS confirmation.
 * ⇒ Ces trois octets sont RELUS à chaque cycle, et c'est EUX que la console
 *   affiche. Une ombre logicielle ne fait plus autorité dans ce module.
 */
uint8_t dn_capt_reg_ctrl_hum(void);  /* 0x72 — osrs_h */
uint8_t dn_capt_reg_ctrl_meas(void); /* 0x74 — osrs_t, osrs_p, mode */
uint8_t dn_capt_reg_config(void);    /* 0x75 — filtre IIR */
/* true quand les registres relus correspondent à ce que l'init a posé. */
bool dn_capt_config_conforme(void);
/*
 * 🔴 « NON CONFORME » et « je n'en sais rien » sont DEUX choses, et les confondre
 * fabriquait un diagnostic faux. Quand l'accès registre nu n'a pas pu s'ouvrir,
 * ou quand la lecture des octets de RÉFÉRENCE a échoué à l'init, il n'y a pas de
 * verdict — il y a une absence de verdict. Sans ce drapeau, une carte démarrée
 * capteur DÉBRANCHÉ affichait `0x72=00 0x74=00 0x75=00 🔴 NON CONFORME` puis
 * « le capteur a REDEMARRE et perdu sa config », pour un capteur qui n'a jamais
 * été là et n'a jamais rien publié. Constat de la revue du 2026-08-17 ; l'init
 * promettait déjà que la garde « sera INERTE, ET ELLE LE DIRA » — elle ne le
 * disait pas.
 */
bool dn_capt_config_verdict_dispo(void);
/* Cadence réellement observée entre les deux dernières lectures valides, en µs.
 * -1 tant qu'il n'y en a pas eu deux. AC7 demande la cadence EFFECTIVE, pas la
 * constante de compilation — une tâche qui dérive doit pouvoir se voir. */
int64_t dn_capt_cadence_reelle_us(void);

/* Identité RELEVÉE à l'init (0 si l'init n'a pas pu lire). Exposée pour que
 * `capteurs` puisse dire CE QU'IL A VU, sans re-solliciter le bus. */
uint8_t dn_capt_chip_id(void);
/* Vrai si la LECTURE de l'identite a abouti. ⛔ Ne dit RIEN de la valeur : elle
 * separe « le capteur a repondu 0x00 » de « il n'a rien repondu », deux
 * diagnostics OPPOSES qui vivaient dans la meme valeur avant dn4-2. */
bool dn_capt_identite_lue(void);
/* Vrai si une lecture d'identite a ete TENTEE. ⛔ FAUX ne veut pas dire « echec » :
 * il veut dire qu'aucune transaction n'a eu lieu (bus absent, device refuse). Ce
 * 3e etat manquait, et `capteurs` affirmait « la transaction a ECHOUE » sur une
 * carte ou on n'avait rien demande (CR dn4-2). */
bool dn_capt_identite_tentee(void);
uint8_t dn_capt_variant(void);
/* Vrai si le VARIANT a ete lu. ⛔ Indispensable : 0x00 est la valeur LEGITIME du
 * BME680 (0x01 = BME688), donc la valeur seule ne peut pas porter l'echec — c'est
 * le defaut que `dn_capt_identite_lue()` a corrige pour le chip id, et qui vivait
 * encore deux lignes plus bas dans la meme fonction (CR dn4-2). */
bool dn_capt_variant_lu(void);
/* Lecture ATOMIQUE des quatre champs : les lire un par un laissait la console
 * observer un etat a demi mis a jour. */
void dn_capt_identite_snapshot(bool *tentee, bool *lue, uint8_t *chip,
                               bool *var_lu, uint8_t *var);
bool dn_capt_gaz_actif(void);

/* Chauffage du gaz à chaud, pour l'A/B de T9. Prend effet au cycle suivant.
 * ⚠️ Le changement RÉINITIALISE la valeur de référence : un delta de température
 *    ne se lit qu'après stabilisation, pas sur la lecture qui suit. */
esp_err_t dn_capt_set_gaz(bool actif);

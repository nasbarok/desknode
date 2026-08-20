#pragma once
/*
 * dn_capteurs — les capteurs environnementaux de DeskNode (dn2-1, P4).
 *
 * Aujourd'hui : UN capteur, le BME680 (température + humidité). Le nom est celui
 * de la FONCTION, pas de la puce — comme dn_touch, dn_link, dn_display — parce
 * que dn4-1 ajoutera BH1750, VL53L0X et INA219 sur le même bus. ⚠️ Il n'est pour
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
} dn_capt_etat_t;

typedef struct {
    uint32_t lectures;      /* lectures VALIDES appliquées */
    uint32_t err_i2c;       /* le transport a échoué (NACK, bus occupé) */
    uint32_t err_donnee;    /* il répond, mais la conversion n'est jamais prête */
    uint32_t err_bornes;    /* valeur hors plage physique du capteur */
    uint32_t reprises;      /* transitions MUET -> VIVANT */
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

/* Dernières valeurs VALIDES, en DIXIÈMES (233 = 23,3 °C · 471 = 47,1 %).
 * Entiers pour rester dans la doctrine du dépôt côté affichage ; le driver rend
 * des float, la conversion est faite ici, une fois.
 * `DN_CAPT_DX_ABSENT` si aucune valeur valide n'est publiée. */
int dn_capt_temperature_dixiemes(void);
int dn_capt_humidite_dixiemes(void);

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
uint8_t dn_capt_variant(void);
bool dn_capt_gaz_actif(void);

/* Chauffage du gaz à chaud, pour l'A/B de T9. Prend effet au cycle suivant.
 * ⚠️ Le changement RÉINITIALISE la valeur de référence : un delta de température
 *    ne se lit qu'après stabilisation, pas sur la lecture qui suit. */
esp_err_t dn_capt_set_gaz(bool actif);

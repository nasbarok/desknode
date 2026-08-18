#pragma once

/*
 * ── dn_rtc — L'HEURE DU MODULE, ET SON HONNÊTETÉ ─────────────────────────────
 *
 * Le module est nommé par sa FONCTION (tenir l'heure), pas par sa puce — même
 * convention que `dn_capteurs` (qui n'est pas « dn_bme680 ») et `dn_link` (qui
 * n'est pas « dn_usbserial »). La puce est un détail d'implémentation qui vit
 * dans le `.c`.
 *
 * ── CE QUI A ÉTÉ MESURÉ LE 2026-08-18, AVANT D'ÉCRIRE UNE LIGNE DE DRIVER ────
 *
 * Doctrine dn2-1, payée deux fois : « le sondage DÉCOUVRE, seule la LECTURE DE
 * REGISTRE QUALIFIE ». Le scan produit des faux positifs (0x76, l'adresse même
 * du BME680, vue à vide) ET des faux négatifs (0x6B, 0x5D, 0x77 soudés ont
 * chacun raté une confirmation en passe x5). Voici donc des LECTURES, pas un
 * scan — sortie console consignée verbatim dans hardware/ §13.14 :
 *
 *   i2c lire 51 00 16  ->  00 00 00 00 96 25 15 01 06 01 00 80 80 80 80 80
 *   i2c lire 51 10 2   ->  00 18
 *
 * 1. 🔴 LE VARIANT EST « A », ET C'EST PROUVÉ PAR LA MESURE, PAS PAR LA DOC.
 *    Entre deux passes espacées de ~45 s, `0x04` et `0x05` BOUGENT (96 25 ->
 *    81 26 -> A8 26) tandis que `0x02` et `0x03` NE BOUGENT PAS. La base de
 *    temps est donc en 0x04. Sur le variant TP elle serait en 0x02, et 0x02
 *    aurait bougé. ⇒ TP RÉFUTÉ PAR LA MESURE.
 *    ⚠️ Ça comptait : la story avertit que « le variant A et le variant TP ne
 *       portent pas la même carte de registres », et le dépôt a payé QUATRE
 *       fois pour avoir cru une source externe (dont SDA/SCL inversés dans la
 *       doc officielle Waveshare).
 *
 * 2. 🔴 `OS` = 1 SUR LES TROIS PASSES. Le bit 7 de 0x04 vaut 1 (0x96, 0x81,
 *    0xA8 ont tous le bit de poids fort). L'oscillateur s'est arrêté ⇒ L'HEURE
 *    LUE N'EST PAS FIABLE. C'est LE témoin d'honnêteté de la barre.
 *
 * 3. Elle COMPTE quand même : 15:25:16 -> 15:26:01 -> 15:26:28 sur trois
 *    lectures. « Elle répond » et « elle dit vrai » sont deux choses
 *    différentes — exactement la leçon du capteur fantôme (§13.6 bis).
 *
 * 4. `Control_1` (0x00) = 0x00 ⇒ STOP=0 (elle tourne), 12_24=0 (format 24 h),
 *    CAP_SEL=0 ⇒ CHARGE DE QUARTZ 7 pF.
 *    ⚠️ CAP_SEL n'est PAS vérifié : rien sur cette carte ne dit quel quartz est
 *       soudé, et un mauvais réglage se paie en DÉRIVE, pas en panne. Laissé
 *       TEL QUEL (on ne change pas un réglage qu'on ne sait pas juger) et
 *       consigné comme inconnu — pas comme un acquis.
 *
 * 5. `Control_2` (0x01) = 0x00 ⇒ COF=000 ⇒ SORTIE CLKOUT 32,768 kHz ACTIVE.
 *    Consommation pour rien (aucune piste ne l'utilise sur ce montage), mais
 *    la couper est une ÉCRITURE de configuration dont le bénéfice n'est pas
 *    mesuré ici. Consignée, non touchée.
 *
 * 6. Alarmes 0x0B..0x0F = 0x80 : le bit AEN_x est posé sur les cinq ⇒ toutes
 *    DÉSARMÉES. Rien à désactiver.
 *
 * 7. Date lue : 2000-01-01, jour de semaine = 6.
 *    ⚠️ ET C'EST UNE COÏNCIDENCE, PAS UNE PREUVE. Le 1er janvier 2000 était
 *       effectivement un samedi (= 6), mais le PCF85063 NE CALCULE PAS le jour
 *       de semaine à partir de la date : il le compte dans son propre
 *       registre, indépendamment. Que les deux concordent ici ne prouve RIEN
 *       sur l'époque de la puce. ⇒ c'est `dn_rtc_poser()` qui CALCULE le jour
 *       de semaine et l'écrit, au lieu de le demander à l'appelant.
 *
 * ── W1 — POURQUOI UN DRIVER MAISON PLUTÔT QU'UN COMPOSANT ────────────────────
 *
 * Les deux candidats ont été TÉLÉCHARGÉS ET LUS, pas jugés sur leur fiche.
 *
 *  · `waveshare/pcf85063a` 2.0.0 — PASSE le critère éliminatoire du dépôt
 *    (`pcf85063a_init(dev, bus_handle, addr)` fait `i2c_master_bus_add_device()`
 *    sur un bus DÉJÀ CRÉÉ, il n'appelle jamais `i2c_new_master_bus`).
 *    🔴 MAIS IL ÉCHOUE SUR LE POINT QUI EST TOUTE LA STORY :
 *       `time->sec = bcdToDec(bufss[0] & 0x7F)` (pcf85063a.c:88 ET :142) — le
 *       masque 0x7F JETTE le bit 7, qui EST le bit OS. Et aucun getter d'OS
 *       n'existe dans les 221 lignes de son en-tête. ⇒ avec ce composant, la
 *       barre NE PEUT PAS savoir qu'elle ment.
 *       Autres relevés : `YEAR_OFFSET 1970` (époque arbitraire — la puce n'a
 *       aucun bit de siècle) ; le `}` de `extern "C"` est placé APRÈS
 *       `#endif // PCF85063A_H`, donc HORS de la garde d'inclusion ; et son
 *       readme documente l'init sous le nom `qmi8658_init` (copier-coller du
 *       driver IMU).
 *  · `espp/pcf85063` 1.1.8 — C++ (`namespace espp`,
 *    `class Pcf85063 : public espp::BasePeripheral<uint8_t,true>`, `std::tm`,
 *    `std::error_code`, `std::recursive_mutex`) et deux dépendances de
 *    framework (`espp/base_peripheral`, `espp/utils`) dans un dépôt 100 % C.
 *    `get_time()` rend un `std::tm`, qui n'a AUCUN champ où loger un bit de
 *    validité.
 *
 * ⇒ Driver maison, le repli nommé par la story. Le travail est 11 registres
 *   BCD ; ce qu'aucun des deux ne fournit — le bit OS exposé, le patron
 *   anti-fantôme, les compteurs par cause — est justement ce que l'AC exige.
 */

#include "driver/i2c_master.h"
#include "esp_err.h"
#include <stdbool.h>
#include <stdint.h>

/* MESURÉE le 2026-08-18, stable 5/5 sur le scan multi-passes, et QUALIFIÉE par
 * lecture de registre. Le bus est l'unique bus de la carte (dn_display). */
#define DN_RTC_ADDR 0x51

/* ── Carte des registres, variant A (CONFIRMÉ PAR LA MESURE, cf. en-tête) ──── */
#define DN_RTC_REG_CTRL1 0x00   /* EXT_TEST | - | STOP | SR | - | CIE | 12_24 | CAP_SEL */
#define DN_RTC_REG_CTRL2 0x01   /* AIE | AF | MI | HMI | TF | COF[2:0] */
#define DN_RTC_REG_OFFSET 0x02  /* correction de marche */
#define DN_RTC_REG_RAM 0x03     /* 1 octet de RAM libre — NOTRE TÉMOIN, voir .c */
#define DN_RTC_REG_SECONDES 0x04 /* 🔴 bit 7 = OS | secondes BCD */
#define DN_RTC_REG_MINUTES 0x05
#define DN_RTC_REG_HEURES 0x06
#define DN_RTC_REG_JOUR 0x07
#define DN_RTC_REG_JSEM 0x08
#define DN_RTC_REG_MOIS 0x09
#define DN_RTC_REG_ANNEE 0x0A
#define DN_RTC_REG_MAX 0x12 /* 0x00..0x11 inclus — au-delà, rien n'est défini */

#define DN_RTC_BIT_OS 0x80   /* Seconds bit 7 — Oscillator Stopped */
#define DN_RTC_BIT_STOP 0x20 /* Control_1 bit 5 */

/*
 * 🔴 LE TÉMOIN ANTI-FANTÔME. Valeur arbitraire, mais NON NULLE et non
 * triviale : c'est tout ce qu'on lui demande. Voir le long commentaire de
 * `temoin_poser()` dans le .c — le choix du REGISTRE, lui, n'est pas arbitraire
 * du tout.
 */
#define DN_RTC_TEMOIN 0xD7

/*
 * Cadence de lecture. 2 Hz, et c'est un choix de MESURE, pas d'habitude :
 *  · la barre doit pouvoir se caler sur le CHANGEMENT DE MINUTE (AC4) — un
 *    sondage à 1 Hz laisserait jusqu'à 1 s de retard, un sondage à 2 Hz 0,5 s ;
 *  · si le régime « secondes » est retenu, 2 Hz évite le battement qui ferait
 *    sauter ou répéter une seconde (deux horloges à 1 Hz non asservies) ;
 *  · le coût est négligeable sur ce bus : ~8 octets par lecture, contre les
 *    ~30 transactions/s que le GT911 y fait déjà en mode `poll`.
 */
#define DN_RTC_PERIODE_MS 500

/* Trois cycles, même règle que dn_capteurs (3 x 5 s) et dn_link (3 s). */
#define DN_RTC_PEREMPTION_US (3LL * DN_RTC_PERIODE_MS * 1000)

/* Époque. La puce porte l'année sur 0..99 et N'A AUCUN BIT DE SIÈCLE : le choix
 * est celui du driver, pas de la puce. 2000..2099 est retenu (Waveshare choisit
 * 1970, tout aussi arbitrairement). ⚠️ À écrire dans la doc comme un CHOIX. */
#define DN_RTC_ANNEE_BASE 2000

typedef enum {
    DN_RTC_JAMAIS,     /* aucune lecture valide depuis le boot */
    DN_RTC_VIVANT,     /* lecture fraîche, BCD légal, OS=0 -> l'heure est FIABLE */
    DN_RTC_MUET,       /* la péremption est passée : elle ne répond plus */
    /*
     * 🔴 LE QUATRIÈME ÉTAT, ET C'EST LUI QUI FAIT LA STORY.
     * Elle répond, son BCD est légal, elle COMPTE — et pourtant l'heure ne vaut
     * rien, parce que OS=1 dit que l'oscillateur s'est arrêté depuis la
     * dernière écriture. Deux causes indiscernables et de même conséquence :
     * l'heure n'a JAMAIS été posée, ou elle a été PERDUE (coupure).
     * ⚠️ C'est le mode de panne à TROIS états du capteur fantôme, transposé :
     *    « il répond » n'est pas « il dit vrai ». Une barre qui affiche
     *    « 03:47 » après une coupure est PIRE qu'une barre qui dit « --:-- ».
     */
    DN_RTC_NON_FIABLE,
} dn_rtc_etat_t;

typedef struct {
    uint16_t annee;   /* DN_RTC_ANNEE_BASE .. +99 */
    uint8_t mois;     /* 1..12 */
    uint8_t jour;     /* 1..31 */
    uint8_t jsem;     /* 0 = dimanche .. 6 = samedi — CALCULÉ, jamais demandé */
    uint8_t heure;    /* 0..23 (la puce est laissée en format 24 h) */
    uint8_t minute;   /* 0..59 */
    uint8_t seconde;  /* 0..59 */
} dn_rtc_heure_t;

typedef struct {
    uint32_t lectures;   /* lectures VALIDES appliquées */
    uint32_t err_i2c;    /* le transport a échoué (NACK, bus occupé) */
    /* 🔴 SEAU DISTINCT, même leçon que `err_donnee` de dn_capteurs : elle
     * répond très bien, mais ce qu'elle rend n'est pas du BCD légal (un quartet
     * > 9). Confondre ça avec `err_i2c` enverrait chercher la panne du côté du
     * câblage, qu'on vient justement de prouver bon. */
    uint32_t err_bcd;
    /* Cycles où OS=1. Ce n'est PAS une erreur — c'est un ÉTAT, et il se compte
     * pour qu'on sache s'il est apparu en cours de route (coupure) ou s'il n'a
     * jamais cessé (jamais posée). */
    uint32_t os_vus;
    uint32_t reprises;   /* transitions MUET/JAMAIS -> VIVANT */
    /* 🔴 LE TÉMOIN A CHANGÉ SOUS NOS PIEDS : la puce a perdu son alimentation
     * ou a été réinitialisée depuis notre init. Compté à part parce que ce
     * n'est NI un défaut de transport (elle répond) NI une donnée illégale
     * (le BCD est parfait) — c'est une horloge qui a redémarré en silence. */
    uint32_t temoins_perdus;
    uint32_t poses;      /* `rtc set` appliqués avec succès */
} dn_rtc_compteurs_t;

/*
 * Démarre la lecture de l'heure. 🔴 NON FATALE, et c'est délibéré — même motif
 * exactement que `dn_link_init` et `dn_capteurs_init` : le seul mode d'échec
 * réaliste est `xTaskCreate`, c'est-à-dire la pénurie de RAM interne. Avec
 * CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y, un abort donnerait « ni console, ni
 * flash, RESET PHYSIQUE obligatoire ». Un module optionnel — une barre — ne doit
 * pas pouvoir briquer le seul outil de diagnostic.
 *
 * ⚠️ À appeler APRÈS dn_display_init() : `dn_display_i2c_bus()` rend NULL tant
 *    que la dalle n'a pas créé l'unique bus de la carte.
 * ⚠️ Et APRÈS dn_ui_init() : la tâche pousse vers la barre par une fonction
 *    publique de dn_ui, qui prend le verrou LVGL elle-même.
 */
esp_err_t dn_rtc_init(void);

dn_rtc_etat_t dn_rtc_etat(void);
const char *dn_rtc_etat_nom(dn_rtc_etat_t e);

/*
 * Rend la dernière heure lue. 🔴 Le retour est le VERDICT D'HONNÊTETÉ, pas un
 * code d'erreur de transport : `false` signifie « cette heure ne doit PAS être
 * affichée », que ce soit parce qu'elle n'a jamais été lue, parce que la puce
 * s'est tue, ou parce que OS=1. L'appelant qui ignore le retour affiche une
 * heure fausse — c'est pour ça qu'il n'y a pas de getter « valeur seule ».
 */
bool dn_rtc_lire(dn_rtc_heure_t *out);

/* Âge de la dernière lecture VALIDE, ou -1 si aucune. */
int64_t dn_rtc_age_us(void);

/*
 * Pose l'heure. Écrit les 7 registres de temps d'un seul coup, ce qui a un
 * effet de bord VOULU et documenté par la puce : écrire le registre des
 * secondes REMET OS À 0. C'est le seul geste qui rend l'heure fiable.
 * `h->jsem` est IGNORÉ : le jour de semaine est calculé depuis la date.
 * ⚠️ Écrire dans le RTC est de l'I²C, pas de la flash — l'interdit D4 sur les
 *    écritures en régime ne s'y applique pas (il vise le défilement d'image
 *    mesuré à 165 343 o/s sur la flash).
 */
esp_err_t dn_rtc_poser(const dn_rtc_heure_t *h);

void dn_rtc_compteurs(dn_rtc_compteurs_t *out);
void dn_rtc_reset_compteurs(void);

/* ── Les états bruts, pour que `rtc` RELISE au lieu de RÉCITER ─────────────── */

/* Recopie les registres 0x00..(n-1) tels qu'ils sont MAINTENANT. Transaction
 * I²C synchrone (~1 ms) : c'est la commande console qui l'appelle, pas la
 * tâche. Rend ESP_ERR_INVALID_STATE si le module n'est pas armé. */
esp_err_t dn_rtc_registres(uint8_t *out, uint8_t n);

bool dn_rtc_arme(void);          /* le device I²C existe-t-il ? */
bool dn_rtc_os(void);            /* dernier bit OS LU (pas déduit) */
uint8_t dn_rtc_ctrl1_init(void); /* Control_1 constaté à l'init */
uint8_t dn_rtc_ctrl1_lu(void);   /* Control_1 au dernier cycle */
uint8_t dn_rtc_temoin_lu(void);  /* RAM_byte au dernier cycle */
bool dn_rtc_temoin_dispo(void);  /* le témoin a-t-il pu être POSÉ à l'init ? */
/*
 * 🔴 LE VERDICT CROSS-BOOT : le témoin tel qu'il a été RELU AU BOOT, AVANT
 *    toute écriture. `0xD7` ⇒ la puce a GARDÉ son alimentation depuis le
 *    dernier démarrage ; autre chose (typiquement `0x00`) ⇒ ELLE L'A PERDUE.
 * ⚠️ À ne pas confondre avec `dn_rtc_temoin_lu()`, qui porte le verdict
 *    RUNTIME (la puce a-t-elle redémarré PENDANT que le firmware tourne ?).
 *    Les deux sont nécessaires, et la première version n'avait que le second —
 *    ce qui rendait `rtc` rassurant précisément quand il ne fallait pas.
 * MESURÉ le 2026-08-18 : cette carte N'A AUCUNE SAUVEGARDE. Coupure de 30 s
 * ⇒ OS=1 et 2000-01-01 00:00:54, la valeur de sortie de reset.
 */
bool dn_rtc_temoin_boot(uint8_t *out);
/* Pile restante de la tâche, en octets. Instrument, pas décoration : les
 * 4 096 o viennent de la RAM INTERNE, la ressource même qui a tué la branche
 * WiFi en dn2-2 (6 407 o libres après init). Sans ce chiffre, un futur
 * « on peut réduire à 2 048 » serait une supposition. */
uint32_t dn_rtc_pile_libre(void);

/*
 * DeskNode — cartographie matérielle de l'affichage.
 *
 * ⚠️ STATUT ÉPISTÉMIQUE (story dn1-2, AC1) : ce fichier est une HYPOTHÈSE tant
 *    que la mire de bits ne l'a pas éprouvé. Il est recoupé entre le miroir
 *    Spotpear du wiki Waveshare et un dépôt communautaire qui fait tourner
 *    CETTE carte exacte. Toute correction faite par la mire se répercute ici
 *    ET dans hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md, avec le symptôme
 *    qui l'a révélée.
 */
#pragma once

#include "driver/i2c_master.h"
#include "esp_io_expander.h"

/* ── Résolution ──────────────────────────────────────────────────────────── */
#define DN_LCD_H_RES 480
#define DN_LCD_V_RES 640
#define DN_LCD_TOTAL_PX (DN_LCD_H_RES * DN_LCD_V_RES)          /* 307 200 px */
#define DN_FB_BYTES ((size_t)DN_LCD_H_RES * DN_LCD_V_RES * 2)  /* 614 400 o */
/* Pas de DN_LCD_BPP : il a existé, personne ne l'a jamais lu, et les 16 bits
 * par pixel sont posés là où ils comptent vraiment — `bits_per_pixel` du
 * rgb_panel_config ET du panel_dev_config, dans dn_display.c. Une constante
 * de géométrie que personne n'utilise finit par diverger de celle qui compte,
 * et c'est celle-là qu'on relit en diagnostiquant. */

/* ── Bus I²C (UNIQUE sur cette carte) ────────────────────────────────────── */
/* Le TCA9554, le GT911, l'IMU, la RTC et le header externe des 4 capteurs sont
 * tous dessus. En P1 on n'y parle QU'À l'expander : pas de scan d'adresses,
 * pas de GT911 (dn1-4), pas de capteur (dn2-1). */
#define DN_PIN_I2C_SDA 15
#define DN_PIN_I2C_SCL 7
#define DN_I2C_PORT I2C_NUM_0
/* ⚠️ FRÉQUENCE PAR DEVICE, pas par bus (correctif dn1-4). En API `i2c_master`
 * d'IDF 5.x, `i2c_master_bus_config_t` n'a pas de champ d'horloge : celle-ci se
 * pose dans `i2c_master_dev_config_t.scl_speed_hz`, device par device. Cette
 * constante est donc la valeur que NOS devices demandent (le GT911 de dn_touch,
 * et le BME680 de dn_capteurs depuis dn2-1) — le TCA9554, lui, pose ses propres
 * 400 kHz dans son driver (esp_io_expander_tca9554.c:18).
 * ⚠️ Le BME680 la demande EXPLICITEMENT contre le défaut 100 kHz de son composant :
 *    une transaction 4× plus courte occupe 4× moins le bus que la DMA du panneau
 *    se dispute (§11.4). */
#define DN_I2C_FREQ_HZ 400000

/*
 * 🔴 dn4-7 — LE VL6180X SEUL EST RALENTI, ET C'EST UNE HYPOTHÈSE À ÉPROUVER,
 *    ⛔ PAS UN CORRECTIF ÉTABLI.
 *
 * Constat du 2026-08-21, bissection à UNE variable, câblage vérifié contre la
 * sérigraphie :
 *   · ToF DÉBRANCHÉ  : `touch` = 559 lectures, **0 erreur I²C**, boot en 2 338 ms
 *   · ToF BRANCHÉ    : panique au boot (TCA9554 muet) — ⚠️ **INTERMITTENTE**,
 *                      la carte repart si on insiste (constat owner)
 * Et à l'ohmmètre, module isolé : ⛔ AUCUN court (`SDA`/`SCL` ↔ `GND` ouverts),
 * `SDA`/`SCL` ↔ `VIN` = **10 kΩ**, soit EXACTEMENT la valeur mesurée en dn4-2
 * quand il fonctionnait.
 *
 * MÉCANISME VISÉ : le TOF050C accepte `VIN` 3-5 V pour une puce à 2,8 V ⇒ il
 * porte un ADAPTATEUR DE NIVEAU bidirectionnel, et les 10 kΩ mesurés sont ses
 * tirages hauts. Un transistor d'adaptateur affaibli garde donc son tirage
 * INTACT (l'ohmmètre ne voit rien) mais a des FRONTS LENTS : à 400 kHz le signal
 * n'a pas le temps de s'établir ⇒ transactions corrompues ⇒ désynchronisation.
 * ⚠️ Un cas de MOSFET d'adaptateur `SDA` endommagé est rapporté sur VL6180X
 *    (element14), et un blocage `SDA` bas après une période de fonctionnement
 *    est rapporté sur le VL53L0X — la puce sœur.
 *
 * ⛔ CE N'EST PAS PROUVÉ. Le critère de réussite est le TAUX DE BOOT RÉUSSI avec
 *    le module branché, ⛔ pas « ça a marché une fois ».
 * ⚠️ Et ⛔ ça n'expliquerait PAS l'analogique mort (ALS et télémétrie sont EN
 *    AVAL de l'adaptateur, internes à la puce) : ce serait un SECOND défaut.
 */
#define DN_I2C_FREQ_TOF_HZ 100000

/* ── Expander TCA9554 ────────────────────────────────────────────────────── */
#define DN_TCA9554_ADDR 0x20

/* ⚠️ LE PIÈGE À UN RANG. Waveshare numérote EXIO1..EXIO8 en base 1 ; le driver
 * indexe en base 0. EXIO1 => bit 0. Se tromper d'un rang, c'est réinitialiser
 * le TACTILE en croyant réinitialiser la DALLE — sans aucun message d'erreur,
 * et en cherchant la panne ailleurs pendant des heures.
 * Recoupé : le YAML ESPHome de cette carte déclare pin 0 = display reset,
 * pin 1 = touch reset, pin 2 = display CS. */
#define DN_EXIO_LCD_RST IO_EXPANDER_PIN_NUM_0 /* EXIO1 */
#define DN_EXIO_TP_RST IO_EXPANDER_PIN_NUM_1  /* EXIO2 — piloté depuis dn1-4 (dn_display_tp_reset) */
#define DN_EXIO_LCD_CS IO_EXPANDER_PIN_NUM_2  /* EXIO3 */

/* ── Tactile : Goodix GT911 (dn1-4) ──────────────────────────────────────────
 *
 * TP_INT — ⚠️ STATUT ÉPISTÉMIQUE, comme le reste de ce fichier l'a été avant la
 * mire de bits. GPIO16 vient de DEUX sources concordantes (le wiki Waveshare,
 * qui parle d'une résistance à souder, et les stories dn1-1/dn1-2) mais était
 * ABSENT de hardware/…-affichage.md §1.2, qui fait autorité. dn1-4 le tranche
 * par un compteur d'interruptions confronté à un toucher réel — un GPIO qui ne
 * bat jamais et un GPIO mal choisi se ressemblent trait pour trait.
 * Le verdict de la mesure est écrit dans §1.2 avec le constat qui l'établit.
 */
#define DN_PIN_TP_INT 16

/*
 * ── LES DEUX ADRESSES DU GT911, ET CE QUI CHOISIT ENTRE ELLES ────────────────
 *
 * Le GT911 n'a pas d'adresse fixe : il ÉCHANTILLONNE le niveau de sa broche INT
 * au moment où son reset est relâché.
 *      INT tenu BAS   au relâchement  =>  0x5D
 *      INT tenu HAUT  au relâchement  =>  0x14
 * C'est pour ça que la séquence de reset appartient à celui qui tient INT, et
 * pas au driver — qui, avec `rst_gpio_num = -1`, ne la joue même pas.
 *
 * ⚠️ Aucune des deux ne rentre en conflit sur ce bus. Occupants MESURÉS par le
 *    scan `i2c` du 2026-08-17 : TCA9554 **0x20**, RTC PCF85063 **0x51** (première
 *    confirmation qu'elle vit), IMU QMI8658 **0x6B** (et NON 0x6A, que ce fichier
 *    laissait ouvert), BME680 **0x77**. ✅ Les 3 derniers capteurs sont MESURÉS
 *    depuis dn4-2 (2026-08-19/20) : BH1750 **0x23**, TOF050C-VL6180X **0x29**,
 *    INA219 **0x40** — voir le bloc dédié plus bas.
 * 🔴 LE PROBE AVANT LE RESET RÉPOND DÉJÀ — MESURÉ LE 2026-08-16 SUR CETTE CARTE.
 *    Ce fichier enseignait le contraire (« tant que la séquence EXIO2 n'a pas été
 *    jouée, le GT911 ne répond à AUCUNE des deux : c'est le témoin négatif
 *    attendu »), et le livrable de dn1-4 l'a RÉFUTÉ dans le même commit :
 *    `probe AVANT reset : il répond DÉJÀ à 0x5D`. TP_RST n'est donc pas maintenu
 *    bas quand l'expander le laisse en entrée haute impédance — le contrôleur
 *    sort de reset seul à la mise sous tension. La séquence reste indispensable,
 *    mais pour rendre l'adresse DÉTERMINISTE, pas pour réveiller le contrôleur ;
 *    et un probe qui répond avant elle n'est pas une anomalie à diagnostiquer.
 *    (Correction de la revue dn1-4 : la phrase réfutée survivait ici, dans LA
 *    source unique du brochage, et dans l'en-tête de dn_touch.h — les deux
 *    fichiers qu'on ouvre en premier.)
 *
 * Les noms viennent du header du composant (ESP_LCD_TOUCH_IO_I2C_GT911_ADDRESS
 * et …_ADDRESS_BACKUP) ; on les redéclare ici parce que dn_pins.h est LA source
 * unique du brochage et que le probe a lieu avant tout appel au driver.
 */
#define DN_GT911_ADDR 0x5D        /* visée : INT tenu bas au relâchement */
#define DN_GT911_ADDR_BACKUP 0x14 /* repli : INT haut/flottant */

/*
 * ── Capteurs externes sur l'embase JST (dn2-1) ───────────────────────────────
 *
 * ✅ BME680 : ADRESSE MESURÉE le 2026-08-17 — 0x77, PAS 0x76.
 *    Ce qui choisit entre les deux : le niveau de SDO (bas => 0x76, haut =>
 *    0x77), et LE BREAKOUT TIRE SDO À VCC (3,3 V relevés au multimètre, broche
 *    laissée en l'air). Constat d'identité, cité au caractère près :
 *        0x77 reg 0xD0 : 61   (chip id — 0x61 = BME680/BME688)
 *        0x77 reg 0xF0 : 00   (variant — 0x00 = BME680, 0x01 aurait dit BME688)
 *    Scan stable 5/5 sur 8 passes (commande console `i2c`).
 *    ✅ **BARRETTE SOUDÉE le 2026-08-17** — le contact est une propriété du
 *    montage, plus un geste, et toutes les campagnes (cadence, auto-échauffement,
 *    budgets) ont été jouées APRÈS. Le premier relevé, lui, avait été pris
 *    barrette non soudée, contact tenu à la main : les deux blocs d'étalonnage
 *    d'usine relus après soudure sont IDENTIQUES OCTET POUR OCTET à ceux d'avant.
 *    Détail : hardware/…-capteurs-i2c.md §13.
 *
 * ⚠️ L'embase JST I²C est sérigraphiée GND·3V3·SDA·SCL — le miroir Spotpear
 *    donnait SCL·SDA (inversés) sur un « header 2,54 mm » qui n'existe pas sous
 *    cette forme : c'est une embase JST, et sa JUMELLE adjacente est l'UART.
 *
 * ✅ LES 3 AUTRES CAPTEURS SONT INVENTORIÉS, BRANCHÉS ET QUALIFIÉS (dn4-2,
 * 2026-08-19/20). Le legs D2-1a est SOLDÉ : 9 photos recto/verso dans
 * docs/cablage/, réfs lues sur la SÉRIGRAPHIE. ⛔ Rien n'entre ici qui ne soit
 * MESURÉ — c'est la source unique du brochage.
 */
#define DN_BME680_ADDR 0x77

/* ── Les 3 capteurs de dn4-2 — adresses MESURÉES, pas attendues ──────────────
 *
 * 🔴 LE 3ᵉ N'EST PAS UN VL53L0X : C'EST UN **TOF050C-VL6180X**. Ce fichier, le
 *    brief, l'epic, le tracker, `i2c_nom_connu()` et six stories ont écrit
 *    « VL53L0X » du 2026-08-14 au 2026-08-19. L'addendum §3 du brief avait POSÉ
 *    la question (« noter la réf réelle du breakout à l'inventaire ») et personne
 *    ne l'avait fermée. Tranché PAR LA LECTURE le 2026-08-19 :
 *      · `i2c lire16 29 0000` -> **B4** (IDENTIFICATION__MODEL_ID), 5 fois sur 5
 *      · témoin négatif `i2c lire 29 C0/C1/C2` -> 01/00/00, ⛔ PAS EE/AA/10
 *      · rév. modèle 1.3, rév. module 2.0 (registres 0x0001..0x0004)
 *    ⚠️ Et « même famille ToF » est FAUX sur les trois points qui comptent :
 *    index 16 bits (pas 8), identité 0x0000 (pas 0xC0), portée GARANTIE 100 mm
 *    (pas 2 m). Le « 50 cm » est une annonce revendeur. dn4-3 hérite du chiffre.
 *
 * ⚠️ CHACUNE DE CES ADRESSES A ÉTÉ QUALIFIÉE PAR UNE TRANSACTION DE DONNÉE,
 *    ⛔ jamais par le scan — qui ment dans les deux sens (§13.2, et le taux de
 *    faux positifs est mesuré à 0,740 % par sondage d'adresse vide en §13.16.5).
 *
 * ✅ ET DEUX BROCHES DE SÉLECTION SONT MESURÉES, PAS SUPPOSÉES :
 *    · `ADDR` du BH1750 est TIRÉ BAS sur le GY-302 -> 0x23 déterministe SANS
 *      fil ajouté (mesuré : il répond 5/5 avec les 4 fils de bus seulement).
 *      ⚠️ La datasheet ROHM ne définit 0x23 que pour ADDR <= 0,3 x VCC ; c'est
 *      le BREAKOUT qui le garantit ici, pas la puce.
 *    · `XSHUT` du VL6180X est TIRÉ HAUT sur le TOF050C -> la puce répond FIL
 *      RETIRÉ, alors que basse ou flottante elle resterait en shutdown sans
 *      acquitter. ⇒ XSHUT n'est PAS câblé, par DÉCISION MESURÉE.
 *      🔴 Si le ToF devient un jour intermittent, XSHUT est le PREMIER suspect
 *         à re-nommer — pas la soudure.
 *    · `INT` du VL6180X n'est PAS câblé (AC11 : aucune broche d'interruption,
 *      le polling suffit ; l'entrée de ledger est FERMÉE).
 *    · `A0`/`A1` de l'INA219 NON PONTÉS (lu à la photo) -> 0x40.
 *
 * ⛔ ZÉRO GPIO CONSOMMÉ : l'I²C est un BUS. Les quatre capteurs partagent
 *    DN_PIN_I2C_SDA et DN_PIN_I2C_SCL. Aucune broche des headers n'est prise.
 */
#define DN_BH1750_ADDR  0x23  /* MESURÉ 5/5, ADDR tiré bas par le breakout      */
#define DN_VL6180X_ADDR 0x29  /* MESURÉ : lire16 0x0000 -> B4, 5/5             */
#define DN_INA219_ADDR  0x40  /* MESURÉ : lire 00 (2 o) -> 39 9F, 5/5          */

/* ── 3-wire SPI d'initialisation du ST7701S ──────────────────────────────── */
/* ⛔ GPIO1/GPIO2 sont PARTAGÉS avec le slot TF (SD_CMD / SD_SCK).
 *    Ne jamais initialiser la SD dans ce firmware. */
#define DN_PIN_LCD_SDA 1
#define DN_PIN_LCD_SCL 2

/* ── Rétroéclairage ──────────────────────────────────────────────────────── */
/* GPIO direct. En P1 : ON FIXE (le clignotement était le signe de vie de P0).
 * La gradation PWM est le sujet de dn1-3. */
#define DN_PIN_BACKLIGHT 6

/* ── Signaux de synchronisation RGB ──────────────────────────────────────── */
#define DN_PIN_HSYNC 38
#define DN_PIN_VSYNC 39
#define DN_PIN_DE 40
#define DN_PIN_PCLK 41

/*
 * ── Les 16 lignes de données ─────────────────────────────────────────────
 *
 * CONVENTION : `data_gpio_nums[i]` est câblé au bit `i` du mot 16 bits sorti
 * par le périphérique LCD_CAM. Comme le framebuffer est en RGB565
 * (RRRRRGGG GGGBBBBB, R sur les bits 15..11), l'ordre est donc :
 *
 *      indice   0  1  2  3  4 |  5  6  7  8  9 10 | 11 12 13 14 15
 *      signal   B0 B1 B2 B3 B4| G0 G1 G2 G3 G4 G5 | R0 R1 R2 R3 R4
 *               (poids faible du bleu à gauche)
 *
 * ─── CORRIGÉ PAR LA MIRE le 2026-08-14 (AC1) ────────────────────────────
 *
 * L'hypothèse de départ lisait les listes du YAML ESPHome
 *     red: [46, 3, 8, 18, 17] / green: [14,13,12,11,10,9] / blue: [5,45,48,47,21]
 * comme allant du POIDS FAIBLE au POIDS FORT. C'EST L'INVERSE : à l'intérieur
 * de chaque canal, ces listes vont du POIDS FORT au POIDS FAIBLE.
 *
 * SYMPTÔME QUI L'A RÉVÉLÉ (mire `bits`, 16 bandes horizontales) : dans chaque
 * groupe, les bandes étiquetées des POIDS FORTS (16, 32) étaient NOIRES et
 * celles des poids faibles visibles — l'exact contraire de l'attendu. Or le
 * blanc plein était franc et neutre, ce qui INTERDIT l'explication « lignes
 * mortes » : une ligne coupée l'est aussi dans le blanc.
 *
 * CE QUI SIGNE LE DIAGNOSTIC — l'asymétrie entre canaux. Bandes visibles :
 *   bleu 2 sur 5 · VERT 4 sur 6 · rouge 2 sur 5.
 * Avec l'ordre inversé, les bandes visibles sont celles des poids forts réels
 * (52 %, 26 %, 13 %…). Le vert étant le canal le plus lumineux à l'œil, il en
 * laisse passer QUATRE là où le bleu n'en laisse que deux. Aucun brochage
 * faux, aucune ligne morte ne produit ce 4-contre-2 ; l'inversion, si.
 *
 * Conséquence pour la divergence connue : **GPIO21 = B0**, le poids FAIBLE du
 * bleu — et non B4 comme le supposait la story. C'est cohérent avec son
 * absence du tableau Spotpear : en 16 bits dans un panneau 18 bits, les LSB
 * sont les lignes qu'on documente le moins.
 */
#define DN_RGB_DATA_GPIOS                                    \
    {                                                        \
        21, 47, 48, 45, 5,     /* B0 B1 B2 B3 B4         */  \
        9, 10, 11, 12, 13, 14, /* G0 G1 G2 G3 G4 G5      */  \
        17, 18, 8, 3, 46       /* R0 R1 R2 R3 R4         */  \
    }

/*
 * ── Timings du panneau ───────────────────────────────────────────────────
 *
 * htotal = 10 + 70 + 480 + 60 = 620
 * vtotal = 10 + 20 + 640 + 20 = 690
 * 620 * 690 = 427 800 pixels/trame
 * 16 000 000 / 427 800 = 37,40 Hz  <- la valeur ATTENDUE, à confronter au réel.
 *
 * Bande passante consommée en permanence par le seul affichage :
 * 480 * 640 * 2 = 614 400 o/trame * 37,40 = ~23,0 Mo/s, 24 h/24, avant qu'une
 * seule ligne d'UI n'ait été dessinée.
 */
#define DN_PCLK_HZ (16 * 1000 * 1000)
#define DN_HSYNC_PULSE 10
#define DN_HSYNC_BACK_PORCH 70
#define DN_HSYNC_FRONT_PORCH 60
#define DN_VSYNC_PULSE 10
#define DN_VSYNC_BACK_PORCH 20
#define DN_VSYNC_FRONT_PORCH 20

#define DN_FPS_THEORIQUE                                                     \
    ((double)DN_PCLK_HZ /                                                    \
     ((double)(DN_LCD_H_RES + DN_HSYNC_PULSE + DN_HSYNC_BACK_PORCH +         \
               DN_HSYNC_FRONT_PORCH) *                                       \
      (double)(DN_LCD_V_RES + DN_VSYNC_PULSE + DN_VSYNC_BACK_PORCH +         \
               DN_VSYNC_FRONT_PORCH)))

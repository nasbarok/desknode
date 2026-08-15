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
 * et demain les capteurs de dn2-1) — le TCA9554, lui, pose ses propres 400 kHz
 * dans son driver (esp_io_expander_tca9554.c:18). */
#define DN_I2C_FREQ_HZ 400000

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
 * ⚠️ Aucune des deux ne rentre en conflit sur ce bus : TCA9554 0x20, RTC
 *    PCF85063 0x51, IMU QMI8658 0x6A/0x6B, et les 4 capteurs de dn2-1
 *    (0x76/0x77, 0x23, 0x29, 0x40) sont tous ailleurs.
 * ⚠️ UN PROBE AVANT LE RESET NE VOIT RIEN : tant que la séquence EXIO2 n'a pas
 *    été jouée, le GT911 ne répond à AUCUNE des deux. « Absent » à ce moment-là
 *    n'est pas une panne — c'est le témoin négatif attendu.
 *
 * Les noms viennent du header du composant (ESP_LCD_TOUCH_IO_I2C_GT911_ADDRESS
 * et …_ADDRESS_BACKUP) ; on les redéclare ici parce que dn_pins.h est LA source
 * unique du brochage et que le probe a lieu avant tout appel au driver.
 */
#define DN_GT911_ADDR 0x5D        /* visée : INT tenu bas au relâchement */
#define DN_GT911_ADDR_BACKUP 0x14 /* repli : INT haut/flottant */

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

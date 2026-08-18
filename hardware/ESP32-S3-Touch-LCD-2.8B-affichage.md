# Configuration d'affichage de référence — Waveshare ESP32-S3-Touch-LCD-2.8B

> **Ce fichier fait autorité.** Tout ce qu'il contient a été **mesuré sur la carte**
> le **2026-08-14** (story dn1-2, P1), pas recopié d'un wiki ni d'un dépôt tiers.
> Là où la mesure a **corrigé** une source tierce, c'est écrit noir sur blanc.
>
> **On ne va plus chercher un brochage ailleurs.** Si quelque chose ici se révèle
> faux, on corrige ici, avec le symptôme qui l'a révélé.

Matériel : ESP32-S3R8 (QFN56) rev v0.2, 16 MB flash / 8 MB PSRAM octale,
dalle IPS **480 × 640 portrait**, contrôleur **ST7701S** en RGB parallèle 16 bits.
Chaîne : ESP-IDF **v5.5.5** (commit `b774170f`).

---

## 0. LA CONFIGURATION DE RÉFÉRENCE POUR dn3 — arbitrée le 2026-08-15 (dn1-3), **corrigée le 2026-08-16 (dn1-4)**

C'est la seule chose à lire si on ne lit qu'une chose.

> 🔴 **QUATRE LIGNES ONT CHANGÉ LE 2026-08-16.** Les trois premières se tiennent :
> `bounce_px` passe de **0 à 4 800 px**, `CONFIG_LCD_RGB_ISR_IRAM_SAFE` de **`y` à
> `n`** — la seconde étant la **condition** de la première, pas un choix
> indépendant — et `draw_lines` de **64 à 128** pour récupérer une partie de la
> latence que le bounce coûte. La quatrième est le **mode de lecture tactile**,
> nouveau dans cette table : **`poll`**.
>
> Motif des trois premières : **toute transaction I²C pendant que la dalle affiche
> fait défiler l'image**, défaut que dn1-4 est la première story à pouvoir voir
> (avant elle, aucune story ne parlait en I²C en fonctionnement). Le même
> changement **solde l'artefact §10.5**, qui était le legs ouvert de dn1-3. Détail
> complet en **§11**.
>
> ⚠️ **Cet encart a annoncé « DEUX LIGNES » pendant que trois avaient changé**, et
> la ligne du draw buffer ci-dessous est restée à 64 lignes alors que le code
> livrait 128. C'est le défaut que la §4 avait DÉJÀ produit en dn1-3, au même
> endroit et sur la même table — corrigé par la revue de code dn1-4.

| | | justifié par |
|---|---|---|
| `num_fbs` | **1** | le double tampon est **réparé** (§4 ter) mais n'apporte **rien de mesuré** : il ne corrige ni le déchirement (c'est la synchro qui le fait) ni l'artefact §10.5, et coûte 614 400 o + une branche Kconfig |
| **`bounce_px`** | **4 800 px (10 lignes)** ⬅️ *change le 2026-08-16* | la DMA du panneau lit désormais un tampon en **RAM interne** au lieu d'aller chercher la PSRAM : c'est ce qui supprime **à la fois** le défilement sous I²C **et** l'artefact §10.5 (§11.4). Coût : 2 × 9 600 o de RAM interne, **rien au repos** et +1,1 point de CPU en redessin, fps **inchangé** — le vrai prix est **+160 ms de latence** (§11.5) |
| **`LCD_RGB_ISR_IRAM_SAFE`** | **`n`** ⬅️ *change le 2026-08-16* | **effet propre nul** sur le défilement (branche enfin jouée, §5.3) — mais avec `y` le bounce buffer **panique** au boot. Il est conservé à `n` comme *condition* du bounce, pas pour lui-même |
| Rendu LVGL | **PARTIEL** | à 128 lignes, un plein écran demande **5 flushes** (§11.7). ⚠️ Le « 10 flushes et ~176 ms » de §10.3 valait à 64 lignes, et son attente a été **corrigée à 267 ms** par la mesure de §11.5 : elle supposait un rendu négligeable, ce que le dashboard n'est pas |
| **Draw buffer** | **480 × 128 px (122 880 o), RAM interne DMA** ⬅️ *change le 2026-08-16* | décision owner pendant le dev : 128 lignes récupèrent **120 des 160 ms** que le bounce coûte, contre +61 440 o de RAM interne. Le levier **sature** à 128 — 160 lignes ne donnent plus rien (§11.5). A/B à aire identique : la PSRAM reste **1,70× plus lente** (§10.3) |
| **Mode de lecture tactile** | **`poll`** ⬅️ *nouveau le 2026-08-16* | verdict AC2 (§11.3). `event` est pourtant **moins cher** (0,5 % contre 0,8 %) : il est écarté sur un symptôme de ROBUSTESSE, pas de coût — `ui off` ne coupe pas le tactile en `event`, l'INT ne bat pas au repos, et l'appui « collé » n'a pas de garde native. Le +0,3 point de CPU est le prix assumé |
| Synchro du flush | **`vsync`** | témoin positif établi : en `off` l'œil **voit** le déchirement, en `vsync` il disparaît (§10.4) |
| `RESTART_IN_VSYNC` | **`y`** (livré) | `n` n'est requis que par la branche d'essai du double tampon (§4 ter) |
| Rétroéclairage | **LEDC 10 bits @ 24 kHz** | 5 kHz **siffle** à duty bas, mesuré à l'oreille (§10.6) |
| Cœur de la tâche LVGL | **0** | sans effet mesuré sur l'artefact §10.5 ; retenu par cohérence avec le reste du pipeline |
| Fond | **flash `mmap`** | la copie PSRAM coûte 614 400 o et ne change rien de mesuré (§10.5, ligne 2) |

**Ce que cette configuration ferme, et qui était ouvert** : l'artefact de redessin de la §10.5.
Il n'était pas un défaut de bande passante, de phase ni de contenu — les sept hypothèses de
dn1-3 cherchaient toutes du mauvais côté. C'était **la DMA du panneau affamée sur le bus SPI0**,
et le bounce buffer y met fin (§11.4). Constat owner du 2026-08-16, témoin = le label 1 Hz.

**Ce que cette configuration NE ferme PAS** : la contention par **écritures flash** de la §5.3.
Le bounce buffer a été mesuré contre un stimulus **I²C** ; rien ne dit qu'il protège aussi des
écritures flash, qui coupent le cache au lieu de simplement occuper le bus. **D4 (pas
d'écritures flash en fonctionnement) reste en vigueur**, et la branche
« bounce 4 800, `ISR_IRAM_SAFE=n`, stimulus flash » n'a **pas** été jouée.

> 🔴 **JOUÉE LE 2026-08-16 (dn2-2), ET LA RÉPONSE EST NON.** `flash on` dans la config de
> référence, témoin positif au compteur (2 514 secteurs, 10 297 344 o, **165 343 o/s
> soutenus**), constat owner à l'œil : **« l'image défile »**. Le bounce buffer NE protège
> PAS des écritures flash — son ISR de réalimentation est masquée pendant l'effacement de
> secteur (`ISR_IRAM_SAFE=n`, condition du bounce lui-même). À l'arrêt du stimulus, l'image
> s'est recalée seule. **Les deux régimes de §11.4 sont désormais séparés PAR LA MESURE :
> le bounce gagne contre l'I²C, il perd contre la flash. D4 est définitivement motivé.**

---

## 1. Brochage vérifié

### 1.1 Les 16 lignes de données RGB

Convention ESP-IDF : `data_gpio_nums[i]` est câblé au **bit `i`** du mot 16 bits
sorti par le périphérique LCD_CAM. Le framebuffer étant en RGB565
(`RRRRRGGG GGGBBBBB`), l'ordre est donc B0..B4, G0..G5, R0..R4.

| Indice | Signal | GPIO | Poids |
|---:|---|---:|---:|
| 0 | B0 | **21** | 1 |
| 1 | B1 | 47 | 2 |
| 2 | B2 | 48 | 4 |
| 3 | B3 | 45 | 8 |
| 4 | B4 | 5 | 16 |
| 5 | G0 | 9 | 1 |
| 6 | G1 | 10 | 2 |
| 7 | G2 | 11 | 4 |
| 8 | G3 | 12 | 8 |
| 9 | G4 | 13 | 16 |
| 10 | G5 | 14 | 32 |
| 11 | R0 | 17 | 1 |
| 12 | R1 | 18 | 2 |
| 13 | R2 | 8 | 4 |
| 14 | R3 | 3 | 8 |
| 15 | R4 | **46** | 16 |

> ### ⚠️ CE QUE LA MIRE A CORRIGÉ — le point le plus utile de ce fichier
>
> L'hypothèse de départ lisait les listes du YAML ESPHome de cette carte
> (`red: [46, 3, 8, 18, 17]`, `green: [14,13,12,11,10,9]`, `blue: [5,45,48,47,21]`)
> comme allant du **poids faible au poids fort**. **C'est l'inverse** : à
> l'intérieur de chaque canal, ces listes vont du **poids FORT au poids FAIBLE**.
> Le tableau ci-dessus est donc l'ordre ESPHome **inversé canal par canal**.
>
> **Symptôme observé** (mire `bits`, 16 bandes horizontales étiquetées) : dans
> chaque groupe, les bandes marquées des **poids forts (16, 32) étaient NOIRES**
> et celles des poids faibles visibles — l'exact contraire de l'attendu.
>
> **Ce qui a interdit l'explication paresseuse** : le blanc plein (`scene white`)
> était **franc et neutre**. Une ligne coupée l'est aussi dans le blanc. Les
> 16 lignes fonctionnaient donc toutes, et « poids forts éteints » était
> impossible.
>
> **Ce qui a signé le diagnostic — l'asymétrie entre canaux.** Bandes visibles :
> bleu **2 sur 5**, **vert 4 sur 6**, rouge **2 sur 5**. Avec l'ordre inversé,
> les bandes visibles sont celles des poids forts réels (52 %, 26 %, 13 %…) ;
> le vert, canal le plus lumineux à l'œil, en laisse passer **quatre** là où le
> bleu n'en laisse que **deux**. Aucun brochage faux ni aucune ligne morte ne
> produit ce 4-contre-2 ; l'inversion, si.
>
> **Vérification par prédiction falsifiable** : après correction, l'image devait
> s'inverser exactement — 3 bandes noires puis 2 bleues, 2 noires puis 4 vertes,
> 3 noires puis 2 rouges. **C'est exactement ce qui a été observé.**
>
> **Conséquence sur la divergence connue** : **GPIO21 = B0**, le poids FAIBLE du
> bleu — et non B4 comme le supposaient les notes de départ. Cohérent avec son
> absence du tableau Spotpear : en 16 bits dans un panneau 18 bits, les LSB sont
> les lignes qu'on documente le moins.

### 1.2 Synchronisation, I²C, expander, rétroéclairage

| Signal | Broche | Note |
|---|---|---|
| HSYNC / VSYNC / DE / PCLK | GPIO **38 / 39 / 40 / 41** | vérifiés par l'affichage |
| I²C (bus unique) | SDA = GPIO**15**, SCL = GPIO**7** | ⚠️ **la fréquence se pose PAR DEVICE**, pas par le bus (voir l'encart). **Occupants MESURÉS au scan** (dn2-1) : TCA9554 **0x20** · **RTC PCF85063 `0x51`** · GT911 **0x5D** · **IMU QMI8658 `0x6B`** *(et non 0x6A)* · **BME680 `0x77`**. Détail : fichier frère §13.3 |
| 3-wire SPI (init ST7701S) | SDA = GPIO**1**, SCL = GPIO**2** | ⛔ **partagées avec le slot TF** — ne jamais initialiser la SD |
| **LCD_RST** | expander **bit 0** (EXIO1) | derrière le TCA9554 |
| **TP_RST** | expander **bit 1** (EXIO2) | *voir §1.3* |
| **LCD_CS** | expander **bit 2** (EXIO3) | derrière le TCA9554 |
| **TP_INT** | GPIO**16** | ✅ **ÉTABLI PAR LA MESURE le 2026-08-16** — voir l'encart ci-dessous |
| Rétroéclairage | GPIO**6** | GPIO direct, ON/OFF (la gradation est dn1-3) |

> ### ✅ TP_INT = GPIO16 — l'écart documentaire est SOLDÉ (dn1-4, AC1)
>
> Jusqu'ici GPIO16 figurait dans les stories dn1-1/dn1-2 et au wiki Waveshare,
> mais **pas dans ce tableau**, qui fait autorité. Il y est désormais, et pas sur
> la foi d'une source tierce : par une **preuve causale**.
>
> Le GT911 échantillonne le niveau de sa broche INT **au relâchement de son
> reset**, et en déduit son adresse I²C. La commande `touch addr` joue donc deux
> resets d'affilée, en tenant GPIO16 à un niveau différent :
>
> ```
>   INT tenu HAUT au relachement -> repond a 0x14  (ESP_OK)
>   INT tenu BAS  au relachement -> repond a 0x5D  (ESP_OK)
> ```
>
> Faire varier GPIO16 fait varier l'adresse latchée. **Aucune autre broche du SoC
> ne peut produire cet effet** : c'est donc bien celle que le GT911 échantillonne.
> C'est plus fort qu'un front observé à l'oscilloscope ou qu'un compteur d'IRQ qui
> monte — ceux-là n'auraient prouvé que l'existence d'un signal, pas son identité.
>
> ⚠️ **Le niveau de repos d'INT est HAUT** (relevé : `niveau instantane 1`), et il
> ne bat **pas** spontanément : **0 IRQ en 30 s** sans toucher la dalle. Pendant un
> contact, en revanche, il pulse abondamment — 999 IRQ pour 22 appuis, soit ~45
> impulsions par appui.

> ### ⚠️ « 400 kHz » n'est pas une propriété du BUS (correctif dn1-4)
>
> Ce tableau annonçait « 400 kHz » sur la ligne I²C, et le log de boot faisait de
> même. C'était une **étiquette non tenue** : en API `i2c_master` (IDF 5.x),
> `i2c_master_bus_config_t` n'a **aucun champ d'horloge**. La fréquence se pose
> dans `i2c_master_dev_config_t.scl_speed_hz`, **device par device**, et deux
> devices du même bus peuvent tourner à deux vitesses différentes.
>
> Ce que le bus porte réellement : les broches, la source d'horloge, le filtre de
> glitch, les tirages internes. Qui pose quoi, ici :
> - **TCA9554** → 400 kHz, posés par son propre driver
>   (`esp_io_expander_tca9554.c:18`, lu dans le source, pas supposé) ;
> - **GT911** → 400 kHz, posés par `dn_touch` (le gabarit du composant proposait
>   100 kHz ; on prend 400 kHz parce que la lecture tactile est dans le chemin de
>   la latence). **0 erreur I²C** mesurée sur 4 978 lectures.

> ⚠️ **La numérotation Waveshare `EXIO1..EXIO8` est en base 1 ; l'index du driver
> est en base 0.** `EXIO1` = bit **0**. Confirmé indépendamment par le YAML
> ESPHome de cette carte (pin 0 = display reset, pin 1 = touch reset,
> pin 2 = display CS). Se tromper d'un rang, c'est réinitialiser le tactile en
> croyant réinitialiser la dalle, sans aucun message d'erreur.

### 1.3 État du tactile — **CLOS par dn1-4 le 2026-08-16**

**Ce que P1 laissait** : le bit 1 (**TP_RST**, le reset du GT911) **DÉLIBÉRÉMENT
en ENTRÉE**, c'est-à-dire dans l'état de mise sous tension du TCA9554 (haute
impédance). P1 ne le pilotait pas : le mettre en sortie lui aurait imposé un
niveau non mesuré, et le GT911 échantillonne son adresse I²C au relâchement de
son reset. *dn1-4 partait donc d'un TP_RST non piloté, pas d'un TP_RST haut.*

**L'état stationnaire depuis dn1-4** : `dn_display_tp_reset()` met TP_RST en
**SORTIE**, joue la séquence (150 ms bas / 50 ms de repos), et **l'y laisse à
l'état HAUT**. C'est le nouvel état de référence.

> 🔴 **UNE CROYANCE DE CE FICHIER EST RÉFUTÉE.** On tenait pour acquis qu'« un
> scan I²C avant le reset tactile ne voit PAS le GT911 (il ne sort de reset
> qu'après la séquence EXIO2) », et dn1-4 devait s'en servir comme **témoin
> négatif**. **C'est faux sur cette carte** : au boot, avant toute intervention,
> le probe répond **déjà**, et à **0x5D**.
>
> ```
> I (1461) dn_touch: probe AVANT reset : il répond DÉJÀ à 0x5D
> ```
>
> **Ce que ça établit** : TP_RST n'est **pas** maintenu bas quand l'expander le
> laisse en entrée haute impédance — un tirage de la carte le tient haut, donc le
> GT911 sort de reset tout seul à la mise sous tension et latche son adresse sur
> le niveau d'INT de ce moment-là (haut au repos… et pourtant 0x5D : le GT911
> tire lui-même INT bas pendant sa propre séquence de démarrage).
>
> **Ce que ça ne retire PAS à la séquence** : elle reste indispensable, mais pour
> une autre raison que celle qu'on croyait. Elle n'« allume » pas le contrôleur —
> elle rend son adresse **DÉTERMINISTE**. Sans elle, l'adresse dépend d'un niveau
> qu'on ne contrôle pas.
>
> **Conséquence méthodologique** : ce probe-là n'est **pas** un témoin négatif sur
> cette carte, et il ne faut pas s'en servir comme tel. Le témoin qui prouve
> quelque chose est `touch addr` (§1.2).

### 1.4 Correction sur le bus 3-wire SPI

Les notes de départ annonçaient « 3-wire SPI, `data_rate` 80 MHz bit-bangé »,
repris du champ `data_rate: 80MHz` du YAML ESPHome. **Ce champ décrit le bus
RGB, pas celui-ci.** Le bus d'initialisation est bit-bangé **par logiciel** et le
composant `esp_lcd_panel_io_additions` le plafonne à
`PANEL_IO_3WIRE_SPI_CLK_MAX` = **500 kHz**. 80 MHz n'y a jamais été atteignable.

---

## 2. Timings retenus, et le rafraîchissement qu'ils imposent

| Paramètre | Valeur |
|---|---|
| `pclk_hz` | **16 000 000** |
| `h_res` × `v_res` | 480 × 640 |
| `hsync_pulse_width` / `back_porch` / `front_porch` | 10 / 70 / 60 |
| `vsync_pulse_width` / `back_porch` / `front_porch` | 10 / 20 / 20 |
| `pclk_active_neg` | `false` |
| `data_width` / `bits_per_pixel` | 16 / 16 |
| `rgb_ele_order` | `LCD_RGB_ELEMENT_ORDER_RGB` |

```
htotal = 10 + 70 + 480 + 60 = 620
vtotal = 10 + 20 + 640 + 20 = 690
620 × 690 = 427 800 pixels/trame
16 000 000 / 427 800 = 37,40 Hz
```

**Bande passante consommée en permanence par le seul affichage** : seuls les
pixels actifs sont lus, soit 480 × 640 × 2 = **614 400 o/trame**,
donc **614 400 × 37,40 ≈ 23,0 Mo/s en continu, 24 h/24**, avant qu'une seule
ligne d'UI n'ait été dessinée.

---

## 3. Le bloc `sdkconfig.defaults` d'affichage

Le fichier commenté fait foi : `firmware/desknode/sdkconfig.defaults`.
Chaque ligne y porte sa raison. Récapitulatif :

| Symbole | Défaut IDF | Retenu | Raison, en une phrase |
|---|---|---|---|
| `CONFIG_ESPTOOLPY_FLASHSIZE_16MB` | 2MB | **y** | la carte porte 16 MB ; sans ça toute partition au-delà de `0x200000` est inaccessible |
| `CONFIG_PARTITION_TABLE_CUSTOM` | n | **y** | 4 MiB d'app + partition d'assets + partition « stimulus » sacrifiable |
| `CONFIG_SPIRAM` | **n** | **y** | pas de PSRAM, pas de framebuffer de 614 400 o |
| `CONFIG_SPIRAM_MODE_OCT` | QUAD | **OCT** | le module ESP32-S3R8 embarque de la PSRAM octale ; en quad elle n'est pas détectée |
| `CONFIG_SPIRAM_SPEED_80M` | 40M | **80M** | à 40 MHz le refill DMA ne suit pas les 23,0 Mo/s permanents |
| `CONFIG_LCD_RGB_RESTART_IN_VSYNC` | n | **y** | **mesuré nécessaire** — voir §5.1 · ⚠️ rend la commande `dma` inopérante, voir §5.1 |
| `CONFIG_LCD_RGB_ISR_IRAM_SAFE` | n | **y** | **conservé par précaution, effet propre NON mesuré** (coût nul) — voir §5.3 |
| `CONFIG_SPIRAM_XIP_FROM_PSRAM` | n | **n** | **RÉFUTÉ par la mesure** : défilement identique avec et sans — voir §5.3 |
| `CONFIG_FREERTOS_HZ` | 100 | **1000** | un tick de 10 ms est plus grossier qu'une trame (26,7 ms) |
| `CONFIG_FREERTOS_GENERATE_RUN_TIME_STATS` | n | **y** | arme `vTaskGetRunTimeStats()` : c'est l'instrument de **charge CPU** exigé par AC6 (commande `cpu`) |
| `CONFIG_FREERTOS_RUN_TIME_STATS_USING_ESP_TIMER` | *(déjà le défaut)* | **y** | écrit explicitement : l'horloge CPU compterait des cycles et **déborderait en ~17 s** |
| `CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG` | UART0 | **USB** | console interactive : un seul binaire pour toutes les mesures — *déplace la console sur l'USB* |

> ⛔ **`CONFIG_SPIRAM_SPEED_120M` est INTERDIT sur ce produit.** Le Kconfig
> d'Espressif prévient qu'en octal, 120 MHz est expérimental et que *« si la puce
> démarre à une certaine température, puis que la température varie d'environ
> 20 °C, les accès PSRAM plantent aléatoirement »*. DeskNode vit H24 sur la
> façade d'une tour de jeu : l'écart de température est le **régime nominal**,
> pas un cas limite. Ce n'est pas une piste d'optimisation, c'est une panne
> programmée.

> **Repli sur le header UART, si l'USB pose problème.** Remplacer
> `CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y` par `CONFIG_ESP_CONSOLE_UART_DEFAULT=y`,
> puis `rm sdkconfig && idf.py build`. On récupère alors le log sur **les deux
> chemins** (header UART GPIO43/44 **et** USB, via la console secondaire en sortie
> seule — le comportement de `hello-desknode`), et la console **interactive** se
> retrouve sur le header : `dn_console.c` monte un REPL UART par compilation
> conditionnelle dans cette configuration. Ce qu'on perd : l'USB ne **reçoit**
> plus les commandes, il faut un adaptateur USB-série sur GPIO43/44 à 115200.

> ⚠️ **Le piège qui rend tout ce tableau inopérant** : `sdkconfig.defaults` n'est
> lu que pour **produire** `sdkconfig`. Un `sdkconfig` déjà présent — **gitignoré,
> donc invisible à `git status`** — l'emporte en silence.
> **Règle du dépôt : toute modification de `sdkconfig.defaults` se valide par
> `rm sdkconfig && idf.py build`, puis par la LECTURE du bandeau de boot.**

Bandeau de boot attendu (relevé verbatim) :

```
I (25) boot.esp32s3: SPI Flash Size : 16MB
I (571) desknode: PSRAM : 8388608 o détectés, mode OCTAL, 80 MHz
```

---

## 4. Configuration framebuffer de référence

| Réglage | Valeur retenue | Pourquoi — **mesuré** |
|---|---|---|
| `num_fbs` | **1** | ⚠️ **ARBITRÉ le 2026-08-15, et c'est un renversement** (valait 2). Le double tampon est **impossible** tant que `RESTART_IN_VSYNC` est activé — et il doit l'être. Repasser à 1 récupère **614 312 o de PSRAM** et rend **toutes** les présentations visibles. Voir §4 bis |
| `fb_in_psram` | **1** | 614 400 o ne tiennent pas en RAM interne |
| `bounce_buffer_size_px` | **4 800 px** ⬅️ *change le 2026-08-16* | 🔴 **RÉHABILITÉ par dn1-4.** Il avait été « éliminé, deux symptômes distincts » (§5.3) sur un essai où `ISR_IRAM_SAFE=y` le faisait paniquer : les deux options étaient **nouées**, ce qui explique le « watchdog » qui l'avait disqualifié. Il est ce qui supprime la famine DMA sous I²C **et** l'artefact §10.5 (§11.4) |
| XIP (`SPIRAM_XIP_FROM_PSRAM`) | **désactivé** | **RÉFUTÉ** : défilement identique avec et sans, et coûterait 342 876 o de PSRAM (§5.3) |
| Bascule d'image | ⛔ **SANS OBJET en `num_fbs=1`** | il n'y a plus qu'un tampon, donc plus de bascule. Le verdict *« attendre `on_frame_buf_complete` »* était mesuré dans une configuration où le double tampon ne fonctionnait pas (§4 bis) : il est **retiré**, pas reporté. La question se reposera en dn1-3, dans les bons termes |
| Emplacement de l'asset | **partition de données `mmap`ée** | `EMBED_FILES` mettrait 600 Ko en `.rodata`, recopiés en PSRAM si XIP était activé |

Ces valeurs sont les **défauts d'un clone neuf** (`dn_bootcfg.c`) : NVS vierge ⇒
`num_fbs=1, bounce_px=4800, draw_lines=128, draw_psram=0, lvgl_core=0`. Vérifié en
effaçant la région NVS puis en rebootant.

> **Corrigé le 2026-08-16 par la revue de code de dn1-4 — LE MÊME DÉFAUT, AU MÊME
> ENDROIT, POUR LA DEUXIÈME FOIS.** La ligne `bounce_buffer_size_px` annonçait
> encore **0** et la liste des défauts `bounce_px=0, draw_lines=64`, alors que
> `dn_bootcfg.c` posait `4800` et `128` depuis le commit `4eb834c` — c'est-à-dire
> depuis la story qui a écrit cette section. L'encart ci-dessous, rédigé en dn1-3
> pour le même écart sur `num_fbs`, disait déjà pourquoi c'est grave : *« le
> fichier d'autorité contredisait le code sur la valeur la plus structurante du
> pipeline »*. Un encart qui décrit un défaut n'empêche pas de le refaire ; seule
> une relecture systématique code↔doc le fait.
>
> ⚠️ **Garde-fou ajouté au passage** : `bounce_px` et `draw_lines` mangent la même
> RAM interne, et leurs bornes ne se parlaient pas. `set bounce 38400` — que
> l'aide de la commande présentait comme « le plafond, un diviseur utile » — ne
> démarrait plus depuis le passage à 128 lignes : panique au boot, CPU halté, plus
> de console pour annuler. `set` vérifie désormais le **budget combiné** contre la
> RAM interne réellement libre.

> **Corrigé le 2026-08-15 (dn1-3).** Ces deux lignes annonçaient encore
> `num_fbs=2` alors que `dn_bootcfg.c:44` posait `DN_DEFAULT_NUM_FBS 1` depuis
> l'arbitrage du §4 bis. Le fichier d'autorité contredisait le code sur la valeur
> la plus structurante du pipeline ; c'est le genre d'écart qu'on relit en
> diagnostiquant, et qui coûte une heure. Les trois clés de dn1-3
> (`draw_lines`, `draw_psram`, `lvgl_core`) sont ajoutées à la même liste.

> ### 🔴 LE POINT À NE PAS RATER EN ARRIVANT EN dn1-3 — la discipline de bascule n'est PAS dans le produit
>
> La ligne « Bascule d'image » ci-dessus décrit une discipline **mesurée**, pas une
> discipline **appliquée**. Dans le firmware tel qu'il est livré :
>
> - **`dn_display_present()`** (`firmware/desknode/main/dn_display.c:327-338`) appelle
>   `esp_lcd_panel_draw_bitmap()` et **rend la main immédiatement**. Il n'attend
>   ni le VSYNC, ni `on_frame_buf_complete`. C'est le **seul** chemin de bascule
>   du produit : boot (`desknode_main.c:128`), commande `scene`, commande `bw`,
>   et la copie de l'asset passent tous par là.
> - **`dn_measure_wait_vsync()` / `dn_measure_wait_frame_done()`** ne sont appelées
>   que depuis `dn_stimulus.c:100` et `:104`, c'est-à-dire **uniquement à
>   l'intérieur de la tâche de stimulus de déchirement**.
>
> **Pourquoi ce n'est pas un bug en P1** : l'image de P1 est **statique**. Rien ne
> se redessine, donc rien ne peut se déchirer. La discipline n'a rien à protéger.
>
> **Décision owner : on ne déplace PAS l'attente dans le chemin produit.** dn1-3
> passe à LVGL, qui gère ses propres tampons et son propre moment de bascule ;
> ajouter une attente bloquante dans `present()` maintenant ralentirait *chaque*
> présentation et invaliderait la durée de présentation publiée.
>
> **⇒ C'est donc le travail de dn1-3 de l'implémenter**, s'il redessine des trames
> entières. S'il ne redessine que des rectangles sales (ce que la §5.4 recommande),
> la question se repose autrement — mais elle se repose. Ne pas partir de l'idée
> que le socle la traite déjà : **il ne la traite pas.**

---

## 4 bis. 🔴 LA CONFIGURATION RETENUE EST CONTRADICTOIRE — mesuré le 2026-08-15

> **`num_fbs = 2` et `CONFIG_LCD_RGB_RESTART_IN_VSYNC=y` sont INCOMPATIBLES sur cette puce.**
> Tant que les deux sont posés, la dalle **n'affiche jamais `fb[0]`** après le boot : elle reste
> collée sur `fb[1]`, et **une présentation sur deux n'atteint pas l'écran**. Le second
> framebuffer est payé 614 400 o de PSRAM et ne sert à rien.

### Ce qui a été observé

Sept commandes de scène consécutives, l'œil de l'owner à chaque fois. Le tampon visé se déduit du
tour de rôle de `s_draw_index` :

| Commande | Tampon dessiné | Vu à l'écran |
|---|---|---|
| `scene asset` | fb[1] | asset |
| `scene frame` | fb[0] | ❌ l'asset reste |
| `scene white` | fb[1] | ✅ blanc |
| `scene frame` | fb[0] | ❌ le blanc reste |
| `scene frame` | fb[1] | ✅ mire |
| `scene red` | fb[0] | ❌ la mire reste |
| `scene frame` | fb[1] | ✅ mire |

**Toutes** les bascules vers fb[0] échouent, **toutes** celles vers fb[1] passent. `draw_bitmap`
rend `ESP_OK` à chaque fois, et `dn_display_present()` rend une durée plausible (680-750 µs) :
**rien, côté logiciel, ne signale la perte.**

### Le mécanisme, vérifié dans le source d'ESP-IDF v5.5.5

`components/esp_lcd/rgb/esp_lcd_panel_rgb.c` :

- `:61` — `#define RGB_LCD_NEEDS_SEPARATE_RESTART_LINK 1`, actif sur ESP32-S3 (contournement matériel) ;
- `:1135` — à la création du panneau, **une seule fois** :
  `gdma_link_concat(rgb_panel->dma_restart_link, 0, rgb_panel->dma_fb_links[0], 1);`
  Le lien de relance est **soudé à `dma_fb_links[0]`** et n'est jamais re-pointé ensuite ;
- `:1187` — sous `RESTART_IN_VSYNC`, **chaque VBlank** fait
  `gdma_start(chan, gdma_link_get_head_addr(panel->dma_restart_link))` ;
- `:713` — la bascule de `draw_bitmap`, elle, ne réaccroche que la **queue** des liens de
  framebuffer (`gdma_link_concat(dma_fb_links[i], -1, dma_fb_links[cur_fb_index], 0)`).

La relance périodique repart donc d'un chemin figé que la bascule ne met pas à jour.

### L'A/B qui le prouve — et le dilemme qu'il révèle

| Configuration | Bascule vers fb[0] | Cadrage au boot |
|---|---|---|
| `RESTART_IN_VSYNC=y` (**retenue en dn1-2**) | ❌ jamais | ✅ correct |
| `RESTART_IN_VSYNC=n` | ✅ passe (`scene green` dans fb[0] s'affiche) | ❌ **décalé en permanence**, reproduit |

Les deux défauts sont **les deux faces du même arbitrage**, pas deux bugs indépendants. Le verdict
de dn1-2 sur `RESTART_IN_VSYNC` reste donc juste — il corrige un défaut réel, re-constaté le
2026-08-15 — mais **son coût n'avait pas été vu**.

### Ce que ça invalide, et une anomalie que ça explique

- ⛔ **Tout le A/B d'AC5 `num_fbs=1` vs `num_fbs=2` est SANS OBJET** : les deux branches
  comparaient, de fait, du simple tampon à du simple tampon.
- 🔎 **Rétrodiction.** §5.2 consignait, comme réfutation de `research-paysage.md` §4 :
  *« le double tampon seul ne change RIEN au déchirement »*. C'est exact, et la cause est
  maintenant connue : **il n'y avait pas de double tampon.** Le défaut explique une anomalie déjà
  écrite, que personne n'avait su interpréter.
- ⚠️ Le verdict *« attendre `on_frame_buf_complete` »* a été mesuré dans les mêmes conditions :
  il est à reprendre, pas à recopier.
- ⚠️ La tâche de stimulus passe par le **même** `dn_display_present()` : les cadences de §5.2
  portent aussi cette perte d'une trame sur deux.

### Ce que ça NE remet pas en cause

Le brochage, les timings, les 37,40 Hz d'AC4, les budgets PSRAM, les trois débits de bande
passante, la réfutation de XIP et l'élimination du bounce buffer : tous mesurés hors de ce chemin,
ou insensibles à lui.

### Les parades essayées le 2026-08-15 — avec leur symptôme (AC8)

Toutes sur la variante `RESTART_IN_VSYNC=n`, qui est la seule où fb[0] redevient affichable.

| # | Parade | Résultat observé |
|---|---|---|
| 1 | Un `dma` **manuel** après le boot | ✅ **recale d'un coup** — l'image redevient correcte |
| 2 | …puis une bascule de scène | ❌ **re-décale** : chaque changement de tampon re-provoque le décrochage |
| 3 | Un `dma` **manuel** après la bascule | ✅ **recale ET garde le bon tampon** — vérifié dans les **deux sens**, fb[1] *et* fb[0] |
| 4 | `esp_lcd_rgb_panel_restart()` **immédiatement** en fin de `dn_display_present()` | ❌ **ne recale pas** — ni au boot, ni après bascule |
| 5 | Idem, mais **30 ms après** la bascule (une trame à 37,40 Hz) | ❌ **ne recale toujours pas** au boot |
| 6 | *(observé incidemment)* démarrage après un `watchdog_reset` d'esptool | ❌ **le dessin du BOOT ne parvient pas à la dalle** : écran noir, avec seulement un fragment du liseré vert de l'asset en haut à gauche. L'application tourne (la console répond, l'uptime avance), le rétroéclairage est ON et DISPON est ON. Un `scene asset` ensuite — donc une bascule vers fb[1] — **rétablit l'image plein écran**. Le chemin d'affichage est intact ; c'est la présentation du boot, qui vise fb[0], qui est perdue. Cohérent avec le défaut ci-dessus, et **symptôme supplémentaire à verser au dossier** |

**Ce que ça apprend, et c'est la piste à reprendre.** La parade *fonctionne* (ligne 3) : recaler
après une bascule rend le bon tampon **avec** le bon cadrage. Ce qui manque, c'est **le moment**.
Un recalage immédiat combat une bascule encore en vol — la DMA ne change de lien qu'en atteignant
la queue du lien courant — et 30 ms ne suffisent pas non plus. Les `dma` manuels qui ont marché
étaient envoyés **plusieurs secondes** après.

⇒ La piste sérieuse est donc de **déclencher le recalage sur l'événement qui dit que la bascule a
réellement eu lieu** (`on_frame_buf_complete`, ou un compteur de VSYNC après la bascule), plutôt
que sur un délai fixe. Non mesuré.

### Statut

**ARBITRÉ le 2026-08-15 : `num_fbs = 1`, `RESTART_IN_VSYNC=y` conservé.** Décision owner, prise
**après mesure** et non sur le papier.

Ce que l'option retenue donne, vérifié de bout en bout sur la carte :

| | |
|---|---|
| PSRAM libre | **7 769 784 o** contre 7 155 472 avant ⇒ **614 312 o récupérés** |
| Présentations | **toutes** atteignent la dalle — il n'y a plus de bascule, donc plus rien à perdre |
| Cadrage | correct au boot **et** après chaque changement de scène, sans aucune intervention |
| AC3 | l'asset s'affiche plein écran et bien cadré, sous cette configuration |
| AC4 | **37,40 Hz** mesurés contre 37,40 théoriques, 561 trames en 14 999 762 µs |
| `cfg reset` | l'issue de secours fonctionne : NVS effacée, le défaut `num_fbs=1` s'applique seul |

**Ce n'est pas un renoncement définitif au double tampon.** C'est le constat qu'il n'apporte
aujourd'hui **rien** — puisqu'il ne fonctionnait pas — et qu'il coûte 614 400 o. La piste du
recalage déclenché sur l'événement de bascule effective (ligne 6 du tableau ci-dessus) reste
ouverte, non mesurée, et **c'est dn1-3 qui en aura réellement besoin** : LVGL redessine, là où P1
affiche une image fixe.

⇒ Reste au ledger pour dn1-3. Les autres options non mesurées : `num_fbs = 3` · bounce buffer
(mais il a fait redémarrer la carte sur watchdog, §5.3).

---

## 4 ter. ✅ LE DOUBLE TAMPON EST RÉPARÉ — mesuré le 2026-08-15 (dn1-3, AC5)

**L'entrée 🔴 du §4 bis est SOLDÉE.** La piste identifiée mais jamais mesurée — recaler la DMA
sur l'**événement de bascule** plutôt qu'après un délai fixe — a été jouée sur la carte, et elle
passe.

### Le montage

`firmware/desknode/main/dn_recal.c` : une tâche dédiée (priorité 5), réveillée par sémaphore
depuis l'ISR `on_vsync`, laisse passer **N retours verticaux après une bascule réussie**, puis
appelle `esp_lcd_rgb_panel_restart()`. Jamais de `restart()` ni de log dans l'ISR — le cache y est
potentiellement désactivé. L'armement se fait dans `dn_display_present()`, sur le chemin où la
bascule vient d'aboutir, et **uniquement quand `num_fbs > 1`**.

⚠️ **Ce montage exige une branche Kconfig**, et c'est le point qui rend la mesure possible :
`esp_lcd_rgb_panel_restart()` ne fait que poser `need_restart`, un bit que le driver **ne lit
jamais** sous `CONFIG_LCD_RGB_RESTART_IN_VSYNC=y` (`esp_lcd_panel_rgb.c:1149-1165`). La branche
vit dans le dépôt : `firmware/desknode/sdkconfig.defaults.ac5-double-tampon`, avec son mode
d'emploi. Sans elle, tout « le recalage n'a rien changé » serait une **non-mesure**.

### Le protocole et le verdict

Protocole de dn1-2 rejoué à l'identique : `num_fbs=2`, LVGL en pause (`ui off`), huit scènes
alternées au chemin brut — `red green blue white red green blue white` —, deux secondes entre
chacune, œil de l'owner.

Le mécanisme rend le test non ambigu : à deux tampons, les scènes visent alternativement `fb[1]`
et `fb[0]`. Le défaut de dn1-2 était que **toutes** les bascules vers `fb[0]` échouaient en
silence, ce qui aurait donné *rouge, rouge, bleu, bleu…*

| | |
|---|---|
| Vu par l'owner | **les 8 couleurs, dans l'ordre** |
| Compteurs `recal` | **9 recalages joués, 0 armement perdu, dernier retour `ESP_OK`** |
| Cadrage | correct — le défaut que `RESTART_IN_VSYNC=y` corrigeait n'est pas revenu |
| Variante de timing | **1 vsync** suffit ; la variante à 2 n'a pas eu à être jouée |

⇒ **Les bascules vers `fb[0]` ET `fb[1]` atteignent la dalle.** Le double tampon fonctionne sur
cette puce, sous recalage événementiel.

### Le coût, et ce qui reste imparfait

**Constat owner, consigné parce qu'une réparation sans sa réserve est une publicité** : sur la
scène `white`, qui porte du texte, « le texte s'est affiché sur plusieurs clignotements en se
décalant ». C'est le coût du mécanisme — avec `RESTART_IN_VSYNC=n` il n'y a plus de relance
automatique par VBlank, donc l'image reste décalée depuis la bascule jusqu'au recalage, soit une
à deux trames.

### Pourquoi ce n'est PAS la configuration de référence pour autant

Parce qu'AC6 se tranche sur ce que le double tampon **apporte**, et la mesure dit : rien
aujourd'hui.

1. Il ne corrige **pas** l'artefact de redessin LVGL (§10.3) — vérifié, il est identique en
   `num_fbs=2` + rendu direct et en `num_fbs=1` + rendu partiel.
2. Il ne corrige pas le déchirement : c'est `flush sync vsync` qui le supprime, à un tampon
   comme à deux.
3. Il coûte **614 400 o de PSRAM** et impose une branche Kconfig hors du build livré.

⇒ **Acquis technique, pas acquis produit.** Il est là, prouvé, rejouable, et il attend un besoin
— dn1-4 (tactile, donc redessins fréquents) ou dn3-2 (six widgets vivants) le trouveront peut-être.

## 5. Les chiffres, datés du 2026-08-14

> **Revue du 2026-08-15.** Certains chiffres de cette section portent désormais un
> **⚠️ à re-mesurer** : ils se contredisaient entre eux, ou mesuraient autre chose
> que ce qu'ils annonçaient. Ils sont laissés en place, en italique et marqués,
> plutôt que remplacés par une valeur choisie au jugé. **Rien n'a été inventé pour
> lever une contradiction.** Liste complète des cases ouvertes : §5.2 (cadences
> d'AC5) et §5.4 (RAM interne, temps de boot, taille du binaire, charge CPU).

### 5.1 Rafraîchissement (AC4)

| Configuration | fps mesuré | Théorie | Écart |
|---|---:|---:|---:|
| `num_fbs=1`, bounce 0 | **37,40 Hz** (561 trames / 14 999 899 µs) | 37,40 Hz | **−0,00 %** |
| `num_fbs=2`, bounce 0 | **37,40 Hz** (561 trames / 14 999 367 µs) | 37,40 Hz | **+0,00 %** |
| `num_fbs=2`, bounce 19 200 px | **37,42 Hz** | 37,40 Hz | +0,05 % |
| `num_fbs=2`, XIP activé | **37,42 Hz** | 37,40 Hz | +0,05 % |

Le rafraîchissement est **rigoureusement celui que les timings imposent**, dans
toutes les configurations essayées. Aucune n'affame la DMA au point de perdre
des trames.

> ⚠️ **Un compteur vsync qui tourne ne prouve PAS que l'écran affiche quoi que ce
> soit.** La DMA émet le signal même dalle non initialisée. Ce chiffre qualifie
> le **pipeline**, pas l'**image** ; et il est **aveugle** au défaut de §5.3.

**Décrochage DMA au démarrage — `CONFIG_LCD_RGB_RESTART_IN_VSYNC`.**
Sans ce symbole : l'image sort avec les **bonnes couleurs** mais un cadrage
**décalé en permanence**, coupée en deux, la partie de droite revenant sur la
gauche. **Preuve que c'est bien un décrochage DMA** : **dans cette configuration
`RESTART_IN_VSYNC=n`**, un appel manuel à `esp_lcd_rgb_panel_restart()`
(commande console `dma`) remet l'image en place d'un coup. Avec le symbole
activé, l'image est cadrée dès le boot, sans geste.

> ### 🔴 La commande `dma` est un NO-OP dans la configuration RETENUE
>
> La preuve ci-dessus reste valide — elle a été faite avec `RESTART_IN_VSYNC=n`.
> Mais **dès que le symbole est activé, `esp_lcd_rgb_panel_restart()` ne fait
> plus rien**, et donc la commande console `dma` non plus.
>
> Vérifié dans la source de l'IDF v5.5.5 :
> `components/esp_lcd/rgb/esp_lcd_panel_rgb.c:1149-1165` —
> `lcd_rgb_panel_try_restart_transmission()` pose `do_restart = true` **sans
> aucune condition** sous `#if CONFIG_LCD_RGB_RESTART_IN_VSYNC`, et ne **lit
> jamais** `panel->flags.need_restart`. Or `need_restart` est le **seul** bit que
> `esp_lcd_rgb_panel_restart()` (ligne 464, écriture ligne 472) sait poser. Le
> flag est écrit, personne ne le lit. C'est la branche `#else` — donc
> `RESTART_IN_VSYNC=n` — qui le consomme.
>
> **Conséquence sur la lecture des observations** : sous la configuration
> retenue, le redémarrage de la DMA a **déjà lieu à chaque VBlank, tout seul**.
> Toute note du type « un `dma` a remis l'image » relevée **sous cette
> configuration** attribue à la commande un travail qu'elle n'a pas fait : la
> récupération venait du redémarrage automatique. Voir §5.3, où cette correction
> est appliquée.

### 5.2 Déchirement (AC5)

**Instrument validé par témoin positif.** À `num_fbs=1` on écrit dans le
framebuffer que la DMA est en train de lire : le déchirement **doit** s'y voir.
Observé : *« brisé en escalier et pas de la même taille, brisé sur le dessus »*.
L'instrument voit ce qu'il prétend voir.

Stimulus : barre verticale blanche de 64 px balayant sur fond noir, trame
entière redessinée à chaque pas.

> ⛔ **CE TABLEAU EST SANS OBJET — voir §4 bis (2026-08-15).** Les deux branches `num_fbs=1` et
> `num_fbs=2` comparaient en réalité du simple tampon à du simple tampon : sous
> `RESTART_IN_VSYNC=y`, la dalle n'affiche jamais `fb[0]`. C'est d'ailleurs ce qui explique le
> « **INCHANGÉ** » de la deuxième ligne, consigné à l'époque comme une réfutation de
> `research-paysage.md` §4. À rejouer **après** l'arbitrage owner sur la configuration de
> framebuffer, pas avant — et les cadences portent en plus le générateur lent corrigé au CR.

| Branche | Cadence — ⚠️ **à re-mesurer** | Ce qui est VU |
|---|---:|---|
| `num_fbs=1`, aucune synchro | *28,9 Hz* | escalier franc, tranches inégales — **témoin positif** |
| `num_fbs=2` + `draw_bitmap` seul | *29,1 Hz* | **INCHANGÉ** |
| `num_fbs=2` + attente **VSYNC** | *18,2 Hz* | escalier sur **la moitié** de la barre |
| **`num_fbs=2` + attente `on_frame_buf_complete`** | *18,2 Hz* | **résiduel confiné aux ~15 % du haut — RETENU** |
| `num_fbs=2` + les deux | *12,5 Hz* | **régression** au niveau du VSYNC seul |

> ### ⚠️ Les cadences de ce tableau mesurent le GÉNÉRATEUR, pas le pipeline — *noté le 2026-08-15*
>
> **Ce qui cloche.** 28,9 Hz vaut **34,6 ms par trame**. Or le **même firmware**
> mesure un `memset` des **mêmes 614 400 octets** à **23,5 ms** (§5.4). Les
> ~11 ms d'écart ne sont pas dans l'affichage : la version du stimulus qui a
> produit ces chiffres remplissait son fond **pixel par pixel** et exécutait un
> **modulo par pixel**. Le plafond mesuré est celui du générateur de mire, pas
> celui du chemin de présentation.
>
> **Ce qui reste valide** : la **comparaison A/B**. Les cinq branches partageaient
> le même générateur, donc les écarts *relatifs* entre elles — et surtout **ce qui
> est VU**, colonne de droite — tiennent. Le classement des disciplines de
> synchronisation n'est pas remis en cause.
>
> **Ce qui ne tient plus** : les valeurs **absolues** (28,9 / 29,1 / 18,2 / 18,2 /
> 12,5 Hz) et toute conclusion tirée d'elles seules.
>
> **À rejouer** une fois le générateur corrigé (`memset` + modulo sorti de la
> boucle) : `tear on`, `tear vsync`, `tear sync`, `tear both`, `tear off`, en
> relevant la cadence de chaque branche.
>
> ⚠️ **Et le verdict que dn1-3 hérite peut bouger.** Le « résiduel confiné aux
> ~15 % du haut » a été observé sous un générateur qui prenait ~34,6 ms par
> trame, soit **1,3 trame d'affichage**. À ~23,5 ms le rapport change, et la
> hauteur du résiduel avec lui — voire sa présence. Ce point est **au registre
> des travaux différés** ; le re-mesurer est un préalable à toute décision de
> dn1-3 fondée dessus.

> **Réfutation.** `research-paysage.md` §4 annonçait « parade = double framebuffer
> PSRAM + VSYNC ». Le **double framebuffer seul ne change rien** : dans
> `esp_lcd_panel_rgb.c`, `draw_bitmap` bascule le lien DMA **immédiatement**, avec
> ce commentaire d'Espressif — *« because of DMA prefetch, there's possibility
> that the old frame buffer might be sent out again; it's hard to know the time
> when the new frame buffer starts »*. C'est la moitié « + VSYNC » qui fait le
> travail, et **pas le VSYNC** : le meilleur signal mesuré est
> `on_frame_buf_complete`.

> ### ⚠️ Le RÉSULTAT tient, le MÉCANISME qu'on lui avait donné est FAUX — *corrigé le 2026-08-15*
>
> **Ce qui n'est pas retiré** : attendre `on_frame_buf_complete` donne bien le
> déchirement le plus faible des cinq branches. C'est **observé à l'œil**, par
> l'owner, et ça reste le réglage retenu.
>
> **Ce qui est retiré, c'est l'explication.** On avait écrit que ce callback
> signifie « l'ancien tampon a fini d'être lu », là où le VSYNC ne dit que « une
> trame commence ». **Cette sémantique n'existe pas sur cet SoC.** Elle vient de
> l'événement GDMA de *link switch*, compilé uniquement sous
> `SOC_AXI_GDMA_SUPPORTED` (`components/esp_lcd/rgb/esp_lcd_panel_rgb.c:52-57`,
> qui définit alors `RGB_LCD_USE_GDMA_LINK_SWITCH_EVENT`). Or
> `components/soc/esp32s3/include/soc/soc_caps.h:33` ne définit que
> **`SOC_AHB_GDMA_SUPPORTED`** — l'ESP32-S3 n'a **pas** de GDMA AXI.
>
> Sur cette puce, le callback part donc de `lcd_rgb_panel_eof_handler()`
> (`esp_lcd_panel_rgb.c:961-967`), c'est-à-dire d'un **trans-EOF de la DMA** —
> et le commentaire d'Espressif juste au-dessus dit exactement pourquoi il ne
> faut pas s'y fier : *« Once the preload has already done, the buffer complete
> callback is not reliable. »*
>
> **Ce qu'il faut donc en dire** : `on_frame_buf_complete` place la bascule à un
> **décalage de phase différent à l'intérieur de la même trame** que le VSYNC.
> C'est empiriquement le meilleur des deux ici. Ce n'est **pas** une garantie que
> l'ancien tampon a fini d'être lu, et il ne faut pas raisonner comme si ç'en
> était une — notamment en dn1-3, où la tentation sera d'en faire un verrou.

> ⚠️ **Ces chiffres valent pour un stimulus ADVERSE** : trame pleine redessinée
> (614 400 o) à la cadence maximale, là où une UI réelle redessine des rectangles
> sales. **Le résiduel des 15 % est mesuré sous une charge que le produit ne
> verra pas** — et, comme noté ci-dessus, sous un générateur qui plafonnait
> lui-même la cadence. La comparaison entre les ms/trame du stimulus et les
> 26,7 ms de période d'affichage est **retirée** : elle chiffrait le générateur.

### 5.3 Contention flash ↔ PSRAM (AC6)

Stimulus : effacement + écriture de secteurs de 4 KiB en boucle sur la partition
`stimulus`, **sans pause**, ~**150 000 à 185 000 o/s soutenus**, ~45 secteurs/s.

**Symptôme observé, et il est pire que ce qui était annoncé** : ce n'est pas un
« scintillement », c'est **« l'image défile vers la droite EN PERMANENCE »** — un
décrochage DMA qui se reproduit à chaque secteur et dont le décalage s'accumule.

| Branche | Sous stimulus | Après arrêt |
|---|---|---|
| **bounce 0, XIP n, `ISR_IRAM_SAFE=y`** | défile | **entièrement recadrée** — voir la note sur `dma` ci-dessous — **RETENU** |
| bounce 0, **XIP y** | défile pareil | — |
| **bounce 19 200 px**, `ISR_IRAM_SAFE=y` | **redémarrage watchdog** | — |
| bounce 19 200 px, `ISR_IRAM_SAFE=n` ⚠️ *deux variables* | défile | décalage **VERTICAL persistant**, `restart()` inefficace |

> ⚠️ **La dernière ligne change DEUX variables à la fois** — le bounce buffer *et*
> `ISR_IRAM_SAFE` — ce qu'AC6 interdit (*« une seule variable à la fois »*). Elle
> ne dit donc rien de l'effet propre de `ISR_IRAM_SAFE`. La branche
> **`bounce 0, ISR_IRAM_SAFE=n`** — la seule qui l'isolerait — **n'a jamais été
> jouée**, ni ici ni ailleurs dans le dépôt.

- **XIP est réfuté pour ce défaut.** Sous stimulus **identique**, l'image défile
  **exactement pareil** avec et sans. XIP retire les *lectures* de code depuis la
  flash ; notre stimulus fait des *écritures* flash explicites, qui bloquent SPI0
  de toute façon. Coût mesuré s'il était activé quand même : **−342 876 o de
  PSRAM** (8 385 048 → 8 042 172 o libres avant framebuffers), **+1,6 Ko** de
  binaire — ⚠️ *delta à re-vérifier : les deux tailles absolues dont il est tiré
  (356,4 → 358,0 Ko) sont fausses, voir §5.4* — et temps de boot **inchangé**
  (⚠️ *chiffres absolus à re-mesurer, voir §5.4 ; l'écart relevé, ~10 ms, est du
  bruit de mesure et c'est lui qui porte le « inchangé »*).
- **Le bounce buffer est éliminé, avec deux symptômes distincts.** Avec
  `CONFIG_LCD_RGB_ISR_IRAM_SAFE=y` il provoque un **redémarrage watchdog** dès la
  première seconde du stimulus — relevé verbatim : `rst:0x8 (TG1WDT_SYS_RST)`,
  `W boot.esp32s3: PRO CPU has been reset by WDT`. Mécanisme : l'ISR de
  remplissage du bounce buffer doit lire le framebuffer **en PSRAM** alors que
  l'effacement flash a coupé le cache. Sans `IRAM_SAFE`, plus de watchdog, mais
  l'image défile **et** garde un décalage **vertical** permanent que
  `esp_lcd_rgb_panel_restart()` ne rattrape pas. Coût qu'il aurait fallu payer :
  **−74 584 o de RAM interne** (348 323 → 273 739 o libres) — ⚠️ *le point de
  départ est incertain : 348 615 o est relevé deux fois ailleurs (§5.4 et le
  journal de la story), 348 323 o n'apparaît que dans ce calcul. À re-mesurer,
  voir §5.4.*
- **La configuration retenue récupère intégralement.** Après 857 secteurs
  (3 510 272 o) écrits puis arrêt du stimulus, l'image revient **entièrement** en
  place — horizontalement **et** verticalement.

  > 🔴 **Correction : ce n'est PAS la commande `dma` qui a fait ça.** Cette
  > observation a été faite **sous la configuration retenue**, donc avec
  > `CONFIG_LCD_RGB_RESTART_IN_VSYNC=y` — et sous ce symbole
  > `esp_lcd_rgb_panel_restart()` est un **no-op** : le flag qu'il pose n'est lu
  > par personne (`esp_lcd_panel_rgb.c:1149-1165`, détail en §5.1). Le
  > redémarrage de la DMA avait déjà lieu **à chaque VBlank, automatiquement**.
  > Ce qui est démontré ici, c'est que **le défaut est entièrement réversible dès
  > que les écritures flash cessent** — un fait plus fort, et qui ne demande
  > aucun geste. Le `dma` tapé à ce moment-là n'a rien changé.

> ⚠️ **Pourquoi le fps ne sert à rien ici.** Mesuré : **37,33 Hz avant** le
> stimulus, **37,45 Hz pendant**. Le contrôleur LCD garde sa cadence même affamé —
> il sort des pixels périmés. **L'instrument d'AC6, c'est l'œil, pas le compteur.**

> ### ⚠️ `CONFIG_LCD_RGB_ISR_IRAM_SAFE=y` — conservé par précaution, **effet propre NON mesuré**
>
> **La justification d'origine est réfutée.** Le symbole avait été activé pour que
> le compteur vsync continue de tourner pendant les écritures flash. Or ce
> compteur est **aveugle au défaut de toute façon** (37,33 Hz / 37,45 Hz
> ci-dessus) : il n'y avait rien à y voir.
>
> **La justification de remplacement ne tient pas non plus.** On avait écrit
> « sans lui, le décalage devient partiellement irrattrapable ». Cette phrase
> repose entièrement sur la ligne `bounce 19 200 px, ISR_IRAM_SAFE=n` du tableau
> ci-dessus — qui change **deux variables à la fois**. **Aucune branche
> `bounce 0, ISR_IRAM_SAFE=n` n'existe** dans les mesures. L'effet propre du
> symbole n'a donc **jamais** été isolé.
>
> **Décision owner : on ne re-mesure pas, on dégrade l'affirmation.** Le symbole
> reste **activé** — son coût est nul et la contrainte qu'il impose (callback
> vsync en `IRAM_ATTR`, RAM interne seulement) est déjà respectée. Mais il est
> **conservé par précaution**, pas parce qu'un A/B l'a démontré. Écrire autre
> chose serait revendiquer une mesure qui n'a pas eu lieu.
>
> ---
>
> ### ✅ 2026-08-16 (dn1-4) — LA BRANCHE MANQUANTE A ÉTÉ JOUÉE
>
> Elle l'a été sous un **autre stimulus** que celui de cette section : non plus
> des écritures flash, mais le **polling I²C du GT911** (30 transactions/s), qui
> produit le même symptôme visuel — l'image défile.
>
> | Branche | Stimulus I²C | Verdict |
> |---|---|---|
> | bounce 0, `ISR_IRAM_SAFE=y` | **défile** | l'état livré par dn1-3 |
> | **bounce 0, `ISR_IRAM_SAFE=n`** ⬅️ *la branche jamais jouée* | **défile pareil** | **effet propre = NUL** |
> | bounce 4 800 px, `ISR_IRAM_SAFE=y` | **panique au boot** | `Guru Meditation Error: Core 0 panic'ed (Cache error). Cache disabled but cached memory region accessed` |
> | **bounce 4 800 px, `ISR_IRAM_SAFE=n`** | **STABLE** | **RETENU** — plus aucun défilement, fps 37,40 Hz (+0,01 %) |
>
> **Ce que ça règle, et qui traînait depuis dn1-2** : l'effet propre de
> `ISR_IRAM_SAFE` est **nul** sur ce défaut. Le symbole ne protégeait rien — mais
> il **empêchait** le bounce buffer de fonctionner. Les deux options étaient
> **nouées**, et c'est très probablement l'explication du « redémarrage watchdog »
> qui avait disqualifié le bounce en dn1-2 : la seule branche bounce+`n` jamais
> essayée portait 19 200 px, jamais 4 800.
>
> **Le bounce buffer est donc RÉHABILITÉ** — à 4 800 px, avec `ISR_IRAM_SAFE=n`.
>
> ⚠️ **CE QUE CETTE MESURE NE DIT PAS.** Le stimulus est de l'**I²C**, qui
> *occupe* le bus SPI0 ; celui de cette section est de l'**écriture flash**, qui
> *coupe le cache*. Ce sont deux régimes distincts, et la victoire sur l'un n'est
> pas la victoire sur l'autre. La branche « bounce 4 800, `ISR_IRAM_SAFE=n`,
> stimulus flash » **n'a pas été jouée** — elle reste une question ouverte, notée
> au ledger. **D4 reste en vigueur.**

> ⚠️ **Piège méthodologique rencontré, à ne pas refaire.** Une première lecture
> a conclu « image stable avec bounce buffer ». Elle était **fausse** : la carte
> venait de redémarrer sur watchdog et le stimulus **ne tournait pas**. Depuis,
> toute observation est précédée d'une vérification que le **compteur de secteurs
> monte réellement**.

### 5.4 Mémoire et bande passante

| Mesure | Valeur |
|---|---|
| PSRAM libre avant framebuffers | **8 385 048 o** |
| PSRAM libre après framebuffers (`num_fbs=2`) | **7 156 240 o** — soit **1 228 808 o** consommés (théorie 1 228 800) |
| PSRAM libre après framebuffers (`num_fbs=1`) | 7 770 644 o — soit 614 404 o |
| RAM interne libre (config retenue) | ⚠️ **à re-mesurer** (`mem`) — deux valeurs incompatibles au dossier : **348 615 o** et **348 323 o** |
| Temps de boot (`app_main` → prêt) | ⚠️ **à re-mesurer** — trois valeurs au dossier pour la même mesure : **864 / 858 / 854 ms** |
| Taille du binaire | ⚠️ **à re-mesurer** (`idf.py build`) — relevé du 2026-08-14 : `0x57b20` = **359 200 o** (350,8 KiB) ; dernière reconstruction de l'arbre courant : `0x59480` = **365 696 o** (357,1 KiB), soit **~91 % libres** sur la partition de 4 MiB |
| **Charge CPU** au repos, config retenue | **0,0 %** — réserve `IDLE0`+`IDLE1` = **100,0 %**. Mesuré le **2026-08-15**, fenêtre de 30 s (`cpu 30`), asset affiché, aucun stimulus. ⇒ **tenir l'image ne coûte RIEN au processeur** : la DMA est matérielle. C'est le budget que dn3-2 peut dépenser en entier. |

> ### ⚠️ Les quatre chiffres ci-dessus se contredisaient — état exact, *au 2026-08-15*
>
> Aucune valeur n'a été inventée pour trancher : là où l'arithmétique ne
> départage pas, la case dit **à re-mesurer**.
>
> - **Taille du binaire — l'arithmétique tranche, et contre les deux lectures.**
>   `0x57b20` vaut **359 200 octets**, soit **350,8 KiB** ou **359,2 ko** selon la
>   convention. **Aucune des deux ne donne 356,4** : la conversion publiée était
>   fausse. Par ailleurs le chiffre est **périmé** — la dernière reconstruction de
>   l'arbre courant rend `0x59480` (365 696 o). Le `+1,6 Ko` de §5.3 (delta XIP)
>   était calculé sur cette base fausse : le *delta* reste plausible (les deux
>   termes subissaient la même conversion), les *absolus* sont à jeter.
> - **RAM interne — l'arithmétique ne tranche pas.** `348 615 o` est relevé deux
>   fois (ici et au journal de la story) ; mais le delta bounce buffer de §5.3
>   (**−74 584 o**, jusqu'à 273 739 o) n'est cohérent qu'avec **348 323 o**
>   (348 323 − 74 584 = 273 739 ✓, alors que 348 615 − 273 739 = 74 876 ✗).
>   Écart : 292 octets. Une seule des deux est la vraie mesure, et rien au dossier
>   ne dit laquelle. **Rejouer `mem` dans la configuration retenue.**
> - **Temps de boot — l'arithmétique ne tranche pas** : 864 ms (§5.3), 858 ms
>   (ce tableau) et 854 ms (journal de la story) désignent la même mesure. L'écart
>   total, **10 ms sur ~858**, soit 1,2 %, est de l'ordre du bruit d'une mesure de
>   boot : c'est pourquoi le verdict « XIP ne change pas le temps de boot » de
>   §5.3, lui, **survit**. C'est le chiffre publiable qui manque.
> - **Charge CPU — elle ne se contredit pas, elle n'existait pas.** AC6 demandait
>   « PSRAM consommée, temps de boot, **charge CPU** » : les deux premiers sont
>   ci-dessus, la troisième **n'était mesurée nulle part dans le dépôt**. Elle est
>   maintenant instrumentée ; la case attend le relevé.

**Bande passante des trois chemins de copie** (`bw` en console, meilleur de 5) —
mesurés **séparément** parce qu'ils n'ont pas le même goulot :

| Chemin | Temps pour 614 400 o | Débit | vs budget de trame (26,7 ms) |
|---|---:|---:|---|
| Remplissage PSRAM (`memset`) | **23,5 ms** | **26,2 Mo/s** | **tient tout juste** |
| PSRAM → PSRAM (`memcpy`) | **36,8 ms** | 16,7 Mo/s | **1,4× trop lent** |
| flash `mmap` → PSRAM | **74,9 ms** | 8,2 Mo/s | **2,8× trop lent** |

> **Le chiffre que dn3-2 doit retenir.** Un simple **aplat plein écran** consomme
> déjà **presque toute une trame** (23,5 ms sur 26,7), et cela **pendant que la
> DMA lit 23,0 Mo/s en continu**. Redessiner la trame entière à chaque image est
> hors budget sur cette carte : l'UI devra travailler en **rectangles sales**.
>
> ⚠️ **Retiré le 2026-08-15** : « c'est aussi pourquoi le stimulus d'AC5 plafonne
> à ~29 Hz et pourquoi le déchirement y est inévitable ». Faux — 28,9 Hz vaut
> 34,6 ms/trame, soit **11 ms de plus** que le `memset` de la même quantité
> d'octets (23,5 ms) mesuré par le même firmware. Ce plafond était celui du
> **générateur de mire** (remplissage pixel à pixel, un modulo par pixel), pas
> celui du chemin d'affichage. La phrase du dessus, elle, tient : elle repose
> directement sur les 23,5 ms mesurés. Voir §5.2.
>
> ⚠️ **Ne pas confondre les trois.** Les 8,2 Mo/s de la copie d'asset sont
> dominés par la **lecture flash**, pas par la PSRAM. Les prendre pour la bande
> passante PSRAM ferait sous-estimer la carte d'un facteur 3.

---

## 6. Provenance de la séquence d'init ST7701S

- **Fichier** : `firmware/desknode/main/dn_st7701_init.h` — **45 commandes**.
- **Source** : `github.com/bundoon/Waveshare-ESP32-S3Touch-LCD-2.8B-Display-Working-with-ESPHome`,
  fichier `working_st7701s_template.yaml`, clé `init_sequence:`, branche `main`,
  **récupérée le 2026-08-14**.
- **Origine amont revendiquée** : extraction du driver C Waveshare de cette carte
  exacte. Marqueur : la séquence commence par `FF 77 01 00 00 13`, la sélection
  Command2 BK3 propre au ST7701S.
- **Pourquoi ne pas prendre celle du driver** : `esp_lcd_st7701` embarque un jeu
  générique (480 × 480). Le dépôt communautaire documente que c'est précisément
  là que tout le monde se casse les dents.
- **Ce que le driver envoie AVANT cette table** : `FF 77 01 00 00 00` (sortie de
  Command2), puis `MADCTL` (0x36) et `COLMOD` (0x3A, valeur **0x50** pour
  16 bpp), déduits de `rgb_ele_order` et `bits_per_pixel`. C'est pourquoi la
  table n'en contient ni l'un ni l'autre.

> ### ⚠️ LE TROU QUI A COÛTÉ LE PREMIER ALLUMAGE — `0x29` (DISPON)
>
> **Symptôme** : dalle nettement rétroéclairée, **uniformément GRISE**, aucune
> image — et pourtant le compteur vsync tournait à 37,40 Hz exacts, l'expander
> répondait en I²C, et **aucune fonction ne renvoyait d'erreur**. Tous les
> voyants au vert, écran vide.
>
> **Cause** : la séquence vendeur reprise d'ESPHome s'arrête à `0x35` (TEON) et
> **ne contient pas `0x29` (DISPON)** — ESPHome l'envoie de son côté, hors de la
> clé `init_sequence`. Or `esp_lcd_panel_init()` ne l'envoie pas non plus : dans
> `esp_lcd_st7701_rgb.c`, DISPON est la **dernière entrée du jeu d'init PAR
> DÉFAUT** (ligne 199) — celui-là même qu'on remplace. **En fournissant
> `init_cmds`, on hérite du trou.**
>
> **Parade** : appeler explicitement `esp_lcd_panel_disp_on_off(panel, true)`
> après `esp_lcd_panel_init()`. Comme `disp_gpio_num` vaut −1, le driver le
> traduit en commande `0x29` sur le bus 3-wire.
>
> **Témoin rejouable** : la commande console `disp off` reproduit exactement le
> symptôme (dalle grise et éclairée), `disp on` le lève. À ne pas confondre avec
> `bl off`, qui donne une dalle **noire**.

---

## 7. Les 11 éliminations, avec leur symptôme

*Une élimination sans symptôme relevé n'est pas une élimination, c'est une opinion.*

> **Décompte, corrigé le 2026-08-15 : il y en a 11, pas 12.** Le « 12 » annoncé
> par AC8 comptait le paragraphe sur les textes fins violets qui suit le tableau —
> or celui-ci est explicitement étiqueté *« Non expliqué, non bloquant »* : ce
> n'est pas une élimination, c'est une observation ouverte. Le tableau fait foi.

| Ce qui a été éliminé | Symptôme **observé** |
|---|---|
| Ordre des bits ESPHome lu comme LSB→MSB | poids forts (16, 32) noirs dans chaque groupe, blanc plein pourtant neutre, asymétrie 4-verts contre 2-bleus |
| Séquence vendeur **sans** `0x29` | dalle grise uniforme, rétroéclairée, vsync à 37,40 Hz, aucune erreur remontée |
| `CONFIG_LCD_RGB_RESTART_IN_VSYNC=n` | image coupée en deux, la droite revenant sur la gauche, en permanence dès le boot |
| `num_fbs=2` sans synchronisation | déchirement **inchangé** par rapport à `num_fbs=1` |
| Synchronisation sur le **VSYNC** | escalier réduit de moitié seulement |
| Synchronisation **VSYNC + `fb_complete`** | **régression** : retour au niveau du VSYNC seul, et cadence divisée par 2 |
| `CONFIG_SPIRAM_XIP_FROM_PSRAM=y` | défilement sous stimulus flash **identique** ; coûte 342 876 o de PSRAM |
| `bounce_buffer_size_px=19200` + `ISR_IRAM_SAFE=y` | **`rst:0x8 (TG1WDT_SYS_RST)`**, « PRO CPU has been reset by WDT » |
| `bounce_buffer_size_px=19200` + `ISR_IRAM_SAFE=n` | défilement, puis décalage **vertical** permanent que `restart()` ne rattrape pas |
| Mire de bits en **16 bandes verticales** de 30 px | illisible sur 2,8" ; a produit une lecture réfutée dans la minute par le blanc plein |
| Stimulus de déchirement par **bascule noir/blanc** plein écran | « l'écran clignote violemment » — le papillotement **masque** le déchirement cherché |

**Non expliqué, non bloquant** : à l'œil, les **textes fins clairs de l'asset**
tirent au **violet**. Le blanc **pur** sur grande surface, lui, est **neutre**
(vérifié sur la barre du stimulus) — c'est donc un effet de rendu sur traits fins,
pas un défaut du pipeline. À revoir en dn1-3, où LVGL rendra du texte antialiasé.

---

## 8. Ce que P1 ne ferme pas

- ~~**Le déchirement résiduel des ~15 % du haut** en redessin plein écran.~~
  ✅ **SANS OBJET depuis le 2026-08-15.** dn1-3 a re-mesuré le déchirement là où
  ça redessine, avec un instrument re-validé par témoin positif (§10.4) : sous
  rendu partiel il n'y a plus de redessin plein écran ni de bascule, et le
  déchirement est supprimé par `flush sync vsync`. Le chiffre des 15 % venait
  d'un générateur invalidé ; il n'est **ni reconduit ni confirmé**, il est retiré.
- **La discipline de bascule d'image n'est pas dans le chemin produit.**
  `dn_display_present()` bascule **sans attendre** ; l'attente n'existe que dans
  le stimulus. Décision owner : c'est **à dn1-3 de l'implémenter** s'il redessine
  des trames entières. Détail et références de code : encadré de la §4.
- **La contention flash ↔ PSRAM** n'a **aucune parade logicielle** trouvée. La
  mitigation est architecturale : **ne pas écrire en flash pendant l'affichage**.
  La décision owner **D4** (pas d'OTA en V1) va déjà dans ce sens.

  > 🔴 **Recommandation corrigée le 2026-08-15.** On lisait ici : *« toute
  > écriture inévitable doit être suivie d'un `esp_lcd_rgb_panel_restart()` »*.
  > **Ce conseil est inerte dans le binaire livré** : sous
  > `CONFIG_LCD_RGB_RESTART_IN_VSYNC=y` — la configuration retenue —
  > `lcd_rgb_panel_try_restart_transmission()` redémarre la DMA **à chaque
  > VBlank sans condition** et ne lit jamais le flag `need_restart` que
  > `esp_lcd_rgb_panel_restart()` est seul à poser
  > (`components/esp_lcd/rgb/esp_lcd_panel_rgb.c:1149-1165`, contre les lignes
  > 464/472 pour la pose du flag). Appeler la fonction ne fait donc **rien**.
  >
  > **Ce qu'il faut faire à la place** : rien de plus que cesser d'écrire — la
  > §5.3 montre que l'image redevient **entièrement correcte d'elle-même** dès
  > l'arrêt des écritures, sans aucun geste. Ce qui doit être encadré, c'est la
  > **durée** pendant laquelle on écrit, pas le nettoyage après.
  >
  > **Et si un jour on repasse à `RESTART_IN_VSYNC=n`** (branche `#else`, qui
  > consomme bien le flag), alors le conseil d'origine redevient valable — mais
  > il faudra le réécrire en le conditionnant explicitement à ce symbole.
- **L'identité visuelle** du Living PCB : l'asset de P1 est un brouillon assumé
  (dn3-3).
- ~~**La gradation** du rétroéclairage (dn1-3) : ici GPIO6 est en tout-ou-rien.~~
  ✅ **FERMÉ le 2026-08-15** : GPIO6 est en LEDC 10 bits, et la fréquence du
  pattern de référence d'Espressif a été **démentie à l'oreille** — voir §10.6.
- L'inventaire physique des breakouts et le câblage photographié (dn2-1, dn4-1) —
  **ce fichier ne couvre que l'affichage**.

---

## 9. Rejouer les mesures

Toutes les mires et tous les stimuli sont dans le firmware, accessibles à la
console série (`idf.py monitor`, taper la commande) :

```
aide                réimprime le bandeau : la liste complète des commandes
scene bits|nbits|rgb|red|green|blue|white|black|frame|gray|asset
fps [secondes]      mesure et confronte aux 37,40 Hz théoriques
bw                  bande passante des 3 chemins de copie
mem                 PSRAM et RAM interne, avant/après framebuffers
cpu                 charge CPU par tâche (vTaskGetRunTimeStats)
cfg                 configuration de boot (NVS) et configuration active
set fbs <1|2|3> | set bounce <px>     s'applique au `reboot` suivant
reboot              redémarre pour appliquer un `set`
tear on|vsync|sync|both|flip|off      les 5 branches d'AC5
flash on|off        le stimulus d'écriture flash d'AC6
disp on|off         sortie d'affichage de la dalle (0x29/0x28)
bl on|off           rétroéclairage
dma                 esp_lcd_rgb_panel_restart()  ⚠️ NO-OP ici, voir ci-dessous
```

> ⚠️ **`aide` est la source de vérité, pas cette liste.** Le bandeau est généré à
> partir de la table `k_cmds[]` de `dn_console.c` : si une commande est ajoutée
> sans que ce fichier soit mis à jour, c'est `aide` qui a raison. Une **forme de
> remise à zéro de la configuration** (retour aux défauts de `dn_bootcfg.c` sans
> passer par un effacement NVS externe) est en cours d'ajout à la famille `set` —
> taper `aide` pour en connaître la syntaxe exacte.

> 🔴 **`dma` ne fait RIEN dans la configuration retenue.** Sous
> `CONFIG_LCD_RGB_RESTART_IN_VSYNC=y`, `esp_lcd_rgb_panel_restart()` pose un flag
> que personne ne lit — le redémarrage a déjà lieu à chaque VBlank
> (`components/esp_lcd/rgb/esp_lcd_panel_rgb.c:1149-1165`). La commande n'a d'effet
> qu'avec `RESTART_IN_VSYNC=n`. **Ne créditer aucune récupération d'image à ce
> `dma`** tant qu'on est sur la configuration de référence : détail en §5.1.

> ⚠️ **`reboot` fait tomber l'attachement `usbipd`.** `esp_restart()` se comporte
> comme un reset de puce : l'USB se ré-énumère, `/dev/ttyACM0` revient en
> `root:root` et toute lecture échoue avec `[Errno 13] Permission denied`.
> Rejouer `./tools/wsl-attach.sh` après chaque `reboot`. C'est le même fait que
> dn1-1 avait mesuré pour le bouton RESET et `--after watchdog_reset`.

---

## 10. La couche UI — LVGL 9.5.0, mesuré le 2026-08-15 (dn1-3)

### 10.1 Ce qui est intégré, et ce que le portage ne fait PAS

`lvgl/lvgl==9.5.0` + `espressif/esp_lvgl_port==2.9.0`, épinglés à l'exact, vérifiés au registre.
`dn_ui.c` monte LVGL **sur** le socle : `dn_display` garde tout le bring-up, LVGL reçoit les
handles esp_lcd déjà créés et n'alloue ni framebuffer ni panneau.

Deux découvertes qui contredisent ce que la story tenait pour acquis :

1. **`avoid_tearing` du portage exige `num_fbs >= 2`** — il appelle
   `esp_lcd_rgb_panel_get_frame_buffer(panel, 2, …)` (`esp_lvgl_port_disp.c:367`). Inutilisable
   dans la configuration de référence.
2. **EN RENDU PARTIEL, LE PORTAGE NE SYNCHRONISE RIEN.** La story annonçait « flush synchronisé
   sur `on_vsync` (le port l'enregistre lui-même) ». C'est **faux** : son
   `lvgl_port_flush_callback()` n'attend `trans_sem` que dans la branche
   `direct_mode || full_refresh` (`esp_lvgl_port_disp.c:748-756`) ; en partiel il tombe dans le
   `else` et rend la main **sans aucune attente** (`:758`). Le `on_vsync` qu'il enregistre
   alimente donc un sémaphore que **personne n'attend** dans notre configuration.
   ⇒ `dn_ui_flush()` **remplace** le flush du portage et porte lui-même la synchronisation, son
   instrument et son interrupteur.

⚠️ **PIÈGE N°1 DU PROJET, VÉRIFIÉ À LA SOURCE.**
`esp_lcd_rgb_panel_register_event_callbacks()` **ASSIGNE** les quatre pointeurs et `user_ctx`
(`esp_lcd_panel_rgb.c:444-448`) — il ne fusionne rien. Or `lvgl_port_add_disp_rgb()` enregistre
son propre `on_vsync` sans condition (`esp_lvgl_port_disp.c:219`). **Le dernier qui parle efface
l'autre, en silence, en rendant `ESP_OK`.** Ordre retenu : `dn_measure_attach()` **après** le
portage, plus un **témoin actif** au boot (`dn_measure_vsync_alive()`, « 4 trames en 100 ms »).
Sans ce témoin, `fps`, la synchro du flush et toute mesure de déchirement mesureraient du vide,
à l'étiquette près.

### 10.2 Les budgets — la référence que dn3-2 dépensera

Configuration : `num_fbs=1`, rendu partiel, draw buffer 480×64 (61 440 o) en RAM interne DMA,
flush synchronisé `vsync`, fond lu en flash `mmap`.

| Mesure | Socle nu (dn1-2) | LVGL au repos | LVGL, label 1 Hz |
|---|---|---|---|
| Charge CPU (`cpu`) | **0,0 %** | **0,3 %** (esp_timer, le tick 5 ms) | **0,9 %** (taskLVGL 0,5 + esp_timer 0,3) |
| Flushes | — | **0** (rien ne redessine) | **1,00 par cycle** |
| `fps` | 37,40 Hz | — | **37,40 Hz** (théorique 37,40 — écart **+0,00 %**) |

> ⚠️ **Portée honnête du « fps inchangé » (revue de code).** AC8 dit « 37,40 Hz
> inchangés dans toutes les configs mesurées » ; le chiffre n'a été CONSIGNÉ que
> pour la config nominale (et le rejeu final, +0,01 %). Les variantes PSRAM,
> 8/32/128 lignes, 2 FB/direct et le régime `anim` ont tourné sans qu'un `fps`
> y soit relevé. Aucun signe contraire (le compteur vsync est resté cohérent
> partout), mais « pas relevé » n'est pas « mesuré inchangé » — la distinction
> est la règle du dépôt.

| Mémoire | |
|---|---|
| RAM interne, avant → après init LVGL | 281 415 → **212 015 o** (−69 400) |
| PSRAM, avant → après init LVGL | 7 770 588 → **7 770 588 o** (−0) |
| Tas LVGL réellement utilisé | **6 588 o sur 63 736** (11 %), fragmentation 1 % |
| Binaire, avant → après LVGL | 377 664 → **740 400 o**, app 4 MiB **82 % libre** |

⚠️ **Les 64 Ko de `LV_MEM_SIZE_KILOBYTES` sont STATIQUES** (`.bss`, prélevés au link) : ils
**n'apparaissent pas** dans l'avant/après de `mem`. Le seul instrument qui les voie est la
commande `ui`, qui imprime `lv_mem_monitor()`. Une mesure de tas qui les ignore sous-estime LVGL
de 64 Ko.

### 10.3 Le rafraîchissement partiel — en chiffres (AC3)

Régime produit, label 1 Hz, mesuré sur 60 s :

| | |
|---|---|
| Cycles | **61 en 60 s** — 1,00/s, aucune dérive (confronté au battement `up N s` de 90 s à 140 s) |
| Flushes par cycle | **1,00** — la zone du label tient dans une bande de 64 lignes |
| Aire par mise à jour | **15 892 px = 5,17 %** des 307 200 px de l'écran |
| Copie | **1 169 µs** en moyenne, 1 219 µs au pire |
| Attente de synchro | **12 669 µs** — soit la moitié de la période de trame (26,7 ms), ce qu'on attend d'une attente uniforme du prochain vsync : **contrôle de cohérence de l'instrument** |

**Preuve négative** — redessin plein écran forcé, même configuration : **10 flushes de 30 720 px,
307 200 px, ~21,8 ms de copie et ~176 ms d'attente**, soit ~5,5 Hz au mieux. Le mode plein écran
ne pourrait jamais tenir 37,40 Hz.

**A/B de l'EMPLACEMENT du draw buffer** — aire strictement identique (323 092 px), une seule
variable :

| | copie/flush | plein écran |
|---|---|---|
| RAM interne DMA | **2 180 µs** | ~21,8 ms |
| PSRAM | **3 709 µs** | ~37,1 ms |

La PSRAM est **1,70× plus lente**, et ses 37,1 ms recoupent le memcpy PSRAM→PSRAM du §5.4
(36,8 ms) **à 0,8 % près** — deux instruments indépendants, le même chiffre. ⇒ **RAM interne**.

**A/B de la TAILLE** — même aire (323 092 px), RAM interne :

| lignes | flushes | copie totale | copie/flush | attente de synchro |
|---|---|---|---|---|
| 32 | 22 | 22 794 µs | 1 036 µs | 433 272 µs |
| 64 | 11 | **23 989 µs** (rejeu : 23 950, **+0,16 %**) | 2 180 µs | 176 044 µs |
| 128 | 6 | 24 892 µs | 4 148 µs | 67 325 µs |

> 🔴 **UNE LECTURE DU SOURCE RÉFUTÉE PAR LA CARTE.** On avait conclu du source
> (`bytes_to_flush = v_res * bytes_per_line` puis `esp_cache_msync()` depuis le début du
> framebuffer, branche `draw_buf_copy_to_fb`) qu'un **coût fixe de 614 400 o par flush**
> dominerait tout. Le tableau le dit non : le nombre de flushes varie d'un facteur **3,7** et le
> temps total ne bouge que de **9 %**, dans le mauvais sens. Un coût fixe ajusté sur ces points
> sort **négatif** — il est donc **sous le seuil de détection (< ~0,1 ms)**. Un `esp_cache_msync`
> en écriture parcourt des **lignes de cache**, il ne transfère pas 614 400 octets : la lecture
> du source avait confondu une plage d'adresses avec un volume. Débit observé : **~27-29 Mo/s**,
> RAM interne → framebuffer PSRAM.
> Confirmation directe : un chemin de flush qui n'écrit QUE les lignes salies et ne resynchronise
> QUE celles-là (`flush path direct`) ne gagne que **4,4 %** (1 113 contre 1 164 µs).

⇒ **64 lignes retenu** : le régime produit tient en **un seul flush**, et l'attente de synchro
d'un plein écran (176 ms) reste raisonnable. 128 lignes ne gagneraient que sur le plein écran —
qui n'est pas le régime de ce produit — pour le double de RAM interne.

### 10.4 Le déchirement, re-mesuré là où ça redessine (AC4)

**Le témoin positif d'abord**, comme exigé — et il est venu du régime **produit**, pas du stimulus
adverse :

| Synchro du flush | Constat owner, label 1 Hz sur le Living PCB |
|---|---|
| `off` | **« des déchirements en plus »** — l'instrument (l'œil) VOIT le déchirement |
| `vsync` | **plus de déchirement** |

⇒ Le témoin positif est établi, donc le verdict « pas de déchirement en `vsync` » est **recevable**
— **pour le régime produit**. `vsync` est retenu. Le mode `off` est **conservé** dans le firmware :
c'est la réfutation de `vsync`, et une élimination sans son témoin n'est pas une élimination.

**Le verdict sous le STIMULUS ADVERSE, config nominale — MESURÉ le 2026-08-15 (revue de code).**
La première rédaction de cette section l'avait écarté (« il n'a pas eu à être invoqué ») : c'était
répondre à la puce 1 d'AC4 (le témoin) et pas à la 2 (le verdict adverse). La revue l'a relevé,
l'owner a choisi de REJOUER plutôt que de déclarer un constat non fait. Protocole dans les règles :
témoin d'abord, sous le stimulus lui-même, puis une variable à la fois. Barre `anim` 24 px pleine
hauteur, période 2 000 ms, label visible, œil de l'owner :

| Synchro | Constat owner, barre adverse |
|---|---|
| `off` | **se coupe** — le témoin positif tient AUSSI sous ce stimulus |
| `vsync` | **« se coupe encore »** — le verdict adverse est NÉGATIF |
| `fbdone` | **PIRE** : « ça scintille à fond, une ligne blanche complète + des morceaux artefactés de ligne blanche déchirée » |

⇒ **`vsync` supprime le déchirement en régime produit, PAS sous la barre adverse** — et c'est
cohérent avec la réserve écrite dès le départ dans `dn_ui.h` (« fenêtre de course réduite, PAS de
garantie formelle ») : une zone sale PLEINE HAUTEUR croise forcément le faisceau pendant la copie,
quel que soit le point de départ. Le mécanisme est désormais MESURÉ, plus seulement prédit. Les
deux verdicts ne se confondent plus, exactement ce qu'AC4 exigeait — et c'est le régime PRODUIT
(zones sales bornées en hauteur) qui définit la config de référence, pas l'adverse. Conséquence
pour dn3 : un widget qui redessinerait une COLONNE pleine hauteur retombera dans le cas adverse.
Le « confinement aux ~15 % du haut » de dn1-2 en `fbdone` ne se reproduit pas ici — sous ce
stimulus, `fbdone` est le pire des trois modes.

Chiffres du stimulus, pour mémoire : 442 flushes en 15 s ≈ 29,5/s, CPU 20,3 %.

**Le « résiduel des ~15 % du haut » de dn1-2 n'est PAS reconduit.** Il avait été relevé avec un
instrument depuis invalidé, et la configuration a changé (rendu partiel, plus de bascule). Il est
**sans objet ici** — pas reporté, pas confirmé.

### 10.5 ✅ L'ARTEFACT DE REDESSIN LVGL — **RÉSOLU le 2026-08-16 (dn1-4)**

> ## ✅ CAUSE TROUVÉE, ET CORRIGÉE — 2026-08-16
>
> **La cause n'était aucune des sept hypothèses ci-dessous. C'était la DMA du
> panneau RGB affamée sur le bus SPI0**, que la flash et la PSRAM se partagent sur
> ESP32-S3. Le correctif est le **bounce buffer** (`bounce_px = 4800`), qui fait
> lire la DMA en RAM interne au lieu d'aller chercher le framebuffer en PSRAM.
>
> **Constat owner, avec le témoin exact de cette section** (label 1 Hz rallumé sur
> le Living PCB) : *« plus aucun clignotement, l'image est stable et ça s'incrémente
> bien »*.
>
> **Ce qui a mis sur la piste** — et qui n'aurait pas pu être vu avant dn1-4 : le
> tactile a introduit le **premier trafic I²C en fonctionnement** de ce projet (le
> TCA9554 ne sert qu'au boot). Or ce trafic produisait un symptôme de la même
> famille, mais **permanent et bien plus violent** : l'image défilait à toute
> vitesse. Le voir en continu, et pouvoir l'allumer et l'éteindre à volonté
> (`touch mode poll|event`), a rendu la cause attaquable — là où un clignotement
> d'une seule trame par seconde ne l'était pas. Détail complet en **§11.4**.
>
> **Pourquoi les sept hypothèses tombaient toutes à côté** : elles cherchaient dans
> le CONTENU (fond flash/PSRAM), la PHASE (off/vsync/fbdone), le VOLUME écrit
> (chemin direct, `set lines`), le TAMPON (num_fbs), les LECTURES (XIP) et
> l'AFFINITÉ (cœur). Aucune ne testait **la disponibilité du bus pour la DMA**.
> L'anomalie qui aurait dû mettre la puce à l'oreille est d'ailleurs consignée
> plus bas — *« absent du chemin brut qui écrit 20× plus »* : un `memcpy` séquentiel
> ne provoque pas les défauts de cache qu'un flush LVGL provoque.
>
> ⚠️ **Ce que ça coûte** : RAM interne 2 × 9 600 o ; **rien de mesurable au repos**
> (0,8 % de charge avant comme après) et **+1,1 point** en redessin (label 1 Hz :
> 0,9 % → 2,0 %) ; et surtout **+160 ms de latence de transition** (267,9 →
> 427,7 ms à 64 lignes) — voir §11.5, où le budget < 300 ms est confronté à ce prix.
>
> *Le texte d'origine est conservé ci-dessous : les sept éliminations restent
> vraies, et une élimination sans son symptôme n'est pas une élimination.*

**Symptôme, constat owner du 2026-08-15 :** à chaque cycle de rafraîchissement LVGL, **l'image
entière « clignote, comme un déplacement rapide » le temps d'une trame**. Avec le label à 1 Hz,
cela se produit une fois par seconde. **AC2 (« la mise à jour du label ne fait ni clignoter ni
frémir le fond ») n'est donc PAS satisfait.**

**Ce qui est ÉTABLI :**

- **Témoin négatif propre** : LVGL en pause, l'image est **parfaitement stable**. L'artefact est
  bien lié à l'acte de redessiner.
- **Indépendant du CONTENU** : LVGL redessinant six fois l'écran entier avec un contenu
  strictement identique, label masqué, produit le **même artefact**.
- **Le chemin brut de dn1-2 en est EXEMPT** : `dn_pattern_draw` + `dn_display_present()`
  redessinant six fois la même image — **614 400 octets, vingt fois plus** que le flush du label
  — ne produit **rien du tout**.

⇒ **Un défaut qui empire quand on écrit vingt fois moins n'est pas un défaut de bande passante.**
La contention mémoire, qui était l'explication de départ, est réfutée par son propre témoin.

**Les sept hypothèses éliminées, chacune avec son témoin (AC9) :**

| # | Hypothèse | Témoin joué | Verdict |
|---|---|---|---|
| 1 | Phase de la copie dans le balayage | `flush sync off` / `vsync` / `fbdone` | ❌ présent dans tous les modes (avec du déchirement **en plus** en `off`) |
| 2 | Lecture du fond depuis la flash `mmap` (contention SPI0, §5.3) | `ui bg psram` — copie PSRAM du fond, 614 400 o | ❌ **identique** |
| 3 | Parcours de cache pleine plage de `draw_bitmap` (614 400 o/flush) | `flush path direct` — 42 240 o resynchronisés | ❌ **identique** |
| 4 | Débit instantané de la copie | `set lines 8` — 5 rafales de 249 µs au lieu d'une de 1 113 µs, mêmes octets | ❌ **identique** |
| 5 | Écriture dans le tampon que la DMA balaie | `num_fbs=2` + rendu **direct** — le flush ne fait que basculer, zéro octet copié | ❌ **identique** |
| 6 | Lectures de code/constantes en flash (483 268 o « map » au bandeau de boot) | branche XIP (`SPIRAM_FETCH_INSTRUCTIONS` + `SPIRAM_RODATA`), fichier `sdkconfig.defaults.xip-lecture-code` | ❌ **identique** — et la réfutation de dn1-2 (§5.3) portait sur les ÉCRITURES ; celle-ci porte sur les LECTURES, et échoue aussi |
| 7 | Affinité de la tâche LVGL au cœur 1, en face du pipeline d'affichage | `set core 0` — le rendu sur le même cœur que le reste, comme le chemin brut | ❌ **identique** |

**Ce qui reste à explorer, non mesuré :** ce que la tâche LVGL fait et que le chemin brut ne fait
pas — le tick `esp_timer` à 5 ms, la mécanique de réveil du portage, le motif d'accès du blit de
LVGL (par lignes avec pas) contre le `memcpy` séquentiel du chemin brut. **Aucune de ces pistes
n'a été jouée** : l'investigation a été bornée ici, par la consigne de périmètre de la story.

⚠️ **Ce défaut n'est PAS un argument pour le double tampon** : il est identique dans les deux
configurations (ligne 5 du tableau). Il ne doit donc pas être invoqué pour arbitrer §4 ter.

⇒ **Porté au ledger pour dn1-4**, avec ce tableau. Le terrain est déblayé : sept explications
plausibles sont mortes, et la prochaine tentative n'aura pas à les rejouer.

### 10.6 Le rétroéclairage gradable (AC7)

GPIO6 passe de `gpio_set_level` à **LEDC** : `LEDC_LOW_SPEED_MODE`, timer 0, canal 0,
**10 bits (1 024 crans)**, `LEDC_AUTO_CLK`, duty 0 dès l'init, montée après la première trame
LVGL. `bl 0..100`, `bl on|off` (rétrocompat), `bl ramp <pct> [ms]`, `bl freq <hz>`.

> 🔴 **LE PATTERN DE RÉFÉRENCE D'ESPRESSIF EST DÉMENTI PAR L'OREILLE.**
> `esp_bsp_generic.c` pose **5 kHz**, et notre première version l'a repris tel quel en écrivant
> « sifflement inaudible en pratique ». **Mesuré faux sur cette carte** : à 3 % de duty, l'owner
> **entend** distinctement un sifflement. La phrase venait d'un BSP générique — c'était une
> prédiction déguisée en acquis.
> A/B joué à luminosité **strictement constante** (3 %), une seule variable, via `ledc_set_freq`
> qui reprogramme le diviseur sans toucher au duty :
> **5 000 Hz → sifflement AUDIBLE · 24 000 Hz → plus rien à l'oreille.**
> ⇒ **24 kHz retenu comme défaut** (au-dessus de la limite haute de l'audition adulte, ~18 kHz).

| Constat AC7 | Résultat |
|---|---|
| Sifflement à duty bas | **supprimé à 24 kHz** (audible à 5 kHz) |
| Papillotement à 3 % | **présent en dn1-3 — mais PAS imputable au rétroéclairage.** Témoin : LVGL mis en pause à luminosité identique, l'image était **parfaitement stable**. C'était l'artefact §10.5, que la basse luminosité rendait plus visible. ✅ **Cet artefact est CORRIGÉ depuis le 2026-08-16** (bounce buffer, §11.4) ; le papillotement à basse luminosité n'a pas été re-cherché spécifiquement, mais l'image est stable à 10 % (constat owner pendant les rampes) |
| Plancher lisible | **3 % = limite** — le Living PCB et le label s'y distinguent encore, tout juste. C'est le plancher du futur mode Ambient |
| Rampe 100→10→100 | ✅ **OBSERVÉE le 2026-08-16 (dn1-4)** — constat owner : **« c'est progressif, aucun palier »**. Rampes de 10 s dans les deux sens, sortie console vérifiée avant le constat. ⚠️ Il a fallu d'abord prouver la gradation par un état STATIQUE (`bl 10` laissé en place : *« oui c'est bien plus sombre »*) pour séparer « je n'ai pas vu » de « ça ne bouge pas », puis intercaler un `fps 10` avant la rampe pour donner le temps de se placer |
| `bl 0` vs `disp off` | distincts et documentés dans l'aide : noir contre gris éclairé |

### 10.7 L'observation « textes fins violets » — REPRODUITE

Héritée de dn1-2 sur l'asset v0, elle était à rejouer sur du texte antialiasé LVGL.
**Constat owner : « oui le texte est violet ».** Le phénomène **se reproduit** sur les jambages
fins du label (Montserrat 28, blanc sur fond sombre). Explication non exigée par la story, non
fournie ici. Il n'est donc pas propre au générateur d'asset : c'est la dalle, le sous-pixel, ou
la conversion RGB565 — à trancher si un jour ça gêne.

---

## 11. LE TACTILE — Goodix GT911, mesuré le 2026-08-16 (dn1-4, P3)

### 11.1 Ce que le contrôleur a répondu

```
I (1461) dn_touch: probe AVANT reset : il répond DÉJÀ à 0x5D
I (1812) dn_disp: reset tactile joué via l'expander bit1/EXIO2 (150 ms bas, 50 ms de repos)
I (1813) dn_touch: probe APRÈS reset : ESP_OK — adresse RÉELLE 0x5D (visée 0x5D)
I (1814) dn_touch: GT911 « 911 » fw 0x1060 · config v93 · résolution native 480x640 · 5 points · INT sur front DESCENDANT
```

| | Valeur mesurée | Ce que ça corrige |
|---|---|---|
| Adresse I²C | **0x5D** | conforme à l'attendu — mais c'est la séquence qui la garantit, pas la chance (§1.3) |
| Identité | « 911 », fw **0x1060**, config **v93** | — |
| Résolution **déclarée par le GT911** | **480 × 640** | ⚠️ la démo Waveshare passe `x_max=640, y_max=480` : **ses valeurs sont écartées**, le contrôleur lui-même dit le contraire |
| Points simultanés | **5** | dn1-4 n'en exploite qu'un (le tap) |
| Déclenchement de l'INT | **front DESCENDANT** (reg `0x804D` bits 1-0 = 1) | lu **avant** de créer le driver, pour armer l'ISR sur le bon front. Une ISR armée sur le front que la dalle ne produit jamais = tactile muet EN SILENCE |
| Fréquence I²C du device | **400 kHz** | 0 erreur sur 4 978 lectures |

⛔ **On LIT la config du GT911, on ne l'écrit jamais.** Sa NVM a un nombre
d'écritures limité, et une config ratée transforme la dalle tactile en
presse-papier.

### 11.2 L'orientation — tranchée par les 4 coins + le centre

Constat owner, `touch trace`, coordonnées **brutes** (avant toute transformation) :

| Point visé | Rapporté | Attendu |
|---|---|---|
| coin haut-gauche | (24, 5) | (0, 0) |
| coin haut-droit | (443, 34) | (479, 0) |
| coin bas-gauche | (91, 628) | (0, 639) |
| coin bas-droit | (456, 619) | (479, 639) |
| **centre** | **(237, 322)** | (240, 320) |

⇒ **Aucune transformation n'est nécessaire.** `swap_xy = 0`, `mirror_x = 0`,
`mirror_y = 0`, `x_max = 480`, `y_max = 640` : le repère du GT911 **est** celui de
la dalle. Deux sources indépendantes concordent — la résolution qu'il déclare
(§11.1) et ce que le doigt produit.

⚠️ `x_max`/`y_max` ne sont **pas** une mise à l'échelle : `esp_lcd_touch` s'en sert
comme **axe de symétrie** des miroirs (`x = x_max - x`). Les quatre champs se
règlent ensemble ou pas du tout.

### 11.3 IRQ ou polling — et pourquoi la question a changé de nature

L'arbitrage attendu portait sur le coût. Il a été mesuré, au repos sur le dashboard :

| Mode | `taskLVGL` | Charge totale | Lectures I²C / 30 s | IRQ / 30 s |
|---|---|---|---|---|
| `poll` (`LV_INDEV_MODE_TIMER`, ~33 ms) | 0,5 % | **0,8 %** | 857 | 0 |
| `event` (`LV_INDEV_MODE_EVENT`, sur INT) | 0,2 % | **0,5 %** | 0 | 0 |

**L'INT ne bat pas spontanément** (0 IRQ en 30 s sans toucher), donc `event` ne
coûte rien au repos. Pendant un contact il pulse fort : **999 IRQ pour 22 appuis**.

> 🔴 **MAIS LE VRAI ARBITRE A ÉTÉ AILLEURS.** Avant le bounce buffer (§11.4), le
> mode de lecture décidait de la **lisibilité de l'écran**, pas de 0,3 point de
> CPU : en `poll`, l'image défilait en permanence ; en `event`, seulement pendant
> le contact du doigt. C'est ce contraste — un défaut qu'on allume et qu'on éteint
> avec une commande — qui a rendu la cause attaquable.
>
> **Depuis le bounce buffer, les deux modes sont visuellement propres.** Le choix
> redevient un choix de coût, et le témoin actif reste obligatoire avant de
> retenir `event` : `touch reset`, toucher, puis lire le compteur d'IRQ. Un
> compteur à zéro après un vrai toucher condamne ce mode, quoi qu'affiche l'écran.

#### ✅ VERDICT — `poll` est la configuration de référence (arrêté le 2026-08-16)

Cette section s'est longtemps arrêtée sur « le choix redevient un choix de coût »,
c'est-à-dire **sans verdict** — alors que l'AC2 exige que le mode écarté le soit
avec son **symptôme exact**. Le symptôme manquait à la campagne. Il est venu de la
**revue de code**, et il ne porte pas sur le coût mais sur la robustesse. Trois
défauts, tous propres au mode `event` :

1. **`ui off` NE COUPE PAS le tactile en `event`.** `lvgl_port_stop()` ne fait que
   `lv_timer_enable(false)` + arrêter le tick : la tâche LVGL continue de tourner
   et lit l'indev sur la branche **événementielle**, avant et indépendamment de
   `lv_timer_handler()`. Conséquence directe et mesurable : des transactions I²C
   ont lieu **pendant** `ui off` — le stimulus exact de la famine DMA de §11.4 —
   au milieu d'une mesure `scene`/`tear` que la pause existe pour isoler. Et un
   tap y produit un vrai `LV_EVENT_CLICKED`.
2. **L'appui « collé ».** En `event` l'indev n'est relu que sur front : un front de
   relâchement manqué (après `touch addr`, qui retire l'ISR) laissait LVGL
   `PRESSED` indéfiniment, et le tap suivant partait sur la case d'origine. Le
   mode `poll` n'a pas ce trou. *(Corrigé depuis — `lv_indev_reset()` dans le
   drain — mais c'est une garde qu'il a fallu ajouter, pas une propriété du
   mode.)*
3. **Une fenêtre au boot** entre `lvgl_port_add_touch()` et le remplacement du
   `read_cb`, où toucher la dalle partait en `abort()`. *(Corrigée : le verrou
   LVGL est désormais pris avant la création de l'indev.)*

Le point 1 est **structurel au portage** : on ne peut pas le corriger sans
réécrire `esp_lvgl_port`. C'est lui qui tranche.

⇒ **`poll` est retenu**, à +0,3 point de CPU assumé et écrit. `touch mode event`
reste disponible pour l'A/B à chaud. La ligne « mode de lecture tactile » entre
dans la configuration de référence §0, où elle manquait.

⚠️ **Ce verdict est une décision de revue, pas une mesure nouvelle** : les chiffres
de coût ci-dessus n'ont pas bougé, et ils donnent `event` gagnant. C'est
l'arbitrage qui change de critère, et le dire est la moitié du travail.

### 11.4 🔴 LE DÉFAUT CENTRAL — l'I²C fait défiler l'image, et le bounce buffer y met fin

**Symptôme, constat owner :** *« l'affichage est archibugué, ça clignote à fond,
défilement ultra rapide, illisible »*.

**Corrélation exacte avec l'activité I²C** — c'est ce qui désigne le coupable :

| Régime | Trafic I²C | Écran |
|---|---|---|
| `poll` | ~30 transactions/s en continu | défile **en permanence** |
| `event`, au repos | aucune | **stable** |
| `event`, pendant le contact | rafale (~45 IRQ/appui) | défile **pendant le contact**, s'arrête au relâchement |

**Ce que les instruments ont éliminé avant toute hypothèse :**

- **`fps` = 37,40 Hz (−0,00 %)** → le pipeline garde sa cadence : ce n'est pas une
  perte de trames.
- **0 flush, 0 cycle en 10 s** et **`taskLVGL` à 0,5 %** → LVGL ne redessine rien.
  Ce n'est donc **pas** un redessin en boucle. *(Deux instruments indépendants.)*
- **`ui off` fige l'image ; `ui on` la fait redéfiler** → c'est bien lié à
  l'activité de la tâche LVGL, pas à la dalle.
- **GPIO15/GPIO7 ne sont dans aucune ligne RGB** (§1.1) → pas de partage de broche.
- 🔑 **La bande du haut reste STABLE pendant que le bas défile** → **décrochage
  global DISQUALIFIÉ**. La DMA repart bien juste à chaque VBlank
  (`RESTART_IN_VSYNC=y`) ; elle prend du retard **en cours de trame**.

**Mécanisme retenu :** sur ESP32-S3, **la flash et la PSRAM partagent le
contrôleur SPI0**. La DMA du panneau lit le framebuffer PSRAM à 23,0 Mo/s en
continu ; du code exécuté depuis la flash (le driver I²C) provoque des défauts de
cache qui lui volent ce bus, et elle est **affamée**. Les lignes peintes après la
perturbation sont décalées — d'où un « défilement » alors que rien n'a bougé dans
le framebuffer.

**La parade, et sa condition** (matrice complète en §5.3) :

| `bounce_px` | `LCD_RGB_ISR_IRAM_SAFE` | Résultat sous I²C |
|---|---|---|
| 0 | `y` *(état livré par dn1-3)* | défile |
| 0 | `n` *(la branche jamais jouée)* | **défile pareil — effet propre NUL** |
| 4 800 | `y` | **panique au boot** : `Cache disabled but cached memory region accessed` |
| **4 800** | **`n`** | ✅ **STABLE**, fps 37,40 Hz (+0,01 %) |

⇒ **Le bounce buffer est RÉHABILITÉ** (il était « DISQUALIFIÉ (watchdog) » depuis
dn1-2), et `ISR_IRAM_SAFE=n` n'est gardé **que** comme sa condition — son effet
propre est nul. Les deux options étaient **nouées** ; c'est très probablement ce
qui avait produit le watchdog de dn1-2, dont la seule branche bounce+`n` portait
19 200 px et non 4 800.

**Le même correctif solde l'artefact §10.5.** Les deux symptômes n'en faisaient
qu'un.

⚠️ **PORTÉE — ce défaut dépassait largement dn1-4.** **dn2-1** (BME680, BH1750,
VL53L0X, INA219 sur ce même bus) aurait fait défiler l'écran en permanence, et
aurait cherché la panne du côté des capteurs. Il est débloqué par ricochet.

⚠️ **CE QUE CETTE MESURE NE COUVRE PAS** : le stimulus est de l'**I²C**, qui
*occupe* le bus. Celui de la §5.3 est une **écriture flash**, qui *coupe le cache*.
Rien ne dit que le bounce protège du second. **D4 reste en vigueur.**

### 11.5 Latence tap → écran, et le budget < 300 ms du brief

Instrument : du clic LVGL (émis au **relâchement**) à la fin du **dernier flush**
du cycle. 20 allers-retours scriptés (`nav ab 20`), 40 transitions par ligne.

| `bounce_px` | `draw_lines` | min | moy | max | Verdict vs 300 ms |
|---|---|---|---|---|---|
| 0 | 64 | 267,1 | **267,9** | 293,9 | tient — mais **écran inutilisable** |
| 0 | 128 | 187,0 | 234,9 | 257,7 | tient — écran inutilisable |
| 4 800 | 64 | 397,1 | **427,7** | 480,6 | **dépassé** |
| **4 800** | **128** | 287,7 | **307,1** | 320,7 | **frôlé, non tenu** |
| 4 800 | 160 | 293,8 | 307,7 | 320,8 | idem — **le levier sature** |

**Au doigt** (14 transitions réelles, `bounce 4800`, `lines 64`) : min 391,8 ms ·
moy **434,7 ms** · max 480,2 ms — cohérent avec les 427,7 ms de la console. Le
doigt n'ajoute donc rien de mesurable au chronomètre : ce qu'on mesure est bien la
transition, pas le geste.

> ### Le verdict, écrit tel quel
> **Le budget < 300 ms du brief n'est PAS tenu** dans la configuration qui rend
> l'écran utilisable : **307,1 ms de moyenne** au mieux, avec un pire cas à
> 320,7 ms. Le bounce buffer coûte **+160 ms** ; repasser le draw buffer à
> 128 lignes en récupère **120**, et pousser à 160 lignes ne donne **plus rien** —
> le plancher n'est alors plus la synchro mais le **rendu** lui-même.
>
> Rappel : le critère brief n°3 est **composite** et se solde en **dn4-1**. Ce qui
> est mesuré ici l'est sur un détail **factice**, dont le rendu n'est pas celui du
> produit.

**Pourquoi 267 ms au plancher, à 64 lignes** — mesuré sur une transition isolée :

```
aire cumulée : 614400 px  => 307200 px et 10.0 flush(es) par CYCLE de redessin
copie              : 2321 us/flush en moyenne  (23,2 ms par cycle)
attente de synchro : 9661 us/flush en moyenne  (96,6 ms par cycle)
```

Un changement d'écran redessine tout : **10 flushes, chacun attendant sa trame**,
soit 10 × 26,7 ms = **267 ms**. ⚠️ Cela **corrige** la prévision de §10.3
(« ~176 ms d'attente ») : ce chiffre supposait un rendu négligeable. Avec sept
conteneurs translucides sur une image de fond, il ne l'est pas — mais le total par
cycle reste gouverné par le nombre de trames.

#### ✅ L'ARBITRAGE DU MODÈLE, REFAIT DANS LA CONFIG LIVRÉE — session carte du 2026-08-16

Les chiffres qui avaient choisi `screens` (267,9 ms contre 307,7) étaient invalides
deux fois : relevés à `bounce_px = 0` (« écran inutilisable »), et sur un A/B dont
la bascule **fuyait un arbre d'écran complet**. Rejoué sur le firmware `0e7fe61`,
dans la configuration de référence (`num_fbs=1 · bounce_px=4800 · draw_lines=128 ·
draw_psram=0 · lvgl_core=0`, lecture tactile `poll`), `touch reset` avant chaque
série, dalle non touchée (la console le vérifie et le dirait) :

| Modèle | min | moy | max | n | tas LVGL utilisé | delta tas |
|---|---|---|---|---|---|---|
| **`screens`** | 285,0 ms | **307,0 ms** | 320,8 ms | 40/40 | **15 216 o** | −12 o |
| `rebuild` | 300,8 ms | **346,9 ms** | 374,2 ms | 40/40 | 12 184 o | 0 o |

⇒ **`screens` est CONFIRMÉ**, et il l'est mieux qu'avant : il gagne **39,9 ms
(11,5 %)** pour **+3 032 o** de tas LVGL.

Trois choses que ce rejeu apprend, et qu'on ne pouvait pas savoir avant :

1. **Le prix de `screens` avait été SURESTIMÉ de 2,7×.** L'ancien relevé donnait
   +8 048 o (20 064 contre 12 016) ; la mesure propre donne **+3 032 o**. L'écart
   est exactement ce qu'on attend d'un tas pollué par les écrans orphelins que la
   bascule abandonnait.
2. **L'écart entre les deux modèles est STABLE**, lui : 39,8 ms à `bounce 0 /
   lines 64`, 39,9 ms à `bounce 4800 / lines 128`. Le coût du modèle ne dépend
   donc pas de la configuration du pipeline — c'est un coût de **construction
   d'arbre**, pas de flush. Le reste (les ~40 ms de décalage absolu entre les deux
   campagnes) appartient au bounce et au draw buffer.
3. **`n = 40` pour 40 transitions réelles, zéro rejet**, dans les deux séries. Le
   dénominateur de la moyenne est enfin prouvé, pas supposé.

**La fuite est morte, et c'est mesuré séparément** — 5 bascules `screens` ⇄
`rebuild` enchaînées, tas relevé à chaque étape :

| Bascule | 1 `screens` | 2 `rebuild` | 3 `screens` | 4 `rebuild` | 5 `screens` |
|---|---|---|---|---|---|
| Tas utilisé | 15 204 o | 12 168 o | 15 180 o | 12 180 o | **15 208 o** |

Plat à ±28 o de bruit près. Avant le correctif, les trois retours vers `screens`
auraient abandonné ~36 Ko sur un pool qui n'a que 47 Ko de libres — `lv_malloc`
aurait échoué pendant la campagne. ⚠️ La **fragmentation** monte en revanche de
1 % à 15-19 % et le plus gros bloc libre descend de 47 060 à ~40 600 o : c'est du
churn create/destroy, pas une fuite (le total utilisé ne bouge pas), mais dn3-2 en
tiendra compte s'il alloue de gros blocs après des bascules.

**Options NOTÉES, non appliquées** (AC5 demande de les noter, pas de les traiter) :

1. **Cases opaques** (`LV_OPA_COVER`) : supprimerait le re-blit du fond sous chaque
   case. Gratuit en mémoire, coûteux en esthétique — le Living PCB ne
   transparaîtrait plus dans les cases. **dn3-1 tranchera.**
2. **Ne pas invalider le fond à la transition** : `lv_screen_load` invalide tout,
   alors que le fond est identique d'un écran à l'autre. C'est la piste de fond
   pour dn3-2.
3. **Bounce plus grand** (9 600 / 19 200 px) : moins d'interruptions de
   remplissage, donc peut-être moins de surcoût CPU. Non essayé.
4. Baisser le PCLK : donnerait de la marge à la DMA, au prix du fps.

### 11.6 Les zones tactiles — géométrie PROVISOIRE

⚠️ **Aucune dimension n'est spécifiée par la planification** (seulement 480 × 640
portrait). Tout ce qui suit est **dérivé** pour que dn1-4 ait des zones à
éprouver. **dn3-2 fera foi.**

| Élément | Géométrie | Tactile |
|---|---|---|
| Barre heure/date | 480 × 70, en (0, 0) | **non** — zone morte |
| Grille 2 × 3 | cases **225 × 156**, marge 10, gouttière 10, à partir de y = 80 | **oui, la case ENTIÈRE** |
| Bandeau MENU | 480 × 60, en (0, 580) | **oui** — no-op consigné |
| Retour `←` (détail) | **120 × 60** en (10, 10) | **oui** — 24 fois l'aire du chevron |

**Les deux drapeaux qui font que « toute la case » est vrai** :
`LV_OBJ_FLAG_CLICKABLE` sur le **conteneur** (les labels enfants restent non
cliquables, donc LVGL remonte au parent), et surtout **`LV_OBJ_FLAG_SCROLLABLE`
RETIRÉ** — `lv_obj_create()` le pose par défaut, et un conteneur scrollable
**avale le geste** dès que le doigt roule de quelques pixels. C'est exactement le
défaut « ça marche au centre, pas au bord » que la preuve aux coins doit attraper.

> ## 🔴 §10.4 SOUS NAVIGATION — LE CONSTAT MANQUANT, FAIT LE 2026-08-16
>
> **La phrase « ⚠️ Aucun élément pleine hauteur, conformément au verdict adverse de
> §10.4 » était fausse, et elle masquait un trou de preuve.** Deux faits :
>
> - le **voile** décrit plus bas fait `480 × 640` (`dn_ui.c`, `fond_poser()`) : il
>   est plein écran. Statique, donc jamais invalidé seul — ce qui atténue le cas,
>   mais ne rend pas la phrase vraie ;
> - surtout, **chaque transition dashboard↔détail salit l'écran ENTIER**. C'est
>   littéralement la *zone sale pleine hauteur* que §10.4 déclare **non protégée**
>   par `vsync`. La précaution prise sur la géométrie des cases (2×3, ~½ largeur ×
>   ~⅓ hauteur) est donc contournée par le régime de navigation lui-même.
>
> ### Ce que l'œil a vu — constat owner, 40 transitions consécutives (`nav ab 20`)
>
> > *« oui mais léger »* (déchirement) — *« à chaque transition le détail
> > s'affiche par morceau, mais rapide, en 1 s »* — *« sinon tout paraît ok »*.
>
> ⇒ **Le verdict adverse de §10.4 s'applique bien en régime de navigation**, mais
> sa manifestation N'EST PAS le déchirement classique : c'est un **repeint bande
> par bande**, visible à chaque transition, sans exception.
>
> ### Le mécanisme, mesuré sur une transition isolée (`flush`)
>
> ```
> flushes            : 5
> cycles de redessin : 1
> aire cumulée       : 307200 px
>   => 61440 px par flush en moyenne        (480 x 128 = UNE bande)
>   => 307200 px et 5.0 flush(es) par CYCLE de redessin
> copie              : 26181 us cumulés, 5236 us/flush
> attente de synchro : 49997 us cumulés, 9999 us/flush
> ```
>
> **640 ÷ 128 = 5 bandes**, chacune attendant sa propre trame. `vsync` synchronise
> chaque bande *individuellement* — rien ne synchronise le **cycle entier**. C'est
> la définition exacte du cas adverse, et l'œil de l'owner et le compteur disent la
> même chose.
>
> ⚠️ **Copie 26,2 ms + synchro 50,0 ms = 76 ms, pour une transition mesurée à
> 307 ms.** Les ~230 ms restants sont le **rendu LVGL** lui-même. Le plancher de la
> transition n'est donc PAS la copie ni l'attente de trame : c'est le dessin. Cela
> corrige une lecture répandue dans ce fichier depuis §10.3.
>
> ### Ce que dn3-2 doit en faire
>
> Le nombre de bandes visibles vaut `640 / draw_lines` : **5 aujourd'hui**, 10 si
> quelqu'un repasse à 64 lignes « pour économiser la RAM ». Et six widgets VIVANTS
> allongeront le rendu, donc le temps pendant lequel les bandes sont
> discernables — le défaut empire avec le contenu, pas avec la mémoire. Les
> parades sont notées en §11.5 (cases opaques, ne pas invalider le fond) ; aucune
> n'est appliquée ici, et l'owner a jugé le rendu acceptable en l'état.
>
> ✅ **Le legs §10.4 est SOLDÉ sous le régime réel** : il n'est plus une garde
> théorique sur la géométrie des widgets, c'est un comportement observé, chiffré,
> et dont le levier est connu.


**Lisibilité — constat owner du 2026-08-16** : *« le fond prend trop, il masque les
détails (des cadres aussi) »*. Le Living PCB est une photo très contrastée. Deux
correctifs, sans flou (LVGL n'en a pas de gratuit, et il faudrait le recalculer à
chaque zone invalidée sur un budget déjà tendu) :
- un **voile** noir à 50 % sur toute la surface, au-dessus de l'image ;
- les conteneurs passés de **40 % à 70 %** d'opacité.

Puis, le détail restant illisible : ses labels étaient posés **à même le fond**,
contrairement aux cases du dashboard. Les quatre blocs du template ont reçu leur
propre aplat. Verdict owner : *« oui c'est nickel comme ça »*.

⚠️ **LES LIBELLÉS SONT SANS ACCENT, ET C'EST UNE CONTRAINTE D'OUTILLAGE.** Les
polices Montserrat embarquées sont générées avec `-r 0x20-0x7F,0xB0,0x2022`
(première ligne de `lv_font_montserrat_14.c`) : ASCII imprimable, signe **degré**,
puce — et **rien d'autre**. « RÉSEAU » ou « AOÛT » y perdraient leur lettre
accentuée **en silence**, LVGL ne dessinant pas le glyphe absent sans se plaindre.
🔴 **Legs pour dn3-1** : du français accentué exigera une police générée
(`lv_font_conv`), donc du binaire à budgéter. Le « °C » passe, lui.

### 11.7 Les budgets avec tactile + navigation — la référence que dn3 dépensera

Configuration : `num_fbs=1 · bounce_px=4800 · draw_lines=128 · draw_psram=0 ·
lvgl_core=0`, lecture tactile `poll`, dashboard affiché, label masqué.
**Colonne dn1-4 re-mesurée le 2026-08-16 sur le firmware `0e7fe61`** (post-revue de
code), sauf les lignes marquées comme antérieures.

| Mesure | dn1-3 (référence) | **dn1-4** | Écart |
|---|---|---|---|
| Charge CPU, socle nu | 0,0 % | — | — |
| Charge CPU, **LVGL au repos** | 0,3 % | **0,9 %** | +0,6 pt, dont **+0,3 pt de polling I²C**. ⚠️ 0,8 % avant la revue de code, 0,9 % après (`0e7fe61`) : +0,1 pt, dans le bruit de la mesure |
| Charge CPU, **label 1 Hz** | 0,9 % | **2,0 %** | +1,1 pt — le surcoût du bounce, qui n'apparaît **qu'en redessin** |
| `fps` | 37,40 Hz | **37,40 Hz (−0,00 %)** | **inchangé** — re-vérifié sur `0e7fe61` : 561 trames en 14 999 789 µs |
| PSRAM libre | 7 770 588 o | **7 768 608 o** | −1 980 o |
| RAM interne libre | 212 015 o | **117 995 o** | −94 020 o : draw buffer 128 lignes (+61 440) et bounce (2 × 9 600). 118 379 o avant la revue de code, 117 995 o après — les correctifs coûtent 384 o |
| Binaire | 740 400 o | **790 736 o** | +50 336 o (driver GT911 + tactile + navigation + les correctifs de revue) ; **81 % de la partition libre**. ⚠️ 782 800 o était la taille AVANT la revue de code du 2026-08-16 ; les 34 correctifs coûtent +7 936 o. **C'est ce binaire-là (`0e7fe61`) qui porte TOUTES les mesures de cette section.** Le commit suivant, qui ne fait qu'inscrire les résultats de la session dans les commentaires et un message de console, retombe à 790 720 o — non re-mesuré, et sans raison de l'être |

> ⚠️ **CORRECTION D'ATTRIBUTION, faite en cours de mesure.** Un premier relevé
> annonçait « CPU 0,8 % → 2,7 % » et mettait tout sur le dos du bounce buffer. Il
> avait été pris **avec le label 1 Hz allumé** — deux variables à la fois. L'A/B
> propre dit autre chose, et c'est plus intéressant : **au repos le bounce ne coûte
> rien de mesurable** (0,8 % avant comme après), son surcoût n'existe **qu'en
> redessin**. Son vrai prix n'est pas le CPU, c'est la **latence**.

**Coût d'une transition** (`flush`, 128 lignes) : 5 flushes par cycle, un plein
écran de 307 200 px. Le détail des 267 ms de plancher à 64 lignes est en §11.5.

**Ce qu'il reste pour dn3** : 118 379 o de RAM interne, 7 768 608 o de PSRAM,
42 Ko sur les 64 Ko du tas LVGL (33 % utilisés avec les deux écrans du modèle
`screens`), et 81 % de la partition applicative.

> ✅ **LE TAS LVGL A ÉTÉ REJOUÉ — session carte du 2026-08-16, firmware `0e7fe61`.**
> Le chiffre ci-dessus (33 % / 20 064 o) venait d'une campagne doublement viciée :
> l'A/B **fuyait un arbre d'écran par bascule**, et l'instrument de non-fuite était
> **aveugle** (il mesurait la RAM interne et la PSRAM, alors que le tas LVGL est un
> pool statique en `.bss`, `LV_MEM_ADR=0`). Les deux sont corrigés, et la mesure
> propre donne **15 216 o (25 %) en `screens`** contre 12 184 o en `rebuild` — soit
> **+3 032 o** pour le modèle retenu, et non +8 048 o. Le prix de `screens` avait
> donc été **surestimé de 2,7×** par la fuite. Détail complet et preuve de
> non-fuite (5 bascules enchaînées) en **§11.5**. `screens` n'est plus provisoire :
> il est confirmé, et il gagne 39,9 ms (11,5 %).

---

## 12. La liaison PC — voir le fichier frère (dn2-2, 2026-08-16)

**`ESP32-S3-Touch-LCD-2.8B-liaison-pc.md`** consigne la fourche transport et son
verdict : **USB série (branche A), par la console REPL** — la branche B (WiFi
WebSocket) est éliminée par BLOCAGE MESURÉ du verrou RAM interne (6 407 o restants
connectée + serveur WS ; `ESP_ERR_NO_MEM` en variante SPIRAM).

> 🔴 **CE QUE dn2-2 A CHANGÉ DANS LA §0, ET IL FAUT LE DIRE ICI** (correctif de la revue
> de code du 2026-08-16). Cette ligne affirmait « *La §0 ci-dessus est INCHANGÉE par
> dn2-2* » — **c'était faux**, et le Debug Log T5 de la story répétait l'affirmation
> pendant que son BONUS disait le contraire. dn2-2 a bel et bien ajouté à la §0 l'encart
> « **JOUÉE LE 2026-08-16, ET LA RÉPONSE EST NON** » : le bounce buffer **ne protège pas**
> des écritures flash. Ce qui est **inchangé**, c'est la **configuration** de référence
> elle-même (paramètres d'affichage et `sdkconfig` : la branche transport retenue n'y
> touche pas) — pas le texte de la §0, dont la conclusion ouverte a été **fermée par la
> mesure**. ⚠️ C'est la **troisième** story de suite qui produit un écart à cet endroit
> précis ; l'AC9 le nomme (« vérifier ligne à ligne, pas au jugé »), et c'est encore la
> revue qui l'a relevé.
Y sont aussi : le protocole de trame v1, les budgets liaison + donnée live
(RAM interne **113 247 o**, CPU 0,8 %, fps 37,40 inchangé), et le legs dn2-1.

---

## 13. Les capteurs sur le bus I²C externe — voir le fichier frère (dn2-1, 2026-08-17)

**`ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md`** consigne le branchement du premier
composant EXTERNE sur ce bus.

✅ **LE BME680 EST VIVANT, ET C'EST UN VRAI BME680** — barrette **soudée** le
2026-08-17, adresse **`0x77` mesurée** (le breakout tire SDO haut), chip id
`0xD0 = 0x61`, variant `0xF0 = 0x00` (BME680, pas BME688). **Température et
humidité vivent dans les cases 4 et 5 du dashboard**, à 5 s, cadence arbitrée.

> ⚠️ **CETTE SECTION A ÉTÉ PÉRIMÉE PENDANT UN COMMIT, ET C'EST CONSIGNÉ PARCE QUE
> C'EST LE DÉFAUT LE PLUS CHER DE CE DÉPÔT.** Elle a été livrée par `b554a4e` en
> annonçant encore « séance en cours : le BME680 n'a pas encore répondu » et « cette
> mesure-là n'a pas encore eu lieu » — alors que le même commit livrait le capteur
> vivant, la soudure faite et la §11.4 constatée à l'œil en régime. Le **fichier
> d'autorité enseignait l'inverse de ce que la story avait mesuré** : la session
> suivante aurait rejoué un arbre de diagnostic déjà soldé. Trouvé par la revue de
> code du 2026-08-17, deux couches sur trois. ⇒ **Une section de renvoi se relit à
> la clôture, pas à l'ouverture de la séance.**

🔴 **DEUX CHOSES Y CORRIGENT CE QU'ON CROYAIT, ET ELLES REMONTENT ICI :**

1. **Le brochage du connecteur I²C externe est `GND · 3V3 · SDA · SCL`** — le miroir
   Spotpear du wiki Waveshare annonçait `GND · 3V3 · **SCL · SDA**`, soit **les deux
   dernières broches permutées**, sur un « header 2,54 mm » qui est en réalité une
   **embase JST**. Deuxième fois qu'une source externe se fait corriger sur cette
   carte, après l'ordre des bits RGB de la §1.1. ⚠️ Une **seconde embase JST
   identique et adjacente** porte l'UART (`GND · 3V3 · TXD · RXD`) : se tromper
   d'embase alimente correctement le composant et le laisse muet.
2. **Deux occupants du bus passent de « déclarés » à MESURÉS** — la **RTC PCF85063
   répond à `0x51`** (première confirmation qu'elle est vivante, utile à dn3-2 pour
   la barre heure/date sans réseau) et **l'IMU QMI8658 est à `0x6B`**, pas `0x6A`
   comme `dn_pins.h` le laissait ouvert. La §1.2 reste exacte, elle gagne deux
   certitudes.

🔴 **LA §11.4 EST SOLDÉE SOUS TRAFIC CAPTEUR RÉEL — c'était le risque n°1 de dn2-1.**
Chaque lecture du BME680 est une **rafale I²C**, exactement le stimulus qui faisait
défiler l'image avant le bounce buffer de dn1-4. **Constat owner à l'œil, en régime
de lecture : IMAGE STABLE**, plus 0 erreur I²C sur le GT911 et un aller-retour au
doigt pendant que la tâche tourne. ⇒ **le bounce buffer encaisse des rafales
périodiques réelles**, ce qui n'était prouvé jusque-là que contre le polling
tactile. ⚠️ Constaté **à l'œil**, comme il se doit : le `fps` est aveugle à ce
défaut (37,33 avant / 37,45 pendant que l'image défilait). ⛔ **`bounce_px = 0`
reste interdit.**

⚠️ **Ce que la §13 N'AUTORISE toujours PAS à conclure** : la commande `i2c` qu'elle
livre dure ~26 ms **quand tout acquitte** — trop bref pour être un test de la
§11.4, et ce n'est pas par elle que la stabilité a été établie. ⚠️ Son pire cas
mesuré au calcul est de **~9 s** (112 sondages à 50 ms + confirmations) ; un budget
d'abandon a été posé par la revue du 2026-08-17, et le scan **dit** quand il tronque.

**La §0 est INCHANGÉE par dn2-1** — vérifié ligne à ligne, pas au jugé, et
re-vérifié à la clôture : `num_fbs=1 bounce_px=4800 draw_lines=128 draw_psram=0
lvgl_core=0` relus au bandeau après le flash final.

⚠️ **Les budgets publiés en §13.8 du fichier frère sont à RE-RELEVER** : la revue de
code du 2026-08-17 a modifié 5 fichiers du firmware (binaire 827 632 → **832 720 o**
au build de revue). Les chiffres de RAM, de CPU et de flush attendent la séance
carte de validation des correctifs.

---

## 14. Les sources externes — ce qu'elles valent, et les QUATRE contradictions mesurées

**Relevé le 2026-08-17**, après que la revue de code de dn2-1 eut demandé d'où venaient les
brochages. Cette section existe pour une raison précise : **le dépôt a corrigé des sources
tierces trois fois, et on croyait que le fautif était un revendeur négligent. C'est faux — la
doc DU FABRICANT porte la même erreur.**

### 14.1 Les trois sources, et leur statut

| Source | Statut | Ce qu'on en a tiré |
|---|---|---|
| `waveshare.com/wiki/ESP32-S3-Touch-LCD-2.8B` | **officielle** — ⚠️ **répond HTTP 403** à toute récupération automatisée | rien : illisible autrement qu'à la main |
| `docs.waveshare.com/ESP32-S3-Touch-LCD-2.8B` | **officielle**, lisible | la §14.2 et la §14.3 ci-dessous |
| `spotpear.com/wiki/ESP32-S3R8-2.8-inch-…` | **miroir tiers** (revendeur) | c'est elle qui avait servi en dn2-1 |

⚠️ **Ces pages ont été lues par un résumé automatique, pas dans leur HTML brut.** Tout ce qui
suit est donc **HYPOTHÈSE**, au même statut que Spotpear l'était — et la §14.2 montre pourquoi
ce statut est mérité même pour une source officielle.

### 14.2 🔴 LES QUATRE CONTRADICTIONS — et la première disculpe Spotpear

**1. L'ordre `SDA`/`SCL` : la doc OFFICIELLE se contredit ELLE-MÊME, sur la même page.**

| Table de `docs.waveshare.com` | Ordre annoncé |
|---|---|
| Header 12×2 **gauche** | `GND · 3V3 · **SDA (GPIO15)** · **SCL (GPIO7)**` |
| Section « **I2C Interface** » | `GND · 3V3 · **SCL** · **SDA**` |

⇒ **Spotpear n'a rien inventé : il a recopié fidèlement celle des deux qui se trompe.**
✅ **C'est la table du header 12×2 qui concorde avec la MESURE** (sérigraphie de la carte, plus
la photo `docs/cablage/2026-08-16_2228-…`). La §13.1 tient, et son verdict s'élargit : *la
divergence n'est pas entre un miroir et le fabricant, elle est DANS le fabricant.*

**2. « Header 2,54 mm » contre « embase JST » — les deux ont raison, et c'est la clé.**
La doc décrit les broches I²C **du header 2×12**, qui les porte effectivement (`SCL SDA 3V3 G`,
visible sur la photo). L'**embase JST 4 points** est un SECOND accès au même bus, que la doc ne
mentionne pas. ⇒ **Deux accès physiques, un seul bus.** Spotpear avait fusionné les deux en un
« header 2,54 mm » qui n'existe pas sous cette forme.

**3. `CH343P` — réfuté par la mesure de dn1-1.** Spotpear annonce une puce USB-UART ; dn1-1 a
mesuré l'**USB natif `303a:1001`**, aucun périphérique `1A86`. La doc officielle, elle, dit
seulement « USB Type-C » sans nommer de puce. ⇒ **Spotpear mélange les variantes 2.8 et 2.8B.**

**4. `GPIO16` annoncé libre — réfuté par dn1-4.** La doc le liste parmi les broches sorties du
header gauche. dn1-4 a établi **PAR CAUSALITÉ** que c'est `TP_INT` du GT911 (INT haut ⇒ 0x14,
bas ⇒ 0x5D). Entrée ⚪ déjà ouverte au ledger sur ce conflit.

> 🔴 **CE QUE ÇA CHANGE À LA RÈGLE DU DÉPÔT.** *« On ne va plus chercher un brochage ailleurs »*
> ne visait qu'un revendeur. Elle vaut désormais **contre la documentation du constructeur** :
> sur quatre points vérifiables, elle s'est trompée ou contredite **quatre fois**. La sérigraphie
> et la mesure font foi, sans exception et sans exception à venir.

### 14.3 Ce que ces pages apprennent QUAND MÊME — et qui n'est mesuré nulle part

⚠️ **Tout ce tableau est HYPOTHÈSE.** Rien n'entre dans `dn_pins.h` avant d'être mesuré.

| Fait annoncé | Pourquoi ça compte | Statut |
|---|---|---|
| 🔴 **`GPIO37, 36, 35, 34, 33` sortis sur le header 2×12 DROIT mais « déconseillés — PSRAM interne »** | **Piège pour dn4-1** : y câbler un capteur casse la PSRAM, donc **le framebuffer**. Un header qui expose des broches inutilisables est exactement le genre de chose qui coûte une soirée | ⚠️ à vérifier avant tout câblage |
| **`GPIO4` = lecture de la tension batterie**, « isolable en dessoudant la résistance » | seule broche analogique documentée ; ⚠️ **aucun rapport de pont diviseur donné** ⇒ à mesurer, jamais à supposer | ⚠️ hypothèse |
| **Connecteur `MX1.25 2PIN` pour LiPo 3,7 V** + chargeur **`MP1605GTF-Z` (2 A max)** | voir la décision **D5** ci-dessous | ⚠️ hypothèse |
| **L'interrupteur ON/OFF est un « Battery Power Control Switch »** | 🔴 **Il n'avait jamais été identifié**, alors qu'il est visible sur `docs/cablage/2026-08-16_2228-…`. Sa portée sur l'alimentation USB **n'est pas documentée** ⇒ une carte qui ne démarre pas après qu'on l'a bougé est un diagnostic à connaître AVANT de dérouler la recette « carte muette » | ⚠️ **à établir par la mesure**, et c'est le plus actionnable des cinq |
| **`TCA9554PWR` : « toutes les broches utilisées, non sorties »** | confirme §1.2 : l'expander est entièrement consommé, rien à en tirer pour dn4-1 | ✅ cohérent avec la mesure |

**Absent des deux pages officielles**, et que ce dépôt possède **par la mesure** : les timings RGB
(pclk, porches), le contrôleur d'écran, la broche du rétroéclairage, les broches TF, **toutes les
adresses I²C**, et la moindre consommation. ⇒ *Sur cette carte, `hardware/` en sait davantage que
son constructeur.*

### 14.4 🔴 D5 — DÉCISION OWNER DU 2026-08-17 : PAS DE BATTERIE DANS CE PROJET

La carte **peut** recevoir un LiPo 3,7 V (connecteur et chargeur présents, §14.3). **L'owner a
décidé de ne pas en mettre.**

⇒ **Ce que ça ferme** : la piste batterie comme réponse au différenciateur du brief (*« PC éteint,
la partie environnementale continue de fonctionner »*).
⇒ **Ce que ça laisse OUVERT pour dn4-1**, et qui reste donc la question entière : le module devra
tenir sur un **port USB alimenté en permanence** (réglage BIOS de la tour) ou sur une **alimentation
séparée**. C'est la formulation d'origine de la story, et elle est confirmée — pas élargie.
⚠️ **`GPIO4` et le chargeur perdent leur intérêt fonctionnel**, mais **PAS leur intérêt de
diagnostic** : l'interrupteur « Battery Power Control » reste sur la carte et peut couper quelque
chose, batterie ou non. **Le mesurer reste utile.**

---

## 15. LE MODÈLE DE WIDGET — mesuré le 2026-08-17 (dn3-1, P6)

> **Ce que cette section ferme** : le `SystemMetricWidget` du brief naît ici, avec sa variante
> multi-grandeurs (D6), sa police accentuée, ses icônes, et **les deux A/B chiffrés** que dn3-2
> dépensera. Firmware de mesure : **`969847c`** (les chiffres de départ, eux, sont attachés à
> `c30c7ad`).
>
> ⚠️ **§0 EST INCHANGÉE.** Aucune ligne de la configuration de référence n'a bougé : `num_fbs=1`,
> `bounce_px=4800`, `draw_lines=128`, `poll`, `vsync`, LVGL sur le cœur 0, fond en flash `mmap`,
> modèle `screens`. Vérifié ligne à ligne, pas au jugé — c'est le point noir récurrent de ce
> fichier, relevé par la revue **trois stories de suite**.

### 15.1 Où vit la brique, et le contrat de verrou

`main/dn_widget.c` / `.h`, module neuf. Les critères de placement ont été écrits **avant** la
décision (story dn3-1, T1). Le seul qui plaidait pour `dn_ui.c` — « pas de frontière d'exécution :
ni tâche, ni état propre, ni péremption » — est **explicitement levé** par le brief, qui exige que
ce modèle soit *généralisé d'avance*, contrairement à la règle de `dn_capteurs.h`.

🔴 **Conséquence non négociable, sinon la décision aurait empiré l'existant** : `dn_widget` possède
la **brique tactile**. Les deux drapeaux qui rendent vraie « toute la case est la zone tactile »
(prouvée à 4 px du bord en dn1-4) étaient **déjà dupliqués** entre `zone_creer()` et `panneau()` ;
un widget qui les aurait ré-implémentés en aurait fait une **troisième copie**. Ils n'ont plus
qu'**une** définition, que traversent désormais toutes les zones tactiles du firmware.

**Le verrou est INVERSÉ, et les deux motifs sont écrits dans l'en-tête** : `dn_widget_*` exige que
`lvgl_port_lock()` soit **déjà pris**.
1. Le motif de `case_vive_poser` (dn2-1) généralisé : *N* grandeurs sous **un** verrou.
2. **Neuf** : le groupage d'invalidation (§15.5) coupe `lv_display_enable_invalidation()`, écrit
   tous les enfants, la rétablit, puis invalide le conteneur. Relâcher le verrou au milieu
   laisserait un cycle LVGL passer **avec l'invalidation coupée** — c'est-à-dire un écran **figé
   sans erreur**.

**Trois choses séparées** : descripteur `const` en `.rodata` · état **persistant** en RAM ·
pointeurs LVGL. Ce qui survit au démontage n'est **jamais** un pointeur — c'est la parade au
use-after-free trouvé par la revue dn1-3. Les pointeurs sont remis à zéro aux **trois** sites, dont
`dn_ui_set_nav_model()` **qui ne le faisait pas**.

**Les trois régimes sont dans le TYPE**, et `DN_VAL_ABSENTE` vaut **0** : un état statique naît donc
*absent*, jamais *réel*. C'est la forme typée de l'initialiseur `= "--"` que dn2-1 avait perdu.

### 15.2 La mise en page, et pourquoi « côte à côte » est impossible

Case 225 × 156. Icône 28 px + titre 14 px en haut, valeurs 28 px à partir de y = 48, pas de 40 px,
jauge et données secondaires en dessous.

🔴 **« Côte à côte » a été écarté par l'arithmétique, pas par goût** : à 28 px, « 25,5 °C » mesure
~110 px et « 52,4 % » ~95 px, soit **205 px pour 201 px utiles**. Ça ne rentre pas, et une
température négative à deux chiffres (« −12,3 °C ») aggraverait. Le côte à côte n'aurait tenu qu'en
**descendant la police**, donc en rendant la case principale **moins** lisible que les autres.
« Principale + secondaire » a été écarté pour une autre raison : il **hiérarchise**, alors que
température et humidité sont deux mesures du même capteur, de même dignité.
⇒ **EMPILÉES**, validé par constat owner. Et c'est le mécanisme **générique** : *N* grandeurs =
*N* lignes. Prouvé sur une instance bi-grandeurs **qui n'est ni Ambiance ni Ventilos**
(`widget demo on`), donc la variante D6 n'est pas un cas spécial déguisé.

### 15.3 La police — ce qui a été mesuré, et ce que la story annonçait de faux

Générateur : `tools/gen_font_dn.py`. Il **lit** les 61 codepoints de symboles dans
`built_in_font_gen.py` amont (jamais recopiés : une liste recopiée dérive, et sa dérive est
**silencieuse**), ajoute les icônes, puis **relit le `.c` produit** pour vérifier que les 68
symboles+icônes et 19 témoins accentués y sont.

**Plage retenue : latin-1 complet** `0x20-0x7F,0xA0-0xFF,0x2022`, **kerning conservé**.
Motif : la partition `factory` est libre à ~80 %, donc **le levier binaire n'existe pas ici** ;
latin-1 ferme la *classe* de défaut au lieu d'un cas, et apporte `µ` et `²`.

🔴 **LA STORY SOUS-ESTIMAIT LES OCTETS DE POLICE D'UN TIERS, ET C'EST VÉRIFIABLE.** Elle annonçait
**33 252 o** pour la plage actuelle sur les deux tailles. Le **témoin** — les `.c` des built-ins
réellement embarqués — en compte **50 844 o** (158 glyphes : 13 596 à 14 px + 37 248 à 28 px).
L'instrument a été validé contre ce témoin avant d'être utilisé.

| plage (icônes comprises) | glyphes | 14 px | 28 px | total |
|---|---:|---:|---:|---:|
| built-ins réels, **sans** icônes (témoin) | 158 | 13 596 | 37 248 | **50 844** |
| actuelle + icônes, kerning | 164 | 14 294 | 39 692 | 53 986 |
| minimale FR + icônes, kerning | 179 | 15 382 | 42 753 | 58 135 |
| **latin-1 + icônes, kerning (RETENUE)** | 259 | 20 942 | 57 462 | **78 404** |
| latin-1 + icônes, **sans** kerning | 259 | 16 164 | 52 684 | 68 848 |

🔴 **ET LA STORY SE TROMPAIT AUSSI SUR LE LEVIER.** Elle affirmait que le kerning coûte *« trois
fois le prix des accents »*. **Mesuré : 1,6 fois** — kerning **6 634-9 556 o** contre accents
**4 149 o** (minimale FR) . Le kerning reste le plus gros poste unitaire, mais l'écart annoncé était
faux d'un facteur 2. **Le conserver était donc encore moins cher que prévu.**

**`--no-compress` est obligatoire** (`CONFIG_LV_USE_FONT_COMPRESSED` n'est pas activé).
**Reproductibilité** : la ligne de commande exacte est dans l'en-tête de chaque `.c` généré, en
**chemins relatifs** (une première version y gravait le `$HOME` de la machine — une recette que
personne d'autre ne peut rejouer). `npx --yes lv_font_conv@1.5.3` mesuré fonctionnel depuis ce WSL.
Licences : `managed_components/lvgl__lvgl/scripts/built_in_font/font_license/`.

⚠️ **Un piège de génération, bruyant mais évitable** : `lv_font_conv` émet un préambule qui choisit
son include sur `LV_LVGL_H_INCLUDE_SIMPLE`, macro que ce build **ne définit pas** (il pose
`LV_CONF_INCLUDE_SIMPLE`, qui est une **autre** macro, pour `lv_conf.h`). Sans réécriture :
`fatal error: lvgl/lvgl.h: No such file or directory`. Le générateur le corrige et **échoue
bruyamment** si le gabarit amont change.

**Décision W6 — VERSIONNÉ, pas généré au build.** `lv_font_conv` est une dépendance **npm** absente
du tableau des versions figées : un `idf.py build` sur un clone neuf **sans réseau** échouerait. Ce
n'est **pas** le même arbitrage que l'asset Living PCB, dont le générateur est en stdlib Python pure.

**`CONFIG_LV_FONT_MONTSERRAT_28` est désactivée** (plus rien ne la référence).
**`MONTSERRAT_14` reste**, et ce n'est pas une incohérence : elle est aussi `LV_FONT_DEFAULT`, et le
`choice LV_FONT_DEFAULT` de LVGL 9.5 (`Kconfig:991-1040`) **n'énumère que des built-ins**. La forcer
demanderait de patcher un composant managé — gitignoré et régénéré, donc un correctif qui ne
survivrait pas au premier `idf.py reconfigure`. Ses 13 596 o sont payés **délibérément**.

### 15.4 Les icônes — 10 glyphes dont 8 neufs, zéro asset, et le manquant est nommé

🔴 **`0xF863` (`fan`) est ABSENT** du `FontAwesome5-Solid+Brands+Regular.woff` du dépôt : il est
arrivé en FontAwesome **5.11** et le fichier embarqué est antérieur. **Vérifié en le convertissant
seul** (`lv_font_conv` échoue bruyamment sur un codepoint absent), pas déduit d'une table.

Codepoints **re-vérifiés un par un** le 2026-08-17, tous **présents** : `0xF2DB` microchip ·
`0xF108` desktop · `0xF538` memory · `0xF6FF` network-wired · `0xF1EB` wifi · `0xF2C9`/`0xF2C8`
thermometer · `0xF043` tint · `0xF72E` wind · `0xF021` sync · `0xF085` cogs · `0xF013` cog ·
`0xF2F1` sync-alt · `0xF0A0` hdd · `0xF233` server.

**W4 tranché par A/B sur la dalle**, quatre substituts embarqués **ensemble** et commutables à chaud
(`widget icone`) — un A/B qui aurait exigé trois reflashs coûte trois observations à l'owner pour un
rendement qui baisse. `sync-alt` : *« ne dit rien »*. `wind` : écarté. **`cog` RETENU.**
🔴 **Et il est GRATUIT** : `0xF013` est **déjà** l'un des codepoints que `built_in_font_gen.py`
injecte (61459). L'icône retenue ne coûte **aucun glyphe** de plus que la police de base.

**Le compte exact, CALCULÉ le 2026-08-18 et non plus récité** — le dictionnaire `ICONES` porte
**10** entrées, dont **2** (`cog` 0xF013 et `tint` 0xF043) sont **déjà** des symboles `LV_SYMBOL_*`
⇒ **8 codepoints neufs**, et **68** au `-r` FontAwesome final. La liste amont déclare **61** entrées
mais en contient **60 uniques** (doublon `61452`).
⚠️ **Ce paragraphe corrige cinq étiquettes fausses relevées en revue de code** : ce titre disait
« 7 glyphes », le README « 9 icônes », `dn_ui.c` et `sdkconfig.defaults` « 7 icônes », et
`dn_font.h` « 61 symboles + 10 icônes » — **aucune n'était simultanément juste**. Les nombres sont
désormais produits par `tools/gen_font_dn.py` et réinjectés dans le `.h` généré.

🔴 **ET LA GARDE QUI VÉRIFIAIT LEUR PRÉSENCE ÉTAIT AVEUGLE** (corrigée le 2026-08-18). `verifier()`
testait les **bornes** de chaque cmap. Or la cmap qui porte les symboles et les icônes est de type
**`SPARSE_TINY`** : dans le `.c` livré elle vaut `.range_start = 8226, .range_length = 55425,
.list_length = 69` — elle **borne** 8226 → 63650 en n'y portant que **69** codepoints. Le test de
bornes rendait donc `True` pour la **totalité** de `syms`, **`couvert(0xF863)` compris** :
**`fan`, le glyphe dont l'absence justifie toute cette section, aurait passé la vérification.**
Seuls les témoins accentués étaient réellement contrôlés (cmaps denses 32..126 et 160..255).
⇒ `codepoints_du_c()` décode maintenant `unicode_list_N` (offsets depuis `range_start`), et échoue
bruyamment si `list_length` et la liste se contredisent. **Contrôlé après correctif, sur les deux
polices livrées** : `fan` → **absent** · `Ā` (hors latin-1) → **absent** · `cog`, `LV_SYMBOL_LIST`,
`LV_SYMBOL_LEFT`, `É` → **présents** · **260 codepoints réellement portés** par police.
⚠️ Deuxième correctif du même bloc : `--mesure` **ne vérifiait rien** alors que c'est lui qui a
produit le tableau de §15.3 ayant tranché **W5** ; et les symboles étaient re-testés contre la liste
**lue dans l'amont** — un témoin tiré de la chose qu'il témoigne n'en est pas un, d'où deux
codepoints (`LV_SYMBOL_LIST` U+F00B, `LV_SYMBOL_LEFT` U+F053) écrits **en dur** et **délibérément**.

⛔ **Aucun asset image**, et le conflit est porté au ledger : `dn_asset` ne gère qu'**un** asset, et
la partition `assets` (1 MiB, 614 400 o occupés) n'a que ~434 Ko libres — **que dn3-3 réclame déjà
pour trois déclinaisons de 614 400 o : 3 × 614 400 > 1 MiB.**

### 15.5 🔴 L'A/B D'INVALIDATION — LE LEGS CHIFFRÉ POUR dn3-2

**Protocole** : `flush reset` avant chaque relevé · 25 mises à jour forcées sur **une seule** case
(`widget pousser`) · mock et capteur isolés · aire, flushes, `copie_us` et `attente_us` publiés
**séparément**.

> ✅ **RÉSERVE LEVÉE LE 2026-08-18 — LA PASSE A EU LIEU, LES CHIFFRES CI-DESSOUS SONT LES REJOUÉS.**
> Ce qui suit est le diagnostic qui l'avait motivée ; il est **confirmé par la mesure**.
>
> 🔴 **CE QUE LA REVUE DE CODE DU 2026-08-18 AVAIT TROUVÉ.**
> `indicateur = true` n'existe que sur **`VENTILOS`** (`dn_ui.c:187-193`) : le cas **(a′) « widget
> MONO avec jauge » EST donc la case 4**, celle que le mock possède. Or « mock isolé » veut dire
> `widget mock off` — et c'est **exactement** ce réglage qui arme un **second écrivain** : après
> chaque `widget pousser 4`, le tick 1 Hz de `mock_tick_nolock` (`dn_ui.c:2142-2148`) voit
> `regime != DN_VAL_ABSENTE` et **repose `ABSENTE`**, soit **un redessin de plus par poussée**, jamais
> compté comme une poussée.
> ⇒ C'est le défaut de `63344fc` **dans son angle mort** : le correctif a fermé le repeint *au repos*,
> pas le repeint *après poussée*. La règle du dépôt s'applique — *« un correctif qui touche un
> instrument invalide rétroactivement ce qu'il a publié »*.
> **Portée** : la ligne (a′) et le titre « −64 % », plus l'écart (a)→(a′) attribué à la jauge.
> **Non touchés** : (c) case nue (aucune source) et (a) `CPU` (`pc` jamais reçue).
> **(b) `AMBIANCE` est à instruire** : `dn_capteurs` y écrit toutes les 5 s et « capteur isolé »
> n'est défini nulle part.
> **Verdict owner : neutraliser le tick, rejouer (a′), instruire (b).** ✅ **FAIT** — correctif
> firmware (drapeau `s_vent_poussee`, `dn_ui.c`), campagne intégralement rejouée sur `9699adb`.
> 🔬 **LE CORRECTIF EST PROUVÉ PAR L'INSTRUMENT LUI-MÊME** : 25 poussées sur VENTILOS produisent
> désormais **exactement 25 cycles**. Avant, la story comptait **24 cycles là où 4 se justifiaient**.
>
> 🔴 **ET DEUX DES SEPT GRANDEURS EXIGÉES PAR AC8 MANQUENT ICI : `timeouts` ET `noops`.**
> `dn_ui.h:174` documente `timeouts` comme *« instrument **suspect** si non nul »*, et
> `dn_ui.h:175-177` documente `noops` comme *« **à SOUSTRAIRE du dénominateur** des moyennes
> temporelles »* — c'est-à-dire des colonnes **ms/cycle** ci-dessous.
> ✅ **RELEVÉS : `timeouts` = 0 et `noops` = 0 sur LES DIX relevés.** Le dénominateur des moyennes
> est donc `flushes` entier, et il est propre.
> 🔴 **ET LA PRÉMISSE DE LA DÉCISION ÉTAIT JUSTE POUR UNE AUTRE RAISON QUE CELLE ÉCRITE.** Ces deux
> lignes ne sont imprimées **QUE si le compteur est non nul** (`dn_console.c:1157-1182`) — le même
> patron que `dn_ui_async_refus()`, que la story documente déjà. **Leur absence EST le zéro**, elles
> n'avaient donc jamais « manqué » à l'instrument ; ce qui manquait, c'est de l'**écrire**.
> ⚠️ `noops` est en outre **structurellement nul ici** : il ne compte que les flushes no-op du
> **mode direct**, et ce build est sur le chemin `bitmap`.

⚠️ **L'injecteur pousse UNE fois par appel, et c'est structurel** : une boucle de *N* poussées dans
la commande aurait fait tomber les *N* invalidations dans le **même cycle LVGL de 33 ms**. LVGL les
aurait fusionnées, on aurait mesuré **1 flush pour N mises à jour**, et conclu que grouper est
gratuit. Séparer les poussées dans le **temps** est la seule façon que chacune ait son cycle.

**RELEVÉS REJOUÉS le 2026-08-18, firmware `9699adb`** — 25 poussées par relevé, espacées de 120 ms
(> 2 cycles LVGL), mock **coupé**, `flush reset` avant chacun, `timeouts` = `noops` = **0** partout.

| cas | branche A — N zones fines | branche B — 1 zone englobante |
|---|---|---|
| **(a)** widget MONO **sans** jauge (CPU) | **2,00** flush/cyc · **10 749 px**/cyc | 1,00 · **35 100 px** |
| **(a′)** widget MONO **avec** jauge (VENTILOS) | **3,12** flush/cyc · **16 577 px**/cyc | 1,00 · 35 100 px |
| **(b)** widget **BI-grandeurs** (AMBIANCE) | **2,12** flush/cyc · **17 536 px**/cyc | 1,00 · **35 100 px** = 225 × 156 |
| **(c)** case **NUE** — témoin négatif (GPU) | **1,00** flush/cyc · **3 321 px**/cyc | **1,00 · 3 356 px** |

| cas | copie A | attente A | copie B | attente B | **ms/cycle A → B** |
|---|---:|---:|---:|---:|---|
| (a) | 276 µs/f | 14 748 µs/f | 2 935 µs/f | 13 163 µs/f | **30,0 → 16,1 (−46 %)** |
| (a′) | 266 µs/f | 17 507 µs/f | 2 934 µs/f | 12 899 µs/f | **55,5 → 15,8 (−71 %)** |
| (a′) *passe 2* | 271 µs/f | 17 124 µs/f | 2 933 µs/f | 14 279 µs/f | **53,6 → 17,2 (−68 %)** |
| (b) | 397 µs/f | 14 243 µs/f | 2 924 µs/f | 14 665 µs/f | **31,0 → 17,6 (−43 %)** |
| (c) | 214 µs/f | 15 792 µs/f | 322 µs/f | 12 597 µs/f | 16,0 → 12,9 (**témoin, voir ci-dessous**) |

🔴 **CE QUE LE REJEU CHANGE, ET C'EST DANS LE SENS QUI DÉRANGE LE PLUS.** Le chiffre-titre n'était pas
trop optimiste, il était **trop timide** : (a′) gagne **−68 à −71 %** sur deux passes, contre les
**−64 %** publiés. La branche FINE coûtait **plus cher** que mesuré (**55,5 / 53,6 ms** contre 48,8),
parce que les repeints `ABSENTE` parasites **gonflaient le dénominateur** — ils ajoutaient des cycles
bon marché qui diluaient `flush/cyc` de **3,12 à 2,95**.
⚠️ **Et l'AIRE, elle, était JUSTE** : 16 577 px/cyc rejoués contre 16 573 publiés — **0,02 % d'écart**.
Le défaut d'instrument touchait le **compte de flushes et de cycles**, jamais la surface. C'est
précisément ce qu'un relevé qui publie ses grandeurs **séparément** permet de dire.

✅ **LE TÉMOIN NÉGATIF TIENT, ET IL A FALLU SOUSTRAIRE LE PARASITE POUR LE VOIR.** Brut, la case nue
semble passer de 3 321 à 4 577 px/cyc — ce qui aurait fait croire que le groupage la touche. Elle
n'a reçu qu'**un cycle parasite** : 26 cycles pour 25 poussées, et ce cycle-là est une écriture
`AMBIANCE` du capteur, à 35 100 px puisqu'on est en branche groupée.
`(118 995 − 35 100) / 25 = 3 356 px` contre **3 321 px** en fine, soit **1,0 % d'écart** et
**1,00 flush/cyc des deux côtés** : la case nue ne traverse pas le modèle, et le groupage ne
l'atteint pas. **Le reste de l'écart en ms est du bruit d'attente de synchro** (12,6 à 17,5 ms selon
le relevé), pas un effet.

🔬 **(b) INSTRUIT — « CAPTEUR ISOLÉ » N'A PAS DE SENS POUR AMBIANCE, ET N'EN A PAS BESOIN.** C'était
la question laissée ouverte. Réponse : pour les cases (a), (a′) et (c), l'écriture du capteur est un
parasite **étranger**, identifiable et soustrayable (`cycles − poussées`, à 35 100 px l'unité en
groupé). Pour **(b), la case du capteur EST la case mesurée** : un cycle venu du capteur et un cycle
venu d'une poussée produisent **le même travail sur la même case**. La mesure est donc **homogène**,
et `cycles` les compte tous les deux correctement — il n'y a rien à museler. Silencer le capteur
aurait au contraire injecté un artefact : la bascule vers `ABSENTE` à la péremption est **elle-même**
un redessin.
🔬 **Contribution parasite mesurée**, fenêtre de 20 s sans aucune poussée : **4 cycles** — le capteur
seul à 5 s, exactement ce qui se justifie. (La story avait mesuré **24** avant son correctif
`63344fc` ; le drapeau `s_vent_poussee` ferme le dernier chemin qui restait.)

🔴 **LA PRÉDICTION EST CONFIRMÉE DANS SON SENS, DÉMENTIE DANS SON AMPLEUR.** La story annonçait que
l'attente domine la copie *« d'un facteur ~50 »*. **Mesuré au rejeu : ~4,4 à 5,0** (copie groupée
**2 924-2 935 µs** contre attente **12 899-14 665 µs**). Le groupage gagne quand même — parce qu'il
**supprime un flush entier** (~15 ms) pour **~2,7 ms** de copie en plus, soit un retour de
**~5,5 pour 1**. Une prédiction démentie est plus instructive qu'une prédiction tenue, et ce dépôt a
déjà vu un facteur 10 d'écart (T9).

⚠️ **CE QUE LE GROUPAGE NE FAIT PAS** : il n'économise **aucun** pixel, il en **multiplie** le nombre
par **2,0 à 3,3 selon la case** (BI 17 536 → 35 100, soit ×2,0 ; MONO sans jauge 10 749 → 35 100,
soit ×3,3). Ce n'est pas une optimisation d'aire, c'est un **échange** : beaucoup de pixels contre
une attente de trame. Le jour où la copie deviendra le goulot, l'arbitrage devra être **rejoué** — la
branche fine reste vivante et rejouable sans reflasher (`widget groupe`).
⚠️ **Le facteur d'aire dépend de la RICHESSE de la case, et il joue à l'ENVERS de l'intuition** :
plus une case a d'enfants qui changent, plus sa branche fine est déjà large, donc **moins** le
groupage lui coûte en pixels — et **plus** il lui rapporte en flushes. C'est pour ça que (a′), la
case la plus riche (3,12 zones fines), est celle qui gagne le plus (**−68 à −71 %**).

⚠️ **UNE MISE EN GARDE SUR L'ATTENTE DE SYNCHRO, POUR QUI RELIRA CE TABLEAU.** Elle varie de
**12,6 à 17,5 ms** d'un relevé à l'autre, sans rapport avec la branche : c'est le régime
d'échantillonnage, pas un effet mesuré (déjà relevé en T0 de dn3-1, 17,7 ms contre les 12,7 ms de
§11.6). ⇒ **Ne jamais comparer deux `attente_us` issus de fenêtres différentes**, et ne conclure que
sur `flush/cyc`, qui est stable à ±0,04 entre les deux passes de (a′).

✅ **LE TÉMOIN NÉGATIF EST INTACT** : la case nue mesure **exactement pareil** dans les deux branches
(elle ne traverse pas le modèle). C'est ce qui prouve que la différence vient du **groupage** et non
d'un effet de bord de la campagne.

**Extrapolation à six widgets vivants, et ce qu'elle suppose** :
- Six widgets **groupés** invalideraient **6 × 35 100 = 210 600 px/cycle**, soit **69 % d'un plein
  écran** — le contre-argument que la story demandait d'instruire. ⚠️ **Mais il ne se réalise que si
  les six se mettent à jour dans le MÊME cycle**, ce qui suppose des sources synchronisées. Elles ne
  le sont pas (liaison PC ~1 s, capteur 5 s, mock 1 s).
- En cadences **décalées**, le coût groupé est de **15,8 à 17,6 ms par mise à jour** — et c'est
  l'observation la plus utile du rejeu : **il ne dépend PLUS de la case**. En fine, il allait de
  16,0 à 55,5 ms selon la richesse ; groupé, les quatre cas tiennent dans **12,9-17,6 ms**. Le
  groupage ne fait pas que réduire le coût, il le rend **PRÉVISIBLE** — un budget par mise à jour,
  indépendant du contenu de la case. C'est ce qui rend un budget à six cases calculable du tout.
  ⇒ **six sources à 1 Hz coûteraient ~100 ms/s (10 % de duty)** en groupé, contre **~180-330 ms/s
  (18-33 %, selon les cases retenues)** en fine — et cette fourchette-là est justement ce que le
  groupage supprime.
- ⚠️ **Ce que l'extrapolation NE prouve PAS** : elle est linéaire, et rien ne dit que le rendu LVGL
  l'est. Le plancher d'une transition est le **rendu** (~230 ms sur 307), pas la copie. **dn3-2 doit
  re-mesurer à six, pas déduire.** *« Ça ne viendra pas tout seul. »*

### 15.6 L'A/B D'OPACITÉ — la seule décision prise CONTRE sa mesure

`nav ab 20`, n = 40 par branche, base dn2-1 = **307,0 ms**.

| opacité des cases | min | **moyenne** | max |
|---|---:|---:|---:|
| **178** (`LV_OPA_70`, état des lieux) | 293,8 | **321,8 ms** | 369,9 |
| **255** (`LV_OPA_COVER`, opaque) | 267,0 | **299,9 ms** | 343,2 |
| **127** (`LV_OPA_50`) | 293,8 | **321,5 ms** | 352,2 |

🔴 **127 et 178 donnent le MÊME chiffre.** Ce n'est donc **pas la valeur** d'opacité qui coûte,
c'est le **fait de n'être pas opaque** : le re-blit du fond est **tout ou rien**. Ce résultat n'était
pas dans les prévisions, et il simplifie l'arbitrage — il n'y a pas de compromis intermédiaire à
chercher.

**W8 — VERDICT OWNER : TRANSLUCIDE.** *« C'était mieux avant. »* Les **21,9 ms** (−6,8 %) sont
**rendues délibérément** : le Living PCB est l'identité du produit, et un dashboard qui l'efface de
ses six cases n'est plus le même objet. ⚠️ **Ce n'est donc pas une optimisation en attente** : c'est
un arbitrage **fermé**, esthétique contre latence, l'esthétique ayant gagné **avec le chiffre en
face**. L'option n°1 du ledger est **tranchée**, pas reportée.

**W9 — voile plein écran : `90/255` (35 %)**, contre `LV_OPA_50` (127) auparavant. Constat owner :
*« le PCB respire mieux »*, texte lisible **partout**, y compris sur les cases-widgets — qui étaient
le risque nommé (un widget est plus contrasté qu'une case nue). ⚠️ **Purement esthétique** : la
mesure ci-dessus montre que le voile ne coûte **rien** en latence. Écrit pour que personne ne
l'« optimise ».

⚠️ **§10.4 rappelé, et non fabriqué** : `vsync` ne protège pas une zone sale **pleine hauteur**. Une
jauge de 10 px **dans** une case de 156 px en est très loin ; un indicateur qui traverserait la dalle
y retomberait. **Aucun élément de dn3-1 n'est pleine hauteur.**

### 15.7 « Toute la case est la zone tactile » — RE-PROUVÉ SUR LE PIÈGE

🔴 **Les jauges de LVGL sont cliquables par défaut** : `lv_obj` pose `CLICKABLE`+`SCROLLABLE`
(`lv_obj.c:584-593`), `lv_label` **retire** clickable (`:762`), mais **`lv_bar` le CONSERVE**
(`:341`), `lv_scale` aussi (`:643`), et `lv_arc` l'**ajoute** (`:539`). Une jauge posée dans une case
**vole le tap sur son propre rectangle**, et la propriété prouvée à 4 px du bord en dn1-4 devient
fausse **en silence** — invisible au compteur de taps si on vise le centre.

**Preuve, `touch trace 30000`, constat owner du 2026-08-17 :**

```
APPUI 1 · (133, 513)  -> TAP sur VENTILOS      <- LA JAUGE (barre y = 506..516)
APPUI 2 · ( 94,  27)  -> TAP sur RETOUR
APPUI 3..19 · y = 24..72 (barre heure/date)    <- AUCUN TAP : zone morte intacte
APPUI 20 · (230, 232) -> TAP sur CPU           <- 5 px du bord droit, 4 px du bas
APPUI 21 · ( 45,  28) -> TAP sur RETOUR
```

- **Le tap visant la jauge est arrivé sur VENTILOS**, pas sur la jauge ⇒ la parade
  `lv_obj_clear_flag(jauge, LV_OBJ_FLAG_CLICKABLE)` tient.
- **17 appuis consécutifs sur la barre heure/date n'ont ouvert RIEN** ⇒ la zone morte est intacte, et
  le voile plein écran reste non cliquable.
- **`dn_ui_async_refus()` = 0** ⇒ aucun tap refusé par `lv_async_call`. ⚠️ Cette ligne n'est imprimée
  **que** si le compteur est non nul (`dn_console.c:1439-1445`, relu) : son absence **est** le zéro.
- ⚠️ **Écart déclaré** : le geste 4 visait la **gouttière** et a atterri **dans** la case CPU, à 4-5 px
  du coin. La zone morte de la gouttière n'a donc **pas** été prouvée. Ce que le tir a prouvé à la
  place vaut mieux : **« toute la case » tient jusqu'à 4 px du bord**, re-démontré avec un widget.

### 15.8 Les budgets, re-relevés — et la seule régression, attribuée

Firmware **`969847c`**, boot frais, contre la base dn2-1 du 2026-08-17 (`c30c7ad`).

| mesure | base `c30c7ad` | **dn3-1 `969847c`** | écart |
|---|---:|---:|---|
| Binaire | 832 720 o | **885 232 o** | **+52 512 o (+6,3 %)** — partition `factory` libre à **79 %** |
| RAM interne libre | 109 303 o | **108 679 o** | −624 o |
| PSRAM libre | 7 768 360 o | **7 768 324 o** | −36 o |
| Tas LVGL (boot) | 15 200 o / 25 %, frag 1 % | **17 768 o / 29 %, frag 1 %** | **+2 568 o** pour 3 widgets |
| `fps 15` | 37,40 Hz, +0,00 % | **37,40 Hz, +0,00 %** | **0** |
| Boot | 2 190 ms | **2 236 ms** | +46 ms |
| Latence transition | 307,0 ms | **321,8 ms** | +14,8 ms (widgets plus riches) |
| CPU au repos | 1,3 % | **3,8 %** | **+2,5 pt — voir ci-dessous** |

🔴 **LA RÉGRESSION CPU EST ENTIÈREMENT ATTRIBUABLE AU MOCK, PAS AU MODÈLE.** Décomposée avec le bon
instrument (`cpu 20`, valide pour le redessin qui ne passe pas par le REPL) :

| mock | groupage | CPU | cycles / 20 s |
|---|---|---:|---:|
| off | off | **1,2 %** | 4 (capteur seul) |
| off | on | **1,4 %** | 5 |
| on | off | **3,2 %** | 24 |
| on | on | **3,8 %** | 33 |

⇒ **À la cadence du capteur, le modèle de widget coûte zéro point mesurable** (1,2 % contre 1,3 %
en base, dans le bruit) malgré une case 7,6 × plus grande et six enfants au lieu de deux. Le
groupage coûte **+0,2 pt**. Les **+2,4 pt** restants viennent du **mock à 1 Hz**, soit **5 × la
cadence du capteur** — et le mock est un **instrument de dn3-1**, pas un comportement produit.

⇒ **LEGS POUR dn3-2, ET C'EST LE PLUS ACTIONNABLE DE TOUS** : **le coût suit la CADENCE DE MISE À
JOUR, pas la richesse du widget.** Ramené par redessin/seconde, on trouve **~2,2 pt** — à comparer
au **+0,53 pt par case et par redessin** de dn2-2, qui vaut **~2,65 pt** une fois ramené à la même
normalisation. ⚠️ **Les deux chiffres viennent de deux instruments et de deux richesses de widget
différentes** : la concordance est un contrôle croisé, pas une égalité.

**Gardes de dn2, toutes re-vérifiées** : « `--` » grisé **dès la première trame** au boot (les six
cases, avant que quiconque ait alimenté quoi que ce soit) · péremption capteur 15 s effective
(`capteurs simuler muet 40` → régime `ABSENTE`) · les **deux** modèles de navigation marchent, et en
`rebuild` vue détail les six cases rendent `dessinee = NON` avec leur **état conservé**, reposé au
retour **sans retomber sur un factice** · `ui off`/`ui on`/`scene`/`tear`/`flush full` **sûrs**
(`flush full` = 307 200 px, 5,0 flush/cycle, aucune panique ; `scene` et `tear` **refusés** tant que
LVGL tient l'écran, ce qui est le comportement voulu).

**Pas de fuite de tas LVGL** : 5 bascules `screens ⇄ rebuild` enchaînées laissent le tas **plat**
(17 768 o au boot → 17 756 o après, **−12 o**).
⚠️ **La fragmentation monte à 28 %** après bascules répétées (relevé du 2026-08-18 sur `9699adb`),
contre **22 %** publié par dn3-1 et **15-19 %** au ledger — elle **s'aggrave à chaque marche**, et
c'est maintenant une tendance à trois points, plus un accident. Le tas reste **PLAT** sur les mêmes
5 bascules (14 724 → 14 744 o, **+20 o**) : ce n'est **pas** une fuite. Elle
retombe à **1 %** au boot. Résiduel **connu, aggravé**, à porter au ledger : les objets de dn3-1
sont plus gros, donc les trous laissés le sont aussi.

### 15.9 Ce qui n'a pas marché, conservé avec son symptôme

1. **Le mock repeignait à 1 Hz même coupé.** `lv_label_set_text` invalide **inconditionnellement**,
   même avec un texte identique. Le témoin d'AC8 (« 0 poussée pendant 20 s ») a compté **24 cycles**
   là où le capteur seul, à 5 s, n'en justifie que **4**. Les 20 en trop sont exactement le nombre de
   ticks : **83 % de la « contribution parasite » qu'on croyait quantifier était fabriquée par la
   mesure elle-même**, et elle polluait aussi les relevés par cas. Trouvé en **regardant** le chiffre
   du témoin au lieu de le noter : *24 ≠ 4 n'a pas d'explication innocente.*
2. **Un compteur d'octets de police aveugle à ce qu'il mesurait.** Les regex exigeaient `= {`, mais
   le `.c` généré met l'accolade **à la ligne suivante** : `glyph_bitmap` **et** les trois tables de
   kerning comptaient **zéro**, et l'outil rendait un total **identique** avec et sans
   `--no-kerning`. Corrigé en **relisant le `.c`**, puis **validé contre le témoin** des built-ins
   embarqués — c'est cette validation qui a révélé l'erreur d'un tiers de la story (§15.3).
3. **`%-10s` remplit en OCTETS.** « RÉSEAU » décalait sa ligne dans le tableau de `widget` — le
   **défaut exact** que l'en-tête de `dn_console_banner()` explique quelques centaines de lignes plus
   bas, **re-commis** parce que dn3-1 est la story qui **accentue les libellés**. Corrigé par un
   remplissage en **colonnes d'affichage** (un octet de continuation UTF-8 vaut `10xxxxxx`).
4. **« 179 = LV_OPA_70 » et « 128 = LV_OPA_50 » : faux.** Ce sont **178** et **127** (`lv_color.h:47-49` :
   70 % de 255 fait 178,5 et LVGL **tronque**). Une étiquette fausse d'un cran reste une étiquette
   fausse.
5. **Une fausse alerte sur AC5, et c'était le protocole.** `capteurs simuler muet 4` (≈20 s) expirait
   **pendant** l'attente : le capteur repoussait une valeur réelle avant le constat owner, qui a donc
   vu un chiffre et conclu que le détail mentait encore. Rejoué avec `muet 40` (≈200 s) : « `--` »
   gris. ⚠️ **Une faute simulée doit couvrir toute la fenêtre d'observation, pas seulement la
   péremption.**
6. **Réfutation conservée** : un `reboot`/flash rend la carte muette ~3,5 s. Deux « cartes muettes »
   de cette session étaient des sollicitations trop précoces, **pas** des pannes — la recette du
   README ne s'appliquait pas.

---

## 16. LE BUDGET À SIX WIDGETS VIVANTS — mesuré le 2026-08-18 (dn3-2, P7)

**Firmware `ea986ed`.** Géométrie **inchangée** (W4 tranché « exigence retirée ») ⇒ **l'unité de
35 100 px de la §15 reste valide et tous les chiffres de dn3-1 restent comparables.**

⚠️ **Cette section remplace l'EXTRAPOLATION de la §15.5, elle ne la contredit pas partout** :
elle en confirme une moitié au pixel près et en **dément une autre**, et les deux sont écrites.

### 16.0 🔴 Le correctif d'instrument qui précède tout le reste

`cpu brut` **rendait du VIDE en silence** — en-tête imprimé, zéro ligne de tâche, invite rendue.
Ce n'était ni une troncature série (l'invite est arrivée), ni un port volé (`TIOCEXCL`), ni le hook
`rtk` (capture par `rtk proxy`). `vTaskGetRunTimeStats()` fait son propre `pvPortMalloc` puis teste
`if (ulTotalTime > 0)`, **et n'a aucun chemin pour signaler qu'elle n'a rien écrit**.

⇒ Remplacée par `uxTaskGetSystemState()`, même source, allocation vérifiée, échec **nommé**.
🔴 **La première campagne AC8 (firmware `e9c52e2`) a donc été JETÉE, pas rattrapée**, et rejouée
entièrement — règle §13.7 : *« un correctif qui touche un instrument invalide rétroactivement tout
ce que cet instrument a publié »*.

⚠️ Le `%` de `cpu brut` est désormais calculé sur le **total DEUX CŒURS** relu et **imprimé** :
deux `IDLE` à 99 % et 85 % ne font pas 184 %, ils font 92 % d'un biprocesseur au repos.

### 16.1 La table de décomposition — mock × groupage, fenêtre 45 s

Protocole : `flush reset` puis `cpu brut` avant, écoute passive 45 s (**rien n'est envoyé**),
`cpu brut` puis `flush` après. `cfg` relevé au début **et** à la fin, identique
(`num_fbs=1 bounce_px=4800 draw_lines=128 draw_psram=0 lvgl_core=0`).

| mock | groupage | CPU | dont `taskLVGL` | cycles/s | **flush/cyc** | **px/cyc** | copie µs/f | attente µs/f | ms/cyc | duty |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| off | off | 1,35 % | 0,86 pt | 0,20 | **2,00** | 12 210 | 315 | 12 439 | 25,5 | 0,5 % |
| off | **on** | 1,49 % | 1,00 pt | 0,22 | **1,10** | 32 342 | 2 437 | 14 913 | 19,1 | 0,4 % |
| on | off | 7,66 % | 7,08 pt | 1,20 | **8,67** | 39 427 | 240 | 15 565 | 137,0 | 16,4 % |
| on | **on** | **10,18 %** | 9,64 pt | 1,21 | **3,47** | 120 756 | 2 883 | 13 075 | 55,4 | 6,7 % |

### 16.2 🔴 LE GROUPAGE GAGNE EN TEMPS MURAL ET PERD EN CPU — dn3-1 n'avait pas de colonne CPU

| | fine | groupé | écart |
|---|---:|---:|---|
| flush/cycle | 8,67 | 3,47 | **−60 %** |
| px/cycle | 39 427 | 120 756 | **×3,06** |
| ms/cycle | 137,0 | 55,4 | **−60 %** |
| duty | 16,4 % | 6,7 % | **−59 %** |
| **CPU** | 7,66 % | **10,18 %** | 🔴 **+2,52 pt** |

**Le mécanisme, et il n'a rien de paradoxal** : ce que le groupage SUPPRIME est de l'**attente de
synchro** — la tâche dort en attendant sa trame, et dormir ne coûte pas de CPU. Ce qu'il AJOUTE est
du **rendu et de la copie** : 2 883 µs/flush contre 240, et une aire ×3,06 que LVGL doit
effectivement **dessiner**. `taskLVGL` passe de 7,08 à 9,64 pt, soit **+2,56 pt** — c'est-à-dire la
totalité de l'écart.

🔴 **dn3-1 a mesuré des ms/cycle SANS colonne CPU** (§15.5 : copie, attente, ms/cycle) et a conclu
« le groupage gagne ». **C'est vrai en LATENCE et muet en CHARGE.** Les deux mesures sont justes,
elles ne portent pas sur la même grandeur — et le budget d'un module qui tourne H24 (dn4-1) se
raisonne sur la seconde.

⚠️ **Ce que le groupage ne fait toujours pas** : il n'économise **aucun pixel**, il en **multiplie
le nombre par 2,65 à 3,06** selon le régime (2,0 à 3,3 en dn3-1 — même ordre, confirmé).

### 16.3 ✅ LE CAS « LES SIX DANS LE MÊME CYCLE » — PROVOQUÉ, ET L'EXTRAPOLATION EST EXACTE

Les six sources ne sont **pas** synchronisées (liaison ~1 s, capteur 5 s, mocks 14/20/26/34 s,
barre à la minute) et `dn_ui_pousser` **interdit par conception** N poussées dans un même appel.
Le cas a donc été **provoqué** par un instrument neuf, `widget rafale` : N poussées sous **un seul
verrou LVGL**, donc dans un seul cycle. Son témoin de validité est `cycles intercalés == 0` — un
cycle qui s'intercale signifie que la rafale a été coupée et que le chiffre ne vaut rien.

Six tirs, stabilisation de 3 s avant chacun, fenêtre de 2 s après :

| tirs | cycles | flushes | aire | lecture |
|---|---|---|---|---|
| **3 / 6** | **1** | **6** | **210 600 px** | le cas pur |
| 3 / 6 | 2 | 7 | 245 700 px | + une source concurrente (exactement +1 case) |

> **6 × 35 100 = 210 600 px, soit 68,6 % d'un plein écran, en 6 flushes.**
> L'extrapolation de la §15.5 annonçait **210 600 px et 69 %**. ✅ **Confirmée au pixel près.**

🔴 **Et elle reconfirme le legs de dn2 : LVGL NE FUSIONNE AUCUNE des six zones.** Six zones
disjointes de 225 × 156 donnent six flushes, pas moins — la plus grande aire relevée reste
**35 100 px**, jamais une union. Copie **2 912 ± 5 µs/flush** sur les six tirs.

⚠️ **PIÈGE D'INSTRUMENT DÉCOUVERT ICI** : `flush reset` remet les **compteurs** à zéro mais **ne
vide pas la file d'invalidation LVGL en attente**. Un premier tir précédé d'un `widget mock off`
dans le même envoi a rendu **5 flushes / 175 500 px** — une invalidation en vol avait traversé le
reset. ⇒ **laisser 3 s de stabilisation avant `flush reset`**, sinon le tir suivant est faussé
*vers le bas*, ce qu'aucune pollution ne peut expliquer et qu'on lirait donc comme un résultat.

### 16.4 Le coût par MISE À JOUR — l'autre moitié de l'extrapolation

| | mesuré à six | extrapolé §15.5 | verdict |
|---|---:|---:|---|
| ms par mise à jour, **groupé** | **16,0 ms** | 15,8 – 17,6 ms | ✅ **dans la fourchette** |
| ms par mise à jour, fine | 39,5 ms | 16,0 – 55,5 ms | ✅ dans la fourchette |
| duty, **groupé** | **6,7 %** | ~10 % | ⚠️ l'extrapolation **surestimait de 49 %** |
| duty, fine | 16,4 % | 18 – 33 % | ⚠️ **sous** le bas de la fourchette |

**Lecture** : l'extrapolation était juste **par mise à jour** et pessimiste **en duty**, parce
qu'elle supposait six sources à 1 Hz. Le régime réel en compte moins : 1,21 cycle/s mesuré, pour
3,47 mises à jour par cycle.

### 16.5 🔴 LA BARRE NE COÛTE PAS 33 600 px — ELLE EN COÛTE **6 334**, ET LA PRÉMISSE ÉTAIT FAUSSE

La story de dn3-2 posait : *« la barre fait 480 × 70 = 33 600 px, soit 96 % d'une case ⇒ une barre
qui bat à 1 Hz est, en coût brut, une 7ᵉ case vivante à 1 Hz »*. ⚠️ Elle demandait aussi que
*« l'ordre de grandeur soit vérifié, pas récité »*. **Il l'a été, et il est faux d'un facteur 5,3.**

**Mécanisme** : la barre n'est **PAS un widget**, donc elle **n'est pas groupée**. Ses deux labels
sont des objets LVGL indépendants, et `lv_label_set_text` invalide **la bbox du label**, pas le
conteneur de 480 × 70. Le raisonnement « 96 % d'une case » supposait implicitement un groupage qui
n'existe pas ici.

**Protocole** : mock coupé, capteur muté (`capteurs simuler muet 60`), `flush reset`, fenêtre 70 s,
`draw_lines = 128`, groupage ON. Le capteur muté continue de pousser ABSENTE toutes les 5 s : il
donne **14 cycles à 35 100 px** qui se soustraient.

| régime | flushes | cycles | flush/cyc | dont barre | **px par mise à jour de barre** |
|---|---:|---:|---:|---:|---:|
| **HH:MM** *(défaut)* | 16 | 16 | 1,00 | ~2 cycles / 70 s | — |
| **HH:MM:SS (1 Hz)** | 84 | 84 | **1,00** | **70 cycles / 70 s** | **6 334 px** |

⇒ **6 334 px = 18 % d'une case (35 100 px)**, et **1,0 flush par mise à jour**.
⇒ En duty, le régime 1 Hz coûte **70 × (678 + 8 252) µs = 625 ms sur 70 s, soit 0,89 %**.

### 16.5 bis 🔴 LE CORRECTIF QUE CETTE MESURE A TROUVÉ — la barre invalidait DEUX zones pour UNE

**Premier relevé, avant correctif : 154 flushes pour 84 cycles**, soit **2,0 flush par mise à jour
de barre** au lieu de 1,0. `barre_composer()` rendait **un seul** booléen « quelque chose a changé »
et `barre_ecrire_nolock()` réécrivait **les deux** labels. Or en 1 Hz l'heure change chaque seconde
et **la date ne change qu'une fois par jour** — et `lv_label_set_text` invalide
**inconditionnellement**, même à texte identique. La date coûtait donc **une seconde zone sale par
seconde, pour rien.**

⚠️ **C'est le défaut que dn3-1 avait corrigé sur le mock** (§15.5 : 24 cycles comptés là où 4
étaient justifiés, **83 % de la contribution parasite fabriquée par la mesure elle-même**),
**réintroduit par une autre porte** — et il polluait l'A/B **même** qui devait chiffrer la cadence.
⇒ Deux drapeaux séparés ; chaque label n'est écrit que si **son** texte a changé. La
(re)construction, elle, passe par un chemin qui pose **les deux** : des labels qui viennent de
naître ne portent ni texte ni couleur.

### 16.5 ter W2 — LA CADENCE EST TRANCHÉE PAR LA MAQUETTE, **ET LE CHIFFRE LE DIT HONNÊTEMENT**

**Régime retenu : `HH:MM`, sans secondes.** Le motif est **la maquette normative** (addendum §1,
qui écrit « 21:46 »), ⛔ **et PAS le coût** — parce que le coût mesuré du 1 Hz est **modeste**
(0,89 % de duty, 6 334 px par mise à jour, 1,0 flush) et **n'aurait pas suffi à trancher**. Écrire
« on prend la minute parce que c'est moins cher » aurait été un raisonnement fabriqué après coup.

⚠️ Le calage sur la minute est **structurel, pas temporisé** : `dn_ui_heure_maj` n'écrit dans les
labels que si le **texte composé change**. En `HH:MM` il ne change qu'au changement de minute ⇒ ça
ne peut pas retarder de 59 s, contrairement à un timer libre. `widget barre 1hz|minute` rejoue l'A/B
**sans reflasher**.

⚠️ La barre est **sondée à 2 Hz** (`DN_RTC_PERIODE_MS 500`) et **dessinée** à la minute : le sondage
et l'affichage sont deux cadences distinctes, et seul le second coûte des pixels.

🔴 **Le régime par défaut est HH:MM, sans secondes**, et c'est la maquette normative qui tranche
(addendum §1 écrit « 21:46 »). Le mécanisme est **structurel, pas temporisé** : `dn_ui_heure_maj`
n'écrit dans les labels que si le **texte composé change**. En HH:MM il ne change qu'au changement
de minute ⇒ le calage sur la minute qu'AC4 exige ne dépend d'aucun timer libre, et ne peut donc pas
retarder de 59 s. `widget barre 1hz|minute` rejoue l'A/B **sans reflasher**.

⚠️ La barre est **sondée à 2 Hz** (`DN_RTC_PERIODE_MS 500`) et **dessinée** à la minute : le
sondage et l'affichage sont deux cadences distinctes, et seul le second coûte des pixels.

### 16.6 Non-régression — table avant/après

| Mesure | `a64d4c3` (dn3-1) | `ea986ed` (dn3-2) | Δ |
|---|---:|---:|---|
| Binaire `desknode.bin` | 886 608 o | **901 328 o** | +14 720 o · partition libre à **79 %** |
| RAM interne libre | 108 435 o | **103 559 o** | **−4 876 o** = la pile 4 096 o de `dn_rtc` + son `.bss` |
| PSRAM libre | 7 768 324 o | 7 768 236 o | −88 o |
| Tas LVGL | 17 772 o / 29 % | **20 108 o / 33 %** | **+2 336 o** pour 3 widgets + 2 labels de barre |
| Plus gros bloc libre | 44 164 / 44 596 | **41 304 / 41 996** | **98,4 % du libre en un bloc** |
| Fragmentation | 28 % (post-revue dn3-1) | **2 %** | 🔴 voir ci-dessous |
| Tas sur transitions | +20 o (n=5) | **+24 o (n=40)** | ✅ PLAT, pas de fuite |
| `fps 15` | 37,40 Hz, +0,00 % | **37,40 Hz, +0,00 %** | ✅ identique |
| Boot | 2 245 ms | **2 287 ms** | +42 ms |
| Latence transition (n=40) | 321,8 (293,8 / 369,9) | **349,1 (293,2 / 452,3)** | 🔴 **+27,3 ms de moyenne, +82,4 ms au max** |

🔴 **LA « TENDANCE À TROIS POINTS » DE LA FRAGMENTATION EST ROMPUE — ET LE CHIFFRE N'ÉTAIT PAS
COMPARABLE.** Le ledger disait 15-19 %, dn3-1 22 % puis 28 %. On mesure **2 %**. Mais le critère
imposé par le tracker est **le plus gros bloc libre**, et lui raconte autre chose : dn3-1 publiait
**44 164 o libres d'un bloc sur 44 596** — soit **99,0 %**, ce qui est **incompatible avec 28 % de
fragmentation**. ⇒ Les deux chiffres de dn3-1 ne décrivaient pas le même instant. **On garde les
deux et on le dit** (règle du dépôt), et on ne publie plus que le plus gros bloc libre : **41 304
sur 41 996, soit 98,4 %.**

🔴 **LA LATENCE DE TRANSITION RÉGRESSE DE +27,3 ms, ET C'EST ATTENDU** : `build_scene()` construit
désormais **six widgets** au lieu de trois widgets + trois cases nues. ⚠️ Le budget brief
**< 300 ms** était **déjà non tenu** (321,8 ms) et **se solde en dn4-1** — mais **l'écart se
creuse**, et le maximum passe de 369,9 à **452,3 ms**. ⛔ Ne pas présenter l'opaque comme la parade :
l'A/B d'opacité est **tranché** (§15.6), l'owner rend les 21,9 ms délibérément.

### 16.7 ✅ W8 — LE REPEINT EN BANDES : ESSAYÉ, CHIFFRÉ, ET IL GAGNE **SOUS CONDITION**

**Le mécanisme est LU dans le source du composant managé, pas supposé** — `lv_refr.c:321-328` :
LVGL envoie `LV_EVENT_INVALIDATE_AREA` avec l'aire, **puis** dédoublonne par
`lv_area_is_in(nouvelle, sauvegardée)`. 🔴 **Il ne FUSIONNE jamais : il JETTE une aire CONTENUE
dans une autre.** ⇒ l'hypothèse de la story est **fondée** : deux cases d'une même ligne élargies à
`0..479` deviennent **identiques**, donc la seconde est jetée.

**Mais l'arithmétique du draw buffer s'y oppose, et la prédiction a été écrite AVANT la mesure** :
le buffer fait `480 × draw_lines` **pixels**. À 225 px de large il tient `61 440 / 225 = 273`
lignes, donc une case de 156 passe en **un** flush. À 480 de large il n'en tient que `draw_lines`.

**Instrument** : `widget bandes on|off`, **inerte par défaut**, et qui **ne reconstruit rien** — le
drapeau agit sur la **prochaine** invalidation, donc l'A/B se joue sans perdre la scène ni la
fenêtre. Mesure sur `widget rafale` (les 6 cases dans un seul cycle), tirs à **1 cycle** retenus :

| `draw_lines` | bandes | **flush/cycle** | px/cycle | **plus grande aire** | copie µs/f | ms/cycle |
|---:|---|---:|---:|---:|---:|---:|
| **128** *(réf. §0)* | off | **6,0** | 210 600 | 35 100 | 2 927 | 87,6 |
| **128** | **on** | **6,0** | 224 640 | **61 440** = `480 × 128` | 2 963 | ~93 |
| **160** | off | **6,0** | 210 600 | 35 100 | 2 927 | 87,6 |
| **160** | **on** | 🔴 **3,0** | 224 640 | **74 880** = `480 × 156` | 6 762 | **59,3** |

🔴 **LA PRÉDICTION EST EXACTE AU PIXEL.** À `draw_lines = 128 < 156`, la plus grande aire mesurée
vaut **61 440 px = 480 × 128, c'est-à-dire le draw buffer lui-même** : chaque bande est **scindée en
deux passes**, le compte de flushes ne bouge pas, et il ne reste que **+6,67 % de pixels**
(224 640 / 210 600 = 1,0667). **Le levier est alors strictement PIRE.**

✅ **À `draw_lines = 160 ≥ 156`, la bande tient en UNE passe** (plus grande aire = **74 880 px =
480 × 156**, exactement une ligne de la grille) et le levier **tombe** :
**6 → 3 flushes (−50 %)**, **87,6 → 59,3 ms/cycle (−32 %)**, pour **+6,67 % de pixels**.

🔴 **ET IL COÛTE** : le draw buffer passe de **122 880 à 153 600 o de RAM interne DMA**, et la RAM
interne libre tombe de **104 311 à 71 527 o (−32 784 o)**. Il reste au-dessus de la réserve DMA
(32 768 o) et de `DN_BUDGET_MARGE_O` (48 KiB = 49 152 o), **mais la marge se resserre nettement**.

⇒ **CHIFFRÉ ET LAISSÉ NON ADOPTÉ, DÉLIBÉRÉMENT.** `draw_lines = 128` appartient à la **§0**, que le
périmètre de dn3-2 interdit explicitement de changer. La configuration de référence a été
**restaurée immédiatement** après la mesure (`cfg` re-relu : `draw_lines=128`). ⇒ **C'est dn3-3 ou
dn4-1 qui tranche**, avec ces chiffres en main et la condition écrite : **le levier n'existe que si
`draw_lines >= DN_UI_CASE_H`.**

⚠️ **Et il interagit avec la géométrie** : si une future story change `DN_UI_CASE_H`, la condition
change avec elle. Les deux nombres doivent être lus **ensemble**, jamais l'un sans l'autre.

### 16.8 Ce que cette section N'A PAS mesuré

- ⛔ **L'option n°2 du ledger** (« ne pas invalider le fond à la transition ») — **déclarée NON
  ESSAYÉE**, avec son motif : elle porte sur le coût d'une **transition** (`build_scene`), pas sur
  le coût d'une **mise à jour**, et la latence de transition **régresse déjà de +27,3 ms** dans
  cette story pour une raison connue et suffisante (six widgets construits au lieu de trois widgets
  + trois cases nues). L'essayer ici mélangerait deux causes dans un même chiffre. ⚠️ Elle reste
  **entière** pour dn4-1, où le budget < 300 ms se solde.
- ⚠️ Les constats **à l'œil** (image stable, aucune bande discernable, six valeurs vivantes) sont
  des **gestes owner** : aucun chiffre de cette section ne les remplace. *« Un fps vert ne prouve
  PAS qu'il y a une image. »*

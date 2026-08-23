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
| **`bounce_px`** | **7 680 px (16 lignes)** ⬅️ *change le 2026-08-16 (0 → 4 800), puis le **2026-08-19** (4 800 → **7 680**, `dn4-6`, §18.9 — 4 800 est l'état qui GLISSE sous trafic USB + repeint). ⚠️ Cette ligne est restée à 4 800 jusqu'à la revue de code du 2026-08-19, dans le tableau qui **fait autorité** — et ~8 autres sites de ce fichier récitent encore `bounce_px=4800` dans des relevés HISTORIQUES, ce qui est correct **pour eux** : ils datent d'avant. ⛔ Ne les corriger nulle part ailleurs qu'ici sans changer aussi le SHA du relevé.* | la DMA du panneau lit désormais un tampon en **RAM interne** au lieu d'aller chercher la PSRAM : c'est ce qui supprime **à la fois** le défilement sous I²C **et** l'artefact §10.5 (§11.4). Coût : 2 × 9 600 o de RAM interne, **rien au repos** et +1,1 point de CPU en redessin, fps **inchangé** — le vrai prix est **+160 ms de latence** (§11.5) |
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
| 🔴 **`GPIO37, 36, 35, 34, 33` sortis sur le header 2×12 ~~DROIT~~ — 🔴 CORRIGÉ `dn4-2` : sur la **RANGÉE A de l'UNIQUE header 2×12** (voir `…-capteurs-i2c.md` §13.1 bis ; il n'y en a qu'un, constat owner carte en main) — mais « déconseillés — PSRAM interne »** | **Piège pour `dn4-2`** (⚠️ l'entrée disait « dn4-1 » : le correct-course du 2026-08-18 a réassigné le câblage à `dn4-2`) : y câbler un capteur casse la PSRAM, donc **le framebuffer** que la DMA lit à ~23 Mo/s. Le symptôme **ne ressemble pas à un problème de capteur** — image corrompue, plantages erratiques, ou pire, dégradation intermittente — et un diagnostic partirait du mauvais côté, alors que la soudure est **irréversible** | ⚠️ **TOUJOURS HYPOTHÈSE — voir la PARADE ci-dessous (`dn4-2`, 2026-08-19)** |
| **`GPIO4` = lecture de la tension batterie**, « isolable en dessoudant la résistance » | seule broche analogique documentée ; ⚠️ **aucun rapport de pont diviseur donné** ⇒ à mesurer, jamais à supposer | ⚠️ hypothèse |
| **Connecteur `MX1.25 2PIN` pour LiPo 3,7 V** + chargeur **`MP1605GTF-Z` (2 A max)** | voir la décision **D5** ci-dessous | ⚠️ hypothèse |
| **L'interrupteur ON/OFF est un « Battery Power Control Switch »** | 🔴 **Il n'avait jamais été identifié**, alors qu'il est visible sur `docs/cablage/2026-08-16_2228-…`. Sa portée sur l'alimentation USB **n'est pas documentée** ⇒ une carte qui ne démarre pas après qu'on l'a bougé est un diagnostic à connaître AVANT de dérouler la recette « carte muette » | ⚠️ **à établir par la mesure**, et c'est le plus actionnable des cinq |
| **`TCA9554PWR` : « toutes les broches utilisées, non sorties »** | confirme §1.2 : l'expander est entièrement consommé, rien à en tirer pour dn4-1 | ✅ cohérent avec la mesure |

> ✅ **PARADE ÉCRITE AVANT LE FER — `dn4-2`, 2026-08-19 (AC3, Y1). LA PARADE DOMINE LA QUESTION,
> ELLE NE LA RÉFUTE PAS.**
> 🔴 **AMENDÉE LE MÊME JOUR, ET DANS LE MAUVAIS SENS POUR NOUS** : il n'existe **PAS** deux headers
> 2×12. Il y en a **UN**, et ses deux rangées portent les deux groupes — `33..37` en rangée A,
> `SCL`/`SDA` en rangée B, **à 2,54 mm l'une de l'autre** (§13.1 bis de `…-capteurs-i2c.md`,
> sérigraphie relue + **constat owner carte en main**). ⇒ La parade tient (aucune de ces broches
> n'est consommée), **mais le risque de contact accidentel est plus élevé que ce paragraphe ne le
> laissait croire**, et c'est une raison de plus de **laisser l'entrée de ledger OUVERTE**.
> **Le constat** : l'I²C est un **BUS**. Les quatre capteurs (BME680 déjà soudé, plus BH1750, ToF et
> INA219) partagent **`SDA = GPIO15` et `SCL = GPIO7`** (`dn_pins.h:31-32`), plus `3V3` et `GND`.
> ⇒ **Brancher trois capteurs de plus coûte ZÉRO GPIO**, et **aucune broche du header 2×12 n'est
> consommée par cette story.** Les deux points d'accès physiques au bus (embase JST 4 points côté
> interrupteur, **le** header 2×12) n'exposent **aucune** de ces cinq broches : ils portent
> `GND · 3V3 · SDA · SCL` et `SCL · SDA · 3V3 · G`.
> ⚠️ *Ce paragraphe disait « ni à droite, ni à gauche » et « header 2×12 **GAUCHE** » six lignes
> après avoir réfuté l'existence de deux headers — corrigé par la revue de code du 2026-08-20. Le
> vocabulaire GAUCHE/DROIT est celui de la doc constructeur, et c'est précisément celui que le
> constat owner a réfuté : **il n'y en a qu'UN**.*
> ⇒ **`dn4-2` ne peut pas tomber dans ce piège**, et c'est écrit **avant** que le fer ne chauffe.
>
> 🔴 **MAIS L'ENTRÉE DE LEDGER RESTE OUVERTE, ET SON STATUT « HYPOTHÈSE » EST CONSERVÉ.** Une parade
> **n'est pas une réfutation** : personne n'a vérifié à la carte que ces cinq broches sont bien la
> PSRAM interne. *« Un piège non vérifié se re-tend »* — la prochaine story qui voudra une broche
> d'interruption, un bouton ou un capteur non-I²C retombera exactement dessus.
> ⚠️ **Et la source qui l'annonce est celle qui s'est trompée ou contredite QUATRE fois sur quatre
> points vérifiables** (§14.2) : elle ne peut ni fermer l'entrée, ni la disqualifier.
> ⇒ **Ce qui la fermerait** : un `gpio_dump_io_configuration()` au boot, ou un essai de
> `gpio_config()` sur l'une des cinq **avec relevé de `mem`/PSRAM avant-après** — ⛔ hors périmètre
> de `dn4-2`, qui n'utilise aucune de ces broches.

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
  > 🔴 **VERDICT dn3-2 (W4/AC10) : CET ÉCART N'EN ÉTAIT PAS UN — L'AC ÉTAIT MAL POSÉE.** Voir
  > **§16.9**. L'arithmétique la réfute avant tout tir : la cible fait 10 px, l'instrument (une
  > empreinte de doigt) fait 8 à 10 mm, soit **4 à 5 fois plus large**. Aucun geste owner ne pouvait
  > atteindre une gouttière, et en réclamer la preuve était demander à un instrument de mesurer
  > plus fin que lui-même. **L'exigence est RETIRÉE, pas reconduite.**

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

🔴 **LE FIRMWARE N'EST PAS LE MÊME POUR TOUTE LA SECTION — corrigé en revue de code le 2026-08-18.**
Cet en-tête annonçait « **Firmware `ea986ed`** » pour §16.0 à §16.8, ce qui est **impossible** :
`widget bandes`, l'instrument de §16.7, **n'existe qu'à partir de `ca17ad9`**. Chaque sous-section
porte donc désormais **le SHA sur lequel elle a réellement été relevée** :

| sous-section | firmware du relevé | pourquoi |
|---|---|---|
| §16.0 à §16.4 (décomposition, coût par mise à jour) | **`ea986ed`** | le correctif de `cpu brut` est ce commit |
| §16.5 / §16.5 bis / §16.5 ter (la barre) | **`421801d`** | §16.5 bis EST le correctif de ce commit |
| §16.6 (non-régression) | **`ea986ed`** ⚠️ **voir l'écart déclaré ci-dessous** | relevé avant trois commits de code |
| §16.7 (W8, les bandes) | **`ca17ad9`** | `widget bandes` naît là |

⚠️ **ÉCART DÉCLARÉ — LA TABLE DE §16.6 NE DÉCRIT PAS LE FIRMWARE LIVRÉ.** Après `ea986ed` sont
arrivés **`ca17ad9`** (le callback `LV_EVENT_INVALIDATE_AREA`, enregistré en permanence),
**`421801d`** (le correctif de la barre) et **`49a8364`** (le correctif du témoin anti-fantôme, qui
touche `dn_rtc.c/.h` et `dn_console.c`). Les colonnes **RAM interne libre, tas LVGL, boot, fps et
latence** de §16.6 sont donc celles de `ea986ed`, **pas** celles de `8f9148a`. **Le binaire, lui, a
été re-relevé** (voir la table). Re-relever le reste demande une séance carte : **porté au ledger,
pas fabriqué ici.** ⛔ Règle du dépôt : *« jamais fabriquer une mesure pour satisfaire une
cohérence. »*

Géométrie **inchangée** (W4 tranché « exigence retirée ») ⇒ **l'unité de
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
verrou LVGL**, donc dans un seul cycle. Son témoin de validité est **`cycles pour dessiner la
rafale == 1`** — deux ou plus signifient que les poussées n'ont pas fusionné et que le chiffre ne
vaut rien ; **zéro** signifie qu'aucun cycle n'a été observé dans le délai, donc une **non-mesure**.
🔴 ⚠️ **CETTE PHRASE DISAIT `== 0` JUSQU'À LA SÉANCE DU 2026-08-18**, comme la console, `dn_ui.h`,
AC7 et le README. C'était l'**ancienne sémantique** : le témoin était alors échantillonné **sous**
le verrou, où le compteur ne peut pas bouger ⇒ il valait 0 par construction et la branche
« coupée » était **inatteignable**. La revue de dn3-2 a corrigé la **mesure** — aucun des cinq
textes qui l'interprètent n'a suivi. ⇒ **l'instrument criait « rejouer » sur une mesure parfaite.**
Découvert à la **première lecture réelle du témoin**, en séance.

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

⚠️ **Colonne dn3-2 = `ea986ed`, SAUF le binaire, re-relevé sur le firmware livré.** Voir l'écart
déclaré en tête de §16.

| Mesure | `a64d4c3` (dn3-1) | dn3-2 | Δ |
|---|---:|---:|---|
| Binaire `desknode.bin` **@ `ea986ed`** | 886 608 o | 903 344 o | +16 736 o |
| 🔴 Binaire `desknode.bin` **@ `8f9148a` (LIVRÉ)** | 886 608 o | **904 768 o** | **+18 160 o** · partition libre à **78 %** |
| 🔴 Binaire **@ post-revue de code** | 886 608 o | **908 944 o** | **+22 336 o** · partition libre à **78 %** |
| RAM interne libre | 108 435 o | **104 311 o** | **−4 124 o** = la pile 4 096 o de `dn_rtc` + son `.bss` |
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

### 16.9 🔴 W4/AC10 — LA GOUTTIÈRE : L'EXIGENCE EST **RETIRÉE**, ET C'EST L'ARITHMÉTIQUE QUI TRANCHE

**La géométrie qui FAIT FOI à partir de dn3-2** (inchangée depuis dn3-1, et c'est le point) :

| grandeur | valeur | commentaire |
|---|---:|---|
| Case | **225 × 156 px** | `DN_UI_CASE_W` / `DN_UI_CASE_H` = **35 100 px**, l'unité de tous les chiffres d'AC8 |
| Marge extérieure | 10 px | |
| Gouttière entre cases | **10 px** | la « zone morte » que dn3-1 cherchait à prouver |
| Plus large bande de fond du dashboard | **12 px** | le meilleur cas possible pour un tir |
| Grille | 2 × 3, à partir de `y = 80` | sous la barre heure/date (70 px) |

🔴 **POURQUOI L'EXIGENCE EST RETIRÉE, ET NON REPORTÉE.** L'empreinte d'un doigt sur une dalle
capacitive fait **8 à 10 mm**. À 480 px pour ~57,6 mm de largeur utile, cela représente **67 à
83 px** de contact. La cible la plus large disponible fait **12 px**.

> **La cible est 4 à 5 fois plus petite que l'instrument** — et encore, en comparant sa largeur à
> celle de l'empreinte, pas à sa surface.

⇒ Aucun geste owner ne peut atteindre une gouttière **par construction**. L'AC de dn3-1 n'était donc
pas « non tenue » : elle était **MAL POSÉE**. Elle demandait à un doigt de mesurer plus fin que
lui-même, et le tir manqué (4-5 px dans la case CPU) en est la démonstration, pas l'échec.

✅ **CE QUI EST PROUVÉ À LA PLACE, ET QUI VAUT MIEUX** : « toute la case est la zone tactile » tient
**jusqu'à 4 px du bord** (dn3-1), et **à six cases, jauges comprises** (dn3-2, 124 appuis / 48 taps).
C'est la propriété que l'owner ressent ; la gouttière était une propriété que personne ne peut
toucher.

🔴 **CONSÉQUENCE CHIFFRÉE DE NE PAS ÉLARGIR — et c'est la raison de fond.** Élargir la gouttière
change `DN_UI_CASE_W/H`, donc **l'unité de 35 100 px**, donc **la comparabilité de TOUS les chiffres
d'AC8 de dn3-1**. La géométrie serait à re-mesurer entièrement dans le nouveau firmware, pas
héritée. On échangeait un legs chiffré complet contre une exigence qu'aucun doigt ne peut vérifier.

### 16.8 Ce que cette section N'A PAS mesuré

- ⛔ **L'option n°2 du ledger** (« ne pas invalider le fond à la transition ») — **déclarée NON
  ESSAYÉE**, avec son motif : elle porte sur le coût d'une **transition** (`build_scene`), pas sur
  le coût d'une **mise à jour**, et la latence de transition **régresse déjà de +27,3 ms** dans
  cette story pour une raison connue et suffisante (six widgets construits au lieu de trois widgets
  + trois cases nues). L'essayer ici mélangerait deux causes dans un même chiffre.
  🔴 **CORRIGÉ LE 2026-08-18 (dn4-1)** : cette ligne écrivait « elle reste **entière** pour dn4-1,
  où le budget < 300 ms se solde ». **C'EST FAUX DEPUIS LE CORRECT-COURSE DU 2026-08-18**, qui a
  redécoupé l'epic dn4 en cinq marches et **réassigné l'option n°2 ET le budget < 300 ms à
  `dn4-4`** (la page de détail avec sa courbe). `dn4-1` porte les **données PC réelles** ; elle
  n'a **pas** touché à `build_scene()`. ⛔ **Ne pas la ramener dans dn4-1** — et ⛔ ne pas
  l'échanger avec W8 (§16.7) : *« W8 n'a jamais été mesuré sur une transition, et l'option n°2
  jamais sur une mise à jour. Les échanger serait une faute de lecture. »*
- ⚠️ Les constats **à l'œil** (image stable, aucune bande discernable, six valeurs vivantes) sont
  des **gestes owner** : aucun chiffre de cette section ne les remplace. *« Un fps vert ne prouve
  PAS qu'il y a une image. »*

---

## 17. LE BUDGET SOUS DONNÉES PC RÉELLES — mesuré le 2026-08-18 (dn4-1, P9.1)

> 🔴 **AVERTISSEMENT DE LECTURE, ET IL VAUT POUR TOUTE LA §16 QUI PRÉCÈDE** : à partir de
> dn4-1, **l'index 4 n'est plus `VENTILOS` mais `DISQUE`** (décision owner D8 du 2026-08-18 :
> les RPM boîtier exigent le Ring0, qui sort du périmètre V1).
> 🔴 **ANNOTÉ LE 2026-08-21 (dn4-8 / D13), ⛔ PAS RÉÉCRIT** : **le Ring0 est REVENU** dans le
> périmètre V1, **par service tiers** (`LibreHardwareMonitor` en service permanent ; ⛔ l'agent
> ne fait aucun Ring0 lui-même). ⇒ **les RPM boîtier et CPU sont sur le fil depuis `dn4-8`.**
> ⛔ **MAIS L'INDEX 4 RESTE `DISQUE`, ET CE N'EST PAS UN OUBLI** : D13 est explicite —
> *« D8 est amendée sur sa PORTÉE Ring0, ⛔ PAS sur son choix de case »*. La case n'est **pas**
> rendue aux ventilateurs : les `tr/min` **s'y AJOUTENT** (`disk` porte quatre grandeurs).
> ⇒ **la consigne de lecture ci-dessous ne change pas d'un iota.**
> ⛔ **Les mentions de
> `VENTILOS` en §15 et §16 NE SONT PAS RÉÉCRITES** : ce sont des relevés historiques, et
> l'histoire d'un dépôt ne se falsifie pas. Lire « VENTILOS » comme « la case d'index 4 »
> partout où un chiffre y est attaché — la géométrie (225 × 156, 35 100 px) et la position
> n'ont pas bougé, donc les chiffres restent comparables.
> ⚠️ Ce qui a changé sur cette case : son **libellé**, son **icône** (la disquette `save`
> U+F0C7, gratuite — déjà dans les deux `.c`), son **unité** (tr/min → Mo/s) et sa **jauge**
> (elle en avait une, elle n'en a plus : un débit n'a pas de plein, même motif que RÉSEAU).

### 17.0 🔴 Le firmware sur lequel ces chiffres sont pris

> 🔴 **CETTE PHRASE ÉTAIT FAUSSE ET ELLE EST CORRIGÉE (revue 2026-08-19).** Elle disait
> « Tous les relevés de cette section sont pris sur le MÊME firmware et dans la MÊME session » —
> c'est très exactement le **SHA global qui ment sur trois lignes** qu'AC13 interdit.
> **§17 couvre désormais TROIS firmwares**, et chaque sous-section nomme le sien :

| Sous-section | Firmware | Séance |
|---|---|---|
| §17.1 (T0) | `395310e` | dev dn4-1 |
| §17.2 · §17.4 · §17.5 · §17.6 | `21d02be` | dev dn4-1 |
| §17.9 | `d5d3539` | séance post-revue du 2026-08-18 |

> ⚠️ **§17.4 et §17.5 ne nomment toujours aucun SHA dans leur propre en-tête** — ils sont pris
> dans la session `21d02be` d'après leur position, mais ce n'est pas ÉCRIT là où on les lit.
> ⏳ **Rattaché au ledger** (revue 2026-08-19) : à qualifier explicitement, ou à re-relever.

Conditions communes à tous les relevés : `draw_lines = 128` restauré, mock **coupé** sauf
mention contraire.
⚠️ **Et T0 a commencé par corriger un écart** : la carte tournait sur `49a8364`, **deux commits
avant** le firmware que dn3-2 déclarait livré. Les budgets de §16.6 ont donc été **re-relevés
sur `395310e`** avant tout changement — c'est la baseline T0 ci-dessous.

### 17.1 T0 — §16.1 et §16.6 re-relevées sur `395310e`, avant de toucher au code

| Grandeur | §16.6 (mesurée à `ea986ed`) | **T0 re-relevé (`395310e`)** | écart |
|---|---:|---:|---:|
| Binaire `desknode.bin` | 908 944 o | **908 944 o** | 0 |
| RAM interne libre | 104 311 o | **104 287 o** | −24 o |
| PSRAM libre | 7 768 236 o | **7 768 236 o** | **0** |
| Tas LVGL utilisé | 20 108 o (33 %) | **20 144 o (33 %)** | +36 o |
| Plus gros bloc libre | 41 304 o | **41 308 o** | +4 o |
| Tas sur 40 transitions | +24 o | **+20 o** | PLAT |
| `fps 15` | 37,40 Hz | **37,40 Hz** | 0 |
| Boot « prêt en N ms » | 2 287 ms | **2 288 ms** | +1 ms |
| Latence transition (n=40) | 349,1 (293,2 / 452,3) | **347,1 (285,7 / 401,0)** | −2,0 ms |

⇒ **Les trois commits de fin de dn3-2 ont coûté 24 octets de RAM interne et rien d'autre.**
L'écart déclaré par dn3-2 était donc réel mais **sans conséquence chiffrable** — c'est une
information, et elle valait la peine d'être relevée plutôt que supposée.

**§16.1 re-jouée à T0**, protocole identique (stabilisation 3 s, `flush reset`, `cpu brut`
avant/après une écoute passive de 45 s) :

| ligne §16.1 | CPU | `taskLVGL` | cycles/s | flush/cyc | px/cyc | duty |
|---|---:|---:|---:|---:|---:|---:|
| `mock off / groupage on` (§16.1) | 1,49 % | 1,00 pt | 0,22 | 1,10 | 32 342 | 0,4 % |
| **`mock off / groupage on` (T0)** | **1,55 %** | **1,06 pt** | **0,22** | **1,00** | **32 023** | **0,5 %** |
| `mock on / groupage on` (§16.1) | 10,18 % | 9,64 pt | 1,21 | 3,47 | 120 756 | 6,7 % |
| **`mock on / groupage on` (T0)** | **10,27 %** | **9,72 pt** | **1,21** | **3,50** | **120 694** | **6,3 %** |

⇒ **§16.1 est reproductible à ≤ 1 % près.** C'est ce qui autorise à s'en servir de baseline.

### 17.2 🔴 LES TROIS RÉGIMES, MÊME FIRMWARE (`21d02be`), MÊME SESSION (AC7)

> ⚠️ **CES RELEVÉS PORTENT SUR `21d02be`, PAS SUR LE FIRMWARE LIVRÉ `2d97850`.**
> Relevé en revue de code le 2026-08-18. `2d97850` (séance carte) modifie **cinq fichiers de
> firmware** — `dn_ui.c` +45, `dn_widget.c` +26, `dn_console.c` +32, `dn_ui.h` +4,
> `dn_widget.h` +9 — dont le passage de **`RÉSEAU` à deux grandeurs** et la suppression de sa
> secondaire duplex. ⛔ **AC12 interdit nommément de mesurer trois commits avant le livré**
> (« c'est l'écart déclaré de dn3-2 ») : l'écart est donc **DÉCLARÉ ICI**, et le re-relevé sur
> `2d97850` est une **tâche de séance carte ouverte** (décision owner du 2026-08-18).
> ⚠️ Le régime **(c) `widget rafale`** est en outre **publié incomplet** (8 colonnes sur 12
> valent « — ») et son **témoin de validité n'a jamais été relevé** —
> AC7 exigeait les deux. Même tâche de séance.
>
> 🔴 **CETTE TABLE EST REMPLACÉE PAR §17.9 — LIRE §17.9 AVANT DE CITER UN CHIFFRE D'ICI**
> (renvoi ajouté par la revue du 2026-08-19 ; il manquait, et cette table est celle que citent
> les Completion Notes de la story). Trois choses que §17.9 établit et que cette table ignore :
> 1. sa **colonne par tâche ne se réconcilie pas** avec sa propre colonne globale (facteur ~2) —
>    voir §17.9, et ⚠️ **la cause en est INCONNUE**, pas celle qui avait été publiée ;
> 2. sa **ligne (c) est remplacée** : 140 400 px/cyc y devient **210 600** sur `d5d3539` ;
> 3. ses colonnes `ms/cyc` et `duty` **ne se comparent pas** à celles de §17.9 — la définition
>    a changé (voir §17.9, régime (a)).
> ⛔ **Elle n'est pas effacée** — AC13 l'exige — mais elle ne fait plus autorité seule.

Instrument : **`flush` + `cpu brut` uniquement**. ⛔ `cpu N` est interdit — il **bloque** la
tâche du REPL, et **sur la branche A le REPL EST le transport** : il décrirait le dashboard au
repos quel que soit le trafic.

| régime | CPU | `taskLVGL` | `console_repl` | `dn_link` | cyc/s | flush/cyc | **flush/s** | px/cyc | plus gr. aire | ms/cyc | duty |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **(a) repos, agent arrêté** | **1,62 %** | 1,11 pt | ~0 | ~0 | 0,22 | 1,00 | 0,22 | 31 998 | 35 100 | 22,1 | **0,5 %** |
| **(d) mock ON — §16.1 rejouée ICI** | **10,51 %** | 9,92 pt | ~0 | ~0 | 1,24 | 3,40 | 4,26 | **120 418** | 35 100 | 56,1 | **7,0 %** |
| **(b) RÉGIME RÉEL, 5 métriques 1 Hz** | **13,09 %** | 11,00 pt | **1,27 pt** | **0,24 pt** | 2,05 | 2,52 | **5,17** | 87 982 | 35 100 | 40,3 | **8,3 %** |
| (c) `widget rafale` (cas provoqué) | — | — | — | — | — | 4,00 | — | **140 400** | 35 100 | — | — |

🔴 **LA LIGNE (d) EST LE POINT LE PLUS IMPORTANT DE CETTE SECTION** : `mock on` rejoué sur le
firmware dn4-1 rend **120 418 px/cycle** contre **120 756** en §16.1 — soit **−0,3 %**, alors
que `CPU` et `GPU` portent désormais **deux labels au lieu d'un**.
⇒ **La prédiction falsifiable d'AC7 est CONFIRMÉE : en mode groupé, les grandeurs
supplémentaires sont GRATUITES en pixels**, parce que l'invalidation porte sur le **conteneur**
(225 × 156) et pas sur les enfants. ⚠️ En mode **fin**, ce serait +1 flush par grandeur — le
firmware sait jouer les deux branches (`widget groupe on|off`).

🔴 **L'ÉCART `cycles/s` A UNE CAUSE MÉCANIQUE, ET ELLE EST DANS LE CODE** (trouvée en revue
le 2026-08-18, après coup). `2,05 cyc/s` contre `~1,2` prédit, et `2,52 flush/cyc` au lieu de
4,4 : c'est la signature de **cinq poussées réparties sur ~2 cycles**, pas d'un cycle unique.
En cause : `dn_ui_pc_maj()` prend **et rend** le verrou LVGL **à chaque métrique**, donc la
boucle « groupée » de `dn_link.c` produit **cinq verrous**, pas un — et entre deux, la tâche
LVGL (priorité supérieure) reprend le mutex et rend un cycle complet.
⇒ **« Groupé » signifiait « dans le même RÉVEIL de `dn_link` », jamais « dans le même cycle
LVGL »** — ce que `dn_link.h` affirmait pourtant, et qui est corrigé depuis.
⚠️ **Ces chiffres restent VALIDES** : c'est bien le régime que le produit produit. Ce qui était
faux, c'est sa description. ⛔ Le « vrai » groupage (les cinq sous UN verrou) est **NON ADOPTÉ**
et renvoyé à `dn4-4` avec son A/B — il allongerait la fenêtre bloquante, donc **le PIC**, ce que
W4 cherchait précisément à réduire. (Décision owner du 2026-08-18.)

**Confrontation à la prédiction, écrite AVANT la mesure** (~4,4 flush/cyc, ~151 000 px/cyc,
CPU ~11,0 %, cyc/s ~1,2) :

| | prédit | mesuré | verdict |
|---|---:|---:|---|
| **travail total** (flush/s) | 5,3 | **5,17** | ✅ **−2,5 %, la prédiction tient** |
| cycles/s | ~1,2 | **2,05** | 🔴 **×1,7 — la prédiction l'avait nommé comme NON couvert** |
| flush/cycle | 4,4 | 2,52 | conséquence directe du point ci-dessus |
| px/cycle | ~151 000 | 87 982 | idem |
| CPU | ~11,0 % | **13,09 %** | +2,1 pt, **attribué** ⤵ |
| plus grande aire | 35 100 | **35 100** | ✅ |

**L'écart de CPU est ATTRIBUÉ, pas constaté** : `console_repl` pèse **1,27 pt** — l'écho que le
REPL ré-imprime pour 5 lignes/s. La prédiction avait explicitement laissé ce poste non chiffré.
⚠️ **Et ce n'est pas un artefact de mesure** : sur la branche A, **le REPL EST le transport**.
L'agent réel produit exactement les mêmes 5 lignes/s. Ce 1,27 pt est un **coût réel du transport
retenu**, à porter au budget.
🔴 ⚠️ **CE CHIFFRE DE BUDGET EST CONTREDIT PAR §17.9, ET LES DEUX SONT EN VIGUEUR**
(revue 2026-08-19). §17.9 mesure **2,51 pt** pour le même poste, dans le même régime. C'est le
« facteur ~2 » que §17.9 relève sur toute la colonne par tâche — et ⛔ **sa cause est INCONNUE**,
l'explication d'abord publiée (normalisation machine contre cœur) étant **mécaniquement
impossible** : `cpu brut` n'a qu'un seul dénominateur, mono-cœur, et son code n'a pas changé
entre les deux séances. ⏳ **Tant que la séance carte n'a pas tranché, aucun budget ne se pose
sur ce poste** : ni 1,27 ni 2,51 ne peut être cité seul.
`dn_link` : **0,24 pt** mesuré contre **0,20 pt** prédit (legs dn2-2 × 5) ✅.

### 17.3 🔴 LE DÉFAUT QUE CETTE MESURE A TROUVÉ — deux écrivains sur la même case

**Premier tir du régime réel : 408 flushes.** Or 223 poussées de métrique (compteur de latence
`n`) + 9 d'AMBIANCE en justifiaient **232**. L'écart, **176**, vaut exactement **4 cases × 45 s**.

**Cause** : avec le mock **coupé**, son tick faisait, chaque seconde, pour chaque case mockable :
`if (!s_poussee[i] && regime != ABSENTE) case_poser(ABSENTE)`. Ce test a été écrit quand
GPU/RAM/RÉSEAU/VENTILOS n'avaient **aucune source** — « pas ABSENTE » y voulait dire « le mock
l'a peinte ». dn4-1 leur donne une source : leur régime devient **RÉELLE**, et le tick les
**repeignait en gris une fois par seconde**, juste avant que `dn_link` ne les repose.

- **Symptôme visible** : les quatre cases clignotent « -- » gris à 1 Hz.
- **Symptôme mesuré** : +176 redessins de case sur 45 s, soit **+76 % de flushes**.
- **Correctif** : le tick ne révoque que ce qu'il a lui-même peint (`regime == SIMULEE`).
- **Vérification** : **408 → 234 flushes**, pour 229 poussées + 9 AMBIANCE = 238 attendues ✅.

⚠️ **CE QUI A OUVERT LE DOSSIER N'EST PAS LE DÉFAUT, C'EST LA PRÉDICTION.** Le nombre de
cycles/s avait été nommé d'avance comme *« ce que la prédiction ne couvre pas — s'il monte, tout
se réévalue »*. Il a doublé. Sans cette phrase écrite avant, le chiffre de 408 aurait été publié
comme « le coût du régime réel ».

### 17.4 LEVIER 1 — décorréler les poussées (W4) : **NON ADOPTÉ**, et le motif est mesuré

A/B dans le **même firmware** (`pc pousse groupe|etale`), régime réel 5 métriques à 1 Hz :

| | **GROUPÉE** (défaut) | **ÉTALÉE** |
|---|---:|---:|
| CPU | 12,85 % | 11,76 % |
| `taskLVGL` | 10,75 pt | 9,61 pt |
| cycles/s | 2,54 | 4,21 |
| **flush/cycle — LE PIC** | **1,94** | **1,00** |
| **px/cycle — LE PIC** | **67 951** | **34 942** (**−49 %**) |
| flush/s (travail total) | 5,20 | 4,21 |
| ms/cycle | 31,2 | 16,2 |
| duty | 7,9 % | 6,8 % |
| trames reçues | 228 | 226 |
| **poussées atteignant l'écran** | **228 / 228** | 🔴 **185 / 226** |
| **latence moy / max** | 221 / 301 ms | 🔴 **574 / 1204 ms** |

🔴 **UNE PRÉMISSE ÉCRITE D'AVANCE EST DÉMENTIE PAR LA MESURE.** Le contrat annonçait *« ça ne
réduit pas le travail total, ça réduit le pic »*. **Le travail total baisse** (5,20 → 4,21
flush/s) — **parce que l'étalé JETTE des mises à jour**. Le mécanisme est arithmétique et il
était prévisible : **4 réveils/s pour 5 métriques/s**. Une métrique sur cinq n'a pas de tour.

⇒ **NON ADOPTÉ.** Il divise le pic par ~1,94 et économise 1,1 pt de CPU, mais **19 % des valeurs
mesurées par la tour n'atteignent jamais l'écran**, et la latence maximale est **multipliée par
4**. Pour un module dont tout le propos est l'honnêteté de l'affichage, c'est disqualifiant.
⚠️ Le levier **reste dans le firmware** (`pc pousse etale`) : c'est l'autre branche de l'A/B, et
elle doit rester vivante pour que ce verdict soit rejouable.

### 17.5 LEVIER 2 — W8, le repeint en bandes : **NON ADOPTÉ**, et à 160 aussi

Les **deux nombres lus ensemble**, comme la méthodologie l'exige — sur le **régime réel**, pas
sur la rafale de §16.7 :

| | `draw_lines=128` OFF | `draw_lines=128` **ON** | `draw_lines=160` OFF | `draw_lines=160` **ON** |
|---|---:|---:|---:|---:|
| CPU | 13,22 % | 🔴 **21,08 %** | 12,99 % | 🔴 **18,44 %** |
| `taskLVGL` | 11,15 pt | 18,89 pt | 10,93 pt | 16,35 pt |
| cycles/s | 2,29 | 3,58 | 2,23 | 2,23 |
| flush/cycle | 2,27 | 2,49 | 2,31 | **1,88** |
| **flush/s** | 5,20 | 8,91 | 5,14 | **4,19** (−18 %) |
| px/cycle | 79 513 | 93 070 | 81 104 | **140 546** (+73 %) |
| **plus grande aire** | 35 100 | 🔴 **61 440** | 35 100 | 🔴 **74 880** |
| copie µs/flush | 2 912 | 2 967 | 2 925 | **6 865** (×2,3) |
| duty | 8,1 % | 12,2 % | 8,1 % | **7,8 %** |
| latence moy/max | 87 / 242 ms | 176 / 399 ms | 179 / 221 ms | 239 / 363 ms |
| **RAM interne libre** | 102 943 o | — | **71 335 o** | — |

🔴 **LES DEUX SIGNATURES PRÉDITES APPARAISSENT, ET ELLES DISENT CE QU'ELLES DEVAIENT DIRE** :
`plus grande aire = 61 440` à `draw_lines=128` (**le draw buffer scinde** — 480 × 128) et
`74 880` à 160 (**les bandes sont actives** — 480 × 156). La prédiction les avait nommées comme
les deux valeurs à surveiller.

- **À 128, le levier est STRICTEMENT PIRE** : +7,9 pt de CPU, +71 % de flushes. Conforme à
  l'avertissement de §16.7 — et maintenant **mesuré sur le régime réel**, pas déduit.
- **À 160, il gagne où §16.7 l'annonçait** (−18 % de flushes, duty 8,1 → 7,8 %) **et il perd
  ailleurs, beaucoup plus fort** : **+5,45 pt de CPU**, **+73 % de pixels**, copie **×2,3**.
  Le mécanisme est le même qu'en §16.2 : on supprime de l'attente vsync (dormir ne coûte rien)
  et on ajoute du rendu et de la copie. **Un module H24 se budgète sur la CHARGE.**
- **Le prix en RAM est MESURÉ à 31 608 o** (102 943 → 71 335), et **non 32 784** comme §16.7
  l'annonçait — écart de 1 176 o, déclaré.

⇒ **NON ADOPTÉ**, et le motif validé par l'owner s'applique : *« on ne tranche qu'après la
mesure ; s'il n'y a pas de gêne mesurée et vue, on ne paie pas les 32 Ko. »* Il n'y a **pas** de
gêne : duty 8,1 %, `fps` à 37,40 Hz, plus grande aire à 35 100 px. **`draw_lines` reste à 128 et
la §0 ne bouge pas.**

### 17.6 Non-régression — table avant/après, **sur le firmware LIVRÉ**

| Grandeur | T0 (`395310e`) | **`21d02be`** ⚠️ | écart |
|---|---:|---:|---:|
| Binaire `desknode.bin` | 908 944 o | **914 048 o** | **+5 104 o** (partition libre à 78 %) |
| RAM interne libre | 104 287 o | **104 087 o** | **−200 o** |
| PSRAM libre | 7 768 236 o | **7 768 236 o** | **0** |
| Tas LVGL utilisé | 20 144 o (33 %) | **20 292 o (33 %)** | +148 o |
| Plus gros bloc libre | 41 308 o | **41 112 o** | −196 o (**98,4 % du libre**, inchangé) |
| Fragmentation | 2 % | **2 %** | 0 |
| Tas sur 40 transitions | +20 o | **−20 o** | **PLAT** ✅ |
| `fps 15` | 37,40 Hz | **37,40 Hz** | **0** ✅ |
| Boot « prêt en N ms » | 2 288 ms | **2 297 ms** | +9 ms (bruit) |
| Latence transition (n=40) | 347,1 (285,7 / 401,0) | **335,0 (291,3 / 397,1)** | **−12,1 ms** |
| `dn_capteurs` | 5 000 ms, 0 erreur | **5 000 ms, 0 erreur** | ✅ |

⚠️ **La latence de transition ne RÉGRESSE PAS**, alors que la story l'avait annoncée comme
pouvant régresser (deux grandeurs de plus à construire). Elle **s'améliore de 12,1 ms**.
⛔ **Elle ne se solde pas ici** : le budget < 300 ms appartient à `dn4-4`.

### 17.7 🔴 Deux défauts d'INSTRUMENT rencontrés, et ce qu'ils coûtaient

1. **La table de `cpu brut` sort TRONQUÉE** juste après une session d'écriture soutenue sur le
   REPL : les lignes `IDLE0`/`IDLE1`/`taskLVGL` manquent, seul `total` survit. Vu **deux fois**.
   ⇒ Un parseur permissif aurait divisé par un idle partiel et rendu **un chiffre faux qui
   ressemble à un succès**. Le harnais de dn4-1 **refuse** une table amputée et retente.
   ⚠️ **Le même symptôme touche `pc`** : un bloc de 5 lignes contiguës a disparu d'un relevé.
2. **L'ÉCHO N'EST PAS UN INSTRUMENT DE LONGUEUR DE LIGNE.** Pour mesurer ce que le REPL délivre
   au parseur, l'écho rendait « intact » jusqu'à **127** caractères — parce que linenoise renvoie
   les octets **à mesure qu'ils arrivent**, donc **avant** le plafond du tampon. L'instrument
   valide est le firmware lui-même (`pc $<...>` sans virgule ré-imprime `argv[1]`) : la vraie
   limite est **124 caractères de trame** (127 pour la ligne entière, « pc » compris).
   ⇒ La bande « ligne trop longue » est **64..124**, large de 61 octets, donc **atteignable** —
   ce qui est la condition pour que `rejets_trop_longue` ne soit pas un compteur décoratif.

### 17.8 Séance carte du 2026-08-18 — ce que l'œil a ajouté, et ce qu'il a corrigé

**Les constats owner et le détail des mesures de liaison sont en `…-liaison-pc.md` §13.11.**
Ce qui touche l'AFFICHAGE, et seulement lui :

- ✅ **Le clignotement gris est confirmé RÉPARÉ À L'ŒIL.** §17.3 l'avait trouvé par la mesure
  (408 flushes pour 232 justifiées) et corrigé ; l'owner confirme *« pas de clignotement »* sous
  agent réel. ⚠️ **Le chiffre seul ne suffisait pas** : un flush de moins ne dit pas qu'un
  scintillement a disparu de la dalle.
- ✅ **Image STABLE sous trafic 1 Hz réel** (*« nickel »*) — pas de déchirement, pas de bande.
- ✅ **Zéro badge « SIMULÉ »** en régime nominal, **vu**, pas seulement relu de `widget`.
- ✅ **Deux grandeurs empilées : PRÉFÉRÉES** (*« oui, mieux »*). ⚠️ L'écart avec la maquette de
  l'addendum §1 (qui les écrit sur UNE ligne) n'est donc plus seulement **assumé** — il est
  **arbitré dans l'autre sens par l'owner, sur la dalle**.
- ✅ **Le différenciateur du brief, VU** : agent arrêté, **5 cases à « -- » et AMBIANCE seule
  vivante**.

**Deux changements de rendu demandés par l'owner EN SÉANCE, et appliqués :**

1. **`RÉSEAU` passe à DEUX GRANDEURS EMPILÉES**, avec ↓ et ↑ comme icônes de grandeur
   (`LV_SYMBOL_DOWN`/`UP`, U+F078/U+F077 — ⛔ **pas** U+2193/U+2191, hors latin-1, qui seraient
   dessinées EN SILENCE). ⚠️ La ligne secondaire duplex disparaît : la garder afficherait **les
   mêmes deux nombres deux fois dans le même rectangle**.
   ✅ **Aucune borne touchée** : c'est le mécanisme `n_grandeurs` d'AMBIANCE, tel quel.
2. **La PISTE de la jauge** (le fond, la part non remplie) passe de `0x203040` à **`0x5A5F6A`**,
   et devient **réglable à chaud** (`widget piste <0xRRGGBB>`) — patron de `opa`/`voile`/`icone` :
   *un A/B qui exigerait trois reflashs coûterait trois observations à l'owner*.
   ⚠️ **Constat owner d'origine** : *« la barre de vide apparaît en vert »*. **Le code n'a JAMAIS
   posé de vert** — `0x203040` est un bleu-gris FONCÉ. Ce qui se voyait est le **PCB vert du fond
   par contraste simultané**. ⛔ On n'a donc pas « corrigé » une couleur qu'on n'avait pas posée :
   on a éclairci la piste pour que le violet tranche, et l'œil a arbitré (*« la barre ressort
   bien »*).
   ⛔ **CE N'EST PAS LA PASSE DE PALETTE** : `dn3-3` refait l'identité visuelle et rejouera cet
   arbitrage. Exception ciblée, demandée explicitement par l'owner en séance.

⚠️ **Le tactile a demandé TROIS tours, et le motif est un enseignement d'affichage** : la jauge de
`RAM` est haute de **10 px**, et quand la case est à « -- » **elle est vide, donc quasi
invisible**. Les deux premiers tours (31 appuis) n'ont jamais atteint la bande. Il a fallu **armer
le mock** pour que la barre se remplisse avant que la cible devienne visible — et alors deux
appuis sur 16 y sont tombés, tous deux rendant « TAP sur RAM ». ⇒ *On ne peut pas viser ce qu'on
ne voit pas*, et une campagne tactile sur un élément dont l'état d'affichage varie doit **d'abord
rendre la cible visible**.

---

### 17.9 🔴 Séance carte du 2026-08-18 (2ᵉ) — après la revue de code, sur le firmware `d5d3539`

> **Firmware de cette section : `d5d3539`** — la revue de code de dn4-1 **plus** le correctif du
> témoin de rafale trouvé ici même. ⛔ **Toutes les lignes ci-dessous portent CE SHA**, et lui seul :
> AC13 exige que le tableau nomme le SHA de **chaque** relevé.
> ⚠️ §17.2 et §17.6 restent telles quelles — elles documentent le firmware du **dev** (`21d02be`)
> et l'histoire ne se masque pas. **Cette section les REMPLACE comme référence**, elle ne les efface pas.

**Pourquoi cette session existe** : la revue de code a établi que la table de non-régression avait
été relevée sur le firmware du **dev**, alors que le livré était celui de la **séance**, et
qu'AC7 régime (c) n'était publié qu'à 4 colonnes sur 12 avec un témoin **jamais relevé**.

#### 🔴 CE QUE LA PREMIÈRE LECTURE DU TÉMOIN A TROUVÉ

`widget rafale` rendait **1**, quatre rejeux de suite, et la console imprimait
*« la rafale a été COUPÉE, son chiffre NE VAUT RIEN. Rejouer. »* — pendant que `flush`, dans la
**même passe**, disait **6 flushes, 1 CYCLE, 210 600 px**, soit exactement la fusion annoncée.

**La rafale marchait parfaitement. C'est l'étiquette qui mentait.** La revue de dn3-2 avait
corrigé ce que la fonction **mesure** (le témoin était échantillonné *sous* le verrou, donc nul
par construction, branche « coupée » **inatteignable**) ⇒ la valeur de succès est passée de 0 à
**1**. ⛔ **Aucun des cinq textes qui l'interprètent n'avait suivi** : la console, `dn_ui.h`,
`dn_ui.c`, ce fichier, le README — et **AC7 lui-même**.
⚠️ **Le défaut a survécu parce que personne n'avait jamais lu le témoin** — ce que la revue
reprochait précisément à AC7. *Un instrument qu'on ne lit pas ne protège de rien.*

> 🔴 **ÉPILOGUE — LE TÉMOIN A ÉTÉ ENTERRÉ LE 2026-08-19, IL N'A JAMAIS RIEN PU VOIR.**
> La revue du 2026-08-19 a montré que **le correctif ci-dessus n'a pas fermé le défaut, il l'a
> déplacé de `0` à `1`** : la boucle d'attente sort au **PREMIER** incrément de `s_n_cycles`, donc
> le delta vaut **1 quoi qu'il se soit passé** pendant la rafale. Obtenir `2` aurait demandé deux
> cycles complets dans un seul `vTaskDelay(5 ms)` — **impossible** à 26,7 ms/cycle (37,40 Hz).
> ⇒ **Les « quatre rejeux, quatre fois 1 » sont la signature d'un témoin CONSTANT**, pas d'une
> validation. C'était son **troisième** état successif, et aucun n'était discriminant.
> ✅ **Décision owner du 2026-08-19 : le témoin est SUPPRIMÉ** (`dn_ui_rafale_cycles()` retiré du
> firmware), et **la fusion se prouve par `flush`, et par lui seul** — les *« 6 flushes, 1 CYCLE,
> 210 600 px »* ci-dessus, qui sont une **mesure indépendante** et qui, eux, tiennent.
> ✅ Effet de bord voulu : la rafale **ne dort plus** (l'attente de 500 ms bloquait le REPL, donc
> le transport PC, plus longtemps que les cinq commandes « RECONSTRUIT »).

#### AC7 — les régimes, sur le firmware de cette séance

> 🔴 **CETTE TABLE EST REMPLACÉE PAR §17.10 — annotation du 2026-08-19.** §17.10 mesure les
> **trois** régimes sur **UN SEUL** firmware (`b5cd141`), définitions de colonne figées et écrites
> AVANT le premier relevé, et son test de réconciliation passe à **−0,00 pt**.
> Deux de ses résultats portent sur cette section :
> 1. ✅ **La colonne par tâche de §17.9 est CONFIRMÉE** par une mesure indépendante sur un autre
>    firmware (`taskLVGL` 2,20 contre 2,20 en (a) ; 22,56 contre 22,16 en (b)). C'est bien **§17.2
>    qui est l'anomalie** — mais la cause en est une **erreur de dérivation de l'opérateur**, pas
>    une propriété de l'instrument (§17.10 corrige la formulation).
> 2. ✅ **Le régime (c) à 210 600 px EST REPRODUIT** — 6 flushes / 1 cycle / 210 600 px, deux tirs
>    propres sur `b5cd141` avec un settle **garanti** de 3 s. ⚠️ §17.10 avait d'abord publié
>    « 4 / 1 / 140 400 » et conclu que l'extrapolation d'AC8 était démentie : **c'était un artefact
>    de lecture précoce**, réfuté le soir même parce que **l'owner a lu la dalle** et y a vu les
>    **six** cases à jour. ⇒ **§17.9 avait raison, l'extrapolation d'AC8 TIENT**, et c'est **§17.2
>    (4,00 / 140 400) qui reste à qualifier** — même piège probable, non vérifié.
> ⚠️ Ses colonnes `ms/cyc` et `duty` **excluent l'attente de synchro** et ne se comparent donc ni
> à §16.1, ni à §17.1, ni à §17.2, ni à §17.10 — qui publie les **deux termes séparément**.

| régime | CPU | `taskLVGL` | `console_repl` | `dn_link` | cyc/s | flush/cyc | flush/s | px/cyc | plus gr. aire | copie µs/flush | ms/cyc | duty |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **(a) repos, agent arrêté** | **1,61 %** | 2,20 pt | 0,07 pt | 0,02 pt | 0,23 | 1,00 | 0,23 | 32 312 | 35 100 | 2 689 | 2,7 | **0,06 %** |
| **(c) `widget rafale`** | — ⚠️ | — ⚠️ | — ⚠️ | — ⚠️ | — ⚠️ | **6,00** | — ⚠️ | **210 600** | 35 100 | **2 933** (max 2 965) | **17,6** | — ⚠️ |

⚠️ **(a) reproduit la référence SUR QUATRE COLONNES, ET DIVERGE D'UN FACTEUR 8 SUR DEUX** —
constat corrigé le 2026-08-19 ; ce paragraphe concluait « **Aucune dérive** » en n'énumérant
que les colonnes qui concordent.
· ✅ **Concordent** : CPU **1,61 %** contre 1,62 % en §17.2 · cyc/s **0,23** contre 0,22 ·
  flush/cyc **1,00** · plus grande aire **35 100 px**.
· 🔴 **Divergent** : `ms/cyc` **2,7** contre **22,1** en §17.2 · `duty` **0,06 %** contre
  **0,5 %**. Références antérieures du **même** régime : §16.1 (`mock off / groupage on`)
  = **19,1 ms/cyc · 0,4 %** ; §17.1 (T0) = **duty 0,5 %**. Le 2,7 / 0,06 % est **seul de son
  espèce**, et le `duty` est précisément le chiffre sur lequel §16.2 dit qu'un module H24 se
  budgète.
🔴 **CAUSE IDENTIFIÉE : LA DÉFINITION DE LA COLONNE A CHANGÉ, ET CE N'ÉTAIT PAS DÉCLARÉ.** Ici,
`ms/cyc = flush/cyc × copie µs/flush` **exactement** ((a) : 1,00 × 2 689 = 2,7 ; (c) : 6,00 ×
2 933 = 17,6). En §16.1 et §17.2 il **incluait l'attente de synchro** (§16.1 `on/on` : 3,47 ×
2 883 = 10,0 ms pour **55,4** publiés). ⚠️ `cmd_flush` imprime la copie **et** l'attente
**séparément** et ne publie ni `ms/cyc` ni `duty` : **ces deux colonnes sont dérivées par
l'opérateur**, et la formule a changé d'une séance à l'autre sans être écrite.
⏳ **TÂCHE DE SÉANCE CARTE OUVERTE** : re-relever (a) et (b) avec la formule **FIGÉE ET ÉCRITE**.
⛔ Jusque-là, aucun `duty` de cette table ne se compare à §16.1, §17.1 ou §17.2.
🔴 **(c) A CHANGÉ DE VALEUR DEPUIS §17.2, ET LA CONFRONTATION MANQUAIT** — ajoutée le
2026-08-19. §17.2 (`21d02be`) publiait `flush/cyc` **4,00** et `px/cyc` **140 400** ; cette
séance (`d5d3539`) publie **6,00** et **210 600** — soit **+2 flushes et +50 % de pixels**.
Le paragraphe ci-dessous confrontait le nouveau chiffre à l'**extrapolation** d'AC8
(`6 × 35 100`) et **jamais à sa propre mesure précédente**, alors qu'AC7 exige que *« l'écart
soit expliqué ou déclaré inexpliqué »* — et que c'est ce régime que la séance avait été
convoquée pour refaire.
⚠️ **HYPOTHÈSE, ÉCRITE COMME TELLE ET NON MESURÉE** : `2d97850` a fait passer `RÉSEAU` à deux
grandeurs ; si la rafale invalidait **quatre** cases sur `21d02be` et en invalide **six** ici,
4,00 → 6,00 flush/cyc et 4 × 35 100 → 6 × 35 100 px suivent exactement. ⛔ **Ce n'est pas
mesuré** : ni le nombre de cases réellement invalidées sur `21d02be`, ni la composition du tir.
⏳ **À trancher en séance carte** (même session que (a) et (b)), ou à déclarer inexpliqué.
✅ **CONFIRMÉ PAR §17.10 (2026-08-19) — 210 600 px, REPRODUIT DEUX FOIS** sur `b5cd141` avec un
settle garanti (6 flushes / 1 cycle). ⚠️ §17.10 avait d'abord publié un démenti (« 4 / 1 /
140 400 ») : **artefact de lecture précoce**, réfuté le soir même par la **lecture de la dalle**.
Le témoin cité ci-dessous a, lui, bien été **SUPPRIMÉ du firmware** — il ne pouvait rendre que sa
valeur de succès, et la fusion se prouve désormais par `flush` seul, avec son témoin négatif
(poussées une par une : 6 flushes / **6 cycles** / 210 600 px).
✅ (c) était mesuré sur `d5d3539`,
et `flush` confirme **6 flushes / 1 cycle / 210 600 px** dans la même passe — soit très exactement
le `6 × 35 100 = 69 % d'un plein écran` que l'extrapolation d'AC8 prédisait.
⚠️ **LES COLONNES « — » DE (c) SONT DÉCLARÉES NON DÉFINIES, PAS OUBLIÉES.** Un CPU global, un
flush/s, un cyc/s ou un duty sont des grandeurs **par unité de temps** : la rafale est un **tir
unique** sous un seul verrou, elle n'a pas de régime permanent. Les chiffrer supposerait de
choisir une fenêtre arbitraire, et le nombre obtenu ne décrirait que cette fenêtre.
⛔ **AC7 demandait les douze colonnes pour chaque régime ; pour (c) c'est la DEMANDE qui est
mal posée, et c'est écrit plutôt que rempli au jugé.**

#### AC12 — non-régression, sur le firmware LIVRÉ de cette séance

| Grandeur | dev dn4-1 (`21d02be`) | **séance de revue (`d5d3539`)** | écart |
|---|---:|---:|---:|
| Binaire `desknode.bin` | 914 048 o | **917 488 o** | **+3 440 o** (partition libre à 78 %) |
| RAM interne libre | 104 087 o | **104 119 o** | **+32 o** |
| PSRAM libre | 7 768 236 o | **7 768 236 o** | **0** |
| Tas LVGL utilisé | 20 292 o (33 %) | **20 504 o (34 %)** | +212 o |
| Plus gros bloc libre | 41 112 o | **40 744 o** | −368 o (**98,0 % du libre**) |
| Fragmentation | 2 % | **2 %** | 0 |
| Tas sur 40 transitions | −20 o | **+8 o** | **PLAT** ✅ |
| `fps 15` | 37,40 Hz | **37,40 Hz** (écart −0,00 %) | **0** ✅ |
| Boot « prêt en N ms » | 2 297 ms | **2 311 ms** | +14 ms (bruit) |
| Latence transition (n=40) | 335,0 (291,3 / 397,1) | **336,5 (291,3 / 398,7)** | **+1,5 ms** |
| `dn_capteurs` | 5 000 ms, 0 erreur | **4 999 ms mesurés, 0 erreur** | ✅ |

⇒ **Aucune régression.** La RAM interne libre **remonte** de 32 o, la PSRAM ne bouge pas, le tas
reste **plat** sur 40 transitions et le `fps` est à la valeur théorique exacte.
🔴 ⚠️ **CE DELTA N'EST PAS « LE COÛT DE LA REVUE DE CODE » — ATTRIBUTION CORRIGÉE LE 2026-08-19.**
La plage `21d02be → d5d3539` contient **`2d97850`**, c'est-à-dire **la séance carte**, dont §17.2
chiffre elle-même l'ampleur (« `dn_ui.c` +45, `dn_widget.c` +26, `dn_console.c` +32, `dn_ui.h` +4,
`dn_widget.h` +9 »). Le **+3 440 o de binaire** et le **+212 o de tas LVGL** couvrent donc **AU
MOINS DEUX CAUSES INDÉPENDANTES**, et rien ici ne permet de les séparer.
⇒ La borne basse correcte pour isoler la revue est **`2e06ff0`** — l'ancre de la plage de revue.
⛔ Ne pas citer ce delta comme un coût de revue tant qu'il n'a pas été re-mesuré depuis `2e06ff0`.
⚠️ **La latence de transition ne se solde toujours pas ici** : le budget < 300 ms appartient à `dn4-4`.

#### ⏳ CE QUE CETTE SÉANCE N'A PAS PU FERMER

- **AC7 régime (b), le vrai 1 Hz avec l'agent** : il exige `COM3`, donc la carte **détachée de WSL**.
- **Le re-relevé de la latence acceptation→label** : la revue a changé ce que l'instrument mesure
  (elle inclut désormais l'attente du verrou LVGL et la pose) ⇒ **`n = 8 075 · 1 / 204 / 480 ms`
  est MORT** et n'a pas encore de remplaçant. ⛔ Ne pas le republier.

#### AC7 régime (b) — LE VRAI 1 Hz, agent réel sur `COM3` (2ᵉ passe de la séance)

Agent lancé depuis la tour (`--duree 180 --temoin`), carte détachée de WSL. **900 trames émises
en 180,1 s à 5,00 trames/s, 0 erreur d'envoi, 0 recalage de cadence.** Compteurs firmware remis à
zéro avant le détachement, relus après ré-attachement — la carte **ne redémarre pas**, les
compteurs traversent l'alternance.

⚠️ **La fenêtre des compteurs (238,9 s) est plus large que la fenêtre d'agent (180,1 s)** :
elle englobe le détachement, mes commandes et le ré-attachement. **La part au repos est
RETRANCHÉE** en utilisant le régime (a) mesuré le même jour (1,61 % · 0,23 cyc/s · 32 312 px/cyc)
— ⛔ pas estimée, mesurée.

| grandeur | mesuré (b) | §17.2 (b) | verdict |
|---|---:|---:|---|
| **CPU global** | **13,19 %** | 13,09 % | ✅ reproduit |
| cycles/s | **2,19** | 2,05 | ✅ |
| flush/s | **5,22** | 5,17 | ✅ |
| flush/cycle | **2,38** | 2,52 | ✅ |
| px/cycle | **83 380** | 87 982 | ✅ |
| copie µs/flush | **2 915** (max 3 020) | 2 925 | ✅ |
| plus grande aire | **35 100** | 35 100 | ✅ |

**Liaison** : 896 trames valides · **0 doublon · 0 resynchro · 0 rejet de TOUTE cause**
(tronquée, trop longue, checksum, version, format, bornes) · **4 pertes seq sur 900 (0,44 %)**,
du même ordre que les 0,31 % de la 1ʳᵉ séance.
**Écho console de l'agent** : **225,7 o/s · 5,12 lignes/s** (1ʳᵉ séance : 232,0 · 5,11) — ✅ stable.
**Coût propre de l'agent** : **2,421 % d'un cœur · 0,1513 % machine**, contre 2,161 % / 0,135 %
à la 1ʳᵉ séance ⇒ **+0,26 pt, NON EXPLIQUÉ**. ⚠️ Candidat : l'isolation par source ajoutée par la
revue (un `try` et une lambda par métrique et par cycle). ⛔ **Pas mesuré en A/B — déclaré, pas attribué.**
✅ **Les deux compteurs ajoutés par la revue rapportent sur la vraie machine** :
« aucun ecretage » (désormais **vérifiable** — la fréquence CPU passe enfin par le compteur) et
« **aucune panne de source : les cinq ont répondu à chaque cycle** ».

#### 🔴 La latence acceptation→label, RE-RELEVÉE — et l'ancien chiffre était autre chose

| | n | min | moy | max |
|---|---:|---:|---:|---:|
| ⛔ **MORT** — ancien instrument, 1ʳᵉ séance | 8 075 | 1 ms | 204 ms | 480 ms |
| ✅ **instrument corrigé**, cette séance | **896** | **30 ms** | **124 ms** | **169 ms** |

⛔ **LES DEUX LIGNES NE SE COMPARENT PAS**, et pour **deux** raisons cumulées :
1. **L'instrument a changé de définition.** L'ancien lisait `v.age_us`, figé **avant** la prise du
   verrou LVGL : il mesurait la **péremption** d'une trame dans la file, pas le trajet jusqu'au
   label. Le nouveau chronomètre jusqu'à la **pose**.
2. **Les conditions diffèrent.** La 1ʳᵉ séance avait un owner qui **naviguait** (`build_scene()`
   bloque 307-322 ms) ; ici **personne n'a touché la dalle**.

✅ **ET LE NOUVEAU CHIFFRE EST PRÉDIT PAR LA THÉORIE, ce qui le rend falsifiable** : la tâche
`dn_link` se réveille toutes les **250 ms** ⇒ une attente uniforme sur cette fenêtre donne une
moyenne attendue de **~125 ms**. Mesuré : **124 ms**.
⚠️ **LA PRÉMISSE D'ABORD PUBLIÉE ICI ÉTAIT FAUSSE** (revue 2026-08-19) : elle disait « les trames
arrivent **toutes les 200 ms** ». L'agent **n'espace pas ses trames** — `t_ms` est calculé **une
seule fois pour tout le cycle** (`dn_agent.py`), puis les cinq trames sont écrites **sans aucun
`sleep`** avant le sommeil jusqu'au top de seconde suivant. Les cinq portent d'ailleurs le **même
horodatage**, ce qui le prouve indépendamment. « 5,00 trames/s » avait été lu comme « une trame
toutes les 200 ms ». Le nombre attendu **reste ~125 ms** sous le modèle rafale (la rafale est
courte devant les 250 ms de réveil) — ⛔ mais dans un dépôt qui vient de consacrer §17.4 à punir
une prémisse écrite d'avance que la mesure a démentie, **une prédiction validée sur une prémisse
fausse ne peut pas être ce qui « rend le chiffre falsifiable »**. La prédiction tient ; sa
justification a été refaite.
Et **max 169 ms < 250 ms** ⇒ **aucune contention de verrou**, cohérent avec un écran non touché.
⚠️ C'est pourquoi l'ancien `max = 480 ms` dépassait deux fenêtres de réveil : ce n'était pas
l'attente du verrou (l'instrument ne pouvait pas la voir) mais les **re-essais** qu'elle
provoquait, chacun ajoutant 250 ms d'âge. L'attribution publiée était **indirectement** juste,
par un mécanisme qui n'était pas celui qu'elle nommait.

#### 🔴 DÉFAUT TROUVÉ DANS §17.2 : sa colonne par tâche ne se réconcilie pas avec sa propre colonne globale

| | CPU global | = pt d'UN cœur | somme des tâches listées | écart |
|---|---:|---:|---:|---|
| §17.2 régime (b) | 13,09 % | **26,18 pt** | `taskLVGL` 11,00 + `console_repl` 1,27 + `dn_link` 0,24 = **12,51 pt** | 🔴 **facteur ~2** |
| cette séance, régime (b) | 13,19 % | **26,38 pt** | 22,16 + 2,51 + 0,51 + `esp_timer` 0,87 + `dn_capt` 0,09 = **26,13 pt** | ✅ **+0,25 pt** (tâches mineures) |

Rapport tâche par tâche entre les deux séances : `taskLVGL` **×2,01**, `console_repl` **×1,98**,
`dn_link` **×2,11** — et le régime (a) fait de même (`taskLVGL` 1,11 → **2,20 pt**).

🔴 **LA CAUSE DE CE FACTEUR 2 EST INCONNUE — ET LA CAUSE D'ABORD PUBLIÉE ICI EST MÉCANIQUEMENT
IMPOSSIBLE** (revue 2026-08-19). Ce paragraphe concluait : *« la colonne par tâche de §17.2 est
exprimée en % de la MACHINE (2 cœurs) alors que son en-tête annonce “pt d'un cœur” »*.
**Cette explication ne peut pas être vraie**, pour deux raisons vérifiées dans le code :
1. `cpu brut` calcule **chaque** pourcentage de tâche par une seule expression —
   `(t * 100ULL) / total` avec `total = portGET_RUN_TIME_COUNTER_VALUE()`, une durée écoulée
   **MONO-CŒUR**. **Il n'existe aucune branche** capable de produire une colonne par tâche
   normalisée machine. Le dénominateur est unique.
2. **Le code n'a pas bougé entre les deux séances** : la légende « rapporté à UN cœur » et la
   garde de rebouclage ont été posées en **`395310e`** (dn3-2), donc **avant** `21d02be` sur
   lequel §17.2 a été relevée. Les deux tables sortent du même binaire et de la même légende.

⚠️ **Le facteur 2 est RÉEL** — il est mesuré, sur cinq postes, dans deux régimes. **C'est son
explication qui est fausse.** ⛔ Le dépôt a remplacé une affirmation chiffrée fausse par une
**autre affirmation chiffrée non mesurée**, alors que la falsification tenait en une commande
(`cpu brut` rejoué deux fois sur le firmware courant), dans la séance même où la carte était
sous la main.
⏳ **TÂCHE DE SÉANCE CARTE OUVERTE** (décision owner du 2026-08-19) : rejouer `cpu brut` **deux
fois** et trancher. Jusque-là, la cause s'écrit **INCONNUE**.
✅ **Les colonnes GLOBALES, elles, sont justes** — 13,09 vs 13,19 % et 1,62 vs 1,61 % : **le régime
se reproduit**, et c'est ce qui autorise à continuer.
⛔ **Ne pas corriger §17.2 en silence** : le défaut est nommé ici, la table d'origine reste lisible
— et elle porte désormais un renvoi vers cette section.

### 17.10 🔴 SÉANCE POST-REVUE DU 2026-08-19 — firmware `b5cd141`, UN SEUL SHA

> **Firmware : `b5cd141`** — les **33 correctifs** de la revue du 2026-08-19.
> ✅ **SHA LU AU BANDEAU `App version`, PAS DÉDUIT DU DÉPÔT** : `I (657) app_init: App version: b5cd141`,
> compilé `Aug 19 2026 01:16:12`, ELF SHA256 `e3faa3a3c…`. ⛔ C'est **exactement** le contrôle qui
> manquait les **deux** fois où AC12 s'est rouverte (`49a8364` au lieu de `395310e` en dn3-2 ;
> `21d02be` au lieu de `2d97850` en dn4-1).
> 🔴 **TOUS les relevés de cette section portent CE SHA**, régimes (a), (b) et (c) compris.
> C'est ce qui la distingue de §17.9, qui mélangeait deux firmwares sur trois régimes.

#### 🔴 LES DÉFINITIONS DE COLONNE, FIGÉES ET ÉCRITES **AVANT** LE PREMIER RELEVÉ

C'est la cause du défaut n°2 de §17.9 : `ms/cyc` et `duty` y ont été **dérivés par l'opérateur**
avec une formule **qui avait changé depuis §16.1/§17.2, sans être déclarée** — d'où un `duty`
divisé par 8 publié sous « Aucune dérive ». ⛔ Aucun de ces deux nombres n'est imprimé par le
firmware : `cmd_flush` publie la copie **et** l'attente **séparément**.

| Colonne | Formule EXACTE | Source |
|---|---|---|
| `CPU global` | `100 − idle0/2 − idle1/2`, en % **machine** | `cpu brut`, delta |
| `taskLVGL`, `console_repl`, `dn_link` | `(t_tâche × 100) / total`, **rapporté à UN cœur** | `cpu brut`, delta |
| `cyc/s` | cycles LVGL / durée de la fenêtre | `flush` |
| `flush/cyc` | flushes / cycles | `flush` |
| `px/cyc` | pixels copiés / cycles | `flush` |
| `plus gr. aire` | plus grande aire de flush, en px | `flush` |
| `copie µs/flush` | temps de **copie seul**, ⛔ attente de synchro **EXCLUE** | `flush` |
| **`ms/cyc`** | **`flush/cyc × copie µs/flush ÷ 1000` + attente de synchro/cycle** | dérivé, **les DEUX termes** |
| **`duty`** | **`ms/cyc × cyc/s ÷ 10`**, en % du temps mural | dérivé |

🔴 **LA DIFFÉRENCE AVEC §17.9 EST LÀ, ET ELLE VAUT UN FACTEUR 8** : §17.9 a calculé
`ms/cyc = flush/cyc × copie µs/flush` **en oubliant l'attente de synchro** ((a) : 1,00 × 2 689
= 2,7 ms). §16.1 et §17.2 l'incluaient (§16.1 `on/on` : 3,47 × 2 883 = 10,0 ms de copie pour
**55,4 ms/cyc** publiés — soit **45,4 ms d'attente**). ⇒ **La colonne de §17.9 n'est pas la même
grandeur que celle de §16.1, §17.1 et §17.2.** Ici, on publie **les deux termes séparément**, en
plus du total, pour que la question ne puisse plus se reposer.

| Terme publié | Ce qu'il est |
|---|---|
| `copie ms/cyc` | la copie seule — comparable à §17.9 |
| `attente ms/cyc` | l'attente de synchro seule — **absente de §17.9** |
| `ms/cyc` | leur **somme** — comparable à §16.1, §17.1 et §17.2 |

#### AC7 — LES TROIS RÉGIMES, MÊME FIRMWARE `b5cd141`, MÊME SESSION

| régime | CPU | `taskLVGL` | `console_repl` | `dn_link` | cyc/s | flush/cyc | flush/s | px/cyc | plus gr. aire | copie µs/flush | **copie ms/cyc** | **attente ms/cyc** | **ms/cyc** | **duty** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **(a) repos, agent arrêté** (120,4 s) | **1,58 %** | 2,20 pt | 0,03 pt | 0,02 pt | 0,216 | 1,00 | 0,216 | 32 725 | 35 100 | 2 740 (max 2 982) | 2,74 | 6,32 | **9,06** | **0,20 %** |
| **(b) RÉGIME RÉEL, 5 métriques à 5 trames/s** (120,6 s) | **13,61 %** | **22,56 pt** | **3,01 pt** | **0,49 pt** | 2,056 | 2,52 | 5,17 | **88 069** | 35 100 | 2 913 (max 3 185) | 7,33 | 41,76 | **49,09** | **10,09 %** |
| **(c) `widget rafale`** (tir unique) | — ⚠️ | — ⚠️ | — ⚠️ | — ⚠️ | — ⚠️ | **6,00** | — ⚠️ | **210 600** | 35 100 | 2 915 (max 2 951) | 17,49 | 47,79 | **65,28** | — ⚠️ |

Autres tâches, régime (b) : `esp_timer` 0,82 · `dn_rtc` 0,23 · `dn_capt` 0,10 · `main` 0,02 pt.
Régime (a) : `esp_timer` 0,68 · `dn_rtc` 0,16 · `dn_capt` 0,06 · `main` 0,02 pt.
⚠️ Les colonnes « — » de (c) sont **NON DÉFINIES, pas oubliées** : CPU global, flush/s, cyc/s et
duty sont des grandeurs **par unité de temps**, et la rafale est un **tir unique** sous un seul
verrou. Les chiffrer supposerait de choisir une fenêtre arbitraire.

##### ✅ LE TEST QUI TRANCHE : la somme des tâches se réconcilie-t-elle avec le global ?

| | CPU global | = pt d'UN cœur | somme des tâches | écart |
|---|---:|---:|---:|---|
| **§17.10 (a)** | 1,58 % | 3,16 pt | 2,20 + 0,68 + 0,16 + 0,06 + 0,03 + 0,02 + 0,02 = **3,17 pt** | ✅ **+0,01 pt** |
| **§17.10 (b)** | 13,61 % | 27,23 pt | 22,56 + 3,01 + 0,82 + 0,49 + 0,23 + 0,10 + 0,02 = **27,23 pt** | ✅ **−0,00 pt** |
| §17.9 (b) | 13,19 % | 26,38 pt | **26,13 pt** | ✅ +0,25 pt |
| §17.2 (b) | 13,09 % | 26,18 pt | **12,51 pt** | 🔴 **facteur ~2** |

#### 🔴 LE « FACTEUR 2 » EST TRANCHÉ — ET LA CAUSE PUBLIÉE EN §17.9 ÉTAIT PRESQUE JUSTE

**Ce que cette séance établit, PAR LA MESURE :**
1. **§17.9 est REPRODUITE par une mesure indépendante, sur un AUTRE firmware.** Régime (a) :
   `taskLVGL` **2,20 pt** ici contre **2,20 pt** en §17.9. Régime (b) : **22,56** contre 22,16,
   `dn_link` **0,49** contre 0,51. ⇒ **c'est §17.2 qui est l'anomalie**, pas §17.9.
2. **Le régime d'AFFICHAGE de §17.2, lui, se reproduit AU CHIFFRE PRÈS** : cyc/s **2,056** contre
   2,05 · flush/cyc **2,52** contre 2,52 · flush/s **5,17** contre 5,17 · px/cyc **88 069** contre
   87 982. ⇒ **le défaut est dans la colonne par tâche SEULE**, pas dans la mesure du régime.
3. **Le test de réconciliation est le discriminant** : §17.10 passe à −0,00 et +0,01 pt, §17.9 à
   +0,25 pt, **§17.2 échoue d'un facteur 2**. Ce test aurait suffi à voir le défaut en §17.2.

⚠️ **CORRECTION D'UNE AFFIRMATION DE LA REVUE DU 2026-08-19, PAR SA PROPRE MESURE.** La revue avait
écrit que la cause publiée en §17.9 — *« la colonne par tâche de §17.2 est exprimée en % de la
MACHINE alors que son en-tête annonce pt d'un cœur »* — était **« mécaniquement impossible »**.
C'était **trop fort**, et il faut le dire : elle est impossible **comme propriété de l'instrument**
(`cpu brut` calcule `(t × 100) / total` avec un `total` **mono-cœur**, et son code n'a pas bougé
depuis `395310e`), mais **parfaitement possible comme erreur de DÉRIVATION DE L'OPÉRATEUR** — et
l'arithmétique la soutient : **12,51 × 2 = 25,02**, à comparer aux **26,18 pt** attendus, l'écart
restant étant les tâches non listées par §17.2 (`esp_timer`, `dn_rtc`, `dn_capt`).
⇒ **§17.9 avait raison sur le QUOI (un facteur 2, machine contre cœur), et se trompait sur le OÙ**
(l'instrument, alors que c'est la dérivation). ⛔ §17.2 reste lisible et n'est pas réécrite ; sa
**colonne par tâche est à lire ×2**, et **son budget `console_repl` de 1,27 pt est MORT** — la
valeur mesurée est **3,01 pt** ici et 2,51 pt en §17.9.

#### 🔴 AC7 (c) — L'EXTRAPOLATION D'AC8 EST **CONFIRMÉE**, ET CETTE SECTION A D'ABORD PUBLIÉ LE CONTRAIRE

> 🔴 **AUTO-RÉFUTATION, LE MÊME SOIR, ET C'EST L'ŒIL DE L'OWNER QUI L'A DÉCLENCHÉE.**
> Cette section a d'abord publié **« 4 flushes / 1 cycle / 140 400 px = 45,7 % d'un plein écran »**
> et en a conclu que l'extrapolation d'AC8 était **démentie**. **C'ÉTAIT FAUX**, et le chiffre a été
> committé avant d'être réfuté. Ce qui s'est passé, dans l'ordre :
> 1. Trois tirs avec un délai de settle **NON GARANTI** (~0,7-1 s, la durée d'un lancement de
>    `dn_console.py`) rendaient **4 flushes / 1 cycle**, de façon **reproductible**.
> 2. ⚠️ **Le tir n°1 de la même série rendait « 1 flush / 0 cycle »** — donc le piège de lecture
>    précoce était **visible**, et il a été écarté comme un cas isolé au lieu d'être suspecté
>    partout. **Un chiffre faux mais PLAUSIBLE est plus dangereux qu'un chiffre absurde.**
> 3. 🔴 **L'OWNER A LU LA DALLE** : les **six** cases affichaient leurs nouvelles valeurs, et elles
>    correspondaient **exactement** au modèle (`48,8 % 36,4 GHz` · `49,9 % 43,7 °C` · `50,0 %` ·
>    `51,1 / 57,3 Mb/s` · `52,2 Mo/s`). ⇒ **six cases peintes ne peuvent pas tenir en 4 flushes** :
>    les deux affirmations ne pouvaient pas être vraies ensemble.
> 4. Rejeu avec une attente **GARANTIE de 3 s** (`--listen 3`), quatre tirs :
>    **6 / 1 / 210 600** · **6 / 1 / 210 600** · 7 / 2 / 245 700 · 7 / 2 / 245 700 — les deux
>    derniers portant exactement **un flush et un cycle de parasite** (AMBIANCE, tick 5 s).
> ⇒ ✅ **LE CHIFFRE EST 6 flushes / 1 cycle / 210 600 px**, et **l'extrapolation d'AC8 tient** :
>   6 × 35 100 = 210 600 px = **69 % d'un plein écran**, LVGL ne fusionne aucune des six zones.
> ⇒ ✅ **§17.9 avait RAISON** et elle est ici reproduite ; c'est **§17.2 (4,00 / 140 400) qui porte
>   le défaut**, très probablement **le même piège de lecture précoce** — hypothèse, non vérifiée.
> ⛔ **LA LEÇON, ET ELLE COÛTE CHER** : le settle d'un compteur de redessin **doit être garanti**,
>   jamais laissé au hasard d'un temps de lancement de process. Et surtout : **l'œil a corrigé
>   l'instrument**. Aucune console de ce firmware ne pouvait voir que 4 flushes contredisaient
>   l'écran — il fallait regarder la dalle. *Le constat owner à l'œil fait foi*, ici littéralement.

#### AC7 (c) — le détail de la mesure retenue

| Ce qu'on provoque | flushes | cycles | px total | **px / cycle** |
|---|---:|---:|---:|---:|
| **Étalé** — six `widget pousser`, une par cycle | 6 | **6** | 210 600 | 35 100 |
| **Rafale** — six poussées sous UN verrou (settle 3 s garanti, 2 tirs propres) | **6** | **1** | **210 600** | **210 600** |
| *(rafale, settle NON garanti ~1 s — ⛔ MESURE FAUSSE, conservée pour la leçon)* | *4* | *1* | *140 400* | *140 400* |

✅ **LA FUSION EST PROUVÉE, ET PAR `flush` SEUL** — six poussées tombent dans **un seul cycle**.
C'est ce qu'AC7 (c) devait établir, et c'est établi **sans témoin** : le témoin de rafale a été
**supprimé** du firmware le 2026-08-19 (il n'a jamais pu rendre autre chose que sa valeur de
succès, trois sémantiques de suite). Le témoin négatif est là aussi : poussées **une par une**,
les six cases produisent bien **6 flushes / 6 cycles / 210 600 px** — donc **les six salissent**.
⇒ *un test négatif ne vaut que si le stimulus est prouvé* : il l'est.

✅ **ET LE COÛT EST CELUI QUI ÉTAIT PRÉDIT** : **210 600 px = 69 % d'un plein écran**, LVGL ne
fusionnant **aucune** des six zones — ce que l'epic écrit, et qui est ici **reproduit deux fois**
avec un settle garanti. `plus grande aire` reste à **35 100 px** : chaque case est copiée
séparément, entière, et aucune n'est jointe à sa voisine.
⇒ **AC7 (c) et AC8 gardent leur chiffre. Aucun correct-course n'est requis de ce côté.**
⚠️ **Ce qui reste à qualifier** : §17.2 publie **4,00 / 140 400** pour ce même régime. L'hypothèse
la plus simple est qu'elle a subi **le même piège de lecture précoce** que cette section a subi ce
soir — mais ⛔ **ce n'est pas vérifié**, et §17.2 n'est pas réécrite sur une hypothèse. Porté au
ledger comme question ouverte, avec sa recette : rejouer (c) sur `21d02be` avec settle garanti.

#### AC12 — non-régression, `d5d3539` → `b5cd141`

| Grandeur | séance de revue (`d5d3539`) | **cette séance (`b5cd141`)** | écart |
|---|---:|---:|---:|
| Binaire `desknode.bin` | 917 488 o | **917 824 o** | **+336 o** (partition libre à 78 %) |
| RAM interne libre | 104 119 o | **103 319 o** | **−800 o** |
| PSRAM libre | 7 768 236 o | **7 768 236 o** | **0** ✅ |
| Tas LVGL utilisé | 20 504 o (34 %) | **20 572 o (34 %)** | **+68 o** |
| Plus gros bloc libre | 40 744 o | **40 744 o** | **0** ✅ |
| Fragmentation | 2 % | **2 %** | 0 ✅ |
| Tas sur 40 transitions | +8 o | **20 572 → 20 596, final 20 568** | **PLAT** ✅ |
| `fps 15` | 37,40 Hz | **37,40 Hz** (561 trames / 14 999 885 µs, écart **−0,00 %**) | **0** ✅ |
| Boot « prêt en N ms » | 2 311 ms | **2 311 ms** | **0** ✅ |
| Latence transition (n=40) | 336,5 (291,3 / 398,7) | **349,9 (291,8 / 425,6)** | **+13,4 ms** ⚠️ |
| `dn_capteurs` | 4 999 ms, 0 erreur | **BME680 @ 0x77, 0 erreur** | ✅ |
| Liaison, régime (b) | — | **598 valides / 600 · 0 rejet · 2 pertes seq (0,33 %) · 1 reprise** | ✅ |

⚠️ **LA LATENCE DE TRANSITION PREND +13,4 ms, ET CE N'EST PAS EXPLIQUÉ.** Le **minimum est
identique** (291,8 contre 291,3) et c'est la **queue** qui s'allonge (max 425,6 contre 398,7).
⛔ **Déclaré, pas attribué** : rien dans les 33 correctifs ne touche le chemin de transition
(`dn_ui_desc_brut` n'y est pas appelé, la garde `k_metriques` est dans le parseur, le `ESP_LOGE`
de `k_pc` ne s'exécute jamais en nominal). Candidat non écarté : **variance** — n = 40, et la
séance précédente publiait déjà 335,0 puis 336,5 pour le même firmware à un commit près.
⚠️ Le budget < 300 ms appartient à **dn4-4**, il ne se solde pas ici.

#### AC5 — LE TÉMOIN « JAUGE VISIBLE », LU POUR LA PREMIÈRE FOIS

🔴 **La revue du 2026-08-18 avait trouvé que cet instrument NE POUVAIT PAS voir ce qu'il prouvait**
(`dn_ui_widget_pointeurs()` ne lisait que `s_wobj[0..5]`, jamais `s_demo`). Le correctif a été
appliqué le jour même — **et l'instrument n'avait jamais été LU**. Il l'est ici.

| Instrument | Ce qu'il rend |
|---|---|
| Journal d'abandon (`ESP_LOGW`, à l'armement) | `« DÉMO 2+JAUGE » : pas de place pour la ligne secondaire (**y_bas=148 + 20 > h=156**) — 2 grandeur(s) + jauge. La jauge est prioritaire` |
| Table de géométrie (`widget`) | `DEMO   2   OUI   non   (n=2, jauge demandee)` |
| **Constat owner à l'œil** | ✅ **la jauge est VISIBLE** · deux lignes de valeur, **pas de troisième** · rien ne déborde |

✅ **La colonne « secondaire » n'est plus constante par construction** : `non` y apparaît, pour la
première fois depuis que la table existe. C'était le défaut n°6 de la revue précédente.
🔴 **ET LE JOURNAL CONFIRME LA CORRECTION D'ARITHMÉTIQUE DE LA REVUE DU 2026-08-19** : il imprime
**`148 + 20 > 156`**, exactement les chiffres que la revue a substitués dans les Dev Notes de la
story. La story publiait **`154` / `174 > 156`** — faux sur **deux** lignes, `+26` compté là où le
code pose `+20`. ⇒ **le correctif de doc est validé PAR LA MESURE**, pas seulement par la lecture.

#### AC12 — les gestes owner, sur le firmware LIVRÉ

⚠️ C'est l'écart qui a rouvert AC12 **deux fois** : des constats à l'œil relevés sur un firmware
qui n'était pas le livré. Ici, **tout est sur `b5cd141`, SHA lu au bandeau.**

| Geste | Résultat |
|---|---|
| **Smoke 6/6** | ✅ **conforme** — grille complète, **cinq cases sur six à « -- » et AMBIANCE seule vivante** (le différenciateur D6, PC éteint), barre `01:17 MER. 19 AOÛT` lisible, rien d'anormal |
| **Tactile, 3 tours** | ✅ **trois taps, trois BONNES cases, retour OK à chaque fois**, aucun tap ignoré. Compteurs : **4 taps · 4 transitions · 0 sur MENU** |

#### 🔴 UN PIÈGE D'INSTRUMENT RENCONTRÉ, ET IL A COÛTÉ UNE FENÊTRE DE 120 s

Lire `cpu brut` **immédiatement après** une rafale d'injection capture **l'écho des dernières
trames** au lieu de la table : la capture rend trois lignes et le relevé est **perdu**. La fenêtre
(b) a été **jetée et rejouée**. ⇒ L'injecteur draine désormais le port **0,4 s avant de fermer**.
⚠️ Corollaire à retenir : une capture série qui « réussit » (exit 0) peut ne contenir **aucune**
des lignes attendues. **Compter ce qu'on a capturé avant de le publier** — c'est le même motif que
`ffmpeg` qui sort en code 0 sans rien produire.

#### ⚠️ CE QUE CETTE SÉANCE N'A PAS MESURÉ, ET QUI DOIT ÊTRE DIT

- **Le régime (b) a été produit par INJECTION depuis le pilote WSL**, pas par l'agent Windows sur
  `COM3`. Même REPL, même `dn_link`, même `dn_ui`, **même cadence mesurée (5,00 puis 4,98 trames/s,
  en rafale une fois par seconde comme l'agent)** ⇒ **le régime FIRMWARE est celui de l'agent**.
  ⛔ **Ce qui n'est PAS mesuré ainsi, c'est le coût côté PC** — AC9 le mesure à part, sur COM3.
  ✅ **C'est un CHOIX, et il corrige un défaut de §17.9** : la fenêtre de §17.9 englobait le
  détachement USB, **les commandes de l'opérateur** et le ré-attachement, puis retranchait cette
  part au régime **(a) « repos, agent arrêté »** — alors que taper au REPL coûte à `console_repl`
  un ordre de grandeur au-dessus. Ici, **aucune commande n'est entrée dans la fenêtre**.
- **Le mécanisme du 140 400 contre 210 600** — voir ci-dessus, INCONNU.
- **Le +13,4 ms de latence de transition** — déclaré, non attribué.



---

## 18. `CPU` À TROIS ET `GPU` À TROIS — mesuré le 2026-08-19 (dn4-6, P9.1b)

> 🔴 **CE CHAPITRE PORTE DEUX BINAIRES, ET C'EST ÉCRIT ICI PARCE QU'IL NE L'ÉTAIT
> PAS** (revue de code du 2026-08-19, décision owner) :
>
> | sous-section | firmware | SHA **LU AU BANDEAU** |
> |---|---|---|
> | §18.0 à §18.6 — voies, largeur, régimes, prédiction | **`690af25`** | ✅ lu au bandeau |
> | **§18.7 — non-régression** | **`db5fcb8`** = **LE FIRMWARE LIVRÉ** | ✅ lu au bandeau |
> | §18.9 — la famine DMA et son remède | **`db5fcb8`** | ✅ lu au bandeau |
>
> ⛔ **L'en-tête de ce chapitre estampillait `690af25` pour l'ENSEMBLE**, y compris
> pour §18.7 — c'est-à-dire que le document désigné par AC14 comme porteur de la
> non-régression décrivait **un autre binaire que celui livré** (938 112 o contre
> 939 296 o, RAM 103 503 o contre 92 203 o). C'est **exactement** la famille
> d'écart qui a rouvert AC12 **deux fois** (`49a8364`/`395310e` en `dn3-2`,
> `21d02be`/`2d97850` en `dn4-1`), et qu'AC14 interdit nommément.
> ⚠️ Les mesures de §18.0-§18.6 **restent valides sur leur SHA** : `db5fcb8` ne
> change que `DN_DEFAULT_BOUNCE_PX` et la garde `bounce_px_refus()`. ⛔ Mais un
> SHA global qui ment sur une ligne est un SHA global qui ment.
>
> Marche P9.1b, insérée entre `dn4-1` et `dn4-2`.

### 18.0 CE QUE CETTE SECTION CORRIGE DANS §17.10 — À LIRE EN PREMIER

🔴 **DEUX CHIFFRES DE §17 NE SONT PAS REPRODUCTIBLES TELS QU'ILS SONT PUBLIÉS.**

1. **La latence de transition n'est pas reproductible à mieux que ±16 ms.**
   Rejouée sur le **MÊME binaire** que §17.10 (`cfd1a54` ≡ `b5cd141`
   fonctionnellement) :

   | | §17.10 | **re-relevé dn4-6** | écart |
   |---|---:|---:|---|
   | moyenne | 349,9 ms | **333,8 ms** | **−16,1 ms (−4,6 %)** |
   | minimum | 291,8 ms | **291,9 ms** | **+0,1 ms** |
   | maximum | 425,6 ms | **374,3 ms** | −51,3 ms |

   ✅ **Cela CONFIRME l'hypothèse que §17.10 avait laissée ouverte** sur le
   « +13,4 ms déclaré, NON attribué » : *« le minimum est identique à 0,5 ms
   près, c'est la QUEUE qui s'allonge »*. **C'était de la variance de queue.**
   ⇒ 🔴 **Le budget « < 300 ms » de `dn4-4` doit se juger sur une DISTRIBUTION,
   pas sur une moyenne.** Un verdict à ±13 ms sur n=40 est du bruit.

2. 🔴 **`flush/cyc`, `px/cyc` et `duty` du régime (b) DÉPENDENT DU RYTHME DE
   L'ÉMETTEUR, que §17.10 n'a pas enregistré.** Même firmware, même jeu de
   valeurs, **seul l'espacement des cinq trames dans la seconde change** :

   | espacement | cycles/s | flush/cyc | px/cyc | duty |
   |---|---:|---:|---:|---:|
   | **40 ms** | 3,154 | 1,63 | **59 630** | 7,96 % |
   | **4 ms** | 2,194 | 2,34 | **85 712** | 9,81 % |
   | *§17.10 (espacement inconnu)* | *2,056* | *2,52* | *88 069* | *10,09 %* |

   ⇒ **32 % d'écart sur `px/cyc`, produit par l'INSTRUMENT et non par le
   firmware.** ⛔ Un relevé de régime (b) qui ne déclare pas son espacement
   n'est comparable à rien. `tools/dn_injecteur.py --espacement` le rend
   explicite.

### 18.1 LA GÉOMÉTRIE RETENUE — ET LES TROIS VOIES AVEC LEUR PRIX

**Décision owner du 2026-08-19, prise SUR LA DALLE** : la voie **« repli »**.

```
case 225 x 163   (D12 : barre 70->60, MENU 60->51, grille 510->529)
  icone  dn_font_28 @ y=8   -> boite  8..43     <- EN-TETE INTACT
  titre  dn_font_14 @ y=22  -> boite 22..40
  val_y = 48, val_pas = 40  -> interligne 40-35 = 5 px  (= le critere de D12)
  3 grandeurs : derniere boite 48 + 2x40 + 35 = 163 = h  PILE
```

**LA TABLE OBJECTIVE DES CINQ CANDIDATS** — compteurs remis à zéro **sous le
verrou**, juste avant l'unique reconstruction de chaque voie :

| voie | case | `val_y`/`val_pas` | interligne | chevauch. | déborde | verdict |
|---|---|---|---:|---:|---:|---|
| **défaut** (avant D12) | 225×156 | 48 / 40 | 5 px | 0 | **2** ⬅️ | 🔴 2 valeurs CLIPPÉES (CPU, GPU) |
| **(a)** MENU supprimé | 225×180 | 36 / 36 | **1 px** | 0 | 0 | ⚠️ tient, **sous le critère D12** |
| **(b)** 3ᵉ police + D12 | 225×163 | 36 / 30 | 12 px* | 0 | 0 | ⚠️ tient — *****police 14, PAS 22** |
| **(c)** côte à côte | 225×156 | 48 / 40 | 5 px | **2** | 0 | 🔴 **RÉFUTÉE** (§18.2) |
| **(c2)** mixte | 225×180 | 48 / 40 | 5 px | **2** | 0 | 🔴 **RÉFUTÉE** (§18.2) |
| ✅ **repli** GPU à 3 + D12 | 225×163 | 48 / 40 | **5 px** | **0** | **0** | ✅ **RETENUE** |

🔴 **LA LIGNE « défaut » DISAIT 3, ET C'ÉTAIT UN RÉSIDU — CORRIGÉ PAR LA MESURE
LE 2026-08-19** (séance post-revue, firmware **`1156eac`**, SHA lu au bandeau).

L'arithmétique donnait 2 : à `case_h = 156`, `val_y = 48`, `val_pas = 40` et
`lh_val = 35`, seules `CPU` et `GPU` (n = 3) débordent — bas de la 3ᵉ valeur
`48 + 2×40 + 35 = 163 > 156` — tandis que `RÉSEAU`/`AMBIANCE` (n = 2) finissent à
123 et `RAM`/`DISQUE` (n = 1) à 83. **Rejouée sur un compteur propre, la mesure
donne 2, et elle les NOMME :**

```
« CPU » : 1 valeur(s) sur 3 DEBORDENT la case — bas 163 > h=156
« GPU » : 1 valeur(s) sur 3 DEBORDENT la case — bas 163 > h=156
⇒ 0 chevauchement · 0 trop large · 2 en HAUTEUR
```

⛔ **LA CAUSE EST INSTRUMENTALE, PAS GÉOMÉTRIQUE**, et c'est ce qui rendait le
chiffre plausible : `s_debordements += hors` vit dans `dn_widget_creer`, donc
s'accumule à **chaque** `build_scene()` — et `widget grille` comme
`widget dispo|entete|val|police` reconstruisaient **sans remettre les compteurs à
zéro**, contrairement à `widget voie`. Le « 3 » additionnait donc un résidu de
l'état précédent. ⇒ corrigé (`compteurs_geom_reset()`, UN endroit) et la voie de
référence est redevenue atteignable par `widget voie avantd12`, qui remet les
compteurs sous le verrou.
⚠️ **Ce que ça ne change pas** : le verdict de la voie « défaut » reste le même —
des valeurs clippées en silence, donc une case qui montre moins qu'elle ne
déclare. Ce sont **deux** cases, pas trois.

**CE QUE CHAQUE VOIE COÛTAIT, ANNONCÉ AVANT LE CONSTAT :**
- **(a)** — la barre MENU quitte la maquette · interligne **1 px, les valeurs se
  touchent** · l'en-tête compacté fait passer **les SIX icônes de 28 à 14 px**,
  or l'icône est le **seul** endroit où le champ `couleur` est exercé.
  🔴 **Sans en-tête compacté, (a) est réfutée par l'arithmétique** : l'icône 28
  descend à 43, et `44 + 4×35 = 184 > 180`.
- **(b)** — la police ~22 **n'est pas embarquée** ; la branche jouable utilise la
  14, donc *la géométrie est représentative, la lisibilité ne l'est pas*. Son
  verdict exigerait une régénération (npm + réseau, ~19 Ko extrapolés).
- **repli** — le `tr/min` tombe. ⚠️ **Alors qu'il a QUALIFIÉ** (§18.3).

**CONSTATS OWNER, VERBATIM (2026-08-19, firmware `793c880`, pire cas injecté) :**
1. lisibilité à ~50 cm : **« oui MAIS reseau pour si valeur haute convertir en Gb/s »**
2. le marquage `c.max` se distingue du % du dessus : **« ok »**
3. l'interligne de 5 px suffit : **« non c'est bon »**
4. la barre et le MENU rétrécis : **« non c'est bon »**
5. la page de détail : **« la 3ᵉ grandeur est tronquée mais pourrait être mise
   sous la 1ʳᵉ, y a la place »** ⇒ §18.4

### 18.2 LA LARGEUR, MESURÉE — L'ESTIMATION DE dn3-1 ÉTAIT FAUSSE DE 22 px

Relue de `lv_text_get_size()` (police liée, **kerning compris**) par
`widget largeur`. Case 225, **utile 201 px**, gouttière 12.

| | « 25,5 °C » | « 52,4 % » | total |
|---|---:|---:|---:|
| **estimé** (dn3-1, ~15,8 px/car.) | ~110 | ~95 | **205** |
| **MESURÉ** | **94** | **89** | **183** |

🔴 **L'estimation qui a écarté le côte à côte en dn3-1 était haute de 22 px
(−10,7 %)**, et `183 + 12 = 195 ≤ 201` : ce couple-là **TIENT**. Une décision de
conception reposait sur un produit `nb_caractères × largeur_moyenne`.

**MAIS AUCUN COUPLE NE TIENT AU PIRE CAS** — `a + b + 12 ≤ 201` :

| couple | a | b | total | tient ? |
|---|---:|---:|---:|---|
| CPU `100,0 %` + `5,7 GHz` | 104 | 107 | **223** | 🔴 |
| CPU `100,0 %` + `100,0 GHz` | 104 | 140 | **256** | 🔴 |
| GPU `100,0 %` + `95,0 °C` | 104 | 98 | **214** | 🔴 |
| GPU `100,0 %` + `150,0 °C` | 104 | 109 | **225** | 🔴 |
| GPU `350,0 W` + `3000,0 tr/min` | 115 | 194 | **321** | 🔴 |
| GPU **entiers** `350 W` + `3000 tr/min` | 91 | 170 | **273** | 🔴 |
| GPU entiers + **unité courte** `350 W` + `3000 rpm` | 91 | 141 | **244** | 🔴 |
| GPU **valeurs réelles** `53 W` + `604 tr/min` | 72 | 152 | **236** | 🔴 |
| AMB `-12,3 °C` + `100,0 %` | 99 | 104 | **215** | 🔴 |
| NET `↓ 1000,0 Mb/s` + `↑ 1000,0 Mb/s` | 202 | 202 | **416** | 🔴 |
| CPU `c.max 100,0 %` **seule** | 197 | — | **197** | ✅ |

⇒ **(c) et (c2) sont RÉFUTÉES.** Les trois variantes qu'il fallait instruire
avant de le dire le sont : **sans décimale** (273), **unité courte** (244),
**ligne mixte** (voie c2). Toutes échouent.
✅ **Un SECOND instrument, indépendant, le confirme sur la dalle** : en voie (c)
le détecteur de chevauchement du runtime lève **2 chevauchements** nommés et
chiffrés (`AMBIANCE` grandeur 1 : colonne gauche à 106 px, colonne droite à 112,
**il manque 6 px**).
⚠️ **Ni l'un ni l'autre seul ne tranche** : le compteur runtime ne voit que ce
qui est affiché À CET INSTANT (agent arrêté, `CPU` et `GPU` sont à « -- » et ne
chevauchent rien), `widget largeur` voit le pire cas.
⚠️ **La conclusion de dn3-1 tient donc, mais pour une raison qu'elle n'avait pas
calculée** : ce n'est pas le couple nominal qui déborde, c'est le pire cas.

### 18.3 `FAN_RPM` A QUALIFIÉ, ET IL N'A PAS DE PLACE

Session **959 échantillons / 16,0 min à 1 Hz**, tour en usage normal, critère
**écrit et HORODATÉ à `2026-08-19T11:17:55Z`, AVANT le tir**. Jugé sur la valeur
**AFFICHÉE** (le `tr/min` ENTIER).

| candidat | étendue (C1 ≥ 5) | taux texte (C2 ≥ 10 %) | σ (C3 ≥ 1) | verdict |
|---|---|---:|---:|---|
| **`FAN_RPM`** (idx 14) | **593..606 = 13** ✅ | **55,2 %** ✅ | **2,02** ✅ | ✅ **QUALIFIE** |
| `ASIC_POWER` (idx 23) *témoin* | 48..51 = **3** ❌ | 57,9 % ✅ | **0,75** ❌ | 🔴 **NE QUALIFIE PAS** |
| `max(cpu_percent(percpu))` | 0..77 ✅ | **90,2 %** ✅ | **12,29** ✅ | ✅ **QUALIFIE** |
| `cpu_percent()` | 0..34 ✅ | 69,3 % ✅ | 4,26 ✅ | ✅ |

🔴 **LE REPLI PRÉ-AUTORISÉ NE QUALIFIAIT PAS.** Trois textes du dépôt écrivent
que `ASIC_POWER` *« qualifie, déjà mesuré »* : le relevé du 2026-08-18 (n=29) ne
publiait que le **taux** (41,4 %) et une étendue de **5** — soit C1 **à la
limite exacte**. Sur 959 échantillons, l'étendue tombe à **3** et σ à **0,75**.
⚠️ **Le témoin fait son travail dans l'autre sens** : son taux (57,9 %) est
cohérent avec les 41,4 % attendus ⇒ **ce n'est pas une session plate**.
⇒ Si `FAN_RPM` avait échoué, le repli aurait été appliqué **sur une
qualification fausse**, en croyant l'avoir mesurée.

✅ **La conclusion de ledger *« le CPU n'aurait rien à mettre en troisième »* est
RÉFUTÉE** : la 3ᵉ grandeur bouge **plus** que la 1ʳᵉ (90,2 % contre 69,3 %,
σ 12,29 contre 4,26).
✅ **Coût de l'agent** : `cpu_percent()` **161 µs** de médiane, `percpu`
**287 µs**, les deux **383 µs/cycle = 0,0383 % d'un cœur** à 1 Hz — **facteur 26
sous le critère brief n°4**. Ordre **alterné** à chaque cycle ; la 1ʳᵉ série
n'était PAS anormale cette fois (158 contre 161 de médiane).
⚠️ **Correction d'un chiffre publié** : `percpu` était annoncé à
**0,07..0,10 ms** ; mesuré à **0,287 ms** de médiane, soit **~3× plus cher**.

### 18.4 LA PAGE DE DÉTAIL — UNE RÈGLE DIMENSIONNÉE SUR LA MAUVAISE CASE

`widget detail` relit le label construit (texte, largeur, x, largeur du parent).

| case | ligne composée | largeur | utile | verdict |
|---|---|---:|---:|---|
| GPU | `100,0 % · 95,0 °C · 350 W` | 405 px | 446 | ✅ tient |
| **CPU** | `100,0 % · 5,7 GHz · c.max 100,0 %` | **520 px** | 446 | 🔴 **DÉBORDE de 74 px** |

🔴 **La règle « trois par ligne » avait été dimensionnée sur `GPU` et appliquée
aux SIX.** Elle n'avait jamais été vérifiée sur la case qui porte un **préfixe** :
`c.max 100,0 %` mesure **197 px** à elle seule. ⛔ C'est l'extrapolation que
§18.2 interdit, commise dans la story qui l'interdit.
⇒ **Deux par ligne**, et **chaque ligne est MESURÉE à la pose**, avec un
`ESP_LOGW` nommant la case, la ligne, sa largeur et les px qui débordent.
Pire cas à deux par ligne, pour 446 utiles : CPU l1 **267** / l2 **197**,
GPU l1 **258** / l2 **90**. Le panneau passe de 62 à **97 px** (deux lignes de
35), pris au **cadre de courbe vide**, dont le bas ne bouge pas.

### 18.5 `RÉSEAU` BASCULE EN `Gb/s` — CONSTAT OWNER, ET LE CHIFFRE LE CONFIRME

`↓ 99999,9 Mb/s` mesure **202 px pour 201 utiles** : elle **débordait déjà**, et
LVGL la clippait sans un mot. Seuil **1000,0 Mb/s** (l'endroit où l'unité change
de nom), diviseur 1000, unité haute `Gb/s`.
- l'unité reste **dans le descripteur** (les DEUX y sont) ⇒ la règle *« une
  valeur ABSENTE ne porte JAMAIS son unité »* tient ; ce qui varie est
  **laquelle**, et ce choix vit dans l'**état**.
- ⚠️ **pas d'hystérésis, et c'est assumé** : elle rendrait l'unité affichée
  dépendante de l'HISTOIRE, donc deux modules côte à côte pourraient afficher
  deux unités pour la même valeur. Le clignotement est honnête.
- 🔴 **L'unité était concaténée à TROIS endroits** (`composer()`,
  `detail_reparametrer`, la table de `widget`). Tant qu'il n'y avait qu'une
  unité par grandeur, les trois disaient la même chose. La bascule l'a révélé
  **à la première mesure** : la console imprimait « 100,0 **Mb/s** » sur une
  valeur convertie en Gb/s — **fausse d'un facteur mille**, dans l'instrument
  qui sert à vérifier. ⇒ `dn_widget_unite()`, une définition, trois appelants.
- ⚠️ `DISQUE` a la même forme (`99999,9 Mo/s`) et le mécanisme est **prêt** —
  ⛔ **non armé** : l'owner a nommé `RÉSEAU`. Legs explicite.

### 18.6 LES TROIS RÉGIMES, SUR LE FIRMWARE LIVRÉ

`ms/cyc` = **copie + attente**, publiées **séparément** (§17.9 avait oublié
l'attente et publié un `duty` divisé par 8 sous le titre « Aucune dérive »).

| régime | cyc/s | flush/cyc | flush/s | px/cyc | plus gr. aire | copie µs/flush | attente µs/flush | ms/cyc | duty |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **(a) repos** | 0,214 | 1,00 | 0,214 | 36 675 | **36 675** | 3 033 | 6 181 | **9,21** | — |
| **(b) 5 tr/s, espacement 4 ms** | 2,194 | 2,34 | 5,13 | 85 712 | **36 675** | 3 067 | 16 062 | **44,71** | **9,81 %** |
| **(b′) 5 tr/s, espacement 40 ms** | 3,154 | 1,63 | 5,15 | 59 630 | **36 675** | 3 076 | 12 386 | **25,25** | **7,96 %** |

✅ **La plus grande aire vaut EXACTEMENT `225 × 163 = 36 675`** dans les trois
régimes. ⛔ **61 440 aurait signifié que le draw buffer scinde, 74 880 que les
bandes sont actives.**
✅ **Test de réconciliation** (somme des tâches = CPU global × 2) : **écart
+0,00 pt**. `taskLVGL` **22,73 pt**, `console_repl` 2,80, `dn_link` **1,04**
(contre 0,49 — le parseur v3 lit plus de champs), CPU global **13,88 %**.
✅ **La prédiction sur la SURFACE est tenue** : aire/flush **34 948 → 36 675 =
+4,9 %** contre **+4,5 %** prédits ; copie/flush **+5,3 %**.
✅ **« Les grandeurs supplémentaires sont GRATUITES en pixels »** est CONFIRMÉ :
l'aire par flush vaut exactement `CASE_W × CASE_H`, quel que soit le nombre de
labels — le groupage invalide bien le conteneur.

### 18.7 NON-RÉGRESSION — ⚠️ DEUX COLONNES, DEUX SHA, ET LE LIVRÉ EST `db5fcb8`

🔴 **`690af25` N'EST PAS LE FIRMWARE LIVRÉ.** Il est publié ici parce que c'est
lui qui porte les trois régimes de §18.6, et parce que la différence entre les
deux colonnes **EST le prix du remède de §18.9** — la lire comme une régression
serait l'inverse de ce qu'elle dit.

| grandeur | T0 `cfd1a54` | `690af25` (bounce 4 800) | **LIVRÉ `db5fcb8`** (bounce 7 680) | écart T0 → livré |
|---|---:|---:|---:|---|
| binaire | 917 824 o | 938 112 o | **939 296 o** | +21 472 (**+2,34 %**), partition **78 % libre** |
| RAM interne libre | 104 119 o | 103 503 o | **92 203 o** | **−11 916 o (−11,4 %)** — ⚠️ dont **−11 520 pour le bounce**, **−396 pour le modèle** |
| PSRAM libre | 7 768 236 o | 7 768 236 o | **7 768 236 o** | **0** |
| tas LVGL | 20 476 o (33 %) | 20 508 o (34 %) | **20 504 o (34 %)** | +28 o |
| plus gros bloc | 40 744 o | 40 752 o | **40 752 o** | +8 o |
| fragmentation | 3 % | 3 % | **2 %** | −1 pt |
| tas sur 80 transitions | — | −28 o | **20 468 → 20 476 = +8 o** | **PLAT** |
| `fps 15` | 37,40 Hz | 37,40 Hz | **37,40 Hz** | **0,00 %** |
| boot | 2 311 ms | 2 327 ms | **2 321 ms** | +10 ms (+0,4 %) |
| latence `nav ab 40` | 333,8 (n=40) | 334,6 (n=80) | **335,2 ms (n=80)** | +1,4 ms — **dans le bruit de ±16 ms** |
| `bounce_px` | 4 800 | 4 800 | **7 680** | 🔴 **correction de défaut** (§18.9) |

🔴 **LES −11,4 % DE RAM INTERNE SONT DOMINÉS PAR LE BOUNCE BUFFER, PAS PAR LE
MODÈLE** : −11 520 o pour la marge DMA contre −396 o pour tout le reste
(`GRANDEURS_MAX` 2→4, `connue[]`, `echelle_haute[]`, `dn_link_etat_m_t` élargi,
la démo). ⛔ Le chiffre se lit, il ne se suppose pas.

⚠️ **Le coût RAM était annoncé à ~+300 o ; il vaut −616 o de libre**, soit deux
fois l'estimation, qui ne comptait que `txt[][]` et `brut[]` : il faut y ajouter
`connue[]`, `echelle_haute[]`, les `dn_link_etat_m_t` élargis et la démo.
✅ **D4** : les seuls `nvs_*` hors `dn_bootcfg.c` sont dans `desknode_main.c`, au
**BOOT** (`nvs_flash_init`) — ⛔ aucun sur un chemin de régime. Vérifié par grep.

### 18.8 CE QUI RESTE OUVERT — ⛔ ÉCRIT COMME MANQUANT, PAS COMME TENU

> 🔴 **LA SÉANCE POST-REVUE DU 2026-08-19 (firmware `1156eac`) A FERMÉ QUATRE DE
> CES LIGNES PAR LA MESURE — voir §18.10.** Elles sont **conservées telles
> quelles ci-dessous**, avec leur état d'origine : c'est la règle du dépôt, et
> c'est aussi ce qui rend lisible *pourquoi* elles étaient ouvertes. Le verdict
> à jour de chacune est en §18.10.

- **La campagne tactile en visant les jauges.** D12 a périmé toutes les
  coordonnées publiées. **Formule contrôlée contre un relevé déjà publié avant
  de faire viser quoi que ce soit** : elle reproduit `y = 340..350` (dn4-1) sur
  l'ancienne géométrie. **Nouvelle bande de la jauge `RAM` : `y = 337..347`,
  `x = 22..223`.** ⏳ 36 appuis / 36 relâches / **0 erreur I²C** relevés, mais
  **les ZONES n'ont pas été tracées** — ⛔ la garde « toute la case est la zone
  tactile » n'est donc **pas** re-prouvée sur la nouvelle géométrie.
- ⚠️ **CONTRADICTION DE COMPTAGE, RELEVÉE PAR LA REVUE DU 2026-08-19 ET NON
  TRANCHÉE** : cette section publie **36 appuis / 36 relâches**, la story publie
  **16 appuis sur la jauge / 32 appuis / 32 relâches**. Deux artefacts de la même
  campagne, deux comptes. ⛔ **Aucun des deux n'est corrigé ici** : la capture
  n'existe plus, et choisir au jugé serait fabriquer un chiffre. *« Un chiffre
  publié se relit »* — celui-ci se **re-relève**, en même temps que les zones.
- ✅ **Le smoke owner 6/6 est FAIT** — verbatim owner *« ok cohérent »*
  (2026-08-19), consigné dans la story. ⚠️ Cette ligne le listait comme OUVERT,
  et le tracker aussi : **trois artefacts, deux états**. Corrigé par la revue du
  2026-08-19 en faveur de celui qui porte une PREUVE (le verbatim daté).
- 🔴 **LE RÉGIME (c) D'AC12 N'A JAMAIS ÉTÉ REJOUÉ, ET CE MANQUE N'ÉTAIT ÉCRIT
  NULLE PART** (revue du 2026-08-19). AC12 exige les **trois** régimes
  (a) / (b) / (c) sur un seul SHA lu au bandeau. §18.6 publie (a), (b) à 4 ms et
  (b′) à 40 ms : **(b′) n'est pas (c)** — c'est un second tir de (b). Le T0
  §17.10 donne (c) à **6,00 flush/cyc et 210 600 px**, et rien ne s'y compare.
  ⚠️ **ET L'INSTRUMENT DE (c) N'ÉTAIT PLUS ÉQUIVALENT AU T0** : `widget rafale`
  passe par `pousser_nolock()`, qui posait **2 grandeurs** (`.n = 2`) là où le
  régime réel en pose **3** — il ne redessinait donc pas le même travail tout en
  prétendant s'y comparer. ✅ **Corrigé** (revue du 2026-08-19, `pousser_nolock`
  pose désormais `desc_n(idx)` grandeurs) ⇒ **(c) est rejouable, et il reste à
  le rejouer.**
- 🔴 **TROIS GARDES EXIGÉES NOMMÉMENT PAR AC13 NE SONT NI MESURÉES NI DÉCLARÉES
  MANQUANTES** (revue du 2026-08-19) : le **témoin négatif d'AC8** (`widget nue` —
  « la case nue mesure quasiment pareil dans les deux branches »), **« barre et
  MENU = zones mortes / 0 tap »**, et la colonne **`dn_capteurs`** de la table de
  non-régression.
- **La voie (b)** — la 3ᵉ police n'est pas générée ; son verdict de lisibilité
  reste inaccessible.
- **`FAN_RPM`** — qualifié, sans place. **Dette de PLACE, ⛔ pas question
  ouverte de source.**

### 18.9 🔴 LA FAMINE DMA, TROISIÈME OCCURRENCE — ET L'AGRESSEUR EST L'USB

> **Ceci amende §11.4 et §11.5.** Constat owner du 2026-08-19, verbatim :
> *« l'image entière glisse d'un cran et se recale vers le bas, ensuite tous les
> chiffres clignotent une fois, et rebelote »*, **une fois par seconde**, dès que
> des données PC arrivent à 5 trames/s **et** que les cases se repeignent.

§11.4 avait établi deux régimes : le bounce buffer **gagne contre l'I²C**, il
**perd contre l'écriture flash**. ⛔ **L'USB n'avait jamais été testé.** C'en est
le troisième régime.

#### CE N'EST PAS UN COUPABLE, C'EST UN SEUIL — ONZE TESTS À UNE VARIABLE

| test | glisse ? |
|---|---|
| mock 1 Hz, 4 cases, **aucun trafic série** | **non** |
| AMBIANCE toutes les 5 s (BME680), sans série | **non** |
| trafic série 5/s, **checksum FAUX** (⇒ zéro dessin) | **non** |
| trafic série 5/s **+ dessin** | 🔴 **OUI** |
| firmware **`cfd1a54` (dn4-1)**, même stimulus | **non** |
| firmware `dn4-6`, **géométrie de dn4-1** (35 100 px) | 🔴 OUI |
| firmware `dn4-6`, chemin de MAJ de dn4-1 (`widget replacer off`) | 🔴 OUI |
| firmware `dn4-6`, **2 grandeurs** (même compte de labels) | 🔴 OUI |
| firmware `dn4-6`, trames **v2** (même volume d'octets) | 🔴 OUI |
| fond en **PSRAM** au lieu de flash mmap | 🔴 OUI |
| compteur de **synchros expirées**, 45 s d'injection | **0** |

⇒ **Ni le dessin seul, ni le trafic seul : leur CONJONCTION.** Et **aucun test à
une variable ne supprime le défaut** — c'est la signature d'un **seuil franchi
par ACCUMULATION**, pas d'un coupable identifiable.
⛔ **AUCUN INSTRUMENT NE LE COMPTE** : zéro synchro expirée, et `fps` rend
**37,40 Hz** — or §11.4 écrit déjà que **`fps` est AVEUGLE à ce défaut**. La
bissection se paie donc en constats owner, et il faut le savoir avant de
commencer.

#### LE REMÈDE : LA MARGE

`DN_DEFAULT_BOUNCE_PX` **4 800 → 7 680** px (10 → **16 lignes**).
**Plus petite valeur *légitime* qui tienne** — il n'existe **aucune** valeur
admissible entre 4 800 et 7 680.

| grandeur | bounce 4 800 | **bounce 7 680** | écart |
|---|---:|---:|---|
| RAM interne libre | 103 503 o | **92 203 o** | **−11 300 o** |
| `fps 15` | 37,40 Hz | **37,40 Hz** | **0** |
| boot | 2 327 ms | **2 321 ms** | −6 ms |
| latence `nav ab 40` (n=80) | 290,9 / **334,6** / 398,8 | 288,2 / **335,2** / 398,7 | **+0,6 ms** |
| tas sur 80 transitions | −28 o | +8 o | **PLAT** |

🔴 **ET ÇA CORRIGE UNE LECTURE DE §11.5.** Elle impute **+160 ms de latence** au
bounce buffer ; passer de 10 à 16 lignes coûte **+0,6 ms** — rien de mesurable,
et bien à l'intérieur du bruit de **±16 ms** chiffré en §18.0.
⇒ **Les 160 ms sont le prix d'AVOIR un bounce, ⛔ pas de sa TAILLE.**

#### 🔴 ET LA GARDE DE `bounce_px` VÉRIFIAIT LE MAUVAIS INVARIANT

En testant **6 400** (13,33 lignes), constat owner : *« image décentrée sur la
droite »*. Un bounce qui n'est pas un **nombre entier de lignes** termine chaque
morceau **au milieu d'une ligne** ⇒ décalage **horizontal** permanent.

`bounce_px_refus()` n'exigeait que *« diviser les pixels d'une trame »*.
⚠️ **Sur les 17 valeurs qu'elle acceptait, DIX cassaient l'image** : 2560, 3072,
3200, 4096, 5120, 6144, 6400, 10240, 12288, 12800.
🔴 **ET CETTE ÉNUMÉRATION ÉTAIT FAUSSE — corrigée par la revue de code du
2026-08-19.** Elle annonçait « les **sept** légitimes : 2400, 3840, 4800, 7680,
9600, 15360, 19200 ». **Il y en a DOUZE** (plus le zéro). La garde combinée est
`v ≤ 38400` ∧ `307200 % v == 0` ∧ `v % 480 == 0`, c'est-à-dire `v = 480 × k` avec
`k` diviseur de 640 et `k ≤ 80` :

✅ **Les douze légitimes** : **480, 960, 1920**, 2400, 3840, 4800, **7680**, 9600,
15360, 19200, **30720, 38400** — soit 1, 2, 4, 5, 8, 10, **16**, 20, 32, 40, 64
et 80 lignes. Les cinq oubliées sont acceptées par le code et n'apparaissaient
nulle part. ⛔ **Une liste présentée comme EXHAUSTIVE et qui ne l'est pas est un
instrument qui ment** — la même famille que le compteur décoratif de `dn_link.h`.
✅ **En revanche la sous-affirmation qui porte la conclusion TIENT** : **aucune
valeur admissible entre 4 800 et 7 680** (5 760 = 480 × 12, et 12 ∤ 640). **7 680
reste donc la plus petite valeur LÉGITIME qui tienne.**
⛔ Le piège était armé pour quiconque réglerait ce paramètre, et il s'est
déclenché **à la première tentative de le régler**. Un réglage refusé est une
gêne ; un réglage **ACCEPTÉ** qui casse l'image en silence est un défaut.
⚠️ Le commentaire de la garde **décrivait déjà** le mécanisme (*« sinon la DMA se
décale d'un reliquat à chaque trame »*) — le test ne le couvrait qu'à moitié.
⇒ Corrigé : `v % DN_LCD_H_RES == 0`. Vérifié : `set bounce 6400` est **refusé**.

#### CE QU'IL FAUT SAVOIR POUR LA SUITE

⚠️ **LA MARGE EST FRANCHIE, PAS CONFORTABLE.** `dn4-2` branche trois capteurs
I²C — **le PREMIER agresseur connu de §11.4**. ⇒ **ce stimulus est à REJOUER en
`dn4-2`**, et le bounce peut avoir à monter encore.
⚠️ **Non vérifié avec l'agent PC réel** : l'exclusivité `WSL ↔ COM3` l'interdit
tant que la carte est attachée à WSL. Même chemin de code, ⛔ pas le même
émetteur.
✅ Deux correctifs posés en chemin **augmentent aussi la marge**, et sont donc
justifiés deux fois : la suppression des 15 `lv_obj_set_pos()` inutiles par
seconde, et celle des 15 `lv_text_get_size()` inutiles par seconde.

---

### 18.10 SÉANCE POST-REVUE DE CODE — firmware `1156eac`, SHA LU AU BANDEAU

> **Séance du 2026-08-19, APRÈS la revue de code adversariale 3 couches.**
> 33 correctifs appliqués (`b2db419` → `1156eac`), `git status --porcelain`
> **vérifié VIDE avant le flash** — ⚠️ c'est la première fois de cette story que
> le bandeau porte le SHA du commit **sans rattrapage**, la règle qu'AC14 pose et
> que `ce41caf` avait violée pour la 3ᵉ fois du dépôt.

#### 18.10.1 🔴 LES TROIS RÉGIMES, SUR **UN SEUL SHA** — CE QU'AC12 EXIGE

⚠️ **§18.6 publiait (a) et (b) sur `690af25` ; (c) n'existait pas.** Relever (c)
seul sur `1156eac` aurait produit exactement la coupure que §18 vient de se
reprocher (décision ② de la revue). Les trois sont donc **rejoués ensemble**.

**RÉGIME (a) — repos, aucune injection, fenêtre de 30 s :**

| grandeur | T0 §17.10 (`b5cd141`) | **`1156eac`** | verdict |
|---|---:|---:|---|
| flush / cycle | 1,00 | **1,00** | ✅ |
| cycles/s | 0,216 | **0,200** | ✅ |
| plus grande aire | 35 100 | **36 675** | = `225 × 163` |
| copie µs/flush | 2 740 | **2 946** | **+7,5 %** |

**RÉGIME (b) — 5 trames/s, `--espacement 4 ms`, 30 s, 150 trames émises :**

| grandeur | T0 §17.10 | `690af25` (tir 4 ms) | **`1156eac`** | verdict |
|---|---:|---:|---:|---|
| flush/s | 5,17 | 5,13 | **5,37** | ✅ |
| cycles/s | 2,056 | 2,194 | **2,30** | ✅ |
| flush/cycle | 2,52 | 2,34 | **2,33** | ✅ |
| px/cycle | 88 069 | 85 712 | **85 575** | ✅ −2,8 % |
| copie µs/flush | 2 913 | 3 067 | **3 032** | ✅ |
| plus grande aire | 35 100 | 36 675 | **36 675** | ✅ |

⚠️ **L'ESPACEMENT EST DÉCLARÉ, ET C'EST LA CORRECTION QUE §18.6 APPORTE À §17.10** :
ces colonnes **ne sont pas des propriétés du firmware seul**, elles dépendent du
rythme de l'émetteur — le même binaire a rendu −32 % de `px/cyc` rien qu'en
passant de 4 à 40 ms.

✅ **LIAISON, régime (b)** : **149 valides sur 150 émises** · 0 doublon ·
**1 perte de seq** · 0 resynchro · **0 rejet de toute cause** (tronquée, trop
longue, checksum, version, format, bornes).

**LES DEUX TÉMOINS DE NON-RÉGRESSION D'AC13, REJOUÉS SUR `1156eac` :**

| témoin | émises | valides | doublons | **pertes seq** | rejets |
|---|---:|---:|---:|---:|---:|
| **v1** (le dialecte de `dn2-2`) | 15 | **15** | 0 | **0** | **0** |
| **v2** (le dialecte de `dn4-1`) | 75 | **75** | 0 | **0** | **0** |

🔴 **ET CES DEUX ZÉROS SONT AUSSI LA PREUVE D'UN CORRECTIF DE LA REVUE.**
`tools/dn_injecteur.py` incrémentait `seq` **avant** le `continue` qui saute les
métriques inconnues de la v1 : l'émetteur produisait seq 1, 6, 11… et le firmware
comptait `pertes_seq += saut - 1`, soit **QUATRE pertes fabriquées par cycle**.
Sur cette campagne de 15 cycles, l'ancien injecteur aurait affiché **~56 pertes**
— sur le témoin de non-régression lui-même. ⛔ Un compteur pollué par l'émetteur
ne prouve rien sur le récepteur ; celui-ci rend maintenant **0**.

#### 18.10.2 🔴 LE RÉGIME (c) — RELEVÉ POUR LA PREMIÈRE FOIS

AC12 exige **trois** régimes ; §18.6 n'en publiait que deux, (b′) n'étant qu'un
second tir de (b). Et son instrument était **cassé** : `pousser_nolock()` posait
`.n = 2` là où le régime réel en pose 3, donc `widget rafale` redessinait deux
labels par case au lieu de trois — il ne mesurait pas le travail auquel il
prétendait se comparer. Corrigé (`desc_n(idx)`), puis relevé.

⚠️ **LE PROTOCOLE A DÛ ÊTRE CORRIGÉ EN COURS DE ROUTE, ET C'EST LE POINT DE
MÉTHODE DE CETTE SÉANCE.** Premier tir : `flush reset` → settle 3 s → rafale →
settle 3 s → `flush` ⇒ **10 flushes / 5 cycles = 2,0 flush/cyc**, très loin des
6,00 du T0. ⛔ Avant d'en conclure quoi que ce soit, **témoin négatif** : la même
fenêtre **sans rafale** rend **3 flushes / 3 cycles**. La fenêtre était donc trop
longue et mesurait la rafale **plus le fond** (`AMBIANCE` toutes les 5 s, la
barre). Fenêtre resserrée, et le témoin rejoué à la même durée :

| | flushes | cycles | aire cumulée |
|---|---:|---:|---:|
| rafale, tir 1 | 7 | 2 | 256 725 px |
| rafale, tir 2 | 7 | 2 | 256 725 px |
| rafale, tir 3 | 7 | 2 | 256 725 px |
| **témoin, même fenêtre, SANS rafale** | **1** puis **0** | **1** puis **0** | 36 675 puis 0 |

⇒ **la rafale seule vaut 7 − 1 = 6 flushes en 2 − 1 = 1 cycle.**

| grandeur | T0 §17.10 (`b5cd141`, case 156) | **`1156eac` (case 163)** | écart |
|---|---:|---:|---|
| **flush / cycle** | **6,00** | **6,00** | **0** ✅ la fusion tient |
| **px / cycle** | 210 600 | **220 050** | **+4,49 %** |
| **plus grande aire** | 35 100 | **36 675** | = `225 × 163` **exactement** |
| copie µs/flush | 2 915 | **2 992** (3003 / 2972 / 3001) | +2,6 % |
| attente | 47,79 ms/cyc | ⛔ **NON PUBLIÉE** | voir ci-dessous |

✅ **Le +4,49 % de px/cycle est EXACTEMENT le rapport de surface de D12**
(163/156 = 1,0449) : la géométrie coûte ce qu'elle mesure, et rien de plus.
✅ **36 675 = `CASE_W × CASE_H`** ⛔ ni **61 440** (le draw buffer scinderait) ni
**74 880** (les bandes seraient actives) — les deux témoins que la prédiction
d'AC12 nommait.
⛔ **L'`attente` n'est PAS publiée** : 76 / 85 / 91 ms cumulés sur trois tirs
**strictement identiques** (7 flushes, 2 cycles, même aire au pixel près), soit
±20 % de dérive de phase vsync. La story l'interdit nommément — *« conclure sur
`flush/cyc`, JAMAIS sur des `attente_us` de fenêtres différentes »*.
⛔ **Le CPU reste « — »**, comme au T0 : une rafale unique est trop courte pour
déplacer un compteur cumulé. Ce n'est pas un oubli, c'est une limite d'instrument.

#### 18.10.3 ✅ LES TROIS TÉMOINS D'AC2 — DANS UNE SEULE SÉQUENCE

T2 laissait décoché *« VÉRIFIER le clamp livré par `dn4-1` (n = 5 sur MAX = 4) »*,
et pour cause : la séquence qui le déclenche était **inerte**. `dn_ui_demo_set()`
ne construisait que si la démo n'existait pas encore, donc `widget demo on` puis
`widget demo on 5` ne rejouait **aucun** `dn_widget_creer()` — pendant que la
console imprimait « AFFICHEE — n = 5 ». Corrigé par la revue (reconstruction quand
`n` change), et joué **sur une démo déjà posée** :

```
« DÉMO 2+JAUGE » : 5 grandeurs demandees, 4 posees — 1 PERDUE(S)
« DÉMO 2+JAUGE » : 1 valeur(s) sur 4 DEBORDENT la case — bas 203 > h=163 …
                   LVGL les CLIPPE sans un mot
« DÉMO 2+JAUGE » : pas de place pour la JAUGE (y_bas=208 + 6 + 10 > h=163)
                   — La jauge est ABANDONNEE (valeurs > jauge > secondaire)
« DÉMO 2+JAUGE » : pas de place pour la ligne secondaire … Texte PERDU
```

✅ **Le clamp de `dn4-1`** — vérifié, ⛔ pas réécrit, exactement ce qu'AC2 exige.
✅ **La jauge bornée ET journalisée** — AC2 preuve n°1, la « 3ᵉ occurrence » du
ledger, prise sur le fait.
✅ **Le débordement de valeur** — le compteur que `dn4-6` a dû ajouter parce que
le clamp *« compte les grandeurs DEMANDÉES, pas celles qui TIENNENT »*.
✅ **La règle de priorité se lit dans l'ordre des trois logs** : les valeurs sont
posées (une clippée, et elle le DIT), puis la jauge cède, puis la secondaire.

#### 18.10.4 ✅ LE TÉMOIN NÉGATIF D'AC8 — VERT, ET CHIFFRÉ

Garde exigée par AC13 et **jamais mesurée** jusqu'ici. Une case rendue **NUE**
(`widget nue 4 on`) doit être **insensible au groupage** — sinon l'A/B d'AC8
mesure autre chose que le widget. Cinq poussées par branche, fond soustrait :

| branche | px par mise à jour (case NUE) |
|---|---:|
| `widget groupe on` | **3 805** · **3 866** |
| `widget groupe off` | **3 785** · **3 896** |

⇒ écart **< 3 %** : la case nue ne voit pas le groupage. ✅
🔴 **Et le contraste porte la conclusion d'AC8** : une case **widget** coûte
**36 675 px/maj** (le conteneur est invalidé d'un bloc) contre **~3 850** pour une
case nue — **facteur 9,5**. C'est ce facteur que le groupage achète.

#### 18.10.5 ✅ LA CAMPAGNE TACTILE, ENFIN **TRACÉE** — la garde passe du COMPTE à la ZONE

§18.8 le disait en toutes lettres : *« la garde est corroborée par le compte, pas
prouvée par la zone »*. `touch trace 90000` imprime **chaque appui avec sa
coordonnée** :

```
fin de trace : 37 appui(s), 20 tap(s) sur zone.  (17 hors zone)
```

| phase | appuis | coordonnées relevées | taps |
|---|---:|---|---:|
| **jauge de `RAM`** | 10 | `y = 326..347` · `x = 58..203` | **10 → TAP sur RAM** |
| retours (bouton RETOUR) | 11 | `y = 9..36` | 10 |
| **BARRE** | 8 | `y = 15..26` · `x = 32..389` | **0** |
| **MENU** | 8 | `y = 602..633` | **0** |

✅ **« Toute la case est la zone tactile » (dn1-4 AC4)** : les dix appuis visant
**la jauge** ont tous ouvert `RAM`, **y compris ceux tombés à `y = 326`**, donc
**au-dessus** de la bande calculée `337..347`. La formule d'AC11 n'est plus
seulement contrôlée contre un relevé publié : elle est **contrôlée par l'usage**.
✅ **« Barre et MENU = zones mortes » (dn1-4 AC3 / dn3-1 AC4 / dn3-2 AC5)** :
**16 appuis, 0 tap**, avec leurs `y` qui disent où ils sont tombés. ⛔ Ce n'est
plus « l'owner n'a rien signalé », c'est seize coordonnées hors zone, comptées.
✅ **0 erreur I²C** sur la campagne.

⚠️ **UN FAIT QUE SEULE LA TRACE POUVAIT DONNER** : l'appui n°8, à **`y = 9`**, n'a
**rien déclenché** — il est passé **au-dessus** du bouton RETOUR, et l'owner l'a
rejoué sans le savoir. Ce n'est pas un défaut de la garde ; c'est la marge haute
du bouton, et elle n'était visible dans aucun compteur.

🔴 **ET ÇA SOLDE LA CONTRADICTION 32/32 CONTRE 36/36 — PAR REMPLACEMENT, PAS PAR
ARBITRAGE.** Les deux comptes d'origine (story : 16 appuis / 32-32 · §18.8 :
36/36) portaient sur une campagne **non tracée** dont la capture n'existe plus :
⛔ aucun des deux n'est déclaré vainqueur, et aucun n'est corrigé. Ils sont
**périmés** par une campagne qui, elle, publie ses coordonnées.

#### 18.10.6 NON-RÉGRESSION SUR `1156eac` — au BOOT, ⛔ pas après la campagne

| grandeur | `db5fcb8` (livré) | **`1156eac`** | écart |
|---|---:|---:|---|
| binaire | 939 296 o | **943 712 o** | +4 416 (**+0,47 %**), partition **78 % libre** |
| RAM interne libre | 92 203 o | **92 315 o** | **+112 o** |
| PSRAM libre | 7 768 236 o | **7 768 236 o** | **0** |
| tas LVGL utilisé | 20 504 o (34 %) | **20 496 o (34 %)** | −8 o |
| plus gros bloc | 40 752 o | **40 752 o** | **0** |
| fragmentation | 2 % | **2 %** | **0** |
| tas sur 80 transitions | +8 o | **20 496 → 20 476 = −20 o** | **PLAT** ✅ |
| `fps 15` | 37,40 Hz | **37,40 Hz** | **0,00 %** |
| latence `nav ab 40` (n=80) | 288,2 / **335,2** / 398,7 ms | 291,1 / **334,4** / 396,7 ms | **−0,8 ms**, dans le bruit de ±16 ms |
| `dn_capteurs` | — | **BME680 VIVANT** · 61 lectures · 0 reprise · 0 reconfiguration · 0 erreur (i²c/donnée/bornes) · cadence **4 999 ms mesurés** pour 5 000 nominale · cycle 26 ms | ✅ colonne exigée par AC13, **jamais publiée avant** |

🔴 **UN PIÈGE ÉVITÉ, ET IL MÉRITE D'ÊTRE ÉCRIT.** Le premier relevé de tas, pris
**après** la campagne, donnait `plus gros bloc 24 724 o` et **`fragmentation
40 %`** contre 40 752 o et 2 % sur `db5fcb8`. Publié tel quel, c'était une
régression spectaculaire — et **fausse** : les chiffres de référence sont pris
**au boot**, et dix navigations, quatre rafales, des bascules `nue` et trois
changements de géométrie fragmentent le tas. Re-relevé après un boot propre :
**40 752 o et 2 %, identiques au pixel près.** ⚠️ *Un chiffre faux mais plausible
est plus dangereux qu'un chiffre absurde* — celui-là était les deux à la fois.

#### 18.10.7 CE QUI RESTE, APRÈS CETTE SÉANCE

- ⏳ **La voie (b)** — la 3ᵉ police n'est toujours pas générée ; son verdict de
  lisibilité reste inaccessible. **Inchangé.**
- ⏳ **`FAN_RPM`** — qualifié, sans place. **Dette de PLACE**, au ledger.
- ⏳ **Le défaut de §18.9 avec l'agent PC RÉEL** — l'exclusivité `WSL ↔ COM3`
  l'interdit tant que la carte est attachée à WSL. Même chemin de code, ⛔ pas le
  même émetteur. **À rejouer en `dn4-2`, avec l'I²C en plus.**
- 🟡 **`widget rafale` récite encore « 6 × 35 100 px »** dans son propre mode
  d'emploi — l'aire d'**avant D12**. Un opérateur qui suit cette consigne calcule
  210 600 et conclut que la mesure est fausse, alors que la valeur juste est
  **220 050**. Même famille que le « 156 px » en dur que dn4-6 a supprimé de
  `dn_console.c`. ⇒ **porté au ledger**, ⛔ pas corrigé en séance : changer le
  code aurait changé le SHA au milieu des relevés.

---

## 19. `dn4-9` (P9.3d) — LA **SÉLECTION** DEVIENT UNE PROPRIÉTÉ DU MODÈLE DE WIDGET

> **Ce que cette section ajoute à §15 et §16, ⛔ sans les réécrire** : le modèle de widget de §15
> décrit une case qui dessine ses grandeurs **`0..n-1` dans l'ordre**. C'était exact, et ça ne
> l'est plus. `dn4-9` ajoute au modèle **une SÉLECTION D'INDICES** et **un SECOND COMPTE**.
> ⚠️ **§0 EST INCHANGÉE** — aucune ligne de la configuration de référence n'a bougé : cette story
> ne touche **ni la géométrie, ni la police, ni le pipeline**. Vérifié ligne à ligne, ⛔ pas au
> jugé : c'est le point noir récurrent de ce fichier, relevé **trois stories de suite**.
> ⛔ **AUCUN CHIFFRE MESURÉ ICI.** Cette section décrit un **mécanisme**. Les largeurs, le coût
> RAM, le fps et la latence exigent la carte et sont **DUS** (voir §19.4).

### 19.1 Ce qui change dans le TYPE, et pourquoi le rang cesse d'être l'index

`dn_widget_desc_t` gagne deux champs :

| champ | sens | défaut |
|---|---|---|
| `sel_p1[DN_WIDGET_GRANDEURS_MAX]` | `sel_p1[rang]` = index de grandeur **+ 1** — ce que la **CASE** dessine | tout à zéro ⇒ **IDENTITÉ** |
| `n_detail` | ce que le **DÉTAIL** montre : les grandeurs `0..n_detail-1`, **dans l'ordre du fil** | `0` ⇒ « comme la case » |

🔴 **L'INDICE ÉTAIT **TRIPLE** ET CONFONDU** : rang d'affichage = entrée de descripteur = slot
d'état. La sélection découple **le premier** des deux autres, ⛔ **jamais les deux autres entre
eux** : `grandeurs[g]` et `etat->txt[g]` décrivent **toujours** la même grandeur. C'est
l'invariant qui rend le mécanisme sûr, et c'est pour lui que la traduction est faite **dans le
module qui dessine** (`dn_widget_sel()`) plutôt qu'en permutant l'état chez l'appelant — permuter
l'état aurait désaligné la case du détail, qui n'ont pas la même sélection.

⚠️ **LE DÉCALAGE DE 1 EST LA CONVENTION DU DÉPÔT** (`DN_VAL_ABSENTE`,
`DN_PREC_NON_RENSEIGNEE`, `k_pc[].idx_p1`), ⛔ pas une astuce locale. Sans lui, un `{0,0,0,0}`
implicite signifierait *« les rangs 0 à 3 dessinent TOUS la grandeur 0 »* — quatre fois la même
ligne, **en silence**, sur **cinq cases sur six**.

### 19.2 🔴 LA MISE À JOUR N'EST PAS LA CONSTRUCTION — et c'est le piège du module

`dn_widget_maj()` ⛔ **NE parcourt PAS `0..n-1`** : elle parcourt les **QUATRE** slots et filtre
par `if (!w->valeur[i]) continue;`. **Le garde-fou est le POINTEUR, pas le compte.** Sa boucle
porte donc bien un **rang**, et il faut lui appliquer **la même traduction** qu'à la création.
Sans elle, la case aurait affiché la bonne grandeur à la construction puis **une autre dès la
première mise à jour** — 5 fois par seconde, **sans un log**.

⚠️ **Et il y avait un second bord au même piège, hors de ce module** : `build_dashboard()` passait
une **copie** du descripteur (icône A/B + compte) tandis que `case_poser()` passait
`&k_desc[idx]`, le descripteur **brut**. Deux descripteurs différents pour un même widget — ça
marchait **par accident**, tant que rang = index. ⇒ **`desc_effectif()`** : une seule fabrique, les
deux chemins la prennent.

### 19.3 ⛔ CE QUE LA GÉOMÉTRIE N'AUTORISE TOUJOURS PAS

Rien de §15 n'est amendé sur ce point, et il décide du périmètre :

| lignes empilées | bas de la dernière | verdict |
|---|---|---|
| 2 | `48 + 1×40 + 35 = 123` | ✅ tient (`DISQUE` passe à deux) |
| **3** | `48 + 2×40 + 35 = 163` | ✅ tient — **PILE** sur `DN_UI_CASE_H = 163` (D12) |
| **4** | `48 + 3×40 + 35 = 203` | ⛔ **ENTIÈREMENT hors case** |

⇒ ⛔ **Aucune case ne passe à quatre.** `CPU` reste à **trois lignes** ; ce qui change, c'est
**LESQUELLES** (`[0, 1, 3]`). Le **DÉTAIL**, lui, a la place : **deux lignes de 35 px** dans un
panneau de **97** (porté de 62 à 97 en `dn4-6`, les 35 px pris **au placeholder de courbe**, dont
le bas reste à **370**).

🔴 **ET LA LEÇON DE `dn4-6` VAUT ENCORE, MOT POUR MOT** : une règle de mise en page **dimensionnée
sur UNE case et appliquée aux SIX est une extrapolation**. Trois par ligne, dimensionné sur `GPU`,
avait fait déborder `CPU` de **74 px, clippés EN SILENCE par LVGL** — et **c'est l'œil de l'owner
qui l'a vu**, ⛔ pas l'arithmétique. ⇒ Les largeurs de `dn4-9` se mesurent **sur les SIX cases**,
⛔ pas sur les deux qu'elle modifie.

### 19.4 🎯 LES LARGEURS, **MESURÉES SUR LA DALLE** LE 2026-08-22

**Firmware `4c3a3f7`** (SHA **lu au bandeau**), `widget largeur`, police `dn_font_28`.
⚠️ **Mesurées AVANT le flash de `dn4-9`**, et c'est légitime : `widget largeur` mesure une **chaîne
libre** dans la police liée — elle ne dépend pas du descripteur. ✅ **Témoin de calibration** :
`« c.max 100,0 % »` rend **197 px**, exactement le chiffre publié en `dn4-6`.

🔴 **DEUX LARGEURS UTILES, ET AUCUNE N'EST CELLE DES COMMENTAIRES** :
- **CASE : 201 px** (rendu par `widget largeur` lui-même).
- **DÉTAIL : 432 px** — `widget detail` rend `panneau 460, x 14` ⇒ `460 − 2×14`.
  ⛔ **Les « 446 px » des commentaires sont FAUX** : ils valent `460 − 2×7` et datent d'un `x`
  antérieur. *Relire, ⛔ ne pas croire* — la story avait raison de l'exiger.

| chaîne | px | contre | verdict |
|---|---|---|---|
| `c.max 100,0 %` | **197** | 201 | ✅ **témoin** — le chiffre de `dn4-6` est reproduit |
| `10000 tr/min` (nu) | **183** | 201 | ✅ marge **18 px** |
| `1358 tr/min` (réel) | 157 | 201 | ✅ |
| `10000 rpm` (nu) | 154 | 201 | ✅ |
| 🔴 `100000,0 Mo/s` | **206** | 201 | ⛔ **DÉBORDE — défaut LIVRÉ, jamais vu** |
| `2999,9 Mo/s` | **167** | 201 | ✅ — ce que l'échelle armée rend |
| `999,9 Mb/s` | 152 | 201 | ✅ (ancien seuil) |
| `2999,9 Mb/s` | **168** | 201 | ✅ (seuil owner à 3000) |
| `99999,9 Mb/s` | 186 | 201 | ✅ *(sans l'icône ↓ ; avec, `dn4-1` mesure 202)* |
| ⛔ `extr.moy 10000 tr/min` | **315** | 201 | ⛔ **+114 px** |
| ⛔ `extr 10000 tr/min` | 247 | 201 | ⛔ +46 |
| ⛔ `ext 10000 tr/min` | 235 | 201 | ⛔ +34 |
| ⛔ `ext 10000 rpm` | 206 | 201 | ⛔ +5 |
| ⚠️ `EX 10000 rpm` | 200 | 201 | ✅ … pour **1 px** |

⇒ 🔴 **AUCUN PRÉFIXE LISIBLE NE TIENT DANS LA CASE.** Il reste **18 px** après `10000 tr/min`,
soit **moins d'un caractère**. ⛔ Ce n'est pas un libellé à raccourcir, c'est un **mur**.

**Le DÉTAIL, à DEUX par ligne** (⚠️ **bornes BASSES** — voir le défaut d'instrument en §19.6) :

| ligne | px | contre 432 | verdict |
|---|---|---|---|
| `100,0 % · 100,0 GHz` (CPU l1) | ≥ 292 | 432 | ✅ |
| `c.max 100,0 % · 150,0 °C` (CPU l2) | ≥ 342 | 432 | ✅ |
| `1000 W · 10000 tr/min` (GPU l2) | ≥ 338 | 432 | ✅ |
| ⛔ `2999,9 Mo/s · extr.moy 10000 tr/min` | ≥ **530** | 432 | ⛔ **+98** |
| ⛔ `100000,0 Mo/s · extr.moy 10000 tr/min` | ≥ 569 | 432 | ⛔ +137 |
| ⛔ `ventirad 10000 tr/min · boitier 10000 tr/min` | ≥ **642** | 432 | ⛔ **+210** |
| `10000 tr/min · 10000 tr/min` **NU** | 414 | 432 | ✅ … mais **indistinguables** ⛔ |
| `ventirad 10000 rpm · boitier 10000 rpm` | ≥ 584 | 432 | ⛔ +152 |
| `CPU 10000 rpm · BOIT 10000 rpm` | ≥ 504 | 432 | ⛔ +72 |

⇒ 🔴 **« DEUX PAR LIGNE » EST MORT POUR `DISQUE`, QUELS QUE SOIENT LES LIBELLÉS.** Le budget pour
**deux** préfixes est de `432 − 414 = **18 px**` — zéro caractère. ⛔ **Raccourcir ne sauve pas** :
ce n'est pas le nom qui déborde, c'est la **règle de mise en page**.

**Le DÉTAIL, à UNE par ligne** — la voie retenue :

| ligne | px | contre 432 | marge |
|---|---|---|---|
| `2999,9 Mo/s` | 167 | 432 | **265** |
| `extr.moy 10000 tr/min` | 315 | 432 | **117** |
| `ventirad 10000 tr/min` | 309 | 432 | **123** |
| `boitier 10000 tr/min` | 285 | 432 | **147** |

✅ **Marge minimale 117 px, libellés français COMPLETS.**

### 19.5 🔴 LES TROIS DÉCISIONS OWNER DU 2026-08-22, PRISES SUR CES CHIFFRES

1. **« Pour les unités on ne dépasse pas 3 000, après on change l'affichage de l'unité M puis G. »**
   ⇒ `net[0]`/`net[1]` : seuil **1000,0 → 3000,0 Mb/s**. `disk[0]` : **échelle ARMÉE**
   (`3000,0 Mo/s → Go/s`), ce qui **AMENDE un legs explicite de `dn4-6`** (*« l'owner a nommé
   RÉSEAU »*).
   🎯 **Et la mesure lui donne raison** : `« 100000,0 Mo/s »` fait **206 px pour 201** — la
   grandeur 0 de `DISQUE` **débordait déjà**, en silence, et **personne ne l'avait vu**.
   ⚠️ **Exemption NOMMÉE, ⛔ pas silencieuse** : les quatre `tr/min` (plafond 10000) n'ont **aucun
   préfixe M/G qui se lise** — `« 10,0 k tr/min »` serait **plus long** que `« 10000 tr/min »`.
   Elles sont **listées par la gate** à chaque tir.
2. **Le détail montre UNE grandeur par ligne quand deux ne tiennent pas.** ⇒ `detail_cols = 1` sur
   `DISQUE`. **Facture : 43 px repris au placeholder de COURBE** (165 → **122 px**), bas inchangé
   à 370. ⇒ **`dn4-4` dessinera dans 122 px.**
3. **La case `DISQUE` ligne 2 porte un `tr/min` NU.** Le nom vit au **détail**, qui a la place.
   ⇒ `prefixe_detail_seul` — et **les gardes jugent désormais chaque vue avec SES étiquettes**,
   sinon une case qui n'affiche pas le préfixe serait jugée comme si elle l'affichait.

### 19.6 ⚠️ UN DÉFAUT D'INSTRUMENT DE CETTE SÉANCE — LE MIEN

🔴 **LE REPL DE LA CARTE MANGE LES OCTETS NON-ASCII.** `dn_console.py` envoie pourtant de l'UTF-8
(`ser.write(…encode("utf-8"))`, vérifié dans la source) — c'est le côté carte qui filtre, en mode
« dumb » (*« Your terminal application does not support escape sequences »*).
**Symptôme** : `widget largeur "c.max 100,0 % · 150,0 °C"` s'échoue
`« c.max 100,0 %      150,0 C »` — **le `·` ET le `°` ont disparu**.
⇒ **Toutes les largeurs de lignes de DÉTAIL ci-dessus sont des BORNES BASSES.** Les largeurs de
CASE, elles, sont **ASCII pures donc EXACTES**.
⛔ **Ne pas « corriger » en ajoutant la largeur manquante au jugé** : ce serait fabriquer un nombre
plausible. ✅ **L'instrument exact est `widget detail`**, qui relit le texte **réellement composé
par le firmware** — il exige donc le flash.
⚠️ **Et c'est le sens de la conclusion** : les bornes basses **suffisent à trancher** (642 ≥ 432
est déjà un refus), ⛔ elles ne suffiraient **pas** à valider un cas serré.

### 19.7 ⏳ CE QUI EST **DÛ** ET QUI EXIGE LE FLASH

✅ **Les largeurs sont FAITES** (§19.4) — c'est ce que la séance du 2026-08-22 a soldé sans flash.
⛔ **Ce qui reste ne peut pas s'obtenir autrement qu'en posant le firmware sur la dalle.**

| à mesurer | instrument | pourquoi ça ne se calcule pas |
|---|---|---|
| le texte **réellement composé** par le détail, avec ses `·` | `widget detail` | ⚠️ le REPL mange les non-ASCII (§19.6) ⇒ les largeurs de détail sont des **bornes basses**. Seul le firmware compose la vraie chaîne |
| que la case `CPU` dessine bien `[%, GHz, °C]` | `pc $DN,…` (témoin v3) + **l'œil** | ⛔ **ÉCHEC si « 88,0 °C » apparaît** — le `c.max` d'un agent v3 pris pour une température |
| que `DISQUE` à deux ne déborde pas | **absence** de l'`ESP_LOGW` + compteur `débordements` | ✅ **déjà obtenu par l'override** le 2026-08-22 (`widget grandeurs 4 2` ⇒ **0 débordement**), ⏳ **à re-confirmer sur le descripteur livré** |
| les **trois** compteurs de géométrie | `widget` **nu** (lecture pure, dn4-9) | ⛔ jamais additionnés : trois diagnostics distincts |
| Δ`mem`, Δ`cpu brut`, Δ`fps`, Δ latence | `mem` · **`cpu brut`** · `fps 15` · `nav ab 40` | ⛔ **jamais `cpu N`** : `cmd_cpu` bloque le REPL, **et le REPL EST le transport PC** |
| que les gardes REFUSENT ce qu'elles doivent | `widget grandeurs 4 3` / `4 4` / `3 2` | ⚠️ **l'attendu s'est INVERSÉ deux fois** — voir §19.9 |

### 19.8 🔴 CE QUE LA SÉANCE A TROUVÉ SUR LA GARDE — ET ELLE DISCULPE `dn4-8`

**`widget grandeurs 4 4` a été ACCEPTÉE** sur la carte, alors que le ledger de `dn4-8` l'annonce
**REFUSÉE**. ⛔ **Ce n'est PAS une régression** : `desc_ligne_indistincte` **n'existe pas** dans le
firmware installé — `git show 4c3a3f7:…/dn_ui.c | grep -c desc_ligne_indistincte` rend **0**,
contre **3** à `cdfe88c`. La garde est arrivée par la **revue du 2026-08-21**, c'est-à-dire
**après** le flash de `4c3a3f7`.
⇒ 🔴 **La colonne « AVANT » du tableau d'AC6 n'est PAS observable sur cette carte** : aucun
firmware qui refuse n'y a jamais été posé. Le ledger de `dn4-8` le disait
(*« la garde n'est pas validée sur la carte — elle exige un FLASH »*) ; la séance le **confirme
par la mesure**, et corrige un tableau qui présentait un état comme observable.

✅ **Et l'override a rendu trois mesures que rien d'autre n'aurait données** :

| commande | log | ce qui est PROUVÉ |
|---|---|---|
| `widget grandeurs 4 4` | `bas 203 > h=163` · **1 en HAUTEUR** | 🎯 le `203 > 163` est **mesuré**, ⛔ plus cité de `dn4-6` |
| `widget grandeurs 4 3` | 0 débordement | 3 lignes tiennent — **pile** (`163 = 163`) |
| `widget grandeurs 4 2` | 0 débordement | 🎯 **AC4 : `y_bas = 128 ≤ 163`**, par l'**absence** du log |

### 19.9 ⚠️ L'ATTENDU DES GARDES A CHANGÉ **DEUX FOIS** — le lire avant de conclure

| commande | `4c3a3f7` (installé) | `cdfe88c` (revue `dn4-8`) | après `dn4-9` |
|---|---|---|---|
| `widget grandeurs 4 4` | ✅ acceptée *(garde absente)* | ⛔ refusée | ⛔ **refusée** — la CASE montrerait 3 `tr/min` **nus** |
| `widget grandeurs 4 3` | ✅ acceptée | ⛔ refusée | ⛔ **refusée** — 2 `tr/min` nus dans la case |
| `widget grandeurs 4 2` | ✅ acceptée | ✅ acceptée | ✅ **acceptée** — `Mo/s` + un seul `tr/min` |
| `widget grandeurs 3 2` (`net`) | ✅ acceptée | ✅ acceptée | ✅ **acceptée** — les icônes ↓/↑ séparent |

🔴 **LE RENVERSEMENT DE `4 4` ET `4 3` EST UNE CONSÉQUENCE DIRECTE DE LA DÉCISION OWNER n°3**, et
il est **VOULU** : puisque la case n'affiche **plus** les préfixes, deux `tr/min` y seraient
**indistinguables à l'œil**. ⛔ Une garde qui les accepterait parce que le *descripteur* porte des
préfixes jugerait un écran qui n'existe pas.
⚠️ **C'est exactement pour ça que `desc_ligne_indistincte()` prend une VUE** — et c'est le
correctif que la mesure du 2026-08-22 a rendu obligatoire.

### 19.10 ⛔ CE QUE `dn4-9` NE TOUCHE PAS

- ⛔ **La COURBE et le MIN/MAX restent des placeholders** — réponse **explicite** au legs de
  `dn4-8` (*« `dn4-9` doit dire lequel elle comble, si elle en comble un »*) : **AUCUN**. Motif :
  les deux demandent un **historique en RAM de session**, qui est le livrable de **`dn4-4`** (P9.4)
  avec le budget des **< 300 ms** qu'il porte. Y ajouter un historique **sans** ce budget serait
  aggraver la dette qu'on va payer.
  ⛔ **Écrire « MIN 12 % · MAX 91 % » parce que le panneau a l'air vide** serait refaire le défaut
  qu'on solde.
- ⛔ **Ni `DN_WIDGET_GRANDEURS_MAX` ni `DN_LINK_GRANDEURS_MAX` ne bougent.**
- ⛔ **La grille reste à SIX cases, et `DISQUE` garde son titre.** D13 amende D8 sur sa **portée
  Ring0**, ⛔ pas sur son **choix de case**.
- ⛔ **L'échelle haute de `DISQUE` (`Mo/s → Go/s`) n'est PAS armée** — mécanisme prêt depuis
  `dn4-6`, legs explicite (*« l'owner a nommé RÉSEAU »*). Au ledger avec son chiffre.

### 19.11 🎯 SÉANCE CARTE DU 2026-08-22, **APRÈS FLASH** — firmware `38c3b99`

**SHA lu au bandeau `App version: 38c3b99`**, ⛔ pas déduit du dépôt, sans `-dirty`, arbre
`porcelain` **vide** au moment du flash. `SPI Flash Size : 16MB`.

#### L'audit de boot, qui a cessé de mentir

```
selections : 6 cases auditees, 0 faute (dn4-9 — invariants A/B/C)
precision d'affichage : 6 cases auditees, 0 trou (AC9)
k_desc[CPU]      : case 3 [0, 1, 3] · detail 4 [0, 1, 2, 3] · peuplees 4 — `widget grandeurs 0 <1..4>` jouable
k_desc[GPU]      : case 3 [0, 1, 2] · detail 4 [0, 1, 2, 3] · peuplees 4 — `widget grandeurs 1 <1..4>` jouable
k_desc[RAM]      : case 1 [0]       · detail 1 [0]          · peuplees 1 — `widget grandeurs 2 <1..1>` jouable
k_desc[RÉSEAU]   : case 2 [0, 1]    · detail 2 [0, 1]       · peuplees 2 — `widget grandeurs 3 <1..2>` jouable
k_desc[DISQUE]   : case 2 [0, 1]    · detail 4 [0, 1, 2, 3] · peuplees 4 — `widget grandeurs 4 <1..2>` jouable
k_desc[AMBIANCE] : case 2 [0, 1]    · detail 2 [0, 1]       · peuplees 2 — `widget grandeurs 5 <1..2>` jouable
```

⇒ Il annonce **`4 <1..2>`** pour `DISQUE`, ⛔ plus « `widget grandeurs 4 4` est jouable ». Et il le
dit **en interrogeant les mêmes gardes** que le setter, ⛔ pas en recopiant leur raisonnement.

#### AC6 — les gardes, SUR LA CARTE

| commande | verdict | motif rendu par le firmware |
|---|---|---|
| `widget grandeurs 4 4` | ⛔ **REFUSÉE** | *« dans la vue **CASE**, la grandeur 2 porterait l'unité "tr/min" DÉJÀ présente sans préfixe ni icône **QUI Y SOIT AFFICHÉ** »* |
| `widget grandeurs 4 3` | ⛔ **REFUSÉE** | idem |
| `widget grandeurs 4 2` | ✅ **ACCEPTÉE** | `[0, 1]` · 0 chevauchement · 0 trop large · 0 en hauteur |
| `widget grandeurs 3 2` (`net`) | ✅ **TOUJOURS ACCEPTÉE** | 🎯 **le témoin qui compte** — les icônes ↓/↑ séparent |

🔴 **`4 4` et `4 3` sont REFUSÉES, ⛔ pas acceptées — et c'est CONTRAIRE à ce que la story d'AC6
écrivait.** La décision owner du 2026-08-22 (`tr/min` **nu** dans la case) inverse l'attendu :
puisque la case n'affiche plus les préfixes, deux `tr/min` y seraient indistinguables. Une garde
qui les accepterait parce que le **descripteur** porte des préfixes jugerait **un écran qui
n'existe pas**.

#### AC5 — les SIX détails, largeur **ET** hauteur, sur le texte RÉELLEMENT composé

Utile **432 px** en largeur, **154 px** en hauteur (label posé à `y = 14`).
⚠️ Ces chiffres-là portent leurs `·` et leurs `°` : ils viennent du **firmware**, ⛔ pas du REPL.

| case | texte relu | largeur | hauteur | marge |
|---|---|---|---|---|
| CPU | `100,0 % · 5,7 GHz` / **`c.max 100,0 % · 100,0 °C`** | 365 | 84 | 70 |
| GPU | `100,0 % · 95,0 °C` / **`350 W · 3000 tr/min`** | 317 | 84 | 70 |
| RAM | `99,9 %` | 89 | 49 | 105 |
| RÉSEAU | **`100,0 Gb/s · 100,0 Gb/s`** | 346 | 49 | 105 |
| **DISQUE** | **`100,0 Go/s` / `extr.moy … ` / `ventirad … ` / `boitier … `** | 296 | **154** | **0** |
| AMBIANCE | `24,1 °C · 53,6 %` | 234 | 49 | 105 |

✅ **Zéro `ESP_LOGW` de débordement**, largeur comme hauteur.
🎯 **Le `c.max` du CPU et le `tr/min` du GPU sont VISIBLES pour la première fois.**
🎯 **`100,0 Go/s` et `100,0 Gb/s`** : la règle des 3000 tourne sur la dalle.
⚠️ **La marge de `DISQUE` est de 0 px en hauteur** — c'est le minimum EXACT, choisi pour ne pas
prendre à `dn4-4` un pixel de plus. ⛔ Une grandeur de plus, ou une police plus haute, et ça
déborde : la garde de hauteur le dira, elle existe maintenant.
⚠️ **`--jeu pire` de l'injecteur n'est PAS le plafond du protocole** : il sert `3000 tr/min` là où
`k_metriques[]` autorise `10000`. Le vrai pire cas a été mesuré **séparément**, par
`widget largeur` : `extr.moy 10000 tr/min` = **315 px** ≤ 432. ⛔ Ne pas conclure du seul injecteur.

#### AC3 — le témoin de non-régression v3, et le piège évité

`pc $DN,3,<seq>,1000,cpu,520,32,880*<XOR recalculé>` — un agent **v3 NON MODIFIÉ**, `cpu` à
**TROIS** valeurs, ⛔ sans °C :

```
CASE   :  0  CPU  WIDGET  RÉELLE   52,0 %  3,2 GHz  --   | case [0, 1, 3] · detail 4
DÉTAIL :  « 52,0 %   ·   3,2 GHz \n c.max 88,0 %   ·   -- »
```

🎯 ⛔ **AUCUN « 88,0 °C ».** C'est **exactement** le chiffre faux mais plausible que l'index 3
existe pour empêcher, et sur lequel **`rejets_bornes` n'aurait pas bronché** (plafond 1500 des deux
côtés). Le `c.max` est **au détail**, la °C absente **dit `--`**.
⚠️ **PIÈGE N°10 PRIS EN FLAGRANT DÉLIT, ET C'EST LE MIEN** : le premier tir a été **REJETÉ** parce
que j'ai **recopié** un checksum au lieu d'utiliser celui que je venais de calculer. *« Une trame de
test copiée peut être FAUSSE — recalculer le XOR avant d'accuser. »*
⚠️ **Et la péremption est à 3 s** : lire la case après coup rend `ABSENTE`. La trame et la lecture
doivent tenir dans la **même invocation**, et ça a demandé un essai. ⛔ Un « `--` » n'est pas une
preuve d'échec tant qu'on n'a pas montré que la valeur était encore vivante.

#### AC7 — la non-régression, MESURÉE

| contrôle | T0 (`4c3a3f7`) | après (`38c3b99`) | verdict |
|---|---|---|---|
| PSRAM libre | 7 768 024 o | **7 768 024 o** | ✅ **0** |
| RAM interne libre | 90 807 o | **90 127 o** | **−680 o** |
| `fps 15` | 37,40 Hz (+0,00 %) | **37,40 Hz** (−0,00 %) | ✅ **0,00** |
| `touch` erreurs I2C | 0 | **0** | ✅ |
| les **trois** compteurs, après `--jeu pire` 12 s | — | **0 · 0 · 0** | ✅ en **LECTURE PURE** |
| `RAM` jauge + secondaire | `OUI OUI` | **`OUI OUI`** | ✅ la case à risque n'a pas bougé |
| `GPU` case | 3 | **3** | ✅ ⛔ pas quatre |
| `nav ab 40` | *(pas de T0)* | **n=80, moy 335,8 ms** (281,2 / 400,9) | ✅ **pas de régression** |

⚠️ **`nav ab` se juge contre les campagnes PUBLIÉES**, ⛔ pas contre un T0 : `dn1-4` **307,0** ·
`dn3-1` **321,8** · `dn3-2` **349,1** · `dn4-1` **335,0** · `dn4-6` **333,8**. À **335,8**, c'est
**+2,0 ms** sur la plus proche — dans l'étalement inter-campagnes. ⛔ **Et le critère n°3 du brief
(< 300 ms) reste NON TENU** : c'est le budget de `dn4-4`, ⛔ pas celui de cette story.
🔴 **LE PROTOCOLE DES TROIS COMPTEURS EST DÉSORMAIS EXÉCUTABLE**, et c'est un livrable :
`widget largeur reset` → stimulus → **`widget` nu**, qui les rend **sans rien reconstruire ni
remettre à zéro**. Avant, les lire DÉTRUISAIT ce qu'on relève.

#### AC9 — la prédiction confrontée, ⛔ y compris là où elle n'est pas testable

| # | prédiction (écrite le 2026-08-22 **avant le premier tir**) | mesure | verdict |
|---|---|---|---|
| 1 | Δ tas LVGL **−200 à −600 o** | — | 🔴 **NON TESTABLE — MA FAUTE** : la prédiction nomme `ui`/`lv_mem_monitor()`, et **je n'en ai pas relevé le T0**. Un instrument nommé dans une prédiction et jamais joué au T0 rend la prédiction indécidable |
| 2 | Δ `cpu brut` **≤ +0,2 point** | — | 🔴 **NON TESTABLE — MA FAUTE** : `cpu brut` est un compteur CUMULÉ, il exige deux relevés, et **le T0 manque** |
| 3 | Δ `fps` **0,0 ± 0,2 Hz** | **0,00 Hz** | ✅ **TENUE** |
| 4 | Δ latence **+0 à +5 ms** | **+2,0 ms** vs `dn4-6` | ✅ **TENUE** |
| 5 | Δ RAM interne libre **inchangée à ±2 ko** | **−680 o** | ✅ **TENUE** |
| 6 | 🔴 **« `trop larges` sera ≥ 1 sur `DISQUE`, la ligne 1 du détail DÉBORDERA »** | **0 débordement** | 🎯 **DÉMENTIE — et c'est la plus instructive** |

🎯 **POURQUOI LA N°6 EST DÉMENTIE, ET CE QUE ÇA APPREND.** Elle était **juste sur les faits et
fausse sur la conclusion**. La ligne 1 du détail `DISQUE` **débordait bien** — 530 px pour 432,
mesuré — et elle ne déborde plus **parce que DEUX décisions owner l'ont fait disparaître en tant
que ligne** : la règle des 3000 (`100000,0 Mo/s` → `100,0 Go/s`) et une grandeur par ligne. ⛔ Le
défaut n'a pas été « absorbé », il a été **supprimé**. ⚠️ Mon extrapolation
(`nb_caractères × largeur_moyenne`, à partir d'un seul point) **avait raison par accident** : elle
prédisait 40 caractères ⇒ débordement, et la mesure a donné 530 px. ⛔ **Ça ne la valide pas** —
elle aurait tout aussi bien pu se tromper, et c'est pour ça qu'elle était écrite comme une
PRÉDICTION et jamais comme un résultat.

⚠️ **DEUX PRÉDICTIONS SUR SIX SONT INDÉCIDABLES PARCE QUE J'AI OUBLIÉ LEUR T0.** ⛔ Ce n'est pas un
détail de protocole : une prédiction qu'on ne peut pas confronter ne coûte rien à celui qui
l'écrit, et c'est exactement ce que l'exigence « prédire AVANT » sert à empêcher. ⇒ **au ledger.**

---

## 20. 🔴 LE SAUTILLEMENT SOUS TRAFIC PC — DOSSIER OUVERT LE 2026-08-22

> ⛔ **CE N'EST PAS UN DÉFAUT DE `dn4-9`, ET C'EST PROUVÉ PAR A/B.** Il est consigné ici parce que
> la séance de `dn4-9` l'a **rencontré**, **reproduit** et **caractérisé** — pas parce qu'elle l'a
> causé. Il touche le **différenciateur du brief** (la liaison PC) **en usage normal**.

### 20.1 Le symptôme, dans les mots de l'owner

> *« l'image sautille, elle se décale chaque seconde de quelques mm vers le bas puis vers le haut »*
> *« 10 sec les cases du haut, puis l'image se décale une fois, et au bout de 40 c'est aléatoire
> mais ça commence à saturer, donc sautiller »*

⚠️ **Deux précisions obtenues en le lui demandant, et elles décident du diagnostic** :
1. **TOUTE l'image bouge, décor Living PCB et cadres compris** — ⛔ ce n'est **pas** du
   repositionnement de label. L'hypothèse de `dn4-6` (*« `lv_obj_set_pos` 15 fois par seconde »*)
   est donc **RÉFUTÉE comme cause de CE symptôme**, et son commentaire disait lui-même qu'elle
   était *« une HYPOTHÈSE, pas une certitude »*.
2. **Rien ne bougeait avant que le trafic démarre.** L'image est **stable** au repos.

### 20.2 🎯 LA SIGNATURE TEMPORELLE — ce que le dépôt n'avait pas

Sous `dn_injecteur.py --jeu reel` (5 trames/s, le régime de l'agent) :

| t | ce qui se voit |
|---|---|
| **~10 s** | les cases **DU HAUT** |
| puis | l'image se décale **UNE FOIS**, en entier |
| **~40 s** | **aléatoire**, ça « sature » |

🎯 **« D'abord le haut » N'EST PAS UN DÉTAIL** : le panneau RGB balaie **de haut en bas**. Un
tampon qui se vide se voit donc **d'abord en haut de la trame**. ⚠️ C'est ce qui oriente vers la
**famine du bounce buffer**, et pas vers le contenu dessiné.

### 20.3 🔴 CE QUI EST ÉLIMINÉ — A/B SUR LA MÊME DALLE, LE MÊME FIRMWARE, LA MÊME TEMPÉRATURE

⛔ **Pas de reflash, et c'est ce qui rend l'A/B propre** : `widget grandeurs` rejoue l'ANCIEN
dashboard **dans le firmware courant** — c'est exactement ce pour quoi cette commande existe.

| bras | dashboard | résultat à l'œil |
|---|---|---|
| **dn4-9** | `CPU [0,1,3]` · `DISQUE` à **2** | saute à **~10 s** |
| **avant dn4-9** | `CPU [0,1,2]` (`widget grandeurs 0 3`) · `DISQUE` à **1** (`4 1`) | saute à **~10 s** |

⇒ ⛔ **LA CHARGE DE PIXELS N'EST PAS EN CAUSE.** Un label de moins redessiné 5 fois par seconde ne
change **ni le moment ni la nature** du symptôme.

⚠️ **CE QUE CET A/B NE FERME PAS, ET IL FAUT LE DIRE** : les deux bras tournent sur du code
`dn4-9`. Restent actifs le formatage élargi de `dn_ui_pc_maj()` (borné par `desc_peuplees()` au
lieu de `desc_n()`) et la copie de descripteur de `case_poser()`. Une poignée de `snprintf` par
seconde ne peut **pas plausiblement** déplacer une marge DMA — ⛔ **mais « plausiblement » n'est pas
« mesuré »**. **Le seul test qui ferme les derniers pourcents est le flash de `cdfe88c`.**

### 20.4 🔴 AUCUN INSTRUMENT DE CE FIRMWARE NE SAIT VOIR CE DÉFAUT

C'est **le fait le plus important de ce dossier**, et il conditionne toute investigation future :

| instrument | pourquoi il est aveugle |
|---|---|
| `fps N` | compte les **vsync**, et *« un compteur vsync tourne MÊME écran noir »*. Il rend **37,40 Hz** pendant que l'image saute |
| `flush` | mesure le **chemin de flush** (aire, copie, attente), ⛔ **pas le remplissage du bounce buffer** |
| `dn_recal` | **INERTE dans ce build** : `CONFIG_LCD_RGB_RESTART_IN_VSYNC=y` ⇒ le driver relance à chaque VBlank et **ne lit jamais** le bit posé |
| `widget largeur` / `detail` | géométrie de texte — hors sujet |
| `mem` | RAM interne 90 127 → 89 315 → **89 179 o** sur ~10 min de trafic. La baisse **DÉCÉLÈRE** ⇒ ça ressemble à une **stabilisation**, ⛔ pas à une fuite qui s'emballe. ⚠️ **Trois points ne sont pas une tendance** |

⇒ 🎯 **L'ŒIL DE L'OWNER EST LE SEUL INSTRUMENT**, et c'est pour ça que ce défaut a pu vivre
jusqu'ici sans être caractérisé. ⛔ **Toute investigation doit COMMENCER par se donner un
instrument** — sans quoi elle mesurera autre chose et conclura de travers.
**Piste** : `esp_lcd_rgb_panel` expose `on_bounce_empty` / `on_bounce_frame_finish`. Un compteur
d'événements de bounce, publié par `flush` ou `fps`, rendrait le défaut **CHIFFRABLE**.
⚠️ `dn_ui.c:3804` mentionne déjà `on_bounce_frame_finish` — **le crochet existe**, il n'est pas
instrumenté.

### 20.5 Ce que le dépôt savait déjà, et ce que cette séance ajoute

**Savait** — ledger, `dn4-6` §18.9 : *« LA FAMINE DMA A UN TROISIÈME AGRESSEUR — L'USB — ET LA
MARGE EST FRANCHIE, PAS CONFORTABLE. »*
**Ajoute** : un **protocole de reproduction** (`dn_injecteur.py --jeu reel --secondes 120`), une
**signature temporelle** (~10 s / décalage isolé / ~40 s aléatoire), la **localisation** (le haut
d'abord), l'**élimination** de la charge de pixels, et le constat qu'**aucun instrument ne le voit**.

### 20.6 ⛔ CE QUI N'EST PAS FAIT

- ⛔ **La cause n'est PAS établie.** « Famine du bounce buffer » est une **HYPOTHÈSE** orientée par
  le balayage haut→bas, ⛔ pas une mesure.
- ⛔ **Le rôle de la TEMPÉRATURE n'est pas testé.** La carte tournait depuis ~1 h. *« Au bout de
  40 s ça sature »* est compatible avec un effet thermique **comme** avec une simple montée en
  régime. ⇒ un tir **à froid**, après les 40 s de garde du bus, reste dû.
- ⛔ **Le flash A/B sur `cdfe88c` n'est pas fait** — il ferme les derniers pourcents.
- ⛔ **`num_fbs=2` n'est pas rejoué** : la config de référence est `num_fbs=1`, et §4bis décrit un
  défaut DIFFÉRENT à `num_fbs=2`. ⛔ Ne pas les confondre.

---

### 20.7 🎯 `dn4-10`, 2026-08-23 — LE DOSSIER PASSE DE « CARACTÉRISÉ » À **« CHIFFRÉ »**

> ⛔ **AJOUT.** §20.1 à §20.6 restent **justes pour leur date** et ne sont pas retouchés. Ce qui
> suit les **complète** et, sur deux points, les **corrige** — les corrections sont signalées.

**Firmwares** : `24f3891` → `f07177c` → `256a49e` → **`3cc7412`**, SHA **lus au bandeau**.

#### 20.7.1 ⛔ TROIS VOIES FERMÉES PAR LA LECTURE DU DRIVER — ne pas les rouvrir

| voie | pourquoi elle est fermée | référence, IDF **v5.5.5** |
|---|---|---|
| **`on_bounce_empty`** | 🔴 appelé **UNIQUEMENT** sous `if (unlikely(panel->num_fbs == 0))`. Nous sommes à **`num_fbs = 1`** ⇒ il **ne sera jamais appelé**. Et l'activer voudrait dire **REMPLACER** la copie du driver, ⛔ pas l'observer | `esp_lcd_panel_rgb.c:899-906` |
| **L'interruption d'underrun MATÉRIELLE** | `LCD_LL_EVENT_UNDERRUN` n'est définie que pour l'**ESP32-P4**. Le **S3 ne l'a pas** — et le driver n'en ferait qu'un `ESP_EARLY_LOGE` | `hal/esp32p4/include/hal/lcd_ll.h:31` · `esp_lcd_panel_rgb.c:1255` |
| **La détection de famine du driver** | `bb_eof_count < expect_eof_count` est dans le **`#else`** de `CONFIG_LCD_RGB_RESTART_IN_VSYNC`. Nous sommes à **`=y`** ⇒ 🔴 **ce test n'existe pas dans notre binaire**, et son compteur n'y est jamais remis à zéro | `esp_lcd_panel_rgb.c:1153-1166` |

#### 20.7.2 🎯 LE MÉCANISME, ÉCRIT PAR LE DRIVER LUI-MÊME

> *« reset the GDMA channel every VBlank to stop permanent desyncs […] **if this interrupt is LATE
> ENOUGH, the display will SHIFT** as the LCD controller already read out the first data bytes, and
> resetting DMA will **re-send those**. »* — `esp_lcd_panel_rgb.c:1142-1148`

⇒ Le glissement **n'est pas un octet manquant** : c'est le **rattrapage au VBlank** d'un remplissage
qui a décroché. Et l'owner l'a décrit **exactement** : *« ça s'abaisse puis revient »* — les octets
**renvoyés** décalent l'image **vers le bas** de leur propre nombre, sur **une** trame.

#### 20.7.3 🎯 POURQUOI `fps` EST AVEUGLE — la réponse, enfin

§11.4, §18.9 et la séance du 2026-08-22 le **constatent** trois fois sans l'expliquer.
🔴 **`fps` MOYENNE** : 561 trames sur 15 s, et la division **efface la gigue**. Toute l'information
est **dans la gigue**, et personne ne l'avait regardée. ⛔ Ce n'est donc pas un défaut de `fps` : il
compte des vsync, et il les compte juste.

#### 20.7.4 🔴 L'INSTRUMENT — ET IL A FALLU DEUX PASSES, L'ŒIL AYANT PRIS LA PREMIÈRE EN DÉFAUT

**Passe 1 — la comptabilité des enroulements** (`manques` / `doubles`).
✅ **Témoin PROUVÉ** par `flash on` (l'ISR de remplissage est **masquée** pendant l'effacement de
secteur, `ISR_IRAM_SAFE=n`) : **1 037 trames sans enroulement sur 1 041**, contre **0** au repos.
⚠️ **Et ça ferme la question ouverte de §5.3** : la combinaison `bounce_px ≠ 0` + stimulus flash,
marquée *« JAMAIS JOUÉE »*, est **jouée** — elle est **catastrophique** pour le bounce.

🔴 **PUIS L'ŒIL A DIT NON.** Agent **RÉEL**, 180 s, `bounce_px = 7 680` : `manques = 0`, gigue max
**+16 µs** — pendant que l'owner voyait *« un glissement de quelques pixels vers le BAS, ça s'abaisse
puis revient, quasiment toutes les secondes »*.

**Passe 2 — LA PHASE `enroulement → VSYNC_END`.** C'est sa phrase qui l'a produite :

| ce qu'il a dit | ce que ça a appris |
|---|---|
| **« quelques pixels »** | 🔴 à 16 MHz **1 pixel = 62,5 ns**. Les seuils de la passe 1 (100 µs, 775 µs) valent **1 600** et **12 400 pixels**. Le compteur ne mentait pas — **il ne regardait pas** |
| **« toutes les secondes »** | l'agent pousse **une rafale par seconde** ⇒ défaut **synchrone de la rafale** |
| **« s'abaisse puis revient »** | mot pour mot le mécanisme du driver ci-dessus |

🎯 **`phase = t_vsync − t_enroulement`.** L'enroulement tombe à un point **fixe** du balayage (la DMA
avance à cadence matérielle) ; le `VSYNC_END` est servi par une **ISR qui peut être retardée**.
⇒ **Une phase COURTE = un enroulement EN RETARD = le remplissage du bounce qui décroche.**

⚠️ **Et les seuils de la passe 2 ont dû être corrigés eux aussi, dans la séance** : référencés au
**minimum**, ils comptaient **6 660 trames sur 6 725** sous trafic et **0** au repos. Le **mode est
en HAUT** ; les écarts vont **vers le bas**. Re-référencés au **MAXIMUM**.

🎯 **LE SEUIL N'EST PAS UN NOMBRE MAGIQUE** : c'est l'écoulement d'un **DEMI-BOUNCE**, lu sur le
panneau **réellement monté** et **annoncé par le firmware au boot**.

| `bounce_px` | lignes | **écoulement d'un demi-bounce** |
|---:|---:|---:|
| 7 680 | 16 | **620 µs** |
| 9 600 | 20 | **775 µs** |

⚠️ **DEUX ANGLES MORTS, ÉCRITS À CÔTÉ DU CHIFFRE** : plancher à la **microseconde** (16 px) ⇒ ⛔ « 0 »
ne veut pas dire « 0 pixel » ; et l'horodatage de référence vient **lui aussi** d'une ISR ⇒ un retard
**commun aux deux** s'annule et reste invisible.

#### 20.7.5 🎯 CE QUE LA PHASE MESURE — trois régimes, fenêtres de 180 s IDENTIQUES

| régime | phase min | moy | MAX | **déficit pire** | 🔴 CORRUPTION |
|---|---:|---:|---:|---:|---:|
| **repos, zéro trafic** | 1 915 | 1 961 | 1 978 | **63 µs** | **0** |
| injecteur 5 tr/s | 1 249 | 1 955 | 1 990 | **741 µs** | ~128 |
| **agent RÉEL de la tour** | 1 248 | 1 943 | 2 010 | **762 µs** | — |

🔴 **Facteur 12 entre repos et trafic**, là où `manques`, la gigue vsync **et** `fps` sont **tous à
zéro**. ✅ **Contrôle** : l'injecteur, ⛔ **sans aucune manipulation USB**, rend le même chiffre que
l'agent ⇒ le déficit n'est **pas** un artefact du detach/attach.

🎯 **ET LA CORRÉLATION AVEC L'ŒIL EST QUANTITATIVE** :

| config | compteur | mots de l'owner |
|---|---|---|
| 7 680 | **0,71 corruption/s** | *« quasiment toutes les secondes »* |
| 9 600 | **0,195 corruption/s** | *« un peu mieux, toutes les 2-3 secondes »* |
| repos | **0** | image stable |

⚠️ **Et son *« c'est bon 10 s, ensuite ça tombe »* est une donnée, pas un détail** : le défaut vient
**par RAFALES**. C'est ce qui rend une **fenêtre unique NON DISCRIMINANTE** — dispersion **×3,7**
mesurée à config identique (0,195 à 0,72 /s à `9 600`).

#### 20.7.6 Le balayage de `bounce_px` — fenêtres de 90 s identiques

| `bounce_px` | lignes | RAM interne libre | `manques` / 3 386 |
|---:|---:|---:|---:|
| 480 | 1 | 119 303 o | **477** (14,1 %) |
| 960 | 2 | 117 387 o | **103** |
| 1 920 | 4 | 113 543 o | **95** |
| 3 840 | 8 | 105 835 o | **81** |
| **7 680** | 16 | 89 019 o | **0** |
| **9 600** | 20 | 82 215 o | **0** |

🎯 **Genou de `manques` entre 3 840 et 7 680.** ✅ **La loi `4v` est vérifiée à ≤ 28 o** sur trois pas
consécutifs (−1 916 / −3 844 / −7 708 contre −1 920 / −3 840 / −7 680).
🔴 **Les deux observables ne mesurent pas la même chose** : `manques` bouge dès 3 840 ; la **phase**
tombe **à 7 680**, là où `manques` reste à 0. **Deux régimes, deux compteurs.**

✅ **Corrélation œil à `bounce 480`** : `manques = 290 / 4 873` **et** l'owner voit *« ça a glissé »*
— dans la **même** fenêtre.

#### 20.7.7 🔴 LE PLAFOND DE `bounce_px` — CARTOGRAPHIÉ SANS UN SEUL REBOOT

La garde de budget s'exécute **avant toute écriture NVS** ⇒ l'échelle se sonde **sans risque**.

| `bounce_px` | coût RAM | `demande + 48 Ko` vs **234 895 o** | verdict |
|---:|---:|---:|---|
| 38 400 | 276 480 o | 325 632 | ⛔ refusé |
| 30 720 | 245 760 o | 294 912 | ⛔ refusé |
| 19 200 | 199 680 o | 248 832 | ⛔ refusé |
| **15 360** | 184 320 o | 233 472 | ✅ **accepté — à 1 423 OCTETS près** |
| 9 600 | 161 280 o | 210 432 | ✅ (24 463 o de marge) |
| 7 680 | 153 600 o | 202 752 | ✅ courant |

🔴 **L'échelle de la marge n'a plus que DEUX crans**, et le second passe à **1 423 o** — `dn4-9` vient
d'en prendre **680**. ⛔ **15 360 n'a PAS été éprouvé au boot** : §4bis dit qu'il ne démarrerait pas,
la garde dit qu'il tient de justesse, et **se tromper coûte un reset physique**. **Contradiction
CONSIGNÉE, ⛔ pas tranchée.**

#### 20.7.8 🔴 UN DÉFAUT DE LA GARDE DE BUDGET, TROUVÉ ET CORRIGÉ (`f07177c`)

Le message annonçait *« pour 234 895 o disponibles […] marge de sécurité **déduite** »* **et
refusait 199 680**. La marge n'est **pas** déduite du disponible : elle **s'ajoute à la demande**
(`veut + DN_BUDGET_MARGE_O > peut`, `dn_bootcfg.c:560`). ⇒ **un refus légitime ressemblait à un bug**
— et « la garde est cassée, on passe outre » mène droit au **CPU halté**. La console imprime
désormais **la comparaison réellement faite**.

#### 20.7.9 🔴 `draw_lines` — LE LEVIER CHIFFRÉ **VERS LE BAS** POUR LA PREMIÈRE FOIS

§11.5 dit *« le levier `draw_lines` SATURE à 128 »*. ⚠️ **C'est vrai VERS LE HAUT** (160 ne donne
rien) ; **vers le bas, personne n'avait chiffré** :

| | `(7 680, **128**)` | `(7 680, **80**)` |
|---|---:|---:|
| RAM interne libre | 89 019 o | **135 507 o** (**+46 488 o**, théorie +46 080) |
| `nav ab 40` moy, n=80 | **336,8 ms** | 🔴 **409,6 ms (+72,8 ms, +21,6 %)** |
| flush / cycle sous `nav` | 4,8 | **7,8** |
| plus grande aire | 61 440 px = 128 lignes, **SATURÉ** | 38 400 px = 80 lignes, **SATURÉ** |

⇒ La zone sale **dépasse le tampon dans les deux configs** ; le rétrécir **multiplie les flushes**.
⛔ **Voie REJETÉE** : 46 488 o (6,6× ce que coûte `9 600`) pour **+21,6 %** de latence, alors que le
budget de `dn4-4` est à **300 ms** et qu'on est déjà à 336.

#### 20.7.11 🔴 L'A/B RÉPÉTÉ `7 680` vs `9 600` — « TAPIS ROULANT », ET LA PREUVE EST MÉCANISTE

⚠️ **D'abord un aveu de méthode** : sur **UNE** fenêtre de 180 s (130 contre 128) j'avais conclu
*« 9 600 n'améliore rien »*. **C'était faux, et c'est l'ŒIL de l'owner qui l'a corrigé**, pas la
mesure. ⛔ **Une fenêtre ne discrimine pas ce défaut** — cause nommée par l'owner lui-même :
*« c'est bon 10 s, ensuite ça tombe »*, **c'est par RAFALES**.

**9 fenêtres, bras alternés, même stimulus** :

| | n | taux min | **moyenne** | taux max | dispersion |
|---|---:|---:|---:|---:|---:|
| **7 680** | 4 | 0,710 | **0,83 corruption/s** | 0,962 | ×1,35 |
| **9 600** | 5 | 0,058 | **0,44 corruption/s** | 0,830 | **×14** |
| **repos** | 1 | — | **0** | — | — |

✅ **Confirmé indépendamment par l'œil** : *« quasiment toutes les secondes »* (7 680) → *« un peu
mieux, toutes les 2-3 s »* (9 600).
⛔ **Mais les distributions SE CHEVAUCHENT** : la pire fenêtre à 9 600 (**0,830 /s**) tombe en plein
dans la plage de 7 680. ⇒ **sur une fenêtre isolée, on ne peut pas dire quelle config on regarde.**

🔴 **LA PREUVE MÉCANISTE — le rapport `déficit / seuil` NE BOUGE PAS** :

| `bounce_px` | seuil | déficits observés | **rapport** |
|---:|---:|---|---:|
| 7 680 | 620 µs | 722 · 723 · 831 · 949 | **1,16 → 1,53** |
| 9 600 | 775 µs | 904 · 942 · 951 · 1 054 · 1 311 | **1,17 → 1,69** |

🎯 **Le déficit croît avec le tampon, dans la même proportion que le seuil** — et c'est vrai **par
construction** : ce qui prend du retard, **c'est le remplissage lui-même**, et un tampon 25 % plus
gros met 25 % plus de temps à se remplir. ⇒ ⛔ **Agrandir `bounce_px` NE PEUT PAS améliorer le
dépassement RELATIF.** Il réduit seulement le **nombre d'ISR** (40 → 32 par trame), donc la
**probabilité** qu'une soit bloquée : facteur ~2 sur la **fréquence**, **rien** sur la **sévérité**.

⇒ 🔴 **Le vrai levier n'est PAS la marge : c'est de réduire le RETARD DU REMPLISSAGE.**
⚠️ **Un point perdu, déclaré** : la bascule vers 9 600 de la paire 2 a **échoué** (reboot /
ré-attachement) ; le point est **écarté**, ⛔ pas remplacé. L'A/B est **3 contre 2**.

#### 20.7.12 ✅ LE CHEMIN DU BRICK EST FERMÉ — filet de sécurité au boot

`ESP_ERROR_CHECK(dn_display_init(&cfg))` (`desknode_main.c:186`) transformait un `ESP_ERR_NO_MEM`
sur les bounce buffers en **panique ⇒ CPU HALTÉ ⇒ plus de console ⇒ valeur fautive relue à CHAQUE
boot**, jusqu'au reflash — et *« une panique haltée ne se flashe pas non plus »*.

🔴 **Et la garde de `set` ne suffisait pas, elle le dit elle-même** : elle protège **au moment du
`set`**, contre la RAM libre **de ce binaire-là**. Une valeur déjà en NVS **survit à un binaire qui
grossit**. ⇒ le jour où le budget bascule, c'est un **boot ordinaire** qui brique la carte, **sans
qu'aucun `set` n'ait été tapé**. Ce n'est donc pas un filet « au cas où » : c'est la fermeture d'un
chemin **qui s'ouvre tout seul avec le temps**.

✅ **Désormais** : une **seule** tentative de repli sur le défaut, **bruyante** (`ESP_LOGE`), et
`desknode_main` **persiste** le repli en NVS pour que le boot suivant soit propre.
✅ `s_bounce_px` est posé depuis `rgb_cfg`, ⛔ plus depuis `cfg` : après un repli les deux
diffèrent, et annoncer la valeur **demandée** serait un chiffre faux mais plausible.
⛔ **CE QU'IL NE COUVRE PAS** : un `assert()` ou une panique levée **ailleurs** — typiquement
`esp_lvgl_port` sous `CONFIG_LCD_RGB_ISR_IRAM_SAFE=y`. ⚠️ ⛔ **Ne pas le lire comme « le boot ne
peut plus paniquer ».**

#### 20.7.13 🎯 `bounce_px = 15 360` **DÉMARRE** — §4bis est RÉFUTÉ pour cette valeur

> ⛔ **AMENDEMENT DE §4bis, ⛔ PAS EFFACEMENT.** §4bis écrit : *« des valeurs que
> `bounce_px_refus()` ACCEPTE (**15 360**, 19 200, 30 720, 38 400) ne démarreraient PAS »*.
> **Éprouvé le 2026-08-23, filet de sécurité en place : 15 360 DÉMARRE.**

`boot 2 385 ms` · `fps 15` = **37,40 Hz, écart +0,00 %** · **aucun repli, aucune panique** ·
RAM interne libre **58 859 o**. La garde auto-calibrée avait **raison** ; §4bis reposait sur un
raisonnement d'avant `dn_bootcfg_budget_refus()`.
⚠️ **Portée EXACTE de la réfutation** : elle vaut pour **15 360 SEULEMENT**. 19 200 / 30 720 /
38 400 sont **refusés par la garde** et restent **non éprouvés**.

🔴 **Et ça ne sert à rien** — c'est le troisième cran, et il **confirme le tapis roulant** :

| `bounce_px` | ISR/trame | seuil | déficit pire | **rapport** | taux moyen | RAM libre |
|---:|---:|---:|---:|---:|---:|---:|
| 7 680 | 40 | 620 µs | 722–949 | **1,16–1,53** | **0,83 /s** | 90 451 o |
| 9 600 | 32 | 775 µs | 904–1 311 | **1,17–1,69** | **0,44 /s** | 81 451 o |
| **15 360** | 20 | 1 240 µs | 1 646 | **1,33** | **0,79 /s** | **58 859 o** |

🎯 **Le rapport `déficit/seuil` est INVARIANT sur un facteur 2 de `bounce_px`**, et le taux ne
décroît même pas de façon monotone (0,83 → 0,44 → 0,79). ⇒ 🔴 **« Remonter la marge » N'EST PAS UNE
RÉPONSE**, et c'est désormais établi sur **trois** crans, avec une **explication mécaniste**.

#### 20.7.14 🔴 `ISR_IRAM_SAFE = y` — VOIE FERMÉE **PAR LECTURE**, sans un seul flash

§0 constate qu'à `y` *« le bounce PANIQUE au boot »* **sans dire pourquoi**. La raison est
**structurelle**, et **le driver l'écrit lui-même**, à la ligne exacte du `memcpy` de remplissage
(`esp_lcd_panel_rgb.c:911-913`) :

> *« Note: if the frame buffer is behind a cache, and the cache is disabled, **crash would happen
> here** when auto write back happens »*

Le raisonnement se referme en trois faits **lus** :

| # | fait | où |
|---|---|---|
| 1 | Notre framebuffer est **derrière le cache** : `.flags.fb_in_psram = 1` | `dn_display.c:295` |
| 2 | À `ISR_IRAM_SAFE=y`, la DMA est allouée `.flags.isr_cache_safe = true` ⇒ **son ISR tourne CACHE COUPÉ** | `esp_lcd_panel_rgb.c:995-997` |
| 3 | Or **c'est cette ISR-là** qui fait le `memcpy` **depuis la PSRAM** | `esp_lcd_panel_rgb.c:911` |

⇒ 🔴 **Les deux mécanismes s'annulent PAR CONSTRUCTION** : `ISR_IRAM_SAFE` existe pour survivre au
cache coupé ; le bounce existe pour recopier **depuis** la PSRAM, ce qui **exige** le cache.
⚠️ Et **le driver ne refuse PAS la combinaison** (aucun `ESP_RETURN_ON_FALSE` ne l'attrape) —
⇒ elle échoue **à l'exécution**, ⛔ pas à la création. C'est exactement le profil d'une panique au
boot, puisque `lcd_rgb_panel_start_transmission()` **pré-remplit les deux tampons au démarrage**.

⛔ **La seule échappatoire serait `fb_in_psram = 0`** — un framebuffer de **614 400 o** en RAM
interne, quand il en reste **~90 000**. **Impossible**, d'un facteur 6,8.

✅ **VOIE ÉLIMINÉE, ⛔ SANS L'AVOIR JOUÉE.** Aucun flash, aucun risque de reset physique.
⚠️ ⛔ **Ne pas la rouvrir** sans avoir d'abord sorti le framebuffer de la PSRAM — ce qui est un
autre produit.

#### 20.7.15 🔴 LE NOMBRE DE GRANDEURS N'Y EST POUR RIEN — C'EST L'AIRE

**Question de l'owner, verbatim** : *« on va ajouter valeur par valeur dans les cases et voir ce qui
fait déconner, ou si on doit baisser le nb de données affichées »*.

**Balayage : 10 fenêtres de 180 s, DEUX passes en ordre INVERSÉ**, trafic **identique** (injecteur
`--jeu reel`), seul le **dessin** varie. L'inversion sépare l'effet de la dérive.

| config | grandeurs | **aire / flush** | passe 1 | passe 2 | **moyenne** |
|---|---:|---:|---:|---:|---:|
| **A. 6 cases NUES** | 0 | **3 456 px** | 0,000 | 0,000 | **0,000 /s** |
| B. 1 par case | 6 | 36 810 | 0,692 | 0,880 | 0,786 |
| C. CPU 2 · GPU 2 | 8 | 36 811 | 0,210 | 0,471 | 0,341 |
| D. CPU 3 · GPU 3 | 10 | 36 808 | 0,868 | 0,814 | 0,841 |
| E. **nominal** | 13 | 36 810 | 0,847 | 0,897 | **0,872** |

🔴 **1. L'AIRE EST CONSTANTE À ±4 PIXELS** de 6 à 13 grandeurs (36 808 → 36 812).
⇒ **ajouter des valeurs ne change RIEN à ce qui est repeint.** Le firmware le dit lui-même :
`invalidation : GROUPEE (1 zone englobante par widget)` — dès qu'**une** valeur change, **la case
entière** est invalidée.

🔴 **2. LE TAUX NE SUIT PAS** : 0,786 → 0,341 → 0,841 → 0,872. **Désordonné**, et l'écart entre les
deux passes d'une même config (C : 0,210 vs 0,471, **×2,2**) **dépasse** l'écart entre configs.
⇒ ⛔ **bruit, pas effet.**

🎯 **3. CASES NUES = ZÉRO CORRUPTION, DEUX FOIS, SOUS LE MÊME TRAFIC.** Aire 3 456 px, déficit pire
**296 / 534 µs** — **sous le seuil de 620**.

⇒ 🔴 **RÉPONSE À L'OWNER : ⛔ « baisser le nombre de données affichées » NE SERVIRA À RIEN.**
Le coupable n'est pas le nombre de valeurs, c'est **l'AIRE REPEINTE** — **×10,7** entre nue et
pleine.

#### 20.7.16 🎯 `widget groupe off` — LE LEVIER, ET IL EST GRATUIT

Scan rapide des leviers d'aire, **40 s par config** (⚠️ l'aire est une moyenne instantanée, elle se
lit vite ; le **taux**, lui, exige 180 s — voir §20.7.17) :

| config | aire/flush | **px / CYCLE** | fl/cyc | **copie moy** | copie pire | CORR (40 s) | déficit |
|---|---:|---:|---:|---:|---:|---:|---:|
| **NOMINAL** (`groupe on`) | 36 675 | **73 350** | 2,0 | **3 069 µs** | 3 975 | 29 | 721 |
| 🎯 **`groupe OFF`** | **6 758** | **31 948** | 4,7 | **350 µs** | **751** | **0** | **233** |
| `bandes on` | 39 120 | 142 873 | 3,7 | 3 028 | 7 093 | 39 | **1 335** |
| `groupe off` + `bandes on` | 54 810 | 89 889 | 1,6 | 4 676 | 6 061 | 0 | 182 |
| `replacer off` | 36 675 | 75 202 | 2,1 | 3 046 | 4 012 | 0 | 419 |

🎯 **`groupe off`** : aire **−82 %** · px par **cycle** **−56 %** · **copie divisée par 8,8**
(3 069 → 350 µs, pire 3 975 → 751) · déficit pire **721 → 233 µs**, soit **SOUS le seuil de 620,
avec 62 % de marge**.
⚠️ `fl/cyc` monte de 2,0 à **4,7** — plus de flushes, mais **chacun 8,8× moins cher** : le bilan par
cycle est **divisé par 2,3**.

⚠️ **ET DEUX VOIES SONT ÉCARTÉES PAR LA MÊME MESURE** :
- 🔴 **`bandes on` AGGRAVE** : aire 39 120 px, déficit **1 335 µs** — plus du DOUBLE du seuil.
  §16.7 annonçait un *« gain SOUS CONDITION »* : **la condition n'est pas remplie dans ce régime**.
  ⛔ Ne plus le proposer sans relire §16.7 **et** re-mesurer.
- **`replacer off`** : **aucun effet** sur l'aire (36 675 px, identique au nominal).

#### 20.7.17 🔴 LA CAMPAGNE 180 s DE LA BASCULE — ET SA PROVENANCE, QUI EST UN DÉFAUT

⚠️ **SECTION ÉCRITE LE 2026-08-23, APRÈS COUP, POUR COMBLER UN RENVOI MORT.** §20.7.16 renvoyait à
« §20.7.17 » depuis `c9ac2c1` alors que **cette section n'avait jamais été écrite**. Elle est donc
rédigée ici **à partir des seules sources qui existaient** — et il faut savoir lesquelles.

🔴 **PROVENANCE, ET C'EST LE POINT LE PLUS IMPORTANT DE CETTE SECTION.** Les chiffres ci-dessous ne
viennent **PAS** d'un relevé consigné. Ils viennent de **deux endroits, et de deux seulement** : le
commentaire de `firmware/desknode/main/dn_widget.c` (au-dessus de `s_groupage`) et le **message du
commit `c9ac2c1`**. ⛔ **Les relevés bruts n'existent nulle part** — ni durée réelle de fenêtre, ni
`n`, ni comptes entiers, ni `ph_max`, ni `aire cumulée`, alors que `flush` **imprime tout cela**.
Recherche exhaustive menée sur les deux dépôts, toutes branches, arbre propre : rien.

| grandeur | `groupe ON` | `groupe OFF` | rapport |
|---|---:|---:|---:|
| aire par flush | 36 675 px | **6 746 px** | −82 % |
| pixels par **CYCLE** | 73 350 | **31 948** | −56 % |
| copie par flush | 3 059 µs | **350 µs** | ÷ 8,7 |
| **déficit de phase PIRE** | 961 µs | **145 µs** | seuil **620 µs** |
| **corruptions par seconde** | 0,329 | **0,008** | ÷ 41 |
| et — | | **0 sur 200 s** | constat owner : *« plus rien, image stable et propre »* |

Annoncé comme : *« fenêtres de 180 s, stimulus identique, DEUX passes en ordre inversé »*.

### ⛔ CE QU'IL FAUT LIRE AVANT DE SE SERVIR DE CES CHIFFRES

🔴 **`÷ 41` ET `÷ 6,6` SONT DES MAJORANTS, ⛔ PAS DES MESURES.** L'instrument de `dn4-10` compare
chaque phase à `s_bnc_ph_max`, un **maximum à cliquet** qui ne redescend jamais dans une fenêtre
(`dn_measure.c:283-290`). Le bras `groupe ON` copie **3 069 µs** par flush contre **350** : il
monopolise davantage la PSRAM, retarde davantage l'ISR de vsync, donc **gonfle davantage sa propre
référence**. ⇒ **le biais joue EN FAVEUR de la bascule.** L'écart publié est un **plafond du gain**.

⚠️ **ET `0,329 /s` EST LE CHIFFRE LE PLUS FLATTEUR DU DOSSIER — À L'ENVERS.** C'est **la plus basse
des huit mesures publiées de ce même régime** : 0,710 · 0,936 · 0,962 · 0,710 (§20.7.11) · 0,786 ·
0,341 · 0,841 · 0,872 (§20.7.15) · 0,725 (§20.7.16, 29 CORR / 40 s). ⇒ **la bascule est SOUS-VENDUE.**
Avec la moyenne réelle du régime, le rapport serait de l'ordre de **÷ 100**, pas ÷ 41.

✅ **CE QUI, MALGRÉ TOUT, TIENT — ET POURQUOI.** Trois raisons indépendantes :

1. **Un instrument qui ne sait que SUR-compter ne peut pas fabriquer un ZÉRO.** `deficit = ph_max − ph`
   avec `ph_max ≥ ph_nominal` **toujours** ⇒ le biais est de signe non négatif. Le bras de la bascule
   rend **0**.
2. **L'amplitude du biais est BORNÉE PAR UNE MESURE DÉJÀ PUBLIÉE ICI** : §20.7.5 donne `ph_max` de
   **1 978 µs** (repos) à **2 010 µs** (pire trafic) — **32 µs d'écart total, soit 5,2 % du seuil de
   620** — contre un effet mesuré de **×3,1 à ×6,6** sur le déficit. Retirer 32 µs ne déplace rien.
3. **La conclusion survit à la dispersion que ce dossier a lui-même chiffrée** (×3,7 à config
   identique, §20.7.6 ; ×14 à 9 600, §20.7.11) : même en appliquant ×14 à `0,008`, on reste à
   **0,112 /s**, soit **6× sous le plancher** jamais atteint en `groupe ON`.

✅ **PREUVE POSITIVE QU'UNE CAMPAGNE LONGUE A BIEN EU LIEU** (⛔ elle n'est simplement pas consignée) :
le firmware n'imprime qu'un **compte entier** (`dn_console.c`, `ph_100pc`) — les taux sont des
divisions faites après coup. Sur 40 s, la plus petite valeur non nulle possible est **1/40 = 0,025 /s**.
Publier **0,008 /s** exige donc **≥ ~118 s** d'observation.

### 🔴 CE QUI RESTE À RELEVER — L'INSTRUMENT L'IMPRIME DÉJÀ, IL SUFFIT DE LE LIRE

| à relever | pourquoi | où |
|---|---|---|
| **`ph_max` du bras `groupe OFF`** | **le chiffre qui fermerait le dossier du cliquet** : s'il vaut ~1 978 µs ou plus, la référence a été correctement établie et le zéro est inattaquable | `flush`, bloc glissement |
| `doubles` | contrôle direct du défaut `n >= 1` (déduit nul à `7 680` via `manques = 0`, jamais relevé) | `flush` |
| **`cpu brut`** à uptime comparable | §16.2 mesure que le groupage **COÛTE +2,52 pt de CPU** : la bascule devrait en **rendre** — jamais vérifié | `cpu brut` |
| Δ RAM interne, Δ boot | exigés par AC6 de `dn4-10`, absents pour cette bascule | `mem`, bandeau |
| **la question 5 d'AC7 — *« l'image est-elle toujours DROITE ? »*** | la bascule change ce que LVGL invalide ; AC7 dit « ⛔ AUCUN COMPTEUR NE REMPLACE CET AC » | l'œil de l'owner |
| le comportement sous **`touch mode event`** | ⚠️ **seul angle mort connu de la bascule** : ce mode met en pause le timer de lecture de l'indev, la fenêtre d'accumulation des zones passe de ~34 ms à ~1 s, et 4 rafales × 13 zones = **52 > `LV_INV_BUF_SIZE` (32)** ⇒ LVGL substituerait **l'écran entier** (307 200 px). ⛔ Ce n'est **pas** le régime livré (le défaut est POLL), mais ce n'est pas rien | `flush` : `aire/flush` et `max_px` |

⚠️ **LE PROTOCOLE A/B N'EST PUBLIÉ VERBATIM NULLE PART** — ni ici, ni dans la story, ni dans le commit.
Il n'existe que dans un `printf` du firmware (`widget groupe on|off` imprime *« `flush reset`
MAINTENANT, puis attendre >= 3 cycles de source avant `flush` »*) et dans la **non-monotonie** des
tableaux, qui prouve *a posteriori* que la RAZ a bien été jouée entre les bras. **Un rejeu se ferait à
l'aveugle.** ⇒ à écrire.

#### 20.7.10 Ce que la séance N'A PAS fait

- ⛔ **`ISR_IRAM_SAFE = y` n'a PAS été éprouvé** : §0 dit qu'il **panique au boot**, une panique
  **halte le CPU**, et seul un **reset physique** en sort. **Décision owner, à prévenir AVANT.**
- ⛔ **`pclk` / fps** : non mesuré, touche le critère du brief.
- ⛔ **La réduction de l'aire invalidée** : la mesure montre que l'aire **sature le tampon**, mais le
  gain de `widget bandes` (§16.7) n'a **pas** été re-chiffré ici.
  🔴 **AMENDÉ LE 2026-08-23 — CETTE PUCE EST FAUSSE DEPUIS `c9ac2c1`, ⛔ ELLE N'EST PAS EFFACÉE.**
  Le même commit qui a écrit cette section a inséré **§20.7.15** et **§20.7.16** juste au-dessus, qui
  chiffrent la réduction de l'aire — et qui **RÉFUTENT `widget bandes`** (aire 39 120 px, déficit
  **1 335 µs**, plus du double du seuil). Le levier réel est **`widget groupe off`**, ⛔ pas `bandes`.
- ⚠️ **`cpu brut` à 9 600 n'est pas comparable au T0** (8 s d'uptime contre 110 s) ⇒ ⛔ **aucun Δ
  publié** plutôt qu'un Δ faux.
- ⚠️ **Deux témoins owner PERDUS** : la fenêtre était lancée **avant** la demande. Corrigé en séance.

## 21. `dn4-9` / AC8 — LE CONSTAT OWNER À L'ŒIL, 2026-08-22, firmware `38c3b99`

🔴 **CE SONT LES YEUX DE L'OWNER, ⛔ PAS UNE DÉDUCTION.** Chaque question posée **une par une**,
sur données **RÉELLES** (agent sur la tour, LHM 5/5 sondes).
⚠️ **ET L'OBSERVATION S'EST FAITE À TRAVERS UN DÉFAUT** : le sautillement de §20 était présent
(il démarre vers 10 s de trafic). C'est un coût accepté explicitement, et il est dit ici parce
qu'il **dégrade** toutes les réponses ci-dessous — ⛔ pas parce qu'il les invalide.

| # | question | verdict owner |
|---|---|---|
| 1 | La 3ᵉ ligne de la case `CPU` se lit-elle comme une **température** ? | ✅ *« oui ça se lit bien comme une température »* |
| 2 | La case `DISQUE` dit-elle **de quel ventilateur** il s'agit ? | 🔴 **NON** — *« on ne sait pas de quel ventilo il s'agit »* · ✅ *« oui `Mo/s` ok »* |
| 3 | Détail `CPU` : les **quatre** tiennent en **deux** lignes ? | ✅ *« oui les 4 tiennent bien en 2 lignes »* |
| 4 | 🎯 Détail `DISQUE` : les **trois `tr/min`** = trois ventilateurs **différents** ? | ✅ *« oui les 3 se distinguent bien »* |
| 5 | LHM coupé : les trois disent **laquelle** manque ? Le `Mo/s` survit ? | ✅ *« yes c'est ok »* |
| 6 | Lequel des trois veux-tu **dans la case** ? | ⏳ **REPORTÉ** — *« aucun, on travaillera sur cet affichage plus tard, on continue »* |
| 7 | Les **cinq autres** cases ont-elles bougé ? | ✅ *« non ça a l'air good »* |
| 8 | `0 tr/min` (arrêt) contre `--` (absent) se distinguent-ils ? | ✅ *« oui on les distingue bien »* |

### 21.1 🔴 L'ÉCHEC DE LA Q2 — ET IL ÉTAIT ANNONCÉ

**La case `DISQUE` ne dit pas de quel ventilateur elle parle.** ⛔ Ce n'est **pas** une surprise :
c'est **exactement** le risque nommé quand l'owner a choisi l'option, verbatim de la proposition —
*« Question 2 d'AC8 à ton œil : sauras-tu que c'est l'extraction sans que ce soit écrit ? »*.
La mesure disait qu'aucun préfixe ne tenait (**315 px pour 201**, il reste **18 px**) ; l'œil dit
maintenant que **s'en passer ne marche pas non plus**.

⇒ 🎯 **LES DEUX LEVIERS ÉVIDENTS SONT ÉPUISÉS, ET IL EN RESTE UN QUI N'A PAS ÉTÉ EXPLORÉ** :
**la LIGNE SECONDAIRE**. Elle est **libre** sur `DISQUE`, elle a **la place**
(`y_bas = 128`, + secondaire = `148 ≤ 163`, et `widget` le confirme : `DISQUE  2  non  OUI`), et
elle est en **`dn_font_14`** — donc **deux fois plus étroite** que la police des valeurs.
⚠️ **Non mesurée** : la largeur en `dn_font_14` reste à relever par `widget largeur`. ⛔ Ne pas la
supposer suffisante.
⚠️ Et la contrainte d'honnêteté **survit** : le nom ne promet toujours pas plus que la tour ne
mesure (⛔ « TOP »/« BOTTOM » pour `CASE_GROUP`, ⛔ « les ventilateurs » pour l'extraction).

### 21.2 ⏳ LA Q6 EST REPORTÉE, ET ELLE PART AVEC LA Q2

*« Aucun, on travaillera sur cet affichage plus tard »* — **décision owner du 2026-08-22**.
⇒ La voie **(c1)** (`extraction_moy` en case) **reste en place par défaut**, ⛔ pas parce qu'elle a
gagné un arbitrage, mais parce que **l'arbitrage est reporté**.
🎯 **Et les deux questions n'en font qu'une** : tant que la case ne sait dire **de quoi** elle
parle, choisir **lequel** des trois y mettre n'a pas de sens. ⇒ **à traiter ENSEMBLE**.

### 21.3 ✅ CE QUE AC8 SOLDE, ET QUI NE SE MESURE PAR AUCUN CHIFFRE

- **La sélection d'indices est LISIBLE** : la °C se lit comme une température dans une case qui
  portait un `%` à cette place la veille (Q1).
- 🎯 **LES TROIS PRÉFIXES FONT LEUR TRAVAIL** (Q4) — c'est **LA** question d'AC2, et elle passe.
  Trois `tr/min` qui étaient **byte-identiques** sur le fil se lisent comme trois ventilateurs.
- **W10 tient jusque dans le détail** (Q5) : le préfixe RESTE quand la valeur part.
- **L4 tient à l'œil** (Q8) : `0 tr/min` (fan-stop, vraie valeur) et `--` (absent) ne se confondent
  pas. ⚠️ La réserve écrite d'avance — *« un ventilateur réellement arrêté ressemblera à une
  panne »* — **ne s'est PAS réalisée**.
- **Zéro régression visible** sur les cinq autres cases (Q7), y compris la jauge de `RAM`.

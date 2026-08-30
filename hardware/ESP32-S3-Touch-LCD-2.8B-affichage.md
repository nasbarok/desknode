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

> 🔴 **AMENDEMENT DU 2026-08-24 — DEUX LIGNES DE CETTE TABLE ÉTAIENT FAUSSES.**
> Relevé par la **deuxième revue de code 3 couches** (plage `c9ac2c1..0f63827`, story `dn4-10`).
> `bounce_px` était resté à **7 680** (faux depuis `1adf259`) et `RESTART_IN_VSYNC` à **`y`**
> (faux depuis `4734d07`). Les deux sont corrigés ci-dessous, **par annotation dans la colonne
> de droite** — la valeur de gauche porte l'état COURANT, comme le veut cette table.
>
> ⛔ **ET C'EST LA TROISIÈME FOIS QUE §0 EST PRISE EN DÉFAUT** : `bounce_px` était resté à 4 800
> jusqu'à la revue du 2026-08-19 (l'encart ci-dessus le raconte), la revue du 2026-08-23 avait
> classé le grief « sans objet » en écrivant que `bounce_px` n'avait pas changé — **il venait de
> changer** — et le voici de nouveau. AC8 de `dn4-10` nomme §0 « le point noir récurrent, relevé
> par la revue trois stories de suite ». ⚠️ **Le réflexe qui manque n'est pas de relire §0 : c'est
> de la modifier DANS LE MÊME COMMIT que le `#define` ou le symbole Kconfig.**

| | | justifié par |
|---|---|---|
| `num_fbs` | **1** | le double tampon est **réparé** (§4 ter) mais n'apporte **rien de mesuré** : il ne corrige ni le déchirement (c'est la synchro qui le fait) ni l'artefact §10.5, et coûte 614 400 o + une branche Kconfig |
| **`bounce_px`** | **9 600 px (20 lignes)** ⬅️ *change le 2026-08-16 (0 → 4 800), puis le **2026-08-19** (4 800 → **7 680**, `dn4-6`, §18.9 — 4 800 est l'état qui GLISSE sous trafic USB + repeint). ⚠️ Cette ligne est restée à 4 800 jusqu'à la revue de code du 2026-08-19, dans le tableau qui **fait autorité** — et ~8 autres sites de ce fichier récitent encore `bounce_px=4800` dans des relevés HISTORIQUES, ce qui est correct **pour eux** : ils datent d'avant. ⛔ Ne les corriger nulle part ailleurs qu'ici sans changer aussi le SHA du relevé.* 🔴 ***PUIS LE 2026-08-24 (7 680 → 9 600, `1adf259`, §20bis.6)*** : l'arbitrage a CHANGÉ DE NATURE avec `RESTART_IN_VSYNC=n`. Une famine ne décale plus toute l'image, elle salit le demi-bounce en cours — on n'optimise donc plus « éviter la famine » mais « borner la SURFACE du dégât ». **9 600 est le minimum sur les DEUX instruments à la fois** (dépassement du seuil ET œil de l'owner) ; 15 360 est **pire** (« une bande qui couvre les % »). ⚠️ **Le dépassement publié est une FOURCHETTE, +176 à +182 µs** (deux fenêtres) — ⛔ ne pas en citer une seule borne. ⚠️ **ET CETTE VALEUR N'A PLUS DE FILET AU BOOT** : le repli de `dn_display.c:359` ne s'arme que si `bounce_px != défaut`, or 9 600 **EST** le défaut désormais. Voir `dn4-10`, décision owner du 2026-08-24.* | la DMA du panneau lit désormais un tampon en **RAM interne** au lieu d'aller chercher la PSRAM : c'est ce qui supprime **à la fois** le défilement sous I²C **et** l'artefact §10.5 (§11.4). Coût : 2 × 9 600 o de RAM interne, **rien au repos** et +1,1 point de CPU en redessin, fps **inchangé** — le vrai prix est **+160 ms de latence** (§11.5) |
| **`LCD_RGB_ISR_IRAM_SAFE`** | **`n`** ⬅️ *change le 2026-08-16* | **effet propre nul** sur le défilement (branche enfin jouée, §5.3) — mais avec `y` le bounce buffer **panique** au boot. Il est conservé à `n` comme *condition* du bounce, pas pour lui-même |
| Rendu LVGL | **PARTIEL** | à 128 lignes, un plein écran demande **5 flushes** (§11.7). ⚠️ Le « 10 flushes et ~176 ms » de §10.3 valait à 64 lignes, et son attente a été **corrigée à 267 ms** par la mesure de §11.5 : elle supposait un rendu négligeable, ce que le dashboard n'est pas |
| **Draw buffer** | **480 × 128 px (122 880 o), RAM interne DMA** ⬅️ *change le 2026-08-16* | décision owner pendant le dev : 128 lignes récupèrent **120 des 160 ms** que le bounce coûte, contre +61 440 o de RAM interne. Le levier **sature** à 128 — 160 lignes ne donnent plus rien (§11.5). A/B à aire identique : la PSRAM reste **1,70× plus lente** (§10.3) |
| **Mode de lecture tactile** | **`poll`** ⬅️ *nouveau le 2026-08-16* | verdict AC2 (§11.3). `event` est pourtant **moins cher** (0,5 % contre 0,8 %) : il est écarté sur un symptôme de ROBUSTESSE, pas de coût — `ui off` ne coupe pas le tactile en `event`, l'INT ne bat pas au repos, et l'appui « collé » n'a pas de garde native. Le +0,3 point de CPU est le prix assumé |
| Synchro du flush | **`vsync`** | témoin positif établi : en `off` l'œil **voit** le déchirement, en `vsync` il disparaît (§10.4) |
| `RESTART_IN_VSYNC` | **`n`** (livré) ⬅️ *change le **2026-08-24** (`y` → `n`, `4734d07`, §20bis)* | 🔴 ***LE MOTIF DE `y` EST TOMBÉ, ET C'EST `y` QUI FABRIQUAIT LE GLISSEMENT.*** À `y`, `lcd_rgb_panel_try_restart_transmission()` est joué **inconditionnellement ~37,4 fois/s**, et Espressif écrit au-dessus (`esp_lcd_panel_rgb.c:1142-1148`) que ce reset « *can lead to single-frame desyncs itself* ». ⇒ **le glissement n'était pas la famine, c'était SON RATTRAPAGE.** À `n`, le reset n'a lieu que sur `need_restart` ou famine AVÉRÉE, et `bb_eof_count` y est enfin remis à zéro. ⚠️ Le motif d'origine de `y` (décrochage au DÉMARRAGE) est traité par un **recalage d'amorçage** armé une fois dans `app_main` (`desknode_main.c:363`). ⛔ **ET CE RECALAGE EST UN ONE-SHOT** : les deux autres appelants de `dn_recal_arm()` sont inatteignables à `num_fbs = 1`. La parade automatique au décalage PERMANENT que `y` fournissait n'a pas d'équivalent livré — décision owner du 2026-08-24 : la brancher sur la famine avérée. ✅ Effet de bord voulu : **la commande `dma` redevient opérante**. |
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
| `CONFIG_LCD_RGB_RESTART_IN_VSYNC` | n | **n** | 🔴 **AMENDÉ LE 2026-08-24** (revue de code 3 couches, `dn4-10`) : **la colonne disait `y`.** Le symbole est passé à **`n`** le 2026-08-24 (`4734d07`) : à `y` le reset DMA inconditionnel ~37,4 fois/s **fabriquait** le glissement (§20bis). ✅ Et la commande `dma` **redevient opérante** — la mise en garde d'origine, conservée ici, ne vaut plus que pour l'historique : *« mesuré nécessaire — voir §5.1 · ⚠️ rend la commande `dma` inopérante »* |
| `CONFIG_LCD_RGB_ISR_IRAM_SAFE` | n | **n** | 🔴 **AMENDÉ LE 2026-08-24** (revue de code 3 couches, `dn4-10`) : **la colonne disait `y`, et c'était faux DEPUIS PLUS LONGTEMPS** — écart préexistant, sans rapport avec ce commit. `sdkconfig.defaults:101` porte `=n` et §0 aussi ; cette table était la seule à dire `y`. ⛔ Avec `y`, le bounce buffer **panique au boot** : c'est la raison du `n`, pas une précaution. Texte d'origine conservé : *« conservé par précaution, effet propre NON mesuré (coût nul) — voir §5.3 »* |
| `CONFIG_SPIRAM_XIP_FROM_PSRAM` | n | **n** | **RÉFUTÉ par la mesure** : défilement identique avec et sans — voir §5.3 |
| `CONFIG_FREERTOS_HZ` | 100 | **1000** | un tick de 10 ms est plus grossier qu'une trame (26,7 ms) |
| `CONFIG_FREERTOS_GENERATE_RUN_TIME_STATS` | n | **y** | arme `vTaskGetRunTimeStats()` : c'est l'instrument de **charge CPU** exigé par AC6 (commande `cpu`) |
| `CONFIG_FREERTOS_RUN_TIME_STATS_USING_ESP_TIMER` | *(déjà le défaut)* | **y** | écrit explicitement : l'horloge CPU compterait des cycles et **déborderait en ~17 s** |
| `CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG` | UART0 | **USB** | console interactive : un seul binaire pour toutes les mesures — *déplace la console sur l'USB* |

> ⛔ **`CONFIG_SPIRAM_SPEED_120M` est INTERDIT sur ce produit.** Le Kconfig
> d'Espressif prévient qu'en octal, 120 MHz est expérimental et que *« si la puce
> démarre à une certaine température, puis que la température varie d'environ
> 20 °C, les accès PSRAM plantent aléatoirement »*. DeskNode vit H24 **posé à
> côté** d'une tour de jeu — décision owner du **2026-08-17** (*« y aura pas de
> montage définitif dans le phantom, il sera posé à côté »*), ⛔ **il n'est PAS
> monté sur la façade** ; la phrase disait le contraire jusqu'au **2026-08-30**
> (`dn4-15`). Ce n'est pas une piste d'optimisation, c'est une panne programmée.
>
> 🔴 **ET LA CONCLUSION TIENT SANS LA PRÉMISSE DE LIEU — MAIS ELLE N'EST PAS
> CONFIRMÉE POUR AUTANT.** Le lieu corrigé **n'apporte aucune mesure** :
> **l'amplitude thermique réelle de l'emplacement actuel n'est PAS mesurée.**
> Une pièce varie aussi (jour/nuit, chauffage, saison), et la carte porte son
> propre échauffement (dalle RGB, rétroéclairage, S3 à 240 MHz) — c'est
> exactement le terme que §13.9 déclare **non couvert** par son A/B.
> ⇒ **fait MANQUANT, ⛔ pas fait acquis** : personne n'a relevé le ΔT vu par la
> carte sur 24 h là où elle est posée. **L'interdiction reste en vigueur**, et
> ⛔ affaiblir sa justification serait conclure à la place de la mesure.

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

> 🔴 **AMENDÉ LE 2026-08-24** (revue de code 3 couches, `dn4-10`) : **cette table décrit un monde à `num_fbs = 2` et `RESTART_IN_VSYNC=y`.** Elle reste juste POUR SA DATE
> et n'est pas retouchée. ⛔ Mais ne pas la lire comme un verdict sur la configuration livrée : depuis le
> 2026-08-24 le produit tourne à **UN** framebuffer et **`RESTART_IN_VSYNC=n`**, régime dans lequel ni la
> conclusion sur `restart()` ni celle sur le décalage permanent n'ont été rejouées. Voir **§20bis**.

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

> ⚠️ **RENVOI (`dn4-15`, 2026-08-30) — « VL53L0X » ci-dessus est la narration d'un
> arbitrage ANTÉRIEUR au 2026-08-19, et la narration n'est PAS réécrite.** Le 3ᵉ
> module est un **`TOF050C-VL6180X`**, tranché **par la lecture**
> (`i2c lire16 29 0000` → `B4`, 5/5 ; témoin négatif `i2c lire 29 C0` → `01/00/00`
> au lieu de `EE/AA/10`). ⇒ **`firmware/desknode/main/dn_pins.h:165`** et
> **§13.16.7** de `…-capteurs-i2c.md` portent la réfutation complète.

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
| Bandeau MENU | 480 × 60, en (0, 580) | **oui** — no-op consigné · 🔴 **PÉRIMÉ 2× :** géométrie **480 × 51 en (0, 589)** depuis D12 (2026-08-19) · **zone morte** de `dn3-2` à `dn3-3`, puis **VRAIE PORTE** vers `DN_VUE_MENU` depuis le 2026-08-25 |
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

> ─────────────────────────────────────────────────────────────────────────────
> 🎯 **ANNOTÉ LE 2026-08-26 PAR `dn4-5` — CETTE QUESTION EST FERMÉE PAR UN CONSTAT
> OWNER DU 2026-08-25, ET LE TEXTE CI-DESSUS EST DONC PÉRIMÉ.** ⛔ On ANNOTE, on
> n'efface pas : la question a été réelle, et sa réponse se lit à côté d'elle.
>
> **LE GESTE QUI A TRANCHÉ, ET IL A TRANCHÉ DEUX CHOSES D'UN COUP** : tour
> **éteinte**, la **dalle DeskNode reste allumée** ⇒ le port USB **où DeskNode
> est branché** reste alimenté.
> - ✅ **D5 est SOLDÉ** : ⛔ **aucune alimentation séparée**, ⛔ **aucun réglage
>   BIOS à toucher**, ⛔ **aucune mesure de courant**.
> - ✅ **L'interrupteur « Battery Power Control Switch » NE COUPE PAS L'USB** —
>   tranché **par le même geste**. L'hypothèse ouverte depuis le **2026-08-16**
>   est **fermée**.
>
> ⚠️ **LA RÉSERVE QUI ÉTAIT ÉCRITE TOMBE, ET IL FAUT DIRE POURQUOI.** Le dossier
> objectait qu'*« un chargeur de téléphone n'établit qu'AU MOINS UN port
> alimenté »* : c'était juste pour un port quelconque, mais le constat du
> 2026-08-25 porte sur **LE port où DeskNode est branché**, et le témoin est
> **DeskNode lui-même**. La réserve ne s'applique donc plus.
>
> ⛔ **CE QUE CE CONSTAT NE DIT PAS**, et il ne faut pas le lui faire dire : il
> ne donne **aucun chiffre de consommation**. L'INA219 est **hors régime et
> retiré physiquement du bus** (owner, 2026-08-21) ⇒ **le courant de DeskNode ne
> sera pas mesuré en V1**, et *« ce n'était pas le livrable »*.
> ─────────────────────────────────────────────────────────────────────────────

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

🎯 **ANNOTÉ LE 2026-08-26 PAR `dn4-5` — CE PARAGRAPHE EST PÉRIMÉ.** ⛔ Non effacé, annoté.
Le constat owner du **2026-08-25** (tour éteinte ⇒ la dalle DeskNode reste allumée) a tranché
**par le même geste** que D5 : **l'interrupteur « Battery Power Control » NE COUPE PAS l'USB**.
⇒ *« Le mesurer reste utile »* **ne tient plus** : il n'y a plus rien à mesurer là.
⚠️ **`GPIO4` garde en revanche son statut d'origine** : *« aucun rapport de pont diviseur donné »*,
⛔ toujours **à mesurer, jamais à supposer** — ce constat-ci ne dit rien de lui.

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
   🔴 **ANNOTÉ LE 2026-08-30 — CETTE VALEUR N'EST PLUS EN VIGUEUR** : elle vaut désormais
   **`0x141820`**, **arbitrée par l'owner le 2026-08-31**. Motif : l'arbitrage ci-dessous a été
   rendu **AVANT que le mode Ambient existe** (`W_AMB_CASE_BG` naît le 2026-08-25, `3d7438e`), donc
   contre un fond de **PCB** et non contre un aplat **noir opaque**.
   ✅ **MESURÉ le 2026-08-31** : la nouvelle piste se lit **verte**, et c'est la **DALLE**, ⛔ pas la
   valeur — le témoin `0x303030` (gris **exactement neutre**, `G - R = 0`) se lit **vert lui aussi**.
   ⇒ **le prédicteur est la LUMINANCE**, et **aucune piste ne peut être à la fois sombre et neutre**
   ici. Le vert est **assumé** par décision owner. ✅ 0 % / régime ABSENTE éprouvé : barre **visible**.
   ⛔ **ÉCART OUVERT** : la piste face au cuivre du PCB **en Actif**. Détail : docblock de
   `W_COL_PISTE_DEFAUT` et `deferred-work.md`.
   ⛔ Le paragraphe d'origine est **conservé** : il décrit exactement ce qui a été arbitré ce jour-là.
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

> ⚠️ **RENVOI (`dn4-15`, 2026-08-30)** — la coordonnée `y = 340..350` citée ci-dessus
> est **conservée telle qu'elle a été publiée**, ⛔ la narration n'est pas réécrite.
> **Elle est morte, et on ne lui substitue AUCUN autre nombre** (⛔ pas `337..347`,
> qui a été publié sans instrument). ⇒ **le rectangle qui fait foi se RELIT** :
> `widget jauge [<case>]` (`dn4-4`/AC9, `dn_ui_widget_jauge_rect()`), et §22.3
> porte l'arbitrage complet. La console et `dn_ui.c` ne l'enseignent plus.
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
  🔴 **`dn3-3` (2026-08-25) SUPPRIME LA MOITIÉ `MENU` DE CETTE GARDE** : le bandeau est devenu une porte. Ce qui reste à tenir est **« la BARRE est une zone morte »**, et AC5.6 le re-tire comme **témoin négatif**.
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

> 🔴 **PÉRIMÉ LE 2026-08-25 PAR `dn3-3`** — le bandeau `MENU` a désormais une DESTINATION (`DN_VUE_MENU`, décision owner D-4), il est CLIQUABLE et `dn_ui_menu_taps()` **monte**. Le relevé ci-dessus décrivait fidèlement le firmware de SA date ; il décrit l'**inverse** de celui-ci. ⛔ Il n'est ni effacé ni réécrit — c'est un relevé, pas une opinion. La **barre du haut**, elle, reste morte, et c'est le témoin négatif d'AC5.6.

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
première mise à jour** — ~~5 fois par seconde~~, **sans un log**.

> 🔴 **CHIFFRE ANNOTÉ LE 2026-08-24 (`dn4-4` / AC3, 2ᵉ passe — revue de code), SUR MESURE,
> ⛔ PAS EFFACÉ** : la cadence de poussée a été mesurée (100 trames acceptées ⇒ 100 poussées
> en 20,5 s) = **5,0 poussées/s TOUTES MÉTRIQUES CONFONDUES**, donc **1,0/s PAR MÉTRIQUE**.
> Le « 5 fois par seconde » ci-dessus vaut donc pour le chemin `case_poser()` **vu de tout
> le tableau de bord** ; pour **UNE** case, **c'est ~1 Hz**. ⚠️ Le premier balayage d'AC3
> n'avait couvert que `firmware/` — ce site vivait dans `hardware/`, que le `grep` de l'AC
> nomme pourtant explicitement. [Source : `liaison-pc.md` §21.6]

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

⇒ ⛔ **LA CHARGE DE PIXELS N'EST PAS EN CAUSE.** Un label de moins redessiné ~~5 fois par seconde~~
ne change **ni le moment ni la nature** du symptôme.

> 🔴 **CHIFFRE ANNOTÉ LE 2026-08-24 (`dn4-4` / AC3, 2ᵉ passe — revue de code), SUR MESURE,
> ⛔ PAS EFFACÉ** : la cadence de poussée a été mesurée (100 trames acceptées ⇒ 100 poussées
> en 20,5 s) = **5,0 poussées/s TOUTES MÉTRIQUES CONFONDUES**, donc **1,0/s PAR MÉTRIQUE**.
> Le « 5 fois par seconde » ci-dessus vaut donc pour le chemin `case_poser()` **vu de tout
> le tableau de bord** ; pour **UNE** case, **c'est ~1 Hz**. ⚠️ Le premier balayage d'AC3
> n'avait couvert que `firmware/` — ce site vivait dans `hardware/`, que le `grep` de l'AC
> nomme pourtant explicitement. [Source : `liaison-pc.md` §21.6]

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
| `dn_recal` | ~~**INERTE dans ce build**~~ → 🔴 **AMENDÉ LE 2026-08-24** (revue de code 3 couches, `dn4-10`) : **il ne l'est PLUS.** Le texte d'origine — *« INERTE dans ce build : `CONFIG_LCD_RGB_RESTART_IN_VSYNC=y` ⇒ le driver relance à chaque VBlank et ne lit jamais le bit posé »* — est vrai **pour sa date**. Depuis `4734d07` le symbole vaut **`n`**, le bit `need_restart` **est consulté**, et `dn_recal` est devenu **porteur de l'image droite au boot** (`desknode_main.c:363`). ⛔ Il reste un **one-shot** : aucune parade automatique au décalage permanent |
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

> ### 🧭 INDEX DE §20.7 — ⚠️ LA NUMÉROTATION N'EST PAS L'ORDRE DE LECTURE
>
> 🔴 **§20.7.10 est physiquement EN FIN DE SECTION, après §20.7.20.** Ce n'est pas une coquille :
> chaque insertion successive a pris §20.7.10 comme point d'ancrage et s'est glissée **avant** elle.
> ⛔ **On ne renumérote PAS** — des renvois pointent déjà sur ces numéros, et la règle du fichier est
> *« par AJOUT, jamais par effacement »*. On répare **l'index**, ⛔ pas les étiquettes.
>
> **Ordre PHYSIQUE réel : 1 → 9, puis 11 → 20, puis 10.**
> **Nombre de sous-sections : 20** (⚠️ la File List de la story a écrit « 10 » puis « 14 » : **les
> deux étaient faux**, et le compte est ici la seule source à jour).
>
> | | |
> |---|---|
> | **1-3** | ce que la lecture du driver a fermé, et pourquoi `fps` est aveugle |
> | **4-6** | l'instrument, en deux passes, et ce qu'il mesure |
> | **7-9** | le plafond de `bounce_px`, le défaut de la garde, `draw_lines` |
> | **11-14** | l'A/B répété, le filet de brick, `15 360`, `ISR_IRAM_SAFE` |
> | **15-17** | le nombre de grandeurs, `widget groupe`, la campagne 180 s |
> | **18-20** | l'injecteur qui ment, les trois modes, les deux signatures visuelles |
> | **10** *(en fin)* | ⚠️ « ce que la séance n'a pas fait » — **partiellement contredite depuis**, voir son propre encart |
> | **§20bis** | 🎯 **LE CORRECTIF** — c'est là qu'est la conclusion du dossier |

#### 20.7.1 ⛔ TROIS VOIES FERMÉES PAR LA LECTURE DU DRIVER — ne pas les rouvrir

| voie | pourquoi elle est fermée | référence, IDF **v5.5.5** |
|---|---|---|
| **`on_bounce_empty`** | 🔴 appelé **UNIQUEMENT** sous `if (unlikely(panel->num_fbs == 0))`. Nous sommes à **`num_fbs = 1`** ⇒ il **ne sera jamais appelé**. Et l'activer voudrait dire **REMPLACER** la copie du driver, ⛔ pas l'observer | `esp_lcd_panel_rgb.c:899-906` |
| **L'interruption d'underrun MATÉRIELLE** | `LCD_LL_EVENT_UNDERRUN` n'est définie que pour l'**ESP32-P4**. Le **S3 ne l'a pas** — et le driver n'en ferait qu'un `ESP_EARLY_LOGE` | `hal/esp32p4/include/hal/lcd_ll.h:31` · `esp_lcd_panel_rgb.c:1255` |
| **La détection de famine du driver** | `bb_eof_count < expect_eof_count` est dans le **`#else`** de `CONFIG_LCD_RGB_RESTART_IN_VSYNC`. Nous sommes à **`=y`** ⇒ 🔴 **ce test n'existe pas dans notre binaire**, et son compteur n'y est jamais remis à zéro | `esp_lcd_panel_rgb.c:1153-1166` |

> 🔴 **AMENDEMENT DU 2026-08-24 — LA TROISIÈME VOIE EST ROUVERTE, ET C'EST CETTE SECTION QUI LE DIT MAL.**
> Relevé par la deuxième revue de code 3 couches. §20.7.1 s'intitule « TROIS VOIES FERMÉES … ⛔ ne pas les
> rouvrir », et la troisième ligne ci-dessus repose entièrement sur « **Nous sommes à `=y`** ». **Nous n'y
> sommes plus** depuis `4734d07` : à `n`, le test `bb_eof_count < expect_eof_count` **existe dans le binaire**
> et le compteur **est** remis à zéro — c'est écrit en **§20bis.2**, ajoutée par le même commit que cette
> contradiction. ⇒ **La détection de famine du driver n'est plus une voie fermée.**
> ✅ Les DEUX premières lignes (`on_bounce_empty` jamais appelé à `num_fbs = 1`, et l'underrun matériel absent
> du S3) **restent justes** — c'est précisément pourquoi cette section méritait une annotation plutôt qu'une
> réécriture : le lecteur envoyé ici par le bloc REPRISE doit savoir laquelle des trois est tombée.


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

> 🔴 **AMENDÉE LE 2026-08-27 — DEUX DÉFAUTS D'INSTRUMENT ONT ÉTÉ TROUVÉS SOUS CES CHIFFRES, ET ILS
> NE SONT PAS EFFACÉS.** La revue de code les a relevés, la lecture les a confirmés, le correctif
> est dans `eeee27f`. ⛔ **Ces valeurs restent PUBLIÉES telles quelles ; ce qui change, c'est ce
> qu'on a le droit d'en conclure.**
>
> 1. **`min` et `MAX` ne portaient PAS sur la même population que `moy`.** Les **32 trames de
>    dégrossissage** entraient dans `min`/`MAX` et **pas** dans `somme`/`n` — pendant que la ligne
>    console présentait les trois comme issues du même `n`. ⇒ `min 1915 · moy 1961 · MAX 1978`
>    **mélange deux échantillons**. Depuis `eeee27f` les trois portent sur la population comptée,
>    et le dégrossissage est annoncé à part.
> 2. 🔴 **La référence des déficits était un MAXIMUM GLISSANT À CLIQUET** : elle était mise à jour
>    avec l'échantillon courant **avant** de servir de référence à ce même échantillon, et ne
>    redescendait jamais. ⇒ un seul retard ponctuel saturait la colonne `CORRUPTION` pour tout le
>    reste de la fenêtre, **et le même jeu de valeurs dans l'ordre inverse rendait un autre
>    chiffre**. ⚠️ **La colonne `CORRUPTION` de ce tableau est donc un MAJORANT**, ⛔ pas une
>    mesure. La référence est **figée** depuis `eeee27f`.
>
> ⇒ **CE QUI TIENT MALGRÉ TOUT, ET C'EST L'ESSENTIEL** : le **facteur 12** entre repos et trafic
> repose sur le **déficit pire** (63 µs contre 741), pas sur la colonne saturable ; et le biais
> décrit ne peut que **SUR-compter** — un instrument qui ne sait que sur-compter **ne fabrique pas
> le ZÉRO du repos**. La corrélation quantitative avec l'œil, elle, est intacte.
> ⛔ **Un nouveau tirage sous ce binaire ne sera PAS comparable à ces chiffres.**

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
| copie par flush | 3 069 µs | **350 µs** | ÷ 8,7 | ⬅️ 🔴 *disait **3 059** ; corrigé le 2026-08-24 (revue de code). Les deux autres occurrences du même chiffre, `:4960` et `:5006`, disaient **3 069** — dont une insérée par le MÊME commit, onze lignes plus bas.*
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
des **NEUF** mesures publiées de ce même régime** (⬅️ 🔴 *disait « huit » et en énumérait neuf ; corrigé le 2026-08-24, revue de code*) : 0,710 · 0,936 · 0,962 · 0,710 (§20.7.11) · 0,786 ·
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
   **0,112 /s**, soit ~~**6× sous le plancher** jamais atteint en `groupe ON`~~ ⬅️ 🔴 **CORRIGÉ LE
   2026-08-24 (revue de code) : LE « 6× » N'EXISTE QUE SI ON JETTE LES DEUX MESURES LES PLUS BASSES
   DE LA LISTE QUE CETTE SECTION VIENT DE PUBLIER.** Les deux plus basses valeurs `groupe ON` sont
   **0,341** et **0,329** ⇒ `0,341 / 0,112 = 3,04` et `0,329 / 0,112 = 2,94`. **La marge réelle est
   SOUS 3×**, ⛔ pas 6×. ⚠️ L'argument n°3 tient toujours — la conclusion survit à la dispersion —
   mais avec **moins de la moitié** de la marge annoncée, et c'est le genre d'écart qui décide si
   on rejoue ou non. ⛔ C'est aussi l'ironie de la section : elle a été écrite POUR déclarer la
   provenance de ses chiffres, et elle a sur-vendu le sien.

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

#### 20.7.18 🔴 L'INJECTEUR MENT SUR LE DESSIN — facteur **108** mesuré

⚠️ **Constat déclencheur, et il vient de l'OWNER, ⛔ pas de la mesure** :
> *« à part la temp les valeurs ne bougent pas, normal ? »*

**Oui.** `dn_injecteur.py`, table `"reel"`, émet des valeurs **FIXES** (`cpu: [52, 32, 350, 410]`,
`gpu: [0, 460, 500, 5980]`…), mesurées les 19 et 21 août et **rejouées telles quelles**. Le mot
« reel » veut dire *« des valeurs réalistes »*, ⛔ pas *« des valeurs qui varient »*. Seule
**AMBIANCE** bouge — c'est le BME680 **local**, cadencé toutes les 5 s.

🔴 **CONSÉQUENCE, MESURÉE** : les cases ne changeant pas, **le dessin ne se déclenche presque pas**.
Le même firmware, la même config, le même bounce :

| stimulus | corruption/s |
|---|---:|
| `dn_injecteur.py --jeu reel` | **0,005 /s** |
| **agent RÉEL de la tour** | **0,54 /s** |

⇒ **facteur 108.** ⛔ **Tout chiffre où le DESSIN est la variable se mesure sous AGENT RÉEL.**
⚠️ Au **nominal** les deux stimuli coïncidaient (déficit 741 vs 762 µs) — parce que **le groupage
dominait tout**. Retirez le groupage, et l'écart se démasque. **C'est pour ça que le piège n'a pas
été vu plus tôt**, et pourquoi il faut le nommer ici.

#### 20.7.19 🔴 LES TROIS MODES D'INVALIDATION, ÉPROUVÉS SOUS AGENT RÉEL — ET LE RETOUR AU GROUPÉ

Chaque ligne : 180 s d'agent RÉEL, même compteur, même `bounce_px = 7 680`, **l'œil de l'owner à
chaque fenêtre**.

| mode | taux | déficit pire | **ce que l'owner voit** |
|---|---:|---:|---|
| **`on`** (groupé, **le défaut**) | **0,94 /s** (173) | 744 µs | décalage · **aucun artefact** |
| `off` (fin) | **0,54 /s** (100) | 772 µs | décalage · **restes de chiffres + bande de fond** |
| `union` | **0,97 /s** (180, puis 179) | 1 337 µs | décalage · **micro-rectangles** |
| `off` + cases **opaques** | 0,86 /s (159) | 715 µs | artefacts **réduits** · **« ligne verte »** |

🔴 **DÉCISION OWNER, 2026-08-23 : RETOUR À `s_groupage = true`.** On ne livre pas une régression
visuelle **certaine** contre **−42 %** sur un défaut qui reste visible de toute façon.
✅ **Contrôle final** : `ae91c60`, groupé, agent réel 124 s ⇒ **0,79 /s**, cohérent avec le départ.

##### Ce que ces quatre lignes ont appris, et qui ne se reperd pas

1. 🎯 **LE GROUPAGE N'EST PAS QU'UNE AFFAIRE D'AIRE : C'EST UNE ATOMICITÉ.**
   Une case = **UNE** zone sale = **UN** flush, et le flush **attend un vsync**. En fin, la même
   mise à jour fait **4,7** flushes au lieu de 2,0 ⇒ la case s'affiche en **plusieurs trames**, et
   l'œil voit l'état intermédiaire. ⛔ **Ni `dn3-1` ni `dn3-2` ne l'avaient nommé** — ils ne
   parlaient que de pixels et de temps mural.
2. ⚠️ **LA TRANSPARENCE EST *UNE* DES CAUSES DES ARTEFACTS, PAS LA SEULE** : cases opaques
   (`opa 255`, `voile 0`) ⇒ artefacts **« réduits »**, ⛔ **pas supprimés**.
3. 🎯 **`union` A ÉTÉ RÉFUTÉ POUR UNE RAISON INSTRUCTIVE** : il calcule l'union des zones **avant
   ET après** écriture. Quand les valeurs ne bougent pas (injecteur), avant == après ⇒ zone
   minimale. Sous agent réel, **les textes changent de largeur** ⇒ l'union s'élargit à chaque mise
   à jour. **Le mécanisme même du mode le rend sensible au stimulus.**

   > 🔴 **RÉFUTÉ LE 2026-08-27, PAR LECTURE — ⛔ CE PARAGRAPHE EST FAUX ET IL N'EST PAS EFFACÉ.**
   > L'explication ci-dessus est **mécaniquement impossible** : **aucune des deux passes ne voyait
   > jamais la nouvelle largeur.** `lv_obj_get_coords()` est une copie de struct nue
   > (`lv_obj_pos.c:566-571`) ; `lv_label_set_text` finit par `lv_obj_mark_layout_as_dirty`, qui ne
   > fait que poser `layout_inv` et poster `LV_EVENT_REFR_REQUEST` (`lv_obj_pos.c:368-379`) — **la
   > géométrie est DIFFÉRÉE** — et `dn_widget.c` n'appelait **nulle part** `lv_obj_update_layout`
   > (grep sur tout le fichier : **0**). ⇒ la seconde boucle unissait **les rectangles identiques**
   > à la première. C'est le **rétrécissement** qui était couvert (par accident : l'union garde
   > l'ancienne boîte, plus large), et **l'élargissement qui ne l'était pas** — soit l'inverse de
   > ce qui est écrit ci-dessus.
   >
   > 🔴 **ET LA MESURE ELLE-MÊME A ÉTÉ PRISE DANS UN ÉTAT CASSÉ.** La zone d'union n'était
   > construite qu'à partir des **valeurs**, alors que la fonction écrit aussi la **jauge**
   > (`lv_bar_set_value`) et le **badge** (`HIDDEN`) pendant que l'invalidation est coupée — tous
   > deux **hors** de la boîte des valeurs, et **sans filet différé** (`lv_bar.c:748`,
   > `lv_obj.c:262`). ⇒ **la jauge gelait et le badge ne suivait pas.** Le `0,97 /s` a donc été
   > mesuré sur un mode **qui perdait des pixels**, puis déclaré « voie morte » sur cette base.
   >
   > ⚠️ **ET L'ATOMICITÉ, SEULE RAISON D'ÊTRE DU MODE, N'AVAIT JAMAIS EXISTÉ** : l'auto-réparation
   > différée des labels tombait **après** le rétablissement de l'invalidation ⇒ chaque label
   > ajoutait **une zone sale de plus**.
   > 🔍 **LA CHAÎNE, RELUE LIGNE À LIGNE DANS LVGL 9.5.0 VENDORISÉ le 2026-08-27** — ⛔ et la
   > citation d'origine (« `lv_label.c:1354` ») désignait **la fin de la chaîne, pas son crochet**,
   > donc elle n'était pas vérifiable telle quelle : `lv_label_mark_need_refr_text()` (`:1059`)
   > abonne `update_layout_completed_cb` au **display** sur `LV_EVENT_UPDATE_LAYOUT_COMPLETED`
   > (**`:1071`**) ; ce callback (**`:1075-1085`**) se **désabonne** puis appelle
   > `lv_label_refr_text()`, qui finit par `lv_obj_invalidate()` (**`:1354`**).
   > ✅ Le désabonnement est ce qui rend le correctif propre : le label ne se répare pas une
   > seconde fois après coup — sa zone est prise **une fois**, dans la fenêtre coupée.
   >
   > ✅ **CORRIGÉ DANS `12016bd`** : tous les enfants écrits entrent dans l'union, et
   > `lv_obj_update_layout()` est appelé **avant** le rétablissement de l'invalidation.
   > ⚠️ **ET SON COÛT EST DÉCLARÉ, ⛔ PAS SUPPOSÉ NÉGLIGEABLE** : cette fonction ne travaille pas
   > sur le widget, elle **remonte à l'ÉCRAN** (`lv_obj_pos.c:390`) et boucle tant que
   > `scr_layout_inv` est posé. Par lecture, le premier widget de la salve fait le travail et
   > éteint le drapeau, les suivants ne paient que l'envoi de l'événement — ⛔ **mais c'est une
   > hypothèse de lecture, pas une mesure.**
   > ⛔ **LE `0,97 /s` EST À REPRENDRE SUR LA CARTE**, sous agent RÉEL. ⚠️ Le verdict « voie morte »
   > n'est **ni confirmé ni infirmé** — il n'a jamais été éprouvé sur un mode qui marchait.
   > ⛔ Ça **ne rouvre pas** la décision owner du 2026-08-23 : le mode livré reste `on`.

#### 20.7.20 🎯 DEUX SIGNATURES VISUELLES QUI DISTINGUENT LES DEUX DÉFAUTS

**Constats owner du 2026-08-23, verbatim, et ce qu'ils désignent :**

| ce qu'il voit | ce que ça désigne |
|---|---|
| *« restes de chiffres superposés »*, *« bande de fond mal repeinte »*, *« micro-rectangle »* | **artefact d'INVALIDATION** — une zone salie trop petite. ⇒ n'apparaît qu'en `off` / `union` |
| 🎯 *« une **ligne verte** à la place, lors du décalage »* | 🔴 **LE GLISSEMENT LUI-MÊME, AU NIVEAU DE L'OCTET** |
| 🎯 *« parfois ça **reste** dans un état glissé […] ensuite ça reglisse »* | 🔴 **LE RATTRAPAGE DU DRIVER QUI ÉCHOUE** |

🎯 **POURQUOI VERTE — et ce n'est pas une couleur au hasard.** Le framebuffer est en **RGB565** : le
rouge occupe les bits 11-15, le **vert les bits 5-10** — donc **À CHEVAL sur les deux octets** d'un
pixel — et le bleu les bits 0-4. Un décalage du flux DMA d'un nombre **IMPAIR d'octets** recombine
le poids fort d'un pixel avec le poids faible du suivant : les bits qui survivent le mieux à cette
recombinaison sont ceux du **vert**. ⇒ **La ligne verte est la signature d'un décalage SUB-PIXEL**,
et elle confirme le mécanisme du driver (*« resetting DMA will **re-send those** »*) **au niveau de
l'octet**, ⛔ pas seulement de la trame.

🎯 **ET LE « ÇA RESTE GLISSÉ » EST DANS LE TEXTE DU DRIVER.** `esp_lcd_panel_rgb.c:1142-1148` :
*« reset the GDMA channel every VBlank **to stop permanent desyncs from happening** […] the
single-frame desync this leads to is **preferable to the permanent desync** that could otherwise
happen »*. ⇒ L'owner vient d'observer **le rattrapage qui échoue** : le cas que `RESTART_IN_VSYNC`
est précisément censé prévenir. ⛔ **Non expliqué à ce jour**, et c'est une piste ouverte.

⚠️ **UTILITÉ IMMÉDIATE DE CES DEUX SIGNATURES** : elles permettent de **distinguer à l'œil**, en une
seconde, un défaut de dessin d'un défaut de DMA. ⛔ Avant cette séance, les deux se disaient
« l'image sautille ».

#### 20.7.10 Ce que la séance N'A PAS fait

> ⚠️ **AMENDÉE LE 2026-08-23, ⛔ PAS RÉÉCRITE — ET ELLE EST CONTREDITE SUR UN POINT.**
> Cette sous-section a été écrite **avant** §20.7.15 à §20.7.20, qui se trouvent pourtant **au-dessus**
> d'elle (voir l'index en tête de §20.7). Une de ses affirmations est **tombée depuis** :
>
> - 🔴 *« le gain de `widget bandes` (§16.7) n'a **pas** été re-chiffré ici »* ⇒ **FAUX** :
>   **§20.7.16 le chiffre**, et il le mesure **AGGRAVANT** — aire 39 120 px, déficit **1 335 µs**,
>   soit **plus du double du seuil**. ⇒ ⛔ la voie est **éliminée par la mesure**, pas « non chiffrée ».
> - ⚠️ *« `ISR_IRAM_SAFE` non éprouvé »* reste **vrai au sens strict** (aucun flash), mais §20.7.14
>   l'a **fermé par LECTURE** — ce qui est un résultat, pas une lacune.
> - ⚠️ *« `pclk`/fps non mesuré »* et *« `cpu brut` non comparable »* restent **vrais**.
>
> ⛔ Le texte d'origine est conservé tel quel ci-dessous : il dit ce qu'on savait à l'instant où il a
> été écrit, et c'est ça qui a de la valeur.

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

## 20bis. 🎯 LE GLISSEMENT EST CORRIGÉ — `RESTART_IN_VSYNC=n` (2026-08-23)

> ⛔ **AJOUT.** §20.1 à §20.7 restent **justes pour leur date**. Ce bloc **résout** le dossier qu'elles ouvraient.
> Enquête complète : `cockpit:…/investigations/glissement-dma-restart-in-vsync-investigation.md`.

### 20bis.1 🔴 LE RENVERSEMENT — le glissement n'était pas la famine, c'était SON RATTRAPAGE

Espressif l'écrit au-dessus de `lcd_rgb_panel_try_restart_transmission()` (`esp_lcd_panel_rgb.c:1142-1148`) :

> *« reset the GDMA channel every VBlank […] **this fix can lead to single-frame desyncs itself** : **if this interrupt
> is late enough, the display will shift** as the LCD controller already read out the first data bytes, and **resetting
> DMA will re-send those**. »*

À **`y`**, ce reset est joué **INCONDITIONNELLEMENT ~37,4 fois par seconde** ⇒ **37,4 occasions de glisser par
seconde**. ⇒ 🔴 **Les cinq leviers éliminés par §20.7 visaient TOUS la famine. Aucun ne touchait au rattrapage. Ils ne
POUVAIENT pas suffire.**

### 20bis.2 Les deux branches, et pourquoi `y` est le pire des deux mondes

| | `=y` *(jusqu'au 2026-08-23)* | **`=n`** |
|---|---|---|
| reset DMA | **inconditionnel, chaque VBlank** | sur `need_restart` **ou** famine avérée |
| `bb_eof_count` | ⛔ **jamais remis à zéro**, test **compilé hors du binaire** | mesuré et remis à zéro |
| ce que le driver **sait** | rien — il reset « au cas où » | **s'il y a famine** |
| commande console `dma` | **inopérante** | ✅ **opérante** |

### 20bis.3 Pourquoi `y` n'avait plus lieu d'être — trois faits déjà au dossier

`y` a été retenu en `dn1-2` contre un **décrochage au DÉMARRAGE**, dans un monde à **`num_fbs = 2`**.
Depuis le 2026-08-15 il n'y en a plus qu'un, et §4bis écrit *« il n'y a plus de bascule, donc plus rien à perdre »*.

1. **§5.3 (l.595-601)** — à `n`, le décalage au boot **se corrige par UN SEUL appel** : *« remet l'image en place d'un
   coup »*. ⛔ Pas un blocage.
2. **§4ter (l.536-541)** — `n` + recalage événementiel **a DÉJÀ tourné en `dn1-3`** : *« cadrage **correct** — le
   défaut que `y` corrigeait **n'est pas revenu** »*, 9 recalages, **1 vsync suffit**.
3. **(l.549-553)** — son seul coût, *« l'image reste décalée **depuis la bascule** »*, est **indexé sur une bascule qui
   n'existe plus**.

### 20bis.4 ✅ LE CORRECTIF LIVRÉ — firmware `1adf259`

1. **`CONFIG_LCD_RGB_RESTART_IN_VSYNC=n`** dans les **deux** `sdkconfig` (le motif de `y` est **annoté**, ⛔ pas effacé).
2. **Un RECALAGE D'AMORÇAGE** unique en fin de `app_main` — ⛔ **sans lui l'image sort décalée en permanence**. Il passe
   par `dn_recal_arm()` **directement**, ⛔ pas par `dn_display_present()` qui garde l'armement derrière `num_fbs > 1`.
   ⚠️ Et si `recal` vaut 0, c'est journalisé en **ERREUR** plutôt que de livrer une image décalée sans explication.
3. **`DN_DEFAULT_BOUNCE_PX` 7 680 → 9 600** — l'optimum du **nouvel** arbitrage (§20bis.6).
   🔴 **AMENDÉ LE 2026-08-24 (revue de code 3 couches) — CE POINT N'ATTEINT PAS TOUTES LES CARTES.**
   C'est un **défaut compilé**, ⛔ pas un réglage poussé. `dn_bootcfg_load()` amorce
   `out->bounce_px = DN_DEFAULT_BOUNCE_PX` puis **l'écrase depuis la NVS** dès que `bounce_px_refus(v)`
   rend `NULL` (`dn_bootcfg.c:352`, `:375-382`) — et **7 680 passe toutes les clauses**
   (`≤ 38 400` ✓, `307 200 % 7 680 == 0` ✓, `7 680 % 480 == 0` ✓). ⇒ **toute carte sur laquelle
   `set bounce 7680` a été tapé garde 7 680 après reflash**, sans que rien ne le signale.
   ⚠️ **Le correctif de ce point est donc CONDITIONNEL à une NVS vierge ou réinitialisée**, et ça n'était
   écrit nulle part. ⛔ La vérification qui tranche reste le **TRIPLET** `cfg` + `widget` + bandeau de
   boot — `cfg` dit la NVS, et c'est elle qui gagne.

### 20bis.5 🎯 LA PREUVE EST UNE DISSOCIATION, ⛔ PAS UN ACCORD

| | image au boot | glissement (œil) | compteur de phase |
|---|---|---|---|
| avant (`y`, 7 680) | ✅ droite | **~1/s**, *« ça descend et remonte »* | 143-173 corruptions / 180 s |
| **après (`n` + amorçage)** | ✅ **« droite et centrée »** | ⛔ **« plus de glissement ! »** | **143 / 186 s — INCHANGÉ** |

🔴 **Le compteur n'a PAS bougé, et c'est ça la preuve.** Il mesure le **déficit de phase**, donc la **famine** — que ce
changement ne touche pas. Ce qui a disparu, c'est le **rattrapage**.
⚠️ **Et ça révèle une limite de l'instrument de `dn4-10`** : il n'a **jamais** mesuré le glissement. Il mesurait la
famine, bon proxy **uniquement parce que `y` transformait chaque famine en décalage**. À `n` le proxy est **cassé** :
c'est le **DÉPASSEMENT du seuil** qui suit l'œil, ⛔ pas le compte.

### 20bis.6 🎯 À `n`, `bounce_px` A UN OPTIMUM — et c'est 9 600

⛔ **L'arbitrage a changé.** À `y` on cherchait à **éviter** la famine (§20.7.11 a montré que c'était vain). À `n`, la
famine ne décale plus l'image : elle **salit les lignes du demi-bounce en cours**. ⇒ on optimise **la SURFACE du
dégât**, et **deux effets s'opposent** : un tampon plus gros **laisse plus de temps** mais **rate plus large**.

| `bounce_px` | demi-bounce | seuil | déficit pire | **dépassement** | constat owner |
|---:|---:|---:|---:|---:|---|
| 7 680 | 16 lignes | 620 µs | 1 340 µs | **+720 µs** | *« plus de glissement, petite ligne »* |
| 🎯 **9 600** | 20 lignes | 775 µs | 951-957 µs | **+176 à +182 µs** | 🎯 *« bien mieux, plus stable »* |
| 15 360 | 32 lignes | 1 240 µs | 1 461 µs | **+221 µs** | *« pire, une bande qui clignote couvre les % »* |

> 🔴 **AMENDEMENT DU 2026-08-24 — DEUX CHIFFRES DE CETTE SECTION ÉTAIENT À REPRENDRE.**
> Relevé par la deuxième revue de code 3 couches (`dn4-10`).
>
> 1. **Le dépassement à 9 600 est une FOURCHETTE, ⛔ pas une valeur.** La source
>    (`investigations/glissement-dma-restart-in-vsync-investigation.md:159`) publie **951-957 µs**, soit
>    **+176 à +182 µs** sur deux fenêtres. Ce fichier avait retenu **+176**, `dn_bootcfg.c:182` **+182**,
>    le ledger **+176** — **chacun une borne différente, en silence**. ⚠️ Et ce fichier avait retenu **la
>    plus flatteuse** : l'écart affiché avec le +221 de 15 360 en dépendait. La ligne du tableau porte
>    désormais la fourchette. ✅ Les deux autres rangées, elles, sont arithmétiquement justes des deux côtés
>    (`1 340 − 620 = 720`, `1 461 − 1 240 = 221`) — **seule la rangée 9 600 divergeait**, celle que le
>    changement existe pour justifier.
>
> 2. 🔴 **« −7 024 o » est 656 o SOUS le minimum que l'allocation exige.** La fonction de coût du dépôt
>    lui-même (`dn_bootcfg_cout_interne()`, `dn_bootcfg.c:565-568`) calcule `bounce = bounce_px * 2 * 2`
>    ⇒ Δ = `(9 600 − 7 680) × 4` = **7 680 o**. Confirmé par le driver (`bb_size = bounce_px × bpp / 8`,
>    ×2 tampons, `esp_lcd_panel_rgb.c:310` et `:196-201`) **et** par le commentaire préexistant de
>    `dn_bootcfg.c:156` (*« +11 520 o … contre +19 200 pour 9 600 »* ⇒ `19 200 − 11 520 = 7 680`).
>    ⛔ **Un relevé brut de tas libre ne peut pas rendre MOINS que ce que les tampons occupent.**
>    ⚠️ L'origine du 7 024 est **introuvable** : §20.7.17 atteste elle-même que les relevés bruts ne sont
>    consignés dans **aucun** des deux dépôts. ⇒ **Le chiffre à retenir est le théorique, −7 680 o**, et
>    le relevé qui disait 7 024 est à refaire à la prochaine séance s'il compte.

**Coût de 9 600**, mesuré en `dn4-10` : **−7 024 o** de RAM interne (⚠️ **voir l'amendement ci-dessus :
le minimum arithmétique est 7 680 o**), et **ZÉRO** ailleurs — `fps 15` reste à
**37,40 Hz (+0,00 %)**, boot non discriminant, `nav ab 40` **−0,3 ms** sur n=80.

### 20bis.7 ⚠️ LE VERDICT DE LA GARDE DE BUDGET DÉPEND DE L'INSTANT

Deux `set bounce 15360` **consécutifs**, même binaire : le premier **REFUSÉ** (tas chargé), le second **ACCEPTÉ** (tas
frais après reboot). `dn_bootcfg_budget_refus()` mesure la RAM libre **à l'instant de l'appel**.
⇒ ⛔ **Un verdict de la garde n'est PAS une propriété stable du binaire.**
🎯 **Et c'est la réalisation exacte de la prédiction de §20.7.7** : *« le second cran passe à 1 423 octets près, il ne
passera plus dès que le binaire grossira »*. Le binaire a grossi ; le cran s'est fermé — **par intermittence**.

### 20bis.8 ⛔ CE QUI RESTE, ET QUI N'EST PAS RÉSOLU

- **Un résiduel** — *« il reste un tout petit peu »* : quelques lignes du demi-bounce, de la **famine pure**.
- 🔴 ***« Parfois ça reste glissé »*** : **non revu** sur quatre fenêtres de 180 s, mais ⛔ **PAS prouvé absent** —
  l'owner ne l'observait déjà que *« parfois »*, et **le compteur ne sait pas mesurer une DURÉE** (il compte des
  trames, pas des états). ⇒ à trancher par l'usage prolongé, ou par un instrument de durée.
  > 🎯 **AMENDÉE LE 2026-08-28 (`dn4-12`), ⛔ LE TEXTE CI-DESSUS RESTE — il était juste pour sa date.**
  > **L'instrument de durée EXISTE désormais : voir §20ter.** `flush` publie la **PLUS LONGUE SÉRIE DE TRAMES
  > CONSÉCUTIVES NON SAINES**, avec sa **composition**, en **trames** (⛔ pas en microsecondes : `esp_timer`
  > reboucle en 71,58 min, un compte de trames en ~3,6 ans). ⚠️ **Ce qui reste vrai de cette puce ci-dessus** :
  > le symptôme n'est **toujours pas prouvé absent**, et cette section-là ne le prouvera pas non plus —
  > **l'instrument est livré, la MESURE de régime attend la séance carte** (§20ter.6). ⛔ Et la 3ᵉ puce
  > ci-dessous (« le nombre de resets réellement joués reste inobservable ») **n'est PAS levée** : c'est une
  > contrainte de conception que `dn4-12` hérite et déclare — on mesure la **PERSISTANCE DE L'ÉTAT**, ⛔ jamais
  > l'échec de relance (§20ter.9).
- ⛔ **Le nombre de resets réellement joués par le driver reste inobservable** : à `n` il relance en interne sans passer
  par `need_restart`, donc `recal` compte **1** (l'amorçage) et rien d'autre.
- ⚠️ **Quatre fenêtres de 180 s ne valent pas une journée d'usage.**
  > 🎯 **CETTE RÉSERVE-LÀ EST LEVÉE LE 2026-08-27, ET PAS PAR UNE MESURE — voir §20bis.9.**

### 20bis.9 🎯 LE CONSTAT OWNER DU 2026-08-27 — le correctif tient sur PLUSIEURS SÉANCES, et il reste UNE chose

🔴 **VERBATIM OWNER, 2026-08-27** :

> *« depuis plusieurs temps dev et test plus de soucis d'image qui glisse juste un petit eartefact
> sur les % dans le detail cpu mais c'est tt »*

**CE QUE ÇA SOLDE, ET C'EST LA MEILLEURE PREUVE QU'ON AIT SUR CE DÉFAUT.**
Les quatre fenêtres de 180 s du 2026-08-23 étaient la réserve explicite de §20bis.8 : *« quatre
fenêtres de 180 s ne valent pas une journée d'usage »*. Ce constat-ci couvre **plusieurs séances de
développement et de test** menées entre le 2026-08-23 et le 2026-08-27 (`dn4-12`, `dn4-13`,
`dn4-17`, `dn4-18`, `dn4-5`), sur le firmware `1adf259` et ses successeurs. ⇒ **la durée d'usage
que le compteur ne savait pas produire, l'usage l'a produite.**

⇒ **DEUX RÉSERVES DE §20bis.8 TOMBENT** :
- ✅ *« quatre fenêtres de 180 s ne valent pas une journée d'usage »* — **soldée par l'usage**.
- ✅ 🔴 *« parfois ça reste glissé »* (le **permanent desync**, le rattrapage du driver qui échoue) —
  **non revu sur plusieurs séances**. ⚠️ ⛔ **Ce n'est toujours PAS « prouvé absent »** : c'est un
  état RARE, l'owner ne l'observait déjà que *« parfois »*, et **rien ne le mesure encore**. Mais un
  défaut qui ne se montre plus sur des jours d'usage n'a plus le même rang qu'un défaut vu la veille.
  ⇒ **`dn4-12` garde son objet** (mesurer une DURÉE), il perd son urgence.

⚠️ **ET LE RÉSIDUEL A CHANGÉ DE NATURE — c'est ça, l'information neuve.**
Le résiduel de §20bis.8 était *« il reste un tout petit peu »* de **glissement**. Ce qui reste
aujourd'hui n'est **plus décrit comme un glissement** : c'est *« un petit artefact sur les % dans le
détail CPU »* — **local**, **localisé sur une zone nommée**, et **permanent dans la description**.

🔴 **⛔ ET ON NE LUI ATTRIBUE PAS DE CAUSE, PARCE QU'AUCUNE DES DEUX SIGNATURES PUBLIÉES NE LUI VA.**
§20.7.20 range *« restes de chiffres »* du côté de l'**invalidation** — mais elle ajoute que ces
artefacts *« n'apparaissent qu'en `off` / `union` »*, et **le mode livré est `on`**. Et *« ligne
verte »*, la signature du glissement, n'est **pas** ce qui est décrit. ⇒ **cet artefact-ci sort de
la table**, et c'est déclaré.

⚠️ **UNE PISTE, ET ELLE N'EST QUE ÇA — ⛔ NON ÉTABLIE.** §20bis.6 relève qu'à `bounce_px = 15 360`
l'owner voyait *« une bande qui couvre les % »* : **la même zone de l'écran**. Ça peut désigner une
géométrie de bounce qui tombe mal sur cette bande-là, ou une pure coïncidence de position.
⛔ **Aucune mesure ne le tranche, et on n'en tire rien.** C'est le sujet d'une observation dédiée,
⛔ pas de cette section.

> 🎯 **AMENDÉ LE MÊME JOUR — LA CAUSE EST DÉSIGNÉE PAR LA MESURE, voir §20bis.12.**
> ⛔ Le paragraphe ci-dessus (« aucune des deux signatures ne lui va », « aucune cause ne lui est
> attribuée ») **n'est pas effacé** : il dit ce qu'on savait avant l'A/B. Ce qui a changé :
> **la vue détail fait 4,0 flushes par cycle contre 1,0 pour la grille** — elle n'est **pas
> groupée** — et elle produit **31 / 12 corruptions** là où la grille en produit **0 / 0**.
> ⇒ l'objection *« un décalage DMA ne peut pas être local »* **tombe** : ce n'est pas le décalage
> qui est local, c'est **sa cause**. ⚠️ Et la piste des 15 360 px (« même zone ») n'a **rien** à voir :
> elle n'a **pas** été confirmée, et elle n'est plus nécessaire pour expliquer quoi que ce soit.
> ⚠️ **CE QUI RESTE OUVERT** : que l'artefact **vu** soit **cette** corruption. La corrélation
> œil ↔ compteur d'AC2 n'a pas été refaite dans cette vue.

✅ **DÉCISION OWNER DU 2026-08-27 : ON LE NOTE, ⛔ ON N'OUVRE RIEN.** Il n'y a pour l'instant qu'une
**description**, aucune mesure ; ouvrir un instrument pour un artefact qui ne gêne pas coûterait
plus que ce qu'il rendrait. ⇒ ce paragraphe **est** le livrable. Il dort ici jusqu'à ce que
l'artefact gêne, ou qu'une séance carte passe par là.
🔧 **ET QUAND ON L'OUVRIRA, LA PREMIÈRE MANIP EST DÉJÀ ÉCRITE** — elle tient en une minute et elle
tranche : un **A/B `widget grandeurs`** pour savoir si l'artefact suit **la CASE** (⇒ invalidation,
donc un défaut de dessin) ou **la POSITION à l'écran** (⇒ géométrie de bounce, donc la piste
ci-dessus). ⛔ Tant que ce n'est pas fait, **aucune des deux ne doit être écrite comme cause.**

### 20bis.10 🔴 LE TÉMOIN PROVOQUÉ DU COMPTEUR DE PHASE — AC1 est levé, et la carte a corrigé mon modèle

**Séance du 2026-08-27, firmware `42c866e`** (SHA **lu dans le descripteur du binaire**, ⛔ pas récité).
AC1 fait du témoin une **condition d'arrêt** : *« si ça ne le fait pas bouger, l'instrument est faux
et la story s'arrête là »*. Le compteur de **phase** n'en avait jamais eu ; seul `manques` avait le
sien (`flash on`), qui valide l'enroulement, ⛔ pas la phase.

🎯 **LE TÉMOIN CHOISI : DÉPLACER LE WRAP D'UN NOMBRE CONNU DE LIGNES.** `bounce_px` fixe la
géométrie du remplissage à la microseconde près. Changer sa valeur déplace l'instant du wrap d'une
quantité **calculable**, ⛔ pas ajustée. Trois points, **au repos**, fenêtres de 60 s identiques :

| `bounce_px` | lignes / tampon | phase **min** | **moy** | **MAX** | référence figée | `t_demi` |
|---:|---:|---:|---:|---:|---:|---:|
| **9 600** | 20 | 2 244 | **2 257** | 2 298 | 2 258 | 775 |
| **7 680** | 16 | 1 868 | **1 961** | 1 988 | 1 963 | 620 |
| **4 800** | 10 | 1 461 | **1 518** | 1 562 | 1 520 | 388 |

**PRÉDICTION N°1, écrite avant la mesure : −155 µs** (4 lignes × 38,75). **Mesuré : −296 µs.**
⛔ **RATÉE D'UN FACTEUR 2, et c'est écrit tel quel.** Le signe et l'ordre de grandeur étaient bons,
l'amplitude non : j'avais compté **un** tampon de bounce, or le driver en alloue **deux** et les
alterne (`esp_lcd_panel_rgb.c`, `bb_size` × 2). Retirer 4 lignes **par tampon** en retire **8**.

**PRÉDICTION N°2, écrite avant la mesure, sur le modèle corrigé** — 7 680 → 4 800, soit
(10 − 16) × 2 = −12 lignes = **−465 µs ⇒ moy 1 496 µs**. **Mesuré : 1 518 µs. Écart 22 µs = 0,57
ligne**, dans la tolérance d'une ligne annoncée. ✅ **Le modèle ajusté est confirmé sur un point
qu'il n'a pas servi à construire.**

🎯 **LA LOI EST LINÉAIRE, ET SA PENTE EST MESURÉE** : 74,0 µs/ligne entre 20 et 16, 73,8 entre 16 et
10 ⇒ **73,9 µs par ligne de tampon, constante à 0,3 % près**. ⚠️ Le modèle géométrique pur donne
2 × 38,75 = **77,5** : il **sur-estime de 4,6 %**. ⛔ **Écart systématique DÉCLARÉ, NON EXPLIQUÉ**
(FIFO du contrôleur, latence d'amorçage de la DMA : aucune des deux n'est mesurée).

🔴 **ET LA CONTRE-ÉPREUVE DE LA RÉFÉRENCE A CRIÉ SUR LES TROIS LIGNES DE CE TABLEAU** — relevé à la
**3ᵉ revue de code, le 2026-08-27**, ⛔ pas pendant la séance. Sur chaque ligne, `MAX > référence` :
**2 298 > 2 258** (+40) · **1 988 > 1 963** (+25) · **1 562 > 1 520** (+42). La console imprime alors
*« les déficits ci-dessous sont SOUS-comptés de N µs. Refaire `flush reset` au REPOS avant de
conclure »* — ⛔ **et ces trois points ONT ÉTÉ PRIS AU REPOS.** Le remède prescrit était **déjà la
condition de la mesure**.

⚠️ **LA CAUSE EST STRUCTURELLE, ⛔ PAS ACCIDENTELLE.** `ph_ref_us` est le **maximum de 32 trames** de
dégrossissage ; `ph_max_us` est le maximum de la population comptée, qui se chiffre en **milliers**.
Par statistique d'ordre, le max d'un grand échantillon dépasse celui d'un petit tiré de la même loi :
**`MAX > référence` est le résultat ATTENDU** dès que `n ≫ 32`. ⇒ **cette sentinelle ne porte aucune
information**, et son déclenchement le 2026-08-27 — noté à l'époque comme *« elle a tiré au premier
tir »*, c'est-à-dire lu comme un **succès de l'instrument** — ne valait **pas** validation.

🎯 **CE QUE ÇA CHANGE, ET ⛔ CE QUE ÇA NE CHANGE PAS — DÉCISION OWNER DU 2026-08-27 : ON NOTE, ON NE
REFOND PAS.**
- ✅ **AC1 N'EST PAS TOUCHÉ.** Sa loi linéaire porte sur **`moy`**, et le biais de référence
  n'intervient que dans le calcul du **déficit**. Les trois `moy` (2 257 · 1 961 · 1 518) sont
  intactes, la pente de 73,9 µs/ligne aussi.
- ✅ **UN SEUIL FRANCHI L'EST *A FORTIORI*.** Le biais **SOUS**-compte ⇒ le déficit vrai est
  **supérieur** au déficit publié. Un franchissement de `t_demi` est donc un **MINORANT**.
- 🔴 **⛔ MAIS DEUX DÉFICITS NE SE COMPARENT PLUS ENTRE EUX.** Les deux termes portent le même biais,
  dans des proportions inconnues. C'est ce qui fait tomber le rapport de §20bis.11 ci-dessous.
- La console **le dit désormais elle-même**, et elle publie `ph_degrossi_n` à côté de `ph_n` pour que
  le lecteur voie les deux tailles d'échantillon sans avoir à lire le code.

⇒ ✅ **AC1 EST LEVÉ.** L'instrument voit un déplacement **provoqué**, **linéairement**, sur une plage
de **739 µs = 14 × la dispersion au repos (54 µs)**, avec une prédiction écrite d'avance qui tombe à
**0,57 ligne**. **AC3, AC4 et AC5 tiennent.**
⚠️ **CE QUE CE TÉMOIN NE PROUVE PAS** : que le compteur voie une **famine**. Il déplace le wrap par
**géométrie**, ⛔ pas par **contention**. C'est le témoin B qui couvre ça — §20bis.11.

### 20bis.14 🔴 SÉANCE DE VALIDATION DES CORRECTIFS DE LA 3ᵉ REVUE — **2026-08-27**

**Firmware `92e67b5`**, ⛔ **SHA LU DANS LE DESCRIPTEUR DU BINAIRE** (`app_desc`, offset 0x30),
build **12:41:07 Aug 27 2026**, `desknode.bin` **0x11BAA0**.
🎯 **`idf.py reconfigure` A ÉTÉ JOUÉ AVANT LE BUILD**, et le piège est **mesuré comme désarmé** : le
bandeau annonce `App version : 92e67b5`, c'est-à-dire le **bon** commit. Sans ce préalable il aurait
nommé le précédent (`App version` = git HEAD au dernier CMake *configure*, ⛔ pas au dernier build).

**État de départ, relevé AVANT le flash** : `num_fbs=1 bounce_px=9600 draw_lines=128 draw_psram=0
lvgl_core=0`, **aucun témoin de repli en NVS**. **Restauré à l'identique en fin de séance et
VÉRIFIÉ** — `cfg reset` rend exactement ces valeurs, donc la config de départ **était** celle des
défauts.

#### ✅ CE QUI EST ÉPROUVÉ SUR LA CARTE

| | mesure | verdict |
|---|---|---|
| **`fps 15`** | **37,40 Hz**, écart **+0,00 %** — 561 trames en 14 999 436 µs | ✅ **le vsync a survécu à la réécriture de l'ISR.** Contrôle obligatoire d'AC1 |
| **`flush full` isole sa fenêtre** | `flush` juste avant : **72 680 ms** ⇒ `flush full` : **776 ms** (29 trames × 26,7 = 774 ✓) | ✅ **témoin DISCRIMINANT, aucun recouvrement.** Le 3ᵉ site du défaut #780 est fermé |
| **`bounce_px = 0` crie au boot** | **DEUX** cris : le neuf à **t+726 ms** dans le bloc de config (`dn_cfg`), le préexistant à **t+2929 ms** (`dn_mes`) | ✅ avant, **seul le second** sortait — 2,2 s plus tard, hors du bloc qu'on lit |
| **`bounce_px` au-dessus du défaut crie** | `38400` ⇒ *« AU-DESSUS de l'optimum mesuré (9600 px) … Monter au-delà n'achète PAS de marge »* | ✅ **les DEUX moitiés du trou sont fermées** : le zéro ET l'au-dessus |
| **`cfg reset` sans témoin** | *« aucun TÉMOIN DE REPLI n'était en NVS : il n'y avait rien à conserver »* | ✅ avant, il **annonçait la conservation** d'un témoin qui n'a jamais existé |
| **`cfg repli` dit son statut** | *« (clé NVS LUE, et elle répond "rien" — ⛔ pas "je ne sais pas".) »* | ✅ l'absence est désormais **établie**, ⛔ plus affirmée |

#### 📊 LE BLOC DE PHASE, RE-RELEVÉ SUR `92e67b5`

⚠️ **Fenêtre de 29 923 ms qui n'est PAS un repos pur** : elle contient `fps 15` et le trafic console.
⛔ **Ces chiffres ne se comparent donc PAS à ceux de §20bis.11**, dont le repos était propre.

| | |
|---|---|
| trames (vsync) / enroulements | **1119 / 1119** — un pour un, **0 manqué, 0 double** |
| phase | `n = 1087` · min **2140** · moy **2256** · MAX **2267** µs (+32 de dégrossissage, hors stats) |
| référence figée | **2256** µs · 1 ligne = **39** µs |
| déficit pire | **111 µs** pour un demi-bounce de **775** ⇒ **664 µs de marge (85 %)** |
| franchissements | 10 % : **1** · 25 % : 0 · 50 % : 0 · 🔴 **100 % : 0** |

🎯 **LA SENTINELLE `MAX > référence` A TIRÉ UNE QUATRIÈME FOIS** — `2267 > 2256` — sur une mesure
**neuve**, et elle **dit désormais ce qu'elle vaut**, avec les deux tailles d'échantillon
**publiées** par le firmware :

> *« ⛔ CETTE LIGNE EST QUASI-CERTAINE, ce n'est PAS un signal : la référence est le MAX de **32**
> trames, le MAX porte sur **1087**. Un `flush reset` au repos ne la lèvera pas. »*

⇒ **La décision owner (a) — « on NOTE, on ne refond pas » — est validée sur la carte** : le
comportement prédit par lecture est exactement celui qu'on observe, et il est désormais **déclaré à
l'endroit où il se lit**.

#### 🔴 CE QUE LA CARTE A APPRIS, ET QUI N'ÉTAIT PAS AU PROGRAMME

**1. `bounce_px = 0` NE REPRODUIT PAS LE GLISSEMENT DE CETTE STORY — c'est un défaut DIFFÉRENT.**
Constat owner, verbatim : *« décalé verticalement + ça défile à toute vitesse horizontalement »*.
⛔ Le glissement de dn4-10 est **périodique et occasionnel** ; ceci est un **défilement continu à
pleine vitesse** avec décalage vertical. Ce n'est pas non plus le décalage **statique** du piège
`6400`. ⇒ **Ne PAS écrire que `bounce 0` est un témoin positif du glissement.** Il désynchronise
entièrement la DMA du panneau, ce qui est un troisième mode de défaillance.

**2. 🔴 LE FILET DE REPLI N'EST PAS ATTEIGNABLE DEPUIS LA CONSOLE, DONC LE TÉMOIN N'EST PAS
PROVOCABLE.** Le repli s'arme quand `dn_display_init()` rend `ESP_ERR_NO_MEM`. Or
`DN_BOUNCE_PX_MAX = 38 400` est précisément choisi pour que **toute valeur légale alloue** —
et c'est **mesuré** : `panneau RGB prêt : … bounce=38400 px`, **aucun repli**.
🎯 **PRÉDICTION ÉCRITE AVANT LE TIR** (règle L18) : *« 2 × 76 800 o contigus sur un tas de ~283 Kio
quasi vierge à cet instant du boot ⇒ ça alloue, donc aucun repli »*. ✅ **Juste.**
⇒ **Les 7 constats du commit du témoin de repli restent LIVRÉS, NON ÉPROUVÉS**, sauf les deux
ci-dessus (`cfg reset` sans témoin, `cfg repli` qui dit son statut). Ils sont dans la **même classe**
que la branche « référence trop haute » de `358fd95` : un chemin que le code couvre et que la carte
ne sait pas atteindre. ⛔ Ce n'est pas un échec de la séance, c'est une **limite de testabilité**, et
elle se déclare.

**3. ⚠️ `ph_futur` EST À ZÉRO, ET CE ZÉRO NE PROUVE RIEN.** Aucune ligne « ÉCHANTILLONS DE PHASE
JETÉS » ne sort ; la garde étant une **disjonction** sur les quatre compteurs, cela **établit** que
`ph_rejete`, `ph_doubles_ec`, `ph_dechire` **et** `ph_futur` valent tous **0**. ⛔ **Mais `ph_futur`
n'a jamais été vu bouger**, et son déclencheur — l'entrelacement de deux ISR — **ne se commande
pas**. ⇒ *« un compteur qui reste à zéro ne prouve rien tant qu'on ne l'a pas fait bouger »* :
**non éprouvé, déclaré tel.**

**4. ⚠️ L'alerte `bounce_px = 0` ressort à CHAQUE `set`**, pas seulement au boot — `set` relit la
NVS. Le texte reste vrai (« vient de la NVS ») mais c'est **bruyant**. ⛔ Non corrigé, consigné.

#### 🎯 CONSTAT OWNER D'ENDURANCE — **2026-08-27**, ⛔ SUR `358fd95`, PAS SUR LE BINAIRE DE CETTE SÉANCE

Verbatim : *« il restait qu'à tester une session longue et là y'en a eu plein vu que ça tourne depuis
hier »*, précisé en *« plein de sessions, avec l'artéfact des % »*.

⚠️ **DATATION, ET ELLE EST DÉCISIVE** : la carte tournait depuis le **2026-08-26** sur **`358fd95`**.
Le flash de `92e67b5` et les redémarrages ont eu lieu **AU MILIEU de la séance du 2026-08-27** ⇒
**ce constat porte sur `358fd95`**, ⛔ **pas** sur le binaire validé ici.

| ce que l'endurance donne | verdict |
|---|---|
| **Le glissement N'EST PAS REVENU** sur plusieurs sessions de plusieurs heures | ✅ **constat owner FAVORABLE**, et c'est la première mesure d'ENDURANCE du dossier — les campagnes précédentes tenaient en fenêtres de 60 à 431 s |
| **L'artéfact sur les `%` du détail CPU est TOUJOURS LÀ** | ⚠️ **inchangé**. Confirme §20bis.9 et **§20bis.12** : la vue DÉTAIL n'est pas groupée (**4,00 flushes/cycle** contre 1,00 pour la grille) |
| **Le « permanent desync » N'A PAS REPARU** | 🟡 toujours **non revu** — ⛔ et toujours pas « prouvé absent » : **rien ne le mesure**, c'est précisément l'objet de `dn4-12` |

🎯 **CE QUE ÇA CHANGE POUR `dn4-5`** : son **AC3 (soak)** demandait une session longue. Celle-ci n'est
⛔ **pas** un soak instrumenté — aucun compteur n'a été relevé au début ni à la fin, et le firmware
n'était pas gelé. ⇒ **elle ne solde PAS AC3**, mais elle en **retire le doute qualitatif** : le
défaut que le soak devait guetter ne s'est pas manifesté sur des heures d'usage réel.

#### ⚠️ TROIS FAITS DE CHAÎNE, MESURÉS EN PASSANT

- 🔴 **LE BUSID `3-1` DU SKILL `desknode-board` EST FAUX SUR CETTE MACHINE.** La carte est sur
  **`3-5`** ; `3-1` porte un **`V31GT` (`0e8d:201c`)**. Suivre le rituel à la lettre aurait détaché
  **le mauvais périphérique**. ✅ `tools/wsl-attach.sh`, lui, résout le BUSID **par VID:PID à chaque
  appel** — l'outil est juste, c'est sa **documentation** qui récite un numéro figé.
- ⚠️ **`usbipd list` immédiatement après un `detach` rend une liste VIDE** — la carte ré-énumère.
  ⛔ Ne pas en conclure qu'elle a disparu : elle revient en `Shared` en quelques secondes.
- ✅ **COM3 était tenu par `dn_agent.py`** (l'attachement WSL échoue en *« Device busy (exported) »*).
  ⛔ **Pas de `taskkill`** : l'agent a une **sortie propre** par sentinelle (`--stop-si`), qui lui
  fait rendre son bilan. Arrêt confirmé en < 10 s, relance à l'identique en fin de séance,
  **un seul `python.exe`** au compte final — aucun reste. ✅ **Et la reprise est confirmée À L'ŒIL** :
  constat owner, le dashboard réaffiche des **données vivantes**. ⛔ C'est la seule preuve de bout en
  bout — la console est côté Windows après le `detach`, donc l'agent ne peut plus être interrogé
  depuis WSL.


### 20bis.11 ✅ LE TÉMOIN B — la famine provoquée par le trafic RÉEL

Agent RÉEL sur la tour, 5 trames/s, mode `on`, `bounce_px = 9 600`, **même binaire, même référence,
même géométrie** que la ligne de repos ci-dessus :

| | repos, 60 s | **agent RÉEL, 431 s** |
|---|---:|---:|
| déficit pire | **14 µs** | **784 µs** (seuil 775 ⇒ **dépassé de 9**) |
| 🔴 100 % (CORRUPTION) | **0** | **62** — soit 0,144 /s |
| 10 % · 25 % · 50 % | 0 · 0 · 0 | 582 · 85 · 77 |

⇒ 🔴 **0 → 62 SUR LES CORRUPTIONS.** Le compteur **discrimine** repos et trafic.
✅ **Le témoin B est acquis** — et il l'est sur **ce** passage-là, ⛔ pas sur un rapport.

⛔ **LE « × 56 » A ÉTÉ RETIRÉ — DÉCISION OWNER DU 2026-08-27, 3ᵉ REVUE DE CODE.** Ce paragraphe
publiait *« × 56 sur le déficit pire »* (784 / 14). ⛔ **Ce quotient n'est pas défendable** : la
contre-épreuve de la référence figée (voir §20bis.10 ci-dessus) déclare les déficits **sous-comptés
de 25 à 42 µs**, et ce biais frappe **le numérateur ET le dénominateur**. Sur un dénominateur de
**14 µs**, un biais de cet ordre le change d'un **facteur 3 ou 4** ; sur un numérateur de 784 µs il
est négligeable. ⇒ le rapport est dominé par l'erreur, dans une proportion **inconnue et non
mesurée**.

✅ **CE QUI RESTE, ET QUI SUFFIT** : les deux relevés bruts ci-dessus, et le passage de **0 à 62
corruptions**. Un compteur qui passe de zéro à soixante-deux **discrimine** — ⛔ il n'a pas besoin
d'un quotient pour le prouver, et le quotient n'ajoutait rien qu'une fausse précision.
⚠️ **Le `dépassé de 9 µs` sur le seuil de 775 TIENT**, et il tient *a fortiori* : le biais
sous-compte, donc le déficit vrai est **au-dessus** de 784.

⛔ **ET ON NE COMPARE PAS AUX 0,94 /s DE §20.7.19.** Référence (cliquet → figée), population
(min/MAX mélangés → disjoints), période (tronquée → arrondie) **et** `bounce_px` (7 680 → 9 600) ont
**tous** changé. Publier un rapport entre les deux serait le chiffre faux mais plausible que ce
dépôt traque.

### 20bis.12 🔴 L'ARTEFACT DES `%` A UNE CAUSE — **LA VUE DÉTAIL N'EST PAS GROUPÉE**

Le constat owner du 2026-08-27 (§20bis.9) est resté **sans cause attribuée** une demi-journée.
Il en a une, et elle était **déjà écrite au dossier** : §20.7.19 pt 1 pose que *« le groupage est une
**ATOMICITÉ** : une case = UNE zone sale = UN flush »*. **La grille l'a. Le détail ne l'a pas.**

**A/B, 4 bras ALTERNÉS**, stimulus identique (`widget pousser 0` × 3 200, ⛔ valeurs **variables** —
`(s_pousse_seq × k_mul) % 100` — donc **vrai dessin**), **la même case poussée dans les deux vues** :

| | **détail CPU** B1 / B2 | **grille** A1 / A2 |
|---|---:|---:|
| durée pour 3 200 poussées | **194 / 196 s** | **106 / 107 s** |
| 🔴 **flushes par cycle** | **4,00 / 3,98** | **1,00 / 1,00** |
| phase **min** | **1 473 / 1 481** | 1 852 / 1 583 |
| déficit pire | **789 / 781 → DÉPASSÉ** | 407 / 679 → sous le seuil |
| 🔴 100 % (CORRUPTION) | **31 / 12** | **0 / 0** |
| px par flush | 18 133 (5,9 %) | 36 630 (11,9 %) |

🎯 **AUCUNE STATISTIQUE NE SE RECOUVRE ENTRE LES DEUX VUES**, et `flushes/cycle` sépare **4,0 de 1,0**
sans la moindre dispersion. ⇒ **une mise à jour du détail coûte QUATRE flushes**, donc **quatre
rendez-vous de synchro**, donc **quatre fenêtres où la DMA peut décrocher** — contre **une** sur la
grille.

⇒ 🎯 **ÇA RÉCONCILIE LES DEUX FAITS QUI SEMBLAIENT INCOMPATIBLES.** La famine est **globale par
nature** (elle décale toute la trame), mais elle n'est **provoquée** que quand le détail se
repeint : d'où un artefact qui ne se voit **que là**. ⛔ L'objection *« un décalage DMA ne peut pas
être local »* tombe — ce n'est pas le **décalage** qui est local, c'est sa **cause**.

⚠️ **CE QUI RESTE NON ÉTABLI, ET IL FAUT LE LIRE AVEC LE TABLEAU** :
- que l'artefact **vu par l'owner** SOIT cette corruption — la corrélation œil ↔ compteur d'AC2
  **n'a pas été refaite dans cette vue** ;
- le stimulus est la console à **28 poussées/s sur une case**, ⛔ pas l'agent à **1/s par case** :
  c'est **~5× plus agressif**, et le tableau mesure un **contraste**, pas un régime ;
- la cadence : 12–31 corruptions sur ~195 s = **0,06–0,16 /s** contre *« toutes les 5 s »* = 0,2 /s
  à l'œil. **Même ordre, ⛔ pas la même valeur.**

⚠️ **ET UNE LEÇON D'INSTRUMENT, PAYÉE ICI** : entre deux bras **identiques**, `phase min` bouge de
**8 µs** côté détail mais de **269 µs** côté grille, et le compte de corruptions varie de **× 2,6**
(31 → 12). ⇒ **`flushes/cycle` est la statistique solide ; le COMPTE de corruptions ne l'est pas.**
Une conclusion bâtie sur le seul compte, sur une seule paire, aurait été indéfendable.

### 20bis.13 ⚠️ LE BANDEAU PEUT NOMMER LE MAUVAIS COMMIT — mesuré le 2026-08-27

🔴 **« SHA LU AU BANDEAU » A UN TROU, ET IL EST SYSTÉMATIQUE DANS CE DÉPÔT.**
`App version` vient de `git describe` évalué **au dernier CMake *configure***, ⛔ **pas au dernier
*build***. Or le rythme d'ici est **build → flash → mesure → commit** : le champ nomme donc le
commit **PRÉCÉDENT**.

**MESURÉ SUR MON PROPRE BINAIRE** : `desknode.bin` déclarait **`4cf35ae`** alors que `HEAD` valait
**`42c866e`** — exactement **un commit de retard**. Après `idf.py reconfigure`, il déclarait
`42c866e`, **taille inchangée** (0x11aa90).

⇒ **CE QUE ÇA A COÛTÉ DANS CETTE SÉANCE** : la story affirmait *« la carte porte `1adf259` »*
depuis le 2026-08-24. **Faux.** Le bandeau disait `c31bb97` et le binaire, compilé le
**26/08 à 17:24:26**, contenait déjà le correctif `fenetre_deborde` de **`afee371`** — commité à
**21:48**, quatre heures plus tard. C'est la **sortie de `flush` elle-même** qui a démenti le
bandeau, ⛔ pas une relecture.

🔧 **LES DEUX RÈGLES QUI EN SORTENT** :
1. **`idf.py reconfigure` AVANT le flash de référence**, sinon l'étiquette ment.
2. Le champ fait foi **seulement** confronté à `Compile time` — et la vraie preuve du contenu reste
   **ce que le binaire IMPRIME**. Ici, `flush` a tranché en une ligne.
3. Lire le descripteur sans la carte : offset **0x20** du `.bin`, `version[32]` à **+16**.

## 20ter. 🎯 `dn4-12` — LE COMPTEUR SAIT ENFIN DIRE QU'UN ÉTAT A **DURÉ** (2026-08-28)

> ⚠️ **SECTION AJOUTÉE, ⛔ RIEN N'EST RENUMÉROTÉ.** §20.1 à §20.7 et tout §20bis restent
> **intacts** : ils sont justes pour leur date. §20bis.8 reçoit un **renvoi** vers ici, et son
> texte d'origine est conservé.

> 🔴 **ÉTAT DE CETTE SECTION AU MOMENT OÙ ELLE EST ÉCRITE.** Elle consigne ce qui est **livré et
> mesuré SANS LA CARTE** : la machine à états, sa gate hôte, et le coût lu dans le `.map`.
> ⛔ **Aucune mesure de régime n'y figure encore** : le témoin provoqué (§20ter.6), les fenêtres
> sous agent réel et la nuit **attendent la séance carte**, qui demande un budget d'arms de
> l'owner. **Ce qui n'a pas été mesuré est nommé, ⛔ pas passé sous silence.**

### 20ter.1 🔴 LE TROU, ET POURQUOI IL A SURVÉCU À `dn4-10`

L'owner décrit, le 2026-08-23, un défaut qui **DURE** :

> *« parfois ça reste dans un état glissé […] ensuite ça reglisse »*

Le driver Espressif nomme ce cas **« permanent desync »** et écrit que `RESTART_IN_VSYNC` existe
pour l'empêcher (`esp_lcd_panel_rgb.c:1142-1148`). Nous avons **désactivé** ce flag le 2026-08-23
(`4734d07`) parce qu'il **FABRIQUAIT** le glissement périodique (§20bis.1). Conséquence, et elle
n'était écrite nulle part :

🔴 **le permanent desync n'a plus AUCUNE parade automatique — et RIEN NE LE MESURE.**

Le compteur de `dn4-10` compte des **trames au-dessus d'un seuil**, jamais leur **consécutivité**.
Il ne peut donc **ni confirmer ni infirmer** le constat de l'owner. Et §20bis.5 a montré pourquoi
il ne suffit pas : **143 corruptions AVANT COMME APRÈS** le correctif, pendant que l'œil passait de
*« ça descend et remonte toutes les secondes »* à *« plus de glissement »*.

⚠️ **CE QUE `dn4-12` NE FAIT PAS** : elle **ne branche pas la parade**. La décision `D4` est
explicite — le ré-armement automatique de `dn_recal` se branchera **après** que cet instrument aura
dit ce que son seuil de déclenchement doit valoir. Écrire ce seuil maintenant reviendrait à poser
un critère **avant d'avoir mesuré la dispersion de ce qui le mesurera** : le défaut que ce dépôt a
déjà payé deux fois.

### 20ter.2 🔴 LE PIÈGE CENTRAL — LE GLISSEMENT RECHERCHÉ EST **JETÉ** PAR L'INSTRUMENT

C'est le constat le plus court du cadrage, et le plus embarrassant : `ph_rejete`
(`dn_measure.c`, borne de sanité) écarte les phases `>= 2 périodes`, et **le code l'écrit
lui-même** :

> *« 🔴 LA BORNE DE SANITÉ ÉCARTE EXACTEMENT LE GLISSEMENT RECHERCHÉ »*

⇒ **un compteur de série branché naïvement dans la population COMPTÉE rendrait « plus longue série
= 0 » PENDANT QUE L'ÉCRAN EST FIGÉ EN GLISSEMENT PERMANENT** — l'exact inverse du livrable.

C'est la **décision D2** : `ph_rejete` **compte EN DÉFAUT**, il ne rompt pas la série.

### 20ter.3 🔴 LA TABLE DES HUIT CLASSES DE TRAME — LA PIÈCE QU'UN LECTEUR CHERCHERA EN PREMIER

**SIX classes de trame n'atteignent JAMAIS le site du déficit**, et aucune source du dépôt ne les
énumérait ensemble avant `dn4-12`. Leur sort est tranché **une par une** :

| # | Classe | Condition dans `on_vsync` | Compteur existant | **Verdict** |
|---|---|---|---|---|
| **A** | déficit franchi | `n == 1`, phase comptée, `déficit > t_demi_us` | `ph_100pc` | 🔴 **EN DÉFAUT — la série CONTINUE** |
| **B** | saine | `n == 1`, phase comptée, `déficit <= t_demi_us` | — | ✅ **SAINE — la série SE ROMPT** |
| **C** | hors borne de sanité | `n == 1`, `ph >= 2 × période` | `ph_rejete` | 🔴 **EN DÉFAUT — la série CONTINUE** (D2) |
| **D** | aucun enroulement | `n == 0` | `manques` | 🔴 **EN DÉFAUT — la série CONTINUE** |
| **E** | horodatage postérieur | `(int32_t)(t_us − tw) < 0` | `ph_futur` | ⚠️ **INDÉTERMINÉE — rompt ET est comptée** |
| **F** | paire `(wraps, t_wrap)` déchirée | `w2 != w` | `ph_dechire` | ⚠️ **INDÉTERMINÉE — rompt ET est comptée** |
| **G** | deux enroulements ou plus | `n >= 2` | `ph_doubles_ecartes` | ⚠️ **INDÉTERMINÉE — rompt ET est comptée** |
| **H** | dégrossissage | `ph_ecarte < 32` | `ph_ecarte` | ⛔ **HORS SUJET — ni l'un ni l'autre** |

**LE MOTIF DE CHAQUE VERDICT — ⛔ ÉCRIT, PAS SUPPOSÉ :**

- **C compte EN DÉFAUT** : voir §20ter.2. Une série qui se romprait là rendrait **0 pendant que
  l'écran est figé**.
- **D compte EN DÉFAUT** parce que **le témoin de référence du dépôt l'impose** : `flash on` +
  `bounce_px != 0` (mesure du 2026-08-22) rend **1 037 trames SANS enroulement sur 1 041**. Si
  `manques` rompait la série, **le témoin le plus violent du dépôt rendrait une plus longue série
  de ~1 pendant que la dalle est détruite** — l'instrument serait **aveugle exactement là où il
  doit hurler**.
- **E / F / G ROMPENT** parce qu'on **ne sait pas** si la trame était saine. Les faire continuer
  **FABRIQUERAIT** de la durée. Rompre **sous-estime** — et **un minorant tient a fortiori**. Le
  prix est **publié** : `ser_rompues_indet` compte les séries qu'une indéterminée a coupées.
- **H ne fait ni l'un ni l'autre** : avant que `ph_ref_us` soit figée, **aucun déficit n'est
  calculable**.

> ⚠️ **UN POINT A ÉTÉ TRANCHÉ PAR LE DEV, ET IL EST DÉCLARÉ.** Le motif de **H** dit *« la série ne
> commence qu'après le dégrossissage »*. Pris à la lettre **pour toutes les classes**, cela
> armerait la machine seulement une fois `ph_ref_us` figée. ⛔ **Ce serait faux, et dangereux** :
> les classes **C** et **D** ne lisent **ni la référence ni le seuil**, et **sous `flash on` le
> dégrossissage n'avance même pas** — il ne se nourrit que de trames à `n == 1`, or 1 037 sur 1 041
> n'ont aucun enroulement. Une machine armée sur le dégrossissage rendrait donc **« plus longue
> série = 0 » pendant que la dalle est détruite** : mot pour mot le mode de défaillance que la
> condition d'arrêt de la story déclare comme *« l'instrument est FAUX »*.
> ⇒ **LA TABLE FAIT AUTORITÉ : C et D comptent TOUJOURS.** Seule la classe **A** exige le
> dégrossissage, donc **une série de classe A ne peut pas commencer avant la 32ᵉ trame** — ce que
> la gate épingle, et ce que la console dit.

### 20ter.4 🔴 L'UNITÉ EST LA **TRAME**, ⛔ PAS LA MICROSECONDE — ET C'EST UN ARGUMENT DE CONCEPTION

`esp_timer` reboucle à **2^32 µs = 71,58 min** : c'est le défaut que `dn4-5`/AC1.2 vient de fermer
sur `fenetre_ms`. Un **compte de trames** ne reboucle qu'à **2^32 trames**, soit **~3,6 ans à
37,40 Hz**.

⇒ **la grandeur survit à une nuit et à une semaine PAR CONSTRUCTION**, ⛔ pas par précaution. La
conversion en millisecondes se fait **côté console**, depuis `periode_ns` (**26 737 500 ns**, exacte)
— ⛔ **jamais dans l'ISR**.

### 20ter.5 🎯 CE QUE `flush` PUBLIE MAINTENANT — UN **TRIPLET**, ⛔ PAS LE MAX NU

Le **DÉPASSEMENT** du seuil était enterré en **sous-ligne** du « DÉFICIT PIRE », lui-même au milieu
du bloc, pendant que le **COMPTE** — qui **ne suit plus l'œil** depuis `4734d07` — sortait en
évidence. **C'est un défaut de présentation réel, et il est corrigé.**

⚠️ **MAIS LA GRANDEUR DE TÊTE EST UN TRIPLET — DÉCISION OWNER DU 2026-08-28.** Le livrable d'origine
demandait le dépassement **seul**, sur la foi du tableau `+720 / +176 / +221 µs` du 2026-08-23. Or
ce tableau **compare trois `ph_deficit_max_us` entre eux** — ce que `dn_console.c` **interdit en
toutes lettres** (*« ils portent le même biais »*) — et **`dn4-22` l'a réfuté PAR LA MESURE** cinq
jours plus tard : **ARM 5 rend 1 300 µs de déficit pire pour UNE corruption, contre 896 µs pour
245** chez `f7be23c`. ⇒ **le MAX n'est pas un discriminateur : un seul point aberrant le déplace.**

L'ordre de tête est donc :

1. **① la PLUS LONGUE SÉRIE** de trames consécutives non saines, en **trames** et en **ms**, avec sa
   **composition (A / C / D)**, sa **trame de début** (depuis la RAZ), le **nombre de séries**, la
   **série EN COURS**, et le nombre de **séries rompues par une indéterminée** — ⚠️ **c'est un
   MINORANT, et la console l'écrit** ;
2. **② la DISTRIBUTION** des quatre seaux `10/25/50/100 %` — 🎯 **le signal jugé fiable par
   `dn4-22`** (⛔ seaux **emboîtés**, ne pas les sommer) ;
3. **③ le DÉPASSEMENT** du seuil, **avec sa RÉFUTATION IMPRIMÉE JUSTE DESSOUS** — le chiffre de
   `dn4-22` est donné dans la sortie elle-même, ⛔ pas seulement connu.

Puis, **en second**, le **COMPTE** `ph_100pc` **avec sa réserve** (143 avant comme après), et les
**cinq chiffres de comparabilité** (`ph_ref`, `ph_max`, `ph_n`, `ph_degrossi_n`, `t_demi`) plus
**l'instant de la dernière RAZ** — ou, à défaut, la ligne
**`⛔ AUCUN flush reset : référence SEMÉE AU BOOT`**.

🎯 **LA COMPOSITION N'EST PAS DÉCORATIVE.** Elle sépare *« la DMA a lu un tampon pas encore rempli
200 fois de suite »* (classe A) de *« la DMA n'a pas fini une seule trame pendant 200 trames »*
(classe D) : **deux pathologies différentes, deux remèdes différents**.

### 20ter.6 ⏳ CE QUI ATTEND LA CARTE, ET CE QUE CHAQUE TIR DOIT RENDRE

⛔ **RIEN DE CE BLOC N'EST MESURÉ À CE JOUR.** Il est écrit **avant** la séance, pour que l'attendu
ne soit pas rédigé après coup.

> 🎯 **JOUÉ LE 2026-08-29 — LES RÉSULTATS SONT EN §20ter.10, ⛔ ET CE TABLEAU N'EST PAS RÉÉCRIT.**
> Il reste tel quel parce que c'est **l'attendu écrit AVANT**, et que c'est sa seule valeur. ⚠️ Deux
> de ses lignes ont été **réfutées par la mesure** : le témoin `flash on` est **désarmé** sur ce
> binaire (0 au lieu de 1 037/1 041) et « deux durées » ne peut pas être joué faute d'un stimulus qui
> **dure**. La ligne « régime réel » est **tenue, et son attendu était juste** : la série y vaut
> **zéro**.

| Tir | Protocole | **Attendu, écrit AVANT** |
|---|---|---|
| **Témoin provoqué** | boot (SHA au bandeau) → **≥ 3 min** → `flush reset` → `flash on` → fenêtre → `flash off` → `flush` | une plus longue série de **plusieurs CENTAINES de trames**, **dominée par la classe D** (référence : 1 037 / 1 041). ⛔ **Si la grandeur ne bouge pas, l'instrument est FAUX et la story s'arrête là.** |
| **Deux durées** | deux tirs `flash on` de rapport **≥ 3** (~10 s et ~35 s), `flush reset` entre | deux séries dont le **rapport suit celui des durées**. ⛔ Un écrêtage ou une saturation se verrait **ici**. |
| **Régime réel** | **≥ 3 × 180 s** sous **AGENT RÉEL** (⛔ jamais l'injecteur : facteur **108** sur le dessin), bras alternés, **dispersion publiée** | la plus longue série doit être **COURTE** (le glissement périodique est corrigé ; il reste ~130-150 corruptions / 180 s, mais **isolées**). 🎯 **Une série longue en régime nominal serait le permanent desync PRIS SUR LE FAIT** — et cette story **n'a pas le droit de le fabriquer.** |
| **Coût en marge de famine** | même protocole avant/après : pire déficit, les 4 seaux, CORRUPTION | ⛔ **à MESURER, pas à déduire** — voir §20ter.8. |
| **La nuit** | protocole §24.16.1 (agent → WSL **ne reboote pas**) | ⚠️ **asymétrie écrite AVANT le résultat** : série **COURTE ⇒ CONCLUANT a fortiori** (le biais sur-compte) · série **LONGUE ⇒ ⛔ NON CONCLUANT** sans vérifier la référence (symptôme : **le seau 10 % vaut presque `n`**) ⇒ la nuit se **rejoue**, elle ne se **conclut** pas. |

### 20ter.7 ✅ LA GATE HÔTE — `tools/verif_serie_dn412.py`, **50 OK / 0 KO**

**Archetype B : elle COMPILE et APPELLE le produit**, ⛔ elle ne relit pas du source. **Deux étages,
et les deux sont le produit** :

- **étage 1** — `dn_measure_serie.h` compilé seul, ses trois fonctions appelées directement. C'est
  le **seul** étage qui peut exercer la **classe F** (`ph_dechire`) : son déclencheur est que
  `s_bnc_wraps` change **entre les deux lectures `w` et `w2`, à l'intérieur de l'ISR**, et il
  n'existe **aucun point d'entrée de coquille entre ces deux lignes**. C'est exactement le sort de
  `ph_futur`, déclaré *« JAMAIS VU BOUGER »* par `dn4-10` — **et c'est la raison qui a fait choisir
  l'unité pure** ;
- **étage 2** — `dn_measure.c` **compilé en entier**, sa **vraie `on_vsync`** appelée via les
  callbacks que `dn_measure_attach()` enregistre. C'est lui qui prouve **le BRANCHEMENT** : un
  étage 1 vert avec un branchement faux serait une gate *« verte sur du code faux »*, et le dépôt en
  a déjà épinglé une.

🎯 **La table `SHIMS` (16 coquilles) est REPRISE de `verif_rebouclage_dn45.py`, ⛔ pas réinventée.**

**CINQ MUTANTS, CHACUN VU ROUGIR**, tous dans la passe nominale (⛔ aucun derrière un drapeau
optionnel qu'aucun runner ne passe) :

| Mutant | Ce qu'il casse | **Ce qu'on l'a vu faire** |
|---|---|---|
| **M1** | l'écrêtage posé **AVANT** le comptage (le défaut exact de `dn_hist_rattraper()`) | **200 et 700 trames rendent LE MÊME nombre (121)** — la durée est effacée avant d'être comptée |
| **M2** | la classe **C** **rompt** au lieu de continuer (D2 renversée) | 7 trames hors borne rendent **max = 0** : **zéro pendant que l'écran est figé** |
| **M3** | une **indéterminée** continue la série en silence | `rompues = 0` au lieu de 3, **et la série GONFLE de 2 à 6** : la durée est **FABRIQUÉE** |
| **M4** | un champ neuf **oublié dans la branche RAZ** | un champ ne revient pas à zéro ⇒ **le témoin n'est plus rejouable** |
| **M5** | un champ neuf **non traduisible** par le miroir `ctypes` | `verif_rebouclage_dn45.py` **CRIE et NOMME le champ**, ⛔ ne meurt pas en silence — **les DEUX chemins** de refus sont épinglés (tableau **et** type non mappé) |

⚠️ **UN CONTRÔLE DE CETTE GATE A ÉTÉ REFAIT PARCE QU'IL NE SAVAIT PAS CRIER.** La première version
de *« ⛔ aucune division dans `on_vsync` »* passait un `re.sub` inutile et **n'avait jamais été vue
rougir** : elle aurait pu être verte pour la mauvaise raison. Elle a **son témoin négatif** désormais.
⚠️ **Et le critère du mutant M1 était faux à UNE UNITÉ PRÈS** : il exigeait un plafond de `120` là où
la mutation en produit `121`. ⛔ **La propriété à épingler n'est pas la valeur du plafond, c'est que
deux durées de rapport 3,5 cessent de se distinguer** — le critère a été réécrit sur la propriété.

⛔ **CE QUE CETTE GATE NE PROUVE PAS**, écrit dans son en-tête : **rien** sur le comportement sous
**ISR réelle** (ici les callbacks sont appelés depuis une tâche Linux, en séquence, sans préemption
ni cache coupé) · **rien** sur la **concurrence** (l'invariant « un seul écrivain » est vérifié **par
lecture**, ⛔ pas par course) · **rien** sur les **valeurs de phase produites par le silicium**.

### 20ter.8 🔴 LE COÛT, **LU DANS LE `.map`**, ⛔ PAS ESTIMÉ

**Deux builds**, sources pristine puis modifiées, `idf.py reconfigure` **avant chacun**.

| grandeur | AVANT | APRÈS | écart |
|---|---|---|---|
| `.bss` de `dn_measure.c.obj` | 218 o | 266 o | **+48 o** |
| `.iram1` (🔴 **`on_vsync`**, résidente) | 1 433 o | 1 789 o | **+356 o** |
| `.text` flash de `dn_measure.c.obj` | 2 457 o | 2 687 o | +230 o |
| **`.rodata` de `dn_measure.c.obj`** | 2 336 o | 2 336 o | ✅ **+0** |
| `.text` de `dn_console.c.obj` | 46 076 o | 46 568 o | +492 o |
| `.rodata` de `dn_console.c.obj` | 151 250 o | 155 582 o | +4 332 o |
| **image `desknode.bin`** | **1 179 984 o** | **1 185 568 o** | **+5 584 o (+0,473 %)** |

🎯 **LA PRÉDICTION `.bss` ÉTAIT ÉCRITE AVANT LA MESURE : 48 octets (12 `uint32_t`). MESURE : 48
octets. ÉCART NUL.** ⛔ La prédiction n'a pas été réécrite pour tomber juste — c'est l'écart qui
s'écrit, et il est nul. Repère : tout le compteur de `dn4-10` coûte **74 o**.

✅ **`.rodata` de `dn_measure.c` : +0.** C'est la conséquence directe du choix `#define` plutôt que
`static const` — **aucun accès `.rodata` ajouté depuis l'ISR**, et la `.rodata` vit en flash, que
l'ISR peut lire **cache coupé** pendant une écriture flash.

🔴 **ET VOICI LE FAIT QUI COMPTE POUR §26 : LA CROISSANCE DU CHEMIN CHAUD EST EN IRAM, ⛔ PAS EN
FLASH CACHÉE.** `on_vsync` est `IRAM_ATTR` ; ses **+356 octets** vivent dans une mémoire **toujours
résidente**, qui **ne subit pas de défaut de cache**. Le mécanisme de §26 — du code réparti dans les
fonctions, cherché en flash à travers le cache, en concurrence avec la DMA — **ne s'applique donc
pas à `on_vsync` lui-même**.

> ⛔ **ET CE N'EST PAS UNE CONCLUSION : C'EST UNE HYPOTHÈSE QUI RESTE À MESURER.** §26 a été établi
> **par la mesure**, et **par un temoin qui a réfuté l'intuition volumétrique** (1 236 octets de
> `.text` MORT rendant une image plus grosse **et** la fenêtre la plus propre de la campagne). Un
> raisonnement sur le placement **ne remplace pas** un relevé avant/après sous agent réel. **C'est
> le tir « coût en marge de famine » de §20ter.6, et il n'a pas eu lieu.**
> ⚠️ **Rappel du repère de sensibilité** : le coût des 17 correctifs de `dn4-5` s'est révélé **non
> distinguable de zéro** (Δ ≤ 0,1 pt sur 24 % de charge, **de signe opposé à un coût réel**), et
> l'étendue de référence est **0,05 pt** sur n = 3. ⇒ ⛔ **ne rien conclure d'un Δ inférieur à
> l'étendue**, et ⛔ **ne pas comparer à un échantillon unique**.

⚠️ **Les +4 332 o de `.rodata` de `dn_console.c` sont les CHAÎNES du bloc de tête.** `dn_console.c`
n'est **pas** sur le chemin chaud : ce coût est en flash, payé une fois à l'image, ⛔ pas par trame.

✅ **Le témoin a survécu au linker** : `.bss.s_bnc_serie` **48 o** est présent dans le `.map`.
C'est la vérification qu'exige `dn4-22`, qui avait **brûlé un arm** parce qu'un témoin de 1 064
octets avait été **supprimé par `--gc-sections`** — `__attribute__((used))` retient le
**compilateur**, ⛔ **pas** le linker.

### 20ter.9 ⛔ CE QUE CET INSTRUMENT NE PROUVE PAS — ET NE POURRA PAS PROUVER

1. 🔴 **LE NOMBRE DE RELANCES RÉELLEMENT JOUÉES PAR LE DRIVER RESTE INOBSERVABLE** à
   `RESTART_IN_VSYNC=n` : il relance **en interne sans passer par `need_restart`**
   (`esp_lcd_panel_rgb.c:1153-1163`), donc `recal` compte **1** (l'amorçage) et rien d'autre
   (§20bis.8). ⇒ **contrainte de conception : on mesure la PERSISTANCE DE L'ÉTAT, ⛔ jamais l'échec
   de relance.**
2. **Plancher = la microseconde = 16 pixels** à `pclk = 16 MHz`. ⛔ « 0 » **ne veut pas dire**
   « 0 pixel ».
3. **Un retard COMMUN aux deux ISR s'annule et reste invisible** — l'horodatage de référence vient
   lui aussi d'une ISR.
4. **La plus longue série est un MINORANT** : E, F et G rompent, donc une série vraie a pu être
   **coupée en deux**. Le nombre de ces coupures est publié — ⛔ **il ne se soustrait pas et ne se
   recompose pas**.
5. **Une nuit n'est pas une semaine.** Le soak 7 jours reste à `dn4-5` ; une nuit **arme** le
   critère n°1 du brief, elle **ne le coche pas**.
6. ⚠️ **À `bounce_px < 480` la classe A n'existe plus** et la ligne est **REFUSÉE**, ⛔ pas imprimée
   à zéro (*« un zéro se lirait "aucune corruption" »*). Le refus **dit laquelle des trois classes
   est perdue** : **C** et **D** restent comptables, seule **A** disparaît.
7. ⚠️ **Le 3ᵉ mode de défaillance de `bounce_px = 0`** (*« décalé verticalement + ça défile à toute
   vitesse horizontalement »*) reste **constaté et non caractérisé** — hors périmètre.

### 20ter.10 🔴 LA SÉANCE CARTE DU 2026-08-29 — L'INSTRUMENT SAIT VOIR, ET LA CARTE A CASSÉ TROIS DE MES PROTOCOLES

> **Binaire `b1a810f`, SHA LU AU BANDEAU** (`App version : b1a810f`, `Compile time : Aug 29 2026
> 00:11:02`), XIP confirmé **à l'exécution** (`mmu_psram: Instructions copied and mapped to SPIRAM`).
> Config : `num_fbs=1 bounce_px=9600 draw_lines=128 draw_psram=0 lvgl_core=0`, seuil **775 µs**.
> **2 arms accordés + 1 en réserve** (décision owner). ⛔ **L'arm de réserve N'A PAS été dépensé.**

#### ✅ AC1.9 EST LEVÉ — L'INSTRUMENT SAIT VOIR, ET IL RETOMBE QUAND LA CAUSE EST RETIRÉE

La preuve est faite **dans les deux sens**, ce que ce dépôt exige :

| tir | ce qui tourne | plus longue série | composition |
|---|---|---|---|
| **T7** | `ui bg psram` **SEUL** (⛔ ni animation ni stimulus flash) | **3 trames ≈ 80 ms** | 3 D |
| **T8** | animation + `flash on` **acceptés**, 90 s, ⛔ **aucune reconstruction de scène** | **0** | — |
| **T9** | reproduction de T7 | **3 trames ≈ 80 ms** | 3 D |

⇒ **retirer la cause fait retomber le compteur, la remettre le fait remonter.** La cause est la
**RECONSTRUCTION DE SCÈNE** (`ui bg …`), qui prend le verrou LVGL et repose une image de 614 400 o :
pendant ~80 ms la DMA n'obtient pas ses enroulements ⇒ **3 trames consécutives de classe D**.

🎯 **ET C'EST LA DÉMONSTRATION DE CE QUE `dn4-12` AJOUTE.** Sur le même événement (tir T3, qui
portait en plus un `flash on`) :
- le compteur de `dn4-10` dit **« 1 corruption »** ;
- le compteur de `dn4-12` dit **« un état dégradé a duré 4 trames consécutives ≈ 106 ms, dont
  3 sans enroulement (D) et 1 franchissement (A) »**.

Ce sont **deux informations différentes**, et la seconde est **celle que l'owner demandait** : la
DURÉE. La composition **1 A + 3 D** est exactement ce que la table des huit classes promettait — deux
pathologies dans une même série.

#### 🔴 CE QUE LA CARTE A CASSÉ CHEZ MOI — TROIS PROTOCOLES, ET LE PREMIER A FAILLI PUBLIER UNE CONCLUSION FAUSSE

**(1) J'ALLAIS ÉCRIRE QUE LE TÉMOIN DE RÉFÉRENCE DU DÉPÔT ÉTAIT MORT. C'ÉTAIT FAUX.**
`flash on` a rendu **0** sur 60 s à plein débit (**169 898 o/s**, le débit de référence), et
`bounce 480` — que §20.7.6 mesure à `manques = 290 / 4 873` — a rendu **0** lui aussi. J'ai conclu
que le remède XIP avait supprimé la famine à la racine.
⛔ **RÉFUTÉ PAR LA RELECTURE DE L'ÉTAT RÉEL** : `veille` disait **`mode : AMBIENT · veille ARMEE ·
inactivite 403 s`**. La veille tombe à **60 s** d'inactivité, donc **avant la fin de presque toute
fenêtre console**. Le chiffre qui tranche : **14 flushes en 60 s (0,23 /s)** contre **1 620 en 321 s
(5,05 /s)** sous agent réel — **FACTEUR 22**. *« Une image statique ne déchire pas. »*
⇒ **RÈGLE** : toute fenêtre console qui mesure la famine DMA **relit `veille` avant de tirer** et
**publie son débit de flushes à côté de son résultat**. `veille off` n'est pas une précaution, c'est
une **condition de validité**.

> 🔴 **AMENDÉ LE 2026-08-29, QUELQUES HEURES PLUS TARD — ⛔ LE TEXTE CI-DESSUS RESTE, MAIS IL NOMME
> LA MAUVAISE CAUSE, ET C'EST MOI QUI L'AI ÉCRIT.** J'ai attribué le vide à **la veille**. ⛔ **Faux** :
> **sous agent réel, en AMBIENT, la carte DESSINE** — mesuré en rendant le port à l'agent puis en le
> reprenant : `mode : AMBIENT · bascules -> Ambient : 1 · reveils : 0` après 32 min d'agent continu,
> et pourtant **5 226 cycles de redessin / 1 960 s = 2,67 cycles/s**. **La veille masque la scène,
> elle ne supprime pas le redessin.**
>
> **CE QUI MANQUAIT À LA FENÊTRE VIDE, C'EST LE STIMULUS DE DESSIN** — ni agent (qui fait **bouger
> les cases**, donc déclenche l'invalidation), ni animation. La table, en **cycles de redessin par
> seconde**, ⛔ pas en flushes :
>
> | régime | cycles/s | rapport à la fenêtre vide |
> |---|---|---|
> | ni agent ni animation, en veille (le tir raté) | **0,22** | — |
> | **agent réel, en AMBIENT** | **2,67** | **×12** |
> | agent réel, fenêtres de 322 s de la séance | **3,10** | **×14** |
> | `veille off` **+ `anim on`**, sans agent | **20,7** | **×94** |
>
> ⇒ **LA RÈGLE CORRIGÉE** : ⛔ **`veille off` NE SUFFIT PAS.** Une fenêtre console qui mesure la
> famine DMA doit porter **un STIMULUS DE DESSIN** — l'agent, ou `anim on` — et **publier son débit
> de cycles de redessin** à côté de son résultat. C'est le débit qui atteste du régime, ⛔ pas l'état
> de la veille.
>
> ✅ **ET CE QUE ÇA CHANGE POUR LA CONCLUSION SUR LE TÉMOIN : RIEN, SINON QU'ELLE TIENT MIEUX.** Le
> re-tir propre de `flash on` avait `veille off` **+ `anim on`**, soit **20,7 cycles/s — SEPT FOIS le
> régime de l'agent réel** — et il rend **0**.

**(2) DEUX COMMANDES REFUSÉES, LUES COMME ACCEPTÉES.** `anim on 10` ⇒ *« refusé :
ESP_ERR_INVALID_ARG — période attendue entre 200 et 10000 ms »* : le stimulus de dessin n'a **jamais**
tourné dans deux fenêtres de 90 s. `flash on` ⇒ *« refusé : ESP_ERR_INVALID_STATE »*, le stimulus
précédent courant encore. **Les deux refus étaient imprimés à l'écran** ; mon harnais ne les lisait
pas. ⇒ **RÈGLE** : un harnais qui pose une commande **échoue bruyamment** sur `refusé` / `ESP_ERR` /
`Unrecognized`, sinon il fabrique des faux négatifs **plausibles**.

**(3) UNE FENÊTRE PERDUE À LA LECTURE.** Le premier `flush` après un `wsl-attach` est parti pendant
que le port bruissait encore : **`ug/JTAG)` + `Unrecognized command`**. Il a échoué **bruyamment** —
⛔ mais rien ne le **gardait** : une sortie **partielle et parsable** aurait publié du faux, en
silence. ⇒ **RÈGLE** : exiger un **marqueur du bloc attendu** avant de retenir une lecture.

#### 🔴 LE TÉMOIN DE RÉFÉRENCE DU DÉPÔT EST DÉSARMÉ SUR CE BINAIRE — RE-TIRÉ **EN RÉGIME DE DESSIN**

Après la correction du protocole (1) ci-dessus, `flash on` a été **re-tiré proprement** : `veille off`
et `anim on` **acceptés** (⛔ pas seulement envoyés), `mode : ACTIF · veille DESARMEE` **relu avant ET
après**, `bounce 9600`, binaire livré. Le stimulus a été **accepté et il a tiré** :

| fenêtre | secteurs écrits | débit soutenu | `manques` | **série** | CORRUPTION | déficit pire |
|---|---|---|---|---|---|---|
| **20 s** | 1 344 (5 505 024 o) | **92 975 o/s** | **0** | **0** | **0** | 120 µs |
| **80 s** | 1 805 (7 393 280 o) | **85 630 o/s** | **0** | **0** | **0** | 121 µs |

⚠️ **Le débit lui-même atteste du régime** : **86-93 ko/s** ici contre **169 898 o/s** dans la fenêtre
au repos — le CPU est bien chargé par l'animation, ⛔ ce n'est pas une carte inactive.

🔴 **CONCLUSION, ET ELLE VAUT AU-DELÀ DE `dn4-12`** : `flash on` + `bounce_px ≠ 0` rendait **1 037
trames SANS enroulement sur 1 041** le **2026-08-22**. Sur le binaire du **2026-08-29**, dans un
régime de dessin, il en rend **ZÉRO**. ⇒ **LE TÉMOIN DE RÉFÉRENCE DE L'INSTRUMENT EST DÉSARMÉ**, et
**aucun document du dépôt ne le disait** — il est encore cité comme *« le TEMOIN de reference : un
compteur qui ne bouge pas sous `flash on` est un compteur mort »*.

⛔ **ET LA CAUSE N'EST PAS PROUVÉE.** L'hypothèse est le **remède XIP** de `dn4-22` (`d244011`) :
`CONFIG_SPIRAM_FETCH_INSTRUCTIONS` + `CONFIG_SPIRAM_RODATA` sortent le code **et** les constantes de
la flash, or le mécanisme du témoin était que *« l'ISR qui réalimente le bounce buffer est MASQUÉE
pendant l'effacement de secteur »* — c'est-à-dire qu'elle allait chercher ses instructions **en
flash**. Cohérent, et confirmé à l'exécution par `mmu_psram: Instructions copied and mapped to
SPIRAM`. ⛔ **Mais une explication n'est pas une preuve** : il faudrait **retirer XIP et voir le
témoin remonter**, ce qui coûte un arm. **Non fait, et déclaré.**

⚠️ **Le même verdict frappe le SECOND témoin du dossier** : `bounce 480`, que §20.7.6 mesure à
`manques = 290 / 4 873`, rend **`manques = 0`** aujourd'hui — en régime de dessin, sur 30 s comme sur
120 s. Ce qu'il produit encore, ce sont des **franchissements de seuil isolés** (le seuil y vaut
39 µs), ⛔ plus de la famine.

#### 📊 LE RÉGIME NOMINAL — CE QUE LA GRANDEUR NEUVE DIT, ET C'EST LA RÉPONSE À LA QUESTION DE LA STORY

**3 fenêtres de ~322 s sous AGENT RÉEL** (témoin positif relevé au début ET à la fin de chacune,
`bounce 9600`, binaire livré) :

| fenêtre | trames | `manques` | **plus longue série** | **nombre de séries** | CORRUPTION | déficit pire |
|---|---|---|---|---|---|---|
| 1/3 | 11 989 | 0 | **0** | **0** | 0 | 121 µs |
| 2/3 | 12 037 | 0 | **0** | **0** | 0 | 122 µs |
| 3/3 | 11 956 | 0 | **0** | **0** | 0 | 121 µs |

⇒ **sur 35 982 trames consécutives sous agent réel, la plus longue série d'un état dégradé vaut
ZÉRO.** ⛔ Ce n'est pas « l'instrument ne voit rien » — il vient de voir, deux fois, une série de 3.
C'est **le régime nominal qui est propre**.

**Et à `bounce 480`, LE TÉMOIN DU DOSSIER, EN RÉGIME DE DESSIN** (veille désarmée + animation) :

| fenêtre | CORRUPTION | seaux 10/25/50 | **plus longue série** | **nombre de séries** | rompues par indéterminée |
|---|---|---|---|---|---|
| 30 s | **2** | 1156 · 3 · 2 | **1 trame** | **2** | **0** |
| 120 s (**rapport 4**) | **8** | 4324 · 16 · 8 | **1 trame** | **8** | **0** |

🎯 **LE NOMBRE DE SÉRIES SUIT EXACTEMENT LA DURÉE (2 → 8 pour ×4), MAIS LA LONGUEUR RESTE 1.**
⇒ **le défaut est STRICTEMENT ISOLÉ : il ne dure jamais.** Et **`rompues par une indéterminée = 0`
sur les deux fenêtres** ⇒ la longueur 1 **n'est pas un artefact de rupture**, elle est réelle. C'est
précisément ce que le compteur de `dn4-10` ne pouvait **ni confirmer ni infirmer**.

⚠️ **UNE NUANCE D'INSTRUMENT, ET ELLE N'ÉTAIT ÉCRITE NULLE PART** : à `bounce 480` le seau 10 % vaut
**4 324 / 4 609 = 94 % de `n`** — ce qui est **le symptôme que la console nomme** pour une référence
pathologique. ⛔ **Ici il n'est PAS diagnostique** : 10 % de `t_demi = 39 µs` valent **3,9 µs**, sous
le bruit de phase, donc le seau se remplit **par construction**. ⇒ **le symptôme « le seau 10 % vaut
presque `n` » ne vaut qu'à GRAND seuil.**

#### 👁️ AC3.4 — LE CONSTAT OWNER, VERBATIM

« Prêt ? » demandé, **OUI attendu** (*« Oui, je regarde »*), ce qu'il fallait guetter annoncé (**la
LIGNE VERTE**, ⛔ pas les restes de chiffres). Fenêtre d'une minute à `bounce 480`, veille désarmée.
Relevé machine **sur la même fenêtre** : **1 corruption**, plus longue série **1 trame ≈ 26 ms**,
déficit pire 40 µs pour un seuil de 39.

> 🔴 **VERBATIM OWNER, 2026-08-29** : *« oui bien stable mini gresillment sur une ligne le long de la
> minute de lh cp et ME de menu mais vraiments tres tres légé »*

**CE QUE ÇA ÉTABLIT** : à `bounce 480`, la config où l'owner disait *« ça a glissé »* le 2026-08-23,
il dit maintenant **« bien stable »**. ⇒ **le glissement n'est PAS revu dans la MÊME configuration**,
et cette fois c'est l'œil qui le dit, pas un compteur.

⚠️ **DEUX RÉSERVES, ⛔ NON RÉCONCILIÉES DE FORCE** :
1. Il décrit un grésillement **« le long de la minute »**, donc **CONTINU**, là où la machine n'a
   compté **qu'UN** événement de 26 ms. ⇒ **l'œil et le compteur ne décrivent pas le même
   phénomène**, et ⛔ on ne les fait pas coïncider.
2. Ce n'est **pas** la ligne verte : c'est localisé sur du **texte** (« lh cp », « ME de menu »),
   signature de l'**artefact d'INVALIDATION** — un défaut **différent**, hors périmètre de `dn4-12`.

#### 💰 AC6.3 — LE COÛT EN MARGE DE FAMINE : ⛔ NON ATTRIBUABLE, ET LE MOTIF EST MON PROTOCOLE

Même protocole, **n = 3 par bras**, agent réel, fenêtres de ~322 s :

| grandeur | **AVANT** `e3064f0` | **APRÈS** `b1a810f` | Δ | étendues |
|---|---|---|---|---|
| **déficit pire** | 117 · 121 · 123 ⇒ **120,3 µs** | 121 · 122 · 121 ⇒ **121,3 µs** | **+1,0 µs** | 6 et 1 |
| **CORRUPTION** | 0 · 0 · 0 | 0 · 0 · 0 | **0** | 0 |
| `manques` | 0 · 0 · 0 | 0 · 0 · 0 | **0** | 0 |
| seau 10 % | 16 · 30 · 33 ⇒ **26,3** | 120 · 149 · 105 ⇒ **124,7** | **+98,4 (×4,7)** | 17 et 44 |

✅ **Sur le déficit pire, le Δ est +1,0 µs pour des étendues de 6 et 1 : NON DISTINGUABLE DE ZÉRO** —
même verdict que les 17 correctifs de `dn4-5`. Et **CORRUPTION reste à 0 sur les six fenêtres.**

⛔ **MAIS LE SEAU 10 % FAIT ×4,7, ET JE NE L'ATTRIBUE PAS À `dn4-12`.** Le Δ dépasse les deux
étendues, donc il est *distinguable de zéro* — ⛔ mais **les deux bras ne sont pas alternés** : ils
sont séparés d'**une heure** et d'une campagne intense (**62 Mo d'écriture flash**, 3 reboots, un
passage à `bounce 480`). **Un A/B qui n'alterne pas ne sépare pas l'effet du binaire de la dérive
temporelle** — c'est exactement pourquoi le protocole du dépôt impose des **bras alternés**, et je
n'ai pas pu alterner **faute d'arms**.

⚠️ **Et un chiffre du dossier borne déjà ce seau** : sur la fenêtre de **4 h 06** relevée en début de
séance sur `e3064f0`, le seau 10 % valait **21 sur 552 563 trames = 0,004 %**, contre **0,22 %** sur
mes fenêtres AVANT de 300 s. ⇒ **le seau 10 % d'une fenêtre courte est dominé par le TRANSITOIRE DE
BOOT**, qui est hautement variable. C'est une raison de plus de ne rien conclure.

🔬 **UN CONTRÔLE DE DÉRIVE A ÉTÉ TIRÉ, ET IL COÛTE ZÉRO ARM** : **3 fenêtres de plus sur le MÊME
binaire `b1a810f`**, ~40 min après le bras APRÈS. Seau 10 % : **103 · 98 · 135**. Déficit pire :
**136 · 120 · 121**. Série : **0 · 0 · 0**. CORRUPTION : **0 · 0 · 0**.

⇒ **SUR SIX FENÊTRES COUVRANT ~55 MINUTES, LE SEAU 10 % DU BINAIRE `b1a810f` RESTE DANS [98, 149]**,
pendant que celui de `e3064f0` tenait dans **[16, 33]**. **Les deux plages ne se recouvrent PAS**, et
la valeur haute **ne dérive pas** : ce n'est donc **pas** un transitoire qui retomberait tout seul.

🟠 **VERDICT, ET IL EST DÉLIBÉRÉMENT INCOMPLET** : c'est un **CANDIDAT DE COÛT RÉEL**, ⛔ **pas un
coût établi**. Ce qui manque est nommé : **les bras n'ont pas été ALTERNÉS** (`AVANT → APRÈS →
AVANT`), faute d'arm. Tant qu'un retour sur `e3064f0` n'a pas fait **retomber** le seau, on ne peut
pas séparer l'effet du binaire d'un changement d'état persistant de la carte survenu entre les deux
bras. **Prouver une cause, c'est LA RETIRER et voir le compteur retomber — ⛔ pas l'expliquer.**

⚠️ **Et le déficit pire, lui, est TRANCHÉ** : `[117, 123]` avant contre `[120, 136]` après, sur 3 et
6 fenêtres. **Les plages se recouvrent largement** ⇒ **Δ NON DISTINGUABLE DE ZÉRO**. Idem pour
**CORRUPTION**, qui vaut **0 sur les NEUF fenêtres**, et pour `manques`, à 0 partout.


#### 🔴 CLÔTURE DU 2026-08-29 — LE ×4,7 D'AC6.3 EST **RÉFUTÉ**, ET C'EST UNE MESURE QUI LE FAIT

> **DÉCISION OWNER DU 2026-08-29** : *« ok on boucle, le soak de 7 jours couvrira mieux »*.
> **AC4 se ferme AVEC ÉCART DÉCLARÉ** — ⛔ pas coché.

Avant de boucler, une dernière fenêtre a été relevée sur le binaire livré `b1a810f`, **carte reposée**
(la tour avait redémarré à 13:42, aucune campagne depuis) :

| grandeur | valeur |
|---|---|
| durée (T0 mural **confronté**) | **725 091 ms = 12 min 05 s** ⇒ ⛔ **aucune coupure** |
| trames | **27 036** · `manques` **0** · `doubles` **0** |
| **plus longue série** | **0** · 0 série · **0 rompue par une indéterminée** |
| CORRUPTION | **0** · déficit pire **120 µs** (seuil 775) |
| `ph_ref` / `ph_max` | 2259 / 2269 µs — sain |
| cycles de redessin | 1 919 / 725 s = **2,65 /s** (régime AMBIENT sous agent, cf. 2,67 la veille) |

🔴 **ET C'EST LE SEAU 10 % QUI TRANCHE AC6.3.** Ramené au même dénominateur, **pour 10 000 trames** :

| bras | taux /10 000 |
|---|---|
| **AVANT** `e3064f0` (hier, 3 fenêtres de ~322 s) | **13,4 · 25,2 · 27,7** |
| **APRÈS** `b1a810f` (hier, 6 fenêtres de ~322 s) | **100 · 124 · 88 · 86 · 82 · 113** |
| **APRÈS** `b1a810f` (**aujourd'hui, carte reposée, 12 min**) | **8,1** |
| pour mémoire, `e3064f0` sur **4 h 06** | **0,38** |

⇒ 🎯 **LE MÊME BINAIRE QUI DONNAIT 82-124 HIER SOIR EN DONNE 8,1 AUJOURD'HUI — c'est-à-dire SOUS la
plage du bras AVANT.** ⛔ **L'attribution du ×4,7 au binaire est donc RÉFUTÉE** : l'écart d'hier
était dominé par **l'état de la carte** (62 Mo d'écriture flash, 3 reboots, un passage à
`bounce 480`) et par **la durée de la fenêtre**, ⛔ pas par le code de `dn4-12`.

⚠️ **CE QUE ÇA VAUT, ET CE QUE ÇA NE VAUT PAS.** C'est **UNE** fenêtre, et le dépôt interdit de
conclure d'un échantillon unique. ⛔ **Mais elle ne SERT PAS à établir un coût : elle DÉTRUIT une
attribution.** Un point qui réfute une hypothèse de coût ne demande pas la même force qu'un point
qui l'établirait — et l'écart est d'un **facteur 10 à 15**, dans le sens qui innocente le code.

✅ **CE QUI RESTE ACQUIS D'AC6.3, ET QUI NE BOUGE PAS** : le **déficit pire** est non distinguable
de zéro ([117, 123] contre [120, 136]), **CORRUPTION vaut 0 sur les DIX fenêtres** de la campagne, et
`manques` vaut 0 partout. ⇒ **aucun coût de marge de famine n'est démontré**, et celui qui était
soupçonné ne se reproduit pas.

⛔ **CE QUI RESTE OUVERT, ET QUI PART AU SOAK** : le seau 10 % dépend **fortement de la DURÉE de la
fenêtre ET de l'ÉTAT de la carte**, dans des proportions **non séparées** (0,38 sur 4 h 06 · 8,1 sur
12 min · 13-28 et 82-124 sur 5 min). ⇒ il **ne peut pas** servir à attribuer un coût depuis des
fenêtres courtes et non alternées. **Le soak 7 jours d'AC3 de `dn4-5` tournera sur ce binaire et
donnera le chiffre long, avec le transitoire de boot dilué.** C'est là que la question se referme.

#### 🎁 UN RÉSULTAT HORS PROGRAMME — LE CORRECTIF `dn4-5`/AC1.2 EST VU CRIER SUR LA CARTE

La toute première lecture de la séance, sur `e3064f0` après ~4 h d'agent réel, a rendu :

```
─── glissement de trame (dn4-10) — fenêtre 14805101 ms ───
⚠️ FENÊTRE AU-DELÀ DE 71,58 min (2^32 µs) — l'instrument
   d'AVANT dn4-5 aurait publié 1920200 ms ici, soit 12884901 ms de MOINS que la réalité.
```

⇒ **4 h 06 mesurées, et l'instrument d'avant `dn4-5` en aurait publié 32 min** — trois enroulements
de 2³² µs perdus. Le correctif d'AC1.2 de `dn4-5` **n'est plus seulement prouvé en logique par sa
gate : il a crié sur le silicium**, et c'est la première fois.


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

---

## 22. 🎯 `dn4-4` (P9.4) — LA BASELINE `=n`, ET LA BANDE TACTILE DE LA JAUGE `RAM` TRANCHÉE

**Séance du 2026-08-24.** Firmware **`d379c0d`** pour la baseline, **`49be42b`** pour la mesure de
bande — **SHA lus au bandeau**, `git status --porcelain` vérifié **vide avant chaque flash**.

### 22.1 🔴 T0 — LA MESURE QUE `dn4-10` AVAIT ACTÉE COMME SAUTÉE

`dn4-10` a livré `CONFIG_LCD_RGB_RESTART_IN_VSYNC=n` + `DN_DEFAULT_BOUNCE_PX = 9 600` **sans jamais
tirer `nav ab` sous ce régime** — sa décision (c) l'acte explicitement. **C'est fait.**

`cfg` : `num_fbs=1 bounce_px=9600 draw_lines=128 draw_psram=0 lvgl_core=0`.
`fps 15` : **37,40 Hz** mesuré = théorique (**+0,00 %**). Poussée **GROUPÉE**.

| Commande | n | min | **moy** | max | Δ tas LVGL | Δ RAM | Δ PSRAM |
|---|---|---|---|---|---|---|---|
| **`nav ab 20`** — le protocole des 3 points publiés | 40 | 287,3 ms | **335,6 ms** | 400,8 ms | −28 o | 0 | 0 |
| `nav ab 40` — contre-vérification | 80 | 280,9 ms | **336,5 ms** | 400,9 ms | −28 o | 0 | 0 |

**Les deux concordent à 0,8 ms (0,25 %).** `flush/cyc` = **4,84**, stable sur les **trois** fenêtres
(Δ150 flush / Δ31 cycles à chaque fois) — cohérent avec les **5 bandes** de 128 lignes (640 ÷ 128).
Tas LVGL : 20 692 / 62 040 o (34 %), plus gros bloc libre 40 476 o, **fragmentation 3 %**.

🔴 **CE QUE CE CHIFFRE DIT DU CRITÈRE N°3 DU BRIEF** : la page de détail **SANS AUCUNE COURBE** coûte
déjà **335,6 ms**, soit **+35,6 ms au-dessus du budget de 300 ms**. Le critère est en défaut **avant**
que `dn4-4` ajoute quoi que ce soit.

⚠️ **⛔ NE PAS LIRE CE TABLEAU COMME UN A/B AVEC LES TROIS POINTS PUBLIÉS** (307,0 / 321,8 / 349,1 ms).
**DEUX variables ont bougé, pas une** : le régime d'affichage (`=y`/7 680 → `=n`/9 600) **et** le
contenu de la page (`dn4-6`, `dn4-8` et `dn4-9` ont tous ajouté du contenu au détail depuis).
Aucune attribution n'est tirable de la comparaison.

### 22.2 ⚠️ UN DÉFAUT DE PROTOCOLE PUBLIÉ : `nav ab 40` NE REND PAS `n = 40`

`nav ab <n>` fait **`n` allers-retours** et chronomètre **les deux sens** ⇒ `n = 2 x` la valeur
passée. Le protocole des trois points publiés (tous à `n = 40`) est donc **`nav ab 20`**, et **le
firmware l'imprime lui-même** dans l'aide de `nav model` : *« comparer proprement : `touch reset`
puis `nav ab 20` »*. ⇒ Les deux ont été tirés ici, et ils concordent.

### 22.3 🎯 LA BANDE TACTILE DE LA JAUGE `RAM` — TRANCHÉE PAR LECTURE, PUIS PAR L'OBJET

**Le désaccord, tel qu'il était publié :**

| Source | `x` | `y` | Nature |
|---|---|---|---|
| `dn4-1` | — | `340..350` | calculé, **déjà déclaré périmé** (`CASE_H` 156 → 163) |
| `dn4-2` | `22..223` | `337..347` | **calculé** |
| Visée du 2026-08-20, cible visible (`widget piste 0xFF2020`), **9 taps** | `38..196` ✅ | 🔴 **`350..371`** | **mesuré au doigt** |

⚠️ **NI L'UNE NI L'AUTRE N'AVAIT ÉTÉ RELUE DE L'OBJET LVGL.** D'où l'instrument
**`widget jauge [<case>]`** (`dn_ui_widget_jauge_rect()`), qui demande à LVGL **où il a vraiment posé
la barre**, en coordonnées écran — exactement comme `widget detail` relit le texte du label.

**Le tracé RÉEL, relu :**

```
JAUGE de la case 2 (RAM) — RELUE des coordonnees LVGL :
  rectangle : x = 23..223  (201 px)
              y = 338..347  (10 px)
     case  : x = 10  y = 243  (225x163)     ecart : dx = 13 px   dy = 95 px
```

#### a. L'écart formule ↔ tracé est de **1 px**, et il est EXPLIQUÉ

La formule donne `x = 10 + W_PAD(12) = 22` et `y = 243 + y_bas(88) + 6 = 337`. Le tracé rend **23** et
**338**. Le pixel vient de `lv_obj_set_style_border_width(o, 1, 0)` sur la **racine de case**
(`dn_widget.c`) : LVGL positionne les enfants dans la **zone de contenu**, à 1 px à l'intérieur du
bord. ⇒ **La formule de `dn4-2` était juste**, à ce pixel près.

#### b. 🔴 LES 13-24 px NE SONT DONC NI UNE FORMULE FAUSSE NI UNE PISTE DESSINÉE AILLEURS

**Ils viennent de ce que la bande DÉPEND D'UNE GÉOMÉTRIE COMMUTABLE À CHAUD.** Démontré en deux
commandes, sur la même carte, dans la même minute :

| `val_y` | rectangle relu de LVGL | les 9 taps du 2026-08-20 |
|---|---|---|
| **48** (défaut) | `y = 338..347` | ⛔ aucun |
| 🔴 **66** | 🔴 **`y = 356..365`** | 🎯 **`350..371` — la bande tombe EN PLEIN DEDANS** |

`widget val <y> <pas>` est un instrument de `dn4-6`, **commutable à chaud** et **RAM-only** (il ne
survit pas au reboot, `cfg` ne le porte pas). ⚠️ Effet de bord observé au passage : à `val_y = 66`,
`CPU` et `GPU` **débordent** et LVGL les clippe — **la garde de `dn_widget.c` a crié**, comme prévu.

⇒ ✅ **LA LECTURE RETENUE : LA FORMULE.** La coordonnée publiée par `dn4-2` était **la photographie
d'UNE géométrie**, publiée comme un invariant. ⛔ **La correction n'est pas un patch de coordonnée —
c'est de supprimer la récitation.** L'origine des cases n'a désormais qu'**une seule fabrique**
(`ui_case_origine()`), prise par la boucle de construction **et** par l'instrument, et
`widget jauge` rend la bande **re-lisible à tout instant**.

#### c. ⛔ CE QUE §22.3 NE PROUVE PAS

Que `val_y` valait **66 ce jour-là**. L'override est RAM-only et la séance du 2026-08-20 ne l'a pas
capturé. Ce qui est prouvé, c'est que **le mécanisme suffit**, au pixel près, à produire l'écart
observé — et qu'**aucune coordonnée tactile ne doit plus être publiée comme une constante**.

✅ **Ce qui n'est PAS en cause et ne se re-teste pas** : *« toute la case est la zone tactile »* tient
sur la géométrie **D12** — les 9 visées sont bien devenues **9 taps**.

### 22.4 🎯 AC7 — LA LATENCE **AVEC LA COURBE**, ET « L'OPTION N°2 » ENFIN CHIFFRÉE

> 🔴 **SECTION MARQUÉE LE 2026-08-24 PAR LA REVUE DE CODE — LIRE AVANT D'EN CITER UN CHIFFRE.**
> Le carré 2×2 ci-dessous décrit l'**ÉTAT T1** du firmware (page **pas encore finale**), et
> **deux de ses quatre coins n'ont AUCUNE capture** dans `mesures/dn4-4/` (`240,5` et `176,3`).
> `brief.md:178-179` publie **un autre carré** pour les deux mêmes cellules (`337,6` et `271,8`,
> tirés de `t1bis`/`t2bis`, page finale) — d'où un **coût de la courbe publié avec DEUX SIGNES
> OPPOSÉS** : `−1,9 ms` ici, `+2,0 ms` au brief.
> 🎯 **DÉCISION OWNER DU 2026-08-24** : cette section **reste** comme relevé de l'état T1 ; **le
> carré du brief est RE-TIRÉ ENTIÈREMENT sur le firmware livré** (4 coins, 4 logs, un seul état),
> avec un `widget fond off` corrigé (il posait l'écran de panne « ASSET ABSENT » au lieu d'un noir).
> ⇒ **Porté par `dn4-13`.** ⛔ Jusque-là, ne pas citer ces chiffres comme ceux du produit.


Firmware **`d71dc1b`** puis descendants, SHA **lus au bandeau**, `porcelain` vide avant chaque flash.
Protocole identique à T0 : **`touch reset` puis `nav ab 20`** (**n = 40**), dalle **non touchée**,
`taps` pendant la série = **0**, `transitions RÉELLES = 40 (demandées 40)` à chaque tir.

#### a. Le prix de la courbe, seul

| Point | n | min | **moy** | max | tas LVGL | frag. |
|---|---|---|---|---|---|---|
| **T0** — page **sans** courbe | 40 | 287,3 | **335,6 ms** | 400,8 | 20 692 o | **3 %** |
| **T1** — page **avec** sa courbe | 40 | 160,3 | **333,7 ms** | 420,2 | 21 320 o | 🔴 **42 %** |

⇒ **Δ = −1,9 ms (0,6 %)** pour une étendue **intra-série de 260 ms**.
🎯 **LE COÛT DE LA COURBE N'EST PAS MESURABLE PAR CET INSTRUMENT À `n = 40`.** ⛔ Ce n'est **pas**
« la courbe est gratuite » : c'est « elle est sous le bruit de la mesure ».

⚠️ **CE QUE LA COURBE COÛTE VRAIMENT SE VOIT AILLEURS** : **+628 o** de tas LVGL, et surtout la
**fragmentation du pool passe de 3 % à 42 %** (plus gros bloc libre : 40 476 → 23 336 o). C'était la
partie **NON PRÉDITE** d'AC5.6 — et elle est le vrai prix, ⛔ pas les millisecondes.

#### b. 🔴 LE CARRÉ 2×2 — ET « L'OPTION N°2 » N'EST PAS CE QUE LE LEDGER CROYAIT

« L'option n°2 » (*ne pas invalider le fond à la transition*) traînait **NON ESSAYÉE** depuis
`dn3-2`. Elle vise le fait qu'en modèle `SCREENS`, `fond_poser()` pose une `lv_image` de
480 × 640 RGB565 (**614 400 o**) sur **chacun** des deux écrans, et que `lv_screen_load()` invalide
tout — **alors que le fond est identique d'un écran à l'autre**.

⛔ **ON NE L'A PAS ESSAYÉE À L'AVEUGLE : ON A D'ABORD MESURÉ SA BORNE HAUTE.** `widget fond off`
retire le fond ⇒ c'est le **meilleur cas** que l'option pourrait atteindre. Puis, les panneaux étant
**semi-transparents** (`opa 178`, `voile 90`), on a séparé la deuxième cause. **Quatre coins, une
seule variable à la fois** :

| | `opa 178 / voile 90` — **LE PRODUIT** | `opa 255 / voile 0` — opaque |
|---|---|---|
| **fond POSÉ** | 🔴 **333,7 ms** (160,3 / 420,2) | **240,5 ms** (186,8 / 310,9) |
| **fond RETIRÉ** | **194,2 ms** (138,3 / 245,2) | **176,3 ms** (132,8 / 216,7) |

| Effet isolé | Valeur |
|---|---|
| le **fond**, à opacité produit | **−139,5 ms** (−41,8 %) |
| le **fond**, à panneaux opaques | −64,2 ms |
| l'**alpha**, fond posé | **−93,2 ms** (−27,9 %) |
| l'**alpha**, fond retiré | −17,9 ms |
| **les deux ensemble** | **−157,4 ms (−47,2 %)** |

🔴 **IL Y A UNE FORTE INTERACTION, ET ELLE CHANGE LA CONCLUSION DU LEDGER.**
`139,5 + 93,2 = 232,7`, mais les deux ensemble ne rendent que **157,4** : l'interaction vaut
**−75,3 ms**. L'alpha ne coûte cher **que parce qu'il y a un fond à mélanger**, et le fond ne coûte
cher **que parce qu'il faut le mélanger**.

⇒ 🔴 **« NE PAS INVALIDER LE FOND » NE PEUT PAS S'OBTENIR PAR UN PARTAGE D'OBJET** (couche
partagée, conteneurs masqués, `lv_layer_bottom()`…) **TANT QUE LES PANNEAUX SONT SEMI-TRANSPARENTS** :
quel que soit le propriétaire de l'image, **le fond doit être relu SOUS chaque panneau** à chaque
recomposition. ⛔ **Ce ne sont pas deux leviers indépendants : c'est UN SEUL MÉCANISME**, et le
ledger le décrivait comme un problème de propriété d'objet.

#### b bis. AC7.6 — `flush/cyc` PAR POINT, ET POURQUOI LE CRITÈRE RESTE INÉVALUABLE

⚠️ **Écrit le 2026-08-24 par la revue de code.** La story déclarait *« `flush/cyc` relevé à T0
(4,84) mais PAS re-relevé par point — écart déclaré »*. **Il EST re-relevable**, depuis les
compteurs bruts des logs livrés — les voici, recalculés :

| Point | Δ flush | Δ cycles | **`flush/cyc`** | log |
|---|---|---|---|---|
| **T0** — sans courbe | 1 004 − 854 = **150** | 225 − 194 = **31** | **4,84** | `t0-navab20-2026-08-24.log` |
| **T1** — avec la courbe | 625 − 473 = **152** | 260 − 229 = **31** | **4,90** | `t1-avec-courbe-navab20.log` |
| **T1bis** — page finale | 963 − 815 = **148** | 326 − 295 = **31** | **4,77** | `t1bis-page-finale-navab20.log` |

**Δ cycles vaut 31 sur les trois fenêtres** — les trois sont donc comparables en durée.
Cohérent avec les **5 bandes** de 128 lignes (640 ÷ 128) : `flush/cyc` tourne autour de 4,8.

🔴 **MAIS LE CRITÈRE D'AC7.6 RESTE INÉVALUABLE, ET C'EST UN ÉCART PLUS HONNÊTE QUE CELUI QUI ÉTAIT
DÉCLARÉ.** L'AC demande `flush/cyc` *« stable à **±0,04 entre deux passes du MÊME cas** »*. Or
T0, T1 et T1bis sont **trois cas DIFFÉRENTS** : leur écart (étendue **0,13**) est le **signal**,
⛔ pas le bruit. **Aucun cas n'a été tiré deux fois** ⇒ la tolérance ne peut être ni vérifiée ni
démentie. ⚠️ **Ce n'est donc pas « le chiffre manque » mais « le chiffre existe et son critère de
stabilité n'a pas d'instrument »** — il faudrait une passe répétée du même cas.
⇒ Écart **réduit, ⛔ pas supprimé**. La passe répétée est portée par `dn4-13`.

#### c. ⛔ CE QUE §22.4 NE PROUVE PAS

- Que **139,5 ms sont récupérables**. C'est une **borne haute**, obtenue en retirant le fond —
  ⛔ pas en le partageant. Le gain d'une implémentation réelle est **entre 0 et 139,5 ms**, et il
  n'a **pas** été mesuré parce que le carré 2×2 montre qu'il n'y a **pas** d'implémentation qui
  garde l'alpha ET évite la recomposition.
- Que la courbe est gratuite. Elle est **sous le bruit** en millisecondes, et **chère en
  fragmentation** (3 % → 42 %).
- ⚠️ `widget fond off` et `widget opa 255 / voile 0` **ne sont pas des états de production** :
  la maquette normative porte le Living PCB **derrière des panneaux translucides**. Les faire passer
  en opaque est **une décision OWNER d'esthétique**, ⛔ pas un arbitrage d'agent.

### 22.5 AC5 — LE COÛT DE L'HISTORIQUE, PRÉDIT PUIS MESURÉ

| | valeur |
|---|---|
| RAM interne libre — **T0**, avant | **81 171 o** |
| RAM interne libre — après | **77 659 o** |
| **Δ MESURÉ** | **−3 512 o** |
| **PRÉDICTION écrite AVANT le code** (`dn_hist.h`) | **−3 400 à −3 500 o** |
| **ÉCART** | 🔴 **−12 o hors de la borne haute (0,34 %)** |

⇒ **La prédiction était légèrement OPTIMISTE, et c'est écrit tel quel.** Les 3 360 o de points +
120 o de `s_dx[]` + les index de l'anneau + les pointeurs de la courbe. ⛔ On ne réécrit pas la
prédiction pour qu'elle tombe juste.

**Δ tas LVGL : +628 o**, et il était **explicitement NON PRÉDIT** (c'est le coût des objets
`lv_chart`) — cf. la leçon **L18** : *une prédiction qu'on ne peut pas confronter ne coûte rien à
celui qui l'écrit.* Ce qui **n'avait pas été anticipé du tout**, c'est la **fragmentation** : 3 % → 42 %.

**L'historique ne ment pas, et ça se lit** (`hist`, aucune source PC branchée) :

```
   CPU / GPU / RAM / RESEAU / DISQUE :  0 reels · 120 TROUS  (aucune source)
   AMBIANCE T                        :  6 reels · 114 trous  ·  300 .. 300 (dixiemes)
   AMBIANCE RH                       :  6 reels · 114 trous  ·  326 .. 327
```

⇒ **Le trou n'est pas un zéro**, et les cinq séries PC le disent au lieu de dessiner une chute à zéro.

### 22.6 🎯 AC4.3 — LA GARDE DE HAUTEUR CRIE, ET DEUX DÉFAUTS D'INSTRUMENT ONT FAILLI FAIRE CONCLURE L'INVERSE

⚠️ **LA PRÉMISSE D'AC4.3 ÉTAIT FAUSSE.** La story écrit : *« la garde ne tourne qu'à la construction,
quand `geom_resolue` est faux — donc jamais »*. **Mesuré : `geom_resolue == true` sur le chemin de
mise à jour.** La garde **s'exécute**. Ce qui restait vrai, c'est qu'**aucun témoin ne l'avait
jamais fait crier** — et qu'aucun n'était atteignable, le pire cas livré tenant **exactement**
(`14 + 140 = 154 ≤ 154`, marge ZÉRO).

`widget detpan <h>` rétrécit le panneau à chaud. **Témoin positif ET négatif, même pire cas `DISQUE`** :

| panneau | passages | **cris** | `geom_resolue` | verdict |
|---|---|---|---|---|
| **154 px** (le produit) | 12 | **0** | **true** | ✅ silence **légitime** |
| **153 px** (témoin négatif) | 21 | **8** | **true** | 🔴 **elle CRIE** |

Sur le fil, texte complet :
```
W dn_ui: detail « DISQUE » : le bloc de valeurs DEBORDE EN HAUTEUR — label 140 px
pose a y = 14 dans un panneau de 153 px : il manque 1 px. LVGL clippe la derniere
ligne SANS un mot.
```

#### 🔴 DEUX DÉFAUTS D'INSTRUMENT — LES MIENS — ET ILS SONT DE LA MÊME FAMILLE

1. **Mon premier tir ouvrait le détail APRÈS la fin de l'injection.** La garde n'a alors que
   **2 passages** (construction + transition), tous deux à `geom_resolue = false`, `panneau 0`,
   `label 0` à `y = -1`. J'aurais conclu *« la garde se coupe elle-même »*. C'est le **piège n°3 du
   dépôt à la lettre** — *une vue qui périme en 3 s exige une injection CONTINUE* — **repayé**.
2. 🔴 **`dn_console.envoyer()` fait un `reset_input_buffer()` AVANT CHAQUE COMMANDE** : tout
   `ESP_LOG` émis **entre** deux commandes est **DÉTRUIT**. Le compteur interne disait **8 cris**
   pendant que ma capture rendait **0 message** — la figure exacte du *« compteur décoratif »*,
   **mais à l'envers** : le compteur était honnête et c'était **le harnais** qui était aveugle.
   ⇒ La parade (**drainer** le flux au lieu de dormir) est désormais **écrite dans
   `tools/dn_console.py`**, avec son motif. ⛔ Le `reset_input_buffer()` n'est **pas** retiré : il
   garantit que la sortie rendue appartient bien à **la** commande envoyée.

✅ **Ce qui rend le diagnostic possible** : la garde est **auditable** (`dn_ui_garde_hauteur()`,
imprimée par `widget courbe`). Une garde qui se tait peut se taire pour **trois** raisons — pas
atteinte, `geom_resolue` faux, condition fausse — et sans compteurs **on les confond**.

### 22.7 AC4 — LA PLACE DE LA COURBE, RELUE (⛔ pas calculée)

```
COURBE du detail — RELUE des coordonnees LVGL :
  courbe : x = 23..458 (436 px)   y = 271..362 (92 px)
  cadre  : 460 x 108 px
  bas du cadre de courbe : 262 + 108 = 370   ✅ INCHANGE (370)
  ecart au panneau du bas (385) : 15 px
```

✅ **L'INVARIANT DU TEMPLATE TIENT — `dn4-4` NE L'A PAS RÉÉCRIT.** Le bas du cadre reste à **370**,
le panneau du bas à **385**, et le template garde ses **QUATRE panneaux** (addendum §1).
⚠️ Et il n'est plus vérifié par un **commentaire qui demande de le vérifier** : `widget courbe` le
**contrôle** et le **DIT** s'il change.
⛔ **La police n'a pas été réduite et aucun texte n'a été rogné** : la courbe tient dans les
**108 px** que `dn4-9` lui avait facturés, ⛔ pas 165.

### 22.8 🔴 AC8 — LE CONSTAT OWNER À L'ŒIL, ET IL A TROUVÉ CE QU'AUCUN CHIFFRE NE VOYAIT

**Séance du 2026-08-24.** Fenêtre **préparée AVANT de demander les yeux**, injection **CONTINUE**
à 1 Hz sur les cinq métriques PC (`tools/anim_courbe_dn44.py`), six pages défilant **22 s chacune**.
⚠️ **`dn_injecteur.py` NE POUVAIT PAS SERVIR** : ses jeux portent des valeurs **FIXES**, la courbe
aurait été une **ligne droite** — indiscernable d'une courbe qui ne se met pas à jour.

**Validité de la fenêtre, prouvée par l'historique** (⛔ pas supposée) : 104-105 points **réels** sur
120 pour CPU/RAM/RÉSEAU/DISQUE, **120/120 sans un trou** pour `AMBIANCE`. ⚠️ `GPU` n'en a eu que
**80** — la perte de lignes du REPL série sous injection soutenue (§21.4), ⛔ pas un défaut du
firmware : l'historique a correctement creusé des **trous** au lieu d'inventer des valeurs.

#### a. 1ʳᵉ passe — les verbatims

| Question | Verbatim owner |
|---|---|
| la courbe bouge-t-elle ? | *« oui »* |
| `AMBIANCE` porte-t-elle deux courbes ? | 🔴 *« de la même couleur ? sinon non »* |
| lisible dans 92 px ? | ✅ *« lisibile »* |
| apparition par morceau ? | 🔴 *« oui au changement de page les petit morceau deja reecris transité sur la page suivant qui elle changé d'echelle et continuer d'ecrir la courbe du coup on a eu des point tillé a la fin »* |
| demande | *« aussi les courbes comence a secrire en ouvrant le detail ou pourrais syystematiquement avoir le min max sur 24h + quelques minutes de graphe ? »* |

#### b. 🔴 CE QUE L'ŒIL A TROUVÉ, ET QUE `nav ab` NE POUVAIT PAS VOIR

**`widget courbe` a rendu `series : 1` sur `AMBIANCE`.** ⇒ **Il n'y avait qu'UNE courbe.** L'owner
n'en a pas vu deux **parce qu'il n'y en avait qu'une**.

**La cause, lue dans `nav_appliquer`** : en modèle `SCREENS` — **le modèle livré** — `build_detail()`
n'est appelée **QU'UNE FOIS**, à la construction de la scène ; toute transition suivante ne fait que
`detail_reparametrer()` + `lv_screen_load()`. Les séries, créées **dans** `build_detail`, restaient
donc **figées sur la première page construite**. Deux conséquences :

1. `AMBIANCE` n'avait **qu'une** courbe dès que la scène naissait ailleurs ;
2. 🔴 **la courbe portait la couleur de la MAUVAISE métrique sur cinq pages sur six.**

🔴 **ET L'INSTRUMENT MENTAIT, DE LA FAMILLE EXACTE QUE CE DÉPÔT TRAQUE** :
`dn_ui_detail_courbe_axes()` **calculait** la couleur depuis `k_desc[s_metrique].couleur` — **la
demande** — au lieu de la **lire** de la série. Il annonçait « orange » sur une ligne **violette**.
⇒ Corrigé : il lit `lv_chart_get_series_color()`.

🎯 **`nav ab` rendait 333,7 ms VERTS sur une page dont la courbe était de la mauvaise couleur et
dont la seconde série n'existait pas. LE CHIFFRE NE VOYAIT RIEN. AC8 vient de payer son existence.**

#### c. Le pointillé au changement de page — ⛔ pas créé par la courbe, RÉVÉLÉ par elle

Le verbatim décrit **l'apparition par bandes déjà mesurée en `dn1-4`** : 5 flushes de 61 440 px
(480 × 128), `640 ÷ 128 = 5` bandes, *chacune attendant sa trame ; vsync synchronise chaque bande,
**rien** ne synchronise le cycle*. La courbe ne la crée pas — **une ligne fine dont l'échelle change
d'une page à l'autre laisse des fragments qui ne se raccordent pas**, et le résultat se lit comme un
pointillé. ⇒ **Le régime d'affichage appartient à `dn4-10`** : déclaré, ⛔ pas maquillé.

#### d. 2ᵉ passe, après correctif — les verbatims

| Question | Verbatim owner |
|---|---|
| `AMBIANCE` a-t-elle deux courbes ? | ✅ *« oui ambiance a bien 2 courbe orange et bleu »* |
| les couleurs changent-elles d'une page à l'autre ? | 🔴 *« non meme couleur pour chaques ecrans.. »* |

**Relevé sur les six pages, couleur RELUE de la série** : violet · cyan · violet · cyan · cyan ·
orange ⇒ **TROIS couleurs pour SIX pages**, le cyan sur **trois** d'entre elles.
✅ **Et ce n'était PAS un défaut de `dn4-4`** : le code le disait lui-même, *« cyan — famille
"données PC" »*. Une couleur de **FAMILLE**, posée en `dn3-1`, défendable tant que rien ne la portait
sur toute la largeur d'un écran. **La courbe l'a rendue voyante.**

⇒ 🔴 **DÉCISION OWNER DU 2026-08-24, ÉCART DE PÉRIMÈTRE ASSUMÉ** : la story écrit
`⛔ Ne change aucun k_desc[]` ; l'owner l'a **levé explicitement, après avoir été averti** que cela
demandait un correct-course. **Six couleurs distinctes**, relues sur la carte :

| Page | avant | après |
|---|---|---|
| CPU | violet `0x9B6CFF` | inchangé |
| GPU | cyan `0x35D6E8` | inchangé |
| **RAM** | violet (= CPU) | **vert `0x4ADE80`** |
| **RÉSEAU** | cyan (= GPU/DISQUE) | **bleu `0x60A5FA`** |
| **DISQUE** | cyan | **rose `0xF472B6`** ✅ solde le *« PROVISOIRE, hérité de VENTILOS (legs dn3-3) »* |
| AMBIANCE | orange `0xFF9640` | inchangé **+** cyan pour l'humidité |

⚠️ **Ce champ pilote TROIS choses et elles changent toutes les trois** : l'icône de la case,
l'indicateur de jauge (`RAM` seule) et la courbe. C'est **voulu** — une métrique, une couleur,
partout. **Le dashboard change donc aussi.**

🔴 **PROXIMITÉ NOMMÉE, ⛔ PAS CORRIGÉE EN SILENCE** : `AMBIANCE` reste `0xff9640` et l'ambre du
régime **SIMULÉE** vaut `0xffb020` — 26 points de vert, 32 de bleu d'écart. Une courbe **RÉELLE** en
orange peut se lire « simulée ». ✅ Ce qui limite le risque : le régime est porté par la couleur du
**TEXTE de valeur** et par le **badge**, ⛔ pas par la courbe. Laissé tel quel **parce que l'identité
orange d'`AMBIANCE` date de `dn3-1`** : ⛔ on ne la change pas au jugé, **l'œil owner arbitre**.

### 22.9 DEMANDE OWNER — LE `MIN/MAX` SUR 24 h, ET SA LIMITE DITE À L'ÉCRAN

Verbatim : *« pourrait-on systématiquement avoir le min max sur 24 h + quelques minutes de
graphe ? »* ⇒ **Extension de périmètre**, acceptée par décision owner.

**24 seaux d'une heure, en anneau** — ⛔ **pas** un min/max « depuis le boot » : un pic survenu il y
a trois jours serait encore affiché comme le maximum d'une page qui prétend parler des 24 dernières
heures. Le seau qu'on ré-atteint est **vidé**, donc la fenêtre **glisse**. Coût : ~~**7 × 24 × 2 × 4 =
1 344 o**~~ **1 728 o** en `.bss` interne.

> 🔴 **CHIFFRE CORRIGÉ LE 2026-08-24 (revue de code) — ⛔ PAS EFFACÉ. Il portait DEUX fautes
> cumulées**, et c'est la troisième valeur publiée pour la même grandeur :
>
> | Publication | Formule | Valeur |
> |---|---|---|
> | ~~ici, §22.9~~ | `7 × 24 × 2 × 4` | ~~1 344 o~~ |
> | ~~`dn_hist.h`~~ | `8 × 24 × 2 × 4` | ~~1 536 o~~ |
> | ✅ **le code** (`dn_hist.c:29-31`) | `8×24×4 + 8×24×4 + 8×24×1` | **1 728 o** |
>
> ① **7 séries au lieu de 8** — `08d4d2b` a ajouté `DN_HIST_S_NET_UP` après cette section.
> ② **`s_svu[8][24]` (192 o) n'était compté nulle part** : c'est le drapeau *« ce seau a vu du
> réel »*, sans lequel un seau vide serait indiscernable d'un seau à zéro. La formule « × 2 »
> ne compte que `s_smin` et `s_smax`.
>
> ⚠️ **Et ce n'est pas le seul chiffre de l'historique qui a vieilli** : le coût total du module
> vaut **~5 609 o** (3 840 points + 1 728 seaux + 32 `s_w` + 9), là où §22.5 publie un Δ mesuré de
> **−3 512 o** — relevé sur un firmware à **7 séries SANS seaux** (commit `8cf16a9`, antérieur à
> `ffff6d2` et `08d4d2b`). **AC5.6 est à re-tirer sur le firmware livré** ⇒ `dn4-13`.

🔴 **LA LIMITE EST DITE À L'ÉCRAN, ⛔ PAS SEULEMENT DANS LE CODE.** D4 interdit toute écriture
flash/NVS en régime ⇒ **ceci ne survit pas à un reboot**. « 24 h » n'est vrai QUE si la carte a
tourné 24 h. La page affiche donc **`MIN/MAX sur : <fenêtre RÉELLE>`**. Relevé sur la carte :

```
fenetre LONGUE : 24 seau(x) d'1 h, couverture REELLE 168 s (2 min)
```

⇒ **Elle affiche « 2 min », ⛔ pas « 24 h ».** Écrire la fenêtre nominale au lieu de la fenêtre
observée serait exactement le mensonge d'interface que `dn2-2` a chassé du dashboard.

⚠️ **Et elle vit dans le bloc d'état (police 14), ⛔ pas collée au `MIN/MAX`** :
`« MIN 100,0 % · MAX 100,0 % (24 h) »` mesure **~496 px pour 432 utiles** en `dn_font_28` — elle
**déborderait**, et la story interdit de réduire la police.

### 22.10 🎯 AC8 — LE CONSTAT AU **DOIGT**, ET C'EST L'OWNER QUI A CORRIGÉ LE PROTOCOLE

⚠️ **LE PROTOCOLE DES QUATRE PREMIÈRES PASSES ÉTAIT FAUX, ET C'EST L'OWNER QUI L'A DIT.**
Verbatim : *« non au contraire tu me fais tourné et moi je regarde si avec le doigts c'est ok »*.

Je faisais défiler les pages **depuis la console** (`nav open`). Or `nav open <autre>` produit une
transition **`détail → détail`** que **le doigt ne peut pas produire** : depuis la dalle, on repasse
**toujours** par le dashboard. ⇒ Les quatre premières fenêtres faisaient regarder un chemin qui
n'existe pas à l'usage — et **c'est ce chemin-là qui portait le défaut de repeint** (§22.11).

✅ **Protocole retenu** : injection **continue**, ⛔ **aucune** navigation depuis la console, **l'owner
pilote au doigt**. Validité prouvée par les compteurs : **26 appuis, 26 relâches, 0 erreur I²C**.

#### a. 🔴 LA LATENCE AU DOIGT — ET `nav ab` LA SOUS-ESTIME

| Instrument | ce qu'il mesure | n | min | **moy** | max |
|---|---|---|---|---|---|
| `nav ab 20` | `dn_ui_nav_open()` → écran flushé | 40 | 171,4 ms | **337,6 ms** | 400,9 ms |
| 🔴 **`touch` (le DOIGT)** | **tap → écran flushé** | **26** | 284,9 ms | **361,8 ms** | 432,1 ms |

🔴 **`nav ab` SOUS-ESTIME DE ~24 ms CE QUE L'OWNER RESSENT.** L'écart est la chaîne tactile
(scrutation GT911 + anti-rebond) que `nav ab` **court-circuite** en appelant la navigation
directement. ⚠️ Comparaison de **deux instruments** sur **deux échantillons** : l'écart est indicatif,
⛔ pas un A/B.
⇒ **Conséquence pour le budget** : en opaque, `nav ab` rend **271,8 ms** — mais **au doigt cela
ferait ~296 ms**. La marge sous les 300 ms serait de **~4 ms**, ⛔ pas de 28.

#### b. Les verbatims de la passe au doigt

| # | Point | Verbatim owner |
|---|---|---|
| 1 | la courbe de la page quittée s'effface ? | ✅ *« oui tt est bon »* |
| 2 | CPU/GPU distincts ? | 🎯 *« en fait c'est parce que la courbe de cpu et gpu sont les mêmes ! sinon couleur bien diff »* |
| 3 | `RÉSEAU` deux courbes + chevrons colorés | ✅ *« ok »* |
| 4 | `RAM` (rose, échelle bornée) | ✅ *« tres bien »* |
| 5 | la ligne `MIN/MAX sur : …` | ✅ *« ok »* |
| 6 | **latence ressentie** | ✅ 🎯 *« franchement ca repond tres bien »* |

#### c. 🔴 LE CONSTAT n°2 EST UN **DÉFAUT DE MON HARNAIS**, LE TROISIÈME DE LA SÉANCE

`tools/anim_courbe_dn44.py` émettait **des sinusoïdes pour toutes les métriques**. Comme l'échelle du
graphe **s'auto-cale**, chaque série **remplit la boîte** : toutes les pages rendaient **la même
vague**, quelles que soient leurs amplitudes réelles.
⇒ 🔴 **LE HARNAIS FABRIQUAIT LA RESSEMBLANCE QU'IL SERVAIT À TESTER.**

⚠️ **C'est la faute que ce dépôt reproche déjà à `dn_injecteur.py`** (*« valeurs FIXES »*), **d'un cran
plus subtile** : des valeurs qui **changent** ne suffisent pas, il faut qu'elles changent
**DIFFÉREMMENT**. Corrigé : une forme **reconnaissable à l'œil** par métrique —

| Métrique | forme | relevé à `t = 0, 3, 6, 9, 12 s` (grandeur 0, dixièmes) |
|---|---|---|
| `CPU` | **dent de scie** | 950 · 737 · 525 · 312 · 950 |
| `GPU` | **créneau** | 950 · 950 · 950 · 150 · 150 |
| `RAM` | **rampe** | 50 · 158 · 266 · 374 · 482 |
| `RÉSEAU` | **marches** (↓) + **sinus** (↑) | 100 · 100 · 6 350 · 12 600 · 18 850 |
| `DISQUE` | **sinus** | 11 000 · 14 740 · 17 803 · 19 636 · 19 907 |

⇒ Si deux pages rendent la même courbe **maintenant**, c'est le **firmware** qui lit la mauvaise
série, ⛔ plus le signal qui se ressemble.

#### d. ⚠️ ET UNE PROPRIÉTÉ RÉELLE QUE CE DÉFAUT A RÉVÉLÉE

L'auto-calage **efface l'information d'amplitude** : deux séries d'amplitudes très différentes
rendent la **même hauteur de vague**. C'est exactement le motif pour lequel l'owner a demandé de
**borner `RAM` à 0..100 %** — et ça vaut **aussi** pour les pourcentages de `CPU` et `GPU`.
⛔ **Non fait sans décision** : la question est posée, ⛔ pas tranchée par l'agent.

### 22.11 LE DÉFAUT DE REPEINT — `détail → détail` N'INVALIDAIT RIEN

Constat owner, en deux temps : *« la transition n'efface pas la cpu pour gpu »*, puis — après un
premier correctif **insuffisant** — *« non pas pour gpu apres cpu … le reste est propre »*.

🎯 **C'est la seconde formulation qui donne la cause** : « le reste est propre ».
`lv_screen_load()` sur l'écran **DÉJÀ ACTIF** est un **no-op** : il n'invalide **rien**. Sur
`dashboard → détail` et `détail → dashboard`, l'écran **change** et LVGL repeint tout — d'où « le
reste est propre ». Mais `détail → détail` ne repeint que ce que les objets invalident **eux-mêmes**,
et un `lv_chart` au fond **transparent** laisse sa ligne précédente sous un repeint partiel en bandes.

⛔ **MON PREMIER CORRECTIF (invalider le CADRE) NE SUFFISAIT PAS, ET C'EST L'ŒIL QUI L'A DIT.**
On invalide désormais **l'écran entier** : un changement de page **est** un repeint de page.

⚠️ **COÛT BORNÉ** : `nav ab` alterne détail↔dashboard, donc l'écran change à chaque fois ⇒ **les
latences publiées ne sont pas affectées**, et ce n'est pas une façon de les embellir.
⚠️ **Et le doigt ne produit pas cette transition** : elle n'est atteignable qu'à la console, donc
**par les harnais de mesure**. Le défaut était réel mais **invisible à l'usage** — ⛔ ce n'est pas une
raison de le laisser : *un instrument qui salit l'écran fausse le prochain constat à l'œil*, et c'est
exactement ce qui est arrivé **deux fois**.

### 22.12 🎯 AC9.3 — LA VISÉE, ET CE QU'ELLE APPREND SUR **LA MÉTHODE**

**2026-08-24.** Cible rendue visible (`widget piste 0xFF2020`, `RAM` sans donnée ⇒ **barre rouge sur
toute sa longueur**), owner visant **la barre** et non le centre de la case, retour par la flèche
entre chaque visée. `touch trace 90000`, capture dans `mesures/dn4-4/visee-jauge-ram-2026-08-24.log`.

⚠️ **9 visées enregistrées** (18 appuis = 9 `RAM` + 9 `RETOUR`) pour **10 annoncées** par l'owner :
la 10ᵉ est probablement tombée **après** la fenêtre de 90 s. ⛔ Elle n'est pas inventée — on compte
ce qui est enregistré.

```
(153,336) (75,338) (208,349) (161,357) (100,351) (55,354) (135,345) (207,354) (211,363)
```

| | relevé | cible **RELUE DE LVGL** |
|---|---|---|
| **x** | `55..211` — **9/9 DEDANS** ✅ | `23..223` (201 px) |
| **y** | `336..363` · moyenne **349,7** · **σ = 8,8 px** | `338..347` (**10 px**), centre 342,5 |
| biais moyen | **+7,2 px** · erreur-type 2,9 ⇒ **2,5 σ** | — |
| 🔴 **dispersion / hauteur de cible** | 🔴 **1,8×** (2 σ = 17,6 px contre 10 px) | — |

#### 🔴 LE RÉSULTAT PRINCIPAL EST UNE LIMITE DE LA MÉTHODE, ⛔ PAS UN CHIFFRE

**AC9.3 demande de confirmer une bande de 10 px par une visée au doigt.** Or la **dispersion du
doigt vaut 1,8× la hauteur de la cible**. ⇒ **Une visée à 9 taps NE PEUT PAS, STRUCTURELLEMENT,
valider une bande de 10 px** : l'instrument n'a pas la résolution de l'arbitrage qu'on lui demande.
⚠️ C'est le même piège que le dépôt traque ailleurs (*« un critère de preuve peut être satisfait par
l'état MORT »*), sous une autre forme : **un critère de preuve peut aussi être HORS DE PORTÉE de
l'instrument qui doit le satisfaire.** ⛔ On ne coche pas en espérant que 2/9 suffisent.

#### CE QUE LA VISÉE RÈGLE QUAND MÊME

- ✅ **`x` est confirmé sans ambiguïté** : 9/9 dans une bande de 201 px.
- ✅ **L'écart systématique de 13-24 px du 2026-08-20 N'EST PAS REPRODUIT.** Il valait alors
  `y = 350..371` ; il vaut aujourd'hui `336..363`, biais **+7,2 px**. ⇒ Cohérent avec §22.3 : la
  bande d'août avait été relevée sous une **géométrie différente** (`widget val` est commutable à
  chaud et **RAM-only**).
- ✅ **La formule reste la lecture retenue**, mais elle l'est **par la relecture de l'objet**
  (`widget jauge`, écart de **1 px** expliqué par la bordure), ⛔ **pas par la visée**.

#### ⛔ CE QUE §22.12 NE PROUVE PAS

Que les **+7,2 px** soient un vrai biais de visée (le centroïde de contact du doigt tombe sous le
point visé sur une ligne fine) **ou du bruit**. À `n = 9` et `σ = 8,8`, on est à **2,5 σ** : à la
limite de la signification. **Indécidable en l'état**, et dit comme tel.
⇒ **Ce qu'il faudrait pour trancher** : une cible **plus haute** (la barre fait 10 px), ou **n ≫ 9**.
Aucun des deux n'est dans le périmètre de `dn4-4`.

---

# §23. 🎯 `dn4-13` (P9.4b) — LES INSTRUMENTS SONT RÉPARÉS, ET LES QUATRE ÉCARTS SONT RE-MESURÉS

> **Séance du 2026-08-25.** Firmware **`7b375c3`**, **SHA LU AU BANDEAU**,
> `git status --porcelain` **vérifié VIDE avant chaque flash**.
> ⛔ **UN SEUL ÉTAT DE FIRMWARE PORTE TOUS LES CHIFFRES DE CETTE SECTION.** C'est la
> règle qu'AC11.1 impose, et c'est exactement celle que `dn4-4` avait violée
> (`aa99fa2` mesuré, `df634d1` livré). Le carré 2×2 a d'ailleurs été tiré **DEUX
> FOIS** ici : une première sur `820f1d5`, puis **RE-TIRÉ ENTIÈREMENT** sur
> `7b375c3` quand les constats œil de l'owner ont changé le binaire. ⛔ Les
> chiffres de `820f1d5` ne sont **pas** publiés.

## 23.1 ⚠️ LA CONTRAINTE DE TRANSPORT, DITE AVANT LES CHIFFRES

**La source est MUETTE pendant toutes les mesures de latence**, et ce n'est pas un
choix de confort : `liaison-pc.md` §13 le mesure — *« Une campagne de mesure ne
peut PAS tourner pendant que l'agent tient le port. Campagne et agent ALTERNENT,
ils ne coexistent pas. »* Or **tous** les relevés ci-dessous se lisent **à travers
la console** (`nav ab`, `widget courbe`, `hist`, `mem`, `touch reset`).

⇒ 🔴 **LE PRÉREQUIS « L'AGENT RÉEL SUR LA TOUR » D'AC11 EST INSATISFIABLE POUR CES
RELEVÉS-LÀ**, et `dn4-4` ne l'avait pas satisfait non plus (§22.4 est console
seule). L'agent réel a servi à ce pour quoi il est indispensable : **l'œil de
l'owner**, où aucune console ne lit rien.
⛔ Ce n'est pas une excuse : c'est une propriété du transport branche A, et elle
borne ce que ces nombres décrivent — **une page dont les cases sont éteintes**.

## 23.2 🔴 LE CARRÉ 2×2, RE-TIRÉ ENTIÈREMENT

Protocole **identique à §22.4**, pour être comparable : `touch reset`, puis
**`nav ab 20`** (**n = 40**), dalle **NON TOUCHÉE**.
**`transitions RÉELLES = 40 (demandées 40)` aux CINQ tirs**, `taps` = **0**,
et **0 synchro expirée NOUVELLE par passe**.

> 🔴 **CORRIGÉ PAR LA REVUE DE CODE DU 2026-08-25 — ⛔ PAS EFFACÉ.**
> Cette ligne annonçait **« 0 synchro expirée »** et un **« `flush reset`
> implicite »**. Les deux étaient FAUX, et les captures livrées le montrent :
> chacun des cinq `*-navab20-*.log` porte **`⚠️ 5 synchro(s) EXPIRÉE(S)`** dans
> son bloc `flush AVANT` **et** dans son bloc `APRÈS` — dont le texte avertit
> lui-même qu'*« une comparaison A/B qui les inclut compare partiellement "rien"
> à "rien" »*. Le compteur vaut **5 des deux côtés** : le « 0 » était un **Δ
> dérivé d'un cumul jamais remis à zéro**. Et le `flush reset` n'a pas eu lieu —
> les flushes cumulent sans discontinuité sur toute la séance (1930 → 2132 →
> 2149 → 2352 → 2369 → 2571 → 2588 → 2804 → 2821 → 3034).
> ⇒ **Le chiffre était juste, la PHRASE était fausse.** C'est la famille n°2 des
> Dev Notes, et aucune des 7 gates ne relit un libellé.
> ⚠️ La même phrase est reprise dans `brief.md` et dans le ledger : les deux
> portent le même correctif, à la même date.

🔴 **CHAQUE CHIFFRE CI-DESSOUS EST DANS `mesures/dn4-13/*.log`**, et le log porte
en tête le SHA, le protocole et la contrainte de source. ⛔ **Le chiffre publié et
le log livré viennent du MÊME geste** — c'est ce que `dn4-4` n'avait pas fait pour
deux de ses quatre coins.

| | `opa 178 / voile 90` — **LE PRODUIT** | `opa 255 / voile 0` — opaque |
|---|---|---|
| **fond POSÉ** | 🔴 **335,8 ms** (289,1 / 400,8) | **253,0 ms** (213,6 / 310,1) |
| **fond RETIRÉ** | **193,9 ms** (140,2 / 244,8) | **167,3 ms** (137,0 / 215,3) |

| Effet isolé | Valeur |
|---|---|
| le **fond**, à opacité produit | **−141,9 ms** (−42,3 %) |
| le **fond**, à panneaux opaques | −85,7 ms |
| l'**alpha**, fond posé | **−82,8 ms** (−24,7 %) |
| l'**alpha**, fond retiré | −26,6 ms |
| **les deux ensemble** | **−168,5 ms (−50,2 %)** |
| 🔴 **INTERACTION** | **−56,2 ms** (224,7 attendus, 168,5 obtenus) |

🔴 **LA CONCLUSION DE §22.4 TIENT, ET ELLE TIENT SUR UN INSTRUMENT CORRIGÉ.**
L'interaction reste **forte** (−56,2 ms ici, −75,3 en T1) ⇒ *« ne pas invalider le
fond »* **ne peut toujours PAS s'obtenir par un partage d'objet tant que les
panneaux sont semi-transparents**. ⛔ **Un seul mécanisme, pas deux leviers.**

⚠️ **CE QUI A CHANGÉ DEPUIS §22.4, ET POURQUOI ON NE PEUT PAS COMPARER COIN À COIN :**
le coin `fond RETIRÉ` de §22.4 (**194,2 ms**) a été mesuré avec un `fond_poser()`
qui posait en réalité **l'écran de panne `ASSET ABSENT`** — un remplissage plat
**+ deux labels** — alors qu'AC7 promettait *« UNE SEULE VARIABLE : le fond, et
rien d'autre »*. Il est corrigé (§23.5). Les deux carrés concordent en
**structure**, ⛔ pas nécessairement au dixième de milliseconde.

## 23.3 🔴 AC7.6 — LE CRITÈRE DEVIENT ÉVALUABLE, **ET IL NE TIENT PAS**

`dn4-4` déclarait le critère **INÉVALUABLE** : la tolérance `±0,04` porte sur
*« deux passes du MÊME cas »*, et **aucun cas n'avait été tiré deux fois**. Le
coin **PRODUIT a donc été tiré DEUX FOIS**, à l'identique :

| Passe | Δ flush | Δ cycles | **`flush/cyc`** | latence moyenne |
|---|---|---|---|---|
| **t1** — produit | 202 | 42 | **4,8095** | 335,8 ms |
| **t1bis** — produit, **RÉPÉTÉ** | 203 | 43 | **4,7209** | 336,7 ms |
| | | | 🔴 **\|Δ\| = 0,0886** | Δ = 0,9 ms |

🔴 **LA TOLÉRANCE ±0,04 NE TIENT PAS : l'écart vaut 0,0886, soit 2,2× la
tolérance.** Le critère est désormais **ÉVALUABLE**, et il est **EN DÉFAUT**.

⚠️ **ET J'ALLAIS PUBLIER L'INVERSE. C'EST LE POINT LE PLUS IMPORTANT DE §23.**
Un **premier** tir du même protocole, **sans capture**, avait rendu `202/42` aux
DEUX passes — `|Δ| = 0,0000`, un accord parfait, et j'avais écrit *« ✅ la
tolérance tient »*. C'est en re-tirant **pour produire les logs manquants** (AC12.5)
que le désaccord est apparu.
⇒ 🔴 **DEUX PAIRES DE PASSES DU MÊME CAS, SUR LE MÊME BINAIRE, DONNENT DEUX
VERDICTS OPPOSÉS.** La conclusion n'est donc pas *« flush/cyc est instable »* ni
*« il est stable »* : c'est que **±0,04 est plus serré que la dispersion propre de
l'instrument**, et qu'**une seule paire de passes ne peut pas trancher ce critère**.
⛔ *Un critère de preuve peut être hors de portée de l'instrument censé le
satisfaire* — la même leçon qu'AC9.3 avait payée sur la visée du doigt (§22.12).

**Ce qu'il faudrait pour trancher** : `k` paires de passes, et une tolérance
dérivée de la dispersion **mesurée**, ⛔ pas posée a priori. Versé au ledger.

⚠️ L'instrument **n'est pas bloqué** : les autres coins rendent **4,8095 · 4,0755 ·
4,0189**. Et l'écart entre « fond posé » (~4,8) et « fond retiré » (~4,0) est un
**signal**, ⛔ pas du bruit — moins de bandes à repeindre sans image de fond.

## 23.4 ✅ AC5 — CE QUE LE CONDITIONNEMENT ÉCONOMISE, CHIFFRÉ, ET OÙ IL N'ÉCONOMISE RIEN

`courbe_reparametrer()` invalidait **460 × 108 px** *inconditionnellement*, jusqu'à
cinq fois par seconde, **y compris sur une série 100 % trous** — pendant que
`dn_hist.h` justifiait de ne pas mettre l'échantillonnage sur `case_poser` au motif
que *« ce chemin est le plus chaud de la vue détail »*. L'ironie est levée.

| Régime, détail `RÉSEAU` ouvert, 30 s | demandes | redessins | évité |
|---|---|---|---|
| source **MUETTE** | 30 | 30 | **0 %** |
| source **VIVE** (150 trames, 5 métriques à 1 Hz) | 62 | 33 | **47 %** |

> 🔴 **QUI POUSSAIT ? `tools/anim_courbe_dn44.py` — NOMMÉ ICI LE 2026-08-25,
> SUR DÉCISION OWNER, À L'ISSUE DE LA REVUE DE CODE.**
> Cette ligne disait *« source VIVE (150 trames, 5 métriques à 1 Hz) »* **sans
> nommer l'instrument**, alors que le `Debug Log` de la story déclare que
> *« L'AGENT RÉEL SUR LA TOUR N'A PAS ALIMENTÉ LES MESURES, ET C'EST
> PHYSIQUE »* (le port série est exclusif).
> ⚠️ **CE QUE ÇA COÛTE, ÉCRIT PLUTÔT QUE TAIT** : `anim_courbe_dn44.py` est un
> **injecteur à formes synthétiques**, ⛔ pas l'agent réel — et le tableau de
> prérequis d'AC11 pose que *« tout chiffre où LE DESSIN est la variable se
> mesure sous agent réel, et c'est exactement le cas d'**AC5** »*, `dn4-10`
> ayant mesuré un **facteur 108** d'écart sur le dessin entre injecteur et
> agent réel. ⇒ **Le 47 % décrit ce que le conditionnement économise SOUS CET
> INJECTEUR-LÀ**, ⛔ pas sous l'agent de la tour.
> ⛔ **ET AUCUNE CAPTURE NE LE PORTE** : les 6 fichiers de `mesures/dn4-13/`
> sont les cinq coins et le `hist`/`mem` — aucun relevé `widget courbe`.
> ⚠️ **La revue du 2026-08-25 a par ailleurs trouvé DEUX défauts dans cet
> injecteur** : sa fenêtre de drainage utilisait un horodatage périmé et
> pouvait être **déjà écoulée** (zéro drainage, cadence 1 Hz perdue en
> silence), et `--par-page 0` était accepté, rendant une fenêtre
> d'observation **vide** annoncée comme accomplie. Les deux sont corrigés —
> mais ⛔ **après** ce relevé.

⚠️ **LES TROIS NOMBRES DE LA LIGNE « VIVE » VIENNENT DU MÊME TIR**, et c'est dit
parce que ça a failli ne pas être le cas : un premier tir avait rendu `60 / 31`
(48 %), un second `62 / 33` (47 %). Mélanger le compte de l'un au pourcentage de
l'autre aurait produit un chiffre **juste-en-apparence**. C'est le tir n°2 qui est
publié, **celui qui porte aussi la mesure d'aire ci-dessous**.

- **29 invalidations de 49 680 px évitées en 30 s**, soit **1 440 720 px** —
  l'équivalent de **39 %** de l'aire réellement poussée (3 671 418 px).
- ⚠️ **CE N'EST PAS « 39 % DE TEMPS GAGNÉ ».** L'aire évitée est une **BORNE
  HAUTE** : LVGL fusionne les zones sales, donc une invalidation de plus n'ajoute
  pas toujours son aire. **Le chiffre solide est le COMPTE.**
- 🔴 **ET LE GAIN EST NUL EN SOURCE MUETTE, DIT ICI PLUTÔT QU'OMIS** : l'horloge
  1 Hz fait avancer l'anneau à chaque tick, donc la signature change et le
  redessin est **DÛ**. Le mécanisme n'économise que ce qui est *inutile*.

## 23.5 ✅ AC5.6 — LE COÛT DE `dn_hist`, PAR TROIS INSTRUMENTS INDÉPENDANTS

| Instrument | Valeur |
|---|---|
| `dn_hist_octets_detail()` sur la carte (`hist`) | **5 657 o** |
| Somme de **TOUS** les symboles `dn_hist.c.obj` du **`.map`** | **5 657 o** |
| `sizeof` recalculé sur l'hôte par `verif_hist_dn413.py` | **5 657 o** |
| **écart** | **+0 o** |

Décomposition : **points 3 840** (8 × 120 × 4) · **seaux 1 728**
(`s_smin` + `s_smax` + `s_svu`) · **index 89**.
🔴 `dn_hist_octets()` rendait `sizeof(s_pts)` **SEUL** = 3 840 o :
**sous-déclaration de 1 817 o (32 %)**, sur l'instrument même censé solder AC5.6.

⚠️ **LA PRÉDICTION N'EST PAS RÉÉCRITE, ON ÉCRIT L'ÉCART.** `dn_hist.h` prédisait
**−3 400 à −3 500 o**, et le relevé `−3 512 o` de §22.5 la confrontait — **les
deux décrivaient un module à 7 séries SANS seaux**. Le module en porte huit et a
gagné ses 24 seaux depuis : il pèse **5 657 o**, soit **~2 200 o de plus** que ce
qui avait été prédit. ⛔ *On ne réécrit pas une prédiction pour qu'elle tombe
juste* — elle était juste à son époque, et c'est la story qui a grossi.
RAM interne libre au relevé : **74 503 o** (`mesures/dn4-13/hist-mem-2026-08-25.log:54`).

> 🔴 **CORRIGÉ PAR LA REVUE DU 2026-08-25.** Cette ligne citait **74 487 o**, un
> chiffre qui ne vient PAS de la capture dont parle cette section : il vient de
> `t3-sans-fond-navab20-2026-08-25.log:62`, **un autre coin du carré**. La règle
> du « MÊME geste » posée en §23.2 vaut aussi pour les octets.
> ⛔ **ET LE `mem` « AVANT/APRÈS » D'AC11.3 N'A PAS ÉTÉ JOUÉ** : la capture ne
> contient qu'**un seul** bloc `mem`. Ce qui a été fait à la place — la
> triangulation par **trois** instruments indépendants (carte, `.map`, hôte),
> écart **+0 o** — est *meilleur* que ce que l'AC décrivait, mais ⛔ **ce n'est
> pas ce que l'AC décrivait**, et AC5.6 est soldé sur celui-là.

## 23.6 ✅ AC2 — LES QUATRE TÉMOINS, AVEC LE CROISÉ VU ROUGIR D'ABORD

Le témoin **CROISÉ** de `dn4-4` rendait **VERT SUR DEUX LECTURES RATÉES** :
`texte()` rend `"<NON RELU>"` en repli, et le verdict était
`avant == apres and avant.strip() != "--"` ⇒ **`True and True`**.
⚠️ Et c'est **la garde que le dossier de `dn4-4` célébrait** (*« le témoin croisé
n'est valide que si l'avant n'est pas `--` »*) : elle attrapait le `--`, **pas** la
sentinelle.

- 🔴 **Le témoin a d'abord été VU ROUGIR** sur **5 entrées** (deux sentinelles, une
  seule, deux `--`, une page qui bouge) — `--temoin-negatif`, **19 cas au total**.
- ✅ Puis les **quatre témoins sont VERTS sur la carte** : POSITIF (3 textes dans
  l'ordre) · PÉREMPTION (retour à `--` après 4 s) · MOCK (régime `SIMULÉE`,
  valeur qui VARIE) · CROISÉ (le détail CPU ne bouge pas pendant que `net` bouge).

## 23.7 ✅ AC4.3 — LE TÉMOIN DE GARDE EST **REJOUABLE**

`s_gardeh_cris` est CUMULATIF, et la console tranchait dessus : après un retour au
produit, elle imprimait encore *« ✅ elle a CRIÉ »* sur une garde **muette**, et la
branche *« 🔴 la garde est CASSÉE »* devenait **injoignable dès le premier cri**.

| État | panneau | label / y | `cris` | Verdict de la console |
|---|---|---|---|---|
| PRODUIT (154) | 154 | 140 @ 14 | **0** | ✅ silence LÉGITIME — `14+140 = 154 ≤ 154`, **marge zéro** |
| ARMÉ (153) | 153 | 140 @ 14 | **2** | ✅ **elle a CRIÉ au dernier passage** |
| RETOUR PRODUIT | 154 | 140 @ 14 | **0** | ✅ silence LÉGITIME |

⇒ **Rejoué trois fois dans la séance**, sur le firmware livré. `widget detpan`
remet les compteurs à zéro : **un témoin se remet à zéro, ou il n'est pas un témoin.**

## 23.8 ✅ CE QUE L'ŒIL A VU, ET LES DEUX CORRECTIONS QU'IL A DEMANDÉES

**Constats validés** (2 fenêtres d'observation, « prêt ? » demandé et OUI attendu
avant chacune, injection continue pendant toute l'observation) :

- ✅ **`RÉSEAU` : deux courbes DISTINCTES sur une échelle commune** (décision n°5).
- ✅ 🎯 **LE PRIX DE LA DÉCISION N°5 EST VU ET ASSUMÉ** : à **985 Mb/s ↓ contre
  5 Mb/s ↑**, le montant **s'écrase en trait plat en bas de boîte**. ⛔ Ce n'est
  **pas** un défaut à corriger — c'est la vérité brute du rapport entre les débits.
- ✅ **`widget fond off` laisse l'écran VRAIMENT NOIR sur les DEUX écrans** —
  dashboard **et** détail. ⛔ Aucun texte, aucun rouge.

**Deux corrections demandées par l'œil, et faites dans la séance** — écart de
périmètre sur `k_desc[]`, **levé explicitement par l'owner** :

1. *« réseau le vert ça ne se voit pas bien donc plutôt bleu et flèche aussi »*
   ⇒ descendant **BLEU VIF `0x3b82f6`** (était vert `0x4ade80`), montant **CYAN
   `0x22d3ee`** (était bleu clair `0x60a5fa`).
   ⛔ **LES DEUX ONT DÛ BOUGER, ET C'EST LA DÉCISION N°5 QUI L'IMPOSE** : sur la
   seule page où les deux courbes partagent la MÊME échelle, **la couleur est le
   seul discriminant restant**. Deux bleus l'auraient annulé.
   ✅ *« et flèche aussi »* est **gratuit** : `chevron_couleur()` **LIT** ces deux
   sources, il ne les recopie pas.
2. *« remettre le texte blanc avec l'icône temp devant le chiffre »*
   ⇒ `k_desc[AMBIANCE].grandeurs[0].icone = DN_ICONE_THERMOMETER_HALF`, colorée en
   **ORANGE** (la couleur de sa propre courbe), **texte BLANC**.
   🔴 **MON CORRECTIF D'AC4.5 MARCHAIT, ET L'OWNER N'EN A PAS VOULU.** Je
   recolorais **le segment entier** faute d'icône — j'avais écarté l'icône *« pour
   ne pas toucher la largeur »*. **La largeur se MESURE, elle ne se redoute pas** :
   après ajout, `widget` compte **0 chevauchement · 0 trop large · 0 en hauteur**,
   et la garde de largeur du détail **ne crie pas**.
   ⚠️ L'owner avait d'abord dit *« rouge »*, puis a tranché **orange** une fois la
   conséquence montrée : `DISQUE` est **déjà** rouge, et deux cases rouges se
   toucheraient sur le dashboard.

## 23.9 ⛔ CE QUE §23 NE PROUVE PAS

- **Que la page coûte 336,7 ms EN USAGE RÉEL.** Toutes les latences sont mesurées
  **source muette**, cases éteintes (§23.1). Une page vivante dessine **plus**.
- **Que le coût de la courbe vaut +0,7 ms.** Ce chiffre (336,3 ms de moyenne des
  deux passes capturées — 335,8 et 336,7 — contre les **335,6 ms** de T0) **CROISE DEUX BINAIRES** — T0 est de
  `dn4-4`/`aa99fa2`, et `dn4-13` a changé le chemin de dessin. Il est publié
  **une seule fois, avec un seul signe**, et cette phrase est le prix de la
  comparaison. ⇒ **Le vrai coût de la courbe reste dans la FRAGMENTATION** :
  **3 % → 45 %** (42 % en `dn4-4`), plus gros bloc libre 40 476 → ~22 000 o.
- **Que la fragmentation à 45 % soit STABLE.** Elle n'a été relevée qu'après des
  séries de transitions, jamais suivie dans le temps. Le tas LVGL est un pool
  **statique en `.bss`** : ⛔ ni `mem` ni la PSRAM n'en disent rien. *(ledger)*
- **Que le nombre AU DOIGT ait été re-tiré.** Les **361,8 ms** de `dn4-4` datent de
  `aa99fa2` et **n'ont pas été rejouées** — il faut `touch trace` et l'owner.
- **Que « > 1 h sans source PC » ait été joué** pour AC2.2. Voir §23.10.
- 🔴 **Que les chiffres de §23.10 et le verdict d'AC3.3 soient CAPTURÉS.** Ils ne
  le sont pas, et la seule capture `hist` livrée les CONTREDIT — autre boot. Voir
  l'encadré de §23.10. *(revue de code du 2026-08-25)*
- ✅ **RÉSOLU LE 2026-08-25 — que le firmware LIVRÉ soit celui qui a été MESURÉ.**
  Les correctifs de la revue avaient rendu le code POSTÉRIEUR à §23.1 → §23.10.
  Une séance de validation a été tirée sur `0ba9fc7`, SHA **lu au bandeau** : voir
  **§23.11**, capture `mesures/dn4-13/validation-revue-0ba9fc7-2026-08-25.log`.
  ⚠️ Les chiffres de **latence** de §23.2 restent ceux de `7b375c3` — §23.11 ne
  re-tire **aucune** latence, et le dit.
- 🔴 **Que le 47 % d'AC5.3 ait été mesuré sous AGENT RÉEL.** Il a été poussé par
  `tools/anim_courbe_dn44.py`, un injecteur à formes synthétiques, et aucune
  capture ne le porte. Voir l'encadré de §23.4. *(idem)*

## 23.10 ⚠️ AC2.2 — L'ÉCART DE MÉTHODE, DÉCLARÉ AVANT D'ÊTRE COMMIS

L'AC écrit *« carte allumée > 1 h »*. **On a tiré à 370 s**, et le témoin est
**plus fort que le protocole demandé** — pour une raison qui n'avait pas été
anticipée : dans **le même relevé**, à **uptime identique**,

- `GPU` et `RAM` — **les deux seules séries jamais alimentées** — rendent
  `couv(s) = **0**` ;
- les six autres rendent `couv(s) = **364**`.

⇒ **La discrimination est prouvée par la COEXISTENCE, ⛔ pas par un seuil de
temps.** L'ancienne version aurait rendu **370 pour les huit**.
⛔ **Le « > 1 h » n'a PAS été joué, et AC2.2 est coché sur CE témoin-ci**, pas sur
celui que l'AC décrivait. Écrit ici pour que personne ne lise l'heure dans ces
chiffres.

*Recoupement indépendant, non cherché* : `AMBIANCE` affiche `ecrits 120 · trous 65`
— les **65 trous sont exactement la pause de 65 s** d'AC3.3, visible dans l'anneau
par un second chemin que celui du compteur de rattrapage.

> 🔴 **ABSENCE DE CAPTURE — DÉCLARÉE LE 2026-08-25 SUR DÉCISION OWNER, À
> L'ISSUE DE LA REVUE DE CODE. ⛔ ELLE N'EST PAS COMBLÉE.**
>
> **Les chiffres de cette section (§23.10) et le verdict d'AC3.3 viennent d'un
> relevé qui N'A PAS ÉTÉ CAPTURÉ, et d'un BOOT DIFFÉRENT des six captures
> livrées.** La seule capture `hist` du dossier les contredit terme à terme :
>
> | Publié ici / coché en T3 | `mesures/dn4-13/hist-mem-2026-08-25.log` |
> |---|---|
> | `couv 0` (GPU/RAM) vs `couv 364` (six autres), uptime **370 s** | `couv 947` pour **les huit**, uptime **947 s** |
> | `AMBIANCE : ecrits 120 · trous 65` | `AMBIANCE T : ecrits 120 · reels 120 · trous 0` |
> | T3/AC3.3 : *« 1 coupure, 65 trous comblés »* | `rattrapage : 0 coupure(s), 0 point(s) de trou comble(s)` |
>
> `grep 364` sur tout `mesures/dn4-13/` ⇒ **aucune capture**.
>
> ⚠️ **C'est §23.2 qui pose la règle enfreinte ici** : *« le chiffre publié et le
> log livré viennent du MÊME geste — c'est ce que `dn4-4` n'avait pas fait »*.
> La story énonce la leçon et la répète.
> ⇒ **AC2.2 et AC3.3 restent soldés sur des relevés VUS À LA CONSOLE mais NON
> CAPTURÉS.** L'owner a tranché : on **déclare**, ⛔ on ne re-tire pas et on ne
> décoche pas. Quiconque relit ces deux verdicts doit savoir qu'aucun fichier du
> dépôt ne les porte.
> 🔗 Même traitement que la capture T0 d'AC12.5, absente et déclarée.

## 23.11 ✅ SÉANCE DE VALIDATION DES CORRECTIFS DE REVUE — firmware `0ba9fc7`

🔴 **POURQUOI CETTE SÉANCE EXISTE.** La revue de code du 2026-08-25 a produit 18
correctifs, dont quatre qui touchent le **firmware**. Le code de l'arbre est donc
devenu **postérieur à tous les chiffres de §23.1 → §23.10**, qui portent `7b375c3`.
C'est **exactement l'écart mesuré/livré que `dn4-13` existe pour solder** — `dn4-4`
avait mesuré `aa99fa2` et livré `df634d1`. On ne le recrée pas en silence.

**Capture : `mesures/dn4-13/validation-revue-0ba9fc7-2026-08-25.log`** (340 l.).
SHA **LU AU BANDEAU** (`I (679) app_init: App version: 0ba9fc7`), `git status
--porcelain` **VIDE** avant le flash, `SPI Flash Size : 16MB`, PSRAM 8 Mo trouvée,
`app_main` atteint. Config active : `num_fbs=1 bounce_px=9600 draw_lines=128`.

| # | Ce qu'on vérifie | Résultat |
|---|---|---|
| A2 | le coût de `dn_hist` n'a pas bougé | ✅ **`5 657 o`**, `index 89 o` — **identique à `7b375c3`** : les correctifs n'ont ajouté **aucune statique**, et §23.5 reste valide |
| A3 | 🔴 le compteur publie **l'observation**, pas le plafond | ✅ `ui off` de **135 s** ⇒ **`+1 coupure, +135 trous`**. L'ancien code écrêtait à `DN_HIST_N_POINTS` **avant** de compter ⇒ il aurait imprimé **120**. Second tir à ~31 s ⇒ **`+29`** : deux coupures de durées différentes sont **DISCERNABLES** |
| A4 | les bornes de `widget detpan` | ✅ `39` **REFUSÉ** · `40` accepté · `167` accepté · `168` **REFUSÉ** · `200` **REFUSÉ**. Refus explicite (`0x1`), ⛔ pas d'écrêtage silencieux |
| A5 | la courbe survit à une reconstruction de scène | ✅ modèle **`rebuild`** + `nav open 5` + `widget detpan 160` (qui rejoue `build_scene()`) ⇒ `series : 2`, **axes POSÉS** (`249..255` / `473..479`), ⛔ **aucun `PAS POSE`** |
| A6 | le ratio d'AC5 ne peut plus déborder | ✅ `344 demandes · 316 redessins ⇒ 8 %`. Aucun `⛔ PAS MESURE` ⇒ le verrou a été pris |
| B1 | 👁️ **constat owner** — le boot | ✅ *« asset plein écran, rétroéclairage fixe, rien d'anormal »* |
| B2 | 👁️ **constat owner** — la courbe après reconstruction | ✅ *« la courbe est dessinée, deux couleurs, rien d'anormal »* — 🔴 **c'est la SEULE preuve du correctif de cache** : la console peut dire « posé » sans qu'un pixel soit arrivé |

### 🔴 CE QUE LA SÉANCE A TROUVÉ ET QUI N'ÉTAIT PAS AU PROGRAMME

**L'HORLOGE D'ÉCHANTILLONNAGE DÉRIVE PENDANT LA PHASE DE BOOT, ET PERSONNE NE LE
SAVAIT.** `hist_tick` est un `lv_timer` à `DN_HIST_PERIODE_MS = 1000` — et un timer
LVGL **ne rattrape pas** : il tire à 1 000 ms **plus** le temps de rendu. Mesuré :
**~21 tirs en 27 s** au boot, soit ~1 290 ms par tir, dont le déficit accumulé
franchit 2 000 ms environ **un tir sur 3,5** ⇒ **6 trous creusés**.

- ⛔ **CE N'EST PAS UNE RÉGRESSION** : la dérive existait déjà. L'ancien code
  **jetait le reste infra-période** et publiait *« 0 coupure — régime nominal »*.
  C'est le correctif qui la rend VISIBLE.
- ✅ **ET ELLE EST TRANSITOIRE** : **8** événements dans les ~90 premières secondes,
  puis **AUCUN** en régime établi — vérifié sur plusieurs minutes de
  reconstructions, navigations et changements de panneau (`10 coupure(s), 172
  trou(s)` inchangé du début à la fin du bloc final).
- ⚠️ **CONSÉQUENCE SUR UNE PHRASE DU DÉPÔT** : `dn_hist.h` écrit qu'« à 1 Hz, ce
  nombre EST la fenêtre courte réelle, en secondes ». Pendant le boot, les
  positions écrites ne valaient **pas** des secondes. C'est le comblement qui
  rétablit la correspondance.

### ⚠️ UNE ERREUR DE MÉTHODE COMMISE DANS CETTE SÉANCE, ÉCRITE PLUTÔT QUE TUE

La première lecture d'A3 rendait `8 coupure(s), 8 trou(s)` **après** la pause de
135 s — donc « le correctif ne compte rien ». **C'ÉTAIT LA LECTURE QUI ÉTAIT
PRÉMATURÉE** : le `lv_timer` de rattrapage n'avait pas encore tiré au moment du
`hist`, et le bloc suivant l'a retrouvé à `9/143`. Le délai mesuré est **> 1 s et
< 3 s** après `ui on`.
🔴 **Et j'ai enchaîné une seconde erreur sur la première** : j'ai conclu que
« l'échantillonnage a continué pendant l'`ui off` » et mis en doute la prémisse
d'AC3, à partir d'un `trous 0` qui n'était que la même lecture prématurée. Le test
discriminant (injection d'une trame `cpu` **pendant** la pause) a tranché
l'inverse : **`CPU` reste à `reels 0`** et le compteur reste **figé** pendant toute
la pause. ⇒ **`ui off` arrête bien `hist_tick`, et `dn_ui.c:5046` disait vrai.**
⇒ *Un instrument asynchrone se relit APRÈS son échéance, sinon on mesure sa
latence en croyant mesurer son verdict.*

---

# §24. 🎯 `dn3-3` (P8) — LA VEILLE DEVIENT UN CONTRAT, ET LE BANDEAU `MENU` UNE PORTE

> ⚠️ **CETTE SECTION EST OUVERTE LE 2026-08-25 ET ELLE N'EST PAS FINIE.**
> §24.1-24.6 sont prouvés **SANS CARTE**. **§24.7 est la SÉANCE CARTE, partie
> SANS ŒIL** — 12 relevés tirés à la console sur le firmware `e0af1c6`, SHA lu au
> bandeau. **§24.8 dit ce qui reste**, et il reste tout ce qui demande l'œil :
> les **20 réveils chronométrés**, les **deux gates tactiles**, les **8 constats
> d'AC9** et la **nuit**. ⛔ **Aucune latence t₁/t₂ n'est publiée à ce jour.**

## 24.1 ✅ AC1.4 — LE RECOMPTE DE LA PARTITION, ET IL COMMENCE À « DEUX »

Le ledger (`deferred-work.md:1620`) écrivait *« trois déclinaisons ne tiennent
pas »*. **Le vrai chiffre commence à DEUX** :

| Poste | Octets | Source |
|---|---:|---|
| Partition `assets` | **1 048 576** | `partitions.csv`, `0x100000` |
| Living PCB v0 + son pied | **614 416** | `DN_FB_BYTES` (480 × 640 × 2) + `DN_ASSET_TRAILER_LEN` (16) |
| Libre | **434 160** | différence |
| Une **2ᵉ** déclinaison | **614 416** | > 434 160 libres ⇒ ❌ il manque **180 256 o** |
| **DEUX** déclinaisons | **1 228 832** | > 1 048 576 ⇒ ❌ |
| **TROIS** déclinaisons | **1 843 248** | facteur **1,75** ⇒ ❌ |

🔴 **LA STORY SE TROMPE DE 16 OCTETS SUR « DEUX »** : elle écrit `1 228 816`,
c'est-à-dire **UN SEUL pied pour deux assets**, alors qu'elle en compte bien
**trois pour trois** (`1 843 248`, exact). Chaque asset porte **sa** bande-annonce
(magie `DNASSET1` + longueur + CRC32). Le verdict ne change pas — les deux
chiffres dépassent — mais **un chiffre publié se relit**.

⚠️ **ET `dn_asset` NE GÈRE QU'UN SEUL ASSET** : offset fixe, une magie, un CRC
(`dn_asset.h:24-48`). Même si la place existait, il faudrait le généraliser.

⇒ **VOIE RETENUE : (b) — UNE SEULE IMAGE + transformation à l'affichage.**
(1) l'arithmétique ci-dessus élimine (a) et (c) **sans mesure** ; (2) le voile
translucide **existe déjà** et fait exactement ça ; (3) la partition ne bouge pas,
donc **aucun risque de brick au reflash**.
✅ `partitions.csv` est **INCHANGÉ** — `git diff --stat` ne le montre pas, et la
gate hôte le **vérifie** (`veille assets` le publie aussi depuis la carte).

🔴 **UN ÉCART DE VÉRITÉ EST DÉCLARÉ, ⛔ PAS CORRIGÉ** : le commentaire de
`partitions.csv` annonce que *« la marge accueille les 3 déclinaisons de
dn3-3 »*. **C'EST FAUX**, et le recompte ci-dessus le prouve. Il n'est **pas**
corrigé ici parce qu'AC1.1 exige que le fichier n'apparaisse **pas** au
`git diff --stat` — les deux exigences sont incompatibles, et c'est la preuve
mécanique qui l'emporte. **Le verbatim est en §24.6, pour `dn4-16`.**

## 24.2 ✅ LE CHEMIN D'AMBIENT — CE QU'IL RECONSTRUIT (RIEN) ET CE QU'IL LAISSE

`build_scene()` coûte **307-322 ms verrou tenu** (mesuré `dn3-1`), sur un budget
de transition **déjà non coché** (337,6 ms au `nav ab`, **361,8 ms AU DOIGT**,
`dn4-4`, décision owner du 2026-08-24). Un Ambient bâti sur les setters visuels
du fichier aurait donné un réveil à ~350 ms **par construction**.

| Levier | Chemin retenu | Reconstruit ? |
|---|---|---|
| Couleur des VALEURS | `dn_val_regime_couleur()` rendue **consciente du mode** — relue à chaque `dn_widget_maj()` | **non** |
| Les six cases | `case_appliquer()`, **extraite de `case_poser()` sans changement de comportement** | **non** |
| Voile | objets **RETENUS** (`s_voiles[]`), on n'écrit que `bg_opa` | **non** |
| Accents (icône + jauge) | `dn_widget_repeindre_accents()` sur pointeurs retenus | **non** |
| Rétroéclairage | `dn_display_backlight_pct()` — LEDC, **avant** toute écriture LVGL | **non** |
| Page de détail / MENU ouverts | `detail_reparametrer()` / `menu_reparametrer()`, leurs chemins normaux | **non** |

⇒ **AUCUN objet n'est détruit ni créé sur une bascule de veille.** C'est ce qui
fait que **t₂ n'est PAS `t₁ + 320 ms`** — mais ⚠️ **t₁ et t₂ RESTENT À MESURER
SUR LA CARTE** (§24.7). ⛔ Rien ici n'autorise à annoncer un chiffre.

⚠️ **CE QUE ÇA NE COUVRE PAS, ET C'EST ÉCRIT** : les aplats des cases
(`dn_widget_set_opa`) ne sont **pas** touchés en Ambient — leur setter
reconstruit. Le voile et le rétroéclairage portent l'assombrissement.

## 24.3 ✅ LES TROIS GRIS, ET LE PIÈGE QU'ILS ÉVITENT

`W_COL_ABSENTE = 0x9a9a9a` était **tentant et gratuit** pour les valeurs
d'Ambient. S'en servir aurait recréé **exactement** le défaut du 2026-08-18
(SIMULÉE indiscernable d'ABSENTE), qui avait demandé une revue de code pour être
vu. Ambient a donc **ses propres trois tons**, et la gate hôte vérifie qu'ils
sont **distincts et séparés en luminance dans les DEUX modes** :

| Régime | Actif | luminance | Ambient | luminance |
|---|---|---:|---|---:|
| RÉELLE | `0xffffff` | 255 | `0xc8c8c8` | 200 |
| SIMULÉE | `0xffb020` | 183 | `0x9a8a5a` | 137 |
| ABSENTE | `0x9a9a9a` | 154 | `0x5a5a5a` | 90 |

Écart minimal : **29** en Actif, **47** en Ambient (critère de gate : ≥ 24/255).

## 24.4 🔴 LES ACCENTS — UN MOTIF FAUX CORRIGÉ **PAR LA MESURE, AVANT PUBLICATION**

Le commentaire initial de `dn_widget_desaturer()` affirmait qu'une **moyenne**
des trois canaux confondrait le cyan de `GPU` et le rose de `RAM`, et que
**BT.601** les séparait. **C'ÉTAIT L'INVERSE.** Mesuré le 2026-08-25 :

| Mapping | Gris distincts sur 7 | Paire confondue |
|---|---:|---|
| **BT.601** (77/150/29) | **6** | `GPU` cyan `22d3ee` ↔ `RAM` rose `f472b6`, **tous deux 160** |
| Moyenne des 3 canaux | **6** | `CPU` violet `a855f7` ↔ humidité `AMBIANCE` `35d6e8`, **tous deux 166** |

⇒ **Les deux mappings perdent exactement une paire**, simplement pas la même.
Le vrai motif de BT.601 est **perceptuel** (le vert pèse 59 %, le bleu 11 %), ⛔
pas « la moyenne confondrait ».

🔴 **CONSÉQUENCE SUR LE PRODUIT, ET ELLE EST TRANCHÉE PAR LA MESURE** : le défaut
de `veille accents` passe de **100 % à 95 %**. À 95 %, l'écart chromatique minimal
des **sept** accents remonte à **7/255** — invisible à l'œil, donc toujours « un
état nuance de gris » au sens de la demande owner — et **les six identités
arbitrées en `dn4-4`/`dn4-13` survivent à la veille**. `veille accents 100` reste
disponible, et la console **DIT quelle paire il confond, calculé à l'exécution**.

⚠️ **`veille accents` est un A/B à chaud** : c'est AC9.4 qui tranche à l'œil.

## 24.5 ✅ CE QUE LA GATE HÔTE PROUVE — 178 CONTRÔLES, SANS CARTE NI TOUR

⚠️ **CHIFFRE À JOUR AU 2026-08-28** : 119 → **139** (bloc « 4 bis »,
§24.12.4, +2 mutants) → **162** (bloc « 4 ter », la 6ᵉ piste W2,
§24.13.1, +2 mutants) → **167** (bloc « 4 quater », l'étiquette de
`w2 reset`, §24.15.3, **+1 mutant TEXTUEL**) → **178 OK / 0 KO** au
**2026-08-28**, après la **REVUE DE CODE 3 COUCHES** (§24.16). Le nombre de
mutants passe de **quatre** à **onze**.

🔴 **CE QUE LES ONZE DERNIERS CONTRÔLES ÉPINGLENT, ET POURQUOI ILS COMPTENT** —
la revue a trouvé **trois contrôles qui épinglaient VERT du code FAUX** :
· le dénominateur W2 était gaté sur `n - 1 - ruptures`, qui retranche **une
  rupture de trop** dès qu'on lit hors Ambient (le cas normal) ⇒ le critère est
  désormais `n - ÉPISODES`, avec `amorce` lu **dans la même section critique**
  que les compteurs, et un **mutant textuel** qui remet l'ancienne formule et la
  fait rougir ;
· le mutant de la condition d'observation visait `s_secondes_vues * 1000u`, qui
  **débordait un `uint32_t` à ~49,7 jours** — sur un module dont le critère n°1
  est « une semaine H24 » ;
· 🎯 et le diagnostic d'appui fantôme lui-même était **structurellement aveugle
  au seul cas qui l'atteint** : sa garde était « aucune bascule DEPUIS LE BOOT »,
  or le verrou de consommation ne se pose **qu'en Ambient**, donc **après** au
  moins une bascule. Trois contrôles neufs le prouvent maintenant dans les deux
  sens — *« après un `veille now` + réveil, l'alerte SORT quand même »*,
  *« une bascule AUTOMATIQUE l'éteint bien »* (⛔ pas de cri sur un module sain)
  et *« RÉVEIL puis doigt collé ⇒ l'alerte SORT, fenêtre ré-armée »*.
⚠️ **Les 167 d'avant n'étaient donc pas faux : ils étaient VRAIS SUR UN CODE QUI
   L'ÉTAIT MOINS.** Une gate ne relit pas ce qu'elle épingle.

🔴 **LE BLOC « 4 quater » GATE UNE ÉTIQUETTE, ⛔ PAS UNE LOGIQUE** — et c'est
délibéré : le défaut de §24.15.3 était **une phrase imprimée qui mentait sur un
instrument juste**. La prédicate **LIT la ligne produite** ; ⛔ elle ne rejoue
pas le `memset` du firmware. La même prédicate sert au produit et au mutant.
🔴 **ET LE BLOC « 4 ter » COMBLE UN TROU PLUS ANCIEN QUE `dn3-3` : W2 n'avait
JAMAIS été gaté** — aucun `verif_*.py` du dépôt ne le touchait.

`tools/verif_veille_dn33.py`. ⛔ **Elle ne relit pas du source** : elle **COMPILE
`dn_veille.c` en entier et l'APPELLE**, et elle **EXTRAIT VERBATIM**
`dn_widget_desaturer()` de `dn_widget.c` pour la compiler et l'appeler aussi.

**Les quatre mutants, COMPILÉS ET EXÉCUTÉS**, chacun vu rougir :

| Mutation | Défaut qu'elle fait revenir |
|---|---|
| `>=` → `>` dans la garde de bascule | le cran 1 min basculerait à **61 s** au lieu de 60 — la fenêtre publiée serait fausse d'une seconde entière |
| `v == 0 \|\| v == 1` → `if (1)` | un `42` corrompu en NVS passerait pour un « ON » **délibéré**, **sans un avertissement** |
| suppression de la condition d'observation | l'alerte d'appui fantôme **crierait au loup dès le 1ᵉʳ tick**, c'est-à-dire quand tout est normal |
| — (témoin) | fonction `dn_widget_desaturer` introuvable ⇒ **la gate échoue bruyamment**, ⛔ elle ne devient pas verte sur du vide |

Ce qu'elle établit aussi : les quatre crans **1/3/5/10** et le **refus** de `7`
(⛔ pas d'écrêtage) · les défauts d'usine **ON / 3 min** · l'aller-retour NVS et
les **deux** replis journalisés · l'annulation de bascule **retranchée** du
compteur · `veille reset` qui **ne touche ni les réglages ni le mode** ·
`partitions.csv` **inchangé** · les étiquettes réparées (AC5.4, AC10.1) ·
`lv_async_call` sur la bascule · le contact **consommé et latché**, chemin
d'erreur I²C compris · les **trois** racines exigées en modèle `SCREENS`.

🔴 **+7 CONTRÔLES AJOUTÉS *PENDANT* LA SÉANCE**, et c'est le point : les deux
défauts de §24.7.9 ont été trouvés **sur la carte**, pas par la gate. Chacun est
désormais épinglé — le rebase de réveil **et sa place dans la fonction** (avant
`dn_veille_reveiller()`, il repousserait une bascule légitime sur une course),
l'écart **latché** et son témoin qui prouve que le tick écrase bien
`inactivite_ms` **sans toucher au latch**.
⚠️ **Ce témoin-là a ROUGI à sa première écriture, et pour la bonne raison** : il
tickait au-dessus du délai, donc le tick **re-basculait** et le témoin mesurait
sa propre bascule. Corrigé à 30 000 ms. Une gate qu'on n'a pas vue rougir pour
une raison qu'on comprend ne prouve rien.

🔴 **AC6.5 — AMENDÉ EN REVUE DE CODE LE 2026-08-28. ⛔ CE QUI SUIT N'EST PAS
EFFACÉ : LE CONSTAT ÉTAIT JUSTE, LA CONCLUSION ÉTAIT FAUSSE.**

✅ **CE QUI RESTE VRAI, ET QUI A ÉTÉ RÉELLEMENT VÉRIFIÉ DANS LE `.c` PRODUIT.**
`codepoints_du_c()` sur `dn_font_14.c` et `dn_font_28.c` : `LV_SYMBOL_OK`
(`0xF00C`), `LV_SYMBOL_LEFT` (`0xF053`) et `LV_SYMBOL_SETTINGS` (`0xF013`) sont
**présents dans les deux**. ⚠️ **Témoin négatif** : `0xF863` (`fan`) est
**ABSENT** — c'est le glyphe qu'un test de bornes avait cru présent en `dn3-1`.
⇒ **Aucun glyphe n'a été ajouté aux DEUX POLICES EXISTANTES**, et les glyphes du
MENU n'ont donc rien coûté. **C'est ça que la vérification a établi.**

🔴 ~~⇒ Aucune police n'est régénérée.~~ **CETTE PHRASE EST FAUSSE, ET ELLE A ÉTÉ
PUBLIÉE DANS UNE SECTION DÉCLARÉE CLOSE.** `dn3-3` a **CRÉÉ DEUX POLICES** :

| Fichier | Taille | Rôle |
|---|---|---|
| `main/fonts/dn_font_33.c` | **134 397 o** | police de veille **33 px** (`veille unite on`) |
| `main/fonts/dn_font_56.c` | **317 998 o** | police de veille **56 px** (`veille unite off`) |

Elles sont **liées** (`main/CMakeLists.txt`) et **consommées** par `dn_ui.c`
(`return s_amb_unite ? &dn_font_33 : &dn_font_56;`), avec `fonts/dn_font.h`
(+26 l.) et `tools/gen_font_dn.py` (120 l. modifiées, plage réduite
`0x20-0x7F,0xB0` ⇒ **97 glyphes au lieu de 261**).

🎯 **DELTA RÉEL : `+76 352 o`** — ⛔ pas `0`.

⇒ **AC6.5 FERME AVEC ÉCART DÉCLARÉ, décision owner du 2026-08-28.** Le motif
n'est **pas** un oubli de dev : c'est **O-2** — *« nombre + unité sur une
ligne »*, choix éclairé de l'owner, qui impose la police de veille à 33 px.
Une AC réfutée par une décision owner **postérieure** se ferme par écart déclaré,
⛔ elle ne se coche pas.

⚠️ **DEUX CHOSES À RETENIR DE CET INCIDENT, ET ELLES DÉPASSENT `dn3-3`** :
1. 🔴 **LE CHIFFRE N'EXISTAIT QU'À UN SEUL ENDROIT DU DÉPÔT.** `grep "76 352"`
   sur `hardware/` et `README.md` rendait **0 occurrence** — il ne vivait que
   dans le Change Log de la story. ⇒ **un coût publié une seule fois n'est pas
   publié.**
2. 🎯 **LA GATE CONNAISSAIT LES DEUX POLICES PENDANT QUE §24.5 NIAIT LEUR
   EXISTENCE.** `tools/verif_veille_dn33.py` **ouvre** `dn_font_33.c` et
   `dn_font_56.c` pour vérifier leur plage réduite. Les **167 OK** épinglaient
   donc la présence de fichiers dont cette sous-section disait qu'ils
   n'existaient pas. ⇒ **une gate verte ne relit pas le dossier**, et c'est
   précisément pour ça qu'AC10.4 exige le `grep` sur tout l'arbre — **y compris
   contre son propre livrable.** Le Change Log de `dn3-3` revendique avoir
   amendé **trois** affirmations devenues fausses de §24 **sans voir celle-ci,
   qui vit dans la même §24.5.**

## 24.6 📋 LE VERBATIM POUR `dn4-16` — CE QUE CETTE STORY PÉRIME

⛔ **`dn3-3` ne réécrit PAS le ledger.** Elle fournit le texte.

**(1) Les trois entrées « palette Actif → dn3-3 » sont PÉRIMÉES** :
`deferred-work.md:79-83`, `:598-604`, `:1701-1705`, plus l'addendum §1 (*« teinte
exacte tranchée en dn3-3 »*).
**Raison** : `dn4-4` a fait une 2ᵉ passe de palette le 2026-08-24 **par décision
owner explicite**, puis `dn4-13` l'a corrigée à l'œil le 2026-08-25. Les six
couleurs sont **posées, distinctes et motivées** dans `dn_ui.c`. `dn3-3` n'a
inventé **qu'une** palette : celle d'**Ambient**.

**(2) `deferred-work.md:1620-1626` sous-compte le conflit d'assets** : il écrit
« trois déclinaisons ne tiennent pas ». **Deux ne tiennent déjà pas** (1 228 832 o
contre 1 048 576). Voir §24.1.

**(3) 🆕 ENTRÉE À CRÉER — le commentaire de `partitions.csv` MENT** : il annonce
*« la marge accueille les 3 déclinaisons de dn3-3 »*. Faux, prouvé en §24.1. ⛔ Non
corrigé par `dn3-3` : AC1.1 exige que ce fichier n'apparaisse pas au
`git diff --stat`, et une preuve mécanique l'emporte sur un commentaire.

**(4) Les deux gates « MENU = zone morte / 0 tap » sont PÉRIMÉES À MOITIÉ** —
`dn3-2`/AC5-AC6 (16 appuis) et `dn4-6` (ledger `:576`, 3 appuis). Les cinq sites
de `hardware/` qui les publient portent désormais leur marque de péremption. Ce
qui reste vrai et re-tiré comme **témoin négatif** : **la barre du haut est une
zone morte**.

**(5) ✅ FERMÉE — `deferred-work.md:1257-1261`** (*« le tap de réveil Ambient→Actif
est-il CONSOMMÉ, ou ouvre-t-il aussi le détail ? »*, ouverte depuis `dn1-4`).
**Tranchée par l'owner le 2026-08-25 (D-7) : CONSOMMÉ.** Implémentée dans
`dn_touch.c` (verrou de consommation latché jusqu'au relâchement, chemin d'erreur
I²C compris) et vérifiée par la gate.

## 24.7 ✅ LA SÉANCE CARTE — PARTIE SANS ŒIL, 2026-08-25, firmware `e0af1c6`

⚠️ **CHAQUE CHIFFRE CI-DESSOUS PORTE SON SHA, LU AU BANDEAU `App version`**, et
`git status --porcelain` était **vide** avant chaque flash. La séance a traversé
trois firmwares — `bcf1d38`, puis `c204f4a`, puis `e0af1c6` — **et les deux
reflashs sont eux-mêmes des résultats** : voir §24.7.9.

### 24.7.1 ✅ AC1.3 — LE LAYOUT NE BOUGE PAS D'UN PIXEL, ET C'EST CHIFFRÉ

| Mode | Signature FNV-1a des 28 nombres |
|---|---|
| `ACTIF` | **`0xE6887D29`** |
| `AMBIENT` (après `veille now`) | **`0xE6887D29`** |

Les six cases rendent les mêmes quatre nombres (`CPU` 10,70,225,163 · `GPU`
245,70 · `RAM` 10,243 · `RÉSEAU` 245,243 · `DISQUE` 10,416 · `AMBIANCE` 245,416)
et le triplet de bandes est identique (**barre 60 · menu 51 · grille 529 ·
case 163** — la géométrie D12). ⛔ Ce n'est pas un constat à l'œil.

### 24.7.2 ✅ AC3.3 — LE DÉLAI MESURÉ EST CELUI ANNONCÉ, TROIS FOIS

Cran **1 min**, écart **dernier contact → bascule**, latché par le tick qui a
basculé :

| # | Écart | Δ au délai | Verdict |
|---|---:|---:|---|
| 1 | **60 520 ms** | +520 ms | ✅ dans [60 000 ; 61 000] |
| 2 | **60 635 ms** | +635 ms | ✅ |
| 3 | **60 275 ms** | +275 ms | ✅ |

Dispersion **360 ms**, cohérente avec un tick 1 Hz. ⚠️ **Le seuil est APPLIQUÉ
PAR L'INSTRUMENT**, pas laissé au lecteur : `veille` imprime le verdict ✅/🔴
ligne par ligne.

### 24.7.3 ✅ AC3.4 — LA VEILLE DÉSARMÉE NE TOMBE JAMAIS

Cran armé à **1 min**, `veille off`, **300 secondes OBSERVÉES** :
inactivité montée à **390 370 ms — soit 6,5× le délai** — **0 bascule**, mode
resté `ACTIF`, `ecarts contact->bascule : AUCUN ECHANTILLON`.
⛔ « Aucun échantillon », pas « 0 ms ».

### 24.7.4 ✅ AC2.2 — LES DONNÉES RESTENT VIVANTES EN VEILLE

Série `AMBIANCE T`, avant l'entrée en veille puis 60 s plus tard, **module resté
en `AMBIENT` tout du long** :

| | écrits | réels | trous | couverture |
|---|---:|---:|---:|---:|
| à l'entrée | 16 | 10 | 6 | 18 s |
| +60 s | **76** | **70** | 6 | **78 s** |
| **Δ** | **+60** | **+60** | **0** | **+60 s** |

⇒ **60 points ± 0**, tous **RÉELS**, **aucun trou creusé**. Le critère demandait
60 ± 1. `dn_hist` ne s'arrête pas en veille.

### 24.7.5 ✅ AC2.5 / AC2.6 — LE 4ᵉ ÉCRIVAIN DE LEDC, AVEC SON TÉMOIN

`bl auto on` **puis** entrée en veille ⇒ la console le DIT **deux fois** :

```
W dn_env: retroeclairage auto DESARME par « veille » — deux ecrivains sur LEDC
          ne s'arbitrent pas tout seuls...
W dn_ui : l'asservissement `bl auto` etait ARME : la VEILLE vient de le DESARMER.
          ... `bl auto on` pour le rearmer.
```

⚠️ Le témoin est **NÉGATIF au sens fort** : `bl auto` est `false` par défaut,
donc **le défaut ne révèle pas le bug**. Il fallait l'armer pour le voir.

### 24.7.6 ✅ AC8.5 — `ui off` DE 75 s NE FABRIQUE PAS UNE FAUSSE BASCULE

`ui off` pendant **75 s** (le délai vaut 60 s), puis `ui on` :

- le rebase est **fait, COMPTÉ (`rebases : 1`) et DIT** — le message nomme la
  cause et la conséquence ;
- **mode `ACTIF`**, **`bascules : 0`** ;
- inactivité repartie à **2 440 ms**.

⚠️ **Sans le rebase, l'inactivité aurait valu ~78 000 ms** contre 60 000 de
délai : la bascule serait tombée **au premier tick**, et ça se serait lu comme
un bug de bascule.

### 24.7.7 ✅ AC5.2 / AC7.3 — LA 3ᵉ VUE ET LA PERSISTANCE

- `nav menu` puis `nav back` jouent dans **les DEUX modèles** ; `nav` publie
  `vue : menu · modele « screens »` **et** `vue : menu · modele « rebuild »`.
- **`5 min` + `ON`** réglés à la console, **reboot**, relus au bandeau :
  `dn_veille: veille ON · delai 5 min (300000 ms)`. ⚠️ Le défaut d'usine est
  **3 min** : c'est donc bien la NVS qui parle, ⛔ pas le défaut.

### 24.7.8 🎯 T5 — LE TAS LVGL, ET LE CRITÈRE DE T5 VALIDÉ DE FAÇON SPECTACULAIRE

Mesuré sur **DEUX firmwares** — la baseline `1f7a4bb` (pré-`dn3-3`) a été
reflashée exprès, parce qu'un delta sans son « avant » n'est pas un delta :

| Firmware | Modèle | utilisé | **plus gros bloc libre** | fragmentation |
|---|---|---:|---:|---:|
| `1f7a4bb` | `screens` (2 racines) | 21 440 o (35 %) | **39 544 o** | 3 % |
| `1f7a4bb` | `rebuild` (1 écran) | 17 816 o (29 %) | **39 544 o** | 12 % |
| `e0af1c6` | `screens` (3 racines) | 28 088 o (46 %) | **31 992 o** | 4 % |
| `e0af1c6` | `rebuild` (1 écran) | 17 860 o (29 %) | **31 992 o** | 29 % |

**Ce que `dn3-3` coûte, ATTRIBUÉ :** **+6 648 o** de tas utilisé en `screens`
(la 3ᵉ racine MENU) et **−7 552 o de plus gros bloc libre** (−19,1 %).
Il reste **31 992 o**, soit ~**4,8×** le coût d'une racine MENU.

🔴 **ET VOICI POURQUOI T5 EXIGEAIT LE PLUS GROS BLOC ET PAS LE POURCENTAGE.**
Sur `e0af1c6`, passer de `screens` à `rebuild` fait bondir la fragmentation
**de 4 % à 29 % — un facteur 7 — pendant que le plus gros bloc libre ne bouge
PAS D'UN OCTET** (31 992 dans les deux cas). Le pourcentage aurait crié à la
régression là où la capacité réelle à allouer est strictement identique.

⚠️ **ET IL DIT AUTRE CHOSE, QU'ON N'ALLAIT PAS CHERCHER** : le plus gros bloc est
le MÊME dans les deux modèles, **y compris en `rebuild` où aucune racine MENU ne
vit**. Il est donc fixé par le **PIC D'ALLOCATION AU BOOT** — `build_scene()`
tourne en `screens` (le défaut) et crée les trois racines — ⛔ pas par le modèle
courant. Libérer les racines ne rend pas le bloc.

### 24.7.9 🔴 DEUX DÉFAUTS TROUVÉS **PAR LA SÉANCE**, ET C'EST ELLE QUI LES A TROUVÉS

**(1) `veille wake` s'annulait tout seul** (`bcf1d38` → corrigé en `c204f4a`).
La console imprimait « Actif. » et le module **retombait en Ambient au tick
suivant**. Cause : l'horloge d'inactivité de LVGL ne se remet à zéro que sur un
`PRESSED` (`lv_indev.c:266-268`) ; un réveil venu de la console ne passe pas par
l'indev, donc la garde retrouvait aussitôt `inactivite >= delai`.
⇒ **C'était EXACTEMENT le défaut qu'AC4.5 ferme pour `nav`, et il n'avait été
fermé QUE pour `nav`.** Le rebase vit désormais dans le chemin de réveil, donc
sur **toutes** les origines.
⚠️ **C'était aussi un bloquant de mesure** : sans t₀ franc, les trois relevés
d'AC3.3 n'étaient pas tirables au clavier.

**(2) AC3.3 n'avait AUCUN INSTRUMENT** (`c204f4a` → `e0af1c6`).
Le critère demande la fenêtre **[délai ; délai + 1 s]**. ⛔ Aucun sondage depuis
l'hôte ne peut la trancher : la latence série et le pas d'interrogation ajoutent
leur **propre seconde** à une fenêtre qui n'en fait qu'une — on aurait publié la
dispersion de l'**instrument** en croyant publier celle du produit. Et
`s_inactivite_ms` ne pouvait pas servir : le tick continue en Ambient et
l'**écrase** à la seconde suivante.
⇒ Un anneau de quatre écarts **latchés au moment exact où la garde cède**. Une
bascule **annulée** retire son échantillon.

### 24.7.10 ✅ CE QUE LES INSTRUMENTS DISENT QUAND ILS N'ONT RIEN

- `veille lat` sans réveil au doigt : **« aucun réveil AU DOIGT ⇒ RIEN À
  PUBLIER »**, ⛔ pas « 0 µs ».
- `ecarts contact->bascule` sans bascule : **« AUCUN ECHANTILLON »**, ⛔ pas 0 ms.
- `dn_ui_veille_compteurs()` sur verrou non pris rendrait **« ⛔ PAS MESURE »** —
  non déclenché en séance, la garde n'est donc **pas éprouvée sur la carte**.

### 24.7.11 ⓘ LE COÛT DE LA PERSISTANCE, MESURÉ

Deux écritures NVS chronométrées : **1 391 µs** et **2 904 µs**.
À comparer à **26,7 ms** de période de trame (37,40 Hz) : le pire des deux vaut
**11 % d'une trame**. ⚠️ **Mesuré depuis la tâche REPL.** Au tap MENU la même
écriture est payée **dans la tâche LVGL** — le chiffre devrait être du même
ordre, mais **ce cas-là n'a pas été tiré** : il demande un doigt.

### 24.7.12 ✅ LA COLLISION D'ACCENTS, CONFIRMÉE SUR LA CARTE

`veille accents 100` sur la dalle :

```
🔴 A 100 %, DES ACCENTS SE CONFONDENT :
   « GPU » et « RAM » rendent tous deux A0A0A0
```

`veille accents 95` : **« ✅ a 95 %, les 6 accents de case restent DISTINCTS deux
a deux. »** ⇒ Le constat de §24.4, calculé par le firmware lui-même, sur les
couleurs relues des descripteurs. C'est ce qui a fait passer le défaut à 95.

## 24.8 ✅ AC4 — LES DEUX LATENCES DE RÉVEIL, MESURÉES AU DOIGT

Campagne du 2026-08-25, firmware `dfa8204`, **10 réveils AU DOIGT en 169 s**.
⚠️ Le geste est à l'owner, la cadence à l'agent : le script rebascule en Ambient
dès qu'un réveil est constaté. ⛔ **Les deux latences sont chronométrées DANS le
firmware** — un chronométrage depuis l'hôte aurait ajouté sa latence série à des
valeurs de l'ordre de la centaine de microsecondes.

| | min | **médiane** | max | cible |
|---|---:|---:|---:|---:|
| **t₁** — contact → rétroéclairage remonté | 86 µs | **107 µs** | 178 µs | **< 50 ms** ✅ |
| **t₂** — contact → palette Actif posée | 25 213 µs | **25 454 µs** | 25 804 µs | budgétée |

🎯 **t₁ médian = 0,107 ms, soit 467× SOUS la cible** — et même le pire cas
(178 µs) reste 280× dessous. C'est le bénéfice direct du réveil EN DEUX TEMPS :
le rétroéclairage remonte avant toute écriture LVGL.

🎯 **t₂ médian = 25,5 ms, dispersion 591 µs.** Il est **SOUS une période de
trame** (26,737 ms) : le repeint lui-même ne coûte presque rien, c'est l'attente
de synchro qui domine. ⇒ **À comparer aux 307-322 ms qu'aurait coûté une
reconstruction de scène : le chemin sans rebuild paie 12× moins.**

⛔ **CES DEUX CHIFFRES NE SE MÉLANGENT NI ENTRE EUX NI AVEC LE CRITÈRE BRIEF.**
Le « < 300 ms » du brief porte sur la NAVIGATION et il est DÉJÀ non coché
(337,6 ms au `nav ab`, 361,8 ms au doigt, `dn4-4`). Trois chiffres, trois
questions.

⚠️ **CE QUE t₁ N'INCLUT PAS, ET C'EST DIT PAR L'INSTRUMENT LUI-MÊME** : l'origine
du chronomètre est l'instant où le `read_cb` VOIT le front, ⛔ pas l'instant du
contact physique. Le trajet GT911 → IRQ → réveil de la tâche LVGL → transaction
I²C est **en amont et non instrumenté**.

### ✅ D-7 — LE TAP DE RÉVEIL EST BIEN CONSOMMÉ, ET C'EST MESURÉ

| compteur | valeur |
|---|---:|
| contacts **CONSOMMÉS** en Ambient | **12** |
| réveils produits | **10** |
| taps attribués à une **zone** | **2** |
| taps sur **MENU** | **0** |

⇒ Si les taps de réveil fuyaient vers les zones, on en compterait une douzaine.
**Aucun n'a ouvert de page.** Les 2 taps de zone ont eu lieu **après** un réveil,
donc en mode Actif, et le dernier a touché `RETOUR` — c'est de la navigation
normale.
⚠️ **12 consommations pour 10 réveils** : deux contacts sont tombés sur la course
« déjà réveillé ». Le code la prévoit (`dn_veille_reveiller()` rend `false`) et
compte quand même la consommation — c'est correct : le contact **a** été
consommé, il n'a simplement pas produit de réveil.

### ⚠️ ÉCART DÉCLARÉ — n = 10, ET AC4.3 EN DEMANDE 20

Décision owner du 2026-08-25 : *« 20 reveils c'est beaucoup mais ok pour une
10aines »*. ⛔ **AC4.3 n'est donc PAS satisfait à la lettre.** Ce qui est publié
ci-dessus vaut pour **n = 10**, et la dispersion observée (t₁ de 86 à 178 µs,
t₂ de 25,2 à 25,8 ms) est assez serrée pour que dix échantillons soient
informatifs — mais ⛔ ce n'est pas la même chose que vingt, et personne ne doit
lire ce tableau comme si ça l'était.

## 24.9 🔴 FAIT MATÉRIEL — **AUCUN GRIS N'EST NEUTRE SUR CETTE DALLE**

⚠️ **CE FAIT DÉPASSE `dn3-3`.** Il vaut pour toute couleur posée sur ce module,
et il a coûté quatre allers-retours avec l'œil de l'owner avant d'être nommé.

### Le symptôme

Constat owner du 2026-08-25, sur le premier rendu d'Ambient :
*« les 6 cases sont pleines en VERT sur fond noir »* — pendant que l'instrument
lisait `opa 255 · couleur 1E1E1E` sur la racine de chaque case, **et disait
vrai**.

### La bissection, en cinq témoins

| # | Test | Résultat | Ce qu'il élimine |
|---|---|---|---|
| 1 | `veille fond` | voile opa 255 noir, aplat 255, écran actif = la bonne racine, voile **au-dessus** de l'image | l'arbre LVGL est correct |
| 2 | `widget fond off` | image **retirée** de l'arbre ⇒ **toujours vert** | le Living PCB n'est pas la source |
| 3 | `ui off` + `scene black` | noir plein écrit **directement dans le framebuffer** ⇒ **NOIR à l'œil** | la chaîne framebuffer → dalle est **saine** |
| 4 | `veille case FF0000` | les cases deviennent **ROUGES** | le style **atteint** le rendu ⇒ `1E1E1E` était bien posé |
| 5 | `bl 100` | **toujours vert** à pleine lumière | ce n'est pas un effet de bas rétroéclairage |

### La cause, et elle est intrinsèque au RGB565

Le canal **vert porte 6 bits**, le rouge et le bleu **5**. Un gris `R = G = B` ne
survit donc pas à la quantification :

```
0x1E1E1E -> r5=3  g6=7   -> R 24  G 28  B 24    ecart vert  +4
0x202020 -> r5=4  g6=8   -> R 33  G 32  B 33    ecart vert  -1
0x000000 ->                 R  0  G  0  B  0    ecart vert   0
0xFFFFFF ->                 R255  G255  B255    ecart vert   0
```

✅ **CONFIRMÉ HORS DE TOUT CODE D'INTERFACE** : `scene gray`, écrite directement
dans le framebuffer, rend — constat owner — *« vert vers les tons sombres,
violet vers le milieu et les tons clairs »*. C'est exactement ce que `dn_mire`
annonce déjà comme **normal** : *« le vert avance deux fois plus vite dans la
rampe, donc il prend puis rend l'avance à chaque pas »*.

### 🔴 CE QUI A ÉTÉ APPRIS, ET QUI SE PAIE SI ON L'OUBLIE

1. **Le critère `|G8 − R8| ≤ 1` NE SUFFIT PAS**, et il a été essayé :
   `0x202020` le satisfait, et l'œil l'a quand même rejeté (*« vert plus
   foncé »*). ⛔ Ne pas relâcher la gate vers ce critère-là.
2. **Les seules valeurs vraiment neutres sont les extrémités** : le noir et le
   blanc. ⇒ Un **aplat plein** d'Ambient se prend dans ces deux-là.
3. **Une surface pleine teinte, un trait fin beaucoup moins.** Les gris de
   TEXTE (`SIMULÉE` `A4A4A4`, `ABSENTE` `585858`) tirent aussi — c'est **assumé
   et déclaré** : les ramener au blanc rendrait les trois régimes
   indiscernables, c'est-à-dire le défaut du 2026-08-18.
4. ⚠️ **AUCUN INSTRUMENT LOGICIEL N'AURAIT TROUVÉ ÇA.** Le build était vert, la
   gate hôte à 112 contrôles était verte, et les quatre instruments de l'écran
   disaient tous la vérité. **Il a fallu la dalle, et un test au ROUGE PUR pour
   écarter le rendu.**

⇒ **Valeur retenue pour l'aplat de case en Ambient : `0x000000`.** Constat owner
sur la dalle : *« enfin propre — blanc sur noir, lisible »*. La tuile est
délimitée par sa **bordure**, ⛔ pas par son remplissage.

## 24.10 🔴 L'INJECTION CONSOLE EST UN MAUVAIS TÉMOIN — MESURÉ, PAS SUPPOSÉ

Constat owner du 2026-08-25 pendant la veille : *« les valeurs pop juste et
entre 2 ya rien […] la courbe est pleine de pointillés »*.

⚠️ **LA PREMIÈRE RÉACTION AURAIT ÉTÉ D'ACCUSER L'AFFICHAGE. LES CHIFFRES DISENT
L'INVERSE.** Injection de 90 s, cinq métriques, cadence visée 1,32 poussée/s par
métrique (donc **plus rapide que l'agent réel**, mesuré à 1,0/s en `dn4-4`) :

| | valeur |
|---|---:|
| trames **émises** par l'injecteur | **595** |
| trames **valides** vues par la carte (`pc`) | **234** |
| **pertes de séquence** | **746** |
| rejets — tronquée / trop longue / checksum / version / format / bornes | **0 partout** |

🔴 **ZÉRO REJET** : les trames ne sont pas refusées, elles **n'arrivent pas**.
`net` et `disk` ont leur dernière trame acceptée à **seq 79 et 80** — elles ont
cessé de passer après ~12 s. L'injecteur **sature le REPL**.

✅ **ET LE TÉMOIN QUI TRANCHE EST DANS LE MÊME RELEVÉ** : `AMBIANCE`, la seule
source **réellement** vivante (le BME680, qui ne passe PAS par le lien série),
affiche **120 réels / 0 trou** sur 120 s — **pendant la veille** :

| série | réels | trous |
|---|---:|---:|
| `AMBIANCE T` / `AMBIANCE RH` | **120** | **0** |
| CPU | 76 | 44 |
| GPU | 38 | 82 |
| RAM | 42 | 78 |
| RÉSEAU | 18 | 102 |
| DISQUE | 19 | 101 |

⇒ **Les pointillés viennent du harnais, pas de l'affichage.** ⛔ Ne pas accuser
le code testé avant d'avoir éprouvé le harnais.

### ⚠️ ET SUR LE FOND : NON, IL NE FAUT PAS LISSER

`dn_hist` échantillonne l'état COURANT à 1 Hz, et **une source qui se tait creuse
un TROU** — délibérément. Le code le dit : *« la courbe mentirait sur la DURÉE,
pas sur la valeur : un mensonge plus difficile à voir »*. Lisser reviendrait à
dessiner des points que personne n'a publiés. `AMBIANCE` montre qu'une vraie
source n'en produit aucun.

⇒ **AC2.1 (le critère W2 chiffré) EXIGE L'AGENT RÉEL.** ⛔ L'injection console
ne peut pas s'y substituer, et ce relevé-ci en est la démonstration chiffrée.

## 24.11 ✅ LA SÉANCE DU 2026-08-25 (SOIR) — L'ŒIL ET LE DOIGT, firmware `6144064`

⚠️ **SHA LU AU BANDEAU `App version`**, `git status --porcelain` **vide** avant
le flash. **Tout chiffre de cette section porte `6144064`** — ⛔ pas `dfa8204`,
sur lequel §24.7 et §24.8 ont été tirées.

### 24.11.1 ✅ AC5.6 — LES DEUX GATES TACTILES, RE-TIRÉES ET SOLDÉES

| Phase | Geste owner | Relevé | Verdict |
|---|---|---|---|
| **positive** | **8 allers-retours** : appui bande MENU (`y = 624..639`) → `←` (`y = 22..56`) | `fin de trace : 21 appui(s), 16 tap(s) sur zone` · `nav` ⇒ **16 taps, dont 8 sur MENU** | ✅ le bandeau n'est plus une zone morte |
| **négative** | **5 appuis** barre du haut, **sur le dashboard** (`x = 122..221`, `y = 22..37`) | **0 tap attribué** | ✅ elle, elle reste morte |

🎯 **LA TRACE DONNE MIEUX QUE CE QUE LE PROTOCOLE DEMANDAIT.** Les appuis sur
`←` (`y = 22..56`) et ceux du témoin négatif (`y = 22..37`) tombent **dans la
même bande physique de la dalle**. Le même endroit est **vivant sur la vue MENU**
et **mort sur le dashboard**. C'est plus fort que deux fenêtres séparées : ça
exclut « on a rendu tout l'écran cliquable » **par la géométrie**, ⛔ pas
seulement par le compte.

⇒ **LES DEUX GATES QUE CETTE STORY PÉRIMAIT SONT RE-TIRÉES** : `dn3-2`/AC5-AC6
(*« 16 appuis, 0 tap »*) et le ledger `:576` (*« barre et MENU = zones mortes »*).
⛔ Elles ne décrivent plus le produit.

⚠️ **UN PIÈGE D'INSTRUMENT RENCONTRÉ, ET LE DÉPÔT A EU RAISON DE REFUSER.**
`touch trace 150000` a été **refusé** (« entre 1000 et 120000 ms ») : le premier
tir a donc mesuré **zéro**. ⚠️ `nav` et `touch` ont été relus **avant** de
relancer, et ils étaient bien restés à 0 — sans cette vérification, des appuis
égarés auraient pollué le compte. ⛔ Un refus chiffré vaut mieux qu'un écrêtage
silencieux : à 120 s tacites, la fenêtre aurait menti de 30 s.

### 24.11.2 ✅ AC6 / AC9.7 — LE MENU AU DOIGT, PAR CONSTAT OWNER

| AC | Question posée | Verbatim / verdict |
|---|---|---|
| **AC6.1-6.2** | les deux réglages sont-ils là ? | ✅ oui |
| **AC6.3** | l'état courant se lit-il **sans interaction** ? | ✅ *« les 2 réglages, état lisible »* — veille `ON` et le cran `10 min` ressortaient sans rien toucher |
| **AC9.7** | les crans se visent-ils au doigt (210 × 66) ? | ✅ *« les cibles sont confortables »* |
| **AC5.7** | le `←` est-il au même endroit qu'au détail ? | ✅ 8 allers-retours l'ont exercé (§24.11.1) — même rectangle `120 × 60` en `(10, 10)`, même glyphe |
| **cohérence** | le MENU suit-il un changement venu **d'ailleurs** ? | ✅ `veille off` tapé **au console** ⇒ *« crans grisés tout seuls »*, sans aucun geste |

🎯 **UN CONSTAT OWNER PLUS FORT QUE L'AC** : à `OFF`, *« y'a pas de cran actif »*.
AC6.3 demandait que le réglage courant soit visible ; le produit va plus loin en
ne laissant **rien faire semblant d'être sélectionné** quand le réglage est sans
objet. ⚠️ Corollaire à dire : **le délai en vigueur n'est pas lisible au MENU
quand la veille est OFF**. Il le redevient au `ON`, avec sa valeur persistée.

### 24.11.3 🔴 AC6.4 — LES CRANS SONT **DÉ-CLIQUABILISÉS**, ET C'EST CHIFFRÉ

⛔ Le constat à l'œil ne suffisait pas : *« rien ne bouge »* est aussi ce que
produit un tap **accepté puis sans effet visible**. Trois témoins ont été relus
après **3 appuis sur le cran `1 min`, veille `OFF`** :

| Témoin | Valeur | Ce qu'il exclut |
|---|---|---|
| délai | **300 000 ms** (5 min), inchangé | le réglage n'a pas bougé |
| écritures NVS | **1** — le seul `OFF` | aucun tap n'a écrit |
| 🎯 **taps de réglage MENU** | **1**, ⛔ pas 4 | les 3 appuis **n'ont même pas été enregistrés comme des taps de réglage** |

⇒ Le troisième est le seul qui distingue **dé-cliquabilisé** de **grisé mais
cliquable** — c'est-à-dire le no-op que W3 avait supprimé, réintroduit.

### 24.11.4 ✅ AC7.3 — LA MOITIÉ **MENU** DE LA PERSISTANCE, ENFIN TIRÉE

Seule la voie console était soldée (§24.7.7). Réglage posé **au doigt** :

| Étape | Relevé |
|---|---|
| posé au MENU | `veille ARMEE · delai 5 min (300000 ms)` · **2 taps de réglage** · 3 écritures NVS (dernière : **3 088 µs**) |
| après `reboot` (`App version: 6144064`) | `veille ARMEE · delai 5 min (300000 ms)` — **identique** |
| 🎯 preuve supplémentaire | *« aucune écriture NVS depuis le boot ou le dernier `veille reset` »* ⇒ les valeurs sont **RELUES** de la NVS, ⛔ pas ré-écrites au démarrage |

✅ **Le coût de l'écriture NVS PAR LA VOIE MENU est mesuré** — c'était un écart
déclaré de §24.7.11, qui ne chiffrait que la voie REPL : **2 364 à 3 088 µs**,
payés **dans la tâche LVGL**, cache flash coupé pendant ce temps.

### 24.11.5 🎯 AC4.3 — **20 RÉVEILS AU DOIGT** : L'ÉCART DÉCLARÉ EST FERMÉ

`tools/campagne_reveils.py 20 420` — **20 réveils en 104 s**, firmware `6144064`.

| Latence | min | **médiane** | max | Cible |
|---|---|---|---|---|
| **t₁** contact → rétroéclairage remonté | 90 µs | **110 µs** | **192 µs** | AC4.2 < 50 ms ⇒ **260× sous, AU PIRE CAS** |
| **t₂** contact → palette Actif complète | 24 795 µs | **25 244 µs** | 25 606 µs | budgetée — **12× moins** qu'une reconstruction (307-322 ms) |

✅ **AC4.3 est satisfait À LA LETTRE** (n ≥ 20). L'écart déclaré du 2026-08-25
(*« n = 10, le critère en demande 20 »*) **est fermé**.
⚠️ **CE QUE t₁ N'INCLUT TOUJOURS PAS** : l'origine du chronomètre est l'instant
où le `read_cb` **voit** le front, ⛔ pas le contact physique. Le trajet
GT911 → IRQ → réveil de la tâche LVGL → transaction I²C reste **hors mesure**.

🎯 **ET D-7 EST PROUVÉE BIEN MIEUX QU'AVANT** : **20 taps consommés pour
20 réveils** (1:1), **0 tap sur zone, 0 sur MENU, 0 transition**. ⛔ Aucun tap de
réveil n'a ouvert quoi que ce soit.
⚠️ Le précédent chiffre publié (« 12 consommés / 2 taps de zone ») était
**CUMULATIF** — voir §24.12.3. Celui-ci est relatif à son `veille reset`.
⚠️ `bascules 19 · réveils 20` **n'est pas un écart** : la carte était **déjà en
Ambient** quand le script a remis les compteurs à zéro, donc le 1ᵉʳ réveil n'a pas
de bascule comptée devant lui.

### 24.11.6 ✅ AC9.5 / AC9.6 — LES DEUX CONSTATS OWNER QUI RESTAIENT

| AC | Question | Verbatim owner | Conséquence |
|---|---|---|---|
| **AC9.6** | la veille ramène au dashboard depuis un détail : normal, ou perte ? | *« page veille dashboard direct c'est nickel »* | ✅ **la décision de conception d'AC3.5 est CONFIRMÉE PAR L'ŒIL**, ⛔ pas par un argument d'agent |
| **AC9.5** | le tap de réveil consommé se voit-il, ou se lit-il comme PERDU ? | *« ça a pris — c'est net »* | ✅ **aucun accusé visuel de réveil n'est nécessaire**. D-7 ne pose pas de problème de perception |

### 24.11.7 ✅ AC3.3 — RE-TIRÉE SUR `6144064`, ET ELLE A VALIDÉ LE CORRECTIF

Trois échantillons **jugeables**, cran `1 min`, réveils par `veille wake` :

```
#1  60 495 ms  (delai arme 60000 ms, +495 ms)  ✅ dans [delai ; delai+1 s]
#2  60 450 ms  (delai arme 60000 ms, +450 ms)  ✅ dans [delai ; delai+1 s]
#3  60 800 ms  (delai arme 60000 ms, +800 ms)  ✅ dans [delai ; delai+1 s]
#4  79 730 ms  (delai arme 60000 ms)           ⚪ NON JUGEABLE
```

Dispersion des trois : **350 ms**, tous dans `[60 000 ; 61 000]`.
Le `#4` est le **plus ancien** : au moment de l'armement, l'inactivité valait
déjà **79 s** — la bascule est tombée au premier tick. Elle est **correcte** ;
c'est la fenêtre qui ne s'y applique pas. Voir §24.12.2.

🎯 **LE TÉMOIN DU CORRECTIF, SUR LA CARTE** : le cran a ensuite été passé à
**10 min (600 000 ms)**, et les trois échantillons portent **toujours
`delai arme 60000 ms`** et **toujours ✅**.
⛔ **Sur `dfa8204`, les trois seraient passés 🔴 HORS d'un coup** — AC3.3 aurait
publié un rouge sur trois mesures justes.

### 24.11.8 ⚠️ UNE ANOMALIE OBSERVÉE, CHIFFRÉE, ET **NON REPRODUITE** — ⛔ AUCUNE CAUSE N'EST NOMMÉE

Pendant la première séance d'AC5.6 (firmware `dfa8204`), `dn_ui` a émis en
continu *« historique : 1 seconde(s) NON ÉCHANTILLONNÉE(S) … préemption longue »*
pendant **~280 s**, y compris **100 s après le dernier contact**.

| Condition | Trous | Instrument |
|---|---|---|
| boot frais, rien touché | **3 / 60 s** (5 %) | `--listen 60` |
| 14 transitions **console** (`nav menu`/`nav back`) | **0 / 60 s** | `--listen 60` |
| `touch trace` 30 s **sans doigt** | **0** | trace |
| **10 appuis au doigt, sans navigation** (barre morte) | **0 / 75 s** | `--listen 75` |
| ⚠️ **séance AC5.6 : doigt + navigation** | **~6 trous / 15 s (≈40 %)**, sur ~280 s | trace + `--listen` |

⇒ Un taux de 40 % signifie que le `lv_timer` à 1 Hz tirait réellement toutes les
**~1,7 s**. ⚠️ Et **la dalle allait bien pendant ce temps** : `vsync` à
**37,4-37,5 Hz**, soit le nominal — c'est la **tâche LVGL** qui était en retard,
⛔ pas le pipeline d'affichage.

⛔ **QUATRE CAUSES SONT ÉLIMINÉES PAR LA MESURE** (navigation seule, trace seule,
contact seul, uptime), **et aucune cause n'est établie**. Le régime est ensuite
retombé à **5 coupures sur ~1 100 s (0,4 %)** malgré doigt, navigation et cycles
de veille. ⛔ **Ne pas inventer de cause. Ne pas la déclarer résolue.**
⚠️ **CE QUI MANQUE POUR TRANCHER, ET QUI N'A PAS ÉTÉ RELEVÉ À TEMPS** : `touch`
(donc `erreurs I2C`) **pendant** l'épisode. Le dépôt sait que le bus se dégrade
à froid à 55,5 % d'erreurs GT911 **sans que le scan le voie** — si l'épisode se
reproduit, **lire `touch` AVANT toute autre chose**.
⚠️ **Ce que ça rend fragile** : §24.7.4 publie *« AC2.2 : +60 réels, 0 trou »*
sur `e0af1c6`. Ce chiffre reste vrai **pour son binaire et son régime**, mais il
ne dit rien de ce régime-là.

## 24.12 🔴 TROIS DÉFAUTS D'INSTRUMENT TROUVÉS PAR CETTE SÉANCE — ET TOUS TROIS SOLDAIENT UN AC

⚠️ Aucun n'était visible à la gate hôte (119 contrôles verts), et aucun n'était
visible à l'œil. **Ils se sont vus en LISANT une sortie de console qui se
contredisait elle-même.**

### 24.12.1 🔴 L'ANNEAU D'ÉCARTS ÉTAIT JUGÉ CONTRE LE DÉLAI **COURANT** (AC3.3)

`dn_console.c` comparait chaque écart latché à `c.delai_ms`, **le délai en
vigueur À LA LECTURE**, alors que `dn_veille.c` ne stockait **que l'écart**.

**Relevé sur la carte** : un écart de **60 400 ms**, latché alors que le cran
était à **1 min** — donc parfaitement dans `[60 000 ; 61 000]` — s'est affiché
**🔴 HORS de [delai ; delai+1 s]** dès que le cran est passé à 10 min entre la
bascule et le `veille`.

⇒ **Une étiquette qui ment, sur l'instrument même qui SOLDE AC3.3** — et le
dépôt tient qu'une étiquette fausse est un défaut au même titre qu'un chiffre
faux (`dn_widget.h`).
**Correctif** : chaque échantillon latche **le délai qui était armé**, et se juge
contre celui-là. Témoin sur la carte en §24.11.7.

### 24.12.2 🔴 CERTAINS ÉCHANTILLONS NE SE JUGENT PAS — ET ILS ÉTAIENT MARQUÉS ROUGE

Armer la veille — ou baisser le cran, ou faire `veille reset` — **alors que
l'inactivité dépasse déjà le délai** fait basculer au tout premier tick, qui
latche l'inactivité **VRAIE**. **Relevé : 178 270 ms pour un cran de 1 min**,
puis **79 730 ms** lors de la re-tire d'AC3.3.

La bascule est **CORRECTE** : la garde a cédé parce que la condition était
remplie. C'est la fenêtre `[délai ; délai+1 s]` qui **ne s'y applique pas**,
faute d'avoir jamais vu d'état **sous** le seuil.

⇒ **Correctif** : `s_garde_amorcee`. Un échantillon non amorcé est **ENREGISTRÉ
et DIT NON JUGEABLE**, avec son motif — même contrat que `veille lat`, qui exclut
les réveils console **en le disant**, ⛔ sans les jeter en silence.
⚠️ **Une annulation de bascule RESTAURE l'amorçage** : elle n'est pas un
ré-armement. Sans ça, la tentative suivante serait marquée non jugeable à tort.

### 24.12.3 🔴 `veille reset` LAISSAIT DEUX COMPTEURS CUMULATIFS (AC8.3)

AC8.3 dit en toutes lettres : *« Tous les compteurs se remettent à zéro par
`veille reset`. ⛔ Un compteur cumulatif ne tranche pas »*. **Deux y échappaient**,
et la sortie **se contredisait dans le même bloc** :

```
bascules -> Ambient : 0 · reveils : 0 · dernier reveil par : aucun
taps CONSOMMES par un reveil : 1          <-- par QUEL reveil ?
```

| Compteur | Était remis à zéro par | Conséquence |
|---|---|---|
| `dn_touch_consommes()` | `touch reset` **seulement** | le « 12 consommés » publié pour D-7 était **cumulatif** |
| `dn_veille_persist_n/us` | **rien** | « N au total » survivait, et *« aucune écriture depuis le boot »* devenait faux après un reset |

⇒ **Correctif** : `veille reset` appelle `dn_touch_consommes_rebaser()` — une
fonction **dédiée**, ⛔ **surtout pas** `dn_touch_reset_stats()`, qui zéroterait
aussi IRQ / lectures / appuis / relâchements / erreurs I²C, que `touch` publie et
que `veille` ne publie pas : ce serait échanger un mensonge contre un autre.
L'étiquette nomme désormais **les deux origines** possibles.

**TÉMOIN SUR LA CARTE** (`6144064`, un tap au doigt puis `veille reset`) :

| | mode | bascules | réveils | taps consommés |
|---|---|---|---|---|
| **avant** | ACTIF | 4 | 4 (dernier : **doigt**) | **1** |
| **après** | ACTIF | **0** | **0** (aucun) | **0** |

### 24.12.4 ✅ CE QUE LA GATE HÔTE ÉPROUVE DÉSORMAIS — **139 OK / 0 KO**

`tools/verif_veille_dn33.py` : **+20 contrôles** (bloc « 4 bis »), qui
**compilent et appellent** `dn_veille.c`, ⛔ ne rejouent pas sa logique.

- le délai est latché **avec** l'échantillon, et **survit à un changement de cran** ;
- un franchissement **amorcé** est jugeable, le **premier tick après armement** ne l'est pas ;
- **changer de cran désamorce**, et un tick **sous le nouveau seuil ré-amorce** ;
- `veille reset` remet `persist_n` à zéro **et** désamorce ;
- **une annulation n'est pas un ré-armement**.

🎯 **DEUX MUTANTS COMPILÉS, EXÉCUTÉS, ET VUS ROUGIR** — « jugeable toujours
vrai » et « délai non latché ». ⚠️ Un test peut être VERT **sans atteindre** la
ligne qu'il prétend couvrir : un mutant survivant l'aurait dit.

## 24.13 ⏳ CE QUI RESTE

✅ **SOLDÉ DEPUIS LA RÉDACTION DE CETTE LISTE** : **AC5.6** (§24.11.1) ·
**AC5.7 / AC6 / AC9.7** (§24.11.2) · **AC6.4 chiffré** (§24.11.3) · **AC7.3
moitié MENU** et le coût NVS de la voie MENU (§24.11.4) · **AC4.3 à la lettre**
et **D-7** (§24.11.5) · **AC9.5 / AC9.6** (§24.11.6) · **AC3.3 re-tirée**
(§24.11.7).

🔴 **CETTE PHRASE ÉTAIT « ⛔ RIEN DE CE QUI SUIT N'EST MESURÉ » — ELLE EST
DEVENUE FAUSSE LE 2026-08-28, ET ELLE EST AMENDÉE, ⛔ PAS EFFACÉE.** Deux des
trois lignes du tableau sont **soldées et chiffrées** (§24.15.1, §24.15.2) ; la
troisième est **close par un écart déclaré**, sur un motif **arithmétique**
(§24.15.4). ⛔ Laisser cette phrase telle quelle aurait publié dans le dossier
exactement le défaut que §24.15.3 corrige dans le firmware : **une étiquette qui
ment sur un état juste.**

| # | À mesurer | Instrument | Pourquoi ce n'est pas encore fait |
|---|---|---|---|
| ✅ **AC2.1** *(SOLDÉ le 2026-08-28 — §24.15.1)* | une case change en Ambient sur 60 s, critère `W2` (étendue ≥ 5, changement de **TEXTE** ≥ 10 %, σ ≥ 1) **sous agent réel** | ✅ `w2`, piste **`CPU % (dixieme) @1s [AMBIENT seul]`** — voir §24.13.1 | l'agent n'est **pas déployé** sur la tour ; il exige `COM3` côté Windows ⇒ **plus de console**. ⚠️ L'instrument, lui, **accumule tout seul** : c'est pour ça qu'il est dans le firmware. |
| ✅ **AC2.4** *(SOLDÉ le 2026-08-28 — §24.15.2)* | les cinq métriques PC **périment** et passent `--` quand les trames s'arrêtent, `AMBIANCE` restant **réelle** | `pc`, `veille` | ⚠️ **se tire AVEC AC2.1** : sans trames préalables, les cases sont `ABSENTE` **par défaut** et ne prouvent aucune péremption |
| **AC9.8** | **une nuit** en Ambient, relevée au matin (compteurs, `veille`, `hist`, heure) | ⛔ **`hist` NE PORTE PAS LA GRANDEUR** — l'anneau fait **120 s** | 🔴 **CLOS PAR ÉCART DÉCLARÉ** (décision owner du 2026-08-28) — le motif est **arithmétique**, pas un renoncement : **§24.15.4** |

⚠️ **AC2.4 NE SE TIRE PAS « PC ÉTEINT » DEPUIS CETTE SÉANCE** : la console vit
dans **WSL sur la tour**. Éteindre le PC supprime l'instrument. L'alimentation
USB de la carte, elle, **survit à l'extinction** (constat owner du 2026-08-25) —
donc un relevé PC éteint est possible, mais **À L'ŒIL uniquement**, et il faut
l'écrire comme tel.

### 24.13.1 ✅ AC2.1 A MAINTENANT UN INSTRUMENT — LA 6ᵉ PISTE W2, SUR `CPU`

#### Le constat qui l'a rendue nécessaire

⚠️ **Cette table nommait `w2` comme instrument d'AC2.1, et la story aussi. C'ÉTAIT
FAUX**, et ça a été relu **dans le source**, ⛔ pas supposé :

```
dn_w2_echantillon() — CINQ appelants, TOUS des capteurs LOCAUX
  dn_env.c:503        DN_W2_LUX              (BH1750)
  dn_capteurs.c:1393  DN_W2_PRESSION_ENT     (BME680)
  dn_capteurs.c:1394  DN_W2_PRESSION_DIX     (BME680)
  dn_capteurs.c:1396  DN_W2_TEMPERATURE_DIX  (BME680, témoin de contrôle)
  dn_capteurs.c:1404  DN_W2_GAZ_KOHM         (BME680 MOX)
```

⛔ **`CPU`, `GPU`, `RAM`, `RÉSEAU` et `DISQUE` n'étaient échantillonnés NULLE
PART** ⇒ AC2.1 était **non mesurable depuis son écriture**, et deux artefacts le
publiaient comme prêt. **Décision owner du 2026-08-25 : ajouter la piste.**

#### Ce qui a été ajouté — `DN_W2_CPU_DIX` (firmware `3188152`)

Échantillonne **`s_dx[CPU][0]`** dans le `hist_tick` de `dn_ui.c` — **le seul
endroit qui tient À LA FOIS la valeur AFFICHÉE et son régime**. La grandeur 0 de
`CPU` est déclarée `DN_PREC_DIXIEME`, donc **le dixième EST l'affichage**.
⛔ Un échantillonnage depuis `dn_link` prendrait la **SOURCE**, ce qu'AC2.1
interdit en toutes lettres.

**Trois décisions de conception, chacune avec son motif MESURÉ :**

| # | Décision | Motif |
|---|---|---|
| 1 | **1 Hz**, ⛔ pas 5 s | à 5 s, les 60 s d'AC2.1 ne font que **12 échantillons ⇒ 11 transitions**, et le **PAS du dénominateur vaut 9,1 %** quand le **SEUIL de taux vaut 10 %**. ⛔ Un seuil plus fin que le pas de son dénominateur n'est pas tranchable. À 1 Hz : 60 échantillons, 59 transitions, pas de **1,7 %** |
| 2 | **AMBIENT seulement** | sous agent réel **il n'y a PAS de console** (branche A : le REPL est le transport PC) ⇒ ⛔ **aucun `w2 reset` ne peut délimiter la fenêtre depuis l'extérieur**. La piste **se délimite elle-même** : tout échantillon qu'elle porte EST un échantillon d'Ambient. AC2.1 demande 60 s ⇒ **n ≥ 60** |
| 3 | **Rupture de chaîne entre épisodes** | la veille tombe et se lève des dizaines de fois par nuit ; concaténer les épisodes compterait comme « changement de texte » un saut qui n'est qu'une reprise. ⇒ `dn_w2_desamorcer()`, **idempotente**, et les ruptures sont **RETIRÉES DU DÉNOMINATEUR** (⛔ sans ce retrait, le biais irait **toujours** vers « NE QUALIFIE PAS ») |

🔴 **LA CADENCE DEVIENT PAR PISTE, ⛔ PLUS GLOBALE.** Chaque nom la porte
(`@5s`, `@1s`), `dn_w2_cadence_ms()` la publie, et **la gate vérifie que le nom
et la cadence CONCORDENT** — un tableau qui aligne des taux de cadences
différentes sans le dire serait une étiquette qui ment.

#### ✅ LE TÉMOIN DE CÂBLAGE, SUR LA CARTE (`3188152`)

⚠️ **CE N'EST PAS AC2.1**, et c'est écrit ici pour qu'on ne le lise jamais comme
tel : les valeurs viennent de **l'injection console**, que §24.10 a démontrée
**mauvais témoin** — et elles ont été choisies **artificiellement sautillantes**.
Ce témoin prouve **que l'instrument est câblé**, ⛔ rien sur le produit.

| Relevé | Valeur | Ce qu'il prouve |
|---|---|---|
| une trame, puis **8 s de silence** | **n = 3, rup = 1** | une trame vaut **3 000 ms** de validité ⇒ **3 échantillons à 1 Hz**, puis la péremption **brise la chaîne**. Exactement le contrat |
| 8 trames étalées sur **18 s** | **n = 18** · `secondes OBSERVEES` = **18** | **un échantillon par seconde de temps réel**, 1:1 |
| — | étendue **508** · taux **41 %** · σ **163,3** ⇒ QUALIFIE | l'arithmétique du verdict tourne |

🔴 **ET UN VERDICT D'AGENT A ÉTÉ ÉCRIT PUIS RÉFUTÉ PAR LA MESURE, DANS LA MÊME
SÉANCE.** Un premier tir avait donné `n = 2` là où on attendait ~25, avec
`secondes OBSERVEES : 1` — j'en ai conclu que **le trafic console affamait la
tâche LVGL**. ⛔ **C'ÉTAIT FAUX.** Le chronométrage du tir a montré que la rafale
d'injections durait **1 seconde**, ⛔ pas 25 : le tick avait donc battu
**exactement le bon nombre de fois**. ⚠️ **Un chiffre JUSTE sous un verdict
FAUX** — et il a suffi de mesurer la durée réelle pour le renverser.
⇒ **Le contre-témoin est publié** : 18 s réelles ⇒ 18 ticks ⇒ 18 échantillons.

⚠️ `31 pertes seq · 3 reprises` au compteur `pc` : artefact des **seq fabriqués à
la main** entre les tirs, ⛔ pas un défaut de liaison.

#### ⛔ CE QUE CETTE PISTE NE FERA JAMAIS

- **Comparer Actif et Ambient** : elle n'accumule qu'en Ambient, par conception.
- **Juger une autre case** : `GPU`, `RAM`, `RÉSEAU`, `DISQUE` restent
  non-échantillonnés. AC2.1 dit « **une** case » ; c'est `CPU`.
- **Se substituer à l'agent réel** : ⛔ l'injection console reste un mauvais
  témoin (§24.10). AC2.1 exige `./tools/deployer_tour.sh` + LHM.

⚠️ **CHAQUE CHIFFRE NOMMERA SON SHA, LU AU BANDEAU `App version`**, ⛔ pas déduit
du dépôt, et `git status --porcelain` **vide avant le flash**.

## 24.14 ⛔ CE QUE §24 NE PROUVERA PAS, MÊME APRÈS LA SÉANCE

- 🔴 **LA TENUE DANS LA DURÉE — ET CE POINT A ÉTÉ RÉÉCRIT LE 2026-08-28, PARCE
  QU'IL AFFIRMAIT CE QUI N'A JAMAIS ÉTÉ TIRÉ.** Il disait : *« `dn3-3`/AC9.8
  prouve **une nuit**, et rien de plus »*. **`dn3-3` ne prouve PAS une nuit** :
  AC9.8 est **clos par écart déclaré** et **aucune nuit n'a été relevée**
  (§24.15.4). ⇒ ~~**La plus longue fenêtre d'Ambient que §24 publie est 513 s**
  (§24.15.1).~~
  🔴 **AMENDÉ UNE SECONDE FOIS LE 2026-08-28 (§24.16.1), ⛔ PAS EFFACÉ — ET
  CETTE FOIS C'EST LA MESURE QUI CORRIGE, PAS LA RELECTURE.** La séance de
  validation a lu, **avant de flasher**, l'état que l'agent venait de laisser sur
  `156b507` : piste `CPU % (dixieme) @1s [AMBIENT seul]` à **n = 5795**, soit
  🎯 **5 795 s d'Ambient continu (1 h 37)**, `taux 98 %`, `σ 175,167` ⇒ QUALIFIE.
  ⇒ **La plus longue fenêtre d'Ambient que §24 publie est donc 5 795 s**, soit
  **11,3×** ce que cette ligne affirmait il y a quelques heures.
  ⚠️ **ET ÇA NE FAIT TOUJOURS PAS UNE NUIT** : 1 h 37 n'est ni 8 h ni 7 jours, et
  `hist` ne porte toujours que 120 s. ⛔ **L'interdiction d'extrapoler tient
  entièrement** — ni à une nuit, ni à une semaine.
  ⚠️ **LEÇON, ET ELLE DÉPASSE `dn3-3`** : ce chiffre n'a rien coûté à produire —
  il suffisait de **lire la carte avant de la flasher**. Le 513 s n'était pas
  faux, il était **le plus grand qu'on avait pensé à relever**.
  La durée, sous toutes ses formes, est **`dn4-5`**, et elle a **ses propres
  instruments** : les **24 seaux d'une heure** (§25.5) et le **`--journal-soak`**
  (§25.4). ⛔ Aucun des deux n'appartient à `dn3-3`.
- **L'appui fantôme RÉEL.** Le diagnostic est **armé et éprouvé sur mutant**, il
  n'a **pas été provoqué** sur la carte. Un GT911 réellement collé n'a pas été
  observé — on sait seulement que s'il l'était, la console le **dirait**.
- **La consommation électrique en Ambient.** Le rétroéclairage baisse, donc elle
  baisse — ⛔ mais **de combien n'est pas mesuré**, et aucun instrument de ce
  dépôt ne le mesure (l'INA219 a été retiré du bus).
- **Le coût réel de l'écriture NVS.** La gate hôte le chronomètre sur une horloge
  **simulée** : elle ne dit **rien** du cache flash de l'ESP32-S3.
- **Que le voile suffise à toutes les luminosités de pièce.** L'A/B d'AC9.2 se
  fait dans **une** pièce, à **un** moment.
- 🔴 **LA CAUSE DE L'ANOMALIE DE §24.11.8.** Un régime à **40 % de secondes non
  échantillonnées**, tenu ~280 s, a été **observé et chiffré** ; quatre causes
  candidates sont **éliminées par la mesure** et **aucune n'est établie**. Il
  n'a pas été reproduit sur ~1 100 s de fonctionnement ensuite. ⛔ §24 ne dit
  **pas** qu'il est corrigé, ⛔ ni qu'il ne reviendra pas. Le relevé qui
  manquerait pour trancher est nommé : **`touch` / `err_i2c` PENDANT l'épisode**.
- **Que les constats owner de §24.11.2 valent sur `dfa8204`.** Ils ont été pris
  sur **`6144064`**. Le correctif de §24.12 ne touche **ni le rendu du MENU ni
  le dispatch des zones** — mais c'est un **raisonnement**, ⛔ pas une mesure.

## 24.15 🏁 LA CLÔTURE DE `dn3-3` — LA SÉANCE SOUS AGENT RÉEL, PUIS L'ÉCART QUI FERME LA STORY

> **Date** : 2026-08-28. **Firmware de la séance** : `156b507`, **SHA LU AU
> BANDEAU**, rebuild fait **APRÈS** le commit.
> **Binaire en place à la clôture** : **`d244011`** (le remède XIP de `dn4-22`).
> ⚠️ **CE N'EST PAS LE MÊME SHA, ET C'EST DIT** : `d244011` est un **descendant**
> de `156b507` (`git merge-base --is-ancestor 156b507 d244011` ⇒ vrai), et il ne
> diffère du HEAD `f5fe6dd` que par **un fichier de mesures** ⇒ le **code** du
> binaire flashé est celui du HEAD. Les chiffres de §24.15.1 et §24.15.2 restent
> attachés à **`156b507`**, ⛔ pas au binaire en place.

### 24.15.1 🎯 AC2.1 — LES DONNÉES SONT VIVANTES EN AMBIENT, ET LE CRITÈRE `W2` QUALIFIE TRÈS AU-DELÀ DU SEUIL

**Agent réel sur la tour** (⛔ ni `dn_injecteur.py`, ni l'injection console : §24.10
démontre par les chiffres que cette dernière est un mauvais témoin) :
**3 265 trames à 5,00/s, 0 erreur d'envoi**, sur **653 s**.

Piste **`CPU % (dixieme) @1s [AMBIENT seul]`** — la valeur **AFFICHÉE**, ⛔ pas la
source (motifs de conception en §24.13.1) :

| Grandeur | Seuil `W2` | Mesuré | Marge |
|---|---|---|---|
| `n` (échantillons) | **60** demandés par AC2.1 | **513** | **8,5×** |
| étendue | **≥ 5** | **899** (min **32** → max **931** dixièmes, soit 3,2 % → 93,1 % de CPU) | **180×** |
| taux de changement du **TEXTE** | **≥ 10 %** | **96 %** | **9,6×** |
| σ | **≥ 1** | **176,411** | **176×** |

⇒ ✅ **QUALIFIE sur les TROIS seuils.** `rup = 2` (ruptures de chaîne entre
épisodes de veille, **retirées du dénominateur** — sans ce retrait le biais irait
**toujours** vers « ne qualifie pas », §24.13.1).

🎯 **UN CHIFFRE QUI SE DÉDUIT DE LUI-MÊME, ET IL VAUT D'ÊTRE DIT** : la piste
n'échantillonne **qu'en Ambient**, à **1 Hz** ⇒ `n = 513` **signifie 513 s
d'Ambient dans les 653 s d'agent**. **C'est la plus longue fenêtre d'Ambient que
§24 publie**, et §24.14 s'appuie dessus pour interdire toute extrapolation.

### 24.15.2 🎯 AC2.4 — LA PÉREMPTION EST PROUVÉE, ⛔ CE N'EST PAS LE `ABSENTE` PAR DÉFAUT

Après **coupure de l'agent**, `widget` relit les régimes :

| Case | Régime | Valeur affichée |
|---|---|---|
| `CPU` `GPU` `RAM` `RÉSEAU` `DISQUE` | **`ABSENTE`** | **`--`** |
| `AMBIANCE` | **`RÉELLE`** | **22,5 °C · 66,9 %** |

🎯 **CE QUI FAIT LA PREUVE, C'EST L'ORDRE** : les **3 265 trames ont COULÉ PUIS
SE SONT ARRÊTÉES**. ⇒ c'est une **vraie péremption**, ⛔ pas le `ABSENTE` par
défaut que la story redoutait en toutes lettres (*« sans agent préalable, les cinq
cases sont ABSENTE par défaut et ne prouvent AUCUNE péremption »*).
⛔ **Aucune valeur gelée n'est présentée comme vivante.**

⚠️ **ÉCART DÉCLARÉ, INCHANGÉ** : le volet **« PC ÉTEINT »** n'est **pas** tiré.
La console vit dans **WSL sur la tour** — l'éteindre supprime l'instrument.
L'alimentation USB de la carte, elle, **survit** à l'extinction (constat owner du
2026-08-25) ⇒ ce relevé reste possible **À L'ŒIL uniquement**.

### 24.15.3 🔴 UN 5ᵉ SITE D'ANGLE MORT — ET C'EST `dn3-3` QUI L'AVAIT CRÉÉ

`w2 reset` répondait *« accumulateurs W2 remis a zero (LES CINQ PISTES) »* alors
que cette story avait ajouté **`DN_W2_CPU_DIX` comme SIXIÈME** (§24.13.1).

⚠️ **L'INSTRUMENT ÉTAIT JUSTE** — `dn_w2_reset()` fait un `memset` sur des
tableaux dimensionnés `DN_W2_NB`, donc **les six pistes étaient bien remises à
zéro**. **C'est l'ÉTIQUETTE qui mentait**, et ce dépôt traite ça comme un défaut
à part entière (`dn_widget.h:165`).

⛔ **ÉCRIRE « SIX » N'AURAIT FAIT QUE DÉPLACER LA DATE DE PÉREMPTION** ⇒ le compte
est désormais **RELU de `DN_W2_NB`**. Un compte récité se périme à la piste
suivante ; un compte relu, jamais.

✅ **LE BALAYAGE A ÉTÉ FAIT SUR TOUT L'ARBRE, ET IL A ÉVITÉ QUATRE MENSONGES** :
les **6 autres occurrences de « cinq »** sont **JUSTES** et ⛔ **non touchées** —
`dn_console.c:8620`, `dn_env.h:373`, `dn_env.h:738`, `dn_ui.c:5811` disent « cinq
pistes **CAPTEURS** » (ce qui est vrai : les cinq appelants historiques sont des
capteurs locaux), et deux autres en parlent **au passé** : l'en-tête du bloc
**« 4 ter »** de `verif_veille_dn33.py` (*« avait cinq appelants »*) et le constat
d'ouverture de **§24.13.1** (*« `dn_w2_echantillon()` — CINQ appelants, TOUS des
capteurs LOCAUX »*). **Corriger à l'aveugle aurait fabriqué 4 mensonges.**

> ⚠️ **CES DEUX-LÀ SONT CITÉS PAR SYMBOLE, ⛔ PAS PAR NUMÉRO DE LIGNE — ET C'EST
> UNE LEÇON PAYÉE DEUX FOIS DANS CE DOSSIER.** `dn4-19` a cité `dn_console.c:8729`
> au cadrage et la ligne était **déjà périmée** à la livraison. La rédaction de
> §24.15 a **rejoué la même faute en direct** : elle citait `affichage.md:7550`
> alors que l'insertion de §24.15 elle-même **venait de décaler ce numéro à
> 7563**. ⇒ dans un fichier de cette taille que **trois stories vivantes** se
> partagent, **un numéro de ligne se périme pendant qu'on l'écrit**.

**Gate hôte : 162 → 167 OK / 0 KO**, dont un **MUTANT TEXTUEL** qui remet « LES
CINQ PISTES » et **le fait rougir sur les DEUX critères** — vu rougir :
`(False, False)`. Commit **`156b507`**.

### 24.15.4 ⛔ AC9.8 « LA NUIT » — CLOS PAR ÉCART DÉCLARÉ, ET LE MOTIF EST ARITHMÉTIQUE

🔴 **AUCUNE NUIT N'A ÉTÉ RELEVÉE. LE CRITÈRE N'EST PAS SATISFAIT.** Ce qui suit
dit **pourquoi il ne pouvait pas l'être avec l'instrument qu'il nomme**, ⛔ pas
pourquoi on a renoncé.

**Constat owner qui a ouvert l'examen, verbatim (2026-08-28)** :
> *« je ne comprend pas l'interret ? juste le pc est alume lagent tourne et la
> tablette point ya pas de nuit avec un autre affichage »*

**Quatre faits, relus dans le source, ⛔ pas dans la story :**

1. 🎯 **`hist` NE PEUT PAS PORTER UNE NUIT — C'EST UNE MULTIPLICATION.**
   `dn_hist.h:135-137` : `DN_HIST_N_POINTS = 120` et `DN_HIST_PERIODE_MS = 1000`
   ⇒ **l'anneau couvre 120 s, soit 2 minutes**. Au matin, `hist` rendrait **les
   deux dernières minutes**. ⇒ **l'AC nomme un instrument qui ne porte pas la
   grandeur qu'il lui demande.**
2. **LES TROIS AUTRES GRANDEURS D'AC9.8 SONT DÉJÀ SOLDÉES**, à des fenêtres plus
   courtes mais **avec leurs chiffres** : `hist` continue ⇒ **AC2.2** (+60 écrits
   / +60 réels / **0 trou**, §24.7.4) · compteurs et `veille` ⇒ **AC2.1**
   (**513 s d'Ambient**, §24.15.1) · l'heure avance ⇒ **AC2.3**. Une nuit sans
   contact rendrait **1 bascule, 0 réveil, Ambient** — ⛔ rien qui ne soit
   prédictible.
3. **CE QUI PORTE VRAIMENT UNE NUIT EXISTE, ET CE N'EST PAS À `dn3-3`** :
   `dn_hist.h:226-227` — `DN_HIST_SEAUX = 24` × `DN_HIST_SEAU_S = 3600` ⇒ **24
   seaux d'une heure**, lus par `dn_hist_minmax_long()` ; et le
   **`--journal-soak`** côté tour (⚠️ **plancher 18,3 o/s**, mesuré ailleurs à **157-163 o/s** ;
   rotation **32 Mo × 4 crans ⇒ rétention 160 Mo** — chiffre repris le 2026-08-28, voir §25.4). **Les
   deux sont les instruments de `dn4-5`** — son **AC3.2** (§25.5) et son **AC2.5**
   (§25.4). AC9.8 demandait donc à `dn3-3` de prouver **un sous-ensemble de
   `dn4-5`** avec un anneau de **2 minutes**.
4. 🔴 ~~**LE SEUL PROTOCOLE DE RELEVÉ DÉTRUIT SA PROPRE MESURE.** L'agent tient
   `COM3` côté Windows ; reprendre le port **redémarre la puce** ⇒ le relevé du
   matin **effacerait les compteurs, `hist` et l'heure** qu'il vient chercher.
   La seule parade (couper l'agent pour la nuit) **dégrade la condition
   nominale** — précisément ce que le constat owner refuse.~~

   🔴 **CE POINT N°4 EST RÉFUTÉ PAR LA MESURE LE 2026-08-28 (§24.16.1). ⛔ IL
   N'EST PAS EFFACÉ : IL A ÉTÉ ÉCRIT, IL A PORTÉ UNE DÉCISION, ET IL ÉTAIT
   FAUX.** Le relevé : après `./tools/rendre-port.sh --vers-flash` — c'est-à-dire
   **exactement le geste du matin** (arrêt propre de l'agent par son fichier-stop,
   puis `detach`/`attach`) — la console a rendu `secondes OBSERVEES : 5868`,
   ⇒ **la puce tournait depuis 1 h 38 SANS reboot, compteurs INTACTS**.
   🎯 **ET LE SENS INVERSE A ÉTÉ MESURÉ DANS LA MÊME SÉANCE** : `up` valait
   **470 s** avant de rendre le port, l'agent a vécu **286 s**, et `up` au retour
   valait **340 s** au lieu des ~760 attendus ⇒ **la puce redémarre quand
   WINDOWS OUVRE `COM3`**, ⛔ pas au `detach`/`attach`. Le dépôt avait donc
   raison sur *« sous Windows, ouvrir le port RESET la carte »* — et
   `dn_agent.py` force bien `dtr=False, rts=False` **avant** `open()` sans que
   ça suffise.
   ⇒ 🔴 **LE MOTIF N°4 TOMBE ENTIÈREMENT, ET LE PROTOCOLE DE NUIT EXISTE** : le
   reboot a lieu **au lancement de l'agent**, donc **AVANT la nuit** — on part
   d'un état neuf **par construction** — et **le relevé du matin, lui, ne
   redémarre rien**. ⛔ Ce qui maintient l'écart d'AC9.8 n'est plus ce motif :
   c'est **l'anneau de 120 s** (motif n°3), et le fait qu'**aucune nuit n'a été
   relevée**.

🎯 **CE QUE LE CONSTAT OWNER DIT, ET QUE LES QUATRE FAITS CONFIRMENT** : *« il n'y
a pas de nuit avec un autre affichage »*. **La nuit n'est pas un ÉTAT, c'est une
DURÉE.** Il n'existe **aucun régime nocturne** à mesurer — Ambient la nuit, c'est
Ambient. Et la durée, sous toutes ses formes, **est le métier de `dn4-5`**.

⇒ **DÉCISION OWNER DU 2026-08-28** : `dn3-3` se **ferme avec cet écart déclaré**,
⛔ **sans `[CC]`** et ⛔ **sans nuit tirée**.

⚠️ **LE COÛT DE CETTE FERMETURE EST ÉCRIT, ⛔ PAS MINIMISÉ** :
- ~~`dn3-3` **ne publie aucune fenêtre d'Ambient au-delà de 653 s** (513 s
  d'Ambient dedans).~~ 🔴 **PÉRIMÉ LE 2026-08-28 (§24.16.1)** : la mesure prise
  avant le flash porte **5 795 s d'Ambient continu**. §24.14 interdit toujours
  l'extrapolation — ⛔ 1 h 37 n'est pas une nuit.
- **`dn4-5` n'hérite formellement de rien** : la fermeture est un écart, ⛔ pas un
  transfert de périmètre. Si la tenue d'une nuit doit être prouvée un jour, elle
  se prouvera **dans `dn4-5`, avec les seaux et le journal**, ⛔ pas ici.

### 24.15.5 ⛔ CE QUE CETTE CLÔTURE NE PROUVE PAS

- 🔴 **LES CAPTURES BRUTES DE LA SÉANCE DU 2026-08-28 NE SONT PAS ARCHIVÉES.**
  Il n'existe **pas** de `mesures/dn3-3/` dans le dépôt (vérifié : `mesures/` ne
  porte que `dn4-4`, `dn4-5`, `dn4-8`, `dn4-13`, `dn4-17`, `dn4-18`, `dn4-19`,
  `dn4-20`, `dn4-22`). Les chiffres de §24.15.1 et §24.15.2 proviennent du relevé
  de séance consigné **le jour même** au tracker. ⚠️ **C'est un écart de
  traçabilité, et il est dit** : ⛔ ces deux sous-sections ne sont pas
  re-vérifiables à partir du dépôt seul, contrairement à §24.7 à §24.12.
- **Que les chiffres de §24.15.1-2 vaillent sur le binaire EN PLACE.** Ils sont
  tirés sur **`156b507`** ; le binaire en place est **`d244011`**. La filiation
  est vérifiée (§24.15, en-tête), mais **la reconduction est un raisonnement**,
  ⛔ pas une mesure.
- **Une nuit, une semaine, ou quelque durée que ce soit** — §24.15.4.
- **Tout ce que §24.14 énumère déjà** reste vrai et non touché.

🏁 **§24 EST CLOSE.** Les critères de `dn3-3` y sont tous adressés : ✅ mesurés,
ou ⛔ **déclarés non tirés avec leur motif**. ⛔ Aucun n'est laissé en silence.

---


## 24.16 🔴 SÉANCE DU 2026-08-28 — LA REVUE DE CODE ÉPROUVÉE SUR LA CARTE, ET DEUX VERDICTS DE §24 QUI TOMBENT

**Firmware `d6123c5`** — SHA **LU AU BANDEAU** (`App version : d6123c5`), arbre propre, rebuild
fait **APRÈS** le commit. `SPI Flash Size : 16MB`, XIP PSRAM active (*« Instructions copied and
mapped to SPIRAM »*), `num_fbs=1`, `bounce=9600`.

### 24.16.1 🎯 DEUX AFFIRMATIONS DE §24 SONT RÉFUTÉES PAR LA MESURE, ⛔ PAS AMENDÉES À LA MARGE

Les deux sont tombées **avant même le flash**, en lisant l'état que l'agent venait de laisser sur
le firmware `156b507`. C'est le genre de mesure qu'on ne peut pas refaire : elle allait être
détruite par le flash suivant.

| # | Ce que §24 affirmait | Ce que la carte a rendu |
|---|---|---|
| **1** | *« reprendre le port REDÉMARRE LA PUCE ⇒ le relevé du matin effacerait exactement les compteurs qu'il vient chercher »* (§24.15.4, l'un des motifs d'AC9.8) | 🔴 **FAUX pour le sens agent → WSL.** `secondes OBSERVEES : 5868` ⇒ la puce tournait depuis **1 h 38 sans reboot**, compteurs intacts, APRÈS la reprise du port. |
| **2** | *« la plus longue fenêtre d'Ambient que §24 publie est 513 s »* (§24.14, amendée le 2026-08-28) | 🔴 **DÉPASSÉE d'un facteur 11,3.** Piste `CPU % (dixieme) @1s [AMBIENT seul]` : **n = 5795**, soit **5 795 s d'Ambient continu** (1 h 37), `taux 98 %`, `σ 175,167` ⇒ **QUALIFIE**. |

🎯 **ET LE SENS INVERSE A ÉTÉ MESURÉ DANS LA MÊME SÉANCE — LA QUESTION EST DONC TRANCHÉE DES DEUX
CÔTÉS, ⛔ PLUS À MOITIÉ.** Témoin, en trois nombres qui se réconcilient :

| Repère | Valeur |
|---|---|
| `up` relevé **avant** de rendre le port | **470 s** |
| durée de vie du process agent | **286 s** |
| `up` attendu si rien ne redémarre | ~**760 s** |
| 🔴 `up` **lu au retour** | **340 s** |

`340 ≈ 286 + 54` ⇒ **la puce a redémarré AU MOMENT OÙ WINDOWS A OUVERT `COM3`**, ⛔ pas pendant le
`detach`/`attach`. Confirmé par `veille` au retour : `bascules : 1 · reveils : 0`,
`Actif 61 s · Ambient 314 s` — la carte a rebooté, passé **exactement le cran de 1 min** en ACTIF,
puis basculé. Tout se réconcilie.

⇒ **LE VERDICT COMPLET, ET IL REND LE RELEVÉ DE NUIT POSSIBLE :**

| Sens | Reboot ? | Conséquence pour un soak |
|---|---|---|
| **WSL → agent** (Windows **ouvre** `COM3`) | 🔴 **OUI** | ⚠️ Sans conséquence : ça a lieu **AVANT** la nuit, on part d'un état neuf **par construction**. |
| **agent → WSL** (`--vers-flash`, arrêt propre puis `attach`) | ✅ **NON** | 🎯 **Le relevé du matin NE DÉTRUIT PAS sa mesure.** |

🔴 **LE MOTIF N°4 D'AC9.8 EST DONC RÉFUTÉ, ET PAS À MOITIÉ** : *« le seul protocole de relevé
détruit sa propre mesure »* est **faux**. Le protocole existe et il tient : **lancer l'agent (le
reboot a lieu ici, avant la nuit) → laisser la nuit courir → reprendre le port au matin (aucun
reboot) → lire.** ⛔ **Ce qui reste vrai**, et qui suffit à maintenir l'écart déclaré : **aucune
nuit n'a été relevée**, et `hist` ne porte toujours que **120 s**.

🔴 **CE QUE ÇA CHANGE POUR AC9.8, ET CE QUE ÇA NE CHANGE PAS.** Le motif d'écart d'AC9.8 reposait
sur **deux** jambes : (a) *l'anneau `hist` ne couvre que 120 s* — ⛔ **elle tient, elle est
arithmétique** (`DN_HIST_N_POINTS = 120` × `DN_HIST_PERIODE_MS = 1000`) ; (b) *le protocole détruit
sa propre mesure* — 🔴 **elle est fausse**. ⇒ L'écart déclaré **reste** (aucune nuit n'a été
relevée, et `hist` ne la porterait toujours pas), mais **son motif est corrigé de moitié**, et
⛔ ce n'est pas une réécriture cosmétique : c'est **une porte qui se rouvre pour `dn4-5`**, dont le
soak d'une semaine se relève précisément par ce chemin.

### 24.16.1 bis ✅ AC2.1 RE-TIRÉE SUR `d6123c5`, SOUS AGENT RÉEL

Agent lancé sur la tour, **286 s** de fenêtre, puis reprise du port et lecture.

| Grandeur | Valeur | Seuil | Marge |
|---|---|---|---|
| `n` (piste `CPU % (dixieme) @1s [AMBIENT seul]`) | **247** | 60 | **4,1×** |
| `rup` | 1 | — | — |
| min / max (dixièmes) | 32 / 657 | — | 3,2 % → 65,7 % de CPU |
| **étendue** | **625** | 5 | **125×** |
| **taux de changement du TEXTE** | **97 %** | 10 % | **9,7×** |
| **σ** | **173,080** | 1,000 | **173×** |
| **verdict** | ✅ **QUALIFIE** | | |

⚠️ **`n = 247` pour 286 s d'agent, ET C'EST COHÉRENT** : la carte a redémarré à l'ouverture de
`COM3` (§24.16.1), donc elle a passé **61 s en ACTIF** avant de basculer — la piste
n'échantillonne **qu'en Ambient**. `247 + 61 ≈ 308`, le reste étant la bascule de port.

🎯 **ET CETTE LECTURE EXERCE LE DÉNOMINATEUR CORRIGÉ** : elle est prise **chaîne FERMÉE** (l'agent
est arrêté depuis ~40 s, les valeurs sont périmées ⇒ `dn_w2_desamorcer()` a tiré, `amorce = false`)
— c'est-à-dire **exactement le cas où l'ancienne formule retranchait une rupture de trop**. Ici
`episodes = rup = 1` ⇒ `transitions = 246` ; l'ancienne écriture aurait rendu **245**.

Liaison sur la même fenêtre : **1 479 trames valides**, 0 doublon, **16 pertes seq**, 0 resynchro ;
latence acceptation→label **n = 1 479 · min 9 / moy 180 / max 447 ms**.
✅ **AC2.4 re-confirmé sur `d6123c5`** : 40 s après l'arrêt de l'agent, les **cinq** métriques PC
sont `MORTE` — les trames ont **coulé PUIS se sont arrêtées**, ⛔ ce n'est pas l'`ABSENTE` par
défaut.
✅ **AC3.2 (`dn4-5`)** sur cette fenêtre : `Actif 61 s · Ambient 314 s` ⇒ **Ambient = 84 %**.

### 24.16.2 ✅ LES QUATRE DÉFAUTS FONCTIONNELS — UN SEUL EST DIRECTEMENT ÉPROUVABLE, ET IL L'EST

🎯 **LE REBASE D'HORLOGE SUR `veille off` / `veille on` (défaut (d)) — PROUVÉ, CHIFFRÉ, SUR LA CARTE.**

| Instant | `mode` | `inactivite` | `max vue` | `bascules` |
|---|---|---|---|---|
| en Ambient depuis ~3 min | `AMBIENT` | 204 260 ms | 204 260 ms | 1 |
| après `veille off` | `ACTIF` | 🎯 **2 560 ms** | 204 260 ms | 1 |
| **24,7 s après `veille on`** | 🎯 **`ACTIF`** | 24 735 ms | 204 260 ms | 🎯 **1** |

⚠️ **CE QUE LE TABLEAU PROUVE, LIGNE PAR LIGNE** : l'horloge est **rebasée** (2 560 ms au lieu de
204 260), le `max vue` **garde la trace** de ce qu'elle valait — donc l'instrument dit **les deux**,
⛔ il n'efface pas —, et **24,7 s après le ré-armement le module est toujours ACTIF avec le même
compteur de bascules**. **AVANT le correctif**, `veille on` trouvait `inactivite = 204 s > delai`
⇒ bascule **au tick suivant (~1 s)**, avec un écart latché de 204 s marqué « NON JUGEABLE ».

⛔ **LES TROIS AUTRES SONT ARMÉS ET DÉCLARÉS, ⛔ PAS PROVOQUÉS** — et c'est écrit ici plutôt que
laissé à deviner, exactement comme l'appui fantôme de §24.14 :

| Défaut | Compteur publié | Pourquoi il n'a pas été provoqué |
|---|---|---|
| (a) course de `veille_dormir_async` | `bascules dont l'async a ete ABANDONNEE : 0` | La fenêtre est **UN cycle `lv_timer_handler`** contre ~100 ms d'aller-retour console. **Budget d'essais annoncé et tenu : zéro tentative**, ⛔ plutôt que dix tirs au hasard présentés comme une preuve. |
| (b) expiration du verrou de consommation | `contacts consommes EXPIRES (bus illisible) : 0` | Demande **32 lectures I²C ratées d'affilée pendant un contact consommé** — c'est la fenêtre de démarrage à froid, ⛔ pas provocable à la demande. |
| (c) détecteur d'appui fantôme ré-armé | (pas de cri) | Le module est **sain** : `inact_max` dépasse le délai à chaque cycle ⇒ le détecteur **doit** se taire, et il se tait. 🎯 **Le sens positif est prouvé HORS CARTE**, par trois contrôles de gate qui compilent et appellent `dn_veille.c` — dont *« RÉVEIL puis doigt collé ⇒ l'alerte SORT »*, le cas que l'ancienne garde ne pouvait **pas** voir. |

### 24.16.3 ✅ LES INSTRUMENTS CORRIGÉS, RE-TIRÉS SUR LA CARTE

- **`veille geom`** — signature FNV-1a **`0xE6887D29`**, ⚠️ **IDENTIQUE** à celle du 2026-08-25 sur
  `6144064` ⇒ la revue n'a **pas** bougé la géométrie. Et la sortie **DIT désormais ce que la preuve
  vaut** : garde de non-régression, ⛔ pas une mesure qui pourrait échouer, avec la liste nommée de
  ce qui n'est **pas** couvert (`val_y` 48→26, pas 40→47, police 28→33/56).
- **`veille accents`** — *« a 95 %, les **7** accents restent DISTINCTS deux a deux (les cases + **l'humidite d'AMBIANCE**) »*.
  🎯 **TÉMOIN POSITIF TIRÉ** : à **100 %**, l'instrument **CRIE** — *« GPU » et « RAM » rendent tous
  deux `A0A0A0` ». ⛔ Sans ce tir, le ✅ à 95 % ne vaudrait rien.
- **`w2 reset`** — *« accumulateurs W2 remis a zero (**LES 6 PISTES**) »*, compte **RELU** de
  `DN_W2_NB`.
- **`veille reset`** — ✅ remet bien à zéro (`ecarts : AUCUN ECHANTILLON`, ⛔ pas « 0 ms ») **et
  NOMME ce qu'il épargne** : le temps mural par mode a **survécu** (`Actif 200 s · Ambient 231 s`),
  parce que c'est la **fenêtre de soak de `dn4-5`, qui dure UNE SEMAINE**.

### 24.16.4 ✅ AC3.3 RE-TIRÉE À LA LETTRE SUR `d6123c5` — ET LES TROIS SONT **JUGEABLES**

| # | écart | délai armé | marge | verdict |
|---|---|---|---|---|
| 1 | **60 590 ms** | 60 000 | +590 | ✅ dans `[délai ; délai+1 s]` |
| 2 | **60 805 ms** | 60 000 | +805 | ✅ |
| 3 | **60 190 ms** | 60 000 | +190 | ✅ |

Dispersion **615 ms** (vs **350 ms** sur `6144064`, §24.11.7 — plus dispersé, **les deux dans la
fenêtre**, ⛔ aucun des deux ne réfute l'autre).
🎯 **ET LES TROIS SONT JUGEABLES**, là où la séance du 25/08 avait dû publier des échantillons
« NON JUGEABLE » : c'est l'effet **direct** du rebase ajouté à `veille delai` / `veille on|off` —
le dépôt traitait le symptôme depuis le 2026-08-25, la revue a traité la cause.

### 24.16.5 ✅ CE QUE LA SÉANCE A CONFIRMÉ AU PASSAGE

- **AC7.3** — les deux réglages ont **survécu au flash** (délai 1 min, veille armée), et
  *« aucune ecriture NVS depuis le boot »* prouve qu'ils sont **RELUS**, ⛔ pas ré-écrits.
- **AC2.4** — sur `156b507`, 62 s après l'arrêt de l'agent : les **cinq** métriques PC en `MORTE`,
  `AMBIANCE` vivante. **29 065 trames valides**, 0 doublon, **193 pertes seq**, 0 resynchro.
  Latence acceptation→label **n = 29 065 · min 0 / moy 152 / max 392 ms**.
- **AC3.2 (`dn4-5`)** — `Ambient = 98 %` sur la fenêtre de 1 h 38, très au-dessus du seuil de 50 %.
- **fps** — **37,40 Hz mesuré = 37,40 Hz théorique, écart +0,00 %**, deux tirs (15 s et 65 s).
- **Constat owner à l'œil** : allumage normal (asset **plein écran**, rétroéclairage **fixe**), et
  🎯 **la DATE BLEUE de la barre en Ambient est ACCEPTÉE** — *« ça va, on la laisse »* ⇒ le report
  du ledger se **ferme par constat owner**, la barre est de la **DONNÉE** (AC2.3), ⛔ pas une
  affordance.

### 24.16.6 ⛔ CE QUE §24.16 NE PROUVE PAS

- ⛔ **Aucune nuit.** La plus longue fenêtre d'Ambient de cette séance est celle du firmware
  **précédent** (5 795 s). Sur `d6123c5`, elle se compte en minutes.
- ⛔ **Le sens WSL → agent n'est pas testé** pour la question du reboot (§24.16.1).
- ⛔ **Trois des quatre défauts fonctionnels ne sont pas provoqués sur la carte** (§24.16.2) — leur
  preuve est *hors carte* pour (c), et **inexistante** pour (a) et (b). Les compteurs sont armés :
  s'ils montent un jour, ils le **diront**, et c'est tout ce qu'on peut affirmer aujourd'hui.
- ⛔ **Le MENU au doigt n'a PAS été re-tiré** sur ce firmware : les constats de §24.11.2 valent par
  **raisonnement**, ⛔ pas par mesure sur `d6123c5`.

---

# §25. 🎯 `dn4-5` (P9.5) — L'INSTRUMENT QUI PEUT VOIR LE GEL, ET LE COMPTEUR QUI NE REBOUCLE PLUS

> **Périmètre** : ce que `dn4-5` a **construit et éprouvé sans carte**, avant le soak de 7 jours.
> ⚠️ **Tout ce qui suit est éprouvé sur le PRODUIT COMPILÉ, sous WSL, avec une horloge pilotée.**
> ⛔ **Rien ici n'est une mesure sur le silicium** — la confirmation carte est AC3, et elle est dite
> à chaque endroit où elle manque.
> **SHA de départ** : `c31bb97`. **Décision owner du 2026-08-26** : **Ordre A** — le soak attend
> `dn3-3` et `dn4-10`, ⛔ aucune story `backlog` n'entre dans le gel.

## 25.1 🎯 LA TRIADE DU BATTEMENT — TROIS HORLOGES, TROIS SOURCES, ET C'EST ÇA L'INSTRUMENT (AC2.1)

**Le verdict de cette story est *« 0 gel sur 7 jours »*, et le piège est STRUCTUREL** :
*« un uptime de 7 jours ne prouve PAS l'absence de gel »*. La carte peut avoir **l'image figée**
pendant que la tâche `app_main` bat tranquillement. Ce qui rend les deux cas **discriminables**,
c'est que la ligne de battement porte **trois compteurs qui ne viennent pas de la même source** :

| compteur | qui l'écrit | ce qu'il prouve QUAND IL AVANCE | ce que son FIGEMENT signifie |
|---|---|---|---|
| `up` / `mural` | tâche `app_main` (`vTaskDelay` / `esp_timer`) | **l'application est planifiée** | FreeRTOS ne planifie plus cette tâche |
| `vsync` | **ISR du panneau RGB** (`dn_measure.c`, `on_vsync`) | **la DMA balaie la dalle** | dalle morte, DMA arrêtée, ou ISR jamais appelée |
| `flush` / `cycles` | **tâche LVGL** (`dn_ui.c`) | **quelque chose est DESSINÉ** | 🔴 **LVGL est bloquée — L'IMAGE EST FIGÉE PENDANT QUE `up` AVANCE** |

🔴 **LA SIGNATURE À CHERCHER DANS LE JOURNAL DU SOAK** : `up` et `vsync` **qui avancent** pendant
que `flush` et `cycles` **ne bougent pas**. C'est ce triplet, et lui seul, qui distingue une image
figée d'une carte en bonne santé.

⛔ **CE QUE LA TRIADE NE VOIT PAS, ET IL FAUT LE SAVOIR EN LISANT** :
- **`vsync` ne descend pas jusqu'à l'œil.** Une dalle qui balaie un framebuffer **figé** compte
  des vsyncs exactement comme une dalle vivante. ⇒ **le constat owner à l'œil reste requis** (AC3.4).
- **`flush` qui avance ne prouve pas que le CONTENU change.** LVGL peut redessiner la même chose.
- **Une carte HALTÉE n'émet plus rien** : elle se lit comme un **silence**, ⛔ jamais comme un
  événement. C'est pour ça que le battement est journalisé — **son absence EST le signal**.

## 25.2 🔴 LA CONTRE-ÉPREUVE — LA COMMANDE `gel`, PARCE QU'UNE GATE JAMAIS VUE CRIER N'EN EST PAS UNE (AC2.2)

**Au cadrage, la triade n'avait JAMAIS été mise à l'épreuve sur un gel.** Elle était un raisonnement,
pas un instrument. Il n'existait par ailleurs **aucun moyen de bloquer LVGL volontairement** : ni
dans `dn_stimulus.c` (qui ne porte que `tear` et `flash`), ni au README.

⇒ **`dn_ui_geler_ms()`** (dn_ui.c) prend le **verrou LVGL** et le **tient**. La tâche LVGL le réclame
à chaque itération : privée de lui, elle **ne dessine plus**. La commande console **`gel [secondes]`**
l'enveloppe et publie le Δ des trois compteurs.

**Trois choix de conception, et chacun ferme un faux négatif** :

1. **LE RELEVÉ EST PRIS AVANT LE DÉVERROUILLAGE.** Relevé après, depuis l'appelant, la tâche LVGL
   aurait le temps de faire **un ou plusieurs cycles de rattrapage** entre le déverrouillage et la
   lecture : `flush` aurait bougé, et la contre-épreuve conclurait *« pas de gel »* **sur un gel qui
   a bel et bien eu lieu**. ⇒ un faux négatif **fabriqué par l'instrument lui-même**.
2. **12 s PAR DÉFAUT, ET LE CHIFFRE N'EST PAS ARBITRAIRE** : il doit dépasser **les 10 s du
   battement** (sans quoi aucune ligne `up` ne sortirait *pendant* le gel, et la preuve la plus
   lisible manquerait) **et les 5 s de `CONFIG_ESP_TASK_WDT_TIMEOUT_S`.**
3. **ON DORT, ON NE TOURNE PAS EN ROND.** Une attente active tiendrait un cœur à 100 % et ferait
   japper le watchdog sur la tâche IDLE : on mesurerait **deux défauts au lieu d'un**, et le journal
   ne saurait plus lequel il regarde.

⚠️ **`gel` rend `false` si le verrou n'est pas pris en 2 s** — et la commande le dit :
*« ⛔ « pas mesuré », PAS « pas de gel ». Rejouer. »*

## 25.2 bis ✅ AC2.2 **TIRÉ SUR LA CARTE** LE 2026-08-26 — ET LA CARTE A TROUVÉ UN DÉFAUT D'INSTRUMENT

**Firmware `dn4-5`, flashé et vérifié** — `desknode.bin` **1 151 120 o**, hash confirmé, **SHA `afee371`**.
⚠️ *« Une mesure porte la date de son binaire »* : tous les chiffres de cette sous-section sont pris sur **ce** binaire, et sur aucun autre.

### Le tir décisif — et le régime est CONFIRMÉ AVANT, ⛔ pas supposé

| relevé | mural | vsync | flush | cycles |
|---|---:|---:|---:|---:|
| **AVANT** (sous verrou) | 85 s | 3 095 | **1 034** | **997** |
| **battement PENDANT le gel** | 93 s | 3 420 | **1 034** | **997** |
| **APRÈS** (sous verrou) | 97 s | 3 543 | **1 034** | **997** |
| **Δ sur 12,0 s** | **+12,0 s** ✅ | **+448** ✅ (attendu ~449) | **+0** 🔴 | **+0** 🔴 |

🎯 **LE RÉGIME EST CHIFFRÉ, ET C'EST CE QUI DONNE SA FORCE AU ZÉRO** : juste avant le tir, `anim on
2000` faisait tourner l'écran à **18,1 flush/s** (286 → 468 → 649, soit **+182 puis +181 par 10 s**).
⇒ **un gel de 12,0 s a supprimé ~217 redessins attendus. Il en est passé ZÉRO.**

### 🔴 QUATRE INSTRUMENTS INDÉPENDANTS, PLUS L'ŒIL

| témoin | ce qu'il a dit |
|---|---|
| le **battement** | `up` +10 et `vsync` +325 pendant que `flush`/`cycles` ne bougent pas d'un cran |
| **`dn_capt`** (⚠️ non prévu) | *« verrou LVGL indisponible 2 fois — poussée perdue »*, **deux fois** |
| **`dn_ui`** (⚠️ non prévu) | *« historique : **11 seconde(s) NON ÉCHANTILLONNÉE(S)** »* — il **chiffre** le gel |
| **`vsync` vs `mural`** | +448 pour 12,0 s = **37,3 Hz**, la dalle balayait normalement |
| 🔴 **CONSTAT OWNER** | *« la barre s'est arrêtée net puis repartie »* |

### 🔴 CE QUE LA CARTE A TROUVÉ, ET QUE LE BANC N'AURAIT PAS TROUVÉ

**Le premier tir a publié `flush +1` et l'instrument a REFUSÉ de conclure** — *« CETTE MESURE est à
jeter, et chercher pourquoi »*. Le refus était juste ; **le défaut était le sien** :
le relevé d'**AVANT** était pris **par l'appelant, HORS du verrou**. Entre ce relevé et la prise du
verrou, la tâche LVGL avait le temps de finir **un cycle**.

⚠️ **ET IL NE SE MONTRE QU'EN RÉGIME CHARGÉ.** Au repos (agent arrêté, ~2 flush / 10 s) la fenêtre
de course est trop courte pour être touchée : **le premier tir, au repos, avait publié `+0`**. Un
instrument éprouvé **uniquement au repos** aurait été déclaré bon. C'est `anim on` qui l'a sorti.
⇒ **les deux relevés sont désormais pris dans `dn_ui_geler_ms()`, verrou en main.**

⚠️ **ET LE PIÈGE S'EST PRÉSENTÉ UNE SECONDE FOIS, SOUS UN AUTRE VISAGE** : le tir de vérification
suivant a été lancé **juste après `anim on`**, alors que l'animation **n'avait pas encore démarré**
(`flush` valait 16 et n'a pas bougé). Il rendait `+0`… **dans le régime au repos, celui-là même qui
cachait le défaut.** ⇒ **le régime se CONFIRME au compteur avant de tirer**, ⛔ il ne se suppose pas
parce qu'on vient d'armer le stimulus.

### 📋 CE QUE CE TIR NE DIT TOUJOURS PAS
- **`vsync` ne descend pas jusqu'à l'œil** : une dalle qui balaie un framebuffer figé compte des
  vsyncs comme une dalle vivante. ⇒ le constat owner reste requis, et il a été pris.
- ⛔ **Il ne dit pas que la carte ne gèlera pas.** Il dit que **si elle gèle, l'instrument le verra**.

### ⚠️ ET UN CONSTAT EN PASSANT, QUI CORRIGE CE QUE §25 ÉCRIVAIT LE MATIN MÊME

L'écart `mural − up` a été relevé **+3 s** à `up 10..90 s`, puis **+5 s** à `up 6010 s` (~100 min
plus tard, même boot). ⇒ **ce n'est PAS un décalage d'amorçage constant : il DÉRIVE.**
⛔ Deux points ne font pas une loi et l'ampleur n'est **pas** extrapolée ici — mais la direction est
mesurée, et c'est **exactement** ce qu'AC1.4 existe pour rendre visible. **Le soak tranchera.**

## 25.3 ⚠️ CE QUE LA CONFIG FAIT SUR UNE PANNE — TROIS FAITS, ET DEUX SONT DES FAUX NÉGATIFS (AC2.3, AC2.4)

Relus dans `sdkconfig` au 2026-08-26.

| réglage | valeur | ce que ça fait **vraiment** |
|---|---|---|
| `CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT` | **`y`** (l.1320) | 🔴 une panique **HALTE la puce** : ⛔ **pas de reboot**, écran figé sur sa dernière image, et **plus un octet sur le fil** |
| `CONFIG_ESP_TASK_WDT_PANIC` | **non posé** (l.1356) · `TIMEOUT_S = 5` | 🔴 une tâche bloquée > 5 s **IMPRIME un avertissement** et **ne redémarre RIEN** ⇒ **`up` continue d'avancer** |
| `CONFIG_ESP_COREDUMP_ENABLE_TO_NONE` | **`y`** (l.1467) | ⛔ **aucun post-mortem**. Si la carte tombe au jour 5, **la seule trace est le fil série** |

🔴 **AC2.3 — LA SIGNATURE DE LA PANIQUE HALTÉE, ET POURQUOI ELLE SE CONFOND AVEC AUTRE CHOSE.**
Une carte haltée et un agent qui a perdu le port produisent **le même symptôme vu du fil** : plus
rien n'arrive, et l'agent voit un `Write timeout`. **Les deux se ressemblent trait pour trait.**
⇒ **c'est le journal de la tour qui les sépare** : il journalise les **événements de port de
l'agent** (`PORT OUVERT` / `PORT PERDU` / `PORT FERMÉ`) **à côté** du battement de la carte.
- battement qui s'arrête **sans** `PORT PERDU` ⇒ 🔴 **la carte s'est tue** (haltée, ou morte) ;
- battement qui s'arrête **avec** `PORT PERDU` ⇒ ⚠️ **l'agent a perdu le port**, la carte est
  peut-être intacte — et la reprise le dira.

⚠️ **ET `esp_reset_reason()` NE VERRA JAMAIS UNE PANIQUE HALTÉE**, puisqu'il n'y a **pas de boot
suivant**. Si quelqu'un débranche après coup, le reset suivant sera `POWERON`. ⇒ **la panique haltée
se détecte par l'ABSENCE de battement, ⛔ jamais par la raison du reset.** C'est écrit dans le code,
au-dessus de `raison_reset_clair()`.

🔴 **AC2.4 — LE TWDT EST NON-PANIQUANT, ET C'EST UNE DÉCISION OWNER, ⛔ PAS UN OUBLI.**
Le poser à `y` ferait **rebooter** la carte sur blocage : c'est un **changement de comportement en
régime**, sur la story qui mesure précisément ce régime.
**Décision owner du 2026-08-26 : il RESTE non posé.** Conséquence, écrite plutôt que subie :
**une tâche bloquée sept jours n'entraîne AUCUN redémarrage, et `up` continue d'avancer.**
⇒ **c'est exactement le faux négatif que la triade de §25.1 existe pour rattraper.**

## 25.4 ✅ LE JOURNAL DU SOAK VIT CÔTÉ TOUR — ET SON VOLUME EST BORNÉ **AVANT** LE DÉPART (AC2.5)

⛔ **AUCUNE ÉCRITURE NVS/FLASH CÔTÉ CARTE (D4/D5).** Une semaine H24 est très exactement le régime
où une écriture périodique se paierait — mesuré : sous écriture flash, *« l'image défile »*, à
**165 343 o/s**.

🔴 **ET `--tracer-console` N'EST PAS L'INSTRUMENT DU SOAK.** Le cadrage de `dn4-5` annonçait
*« 232,0 o/s ⇒ ~140 Mo sur 7 jours »* (§13.11.1). **Le dépôt avait déjà corrigé ce chiffre** :
`dn_agent.py` écrit lui-même **447 à 530 o/s, soit 270 à 320 Mo sur 7 jours, sans aucune rotation**,
et conclut *« ⛔ Ne pas le laisser armé sur un soak »*. **Le cadrage sous-estimait d'un facteur ~1,9.**

⇒ **`--journal-soak FICHIER`** est un **canal DISTINCT**, ⛔ il ne remplace pas `--tracer-console`
(qui reste l'instrument de diagnostic de `dn4-18`, sur fenêtre courte) :

| | `--tracer-console` | `--journal-soak` |
|---|---|---|
| contenu | **tout** le fil, brut | battement · reboots · alarmes · **événements de port** |
| débit | **447-530 o/s** | ⚠️ **PLANCHER 18,3 o/s** · mesuré ailleurs à **157-163 o/s** |
| sur 7 jours | **270-320 Mo** | ⚠️ **PLANCHER 10,6 Mo** · ~**95-98 Mo** au débit haut |
| rotation | ⛔ aucune | ✅ 32 Mo × 4 crans ⇒ **rétention 160 Mo**, au-delà le DÉBUT est détruit |
| usage | diagnostic, fenêtre courte | **la boîte noire du soak** |

🔴 **CORRIGÉ LE 2026-08-28 (revue de code) — CETTE TABLE PUBLIAIT UN CHIFFRE QUE §25.8.3 RÉFUTE.**
Elle affichait `18,3 o/s` et `10,6 Mo sur 7 jours` **sans réserve**, pendant que §25.8.3 écrit
*« le volume de régime se mesurera **pendant le soak lui-même** ⛔ Aucun chiffre de volume de
régime n'est publié ici »*, et que le code lui-même porte les **deux** versions (`dn_agent.py`
docstring `~18 o/s` contre le bloc voisin `157 o/s ⇒ ~95 Mo sur 7 j, faux d'un facteur ~8,6`).
La gate, elle, requalifiait déjà 10,6 Mo en **« ⚠️ PLANCHER »**. ⇒ **Le plancher et le plafond de
rétention sont publiés, le chiffre unique ne l'est plus.** ⚠️ AC2.5 exige de borner **AVANT** de
lancer : ce qui borne n'est PAS le débit (inconnu), c'est la **rétention de 160 Mo** — et chaque
rotation l'écrit désormais dans le journal, sous l'étiquette `ROTATION`.

⚠️ **L'ÉCRÊTAGE EST DIT, JAMAIS SILENCIEUX** : un quota de 60 lignes « fil » par minute protège la
boîte noire d'une tempête d'erreurs, et **les lignes écartées sont comptées et publiées**
(`QUOTA  N ligne(s) ECARTEE(S)`). ⛔ Les **événements de port échappent au quota** — les perdre
reviendrait à rendre §25.3 indécidable.

⚠️ **LE FRAGMENT EST REPORTÉ** : une ligne de battement peut être coupée entre deux `read()`. Sans
report du reste, on en perdrait une de temps en temps, **en silence** — le piège exact que `dn4-18`
a payé sur son marqueur.

## 25.5 ✅ LE CUMUL « EN AMBIANT LA MAJORITÉ DU TEMPS » — IL N'EXISTAIT PAS (AC3.2)

Le brief exige *« en Ambient la majorité du temps »*. **> 50 % est un SEUIL**, ⛔ pas une figure de
style — et **aucun instrument ne le mesurait**.

🔴 **ET IL NE FALLAIT SURTOUT PAS COMPTER DES TICKS.** La tentation était `s_secondes_vues`. Le
dépôt dit lui-même, **dans sa propre sortie console**, que *« le tick 1 Hz ne bat pas pendant
`ui off` »*, et `dn_ui.c` documente que `veille now` passe **délibérément** à côté du tick
(*« un geste d'opérateur ne doit pas faire avancer une horloge d'observation »*). ⇒ un dénominateur
en ticks aurait des **trous**, et rendrait sur 7 jours **un pourcentage plausible et faux**.

⇒ **on cumule du TEMPS MURAL** (`esp_timer_get_time()`, int64), canalisé par **l'unique poseur de
mode** de `dn_veille.c` — vérifié par gate sur **tout le fichier** : `s_mode` n'est écrit qu'à
l'initialisation et dans `veille_poser_mode()`.

⚠️ **L'INTERVALLE EN COURS EST AJOUTÉ À LA LECTURE.** Sans lui, un module en Ambient depuis six
jours publierait le cumul de la **dernière bascule** — soit **« 0 % d'Ambient »** sur un critère qui
est en réalité tenu. **Le pire cas possible** : faux, plausible, et dans le sens qui fait échouer à
tort. Un mutant le montre (**3 240 s publiés au lieu de 23 240**).

⛔ **EN RAM (D4)** : le cumul ne survit pas au reboot — et un reboot rompt la fenêtre du soak de
toute façon (AC3.6).
⚠️ **CE QU'IL NE DIT PAS** : il dit **dans quel MODE le module se croit**, ⛔ pas que la dalle est
effectivement sombre. **Le constat owner reste requis.**

## 25.6 ✅ CE QUE LES GATES PROUVENT — 145 CONTRÔLES, SANS CARTE NI TOUR

🔴 **CHIFFRES REPRIS LE 2026-08-28 APRÈS LA REVUE DE CODE, ET LE PRÉCÉDENT ÉTAIT FAUX.** Cette
section publiait *« 120 CONTRÔLES »* et *« 112 sites »* : au tir réel du 2026-08-28, les huit gates
rendaient **124 OK et UN KO** — `audit_rebouclage_dn45.py` sortait en **exit 1** avec **six
compteurs NON CLASSÉS**, ajoutés par `dn3-3`/`dn4-19`/`dn4-20` **après** `dn4-5`. ⚠️ Aucun de ces
six ne reboucle en 7 jours : le défaut n'était pas un rebouclage, c'était que **l'instrument
d'AC1.1 ne décrivait plus le firmware qu'on s'apprêtait à geler — et qu'il le disait lui-même**.
C'était la **deuxième** dérive de cette table (la première réparée par `73a49ad`). Les chiffres
ci-dessous sont **tirés**, ⛔ pas recopiés.

| gate | ce qu'elle éprouve | contrôles |
|---|---|---|
| `tools/audit_rebouclage_dn45.py` | l'inventaire de rebouclage **mécanique** sur tout `main/` (**123 sites**) | **13** |
| `tools/verif_rebouclage_dn45.py` | la fenêtre en base 64 bits + **3 mutants vus rougir** | **30** |
| `tools/verif_cumul_ambient_dn45.py` | le cumul Ambient + le **seqlock par sa forme** + **2 mutants vus rougir** | **23** |
| `tools/verif_journal_soak_dn45.py` | la boîte noire, **y compris ses propres chemins de panne** | **27** |
| `tools/verif_bme680_retard_dn45.py` | le miroir console↔docblock + **1 mutant vu rougir** | **15** |
| `tools/verif_dossier_d5_dn45.py` | le balayage D5 sur **les deux dépôts** | **10** |
| `tools/verif_d4_nvs_dn45.py` | les écrivains NVS (**4**), chacun avec son déclencheur | **6** |
| `tools/verif_lissage_dn45.py` | le lissage + la **borne d'âge** d'AC4.3 + **4 mutants vus rougir** | **21** |

**TOTAL : 145 contrôles au vert, 0 KO, 10 mutants vus rougir** — les huit gates sortent en `exit 0`.

⛔ **CE QUE CES 145 CONTRÔLES NE PROUVENT PAS** : que la carte tient sept jours. Ils prouvent que
**l'instrument qui le dira ne ment pas**. C'est tout — et c'est ce qui manquait.
⛔ **ET UNE CHOSE QU'ILS NE PROUVENT TOUJOURS PAS, ÉCRITE PLUTÔT QUE TUE** : le **seqlock** de
`dn_veille_cumul()` est vérifié **par sa FORME**, ⛔ pas par son effet. Un banc séquentiel
**n'exerce pas une course** : le mutant « seqlock retiré » a été construit, il s'applique, il
compile, et il rend **le même chiffre**. Le garder aurait donné une gate rouge en permanence ;
l'inverser pour la faire passer aurait épinglé **vert une absence de preuve**. Il a donc été
**retiré et son échec est écrit dans la gate**.
⚠️ **ET AUCUN D'EUX N'A VU LE SILICIUM.** Quatre choses restent dues **sur la carte** : la capture
de `gel` (AC2.2), le témoin de péremption **sur la carte** (AC4.3), l'A/B à l'œil (AC4.4) et les
Δ px / Δ latence (AC4.5).

## 25.7 ✅ D4 EST **VÉRIFIÉ**, ⛔ PAS AFFIRMÉ — LES **QUATRE** ÉCRIVAINS, ET LEUR DÉCLENCHEUR (AC9)

🔴 **L'INSTRUMENT QUI EXISTAIT NE COUVRAIT QU'UN SEUL ÉCRIVAIN.** La commande `veille` publie
*« aucune écriture NVS depuis le boot ou le dernier `veille reset` »* — mais elle ne connaît que
`dn_veille`. Un verdict fondé sur elle seule serait **LOCAL, pas global** : *« une gate scopée à UNE
fonction peut épingler VERT le même défaut ailleurs »*.

🔴 **ET L'INSTRUMENT QUI A REMPLACÉ CELUI-LÀ AVAIT LUI AUSSI UN ANGLE MORT — TROUVÉ LE 2026-08-28.**
Le balayage cherchait **sept** primitives, et `nvs_flash_erase` n'en faisait pas partie : ni
`"nvs_erase"` ni `"esp_flash_erase"` n'est une **sous-chaîne** de `nvs_flash_erase` (vérifié :
`[p for p in PRIMITIVES if p in "nvs_flash_erase"]` rendait `[]`). ⇒ `desknode_main.c` **effaçait
la partition NVS ENTIÈRE** sans que l'inventaire le voie, et cette page publiait *« trois
écrivains »*. ⚠️ **La substance de D4 tenait** — ce chemin est un `nvs_flash_init()` en échec **au
boot**, donc hors régime ; ce qui était en défaut, c'est **l'inventaire**, et un inventaire
incomplet rend le verdict d'AC9.1 **local, pas global** : exactement ce qu'AC9.2 interdit.
⚠️ **Le site existait déjà à `c31bb97`** : ⛔ ce n'est **pas** une régression post-`dn4-5`.

🎯 **ET LA PRIMITIVE AJOUTÉE A IMMÉDIATEMENT ACCUSÉ DU CODE SAIN** : le balayage a classé
`dn_console.c` comme écrivain, alors que ses deux seules occurrences sont un `printf(...)` qui
**explique** à l'opérateur ce qu'est un `nvs_flash_erase()` au boot, et un commentaire. ⇒ le
balayage blanchit désormais **les littéraux de chaîne** en plus des commentaires. **Une gate qui
prend une MENTION TEXTUELLE pour un APPEL accuse du code sain** — c'est la faute symétrique de
*« une gate verte sur du code faux »*, et elle a la même racine : lire du **texte** là où on croit
lire du **code**.

⇒ balayage de **tout** `firmware/desknode/main/` sur les **huit** primitives d'écriture
(`nvs_set_*`, `nvs_commit`, `nvs_erase*`, **`nvs_flash_erase`**, `esp_partition_write/erase`,
`esp_flash_write/erase`), **commentaires et chaînes blanchis** :

| fichier | appels | déclencheur | en régime ? |
|---|---|---|---|
| `desknode_main.c` | **1** | `nvs_flash_erase()` — **efface la partition ENTIÈRE**. Déclencheur : `nvs_flash_init()` qui rend `NO_FREE_PAGES`/`NEW_VERSION_FOUND` **au boot** | ⛔ **non** |
| `dn_bootcfg.c` | **16** | console (`set fbs\|bounce\|lines\|drawmem\|core`, `cfg reset`, **`cfg repli clear`**) — **ET un chemin de BOOT** | ⛔ **non** |
| `dn_stimulus.c` | **2** | `esp_partition_write` du **stimulus flash**, armé par `flash on` **uniquement** | ⛔ **non** |
| `dn_veille.c` | **2** | persistance des **deux réglages** de veille, sur un **geste** (tap MENU / `veille`) | ⛔ **non** |

⚠️ **DEUX CHIFFRES DE CETTE TABLE AVAIENT DÉRIVÉ** : `dn_bootcfg.c` publiait **4** appels, il y en a
**16** au HEAD, et un déclencheur console ajouté **après** `dn4-5` n'était pas nommé —
`cfg repli clear` → `dn_bootcfg_clear_repli()` (`nvs_erase_key` ×3 + `nvs_commit`). ✅ **Le COMPTE
avait dérivé, ⛔ pas le VERDICT** : vérifié, **aucun chemin de RÉGIME n'a été introduit**
(`dn_bootcfg_note_repli` n'est appelé que depuis `desknode_main.c:315`, `dn_veille` n'écrit que par
`dn_veille_armer`/`dn_veille_cran` et **jamais** depuis `veille_poser_mode()`, et `dn_env.c`
n'appelle **aucune** primitive NVS).

⚠️ **LE CHEMIN DE BOOT EST NOMMÉ PLUTÔT QUE TU** : `desknode_main.c` **corrige la NVS** quand
`bounce_px` **ne s'alloue pas** (repli `dn4-10` du 2026-08-23). Il est **conditionnel**, il tombe
**avant** que le régime commence, et **il s'auto-éteint** — le boot suivant est propre.

⚠️ **`hist` RESTE EN RAM, ET LE DIT LUI-MÊME** : *« EN RAM, ⛔ AUCUNE écriture NVS/flash (D4) »*.
⇒ l'historique de session **ne survit pas au reboot, et c'est VOULU** — à rappeler dans le journal
du soak.

⛔ **CE QUE CETTE GATE NE PROUVE PAS** : que rien n'a été écrit **pendant** le soak. Elle prouve que
**les seuls chemins d'écriture qui existent** sont hors régime. La vérification de terrain est
**AC9.1** — relire `veille` **à la fin du soak, sur la carte**.

## 25.8 🔴 SÉANCE DU 2026-08-26 (SUITE) — TROIS CHOSES QUE LA CARTE A APPRISES AU DOSSIER

### 25.8.1 ✅ **RENDRE LE PORT À L'AGENT REDÉMARRE LA PUCE** — mesuré, 3 occurrences

Le dossier portait ce soupçon **depuis le 2026-08-16** sans jamais l'avoir établi : *« la parade
DTR/RTS est WINDOWS-ONLY, et le côté Windows n'a jamais été validé par A/B »*.

| # | avant le passage à l'agent | après | cause publiée |
|---|---:|---:|---|
| 1 | `up 5780 s` | **`up 160 s`** | `reset: USB` |
| 2 | `up 160 s` | **`up 40 s`** | `reset: USB` |
| 3 | (jambe de contrôle) | **bandeau de boot complet dans le journal** | idem |

🎯 **ET C'EST LA GARDE D'AC1.4/AC1.5 QUI L'A ATTRAPÉ.** Sans `up`/`mural`/`reset:` au battement,
la première jambe de mesure aurait été publiée : `flush reset` avant le passage, compteurs **remis à
zéro par le reboot**, et un Δ px calculé sur des compteurs qui ne couvraient pas ce qu'on croyait.
⛔ **Silencieux, plausible, faux.**

⇒ **CONSÉQUENCE DE MÉTHODE, À APPLIQUER** : ⛔ **un `flush reset` avant un passage de port ne sert à
rien.** Le reboot fait le zéro lui-même, à l'instant où l'agent ouvre. La fenêtre utile part donc
**du boot**, et toute comparaison A/B doit avoir **des fenêtres de même longueur** — ce que la
première tentative n'avait pas (145 s contre 228 s, la queue inactive valant 25 s d'un côté et 108 s
de l'autre). **Ce Δ px n'a pas été publié : il aurait mesuré ma lenteur, pas le lissage.**

### 25.8.2 🔴 LA BOÎTE NOIRE JETAIT LE SIGNAL POUR GARDER SON PROPRE BRUIT

**Mesuré sur 120 s de régime réel** : le journal a écrit **18 873 o = 157 o/s**, là où le banc
prédisait **18,3 o/s** — **faux d'un facteur ~8,6**. Et le quota a jeté **437 lignes en deux
minutes**, en le disant.

**Ce qui saturait le quota était l'agent lui-même** : le REPL **renvoie en écho** chaque trame
`pc $DN,...` — cinq par seconde — entrelacée d'invites `desknode> `.
🔴 **La vraie faute était la conséquence** : *une anomalie **réelle** pouvait être écartée par le
quota parce que l'écho l'avait saturé.* Un instrument qui jette le signal pour garder son propre
bruit ne protège rien.
⇒ **l'écho est FILTRÉ, ⛔ plus écrêté** — et il reste **compté et dit** (ligne `MINUTE`) : un écho
qui s'effondrerait dirait que **la carte ne reçoit plus rien**, et ce serait une information.

⚠️ **ET LE FILTRE A DÛ ÊTRE REPRIS UNE SECONDE FOIS, PAR LA MESURE.** Ancré en début de ligne, il
ratait `desknode> desknode> c $DN,3,126,...` — la trame avait été **coupée entre deux `read()`** et
le `p` de `pc` était parti dans l'autre morceau. **Un filtre qui ne tient pas sur un fragment ne
tient pas du tout** : le fil en produit en permanence.

### 25.8.3 ⛔ ET LE VOLUME NE S'EXTRAPOLE PAS D'UNE FENÊTRE QUI CONTIENT UN BOOT

Après filtrage, la mesure suivante donnait **encore 163 o/s**. En regardant **ce que c'était** :
le **bandeau de boot** (avertissements `dn_ui`/`dn_env`/`dn_rtc`, texte d'accueil du REPL) — parce
que le passage de port avait **encore** redémarré la carte.
🔴 **Un bandeau de boot est un ÉVÉNEMENT PONCTUEL, ⛔ pas un débit.** Multiplier 163 o/s par 7 jours
revient à facturer 6 048 boots. **Le « ~95 Mo sur 7 jours » que j'avais écrit une heure plus tôt est
donc faux à son tour**, et pour une raison différente de la première.
⇒ **le volume de régime se mesurera sur une fenêtre SANS reboot** — c'est-à-dire pendant le soak
lui-même. ⛔ Aucun chiffre de volume de régime n'est publié ici.

---

# §26. 🔴 `dn4-22` (P9.13) — LA DALLE SE DÉCHIRE PARCE QUE LA **MARGE** A ÉTÉ DÉPENSÉE, ⛔ PAS PARCE QU'UNE LIGNE COÛTE

> **Séance du 2026-08-28**, `dn4-22`. Captures : `mesures/dn4-22/` (⚠️ la séance du 28/08 au matin
> n'en avait laissé **aucune** — ce n'est plus le cas).
> ⚠️ **Cette section CORRIGE des verdicts consignés.** Voir §26.6, « ce que ça ne prouve pas », et
> §26.7, « ce que ça retire au dossier ».

## 26.1 🎯 CE QUE LA SÉANCE ÉTABLIT, EN QUATRE LIGNES

1. **La régression d'affichage est RÉELLE** — ⛔ pas un artefact d'instrument — et elle vit **dans
   `f7be23c`** : les dix commits suivants n'ajoutent rien.
2. **Le mécanisme est une MARGE DE FAMINE DMA CONSOMMÉE, ⛔ pas une ligne coûteuse.** `0ced322`
   garde ~400 µs de marge sous le seuil quoi qu'on lui fasse ; `f7be23c` est **à la limite sans
   charge** et **franchit sous charge**.
3. **La charge de l'agent réel est un CO-FACTEUR NÉCESSAIRE.** ⛔ Ça **réfute** l'élimination
   *« l'agent / le trafic série est éliminé »* du `[CC]` D17.
4. **Il n'y a pas UN site.** Trois fichiers contribuent, par **trois voies différentes**, et
   **aucun ne suffit seul**.

## 26.2 ⚠️ LE PROTOCOLE — ET POURQUOI IL A DÛ CHANGER

🔴 **Rendre le port à l'agent REDÉMARRE la puce** (§25.8.1, 3 occurrences le 26/08 ; **4ᵉ mesurée le
28/08** : fenêtre `flush` 96 489 ms avant, **130 792 ms** après, et `applications` retombé de 10 à 2).
⇒ **toute fenêtre « agent réel » CONTIENT un boot**, donc `ph_ref` y est **semée au boot**.

**Ce que ça coûte, mesuré sur `0ced322` (un seul binaire) :**

| RAZ | `ph_ref` relevées | étendue | seau 10 % |
|---|---|---|---|
| **`flush reset` EN RÉGIME** | 2262 · 2261 | **1 µs** | 4,5 % des trames |
| **semée au BOOT** | **2359** · 2261 · 2259 · 2260 | **100 µs** | **99,98 %** puis 3,0-4,5 % |

⇒ 🔴 **le semis au boot est une LOTERIE — 1 pathologique sur 4** — et quand il l'est, le seau 10 %
vaut ~`n`. **AC3.3 (`flush reset` en régime) n'est pas une précaution : c'est la condition de
comparabilité.** ⛔ **Aucun des huit points de la table d'A/B du `[CC]` D17 ne la respecte, et aucun
ne publie `ph_ref`.**

**⇒ DEUX PROTOCOLES, ET LES DEUX SONT PUBLIÉS :**

| | régime | RAZ | ce qu'il vaut |
|---|---|---|---|
| **injecté** | `dn_console.py "pc $DN,…"`, **5,00 trames/s** (la cadence réelle de l'agent), **valeurs variables** | `flush reset` **en régime** *ou* boot | ✅ **défendable** — ⛔ **le PC n'est pas mesuré** |
| **agent réel** | `dn_agent.py` sur la tour, `COM3` natif | **le boot** que la remise du port provoque | ✅ **comparable à la table du `[CC]`** — ⚠️ biais de référence **déclaré** |

⛔ **« Agent réel » et « topologie du port » ne sont PAS séparés par cette séance** : en agent réel
le port est `COM3` **natif Windows**, en injecté il est **usbipd→WSL**. Les deux changent ensemble.
⇒ ce que la séance nomme est **« la charge de l'agent »**, ⛔ pas « le trafic série ».

## 26.3 📊 LA MATRICE — 8 BINAIRES, 3 FICHIERS, **AGENT RÉEL**, FENÊTRES DE ~306 s

| binaire | `dn_env` | `dn_ui` | `dn_console` | image (o) | pire déficit | 25 % | 50 % | 🔴 **100 %** |
|---|:-:|:-:|:-:|---:|---:|---:|---:|---:|
| `0ced322` | — | — | — | 1 167 553 | 241 µs | *417*⚠️ | **0** | **0** |
| ARM 4 | ✓ | — | — | 1 167 561 | 645 µs | 5 | 3 | **0** |
| ARM 5 | ✓ | ✓ | — | 1 168 081 | 1 300 µs | 2 | 2 | **1** |
| ARM 6 *(= ARM 5)* | ✓ | ✓ | — | 1 168 081 | — | 1 | 1 | **0** |
| ARM 7 *(ARM 5 + 1 236 o MORTS)* | ✓ | ✓ | *(bourrage)* | **1 169 317** | **125 µs** | **0** | **0** | **0** |
| **ARM 8** | ✓ | — | **✓** | 1 168 613 | 1 095 µs | **39** | **22** | 🔴 **9** |
| **`f7be23c`** | ✓ | ✓ | **✓** | 1 169 145 | 896 µs | 253 | 248 | 🔴 **245** |
| **`156b507`** | ✓ | ✓ | **✓** | 1 169 145 | 900 µs | 75 | 74 | 🔴 **74** |

*(⚠️ le `417` de `0ced322` vient de sa fenêtre à **référence pathologique** — sur-comptage sur toutes
les trames ; ses seaux **50 %** et **100 %** sont à **0**, et ce `0` tient **a fortiori** puisque le
biais ne peut que **fabriquer** de la corruption.)*

🔴 **SANS `dn_console.c`@`f7be23c` : `0 · 0 · 1 · 0 · 0`** — cinq fenêtres, quatre binaires.
🔴 **AVEC : `9 · 245 · 74`** — trois fenêtres, trois binaires.
⇒ **son retrait fait retomber le compteur, sa remise le fait remonter. Les DEUX SENS sont prouvés —
au niveau FICHIER.**

**Et sous protocole INJECTÉ (fenêtres de 450 s), la marche existe aussi, en plus fin :**

| binaire | `0ced322` | `f7be23c` | `156b507` |
|---|---|---|---|
| pire déficit | **376 µs** | **779 µs** ⚠️ *(+4 au-dessus du seuil)* | **777 µs** *(+2)* |
| CORRUPTION | **0** | **1** | **1** |

⇒ **`f7be23c` reproduit `156b507` à 2 µs près** (bruit mesuré : **41 µs**), et `0ced322` est
**400 µs plus bas**. **Le périmètre `0ced322..f7be23c` du `[CC]` D17 est ÉTABLI PAR LA MESURE**,
⛔ plus seulement par l'A/B non contrôlé du 28/08.

## 26.4 🎯 LE MÉCANISME — TROIS CONTRIBUTIONS, TROIS VOIES, AUCUNE NE SUFFIT

| contribution | par quelle voie | mesuré |
|---|---|---|
| **`dn_env.c`** | son **EXÉCUTION** (`dn_env_cycle()`, 5 s, tâche `dn_capt`) | pire déficit **241 → 645 µs** sous agent, **pour +8 OCTETS d'image** ⇒ ⛔ ce n'est pas la taille |
| **`dn_ui.c`** | son **empreinte / placement** (+520 o) | seul avec `dn_env` : **encore propre** (0-1). **Amplificateur** en présence de `dn_console` : **9 → 74-245** (×8 à ×27) |
| **`dn_console.c`** | son **placement** (+1 064 o **répartis dans ses fonctions**) | 🔴 **NÉCESSAIRE** : sans lui **jamais**, avec lui **toujours** |
| **la charge de l'agent** | co-facteur **NÉCESSAIRE** | injecté **0-1** · agent réel **9-245** |

🔴 **ET LE POINT QUI FERME LE RAISONNEMENT** : le diff de `dn_console.c` a été **relu ligne à ligne**
(⛔ pas récité) — il est **entièrement** dans `cmd_bl`, `cmd_veille`, `bl_auto_etat` et `bl loi`.
⛔ **Aucun de ces chemins ne s'exécute pendant une fenêtre de mesure** : l'agent ne tape ni `bl` ni
`veille`, seulement `rtc`. ⇒ **`dn_console.c` NE PEUT PAS coûter de temps CPU. Son seul effet
possible est de DÉPLACER le code qui suit dans l'image.**

### 26.4.1 ⛔ LE **VOLUME** EST RÉFUTÉ PAR TÉMOIN DIRECT — le placement fin, NON

**ARM 7 = ARM 5 + exactement 1 236 octets de `.text` MORT**, posés **dans `dn_console_banner()`**
(fonction réellement appelée) derrière `static volatile int dn422_jamais_vrai = 0;`.
**Image : 1 169 317 o — PLUS GROSSE que `f7be23c` (1 169 145).**
⇒ **la fenêtre la plus PROPRE de toute la campagne** : `CORRUPTION 0`, pire déficit **125 µs**,
**650 µs de marge (83 %)**.

⇒ ⛔ **F-B « le VOLUME » est MORTE.** ⚠️ **MAIS le bourrage est UN SEUL bloc en fin d'unité**, là où
`f7be23c` **répartit** sa croissance **DANS** ses fonctions. ⇒ **le VOLUME est réfuté ; le PLACEMENT
FIN ne l'est pas.** *(Limite écrite AVANT la mesure.)*

🔴 **PIÈGE PAYÉ AU PASSAGE — L'ARM 6 A ÉTÉ PERDU.** Sa première version posait `.space 1064` dans une
fonction `__attribute__((used, noinline))` **jamais appelée** : ESP-IDF compile en
`-ffunction-sections` et lie en `--gc-sections` ⇒ **le linker l'a supprimée** (`nm` : symbole absent
de l'ELF, image **identique** à l'arm 5). ⛔ `used` ne lie que le **compilateur**.
⚠️ **Sans la relecture de la taille AVANT de conclure, un « propre » aurait été publié comme
réfutation de la taille alors que le témoin n'existait pas dans le binaire mesuré.**

## 26.5 🎯 CE QUE ÇA RÉSOUT — LE PARADOXE DU CADRAGE

Le `[CC]` D17 avait dressé **l'inventaire exécutable complet de `f7be23c` — 17 sites numérotés** —
et conclu, à juste titre, qu'**aucun ne tourne sur un chemin chaud** : le seul périodique
(`dn_env_cycle()`, 5 s) était éliminé, et le relevé le plus sale avait été pris **écran statique**.
Il en tirait que *« chercher la ligne coûteuse est une impasse »*.

🎯 **C'était exact, et pour la bonne raison : IL N'Y A PAS DE SITE.** Le cadrage cherchait une ligne
qui coûte ; il n'y en a pas. Il y a **une marge de famine DMA d'environ 400 µs, dépensée par trois
causes distinctes, dont DEUX ne sont pas de l'exécution.**

⇒ **AC1.4 (« la cause est désignée par UN SITE, prouvée par SON retrait ») est INATTEIGNABLE tel
qu'écrit** — ⛔ pas parce que la chasse a échoué, mais parce que **la cause n'a pas la forme que
l'AC suppose**. C'est **AC1.6**, et un **`[CC]`** est posé.

## 26.6 🎯 LE REMÈDE — **XIP DEPUIS LA PSRAM**, ET IL NE TOUCHE AUCUNE LIGNE DE `f7be23c`

**Décision owner du 2026-08-28.** La cause étant une **marge dépensée par le placement**, ⛔ il n'y a
aucune ligne à retirer. On rend la marge **en supprimant le mécanisme** : sortir le code et les
constantes de la flash, donc **de SPI0**, que la DMA du panneau partage (§5.3, §11.4).

**ARM 9 = `156b507` + `sdkconfig.defaults.xip-lecture-code`.**
⛔ **SANS `sdkconfig.defaults.ac5-double-tampon`**, que le mode d'emploi de la branche associe : il
pose `num_fbs = 2`, et **`dn4-22` s'interdit nommément de toucher `num_fbs`**.

| | `156b507` seul | 🎯 **`156b507` + XIP** |
|---|---|---|
| **injecté**, 450 s — pire déficit | **777 µs** *(dépassé de 2)* | **176 µs** — **599 µs de marge (77 %)** |
| **injecté** — CORRUPTION | 1 | **0** |
| **agent réel**, ~305 s — pire déficit | **900 µs** *(dépassé de 125)* | **121 µs** — **654 µs de marge (84 %)** |
| **agent réel** — 🔴 **CORRUPTION** | 🔴 **74** | 🎯 **0** |
| seaux 10 / 25 / 50 % | 463 / 75 / 74 | **144 / 0 / 0** |
| `ph_max − ph_ref` | 27 µs | **9 µs** |
| duty relu | 80 % (237 lx) | **80 %** (130 lx) |

🎯 **ET C'EST MIEUX QUE `0ced322` LUI-MÊME** (pire déficit **241 → 121 µs**). ⇒ **XIP ne MASQUE pas,
il RÉTABLIT la marge** : la population de phases se **resserre** (`ph_max − ph_ref` divisé par 3) et
le seau 10 % **s'effondre de 463 à 144**. **La contention SPI0 était bien le mécanisme.**

**Coût mesuré (`mem`, sur la carte)** : PSRAM libre **6 655 456 o**, pool après copie du code
**7 272 536 o** (contre 8 Mo de puce) ⇒ **≈ 1,08 Mo de PSRAM** pour le code + `.rodata` copiés.
Le framebuffer prend **614 760 o** (théorie 614 400). ⛔ **Aucune marge en danger.**
⚠️ Image : **1 171 645 o** (+2 500 vs `156b507`) — le code reste **stocké** en flash, il est
**copié** en PSRAM au boot. ⇒ ⛔ **`idf.py size` NE PEUT PAS dire si XIP est armé.**

### 26.6.1 🔴 LE BANDEAU **MENT SUR XIP** — défaut d'étiquette, à corriger

`desknode_main.c` imprime *« config : XIP depuis la PSRAM **désactivé** (branche « sans » d'AC6) »*
**alors que XIP TOURNE**. Il teste `CONFIG_SPIRAM_XIP_FROM_PSRAM` — le symbole **parapluie**, non
posé — au lieu des deux symboles que la branche pose réellement, tous deux à `y` :
`CONFIG_SPIRAM_FETCH_INSTRUCTIONS` et `CONFIG_SPIRAM_RODATA`.

✅ **LA PREUVE D'EXÉCUTION, ⛔ pas l'étiquette** — dans le log de boot :
```
I (307) mmu_psram: Read only data copied and mapped to SPIRAM
I (375) mmu_psram: Instructions copied and mapped to SPIRAM
```

⚠️ **ET ÇA JETTE UNE RÉSERVE SUR §11.4** : la réfutation de XIP par `dn1-3` (« ❌ identique ») a été
faite avec **ce même fichier de branche**, donc avec **ce même bandeau menteur**. ⛔ **Impossible de
savoir rétroactivement si XIP y était réellement armé** — les captures de l'époque ne sont pas
au dépôt. ⇒ **la ligne 6 du tableau des sept causes de §11.4 est à considérer comme NON ÉTABLIE**
tant qu'elle n'est pas re-tirée avec la preuve `mmu_psram` au boot.

### 26.6.2 ✅ AC3.1 / AC3.5 — LE COMPTEUR RETOMBE, **DEUX FOIS**, ET L'ÉTENDUE VAUT `0`

| `156b507` + XIP, **agent réel** | fenêtre 1 | fenêtre 2 | **fenêtre du constat owner** |
|---|---|---|---|
| durée | 304 587 ms | 307 977 ms | **284 172 ms** |
| `ph_ref` / `ph_max` | 2259 / 2268 | 2260 / 2268 | 2258 / 2265 |
| **pire déficit** | **121 µs** | **121 µs** | **120 µs** |
| seau 10 % | 144 | 92 | 103 |
| seaux 25 / 50 / **100 %** | 0 / 0 / **0** | 0 / 0 / **0** | 0 / 0 / **0** |
| duty **relu** | 80 % (130 lx) | 80 % (239 lx) | **80 % (372 lx)** |

🎯 **Trois fenêtres, trois lumières très différentes (130 · 239 · 372 lx), et le pire déficit vaut
121 · 121 · 120 µs.** ⇒ **l'étendue du bras remède est `0` sur CORRUPTION et `1 µs` sur le pire
déficit** — la mesure la plus reproductible de toute la campagne, et **très largement sous le seuil
de `4`** d'AC3.1.

## 26.7 ✅ AC4 — LE CONSTAT OWNER, **VERBATIM**

**2026-08-28, ~14:56.** Binaire `156b507` + XIP, **agent réel** (PID 19492), régime depuis 14:52:30.

> **« non plus rien c'est nickel ya meme plus l'artefact sur le detail cpu c'est genial ! »**

🎯 **ET IL DONNE PLUS QUE CE QUI ÉTAIT DEMANDÉ** : *« ya même plus l'artefact sur le détail CPU »* —
un défaut **hors périmètre de `dn4-22`**, jamais nommé dans le cadrage, que le remède **fait
disparaître aussi**. ⇒ **renfort majeur du mécanisme** : si un artefact d'une AUTRE vue tombe avec
le même correctif, c'est que la contention SPI0 le nourrissait lui aussi.
⛔ **Ce n'est PAS une preuve** pour ce défaut-là (aucun instrument ne l'a mesuré) — **entrée ledger**.

### Les conditions, **RELUES** (AC4.2) — ⛔ pas supposées

| | |
|---|---|
| SHA | `156b507`, **lu au bandeau** · XIP prouvé par `mmu_psram` au boot (§26.6.1) |
| duty | **80 %**, **relu** (`rétroéclairage : 80 % à 24000 Hz`) |
| lux | **372 lx** (BH1750, âge 2 061 ms) |
| servo | **ARMÉ** · `applique : 80 % (sur 372 lx)` · `applications : 1 depuis le boot` |
| loi en vigueur | **`20 % à ≤ 2 lx · 80 % à ≥ 11 lx`, courbe log** — ⚠️ **les bornes de `dn4-20`** |
| veille | **`mode : AMBIENT` · ARMÉE · délai 1 min** |
| agent | **1 361 trames valides**, 13 pertes seq |
| compteur de LA fenêtre observée | **CORRUPTION 0**, pire déficit **120 µs** |

### ⚠️ DEUX CONDITIONS QUI N'AVAIENT PAS ÉTÉ RELEVÉES — et elles sont écrites (règle n°3)

1. 🔴 **`156b507` porte les bornes de `dn4-20`** (20 / 80 / 2 lx / 11 lx) là où **`0ced322` et
   `f7be23c` portent celles de `dn4-19`** (8 / 100 / 20 lx / 600 lx). ⇒ **à servo ARMÉ, le duty
   n'était PAS le même d'un binaire à l'autre** : les fenêtres agent ont tourné entre **64 % et
   86 %**. ⛔ **Ça ne casse pas la conclusion** — le duty est éliminé comme cause par la mesure du
   `[CC]`, et **la comparaison du remède (`156b507` ± XIP) est à duty IDENTIQUE (80 %)** — mais
   **c'est un écart, et il est déclaré**.
2. ⚠️ **La carte était en `mode : AMBIENT`** au relevé (délai de veille **1 min** sur `156b507`,
   contre 10 min sur `0ced322`). ⛔ **Sans effet visuel** ici — `ambiant : échelle 100 % de la loi`
   ⇒ Ambient rend le même niveau qu'Actif — mais **le mode exact à l'instant où l'œil a jugé n'est
   pas capturé**.

## 26.8 📊 LA TABLE D'A/B DU `[CC]` D17 — CE QU'ELLE VAUT APRÈS CETTE SÉANCE

| Binaire | Duty | Agent | CORRUPTION *(28/08)* | **re-tiré le 28/08 après-midi** |
|---|---|---|---:|---|
| `92e67b5` | 10 % | oui | **0** | ⛔ non re-tiré |
| `1871904` | 17 % | oui | 14 | ⛔ non re-tiré |
| `0ced322` | 45 % | oui | **4** | 🎯 **0** *(agent réel, 306 s)* |
| **`f7be23c`** | 45 % | oui | **130** | 🎯 **245** *(agent réel, 306 s)* |
| `a445761` + `156b507` | 80 % | oui | 219-255 | 🎯 **74** *(agent réel, 306 s)* |
| `156b507` | 10 % | **non**, statique | **332** | ⛔ non re-tiré |
| `f8d5813` | 80 % | oui | 181 | ⛔ **commit pendant**, ⛔ non re-tiré |
| `0ced322` (78 lx) | 45 % | oui | **0 / 510 s** | cohérent avec le **0** re-tiré |

⚠️ **BRUIT DÉCLARÉ DU `[CC]`** : **219 / 255 / 332** sur des conditions **nominalement identiques**.
🎯 **Cette séance le confirme** : `f7be23c` rend **245** et `156b507` rend **74** — **le même
groupe**, à un facteur 3,3. ⛔ **74 et 245 NE SE DISTINGUENT PAS.** Ce qui se distingue, c'est
**`0-1` contre `9-245`** — **deux ordres de grandeur**, exactement le **fait 5** du cadrage.

🎯 **LES CINQ CHIFFRES D'INSTRUMENT, POUR CHAQUE POINT RE-TIRÉ** (AC3.2) — ⛔ aucun `CORRUPTION` nu :

| binaire · protocole | `ph_ref` | `ph_max` | `ph_n` | `ph_degrossi_n` | `t_demi` | RAZ | 🔴 CORR. |
|---|---:|---:|---:|---:|---:|---|---:|
| `0ced322` · injecté · reset régime (A) | 2262 | 2316 | 12 497 | 32 | 775 | **02:59:37** | **0** |
| `0ced322` · injecté · reset régime (B) | 2261 | 2288 | 12 498 | 32 | 775 | **03:05:13** | **0** |
| `0ced322` · injecté · boot (C) | 2260 | 2310 | 16 149 | 32 | 775 | boot 03:11:13 | **0** |
| `0ced322` · injecté · boot (d′) | 2261 | 2311 | — | 32 | 775 | boot | **0** |
| `0ced322` · **agent** · boot (b′) | **2379** | 2327 | — | 32 | 775 | boot | **0** ⚠️ |
| `f7be23c` · injecté · boot (d″) | 2260 | 2316 | — | 32 | 775 | boot | **1** |
| `f7be23c` · **agent** · boot (b″) | 2260 | 2287 | — | 32 | 775 | boot | **245** |
| `156b507` · injecté · reset régime (a) | 2259 | 2290 | 12 497 | 32 | 775 | **11:03:00** | **0** ⚠️ |
| `156b507` · injecté · boot (d) | 2261 | 2281 | — | 32 | 775 | boot | **1** |
| `156b507` · **agent** · boot (b) | 2264 | 2281 | 11 331 | 32 | 775 | boot | **74** |
| **`156b507`+XIP · agent** (1) | 2259 | 2268 | — | 32 | 775 | boot | 🎯 **0** |
| **`156b507`+XIP · agent** (2) | 2260 | 2268 | — | 32 | 775 | boot | 🎯 **0** |
| **`156b507`+XIP · agent** (owner) | 2258 | 2265 | — | 32 | 775 | boot | 🎯 **0** |

⚠️ La ligne **(b′)** porte **`ph_ref > ph_max`** ⇒ *« RÉFÉRENCE AU-DESSUS DU MAX »*, **SUR-comptage**.
Elle est publiée **parce qu'elle rend `0`** : un biais qui **fabrique** de la corruption n'en a
fabriqué **aucune** ⇒ le `0` tient **a fortiori**. ⛔ **La réciproque serait irrecevable.**
⚠️ La ligne **(a)** est **HORS SUJET** : `bl 80` y **désarmait le servo**, or les 17 sites vivent
dans le chemin du rétroéclairage ⇒ **elle mesure un binaire dont la machinerie suspecte est
éteinte**. Elle est **conservée pour ce qu'elle démontre**, ⛔ pas comme point d'A/B.

## 26.9 ⛔ CE QUE ÇA NE PROUVE PAS

1. ⛔ **« La marche vient d'UN SITE. »** Elle ne vient d'aucun site. **`dn_console.c` est
   nécessaire**, `dn_ui.c` **amplifie**, `dn_env.c` **consomme par exécution** — et **aucun ne
   suffit seul**. **AC1.4 est NON ATTEINT**, déclaré.
2. ⛔ **« L'agent réel est la cause. »** Il est **co-facteur NÉCESSAIRE**, ⛔ pas cause : `0ced322`
   **avec** agent rend **0**. ⚠️ **Et « agent réel » n'est PAS séparé de « topologie du port »** —
   `COM3` natif Windows contre usbipd→WSL changent **ensemble**.
3. ⛔ **« Le placement fin est réfuté. »** ⛔ **NON.** L'arm 7 réfute le **VOLUME** (1 236 o morts,
   image **plus grosse** que `f7be23c`, **propre**) — mais son bourrage est **UN BLOC en fin
   d'unité** là où `f7be23c` **répartit** sa croissance **dans** ses fonctions.
4. ⛔ **`n = 1` sur les binaires SALES.** `f7be23c` (245), `156b507` (74) et ARM 8 (9) n'ont **UNE
   fenêtre agent chacun**. Les binaires **propres** ont, eux, **5 fenêtres sur 4 binaires**.
5. ⛔ **Le chemin d'APPLICATION du servo n'a JAMAIS été exercé** : toutes les fenêtres à servo armé
   affichent `applique : AUCUNE application depuis le dernier armement` (lumière stable, bande
   morte). ⇒ **une classe entière de comportement reste non mesurée.**
6. ⛔ **Le duty n'était pas constant entre binaires à servo armé** (64 % à 86 %), parce que
   `156b507` porte les bornes de `dn4-20` et les autres celles de `dn4-19`. ✅ **La comparaison du
   remède est, elle, à duty identique.**
7. ⛔ **Les quatre points de la table du `[CC]` NON re-tirés** (`92e67b5`, `1871904`, `156b507`
   statique, `f8d5813`) restent **sans `ph_ref`** ⇒ **incomparables**, et le **332** ⛔ n'est pas
   expliqué.
8. ⛔ **La fenêtre injectée de l'arm 5 est PERDUE** (capture série tronquée, `pertes seq : 28`).
   Elle a été **remplacée** par celle de l'arm 6 (même binaire), ⛔ pas re-tirée.
9. ⛔ **« L'artefact du détail CPU » n'est PAS mesuré.** Le constat owner le nomme et dit qu'il
   disparaît ; **aucun instrument ne l'a chiffré**, ni avant ni après. ⇒ **entrée ledger**.
10. ⛔ **AC1.5 a été RESPECTÉ — l'ancre n'a pas été re-testée** — mais le **fait 7/8 du `[CC]` est
    FRAGILISÉ** : son unique preuve est `f8d5813`, un **commit pendant** dont le cadrage écrit
    lui-même que **la portée annoncée était fausse**, et le `applications : 0` qui l'appuie a une
    **explication concurrente** (un `bl <n>` posé par l'agent, qui **désarme**). ⇒ **`[CC]`**.
11. ⛔ **L'observation sous éclairage VARIABLE reste partielle** : 130 · 239 · 372 lx sur le remède
    (✅ ce que le cadrage réclamait), mais ⛔ **rien sous 100 lx ni dans le noir** sur le remède.

## 26.10 ⚠️ LE RENVOI À §5.3 / §10.5 / §11.4 / §20bis — **EXPLICITE ET NUANCÉ** (AC6.4)

- **§5.3** — la DMA du panneau lit **23,0 Mo/s en continu** sur **SPI0**, que la PSRAM partage.
  ⚠️ **Le chiffre « 483 268 o « map » au bandeau de boot » y est PÉRIMÉ D'UN FACTEUR 2,2** : les
  segments « map » réels valent **454 712 + 616 370 = 1 071 082 o** au bandeau du 2026-08-28.
  ⛔ **Ne plus le citer sans le dater.**
- **§20bis** — *« l'arbitrage a CHANGÉ DE NATURE avec `RESTART_IN_VSYNC=n` : une famine ne décale
  plus toute l'image, elle salit le demi-bounce en cours »*. 🎯 **C'est exactement les lignes
  blanches de l'owner**, et c'est pourquoi la piste « lectures de code en flash » était **légitime
  ici** alors qu'elle avait échoué en `dn1-3`.
- **§11.4, ligne 6 des sept causes** — *« Lectures de code/constantes en flash → branche XIP →
  ❌ identique »*. 🔴 **CETTE LIGNE EST À CONSIDÉRER COMME NON ÉTABLIE.** Elle a été tirée avec
  **le même fichier de branche** que cette séance, donc avec **le même bandeau menteur** (§26.6.1) :
  ⛔ **impossible de savoir rétroactivement si XIP y était réellement armé**, les captures de
  l'époque n'étant pas au dépôt. ⚠️ **Et son périmètre ne couvrait pas ce symptôme** : elle portait
  sur le **glissement** sous `RESTART_IN_VSYNC=y`, ⛔ pas sur la salissure du demi-bounce à `n`.
  ⇒ **la réfutation de `dn1-3` ne s'applique PAS à `dn4-22`**, pour **deux** raisons indépendantes.
- **§10.5** — les sept causes de `dn1-3` restent valides **pour le glissement**. ⛔ Elles ne disent
  rien de la **marge de famine sous charge**, qui est le sujet de §26.

---

# §27 — SÉANCE CARTE DU 2026-08-28 : LA REVUE DE CODE `dn4-5` ÉPROUVÉE SUR LE SILICIUM

> **Contexte.** `dn4-5` a été débloquée le 2026-08-28 et une **revue de code 3 couches** a été
> tirée dans la foulée : 20 constats retenus, 3 décisions owner, **17 correctifs**. Cette séance
> mesure ce que ces correctifs ont coûté et vérifie ceux qui ne se voient que sur la carte.
> **Firmwares** : `A = 1bc4672` (avant revue) · `B = e3064f0` (les 17 correctifs).
> **Config INCHANGÉE avant/après** : `num_fbs=1 bounce_px=9600 draw_lines=128 draw_psram=0
> lvgl_core=0`. Relevés bruts : `mesures/dn4-5/R-seance-2026-08-28/`, synthèse `R2-…txt`.

## 27.1 🔴 LE PIÈGE QUE LA SÉANCE A TROUVÉ, ET IL INVALIDE UNE PRATIQUE — **LES DEUX PREMIÈRES MINUTES APRÈS UN BOOT MENTENT**

| relevé | uptime au départ de la fenêtre | cœur 0 occupé |
|---|---|---|
| **B1** | **44 s** | **42,26 %** |
| B4 | 225 s | 24,16 % |
| B5 | 256 s | 24,11 % |
| B6 | 288 s | 24,11 % |

**Même firmware. Même stimulus. Même protocole. 18 POINTS D'ÉCART**, soit **+75 % en relatif**.

🔴 **CE QUE ÇA A FAILLI COÛTER** : `B1` avait été pris juste après le flash, et il donnait
`42,26 %` contre `24,22 %` pour la référence. Lu seul, il concluait que **trois comparaisons
entières coûtaient 74 % de CPU** — une absurdité qu'on aurait pu publier. C'est la méthode du
**bruit de répétition** qui l'a démasqué : ⛔ on ne compare pas deux points, on compare un point à
une **étendue**.

⇒ **RÈGLE POUR TOUTE SÉANCE FUTURE : ⛔ AUCUNE MESURE DE CHARGE DANS LES ~3 PREMIÈRES MINUTES
APRÈS UN FLASH.** Attendre que la carte soit chaude, et le dire dans le relevé.

⚠️ **LA CAUSE N'EST PAS ÉTABLIE, ET ⛔ ON N'EN PUBLIE PAS.** Le relevé donne l'effet, pas le
mécanisme. Candidats à vérifier si quelqu'un veut la fermer : chauffe du BME680, convergence de
l'asservissement de rétroéclairage (`dn4-19`/`dn4-20`), premiers dessins LVGL.

## 27.2 📊 LE COÛT DU CHEMIN CHAUD LVGL — A/B EN RÉGIME CHAUD COMPARABLE

Les 17 correctifs n'ajoutent **qu'une seule chose** sur le chemin chaud : **trois comparaisons
entières par flush** (détection d'enroulement de `s_px`/`s_copie_us`/`s_attente_us`). ⛔ Aucun
verrou. Elles tombent **après** `draw_bitmap`, donc **invisibles à `copie_us`** — l'instrument
valide est donc la **charge CPU** et le **débit de flushes**, ⛔ pas les compteurs de temps.

`A` pris à **198 s** d'uptime ; `B4/B5/B6` à **225 / 256 / 288 s**. **Même régime.**

| grandeur | A `1bc4672` (n=1) | B `e3064f0` (n=3) | étendue de B | Δ |
|---|---|---|---|---|
| **cœur 0 occupé** | **24,22 %** | 24,11 · 24,11 · 24,16 % | **0,05 pt** | **−0,10 pt** |
| flushes/s | 26,25 | 25,84 · 25,99 · 25,87 | 0,14 | −0,34 |
| px / flush | 21 207 | 21 130 · 21 097 · 21 132 | 36 | −87 |
| copie µs / flush | 1 461 | 1 477 · 1 439 · 1 473 | 38 | +2 |

🎯 **VERDICT : LE COÛT DES TROIS COMPARAISONS N'EST PAS DISTINGUABLE DE ZÉRO.** Δ ≤ **0,1 point**
sur une charge de 24 %, soit **< 0,5 % en relatif**.

🔴 **ET LE SIGNE EST OPPOSÉ À UN COÛT RÉEL** : `B` mesure marginalement **moins** que `A`. Ce n'est
pas physique ⇒ ce qui reste est de la **variation résiduelle**, ⛔ pas un effet.

⛔ **CE QUE CE CHIFFRE NE PROUVE PAS, ET ⛔ IL NE FAUT PAS LE LIRE SANS ÇA : `A` EST UN ÉCHANTILLON
UNIQUE.** L'étendue de `B` est connue (0,05 pt) ; celle de `A` est **INCONNUE**. Fermer
symétriquement demanderait `A ×3`, soit **deux flashs de plus** que le budget annoncé (2, tous deux
consommés). **Décision owner du 2026-08-28 : on s'arrête là et on écrit la limite.**
⛔ **Aucun chiffre n'a été fabriqué pour combler ce trou.**

## 27.3 ✅ AC2.2 — LA CONTRE-ÉPREUVE DU GEL, MACHINE **ET** ŒIL

`gel 12` sur `B`, **les deux relevés pris SOUS LE VERROU** :

```
mural  (tâche app_main / horloge) : +12,0 s   ✅ VIVANT
vsync  (ISR du panneau RGB)       : +449      ✅ VIVANT (attendu ~449 à 37,40 Hz)
flush  (tâche LVGL)               : +0        🔴 FIGÉ
cycles (tâche LVGL)               : +0        🔴 FIGÉ
```

✅ **CONSTAT OWNER, DEMANDÉ ET OBTENU — ⛔ PAS DÉDUIT D'UN COMPTEUR.** L'image s'est **figée ~12 s
puis est repartie** ; le rétroéclairage est resté **allumé fixe** ; **aucun** artefact, clignotement
ou reprise brutale. **Verbatim : *« oui oui non rien de special »*.**

⇒ **AC2.2 EST COMPLET** : l'écart entre `up`/`vsync` et `flush`/`cycles` **est** la signature d'un
gel d'image sur une application vivante, et **l'œil l'a confirmé**. ⚠️ Le rappel imprimé par la
commande reste vrai : `vsync` ne descend pas jusqu'à l'œil, une dalle qui balaie un framebuffer
figé compte des vsyncs comme une dalle vivante — **c'est pourquoi le constat owner était requis**.

⚠️ **DEUX EFFETS DE BORD ATTENDUS, ET LES DEUX INSTRUMENTS ONT *DIT* CE QU'ILS PERDAIENT** :
`dn_capt` — *« verrou LVGL indisponible 2 fois — poussée perdue »* ; `dn_ui` — *« historique :
11 seconde(s) NON ÉCHANTILLONNÉE(S) … la courbe ne reliera PAS les deux bords de la coupure »*.
⛔ **Rien n'est passé en silence.**

✅ **LES TROIS AVERTISSEMENTS AJOUTÉS À `cmd_gel` PAR LA REVUE SE SONT AFFICHÉS** : famine du REPL
(le REPL **est** le transport), ⛔ pas pendant le soak, ⛔ pas près d'une échéance de veille.

## 27.4 ✅ LES CORRECTIFS DE REVUE, VÉRIFIÉS SUR LA CARTE — ET LA CARTE EN A CASSÉ UN

**LE BATTEMENT — le défaut, confirmé sur données réelles AVANT de flasher quoi que ce soit :**
sur `A` et dans le journal de soak du 26/08, `écart +3 s` à `up` 10/20/30/40/50 s — **constant,
jamais une variation**. C'était le **socle d'initialisation**, ⛔ pas de la famine
d'ordonnancement — et le commentaire du code affirmait le contraire.

Après correctif : `écart -1 s, Δ -1 s` **plus** `socle d'initialisation : 3 s … ⛔ EXCLU de
l'écart`. **Le socle vaut exactement les 3 s** qui polluaient la mesure.

🔬 **ET LA CARTE A TROUVÉ UN DÉFAUT DANS LE CORRECTIF LUI-MÊME.** L'écart partait à **−1 s** alors
que le commentaire annonçait 0 : division **entière tronquée** (10 s de `vTaskDelay` mesurent
9,9998 s, tronqué à 9). ⚠️ **Il se résorbait tout seul** — à **640 s** d'uptime la carte affichait
déjà `écart +0 s`. Le défaut est donc **plus petit que le correctif ne le suggère**, et c'est écrit.
⛔ **Mais un commentaire qui annonce « il part de 0 » au-dessus d'un code qui rend −1 est
exactement l'étiquette qui ment que ce dépôt traque.** Corrigé par **arrondi au plus proche**
(décision owner), reflashé, **re-vérifié** : `up 10 s … (écart +0 s, Δ +0 s)` **dès le premier
battement**. Coût : `0x120140` → `0x120150` = **+16 o**.

✅ **Les cumuls `flush` sont composés sur 64 bits** et s'impriment.
⚠️ **LA BANNIÈRE D'ENROULEMENT NE S'EST PAS AFFICHÉE, ET C'EST CORRECT** : `px` enroule en
**~6,48 h** et la carte avait 5 min. ⛔ **CE CHEMIN N'EST DONC PAS ÉPROUVÉ SUR LA CARTE.** Il le
sera par le soak lui-même — **c'est la première chose à regarder au bloc `flush` du jour 7**.
✅ `fps` : **37,40 Hz** mesuré contre 37,40 Hz théorique, écart **+0,00 %**.

## 27.5 ⛔ CE QUE CETTE SÉANCE N'A **PAS** FAIT

- **AC4.6** (budget de l'agent) : ⛔ **non tiré**. Il exige la tour en **régime livré, WSL ÉTEINT**.
- **AC3 / AC5 / AC8 / AC9.1** : le **soak de 7 jours n'a pas été lancé**.
- Le **coût AGENT** de la borne d'âge du lisseur : ⛔ non mesuré, **à verser à AC4.6**.
- La **COURSE** du seqlock de `dn_veille_cumul()` : ⛔ **non exercée** — un banc séquentiel n'exerce
  pas une course. Elle est vérifiée **par sa forme** (§25.6).

---

# §28 — `dn4-14` (P9.6) : LA PRÉMISSE ÉTAIT FAUSSE, ET C'EST **L'INSTRUMENT DU DÉPÔT** QUI LE DIT

⚠️ **NUMÉROTATION** : §27 était le dernier bloc au 2026-08-29 (séance `dn4-5` du 2026-08-28).
`dn4-5` est **encore `in-progress`** et son soak de 7 jours n'a rien écrit : si sa clôture réclame
un §28, **c'est celui-ci qui a le numéro** et l'autre prend §29. ⛔ Ne pas fusionner deux séances
sous un même numéro — c'est déjà arrivé.

⛔ **CE §28 NE CONTIENT AUCUNE MESURE SUR CARTE.** Tout ce qui suit a été tiré **depuis WSL**, sur
le dépôt. La séance carte (`AC4` le jaune, `AC2.4` l'A/B `GPU`, `AC5.3` l'arbitrage violet) est
**le point de synchronisation** et reste **à jouer avec l'owner**.

## 28.1 🔴 « IL N'Y A PAS DE MAISON » ÉTAIT FAUX — ET L'EPIC ET LE LEDGER LE DISAIENT TOUS LES DEUX

L'epic (`epics-desknode-v1.md` § `dn4-14`) et le ledger écrivaient : *« la police n'embarque que
ONZE glyphes et il n'y a pas de maison ⇒ **deux des trois demandes owner exigent une régénération
de police** »*.

**MESURÉ le 2026-08-29 avec `tools/gen_font_dn.py::codepoints_du_c()`** — ⛔ **jamais un test de
bornes** (c'est ce test-là qui avait fait croire `fan` présent sur une cmap SPARSE) :

| Fait | Mesure |
|---|---|
| `home` U+F015 **est déjà porté** par `dn_font_14.c` **et** `dn_font_28.c` | 260 codepoints / 3 cmaps par police, présent dans les deux |
| Pourquoi | `home` est `LV_SYMBOL_HOME`, l'un des **60 codepoints que le générateur AMONT injecte** |
| Coût de la maison | union `-r` **inchangée à 68** · `sha256sum` des 4 `.c` **identique** avant/après `--entete-seule` · **delta de binaire = 0 octet** |

⇒ **UNE SEULE des trois demandes exigeait une régénération : le `GPU`.**
⚠️ **La CONCLUSION de l'epic (« les deux se font en une passe ») reste JUSTE** — c'est son
**chiffrage** qui était faux, pas son plan.

⚠️ **ET LE BLOCAGE DU LEDGER ÉTAIT LEVÉ AUSSI.** Il reportait le ménage sur *« npm + réseau,
absents du tableau des versions figées »*. `lv_font_conv --version` rend **1.5.3**, rc = 0. **Une
ligne suffisait.** ⛔ Ne pas re-supposer un blocage : le re-vérifier.

## 28.2 🎯 LA MÉTHODE DE SONDE, ET POURQUOI IL FAUT **DEUX** CONTRÔLES NÉGATIFS

LVGL **ne dessine pas** un glyphe absent **et ne se plaint pas**. Un codepoint adopté depuis une
table FontAwesome donne donc un rectangle vide, sans une erreur. La seule méthode admise est de
**convertir le codepoint SEUL** :

```bash
lv_font_conv --no-compress --no-prefilter --bpp 4 --size 28 \
  --font "FontAwesome5-Solid+Brands+Regular.woff" -r 0xF015 \
  --format lvgl -o /tmp/sonde.c --force-fast-kern-format
```

**14 candidats sondés un par un le 2026-08-29, tous `rc = 0`.** Et **DEUX contrôles négatifs ont
échoué bruyamment dans la même passe** :

| Codepoint | rc | Message |
|---|---|---|
| `fan` **0xF863** | 1 | *« doesn't have any characters included in range 0xf863-0xf863 »* |
| `display` **0xF390** | 1 | idem, plage `0xf390` |

Les deux sont arrivés en **FontAwesome ≥ 5.11** ; le `.woff` embarqué est antérieur.
🎯 **C'est ce DOUBLE échec qui donne du sens aux 14 `rc = 0`** : sans lui, une sonde qui dit
« présent » pour tout ne prouve rien. ⛔ **Un contrôle négatif n'est pas une formalité.**

## 28.3 📊 L'ARITHMÉTIQUE DU BUDGET — **CALCULÉE**, ⛔ pas estimée

| Étape | Union `-r` FontAwesome |
|---|---|
| Avant la story (11 icônes, dont 3 amont) | **68** |
| − ménage des 3 morts **propres au dépôt** (`sync-alt` F2F1, `wind` F72E, `cogs` F085) | **65** |
| + `home` F015 (amont) | **65** |
| + `bolt` F0E7, `image` F03E, `film` F008 (**amont** — `LV_SYMBOL_CHARGE` / `_IMAGE` / `_VIDEO`) | **65** |
| + `gamepad` F11B, `cube` F1B2, `vr-cardboard` F729 | **68** |

⇒ **SIX candidats `GPU` + la maison, pour un budget STRICTEMENT NEUTRE.**

⚠️ **`cog` 0xF013 SORT DU DICTIONNAIRE MAIS RESTE DANS LA POLICE** : il est `LV_SYMBOL_SETTINGS`,
injecté par l'amont. C'est **la macro** `DN_ICONE_COG` qui disparaît, ⛔ **pas le glyphe**. Écrit
ici **et dans le source** pour que la prochaine lecture de `codepoints_du_c()` n'y voie pas une
régression.

### Le prix, en BINAIRE — c'est lui qui fait foi

| Build | `desknode.bin` | Delta |
|---|---|---|
| Avant la story (`77e06b5`) | 1 185 568 o | — |
| Après la maison seule (T1) | 1 185 568 o | **0** |
| Après la régénération complète (T3) | 1 185 520 o | 🎯 **−48 o** |
| Après `widget couleur` + son aide (T4..T7) | 1 187 280 o | +1 712 o |

⇒ **Le travail sur les icônes RAPPORTE 48 octets.** Le `+1 712` final est **l'instrument de
réglage** (`widget couleur` et son texte d'aide), ⛔ pas la police.

## 28.4 🔴 CE QUE LE MÉNAGE PROUVE, ET CE QU'IL NE PROUVERAIT PAS

⛔ **`--entete-seule` NE PAIE JAMAIS UN MÉNAGE.** Elle vérifie une **PRÉSENCE**, pas une
**absence** : retirer des entrées d'`ICONES` puis la lancer **PASSE** (il y a moins de codepoints à
vérifier) et **les octets restent dans les `.c`**. Le ménage serait **annoncé et NON PAYÉ**, en
silence.

**La preuve est `codepoints_du_c()` sur les `.c` RÉGÉNÉRÉS** :

| Codepoint | Après régénération |
|---|---|
| `sync-alt` 0xF2F1 · `wind` 0xF72E · `cogs` 0xF085 | ⛔ **ABSENTS** |
| `cog` 0xF013 | ✅ présent — **amont, ce n'est pas une régression** |
| `gamepad` F11B · `cube` F1B2 · `vr-cardboard` F729 | ✅ présents |
| Total porté | **260** (inchangé : −3 puis +3, c'est le troc du budget neutre) |

⚠️ **LE COMPTE TOTAL NE BAISSE PAS, ET C'EST ATTENDU** : la story dépense l'économie du ménage sur
les candidats `GPU`, dans la même passe. Le ménage se prouve **glyphe par glyphe**, ⛔ pas au
compteur — un total identique peut cacher un troc, et c'est exactement ce qu'il cache ici.

## 28.5 🔴 UN **QUATRIÈME** CONSOMMATEUR DE LA COULEUR DE CASE, QUE LE CADRAGE N'AVAIT PAS VU

Le cadrage recensait **trois** lecteurs de `k_desc[].couleur` : la tuile (`desc_effectif`), le
chevron (`chevron_couleur`), la série 0 de la courbe (`coul0`). **En les branchant sur le résolveur
unique `case_couleur()`, un QUATRIÈME est apparu** :

> `dn_console.c::veille_accents_collisions()` lisait **`dn_ui_desc(i)->couleur`** — un pointeur vers
> la table **`const`**, donc **aveugle à l'override à chaud**.

🎯 **ET C'EST L'INSTRUMENT MÊME DE L'ARBITRAGE.** `veille accents <pct>` est ce qu'on interroge
pour savoir si un nouveau violet `RAM` se confond avec le violet `CPU` en Ambient. Sans ce
correctif, il aurait rendu **son verdict sur l'ANCIENNE palette pendant que la dalle affichait la
nouvelle** — la classe de défaut « l'étiquette qui ment », au pire endroit possible.
⇒ `dn_ui_case_couleur()` est exposé, et **les quatre** le consomment.

## 28.6 🔴 LA GATE DES ACCENTS ÉTAIT **VERTE EN MESURANT LA MÉTRIQUE FICTIVE**

`tools/verif_veille_dn33.py::bloc_accents()` faisait un `re.findall(r"\.couleur = 0x([0-9a-f]{6})")`
sur **tout** `dn_ui.c` et prenait les **sept** valeurs trouvées, en écrivant que la 7ᵉ était
*« cyan pour l'humidité »* de la bicolore D6.

**MESURÉ** :

| Rang | Valeur | Ce que c'est **vraiment** |
|---|---|---|
| 1–6 | `a855f7 22d3ee f472b6 3b82f6 f87171 ff9640` | les six cases ✅ |
| **7** | **`35d6e8`** (l. 10139) | 🔴 **`k_demo_desc.couleur` — LA MÉTRIQUE FICTIVE DE DÉMO** |
| *(absente)* | `67e8f9` (`DET_COURBE_COUL_HUM`, l. 322) | l'accent **réel** de l'humidité, **non couvert** |

⇒ **Elle mesurait une couleur que personne ne voit, et ne mesurait pas celle qu'elle annonçait.**

### Et une propriété épinglée a basculé — par la **correction du jeu**, ⛔ pas par la palette

La gate affirmait : *« TÉMOIN : la moyenne en confond UNE AUSSI — simplement pas la même »*.

| Jeu | BT.601 (100 %) | Moyenne |
|---|---|---|
| **Ancien** (avec la démo) | 1 collision : `GPU`/`RAM` à 160 | 1 collision : **`CPU`/DÉMO** à 166 |
| **Corrigé** (avec l'humidité) | 1 collision : `GPU`/`RAM` à 160 | 🔴 **AUCUNE** — 7/7 distinctes |

⇒ La paire que le témoin comptait était **`CPU` / la métrique fictive**, ⛔ pas `CPU`/humidité. Sur
le jeu **réellement peint**, c'est **BT.601 qui confond et la moyenne qui sépare tout** — donc la
phrase d'origine de `dn_widget_desaturer()` (*« la moyenne confondrait, BT.601 sépare »*) est fausse
**encore plus fort**, et **dans l'autre sens**.

⛔ **ET CE N'EST PAS UNE RAISON DE TOUCHER LA FONCTION.** Le produit tourne au défaut
`s_accent_amb_pct = 95`, où les **sept restent distincts** avec un écart chromatique de **10/255**.
L'écart BT.601/moyenne n'existe **qu'à 100 %**, un régime que le produit n'emploie pas.
**C'est un fait à écrire, pas un correctif à faire.**

⚠️ **Et `dn_ui.c` mentait deux fois sur la même valeur** : *« l'humidité garde le cyan `0x35d6e8`,
celui de `GPU` »* — l'humidité vaut `0x67e8f9` et `GPU` vaut `0x22d3ee`. **`0x35d6e8` n'est ni
l'un ni l'autre.** Les deux valeurs coïncidaient par accident d'arithmétique : **c'est ce qui a
laissé la gate verte**.

## 28.7 ✅ CE QUE LES GATES DISENT, ET LES **TROIS MUTANTS VUS ROUGIR**

`python3 tools/verif_veille_dn33.py` ⇒ **187 OK · 0 KO**. ⛔ Une gate verte ne prouve rien seule
(*« une gate N OK / 0 KO peut épingler du code FAUX »*). Trois mutants ont donc été tirés :

| Mutant | Verdict |
|---|---|
| L'humidité ramenée à `0x35d6e8` (le défaut d'avant `dn4-14`) | 🔴 **rougit** — le témoin de la moyenne |
| `RAM` passée en cyan sous un commentaire qui dit toujours *« ROSE »* | 🔴 **rougit 4 fois** (dont AC6.5) |
| La teinte de démo **infiltrée dans `k_desc[]`** | 🔴 **rougit 5 fois** — l'exclusion opère |

`idf.py build` : **0 erreur, 0 avertissement**.

## 28.8 ⛔ CE QUE CE §28 N'A **PAS** FAIT — ET QUI DEMANDE L'OWNER

- ⛔ **AC4 — LE JAUNE DE `RAM` N'EST PAS RELEVÉ.** Il se relève **sur la dalle, AVANT tout
  changement de palette**, sinon le relevé ne relève plus rien. ⚠️ Le **seul jaune que ce firmware
  sait peindre** est l'ambre `W_COL_SIMULEE = 0xffb020` du **régime SIMULÉE** (`dn_widget.c`) —
  ⛔ **ce n'est pas une conclusion**, c'est la première chose à écarter **avec les yeux**. Si c'est
  lui, la demande owner ne portait **pas** sur la palette et **AC5 devient sans objet**.
- ⛔ **AC2.4 — L'A/B `GPU` n'est pas joué.** Six candidats + l'icône en place sont embarqués et
  commutables à chaud (`widget icone <case> <n>`). **L'agent ne choisit pas.**
- ⛔ **AC5.3 — L'ARBITRAGE DU VIOLET.** `CPU` est **déjà** violet `0xa855f7`, et `dn4-4` l'y avait
  **déplacé exprès** le 2026-08-24 pour l'écarter du cyan de `GPU`. « `RAM` en violet » remet donc
  **deux violets côte à côte** — le défaut que `dn4-4` a corrigé. ⇒ arbitrage **owner**.
- ⛔ **AC6.4 — les nombres de la gate ne sont pas re-mesurés sur la palette RETENUE** : ils en
  dépendent. Si le violet de `RAM` fait passer la collision BT.601 à **zéro paire**, la gate
  **rougira sur une AMÉLIORATION** ⇒ **ré-écrire le nombre AVEC son motif**, ⛔ jamais l'ajuster.

⚠️ **PIÈGE À TENIR EN SÉANCE** : `dn_widget.c` masque `{ titre, icone, badge }` en **Ambient**.
⇒ **L'A/B d'icône se juge en mode ACTIF**, sinon l'owner regarde une case où **il n'y a pas
d'icône**. La **couleur**, elle, a **deux régimes à juger** — teinte pleine en Actif, gris désaturé
à 95 % en Ambient, encore visible **par la jauge**.

## 28.9 🔴 LA SÉANCE DU 2026-08-29 — **LES TROIS VERDICTS SONT DE L'ŒIL, ET DEUX RENVERSENT LA STORY**

Firmware `6f188ed` puis `6af9bd8`, **SHA lu au bandeau** · **agent RÉEL** sur la tour
(⛔ pas le mock) · veille désarmée pendant les A/B.

### 28.9.1 ⛔ AC4 — LE JAUNE N'EST PAS CE QUE LA STORY AVAIT PRÉSUMÉ

**Verbatim owner, dalle sous les yeux :**

> *« l'icone est jaune la barre des 53% utilisé aussi est jaune le logo du disque aussi est jaune
> (c'est juste que disque et ram sont jaune il fau une autre couleur pour l'un des 2) »*

🔴 **La story annonçait l'ambre du régime SIMULÉE** (`W_COL_SIMULEE 0xffb020`, le texte de valeur)
et prévoyait qu'AC5 devienne **sans objet** si c'était lui. **RÉFUTÉ** : l'owner nomme **l'icône et
la jauge**, donc **l'accent**, donc `k_desc[].couleur`. AC5 reste dans le périmètre.

🔴 **Et le défaut n'est pas « `RAM` est jaune » — c'est « `RAM` et `DISQUE` sont la même couleur ».**

| Mesure | Valeur |
|---|---|
| Écart de teinte `RAM` (rose 328,6°) / `DISQUE` (corail 0,0°) | **31,4°** |
| Leurs luminosités | **70,2 %** et **70,8 %** — quasi égales |

⚠️ **Et ce n'était qu'UNE des TROIS paires serrées** : `DISQUE`/`AMBIANCE` **27,0°**,
`GPU`/`RÉSEAU` **29,3°**, `RAM`/`DISQUE` **31,4°**. Les six teintes tiennent en **deux paquets**
(chaud 0/27/329° · froid 188/217/271°) avec un **vide de 160,9°**.
🎯 **Calculé** : déplacer **une seule** case ne pouvait pas régler ça — le meilleur coup unique ne
fait passer la pire paire que de **27,0° à 29,3°**.

### 28.9.2 🔴 AC5 — LE VIOLET EST ESSAYÉ SUR LA DALLE, PUIS **RÉFUTÉ PAR SON DEMANDEUR**

`0x7c3aed` posé à chaud sur `RAM` (`widget couleur 2 …`, **sans reflash**). Verdict :

> *« maintennat c'est la meme couleur que cpu lol »*

`CPU` est déjà `0xa855f7`, où `dn4-4` l'avait **déplacé exprès** le 2026-08-24 pour s'écarter du
cyan de `GPU`. ⇒ le violet ne faisait que **déplacer** la collision.
⇒ 🎯 **LA DEMANDE DE L'ADDENDUM §1 (« RAM : violet ») EST REFUSÉE PAR SON PROPRE AUTEUR**, sur
constat à l'œil. **`RAM` garde son rose**, et son commentaire est **amendé, ⛔ pas effacé**.

⇒ **C'est `DISQUE` qui bouge** — chemin proposé par l'owner lui-même (*« il faut une autre couleur
pour l'un des 2 »*) : `0xf87171` → **`0xe2e8f0`**. Verdict : *« disque est bien distinct
maintenant »*.

⛔ **Le VERT n'a pas été proposé** : `dn4-4` l'a déjà tué (« vert sur vert » avec le PCB). **Une
expérience déjà perdue ne se rejoue pas au prix d'un regard owner.**

### 28.9.3 🎯 ET LA DALLE REND CE CLAIR **VIOLET** — CE QUI ÉTAIT **PRÉDIT** DEPUIS QUATRE JOURS

> *« disque est en violet mais c'est nickel »*

`0xe2e8f0` vaut R226 G232 B240 : un **clair neutre** (écart max-canal 14). L'owner le voit
**violet**. ⛔ **Ce n'est ni une erreur d'observation ni un bug** — `dn_widget.c` porte déjà, depuis
le **2026-08-25**, le constat de `scene gray` :

> *« sur CETTE dalle, en RGB565, **AUCUN GRIS N'EST NEUTRE** : vert vers les tons sombres, **violet
> vers le milieu et les tons clairs** »* — le vert a **6 bits**, le rouge et le bleu **5** : il prend
> puis rend son avance à chaque pas de la rampe.

🎯 **Cette propriété, relevée quatre jours plus tôt, A PRÉDIT le résultat d'aujourd'hui.** C'est le
seul cas connu de ce dépôt où une mesure de dalle a **anticipé** un résultat de conception.
⚠️ ⛔ Ne pas « corriger » cette valeur vers un violet explicite en croyant réparer une incohérence,
ni la pousser vers le blanc pur en croyant la neutraliser : **elle est validée telle quelle**.
✅ Le piège de la **collision déplacée** a été **vérifié, ⛔ pas déduit** :
*« oui c'est bien distinct de cpu qui est beaucoup plus bleuté »*.

### 28.9.4 ✅ AC2.4 — L'A/B DES SIX ICÔNES, MÊME CASE, **ZÉRO REFLASH**

Verdict : **`gamepad`** — *« on garde gamepad »*. Les cinq rejets sont consignés **verbatim** dans
le descripteur pour que personne ne les re-propose :

| Candidat | Verdict owner |
|---|---|
| `cube` (un cube en perspective) | *« cube tres bof »* |
| `vr-cardboard` (casque de RV) | *« vr non plus »* |
| `bolt` (un éclair) | *« elimine »* |
| `image` (cadre photo) | *« elimine »* |
| `film` (pellicule perforée) | *« nop »* |

⛔ **L'agent n'a choisi aucune des six.** Les sept glyphes (six candidats + l'icône en place) étaient
embarqués **ensemble** : l'A/B complet a coûté **UN flash**, pas sept.
✅ La **maison** d'`AMBIANCE` est relue à l'œil en mode ACTIF : *« oui nickel aussi »* — ⚠️ et
c'était nécessaire : le coût nul était prouvé au `sha256sum`, mais **une preuve d'octets n'est pas
une preuve de dessin**.

### 28.9.5 🔴 CE QUE LA SÉANCE A TROUVÉ EN PLUS — **LA JAUGE SE POSE 27 px TROP HAUT**

> *« la barre a été un peu remontté ? maintenant elle est sur le chiffre % et plus en dessous ?! »*
> puis, après reconstruction en actif : *« oui la barre est revenue sous le chiffre »*

**MÉCANISME, RELU DANS LE CODE :** `dn_widget_creer()` calcule la position de la jauge à partir de
`font_val()`, **qui dépend du mode** :

| Mode | `val_y` | interligne | bas de valeur (n=1) |
|---|---|---|---|
| **ACTIF** | 48 | 35 (`dn_font_28`) | **83 px** |
| **AMBIENT** | 26 (`W_AMB_VAL_Y`) | 30 (police de veille) | **56 px** |

⇒ Une scène **reconstruite en veille** pose la jauge ~**27 px trop haut** pour l'actif. Elle ne fait
que **10 px** (`W_JAUGE_H`) : elle atterrit **en plein sur le chiffre**.

🔴 **ET LA GARDE EXISTANTE NE LE VOIT PAS.** `dn_widget_controler_tenue()` tourne bien à la bascule,
mais elle **CONSTATE et JOURNALISE** un débordement — ⛔ **elle ne repositionne rien**, et elle ne
teste que *« le texte sort-il de la case »*, ⛔ **pas** *« la jauge est-elle encore sous la
valeur »*. **Compteurs de débordement à ZÉRO pendant que la jauge chevauchait le chiffre.**
⇒ **L'œil a vu ce que l'instrument ne mesure pas** — une garde plus étroite que la propriété
qu'elle annonce, la classe de défaut récurrente de ce dépôt.

⚠️ **PRÉCISION OWNER, ET ELLE COMPTE** : *« la veille etait ok ! »* — ⛔ le défaut **n'est pas la
veille**, c'est la **RECONSTRUCTION PENDANT la veille**.
⚠️ **PORTÉE** : `dn_ui.c:9545` écrit que *« le régime courant ne doit pas déclencher
`build_scene()` »*, et les appelants restants sont l'init, la navigation et **les commandes
console**. Or un doigt **réveille avant de naviguer** ⇒ **l'usage normal n'est pas atteint** ; ce
sont **les outils d'A/B** qui l'exposent. ⇒ versé au ledger avec son remède.

### 28.9.6 ✅ RÉFUTÉ AU PASSAGE — « LA DALLE DÉFORME LES COULEURS »

Les six accents décrits par l'owner ne correspondaient qu'**une fois sur six** aux valeurs du
source. Avant tout arbitrage, témoin `scene rgb` (trois bandes **auto-étiquetées**) :

> *« oui rouge est rouge bleu est bleu et vert est vert (vraiment les RGB classique) »*

⇒ ⛔ **ni permutation R/B, ni octets échangés.** Les primaires sont exactes — ce sont les **tons
intermédiaires et clairs** qui dérivent (§28.9.3).

🔴 **ET UNE LEÇON D'INSTRUMENT, PAYÉE DANS LA MÊME PASSE** : au premier tir, `scene rgb` a rendu une
capture **totalement vide** et j'ai failli conclure à une panne d'affichage. La commande avait en
fait été **REFUSÉE** (`ui_bloque` : *« LVGL tient l'écran — `ui off` d'abord »*), et le message
n'avait pas été capturé.
⇒ ⛔ **UNE CAPTURE VIDE N'EST PAS « la commande a tourné sans rien dire ».** Le *« je ne vois
rien »* de l'owner était **exact** : aucune bande n'avait jamais été dessinée.

### 28.9.7 ⛔ CE QUE LA SÉANCE N'A **PAS** FAIT

- ⛔ **`GPU`/`RÉSEAU` (29,3°) reste une paire serrée** — ⛔ non corrigée, **non masquée**. L'owner ne
  l'a pas signalée (il voit *« cpu gpu bleu claire »* et *« reseau bleu foncé »*, donc il les
  distingue). **Versée au ledger** plutôt que corrigée sans demande.
- ⛔ **Les libellés de case ne sont pas agrandis.** Demande owner de séance : *« les ecriture sont
  trop petites elles devrais etre agrandit un peu (cpu, gpu etc..) »*. Les titres sont en
  `dn_font_14` et les seules autres tailles embarquées sont **28/33/56** : passer à 28 les
  **doublerait**. Il faut une **taille intermédiaire**, donc une **vraie régénération** — et ça
  change **tous les pixels**, donc `px/cycle`, `ms/cycle`, `duty`, que le soak de `dn4-5` mesure.
  ⇒ **élargit `dn4-14-2`** (« la typographie du chrome »), qui existe exactement pour payer ce coût
  une seule fois.
- ⛔ **Le remède du défaut de jauge** (§28.9.5) n'est pas appliqué : hors périmètre `dn4-14`.

---

# §29 — `dn4-14-2` (P9.6b) : **LE MUR N'ÉTAIT NI VERTICAL NI LÀ OÙ ON LE CHERCHAIT**

*Séance des 2026-08-29 / 30. Firmware de mesure `1e968c0`, firmware des candidats `6013e57`,
firmware livré `8308bbf`. Trois flashs, l'A/B joué en mode **ACTIF** avec **l'agent réel**.*

## §29.0 — Ce que la story venait faire, et ce qu'elle a trouvé

Deux constats owner **à l'œil**, à dix jours d'écart : *« la date pourrait être un peu plus
grande »* (2026-08-19) et *« les ecriture sont trop petites elles devrais etre agrandit un peu
(cpu, gpu etc..) »* (2026-08-29). ⛔ Aucun des deux ne nomme une taille ⇒ **A/B piloté par l'owner**.

Le cadrage annonçait un mur **vertical** (la hauteur de barre, `BARRE_H`) et un plafond de **20 px**
pour le titre. **Les deux sont faux**, et c'est la mesure qui le dit.

## §29.1 — 🔴 LE MUR EST HORIZONTAL, ET IL ÉTAIT **DÉJÀ FRANCHI** AVANT LA STORY

Relevé sur `1e968c0`, **avant tout changement de police**. Les slots sont **relus du rendu**
(`dn_ui_barre_slots()`, `dn_widget_titre_utile()`), ⛔ pas écrits dans le message :

| slot | x | utile |
|---|---|---|
| DATE de barre | 300 | **170 px** (dalle 480 − x − marge) |
| HEURE de barre | 10 | **290 px** |
| TITRE de case | 52 | **107 px** (case 225, badge à 159) |

**Largeurs mesurées** (`lv_text_get_size`, kerning compris, police réellement liée) :

| chaîne | 14 | 16 | 18 | 20 | 22 | 28 | budget |
|---|---|---|---|---|---|---|---|
| `AMBIANCE` — plus long titre **livré** | 78 | 92 | **103** | 113 🔴 | 126 🔴 | 161 🔴 | **107** |
| `DÉMO 2+JAUGE` — plus long titre **existant** | **114 🔴** | 129 🔴 | 147 🔴 | 162 🔴 | 181 🔴 | 230 🔴 | **107** |
| pire date **réelle**, balayée | 104 | 122 | 135 | 151 | 167 | 213 🔴 | **170** |
| `HEURE NON POSÉE` — pire cas du **slot** | 141 | **164** | 184 🔴 | 201 🔴 | 227 🔴 | 288 🔴 | **170** |
| `01:17` / `01:17:33` | 30/49 | 37/58 | 41/64 | 44/71 | 49/79 | 62/99 | **290** |

⇒ 🎯 **Le titre plafonne à 18, ⛔ pas à 20.** Le cadrage donnait le plafond **vertical** (à 22 la
boîte du titre passe sous `val_y`) ; le mur **horizontal** mord **avant**.
⇒ 🎯 **`DÉMO 2+JAUGE` ne tenait DÉJÀ PAS à 14 px** : 114 pour 107, **déborde de 7 px dans la
réserve du badge**, sur le firmware d'avant. Défaut **préexistant**, révélé par l'instrument.

### 🔴 REVUE DE CODE DU 2026-08-30 — CE PARAGRAPHE DISAIT « CLIPPÉ DE 7 px », ET C'ÉTAIT LE MAUVAIS MÉCANISME

Relu du code, ⛔ pas supposé :

- le label de titre est créé par `dn_widget_texte()` **sans largeur posée** ⇒ il se dimensionne au
  contenu ;
- son parent est la **zone de case**, large de `DN_UI_CASE_W` = **225 px** ;
- ⇒ **LVGL ne le clippe qu'à `x = 225`**, c'est-à-dire après **173 px** de titre depuis `x = 52`.
  ⛔ **Pas à 107.**
- et le badge « SIMULÉ » est créé **`LV_OBJ_FLAG_HIDDEN`** (`dn_widget.c`) : il n'est démasqué que
  sur une case **SIMULÉE**.

⇒ 🎯 **Dans la bande 107..173 px il n'y a AUCUN clip** : il y a un **chevauchement de la réserve du
badge**, visible seulement si le badge l'est. Au-delà de 173, c'est un vrai clip de zone.

⇒ 🔴 **ET SUR LE DÉMONSTRATEUR LUI-MÊME, RIEN NE SE VOYAIT.** `DÉMO 2+JAUGE` = 114 px finit à
`x = 166 < 225`, et la case de démo n'appelle jamais `dn_widget_maj()` avec un régime SIMULÉ ⇒
**son badge reste masqué**. Les « 7 px » sont exactement `166 − 159`, la morsure dans une réserve
**invisible**. Le défaut trouvé est réel comme **ABSENCE DE GARDE** — ⛔ pas comme artefact visible
sur ce stimulus-là.

✅ **VERDICT OWNER DU 2026-08-30 — LE SEUIL RESTE 107.** Un titre qui mord la réserve casse dès que
la case passe SIMULÉE, et le régime d'une case n'est pas une propriété de sa géométrie. Ce qui
change, ce sont les **mots** : le log runtime dit désormais *« CHEVAUCHE LA RESERVE DU BADGE (visible
seulement si la case est SIMULEE ; LVGL ne clippe qu'au bord de zone, a N px) »*.
⚠️ **ÉCART ASSUMÉ, ÉCRIT** : `s_trop_larges` monte aussi quand le badge est masqué, donc **sur des
cases où rien ne se voit**. C'est le prix accepté pour ne pas conditionner une garde de géométrie à
un état d'affichage.

## §29.2 — 🔴 LE PIRE CAS DE LA DATE **N'EST PAS UNE DATE**, ET LE PIRE CAS DE DATE N'EST PAS CELUI QU'ON CROYAIT

`DN_UI_DATE_INCONNUE` vaut `"HEURE NON POSÉE"` — **15 caractères**, et c'est **elle** qui plafonne
la date à **16 px**. Toutes les **vraies** dates tiennent jusqu'à **22**.

Et le pire cas de date a été **BALAYÉ**, ⛔ pas supposé : toutes les formes que `barre_composer()`
peut produire, **mesurées une par une** via `dn_ui_barre_date_forme()`.

> 🔴 **REVUE DE CODE DU 2026-08-30 — LE DOMAINE PUBLIÉ ICI ÉTAIT FAUX, ET IL L'ÉTAIT DE DEUX
> FAÇONS.** Ce paragraphe écrivait « **7 × 12 × 31 = 2 604** » ; quatre docblocs du firmware
> écrivaient « **7 × 12 × 32** » ; et une même ligne de `dn_console.c` portait « 32 » en commentaire
> et « 31 » dans son `printf`, trois lignes plus bas. **Aucun des trois n'était juste** : le
> balayage n'excluait pas les jours qui n'existent pas dans leur mois, donc il mesurait
> « **MER. 31 FÉVR.** » — exactement la classe corrigée la veille pour `jour = 00` (*« un pire cas
> injoignable est un budget qu'on s'invente »*), corrigée pour le seul jour zéro.
> ⇒ Le domaine réel est **7 × 366 = 2 562** formes (février à 29). ⚠️ **Et il n'est plus écrit
> nulle part** : l'instrument IMPRIME `n`, relu de son propre balayage — le seul remède à un compte
> qui a menti à quatre endroits à la fois.
> 🔴 **ET IL MANQUAIT UNE FORME QUE LE PRODUIT REND VRAIMENT** : `dn_rtc.c` masque le registre du
> jour de semaine en `0x07`, donc **7 est atteignable**, et `barre_composer()` émet alors `"???"`.
> `dn_ui_barre_date_forme()` rendait `false` sur ce cas ⇒ **le balayage ne mesurait jamais la forme
> d'une lecture RTC dégradée.** Elle est désormais tirée.
> ⚠️ **Le pire cas mesuré ci-dessous n'a PAS bougé** — `MAR. 04 MARS` est une date réelle — mais le
> verdict repose maintenant sur un domaine qui est celui du produit.

| | pire cas | px à 14 |
|---|---|---|
| **supposé** par le cadrage | `MER. 06 SEPT.` (13 car.) | 100 |
| **mesuré** | **`MAR. 04 MARS`** (12 car.) | **104** |

⇒ ⛔ *« le plus long »* n'est pas *« le plus large »*. Le pire cas réel est **plus court d'un
caractère** et **plus large de 4 px**.

⚠️ **Et la FRÉQUENCE annoncée est réfutée** : le cadrage écrivait que `HEURE NON POSÉE` est
*« l'état au boot … donc un état que l'owner voit régulièrement »*. **Relu sur la carte** (`rtc`) :
`retention : 0xD7 relu AU BOOT = attendu` et `bit OS : 0` ⇒ **le PCF85063A garde l'heure au travers
des reboots**. C'est un état **transitoire**, ⛔ pas quotidien — et c'est ce fait qui a rendu
acceptable l'écart déclaré de §29.6.

## §29.3 — 🔴 AC5.2 PROUVÉE PAR UN **AVANT/APRÈS SUR LE MÊME STIMULUS**

`widget demo on`, titre en 14, `DÉMO 2+JAUGE` clippé de 7 px :

| | chevauchements | trop larges | débordements |
|---|---|---|---|
| **AVANT** (`1e968c0`) | 0 | **0** | 0 |
| **APRÈS** (`6013e57`) | 0 | **1** | 0 |

⇒ **Un compteur à zéro n'était pas une absence d'histoire : c'était une absence de GARDE.**
`dn_widget_controler_tenue()` teste *« le texte de VALEUR sort-il de la case »* et **ne regardait
pas le titre**. La garde est posée à la construction et alimente `trop_larges` — ⛔ pas un
quatrième compteur, les trois restent trois.

**Témoin négatif tiré** (`widget titre 22`) :
`TITRE trop large : « AMBIANCE » = 126 px pour 107 utiles (x 52, badge a 159) — CLIPPE EN SILENCE`
⇒ **la garde sait crier.**

> 🔴 **REVUE DE CODE DU 2026-08-30 — CE MESSAGE EST CONSERVÉ TEL QU'IL A ÉTÉ RELEVÉ, ET SA FIN EST
> FAUSSE.** *« CLIPPE EN SILENCE »* nomme le mauvais mécanisme (voir §29.1) : dans la bande
> 107..173 px le titre **chevauche la réserve du badge**, il n'est pas clippé. Le message du
> firmware a été corrigé ; le relevé, lui, reste **tel quel** — c'est un constat daté, ⛔ pas une
> affirmation courante.
> ⚠️ **Ce que ce tableau AVANT/APRÈS prouve reste vrai et entier** : le compteur passe de 0 à 1 sur
> le **même** stimulus, donc **la garde existe désormais et elle mord**. Ce qu'il ne prouve pas,
> c'est que quelque chose se voyait à l'œil avant — et personne ne l'a prétendu ici.

## §29.4 — 🔴 LA CHAÎNE DE POLICE AVAIT **DEUX MOITIÉS CASSÉES**

Le cadrage demandait de *vérifier* qu'une 3ᵉ taille « ne casse rien ». **Vérifié : elle cassait deux
fois.**

| Moitié | Ce qui se passait | Symptôme |
|---|---|---|
| **Déclaration** | `ENTETE_MODELE` récitait `LV_FONT_DECLARE(dn_font_14)` / `(dn_font_28)` **en dur** | le `.c` neuf **jamais déclaré** — aucun site ne pouvait le nommer |
| **Compilation** | `main/CMakeLists.txt` **énumérait** les `.c` à la main | `undefined reference` **au LINK**, ⇒ *après* avoir payé la régénération complète |

Démontré en chargeant **les deux** générateurs avec `TAILLES = (14, 18, 28)` :
`AVANT → 14, 28, 33, 56` (⛔ pas de 18) · `APRÈS → 14, 18, 28, 33, 56`.

⇒ Corrigé **dans le générateur** (⛔ pas dans le `.h`, qui est écrasé) : déclarations **et** X-macro
`DN_FONT_LISTE(X)` construites depuis `TAILLES`, sources **découvertes** par
`file(GLOB … CONFIGURE_DEPENDS)`.
⚠️ **Piège du glob** : ESP-IDF relit `CMakeLists.txt` en **script mode**, où CMake **refuse**
`CONFIGURE_DEPENDS` (*« invalid for script and find package modes »*) ⇒ garde
`if(CMAKE_SCRIPT_MODE_FILE)`. Sans elle **le projet ne configure plus du tout**.

## §29.5 — 🔴 LE COMPTE DES « RECONSTRUIT » A ROMPU UNE **CINQUIÈME** FOIS — ET AUTREMENT

Les quatre premières ruptures étaient des **arriérés**. La cinquième est d'une autre nature :
**le TREIZE publié était FAUX AU MOMENT MÊME où on l'écrivait.**

Recompté **depuis le code** (chaque appel à `build_scene()` remonté à sa sous-commande) :
la liste de TREIZE **omettait `widget detpan` et `widget fond`**, que le README décrivait pourtant
*« reconstruit la scène »*. La **même ligne** du README publiait donc *« est passé à TREIZE »*
**et** *« le compte passe de DOUZE à QUATORZE »*.

**Le vrai nombre est 16** (15 avant cette story, +`titre`).
⚠️ `widget courbe` ne reconstruit **pas** (`dn_ui_detail_courbe_axes()` est un LECTEUR) — une
première analyse l'avait compté ; vérifié à la main.
⚠️ `widget date` non plus : le label est **repeint en place**, parce qu'une reconstruction
**pendant la veille** poserait la jauge 27 px trop haut (§28.9.5).

🎯 **La parade n'est plus « faire attention », parce que ça a échoué cinq fois** :
`verif_veille_dn33.py` / `bloc_reconstruit` **RECOMPTE** et **CONFRONTE** aux deux textes.
⚠️ Il a fait rougir sa propre première version, qui perdait `voile` (elle partage sa branche avec
`opa`, laquelle re-teste `argv[1]` dans son corps).

## §29.6 — LES TROIS VERDICTS OWNER, ET L'ÉCART DÉCLARÉ

A/B joué **en mode ACTIF**, avec **l'agent réel** (⛔ pas `widget mock on`, qui repeint les valeurs
en ambre — leçon `dn4-14`). `veille off` avant la série.

| Question | Verdict, **verbatim** |
|---|---|
| police du TITRE | *« C'est ça, on garde 18 »* |
| police de la DATE | *« Garder 18 et ACCEPTER la coupe »* |
| les libellés secondaires suivent-ils ? | *« Oui — tout le chrome en 18 »* |

⚠️ 🔴 **ÉCART DÉCLARÉ — la date en 18 CLIPPE `HEURE NON POSÉE`** (184 px pour 170, ~2 caractères).
Le conflit a été **énoncé avant d'être tranché**, avec ses quatre leviers :
accepter la coupe · redescendre à 16 (seule taille où **même ce pire cas** tient) · déplacer
`x = 300` · bouger `BARRE_H` — qui **périmerait toute coordonnée tactile publiée**
(`VENTILOS 506..516`, jauge `y = 340..350`) pendant que `dn4-5` et `dn4-10` sont ouverts.

> ⚠️ **RENVOI (`dn4-15`, 2026-08-30)** — la coordonnée `y = 340..350` citée ci-dessus
> est **conservée telle qu'elle a été publiée**, ⛔ la narration n'est pas réécrite.
> **Elle est morte, et on ne lui substitue AUCUN autre nombre** (⛔ pas `337..347`,
> qui a été publié sans instrument). ⇒ **le rectangle qui fait foi se RELIT** :
> `widget jauge [<case>]` (`dn4-4`/AC9, `dn_ui_widget_jauge_rect()`), et §22.3
> porte l'arbitrage complet. La console et `dn_ui.c` ne l'enseignent plus.

## §29.7 — LE COÛT, MESURÉ — ⛔ NI EXTRAPOLÉ, NI AU PLANCHER

Référence : binaire **reconstruit depuis l'arbre PROPRE** (`ae18700`) = **1 188 016 o**.
⚠️ Le cadrage annonçait cette référence **périmée** (bâtie sur un arbre sale) — **reconstruite, elle
est identique À L'OCTET**. La crainte est réfutée par sa propre mesure.

| étape | binaire | delta |
|---|---|---|
| référence | 1 188 016 | — |
| instrument seul (`1e968c0`) | 1 191 664 | +3 648 |
| **4 candidats à bord** (`6013e57`) | 1 322 848 | **+134 832** |
| **après ménage** (`34d3c2c`) | 1 225 440 | **+37 424** |

⇒ **le ménage rend 97 408 o** — le compte baisse **pour de vrai** (leçon `dn4-14`/AC3.3).
**Coût net : +37 424 o, soit 1,24 % du libre** (partition 4 194 304, ~3,0 Mio libres).

**Le plancher n'est pas le coût** — les deux, côte à côte :

| taille | plancher `octets_police` | **objet compilé** | écart |
|---|---|---|---|
| 16 | 24 429 | 24 506 | +77 |
| 18 | 29 344 | **29 421** | +77 |
| 20 | 33 502 | 33 579 | +77 |
| 22 | 39 173 | **39 250** | +77 |
| **les quatre** | 126 448 | **126 756** | **+308** |

⇒ Et le plancher sous-estime le **binaire** de **8 384 o** : le reste est du **code**.
⚠️ **« ~19 Ko extrapolés par l'aire » pour la police 22 était FAUX D'UN FACTEUR ~2** — corrigé dans
`addendum.md:172` (texte d'origine **conservé**) et dans `widget police`.

> 🔴 **REVUE DE CODE DU 2026-08-30 — LE DELTA DES QUATRE CANDIDATS ÉTAIT PUBLIÉ AVEC DEUX VALEURS.**
> Ce tableau écrit **+134 832** ; `dn_console.c` (`widget police`) et `addendum.md` écrivaient
> **+134 304** — **528 o d'écart**, et les deux textes fautifs sont précisément ceux qu'AC7.1/AC7.2
> venaient de corriger. C'est **134 832** qui est juste : seul cohérent avec `1 322 848 − 1 188 016`
> **et** avec `37 424 + 97 408`. Les deux textes sont alignés sur la mesure. ⚠️ Le motif est celui
> que ce dossier dénonce partout : **un nombre recopié d'un texte à l'autre au lieu d'être relu de
> sa mesure** — et le recopier dans le geste même qui le corrige est le pire moment pour le faire.

### 🔬 AC6.2 — LA PREUVE **TAILLE PAR TAILLE**, PRODUITE (revue du 2026-08-30)

AC6.2 exige *« la preuve est **taille par taille** : `ls` des `.c` **et** `codepoints_du_c()` sur ce
qui reste, ⛔ pas un total »*. Le Dev Agent Record l'**affirmait** ; §29.7 ne publiait que des
**totaux**. La voici, relue de l'arbre :

| `.c` présent | rôle | codepoints | `É` U+00C9 | `Û` U+00DB | `°` U+00B0 | glyphes ≥ U+F000 |
|---|---|---|---|---|---|---|
| `dn_font_14.c` | interface | **258** | ✅ | ✅ | ✅ | 66 |
| `dn_font_18.c` | interface | **258** | ✅ | ✅ | ✅ | 66 |
| `dn_font_28.c` | interface | **258** | ✅ | ✅ | ✅ | 66 |
| `dn_font_33.c` | **veille** | **96** | ⛔ absent (voulu) | ⛔ absent (voulu) | ✅ | **0** |
| `dn_font_56.c` | **veille** | **96** | ⛔ absent (voulu) | ⛔ absent (voulu) | ✅ | **0** |

*(Relevé par `codepoints_du_c()` sur les cinq `.c` de l'arbre. Les 66 glyphes ≥ U+F000 des polices
d'interface sont les **12 icônes du dépôt** plus les symboles injectés par l'amont ; les polices de
veille n'en portent **aucun**, ce que §29.4 chiffre.)*

⇒ **Cinq `.c`, et cinq seulement** — `dn_font_16/20/22.c` ont bien quitté l'arbre.
🔴 **ET CETTE PREUVE N'EST PLUS UN TABLEAU : ELLE EST UNE GATE.** `bloc_polices_couverture()`
appelle `codepoints_du_c()` sur **chaque** police d'interface et exige `É`, `Û`, `°` et les dix
chiffres. Jusqu'à cette revue, `codepoints_du_c()` n'était appelé **que** sur 33 et 56 : la police
qui porte désormais **le titre, la date ET les libellés** n'avait **aucun** contrôle de couverture,
et son drapeau « interface » de `DN_FONT_LISTE` est posé **à la main** par le générateur d'après le
tuple d'origine, ⛔ jamais relu de la plage gravée. *(Pas de défaut vivant — vérifié —, mais une
garde qui n'était pas prouvée.)*

## §29.8 — AC2.4 : LE CALCUL HORS CARTE, **CONFRONTÉ**

Le cadrage pose `adv_w ÷ taille = 0,695`, constant à 0,1 % ⇒ largeur **linéaire** en la taille, donc
14 → 28 devrait valoir **×2,000**. Mesuré sur huit chaînes : **min 2,018 · max 2,174 · moyenne
2,057**.

⇒ Le modèle **sous-estime de +0,9 % à +8,7 %** (moyenne **+2,9 %**), et **toujours du même côté** :
celui qui fait croire que ça tient. ⛔ Ce n'est **pas** *« l'estimation est fausse »* au sens de
`dn3-1` (22 px d'erreur sur 205) — c'est **un biais systématique et optimiste**. Les deux
propositions sont **distinctes**.
✅ Les prédictions faites depuis ce biais corrigé (`AMBIANCE` ~103 à 18, `HEURE NON POSÉE` ~166 à 16)
ont été **confirmées par la mesure** (103 et 164).

## §29.9 — CE QUE CETTE SECTION NE PROUVE **PAS**

- ⛔ **Aucune mesure de charge** n'a été prise : `px/cycle`, `ms/cycle` et `duty` **changent** (tous
  les pixels du chrome ont bougé) mais n'ont **pas** été re-relevés. ⇒ **tout chiffre de `dn4-5` /
  `dn4-10` / `dn4-12` cité après le 2026-08-30 doit porter son SHA.**
- ⛔ Le soak `dn4-5` a été **coupé** (60 317 trames valides · 483 pertes seq · latence n=60317
  1/174/541 ms, sur `6af9bd8`) et **redémarré** sur `8308bbf`. **Ordre B, décision owner.**
- ⛔ `DÉMO 2+JAUGE` **déborde toujours la réserve du badge** (147 px pour 107 en 18) : c'est une
  case d'**instrument**, et elle sert désormais de **témoin négatif permanent et gratuit** de la
  garde de largeur. ⚠️ **Elle n'est PAS clippée** (elle finit à 199 < 225) et son badge est masqué —
  voir §29.1, revue du 2026-08-30.
- ⛔ Le badge « SIMULÉ » reste en `dn_font_14` — **contraint par sa largeur**, hors périmètre.

## §29.10 — 🔬 REVUE DE CODE 3 COUCHES DU 2026-08-30 — CE QU'ELLE A TROUVÉ, ET CE QU'ELLE A COÛTÉ

Périmètre `ae18700..cea2481` (11 fichiers, +1 873 / −56, hors les 4 422 lignes générées de
`dn_font_18.c`). ⚠️ Le baseline du frontmatter (`a503e66`) **n'a pas été retenu** : `ae18700`
appartient à `dn4-14` et avait déjà été revu sous son nom. **29 constats retenus, 2 écartés.**

**LES QUATRE CONSTATS QUI CHANGENT LE COMPORTEMENT, ⛔ pas seulement les mots :**

1. 🔴 **`W_SEC_H` était resté à 20 alors que la ligne secondaire dessine 25 px.** La constante valait
   exactement `2 + lh(dn_font_14)` ; depuis que le libellé **suit le titre** (`s_titre_suit = true`,
   verdict owner), il prend `dn_font_18` (`lh` 23). ⇒ La garde `y_bas + W_SEC_H <= h` passait
   pendant que LVGL clippait, et la branche `else` — **celle qui DIT que la secondaire est
   abandonnée** — n'était jamais atteinte. C'est la panne muette que W5 avait rendue audible,
   **réarmée par la story qui change les polices**. ⚠️ Latent à `h = 163` (les marges absorbent les
   5 px), atteignable par `widget val`, `widget grille` et `widget voie`, tous dans la plage
   acceptée. ⇒ `W_SEC_H` est **supprimé** ; la réserve est `sec_h()`, relue de la police posée.
2. 🔴 **Aucune garde VERTICALE sur les deux polices que la story rend commutables.**
   `widget titre 28` était accepté : boîte 22..57 contre `val_y = 48`, **9 px de recouvrement** avec
   la première ligne de valeur, sans log ni compteur — pendant que `dn_widget.h` publiait
   « 20 px est le plafond VERTICAL du titre ; 22 est RÉFUTÉ ». **Un plafond publié que personne
   n'exécute n'est pas un plafond.** Et `widget date 28` posait 28..63 dans une barre de 60, le
   plancher `53` de `dn_ui_bandes_valider()` étant **écrit** et justifié par un commentaire qui
   parlait encore de `dn_font_14`. ⇒ `dn_widget_titre_bas()` et `dn_ui_barre_plancher()` sont deux
   fabriques, et les deux validateurs les appellent.
3. 🔴 **Le balayage du pire cas mesurait des dates impossibles et en ratait une réelle** — voir
   §29.2.
4. 🔴 **Le clip ACCEPTÉ de la barre n'avait aucun instrument.** Le titre a reçu `ESP_LOGW` +
   compteur dans le commit même de la story ; la date, sur le **seul texte que la story SAIT
   déborder**, n'avait ni log ni compteur ⇒ `widget` rendait « 0 trop-large » pendant que
   « HEURE NON POSÉE » était clippée à l'écran. ⇒ **Quatrième compteur**, séparé des trois autres.

**LES DEUX GATES QUI NE GARDAIENT RIEN :**

- 🔴 **`bloc_polices` n'exécutait JAMAIS le générateur.** Il regexait `TAILLES` et comparait au
  `dn_font.h` **commité** — un artefact de build versionné. **Mesuré** : en remplaçant
  `decl = lambda ts: …` par une constante — c'est-à-dire en **réarmant le défaut d'AC3.1** —,
  `bloc_polices` rendait toujours **24 OK / 0 KO**. ⇒ `bloc_generateur_execute()` **appelle**
  `ecrire_entete()` dans un répertoire jetable, confronte son produit au `.h` de l'arbre, puis
  retire une taille de `TAILLES` et voit la déclaration **disparaître**. ✅ **Vu rougir** sur ce
  mutant exact.
- 🔴 **La garde « le README ne porte plus de SECOND compte » mesurait une FORME MARKDOWN.** Elle
  exigeait `**` collés au nombre ; le README bolde la phrase entière, donc `re.findall` rendait
  `[]` et la gate imprimait « trouve : aucun » — **verte, sur exactement la 5ᵉ rupture qu'elle avait
  été écrite pour clore**, qui était toujours vivante (« le compte passe de CINQ à DOUZE » contre le
  16 publié plus bas, dans la même ligne).
- 🔴 **Et une gate qui MEURT n'a pas de verdict.** Reproduit : écrire `TAILLES=(14, 18, 28)` **sans
  espaces** ⇒ `AttributeError` dans `bloc_polices_mutants`, **après 200 lignes `[OK ]` et AVANT la
  ligne `BILAN`**. Un humain voit des dizaines de OK et croit avoir lu un résultat. ⇒ `lire()` et le
  bloc rendent désormais un KO et laissent le bilan s'imprimer.

**⚠️ ÉCART DÉCLARÉ — AC5.5 « deux mutants vus rougir » est RÉFUTÉE.** Les trois contrôles dits
« mutants » **relisent du texte ou restatent le prédicat en Python** : (a) est vrai par construction
dès que son voisin est vert ; (b) réimplémente `police_interface()` / `valider_titre()` en Python et
teste la lambda — ⛔ jamais `dn_ui_geom_valider()`, que la gate se borne à grepper ; (c) est un `in`
textuel sur 400 caractères. **Une régression côté C ne ferait rougir aucun des trois.**
✅ **Verdict owner du 2026-08-30 : fermeture avec écart déclaré**, ⛔ pas de `[CC]`. **Coût du
report, écrit** : la garde veille/interface reste vérifiée **par relecture**, ⛔ pas par mutation.
Le différé « `s_trop_larges++ == 3` épingle un total » relève de la même refonte.

**📊 LE COÛT DE LA REVUE, MESURÉ :**

| | binaire | delta |
|---|---|---|
| `cea2481` (avant revue) | 1 226 864 | — |
| après les 25 correctifs | **1 228 864** | **+2 000** |

⚠️ **Le `1 225 440` de §29.7 est la mesure à `34d3c2c`**, ⛔ pas à `cea2481` : `8308bbf` a ajouté
1 424 o. Un delta se prend entre **deux points nommés**.

**🔬 GATES : 237 → 267 OK / 0 KO** (+30 contrôles), dont trois blocs neufs
(`bloc_generateur_execute`, `bloc_polices_couverture`, `bloc_barre_date_forme`) et **deux mutants
vus rougir puis revenir au vert** (le générateur réarmé, et le format de date désaccordé d'un
espace).
🔴 **ET LE « 187 → 237 » PUBLIÉ PAR LA STORY EST FAUX** : rejoué sur worktree, `ae18700` rend
**193 OK / 0 KO** — le 187 est la valeur d'**avant** `ae18700`, donc d'avant `dn4-14`. `dn4-14-2`
ajoutait **44** contrôles, pas 50 ; la revue en ajoute 30 de plus.

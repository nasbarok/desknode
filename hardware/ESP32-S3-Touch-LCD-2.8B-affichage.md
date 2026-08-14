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
| I²C (bus unique) | SDA = GPIO**15**, SCL = GPIO**7** | 400 kHz ; TCA9554 répond à **0x20** |
| 3-wire SPI (init ST7701S) | SDA = GPIO**1**, SCL = GPIO**2** | ⛔ **partagées avec le slot TF** — ne jamais initialiser la SD |
| **LCD_RST** | expander **bit 0** (EXIO1) | derrière le TCA9554 |
| **TP_RST** | expander **bit 1** (EXIO2) | *voir §1.3* |
| **LCD_CS** | expander **bit 2** (EXIO3) | derrière le TCA9554 |
| Rétroéclairage | GPIO**6** | GPIO direct, ON/OFF (la gradation est dn1-3) |

> ⚠️ **La numérotation Waveshare `EXIO1..EXIO8` est en base 1 ; l'index du driver
> est en base 0.** `EXIO1` = bit **0**. Confirmé indépendamment par le YAML
> ESPHome de cette carte (pin 0 = display reset, pin 1 = touch reset,
> pin 2 = display CS). Se tromper d'un rang, c'est réinitialiser le tactile en
> croyant réinitialiser la dalle, sans aucun message d'erreur.

### 1.3 État dans lequel P1 laisse le tactile — **à lire avant dn1-4**

Le bit 1 (**TP_RST**, le reset du GT911) est laissé **DÉLIBÉRÉMENT en ENTRÉE**,
c'est-à-dire dans l'état de mise sous tension du TCA9554 (haute impédance).
P1 ne le pilote pas : le mettre en sortie lui imposerait un niveau qu'on n'a pas
mesuré, et le GT911 échantillonne son adresse I²C au relâchement de son reset.
**dn1-4 part donc d'un TP_RST non piloté, pas d'un TP_RST haut.**

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
| `CONFIG_LCD_RGB_RESTART_IN_VSYNC` | n | **y** | **mesuré nécessaire** — voir §5.1 |
| `CONFIG_LCD_RGB_ISR_IRAM_SAFE` | n | **y** | **mesuré nécessaire** — voir §5.3 |
| `CONFIG_SPIRAM_XIP_FROM_PSRAM` | n | **n** | **mesuré INUTILE ici** — voir §5.3 |
| `CONFIG_FREERTOS_HZ` | 100 | **1000** | un tick de 10 ms est plus grossier qu'une trame (26,7 ms) |
| `CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG` | UART0 | **USB** | console interactive : un seul binaire pour toutes les mesures — *coûte le log sur le header UART* |

> ⛔ **`CONFIG_SPIRAM_SPEED_120M` est INTERDIT sur ce produit.** Le Kconfig
> d'Espressif prévient qu'en octal, 120 MHz est expérimental et que *« si la puce
> démarre à une certaine température, puis que la température varie d'environ
> 20 °C, les accès PSRAM plantent aléatoirement »*. DeskNode vit H24 sur la
> façade d'une tour de jeu : l'écart de température est le **régime nominal**,
> pas un cas limite. Ce n'est pas une piste d'optimisation, c'est une panne
> programmée.

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
| `num_fbs` | **2** | le double tampon ne supprime pas le déchirement à lui seul (§5.2), mais il est le socle de la seule configuration qui l'atténue |
| `fb_in_psram` | **1** | 614 400 o ne tiennent pas en RAM interne |
| `bounce_buffer_size_px` | **0** | **éliminé, deux symptômes distincts** (§5.3) |
| XIP (`SPIRAM_XIP_FROM_PSRAM`) | **désactivé** | **ne change rien au défaut visé** et coûte 342 876 o de PSRAM (§5.3) |
| Bascule d'image | **attendre `on_frame_buf_complete`** | seule variante qui réduit le déchirement (§5.2) |
| Emplacement de l'asset | **partition de données `mmap`ée** | `EMBED_FILES` mettrait 600 Ko en `.rodata`, recopiés en PSRAM si XIP était activé |

Ces valeurs sont les **défauts d'un clone neuf** (`dn_bootcfg.c`) : NVS vierge ⇒
`num_fbs=2, bounce_px=0`. Vérifié en effaçant la région NVS puis en rebootant.

---

## 5. Les chiffres, datés du 2026-08-14

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
gauche. **Preuve que c'est bien un décrochage DMA** : un appel manuel à
`esp_lcd_rgb_panel_restart()` (commande console `dma`) remet l'image en place
d'un coup. Avec le symbole activé, l'image est cadrée dès le boot, sans geste.

### 5.2 Déchirement (AC5)

**Instrument validé par témoin positif.** À `num_fbs=1` on écrit dans le
framebuffer que la DMA est en train de lire : le déchirement **doit** s'y voir.
Observé : *« brisé en escalier et pas de la même taille, brisé sur le dessus »*.
L'instrument voit ce qu'il prétend voir.

Stimulus : barre verticale blanche de 64 px balayant sur fond noir, trame
entière redessinée à chaque pas.

| Branche | Cadence | Ce qui est VU |
|---|---:|---|
| `num_fbs=1`, aucune synchro | 28,9 Hz | escalier franc, tranches inégales — **témoin positif** |
| `num_fbs=2` + `draw_bitmap` seul | 29,1 Hz | **INCHANGÉ** |
| `num_fbs=2` + attente **VSYNC** | 18,2 Hz | escalier sur **la moitié** de la barre |
| **`num_fbs=2` + attente `on_frame_buf_complete`** | 18,2 Hz | **résiduel confiné aux ~15 % du haut — RETENU** |
| `num_fbs=2` + les deux | 12,5 Hz | **régression** au niveau du VSYNC seul |

> **Réfutation.** `research-paysage.md` §4 annonçait « parade = double framebuffer
> PSRAM + VSYNC ». Le **double framebuffer seul ne change rien** : dans
> `esp_lcd_panel_rgb.c`, `draw_bitmap` bascule le lien DMA **immédiatement**, avec
> ce commentaire d'Espressif — *« because of DMA prefetch, there's possibility
> that the old frame buffer might be sent out again; it's hard to know the time
> when the new frame buffer starts »*. C'est la moitié « + VSYNC » qui fait le
> travail, et **pas le VSYNC** : le bon signal est `on_frame_buf_complete`, qui
> dit « l'ancien tampon a fini d'être lu », là où le VSYNC dit seulement « une
> trame commence ».

> ⚠️ **Ces chiffres valent pour un stimulus ADVERSE** : trame pleine redessinée
> (614 400 o) à la cadence maximale, soit ~30 ms par trame contre 26,7 ms de
> période d'affichage. Une UI réelle redessine des rectangles sales, pas la trame
> entière. **Le résiduel des 15 % est mesuré sous une charge que le produit ne
> verra pas.**

### 5.3 Contention flash ↔ PSRAM (AC6)

Stimulus : effacement + écriture de secteurs de 4 KiB en boucle sur la partition
`stimulus`, **sans pause**, ~**150 000 à 185 000 o/s soutenus**, ~45 secteurs/s.

**Symptôme observé, et il est pire que ce qui était annoncé** : ce n'est pas un
« scintillement », c'est **« l'image défile vers la droite EN PERMANENCE »** — un
décrochage DMA qui se reproduit à chaque secteur et dont le décalage s'accumule.

| Branche | Sous stimulus | Après arrêt |
|---|---|---|
| **bounce 0, XIP n, `ISR_IRAM_SAFE=y`** | défile | **entièrement recadrée** par `dma` — **RETENU** |
| bounce 0, **XIP y** | défile pareil | — |
| **bounce 19 200 px**, `ISR_IRAM_SAFE=y` | **redémarrage watchdog** | — |
| bounce 19 200 px, `ISR_IRAM_SAFE=n` | défile | décalage **VERTICAL persistant**, `restart()` inefficace |

- **XIP est réfuté pour ce défaut.** XIP retire les *lectures* de code depuis la
  flash ; notre stimulus fait des *écritures* flash explicites, qui bloquent SPI0
  de toute façon. Coût mesuré s'il était activé quand même : **−342 876 o de
  PSRAM** (8 385 048 → 8 042 172 o libres avant framebuffers), **+1,6 Ko** de
  binaire (356,4 → 358,0 Ko), temps de boot **inchangé** (854 ms contre 864 ms).
- **Le bounce buffer est éliminé, avec deux symptômes distincts.** Avec
  `CONFIG_LCD_RGB_ISR_IRAM_SAFE=y` il provoque un **redémarrage watchdog** dès la
  première seconde du stimulus — relevé verbatim : `rst:0x8 (TG1WDT_SYS_RST)`,
  `W boot.esp32s3: PRO CPU has been reset by WDT`. Mécanisme : l'ISR de
  remplissage du bounce buffer doit lire le framebuffer **en PSRAM** alors que
  l'effacement flash a coupé le cache. Sans `IRAM_SAFE`, plus de watchdog, mais
  l'image défile **et** garde un décalage **vertical** permanent que
  `esp_lcd_rgb_panel_restart()` ne rattrape pas. Coût qu'il aurait fallu payer :
  **−74 584 o de RAM interne** (348 323 → 273 739 o libres).
- **La configuration retenue récupère intégralement.** Après 857 secteurs
  (3 510 272 o) écrits puis arrêt du stimulus, un `dma` remet l'image
  entièrement en place — horizontalement **et** verticalement.

> ⚠️ **Pourquoi le fps ne sert à rien ici.** Mesuré : **37,33 Hz avant** le
> stimulus, **37,45 Hz pendant**. Le contrôleur LCD garde sa cadence même affamé —
> il sort des pixels périmés. **L'instrument d'AC6, c'est l'œil, pas le compteur.**
> C'est aussi ce qui a affaibli la justification de `ISR_IRAM_SAFE=y` : il avait
> été activé pour que le compteur voie pendant les écritures flash, or il n'y a
> rien à y voir. Il est **conservé pour une autre raison** — sans lui, le
> décalage devient partiellement irrattrapable.

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
| RAM interne libre (config retenue) | **348 615 o** |
| Temps de boot (`app_main` → prêt) | **858 ms** |
| Taille du binaire | **356,4 Ko** (0x57b20) sur une partition de 4 MiB — 91 % libre |

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
> C'est aussi pourquoi le stimulus d'AC5 plafonne à ~29 Hz et pourquoi le
> déchirement y est inévitable.
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

## 7. Éliminations, avec leur symptôme

*Une élimination sans symptôme relevé n'est pas une élimination, c'est une opinion.*

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

- **Le déchirement résiduel des ~15 % du haut** en redessin plein écran. Piste
  non explorée : `refresh_on_demand`, et surtout le redessin par rectangles sales
  que LVGL fait nativement (dn1-3).
- **La contention flash ↔ PSRAM** n'a **aucune parade logicielle** trouvée. La
  mitigation est architecturale : **ne pas écrire en flash pendant l'affichage**.
  La décision owner **D4** (pas d'OTA en V1) va déjà dans ce sens. Toute écriture
  inévitable doit être suivie d'un `esp_lcd_rgb_panel_restart()`.
- **L'identité visuelle** du Living PCB : l'asset de P1 est un brouillon assumé
  (dn3-3).
- **La gradation** du rétroéclairage (dn1-3) : ici GPIO6 est en tout-ou-rien.
- L'inventaire physique des breakouts et le câblage photographié (dn2-1, dn4-1) —
  **ce fichier ne couvre que l'affichage**.

---

## 9. Rejouer les mesures

Toutes les mires et tous les stimuli sont dans le firmware, accessibles à la
console série (`idf.py monitor`, taper la commande) :

```
scene bits|nbits|rgb|red|green|blue|white|black|frame|gray|asset
fps [secondes]      mesure et confronte aux 37,40 Hz théoriques
bw                  bande passante des 3 chemins de copie
mem                 PSRAM et RAM interne, avant/après framebuffers
cfg / set fbs N / set bounce N / reboot
tear on|vsync|sync|both|flip|off      les 5 branches d'AC5
flash on|off        le stimulus d'écriture flash d'AC6
disp on|off         sortie d'affichage de la dalle (0x29/0x28)
bl on|off           rétroéclairage
dma                 esp_lcd_rgb_panel_restart()
```

> ⚠️ **`reboot` fait tomber l'attachement `usbipd`.** `esp_restart()` se comporte
> comme un reset de puce : l'USB se ré-énumère, `/dev/ttyACM0` revient en
> `root:root` et toute lecture échoue avec `[Errno 13] Permission denied`.
> Rejouer `./tools/wsl-attach.sh` après chaque `reboot`. C'est le même fait que
> dn1-1 avait mesuré pour le bouton RESET et `--after watchdog_reset`.

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

## 0. LA CONFIGURATION DE RÉFÉRENCE POUR dn1-4 → dn3 — arbitrée le 2026-08-15 (dn1-3, AC6)

C'est la seule chose à lire si on ne lit qu'une chose.

| | | justifié par |
|---|---|---|
| `num_fbs` | **1** | le double tampon est **réparé** (§4 ter) mais n'apporte **rien de mesuré** : il ne corrige ni le déchirement (c'est la synchro qui le fait) ni l'artefact §10.5, et coûte 614 400 o + une branche Kconfig |
| Rendu LVGL | **PARTIEL** | un plein écran demande 10 flushes et ~176 ms d'attente, soit ~5,5 Hz au mieux (§10.3) |
| Draw buffer | **480 × 64 px (61 440 o), RAM interne DMA** | A/B à aire identique : la PSRAM est **1,70× plus lente** ; le régime produit tient en **un seul flush** à 64 lignes (§10.3) |
| Synchro du flush | **`vsync`** | témoin positif établi : en `off` l'œil **voit** le déchirement, en `vsync` il disparaît (§10.4) |
| `RESTART_IN_VSYNC` | **`y`** (livré) | `n` n'est requis que par la branche d'essai du double tampon (§4 ter) |
| Rétroéclairage | **LEDC 10 bits @ 24 kHz** | 5 kHz **siffle** à duty bas, mesuré à l'oreille (§10.6) |
| Cœur de la tâche LVGL | **0** | sans effet mesuré sur l'artefact §10.5 ; retenu par cohérence avec le reste du pipeline |
| Fond | **flash `mmap`** | la copie PSRAM coûte 614 400 o et ne change rien de mesuré (§10.5, ligne 2) |

**Ce que cette configuration NE ferme PAS** : l'artefact de redessin de la §10.5, ouvert, avec
sept hypothèses déjà éliminées. Il est le legs principal de dn1-3 à dn1-4.

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
| `bounce_buffer_size_px` | **0** | **éliminé, deux symptômes distincts** (§5.3) |
| XIP (`SPIRAM_XIP_FROM_PSRAM`) | **désactivé** | **RÉFUTÉ** : défilement identique avec et sans, et coûterait 342 876 o de PSRAM (§5.3) |
| Bascule d'image | ⛔ **SANS OBJET en `num_fbs=1`** | il n'y a plus qu'un tampon, donc plus de bascule. Le verdict *« attendre `on_frame_buf_complete` »* était mesuré dans une configuration où le double tampon ne fonctionnait pas (§4 bis) : il est **retiré**, pas reporté. La question se reposera en dn1-3, dans les bons termes |
| Emplacement de l'asset | **partition de données `mmap`ée** | `EMBED_FILES` mettrait 600 Ko en `.rodata`, recopiés en PSRAM si XIP était activé |

Ces valeurs sont les **défauts d'un clone neuf** (`dn_bootcfg.c`) : NVS vierge ⇒
`num_fbs=1, bounce_px=0, draw_lines=64, draw_psram=0, lvgl_core=0`. Vérifié en
effaçant la région NVS puis en rebootant.

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

### 10.5 🔴 L'ARTEFACT DE REDESSIN LVGL — ouvert, caractérisé, sept hypothèses tuées

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
| Papillotement à 3 % | **présent — mais PAS imputable au rétroéclairage.** Témoin : LVGL mis en pause à luminosité identique, l'image est **parfaitement stable**. C'est l'artefact §10.5, que la basse luminosité rend plus visible |
| Plancher lisible | **3 % = limite** — le Living PCB et le label s'y distinguent encore, tout juste. C'est le plancher du futur mode Ambient |
| Rampe 100→10→100 | ⚠️ **CONSTAT NON FAIT** — l'owner n'était pas devant la dalle, deux tentatives. Ce n'est pas « pas de palier », c'est **pas observé**. À rejouer en dn1-4 |
| `bl 0` vs `disp off` | distincts et documentés dans l'aide : noir contre gris éclairé |

### 10.7 L'observation « textes fins violets » — REPRODUITE

Héritée de dn1-2 sur l'asset v0, elle était à rejouer sur du texte antialiasé LVGL.
**Constat owner : « oui le texte est violet ».** Le phénomène **se reproduit** sur les jambages
fins du label (Montserrat 28, blanc sur fond sombre). Explication non exigée par la story, non
fournie ici. Il n'est donc pas propre au générateur d'asset : c'est la dalle, le sous-pixel, ou
la conversion RGB565 — à trancher si un jour ça gêne.

---

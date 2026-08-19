# DeskNode

Mini-display tactile 2,8" (Waveshare **ESP32-S3-Touch-LCD-2.8B**, 480×640 IPS portrait) **posé à
côté de la tour PC** (décision owner du 2026-08-17 — le brief dit encore « monté sur la façade du
NZXT Phantom 630 », c'est périmé : pas de support imprimé, pas de passage de câble interne, et le
capteur mesure l'ambiance là où il est posé, ce qui est assumé). Affiche en continu 6 métriques — CPU, GPU, RAM,
réseau (via un agent Windows) + température, humidité (capteurs I²C locaux) — avec deux états
visuels (**Ambient** H24 / **Actif** au toucher) et une identité « **Living PCB** ».

## Pilotage projet

Le cockpit BMad (brief, epics, stories, sprint status) vit dans le repo `compagnon_project` :

- Brief : `compagnon_project/_bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/`
- Epics V1 : `compagnon_project/_bmad-output/planning-artifacts/epics-desknode-v1.md`

La V1 avance par **escalier de mini-POC** (P0 toolchain → P9 endurance H24), chaque marche
fermant une question technique par la mesure. Les choix techniques (framework, transport
PC↔module, agent Windows) sont **ouverts** tant qu'un POC ne les a pas tranchés.

## Arborescence

```
docs/       vision, roadmap, notes de câblage, photos
firmware/
  hello-desknode/   P0 — TÉMOIN MINIMAL, figé. Log + rétroéclairage clignotant.
                    Quand le bring-up de l'écran part en vrille, c'est lui qui
                    prouve en 6 s que la chaîne build/flash/monitor n'est pas en
                    cause. Ne pas l'enrichir.
  desknode/         P1+ — le vrai firmware : écran RGB, mires, mesures, console.
    main/dn_widget.c/.h   dn3-1 — LE MODÈLE DE CASE du dashboard (icône, titre,
                          valeur(s), unité, couleur, indicateur, secondaires).
                          Son en-tête porte le CONTRAT DE VERROU et la raison
                          pour laquelle il est inversé. Il possède aussi la
                          BRIQUE TACTILE : les deux drapeaux qui rendent vraie
                          « toute la case est la zone tactile » n'ont plus
                          qu'UNE définition dans tout le firmware.
    main/dn_rtc.c/.h      dn3-2 — L'HEURE DU MODULE (PCF85063A @ 0x51). Driver
                          MAISON, et le motif est écrit dans son en-tête : le
                          composant `waveshare/pcf85063a` passe pourtant le
                          critère du bus, mais il MASQUE le bit OS (`& 0x7F`,
                          deux sites) — avec lui, la barre ne peut PAS savoir
                          qu'elle ment. `espp/pcf85063` est du C++ + 2 dépendances
                          de framework. L'en-tête porte aussi les LECTURES DE
                          REGISTRE qui ont qualifié la puce et RÉFUTÉ le variant TP.
    main/fonts/           dn3-1 — dn_font_14.c / dn_font_28.c / dn_font.h,
                          GÉNÉRÉS et VERSIONNÉS (voir § Les polices).
hardware/   ESP32-S3-Touch-LCD-2.8B-affichage.md  <- LA config d'affichage de
            référence (brochage VÉRIFIÉ, timings, framebuffer, chiffres datés).
            ESP32-S3-Touch-LCD-2.8B-liaison-pc.md <- §12, la FOURCHE TRANSPORT
            (dn2-2) : verdict USB série, protocole de trame, budgets liaison.
            ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md <- §13, LE BUS I²C EXTERNE
            (dn2-1) : brochage du connecteur MESURÉ (le wiki avait SDA/SCL
            inversés), les 4 occupants réels du bus, la commande `i2c` et son
            défaut de faux positifs, l'arbre de diagnostic du BME680.
assets/     assets graphiques 480×640
  mockups/living-pcb-v0.png   prévisualisation COMMITÉE de l'asset généré
agent/      dn_agent.py — l'agent PC (Windows), **5 métriques / 7 grandeurs** à 1 Hz (voir § L'agent PC)
tools/      wsl-attach.sh (attachement USB WSL)
            gen_living_pcb.py (génération de l'asset 480×640)
            gen_font_dn.py (génération des polices — voir § Les polices)
tests/      harnais et smokes
```

> ⚠️ **Deux projets firmware, et c'est voulu** (décision D-F de dn1-2).
> `hello-desknode` a une configuration minimale et **figée** ; `desknode` a une
> configuration radicalement différente (PSRAM octale, 16 MB, partitions, ISR en
> IRAM). Les garder séparés préserve un A/B propre et un témoin qui compile
> toujours.

## Toolchain / build & flash

> Tout ce qui suit est **mesuré sur la tour `DESKTOP-08RT3CL` le 2026-08-14** (story dn1-1), pas
> recopié d'une doc. Les chiffres et les messages d'erreur sont ceux de cette machine.

### Versions figées

| Élément | Version | Où |
|---|---|---|
| ESP-IDF | **v5.5.5** (commit `b774170f`) | `~/esp/esp-idf` |
| Cible | `esp32s3` uniquement | `install.sh esp32s3` |
| esptool **côté IDF/WSL** | **4.12.0** — sous-commandes en `write_flash` (underscores) | embarqué par l'IDF |
| esptool **côté Windows** | **5.3.1** — sous-commandes en `write-flash` (tirets) | `pip install --user esptool` |
| usbipd-win | **5.3.0** | `C:\Program Files\usbipd-win\usbipd.exe` |
| Carte | ESP32-S3 rev **v0.2**, 8 MB PSRAM, MAC `a0:f2:62:e3:d7:f4` | USB natif `303a:1001` |

**Composants managés de `firmware/desknode`** — versions **épinglées à l'exact** dans
`main/idf_component.yml`, et ce que `dependencies.lock` a réellement résolu :

| Composant | Épinglé | Résolu | Rôle |
|---|---|---|---|
| `espressif/esp_lcd_st7701` | `==2.0.2` | 2.0.2 | driver ST7701(S) « 3-wire SPI + RGB » |
| `espressif/esp_lcd_panel_io_additions` | `==1.0.1` | 1.0.1 | bus 3-wire SPI bit-bangé, CS via IO expander |
| `espressif/esp_io_expander_tca9554` | `==2.0.3` | 2.0.3 | driver TCA9554 (le nôtre est à `0x20`) |
| `espressif/esp_io_expander` | *(transitif)* | 1.2.1 | socle commun des expanders |
| `espressif/cmake_utilities` | *(transitif)* | 0.5.3 | outillage CMake des composants Espressif |
| `lvgl/lvgl` | `==9.5.0` | 9.5.0 | la couche UI (dn1-3). ⚠️ API **v9** : `lv_display_create` / `lv_display_set_buffers`. Tout tuto qui parle de `lv_disp_drv_t` est du LVGL 8 et ne compile pas ici |
| `espressif/esp_lvgl_port` | `==2.9.0` | 2.9.0 | tick esp_timer, tâche LVGL, mutex, et `lvgl_port_add_disp_rgb()` qui prend les handles esp_lcd **déjà créés** par `dn_display` |
| `espressif/esp_lcd_touch_gt911` | `==1.2.1` | 1.2.1 | driver du Goodix GT911 (dn1-4). 🔴 avec `rst_gpio_num = -1` — notre cas, TP_RST étant derrière l'expander — il **saute sa séquence de sélection d'adresse** ; `dn_touch` la joue lui-même AVANT le `new` |
| `k0i05/esp_bme680` | `==1.2.7` | 1.2.7 | driver BME680 (dn2-1). 🔴 **Seul candidat du registre compatible avec CE bus** : `bme680_init()` prend un `i2c_master_bus_handle_t` **déjà créé**. Les trois autres (`esp-idf-lib/bme680` via `i2cdev` legacy, `francisduvivier/bme68x_…` et `espressif/bme690` via `espressif/i2c_bus`) **créent leur propre bus** — éliminatoire ici. ⛔ Il n'existe **aucun** `espressif/bme680`. ⚠️ Premier composant non-Espressif du manifeste ; son `CMakeLists` exotique est **inerte, vérifié par un build**. ⚠️ `bme680_get_data()` boucle jusqu'à **1 500 ms** ⇒ tâche dédiée obligatoire, jamais depuis le REPL |
| `k0i05/esp_type_utils` | `==1.2.7` | 1.2.7 | transitif de `esp_bme680`, sans dépendance propre au-delà de l'IDF. 🔴 **Épinglé EXPLICITEMENT depuis la revue du 2026-08-17** : cette colonne l'annonçait déjà `==1.2.7` alors que **rien ne l'épinglait** — `esp_bme680` le déclare en `>=0.0.1`, et `dependencies.lock` (gitignoré) le résolvait comme tel. Le manifeste étant la seule autorité versionnée, la doc affirmait le contraire du dépôt. Même précédent assumé que `esp_lcd_touch` |
| `espressif/esp_lcd_touch` | `==1.2.1` | 1.2.1 | socle tactile commun. Épinglé **explicitement** bien que transitif : le GT911 déclare `^1.2.0`, donc sans cette ligne le résolveur prendrait « la dernière ». ⚠️ c'est lui qui applique `swap_xy`/`mirror_x`/`mirror_y` **en logiciel**, avec `x_max`/`y_max` comme axe de symétrie |

> ⚠️ **Ce que le portage ne fait PAS, et qu'il faut savoir avant de le croire** (mesuré en dn1-3) :
> en rendu **partiel**, son flush n'attend **rien** — il n'attend `trans_sem` que dans la branche
> `direct_mode || full_refresh` (`esp_lvgl_port_disp.c:748-756`). Le `on_vsync` qu'il enregistre
> alimente donc un sémaphore que personne n'attend. Et cet enregistrement **écrase** celui de
> `dn_measure` (`esp_lcd_rgb_panel_register_event_callbacks` ASSIGNE, ne fusionne pas). D'où
> l'ordre d'appel et le témoin actif au boot — détail en §10.1 du fichier `hardware/`.
> Le binaire passe de **377 664 o à 740 400 o** avec LVGL, puis à **790 736 o** avec le tactile et
> la navigation de dn1-4 ; l'app fait 4 MiB, il reste **81 %**.

> **Pourquoi `dependencies.lock` et `managed_components/` restent gitignorés** — la question
> se reposait légitimement en dn1-2, puisqu'il y a désormais de vraies dépendances.
> Réponse : `idf_component.yml` épingle des versions **exactes** (`==`), pas des plages.
> Le lock ne fixerait donc rien de plus que ce que le manifeste fixe déjà, et il changerait
> à chaque résolution — du bruit dans les diffs sans garantie supplémentaire. C'est le
> **manifeste** qui fait foi ; le tableau ci-dessus enregistre ce qui a été résolu.
>
> ⛔ **Il n'existe AUCUN BSP `waveshare/esp32_s3_touch_lcd_2_8b`** sur le registre
> (vérifié par appel API : `ComponentNotFoundError`). Ne pas le chercher.

⚠️ **Les deux esptool ne sont pas de la même majeure.** Ne jamais copier une commande de l'un vers
l'autre : la 5.x a renommé toutes les sous-commandes.

### Installation — une seule fois

```bash
# 1. Prérequis Ubuntu (aucun n'était présent hormis git)
sudo apt-get update      # obligatoire : l'index périmé fait échouer libssl-dev en 404
sudo apt-get install -y git wget flex bison gperf python3 python3-pip python3-venv \
                        cmake ninja-build ccache libffi-dev libssl-dev dfu-util \
                        libusb-1.0-0 usbutils

# 2. ESP-IDF sur le tag exact (≈ 4,0 Go avec les sous-modules)
mkdir -p ~/esp && cd ~/esp
git clone -b v5.5.5 --recursive https://github.com/espressif/esp-idf.git
cd ~/esp/esp-idf && ./install.sh esp32s3     # esp32s3 seul : inutile de tirer les autres toolchains
```

Côté Windows, dans **PowerShell normal** (pas admin) — version **épinglée**, parce qu'une majeure
esptool renomme toutes les sous-commandes et invaliderait le bloc de flash de la voie A :

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m pip install --user esptool==5.3.1
usbipd list                       # relever le BUSID de la ligne 303a:1001 — ici : 3-1
                                  # (mesuré : 'list' n'exige AUCUNE élévation)
```

Côté Windows, dans **PowerShell ÉLEVÉE** — uniquement ces deux commandes-là, une seule fois :

```powershell
winget install --id dorssel.usbipd-win --exact --version 5.3.0
usbipd bind --busid 3-1           # une fois pour toutes ; l'état passe à "Shared"
```

> Le `bind` est **persistant** : il ne se rejoue pas après un reboot. Seul l'`attach` se rejoue.

### La boucle de travail (voie C — retenue)

Dans **chaque shell WSL neuf** :

```bash
. $HOME/esp/esp-idf/export.sh                      # prépare l'environnement ESP-IDF
cd ~/projects/desknode && ./tools/wsl-attach.sh    # rend la carte visible ; il IMPRIME le port
cd firmware/desknode                               # ou firmware/hello-desknode (le témoin)
idf.py -p /dev/ttyACM0 flash monitor               # quitter le moniteur : Ctrl+]
```

**Ce qu'on doit constater — et ça DÉPEND du projet flashé.**

`firmware/desknode` (P1 et suite) :

- au **log**, et ce sont **deux lignes distinctes, imprimées par deux acteurs différents** :
  - `I (25) boot.esp32s3: SPI Flash Size : 16MB` — c'est le **bootloader**, *avant* `app_main` ;
    elle atteste que l'en-tête flashé annonce bien 16 MB ;
  - puis le bandeau `──── socle ────` de l'application, qui imprime `flash physique détectée : …`
    et `PSRAM : 8388608 o détectés, mode OCTAL, 80 MHz` — celui-là interroge la **puce**.
    ⚠️ Ne pas chercher `SPI Flash Size : 16MB` *dans* le bandeau `socle` : il n'y est pas, et les
    deux lignes ne prouvent pas la même chose (l'en-tête déclaré vs le silicium réel) ;
  - puis `up N s` toutes les 10 s ;
- à l'**œil** : le **dashboard** (barre heure/date, grille 2 × 3, bandeau `MENU`) s'affiche sur
  l'asset **Living PCB** voilé, et le **rétroéclairage est ALLUMÉ FIXE**. ⚠️ **Il ne clignote
  plus** — le clignotement était le signe de vie de P0 ;
- **au DOIGT** (dn1-4) : toucher une case ouvre sa page de détail, le `←` ramène au dashboard ;
- la **console est interactive** : taper `aide` dans le moniteur liste les commandes. Jeu complet :
  `scene`, `fps`, `bw`, `mem`, `cpu`, `cfg`, `set`, `tear`, `flash`, `ui`, `flush`, `anim`,
  `touch`, `nav`, `recal`, `bl`, `disp`, `dma`, `i2c`, `capteurs`, `pc`, `wifi`, `widget`, `rtc`, `reboot`, `aide`. `cfg reset` rend
  les défauts au prochain boot. **C'est `aide` qui fait foi**, pas cette liste. Les commandes de
  dn1-3 et dn1-4 :

  | Commande | Ce qu'elle sert |
  |---|---|
  | `ui [on\|off]` · `ui label on\|off` · `ui bg flash\|psram` | pilote LVGL. ⚠️ `ui off` est **obligatoire** avant `scene` ou `tear` : ces deux-là dessinent une trame entière à la main pendant que LVGL ne redessine que ses zones sales, et l'écran devient inattribuable |
  | `flush` · `flush reset` · `flush sync off\|vsync\|fbdone` · `flush path bitmap\|direct` · `flush full` | le rafraîchissement partiel **en chiffres** : aire, copie, attente de synchro. `sync off` est le **témoin** qui doit produire du déchirement — s'il n'en produit pas, aucune conclusion « pas de tearing » n'est recevable |
  | `anim on [ms]` · `anim off` | stimulus adverse LVGL : barre verticale balayant l'écran |
  | `recal <0..4>` | recalage DMA N vsyncs après une bascule (le double tampon, §4 ter) |
  | `bl <0..100>` · `bl ramp <pct> [ms]` · `bl freq <hz>` | rétroéclairage **gradable**. ⚠️ `bl 0` = dalle NOIRE ; `disp off` = dalle GRISE éclairée |
  | `set lines <8..160>` · `set drawmem <0\|1>` · `set core <-1\|0\|1>` · `set bounce <px>` | variables de mesure du rendu, relues au boot (`reboot` pour appliquer) |
  | **`touch`** (dn1-4) | état du GT911 : adresse **mesurée**, config lue, mode de lecture, compteurs (IRQ, lectures, appuis, erreurs I²C) et **latence tap → écran** |
  | **`touch mode event\|poll`** | mode de lecture de l'indev, **à chaud** — l'A/B d'AC2 sans reflasher |
  | **`touch trace [ms]`** | imprime chaque **APPUI** (avec ses coordonnées brutes) et chaque **TAP** avec sa zone. L'instrument des campagnes au doigt |
  | **`touch int [ms]`** | témoin **physique** de TP_INT : échantillonne la broche sans passer par le driver ni l'ISR |
  | **`touch addr`** | **preuve causale** de TP_INT : deux resets, INT haut puis bas, et l'adresse latchée suit (0x14 / 0x5D) |
  | **`touch axes <swap> <mx> <my>`** | orientation à chaud. ⚠️ les miroirs se replient sur `x_max`/`y_max` : les quatre champs se règlent ensemble. ⛔ **`swap=1` est REFUSÉ** : `x_max`/`y_max` sont figés à 480/640 et un échange d'axes rendrait injoignables les **160 dernières lignes**, bandeau MENU compris (AC2 a mesuré qu'aucune transformation n'est nécessaire) |
  | **`touch delais <bas> <haut>`** | délais de la séquence de reset (1..2000 ms chacun), sans reflasher — puis `touch addr` pour les **appliquer** en rejouant. ⚠️ ce n'est PAS `touch reset`, qui remet les compteurs à zéro : trois commentaires du firmware annonçaient la mauvaise commande |
  | **`nav`** · `nav open <0..5>` · `nav back` | navigation dashboard ↔ détail depuis la console. **Refusée si LVGL est en pause** : elle armerait le chronomètre de latence sur un cycle qui n'aura pas lieu |
  | **`nav model rebuild\|screens`** | le **modèle** de navigation, les deux restent jouables. ✅ **`screens` retenu**, re-mesuré le 2026-08-16 dans la config livrée après correction de la fuite : **307,0 ms** de moyenne contre **346,9 ms** pour `rebuild`, soit 39,9 ms (11,5 %) pour +3 032 o de tas LVGL. *(Les anciens 267,9 / 307,7 avaient été relevés à `bounce_px = 0` sur un A/B qui fuyait ; ils surestimaient le prix de `screens` de 2,7×.)* |
  | **`nav ab <n>`** | N allers-retours scriptés : latences min/moy/max **et** preuve de non-fuite (RAM interne et PSRAM avant/après) |
  | **`capteurs`** (dn2-1) | le **BME680** : état (VIVANT / MUET / jamais lu), valeurs + âge, cadence, cycle de mesure mesuré, compteurs **par cause** (i2c / donnée / bornes / **reconfigurations**). `capteurs gaz on|off` = l'A/B d'auto-échauffement à chaud. 🔴 **`capteurs simuler muet\|bornes\|config <n>`** rejoue une panne SANS toucher au connecteur (un Dupont ne supporte pas les insertions répétées) — l'injecteur ne falsifie que le VERDICT, jamais la lecture, et s'annonce bruyamment. ⚠️ **Elle ne déclenche AUCUNE mesure** : `bme680_get_data()` peut dormir 1 500 ms, et le REPL est le transport PC |
  | **`i2c`** (dn2-1) | le **bus vu de ses adresses** : `i2c` scanne 0x08..0x77, `i2c lire <addr> <reg> [n]` lit un registre (hexa). 🔴 **Chaque adresse trouvée est RE-SONDÉE 5 fois et le résultat publié `n/5`** — un scan à une passe fabrique des faux positifs, et il en a sorti un **à `0x76`, l'adresse du BME680, alors qu'aucun capteur n'était branché** (`hardware/…-capteurs-i2c.md` §13.2). Témoin positif intégré : la commande conclut elle-même sur `0x20`+`0x5D`, et un scan qui ne les voit pas est un instrument cassé. ⚠️ bloque le REPL — donc le transport PC — pendant sa durée (~26 ms) |
  | **`pc`** (dn2-2) | la **liaison PC** : état (VIVANTE / MORTE / jamais reçue), dernière valeur + son âge, compteurs (trames valides, doublons, pertes de seq, **resynchros**, reprises, rejets **par cause** — ⚠️ « tronquée » = la fin de ligne est PERDUE, **« trop longue »** = la ligne dépasse 63 o — deux diagnostics opposés, **MAIS SEULEMENT JUSQU'À 124** : le REPL délivre **124 caractères de trame** au parseur (MESURÉ en dn4-1), donc toute ligne émise à **125 o ou plus arrive AMPUTÉE** — symptôme « tronquée » — tout en étant comptée « trop longue ». 🔴 **La plage réellement discriminante est 64..124** ; au-delà, `rejets_trop_longue` ne prouve plus qu'un émetteur a changé de format, il peut aussi dire que le transport a coupé (revue 2026-08-19)), latence acceptation→label. `pc reset` remet les compteurs **et oublie le seq** (sans ça, une campagne relancée avec la trame d'exemple retombait en doublon et mesurait du vide). **`pc $DN,…`** ingère UNE trame — c'est le dialecte de l'agent en branche A, et l'injecteur des campagnes de bruit. 🔴 **dn4-1** : `pc` liste désormais **les cinq métriques une par une** avec **leur propre état et leur propre âge** (une horloge par métrique) — le résumé global « liaison PC » dirait « VIVANTE » avec quatre cases mortes. Et **`pc pousse groupe\|etale`** est l'A/B du levier n°1 (W4), **NON ADOPTÉ** : mesuré, l'étalement divise le pic par 1,94 mais **jette 18,1 % des mises à jour** (185 poussées atteignent l'écran sur **226** trames reçues : **41 / 226 = 18,1 %** — publié « 19 % » jusqu'au 2026-08-19, ce qui était 185/**228**, le dénominateur de l'autre branche) et multiplie la latence maximale par 4 |
  | **`widget`** (dn3-1) | le **modèle de case** : pour chacune des 6 cases, sa **forme** (widget / nue), son **régime** (RÉELLE / SIMULÉE / ABSENTE), si elle est **dessinée en ce moment**, et ses valeurs — le tout **RELU de l'état réel**, jamais récité d'une constante. Plus la forme **annoncée** de **chacun des quatre mocks** — dn3-2 les a généralisés (W5) : GPU 38→72 **%** / 26 s (⚠️ **dn4-1** : la grandeur 0 du GPU est le **pourcentage** depuis D10 — la rampe s'affiche donc en `%`, pas en °C ; **les nombres et la période ne bougent PAS**, même motif que DISQUE), RAM 18→78 % / 34 s, RÉSEAU 5→985 Mb/s / 14 s, **DISQUE** 800→1600 **Mo/s** / 20 s (⚠️ dn4-1 : la case a changé de métrique **et d'unité**, mais **les nombres et la période ne bougent PAS** — la ligne « mock on » de §16.1 doit rester rejouable à l'identique, et 800-1600 Mo/s reste plausible pour un NVMe), toutes rampes triangulaires au pas de 1 s. ⚠️ **Périodes PAIRES et ≥ 2** — la rampe n'est bornée que dans ce cas, et le boot le **vérifie** désormais. ⚠️ Périodes premières entre elles autant que possible : des périodes multiples feraient battre la grille à l'unisson, ce qui n'est pas le régime réel qu'AC8 chiffre. 🔴 **CPU et AMBIANCE n'ont PAS de mock** : elles ont des sources RÉELLES, et D6 veut que « PC éteint, une seule case sur six est vivante » **se voie**. Et l'icône active. Sous-commandes : **`widget groupe on\|off`** (l'A/B d'invalidation d'AC8, §15.5 — rejouable sans reflasher), **`widget opa <0..255>`** et **`widget voile <0..255>`** (l'A/B d'opacité, §15.6 ; **bornées et REFUSÉES** hors plage, jamais écrêtées), **`widget mock on\|off`** (couper le mock rend la case ABSENTE : c'est le témoin que le mock EST sa seule source), **`widget icone <case> <0..4>`** (l'A/B de glyphe **sur n'importe quelle case** — ⚠️ **dn4-1 l'a généralisé** : il écrivait l'index 4 EN DUR et aurait continué de viser « l'ancienne case ventilateur » après le renommage, en l'annonçant comme un choix), **`widget demo on\|off`** (la **7ᵉ métrique fictive** d'AC1 : une case complète produite par le même appel que les autres, depuis un descripteur et **rien d'autre**), **`widget pousser <idx>`** (UNE mise à jour synthétique — ⚠️ **une par appel**, sinon les N invalidations tombent dans le même cycle LVGL et LVGL les fusionne ; c'est l'appelant PC qui les espace). **`widget oublier <idx>`**, **`widget rafale`** (AC8 — les 6 cases poussées sous **UN SEUL verrou**, donc dans **un seul cycle LVGL** : c'est l'instrument qui produit le cas que l'extrapolation prédit et que le régime réel ne produit **jamais**, puisque les six sources ne sont pas synchronisées. ⛔ Il **contredit délibérément** l'interdit de `pousser`, d'où son autre nom ; 🔴 **elle n'a PLUS de témoin de validité, et c'est délibéré (2026-08-19)** : `cycles pour dessiner la rafale` en était à sa **troisième** sémantique (`cycles intercalés`, puis `== 0`, puis `== 1`) et **n'a jamais pu rendre autre chose que sa valeur de succès** — la boucle d'attente sortait au **premier** cycle observé. Supprimé. ⇒ **la fusion se prouve par `flush`**, et par lui seul : `flush` avant/après le tir doit montrer **N flushes pour UN cycle**. ✅ Effet de bord : la rafale **ne dort plus**), **`widget nue <idx> on|off`** (W11 — rendre une case **nue à chaud** : le **témoin négatif** d'AC8 ne quitte pas le firmware, sinon AC8 comparerait deux firmwares. ⚠️ **reconstruit la scène**), **`widget barre 1hz|minute`** (W2/AC4 — la cadence de la barre heure/date, **défaut = minute** parce que la maquette normative écrit « 21:46 » **sans secondes**), **`widget bandes on|off`** (W8/AC9 — le **levier n°2** : un callback `LV_EVENT_INVALIDATE_AREA` étend chaque zone salie à la **pleine largeur**, pour que deux cases d'une même ligne se CONTIENNENT et que LVGL les joigne. Chiffré en §16.7 : il **gagne SOUS CONDITION**. ⚠️ Absent de ce README jusqu'à la revue du 2026-08-18, alors que §16.7 en publiait déjà les chiffres — « une commande qu'on ne trouve que depuis la carte n'est pas documentée »). ⚠️ **`pousser` ne se retire pas TOUT SEUL** : la case reste SIMULÉE jusqu'à ce que sa vraie source reparle. ✅ **dn3-2 solde ce différé** (`deferred-work.md:1019-1023`) avec **`widget oublier <idx>`**, qui rend la case à son **régime naturel** (ABSENTE ; le mock la reprend au tick suivant s'il est armé, une source réelle la repeindra quand elle parlera). ⛔ **Ne plus rebooter pour ça** : un `reboot` rejoue le boot entier et **perd la fenêtre de mesure**. Sans cette commande, tout constat owner lancé après une campagne verrait des badges « SIMULÉ » **résiduels** et pourrait les lire comme une régression. **`widget piste <0xRRGGBB>`** (la **piste de la jauge**, c'est-à-dire le fond de la part NON remplie — ajoutée en séance le 2026-08-18, `0x203040` → `0x5A5F6A`, arbitrage **à l'œil** ; ⚠️ **reconstruit la scène**. Constat d'origine : *« la barre de vide apparaît en vert »* — **le code n'a jamais posé de vert**, c'est le PCB par contraste simultané). ⚠️ `opa`, `voile`, `icone`, **`nue` et `piste`** **reconstruisent la scène**, ce qui retire le stimulus `anim` et la démo, et ramène la vue au dashboard. 🔴 **Et ce sont les CINQ sous-commandes de `widget` qui BLOQUENT le REPL** — ⚠️ **corrigé DEUX FOIS** : ce paragraphe écrivait « les **trois** seules » **dix lignes après** avoir décrit `widget nue` comme « ⚠️ reconstruit la scène ». Or `nue` est l'instrument **central** du témoin négatif d'AC8, celui qu'on actionne le plus pendant une campagne — — donc le transport PC (dn2-2) — le temps d'un `lvgl_port_lock(2000)` **plus** un `build_scene()` complet : les deux racines sont détruites et reconstruites, soit plus lourd qu'une transition, que §15.6 chiffre à **307-322 ms** avec un plancher de rendu LVGL ~230 ms. Comparaison : `i2c` bloque ~26 ms. Ne pas les appeler pendant une campagne de mesure de la liaison (relevé en revue de code le 2026-08-18 : le docblock de `cmd_widget` affirmait qu'aucune sous-commande n'était un travail long). 🔴 **dn4-6 ajoute SIX sous-commandes qui reconstruisent, et le compte passe de CINQ à ONZE** — ce compte est un point de rupture connu du fichier, il se corrige **ici et dans le docblock de `cmd_widget` dans le même geste**. **`widget voie defaut\|a\|b\|c\|c2`** applique une **voie entière** de l'A/B de dn4-6 et **imprime son PRIX AVANT le constat owner** (⚠️ elle reconstruit **DEUX FOIS** — les bandes, puis la géométrie de case — soit ~700 ms de REPL bloqué) : `a` = police 28 + **MENU supprimé** (case 180) + en-tête compacté ; `b` = 3ᵉ police + D12 (case 163) — 🔴 **la police ~22 n'est PAS embarquée**, la branche est jouée en 14 px, donc « la géométrie est représentative, **la lisibilité ne l'est pas** » ; `c` = **côte à côte**, géométrie **inchangée** ; `c2` = variante **MIXTE** (ligne 1 côte à côte), qui **exige** la case de 180. **`widget dispo empile\|cote\|mixte`** (⛔ **EMPILE reste le défaut** tant que rien ne l'a battu SUR LA DALLE), **`widget entete normal\|compact`** (🔴 **décision OWNER** : elle change les SIX cases, et l'icône est le **seul** endroit où le champ `couleur` du descripteur est EXERCÉ), **`widget val <y> <pas>`** (elle **calcule et imprime** l'interligne, la garde sous l'en-tête et le `y_bas` à 4 grandeurs, et **dit** quand l'interligne passe sous le critère écrit de D12 : ≥ 5 px), **`widget police 14\|28`**, **`widget grille <barre_h> <menu_h>`** (`70 60` = l'état des lieux, `60 51` = D12, `60 0` = voie (a) — ⚠️ elle **annonce que toute coordonnée tactile publiée devient PÉRIMÉE**). Et l'instrument d'**AC5** : **`widget largeur`** rend la table des couples avec leur largeur **RELUE de `lv_text_get_size()`** — la police réellement liée, kerning compris — ⛔ **jamais un produit `nb_caractères × largeur_moyenne`**, qui est l'extrapolation (~15,8 px/car.) ayant servi à **écarter le côte à côte en dn3-1** et que cette table **confronte**. **`widget largeur <texte>`** mesure une chaîne libre, **`widget largeur reset`** remet à zéro le **compteur de chevauchements** — ⛔ parce qu'« un texte trop large ne se voit PAS comme une erreur » : LVGL clippe au parent **sans un mot**, et « rien n'a planté » n'est pas « ça tient ». Enfin **`widget demo on\|off [n]`** : le `n` (1..6) est le **SEUL** chemin vers les deux témoins d'AC2 de dn4-6 — l'abandon de **jauge** (n ≥ 3) et le **clamp** de `DN_WIDGET_GRANDEURS_MAX` (n = 5, donc **au-delà du maximum**, ce qui est le point) |
  | **`rtc`** (dn3-2) | l'**horloge PCF85063A** à `0x51` : état, heure lue **avec sa recevabilité**, âge, registres `0x00..0x11` **RELUS à l'instant**, compteurs **par cause** (i2c / **bcd**), le témoin anti-fantôme, et la pile restante de la tâche. 🔴 **Le bit `OS` (Seconds bit 7) est imprimé en clair et il GOUVERNE l'affichage** : `OS = 1` ⇒ l'oscillateur a décroché ⇒ l'heure lue **ne vaut rien**, et la barre affiche « --:-- HEURE NON POSÉE » — ⛔ **jamais une heure fausse**, parce qu'une barre qui dit « 03:47 » après une coupure est **pire** qu'une barre qui se tait. **`rtc set <AAAA-MM-JJ> <HH:MM[:SS]>`** pose l'heure ; écrire le registre des secondes est ce qui **remet `OS` à 0**, et il n'y a pas d'autre chemin (d'où l'absence de tout `clear_os`). L'écriture est **RELUE** : un `ESP_OK` d'I²C ne prouve pas que la pose a pris. ⚠️ Le **jour de semaine n'est pas demandé**, il est **calculé** de la date (Sakamoto) — la puce ne le déduit pas, elle le compte à part, et le laisser saisir ferait deux sources de vérité. ⚠️ **Époque 2000..2099, et c'est un CHOIX du driver** : la puce porte l'année sur 0..99 et n'a **aucun bit de siècle**. ⚠️ `CAP_SEL` (charge du quartz) est **lu et imprimé mais NON vérifié** : rien sur cette carte ne dit quel quartz est soudé, et un mauvais réglage se paie en **dérive**, pas en panne — consigné comme INCONNU. `rtc reset` remet les compteurs à zéro |
  | **`wifi`** (dn2-2) | la maquette **branche B**, ÉCARTÉE par la fourche (verrou RAM, `hardware/…-liaison-pc.md` §12.2). **Non compilée par défaut** : la commande répond « maquette B non compilee » avec la recette de re-mesure |
  ⚠️ Le log de ce projet ne part **plus** sur le header UART GPIO43/44 : la console primaire est
  passée sur l'USB pour pouvoir RECEVOIR des commandes. Pour retrouver le header, voir le
  commentaire de `CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG` dans son `sdkconfig.defaults` : on y récupère
  le log sur **les deux** chemins **et** la console interactive sur l'UART.

`firmware/hello-desknode` (le témoin minimal de P0) :

- au **log** : `I (12280) desknode: DeskNode P0 - up 12 s - retroeclairage ON`, avec un compteur de
  secondes qui progresse (le CPU exécute *notre* code, pas un tampon figé) ;
- à l'**œil** : le **rétroéclairage de la dalle clignote** à 1 s (GPIO6, un GPIO direct). C'est le
  signe de vie *matériel* — un `printf` ne prouve pas que la carte agit sur quoi que ce soit.
  Le buzzer, lui, est sur `EXIO8`, derrière l'expander I²C TCA9554 : hors périmètre P0.
- son log part sur **les deux chemins** (USB **et** header UART GPIO43/44).

- **Baud du moniteur : 115200** · **baud du flash : 460800** (valeurs par défaut de l'IDF, mesurées
  comme fonctionnelles).
- Durées mesurées : build **incrémental 1 s** (rien n'a changé) · build **après `rm -rf build`
  36 s** · **reconstruction totale 54 s** (après `rm -rf build sdkconfig`, la cible est reposée
  depuis `sdkconfig.defaults`) · **flash 6 s**.
- Le projet vit sur **ext4** (`~/projects/desknode/`). ⛔ Ne jamais le déplacer sous `/mnt/c/…` :
  le 9p de WSL2 y divise les temps de build par un ordre de grandeur.

### Ce qu'il faut refaire — et quand

| Événement | À rejouer | Pourquoi |
|---|---|---|
| **Nouveau shell WSL** | `. $HOME/esp/esp-idf/export.sh` | l'environnement n'est pas persistant |
| **`wsl --shutdown` / reboot Windows** | `./tools/wsl-attach.sh` (les 4 étapes) | les modules noyau et l'attachement tombent |
| **Carte débranchée/rebranchée** | `./tools/wsl-attach.sh` | l'attachement tombe ; le `bind`, lui, survit |
| **Après un `flash`** | **rien** | mesuré : le flash **ne ré-énumère pas** l'USB, l'attachement tient |
| **Après un RESET de la puce** (bouton RESET, ou `--after watchdog-reset`) | `./tools/wsl-attach.sh` | mesuré : là, l'USB **se ré-énumère** et l'attachement **tombe** |
| **Après un `reboot` tapé dans la console de `firmware/desknode`** | `./tools/wsl-attach.sh` | mesuré en dn1-2 : `esp_restart()` compte comme un reset de puce — le port revient en `root:root` et toute lecture sort `[Errno 13] Permission denied` |
| **Après un reset par impulsion RTS** (`./tools/dn_console.py --reset`) | **rien** | ⚠️ mesuré le 2026-08-15 : **contre-exemple à la ligne du dessus.** Tous les resets de puce ne se valent pas — celui-ci donne bien `rst:0x15 (USB_UART_CHIP_RESET)`, mais l'USB **ne se ré-énumère pas** et l'attachement tient. C'est ce qui permet de capturer le bandeau de boot **depuis sa première ligne**, ce qu'un `flash` suivi d'une écoute rate toujours |

⚠️ **Ce sont deux resets différents, et c'est le piège de cette carte.** Le reset *logiciel* que
joue esptool en fin de flash (« Hard resetting via RTS pin ») **ne réinitialise pas** le périphérique
USB-Serial/JTAG : rien ne bouge côté hôte. Le reset *de la puce* (bouton, ou watchdog) coupe tout :
`usbipd list` repasse de `Attached` à `Shared`, `dmesg` affiche `usb 1-1: USB disconnect`, et
`/dev/ttyACM0` devient un nœud mort (`[Errno 19] No such device`).

**Parade si les resets sont fréquents** : `./tools/wsl-attach.sh --auto`. Mesuré : le périphérique
revient **tout seul en ~6 s**. Deux réserves, toutes deux gérées par le script :

- `--auto-attach` ne restaure **que le périphérique** — les droits retombent à `root:root
  crw-------`, donc il faut **rejouer le script** pour pouvoir relire le port ;
- il laisse un **processus Windows résident**. Le script en arrête les anciens avant d'en lancer un
  nouveau (ils ne s'empilent donc pas), et `./tools/wsl-attach.sh --stop-auto` les arrête tous.
  ⛔ **Ce `--stop-auto` est obligatoire avant de passer à la voie A** : un auto-attach vivant
  reprend la carte aussitôt après le `detach`, et `COM3` ne revient jamais côté Windows.

⚠️ `sudo modprobe` et `sudo chown` sont à rejouer **explicitement** : sur cette machine **systemd est
offline**, donc `/etc/modules-load.d/` et les règles `udev` sont **inopérants** — une règle
`/etc/udev/rules.d/*.rules` ne se déclencherait jamais. `tools/wsl-attach.sh` encapsule exactement
ces gestes, c'est sa seule raison d'être.

⚠️ **Ne pas coder `/dev/ttyACM0` en dur dans un outil.** L'index n'est pas garanti, et un nœud gardé
ouvert par un moniteur **survit** à la mort du périphérique (il répond alors `[Errno 19] No such
device`). Le script identifie le bon port par son identité en sysfs (`idVendor`/`idProduct`), qui
disparaît avec le périphérique — puis il **imprime le port** qu'il a trouvé.

### La carte est muette ? (le port s'ouvre mais rien n'en sort)

Symptôme : `/dev/ttyACM0` existe, s'ouvre sans erreur, et ne rend **0 octet**. Ce n'est pas un
problème de câble ni de baud : la carte est très probablement restée en **mode download**, où
l'application ne tourne pas.

> ⚠️ **Le second symptôme dépend du firmware flashé — corrigé en dn1-2.**
> Avec `hello-desknode`, « le rétroéclairage ne clignote plus » était un signe fiable.
> Avec `firmware/desknode`, le rétroéclairage est **allumé FIXE** en fonctionnement normal :
> « il ne clignote pas » n'y veut plus rien dire. Les critères valides pour `desknode` sont :
> **le port est muet** ET **l'écran n'affiche pas l'asset** (dalle noire ou figée).
> Le critère qui marche dans les deux cas reste **0 octet sur le port** — mais ⚠️ **PAS À
> N'IMPORTE QUELLE DURÉE**, et c'est le rejeu à froid du 2026-08-15 qui l'a trouvé.
>
> `firmware/desknode` n'imprime spontanément qu'une ligne de battement **toutes les 10 s**.
> **Cadence RE-VÉRIFIÉE INCHANGÉE par dn1-3** (2026-08-15) puis **par dn1-4**
> (2026-08-16, revue de code) : la ligne s'est enrichie des compteurs de flush, puis
> du tactile, mais le `vTaskDelay(10000)` de `desknode_main.c` n'a pas bougé — la
> durée d'écoute ci-dessous reste donc valable telle quelle. C'est vérifié à chaque
> story parce que changer cette cadence sans changer la recette rendrait la recette
> de survie fausse le jour où on en a besoin. ⚠️ L'AC9 de dn1-4 demandait cette
> re-vérification ; elle avait été faite pour le bloc « voie A » et **pas tracée
> ici** — c'est la revue qui l'a relevé.
> 🔴 **RE-VÉRIFIÉE INCHANGÉE par dn2-2** (2026-08-16, revue de code) : le
> `vTaskDelay(10000)` du battement de `desknode_main.c` n'a **pas** bougé, et dn2-2
> n'ajoute **aucune impression spontanée** — une trame acceptée est silencieuse
> (doctrine du REPL), seuls l'écho et l'invite passent sur le fil. La durée d'écoute
> ci-dessous reste donc valable telle quelle. ⚠️ Et l'histoire s'est répétée : dn2-2
> avait coché sa tâche AC9 sans poser cette trace — **deux stories de suite**, relevé
> par la revue les deux fois. C'est le mémo trois lignes plus haut qui aurait dû
> l'éviter.
> Écouter 6 s sur une carte parfaitement saine rend donc **0 octet** — et diagnostique une carte
> muette qui va très bien. C'est un faux positif qui envoie dérouler une recette de déblocage
> pour rien, sur une carte qu'on va inutilement remettre en mode download.
>
> **Le bon geste, celui qui SOLLICITE au lieu d'attendre :**
>
> ```bash
> python3 tools/dn_console.py "cfg"      # envoie \n, attend l'invite, échoue en 3 s si muette
> ```
>
> Il envoie une ligne vide, attend l'invite `desknode>` et diagnostique lui-même le mutisme. À
> défaut, écouter **au moins 12 s** — jamais moins qu'une période de battement.

⚠️ **Ce bloc est côté WSL, donc esptool 4.12.0** : l'exécutable s'appelle `esptool.py` (il n'y a
**pas** d'`esptool` tout court dans l'environnement de l'IDF) et ses options sont en **underscores**.
Ne pas y recopier la syntaxe en tirets de la voie A, qui est celle de la 5.3.1 côté Windows.

```bash
. $HOME/esp/esp-idf/export.sh    # sans lui, esptool.py n'est pas dans le PATH

# 1. Confirmer : si esptool dialogue SANS reset, la carte est dans le bootloader ROM.
esptool.py --chip esp32s3 -p /dev/ttyACM0 --before no_reset --after no_reset flash_id

# 2. La relancer. ⚠️ `--after hard_reset` NE SUFFIT PAS ici — il faut le watchdog.
esptool.py --chip esp32s3 -p /dev/ttyACM0 --after watchdog_reset flash_id

# 3. Ce reset ré-énumère l'USB : l'attachement usbipd est tombé, il faut le refaire.
cd ~/projects/desknode && ./tools/wsl-attach.sh
```

> ⚠️ **Troisième état, rencontré en dn2-2 : la PANIQUE HALTÉE** (une `assert` avec
> `CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y`). Le symptôme est PIRE que la carte muette :
> même l'étape 1 échoue en **`A serial exception error occurred: Write timeout`** —
> le CPU est halté, l'USB n'est plus servi, aucun octet ne part. La recette :
> `dn_console.py --reset` (impulsion RTS) peut suffire ; sinon **bouton RESET
> physique**, puis rejouer `./tools/wsl-attach.sh`. Vérifié le 2026-08-16.

Succès attendu — **et lui aussi dépend du firmware flashé**, comme le symptôme :

- avec **`hello-desknode`** : le rétroéclairage se remet à **clignoter**, le log reprend à `up 0 s` ;
- avec **`firmware/desknode`** : le rétroéclairage est **fixe** (il ne clignote pas, et ce n'est pas
  un défaut), l'**asset Living PCB réapparaît** à l'écran, le log reprend à `up 0 s` et **`aide`
  répond** dans le moniteur.

Le critère commun aux deux, et le seul qui ne trompe jamais : **le port n'est plus muet**.

### Voie A — build WSL, flash depuis Windows (secours, et cap à terme)

Elle n'installe **rien** sur le système et ne dépend ni de WSL-USB ni du réseau. C'est aussi la
direction visée à terme (fonctionner sans WSL).

**Étape 1 — dans WSL : construire seulement.**

```bash
. $HOME/esp/esp-idf/export.sh
cd ~/projects/desknode/firmware/desknode && idf.py build   # ou hello-desknode
```

**Étape 2 — dans WSL : rendre la carte à Windows.** Sans ce `detach`, `COM3` **n'existe pas** côté
Windows (exclusivité stricte, mesurée). Le BUSID est relu, jamais figé — il change si la carte est
branchée sur un autre port USB physique.

```bash
# Si un ./tools/wsl-attach.sh --auto tourne encore, il reprendrait la carte aussitôt :
./tools/wsl-attach.sh --stop-auto

USBIPD='C:\Program Files\usbipd-win\usbipd.exe'
busid=$(powershell.exe -NoProfile -Command "& '$USBIPD' list" | tr -d '\r' \
        | awk '/303a:1001/ {print $1; exit}')
powershell.exe -NoProfile -Command "& '$USBIPD' detach --busid $busid"
```

**Étape 3 — dans PowerShell : flasher.** Le port est `COM3` sur cette machine ; la première commande
le redonne s'il a changé.

Pour **`firmware/desknode`** (P1 et suite) — **QUATRE fichiers, pas trois** :

```powershell
[System.IO.Ports.SerialPort]::getportnames()

$py = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
$B  = '\\wsl.localhost\Ubuntu\home\nasbarok\projects\desknode\firmware\desknode\build'
& $py -m esptool --chip esp32s3 -p COM3 -b 460800 --before default-reset --after hard-reset `
      write-flash --flash-mode dio --flash-size detect --flash-freq 80m `
      0x0      "$B\bootloader\bootloader.bin" `
      0x8000   "$B\partition_table\partition-table.bin" `
      0x10000  "$B\desknode.bin" `
      0x410000 "$B\living_pcb_v0.bin"
```

> ### ⚠️ Le 4ᵉ fichier n'est pas optionnel
>
> `living_pcb_v0.bin` est l'**asset** de la partition `assets`. Côté WSL,
> `idf.py flash` l'écrit tout seul (via `esptool_py_flash_to_partition` dans le
> `CMakeLists.txt`) : **il n'apparaît nulle part dans la commande**, et c'est
> précisément pour ça qu'on l'oublie en passant à la voie A.

> **Vérifié inchangé par dn1-3 (2026-08-15), RE-VÉRIFIÉ par dn1-4 (2026-08-16), puis
> par dn2-2 (2026-08-16, revue de code).**
> Ce bloc a été relu contre le livrable des trois stories : la table de partitions
> n'a pas bougé (l'app fait toujours 4 MiB à `0x10000`, `assets` toujours 1 MiB à
> `0x410000`), et l'asset non plus (`tools/gen_living_pcb.py` n'a pas été touché).
> **Les quatre offsets restent exacts.** LVGL fait passer `desknode.bin` de
> 377 664 à ~740 400 o, le tactile + la navigation de dn1-4 à **790 736 o** (dont
> +7 936 o de correctifs de revue), et la liaison PC de dn2-2 à **796 240 o**
> (`dn_link` + `pc` + stubs `dn_wifi` + les correctifs de revue) — soit **81 % de la
> partition encore libre**. Ça tient largement — mais c'est bien le genre de croissance
> qui finirait par obliger à revoir la table, et c'est pour ça qu'on le note ici plutôt
> que de supposer que « ça n'a pas dû changer ».
>
> ⚠️ **dn1-4 a en revanche touché la NVS**, et il faut le savoir avant de dépanner :
> une valeur de `set bounce` trop grande, ou incompatible avec le build, peut
> mettre la carte en **boucle de panique avant le démarrage de la console** — plus
> aucune commande pour l'annuler. La sortie est d'effacer la seule partition NVS,
> sans toucher au reste :
>
> ```bash
> python3 -m esptool --chip esp32s3 --port /dev/ttyACM0 \
>     --before default_reset --after watchdog_reset erase_region 0x9000 0x6000
> ```
>
> 🔴 **CETTE COMMANDE ÉTAIT CASSÉE** (corrigée le 2026-08-16 par la revue de code
> dn1-4) : un `>` avait remplacé le `\` de continuation de ligne. Telle
> qu'écrite, bash **redirigeait la sortie vers un fichier nommé `--before`** et
> retirait l'argument de la ligne de commande — la NVS n'était pas effacée. Dans
> un bloc dont le seul objet est de sortir d'une boucle de panique, c'est le pire
> endroit possible pour une coquille.
>
> Elle rend les défauts du firmware au boot suivant, et l'asset survit (il vit à
> `0x410000`).
>
> ⚠️ **ELLE NE COUVRE QU'UN DES DEUX CHEMINS DE BRICK.** Effacer la NVS remet
> `bounce_px = 4800` et `draw_lines = 128`, qui sont désormais les **défauts du
> firmware** — ce qui est bon si la panique venait d'une valeur `set` fautive.
> Mais si elle vient d'un **`sdkconfig` périmé**, ça ne change rien : `sdkconfig`
> est gitignoré et ESP-IDF n'applique `sdkconfig.defaults` qu'aux symboles
> **absents**, donc un arbre d'avant dn1-4 garde `CONFIG_LCD_RGB_ISR_IRAM_SAFE=y`,
> que `bounce_px = 4800` transforme en *« Guru Meditation Error: Cache disabled
> but cached memory region accessed »* au boot. La sortie est alors :
>
> ```bash
> cd ~/projects/desknode/firmware/desknode
> rm sdkconfig && idf.py build && idf.py -p /dev/ttyACM0 flash
> ```
>
> ⚠️ **Le garde-fou qui manquait.** `set bounce 38400` — que l'aide de la commande
> présentait elle-même comme « le plafond, un diviseur utile » — ne démarrait plus
> depuis que `draw_lines` est passé à 128 : les deux clés mangent la même RAM
> interne et leurs bornes ne se parlaient pas. `set` vérifie désormais le **budget
> combiné** contre la RAM interne réellement libre, et refuse avant d'écrire.
>
> Sans lui, la partition est vierge (0xFF partout). Le firmware **le détecte et
> le dit** — au log (`partition « assets » VIERGE`) et **à l'écran** (panneau
> « ASSET ABSENT » sur la mire de cadrage) plutôt que d'afficher un écran blanc
> silencieux. Mais c'est une rustine : le bon geste est de flasher les 4.

**Redonner les offsets réels** si la table de partitions change — ne jamais les
retaper de mémoire :

```bash
cd ~/projects/desknode/firmware/desknode
idf.py partition-table          # imprime la table complète, offsets compris
```

`idf.py build` imprime de toute façon, en dernière ligne, la commande de flash
complète **avec tous les offsets** : c'est la source la plus fiable.

Pour **`firmware/hello-desknode`** (le témoin minimal) — trois fichiers, pas
d'asset, table de partitions par défaut :

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
$B  = '\\wsl.localhost\Ubuntu\home\nasbarok\projects\desknode\firmware\hello-desknode\build'
& $py -m esptool --chip esp32s3 -p COM3 -b 460800 --before default-reset --after hard-reset `
      write-flash --flash-mode dio --flash-size detect --flash-freq 80m `
      0x0     "$B\bootloader\bootloader.bin" `
      0x8000  "$B\partition_table\partition-table.bin" `
      0x10000 "$B\hello-desknode.bin"
```

⚠️ **`--flash-size detect` plutôt qu'une valeur en dur.** `--flash-size` réécrit l'en-tête du
bootloader **au moment du flash** : figer `2MB` ici annulerait en silence le correctif **apporté en
dn1-2** (la carte porte 16 MB, voir « **Écart 2 MB / 16 MB — SOLDÉ en dn1-2** » en fin de page).
`detect` lit la puce et suit.

Flash mesuré : **3,1 s**. Pour lire le log ensuite :

```powershell
& $py -m serial.tools.miniterm COM3 115200      # quitter : Ctrl+]
```

⚠️ **Trois pièges mesurés sur cette voie :**

1. **`@flash_args` est inutilisable ici, et pas pour la raison qu'on croit.** Le fichier
   `build/flash_args` généré par l'IDF contient `--flash_mode / --flash_freq / --flash_size` en
   **underscores** (syntaxe esptool 4.x) : l'esptool **5.3.1** de Windows les rejette. C'est *ça* qui
   impose de réécrire les arguments à la main ci-dessus. *(Séparément : `cmd.exe` refuse un
   répertoire courant UNC — « CMD ne prend pas les chemins UNC comme répertoires en cours » — mais
   **PowerShell l'accepte**, donc ce n'est pas le blocage. D'où les chemins UNC absolus, par
   commodité et non par contrainte.)*
2. **Exclusivité stricte** : tant que la carte est attachée à WSL, `COM3` **n'existe pas** côté
   Windows — et inversement. Il faut `detach` avant, `./tools/wsl-attach.sh` pour revenir.
3. **Un `--auto-attach` résident reprend la carte juste après le `detach`** : lancer
   `./tools/wsl-attach.sh --stop-auto` d'abord, sinon `COM3` n'apparaît jamais.

Ce que la voie A coûte au quotidien : la commande de flash est longue, le moniteur `miniterm` ne
**décode pas les backtraces** (adresses hexadécimales brutes, là où `idf.py monitor` les symbolise
via l'ELF), et les deux syntaxes esptool se ressemblent assez pour se confondre.

### Voies écartées — avec le symptôme relevé

| Voie | Verdict | Symptôme **observé** |
|---|---|---|
| **B** — `esp_rfc2217_server` sur Windows + `idf.py` sur WSL | ⛔ **flash impossible**, monitor OK | `A serial exception error occurred: Remote does not accept parameter change (RFC2217): dict_values([baudrate:REQUESTED, datasize:REQUESTED, parity:REQUESTED, stopsize:REQUESTED])` |

Détail de l'élimination de B, parce qu'une élimination sans preuve se retente :

- Le **transport marche** : pySerial nu (`serial_for_url(...)`) ouvre l'URL et lit le log de la carte
  (256 octets du firmware d'usine). Ce n'est donc **pas** un problème de réseau ni de pare-feu.
- Le **pare-feu Windows laisse passer** l'entrant depuis le sous-réseau WSL **sans élévation** —
  testé, `TCP_OK` sur le port 4000.
- Le changement de paramètres **après ouverture** marche aussi en pySerial nu (0,15 s). L'échec est
  donc propre à l'entrelacement reset + reconfiguration d'esptool, et **`--before usb-reset` ne le
  corrige pas**.
- Le serveur est **mono-client** et **ne se remet pas d'un client interrompu** : la connexion reste
  en `CloseWait` et tout client suivant reçoit `the port is busy or doesn't exist`. Il faut tuer et
  relancer le processus à chaque échec.
- Enfin, le client affiche `Device VID/PID identification is only supported on COM and absolute
  device paths` : à travers RFC2217, esptool **perd l'identification du chip** et ne peut pas
  choisir la bonne stratégie de reset.

⚠️ **Le serveur suggère lui-même une mauvaise adresse** (`rfc2217://10.14.0.2:4000`). L'hôte Windows
vu depuis WSL est la **passerelle par défaut**, à obtenir par `ip route | awk '/^default/{print $3}'`
→ **`192.168.224.1`**. Ce n'est **pas** le `nameserver` de `/etc/resolv.conf` (figé à `8.8.8.8` par
`generateResolvConf = false`), et il n'y a **pas** de `localhost` partagé (le mode *mirrored* exige
Windows 11 ; la tour est en Windows 10 19045).

### Faits matériels mesurés qui contredisent les recettes courantes

- **La carte est en USB natif ESP32-S3 Serial/JTAG (`303a:1001`), pas en pont CH343P.** Aucun
  périphérique `1A86` n'est présent. Aucun pilote à installer, ni côté Windows (`usbser` natif) ni
  côté Linux (`cdc-acm`). Le JTAG est disponible gratuitement sur l'interface `MI_02`.
- **Deux resets, deux comportements USB opposés — le fait le plus utile de cette page.**
  - *Reset logiciel* (fin de flash, « Hard resetting via RTS pin ») : **aucune ré-énumération**.
    Les 3 interfaces PnP restent `OK` de bout en bout et l'attachement `usbipd` **simple** survit à
    un flash complet. `--auto-attach` est **inutile** pour flasher.
  - *Reset de la puce* (**bouton RESET**, ou `esptool --after watchdog-reset`) : **ré-énumération
    complète**, mesurée à **1,4 s** côté Windows (les interfaces tombent, `COM3` disparaît, puis
    tout revient). Côté WSL, l'attachement `usbipd` **tombe**. C'est **là** que `--auto-attach`
    sert, et nulle part ailleurs.
- **Sortir du mode download demande le BON reset.** Une fois la carte passée en mode download
  (BOOT maintenu + RESET), `--after hard-reset` **ne la fait PAS repartir** : elle reste dans la ROM,
  le port série est totalement muet (0 octet), et même un `idf.py flash` complet n'y change rien —
  vérifié 3 fois. **`esptool.py --after watchdog_reset` la relance**, lui : l'application redémarre
  et le log reprend à `up 0 s`. Recette complète : § « La carte est muette ? ».
- **Ne transposer aucune recette de reset DTR/RTS type CH343/CP2102** : le reset passe par le
  mécanisme propre au USB-Serial/JTAG. Le log de boot le confirme : `rst:0x15 (USB_UART_CHIP_RESET)`.
- **Le mode download ne change PAS le VID:PID** : toujours `303A:1001` avec ses 3 interfaces, et
  `COM3` revient au même endroit. On ne peut donc **pas** détecter le mode download en regardant
  l'identité USB. Ce qui le trahit : le port devient muet, et `esptool.py --before no_reset` réussit
  à dialoguer **sans reset préalable** (ce qui n'arrive que dans le bootloader ou le stub).
- **Le log part sur DEUX chemins à la fois** : la console UART0 (`GPIO43`/`GPIO44`, le header) **et**
  l'USB-Serial/JTAG, via la console secondaire activée par défaut. Le header UART est donc une voie
  de secours réellement vivante si l'USB pose problème.
- `/dev/ttyACM*` arrive en **`root:root crw-------`** et l'utilisateur n'est pas dans `dialout` :
  sans `chown`/`chmod`, esptool sort `[Errno 13] Permission denied`.

### Écart 2 MB / 16 MB — **SOLDÉ en dn1-2**

Le bootloader annonçait `SPI Flash Size : 2MB` sur une carte qui en porte **16**. C'était la valeur
par défaut de l'IDF, non ajustée, et elle est corrigée dans `firmware/desknode` :
`CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y`. Relevé verbatim au bandeau de boot :

```
I (25) boot.esp32s3: SPI Flash Size : 16MB
```

`firmware/hello-desknode` reste **délibérément** sur le défaut 2 MB : c'est le témoin minimal, sa
configuration est figée.

⚠️ **Le piège reste entier, et il vaut pour TOUTE modification de config** : `sdkconfig.defaults`
n'est lu que pour **produire** `sdkconfig`. Un `sdkconfig` déjà présent (gitignoré, donc invisible à
`git status`) **l'emporte** en silence. Règle du dépôt : **tout changement de `sdkconfig.defaults`
se valide par `rm sdkconfig && idf.py build`, puis par la LECTURE du bandeau de boot** — jamais par
la relecture du fichier source.

### La configuration d'affichage — où elle vit

Le brochage vérifié, les timings, la configuration framebuffer retenue et tous les chiffres datés
sont dans **[`hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md`](hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md)**.
C'est **ce fichier** qui fait autorité — plus jamais besoin d'aller chercher un brochage dans un
wiki constructeur ou un dépôt communautaire. Sa **§0** donne la configuration de référence en un
tableau : c'est la seule chose à lire si on ne lit qu'une chose.

**Deux branches d'essai vivent à côté du `sdkconfig.defaults` livré**, chacune avec son mode
d'emploi en tête de fichier — elles sont versionnées pour que les mesures soient **rejouables**,
pas pour être activées par défaut :

| Fichier | Ce qu'il éprouve | Verdict |
|---|---|---|
| `sdkconfig.defaults.ac5-double-tampon` | `RESTART_IN_VSYNC=n`, sans quoi le recalage DMA est **inerte** et toute conclusion serait une non-mesure | ✅ le double tampon **fonctionne** (§4 ter) — mais n'apporte rien de mesuré aujourd'hui |
| `sdkconfig.defaults.xip-lecture-code` | XIP pour les **lectures** de code, le cas que la réfutation de dn1-2 excluait de son périmètre | ❌ réfuté ici aussi (§10.5, ligne 6) |

### L'asset Living PCB — ce qui est versionné, ce qui ne l'est pas

Règle tranchée en dn1-2 :

| Fichier | Versionné ? | Pourquoi |
|---|---|---|
| `tools/gen_living_pcb.py` | **oui** | c'est la SOURCE ; bibliothèque standard seulement, aucune dépendance à installer |
| `assets/mockups/living-pcb-v0.png` | **oui** | prévisualisation, pour voir l'asset **sans carte** |
| `build/living_pcb_v0.bin` | **non** | 614 400 o **générés** par le build, à graine égale identiques au bit près |

Un clone neuf n'a rien à faire : `idf.py build` régénère le `.bin`, `idf.py flash` l'écrit dans la
partition `assets`. Pour le regarder sans construire :

```bash
python3 tools/gen_living_pcb.py --out-png /tmp/apercu.png
```

## Les polices (dn3-1) — générées, vérifiées, VERSIONNÉES

Les libellés du dashboard perdaient leur accent **en silence** : les built-ins
`lv_font_montserrat_14/_28` sont générées avec `-r 0x20-0x7F,0xB0,0x2022` (relu dans l'en-tête de
leur `.c`), soit ASCII + le signe degré + la puce, **et rien d'autre**. LVGL ne dessine pas un
glyphe absent **et ne se plaint pas** — « RÉSEAU », « HUMIDITÉ », « AOÛT » y perdaient leur lettre.

`main/fonts/dn_font_14.c` et `dn_font_28.c` les remplacent : **ASCII + latin-1 complet + la puce +
les 60 `LV_SYMBOL_*` uniques + 10 icônes FontAwesome** — dont **2 sont déjà des symboles** (`cog`
0xF013, `tint` 0xF043), soit **8 codepoints neufs** et **68 au `-r` FontAwesome final**. Ce sont des
**sur-ensembles stricts** des built-ins.
⚠️ **« 61 » est le nombre d'entrées BRUTES de la liste amont** : elle contient un **doublon** (61452
deux fois), d'où **60** uniques. Ces nombres sont désormais **calculés** par le générateur et
réinjectés dans `dn_font.h` — cinq endroits du dépôt en annonçaient **trois valeurs différentes,
aucune juste** (revue de code du 2026-08-18).

### Régénérer

```bash
# lv_font_conv est appelé PAR SON NOM par le générateur amont de LVGL.
# npx le fournit sans installation globale — il suffit d'un shim sur le PATH :
printf '#!/usr/bin/env bash\nexec npx --yes lv_font_conv@1.5.3 "$@"\n' > ~/.local/bin/lv_font_conv
chmod +x ~/.local/bin/lv_font_conv

python3 tools/gen_font_dn.py            # régénère les 2 .c + dn_font.h
python3 tools/gen_font_dn.py --mesure   # compare les plages et le kerning, ne génère rien
```

- **Mesuré depuis ce WSL le 2026-08-17** : `node v24.14.0`, `npm 11.9.0`,
  `npx --yes lv_font_conv --version` → **1.5.3** (rc=0).
- Le générateur **lit** les codepoints de symboles dans
  `managed_components/lvgl__lvgl/scripts/built_in_font/built_in_font_gen.py` — il ne les recopie
  **jamais**. Une liste recopiée dérive, et sa dérive est **silencieuse** : `LV_SYMBOL_LIST` (bandeau
  MENU) et `LV_SYMBOL_LEFT` (chevron de retour) disparaîtraient sans un mot.
- Il **relit** ensuite le `.c` produit et **échoue bruyamment** si un symbole, une icône ou un témoin
  accentué manque. Une génération qui « réussit » sans ses glyphes est l'étiquette qui ment.
  🔴 **Et cette garde a été aveugle une fois** (corrigée le 2026-08-18, revue de code) : elle testait
  les **bornes** des cmaps au lieu de leur **contenu**, or la cmap qui porte les symboles est de type
  **SPARSE** — elle borne `8226 → 63650` en n'y portant que **69** codepoints. Tout `syms` passait
  donc quoi qu'il arrive, **`fan` (0xF863) compris** — le glyphe absent que ce README documente.
  `codepoints_du_c()` décode maintenant `unicode_list_N` (offsets depuis `range_start`). **Contrôlé
  après correctif** : `fan` → absent, `Ā` (hors latin-1) → absent, les 68 + les témoins → présents,
  **260 codepoints réellement portés** par police.
- ⚠️ **Deux témoins ne viennent PAS de l'amont, et c'est délibéré** : `LV_SYMBOL_LIST` (U+F00B) et
  `LV_SYMBOL_LEFT` (U+F053) sont écrits **en dur** dans `SYMBOLES_TEMOINS`. Un témoin tiré de la
  chose qu'il témoigne n'est pas un témoin — sans eux, un retrait amont serait retiré de la police
  **et** de la liste de contrôle, et le script annoncerait un succès.
- `--mesure` **vérifie aussi** chaque police qu'il chiffre (correctif du 2026-08-18 : il ne
  vérifiait rien, alors que c'est lui qui a produit le tableau ayant tranché **W5**).
- `dn_font.h` (les macros `DN_ICONE_*`) est **généré depuis le même dictionnaire** que la police :
  une macro **ne peut pas** pointer un codepoint que la police n'aurait pas.
- ⚠️ `managed_components/` est **gitignoré mais régénéré** par `idf.py` depuis `main/idf_component.yml`,
  où `lvgl/lvgl: "==9.5.0"` est épinglé. Sans lui, ni générateur, ni TTF, ni WOFF :
  `idf.py reconfigure` d'abord.
- ⚠️ **`--no-compress` est obligatoire** : `CONFIG_LV_USE_FONT_COMPRESSED` n'est **pas** activé dans
  ce build, et la compression coûte de toute façon ~30 % de temps de rendu.

### Pourquoi les `.c` sont VERSIONNÉS et non produits au build

`lv_font_conv` est une dépendance **npm**, absente du tableau des versions figées : un `idf.py build`
sur un clone neuf **sans réseau** échouerait. Ce n'est **pas** le même arbitrage que l'asset Living
PCB, dont le générateur (`gen_living_pcb.py`) est en **stdlib Python pure** — celui-là peut se
regénérer partout, hors ligne.

### Ce que ça coûte, mesuré

Binaire **832 720 → 885 232 o** (+52 512, +6,3 %), partition `factory` libre à **79 %**.
Détail, tableau des plages et les **deux erreurs de la story corrigées par la mesure** :
`hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md` **§15.3**.

### Les icônes, et celle qui manque

🔴 **`0xF863` (`fan`) est ABSENT** du `FontAwesome5-Solid+Brands+Regular.woff` du dépôt : il est
arrivé en **FontAwesome 5.11** et le fichier embarqué est antérieur. **Vérifié en le convertissant
seul**, pas déduit d'une table. Quatre substituts sont embarqués **ensemble** et commutables à chaud
(`widget icone`) ; **`cog` a été retenu** par constat owner — et il est **gratuit**, `0xF013` étant
déjà l'un des 60 symboles injectés par le générateur amont.
⚠️ **`main/fonts/dn_font.h` annonçait `sync-alt` jusqu'au 2026-08-18**, alors que `k_desc[]` pose
`DN_ICONE_COG`. Le `.h` étant **généré**, la phrase revenait à chaque régénération : le correctif est
dans `tools/gen_font_dn.py` (`ENTETE_MODELE`), pas dans le `.h`.

⛔ **Aucun asset image pour les icônes** : `dn_asset` ne gère qu'**un** asset, et la partition
`assets` n'a que ~434 Ko libres — que **dn3-3 réclame déjà**.

**Licences**, **lues** dans les fichiers, pas récitées
(`managed_components/lvgl__lvgl/scripts/built_in_font/font_license/`) :
- `Montserrat/OFL.txt` — *« This Font Software is licensed under the SIL Open Font License,
  Version 1.1 »*, © 2011 The Montserrat Project Authors.
- `FontAwesome5/LICENSE.txt` — Font Awesome Free, © Fonticons Inc. : **icônes CC BY 4.0**,
  **fontes SIL OFL 1.1**, code MIT. Nous n'embarquons que des **glyphes** ⇒ CC BY 4.0 + OFL 1.1.

⚠️ Ces licences vivent dans `managed_components/`, qui est **gitignoré**. Elles sont donc
**absentes d'un clone** tant que `idf.py reconfigure` n'a pas tourné — c'est un fait à connaître
avant toute distribution du binaire, pas un détail d'attribution.

## L'agent PC (dn2-2 → dn4-1) — CINQ métriques de la tour, à ~1 Hz, par l'USB série

Un seul fichier : `agent/dn_agent.py`. Il tourne sur le **Python Windows 3.13** de la
tour, **sans élévation, sans driver, sans .NET**.
⛔ **Et c'est une FRONTIÈRE, pas une préférence (D8)** : le Ring0 / LibreHardwareMonitor —
donc la **température CPU** et les **RPM ventilateurs** — sort du périmètre V1. C'est ce qui
a fait de la 6ᵉ case un **DISQUE** et de la 2ᵉ grandeur du CPU une **fréquence**.

### Les cinq métriques et leurs sources (dn4-1, mesurées le 2026-08-18)

| case | grandeur 0 | grandeur 1 | source | droits | coût mesuré |
|---|---|---|---|---|---|
| **CPU** | % | **GHz** | `psutil.cpu_percent` + `cpu_freq` | aucun | ~0 ms/tir |
| **GPU** | % | **°C** | **`atiadlxx.dll` / `ADL2_New_QueryPMLogData_Get`** (ctypes) | aucun | **0,5 ms/tir** |
| **RAM** | % *(+ jauge)* | Go **totaux** | `psutil.virtual_memory` | aucun | 7,8 ms/tir |
| **RÉSEAU** | Mb/s ↓ | Mb/s ↑ | `psutil.net_io_counters` (**deltas**) | aucun | 6,8 ms/tir |
| **DISQUE** | **Mo/s** | — | `psutil.disk_io_counters` (**deltas**) | aucun | ~0 ms/tir |

🔴 **NVML est INAPPLICABLE sur cette tour** : `Win32_VideoController` rend **un seul**
contrôleur, une **AMD Radeon RX 6800 XT**, et `pynvml` n'est pas installé. Le repli
pré-autorisé (« GPU en % seul ») **n'a pas servi** : ADL rend le % **et** la °C en un appel.
⛔ **Le candidat WMI `GPUEngine` a été ÉCARTÉ PAR LA MESURE** : 720 instances, **342 ms de CPU
par tir** (30,8 % d'un cœur) — **657× plus cher qu'ADL**, au-dessus du critère « < 1 % » du
brief à lui seul, et incapable de tenir 1 Hz.
⚠️ **Le mapping des capteurs PMLog se VÉRIFIE, il ne se croit pas** : l'agent exige que les
mêmes indices rendent une **largeur de lien PCIe légale** et une **horloge mémoire plausible**,
et **refuse de servir** sinon — le témoin est rejoué **à chaque tir**, pas seulement à
l'ouverture. Un mapping décalé publierait une tension comme une température.
🔴 **CE QUE CE TÉMOIN NE PROUVE PAS** (corrigé en revue le 2026-08-18 — ce paragraphe, la
docstring de l'agent et `liaison-pc.md` §13.5 annonçaient tous trois « exige `BUS_LANES = 16`
et `CLK_MEMCLK ≈ 2000 MHz` », ce que le code n'a jamais fait **et a raison de ne pas faire** :
une RX 6000 **abaisserait son lien PCIe au repos** — ⚠️ **HYPOTHÈSE NON MESURÉE**, et la séance
du 2026-08-18 ne la confirme pas : le témoin a lu **`BUS_LANES = 16` · `CLK_MEMCLK = 1988 MHz`**,
soit exactement ce que les quatre textes annonçaient. ⇒ **Ce qui est acquis** : le code vérifie une
plage, et les textes doivent dire ce que le code fait. ⇒ **Ce qui reste ouvert** : faut-il resserrer ?
Il faudrait relever `BUS_LANES` **au repos prolongé**, ce qui n'a pas été fait). C'est une **cohérence de plage**, pas la preuve du bon capteur.
✅ **Ce qui a prouvé le capteur, c'est AC10** : **47 °C à l'écran contre 47 °C au Gestionnaire
des tâches**, lus **en même temps**. Deux instruments, un seul répond à la question.
⚠️ **`ram` porte le TOTAL, pas l'utilisé** : le firmware compose « 22,7 / 34,2 Go » depuis le
pourcentage. Deux nombres échantillonnés séparément finiraient par afficher **deux vérités
contradictoires dans le même rectangle**.
⛔ **`errin`/`errout`/`dropin`/`dropout` ne sont JAMAIS publiés** : cette tour rend
`dropin = 113 558 935 299 979`. On regarde un compteur avant de le publier.

- **Sources : `psutil` + `ctypes`/`atiadlxx.dll`** — ⚠️ **dn4-1 n'ajoute AUCUNE dépendance** : le GPU passe par `ctypes` (stdlib) et une DLL installée par le pilote AMD. Détail du % CPU ⤵
- **Source du % CPU : `psutil`** (`pip install --user psutil` — la SEULE dépendance
  posée par dn2-2 ; `pyserial` et `websockets` étaient déjà là). Ce sont les mêmes
  compteurs noyau que le Gestionnaire des tâches. Raisons chiffrées de l'élimination
  de `Get-Counter` (noms localisés FR) et de WMI (spawn 4,2 s) : en-tête de l'agent.
- **Lancement** (PowerShell, la carte étant **détachée** de WSL — voir plus bas) :

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
& $py \\wsl.localhost\Ubuntu\home\nasbarok\projects\desknode\agent\dn_agent.py --serie COM3
#  --temoin     imprime son propre coût CPU toutes les 10 s
#  --duree 60   s'arrête proprement après 60 s (le témoin « arrêt propre » d'AC7)
#  --stdout     trames à l'écran, sans carte (débogage)
#  --ws URL     branche B (WiFi WebSocket) — ÉCARTÉE par la fourche, gardée pour une
#               re-mesure ; sans firmware branche B en face, elle ne sert à rien
```

- ⚠️ **CES DEUX CHIFFRES NE SONT PAS CEUX DE L'AGENT LIVRÉ** (annotation de revue
  2026-08-19). La séance post-revue mesure l'agent tel qu'il est livré à
  **2,421 % d'un cœur = 0,1513 % machine** (`hardware/…-affichage.md` §17.9), soit
  **+0,26 pt NON EXPLIQUÉ** par rapport aux 2,161 % ci-dessous. L'écart est au
  ledger. ⛔ Les chiffres ci-dessous restent lisibles — ils datent leur firmware —
  mais **ne pas les citer comme le coût de l'agent courant**.
- 🔴 **Coût propre, dn4-1, SUR LE TRANSPORT RÉELLEMENT UTILISÉ (`COM3`, série) :
  2,161 % d'un cœur = 0,135 % machine** — mesuré en séance carte le 2026-08-18,
  agent réel sur le port, **3 000 trames à 5,00/s, 0 erreur · 0 recalage · 0 écrêtage**.
  🔴 **+0,63 pt contre `--stdout` : LE PORT SÉRIE A UN COÛT PROPRE, et il n'existait
  dans AUCUN budget.** ⛔ Ne pas comparer un chiffre `--stdout` à un chiffre `COM3`.
- **Coût propre, dn4-1, sur `--stdout` (témoin, PAS le transport) : 1,528 % d'un cœur
  = 0,0955 % machine** —
  **2,750 s CPU / 180,0 s** de temps mural, 900 trames, **0 écrêtage, 0 recalage**.
  L'augmentation est **attribuée** : 7,8 ms (`virtual_memory`) + 6,8 ms (`net_io_counters`)
  + 0,5 ms (ADL) ≈ **15,1 ms/s = 1,51 % d'un cœur**, soit 1,51 des 1,528 points expliqués.
  🔴 **Ce n'est PAS le GPU qui coûte** — c'est le poste que le cadrage soupçonnait, et il pèse
  **3 %** du total. 🔴 **QUELLE LECTURE DE « < 1 % » ? LA QUESTION EST OUVERTE, ET ELLE
  EST AU LEDGER** (décision owner du 2026-08-18, revue de code) : sur le transport
  retenu, **0,135 % machine** ✅ contre **2,161 % d'un cœur** ❌. ⛔ **Le critère n°4
  du brief n'est donc PAS coché** — ni infirmé. Les deux lectures sont publiées,
  comme dn2-2 le faisait déjà ; ce qui manque, c'est **l'unité que le brief vise**,
  et c'est à écrire dans le brief. ⚠️ D3 affirme que ce critère « se coche ici » :
  tant que l'unité n'est pas énoncée, cette affirmation est sans objet.
- **Coût propre en dn2-2 (1 métrique) : 0,35 % d'un cœur** (0,022 % machine) — 0,141 s CPU pour
  40 s de temps mural, 16 cœurs logiques. ⚠️ **La méthode fait partie du chiffre** : c'est
  le **cumul** `psutil.Process().cpu_times()` rapporté au temps mural, **pas** une fenêtre
  glissante `cpu_percent()` — une fenêtre de 10 s a une résolution de ~0,16 pt (ticks de
  15,6 ms) et ne PEUT PAS voir un coût de cet ordre. Le cumul, lui, affine avec la durée
  (le démarrage domine, la tendance est décroissante). Critère brief « < 1 % » :
  largement dedans, **première mesure**, soldée en dn4-1. *(Ce README et le tracker
  annonçaient 0,23 % sans méthode ni source — corrigé par la revue du 2026-08-16 :
  c'est le chiffre dont la méthode est écrite qui fait foi.)*
- **Le bilan de fin sort dans TOUS les cas, Ctrl+C compris** : trames émises, erreurs
  d'envoi, **recalages de cadence**, bruit d'écho console, et les **refus signalés par le
  firmware** — « n trames émises » ne prouve que n écritures, pas n acceptations.

- **Protocole** : `$DN,2,<seq>,<t_ms>,<metrique>,<v1>[,<v2>]*<CK>` — ⛔ **l'autorité est `main/dn_link.h`**, ce README renvoie et ne redéfinit pas. **v1 reste acceptée** (`$DN,1,…,cpu,…`, 6 champs), et l'agent de dn2-2 **non modifié** fait toujours vivre la case CPU : c'est le témoin de non-régression, et il passe **8/8 avec `rejets_version` = 0**. Envoyé en `pc $DN,…` au
  REPL — l'agent parle le dialecte de la console. Autorité : `dn_link.h` et
  `hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md` §12.5.
- **Case CPU du dashboard** : vivante quand la liaison l'est ; **« -- » grisé** dès
  3 s sans trame valide (une valeur figée serait un mensonge d'interface) ; reprise
  sans reboot en ≤ 2 s quand l'agent revient.

### ⚠️ Le port est EXCLUSIF : agent ⇄ boucle de flash, le geste (branche A)

L'agent (Windows, COM3) et la boucle WSL (flash + `dn_console.py`) ne coexistent
JAMAIS — exclusivité usbipd + TIOCEXCL, mesurée. L'alternance :

🔴 **ÉTAPE 0 — TUER LES VEILLEURS `--auto-attach`, AVANT TOUT LE RESTE.** Sinon ils
re-attachent la carte à WSL en quelques secondes après le detach, et l'agent trouve un
COM3 fantôme (`FileNotFoundError`) pendant que l'état usbipd se bloque en « Attached »
orphelin. *(Ce piège a coûté une heure en session dn2-2 ; l'avertissement était écrit
APRÈS le bloc de commandes, soit dans l'ordre inverse de l'exécution — corrigé par la
revue du 2026-08-16.)*
`ps aux | grep usbip-auto-attach` (WSL) et, côté Windows,
`Get-CimInstance Win32_Process -Filter "Name='usbipd.exe'"` → `Stop-Process` sur
ceux dont la ligne de commande contient `auto-attach`.

```bash
# 1) WSL → Windows (rendre COM3 à l'agent) — 0,3 s :
powershell.exe -Command "& 'C:\Program Files\usbipd-win\usbipd.exe' detach --busid 3-1"
# 2) VÉRIFIER que le detach a TENU (les veilleurs ressuscitent en ~2 s) :
powershell.exe -Command "& 'C:\Program Files\usbipd-win\usbipd.exe' list"
#    → la ligne 3-1 doit afficher STATE = « Shared », PAS « Attached ».
#      Si elle est « Attached », un veilleur a survécu : retour à l'étape 0.
# 3) Windows → WSL (reflasher / mesurer) — ~3,1 s :
cd ~/projects/desknode && ./tools/wsl-attach.sh
```

🔴 **DTR/RTS : la parade est WINDOWS-ONLY, et sous Linux elle NUIT.** Sous Windows,
pyserial pose DTR/RTS à l'ouverture et la séquence **RESET la carte** (dn2-2, trois
sessions perdues avant le diagnostic) ⇒ `dn_agent.py` force `dtr=False, rts=False`
AVANT `open()` — **mais uniquement si `sys.platform == "win32"`**.
⚠️ **Sous Linux, poser ces lignes PROVOQUE le reset qu'elles prétendent empêcher** :
A/B à une variable sur `/dev/ttyACM0` (2026-08-16) — **avec** la parade, 6 664 o reçus
et `rst:0x15 (USB_UART_CHIP_RESET)` ; **sans**, 38 o et aucun reboot. Témoin négatif :
`dn_console.py` n'y touche jamais et n'a pas reset la carte de vingt invocations.
⇒ **Tout outil série côté WSL ne doit PAS toucher DTR/RTS.** Côté tour, si.

## Matériel

| Module | Rôle | I²C |
|---|---|---|
| ESP32-S3-Touch-LCD-2.8B | carte + écran + tactile (16 MB flash / 8 MB PSRAM, IMU QMI8658, RTC PCF85063, buzzer) | ext. : SCL=GPIO7, SDA=GPIO15 |
| BME680 | température, humidité (pression et VOC non affichés — brief : 6 widgets) | ✅ **`0x77` MESURÉ** · chip id `0x61`, variant `0x00` |
| BH1750 | luminosité ambiante | 0x23 — ⚠️ adresse ATTENDUE ; **ni inventorié ni branché** (dn4-1) |
| VL53L0X | proximité / présence | 0x29 — ⚠️ adresse ATTENDUE ; **ni inventorié ni branché** (dn4-1) |
| INA219 | tension / courant / puissance | 0x40 — ⚠️ adresse ATTENDUE ; **ni inventorié ni branché** (dn4-1) |

**Occupants du bus MESURÉS le 2026-08-16** (scan stable `5/5`, ~20 passes) : `0x20` TCA9554 ·
**`0x51` PCF85063 — la RTC est vivante, première confirmation** · `0x5D` GT911 ·
**`0x6B` QMI8658 — et c'est `0x6B`, pas `0x6A`**.

🔴 **Le connecteur I²C externe est une EMBASE JST, sérigraphiée `GND · 3V3 · SDA · SCL`.** Le
miroir Spotpear du wiki Waveshare annonçait `GND · 3V3 · SCL · SDA` sur un « header 2,54 mm » :
**deux erreurs dans la même ligne**. ⚠️ Une **seconde embase JST identique** juste à côté porte
l'UART (`GND · 3V3 · TXD · RXD`) — se tromper d'embase alimente correctement le composant et le
laisse muet. Détail et symptômes : `hardware/…-capteurs-i2c.md` §13.1.

### Procédure de câblage du BME680 — et les photos qui en font foi

Les photos vivent dans **`docs/cablage/`**, nommées par leur **horodatage EXIF**. Elles sont
décrites une par une en **`hardware/…-capteurs-i2c.md` §13.0**, avec ce qu'elles prouvent **et ce
qu'elles ne prouvent pas** — c'est le critère n°5 du brief (« câblage photographié »).

Le montage, dans l'ordre où il a été fait :

1. 🔴 **Carte DÉBRANCHÉE de l'USB.** Aucun fil ne se pose sur un bus vivant.
2. **Identifier la BONNE embase** des deux jumelles : la sérigraphie fait foi (`SDA · SCL` et non
   `TXD · RXD`), et `docs/cablage/2026-08-16_2228-…` la photographie.
   ⚠️ **Le wiki ne fait PAS foi** — il a été réfuté sur cette ligne même.
3. **Souder la barrette 6 broches** sur le breakout : elle est **fournie NON montée**, et les
   broches simplement posées dans leurs trous **ne conduisent pas** — c'est ce qui a coûté la
   moitié de la séance du 2026-08-16 (§13.5, hypothèse 6). ⛔ Rien à souder côté carte.
4. **Poser les 4 fils un par un** : `GND↔GND`, `3V3↔VCC`, `SCL(GPIO7)↔SCL`, `SDA(GPIO15)↔SDA`.
   ⚠️ **L'ordre du câble JST et celui du breakout sont EN MIROIR sur les deux premières broches** :
   suivre « l'ordre » inverse l'alimentation ET croise les signaux.
5. **Contrôle de continuité au multimètre** (mode bip), fil par fil — c'est ce qui attrape un
   Dupont mal enfoncé, qu'aucun coup d'œil ne voit.
6. **Placer le breakout ÉCARTÉ de la carte**, sur ses fils : collé à la dalle, il mesure la carte
   et non la pièce (§10.2 de la story).
7. **Rebrancher l'USB**, relire le bandeau de boot en entier, puis `i2c` : `0x77` doit sortir
   **`5/5`**, et `i2c lire 77 D0` rendre `61`. ⚠️ **C'est la lecture de registre qui QUALIFIE**, pas
   le scan — il produit des faux positifs ET des faux négatifs (§13.6 bis).

⚠️ **Un front descendant sur `CSB` bascule la puce en SPI jusqu'à la coupure d'alimentation
suivante.** Manipuler les fils sous tension ré-arme donc la panne qu'on vient de purger : la
séquence *bouger → scanner* **ne peut pas converger**, seule *bouger → couper l'alim → rescanner*
le peut. ⛔ Et `reboot` en console **ne coupe PAS le capteur** : `esp_restart()` laisse le rail
3V3 debout. 🔴 Débrancher `VCC` non plus — voir l'alimentation fantôme par les diodes ESD, §13.10.

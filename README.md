# DeskNode

Mini-display tactile 2,8" (Waveshare **ESP32-S3-Touch-LCD-2.8B**, 480×640 IPS portrait) monté sur
la façade de la tour PC (NZXT Phantom 630). Affiche en continu 6 métriques — CPU, GPU, RAM,
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
hardware/   ESP32-S3-Touch-LCD-2.8B-affichage.md  <- LA config d'affichage de
            référence (brochage VÉRIFIÉ, timings, framebuffer, chiffres datés).
            L'inventaire des breakouts et le câblage viennent en dn2-1.
assets/     assets graphiques 480×640
  mockups/living-pcb-v0.png   prévisualisation COMMITÉE de l'asset généré
agent/      DeskNode PC Agent (Windows)
tools/      wsl-attach.sh (attachement USB WSL)
            gen_living_pcb.py (génération de l'asset 480×640)
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
- à l'**œil** : l'**asset Living PCB** s'affiche plein écran, et le **rétroéclairage est ALLUMÉ
  FIXE**. ⚠️ **Il ne clignote plus** — le clignotement était le signe de vie de P0 ;
- la **console est interactive** : taper `aide` dans le moniteur liste les commandes. Jeu complet :
  `scene`, `fps`, `bw`, `mem`, `cpu`, `cfg`, `set`, `tear`, `flash`, `disp`, `bl`, `dma`, `reboot`,
  `aide`. Une **forme de remise à zéro de la configuration** vers les défauts est en cours d'ajout
  à la famille `set` — `aide` en donne la syntaxe exacte, qui fait foi sur cette liste.
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
> Le critère qui marche dans les deux cas reste **0 octet sur le port**.

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
wiki constructeur ou un dépôt communautaire.

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

## Matériel

| Module | Rôle | I²C |
|---|---|---|
| ESP32-S3-Touch-LCD-2.8B | carte + écran + tactile (16 MB flash / 8 MB PSRAM, IMU QMI8658, RTC PCF85063, buzzer) | ext. : SCL=GPIO7, SDA=GPIO15 |
| BME680 | température, humidité, pression, VOC | 0x76/0x77 |
| BH1750 | luminosité ambiante | 0x23 |
| VL53L0X | proximité / présence | 0x29 |
| INA219 | tension / courant / puissance | 0x40 |

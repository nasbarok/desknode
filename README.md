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
firmware/   firmware ESP32-S3 — ESP-IDF v5.5.5 (tranché en P0/dn1-1)
hardware/   inventaire des breakouts, brochages, schéma V1
assets/     assets graphiques 480×640 (Living PCB, icônes, mockups)
agent/      DeskNode PC Agent (Windows)
tools/      outillage poste de dev (attachement USB WSL)
tests/      harnais et smokes
```

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

Côté Windows, dans **PowerShell normal** (pas admin) :

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m pip install --user esptool
```

Côté Windows, dans **PowerShell ÉLEVÉE** (uniquement pour la voie C) :

```powershell
winget install --id dorssel.usbipd-win --exact
usbipd list                       # relever le BUSID de la ligne 303a:1001 — ici : 3-1
usbipd bind --busid 3-1           # une fois pour toutes ; l'état passe à "Shared"
```

> Le `bind` est **persistant** : il ne se rejoue pas après un reboot. Seul l'`attach` se rejoue.

### La boucle de travail (voie C — retenue)

Dans **chaque shell WSL neuf** :

```bash
. $HOME/esp/esp-idf/export.sh                      # prépare l'environnement ESP-IDF
cd ~/projects/desknode && ./tools/wsl-attach.sh    # rend la carte visible : /dev/ttyACM0
cd firmware/hello-desknode
idf.py -p /dev/ttyACM0 flash monitor               # quitter le moniteur : Ctrl+]
```

- **Baud du moniteur : 115200** · **baud du flash : 460800** (valeurs par défaut de l'IDF, mesurées
  comme fonctionnelles).
- Durées mesurées : build **à froid 36 s**, **à chaud 1 s**, reconstruction vierge **54 s**,
  **flash 6 s**.
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

⚠️ **Ce sont deux resets différents, et c'est le piège de cette carte.** Le reset *logiciel* que
joue esptool en fin de flash (« Hard resetting via RTS pin ») **ne réinitialise pas** le périphérique
USB-Serial/JTAG : rien ne bouge côté hôte. Le reset *de la puce* (bouton, ou watchdog) coupe tout :
`usbipd list` repasse de `Attached` à `Shared`, `dmesg` affiche `usb 1-1: USB disconnect`, et
`/dev/ttyACM0` devient un nœud mort (`[Errno 19] No such device`).

**Parade si les resets sont fréquents** : `./tools/wsl-attach.sh --auto`. Mesuré : le périphérique
revient **tout seul en ~6 s**. ⚠️ Mais `--auto-attach` ne restaure **que le périphérique** — les
droits retombent à `root:root crw-------`, donc il faut rejouer le script (ou le `chmod`) pour
pouvoir relire le port.

⚠️ `sudo modprobe` et `sudo chmod` sont à rejouer **explicitement** : sur cette machine **systemd est
offline**, donc `/etc/modules-load.d/` et les règles `udev` sont **inopérants** — une règle
`/etc/udev/rules.d/*.rules` ne se déclencherait jamais. `tools/wsl-attach.sh` encapsule exactement
ces gestes, c'est sa seule raison d'être.

### La carte est muette ? (le port s'ouvre mais rien n'en sort)

Symptôme : `/dev/ttyACM0` existe, s'ouvre sans erreur, et ne rend **0 octet** — aucun `DeskNode P0 —
up N s`. Ce n'est pas un problème de câble ni de baud : la carte est très probablement restée en
**mode download**, où l'application ne tourne pas.

```bash
# 1. Confirmer : si esptool dialogue SANS reset, la carte est dans le bootloader ROM.
esptool --chip esp32s3 -p /dev/ttyACM0 --before no-reset --after no-reset flash-id

# 2. La relancer. ⚠️ `--after hard-reset` NE SUFFIT PAS ici — il faut le watchdog.
esptool --chip esp32s3 -p /dev/ttyACM0 --after watchdog-reset flash-id

# 3. Ce reset ré-énumère l'USB : l'attachement usbipd est tombé, il faut le refaire.
cd ~/projects/desknode && ./tools/wsl-attach.sh
```

### Voie A — build WSL, flash depuis Windows (secours, et cap à terme)

Elle n'installe **rien** sur le système et ne dépend ni de WSL-USB ni du réseau. C'est aussi la
direction visée à terme (fonctionner sans WSL).

```bash
# 1. Dans WSL : construire seulement
. $HOME/esp/esp-idf/export.sh
cd ~/projects/desknode/firmware/hello-desknode && idf.py build
```

```powershell
# 2. Dans WSL, rendre la carte à Windows (sinon COM3 n'existe pas côté Windows)
#    -> depuis WSL :  powershell.exe -c "& 'C:\Program Files\usbipd-win\usbipd.exe' detach --busid 3-1"

# 3. Dans PowerShell : flasher. Le port est COM3 (le relever avec la commande ci-dessous).
[System.IO.Ports.SerialPort]::getportnames()

$py = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
$B  = '\\wsl.localhost\Ubuntu\home\nasbarok\projects\desknode\firmware\hello-desknode\build'
& $py -m esptool --chip esp32s3 -p COM3 -b 460800 --before default-reset --after hard-reset `
      write-flash --flash-mode dio --flash-size 2MB --flash-freq 80m `
      0x0     "$B\bootloader\bootloader.bin" `
      0x8000  "$B\partition_table\partition-table.bin" `
      0x10000 "$B\hello-desknode.bin"
```

Flash mesuré : **3,1 s**. Pour lire le log ensuite :

```powershell
& $py -m serial.tools.miniterm COM3 115200      # quitter : Ctrl+]
```

⚠️ **Deux pièges mesurés sur cette voie :**

1. **`cmd.exe` refuse un répertoire courant UNC** (« CMD ne prend pas les chemins UNC comme
   répertoires en cours ») — PowerShell, lui, l'accepte. D'où les **chemins UNC absolus** ci-dessus
   plutôt qu'un `cd` dans `build/` suivi de `@flash_args`.
2. **Exclusivité stricte** : tant que la carte est attachée à WSL, `COM3` **n'existe pas** côté
   Windows — et inversement. Il faut `detach` avant, `./tools/wsl-attach.sh` pour revenir.

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
  vérifié 3 fois. **`esptool --after watchdog-reset` la relance**, lui : l'application redémarre et
  le log reprend à `up 0 s`.
- **Ne transposer aucune recette de reset DTR/RTS type CH343/CP2102** : le reset passe par le
  mécanisme propre au USB-Serial/JTAG. Le log de boot le confirme : `rst:0x15 (USB_UART_CHIP_RESET)`.
- **Le mode download ne change PAS le VID:PID** : toujours `303A:1001` avec ses 3 interfaces, et
  `COM3` revient au même endroit. On ne peut donc **pas** détecter le mode download en regardant
  l'identité USB. Ce qui le trahit : le port devient muet, et `esptool --before no-reset` réussit
  à dialoguer **sans reset préalable** (ce qui n'arrive que dans le bootloader ou le stub).
- **Le log part sur DEUX chemins à la fois** : la console UART0 (`GPIO43`/`GPIO44`, le header) **et**
  l'USB-Serial/JTAG, via la console secondaire activée par défaut. Le header UART est donc une voie
  de secours réellement vivante si l'USB pose problème.
- `/dev/ttyACM0` arrive en **`root:root crw-------`** et l'utilisateur n'est pas dans `dialout` :
  sans `chmod`, esptool sort `[Errno 13] Permission denied`.

### Écart connu, laissé à dn1-2

Le bootloader annonce `SPI Flash Size : 2MB` alors que la carte en porte **16 MB** : c'est la valeur
par défaut de l'IDF, non ajustée. Sans effet en P0 (l'application occupe 195 Ko sur une partition de
1 Mio, 81 % libre), mais à corriger quand la taille de l'image commencera à compter.

## Matériel

| Module | Rôle | I²C |
|---|---|---|
| ESP32-S3-Touch-LCD-2.8B | carte + écran + tactile (16 MB flash / 8 MB PSRAM, IMU QMI8658, RTC PCF85063, buzzer) | ext. : SCL=GPIO7, SDA=GPIO15 |
| BME680 | température, humidité, pression, VOC | 0x76/0x77 |
| BH1750 | luminosité ambiante | 0x23 |
| VL53L0X | proximité / présence | 0x29 |
| INA219 | tension / courant / puissance | 0x40 |

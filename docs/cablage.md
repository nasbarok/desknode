# Câbler un DeskNode, et vérifier que le bus répond

Cette page est écrite pour **quelqu'un qui vient de recevoir ses composants** et qui n'a jamais vu
cette carte. Elle dit **où brancher**, **ce qu'on doit voir ensuite**, et surtout **quoi faire quand
on voit autre chose**. Elle est la suite de [ce qu'il faut acheter](bom.md).

⚠️ **Ce qu'elle ne promet pas.** Ce n'est ⛔ pas un manuel du constructeur. **Chaque valeur publiée
ici cite la mesure d'où elle sort**, et elle le fait de **deux façons, ⛔ pas une** :

- une valeur **mesurée sur la carte** cite le **fichier du dossier matériel ET la section** — jamais
  la section seule, parce que le numéro nu ne désigne rien : les trois fichiers de `hardware/` ont
  des sections **homonymes** dont les contenus n'ont aucun rapport ;
- l'**état d'un chantier** ne vit ⛔ pas dans `hardware/` : il se cite par sa **clé**, son **statut**
  et la **date où le statut a été relu**.

Ce qui n'a pas été mesuré est écrit comme tel.

---

## 🔴 AVANT LE PREMIER FIL — la source que tu vas trouver en ligne est FAUSSE sur ce point

Le miroir Spotpear du wiki Waveshare, **relevé le 2026-08-16**, annonce pour ce connecteur
*« 1 GND · 2 3V3 · 3 SCL · 4 SDA »*. **Les broches 3 et 4 sont permutées** : la carte porte
`SDA` en 3 et `SCL` en 4. La même page annonce un header 2,54 mm là où c'est une **embase JST**, et
une puce `CH343P` que ce projet a mesurée **absente** de la carte.

⇒ **Si tu croises une autre source, c'est celle-ci qui est mesurée.** Sérigraphie relue sur la carte
et confirmée par constat, et le comptage `SDA`/`SCL` **inversés** de la source tierce est daté du
**2026-08-16** :
[`…-capteurs-i2c.md` §13.1](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md).

**La sérigraphie fait foi, ⛔ pas la position, ⛔ pas une page web.**

---

## Les DEUX points d'accès au bus I²C — et chacun a son piège

Il y a **deux** endroits où atteindre `SDA`/`SCL` sur cette carte. Ils marchent tous les deux. Ils
ont **le même piège**, sous deux formes, et ce piège produit **exactement le symptôme de la mauvaise
soudure** : le composant reste muet et **rien ne le signale**.

### Accès A — l'embase JST 4 broches

| Embase | Sérigraphie | Rôle | Source mesurée |
|---|---|---|---|
| côté **interrupteur ON/OFF** | `GND` `3V3` `SDA` `SCL` | ✅ **I²C** — `SDA` = **GPIO15**, `SCL` = **GPIO7** | [`…-capteurs-i2c.md` §13.1](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md) |
| côté **batterie / BAT** | `GND` `3V3` `TXD` `RXD` | ⛔ **UART** — ⛔ pas le bus | [`…-capteurs-i2c.md` §13.1](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md) |

🔴 **LE PIÈGE : les deux embases sont physiquement IDENTIQUES et ADJACENTES.** Se tromper
**alimente correctement** ton capteur — `3V3` et `GND` sont aux mêmes rangs des deux côtés — et lui
envoie l'**UART** à la place de l'I²C. Le capteur ne répondra jamais, et **rien ne dira pourquoi**.
Tu chercheras une mauvaise soudure pendant une soirée.
⇒ **Ce qui distingue la bonne embase : elle est du côté de l'interrupteur ON/OFF**, et sa
sérigraphie écrit `SDA` et `SCL`.

Photo de la sérigraphie des deux embases :
[les deux embases JST jumelles](cablage/2026-08-16_2228-carte-embases-jst-jumelles-i2c-uart.jpg).

### Accès B — le header 2×12 au pas de 2,54 mm

**Il n'y en a qu'UN**, déjà soudé, à deux rangées. C'est celui que ce projet utilise, parce qu'il
accepte du Dupont femelle sans adaptateur.

| Rangée | Positions 1 → 12 | Source mesurée |
|---|---|---|
| **B** — celle du bus | `5V` `VCC` `G` `D-` `D+` `0` `4` `16` **`SCL`** **`SDA`** `3V3` `G` | [`…-capteurs-i2c.md` §13.1 bis](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md) |
| **A** — ⛔ celle qu'il ne faut pas | `5V` `BAT` `G` `33` `34` `35` `36` `37` **`RXD`** **`TXD`** `3V3` `G` | [`…-capteurs-i2c.md` §13.1 bis](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md) |

🔴 **LE MÊME PIÈGE, AU PAS DE 2,54 mm.** `RXD` et `TXD` sont en positions 9 et 10 de la rangée A,
c'est-à-dire **exactement derrière** `SCL` et `SDA`. Se tromper de rangée alimente correctement le
capteur (`3V3` et `G` sont en 11-12 **des deux rangées**) et lui envoie l'UART : muet, sans
signal, encore une fois.
⇒ **La rangée B se reconnaît à ce qu'elle porte AUSSI `D-` `D+` `0` `4` `16`.** Compte les broches
en partant du bord, ⛔ ne te fie pas au côté.

✅ **Et c'est un gain, pas seulement un piège** : `3V3` et `G` étant en 11-12 sur **les deux**
rangées, tu disposes de **deux masses et deux 3V3** — de quoi alimenter les deux capteurs *et* tirer
`ADDR` du BH1750 à la masse sans te battre pour un point unique
([`…-capteurs-i2c.md` §13.1 bis](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).

---

## Le schéma, palier par palier

Ce sont **les deux mêmes paliers** que [la page d'achat](bom.md) et que le
[README](../README.md) — mêmes noms, ⛔ pas des synonymes.

### Palier « DeskNode » — la carte seule, et rien à câbler

**Il n'y a rien à câbler.** Un câble USB-C données, et c'est tout. Le firmware sait qu'il n'a pas de
capteur, il le dit, et il désarme ce qui n'a plus d'entrée. ⛔ Ne branche **rien** sur le bus : ce
palier est valide tel quel.

### Palier « DeskNode + Ambiance » — la carte + BME680 + BH1750

Quatre lignes partent de la carte et vont **aux deux modules en parallèle** : `SDA` et `SCL` sont un
**bus**, ils se partagent. Plus **une** cinquième liaison, locale au BH1750.

| Depuis la carte | Vers le BME680 | Vers le BH1750 (GY-302) | Source mesurée |
|---|---|---|---|
| `3V3` (rangée B, pos. 11) | `VCC` | `VCC` | [`…-capteurs-i2c.md` §13.4](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md) |
| `G` / `GND` (rangée B, pos. 12) | `GND` | `GND` | [`…-capteurs-i2c.md` §13.4](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md) |
| `SDA` = **GPIO15** (rangée B, pos. 10) | `SDA` | `SDA` | [`…-capteurs-i2c.md` §13.1](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md) |
| `SCL` = **GPIO7** (rangée B, pos. 9) | `SCL` | `SCL` | [`…-capteurs-i2c.md` §13.1](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md) |
| — | *(rien : `SDO` et `CS` restent en l'air)* | `ADDR` → **`GND`** | [`…-capteurs-i2c.md` §13.4 bis](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md) |

⚠️ **Les barrettes des deux modules sont FOURNIES NON SOUDÉES** — trous métallisés nus, barrette
libre dans le sachet. Il faut un fer
([`…-capteurs-i2c.md` §13.4](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).
Photo du BME680 tel qu'il arrive :
[barrette non soudée](cablage/2026-08-16_2140-bme680-recto-barrette-non-soudee.jpg) ·
photo du BH1750 côté broches :
[`VCC GND SCL SDA ADDR`](cablage/2026-08-19_1720-bh1750-gy302-face-broches-vcc-gnd-scl-sda-addr.jpg).

### 🔴 LE PIÈGE DU MIROIR — ⛔ ne pose PAS les fils « dans l'ordre »

```
accès A — embase JST      :  GND   3V3   SDA   SCL
accès B — rangée B, 9→12  :  SCL   SDA   3V3   G
BME680                    :  VCC   GND   SCL   SDA   SDO   CS
BH1750 (GY-302)           :  VCC   GND   SCL   SDA   ADDR
```

⚠️ **Les deux accès n'ont PAS le même ordre, et ⛔ ce n'est pas une coquille** : l'embase JST donne
`GND 3V3 SDA SCL`, la rangée B donne `SCL SDA 3V3 G` — ordre **différent** et **inversé**. La ligne
`embase` est celle que la source étiquette, mot pour mot, *« câble / embase carte »* ; la rangée B
vient de la table de sérigraphie plus haut sur cette page. ⛔ **Ne transpose pas l'une sur l'autre.**

⇒ **Aucun des deux modules ne s'aligne « premier avec premier », sur AUCUN des deux accès.** Poser
les quatre fils dans l'ordre **inverse l'alimentation** (`VCC` sur `GND`) **et croise `SDA`/`SCL`**
— sur les deux modules.
Source : [`…-capteurs-i2c.md` §13.4 bis](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md).
**Vérifie chaque fil par le NOM écrit aux deux bouts**, ⛔ jamais par le rang.

### Pourquoi `ADDR` va à la masse

Sur le BH1750, `ADDR` n'est **pas** une broche libre : c'est une **entrée de sélection d'adresse**.
La datasheet ROHM ne définit `0x23` que pour `ADDR ≤ 0,3 × VCC`, et **flottant est INDÉFINI** —
décision écrite de ce projet : **souder `ADDR` à `GND`**
([`…-capteurs-i2c.md` §13.4 bis](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).

⚠️ **Et la mesure, elle, dit que l'exemplaire testé s'en passe** : branché avec les 4 fils de bus
**seulement**, sans fil `ADDR`, il a répondu `0x23` **5 fois sur 5** et `0x5C` n'est apparu nulle
part ⇒ `ADDR` est tiré bas **sur ce GY-302**
([`…-capteurs-i2c.md` §13.16.8](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).
⇒ **Le fil reste recommandé** : il rend l'adresse déterministe **quel que soit ton exemplaire**, et
il coûte une soudure. ⛔ Un exemplaire mesuré n'est pas une garantie de série.

---

## Ce que le bus doit répondre

| Adresse | Composant | D'où il vient | Source mesurée |
|---|---|---|---|
| `0x20` | TCA9554 | soudé sur la carte — **témoin positif** | [`…-capteurs-i2c.md` §13.3](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md) |
| `0x23` | BH1750 | **ton module d'ambiance** | [`…-capteurs-i2c.md` §13.3](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md) |
| `0x51` | PCF85063A | soudé sur la carte (horloge) | [`…-capteurs-i2c.md` §13.3](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md) |
| `0x5D` | GT911 | soudé sur la carte (tactile) — **témoin positif** | [`…-capteurs-i2c.md` §13.3](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md) |
| `0x6B` | QMI8658 | soudé sur la carte (IMU) | [`…-capteurs-i2c.md` §13.3](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md) |
| `0x77` | BME680 | **ton module d'ambiance** | [`…-capteurs-i2c.md` §13.3](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md) |

⚠️ **Cette table n'est PAS exhaustive : elle donne ce que TES deux paliers rendent.** Au palier
« DeskNode » (carte seule) tu verras **QUATRE** adresses — `0x20`, `0x51`, `0x5D`, `0x6B`, les
composants soudés sur la carte ; au palier « DeskNode + Ambiance », **SIX**.

🔴 **Et si tu lis « 8 devices » ailleurs dans ce dépôt, les deux de plus sont NOMMÉS** : `0x29`
(**TOF050C-VL6180X**, distance) et `0x40` (**INA219**, courant). Ils étaient sur le prototype, ils
ne sont **dans aucun palier V1**, et [la page d'achat](bom.md) écrit pourquoi
([`…-capteurs-i2c.md` §13.3](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).
⇒ ⛔ Ne cherche pas `0x23` ou `0x77` avant d'avoir câblé tes modules, et ⛔ ne t'attends pas à
`0x29` ni `0x40` : tu ne les as pas achetés.

🎯 **`0x20` et `0x5D` sont tes DEUX TÉMOINS POSITIFS.** Ils sont soudés sur la carte, ils sont là
avant que tu branches quoi que ce soit. **Un scan qui ne les voit pas de façon stable est un
instrument cassé** — et aucune conclusion sur un composant neuf n'est alors recevable
([`…-capteurs-i2c.md` §13.3](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).

🔴 **Le BME680 de cette carte est à `0x77`, ⛔ pas à `0x76`.** Sa broche `SDO` a été mesurée à
**3,3 V** sur le breakout, carte allumée, ce qui sélectionne l'adresse haute ; sa broche `CS` est
tirée, donc la puce est en mode I²C
([`…-capteurs-i2c.md` §13.4](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).

---

## 🔴 LA PROCÉDURE DE VÉRIFICATION — et pourquoi UNE passe ne suffit pas

Branche la carte en USB, ouvre la console série, et tape `i2c`. La commande scanne `0x08`..`0x77` et
**re-sonde 5 fois** chaque trouvaille, en publiant le résultat `n/5`
([`…-capteurs-i2c.md` §13.6](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).

### Pourquoi `n/5` et ⛔ pas un scan simple

Ce n'est pas de la prudence, c'est **un fait mesuré avant qu'aucun capteur ne soit branché** :
quatre passes consécutives, bus strictement inchangé, ont rendu 4 adresses stables **et une
cinquième qui changeait à chaque fois**. Sur la séance entière — **~20 scans — une quinzaine de faux
positifs, tous à des adresses différentes, aucun jamais reproduit**
([`…-capteurs-i2c.md` §13.2](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).

⇒ **Un scan à une seule passe FABRIQUE des adresses.** Fais toujours **plusieurs passes**, et lis le
`n/5`. Sur cette séance, les faux positifs ne sont **jamais montés au-dessus de `1/5`**, et les vrais
composants sont sortis **`5/5`**.

### 🔴 `0x76` — le faux positif qu'il faut connaître AVANT de le voir

L'un de ces faux positifs est tombé sur **`0x76`** — **l'adresse par défaut d'un BME680** — alors
qu'**aucun capteur n'était branché**
([`…-capteurs-i2c.md` §13.2](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).

⇒ Si ton scan rend `0x76` : ⛔ **ça ne veut PAS dire que ton capteur répond.** C'est un faux positif
**mesuré** sur cette carte, et **le BME680 de ce montage est à `0x77`**, sa broche `SDO` étant à
3,3 V ([`…-capteurs-i2c.md` §13.4](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).
Conclure « le capteur répond » sur un `0x76`, c'est câbler un driver par-dessus et chercher pendant
des heures pourquoi il ne lit que du vide.

### Ce qu'on conclut d'un DÉSACCORD entre passes

| Ce que tu lis | Ce que ça veut dire | Ce que ça ne veut ⛔ PAS dire |
|---|---|---|
| `5/5` | le composant est là, à cette adresse | qu'il **fonctionne** — le scan découvre, il ne qualifie pas |
| `n/5` avec `n < 5` | 🔴 **« à ne pas croire sur parole »** | ⛔ **« faux positif prouvé »** |
| rien du tout | rien n'a acquitté à cette adresse | que la broche est mal soudée — voir les deux pièges d'embase ci-dessus |
| `probe device timeout` | l'adresse n'a **pas été sondée** | ⛔ **une absence** |

🔴 **`n/5 < 5` n'est PAS un verdict.** La règle n'est pas absolue et c'est écrit : `0x6B`, l'IMU
**soudée sur la carte**, est déjà tombée à `1/5`. Un vrai composant peut rater une confirmation
([`…-capteurs-i2c.md` §13.2](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).

🎯 **CE QUI TRANCHE : `i2c lire <addr> D0`.** Une lecture de **registre**. Un faux positif n'a aucun
registre à rendre ; un BME680 rend son *chip id* `0x61`
([`…-capteurs-i2c.md` §13.6](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).

⚠️ Le BH1750, lui, **n'a aucun registre** : il se qualifie par **stimulus** — `i2c ecrire 23 01`
puis `i2c ecrire 23 10`, puis `i2c brut 23 2` en posant et retirant la main. La **première lecture
rend `00 00`** parce que la mesure n'est pas prête : ⛔ ne conclus pas sur une lecture unique
([`…-capteurs-i2c.md` §13.16.8](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).

⚠️ **Un timeout n'est PAS une absence.** La première version de la commande sondait à 20 ms et a
produit un `probe device timeout` : une adresse **jamais sondée**, comptée nulle part, dans une liste
qui se lisait comme exhaustive. Le sondage est passé à **50 ms** et les timeouts sont désormais
**comptés et signalés** — s'il en reste un, **relance**, ⛔ ne conclus pas
([`…-capteurs-i2c.md` §13.2](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).

### ⛔ « Je bouge un fil et je rescanne » NE CONVERGE PAS

C'est le réflexe naturel, et il est **structurellement faux sur cette famille de modules** :
débrancher `VCC` **ne coupe pas** le capteur. Il reste alimenté **parasitairement** par les tirages
du bus, à travers ses diodes de protection sur `SDA`/`SCL` — assez pour **acquitter à `5/5`**, pas
assez pour tenir sa configuration
([`…-capteurs-i2c.md` §13.10](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).

⇒ **La seule séquence valable est : bouger → COUPER L'ALIMENTATION → rescanner.** Couper
l'alimentation veut dire **débrancher le câble USB** — ⛔ ni un `reboot`, qui laisse le rail 3V3
debout, ⛔ ni le retrait du fil `VCC`
([`…-capteurs-i2c.md` §13.4 bis](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).

⚠️ **Il existe un TROISIÈME état**, entre « sain » et « absent » : **fantôme** — présent, bavard,
`5/5`, et **des valeurs fausses ET plausibles**. C'est ce que produit un capteur alimenté par le bus
seul : il a été mesuré à 32,8 °C et 100 %RH, affichés comme fiables
([`…-capteurs-i2c.md` §13.10](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).

### ⚠️ ET SI TU VIENS DE BRANCHER LA CARTE À FROID, ATTENDS UNE MINUTE

Sur six démarrages à froid réels, **un cycle sur six** est parti dégradé : le scan disait
**« 8 stables », témoin positif vert**, pendant que le tactile encaissait **950 erreurs I²C sur
1 713 lectures — 55,5 %**. Ce n'est ⛔ ni une soudure ⛔ ni ton capteur : c'est une dégradation
**transitoire de tout le bus**, qui dure **~40 s** et se rétablit **seule**
([`…-capteurs-i2c.md` §13.17.1](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).

⇒ **Après un branchement à froid, laisse passer une minute avant de conclure quoi que ce soit.** Un
scan pris dans cette fenêtre peut être **parfaitement vert et complètement trompeur** — c'est la
démonstration la plus extrême de la règle du dépôt : *le scan DÉCOUVRE, seule une transaction de
DONNÉE qualifie.*

⛔ **La cause reste ENTIÈRE, et elle a un porteur** : `dn4-26`, statut **`backlog`**, relu le
**2026-09-07**. Ce qui existe aujourd'hui empêche le **briquage** de la carte, ⛔ il ne répare pas
le bus. ⛔ On ne t'écrit donc pas « corrigé ».

---

## `TESTED` — ce qui a réellement tourné, et ce qui n'a JAMAIS été essayé

⛔ **Le silence n'est pas un `TESTED`.** Chaque bloc dit ce qui a tourné, **combien de temps**, sur
**quel SHA de firmware**, et **ce qui n'a jamais été exercé**. Ces blocs sont ce que ce projet peut
défendre, ⛔ pas ce qu'il aimerait annoncer.

### `TESTED` — palier « DeskNode »

| | |
|---|---|
| **Ce qui a tourné** | Le comportement « aucun capteur joignable » : la carte boote, l'affichage passe à `--`, le rétroéclairage automatique **gèle** son duty au lieu de tomber à zéro, et rien ne boucle ni ne plante. Verdict `ABSENT` atteint dans les deux modules au même mot, **réversible et compté**. |
| **Combien de temps** | Fenêtres de séance, **120 s minimum par cycle** de lecture (soit deux fois la fenêtre froide), sur **six démarrages à froid réels** dont un boot observé **630 s** ([`…-capteurs-i2c.md` §13.29.2](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)). ⛔ Aucune veille longue. |
| **Sur quel SHA** | `4f9b401`, puis `c081a6c`, puis `762b767` — **trois binaires, ⛔ pas un**, tous lus au bandeau de démarrage. ⚠️ Ces trois SHA viennent du **tracker**, clé `dn4-41`, statut relu le **2026-09-07** : ⛔ ils n'ont pas de section citable dans `hardware/`, et c'est écrit plutôt que maquillé. |
| **Ce qui n'a JAMAIS été essayé** | 🔴 **Le démarrage à froid SANS AUCUN CAPTEUR DU TOUT n'a jamais été exercé**, et les conditions électriques d'un bus nu non plus. Motif écrit : **il n'existe qu'une seule carte**, celle du développement, et l'owner a préféré ne rien débrancher. ⇒ ce palier part **raisonné et instrumenté**, ⛔ **jamais démarré sur silicium nu**. Tu es peut-être le premier à l'assembler. |
| **État de la marche qui l'établit** | `dn4-41`, statut **`in-progress`**, relu le **2026-09-07**. ⛔ On ne t'écrit pas « validé ». |

### `TESTED` — palier « DeskNode + Ambiance »

| | |
|---|---|
| **Ce qui a tourné** | Le bus à **huit devices**, les deux capteurs qualifiés **par une transaction de donnée** (BME680 : *chip id* + coefficients d'usine · BH1750 : stimulus lumineux, rapport **×13 286 à ×14 990** entre main posée et main retirée, [`…-capteurs-i2c.md` §13.17.4](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)), scan de contrôle en fin de régime **8 stables, témoin positif vert**. |
| **Combien de temps** | 🎯 **31 min 32 s = 1 892 s, CHRONOMÉTRÉS à l'horloge de l'hôte** — ⛔ pas déduits d'un compteur : **0 erreur I²C sur 53 652 lectures** du tactile et **378 lectures BME680 sans erreur** ([`…-capteurs-i2c.md` §13.17.9](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)). Plus **six démarrages à froid réels**, zéro faux positif ([`…-capteurs-i2c.md` §13.29.2](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)). |
| **Sur quel SHA** | `8c928db` pour le régime long chronométré ([`…-capteurs-i2c.md` §13.17](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)) ; `4f9b401` / `c081a6c` / `762b767` pour les démarrages à froid — ces trois-là viennent du **tracker**, clé `dn4-41`, statut relu le **2026-09-07**. |
| **Ce qui n'a JAMAIS été essayé** | 🔴 **Le fonctionnement continu longue durée n'a jamais tenu plus de 60 SECONDES.** Le journal de ce fonctionnement continu part à `2026-08-26 23:27:39` et s'arrête à `23:28:39` ; l'`up` de la carte y plafonne à **50 s**. ⚠️ Ces trois chiffres viennent du **tracker**, clé `dn4-5`, statut relu le **2026-09-07** — ⛔ pas de `hardware/`. Et ce n'est pas qu'il a été coupé : **le lanceur livré ne sait pas l'armer**. ⇒ ⛔ aucune donnée au-delà de la demi-heure chronométrée ci-dessus. La fenêtre de régime reste **5,2× plus courte** que la référence de ce dépôt en nombre de lectures, et le cycle dégradé à froid **n'a pas été observé** sur les six derniers cycles — ce qui s'écrit **« non observé sur 6 cycles »**, ⛔ **jamais « prouvé »** ([`…-capteurs-i2c.md` §13.29.2](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)). |
| **État de la marche qui l'établit** | `dn4-5`, statut **`in-progress`**, relu le **2026-09-07**. ⛔ On ne t'écrit pas « validé ». |

⚠️ **Ce que ces deux blocs ne couvrent pas, et c'est écrit** : le régime long a été tenu **à chaud**,
après un boot sain. La non-régression est établie **en régime**, ⛔ pas **au démarrage à froid**
([`…-capteurs-i2c.md` §13.17.9](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)).

---

## Où lire la mesure complète

Les valeurs de cette page sortent toutes du **journal de mesure** de la carte, qui n'est ⛔ pas une
page de lecture : c'est un dossier de séance, avec ses ratés et ses rétractations. Il vit dans
`hardware/` et le fichier qui porte le bus I²C est
[`ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md`](../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md).

⚠️ **Cite toujours le FICHIER avec la section.** Les trois fichiers de `hardware/` portent des
sections **homonymes** — un même numéro y désigne deux contenus sans rapport. C'est pour ça que
chaque renvoi de cette page nomme les deux.

---

## Licence

Cette page est de la documentation : **CC-BY-SA-4.0**, comme le reste de ce répertoire. Voir
[LICENSING.md](../LICENSING.md).

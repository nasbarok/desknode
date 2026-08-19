# §13 — Les capteurs sur le bus I²C externe (dn2-1, P4)

> **Fichier frère** de `ESP32-S3-Touch-LCD-2.8B-affichage.md`, référencé depuis sa §13.
> Même règle que lui : **tout ce qui est ici a été mesuré sur la carte**, et là où la mesure a
> corrigé une source tierce, c'est écrit noir sur blanc avec la source fautive.
>
> ✅ **ÉTAT FINAL DE LA STORY : le BME680 est SOUDÉ, mesuré à `0x77`, et ses deux grandeurs
> vivent à l'écran.** Les encarts ci-dessous racontent la séance **dans son ordre chronologique** —
> plusieurs d'entre eux étaient vrais à leur heure et ont été dépassés depuis. Chacun porte sa date.
>
> 🔴 **ORDRE DE LECTURE — la numérotation de ce fichier N'EST PAS CROISSANTE** (constat de la revue
> du 2026-08-17, laissée telle quelle pour ne pas casser les renvois déjà écrits ailleurs) :
> `13.0 → 13.1 → 13.2 → 13.3 → 13.4 → 13.5 → 13.6 → 13.6 bis → 13.6 ter → 13.8 → 13.9 → 13.10 →
> 13.11 → 13.7`. **§13.7 « Ce que la séance laisse » FERME le fichier** malgré son numéro, et
> §13.8 porte les budgets. ⚠️ Citer « §13.6 » pour un coût binaire, c'est citer un chiffre d'étape
> que §13.8 a déjà remplacé.
>
> ✅ **DÉNOUEMENT (2026-08-17, 00h45) — LE CAPTEUR EST VIVANT, ET C'EST UN VRAI BME680.**
> Contact rétabli par repositionnement manuel de la barrette (owner : « là je vois bien toutes
> les pins connectées »), maintenu à la main pendant la mesure :
>
> ```
> 0x77  5/5   — stable sur 8 scans consécutifs
> 0x77 reg 0xD0 : 61   => chip id 0x61 = BME680 ou BME688
> 0x77 reg 0xF0 : 00   => variant 0x00 = BME680
> ```
>
> **L'arbre de diagnostic de §13.5 est SOLDÉ : c'était l'hypothèse 6** (les broches signal ne
> touchaient pas dans les trous non soudés). La 7 (puce morte) est morte avec, et le chemin
> embase JST → bus est désormais **PROUVÉ** par un composant qui répond à travers lui.
> ⚠️ **À cette heure-là, le contact était tenu à la main : la SOUDURE demeurait obligatoire** avant
> toute campagne (cadence, auto-échauffement, budgets) — un chiffre pris sur un contact précaire
> n'est pas recevable.
> ✅ **ELLE A ÉTÉ FAITE le 2026-08-17** (voir §13.6 bis, « Après SOUDURE ») : toutes les campagnes
> publiées dans ce fichier ont été jouées **après**. Cette phrase est conservée parce qu'elle datait
> une contrainte réelle, pas parce qu'elle vaut encore.

Séance du **2026-08-16** (`/desknode-board`), firmware `ce32c87` puis la commande `i2c` de dn2-1.

---

## 13.0 LES PHOTOS — la base probante (dn2-1 le 2026-08-17, **les 3 breakouts le 2026-08-19**)

Livrable du **critère n°5 du brief** (« câblage photographié, capteurs référencés ») et des AC1/AC2.
Elles vivent dans **`docs/cablage/`** et sont **nommées par leur horodatage EXIF**, pas par ce qu'on
croit y voir — c'est l'horodatage qui les situe dans la séance, et il a déjà corrigé une lecture.

| Fichier (`docs/cablage/`) | EXIF | Ce qu'elle ÉTABLIT |
|---|---|---|
| `2026-08-16_2140-bme680-recto-barrette-non-soudee.jpg` | 21:40:12 | Le breakout **face composants** : sérigraphie `VCC GND SCL SDA SDO CS`, la puce, et la **barrette 6 broches fournie NON SOUDÉE posée à côté**. Plus le câble JST→Dupont 4 fils. C'est l'inventaire T1 (AC1) |
| `2026-08-16_2228-carte-embases-jst-jumelles-i2c-uart.jpg` | 22:28:41 | 🔴 **Les DEUX embases JST jumelles avec leurs sérigraphies lisibles** : `GND 3V3 SDA SCL` et `GND 3V3 TXD RXD`. C'est **la preuve photographique de §13.1** (le miroir Spotpear annonçait `SCL·SDA`) **et du Trap n°7** (les deux embases sont identiques et adjacentes). On y lit aussi le header 2×12 soudé portant `SCL SDA 3V3 G` |
| `2026-08-17_0012-cablage-4-fils-sous-tension.jpg` | 00:12:29 | Le **montage 4 fils en fonctionnement** : JST sur la BONNE embase, wattmètre en ligne (~0,5 W), et le breakout **posé à l'écart de la carte** — l'exigence AC2 « sur fils volants, écarté de la carte » constatée en image |
| `2026-08-17_0012-breakout-ecarte-barrette-inseree.jpg` | 00:12:33 | Gros plan du breakout écarté, barrette **insérée dans ses trous** et bloc Dupont enfiché |

🔴 **LES NEUF PHOTOS DE `dn4-2`** — versées le **2026-08-19**, prises par l'owner entre **17:18:48
et 17:20:58** (EXIF). Elles couvrent les **trois nouveaux breakouts, sur leurs DEUX faces**, et
c'est l'une d'elles qui **réfute l'étiquette « VL53L0X »** portée depuis le 2026-08-14 par le brief,
l'epic, le tracker, `dn_pins.h`, `i2c_nom_connu()` et six stories.

| Fichier (`docs/cablage/`) | EXIF | Ce qu'elle ÉTABLIT |
|---|---|---|
| `2026-08-19_1718-tof050c-vl6180x-face-capteur-et-sachet.jpg` | 17:18:48 | 🔴 **LA PIÈCE QUI RÉFUTE « VL53L0X ».** Étiquette du sachet lisible : **`F2/ TOF050C-VL6180X`**, *« Laser Ranging Sensor Module »*, *« Color: TOF050C-VL6180X »*. Le module montre sa **face capteur** (boîtier optique noir) et la barrette 6 broches **fournie NON SOUDÉE** |
| `2026-08-19_1718-tof050c-vl6180x-face-capteur-et-sachet-2.jpg` | 17:18:49 | Même cadrage, **seconde prise** — la sérigraphie `TOF050C-VL6180X` du bord bas de la carte y est lisible. ⇒ **la référence est lue DEUX FOIS et sur DEUX supports** : le sachet **et** le cuivre |
| `2026-08-19_1719-tof050c-vl6180x-face-broches-et-sachet.jpg` | 17:19:00 | 🔴 **LE VERSO du ToF** : la **face broches**, sérigraphie `VIN · GND · SDA · SCL · INT · XSHUT` — **six** broches, dont **deux qui ne sont pas des signaux de bus** et qui décident si la puce répond (`XSHUT`) |
| `2026-08-19_1719-tof050c-vl6180x-face-broches-deux-barrettes.jpg` | 17:19:20 | Face broches en gros plan, **DEUX barrettes** posées à côté (une droite, une coudée) — les deux **non soudées**. C'est l'état de départ de T5 |
| `2026-08-19_1719-ina219-cjmcu-recto-cavaliers-a0-a1-shunt-r100.jpg` | 17:19:56 | 🔴 **LE RECTO de l'INA219, et il porte les DEUX choses qui décident de son adresse et de sa mesure** : les cavaliers de sélection **`A0` et `A1`** (sérigraphie *« I2C Address »*), **VISIBLEMENT NON PONTÉS** — ⇒ `A1=A0=GND` ⇒ **`0x40`** (TI SBOS448G, Table 1) — et le **shunt `R100`** (0,1 Ω). Sérigraphie des broches : `Vin+ · Vin- · Sda · Scl · Gnd · Vcc`. Bornier à vis 2 points et barrette 6 broches **fournis NON SOUDÉS** |
| `2026-08-19_1720-ina219-cjmcu-verso-caracteristiques.jpg` | 17:20:04 | **Le VERSO de l'INA219** : `INA219 DC Current Monitor` · `CJMCU` · `Bus Voltage: 0~26V` · `Max Current: 3.2A` · **`VCC/LOGIC: 3~5V`** ⇒ ✅ **compatible 3V3**, aucun adaptateur de niveau nécessaire |
| `2026-08-19_1720-bh1750-gy302-face-composants-et-sachet.jpg` | 17:20:45 | Étiquette du sachet : *« 1PCS GY-30 GY-302 BH1750fvi BH1750 **3V-5V** … Of Module For Arduino#Color: **GY-302** »* ⇒ la variante est **GY-302**, pas GY-30. Barrette 5 broches **fournie NON SOUDÉE** |
| `2026-08-19_1720-bh1750-gy302-face-composants-serigraphie-v322.jpg` | 17:20:48 | **La face composants du BH1750** : sérigraphie **`BH1750`** et **`V322`** (révision de carte), la puce 6 broches, et le bloc de composants passifs côté barrette. ⚠️ **Les marquages de ces passifs NE SONT PAS LISIBLES** — voir l'encart Y6 ci-dessous |
| `2026-08-19_1720-bh1750-gy302-face-broches-vcc-gnd-scl-sda-addr.jpg` | 17:20:58 | 🔴 **LE VERSO du BH1750, et c'est la photo qui compte** : sérigraphie `VCC · GND · SCL · SDA · **ADDR**` — **CINQ** broches, la cinquième étant **une entrée de sélection d'adresse**, pas un signal de bus. Sérigraphie `GY-302` / `V322` confirmée sur cette face aussi |

✅ **LE VERSO DU BME680 EST SOLDÉ PAR CONSTAT OWNER, PAS PAR PHOTO** — 2026-08-19, verbatim :
*« le verso c'est juste écrit `bme680` dessus (en plus elle fonctionne et est branchée) »*.
Le legs **D2-1a** demandait *« recto ET verso »* parce qu'une face non regardée peut porter un pont
de sélection, une référence de variante ou un tirage. **L'owner a regardé : il n'y a qu'une
sérigraphie.** C'est **l'instrument valide** — l'œil de l'owner, ⛔ jamais une déduction de l'agent.
⇒ Cette ligne est un **CONSTAT**, ⛔ pas une photo qui existerait.

> 🔴 **Y6 — LES TIRAGES DE BUS : L'INVENTAIRE PHOTO NE PEUT PAS LES LIRE, ET C'EST ÉCRIT PLUTÔT QUE
> CONTOURNÉ.** Les trois breakouts portent chacun un bloc de passifs côté barrette (tirages
> `SDA`/`SCL`, découplage). Les neuf photos ont été **recadrées et agrandies ×10 au cadrage** sur
> ces blocs : **aucun code de marquage n'est lisible** — le flou optique est plus large que le
> caractère. ⇒ **Valeur des tirages : NON MESURÉE.** ⛔ Ne pas recopier « 4,7 kΩ » d'un catalogue :
> ce serait exactement l'étiquette héritée que cette story vient de réfuter sur le ToF.
> **Ce qui est acquis quand même** : on passe de **2 à 5 jeux de tirages en parallèle** sur le même
> bus, donc la résistance équivalente **est divisée**, donc le courant que chaque device doit
> encaisser à l'état bas **augmente** (limite I²C : **3 mA**). Ce n'est pas nécessairement un
> défaut — un tirage plus fort accélère les fronts — **mais c'est une variable qui change dans cette
> story et que personne n'avait nommée.**
> ⇒ **Ce qui la solderait** : ohmmètre entre `SDA` et `VCC`, puis `SCL` et `VCC`, **breakout seul et
> hors tension**, avant soudure (deux minutes, T5). À défaut, elle se lit dans le **budget d'erreurs
> d'AC8** : si des erreurs apparaissent à 8 devices, **les tirages sont un suspect nommé d'avance**.

> 🔴 **CE QUE CES PHOTOS NE MONTRENT PAS, ET IL FAUT LE LIRE AVANT DE LES CITER.**
> Les quatre horodatages sont **antérieurs au dénouement de séance (~00h45) et à la soudure**
> (2026-08-17, plus tard). ⇒ **Aucune ne documente l'état SOUDÉ**, ni le montage final.
> La quatrième montre une barrette **insérée**, pas soudée — et c'est précisément l'état dans
> lequel le capteur **NE répondait PAS** (hypothèse 6 de §13.5). Elle vaut donc comme témoin du
> défaut, pas comme preuve du montage.
> ⚠️ **MISE À JOUR 2026-08-19 (dn4-2) — l'encart n'est PAS effacé, il est corrigé point par point,
> parce que ce qu'il annonçait comme manquant ne l'est plus tout à fait :**
> - ✅ **Les 3 autres breakouts SONT photographiés**, recto ET verso — 9 photos, table ci-dessus.
>   Le legs **D2-1a** est **SOLDÉ**.
> - ✅ **Le verso du BME680** est soldé **par constat owner**, pas par photo (encart ci-dessus).
> - ⛔ **RESTE VRAI, ET C'EST DÛ DANS `dn4-2` MÊME** : **aucune photo du dépôt ne documente l'état
>   SOUDÉ des trois modules, ni le montage final à 8 devices.** C'est **AC5** qui les produit.
> - ⛔ **RESTE VRAI AUSSI** : les quatre photos de dn2-1 restent antérieures à la soudure du BME680.
> ⇒ **AC1 de `dn2-1` est SOLDÉ ; AC5 de `dn4-2` reste OUVERT.**

⚠️ **Correction d'une lecture faite trop vite, consignée parce qu'elle est du genre que ce dépôt
traque** : la quatrième photo a d'abord été décrite comme « barrette **soudée** » sur la seule foi
de l'image. L'EXIF l'a réfutée — 00:12:33, soit 33 minutes **avant** que le capteur ne réponde pour
la première fois. **L'horodatage est l'instrument, l'œil sur une photo floue ne l'est pas.**

---

## 13.1 🔴 LE BROCHAGE DU HEADER I²C — LA SOURCE TIERCE AVAIT SDA ET SCL INVERSÉS

**Ce que la carte porte réellement**, lu sur sa sérigraphie (deux lectures concordantes : photo
+ constat owner) :

| Connecteur JST 4 broches | Sérigraphie | Rôle |
|---|---|---|
| côté **BAT / batterie** | `GND  3V3  TXD  RXD` | **UART** (GPIO43/44) |
| côté **interrupteur ON/OFF** | `GND  3V3  SDA  SCL` | ✅ **I²C** (GPIO15/GPIO7) |

**Ce que la source tierce annonçait** — miroir Spotpear du wiki Waveshare
(`spotpear.com/wiki/ESP32-S3R8-2.8-inch-LCD-Display-RGB-TouchScreen-480x640.html`, relevé le
2026-08-16) : *« 1 GND · 2 3V3 · 3 SCL · 4 SDA »*, sur un **header 2,54 mm**.

⇒ **DEUX ERREURS DANS LA MÊME LIGNE** : les broches 3 et 4 sont **permutées**, et le connecteur
n'est pas un header 2,54 mm mais une **embase JST**. *(Un header 2×12 en 2,54 mm existe bel et
bien sur la carte, déjà soudé, et il expose lui aussi `SCL`, `SDA`, `3V3`, `G` — la source a
probablement confondu les deux.)*

⚠️ **La même page annonce un « CH343P USB to UART chip »**, que dn1-1 a mesuré **absent** (USB
natif `303a:1001`, aucun périphérique `1A86`). **Elle mélange les variantes 2.8 et 2.8B.**

> 🔴 **C'est la DEUXIÈME fois qu'une source externe se fait corriger sur ce matériel**, après
> l'ordre des bits RGB de dn1-2 (§1.1). Si le tableau Spotpear avait été suivi, SDA et SCL
> auraient été croisés, le capteur n'aurait jamais répondu — et le diagnostic serait parti du
> côté du capteur, avec un `CS` flottant comme faux coupable tout désigné pour brouiller la
> piste. **La règle de ce dépôt tient : on ne va plus chercher un brochage ailleurs.**

⚠️ **Les deux embases sont physiquement identiques et adjacentes.** Se tromper d'embase alimente
correctement le capteur (3V3 + GND aux mêmes rangs) mais lui envoie l'UART à la place de l'I²C :
le composant reste muet, et rien ne signale l'erreur. **La sérigraphie fait foi, pas la position.**

---

## 13.2 🔴 LE SCAN DE BUS À UNE SEULE PASSE FABRIQUE DES FAUX POSITIFS — ET IL EN A FABRIQUÉ UN À 0x76

**Le fait, mesuré avant qu'aucun capteur ne soit branché.** La première version de la commande
`i2c` sondait chaque adresse **une fois**. Quatre passes consécutives, bus strictement inchangé,
carte au repos :

| Passe | Adresses rendues |
|---|---|
| 0 | `0x20` `0x51` `0x5D` `0x6B` + **`0x6F`** (+ 1 timeout) |
| 1 | `0x20` `0x51` `0x5D` `0x6B` |
| 2 | `0x20` `0x51` `0x5D` `0x6B` |
| 3 | `0x20` `0x51` `0x5D` `0x6B` + **`0x58`** |

Quatre adresses stables, et une cinquième **qui change de valeur à chaque fois**.

**Sur l'ensemble de la séance : ~20 scans, une quinzaine de faux positifs, TOUS À DES ADRESSES
DIFFÉRENTES** (`0x6F 0x58 0x2E 0x76 0x29 0x49 0x2D 0x53 0x5A 0x0D 0x67 0x73 0x15 0x65 0x19 0x62
0x4C 0x59 0x22 0x40 0x09 0x43`), **aucun jamais reproduit**, pendant que les quatre vrais
composants répondent à chaque sondage.

> 🔴 **ET L'UN DE CES FAUX POSITIFS ÉTAIT `0x76` — L'ADRESSE MÊME DU BME680 — ALORS QU'AUCUN
> CAPTEUR N'ÉTAIT BRANCHÉ.** Avec le scan d'origine, la séance aurait conclu « le capteur
> répond », aurait câblé un driver par-dessus, et aurait cherché pendant des heures pourquoi il
> ne lit que du vide. **L'instrument était incapable de voir le défaut qu'il prétendait exclure**
> — le Trap n°2 de la story, appliqué à l'outil que la story elle-même demandait d'écrire.

**La parade, en vigueur :** chaque adresse détectée est **re-sondée 5 fois** et le résultat est
publié `n/5`. Séparation totale sur toute la séance — faux positifs **jamais au-dessus de 1/5**,
vrais composants **à 5/5**.

⚠️ **La règle n'est pas absolue, et c'est écrit** : à une passe, `0x6B` (l'IMU, **soudée sur la
carte**) est tombée à `1/5`. Un vrai composant peut donc rater une confirmation. `n/5 < 5` veut
dire « à ne pas croire sur parole », pas « faux positif prouvé ». Ce qui tranche définitivement :
**`i2c lire <addr> D0` — un faux positif n'a aucun registre à rendre.**

⚠️ **Un timeout n'est pas une absence.** La première version sondait à **20 ms** (= 2 ticks à
100 Hz) et a produit un `probe device timeout` : une adresse **jamais sondée**, comptée nulle
part, dans une liste qui se lisait comme exhaustive. Cause probable : `i2c_master_probe()` prend
le **verrou de bus**, que le polling du GT911 tient ~30 fois par seconde. Porté à **50 ms**, et
les timeouts sont désormais **comptés et signalés**.

**Effet de bord exploité en dn2-1** : le compteur `n/5` est aussi un **mesureur de qualité de
contact**. Un composant dont la barrette n'est pas soudée sortirait `2/5` ou `3/5` là où un
composant soudé sort `5/5`.

---

## 13.3 Les occupants RÉELS du bus — mesurés, pas déclarés

Scan stable (`5/5`), reproduit sur ~20 passes :

| Adresse | Composant | Statut avant cette séance |
|---|---|---|
| **`0x20`** | TCA9554 — expander (LCD_RST bit 0, TP_RST bit 1, LCD_CS bit 2) | connu, piloté depuis dn1-2 |
| **`0x51`** | **PCF85063 — RTC** | ✅ **VIVANTE, première confirmation.** Elle n'avait jamais répondu à quoi que ce soit dans ce dépôt : elle n'était que *déclarée*. Utile pour dn3-2 (barre heure/date sans réseau) |
| **`0x5D`** | GT911 — tactile | connu depuis dn1-4 |
| **`0x6B`** | **QMI8658 — IMU** | ✅ **et c'est `0x6B`, pas `0x6A`.** `dn_pins.h` annonçait « 0x6A/0x6B » ; c'est tranché |

⇒ **Les deux témoins positifs du scan sont `0x20` et `0x5D`.** La commande conclut elle-même sur
leur présence : un scan qui ne les voit pas de manière stable est un **instrument cassé**, et
aucune conclusion sur un composant neuf n'est alors recevable.

---

## 13.4 Le breakout BME680 — inventaire

| | |
|---|---|
| Type | breakout violet **6 broches**, capteur Bosch en boîtier métallique visible |
| Sérigraphie des broches | `VCC  GND  SCL  SDA  SDO  CS` |
| Barrette | ⚠️ **FOURNIE NON SOUDÉE** — trous métallisés nus, barrette libre |
| Interfaces | I²C **et** SPI (d'où `SDO` et `CS` exposés) |

⚠️ **L'ordre du breakout et celui du câble sont EN MIROIR sur les deux premières broches** :

```
câble carte  :  GND   3V3   SDA   SCL
breakout     :  VCC   GND   SCL   SDA
```

Poser les fils « dans l'ordre », premier avec premier, **inverse l'alimentation ET croise les
signaux**. C'est le piège le plus coûteux de ce câblage, et il n'est signalé nulle part ailleurs.

**Niveaux mesurés au multimètre, carte allumée, pointe noire sur `GND` du breakout :**

| Broche | Mesuré | Ce que ça établit |
|---|---|---|
| `VCC` | **+3,3 V** | ✅ alimentation présente, **polarité correcte** |
| `SCL` | 3,3 V | repos haut — ⚠️ **ne prouve PAS la connexion**, voir ci-dessous |
| `SDA` | 3,3 V | idem |
| `CS` | **3,3 V** | ✅ **il y a un tirage** ⇒ la puce est en **mode I²C**, pas en SPI |
| `SDO` | **3,3 V** | ⇒ adresse attendue **`0x77`** (et non `0x76`) |

> ⚠️ **LES 3,3 V SUR `SDA`/`SCL` NE PROUVENT RIEN SUR LA CONNEXION — correction d'une conclusion
> tirée trop vite en séance.** Ces breakouts portent en général leurs **propres tirages** vers
> `VCC` sur les deux lignes : une broche totalement déconnectée afficherait **exactement** la même
> chose. Seule la **continuité**, ou la soudure, tranche. C'est le Trap n°2 commis une seconde
> fois dans la même séance, sur une autre mesure.

---

## 13.4 bis 🔴 LES TROIS BREAKOUTS DE `dn4-2` — inventaire, et **le 3ᵉ n'est PAS celui qu'on croyait**

**Relevé le 2026-08-19 sur les 9 photos de l'owner (§13.0), réfs lues sur la SÉRIGRAPHIE et sur
l'étiquette du sachet — ⛔ jamais déduites du bon de commande.**

| | **BH1750** | **ToF** | **INA219** |
|---|---|---|---|
| Réf lue sur la carte | `BH1750` · `V322` | 🔴 **`TOF050C-VL6180X`** | `INA219 DC Current Sensor` · `CJMCU` |
| Réf lue sur le sachet | *« GY-30 GY-302 BH1750fvi … Color: **GY-302** »* | *« **F2/ TOF050C-VL6180X** »* · *« Color: TOF050C-VL6180X »* | — |
| Brochage, **dans l'ordre physique** | `VCC · GND · SCL · SDA · **ADDR**` (5) | `VIN · GND · SDA · SCL · **INT** · **XSHUT**` (6) | `Vin+ · Vin- · Sda · Scl · Gnd · Vcc` (6) |
| Connecteur | barrette 5 broches, **NON SOUDÉE** | barrette 6 broches ×2 (droite + coudée), **NON SOUDÉES** | barrette 6 broches **+ bornier à vis 2 points**, **NON SOUDÉS** |
| Alimentation supportée | **3 V – 5 V** (sachet) | 3V3 (`VIN`) | **`VCC/LOGIC: 3~5V`** (verso) ✅ |
| Adresse par défaut | **`0x23`** | **`0x29`** (fixe) | **`0x40`** |
| Ce qui la sélectionne | broche **`ADDR`** : bas/flottant ⇒ `0x23` · haut ⇒ `0x5C` | ⛔ **rien** — fixe en dur ; reprogrammable **en RAM**, non persistant | cavaliers **`A0`/`A1`**, **NON PONTÉS À LA PHOTO** ⇒ `1000000` = `0x40` |
| Tirages `SDA`/`SCL` | ⛔ **NON LISIBLES** (§13.0, encart Y6) | ⛔ **NON LISIBLES** | ⛔ **NON LISIBLES** |
| Autre marquage utile | — | — | shunt **`R100`** = 0,1 Ω · `Bus Voltage 0~26V` · `Max Current 3.2A` |

> 🔴 **LE 3ᵉ CAPTEUR N'EST PAS UN VL53L0X. C'EST UN VL6180X — et *« même famille ToF »* est faux
> sur les trois points qui comptent.** L'addendum du brief (§3) avait pourtant **posé la question**
> le 2026-08-14 — *« La roadmap historique nomme "TOF050C" là où le dump dit VL53L0X — même famille
> ToF, noter la réf réelle du breakout à l'inventaire »* — et **personne ne l'avait fermée pendant
> cinq jours**. L'inventaire la ferme. Ce qui sépare les deux puces :
>
> | | **VL6180X** (ce qu'on a) | **VL53L0X** (ce que six documents annoncent) |
> |---|---|---|
> | Index de registre | **16 bits** (2 octets, MSB d'abord) | **8 bits** |
> | Registre d'identité | `0x0000` → **`0xB4`** | `0xC0`→`0xEE` · `0xC1`→`0xAA` · `0xC2`→`0x10` |
> | Portée **garantie** | 🔴 **100 mm** (*« ranging beyond 100 mm is possible … but not guaranteed »*) | ~2 m |
> | Bonus | **ALS intégré** (lumière ambiante) — recouvre partiellement le BH1750 | aucun |
>
> ⇒ **Le « 50 cm » de l'annonce revendeur n'est PAS une spec.** `dn4-3` hérite du **100 mm**, pas de
> l'annonce. ⚠️ Et se tromper de protocole, c'est passer une séance à chercher une mauvaise soudure
> sur un composant qui **répond parfaitement à un protocole qu'on ne lui parle pas**.

### 🔴 LE PIÈGE DU MIROIR SE RE-TEND SUR LES QUATRE — et l'INA219 est le pire

```
câble / embase carte  :  GND    3V3    SDA    SCL
BH1750  (GY-302)      :  VCC    GND    SCL    SDA    ADDR
ToF     (TOF050C)     :  VIN    GND    SDA    SCL    INT    XSHUT
INA219  (CJMCU)       :  Vin+   Vin-   Sda    Scl    Gnd    Vcc
BME680  (rappel §13.4):  VCC    GND    SCL    SDA    SDO    CS
```

⇒ **AUCUN des quatre ne s'aligne « premier avec premier » sur le câble.** Poser les fils dans
l'ordre **inverse l'alimentation sur les quatre**, et **croise `SDA`/`SCL` sur deux d'entre eux**
(BH1750 et BME680).

🔴 **ET L'INA219 EST LE PIRE DES QUATRE, POUR UNE RAISON QUI N'EST PAS UN SIMPLE MIROIR** : ses deux
premières broches sont **`Vin+` / `Vin-`**, c'est-à-dire **les bornes du SHUNT**, pas l'alimentation
logique. Un câblage « dans l'ordre » n'inverse pas seulement l'alimentation : il envoie le **3V3
directement sur un shunt de 0,1 Ω**. Son alimentation logique est à **l'autre bout** de la rangée
(`Gnd · Vcc`, broches 5 et 6).

### 🔴 DEUX MODES DE PANNE PROPRES À CES MODULES — nommés AVANT le fer

Ils produisent tous les deux **le symptôme exact de la mauvaise soudure** (« le capteur ne répond
pas »), et `dn2-1` a déjà dépensé **une séance entière** sur cette confusion (§13.5).

1. 🔴 **`XSHUT` du VL6180X est une ENTRÉE D'ACTIVATION.** Basse ou flottante, **la puce reste en
   shutdown et n'acquitte pas**. Certains breakouts la tirent au 3V3, d'autres non — ⛔ **cela ne se
   suppose pas, et la photo ne le dit pas**. ⇒ **Avant d'accuser la soudure : tirer `XSHUT` à 3V3 et
   rescanner.**
2. 🔴 **`ADDR` du BH1750 est une ENTRÉE DE SÉLECTION.** La datasheet ROHM ne définit `0x23` que pour
   **`ADDR ≤ 0,3 × VCC`** ; **flottant est INDÉFINI**. ⇒ **Décision : souder `ADDR` à `GND`** —
   une soudure pour une adresse déterministe. Le laisser en l'air, c'est accepter qu'une adresse
   instable ressemble un jour à un faux positif du scan (et §13.2 en fabrique une quinzaine).

⛔ **Et la séquence *bouger → scanner* ne peut structurellement pas converger** sur cette famille :
seule *bouger → **couper l'alimentation** → rescanner* est valable (§13.10, alimentation fantôme).

---

## 13.5 L'arbre de diagnostic — quatre hypothèses ÉLIMINÉES, deux vivantes

Le capteur n'a **jamais** répondu, ni à `0x76` ni à `0x77`, sur ~20 scans — pas même une fois à
`1/5`, alors que le bruit de sondage produisait une quinzaine d'adresses fantômes.

| # | Hypothèse | Statut | Ce qui l'a tranchée |
|---|---|---|---|
| 1 | **Câble JST inversé** (GND↔SCL) | ⛔ **ÉLIMINÉE** | SCL serait tiré à la masse ⇒ le bus mourrait. `0x20`/`0x5D` restent à `5/5` |
| 2 | **Alimentation inversée** | ⛔ **ÉLIMINÉE** | `+3,3 V` entre `VCC` et `GND`, polarité vérifiée par calibration du multimètre sur une référence connue (le `3V3`/`G` de la carte) |
| 3 | **Contact mécanique absent** (barrette non soudée) | ⛔ **ÉLIMINÉE POUR L'ALIMENTATION** | les 3,3 V au breakout exigent que `VCC` **et** `GND` conduisent |
| 4 | **`CS` flottant ⇒ mode SPI** | ⛔ **ÉLIMINÉE** | `CS` mesuré à 3,3 V (tirage présent). Un éventuel latch SPI a de plus été purgé par une **vraie coupure d'alimentation** (port USB disparu de l'hôte, donc pas un `reboot` déguisé) |
| 5 | **`SDA`/`SCL` croisés** | ⛔ **ÉLIMINÉE** | les deux orientations essayées ; le capteur a fini par répondre dans le câblage étiquette-contre-étiquette |
| 6 | **Les fils de signal n'arrivent pas** (trous non soudés côté `SDA`/`SCL`) | ✅ **CONFIRMÉE — C'ÉTAIT ELLE** | repositionnement manuel de la barrette + maintien à la main ⇒ `0x77` à **5/5 sur 8 scans**. ⚠️ Un **premier** test incliné (10 scans) n'avait RIEN donné : l'inclinaison ne garantit pas le contact, seul le constat visuel « toutes les pins touchent » a payé |
| 7 | **Puce morte, ou ce n'est pas un BME680** | ⛔ **ÉLIMINÉE** | `0xD0` = **0x61**, `0xF0` = **0x00** ⇒ **BME680 authentique** (pas un BME688, pas un BME280) |

> ✅ **VERDICT (2026-08-17)** : adresse **`0x77`** (conforme à la prédiction du tirage `SDO` haut),
> chip id **0x61**, variant **0x00**. Le chemin embase JST → GPIO15/GPIO7 est prouvé au passage —
> un composant répond à travers lui. **Il ne restait qu'un geste : SOUDER la barrette**, pour que le
> contact cesse d'être un geste d'owner et devienne une propriété du montage.
> ✅ **FAIT le 2026-08-17** — voir §13.6 bis, « Après SOUDURE » : deux blocs d'étalonnage identiques
> **octet pour octet** à ceux relevés avant, 10 lectures de registre sur 10. Le contact **est**
> désormais une propriété du montage.

⚠️ **PIÈGE DE MÉTHODE RELEVÉ EN SÉANCE, ET IL VAUT POUR TOUTE REPRISE** : sur cette famille de
capteurs, **un front descendant sur `CSB` bascule la puce en SPI jusqu'à la coupure d'alimentation
suivante**. Manipuler les fils **sous tension** peut donc re-armer la panne qu'on vient de purger.
⇒ La séquence *bouger → scanner* **ne peut structurellement pas converger** ; la seule valable est
*bouger → couper l'alimentation → rescanner*. Trois essais à l'aveugle ont été dépensés avant que
ce mécanisme soit nommé.

⚠️ **`reboot` en console NE COUPE PAS le capteur** : `esp_restart()` redémarre l'ESP32 sans couper
le rail 3V3. Une vraie coupure passe par l'**interrupteur `ON/OFF`** de la carte ou par le
débranchement USB — et se **vérifie** à la disparition de `/dev/ttyACM0` côté hôte.

---

## 13.6 La commande `i2c` — mode d'emploi

```
i2c                              scan 0x08..0x77, chaque trouvaille re-sondée 5 fois
i2c lire <addr> <reg> [n=1..16]  lecture registre (adresse et registre en HEXA)
```

- `i2c lire 77 D0` → **chip id**. `0x61` = BME680 **ou** BME688 · `0x60` = BME280 (pas de gaz) ·
  `0x58` = BMP280 (ni gaz ni humidité). La commande **interprète l'octet elle-même**.
- `i2c lire 77 F0` → **variant**. `0x00` = BME680 · `0x01` = BME688.
- ⛔ **Ne bloque pas seulement le REPL : sur la branche A, le REPL EST le transport PC.** Une
  trame d'agent attend dans le tampon USB pendant toute la durée du scan (~26 ms sain).
- ⚠️ **Le scan n'est PAS un test de §11.4.** Il dure ~26 ms, et une perturbation de 26 ms n'est
  pas observable à l'œil. Le vrai test de stabilité d'image est la **cadence de lecture en
  régime**, pas le scan.
- Premier `i2c_master_bus_add_device()` du dépôt — le TCA9554 et le GT911 passent tous deux par
  leur composant, qui le fait en interne. Le device est retiré sur **tous** les chemins de sortie.
- ⚠️ Le type est **`i2c_device_config_t`**, pas `i2c_master_dev_config_t` (qui n'existe pas). Le
  compilateur ne le dit qu'en aval, sur un « incompatible pointer type (`int *`) » qui envoie
  chercher au mauvais endroit.

**Coût DE CETTE ÉTAPE** : binaire **796 240 → 800 640 o** (+4 400 o) — *la commande `i2c` seule*.
Aucune ligne de `sdkconfig.defaults` touchée, et **à ce stade** aucun composant au manifeste.
⚠️ **Ces deux affirmations ne valent QUE pour ce point de la séance** (CR 2026-08-17) : elles se
lisaient comme un bilan de story, et contredisaient alors la §13.8 (**827 632 o**) et le manifeste,
où `k0i05/esp_bme680 ==1.2.7` **a bien été ajouté** au commit suivant. **Le bilan fait foi, pas
cette ligne d'étape.**

---

## 13.6 bis Le capteur est FONCTIONNEL, pas seulement présent

Un composant peut acquitter son adresse sans rien faire d'utile. Preuve qu'il n'en est rien —
ses **coefficients d'étalonnage d'usine**, gravés en NVM à la fabrication, lus le 2026-08-17 :

```
0x77 reg 0x89 (16 o) : 40 43 68 03 00 18 8A 92 D7 58 00 C7 1E 5C FF 1F
0x77 reg 0xE1 (16 o) : 42 4E 1E 00 2D 14 78 9C CD 66 9D D3 E6 12 E6 00
```

Données **variées et individualisées** — ni tout à `00`, ni tout à `FF`. Un composant fantôme ou
mort rendrait du vide. Et ce sont **deux transactions de 16 octets** qui passent sans faute : la
liaison porte des échanges multi-octets, pas seulement un bit d'acquittement.

**Non-régression du bus (début d'AC4)** : avec le 5ᵉ composant en place, `touch` relève
**0 erreur I²C sur 17 438 lectures** du GT911. ⚠️ Ce chiffre réfute au passage un
« TEMOIN POSITIF EN ECHEC » apparu sur une passe de scan (le tactile tombé sous 5/5) : c'était le
bruit de sondage documenté en §13.2, pas un décrochage réel. **Deux instruments indépendants, et
c'est le plus fiable qui tranche.**

⚠️ **Ce que ça ne prouve PAS** : la stabilité de l'image sous lecture en régime (§11.4), qui
demande l'œil de l'owner et une cadence réelle, pas des lectures ponctuelles.

### ✅ Après SOUDURE (2026-08-17) — et le scan seul aurait mal conclu

Barrette soudée, carte redémarrée sans incident (**pas de pont `VCC`/`GND`** : elle boote et `cfg`
répond). Six scans **sans les mains** :

| Passe | `0x77` |
|---|---|
| 1, 2, 3, 5, 6 | **5/5** |
| **4** | ⚠️ **ABSENT** (et un `0x76` parasite à 1/5 dans la même passe) |

**Le scan seul aurait donc laissé un doute sur la soudure.** Départagé par l'instrument fort — la
**lecture de registre**, qui est une vraie transaction et non un sondage :

```
8 × « i2c lire 77 D0 » → 61, 61, 61, 61, 61, 61, 61, 61      (8/8)
i2c lire 77 89 16 → 40 43 68 03 00 18 8A 92 D7 58 00 C7 1E 5C FF 1F
i2c lire 77 E1 16 → 42 4E 1E 00 2D 14 78 9C CD 66 9D D3 E6 12 E6 00
```

**10 lectures sur 10 réussies**, et les deux blocs d'étalonnage sont **identiques octet pour octet**
à ceux relevés AVANT la soudure. La soudure est bonne ; la passe 4 était du bruit de sondage.

> 🔴 **CARACTÉRISATION COMPLÉTÉE — `i2c_master_probe` produit aussi des FAUX NÉGATIFS.** La §13.2
> ne documentait que les faux positifs. Sur l'ensemble de la séance, **trois composants SOUDÉS ont
> raté une confirmation** : `0x6B` (IMU), `0x5D` (GT911) et `0x77` (BME680 après soudure), une fois
> chacun. ⇒ **`n/5 < 5` ne prouve rien dans un sens comme dans l'autre.** Le sondage sert à
> DÉCOUVRIR ; **seule la lecture de registre QUALIFIE**. Écrire l'inverse aurait fait rejeter une
> soudure correcte.

**Non-régression après soudure** : `touch` = **0 erreur I²C sur 2 663 lectures** · RAM interne
**113 847 o** (T0 : 113 871) · PSRAM **7 768 448 o** — variations dans le bruit d'allocation.

## 13.6 quater 🔴 L'INSTRUMENT NE QUALIFIE QU'**UN** CAPTEUR SUR TROIS — critères d'extension écrits AVANT le code (`dn4-2`, 2026-08-19 ~18h20)

### Le fait, établi aux datasheets et dans le code — ⛔ ce n'est pas une opinion de conception

`i2c lire <addr> <reg> [n]` fait, à `dn_console.c:4330` :
`i2c_master_transmit_receive(dev, &reg, **1**, rx, n, 200)` — **il ÉCRIT un octet d'index, puis
lit**. Conséquences, chacune vérifiée à la datasheet :

| | **BH1750** `0x23` | **VL6180X** `0x29` | **INA219** `0x40` |
|---|---|---|---|
| Adressage de registre | 🔴 **AUCUN** — machine à **OPCODES** | 🔴 **16 bits** (2 o, MSB d'abord) | ✅ **8 bits** |
| Registre d'identité | 🔴 **inexistant** | `0x0000` `IDENTIFICATION__MODEL_ID` → **`0xB4`** | `0x00` Configuration, reset = **`0x399F`** |
| **`i2c lire` le qualifie-t-il ?** | ⛔ **NON — et pire : il le PILOTE au hasard** | ⛔ **NON — violation de protocole** | ✅ **OUI** : `i2c lire 40 00 2` → `39 9F` |

- 🔴 **BH1750** — l'octet « registre » **EST une commande**. `i2c lire 23 00` le met en **power
  down**, `i2c lire 23 07` **reset** son registre de données, `0x08..0x0F` sont **INDÉFINIS**, et
  `0x40..0x7F` reprogramment le `MTreg`. ⇒ **Utiliser `i2c lire` sur le BH1750 ne le qualifie pas :
  ça le pilote au hasard**, et les 2 octets rendus seraient lus comme une identité alors que ce sont
  des **lux**. *(Jeu d'opcodes utile : `0x01` power on · `0x10` continu H-res — **120 ms typiques,
  jusqu'à 180 ms** · `0x20` one-shot H-res · `0x00` power down · `0x07` reset. Conversion :
  **`lux = brut / 1,2`** au `MTreg` par défaut de 69.)*
- 🔴 **VL6180X** — l'index fait **deux octets**. Envoyer **un** octet puis un restart-read est une
  **violation de protocole** : le résultat n'est ni `0xB4` ni reproductible. ⇒ l'instrument ne peut
  pas le qualifier, et **un échec ici ressemblerait EXACTEMENT à une mauvaise soudure** — la
  confusion qui a coûté une séance entière à `dn2-1` (§13.5).
- ✅ **INA219** — registres 16 bits **derrière un index 8 bits** : `i2c lire 40 00 2` rend les deux
  octets du registre Configuration, **`39 9F`** au reset (TI **SBOS448G** §8.6.2.1). Contrôle
  négatif gratuit dans la même foulée : `05` (Calibration) doit rendre **`00 00`**.

### Les CINQ critères d'arbitrage, posés avant d'ouvrir le code

1. 🔴 **Compatibilité avec le bus EXISTANT — ÉLIMINATOIRE.** ⛔ Jamais `i2c_new_master_bus()` sur
   `I2C_NUM_0` (rend `ESP_ERR_INVALID_STATE`). Le handle se demande à `dn_display_i2c_bus()`.
2. **Le device temporaire est retiré sur TOUS les chemins de sortie** — patron de
   `i2c_lire_registre()` (`:4304-4360`) et de `relever_identite()` (`dn_capteurs.c:378-398`).
3. **Coût en binaire mesuré** ; ⛔ **ZÉRO coût en régime** : aucune tâche, aucun timer, aucune
   allocation permanente, aucune boucle, aucun `vTaskDelay` — **le REPL EST le transport PC**.
4. **Refus expliqués, bornes annoncées ET tenues** (`parse_*`, ⛔ `atoi` interdit, ⛔ jamais
   d'écrêtage silencieux).
5. **`aide` fait foi** : toute sous-commande neuve entre dans `k_cmds[]` **et** dans la liste
   « Jeu complet » du `README.md`, **dans le même geste**.

### Les TROIS primitives que les datasheets imposent, et pourquoi elles manquent

| Primitive retenue | Pourquoi elle manque aujourd'hui | Qui en a besoin |
|---|---|---|
| `i2c ecrire <addr> <o1> [o2..o8]` — **écriture NUE**, aucune lecture | `i2c lire` **lit toujours** ⇒ impossible d'envoyer un opcode sans lire | **BH1750** (`01` power on, `10` mode continu) |
| `i2c brut <addr> [n]` — **lecture SANS index** | `i2c lire` **écrit toujours** un index ⇒ chaque lecture **repiloterait** le BH1750 | **BH1750** (2 o de mesure) |
| `i2c lire16 <addr> <reg16> [n]` — **index sur 2 octets** | `transmit_receive` n'envoie **qu'un** octet | **VL6180X** (`0x0000` → `0xB4`) |

⛔ **Ne PAS surcharger `i2c lire` d'un drapeau** : elle **interprète déjà l'octet elle-même** pour le
BME680 (`0xD0` → chip id, `0xF0` → variant, en dur). Deux sémantiques d'index dans une même commande
est exactement l'ambiguïté qui produit un chiffre **faux ET plausible**.

⚠️ **`i2c ecrire` PEUT CASSER UN COMPOSANT SAIN** (`00` = power down du BH1750, `07` = reset) ⇒ la
sortie **dit ce qu'elle a envoyé**, et l'aide porte l'avertissement.

### 🔴 LE TÉMOIN POSITIF : l'instrument est prouvé sur du CONNU avant de servir sur de l'INCONNU

Le dépôt a une cible parfaite — les blocs d'étalonnage du BME680, relevés **deux fois** en `dn2-1`
et **identiques octet pour octet** :

```
i2c lire 77 89 16 → 40 43 68 03 00 18 8A 92 D7 58 00 C7 1E 5C FF 1F
i2c lire 77 E1 16 → 42 4E 1E 00 2D 14 78 9C CD 66 9D D3 E6 12 E6 00
i2c lire 77 D0    → 61   (chip id)
```

⇒ **Toute primitive neuve doit reproduire ces octets sur un composant DÉJÀ SOUDÉ, AVANT qu'on lui
fasse dire quoi que ce soit sur un composant neuf.** ⛔ *Un instrument neuf non prouvé sur du connu
est exactement l'étiquette qui ment que ce dépôt traque.*

**Budget d'essais annoncé** : **3 variantes** d'implémentation maximum, puis on consigne et on
bascule sur le repli (qualification **par stimulus physique**, §AC6), avec l'écart écrit.

---

## 13.6 ter L'arbitrage du driver (AC5) — critères écrits AVANT la mesure

**Les critères, posés avant d'ouvrir le moindre candidat :**

1. **Compatibilité avec le bus EXISTANT** — *éliminatoire*. `dn_display` possède l'unique bus de
   la carte ; un composant qui appelle `i2c_new_master_bus()` échoue (`ESP_ERR_INVALID_STATE`),
   et un composant sur le driver i2c **legacy** entre en conflit frontal.
2. Coût en **RAM interne** (114 123 o libres — le chiffre qui gouverne) et en **binaire**.
3. **Dépendances transitives** ajoutées au manifeste.
4. **Traçabilité de la compensation Bosch** (T/H) — formules non triviales, transcription
   risquée à la main.
5. **Blocage** : compatible avec la contrainte §6 (le REPL est le transport PC) ?
6. **Lisibilité** — combien de code étranger on adopte sans le relire.
7. **Ce que ça engage pour dn4-1** (3 capteurs de plus).

**Le critère 1 tranche à lui seul, et il élimine trois candidats sur quatre :**

| Candidat | Verdict | Fait éliminatoire |
|---|---|---|
| `espressif/bme680` | ⛔ **n'existe pas** | vérifié par appel direct à l'API du registre |
| `esp-idf-lib/bme680` 1.0.7 | ⛔ éliminé | dépend de `esp-idf-lib/i2cdev`, qui **installe le driver i2c LEGACY** sur le port |
| `francisduvivier/bme68x_sensorapi_espidf` 0.0.6 | ⛔ éliminé *en tant que composant* | dépend de `espressif/i2c_bus`, qui **crée le bus**. *(Le SensorAPI Bosch nu, lui, est transport-agnostique — c'est la porte de sortie si le retenu déçoit.)* |
| `espressif/bme690` 1.0.3~1 | ⛔ éliminé | autre puce **et** `espressif/i2c_bus` |
| ✅ **`k0i05/esp_bme680` 1.2.7** | **RETENU** | `bme680_init(i2c_master_bus_handle_t, …)` prend un bus **déjà créé** et fait lui-même le `i2c_master_bus_add_device` |

**Ce que la mesure a ajouté** (build du 2026-08-17, composant au manifeste, non encore appelé) :

- ✅ **Il compile proprement.** Le `CMakeLists.txt` exotique (`include` de `version.cmake` + bloc
  `dotnet-gitversion`) est bien **inerte** chez nous — le doute est levé par un build, pas par une
  lecture.
- Résolus : `k0i05/esp_bme680 1.2.7` + `k0i05/esp_type_utils 1.2.7` (une seule dépendance
  transitive, sans dépendance propre au-delà de l'IDF).
- Code compilé : `libk0i05__esp_bme680.a` **261 984 o**, `libk0i05__esp_type_utils.a` **48 268 o**
  — c'est un **plafond**, pas un coût.
- 🔴 **BINAIRE INCHANGÉ : 800 640 o avant, 800 640 o après.** Et il ne faut **PAS** publier « le
  composant coûte 0 o » : le linker élague simplement tout ce que personne n'appelle. **Le coût
  réel n'existera qu'une fois `dn_capteurs` écrit** — mesurer le poids d'un composant que rien
  n'appelle, c'est le Trap n°2 sous une troisième forme. Le chiffre est donc **à relever après
  T5**, et ce fichier le dira alors.

⚠️ **Ce que ce choix N'ENGAGE PAS** : les 3 capteurs de dn4-1. `k0i05` publie aussi `esp_bh1750`,
mais BH1750/VL53L0X/INA219 se ré-arbitrent chacun sur le même critère 1. **Rien n'oblige à rester
dans la même famille.**

**Ce qui renverserait la décision** : une compensation T/H fausse ou invérifiable (⇒ repli sur le
SensorAPI Bosch nu, transport-agnostique), un coût binaire disproportionné une fois lié, ou une
contrainte de blocage incompatible avec §6 (`bme680_get_data()` boucle jusqu'à **1 500 ms** — donc
**tâche dédiée obligatoire**, ⛔ jamais depuis le REPL ni depuis LVGL).

## 13.8 Les budgets avec les deux cases vivantes — la référence que dn3 dépensera

Firmware du 2026-08-17, `dn_capteurs` en régime (BME680 @ 0x77, cadence 5 s, gaz coupé).
Base = le relevé **post-soudure de la même session**, même instrument.

| Mesure | Base (post-soudure) | dn2-1 en régime | Delta |
|---|---:|---:|---|
| **RAM interne libre** | 113 847 o | **109 295 o** | **−4 552 o** (tâche 4096 + TCB + état driver) — même ordre que `dn_link` (−4 452) |
| PSRAM libre | 7 768 448 o | 7 768 412 o | −36 o, dans le bruit |
| Tas LVGL | 15 228 o (25 %) | **15 244 o (25 %)**, frag 1 % | **+16 o** — les deux tampons de texte, PAS des labels neufs (ils existaient depuis dn1-4) |
| **Binaire** | 800 640 o | **827 632 o** | 🔴 **+26 992 o** — *le coût réel de TOUT ce que T5/T6 ont lié*, celui que §13.6 ter refusait de publier à 0 |
| **CPU** (`cpu 30`) | 0,9 % | **1,2 %** | **+0,3 pt** pour DEUX cases à 5 s |
| `fps 15` | 37,40 Hz | **37,34 Hz (−0,18 %)** | dans la bande de bruit du dépôt (37,33-37,45) |
| Cycle de mesure | — | **26 ms** | mesuré, pas repris de la datasheet |
| Fiabilité | — | **62 lectures, 0 erreur** (i2c/donnée/bornes) | ~5 min de régime |

> 🔴 **CES CHIFFRES SONT PÉRIMÉS PAR LA REVUE DE CODE DU 2026-08-17 — À RE-RELEVER.**
> Elle a modifié **5 fichiers du firmware** (29 correctifs). Au build de revue, le binaire passe
> de 827 632 à **832 720 o (+5 088 o)** : re-tentative d'ouverture du driver, garde de verdict de
> configuration, discrimination `err_donnee`/`err_i2c` par la durée, re-tentative de poussée UI et
> son compteur, budget d'abandon du scan. **RAM, CPU et flush n'ont PAS été re-mesurés** — ils
> demandent la carte. ⇒ **Ne pas citer la RAM ni le CPU de ce tableau tant que la séance carte de
> validation des correctifs n'a pas eu lieu.** Le `+26 992 o` du coût de liaison, lui, reste
> l'ordre de grandeur juste.
>
> ⚠️ **Et l'étiquette du binaire est trop large, quel que soit le chiffre** (constat de la même
> revue) : ce delta contient `dn_capteurs.c/h`, les ~500 lignes de `cmd_capteurs`/`cmd_i2c` dans
> `dn_console.c` et les changements de `dn_ui` — **pas seulement le composant tiers**. AC10
> demandait le coût du driver **isolé** ; il ne l'est pas, et personne ne l'a mesuré séparément.

> ✅ **`cpu N` EST VALIDE ICI, ET C'EST UNE DIFFÉRENCE DE NATURE AVEC dn2-2.** La §12.6 a dû
> abandonner `cpu N` parce que le trafic passait par le REPL, que la commande bloque. **La tâche
> capteur, elle, ne passe pas par le REPL** : elle continue de mesurer et de redessiner pendant la
> fenêtre. L'instrument voit donc réellement le régime qu'il prétend mesurer.
> ⚠️ **En revanche, comparer ce +0,3 pt au +0,53 pt de dn2-2 demande de la prudence** : celui-là
> venait des compteurs **cumulés** (`cpu brut`), celui-ci d'une **fenêtre**. Le delta publié ici est
> interne à une seule session et un seul instrument (0,9 → 1,2 %) ; c'est à ce titre qu'il vaut.

> 🔴 **LE LEGS CHIFFRÉ POUR dn3-2 — ET LA RÉPONSE N'EST PAS CELLE QU'ON ATTENDAIT.**
> La question posée par dn2-2 était : *le coût suit-il le nombre de cases, ou le nombre de
> redessins par seconde ?* Les chiffres de flush tranchent :
>
> | Régime | Aire/cycle | Flushes/cycle | Copie |
> |---|---:|---:|---|
> | dn2-2 — **1** case @ 1 Hz | 4 611 px (1,50 %) | **1,0** | 245 µs |
> | dn2-1 — **2** cases @ 0,2 Hz | **9 581 px** | **2,0** | 257 µs/flush |
>
> **Deux cases coûtent exactement deux fois une case** — en aire (2,08×) **et en flushes**. Et
> elles les coûtent alors qu'elles sont **CÔTE À CÔTE SUR LA MÊME LIGNE** de la grille (idx 4 et 5) :
> LVGL n'a PAS fusionné leurs deux zones sales en un seul flush, alors qu'elles tiennent dans la
> même bande de 128 lignes du draw buffer.
> ⇒ **Extrapolation pour dn3-2 : six cases vivantes = ~6 flushes et ~28 700 px par cycle**, pas
> moins. Le coût suit **le nombre de CASES**, et la cadence ne fait que le multiplier. Si dn3-2
> veut payer moins, il devra **grouper l'invalidation** — et ça ne viendra pas tout seul.

## 13.9 L'auto-échauffement du chauffage gaz — MESURÉ (A/B du 2026-08-17)

**Protocole, écrit avant de mesurer** : trois phases, une seule variable (`capteurs gaz on|off`),
même cadence, même pièce, même capteur, échantillons toutes les 25 s.

| Phase | Gaz | Température | Humidité |
|---|---|---:|---:|
| **A** — ligne de base | coupé | **25,53 °C** *(25,5-25,6 · dispersion 0,1)* | **48,70 %** |
| **B** — régime chauffé | **ACTIF** | **25,72 °C** *(plateau)* | **46,06 %** *(encore en baisse)* |
| **C** — témoin négatif | coupé | **25,30 °C** *(plateau)* | ~47,1 % *(remontée en cours)* |

> 🔴 **SANS LA PHASE C, LE CHIFFRE PUBLIÉ AURAIT ÉTÉ FAUX D'UN FACTEUR 2.**
> B − A donne **+0,19 °C**. B − C donne **+0,42 °C**. Les deux sont des soustractions légitimes
> entre deux états réels — **et elles ne peuvent pas être vraies toutes les deux**. L'explication
> est dans la phase C elle-même : elle ne revient PAS à la ligne de base, elle atterrit **0,23 °C
> plus bas**. **La pièce a refroidi pendant l'expérience.** Un A/B sans retour à l'état initial
> aurait attribué au chauffage une dérive d'ambiance — ou l'inverse.
>
> **Correction de la dérive** (linéaire entre le milieu de A et le plateau de C, ~430 s) :
> à l'instant du plateau B, la température « gaz coupé » aurait valu ~25,43 °C.
> ⇒ **BIAIS DU CHAUFFAGE : ≈ +0,3 °C** · et sur l'humidité, même méthode : **≈ −2 points de RH**.

**✅ Les deux grandeurs bougent en SENS OPPOSÉS, comme prédit avant la mesure** : chauffer le die
fait monter la température lue et baisser l'humidité relative lue. Deux signaux corrélés en
opposition sont bien plus durs à confondre avec une dérive ambiante qu'un seul chiffre — c'est ce
qui rend l'attribution solide, en plus de la réversibilité.

> ⚠️ **UNE PRÉDICTION DE LA STORY EST DÉMENTIE, ET DANS LE BON SENS.** Le contexte annonçait un
> biais « de 1 à 3 °C », repris de la littérature communautaire. **Le mesuré est ~10× plus petit.**
> Le mécanisme est dans la cadence : 300 ms de chauffe toutes les **5 000 ms** = **6 % de rapport
> cyclique**. La cadence de 5 s, choisie pour la fidélité et le budget de redessin, **atténue déjà
> l'auto-échauffement** — les trois entrées de l'arbitrage de cadence n'étaient pas indépendantes,
> et personne ne l'avait vu. ⚠️ **Corollaire pour dn4-1** : une cadence à 1 Hz porterait le rapport
> cyclique à **30 %**, et le biais avec.

**✅ DÉCISION CONFIRMÉE PAR LA MESURE, PAS PAR LE RAISONNEMENT — le gaz reste COUPÉ**
(`DN_CAPT_GAZ_DEFAUT = false`) : il coûte ~0,3 °C et ~2 points de RH **sur les deux seules
grandeurs que la story livre**, pour une donnée (COV/IAQ) qui n'est dans **aucun** des six widgets
du brief. Payer un biais mesurable pour une valeur qu'on n'affiche pas n'a pas de contrepartie.

**Ce qui renverserait la décision** : un 7ᵉ widget « qualité d'air » (qui sortirait du brief), ou
une compensation du biais — laquelle exigerait de le caractériser en température ET en cadence,
soit une campagne à elle seule. ⚠️ **Et un offset ne se persiste PAS en NVS en régime (D4).**

⚠️ **Ce que cet A/B ne mesure PAS** : l'échauffement dû à la **proximité de la carte** (dalle RGB,
rétroéclairage, S3 à 240 MHz), qui est un tout autre terme.

> ✅ **ET CETTE QUESTION EST FERMÉE PAR DÉCISION OWNER (2026-08-17), PAS PAR UNE MESURE.**
> Le module sera **POSÉ À CÔTÉ de la tour**, pas monté dans la façade du Phantom 630 — verbatim :
> *« y aura pas de montage définitif dans le phantom, il sera posé à côté »*. Et l'owner assume
> explicitement que le capteur mesure la température **à l'endroit où il est** : *« c'est conscient
> que ça prend la temp au niveau du capteur donc c'est ok »*.
> ⇒ **Il n'y a donc rien à re-mesurer en dn4-1** sur ce point : pas de flux d'air chaud de boîtier,
> pas de support imprimé, pas de passage de câble interne. Le legs thermique que cette section
> annonçait est **annulé**.
> ⚠️ **Le README et le brief disent encore « monté sur la façade »** — c'est désormais faux et
> corrigé au README. Le **brief** relève d'un correct-course, pas d'une réécriture silencieuse.

## 13.10 🔴 LE CAPTEUR FANTÔME — le mode de panne que personne n'avait imaginé

**Le geste** : débrancher le fil `VCC` du breakout en marche, puis le rebrancher. C'est le témoin
que l'AC7 réclamait. **Il a trouvé bien autre chose que ce qu'il cherchait.**

### Ce qui s'est réellement passé

Au rebranchement, les cases ont affiché **32,8 °C et 100 %RH — en BLANC**, comme si c'était fiable.
Diagnostic par lecture directe des registres, pas par supposition :

```
0x72 (ctrl_hum)  : 00   →  suréchantillonnage humidité SKIPPED
0x74 (ctrl_meas) : 00   →  température et pression SKIPPED, mode SLEEP
0x75 (config)    : 00   →  filtre IIR OFF
```

**La coupure a remis le BME680 à ses défauts d'usine.** La compensation Bosch, alimentée par des
ADC non configurés, produit alors des nombres parfaitement plausibles et entièrement faux.

### 🔴 Et débrancher `VCC` NE COUPE PAS le capteur — alimentation fantôme

Fil `VCC` retiré, le scan le voit toujours : **`0x77` à `5/5`**. Il est alimenté **parasitairement
par les tirages du bus, à travers ses diodes de protection ESD sur `SDA`/`SCL`** — sa consommation
en sommeil est de l'ordre du microampère, les pull-ups suffisent largement. Il a assez de tension
pour acquitter en I²C, **pas assez pour tenir sa configuration ni faire tourner son étage
analogique** (la reconfiguration échouait en boucle tant que le vrai 3,3 V n'était pas revenu).

⇒ **Il existe TROIS états, pas deux** :

| État | Sur le bus | Valeurs | Qui le voit |
|---|---|---|---|
| sain | présent | justes | — |
| **absent** | disparaît du scan | aucune | tout le monde |
| 🔴 **fantôme** | **présent, bavard, `5/5`** | **fausses ET plausibles** | **personne, avant ce correctif** |

### Pourquoi aucune garde existante ne pouvait l'attraper

- **Pas une erreur de transport** — le capteur répond parfaitement (`err_i2c` = 1, la seule
  transaction tombée pendant la coupure) ;
- **Pas une valeur aberrante** — 32,8 °C et 100 %RH sont dans les bornes physiques du composant ;
- **Pas un silence** — l'état restait `VIVANT`, la péremption ne se déclenchait jamais.

**L'AC7 protège contre « le capteur se tait et la case fige une valeur périmée ». Le vrai mode de
panne est « le capteur répond avec du n'importe quoi ».** Il fallait le geste physique pour le
faire apparaître ; aucune revue de code ne l'aurait deviné.

### Le correctif : l'ombre logicielle cesse de faire autorité

La configuration est **relue dans le capteur à chaque cycle** et comparée à celle que l'init y a
**constatée** (et non à celle qu'on croit avoir demandée). Non conforme ⇒ la valeur est
**invalidée** (les cases passent à `--`), le capteur est **reconfiguré**, et l'événement va dans
son **propre compteur** — ni transport, ni bornes, ni silence.

⚠️ **`capteurs` affichait `FORCED · T/H 8x · P 1x · IIR 3` pendant que le capteur était à `00`
partout.** C'est l'étiquette-qui-ment que ce dépôt traque depuis dn1-3, et la règle existait déjà
à côté : `dn_display_backlight_pct_state` ne suit le matériel qu'**après confirmation**. La console
imprime désormais les **octets relus**, et signale l'écart.

### Ce que le témoin a donné, une fois le correctif posé

| Phase | Constat |
|---|---|
| Débranché | état **MUET**, âge qui grimpe (35 → 60 s), `config LUE 🔴 NON CONFORME`, **cases à `--` grisé** *(constat owner)* |
| Rebranché | reconfiguration **réussie**, `config LUE (conforme)`, valeurs **plausibles** (26,6 → 26,3 °C en convergeant), **`reprises : 1`** |

Recoupement complet : **1** erreur i2c (la transaction de la coupure), **1** reconfiguration,
**1** reprise. Aucun compteur en trop, aucun manquant.

### 🔴 Deux défauts de plus, trouvés dans les correctifs eux-mêmes

1. **`reprises` restait à 0** alors que la reprise était visible à l'écran. Cause : l'invalidation
   efface l'horodatage, donc l'état tombait à `JAMAIS` et non à `MUET` — et la détection de reprise
   s'appuyait dessus. **Le code de réparation aveuglait le compteur censé prouver qu'il répare.**
   Corrigé par deux drapeaux indépendants de l'horodatage.
2. **La console imprimait `0,1 C · 0,-1 %`** : sa garde d'affichage portait sur l'ÉTAT
   (`!= JAMAIS`). Le jour où `MUET` a cessé d'être synonyme de « valeur présente », la sentinelle
   `-1` s'est retrouvée **formatée comme une mesure**. La garde porte désormais sur la **valeur**.
   ⚠️ Défaut introduit par le correctif précédent, à une ligne de distance — et attrapé par le
   smoke, pas par la relecture.

## 13.11 L'injecteur de fautes — pour ne plus toucher au connecteur

**Contrainte owner du 2026-08-17** : *« les pin ne sont pas faites pour être enlevées et remises
sans arrêt, ça assouplit la connectique »*. C'est exact — un Dupont est donné pour quelques
dizaines d'insertions, et rejouer l'AC7 à la main **dégrade le montage qu'on prétend éprouver**.

`capteurs simuler muet|bornes|config <cycles>` arme une faute qui emprunte **exactement les chemins
d'erreur réels**, compteurs compris.

**Validé contre la vraie panne** : la faute `config` produit la **même signature de compteurs** que
le débranchement physique (`reprises` +1, `reconfigurations` +1, cases à `--`, retour à des valeurs
justes). Smoke des trois causes rejoué le 2026-08-17.

Deux garanties de conception, parce qu'un injecteur qui ment est pire que pas d'injecteur :

- il **ne falsifie que le VERDICT**, jamais la lecture — `capteurs` continue d'imprimer les octets
  réels des registres, si bien qu'on voit `0x72=04 · 0x74=84 · 0x75=08 🔴 NON CONFORME` et qu'on
  comprend immédiatement qu'on regarde une simulation ;
- il **s'annonce** : `🔴 FAUTE SIMULEE ACTIVE … AUCUN chiffre releve maintenant n'est un chiffre
  REEL`, avec les cycles restants.

> ⚠️ **CE QU'IL NE PROUVE PAS, ET QUI DOIT RESTER ÉCRIT** : il teste le **chemin de code**, pas le
> matériel. **Il ne peut pas découvrir un mode de panne qu'on n'a pas imaginé** — l'alimentation
> fantôme par les diodes ESD, personne ne l'aurait injectée parce que personne ne la soupçonnait.
> Il vaut pour la **non-régression**, *après* qu'une campagne physique a établi la liste des fautes
> réelles. Cette liste a été établie le 2026-08-17, et elle a coûté trois défauts.

## 13.7 Ce que la séance laisse — et ce qu'elle a fermé

**Fermé, par la mesure :**

- **Le capteur** : BME680 authentique, vivant, à **`0x77`** (`dn_pins.h` porte l'adresse et son
  constat). Le témoin négatif est naturel et surabondant : ~30 scans sans contact = adresse
  absente ; contact rétabli = `5/5` sur 8 passes.
- **Le chemin complet** embase JST → câble → barrette → puce : prouvé de bout en bout.
- **Le brochage du connecteur**, les 4 occupants internes du bus, l'instrument `i2c` et son
  défaut de faux positifs corrigé.

- **Le driver** : `k0i05/esp_bme680 == 1.2.7` épinglé au manifeste, il compile (§13.6 ter).

- **La barrette est SOUDÉE** (§13.6 bis) : le contact est une propriété du montage, plus un geste.
- **Le module** `dn_capteurs` : tâche dédiée, cadence raisonnée, état + péremption, compteurs par
  cause, garde de reconfiguration, injecteur de fautes.
- **Les cases** `TEMP.` et `HUMIDITE` vivent, constatées à l'œil, **image stable** sous rafales I²C.
- **Les budgets** (§13.8) et **l'A/B du chauffage** (§13.9).
- **Le mode de panne « capteur fantôme »** (§13.10), que rien n'avait anticipé.

**Ce qui reste, et à qui :**

1. **dn4-1** — les 3 autres breakouts (BH1750 `0x23`, VL53L0X `0x29`, INA219 `0x40`) : **ni
   inventoriés ni branchés**, une variable à la fois (décision owner **D2-1a**). Ils se
   ré-arbitrent chacun sur le critère 1 de §13.6 ter (compatibilité avec le bus existant) —
   **rien n'oblige à rester chez `k0i05`**. ⚠️ Et ils feront une **campagne physique** : l'injecteur
   de §13.11 ne découvre pas les modes de panne qu'on n'a pas imaginés.
2. **dn3-1 / dn3-2** — la vue **détail** de `TEMP.`/`HUMIDITE` reste **factice** (comme celle de
   CPU depuis dn2-2, décision owner R1) ; le legs de flush de §13.8 ; et la **fusion des deux cases
   en une « Ambiance »** demandée par l'owner le 2026-08-17, qui libère une 6ᵉ place — **à cadrer
   en correct-course**, c'est un changement de brief.
3. **Correct-course** — l'affichage du **gaz**, qui renverse la décision mesurée de §13.9
   (+0,3 °C et −2 pts de RH) et bute sur deux défauts du composant tiers **plus** le fait que la
   résistance de gaz du BME680 est **relative** (ligne de base + rodage requis).

⚠️ **Ce que dn2-1 change pour dn4-1, en une ligne** : le bus porte désormais **5 occupants**, la
commande `i2c` en fait l'inventaire en une seconde, `dn_capteurs` est le patron à étendre, et la
RAM interne libre est passée de 113 847 à **109 295 o** (⚠️ chiffre d'avant la revue — voir §13.8).

---

## 13.12 🔴 CE QUE LA SÉANCE N'A PAS MESURÉ — quatre trous nommés (revue de code, 2026-08-17)

Quatre mesures **exigées par des AC** étaient cochées sans avoir été faites. Aucune ne se répare au
clavier : elles demandent la carte. **Décision owner : elles se soldent à la séance de validation
des correctifs de la revue** — celle qui re-flashe de toute façon.

Elles sont écrites ici, dans le fichier de mesure, parce qu'un trou de mesure qui ne vit que dans
une story se perd à la story suivante.

| # | Ce qui manque | Exigé par | Pourquoi ça compte |
|---:|---|---|---|
| 1 | Les **compteurs d'erreurs I²C de `touch` relevés AVANT et APRÈS un scan** | **AC3** | Le fichier ne publie que des relevés **isolés** (0 erreur / 17 438, puis / 2 663). Sans le couple encadrant, **un scan qui induirait des erreurs sur le tactile serait invisible** — c'est l'AC qui le dit : *« sans ces deux relevés on ne le verrait pas »* |
| 2 | Le **nombre de transactions I²C par cycle de lecture** | **AC6** | Seule la **durée** (26 ms) est publiée. L'AC demande le nombre **compté**, pas estimé : c'est ce qui dimensionne la charge que dn4-1 va multiplier par 4 |
| 3 | Le **re-test du tactile juste après le débranchement à chaud**, et le **délai de reprise chiffré** | **AC7** | §13.10 décrit le geste et le mode fantôme, mais **ne mentionne pas le GT911** ; le tableau chiffre l'âge en MUET (35 → 60 s), pas la reprise. Or l'AC nomme le risque : perturber le bus peut fâcher le tactile |
| 4 | Un **second point de comparaison thermique** (thermomètre, station météo, téléphone) | **AC9** | Ni cherché, ni déclaré absent. ⚠️ **L'AC prévoyait explicitement le cas « aucun »** — *« s'il n'y en a aucun, c'est écrit comme tel »*. Sans lui, l'A/B de §13.9 mesure un **delta** juste, mais rien ne dit que la **valeur absolue** l'est |

⚠️ **Le point 4 est le plus important des quatre** : §13.9 établit très bien que le chauffage gaz
coûte +0,3 °C — c'est un delta interne, chaque phase étant mesurée par le même capteur. **Il
n'établit rien sur la justesse de la température affichée.** Un biais constant de 2 °C passerait
entièrement à travers cette expérience, et c'est le livrable de la story.

---

## 13.13 ✅ SÉANCE DE VALIDATION DES CORRECTIFS (2026-08-17, firmware `b554a4e-dirty`)

Séance `/desknode-board` qui valide les **29 correctifs** de la revue de code et solde **3 des 4
trous** de la §13.12. Binaire **832 720 o** (`0xcb2d0`), arbre non committé au moment des mesures —
**le bandeau de boot porte `App version: b554a4e-dirty`**, ce qui les rend rattachables au commit
qui a suivi.

### 13.13.1 Non-régression : le smoke passe 6/6

Constats owner à l'œil, firmware corrigé : dashboard plein écran · rétroéclairage **fixe** ·
cases `TEMP.`/`HUMIDITE` **vivantes avec le `°`** · 🔴 **IMAGE STABLE** · case CPU à `--` grisé
(agent absent, état honnête) · aller-retour au doigt **OK**. Aucune ligne d'erreur nouvelle au
bandeau ; la ligne `E gpio_install_isr_service already installed` reste **antérieure**.

🔴 **Le correctif n°1 est confirmé PAR L'ŒIL** : après reboot, les cases affichent **« -- » grisé
pendant ~5 s** avant la première valeur. Avant correctif elles étaient **VIDES** — l'initialiseur
`= "--"` avait été perdu en généralisant `s_cpu_texte` en `s_vive_texte[]`, et le défaut devenait
**permanent** si le capteur ne répondait pas au boot, pendant que deux fichiers journalisaient
« les cases resteront « -- » ».

### 13.13.2 ✅ AC3 SOLDÉ — le scan n'induit AUCUNE erreur sur le tactile

Le couple de relevés qui manquait, joué **deux fois** (avant et après le flash des correctifs) :

| Firmware | GT911 avant scan | GT911 après scan | erreurs I²C induites |
|---|---:|---:|---|
| `b554a4e` (avant correctifs) | 279 598 lectures, **0 err** | 279 604 lectures, **0 err** | **0** |
| `b554a4e-dirty` (corrigé) | 13 979 lectures, **0 err** | 13 985 lectures, **0 err** | **0** |

Scan mesuré à **28-32 ms**, témoin positif OK (`0x20` et `0x5D` à 5/5). La passe sur l'ancien
firmware a sorti **deux faux positifs à 1/5** (`0x17`, `0x54`), jamais reproduits — signature
exacte de §13.2 ; la passe sur le firmware corrigé n'en a sorti **aucun**.

### 13.13.3 ✅ AC6 SOLDÉ — 7 transactions I²C par cycle, COMPTÉES et réconciliées

Chaque transaction identifiée dans le source du composant, pas estimée :

| # | Transaction | Origine | Délai qui suit |
|---:|---|---|---:|
| 1 | lecture `0x74` (ctrl_meas) | `bme680_set_power_mode` → `get_control_measurement_register` | 5 ms |
| 2 | écriture `0x74` (FORCED) | `bme680_set_power_mode` → `set_control_measurement_register` | 5 ms |
| 3 | lecture `0x1D` (status0) | boucle « data ready », **1 seule itération** | 5 + 1 ms |
| 4 | lecture rafale `0x1F`, 13 o | `bme680_i2c_read_from(REG_PRESS)` | 5 ms |
| — | | `bme680_get_data`, sortie | 5 ms |
| 5-7 | lectures `0x72` · `0x74` · `0x75` | **notre** garde de configuration (§13.10) | — |

**4 transactions du driver + 3 de la garde = 7 par cycle.**
**Somme des délais du driver : 26 ms — contre 25-26 ms MESURÉS.** Le compte n'est donc pas une
lecture de source qu'on croit sur parole : il se réconcilie avec la durée à **1 ms près**.
⚠️ `CONFIG_FREERTOS_HZ=1000` : les `pdMS_TO_TICKS` du composant sont des délais réels, pas des
arrondis à zéro. Le compte en dépend.

> 🔴 **CE QUE LA RÉCONCILIATION RÉVÈLE, ET QUE PERSONNE N'AVAIT VU : L'AFFICHAGE A UN CYCLE DE
> RETARD.** La boucle « data ready » sort à la **première** itération. Or la conversion 8×/8×/1×
> demande **~41 ms** (datasheet). Si la boucle l'attendait, le cycle mesurerait ≥ 41 ms, pas 25.
> ⇒ **la valeur lue à chaque cycle est celle de la conversion déclenchée au cycle PRÉCÉDENT**,
> soit **5 secondes de retard** à la cadence actuelle.
>
> ✅ **TÉMOIN POSITIF, et il est décisif** : `capteurs gaz on` ajoute **300 ms** de chauffe à la
> conversion. Le cycle est resté à **26 ms**, identique en gaz ON et OFF, sur 4 relevés — alors que
> la température dérivait de **26,0 → 26,2 °C**, ce qui **prouve que le chauffeur tournait**. Un
> témoin négatif dont le stimulus n'est pas prouvé ne vaut rien ; celui-ci a le sien.
>
> ⚠️ **Anodin pour une pièce à 5 s, PAS anodin pour dn4-1** qui touchera à la cadence : à 1 Hz, on
> afficherait une mesure vieille d'une seconde tout en croyant lire l'instant. Et le vrai correctif,
> si un jour il faut la fraîcheur, n'est pas d'attendre la conversion (ça bloquerait la tâche 41 ms)
> mais de **déclencher au cycle N et lire au cycle N+1 en connaissance de cause**.

### 13.13.4 ✅ AC7 (b) SOLDÉ — délai de reprise chiffré, sans toucher au connecteur

Joué à l'injecteur (`capteurs simuler muet 5`), donc **sans user la connectique** — c'est
exactement ce pour quoi il a été écrit :

| t | état | `err_i2c` | `reprises` |
|---:|---|---:|---:|
| +3 → +12 s | VIVANT, âge croissant | 1 → 2 | 0 |
| **+15,6 s** | 🔴 **MUET** (âge 16 363 ms) | 3 | 0 |
| +25 s | MUET, fin d'injection | **5** | 0 |
| **+31,2 s** | ✅ **VIVANT**, âge 1 942 ms | 5 | **1** |

- **Péremption à 15 000 ms pile** — bascule entre âge 13 218 et 16 363 ms, soit les 3 cycles annoncés.
- **5 cycles armés = 5 incréments de `err_i2c`** : l'injecteur ne dérive pas d'un cycle.
- **Délai de reprise ≈ 4,3 s** — la première lecture valide qui suit la fin de la panne, donc
  **borné par la cadence (≤ 5 s)**, et `reprises` passe bien à 1.

### 13.13.5 🔴 AC9 SOLDÉ — et l'humidité CORROBORE la température par un chemin indépendant

**Deux thermomètres de la pièce** (grand public, non étalonnés), relevés simultanément, ⚠️ **avec
une climatisation mobile en marche — la pièce n'est donc pas homogène** :

| Sonde | Position | Lecture |
|---|---|---|
| Réf. 1 | **50 cm** du capteur | **24,0 °C · 53 %** |
| Réf. 2 | **1,5 m** du capteur | **25,0 °C** |
| **BME680** | sur ses fils, écarté de la carte | **25,9 °C · 47,1 %** |

- Écart carte − réf. 50 cm : **+1,9 °C** · carte − réf. 1,5 m : **+0,9 °C**
- **Gradient propre de la pièce : 1,0 °C sur ~1 m** — c'est le plancher d'incertitude, pas du bruit.

🔴 **Le test qui tranche, et il ne coûte rien** : la pression de vapeur de l'air, prise sur la
référence (24,0 °C à 53 %), vaut **15,78 hPa** (Magnus). **Ce même air, à 25,9 °C, doit lire
47,3 %RH.** Le BME680 lit **47,1 %** — **écart 0,22 point**.

| Hypothèse | Ce qu'elle prédit pour l'humidité | Observé |
|---|---|---|
| **Biais d'étalonnage** (die à 24 °C, annonce 25,9) | l'élément baigne dans 53 % ⇒ il lirait **~53 %** | ❌ |
| **Température locale RÉELLE** (die à 25,9 °C) | même air, plus chaud ⇒ **47,3 %** | ✅ **47,1 %** |

⇒ **Le +1,9 °C n'est PAS une erreur du capteur : l'élément sensible est réellement dans de l'air
plus chaud.** C'est l'auto-échauffement / la proximité de la carte du §10.2 — la question que la
story léguait à dn4-1 **sans jamais la chiffrer**. Elle a maintenant un premier nombre, et une
méthode pour la re-mesurer.

⚠️ **CE QUE ÇA N'ÉTABLIT PAS, et qui doit rester écrit** : les deux sondes sont **non étalonnées**
(±1 °C typique pour du grand public), leur propre écart est de 1,0 °C, et la clim rend la pièce
**non stationnaire** — c'est un instantané simultané, pas une série temporelle. **La justesse
absolue du BME680 n'est donc pas établie à mieux que ~±1 °C.** Ce qui EST établi : la **cohérence
interne** de son couple T/RH (0,22 point) et le **sens et l'ordre de grandeur** de l'écart.

### 13.13.6 ⏭️ AC7 (a) — le seul trou qui RESTE, et il est déclaré

**Le tactile n'a PAS été re-testé après une perturbation ÉLECTRIQUE du bus** (débranchement à
chaud du 3V3). **Motif, décision owner du 2026-08-17 : on ne touche plus aux Dupont** — un
connecteur n'est donné que pour quelques dizaines d'insertions, et le dégrader pour tester sa
robustesse est un mauvais échange. ⚠️ **L'injecteur ne peut PAS s'y substituer : il exerce le
chemin de code, jamais le bus.** C'est un écart **écrit**, pas contourné.

**Ce qui EST acquis sur la robustesse du bus, et qui est substantiel :**

| Preuve | Résultat |
|---|---|
| ~2 h 45 de régime continu, 5ᵉ device sur le bus | **0 erreur I²C / 279 604 lectures** GT911 |
| Encadrement d'un scan (les deux firmwares) | **0 erreur induite**, deux fois |
| Aller-retour au doigt **pendant** la lecture capteur en régime | **OK** (constat owner) |

**Ce qui manquerait encore** : le tactile actif **pendant** une perturbation. Une variante
entièrement logicielle existe (saturer le bus de scans en rafale pendant des appuis) et **ne
présente aucun risque électrique ni thermique** — un scan n'est que du trafic à 400 kHz, sans
écriture de donnée, sur une plage bornée à `0x08..0x77` qui exclut les adresses réservées. Elle a
été **écartée par l'owner**, l'information marginale étant faible au regard de ce qui précède.
⇒ **À rejouer en dn4-1**, où les 4 capteurs sur le bus rendront la question réellement neuve.

### 13.13.7 Budgets RE-RELEVÉS — ceux de §13.8 sont remplacés

| Mesure | dn2-1 (périmé) | **Séance de validation** | Delta |
|---|---:|---:|---|
| Binaire | 827 632 o | **832 720 o** | **+5 088 o** (29 correctifs) |
| RAM interne libre | 109 295 o | **109 287 o** | −8 o — **bruit** : les correctifs ne coûtent RIEN en RAM |
| PSRAM libre | 7 768 412 o | 7 768 360 o | −52 o, bruit |
| Tas LVGL | 15 244 o (25 %) | **15 228 o (25 %)**, frag **1 %** | −16 o, bruit d'allocation de texte |
| CPU (`cpu 30`) | 1,2 % | **1,3 %** | +0,1 pt (repos de référence : 0,9 %) |
| `fps 15` | 37,34 Hz (−0,18 %) | **37,40 Hz, écart +0,00 %** | ✅ **pile la théorie** |
| `flush` en régime | 2,0 flush/cycle, 9 581 px | **2,0 flush/cycle, 9 049 px** | ✅ **le legs dn3-2 est CONFIRMÉ** |
| Cadence effective | non mesurée | **4 999 ms** entre deux lectures valides | `vTaskDelayUntil` ne dérive pas |
| Cycle de mesure | 25-26 ms | 25-26 ms | inchangé |

- **12 flushes pour 6 cycles sur 30 s** : la cadence de 5 s se retrouve exactement, et le rapport
  **2,0 flush par cycle** re-confirme que **LVGL ne fusionne pas** deux cases côte à côte.
  ⇒ le legs chiffré pour dn3-2 tient : **le coût suit le nombre de CASES**, pas la géométrie.
- ⚠️ `cpu N` reste **valide ici** (la tâche capteur ne passe pas par le REPL), mais le +0,1 pt est
  **dans le bruit** de l'instrument — ne pas en conclure que les correctifs coûtent du CPU.

### 13.13.8 Correctifs vérifiés à la console

| Correctif | Preuve observée |
|---|---|
| Cases à `--` avant la 1ʳᵉ lecture | ✅ **constat owner** au reboot, ~5 s |
| Cadence **effective** exposée (AC7) | `4999 ms MESURES entre les deux dernieres lectures valides` |
| Libellés de config venus du `.h`, plus d'un littéral console | `demande : FORCED · T/H 8x · P 1x · IIR 3` |
| Référence de config **testée** à l'init | `config relue dans le capteur : 0x72=04 0x74=84 0x75=08` |
| Étiquette `0x77` corrigée | `0x77 5/5 BME680 — … — L'ADRESSE MESUREE` |
| **`simuler config 1` n'est plus un no-op** | `reconfigurations` **0 → 1**, état MUET immédiat, puis `reprises` 1 → 2 |
| Sentinelle hors plage physique (`DN_CAPT_DX_ABSENT`) | `MUET — aucune valeur courante` au lieu de `0,1 C · 0,-1 %` |
| Durée minimale d'injection annoncée | `1 cycle(s) NE SUFFIT PAS … armer au moins 4 cycles` |
| Boot non retardé par la re-tentative d'ouverture | `prêt en 2190 ms` — **inchangé** |

---

## 13.14 🔴 LA STABILISATION DU DIE APRÈS EXTINCTION DU CHAUFFEUR — **D7 TOMBE** (dn3-2, 2026-08-18)

**Firmware `ea986ed`.** C'était le **prérequis BLOQUANT** de dn3-2 : dn2-1 (§13.9) avait mesuré le
**coût** du chauffeur (+0,3 °C, −2 pts RH), **jamais le temps de RETOUR**. Sans ce temps, D7 — « le
gaz à la demande, à l'ouverture de la page de détail Ambiance » — ne pouvait pas être décidé.

### Le critère, ÉCRIT AVANT LA MESURE

> **Retour à ≤ 0,1 °C de la ligne de base en ≤ 3 cycles capteur (15 s).**

Les deux nombres viennent d'ailleurs que de cette mesure, délibérément : **0,1 °C est la résolution
AFFICHÉE** par les cases, **15 s est déjà la constante de péremption** du module
(`DN_CAPT_PEREMPTION_US`). *« Les critères écrits avant la décision »* — sinon on trouve toujours la
mesure acceptable.

### Le protocole — TROIS phases, avec témoin de dérive de pièce

Sans la phase C, le chiffre de T9 (dn2-1) aurait été **faux d'un facteur 2**. On ne refait pas
l'erreur. Phases A (gaz OFF, 240 s) → B (gaz ON, 240 s) → C (gaz OFF, 360 s), échantillonnage
continu (~11 relevés/s, dédoublonnés par lecture capteur distincte), cadence capteur **inchangée**,
`capteurs gaz on|off` comme **unique** variable.

⚠️ **Les horodatages sont corrigés DEUX fois** : on retranche l'`age` rendu par `capteurs` **et**
**un cycle capteur de 5 s**, parce que la boucle « data ready » sort à la première itération —
chaque cycle **déclenche une conversion ET LIT LA PRÉCÉDENTE**. ⛔ Ce comportement n'est **pas**
corrigé par cette story, il est **compensé à l'analyse**.

### Les plateaux

| plateau | fenêtre | T | RH | n |
|---|---|---:|---:|---:|
| **A** — gaz OFF | 90–240 s | **25,503 °C** | **53,90 %** | 60 |
| **B** — gaz ON | 370–478 s | **25,850 °C** | **52,66 %** | 34 |
| **C** — gaz OFF | 660–840 s | **25,615 °C** | **53,78 %** | 60 |

### ✅ Le coût du chauffeur — dn2-1 est CONFIRMÉ, et le témoin sert encore

| | T | RH |
|---|---:|---:|
| naïf **B − A** | +0,347 °C | −1,23 pt |
| naïf **B − C** | +0,235 °C | −1,11 pt |
| **DÉRIVE DE PIÈCE A → C** | **+0,112 °C** sur 583 s (**+0,69 °C/h**) | −0,12 pt |
| 🔴 **CORRIGÉ** (base interpolée à l'instant de B) | **+0,299 °C** | **−1,18 pt** |

> **dn2-1 publiait +0,3 °C et −2 pts.** La température est **confirmée au centième** ; l'humidité
> est **moins sévère que publiée** (−1,18 au lieu de −2).
> ⚠️ **Sans la phase C on publiait +0,347 °C, soit 16 % trop haut.** L'écart est plus petit qu'en
> dn2-1 (facteur 2) — **le principe tient, son ampleur varie d'une séance à l'autre**, ce qui est
> précisément pourquoi le témoin n'est pas négociable.

### 🔴 LE TEMPS DE RETOUR — la mesure qui n'avait jamais été faite

Ligne de base à l'instant de la commande (interpolée) : **T = 25,563 °C · RH = 53,83 %**.

| grandeur | seuil | temps de retour | en cycles capteur |
|---|---|---:|---:|
| **T** | **≤ 0,1 °C** *(le critère)* | **24,6 s** | **4,9** |
| T | ≤ 0,15 °C | 9,6 s | 1,9 |
| **RH** | **≤ 0,2 pt** | **89,6 s** | **17,9** |
| RH | ≤ 0,5 pt | 24,6 s | 4,9 |

### 🔴 ET LE PROTOCOLE SE RÉFUTE LUI-MÊME — le bruit de pièce dépasse le critère

| phase | gaz | étendue de T sur la phase |
|---|---|---:|
| A | OFF tout du long | **0,20 °C** (25,40 → 25,60) |
| **C** | **OFF tout du long** | **0,40 °C** (25,40 → 25,80) |

**Gaz coupé du début à la fin, la température parcourt 0,20 à 0,40 °C.** Le critère en demande
**0,1**. ⇒ **Le bruit propre de la pièce est 2 à 4 fois plus grand que la grandeur à trancher.**

🔴 C'est le **piège n°2 de la méthodologie appliqué au protocole lui-même** : *« cet instrument
PEUT-IL voir le défaut qu'il prétend exclure ? »* — **non.** Un « retour en 24,6 s » mesuré contre
une ligne de base qui bouge de 0,4 °C n'est pas une mesure de 0,1 °C.

### ⇒ VERDICT : **D7 TOMBE**, pour TROIS raisons cumulées

1. **Le critère écrit avant n'est pas tenu** : **4,9 cycles** contre ≤ 3.
2. 🔴 **L'humidité met 17,9 cycles (89,6 s)** — et la case **AMBIANCE affiche T *et* RH** (D6). La
   page de détail laisserait donc l'humidité fausse **une minute et demie** après sa fermeture, sur
   la seule case du dashboard qui porte une source **réelle**. C'est le mensonge d'interface que ce
   dépôt traque depuis dn1-3, réintroduit par la fonctionnalité censée enrichir la page.
3. **Le critère est ININSTRUMENTABLE ici** : 0,1 °C demandé contre 0,2–0,4 °C de bruit de pièce.

**Conséquences, écrites :** `DN_CAPT_GAZ_DEFAUT` **reste `false`** · **le gaz repart post-V1** ·
la tâche T7 de dn3-2 **n'est pas exécutée** · les deux défauts de l'`iaq_score`
(`deferred-work.md`) **redeviennent non bloquants**, et le choix de source d'indice (BSEC…) est
**reporté avec le gaz**.

⚠️ **Ce n'est PAS un échec de la story.** D1 : *« chaque story-POC ferme sa question PAR LA MESURE,
jamais sur le papier. »* La question est **fermée**.

### Ce qu'il faudrait pour rouvrir D7 proprement (post-V1)

- Une **enceinte thermiquement stable** — ou un témoin de température **indépendant du BME680**,
  puisque c'est le die chauffé qui porte le thermomètre. Sans référence externe, la ligne de base et
  la grandeur mesurée partagent le même capteur.
- Ou **abandonner le critère en température absolue** au profit d'un critère sur la **dérivée**
  (« la pente est retombée sous X °C/min »), qui est insensible à une dérive lente de pièce.
- ⚠️ Et le problème de la **RH** resterait entier : 90 s de retour, c'est structurel au capteur, pas
  au protocole de mesure.

---

## 13.15 🔴 LE RTC PCF85063A À `0x51` — QUALIFIÉ, ET SA RÉTENTION MESURÉE (dn3-2, 2026-08-18)

Jusqu'à dn3-2, tout ce que le dépôt savait de cette puce tenait en une ligne : *« adresse `0x51`,
stable sur les 4 passes du scan »*. **Aucun registre lu, aucun driver, état de l'heure et existence
d'une pile totalement inconnus.** Cette section ferme les trois.

### 13.15.1 La qualification — par LECTURE, jamais par le scan

Doctrine dn2-1, payée deux fois (faux positifs **et** faux négatifs, §13.2 et §13.6 bis) :
*« le sondage DÉCOUVRE, seule la LECTURE DE REGISTRE QUALIFIE »*. Sortie verbatim :

```
i2c lire 51 00 16  ->  00 00 00 00 96 25 15 01 06 01 00 80 80 80 80 80
i2c lire 51 10 2   ->  00 18
```

| Registre | Valeur | Ce qu'on en tire |
|---|---|---|
| `0x00` Control_1 | `0x00` | `STOP=0` (elle tourne) · `12_24=0` (**24 h**) · **`CAP_SEL=0` ⇒ quartz 7 pF** |
| `0x01` Control_2 | `0x00` | `COF=000` ⇒ **sortie CLKOUT 32,768 kHz ACTIVE** — consommation pour rien, aucune piste ne l'utilise. Consignée, **non touchée** (la couper est une écriture dont le bénéfice n'est pas mesuré) |
| `0x02`-`0x03` | `00 00` | Offset et RAM_byte |
| `0x04` Seconds | `0x96` | 🔴 **bit 7 = `OS` = 1** + `16` s en BCD |
| `0x05`-`0x0A` | | `25` min · `15` h · `01` · jsem `6` · mois `01` · an `00` |
| `0x0B`-`0x0F` | `0x80` ×5 | bit `AEN_x` posé sur les cinq ⇒ **toutes les alarmes DÉSARMÉES** |
| `0x10`-`0x11` | `00 18` | Timer désactivé, `TCF` = 1/60 Hz (défaut) |

### 13.15.2 ✅ LE VARIANT EST « A », ET C'EST LA MESURE QUI RÉFUTE « TP »

⚠️ La story avertissait que *« le variant A et le variant TP ne portent pas la même carte de
registres »*, et le dépôt a payé **quatre fois** pour avoir cru une source externe — dont **SDA/SCL
inversés dans la doc officielle Waveshare** (§13.1). On ne tranche donc pas sur la doc.

**Trois passes espacées** : `0x04`/`0x05` **bougent** (`96 25` → `81 26` → `A8 26`) pendant que
`0x02`/`0x03` **ne bougent pas**. ⇒ la base de temps est en **`0x04`**. Sur le variant **TP** elle
serait en `0x02`, qui aurait bougé. **⇒ TP RÉFUTÉ PAR LA MESURE.**

✅ **Confirmé une seconde fois, autrement** : après écriture du témoin, `0x03` relit **`0xD7`** —
une valeur arbitraire qu'il conserve. C'est donc bien un **octet de RAM libre**, ce que seul le
variant A possède. Sur TP, `0x03` est le registre des **minutes** et `0xD7` y serait destructeur.

### 13.15.3 🔴 LA RÉTENTION — **CETTE CARTE N'A AUCUNE SAUVEGARDE**

**Geste owner** : câble USB débranché (**seule** alimentation — D5 : pas de batterie), **30 s**,
rebranché. 30 s et pas 2, délibérément : sans sauvegarde le RTC perd tout en moins d'une seconde,
un **supercondensateur** tiendrait quelques secondes — 30 s discrimine les deux.

| Instrument | Avant coupure | Après rebranchement |
|---|---|---|
| `OS` | **0** | 🔴 **1** |
| Heure lue | `2026-08-18 11:32:13` | 🔴 **`2000-01-01 00:00:54`** (valeur de sortie de reset, recomptée depuis zéro) |
| Témoin cross-boot | — | 🔴 **`0x00`** au lieu de `0xD7` |
| Barre à l'écran | `11:32` / `MAR. 18 AOÛT` | **`--:--` / `HEURE NON POSÉE`** |

**⇒ TROIS instruments indépendants concordent. Il n'y a pas de cellule de sauvegarde.**
D5 disait *« PAS DE BATTERIE »* en parlant de la LiPo principale et **ne disait rien** d'un backup
RTC. **Maintenant on sait** : l'heure doit être re-posée après **toute** coupure secteur.

✅ **Et W9 est validé EN CONDITIONS RÉELLES, pas en simulation** : la barre a affiché
**« --:-- HEURE NON POSÉE »**, **vu sur la dalle par l'owner**. Une barre qui aurait affiché
« 00:00 » aurait été le mensonge exact qu'AC3 interdit — et il aurait été **indétectable**.

📌 **Le jour de semaine relit `6` au reset**, comme au tout premier allumage. ⇒ **confirmation que
la prudence de l'en-tête était fondée** : `6` est la valeur POR du registre, **pas** une cohérence
calculée avec « 2000-01-01 était un samedi ». La puce compte le jour de semaine dans son propre
registre, indépendamment de la date — d'où `dn_rtc_poser()` qui le **calcule** (Sakamoto).

### 13.15.4 🔴 LE TÉMOIN ANTI-FANTÔME ÉTAIT AVEUGLE AU CAS QU'IL PRÉTENDAIT TRANCHER

Le patron du BME680 (§13.6 bis) transposé au RTC posait déjà une question : **Control_1 ne peut pas
servir de témoin**, parce que sa valeur de sortie de reset est `0x00` — exactement celle qu'on
mesure. Une garde dessus serait **verte pendant le défaut qu'elle prétend détecter**.
⇒ Le témoin est donc **`RAM_byte` (0x03)**, où l'on **impose** `0xD7` au lieu de **constater** une
valeur. C'était juste.

🔴 **Mais la première implémentation ÉCRIVAIT sans relire.** Or toute coupure est suivie d'un
reboot, donc d'un `dn_rtc_init()`, donc d'une réécriture : après la coupure, `rtc` annonçait
tranquillement **« témoin 0xD7 ✅ la puce n'a pas redémarré »**. Vrai *depuis l'init*, et **trompeur
pour qui cherchait justement à savoir si l'heure avait survécu**.
⚠️ Et l'en-tête du module **affirmait** qu'il *« répond à la question de la rétention sans
ambiguïté »* — *« un commentaire qui affirme un invariant que le code ne tient pas est pire que pas
de commentaire »*. **C'est le piège n°2 retourné contre le garde lui-même.**

**Correctif** : `temoin_poser()` **relit d'abord, journalise, puis écrit**. Le module porte
désormais **deux verdicts nommés et distincts** :

| Verdict | Question | Instrument |
|---|---|---|
| **CROSS-BOOT** | l'alimentation a-t-elle été coupée depuis le dernier démarrage ? | `dn_rtc_temoin_boot()` |
| **RUNTIME** | la puce a-t-elle redémarré **pendant** que le firmware tourne ? | `dn_rtc_temoin_lu()` + compteur `temoins_perdus` |

✅ **Prouvé DES DEUX CÔTÉS le 2026-08-18**, et la seconde coupure le montre de façon décisive —
les deux verdicts sont **opposés au même instant**, et tous deux vrais :

```
retention : 0x00 relu AU BOOT (attendu 0xD7) ⇒ 🔴 ELLE A PERDU SON ALIMENTATION
temoin    : 0xD7 en 0x03                      ⇒ ✅ pas de redemarrage EN COURS DE ROUTE
```

**Un instrument unique aurait affiché `0xD7 ✅` et masqué la coupure.**

⚠️ **Et la preuve a failli être effacée par sa propre lecture** : le verdict est relevé **au boot**.
Un `dn_console.py --reset` aurait rejoué `temoin_poser()`, réécrit `0xD7`, et détruit l'évidence.
⇒ **C'est parce que le verdict est LATCHÉ EN RAM et exposé par `rtc` qu'il a survécu.** Un verdict
qui ne vivrait que dans le log de boot serait perdu dès qu'on rate la fenêtre de capture.

### 13.15.5 La dérive — une borne, honnête, et un instrument laissé en place

Protocole : `rtc set` sur l'heure de l'hôte, puis relecture **encadrée** par deux `date` (fenêtre
hôte de **0 s**, donc ±1 s de quantification).

| t | RTC | hôte | écart |
|---|---|---|---|
| référence | `09:32:44` | `09:32:44` | **0 s** |
| +35 min | `10:08:06` | `10:08:06` | **0 s** |
| +2 h 00 | `11:32:13` | `11:32:14` | **−1 s** |

⇒ **≈ −139 ppm (−12 s/jour)**, ⚠️ **mais l'incertitude de quantification est du même ordre que la
mesure** (±1 s sur 7 170 s = ±140 ppm). **Borne honnête : |dérive| < 280 ppm.**
⛔ **Ne pas publier −139 ppm comme un fait** : la mesure ne sait pas encore distinguer −139 de 0.
Une fenêtre de **24 h** resserrerait la borne d'un facteur 12 — et l'instrument (un `rtc` encadré
par deux `date`) est **déjà en place**, donc la mesure est gratuite.

⚠️ **Ça compte pour `CAP_SEL`** : un quartz 32,768 kHz correctement chargé dérive de ±20 ppm. Une
dérive réelle de −139 ppm serait cohérente avec un **désaccord de capacité de charge** (7 pF posés
contre un quartz qui en demanderait 12,5) — mais **la mesure ne le prouve pas encore**, et
`CAP_SEL` reste consigné **INCONNU**, non touché.

### 13.15.6 Le coût du module, mesuré

| | |
|---|---|
| Pile de la tâche `dn_rtc` | **4 096 o alloués**, high-water mark relu : **2 836 o libres** ⇒ **1 260 o réellement consommés au pire** |
| RAM interne libre, avant → après | 108 435 → **104 311 o** (**−4 124 o**) |
| Cadence de sondage | **2 Hz** (`DN_RTC_PERIODE_MS 500`), ~8 octets par lecture |
| Charge de bus | négligeable devant les **~30 transactions/s** du GT911 en `poll` |
| Erreurs sur ~1 700 lectures | **i2c 0 · bcd 0 · témoins perdus 0** |

📌 **Piste chiffrée pour dn4-1, pas une action** : à 1 260 o consommés sur 4 096, la pile pourrait
descendre à **2 048 o** et rendre ~2 Ko de RAM interne. ⛔ Non fait ici : le budget n'est pas
contraint aujourd'hui, et la marge protège contre un `printf` ajouté plus tard. **Le chiffre est
publié pour que la décision soit une mesure, pas une intuition.**

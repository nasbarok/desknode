# §13 — Les capteurs sur le bus I²C externe (dn2-1, P4)

> **Fichier frère** de `ESP32-S3-Touch-LCD-2.8B-affichage.md`, référencé depuis sa §13.
> Même règle que lui : **tout ce qui est ici a été mesuré sur la carte**, et là où la mesure a
> corrigé une source tierce, c'est écrit noir sur blanc avec la source fautive.
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
> ⚠️ **Le contact reste tenu à la main : la SOUDURE demeure obligatoire** avant toute campagne
> (cadence, auto-échauffement, budgets) — un chiffre pris sur un contact précaire n'est pas
> recevable.

Séance du **2026-08-16** (`/desknode-board`), firmware `ce32c87` puis la commande `i2c` de dn2-1.

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
> un composant répond à travers lui. **Il ne reste qu'un geste : SOUDER la barrette**, pour que le
> contact cesse d'être un geste d'owner et devienne une propriété du montage.

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

**Coût** : binaire **796 240 → 800 640 o** (+4 400 o). Aucune ligne de `sdkconfig.defaults`
touchée, aucun composant ajouté au manifeste.

---

## 13.7 Ce que la séance laisse — et ce qu'elle a fermé

**Fermé, par la mesure :**

- **Le capteur** : BME680 authentique, vivant, à **`0x77`** (`dn_pins.h` porte l'adresse et son
  constat). Le témoin négatif est naturel et surabondant : ~30 scans sans contact = adresse
  absente ; contact rétabli = `5/5` sur 8 passes.
- **Le chemin complet** embase JST → câble → barrette → puce : prouvé de bout en bout.
- **Le brochage du connecteur**, les 4 occupants internes du bus, l'instrument `i2c` et son
  défaut de faux positifs corrigé.

**Restant, dans l'ordre :**

1. **SOUDER la barrette** (6 broches, ou les 4 utiles) — préalable à toute campagne. Le contact de
   cette séance était tenu à la main.
2. Après soudure : re-scan de confirmation (`0x77` attendu à 5/5 **sans** les mains), puis
   l'arbitrage du **driver** (AC5), le module `dn_capteurs` (AC6/AC7), les cases du dashboard
   (AC8), l'A/B chauffage (AC9) et les budgets (AC10).
3. Les 3 autres breakouts (BH1750, VL53L0X, INA219) ne sont **ni inventoriés ni branchés** — une
   variable à la fois (décision owner **D2-1a**), ils sont à dn4-1.

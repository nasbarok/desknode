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
| **Binaire** | 800 640 o | **827 632 o** | 🔴 **+26 992 o** — *c'est LE coût réel du composant, celui que le §13.6 ter refusait de publier à 0* |
| **CPU** (`cpu 30`) | 0,9 % | **1,2 %** | **+0,3 pt** pour DEUX cases à 5 s |
| `fps 15` | 37,40 Hz | **37,34 Hz (−0,18 %)** | dans la bande de bruit du dépôt (37,33-37,45) |
| Cycle de mesure | — | **26 ms** | mesuré, pas repris de la datasheet |
| Fiabilité | — | **62 lectures, 0 erreur** (i2c/donnée/bornes) | ~5 min de régime |

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
RAM interne libre est passée de 113 847 à **109 295 o**.

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

🔴 **LES SEPT PHOTOS DE LA SÉANCE DE CÂBLAGE** — versées le **2026-08-20**, prises par l'owner
entre **00:38:30 et 09:51:16** (EXIF). ⚠️ *Cet en-tête disait « CINQ » et « jusqu'à 01:16:56 » —
corrigé par la revue du 2026-08-20 : `e931c31` a ajouté les **deux photos du montage final** (09:51)
sans mettre l'en-tête à jour.* ⚠️ **Réduites à 2 600 px de côté long** (0,44 à 0,61 Mo au
lieu de 10 à 13 Mo) : la sérigraphie y reste lisible, et les originaux restent chez l'owner. C'est
un arbitrage assumé — 12 photos brutes auraient pesé **136 Mo** dans un dépôt qui en portait 12.

| Fichier (`docs/cablage/`) | EXIF | Ce qu'elle ÉTABLIT |
|---|---|---|
| `2026-08-20_0038-derivation-premier-pin-deux-fils-soudes.jpg` | 00:38:30 | Le **geste** de la dérivation : deux fils soudés **sur l'arrière d'un même pin mâle**. C'est le pin qui fait la dérivation, et c'est ce qui remplace une plaque à pastilles (l'owner n'en a pas) |
| `2026-08-20_0058-derivation-quatre-cables-en-cours.jpg` | 00:58:35 | Les **quatre câbles en cours** : on y compte les fils convergents de chaque faisceau |
| `2026-08-20_0110-derivation-quatre-cables-finis-gaines.jpg` | 01:10:55 | Les **quatre câbles terminés et gainés**, pin mâle en bout. ⇒ **La topologie Y2 est PHOTOGRAPHIÉE** — exigence d'AC5 |
| 🔴 `2026-08-20_0116-bh1750-et-ina219-barrettes-SOUDEES.jpg` | 01:16:53 | 🔴 **LA PREMIÈRE PHOTO D'UN ÉTAT SOUDÉ DU DÉPÔT.** BH1750 (`BH1750`, `V322`) barrette **5 broches SOUDÉE**, les cinq pastilles d'étain visibles ; INA219 barrette **6 broches SOUDÉE** **et bornier vert SOUDÉ**, sérigraphie `Vin- · Vin+ · Sda · Scl · Gnd · Vcc`, shunt `R100`, et les cavaliers **`I2C Address` `A1`/`A0`** |
| 🔴 `2026-08-20_0116-ina219-et-tof050c-barrettes-SOUDEES.jpg` | 01:16:56 | Le **ToF soudé**, sérigraphie **`TOF050C-VL6180X`** lisible sur le bord, barrette **6 broches SOUDÉE**, et le boîtier optique noir. ⇒ **La réf est lisible SUR LA PHOTO DE L'ÉTAT SOUDÉ**, pas seulement sur celle du sachet |
| 🔴 **LE MONTAGE FINAL — deux photos, 09:51** | EXIF | Ce qu'elles ÉTABLISSENT *(sous-titre ajouté par la revue du 2026-08-20 : `e931c31` avait inséré ces deux lignes APRÈS une ligne vide, ce qui les laissait ORPHELINES. ⚠️ **Le correctif avait posé un `\|---\|---\|---\|` sous ce sous-titre — retiré le 2026-08-24** : en GFM la ligne de délimitation n'est reconnue qu'**immédiatement après l'en-tête**, donc au milieu d'un corps de table elle rendait trois cellules `---`. La suppression de la ligne vide suffisait.)* |
| 🔴 `2026-08-20_0951-montage-final-8-devices-grille-six-cases.jpg` | 09:51:16 | 🔴 **LE MONTAGE FINAL, ET L'ÉCRAN EST LISIBLE.** Le bandeau latéral `DESKNODE · LIVING PCB V0 — P1`, **les SIX cases** (`CPU` · `RÉSEAU` · `AMBIANCE` / `CPU` · `RAM` · `DISQUE`), les libellés `I2C` et `WIFI/BT`, `c.max`, et le bandeau **`MENU`**. Deux modules dans le cadre : le **BH1750** (bleu) et le **ToF** (noir, lucarne optique visible). ⚠️ La barre affiche **« HEURE NON POSÉE »** — **attendu** : §13.15.3, cette carte n'a **aucune sauvegarde RTC**, et l'A/B de démarrage à froid a coupé l'alimentation sept fois de plus. **La garde refuse une heure fausse ; elle fonctionne** |
| `2026-08-20_0951-montage-final-en-main-les-quatre-modules.jpg` | 09:51:02 | Le **montage complet en main**, à l'échelle : la carte, ses **quatre modules** en étoile autour d'elle (BH1750, ToF, INA219, et le **BME680** au bout du câble tressé, toujours sur son embase JST), le câble USB, et le bureau derrière. ⇒ **C'est la photo qui montre que le bus a DEUX points d'entrée physiques** (embase JST pour le BME680, header 2×12 pour les trois nouveaux) |

✅ **CE QUE CES SEPT PHOTOS FERMENT** : l'encart de cette section annonçait depuis le **2026-08-17**
qu'**aucune photo du dépôt ne documentait un état SOUDÉ ni le montage final**. 🎯 **LES DEUX SONT
FAITS.** ⇒ **AC1 et AC5 sont complets, et l'encart peut enfin être clos** — ce qu'il annonçait comme
manquant ne l'est plus.

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
> caractère. ⇒ **La voie MARQUAGES est ÉPUISÉE et déclarée.** ⛔ Ne pas recopier « 4,7 kΩ » d'un
> catalogue : ce serait exactement l'étiquette héritée que cette story vient de réfuter sur le ToF.
>
> 🔴 **MISE À JOUR 2026-08-20 — LES TIRAGES SONT MESURÉS À L'OHMMÈTRE, ET LE CATALOGUE AURAIT
> MENTI.** Ajouté par la revue de code du 2026-08-20 : la mesure avait été faite en séance (T1/T5)
> et **n'était jamais entrée dans cette table, qui continuait d'annoncer « NON MESURÉE »**.
> Modules **isolés, hors tension**, `SDA`/`SCL` ↔ `VCC` :
>
> | Module | `SDA` ↔ `VCC` | `SCL` ↔ `VCC` | Verdict |
> |---|---|---|---|
> | **BH1750 (GY-302)** | **OUVERT** | **OUVERT** | 🔴 **AUCUN tirage** — or le GY-302 est *réputé* en porter à 4,7 kΩ. **Le catalogue aurait menti.** |
> | **ToF (TOF050C)** | **9,99 kΩ** | **10,04 kΩ** | 10 kΩ |
> | **INA219 (CJMCU)** | **10,09 kΩ** | **10,08 kΩ** | 10 kΩ |
>
> ⇒ **`+2` jeux de tirages, PAS `+3`** : on passe de **2 à 4**, pas de 2 à 5.
> `10k ∥ 10k = 5 kΩ` ⇒ **l'ajout coûte `+0,66 mA`** à l'état bas, sur un budget I²C de **3 mA**
> **dont la consommation de départ n'est pas mesurée.**
> ⚠️ *Ce verdict disait **« Large »** jusqu'à la revue du **2026-08-24**, ce qui comparait un
> **INCRÉMENT** à une **limite ABSOLUE** — or la limite de 3 mA porte sur le courant **total** que
> chaque device encaisse à l'état bas, et la contribution des **deux jeux préexistants** (carte +
> BME680) est inconnue, comme la ligne suivante le dit elle-même. **Y6 demandait un TOTAL, la réponse
> publiait un DELTA.** ⇒ Le `+0,66 mA` reste juste ; c'est la **conclusion** qui outrepassait la
> mesure. **Décision owner du 2026-08-24 : reformuler plutôt que ressortir l'ohmmètre** — l'écart est
> déclaré, il n'est pas fermé.*
> ⛔ **CE QUE CETTE MESURE NE COUVRE PAS** : elle est prise **côté MODULES**, pas côté **CARTE**.
> La mesure carte n'a pas été faite — instrument inadéquat, dit par l'owner (*« je ne peux pas
> prendre les données avec le multimètre »*) — ⇒ **écrit plutôt que bâclé.**
> ⚠️ **La ligne « 2 à 5 » ci-dessous est celle du cadrage, conservée** : elle supposait trois jeux
> de tirages là où il n'y en a que deux. C'est la supposition que la mesure a corrigée.
>
> **Ce qui était acquis AVANT la mesure** : on passe de **2 à 5 jeux de tirages en parallèle** sur
> le même bus, donc la résistance équivalente **est divisée**, donc le courant que chaque device
> doit encaisser à l'état bas **augmente** (limite I²C : **3 mA**). Ce n'est pas nécessairement un
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
> - ✅ **CLOS LE 2026-08-20** : l'état **SOUDÉ** (deux photos, 01:16) **et** le **montage final à
>   8 devices** (deux photos, 09:51) sont versés. ⇒ **La demande ouverte depuis le 2026-08-17 est
>   satisfaite**, et c'est bien `dn4-2` qui l'a produite, comme annoncé.
> - ⛔ **RESTE VRAI AUSSI** : les quatre photos de dn2-1 restent antérieures à la soudure du BME680.
> ⇒ ~~**AC1 de `dn2-1` est SOLDÉ ; AC5 de `dn4-2` reste OUVERT.**~~ → 🔴 **LIGNE PÉRIMÉE,
> CORRIGÉE PAR LA REVUE DU 2026-08-20** : elle disait l'inverse des trois lignes juste au-dessus
> (et de la conclusion de la table, *« AC1 et AC5 sont complets »*), **dans le même encart et le
> même commit** — la conclusion n'avait pas suivi la mise à jour de `e931c31`.
> ⇒ **AC1 de `dn2-1` est SOLDÉ, et le volet PHOTOS d'AC5 de `dn4-2` l'est aussi** (état soudé +
> montage final, 4 photos). ⚠️ **Ce qui restait dû sur AC5 n'était pas une photo** mais la
> consignation des vérifications d'avant mise sous tension — voir **§13.16.4 bis**.

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

### 🔴 13.1 bis LE HEADER 2×12 — IL N'Y EN A QU'**UN**, ET LE DÉPÔT ÉCRIVAIT « GAUCHE » ET « DROIT » COMME S'IL Y EN AVAIT DEUX (`dn4-2`, 2026-08-19)

**Sérigraphie relue sur `docs/cablage/2026-08-16_2228-carte-embases-jst-jumelles-i2c-uart.jpg`** —
une photo **versée au dépôt depuis le 2026-08-17** et jamais relue à ce niveau de détail — puis
**CONFIRMÉE PAR CONSTAT OWNER, carte en main** (2026-08-19) : *« UN seul »*.

| Rangée | Position 1 → 12 |
|---|---|
| **A** | `5V · BAT · G · **33** · **34** · **35** · **36** · **37** · **RXD** · **TXD** · 3V3 · G |
| **B** | `5V · VCC · G · D- · D+ · 0 · 4 · 16 · **SCL** · **SDA** · 3V3 · G` |

🔴 **CE QUE ÇA CORRIGE.** `§14.3` de `…-affichage.md` et l'entrée de ledger correspondante parlent du
*« header 2×12 **DROIT** »* (les broches PSRAM), et la story `dn4-2` du *« header 2×12 **GAUCHE** »*
(l'accès I²C) — **comme s'il s'agissait de deux connecteurs distincts**. Il n'y en a qu'un :
**« gauche » et « droite » désignaient les deux RANGÉES du même header**, et personne ne l'avait
écrit. ⚠️ **Ce n'est pas une contradiction du brief ni de l'epic** (ni l'un ni l'autre ne parle de
headers) ⇒ **pas de `[CC]`** : c'est une imprécision de `hardware/`, corrigée ici.

🔴 **ET ÇA ARME UN PIÈGE QUI EST LE JUMEAU EXACT DE CELUI DES DEUX EMBASES JST — MAIS À 2,54 mm.**
`RXD` et `TXD` sont en **positions 9 et 10 de la rangée A**, c'est-à-dire **exactement derrière
`SCL` et `SDA`**. Se tromper de rangée **alimente correctement le capteur** (`3V3`/`G` sont en 11-12
sur les **deux** rangées) et **lui envoie l'UART** : le composant reste muet, **et rien ne le
signale** — le symptôme de la mauvaise soudure, pour la troisième fois dans ce dossier.
⇒ **La rangée B se reconnaît à ce qu'elle porte aussi `D- · D+ · 0 · 4 · 16`.**
**La sérigraphie fait foi, pas la position.**

⚠️ **Conséquence sur le piège PSRAM (`§14.3`, AC3 de `dn4-2`)** : `33..37` ne sont pas sur *« un autre
header »*, ils sont sur **le même connecteur, une rangée plus loin**. La parade tient — l'I²C est un
bus, aucune de ces broches n'est consommée — mais **le risque de contact accidentel est plus élevé
que la doc ne le laissait croire**, et l'entrée de ledger reste **OUVERTE** pour cette raison de plus.

✅ **Et un gain, mesuré sur la même sérigraphie** : `3V3` et `G` sont en **positions 11-12 des DEUX
rangées** ⇒ **deux masses et deux 3V3 disponibles**, de quoi alimenter la guirlande *et* tirer
`ADDR` du BH1750 à la masse sans se battre pour un point unique.

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

> 🔴 **AMENDÉ PAR LA REVUE DE CODE DU 2026-08-20 — CETTE TABLE ÉTAIT RESTÉE À QUATRE.**
> Une section titrée *« les occupants **RÉELS** du bus — mesurés, pas déclarés »* qui en oublie la
> moitié est exactement l'instrument qui ment. **Le bus en porte HUIT**, tous qualifiés **par une
> transaction de donnée**, ⛔ jamais par le scan :
>
> | Adresse | Composant | Qualifié par | Depuis |
> |---|---|---|---|
> | **`0x20`** | TCA9554 — expander | témoin positif du scan **+ transactions du pilote `esp_io_expander`** (LCD_RST/TP_RST/LCD_CS) | dn1-2 |
> | **`0x23`** | **BH1750 (GY-302)** — luminosité | 🔴 **STIMULUS** — il n'a **aucun** registre | **dn4-2** |
> | **`0x29`** | **TOF050C-VL6180X** — distance | `lire16 0000` → **`B4`**, 5/5 | **dn4-2** |
> | **`0x40`** | **INA219 (CJMCU)** — tension/courant | `lire 00 2` → **`39 9F`**, 5/5 | **dn4-2** |
> | **`0x51`** | PCF85063**A** — RTC | lecture + témoin anti-fantôme `0xD7` | dn2-1 / dn3-2 |
> | **`0x5D`** | GT911 — tactile | témoin positif du scan · `lire16 5D 8140 4` → `"911"` | dn1-4 |
> | **`0x6B`** | QMI8658 — IMU | scan (**hors V1**, non piloté) — ⚠️ **LA SEULE EXCEPTION À LA PHRASE D'INTRO** : elle n'est PAS qualifiée par une transaction de donnée, faute de pilote. *(Écart relevé le 2026-08-24 : le préambule disait « tous qualifiés par une transaction, ⛔ jamais par le scan » dans une section dont l'amendement dit qu'« une liste qui en oublie la moitié est exactement l'instrument qui ment ».)* | dn2-1 |
> | **`0x77`** | BME680 | `lire 77 D0` → `61` | dn2-1 |
>
> ✅ **Aucune collision d'adresses — CONSTATÉE, pas supposée.**

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
i2c                                    scan 0x08..0x77, chaque trouvaille re-sondée 5 fois
i2c lire   <addr> <reg>     [n=1..16]  lecture registre, index 8 bits
i2c lire16 <addr> <reg16>   [n=1..16]  lecture registre, index 16 BITS   (dn4-2)
i2c brut   <addr>           [n=1..16]  lecture SANS index                (dn4-2)
i2c ecrire <addr> <o1> [o2..o8]        écriture NUE, aucune lecture      (dn4-2)
i2c rafale <ms=1000..30000>            saturation du bus (AC9)           (dn4-2)
```

> 🔴 **AMENDÉ PAR LA REVUE DE CODE DU 2026-08-20.** Cette liste s'était arrêtée à deux entrées
> alors que `dn4-2` en a livré quatre de plus — et elle **se lit comme exhaustive**, ce qui est
> précisément le défaut que ce chapitre traque. ⛔ **C'est `aide` qui fait foi, pas cette liste.**
> - **Pourquoi trois primitives de plus** : `i2c lire` **écrit un octet d'index puis lit**. Le
>   **BH1750 n'a aucun registre** (l'octet est un **opcode** : `00` = power down, `07` = reset) et
>   le **VL6180X exige un index 16 bits**. ⇒ L'instrument d'origine ne qualifiait qu'**un** des
>   trois capteurs. Détail et critères d'arbitrage : **§13.6 quater**.
> - ⚠️ **`n` et `ms` sont en DÉCIMAL**, les adresses / registres / octets en **HEXA sans `0x`**.
>   La bannière disait « tout est en HEXA » : `i2c brut 23 12` lit **12** octets, pas 18, et les
>   deux lectures tombant dans les bornes, **rien ne le signalait**. Corrigé le 2026-08-20.
> - ⚠️ **`i2c rafale` bloque le REPL — donc le transport PC — pendant TOUTE sa fenêtre**, jusqu'à
>   **30 s**. ⛔ Le « ~26 ms » qu'on lit ailleurs est le coût d'**un scan sain** ; le pire cas du
>   scan est **~9 s**, et la rafale est bornée à 30 s. **Trois chiffres, trois commandes.**

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

⚠️ **Ce que ce choix N'ENGAGE PAS** : les 3 capteurs de **`dn4-2`** (⚠️ *cette ligne écrivait
« dn4-1 » et « VL53L0X » — deux étiquettes fausses, corrigées par la revue de code du 2026-08-20 :
`dn4-1-tout-branche-tenue-h24` est `superseded`, et le module est un `TOF050C-VL6180X`*).
`k0i05` publie aussi `esp_bh1750`, mais **BH1750 / TOF050C-VL6180X / INA219** se ré-arbitrent chacun
sur le même critère 1. **Rien n'oblige à rester dans la même famille.**
🔴 **Et l'arbitrage appartient à `dn4-3`, pas à `dn4-2`** : celle-ci les a **branchés et qualifiés**,
elle n'en pilote aucun en régime.

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

1. ~~**dn4-1** — les 3 autres breakouts (BH1750 `0x23`, VL53L0X `0x29`, INA219 `0x40`) : **ni
   inventoriés ni branchés**~~ — 🔴 **PÉRIMÉ, CORRIGÉ PAR LA REVUE DE CODE DU 2026-08-20.**
   ⛔ Trois mensonges dans une ligne : (a) `dn4-1-tout-branche-tenue-h24` est **`superseded`**, le
   travail est passé à **`dn4-2`** au correct-course du 2026-08-18 ; (b) ce n'est **pas** un
   `VL53L0X` mais un **`TOF050C-VL6180X`**, tranché **par la lecture** (`i2c lire16 29 0000` → `B4`,
   5/5, §13.16.6) ; (c) les trois sont **inventoriés, SOUDÉS et QUALIFIÉS** depuis le 2026-08-20.
   ⚠️ La ligne est **barrée, pas effacée** — un lecteur qui suivait ce pointeur arrivait sur une
   story close qui ne parle pas de capteurs, et c'est la trace qui l'explique.
   *(État réel : décision owner **D2-1a**, une variable à la fois — elle a été tenue.)* Ils se
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
⇒ ~~**À rejouer en dn4-1**~~ → 🔴 **REJOUÉ EN `dn4-2` le 2026-08-20** (AC9, §13.16.12), par la seule
voie qui restait une fois les capteurs soudés : la saturation **logicielle** (`i2c rafale`).
⚠️ **Et le « 400 kHz » de cette section est faux** — corrigé par la revue du 2026-08-20 :
`i2c_master_probe()` reprogramme le bus à **100 kHz** à chaque sondage
(`esp_driver_i2c/i2c_master.c:1391`). Sans effet durable (chaque transaction de device réapplique
son `scl_speed_hz`, `:703`), **mais le sondage est tout ce que le scan et la rafale font** ⇒ les
cadences publiées décrivent une saturation **à 100 kHz**.

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

---

## 13.16 🔴 SÉANCE `dn4-2` (2026-08-19) — T0, ET L'INSTRUMENT RÉPARÉ **AVANT** LE FER

### 13.16.1 T0 — le point de départ, prouvé sur `df5d23d` (SHA **LU AU BANDEAU**)

**Protocole** : arbre `~/projects/desknode` **propre** (`git status --porcelain` vide, vérifié
**AVANT** le flash), `idf.py build`, `idf.py -p /dev/ttyACM0 flash`, puis `dn_console.py --reset`
pour capturer depuis la **première ligne**. `App version: df5d23d` **lu au bandeau**, ⛔ pas déduit
du dépôt. Aucun `idf.py monitor` ouvert.

| Grandeur | T0 mesuré (`df5d23d`) | Référence `dn4-6` (`1156eac`) | Écart |
|---|---|---|---|
| Binaire | **943 712 o** | 943 712 o | **0,00 %** |
| RAM interne libre | **92 219 o** | 92 315 o | **−0,10 %** |
| PSRAM libre | **7 768 236 o** | 7 768 236 o | **0,00 %** |
| Tas LVGL utilisé | **20 468 o (33 %)** | 20 504 o (34 %) | **−0,18 %** |
| Plus gros bloc libre | **40 752 o** | 40 752 o | **0,00 %** |
| Fragmentation | **3 %** | 2 % | +1 pt |
| `fps 15` | **37,40 Hz**, écart **+0,00 %** | 37,40 Hz, +0,00 % | **0,00 %** |
| Boot | **2 319 ms** | 2 321 ms | −0,09 % |
| `nav ab 40` (n=80) | **291,1 / 335,2 / 398,7 ms** | 334,4 (291,1 / 396,7) | +0,8 ms sur la moyenne |

✅ **GATE D'ARRÊT PASSÉE** : aucun écart > 2 % sur `fps`, aucun > 5 % sur un budget mémoire.
⚠️ Le +0,8 ms de `nav ab` est **très en dessous des ±16 ms de bruit sur n=40** — ⛔ ce n'est pas un
verdict, c'est du bruit, et c'est dit.
⚠️ **Instruments modifiés depuis la dernière séance carte : AUCUN** — HEAD est resté `df5d23d`,
c'est-à-dire exactement le commit de la séance post-revue de `dn4-6`. Les chiffres de `dn4-6` ne
sont donc pas morts, et cette table le **confirme par la mesure** plutôt que par le raisonnement.

**Gardes des marches du dessous, toutes vertes** : BME680 `VIVANT`, config `LUE (conforme)`
(`0x72=04 · 0x74=84 · 0x75=08`), cadence **4 999 ms**, `err_i2c` **0** · RTC `0x51` **FIABLE**,
bit `OS` **0**, témoin anti-fantôme `0xD7` **relu au boot ET en régime** · GT911 **0 erreur I²C**.
Bandeau de boot : **aucune ligne d'erreur nouvelle**. La seule qui reste est
`E gpio_install_isr_service already installed` (ligne 123 de la capture), **nommée et rattachée** —
c'est le sujet d'AC11, fermé par cette story.

**Couple encadrant à 5 devices** (la référence que AC8 devra battre à 8) : `touch` avant / 5 scans
`i2c` / `touch` après ⇒ **0 erreur I²C induite**. Scan sain : **27-31 ms**.

---

### 13.16.2 🔴 CONSTAT NEUF À T0 — `dn_console.py` PERD DES LIGNES, ET LA PERTE EST INVISIBLE

**Ce n'est pas une impression de lecture, c'est une violation arithmétique.** La commande `i2c`
imprime N lignes `0xNN n/5`, **puis** un bilan `« X stable(s), Y instable(s) »`, **puis** un verdict
de témoin positif — les trois produits par le **même** firmware, dans la **même** passe. L'invariant
`N == X + Y` ne peut pas être faux côté carte.

| Mode | Passes | Captures violant `N == X+Y` |
|---|---|---|
| **LOT** (`dn_console.py "i2c" "i2c" …`) | **20** | 🔴 **6** |
| **SOLO** (une commande, un processus) | **5** | ✅ **0** |

**Les deux pires, et elles touchent les TÉMOINS** :
- une passe rend **5 lignes pour un bilan de 6**, `0x5D` **absent de la liste** — or `0x5D` est
  **l'un des deux témoins positifs**, et le verdict imprimé juste en dessous dit
  **« ✅ témoin positif OK »**, ce que `dn_console.c:4471-4473` ne peut produire **que si `0x5D` a
  été vu STABLE**. ⇒ **la liste ment, le verdict dit vrai, et rien ne signale le désaccord** ;
- deux passes rendent **4 lignes pour un bilan de 5**, `0x20` (**l'autre témoin**) absent ;
- une passe est rendue **vide**, une autre recolle **11 lignes** sous un bilan de 6.

🔴 **POURQUOI C'EST EXACTEMENT LE DÉFAUT QUE `dn4-2` NE POUVAIT PAS SE PERMETTRE** : une ligne
perdue produit *« l'adresse `0x23` n'est pas là »* sur un BH1750 **qui répond** — juste avant qu'on
décide de dessouder. C'est le faux négatif de §13.2, mais fabriqué **côté hôte**, là où aucun
compteur ne regarde.

⚠️ **VARIABLE CAUSALE NON ISOLÉE, ET C'EST ÉCRIT PLUTÔT QUE DEVINÉ.** Budget d'essais dépensé :
**2 A/B, 30 passes de contrôle** (15 avec `--capture`, 15 sans) — **aucune n'a reproduit**. Deux
mécanismes candidats, aucun prouvé : `ser.reset_input_buffer()` appelé **avant** l'écriture de la
commande suivante (`tools/dn_console.py:170`), et `nettoyer()` (`:154-166`) qui coupe *« jusqu'à la
première ligne qui se termine par la commande »*. ⇒ **Le défaut est RÉEL, INTERMITTENT, et son
déclencheur reste OUVERT.**

✅ **PARADE APPLIQUÉE DANS TOUTE CETTE STORY, et elle ne dépend d'AUCUNE hypothèse causale** :
1. **toute passe publiée vient d'une invocation SOLO** ;
2. **l'invariant `lignes == stables + instables` est vérifié sur chaque capture avant publication.**
Il aurait attrapé les six, qu'elles viennent de l'USB ou du nettoyage.

---

### 13.16.3 ✅ AC4 SOLDÉ — l'instrument couvre les TROIS capteurs, et il est **PROUVÉ SUR DU CONNU**

**Firmware `62e5f1d`, SHA LU AU BANDEAU**, `git status --porcelain` vérifié **VIDE AVANT** le flash.
Critères d'arbitrage : §13.6 quater, **écrits et horodatés AVANT d'ouvrir le code**.

#### Les témoins POSITIFS — chaque primitive reproduit une valeur DÉJÀ PUBLIÉE par ce dépôt

| # | Transaction | Rendu | Ce que ça prouve |
|---|---|---|---|
| 1 | `i2c lire 77 D0` | **`61`** | ✅ le chemin **existant** est intact |
| 2 | `i2c lire 77 89 16` | **`40 43 68 03 00 18 8A 92 D7 58 00 C7 1E 5C FF 1F`** | ✅ **identique OCTET POUR OCTET** au bloc d'étalonnage relevé deux fois en `dn2-1` |
| 3 | `i2c lire 77 E1 16` | **`42 4E 1E 00 2D 14 78 9C CD 66 9D D3 E6 12 E6 00`** | ✅ idem, second bloc |
| 4 | **`i2c ecrire 77 D0`** | **ACQUITTÉ**, `1 octet ENVOYÉ` | ✅ **écriture NUE** — le pointeur du BME680 est posé **sans lecture** |
| 5 | **`i2c brut 77 1`** | **`61`** | 🔴 **LE TÉMOIN CROISÉ** : le chip id relu **SANS index**, parce que (4) avait posé le pointeur. ⇒ `ecrire` et `brut` **coopèrent à travers DEUX invocations séparées** — c'est **exactement** le protocole que le BH1750 exigera (opcode, attente ≥ 180 ms, lecture) |
| 6 | **`i2c lire16 5D 8140 4`** | **`39 31 31 00`** | 🔴 = **`"911\0"` en ASCII**, le Product ID du GT911 — que `touch` publie déjà (`identite : « 911 »`). ✅ **L'index 16 bits fonctionne, prouvé sur un composant SOUDÉ dont la valeur était connue d'avance** |

#### Les témoins NÉGATIFS — sans eux, un témoin positif peut être une coïncidence

| Transaction | Rendu | Ce que ça écarte |
|---|---|---|
| `i2c lire 5D 40 4` (index **8 bits** sur un device **16 bits**) | `00 20 0A FE` | 🔴 **PAS `39 31 31`.** ⇒ l'ancien instrument **ne peut structurellement pas** lire ce que le neuf lit — la primitive n'est pas décorative |
| `i2c lire16 5D 0140 4` (mauvais index 16 bits) | `00 00 00 00` | ⇒ `"911"` ne sort **pas par accident** : c'est bien l'index `8140` qui le produit |
| `i2c lire16 80 0000` | **refus expliqué**, bornes annoncées | `0x78-0x7F` sont RÉSERVÉES par la spec I²C |
| `i2c ecrire 23 GG` | **refus**, `⛔ RIEN N'A ÉTÉ ENVOYÉ` | ⇒ la validation est **AVANT** l'écriture — une écriture partielle laisserait un état qu'on ne sait pas nommer |
| `i2c brut 77 99` | **refus**, bornes `1..16` | ⛔ jamais d'écrêtage silencieux |

#### Non-régression, mesurée après avoir exercé les primitives sur le bus

| Garde | Après |
|---|---|
| GT911 | **0 erreur I²C / 2 426 lectures** — et `0x5D` a pourtant reçu une écriture d'index 16 bits |
| BME680 | **`VIVANT`**, config `LUE (conforme)`, cadence **4 999 ms**, cycle **25 ms**, `err_i2c` **0** |

#### Le coût

| | Avant (`df5d23d`) | Après (`62e5f1d`) | Δ |
|---|---|---|---|
| Binaire | 943 712 o | **948 944 o** | **+5 232 o** (partition **77 %** libre) |
| Coût en **régime** | — | — | ⛔ **ZÉRO** — aucune tâche, aucun timer, aucune allocation permanente, aucune boucle, aucun `vTaskDelay` |

*(Référence historique : la commande `i2c` complète avait coûté +4 400 o en `dn2-1`.)*

⇒ **Le repli « qualification par stimulus physique » n'a PAS eu à être dégainé** : le budget d'essais
annoncé était de **3 variantes**, **une seule a été nécessaire**. Le stimulus reste néanmoins la
voie de qualification du **BH1750**, non par repli mais **parce qu'il n'a aucun registre d'identité**
(AC6).

---

### 13.16.4 🔴 LES DÉCISIONS DE T5 — prises AVANT le fer, et l'owner a corrigé le plan

**Toutes datées du 2026-08-19, toutes owner.** Elles sont écrites **avant** le geste, parce qu'après
il n'y a pas de retour en arrière.

#### Y2 — La topologie : l'owner a demandé de PIQUER, et il avait raison

**Demande owner, verbatim** : *« heu je ne peux pas les piquer dans la barre de connectique ? »*

⇒ **Il y a DEUX jonctions, et une seule demande le fer** — ce que ni la story ni l'epic n'avaient
séparé :

| Jonction | Verdict |
|---|---|
| **Côté CARTE** (header 2×12) | ✅ **Rien à souder** — le header est **déjà soudé**, des Dupont femelles s'y piquent |
| **Côté BREAKOUT** | 🔴 **Il FAUT souder** — les trois barrettes sont **fournies non soudées** (constaté sur les 9 photos) |

🔴 **ET C'EST MESURÉ, PAS SUPPOSÉ** : `dn2-1` a essayé exactement *« barrette insérée, non soudée »*.
§13.5 en garde les deux lignes — **hypothèse 3** *« contact mécanique absent »* → **« ÉLIMINÉE POUR
L'ALIMENTATION »** (les 3,3 V arrivaient bien), et **hypothèse 6** *« les fils de signal n'arrivent
pas, trous non soudés côté `SDA`/`SCL` »* → ✅ **« CONFIRMÉE — C'ÉTAIT ELLE »**.
⇒ **Une barrette posée conduit CERTAINES broches et pas d'autres.** C'est **pire** qu'un contact
absent : le capteur est alimenté, il a l'air vivant, et il ne répond jamais. Ça a coûté une séance.

✅ **Compatible avec D9, et vérifié dans son texte plutôt que supposé** : D9 justifie le soudé par
*« un Dupont n'est donné que pour quelques dizaines d'insertions »* — la contrainte visait les
**insertions RÉPÉTÉES**. Un connecteur piqué **une fois** et laissé en place n'en fait pas des
dizaines. ⇒ **Barrette soudée au breakout + Dupont côté carte** satisfait la raison de D9 et garde
le montage démontable.

⚠️ **UNE PRÉMISSE D'AC9 BOUGE, ET C'EST ÉCRIT PLUTÔT QUE LAISSÉ FILER.** D9 concluait *« en soudé,
plus aucun débranchement à chaud sans dessouder »*, et **AC9 en tire que la saturation logicielle est
« la seule voie restante »**. Avec des Dupont côté carte, **le débranchement à chaud du GROUPE
redevient possible** (⛔ pas module par module : la guirlande, elle, est soudée). ⇒ **AC7 (a) par le
fil redevient jouable**, et le mode « capteur fantôme » (§13.10) **redevient testable** — c'est un
**gain**. AC9 reste dû : trois devices de plus rendent la saturation réellement neuve.

> 🔴 **LES DEUX DÉCISIONS DE FIL CI-DESSOUS ONT ÉTÉ RÉFUTÉES PAR LA CARTE LE MÊME JOUR —
> renvoi ajouté par la revue de code du 2026-08-20, parce que sans lui un lecteur de cette
> sous-section souderait DEUX FILS INUTILES sur un montage fini.**
> - **`ADDR` du BH1750 est TIRÉ BAS par le GY-302** ⇒ `0x23` déterministe **sans fil** (mesuré : il
>   répond **5/5** avec les quatre fils de bus seulement).
> - **`XSHUT` du ToF est TIRÉ HAUT par le TOF050C** ⇒ la puce répond **fil retiré**.
> ⇒ **Aucun fil ajouté.** Voir **§13.16.8** et `firmware/desknode/main/dn_pins.h:169-171`.
> ⚠️ Le texte ci-dessous est **conservé tel qu'il a été écrit AVANT le fer** — c'est la trace de ce
> qui était su au moment de la décision, et la datasheet ROHM reste juste : c'est le **BREAKOUT**
> qui garantit `0x23` ici, **pas la puce**.

#### Y4 — `ADDR` du BH1750 : **fil vers `GND`** (décision owner)

La datasheet ROHM ne définit `0x23` que pour **`ADDR ≤ 0,3 × VCC`** ; **flottant est INDÉFINI**.
⇒ `0x23` devient **déterministe** pour le prix d'un fil. Le laisser en l'air aurait été accepter
qu'une adresse instable ressemble un jour à l'un des **~15 faux positifs** que le scan de cette carte
fabrique (§13.2).

#### `XSHUT` du ToF : **fil vers `3V3`** — ce n'est pas une option

Basse ou flottante, **la puce reste en shutdown et n'acquitte pas** : le symptôme **exact** de la
mauvaise soudure. Aucune photo ne dit si ce breakout la tire déjà haut ⇒ ⛔ **cela ne se suppose
pas**, on la tire.

### 13.16.4 bis 🔴 CE QUI A ÉTÉ VÉRIFIÉ **AVANT** LA MISE SOUS TENSION — AC5

> ⚠️ **AJOUTÉE PAR LA REVUE DE CODE DU 2026-08-20.** Ces quatre vérifications ont bien eu lieu en
> séance et étaient cochées dans la story — **mais aucune n'était consignée dans ce fichier**, qui
> est le document qui fait foi. Une garde qui n'existe que dans le compte rendu de la séance qui
> l'a exécutée n'est pas une garde, c'est un souvenir.

| Vérification | Instrument | Résultat |
|---|---|---|
| **Carte HORS TENSION** pendant tout le geste | 🔴 **disparition de `/dev/ttyACM0` côté hôte** ET sortie de `3-1` de la liste `usbipd` | ✅ **les deux constatés** |
| **Absence de pont `VCC`/`GND`** | ohmmètre, modules isolés | ✅ **`OL` sur les TROIS modules** |
| **Continuité** des 4 fils de bus | ohmmètre | ✅ |
| **Miroir** contrôlé breakout par breakout contre la table d'AC1 | lecture sérigraphie ↔ câble | ✅ — aucun des quatre ne s'aligne « premier avec premier », et **l'INA219 est le pire** (`Vin+`/`Vin-` en tête, c'est-à-dire le **shunt**, pas l'alimentation logique) |

⛔ **POURQUOI L'INSTRUMENT DE LA PREMIÈRE LIGNE EST CELUI-LÀ, ET PAS UN AUTRE** : la coupure ne se
prouve **ni** par `reboot` (`esp_restart()` laisse le rail 3V3 debout) **ni** par le retrait de
`VCC` (alimentation fantôme par les diodes ESD, §13.10). Seule la disparition du port côté hôte le
dit. **19 points de soudure, tous sur les modules, aucun sur la carte.**

---

#### `INT` du ToF : **NON CÂBLÉ** — c'est AC11

Décision écrite et entrée de ledger **fermée** : aucune broche d'interruption n'est câblée, le
polling suffit.

#### L'INA219 **EN SÉRIE** : décision owner = **PAS MAINTENANT**

⚠️ La question a d'abord été **mal comprise** — l'owner a répondu sur la **guirlande** (chaîner les
modules) alors qu'elle portait sur le **shunt** (faire passer un courant à mesurer par `Vin+`/`Vin-`).
**Reposée en la distinguant explicitement**, la réponse est : **bus seulement**.
⇒ `Vin+` et `Vin-` **restent libres**, le **bornier à vis reste NON SOUDÉ**, et l'INA219 est un
device de plus sur le bus, qualifié par `i2c lire 40 00 2` → **`39 9F`**. **`dn4-3` décidera ce qu'il
mesure.** ✅ *La réponse est écrite, même négative* — c'était l'exigence de la question n°2 du cadrage.

> 🔴 **CORRIGÉ PAR AJOUT — 2026-08-20, correct-course. ⛔ « le bornier à vis reste NON SOUDÉ » décrit
> l'INTENTION, PAS CE QUI A ÉTÉ FAIT.** La photo `2026-08-20_0116` de la **MÊME SÉANCE** montre
> *« bornier vert **SOUDÉ** »* (§ Inventaire, l. 84), et le **constat owner du 2026-08-20 le
> confirme : il EST soudé.** Deux lignes du même document se contredisaient ; ⛔ aucune n'est
> effacée, et c'est l'œil de l'owner qui tranche.
>
> ⚠️ **CE QUE ÇA CHANGE, ET C'EST EN NOTRE FAVEUR** : `Vin+`/`Vin−` sont **accessibles par un
> bornier à vis, SANS FER**. Remettre le shunt en service ne demande donc **aucune soudure** —
> dénuder la ligne 5 V d'un câble USB-C, la couper, **visser les deux bouts**. **Réversible en
> dévissant**, et ⛔ **sans toucher la carte** (dont le tracé d'alimentation n'est de toute façon
> **pas établi** : §14.3 de `…-affichage.md` classe le connecteur batterie, le chargeur et la portée
> de l'interrupteur ON/OFF en **hypothèse**).
>
> ⛔ **UNE CHOSE RESTE NON VÉRIFIÉE, ET ELLE NE SE SUPPOSE PAS** : que le bornier soit
> **électriquement relié à `Vin+`/`Vin−`**. C'est le câblage standard des breakouts CJMCU, mais
> **ce dépôt ne l'a JAMAIS mesuré** ⇒ **contrôle de continuité au multimètre** (patron `dn4-2` AC5)
> avant de compter dessus.
> ⛔ **Et `Vin+`/`Vin−` NE SONT PAS une alimentation** : y poser 5 V et la masse
> **court-circuiterait le shunt de 0,1 Ω**. *« Le miroir tue »* — le piège est déjà nommé plus haut.
>
> 🔴 **ET L'HISTOIRE S'EST TERMINÉE AUTREMENT** : `dn4-3` a bien décidé « ce qu'il mesure » — la
> réponse est **RIEN d'utile** — et le **correct-course du 2026-08-20 l'a SORTI DU RÉGIME**. Il
> reste **soudé, ouvert, configuré au boot, et INERTE**. Voir `epics-desknode-v1.md`, entrée INA219.

#### Le tableau ANTI-MIROIR de la guirlande, écrit avant le fer

🔴 **Le BH1750 et le ToF ont `SDA`/`SCL` dans l'ordre INVERSE l'un de l'autre.** Câbler « en face »
les croise.

| Signal du bus | **BH1750** | **ToF** | **INA219** |
|---|---|---|---|
| `3V3` | `VCC` — br. **1** | `VIN` — br. **1** | `Vcc` — br. **6** |
| `GND` | `GND` — br. **2** | `GND` — br. **2** | `Gnd` — br. **5** |
| `SDA` | `SDA` — br. **4** | `SDA` — br. **3** | `Sda` — br. **3** |
| `SCL` | `SCL` — br. **3** | `SCL` — br. **4** | `Scl` — br. **4** |

Plus : ~~**`ADDR`** (BH1750, br. 5) → `GND`~~ · ~~**`XSHUT`** (ToF, br. 6) → `3V3`~~ → 🔴 **NI L'UN NI
L'AUTRE : les deux sont tirés par le breakout, MESURÉ (§13.16.8). Aucun fil.** ·
⛔ **`INT`** (ToF, br. 5), **`Vin+`/`Vin-`** (INA219, br. 1-2) → **rien**.

**Point d'entrée sur la carte** : header **rangée B**, les 4 broches contiguës de bout de rangée
`SCL · SDA · 3V3 · G`. ⛔ **`RXD`/`TXD` sont juste derrière** (§13.1 bis).
⚠️ **Le BME680 reste sur l'embase JST** : le bus aura donc **deux points d'entrée physiques**, ce qui
est sans conséquence électrique — c'est le même bus — mais doit être **photographié** (AC5).

---

### 13.16.5 ✅ L'INSTRUMENT D'AC9 (`i2c rafale`) EXISTE, ET SA MISE À L'ÉPREUVE À 5 DEVICES DONNE LA RÉFÉRENCE À BATTRE

**Firmware `43e108f`, SHA LU AU BANDEAU**, `porcelain` vérifié **VIDE avant** le flash.
Bus **à 5 devices** (⛔ avant soudure), **sans appui** — c'est la référence « saturation seule ».

**Protocole** : `touch reset` (solo) → `touch` (solo, le relevé AVANT) → `i2c rafale 10000`
(solo, `--timeout 60`) → `touch` (solo, le relevé APRÈS). **Quatre invocations séparées**, parade de
§13.16.2.

| Grandeur | Mesuré |
|---|---|
| Durée **demandée** | 10 000 ms |
| Durée **réelle** | **10 003 ms** (+0,03 %) — ⚠️ **mesurée, pas déduite** |
| Passes complètes | **537** |
| Sondages émis | **60 144** |
| **Cadence** | 🔴 **6 012 sondages/s** · **53 passes/s** |
| Timeouts | **0** sur 60 144 |
| GT911 pendant la rafale | **292 lectures**, soit **~29 Hz** — sa cadence nominale |
| **Erreurs I²C GT911** | **0 avant · 0 après** |

⇒ ✅ **À 5 devices, une saturation à 6 012 sondages/s n'affame PAS le contrôleur tactile** : il tient
sa cadence nominale et n'enregistre **aucune** erreur. **C'est la référence que le bus à 8 devices
devra battre**, et le couple encadrant est publié comme AC8 l'exige — *« sans ces deux relevés on ne
le verrait pas »*.
⛔ **Ce que ce relevé NE dit PAS** : il n'y a **eu aucun appui**. AC9 exige que **l'owner appuie
pendant la rafale et dise ce qu'il ressent** — *« un compteur seul ne peut pas répondre à "le tactile
est-il fâché" »*. Ce relevé est le **témoin sans stimulus**, pas le verdict.

#### 🔴 EFFET DE BORD : LE TAUX DE FAUX POSITIFS DU SONDAGE EST MESURÉ SUR UN ÉCHANTILLON **27× PLUS GRAND**, ET IL CONFIRME §13.2

La rafale compte ses acquittements. À 5 devices réels et 537 passes, on attend **2 685**
acquittements ; il en est venu **3 110**.

| | |
|---|---|
| Acquittements **en trop** | **425** |
| Par passe | **0,79 fantôme** |
| Sondages d'adresses **vides** (537 × 107) | **57 459** |
| **Taux de faux positif par sondage d'adresse vide** | 🔴 **0,740 %** |
| Estimation historique de §13.2 (~15 fantômes en ~20 scans) | **0,75 par passe** |

⇒ ✅ **L'estimation « à la louche » de `dn2-1` était JUSTE à 5 % près**, et elle est désormais
confirmée par un échantillon **27 fois plus grand**, par un chemin de code **différent**, et **sans
qu'aucune passe n'ait été imprimée** — donc sans le biais de capture de §13.2.
⚠️ **425 est un PLANCHER, pas une valeur exacte** : le calcul suppose que les 5 devices réels ont
acquitté à **chaque** passe. §13.2 a mesuré des **faux négatifs** sur composants soudés — s'il y en a
eu ici, les fantômes sont **plus nombreux** que 425, jamais moins.
⛔ **Et ça ne change RIEN à la règle** : le scan **découvre**, seule une transaction de donnée
**qualifie**. Ce chiffre la **renforce** — 0,74 % par adresse vide, c'est **près d'un fantôme par
passe**, dans un balayage qui en fait 53 par seconde.

---

### 13.16.6 ✅ L'INA219 EST SUR LE BUS ET QUALIFIÉ — et il **RÉFUTE** le verdict d'AC7 sur son propre témoin

**Firmware `43e108f`, SHA LU AU BANDEAU.** Bus à **6 devices** (BME680 + INA219 + les 4 de la carte).
Boot **2 320 ms** (T0 : 2 319), **aucune ligne d'erreur nouvelle**.

#### Le montage, décidé par l'owner et corrigé PAR l'owner

🔴 **Le header 2×12 de la carte est une embase FEMELLE**, pas des broches mâles — **constat owner,
carte en main**, confirmé ensuite au zoom sur `docs/cablage/2026-08-16_2228-…jpg` (cavités carrées,
contacts dorés au fond). **Le dépôt ne l'avait jamais noté**, et ça décide du type de câble :
**MF** (mâle côté carte, femelle sur la broche du module), ⛔ pas FF.
⚠️ **L'agent avait donné la consigne inverse** ; c'est l'owner qui l'a réfutée. *L'œil de l'owner est
l'instrument.*

⛔ **Une seule cavité `SCL` et une seule cavité `SDA`** ⇒ **UN module à la fois** sur le header.
L'embase JST — le second point d'entrée du bus — **est prise par le BME680**. ⇒ Les trois modules
sont qualifiés **un par un**, ce qui est **méthodologiquement meilleur** : un module qui ne répond
pas n'a **aucune ambiguïté** sur son identité, alors que brancher les trois puis scanner recrée la
séance de `dn2-1` où l'on cherchait quelle hypothèse tombait.

#### Le scan — 5 passes en invocations SOLO, invariant vérifié sur chacune

| Passe | Adresses | Bilan | Invariant | Témoin |
|---|---|---|---|---|
| 1 | `0x20` `**0x2F(1/5)**` `0x40` `0x51` `0x5D` `0x6B` `0x77` | 6 st + 1 inst, 32 ms | ✅ 7 = 7 | ✅ |
| 2 | `0x20` `**0x3B(1/5)**` `0x40` `0x51` `0x5D` `0x6B` `0x77` | 6 st + 1 inst, 33 ms | ✅ 7 = 7 | ✅ |
| 3 | `0x20` `0x40` `0x51` `0x5D` `0x6B` `0x77` | 6 st + 0, 32 ms | ✅ 6 = 6 | ✅ |
| 4 | `0x20` `0x40` `0x51` `0x5D` `0x6B` `0x77` | 6 st + 0, 32 ms | ✅ 6 = 6 | ✅ |
| 5 | `0x20` `**0x29(1/5)**` `0x40` `0x51` `**0x52(1/5)**` `0x5D` `0x6B` `0x77` | 6 st + 2 inst, 39 ms | ✅ 8 = 8 | ✅ |

⇒ **`0x40` à `5/5` sur les CINQ passes.**

🔴 **ET LA PASSE 5 OFFRE UNE PREUVE GRATUITE ET DATÉE QUE LE SCAN NE QUALIFIE RIEN** : elle sort
**`0x29` à 1/5** — **l'adresse du ToF, qui n'était PAS branché**. Si le ToF avait été là, ce `1/5` se
serait lu comme un **mauvais contact**, et la séance serait partie chercher une soudure. §13.2
annonçait que la liste des fantômes *« contient `0x29` ET `0x40` »* ; la voici prise sur le fait.

#### La qualification — par la DONNÉE, jamais par le scan

| Transaction | Rendu | Attendu |
|---|---|---|
| `i2c lire 40 00 2` (Configuration) **×5** | 🎯 **`39 9F` · 5 fois sur 5** | `399F` = reset, TI **SBOS448G** §8.6.2.1 |
| `i2c lire 40 05 2` (Calibration) **×2** | **`00 00`** | contrôle négatif ✅ |
| `i2c lire 40 01 2` (Shunt Voltage) | `00 00` | shunt libre, cohérent |
| `i2c lire 40 02 2` (Bus Voltage) | **`07 0A`** | ⇒ **bit `CNVR` = 1 : l'ADC a CONVERTI.** ⚠️ Le reset de `02h` est `0000` — **c'est une valeur que la puce PRODUIT**, pas une qu'elle hérite |

#### 🔴 AC7 EST RÉFUTÉ POUR L'INA219 — son témoin anti-fantôme est FORT, pas faible

**Ce que la story écrivait** : *« un témoin existe mais il est FAIBLE, et sa faiblesse est nommée —
c'est le cas de l'INA219, qui se qualifie par sa valeur de reset, donc exactement à la manière de
`Control_1` : ⛔ il ne peut pas distinguer "sain au repos" de "redémarré". »*

**Ce que la mesure dit** :

```
i2c lire   40 05 2      →  00 00      état de départ, RELU et journalisé AVANT d'écrire
i2c ecrire 40 05 D7 A4  →  ACQUITTE   on IMPOSE une valeur, on ne CONSTATE pas
i2c lire   40 05 2      →  D7 A4      ✅ le temoin est POSE et RELU
i2c lire   40 05 2      →  D7 A4      ✅ et il SURVIT en regime
```

⇒ Le registre **Calibration (`05h`) est INSCRIPTIBLE, RELISIBLE, et sa valeur de reset (`0000`)
DIFFÈRE de la valeur imposée (`D7A4`)** — **les trois propriétés exactes** que §13.15.4 exige d'un
témoin valide, et que le `Control_1` du RTC n'avait justement **pas** (sa valeur de reset **était**
celle du défaut, d'où une garde *« verte pendant le défaut qu'elle prétend détecter »*).

✅ **L'INA219 passe donc de « témoin FAIBLE » à « témoin FORT »**, du même type que le
`RAM_byte = 0xD7` de la RTC, et selon le **même patron** : *relire d'abord, journaliser, puis écrire*.
⚠️ **Et c'est la primitive `i2c ecrire` construite en T4 qui l'a rendu possible** — sans écriture nue,
on ne pouvait qu'**observer**, jamais **imposer**. L'instrument réparé a produit un résultat que la
story n'attendait pas de lui.
⚠️ **Ce que ce témoin ne prouve toujours pas** : qu'un INA219 alimenté **parasitement** ne saurait pas
accepter l'écriture. §13.10 n'a jamais mesuré ce cas sur cette puce. ⇒ **La garde est possible ;
`dn4-3` l'écrira, et c'est à elle de la mettre à l'épreuve.**

#### Non-régression à 6 devices

| Garde | Mesuré |
|---|---|
| `touch` **encadrant** (avant / scan complet / après) | **0 erreur I²C · 0 erreur I²C** |
| BME680 | `config LUE (conforme)` · cadence **4 999 ms** · `err_i2c` **0** |
| Bandeau de boot | **aucune ligne d'erreur nouvelle** ; seule reste la ligne ISR d'AC11 |

#### ✅ CONSTAT OWNER À L'ŒIL (AC5), cité verbatim

Question groupée posée en trois points ; réponses : **« A »** (le dashboard s'affiche), *« ok »* pour
le rétroéclairage allumé fixe, *« tt est ok »* pour l'absence d'anomalie — **et une précision
spontanée de l'owner** : *« mais seul le temps humidité est vivant »*.

✅ **C'est le comportement ATTENDU, et c'est précisément ce que `D6` voulait rendre VISIBLE.** Les
cinq autres cases sont nourries par l'agent qui tourne **sur la tour Windows via `COM3`**, et `COM3`
**n'existe pas** tant que la carte est attachée à WSL — l'exclusivité est stricte et mesurée depuis
`dn2-2`. ⇒ **Pendant toute séance carte, les 5 cases PC sont nécessairement mortes**, et la seule
case vivante est celle qui **peut** l'être. ⛔ **Ce n'est pas une régression** : *« le mock MASQUAIT
le déséquilibre que D6 avait annoncé ; le supprimer le REND VISIBLE. »*
⚠️ **À dire chaque fois qu'on publiera un constat d'écran en séance carte**, sinon un lecteur futur
le lira comme un défaut.

---

### 13.16.7 🎯 AC2 SOLDÉ — **LE ToF EST UN VL6180X**, et l'étiquette mentait depuis cinq jours

**Firmware `43e108f`, SHA lu au bandeau.** Bus à **6 devices** (BME680 + ToF).

| Hypothèse | Transaction | Rendu | Verdict |
|---|---|---|---|
| **VL6180X** | `i2c lire16 29 0000` — index **16 bits** | 🎯 **`B4` · 5 fois sur 5** | ✅ **CONFIRMÉE** |
| **VL53L0X** (témoin négatif) | `i2c lire 29 C0` · `C1` · `C2` — index **8 bits** | **`01` · `00` · `00`** | ⛔ **RÉFUTÉE** (attendu `EE`/`AA`/`10`) |

**Registres d'identité complémentaires** (index 16 bits) : `0x0001` = `01` · `0x0002` = `03` ·
`0x0003` = `02` · `0x0004` = `00` ⇒ **modèle rév. 1.3, module rév. 2.0**.
Scan : `0x29` à **`5/5` sur 3 passes**, invariant vérifié, témoins verts.

⇒ 🔴 **Le brief, l'epic, le tracker, `dn_pins.h`, `i2c_nom_connu()` et six stories se trompaient
depuis le 2026-08-14.** L'addendum §3 avait **posé** la question — *« noter la réf réelle du breakout
à l'inventaire »* — et personne ne l'avait fermée. **Fermée par la lecture, pas par l'étiquette.**
⚠️ Et il a fallu **construire l'instrument** pour ça : `i2c lire16` n'existait pas ce matin, et
`i2c lire` **ne pouvait structurellement pas** poser un index de 2 octets.

#### 🔴 Y5 FERMÉ PAR LA MESURE, ET LA RÉPONSE EST L'INVERSE DE LA PRÉCAUTION

**`XSHUT` est TIRÉ HAUT sur ce breakout.** Preuve : la puce rend **`B4` cinq fois sur cinq avec le
fil RETIRÉ**, alors que la datasheet ST est formelle — `XSHUT` basse ou flottante ⇒ **shutdown, pas
d'acquittement**. ⇒ **Le fil n'était pas seulement inutile : c'est lui qui a tué le bus** (ci-dessous).

⇒ **DÉCISION : `XSHUT` n'est PAS câblé**, et c'est une décision **mesurée**, pas une précaution.
Les trois usages de la broche sont sans objet ici : endormir (**D4** range le ToF en bonus post-V1),
reset matériel (on a le cycle d'alimentation), et **mettre DEUX VL6180X sur le bus** — son vrai usage,
l'adresse `0x29` étant fixe et reprogrammable seulement en RAM. **On en a un.**
⚠️ **Résiduel écrit** : on s'appuie sur le tirage du breakout, pas sur un fil à nous. **Si le ToF
devient un jour intermittent, `XSHUT` est le premier suspect à re-nommer — pas la soudure.**

#### 🔴 L'INCIDENT : LE 5ᵉ FIL A TUÉ LE BUS ENTIER, ET LE MÉCANISME N'EST **PAS** ISOLÉ

**Symptôme, au boot** : `E dn_disp: expander_bring_up(191): TCA9554 muet à 0x20` puis
`E dn_disp: dn_display_init(451): étape 2/5`. **`0x20` est sur la CARTE et c'est l'un des deux
témoins positifs** ⇒ ce n'était pas *« le ToF ne répond pas »*, c'était *« plus rien ne répond »*.
`dn_display_init()` étant sous `ESP_ERROR_CHECK`, la panique a **halté le CPU** (§8 des pièges) :
**plus de console non plus** — le pilote n'obtenait plus l'invite. **Troisième état.**

C'est mot pour mot **l'hypothèse 1 de §13.5** : *« SCL serait tiré à la masse ⇒ le bus mourrait »*.

**Bissection, une seule variable annoncée** : retirer **uniquement** le fil `XSHUT`, couper
l'alimentation, rebrancher. ⇒ **Le bus est revenu du premier coup** : plus d'erreur `TCA9554`,
console vivante, `0x20` et `0x5D` à `5/5`, et le ToF répond.

⚠️ **CONSTAT OWNER SUR L'EMPLACEMENT** : *« XSHUT était sur le 3V3 de l'autre côté »* — c'est-à-dire
**la cavité `3V3` de la rangée A, l'emplacement DEMANDÉ**. ⇒ 🔴 **LE MÉCANISME N'EST PAS EXPLIQUÉ** :
un fil vers `3V3` ne devrait pas tuer un bus I²C.

⛔ **ET LA CONCLUSION « c'était XSHUT » N'EST PAS PROUVÉE** : un seul essai a changé **DEUX choses** —
le fil retiré **et** un cycle d'alimentation (qui a pu reseater un contact). *Bouger → ça marche* est
exactement le raisonnement que ce dépôt refuse. **Le test de reproduction n'a pas été fait** —
arbitrage owner, et il se défend : `XSHUT` ne sera **pas** câblé, donc le fil n'existera plus.
⇒ **Écrit comme : « corrélation forte, mécanisme NON ISOLÉ, une variable non séparée du cycle
d'alimentation ».**
⚠️ **Hypothèse la plus plausible, à traiter comme telle** : la cavité `3V3` (rang 11) est **voisine
de `G` (rang 12)** sur la même rangée ; un pin mal enfoncé ou de travers **pontant `3V3` et `G`**
produirait un affaissement partiel du rail — assez pour faire taire le TCA9554 sans empêcher l'ESP
de démarrer ni le rétroéclairage de s'allumer. ⇒ **`dn4-5` (installation définitive) doit le savoir :
une cavité ou un pin capricieux se re-tendra.**

---

### 13.16.8 🎯 AC6 SOLDÉ POUR LES TROIS — et **le BH1750 est le plus fortement qualifié des trois**

#### Y4 fermé par la mesure, symétriquement à Y5

**Le BH1750 a été branché avec les 4 fils de bus SEULEMENT, ⛔ sans fil `ADDR`** — délibérément,
pour que la carte réponde à la question au lieu qu'on la contourne.
⇒ **`0x23` répond `5/5` sur CINQ passes**, et `0x5C` n'apparaît **nulle part**.
⇒ **`ADDR` est TIRÉ BAS sur le GY-302.** L'adresse est déterministe **sans fil supplémentaire**.

🔴 **DEUX PRÉCAUTIONS ÉCRITES D'AVANCE, DEUX FOIS RÉFUTÉES PAR LA CARTE** : `XSHUT` tiré haut,
`ADDR` tiré bas. Les deux breakouts mettent leur broche spéciale **dans l'état sûr**. ⚠️ Ça ne rend
pas les précautions inutiles — **elles étaient indispensables tant que ce n'était pas mesuré**, et
la datasheet ROHM ne définit toujours `0x23` que pour `ADDR ≤ 0,3 × VCC`. **Ce qui a changé, c'est
qu'on a la mesure.**

#### 🔴 LE PIÈGE DE CADENCE S'EST DÉCLENCHÉ EN DIRECT, ET LE CODE L'AVAIT ANNONCÉ

```
i2c ecrire 23 01   ->  ACQUITTE, opcode POWER ON
i2c ecrire 23 10   ->  ACQUITTE, mesure CONTINUE haute resolution (120-180 ms)
i2c brut   23 2    ->  00 00  =  0,0 lx     <- 🔴 MESURE PAS ENCORE PRETE
i2c brut   23 2    ->  00 17  =  19,1 lx
i2c brut   23 2    ->  00 17  =  19,1 lx
i2c brut   23 2    ->  00 17  =  19,1 lx    <- stable
```

⇒ **La première lecture rend `00 00`.** Une lecture unique aurait **déclaré mort un capteur qui
fonctionne** — exactement le faux négatif que la story avait armé d'avance et que la sortie de
`i2c ecrire` imprime en garde. **Le piège n'est plus théorique : il est daté.**

#### Le stimulus — geste owner, lecture agent, ⛔ jamais l'inverse

| État | Geste **owner** | Brut | Lux | Lectures |
|---|---|---|---|---|
| **départ** | — | 23 | **19,1 lx** | 3, identiques |
| **masqué** | main posée sur le capteur | 0 | **0,0 lx** | 3, identiques |
| **retiré** | main retirée | 28 | **23,3 lx** | 3, identiques |

> 🔴 **LA COLONNE « 3, IDENTIQUES » N'EST PAS UNE PREUVE DE VIE — RÉFUTÉE PAR LA MESURE LE
> 2026-08-24, VOIR §13.22.4.** Un BH1750 **éteint** rend la **dernière mesure, FIGÉE** (mesuré :
> `211 · 211 · 211`), parce que le power down **ne vide pas** le registre de données ; et un bus qui
> lit des uns rend `FFFF` **trois fois**. ⇒ Le critère est satisfait par **deux états morts**.
> ⚠️ **Ce qui sauve CE relevé-ci**, c'est qu'il ne repose pas sur la colonne : il repose sur le
> **RAPPORT** entre trois états (`19,1 → 0,0 → 23,3`), et **une valeur qui change sous stimulus est
> le seul discriminant valide**. Le verdict d'AC6 **tient donc**, ⛔ mais pas par l'argument que
> cette colonne suggère.
| **éclairé** | 🔦 lampe du téléphone | **55 378** | 🎯 **46 148,3 lx** | 3 (46 058,3 puis 46 148,3 ×2) |

⇒ **Quatre décades, dans les DEUX sens, sous le geste de l'owner.**

✅ **DEUX DÉTAILS QUI FONT LA PREUVE, ET PAS SEULEMENT LE CHIFFRE** :
> 🔴 **LES LUX DE CE RELEVÉ ONT ÉTÉ CORRIGÉS LE 2026-08-20 PAR LA REVUE DE CODE — ILS ÉTAIENT
> DIVISÉS PAR DIX, ET C'EST LA CLASSE DE DÉFAUT QUE CE CHAPITRE TRAQUE.**
> `dn_console.c` calculait `lux10 = (brut * 10) / 12`, ce qui **EST déjà la valeur en lux entiers**
> (`brut / 1,2`), puis l'imprimait comme des **dixièmes**. Publié ici et dans le `README.md` :
> `1,9` pour **19,1** · `2,3` pour **23,3** · **`4 614,8` pour `46 148`**.
> ⚠️ *Cette ligne écrivait **`19,2`** jusqu'à la revue du **2026-08-24** — un chiffre que la formule
> corrigée **ne peut pas produire** : `(23 × 100) / 12 = 191` ⇒ le firmware imprime **`19.1`**, la
> table ci-dessous publie **19,1**, et l'encart dit lui-même deux lignes plus bas que le dixième est
> **tronqué, pas arrondi**. `19,2` est l'**arrondi** de 19,166… Le cas jumeau `2,3 → 23,3` est exact,
> donc la contradiction ne se voyait que sur le seul des deux exemples où troncature ≠ arrondi.*
> ⚠️ **AC6 tient, et ce n'est pas une concession** : le stimulus qualifie par le **RAPPORT** — main
> posée → main retirée → lampe — et **les rapports étaient justes**. Le verdict « le BH1750 répond
> à une main » n'est pas touché.
> ⛔ **Mais « 4 614,8 lx sous une lampe de téléphone » était plausible**, et c'est ce qui a permis
> au chiffre de passer trois publications sans être recalculé. *« Un chiffre faux mais plausible
> est plus dangereux qu'un chiffre absurde. »*
> ⚠️ Les valeurs ci-dessus sont **recalculées depuis le BRUT publié**, qui lui n'a jamais bougé —
> ⛔ pas re-mesurées sur la carte. Le dixième est **tronqué**, pas arrondi.

1. **Le retour n'est pas identique au départ** (23,3 contre 19,1 lx). Une valeur **rejouée** serait
   revenue **exacte**. Une vraie pièce dérive.
2. **La lampe lève l'ambiguïté du `00 00`** : masqué, le capteur rend `00 00`, ce qui est **aussi**
   ce que rend une mesure pas prête. Le masquage seul était donc **faible**. **46 148 lx ne peut
   venir que de la lumière.**
   ⚠️ *Cette phrase a gardé l'ancienne valeur **`4 615`** jusqu'à la revue de code du **2026-08-24**,
   quatre lignes sous l'encart qui déclarait avoir tout recalculé, et alors que le point **1**
   ci-dessus avait bien été repris. **C'est la phrase qui PORTE la preuve** — donc le pire endroit
   où l'oublier. Le `grep` de §13.17.6 bis est exactement ce qui l'aurait trouvée.*

🔴 **POURQUOI LE BH1750 EST LE MIEUX QUALIFIÉ DES TROIS, ET PAS LE MOINS BIEN.** L'INA219 et le
VL6180X rendent chacun **un octet constant** (`39 9F`, `B4`) — un faux positif de bus peut acquitter
et peut rendre des octets. **Il ne répond pas à une main.** Privé de registre d'identité, le BH1750
se trouve qualifié par **l'instrument le plus discriminant du lot**, et c'est ce que la story avait
écrit *avant* de le mesurer.
⚠️ **Et ça n'aurait pas été possible ce matin** : `i2c ecrire` (opcode sans lecture) et `i2c brut`
(lecture sans index) **n'existaient pas**, et `i2c lire` aurait **piloté le capteur au hasard** au
lieu de le lire.

#### Non-régression, à 6 devices, sur chacun des trois montages

| Montage | `touch` avant → après (scan complet entre) | BME680 | `fps 15` |
|---|---|---|---|
| **INA219** | **0 err → 0 err** | `config LUE (conforme)`, 4 999 ms, 0 err | — |
| **ToF** | **0 err → 0 err** | `config LUE (conforme)`, 0 err | **37,40 Hz, +0,00 %** |
| **BH1750** | **0 err → 0 err** | `config LUE (conforme)`, 0 err | — |

Bandeau de boot : **aucune ligne d'erreur nouvelle** sur les trois montages ; seule reste la ligne
ISR d'AC11.

---

### 13.16.9 AC7 — le mode « capteur fantôme » instruit pour les trois, **une ligne par capteur**

Rappel du mécanisme (§13.10) : `VCC` retiré, le composant reste **alimenté parasitement par les
tirages du bus à travers ses diodes de protection ESD**. Assez pour **acquitter**, pas assez pour
**tenir sa configuration** ⇒ un troisième état : **présent, bavard, `5/5`, valeurs fausses ET
plausibles**. Le patron de parade (§13.15.4) **impose** une valeur au lieu d'en **constater** une —
parce que le `Control_1` du RTC avait sa valeur de reset **égale** à celle du défaut, donc une garde
*« verte pendant le défaut qu'elle prétend détecter »*.

| Capteur | Verdict AC7 | Preuve |
|---|---|---|
| **INA219** `0x40` | ✅ **UN TÉMOIN EXISTE, ET IL EST FORT** — ⚠️ **la story le disait FAIBLE** | Registre **Calibration `05h`** : **inscriptible**, **relisible**, et sa **valeur de reset (`0000`) DIFFÈRE de la valeur imposée**. Vérifié : `00 00` relu **avant** d'écrire (journalisé), `D7 A4` imposé, `D7 A4` relu **deux fois**. Les **trois** propriétés de §13.15.4, que `Control_1` n'avait pas |
| **VL6180X** `0x29` | ⏳ **UN TÉMOIN EXISTE PROBABLEMENT, ⛔ NON VÉRIFIÉ SUR LA CARTE** | ST expose **`SYSTEM__FRESH_OUT_OF_RESET` (`0x0016`)**, qui vaut **`0x01`** à la sortie de reset et que l'hôte est **censé** remettre à `0x00` — c'est un détecteur de redémarrage **prévu par le constructeur**. ⛔ **Non mesuré** : le ToF avait déjà été retiré du montage quand la question s'est posée. ⇒ **à vérifier en `dn4-3`**, avec la primitive `i2c lire16`/`i2c ecrire` qui existe désormais |
| **BH1750** `0x23` | ⛔ **AUCUN TÉMOIN — écrit comme tel, pas contourné** | Il n'a **aucun registre inscriptible RELISIBLE**. Le seul écrivable est le **`MTreg`**, et il **n'est pas relisible** |

#### 🔴 LA PISTE `MTreg` A ÉTÉ TENTÉE POUR LE BH1750, ET ELLE A ÉCHOUÉ — écrit pour que personne ne la retente à l'aveugle

**L'idée** : le `MTreg` n'est pas relisible, mais il **change l'échelle de la mesure** (facteur
`MTreg/69`). On pouvait donc l'**imposer** et **l'observer indirectement** — ce qui aurait satisfait
le patron de §13.15.4 sans registre relisible.

**Essai 1** (`MTreg` 69 → 254 → 69, deux lectures par état) :

| État | Brut lus |
|---|---|
| référence (69) | 24 · 24 |
| **imposé (254)** | 24 · 24 — **aucun changement** |
| retour (69) | 🔴 **88** · 24 |

⚠️ **`88 = 24 × 3,67`, et `254/69 = 3,681`.** Le facteur est **exact**. L'hypothèse formée sur le
coup : les lectures ont **un cycle de retard** (le même phénomène que le BME680, `deferred-work`),
et le `88` serait la mesure faite à `MTreg = 254` arrivée trop tard.

**Essai 2, protocole corrigé** (4 à 6 lectures par état pour absorber le retard), **budget d'essais
annoncé à UN essai supplémentaire** :

| État | Brut lus |
|---|---|
| référence (69) | 23 · 23 · 23 · 23 |
| **imposé (254)** | 23 · 23 · 23 · 23 · 23 · 23 |
| retour (69) | 23 · 23 · 23 · 23 · 23 · 23 |

⇒ 🔴 **NON REPRODUCTIBLE. Le `MTreg` n'a pas pris.** Le `88` isolé reste **INEXPLIQUÉ**.
⛔ **Budget dépensé, on s'arrête** — *« se donner un budget d'essais et l'annoncer »*. Construire une
conclusion sur une observation **unique et non reproduite** est exactement ce que ce dépôt refuse,
et le facteur exact la rendait d'autant plus tentante.

⏳ **Hypothèse NOMMÉE pour qui reprendra**, ⛔ non testée : les bibliothèques usuelles envoient
`0x01` (power on) **puis** les deux octets de `MTreg` **puis** le mode. Ici le capteur était **déjà
en mode continu** quand `MTreg` a été écrit. ⇒ **Essayer la séquence complète depuis le power-on
avant de conclure que la piste est morte.**

#### Ce qui est porté à `dn4-3`, et ce que cette story ne fait PAS

⛔ **Cette story n'écrit AUCUNE garde de régime** — elle établit **ce qui est possible**. `dn4-3`
écrira les gardes, et elle hérite de trois choses : un témoin **FORT** pour l'INA219 (utilisable
tel quel), une **piste constructeur à vérifier** pour le VL6180X, et **aucun témoin** pour le
BH1750, avec la piste `MTreg` documentée comme **tentée et non reproduite**.
⛔ **Et l'injecteur `capteurs simuler` n'est PAS une parade** : *« il exerce le chemin de code,
jamais le bus »*, et *« il ne peut pas découvrir un mode de panne qu'on n'a pas imaginé »*.

---

### 13.16.10 🎯 LE BUS À **HUIT** DEVICES — AC8, et le montage s'est fait EN TROIS TEMPS pour une raison

**Firmware `43e108f`, SHA lu au bandeau.** ⚠️ **Le header n'a qu'UNE cavité `SCL` et UNE `SDA`**, et
l'embase JST est prise par le BME680 ⇒ **un module à la fois en direct**. L'owner a fabriqué
**quatre câbles de dérivation** (§13.0) : deux **Y à 3 sorties** pour `SDA` et `SCL`, deux **Y à 2**
pour `3V3` et `GND` — `3V3` et `G` existant sur **les deux rangées**, deux sorties y suffisent.

#### Les huit occupants, et l'absence de collision est CONSTATÉE

| Passe (invocation SOLO) | Adresses `5/5` | Bilan | Invariant | Témoin |
|---|---|---|---|---|
| 1 | `0x20 0x23 0x29 0x40 0x51 0x5D 0x6B 0x77` | 8 st + 0 inst, 38 ms | ✅ | ✅ |
| 2 | idem | 8 st + 0 inst, 37 ms | ✅ | ✅ |
| 3 | idem | 8 st + 3 inst, 44 ms | ✅ | ✅ |
| 4 | idem | 8 st + 1 inst, 39 ms | ✅ | ✅ |
| 5 | idem | 8 st + 1 inst, 41 ms | ✅ | ✅ |

⇒ **`0x20 · 0x23 · 0x29 · 0x40 · 0x51 · 0x5D · 0x6B · 0x77`** — les huit attendues, **aucune
collision**, sur les cinq passes. Durée du scan : **37-44 ms** contre **27-32 ms à 5 devices**
(≈ +4,5 ms par device ajouté, cohérent avec la re-sonde ×5).

#### Les gardes à 8 devices

| Garde | Mesuré |
|---|---|
| **`touch` encadrant** (scan complet entre les deux relevés) | **0 erreur I²C · 0 erreur I²C** |
| BME680 | `chip id 0x61`, `config LUE (conforme)`, cadence **4 999 ms**, **0 erreur** |
| `fps 15` | **37,40 Hz**, écart **−0,00 %** |
| RTC | ⚠️ `OS = 1` **ATTENDU** — voir ci-dessous |
| Bandeau de boot | **1 seule ligne `E`** : celle de l'ISR (AC11), **aucune nouvelle** |

⚠️ **`OS = 1` N'EST PAS UNE RÉGRESSION, C'EST UNE GARDE QUI SE DÉCLENCHE.** §13.15.3 a mesuré que
**cette carte n'a AUCUNE sauvegarde RTC**. Le montage en trois temps a demandé **une dizaine de
coupures USB** ⇒ l'oscillateur s'est arrêté, l'heure lue est devenue `2000-01-01 00:00:43`, et
**la barre a affiché « --:-- HEURE NON POSÉE »** au lieu d'une heure fausse. ⇒ **La garde de `dn3-2`
est prouvée EN CONDITIONS RÉELLES**, ce qu'aucune séance n'avait fait. L'heure a été reposée
(`rtc set`) : `FIABLE`, `OS = 0`, témoin `0xD7` vert.

#### 🔴 L'INCIDENT DU MONTAGE — et pourquoi les trois temps ont sauvé la mesure

**Premier essai, deux modules d'un coup** : le bus s'est dégradé. Symptômes capturés au bandeau —
`dn_capt: identite INATTENDUE : chip id 0x00`, puis **un flot d'erreurs `GT911: I2C read error!`
de 5 100 ms à 8 146 ms**, ~30 par seconde. Sur une occurrence, la carte a **paniqué et halté**
(voir §13.16.11).

🔑 **Mais le scan, lui, voyait `7/7` à `5/5`, témoin positif vert, en 36 ms.** ⇒ **Le bus n'était pas
mort : il était INTERMITTENT.** Les sondages courts (9 bits) passaient à 100 % ; les **transactions
longues** — lecture multi-octets du GT911, bloc d'étalonnage du BME680 — rataient. Sur cette
occurrence : **58 erreurs I²C sur 1 479 lectures GT911 = 3,9 %.**

**Puis, sur une fenêtre chronométrée de 15 s : 435 lectures, ZÉRO erreur.** ⇒ **La dégradation est
TRANSITOIRE et se produit AU BOOT**, pas en régime.

🔴 **CE PARAGRAPHE A ÉTÉ ÉCRIT FAUX, PUIS CORRIGÉ PAR UNE REPRODUCTION — ET LES DEUX VERSIONS SONT
CONSERVÉES, PARCE QUE L'ERREUR EST INSTRUCTIVE.**

**Ce qui était écrit** : *« 1 échec sur 4 démarrages, non reproduit sur 3 essais. Cause NON ISOLÉE.
Le plus plausible est l'instant du branchement plutôt que le régime. »* Les trois redémarrages à
7 devices étaient bien propres — comptés **en Python**, ⛔ pas par `grep -c` que le hook `rtk` a déjà
faussé dans ce dépôt : **0 `identite INATTENDUE`, 0 erreur GT911, 0 expander muet, 0 `abort()`,
`chip id 0x61` sur les trois**.

🔴 **Puis le défaut S'EST REPRODUIT**, sur un rebranchement physique ultérieur : `identite
INATTENDUE = 1`, **`abort() = 1`**, `chip id 0x61 = 0`. ⇒ **carte haltée, console morte.**

**Et en recomptant TOUS les démarrages depuis que des modules sont sur le bus, un motif apparaît que
le premier dépouillement avait manqué :**

| Type de démarrage | Résultats | Échecs |
|---|---|---|
| 🔴 **Rebranchement PHYSIQUE** (démarrage à FROID) | ❌ ❌ ✅ ❌ | **3 sur 4** |
| ✅ **`--reset`** (impulsion RTS, **alimentation maintenue**) | ✅ ✅ ✅ ✅ | **0 sur 4** |

⇒ 🔴 **CE N'EST PAS « TRANSITOIRE ET NON ISOLÉ ». C'EST UN DÉFAUT DE DÉMARRAGE À FROID,
REPRODUCTIBLE, QUE LE RESET CHAUD NE MONTRE JAMAIS.** **3 échecs sur 8 démarrages** au total.

⚠️ **CE QUE ÇA IMPLIQUE POUR LE PRODUIT, ET C'EST LE POINT** : DeskNode est censé démarrer **seul,
quand la tour est mise sous tension** (le différenciateur du brief). Le **démarrage à froid EST le
mode de fonctionnement normal du produit** — et il échoue **trois fois sur quatre**, en **briquant la
carte** (§13.16.11). ⛔ **Ce n'est pas un artefact de séance.**

⚠️ **Hypothèses NOMMÉES, aucune vérifiée** — ⛔ à ne pas confondre avec un diagnostic :
1. **Séquence de démarrage des capteurs** : à froid, les trois modules s'alimentent **en même temps**
   que l'ESP32. Le VL6180X en particulier a sa propre séquence de boot ; un composant qui tient
   `SDA`/`SCL` pendant la sienne expliquerait des transactions ratées **tôt** et un bus sain ensuite.
   ⇒ **Le reset RTS ne les réveille pas** : ils sont **déjà démarrés**, ce qui colle exactement au motif.
2. **Appel de courant** à froid, affaissant le rail 3V3 le temps de l'établissement.
3. **Tirages faibles** (Y6 : BH1750 **aucun**, ToF 10 kΩ) rendant les fronts marginaux **précisément**
   quand le rail n'est pas encore stable.

⇒ **Ce qui trancherait** : un **A/B compté** — N rebranchements physiques contre N `--reset`, avec
le décompte des `abort()` — et, si l'hypothèse 1 tient, **retarder `dn_capteurs_init()`** ou lui
donner une **reprise** (§13.16.11, second défaut : elle ne retente JAMAIS).
⛔ ~~**Hors périmètre de `dn4-2`**, qui n'a pas le droit de toucher `dn_capteurs.c`. **Porté au
ledger.**~~ → 🔴 **RENVERSÉ LE MÊME JOUR, PAR DÉCISION OWNER EN SÉANCE** (§13.16.16) : six
démarrages à froid ratés sur sept **en haltant le CPU** ont rendu l'interdiction intenable — la
carte était inutilisable à froid, **sans console**. ⚠️ **Écrit par ajout, pas réécrit** : l'état de
la décision au moment où ce constat a été pris fait partie du constat.

⚠️ **Le montage en trois temps reste ce qui a permis de le dire** : deux modules d'un coup n'auraient
jamais séparé « câblage d'un module » de « câble Y neuf ». **Le BH1750 seul par les Y a validé les
Y**, puis le ToF a validé sa propre paire de pattes.
*(Ce paragraphe était écrit DEUX FOIS, mot pour mot — doublon retiré par la revue du 2026-08-20.)*
⚠️ **L'hypothèse « pin qui ponte `3V3` et `G` sur la rangée A »** (§13.16.7) **ne s'est PAS
reproduite** : l'INA219 a été ajouté **par ces cavités-là** et le boot est resté propre. ⇒ Elle
reste **une hypothèse non confirmée**, et non une cause écartée.

---

### 13.16.11 🔴 UN CAPTEUR QUI RÉPOND MAL BRIQUE LA CARTE — le mode de panne que `dn2-2` croyait FERMÉ

Sur la première occurrence de la dégradation, le bandeau s'est terminé par :

```
E dn_capt: identite INATTENDUE : chip id 0x00 (attendu 0x61) => INCONNU
E bme680: bme680_i2c_read_word_from(164): bme680_i2c_read_word_from failed
ESP_ERROR_CHECK failed: esp_err_t 0x103 (ESP_ERR_INVALID_STATE)
  file: "./managed_components/k0i05__esp_bme680/bme680.c" line 432
  func: bme680_get_cal_factors
abort() was called at PC 0x4037c773 on core 0
```

⇒ **`abort()` ⇒ panique ⇒ CPU HALTÉ ⇒ plus de console du tout.** L'outil de diagnostic disparaît **au
moment précis où il servirait**, et seule une modification du câblage physique fait sortir de là.

🔴 **CE DÉPÔT S'ÉTAIT DONNÉ LA RÈGLE INVERSE, ET DEUX FOIS** — *« `ESP_ERROR_CHECK` est réservé au
socle non optionnel »*, et le piège n°9 du skill : *« un module optionnel ne doit jamais pouvoir
briquer la console »*, **corrigé en revue `dn2-2`** pour `dn_link_init()`.

⚠️ **ET `dn_capteurs_init()` EST BIEN NON FATALE.** Le trou n'est pas dans le code du dépôt : il est
dans la **dépendance tierce**, qui appelle `ESP_ERROR_CHECK` **en interne** — et `ESP_ERROR_CHECK`
n'est pas une valeur de retour, c'est un `abort()`. **Aucun code applicatif ne peut le rattraper.**

**Audit fait en séance** (`grep -c` sur `managed_components/`, 2026-08-20) :

| Composant | `ESP_ERROR_CHECK` | Chemin |
|---|---|---|
| `espressif__esp_lvgl_port` | 55 | socle — toléré |
| 🔴 **`k0i05__esp_bme680`** | **26** | 🔴 **module OPTIONNEL — interdit par la règle** |
| `espressif__esp_lcd_st7701` | 14 | socle — toléré |
| 5 autres | 8 | socle — toléré |
| **TOTAL** | **103** | |

Et la ligne fautive est **une lecture I²C enveloppée** :
`ESP_ERROR_CHECK( bme680_i2c_read_word_from(handle, 0xe9, &…->par_T1) );` — ⇒ **n'importe quel hoquet
du bus provoque un `abort()`**, sur le chemin **nominal** d'initialisation.

🔴 **SECOND DÉFAUT, DISTINCT ET TOUT AUSSI RÉEL** : sur les occurrences **sans** panique,
`dn_capteurs` a logué `identite INATTENDUE : chip id 0x00` puis **n'a JAMAIS retenté**. Le bus
redevenait sain **cinq secondes plus tard**, et le capteur restait mort **jusqu'au reboot suivant**.
⇒ **Une perturbation transitoire au boot tue le BME680 pour toute la session.**

⇒ **Les deux sont portés au ledger, et ils mordront `dn4-3`** qui ajoutera des drivers.
⛔ **Cette story ne les corrige pas** : elle n'a pas le droit de toucher `dn_capteurs.c`, et un
correctif non mesuré serait pire que le défaut écrit.

---

### 13.16.12 🎯 AC9 SOLDÉ — le tactile sous saturation, à 8 devices

**Deux campagnes de 20 s, la première étant le témoin sans lequel la seconde ne dit rien.**

#### Campagne 1 — SANS rafale : ✅ et elle solde le résiduel 🟡 du ledger

`touch trace 20000` : **18 appuis tracés · 15 taps sur zone · 3 hors zone · 0 erreur I²C**
(cumulé : 49 appuis, 49 relâches, 4 949 lectures).

**Coordonnées relevées sur la géométrie D12** — c'est ce que le ledger réclame depuis `dn4-6`
(`:347`), où la campagne avait compté *36 appuis / 36 relâches / 0 erreur* **sans jamais relever les
zones** :

```
(25, 20) (45, 32) (33, 21) (53, 13) (24, 30) (45, 48) (71, 25) (58, 30)
(122,366) (134,138) (351,358) (360,512) (122,530) (347,522) (69,129) (211,154) (317,181) (129,374)
```

🔑 **Le geste se LIT dans les chiffres** : les huit premiers sont tous à **`x < 75` et `y < 60`**,
c'est-à-dire la **flèche retour `←`** ; les autres sont dans les cases. ⇒ *ouvrir une case, revenir,
recommencer*. Et l'instrument les compte **comme des taps sur zone**, ce qui est correct — la flèche
est un contrôle, pas une marge. **Le résiduel est SOLDÉ.**

#### Campagne 2 — AVEC rafale : ✅ AC7 (a) de `dn2-1` est REJOUÉ et il PASSE

| Grandeur | Mesuré |
|---|---|
| Durée demandée / **réelle** | 20 000 / **20 018 ms** |
| Passes complètes | **1 066** |
| Sondages émis | **119 392** |
| **Cadence** | **5 964 sondages/s** · 53 passes/s |
| Timeouts | **0** |
| **`touch` encadrant** | **18 appuis · 18 relâches · 🎯 0 ERREUR I²C** |

✅ **CONSTAT OWNER, cité verbatim** — et c'est la moitié de la mesure, celle qu'aucun compteur ne
donne : à la question *« délai ? appuis perdus ? différence ressentie entre les deux campagnes ? »*,
la réponse est **« nn tt nickel »**.

⇒ **D9 avait fermé la voie du fil ; la voie logicielle a répondu.** Le tactile encaisse
**119 392 sondages en 20 s** sans perdre un appui ni compter une erreur.
✅ **Et la cadence tient la charge** : **6 012 sondages/s à 5 devices → 5 964 à 8**, soit **−0,8 %**.

#### 🔴 EFFET DE BORD MESURÉ : LE SCAN MENT **2,36 FOIS PLUS** À 8 DEVICES

La rafale compte ses acquittements ; en soustrayant ceux des devices réels :

| | **5 devices** | **8 devices** |
|---|---:|---:|
| Passes · sondages | 537 · 60 144 | 1 066 · 119 392 |
| Acquittements | 3 110 | 10 461 |
| Attendus des devices réels | 2 685 | 8 528 |
| **Fantômes** | **425** | **1 933** |
| Par passe | 0,79 | **1,81** |
| **Taux par sondage d'adresse VIDE** | **0,740 %** | 🔴 **1,744 %** |

⇒ 🔴 **Brancher trois capteurs de plus a MULTIPLIÉ PAR 2,36 le taux de faux positifs du sondage.**
§13.2 savait que le scan ment ; **personne ne savait qu'il ment davantage à mesure qu'on charge le
bus**. C'est un argument de plus, **chiffré**, pour la règle : *le scan DÉCOUVRE, seule une
transaction de DONNÉE QUALIFIE*.
⚠️ **1 933 est un PLANCHER** : le calcul suppose que les 8 devices réels ont acquitté à **chaque**
passe ; §13.2 a mesuré des faux **négatifs** sur composants soudés.

---

### 13.16.13 ✅ AC10 SOLDÉ — la famine DMA NE se reproduit PAS, avec le premier agresseur en trois exemplaires

**Stimulus rejoué dans les conditions EXACTES de `dn4-6`** : `tools/dn_injecteur.py --jeu reel
--secondes 45 --espacement 0.004` ⇒ **225 trames émises en 45 s = 5 trames/s**, conjuguées au
repeint de case.

🔴 **LA MESURE EST UN CONSTAT OWNER, parce qu'aucun instrument ne compte ce défaut** — §11.4 écrit
que **`fps` est AVEUGLE** : il rendait déjà **37,40 Hz** pendant que l'image sautait, en `dn4-6`.

**Le symptôme a été cherché sous son nom, donné à l'owner AVANT** : *« l'image entière glisse d'un
cran et se recale vers le bas, ensuite tous les chiffres clignotent une fois, et rebelote »*, **une
fois par seconde**. Consigne explicite : *« si tu vois quelque chose que je n'ai pas décrit, dis-le
tel que tu le vois, ne le fais pas rentrer dans mes mots »*.

✅ **RÉPONSE OWNER, verbatim : « tt nickel ».** ⇒ **RIEN.**

**Les instruments, en regard, et ils COLLENT aux références de `dn4-6`** :

| Grandeur | `dn4-6` régime (b) | **`dn4-2`, 8 devices** |
|---|---:|---:|
| flush / cycle | 2,33 | **2,4** |
| px / cycle | 85 575 | **87 196** |
| plus grande aire | 36 675 | **36 675** |
| copie µs/flush | 3 032 | **2 979** |
| Liaison | 149/150, 1 perte seq, 0 rejet | **224/225, 1 perte seq, 0 rejet de TOUTE cause** |
| Latence acceptation→label | — | **n=224 · min 60 · moy 109 · max 180 ms** |
| `touch` encadrant | — | **0 erreur · 0 erreur** (1 026 lectures) |

⇒ ✅ **`DN_DEFAULT_BOUNCE_PX` RESTE À 7 680.** Aucune montée vers 9 600 n'est nécessaire, et les
**+19 200 o** de RAM interne que le pas suivant aurait coûtés ne sont pas dépensés.
⇒ **L'entrée de ledger 🟠 `[→ dn4-2, IMPÉRATIF]` est SOLDÉE** : le stimulus est rejoué, avec le
premier agresseur connu enfin présent **en trois exemplaires**, et il ne reproduit rien.

⏳ **LA LIMITE EST DÉCLARÉE, comme AC10 l'exige** : l'injection venait de `dn_injecteur.py` **depuis
WSL**, ⛔ **pas de l'agent réel sur la tour** — l'exclusivité `WSL ↔ COM3` l'interdit tant que la
carte est attachée à WSL. **Même chemin de code** (même REPL, même `dn_link`, même `dn_ui`),
⛔ **pas le même émetteur.** Ce qui n'est pas mesuré ici, c'est le PC.

---

### 13.16.14 ✅ AC12 — les budgets, sur le firmware LIVRÉ et au BOOT PROPRE

**`43e108f`, SHA lu au bandeau**, `porcelain` vérifié **VIDE avant** le flash.
⚠️ **Le tas est relevé AU BOOT PROPRE, ⛔ pas après campagne** — un relevé post-campagne a déjà rendu
**40 %** de fragmentation contre 2 % au boot, et *« un chiffre faux mais plausible est plus dangereux
qu'un chiffre absurde ; celui-là était les deux »*.

| Grandeur | **T0** `df5d23d`, 5 devices | **LIVRÉ** `43e108f`, 8 devices | Δ |
|---|---:|---:|---:|
| **Binaire** | 943 712 o | **950 800 o** | **+7 088 o (+0,75 %)** |
| Partition libre | 78 % | **77 %** | −1 pt |
| RAM interne libre | 92 219 o | **92 315 o** | **+96 o (+0,10 %)** |
| PSRAM libre | 7 768 236 o | **7 768 236 o** | **0,00 %** |
| Tas LVGL utilisé | 20 468 o (33 %) | **20 496 o (34 %)** | +28 o |
| Plus gros bloc libre | 40 752 o | **40 752 o** | **0** |
| Fragmentation | 3 % | **2 %** | −1 pt |
| `fps 15` | 37,40 Hz, +0,00 % | **37,40 Hz, +0,00 %** | **0** |
| Boot | 2 319 ms | **2 328 ms** (2 321 au suivant) | +9 ms (+0,39 %) |
| `nav ab 40` (n=80) | 291,1 / 335,2 / 398,7 ms | **291,1 / 335,3 / 398,7 ms** | **+0,1 ms** |

⚠️ **Le +0,1 ms de `nav ab` est du BRUIT** : la mesure porte **±16 ms sur n=40**, et tout verdict à
moins de ~±20 ms n'en est pas un. ⇒ **Publié comme distribution (min/moy/max), ⛔ pas comme moyenne
seule.**

**Le coût se décompose exactement**, et c'est **le binaire SEUL** :

| Commit | Ce qu'il ajoute | Coût |
|---|---|---:|
| `62e5f1d` | `i2c ecrire` · `i2c brut` · `i2c lire16` | **+5 232 o** |
| `43e108f` | `i2c rafale` (l'instrument d'AC9) | **+1 856 o** |
| | **total** | **+7 088 o** |

*(Référence historique : la commande `i2c` complète avait coûté +4 400 o en `dn2-1`.)*

#### ⛔ ZÉRO COÛT EN RÉGIME — et c'est mesuré, pas déduit

**`cpu brut` encadrant une fenêtre CALME chronométrée de 30,2 s**, à 8 devices :

| Tâche | % d'un cœur |
|---|---:|
| `taskLVGL` | 2,31 % |
| `esp_timer` | 0,68 % |
| `dn_rtc` | 0,17 % |
| **`dn_capt`** | **0,09 %** |
| `console_repl` | 0,05 % |
| `dn_link` · `main` | 0,02 % chacun |
| **⇒ cœur 0 occupé** | **3,31 %** |
| **⇒ cœur 1 occupé** | **0,04 %** |

⇒ **`dn_capt` à 0,09 % est le BME680 SEUL, inchangé.** Les trois nouveaux capteurs sont **sur le bus
et qualifiés**, ⛔ **pas pilotés** : aucune tâche, aucun timer, aucune allocation. **Le périmètre est
tenu, et le chiffre le prouve.**
⚠️ **Un premier couple `cpu brut` a été écarté** parce qu'il encadrait `fps 15` **et** `nav ab 40` :
il rendait 51,6 % sur le cœur 0, ce qui mesurait **la campagne**, pas le régime. **Dit plutôt que
publié.**

---

### 13.16.15 ✅ AC13 — les gardes des marches du dessous restent vertes

| Garde | Origine | Mesuré à 8 devices |
|---|---|---|
| **BME680 vivant** | `dn2-1` | ✅ `VIVANT` · `config LUE (conforme)` (`0x72=04 · 0x74=84 · 0x75=08`) · cadence **4 999 / 5 005 ms** · `err_i2c` **0** |
| **RTC vivante** | `dn3-2` | ✅ `0x51` qualifiée **par lecture** · témoin anti-fantôme **`0xD7` vert** · ⚠️ `OS = 1` **attendu** après ~10 coupures USB (§13.15.3 : **aucune sauvegarde**), barre passée à **« --:-- HEURE NON POSÉE »** ⇒ **la garde a fonctionné**, heure reposée, `OS = 0` |
| **Témoin v1** (agent `dn2-2` non modifié) | `dn2-2` / `dn4-1` | ✅ **6 trames v1 valides, 0 rejet de TOUTE cause**, case CPU à 100 % et les grandeurs non publiées marquées `--` |
| **Péremption 3 s par métrique** | `dn2-2` | ✅ les **5 métriques** portent chacune **leur propre âge et leur propre état** (`pc`) ⇒ une source qui meurt **meurt SEULE** |
| **« toute la case est la zone tactile »** | `dn1-4` / D12 | ✅ **re-prouvée sur la géométrie D12** : **15 taps sur zone / 18 appuis**, coordonnées publiées (§13.16.12) |
| **Barre et MENU = zones mortes** 🔴 *(PÉRIMÉE À MOITIÉ le 2026-08-25 par `dn3-3` : le bandeau `MENU` est devenu une VRAIE PORTE vers `DN_VUE_MENU` et son compteur MONTE. Ce relevé décrit fidèlement le firmware de sa date — ⛔ il n'est ni effacé ni réécrit. Ce qui reste à tenir est « la BARRE est une zone morte », re-tiré par `dn3-3`/AC5.6 comme témoin négatif.)* | `dn1-4` / `dn3-1` / `dn3-2` | ✅ **3 appuis hors zone ⇒ 0 tap** — la garde se déclenche, et l'instrument le **dit** |
| **D4 — aucun `nvs_*` en régime** | brief | ✅ **RE-VÉRIFIÉ PAR GREP** : toutes les écritures (`nvs_set_i32`, `nvs_commit`, `nvs_erase_all`) sont dans `set_i32()` et `dn_bootcfg_reset()`, **dont les SEULS appelants sont `dn_console.c`** (`set …` et `cfg reset`). Les lectures sont au boot. ⇒ **aucune écriture sur un chemin de régime** |
| **Bandeau de boot** | — | ✅ **une seule ligne `E`** sur un boot sain : celle de l'ISR, **nommée et rattachée** (AC11). ⛔ Aucune nouvelle |
| **Smoke owner 6/6** | — | ✅ **FAIT** — constat owner du 2026-08-20, verbatim : *« reste ok »*. ⚠️ *Transcrit ici par la revue de code du 2026-08-20 : le constat avait eu lieu en séance et n'était consigné que dans la story, cette table portant encore « ⏳ dû ». **L'œil de l'owner est l'instrument ; l'agent n'a fait que le recopier.*** |

> ✅ **SOLDÉ — VOIR §13.17.5, §13.17.7 ET §13.17.9, PLUS BAS DANS CE MÊME DOCUMENT.** *(Renvoi ajouté
> par la revue du **2026-08-24** : la séance qui a soldé ces trois lignes les a écrites en §13.17 et
> **n'a pas annoté cet encart** — `grep -n "13\.17"` depuis §13.16 rendait **zéro renvoi avant**. Un
> lecteur qui s'arrêtait ici lisait **trois AC ouverts qui ne le sont plus**. C'est le motif
> « §13.16.10 laisse debout une affirmation que §13.16.16 réfute six sections plus bas », déjà relevé
> par la revue précédente — et **re-commis dans le diff qui le corrigeait**.)*
>
> 🔴 **CE QUE LA REVUE DE CODE DU 2026-08-20 A ROUVERT, ET QUI EST DÛ À UNE SÉANCE CARTE
> APRÈS LES CORRECTIFS.** Décision owner du 2026-08-20 : **on corrige d'abord, on mesure ensuite**,
> parce que mesurer maintenant reviendrait à publier des budgets sur un firmware qui va changer —
> c'est-à-dire à rejouer l'écart qu'AC14 dénonce (*« trois flashs ont porté un SHA de bandeau
> différent du livrable, ce qui a rouvert un AC DEUX FOIS »*).
>
> | AC | Ce qui manque | Ce qui le solderait |
> |---|---|---|
> | **AC12** | La table des budgets (§13.16.14) est relevée sur **`43e108f`**, alors que le livrable était **`3a7d938`** puis `e931c31`. RAM interne, PSRAM, tas LVGL, plus gros bloc, fragmentation, `fps 15`, boot et `nav ab` **non re-relevés** après l'élargissement de périmètre. Le binaire publié (`950 800 o`) est périmé. ⚠️ **Et le `cpu brut` qui porte le « zéro coût en régime » est mesuré AVANT le commit qui modifie `dn_capteurs.c`** ⇒ **asserté, pas mesuré** | Table avant/après **complète**, sur le firmware livré, **SHA lu au bandeau**, tas relevé **au boot propre** |
> | **AC8** | **Aucun régime long à 8 devices.** Le plus long publié est **15 s / 435 lectures** (plus une fenêtre CPU de 30,2 s), contre la référence **0 err / 279 604 lectures (~2 h 45) à 5 devices** — soit **0,16 %**. T8 cochait *« régime CHRONOMÉTRÉ »* **sans dire la durée** | Un régime **chronométré**, durée annoncée, avec le **couple encadrant** `touch` et `capteurs` en regard |
> | **AC9** | Les coordonnées D12 sont bien relevées (le résiduel 🟡 du ledger est soldé), mais **la cible n'a pas été rendue VISIBLE** avant qu'on demande de viser, et **la formule n'a pas été contrôlée contre un relevé déjà publié** — les deux sont exigés par l'AC, avec leur motif de ledger (*« trois tours et 31 appuis perdus sur une jauge invisible »*). Le compte de **`taps`** manque aussi pour la campagne sous rafale | Cible **rendue visible**, formule contrôlée, campagne rejouée, **les quatre compteurs** publiés |
>
> ⚠️ **Et `i2c rafale` a été corrigée par cette même revue** (bornage **par adresse**, **témoin
> positif**, « 400 kHz » → **100 kHz**) : rejouer AC9 **avant** ces correctifs aurait produit un
> relevé portant les défauts de l'instrument.

⚠️ **CE QU'AC13 NE PEUT PAS DÉCLARER VERT** : le **démarrage à froid** (§13.16.10). Les gardes
ci-dessus sont mesurées **sur un boot sain** ; trois démarrages à froid sur quatre n'en produisent
pas un. ⇒ **La non-régression est établie EN RÉGIME, pas AU DÉMARRAGE**, et la distinction est écrite
plutôt que gommée.

---

### 13.16.16 🔴 ÉLARGISSEMENT DE PÉRIMÈTRE ASSUMÉ — un capteur qui ne répond pas ne doit pas BRIQUER la carte

⚠️ **`dn4-2` s'interdit explicitement de toucher `dn_capteurs.c`.** La mesure a rendu cette
interdiction intenable : **6 démarrages à froid ratés sur 7** à huit devices, **la plupart en carte
HALTÉE**, c'est-à-dire **sans console** — l'outil de diagnostic disparaissant au moment précis où il
sert. **Décision owner en séance : on corrige, et on le mesure par un A/B avant/après DANS LA MÊME
SÉANCE.** *(Un avant/après d'une seule séance vaut mieux que deux mesures séparées par un firmware.)*

#### 🔴 LA CHAÎNE — trois maillons, établis par la mesure PUIS vérifiés dans le code

| # | Défaut | Où |
|---|---|---|
| **1** | Une lecture I²C qui **ÉCHOUE** écrivait `s_chip_id = 0` — soit **exactement** ce qu'aurait rendu un capteur ayant **répondu** `0x00`. **Deux diagnostics opposés dans la même valeur.** | `dn_capteurs.c:390` |
| **2** | Le message publiait alors *« identite INATTENDUE : chip id 0x00 »* — une **AFFIRMATION SUR LE CAPTEUR** alors qu'il n'avait rien dit. Et il **se contredisait lui-même** en ajoutant *« le câblage n'est PAS en cause si le scan voit 0x77 »* | `journaliser_identite()` |
| **3** | `ouvrir_driver()` était appelé **QUOI QU'IL ARRIVE** ⇒ le composant **tiers** partait, et il enveloppe ses lectures I²C dans `ESP_ERROR_CHECK` (`bme680.c:433`, chemin **nominal**) ⇒ `abort()` ⇒ **CPU halté** | `dn_capteurs.c:878` |

🔴 **ET LE CHEMIN DE REPRISE ÉTAIT PIRE : l'ordre y était INVERSÉ.**
`if (bus && ouvrir_driver(bus)) { relever_identite(bus); … }` — **le driver tiers partait AVANT
toute vérification**. ⇒ **Même un boot réussi pouvait se faire briquer à la reprise suivante, UNE
MINUTE plus tard**, par la même perturbation.

#### La preuve que le capteur n'était PAS en cause — relevée sur la carte DANS l'état fautif

```
i2c            -> 8 stable(s), 0 instable(s) en 39 ms, temoin positif OK
i2c lire 77 D0 -> 61        i2c lire 77 F0     -> 00
i2c lire 40 00 2 -> 39 9F   i2c lire16 29 0000 -> B4
```

⇒ **Le bus était PARFAITEMENT SAIN, les huit devices répondaient, BME680 compris**, pendant que le
bandeau annonçait *« chip id 0x00 »*. ⛔ **L'instrument mentait, pas le matériel.**

⚠️ **ET C'EST LA FAUTE QUE CE DÉPÔT A DÉJÀ CORRIGÉE DEUX FOIS** — `tronquee`/`trop_longue` en
`dn2-2`, puis **`err_i2c`/`err_donnee` DANS CE FICHIER MÊME** au CR du 2026-08-17 (*« les deux
tombaient dans `i2c`, et `donnee` ne pouvait pas quitter 0 »*). **La leçon avait été appliquée aux
compteurs de RÉGIME, jamais à l'identification au BOOT.**
⚠️ **Et le garde-fou d'AC7 (a) existait EN INTENTION** : le docblock de `relever_identite()` dit
*« pourquoi AVANT `bme680_init()` »* — mais **son résultat ne DÉCIDAIT rien**. *Le sondage
INFORMAIT ; il PROTÈGE désormais.*

#### Le correctif — firmware `3a7d938`, SHA lu au bandeau, `porcelain` vide avant flash

1. **`s_id_lue`** sépare *« la lecture a abouti »* de *« la valeur lue »* ;
2. **`identite_est_bme680()`** est le garde-fou, et **les DEUX chemins** y passent ;
3. la **reprise relève l'identité AVANT** d'ouvrir ;
4. `journaliser_identite()` a un **troisième cas** — *« identite NON LUE »* — qui **n'affirme RIEN**
   sur le capteur et donne les deux commandes qui tranchent ;
5. **`capteurs` aussi** — sans quoi le mensonge se serait **déplacé** du bandeau vers la console.

#### 🎯 L'A/B, sur le geste qui compte — le DÉMARRAGE À FROID

| | **AVANT** `43e108f` | **APRÈS** `3a7d938` |
|---|---:|---:|
| Démarrages à froid | **7** | **3** |
| 🔴 **HALTÉE** (carte briquée, console morte) | **6** | **0** |
| ✅ Carte vivante et utilisable | 1 | **3** |
| Capteur récupéré ensuite | — | ✅ **oui, PAR LA REPRISE** |

**Constat owner, verbatim** : *« à chaque rebranchement j'ai bien le bon screen qui s'affiche (par
contre ambiance n'est plus vivant ?) »* — ⇒ **exactement le comportement visé**, et l'owner a repéré
lui-même la moitié qui reste.

✅ **Et la reprise ramène le capteur, mesuré** : `identite : chip id 0x61 · variant 0x00 => BME680`,
`11 lectures · 0 reprises · 0 reconfigurations`, `erreurs : i2c 0 · donnee 0 · bornes 0`.

⚠️ **CE QUE LE CORRECTIF NE FAIT PAS, ET ÇA A ÉTÉ DIT AVANT DE MESURER** *(pour ne pas pouvoir
déplacer la cible après)* : **la lecture d'identité échoue TOUJOURS au démarrage à froid.** La cause
reste à comprendre ⇒ **`dn4-3`**. Le correctif transforme *« carte briquée, plus aucun diagnostic
possible »* en *« capteur muet une minute, tout le reste marche »*. ⛔ **Et les 103
`ESP_ERROR_CHECK` des dépendances épinglées restent là** : seul le chemin du BME680 est protégé.

**Coût : +1 648 o de binaire** (950 800 → 952 448). ⛔ **Zéro en régime.**
⚠️ *Ce chiffre était publié « +1 660 » ici, dans le message de commit et dans le Change Log de la
story : `952 448 − 950 800 = 1 648`. Corrigé par la revue du 2026-08-20 — un écart de 12 octets ne
change rien au verdict, mais un nombre publié trois fois qui ne se recalcule pas est un nombre qu'on
n'a pas vérifié.*

⚠️ **Un artefact de mesure s'est re-manifesté pendant cet A/B** : la capture du cycle 1 est revenue
**vide** alors que la console avait rendu écho **et** invite — c'est le défaut de `dn_console.py`
de §13.16.2, **pris sur le fait une seconde fois**. ⇒ Le cycle est classé **« vivant, capture
tronquée »**, ⛔ pas « HALTÉE » : **l'invite rendue prouve que le CPU tournait.**


---

## 13.17 🔴 SÉANCE POST-REVUE `dn4-2` (2026-08-20) — L'A/B DU GARDE-FOU, ET LE DÉFAUT À FROID ENFIN CARACTÉRISÉ

> **Firmware `8c928db`**, SHA **LU AU BANDEAU** (`App version: 8c928db`), `git status --porcelain`
> vérifié **VIDE AVANT le flash**. Séance conduite après la revue de code 3 couches du même jour
> (45 constats, 38 correctifs appliqués en 7 commits).
> ⚠️ **TOUS LES HORODATAGES DE CETTE SECTION SONT EN HEURE LOCALE `CEST` (UTC+2)**, celle que
> l'owner lit sur sa montre. ⛔ Les relevés bruts de la séance ont d'abord été publiés en **UTC** —
> l'owner a immédiatement relevé l'écart (*« 11h14 alors que ça a commencé vers 12h45 ? »*). Le
> chiffre était juste et l'étiquette `UTC` était écrite, **mais un chiffre juste que le lecteur lit
> faux est un chiffre faux** : c'est la classe de défaut de ce chapitre, appliquée à une unité de
> temps. ⇒ **Règle** : dans une séance carte, horodater en **heure locale**, ou porter les deux.
>
> ⚠️ **Busid `3-7`, pas `3-1`.** Le skill `/desknode-board`, le `README.md` et six stories écrivent
> `3-1` en dur. `tools/wsl-attach.sh` **relit le busid à chaque appel** — il l'avait prévu (*« le
> figer dans le script serait un piège »*) — donc la séance n'en a pas souffert. ⛔ **Les recettes
> écrites en dur, elles, sont fausses.**

### 13.17.1 🎯 L'A/B DU DÉMARRAGE À FROID — 6 SUR 6, ET LE DÉFAUT EST ENFIN CARACTÉRISÉ

**Protocole** : débranchement **physique** du câble USB (le seul geste qui coupe réellement le rail
3V3 — ⛔ ni `reboot`, qui laisse le rail debout, ni le retrait de `VCC`, à cause de l'alimentation
fantôme §13.10), attente ~3 s, rebranchement. **Geste owner**, six fois. Budget **annoncé à 6 et
tenu**.

| Cycle | Console | Identité **à froid** | GT911 | Verdict |
|---|---|---|---|---|
| **1** | ✅ vivante | ⛔ **NON LUE** | 🔴 **950 err / 1 713 lectures = 55,5 %** | dégradé, **rétabli SEUL** |
| **2** | ✅ vivante | ✅ lue (`0x61`) | 0 / 455 | propre |
| **3** | ✅ vivante | ✅ lue | 0 / 368 | propre |
| **4** | ✅ vivante | ✅ lue | 0 / 490 | propre |
| **5** | ✅ vivante | ✅ lue | 0 / 353 | propre |
| **6** | ✅ vivante | ✅ lue | 0 / 659 | propre |

🎯 **AVANT le correctif : 6 échecs sur 7, la plupart CARTE HALTÉE, sans console.**
🎯 **APRÈS : 0 briquage sur 6, console vivante à chaque cycle.**

🔴 **ET LE CYCLE 1 A LIVRÉ CE QUE ONZE TESTS À UNE VARIABLE N'AVAIENT JAMAIS ISOLÉ.**

| Instrument, au cycle 1 | Ce qu'il a dit |
|---|---|
| **Scan `i2c`** | **8 stables, 0 instable**, témoin positif **vert**, 38 ms — le bus a l'air **PARFAIT** |
| **`touch`** | **950 erreurs I²C sur 1 713 lectures** — **55,5 % d'échec** |

> 🔴 **LE SCAN DIT QUE TOUT VA BIEN PENDANT QU'UNE TRANSACTION DE DONNÉE SUR DEUX ÉCHOUE.**
> C'est la doctrine du dépôt — *« le scan DÉCOUVRE, seule une transaction de DONNÉE QUALIFIE »* —
> démontrée dans sa forme la plus extrême, et **sur le tactile, pas sur le BME680**.

**⇒ TROIS CONCLUSIONS QUI CHANGENT LE DOSSIER :**

1. **Le démarrage à froid n'est PAS un défaut du BME680.** C'est une défaillance des transactions
   **multi-octets à l'échelle du BUS**. Le BME680 n'en mourait que parce qu'il est le seul composant
   dont les lectures passent par un `ESP_ERROR_CHECK` (dépendance tierce `k0i05__esp_bme680`).
   Le GT911 encaissait déjà 55 % d'erreurs **sans que personne le regarde**.
2. **Ce n'est PAS une soudure.** Le sondage d'adresse voit les huit devices, **5/5, à chaque passe**.
   Un défaut de contact ne se comporte pas ainsi.
3. 🔴 **LE DÉFAUT EST TRANSITOIRE ET AUTO-RÉTABLI.** Compteur GT911 : **950 à T0, 950 à T+35 s**,
   alors que les lectures passaient de 2 606 à 3 468 — **+862 lectures, ZÉRO erreur nouvelle**. Les
   950 erreurs se sont **toutes** produites dans les ~40 premières secondes.

**Et la reprise a ramené le capteur, entièrement, sans intervention :**

```
T+~60 s   identite   : chip id 0x61 · variant 0x00 => BME680      (elle était « NON LUE »)
T+~90 s   BME680 @ 0x77 : VIVANT — 24,5 C · 52,8 % · age 471 ms
          config LUE : 0x72=04 · 0x74=84 · 0x75=08 (conforme)
          compteurs  : 11 lectures · erreurs : i2c 0 · donnee 0 · bornes 0
```

⇒ **C'est exactement le chemin de reprise que la revue a corrigé** : il relève l'identité **d'abord**,
et elle **décide** — avant, `ouvrir_driver()` partait sans aucune vérification et pouvait se faire
briquer une minute après un boot réussi.

⚠️ **CE QUE CET A/B NE PROUVE PAS** : la lecture d'identité **échoue toujours** à froid (1 cycle sur
6). Le correctif empêche le **briquage**, ⛔ **il ne répare pas la cause** — et ça avait été écrit
**AVANT** de mesurer, pas après. **La cause reste ouverte, et elle est désormais NOMMÉE : dégradation
transitoire des transactions multi-octets sur tout le bus, ~40 s après un démarrage à froid.** ⇒ `dn4-3`.

⚠️ **Le tri-état d'identité a servi dès le premier cycle**, et c'est sa raison d'être :
```
identite : ⛔ NON LUE — la transaction I2C a ECHOUE. Ce n'est PAS
           « il a repondu 0x00 » : il n'a RIEN repondu.
```
Sous l'ancien code, cette situation **exacte** imprimait **« chip id 0x00 »** — une affirmation sur un
capteur qui n'avait rien dit, qui envoie chercher un mauvais composant.

### 13.17.2 ✅ LES CORRECTIFS DE LA REVUE, VÉRIFIÉS UN PAR UN SUR LA CARTE

| Correctif | Vérification | Résultat |
|---|---|---|
| **Conversion lux ÷10** | `i2c brut 23 2` | `brut 1113` → **`927.5 lx`** (`1113 / 1,2` ✅). ⛔ **L'ancien code aurait imprimé `92,7 lx`** — et 92,7 lx est *aussi* plausible. C'est **pour ça** que le défaut a traversé trois publications |
| **Garde d'adresse de `lire16`** | `i2c lire16 40 0000` | Sortie **NUE** : `0x40 reg16 0x0000 : 39`. ⛔ Avant : *« MODEL_ID = 0x39 = PAS un VL6180X … **REMONTÉE OWNER** »* — un faux verdict **qui escalade**, sur un device qui n'a jamais été un ToF |
| **Garde d'adresse, contrôle positif** | `i2c lire16 29 0000` | **`B4`** + le verdict VL6180X — il sort **là où il doit** |
| **Garde du `n` par défaut** | `i2c brut 23` | Rend `00` **et** dit *« l'interprétation n'est PAS faite, ne rien conclure »*. ⛔ Avant : un `00` **muet**, sans l'avertissement *« 0000 ne prouve PAS un capteur mort »* — c'est-à-dire **sans le discriminant de toute la procédure de stimulus** |
| **Avertissement d'occupant** | `i2c ecrire 77 D0` (1 octet = pointeur de registre, **inoffensif**) | Le bloc sort **sur le chemin NOMINAL**. ⛔ Avant, il n'était imprimé **que si l'invocation était malformée** |
| **Bornage `rafale` par adresse** | `i2c rafale 25000` | **25 000 ms demandés, 25 000 ms réels** — **0 ms de dépassement**, et la passe interrompue **exclue** du décompte |
| **Retour de `rm_device` lu** | 13 lectures | 🔴 **LE REFUS S'EST PRODUIT** — voir §13.17.3 |

### 13.17.3 🔴 `i2c_master_bus_rm_device()` REFUSE POUR DE VRAI — la carte tranche un désaccord entre deux couches de revue

La couche **Edge Case Hunter** avait annoncé la course comme réelle ; la couche **Acceptance
Auditor** avait conclu *« aucune fuite possible »* après avoir vérifié que l'appel était **présent**
sur tous les chemins. **La carte donne raison à la première :**

```
⚠️ RETRAIT DU DEVICE REFUSE (ESP_ERR_INVALID_STATE) — un device FANTOME reste sur le
   bus et deux allocations ont fui. Course connue avec le sondage du GT911 (~30/s).
   ⛔ Le resultat ci-dessus reste VALIDE ; c'est le menage qui a rate.
```

**Mesure : 1 refus sur 13 lectures.** ⛔ **Non reproduit sur 12 essais consécutifs** ⇒ c'est un
**événement rare et racé**, ⛔ **pas un taux**. Le mécanisme est lu dans l'IDF épinglé :
`ESP_RETURN_ON_FALSE(atomic_load(&bus->status) > I2C_STATUS_START, ESP_ERR_INVALID_STATE, …)`
(`esp_driver_i2c/i2c_master.c:1216`) — **et ce test précède la prise de `bus_lock_mux`**, alors que
le GT911 sonde le même bus ~30 fois par seconde.

🔴 **CE QUI COMPTE N'EST PAS LE TAUX, C'EST QU'AVANT CE CORRECTIF LA FUITE ÉTAIT TOTALEMENT
SILENCIEUSE.** Le docblock promettait *« retiré sur TOUS les chemins de sortie »* et §13.6 quater en
faisait le **critère éliminatoire n°2** : la promesse était tenue par l'**appel**, pas par la
**vérification**. Personne n'aurait jamais su.

### 13.17.4 🎯 AC6 REJOUÉ — le stimulus BH1750, avec les VRAIS lux

| État | brut | lux | n |
|---|---|---|---|
| **départ** (témoin) | 1 113 | **927,5** | 3, identiques (⚠️ *voir l'encart de §13.16.8 : « 3, identiques » n'est pas une preuve de vie — réfuté le 2026-08-24*) |
| 🖐️ **main posée** | 2 | **1,6** | 3, identiques |
| **main retirée** | 25 510 · 28 781 · 28 124 | **21 258 → 23 984** | 3, **VARIABLES** |

**Rapport main posée / main retirée : ×13 286 à ×14 990.** Un faux positif de bus n'acquitte pas
différemment selon qu'une main est posée dessus.

> 🔴 **ÉCART DÉCLARÉ SUR AC6 — REVUE DE CODE DU 2026-08-24, DÉCISION OWNER.** AC6 exige la
> qualification *« à condition que **l'owner fasse le geste et le constat**, ⛔ jamais l'agent »*.
> Les **deux moitiés vivent dans deux sections, et aucune ne les réunit** : le relevé annoté
> *« Geste **owner** »* est celui de §13.16.8, **dont les lux sont recalculés depuis le brut publié,
> ⛔ pas re-mesurés** ; ce relevé-ci — le seul **réellement mesuré sur le firmware corrigé** — ne
> porte **aucune** occurrence du mot « owner » ni de verbatim. ✅ **La qualification elle-même n'est
> PAS en cause** : le stimulus qualifie par le **rapport**, les rapports étaient justes, et le
> stimulus a bien été **rejoué** ici sur le firmware corrigé. C'est l'**attribution du geste** qui
> manque sur le relevé qui fait foi.

⚠️ **DEUX CHOSES QUI NE SONT PAS MASQUÉES** :
1. **Le retour n'est PAS identique au départ** — 23 984 contre 927,5 lx, soit **×25**. Le module est
   sur fils volants : soit il a bougé pendant le geste, soit il reçoit une lumière directe qu'il ne
   recevait pas au départ. ⛔ **Non tranché** — et ça ne change rien au verdict, qui porte sur le
   **rapport**, pas sur les absolus.
2. **Les trois lectures « main retirée » varient de 13 %.** Ce n'est **pas** un défaut : c'est de la
   lumière ambiante avec quelqu'un qui bouge à côté. 🔴 **Une valeur qui VARIE est une preuve plus
   forte qu'une constante** — une constante peut être rejouée par un chemin de code mort, pas ça.

### 13.17.5 🎯 AC9 COMPLET — la cible RENDUE VISIBLE, et le relevé publié RÉFUTÉ

🔴 **La moitié qui manquait au relevé du 2026-08-20 est faite, et elle a produit une réfutation.**

**Rendre la cible visible** (exigence de l'AC, motif de ledger : *trois tours et 31 appuis perdus sur
une jauge invisible*) : `widget piste 0xFF2020` — l'instrument dit lui-même *« seule RAM porte une
jauge aujourd'hui : c'est la seule case où le changement se voit »*.
✅ **Constat owner, verbatim** : *« oui barre rouge plein sur la case ram »*. ⛔ **L'œil de l'owner
est l'instrument** — l'agent ne peut pas attester qu'une cible est visible.

**Campagne de visée** (`touch trace 45000`) : **25 appuis · 25 relâches · 24 taps · 0 erreur I²C**
sur 2 043 lectures.

🔴 **LES COORDONNÉES RÉFUTENT LA BANDE PUBLIÉE.** Les neuf taps `RAM`, l'owner visant la barre rouge
**qu'il voyait** :

```
(119,368) (38,357) (196,360) (136,362) (93,366) (153,371) (46,350) (133,362) (192,365)
⇒ y = 350..371   ·   x = 38..196
```

**AC9 publie la bande jauge `RAM` à `y = 337..347`, `x = 22..223`.**
⛔ **PAS UN SEUL des neuf appuis n'y est tombé** — tous **en dessous**, de **3 à 24 px**.
⚠️ *Ce chiffre était publié **« 13 à 24 px »** jusqu'à la revue du **2026-08-24**. Recalculé contre le
bord bas de la bande (`347`), les neuf écarts sont **3 · 10 · 13 · 15 · 15 · 18 · 19 · 21 · 24** :
**« 13 à 24 » écartait les DEUX appuis les plus proches**, dont un à **3 px** — c'est-à-dire dans le
bruit de visée tactile. (Contre le bord haut `337` la plage serait `13..34` : « 13 à 24 » ne
correspondait à **aucune** des deux références.) ⛔ **Le chiffre publié durcissait la réfutation en
supprimant les deux mesures qui l'affaiblissent** — et c'est lui qui porte le `[CC]`.*

⇒ **Deux lectures possibles, et la séance n'en tranche AUCUNE** : soit la formule publiée est
fausse, soit la **piste** (le fond de la part NON remplie) n'est pas dessinée où la **bande** est
calculée. ⚠️ **Une mesure qui contredit un verdict consigné ne se réécrit pas en silence** ⇒
**`[CC]` `bmad-correct-course` proposé**, et les deux chiffres restent écrits côte à côte.

✅ **CE QUI EST RE-PROUVÉ AU PASSAGE, ET QUI EST LE VRAI SUJET** : les **neuf** visées `RAM` sont
devenues des **taps**. La garde *« toute la case est la zone tactile »* tient sur la géométrie **D12**,
**avec ses coordonnées**. ⇒ Le résiduel 🟡 du ledger (`:347`) est **SOLDÉ pour de bon**.

⚠️ L'appui **`(10, 33)`** n'a **rien déclenché** — marge haute du bouton RETOUR, entrée de ledger
déjà ouverte, **re-observée**.

**Campagne sous SATURATION** (`i2c rafale 25000`, l'owner appuie pendant) :

| | `dn4-6` (réf.) | **2026-08-20** |
|---|---|---|
| Sondages | 119 392 / 20 s | **147 922 / 25 s** |
| Cadence | 5 964 /s | **5 916 /s** |
| Appuis · relâches | 18 · 18 | **38 · 38** |
| **Taps** | ⏳ non publiés | ✅ **38 (dont 0 sur MENU)** |
| **Erreurs I²C induites** | **0** | **0** |

✅ **Constat owner, verbatim** : *« reactivité normal, tt est nickel »*.
✅ **`0 tap sur MENU`** re-prouve la garde *« Barre et MENU = zones mortes »* sur D12.

> 🔴 **PÉRIMÉ LE 2026-08-25 PAR `dn3-3`** — le bandeau `MENU` a désormais une DESTINATION (`DN_VUE_MENU`, décision owner D-4), il est CLIQUABLE et `dn_ui_menu_taps()` **monte**. Le relevé ci-dessus décrivait fidèlement le firmware de SA date ; il décrit l'**inverse** de celui-ci. ⛔ Il n'est ni effacé ni réécrit — c'est un relevé, pas une opinion. La **barre du haut**, elle, reste morte, et c'est le témoin négatif d'AC5.6.

✅ Le compteur de **`taps`** vit dans **`nav`**, pas dans `touch` — c'est ce qui manquait au relevé
précédent, et l'entrée de ledger créée le matin même est **soldée le jour même**.

### 13.17.6 🔴 DEUX DÉFAUTS NEUFS, ET LE PREMIER EST DANS UN CORRECTIF DE LA REVUE

#### (a) LE TÉMOIN POSITIF DE `i2c rafale` EST TROP STRICT — une garde qui ne peut JAMAIS être verte

```
temoin positif  : 0x20 vu 1300/1320 passes · 0x5D vu 1298/1320
🔴 TEMOIN POSITIF EN ECHEC
```

La revue du 2026-08-20 a ajouté ce témoin parce que la rafale n'en avait aucun — un bus coincé
publiait une « cadence » qui aurait été **une cadence de NACKs**. ✅ **Le besoin était réel.**
⛔ **Mais il exige 100 % sur 1 320 passes, sur un instrument dont CE FICHIER documente déjà les faux
négatifs** (§13.2 : *« 3 composants SOUDÉS ont raté une confirmation »*). ⇒ **Il ne peut structurellement
jamais être vert sur une longue fenêtre.**

🔴 **C'est exactement la faute que ce chapitre traque, commise dans un correctif écrit pour la
corriger** : une garde qui se déclenche toujours est aussi inutile qu'une garde qui ne se déclenche
jamais. ⇒ **Recette pour solder** : un **seuil**, calibré sur le taux ci-dessous, ⛔ pas 100 %.

**ET IL A PRODUIT UNE DONNÉE QUE PERSONNE N'AVAIT :**

| Témoin | Manqués | **Taux de faux NÉGATIF** |
|---|---|---|
| `0x20` TCA9554 | 20 / 1 320 | **1,52 %** |
| `0x5D` GT911 | 22 / 1 320 | **1,67 %** |

⇒ **Première mesure À L'ÉCHELLE du taux de faux négatifs de `i2c_master_probe()` sur cette carte.**
Le dépôt n'avait jusqu'ici qu'un décompte anecdotique (*« 3 composants, une fois chacun »*). ⚠️ Et
`timeouts : 0` sur les 147 922 sondages ⇒ **ces manques sont des NACKs, pas des expirations** : un
device sain, soudé, refuse d'acquitter une fois sur soixante.

#### (b) `dn_console.py` PERD DES LIGNES EN INVOCATION **SOLO**, pas seulement en lot

L'entrée de ledger ouverte le matin limite le défaut au **mode lot**. **La séance l'a pris sur le
fait en SOLO, trois fois** :
- une capture de `i2c ecrire 77 D0` a rendu **10 lignes sur 14** — **4 lignes perdues** au milieu du
  bloc d'avertissement, puis **6 captures identiques consécutives ont rendu les 14** ⇒ **1 perte sur 7** ;
- la capture de `capteurs` du **cycle 1** est revenue **entièrement vide** alors que la console avait
  rendu **écho ET invite** ;
- idem au **cycle 6**.

🔴 **CONSÉQUENCE MÉTHODOLOGIQUE, ET ELLE EST LOURDE** : la parade écrite (*« invocations SOLO +
invariant vérifié »*) est **INSUFFISANTE**. ⛔ Une capture vide **ne prouve pas** une carte muette —
aux cycles 1 et 6, l'invite rendue prouvait que le CPU tournait, et **re-sonder a rendu la sortie
complète**. ⇒ **Toujours re-sonder avant de conclure au silence.**

### 13.17.6 bis ⚠️ UNE TROISIÈME ÉTIQUETTE QUI MENT, QUE LA REVUE 3 COUCHES N'AVAIT PAS VUE

La revue de code du 2026-08-20 en avait trouvé **deux** (§13.7 et §13.13.6). Un simple `grep` de
vérification, en fin de séance, en a trouvé une **troisième** — et elle est **prospective**, donc du
même genre que les deux autres :

> §13.6 ter : *« Ce que ce choix N'ENGAGE PAS : les 3 capteurs de **dn4-1**. […] mais
> BH1750/**VL53L0X**/INA219 se ré-arbitrent chacun sur le même critère 1. »*

⇒ **Corrigée par ajout**, comme les deux autres.

🔴 **CE QUE ÇA ENSEIGNE, ET C'EST LE POINT** : trois couches de revue adversariales, lancées en
parallèle et sans contexte, ont trouvé **2 survivantes sur 3**. Le `grep` qui a trouvé la troisième
tient en une ligne. ⇒ **Une revue par lecture ne remplace pas un contrôle mécanique exhaustif** ;
les deux se complètent, et celui qui coûte le moins n'est pas celui qu'on croit.
⚠️ **Recette, pour les prochaines** : après toute story qui renomme quoi que ce soit, passer
`grep -rn '<ancien nom>'` sur **tout** le dépôt et **trier à la main** historique contre prospectif.

### 13.17.7 ✅ AC12 — LES BUDGETS, SUR LE FIRMWARE RÉELLEMENT LIVRÉ ET AU BOOT PROPRE

⚠️ **Ce relevé remplace celui de §13.16.14**, qui portait sur `43e108f` alors que le livrable était
`3a7d938` puis `e931c31` — écart relevé par la revue de code.

| Ressource | `1156eac` (dn4-6) | **`8c928db` (LIVRÉ)** | Δ |
|---|---|---|---|
| **Binaire** | 943 712 o | **956 128 o** | **+12 416 o (+1,32 %)** — partition **77 % libre** |
| **RAM interne libre** | 92 315 o | **92 275 o** | **−40 o (−0,04 %)** |
| **PSRAM libre** | 7 768 236 o | **7 768 236 o** | **0,00 %** |
| **Tas LVGL utilisé** | 20 504 o (34 %) | **20 500 o (34 %)** | −4 o |
| **Plus gros bloc** | 40 752 o | **40 752 o** | **0** |
| **Fragmentation** | 2 % | **2 %** | **0** |
| **`fps 15`** | 37,40 Hz | **37,40 Hz** (×2 fenêtres) | **+0,00 %** |
| **Boot** | 2 321 ms | **2 332 ms** | +11 ms |
| **`nav ab 40`** | 334,4 ms (291,1 / 396,7, n=80) | **334,2 ms (286,8 / 396,4, n=80)** | −0,2 ms |

🎯 **LE « ZÉRO COÛT EN RÉGIME » EST MESURÉ EN MÉMOIRE, PAS ASSERTÉ.** Le relevé précédent était pris
**avant** le commit qui modifie `dn_capteurs.c` ; celui-ci porte sur le firmware qui contient **tous**
les correctifs. **La RAM interne bouge de 40 octets et la PSRAM de zéro.**

> 🔴 **ÉCART DÉCLARÉ — REVUE DE CODE DU 2026-08-24, DÉCISION OWNER.** Cette affirmation disait
> *« mesuré, pas asserté »* **sans qualifier**, et la table ci-dessus publie **neuf** des **dix**
> lignes qu'AC12 énumère : **`cpu brut` (encadrant) MANQUE**, et `grep -n "cpu"` sur tout §13.17 ne
> rend aucune mesure de CPU. ⛔ **Or `cpu brut` est PRÉCISÉMENT l'instrument que le constat de la
> revue du 2026-08-20 mettait en cause** — il reste relevé sur **`43e108f`**, donc **avant** le
> commit qui ajoute au chemin dégradé de `config_verifier_et_reparer()` (cadence **5 s**) un
> `relever_identite()` de **deux transactions I²C à 200 ms de timeout**. ⇒ **AC12 est soldé EN
> MÉMOIRE et ASSERTÉ EN CPU.** L'owner a tranché de **déclarer l'écart plutôt que d'ouvrir une
> séance** — d'autant qu'un `cpu brut` relevé aujourd'hui porterait sur un HEAD **45 commits plus
> loin** et ne dirait rien de `8c928db`.

⚠️ **PIÈGE DE §13.16.14 REPRODUIT À L'IDENTIQUE, ET C'EST POUR ÇA QUE LE TAS EST RELEVÉ AU BOOT
PROPRE** : après les campagnes, `nav` rendait **fragmentation 40 %, plus gros bloc 25 028 o** — contre
**2 %** et **40 752 o** au boot propre. *« Un chiffre faux mais plausible est plus dangereux qu'un
chiffre absurde — celui-là était les deux. »* **Le relevé ci-dessus a été pris AVANT toute campagne.**

### 13.17.8 ✅ AC13 — les gardes restent vertes, et TROIS le sont désormais PAR LA MESURE

| Garde | Mesuré le 2026-08-20 |
|---|---|
| **BME680 vivant** | ✅ `VIVANT` · `config LUE (conforme)` `0x72=04 · 0x74=84 · 0x75=08` · `err_i2c 0` — **et re-vivant APRÈS un démarrage à froid dégradé**, sans intervention |
| **RTC vivante** | ✅ `0x51` **5/5** au scan · témoin anti-fantôme `0xD7` **relu** · ⚠️ `OS = 1` **attendu** après les 6 coupures physiques (§13.15.3 : aucune sauvegarde RTC), barre en « --:-- HEURE NON POSÉE » ⇒ **la garde a fonctionné** |
| **« toute la case est la zone tactile »** | ✅ **re-prouvée sur D12 AVEC LES COORDONNÉES** — 9 visées `RAM` ⇒ 9 taps (§13.17.5) |
| **Barre et MENU = zones mortes** 🔴 *(PÉRIMÉE À MOITIÉ le 2026-08-25 par `dn3-3` : le bandeau `MENU` est devenu une VRAIE PORTE vers `DN_VUE_MENU` et son compteur MONTE. Ce relevé décrit fidèlement le firmware de sa date — ⛔ il n'est ni effacé ni réécrit. Ce qui reste à tenir est « la BARRE est une zone morte », re-tiré par `dn3-3`/AC5.6 comme témoin négatif.)* | ✅ **`0 tap sur MENU` sur 38** |
| **Bandeau de boot** | ✅ **une seule ligne `E`** : celle de l'ISR, **nommée et rattachée** (AC11). ⛔ **Aucune nouvelle** |
| **Smoke owner 6/6** | ✅ constat owner sur le boot du firmware livré : grille affichée, six cases, rétroéclairage **allumé fixe**, rien d'anormal — ⚠️ **SANS VERBATIM** (écart déclaré le 2026-08-24 matin) → ✅ **UN CONSTAT OWNER A ÉTÉ RECUEILLI LE SOIR MÊME sur `8a1dac9`, après TROIS flashs — voir §13.22.6.** ⛔ Recueilli **par question fermée**, donc toujours **pas un verbatim libre** ⤵ |

> 🔴 **ÉCART DÉCLARÉ — REVUE DE CODE DU 2026-08-24, DÉCISION OWNER.** C'est la **seule** ligne
> « constat owner » de tout §13.17 **sans citation**, alors que les quatre autres en portent une
> (*« oui barre rouge plein sur la case ram »*, *« reactivité normal, tt est nickel »*, *« oui c'est
> moi »*, *« 11h14 alors que ça a commencé vers 12h45 ? »*). Le verbatim *« reste ok »* transcrit
> plus haut se rapporte au smoke du **2026-08-20 sur `e931c31`**, ⛔ **pas au livrable `8c928db`**.
> ⚠️ **Et le second verbatim, *« oui revivant »*** — que les Completion Notes de la story citent comme
> preuve à l'œil de la boucle de reprise — **est introuvable dans tout le dépôt** (`git grep` → zéro).
> ⛔ **Un constat à l'œil est l'owner, JAMAIS l'agent** : le fabriquer a posteriori serait exactement
> la faute que §13.3 interdit. ⇒ **AC13 est tenu par le smoke du 2026-08-20 et par les compteurs**,
> et la boucle de reprise **par le compteur, pas par l'œil**.


### 13.17.9 ✅ AC8 — LE RÉGIME LONG À HUIT DEVICES, **CHRONOMÉTRÉ**

⚠️ **Ce relevé remplace la fenêtre de 15 s de §13.16.10**, que la revue de code du 2026-08-20 a
épinglée comme représentant **0,16 %** de la référence.

**Couple encadrant, compteurs remis à zéro à T0 (`touch reset` + `capteurs reset`) :**

| | T0 | T1 |
|---|---|---|
| Horloge **locale CEST** | **12:44:13** | **13:15:45** |
| **Durée CHRONOMÉTRÉE** | — | 🔴 **31 min 32 s = 1 892 s** — ⛔ **pas déduite d'un compteur** |
| GT911 — lectures | 0 | **53 652** |
| GT911 — **erreurs I²C** | 0 | 🎯 **0** |
| BME680 — lectures | 0 | **378** |
| BME680 — erreurs (`i2c` / `donnee` / `bornes`) | 0 / 0 / 0 | 🎯 **0 / 0 / 0** |
| BME680 — état | `VIVANT` | `VIVANT` · `config LUE (conforme)` `0x72=04 · 0x74=84 · 0x75=08` |
| `fps 15` | 37,40 Hz | **37,40 Hz** (relevé en cours de régime) |

**Contrôles dérivés, qui valident les compteurs entre eux :**
- **Cadence BME680** : `1 892 s / 378 lectures` = **5,005 s** contre 5 000 ms nominaux. ✅ La cadence
  en temps absolu (`vTaskDelayUntil`) tient sur une demi-heure.
- **Cadence GT911** : `53 652 / 1 892` = **28,4 lectures/s** — cohérent avec le sondage ~30 Hz.
- **Scan de contrôle** en fin de régime : **8 stables**, témoin positif vert.

⚠️ **LE RÉGIME N'ÉTAIT PAS STRICTEMENT AU REPOS, ET C'EST ÉCRIT** : `appuis 1 · relâches 1`, avec
**841 IRQ**. 🔴 **Le tap est ATTRIBUÉ, pas seulement constaté** : l'owner l'a revendiqué
(*« oui c'est moi »*). ⛔ *« 1 appui, cause inconnue »* aurait ouvert une question ; *« 1 appui,
l'owner »* la ferme. Un tap ne fabrique aucune erreur I²C, et le compteur est resté à 0.

🔴 **CE QUE CE RELEVÉ NE PRÉTEND PAS ÊTRE, ET IL FAUT LE LIRE AVANT DE LE CITER.**

| | Référence `dn2-1` | **Ce relevé** |
|---|---|---|
| Devices sur le bus | **5** | 🎯 **8** |
| Lectures GT911 | **279 604** | **53 652** — soit **19,2 %** |
| Erreurs I²C | **0** | 🎯 **0** |
| Durée | *« ~2 h 45 »* | **31 min 32 s** |
| **Nature de la durée** | ⛔ **DÉDUITE** (`279 604 / 30 Hz`) — une **estimation**, pas une mesure | ✅ **CHRONOMÉTRÉE** à l'horloge de l'hôte |

⇒ **Le budget d'erreurs tient à 8 devices : 0 erreur sur 53 652 lectures.** ⛔ **Mais la fenêtre
reste 5,2× plus courte que la référence en nombre de lectures, et c'est déclaré, pas arrondi.**
✅ **En revanche, elle est CHRONOMÉTRÉE là où la référence était DÉDUITE** — c'est exactement ce
qu'AC8 exigeait (*« la durée de régime est CHRONOMÉTRÉE, pas déduite du compteur ; les deux sont
publiées séparément si elles divergent »*). **Sur ce point précis, ce relevé est meilleur que sa
référence.**

⚠️ **Le résultat des tirages (Y6) relu à la lumière du budget**, comme l'AC le demande : **aucune**
erreur n'est apparue, donc **le suspect nommé d'avance — la résistance équivalente des tirages, qui
passe de 2 à 4 jeux en parallèle, soit `+0,66 mA` à l'état bas contre une limite de 3 mA — n'a pas eu
à être instruit.** Il reste nommé pour la prochaine fois.

⚠️ **CE QUE CE RÉGIME NE COUVRE PAS** : il est tenu **à chaud**, après un boot sain. 🔴 **La
non-régression est établie EN RÉGIME, ⛔ pas AU DÉMARRAGE À FROID** — §13.17.1 montre qu'un cycle sur
six part avec **55,5 % d'erreurs** pendant ~40 s. **La distinction est écrite plutôt que gommée.**

---

## 13.18 ⚠️ CE QUI N'A PAS MARCHÉ DANS CETTE SÉANCE — y compris mes propres erreurs de méthode

1. 🔴 **J'AI PUBLIÉ LES HORODATAGES EN `UTC` À QUELQU'UN QUI LIT `CEST`.** L'owner l'a relevé en une
   phrase : *« 11h14 alors que ça a commencé vers 12h45 ? »*. Le chiffre était **juste**, l'étiquette
   `UTC` était **écrite** — et le lecteur l'a quand même lu faux, parce qu'il lit sa montre.
   ⇒ **Un chiffre juste que le lecteur lit faux est un chiffre faux.** C'est la thèse de ce chapitre
   appliquée à une unité de temps, et c'est l'agent qui s'est fait prendre.
   ✅ **Règle** : dans une séance carte, horodater en **heure locale**, ou porter **les deux**.

2. ⚠️ **MON PROPRE `grep -c` M'A RENDU UN FAUX POSITIF**, à la fin de la séance : `ps aux | grep -cE
   '[d]n_console|[i]df.py monitor'` a rendu **3** là où `lsof /dev/ttyACM0` et un `ps` non compté
   rendaient **zéro** — le motif comptait la ligne de commande du sous-shell qui le portait.
   ⛔ C'est **exactement** le piège déjà consigné (*« le hook a fabriqué un faux positif "2 processus
   `idf.py monitor`" en faussant un `grep -c` »*), re-produit avec un autre outil.
   ✅ **Vérifié avant de conclure** — un lecteur résiduel du port aurait corrompu toutes les captures
   **en silence**. ⇒ **Un compte de processus se confirme par `lsof`/`fuser`, ⛔ jamais par `grep -c`.**

3. ⚠️ **J'ai lancé le relevé de clôture d'AC8 en tâche de fond ET pris le relevé à la main**, ce qui
   allait ouvrir **deux lecteurs simultanés** sur `/dev/ttyACM0`. Rattrapé avant l'ouverture — mais
   c'est le défaut n°1 de la boucle de travail de ce dépôt (*« deux lecteurs ne s'excluent pas : ils
   se volent les octets sans erreur »*), et je l'ai frôlé.
   ✅ **Règle** : ⛔ **jamais de relevé série armé en tâche de fond** tant qu'une session interactive
   peut toucher le même port.

4. ⚠️ **La revue 3 couches avait laissé passer une étiquette qui ment sur trois** (§13.17.6 bis).
   Un `grep` d'une ligne l'a trouvée. **Une revue par lecture ne remplace pas un contrôle mécanique.**

---

## 13.19 — SÉANCE `dn4-3` « Exploiter les capteurs » (2026-08-20)

> **Ce que cette section couvre** : la marche **P9.3**. Ce que les trois capteurs soudés en `dn4-2`
> valent, et à quoi on les dépense. ⛔ **Elle ne réouvre PAS la cause de la dégradation du bus à
> froid** (§13.17.1) : l'epic la garde **hors périmètre**, comme **contrainte de conception**.

### 13.19.1 ✅ T0 — LE POINT DE DÉPART, PROUVÉ SUR `2992181`

**Firmware `2992181`, SHA LU AU BANDEAU** (`I (665) app_init: App version: 2992181`),
**`git status --porcelain` vérifié VIDE AVANT le flash**, build refait après. Compile time
`Aug 20 2026 15:02:49`.

⚠️ **Pourquoi ce T0 était nécessaire alors que « HEAD est fonctionnellement `8c928db` »** : la
phrase est vraie *du code* (`8c928db..HEAD` = 423 insertions, **0 ligne** de `firmware/`), mais
**un bandeau qui affiche `8c928db` ne prouve rien sur un dépôt à `2992181`**. Le T0 se relève sur
le SHA qu'on va modifier, ⛔ pas sur son ancêtre fonctionnel. ✅ **Et la prédiction se vérifie** :
le binaire fait **exactement 956 128 o**, au *même octet* que `8c928db`.

**Configuration d'affichage de référence, relue au bandeau d'état** — ⛔ elle NE BOUGE PAS (AC13) :
`num_fbs=1` · `bounce=7680 px` · `draw buffer 480 × 128 px en RAM interne DMA` · synchro `vsync` ·
LVGL **ACTIF** · **6/6 cases** · rétroéclairage **100 %**.

#### a) Budget statique et tas — **AU BOOT PROPRE**, ⛔ pas après campagne

| Ressource | **T0 `2992181`** | `8c928db` (`dn4-2` §13.17.7) | Écart |
|---|---:|---:|---|
| Binaire | **956 128 o** | 956 128 o | **0** — partition **77 % libre** |
| RAM interne libre | **92 307 o** | 92 275 o | +32 o (bruit d'allocation) |
| PSRAM libre | **7 768 236 o** | 7 768 236 o | **0** |
| Tas LVGL utilisé | **20 500 o (34 %)** | 20 500 o (34 %) | **0** — ⚠️ relevé par **`ui`**, ⛔ pas `mem` |
| Plus gros bloc / fragmentation | **40 752 o / 2 %** | 40 752 o / 2 % | **0** |
| Boot | **2 332 ms** depuis `app_main` | 2 332 ms | **0** |
| `fps 15` | **37,40 Hz** (561 trames / 14 999 367 µs), écart **+0,00 %** | 37,40 Hz | **0** |
| `nav ab 40` (n=80) | **334,6 ms** (281,1 / 396,4) | 334,2 ms (286,8 / 396,4) | **+0,4 ms** ⇒ **bruit** (±16 ms) |

✅ **Non-fuite `nav ab 40`** : tas LVGL **20 500 → 20 472 o (−28 o)**, RAM interne **0**, PSRAM **0**.

✅ **`descripteurs_auditer()` au boot : 6 cases auditées, 0 trou.** C'est la référence d'AC11.

#### b) L'état du bus à huit devices

- **Scan** : `0x20 · 0x23 · 0x29 · 0x40 · 0x51 · 0x5D · 0x6B · 0x77` — **8 stables, 0 instables en
  38 ms**, **témoin positif VERT** (expander **et** tactile stables).
- **`touch`** : IRQ 22 · **1 619 lectures** · **`err_i2c` = 0**.
- **`capteurs`** : BME680 **VIVANT**, `config LUE : 0x72=04 · 0x74=84 · 0x75=08 (conforme)`,
  cadence **4 999 ms MESURÉS** entre les deux dernières lectures valides, cycle **26 ms**,
  erreurs **i2c 0 · donnee 0 · bornes 0**.

⚠️ **Le boot de ce T0 était un reset RTS, ⛔ pas un démarrage à froid** : la dégradation §13.17.1
**ne pouvait donc pas s'y présenter** (mesuré `dn4-2` : 0 échec sur 4 en `--reset`). ⇒ ce `err_i2c 0`
qualifie **un bus chaud**, et rien d'autre. La tolérance à froid est l'objet d'AC3, ⛔ pas de ce T0.

#### c) Le régime, avec son **espacement déclaré**

**Stimulus** : `tools/dn_injecteur.py --jeu reel --secondes 45 --espacement 0.004` ⇒ **225 trames**.
Compteurs remis à zéro **avant** (`flush reset`, `touch reset`, `pc reset`), **settle de 3,5 s**
après la fin de l'injection **avant** la lecture (⚠️ `flush reset` ne vide pas la file en vol).

| Grandeur | **T0 `2992181`** | Point de comparaison |
|---|---:|---|
| flush / cycle | **2,7** | 2,4 — §13.16.13, **firmware `dn4-2` AVANT correctifs** |
| px / cycle | **97 800** | 87 196 — *idem* |
| plus grande aire | **36 675 px** | 36 675 — *idem* ⇒ **l'unité de case n'a pas bougé** |
| copie | **2 992 µs/flush** (pire **3 193**) | 2 979 — *idem* |
| attente de synchro | **12 686 µs/flush** | — |
| Liaison | **224/225 valides · 1 perte seq · 0 rejet de TOUTE cause** | 224/225, 1 perte, 0 rejet — *idem* |
| Latence acceptation→label | **n=224 · min 29 · moy 86 · max 131 ms** | n=224 · 60 / 109 / 180 ms — *idem* |
| `touch` encadrant | **1 265 lectures · 0 erreur I²C** | 1 026 lectures · 0 → 0 |

🔴 **⛔ CES ÉCARTS NE SONT PAS DES DELTAS, ET IL FAUT LE DIRE** : la colonne de droite vient d'un
**AUTRE SHA** (§13.16.13, séance `dn4-2` **avant** les correctifs de revue). *« Un delta entre deux
SHA différents n'est pas un delta. »* ⇒ **la colonne de gauche EST la baseline de `dn4-3`**, et
c'est contre **elle seule** qu'AC12 comparera le firmware livré.

#### d) CPU en régime calme — **fenêtre chronométrée**, ⛔ pas `cpu N`

**Méthode** : deux `cpu brut` encadrants ; la fenêtre est le **delta du champ `total`**, ⛔ pas une
durée déduite d'une horloge de PC. **Fenêtre mesurée : 30 125 749 µs = 30,126 s.**
⚠️ `cpu N` est **AVEUGLE au trafic** (il dort la fenêtre, **et le REPL EST le transport**).

| Tâche | **T0 `2992181`** | Référence `dn4-2` (fenêtre 30,2 s) |
|---|---:|---:|
| `taskLVGL` | **2,270 %** | 2,31 % |
| `esp_timer` | **0,700 %** | 0,68 % |
| `dn_rtc` | **0,129 %** | 0,17 % |
| 🔴 **`dn_capt`** | 🔴 **0,068 %** | 0,09 % |
| `console_repl` | **0,059 %** | 0,05 % |
| `dn_link` | **0,020 %** | — |
| `main` | **0,018 %** | — |
| **cœur 0** | **3,249 %** (IDLE0 96,751 %) | 3,31 % |
| **cœur 1** | **0,015 %** (IDLE1 99,985 %) | 0,04 % |

✅ **TEST DE RÉCONCILIATION PASSÉ** : somme des deltas de toutes les tâches **60 251 406** contre
`fenêtre × 2` = **60 251 498** ⇒ **199,9997 %** pour 200 % attendus, écart **0,0003 pt** (seuil
±0,01). ⛔ Sans ce test, une colonne peut être fausse d'un facteur 2 — c'est arrivé.

🔴 **`dn_capt = 0,068 %`, ET C'EST LE BME680 SEUL.** Les trois nouveaux capteurs n'ont aujourd'hui
**aucune tâche, aucun timer, aucune allocation**. ⇒ **C'est CE chiffre-là que `dn4-3` fait bouger,
et c'est lui qu'AC12 doit prédire AVANT de le mesurer.**

### 13.19.2 🔴 LES CRITÈRES D'ARBITRAGE DU DRIVER — écrits et horodatés **AVANT** d'ouvrir un source (`dn4-3`, 2026-08-20 **15:11 CEST**)

> 🔴 **CETTE SECTION EST ÉCRITE AVANT TOUTE LECTURE DE CODE CANDIDAT ET AVANT TOUTE
> INTERROGATION NEUVE DU REGISTRE.** C'est le patron **§13.6 ter**, et il existe pour une raison
> précise : *des critères écrits après coup ne sont pas des critères, ce sont des justifications.*
> ⚠️ **Ce qui était déjà connu** : la pré-lecture du registre faite au **cadrage** de la story
> (2026-08-20, §6 de `dn4-3-exploiter-les-capteurs.md`). Elle est un **point de départ daté**,
> ⛔ **pas un verdict**, et §13.19.3 la **rejoue**.

#### Les critères, par ordre décroissant de pouvoir éliminatoire

| # | Critère | Nature | Pourquoi il existe |
|---|---|---|---|
| **C1** | **Le composant accepte un `i2c_master_bus_handle_t` DÉJÀ CRÉÉ** | ⛔ **ÉLIMINATOIRE** | `dn_display` possède l'unique bus (`dn_display_i2c_bus()`). Un second `i2c_new_master_bus()` sur `I2C_NUM_0` rend `ESP_ERR_INVALID_STATE`. **A déjà éliminé 3 candidats sur 4** pour le BME680 (§13.6 ter) |
| **C2** | **Aucune dépendance au driver I²C LEGACY** (`i2cdev`, `espressif/i2c_bus`) | ⛔ **ÉLIMINATOIRE** | conflit frontal avec `i2c_new_master_bus` — c'est C1 par un autre chemin |
| **C3** | **ZÉRO `ESP_ERROR_CHECK` (ni `assert`, ni `abort()`) sur un chemin de LECTURE ou d'INIT** | ⛔ **ÉLIMINATOIRE**, sauf garde-fou reproduit | 🔴 C'est le défaut qui **briquait la carte** : `bme680.c:432` enveloppait une lecture I²C sur le chemin nominal ⇒ `abort()` ⇒ `PANIC_PRINT_HALT` ⇒ **console disparue**. Mesuré : **6 briquages sur 7 AVANT → 0 sur 6 APRÈS** la parade (⚠️ compte **non réconcilié** avec le 3/4 de `deferred-work.md:297` — les deux sont conservés). Un capteur au **contact intermittent** briquerait la carte **chez l'owner, sans console** |
| **C4** | **Aucun blocage long sur le bus** — un appel qui dort > **200 ms** est un défaut, pas un détail | ⛔ **ÉLIMINATOIRE** au-delà de 1 s en régime | La lecture tourne dans une tâche cadencée à 5 s sur un bus que **le GT911 pole ~30×/s**, et **l'I²C est le PREMIER AGRESSEUR CONNU de la famine DMA** (§11.4, `bounce_px` 7 680, *« marge franchie, pas confortable »*). ⚠️ Un timeout **bloquant d'UNE SECONDE** par lecture (cas connu de `espressif/bh1750`) est à peser **contre le cycle de 5 s ET contre le bus dégradé à froid** |
| **C5** | **Tolérance native à l'échec** : la fonction rend un `esp_err_t` que l'appelant peut ignorer, et le composant **ne garde pas d'état corrompu** après un échec | fort | §13.17.1 : à froid, **une transaction de donnée sur deux échoue pendant ~40 s**, et ça **se rétablit seul**. Un driver qui se verrouille au premier échec est inutilisable ici |
| **C6** | **Pas d'appel à `i2c_master_bus_rm_device()`** sur un chemin atteignable | fort | 🔴 **MESURÉ SUR CETTE CARTE : ce retrait a REFUSÉ pour de vrai, 1 fois sur 13** (§13.17.3). Un `*_delete()` qui l'appelle est une bombe à retardement |
| **C7** | **Dépendances transitives** : nombre, éditeur, **épinglabilité** | fort | `main/idf_component.yml` est **la seule autorité** (`dependencies.lock` et `managed_components/` sont **gitignorés**). Une transitive non épinglée est le défaut exact que la revue a corrigé sur `k0i05/esp_type_utils` |
| **C8** | **Adoption et maintenance** : téléchargements, date de publication, licence | moyen | ⚠️ **11 téléchargements** (cas `tny-robotics/ina219-esp-idf`) ⇒ **lecture de source OBLIGATOIRE**, pas un rejet automatique. *« provided as-is, no further development »* n'est pas éliminatoire non plus : ce dépôt lit le source de toute façon |
| **C9** | **Lisibilité** : combien de lignes de code étranger on adopte sans les relire | moyen | 🔴 **Le contre-poids honnête** : `dn_console.c` parle **déjà** aux trois capteurs en `i2c_master_transmit_receive` nu, retour testé, via `i2c_dev_ouvrir()` / `i2c_ecrire_nu()` / `i2c_lire_brut()` / `i2c_lire_registre16()`. **Pour le BH1750, le driver entier tient en TROIS transactions.** ⇒ **le driver maison n'est pas une paresse, c'est un candidat de plein droit** |
| **C10** | **Coût binaire et RAM interne** une fois **RÉELLEMENT LIÉ** | moyen | ⚠️ **Piège déjà payé** : `k0i05/esp_bme680` au manifeste mais non appelé ⇒ **binaire INCHANGÉ**, et publier *« le composant coûte 0 o »* aurait été un mensonge. **Le coût ne se mesure qu'APRÈS l'appel** (il a valu **+26 992 o**). ⚠️ RAM interne libre au T0 : **92 307 o**, et la marge DMA est **déjà consommée** |

#### 🔴 Ce qui, écrit d'avance, ferait **renverser** un verdict

- Un composant retenu qui **ne compile pas** avec l'IDF v5.5.5 épinglée ⇒ retour au maison.
- Un driver maison dont la **conversion** est fausse ou invérifiable ⇒ retour au composant.
  ⚠️ **Précédent exact et récent** : `lux10 = (brut * 10) / 12` publiait **`4 614,8` pour `46 148`**,
  et **c'est passé TROIS publications parce que le chiffre était PLAUSIBLE**.
- Un coût binaire ou RAM interne **disproportionné une fois lié** (référence : **+26 992 o** pour
  le BME680) ⇒ ré-arbitrage, et **le chiffre est publié**.

#### 🔴 Le critère W2 — écrit ici aussi, parce qu'il se joue AVANT le tir (AC6)

Toute grandeur candidate à une **case** qualifie sur la **valeur AFFICHÉE** (⛔ pas sur la source) :
**étendue ≥ 5** · **taux de changement du TEXTE ≥ 10 %** · **σ ≥ 1**, sur un échantillonnage annoncé.
Référence : `FAN_RPM` **13 / 55,2 % / 2,02** (n=959) **QUALIFIE** ; le témoin de contrôle
`ASIC_POWER` **3 / 57,9 % / 0,75** **NE QUALIFIE PAS**.
⚠️ **Un lux de bureau à éclairage stable est exactement le candidat qui peut échouer là.**
⇒ **le mesurer, ⛔ pas le supposer.** *Une case morte est un défaut, même si la donnée est locale.*

#### ⛔ Ce que ces critères NE tranchent PAS

Ils arbitrent **tiers vs maison** (X5). Ils **ne disent rien** de **X4** — *où vit le code* :
`dn_capteurs` généralisé **(A)** ou un module à côté **(B)**. **X4 se tranche en §13.19.4**, et les
Dev Notes de la story posent la borne : *« une seule tâche qui lit tout est probablement plus sûre…
⛔ ça se mesure, ça ne se suppose pas »*.

### 13.19.3 ✅ LE REGISTRE, REJOUÉ (2026-08-20 15:12 CEST) — il a rendu **un candidat de plus** et **démenti un verdict**

**Méthode** : `GET https://components.espressif.com/api/components?q=<mot>` puis
`GET …/api/components/<ns>/<nom>` pour les versions, licences et **compteurs de téléchargement**
(champ `downloads_total`, sommé sur toutes les versions).
⚠️ **Les mots interrogés sont écrits** : `bh1750` · `ina219` · `vl6180` · `vl6180x` · `vl53` · `tof`
· `proximity`. ⛔ Un relevé qui ne dit pas ce qu'il a cherché ne peut pas prouver une absence.

#### BH1750 — **10 réponses**, dont **4 vrais pilotes**

| Composant | Ver. | Publié | Licence | Dépendances | Téléch. | C1/C2 |
|---|---|---|---|---|---:|---|
| **`espressif/bh1750`** | **2.0.0** | 2025-09-23 | Apache-2.0 | **`idf >= 5.3` SEULE** | **7 147** | ✅ prend le bus |
| `k0i05/esp_bh1750` | 1.2.7 | 2025-08-29 | MIT | `k0i05/esp_type_utils >= 0.0.1` — ⚠️ **NON épinglée** | 67 | ✅ prend le bus |
| `esp-idf-lib/bh1750` | 1.1.7 | 2025-07-31 | BSD-3 | **`i2cdev`** + `esp_idf_lib_helpers` | — | ⛔ **C2** |
| 🆕 **`achimpieters/esp32-bh1750`** | **1.0.1** | 2025-03-17 | MIT | `idf >= 5.0` seule | 36 | ⛔ **voir ci-dessous** |

> 🆕 🔴 **CE QUATRIÈME CANDIDAT N'ÉTAIT PAS DANS LA PRÉ-LECTURE DU CADRAGE.** C'est exactement
> pourquoi AC4 exige de **rejouer** le registre : *un relevé daté vaut comme point de départ, pas
> comme verdict.* ⇒ **Et il est éliminé DEUX FOIS** : `#include <driver/i2c.h>` (**LEGACY**, C2) et
> `bh1750_init_desc(i2c_dev_t*, uint8_t addr, i2c_port_t port, gpio_num_t sda, gpio_num_t scl)` —
> **il configure les broches lui-même** (C1). ⚠️ Sa fiche au registre ne le dit **nulle part** :
> il a fallu **ouvrir le source**.

Également retournés, **non pilotes BH1750** et écartés sans arbitrage : `espressif/extended_vfs`,
`espressif/esp32_azure_iot_kit` (agrégat, **target `esp32` seul**), `sensmonitor/smonitor-i2c`
(⛔ `espressif/i2c_bus` ⇒ C2), `h-000-h/mini_tree`, `h-000-h/mini-tree`, `shaxzodahmedov/risaldash`.

#### INA219 — **7 réponses**, dont **3 pilotes**

| Composant | Ver. | Publié | Licence | Dépendances | Téléch. | C1/C2 |
|---|---|---|---|---|---:|---|
| **`tny-robotics/ina219-esp-idf`** | **1.0.0** | 2026-05-11 | MIT | **aucune** | **11** | ✅ prend le bus |
| **`zorxx/ina219`** | **1.0.3** | 2026-07-04 | BSD-3-Clause | **aucune** | 24 | ✅ **voir la réfutation** |
| `esp-idf-lib/ina219` | 1.0.7 | 2025-07-31 | BSD-3 | **`i2cdev`** | — | ⛔ **C2** |
| `sensmonitor/smonitor-i2c` | 0.1.1 | 2026-07-27 | Apache-2.0 | **`espressif/i2c_bus`** | — | ⛔ **C2** |

> 🔴 **RÉFUTATION D'UN VERDICT DU CADRAGE — `zorxx/ina219` N'EST PAS ÉLIMINATOIRE.**
> §6 de la story le classait *« ⛔ ÉLIMINATOIRE — API `i2c_lowlevel_config{port, pin_sda, pin_scl}`
> ⇒ **il crée son bus** »*. **Le source dit l'inverse**, et il le dit en commentaire
> (`include/ina219/sys_esp.h:13-17`) :
> *« If bus == NULL, port, pin_sda, and pin_scl will be used to initialize the I2C bus, otherwise
> it's assumed that a previous call was made to i2c_new_master_bus »*.
> `lib/esp-idf.c:47-68` : la création est **dans une branche `if (NULL == config->bus)`**, et le
> chemin `bus != NULL` fait un simple `i2c_master_bus_add_device(*l->config.bus, …)`.
> ⇒ ✅ **C1 SATISFAIT.** ⛔ **La pré-lecture avait lu la structure de config sans lire la branche.**
> **C'est écrit ici, pas corrigé en silence** — et c'est le deuxième point que le rejeu a gagné.

#### VL6180X — 🔴 **L'ABSENCE EST CONFIRMÉE, ET PAR UNE 404**

| Requête | Réponse HTTP | Contenu |
|---|---|---|
| `q=vl6180` | **404** | `{"error":"ComponentNotFoundError","messages":["No component found"]}` |
| `q=vl6180x` | **404** | *idem* |
| `q=vl53` | 200 | `espp/vl53l` 1.1.8 · `rjrp44/vl53l5cx` 4.0.1 · `rjrp44/vl53l8cx` 4.0.1 · `grrtzm/v53l7cx-library` 1.0.6 · `saleca/vl53l1x_uld_esp_wrapper` 0.0.6 · `grrtzm/vl53l1x_library` 0.3.1 · `pkolt/vl53l0x` 1.0.0 — ⛔ **tous des VL53Lxx, puce DIFFÉRENTE** |
| `q=tof` | 200 | rien de pertinent (`esp32-camera`, `radiolib`, `nlohmann-json`…) |

⇒ ✅ **Le fait hérité TIENT : il n'existe AUCUN composant VL6180X au registre.**
⛔ **Un driver maison est donc OBLIGATOIRE pour l'ALS**, quelle que soit la décision sur les deux
autres. **Ce n'est pas une préférence, c'est le registre qui le dit.**

### 13.19.4 🎯 X5 et X4 TRANCHÉS — **driver MAISON pour les trois**, **une seule tâche**, module séparé

#### L'audit de source, candidat par candidat — ⛔ lu, pas récité

| Candidat | Lignes (hors ex./tests) | **C3** `ESP_ERROR_CHECK`/`assert`/`abort` | **C4** blocage | **C6** `rm_device` | Verdict |
|---|---:|---|---|---|---|
| `espressif/bh1750` **2.0.0** | **105 + 136** | **1 `assert`** (`bh1750.c:46`) — ⚠️ **placé APRÈS le test `ret != ESP_OK`** d'`i2c_master_bus_add_device`, donc **inatteignable**. ✅ | 🔴 **`pdMS_TO_TICKS(1000)` sur `i2c_master_transmit` (`:24`) ET sur `i2c_master_receive` (`:99`)** — **UNE SECONDE bloquante par transaction** | ⚠️ `bh1750_delete` (`:55`) | ⚠️ **survit à C1-C3, achoppe sur C4** |
| `k0i05/esp_bh1750` **1.2.7** | **397 + 217** | ✅ que des `ESP_RETURN_ON_ERROR` / `ESP_GOTO_ON_ERROR` — **ils RENDENT, ils n'abortent pas** | ⚠️ 500 ms + 🔴 **`vTaskDelay` DANS le chemin de lecture** (`:266`, `:274`, `:291`) et à l'init (`:179`, `:206`, `:235`) | 🔴 **`:241` (chemin d'ERREUR d'init, ATTEIGNABLE)** + `:382` | ⚠️ **+ `i2c_master_probe()` à l'init (`:182`)** — l'entrée de ledger sur les **faux positifs du sondage (1,744 % à 8 devices)** nomme `dn4-3` comme prochain porteur ; **+ transitive non épinglée** ; **+ même éditeur que le composant qui briquait la carte** |
| 🆕 `achimpieters/esp32-bh1750` **1.0.1** | 94 + 68 | ✅ aucun | ✅ 100 ms | ✅ aucun | ⛔ **ÉLIMINÉ C1 + C2** (`driver/i2c.h` legacy, et il configure SDA/SCL) |
| `tny-robotics/ina219-esp-idf` **1.0.0** | **193 + 255** | ✅ **ZÉRO** — vérifié par `grep` sur `ESP_ERROR_CHECK\|ESP_RETURN_ON\|abort(\|assert(\|ESP_GOTO_ON` | ✅ **100 ms** (`:49`, `:55`) | ⚠️ `ina219_delete` (`:191`) uniquement | ✅ **PROPRE** — le meilleur des cinq sur C3/C4 |
| `zorxx/ina219` **1.0.3** | **279 + 241 + portage** | ✅ aucun | ✅ 50 ms (`ina219.c:21`) — ⚠️ mais `xSemaphoreTake(…, portMAX_DELAY)` (`esp-idf.c:149`) | ⚠️ dans `i2c_ll_deinit` | ✅ **C1 satisfait** (réfutation ci-dessus), 3 fichiers de portage à adopter |

#### 🎯 X5 — **DRIVER MAISON POUR LES TROIS.** Le motif, critère par critère

1. **C9 tranche presque seul, et le chiffre est vérifiable** : `dn_console.c` **parle DÉJÀ aux trois
   capteurs**, en `i2c_master_transmit_receive` nu **avec retour testé** — `i2c_dev_ouvrir()`
   (`:4329`), `i2c_lire_registre()` (`:4380`), `i2c_ecrire_nu()` (`:4484`), `i2c_lire_brut()`
   (`:4566`), `i2c_lire_registre16()` (`:4772`). **Le protocole des trois est déjà écrit, exercé, et
   qualifié SUR CETTE CARTE.** Pour le BH1750, le pilote entier tient en **trois transactions**.
2. 🔴 **C3 + le ledger : prendre UN composant rouvre une obligation SANS MÉCANISME.**
   `managed_components/` est **gitignoré**, l'audit des **103 `ESP_ERROR_CHECK`** est **manuel**, et
   *« rien ne signale qu'une mise à jour ait introduit un `abort()` de plus »*. **Zéro composant
   ajouté ⇒ le compte reste à 103 et l'obligation ne s'étend pas.** ⇒ **le garde-fou
   « sonder AVANT d'appeler » n'a rien de neuf à protéger.**
3. 🔴 **C4 élimine le mieux adopté.** `espressif/bh1750` — 7 147 téléchargements, Apache-2.0,
   esp-bsp, **le candidat que l'adoption désignait** — bloque **1 000 ms par transaction**. Sur un
   bus qui **se dégrade 40 s à froid** et dont l'I²C est **le premier agresseur connu de la famine
   DMA** (marge *« franchie, pas confortable »*), **une seconde de blocage dans la tâche capteurs
   est un coût qu'on ne sait pas encore payer.** ⚠️ **Ce n'est pas un défaut du composant** : 1 s est
   un choix raisonnable ailleurs. **C'est une incompatibilité avec CETTE carte.**
4. 🔴 **L'ALS force la main de toute façon** : **AUCUN composant VL6180X n'existe** (404). Prendre un
   tiers pour BH1750 et INA219 laisserait **trois patrons d'erreur, trois politiques de timeout et
   deux entrées de manifeste** pour **un seul module maison de toute manière obligatoire**.
   ⇒ **l'homogénéité vaut plus que la mutualisation.**
5. **C10 n'est pas un argument dans ce sens-ci, et il faut le dire** : le maison **coûtera** du
   binaire lui aussi. La référence est **+26 992 o** pour le BME680 une fois lié ; le maison sera
   **très en dessous**, mais ⛔ **le chiffre se relève APRÈS l'appel**, pas maintenant (AC12).

⏳ **CE QUI RENVERSERAIT CE VERDICT, écrit d'avance** : une conversion maison fausse ou invérifiable
(⚠️ précédent `lux10` : **`4 614,8` publié pour `46 148`**, *passé trois fois parce que plausible*)
⇒ repli sur **`espressif/bh1750` 2.0.0**, dont la conversion `brut / 1.2` est **identique à la
nôtre**, en acceptant son 1 000 ms. **C'est le plan B, il est nommé.**

#### 🎯 X4 — **un module `dn_env` SÉPARÉ, mais cadencé par la tâche `dn_capt` EXISTANTE** (voie C)

⛔ **Ni (A) ni (B) telles qu'écrites.** Les deux voies des Dev Notes portent chacune un défaut que
la lecture du code rend concret :

- **(A) généraliser `dn_capteurs`** ⇒ un `dn_capt_id_t` dans **toute** l'API (`dn_capt_etat`,
  `dn_capt_compteurs`, `dn_capt_age_us`…), consommée par **quatre appelants**, et 🔴 **AC13 le dit
  sans détour : « LA SEULE CASE VIVANTE AUJOURD'HUI EST `AMBIANCE`, ET LA VOIE (A) LA TRAVERSE »**.
  On refactorerait le seul chemin qui marche, pour y ajouter des capteurs qui n'ont ni le même
  protocole, ni le même garde-fou (celui-ci protège d'un **driver tiers** — les trois autres n'en
  ont pas).
- **(B) un second module AVEC SA TÂCHE** ⇒ **deux réveils** sur un bus que le GT911 pole ~30×/s.
  Les Dev Notes posent que *« une seule tâche qui lit tout est probablement plus sûre »*, et AC4
  exige alors **le couple encadrant `touch`/`err_i2c` sur LES DEUX VOIES DANS LE MÊME FIRMWARE**.

✅ **(C) prend le meilleur des deux, et elle est possible parce que le code le permet** — vérifié,
⛔ pas supposé : `dn_capteurs.c:1121-1129` montre que **la tâche `dn_capt` démarre MÊME si le BME680
est injoignable** (`s_dev = NULL`, *« NON FATAL, et la tâche démarre QUAND MÊME »*).

| Propriété | (A) | (B) | ✅ **(C)** |
|---|---|---|---|
| Nombre de tâches sur le bus | 1 | **2** | ✅ **1** |
| API `dn_capt_*` modifiée | 🔴 **toute** | aucune | ✅ **aucune** |
| Surface touchée sur la seule case vivante | 🔴 large | nulle | ✅ **UN appel ajouté** |
| A/B deux-voies exigé par AC4 | non | 🔴 **oui** | ✅ **sans objet — il n'y a pas de 2ᵉ tâche** |
| `dn_capteurs` reste « le module BME680 » (`dn_capteurs.h:8-10`) | ⛔ non | oui | ✅ **oui** |

🔴 **ET LE POINT D'ACCROCHE EST CONTRAINT PAR LE CODE, PAS PAR LE GOÛT** : le corps de
`tache_capteurs()` est **truffé de `continue`** sur chaque chemin d'erreur BME680
(`dn_capteurs.c:952`, `:961`, `:1004`, `:1033`, `:1054`…). ⇒ ⛔ **un appel placé en FIN de boucle
serait SAUTÉ à chaque erreur du BME680 — c'est-à-dire précisément pendant la dégradation à froid,
le seul moment où la tolérance d'AC3 se mesure.**
✅ **`dn_env_cycle()` s'appelle donc IMMÉDIATEMENT APRÈS `vTaskDelayUntil()`**, avant toute branche.
Bénéfice second : la cadence des trois capteurs devient **déterministe**, indépendante du BME680 —
qui, lui, peut bloquer **jusqu'à 1 500 ms**.

⚠️ **LA LIMITE DE (C) EST DÉCLARÉE, PAS CACHÉE** : si `xTaskCreate` échoue,
`dn_capteurs_init()` rend `ESP_ERR_NO_MEM` et **aucune tâche ne tourne** ⇒ **`dn_env` ne serait
jamais cadencé**. ⛔ Il ne doit pas acquitter dans le vide (patron `dn_capteurs.c:1155-1170`).
⇒ **`dn_env` compte ses cycles et la console affiche `JAMAIS CADENCE` tant qu'aucun n'est arrivé.**

🔴 **UN FAIT DE CODE QUI INTERDIT DE RECOPIER LES HELPERS DE LA CONSOLE TELS QUELS** : `i2c_dev_ouvrir()`
**ajoute un device TEMPORAIRE et le retire à chaque appel** — correct pour un REPL, ⛔ **inacceptable
à 5 s en régime** : ce serait **~5 `i2c_master_bus_rm_device()` par cycle**, et ce retrait
**a REFUSÉ pour de vrai, 1 fois sur 13, sur CETTE carte** (§13.17.3).
✅ **`dn_env` ouvre ses devices UNE FOIS à l'init et les GARDE** — exactement le patron de `s_brut`
dans `dn_capteurs.c:1100-1109`.

### 13.19.5 🎯 LA QUALIFICATION DES TROIS À LA CONSOLE — **avant** la première ligne de driver (AC8, AC10)

**Firmware `2992181`.** Toutes les valeurs ci-dessous sont des relevés `i2c` de la console,
⛔ **aucune n'est recopiée d'une datasheet ou d'un article.**

#### a) 🔴 L'ALS DU VL6180X NE MESURE PAS LA LUMIÈRE — et l'instrument le prouve en sept points

Registres identifiés puis **écrits, relus, et confirmés conformes** :
`0x0014` INT_CONFIG (reset `00` → imposé `20`) · `0x003F` ALS_GAIN (reset `06` → imposé `46`,
gain **1,0×, le MINIMUM de la puce**) · `0x0040`/`0x0041` ALS_INTEGRATION (reset `00 00` → imposé
`00 63`). Le déclenchement `0x0038 ← 01` rend bien `0x004F = 0x20`, soit **bits 5:3 = 4 = « new
sample ready »** : ✅ **la chaîne de commande fonctionne, la mesure se déclenche et se signale.**

**Le balayage de la période d'intégration, à gain constant 1,0× :**

| Intégration | 1 ms | 2 ms | 3 ms | 5 ms | 10 ms | 20 ms | 50 ms | 100 ms |
|---|---|---|---|---|---|---|---|---|
| `RESULT__ALS_VAL` (`0x0050`) | `0000` | `0000` | **`FFFF`** | `FFFF` | `FFFF` | `FFFF` | `FFFF` | `FFFF` |

🔴 **RÉPONSE STRICTEMENT BINAIRE.** Une intégration qui fonctionne rend une valeur **proportionnelle
à la durée** ; celle-ci bascule d'un plancher à un plafond entre 2 et 3 ms. ⛔ **Ce n'est pas une
saturation lumineuse** : à gain 1,0× et 100 ms, la pleine échelle est ~20 971 lx, et le BH1750
mesurait **411 lx dans la même pièce au même instant**. C'est un **comparateur saturé**.

⚠️ **CE QUE LE PREMIER RELEVÉ AVAIT FAIT CROIRE, ET QUI ÉTAIT FAUX** : `FFFF` à 100 ms **et** à
10 ms avait été lu comme *« l'intégration n'agit pas »*. Le point à **1 ms**, qui rend `0000`, l'a
**démenti** : le registre agit, il n'y a simplement **aucun point de fonctionnement**.
🔴 *La conclusion la plus dangereuse de cette séance a été corrigée par UN point de mesure de plus.*

**La cause est NOMMÉE, ⛔ pas devinée** : ST impose un **chargement de registres PRIVÉS**
(*« SR03 settings »*) après `SYSTEM__FRESH_OUT_OF_RESET`, et sans lui la puce *« may not perform to
specification »*. ⇒ **Recette de reprise, écrite pour la prochaine story qui en voudra** :
1. Obtenir la séquence **depuis la datasheet ST ou AN4545**, ⛔ **jamais de mémoire ni d'un article**
   — ⚠️ `st.com` était **injoignable depuis cette session** (`curl` → `http=000`), c'est ce qui a
   arrêté la piste, ⛔ pas un jugement sur sa valeur.
2. La jouer **une seule fois**, à l'init, quand `0x0016` vaut `01`.
3. **Rejouer exactement le balayage ci-dessus** : le critère de succès est une réponse
   **proportionnelle**, ⛔ pas « ça rend un nombre ».

⇒ **X7 EST TRANCHÉ : l'ALS n'est PAS retenu comme seconde mesure de lumière dans `dn4-3`.**
🔴 **AC8 se solde donc par un écart NON CHIFFRABLE**, avec sa cause nommée et sa recette.
⚠️ **La décision owner du 2026-08-20** (*« ça permet d'avoir les deux et de les utiliser — meilleur
étalonnage »*) **n'est pas contredite** : elle reste valable *le jour où le SR03 est chargé*. Ce qui
est mesuré ici, c'est qu'**elle n'est pas réalisable aujourd'hui**, et pourquoi.

#### b) 🎯 LA GARDE ANTI-FANTÔME DU VL6180X EXISTE — la piste `0x0016`, jamais vérifiée, **répond**

| Étape | Mesure |
|---|---|
| Valeur au power-on | `0x0016` = **`01`** |
| On impose | `0x0016 ← 00` |
| Relecture | **`00`** |

⇒ ✅ **Les TROIS propriétés du patron §13.15.4 sont tenues** : registre **inscriptible**,
**relisible**, et **valeur de reset (`01`) ≠ valeur imposée (`00`)`**.
**L'entrée « ⏳ piste JAMAIS VÉRIFIÉE » du dossier est SOLDÉE.**

🔴 **MAIS LE MODULE LIVRÉ N'UTILISE PAS CE REGISTRE-LÀ, ET C'EST DÉLIBÉRÉ** : la valeur de
`0x0016` est un **FAIT sur l'historique de la puce** (*a-t-elle été réinitialisée depuis son
alimentation ?*). L'écraser en régime **détruirait l'information**, et la garde deviendrait de plus
en plus faible à chaque cycle (imposer `00` sur un registre déjà à `00` ne discrimine rien).
⇒ `dn_env` garde `0x003F` et `0x0041` — **même patron, valeurs de reset différentes, et ce sont
aussi la configuration utile**.
⚠️ **EFFET DE BORD DE CETTE SÉANCE, ÉCRIT POUR QUE PERSONNE NE S'Y TROMPE** : `0x0016` **vaut
maintenant `00` sur cette carte**, et il ne repassera à `01` qu'à une **coupure d'alimentation du
VL6180X** — ⛔ **pas** à un `--reset` ni à un `reboot` de l'ESP32. Un futur lecteur qui y verrait
« déjà initialisé » se tromperait.

#### c) 🎯 L'INA219 — le témoin FORT tient, et **un fait publié est RÉFUTÉ**

| Registre | Lu | Attendu au dossier | Verdict |
|---|---|---|---|
| `00h` Configuration | **`39 9F`** | `39 9F` | ✅ conforme |
| `05h` Calibration (reset) | **`00 00`** | `0000` | ✅ conforme |
| `05h` après `← D7 A4` | **`D7 A4`** | — | ✅ **témoin FORT ÉPROUVÉ** |
| `02h` Bus Voltage | **`07 0A`** ⇒ 225 × 4 mV = **900 mV**, CNVR=1, OVF=0 | — | 🆕 **jamais relevé** |
| `01h` Shunt Voltage | 🔴 **`FF FB`** = **−50 µV** | 🔴 *« rend `00 00` — shunt libre »* (`README.md:916`, §3 de la story) | 🔴 **RÉFUTÉ** |

> 🔴 **RÉFUTATION** : le shunt libre ne rend **PAS** `00 00`. Il rend **`FF FB`, soit −50 µV** — du
> **bruit**, ce qui est **physiquement attendu** d'une entrée différentielle flottante, et **plus
> honnête** qu'un zéro. ⛔ **Le fait publié n'est pas réécrit, il est daté et contredit ici.**
> ⚠️ **Conséquence pratique, et elle est vicieuse** : `00 00` avait été proposé comme *contrôle* du
> shunt libre. **Ce contrôle ne peut pas fonctionner** — il rendrait « anormal » l'état normal.

🔴 **ET CE QUE L'INA219 MESURE AUJOURD'HUI EST DÉSORMAIS NOMMÉ, comme AC7 l'exige** : `Vin+`/`Vin−`
n'étant pas câblés, **`02h` lit le potentiel d'une entrée FLOTTANTE** — 900 mV, une valeur stable et
**parfaitement plausible**, qui n'est **l'alimentation de rien**. ⛔ **Ce n'est pas une mesure de
consommation, et aucun chiffre de D5 ne peut en sortir.**
⚠️ 🔴 **ET CE N'EST PAS UNE GARDE, IL FAUT L'ÉCRIRE** : un INA219 fantôme rendrait lui aussi des
valeurs plausibles sur `01h`/`02h`. **Seul le `05h` discrimine.**

#### d) Le BH1750 — il vit, et sa garde **n'existe pas**

Séquence `0x01` (power on) puis `0x10` (continu, haute résolution), lecture nue 2 octets :
**brut `01 EE` = 494 ⇒ 411 lx**. ✅
⚠️ **Avant la séquence, il rendait `00 00`** — ⛔ ce qui ne prouvait **pas** un capteur mort : c'est
aussi l'état *power-down* et *conversion pas prête*. **Le discriminant est le stimulus, et il
demande un geste owner.**
🔴 **Garde anti-fantôme : AUCUNE, et c'est DÉCLARÉ.** Le BH1750 n'expose **aucun registre relisible**
— son unique registre écrivable est le `MTreg`, **non relisible**, et la piste a été **tentée et NON
REPRODUITE**. ⇒ `dn_env` **le dit à la console** au lieu de faire semblant. ⛔ Le stimulus reste sa
qualification la plus forte, mais **il ne peut pas être une garde de régime**.

#### e) 🆕 UN FAIT NEUF SUR LES « 103 `ESP_ERROR_CHECK` » — **21 d'entre eux ne sont PAS du code**

Audit rejoué le 2026-08-20 après `dn4-3`, `main/idf_component.yml` **vérifié intact**
(`git diff --stat` vide), **aucun composant ajouté** :

| Composant | Total (commande de la story) | **Dans du `.c`/`.h`** | Ailleurs |
|---|---:|---:|---|
| `espressif__esp_lvgl_port` | 55 | **52** | 3 (`README.md`) |
| 🔴 **`k0i05__esp_bme680`** | **26** | 🔴 **26** | **0** |
| `espressif__esp_lcd_st7701` | 14 | **3** | 11 (`README.md`) |
| `espressif__esp_io_expander` | 3 | **0** | 3 (`README.md`) |
| `esp_lcd_panel_io_additions` | 2 | **0** | 2 (`README.md`) |
| `esp_io_expander_tca9554` | 1 | **1** | 0 |
| `esp_lcd_touch_gt911` | 1 | **0** | 1 (`README.md`) |
| `lvgl__lvgl` | 1 | **0** | 1 (`docs/…/*.rst`) |
| **TOTAL** | **103** | **82** | **21** |

✅ **Le total 103 est reproduit LIGNE À LIGNE** ⇒ le compte est **inchangé**, aucun composant tiers
n'est entré (X5 : drivers maison).
🆕 🔴 **Mais le chiffre qui porte le RISQUE DE BRIQUAGE est 82, pas 103** : les 21 autres sont dans
des `README.md` et un `.rst` de documentation. ⇒ **la part du module OPTIONNEL passe de 26/103 =
25 % à 26/82 = 32 %**, et **`k0i05__esp_bme680` est le SEUL composant dont les 26 occurrences sont
TOUTES dans du code compilé.**
⚠️ **Et l'écart s'est révélé par accident** : un premier passage avec `--include=*.c --include=*.h`
a rendu **82** contre les 103 attendus. ⛔ **Ne jamais comparer deux comptes sans comparer leurs
INSTRUMENTS** — celui de la story n'a pas de filtre d'extension, et rien ne le disait.

#### f) 🎯 AC2 — le contrôle mécanique sur le code AJOUTÉ

| Motif | `dn_env.c` | `dn_env.h` | Les 4 fichiers modifiés (lignes `+` du diff) |
|---|---:|---:|---:|
| `ESP_ERROR_CHECK` | 2 | 1 | 1 |
| `abort(` · `assert(` · `ESP_GOTO_ON` | **0** | **0** | **0** |

🔴 **LES QUATRE OCCURRENCES SONT DES COMMENTAIRES, ET DEUX D'ENTRE ELLES ÉNONCENT L'INTERDICTION
ELLE-MÊME** — vérifié en imprimant **les lignes**, ⛔ pas en lisant un compte :
`dn_env.c:5` (*« RÈGLE ABSOLUE DE CE FICHIER : ⛔ AUCUN `ESP_ERROR_CHECK` »*) · `dn_env.h:40`
(*« le compte de 103 »*) · `CMakeLists.txt` (*« ce qui garde le compte de 103 à 103 »*).
⇒ ✅ **ZÉRO `ESP_ERROR_CHECK` EXÉCUTABLE dans le code ajouté.**
⚠️ *Un `grep -c` aurait publié « 4 » et fait échouer un AC qui passe.* C'est le même piège que le
`grep -c` qui comptait sa propre ligne.

✅ **D4 vérifié** : `grep -cE "nvs_|esp_partition_write|esp_flash_write"` sur `dn_env.c` = **0**.

#### g) Coût binaire — **mesuré une fois LIÉ**, ⛔ pas au manifeste

| | Binaire | Écart |
|---|---:|---|
| T0 `2992181` | **956 128 o** | — |
| avec `dn_env` + `env` + `bl auto` | **970 080 o** | 🔴 **+13 952 o** |

⚠️ **À mettre en regard du précédent** : le seul BME680 en **composant tiers** avait coûté
**+26 992 o** une fois lié. ⇒ **trois drivers maison, une commande console et un asservissement
coûtent la MOITIÉ d'un composant tiers pour un capteur.** ⛔ Ce n'est pas un argument général sur
« maison vs tiers » : c'est le chiffre de CE cas, et il va dans le sens de l'arbitrage de §13.19.4.
✅ Partition toujours **77 % libre**.

### 13.19.5bis 🎯 AC1 / AC2 / AC3 — LA QUALIFICATION PAR LE STIMULUS ET LES SIX DÉBRANCHEMENTS

🔴 **SECTION ÉCRITE EN REVUE DE CODE LE 2026-08-20, ET C'EST UN TROU QUI EST COMBLÉ, ⛔ PAS UNE
MESURE NEUVE.** Les chiffres ci-dessous ont été relevés pendant la séance carte de `dn4-3` et
publiés **uniquement dans la story** (`Dev Agent Record`, notes 14 et 15) et, pour la campagne, dans
`deferred-work.md:298`. **Ils ne se trouvaient dans AUCUNE section de ce document**, alors que §14
pose que *« le livrable de test est un TABLEAU DE MESURES »* — et que ce document EST le livrable de
séance. ⛔ **La preuve des deux AC les plus structurants ne peut pas vivre dans le seul artefact que
la story écrit sur elle-même.**
⚠️ **Et le renvoi du ledger était FAUX** : `deferred-work.md:298` citait **§13.19.12**, qui est
*« LES BUDGETS SUR LE FIRMWARE LIVRÉ »* — aucun débranchement, aucun 42,9 % n'y figure. Corrigé
**par ajout** vers cette section-ci.

#### a) 🎯 AC1 — LE STIMULUS BH1750, GESTE OWNER, DANS LES DEUX SENS

**Protocole** : trois lectures par état, à la console (`env`), l'owner posant puis retirant la main
sur le capteur. ⛔ **Jamais le scan** — démontré aveugle (8/8 vert pendant 55,5 % d'erreurs).

| État | Lecture 1 | Lecture 2 | Lecture 3 |
|---|---:|---:|---:|
| **Départ** (pièce éclairée) | **620 lx** | **635 lx** | **647 lx** |
| 🖐️ **Main posée** sur le capteur | **0 lx** | **0 lx** | **1 lx** |
| **Main retirée** | **850 lx** | **860 lx** | **871 lx** |

🎯 **LE RETOUR N'EST PAS IDENTIQUE AU DÉPART : +35 %** — et c'est le critère de l'AC, mot pour mot :
*« une valeur rejouée reviendrait exacte »*. Elle ne revient pas exacte, donc **la valeur suit la
pièce**, elle n'est pas régurgitée depuis un cache.
**48 cycles, 0 erreur de toute cause** sur la fenêtre.

✅ **ET LE TERRAIN A VALIDÉ UN CHOIX DE CONCEPTION** : `brut = 0` est arrivé **deux fois** sous la
main, et il est publié comme une **valeur LÉGITIME** (obscurité), ⛔ pas comme une erreur de bornes.
🔴 **Si je l'avais borné, la main de l'owner aurait fabriqué 2 erreurs sur 3.** C'est la raison pour
laquelle `0 lx` n'entre dans aucun seau — et pourquoi la console distingue désormais *« un lux
JAMAIS LU »* de *« 0 lx »* (corrigé en revue de code : elle imprimait `0` pour les deux).

#### b) 🎯 AC2 + AC3 — SIX DÉBRANCHEMENTS PHYSIQUES, BUDGET ANNONCÉ, **0 BRIQUAGE**

**Protocole** : débranchement **PHYSIQUE** du câble USB — le seul geste qui coupe réellement le rail
(⛔ `reboot` et `--reset` **ne reproduisent pas** le défaut). **Budget annoncé d'avance : 6 cycles.**
**Instrument : `touch` (`err_i2c`) dans les 60 s**, ⛔ **pas le scan**.

| Grandeur | Résultat |
|---|---|
| Briquages | 🎯 **0 sur 6** |
| Cycles **dégradés** | **2 sur 6** (contre **1/6** en `dn4-2`) |
| Pic d'erreurs GT911 | **260 erreurs / 606 lectures = 42,9 %** |
| Signature transitoire | 🎯 **REPRODUITE** : **+1 567 lectures, ZÉRO erreur nouvelle** entre le relevé précoce et T+60 s (`dn4-2` avait publié *+862 lectures, zéro erreur nouvelle*) |
| **BH1750** pendant les 42,9 % | 🔴 **pas UNE erreur** |
| **INA219** pendant les 42,9 % | 🔴 **pas UNE erreur** |
| **VL6180X** pendant les 42,9 % | **4 `err_i2c` + 5 pertes de configuration**, **TOUTES réparées seules**, ⛔ **aucune valeur fausse publiée** |

🎯 **LE DÉFAUT FRAPPE OÙ LA THÉORIE LE PRÉDISAIT.** Le VL6180X est **le seul des trois dont l'index
de registre est sur 16 bits**, donc **le seul à faire des transferts multi-octets** — précisément le
mode de défaillance que §13.17.1 désigne. ⛔ Ce n'est pas un hasard, et ça vaut mieux qu'un chiffre.

⚠️ 🔴 **CE QUE CE RELEVÉ NE CONTIENT PAS, ET L'AC LE DEMANDAIT NOMMÉMENT : LE DÉLAI DE REPRISE.**
AC3 exige *« et **le délai de reprise** »*. Il n'a **pas été chronométré** pendant la séance. On sait
que la reprise a eu lieu (les 5 pertes de configuration du VL6180X sont **toutes** réparées) et
qu'elle tient dans la fenêtre de 60 s, ⛔ **mais aucun chiffre ne peut être publié ici.**
⇒ **PORTÉ AU T0 DE `dn4-4`**, avec les quatre compteurs manquants d'AC13.
⛔ **Ne pas re-cocher AC3 de `dn4-3` sur ce relevé futur : il portera un AUTRE firmware.**

⚠️ **ET LES CHIFFRES CI-DESSUS PORTENT LE FIRMWARE `fd959f2`**, ⛔ **pas celui d'après la revue de
code.** Les correctifs de revue changent des chemins que cette campagne a exercés — notamment la
reconfiguration après une perte, qui n'écrit plus sur une simple erreur de transport. ⇒ **la
campagne est à REJOUER** sur le firmware corrigé, et c'est écrit ici pour que personne ne recopie
ces lignes comme si elles portaient le nouveau binaire.

---

### 13.19.6 🎯 X3 TRANCHÉ — **NON**, et l'ambiguïté a été levée **par la mesure**, ⛔ pas en reposant la question

**La question a été posée à l'owner le 2026-08-20**, en distinguant explicitement — comme AC7
l'exige, et parce que `dn4-2` s'y était trompé — *« l'INA219 sur le bus »* (les quatre capteurs en
parallèle, état actuel) de *« l'INA219 EN SÉRIE, `Vin+`/`Vin−` soudées sur le rail qui alimente le
module »*.

**Réponse owner, verbatim** : *« non les l'ina219 est deja connecté avec les bon branchement »*.

⚠️ **Cette réponse admet DEUX lectures**, et §13.6/AC7 interdisent de décider sur une réponse
ambiguë : *(a)* « non [pas de fer], il est déjà bien câblé **sur le bus** » · *(b)* « ta prémisse
est fausse, `Vin+`/`Vin−` **sont déjà** sur le rail ».
🔴 **⛔ On ne repose PAS la question : on la MESURE.** Le dépôt a un instrument pour ça, et il est
décisif.

**L'A/B, et il est bâti pour être discriminant** : `bl 0` ↔ `bl 100` fait varier le courant du
module de **plusieurs dizaines de mA** (le rétroéclairage d'une dalle 2,8"). À travers le shunt
`R100` de **0,1 Ω**, 50 mA valent **5 mV = 500 LSB** de `01h` (LSB 10 µV).
⇒ 🎯 **« Cet instrument PEUT-IL voir le défaut qu'il prétend exclure ? » — OUI, avec ~250× de
marge.** *(La question de §14.1, posée avant de publier le chiffre.)*

| Passe | `bl` | `01h` Shunt | en µV | `02h` Bus |
|---|---:|---|---:|---|
| 1 | **100 %** | `FF FF` | **−10** | `07 0A` ⇒ 900 mV |
| 1 | **0 %** | `FF FE` | **−20** | `07 0A` ⇒ 900 mV |
| 2 | **100 %** | `FF FD` | **−30** | `07 12` ⇒ 904 mV |
| 2 | **0 %** | `FF FF` | **−10** | `07 12` ⇒ 904 mV |

⚠️ **Ordre ALTERNÉ sur deux passes** (piège §14 n°14 : la première boucle paie son amorçage).

🔴 **VERDICT : `Vin+`/`Vin−` NE SONT PAS EN SÉRIE SUR L'ALIMENTATION.** L'amplitude observée est de
**1 à 3 LSB**, soit **10 à 30 µV = 0,1 à 0,3 mA**, et surtout **elle n'est PAS corrélée au
rétroéclairage** : 100 % rend `FF FF` puis `FF FD`, 0 % rend `FF FE` puis `FF FF`. **C'est du
bruit**, exactement ce qu'on attend d'une entrée différentielle flottante — et l'ordre de grandeur
attendu s'il était en série (**~500 LSB**) est absent d'un facteur **~200**.
La tension de bus, elle, reste à **900-904 mV** : ⛔ ni 3,3 V, ni 5 V.

✅ **⇒ LA RÉPONSE DE L'OWNER SE LIT (a), ET ELLE EST EXACTE** : l'INA219 **est** correctement câblé
— **sur le bus I²C** (`0x40`, 5/5, `00h` = `39 9F`). ⛔ **Ce n'est pas lui qui était ambigu, c'était
la question.** Aucune décision n'a été prise sur l'ambiguïté : elle a été **levée par un A/B**.

**Ce que la story doit donc écrire, et AC7 l'impose :**
- ⛔ **Aucun geste de fer dans `dn4-3`.** Le montage fini et photographié n'est pas rouvert.
- 🔴 **`dn4-5` DEVRA MESURER LA CONSOMMATION AUTREMENT**, et c'est écrit ici à sa place. L'epic le
  prévoyait déjà : *« Si `dn4-3` a posé l'INA219 en série, le chiffre est déjà là ; sinon il faut le
  mesurer autrement. »* ⇒ **le chiffre de D5 (alimentation permanente) n'existe toujours pas.**
- ⏳ **ET L'OCCASION DU LEDGER RESTE OUVERTE, non prise** : la portée du **« Battery Power Control
  Switch »** sur l'alimentation USB n'est **toujours pas documentée**. `dn4-2` avait l'occasion de
  la mesurer et ne l'a pas fait ; `dn4-3` non plus, **et c'est écrit**. Un INA219 en série y
  répondrait dans le même geste — **le jour où le fer ressortira**, pas avant.
- ✅ **L'INA219 est lu EN RÉGIME quand même** (AC1), et **ce qu'il mesure est NOMMÉ** : le potentiel
  d'une entrée flottante (**~900 mV**, stable et plausible) et le bruit de son shunt libre
  (**−10 à −50 µV**). ⛔ **Ce ne sont PAS des grandeurs d'alimentation**, et `env` le dit en toutes
  lettres pour que personne ne les lise comme telles.

### 13.19.7 🎯 AC5 — LE RÉTROÉCLAIRAGE AUTOMATIQUE, ET **DEUX BORNES DÉPLACÉES PAR L'ŒIL**

**Firmwares `60ba0a4` puis `d856bc9` puis `222c4f4`** — la loi est **commutable à chaud**, donc l'A/B
s'est joué **dans un seul firmware à la fois**, ⛔ jamais par comparaison de deux binaires.

#### a) 🔴 LA CONTRE-RÉACTION OPTIQUE EST EXCLUE — et le premier test ne valait rien

| Condition | `bl 100` | `bl 0` | Verdict |
|---|---|---|---|
| **Pièce éclairée (~2 500 lx)** | 2 488 · 2 529 lx | 2 521 · 2 534 lx | ⚠️ **NON CONCLUANT** |
| 🎯 **Pièce NOIRE (rideau fermé)** | **brut 0** · **brut 0** | **brut 0** · **brut 0** | ✅ **AUCUNE contre-réaction** |

🔴 **LE PREMIER TEST A ÉTÉ PUBLIÉ PUIS RETIRÉ PAR SON PROPRE AUTEUR.** À 2 500 lx d'ambiante,
l'écart `bl 100`↔`bl 0` (33 puis 5 lx) était **noyé dans une dérive ambiante de +46 lx sur la même
fenêtre**, et de signe incohérent. ⇒ il excluait une contre-réaction **FORTE**, ⛔ **pas une faible**
— alors qu'une contre-réaction ne serait dangereuse **QUE** près du plancher, en pièce sombre.
✅ **Rejoué dans la condition où la réponse compte** : le capteur ne rend **pas un seul count**
(1 count = 0,83 lx) alors que le rétroéclairage à 100 % serait la **seule** source de lumière.
✅ **Et la photo de montage le confirme géométriquement** : le breakout GY-302 est **dressé, face
tournée vers la pièce**, à l'opposé de la dalle.
⇒ 🎯 **Le « il ne pompe pas » d'AC5 n'est pas qu'une observation : il a une CAUSE mesurée.**

#### b) Le plancher — **3 % → 8 %**, par dichotomie, dans la condition où il s'applique

| Duty | Constat owner, **rideau fermé** (capteur à **2 lx**) |
|---|---|
| **3 %** | 🔴 *« casiement plus lisible super sombre »* |
| **10 %** | *« pas mal lisible (limite) »* rideau OUVERT · *« encore un peu trop lumineux »* rideau fermé |
| **6 %** | *« oui toujours lisible, un poil trop sombre »* |
| 🎯 **8 %** | ✅ ***« 8 % serait mieux »*** puis ***« oui 8 % c'est bien »*** |

🔴 **LE 3 % DE `dn1-3` N'EST PAS INVALIDÉ, ET IL FAUT LE DIRE PRÉCISÉMENT.** Son AC7 l'avait mesuré
comme *« le plancher LISIBLE »* — mais **sur le Living PCB et son label**, une image de fond
contrastée. Rejoué sur le **dashboard à six cases**, du texte fin, il ne tient plus.
⇒ **Un plancher de lisibilité est une propriété du COUPLE duty × contenu, ⛔ pas du duty seul.**
C'est une correction **par ajout** : les deux chiffres sont vrais, sur deux contenus différents.

⚠️ **ET LA CONDITION DE MESURE A DÛ ÊTRE CORRIGÉE EN COURS DE ROUTE** : la lisibilité avait d'abord
été jugée **rideau OUVERT** (~1 500 lx : l'ambiante délave la dalle, « limite » y est sévère) alors
que **le plancher ne s'applique QU'EN PIÈCE SOMBRE**. ⇒ la dichotomie a été **rejouée rideau fermé**.
*Un seuil se mesure dans la condition où il s'applique, pas dans celle où l'on se trouve.*

#### c) Le plafond — **400 → 1500 → 600 lx**, deux fois par l'œil

| Étape | Plafond | Ce qui l'a déplacé |
|---|---|---|
| Livré | **400 lx** | UNE mesure (411 lx) |
| Corrigé | **1500 lx** | la séance a relevé **2 lx** (rideau fermé) à **2 262 lx** (jour) dans la même pièce ⇒ à 400 lx, la loi **saturait à 100 % dès un éclairage artificiel modeste** |
| 🎯 **Retenu** | **600 lx** | à 1 500, une pièce à **170 lx** ne recevait que **17 %** ⇒ constat owner *« un peu plus lumineux »*. À 600, la même pièce reçoit **32 %** ⇒ ✅ ***« c'est ça »*** |

⚠️ 🔴 **UNE RÉPONSE OWNER A ÉTÉ RECONNUE AMBIGUË ET N'A PAS ÉTÉ TRANCHÉE AU JUGÉ** :
*« ok pas mal pour être un peu plus »* — **plus RAPIDE** (le pas) et **plus LUMINEUX** (le plafond)
se corrigent à **deux endroits opposés** de la loi. La question a été **reposée en distinguant les
deux**, exactement comme pour X3. ⇒ réponse : **plus lumineux**.

⚠️ **ET LE DIAGNOSTIC QUI A CONDUIT AU 1500 ÉTAIT LUI-MÊME FAUX AU DÉPART** : il s'appuyait sur un
*« rideaux fermés = 1 296 lx, la loi ne modulera jamais »*. Le rideau **n'était pas encore fermé** :
fermé, c'est **2 lx**. ⛔ **C'est l'owner qui l'a dit**, pas une déduction — et la conclusion (le
plafond était trop haut) restait juste **pour une autre raison**.

#### d) 🔴 LE PLANCHER N'ÉTAIT PAS RÉGLABLE À CHAUD, ET C'EST LA SÉANCE QUI L'A PROUVÉ NÉCESSAIRE

Les bornes en **lux** étaient ajustables (`bl auto bornes`), le plancher en **%** était **figé à la
compilation** — or **c'est précisément lui que l'œil a déplacé**. La règle *« l'arbitrage se tranche
sur la dalle »* n'avait donc été appliquée **qu'à moitié**. ⇒ `bl auto plancher <n>` ajouté.
*Un paramètre qu'on ne peut pas bouger en séance n'est pas arbitrable en séance.*

#### e) Les deux écrivains sur LEDC — la garde **fonctionne et elle parle**

```
W (521743) dn_env: retroeclairage auto DESARME par « bl <n> » — deux ecrivains sur
LEDC ne s'arbitrent pas tout seuls, et une commande ecrasee au cycle suivant
serait un instrument qui ment.
⚠️ l'asservissement automatique était ARMÉ : il vient d'être DÉSARMÉ par « bl <n> ».
   Sinon la valeur que vous venez de poser aurait été écrasée au prochain cycle
   (5 s), sans un mot. `bl auto on` pour le réarmer.
```

#### f) 🎯 LE CONSTAT OWNER, VERBATIM

| Question | Réponse owner |
|---|---|
| Le plancher à 8 % dans le noir te va ? | ✅ **« oui »** |
| La montée quand la lumière revient ? | **« ok pas mal »** (+ *« un peu plus lumineux »*, soldé en (c)) |
| 🔴 **À lumière STABLE, la luminosité bouge-t-elle toute seule ?** | ✅ **« Non, elle est stable »** |
| Le plafond à 600 lx ? | ✅ **« c'est ça »** |

⇒ ✅ **AC5 EST SOLDÉ. La loi était écrite avant, elle a été déplacée deux fois par l'œil, et
⛔ ÇA NE POMPE PAS** — avec une cause mesurée, pas seulement une observation.

### 13.19.8 🎯 AC9 — « LA PIÈCE OU LA CARTE ? » À QUATRE CAPTEURS : **+2,1 °C**, et le biais d'étalonnage est RÉFUTÉ

**Méthode `dn2-1` rejouée**, pression de vapeur (Magnus/Tetens, WMO), relevé simultané à `17:14:59`.
🎯 **DEUX références au lieu d'une** — et ça change la force du verdict : deux sondes qui encadrent
la pièce donnent le **bruit spatial**, donc la barre au-dessus de laquelle un écart signifie
quelque chose.

| Source | T | RH | `e` (pression de vapeur) |
|---|---:|---:|---:|
| **Station Lidl** (gauche) | 26,0 °C | 49 % | **16,431 hPa** |
| **Épurateur Xiaomi** (droite) | 26,0 °C | 51 % | **17,102 hPa** |
| **BME680** | **28,1 °C** | **44,5 %** | **16,880 hPa** |

**Le même air à 28,1 °C devrait lire entre 43,3 % et 45,1 %RH.**
🎯 **Le capteur lit 44,5 % — DANS l'encadrement**, à 0,6 pt du Xiaomi et 1,2 pt du Lidl.

🔴 **ET LE TÉMOIN NÉGATIF EST RÉFUTÉ PAR LE MÊME CALCUL** : un capteur affecté d'un **biais
d'hygrométrie**, mesurant le même air **sans s'échauffer**, aurait lu **~50 %**. Il lit 44,5 %, soit
**5,5 points en dessous** — ce que **seule** une hausse de température explique.
⇒ ✅ **AUTO-ÉCHAUFFEMENT : +2,1 °C**, contre **+1,9 °C** publié par `dn2-1` **à UN capteur**.
**Écart 0,2 °C** ⇒ **trois composants de plus ne l'ont pas déplacé de façon détectable.**

⚠️ **TROIS LIMITES DÉCLARÉES, ET LA TROISIÈME VA CONTRE MON PROPRE RÉSULTAT :**
1. Sondes **non étalonnées** ; l'écart entre les deux références (**2 pts de RH, 0 °C**) donne le
   bruit spatial. La justesse absolue n'est **pas** établie à mieux que ~±1 °C.
2. `dn2-1` mesurait pièce à **24,0 °C**, ici **26,0 °C**. Conditions différentes.
3. 🔴 **Le rétroéclairage était à 32 %** (asservi) au moment du relevé, alors que `dn2-1` mesurait
   très probablement à **100 %**. **C'est une variable non contrôlée qui va dans le sens de RÉDUIRE
   l'échauffement** ⇒ **le +2,1 °C est peut-être SOUS-ESTIMÉ.** *Une limite qui affaiblit son propre
   résultat est la seule qui vaille la peine d'être écrite.*

⚠️ ✅ **ET UNE INFÉRENCE DE L'AGENT A ÉTÉ CORRIGÉE PAR L'OWNER.** Sur la photo de montage
(`install_01.jpg`), j'avais lu *« la carte est posée sur la grille d'aération de la tour »* et j'en
avais tiré un **troisième terme** (« la pièce, la carte, ou le flux d'air du PC ? »). Réponse owner :
*« le capteur est éloigné de la soufflerie »*. ⛔ **Sa connaissance du montage remplace ma déduction
photographique.** ⚠️ *Une photo se lit, elle ne se déduit pas.*

⚠️ **ET LA PIÈCE A DÉRIVÉ PENDANT LA SÉANCE** : les deux références sont passées de **26 à 27 °C**
(*« rideau fermé ça bloque l'aération, la chaleur monte »*). Le relevé ci-dessus est **simultané**,
donc il tient — mais **tout A/B thermique ultérieur exige un témoin négatif**, ce que §13.9 avait
déjà payé pour apprendre.

### 13.19.9 🎯 X2 TRANCHÉ — **AUCUNE 3ᵉ grandeur**, et les QUATRE candidats sont mesurés

⚠️ **La story n'en listait que trois** (lux, ALS, pression). **L'owner en a proposé un quatrième en
séance** — *« pas hPa mais au moins un statut de qualité de l'air, je fume dans la pièce, ça devrait
être facile de tester »*. Il est instruit ici comme les autres.

#### a) L'instrument : `w2`, le critère W2 mesuré **dans le firmware**

Patron `FAN_RPM` de `dn4-6`, jugé sur la **valeur AFFICHÉE** : **étendue ≥ 5** · **taux de changement
du TEXTE ≥ 10 %** · **σ ≥ 1**. Seuils **écrits avant le tir**, et la commande imprime ses références.

🔴 **ÉCHANTILLONNÉ DANS LE FIRMWARE, ⛔ PAS DEPUIS WSL** : `tools/dn_console.py` **perd des lignes**
(mesuré, deux captures entièrement vides le 2026-08-20), et **un taux de changement calculé sur un
échantillonnage qui perd des points est faux d'un biais qu'on ne sait pas borner.**
🔴 **QUATRE PISTES, DONT UN TÉMOIN DE CONTRÔLE** : X2 est un **choix entre candidats** — les comparer
avec deux instruments différents ne prouverait rien. Et la **température**, grandeur **déjà affichée
dans une case livrée**, dit ce que *« bouger assez »* vaut **sur cette carte, dans cette pièce**.

#### b) Les résultats — **deux fenêtres**, et la seconde nuance la première

| Piste | Fenêtre A (n=210, 17,5 min) | Fenêtre B (n=195, 16 min) |
|---|---|---|
| **lux (entier)** | **992 / 77 % / 148,76** ✅ QUALIFIE | **2 228 / 95 % / 568,14** ✅ QUALIFIE |
| pression (hPa entier) | **1 / 1 % / 1,01** ⛔ | — |
| pression (hPa dixième) | **4 / 7 % / 3,47** ⛔ | — |
| **température [CONTRÔLE]** | **16 / 12 % / 5,04** ✅ | **9 / 7 % / 2,11** ⛔ |
| gaz MOX (kΩ) | — | **781 / 38 % / 54,78** ✅ *(mais voir §13.19.10)* |

🎯 **SUR LA FENÊTRE A, LE TÉMOIN DE CONTRÔLE REND LE VERDICT SOLIDE** : la **température** QUALIFIE
sur **exactement la même fenêtre** où la pression échoue à **1 hPa d'étendue et 1 % de taux**.
⇒ **la fenêtre n'est pas trop courte** : la pression échoue là où une vraie grandeur d'environnement
réussit. **Ce n'est pas un artefact de durée, c'est une propriété de la grandeur.**

⚠️ 🔴 **MAIS LA FENÊTRE B AFFAIBLIT CE VERDICT, ET IL FAUT LE DIRE** : sur B, **le témoin de contrôle
NE QUALIFIE PLUS** (taux **7 %** < 10 %). ⇒ **le témoin est PRÈS DU SEUIL**, donc l'argument
*« la fenêtre suffit »* est **moins solide** qu'il n'y paraissait sur A. ⛔ **Les deux fenêtres sont
conservées et l'écart est nommé.** Ce qui reste hors de doute : la pression fait **1 hPa** là où la
température en fait **1,6 °C** — un facteur qu'aucune marge de seuil ne rattrape.

⚠️ 🔴 **ET W2 A UNE LIMITE QUE CETTE SÉANCE A RENDUE VISIBLE** : le **gaz QUALIFIE** (781 / 38 % /
54,8) — **uniquement par son burn-in** (2 kΩ → 50 kΩ en 12 min, plus une excursion à 782 kΩ),
alors que le stimulus fumée n'a produit **rien**. ⇒ **W2 mesure « ça bouge », ⛔ PAS « ça bouge pour
une raison utile ». Une dérive qualifie aussi bien qu'un signal.** Le témoin de contrôle protège
contre une fenêtre trop courte, **pas** contre une grandeur qui dérive sans informer.

#### c) 🎯 LA DÉCISION OWNER

**Verbatim de l'arbitrage** : ✅ **« AUCUNE — la case reste à deux ».**

| Candidat | Sort | Motif **mesuré** |
|---|---|---|
| **Pression** | ⛔ éliminée | **1 hPa d'étendue en 17 min**, taux **1 %**. Et elle n'avait pourtant PAS le conflit de verdict — c'est la mesure qui la tue, pas la conception |
| **ALS VL6180X** | ⛔ éliminé | réponse **strictement binaire** sur 7 points (§13.19.5) |
| **Gaz / qualité d'air** | ⛔ éliminé | **aucune réponse à deux bouffées** dont une au contact ; `iaq_score` **inutilisable** (3 défauts lus au source) ; coûte **+0,5 °C / −1,4 pt de RH** sur les deux grandeurs de la même case (§13.19.10) |
| **Lux BH1750** | ⛔ **non retenu, et ce n'est PAS un échec de qualification** | il **QUALIFIE largement** (jusqu'à **2 228 / 95 % / 568**). ⚠️ **C'est justement l'argument contre** : **10 à 70× la référence `FAN_RPM`** (13 / 55,2 % / 2,02) — un chiffre qui change **95 % du temps** entre 0 et 2 438 serait **agitant** dans une case. **W2 est un seuil PLANCHER, ⛔ pas un optimum** |

🔴 **CE QUE LE REPLI COÛTE, ET IL FAUT L'ÉCRIRE (AC6 l'exige) :**
**Le différenciateur « PC éteint » n'est PAS réparé par la grille.** `AMBIANCE` reste la seule case
vivante quand la tour dort, avec ses deux grandeurs — **exactement comme avant `dn4-3`**.
✅ **Il est réparé AILLEURS, et c'est mesuré** : **le rétroéclairage suit la pièce** (§13.19.7).
**C'est une réponse locale, vivante PC éteint, et l'owner l'a vue.** ⛔ **Mais ce n'est pas une donnée
affichée**, et la story doit le dire au lieu de le maquiller.

✅ **CE QUE LE REPLI ÉPARGNE, ET CE N'EST PAS RIEN :**
- ⛔ **`dn_ui.c` n'est PAS touché** : ni `k_desc[DN_UI_CASE_AMB]`, ni le `.n = 2` en dur de
  `dn_ui_ambiance_maj()`, ni le verdict de validité. **Zéro risque sur la seule case vivante.**
- ✅ **`AMBIANCE` garde jauge ET ligne secondaire en réserve** : à 3 grandeurs, `y_bas = 168 > 163`
  les aurait fermées **définitivement**, ⛔ pas « pour l'instant ».
- ✅ **Les trois dettes latentes de `dn4-6` restent DÉSARMÉES** : aucune bascule d'échelle
  (`lx → klx`), aucune grandeur signée en `ENTIER`, aucun `widget grandeurs 5 3`.

⚠️ **CONTRAINTE LÉGUÉE À `dn4-4`, énoncée par l'owner en séance** : *« dans tous les cas les infos
iront dans le détail d'`AMBIANCE` »*. ⛔ **La page de détail est hors périmètre de `dn4-3`** — c'est
`dn4-4`, et elle hérite donc de **lux, pression et gaz déjà lus, bornés et instrumentés**.

### 13.19.10 ⛔ LE GAZ — le stimulus fumée ne produit RIEN, et l'`iaq_score` du composant est INUTILISABLE

**A/B DÉCLARÉ** (`capteurs gaz on`), à la demande de l'owner. Rétroéclairage maintenu à **100 % fixe**
pendant tout le test pour que la thermique ne bouge pas.

| Phase | Gaz | T | RH | MOX |
|---|---|---:|---:|---:|
| **A** — ligne de base | coupé | **28,6 °C** *(×3 identiques)* | **44,9 %** | — |
| **B** — chauffeur actif | **ACTIF** | **29,1 → 29,5 °C** | **43,5 → 41,9 %** | 2 358 → **56 234 Ω** |
| **C** — témoin négatif | coupé | **29,5 → 28,8 °C** | 41,9 → **43,3 %** | — |

✅ **Le coût du chauffeur se reproduit, et dans le bon sens** : **B−A brut = +0,5 °C / −1,4 pt de RH**,
les deux grandeurs bougeant **en sens OPPOSÉS** comme §13.9 l'avait prédit puis mesuré.
🔴 **⛔ MAIS CE CHIFFRE EST NON CORRIGÉ DE LA DÉRIVE, ET IL NE PEUT PAS L'ÊTRE** : entre A et C,
**la pièce a pris +1 °C** (références owner 26 → 27 °C) **et** le rétroéclairage est passé de **32 %
à 100 %** (le flash désarme l'auto). **Trop de variables ont bougé.** ⇒ la phase C montre une
**réversibilité** (T redescend, RH remonte) mais **ne chiffre rien**.
✅ **La valeur de référence reste le +0,3 °C / −2 pts de `dn2-1`**, corrigé de sa dérive. ⛔ **Les
deux sont conservés et l'écart est nommé.**

#### 🔴 LE STIMULUS FUMÉE — **DEUX tentatives, budget annoncé, ZÉRO réponse**

| Tentative | Avant | Pendant | Verdict |
|---|---:|---|---|
| 1 — bouffée ambiante | 49 388 Ω (+20 Ω/s) | **51 100 Ω × 10 lectures**, puis 51 278 | ⛔ aucune chute |
| 2 — **bouffée dirigée, au contact** | 51 278 Ω | **56 234 Ω × 10 lectures** | ⛔ aucune chute |

Une résistance MOX **BAISSE** en présence de COV. Elle a **monté** dans les deux cas.

**Quatre causes possibles, ⛔ AUCUNE tranchée :**
1. La fumée n'atteint pas le capteur *(éliminée en partie : tentative 2 était au contact)*
2. Le **burn-in** monte encore et masque une chute modeste
3. 🔴 **LE RAPPORT CYCLIQUE** : le chauffeur ne tourne que **300 ms toutes les 5 000 ms = 6 %**. La
   surface du MOX n'a peut-être pas le temps de s'équilibrer avec l'air. **C'est la MÊME cadence qui
   atténue déjà l'auto-échauffement d'un facteur 10** (§13.9), et Bosch spécifie le gaz avec un
   **profil de chauffe dédié**. ⇒ **hypothèse la plus forte, et elle est TESTABLE** : une cadence
   gaz dédiée. ⛔ **C'est du code, hors périmètre de `dn4-3`.**
4. Bouffée trop diffuse

⚠️ **UNE FAUSSE ALERTE DE L'AGENT, LEVÉE PAR LA MESURE** : dix valeurs **rigoureusement identiques**
(`56234 Ω`, `29,5 °C`, `41,9 %`) ont fait soupçonner **une tâche `dn_capt` morte**. ⛔ Discriminé au
lieu d'être supposé : `age` **4 939 → 3 079 → 1 233 ms**, `lectures` **195 → 197 → 199**, cadence
**5 001 / 5 001 / 5 000 ms**. ✅ **La tâche allait parfaitement** — et c'est une **non-régression
forte gagnée par accident**, relevée **chauffeur gaz ACTIF et `dn_env` en régime**.

#### 🔴 L'`iaq_score` DU COMPOSANT EST INUTILISABLE — trois défauts LUS AU SOURCE

C'est une **invention maison** (« IAQ Rating Index » de Dr. Julie Riggs, iaquk.org.uk), ⛔ **pas du
BSEC** de Bosch :

| # | Fait | Ligne |
|---|---|---|
| 1 | Le header annonce **`0..500`** ; la formule somme 6,5 + 6,5 + 52 ⇒ **max réel 65** | `bme680.h:369` vs `bme680.c:737` |
| 2 | 🔴 `else if (gas >= 13500 && gas > 9000)` — **le second test est IMPLIQUÉ par le premier**. L'intention était `>= 9000 && < 13500`. ⇒ **la bande 9 000..13 500 Ω traverse toute la cascade SANS QU'AUCUN SCORE SOIT ASSIGNÉ**, et `gas_score` garde une **valeur résiduelle** | `bme680.c:733` |
| 3 | 🔴 Le score de température tombe à **0 au-dessus de 26 °C**. Or ce capteur lit **~28-29 °C à cause de son PROPRE auto-échauffement** (+2,1 °C mesuré) ⇒ **6,5 points perdus EN PERMANENCE par un artefact de MONTAGE**, pas par la qualité de l'air | `bme680.c:725` |

⇒ ✅ **Ce que `dn4-3` livre : la RÉSISTANCE BRUTE en ohms**, avec l'`iaq_score` imprimé **à côté de
ses trois défauts**, pour qu'il ne puisse pas être pris au sérieux par erreur.
⛔ **ABSENT et non `0` quand le chauffeur est coupé** : zéro ohm serait une valeur **physique** (un
court-circuit), donc **un mensonge plausible** — ce dépôt a déjà payé pour une sentinelle dans la
plage utile (`-1` qui valait −0,1 °C).

### 13.19.11 🔴 AC12 — **LA PRÉDICTION, ÉCRITE ET COMMITTÉE AVANT LA MESURE**

> *« Une prédiction démentie est plus instructive qu'une prédiction tenue. »*
> ⛔ **Rien de ce qui suit n'a été mesuré au moment où ces lignes sont committées**, à l'exception
> de la taille du binaire, qui sort du build et est donc **déjà connue** — elle est donnée ici comme
> **entrée du raisonnement**, ⛔ pas comme prédiction.

**Firmware à mesurer : le HEAD de cette séance** (X2 ayant tranché « aucune case », `dn_ui.c` n'est
pas touché ⇒ **c'est le firmware livré**).

**Ce que `dn4-3` ajoute réellement au régime**, et c'est la base du raisonnement :

| Capteur | Transactions I²C par cycle de 5 s |
|---|---|
| BH1750 | **1** (lecture nue 2 o) |
| INA219 | **5** (conformité `05h` + bus + shunt + courant + puissance) |
| VL6180X | **3** (conformité gain + conformité intégration + identité) |
| **`dn_env` TOTAL** | **9** |
| *rappel — BME680 seul* | *7* |

⇒ **le nombre de transactions par cycle passe de 7 à 16 (× 2,3)**, mais leur **poids** est très
différent : `dn_env_cycle()` a été **mesuré à ~2 300 µs**, contre **~26 000 µs** pour le cycle
BME680 — dont la majeure partie est de l'**attente** dans la boucle « data ready » du composant.

| Grandeur | T0 (`2992181`) | 🔮 **PRÉDICTION** | Raisonnement |
|---|---:|---:|---|
| Binaire | 956 128 o | **977 760 o** *(déjà connu du build)* | **+21 632 o** — trois drivers maison, `env`, `w2`, `bl auto`, la pression, le gaz. ⚠️ à comparer aux **+26 992 o** du seul BME680 en composant TIERS |
| RAM interne libre | 92 307 o | **91 300 – 91 800 o** | 3 `i2c_master_bus_add_device` (~150-250 o chacun) + les statiques du module ⇒ **−500 à −1 000 o** |
| PSRAM libre | 7 768 236 o | **7 768 236 o — INCHANGÉ** | ⛔ aucune allocation PSRAM ajoutée |
| Tas LVGL utilisé | 20 500 o (34 %) | **20 500 o — INCHANGÉ** | ⛔ `dn_env` ne crée **aucun objet LVGL** (X2 : pas de 3ᵉ grandeur) |
| Plus gros bloc / frag | 40 752 o / 2 % | **inchangés** | même raison |
| `fps 15` | 37,40 Hz (+0,00 %) | **37,40 Hz, +0,00 %** | le pipeline d'affichage n'est pas touché |
| Boot | 2 332 ms | **2 340 – 2 365 ms** | `dn_env_init()` ouvre 3 devices et écrit ~10 registres ⇒ **+10 à +30 ms** |
| `nav ab 40` (n=80) | 334,6 ms | **334 ± 20 ms** *(= inchangé)* | ⚠️ le bruit est de **±16 ms** : tout verdict sous ~±20 ms **est du bruit** |
| `flush` régime (esp. 4 ms) | 2,7 fl/cyc · 97 800 px/cyc | **inchangé à ±0,3 fl/cyc** | ⛔ `dn_env` ne pousse **rien** vers l'UI |
| 🔴 **`dn_capt` CPU** | 🔴 **0,068 %** | 🔴 **0,08 – 0,12 %** | 0,068 % sur 5 000 ms ≈ **3,4 ms de CPU par cycle**. `dn_env` ajoute **2,3 ms de temps MURAL**, dont une part est de l'attente I²C ⇒ **la part CPU est inférieure à 2,3 ms**. Fourchette large **assumée** : c'est le chiffre le moins bien contraint de la table |
| **cœur 0** | 3,249 % | **3,26 – 3,31 %** | `dn_capt` est le seul poste qui bouge |
| **cœur 1** | 0,015 % | **inchangé** | rien n'est ajouté sur le cœur 1 |

🔮 **PRÉDICTION SUR LA FAMINE DMA — la plus engageante, et la plus facile à démentir :**
**NON REPRODUITE.** Motif chiffré : `dn_env` ajoute **9 transactions toutes les 5 s = 1,8/s**, contre
un GT911 qui pole **~30×/s** ⇒ **+6 % de trafic I²C**. C'est **très en dessous** de ce que
`i2c rafale` produit (des centaines de sondages/s) sans rien casser.
🔴 **MAIS LA CONDITION QUI ROUVRE L'ENTRÉE EST RÉELLE ET ELLE EST NOMMÉE** : `dn4-2` **SONDAIT**,
`dn4-3` **LIT EN RÉGIME**, en permanence, pour toujours. ⚠️ **`fps` est AVEUGLE à ce défaut**
(37,45 Hz relevés *pendant que l'image défilait*) ⇒ **seul l'œil de l'owner tranche.**

🔮 **PRÉDICTION SUR AC13** : les **sept** compteurs de `dn_capt_compteurs_t` restent à **0** sauf
`lectures`, `touch`/`err_i2c` reste à **0 → 0** en couple encadrant, `config LUE (conforme)`, cadence
**~5,00 s**, et les **trois compteurs de débordement de case à zéro**.
⚠️ **Deux réserves honnêtes** : (a) un **démarrage à froid** peut faire monter `err_i2c` et
`conformite` — c'est **attendu**, mesuré, et **ce n'est pas une régression** (§13.19.12) ; (b) le
relevé se fait **après un `--reset`**, donc sur un **bus chaud**.

### 13.19.12 🎯 AC12 / AC13 — LES BUDGETS SUR LE FIRMWARE LIVRÉ, **CONFRONTÉS À LA PRÉDICTION**

**Firmware `fd959f2`, SHA LU AU BANDEAU**, `porcelain` vérifié **VIDE avant le flash**, build refait
après les commits. **La prédiction (§13.19.11) était committée avant le premier chiffre.**

| Grandeur | T0 `2992181` | 🔮 prédit | **MESURÉ** | Verdict |
|---|---:|---:|---:|---|
| Binaire | 956 128 o | *(connu du build)* | **977 760 o** | **+21 632 o** — la **moitié** des +26 992 o du seul BME680 en composant tiers. Partition **77 % libre** |
| RAM interne libre | 92 307 o | 91 300–91 800 | **91 631 o** | ✅ **TENUE** (−676 o) |
| **PSRAM libre** | 7 768 236 o | **inchangée** | **7 768 008 o** | 🔴 **DÉMENTIE — −228 o** |
| Tas LVGL utilisé | 20 500 o | inchangé | **20 472 o** | ✅ tenue (−28 o = le bruit d'allocation déjà vu au T0) |
| Plus gros bloc | 40 752 o | inchangé | **40 752 o** | ✅ **TENUE, à l'octet** |
| Fragmentation | 2 % | inchangée | **3 %** | ⚠️ +1 pt |
| `fps 15` | 37,40 Hz | 37,40 Hz | **37,40 Hz (+0,00 %)** | ✅ **TENUE** |
| **Boot** | 2 332 ms | **2 340–2 365** | **2 330 ms** | 🔴 **DÉMENTIE** |
| `nav ab 40` (n=80) | 334,6 ms | 334 ± 20 | **334,5 ms** | ✅ **TENUE** (écart **0,1 ms**) |
| flush/cycle (jeu figé, esp. 4 ms) | 2,7 | ±0,3 | **2,4** puis **2,6** | ✅ tenue, à la limite |
| plus grande aire | 36 675 px | — | **36 675 px** | ✅ **identique** |
| 🔴 **`dn_capt` CPU** | 🔴 **0,068 %** | 🔴 **0,08–0,12 %** | 🔴 **0,095 %** | ✅ 🎯 **TENUE** (**+40 %**) |
| cœur 0 | 3,249 % | 3,26–3,31 % | **3,157 %** | 🔴 **DÉMENTIE, ET À L'ENVERS** |
| cœur 1 | 0,015 % | inchangé | **0,029 %** | bruit |
| **Famine DMA** | — | **NON reproduite** | **NON reproduite** | ✅ 🎯 **TENUE** |

✅ **TEST DE RÉCONCILIATION PASSÉ** : somme des deltas **60 275 627** contre `fenêtre × 2` =
**60 276 976** sur une fenêtre **mesurée à 30,138 s** ⇒ écart **−0,0045 pt** (seuil ±0,01).

**BILAN : 7 prédictions tenues, 3 démenties** — et **les trois démenties sont les plus
instructives.**

#### 🔴 Démentie n°1 — le boot : **l'instrument s'arrête avant ce qu'on mesure**

Prédit **+10 à +30 ms** parce que `dn_env_init()` ouvre 3 devices et écrit ~10 registres.
Mesuré **2 330 ms**, soit **−2 ms**. La cause est **dans le log, en clair** :
`prêt en 2330 ms depuis app_main` est imprimé à **`I (3006)`**, alors que `dn_env pret` arrive à
**`I (3186)`**. ⇒ 🎯 **le chronomètre de boot s'arrête AVANT l'init des modules optionnels.**
**AUCUN module optionnel ne peut faire bouger ce chiffre**, et j'ai prédit un delta sans vérifier où
l'instrument s'arrête. ⚠️ *Corollaire pour les prochaines stories : « boot » ne mesure pas le boot,
il mesure le boot du SOCLE.*

#### 🔴 Démentie n°2 — le cœur 0 : **le bruit est 4× le signal**

Prédit **3,26–3,31 %**. Mesuré **3,157 %** — **MOINS** qu'au T0 (3,249 %), alors que du travail a
été **ajouté**. Cause : `taskLVGL` est passé de **2,270 % à 2,169 %** (**−0,10 pt**) d'une fenêtre à
l'autre, ce qui **noie** le +0,027 pt de `dn_capt`.
⇒ 🔴 **Le total du cœur 0 n'est PAS un instrument capable de voir cet ajout.** Seul **`dn_capt`
isolé** le voit — et lui, il le voit très bien : **0,068 → 0,095 %, soit +40 %.**
⚠️ *Un total qui contient un poste bruyant ne peut pas mesurer un poste discret.*

#### 🔴 Démentie n°3 — la PSRAM : **228 o là où j'avais écrit « aucune allocation »**

J'avais écrit *« ⛔ aucune allocation PSRAM ajoutée »*. Il y en a **228 o = exactement 76 o × 3
devices I²C**. ⇒ **l'allocateur a placé les handles de device en PSRAM**, ce que je n'avais pas
envisagé. ⚠️ **Cause plausible et arithmétiquement exacte, ⛔ NON VÉRIFIÉE** — je ne l'ai pas
instrumentée, et je ne la présente donc pas comme établie.

#### ✅ AC13 — les gardes des marches du dessous, PAR LA MESURE

| Garde | Relevé sur `fd959f2` |
|---|---|
| `touch` couple encadrant | **0 → 0 erreur I²C** sur **12 196 lectures**, 6 appuis / 6 relâches *(les allers-retours de l'owner)* |
| BME680 | `config LUE : 0x72=04 · 0x74=84 · 0x75=08 (conforme)` · cadence **5 004 ms** · `i2c 0 · donnee 0 · bornes 0` |
| `dn_env` | **193 cycles**, dernier cycle **2 661 µs** · les **trois VIVANT** · `i2c 0 · donnee 0 · bornes 0 · conformite 0` |
| Bandeau de boot | **UNE seule ligne W/E nouvelle** par rapport au T0, et c'est **la nôtre, délibérée** (l'unité de la pression). Les 9 autres sont **identiques** — vérifié par `diff` |
| `descripteurs_auditer()` | **6 cases auditées, 0 trou** |
| `fps 15` | **37,40 Hz** |
| Géométrie de case | **Chevauchements détectés : 0** |
| **D4** | ✅ `grep -cE "nvs_set\|nvs_commit\|esp_partition_write\|esp_flash_write"` sur `dn_env.c`/`.h` = **0** |
| Config d'affichage | `num_fbs=1` · `bounce=7680` · `draw 480×128` · `vsync` · **inchangée** |

⏳ **UNE LIMITE DÉCLARÉE SUR AC13** : `widget largeur` n'imprime **qu'un** des trois compteurs de
géométrie (les chevauchements, à **0**). Les deux autres — *trop larges* et *débordements en
hauteur* — **journalisent par `ESP_LOGW`**, et **aucune telle ligne n'est apparue** dans les captures
de cette séance. ⛔ **C'est plus faible qu'une lecture directe, et je le dis** plutôt que d'écrire
« les trois sont à zéro ».

🎯 **LE SMOKE OWNER, VERBATIM**

⚠️ **Rappel obligatoire** : pendant toute cette séance, **les 5 cases PC sont NÉCESSAIREMENT mortes**
(exclusivité WSL ↔ COM3) — sauf sous injecteur ou sous `widget mock on`. ⛔ **Ce n'est pas un défaut.**

| Question | Réponse owner |
|---|---|
| Sous régime réel (jeu figé), l'image saute-t-elle ? | ✅ **« image ok »** |
| Les six cases sont-elles remplies ? | ✅ **« 6 case rempli »** ⚠️ *« mais n'avais pas l'air de bouger beaucoup »* |
| L'heure ? | **« pas d'h »** ⇒ ✅ **comportement CORRECT** |
| 🔴 Sous **dashboard vivant** (+36 % de pixels), quoi que ce soit d'anormal ? | ✅ **« rien d'anormal »** |
| Ça bouge, cette fois ? | ✅ **« oui les 4 : gpu ram reseau et disque + temp »** |
| Le toucher ouvre le détail, le retour revient ? | ✅ **« aller retours details ok »** |

🎯 **DEUX OBSERVATIONS DE L'OWNER ONT CORRIGÉ L'AGENT, ET LA PREMIÈRE EST UNE TROUVAILLE SUR
L'INSTRUMENT :**

1. 🔴 ***« n'avait pas l'air de bouger beaucoup »*** — **il a raison, et c'est MON stimulus qui est
   en cause.** Le jeu `reel` de `dn_injecteur.py` est un **dictionnaire de valeurs CONSTANTES** : il
   envoie **45 fois les mêmes nombres**. Les cases se **remplissent** mais **ne changent jamais**.
   ⇒ ⛔ **Un constat de VIVACITÉ ne peut PAS être obtenu avec ce jeu**, et ⚠️ **ça affaiblissait mon
   verdict sur la famine DMA** : un dashboard figé salit moins de pixels qu'un dashboard vivant.
   ✅ **Rejoué avec `widget mock on`** (4 mocks en rampe + `AMBIANCE` réelle) : **128 613 px/cycle et
   3,5 flush/cycle**, contre 94 645 / 2,6 ⇒ **+36 % de pixels, +35 % de flushes**. **Et l'owner
   confirme : « rien d'anormal ».** ⇒ **le verdict « famine non reproduite » est PLUS FORT qu'il ne
   l'aurait été sans son observation.**
2. ✅ ***« pas d'h »*** — **comportement correct et vérifié** : `rtc` rend **`bit OS = 1`**,
   l'oscillateur du PCF85063A s'est arrêté, l'heure lue (`2000-01-01 01:48`) **ne vaut rien**, et la
   barre affiche **« --:-- HEURE NON POSÉE »** au lieu de mentir. AC13 exige *« juste OU dit
   honnêtement qu'elle ne l'est pas »* — **elle le dit.** `rtc set` la pose.

### 13.19.14 🔴 LA REVUE DE CODE DU 2026-08-20 — 34 CONSTATS, ET LE PIRE POUVAIT PERDRE LA CONSOLE

**Trois couches adversariales** (chasse à l'aveugle · parcours exhaustif des bornes · audit
d'acceptance) sur `2992181..4724944`, `firmware/` seul. **Chaque constat a été re-vérifié au code
avant d'être retenu**, et **trois ont été RÉFUTÉS par cette vérification** — ils sont écrits ici
avec leur réfutation, parce qu'un constat de revue qui tombe est aussi instructif qu'un qui tient.

#### a) 🔴 LES CINQ QUI CHANGENT LE COMPORTEMENT DU FIRMWARE

| # | Le défaut | Ce qui l'a prouvé |
|---|---|---|
| **1** | 🔴 **`w2` : la racine de Newton entière NE TERMINE PAS.** `while (r != prev)` entre dans un cycle de période 2 pour toute variance de la forme `k²−1` | **Force brute : 446 valeurs piègent la boucle dans 1..199 999.** Cas atteignable : lux `{0,0,0,3,3}` (rideau fermé — l'owner a mesuré **2 lx** dans cette condition) donne `var = 1 560 000 = 1249²−1`, et `r` oscille **1248↔1249 pour toujours** ⇒ REPL à 100 %, console perdue, TWDT, et avec `PANIC_PRINT_HALT` c'est *« RESET physique obligatoire »*. **Introduit par `d856bc9`, ⛔ pas hérité** |
| **2** | 🔴 **Un BH1750 dont la config échoue au boot n'est JAMAIS reconfiguré, et publie `0 lx` VIVANT à vie** | Trois maillons : `conformite_ok(LUM)` rendait **`true` en dur** ⇒ branche de réparation inatteignable · `dev` **jamais remis à `NULL`** ⇒ branche de ré-ouverture inatteignable · `config_us` **restait à 0** ⇒ la garde des 180 ms ne pouvait plus tirer. Et le log de boot **promettait le contraire** : *« la garde de conformite la reposera »* |
| **3** | 🔴 **Une erreur de TRANSPORT était comptée et journalisée comme « CONFIGURATION PERDUE », et déclenchait des ÉCRITURES en régime** | Un seul NACK produisait `err_i2c++` **ET** `conformite++`, une **cause affirmée sans preuve** (l'ESD), et **2 à 4 écritures** sur le bus en train de se dégrader. ⚠️ **La campagne le confirme** : *« 4 `err_i2c` + 5 pertes de configuration »* sur le VL6180X à froid ⇒ **jusqu'à 5 séquences d'écriture réellement jouées**. ⛔ Contredisait trois textes écrits par cette même story |
| **4** | 🔴 **Le σ de `w2` avait un biais de troncature du même ordre que son propre seuil** | `e_x2` tronqué **avant** le × 10⁶ ⇒ jusqu'à **10⁶ de variance jetée**, quand le seuil vaut `var = 10⁶` tout rond. Mesuré : σ 1,633 → **1,414** (−13 %) · 0,748 → **0,600** (−20 %) · 0,748 → **0,000** (−100 %). **Biais toujours vers « NE QUALIFIE PAS »** |
| **5** | **Courant, puissance et gaz publiés SANS borne ni source** | AC10 les exigeait nommément. `04h`/`03h` sont des lectures **indépendantes** de celle du bus : un `CALIB` corrompu publiait `131 070 mW` sur un shunt **non câblé**, sans qu'aucun seau ne bouge |

✅ **APRÈS CORRECTIF, VÉRIFIÉ NUMÉRIQUEMENT** : la racine est **exacte** (écart **0** contre `isqrt`
sur 3 000 tirages jusqu'à 10¹²), **zéro** valeur ne boucle sur 300 000 testées, et l'erreur de σ
tombe de −13/−20/−100 % à **~−0,05 %**.

#### b) Les autres, par famille

- **Deux seaux structurellement inatteignables** (`err_donnee` du BH1750, `err_bornes` du VL6180X) —
  **et non déclarés**, alors que le patron de déclaration existait déjà pour `conformite`.
- **Trois lectures non atomiques** : `env` prenait 2 (lux) et 4 (INA219) sections critiques là où le
  cycle publie sous **une seule** ⇒ `« 411 lx (brut 500) »`. C'est le défaut **« CR `dn4-2` —
  LECTURE ATOMIQUE »**, réintroduit pour le module neuf.
- **Le W2 du lux ré-échantillonnait une valeur PÉRIMÉE** (la garde disait *« pas encore périmé »*,
  ⛔ pas *« lu ce cycle-ci »*) — les quatre autres pistes non ⇒ **deux instruments différents pour
  comparer des candidats**, ce que `dn_env.h` interdit explicitement.
- **`gas_valid`/`heater_stable` ignorés** : `s_gaz` est notre **demande**, pas un état de mesure ⇒
  le premier cycle après `capteurs gaz on` publiait **~12,9 MΩ** et le poussait dans W2, où il
  fixait le min/max de toute la fenêtre.
- **Un verrou mortel dans les réglages à chaud** : `bl auto pas 1` + `bl auto plancher 97` figeait le
  duty à **99 %**, dans les deux sens, pour tous les lux — pendant que `bl auto` annonçait une
  « course complète ».
- **Trois « deux diagnostics dans une phrase »** : `env` accusait `dn_capt` quand la cause pouvait
  être `dn_env_init()` · `gaz : chauffeur COUPE` s'affirmait aussi quand rien n'avait jamais été lu ·
  `bl` imprimait *« sur 0 lx »* pour un lux **jamais lu**, alors que `0 lx` est une **valeur mesurée
  légitime** sur ce capteur. ⛔ C'est la faute que *« TROIS ETATS, TROIS PHRASES »* venait d'éliminer.
- **Le signe posé par une division entière** (pression brute) — le correctif existait **vingt lignes
  plus haut**, et `dn_capteurs` l'avait **déjà payé** sur l'humidité (`« -5,-5 % »`).
- **Arguments surnuméraires acceptés en silence** sur `bl auto …`, `env reset`, `w2 reset`.
- **Bornage de blocage documenté faux** : *« 3 × 100 ms par capteur »* annoncé, **6 ×** réel pour le
  VL6180X sur conformité perdue, **~12 ×** par cycle. ⚠️ Ce pire cas **n'a jamais été exercé** :
  la famine DMA d'AC12 a été rejouée sur un bus **sain**.
- **Un contrat d'ordre d'init faux dans le header** (*« APRÈS `dn_console_start()` »*) — 🎯 **décision
  owner : le CODE fait autorité**, c'est le contrat écrit qui se corrige.

#### c) ⚠️ LES TROIS CONSTATS QUE LA VÉRIFICATION A RÉFUTÉS

1. ⛔ **« Division par zéro dans `dn_env_bl_loi()` »** — **INATTEIGNABLE** : si `span ≤ 0`, alors
   soit `lux <= bas` soit `lux >= haut`, et **les deux retours anticipés attrapent le cas avant la
   division**.
2. ⛔ **« La course `bl <n>` ↔ loi auto ouvre une fenêtre de ~600 ms d'I²C »** — **FAUX d'un facteur
   ~10⁵** : le bloc de rétroéclairage s'exécute **APRÈS** les lectures, la fenêtre fait quelques
   **µs**. La course existe, elle ne pèse pas ça.
3. ⛔ **« Le verdict de X2 repose sur des instruments biaisés »** — **les deux biais trouvés vont
   DANS LE SENS du verdict rendu**, et **aucun candidat n'a été tranché sur σ** : la pression tombe
   sur l'étendue (1 hPa) et le taux (1 %), le lux qualifie à 77-95 % de taux. ⇒ **X2 tient.**

#### c bis) 🔴 UN DÉFAUT INTRODUIT **PAR LE CORRECTIF LUI-MÊME**, TROUVÉ AVANT LE FLASH

⚠️ **Écrit ici parce que c'est exactement ce que §13.19.13 impose : conserver ce qui n'a pas marché,
y compris mes propres erreurs de méthode.**

Le premier jet du correctif du σ écrivait `(somme_carres * 1000000) / n` — **le produit d'abord**.
Sur la piste **lux** (54 611 lx max, carré **2,98 × 10⁹**), `int64` déborde à **~3 092 échantillons**,
soit **4,3 h** à 5 s par échantillon. 🔴 **Et `dn4-5` est un soak d'UNE SEMAINE** ⇒ le débordement
était **certain**, pas théorique.

| Piste | Valeur max | Carré | `n` avant débordement | Durée à 5 s |
|---|---:|---:|---:|---:|
| **lux (BH1750)** | 54 611 | 2 982 361 321 | **3 092** | 🔴 **4,3 h** |
| pression (dixièmes) | 11 000 | 121 000 000 | 76 226 | 105,9 h |
| gaz (kΩ) | 500 | 250 000 | 36 893 488 | 51 241 h |
| température (dixièmes) | 850 | 722 500 | 12 765 912 | 17 730 h |

✅ **Corrigé par un découpage QUOTIENT + RESTE**, qui garde la précision sans jamais former le grand
produit : `E[x²]×10⁶ = (S2/n)×10⁶ + ((S2 mod n)×10⁶)/n`.
**Marges vérifiées** : `(S2/n)×10⁶ ≤ 2,98e15` · `(S2 mod n)×10⁶ < n×10⁶ ≤ 4,3e15` (`n` est un
`uint32`) · `moy_x1000² ≤ 2,98e15`. ⛔ **Aucun ne s'approche de 9,22e18.**
🎯 **Vérifié sur un soak d'UNE SEMAINE simulé** (n = 120 960, lux aléatoires 0..54 611) : **erreur
+0,0000 %, aucun débordement**.

🔴 **LA LEÇON, ET ELLE EST DÉSAGRÉABLE** : le correctif d'un défaut de débordement/troncature en a
introduit un autre **de la même famille**, et il aurait été **invisible en séance** — il ne se
déclenche qu'après 4,3 h de régime. ⛔ **Il n'a pas été trouvé par la revue, ni par le build (zéro
warning), mais en CALCULANT les marges au moment de préparer le flash.** ⇒ *un correctif
arithmétique se vérifie par ses BORNES, pas par ses cas de test.*

---

#### d) 🔴 CE QUE CETTE REVUE COÛTE, ET IL FAUT L'ÉCRIRE

**Le firmware corrigé pèse **980 752 o** (+2 992 o sur `fd959f2`) et IL N'A JAMAIS TOURNÉ SUR LA CARTE.** Build
**propre, zéro warning**, ⛔ **et c'est tout ce qu'on en sait.**
⇒ **Les chiffres de §13.19.5bis et §13.19.12 portent `fd959f2`**, ⛔ pas ce binaire. Les correctifs
changent des chemins que la campagne a exercés — notamment la reconfiguration après perte, qui
**n'écrit plus** sur une simple erreur de transport. **⇒ SÉANCE CARTE DE RE-VALIDATION DUE**, et
`dn4-3` ne peut pas passer `done` sans elle.

---

### 13.19.15 🎯 LA SÉANCE DE RE-VALIDATION APRÈS REVUE — firmware `1b2adca`, SHA LU AU BANDEAU

⚠️ **SÉANCE PARTIELLE, ET LA LIMITE EST LA PREMIÈRE CHOSE ÉCRITE : L'OWNER N'ÉTAIT PAS À LA CARTE.**
⇒ ⛔ **Aucun geste physique, aucun constat à l'œil.** Tout ce qui suit est **console seule**.
**Ce qui reste DÛ, et qui ne peut PAS être coché sur cette séance** : AC1 (stimulus main posée),
AC2/AC3 (les 6 débranchements physiques **et le délai de reprise**), AC5 (constat owner sur la
dalle), AC13 (smoke owner). ⛔ **Ne pas lire les verts ci-dessous comme les soldant.**
⚠️ Et **les 5 cases PC étaient nécessairement mortes** pendant toute la séance (exclusivité
WSL↔COM3) — comme à chaque séance carte.

**Chaîne : commits AVANT le flash** (`9f889bf` · `ed29bb4` · `37cbd99`), `porcelain` vérifié **VIDE**,
build refait **après** les commits, SHA **lu au bandeau** (`app_init: App version`). Puis un
correctif de séance (`1b2adca`), re-committé et re-flashé selon la même chaîne.

#### a) 🎯 CE QUE LA CARTE A CONFIRMÉ

| Vérification | Résultat |
|---|---|
| 🔴 **`w2` ne cloue plus le REPL** | **rend la main en 0,121 s**, colonne σ enfin peuplée (1,479 sur le lux) |
| **Boot, les trois capteurs** | `dn_env pret — 3/3 devices ouverts` — aucune `configuration refusee`, donc **la branche de reprise n'a pas eu à jouer** |
| **Aucune panique** | console vivante du premier boot, `6 cases auditees, 0 trou` |
| **Courant en dixièmes** | `0,0 mA` — la décimale est là, le signe se pose |
| **Bornes INA219 publiées** | `bus 0..32764 mV` (⛔ plus 32760) · `courant +-3200,0 mA` · `puissance 0..104844 mW` |
| **`bl auto pas 1`** | 🎯 **REFUSÉ**, avec le mécanisme du gel expliqué |
| **`bl auto bornes 0 54612`** | 🎯 **REFUSÉ** — 54611 est le plus grand lux publiable |
| **`bl auto bornes 1 2 3`** | 🎯 **REFUSÉ** — argument surnuméraire |
| **`bl auto on` sans lux appliqué** | 🎯 **« AUCUNE application depuis le boot »** — ⛔ plus « 100 % (sur 0 lx) » |
| **La loi en régime** | **100 → 80 → 60 → 56 %** en 3 cycles, puis **STABLE** pendant que le lux dérive 322 → 314 lx |
| **Pression** | porte enfin son **âge** (162 ms) ; unité **Pa** annoncée, conversion faite ici |
| **Gaz, retour à l'état coupé** | propre après `capteurs gaz off` |
| **`fps 15`** | **37,40 Hz, écart +0,00 %** — identique au T0 |

#### b) Budgets sur `1b2adca` — ⚠️ tas relevé **AU BOOT PROPRE** (aucune navigation jouée)

| Grandeur | `fd959f2` | **`1b2adca`** | Écart |
|---|---:|---:|---|
| Binaire | 977 760 o | **981 664 o** | **+3 904 o** — partition **77 % libre** |
| RAM interne libre | 91 631 o | **91 575 o** | −56 o (bruit d'allocation) |
| PSRAM libre | 7 768 008 o | **7 768 008 o** | ✅ **identique à l'octet** |
| Tas LVGL utilisé | 20 472 o | **20 500 o** | +28 o (le même bruit qu'au T0, en sens inverse) |
| Plus gros bloc | 40 752 o | **40 752 o** | ✅ **identique à l'octet** |
| Fragmentation | 3 % | **2 %** | −1 pt |
| `fps 15` | 37,40 Hz | **37,40 Hz** | ✅ **+0,00 %** |
| Boot | 2 330 ms | **2 350 ms** | +20 ms |

#### c) 🔴 CE QUE LA SÉANCE A TROUVÉ, ET QUE LA REVUE DE CODE AVAIT MANQUÉ

**`env` NIAIT UNE DÉCISION OWNER.** Sa ligne de clôture imprimait *« X2 (la 6ᵉ case) **n'est pas
tranché** »* — alors que **X2 EST TRANCHÉ** depuis la séance du même jour, et que c'est **le
résultat central de la story** (*« AUCUNE 3ᵉ grandeur »*, décision owner).

🔴 **LES TROIS COUCHES DE REVUE L'ONT MANQUÉE, ET LE MÉCANISME EST INSTRUCTIF** : elles ont lu
**le code** et **les artefacts**, sur 2 285 lignes de diff — ⛔ **jamais la SORTIE de la commande**.
Il a fallu **flasher et taper `env`** pour la voir.
⇒ **LEÇON D'INSTRUMENT : une revue de code ne lit pas ce que le programme DIT.** Les étiquettes de
sortie se relisent **À L'EXÉCUTION**, exactement comme les chiffres. ✅ Corrigé (`1b2adca`) et
**vérifié à la sortie**, pas au source.

#### d) 🔴 UNE PRÉMISSE DE MON PROPRE CORRECTIF, DÉMENTIE PAR LA CARTE

Le message du commit `9f889bf` affirme : *« Au premier cycle après `capteurs gaz on` la plaque n'est
pas à 300 °C et la compensation rend **~12,9 MΩ** — publié ET poussé dans W2 »*. **C'était une
PRÉDICTION tirée de la lecture du source du composant, ⛔ pas une mesure.**

**Mesuré sur la carte** : le premier cycle après `capteurs gaz on` publie **5 093 Ω**, et
`gas_valid` **et** `heater_stable` sont **VRAIS immédiatement**. Puis la résistance grimpe :

| cycle | +0 | +1 | +2 | +3 | +4 | +5 |
|---|---:|---:|---:|---:|---:|---:|
| **gaz (Ω)** | **5 093** | 13 673 | 16 365 | 18 929 | 21 259 | **24 468** |

🔴 **CONCLUSION QUI VA CONTRE MON CORRECTIF : `heater_stable` dit « la plaque a atteint sa
température », ⛔ PAS « le film MOX s'est stabilisé ».** Le **burn-in** décrit en §13.19.10
(2 kΩ → 50 kΩ en 12 min) **traverse intégralement la garde** — les deux drapeaux sont verts pendant
toute la montée.

⇒ **Ce que le correctif fait vraiment** : il garde l'artefact `adc_gas ≈ 0` (une lecture invalide
signalée par la puce), **qui ne s'est pas produit ici**. C'est une garde **défensive et correcte**,
⛔ **mais elle ne répare PAS ce que §13.19.10 a mesuré.**
⇒ **LA PISTE GAZ DE `w2` RESTE POLLUÉE PAR LE BURN-IN.** L'observation de §13.19.10 — *« le gaz
qualifie UNIQUEMENT par son burn-in »* — **tient entièrement**, et le verdict X2 sur le gaz reste
fondé sur l'**absence de réponse aux deux bouffées**, ⛔ pas sur son W2.
⚠️ **Une garde correcte contre le mauvais mode de défaillance reste une garde qui ne protège pas.**

---

### 13.19.16 🎯 LA SÉANCE OWNER — AC1, AC5, AC2/AC3 ET AC13 SOLDÉS, firmware `1b2adca`

**Owner À LA CARTE.** Gestes physiques et constats à l'œil : Nasbarok. Commandes et relevés : agent.
⚠️ **Les 5 cases PC étaient nécessairement mortes** (exclusivité WSL↔COM3) — dit ici comme à chaque
séance, parce que le smoke porte dessus.

#### a) 🎯 AC1 — LE STIMULUS, ET LE RETOUR N'EST PAS LE DÉPART

Auto **DÉSARMÉ** pendant tout le test (⛔ pour que la dalle ne bouge pas et ne pollue pas la lecture).
⚠️ **Lectures espacées de 5,5 s** : le capteur ne se rafraîchit qu'au cycle, trois appels rapprochés
rendraient **trois fois la même mesure** — un piège d'instrument qui aurait fabriqué une fausse
stabilité.

| État | L1 | L2 | L3 |
|---|---:|---:|---:|
| **Départ** | **241 lx** (brut 290) | 240 (289) | 239 (287) |
| 🖐️ **Main posée** | **0 lx** (brut 1) | 0 (1) | 0 (1) |
| **Main retirée** | **210 lx** (brut 253) | 210 (252) | **209** (251) |

🎯 **LE RETOUR N'EST PAS IDENTIQUE AU DÉPART : 239 → 209, soit −12,6 %.** *Une valeur rejouée serait
revenue exacte.* La valeur change **dans les deux sens**. **155 lectures, 0 erreur de toute cause.**
⚠️ **Le brut vaut 1 sous la main, pas 0** — le capteur mesure encore : c'est ce qui sépare une main
d'un capteur mort. (Sur `fd959f2` le retour montait de +35 % ; ici il descend de −12,6 % parce que la
pièce s'assombrissait — le départ dérivait déjà 241 → 239. **Le sens n'est pas le critère, l'écart
l'est.**)

#### b) 🎯 AC5 — LE CONSTAT OWNER, ET LA PREUVE QUE L'INSTRUMENT POUVAIT VOIR LE DÉFAUT

Pièce à ~200 lx. Armement, puis descente **relevée** : **100 → 80 → 60 → 37 %**, puis **stable à
37 %** sur quatre cycles pendant que le lux glisse 204 → 200 lx.

**VERBATIM OWNER, sur les trois questions posées séparément :**
1. *« la dalle s'est-elle assombrie ? »* → **« bof un peu oui »**
2. *« 37 % est-il lisible ici ? »* → **« oui cca va »**
3. *« est-ce que ça pompe ? »* → 🎯 **« nop rien image stable »**

⚠️ **LE POINT 1 EST À GARDER TEL QUEL** : **63 points de duty** en moins n'ont produit qu'un
*« bof un peu »* perçu. ⇒ **le duty LEDC n'est PAS linéaire en luminosité perçue**, et une loi
linéaire en lux produit une réponse visuellement molle. ⛔ Ce n'est pas un défaut de l'AC — c'est
une donnée pour qui voudra un jour courber la loi.

🔴 **ET LA QUESTION QUE §13.19.7 LAISSAIT OUVERTE EST FERMÉE PAR LA MESURE : LA BOUCLE OPTIQUE NE SE
FERME PAS, MÊME EN PIÈCE ÉCLAIRÉE.** Le constat *« ça ne pompe pas »* de la séance précédente avait
été fait **dans le noir**, où `bl 100` et `bl 0` rendent tous deux `brut 0` ⇒ il ne prouvait rien.
**A/B joué ici à ~180 lx, puis REJOUÉ DANS L'ORDRE INVERSE pour annuler la dérive de la pièce** :

| Ordre | Bloc 1 (moyenne) | Bloc 2 (moyenne) | Écart `bl100 − bl0` |
|---|---:|---:|---:|
| `bl 0` puis `bl 100` | 186,0 lx | 183,3 lx | **−2,7 lx** |
| `bl 100` puis `bl 0` | 177,3 lx | 174,0 lx | **+3,3 lx** |

🎯 **LE SIGNE S'INVERSE AVEC L'ORDRE** — dans les deux cas c'est le **premier bloc** qui lit le plus
haut, quelle que soit la luminosité de la dalle. ⇒ **la différence est entièrement expliquée par la
dérive de la pièce (~3 lx par bloc de 33 s), et la contribution de la dalle est SOUS le bruit.**
⇒ 🔴 **L'AUTO-POMPAGE EST PHYSIQUEMENT IMPOSSIBLE SUR CETTE CARTE : la boucle est OUVERTE.** Le
*« nop rien image stable »* de l'owner est vrai, **et on sait maintenant POURQUOI** — ce n'est pas la
bande morte qui l'empêche, c'est l'absence de contre-réaction.
⚠️ **CE QUE ÇA CHANGE POUR LE DÉFAUT REPORTÉ** (bande morte inclusive, non hystérétique) : il reste
**RÉEL et NON EXERCÉ**, mais il ne peut être déclenché que par un **éclairage EXTERNE** qui papillote
de ~19 lx. ⛔ Pas par la dalle elle-même.

#### c) 🎯 AC2 / AC3 — SIX DÉBRANCHEMENTS PHYSIQUES, BUDGET ANNONCÉ D'AVANCE, **0 BRIQUAGE**

| Cycle | `dn_env` (3 capteurs) | GT911 | Verdict |
|---|---|---|---|
| 1 | 0 erreur, 15 cycles | 2 202 lect. / **0** | propre |
| 2 | 0 erreur, cycles 3→10 couverts | 2 246 lect. / **0** | propre |
| 3 | 0 erreur | **0** | propre |
| 4 | 0 erreur, 32 cycles | 3 227 lect. / **0** | propre |
| **5** | 0 erreur | 🔴 **1 erreur**, puis **+1 214 lectures SANS nouvelle** | **DÉGRADÉ** |
| 6 | 0 erreur | 1 848 lect. / **0** | propre |

🎯 **0 BRIQUAGE SUR 6.** **1 cycle dégradé sur 6**, et la **signature transitoire est reproduite** :
l'erreur apparaît dans les premières secondes puis **le compteur se fige** pendant que les lectures
continuent par milliers.

🔴 **ÉCART AVEC LA CAMPAGNE `fd959f2`, ET IL NE S'ATTRIBUE PAS AUX CORRECTIFS.** Elle avait rendu
**2 cycles dégradés sur 6, pic à 42,9 %** ; celle-ci **1 sur 6, pic à 1 erreur**. ⛔ **La condition
diffère** : la carte tournait depuis la séance console, donc **elle était CHAUDE**, et le défaut est
un **démarrage à FROID**. ⚠️ **Conclure « les correctifs ont amélioré le bus » serait une faute de
lecture** — le firmware ne touche pas le GT911.

⛔ **ET LE DÉLAI DE REPRISE N'EST TOUJOURS PAS CHRONOMÉTRÉ — L'INSTRUMENT N'A PAS LA RÉSOLUTION.**
Le réattachement `usbipd` coûte **2,7 à 3,1 s**, et la carte a déjà **3 à 6 cycles** (15-30 s) quand
la console redevient joignable. ⇒ **la fenêtre où la reprise se joue est passée avant qu'on puisse
mesurer.** **AC3 reste PARTIEL sur ce point, et c'est écrit plutôt que contourné.**
⇒ **Recette pour le mesurer un jour** : il faut un instrument **embarqué** (le firmware horodate
lui-même sa première lecture valide par capteur et l'expose), ⛔ pas un poll depuis l'hôte.

#### d) 🎯 AC13 — LE SMOKE OWNER

**Verbatim, sur trois questions posées séparément :** les six cases s'affichent → **« oui »** · le
toucher ouvre le détail et le retour revient → **« oui ok »** · l'heure → **« pas dh »**, précisé
ensuite : la barre affiche **`--:--` / `HEURE NON POSÉE`**.

🎯 **L'HEURE PASSE, ET C'EST LE BON COMPORTEMENT.** Le RTC a son **bit `OS` à 1** — l'oscillateur
s'est arrêté, conséquence attendue de **six coupures d'alimentation d'affilée**. L'heure lue
(`2000-01-01 00:05:10`) est déclarée **`⛔ NON AFFICHABLE`** par le driver, et la barre **AVOUE** au
lieu de mentir. AC13 demande *« l'heure est juste **ou dit honnêtement qu'elle ne l'est pas** »*.
✅ **La deuxième branche est exactement ce qui s'est produit.**

#### e) ⚠️ DEUX DÉFAUTS D'INSTRUMENT DE L'AGENT, DANS CETTE SÉANCE, ET ILS SONT DE LA MÊME FAMILLE

1. 🔴 **UN COMPTEUR D'ERREURS FABRIQUÉ À PARTIR DU NOM DU BUS.** Le harnais extrayait les erreurs par
   `grep -oE "[0-9]+"` appliqué à la chaîne **`i2c 0`** — qui capture **le `2` de « i2c »** en plus du
   `0`. Trois capteurs × (2+0) = **6**. J'ai publié *« débranchement 3/6 DÉGRADÉ, 6 erreurs »* et
   j'en ai tiré *« ma prédiction est confirmée »*. **LES DEUX ÉTAIENT FAUX** : le cycle 3 est propre,
   et la prédiction reste **NON TESTÉE**.
   ⚠️ **Le tell que j'aurais dû voir immédiatement** : une valeur **exactement constante à 6** sur
   **14 relevés**, présente dès la première seconde. **Un compteur d'erreurs qui n'évolue jamais
   d'un iota n'est pas un compteur, c'est une constante.**
2. **UN `bc` NOURRI DE VIDE.** `sed 's/.*conformite \([0-9]*\).*/\1/p'` matchait **aussi** les
   lignes de TEXTE contenant le mot « conformite » (*« présence et conformite SEULEMENT »*), où
   `[0-9]*` matche le **vide** ⇒ `bc` recevait `0++0` et rendait une erreur de syntaxe, colonne
   affichée `?`.

✅ **CORRIGÉ ET PROUVÉ PAR TÉMOIN POSITIF** (méthode `dn1-1`) : le harnais corrigé extrait **42 / 7 /
3** d'une ligne d'erreurs **fabriquée**, ignore la ligne de texte, et rend **0** sur la vraie sortie.
⛔ **Sans ce témoin, « 0 erreur » et « instrument aveugle » seraient indiscernables** — et c'est
précisément ce qui venait de se produire.

🔴 **LA LEÇON, ET ELLE VAUT AU-DELÀ DE CETTE SÉANCE** : la console de ce dépôt est **riche et
rédigée pour un humain** — mots-clés répétés dans la prose, chiffres au milieu des phrases. **La
gratter au `grep` fabrique des nombres plausibles.** ⇒ **tout harnais de scraping se prouve sur une
ligne FABRIQUÉE avant d'être cru sur une ligne réelle.**

---

### 13.19.13 ⚠️ CE QUI N'A PAS MARCHÉ DANS CETTE SÉANCE — y compris mes propres erreurs de méthode

1. 🔴 **J'AI PUBLIÉ UN CRITÈRE DE VALIDITÉ, PUIS JE L'AI DÛ RÉTRACTER DEVANT L'OWNER.**
   La latence `acceptation→label` a dérivé sur trois fenêtres (**86 → 138 → 220 ms**) avec des
   pertes seq croissantes (1 → 4 → 5). J'en ai tiré, avec assurance, une règle : *« un relevé de
   latence n'est recevable que si l'injecteur a placé 225/225 avec 0 perte seq »*. **La cinquième
   fenêtre l'a démolie : 225/225, 0 perte seq, et latence 260 ms** — la plus haute de toutes.
   ⇒ ⛔ **La corrélation sur quatre points était une COÏNCIDENCE.**
   ✅ **Ce qui reste vrai, et c'est tout** : cette latence varie d'un **facteur 3** (86 à 260 ms) sur
   **le même firmware**, sans que les compteurs de liaison en disent la cause. ⇒ **instrument NON
   FIABLE pour un delta** tant que sa variance n'est pas isolée. **Au ledger.**
   ⚠️ **Et l'hypothèse « fragmentation du tas LVGL » a été RÉFUTÉE dans le même geste** : `20 500 o /
   40 752 / 2 %` **avant ET après** une fenêtre complète.

2. 🔴 **J'AI FAILLI PUBLIER UNE MESURE DE CONTRE-RÉACTION OPTIQUE QUI NE VALAIT RIEN.** Le premier
   A/B `bl 100`/`bl 0` a été fait à **2 500 lx d'ambiante**, où l'apport de la dalle est
   nécessairement invisible — et la dérive ambiante (+46 lx) était **plus grande que l'effet
   cherché**. ⇒ **il excluait une contre-réaction FORTE, pas une faible**, alors qu'elle ne serait
   dangereuse **qu'en pièce sombre**. **Rejoué dans le noir**, il devient décisif.
   ⚠️ *Un A/B doit se jouer dans la condition où sa réponse compte, pas dans celle où l'on est.*

3. 🔴 **J'AI CONFONDU DEUX DIAGNOSTICS DANS UNE SEULE PHRASE, JUSTE APRÈS AVOIR CITÉ LA LEÇON QUI
   L'INTERDIT.** Mon premier message de console pour la pression disait *« hors plage 300..1100 hPa,
   OU jamais lue »* — c'est **exactement** la faute `tronquee`/`trop_longue` (CR 2026-08-17), et je
   l'avais recopiée dans le commit précédent en la présentant comme une leçon acquise.
   ✅ Corrigé : **trois états, trois phrases**, et la **valeur brute** est conservée pour pouvoir
   diagnostiquer au lieu de deviner.

4. ⚠️ **UNE FAUSSE ALERTE : j'ai soupçonné une tâche morte sur dix valeurs identiques.**
   Discriminé au lieu d'être supposé (`age` **4 939 → 3 079 → 1 233 ms**, `lectures` **195 → 199**),
   l'alerte était **fausse**. ✅ **Mais la lever a produit une non-régression forte** relevée
   chauffeur gaz ACTIF et `dn_env` en régime. *Une alarme fausse levée par la mesure coûte moins
   qu'une alarme vraie ignorée.*

5. ⚠️ **J'AI LU UNE PHOTO COMME UNE MESURE.** De `install_01.jpg` j'ai tiré *« la carte est posée sur
   la grille d'aération de la tour »* et j'en ai fait un **troisième terme** pour AC9. Réponse
   owner : *« le capteur est éloigné de la soufflerie »*. ⛔ **Une photo se lit, elle ne se déduit
   pas** — et l'owner voit le montage.

6. ⚠️ **MON PREMIER `grep -c` SUR `managed_components/` A RENDU 82 CONTRE LES 103 ATTENDUS**, parce
   que j'avais ajouté `--include=*.c --include=*.h` que la commande d'origine n'a pas.
   ⇒ ⛔ **Ne jamais comparer deux comptes sans comparer leurs INSTRUMENTS.**
   ✅ **Effet de bord utile** : l'écart a révélé que **21 des 103 sont dans de la documentation**, et
   que le chiffre qui porte le risque est **82**.

7. ⚠️ **UN ARTEFACT DE MON PROPRE `grep`** : `13500 ohms` apparaissait à chaque relevé de gaz — il
   attrapait le **texte de l'avertissement IAQ**, pas une mesure. Repéré avant publication.

8. ⚠️ **LE PLANCHER DU RÉTROÉCLAIRAGE N'ÉTAIT PAS RÉGLABLE À CHAUD.** J'avais rendu les bornes en
   **lux** ajustables et laissé le plancher en **%** figé à la compilation — or **c'est précisément
   lui que l'œil a déplacé**. J'avais appliqué *« l'arbitrage se tranche sur la dalle »* **à moitié**.

9. ⚠️ **J'AI JUGÉ LE PLANCHER DE LISIBILITÉ DANS LA MAUVAISE CONDITION** (rideau ouvert, ~1 500 lx)
   alors que **le plancher ne s'applique qu'en pièce sombre**. La dichotomie a dû être rejouée.

---

## 13.20 — SÉANCE `dn4-7` « Le ToF porte-t-il vraiment » (2026-08-21) — **P9.3b**

> **Ce que cette marche instruit** : la portée RÉELLE du VL6180X, mesurée, contre une datasheet dont
> une étiquette avait été prise pour une mesure en `dn4-3`. **D4 est rouverte sur ce point précis**
> par décision owner. Le reste de D4 est intact.

### 13.20.1 🎯 AC1 (a) — LA SOURCE EST OBTENUE, ET **`st.com` N'EST PAS « INJOIGNABLE »** : LA CAUSE EST NOMMÉE

`dn4-3` avait arrêté la piste SR03 sur un constat brut : *« `st.com` injoignable, `curl` → `http=000` »*.
Ce constat était **vrai mais muet** — il ne disait pas *pourquoi*, donc il ne pouvait pas être contourné.

**Mesuré le 2026-08-21 :**

| Chemin | Résultat |
|---|---|
| DNS `www.st.com` | ✅ résout (`104.126.37.179`, Akamai) |
| Réseau générique (`example.com`) | ✅ `200` |
| `https://www.st.com/…` en HTTP/2 | 🔴 **le TLS ABOUTIT**, puis `HTTP/2 stream 1 was not closed cleanly: INTERNAL_ERROR (err 2)` |
| idem forcé en `--http1.1` | 🔴 expire à 60 s, **0 octet reçu** |
| idem depuis **Windows** (`Invoke-WebRequest`, hors WSL) | 🔴 expire aussi |

🔴 **CE N'EST DONC PAS WSL**, et ce n'est pas une panne de résolution : c'est **`st.com` qui refuse ce
client**, après avoir accepté la poignée de main TLS. ⇒ le contournement n'est pas réseau, il est
**documentaire** : passer par un miroir, et **prouver l'identité du fichier**.

### 13.20.2 🔴 LE PIÈGE DU MIROIR — **UN `200` ET UN NOM DE FICHIER ONT MENTI TOUS LES DEUX**

Deux URL plausibles ont rendu **HTTP 200** :

| URL | Ce que ça rendait vraiment |
|---|---|
| `mouser.com/datasheet/2/389/vl6180x-1849942.pdf` | ⛔ **pas un PDF** — une page anti-bot JavaScript de 13 895 o |
| `pololu.com/file/0J1187/VL6180X.pdf` | ⛔ un **vrai PDF ST**… du **VL53L0X** (titre : *« World's smallest Time-of-Flight ranging and gesture detection sensor »*) |
| `pololu.com/file/0J1188/VL6180X-application-note.pdf` | ⛔ un **schéma de carte Pololu**, `Author: Pololu Corporation` |

🎯 **C'est exactement la confusion que §13.16.7 avait déjà tranchée une fois** — et elle est revenue
par la porte du nom de fichier. **Seule la lecture du titre et de l'auteur l'a vue.**
⇒ ⛔ **Un code 200 ne qualifie pas un document. Un nom de fichier non plus.**

### 13.20.3 ✅ LES DEUX DOCUMENTS ST, **IDENTIFIÉS ET CROISÉS**

| Réf | Document | DocID | Rév / date | Empreinte `sha256` | Auteur PDF |
|---|---|---|---|---|---|
| **[AN]** | *VL6180X basic ranging application note* | `026571` | **Rev 1, juin 2014** | `091291adc9812852e4206f4bf33a6a1646a51c1c9d92bf5c4b00d1ee5efabbab` | `STMICROELECTRONICS` |
| **[DS]** | *Proximity and ambient light sensing (ALS) module* | `026171` | **Rev 7, mars 2016** | `87e1b09668160d71…` | `STMICROELECTRONICS` |

🎯 **[AN] a été téléchargé depuis DEUX hébergeurs indépendants** — `cdn.sparkfun.com` et `pololu.com` —
et les deux copies ont la **même empreinte `sha256`**. ⇒ le fichier n'a pas été retouché en route.
C'est ce croisement, ⛔ pas la confiance dans un hébergeur, qui rend la source recevable.

⚠️ **[AN] existe en Rev 2 (juillet 2018)**, non obtenue (même blocage `st.com`). **Ce qui est joué ici
est la Rev 1**, et c'est écrit tel quel. ⛔ Ne pas laisser croire que la dernière révision a été lue.

⚠️ **[AN] se prévient lui-même**, p. 1 : *« Settings presented in this document are for test purpose
only. Performance and reliability not guaranteed. »*

### 13.20.4 🎯 LA PRÉMISSE DE LA STORY EST **CONFIRMÉE MOT POUR MOT** — l'owner avait raison

[DS] §3.1, p. 27, verbatim :

> *« The following table specifies ranging performance up to 100mm. **Ranging beyond 100mm is
> possible with certain target reflectances and ambient conditions but not guaranteed.** »*

⇒ **« possible » n'est pas « non ».** Le verdict de `dn4-3` (*« ne porte que 100 mm GARANTIS »*)
citait correctement la garantie, mais **en tirait une portée**, ce que le texte ne dit pas.

### 13.20.5 🔴 **LE PLAFOND STRUCTUREL — ET IL EST DANS LE REGISTRE, PAS DANS UNE ÉTIQUETTE**

[DS] §6.2.42, p. 72 :

```
RESULT__RANGE_VAL     Address: 0x062     Type: R
  [7:0]  result__range_val: Final range result value presented to the user for use. Unit is in mm.
```

🔴 **Le résultat de portée est un champ de 8 BITS, en MILLIMÈTRES.**
⇒ **255 mm est le maximum REPRÉSENTABLE.** ⛔ **Aucun réglage optique, aucune cible, aucune
convergence ne peut faire tenir 2 000 mm dans un octet.**

⚠️ **Et c'est une nature différente de l'étiquette « 100 mm »** : « 100 mm » est une *garantie de
performance*, qui se conteste par la mesure. **8 bits en mm est une propriété de la carte des
registres**, qui ne se conteste pas — elle se lit. C'est pour ça qu'elle est recevable **sans carte**,
là où la portée, elle, ⛔ ne l'est pas.

⛔ **Aucun facteur d'échelle de portée n'est publié** dans les **trois** documents ST récupérés
([DS], [AN], et **DT0037** *« VL6180X range and ambient light sensor quick setup guide »*, DocID026595).
Le seul « scaler » de [DS] (§2.10.7) est celui de **l'ALS**, ⛔ pas de la télémétrie.

### 13.20.6 🎯 **LE « TROISIÈME ÉTAT » D'AC2 EST DOCUMENTÉ PAR ST** — la valeur plausible et fausse

[DS] **Table 12, « Range error codes »**, p. 27 :

| Code | Nom ST | Texte ST |
|---|---|---|
| **13 / 15** | Range overflow | *« Range value out of range. This occurs when the target **is detected** by the device but is placed at a high distance (**> 200mm**) resulting in internal variable overflow. »* |
| **16** | `Ranging_Filtered` | *« Distance filtered by **Wrap Around Filter (WAF)**. Occurs when a **high reflectance target** is detected **between 600mm to 1.2m**. »* |
| **18** | `Data_Not_Ready` | — |

> **1.** *« Errors 16 & 18 require VL6180X API. »*

🔴 **LA PHRASE QUI COMPTE** : le filtre anti-repliement **n'existe QUE dans l'API ST**, qui **n'est pas
embarquée ici** (driver MAISON, X5 tranché en §13.19.4). ⇒ **sans lui, une cible très réfléchissante
entre 600 mm et 1,2 m peut rendre une valeur PROCHE, PLAUSIBLE, et SANS AUCUN code d'erreur.**

⇒ **C'est précisément l'état n°3 que AC2 nomme comme le dangereux**, et il n'est pas hypothétique :
**ST le décrit, avec sa plage.** ⛔ Une valeur de portée ne se croit **jamais** seule : elle se croise
avec la distance **mesurée au mètre**.

### 13.20.7 ⚠️ DEUX CORRECTIONS DE PROTOCOLE — écrites **avant** la carte, pas après

**a) `42°` n'est PAS le cône de télémétrie.** [DS] §2.10.1 *« Field of view »* — **42 degrés (demi-angle)**
— est dans le **chapitre 2.10 « Ambient light sensor (ALS) »**, et Table 20 le range sous
*« ALS performance »*. ⛔ **C'est le champ de l'ALS.**

**Le cône de TÉLÉMÉTRIE** est la divergence de l'émetteur, [DS] §2.9.3 :
> *« Angle of divergent laser emission is **25° +/- 5°** … at 1/e² of the peak intensity. »*

**b) `0x0040` : les DEUX documents ST se contredisent, et c'est [DS] qui fait foi.**

| Source | Ce qu'elle dit |
|---|---|
| **[AN] §9** | `WriteByte(0x0040, 0x63);  // Set ALS integration time to 100ms` |
| **[DS] §6.2.36** | `SYSALS__INTEGRATION_PERIOD`, offset `0x040`, registre **16 bits**, champ **`[8:0]`**, *« 1 code = 1 ms (0 = 1 ms). Recommended setting is 100 ms (0x63) »* |

⇒ `0x63` est la valeur du **champ**, donc l'octet de **poids FAIBLE** (`0x0041`). L'écriture de [AN]
pose `0x63` dans le poids **fort** et déborde le champ `[8:0]`.

🎯 **CONSÉQUENCE À ÉCRIRE DANS LE BON SENS** : `dn4-3` avait posé `0x0040=0x00` / `0x0041=0x63`.
**C'est `dn4-3` QUI A RAISON, et [AN] qui est bancal.** ⛔ **Ne pas inverser ce verdict.**
✅ Effet utile : la garde anti-fantôme de `dn_env` (qui relit `0x0041 == 0x63`) **reste conforme après
le passage de SR03** — ce qui n'aurait pas été le cas en jouant [AN] à la lettre.

### 13.20.8 🎯 AC1 (b) — **LA DÉCISION D'INSTRUMENT, ET SON MOTIF**

**Décision : poser l'instrument** (patron `dn4-2` AC4), **dans `dn_console.c`**, ⛔ pas ~37 commandes
tapées, ⛔ pas un module neuf.

| Option | Pourquoi elle est écartée |
|---|---|
| **~37 `i2c ecrire 29 <hi> <lo> <val>` à la main** | [AN] §1.3 : *« This procedure **must be repeated** if the VL6180X has been power cycled »*. Une campagne = des dizaines de cycles ⇒ **des CENTAINES de lignes tapées**, sur un bus dont §13.17.1 a mesuré qu'il lâche les transferts multi-octets à froid. **L'instrument deviendrait la première source d'erreur de la mesure.** |
| **Poser `i2c ecrire16` d'abord** | Il raccourcit chaque ligne, **il n'en supprime aucune**. ⛔ **Mauvaise granularité.** |
| **Un module `dn_tof.c` séparé** | Il devrait dupliquer `i2c_dev_fermer()`, qui **porte le correctif de revue `dn4-2`** sur la course avec le sondage GT911 (~30/s) ⇒ **deux sources de vérité sur exactement ce qui venait d'être durci.** |

✅ **Retenu** : la table SR03 **dans le source**, où elle **porte sa citation** et **se relit en revue** —
et **hors du chemin de régime** : `dn_env` n'est **pas** touché tant qu'AC1 n'a pas prouvé la
proportionnalité.

### 13.20.9 ✅ LA SÉQUENCE EST POSÉE — ET **PROUVÉE PAR EXTRACTION CROISÉE**, ⛔ pas relue à l'œil

`tools/verif_sr03.py` **extrait la séquence des DEUX côtés** et les compare :
- côté document : le texte de [AN] §9, via `pdftotext`
- côté firmware : la table C `k_sr03_prive[]` / `k_sr03_public[]` de `dn_console.c`

⛔ **Le harnais ne contient PAS la séquence** — il ne prouverait que sa cohérence avec lui-même.

```
[AN] prives  : 30   firmware : 30
[AN] publics :  6   firmware :  7
✅ BLOC PRIVE : les 30 ecritures sont IDENTIQUES, valeurs ET ordre
✅ BLOC PUBLIC : conforme, hors l'ecart 0x0040/0x0041 DECLARE en commentaire
```

🎯 **ET LA GARDE A ÉTÉ VUE ROUGE** — quatre mutants, tous attrapés (`exit 1`) :

| Mutant | Ce qui a été muté | Verdict |
|---|---|---|
| 1 | une **valeur** privée (`0x00DB` `0xCE`→`0xCF`) | 🔴 `[11] doc 0x00DB=0xCE  fw 0x00DB=0xCF` |
| 2 | deux entrées **permutées** (l'ordre) | 🔴 `[04]` et `[05]` signalés |
| 3 | un **public non déclaré** (`0x0031` `0xFF`→`0xFE`) | 🔴 `ecart(s) NON DECLARE(S) : 0x0031` |
| 4 | une entrée **supprimée** | 🔴 `longueurs differentes : 30 vs 29` |

⚠️ **Et il refuse le mauvais document** : pointé sur [DS] au lieu de [AN], il sort en `exit 2` sur
l'empreinte — **la parade directe au piège de §13.20.2**.

⚠️ **La séquence fait 30 privés, pas « ~30 »** — le compte est maintenant EXACT, et il est vérifié
mécaniquement.

### 13.20.10 🔴 AC7 — **LA PRÉDICTION, ÉCRITE ET COMMITTÉE AVANT LA MOINDRE MESURE**

> *Une prédiction démentie est plus instructive qu'une prédiction tenue.* Ce qui suit est écrit
> **avant** que la carte ait rendu un seul chiffre de portée.

**Référence de départ** (état du dépôt, à re-mesurer en T0) : `dn_env` fait **4 transactions I²C par
cycle** (BH1750 : 1 · VL6180X : 3), cycle **~1 140 µs**, bus à **7 devices**.

**Ce qu'une lecture de distance EN RÉGIME ajouterait**, en coup par coup ([DS] §6.2.16) :

| Geste | Transactions |
|---|---|
| `0x015 ← 0x07` (effacer l'interruption) | 1 |
| `0x018 ← 0x01` (déclencher) | 1 |
| sondage de `0x04F` jusqu'à *New Sample Ready* | **n, inconnu** |
| `0x062` (valeur) + `0x04D` (statut) | 2 |
| `0x015 ← 0x07` (ré-effacer) | 1 |

**PRÉDICTIONS, chiffrées :**

1. **P1 — transactions** : **5 fixes + n sondages**. Avec un sondage toutes les 2 ms et une
   convergence de l'ordre de 10 ms, **n ≈ 5** ⇒ **~10 transactions**, soit `dn_env` qui passe de
   **4 à ~14 par cycle** — un facteur **~3,5×**.
2. **P2 — durée** : à ~285 µs la transaction (1 140 µs / 4), **~+2,9 ms** de transport ⇒ cycle
   **~4,0 ms**. ⚠️ **Mais le terme dominant n'est PAS le transport, c'est l'ATTENTE** :
   `SYSRANGE__MAX_CONVERGENCE_TIME` (`0x001C`) vaut **`0x31` = 49 ms** au reset ([DS] §6.2.20).
   ⇒ **je prédis que la mesure démentira P2 par le haut**, et que le coût réel sera **dominé par la
   convergence**, pas par l'I²C.
3. **P3 — portée** : au vu de §13.20.5, **je prédis qu'aucune valeur valide ne dépassera 255 mm**, et
   qu'au-delà de ~200 mm le code d'erreur **13/15 « Range overflow »** apparaîtra ([DS] Table 12).
4. **P4 — cône** : divergence **25° ± 5°** ⇒ demi-angle **12,5°** ⇒ largeur vue à distance `d` :
   `2 · d · tan(12,5°) = 0,443 · d`.
   ⇒ **à 1 m je prédis une bande de ~44 cm** (bornes de la tolérance : **35 à 54 cm**).
   ⚠️ **P4 est une prédiction OPTIQUE, et elle suppose que la puce VOIE à 1 m** — ce que P3 dit
   improbable. ⇒ **le cône devra se mesurer à une distance où la détection EXISTE** (AC3 le dit déjà),
   et la formule s'y applique à l'identique.
5. **P5 — SR03** : je prédis que **les 37 écritures aboutiront** (le bus les porte déjà en régime) et
   que **le balayage d'intégration deviendra proportionnel**. ⚠️ **Si P5 est démentie, Z1 se solde par
   la négative et la story s'arrête** — et **c'est un résultat**, pas un échec.

⛔ **Aucune de ces cinq prédictions n'est un résultat.** Elles sont là pour être confrontées.

### 13.20.11 ✅ CE QUE LE FIRMWARE PORTE MAINTENANT — `tof`, et **rien dans le régime**

| Commande | Ce qu'elle fait |
|---|---|
| `tof etat` | les registres, **LECTURE SEULE** — ⛔ aucune écriture |
| `tof sr03` | joue [AN] §9 (30 privés + 7 publics), **relit**, et **distingue** ce qui se relit de ce qui ne se relit pas |
| `tof balayage` | **rejeu à l'identique** de §13.19.5 — 1, 2, 3, 5, 10, 20, 50, 100 ms. **LE critère d'AC1** |
| `tof als <ms>` | une mesure ALS à intégration imposée |
| `tof range [n]` | télémétrie, **les trois états**, taux de détection, écart-type |

**Deux choix de conception écrits, parce qu'ils sont contestables :**

1. 🔴 **La relecture des registres PRIVÉS est imprimée comme une DONNÉE, ⛔ pas comme un verdict.**
   ST ne les documente pas et ne promet nulle part qu'ils se relisent. **Un écart de relecture sur un
   registre non documenté ne prouve rien** — le traiter comme un échec fabriquerait un défaut.
   Seuls les **publics** concluent.
2. 🔴 **`tof range` ne peut PAS trancher l'état n°3** et **le dit** : *« la console ne peut pas le
   dire, il faut la distance PHYSIQUE au mètre »*. ⛔ Une console qui prétendrait valider une distance
   sans référence externe serait exactement le fantôme de §13.10, en pire.

⛔ **Ce qui N'A PAS été fait, et c'est délibéré** : `dn_env` n'est **pas** touché, `dn_ui.c` non plus
(grille figée à six, X2). **La story l'exige tant que T1 n'a pas rendu son verdict.**

### 13.20.12 ⚠️ CE QUI N'A PAS MARCHÉ DANS CETTE SÉANCE — y compris mes propres erreurs de méthode

1. 🔴 **J'AI TÉLÉCHARGÉ ET FAILLI CROIRE DEUX DOCUMENTS DU MAUVAIS CAPTEUR.** Les URL
   `pololu.com/file/0J1187/VL6180X.pdf` et `…/0J1188/VL6180X-application-note.pdf` portent
   « VL6180X » **dans leur nom** et rendent des PDF valides en `200` — l'un est la datasheet du
   **VL53L0X**, l'autre un schéma **Pololu**. Je les avais déjà rangés comme sources avant de lire
   leur titre. ⇒ ⛔ **Vérifier l'identité AVANT de ranger, jamais après.** La garde `sha256` de
   `verif_sr03.py` existe **à cause de cette erreur**.

2. ⚠️ **J'AI ANNONCÉ « DEUX ÉCARTS AVEC CE QUE `dn4-3` AVAIT ÉCRIT » AVANT D'AVOIR LU §6.2.36.**
   Sur `0x0040`, la lecture du registre a montré **l'inverse de ce que j'avais dit** : c'est `dn4-3`
   qui est conforme et **[AN] qui est bancal**. ⛔ **Un écart entre deux sources n'est pas un défaut
   de la carte tant qu'on n'a pas lu laquelle fait foi.**

3. ⚠️ **`curl` a rendu `200` sur une page anti-bot de 13 895 o** que j'ai d'abord comptée comme un
   PDF. Le `file` l'a démentie : `JavaScript source, ASCII text`. ⇒ ⛔ **le code HTTP ne qualifie pas
   un contenu** — c'est la **signature `%PDF-`** qui l'a fait, et c'est elle qui a été mise dans la
   boucle de sondage ensuite.

4. ⚠️ **`dn4-3` avait écrit « `st.com` injoignable » sans instruire la cause**, et ce constat muet a
   **coûté une piste entière**. La cause tient en une ligne (`INTERNAL_ERROR` HTTP/2) et se
   contourne. ⛔ **Un blocage se NOMME, sinon il se re-subit.**

---

## 13.21 🔴 SÉANCE CARTE `dn4-7` (2026-08-21) — SR03 SE CHARGE, ET **CE N'ÉTAIT PAS LA CAUSE**

> Firmwares : `98baeb4` puis `d75a5f6`, **SHA lus au bandeau** les deux fois. Arbre `porcelain`
> **vide** avant chaque flash. Owner **absent de la boucle** : aucun geste physique dans cette passe.

### 13.21.1 ✅ T0 — le point de départ

| Instrument | Relevé |
|---|---|
| Bandeau | `App version: 98baeb4` puis `d75a5f6` — ⛔ **sans `-dirty`** |
| `SPI Flash Size` | `16MB` (bootloader) |
| `dn_env` | `2/3 devices ouverts`, INA219 `NON CADENCE` ✅ conforme au retrait |
| **`touch` (l'instrument du bus)** | **874 lectures, `erreurs I2C 0`** ⇒ 🎯 **bus SAIN**, la fenêtre à froid n'est pas active |
| VL6180X (`env`) | **VIVANT**, 7 lectures, `i2c 0 · donnee 0 · bornes 0 · conformite 0` |
| Ligne `gpio_install_isr_service` | présente — ⚠️ **antérieure et attendue**, ⛔ pas une régression |

⚠️ **Un reset RTS après `flash` n'est PAS un démarrage à froid** — §13.17 le dit : le geste qui
reproduit la dégradation est le **débranchement PHYSIQUE**. Le bus sain ici ne contredit donc rien.

### 13.21.2 🎯 SR03 SE CHARGE — ET C'EST PROUVÉ REGISTRE PAR REGISTRE

`0x0016` valait **`0x01`** (puce fraîche) : la condition exacte qu'AC1 impose.

| Bloc | Résultat |
|---|---|
| **38 écritures** | **0 en échec** |
| **30 registres PRIVÉS** | 🎯 **tous relus EXACTEMENT comme écrits**, un par un |
| **8 registres publics** | tous conformes, `0x002E` compris (auto-effaçant, voir §13.21.4) |

⇒ ⛔ **« SR03 ne se charge pas » est RÉFUTÉ.** La séquence entre, tient, et se relit.

### 13.21.3 🔴 ET LE BALAYAGE EST **IDENTIQUE AVANT ET APRÈS** — L'HYPOTHÈSE DE LA STORY TOMBE

**A/B joué dans la MÊME séance, même firmware, même pièce, même lumière** — ⛔ pas une comparaison
avec un relevé d'un autre jour :

| Intégration | 1 ms | 2 ms | 3 ms | 5 ms | 10 ms | 20 ms | 50 ms | 100 ms |
|---|---|---|---|---|---|---|---|---|
| §13.19.5 (`dn4-3`) | `0000` | `0000` | `FFFF` | `FFFF` | `FFFF` | `FFFF` | `FFFF` | `FFFF` |
| **AVANT SR03** (2026-08-21) | `0000` | `0000` | `0000` | `FFFF` | `FFFF` | `FFFF` | `FFFF` | `FFFF` |
| **APRÈS SR03** (2026-08-21) | `0000` | `0000` | `0000` | `FFFF` | `FFFF` | `FFFF` | `FFFF` | `FFFF` |

⇒ 🔴 **SR03 NE CHANGE RIEN À L'ALS.**

**CE QUE ÇA DÉTRUIT** : l'hypothèse qui fondait toute la garde d'AC1 — *« l'ALS est binaire PARCE QUE
SR03 manque, donc le télémètre a la même dépendance »* — est **RÉFUTÉE PAR LA MESURE**.
⇒ ⛔ **Le balayage ALS ne qualifie PAS SR03** : il y est **insensible**. Une garde insensible à ce
qu'elle prétend garder est une garde décorative, et Z1 ne peut pas se solder dessus.

⚠️ **Détail qui compte et qui écarte une explication facile** : la colonne `attendu_ms` **suit**
l'intégration demandée (2, 3, 3, 5, 11, 19, 49, 97 ms). **La puce HONORE la durée** ; c'est la
**valeur** qui ne bouge pas. ⛔ Ce n'est donc pas « les écritures n'arrivent pas ».

### 13.21.4 🔴 TROIS DÉFAUTS DE **MON** INSTRUMENT — dont un qui **fabriquait un taux de détection**

⚠️ **Aucun des trois n'est de la carte. Les trois sont de moi.**

**a) 🔴 LE PIRE — `tof range` COMPTAIT DES MESURES INEXISTANTES.**
La branche de comptage testait `err == 0` **seul**. Or `err` est le code de la **dernière** mesure :
quand l'attente **expire**, aucune mesure neuve n'a lieu et `err` vaut 0. Sortie **réellement
imprimée** sur dix tirs qui n'avaient **jamais** abouti :

```
  1. mesure VALIDE (err = 0)  : 10 / 10
  taux de detection           : 10/10 = 100,0 %
  moyenne des VALIDES : 0,0 mm · ecart-type : 0,0 mm
```

…pendant que les dix lignes au-dessus disaient toutes `⚠️ PAS DE New Sample Ready` à **601 ms**.
🎯 **Le tell était là, et c'est exactement celui du dépôt** : une valeur **exactement constante**
(`0,0` / `0,0`). ⇒ **Correctif** : un **quatrième seau**, *« AUCUNE MESURE (pas de New Sample) »*.
Un tir qui n'a pas signalé sa mesure **n'est pas une mesure à 0 mm** — il ne compte **nulle part**.

**b) 🔴 J'AI DÉSACTIVÉ MOI-MÊME L'INTERRUPTION DE PORTÉE, EN L'ÉCRIVANT COMME UN CHOIX.**
J'avais écarté les trois registres « Optional » de [AN] §9 en motivant : *« `0x0014 = 0x24`
écraserait le `0x20` posé par `dn_env_configurer()`, dont le témoin de conformité dépend »*.
⛔ **FAUX, et vérifiable en trois lignes** : `conformite_verifier()` relit **`0x003F` et `0x0041`**,
**rien d'autre**. `0x0014` est **écrit** par `configurer()` mais **jamais relu** par la garde.
**Conséquence, [DS] §6.2.12** : `0x014` porte `als_int_mode` en `[5:3]` et `range_int_mode` en `[2:0]`.

| Valeur | `[5:3]` ALS | `[2:0]` PORTÉE |
|---|---|---|
| `0x20` (dn4-3) | `4` New sample ✅ | **`0` Disabled** 🔴 |
| `0x24` ([AN] Optional) | `4` New sample ✅ | `4` New sample ✅ |

⇒ **la puce ne pouvait PHYSIQUEMENT pas signaler sa mesure**, et j'ai failli conclure « le télémètre
ne répond pas ». ⛔ **J'ai affirmé une dépendance qui n'existait pas dans le code que je venais de
lire.**

**c) ⚠️ UN FAUX ROUGE SUR UN COMPORTEMENT CONFORME.** `tof sr03` sortait
*« 🔴 `0x002E` : écrit `0x01`, relu `0x00` — c'est un fantôme »*. [DS] **§6.2.29** :
*« FW clears bit after operation carried out »*. ⇒ relire `0x00` est le **signal de SUCCÈS** : la
recalibration VHV **a été menée à terme**. ⛔ Traiter un registre **auto-effaçant** comme s'il gardait
sa valeur **fabrique un défaut** sur une puce correcte.

⚠️ **Et la garde a suivi PAR EXTRACTION, ⛔ pas par exception** : `verif_sr03.py` a **correctement
refusé** le nouveau `0x0014` (*« écart NON DÉCLARÉ »*), parce qu'il ne parsait que le bloc
« Recommended ». Il extrait désormais **aussi** le bloc « Optional » du **même document** et vérifie
la valeur contre lui. Témoins rejoués : valeur d'optionnel fausse ⇒ `exit 1` · optionnel retiré ⇒
`exit 0` (en jouer moins est légitime) · arbre livré ⇒ `exit 0`.
⚠️ **Mon premier test de ce témoin lisait `$?` APRÈS un `| tail`** — donc le code de `tail` : il
annonçait `exit 0` sur un mutant qui échouait. **Rejoué sans le tuyau.**

### 13.21.5 🔴 LE TÉLÉMÈTRE NE MESURE TOUJOURS PAS — ET LE TABLEAU CLINIQUE EST NET

Avec `0x0014 = 0x24` **vérifié en place**, `tof range 10` :

```
  1. mesure VALIDE (err = 0)           : 0 / 10
  2. la PUCE DIT qu'elle a echoue      : 0 / 10
  · transport I2C en echec             : 0 / 10
  · AUCUNE MESURE (pas de New Sample)  : 10 / 10
```

**Sondage MANUEL, registre par registre** (⛔ pas par la commande, pour ne pas dépendre d'un
instrument que je venais de corriger) :

| Registre | Lu | Ce que ça dit |
|---|---|---|
| `0x0018` SYSRANGE__START | écrit `01` → relu **`00`** | ✅ **le firmware a CONSOMMÉ le déclenchement** |
| `0x0119` FIRMWARE__BOOTUP | `01` | ✅ le firmware de la puce a démarré |
| `0x0014` INTERRUPT_CONFIG | `24` | ✅ l'interruption de portée est bien armée |
| `0x004D` RANGE_STATUS | `01` | `device_ready` seul — ⛔ **aucun code d'erreur** |
| `0x004F` INTERRUPT_STATUS | `00` | ⛔ jamais de *New Sample Ready* |
| `0x0062` RANGE_VAL | `00` | — |
| **`0x006C` RETURN_SIGNAL_COUNT** | **`00 00 00 00`** | 🔴 **zéro photon compté** |
| **`0x0074` RETURN_AMB_COUNT** | **`00 00 00 00`** | 🔴 **zéro ambiant compté** |
| **`0x007C` RETURN_CONV_TIME** | **`00 00 00 00`** | 🔴 **le moteur n'a JAMAIS convergé** |

### 13.21.6 🎯 ET L'ALS DIT **« UNDERFLOW »** — ⛔ PAS « SATURÉ ». `dn4-3` AVAIT LU À L'ENVERS

`RESULT__ALS_STATUS` (`0x004E`) = **`0x23`** ⇒ `[7:4] = 2`. [DS] **§6.2.38** :

> `0000: No error` · `0001: Overflow error` · **`0002: Underflow error`**

🔴 **La puce déclare un SOUS-FLUX**, c'est-à-dire **pas assez de lumière**.
⇒ le `FFFF` de §13.19.5 **n'est PAS une saturation** : c'est une **valeur INVALIDE** accompagnée d'un
drapeau d'erreur **que personne n'avait lu**. ⛔ **§13.19.5 concluait « comparateur saturé » — c'est
à REPRENDRE** : le registre d'état dit l'inverse.

**LE CROISEMENT QUI TRANCHE, MÊME INSTANT, MÊME CARTE, À QUELQUES CENTIMÈTRES :**

| Capteur | Ce qu'il dit |
|---|---|
| **BH1750** `0x23` | **76 lx** — VIVANT, `i2c 0 · donnee 0 · bornes 0` |
| **VL6180X** ALS `0x29` | **UNDERFLOW** — « pas assez de lumière » |

⇒ 🔴 **LES DEUX CAPTEURS DE LUMIÈRE DE LA MÊME CARTE VOIENT DES CHOSES INCOMPATIBLES.**

**FAISCEAU COHÉRENT** : côté **numérique**, le VL6180X est **parfait** (I²C, 38 écritures, 30 relectures
privées exactes, firmware démarré, VHV recalibré). Côté **optique**, il ne reçoit **RIEN** : ALS en
sous-flux, **zéro** signal, **zéro** ambiant, **zéro** convergence, et **aucun code d'erreur de portée**
— ⚠️ **ce qui est logique : un émetteur qui ne tire pas ne produit ni mesure NI erreur.**

### 13.21.7 ⏳ CE QUI RESTE À TRANCHER — **ET ÇA DEMANDE LES MAINS ET LES YEUX DE L'OWNER**

Trois causes candidates, **⛔ aucune n'est départagée par la console** :

1. 🎯 **UN FILM DE PROTECTION ENCORE SUR LA FENÊTRE DU CAPTEUR** — le plus fréquent sur ces
   breakouts, et **le moins cher à vérifier** : ça se regarde en cinq secondes.
   ⚠️ **Cohérent avec TOUT le tableau** : un cache opaque au proche-IR laisse le numérique intact et
   met l'optique à zéro.
2. ⚠️ **`AVDD_VCSEL` mal alimenté.** [DT0037] p. 2 : *« The VL6180X requires power to be applied to
   **AVDD_VCSEL pin before or at the same time** as power is applied to AVDD »*. Le TOF050C a son
   propre régulateur, et **ce dépôt n'a JAMAIS mesuré ce rail**. Un VCSEL non alimenté = laser muet,
   sans erreur.
3. ⚠️ **Module défectueux.**

⛔ **AUCUNE mesure de portée, de cône, de répétabilité ou de lumière n'est recevable tant que ce
point n'est pas tranché** — elles mesureraient toutes le même zéro.

### 13.21.8 🔴 CE QUE LA SÉANCE FAIT À LA STORY — **c'est un `[CC]`, ⛔ pas une mise à jour**

La story `dn4-7` prévoyait : *« si le balayage n'est pas proportionnel, Z1 se solde PAR LA NÉGATIVE
et la story s'arrête »*. **Appliquer cette règle telle quelle serait une faute**, et voici pourquoi :

| Ce que la story supposait | Ce que la mesure a établi |
|---|---|
| l'ALS est binaire **parce que** SR03 manque | ⛔ **RÉFUTÉ** — identique avant/après un SR03 prouvé chargé |
| donc le balayage ALS **qualifie** SR03 | ⛔ **RÉFUTÉ** — il y est **insensible** |
| donc « pas proportionnel » ⇒ « SR03 a échoué » | ⛔ **FAUX** : SR03 a **réussi**, registre par registre |
| l'ALS `FFFF` = **saturation** | 🔴 la puce dit **UNDERFLOW** |

⇒ **Z1 se scinde en deux, et les deux moitiés ont des réponses OPPOSÉES** :
- *« La séquence SR03 se charge-t-elle ? »* → ✅ **OUI, prouvé.**
- *« La puce se met-elle à mesurer ? »* → 🔴 **NON — et pour une cause qui n'a RIEN à voir avec SR03.**

⚠️ **Le périmètre change** : la question n'est plus *« jusqu'où porte-t-il ? »* mais
***« pourquoi son optique ne reçoit-elle rien ? »***. ⇒ **`[CC] bmad-correct-course`**, ⛔ pas une
réécriture silencieuse du tableau.

### 13.21.9 🔴 LE CANAL DE **RÉFÉRENCE** EST À ZÉRO — ça élimine toute l'optique, et **rouvre `XSHUT`**

**Constat owner du 2026-08-21** : ⛔ **il n'y a AUCUN film de protection** sur la fenêtre du capteur.
⇒ **la piste n°1 de §13.21.7 est FERMÉE par l'œil.** Question owner dans la foulée :
*« c'est pas parce qu'il n'est pas branché entièrement ? »*

**Lecture décisive, après un déclenchement :**

| Canal | Registres | Lu |
|---|---|---|
| **RETOUR** (voit la cible) | `0x06C` · `0x074` · `0x07C` | `00 00 00 00` ×3 |
| 🔴 **RÉFÉRENCE** (voit le VCSEL **EN INTERNE**) | `0x070` · `0x078` · `0x080` | **`00 00 00 00` ×3** |

🎯 **POURQUOI LE CANAL DE RÉFÉRENCE TRANCHE** : il est **interne au boîtier** — il voit l'émetteur par
un chemin optique qui **ne sort jamais du composant**. Il ne dépend ⛔ ni d'une cible, ⛔ ni de la
propreté de la fenêtre, ⛔ ni de l'éclairage de la pièce. **Il compterait des photons capteur posé
face contre la table.**

⇒ **Référence = 0 ET retour = 0 ET convergence = 0 ⇒ LE MOTEUR DE MESURE NE DÉMARRE JAMAIS.**
**Ce qui est ÉLIMINÉ, et ce n'est pas une opinion :**
- ⛔ le film de protection (déjà écarté à l'œil — **et il n'aurait de toute façon pas mis le canal
  INTERNE à zéro**) ;
- ⛔ « pas de cible en vue » — une absence de cible **converge quand même** et rend un code d'erreur ;
- ⛔ toute obstruction optique externe.

#### 🔴 CE QUE ÇA ROUVRE : « `XSHUT` EST TIRÉ HAUT » N'A **JAMAIS ÉTÉ MESURÉ ÉLECTRIQUEMENT**

Le module est un **`TOF050C-VL6180X`, 6 broches : `VIN · GND · SDA · SCL · INT · XSHUT`**, barrette
soudée. **Quatre sont câblées.** `INT` et `XSHUT` ne le sont pas (§13.16.7, décision mesurée).

- **`INT`** est une **SORTIE**. La laisser en l'air ⛔ **ne peut pas** empêcher le moteur de tourner.
- **`XSHUT`** est **l'ENTRÉE D'ACTIVATION**.

🔴 **ET VOICI LA FAILLE DANS LE VERDICT DE `dn4-2`** : §13.16.7 conclut *« `XSHUT` est TIRÉ HAUT sur ce
breakout »* par un **RAISONNEMENT**, ⛔ pas par un voltmètre :

> *« Preuve : la puce rend `B4` cinq fois sur cinq avec le fil RETIRÉ, alors que la datasheet ST est
> formelle — `XSHUT` basse ou flottante ⇒ shutdown, pas d'acquittement. »*

⚠️ **La déduction vaut ce que vaut sa prémisse**, et la prémisse traite « shutdown » comme **BINAIRE**.
🔴 **L'instrument d'alors — « est-ce que ça acquitte en I²C ? » — ne pouvait PAS distinguer
« pleinement activé » de « NUMÉRIQUE activé, ANALOGIQUE éteint ».**
⇒ **Et c'est exactement l'état qu'on mesure aujourd'hui.** L'inférence n'était pas fausse au moment
où elle a été faite : **elle était sous-déterminée, et rien ne le disait.**

🎯 **`dn4-2` AVAIT ÉCRIT LE RÉSIDUEL, ET IL SE RÉALISE** :
> *« Si le ToF devient un jour intermittent, **`XSHUT` est le premier suspect à re-nommer** — pas la
> soudure. »*

#### 🔴 PRÉDICTION, ÉCRITE ET COMMITTÉE **AVANT** LE GESTE OWNER

| # | Prédiction | Ce qu'elle vaut si elle tombe |
|---|---|---|
| **Q1** | La tension sur `XSHUT` **n'est PAS un 3V3 franc** (flottante, ou nettement en dessous) | si elle est à **3,3 V franc**, ⛔ **`XSHUT` est EXONÉRÉ** et le suspect suivant devient le rail `VIN`/`AVDD_VCSEL` |
| **Q2** | `XSHUT` tiré **franchement** à 3V3 ⇒ `REFERENCE_CONV_TIME` devient **non nul** et *New Sample Ready* apparaît | si **rien ne change**, ⛔ `XSHUT` est exonéré **par la mesure**, ⛔ pas par un raisonnement |

⚠️ **L'ORDRE COMPTE, ET IL EST DICTÉ PAR LE RISQUE** : **Q1 D'ABORD** (voltmètre, **risque nul**), Q2
seulement ensuite. ⛔ **Ne pas commencer par le fil** : §13.16.7 a mesuré qu'un fil `XSHUT` vers
`3V3` a coïncidé avec **la mort du bus entier** (TCA9554 muet, panique haltée, console perdue).
⚠️ **Le mécanisme n'a JAMAIS été isolé** — hypothèse dominante : un pin mal enfoncé **pontant `3V3`
(rang 11) et `G` (rang 12)**, donc un **accident de câblage**, ⛔ pas `XSHUT` lui-même.
⇒ **Si Q2 est joué : vérifier que le pin est À FOND et ne touche PAS la cavité `G` voisine.**
✅ **Et si le bus remeurt de la même façon, ce sera la DEUXIÈME occurrence** — donc, pour la première
fois, un mécanisme **isolable** au lieu d'une corrélation.

### 13.21.10 🔴 **RÉTRACTATION — `XSHUT` EST EXONÉRÉ, ET `dn4-2` AVAIT RAISON**

⛔ **Ce qui suit CONTREDIT §13.21.9, écrit une heure plus tôt. On ne le réécrit pas : on l'annule
ici, avec son motif.** §13.21.9 accusait le verdict de `dn4-2` d'être *« sous-déterminé »*. **C'est
MON accusation qui était fausse.**

**Question owner** : *« XSHUT n'alimenterait pas le laser justement ? »* — elle mérite la machine
d'états, ⛔ pas un « non ».

**[DS] §2.2, Figure 9 — le diagramme d'états complet :**

```
  Power off ──AVDD on, GPIO0=0──> Hardware standby ──GPIO0=1──> MCU boot ──> Software standby
                                  (EN RESET,                                  ├─ range_start ─> Range measurement ─done─┐
                                   ⛔ NE REPOND PAS                           └─ als_start ───> ALS measurement ──done─┤
                                   A L'I2C)                                   <───────────────────────────────────────┘
```

**DEUX FAITS QUI FERMENT LA QUESTION :**

1. 🔴 **`XSHUT` N'ALIMENTE RIEN.** [DS] table des broches : `GPIO0/CE` est un **`Digital I/O`**, un
   **signal logique**. L'alimentation du laser est une **BROCHE SÉPARÉE** : **broche 8 `AVDD_VCSEL`,
   *« VCSEL power supply 2.6 to 3.0 V »***, avec sa propre masse (broche 9 `AVSS_VCSEL`).
2. 🔴 **ET `XSHUT` FAIT DÉJÀ SON TRAVAIL — c'est PROUVÉ, pas supposé.** L'état où nous sommes
   (**I²C qui répond** + **`FIRMWARE__BOOTUP` = `01`**) est *Software standby*. Or **le SEUL chemin
   qui y mène passe par `GPIO0 = 1` puis `MCU boot`**. [DS] §2.2 est formel sur l'autre branche :
   *« The device is held in reset until GPIO0 is de-asserted. Note that the device **will not
   respond to I²C communication** in this mode. »*
   ⇒ ⛔ **Il n'existe AUCUN état intermédiaire** « GPIO0 à moitié haut, analogique éteint » : le
   diagramme n'a que **deux** transitions pilotées par GPIO0, et **les deux sont AVANT que l'I²C
   fonctionne.**

⇒ 🎯 **`XSHUT` EST EXONÉRÉ PAR LA MACHINE D'ÉTATS.** Et donc **le verdict de `dn4-2` était BON** :
sa déduction *« la puce acquitte ⇒ `XSHUT` est haut »* est **exactement ce que le diagramme
autorise**. ⛔ **Ma critique de §13.21.9 est RETIRÉE.**
⚠️ **Ce que je maintiens de §13.21.9** : la distinction « inférence » / « mesure » reste juste **en
général** — ⛔ mais elle ne s'appliquait pas ICI, parce que la datasheet interdit l'état
intermédiaire que je supposais possible. **J'ai généralisé une bonne règle à un cas où elle ne
mordait pas.**

#### ⇒ ET C'EST `AVDD_VCSEL` QUE ÇA DÉSIGNE, PAR ÉLIMINATION ET PAR CONSTRUCTION

⚠️ **LE POINT DÉCISIF** : la machine d'états de [DS] §2.2 **ne modélise QUE `AVDD`**. `AVDD_VCSEL`
n'y apparaît **nulle part** — ST le suppose présent.
⇒ 🔴 **UN `AVDD_VCSEL` ABSENT EST INVISIBLE À TOUT CE QU'ON PEUT LIRE EN I²C** : la puce démarre,
répond, accepte `range_start`, retourne en *Software standby*… et n'a **rien** mesuré. **C'est
mot pour mot le tableau de §13.21.5/.6/.9.**

| Suspect | Verdict |
|---|---|
| Film de protection | ⛔ **ÉLIMINÉ** — constat owner, **et** le canal de référence est **interne** |
| Absence de cible | ⛔ **ÉLIMINÉ** — une absence de cible **converge** et rend un code d'erreur |
| `INT` non câblé | ⛔ **ÉLIMINÉ** — c'est une **SORTIE**, et [DS] écrit *« otherwise left unconnected »* |
| `XSHUT` non câblé | ⛔ **ÉLIMINÉ** — machine d'états, ci-dessus |
| 🔴 **`AVDD_VCSEL` non alimenté** | ⏳ **SEUL SUSPECT DEBOUT**, et **invisible en I²C par construction** |

⚠️ **`AVDD_VCSEL` n'est PAS sorti sur la barrette 6 broches** (`VIN GND SDA SCL INT XSHUT`) : c'est
une broche du **composant**, alimentée par le régulateur **du breakout**. ⇒ **ce qui est mesurable
sans démonter reste `VIN`**, et au-delà c'est **interne au module**.

🎯 **CONSÉQUENCE PRATIQUE, ET ELLE EST FRANCHE** : si `VIN` est bon, **il n'y a rien à recâbler** —
le défaut est **dans le module**, et la question devient *« on en remplace un »*, ⛔ pas
*« on ajoute un fil »*.

### 13.21.11 🔴 **LA PUCE DIAGNOSTIQUE SON PROPRE LASER : « VCSEL Continuity Test »**

**Lu sur une passe ENTIÈREMENT PROPRE** (reboot, attente hors fenêtre de boot, **une seule**
commande, **les 10 registres lus sans un seul échec**, bus à **2 erreurs sur 2 392 lectures**) :

| Registre | Lu | Décodage [DS] |
|---|---|---|
| `0x004D` RANGE_STATUS | **`0x11`** | `[7:4] = 1` ⇒ 🔴 **« VCSEL Continuity Test »** (Table 12) |
| `0x004F` INTERRUPT_STATUS_GPIO | **`0x40`** | `[7:6] = 1` ⇒ 🔴 **« Laser Safety Error »** (§6.2.39) |
| `0x0062` RANGE_VAL | **`0xFF`** | 255 — valeur de butée, ⛔ pas une distance |

🎯 **CE N'EST PAS UN CHIFFRE QU'UN DÉFAUT DE BUS FABRIQUE** : c'est un **code d'erreur nommé**, issu
de l'**auto-test du composant**, qui porte précisément sur la **continuité électrique du VCSEL**.
**Lu proprement DEUX fois**, sur deux passes séparées par un reboot.

⇒ **Ça converge avec tout le reste** (§13.21.5/.6/.9) : côté **numérique** la puce est parfaite, côté
**émetteur** elle échoue son propre test de continuité. **C'est le seul suspect qui restait debout —
et il n'est plus déduit par élimination, il est NOMMÉ PAR LA PUCE.**

#### ⚠️ CE QUI N'EST **PAS** ENCORE PROUVÉ, ET IL FAUT L'ÉCRIRE

🔴 **La confirmation sur un tir FRAIS N'A PAS ÉTÉ OBTENUE.** `tof range 5` a échoué **avant même de
déclencher** — les cinq tirs sortent en `DEMARRAGE KO (ESP_ERR_INVALID_STATE)`, donc **aucune mesure
neuve n'a eu lieu** et `0x004D` n'a **pas été rafraîchi**.
⇒ ⛔ **`0x11` est un RÉSIDU d'une tentative antérieure**, ⛔ pas le produit d'un tir observé de bout
en bout. **Corrélation forte, mécanisme non re-déclenché.** ⚠️ *C'est exactement la nuance que
§13.16.7 avait dû écrire pour `XSHUT`, et elle vaut ici aussi.*

### 13.21.12 🔴 **QUATRIÈME DÉFAUT D'INSTRUMENT — ET CELUI-LÀ A INVENTÉ UNE PANNE MATÉRIELLE**

**J'ai annoncé à l'owner « le ToF est intermittent ». C'ÉTAIT FAUX.** A/B, **même capteur, même
instant** :

| Chemin | Résultat |
|---|---|
| **`dn_env`** — **handle PERSISTANT**, 3 transactions / 5 s | **22 lectures · `i2c 0` · `conformite 0`** |
| **console `tof …` / `i2c lire16`** — **ouvre ET ferme un device À CHAQUE APPEL** | **2 réussites / 15** |

⇒ 🔴 **LE DÉFAUT EST DANS MON CHEMIN D'ACCÈS, ⛔ PAS DANS LE CAPTEUR.** Le symptôme s'effondre sous
la **répétition rapide** d'ajout/retrait de device — alors que `dn_env` tient déjà un handle
permanent sur `0x29` — et **une commande isolée et espacée réussit**.
⚠️ ⛔ **Le retrait de device n'est PAS en cause** : `RETRAIT DU DEVICE REFUSE` compté **0 fois sur
15**. Le mécanisme exact **reste ouvert** ; ce qui est établi, c'est **l'A/B**.

🔴 **C'est le PIRE des quatre défauts de cette séance.** Les trois premiers rendaient un **chiffre**
faux ; celui-là a **fabriqué un récit de panne matérielle** — et je l'ai présenté à l'owner comme une
observation, en le raccrochant au résiduel `XSHUT` de §13.16.7 qui **n'est donc PAS déclenché**.
⇒ **RÈGLE** : ⛔ **avant de conclure « le capteur est intermittent », comparer AU CHEMIN D'ACCÈS
STABLE qui tourne déjà à côté.** Ici il existait, il tournait, et il disait l'inverse.

#### ⇒ LA SUITE EST UN CORRECTIF D'INSTRUMENT, ⛔ PAS UN AUTRE SONDAGE À L'AVEUGLE

**`tof range` doit passer par le handle PERSISTANT de `dn_env`**, comme les lectures de régime qui,
elles, ne ratent jamais. ⛔ **Tant que le déclenchement passe par un device ouvert/fermé à la
volée, aucun tir frais ne sera observable de bout en bout** — et donc `0x11` restera un résidu.
✅ **Et c'est la voie que les Dev Notes de la story prévoyaient déjà** (*« `dn_env.c` : y ajouter la
séquence SR03 à l'init »*).

### 13.21.13 🔴 LE TIR FRAIS **NE REPRODUIT PAS** LE « VCSEL Continuity Test » — et mon correctif n'a PAS marché

**Firmware `e162f56`** (les commandes `tof` passent par le handle persistant de `dn_env`),
hors fenêtre de boot, bus à **0 erreur sur 2 085 lectures**.

#### a) ⛔ LE VCSEL EST DISCULPÉ POUR L'INSTANT — l'erreur ne se rejoue pas

Sur les tirs où **toutes** les transactions ont abouti :

```
  #   0x0062   status  err  retour  ms   lecture
  1     0 mm   0x01    0        0  601  ⚠️ PAS DE New Sample Ready
  3     0 mm   0x01    0        0  601  ⚠️ PAS DE New Sample Ready
  5     0 mm   0x01    0        0  601  ⚠️ PAS DE New Sample Ready
  7     0 mm   0x01    0        0  603  ⚠️ PAS DE New Sample Ready
```

🔴 **`status = 0x01`, ⛔ PAS `0x11`.** Le code d'erreur est **0**, pas 1.
⇒ **Le « VCSEL Continuity Test » de §13.21.11 NE SE REPRODUIT PAS sur un tir frais.**
⛔ **Il ne peut donc PAS être retenu comme diagnostic** — c'était bien un **résidu**, et §13.21.11
avait raison de refuser de le conclure. ⚠️ **Ce qui l'a produit reste INEXPLIQUÉ**, et c'est écrit
comme tel : une erreur lue proprement deux fois, qui ne se rejoue pas, **reste une observation
ouverte** — ⛔ ni un diagnostic, ⛔ ni un artefact qu'on efface.

#### b) ✅ CE QUI SE CONFIRME, LUI, POUR LA QUATRIÈME FOIS

**Sur toute transaction propre, depuis le premier essai : la puce accepte le déclenchement et
NE CONVERGE JAMAIS.** Pas de *New Sample Ready* après **600 ms** (budget de convergence : **49 ms**),
`RANGE_VAL` = 0, taux de retour = 0, et §13.21.5 avait déjà mesuré signal / ambiant / temps de
convergence **tous à zéro**, **canal de RÉFÉRENCE INTERNE compris** (§13.21.9).
⇒ **C'est LE fait stable de cette séance**, et ⛔ **aucun code d'erreur ne l'accompagne**.

#### c) 🔴 CINQUIÈME AVEU — MON CORRECTIF DE §13.21.12 N'A PAS RÉSOLU LE PROBLÈME

Les lectures échouent encore, **et selon un motif qui n'est pas du hasard** :

| Tir | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| lecture | 🔴 KO | ✅ | 🔴 KO | ✅ | 🔴 KO | ✅ | 🔴 KO | ✅ |
| `attendu_ms` | 1 | 601 | 1 | 601 | 2 | 601 | 1 | 603 |

🎯 **ALTERNANCE PARFAITE**, et les échecs sont **immédiats** (1-2 ms), ⛔ pas des expirations.
Même chose sur `tof sr03` : **les 38 écritures aboutissent**, et **les 8 relectures échouent toutes**
en `ESP_ERR_INVALID_STATE`.

⇒ 🔴 **J'AI SUR-ATTRIBUÉ L'A/B DE §13.21.12 AU HANDLE.** L'A/B lui-même est vrai — `dn_env` ne rate
jamais, la console ratait — mais j'en ai tiré **une CAUSE** (« c'est l'ouverture/fermeture de
device ») alors qu'il comparait **AUSSI deux cadences d'accès** radicalement différentes.
**Le confondant n'était pas séparé.** Le correctif reste défendable, ⛔ mais sa justification était
trop rapide, et **c'est la mesure qui le dit**.
⚠️ **Ce qui reste ACQUIS de §13.21.12** : que « le ToF est intermittent » était **faux**, et que
`dn_env` lit ce capteur **sans une seule erreur**. 🔴 **Ce qui TOMBE** : que la cause soit le handle.

**Piste la plus probable, ⛔ NON VÉRIFIÉE, écrite pour la prochaine passe** : un enchaînement
**écriture → lecture immédiate** sur ce device. Les tirs qui ont **attendu 601 ms** avant de lire
**réussissent** ; ceux qui lisent **tout de suite après des écritures** **échouent**.
⇒ **à tester par un DÉLAI EXPLICITE entre écriture et lecture**, ⛔ pas par une nouvelle refonte.

### 13.21.14 🎯 LA CADENCE DE SONDAGE ÉTAIT **UNE** CAUSE — ⛔ pas TOUTE la cause

**Firmware `95d49cb`.** Prédiction écrite avant le flash : *« référence à battre = 4 `LECTURE KO`
sur 8 »*.

| | avant (`e162f56`) | après (`95d49cb`) |
|---|---|---|
| sondages par tir | ~300 (2 ms × 600 ms) | **~50** (5 ms × 250 ms) |
| **`LECTURE KO`** | **4 / 8** | 🎯 **2 / 8** |

⇒ **La piste « martelage du bus » est CONFIRMÉE À MOITIÉ** : diviser les transactions par six
**divise les échecs par deux**. ⛔ **Mais elle ne les supprime pas** ⇒ **ce n'était pas toute la
cause**, et le reste **demeure inexpliqué**. ✅ Écrit comme tel : une hypothèse à moitié vraie
**reste à moitié fausse**.

#### 🔴 ET UN FAIT NOUVEAU QUI AFFINE TOUT : **LE MOTEUR DÉMARRE VRAIMENT**

Sur deux tirs, `RANGE_STATUS` = **`0x00`** — et `[0]` est `result__range_device_ready`, dont [DS]
§6.2.38 dit : *« When 0, indicates **the device is busy** »*.

⇒ 🎯 **La puce PASSE BIEN EN MESURE.** ⛔ Ce n'est donc PAS « elle ignore le déclenchement ».

**LE TABLEAU COMPLET, SUR SIX TIRS PROPRES :**

| Ce qu'on observe | Valeur |
|---|---|
| le déclenchement est consommé (`0x018` → `00`) | ✅ |
| le composant passe **occupé** (`status` `0x00`) | ✅ |
| *New Sample Ready* après **255 ms** (budget : **49 ms**) | 🔴 **JAMAIS** |
| `RANGE_VAL` · taux de retour | **0** · **0** |
| code d'erreur | 🔴 **0 — AUCUN** |
| signal · ambiant · temps de convergence (§13.21.5) | **0** · **0** · **0** |
| **canal de RÉFÉRENCE INTERNE** (§13.21.9) | 🔴 **0** |

⇒ **La puce démarre une mesure, reste occupée, ne converge jamais, ne se plaint jamais, et ne
compte AUCUN photon — ⛔ pas même sur son chemin optique INTERNE.**

⚠️ **ET IL Y A UNE ANOMALIE DANS CETTE ANOMALIE, écrite pour la prochaine passe** : [DS] §6.2.20
borne la mesure à `SYSRANGE__MAX_CONVERGENCE_TIME` = **49 ms** au reset, et [DS] Table 12 prévoit le
code **7 « Max Convergence »** quand la limite est atteinte. **Ni l'abandon ni le code n'arrivent.**
⇒ ⛔ **Ne pas conclure « émetteur mort » tant que ce point n'est pas instruit** : une puce qui
n'abandonne pas au bout de son propre budget ne se comporte pas comme la datasheet le décrit, et
**cette anomalie-là n'a pas de suspect nommé.**

#### ⇒ CE QUE LA SÉANCE LAISSE

✅ **Solide, mesuré et REPRODUIT** : SR03 se charge (38/38, quatre fois) · le balayage ALS est
identique avant/après · **la télémétrie ne converge jamais, sans erreur, avec zéro photon des deux
côtés**.
🔴 **Non conclu** : *pourquoi*. Le « VCSEL Continuity Test » **ne se rejoue pas** (§13.21.13) et reste
une **observation ouverte**.
🔴 **Cinq défauts d'instrument** ont été trouvés et corrigés **dans cette seule séance**, dont un qui
**fabriquait un taux de détection de 100 %** et un qui a **inventé une panne matérielle**.
⏳ **T2 à T6 restent SUSPENDUS.** ⇒ **`[CC] bmad-correct-course`** : le périmètre n'est plus
*« jusqu'où porte-t-il ? »* mais *« pourquoi ne converge-t-il jamais ? »*.

### 13.21.15 🔴 **VERDICT — L'ÉTAGE ANALOGIQUE DU VL6180X EST MORT. LE NUMÉRIQUE, LUI, EST INTACT.**

**Test de stimulus owner, protocole `dn4-2` (main puis lampe), avec le BH1750 en CONTRÔLE au même
instant, sur la même carte, à quelques centimètres.**

| Condition | **BH1750** (contrôle) | **VL6180X ALS** 1 ms | **VL6180X ALS** ≥ 5 ms |
|---|---|---|---|
| ambiant | 276 lx | — | `FFFF` |
| 🖐 **main posée** | **5 lx** | `0000` | **`FFFF`** |
| 🔦 **lampe de téléphone** | 🎯 **11 418 lx** | **`0000`** | **`FFFF`** |

🔴 **L'ALS NE RÉAGIT PAS À UNE VARIATION DE LUMIÈRE DE ~2 280×** (5 lx → 11 418 lx).
Sa sortie ne dépend **QUE de la durée d'intégration** : `0000` à 1 ms, `FFFF` dès 5 ms, **quelle que
soit la lumière**. ⇒ **Ce n'est ni « pas de lumière » (on aurait un compte faible à 100 ms) ni « trop
de lumière » (on aurait `FFFF` dès 1 ms). C'est un compteur qui accumule le TEMPS sans recevoir de
signal photodiode.**

⚠️ **LE PREMIER ESSAI DE LAMPE A ÉTÉ REJETÉ**, et c'est ce qui rend celui-ci recevable : le BH1750
n'y lisait que **235 lx** — la lampe n'éclairait rien. **Un stimulus non prouvé ne produit pas un
constat.** Rejoué avec les deux capteurs sous la lampe.

#### 🎯 LA DÉDUCTION QUI FERME LE DOSSIER — et elle ÉLIMINE l'hypothèse d'alimentation

[DS], table des broches :

| Broche | Rôle |
|---|---|
| 10 **`AVDD`** | *« **Digital/analog** power supply 2.6 to 3.0 V »* |
| 8 `AVDD_VCSEL` | *« VCSEL power supply »* |

🔴 **Le RÉCEPTEUR et le CŒUR NUMÉRIQUE partagent le MÊME rail `AVDD`.** Or le numérique est
**parfait** : I²C, 38 écritures, 30 registres privés relus exactement, `FIRMWARE__BOOTUP = 01`,
recalibration VHV menée à terme.
⇒ **`AVDD` est donc SAIN.** ⛔ **Un défaut d'alimentation ne peut PAS expliquer un récepteur mort
avec un numérique intact** — les deux sont sur le même rail.
⇒ 🔴 **LA PANNE EST DANS LA PUCE, ⛔ PAS DANS SON ALIMENTATION NI DANS SON CÂBLAGE.**

**ET ÇA EXPLIQUE TOUT LE DOSSIER, D'UN SEUL MÉCANISME :**

| Symptôme | Explication |
|---|---|
| ALS « binaire » depuis `dn4-3` (§13.19.5) | ⛔ **n'a JAMAIS eu de rapport avec SR03** — le récepteur ne reçoit rien |
| télémétrie qui ne converge jamais | le FW attend des photons qui n'arrivent **jamais**, ni du retour ni de la **référence interne** |
| **aucun code d'erreur** | le FW **n'atteint jamais** sa branche de terminaison (Finding 4 : abandon inopérant même à **1 ms** de budget) |
| canal de **référence interne** à zéro | même cause : le récepteur ne compte rien, **même sur le chemin optique interne** |

#### ⇒ CE QUE ÇA SOLDE, ET CE QUE ÇA ROUVRE

🔴 **`dn4-3` avait nommé la MAUVAISE CAUSE** : *« ST impose un chargement de registres privés, et sans
lui la puce may not perform to specification »* était une hypothèse **plausible et bien sourcée** —
**mais fausse**. SR03 se charge parfaitement et **ne change rien**. ⛔ Ce n'était pas un défaut de
raisonnement : c'était **une hypothèse non testée présentée comme une cause**, et il aura fallu
`dn4-7` pour la tester.

✅ **L'hypothèse OWNER — « l'émetteur / l'analogique » — ÉTAIT LA BONNE**, dans une forme plus large
que celle qu'on lui donnait : ⛔ pas seulement le VCSEL, **tout l'étage analogique**.

🎯 **ET LE NOM DU MODULE RÉPOND À AC6 PAR AVANCE** : **`TOF050C` = 50 cm**. Le plafond du registre
étant **255 mm** (§13.20.5), 50 cm ne s'atteint qu'avec un **facteur d'échelle 2×**
(2 × 255 = 510 mm ≈ 50 cm) — et le registre d'échelle `0x0096`/`0x0097` est **dans SR03**, posé à
**1×** (`0x00`/`0xFD`). ⇒ **avec un module SAIN, la story tombe dans la bande « ~50 cm — réveil au
GESTE »**, ⛔ ni le bouton sans contact, ⛔ ni la présence à 2 m.
⚠️ **À VÉRIFIER PAR LA MESURE sur le module de remplacement**, ⛔ pas à écrire comme acquis : c'est
une déduction depuis un nom commercial et une arithmétique de registre.

### 13.21.16 🔴 SECOND DÉFAUT — **LE MODULE EMPÊCHE LA CARTE DE DÉMARRER**, et tout le reste est éliminé

En fin de séance, le module cesse d'être seulement inutile : **il devient nuisible.** Symptôme :
**écran noir, rétroéclairage allumé** = `dn_display_init()` échoue sur le TCA9554 sous
`ESP_ERROR_CHECK` ⇒ panique ⇒ **CPU halté** ⇒ ⛔ **plus d'USB du tout** (piège n°8 du README).
⚠️ **Le défaut est INTERMITTENT** — constat owner : *« ça n'échoue pas systématiquement, quand tu
forces le redémarrage ça se relance »*.

#### 🎯 LA BISSECTION, UNE SEULE VARIABLE, CÂBLAGE VÉRIFIÉ CONTRE LA SÉRIGRAPHIE

| Bras | `touch` | Boot |
|---|---|---|
| **A — ToF DÉBRANCHÉ** (4 fils retirés) | **559 lectures, 0 erreur I²C** | ✅ **2 338 ms**, témoin positif vert |
| **B — ToF REBRANCHÉ**, rangée B | — | 🔴 **panique**, reproduit |

⚠️ **Les QUATRE fils sont retirés au bras A, ⛔ pas seulement `VIN`** : couper l'alimentation en
laissant `SDA`/`SCL` recréerait le **capteur fantôme de §13.10** (alimentation parasite par les
diodes ESD), et le bras « sans » ne prouverait rien.

#### ⛔ QUATRE CAUSES ÉLIMINÉES — chacune par une mesure, ⛔ aucune par raisonnement

| Cause | Comment elle est tombée |
|---|---|
| **Court-circuit** dans le module | 🔴 **ohmmètre, module ISOLÉ** : `SDA`↔`GND` et `SCL`↔`GND` **ouverts**, `VIN`↔`GND` **ouvert**, et `SDA`/`SCL`↔`VIN` = **10 kΩ** — ⚠️ **exactement la valeur mesurée en `dn4-2`** quand il fonctionnait |
| **Erreur de câblage** | vérifié **fil par fil contre la sérigraphie** par l'owner, polarité `3V3`→`VIN` / `G`→`GND` |
| **Vitesse I²C** (400 kHz) | ⛔ **test INVALIDE, voir ci-dessous** |
| 🔴 **LE LOGICIEL** | **firmware du DÉBUT DE SÉANCE reflashé** — et **vérifié PAR SON CONTENU** |

#### 🔴 LE TEST QUI FERME LA PISTE LOGICIELLE — proposé par l'OWNER

Question owner : *« ça serait la config de boot pas bonne ? pourquoi ça marchait avant et plus
maintenant si on regarde que le code ? »* — **légitime, et instruite plutôt qu'écartée.**

**a) Le diff.** Sur toute la séance, **QUATRE fichiers** touchés : `dn_console.c`, `dn_env.c`/`.h`,
`dn_pins.h`. ⇒ 🔴 **`dn_display.c`, `desknode_main.c` et `dn_touch.c` : ZÉRO modification** — or
**c'est là que la panique se produit.** Le chemin de démarrage est **identique à l'octet près**.

**b) Le déroulé, qui ne dépend d'aucune lecture de code.** Le firmware `95d49cb` a démarré des
dizaines de fois avec le ToF branché **avant** le déplacement en rangée A, et panique **après**,
**binaire inchangé**. ⇒ la seule variable est **un geste physique**.

**c) Et le test direct** : les 4 fichiers ramenés à `fff4518`, rebuild, flash.
🎯 **VÉRIFIÉ PAR LE CONTENU, ⛔ PAS PAR L'ÉTIQUETTE** : le bandeau affichait encore `8abed6c` **sans
`-dirty`** (chaîne de version non régénérée — **un label menteur, exactement ce que ce chapitre
traque**). Contrôle réel : **la commande `tof` est ABSENTE de `aide`** ⇒ c'est bien le code d'avant.
⇒ **Résultat : panique identique.** ⛔ **LE LOGICIEL EST ÉLIMINÉ SANS DISCUSSION.**

#### ⚠️ ET UN SIXIÈME DÉFAUT DE MÉTHODE — MON TEST DES 100 kHz NE POUVAIT RIEN MESURER

J'ai fait flasher un firmware ralentissant le VL6180X à **100 kHz** (`8abed6c`) pour tester
l'hypothèse de l'adaptateur de niveau. ⛔ **Ce test est INVALIDE PAR CONSTRUCTION** : la panique se
produit dans `dn_display_init()`, **avant que `dn_env_init()` n'ouvre le device du ToF** — à cet
instant le module **n'a aucun handle et donc aucune horloge**. Le réglage ne s'applique qu'à des
transactions que le boot **n'atteint jamais**.
🔴 **C'est le motif « la garde n'atteint jamais ce qu'elle prétend couvrir »**, et j'allais faire
enchaîner **cinq cycles d'alimentation** à l'owner pour un chiffre sans signification.
⇒ `DN_I2C_FREQ_TOF_HZ = 100 000` reste au dépôt mais **NON VALIDÉ**, et c'est écrit.

#### 🎯 CE QUI RESTE, PAR ÉLIMINATION — et ce que dit l'art antérieur

Défaut **intermittent**, **absent à l'ohmmètre**, **présent dès la mise sous tension**, ⛔ indépendant
du logiciel et du câblage.

⚠️ **Le `TOF050C` accepte `VIN` 3-5 V pour une puce à 2,8 V** ⇒ il porte forcément un **adaptateur de
niveau bidirectionnel** sur `SDA`/`SCL`, et **les 10 kΩ mesurés sont ses tirages hauts**. Un
transistor d'adaptateur affaibli garde son tirage **intact** — l'ohmmètre ne voit rien — mais conduit
mal une fois **polarisé**. **Art antérieur** : un **MOSFET d'adaptateur `SDA` endommagé** est rapporté
sur VL6180X (element14), et un **blocage `SDA` bas après une période de fonctionnement** sur le
VL53L0X, la puce sœur.
⛔ **HYPOTHÈSE, non prouvée** : la mesure qui la trancherait est la **tension sur `SDA`/`SCL` carte
allumée et module branché** (~0 V au lieu de ~3,3 V). ⚠️ **Non faite** — arrêt de séance.

#### 🔴 GARDE NOUVELLE — ⛔ NE PLUS RIEN ALIMENTER DEPUIS `3V3`/`G` DE LA **RANGÉE A**

**DEUXIÈME occurrence** du même symptôme sur ces cavités (la 1ʳᵉ : §13.16.7, `dn4-2`).
🎯 **Et cette fois il n'y a AUCUN fil `XSHUT`** ⇒ ⛔ **le soupçon que `dn4-2` portait sur `XSHUT` est
RÉFUTÉ.** Ce sont **les cavités**, ou ce qu'on y branche. Le mécanisme reste inexpliqué — **deux
occurrences suffisent à interdire l'emplacement sans attendre de le comprendre.**
⚠️ **Et c'est cet épisode qui a précédé la dégradation du module** : il démarrait la carte
normalement avant, plus après. **Corrélation temporelle forte, causalité NON établie.**

⚠️ **MA FAUTE, ÉCRITE** : le risque de la rangée A était **consigné dans ce fichier depuis `dn4-2`**,
et je ne l'ai rappelé à l'owner **qu'APRÈS** son essai — je le lui avais sorti pour le 5 V, ⛔ pas
quand il a déplacé l'alimentation. **La garde existait, je ne l'ai pas jouée au bon moment.**

---

## 13.22 🔴 SÉANCE CARTE `dn4-2` (2026-08-24) — L'EXERCICE DES 34 CORRECTIFS, ET **DEUX RÉFUTATIONS DANS LA MÊME HEURE**

> **Contexte.** La 2ᵉ revue de code 3 couches du 2026-08-24 a porté sur `e931c31..c1a9167` — le
> delta des correctifs produits par la revue du 2026-08-20, **que personne n'avait relu**. Elle a
> rendu **41 constats**, tous corrigés (`f94753e`, `3021f8b`). Cette séance les **exerce**.
>
> ⛔ **CE N'EST PAS UN REJEU DE `dn4-2`, ET C'EST IMPOSSIBLE.** Des trois capteurs que la story a
> qualifiés, **l'INA219 est retiré du bus** (`cc-ina219`) et **le VL6180X est mort** (`dn4-7`,
> `blocked`). **Seul le BH1750 survit** — constat owner du 2026-08-24. Les 7 correctifs hauts
> portent tous sur le BH1750 ou sur des gardes génériques : c'est ce qui rend la séance jouable.
>
> **Firmwares** : `3021f8b` → `2db3c78` → `8a1dac9`, **SHA lu au bandeau à chaque flash**,
> `git status --porcelain` vérifié **vide avant chaque flash**. Bus à **6 devices**.

### 13.22.1 Les sept gestes — ce que la carte a répondu

| # | Geste | Attendu | Mesuré |
|---|---|---|---|
| 1 | `i2c lire 23 00` | la garde crie | ✅ elle crie — et la dernière ligne reste `0x23 reg 0x00 : 00`, **d'apparence parfaitement réussie**. C'est *tout* ce qui sortait avant |
| 2 | `i2c brut 23 2` | le bloc d'hypothèses | ✅ `SUPPOSE Mode1 ET MTreg 69` à chaque lecture · `168 × 100 / 12 = 1400` ⇒ **`140.0`** ✓ |
| 3 | `i2c ecrire 23 11` | Mode2 **+** 180 ms | ✅ **les deux**. Avant : *« opcode NON REPERTORIE »*, **zéro** avertissement |
| 4 | `i2c lire 6B D0` | plus de verdict BME | ✅ `0x6B reg 0xD0 : 00` **et rien d'autre** |
| 5 | `i2c ecrire 23 00` | avertissement **avant** l'écriture | ✅ il précède `0x23 <- 00` |
| 6 | `i2c lire16 0x29 0000` | refusé | ✅ `adresse « 0x29 » refusee` |
| 6b | `i2c lire 77 D0` (**témoin positif**) | l'usage légitime intact | ✅ garde d'occupant + `61` + `chip id 0x61 = BME680` — la garde d'adresse **n'a pas cassé** le verdict là où il est juste |
| 7 | `i2c rafale` | `vus ≤ passes` | ✅ `518/524` et `1298/1308` — l'ancien code pouvait rendre `1301/1300` |

### 13.22.2 Le facteur 2 du Mode2 — **prouvé, pas affirmé**

| Mode | brut | moyenne |
|---|---|---|
| **Mode2** (`0x11`) | `482` · `550` | **516** |
| **Mode1** (`0x10`) | `287` · `281` | **284** |

⇒ **×1,82** pour un ×2 théorique, sous une lumière **non contrôlée et qui dérivait** (elle est
passée de `250` à `389` en trois lectures plus tôt dans la séance). ✅ Le facteur 2 est établi ;
⛔ l'écart à 2,00 n'est **pas** mesuré, il est attribué à la dérive — **non isolé**.

### 13.22.3 🔴 LE RE-RELEVÉ QU'IMPOSAIT LA RÈGLE « INSTRUMENT MODIFIÉ ⇒ CHIFFRES MORTS »

Le témoin de `i2c rafale` comptait la passe tronquée au **numérateur** et l'excluait du
**dénominateur** ⇒ **les deux taux de faux négatifs publiés par AC9 sont morts.**

| | publié §13.17.6 (**mort**) | re-mesuré 2026-08-24, 25 s |
|---|---|---|
| `0x20` TCA9554 | 1,52 % (20/1320) | **0,76 %** (10/1308) |
| `0x5D` GT911 | 1,67 % (22/1320) | **0,31 %** (4/1308) |
| cadence | 5 916 sondages/s | **5 862** sondages/s |
| fenêtre 10 s (contrôle) | — | `0x20` **1,15 %** (6/524) · `0x5D` **0,57 %** (3/524) |

⛔ **CE N'EST PAS UNE CORRECTION DES ANCIENS CHIFFRES, C'EST UNE MESURE NEUVE.** Le bus est passé
de **8 à 6 devices** et le firmware n'est pas le même : les deux séries **ne sont pas comparables**.
**Les deux restent écrites.** ⚠️ Le témoin « en échec » (il exige 100 %) s'affiche toujours — c'est
le défaut **déjà déclaré** le 2026-08-20, ⛔ pas un constat neuf.

### 13.22.4 🔴 LE CONSTAT NEUF — **UN BH1750 ÉTEINT NE REND PAS `00 00`**

| État | trois lectures consécutives |
|---|---|
| **éteint** (`i2c lire 23 00`) | `211` · `211` · `211` — **FIGÉ** |
| **rallumé** (`01` puis `10`) | `250` · `280` · `389` — **dérive** |

Le registre de données **n'est pas vidé** par le power down. ⇒ **Le symptôme d'un capteur éteint
est une VALEUR PLAUSIBLE QUI NE BOUGE PLUS**, ce qui est **pire qu'un zéro** : ça passe pour une
mesure.

> 🔴 **ET ÇA CASSE LE CRITÈRE DE PREUVE DE §13.16.8.** Ce critère est *« 3 lectures, identiques »*.
> Il est **satisfait par un capteur éteint** — et aussi par un **bus qui lit des uns** (la garde
> `FFFF` posée la veille décrit déjà ce second cas). ⇒ **« TROIS LECTURES IDENTIQUES » N'EST PAS
> UNE PREUVE DE VIE, dans aucun des deux sens.** Le seul discriminant est une valeur qui **CHANGE**
> sous stimulus. ⚠️ Et l'inverse n'est pas vrai non plus : trois lectures identiques sous une
> lumière **stable** sont normales — mesuré dans cette même séance (`207` × 3, capteur vivant).

### 13.22.5 ⚠️ DEUX RÉFUTATIONS DE MES PROPRES CORRECTIFS, DANS LA MÊME HEURE

1. **L'avertissement destructeur, écrit le matin même**, affirmait *« après lui, `i2c brut 23 2`
   rendra `00 00` »*. **Mesuré faux** (§13.22.4). Corrigé — `2db3c78`.
2. **La correction de (1) en a écrit une seconde, non mesurée** : *« le reset `0x07`, lui, rend
   `00 00` »*. **Mesuré faux aussi.**

| Condition | `i2c ecrire 23 07` | lecture après |
|---|---|---|
| capteur **éteint** | **ignoré** — datasheet ROHM : le reset **n'est pas accepté** en power down | `209`, **figé** |
| capteur **alimenté** | accepté | **`00 00`** |

⚠️ **La puce ACQUITTE dans les deux cas** — ce que la ligne *« acquitte ne veut pas dire a obei »*
annonçait déjà deux lignes plus bas, sans que je l'applique à mon propre texte. Corrigé — `8a1dac9`.

> 🎯 **LA LEÇON DE MÉTHODE, ÉCRITE PARCE QU'ELLE VAUT AU-DELÀ DE CE TEXTE : UNE CORRECTION N'EST PAS
> UNE MESURE.** En corrigeant une affirmation non mesurée, j'en ai écrit une seconde, non mesurée,
> **dans le même geste**. Elle était **plausible** (*« reset ⇒ registre vide »*) et elle était
> **fausse**. Les deux n'ont été trouvées que **parce que le geste a été joué sur la carte**.

### 13.22.6 Non-régression, et l'état où la séance laisse la carte

- **Boot propre** sur les trois firmwares : `prêt en 2 348 / 2 349 / 2 350 ms`, aucune panique,
  `BME680 pret @ 0x77`, `dn_env pret — 2/3 devices ouverts`, asset **CRC32 `0x0F027C7D` vérifié**.
- ✅ **Constat owner sur `8a1dac9`** (2026-08-24, après **trois** flashs et **cinq** cycles
  d'extinction du luxmètre) : **grille complète, six cases, rétroéclairage fixe, rien d'anormal.**
  ⚠️ **Recueilli par question fermée, ⛔ pas un verbatim libre** — c'est bien l'œil de l'owner sur le
  livrable, et c'est ce qui manquait à AC13 ; ce n'est pas une citation.
- **Capteur restauré** : `01` + `10`, et les deux lecteurs s'accordent — console `209`,
  `dn_env` `174 lx (brut 209)`.
- ⚠️ **Transitoire observé et expliqué** : juste après un reset, `env` a publié `0 lx (brut 0)`
  pendant que la console lisait `207`. C'est le registre attrapé **entre le reset et la conversion
  suivante** — exactement le cas *« mesure pas encore prête »* dont l'instrument avertit. ⛔ Pas un
  défaut ; produit **involontairement**, et gardé ici parce qu'il **valide l'avertissement**.


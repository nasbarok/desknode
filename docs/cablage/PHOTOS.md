# Les photos de câblage — ce que chacune établit, ce qu'elle pèse, et ce que l'alléger a coûté

Ce dossier porte les **20 photographies** qui servent de **base probante** au câblage de DeskNode :
les sérigraphies, les états soudés, les pièges d'embase, et le montage final. Cette page est leur
**index**. Elle dit, pour chacune, **ce qu'elle établit**, **qui la cite**, et **ce qu'elle pèse
avant et après** la curation du **2026-09-07**.

🔴 **Elle publie aussi le prix de cette curation, et il est POSITIF.** L'historique de ce dépôt
ne se réécrit jamais : git garde les images d'origine. Alléger une photo **n'enlève donc rien à un
clone, ça lui AJOUTE**. Le gain est réel — il est sur **l'arbre de travail** et sur la **lecture en
ligne** — mais il **se paie sur le clone**, et ce prix est écrit ci-dessous plutôt que tu.

---

## 1. Le bilan, en octets

### Ce que la curation a RENDU — l'arbre de travail

| grandeur | avant (T0) | après (T7) |
|---|---:|---:|
| fichiers dans `docs/cablage/` | **20** | **20** |
| poids de `docs/cablage/` | **27 860 048** octets | **15 762 150** octets |
| la plus grosse photo | **5 071 848** octets | **2 708 418** octets |

⇒ l'arbre de travail **rend 12 097 898 octets**, soit **43,42 %** du dossier.
⇒ **0 photo retirée**, **0 photo renommée**, **0 définition modifiée**.

### 🔴 Ce que cette curation N'A PAS allégé — le clone

La question n'est pas rhétorique : c'est celle qu'un lecteur pose en voyant « 28 Mo de photos ».
La réponse **se mesure**, elle ne se raisonne pas. L'instrument est le **bundle**, qui est
exactement ce qu'un clone transporte.

⚠️ **La colonne « après » n'est ⛔ PAS `main` : `main` n'a jamais pesé ce nombre.** C'est le bundle
d'un commit de **mesure**, posé sur la baseline et ne portant **que les 11 photos recompressées** —
⛔ ni cette page, ⛔ ni la gate, ⛔ ni les relevés. C'est ce que *« ce que la **curation** a fait au
poids du clone »* veut dire. Le commit de mesure est un objet jetable : aucune branche publiée n'y
mène, et il est supprimé après relevé.

| ce que transporte un clone | avant (T0) | après (T7) |
|---|---:|---:|
| bundle de l'historique — `main` à la baseline, puis la **curation seule** posée dessus | **33 548 491** octets | **43 713 244** octets |

⇒ le clone **COÛTE 10 164 753 octets de plus**, soit **+30,30 %**.

**Lis les deux lignes ensemble** : pendant que l'arbre de travail baisse de 43 %, le clone **monte
de 30 %**. Les onze images recompressées sont **onze objets de plus**, et les onze originaux
**restent** — ils sont atteignables depuis chaque commit qui les portait. ⛔ Ce n'est pas un défaut
de la curation : c'est ce que « ⛔ ne jamais réécrire l'historique » **coûte**, écrit une fois pour
toutes avec son chiffre.

⚠️ **La mesure a un bruit, et il est déclaré.** `git bundle create` n'est **pas déterministe** par
défaut : cinq passes consécutives sur le même commit, arbre inchangé, rendent des tailles étalées
sur **202 306 octets** (0,60 %) — c'est la delta-compression **multi-thread**. Les deux nombres
ci-dessus sont donc pris à `pack.threads=1`, qui est **reproductible à l'octet** (trois passes
identiques). Le bruit reste **cinquante fois plus petit** que l'écart mesuré, donc la conclusion
n'en dépend pas ; le **nombre**, si.

⚠️ **Ce nombre est reproductible SOUS CONDITIONS, et les conditions s'écrivent — ⛔ ce n'est pas
une garantie « à l'octet ».** Un bundle contient l'objet commit *et* le nom de la ref : **quatre**
variables déplacent donc le total de quelques octets — le **message** de commit, les **dates**,
l'**identité** de l'auteur, et le **nom de la ref**. Mesuré : une ref nommée autrement change le
total de **7 octets**, une identité plus longue de **2**. ⇒ la recette de
[`T7-etat-arrivee.txt`](../../mesures/dn6-3/T7-etat-arrivee.txt) §2 les **fixe toutes les quatre**,
et rend alors **43 713 244** sur trois passes identiques ; elle ajoute `docs/cablage/*.jpg`,
⛔ **pas** `docs/cablage`, qui emporterait cette page-ci.
✅ **La conclusion, elle, ne dépend d'aucun de ces octets** : l'ordre de grandeur est 10⁷, la
sensibilité 10¹. **+10,16 Mo** et **+30 %** survivent à n'importe laquelle de ces variations.

Relevé complet : [`T7-etat-arrivee.txt`](../../mesures/dn6-3/T7-etat-arrivee.txt) et
[`T0-etat-depart.txt`](../../mesures/dn6-3/T0-etat-depart.txt).

---

## 2. Ce qui a été fait aux fichiers, et ce qui ⛔ ne l'a PAS été

**Onze photos** étaient encodées à une qualité JPEG **≥ 90**. Elles ont été **recompressées en
place à la qualité 88**, ⛔ **sans être redimensionnées**, **EXIF conservé**.

🔴 **88 n'est pas un réglage inventé : c'est celui du dépôt.** Les sept photos du 2026-08-20 y sont
déjà — l'owner les avait traitées lui-même, et
[`ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md`](../../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)
§13.0 déclare l'arbitrage assumé. Cette passe **étend** ce réglage, elle ⛔ n'en choisit pas un
nouveau.

**Chaque fichier produit a été vérifié AVANT de remplacer son original**, sur cinq conditions :
définition identique en pixels · même nombre de tags EXIF · même horodatage EXIF · **PSNR ≥ 38 dB** ·
fichier réellement plus léger. Une photo qui rate l'une des cinq **n'est pas remplacée** et le motif
s'écrit. Mesure : **0 refus sur 11**.

**La perte est bornée par un nombre**, ⛔ pas par un avis : le **PSNR minimum est de 39,90 dB**
(sur `2026-08-17_0012-breakout-ecarte-barrette-inseree.jpg`, la plus grosse) ; les dix autres sont
entre **45,67 et 49,81 dB**. Photo par photo :
[`T3-psnr-exif-photo-par-photo.txt`](../../mesures/dn6-3/T3-psnr-exif-photo-par-photo.txt).

**Ce qui ⛔ n'a PAS été touché** : les neuf autres photos sont **octet pour octet** celles d'avant
(sept déjà à qualité 88 et 2 600 px, deux déjà à qualité 75/76).

---

## 3. 🔴 Les deux questions qui appartenaient à l'owner — TRANCHÉES le 2026-09-07

### ✅ Le verdict d'observation est RENDU — 2026-09-07, à l'œil de l'owner

**La sérigraphie est LISIBLE après recompression.** C'est le seul contrôle qu'⛔ aucune gate ne
peut rendre, et il est **fait** : ⛔ plus une supposition. La recompression à Q88 est donc validée
**sur le critère qui décide**, ⛔ pas seulement sur le PSNR qui la borne.

### 🔴 ET LE MÊME REGARD A OUVERT AUTRE CHOSE — ces photos sont un CHANTIER, ⛔ pas une publication

Constat owner, même séance, **verbatim** : *« c'est lisible mais si on veut les exploiter il faudra
faire quelques recadrages car c'était seulement des images pour la construction. Pas forcément
intéressant de publier tout ça. »*

⇒ **Il y a DEUX usages, et ils n'ont ⛔ pas les mêmes exigences** :

| usage | ce qu'il demande | état |
|---|---|---|
| **PREUVE** — établir une sérigraphie, une adresse, un état soudé | que le détail soit **lisible** | ✅ **tenu** — c'est le rôle que ces photos remplissent dans le journal de mesure et dans la page de câblage |
| **VITRINE** — montrer le montage à quelqu'un qui découvre | des images **cadrées et choisies** | ⛔ **n'existe pas** — ces vingt-là sont des prises de chantier |

⚠️ **Et cette page a AUGMENTÉ l'exposition, c'est écrit plutôt que tu.** Avant elle, **11 des 20
photos n'étaient citées que par le journal de mesure** — un dossier de séance assumé comme tel.
Elles sont maintenant indexées dans `docs/`, que `LICENSING.md` déclare *« documentation lecteur »*.
Ce déplacement est un **effet de cette marche**, ⛔ pas une intention de l'owner.

⛔ **Rien n'est publié pour autant, et c'est ce qui rend la question NON URGENTE** : le dépôt est
`PRIVATE` (garde-fou `NFR6.2`), donc il n'existe aujourd'hui **aucun inconnu** pour voir ces photos.
La question devient réelle **à la bascule publique**, ⛔ pas avant — et c'est un **DÉCLENCHEUR DE
RÉÉVALUATION**, ⛔ pas une échéance : si la bascule n'a pas lieu, elle ne se repose pas.

⚠️ **ANNOTÉ LE 2026-09-15 (`dn8-8`) — LE DÉCLENCHEUR A JOUÉ, ET LA RÉPONSE EST ÉCRITE.** Le dépôt
est **public** depuis ce jour. Juste avant la bascule, l'owner a répondu à la question « l'historique
part-il tel quel ? » : *« oui »* (2026-09-14). Ces photos deviennent donc publiques **telles
quelles**, dans l'arbre comme dans l'historique — ⛔ sans recadrage, ⛔ sans retrait. L'usage VITRINE,
lui, n'existe toujours pas, et le porteur proposé ci-dessous reste une proposition.
🔬 **Ce qu'elles emportent en plus de l'image, mesuré avant la bascule** (relevé
`mesures/dn8-8/T1-releve-de-ce-qui-devient-public.txt`, 2026-09-15) : l'historique poussé atteint
**33 versions de JPEG**, sur 22 chemins. `T1` compte **séparément** les versions qui portent **à la
fois** la marque et le modèle de l'appareil dans leurs EXIF — **29** — et celles qui portent **au
moins l'un des deux** — **29** aussi. **29** portent la date de **modification** du fichier
(étiquette `0x0132`, ⛔ la date de prise de vue) et **31** une date de **prise de vue**
(`DateTimeOriginal`) ; **31** nomment le logiciel qui les a écrites, et **29** portent une vignette
(l'image réduite de l'IFD1). **7** portent une entrée de commentaire utilisateur, **vide** dans les
7 cas. Parmi les **étiquettes standard lues**, **0** portent un auteur, un copyright, un propriétaire
ou un numéro de série de l'appareil ; mais **7** portent un bloc propriétaire du constructeur
(`MakerNote`), **⛔ décodé par personne** : ce qu'il contient — un numéro de série, par exemple —
n'est ni lu ni compté ici. **0** portent un paquet XMP, et **0** une position GPS.

🎯 **Porteur proposé : l'epic vitrine** — elle doit **déjà** re-tourner le média une fois le boîtier
posé (réserve mesurée : *« le câblage est à nu dans le cadre »*). Recadrer, choisir, et re-tourner
sont **le même geste, au même moment** : les séparer, c'est cadrer deux fois. ⛔ Ce n'est pas
tranché ici — c'est **écrit pour que ça ne se reperde pas**.


### 🔴 Faut-il aussi réduire la définition ? — NON, et le motif vient du constat ci-dessus

**La marche l'avait chiffrée et POSÉE ; elle est désormais TRANCHÉE — et par un argument que le
cadrage ⛔ n'avait pas.** Décision owner du 2026-09-07 : **on ne redimensionne pas.**

🎯 **Le motif : un recadrage MANGE de la définition.** Recadrer, c'est ne garder qu'une **portion**
de l'image ; ce qui reste après coup, c'est la définition d'origine **moins** ce qu'on a coupé. Or
le constat owner ci-dessus dit que ces photos devront être **recadrées** pour être exploitables.
⇒ les **3072×4096** conservés ne sont ⛔ pas de la matière dormante : ils sont **la marge du
recadrage à venir**. Réduire à 2 600 px maintenant économiserait 5 210 987 octets et **dépenserait
cette marge** — pour un travail qui n'a même pas encore commencé.

⚠️ **Ce n'est ⛔ pas le raisonnement qui a produit la décision de livraison.** Le cadrage avait
retenu la recompression seule parce que c'est la voie dont **la perte est bornée par un nombre**
(PSNR ≥ 39,90 dB, définition intacte), et il **posait** le redimensionnement à l'owner faute de
pouvoir juger une sérigraphie. Le motif du recadrage est arrivé **après**, avec le regard de
l'owner. ⇒ la bonne option a été livrée **avant** que sa meilleure raison ne soit connue : ⛔ ce
n'est pas de la prévoyance, et l'écrire autrement serait se donner le beau rôle.

**Les deux options restent chiffrées ci-dessous** (`NFR3` : annoter, ⛔ pas effacer) — la seconde
n'est ⛔ pas réfutée, elle **n'est pas retenue**, et son motif est écrit.

| option | poids de `docs/cablage/` | bundle | ajouté au clone | définition des 11 |
|---|---:|---:|---:|---|
| recompression seule — **ce qui est livré** | **15 762 150** octets | **43 713 244** octets | **+10 164 753** octets | inchangée (3072×4096 / 4096×3072) |
| recompression **+ 2 600 px de côté long** — ⛔ **NON RETENUE** (elle dépenserait la marge du recadrage) | **10 551 163** octets | **38 506 885** octets | **+4 958 394** octets | 1950×2600 / 2600×1950 |

Les deux bundles sont pris par la **même** méthode et le **même** réglage que ceux du §1 (variante
mesurée sans toucher l'arbre de travail : les onze fichiers redimensionnés sont écrits en objets
git, puis posés dans un index temporaire).

Le redimensionnement rendrait **5 210 987 octets de plus** sur l'arbre et coûterait **5 206 359
octets de moins** au clone : il est meilleur **sur les deux tableaux chiffrés**. Il perd sur le seul
qui décide, et qui ⛔ ne se calcule pas : **la sérigraphie reste-t-elle lisible ?** Sur les photos du 2026-08-19, la sérigraphie **est la
pièce** — c'est elle qui a réfuté l'étiquette d'un capteur portée par six stories. Un facteur 0,635
linéaire sur un gros plan de sérigraphie **se juge à l'œil**, en trois secondes, par la personne qui
soudera.

✅ **Et le contrôle « à l'œil » de ce qui est LIVRÉ a été RENDU** — verdict du 2026-09-07, en tête de
section : *« c'est lisible »*. ⛔ Aucune gate ne sait dire si une sérigraphie reste lisible ; c'est
un **geste humain** qui l'a tranché, et la ligne ci-dessous est **conservée** parce qu'elle dit
**quelles photos regarder** si la question se repose. Les deux à regarder en premier sont
[`2026-08-17_0012-breakout-ecarte-barrette-inseree.jpg`](2026-08-17_0012-breakout-ecarte-barrette-inseree.jpg)
(PSNR le plus bas) et
[`2026-08-19_1720-bh1750-gy302-face-composants-serigraphie-v322.jpg`](2026-08-19_1720-bh1750-gy302-face-composants-serigraphie-v322.jpg)
(la sérigraphie de révision). ⛔ Cette page le **déclare** au lieu de le supposer acquis.

---

## 4. Les photos RETIRÉES — la liste est VIDE, et voici son motif

**Aucune photo n'a été retirée.** ⛔ Ce n'est pas une case cochée sur du vide : **trois mesures**
ferment la question.

1. **Le critère de retrait est l'orphelinat**, et il n'est rempli par personne : **0 photo orpheline
   sur 20** — chacune est citée par au moins un document du dépôt. Carte complète :
   [`T1-carte-des-citations.txt`](../../mesures/dn6-3/T1-carte-des-citations.txt).
2. **Onze photos sur vingt ne sont citées que par le journal de mesure**
   ([`ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md`](../../hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md)),
   un fichier que cette marche a **interdiction d'écrire**. En supprimer une poserait un **lien mort
   dans un fichier qu'elle n'aurait pas le droit de réparer**.
3. **Sur le clone, supprimer et recompresser font la même chose — rien.** Les blobs d'origine
   restent dans l'historique dans les deux cas.

⇒ **recompresser, retirer zéro.** La ligne du dessous existe pour qu'un futur retrait ait un endroit
où écrire son motif.

| photo retirée | date | motif écrit |
|---|---|---|
| *(aucune)* | — | *(sans objet — 0 orpheline sur 20 au 2026-09-07)* |

---

## 5. 🔴 Un écart DÉCLARÉ, ⛔ pas réparé : deux photos ont déjà perdu leur EXIF

Le journal de mesure affirme que ces photos *« sont nommées par leur horodatage EXIF »*, et il
publie l'horodatage de chacune — c'est donc une **pièce**, ⛔ pas une métadonnée.

Or **deux fichiers ne portent plus que 2 tags EXIF, et aucun horodatage** :

| photo | ce que le journal publie | ce que le fichier porte |
|---|---|---|
| `2026-08-16_2140-bme680-recto-barrette-non-soudee.jpg` | `21:40:12` | **2 tags, ⛔ aucun horodatage** |
| `2026-08-16_2228-carte-embases-jst-jumelles-i2c-uart.jpg` | `22:28:41` | **2 tags, ⛔ aucun horodatage** |

Ce sont exactement les deux **déjà recompressées avant cette marche** (qualité 75 et 76). **Une passe
d'allègement antérieure a effacé la pièce, et aucune gate ne l'avait vu.** C'est la faute que cette
marche pouvait commettre **onze fois de plus** — d'où la vérification **fichier par fichier avant
remplacement**, et d'où la gate.

⛔ **Cette marche ne le répare pas** : les originaux ne sont pas au dépôt, ils sont chez l'owner.
**Porteur de la réparation : l'owner**, qui seul détient les fichiers d'origine. L'écart est écrit
ici pour qu'il ne se reperde pas.

---

## 6. L'index des 20 photos

Les tailles sont en **octets**. La colonne *tags EXIF IFD0* compte les entrées du **premier IFD
seul** — ⛔ pas les sous-IFD (`ExifIFD`, `Interop`, `GPS`) : un outil qui les additionne rend un
nombre plus grand, et **ce n'est pas celui-ci**. La colonne *qui la cite* liste les fichiers du
dépôt qui nomment la photo — **cette page en est exclue**, sinon elle se citerait elle-même et la
question « cette photo sert-elle à quelque chose ? » n'aurait plus de réponse.

| photo | ce qu'elle établit | qui la cite | définition | tags EXIF IFD0 | T0 octets | T7 octets |
|---|---|---|---|---|---:|---:|
| `2026-08-16_2140-bme680-recto-barrette-non-soudee.jpg` | Le BME680 **face composants** : sérigraphie `VCC GND SCL SDA SDO CS`, et la barrette 6 broches **fournie NON SOUDÉE** posée à côté. L'inventaire de départ. | `journal-de-bord.md` · `cablage.md` · `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 4096x3072 | 2 | 423574 | 423574 |
| `2026-08-16_2228-carte-embases-jst-jumelles-i2c-uart.jpg` | 🔴 **Les DEUX embases JST jumelles**, sérigraphies lisibles (`GND 3V3 SDA SCL` et `GND 3V3 TXD RXD`) : la preuve du piège d'embase, et le header 2×12 soudé. | `cablage.md` · `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 3072x4096 | 2 | 833103 | 833103 |
| `2026-08-17_0012-breakout-ecarte-barrette-inseree.jpg` | Gros plan du breakout **écarté de la carte**, barrette insérée dans ses trous, bloc Dupont enfiché. C'était **le plus gros fichier de l'arbre** à T0. | `CONTRIBUTING.md` · `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 3072x4096 | 19 | 5071848 | 2708418 |
| `2026-08-17_0012-cablage-4-fils-sous-tension.jpg` | Le montage **4 fils SOUS TENSION** : JST sur la bonne embase, wattmètre en ligne, breakout écarté de la carte. | `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 3072x4096 | 19 | 2493891 | 1302753 |
| `2026-08-19_1718-tof050c-vl6180x-face-capteur-et-sachet-2.jpg` | Seconde prise du même cadrage : la sérigraphie `TOF050C-VL6180X` est lisible **sur le cuivre**, pas seulement sur le sachet. | `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 3072x4096 | 19 | 1804073 | 797453 |
| `2026-08-19_1718-tof050c-vl6180x-face-capteur-et-sachet.jpg` | 🔴 **La pièce qui a réfuté l'ancienne étiquette du capteur de distance**, portée par six stories : l'étiquette du sachet, `TOF050C-VL6180X`, et la face capteur du module. | `dn4-15-arbitrage.md` · `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 3072x4096 | 19 | 1812234 | 809079 |
| `2026-08-19_1719-ina219-cjmcu-recto-cavaliers-a0-a1-shunt-r100.jpg` | 🔴 **Le recto de l'INA219** : les cavaliers `A0`/`A1` **visiblement non pontés** — ce qui décide de son adresse — et le shunt `R100`. | `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 4096x3072 | 19 | 1673229 | 722457 |
| `2026-08-19_1719-tof050c-vl6180x-face-broches-deux-barrettes.jpg` | La face broches en gros plan, **deux barrettes non soudées** posées à côté : l'état de départ de la soudure. | `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 3072x4096 | 19 | 1589895 | 647535 |
| `2026-08-19_1719-tof050c-vl6180x-face-broches-et-sachet.jpg` | 🔴 **Le verso du ToF** : `VIN GND SDA SCL INT XSHUT` — **six** broches, dont deux qui ne sont **pas** des signaux de bus et qui décident si la puce répond. | `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 3072x4096 | 19 | 1754508 | 775952 |
| `2026-08-19_1720-bh1750-gy302-face-broches-vcc-gnd-scl-sda-addr.jpg` | 🔴 **Le verso du BH1750** : `VCC GND SCL SDA ADDR` — **cinq** broches, la cinquième étant une **sélection d'adresse**, pas un signal de bus. | `journal-de-bord.md` · `cablage.md` · `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 4096x3072 | 19 | 1584600 | 675966 |
| `2026-08-19_1720-bh1750-gy302-face-composants-et-sachet.jpg` | L'étiquette du sachet : la variante est **`GY-302`**, ⛔ pas `GY-30`. Barrette 5 broches fournie non soudée. | `journal-de-bord.md` · `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 4096x3072 | 19 | 1581285 | 688734 |
| `2026-08-19_1720-bh1750-gy302-face-composants-serigraphie-v322.jpg` | La face composants du BH1750 : sérigraphie **`BH1750`** et **révision `V322`**. ⚠️ Les marquages des passifs n'y sont **pas** lisibles. | `journal-de-bord.md` · `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 4096x3072 | 19 | 1613886 | 719054 |
| `2026-08-19_1720-ina219-cjmcu-verso-caracteristiques.jpg` | Le verso de l'INA219 : `VCC/LOGIC: 3~5V` ⇒ **compatible 3V3**, aucun adaptateur de niveau nécessaire. | `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 4096x3072 | 19 | 1693321 | 727471 |
| `2026-08-20_0038-derivation-premier-pin-deux-fils-soudes.jpg` | Le **geste** de la dérivation : deux fils soudés à l'arrière d'un **même pin mâle**. C'est ce qui remplace une plaque à pastilles. | `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 2600x1733 | 12 | 437948 | 437948 |
| `2026-08-20_0058-derivation-quatre-cables-en-cours.jpg` | Les **quatre câbles en cours** : on y compte les fils convergents de chaque faisceau. | `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 2600x1733 | 12 | 611092 | 611092 |
| `2026-08-20_0110-derivation-quatre-cables-finis-gaines.jpg` | Les **quatre câbles terminés et gainés**, pin mâle en bout ⇒ la topologie en Y est **photographiée**. | `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 2600x1733 | 12 | 491132 | 491132 |
| `2026-08-20_0116-bh1750-et-ina219-barrettes-SOUDEES.jpg` | 🔴 **La première photo d'un état SOUDÉ du dépôt** : BH1750 barrette 5 broches soudée, INA219 barrette 6 broches **et** bornier soudés. | `journal-de-bord.md` · `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 2600x1733 | 12 | 534977 | 534977 |
| `2026-08-20_0116-ina219-et-tof050c-barrettes-SOUDEES.jpg` | Le **ToF soudé** : la référence `TOF050C-VL6180X` est lisible **sur la photo de l'état soudé**, pas seulement sur celle du sachet. | `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 2600x1733 | 12 | 602035 | 602035 |
| `2026-08-20_0951-montage-final-8-devices-grille-six-cases.jpg` | 🔴 **Le montage final, et l'écran est lisible** : les six cases, les libellés, le bandeau. Le bus porte alors **huit devices**. | `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 2600x1733 | 12 | 622912 | 622912 |
| `2026-08-20_0951-montage-final-en-main-les-quatre-modules.jpg` | Le montage complet **en main, à l'échelle** : les quatre modules autour de la carte ⇒ le bus a **deux points d'entrée physiques**. | `journal-de-bord.md` · `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` | 2600x1733 | 12 | 630505 | 630505 |

⚠️ **La plupart de ces citations ne sont ⛔ PAS des liens : ce sont des noms nus entre accents
graves, dans les tables du journal de mesure.** Mesuré le 2026-09-07 : **8 photos sur 20** sont
citées quelque part sous la forme d'un chemin `docs/cablage/…` ; les **12 autres ne le sont
JAMAIS**. Un contrôle ancré sur le chemin déclarerait donc **12 orphelines** sur des photos
parfaitement citées — un « tout va bien » sur une population fausse. C'est pour ça que la gate
cherche le **nom de fichier**, ⛔ pas le chemin.

---

## 7. Comment ces nombres se re-mesurent

⛔ Aucun chiffre de cette page n'est à croire sur parole : ils sont **rejoués à chaque passe de
gates** et confrontés à l'arbre, fichier par fichier.

```
python3 tools/verif_photos_dn63.py                 # le verdict : n OK, 0 KO
python3 tools/verif_photos_dn63.py --liste-mutants  # ce que chaque mutant replante
```

Ce que cette gate garde : que **toute photo du dossier est citée** quelque part — le sens que
**personne** ne gardait — et que **toute citation résout** ; que les **tailles**, **définitions** et
**comptes de tags EXIF** publiés ci-dessus **égalent l'arbre**, y compris les **trois chiffres
d'ouverture** du §1 ; que la **définition en pixels** égale une borne **épinglée dans la gate**, ⛔
pas ce que cette page dit d'elle-même ; que le **bilan T0 → T7** est arithmétiquement juste ; que
cette page **déclare le coût sur le clone** au lieu d'annoncer un gain seul ; qu'elle est **liée**
par une autre page ; que le dossier ne porte **ni fichier non suivi ni format illisible** ; et que
les chiffres que [`CONTRIBUTING.md`](../../CONTRIBUTING.md) **republie** sont bien **les mêmes** —
republier un nombre ⛔ n'est pas le re-mesurer.

⛔ **Ce qu'elle ne fait pas** : elle ne juge **aucune** qualité d'image. Elle ne sait pas si une
sérigraphie est lisible — ça, c'est l'œil de l'owner, et c'est écrit au §3 plutôt que supposé.

---

## Licence

Cette page est de la documentation, comme les photographies qu'elle indexe : **CC-BY-SA-4.0**.
Voir [LICENSING.md](../../LICENSING.md).

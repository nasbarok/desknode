# Ce qu'il faut acheter pour construire un DeskNode

Cette page dit **quoi commander**, **à quel palier**, et **combien ça coûtait le jour où on a
regardé**. Elle est écrite pour quelqu'un qui n'a jamais vu ce projet.

⚠️ **Ce qu'elle ne promet pas** : aucun prix ici n'est garanti. Ce sont des relevés **datés**, faits
sur des places de marché où les prix bougent sans préavis. **Un prix sans sa date ne vaut rien** —
c'est pour ça qu'ils portent tous la leur.

---

## Les deux paliers

Ce sont les mêmes deux paliers que le [README](../README.md) — mêmes noms, ⛔ pas des synonymes.

| Palier | Ce que tu construis |
|---|---|
| **DeskNode** | la carte, seule. ⛔ Ce n'est **pas** un mode dégradé : c'est une configuration valide et gardée. |
| **DeskNode + Ambiance** | la même carte, **plus deux capteurs** soudés sur le header I²C. |

---

## Palier « DeskNode » — la carte seule

| Désignation | Référence exacte | Qté | Fournisseur | Prix | Date du relevé | Source |
|---|---|---|---|---|---|---|
| Carte de développement écran tactile | **Waveshare ESP32-S3-Touch-LCD-2.8B** (Type B, **480 × 640**) | 1 | place de marché AliExpress | **26,77 – 27,88 €** (médiane **27,32 €**, 2 annonces) | 2026-09-06 | `https://www.aliexpress.com/w/wholesale-Waveshare-ESP32-S3-Touch-LCD-2.8B.html` |
| Câble USB-C données | quelconque, **données ET charge** | 1 | — | ⛔ **non relevé** — consommable générique, aucune référence unique à commander : ⛔ aucune source n'a donc été tentée | — | — |

⛔ **Prix fabricant non relevable.** `https://www.waveshare.com/esp32-s3-touch-lcd-2.8b.htm` rend
**HTTP 403** à toute récupération automatisée (tenté le 2026-09-06). Le dossier matériel écrit déjà
la même chose du wiki officiel. ⇒ le prix ci-dessus vient d'une **place de marché**, ⛔ pas du
fabricant, et c'est écrit plutôt que tu.

### 🔴 L'erreur d'achat la plus probable — et elle coûte moins cher que la bonne

Waveshare vend **plusieurs cartes qui portent presque le même nom**. Relevé le 2026-09-06, **sur la
même page de résultats** :

<!-- ⛔ PAS UNE TABLE DE BOM : table de COMPARAISON. Elle porte deux prix pour
     montrer que la mauvaise carte est la moins chère — ⛔ elle ne propose rien
     à l'achat, et les deux prix sont datés dans la phrase qui la précède. -->

| Ce que tu veux | Ce que tu risques de prendre |
|---|---|
| `ESP32-S3-Touch-LCD-2.8**B**` — **480 × 640**, Type B — **26,77 €** | `ESP32-S3-Touch-LCD-2.8` — **240 × 320** — **23,08 €** |

⇒ **la mauvaise carte est la moins chère**, de 3,69 €. Quelqu'un qui trie par prix croissant prend
la mauvaise. Il existe aussi une `2.8C` ronde en 480 × 480 — ⛔ **relevée nulle part ici** : aucune annonce la nommant n'a été ouverte le 2026-09-06, donc ⛔ ni prix, ni source. C'est écrit pour que tu l'écartes, ⛔ pas pour la comparer.

**Ce qui tranche, c'est la résolution : 480 × 640.** Si l'annonce ne l'écrit pas, ⛔ ne l'achète pas.

⚠️ **Et la documentation constructeur n'est pas fiable sur ce point.** Le dossier matériel a
confronté trois sources sur quatre points vérifiables : elles se sont trompées ou contredites
**quatre fois** — dont un miroir revendeur qui annonce une puce `CH343P` **mesurée absente** de la
carte réelle, parce qu'il mélange les variantes `2.8` et `2.8B`. Détail en **§14.2** de
`hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md`. **La sérigraphie et la mesure font foi.**

### ⚠️ Ce que ce palier a vraiment été, et ce qu'il n'a pas été

La marche qui l'établit est **`dn4-41`**, et elle est **encore ouverte** — statut `in-progress`,
relu le **2026-09-06**, dernière annotation du **2026-09-01**. ⛔ On ne t'écrit donc pas « validé ».

Ce qui **a** été mesuré : le module ToF était **réellement débranché** — établi par trois sources
concordantes, dont **le fait physique demandé à l'owner** — pendant que l'autre capteur répondait
5 fois sur 5. Six démarrages à froid réels, **zéro faux positif**.

Ce qui **n'a pas** été fait, et qui reste ouvert, **par leurs clés** — `AC2.9`, fermée **avec écart
déclaré**, et `AC5`, **non mesurée** : le démarrage à froid **sans aucun capteur du tout**, et les
conditions électriques d'un bus nu. La raison est écrite : il n'existe **qu'une seule
carte**, celle du développement. ⇒ ce palier part **raisonné et instrumenté**, ⛔ **jamais démarré
sur silicium nu**. Tu es peut-être le premier à l'assembler.

---

## Palier « DeskNode + Ambiance » — la carte + deux capteurs

**Exactement** la carte ci-dessus, **plus ces deux capteurs** — la ligne de connectique qui
suit est un consommable, ⛔ pas un troisième module.

🔴 **Piège de nom, mesuré au relevé** : chercher « BME680 » ramène aussi du **BME688** et du
**BME280**. Ce ⛔ **ne sont pas** la même puce — le BME280 n'a **pas** de capteur de gaz. Sur les
annonces retenues le 2026-09-06, il a fallu **écarter à la lecture des titres**. Vérifie que
l'annonce écrit **680**, ⛔ pas « 6xx ».

| Désignation | Référence exacte | Qté | Fournisseur | Prix | Date du relevé | Source |
|---|---|---|---|---|---|---|
| Capteur température / humidité / pression / gaz | **BME680**, breakout type **CJMCU-680** (6 broches `VCC GND SCL SDA SDO CS`) | 1 | place de marché AliExpress | médiane **11,74 €** (10 annonces, 7,77 – 16,96 €) | 2026-09-06 | `https://www.aliexpress.com/w/wholesale-BME680-module.html` |
| Capteur de luminosité | **BH1750**, module **GY-302** (5 broches `VCC GND SCL SDA ADDR`, 3 – 5 V) | 1 | place de marché AliExpress | médiane **1,93 €** (10 annonces, 1,45 – 14,62 €) | 2026-09-06 | `https://www.aliexpress.com/w/wholesale-BH1750-GY-302.html` |
| Fil de liaison | Dupont femelle-femelle, ~10 cm | 4 min. | — | ⛔ **non relevé** — consommable générique vendu au lot, aucune référence unique : ⛔ aucune source n'a donc été tentée | — | — |

**Coût du palier, au 2026-09-06 :** environ **27,32 + 11,74 + 1,93 ≈ 41 €**, hors port, hors câbles.

<!-- ⛔ ANNOTATION, PAS UNE REECRITURE (NFR3) : la ligne « Fil de liaison »
     ci-dessus reste TELLE QUELLE. Ce qui suit la precise ; le report herite
     de dn6-1 designait le cablage comme territoire de la marche suivante. -->

### ⚠️ Annotation du 2026-09-07 — la ligne « Fil de liaison », précisée

La ligne **« Fil de liaison — Dupont femelle-femelle, ~10 cm | 4 min. »** ci-dessus reste telle
quelle ; ce paragraphe la **précise**, il ne la remplace pas.

**Le connecteur visé par CETTE ligne est le header 2×12 au pas de 2,54 mm**, rangée `B` : du Dupont
femelle-femelle s'y enfiche directement. ⚠️ **C'est une contrainte de TYPE DE CONNECTEUR, ⛔ pas un
choix d'accès** : la carte offre **deux** points d'accès au bus, tous deux valides, et l'autre — une
embase **JST 4 broches** — demande un **cordon JST**, ⛔ que du Dupont ne remplace pas. Si tu passes
par l'embase JST, c'est ce cordon-là qu'il te faut, ⛔ pas cette ligne. Et dans les deux cas se
tromper de voisin (embase jumelle, ou rangée voisine) envoie l'UART au capteur **sans que rien ne le
signale**. Le détail, avec la sérigraphie des deux accès et leurs deux pièges :
[câbler un DeskNode](cablage.md).

⚠️ **Et « 4 min. » est un plancher, ⛔ pas le compte.** Sur un bus I²C, `SDA` et `SCL` sont
**communs aux deux modules** — un seul bus, ⛔ pas deux — mais **partager un signal ⛔ n'économise
aucun fil** : chaque module veut sa propre liaison physique. Le compte est posé ici plutôt
qu'affirmé en l'air :

| Ce qu'il faut | Combien | Pourquoi |
|---|---|---|
| liaisons vers le **1er** module | **4** | `3V3`, `GND`, `SDA`, `SCL` |
| liaisons vers le **2ᵉ** module | **4 aussi** | il lui faut les **mêmes quatre** signaux : ⛔ un module ne se branche pas avec moins parce que le bus est partagé |
| fil `ADDR` du BH1750 vers la masse | **+1** | c'est une **entrée de sélection d'adresse**, ⛔ pas une broche libre — la laisser en l'air rend l'adresse indéfinie |

⚠️ **Ce qui VARIE, c'est l'ENDROIT d'où partent les quatre fils du 2ᵉ module, ⛔ pas leur nombre** :
soit de la carte (la rangée `B` porte `3V3` et `G`, et la rangée `A` en porte **deux autres**), soit
en dérivation depuis le 1er module. Dans les deux cas ce sont **quatre fils de plus**.

⇒ **Neuf fils au total**, et ⛔ ce n'est ni 8 ni 5 : `SDA`/`SCL` sont **communs** au sens
**électrique** — un bus, ⛔ pas deux — mais ça ⛔ n'économise **aucun fil**. **Prends un lot**, ⛔ ne
compte pas au fil près : c'est un consommable, et c'est pour ça que la ligne ci-dessus n'a ni prix,
ni source, ni quantité ferme.

### ⚠️ Pourquoi une médiane et pas une moyenne

Parce que la moyenne ment, et c'est **mesuré ici**. Sur les 10 annonces BH1750, **une seule à
14,62 €** (un lot, ou une erreur de prix) fait passer la moyenne de **2,14 à 3,39 €** — **+58 %** —
pendant que la médiane ne bouge que de 1,86 à 1,93 €.

⇒ sur une place de marché, **c'est la médiane qui tranche**. Toutes les lignes ci-dessus la
publient, et la fourchette est donnée à côté pour que tu voies l'étalement.

### Ce que le projet a mesuré sur ces deux modules

Ces valeurs viennent du dossier `hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md`, où **chacune
cite la mesure dont elle sort** — ⛔ jamais une reprise de fiche technique.

| | BME680 | BH1750 |
|---|---|---|
| Adresse I²C **mesurée** | `0x77` (§13.3) | `0x23` (§13.3) |
| Comment elle a été établie | lecture d'un registre d'identité, puis des coefficients d'usine (§13.6 bis) | par **stimulus lumineux** — il n'a aucun registre à lire (§13.16.8) |
| Broche d'adresse | `SDO` mesuré à 3,3 V ⇒ `0x77` | `ADDR` **laissé libre** ⇒ `0x23`, déterministe, **5 réponses sur 5** |
| Tension | +3,3 V mesuré au multimètre, carte allumée | 3 – 5 V (sachet) |
| Barrette | **fournie non soudée** | **fournie non soudée** |

🔴 **Les deux se soudent, et ⛔ ils ne se câblent pas pareil.** Aucun des breakouts ne s'aligne
« première broche avec première broche » : sur ces deux modules, **`SDA` et `SCL` sont croisés** l'un
par rapport à l'autre. Le schéma de câblage est le sujet de la marche suivante — d'ici là, les
photos sont là :
[BME680 avant soudure](cablage/2026-08-16_2140-bme680-recto-barrette-non-soudee.jpg) ·
[BH1750 côté broches](cablage/2026-08-19_1720-bh1750-gy302-face-broches-vcc-gnd-scl-sda-addr.jpg) ·
[BH1750 sérigraphie V322](cablage/2026-08-19_1720-bh1750-gy302-face-composants-serigraphie-v322.jpg) ·
[BH1750 sérigraphie et sachet](cablage/2026-08-19_1720-bh1750-gy302-face-composants-et-sachet.jpg)

⚠️ **Le brochage I²C de la carte est `SDA = GPIO15`, `SCL = GPIO7`** — et une source tierce les
donnait **inversés**. Mesure et sérigraphie en **§13.1** du dossier capteurs.

---

## Ce qui est sur le prototype et **hors des deux paliers**

Ces deux modules sont visibles sur les photos et présents dans le dossier de mesure. Ils ne sont
**dans aucun palier**, et voici **pourquoi** — ⛔ un composant du prototype absent de cette page
sans motif écrit serait un défaut.

| Module | Référence exacte | Prix relevé | Date du relevé | Source | Pourquoi il n'est **pas** au catalogue |
|---|---|---|---|---|---|
| Capteur de distance | **TOF050C-VL6180X** (⛔ **PAS** un VL53L0X) | **3,21 €** (1 annonce le nommant explicitement) | 2026-09-06 | `https://www.aliexpress.com/w/wholesale-TOF050C-VL6180X.html` | 🔴 **L'exemplaire testé est doublement défaillant** : son **étage analogique est mort** — aucune réaction à une variation de lumière de **~2 280×**, alors que son étage numérique répond parfaitement — **et** sa présence **empêche la carte de démarrer** (écran noir, processeur arrêté, plus d'USB). ⇒ ⛔ hors V1. |
| Capteur de courant | **INA219**, module **CJMCU** (shunt `R100`, 0,1 Ω) | médiane **1,87 €** (3 annonces, 1,80 – 2,41 €) | 2026-09-06 | `https://www.aliexpress.com/w/wholesale-INA219-CJMCU.html` | Décision projet : **pas maintenant**. Il a été **physiquement retiré du bus le 2026-08-21** et la lecture correspondante supprimée du code. ⇒ la consommation **ne sera pas mesurée en V1**. |

Ces deux modules sont sur les photos du prototype, et **les légendes le disent** : ⛔ ce que tu y
vois n'est pas ce que tu achètes.
[BH1750 **et INA219** soudés côte à côte](cablage/2026-08-20_0116-bh1750-et-ina219-barrettes-SOUDEES.jpg) ·
[le prototype en main — **quatre** modules, dont deux hors palier](cablage/2026-08-20_0951-montage-final-en-main-les-quatre-modules.jpg)

🔴 **Piège si tu cherches un INA219 toi-même** : sur 12 résultats relevés, **9 étaient des puces
nues** à souder (boîtiers SOP8, SOIC-8, SC70-6) — jusqu'à 41,68 € pour un sachet de 50. Ce que tu
veux est un **module** avec bornier et broches. Le nom seul ne suffit pas à trier.

---

## Les sources qu'on n'a pas pu atteindre

Écrit parce que c'est une information, ⛔ pas un trou : **10 sources tentées le 2026-09-06, 10 sans
prix exploitable.**

⚠️ Chaque ligne porte **l'adresse exacte** qui a été tentée et **la date de la tentative** : ⛔ un
nom de boutique ne se re-tente pas, une URL si.

| Adresse tentée | Date de la tentative | Résultat |
|---|---|---|
| `https://www.waveshare.com/esp32-s3-touch-lcd-2.8b.htm` | 2026-09-06 | HTTP 403 |
| `https://www.mouser.fr/c/?q=ESP32-S3-Touch-LCD-2.8B` | 2026-09-06 | délai dépassé à 60 s |
| `https://www.tinytronics.nl/en/search?query=ESP32-S3-Touch-LCD-2.8B` | 2026-09-06 | HTTP 403 |
| `https://eckstein-shop.de/en/search?sSearch=ESP32-S3-Touch-LCD-2.8B` | 2026-09-06 | HTTP 403 |
| `https://octopart.com/search?q=ESP32-S3-Touch-LCD-2.8B` | 2026-09-06 | HTTP 403 |
| `https://www.adafruit.com/?q=BME680` | 2026-09-06 | HTTP 403 |
| `https://www.gotronic.fr/search.php?q=BME680` | 2026-09-06 | HTTP 404 |
| `https://www.welectron.com/catalogsearch/result/?q=BH1750` | 2026-09-06 | HTTP 404 |
| `https://www.berrybase.de/search?q=ESP32-S3-Touch-LCD-2.8B` | 2026-09-06 | page rendue, **aucune fiche produit** |
| `https://thepihut.com/search?q=BME680` | 2026-09-06 | page rendue, « no results found » |

Une seule alternative européenne a répondu, et c'est **un produit différent** : Pimoroni vend son
propre « BME680 Breakout » à **11,05 GBP** hors TVA (relevé le 2026-09-06) — ⛔ ce n'est pas le
module 6 broches du prototype.

⚠️ **Ce que ces prix ne contiennent pas** : ni le port, ni les taxes à l'import, ni le délai. Et
aucune fiche produit n'a été ouverte une par une — ce sont les prix des pages de résultats, où une
fiche peut porter des variantes plus ou moins chères.

---

## Liens affiliés

**Cette page ne porte aucun lien affilié.** Les URL ci-dessus sont des adresses de recherche nues.

⚠️ Si ça change un jour, ça se dira **ici**, à cette place. Mettre en place une affiliation n'est pas
une case à cocher — ça demande de s'inscrire quelque part, de le déclarer, et de tenir la promesse
dans la durée. C'est donc porté comme un sujet à part entière, ⛔ pas comme une ligne de bas de page.

<!-- ⛔ ANNOTATION, PAS UNE REECRITURE (NFR3) : les deux paragraphes
     ci-dessus restent MOT POUR MOT. Ce qui suit les complete — le sujet
     annonce « a part entiere » a desormais sa page, et le point de bascule
     s'ecrit ici, la ou vit deja la phrase d'etat. -->

### Annotation du 2026-09-07 — le sujet a sa page, et le point de bascule est écrit

Le sujet annoncé « à part entière » ci-dessus **a désormais sa page** :
[les liens affiliés](affiliation.md). Elle dit quels programmes existent réellement pour les
fournisseurs que **cette** page cite, à quelles conditions, ce que la loi française et européenne
oblige à déclarer — chaque fait avec son adresse et sa date, chaque fait non vérifiable **déclaré**
comme tel — et ce que l'owner doit signer lui-même.

**Le point de bascule**, c'est-à-dire ce qui doit être vrai pour que la phrase d'état ci-dessus
change :

1. **le programme doit être ouvert à ce dépôt** — aujourd'hui **inconnu, ⛔ pas acquis** : les
   conditions d'admission d'AliExpress sont derrière une authentification, et celles de Waveshare,
   **publiques et lues le 2026-09-07**, disent inviter *« primarily »* des personnes ayant une
   présence sur **GitHub** — or ce dépôt y est **privé** ;
   ⚠️ *annoté le 2026-09-15 (`dn8-8`) : ce dépôt y est **public** depuis ce jour ;*
2. **l'owner doit ouvrir le compte lui-même** et accepter les conditions générales — ⛔ ce n'est pas
   un geste qu'un agent peut faire à sa place ;
3. **les deux phrases d'état doivent être réécrites** — celle-ci et celle de la page ci-dessus. Elles
   cesseront de dire « aucun » pour dire ce qui est vrai ; ⛔ elles ne s'effaceront pas.

⚠️ **Et ça se dira ici, à cette place.** Ce n'est pas une intention : c'est **gardé mécaniquement,
dans les deux sens**. Tant qu'aucune adresse publiée ne porte de marqueur d'affiliation, les deux
pages doivent l'**affirmer** ; le jour où l'une en porte un, l'affirmation devient fausse et la
vérification **rougit** — y compris si personne n'a pensé à revenir écrire ici.

---

## Licence

Cette page est de la documentation : **CC-BY-SA-4.0**, comme le reste de ce répertoire. Voir
[LICENSING.md](../LICENSING.md).

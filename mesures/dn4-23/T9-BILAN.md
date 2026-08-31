# dn4-23 / T9 — SÉANCE CARTE DU 2026-08-31

**Firmware de campagne** : `31535c0` — **SHA LU AU BANDEAU** (`App version`), ⛔ pas déduit du dépôt.
`git status --porcelain` vérifié **VIDE AVANT** le flash.
**Firmware final livré** : `8dafd15` — il ne diffère que par **un message corrigé par l'œil de
l'owner** (AC6.2), relu au bandeau après reflash.
**Conditions** : agent PC **ARRÊTÉ** (port rendu à WSL par `rendre-port.sh --vers-flash`),
`widget mock off` sauf mention, espacement injecteur **0,040 s**.

---

## AC2.7 — 🎯 **LE COMPTEUR A ATTRAPÉ UNE VRAIE PERTE**, et du premier coup

**30 captures, 2 PERTES VUES.**

| capture | annoncé | reçu | manquant |
|---|---:|---:|---:|
| `cpu delta` (1ʳᵉ séquence) | 12 | 5 | **7** |
| `cpu delta` (rejeu, passe 1) | 12 | 8 | **4** |

Ce qui manquait dans la 1ʳᵉ : **la ligne d'en-tête et tout le tableau des tâches**
(`IDLE0`, `IDLE1`, `taskLVGL`…). ⇒ **Sans le compteur, on publiait « RÉSERVE 98,9 % — CHARGE
1,1 % » sans savoir que 7 lignes manquaient.** C'est mot pour mot le faux négatif plausible que
cette story existe pour supprimer, et c'est **la même signature** que le scan I²C amputé de
`IDLE0`/`IDLE1`/`taskLVGL` de l'entrée `l.561`.

⚠️ **ELLE EST INTERMITTENTE, ET C'EST PUBLIÉ TEL QUEL** : 20 passes SOLO de `pc` ⇒ **0 perte** ;
6 rejeux de la séquence exacte qui avait perdu ⇒ **0 perte**. ⛔ **La cause reste NON INSTRUITE**
et cette story ne l'instruit pas.

✅ **Et la distinction PERTE / ÉTRANGÈRES a été exercée sur la carte** : `flash on` a rendu
**13 lignes pour 12 annoncées** — un `ESP_LOGx` de `dn_stim` tombé pendant la commande. Classé
⚠️ ÉTRANGÈRE, ⛔ **pas** perte, rc **0**. `cpu 20` : 26 pour 17. La garde ne crie pas au mauvais endroit.

## AC1 — 🎯 **LE REFUS EST LU SUR LA CARTE**

| commande | motif lu | rc |
|---|---|---:|
| `zzz` | `Unrecognized command` (REPL ESP-IDF) | **1** |
| `anim on 10` | `refusé : ESP_ERR_INVALID_ARG` **+** `Command returned non-zero error code: 0x1` | **1** |

⇒ **L'entrée de ledger `l.233` est reproduite, et l'instrument la voit maintenant.**
⚠️ **CONSÉQUENCE D'EXPLOITATION, ÉCRITE PLUTÔT QUE DÉCOUVERTE** : lire le rc du REPL fait aussi
lever le drapeau sur un **message d'usage** (`veille case` sans argument rend 1). C'est **juste** —
la commande n'a pas fait ce qu'on demandait — et `--refus-tolere <commande>` est là pour ça.
⚠️ `Unrecognized command` vient du REPL, **hors `k_cmds[]`** ⇒ pas de compteur ⇒ l'hôte imprime
**« SANS COMPTEUR »**, ⛔ jamais « 0 perte ». Comportement prévu, vu sur la carte.

## AC3.5 — 🔴 **LA MESURE RÉFUTE LA PRÉMISSE DE L'ENTRÉE `l.3126`**

Trois bras, **60 s chacun**, `flush reset` avant chaque tir, espacement **0,040 s** :

| bras | passe | cycles | aire cumulée (px) | **px/cycle** |
|---|---:|---:|---:|---:|
| `--jeu reel` (FIXE) | 0 | 245 | 11 410 225 | 46 572 |
| `--jeu reel` (FIXE) | 1 | 158 | 11 373 450 | 71 984 |
| `--jeu reel` (FIXE) | 2 | 153 | 11 410 125 | 74 576 |
| `--jeu rampe` (VARIABLE) | 0 | 209 | 11 373 550 | 54 419 |
| `--jeu rampe` (VARIABLE) | 1 | 260 | 11 263 475 | 43 321 |
| `--jeu rampe` (VARIABLE) | 2 | 180 | 11 373 400 | 63 186 |
| `widget mock on` | 1 | 75 | 9 356 375 | **124 752** |
| `widget mock on` | 2 | 75 | 9 356 125 | **124 748** |

🔴 **(1) L'AIRE CUMULÉE EST LA MÊME, FIXE OU VARIABLE** — ~11,37 M px sur 60 s, à **1 % près**.
⇒ **le jeu variable NE FAIT PAS DESSINER PLUS.** Sur ce firmware, le redessin est déclenché par
**l'ARRIVÉE DE LA TRAME**, ⛔ pas par le changement de valeur.

🔴 **(2) LE px/CYCLE EST DOMINÉ PAR LE BRUIT** : `reel` va de **46 572 à 74 576** (×1,60) et
`rampe` de **43 321 à 63 186** (×1,46) — **les deux plages se chevauchent intégralement**.
⇒ ⛔ **px/cycle n'est PAS un discriminateur** entre ces deux jeux sur n = 3. C'est la doctrine
d'AC7 appliquée ici : **on refuse le delta parce que les étendues se chevauchent.**

✅ **(3) LE REPÈRE `mock` TIENT, ET IL EST D'UNE STABILITÉ REMARQUABLE** : 75 cycles / 9 356 xxx px
**deux fois**, à **250 px près** ⇒ **124 750 px/cycle**, contre **128 613** au repère de la story
(−3 %). Et il dessine **MOINS en aire** (9,36 M contre 11,37 M) en **beaucoup moins de cycles**
(75 contre 153-260) : le mock bat à 14/20/26/34 s, l'injecteur à 1 Hz.

⇒ 🎯 **CE QUE L'ÉCART « 94 645 vs 128 613 » MESURAIT VRAIMENT, C'EST LA CADENCE**, ⛔ pas la
variabilité des valeurs. L'entrée `l.3126` attribuait à la **fixité** un écart qui vient du
**rythme de poussée**. **AC3.5 est donc RÉFUTÉ dans sa prémisse** — voir la disposition au ledger.

✅ **Ce que le jeu `rampe` apporte QUAND MÊME, et il faut l'écrire** : il fait **changer le TEXTE**
des six cases, donc il exerce le chemin de composition, la largeur des chaînes et le clip — ce que
quatre dictionnaires de constantes n'exercent pas. ⛔ Il ne change simplement pas le **volume**
de dessin sur ce firmware.

## AC4.4 — ⚠️ **PARTIEL, ÉCART DÉCLARÉ**

| instrument | fenêtre | CHARGE au repos |
|---|---|---:|
| `cpu 20` (**BLOQUANT**) | 20,0 s | **1,5 %** |
| `cpu depart` / `cpu delta` (**NON BLOQUANT**) | 20,3 à 20,6 s, n = 3 | **1,1 %** (3 fois sur 3) |

✅ **Les deux instruments s'accordent à 0,4 point**, et le non bloquant est **reproductible à
0,0 point sur 3 passes**. ✅ Sous trafic d'injection (60 s), `cpu delta` rend **5,4 %** (jeu fixe)
et **5,8 %** (rampe) — **une charge que `cpu N` ne peut PAS mesurer**, puisqu'il aurait fallu
taper la commande pendant que l'injecteur tient le port. **C'est exactement la démonstration
d'AC4.**

🔴 **ÉCART** : AC4.4 attend **~0,89 %** (les 0,9 % de `dn1-4`). Mesuré **1,1 %**, soit **+24 %**.
⛔ **Non atteint, et ce n'est pas arrondi vers le bas.** Le repère `dn1-4` vient d'un **autre
firmware** et d'une **autre scène** ; rien dans cette séance ne permet de dire lequel des deux
chiffres décrit quoi. ⇒ **fermé avec écart déclaré**, ⛔ pas coché.

## AC5.3 — 🎯 **SOLDÉ, AVEC SON TÉMOIN NÉGATIF**

| commande tapée | mesuré par la carte | largeur | drapeau |
|---|---|---:|---|
| `widget largeur RÉSEAU 18` | **`RSEAU`** | **63 px** | 🔴 *« RSEAU est EXACTEMENT RÉSEAU privé de ses octets ≥ 0x80 »* |
| `widget largeur RESEAU 18` | `RESEAU` | **75 px** | ⚠️ la limite générale seulement — ⛔ aucune accusation |

⇒ **L'écart que l'instrument rendait « sans un mot » vaut 12 px, soit 16 %.**
Et `argc` est resté à **4** : la mutilation est **partielle**, la garde de `dn4-14-2` ne la voyait pas.

## AC7.6 — 🎯 **LA DISPERSION, SUR LE MÊME FIRMWARE, ET LE DELTA REFUSÉ**

| relevé | moyennes par fenêtre (ms) | étendue | σ | facteur |
|---|---|---:|---:|---:|
| A | 110 · 110 · 124 · 153 · 170 | **60 ms** | 24,1 | **×1,55** |
| B | 153 · 170 · 130 · 100 · 96 | **74 ms** | 28,9 | **×1,77** |

**Même binaire `31535c0`, même jeu, même espacement, 5 fenêtres de 20 s chacune.**
⇒ `--latence-delta A B` : **🔴 REFUS — les étendues se chevauchent** (A [110 ; 170], B [96 ; 170]),
écart des médianes **6,0 ms**, dans le bruit. Et l'outil a signalé de lui-même que **les deux
relevés portent le même firmware** — *« c'est une mesure de la VARIANCE, ⛔ ne pas l'étiqueter
autrement »*.

⚠️ Sur les **10 fenêtres** cumulées : **96 à 170 ms**, facteur **×1,77**. Ce n'est pas le ×3 de
`fd959f2`, mais **la thèse tient** : un delta de firmware inférieur à ~70 ms est **indiscernable
du bruit** sur cet instrument.
⛔ **Aucune tendance n'est publiée** : A monte (110→170), B descend (153→96). ⇒ **du bruit, pas une
dérive.** ⛔ La variance n'est toujours pas isolée, et cette story ne l'isole pas.

## AC6.2 — 🎯 **SOLDÉ, ET L'ŒIL A CORRIGÉ MON VERDICT**

**A/B à DEUX fenêtres de 60 s, injecteur `--jeu rampe`, UNE SEULE VARIABLE (l'aplat).**
Verbatims owner, **séparés** (⛔ ne pas les fusionner) :

| fenêtre | aplat | écart | verbatim owner |
|---|---|---:|---|
| **A** | `000000` | 23 | *« 2 zones distinctes vert claire et vert foncé on vois bien la barre bouger »* |
| **B** | `141820` | **0** | *« les 6 cases sont vertes et la barre de chargement etait vert claire dessus »* |

🔴 **CE QUE ÇA CORRIGE, ET C'EST DANS MON PROPRE CODE** : le verdict imprimait
**« LA JAUGE DISPARAIT »**. **C'est TROP FORT.** Ce qui disparaît, c'est **LA PISTE** ; l'INDICATEUR
reste parfaitement visible. Ce qui est **perdu**, c'est la **LONGUEUR TOTALE** — la jauge ne se lit
plus comme une **PROPORTION**, seulement comme une longueur nue.
⇒ Message corrigé en **« ECART NUL — LA PISTE SE FOND DANS LA CASE »**, rebuild, reflash,
**relu sur la carte** (firmware `8dafd15`).
⛔ **Un instrument qui SUR-ANNONCE est du même genre que celui qui se tait** — le commettre dans
le verdict même de cette story aurait été une faute de famille.

✅ **Et le VERT est confirmé comme une contrainte de la DALLE**, ⛔ pas un effet du réglage : les
**deux** fenêtres l'ont rendu, y compris celle à l'aplat noir. C'est l'arbitrage owner du
2026-08-31 déjà consigné dans `dn_widget.c`, et il **tient**.

✅ **Le verdict console confirme la mesure de la story** : les six descripteurs livrés sont hors de
danger — **Δ 97 à 208**, le minimum étant `RÉSEAU` à **97**, exactement le `Δ ≥ 97` annoncé.
La paire piste↔fond livrée rend **23**, signalée **⚠️ FAIBLE — à vérifier À L'ŒIL**, ⛔ pas refusée.

---

## ⛔ CE QUE CETTE SÉANCE N'A PAS FAIT

- ⛔ **Elle n'a pas instruit la cause de la perte de lignes.** 30 captures, 2 pertes, aucune
  reproduction à la demande. C'était **hors périmètre**, et ça le reste.
- ⛔ **Elle n'a pas isolé la variance de la latence.** Deux hypothèses restent réfutées.
- ⛔ **Elle n'a pas mesuré le contraste sous ARTWORK** : en Actif, l'aplat est du noir à 178/255 sur
  le Living PCB, et l'écart réel dépend de ce qui passe sous la case. **Le verdict le DIT** et rend
  un **PLAFOND**, ⛔ pas une mesure. C'est l'écart déclaré de `dn4-29`, et il reste ouvert.

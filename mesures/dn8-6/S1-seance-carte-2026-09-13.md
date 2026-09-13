# `dn8-6` — séance carte du 2026-09-13 : la version se lit dans le MENU

**Firmware éprouvé : `55006c19182b3ff1ccc017044057347841ede475`**, relu au bandeau (`App version: 55006c1`,
compilé le 2026-09-13 à 19:48:28). **Référence A** : le binaire trouvé sur la carte, `40be2c8` (relu au
bandeau, compilé le 2026-09-08). Captures brutes, ⛔ non retouchées : `seance-2026-09-13/`.
Agent : l'œil de l'owner et le pilote série. Owner : un tap et deux constats.

## 0. Cadrage — relevé avant de toucher au port

- **Arbre** `desknode` `main` @ `55006c1`, `git status --porcelain` vide. **Gate de dossier**
  `verif_dossier_dn415.py --cockpit` : `23 OK, 10 KO`. ⚠️ Rouge **pré-existant**, ⛔ pas imputable à la
  séance.
- **Build de référence** : `idf.py reconfigure` **puis** `idf.py build` sur l'arbre committé. Le
  descripteur du `.bin` (`0x30..0x50`) rend **`55006c1`**, `git describe --tags --always --dirty` rend
  **`55006c1`**, sans `-dirty`. 1 266 928 o.
- **A est comparable sans flash de plus** : `git diff --quiet 40be2c8 e0dd063 -- firmware/desknode/main`
  rend 0, et `git diff --stat` sur `firmware/desknode` est vide.
- **État de la carte avant** (`A2`) : `veille ARMEE · delai 3 min`. ⚠️ `veille off` **écrit la NVS** :
  désarmée pour les fenêtres, **ré-armée et relue à la fin** (`C1` : `veille ARMEE · delai 3 min`).

## 1. `AC8.6.3` — les quatre sources disent la même chose

| source | lue | quand |
|---|---|---|
| `git describe --tags --always --dirty` (arbre committé, après `reconfigure`) | `55006c1` | 19:48 |
| descripteur de `build/desknode.bin` | `55006c1` | 19:48 |
| bandeau série `App version` après flash (`B2`) | `55006c1` | 20:00:52 |
| **la dalle**, ligne sous le titre du MENU, lue par l'owner | **`version 55006c1`** | 21:24 |

⛔ Aucune ne porte `-dirty`. **`AC8.6.5`** : le commit `55006c1` précède le build de référence et le
flash (20:00:21). L'arbre a été vérifié propre (`git status --porcelain` vide) dans la même commande
que le flash. ⚠️ Cette vérification n'est **pas** dans `B1`, qui ne capture que la sortie
d'`idf.py`.

## 2. `AC8.6.2` — l'œil de l'owner, le MENU ouvert AU DOIGT

Tap owner à **au moins 3 min** d'uptime (boot 20:00:43, relevé préalable `B4` à 20:04:14).

> **Verbatim owner : « version 55006c1 lisible ok (mais a la limite), menu ouvert »**

La carte confirme le geste (`B5`) : `taps sur zone : 1 (dont 1 sur MENU)`, `1 transitions depuis le
boot`, `libelles du MENU trop larges : 0`.
⚠️ **« À LA LIMITE » EST CONSIGNÉ TEL QUEL, ⛔ PAS ARRONDI EN « OK »** : la ligne tient dans
l'en-tête avec **0 px** de marge basse (liseré compris) et **1 px** sous le titre. ⛔ Aucun correctif
improvisé en séance.

## 3. `AC8.6.4` — le coût, en cycles et en `flush`

**Protocole** (§26.2 du dossier d'affichage, régime **injecté**) :
- `tools/dn_injecteur.py --jeu rampe`, 5 trames/s, espacement 0,04 s, protocole v3 ;
- `pc reset` + `flush reset` **en régime**, puis tir, puis relevé `flush` + `pc` ;
- aucune fenêtre dans les 3 min qui suivent un boot.

⛔ **Le PC n'est pas mesuré** (port en usbipd⇒WSL, pas l'agent réel).

| fenêtre | durée | cycles de redessin | cycles/s | flushes | aire cumulée | série non saine | seaux 10 / 25 / 50 % | 🔴 CORRUPTION | déficit pire | `ph_ref` · `ph_max` |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---|
| **A** `40be2c8` · tableau de bord | 300 730 ms | 1 442 | 4,795 | 1 553 | 56 793 550 px | 0 | 176 / 0 / 0 | **0** | 168 µs (607 de marge) | 2259 · 2267 |
| **B** `55006c1` · tableau de bord | 300 626 ms | 1 432 | 4,763 | 1 555 | 56 866 750 px | 0 | 94 / 0 / 0 | **0** | 120 µs (655 de marge) | 2258 · 2269 |
| A · MENU ouvert | 120 706 ms | 1 | — | 5 | 307 200 px | — | 0 / 0 / 0 | **0** | 10 µs | 2259 · 2275 |
| B · MENU ouvert | 120 629 ms | 0 | — | 0 | — | — | 0 / 0 / 0 | **0** | 16 µs | 2261 · 2273 |

**Ce que la table établit** : aucune dépense de la marge de déchirure. CORRUPTION **0** et seaux
25 / 50 % à **0** dans les deux fenêtres de tableau de bord, et le déficit pire reste à un ordre de
grandeur sous le demi-bounce de 775 µs. Le régime de dessin est le même à 1 % près : 1 442 contre
1 432 cycles, +0,13 % d'aire cumulée.

⛔ **Ce qu'elle n'établit PAS** :
- **Une amélioration.** L'écart 176 ⇒ 94 au seau 10 % et 168 ⇒ 120 µs au déficit pire tient dans le
  bruit connu du compteur. Le déficit pire est un MAX, et il n'y a qu'**une** fenêtre par binaire.
- **Le coût d'un MENU ouvert.** Un menu ouvert **ne redessine pas**, car le tableau de bord n'est pas
  l'écran chargé : A rend un seul cycle (le chargement du menu, un plein écran de 307 200 px), B zéro.
  ⇒ ces deux fenêtres mesurent **presque du vide**, et c'est dit.
- **L'égalité des conditions thermiques.** A démarre à ~3,5 min d'uptime et B à ~86 min : l'owner est
  revenu 80 min après le flash, et la carte a tourné **sans trafic** entre 20:04 et 21:24.

**Refus lus par l'injecteur** : chauffe A 4/750 · tir A 12/1 500 · menu A 7/600 · chauffe B 5/925 ·
menu B 8/600 · tir B 10/1 500. Ce sont des lignes corrompues côté REPL (`Unrecognized command`).
Côté liaison, `pc` rend `rejets : tronquee 0 · trop longue 0 · checksum 0 · version 0 · format 0 ·
bornes 0` et la liaison **VIVANTE** dans les deux fenêtres de tableau de bord.

## 4. Retour en régime

- `veille on` relu : `ARMEE · delai 3 min`, identique au départ.
- `rendre-port.sh --vers-agent` : STATE `Shared`, COM3 libre. Tâche `DeskNode agent` relancée par
  `Start-ScheduledTask` ⇒ `Running`, COM3 tenu.

> **Verbatim owner : « oui ça tourne, valeurs vivantes »**

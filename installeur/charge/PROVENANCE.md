# D'où vient ce que cette page installe

Ce dossier porte **la charge** que `installeur/index.html` écrit sur la carte : quatre images
binaires et le manifeste qui dit **où** chacune se pose. Cette page dit **d'où elles sortent**,
**qui les a produites**, et — c'est la partie qui compte — **ce que personne ne vérifie
automatiquement**.

## La révision exacte, et comment elle se relit

| | |
|---|---|
| **révision du dépôt** | **`55006c1`** — `git describe --tags --always --dirty` au dernier *configure* avant le build |
| **où elle est écrite** | dans `desknode.bin` lui-même, champ `version` de `esp_app_desc_t` |
| **comment on la relit** | offset `0x20` (magie `0xABCD5432`), puis `version[32]` à `+16` ⇒ `0x30` |
| **horodatage du build** | `Sep 13 2026 19:48:28`, lu au même endroit |
| **ESP-IDF** | `v5.5.5`, lu au même endroit |

> 🔴 **ANNOTÉ LE 2026-09-14 (`dn8-7`) — LA CHARGE A CHANGÉ, ET CE QUE CE TABLEAU DISAIT RESTE ÉCRIT
> ICI, ⛔ PAS EFFACÉ (`NFR10`).** Du 2026-09-08 au 2026-09-14 il portait : révision **`40be2c8`** —
> *« `git rev-parse --short HEAD` au moment du build »* —, horodatage `Sep  8 2026 23:14:36`,
> ESP-IDF `v5.5.5` ; et le manifeste portait `"version": "40be2c8"`. Ce build-là **n'affichait pas
> sa version sur la dalle** : la ligne `version` de l'en-tête du MENU est arrivée avec `55006c1`.
> ⇒ ce que la release `v0.1.0-beta` distribue est le binaire **vu sur la dalle**, ⛔ pas celui-là.
> ⚠️ La révision se décrit désormais par `git describe`, ⛔ plus par `git rev-parse` : c'est ce
> qu'ESP-IDF évalue réellement (paragraphe *`idf.py reconfigure`* ci-dessous), et les deux ne
> rendent la même chaîne que tant qu'aucun tag n'existe et que l'arbre est propre.

```bash
python3 -c "d=open('installeur/charge/desknode.bin','rb').read(0x100); \
            print(d[0x30:0x50].split(b'\x00')[0].decode())"
```

🔴 **Cette chaîne n'est ⛔ pas recopiée dans le manifeste : elle en est LUE.**
`installeur/charge/manifest.json` porte `"version": "55006c1"`, et
`tools/verif_flash_dn72.py` **confronte les deux mécaniquement**, à chaque passe de
`tools/run_gates.sh`. ⛔ Une version annoncée qui ne serait pas celle du binaire servi est le
défaut exact que `NFR7.3` interdit — le prototype du 2026-08-31 annonçait `0.1.0-beta-essai`,
la valeur de son banc d'essai, sur une charge dont plus personne ne savait dire l'âge.

## La commande qui l'a produite

```bash
. $HOME/esp/esp-idf/export.sh
cd firmware/desknode
idf.py reconfigure     # ⛔ OBLIGATOIRE — voir juste en dessous
idf.py build

cp build/bootloader/bootloader.bin              ../../installeur/charge/bootloader.bin
cp build/partition_table/partition-table.bin    ../../installeur/charge/partition-table.bin
cp build/desknode.bin                           ../../installeur/charge/desknode.bin
cp build/living_pcb_v0.bin                      ../../installeur/charge/living_pcb_v0.bin
```

🎯 **POUR LA CHARGE SERVIE DEPUIS LE 2026-09-14, CETTE COMMANDE A ÉTÉ JOUÉE UNE FOIS — ET ⛔ PAS
REJOUÉE POUR LA RELEASE.** `desknode.bin` est le **build de référence de la séance carte de
`dn8-6`**, le 2026-09-13 : `idf.py reconfigure` puis `idf.py build` sur l'arbre **committé et
propre** à `55006c1`, flashé par `idf.py` sur la carte de développement, relu au bandeau série
(`App version: 55006c1`, `Compile time: Sep 13 2026 19:48:28`, `ELF file SHA256: fa4ac7bd7...`) et
**lu sur la dalle** par l'owner (`version 55006c1`, sous le titre du MENU). `dn8-7` l'a **copié**
de `firmware/desknode/build/desknode.bin` — une copie **gardée**, SHA-256 relu avant et après —,
⛔ **sans le reconstruire** : le même jour, trois builds de **même taille** (1 266 928 o) ont rendu
trois SHA-256 **différents** — un rebuild aurait distribué un binaire que personne n'a vu tourner.
Les trois autres images de `build/` sont **identiques octet pour octet** à celles du 2026-09-08.
Relevés : `mesures/dn8-6/seance-2026-09-13/` (flash et bandeau) et
`mesures/dn8-7/T1-la-charge-de-la-seance.txt` (la copie, relue).
⚠️ **Ce qui n'est ⛔ pas rejoué** : le flash de **ce** binaire-là **depuis la page**. `dn7-2` l'a
prouvé sur la charge précédente ; la séance de `dn8-6` a flashé par `idf.py`.

⚠️ **`idf.py reconfigure` avant le build n'est ⛔ pas une précaution.** Le champ
`esp_app_desc_t.version` vient de `git describe`, **évalué au dernier *configure*** — ⛔ pas au
dernier *build* (`hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md`, § *l'étiquette de version*).
Sans lui, l'étiquette nomme **le commit précédent** : c'est le piège qui a fait écrire
*« la carte porte `1adf259` »* pendant trois jours en `dn4-10`. Mesuré ici même le
2026-09-08 : avant le `reconfigure`, le `build/` local portait encore `6a91fa3` — du
**1ᵉʳ septembre** — pour un `HEAD` à `40be2c8`.

Les **offsets** du manifeste ne sont pas tapés à la main non plus : ils sont lus dans
`firmware/desknode/build/flasher_args.json`, clé `flash_files`, qui est ce que l'IDF écrit
lui-même à la fin du build.

## Ce que chaque morceau pèse, et ce qu'il vaut

| fichier | offset | taille (octets) | SHA-256 |
|---|---|---|---|
| `bootloader.bin` | `0` | `20848` | `d1bf1fd347b3494bcb3d38c7cee0d4698fd45617505529cf5c5dc1653ae0a478` |
| `partition-table.bin` | `32768` | `3072` | `0934eb422b7c7f52193373a9ce81818e7344d9f0061e073b60fb8ebe209e46eb` |
| `desknode.bin` | `65536` | `1266928` | `2b845a161079de8bb90ee2b23208a2531d04b157f76fea1c61933a6f8d474e3b` |
| `living_pcb_v0.bin` | `4259840` | `614416` | `fae162a0a422c3c134db7ba015d8ddcf0adb20502be4f1617c17dba9fb3500ed` |

**Total : 1 905 264 octets.** Les quatre morceaux se posent **séparément**, ⛔ **sans
`merge_bin`** : c'est ce qui a été mesuré le 2026-08-31, et c'est ce que le manifeste décrit.

> 🔴 **ANNOTÉ LE 2026-09-14 (`dn8-7`) — LA LIGNE `desknode.bin` ET LE TOTAL ONT CHANGÉ ; LES ANCIENS
> SONT CITÉS ICI, ⛔ PAS EFFACÉS (`NFR10`).** Du 2026-09-08 au 2026-09-14, pour la révision
> `40be2c8`, la table portait :
>
> | `desknode.bin` | `65536` | `1266752` | `00719e7310df9c5368cd84b965190883a001b39530c35ae61c6b8729f63e72b5` |
>
> et un total de 1 905 088 octets. Les trois autres lignes n'ont ⛔ pas bougé : leurs images sont
> identiques. ⚠️ **La citation est HORS de la table, et c'est voulu** : `tools/verif_flash_dn72.py`
> lit toute ligne qui **commence** par `|`, et une ancienne ligne gardée dans la table ferait
> confronter la charge servie à une empreinte périmée.

⚠️ **`living_pcb_v0.bin` fait `614 416` o et ⛔ pas `614 400`.** Les **16 octets** de plus sont
une **bande-annonce d'intégrité** collée après la charge utile par `tools/gen_living_pcb.py` :
magie ASCII `DNASSET1` (8 o), longueur `uint32` little-endian, **CRC32 zlib** `uint32`
little-endian. Le firmware la relit à l'identique (`firmware/desknode/main/dn_asset.c`), et
`tools/verif_flash_dn72.py` la **revérifie ici** — magie, longueur **et** CRC — parce que
c'est un instrument d'intégrité **gratuit** sur une charge qu'on distribue.

## Ce que le manifeste décide d'autre, et pourquoi

Le manifeste ne porte pas que des offsets. Il porte aussi
**`"new_install_prompt_erase": false`**, et cette valeur mérite une phrase parce qu'elle
**décide de ce qui arrive à la carte de quelqu'un**.

Elle dit à l'outil de flash de **⛔ ne pas proposer d'effacer la puce entière** au premier
passage. Écrire les quatre morceaux **par-dessus** ce qui est là suffit dans le cas visé — une
carte DeskNode, neuve ou déjà flashée — parce que le **découpage de partitions est écrit à
`32768`** au même passage : la table qui décide de tout est donc **remplacée**, ⛔ pas héritée.

⚠️ **Le prix, écrit** : la partition `nvs` (à `0x9000`) est **hors** des quatre morceaux ⇒ elle
**survit**. Un choix de langue, un réglage de veille ou une clé posés par un firmware
**antérieur** restent en place — ce qui est **voulu** pour une mise à jour, et c'est ce qui rend
*« mettre à jour = réinstaller »* tenable. ⛔ Sur une puce venue d'un **autre projet**, une NVS
étrangère survit elle aussi ; le firmware la lit comme une NVS DeskNode, et son garde-fou de
lecture est ce qui l'attrape — ⛔ pas ce manifeste. Proposer l'effacement à tout le monde pour
ce cas-là coûterait, à chaque mise à jour ordinaire, la perte des réglages de quelqu'un.

> 🔴 **ANNOTÉ LE 2026-09-09 (`dn7-3`) — LE PARAGRAPHE CI-DESSUS EST RÉFUTÉ PAR LA MESURE,
> ET IL N'EST ⛔ PAS EFFACÉ (`NFR3`).** *« la partition `nvs` est hors des quatre morceaux
> ⇒ elle **survit** »* est **FAUX** : le 2026-09-09, après un flash **depuis cette page**,
> la commande `cfg` de la carte rend *« aucune config en NVS — defauts appliques »*, et le
> témoin de repli sort en `ESP_ERR_NVS_NOT_FOUND`. **Les réglages ne survivent pas.**
> ⇒ ce qui reste vrai du paragraphe : la table de partitions **est** réécrite à `32768`, et
> `new_install_prompt_erase: false` **est** ce que porte le manifeste. Ce qui est réfuté,
> c'est la **conséquence** qu'on en tirait pour la NVS.
>
> 🔴 **ET C'EST CLOS PAR UNE DÉCISION OWNER DU 2026-09-09, ⛔ pas par un correctif** :
> l'effacement à l'installation est **ACCEPTÉ** — verbatim owner : *« franchement que tout
> soit écrasé pour 3 pauvres param on s'en branle »*. ⇒ ⛔ **ce n'est pas un défaut à
> corriger**, et la **cause** (le firmware d'un côté, l'outil de flash de l'autre) n'a
> **volontairement pas été tranchée**. ⛔ Ne pas rouvrir le sujet en lisant cette annotation.
>
> ⚠️ **POURQUOI CETTE PAGE-CI EST ANNOTÉE, ET ⛔ PAS UNE AUTRE** : c'est exactement le sujet
> de la marche qui pose la **langue de la dalle**. La langue est rangée en NVS ; si la NVS
> survivait, la reposer après chaque mise à jour serait inutile. Elle ne survit pas ⇒ **le
> geste de langue est à rejouer après chaque flash**, et la page le **dit à l'étape qui pose
> la langue** plutôt que de laisser quelqu'un le découvrir sur une dalle redevenue anglaise.

⇒ La valeur est **`false`**, et `tools/verif_flash_dn72.py` l'épingle : la basculer à `true`
fait rougir la gate, parce qu'un changement pareil ⛔ ne doit pas passer sans que ce paragraphe
soit réécrit.

## 🔴 Ce que RIEN ne vérifie — écrit, ⛔ pas tu

**La provenance de ces quatre fichiers n'est mécanisée par AUCUNE chaîne automatique.** Ce
n'est ni un oubli ni une négligence : c'est un état, et il est mesurable.

- **Aucune CI ne construit ce firmware.** Le marqueur qui porte ce chantier — *« la CI
  construit le firmware »* — est **`not started`** dans [`docs/roadmap.md`](../../docs/roadmap.md),
  et le motif y est écrit : un runner devrait installer ESP-IDF v5.5.5 (**3,84 Gio**,
  23 sous-modules) et ses chaînes (**4,30 Gio**), puis tirer **172,5 Mio** de composants.
  ⇒ **aucun workflow de `.github/` n'appelle `idf.py`.**
- **Ces fichiers ont donc été construits À LA MAIN**, sur un poste, avec les commandes
  ci-dessus. Ce qui les relie à `40be2c8` est **l'étiquette dans le binaire**, ⛔ pas une trace
  de build reproductible par un tiers.
- **`living_pcb_v0.bin` n'est même pas un produit du compilateur** : il sort de
  `tools/gen_living_pcb.py`, un script Python déterministe à graine égale. Sa reproductibilité
  repose sur cette déterminisme, ⛔ pas sur une signature.
- **Il n'y a ⛔ aucun tag et ⛔ aucune release** — mesuré le 2026-09-08 : `git tag -l` est
  **vide**, `gh release list` est **vide**, et ce dépôt est **privé**. ⇒ ce que cette page
  pointe est **la révision exacte**, `40be2c8`, ⛔ pas une source **publiquement atteignable**.

> 🔴 **ANNOTÉ LE 2026-09-14 (`dn8-7`) — LES DEUX PUCES CI-DESSUS SONT DATÉES, ⛔ PAS EFFACÉES.**
> *(i)* La révision que ces fichiers relient est désormais `55006c1` (voir la table du haut), et
> le lien reste **l'étiquette dans le binaire** : ils sont toujours construits **à la main**.
> *(ii)* **Un tag et une release existent** : le tag annoté `v0.1.0-beta` et sa pre-release GitHub
> portent **cette** charge — les quatre images, le manifeste, et l'archive de l'arbre du tag, dont
> le `firmware/` est identique à `55006c1`. ⚠️ **Ce qui ne change PAS** : ce dépôt est **encore
> privé**. La source est donc atteignable par **son seul propriétaire**, ⛔ par un inconnu, et
> c'est ce qui reste du second manque ci-dessous.

> ⚠️ **ANNOTÉ LE 2026-09-15 (`dn8-8`) — ⛔ RIEN N'EST EFFACÉ.** *« Ce dépôt est encore privé »* a
> cessé d'être vrai ce jour : le dépôt est **public**. La source que cette page nomme — le tag
> `v0.1.0-beta` et la révision `55006c1` — est donc dans un dépôt **public**, et le second manque
> ci-dessous, dont la cause écrite était la visibilité du dépôt, est **fermé**. ⚠️ Ce qu'un inconnu
> en lit réellement sans compte se relève **après** la bascule, ⛔ dans cette annotation. Le
> premier manque, la mécanisation, n'a pas bougé.

🎯 **Porteur de la mécanisation : `dn4-45`** (*« la CI construit le firmware »*), aujourd'hui
`not started` — c'est lui, et personne d'autre, qui remplacera « construit à la main sur un
poste » par une trace vérifiable.
🎯 **Porteur de la source publiquement atteignable : `epic-dn8`** (la vitrine, le tag et la
première release). ⛔ Un écart sans porteur écrit est un oubli déguisé, et celui-ci en a
**deux**, parce que ce sont **deux manques différents**.

> ⚠️ **ANNOTÉ LE 2026-09-14 (`dn8-7`) — LES DEUX LIGNES CI-DESSUS SONT GARDÉES TELLES QUELLES.** Des
> trois gestes que `epic-dn8` nommait pour le second manque — la vitrine, le tag, la première
> release —, la vitrine est en place, et le tag et la release existent. Ce qui reste du manque est
> **la bascule du dépôt en public**, sans laquelle ni le tag ni la release ne sont atteignables
> par un inconnu. Le premier manque, lui, n'a pas bougé d'un octet.

> ⚠️ **ANNOTÉ LE 2026-09-15 (`dn8-8`).** La bascule du dépôt en public a été jouée ce jour : il ne
> reste **rien** du second manque, et `epic-dn8` n'a plus rien à porter pour lui.

> ✅ **MESURÉ LE 2026-09-15 (`dn8-8`), après la bascule** (`mesures/dn8-8/P1-bascule.txt`) : sans
> compte, la page du tag, l'arbre du tag et l'arbre de la révision `55006c1` répondent 200 ; les
> quatre images téléchargées depuis la release ont la taille et le sha256 de la table de cette
> page ; un clone anonyme porte `55006c1`.

## Pourquoi ces binaires sont AU DÉPÔT, et pourquoi le dossier s'appelle `charge/`

Quelqu'un qui télécharge DeskNode **n'a pas de build**. Sans images dans l'arbre, la page n'a
rien à poser et *« la carte se flashe depuis la page »* est inatteignable. Le coût est
**mesuré** — 1 905 088 octets — et il est **assumé**, faute d'une release (`epic-dn8`) et d'une
CI de build (`dn4-45`).

> ⚠️ **ANNOTÉ LE 2026-09-14 (`dn8-7`).** Le coût vaut désormais **1 905 264 octets** (table
> ci-dessus), et *« faute d'une release »* a cessé d'être vrai : la release `v0.1.0-beta` porte
> ces quatre images. ⛔ **Elle ne les retire pas de l'arbre** : la page les sert depuis ce dossier,
> et l'archive de la release **est** l'arbre du tag. Ce qui les en ferait sortir reste une CI de
> build, et ce manque-là est entier.

⛔ **Le dossier ne s'appelle ⛔ ni `build/` ni `build-quelque-chose/`, et ce n'est pas un
goût.** `.gitignore` porte `build/` et `build-*/` **sans `/` initial** : ces motifs mordent **à
toute profondeur**. Mesuré à `git check-ignore` le 2026-09-08 : `installeur/charge/desknode.bin`
n'est **pas** ignoré, `installeur/build/a.bin` l'**est** — les binaires auraient disparu de
`git status` **en silence**.

Et le dossier reste **sous `installeur/`** parce qu'un répertoire de 1er niveau neuf ferait
rougir **deux** gates d'un coup (la couverture de licences et la table des répertoires figés du
boîtier). Il hérite donc de la ligne `installeur/` de [`LICENSING.md`](../../LICENSING.md) :
**GPL-3.0-or-later**, ce que la section *Binary releases* de ce fichier annonçait déjà pour les
binaires *« installés par le flasheur web »*.

Copyright © 2026 Nasbarok. Ce fichier suit la licence du dossier `installeur/`, déclarée dans
[`LICENSING.md`](../../LICENSING.md).

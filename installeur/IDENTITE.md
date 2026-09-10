# L'identité visuelle de la page d'installation

Cette page est **la seule surface qu'un inconnu traverse forcément**. Elle mérite donc une
identité **statuée et écrite**, ⛔ pas héritée d'un banc d'essai — et c'est ce fichier qui
l'écrit, jeton par jeton, chacun citant **son fichier et sa ligne** dans le firmware.

`tools/verif_installeur_dn71.py` garde l'égalité **dans les deux sens** : toute couleur
déclarée ici doit servir dans `index.html`, et toute couleur employée par `index.html` doit
être déclarée ici. Une palette qui dérive de sa page cesse d'être une identité.

## La décision, et ce qu'elle remplace

Le prototype de flash du 2026-08-31 (`C:\Users\naoua\dn-webflash\`, ⛔ jamais versionné)
portait un fond `#0d1117`, un texte `#e6edf3`, un accent `#3fb950` et des cartes
`#161b22` / `#30363d`. **C'est la palette de GitHub**, prise telle quelle pour un essai qui
devait durer une soirée. Elle n'a jamais été choisie : elle a été *trouvée sous la main*.

🎯 **Ce qui la remplace est la palette de la dalle, MESURÉE dans le firmware.** Le motif
n'est pas esthétique et il est vérifiable : la page et la dalle sont **le même produit**, vu
à deux moments. Quelqu'un qui installe DeskNode voit la page, puis, trente secondes plus
tard, l'écran ; si les deux ne se ressemblent pas, la page est une brochure pour un autre
objet. ⇒ **les couleurs ne sont pas inventées ici, elles sont relevées là-bas.**

⚠️ **Ce n'est ⛔ pas une charte graphique.** C'est une liste fermée de sept rôles, avec leur
source. Elle ne dit rien des typographies, des espacements ni des formes — ceux-là suivent
les valeurs par défaut du système, délibérément : une page d'installation qui charge une
police distante est une page qui ne s'ouvre pas quand le réseau est mauvais.

## Les sept jetons

| jeton | rôle dans la page | valeur | source dans le firmware | nom là-bas |
|---|---|---|---|---|
| `--dn-fond` | le fond de la page et des cartes | `#000000` | `firmware/desknode/main/dn_widget.c:1425` | `W_AMB_CASE_BG` |
| `--dn-accent` | titres, boutons, liens, valeurs mises en avant | `#a0d8ff` | `firmware/desknode/main/dn_ui.c:3996` | *(titre de menu)* |
| `--dn-texte` | le corps du texte | `#c0d8e8` | `firmware/desknode/main/dn_widget.c:657` | `W_COL_SEC` |
| `--dn-eteint` | ce qui est secondaire, absent, ou pas encore su | `#9a9a9a` | `firmware/desknode/main/dn_widget.c:652` | `W_COL_ABSENTE` |
| `--dn-trait` | bordures, séparateurs, cadres | `#33404a` | `firmware/desknode/main/dn_ui.c:4576` | *(trait de courbe)* |
| `--dn-avertissement` | ce qui demande un geste, sans être cassé | `#ffb020` | `firmware/desknode/main/dn_widget.c:654` | `W_COL_SIMULEE` |
| `--dn-alerte` | le fond des blocs d'échec | `#7f0000` | `firmware/desknode/main/dn_ui.c:2975` | *(écran d'alerte)* |

> 🎯 **ANNOTÉ ET DATÉ LE 2026-09-10 (`dn7-4`) — ⛔ AUCUNE COLONNE DE LA TABLE N'EST TOUCHÉE,
> ET ⛔ AUCUN JETON N'EST AJOUTÉ.** **QUATRE** rôles s'élargissent — ⛔ pas deux, et le compte est
> corrigé ici plutôt qu'ailleurs. Ce sont les quatre jetons que les règles d'état des deux
> sélecteurs de langue (`#sec-langue`, `#sec-langue-dalle`) emploient :
>
> | jeton | rôle élargi | où |
> |---|---|---|
> | `--dn-accent` | **fond** de la position active, et sa bordure | position **active** |
> | `--dn-fond` | **couleur de texte** posée sur cet aplat | position **active** |
> | `--dn-trait` | **fond ET bordure** de la position active **désarmée** | pendant `langueEnVol` |
> | `--dn-eteint` | **texte** de la position active désarmée | pendant `langueEnVol` |
>
> ⚠️ **CE QUE CE CHANGEMENT REMPLACE, NOMMÉ PLUTÔT QU'EFFACÉ** : ces deux règles portaient
> `border-color: var(--dn-texte); color: var(--dn-texte);` — c'est-à-dire **rigoureusement les
> mêmes déclarations que `button:hover:enabled`**. « Sélectionné » et « survolé » étaient donc
> **indiscernables**, et l'écart au repos tenait à **deux teintes voisines** (`--dn-accent`
> ⇄ `--dn-texte`). Coût mesuré **en séance le 2026-09-10** : l'owner a lu une position pour
> l'autre. ⇒ l'aplat est une différence de **forme**, ⛔ pas de teinte.
>
> 🔴 **LES RAPPORTS DE CONTRASTE, CALCULÉS ⛔ PAS ESTIMÉS.** Ils se calculent depuis les valeurs
> de la table ci-dessus (WCAG 2.x, luminance relative), **sans navigateur** — c'est la seule part
> de « lisibilité » qu'un chiffre peut tenir, et elle est donc écrite :
>
> | paire | valeurs | rapport | lecture |
> |---|---|---|---|
> | texte actif sur son aplat | `#000000` sur `#a0d8ff` | **13,76:1** | ≥ 7:1 (AAA) |
> | texte au repos sur le fond | `#a0d8ff` sur `#000000` | **13,76:1** | ≥ 7:1 (AAA) |
> | aplat actif contre le fond de page | `#a0d8ff` / `#000000` | **13,76:1** | la forme se voit |
> | texte désarmé sur son aplat | `#9a9a9a` sur `#33404a` | **3,78:1** | composant **inactif** |
> | aplat désarmé contre le fond de page | `#33404a` / `#000000` | **1,97:1** | ⚠️ faible |
>
> ⚠️ **CE QUE CES CHIFFRES ⛔ NE DISENT PAS.** *(1)* Le **3,78:1** du cas désarmé est **sous** le
> minimum 4,5:1 de WCAG 1.4.3 — et ce critère **exempt explicitement** le texte d'un composant
> d'interface **inactif**. Le choix est donc **assumé et daté**, ⛔ pas ignoré : le rôle « éteint »
> est celui que la dalle emploie pour *« on ne sait pas »*, et le remplacer par un jeton plus clair
> ferait mentir le rôle. *(2)* Le **1,97:1** de l'aplat désarmé contre le fond de page est faible :
> ce qui distingue la position active désarmée d'une position inactive désarmée est **l'aplat
> lui-même**, et il est sourd. ⇒ ce que ces chiffres tiennent, c'est le **contraste** ; ⛔ ils ne
> disent **pas** que l'œil reconnaît « la position choisie » d'un coup d'œil. Cette part-là se
> ferme **à l'œil de l'owner**, sur la page servie, et elle ⛔ **n'était pas relevée** à cette date.
>
> ⛔ **Et ça ne coûte aucune couleur** : les quatre jetons sont **déjà déclarés dans la table
> ci-dessus**, et `tools/verif_installeur_dn71.py` continue de garder l'égalité **dans les deux
> sens**. ⚠️ Ce que `(c19)` ⛔ **ne** garde **pas** : le **NOM** d'une propriété personnalisée —
> `var(--dn-accnt)` ne serait déclaré nulle part et disparaîtrait **en silence** au rendu. C'est
> `tools/verif_placement_dn74.py (c13)` qui confronte les noms employés à ceux de `:root`.

## Pourquoi ces sept-là, et ⛔ pas d'autres

- **Le fond est un noir pur, et c'est la dalle qui le dit.** `W_AMB_CASE_BG` vaut `0x000000` :
  l'aplat de case en régime Ambient. Sur un écran de bureau ce noir n'est pas un choix de
  mode sombre à la mode, c'est **la couleur que la dalle a réellement** quand elle est posée
  sur un bureau, de nuit.
- **L'accent est le plus employé du firmware**, ⛔ pas le plus joli : `lv_color_hex(0xa0d8ff)`
  apparaît **six fois** dans `dn_ui.c` — titre du menu, en-tête, barre de date, libellé de
  case, titre de détail, titre de l'écran de démarrage. C'est **le bleu de DeskNode** par la
  mesure, ⛔ pas par la préférence.
- **Les deux gris sont des rôles, ⛔ pas des nuances.** `W_COL_SEC` est le texte secondaire,
  `W_COL_ABSENTE` est *« on ne sait pas »*. La page s'en sert exactement pareil : une valeur
  qu'elle n'a pas encore mesurée s'écrit dans le gris qui, sur la dalle, veut déjà dire ça.
- **L'avertissement est celui du régime SIMULÉ.** Sur la dalle, `W_COL_SIMULEE` signale une
  grandeur qui n'est pas mesurée. Sur la page, il signale la même famille de fait : *tu as
  quelque chose à faire avant que ce soit vrai* — l'écart déclaré, le navigateur qui n'a pas
  l'accès série, l'adresse qui ne convient pas.
- **L'alerte est un FOND, ⛔ pas un texte, et le firmware la traite pareil.** À
  `dn_ui.c:2975`, `0x7f0000` est posé en `bg_color` d'un écran entier. Écrit en couleur de
  texte sur du noir, il serait illisible ; la page le garde donc en fond, avec le texte
  ordinaire par-dessus.

## Comment cette liste se re-mesure

```bash
# la valeur citée est-elle vraiment à la ligne citée ?
sed -n '1425p' firmware/desknode/main/dn_widget.c
sed -n '3996p;4576p;2975p' firmware/desknode/main/dn_ui.c
sed -n '652p;654p;657p' firmware/desknode/main/dn_widget.c

# l'accent dominant, compté plutôt qu'affirmé
grep -c 'lv_color_hex(0xa0d8ff)' firmware/desknode/main/dn_ui.c

# les deux sens de l'égalité page ⇄ déclaration
python3 tools/verif_installeur_dn71.py
```

⚠️ **Une ligne citée peut bouger** — le firmware vit. C'est **voulu que ça casse** : la gate
relit la ligne citée et rougit si la couleur n'y est plus, ce qui force à re-relever la
source au lieu de laisser la citation pourrir en silence. ⛔ Une source qu'on ne peut plus
rouvrir n'est pas une source.

Copyright © 2026 Nasbarok. Ce fichier suit la licence du dossier `installeur/`, déclarée
dans [`LICENSING.md`](../LICENSING.md).

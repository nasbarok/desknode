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

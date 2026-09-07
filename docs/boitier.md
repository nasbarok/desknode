# Le boîtier — sa place, son format, sa licence, et ce qu'on ne sait pas de son impression

Cette page dit **où vont les plans du coffrage imprimable de DeskNode**, **sous quelle forme**,
**sous quelle licence**, et **ce qu'on ne sait pas encore** de son impression. Elle existe parce que
ce dépôt **promettait déjà** ces plans à son lecteur — la table de [LICENSING.md](../LICENSING.md)
licencie les *enclosure plans*, et [`roadmap.md`](roadmap.md) annonce *« the 3D-printed case »* —
alors qu'il n'en porte **aucun**. Une promesse que personne ne porte est une dette ; celle-ci est
désormais **écrite, chiffrée et attribuée**.

🔴 **Ce que cette page ⛔ n'est pas : un plan.** Le dessin du coffrage n'a pas commencé et il est
rangé **après la première version publique**. Ce qui est livré ici est **la place, le format, la
licence, la notice et le manque déclaré** — ⛔ pas une pièce à imprimer.

---

## 1. Aucun boîtier n'est obligatoire

DeskNode **fonctionne sans coffrage**. La carte se pose, se branche en USB, s'allume et affiche.
Toutes les mesures publiées par ce dépôt — le bus I²C, les températures, la liaison PC, la veille —
ont été relevées sur un **prototype nu**, posé sur un bureau. Le boîtier n'est ⛔ **ni un prérequis
de fonctionnement, ni une condition de reproduction** : c'est du confort et de la présentation.

⚠️ **Et ça a un prix, écrit ici plutôt que découvert plus tard** : le média qui présentera la
première version montrera **un prototype câblé à nu**. C'est la conséquence assumée du report du
coffrage, ⛔ pas un oubli de tournage.

⛔ **Ce qu'un boîtier ne réparera pas** : il ne change **aucune** valeur mesurée. Il déplacera en
revanche l'air autour de la carte et **le capteur d'ambiance mesure cet air** ; le jour où un
coffrage existe, les relevés de température devront être **re-tirés dedans**, ⛔ pas transposés.

---

## 2. La place, et le format

La place est **`docs/boitier/`** — un sous-répertoire de `docs/`, ⛔ pas un répertoire neuf à la
racine du dépôt. Ce n'est pas un détail de rangement : `docs/` est **déjà** nommé par la licence et
**déjà** couvert par la vérification qui garde les deux sens de cette couverture. Un répertoire
`cad/` ou `plans/` à la racine ferait rougir cette vérification le jour de sa création, et il
faudrait rouvrir la licence pour un dossier vide.

Ce qui s'y dépose, format par format, est écrit dans [`PLANS.md`](boitier/PLANS.md) : `.3mf`,
`.stl`, `.scad`, `.step`, `.stp` et `.f3d`, **avec la règle qu'un maillage seul ne suffit pas** — il
faut au moins une source modifiable, sans quoi personne ne peut adapter la pièce.

### L'état, mesuré le 2026-09-07

| grandeur | valeur mesurée | comment elle se re-mesure |
|---|---:|---|
| plans CAO suivis sous `docs/boitier/` | **0** | `git ls-files docs/boitier`, filtré sur les six extensions ci-dessus |
| plans CAO suivis ailleurs dans le dépôt | **0** | `git ls-files`, même filtre, hors `docs/boitier/` |

⇒ **aucun plan n'est déposé**. La place est prête et **vide**, et cette page le dit plutôt que de
laisser un lecteur chercher.

---

## 3. La licence

Les plans déposés dans `docs/boitier/` sont **CC-BY-SA-4.0**, comme tout `docs/`. Voir
[LICENSING.md](../LICENSING.md).

✅ **Cette licence était acquise avant d'être demandée, et c'est mesuré.** La ligne de table qui
couvre `docs/` nomme déjà les *enclosure plans*, et la phrase de repli du même fichier les nomme une
seconde fois. Poser le dossier sous `docs/` n'a donc demandé **aucune** modification de la licence.
⛔ Ce n'est pas de la chance : c'est la raison pour laquelle la place est là et pas ailleurs.

---

## 4. La notice d'impression — quatre paramètres, quatre fois « non mesuré »

🔴 **Les quatre paramètres sortent NON MESURÉS, et c'est la seule sortie honnête.** Aucun tirage n'a
eu lieu, et il ne peut pas y en avoir : **il n'y a rien à imprimer**. Écrire *« PLA, 0,2 mm, 20 %,
sans supports »* serait plausible, courant, et **faux** au sens de la règle que ce dépôt s'applique
— toute affirmation porte un nombre **ou se déclare non mesurée**. Ce dépôt a déjà payé une source
tierce recopiée sans mesure : elle avait `SDA` et `SCL` inversés.

| paramètre | valeur publiée | disposition — pourquoi elle est vide, et qui la remplira |
|---|---|---|
| **matériau** | ⛔ **non mesuré** | Le matériau se choisit **avec** le dessin : une paroi de 1,6 mm ne reprend pas les mêmes efforts en PLA et en PETG, et la carte chauffe. Rien n'a été imprimé, donc rien n'a été comparé. Porteur : `epic-dn6`, le territoire matériel, encore ouvert. |
| **hauteur de couche** | ⛔ **non mesuré** | Elle se règle sur la hauteur des détails du dessin — congés, filets, empreintes de vis — qui n'existent pas. La publier maintenant reviendrait à **transposer** le réglage d'un autre boîtier, ce que ce dépôt s'interdit. Porteur : `epic-dn6`. |
| **remplissage** | ⛔ **non mesuré** | Il dépend des efforts que la pièce reprend : le poids de la carte, l'appui du doigt sur la dalle tactile, la tenue des inserts. Aucun de ces efforts n'a été mesuré, et aucun ne peut l'être sans pièce. Porteur : `epic-dn6`. |
| **supports** | ⛔ **non mesuré** | Ils dépendent des porte-à-faux du dessin. *« Sans supports »* est la réponse la plus fréquente, et c'est précisément pour ça qu'on ⛔ ne l'écrit pas avant de l'avoir vue sur une pièce réelle. Porteur : `epic-dn6`. |

⚠️ **Ce que ça coûte, écrit** : quelqu'un qui imprimerait un boîtier de DeskNode demain n'aurait
**aucun réglage de départ** venant de ce dépôt. C'est le prix du report du coffrage, ⛔ pas un oubli
— et le manque est **porté** au registre des reports, avec la clé nommée ci-dessous.

⚠️ **À quoi cette table ressemblera quand elle sera vraie** : chaque case *« valeur publiée »*
portera un nombre **et** un renvoi vers le relevé qui le produit, dans `mesures/`. Une valeur sans
renvoi reste refusée : la vérification de cette page rougit sur un chiffre qui ne cite pas sa
mesure.

---

## 5. Ce qui n'a PAS été essayé

⛔ Cette liste n'est ⛔ pas un aveu de faiblesse : c'est la moitié utile de la notice.

- **Aucune impression.** Zéro tirage, sur zéro imprimante. ⛔ Ni FDM, ni résine.
- **Aucun essai de matière.** PLA, PETG, ABS, ASA : aucun n'a été comparé sur cette carte.
- **Aucune tenue en température.** La carte chauffe en régime ; ce que ça fait à une pièce en PLA
  dans un volume fermé n'a **jamais** été mesuré, et le PLA est précisément la matière qui s'en
  soucie le plus.
- **Aucune mesure d'ambiance en volume fermé.** Le capteur d'ambiance mesure l'air **autour** de la
  carte ; toutes les valeurs publiées le sont **à l'air libre**.
- **Aucun essai de fixation.** Ni inserts, ni vis autotaraudeuses, ni clips : le choix se fera avec
  le dessin.
- **Aucune découpe validée** pour l'USB, ni pour les deux points d'accès au bus I²C — leurs
  positions se lisent dans [`cablage.md`](cablage.md), mais rien n'a été confronté à une pièce.
- **Aucune vérification de la dalle tactile sous cadre.** Un cadre qui déborde sur la zone active
  se sent au doigt ; ⛔ personne ne l'a essayé.

---

## 6. Le manque, déclaré — et son porteur

Le dessin du coffrage **n'existe pas**, il **appartient à l'owner**, et il est rangé **après la
première version publique**. Ce n'est ⛔ ni un blocage ni un oubli : c'est une décision datée, et ce
qu'elle laisse ouvert est écrit ici.

| ce qui manque | qui le porte | ce que ça débloque |
|---|---|---|
| le dessin lui-même, et donc les quatre paramètres du §4 | porteur : `epic-dn6` — le territoire matériel, `backlog` au 2026-09-07 | la notice devient chiffrée, et cette page cesse de dire « non mesuré » |
| le re-tournage du média une fois le boîtier posé | porteur : `epic-dn8` — la vitrine, `backlog` au 2026-09-07 | la première version pourra montrer autre chose qu'un prototype nu |

⚠️ **Le second porteur n'est ⛔ pas décoratif** : la vitrine **dépend** de cette marche, et pas
l'inverse. Tant que le boîtier n'est pas posé, le média montre du câblage à nu — le choix
(l'assumer, ou re-tourner sans boîtier) appartient à la vitrine, ⛔ pas à cette page.

Le manque est aussi inscrit au registre des reports du dépôt de planification, avec sa preuve et sa
date, sous la clé `dn6-4` — que [`roadmap.md`](roadmap.md) définit.

---

## 7. Comment ces nombres se re-mesurent

⛔ Aucun chiffre de cette page n'est à croire sur parole. Les deux comptes du §2 sont **rejoués à
chaque passe de vérification** et confrontés à l'arbre suivi.

```
python3 tools/verif_boitier_dn64.py                  # le verdict : n OK, 0 KO
python3 tools/verif_boitier_dn64.py --liste-mutants  # ce que chaque mutant replante
```

⚠️ **Dans un clone, la première commande sort en `4`, et c'est normal.** Deux de ses contrôles
lisent le dépôt de planification, qui est **privé** et n'est jamais cloné à côté du code : elle les
imprime alors `[ ××  ] … ⛔ NON JOUE` avec leur motif, garde tous les autres, et rend **`4`** —
« prérequis absent », ⛔ pas un échec. Un vrai défaut rend **`1`** et l'emporte toujours.

Ce que cette vérification garde, **dans les deux sens** : tant qu'aucun plan n'est déposé, cette
page **doit le dire** ; le jour où un plan arrive, la phrase *« aucun plan n'est déposé »* devient
fausse et la vérification **rougit** — et chaque plan déposé doit être **cité** par cette page. Elle
garde aussi que la place reste **sous `docs/`**, que ce dossier ne porte **que** des
plans, qu'aucun plan ne se dépose **ailleurs**, que les **quatre** paramètres du §4
portent chacun leur disposition, qu'⛔ **aucun** d'eux ne porte une
valeur chiffrée sans citer sa mesure, que la section *« ce qui n'a PAS été essayé »* existe, que le
manque **nomme un porteur**, et que cette page reste **atteignable** depuis
[README.md](../README.md) et depuis [`cablage.md`](cablage.md).

⚠️ **Le compte se prend sur `git ls-files`, ⛔ jamais sur l'arbre de travail** — le relevé de départ
est [`T0-bornes-depart.txt`](../mesures/dn6-4/T0-bornes-depart.txt), et le piège y est chiffré :
`firmware/` porte **6 726** fichiers `.obj` de compilation, non suivis.

⛔ **Ce que cette vérification ne fait pas** : elle ne juge **aucun** dessin, **aucune** cote et
**aucune** imprimabilité. Elle ne sait pas si une pièce sort correctement — ça, c'est un tirage, et
il n'a pas eu lieu.

---

## Licence

Cette page est de la documentation, comme les plans qu'elle attend : **CC-BY-SA-4.0**. Voir
[LICENSING.md](../LICENSING.md).

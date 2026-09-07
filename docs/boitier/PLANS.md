# Ce dossier attend les plans du boîtier — et il est vide, c'est mesuré

Ce dossier est **la place** des plans du coffrage imprimable de DeskNode. Il ne porte aujourd'hui
**aucun plan**, et cette page existe pour le **dire** plutôt que pour faire bouchon : un dossier
peuplé d'un fichier vide et muet donnerait à lire « il y a quelque chose ici » là où il n'y a rien.
C'est exactement le défaut que le reste de ce dépôt combat.

La page qui explique **à quoi sert ce boîtier**, ce qu'il **n'est pas**, et ce qu'on ne sait pas
encore de son impression, est [`boitier.md`](../boitier.md). Celle-ci ne dit que **ce qui se dépose
ici et sous quelle forme**.

---

## Ce qui se dépose ici, et pourquoi chaque format

| extension | ce que c'est | pourquoi elle est acceptée |
|---|---|---|
| `.3mf` | l'échange moderne : maillage **avec** ses unités, son orientation et son plateau | un trancheur l'ouvre sans avoir à deviner l'échelle — le `.stl` fait deviner |
| `.stl` | le maillage nu, sans unité ni orientation | c'est le plus universel, et c'est **le seul** que tous les trancheurs lisent |
| `.scad` | le modèle **paramétrique** OpenSCAD — du texte, qui se lit et se `diff`e | c'est le seul format de cette liste qu'un inconnu peut **modifier** |
| `.step` · `.stp` | l'échange CAO solide, neutre | ce qu'on ouvre dans un autre logiciel que celui qui a dessiné |
| `.f3d` | le projet natif Fusion 360 | il porte l'historique de construction, que l'échange perd |

🔴 **Un maillage seul ne suffit pas, et c'est une règle, ⛔ pas une préférence.** Un `.stl` ou un
`.3mf` s'imprime mais ⛔ **ne se modifie pas** : reprendre 2 mm sur une paroi demande de tout
redessiner. Le jour où des plans arrivent ici, ils arrivent avec **au moins une source
modifiable** — `.scad`, `.step` ou `.f3d`. Sinon, ce dépôt publierait un objet que personne ne peut
adapter à sa carte, ce qui est le contraire de ce qu'il promet.

⚠️ **Ce dossier ne porte que des plans.** Les photographies du montage vivent dans `docs/cablage/`,
indexées par leur propre page, et ce qu'elles montrent se lit dans [`cablage.md`](../cablage.md) ;
les notes de mesure vivent dans `hardware/`. Un fichier déposé ici qui n'est pas un plan est un
fichier mal rangé — et la vérification le **refuse** : tout ce qui vit ici est soit cette page,
soit l'un des six formats ci-dessus.

---

## L'état, mesuré le 2026-09-07

| grandeur | valeur mesurée | comment elle se re-mesure |
|---|---:|---|
| plans CAO suivis sous `docs/boitier/` | **0** | `git ls-files docs/boitier`, filtré sur les six extensions ci-dessus |
| plans CAO suivis ailleurs dans le dépôt | **0** | `git ls-files`, même filtre, hors `docs/boitier/` |

⇒ **aucun plan n'est déposé** dans ce dépôt, nulle part. La place existe, elle est licenciée, son
format est écrit — le dessin, lui, n'a pas commencé, et [`boitier.md`](../boitier.md) dit **qui le
porte**.

⚠️ **Le compte se prend sur les fichiers SUIVIS, ⛔ jamais sur l'arbre de travail.** Mesuré le même
jour : `firmware/` porte **6 726** fichiers `.obj` non suivis, produits par la compilation. Un
détecteur de plans qui lirait le disque **et** rangerait `.obj` parmi les formats CAO annoncerait
**6 726 plans** là où il y en a zéro. `.obj` ⛔ n'est **pas** un format de plan dans ce dépôt, et le
témoin qui le prouve est `tools/fixtures/dn64-temoin-obj.obj` : il est **vu** par la vérification,
et il en est **écarté**.

---

## Ce que ce dossier n'est pas

- ⛔ Ce n'est **pas** une promesse de date. La création du coffrage est rangée **après la première
  version publique** ; ce dossier est ce qui l'attend, ⛔ pas ce qui l'annonce.
- ⛔ Ce n'est **pas** un dossier de rendus ou de captures : une image du boîtier n'est pas un plan.
- ⛔ Ce n'est **pas** l'endroit où l'on discute du dessin. Ce qui est décidé, ce qui ne l'est pas et
  ce qui n'a jamais été essayé se lit dans [`boitier.md`](../boitier.md).

---

## Licence

Les plans déposés ici sont de la documentation au sens de ce dépôt : **CC-BY-SA-4.0**, comme le
reste de `docs/`. La ligne qui les couvre existait **avant** ce dossier — elle licencie déjà les
*enclosure plans*. Voir [LICENSING.md](../../LICENSING.md).

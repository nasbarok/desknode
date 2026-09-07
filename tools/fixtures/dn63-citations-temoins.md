# Fixture `dn6-3` — les TEMOINS NEGATIFS de `tools/verif_photos_dn63.py`

⛔ **Ce fichier n'est PAS de la documentation.** C'est une **fixture** : il existe pour qu'un
contrôle de `tools/verif_photos_dn63.py` rencontre, **à chaque passe**, un jeton qu'il doit
**ÉCARTER**. ⛔ Ne rien y ajouter qui ressemble à une citation de photo, et ⛔ ne pas le déplacer.

## Le témoin de `(c5)` — un nom d'image qui n'appartient PAS à `docs/cablage/`

`install_01.jpg`

Ce nom est cité **entre accents graves, comme un nom nu**. Il ne suit **pas** la convention de
`docs/cablage/` (`AAAA-MM-JJ_HHMM-<slug>.jpg`), et le fichier **n'est pas au dépôt** : c'est une
photo que l'owner a envoyée et qui n'a jamais été versée.

🔴 **Ce que le témoin prouve, et pourquoi il vit ICI.** Une gate qui mettrait « tout `*.jpg` cité »
en population rougirait dessus — un **faux KO sur de la prose juste**. `(c5)` vérifie donc les
**deux** sens : le jeton est **VU**, et il est **ÉCARTÉ**. Une branche « ⛔ JAMAIS VU » distingue
l'instrument mort du contrôle satisfait.

⚠️ **Il était ancré sur le journal de mesure du matériel, et c'était une dépendance FRAGILE.**
Mesuré le 2026-09-07 : ce nom n'y apparaissait que **deux fois**, dans un seul fichier — un fichier
dont la correction est le travail d'une **autre marche vivante**, et que le périmètre de `dn6`
interdit d'écrire. Le jour où cette marche passe, `(c5)` serait sorti « ⛔ JAMAIS VU » et
**personne n'aurait eu le droit de le réparer**. ⇒ le témoin vit désormais dans une fixture que la
marche qui le lit **possède**.

⚠️ Le témoin de `(c4)` — la citation **tronquée** — ⛔ n'a **pas** besoin d'être ici : il est vu
dans **quatre** fichiers, dont `README.md`, qui n'appartient à aucune marche en vol.

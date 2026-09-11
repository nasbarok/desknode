# `dn8-1` — le relevé de livraison : le **COMPTE** de chaque gate, avant et après

> **Date** : 2026-09-11 · **arbre d'entrée** : `desknode` `1920f178f607e68751611f2cc6ea79c0e741c536`,
> vérifié **propre** · **cockpit** : `compagnon_project` `6c1dfcb`.

## Pourquoi ce fichier porte un COMPTE et ⛔ pas une couleur

**Une gate déjà rouge absorbe un KO de plus sans changer de couleur.** Le dépôt en a
exactement une — `verif_dossier_dn415.py`, à **23 OK / 10 KO**, rouge **pré-existant**,
⛔ pas de cette marche. Un relevé qui dirait *« 1 rouge avant, 1 rouge après »* serait
vrai et ⛔ ne prouverait rien.

⚠️ **Et un relevé gate par gate est AVEUGLE à ce qui n'est pas une gate.** La dernière
section relève donc aussi les outils que ⛔ **aucune** gate ne garde.

⚠️ **Cinq gates ne PUBLIENT aucun couple `N OK / M KO`** : elles impriment un verdict en
prose (`✅ TOUT TIENT.`). Pour celles-là le compte est **DÉRIVÉ** des marqueurs de ligne,
et la colonne *source* le dit. Un compte dérivé se compare à un compte dérivé ; ⛔ il ne
se compare pas à un compte publié.

**Invocation** : identique à `bash tools/run_gates.sh` **sans** `--cockpit` (le chemin
CI/défaut) — aucune gate ne reçoit d'argument. Brut : `T0-borne-entree.txt`,
`T3-borne-arrivee.txt`.

## Le tableau

| gate | T0 (entrée) | T3 (arrivée) | écart | source |
|---|---|---|---|---|
| `verif_affiliation_dn65.py` | 23 OK / 0 KO | 23 OK / 0 KO | inchangé | publie |
| `verif_banc_langue_dn73.py` | 45 OK / 0 KO | 45 OK / 0 KO | inchangé | publie |
| `verif_bme680_retard_dn45.py` | 15 OK / 0 KO | 15 OK / 0 KO | inchangé | publie |
| `verif_boitier_dn64.py` | 29 OK / 0 KO | 29 OK / 0 KO | inchangé | publie |
| `verif_bom_dn61.py` | 24 OK / 0 KO | 24 OK / 0 KO | inchangé | publie |
| `verif_cablage_dn62.py` | 37 OK / 0 KO | 37 OK / 0 KO | inchangé | publie |
| `verif_campagne_dn440.py` | 60 OK / 0 KO | 62 OK / 0 KO | **OK +2 · KO +0** | publie |
| `verif_campagne_dn56.py` | 8 OK / 0 KO | 8 OK / 0 KO | inchangé | publie |
| `verif_courbe_dn413.py` | 58 OK / 0 KO | 58 OK / 0 KO | inchangé | publie |
| `verif_cumul_ambient_dn45.py` | 23 OK / 0 KO | 23 OK / 0 KO | inchangé | publie |
| `verif_d4_nvs_dn45.py` | 6 OK / 0 KO | 6 OK / 0 KO | inchangé | publie |
| `verif_decoupe_horloge_dn418.py` | 7 OK / 0 KO | 7 OK / 0 KO | inchangé | derive |
| `verif_demarrage_dn443.py` | 58 OK / 0 KO | 58 OK / 0 KO | inchangé | publie |
| `verif_dossier_d5_dn45.py` | 12 OK / 0 KO | 12 OK / 0 KO | inchangé | publie |
| `verif_dossier_dn415.py` | 23 OK / 10 KO | 23 OK / 10 KO | inchangé | publie |
| `verif_flash_dn72.py` | 30 OK / 0 KO | 30 OK / 0 KO | inchangé | publie |
| `verif_harnais_dn413.py` | 22 OK / 0 KO | 22 OK / 0 KO | inchangé | publie |
| `verif_harnais_dn81.py` | — | 25 OK / 0 KO | 🆕 **NOUVELLE** | publie |
| `verif_hist_dn413.py` | 56 OK / 0 KO | 56 OK / 0 KO | inchangé | publie |
| `verif_installeur_dn71.py` | 28 OK / 0 KO | 28 OK / 0 KO | inchangé | publie |
| `verif_instruments_dn423.py` | 163 OK / 0 KO | 163 OK / 0 KO | inchangé | publie |
| `verif_journal_soak_dn45.py` | 26 OK / 0 KO | 26 OK / 0 KO | inchangé | publie |
| `verif_langue_dalle_dn73.py` | 61 OK / 0 KO | 61 OK / 0 KO | inchangé | publie |
| `verif_langues_dn442.py` | 31 OK / 0 KO | 31 OK / 0 KO | inchangé | publie |
| `verif_ledger_dn416.py` | 35 OK / 0 KO | 36 OK / 0 KO | **OK +1 · KO +0** | publie |
| `verif_licences_dn52.py` | 34 OK / 0 KO | 34 OK / 0 KO | inchangé | publie |
| `verif_lissage_dn45.py` | 21 OK / 0 KO | 21 OK / 0 KO | inchangé | publie |
| `verif_miroir_horloge_dn418.py` | 18 OK / 0 KO | 18 OK / 0 KO | inchangé | derive |
| `verif_page_dn722.py` | 56 OK / 0 KO | 56 OK / 0 KO | inchangé | publie |
| `verif_paliers_dn441.py` | 42 OK / 0 KO | 42 OK / 0 KO | inchangé | publie |
| `verif_photos_dn63.py` | 28 OK / 0 KO | 28 OK / 0 KO | inchangé | publie |
| `verif_placement_dn74.py` | 42 OK / 0 KO | 42 OK / 0 KO | inchangé | publie |
| `verif_polices_dn440.py` | 11 OK / 0 KO | 11 OK / 0 KO | inchangé | publie |
| `verif_preconditions_dn76.py` | 52 OK / 0 KO | 52 OK / 0 KO | inchangé | publie |
| `verif_prerequis_dn75.py` | 47 OK / 0 KO | 47 OK / 0 KO | inchangé | publie |
| `verif_rebouclage_dn45.py` | 30 OK / 0 KO | 30 OK / 0 KO | inchangé | publie |
| `verif_reprise_horloge_dn418.py` | 44 OK / 0 KO | 44 OK / 0 KO | inchangé | derive |
| `verif_selection_dn49.py` | 70 OK / 0 KO | 70 OK / 0 KO | inchangé | publie |
| `verif_serie_dn412.py` | 50 OK / 0 KO | 50 OK / 0 KO | inchangé | publie |
| `verif_source_lhm_dn48.py` | 47 OK / 0 KO | 47 OK / 0 KO | inchangé | derive |
| `verif_sr03.py` | 0 OK / 0 KO | 0 OK / 0 KO | inchangé | derive |
| `verif_temoin_filtre_dn447.py` | 5 OK / 0 KO | 5 OK / 0 KO | inchangé | publie |
| `verif_veille_dn33.py` | 267 OK / 0 KO | 267 OK / 0 KO | inchangé | publie |
| `verif_verrou_lvgl_dn413.py` | 60 OK / 0 KO | 60 OK / 0 KO | inchangé | publie |
| `verif_xip_dn422.py` | 10 OK / 0 KO | 10 OK / 0 KO | inchangé | publie |
| **TOTAL** | **1814 OK / 10 KO** | **1842 OK / 10 KO** | **OK +28 · KO +0** | |

**Gates au glob `tools/verif_*.py` : 44 ⇒ 45.** ⛔ Aucune gate perdue.

⚠️ **LE TABLEAU CI-DESSUS EST LE TIR T3/T4, ⛔ IL N'EST PAS RÉÉCRIT.** La revue de
code a fait passer `verif_harnais_dn81.py` de **25** à **28 OK / 0 KO** (+1 contrôle,
+2 mutants) ⇒ le TOTAL d'arrivée se lit **1845 OK / 10 KO**, ⛔ pas 1842. Les 44 autres
gates ont été **re-tirées après le correctif** et sont **inchangées au caractère près**
— `verif_dossier_dn415.py` compris, toujours à **23 OK / 10 KO**. ⛔ Le chiffre
d'origine est daté, ⛔ pas effacé.
🎯 **ΔKO = 0 sur les 45 gates, gate par gate.** ⛔ Aucune gate ne perd un OK.

### Les trois gates qui bougent, et ce qu'elles ont gagné

| gate | écart | ce que c'est |
|---|---|---|
| `verif_harnais_dn81.py` | 🆕 **28 OK / 0 KO** | la gate neuve (`AC8.1.1`, `AC8.1.3`, `AC8.1.4`). ⚠️ ~~25~~ **28** depuis la revue de code : +1 contrôle (la réciproque cibles/identifiants) et +2 mutants (`z`, la région `grep` pure). Le chiffre d'origine est **daté, ⛔ pas effacé** |
| `verif_ledger_dn416.py` | **+1 OK** | **UN SEUL** contrôle ajouté — l'exception nommée à la frontière de l'epic (`AC8.1.2`) |
| `verif_campagne_dn440.py` | **+2 OK** | les deux mutants `Y1`/`Y2` qui gardent ce contrôle. ⚠️ Elle l'avait **épinglé comme nu** (`GARDÉS PAR RIEN : 1`) avant qu'ils n'existent |

## Les outils qui ne sont **PAS** des gates

⛔ Un changement a déjà cassé un outil dont la documentation publie les chiffres **sans
que rien ne rougisse**. Ils sont donc relevés à part.

| outil | T0 | T3 |
|---|---|---|
| `bash tools/run_gates.sh -h` | `rc=0` | `rc=0` |
| `python3 tools/campagne_ctrl_dn440.py --liste` | `rc=2` (option inconnue — **c'est son comportement**, pas une régression) | `rc=2` |
| `import dn_police, dn_sites, dn_trace` | `rc=0` | `rc=0` |
| `import dn_gates` (le module de `dn8-1`) | `rc=1` — **`Traceback`, le module n'existait pas** | `rc=0`, **8 noms exportés** |
| `python3 -m compileall tools/` | `rc=0` | `rc=0` |

⚠️ La ligne `import dn_gates` est le **témoin négatif** de cette marche : elle était
**rouge** au T0 par construction, et c'est ce qui rend le vert du T3 falsifiable.

## Les cinq ancres `📍` re-routées — ⛔ le texte d'origine n'est pas effacé

Mesure sur les **94 cibles** portées par **86 lignes** d'ancre dans `deferred-work.md`
(⚠️ **87** lignes portent le glyphe ; **une** est de la prose qui le cite entre accents
graves — elle n'est ⛔ pas une ancre). **5 mortes**, **7** trouvables seulement **après
normalisation**.

⚠️ Le cadrage annonçait **48** ancres et **3** mortes. La population a **grandi**. Les deux
chiffres sont écrits, ⛔ aucun n'est effacé.

| ligne | ancre d'ORIGINE (⛔ non effacée) | ancre APRÈS | motif |
|---|---|---|---|
| 6199 | `desknode:mesures/dn4-13/T2-hors-ligne.txt` | `desknode:mesures/dn4-13/` | le fichier n'a **jamais** existé — le dossier, si (7 captures, toutes en `t*-…-2026-08-25.log`) |
| 6315 | `desknode:tools/verif_bom_dn61.py (motif `autoportance`)` | `… (motif `est NOMME dans le document`)` | le mot `autoportance` n'est **nulle part** dans cette gate ; le contrôle que le constat vise s'appelle *« %s est NOMME dans le document »* — c'est **littéralement** le comptage de présence que le constat dénonce |
| 6326 | `desknode:tools/verif_cablage_dn62.py (motif `def citations`)` | `… (motif `RE_CITATION`)` | ⛔ aucune fonction `citations` dans cette gate ; la citation y est portée par la constante `RE_CITATION` |
| 6983 | `desknode:installeur/index.html (motif `Ce que vous allez voir, et ce qu'il faut faire`)` | `… (motif `<section id="sec-suite">`)` | la phrase n'est plus sur la page ; la section que le constat désigne, si |
| 7008 | `desknode:installeur/index.html (motif `poste le MEME`)` | `… (motif `id="b-stop"`)` | idem — le constat porte sur **deux boutons pour un effet**, et `#b-stop` est l'un des deux |

⚠️ **Ce que ce re-routage ⛔ ne fait PAS** : il ⛔ ne ferme aucun constat, ⛔ ne change
aucun verdict et ⛔ ne touche à aucune ligne de disposition `⇒ […]`. Il rend **l'adresse**
atteignable, rien d'autre. Les cinq entrées restent **OUVERTES**, avec leur porteur
inchangé.

## Ce que la marche a laissé ouvert

- 🔴 **Les 101 copies / 57 implémentations des 44 gates ⛔ NE SONT PAS TOUCHÉES.** La gate
  neuve les **inventorie et les imprime à chaque passe**, ⛔ jamais en KO. Porteur :
  `epic-dn4` (l'hygiène des 44 gates est son territoire, et la frontière de `epic-dn8` est
  explicite). ⚠️ Un inventaire imprimé est falsifiable — il bouge quand l'arbre bouge ; un
  silence ne l'est pas.
- ⚠️ **Le périmètre `dn8` dépend d'une CONVENTION DE NOM** (`tools/*dn8*.py`). Une gate de
  `dn8` nommée autrement en sortirait **EN SILENCE**. `(c0)` rougit si le périmètre est
  vide — ⛔ il ne peut pas dire ce qu'il ne voit pas.
- ⚠️ **`(c2)` cherche les motifs d'ancre EN TEXTE**, y compris dans des fichiers HTML, CSS
  et PowerShell : ⛔ aucun parseur. C'est déclaré en propre par `AVEUGLEMENT_HTML` et
  `AVEUGLEMENT_POWERSHELL`, et ces déclarations sont **imprimées**, ⛔ pas seulement écrites.
- ⚠️ **Le chemin CI et le chemin local ⛔ ne jouent PAS le même contrôle.** `yaml` n'est pas
  stdlib et la CI s'interdit `pip install` : en CI le contrôle de parse se **déclare non
  joué** avec son motif. ⚠️ Cela reste sans effet pratique tant que la gate du ledger y est
  **`NON_JOUABLE`** (cockpit privé, `rc=4`) — mais ⛔ ce n'est pas une raison de ne pas
  l'écrire.

## T4 — la CONFIRMATION, sur l'arbre FINAL

⚠️ **Pourquoi une quatrième passe.** Deux fichiers de relevé (`T3-borne-arrivee.txt` et
celui-ci) ont été **écrits pendant** la passe `T3` : un tir à cheval sur une mutation de
l'arbre rend un chiffre faux **sans que rien ne rougisse**. ⇒ la passe a été **rejouée
entière** sur l'arbre final, et les deux sont comparées — ⛔ l'absence d'effet est
**mesurée**, ⛔ pas supposée.

| | gates | OK | KO |
|---|---|---|---|
| **T3** | 45 | 1842 | 10 |
| **T4** (arbre final) | 45 | 1842 | 10 |

🎯 **Gates dont le compte bouge entre T3 et T4 : AUCUNE.**

### `bash tools/run_gates.sh` sur l'arbre final

```
BILAN : 43 VERTE, 1 ROUGE, 1 NON-JOUABLE sur 45 gates (645s)
appariement --cockpit : 0 divergence(s) entre la detection LARGE et la detection ETROITE
[ROUGE      ] tools/verif_dossier_dn415.py    rc=1    ← 23 OK / 10 KO, rouge PRE-EXISTANT
[NON-JOUABLE] tools/verif_sr03.py             rc=2    (attendu) temoin absent
[  temoin  ] tools/verif_harnais_dn81.py      le cockpit est present ⇒ la gate est JOUEE
[VERTE      ] tools/verif_harnais_dn81.py     rc=0
```

⚠️ **`rc=1` du script, et c'est le rouge PRÉ-EXISTANT** — `verif_dossier_dn415.py`, à
**23 OK / 10 KO**, inchangé au caractère près entre T0 et T4. ⛔ Une gate déjà rouge
absorbe un KO de plus sans changer de couleur : c'est son **COMPTE** qui le dit, et il
n'a pas bougé.

### Le chemin CI, simulé

| tir | rc | attendu |
|---|---|---|
| `env HOME=/tmp/nohome python3 tools/verif_harnais_dn81.py` | **4** | 4 — prérequis absent, déclaré `NON_JOUABLE` |
| `env HOME=/tmp/nohome python3 tools/verif_ledger_dn416.py` | **4** | 4 — inchangé par cette marche |
| `env HOME=/tmp/nohome PYTHONPATH=<sans yaml> …verif_ledger_dn416.py` | **4** | 4 — ⛔ **aucun `Traceback` à l'import**, l'import est gardé |

### Les codes de sortie de la gate neuve

| tir | rc |
|---|---|
| arbre sain, cockpit présent | **0** (`28 OK / 0 KO`) |
| `--cockpit /nonexistent`, **sans** `--mutant` | **4** (prérequis absent, motif + remède imprimés) |
| cockpit absent, **avec** `--mutant` | **1** — voir la section suivante |
| `--mutant 99` (inconnu) | **2** (erreur d'appel, ⛔ pas un défaut) |
| `--mutant 3` sur un arbre où son ancre a disparu | **3** (mutant **PÉRIMÉ**, ⛔ pas un vert) |
| `--mutant 1`…`15` | **1**, **un seul KO**, **sur le contrôle déclaré en cible** |

## Ce que la revue de code a trouvé, et qui est fermé

🔴 **La suite était ROUGE EN CI, et ⛔ aucune de mes passes ne pouvait le voir.**
`tools/verif_campagne_dn56.py` ⛔ n'est **pas** dans `NON_JOUABLES` : elle **tourne en
CI**, découvre à l'AST toute gate déclarant `--liste-mutants`, joue chacun de ses mutants
et classe tout `rc != 1` en *« NE ROUGISSENT PLUS »*. Sur un runner (cockpit absent) mes
13 mutants rendaient **`rc=4`**.

| tir | parent `1920f17` | à ma livraison | après le correctif |
|---|---|---|---|
| `env HOME=<vide> python3 tools/verif_campagne_dn56.py` | `8 OK / 0 KO` | **`7 OK / 1 KO`** | `8 OK / 0 KO` |

⇒ **en mode mutant, un prérequis absent est un ROUGE NOMMÉ, ⛔ pas un `4`** — la
convention que `verif_temoin_filtre_dn447.py` publie déjà. ⛔ Le chemin **sans**
`--mutant` garde son `4` : c'est **lui** que la table `NON_JOUABLES` déclare.
⛔ ⛔ **Pas** par les `EXCEPTIONS` de `dn56` : elles sont à **double sens** et
ressortiraient `PERIMEE` partout où le cockpit **est** présent.

⚠️ **Trois autres défauts, tous sur `verif_harnais_dn81.py`, tous avec leur témoin :**

| défaut | ce qu'il valait | le témoin qui le ferme |
|---|---|---|
| **le mutant 9 DÉBRANCHAIT la garde** — son corps entier était un drapeau, ⛔ aucune ancre réécrite, et son libellé prétendait le contraire | en déplaçant l'`append` au-dessus du test de normalisation, `(c2c)` comptait **94** ancres en restant vert **et le mutant sortait rouge quand même** | il réécrit maintenant **le ledger** : tout motif qui ne se trouve qu'après normalisation devient un motif **littéral de sa propre cible** ⇒ `(c2a)`/`(c2b)` restent verts, `(c2c)` rougit |
| **`parse_ou_declare` accordait l'exemption sur un jeton trouvé n'importe où dans le module**, docstrings et commentaires compris — alors que `sujets_de` prenait déjà la précaution symétrique | une région en `grep` pur greffée **à côté** de la région qui parse sortait `(True, True)` : `(c3b)` vert sur un contrôle aveugle | le parseur **et** la charge de l'aveuglement se cherchent **dans le bloc**, littéraux égaux à un jeton déclaré écartés. **Mutant 15** le rejoue : `rc=0` avec l'ancienne recherche, **`rc=1`** avec le correctif — et le **mutant 11 ⛔ ne peut pas** l'atteindre (il remplace sur tout le fichier) |
| **`(z)` avait un consommateur vivant et ⛔ AUCUN tir ne le faisait tomber** : les 13 mutants basculaient un contrôle **sans changer le compte**, et les sorties anticipées passent `anticipee`, qui le désarme par construction | une gate pouvait émettre moins de contrôles qu'annoncé sans que rien ne le dise | **mutant 14** fait **sauter** un contrôle de fond ⇒ `27 émis pour 28 prévus` ⇒ `(z)` rougit |
| **la table `CIBLES` n'était rejouée par personne** — `(c0)` n'assertait que `bool(CIBLES.get(n))`, et la colonne « cible » de `T2` n'était qu'une **capture** | une cible pouvait nommer `c9z`, un identifiant qui n'existe nulle part ; et un contrôle pouvait n'être visé par **aucun** mutant | `(c0)` lit les identifiants **à l'AST** via `dn_gates.ids_par_ast` — qui avait **zéro appelant** — et vérifie **les deux sens**. Témoins : `CIBLES[15]=("c9z")` ⇒ `cible(s) FANTÔME(S)` · `CIBLES[13]=("c3a")` ⇒ `contrôle(s) visé(s) par AUCUN mutant : ['c3c']` |

⚠️ **Un seul identifiant n'est visé par aucun mutant, et c'est déclaré** (`IDS_SANS_MUTANT`) :
`(c0)`, le pré-vol — c'est **lui** qui garde les mutants (cible déclarée, mutant sans effet
⇒ `rc=3`, mutant qui lève ⇒ `rc=1`). Un mutant qui le viserait devrait se saboter lui-même.
Ce qui le garde à la place est le **témoin `rc=3`** relevé dans `T2`, ⛔ pas une promesse.

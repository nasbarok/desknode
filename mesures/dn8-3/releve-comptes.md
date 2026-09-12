# dn8-3 — LE RELEVÉ **AU COMPTE**, gate par gate, AVANT / APRÈS

🔴 **LE COMPTE, ⛔ PAS LA COULEUR.** La seule gate rouge de ce dépôt est à
`23 OK / 10 KO` : **une gate déjà rouge absorbe un KO de plus sans changer de
couleur**. ⇒ ce relevé porte `N OK / M KO`, et ⛔ jamais « verte ».

**Borne d'entrée** : `T0-borne-entree.txt`, `T0-run-gates.txt`, `T0-campagne-dn56.txt`
(2026-09-12, `HEAD = 0fa214d`). **Borne d'arrivée** : `T5-borne-arrivee.txt`,
`T5-run-gates.txt` (2026-09-12).

## 1. Les gates que cette marche TOUCHE

| gate | AVANT | APRÈS | ce qui a bougé |
|---|---|---|---|
| `verif_lhm_ps_dn83.py` | ⛔ n'existait pas | **`19 OK / 0 KO`** · 7,08 s | 🆕 **8 contrôles**, **11 mutants**, joue le pré-vol dans un **vrai `powershell.exe`**, dans les **deux sens** |
| `verif_prerequis_dn75.py` | `47 OK / 0 KO` | **`47 OK / 0 KO`** | l'outil gagne `-Lhm` ; `(c2)(c3)(c11)(c12)(c17)` inchangés |
| `verif_installeur_dn71.py` | `28 OK / 0 KO` | **`28 OK / 0 KO`** | `[ValidateSet]` toujours **unique** dans l'outil |
| `verif_harnais_dn81.py` *(cockpit)* | `28 OK / 0 KO` | **`28 OK / 0 KO`** | son périmètre `dn8` porte désormais **4** fichiers |
| `verif_ledger_dn416.py` *(cockpit)* | `36 OK / 0 KO` | **`36 OK / 0 KO`** | section neuve **en queue**, 6 dispositions, 6 ancres |

## 2. Les gates que cette marche NE TOUCHE PAS — le compte est relu quand même

| gate | AVANT | APRÈS |
|---|---|---|
| `verif_banc_langue_dn73.py` | `81 OK / 0 KO` | **`81 OK / 0 KO`** |
| `verif_entree_dn82.py` | `45 OK / 0 KO` | **`45 OK / 0 KO`** |
| `verif_page_dn722.py` | `56 OK / 0 KO` | **`56 OK / 0 KO`** |
| `verif_langue_dalle_dn73.py` | `61 OK / 0 KO` | **`61 OK / 0 KO`** |
| `verif_preconditions_dn76.py` | `52 OK / 0 KO` | **`52 OK / 0 KO`** |
| `verif_placement_dn74.py` | `42 OK / 0 KO` | **`42 OK / 0 KO`** |
| `verif_flash_dn72.py` | ⛔ non relevé à `T0` | **`30 OK / 0 KO`** |
| `verif_campagne_dn440.py` *(cockpit)* | `62 OK / 0 KO` · 136,30 s | **`62 OK / 0 KO`** |
| `verif_dossier_dn415.py` *(cockpit)* | `23 OK / 10 KO` **PRÉ-EXISTANT** | **`23 OK / 10 KO`** — ⛔ pas un KO de plus |

## 3. Le budget — 🔴 LE VRAI PLAFOND, ET IL A ENCORE FONDU

| | AVANT | APRÈS |
|---|---|---|
| `verif_campagne_dn56.py` | `8 OK / 0 KO` · **483,17 s** · 20 cibles / 634 mutants | **`8 OK / 0 KO`** · **572,87 s** · **21 cibles / 645 mutants** |
| le même, **sans cockpit** (chemin CI) | ⛔ non relevé à `T0` | **`8 OK / 0 KO`** · **472,38 s** |
| `bash tools/run_gates.sh` | **44 VERTE / 1 ROUGE / 1 NON-JOUABLE sur 46** · 719 s | **45 VERTE / 1 ROUGE / 1 NON-JOUABLE sur 47** · 779 s — ⚠️ mesurée **avant** les correctifs de revue du 2026-09-12 ; ⛔ non rejouée ici |

🔴 **LE PRIX DE CETTE MARCHE, CHIFFRÉ** : les **11 mutants** neufs coûtent
**+89,70 s** à `dn56` (483,17 ⇒ **572,87 s**). La marge sous le plafond de **600 s**
passe de **~117 s** à **27,13 s**. ⚠️ **Écrit plutôt que tu : un runner de CI est plus lent que cette
tour**, et le chemin CI mesuré ici (**472,38 s**) l'est *sans* cockpit — il ⛔ ne
dit rien de la vitesse du runner.

⚠️ **UN CHIFFRE DE `T0` MESURAIT UNE ERREUR D'APPEL, ⛔ PAS UN BUDGET** : le
premier tir de `dn56` a reçu `--cockpit`, que la gate ⛔ **n'accepte pas** —
`usage`, **`rc=2`, 0,06 s**. ⛔ Il n'est pas effacé.

## 4. ⚠️ LES OUTILS QUI NE SONT **PAS** DES GATES — relevés aussi

| outil | AVANT | APRÈS |
|---|---|---|
| `node banc_langue_dalle_dn73.mjs` | `BANC : 39 OK, 0 KO` | **`BANC : 39 OK, 0 KO`** |
| `node banc_couverture_dn82.mjs` | `96/100 fonctions · 131/190 blocs` | **`96/100 · 131/190`**, seuils tenus |
| `stub_lhm_dn48.py --port 8085` | refus, `rc=1` | **refus, `rc=1`** |
| `verif_source_lhm_dn48.py` | VERTE dans la passe | **`rc=0`** — ⚠️ elle ⛔ n'imprime **AUCUN** `BILAN` |
| `verif_ledger_dn416.py --manifeste --en-place` | 376 lignes de tableau | **376 lignes**, `rc=0` |
| `tools/dn_agent_tour.ps1` | ⛔ non relevé à `T0` | **ASCII pur** |
| `tools/dn_lhm_tour.ps1` | ASCII pur | **ASCII pur** |
| `tools/dn-agent.bat` | DOS batch · `eol=crlf` livré | **DOS batch · `eol=crlf` livré** · ⛔ 0 accent circonflexe |

## 5. L'EMPREINTE — ⛔ une passe de mesure ne chevauche pas une mutation

- passe **d'entrée** : `a2d37bafe33074a5` **avant et après** ⇒ l'arbre ⛔ n'a pas bougé ;
- passe **d'arrivée** : `8a1518460254c4ef` **avant et après** ⇒ idem.

## 6. ⛔ CE QUE CE RELEVÉ NE DIT **PAS**

- ⛔ **`AC8.3.1` N'EST PAS COCHÉE.** Son instrument est **l'œil de l'owner sur la
  page servie côté Windows**. La prémisse *« le WSL est en NAT ⇒ `localhost` ne
  traverse pas »* est **réfutée** (M6 : `200` depuis Windows vers un serveur lié
  dans WSL) — 🔴 **et ça ne ferme RIEN** : M6 mesure un **client HTTP**, ⛔ pas un
  **navigateur**, et ⛔ surtout pas un **œil**. Le motif `NON RELEVE` **reste** et
  ⛔ n'est pas contourné. **ÉCART DÉCLARÉ**, porteur au ledger.
- ⛔ **`AC8.3.3` N'EST PAS COCHÉE** : le bouton grisé **vu**, l'agent activé
  **constaté par requête**, le plafond `pip` de **900 s** ⛔ jamais confronté, la
  course au logon. **ÉCART DÉCLARÉ**, porteur au ledger.
- ⛔ **La TOUR RÉELLE n'est pas mesurée** : le banc gagne un **hôte PowerShell** et
  un **stub**, ⛔ pas une machine provisionnée.
- 🔴 **Le déploiement de la tour est PÉRIMÉ** — `e3064f0` (2026-08-28), **zéro**
  occurrence de `exit 12` — **et l'agent qui tourne en ce moment en vient**. Une
  séance jouée avant redéploiement mesurerait un produit d'il y a deux semaines :
  un **faux négatif que rien ne signalerait**.
- ⛔ **« 11 mutants, 11 vus rougir » prouve `mutant ⇒ rouge`, ⛔ pas `contrôle ⇒
  couvert`.** La comparaison **cible vue ⇄ cible déclarée** est jouée **à la main**
  dans `T2` — `verif_campagne_dn56.py` ⛔ ne la fait pas. Elle a trouvé **quatre** déclarations inexactes à la
  première rédaction, puis **trois de plus** quand `(c7)`/`(c8)` ont élargi ce que
  les mutants 4, 9 et 10 font rougir — **deux balayages, sept corrections**.
- ⛔ **Ce relevé ne dit rien de la CI** : `gates.yml` tourne sur `ubuntu-latest`,
  où la gate neuve est **NON-JOUABLE déclarée** (`rc=4`). Elle y est **invoquée**,
  ⛔ pas **exercée**.

## 7. 🔴 LA PASSE DE **CONFIRMATION** (`T6`) — l'état LIVRÉ, ⛔ pas celui mesuré à `T5`

> 🔴 **ANNOTÉ LE 2026-09-12 — LE TITRE CI-DESSUS N'EST PLUS VRAI, ET IL EST
> LAISSÉ EN PLACE (`NFR3`).** Une **revue** est passée APRÈS `T6` et a imposé
> **19 correctifs** (la gate, le `.ps1`, `run_gates.sh`, cinq relevés, le
> ledger). ⇒ `T6` ⛔ **ne mesure plus l'arbre livré** — c'est **exactement** le
> défaut que cette section existait pour fermer, re-commis **d'un cran plus
> haut**. La passe qui fait foi est **`T7-revue-correctifs.txt`**, et ses
> chiffres sont ceux des tableaux **§1 à §3** ci-dessus.
> ⚠️ **Les colonnes ci-dessous restent celles de `T6`**, ⛔ pas retouchées : ce
> sont des mesures **datées**, et les réécrire fabriquerait un relevé qui n'a
> jamais eu lieu.

⚠️ **POURQUOI ELLE EXISTE** : entre `T5` et la livraison, **quatre éditions de
prose** ont eu lieu — `T1-powershell-refute.txt` (créé, puis corrigé),
l'annotation de `T5`, `docs/roadmap.md` (`done` ⇒ `in review`), et les deux
annotations du dossier + la docstring de la gate. ⇒ *l'état mesuré à `T5`
n'était plus l'état livré*, et le relevé de `dn8-2` avait justement dû
**déclarer** ce manque. Ici il est **comblé** : `T6` mesure l'arbre **final**.

| | `T5` (arrivée) | **`T6` (confirmation, état livré)** |
|---|---|---|
| `verif_lhm_ps_dn83.py` | `15 OK / 0 KO` · 4,99 s | **`15 OK / 0 KO`** · 4,73 s |
| les 13 gates voisines | au compte de `T0` | **au compte de `T0`** — ⛔ aucune perte |
| `verif_dossier_dn415.py` | `23 OK / 10 KO` | **`23 OK / 10 KO`** — ⛔ pas un KO de plus |
| `verif_campagne_dn56.py` | `8 OK / 0 KO` · 547,35 s | **`8 OK / 0 KO`** · **539,77 s** |
| le même, sans cockpit (CI) | 472,38 s | **474,48 s** |
| `bash tools/run_gates.sh` | 45 V / 1 R / 1 NJ sur 47 · 779 s | **45 V / 1 R / 1 NJ sur 47** · 783 s |
| prérequis absent | — | **`rc=4`, ⛔ 0 ligne `BILAN`**, quatre noms nommés |
| les 9 mutants | 9/9 sur cible (`T2`) | **9/9 sur cible**, `rc=1`, un seul `BILAN` |

### 7 bis. `T7` — LA PASSE QUI FAIT FOI (après les 19 correctifs de revue)

| | `T6` (avant revue) | **`T7` (état livré)** |
|---|---|---|
| `verif_lhm_ps_dn83.py` | `15 OK / 0 KO` · 4,73 s · 6 contrôles / 9 mutants | **`19 OK / 0 KO`** · 7,08 s · **8 contrôles / 11 mutants** |
| les mutants, cible VUE ⇄ DÉCLARÉE | 9/9 | **11/11**, `rc=1`, un `BILAN`, ≥ 1 `[KO ]` |
| prérequis absent, **sans** mutant | `rc=4`, ⛔ 0 `BILAN` | **`rc=4`, ⛔ 0 `BILAN`** |
| prérequis absent, **sous** mutant | `rc=1` + `[KO ]` ⇒ ⛔ satisfaisait `dn56` **à vide** | **`rc=3`** « NON EXERCÉ » · et **0 mutant déclaré** (11 ici) |
| fichier du dépôt illisible | `rc=1`, **1 Traceback, 0 `BILAN`** | **`rc=1`, 0 Traceback, 1 `BILAN`** qui le NOMME |
| `verif_campagne_dn56.py` | `8 OK / 0 KO` · 539,77 s | **`8 OK / 0 KO`** · **572,87 s** · 21 cibles / **645** mutants |
| `verif_prerequis_dn75.py` · `dn71` · `dn76` · `dn74` | au compte de `T0` | **au compte de `T0`** — ⛔ aucune perte |
| ledger · harnais · dossier | 36/0 · 28/0 · 23/10 | **36/0 · 28/0 · 23/10** |

⚠️ **CE QUE `T7` ⛔ NE REJOUE PAS, ET C'EST DÉCLARÉ** : la passe entière
`bash tools/run_gates.sh`. La consigne de revue bornait la vérification aux
**fichiers édités** ; la passe complète est donc **laissée au relecteur**, et le
chiffre publié en §3 (**45 V / 1 R / 1 NJ sur 47**) date d'**avant** les
correctifs. ⛔ Il ⛔ n'est **pas** présenté comme l'état livré.

🔬 **L'EMPREINTE DE `T6`, DIAGNOSTIQUÉE PLUTÔT QUE PROCLAMÉE.** Le couple
avant/après de `T6` a **différé** — et c'était un **artefact de mon instrument** :
`emp()` hashait `mesures/dn8-3/*.txt`, dossier où la passe **écrit ses propres
sorties**. Recalculée **hors sorties de `T6`** : `0befa3a3b2814bce`, identique sur
deux calculs ; les seuls fichiers écrits dans la fenêtre sont `T6-run-gates.txt`
et `T6-verification.txt` ; les fichiers **suivis** restent à `381 insertions,
10 deletions`. ⇒ **l'arbre ⛔ n'a pas bougé.** Détail : `T6`, annotation (B).

## 8. ⚠️ DES VERDICTS FAUX, TOUS TROUVÉS EN RE-MESURANT — ⛔ AUCUN EN RELISANT

Cette marche a produit **plusieurs** verdicts faux, et ⛔ **pas un seul** n'a été
trouvé par une relecture. Ils sont écrits parce qu'ils forment **un motif**, et
que le motif est le sujet même de la marche :

⇒ **LE COMPTE EST TENU EN UN SEUL ENDROIT** :
`mesures/dn8-3/FAUX-VERDICTS-LE-COMPTE.md`. ⛔ Il n'est **pas recopié ici** :
un compte écrit à cinq endroits se périme à la première addition.


### 7 ter. `T8` — LA PASSE ENTIÈRE SUR L'ÉTAT LIVRÉ

`7 bis` déclarait que `T7` ⛔ **ne rejouait pas** `bash tools/run_gates.sh`, et que
le chiffre de §3 datait d'**avant** les correctifs. **C'est joué, le 2026-09-12 :**

| | `T0` | `T6` (avant revue) | **`T8` (état livré)** |
|---|---|---|---|
| `bash tools/run_gates.sh` | 44 V / 1 R / 1 NJ sur **46** · 719 s | 45 V / 1 R / 1 NJ sur **47** · 783 s | **45 V / 1 R / 1 NJ sur 47** · 814 s |
| la seule ROUGE, **au compte** | `23 OK / 10 KO` | `23 OK / 10 KO` | **`23 OK / 10 KO`** — ⛔ pas un KO de plus |
| la NON-JOUABLE | `verif_sr03.py` (témoin absent) | idem | **idem** |
| `verif_lhm_ps_dn83.py` dans la passe | ⛔ n'existait pas | VERTE, témoin résolu | **VERTE**, `rc=0`, 7 s, témoin résolu ⇒ **JOUÉE** |
| `verif_campagne_dn56.py` dans la passe | — | — | **VERTE `rc=0` · 569 s** (plafond 600) |
| ledger · harnais · tracker | 36/0 · 28/0 · parse | 36/0 · 28/0 · parse | **36/0 · 28/0 · parse** · manifeste **déjà d'accord** |
| banc · couverture · stub 8085 | — | — | **39 OK/0 KO** · **96/100 · 131/190** seuils tenus · refus `rc=1` |
| `.ps1` ASCII · `.bat` | — | — | **les deux ASCII purs** · DOS batch · **0** accent circonflexe |

🔴 **⇒ `0 KO DE PLUS`, GATE PAR GATE, SUR L'ARBRE LIVRÉ.** C'est le contrôle que
`7 bis` laissait explicitement au relecteur, et il est **joué**.

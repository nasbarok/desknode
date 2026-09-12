# dn8-2 — LE RELEVE **AU COMPTE**, gate par gate, AVANT / APRES

🔴 **LE COMPTE, ⛔ PAS LA COULEUR.** La seule gate rouge de ce depot est a
`23 OK / 10 KO` : **une gate deja rouge absorbe un KO de plus sans changer de
couleur**. ⇒ ce relevé porte `N OK / M KO`, et ⛔ jamais « verte ».

**Bornes d'entree** : `mesures/dn8-2/T0-borne-entree.txt` et `T0-run-gates.txt`,
mesurees le 2026-09-11 a `HEAD = 8a2a8c7`.  **Arrivee** : 2026-09-12.

## 1. Les gates que cette marche TOUCHE

| gate | AVANT | APRES | ce qui a bouge |
|---|---|---|---|
| `verif_banc_langue_dn73.py` | `45 OK / 0 KO` · 3,48 s | **`81 OK / 0 KO`** · 2,41 s | +36 controles emis (**17** numerotes + **63** pre-vols de mutant), 38 ⇒ **63** mutants, elle lie le VRAI serveur, et elle JOUE ses deux prerequis |
| `verif_entree_dn82.py` | ⛔ n'existait pas | **`45 OK / 0 KO`** · 0,16 s | 🆕 20 controles, 24 mutants |
| `verif_harnais_dn81.py` *(cockpit)* | `28 OK / 0 KO` | **`28 OK / 0 KO`** | inchangee au compte ; son perimetre `dn8` porte desormais DEUX fichiers |

## 2. Les gates que cette marche NE TOUCHE PAS — le compte est relu quand meme

| gate | AVANT | APRES |
|---|---|---|
| `verif_installeur_dn71.py` | `28 OK / 0 KO` | **`28 OK / 0 KO`** |
| `verif_page_dn722.py` | `56 OK / 0 KO` | **`56 OK / 0 KO`** |
| `verif_langue_dalle_dn73.py` | `61 OK / 0 KO` | **`61 OK / 0 KO`** |
| `verif_preconditions_dn76.py` | `52 OK / 0 KO` | **`52 OK / 0 KO`** |
| `verif_ledger_dn416.py` *(cockpit)* | `36 OK / 0 KO` | **`36 OK / 0 KO`** |
| `verif_campagne_dn440.py` *(cockpit)* | `62 OK / 0 KO` | **`62 OK / 0 KO`** |
| `verif_campagne_dn56.py` | `8 OK / 0 KO` · 428 s · **19 cibles / 579 mutants** | **`8 OK / 0 KO`** · 409,58 s · **20 cibles / 634 mutants** |

⚠️ **ET C'EST LA POPULATION QUI PROUVE L'ENTREE DE LA GATE NEUVE, ⛔ PAS LE
BILAN** : `8 OK / 0 KO` ⛔ ne varie **ni** avec le nombre de cibles **ni** avec
celui des mutants. Le couple **19 ⇒ 20 cibles** et **579 ⇒ 634 mutants** (gate du
banc 32 ⇒ 63, gate d'entree absente ⇒ 24), lui, bouge — il est capture en
APPELANT `cibles()` et `liste_mutants()` de `dn56`, aux deux bornes (`T6`).
🔴 ⚠️ **ET LES 409,58 s SONT ANTERIEURES AUX 17 CORRECTIFS** de la seconde boucle
de revue : mesurees a 60 mutants et 1,95 s par tir, quand l'etat livre en porte
**63 a 2,41 s**. ⇒ **le budget se RE-MESURE a la passe complete** (estimation
arithmetique : ~476 s pour un plafond de 600 s), et ⛔ ce relevé ne pretend pas
qu'il est tenu.
| `verif_dossier_dn415.py` *(cockpit)* | `23 OK / 10 KO` **PRE-EXISTANT** | **`23 OK / 10 KO`** — ⛔ pas un KO de plus |

## 3. La passe entiere

| | AVANT (2026-09-11) | APRES (2026-09-12) |
|---|---|---|
| `bash tools/run_gates.sh` | 43 VERTE / 1 ROUGE / 1 NON-JOUABLE sur 45 · 666 s | **44 VERTE / 1 ROUGE / 1 NON-JOUABLE sur **46**** · 625 s |

## 4. ⚠️ LES OUTILS QUI NE SONT **PAS** DES GATES — relevés aussi

Un changement a deja casse un outil dont la documentation publie les chiffres,
**sans que rien ne rougisse**. ⇒ ils sont relus :

| outil | AVANT | APRES |
|---|---|---|
| `node tools/banc_langue_dalle_dn73.mjs` (seul) | `BANC : 27 OK, 0 KO` · 3,91 s | **`BANC : 39 OK, 0 KO`** · 0,75 s |
| le meme, derriere `--base` | ⛔ n'existait pas | **`BANC : 42 OK, 0 KO`** |
| `--temoin-chaine` | rc=3, ⛔ aucun bilan | **rc=3**, ⛔ aucun bilan |
| `--temoin-dom` | rc=4, `DOM DEGENERE` | **rc=4**, `DOM DEGENERE` |
| `node tools/banc_couverture_dn82.mjs` | ⛔ n'existait pas | **96/100 fonctions · 131/190 blocs**, rc=0 · 0,92 s |
| `--temoin-decision` (le relevé) | ⛔ n'existait pas | **8 scenarios decides** : 2·2·3·3·3·1·1·0 (les deux `2` sont le code « MESURE ABSENTE », decide DANS `decider()`) |
| `--temoin-comptage` (le relevé) | ⛔ n'existait pas | **`fn=2/3 blk=0/1 morts=1`** sur une couverture FIXTURE — ⛔ sans lui, `nFe++` inconditionnel rendait `100/100` et le plancher n'en etait plus un |
| `tools/verif_ledger_dn416.py --manifeste --en-place` | 370 lignes | **372 lignes**, rc=0 |

| `.github/workflows/gates.yml` | ⛔ jamais valide localement | **YAML PARSE**, l'etape de couverture porte `if: always()`, ⛔ aucun `continue-on-error`, ⛔ aucun `\|\| true` sur le `node`, `bash -n` OK |
| gate du banc, `PATH` sans `node` | rc=4 | **rc=4** (normal) · **rc=1 NOMME** (sous mutant) |

⚠️ **ET LE WORKFLOW N'EST GARDE PAR AUCUNE GATE DE CE DEPOT** : rien n'y verifie
la syntaxe de `.github/workflows/`. Le relevé le dit plutot que de le supposer —
la validation ci-dessus est un geste de CETTE passe, ⛔ pas un controle qui se
rejouera tout seul.

## 5. L'EMPREINTE — ⛔ une passe de mesure ne chevauche pas une mutation

`sha256` de l'ensemble des fichiers modifies/ajoutes (`git ls-files -mo`) :

🔴 **ET LA PREMIERE TENTATIVE DE CETTE PREUVE A ECHOUE — ELLE EST ECRITE ICI
PLUTOT QUE REFAITE EN SILENCE.** L'empreinte « avant » avait ete prise a
**00:37**, AVANT le balayage des mutants ; celui-ci a trouve deux defauts (le
mutant 15 devenu gardien MORT, quatre declarations de cibles incompletes), donc
`tools/verif_banc_langue_dn73.py` et `tools/verif_entree_dn82.py` ont ete
**corriges a 00:56:42** — entre les deux prises. La comparaison a donc
legitimement rendu **⛔ L'ARBRE A BOUGE** : le couple enjambait une mutation, ⛔ il
ne la contenait pas.

⇒ **CE QUI EST PROUVE, ET COMMENT** : la passe de mesure a tourne de
**00:57:48 a 01:20:51**. Le `mtime` de CHACUN des 19 fichiers modifies est
ANTERIEUR a 00:57:48 — le plus recent est 00:56:42, soit **66 s avant** le
depart —, et ⛔ **aucun** ne tombe dans la fenetre. L'empreinte relue APRES la
passe et l'empreinte relue MAINTENANT sont **identiques** :

 · empreinte de l'etat mesure **PAR LA CAMPAGNE** : `48adaf20599aba6e` (19 fichiers)
 · empreinte de la prise perimee (avant les correctifs du balayage) : `93220e6bc8f96124`
 · 🔴 empreinte de l'etat **LIVRE** : `642d4df5fc7236c1`

⇒ **L'ARBRE EST STABLE PENDANT LA PASSE** (aucun `mtime` dans la fenetre), et la
seule chose que la premiere empreinte prouvait est que ⛔ je m'etais trompe de
borne.
🔴 ⚠️ **MAIS L'ETAT LIVRE N'EST PLUS CELUI QUE LA CAMPAGNE A MESURE, ET C'EST
ECRIT PLUTOT QUE LISSE.** La seconde boucle de revue a impose **17 correctifs**
apres la campagne — ils touchent `banc_couverture_dn82.mjs`,
`banc_langue_dalle_dn73.mjs`, `verif_banc_langue_dn73.py`, `verif_entree_dn82.py`
et les textes —, si bien que l'empreinte est passee de `48adaf20599aba6e` a
`642d4df5fc7236c1`. ⇒ **CE QUI A ETE RE-MESURE APRES LES CORRECTIFS** : le banc
(39 OK), les deux gates (81 OK / 45 OK), le relevé et ses DEUX temoins, et les
13 mutants touches ou neufs — tous rouges sur leur cible. ⛔ **CE QUI NE L'A PAS
ETE** : `verif_campagne_dn56.py` (les deux tirs) et `bash tools/run_gates.sh`,
c'est-a-dire precisement les deux chiffres de budget. Ils se rejouent a la
verification complete.

## 6. ⛔ CE QUE CE RELEVE NE DIT PAS

 · ⛔ **`AC8.2.6` n'est PAS cochee**, et elle ⛔ ne peut pas l'etre ici : sa
   moitie mecanique est livree (clic REEL sur les deux boutons, `aria-pressed`
   relu sur les VRAIS boutons, etat de depart LU dans le balisage), mais le
   verdict de **lisibilite** se prend **a l'œil de l'owner sur la page servie
   cote Windows**, et le WSL de cette tour est en **NAT**. ⇒ **ECART DECLARE**,
   porteur **`dn8-3`** (son `AC8.3.1` re-heberge `AC7.4.3`).
 · ⛔ Le tir **`cmd.exe`** du point d'entree : NON JOUE, porteur **au ledger**
   (`epic-dn8`).
 · ⛔ Le cout de `/api/etat` **cote Windows** : NON MESURE, porteur **au ledger**
   (`epic-dn8`).
 · ⛔ Et une couverture qui monte ⛔ ne prouve pas qu'une faute serait vue : ce
   que ce relevé garde est une POPULATION ; ce qui JUGE, ce sont les cas et les
   84 mutants.

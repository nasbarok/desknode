# `dn5-1` — L'écart entre ce que le dépôt **demande** et ce qu'il **sait faire**

> Écrit le **2026-09-02**, **AVANT tout push**, sur `desknode@e578def` (arbre propre) contre
> `origin/main@b524e98`. Story : `dn5-1-ce-qui-est-pousse-est-ce-qui-tourne` / **AC1.1**.
> *This page is in French, like its neighbour `dn4-15-arbitrage.md`. Splitting the repository
> between French (engineering log) and English (reader-facing files) is **D21** and belongs to
> `dn8` — see instance n°1 below, which is exactly what that split costs today.*

## 0. La règle que cet écart applique

> 🎯 **Rien de ce qui est poussé ne ment.**

⛔ Ce n'est **pas** *« on pousse quand toutes les stories sont closes »*. À ce critère, rien ne
serait jamais poussé : `dn4-41` est `in-progress`, `dn4-42` est en `review` **avec un écart
déclaré**, `dn4-5` est un soak. Le critère est plus faible sur l'avancement et **beaucoup plus
dur sur l'honnêteté** : un dépôt peut publier du travail inachevé, **il ne peut pas publier une
affirmation que son propre contenu réfute**.

Le contre-exemple qui a fait écrire cette règle est daté et mesuré : voir
[`CONTRIBUTING.md`](../CONTRIBUTING.md) § *Conventions in this repository*.

## 1. Les six instances, chacune avec sa disposition

> ⚠️ **ANNOTATION DU 2026-09-02 (revue de code) — DEUX CLASSES, ⛔ PAS UNE.**
> `CONTRIBUTING.md` annonce au lecteur *« three more instances »* (⇒ **quatre**), et
> l'annotation portée à l'epic écrit *« QUATRE instances »*. **Les deux disent vrai, et
> ce tableau aussi** : les instances **1 à 4** sont la classe *« le dépôt DEMANDE ou
> PROMET ce que son arbre réfute »* (celle de l'epic, et celle que la règle nomme) ;
> les instances **5 et 6** relèvent d'une **autre** classe — *« le dépôt publie un
> défaut qu'il connaît »* (une gate rouge · des chemins personnels). ⛔ Ni l'un ni
> l'autre chiffre n'est faux ; **c'est le fait qu'aucun des trois écrits ne disait de
> quoi il comptait** qui l'était. Corrigé aux trois endroits, ⛔ rien d'effacé.

⚠️ **Aucune instance sans porteur.** Une instance dont la disposition est vide est une promesse
creuse de plus — c'est le défaut même que cette marche solde.

| # | ce que `main` **demande** ou **promet** | ce que `main` **porte** (mesuré le 2026-09-02) | disposition |
|---|---|---|---|
| **1** | `CONTRIBUTING.md` : *« Which **tier** you built: board only, or board + ambient sensors »* | 🔴 `README.md` de `main` : **0** occurrence de `\bpaliers?\b` sur **173 361 o**. Celui de `HEAD` : **13** — mais **en français**, et la question est posée **en anglais**. Le seul `\btiers?\b` des deux côtés est le **français `tiers`** (composants tiers) ⇒ *tier* au sens anglais = **0 des deux côtés** | ✅ **SOLDÉE ICI** — le push amène la définition (0 ⇒ 13) **et** `CONTRIBUTING.md` nomme désormais les deux paliers **tels que le README les nomme** (voie (a)) |
| **2** | `CONTRIBUTING.md` : *« A CLA is required… **A bot handles it in one click**. »* | 🔴 **0 fichier sous `.github/`**, ni sur `main` ni sur `HEAD`. Il n'y a **aucun bot**. | ✅ **SOLDÉE le 2026-09-02 par `dn5-2` / AC2.4** — ⛔ la ligne d'origine n'est pas effacée : elle disait vrai le 2026-09-02 au matin. L'artefact existe désormais : `CLA.md` (le document, qui n'existait pas non plus) et `.github/workflows/cla.yml` (l'action, **épinglée** `contributor-assistant/github-action@v2.6.1` — dépôt **archivé** depuis le 2026-03-23, et c'est écrit dans `CONTRIBUTING.md`). ⚠️ **Ce qui reste, et qui ne peut pas se faire ici** : la preuve d'exécution sur une PR d'un contributeur **externe** — un dépôt à **0 fork** et **1 collaborateur** n'en reçoit aucune. Porteur **`dn8`**, écrit dans `CONTRIBUTING.md`, `CHANGELOG.md` et `docs/roadmap.md` |
| **3** | `CONTRIBUTING.md` : *« Your **DeskNode version** — it is **displayed on the device**. »* | 🔴 **AUCUNE version n'est affichée sur la dalle.** **0** appel à `esp_app_get_description` sur les **54** fichiers de `firmware/desknode/main/` (`main` : 0 sur 48). `dn_ui.c` l'écrit pour le MENU : *« pas de reboot, **pas de version** »*. Le seul identifiant est `App version: <sha>`, **au bandeau SÉRIE de boot** | ✅ **SOLDÉE ICI** — décision owner du 2026-09-02 : `CONTRIBUTING.md` **demande ce qui existe** (le SHA du bandeau série) **et dit comment l'obtenir**. ⚠️ Une **vraie** version affichée + le tag `v0.1.0-beta` restent à **`dn8`** |
| **4** | `CHANGELOG.md` : *« **NVIDIA and AMD GPUs are covered**; Intel Arc and integrated GPUs are untested »* | 🔴 **0** `import pynvml` · **4** `atiadlxx` dans `agent/dn_agent.py` ⇒ la **seule** source GPU est AMD ADL. Et le code **le réfute par écrit** : `dn_agent.py:104-106` — *« 🔴 LE CADRAGE ANNONÇAIT NVML : INAPPLICABLE, la tour est une AMD Radeon… `pynvml` n'est même pas installé. »* | ✅ **SOLDÉE le 2026-09-02 par `dn5-2` / AC2.5** — ⛔ la ligne d'origine n'est pas effacée. 🔴 **ET LE DÉFAUT ÉTAIT DANS TROIS FICHIERS, ⛔ PAS UN** : `CHANGELOG.md` (*« NVIDIA and AMD GPUs are covered »*), `THIRD-PARTY.md:36` (*« reads system metrics through psutil, NVIDIA NVML and AMD atiadlxx »*) — celui-là n'était nommé nulle part — et `CONTRIBUTING.md` qui demandait le GPU sans dire ce qu'il en fait. ⚠️ **La forme du correctif n'est PAS « supprimer le mot NVIDIA »** — ce serait interdire de le démentir : **toute ligne qui le nomme porte sa réfutation**, et c'est gardé par `tools/verif_licences_dn52.py` |
| **5** | Le dépôt publie `tools/run_gates.sh` et **26 gates**, sous une convention qui promet qu'elles passent | 🔴 **1 gate ROUGE au moment du push** : `tools/verif_dossier_dn415.py`, **17 OK / 10 KO**. ⚠️ **Elle PRÉ-EXISTE**, ⛔ elle n'est pas de cette story : ses 10 KO portent **tous** sur des fichiers du **cockpit** (`_bmad-output/…`, préfixe `cockpit:` dans sa sortie), qui **ne sont pas dans le clone** | ⛔ **`dn4-39` / `dn4-40`** — ⛔ **ni imputée, ni aggravée, ni réparée ici** ; **déclarée** parce que taire une gate rouge qu'on publie serait le défaut de classe |
| **6** | Le dépôt se veut clonable — `CONTRIBUTING.md` invite à contribuer, `run_gates.sh` à vérifier | 🔴 **4 outils de `tools/` ont une dépendance FONCTIONNELLE à un chemin personnel** (⚠️ **le chiffre `3` ci-dessous est CORRIGÉ le 2026-09-02, voir §5**) : `verif_dossier_d5_dn45.py:47-48` (`/home/nasbarok/projects/{desknode,compagnon_project}` en **absolu**), `verif_dossier_dn415.py:168` et `verif_ledger_dn416.py:148` (`~/projects/compagnon_project`). ⇒ sur un clone neuf **elles ne peuvent pas s'exécuter**. S'y ajoutent **5** fichiers `firmware/…/fonts/dn_font_*.c` qui portent `/home/nasbarok/…` dans un commentaire de générateur | ⛔ **`dn5-3`** — ⚠️ **ANNOTATION** : le périmètre de `dn5-1` et l'epic écrivent *« les **2** dépendances fonctionnelles de `tools/` »*. **Mesuré le 2026-09-02 : elles sont TROIS.** ⛔ La ligne ne se réécrit pas, elle se **date** (NFR3) |

### Ce que le tri de ce tableau apprend, et qui déplace la story

🔴 **Deux instances sur six ne partent PAS avec le push** — parce que les fichiers qui les portent
sont **identiques au caractère près** entre `main` et `HEAD` :

| fichier | `main` vs `HEAD` |
|---|---|
| `README.md` | **DIFFÈRE** — +264 / −5 |
| `CONTRIBUTING.md` · `LICENSING.md` · `THIRD-PARTY.md` · `CHANGELOG.md` | ✅ **IDENTIQUES** |

⇒ **Le push ne répare rien de ce que ces quatre fichiers promettent.** Il ne répare que ce que le
README ne portait pas.

> ⚠️ **ANNOTATION DU 2026-09-02 (revue de code) — CE TABLEAU EST DATÉ, ⛔ PAS FAUX.**
> Il a été mesuré sur `e578def` **avant tout push**, comme l'en-tête le dit. Depuis, la
> story a **écrit dans `CONTRIBUTING.md`** (instances 1 et 3) : sur l'arbre publié,
> `git diff --numstat b524e98 6728a80 -- CONTRIBUTING.md` rend **`39  2`**, ⛔ il n'est
> **plus** identique. Les trois autres — `LICENSING.md`, `THIRD-PARTY.md`,
> `CHANGELOG.md` — le sont toujours, et c'est ce qui fait léguer les instances 2 et 4.
> ⛔ La ligne ne se réécrit pas : elle se **date** (NFR3). C'est pour ça que les instances **2** et **4** sont léguées, et pourquoi les
instances **1** et **3** demandent une **écriture** dans `CONTRIBUTING.md`, ⛔ pas seulement un push.

## 2. ⚠️ **ANNOTATION NFR3** — `dn_paliers.c` n'existe sur **aucune** branche

La ligne `dn5-1` du tracker et le *step 3* de `epics-desknode-v1.md` écrivent :

> *« `dn_paliers.c` est **ABSENT de `main`** »*

**Mesuré le 2026-09-02** : `git ls-tree -r --name-only` ne rend **aucun** `dn_paliers.*`, **ni sur
`main`, ni sur `HEAD`**. Le fichier **n'a jamais existé**. « Absent de `main` » laisse croire qu'il
existe ailleurs — il n'existe nulle part.

⛔ **Ces deux lignes ne se réécrivent pas.** Elles se **datent** : *annoter, ⛔ pas effacer*.

**La preuve réelle de l'instance n°1** — ce qui manque vraiment à `main` — est :

1. la section README **« Les deux paliers matériels »** (`README.md`, HEAD, l. 30-38) ;
2. la gate **`tools/verif_paliers_dn441.py`** ;
3. les **21** fichiers `firmware/` livrés par `dn4-41`, `dn4-42` et `dn4-43`.

⚠️ Et **`palier` a deux sens dans ce dépôt** : le **palier matériel** (D19) et le **plateau** d'une
courbe (`dn_ui.c`, ~7378-7406 et ~10770). ⛔ Ne pas les additionner : les **13** occurrences comptées
sur `HEAD:README.md` sont bien la notion matérielle.

## 3. Ce qui reste **non défini** après cette marche — avec son porteur

| notion demandée au lecteur | définie dans le clone après `dn5-1` ? | porteur |
|---|---|---|
| **tier** (les deux paliers) | ✅ **OUI** — nommée dans `CONTRIBUTING.md`, définie dans `README.md` § *Les deux paliers matériels* | — |
| **LibreHardwareMonitor** | ✅ **OUI** — `README.md` et `CHANGELOG.md` des deux côtés | — |
| **DeskNode version** | ✅ **OUI** — `CONTRIBUTING.md` demande le SHA du bandeau série **et dit comment le lire**. ⚠️ Une version *affichée sur la dalle* n'existe toujours pas | `dn8` (version affichée + tag `v0.1.0-beta`) |
| **GPU (NVIDIA / AMD / Intel)** | 🔴 **NON** — `CHANGELOG.md` annonce NVIDIA couvert, le code le réfute **[ANNOTÉ LE 2026-09-02 (`dn5-2`) : ✅ **OUI** désormais — les trois fichiers disent que NVIDIA n'est **pas implémenté**, et une gate garde la propriété. ⛔ La ligne se DATE, elle ne se réécrit pas]** | **`dn5-2` / AC2.5** — ✅ soldé |
| **le bot CLA** | 🔴 **NON** — il n'existe pas **[ANNOTÉ LE 2026-09-02 (`dn5-2`) : ✅ **OUI** désormais — `CLA.md` + `.github/workflows/cla.yml`. ⚠️ Ce qui reste est la preuve sur une PR **externe**, impossible à 0 fork / 1 collaborateur]** | **`dn5-2` / AC2.4** — ✅ posé · preuve externe ⇒ **`dn8`** |
| **sortie console série** | ✅ **OUI** — `README.md` donne le baud (**115200**), `tools/dn_console.py`, `idf.py monitor` et `miniterm` | — |
| **les gates tournent sur un clone** | 🔴 **NON** — 3 outils exigent un chemin personnel absent du clone | **`dn5-3`** |
| **le dépôt compile à froid** | 🔴 **NON MESURÉ** — ⛔ pas mesuré ici, et ⛔ pas affirmé | **`dn5-4`** |
| **le poids d'un clone** | 🔴 **NON MESURÉ** ici (bundle `main` ≈ 31 Mo au cadrage) | **`dn5-5`** |

## 4. ⚠️ Constat de dossier voisin — il ne fait pas partie de l'écart, mais il le borde

L'en-tête du tracker et l'epic `dn5` posent en garde-fou : *« le soak de `dn4-5` **tourne** ⇒ ⛔
aucun flash »*. **Mesuré le 2026-09-02, sans ouvrir le port** :

- la boîte noire `dn4-5-journal-soak.log` s'arrête le **2026-08-26 à 23:28:39** sur `PORT FERME` ;
  elle avait démarré à **23:27:39**. 🔴 **Le soak a vécu 60 secondes**, et l'`up` de la carte y
  plafonne à **50 s** ;
- l'agent qui tourne aujourd'hui **n'arme pas** ce journal : `dn-agent.started` porte
  `--serie COM3 --stop-si … --temoin`, ⛔ **aucun `--journal-soak`** ;
- et ce n'est pas un oubli : **`tools/dn_agent_tour.ps1:344-346` n'a aucun chemin qui le passe**.
  Le drapeau existe (`agent/dn_agent.py:3568`, classe `JournalSoak` l. 2387) mais il n'est
  atteignable **qu'à la main**, ⛔ pas par le double-clic livré.

⇒ **NFR8 tient dans tous les cas** — cette story ne flashe rien. Mais **le témoin d'AC1.4 change** :
il est pris sur le compteur `s mur` / `seq` de `dn-agent.log`, ⛔ pas sur le bandeau de boot.
Détail et motif : [`mesures/dn5-1/T0-etat-soak.txt`](../mesures/dn5-1/T0-etat-soak.txt).

⇒ ⚠️ **Porté à `dn4-5`** : son soak n'est pas seulement arrêté, il **n'est pas armable par le geste
owner livré**. ⛔ Rien n'est corrigé ici.

---

## 5. ⚠️ **ANNOTATION DU 2026-09-02 (revue de code)** — l'inventaire de l'instance n°6 SOUS-COMPTAIT

L'instance n°6 existe pour **corriger un sous-comptage** : l'epic et le périmètre de `dn5-1`
écrivaient *« les **2** dépendances fonctionnelles de `tools/` »*, et cette page a mesuré
*« elles sont **TROIS** »*. **La revue en a mesuré QUATRE**, et le seau documentaire était pire.

### (a) La 4ᵉ dépendance fonctionnelle — `tools/bench_lisseur_dn45.py`

Elle porte, **au niveau module** (⛔ pas dans un commentaire), motif `sys.path.insert` :

```python
sys.path.insert(0, r"\\wsl.localhost\Ubuntu\home\nasbarok\projects\desknode\agent")
import dn_agent
```

⇒ sur un clone neuf, **l'`import` échoue** : le script ne démarre pas. C'est exactement le
critère de la *classe 1* — une dépendance **fonctionnelle**, ⛔ pas un exemple.

⚠️ **ET LA FORMULE « elles ne peuvent pas s'exécuter » EST TROP FORTE — mesuré le 2026-09-02.**
Lancées depuis un **clone neuf**, trois des quatre **tournent quand même** :
`verif_dossier_d5_dn45.py` (rc 0), `verif_ledger_dn416.py` (rc 0) et `verif_dossier_dn415.py`
(rc 1 — son rouge **pré-existant**, ⛔ pas un échec de démarrage). 🔴 **Et c'est PIRE que si
elles échouaient** : elles tournent **parce qu'elles sortent du clone** et atteignent
`/home/nasbarok/projects/…`, qui existe sur cette machine. **Sur la machine de n'importe qui
d'autre, il n'y a rien à atteindre.** Seule `bench_lisseur_dn45.py` échoue ici et maintenant
(`ModuleNotFoundError: No module named 'dn_agent'`). ⇒ **la mesure prise sur la machine de
l'auteur ne peut pas, par construction, révéler ce défaut** — il faut le lire dans le code,
⛔ pas l'attendre d'un code de sortie. ⚠️ Constat pour `dn5-3`.

**Les quatre, re-mesurées :**

| outil | motif |
|---|---|
| `tools/verif_dossier_d5_dn45.py` | deux chemins absolus `/home/nasbarok/projects/…` |
| `tools/verif_dossier_dn415.py` | `~/projects/compagnon_project` |
| `tools/verif_ledger_dn416.py` | `~/projects/compagnon_project` |
| **`tools/bench_lisseur_dn45.py`** | 🆕 `sys.path.insert` vers `\\wsl.localhost\…` puis `import dn_agent` |

### (b) Le seau **documentaire** : 13 fichiers tracés, ⛔ pas 5

Cette page écrivait *« s'y ajoutent **5** fichiers `firmware/…/fonts/dn_font_*.c` »*.
**Mesuré** — `git grep -l nasbarok` sur l'arbre publié rend **13** fichiers tracés :

- les **5** polices `firmware/desknode/main/fonts/dn_font_{14,18,28,33,56}.c` ;
- **`agent/dn_agent.py`** — 🔴 le livrable que le contributeur **exécute**, et il n'était
  nommé nulle part ;
- `tools/dn_lhm_tour.ps1` · `tools/identifier_ventilos_dn48.py` ·
  `tools/mesure_grandeurs_dn46.py` · `tools/mesure_lhm_dn48.py` ·
  `tools/mesure_lissage_dn45.py` · `tools/verif_dossier_d5_dn45.py` ·
  `tools/bench_lisseur_dn45.py`.

⚠️ `verif_dossier_dn415.py` et `verif_ledger_dn416.py` **n'apparaissent pas** dans ce compte :
ils écrivent `~/projects/…` **sans** le nom d'utilisateur. ⇒ **deux instruments, deux comptes** —
`git grep -l nasbarok` rend **13**, l'union avec les chemins en `~` en rend **15**. ⛔ Publier
l'un des deux sans dire lequel serait le défaut que cette page solde.

⇒ **Disposition inchangée : `dn5-3`.** Ce qui change, c'est **son périmètre** : il était écrit à
moins de la moitié du réel. ⛔ Les chiffres `2`, `3` et `5` ne se réécrivent pas — ils se
**datent** (NFR3), ici et à leurs sites.

---

### Mesures qui portent cette page

⚠️ **Complété le 2026-09-02 (revue de code)** : l'index ne listait que les quatre captures **T0**.
Les captures qui **ferment** la story ont été committées après l'écriture de cette page et n'y
avaient jamais été ajoutées.

| capture | ce qu'elle prouve |
|---|---|
| [`mesures/dn5-1/T0-gates-avant.txt`](../mesures/dn5-1/T0-gates-avant.txt) | 24 VERTE, 1 ROUGE, 1 NON-JOUABLE / 26 — le rouge **avant** toute écriture |
| [`mesures/dn5-1/T0-etat-remote.txt`](../mesures/dn5-1/T0-etat-remote.txt) | 3 réfs à `b524e98` · `main` ancêtre de `HEAD` · 73 fichiers / 21 `firmware/` · les 4 fichiers qui promettent sont **identiques** |
| [`mesures/dn5-1/T0-comptage-rejeu.txt`](../mesures/dn5-1/T0-comptage-rejeu.txt) | les comptages **à bornes de mot**, chaque chiffre **avec son motif** — et le piège de sous-chaîne mesuré |
| [`mesures/dn5-1/T0-etat-soak.txt`](../mesures/dn5-1/T0-etat-soak.txt) | le soak ne tourne pas, et le témoin NFR8 retenu **avec son motif** |
| [`mesures/dn5-1/T3-temoin-nfr8-avant.txt`](../mesures/dn5-1/T3-temoin-nfr8-avant.txt) | le témoin NFR8 **avant** la 1ʳᵉ pousse, ⛔ sans ouvrir le port |
| [`mesures/dn5-1/T3-etat-remote-apres.txt`](../mesures/dn5-1/T3-etat-remote-apres.txt) | l'état du remote après la 1ʳᵉ pousse — ⚠️ **annotée** : elle porte `18737fe`, périmé |
| [`mesures/dn5-1/T3-temoin-nfr8-apres.txt`](../mesures/dn5-1/T3-temoin-nfr8-apres.txt) | le témoin **après** la 1ʳᵉ pousse — ⚠️ **annotée** : elle n'encadre que celle-là |
| [`mesures/dn5-1/T4-comptage-clone-neuf.txt`](../mesures/dn5-1/T4-comptage-clone-neuf.txt) | le comptage sur clone neuf — ⚠️ **annotée** : clone pris à `18737fe`, et 2 verdicts corrigés |
| [`mesures/dn5-1/T6-gates-apres.txt`](../mesures/dn5-1/T6-gates-apres.txt) | les 26 gates comparées une à une, et les **trois** corrections d'instrument |
| [`mesures/dn5-1/T7-etat-final.txt`](../mesures/dn5-1/T7-etat-final.txt) | 🆕 **l'état RÉELLEMENT publié** (`6728a80`) : réfs, `ahead`, PRIVATE, tags, `firmware/` vide, témoin NFR8 étendu à toute la story |

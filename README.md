# DeskNode

> **Licence** — DeskNode se licencie **par nature de fichier** : `firmware/` en
> **GPL-3.0-or-later**, `agent/` en **MIT**, `docs/` en **CC-BY-SA-4.0**.
> Détail et ce que ça implique pour toi : [`LICENSING.md`](LICENSING.md).
> Composants tiers : [`THIRD-PARTY.md`](THIRD-PARTY.md) · Contribuer :
> [`CONTRIBUTING.md`](CONTRIBUTING.md) · Journal : [`CHANGELOG.md`](CHANGELOG.md).
>
> ⚠️ Ce README est le **journal de bord** du projet (168 Ko). Il sera **scindé** avant
> la `v0.1.0-beta` : le journal partira dans `docs/`, une vitrine courte restera ici.


Mini-display tactile 2,8" (Waveshare **ESP32-S3-Touch-LCD-2.8B**, 480×640 IPS portrait) **posé à
côté de la tour PC** (décision owner du 2026-08-17 — le brief dit encore « monté sur la façade du
NZXT Phantom 630 », c'est périmé : pas de support imprimé, pas de passage de câble interne, et le
capteur mesure l'ambiance là où il est posé, ce qui est assumé). Affiche en continu 6 métriques — CPU, GPU, RAM,
réseau (via un agent Windows) + température, humidité (capteurs I²C locaux) — avec deux états
visuels (**Ambient** H24 / **Actif** au toucher) et une identité « **Living PCB** ».

## 🔴 CE QUE TA CONFIGURATION TE DONNE — ET CE QU'ELLE TE RETIRE (`dn4-41`, D19)

> ⚠️ **Cette section est un AJOUT, ⛔ pas une réorganisation.** Ce README fait 169 Ko et
> c'est `dn8` qui le **scinde** (journal vers `docs/`, vitrine courte à la racine).

**DeskNode ne t'oblige à rien.** Pas de compte, pas de cloud, pas de chaîne de compilation, pas de
droits administrateur, **pas de capteur obligatoire**. Ce qui suit dit exactement ce que chaque
configuration affiche — et ce qu'elle **ne peut pas** afficher. ⛔ Rien n'y est promis qui n'ait
été mesuré sur cette carte.

### Les deux paliers matériels

| palier | ce que tu achètes | ce que tu ajoutes |
|---|---|---|
| **DeskNode** | **la carte Waveshare ESP32-S3-Touch-LCD-2.8B, seule** | rien |
| **DeskNode + Ambiance** | la même carte | **BME680** (température, humidité) + **BH1750** (lumière), sur le header I²C 2×12 — **capteurs soudés** côté breakout, **Dupont** côté carte |

⛔ **La carte seule n'est pas un mode dégradé.** C'est une configuration **valide et gardée** : le
firmware sait qu'il n'a pas de capteur, il le **dit**, et il **désarme** ce qui n'a plus d'entrée.

📦 **Références exactes, quantités et prix datés : [ce qu'il faut acheter](docs/bom.md).** Cette page
dit aussi **quelle carte NE PAS prendre** — Waveshare en vend trois aux noms presque identiques, et
la mauvaise est la moins chère.

🔌 **Où brancher, et comment vérifier que le bus répond : [câbler un DeskNode](docs/cablage.md).** Cette page donne les deux points d'accès au bus I²C **avec leur piège**, et dit **quoi conclure** de ce que le scan répond — un scan à une seule passe fabrique des faux positifs.

📦🖨️ **Et le boîtier ? [sa place, son format et sa notice](docs/boitier.md).** ⚠️ Aucun boîtier n'est obligatoire, et **aucun plan n'est encore déposé** : cette page dit où ils iront, sous quelle licence, et pourquoi ses **quatre** paramètres d'impression sortent **non mesurés**.

### 🔴 L'ÉCRAN PARLE **ANGLAIS PAR DÉFAUT**, ET LE FRANÇAIS SE PREND AU DOIGT

| | |
|---|---|
| **l'écran** | **FR / EN**, **défaut : ANGLAIS** |
| **où on change** | 🟡 **au flasheur web** — ⚠️ **pas encore livré**, voir ci-dessous |
| ⚠️ *annoté le 2026-09-08* | le **flasheur** est livré (§ *Installer DeskNode*) ; ce qui reste vrai, c'est que **le choix de langue** n'y est pas encore — ⛔ ligne du dessus non effacée |
| 🎯 *ré-annoté le 2026-09-09* | **la moitié « n'y est pas encore » a cessé d'être vraie**, et ⛔ aucune des deux lignes du dessus n'est effacée : le choix **est** sur le flasheur, deux positions, **anglais par défaut**, au-dessus du bouton d'installation — et un geste explicite l'écrit dans la carte après le flash. ⇒ le « **en attendant** » de la ligne suivante devient **le second chemin**, ⛔ plus le seul |
| **en attendant** | la commande console `langue fr` / `langue en` |
| **ce qui survit au reboot** | le choix, rangé en NVS |
| 🔴 **la console (le REPL série)** | **elle reste en FRANÇAIS** — voir plus bas |

⛔ **Les codes ne se traduisent pas.** C'est `FR` et `EN`, ⛔ pas « Langue » ni « Language » :
écrire un mot français à quelqu'un qui ne lit que l'anglais est exactement ce que ce réglage
corrige.

⚠️ **Au premier démarrage après un flash, la carte parle ANGLAIS**, et il n'y a rien à faire pour
ça : il n'y a rien en NVS, et le défaut est l'anglais.

#### 🟡 CE QUI N'EST PAS ENCORE LÀ, ET C'EST DIT PLUTÔT QUE DÉCOUVERT

🔴 **Le choix de langue N'EST PAS sur la dalle.** Il a été construit — deux cibles `FR`/`EN` dans
l'entête du MENU, flashées et validées à l'œil le 2026-09-01 — puis **retiré**, pour deux raisons :

1. **Décision owner** : le choix appartient au **flasheur web**, ⛔ pas au MENU. Ce flasheur est
   son propre chantier (`epic-dn7`) et **il n'est pas livré**.
   > ⚠️ **ANNOTÉ LE 2026-09-08 — LA MOITIÉ « il n'est pas livré » A CESSÉ D'ÊTRE VRAIE, ET LA
   > PHRASE N'EST ⛔ PAS EFFACÉE.** Ce qui est livré depuis ce jour-là, c'est **l'installeur
   > local** : `installeur/DeskNode-installeur.bat` ouvre une page servie sur cette machine,
   > qui dit l'état du poste et **arrête** ou **retire** l'agent. Voir la section
   > *« Installer DeskNode »* plus bas. 🔴 **Ce qui reste vrai, et il faut le lire** : cette
   > page **ne flashe encore rien** et **ne propose aucun choix de langue** — donc la phrase
   > ci-dessus reste exacte *pour le point dont elle parle*, le choix de langue. ⇒ la langue
   > se change toujours au REPL série, comme dit juste en dessous.
   > 🎯 **RE-ANNOTÉ LE 2026-09-08 — ⛔ AUCUNE DES DEUX ANNOTATIONS PRÉCÉDENTES N'EST
   > EFFACÉE, ET LA SECONDE VIENT DE PERDRE UNE MOITIÉ.** *« Cette page ne flashe encore
   > rien »* a cessé d'être vrai le jour même : la page **pose le firmware sur la carte**,
   > avec quatre images versionnées et leur manifeste. ⇒ de la phrase d'origine, il ne
   > reste vrai que **le choix de langue**, qui n'est toujours pas sur la page et se fait
   > toujours au REPL série.
   > 🎯 **RE-ANNOTÉ LE 2026-09-09 — ⛔ AUCUNE DES TROIS ANNOTATIONS PRÉCÉDENTES N'EST
   > EFFACÉE, ET LA DERNIÈRE MOITIÉ VIENT DE TOMBER À SON TOUR.** *« Le choix de langue
   > n'est toujours pas sur la page »* a cessé d'être vrai : la page **porte le choix**,
   > **avant le flash**, anglais par défaut, et un geste explicite l'**écrit dans la carte**.
   > ⇒ de la phrase d'origine — *« le choix appartient au flasheur web, ⛔ pas au MENU »* —
   > il ne reste plus rien d'ouvert : le flasheur est livré, **et il porte le choix**.
   > ⚠️ **Ce qui reste vrai, et c'est ce dont parle le point 2 ci-dessous** : les deux cibles
   > `FR`/`EN` **de l'entête du MENU** restent retirées, et la régression de charge qu'elles
   > causaient reste la raison. Le choix se fait **sur la page**, ⛔ pas au doigt sur la dalle.
2. 🔴 **Ces deux cibles causaient une régression de charge MESURÉE** : `taskLVGL` passait de
   **3,5 % à 99,3 %** après une poignée de reconstructions de scène, watchdog déclenché, écran
   saccadé et tactile en retard. Elle est **partie avec elles** (A/B sur la carte, même protocole).

⇒ **Aujourd'hui, la langue se change au REPL série** (`langue fr`). ⚠️ Le README ne prétend donc
**pas** que le produit se règle entièrement au doigt sur ce point-là — et c'est écrit ici plutôt
que constaté le premier soir.

> 🎯 **ANNOTÉ LE 2026-09-09 — LA PHRASE CI-DESSUS RESTE VRAIE, MAIS ELLE N'EST PLUS TOUTE
> L'HISTOIRE, ET ELLE N'EST ⛔ PAS EFFACÉE.** Le canal n'a pas changé : c'est **toujours**
> `langue fr` au REPL série qui pose la langue. Ce qui change, c'est **qui le tape** : la page
> d'installation le fait désormais **pour vous**, sur un geste explicite, après le flash — elle
> réveille la console, envoie l'ordre, **relit l'état** et vous rend le refus de la carte s'il y
> en a un. ⇒ vous n'avez plus à trouver un terminal série ; ⛔ mais rien n'a été construit dans
> le firmware pour ça, et la commande console reste ce qu'elle était.

#### ⛔ LA CONSOLE RESTE EN FRANÇAIS, ET C'EST UNE DÉCISION — ⛔ PAS UN OUBLI

Le REPL série (`dn_console.c`) fait **~12 000 lignes de diagnostic écrites pour l'auteur**. Il
n'est pas le produit : le produit se règle **au doigt** sur la dalle, et l'agent PC est
**Windows seul**.

⇒ **Si tu ouvres le REPL, attends-toi à du français.** C'est dit ici plutôt que découvert.

✅ **Et les deux ne peuvent pas diverger** : il n'existe **qu'une seule définition par chaîne**
(`main/dn_langue.h`). L'écran la lit dans la langue courante, la console la lit **toujours dans
la colonne française**. Une gate (`tools/verif_langues_dn442.py`) refuse qu'un texte de la dalle
échappe à cette table, qu'un glyphe absent des polices y entre, ou qu'un libellé déborde de sa
place **dans l'une ou l'autre langue**.

### 🔴 TROIS AXES, ⛔ PAS DEUX — et le troisième est indépendant des autres

Le troisième axe est **logiciel, côté PC** : `LibreHardwareMonitor` se combine avec les deux
paliers matériels, il ne s'y range pas.

| capteurs soudés | LHM installé | PC allumé | ce qui VIT | ce qui dit `--` |
|:---:|:---:|:---:|---|---|
| ✅ | ✅ | ✅ | **les 6 cases**, CPU avec sa °C, DISQUE avec ses tr/min | — |
| ✅ | ⛔ | ✅ | les 6 cases · CPU garde **% et GHz** · DISQUE garde ses **Mo/s** | la **°C CPU** et les **tr/min** |
| ✅ | — | ⛔ | **AMBIANCE seule** (température, humidité) — 1 case sur 6 | les 5 cases venues du PC |
| ⛔ | ✅ | ✅ | 5 cases sur 6 — CPU/GPU/RAM/RÉSEAU/DISQUE, °C et tr/min comprises | **AMBIANCE** entière |
| ⛔ | ⛔ | ✅ | 5 cases sur 6, sans la °C CPU ni les tr/min | AMBIANCE · °C CPU · tr/min |
| ⛔ | — | ⛔ | 🔴 **RIEN — 0 case sur 6** | **tout** |

🔴 **ANNOTÉE LE 2026-09-10, ⛔ PAS CORRIGÉE — ET C'EST ELLE QUI REND LE PRIX LISIBLE.** Les
deux lignes *« LHM ⛔ »* restent **vraies du matériel** : la dalle afficherait bien tout cela
sans LibreHardwareMonitor. Ce qui a changé ce jour-là, c'est **le chemin supporté**, ⛔ pas la
mesure : l'owner a tranché que **LHM est un prérequis DUR**, et le pré-vol de l'agent
~~**refuse** désormais de le lancer sans lui~~. ⇒ sur une machine sans LHM, ces deux lignes
décrivent ce que le **matériel** ferait, et ⛔ **plus** ce que le projet accepte de livrer —
il n'y a **pas d'agent** pour remplir les cases. ⛔ **Effacer la table effacerait le prix de
la décision** ; la laisser nue ferait mentir ce fichier. Voir *Ce que vous devez installer
vous-même — écart déclaré*, plus bas, où ce prix est chiffré.

🟢 **RE-ANNOTÉE LE 2026-09-12 (`dn4-48`) — LA PHRASE BARRÉE CI-DESSUS EST TOMBÉE, ET LES
DEUX LIGNES *« LHM ⛔ »* REDEVIENNENT VRAIES DU PRODUIT, ⛔ plus seulement du matériel.** Le
pré-vol ⛔ **ne refuse plus** : il **attend** LHM (borné, 5 min par défaut) puis **démarre
quand même**. ⇒ sur une machine sans LHM il y a **bien un agent**, la dalle **se remplit**,
et ce sont exactement **5 cases sur 6** — la ligne du tableau, telle qu'elle a toujours été
écrite. ⚠️ **⛔ Aucune des deux annotations n'est effacée** : la première dit ce que le
projet acceptait de livrer du 2026-09-10 au 2026-09-12, et c'est **elle** qui rend lisible le
coût qu'une mesure a fait retirer. Motif : `dn4-48`, section de l'écart déclaré.

### 🔴 « VIVANT MÊME PC ÉTEINT » N'EXISTE PAS AU PALIER « DeskNode »

**D6** promettait qu'une case sur six survive au PC éteint : c'est **AMBIANCE**, et elle vient du
**BME680**. Sans lui, c'est **0 sur 6**, ⛔ pas 1.
⛔ **Ce n'est pas un défaut, c'est ce que le palier coûte** — et c'est écrit ici plutôt que
découvert le premier soir.

### 🔴 LE PALIER LHM N'EST PAS « AVEC LHM ⇒ °C »

La table des sondes de l'agent est une **propriété de la tour de l'auteur** :
`/intelcpu/0/temperature/10` et `/lpc/nct6792d/0/fan/{0,1,2,4}`.
⇒ **Avec un autre CPU ou une autre carte mère, LHM peut être debout et ne rien donner.**

✅ **Et l'instrument qui le montre existe déjà** : le bilan de fin de l'agent distingue **six**
diagnostics jamais fondus, dont le seau **`absences`** — *« LHM a RÉPONDU, SANS cette valeur »* —
qui n'est **ni** `pannes` (LHM injoignable) **ni** `rejets`. ⇒ si tes tr/min restent à `--` pendant
que LHM tourne, **c'est ce seau-là qu'il faut lire**, et il te dira que le mapping ne correspond
pas à ton matériel.

### 🔴 « PAS DE DROITS ADMINISTRATEUR » EST VRAI AU PALIER CARTE SEULE, **ET FAUX AU PALIER LHM**

- ✅ **L'agent DeskNode** : *« sans élévation, sans driver, sans .NET »*. Cette formule est
  **vraie** et elle ne change pas.
- 🔴 **LibreHardwareMonitor**, lui, exige **une élévation**, une tâche planifiée en
  **`RunLevel Highest`**, et un **driver noyau signé** (PawnIO 2.2.0).
  ⚠️ Son prédécesseur **WinRing0 est frappé par CVE-2020-14979** et Defender le détecte depuis
  fin 2024 sous `HackTool:Win32/Winring0`.
- ⇒ **C'est LHM qui coûte l'élévation, ⛔ pas DeskNode.** Le palier carte seule + agent n'en
  demande aucune, et le palier « avec LHM » en demande une. **Écrit, ⛔ pas tu.**

### ⚠️ PORTABILITÉ — CE QUI EST COUVERT, ET CE QUI NE L'EST PAS

| | état |
|---|---|
| **GPU AMD** | ✅ **couvert et mesuré** — via `atiadlxx.dll` (ADL) |
| **GPU NVIDIA** | 🔴 **NON IMPLÉMENTÉ.** ⛔ Il n'y a **aucun NVML** dans l'agent (`pynvml` n'est même pas installé). Un dossier de ce dépôt a écrit *« GPU : NVIDIA (NVML) et AMD »* — **c'est faux dans le code**, et le README ne le promet pas. |
| **Intel Arc / iGPU** | ⚠️ **non instruits** — aucun matériel ici pour le savoir |
| **agent** | **Windows seulement** |

### ⚠️ CE QUI N'A PAS ÉTÉ VÉRIFIÉ — ET LE VRAI, ⛔ PAS PLUS

- ✅ Le palier « DeskNode » (carte seule) est **construit, instrumenté et gardé** : le firmware
  rend un verdict **ABSENT** distinct de « pas encore lu », il **compte** ses absences, il
  **désarme** l'asservissement de luminosité et **dit pourquoi**, et la luminosité **se règle au
  doigt** au MENU. Une gate (`tools/verif_paliers_dn441.py`) garde ces invariants.
- ✅ **L'écran bilingue FR/EN** est construit et gardé : une seule définition par chaîne,
  **défaut anglais**, persistance NVS, et une gate qui **relit les cmaps des polices** et
  **recalcule les largeurs** dans les deux langues (`tools/verif_langues_dn442.py`,
  30 contrôles, 24 mutants vus rougir).
  ✅ **Vu sur la dalle le 2026-09-01** : les six titres et la date en anglais au premier boot, et
  le basculement qui survit au reboot.
  🟡 **Ce qu'aucune gate ne dit : si le mot anglais est le BON mot.** Ça se lit à l'œil.
  🟡 **Et le choix au doigt N'EST PAS livré** — voir « ce qui n'est pas encore là » plus haut.
- 🟡 **Le démarrage à froid sur un bus réellement sans capteurs** est le témoin **qualifiant**.
  ⚠️ **Son état est tenu à jour ci-dessous, et il dit le vrai, ⛔ ni « non testé » ni « validé ».**

  > **État au 2026-09-01, mesuré sur la carte (binaires `4f9b401` puis `c081a6c`)** :
  >
  > ✅ **Un capteur du bus était RÉELLEMENT DÉBRANCHÉ** pendant toute la séance (le VL6180X,
  > `0x29`), confirmé par **deux instruments indépendants** — le scan ne le voit plus (`0/5`) et
  > toute transaction de donnée échoue — **et par le fait physique**, demandé à l'owner plutôt que
  > déduit.
  > ✅ **Six démarrages à froid réels** (débranchement du câble USB, ~3 s, rebranchement). À chaque
  > fois : le capteur absent est déclaré **`ABSENT`**, et **les deux capteurs présents restent à
  > ZÉRO échec** — dont un boot observé **630 s**. ⇒ **aucun faux positif sur 6 cycles.**
  > ✅ Le modèle a été **confronté cinq fois** à la carte (`échecs = ⌊uptime/60⌋`) : **aucun écart**.
  > ✅ **Le pire cas de blocage I²C est chiffré, et il est THÉORIQUE** : une transaction contre une
  > adresse morte rend en **174–235 µs**, et le cycle complet coûte **453 µs au maximum** sur une
  > période de 5 000 ms — soit **0,009 %**, là où le dossier craignait **24 %**.
  >
  > 🔴 **CE QUI N'A PAS ÉTÉ FAIT, ET QUI RESTE LE TÉMOIN QUALIFIANT** : le démarrage à froid d'une
  > carte **sans AUCUN capteur**. L'owner a décidé de ne rien débrancher, et **le budget de
  > 4 insertions annoncé n'a donc pas été entamé**. ⇒ ⛔ ne sont **pas** exercées : les conditions
  > électriques d'un bus nu (pull-ups, appel de courant à froid), ni la composition
  > « fenêtre froide × bus nu » — qui **ne s'extrapole pas** depuis des mesures à chaud.
  > ⇒ Cette ligne portera **son chiffre** quand ce démarrage aura eu lieu. ⛔ Ni « non testé », ni
  > « validé » : **ceci**.

- 🔴 **ET CE QUI RESTE VRAI DANS TOUS LES CAS** : ce palier a été éprouvé **sur UNE carte** —
  celle du développement — ⛔ **jamais sur un exemplaire monté par quelqu'un d'autre.**
  ⇒ *« Ce palier est construit, instrumenté et gardé ; **tu es le premier à l'assembler** —
  dis-nous ce que tu vois. »*

---

## Pilotage projet

Le cockpit BMad (brief, epics, stories, sprint status) vit dans le repo `compagnon_project` :

- Brief : `compagnon_project/_bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/`
- Epics V1 : `compagnon_project/_bmad-output/planning-artifacts/epics-desknode-v1.md`

La V1 avance par **escalier de mini-POC** (P0 toolchain → P9 endurance H24), chaque marche
fermant une question technique par la mesure. Les choix techniques (framework, transport
PC↔module, agent Windows) sont **ouverts** tant qu'un POC ne les a pas tranchés.

## Passer les gates — **UNE commande** (`dn4-24`)

```bash
bash tools/run_gates.sh
```

> ✅ **Et depuis le 2026-09-02, PERSONNE N'A PLUS À Y PENSER** (`dn4-39`).
> `.github/workflows/gates.yml` joue cette même commande à **chaque poussée** et sur
> **chaque pull request**. ⛔ **La commande ci-dessus n'est pas remplacée** — elle
> reste la façon de voir le verdict avant de pousser ; elle cesse seulement d'être
> le **seul** moyen.
>
> 🔴 **LE VERDICT DE LA CI N'EST PAS CELUI DU POSTE, ET L'ÉCART EST MESURÉ.** Six
> gates ne peuvent pas s'exercer là où la CI tourne : deux lisent le dépôt privé de
> planification, trois ont besoin de `managed_components/` (gitignoré), et ~~une lit
> des chemins **absolus** de la machine de l'auteur~~. ⛔ Elles ne sont ni tues ni
> exclues : elles sont **déclarées** dans la table des NON-JOUABLES ci-dessous.
>
> ⚠️ **BARRÉ LE 2026-09-04 (revue de code de `dn5-3`), ⛔ pas effacé — la clause disait
> vrai quand elle a été écrite.** Elle décrivait `tools/verif_dossier_d5_dn45.py`, qui ne
> lit **plus aucun** chemin absolu : sa racine dérive de `__file__` et le cockpit est un
> **argument**. ⇒ son motif est désormais **le même que celui des deux premières** — le
> cockpit est un dépôt privé, jamais dans le clone. 🔴 **Sa jumelle anglaise de
> `CONTRIBUTING.md` avait été annotée le jour même ; celle-ci ⛔ non.** ⚠️ Les **comptes**
> de ce paragraphe (« Six », et « sept » plus bas) restent périmés **et ⛔ ne sont pas
> corrigés ici** : ils appartiennent à `dn4-39`, qui les porte.

Il découvre les gates **par glob** (`tools/verif_*.py`), les joue toutes, imprime
`VERTE` / `ROUGE` / `NON-JOUABLE` par gate plus un **BILAN**, et sort en **1 dès qu'une
est ROUGE** — **0** si toutes sont vertes ou déclarées non-jouables.

- ⛔ **Aucune gate n'est énumérée à la main.** Une liste écrite se périme le jour où on
  ajoute une gate, c'est-à-dire le jour où elle compte. Le dépôt a payé le motif : il en
  portait **21** pendant qu'un dossier en comptait **20**.
- ⛔ **Aucune sortie n'est jetée.** Elle est **capturée** et **imprimée uniquement sur
  échec** : un rouge sans son motif n'est pas un diagnostic. Le runner refuse même de
  démarrer si **son propre source** contient une redirection vers le puits.
- ⚠️ **Une gate NON-JOUABLE est DÉCLARÉE dans le script, avec son motif** — ⛔ jamais
  déduite d'un code de retour, sans quoi un vrai rouge (traceback, timeout, segfault)
  deviendrait « non-jouable » en silence. Et sa déclaration porte un **témoin** : le
  chemin dont l'apparition la rend jouable. Elle est alors **jouée**, pas sautée.
- 🔴 **Et depuis la revue du 2026-08-31, une NON-JOUABLE est JOUÉE QUAND MÊME**, sans
  argument, et doit rendre **exactement le `rc` que sa déclaration annonce**. Motif payé :
  `verif_sr03.py` remplacée par un `print(); sys.exit(0)` produisait une sortie **identique**
  — une gate déclarée n'était jamais confrontée à ce que sa déclaration affirme d'elle. La
  déclaration est désormais falsifiable **dans les deux sens**, et une déclaration
  malformée, à champ vide ou périmée fait **sortir en 1**.
- 🔴 **Et depuis `dn4-39` (2026-09-02), un `rc` DÉDIÉ dit « prérequis absent ».**
  Motif payé : les six gates concernées rendaient toutes **`1`** sans leur prérequis
  — **la même valeur que leur rouge**. Déclarer `rc attendu = 1` aurait produit une
  déclaration satisfaite **aussi bien par un vrai défaut** que par un terrain
  manquant : la falsifiabilité ci-dessus serait tombée **à vide**.

  | `rc` | ce qu'il veut dire | qui le rend |
  |---|---|---|
  | `0` | toutes vertes, ou déclarées non-jouables **et conformes** | `run_gates.sh` |
  | `1` | **un VRAI défaut trouvé** — ou une déclaration démentie / malformée / périmée | toutes |
  | `2` | **message d'usage** (il manque un ARGUMENT) — ⛔ pas un rouge | `verif_sr03.py` |
  | `3` | **mutant PÉRIMÉ** : le motif a disparu du source, la campagne est cassée | `verif_paliers_dn441.py` |
  | `4` | **PRÉREQUIS ABSENT** (il manque un DÉPÔT ou un ARBRE), avec son motif imprimé | les 6 gates déclarées |

  ⚠️ **L'ordre est une règle, ⛔ pas un détail : un VRAI défaut l'emporte sur un
  prérequis absent.** Une gate qui trouve un KO rend **1** même si un prérequis
  manque — sinon un prérequis absent **masquerait** un rouge.

### Les options

| option | ce qu'elle fait |
|---|---|
| `--cockpit <chemin>` | passe le chemin du cockpit aux ~~**2 gates qui le comprennent** (`verif_dossier_dn415.py`, `verif_ledger_dn416.py`)~~ **4 gates qui le comprennent** — `verif_campagne_dn440.py`, `verif_dossier_d5_dn45.py`, `verif_dossier_dn415.py`, `verif_ledger_dn416.py`. Sans elle, elles cherchent `~/projects/compagnon_project` et **échouent fermé** si l'arbre est ailleurs.<br><br>⚠️ **DATÉ LE 2026-09-04 (`dn5-3`), ⛔ pas réécrit — et le « 2 » était DÉJÀ faux avant cette story.** Mesuré au motif exact que cherche le runner (la déclaration `argparse` de l'option, **guillemets doubles compris**) : elles étaient **3** dès `f4848e4`, `verif_campagne_dn440.py` ayant reçu l'option sans que personne ne mette cette ligne à jour. La voie (a) de `dn5-3` en fait **4**.<br><br>🔴 **CORRIGÉ À LA REVUE DE CODE DU 2026-09-04 — ⛔ la phrase ci-dessus n'est pas effacée, elle est FAUSSE et c'est écrit.** Rejoué au motif exact du runner : à `f4848e4` elles sont **2** (`verif_dossier_dn415.py`, `verif_ledger_dn416.py`) — et `tools/verif_campagne_dn440.py` **n'existe pas** à ce commit. Elles passent à **3** en `3325c39`, la baseline de `dn5-3` elle-même. ⚠️ **Le « 4 » d'aujourd'hui, lui, est juste.** 🎯 Une annotation dont le sujet est *« le compte se mesure, il ne se recopie pas »* avait recopié un commit. ⇒ le compte se **mesure**, il ne se recopie pas : `grep -l -- 'add_argument("--cockpit"' tools/verif_*.py`.<br><br>🔴 **ET LE « 4 » EST FAUX DEPUIS, MESURÉ LE 2026-09-11 : LA COMMANDE CI-DESSUS REND **6**.** ⛔ La ligne n'est pas effacée — elle est datée, comme les deux précédentes. Les deux qui manquent : `verif_boitier_dn64.py`, qui a reçu l'option **sans que cette ligne bouge** (le défaut exact que l'annotation de 2026-09-04 dénonçait, re-commis), et `verif_harnais_dn81.py`, posée par `dn8-1`. 🎯 **Une ligne qui se termine par « le compte se mesure, il ne se recopie pas » avait, elle, recopié un compte — trois fois de suite.** ⇒ ⛔ ne plus écrire de compte ici : la commande est la seule source. |
| `--silencieux` | tait le **motif** des NON-JOUABLES. ⛔ Ne tait rien d'autre : la sortie d'une gate ROUGE reste imprimée, toujours. |
| `-h`, `--help` | l'en-tête du script — ses **cinq** règles. ⚠️ **La table des NON-JOUABLES n'y est PAS** : elle vit dans le corps du script, et l'aide dit comment la lire (`sed -n '/^NON_JOUABLES=(/,/^)/p'`). *(Corrigé à la revue du 2026-09-02 : cette ligne annonçait quatre règles et une table que la sortie ne contenait pas.)* |

### Les NON-JOUABLES aujourd'hui — **sept**

⚠️ **Elles ne sont non-jouables que là où leur témoin manque.** Sur le poste de
l'auteur, six des sept ci-dessous sont **JOUÉES** — le témoin est là, et le runner
l'imprime (`[  temoin  ] … est present ⇒ la gate est JOUEE`).

| gate | motif | ce qui la rend jouable | `rc` sans son témoin |
|---|---|---|---|
| `tools/verif_sr03.py` | le PDF **[AN] AN4545** (VL6180X, DocID026571 Rev 1) **n'est pas au dépôt** — document STMicroelectronics, ⛔ non redistribuable. La gate l'attend en argument et sort sur son message d'usage. | poser le PDF en `tools/fixtures/AN4545.pdf` (son **sha256** est écrit dans la gate, qui refuse tout autre fichier) | `2` |
| `tools/verif_dossier_dn415.py` | **le cockpit de planification n'est pas dans le clone** — c'est un dépôt **privé**, ⛔ jamais publié. Sans lui elle n'a aucune occurrence à arbitrer. | le dossier du cockpit (`~/projects/compagnon_project`, ou `--cockpit <chemin>`) | `4` |
| `tools/verif_ledger_dn416.py` | **idem** — sans le cockpit il n'y a ni ledger ni tracker à confronter. ⚠️ « le dépôt code EST desknode » reste un **contrôle** : son échec reste un **rouge**. | le dossier du cockpit (`~/projects/compagnon_project`, ou `--cockpit <chemin>`) | `4` |
| `tools/verif_dossier_d5_dn45.py` | ~~elle lit **deux chemins ABSOLUS** de la machine de l'auteur ⇒ ⛔ `HOME` n'y peut rien. **Verte dans un clone posé sur cette machine, rouge sur un runner** : le seul des six qu'aucune mesure prise depuis ce poste ne pouvait montrer. La réparation est `dn5-3`.~~<br><br>✅ **RÉPARÉE LE 2026-09-04 — ⛔ la ligne d'origine est barrée, pas effacée : elle disait vrai.** Elle ne lit plus **aucun** chemin absolu : sa racine dérive de `__file__` et le cockpit est un **argument**. ⇒ son motif est désormais **le même que celui des deux gates au-dessus** : le cockpit est un dépôt **privé**, ⛔ jamais dans le clone. 🎯 **Et sans lui elle ne se tait plus** : elle contrôle les **4** fichiers faisant autorité qui vivent dans le clone, **imprime les 2** qu'elle n'a pas pu atteindre, et rend `4` — ou **`1`** si elle trouve un vrai KO, dans cet ordre. | le dossier du cockpit (`~/projects/compagnon_project`, ou `--cockpit <chemin>`) | `4` |
| `tools/verif_veille_dn33.py` | **`managed_components/` est gitignoré** (186 Mo) et porte le générateur **amont** de LVGL. ⛔ 2 blocs sur 18 ne sont pas exercés ; **tout le reste est joué**. | `idf.py reconfigure` dans `firmware/desknode` | `4` |
| `tools/verif_harnais_dn413.py` | **idem** — sans l'arbre LVGL le corpus C est **incomplet**, et la chasse aux renvois fantômes accusait des fonctions **qui existent**. Elle **déclare** désormais, ⛔ elle n'accuse plus. | `idf.py reconfigure` dans `firmware/desknode` | `4` |
| `tools/verif_hist_dn413.py` | **idem** — elle **relit** `LV_CHART_POINT_NONE` dans l'en-tête LVGL, ce qui garantit que la sentinelle d'historique vaut bien celle de LVGL. Elle échoue **fermé**, ⛔ elle ne plante plus. | `idf.py reconfigure` dans `firmware/desknode` | `4` |

> 🔴 **`rc=2` de `verif_sr03.py` n'est PAS un rouge** — c'est son message d'usage. Le
> confondre avec un échec a coûté un « deux rouges » dans le dossier là où il y en avait
> **un de code** et **un d'instrument**, qui ne se corrigent pas de la même façon.
>
> 🔴 **`rc=4` n'est pas un rouge non plus** — c'est « il me manque un dépôt ou un
> arbre », et la gate l'**imprime avec son motif et son remède**. ⛔ Ce n'est pas un
> skip : `run_gates.sh` **joue la gate quand même** et exige **exactement** ce `rc`.
> Un `rc` différent — un vert compris — fait sortir le runner en **1** avec
> `⛔ DECLARATION DEMENTIE`.

### Ce que `tests/` contient, et pourquoi

Rien — et c'est **écrit** : voir `tests/README.md`. La vérification rejouable de ce dépôt,
ce sont **les gates**, et elles vivent dans `tools/`.

## 🔴 LES INSTRUMENTS DISENT QUAND ILS MENTENT (`dn4-23`)

> **Une règle, quatre conséquences.** Elles ne sont pas des conseils : elles sont **posées
> dans le code**, et chacune a son **témoin négatif jouable sans carte**.

### 1. **Un harnais qui pose une commande LIT LE REFUS**

⛔ **C'est la règle.** Un pilote qui envoie une commande et ne regarde pas si la carte l'a
**refusée** ne mesure pas la carte : il mesure son propre silence.

📊 **Ce que ça a coûté, mesuré** : **deux fenêtres de 90 s ont rendu `0`** sur un stimulus
qui **n'a jamais tourné** — `anim on 10` ⇒ `refusé : ESP_ERR_INVALID_ARG`, `flash on` ⇒
`refusé : ESP_ERR_INVALID_STATE`. Les deux refus étaient **à l'écran, en clair**.

`tools/dn_console.py` inspecte donc la sortie de **chaque** commande et cherche **cinq**
motifs. Les trois derniers viennent du **REPL d'ESP-IDF lui-même**
(`components/console/esp_console_common.c`) et valent pour **toute** commande qui rend non
zéro — **y compris celles qui n'impriment rien** :

| motif | origine |
|---|---|
| `refusé(s) :` / `refuse :` / `REFUSE :` | **notre** convention (⛔ le compte n'est plus récité ici : il se périmait au commit suivant) |
| `ESP_ERR_…` | `esp_err_to_name()`, partout |
| `Unrecognized command` | REPL ESP-IDF |
| `Command returned non-zero error code: 0x…` | REPL ESP-IDF — ✅ déjà lu par `sonde_horloge_dn418.py` |
| `Internal error: …` | REPL ESP-IDF |

- Le refus est **imprimé en tête**, ⛔ pas noyé, et le **code de retour est non nul**.
- `--refus-tolere <commande>` le désarme **commande par commande**, pour les campagnes où
  le refus **est l'objet de la mesure** (un scan I²C sur une adresse absente). ⛔ **Jamais
  par défaut**, et le refus reste **imprimé**.
- ⛔ **Ne pas se contenter du français** : une commande peut refuser **sans imprimer un mot**.

### 2. **La console COMPTE ce qu'elle émet, et le pilote LIT ce compteur**

Chaque commande se termine par `--- fin : N lignes emises ---`, et `dn_console.py`
**confronte** ce `N` à ce qui est arrivé. ⛔ **Un compteur que personne ne lit ne compte pas.**

| verdict | ce qu'il veut dire |
|---|---|
| **PERTE** (reçu < annoncé) | 🔴 des lignes **manquent** — rc non nul, ⛔ ne rien conclure, **rejouer** |
| **LIGNES ÉTRANGÈRES** (reçu > annoncé) | ⚠️ un `ESP_LOGx` **asynchrone** est tombé pendant la commande. ⛔ Ce n'est **pas** une perte |
| **SANS COMPTEUR** | ⛔ **pas** « 0 perte » — « **on ne sait pas** ». **DEUX** causes : firmware antérieur à `dn4-23`, **ou la ligne de compteur elle-même a été perdue**. `--exiger-compteur` en fait un échec |
| **COMPTE NON FIABLE** | la carte déclare son propre compte invalide (sortie tronquée faute de RAM) — rc non nul |
| **verdict NON CRÉDIBLE** | 🔴 la carte a écrit `DRAPEAU LEVE` / `NE PAS CONCLURE` / `TEMOIN POSITIF EN ECHEC` : elle publie un chiffre qu'elle désavoue ⇒ rc non nul (revue 2026-08-31) |

🔴 **L'ANGLE MORT DE CET INVARIANT, ÉCRIT PLUTÔT QUE TU** (revue du 2026-08-31) : c'est une
**somme signée par capture**. Une ligne **perdue** et une ligne **étrangère** dans la même
capture **s'annulent** et rendent `OK`. La source **structurelle** de surplus a été tarie
(`dn_ui_log_mem()` et `dn_wifi` imprimaient **hors** du compteur : 6 et 13 lignes non
annoncées, donc `LIGNES ÉTRANGÈRES` permanent sur ces commandes) ; ce qui reste, c'est le
log asynchrone, et **deux nombres ne peuvent pas le distinguer d'une perte simultanée**.
L'instrument **imprime** cette limite au lieu de la taire.

⛔ **LA PARADE DE `dn4-2` EST INSUFFISANTE, ET C'EST ÉCRIT** : elle demandait *« toute
passe publiée vient d'une invocation SOLO »*. **La perte existe aussi en solo — 1 sur 7**
(et 6 sur 20 en lot). Le second point de la parade — l'invariant arithmétique par capture —
reste bon : c'est lui qu'on **généralise ici à toute commande**.

⚠️ **La cause reste NON INSTRUITE, et on n'en invente pas une** : **2 A/B et 30 passes de
contrôle** n'ont rien reproduit. **Cet outillage rend la perte VISIBLE ; il ne la supprime
pas.**

⛔ **UNE CAPTURE VIDE NE PROUVE PAS UNE CARTE MUETTE** : aux cycles 1 et 6 de l'A/B du
2026-08-24, **re-sonder a rendu la sortie complète**.

### 3. **Tout chiffre où le DESSIN est la variable se mesure sous agent RÉEL, ou avec `--jeu rampe`**

Les quatre jeux de `tools/dn_injecteur.py` (`pire` · `reel` · `nominal` · `trou`) sont des
**dictionnaires de constantes**. Une valeur qui ne change pas ne change pas le **texte** ;
un texte qui ne change pas **n'invalide rien** ; LVGL ne redessine que ce qui est invalidé.

📊 **Mesuré, et ⛔ CE N'EST PAS CE QUE CETTE SECTION DISAIT** — corrigé par la revue du
2026-08-31 : la séance carte a mesuré que **l'aire cumulée est LA MÊME**, jeu fixe ou jeu
variable (**11,37 M px** à 1 % près, **3 passes chacun**). ⇒ **le jeu variable ne fait PAS
dessiner plus**, et l'écart « 94 645 contre 128 613 » mesurait **LA CADENCE**
(1 Hz contre 14/20/26/34 s), ⛔ **pas la fixité**. Le repère **94 645 ne se reproduit pas**
non plus (46 572 · 71 984 · 74 576) ; le repère `mock`, lui, **tient** (124 750).

📊 **CE QUI RESTE MESURÉ, ET C'EST UNE AUTRE MESURE** : **0,005 corruption/s** contre
**0,54 /s** sous agent réel — **facteur 108**. C'est **ça**, et ça seul, qui rend un jeu
figé impropre à décrire un régime réel.

⇒ `--jeu rampe` fait **varier** les 16 grandeurs (rampes triangulaires, **16 périodes
premières deux à deux**, dans les bornes de `k_metriques[]`). L'injecteur **annonce au
démarrage** si son jeu est fixe, et ce que ça interdit de conclure.
⛔ Les quatre jeux figés **restent** : ils sont justes pour la **mise en page**.

### 4. **Une latence ne se publie JAMAIS en moyenne seule**

📊 **Mesuré sur `fd959f2`** : `acceptation→label` = **86 · 138 · 220 · 86 · 260 ms** —
**facteur 3 sur le MÊME firmware**.

- `dn_injecteur.py --latence N` joue **N fenêtres consécutives** et publie **la dispersion**.
- `--latence-delta A.json B.json` **REFUSE** le delta quand un relevé n'a **qu'une fenêtre**,
  ou quand les deux **étendues se chevauchent**. ⛔ **Refusé par l'outil**, ⛔ pas déconseillé
  dans un commentaire.
- ⚠️ **Conséquence rétroactive** : tout écart de latence publié sur une **fenêtre unique**
  est **non recevable**, **y compris ceux de `dn4-2`**.
- ⛔ **La règle réfutée reste réfutée** : *« un relevé n'est recevable que si l'injecteur a
  placé 225/225 avec 0 perte seq »* a été **publiée puis démolie** par la 5ᵉ fenêtre
  (225/225, 0 perte seq, **260 ms** — la plus haute). ⛔ Ne pas la ressusciter.
- ✅ **Deux hypothèses restent RÉFUTÉES** — fragmentation du tas LVGL, compteurs de liaison.
  ⛔ Ne pas les rejouer. **La variance n'est pas isolée, et cette story ne l'isole pas.**

### 5. **`cpu` ne bloque plus le transport qu'il mesure**

`cpu N` **dort dans la tâche du REPL** — c'est-à-dire dans le transport. Elle décrivait donc
le dashboard **au repos**, quel que soit le trafic (**0,8 % sous trafic contre 0,9 % au
repos**). Elle le **dit maintenant, avant de dormir**.
⇒ `cpu depart` … *session* … `cpu delta` : **aucun `vTaskDelay`** entre les deux points, et
la fenêtre **refuse de publier** au-delà de l'horizon de rebouclage (**2^32 µs ≈ 71,6 min**).

### Les témoins, jouables **sans carte**

```bash
python3 tools/dn_console.py   --temoin-negatif   # refus · complétude · dispersion
python3 tools/dn_injecteur.py --temoin-negatif   # rampes dans les bornes RELUES
python3 tools/verif_instruments_dn423.py         # la gate (jouée par run_gates.sh)
```

## 🔴 L'ÉTAT DE DÉMARRAGE, ET LE DÉFAUT CONNU QU'IL ANNONCE (`dn4-43`)

### Ce que tu vois au premier branchement, et **ce que ça veut dire**

Au démarrage, la dalle porte pendant environ une seconde et demie :

```
                    DESKNODE
                  DÉMARRAGE...
              contrôle du bus I2C
```

⚠️ **CE N'EST PAS UNE PANNE, ET CE N'EST PAS UN ÉCRAN DE CHARGEMENT DÉCORATIF.**
Pendant ce temps, le firmware **observe réellement** le bus I²C : il attend que les
transactions du contrôleur tactile cessent de rater. Il s'en va **sur un critère relu de
l'état réel**, ⛔ pas sur un minuteur — c'est pour ça qu'il est bref sur une carte qui va
bien, et plus long sur une carte qui démarre à froid.

**Quand il disparaît, la carte répond au doigt.** C'est le signal — **sauf dans un cas, et
il est nommé ici plutôt que tu.**

⚠️ **SI LE CONTRÔLEUR TACTILE N'A PAS RÉPONDU DU TOUT AU DÉMARRAGE** (nappe débranchée,
GT911 mort), il n'y a **rien à observer** : l'écran de démarrage se retire presque
aussitôt — en une fraction de seconde, à peine visible — et le dashboard prend la dalle
**sans jamais répondre au doigt**. Les deux lignes ci-dessous ne s'affichent pas non plus,
puisqu'aucune erreur ne peut être mesurée sur un bus que personne n'interroge.
⇒ **Dans ce cas-là, la disparition rapide de l'écran n'est PAS le signal que la carte est
prête.** Le journal série le dit sans ambiguïté (*« aucun indev tactile : l'observation
était IMPOSSIBLE, ⛔ pas concluante »*), et la commande `touch` dit **où** la séquence a
échoué.

🔴 **ET SI, ET SEULEMENT SI, DES ERREURS SONT RÉELLEMENT MESURÉES**, deux lignes de plus
apparaissent — ⛔ elles ne s'affichent pas « au cas où » :

```
           le tactile ne répond pas encore
        c'est connu, et ça revient tout seul
```

### 🔴 DÉFAUT CONNU — ~40 s de tactile dégradé après un démarrage **À FROID**

> **Sur environ 1 démarrage à froid sur 6**, pendant les **~40 premières secondes**, les
> transactions I²C du contrôleur tactile GT911 échouent à **55,5 %** (950 erreurs sur
> 1 713 lectures, **mesuré**, `hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` §13.17.1).
> **Le doigt semble alors ne rien faire.**
>
> ✅ **LE DÉFAUT EST TRANSITOIRE ET AUTO-RÉTABLI** : passé ce délai, plus **aucune** erreur
> nouvelle n'apparaît (compteur figé à 950 pendant +862 lectures) et la carte redevient
> pleinement utilisable, **sans aucune intervention**. Le capteur d'ambiance, lui, revient
> vers T+60 s.
>
> ⛔ **NOUS NE LE TAISONS PAS, ET NOUS NE LE RÉPARONS PAS ENCORE.** La cause est nommée —
> *dégradation transitoire des transactions multi-octets sur tout le bus après un démarrage
> à froid* — et son traitement est une tâche à part entière, ⛔ pas un correctif discret.
> Ce que cette version livre, c'est que **le défaut soit ANNONCÉ** au lieu d'être découvert
> par quelqu'un qui croira son module cassé.

⚠️ **DEUX PIÈGES SI TU VEUX LE REPRODUIRE :**

- 🔴 **`reboot` NE LE REPRODUIT PAS.** Il laisse le rail 3V3 debout. **Seul un débranchement
  physique du câble USB** (~3 s) coupe réellement l'alimentation — ⛔ ni `reboot`, ni le
  retrait de `VCC` (alimentation fantôme, §13.10).
- 🔴 **LE SCAN `i2c` MENT PENDANT CETTE FENÊTRE.** Il annonce *« 8 stables, 0 instable »*,
  témoin positif **vert**, pendant qu'une transaction de donnée sur deux échoue.
  *Le scan DÉCOUVRE, seule une transaction de DONNÉE QUALIFIE.*

### Le lire après coup

```bash
dem      # verdict, durée, erreurs I2C VUES, fenêtres relancées — et ⛔ TOUJOURS ses limites
touch    # les compteurs bruts du GT911
```

⚠️ Un verdict `PLAFOND` ne veut **pas** dire « la carte est prête » : il dit **« on a cessé
d'attendre »**. Et `builds` doit valoir **1** — un 2 dirait que l'état de démarrage se
ré-affiche, c'est-à-dire qu'il ment sur ce qu'il mesure.

## 🆕 Installer DeskNode — **une seule chose à lancer**, et aucun droit administrateur

> Cette section s'adresse à quelqu'un qui vient de récupérer le dépôt et **n'a rien à
> comprendre du projet pour l'essayer**. Tout ce qui suit est mesuré sur une machine
> Windows le 2026-09-08.

**Le geste :** double-cliquer **`installeur/DeskNode-installeur.bat`**.

Ce fichier démarre un petit serveur **sur votre propre machine**, puis ouvre votre
navigateur sur une adresse en `http://127.0.0.1:<port>`. **Depuis cette page, vous posez
le firmware sur la carte** — sans installer d'outil et sans le moindre pilote. **Le port est tiré au lancement**,
il change à chaque fois — c'est voulu : un port fixe peut être déjà pris chez quelqu'un
d'autre, et *mettre à jour DeskNode, c'est le réinstaller*, donc le deuxième lancement est
le cas de tout le monde, ⛔ pas un cas rare.

⛔ **Rien là-dedans ne demande de droits administrateur**, et ce n'est pas une promesse en
l'air : la tâche planifiée de l'agent est posée en `-RunLevel Limited`, et l'outil qui la
pose **traite un autre niveau comme un défaut** et s'arrête dessus. Un installeur élevé
ferait donc échouer l'outil qui existe déjà.

### Ce que la page sait déjà faire

| geste sur la page | ce qui est appelé | comment c'est vérifié |
|---|---|---|
| **Arrêter l'agent et rendre le port** | le verbe `stop` de `tools/dn_agent_tour.ps1`, **sur le port découvert** | l'outil **rouvre le port** — et « rendu » (`0`) et « disparu » (`7`) sont rendus **distincts**, ⛔ pas confondus |
| **Installer DeskNode sur la carte** | ESP Web Tools, **épinglé `10.4.0`**, avec `installeur/charge/manifest.json` | les **quatre** morceaux aux **quatre** offsets, ⛔ sans binaire fusionné ; la version annoncée est **lue dans le binaire servi**, et une gate refuse qu'elles diffèrent |
| 🆕 **Se brancher à la carte et lire sa console** | **rien du dépôt** : la page ouvre **son** port avec l'accès série du navigateur, à **115200** bauds | une gate vérifie que l'entrée est un élément **distinct** du bouton de flash, que le débit est **déclaré une fois** et que les **trois refus** sont nommés séparément |
| 🆕 **Poser la langue de la dalle sur la carte** | la commande console `langue` que le **firmware livre déjà** — ⛔ la page ne construit aucun mécanisme, elle pose **le choix** | **deux** gates : l'une lit la structure — le choix précède le flash, l'anglais **n'écrit rien**, l'invite est attendue **avant** l'envoi, le succès n'est atteignable que **depuis la relecture** — l'autre **EXÉCUTE** le script de la page contre un port de banc d'essai et rejoue les **neuf** lignes de sa matrice, plus neuf chemins nommés par deux revues |
| 🆕 **Installer les dépendances de l'agent** | **rien de l'outil** : le serveur local joue lui-même le geste publié juste en dessous, **non élevé**, avec **l'interpréteur qui sert cette page** | la commande jouée est **dérivée** de la chaîne publiée, ⛔ pas une seconde copie ; sa sortie et son code de retour vous sont rendus **tels quels**, et l'état est **re-mesuré** ensuite — ⛔ ce n'est pas le code de `pip` qui tranche |
| 🆕 **Activer l'agent** | un **verbe neuf** de `tools/dn_agent_tour.ps1`, qui **compose** la pose de la tâche planifiée **et** le démarrage immédiat | la tâche est **redemandée au système** et le processus **constaté vivant**, ⛔ pas déduits du message ; et l'issue « tâche posée, agent non démarré » a **son propre code**, parce que ⛔ ni un succès ni un échec ne serait vrai |
| **Retirer l'agent** | le verbe `retirer` du même outil | la tâche est **redemandée au système** après coup, ⛔ le message de sortie ne fait pas foi |

⇒ Ces **cinq** gestes **n'inventent rien** — et **deux d'entre eux** *(arrêter, retirer)*
exposent des verbes que le dépôt livre déjà, dont la sortie vous est rendue **telle quelle**,
code de retour compris. Le détail des sept verbes, leurs arguments et ce qu'ils mesurent sont
documentés plus bas, à **§ *« Lancer / arrêter l'agent DEPUIS WINDOWS »***. ⛔ Ils ne sont pas
redits ici : une table dupliquée est une table qui divergera.

> ⚠️ **CORRIGÉ LE 2026-09-09 (`dn7-2-2`) — ⛔ LA VALEUR D'AVANT EST NOMMÉE, PAS EFFACÉE.**
> Cette table listait **quatre** lignes pendant que la phrase juste en dessous disait « ces
> **deux** gestes » : elle se contredisait dans le même paragraphe. Et **deux de ses quatre
> lignes étaient le même geste** — *« Libérer le port »* et *« Arrêter l'agent »* postaient le
> **même** verbe `stop`, sur le **même** port, et rendaient la **même** sortie. ⇒ les deux sont
> **fusionnés** dans la page, le bouton survivant est nommé par **tout** son effet, et une
> entrée **neuve** — la console — prend la ligne libérée.

> 🎯 **COMPLÉTÉ LE 2026-09-09 (`dn7-3`) — ⛔ RIEN N'EST EFFACÉ, UNE LIGNE EST AJOUTÉE.**
> La table portait **quatre** lignes ; elle en porte **cinq**. La cinquième — *poser la
> langue de la dalle* — est le seul geste de cette page qui **écrive** sur le port série :
> la console, elle, ne fait que **lire**, et elle continue.

> 🔴 **CORRIGÉ LE 2026-09-10 (`dn7-4`) — TROIS CONSTATS RELEVÉS À L'ŒIL PAR L'OWNER**, ⛔ par
> aucune gate, et ⛔ **aucun des trois n'est un mensonge de la page** : c'est du **placement**
> et de la **lisibilité**. Ce qui change, et la valeur d'avant est **nommée plutôt qu'effacée** :
> · **Le verdict d'un verbe s'affiche désormais SOUS LE BOUTON QUI L'A DÉCLENCHÉ.** Le
>   transcript n'avait qu'**une** place — après la quatrième étape — pendant que *« Arrêter
>   l'agent »* vit à la **première** : on cliquait, et la vue partait sur l'étape 2 sans qu'un
>   mot change sous les yeux. ⚠️ C'est **le défaut que `dn7-2-2` avait corrigé pour
>   « Retirer »**, survivant **dans l'autre sens** : une place **fixe** ne peut pas servir deux
>   boutons éloignés de quatre gestes. ⇒ la place devient **mobile**, et un fait de **page** —
>   « pas de serveur », écrit **sans clic** — **revient à sa place d'origine**, parce que
>   l'attribuer au dernier bouton cliqué publierait une **cause fausse**.
> · **Le geste de langue relaie le refus EXACT de la console.** La page **connaissait** la
>   cause — *« le sélecteur a été fermé sans sélectionner la ligne »* — et l'écrivait dans le
>   bloc de l'**étape 4**, pendant qu'elle affichait une **supposition** à l'étape 3 : *« le
>   plus souvent, un sélecteur de port est déjà ouvert »*. ⇒ le fait nommé remonte **là où
>   l'œil est**. ⛔ **Aucun texte neuf n'a été écrit** : la phrase de supposition **reste**,
>   pour le **seul** cas où elle est **vraie** — une ouverture réellement **déjà en vol**.
> · **La position active d'un sélecteur est en APLAT**, ⛔ plus en contour. Les deux règles
>   d'état portaient **exactement** les déclarations du **survol** : survoler une position
>   inactive la faisait **passer pour active**. ⚠️ Ce n'est ⛔ pas du confort — toute la
>   propriété du **défaut anglais structurel** suppose qu'on **VOIE** quelle position est
>   active, et la confusion a coûté **une mauvaise lecture dans la séance même**.
> ⚠️ **CE QUI MARCHAIT DÉJÀ ET N'A PAS BOUGÉ** : le bloc d'état du geste de langue était
> **bien placé** (vu sans défiler), et celui de la console **reste dans l'étape 4** — c'est sa
> place. Les deux ⛔ **ne sont pas le même problème**.
> 🔴 **ET CE QUI N'EST PAS MESURÉ EST ÉCRIT ICI PLUTÔT QUE TU.** Ce que ce dépôt sait tenir,
> ce sont les **mécanismes** : deux vérifications les gardent, l'une structurelle et l'autre
> qui **exécute** le script de la page contre un port de banc d'essai. ⛔ **Aucune n'ouvre un
> navigateur et aucune ne dessine** — donc ⛔ **aucune ne dit que le lecteur voit quoi que ce
> soit**. Que la position remplie se lise comme « choisie » d'un coup d'œil se ferme **à l'œil
> de l'owner**, sur la page servie, et cette observation ⛔ **n'avait pas été relevée** quand
> ce bloc a été écrit.

> 🎯 **COMPLÉTÉ LE 2026-09-10 (`dn7-6`) — ⛔ RIEN N'EST EFFACÉ, ET LA TABLE CHANGE DE COMPTE.**
> Elle portait **cinq** lignes ; elle en porte **sept**. ⚠️ **La phrase juste au-dessus,
> *« Ces cinq gestes n'inventent rien »*, a donc cessé d'être exacte sur DEUX points, et elle
> est nommée ici plutôt que réécrite** : le compte n'est plus cinq, et *« n'inventent rien »*
> n'est plus vrai de tous — le geste **« Activer l'agent »** appelle un **verbe neuf**, écrit
> pour cette marche. ⛔ Ce qui reste vrai mot pour mot : il ne **réimplémente** rien, il
> **compose** deux verbes que le dépôt livrait déjà, et il ⛔ **ne redéclare aucun réglage de
> la tâche planifiée** — le niveau limité vient **avec** le bloc réemployé, ⛔ pas d'une
> consigne qu'on pourrait oublier.
> 🔴 **ET LE FIL CONDUCTEUR DE `dn7` EST AMENDÉ, DATÉ, PAR DÉCISION OWNER** : *« `dn7` EXPOSE,
> ⛔ elle ne construit rien »* était vrai de `dn7-1` à `dn7-3` ; il **cesse ici**, sur
> l'arbitrage du 2026-09-10 — *« elle installe dans la mesure du possible, sinon elle
> expose »*. ⛔ La phrase d'avant n'est pas effacée : elle décrivait exactement ce que la
> page faisait ces trois marches-là.

🆕 **Relire la carte ne passe plus par le bouton qui la flashe.** Jusqu'au 2026-09-09, le
**seul** chemin vers les logs de la carte était le bouton d'installation : pour **regarder**
sa carte, il fallait cliquer sur ce qui annonce qu'on va la **réécrire**. La page porte
désormais une entrée **« Se brancher à la carte et lire sa console »**, et un geste explicite
**« Fermer et rendre le port »** qui relâche le port — ⛔ pas de port retenu en silence.
⚠️ **Et les trois refus sont nommés séparément** : *pas d'accès série dans ce navigateur* ·
*aucun port choisi* (le sélecteur fermé sans sélection) · **port refusé** — ce dernier voulant
dire que le port **existe**, qu'il a été **choisi**, et que **l'agent le tient**. ⛔ Jamais
« aucune carte » pour un port refusé : c'est le message qui n'explique rien.

🆕 **La page parle deux langues, l'anglais par défaut.** Le sélecteur est **en tête**, ⛔ pas
dans un menu. Le défaut anglais est **structurel** — il tient à l'attribut de la racine du
document et à une règle de style, ⛔ pas à un script qui aurait pu ne pas tourner.
⚠️ **⛔ Aucune mémoire n'est promise, et c'est mesuré** : le serveur tire **un port différent à
chaque lancement**, donc une **nouvelle origine** à chaque fois, donc **aucun stockage de
navigateur ne survit**. La page revient en anglais à chaque lancement, et elle ⛔ ne prétend
pas le contraire. ⚠️ ⛔ **À ne pas confondre avec la langue de la DALLE**, qui est un autre
sujet et une autre langue.

🆕 **Et la langue de la DALLE se choisit maintenant sur la page, avant le flash.** Deux
positions — **anglais par défaut** — posées **juste au-dessus du bouton d'installation**, sans
rien dérouler, et un **geste explicite** qui l'écrit dans la carte **après** le flash.

- 🔴 **Choisir l'anglais n'écrit RIEN dans la carte, et c'est la propriété.** Le défaut de la
  dalle est **structurel** : elle démarre en anglais quand sa NVS ne porte **aucune** langue.
  Écrire une valeur qui voudrait dire « anglais » remplacerait un **défaut** par un **choix** —
  ce n'est pas la même chose le jour où le défaut change. ⇒ le défaut se prouve **par l'absence
  d'écriture**, et c'est **mesuré** : le geste joué avec l'anglais choisi écrit **zéro octet**.
- 🔴 **Le geste est explicite, ⛔ pas enchaîné à la fin du flash**, et deux mesures le décident :
  la page ne porte **aucun écouteur** sur le module de flash, et **le délai entre la fin du
  flash et le moment où le REPL répond n'est pas mesuré**. Un envoi trop tôt perdrait la ligne,
  et une ligne perdue produirait *« un succès annoncé sur une langue non posée »*. ⇒ le geste
  **réveille** la console et **attend l'invite** avant d'envoyer quoi que ce soit.
- 🔴 **On relit l'acceptation, puis l'ÉTAT — ⛔ jamais l'ordre envoyé.** Après l'ordre, la page
  redemande la langue à la carte et n'annonce *« posée »* **que si la relecture porte le code
  choisi**. **Cinq issues, cinq messages distincts**, chacune reconnue par le littéral que la
  commande imprime **pour elle** : *posée* · *refusée* · *posée à chaud mais ⛔ NON gardée* ·
  *sans réponse* · *pas d'invite*. ⛔ Jamais « posée » pour un silence, ⛔ jamais « refusée » pour
  une absence d'invite — et quand la carte refuse, **ses propres mots vous sont rendus tels
  quels**. ⚠️ **La troisième existe parce qu'elle a été MESURÉE** : quand la carte n'arrive pas à
  ranger le réglage, elle imprime son avertissement, **puis reconstruit la scène, puis** imprime
  la ligne de succès. Les deux moitiés tombaient dans le même motif ⇒ la page aurait annoncé
  l'inverse de ce que la carte venait d'écrire. Sa clé dit **les deux faits** : la dalle **a**
  changé, et ⛔ elle **ne gardera pas** ce changement.
- ⚠️ **Et *« posée »* ⛔ ne promet PAS qu'un redémarrage y survive.** Le firmware pose la valeur
  **à chaud AVANT** de l'écrire : la relecture rend donc le code choisi que l'écriture ait réussi
  ou non. **La seule preuve** est le bandeau du haut de la dalle, **après une coupure
  d'alimentation**, et ⛔ nulle part ailleurs.
- 🔴 **⛔ LE PREMIER DÉMARRAGE APRÈS UNE INSTALLATION EST ANGLAIS, QUEL QUE SOIT VOTRE CHOIX**, et
  c'est mesuré : le flash **efface les réglages rangés dans la carte** (après un flash depuis
  cette page, la commande `cfg` rend *« aucune config en NVS — defauts appliques »*), et la carte
  **redémarre toute seule AVANT** que le geste soit joué. ⇒ **le geste est à rejouer après chaque
  installation** — mettre DeskNode à jour, c'est le reflasher. La page le dit à l'étape qui pose
  la langue.
- ⚠️ **Ce que la page ⛔ ne construit PAS** : le mécanisme. La commande console, la clé NVS et la
  table à une définition par chaîne sont **livrées par le firmware** ; cette page pose **le
  choix**, et rien d'autre. `git diff -- firmware/` est **vide** pour cette marche.
- 🆕 **Et ce geste-là est le premier de cette page à être REJOUÉ, ⛔ pas seulement relu.**
  Jusqu'ici **aucun outil du dépôt n'exécutait le JavaScript** de la page d'installation :
  les gates en lisaient la structure. `tools/banc_langue_dalle_dn73.mjs` **extrait le
  `<script>` de la page et l'exécute** contre un DOM et un port de banc d'essai, puis joue
  les **neuf** lignes de la matrice — dont *« le port est tenu par l'agent »*, *« double
  clic »* et *« pas d'accès série »* — plus **neuf** chemins que deux revues ont nommés : le
  port obtenu **par le sélecteur** du navigateur suivi d'une pose complète, la réponse
  *« posée à chaud, non gardée »*, une relecture qui **ne porte pas** le code, un sélecteur
  **déjà ouvert**, un sélecteur **annulé**, un **vrai clic** sur le bouton français, le bloc
  d'installation **révélé** puis **masqué**, et une écriture qui **rejette en vol**. ⛔ Il ne recopie aucune logique : un harnais qui rejoue sa propre copie ne mesure
  que lui-même. 🔴 Et il **sort en non-zéro quand sa chaîne ne se résout pas** : un banc qui
  rend 0 sur une liste tronquée annonce un succès qu'il n'a pas mesuré.
  `tools/verif_banc_langue_dn73.py` le **lance** à chaque passe de `tools/run_gates.sh`. ⚠️ **Le moteur `node` est un prérequis déclaré** :
  s'il manque, cette gate rend **4** avec son motif et elle est portée **non-jouable** —
  ⛔ elle ne sort **jamais verte** sans avoir joué le banc.
  ⛔ **Ce que ce banc ne prouve pas** : il joue une carte **de banc d'essai**. Que la langue
  soit vraiment posée, et qu'elle **survive à une coupure**, se lit **au bandeau de la
  dalle**, à l'œil.
- 🆕 **ANNOTÉ LE 2026-09-12 (`dn8-2`) — ⛔ RIEN CI-DESSUS N'EST EFFACÉ, MAIS DEUX DE SES
  CHIFFRES ÉTAIENT PÉRIMÉS ET UNE DE SES PROMESSES ÉTAIT CREUSE.** Le banc jouait **27**
  cas et non dix-huit (`dn7-4` en avait ajouté deux, `dn7-6` six), et **l'existence d'un
  banc ⛔ ne vaut pas couverture** : mesuré sous `NODE_V8_COVERAGE`, **21 des 93 fonctions**
  du `<script>` de la page n'étaient **jamais entrées**, et **54 des 141 blocs** internes des
  fonctions vivantes jamais atteints — pendant que le banc rendait `27 OK, 0 KO`.
  Ce qui change :
  · le banc **ASSERTE que son DOM n'est pas dégénéré** — et il juge des **VALEURS** : le
  parent d'un élément monté **EST** son conteneur, son frère suivant **EST** celui du
  conteneur. Il le fait **AVANT** d'évaluer la moindre ligne, parce que la page les lit **au
  chargement** ; le témoin `--temoin-dom` **replante** la faute mesurée le 2026-09-10, où deux
  branches de `montrerSortie()` étaient MORTES et le banc restait vert dessus ;
  · il **parle au VRAI serveur** — le `ThreadingHTTPServer` du produit, **lié par la gate**
  sur `127.0.0.1:0` et **fermé dans son `finally`** — au lieu d'un `fetch` qui rejetait
  toujours, et **le pont imite le navigateur** : un POST porte son `Origin`. ⚠️ Sans cela le
  refus `Origin` du produit n'était **jamais** joué comme la page le déclenche — le `fetch` de
  node n'envoie **aucun** `Origin` (valeur reçue : `null`) ;
  · chaque cas **nomme la route ATTEINTE**, lue dans ce que la réponse porte (la commande, et
  **qui** a posé le code) — ⛔ pas le chemin demandé : sous une inversion de routage, la ligne
  « stop ⇒ 200 rc=0 » ⛔ ne bouge pas d'un caractère ;
  · il entre dans les surfaces mortes — **console série** (ouverture, lecture, fin de lien,
  perte de lien, fermeture, `pagehide`, et une **fermeture qui ÉCHOUE**), **langue de la
  PAGE**, `b-dalle-en`, les trois verbes qu'aucun clic n'atteignait.
  🔬 **CE QUE ÇA DONNE, MESURÉ LE 2026-09-12 SANS SERVEUR — le tir que la CI rejoue** :
  **96/100 fonctions exercées** (4 encore mortes) et **131/190 blocs atteints**.
  ⚠️ **Un chiffre « avec le vrai serveur » ⛔ n'est PAS publié ici**, et le motif est
  mécanique : ⛔ aucun appelant **committé** de ce dépôt ne passe `--base` au relevé, donc
  ⛔ personne ne le rejoue — et un chiffre que personne ne rejoue est un chiffre à croire sur
  parole. ⚠️ Les blocs morts passent de **54 sur 141** à **59 sur
  190**, et ces deux comptes ⛔ **ne se soustraient pas** : V8 ⛔ n'émet les blocs internes
  d'une fonction **que** lorsqu'elle a été compilée, donc le **dénominateur MONTE avec la
  couverture**. C'est pourquoi le seuil déclaré dans `tools/banc_couverture_dn82.mjs`
  (**92 fonctions · 120 blocs**) porte sur le **numérateur**, ⛔ jamais sur un ratio.
  🔴 **ET C'EST LÀ LE POINT QUI COMPTE : UNE COUVERTURE QUI MONTE ⛔ NE PROUVE PAS QU'UNE FAUTE
  SERAIT VUE.** C'est **mesuré**, ⛔ pas craint : un premier essai passait de 21 à 5 fonctions
  mortes **et restait VERT sur onze inversions RÉELLES** de cette page — dont l'avertissement
  hors Windows. ⇒ ce qui **juge** est ailleurs : **chaque bloc d'affichage conditionnel** est
  désormais observé dans ses **DEUX** états par un vecteur comparé en entier
  (`etat-hors-windows`, `etat-orphelin`, `etat-port-tenu`, `etat-cdn`, `etat-inactif`,
  `etat-not-allowed`, `etat-unsupported`, le bloc d'installation, `etat-charge`, `etat-deps`,
  `etat-lhm`), et **chacune de ces inversions est replantée par un mutant vu ROUGE**.
  ⛔ **Et ce banc ne devient PAS un navigateur** : il n'a pas de moteur de rendu et il n'en
  aura pas. Ce qu'il gagne est un **serveur réel**, ⛔ pas un DOM réel.
- 🆕 **CINQ DES SIX CODES DU POINT D'ENTRÉE SONT PROVOQUÉS, ET LE SIXIÈME EST LU DANS LE
  FLOT** (`dn8-2`, 2026-09-12). L'en-tête de `installeur/DeskNode-installeur.bat` publie
  `0` `2` `3` `4` `5` `6` ; avant cette date, **aucun n'était provoqué** — la seule chose jouée
  était `prevol()` **par import**, sur **quatre** de ses issues, donc **`2`, `4` et `5`
  n'étaient joués par RIEN**. `tools/verif_entree_dn82.py` provoque désormais **`0`, `3`, `4`,
  `5` et `6`** en appelant **`main()`** du produit — ⚠️ `main()` ⛔ ne prend **aucun
  paramètre** : c'est `sys.argv` qui est **posé**, `--verifier` pour `0`, `3`, `5` et `6`, et
  **`--sans-navigateur`** pour le `4`, parce que sous `--verifier` `main()` **rend avant le
  `bind`** et ⛔ ne peut donc pas le donner — dans une **copie jetable** de
  `installeur/` — la page est réellement retirée, la charge réellement amputée —, et lit chacun
  **par son nom**, `5` **avant** `6`. Le `4` est provoqué en **empêchant le `bind` au niveau
  `socket`**, ⛔ pas en substituant un nom de serveur.
  ⚠️ **Pourquoi `main()` et non `prevol()` : c'est mesuré.** Un `if a.verifier: return 0` —
  c'est-à-dire le précédent `dn7-1` rejoué **un cran plus loin** — laissait la première
  rédaction de cette gate à `36 OK / 0 KO` : `prevol()` rendait toujours ses codes, et
  personne ne regardait ce que le point d'entrée en **faisait**.
  ⛔ **Le `2`, lui, n'est PAS provoqué** : il est posé par `cmd.exe` sur un argument inconnu,
  et la CI de ce dépôt tourne sur **Linux**. Du `.bat`, la gate **modélise le FLOT** —
  étiquettes, `goto`, chute, `exit /b` — et exige quatre choses : toute étiquette à code est
  **atteinte depuis la tête du fichier**, elle pose **le** code que la table déclare, ⛔ **aucune
  étiquette hors table** ne pose de code, les **deux** appels `%PY%` relaient
  `%ERRORLEVEL%` **immédiatement**, et `:FIN` sort par **`exit /b %RC%`**. Ces quatre-là
  étaient absentes, et quatre mutations l'ont démontré en restant vertes.
  ⚠️ **Le tir réel sous `cmd.exe` est NON JOUÉ**, et son porteur est **au ledger**
  (`epic-dn8`) — ⛔ pas une autre marche : aucune AC d'une marche existante ne le porte.
- 📏 **CE QUE COÛTE UNE INTERROGATION D'ÉTAT — MESURÉ, PUIS DÉCLARÉ** (`dn8-2`, 2026-09-12,
  banc WSL). `etat_machine()` coûte **387,73 ms** (médiane, n=5) ; `GET /api/etat` sous les
  doubles de la gate, **3,72 ms**. 🔴 **La moitié qu'on croyait chère est RÉFUTÉE** : relire
  **et** CRC32-er l'asset de **614 416 o** coûte **0,74 ms**, soit **0,2 %** (CRC32 seul :
  **0,20 ms**) — la réduire n'achèterait rien et **coûterait** la garde d'intégrité qui attrape
  l'asset blanc. 🔴 **Et l'attribution de ce qui coûte était FAUSSE, dans ce README même** :
  ce ne sont ⛔ **pas** des « allers-retours PowerShell ». Sur ce banc `powershell` et `pwsh`
  sont **introuvables** (`PATH` : 35 entrées `/mnt`), `_powershell()` rend `rc=None` avec
  `echec='lancement'`, et les **99 / 103 / 107 ms** de `decouvrir_port`, `tache_presente` et
  `localiser_pilote` sont le coût d'un **lancement qui ÉCHOUE**. La sonde réellement chère
  **mesurée ici** est `dependance_presente` : **158,15 ms**, **deux interpréteurs Python par
  module**, et **deux modules** par requête.
  ⚠️ **Le chiffre côté Windows — là où PowerShell existe et où `decouvrir_port` porte un
  plafond de 45 s — est ⛔ NON MESURÉ**, et il ne peut pas l'être d'ici : le WSL de cette tour
  est en **NAT**. ⇒ **387,73 ms est un minorant dont la cause est fausse**, c'est **écrit**, et
  le relevé Windows est **porté au ledger** (`epic-dn8`). ⛔ Aucun cache n'est posé au
  passage : un cache qui survivrait à un débranchement serait **pire** que le coût qu'il
  économise.
- ⚠️ **ET CE QUI RESTE OUVERT, ÉCRIT AVEC SON PORTEUR** : la **lisibilité du choix de
  langue** sur la page servie. La moitié mécanique est livrée — un **vrai clic** sur
  `b-langue-fr` puis `b-langue-en`, `aria-pressed` **relu sur les vrais boutons**, et l'état
  de départ des **quatre** boutons de choix **lu dans le balisage** par un parseur (l'anglais
  est pressé) au lieu d'être supposé par le banc — mais savoir si l'option retenue se
  **distingue à l'œil** ⛔ ne se mesure pas ici : il n'y a aucun rendu dans ce banc, et le WSL
  de cette tour est en **NAT**, donc la page servie ⛔ ne s'ouvre pas depuis lui. ⇒ **écart
  déclaré**, porteur **`dn8-3`** — son `AC8.3.1` ré-héberge `AC7.4.3`, qui porte cette
  lisibilité au ledger.

### 🔴 Ce que vous devez installer vous-même — **écart déclaré**, avec son porteur

DeskNode **ne se télécharge pas encore en UN seul morceau**, et c'est écrit ici plutôt que
découvert au premier lancement :

- il faut **Python 3** (le `.bat` le cherche, et s'il ne le trouve pas il vous donne le
  geste exact : installeur officiel, case *« Add python.exe to PATH »* cochée) ;
- l'agent a besoin de **deux modules**, `psutil` (le % CPU) et `pyserial` (le lien série) :

```
pip install --user psutil pyserial
```

- et il lui faut **LibreHardwareMonitor**, qui n'est ⛔ **pas** un module Python — donc ⛔ pas
  une ligne de la commande ci-dessus. Son geste est **le sien**, et le dépôt le porte déjà :

```
tools\dn_lhm_tour.ps1 -Poser -Permanence tache
```

🔴 **CE QUI TOMBE SANS LUI, MESURÉ : la température du CPU et les trois vitesses de
ventilateur — et ⛔ rien d'autre.** Le % CPU, les GHz, les Mo/s et la case AMBIANCE ⛔ n'en
dépendent pas : la table du haut de ce fichier, **TROIS AXES, ⛔ PAS DEUX — et le troisième
est indépendant des autres**, le mesure ligne à ligne, et c'est le même endroit qui écrit
que **c'est LHM qui coûte l'élévation, ⛔ pas DeskNode**. Sans argument, `dn_lhm_tour.ps1`
**vérifie et ne change rien**.

🔴 **ET DEPUIS LE 2026-09-10, C'EST UN PRÉREQUIS DUR — ⛔ plus un confort.** Arbitrage owner,
verbatim : *« LHM est-il un prerequis DUR !!! car sinon la dalle sert a rien »*. ⇒ le pré-vol
de l'agent **REFUSE** de le lancer sans lui, avec **son propre code de sortie**, **`12`**, et
un message qui nomme LHM, son geste et ce qui tombe sans lui. ⛔ **La page d'installation, elle,
⛔ ne refuse pas** : elle l'**imprime** et **s'ouvre quand même** — poser le firmware sur la
carte ⛔ n'a rien à voir avec LHM, et bloquer la page priverait un inconnu du geste
**principal** pour une dépendance de l'**agent**.
⚠️ **Et le prix est écrit, ⛔ pas tu, en deux pièces mesurées** : *(i)* une machine sans LHM
gardait tout **sauf les quatre grandeurs que LHM publie** — la température du CPU
et les trois vitesses de ventilateur ; elle perd désormais **l'agent entier** — la table
du haut, qui mesure le contraire, est **annotée à sa date**, ⛔ pas effacée, parce que c'est
elle qui rend ce coût lisible ; *(ii)* la tâche de LHM démarre **élevée** à l'ouverture de
session et celle de l'agent ⛔ **non** — les deux tirent sur le **même** événement, donc elles
**se courent après**. La reprise existe déjà et **porte sa borne** : **3 reprises à 1 minute**.
⇒ **au-delà d'environ trois minutes, l'agent est absent TOUTE LA SESSION**, en silence.

🔴 **CORRECTION DATÉE DU 2026-09-12 (`dn4-48`) — LA PHRASE DU REFUS DUR A CESSÉ D'ÊTRE
VRAIE. Elle est reprise ici, BARRÉE, et ⛔ elle n'est PAS effacée là-haut** : elle était
**exacte** du 2026-09-10 au 2026-09-12, et l'effacer effacerait ce que ce dossier savait ces
jours-là.

~~« le pré-vol de l'agent **REFUSE** de le lancer sans lui, avec **son propre code de
sortie**, **`12`** »~~ — **il l'ATTEND, puis il démarre QUAND MÊME.**

🔬 **CE QUI A RÉFUTÉ LE REFUS, ET C'EST UNE MESURE SUR UN VRAI REDÉMARRAGE, ⛔ pas un avis.**
Le 2026-09-12, la tâche au logon a tiré à `18:13:13` et rendu `LastTaskResult = 12` pendant
que le process LHM montait à `18:13:34` — **21 s trop tard**. La dalle est restée **morte, en
silence**, toute la session, sur une machine **SAINE**. ⚠️ **Et la reprise n'a PAS tiré** :
relevé à `18:25`, bien au-delà de la borne publiée juste au-dessus, `LastRunTime` valait
**toujours** `18:13:13` et `NextRunTime` était **vide**. ⇒ la borne décrivait un **délai** ;
le fait mesuré est qu'il ⛔ **n'y a eu AUCUNE reprise du tout**. ⛔ **Le mécanisme, lui, n'est
PAS établi, et c'est dit** : le journal qui le montrerait
(`Microsoft-Windows-TaskScheduler/Operational`) est **éteint** sur cette tour, donc
« aucun événement » est une propriété de **la méthode**, ⛔ pas du Planificateur.

🎯 **CE QUE LE PRÉ-VOL FAIT DEPUIS, ET LE RÉGLAGE DE LA TÂCHE ⛔ N'A PAS BOUGÉ.** Il **attend**
LibreHardwareMonitor, **borné** — `-AttenteLhm <secondes>`, **300 s par défaut**, `0` = aucune
attente, une valeur **négative** est **refusée** (code `3`) et ⛔ jamais repliée en silence.
Chaque tour d'attente **imprime sa ligne** (écoulé / borne) : une fenêtre immobile cinq minutes
serait indiscernable d'un blocage. À l'échéance, le pré-vol **continue** :

- **l'agent DÉMARRE**, et la dalle reste **vivante** — seules la température du CPU et les
  trois vitesses de ventilateur restent à « `--` » ; le % CPU, les GHz, les Mo/s et la case
  AMBIANCE ⛔ n'en dépendent pas. ⚠️ **Ce n'est pas une nouveauté du produit, c'est une
  tolérance qu'il avait déjà** : `agent/dn_agent.py` pose ⛔ **aucune grandeur LHM en position
  0**, précisément pour qu'une source LHM absente n'empêche rien — elle était acquise quand
  LHM meurt **en cours de route**, et refusée au seul cas du **démarrage** ;
- **le pré-vol dégradé rend `0`**, et c'est **load-bearing** : `tools/dn-agent.bat` fait
  `if errorlevel 1 goto :FIN` juste après le pré-vol en `:RUN` — **le chemin de la tâche au
  logon**. Un pré-vol dégradé qui rendrait `12` ferait sauter le lancement, c'est-à-dire
  **exactement la panne réparée**, déplacée d'un cran. ⇒ la dégradation voyage par **l'état
  écrit** (`dn-agent.started`, `dn-agent.bat etat`) et par le **bandeau**, ⛔ jamais par un
  code de retour ;
- **le POURQUOI part sur une surface côté Windows** — `msg.exe`, **sans élévation et sans
  .NET** (`D8` écarte NotifyIcon, qui exige `System.Windows.Forms`, et le toast WinRT, qui
  exige .NET ou un module tiers). ⚠️ **Son défaut est connu et il se DÉCLARE** : `msg.exe`
  est absent des éditions Familiales ⇒ le pré-vol **dit** qu'aucune surface de notification
  n'était disponible, au lieu de laisser croire qu'il a prévenu. ⛔ Une ignorance n'est pas
  un écart : le code de retour ne bouge pas ;
- **`12` change d'émetteur ET de sens, et il reste unique** dans `tools/dn_agent_tour.ps1` :
  il quitte le bloc LHM du pré-vol pour le verbe **poser** — ⛔ le nom n'est PAS mis en
  code ici, et c'est une garde MESUREE : `tools/verif_installeur_dn71.py` (c21) refuse
  qu'un verbe de l'outil soit **redit** dans la section d'installation du README, qui doit
  y **renvoyer** —, où il veut désormais dire
  « la permanence est **posée** et l'agent **TOURNE**, mais **SANS LHM** ». ⛔ Il ne dit plus
  « RIEN n'a été posé » — ce serait **faux**, et enverrait chercher une panne qui n'existe
  pas. La propriété qui survit, et qu'une vérification garde, est qu'il **nomme
  LibreHardwareMonitor**.

⚠️ **CE QUE `dn4-48` ⛔ NE FAIT PAS, ET C'EST DIT PLUTÔT QUE TU.** Elle ⛔ **ne touche pas**
au réglage de reprise de la tâche — le relever déplacerait le coût au lieu de le supprimer,
et la mesure dit qu'il ⛔ **ne tire pas** sur ce mode de panne : elle **supprime la
dépendance** à cette parade, qui reste une seconde ligne de défense pour les **autres**
causes (carte attachée à WSL). Elle ⛔ **n'affiche pas** le motif **sur la dalle** : la trame
`$DN,…` n'a **aucun champ de texte**, il faudrait toucher le protocole **et** le firmware,
que `NFR8`/`H1` gèlent tant que le soak est en cours ⇒ **évolution POST-V1**, arbitrage owner
du 2026-09-12, ⛔ sans porteur V1 et c'est **voulu**. Et ⛔ **la page d'installation garde
l'activation désarmée** tant que LHM ne répond pas : c'est désormais la précondition **de la
page**, ⛔ plus un refus de l'outil, et le geste reste **jouable à la main**
(`tools\dn-agent.bat start`). ⇒ **écart déclaré**, porté au ledger.

🎯 **DEPUIS LE 2026-09-10 (`dn7-6`), LA PAGE INSTALLE LA PREMIÈRE DE CES TROIS CHOSES —
⛔ ET ELLE ÉCRIT POURQUOI ELLE N'INSTALLE PAS LES DEUX AUTRES.** ⛔ Rien de ce qui précède
n'est effacé : les trois manques sont toujours là, et c'est **le geste** qui a changé pour
l'un d'eux.

- ✅ **Les deux modules Python** ont désormais un **bouton** sur la page. Il joue la commande
  publiée juste au-dessus, **non élevé**, avec **l'interpréteur qui sert la page** — donc
  celui dont l'agent se servira, ⛔ pas le premier `pip` du `PATH`. La commande jouée est
  **dérivée** de cette chaîne-là, ⛔ ce n'est pas une seconde rédaction qui divergerait. Sa
  sortie et son code vous sont rendus **tels quels**, et ⚠️ **ce n'est ⛔ pas le code de `pip`
  qui tranche** : l'état est **re-mesuré** ensuite, et c'est cette mesure qui décide.
- ⛔ **LibreHardwareMonitor n'a ⛔ pas de bouton, et le motif est une mesure.** Son propre
  script écrit noir sur blanc que, lancé sans **droits administrateur**, sa vérification
  marche mais qu'il **ne peut pas agir** — et la tâche qu'il pose est élevée. Cet installeur
  ⛔ **ne demande jamais ces droits** ; deux vérifications vivantes de ce dépôt refusent le
  seul chemin qui le permettrait. ⇒ la commande reste **à recopier**, dans une fenêtre que
  vous ouvrez vous-même. ⚠️ Un bouton qui la jouerait non élevée promettrait un geste qui
  **n'agit pas** : ce serait **pire** que pas de bouton.
- ⛔ **Python 3 non plus — et ⛔ ce n'est pas le même motif.** La page ⛔ **ne peut pas** en
  faire une précondition : **sans Python, la page n'existe pas**. Le fichier que vous
  double-cliquez s'arrête **avant d'avoir servi le moindre octet**, et c'est **cette
  fenêtre-là** qui porte le lien et la marche à suivre. ⇒ le lien vit donc **aux deux
  endroits** — dans cette fenêtre, et ici :
  <https://www.python.org/downloads/windows/>, la seule case qui compte étant
  *« Add python.exe to PATH »*. ⚠️ Un lien que personne **dans le besoin** ne peut voir serait
  **pire qu'absent**.

⚠️ **Ce n'est ⛔ ni un oubli ni une panne : c'est le prix, écrit, d'une décision datée.** Le
2026-09-08, l'owner a tranché qu'un **script lançable** suffisait pour la première version,
plutôt qu'un exécutable autonome — le moins coûteux et le plus fiable. Or c'est l'exécutable
qui **absorbait le runtime**. ⇒ **Porteur du retour à « un seul téléchargement » : l'agent
en exécutable autonome, prévu en V0.2.** ⛔ La case n'est **pas** cochée, et la confondre
avec un échec ferait mentir ce dossier.

⚠️ **Deux des trois dépendances de l'agent n'avaient aucune garde** (mesuré le 2026-09-08) :
`agent/dn_agent.py` explique proprement l'absence de `psutil` (l.226-230) mais **pas** celle
de `pyserial` (l.2745) ni celle de `websockets` (l.3155) — celles-là sortent en trace nue.
🔴 **Ce que le pré-vol de l'installeur teste, exactement** : **`psutil` et `pyserial`**, et
⛔ **pas `websockets`**. La phrase publiée ici disait *« il les teste toutes les deux »* avec
`pyserial` **et** `websockets` pour antécédent — c'était **faux**, et ça fermait sur le papier
un trou que personne n'avait bouché. ⇒ le pré-vol déplace le problème pour deux modules sur
trois, ⛔ il ne le referme pour aucun **côté agent** : quelqu'un qui lance `dn_agent.py` sans
passer par l'installeur — ce que la tâche planifiée fait à **chaque** ouverture de session —
retombe sur la trace nue. Le manque est au ledger, porteur `epic-dn4`.

🔴 **CORRECTION DATÉE DU 2026-09-10 — une phrase du paragraphe ci-dessus a CESSÉ d'être vraie.
Elle est reprise ici, BARRÉE, et ⛔ elle n'est PAS effacée là-haut** : elle était **exacte** le
2026-09-08, et l'effacer effacerait ce que ce dossier savait ce jour-là.
~~« Ce que le pré-vol de l'installeur teste, exactement :
`psutil` et `pyserial` »~~ : il teste **aussi LibreHardwareMonitor**, et il l'**imprime** avec
son geste propre. Deux précisions, parce qu'une correction qui en dit trop est une nouvelle
erreur :
- **le code de sortie `6` ⛔ n'a PAS bougé**, et c'est voulu. LHM ⛔ n'entre **pas** dans la
  liste des modules manquants — cette liste commande **à la fois** le `6` **et** le bloc qui
  publie la commande `pip` ci-dessus. Y verser LHM ferait imprimer **le mauvais geste** pour
  une dépendance qui ⛔ n'est **pas** un module. ⇒ LHM a **son** bloc et **son** geste ;
- **la sonde a TROIS positions, ⛔ pas deux** : *présent*, *ABSENT*, et *« non testable ici »*
  — cette dernière quand l'adresse de LHM ne peut pas être relue dans `agent/dn_agent.py`.
  ⛔ Une ignorance **n'est pas** un écart, et elle ⛔ ne pèse **pas** sur le code de sortie.

⚠️ **Et cette adresse est LUE, ⛔ jamais recopiée.** L'hôte, le port et le chemin de LHM sont
des valeurs de `agent/dn_agent.py` ; la page, son serveur local et l'outil de l'agent les y
**relisent** au lieu d'en garder un miroir. Une seconde source de vérité pourrirait **en
silence** le jour où l'un des deux change. Le même principe garde l'écart déclaré lui-même :
les dépendances publiées ici sont **re-dérivées** des `import` réels de l'agent, dans les
**deux sens**, de sorte qu'une dépendance qui apparaît, disparaît ou perd sa garde fasse
**rougir** une vérification au lieu de se taire.

🆕 **ET DEPUIS LE 2026-09-12 (`dn8-3`), CETTE ADRESSE SE **PASSE** JUSQU'À L'AGENT.**
Jusque-là, `tools/dn_lhm_tour.ps1` écrivait en toutes lettres qu'un `-Port` différent du
défaut est une **configuration SUPPORTÉE** — et ⛔ **ni** `tools/dn_agent_tour.ps1` ⛔ **ni**
`tools/dn-agent.bat` ne savaient la transmettre : **zéro** occurrence de `--lhm` dans les
deux. ⇒ sur une tour **saine** dont LHM écoute ailleurs, le pré-vol sondait le port lu dans
`agent/dn_agent.py`, ne trouvait rien, et **refusait de lancer l'agent**.

```
tools\dn-agent.bat run COM3 0 "" 127.0.0.1:8086
tools\dn-agent.bat start COM3 0 -Temoin 127.0.0.1:8086
```

- l'adresse **traverse** `dn-agent.bat` → `dn_agent_tour.ps1` → `DN_ARGS` → l'agent
  (`--lhm HOTE:PORT`), et la **tâche au logon la porte** — vérifiée après la pose, comme
  `-Serie` et `-Temoin` ;
- **sans** cet argument, ⛔ **rien ne change** : l'adresse reste **LUE** dans
  `agent/dn_agent.py`. `-Lhm` **surcharge** une valeur déjà lue, il ⛔ n'en **fige** aucune —
  une seconde source de vérité pourrirait en silence, et c'est précisément ce que le
  paragraphe ci-dessus interdit ;
- une valeur **malformée** est **refusée explicitement** (code `3`), ⛔ **jamais** repliée en
  silence sur le défaut — c'est le défaut que l'agent a payé **quatre fois** en revue ;
- ⚠️ **la 4ᵉ place (le témoin) doit être OCCUPÉE** : `""` si vous n'en voulez pas. Sinon
  `cmd.exe` lit l'adresse en `%4`, et le port part **en silence**.

⚠️ **CE QUI EST MESURÉ, ET CE QUI NE L'EST PAS** (2026-09-12). La **polarité** du refus est
désormais **rejouée dans un vrai `powershell.exe`**, dans les deux sens, par
`tools/verif_lhm_ps_dn83.py`, **dans les TROIS sens depuis `dn4-48`** : LHM qui répond
**sans une seule ligne `lhm_`** ⇒ **démarrage dégradé** (⛔ pas `12`, bandeau qui nomme LHM,
attente imprimée) ; LHM debout sous `-AttenteLhm 0` ⇒ ligne passante et ⛔ **aucune** attente ;
LHM qui **monte APRÈS** le pré-vol ⇒ il **attend**, puis il **passe** — le cas mesuré du
2026-09-12, rejoué. ~~LHM debout ⇒ ⛔ **pas** de refus.~~ 🔴 **En revanche, la TOUR RÉELLE ⛔ n'est PAS mesurée** :
⛔ aucune vérification de ce dépôt n'installe LibreHardwareMonitor, ⛔ n'ouvre un navigateur,
⛔ ne pose de tâche planifiée. Ce qui reste — le bouton grisé **vu**, l'agent activé
**constaté par requête**, la course au logon — est **porté au ledger avec son porteur**, et
se ferme **à l'œil de l'owner**, ⛔ pas ici.

### ⚠️ Si vous avez **téléchargé** ce fichier plutôt que cloné le dépôt

Windows pose une **Marque du Web** sur ce qui vient d'Internet, et peut afficher
*« Fichier ouvert — Avertissement de sécurité »* au premier lancement. **Le geste qui lève
ça** : clic droit sur `DeskNode-installeur.bat` → *Propriétés* → cocher **Débloquer** en bas
de l'onglet *Général* → *OK*. Aucun droit administrateur là non plus.

🔴 **Et c'est aussi la raison d'être du `.bat`.** La politique d'exécution PowerShell mesurée
sur la machine de référence est **`Restricted`**, ses cinq portées `Undefined` : un `.ps1`
double-cliqué est **refusé**, Marque du Web ou pas. Le `.bat` contourne cela exactement comme
`tools/dn-agent.bat` le fait depuis `dn4-17` — en lançant PowerShell avec
`-ExecutionPolicy Bypass`, **pour ce processus-là seulement**, sans rien écrire sur la machine.

⚠️ **RÉSIDUEL DÉCLARÉ, ⛔ pas fermé.** La friction ci-dessus a été reproduite **fidèlement**
en posant le flux `Zone.Identifier` (`[ZoneTransfer] ZoneId=3`) sur une copie hors dépôt. Ce
qui n'a **pas** pu être mesuré, c'est un **vrai téléchargement depuis une vraie release** :
il n'en existe aucune à ce jour. ⇒ cette moitié-là reste ouverte, et **son porteur est
`dn8`**, l'étape qui publie la vitrine et la première release (voir
[`docs/roadmap.md`](docs/roadmap.md)). ⛔ Un *« ça marche chez moi depuis le dépôt »* ne la
ferme pas.

### 🆕 Ce que la page va écrire sur la carte, et **d'où ça vient**

La page sert **quatre images** versionnées dans le dépôt, sous
[`installeur/charge/`](installeur/charge/), plus le manifeste qui dit où chacune se pose.
Les offsets sont ceux **déjà publiés** plus bas dans ce fichier (§ *Voie A*) — ⛔ ils ne
sont pas redits ici, ils sont **les mêmes**, et le manifeste les tient de
`build/flasher_args.json`. Les quatre morceaux se posent **séparément**, ⛔ **sans binaire
fusionné**.

🔴 **La version annoncée est LUE dans le binaire, ⛔ jamais recopiée à côté.** C'est le
champ `version` de `esp_app_desc_t`, à l'offset `0x30` de `desknode.bin` — et
`tools/verif_flash_dn72.py` **refuse** que le manifeste et le binaire servi disent deux
choses différentes. Le prototype de flash du 2026-08-31 annonçait `0.1.0-beta-essai`, la
valeur de son **banc d'essai**, sur des images que plus personne ne savait dater : c'est
exactement ce que ce contrôle rend impossible.

⚠️ **Deux manques sont écrits plutôt que cochés**, et chacun a son porteur :

- **La provenance de ces quatre fichiers n'est mécanisée par RIEN.** Aucune intégration
  continue ne construit ce firmware (`dn4-45`, `not started` — voir
  [`docs/roadmap.md`](docs/roadmap.md)) ; les binaires ont été produits **à la main**, et
  [`installeur/charge/PROVENANCE.md`](installeur/charge/PROVENANCE.md) le dit, avec la
  révision exacte, la commande, les tailles et les empreintes.
- 🔴 **L'obligation GPL-3.0 de pointer la source de CETTE révision est tenue par la
  révision elle-même, ⛔ pas par une source publiquement atteignable.** Mesuré le
  2026-09-08 : `git tag -l` est **vide**, `gh release list` est **vide**, et ce dépôt est
  **privé**. ⇒ ce résiduel est un **écart déclaré**, et **son porteur est `dn8`**, l'étape
  qui publie la vitrine, le tag et la première release.

### 🆕 Ce que vous allez voir au moment de choisir le port

La page le dit **aussi**, parce que c'est elle que vous regardez à ce moment-là. Ici, c'est
pour l'avoir sous la main avant de commencer.

- ~~**Le port ne s'appelle ⛔ PAS « DeskNode »**, et il porte **deux noms selon qui
  l'affiche** : Windows le nomme de façon **traduite** — `Périphérique série USB (COM3)` —
  tandis que la puce se présente comme `USB JTAG/serial debug unit`.~~
- ~~**La sélection se fait en DEUX gestes** : **cliquer la ligne** du port, **puis**
  **« Se connecter »**.~~
  > 🔴 **ANNOTÉ LE 2026-09-09 (`dn7-2-2`) — LES DEUX LIGNES CI-DESSUS SONT BARRÉES PLUTÔT
  > QU'EFFACÉES (`NFR3`), PARCE QUE LE SÉLECTEUR A ENFIN ÉTÉ OUVERT ET QU'IL LES RÉFUTE.**
  > Ce que la mesure du 2026-09-09 montre, à l'œil, dans le sélecteur d'Edge :
  > **UNE SEULE LIGNE**, `USB JTAG/serial debug unit (COM3)`, et un bouton **« Connexion »**.
  > ⇒ Ce qui reste **vrai** de la première ligne : le port ne s'appelle ⛔ **pas
  > « DeskNode »**, et le numéro `COM<n>` change d'une machine à l'autre. Ce qui était
  > **faux** : « deux noms **selon qui l'affiche** » présentait les deux formes comme deux
  > possibilités **du sélecteur** ; la forme localisée est ce que montre le **Gestionnaire de
  > périphériques**, ⛔ **pas** le navigateur.
  > ⇒ Ce qui reste **vrai** de la seconde ligne : il faut bien **deux gestes**, et fermer la
  > fenêtre sans choisir fait sortir sur *« No port selected »*. Ce qui était **faux** : le
  > libellé du second. Il s'appelle **« Connexion »**.
  > 🎯 **MÉCANISME** : Edge nomme le port par la **chaîne produit USB** de la puce, ⛔ pas par
  > le `FriendlyName` **localisé** de Windows. `dn7-2` avait mesuré `Get-PnpDevice` — la vue du
  > Gestionnaire — et l'avait **généralisée** à un sélecteur que personne n'avait ouvert.
  > ⚠️ **La découverte côté serveur, elle, reste JUSTE** : elle vise l'interface `MI_00` et rend
  > le bon `COM<n>`. ⛔ C'est l'**affichage** qui mentait.

🆕 **Ce que le sélecteur montre, tel qu'il a été relevé le 2026-09-09** :

- **UNE seule ligne** : **`USB JTAG/serial debug unit (COM<n>)`**. ⚠️ Le numéro change d'une
  machine à l'autre ; la page affiche **celui qu'elle a découvert** sur la vôtre.
- **Deux gestes** : **cliquer la ligne**, **puis** cliquer **« Connexion »**. Tant que la
  ligne n'est pas sélectionnée, le bouton reste **grisé**, et fermer la fenêtre fait sortir
  sur *« No port selected »* — un message qui n'explique pas qu'il manquait un clic.
- **Ailleurs**, le **Gestionnaire de périphériques** de Windows nomme la même carte
  `Périphérique série USB (COM3)` (nom **traduit**, mesuré sur la machine de référence le
  2026-09-08). C'est utile pour **retrouver son port**, ⛔ ce n'est pas ce que le navigateur
  affiche.
- ⛔ **Si l'outil de flash propose d'installer un pilote (CP2102, CH340, CH342), n'en
  installez aucun.** Ce dialogue parle d'un problème que vous n'avez pas : cette carte est
  en **USB natif** `303A:1001`, et **aucun pilote n'est à installer** — c'est déjà écrit
  plus bas, § *Faits matériels mesurés qui contredisent les recettes courantes*.
- **Si rien ne démarre** : maintenir **`BOOT`** enfoncé, appuyer brièvement sur **`RESET`**,
  relâcher `BOOT`. La carte passe en mode *download*, où le flash marche même quand
  l'application ne démarre plus. Détail et sortie de ce mode : § *La carte est muette ?*.
  ⚠️ **Écart de formulation, écrit plutôt que recopié** : le cadrage de cette page parlait
  de *« BOOT maintenu pendant le branchement »*. Cette formule n'est **écrite nulle part**
  dans ce dépôt et n'a **jamais été mesurée** ; `BOOT` **+** `RESET`, si.

### 🆕 Le deuxième lancement, et pourquoi c'est le cas de tout le monde

**Mettre DeskNode à jour, c'est le réinstaller** — il n'y a qu'un seul parcours. Donc dès la
deuxième fois, **l'agent tourne déjà et tient le port**, et un flash lancé tel quel sortirait
sur `Failed to execute 'open' on 'SerialPort'`, qui n'explique rien.

⇒ La page porte un bouton **« Arrêter l'agent et rendre le port »** qui appelle le verbe
**`stop`** que ce dépôt livre déjà — ⛔ il n'en réimplémente aucun — **sur le port qu'elle a
découvert** (`VID_303A&PID_1001`, interface `MI_00`), ⛔ pas sur le `COM3` par défaut de
l'outil.

> ⚠️ **ANNOTÉ LE 2026-09-09 (`dn7-2-2`) — LE BOUTON S'APPELAIT *« Libérer le port »*, ET IL
> N'ÉTAIT PAS SEUL.** L'ancienne valeur est **nommée ici plutôt qu'effacée** (`NFR3`). Un
> second bouton, *« Arrêter l'agent »*, postait le **même** verbe sur le **même** port : le
> lecteur choisissait entre deux commandes qu'il croyait distinctes. Les nommer par ce qui
> les **distingue** était impossible — rien ne les distinguait. ⇒ **fusion**, et le survivant
> est nommé par **tout** son effet, parce que c'est **un seul** fait.

⚠️ **Et les codes de `stop` ne sont ⛔ pas un booléen** : `0` le port est **rendu** · `4` le
drapeau d'arrêt n'a pas pu être écrit · `7` l'agent est arrêté mais le port a **disparu**
(carte débranchée, ou reprise par WSL) · `8` il est **encore tenu**. Lire `7` comme un échec
ferait renoncer quelqu'un dont le geste a réussi ; le lire comme un succès ferait annoncer
« port rendu » sur un port qui n'existe plus. La page rend **le fait**.

🔴 **Ce que cette page ne referme PAS, et c'est écrit** : le **chemin de retour** — relancer
l'agent après que le flash a ré-énuméré le port — reste servi par la valeur par défaut
`COM3` de `tools/dn_agent_tour.ps1` et de `tools/dn-agent.bat`. **Porteur : `dn4-28`**, la
dépendance dure déjà déclarée de ce chantier.

### Ce que cette page ne fait pas encore

- ~~⛔ **Elle ne flashe pas la carte**~~, et ⛔ **elle n'installe pas l'agent** : elle sait
  l'arrêter et le retirer, ⛔ pas le mettre en place.
  > ⚠️ **ANNOTÉ LE 2026-09-08 — LA PREMIÈRE MOITIÉ A CESSÉ D'ÊTRE VRAIE, ET ELLE EST
  > BARRÉE PLUTÔT QU'EFFACÉE (`NFR3`).** La page **flashe** désormais la carte : voir les
  > trois sections ci-dessus. **La seconde moitié reste vraie** — elle n'installe toujours
  > **pas l'agent**, et le poser reste le geste décrit § *« Lancer / arrêter l'agent DEPUIS
  > WINDOWS »*.
- ~~⛔ **Elle ne propose aucun choix de langue** : la dalle démarre en anglais et le choix se
  fait au REPL série (`langue fr`), comme dit plus haut.~~
  > ⚠️ **ANNOTÉ LE 2026-09-09 (`dn7-2-2`) — LA PHRASE EST BARRÉE PLUTÔT QU'EFFACÉE (`NFR3`),
  > PARCE QU'ELLE MÉLANGEAIT DEUX LANGUES DIFFÉRENTES.** La page choisit désormais **sa
  > propre** langue — **FR/EN, anglais par défaut**, sélecteur en tête. ⇒ ce qui **reste
  > vrai** : elle ne choisit toujours **aucune langue pour la DALLE**, qui démarre en anglais
  > et se règle au REPL série (`langue fr`). ⛔ **Deux langues différentes, deux sujets
  > différents** : celle que le lecteur lit, et celle qui est posée dans la carte.
  > 🎯 **RE-ANNOTÉ LE 2026-09-09 — ⛔ RIEN N'EST EFFACÉ, ET LA MOITIÉ « ce qui reste vrai »
  > VIENT DE TOMBER.** La page **choisit désormais** la langue de la DALLE : deux positions,
  > **anglais par défaut**, au-dessus du bouton d'installation, et un geste explicite qui
  > l'écrit dans la carte par sa console série — en **relisant** l'état plutôt qu'en annonçant
  > un succès. ⇒ ce qui reste vrai est **plus petit** : la **dalle elle-même** ne porte aucun
  > sélecteur à l'écran, et le canal reste le REPL — c'est la page qui le tape. ⛔ **Deux
  > langues différentes** : cette distinction-là, elle, ne bouge pas.
- ⛔ **Elle ne montre aucun aperçu de la dalle** : c'est une **exclusion déclarée** de la
  première version, ⛔ ni un oubli ni un manque à réparer.
- ⚠️ **L'agent est Windows seulement**, et ça ne change pas. La page s'ouvre ailleurs — et
  **elle vous le dit AVANT de flasher**, parce que le flash, lui, **réussirait** : l'accès
  série du navigateur existe aussi sur macOS, Linux et ChromeOS. Vous repartiriez avec une
  carte correctement flashée et **rien à afficher dessus**. ⛔ Ce n'est pas un élargissement
  du périmètre : c'est la fin d'un silence.

### Le pré-vol, sans ouvrir de fenêtre

```bat
installeur\DeskNode-installeur.bat verifier
```

Il dit ce qui manque, donne le geste, et rend **6** si une dépendance de l'agent manque —
c'est l'instrument mécanique de l'écart ci-dessus, ⛔ pas un message décoratif. 🆕 Il rend
**5** si la **charge à flasher** est absente ou abîmée, et il ne se contente pas de compter
les fichiers : il **revérifie la bande-annonce d'intégrité** de l'asset (magie `DNASSET1`,
longueur, **CRC32**), celle-là même que le firmware relit au démarrage. Une image tronquée
est ainsi refusée **avant** d'être servie, ⛔ pas découverte sur une dalle blanche. L'identité
visuelle de la page, ses sept couleurs et **la ligne de firmware d'où chacune sort** sont
écrites dans [`installeur/IDENTITE.md`](installeur/IDENTITE.md).

## Arborescence

```
docs/       vision, roadmap, notes de câblage, photos, plans du boîtier, déclaration des liens affiliés
installeur/ DeskNode-installeur.bat — LE point d'entrée (double-clic), en CRLF
            dn_installeur.py — sert index.html sur 127.0.0.1, port TIRÉ au lancement
            index.html — la page : état du poste, « arrêter » et « retirer » l'agent
            IDENTITE.md — les 7 jetons de couleur, chacun citant sa ligne de firmware
firmware/
  hello-desknode/   P0 — TÉMOIN MINIMAL, figé. Log + rétroéclairage clignotant.
                    Quand le bring-up de l'écran part en vrille, c'est lui qui
                    prouve en 6 s que la chaîne build/flash/monitor n'est pas en
                    cause. Ne pas l'enrichir.
  desknode/         P1+ — le vrai firmware : écran RGB, mires, mesures, console.
    main/dn_widget.c/.h   dn3-1 — LE MODÈLE DE CASE du dashboard (icône, titre,
                          valeur(s), unité, couleur, indicateur, secondaires).
                          Son en-tête porte le CONTRAT DE VERROU et la raison
                          pour laquelle il est inversé. Il possède aussi la
                          BRIQUE TACTILE : les deux drapeaux qui rendent vraie
                          « toute la case est la zone tactile » n'ont plus
                          qu'UNE définition dans tout le firmware.
    main/dn_rtc.c/.h      dn3-2 — L'HEURE DU MODULE (PCF85063A @ 0x51). Driver
                          MAISON, et le motif est écrit dans son en-tête : le
                          composant `waveshare/pcf85063a` passe pourtant le
                          critère du bus, mais il MASQUE le bit OS (`& 0x7F`,
                          deux sites) — avec lui, la barre ne peut PAS savoir
                          qu'elle ment. `espp/pcf85063` est du C++ + 2 dépendances
                          de framework. L'en-tête porte aussi les LECTURES DE
                          REGISTRE qui ont qualifié la puce et RÉFUTÉ le variant TP.
    main/fonts/           dn3-1 — dn_font_14.c / dn_font_28.c / dn_font.h,
                          GÉNÉRÉS et VERSIONNÉS (voir § Les polices).
hardware/   ESP32-S3-Touch-LCD-2.8B-affichage.md  <- LA config d'affichage de
            référence (brochage VÉRIFIÉ, timings, framebuffer, chiffres datés).
            ESP32-S3-Touch-LCD-2.8B-liaison-pc.md <- §12, la FOURCHE TRANSPORT
            (dn2-2) : verdict USB série, protocole de trame, budgets liaison.
            ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md <- §13, LE BUS I²C EXTERNE
            (dn2-1) : brochage du connecteur MESURÉ (le wiki avait SDA/SCL
            inversés), les 4 occupants réels du bus, la commande `i2c` et son
            défaut de faux positifs, l'arbre de diagnostic du BME680.
assets/     assets graphiques 480×640
  mockups/living-pcb-v0.png   prévisualisation COMMITÉE de l'asset généré
agent/      dn_agent.py — l'agent PC (Windows), **5 métriques / 7 grandeurs** à 1 Hz (voir § L'agent PC)
tools/      wsl-attach.sh (attachement USB WSL)
            gen_living_pcb.py (génération de l'asset 480×640)
            gen_font_dn.py (génération des polices — voir § Les polices)
            dn_injecteur.py (dn4-6 — injection de trames `pc $DN,…` à cadence et
              **espacement** réglables. 🔴 `--espacement` n'est PAS un confort :
              c'est l'axe qui fait varier `px/cyc` de **32 %** sur le même
              binaire, donc **tout relevé de régime (b) doit le déclarer**)
            mesure_grandeurs_dn46.py (dn4-6 — échantillonnage ADL/psutil côté
              Windows, le harnais de T6/AC6 : étendue, taux de changement du
              TEXTE et σ, jugés sur la valeur **AFFICHÉE**)
tests/      harnais et smokes
```

> ⚠️ **Deux projets firmware, et c'est voulu** (décision D-F de dn1-2).
> `hello-desknode` a une configuration minimale et **figée** ; `desknode` a une
> configuration radicalement différente (PSRAM octale, 16 MB, partitions, ISR en
> IRAM). Les garder séparés préserve un A/B propre et un témoin qui compile
> toujours.

## Toolchain / build & flash

> Tout ce qui suit est **mesuré sur la tour `DESKTOP-08RT3CL` le 2026-08-14** (story dn1-1), pas
> recopié d'une doc. Les chiffres et les messages d'erreur sont ceux de cette machine.

### Versions figées

| Élément | Version | Où |
|---|---|---|
| ESP-IDF | **v5.5.5** (commit `b774170f`) | `~/esp/esp-idf` |
| Cible | `esp32s3` uniquement | `install.sh esp32s3` |
| esptool **côté IDF/WSL** | **4.12.0** — sous-commandes en `write_flash` (underscores) | embarqué par l'IDF |
| esptool **côté Windows** | **5.3.1** — sous-commandes en `write-flash` (tirets) | `pip install --user esptool` |
| usbipd-win | **5.3.0** | `C:\Program Files\usbipd-win\usbipd.exe` |
| Carte | ESP32-S3 rev **v0.2**, 8 MB PSRAM, MAC `a0:f2:62:e3:d7:f4` | USB natif `303a:1001` |

**Composants managés de `firmware/desknode`** — versions **épinglées à l'exact** dans
`main/idf_component.yml`, et ce que `dependencies.lock` a réellement résolu :

| Composant | Épinglé | Résolu | Rôle |
|---|---|---|---|
| `espressif/esp_lcd_st7701` | `==2.0.2` | 2.0.2 | driver ST7701(S) « 3-wire SPI + RGB » |
| `espressif/esp_lcd_panel_io_additions` | `==1.0.1` | 1.0.1 | bus 3-wire SPI bit-bangé, CS via IO expander |
| `espressif/esp_io_expander_tca9554` | `==2.0.3` | 2.0.3 | driver TCA9554 (le nôtre est à `0x20`) |
| `espressif/esp_io_expander` | *(transitif)* | 1.2.1 | socle commun des expanders |
| `espressif/cmake_utilities` | *(transitif)* | 0.5.3 | outillage CMake des composants Espressif |
| `lvgl/lvgl` | `==9.5.0` | 9.5.0 | la couche UI (dn1-3). ⚠️ API **v9** : `lv_display_create` / `lv_display_set_buffers`. Tout tuto qui parle de `lv_disp_drv_t` est du LVGL 8 et ne compile pas ici |
| `espressif/esp_lvgl_port` | `==2.9.0` | 2.9.0 | tick esp_timer, tâche LVGL, mutex, et `lvgl_port_add_disp_rgb()` qui prend les handles esp_lcd **déjà créés** par `dn_display` |
| `espressif/esp_lcd_touch_gt911` | `==1.2.1` | 1.2.1 | driver du Goodix GT911 (dn1-4). 🔴 avec `rst_gpio_num = -1` — notre cas, TP_RST étant derrière l'expander — il **saute sa séquence de sélection d'adresse** ; `dn_touch` la joue lui-même AVANT le `new` |
| `k0i05/esp_bme680` | `==1.2.7` | 1.2.7 | driver BME680 (dn2-1). 🔴 **Seul candidat du registre compatible avec CE bus** : `bme680_init()` prend un `i2c_master_bus_handle_t` **déjà créé**. Les trois autres (`esp-idf-lib/bme680` via `i2cdev` legacy, `francisduvivier/bme68x_…` et `espressif/bme690` via `espressif/i2c_bus`) **créent leur propre bus** — éliminatoire ici. ⛔ Il n'existe **aucun** `espressif/bme680`. ⚠️ Premier composant non-Espressif du manifeste ; son `CMakeLists` exotique est **inerte, vérifié par un build**. ⚠️ `bme680_get_data()` boucle jusqu'à **1 500 ms** ⇒ tâche dédiée obligatoire, jamais depuis le REPL |
| `k0i05/esp_type_utils` | `==1.2.7` | 1.2.7 | transitif de `esp_bme680`, sans dépendance propre au-delà de l'IDF. 🔴 **Épinglé EXPLICITEMENT depuis la revue du 2026-08-17** : cette colonne l'annonçait déjà `==1.2.7` alors que **rien ne l'épinglait** — `esp_bme680` le déclare en `>=0.0.1`, et `dependencies.lock` (gitignoré) le résolvait comme tel. Le manifeste étant la seule autorité versionnée, la doc affirmait le contraire du dépôt. Même précédent assumé que `esp_lcd_touch` |
| `espressif/esp_lcd_touch` | `==1.2.1` | 1.2.1 | socle tactile commun. Épinglé **explicitement** bien que transitif : le GT911 déclare `^1.2.0`, donc sans cette ligne le résolveur prendrait « la dernière ». ⚠️ c'est lui qui applique `swap_xy`/`mirror_x`/`mirror_y` **en logiciel**, avec `x_max`/`y_max` comme axe de symétrie |

> ⚠️ **Ce que le portage ne fait PAS, et qu'il faut savoir avant de le croire** (mesuré en dn1-3) :
> en rendu **partiel**, son flush n'attend **rien** — il n'attend `trans_sem` que dans la branche
> `direct_mode || full_refresh` (`esp_lvgl_port_disp.c:748-756`). Le `on_vsync` qu'il enregistre
> alimente donc un sémaphore que personne n'attend. Et cet enregistrement **écrase** celui de
> `dn_measure` (`esp_lcd_rgb_panel_register_event_callbacks` ASSIGNE, ne fusionne pas). D'où
> l'ordre d'appel et le témoin actif au boot — détail en §10.1 du fichier `hardware/`.
> Le binaire passe de **377 664 o à 740 400 o** avec LVGL, puis à **790 736 o** avec le tactile et
> la navigation de dn1-4 ; l'app fait 4 MiB, il reste **81 %**.

> **Pourquoi `dependencies.lock` et `managed_components/` restent gitignorés** — la question
> se reposait légitimement en dn1-2, puisqu'il y a désormais de vraies dépendances.
> Réponse : `idf_component.yml` épingle des versions **exactes** (`==`), pas des plages.
> Le lock ne fixerait donc rien de plus que ce que le manifeste fixe déjà, et il changerait
> à chaque résolution — du bruit dans les diffs sans garantie supplémentaire. C'est le
> **manifeste** qui fait foi ; le tableau ci-dessus enregistre ce qui a été résolu.
>
> ⛔ **Il n'existe AUCUN BSP `waveshare/esp32_s3_touch_lcd_2_8b`** sur le registre
> (vérifié par appel API : `ComponentNotFoundError`). Ne pas le chercher.

⚠️ **Les deux esptool ne sont pas de la même majeure.** Ne jamais copier une commande de l'un vers
l'autre : la 5.x a renommé toutes les sous-commandes.

### Installation — une seule fois

```bash
# 1. Prérequis Ubuntu (aucun n'était présent hormis git)
sudo apt-get update      # obligatoire : l'index périmé fait échouer libssl-dev en 404
sudo apt-get install -y git wget flex bison gperf python3 python3-pip python3-venv \
                        cmake ninja-build ccache libffi-dev libssl-dev dfu-util \
                        libusb-1.0-0 usbutils

# 2. ESP-IDF sur le tag exact (≈ 4,0 Go avec les sous-modules)
mkdir -p ~/esp && cd ~/esp
git clone -b v5.5.5 --recursive https://github.com/espressif/esp-idf.git
cd ~/esp/esp-idf && ./install.sh esp32s3     # esp32s3 seul : inutile de tirer les autres toolchains
```

Côté Windows, dans **PowerShell normal** (pas admin) — version **épinglée**, parce qu'une majeure
esptool renomme toutes les sous-commandes et invaliderait le bloc de flash de la voie A :

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m pip install --user esptool==5.3.1
usbipd list                       # ⛔ NE JAMAIS RECOPIER UN BUSID : il se RELÈVE sur la
                                  #    ligne 303a:1001, à CHAQUE fois (mesuré : 'list'
                                  #    n'exige AUCUNE élévation)
```

Côté Windows, dans **PowerShell ÉLEVÉE** — uniquement ces deux commandes-là, une seule fois :

```powershell
winget install --id dorssel.usbipd-win --exact --version 5.3.0

# ⛔ AUCUNE CONSTANTE ICI : le busid SUIT LE PORT PHYSIQUE, il se RÉSOUT.
# 🔴 ET IL SE VALIDE — corrigé par la revue du 2026-08-30. La version d'origine
#    était `$b = ((usbipd list | Select-String '303a:1001') -split '\s+')[0]`,
#    SANS AUCUNE GARDE, en shell ÉLEVÉE :
#      · 0 ligne (carte débranchée)  ⇒ `$b` vide ⇒ `bind` sur un busid vide ;
#      · 2 lignes — `303a:1001` est le VID:PID de TOUT ESP32-S3 ⇒ `-split`
#        aplatit le tableau et `[0]` prend le 1er jeton de la 1re ligne
#        ⇒ **bind de la MAUVAISE carte**, le défaut même qu'on prétend supprimer ;
#      · ligne indentée ⇒ `[0]` vaut `''`.
#    `tools/wsl-attach.sh:114-126` posait déjà ces trois gardes. Les voici.
$lignes = @(usbipd list | Select-String '303a:1001')
if ($lignes.Count -ne 1) {
    throw "attendu UNE ligne 303a:1001, trouvé $($lignes.Count) — débranche les autres cartes S3, ou relève le busid à la main."
}
$b = ($lignes[0].Line.Trim() -split '\s+')[0]
if ($b -notmatch '^\d+-\d+$') { throw "BUSID inattendu : '$b'" }
Write-Host "busid résolu : $b"
usbipd bind --busid $b            # une fois pour toutes ; l'état passe à "Shared"
```

> Le `bind` est **persistant** : il ne se rejoue pas après un reboot. Seul l'`attach` se rejoue.
>
> 🔴 **ET LE BUSID N'EST ÉCRIT EN DUR NULLE PART DANS CE FICHIER — c'est délibéré, et
> c'est mesuré.** **TROIS valeurs ont été vraies** : `3-7` (2026-08-20), `3-1`
> (2026-08-26), `3-5` (2026-08-27/28). ⛔ **`3-1` n'est pas seulement périmé : il est
> OCCUPÉ** — sur cette machine il porte un **`V31GT` (`0e8d:201c`)**. ⇒ **suivre une
> recette qui le récite ne rate pas : elle DÉTACHE LE MAUVAIS PÉRIPHÉRIQUE.**
> `tools/wsl-attach.sh` et `tools/rendre-port.sh` le **relisent** à chaque appel ; le
> skill `/desknode-board` aussi depuis le 2026-08-27. *(constante retirée par
> `dn4-15`, 2026-08-30 — ce fichier se contredisait lui-même à 1 000 lignes d'écart.)*

### La boucle de travail (voie C — retenue)

> 🔴 **LA RÈGLE QUI PRIME SUR LA RECETTE : ON COMMITTE AVANT DE FLASHER, ET `git status --porcelain`
> EST VÉRIFIÉ VIDE *AVANT* LE FLASH, PAS APRÈS.**
> Motif, mesuré : le bandeau de boot imprime `App version: <sha>`, et **c'est ce SHA qui fait foi**
> dans toute mesure publiée. Flasher depuis un arbre sale produit un firmware dont **aucun commit ne
> porte le contenu** — la mesure devient irreproductible, et **trois flashs de ce dépôt ont porté un
> SHA de bandeau différent du livrable**, ce qui a **rouvert un AC DEUX FOIS**.
> - ⛔ **Ne jamais déduire le SHA du dépôt** : il se **LIT au bandeau**, ligne `App version`.
> - ⚠️ Message de commit **toujours** par `git commit -F -` + heredoc **quoté** (`<<'EOF'`),
>   ⛔ jamais `-m "…"` : un message à backticks a déjà été **avalé par bash** pendant que `rtk`
>   imprimait « 4 files changed », donnant **toutes les apparences du succès**.
> - Le build de vérification se refait **APRÈS** les commits — un build sur arbre sale a une chaîne
>   de version sans valeur.
>
> *« Une règle qui ne vit que dans le compte rendu de la séance qui l'a apprise n'est pas une règle,
> c'est un souvenir. »* — ⚠️ Elle ne vivait que dans `hardware/…-affichage.md` §18.10, rattachée à
> l'AC14 d'une story ; elle entre ici en `dn4-2` (2026-08-19).

Dans **chaque shell WSL neuf** :

```bash
. $HOME/esp/esp-idf/export.sh                      # prépare l'environnement ESP-IDF
cd ~/projects/desknode && ./tools/wsl-attach.sh    # rend la carte visible ; il IMPRIME le port
cd firmware/desknode                               # ou firmware/hello-desknode (le témoin)
idf.py -p /dev/ttyACM0 flash monitor               # quitter le moniteur : Ctrl+]
```

**Ce qu'on doit constater — et ça DÉPEND du projet flashé.**

`firmware/desknode` (P1 et suite) :

- au **log**, et ce sont **deux lignes distinctes, imprimées par deux acteurs différents** :
  - `I (25) boot.esp32s3: SPI Flash Size : 16MB` — c'est le **bootloader**, *avant* `app_main` ;
    elle atteste que l'en-tête flashé annonce bien 16 MB ;
  - puis le bandeau `──── socle ────` de l'application, qui imprime `flash physique détectée : …`
    et `PSRAM : 8388608 o détectés, mode OCTAL, 80 MHz` — celui-là interroge la **puce**.
    ⚠️ Ne pas chercher `SPI Flash Size : 16MB` *dans* le bandeau `socle` : il n'y est pas, et les
    deux lignes ne prouvent pas la même chose (l'en-tête déclaré vs le silicium réel) ;
  - puis `up N s` toutes les 10 s ;
- à l'**œil** : le **dashboard** (barre heure/date, grille 2 × 3, bandeau `MENU`) s'affiche sur
  l'asset **Living PCB** voilé, et le **rétroéclairage est ALLUMÉ FIXE**. ⚠️ **Il ne clignote
  plus** — le clignotement était le signe de vie de P0 ;
- **au DOIGT** (dn1-4) : toucher une case ouvre sa page de détail, le `←` ramène au dashboard ;
- la **console est interactive** : taper `aide` dans le moniteur liste les commandes. Jeu complet :
  `scene`, `fps`, `bw`, `mem`, `cpu`, `cfg`, `set`, `tear`, `flash`, `ui`, `flush`, `anim`,
  `touch`, `nav`, `recal`, `bl`, `disp`, `dma`, `i2c` (`lire` · **`lire16`** · **`brut`** · **`ecrire`** · **`rafale`**), `capteurs`, **`env`**, **`tof`** (`etat` · `sr03` · `balayage` · `als` · `range`), **`w2`**, `pc`, `wifi`, `widget`, **`hist`**, `rtc`, **`veille`**, `reboot`, `aide`. `cfg reset` rend
  les défauts au prochain boot, et **`cfg repli [clear]`** lit (ou efface) le
  **témoin de repli de bounce** — ⛔ le seul geste **d'opérateur** qui l'efface
  (un `nvs_flash_erase()` au boot l'emporte aussi ; voir plus bas). **C'est `aide` qui fait foi**, pas cette liste. Les commandes de
  dn1-3 et dn1-4 :

  | Commande | Ce qu'elle sert |
  |---|---|
  | `ui [on\|off]` · `ui label on\|off` · `ui bg flash\|psram` | pilote LVGL. ⚠️ `ui off` est **obligatoire** avant `scene` ou `tear` : ces deux-là dessinent une trame entière à la main pendant que LVGL ne redessine que ses zones sales, et l'écran devient inattribuable |
  | `flush` · `flush reset` · `flush sync off\|vsync\|fbdone` · `flush path bitmap\|direct` · `flush full` | le rafraîchissement partiel **en chiffres** : aire, copie, attente de synchro. `sync off` est le **témoin** qui doit produire du déchirement — s'il n'en produit pas, aucune conclusion « pas de tearing » n'est recevable  🔴 **`flush` PUBLIE EN TÊTE UN TRIPLET DEPUIS `dn4-12` (2026-08-28), ⛔ plus le seul compte de corruptions** : ① **la PLUS LONGUE SÉRIE de trames CONSÉCUTIVES NON SAINES** — la seule grandeur qui distingue un glissement d'UNE trame d'un état qui **DURE** (le « permanent desync » du driver, que l'owner décrit comme *« parfois ça reste dans un état glissé »* et que **rien ne mesurait**), avec sa **composition** (classe A déficit franchi · C hors borne de sanité · D sans enroulement), sa trame de début, le nombre de séries, **la série EN COURS**, et le nombre de séries **rompues par une trame INDÉTERMINÉE** — ⚠️ c'est un **MINORANT**, et ce nombre **ne se soustrait pas** ; ② la **DISTRIBUTION** des quatre seaux `10/25/50/100 %`, 🎯 **le signal jugé fiable par `dn4-22`** (⛔ seaux **EMBOÎTÉS**, ne pas les sommer) ; ③ le **DÉPASSEMENT** du seuil **avec sa RÉFUTATION IMPRIMÉE À CÔTÉ** — c'est un **MAX**, qu'**un seul point aberrant déplace** (`dn4-22`/ARM 5 : **1 300 µs pour UNE corruption** contre **896 µs pour 245**), donc un **ordre de grandeur**, ⛔ **pas un discriminateur entre deux fenêtres**. **Le COMPTE descend en second, avec sa réserve** : à `RESTART_IN_VSYNC=n` il mesure la **FAMINE**, pas le **GLISSEMENT** — **143 corruptions AVANT COMME APRÈS** le correctif du 2026-08-23, pendant que l'œil passait de « ça glisse » à « plus de glissement ». ⚠️ **L'unité de ① est la TRAME, ⛔ pas la microseconde** : `esp_timer` reboucle en **71,58 min**, un compte de trames à 37,40 Hz en **~3,6 ans** — la conversion en ms se fait **côté console**, depuis `periode_ns` (26 737 500 ns, exacte). ⛔ **À `bounce_px < 480` ① et ② sont DÉSARMÉS et la ligne est REFUSÉE** (⛔ pas imprimée à zéro : *« un zéro se lirait « aucune corruption » »*) — et le refus **dit laquelle des trois classes est perdue** : seule **A** disparaît, **C** et **D** restent comptables. `flush reset` remet ① à zéro **par drapeau consommé par l'ISR**, donc le témoin est **rejouable** |
  | `anim on [ms]` · `anim off` | stimulus adverse LVGL : barre verticale balayant l'écran |
  | `recal <0..4>` | recalage DMA N vsyncs après une bascule (le double tampon, §4 ter) |
  | `bl <0..100>` · `bl ramp <pct> [ms]` · `bl freq <hz>` · **`bl auto on\|off`** · **`bl auto bornes <bas> <haut>`** · **`bl auto pas <n>`** · **`bl auto plancher <n>`** · 🆕 **`bl auto ambiant <0..100>`** · 🆕 **`bl auto ambiant plancher <n>`** · 🆕 **`bl auto courbe log\|lineaire`** · 🆕 **`bl loi [lux]`** | rétroéclairage **gradable** et, depuis **dn4-3**, **asservi au BH1750**. ⚠️ `bl 0` = dalle NOIRE ; `disp off` = dalle GRISE éclairée. 🔴 **La loi est ÉCRITE AVANT la mesure, et DEUX de ses quatre bornes ont ensuite été DÉPLACÉES PAR L'ŒIL DE L'OWNER — c'est le propos d'AC5** : ~~**8 %** à ≤ **20 lx** · **100 %** à ≥ **600 lx**~~ ⇒ 🔴 **`dn4-20`, 2026-08-27 : LES QUATRE BORNES SONT RÉÉCRITES PAR L'ŒIL — ⛔ barré, pas effacé** ⇒ **20 %** à ≤ **2 lx** · **80 %** à ≥ **11 lx**. **Aucun des quatre candidats de forme n'a été retenu, et c'est la MESURE qui a démoli la question** : séance à l'œil sur le binaire `be0431f`, régime ACTIF, owner aux commandes ⇒ à **0 lx** *« pas assez lumineux »* (8 %) et *« trop sombre »* (12 %), **16 et 20 passent**, mais **72 % est *« un peu fort quand même »*** ; à **11 lx** *« trop sombre »* (20 %) et **72 % *« bon »*** ; à **34 lx** *« trop bas »* (40), *« un peu encor trop bas »* (60), **72 *« bon »***, 85 *« pareil »* ; et **~80 %, PLAT de 105 à 391 lx** (27/08). ⇒ 🎯 **L'ŒIL NE DEMANDE PAS UNE LOI, IL DEMANDE UNE MARCHE**, et elle se joue **ENTRE 0 ET 11 lx** — ⛔ pas entre 20 et 600. **`LUX_BAS = 20` était AU-DESSUS de la marche** (à 11 lx la loi rendait encore son plancher, 8 %, quand l'œil veut 72) et **`LUX_HAUT = 600` étalait sur 30× de lumière une montée que l'œil termine en 11 lx**. ⇒ la question *« log, linéaire, plateau ou puissance ? »* **s'effondre** : entre des bornes aussi rapprochées, la FORME ne se voit plus. ⚠️ **CE QUE `2` ET `11` SONT, HONNÊTEMENT : l'ENCADREMENT LE PLUS LARGE QUE LA MESURE DÉFEND, ⛔ pas le bord de la marche** — **aucun point n'a été pris entre 0 et 11 lx** (décision owner de clore la séance), donc les **44 % que la loi rend à 4 lx n'ont JAMAIS été jugés**. ⚠️ **ET LE PRIX EST MESURÉ** : ~60 points sur 9 lx dans une pièce qui bouge de **±2 à 4 lx toute seule** (`mesures/dn4-20/T-04`) ⇒ **la bande morte de 3 points ne peut rien contre ça**, et l'hystérésis à deux seuils *« refusée tant qu'on ne l'a pas vue »* **vient d'être vue**. ⚠️ Le plafond de la loi passant à 80, **le boot descend désormais de 100 à 80 %** — annoncé par la ligne de boot. ⛔ `bl 100` reste atteignable : le plafond borne **la loi**, pas la dalle. 🆕 **`bl auto plafond <n>`** (dn4-20/AC4.6) le rend réglable À CHAUD, comme le plancher — sans lui le candidat « plateau » aurait coûté **un reflash par valeur essayée**, exactement le défaut que `dn4-3` avait déjà payé sur le plancher. Captures : `mesures/dn4-20/`, ~~interpolation linéaire~~ ⇒ **courbe LOGARITHMIQUE** entre les deux (⛔ barré, pas effacé — `dn4-19`/AC6.3, 2026-08-27). 🔴 **C'est une RÉFUTATION de la loi linéaire, ⛔ pas un réglage** : A/B en **Actif**, 4 niveaux (41 / 55 / 75 / 100 %), **n = 5** par point, **lux relevé à chaque point** ⇒ constat owner **« 75 % — nettement plus »** là où la loi linéaire rendait **44 %** à 245 lx. 🔴 **ET LE TROU EST ÉCRIT ICI AUSSI, ⛔ pas seulement dans la story** (ajouté en revue de code le 2026-08-27) : cet A/B n'a eu **QU'UNE SEULE condition d'éclairage (245 lx)** là où AC6.2 en exige **≥ 2**, et le 2ᵉ point de la courbe est **EMPRUNTÉ À AMBIENT** (le plancher 16 % mesuré dans le noir), **sur décision owner**. ⛔ **La loi log n'a donc JAMAIS été jugée à l'œil en AMBIENT** — l'échelle `100 %` d'Ambient, elle, a été tranchée **sous la loi LINÉAIRE**. ⇒ ⛔ ne pas lire cette ligne comme un A/B complet. ⛔ **Le gamma a été écarté PAR LE CALCUL, pas par goût** : il aurait fallu le *caler* sur ce point (γ ≈ 3,0) et il produisait alors un **coude brutal** juste au-dessus de `LUX_BAS` (8 % à 20 lx, puis **27 % à 25 lx**) que personne n'a validé. ✅ **La loi log n'a AUCUN paramètre à caler** et retombe sur le constat : `8 + 92 × ln(245/20)/ln(600/20)` = **76 %**. Son motif était déjà au ledger : *« l'œil et le lux sont tous deux logarithmiques »*. ⛔ **Les deux bornes sont préservées à l'identique** — c'est la FORME entre elles qui change, ⛔ aucune des quatre valeurs réglées à l'œil n'est déplacée. ✅ **Et elle reste RÉFUTABLE** : `bl auto courbe lineaire|log` rebascule **à chaud**, et `bl loi` imprime **les deux formes côte à côte** ⛔ SANS jamais toucher à la courbe active — corrigé en revue de code le 2026-08-27 : il la **basculait puis la remettait**, ce qui laissait `dn_env_cycle()` (autre tâche, autre cœur) appliquer la mauvaise loi pendant la fenêtre. La courbe est désormais un **paramètre**, ⛔ plus un état muté. 🔴 **CORRIGÉ PAR AJOUT EN REVUE DE CODE LE 2026-08-20 : cette ligne annonçait « 1 500 lx » alors que le firmware grave `DN_ENV_BL_LUX_HAUT 600` depuis le commit `222c4f4`** — le plafond a bougé une TROISIÈME fois (400 → 1 500 → **600**), le code a suivi, la doc non. ⛔ Une étiquette qui ment se relit à chaque boot, et c'est exactement le défaut que cette story passe son temps à traquer. ⚠️ **Le plancher valait 3 %**, repris d'AC7 de `dn1-3` — mais ce 3 % avait été mesuré sur le **Living PCB et son label** (une image de fond contrastée), pas sur un **dashboard de texte fin**. Rejoué sur la scène livrée, constat owner : *« casiement plus lisible super sombre »*. La dichotomie **10 / 6 / 8**, conduite **rideau fermé** (capteur à **2 lx**, la condition où le plancher s'applique) : 10 % *« un peu trop lumineux »*, 6 % *« lisible, un poil trop sombre »*, **8 % *« c'est bien »***. ⛔ **Le 3 % de `dn1-3` n'est pas invalidé** : un plancher de lisibilité est une propriété du **couple duty × contenu**, pas du duty seul. ⚠️ **Le plafond valait 400 lx**, sur UNE mesure (411 lx). La séance a relevé **2 lx rideau fermé → 2 262 lx en journée** dans la même pièce : à 400 lx, la loi saturait à 100 % dès un éclairage artificiel modeste. ⇒ porté à **1 500 lx**. 🔴 **Puis REDESCENDU à 600 lx, encore par l'œil** : à 1 500 de plafond, une pièce éclairée à 170 lx ne recevait que **17 %** (*« un peu plus lumineux »*) ; à **600**, la même pièce reçoit **32 %** et le constat est **« c'est ça »**. ⚠️ Une réponse intermédiaire de l'owner était **AMBIGUË** (*« ok pas mal pour être un peu plus »*) — plus RAPIDE ou plus LUMINEUX se corrigent à deux endroits opposés de la loi : ⛔ elle n'a PAS été tranchée au jugé, la question a été reposée en distinguant les deux. **Bande morte 3 points** (= 31 crans LEDC sur 1 023 : en dessous, l'œil ne peut pas voir la correction), **~~pas maximal 20 points~~ ⇒ 50 points par cycle de 5 s** ⇒ course complète en **2 cycles ≈ 10 s** (⛔ barré, pas effacé — `dn4-19`, **constat owner du 2026-08-27** : *« trop lent »*, puis, main posée devant le capteur puis retirée, **« on voit bien les 2 se déclencher c'est good »**. ⚠️ La question *« plus RAPIDE ? »* a été posée **séparément** de *« plus LUMINEUX ? »* — elles se corrigent à deux endroits opposés de la loi. ⛔ **La cadence de 5 s n'a PAS bougé** : elle cadence les **cinq** pistes capteurs, pas seulement le rétroéclairage). 🔴 **`bl auto pas <n>` REFUSE un pas plus petit que la bande morte** (posé en revue de code le 2026-08-20) : un pas inférieur à 3 laisse la loi ENTRER (écart ≥ 3) puis ne bouger que de `pas`, ce qui laisse un écart < 3 ⇒ **gelée à mi-chemin, dans les DEUX sens, pour TOUS les lux**, pendant que `bl auto` annonce une « course complète » qui ne peut pas s'achever. ⛔ **`dn_display_backlight_ramp()` n'est JAMAIS appelée par l'asservissement** : elle est BLOQUANTE (`vTaskDelay`) et son docblock la déclare « geste d'OPÉRATEUR, pas un effet de fond ». 🔴 **`bl <n>`, `bl on|off` et `bl ramp` DÉSARMENT l'auto ET LE DISENT** — `dn_display_backlight_pct()` n'a **aucun verrou** et `s_backlight_pct` est un `int` nu ; sans ce désarmement, un `bl 50` tapé en séance serait **écrasé au cycle suivant SANS UN MOT**, et le constat owner mesurerait **la boucle en croyant mesurer la commande**. ⚠️ **Capteur muet ⇒ le duty NE BOUGE PAS** (journalisé une fois) : un capteur silencieux ne doit ni éteindre l'écran ni le mettre à fond. 🔴 **~~DÉSARMÉ PAR DÉFAUT~~ ⇒ ARMÉ PAR DÉFAUT depuis `dn4-19` (2026-08-27)** — ⛔ barré, pas effacé. Le motif d'origine (*« le repli pré-autorisé d'AC5 qui devient l'état de départ, l'A/B dans UN SEUL firmware »*) **était l'A/B de `dn4-3`, et l'A/B est fini** ; il avait une conséquence que personne n'avait mesurée : **l'asservissement n'a JAMAIS TOURNÉ**. Carte à `up 3820 s`, 68 % du temps en Ambient, `bl` rendait `applique : AUCUNE application depuis le boot`, et le duty restait cloué à 10 % pendant que le BH1750 lisait 357 lx. ✅ Le passage à `true` **ne coûte rien** : 0 écriture NVS en régime, 0 clé de plus, `dn_env.c` reste hors de la table D4 — et `bl auto off` ne survivant pas au reboot, un module laissé bancal par un geste **se répare en le redémarrant**. ⚠️ **CONSÉQUENCE VISIBLE ET VOULUE** : le boot pose 100 %, et la loi **le fait redescendre** vers sa valeur en quelques cycles de 5 s. Si le BH1750 est encore muet (le bus se dégrade ~40 s à froid), le duty **ne bouge pas** et la dalle reste à 100 % jusqu'à la première lecture valide — **c'est correct, ⛔ ce n'est pas une panne**. 🔴 **ET LA VEILLE NE DÉSARME PLUS** (`dn4-19`) : elle **pose le niveau du régime EN UNE FOIS**, et la loi le maintient ensuite. La règle de priorité des écrivains de LEDC est écrite **en une phrase** dans `dn_env.h` : *le dernier GESTE D'OPÉRATEUR l'emporte sur tout ; sinon la BASCULE pose le niveau du nouveau régime EN UNE FOIS, et l'ASSERVISSEMENT le maintient ensuite.* 🆕 **`bl loi [lux]`** imprime ce que la loi rendrait, ⛔ **sans l'appliquer** — la fonction était exposée exprès pour ça depuis `dn4-3` et **n'avait aucun appelant**, si bien que la prédiction « 61 % » de la séance du 2026-08-27 a été calculée **à la main**. 🆕 **`bl auto ambiant <0..100>`** (l'échelle de la loi en Ambient) et **`bl auto ambiant plancher <n>`** (🎯 **MESURÉ le 2026-08-27, et c'est bien un TROISIÈME chiffre** : balayage 3 / 6 / 8 / 12 / 16 % conduit **dans le noir** (BH1750 à **0 lx**), **sur le rendu d'Ambient** ⇒ constat owner **« 8 % c'est trop bas, 16 c'est bien »**. 🔴 **Il est PLUS HAUT que les deux autres**, ⛔ à rebours de l'intuition « gros chiffres blancs sur noir, donc ça se lit plus bas » : **3 %** = Living PCB (`dn1-3`/AC7) · **8 %** = dashboard à texte fin · **16 %** = rendu d'Ambient. ⛔ **Aucun des deux autres n'est invalidé** : ils ne portent pas sur ce contenu-là). Bornes, pas **et plancher** (`bl auto plancher <n>`) **réglables à chaud**, parce que l'arbitrage se tranche **sur la dalle**, pas au papier. 🔴 **Le plancher n'était PAS réglable à la première livraison, et c'est la séance qui l'a prouvé nécessaire** : les bornes en **lux** l'étaient, le plancher en **%** était figé à la compilation — or c'est précisément lui que l'œil a déplacé |
  | `set lines <8..160>` · `set drawmem <0\|1>` · `set core <-1\|0\|1>` · `set bounce <px>` | variables de mesure du rendu, relues au boot (`reboot` pour appliquer) |
  | **`touch`** (dn1-4) | état du GT911 : adresse **mesurée**, config lue, mode de lecture, compteurs (IRQ, lectures, appuis, erreurs I²C) et **latence tap → écran** |
  | **`touch mode event\|poll`** | mode de lecture de l'indev, **à chaud** — l'A/B d'AC2 sans reflasher |
  | **`touch trace [ms]`** | imprime chaque **APPUI** (avec ses coordonnées brutes) et chaque **TAP** avec sa zone. L'instrument des campagnes au doigt |
  | **`touch int [ms]`** | témoin **physique** de TP_INT : échantillonne la broche sans passer par le driver ni l'ISR |
  | **`touch addr`** | **preuve causale** de TP_INT : deux resets, INT haut puis bas, et l'adresse latchée suit (0x14 / 0x5D) |
  | **`touch axes <swap> <mx> <my>`** | orientation à chaud. ⚠️ les miroirs se replient sur `x_max`/`y_max` : les quatre champs se règlent ensemble. ⛔ **`swap=1` est REFUSÉ** : `x_max`/`y_max` sont figés à 480/640 et un échange d'axes rendrait injoignables les **160 dernières lignes**, bandeau MENU compris (AC2 a mesuré qu'aucune transformation n'est nécessaire) |
  | **`touch delais <bas> <haut>`** | délais de la séquence de reset (1..2000 ms chacun), sans reflasher — puis `touch addr` pour les **appliquer** en rejouant. ⚠️ ce n'est PAS `touch reset`, qui remet les compteurs à zéro : trois commentaires du firmware annonçaient la mauvaise commande |
  | **`nav`** · `nav open <0..5>` · `nav back` · **`nav menu`** | navigation dashboard ↔ détail ↔ **MENU** depuis la console. **Refusée si LVGL est en pause** : elle armerait le chronomètre de latence sur un cycle qui n'aura pas lieu |
  | **`nav model rebuild\|screens`** | le **modèle** de navigation, les deux restent jouables. ✅ **`screens` retenu**, re-mesuré le 2026-08-16 dans la config livrée après correction de la fuite : **307,0 ms** de moyenne contre **346,9 ms** pour `rebuild`, soit 39,9 ms (11,5 %) pour +3 032 o de tas LVGL. *(Les anciens 267,9 / 307,7 avaient été relevés à `bounce_px = 0` sur un A/B qui fuyait ; ils surestimaient le prix de `screens` de 2,7×.)* |
  | **`nav ab <n>`** | N allers-retours scriptés : latences min/moy/max **et** preuve de non-fuite (RAM interne et PSRAM avant/après) |
  | **`veille`** | l'état complet de la VEILLE : mode (`ACTIF`/`AMBIENT`), armement, délai, inactivité courante **et maximale**, bascules, réveils, origine du dernier réveil, rebases d'horloge, bascules annulées, taps consommés, coût de la dernière écriture NVS. 🔴 Publie aussi le **soupçon d'appui fantôme** : veille armée + assez de secondes OBSERVÉES + aucune bascule + inactivité max restée sous le délai ⇒ le GT911 est probablement collé, et **le scan I²C ne le voit pas** (l'instrument est `touch`/`err_i2c`) |
  | **`veille on\|off`** · **`veille delai <1\|3\|5\|10>`** | les **deux** réglages, appliqués **à chaud** et **persistés en NVS** (namespace `desknode`, clés `veille_on` / `veille_dly` — ⛔ **pas** `dn_bootcfg`, qui est BOOT-ONLY par contrat). Défauts d'usine : **`ON` / `3 min`** (décision owner du 2026-08-25). ⛔ `veille delai 7` est **refusé et expliqué**, jamais arrondi vers 5 |
  | **`veille now`** · **`veille wake`** | bascule / réveil immédiats. `now` **respecte l'armement** : ⛔ on ne contourne pas le réglage de l'utilisateur |
  | **`veille lat`** | les **DEUX** latences de réveil, ⛔ jamais leur moyenne : **t₁** = contact → rétroéclairage remonté, **t₂** = contact → palette Actif posée. ⚠️ **Seuls les réveils AU DOIGT** entrent dans la statistique ; un `veille wake` au clavier est enregistré mais **exclu**, ⛔ pas jeté en silence. ⚠️ t₁ part de l'instant où le `read_cb` **voit** le front — le trajet GT911 → IRQ → tâche LVGL est **en amont et non instrumenté**, et c'est dit |
  | **`veille geom`** | la preuve **chiffrée** qu'Ambient ne déplace **rien** : les 4 nombres des 6 cases + le triplet de bandes, plus une **signature FNV-1a** des 28 nombres. ⛔ Pas un constat à l'œil. La preuve se fait en **deux** relevés (avant/après `veille now`) : les signatures doivent être identiques |
  | **`veille assets`** | le recompte de la partition : `assets` = 1 048 576 o, asset = 614 416 o, libre = 434 160 o, **deux** déclinaisons = 1 228 832 o ⇒ ❌. ⇒ Ambient est obtenu **sans un octet d'asset neuf**, et `partitions.csv` est **inchangé** |
  | **`veille reset`** | compteurs **et** latences à zéro. ⛔ Ne touche ni les deux réglages ni le mode |
  | **`veille pct <3..100>`** · **`veille voile <0..255>`** · **`veille gris <reel\|simule\|absent> <rrggbb>`** · **`veille accents <0..100>`** | les leviers de l'A/B **à chaud**, ⛔ **non persistés** (ce sont des instruments : la valeur retenue se **grave** dans le source avec son constat). 🔴 **`veille pct` A CHANGÉ DE NATURE EN `dn4-19` — ⛔ CE N'EST PLUS « LE NIVEAU D'AMBIENT »** : depuis que la loi vit en Ambient, le niveau d'Ambient **suit le lux** (`bl auto ambiant …` est son levier). Ce pourcentage est désormais le niveau de **DERNIER RECOURS**, celui que la bascule pose **quand la loi ne peut pas parler** (BH1750 muet ou jamais lu, ou `bl auto` désarmé par un geste) — **et il est journalisé quand il sert**, parce qu'un repli silencieux serait exactement le défaut que `dn4-19` ferme. ⚠️ **Sa borne haute est passée de ~~40~~ à 100**, et c'est le même motif : le 40 disait *« Ambient est un état sombre »*, or ce chiffre s'applique maintenant **à n'importe quel éclairage** — un plafond à 40 y serait faux **pour la raison exacte** qui rendait le 10 % faux en pleine lumière. ⛔ **Le constat du 2026-08-25 (*« la luminosité de la veille est bien »*) n'est PAS invalidé** : il a été fait **rideau fermé**, où ~~10 % coïncide à deux points près avec le plancher de la loi (8 %)~~ 🔴 **PÉRIMÉ PAR `dn4-20` le 2026-08-27, ⛔ barré et pas effacé : le plancher de la loi vaut désormais `20 %`** (le `8 %` a été refusé par l'œil sur le contenu même où il avait été mesuré). ⇒ **le 10 % de `veille pct` n'est plus « à deux points près » de quoi que ce soit** — il est maintenant **10 points SOUS** le plancher de la loi, et ⛔ **il n'a pas été re-jugé à l'œil** : c'est un niveau de DERNIER RECOURS (capteur muet), donc il ne se voit qu'en panne. Entrée de ledger, ⛔ pas une correction au jugé. Ce qui manquait, c'est **sa condition d'éclairage**. ⛔ Aucun ne reconstruit la scène. 🔴 `veille accents` **dit quelles paires d'accents il confond**, calculé à l'exécution : à **100 %** (gris pur) le cyan de `GPU` et le rose de `RAM` rendent **tous deux 160/255** — d'où le défaut à **95 %**, où les sept accents restent distincts pour 7/255 de teinte résiduelle |
  | **`capteurs`** (dn2-1) | le **BME680** : état (VIVANT / MUET / jamais lu), valeurs + âge, cadence, cycle de mesure mesuré, compteurs **par cause** (i2c / donnée / bornes / **reconfigurations**). `capteurs gaz on|off` = l'A/B d'auto-échauffement à chaud. 🔴 **`capteurs simuler muet\|bornes\|config <n>`** rejoue une panne SANS toucher au connecteur (un Dupont ne supporte pas les insertions répétées) — l'injecteur ne falsifie que le VERDICT, jamais la lecture, et s'annonce bruyamment. ⚠️ **Elle ne déclenche AUCUNE mesure** : `bme680_get_data()` peut dormir 1 500 ms, et le REPL est le transport PC. 🔴 **`dn4-3` y ajoute la PRESSION**, mesurée par la puce depuis `dn2-1` et **JETÉE** jusqu'ici. Elle est **publiée, pas affichée** : c'est le troisième candidat à la 6ᵉ case (X2), et — à la différence du lux — elle vient du **même capteur** que T et RH, donc elle **n'a pas** le conflit de verdict unique. Bornes **300..1100 hPa** (Bosch). ⛔ **Hors plage, SEULE la pression devient absente** : T et RH restent publiées — une grandeur qu'on ne fait qu'instruire ne doit pas pouvoir éteindre la seule case vivante de la grille. 🔴 **ET DEPUIS `222c4f4`, LA RÉSISTANCE DE GAZ (MOX) — documentée ici en revue de code le 2026-08-20, elle ne l'était nulle part** : `capteurs` imprime la **résistance BRUTE** du capteur MOX quand `capteurs gaz on` est actif. ⛔ **CE N'EST PAS UN INDICE DE QUALITÉ D'AIR** : elle BAISSE en présence de COV, et elle dépend AUSSI de la température, de l'humidité et de l'historique du capteur. ⚠️ **TROIS ÉTATS, TROIS PHRASES** (posés en revue de code) : *chauffeur coupé* · *chauffeur demandé mais aucune lecture valide* · *le chauffeur tourne mais `gas_valid`/`heater_stable` sont à faux* — au premier cycle la plaque n'est pas à 300 °C, la compensation rend **~12,9 MΩ**, et publier cet artefact fixerait le min/max de toute la fenêtre `w2`. ⛔ **L'`iaq_score` du composant est INUTILISABLE et la console le dit en huit lignes** : le header annonce 0..500 quand la formule plafonne à **65** ; la bande **9 000..13 500 Ω** ne reçoit **aucun score** (`bme680.c:733` teste `gas>=13500 && gas>9000`, le second est impliqué par le premier) ; et l'auto-échauffement de **+2,1 °C** lui coûte 6,5 points **par artefact de montage**. ⇒ un vrai IAQ demande **BSEC**, binaire propriétaire |
  | **`env`** (dn4-3) | les **TROIS capteurs d'environnement LOCAUX** : **BH1750** `0x23`, **INA219** `0x40`, **VL6180X** `0x29`. Pour chacun : état (**JAMAIS** / **VIVANT** / **MUET**), valeurs, **âge**, et les **seaux d'erreur discriminés** — `i2c` (transport) · `donnee` (il répond, la donnée n'est pas exploitable) · `bornes` (hors plage physique) · `reprises` · **`conformite`** (la garde anti-fantôme). `env reset` remet les compteurs à zéro. 🔴 **AUCUNE TÂCHE PROPRE** : ils sont cadencés par la tâche `dn_capt` (5 s), et l'appel est placé **AVANT toute branche** de sa boucle — sinon il serait **sauté à chaque erreur du BME680**, c'est-à-dire précisément pendant la dégradation du bus à froid, le seul moment où la tolérance qu'on prétend livrer se mesure. 🔴 **`env` dit « JAMAIS CADENCÉ »** si aucun cycle n'est arrivé (`xTaskCreate` a échoué) : ⛔ un module optionnel n'acquitte pas dans le vide. 🔴 **Drivers MAISON pour les trois**, arbitré sur des critères **écrits et horodatés AVANT** d'ouvrir un source (`hardware/…-capteurs-i2c.md` §13.19.2/.3/.4) : le mieux adopté du registre (`espressif/bh1750` 2.0.0, 7 147 téléch.) bloque **1 000 ms par transaction**, et **il n'existe AUCUN composant VL6180X** (404 vérifié). ⇒ **le compte de 103 `ESP_ERROR_CHECK` dans `managed_components/` reste à 103**, et l'obligation de ré-audit — manuelle, sans mécanisme, sur un répertoire **gitignoré** — ne s'étend pas. ⚠️ **Les gardes anti-fantôme sont des LECTURES, ⛔ pas des écritures** : la configuration est écrite **une fois** à l'ouverture et **relue à chaque cycle**. Même pouvoir discriminant (un fantôme ne tient pas la valeur), sans ajouter d'**agresseur permanent** sur un bus que le GT911 pole ~30×/s. INA219 : `05h` Calibration (reset `0000` → imposé `0x1000`, qui est **aussi la vraie calibration** du shunt R100). VL6180X : `003F` (reset `06` → `46`) et `0041` (reset `00` → `63`). 🔴 **BH1750 : AUCUNE garde, et c'est DÉCLARÉ à la console** — il n'a **aucun registre relisible** (le `MTreg` est écrivable mais **NON RELISIBLE**, piste tentée et **non reproduite**). Son stimulus (main posée) reste sa qualification la plus forte, mais **il demande un geste owner** : ⛔ ce n'est pas une garde de régime. 🔴 **Le VL6180X ne publie AUCUNE grandeur — ET LA RAISON A CHANGÉ LE 2026-08-21.** ⛔ Ce README a affirmé jusque-là que la cause était *« ST impose un chargement de registres privés »* (SR03) : **c'était FAUX**, et c'est corrigé ici plutôt qu'effacé. **SR03 se charge** (38/38 écritures, les **30 registres privés relus EXACTEMENT**) et **le balayage d'intégration est IDENTIQUE avant et après**. 🔴 **La vraie cause : l'étage ANALOGIQUE de ce composant est MORT.** L'ALS ne réagit ni à **2 280×** de lumière (5 lx → 11 418 lx, **BH1750 en CONTRÔLE au même instant**), ni à **40×** de gain, ni à un cycle d'alimentation complet — sa sortie ne dépend **que de la durée d'intégration**. Télémétrie **0/200**, zéro photon **jusque sur le canal de RÉFÉRENCE INTERNE**. ⚠️ Et le module **empêche aussi la carte de démarrer** par intermittence ⇒ **il est RETIRÉ du montage**. Dossier : §13.20-§13.21 et `investigations/dn4-7-vl6180x-ne-converge-jamais-investigation.md`. 🔴 **L'INA219 ne mesure PAS le rail du module** : `Vin+`/`Vin-` **ne sont pas câblés**. Le shunt libre rend **`FF FB` = −50 µV de bruit** — ⛔ **PAS `00 00`**, comme l'annonçait ce README jusqu'au 2026-08-20 : *le contrôle proposé aurait rendu « anormal » l'état normal*. La tension de bus lue (**900 mV**) est celle d'une entrée **flottante**, stable et **parfaitement plausible**, qui n'est l'alimentation de rien. ⇒ le poser **en série** était une **question OWNER** (X3, AC7). 🔴 **ET ELLE EST TRANCHÉE — CORRECT-COURSE DU 2026-08-20 : L'INA219 SORT DU RÉGIME.** ⛔ **Il n'est plus lu**, et `env` l'affiche désormais **`⛔ INERTE — plus lu en regime`**, compteurs à zéro à vie. **Motif** : il ne mesurait que du bruit, **pour 5 transactions I²C sur les 9 du cycle — 56 % du trafic de `dn_env`** — sur le bus que §11.4 nomme *« le PREMIER AGRESSEUR CONNU »* de la famine DMA. ✅ **Gain mesuré à la carte** : le cycle de `dn_env` passe de **~2 400 µs à ~1 140 µs**. ⛔ **Il n'est PAS dessoudé** (**D9** : montage fini, le dessoudage est un risque sur le bus pour **zéro gain**) — il reste soudé, ouvert et configuré au boot. ✅ **POUR LE REMETTRE EN SERVICE** : il faut du **courant dans son shunt**, et le **bornier à vis 2 points est DÉJÀ SOUDÉ** ⇒ `Vin+`/`Vin−` sont accessibles **SANS FER** (couper la ligne 5 V d'un câble USB-C, visser les deux bouts — réversible). ⚠️ **VÉRIFIER D'ABORD AU MULTIMÈTRE** que le bornier est bien relié à `Vin+`/`Vin−` : c'est le câblage standard CJMCU, mais **ce dépôt ne l'a jamais mesuré**. ⛔ **Et `Vin+`/`Vin−` NE SONT PAS une alimentation** : y poser 5 V et la masse **court-circuiterait le shunt de 0,1 Ω** |
  | **`tof`** (dn4-7) | le **VL6180X** `0x29` instruit **pour de bon** — `etat` (registres, **lecture seule**), `sr03`, `balayage`, `als <ms>`, `range [n]`. 🔴 **`sr03` joue la séquence d'initialisation que ST rend OBLIGATOIRE** — *AN4545 « VL6180X basic ranging application note », DocID026571 **Rev 1, juin 2014**, §9* : **30 registres PRIVÉS** + 7 publics. Sans elle, ST écrit que la puce *« may not perform to specification »*, et c'est la cause nommée de la réfutation de l'ALS (§13.19.5). ⚠️ **`st.com` est INJOIGNABLE depuis ce poste** — et la cause est maintenant NOMMÉE : le TLS **aboutit**, puis le flux HTTP/2 casse (`INTERNAL_ERROR`) ; en HTTP/1.1 forcé il expire à zéro octet ; **depuis Windows hors WSL aussi** ⇒ ⛔ ce n'est pas WSL. Le document vient donc de **deux miroirs indépendants** (`cdn.sparkfun.com`, `pololu.com`) dont les copies ont la **même empreinte `sha256`**. 🔴 **ET LA TABLE DU FIRMWARE EST PROUVÉE PAR EXTRACTION CROISÉE** : `python3 tools/verif_sr03.py <AN4545.pdf> firmware/desknode/main/dn_console.c` extrait la séquence **des deux côtés** et les compare — ⛔ le harnais **ne contient pas** la séquence, il ne prouverait que sa cohérence avec lui-même. Il **se prouve par mutation** (valeur changée · ordre permuté · entrée supprimée · public non déclaré ⇒ **4 mutants, 4 rouges**) et **refuse le mauvais document** sur son empreinte. ⚠️ **Cette garde existe à cause d'une vraie erreur** : deux URL nommées « VL6180X » rendaient en `200` un PDF ST authentique… **du VL53L0X**. 🔴 **`balayage` REJOUE À L'IDENTIQUE** les huit points de §13.19.5 (1, 2, 3, 5, 10, 20, 50, 100 ms à gain 1,0×) — **le critère n'est PAS « ça rend un nombre », c'est que la réponse VARIE AVEC LA DURÉE**. 🔴 **`range` distingue TROIS états, ⛔ pas deux** : *valide* · *la puce DIT qu'elle a échoué* (code décodé depuis [DS] Table 12) · *valeur plausible MAIS fausse* — et il **dit qu'il ne peut pas trancher le troisième**, parce qu'il faut la distance **physique au mètre**. ⚠️ **Le troisième état est documenté par ST** : l'erreur 16 `Ranging_Filtered` — *« a high reflectance target … between 600mm to 1.2m »* — ne sort **qu'avec l'API ST**, absente ici (driver MAISON, X5). 🔴 **PLAFOND STRUCTUREL** : [DS] §6.2.42 définit `RESULT__RANGE_VAL` comme un champ **`[7:0]` en MILLIMÈTRES** ⇒ **255 mm est le maximum REPRÉSENTABLE**, et **aucun facteur d'échelle n'est publié** dans les trois documents ST récupérés. ⛔ **Ce n'est PAS une étiquette de performance** (celles-là se contestent par la mesure) : c'est la **carte des registres**. ⚠️ **La relecture des registres PRIVÉS est imprimée comme une DONNÉE, ⛔ pas comme un verdict** — ST ne les documente pas et ne promet nulle part qu'ils se relisent ; seuls les **publics** concluent. ⛔ **`tof` ne touche NI `dn_env` NI `dn_ui`** : c'est un instrument de qualification, hors du chemin de régime, tant qu'AC1 n'a pas rendu son verdict |
  | **`w2`** (dn4-3) | le critère **« une case de six doit BOUGER »**, MESURÉ. Patron `FAN_RPM` de `dn4-6`, jugé sur la **valeur AFFICHÉE** (⛔ jamais sur la source) : **étendue ≥ 5** · **taux de changement du TEXTE ≥ 10 %** · **σ ≥ 1**, seuils **écrits AVANT le tir**. Références imprimées par la commande elle-même : `FAN_RPM` **13 / 55,2 % / 2,02** (n=959) **QUALIFIE**, `ASIC_POWER` **3 / 57,9 % / 0,75** **NE QUALIFIE PAS**. 🔴 **SIX pistes depuis `dn3-3`, et ce n'est pas du zèle** — ⚠️ **la CADENCE est désormais PAR PISTE** (`@5s` pour les cinq capteurs, `@1s` pour `CPU`), chaque nom la porte, `dn_w2_cadence_ms()` la publie, et **la gate vérifie que les deux concordent** ; la colonne **`rup`** compte les **chaînes brisées** (sortie d'Ambient, valeur invalide), qui sont **RETIRÉES du dénominateur** du taux — sans ce retrait le biais irait TOUJOURS vers « NE QUALIFIE PAS ». 🔴 **La 6ᵉ piste, `CPU % (dixieme) @1s [AMBIENT seul]`, est la SEULE qui porte une case nourrie par le PC** : elle existe parce qu'**AC2.1 de `dn3-3` n'avait AUCUN instrument** — les cinq appelants d'origine étaient tous des capteurs locaux. Elle n'accumule **qu'en Ambient**, parce que sous agent réel il n'y a **plus de console** pour délimiter la fenêtre. ⛔ Elle ne compare donc jamais Actif et Ambient. Motifs complets dans `dn_env.h` et `hardware/` §24.13.1. **Le reste du raisonnement d'origine tient** : X2 est un **choix entre deux candidats** — comparer le lux et la pression avec deux instruments différents ne prouverait rien. Et pour la pression c'est **la précision qui est en jeu** (AC11 : ⛔ aucune décimale que la source ne porte), d'où **deux formatages accumulés séparément** (`1013 hPa` et `1013,2 hPa`). La quatrième piste est la **TEMPÉRATURE**, en **témoin de CONTRÔLE** : c'est une grandeur **déjà affichée dans une case livrée**, donc son W2 dit ce que « bouger assez » vaut *sur cette carte, dans cette pièce*. ⛔ Sans témoin, un verdict W2 n'est qu'un nombre comparé à un seuil venu d'ailleurs. 🔴 **Échantillonné DANS LE FIRMWARE**, un point par cycle de 5 s : `tools/dn_console.py` **perd des lignes** (mesuré, y compris en invocation solo, et **deux captures entièrement vides** le 2026-08-20), et un taux de changement calculé sur un échantillonnage qui perd des points est **faux d'un biais qu'on ne sait pas borner**. ⛔ **Seules les valeurs VALIDES sont échantillonnées** : compter une absence comme un changement gonflerait le taux d'un capteur **MUET** — l'instrument dirait « ça bouge » d'une case qui ne dit rien. ⚠️ **Le taux se calcule sur les TRANSITIONS (n−1)**, pas sur n : le premier échantillon n'a pas de précédent, et diviser par n gonflerait les petits échantillons. σ est calculé **en entiers** (variance = E[x²] − E[x]², racine par Newton) — ⛔ aucun flottant. ⚠️ **La fenêtre fait n × 5 s, et un verdict sur une fenêtre trop courte ne vaut rien** : une pression atmosphérique bouge sur des **heures**, un lux de bureau sur des **secondes**. `w2 reset` remet **toutes** les pistes à zéro **ensemble**, pour que la comparaison porte sur la même fenêtre |
  | **`i2c`** (dn2-1/**dn4-2**) | le **bus vu de ses adresses** : `i2c` scanne 0x08..0x77, `i2c lire <addr> <reg> [n]` lit un registre (hexa). 🔴 **dn4-2 ajoute QUATRE sous-commandes — TROIS primitives de lecture/écriture, plus `rafale`** (⚠️ *ce README, le docblock et l'aide écrivaient « TROIS » pour quatre : le critère de sûreté « aucune boucle » avait été écrit pour « les trois » et exemptait donc `rafale` en silence — corrigé le 2026-08-20*). **Les trois primitives existent parce que l'instrument ne qualifiait qu'UN capteur sur les trois qu'elle branche** — et ce n'est pas une opinion de conception, c'est une incompatibilité de protocole lue aux datasheets : **`i2c lire` ÉCRIT un octet d'index PUIS lit**, or le **BH1750 n'a AUCUN registre** (l'octet est un **OPCODE** : `00` = power down, `07` = reset ⇒ l'utiliser **le pilote au hasard** au lieu de le lire) et le **VL6180X exige un index sur 16 BITS** (un seul octet est une violation de protocole, dont l'échec **ressemble exactement à une mauvaise soudure**). ⇒ **`i2c ecrire <addr> <o1> [o2..o8]`** écrit **SANS lire** (⚠️ elle **peut casser un composant sain**, elle **dit ce qu'elle a envoyé**, et elle **refuse AVANT d'écrire** si un octet est mal formé — une écriture partielle laisse un état qu'on ne sait pas nommer) ; **`i2c brut <addr> [n]`** lit **SANS index** (les 2 octets de mesure du BH1750, convertis en lux — `lux = brut / 1,2` au `MTreg` par défaut, **dixième TRONQUÉ**) ; **`i2c lire16 <addr> <reg16> [n]`** pose un index de **2 octets, MSB d'abord** (`i2c lire16 29 0000` → **`B4`** = VL6180X ; témoin négatif : `i2c lire 29 C0` **ne doit pas** rendre `EE` de façon reproductible, sinon c'est un VL53L0X **et le sachet ment**). 🔴 **NE JAMAIS enchaîner `i2c ecrire 23 10` et `i2c brut 23 2` dans le MÊME LOT** : le pilote envoie un lot en quelques **dizaines** de ms, la mesure du BH1750 en demande **jusqu'à 180** — la lecture rendrait `00 00` et le capteur serait déclaré mort alors qu'il fonctionne. ⇒ **deux invocations séparées**, et la commande l'imprime elle-même quand elle voit passer l'opcode. 🔴 **`i2c rafale <ms=1000..30000>`** est l'instrument d'**AC9** : elle sonde `0x08..0x77` **en boucle** pendant une fenêtre bornée **ET TENUE PAR ADRESSE** (⚠️ elle ne l'était qu'entre passes complètes jusqu'à la revue du 2026-08-20 : une passe entamée à une microseconde de la fin allait jusqu'au bout, soit 112 sondages de plus), **sans rien imprimer ELLE-MÊME avant la fin** (⚠️ le driver IDF, lui, imprime un `probe device timeout` par sondage expiré — d'où le compteur), avec un **TÉMOIN POSITIF** (`0x20`+`0x5D` à chaque passe : sans lui, un bus coincé rendait une « cadence » qui était une cadence de NACKs), puis publie **durée réelle, passes, sondages émis, CADENCE en sondages/s, acquittements et timeouts**. Elle existe parce que D9 a soudé les capteurs : le rejeu d'AC7 (a) ne peut plus se faire en débranchant un fil, et la voie logicielle est **la seule restante**. ⛔ **Ce n'est PAS `i2c` dans une boucle hôte** — `i2c` imprime à chaque passe, ce qui noierait la capture et changerait la cadence mesurée ; et le pilote **perd des lignes** quand on lui passe plusieurs commandes (mesuré : 6 captures sur 20, `…-capteurs-i2c.md` §13.16.2). ⚠️ **Elle BLOQUE le REPL pendant toute sa fenêtre, et c'est voulu** — l'owner appuie sur la dalle, il ne tape pas ; passer `--timeout` en conséquence, sinon le pilote annonce une **carte muette sur une carte qui va parfaitement bien**. ✅ **Aucun risque électrique ni thermique** : que des adresses, **aucune écriture de donnée**, bornées hors adresses réservées. ⛔ **À 100 kHz, PAS 400** — corrigé par la revue du 2026-08-20 : `i2c_master_probe()` reprogramme le bus à 100 kHz à chaque sondage (`esp_driver_i2c/i2c_master.c:1391`). Sans effet durable (chaque transaction de device réapplique son `scl_speed_hz`), **mais le sondage est tout ce que le scan et la rafale font** ⇒ les cadences publiées d'AC9 décrivent une saturation à **100 kHz**. 🔴 **Chaque adresse trouvée est RE-SONDÉE 5 fois et le résultat publié `n/5`** — un scan à une passe fabrique des faux positifs, et il en a sorti un **à `0x76`, l'adresse du BME680, alors qu'aucun capteur n'était branché** (`hardware/…-capteurs-i2c.md` §13.2). Témoin positif intégré : la commande conclut elle-même sur `0x20`+`0x5D`, et un scan qui ne les voit pas est un instrument cassé. ⚠️ **bloque le REPL — donc le transport PC — et le coût dépend de la SOUS-COMMANDE** : un scan sain ~**26 ms**, son **pire cas ≈ 5,7 s**, et **`rafale` jusqu'à 30 s**. ⚠️ *Cette ligne publiait « **pire cas ~9 s** (borné par `DN_I2C_SCAN_BUDGET_MS`) » jusqu'à la revue du **2026-08-24** — **deux erreurs dans six mots** : ~9 s est le pire cas **d'AVANT** ce budget (son propre commentaire le dit), et le budget vaut **2 500 ms**, donc il ne peut pas produire 9 s ; surtout **il ne borne que la boucle de DÉCOUVERTE** — la boucle de **confirmation** (jusqu'à 16 candidats × 4 × 50 ms = 3 200 ms) est **hors budget**. Réel : 2 500 + 3 200 ≈ **5,7 s**, et ce n'est **pas** « borné par `DN_I2C_SCAN_BUDGET_MS` ». Le correctif qui existait pour arrêter de facturer « ~26 ms » à toutes les sous-commandes republiait un chiffre périmé avec une attribution fausse.* ⚠️ *Cette ligne facturait « ~26 ms » pour toute la commande, y compris pour la sous-commande à 30 000 ms — corrigé par la revue du 2026-08-20.* |
  | **`pc`** (dn2-2) | la **liaison PC** : état (VIVANTE / MORTE / jamais reçue), dernière valeur + son âge, compteurs (trames valides, doublons, pertes de seq, **resynchros**, reprises, rejets **par cause** — ⚠️ « tronquée » = la fin de ligne est PERDUE, **« trop longue »** = la ligne dépasse **71 o** (⚠️ 63 avant `dn4-6` — corrigé par la revue du 2026-08-19) — deux diagnostics opposés, **MAIS SEULEMENT JUSQU'À 124** : le REPL délivre **124 caractères de trame** au parseur (MESURÉ en dn4-1), donc toute ligne émise à **125 o ou plus arrive AMPUTÉE** — symptôme « tronquée » — tout en étant comptée « trop longue ». 🔴 **La plage réellement discriminante est 72..124 = 53 o** (⚠️ elle valait 64..124 = 61 o avant que `dn4-6` porte la borne à 71 : elle **rétrécit de 13 % et reste ATTEIGNABLE**, ce qui est la condition pour que ce compteur ne devienne pas décoratif — *« et un compteur décoratif est un instrument qui ment »*) ; au-delà, `rejets_trop_longue` ne prouve plus qu'un émetteur a changé de format, il peut aussi dire que le transport a coupé (revue 2026-08-19)), latence acceptation→label. `pc reset` remet les compteurs **et oublie le seq** (sans ça, une campagne relancée avec la trame d'exemple retombait en doublon et mesurait du vide). **`pc $DN,…`** ingère UNE trame — c'est le dialecte de l'agent en branche A, et l'injecteur des campagnes de bruit. 🔴 **dn4-1** : `pc` liste désormais **les cinq métriques une par une** avec **leur propre état et leur propre âge** (une horloge par métrique) — le résumé global « liaison PC » dirait « VIVANTE » avec quatre cases mortes. Et **`pc pousse groupe\|etale`** est l'A/B du levier n°1 (W4), **NON ADOPTÉ** : mesuré, l'étalement divise le pic par 1,94 mais **jette 18,1 % des mises à jour** (185 poussées atteignent l'écran sur **226** trames reçues : **41 / 226 = 18,1 %** — publié « 19 % » jusqu'au 2026-08-19, ce qui était 185/**228**, le dénominateur de l'autre branche) et multiplie la latence maximale par 4 |
  | **`widget`** (dn3-1) | le **modèle de case** : pour chacune des 6 cases, sa **forme** (widget / nue), son **régime** (RÉELLE / SIMULÉE / ABSENTE), si elle est **dessinée en ce moment**, et ses valeurs — le tout **RELU de l'état réel**, jamais récité d'une constante. Plus la forme **annoncée** de **chacun des quatre mocks** — dn3-2 les a généralisés (W5) : GPU 38→72 **%** / 26 s (⚠️ **dn4-1** : la grandeur 0 du GPU est le **pourcentage** depuis D10 — la rampe s'affiche donc en `%`, pas en °C ; **les nombres et la période ne bougent PAS**, même motif que DISQUE), RAM 18→78 % / 34 s, RÉSEAU 5→985 Mb/s / 14 s, **DISQUE** 800→1600 **Mo/s** / 20 s (⚠️ dn4-1 : la case a changé de métrique **et d'unité**, mais **les nombres et la période ne bougent PAS** — la ligne « mock on » de §16.1 doit rester rejouable à l'identique, et 800-1600 Mo/s reste plausible pour un NVMe), toutes rampes triangulaires au pas de 1 s. ⚠️ **Périodes PAIRES et ≥ 2** — la rampe n'est bornée que dans ce cas, et le boot le **vérifie** désormais. ⚠️ Périodes premières entre elles autant que possible : des périodes multiples feraient battre la grille à l'unisson, ce qui n'est pas le régime réel qu'AC8 chiffre. 🔴 **CPU et AMBIANCE n'ont PAS de mock** : elles ont des sources RÉELLES, et D6 veut que « PC éteint, une seule case sur six est vivante » **se voie**. Et l'icône active. Sous-commandes : **`widget groupe on\|off\|union`** (l'A/B d'invalidation d'AC8, §15.5 — rejouable sans reflasher. 🔴 **`union` ajouté par `dn4-10` le 2026-08-23 et ABSENT DE CE README jusqu'à la revue de code du 2026-08-24** — exactement le grief que `widget bandes` avait déjà valu au dépôt, deux paragraphes plus loin : *« une commande qu'on ne trouve que depuis la carte n'est pas documentée »*. ⛔ **`union` est une VOIE MORTE mesurée** — 0,97 corruption/s contre 0,94 en `on`, et des micro-rectangles à l'œil — **et il est CASSÉ** : la zone unie ne couvre que les labels de valeur, donc la **jauge** et le **badge SIMULÉ** sont écrits l'invalidation coupée et **jamais resalis** (revue de code du 2026-08-24). Le mode reste dans le firmware pour ne pas perdre l'A/B, ⛔ pas parce qu'il marche), **`widget opa <0..255>`** et **`widget voile <0..255>`** (l'A/B d'opacité, §15.6 ; **bornées et REFUSÉES** hors plage, jamais écrêtées), **`widget mock on\|off`** (couper le mock rend la case ABSENTE : c'est le témoin que le mock EST sa seule source), **`widget icone <case> <-1..N>`** (⚠️ **la borne haute est CELLE DE LA TABLE, ⛔ pas un nombre écrit ici** — `widget icone` la relit et l'imprime, avec la marque « ← EN PLACE » **dérivée de l'état courant** ; ce README annonçait `<0..4>` pour une table qui en portait **neuf**, rendant les rangs 5-8 inatteignables à qui le suit. `-1` **rend la main à l'icône du descripteur**, seul chemin de retour pour `CPU`/`RAM`/`RÉSEAU`, dont les icônes ne sont pas dans la table), **`widget couleur <case> <0xRRGGBB>`** (dn4-14 — l'A/B de **couleur d'accent** à chaud : elle peint l'accent de tuile, la série 0 de la courbe, et le chevron **sur les seules cases à deux séries**. `0` **rend la main au descripteur** ⇒ ⛔ elle ne peut pas poser un accent noir. **AUCUN état livré** : au boot le descripteur fait foi. ⛔ **`veille off` d'abord** — une scène reconstruite en Ambient pose la jauge 27 px trop haut. La page `widget` liste désormais les cases forcées), **`widget icone <case> <0..4>`** (l'A/B de glyphe **sur n'importe quelle case** — ⚠️ **dn4-1 l'a généralisé** : il écrivait l'index 4 EN DUR et aurait continué de viser « l'ancienne case ventilateur » après le renommage, en l'annonçant comme un choix), **`widget demo on\|off`** (la **7ᵉ métrique fictive** d'AC1 : une case complète produite par le même appel que les autres, depuis un descripteur et **rien d'autre**), **`widget pousser <idx>`** (UNE mise à jour synthétique — ⚠️ **une par appel**, sinon les N invalidations tombent dans le même cycle LVGL et LVGL les fusionne ; c'est l'appelant PC qui les espace). **`widget oublier <idx>`**, **`widget rafale`** (AC8 — les 6 cases poussées sous **UN SEUL verrou**, donc dans **un seul cycle LVGL** : c'est l'instrument qui produit le cas que l'extrapolation prédit et que le régime réel ne produit **jamais**, puisque les six sources ne sont pas synchronisées. ⛔ Il **contredit délibérément** l'interdit de `pousser`, d'où son autre nom ; 🔴 **elle n'a PLUS de témoin de validité, et c'est délibéré (2026-08-19)** : `cycles pour dessiner la rafale` en était à sa **troisième** sémantique (`cycles intercalés`, puis `== 0`, puis `== 1`) et **n'a jamais pu rendre autre chose que sa valeur de succès** — la boucle d'attente sortait au **premier** cycle observé. Supprimé. ⇒ **la fusion se prouve par `flush`**, et par lui seul : `flush` avant/après le tir doit montrer **N flushes pour UN cycle**. ✅ Effet de bord : la rafale **ne dort plus**), **`widget nue <idx> on|off`** (W11 — rendre une case **nue à chaud** : le **témoin négatif** d'AC8 ne quitte pas le firmware, sinon AC8 comparerait deux firmwares. ⚠️ **reconstruit la scène**), **`widget barre 1hz|minute`** (W2/AC4 — la cadence de la barre heure/date, **défaut = minute** parce que la maquette normative écrit « 21:46 » **sans secondes**), **`widget bandes on|off`** (W8/AC9 — le **levier n°2** : un callback `LV_EVENT_INVALIDATE_AREA` étend chaque zone salie à la **pleine largeur**, pour que deux cases d'une même ligne se CONTIENNENT et que LVGL les joigne. Chiffré en §16.7 : il **gagne SOUS CONDITION**. ⚠️ Absent de ce README jusqu'à la revue du 2026-08-18, alors que §16.7 en publiait déjà les chiffres — « une commande qu'on ne trouve que depuis la carte n'est pas documentée »). ⚠️ **`pousser` ne se retire pas TOUT SEUL** : la case reste SIMULÉE jusqu'à ce que sa vraie source reparle. ✅ **dn3-2 solde ce différé** (`deferred-work.md:1019-1023`) avec **`widget oublier <idx>`**, qui rend la case à son **régime naturel** (ABSENTE ; le mock la reprend au tick suivant s'il est armé, une source réelle la repeindra quand elle parlera). ⛔ **Ne plus rebooter pour ça** : un `reboot` rejoue le boot entier et **perd la fenêtre de mesure**. Sans cette commande, tout constat owner lancé après une campagne verrait des badges « SIMULÉ » **résiduels** et pourrait les lire comme une régression. **`widget piste <0xRRGGBB>`** (la **piste de la jauge**, c'est-à-dire le fond de la part NON remplie — ajoutée en séance le 2026-08-18, `0x203040` → `0x5A5F6A`, **puis `0x141820` les 2026-08-30/31** (séance `/desknode-board`, **arbitrage owner, LE VERT ÉTANT ASSUMÉ** : la piste se lit verte, et c'est une **contrainte de la dalle**, ⛔ pas un défaut de la valeur — le témoin `widget piste 0x303030`, gris **exactement neutre** (`G - R = 0`), **se lit vert lui aussi** ⇒ **le prédicteur est la LUMINANCE, ⛔ pas `G - R`**, et **il n'existe pas de piste à la fois sombre et neutre sur ce matériel**. ✅ 0 % / régime ABSENTE — donc **PC éteint** — éprouvé : la barre reste **visible**. ⛔ **ÉCART OUVERT** : la piste face au cuivre du PCB **en Actif** n'a pas été regardée. Chiffres et branches écartées dans le docblock de `W_COL_PISTE_DEFAUT`), arbitrage **à l'œil** ; ⚠️ **reconstruit la scène**. Constat d'origine : *« la barre de vide apparaît en vert »* — **le code n'a jamais posé de vert**, c'est le PCB par contraste simultané). ⚠️ `opa`, `voile`, `icone`, **`nue` et `piste`** **reconstruisent la scène**, ce qui retire le stimulus `anim` et la démo, et ramène la vue au dashboard. 🔴 **Et ce sont les CINQ sous-commandes de `widget` qui BLOQUENT le REPL** — ⚠️ **corrigé DEUX FOIS** : ce paragraphe écrivait « les **trois** seules » **dix lignes après** avoir décrit `widget nue` comme « ⚠️ reconstruit la scène ». Or `nue` est l'instrument **central** du témoin négatif d'AC8, celui qu'on actionne le plus pendant une campagne — — donc le transport PC (dn2-2) — le temps d'un `lvgl_port_lock(2000)` **plus** un `build_scene()` complet : les deux racines sont détruites et reconstruites, soit plus lourd qu'une transition, que §15.6 chiffre à **307-322 ms** avec un plancher de rendu LVGL ~230 ms. Comparaison : `i2c` **scan sain** bloque ~26 ms (⚠️ *ce chiffre était donné nu jusqu'au 2026-08-24 — c'est le cas SAIN de la SOUS-COMMANDE de scan, ⛔ pas le coût de `i2c` : le pire cas du scan est ≈ 5,7 s et `rafale` va jusqu'à 30 s. C'est le site que la revue du 2026-08-20 avait nommé et pas corrigé*). Ne pas les appeler pendant une campagne de mesure de la liaison (relevé en revue de code le 2026-08-18 : le docblock de `cmd_widget` affirmait qu'aucune sous-commande n'était un travail long). 🔴 **dn4-6 a ajouté SEPT sous-commandes qui reconstruisent** — ⚠️ **corrigé par la revue de code du 2026-08-19, qui l'a trouvé rompu une TROISIÈME fois** : ce README publiait « de CINQ à ONZE » pendant que le docblock de `cmd_widget` publiait « HUIT de plus, soit TREIZE » en n'en listant que **sept**. Trois textes, trois valeurs, aucune juste — et corrigés dans le **même commit**, donc la règle « dans le même geste » avait été tenue à la lettre et manquée sur le fond. 🔴 **ET UNE CINQUIÈME FOIS, LE 2026-08-30, PAR LA REVUE DE `dn4-14-2` : cette phrase portait encore « et le compte passe de CINQ à DOUZE » — un SECOND compte, contradictoire avec le 16 publié plus bas, dans la MÊME ligne.** ⚠️ Et la garde écrite pour l'attraper ne pouvait pas le voir : elle exigeait `**` collés au nombre, alors que le gras porte sur la phrase entière — **une gate qui mesurait une forme markdown, ⛔ pas un compte**. Les deux sont corrigés : le compte absolu a disparu d'ici (il est RECALCULÉ, voir plus bas) et la garde cherche désormais le nombre, en chiffres comme en toutes lettres. ⛔ **ET L'ÉNUMÉRATION QUI SUIVAIT EST SUPPRIMÉE, PAS MISE À JOUR** : elle listait douze noms — anciennes `opa` · `voile` · `icone` · `nue` · `piste` ; dn4-6 `voie` · `grandeurs` · `dispo` · `entete` · `val` · `police` · `grille` — en omettant `detpan`, `fond`, `couleur` et `titre`, c'est-à-dire en se périmant à chaque ajout. *Une liste écrite à la main à côté d'un compte calculé est le prochain point de rupture.* ⇒ `widget` **imprime** la liste, et la gate la **recalcule**. ⛔ `replacer`, `largeur`, `detail`, `courbe`, `jauge` et `date` **ne reconstruisent pas**. **`widget voie defaut\|avantd12\|a\|b\|c\|c2\|repli`** applique une **voie entière** de l'A/B de dn4-6 et **imprime son PRIX AVANT le constat owner** (⚠️ elle reconstruit **UNE SEULE FOIS**, ~350 ms de REPL bloqué — ce README annonçait « DEUX FOIS, ~700 ms », ce qui **décrivait le défaut corrigé par `ce41caf`**, pas le produit : `dn_ui_set_voie()` prend un verrou et appelle un seul `build_scene()`. ⚠️ `defaut` applique **les défauts du firmware**, donc **D12 / case 163** depuis que la voie retenue est gravée ; `avantd12` est la référence **70/60 ⇒ case 156** de la table §18.1, ajoutée par la revue parce que cette ligne n'était plus rejouable autrement) : `a` = police 28 + **MENU supprimé** (case 180) + en-tête compacté ; `b` = 3ᵉ police + D12 (case 163) — 🔴 **la police ~22 n'est PAS embarquée**, la branche est jouée en 14 px, donc « la géométrie est représentative, **la lisibilité ne l'est pas** » ; `c` = **côte à côte**, géométrie **inchangée** ; `c2` = variante **MIXTE** (ligne 1 côte à côte), qui **exige** la case de 180. **`widget dispo empile\|cote\|mixte`** (⛔ **EMPILE reste le défaut** tant que rien ne l'a battu SUR LA DALLE), **`widget entete normal\|compact`** (🔴 **décision OWNER** : elle change les SIX cases, et l'icône est le **seul** endroit où le champ `couleur` du descripteur est EXERCÉ), **`widget val <y> <pas>`** (elle **calcule et imprime** l'interligne, la garde sous l'en-tête et le `y_bas` à 4 grandeurs, et **dit** quand l'interligne passe sous le critère écrit de D12 : ≥ 5 px), **`widget police <taille>`** (⚠️ **`14|28` était écrit ici et dans l'`aide` enregistrée jusqu'à la revue du 2026-08-30**, alors que la liste se RELIT de `DN_FONT_LISTE` depuis `dn4-14-2` — le défaut exact que cette liste générée existe pour empêcher), **`widget grille <barre_h> <menu_h>`** (`70 60` = l'état des lieux, `60 51` = D12, `60 0` = voie (a) — ⚠️ elle **annonce que toute coordonnée tactile publiée devient PÉRIMÉE**). 🔴 **dn4-14-2 AJOUTE TROIS SOUS-COMMANDES, ET ELLES SONT ICI PARCE QUE L'`aide` LES A OUBLIÉES** — relevé par la revue de code du 2026-08-30, qui a trouvé la chaîne `DN_CMD("widget", …)` **enregistrée** encore à `police 14|28` et sans aucune des trois, sous le commentaire qui exige de les inscrire « ICI **ET** dans le « Jeu complet » du README dans le même geste ». C'est le grief que `union` et `bandes` avaient déjà valu au dépôt, une troisième fois : **`widget titre [<police>|defaut]`** (la police du TITRE de case ; nu, il RELIT l'état et imprime le verdict de largeur — ⚠️ **RECONSTRUIT**), **`widget titre suit on|off`** (les libellés SECONDAIRES prennent la police du titre — **`on` par verdict owner du 2026-08-30**, verbatim *« Oui — tout le chrome en 18 »* ; ⚠️ l'en-tête `dn_widget.h` a annoncé « `off` par défaut, aucun état livré » jusqu'à la revue, pendant que le code posait `true`, et c'est CE mensonge qui masquait que la réserve verticale du libellé était restée calée sur `dn_font_14` ; ⚠️ **RECONSTRUIT**), **`widget date [<police>|defaut]`** (la police de la DATE de barre — ⛔ **ne reconstruit PAS**, le label est repeint en place, parce qu'une reconstruction *pendant la veille* pose la jauge 27 px trop haut ; nu, il rend les deux verdicts, horizontal **et** vertical). ⚠️ Et l'instrument d'**AC5** : **`widget largeur`** rend la table des couples avec leur largeur **RELUE de `lv_text_get_size()`** — la police réellement liée, kerning compris — ⛔ **jamais un produit `nb_caractères × largeur_moyenne`**, qui est l'extrapolation (~15,8 px/car.) ayant servi à **écarter le côte à côte en dn3-1** et que cette table **confronte**. **`widget largeur <texte> [<police>]`** mesure une chaîne libre dans une police NOMMÉE, **`widget largeur mur`** rend le TABLEAU du mur horizontal — slots relus du rendu, chaînes nommées dans chaque police d'interface, et le pire cas de date BALAYÉ (⚠️ **le domaine n'est plus écrit** : « 7 × 12 × 32 » était publié à quatre endroits pendant que le code balayait 31 jours *et* des jours qui n'existent pas dans leur mois — l'instrument IMPRIME désormais son propre compte), **`widget largeur reset`** remet à zéro les **quatre** compteurs de géométrie (⚠️ **le 4ᵉ est né de la revue du 2026-08-30** : le clip ACCEPTÉ de la date de barre n'avait NI log NI compteur, donc `widget` rendait « 0 trop-large » pendant que « HEURE NON POSÉE » était clippée à l'écran) — ⛔ parce qu'« un texte trop large ne se voit PAS comme une erreur » : LVGL clippe au parent **sans un mot**, et « rien n'a planté » n'est pas « ça tient ». 🔴 **Ils sont TROIS depuis la revue du 2026-08-19, et pas deux** : `chevauchements` (deux colonnes se marchent dessus — **côte à côte SEULEMENT**), `trop larges` (une valeur seule dépasse la case — **le trou de la disposition LIVRÉE** : en `EMPILE` il n'y a aucune colonne droite à caler, donc rien n'était mesuré, et la marge est de **4 px** sur `c.max 100,0 %` — 197 px pour 201 utiles), et `débordements` (la valeur sort en **hauteur**). ⛔ Trois causes, trois compteurs : ce dépôt a déjà payé d'avoir mis deux diagnostics opposés dans le même seau (`tronquee`/`trop_longue`). Enfin deux instruments qui **ne reconstruisent pas** : **`widget detail`** (ce que la GRANDE VALEUR du détail a réellement POSÉ — texte **copié sous le verrou**, largeur, panneau ; ⛔ elle refuse de conclure tant que la géométrie n'est pas résolue, au lieu de crier au loup sur un parent NULL) et **`widget replacer on|off`** (l'instrument de **bissection** du tressautement : `off` retire `valeur_placer()` du chemin de mise à jour, qui redevient ligne pour ligne celui de `dn4-1` — ⛔ légitime **uniquement** en `EMPILE`). Enfin **`widget demo on\|off [n]`** : le `n` (1..6) est le **SEUL** chemin vers les deux témoins d'AC2 de dn4-6 — l'abandon de **jauge** (n ≥ 3) et le **clamp** de `DN_WIDGET_GRANDEURS_MAX` (n = 5, donc **au-delà du maximum**, ce qui est le point). 🔴 **dn4-9 — `widget` PUBLIE DÉSORMAIS DEUX COMPTES ET DEUX LISTES D'INDICES PAR CASE, ⛔ plus un seul compte.** Depuis que la CASE et le DÉTAIL montrent des sous-ensembles **différents** de la même métrique, « CPU : 3 grandeurs » ne dit pas LESQUELLES — et `[0, 1, 3]` (ce que D13 demande) comme `[0, 1, 2]` (l'ancien mécanisme) comptent **trois**. La table imprime donc `case N [i, j, k] · detail N`. ⚠️ **`widget grandeurs <case> <n>` NE DÉPLACE PLUS QUE LA CASE** : le compte du DÉTAIL n'a **aucun** override à chaud, et les `n` grandeurs montrées sont **les `n` PREMIÈRES DU DÉTAIL** (`0..n-1`), ⛔ pas les `n` premières de la sélection. ⇒ Sur `CPU`, `widget grandeurs 0 3` montre `[%, GHz, c.max]` et **⛔ PAS** la sélection livrée `[%, GHz, °C]` ; c'est `widget grandeurs 0 0` qui rend la case à son descripteur. 🔴 **ET `widget` NU REND MAINTENANT LES TROIS COMPTEURS DE GÉOMÉTRIE, SANS RIEN DÉTRUIRE** — c'est un correctif d'instrument, ⛔ pas un confort : `widget largeur` n'en imprimait qu'**UN**, et les trois ne sortaient que de `widget voie` et `widget grandeurs`, **qui reconstruisent (~350 ms) et remettent les compteurs à zéro juste avant**. Lire « avant » DÉTRUISAIT donc ce qu'on relève, et le protocole « avant / après » d'une campagne **n'était pas exécutable en l'état**. ⛔ Les trois ne s'additionnent jamais. 🔴 **Le compte des sous-commandes qui reconstruisent est de **16**, et il n'est PLUS ÉCRIT : il est RECALCULÉ par la gate** (`tools/verif_veille_dn33.py`, `bloc_reconstruit`), qui remonte chaque appel à `build_scene()` jusqu'à sa sous-commande et CONFRONTE le résultat à ce que ce README **et** `dn_console.c` publient. ⚠️ **Ce compte a rompu CINQ fois** — 2026-08-18, -19, puis deux fois le -29. Les quatre premières étaient des arriérés ; **la cinquième est pire** : `dn4-14-2` a recompté depuis le code et trouvé que le **TREIZE** publié était **faux au moment même où on l'écrivait**. Il **omettait `widget detpan` et `widget fond`**, que ce README décrivait pourtant « reconstruit la scène » — et cette même ligne portait DEUX valeurs contradictoires. ⛔ *« Faire attention » a échoué cinq fois de suite : c'est pour ça que le nombre est maintenant CALCULÉ.* ⚠️ `widget courbe`, lui, ne reconstruit **pas** : `dn_ui_detail_courbe_axes()` est un LECTEUR. Et `widget date` (dn4-14-2) non plus — le label est repeint EN PLACE, parce qu'une reconstruction **pendant la veille** poserait la jauge 27 px trop haut : `widget` nu est une **lecture pure**, il n'en ajoute aucune  🔴 **dn4-4 AJOUTE DEUX INSTRUMENTS, ET LES DEUX SONT DES LECTURES PURES** (⛔ ils ne reconstruisent rien, le compte est INCHANGÉ — ⚠️ « reste DOUZE » était écrit ici : un total ABSOLU dans une clause historique se périme au premier ajout, et celui-là s'est périmé quatre fois) : **`widget jauge [<case>]`** relit le rectangle que LVGL a **réellement posé** pour la barre, en coordonnées ÉCRAN, et l'imprime **à côté** de ce que la formule calcule — c'est lui qui a tranché le désaccord publié sur la bande tactile de la jauge `RAM` (`affichage.md` §22.3 : la formule était juste **à 1 px près**, le pixel venant du `border_width = 1` de la racine de case, et les 13-24 px de la visée du 2026-08-20 s'expliquent par une **géométrie commutable à chaud** — `widget val 66 40` repose la bande à `y = 356..365`, le centre exact des 9 taps). ⛔ **Toute coordonnée tactile se relit désormais ici, elle ne se récite plus** : l'origine des cases n'a qu'**une seule fabrique** (`ui_case_origine()`), prise par la boucle de construction **et** par l'instrument. Et **`widget courbe`** relit le rectangle de la **courbe** et celui de son **cadre**, puis **vérifie l'invariant du template** (bas du cadre = **370**, panneau du bas = **385**) — ⛔ il le DIT s'il a changé, au lieu de le casser en silence. Et **`widget detpan <0\|40..200>`** est le **TÉMOIN NÉGATIF** de la garde de hauteur du détail (AC4.3) — ⛔ **pas un réglage** : au pire cas LIVRÉ le bloc tient **exactement** (`14 + 140 = 154 ≤ 154`, marge ZÉRO), donc **aucune donnée réelle ne peut faire crier cette garde**. À `153`, elle **DOIT** émettre « le bloc de valeurs DÉBORDE EN HAUTEUR » ; si elle se tait, c'est **la garde** qui est cassée, ⛔ pas le stimulus. *Une garde qu'aucun test n'a vue crier n'est pas prouvée.* ⛔ Il ne quitte pas le firmware — même doctrine que `widget nue` : sortir un témoin négatif du produit obligerait à comparer deux firmwares. ⚠️ **reconstruit la scène**. Enfin **`widget fond on\|off`** est la **BORNE HAUTE de « l'option n°2 » du ledger** (*ne pas invalider le fond à la transition*), **déclarée NON ESSAYÉE par `dn3-2`** (§16.8) et **réassignée à `dn4-4`** par le correct-course du 2026-08-18 — ⛔ **pas un réglage, et surtout pas un mode de production** : en modèle `SCREENS`, `fond_poser()` pose une `lv_image` de 480 × 640 RGB565 (**614 400 o**) sur **chacun** des deux écrans et `lv_screen_load()` invalide tout, **alors que le fond est identique d'un écran à l'autre**. `off` le retire complètement, c'est-à-dire mesure **le meilleur cas que l'option pourrait atteindre** : si le meilleur cas ne gagne rien, l'option est **morte — et elle meurt AVEC SON CHIFFRE**, ⛔ pas sur une intuition. ⚠️ **reconstruit la scène** — ⚠️ **et `widget fond` comme `widget detpan` étaient ABSENTS du compte publié jusqu'à `dn4-14-2`** : le total est RECALCULÉ par la gate, ⛔ plus additionné à la main ici |
  | **`rtc`** (dn3-2) | l'**horloge PCF85063A** à `0x51` : état, heure lue **avec sa recevabilité**, âge, registres `0x00..0x11` **RELUS à l'instant**, compteurs **par cause** (i2c / **bcd**), le témoin anti-fantôme, et la pile restante de la tâche. 🔴 **Le bit `OS` (Seconds bit 7) est imprimé en clair et il GOUVERNE l'affichage** : `OS = 1` ⇒ l'oscillateur a décroché ⇒ l'heure lue **ne vaut rien**, et la barre affiche « --:-- HEURE NON POSÉE » — ⛔ **jamais une heure fausse**, parce qu'une barre qui dit « 03:47 » après une coupure est **pire** qu'une barre qui se tait. **`rtc set <AAAA-MM-JJ> <HH:MM[:SS]>`** pose l'heure ; écrire le registre des secondes est ce qui **remet `OS` à 0**, et il n'y a pas d'autre chemin (d'où l'absence de tout `clear_os`). L'écriture est **RELUE** : un `ESP_OK` d'I²C ne prouve pas que la pose a pris. ⚠️ Le **jour de semaine n'est pas demandé**, il est **calculé** de la date (Sakamoto) — la puce ne le déduit pas, elle le compte à part, et le laisser saisir ferait deux sources de vérité. ⚠️ **Époque 2000..2099, et c'est un CHOIX du driver** : la puce porte l'année sur 0..99 et n'a **aucun bit de siècle**. ⚠️ `CAP_SEL` (charge du quartz) est **lu et imprimé mais NON vérifié** : rien sur cette carte ne dit quel quartz est soudé, et un mauvais réglage se paie en **dérive**, pas en panne — consigné comme INCONNU. `rtc reset` remet les compteurs à zéro 🔴 **dn4-18 (2026-08-26) — LA POSE EST DÉSORMAIS AUTOMATIQUE, ET `rtc set` RESTE DOCUMENTÉE COMME LE REPLI.** L'**agent de la tour** interroge `rtc` **à chaque reprise de liaison** (ouverture du port, sortie de backoff) puis **toutes les 600 s**, et il pose l'heure **quand la carte le demande** — c'est-à-dire quand elle rend `NON FIABLE (OS=1)`, ⛔ **jamais** « au démarrage de l'agent ». ⚠️ **À DEUX CONDITIONS, ET ELLES SE LISENT AU BILAN DE L'AGENT** : il faut la branche `--serie` (⛔ sur `--stdout` et `--ws` il n'y a pas de REPL, et l'agent le DIT), et il faut que l'agent tourne. ⇒ **`rtc set` à la main reste le chemin quand l'agent est arrêté** (carte attachée à WSL). ✅ Il repose **aussi** quand la carte se déclare `FIABLE` mais dérive de plus de **120 s** de l'heure de la tour — c'est le trou **été/hiver**, que le bit `OS` ne voit pas par construction. ⚠️ **L'heure de la carte devient dépendante de celle de la TOUR** : une tour à l'heure fausse fait une carte à l'heure fausse, **et la carte dira `OS = 0`**. Détail : `hardware/…-capteurs-i2c.md` §13.15.7. |
  | **`wifi`** (dn2-2) | la maquette **branche B**, ÉCARTÉE par la fourche (verrou RAM, `hardware/…-liaison-pc.md` §12.2). **Non compilée par défaut** : la commande répond « maquette B non compilee » avec la recette de re-mesure |
  ⚠️ Le log de ce projet ne part **plus** sur le header UART GPIO43/44 : la console primaire est
  passée sur l'USB pour pouvoir RECEVOIR des commandes. Pour retrouver le header, voir le
  commentaire de `CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG` dans son `sdkconfig.defaults` : on y récupère
  le log sur **les deux** chemins **et** la console interactive sur l'UART.

`firmware/hello-desknode` (le témoin minimal de P0) :

- au **log** : `I (12280) desknode: DeskNode P0 - up 12 s - retroeclairage ON`, avec un compteur de
  secondes qui progresse (le CPU exécute *notre* code, pas un tampon figé) ;
- à l'**œil** : le **rétroéclairage de la dalle clignote** à 1 s (GPIO6, un GPIO direct). C'est le
  signe de vie *matériel* — un `printf` ne prouve pas que la carte agit sur quoi que ce soit.
  Le buzzer, lui, est sur `EXIO8`, derrière l'expander I²C TCA9554 : hors périmètre P0.
- son log part sur **les deux chemins** (USB **et** header UART GPIO43/44).

- **Baud du moniteur : 115200** · **baud du flash : 460800** (valeurs par défaut de l'IDF, mesurées
  comme fonctionnelles).
- Durées mesurées : build **incrémental 1 s** (rien n'a changé) · build **après `rm -rf build`
  36 s** · **reconstruction totale 54 s** (après `rm -rf build sdkconfig`, la cible est reposée
  depuis `sdkconfig.defaults`) · **flash 6 s**.
- Le projet vit sur **ext4** (`~/projects/desknode/`). ⛔ Ne jamais le déplacer sous `/mnt/c/…` :
  le 9p de WSL2 y divise les temps de build par un ordre de grandeur.

### Ce qu'il faut refaire — et quand

| Événement | À rejouer | Pourquoi |
|---|---|---|
| **Nouveau shell WSL** | `. $HOME/esp/esp-idf/export.sh` | l'environnement n'est pas persistant |
| **`wsl --shutdown` / reboot Windows** | `./tools/wsl-attach.sh` (les 4 étapes) | les modules noyau et l'attachement tombent |
| **Carte débranchée/rebranchée** | `./tools/wsl-attach.sh` | l'attachement tombe ; le `bind`, lui, survit |
| **Après un `flash`** | **rien** | mesuré : le flash **ne ré-énumère pas** l'USB, l'attachement tient |
| **Après un RESET de la puce** (bouton RESET, ou `--after watchdog-reset`) | `./tools/wsl-attach.sh` | mesuré : là, l'USB **se ré-énumère** et l'attachement **tombe** |
| **Après un `reboot` tapé dans la console de `firmware/desknode`** | `./tools/wsl-attach.sh` | mesuré en dn1-2 : `esp_restart()` compte comme un reset de puce — le port revient en `root:root` et toute lecture sort `[Errno 13] Permission denied` |
| **Après un reset par impulsion RTS** (`./tools/dn_console.py --reset`) | **rien** | ⚠️ mesuré le 2026-08-15 : **contre-exemple à la ligne du dessus.** Tous les resets de puce ne se valent pas — celui-ci donne bien `rst:0x15 (USB_UART_CHIP_RESET)`, mais l'USB **ne se ré-énumère pas** et l'attachement tient. C'est ce qui permet de capturer le bandeau de boot **depuis sa première ligne**, ce qu'un `flash` suivi d'une écoute rate toujours |

⚠️ **Ce sont deux resets différents, et c'est le piège de cette carte.** Le reset *logiciel* que
joue esptool en fin de flash (« Hard resetting via RTS pin ») **ne réinitialise pas** le périphérique
USB-Serial/JTAG : rien ne bouge côté hôte. Le reset *de la puce* (bouton, ou watchdog) coupe tout :
`usbipd list` repasse de `Attached` à `Shared`, `dmesg` affiche `usb 1-1: USB disconnect`, et
`/dev/ttyACM0` devient un nœud mort (`[Errno 19] No such device`).

**Parade si les resets sont fréquents** : `./tools/wsl-attach.sh --auto`. Mesuré : le périphérique
revient **tout seul en ~6 s**. Deux réserves, toutes deux gérées par le script :

- `--auto-attach` ne restaure **que le périphérique** — les droits retombent à `root:root
  crw-------`, donc il faut **rejouer le script** pour pouvoir relire le port ;
- il laisse un **processus Windows résident**. Le script en arrête les anciens avant d'en lancer un
  nouveau (ils ne s'empilent donc pas), et `./tools/wsl-attach.sh --stop-auto` les arrête tous.
  ⛔ **Ce `--stop-auto` est obligatoire avant de passer à la voie A** : un auto-attach vivant
  reprend la carte aussitôt après le `detach`, et `COM3` ne revient jamais côté Windows.

⚠️ `sudo modprobe` et `sudo chown` sont à rejouer **explicitement** : sur cette machine **systemd est
offline**, donc `/etc/modules-load.d/` et les règles `udev` sont **inopérants** — une règle
`/etc/udev/rules.d/*.rules` ne se déclencherait jamais. `tools/wsl-attach.sh` encapsule exactement
ces gestes, c'est sa seule raison d'être.

⚠️ **Ne pas coder `/dev/ttyACM0` en dur dans un outil.** L'index n'est pas garanti, et un nœud gardé
ouvert par un moniteur **survit** à la mort du périphérique (il répond alors `[Errno 19] No such
device`). Le script identifie le bon port par son identité en sysfs (`idVendor`/`idProduct`), qui
disparaît avec le périphérique — puis il **imprime le port** qu'il a trouvé.

### La carte est muette ? (le port s'ouvre mais rien n'en sort)

Symptôme : `/dev/ttyACM0` existe, s'ouvre sans erreur, et ne rend **0 octet**. Ce n'est pas un
problème de câble ni de baud : la carte est très probablement restée en **mode download**, où
l'application ne tourne pas.

> ⚠️ **Le second symptôme dépend du firmware flashé — corrigé en dn1-2.**
> Avec `hello-desknode`, « le rétroéclairage ne clignote plus » était un signe fiable.
> Avec `firmware/desknode`, le rétroéclairage est **allumé FIXE** en fonctionnement normal :
> « il ne clignote pas » n'y veut plus rien dire. Les critères valides pour `desknode` sont :
> **le port est muet** ET **l'écran n'affiche pas l'asset** (dalle noire ou figée).
> Le critère qui marche dans les deux cas reste **0 octet sur le port** — mais ⚠️ **PAS À
> N'IMPORTE QUELLE DURÉE**, et c'est le rejeu à froid du 2026-08-15 qui l'a trouvé.
>
> `firmware/desknode` n'imprime spontanément qu'une ligne de battement **toutes les 10 s**.
> **Cadence RE-VÉRIFIÉE INCHANGÉE par dn1-3** (2026-08-15) puis **par dn1-4**
> (2026-08-16, revue de code) : la ligne s'est enrichie des compteurs de flush, puis
> du tactile, mais le `vTaskDelay(10000)` de `desknode_main.c` n'a pas bougé — la
> durée d'écoute ci-dessous reste donc valable telle quelle. C'est vérifié à chaque
> story parce que changer cette cadence sans changer la recette rendrait la recette
> de survie fausse le jour où on en a besoin. ⚠️ L'AC9 de dn1-4 demandait cette
> re-vérification ; elle avait été faite pour le bloc « voie A » et **pas tracée
> ici** — c'est la revue qui l'a relevé.
> 🔴 **RE-VÉRIFIÉE INCHANGÉE par dn2-2** (2026-08-16, revue de code) : le
> `vTaskDelay(10000)` du battement de `desknode_main.c` n'a **pas** bougé, et dn2-2
> n'ajoute **aucune impression spontanée** — une trame acceptée est silencieuse
> (doctrine du REPL), seuls l'écho et l'invite passent sur le fil. La durée d'écoute
> ci-dessous reste donc valable telle quelle. ⚠️ Et l'histoire s'est répétée : dn2-2
> avait coché sa tâche AC9 sans poser cette trace — **deux stories de suite**, relevé
> par la revue les deux fois. C'est le mémo trois lignes plus haut qui aurait dû
> l'éviter.
> Écouter 6 s sur une carte parfaitement saine rend donc **0 octet** — et diagnostique une carte
> muette qui va très bien. C'est un faux positif qui envoie dérouler une recette de déblocage
> pour rien, sur une carte qu'on va inutilement remettre en mode download.
>
> **Le bon geste, celui qui SOLLICITE au lieu d'attendre :**
>
> ```bash
> python3 tools/dn_console.py "cfg"      # envoie \n, attend l'invite, échoue en 3 s si muette
> ```
>
> Il envoie une ligne vide, attend l'invite `desknode>` et diagnostique lui-même le mutisme. À
> défaut, écouter **au moins 12 s** — jamais moins qu'une période de battement.

⚠️ **Ce bloc est côté WSL, donc esptool 4.12.0** : l'exécutable s'appelle `esptool.py` (il n'y a
**pas** d'`esptool` tout court dans l'environnement de l'IDF) et ses options sont en **underscores**.
Ne pas y recopier la syntaxe en tirets de la voie A, qui est celle de la 5.3.1 côté Windows.

```bash
. $HOME/esp/esp-idf/export.sh    # sans lui, esptool.py n'est pas dans le PATH

# 1. Confirmer : si esptool dialogue SANS reset, la carte est dans le bootloader ROM.
esptool.py --chip esp32s3 -p /dev/ttyACM0 --before no_reset --after no_reset flash_id

# 2. La relancer. ⚠️ `--after hard_reset` NE SUFFIT PAS ici — il faut le watchdog.
esptool.py --chip esp32s3 -p /dev/ttyACM0 --after watchdog_reset flash_id

# 3. Ce reset ré-énumère l'USB : l'attachement usbipd est tombé, il faut le refaire.
cd ~/projects/desknode && ./tools/wsl-attach.sh
```

> ⚠️ **Troisième état, rencontré en dn2-2 : la PANIQUE HALTÉE** (une `assert` avec
> `CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y`). Le symptôme est PIRE que la carte muette :
> même l'étape 1 échoue en **`A serial exception error occurred: Write timeout`** —
> le CPU est halté, l'USB n'est plus servi, aucun octet ne part. La recette :
> `dn_console.py --reset` (impulsion RTS) peut suffire ; sinon **bouton RESET
> physique**, puis rejouer `./tools/wsl-attach.sh`. Vérifié le 2026-08-16.

Succès attendu — **et lui aussi dépend du firmware flashé**, comme le symptôme :

- avec **`hello-desknode`** : le rétroéclairage se remet à **clignoter**, le log reprend à `up 0 s` ;
- avec **`firmware/desknode`** : le rétroéclairage est **fixe** (il ne clignote pas, et ce n'est pas
  un défaut), l'**asset Living PCB réapparaît** à l'écran, le log reprend à `up 0 s` et **`aide`
  répond** dans le moniteur.

Le critère commun aux deux, et le seul qui ne trompe jamais : **le port n'est plus muet**.

### Voie A — build WSL, flash depuis Windows (secours, et cap à terme)

Elle n'installe **rien** sur le système et ne dépend ni de WSL-USB ni du réseau. C'est aussi la
direction visée à terme (fonctionner sans WSL).

**Étape 1 — dans WSL : construire seulement.**

```bash
. $HOME/esp/esp-idf/export.sh
cd ~/projects/desknode/firmware/desknode && idf.py build   # ou hello-desknode
```

**Étape 2 — dans WSL : rendre la carte à Windows.** Sans ce `detach`, `COM3` **n'existe pas** côté
Windows (exclusivité stricte, mesurée). Le BUSID est relu, jamais figé — il change si la carte est
branchée sur un autre port USB physique.

```bash
# Si un ./tools/wsl-attach.sh --auto tourne encore, il reprendrait la carte aussitôt :
./tools/wsl-attach.sh --stop-auto

USBIPD='C:\Program Files\usbipd-win\usbipd.exe'
busid=$(powershell.exe -NoProfile -Command "& '$USBIPD' list" | tr -d '\r' \
        | awk '/303a:1001/ {print $1; exit}')
powershell.exe -NoProfile -Command "& '$USBIPD' detach --busid $busid"
```

**Étape 3 — dans PowerShell : flasher.** Le port est `COM3` sur cette machine ; la première commande
le redonne s'il a changé.

Pour **`firmware/desknode`** (P1 et suite) — **QUATRE fichiers, pas trois** :

```powershell
[System.IO.Ports.SerialPort]::getportnames()

$py = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
$B  = '\\wsl.localhost\Ubuntu\home\nasbarok\projects\desknode\firmware\desknode\build'
#  ⚠️ dn5-3 (2026-09-04) — EXEMPLE : ce chemin UNC est celui de la machine de
#     l'auteur. Le vôtre s'obtient dans WSL par `wslpath -w ~/projects/desknode`.
#     ⛔ Il n'est PAS généralisé : c'est ce qu'il faut taper, et une recette
#     Windows qu'on généralise à l'aveugle ne marche plus.
& $py -m esptool --chip esp32s3 -p COM3 -b 460800 --before default-reset --after hard-reset `
      write-flash --flash-mode dio --flash-size detect --flash-freq 80m `
      0x0      "$B\bootloader\bootloader.bin" `
      0x8000   "$B\partition_table\partition-table.bin" `
      0x10000  "$B\desknode.bin" `
      0x410000 "$B\living_pcb_v0.bin"
```

> ### ⚠️ Le 4ᵉ fichier n'est pas optionnel
>
> `living_pcb_v0.bin` est l'**asset** de la partition `assets`. Côté WSL,
> `idf.py flash` l'écrit tout seul (via `esptool_py_flash_to_partition` dans le
> `CMakeLists.txt`) : **il n'apparaît nulle part dans la commande**, et c'est
> précisément pour ça qu'on l'oublie en passant à la voie A.

> **Vérifié inchangé par dn1-3 (2026-08-15), RE-VÉRIFIÉ par dn1-4 (2026-08-16), puis
> par dn2-2 (2026-08-16, revue de code).**
> Ce bloc a été relu contre le livrable des trois stories : la table de partitions
> n'a pas bougé (l'app fait toujours 4 MiB à `0x10000`, `assets` toujours 1 MiB à
> `0x410000`), et l'asset non plus (`tools/gen_living_pcb.py` n'a pas été touché).
> **Les quatre offsets restent exacts.** LVGL fait passer `desknode.bin` de
> 377 664 à ~740 400 o, le tactile + la navigation de dn1-4 à **790 736 o** (dont
> +7 936 o de correctifs de revue), et la liaison PC de dn2-2 à **796 240 o**
> (`dn_link` + `pc` + stubs `dn_wifi` + les correctifs de revue) — soit **81 % de la
> partition encore libre**. Ça tient largement — mais c'est bien le genre de croissance
> qui finirait par obliger à revoir la table, et c'est pour ça qu'on le note ici plutôt
> que de supposer que « ça n'a pas dû changer ».
>
> ⚠️ **dn1-4 a en revanche touché la NVS**, et il faut le savoir avant de dépanner :
> une valeur de `set bounce` trop grande, ou incompatible avec le build, peut
> mettre la carte en **boucle de panique avant le démarrage de la console** — plus
> aucune commande pour l'annuler. La sortie est d'effacer la seule partition NVS,
> sans toucher au reste :
>
> ```bash
> python3 -m esptool --chip esp32s3 --port /dev/ttyACM0 \
>     --before default_reset --after watchdog_reset erase_region 0x9000 0x6000
> ```
>
> 🔴 **CETTE COMMANDE ÉTAIT CASSÉE** (corrigée le 2026-08-16 par la revue de code
> dn1-4) : un `>` avait remplacé le `\` de continuation de ligne. Telle
> qu'écrite, bash **redirigeait la sortie vers un fichier nommé `--before`** et
> retirait l'argument de la ligne de commande — la NVS n'était pas effacée. Dans
> un bloc dont le seul objet est de sortir d'une boucle de panique, c'est le pire
> endroit possible pour une coquille.
>
> Elle rend les défauts du firmware au boot suivant, et l'asset survit (il vit à
> `0x410000`).
>
> ⚠️ **ELLE NE COUVRE QU'UN DES DEUX CHEMINS DE BRICK.** Effacer la NVS remet
> `bounce_px = 9600` et `draw_lines = 128`, qui sont désormais les **défauts du
> firmware** — ce qui est bon si la panique venait d'une valeur `set` fautive.
>
> 🔴 **CE PARAGRAPHE DISAIT `bounce_px = 7680`, ET IL EST FAUX DEPUIS `1adf259`**
> (2026-08-23) — relevé par la revue de code du **2026-08-24**. Le défaut est
> **9 600** (20 lignes) : avec `CONFIG_LCD_RGB_RESTART_IN_VSYNC=n`, l'arbitrage
> n'est plus « éviter la famine » mais « borner la SURFACE du dégât », et 9 600
> est le minimum sur les deux instruments à la fois (§20bis.6).
>
> 🔴 **ET ÇA CHANGE CE QUE CETTE PROCÉDURE GARANTIT.** Le repli de boot
> (`dn_display.c:359`) ne s'arme que si `bounce_px != défaut`. Effacer la NVS
> repose donc la carte sur **9 600, la seule valeur qui n'a PAS de filet** :
> si elle ne s'alloue pas, c'est panique → CPU halté → brick, sans repli.
> ⚠️ **Décision owner du 2026-08-24** : armer le repli sur `ESP_ERR_NO_MEM`
> quelle que soit l'égalité, vers un plancher codé en dur. **⛔ Non implémenté
> à la date de ce paragraphe.**
> ✅ **IMPLÉMENTÉ DEPUIS — `1db68bf`, le 2026-08-24.** ⛔ Cette ligne « non
> implémenté » n'est pas effacée : elle date le moment où on l'a écrite.
> `dn_display.c` descend désormais une **ÉCHELLE** `{ défaut,
> DN_BOUNCE_PX_PLANCHER = 4 800 }` et saute toute marche qui ne descend pas ⇒
> **il y a toujours une marche SOUS la valeur demandée, y compris quand elle EST
> le défaut** — qui était très exactement le trou. Et le repli ne s'arme que sur
> `ESP_ERR_NO_MEM` avéré : tout autre code remonte tel quel, **le réglage est
> CONSERVÉ**, et le log dit que ce n'est pas l'allocation.
>
> ⚠️ Et **`cfg reset` / l'effacement NVS sont le SEUL chemin** par lequel 9 600
> atteint une carte déjà configurée : `dn_bootcfg_load()` écrase le défaut
> compilé dès que la NVS porte une valeur admissible, et **7 680 en est une**.
> Une carte sur laquelle `set bounce 7680` a été tapé **garde 7 680 après
> reflash**, sans que rien ne le signale.
> ✅ **CORRIGÉ LE 2026-08-27 — ÇA SE SIGNALE MAINTENANT, ET EN DEUX TONS.**
> Le seuil d'alerte du boot était collé à `DN_DEFAULT_BOUNCE_PX` : le monter à
> 9 600 a fait tomber **7 680 dans une alerte de GLISSEMENT**, pour une valeur
> qui est seulement **sous-optimale**. Un seuil unique portait deux sens.
> ⇒ `DN_BOUNCE_PX_ALERTE = 7 680`, **découplé du défaut** : sous 7 680 le boot
> crie un **DÉFAUT** (l'image glisse, §18.9) ; entre 7 680 et le défaut il
> signale un **RÉGLAGE** (fonctionnel, sous l'optimum de §20bis.6).
>
> 🔴 **ET UN REPLI NE DÉTRUIT PLUS UN RÉGLAGE EN SILENCE — décision owner du
> 2026-08-27.** Quand le filet replie, le firmware réécrit la NVS (sinon le
> repli se rejoue à chaque boot et `cfg` ment) : **le réglage de l'opérateur est
> donc PERDU**, et jusqu'ici la seule trace était une ligne de log qui défile.
> ⇒ un **TÉMOIN DE REPLI** est désormais posé en NVS (valeur demandée, valeur
> retenue, nombre d'occurrences). **`cfg` nu le crie** tant qu'il est là,
> **`cfg repli`** en donne le détail, et **il SURVIT à `cfg reset`** —
> délibérément, puisque `cfg reset` est précisément ce qu'on tape pour sortir
> d'une valeur fautive. Seul **`cfg repli clear`** l'efface **du côté
> OPÉRATEUR**, et c'est un geste explicite.
> 🔴 **⛔ IL EXISTE UN TROISIÈME CHEMIN D'EFFACEMENT, ET IL N'EST PAS UN GESTE**
> — déclaré à la 3ᵉ revue de code, le 2026-08-27. `nvs_flash_init()` au boot
> rend `NO_FREE_PAGES` ou `NEW_VERSION_FOUND` quand la partition est saturée ou
> change de format, et le firmware appelle alors **`nvs_flash_erase()`**, qui
> emporte la partition **entière — témoin compris**. On ne peut pas le sauver ;
> le firmware **CRIE** désormais qu'il vient de le perdre, et dit qu'un
> `cfg repli` postérieur à ce message ne prouve rien.
> ⚠️ Le témoin date du 2026-08-27 : **les replis d'avant n'ont laissé
> qu'une ligne de log**, et « aucun repli noté » ne veut donc pas dire
> « aucun repli ».
> 🔴 **ET « aucun repli noté » N'EST PLUS IMPRIMÉ QUAND LA CLÉ N'A PAS PU ÊTRE
> LUE** (3ᵉ revue) : `dn_bootcfg_get_repli()` rendait `void`, donc une NVS qui
> ne s'ouvrait pas produisait exactement la même phrase qu'une NVS vide. La
> console distingue désormais **« ILLISIBLE »** de **« rien »**, et une valeur
> qu'elle n'a pas su relire s'affiche **« VALEUR NON RELUE »** — ⛔ plus
> « 0 px », qui est un `bounce_px` légal et se lisait comme une mesure.
> ⚠️ Le repli peut atterrir sur le **PLANCHER (4 800 px)**, une valeur au
> **défaut visible CONNU** — la console le dit explicitement dans ce cas.
>
> 🔴 **CE PARAGRAPHE DISAIT `bounce_px = 4800`, ET C'ÉTAIT DEVENU DANGEREUX**
> (revue de code du 2026-08-19). `dn4-6` a porté `DN_DEFAULT_BOUNCE_PX` à
> **7 680** (16 lignes) parce que **4 800 est l'état qui GLISSE** : sous trafic
> série 5 trames/s + repeint de case, l'image se décale d'un cran une fois par
> seconde (famine DMA, `hardware/…-affichage.md` §18.9). Une procédure de
> récupération qui renvoie l'opérateur vers 4 800 le sortirait d'un brick pour
> le remettre dans un défaut visible. ⚠️ Et une carte qui porte déjà un
> `set bounce 4800` en NVS **garde** cette valeur : le boot le **DIT** désormais
> (`ESP_LOGW`, ⛔ sans l'écraser — un réglage explicite n'est pas une erreur).
> Mais si elle vient d'un **`sdkconfig` périmé**, ça ne change rien : `sdkconfig`
> est gitignoré et ESP-IDF n'applique `sdkconfig.defaults` qu'aux symboles
> **absents**, donc un arbre d'avant dn1-4 garde `CONFIG_LCD_RGB_ISR_IRAM_SAFE=y`,
> que `bounce_px = 4800` transforme en *« Guru Meditation Error: Cache disabled
> but cached memory region accessed »* au boot. La sortie est alors :
>
> ```bash
> cd ~/projects/desknode/firmware/desknode
> rm sdkconfig && idf.py build && idf.py -p /dev/ttyACM0 flash
> ```
>
> 🔴 **ET UN SECOND INVARIANT, ATTRAPÉ PAR L'ŒIL DE L'OWNER** (dn4-6, §18.9) :
> `bounce_px` doit être un **nombre ENTIER DE LIGNES** (multiple de 480), pas
> seulement un diviseur des pixels d'une trame. `bounce_px = 6400` (13,33 lignes)
> était **accepté** et sortait l'image **décalée horizontalement** — constat
> verbatim : *« image décentrée sur la droite »*. ⛔ Un réglage refusé est une
> gêne ; un réglage **accepté** qui casse l'image en silence est un défaut.
> ⚠️ Les valeurs légales sont donc **douze** (plus le zéro) : 480, 960, 1920,
> 2400, 3840, 4800, **7680**, 9600, 15360, 19200, 30720, 38400 — et **aucune
> n'est admissible entre 4 800 et 7 680**, ce qui fait de 7 680 la plus petite
> valeur légitime qui tienne.
>
> ⚠️ **Le garde-fou qui manquait.** `set bounce 38400` — que l'aide de la commande
> présentait elle-même comme « le plafond, un diviseur utile » — ne démarrait plus
> depuis que `draw_lines` est passé à 128 : les deux clés mangent la même RAM
> interne et leurs bornes ne se parlaient pas. `set` vérifie désormais le **budget
> combiné** contre la RAM interne réellement libre, et refuse avant d'écrire.
>
> Sans lui, la partition est vierge (0xFF partout). Le firmware **le détecte et
> le dit** — au log (`partition « assets » VIERGE`) et **à l'écran** (panneau
> « ASSET ABSENT » sur la mire de cadrage) plutôt que d'afficher un écran blanc
> silencieux. Mais c'est une rustine : le bon geste est de flasher les 4.

**Redonner les offsets réels** si la table de partitions change — ne jamais les
retaper de mémoire :

```bash
cd ~/projects/desknode/firmware/desknode
idf.py partition-table          # imprime la table complète, offsets compris
```

`idf.py build` imprime de toute façon, en dernière ligne, la commande de flash
complète **avec tous les offsets** : c'est la source la plus fiable.

Pour **`firmware/hello-desknode`** (le témoin minimal) — trois fichiers, pas
d'asset, table de partitions par défaut :

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
$B  = '\\wsl.localhost\Ubuntu\home\nasbarok\projects\desknode\firmware\hello-desknode\build'
#  ⚠️ dn5-3 (2026-09-04) — EXEMPLE : chemin de la machine de l'auteur.
#     Le vôtre : `wslpath -w ~/projects/desknode`.
& $py -m esptool --chip esp32s3 -p COM3 -b 460800 --before default-reset --after hard-reset `
      write-flash --flash-mode dio --flash-size detect --flash-freq 80m `
      0x0     "$B\bootloader\bootloader.bin" `
      0x8000  "$B\partition_table\partition-table.bin" `
      0x10000 "$B\hello-desknode.bin"
```

⚠️ **`--flash-size detect` plutôt qu'une valeur en dur.** `--flash-size` réécrit l'en-tête du
bootloader **au moment du flash** : figer `2MB` ici annulerait en silence le correctif **apporté en
dn1-2** (la carte porte 16 MB, voir « **Écart 2 MB / 16 MB — SOLDÉ en dn1-2** » en fin de page).
`detect` lit la puce et suit.

Flash mesuré : **3,1 s**. Pour lire le log ensuite :

```powershell
& $py -m serial.tools.miniterm COM3 115200      # quitter : Ctrl+]
```

⚠️ **Trois pièges mesurés sur cette voie :**

1. **`@flash_args` est inutilisable ici, et pas pour la raison qu'on croit.** Le fichier
   `build/flash_args` généré par l'IDF contient `--flash_mode / --flash_freq / --flash_size` en
   **underscores** (syntaxe esptool 4.x) : l'esptool **5.3.1** de Windows les rejette. C'est *ça* qui
   impose de réécrire les arguments à la main ci-dessus. *(Séparément : `cmd.exe` refuse un
   répertoire courant UNC — « CMD ne prend pas les chemins UNC comme répertoires en cours » — mais
   **PowerShell l'accepte**, donc ce n'est pas le blocage. D'où les chemins UNC absolus, par
   commodité et non par contrainte.)*
2. **Exclusivité stricte** : tant que la carte est attachée à WSL, `COM3` **n'existe pas** côté
   Windows — et inversement. Il faut `detach` avant, `./tools/wsl-attach.sh` pour revenir.
3. **Un `--auto-attach` résident reprend la carte juste après le `detach`** : lancer
   `./tools/wsl-attach.sh --stop-auto` d'abord, sinon `COM3` n'apparaît jamais.

Ce que la voie A coûte au quotidien : la commande de flash est longue, le moniteur `miniterm` ne
**décode pas les backtraces** (adresses hexadécimales brutes, là où `idf.py monitor` les symbolise
via l'ELF), et les deux syntaxes esptool se ressemblent assez pour se confondre.

### Voies écartées — avec le symptôme relevé

| Voie | Verdict | Symptôme **observé** |
|---|---|---|
| **B** — `esp_rfc2217_server` sur Windows + `idf.py` sur WSL | ⛔ **flash impossible**, monitor OK | `A serial exception error occurred: Remote does not accept parameter change (RFC2217): dict_values([baudrate:REQUESTED, datasize:REQUESTED, parity:REQUESTED, stopsize:REQUESTED])` |

Détail de l'élimination de B, parce qu'une élimination sans preuve se retente :

- Le **transport marche** : pySerial nu (`serial_for_url(...)`) ouvre l'URL et lit le log de la carte
  (256 octets du firmware d'usine). Ce n'est donc **pas** un problème de réseau ni de pare-feu.
- Le **pare-feu Windows laisse passer** l'entrant depuis le sous-réseau WSL **sans élévation** —
  testé, `TCP_OK` sur le port 4000.
- Le changement de paramètres **après ouverture** marche aussi en pySerial nu (0,15 s). L'échec est
  donc propre à l'entrelacement reset + reconfiguration d'esptool, et **`--before usb-reset` ne le
  corrige pas**.
- Le serveur est **mono-client** et **ne se remet pas d'un client interrompu** : la connexion reste
  en `CloseWait` et tout client suivant reçoit `the port is busy or doesn't exist`. Il faut tuer et
  relancer le processus à chaque échec.
- Enfin, le client affiche `Device VID/PID identification is only supported on COM and absolute
  device paths` : à travers RFC2217, esptool **perd l'identification du chip** et ne peut pas
  choisir la bonne stratégie de reset.

⚠️ **Le serveur suggère lui-même une mauvaise adresse** (`rfc2217://10.14.0.2:4000`). L'hôte Windows
vu depuis WSL est la **passerelle par défaut**, à obtenir par `ip route | awk '/^default/{print $3}'`
→ **`192.168.224.1`**. Ce n'est **pas** le `nameserver` de `/etc/resolv.conf` (figé à `8.8.8.8` par
`generateResolvConf = false`), et il n'y a **pas** de `localhost` partagé (le mode *mirrored* exige
Windows 11 ; la tour est en Windows 10 19045).

### Faits matériels mesurés qui contredisent les recettes courantes

- **La carte est en USB natif ESP32-S3 Serial/JTAG (`303a:1001`), pas en pont CH343P.** Aucun
  périphérique `1A86` n'est présent. Aucun pilote à installer, ni côté Windows (`usbser` natif) ni
  côté Linux (`cdc-acm`). Le JTAG est disponible gratuitement sur l'interface `MI_02`.
- **Deux resets, deux comportements USB opposés — le fait le plus utile de cette page.**
  - *Reset logiciel* (fin de flash, « Hard resetting via RTS pin ») : **aucune ré-énumération**.
    Les 3 interfaces PnP restent `OK` de bout en bout et l'attachement `usbipd` **simple** survit à
    un flash complet. `--auto-attach` est **inutile** pour flasher.
  - *Reset de la puce* (**bouton RESET**, ou `esptool --after watchdog-reset`) : **ré-énumération
    complète**, mesurée à **1,4 s** côté Windows (les interfaces tombent, `COM3` disparaît, puis
    tout revient). Côté WSL, l'attachement `usbipd` **tombe**. C'est **là** que `--auto-attach`
    sert, et nulle part ailleurs.
- **Sortir du mode download demande le BON reset.** Une fois la carte passée en mode download
  (BOOT maintenu + RESET), `--after hard-reset` **ne la fait PAS repartir** : elle reste dans la ROM,
  le port série est totalement muet (0 octet), et même un `idf.py flash` complet n'y change rien —
  vérifié 3 fois. **`esptool.py --after watchdog_reset` la relance**, lui : l'application redémarre
  et le log reprend à `up 0 s`. Recette complète : § « La carte est muette ? ».
- **Ne transposer aucune recette de reset DTR/RTS type CH343/CP2102** : le reset passe par le
  mécanisme propre au USB-Serial/JTAG. Le log de boot le confirme : `rst:0x15 (USB_UART_CHIP_RESET)`.
- **Le mode download ne change PAS le VID:PID** : toujours `303A:1001` avec ses 3 interfaces, et
  `COM3` revient au même endroit. On ne peut donc **pas** détecter le mode download en regardant
  l'identité USB. Ce qui le trahit : le port devient muet, et `esptool.py --before no_reset` réussit
  à dialoguer **sans reset préalable** (ce qui n'arrive que dans le bootloader ou le stub).
- **Le log part sur DEUX chemins à la fois** : la console UART0 (`GPIO43`/`GPIO44`, le header) **et**
  l'USB-Serial/JTAG, via la console secondaire activée par défaut. Le header UART est donc une voie
  de secours réellement vivante si l'USB pose problème.
- `/dev/ttyACM*` arrive en **`root:root crw-------`** et l'utilisateur n'est pas dans `dialout` :
  sans `chown`/`chmod`, esptool sort `[Errno 13] Permission denied`.

### Écart 2 MB / 16 MB — **SOLDÉ en dn1-2**

Le bootloader annonçait `SPI Flash Size : 2MB` sur une carte qui en porte **16**. C'était la valeur
par défaut de l'IDF, non ajustée, et elle est corrigée dans `firmware/desknode` :
`CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y`. Relevé verbatim au bandeau de boot :

```
I (25) boot.esp32s3: SPI Flash Size : 16MB
```

`firmware/hello-desknode` reste **délibérément** sur le défaut 2 MB : c'est le témoin minimal, sa
configuration est figée.

⚠️ **Le piège reste entier, et il vaut pour TOUTE modification de config** : `sdkconfig.defaults`
n'est lu que pour **produire** `sdkconfig`. Un `sdkconfig` déjà présent (gitignoré, donc invisible à
`git status`) **l'emporte** en silence. Règle du dépôt : **tout changement de `sdkconfig.defaults`
se valide par `rm sdkconfig && idf.py build`, puis par la LECTURE du bandeau de boot** — jamais par
la relecture du fichier source.

### La configuration d'affichage — où elle vit

Le brochage vérifié, les timings, la configuration framebuffer retenue et tous les chiffres datés
sont dans **[`hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md`](hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md)**.
C'est **ce fichier** qui fait autorité — plus jamais besoin d'aller chercher un brochage dans un
wiki constructeur ou un dépôt communautaire. Sa **§0** donne la configuration de référence en un
tableau : c'est la seule chose à lire si on ne lit qu'une chose.

**Deux branches d'essai vivent à côté du `sdkconfig.defaults` livré**, chacune avec son mode
d'emploi en tête de fichier — elles sont versionnées pour que les mesures soient **rejouables**,
pas pour être activées par défaut :

| Fichier | Ce qu'il éprouve | Verdict |
|---|---|---|
| `sdkconfig.defaults.ac5-double-tampon` | `RESTART_IN_VSYNC=n`, sans quoi le recalage DMA est **inerte** et toute conclusion serait une non-mesure | ✅ le double tampon **fonctionne** (§4 ter) — mais n'apporte rien de mesuré aujourd'hui |
| `sdkconfig.defaults.xip-lecture-code` | XIP pour les **lectures** de code, le cas que la réfutation de dn1-2 excluait de son périmètre | ❌ réfuté ici aussi (§10.5, ligne 6) |

### L'asset Living PCB — ce qui est versionné, ce qui ne l'est pas

Règle tranchée en dn1-2 :

| Fichier | Versionné ? | Pourquoi |
|---|---|---|
| `tools/gen_living_pcb.py` | **oui** | c'est la SOURCE ; bibliothèque standard seulement, aucune dépendance à installer |
| `assets/mockups/living-pcb-v0.png` | **oui** | prévisualisation, pour voir l'asset **sans carte** |
| `build/living_pcb_v0.bin` | **non** | 614 400 o **générés** par le build, à graine égale identiques au bit près |

Un clone neuf n'a rien à faire : `idf.py build` régénère le `.bin`, `idf.py flash` l'écrit dans la
partition `assets`. Pour le regarder sans construire :

```bash
python3 tools/gen_living_pcb.py --out-png /tmp/apercu.png
```

## Les polices (dn3-1) — générées, vérifiées, VERSIONNÉES

Les libellés du dashboard perdaient leur accent **en silence** : les built-ins
`lv_font_montserrat_14/_28` sont générées avec `-r 0x20-0x7F,0xB0,0x2022` (relu dans l'en-tête de
leur `.c`), soit ASCII + le signe degré + la puce, **et rien d'autre**. LVGL ne dessine pas un
glyphe absent **et ne se plaint pas** — « RÉSEAU », « HUMIDITÉ », « AOÛT » y perdaient leur lettre.

`main/fonts/dn_font_<taille>.c` les remplacent : **ASCII + latin-1 complet + la puce +
les 60 `LV_SYMBOL_*` uniques + les icônes FontAwesome du dictionnaire `ICONES`**. Ce sont des
**sur-ensembles stricts** des built-ins.

🔴 **COMBIEN Y EN A-T-IL ? ⛔ CE README NE LE DIT PAS, ET C'EST LA RÈGLE** (`dn4-14-2`). La liste
vient de `TAILLES` / `TAILLES_VEILLE` dans `tools/gen_font_dn.py`, et le générateur en dérive **et**
les `LV_FONT_DECLARE`, **et** la macro `DN_FONT_LISTE(X)` de `dn_font.h`, que `dn_widget.c` développe
en registre et que la console imprime avec `widget largeur mur` ou une police inconnue.
⚠️ **`widget police` a longtemps annoncé « IL N'Y A QUE DEUX POLICES EMBARQUEES » dans un `printf`** —
une phrase que **rien ne re-vérifiait jamais**, et qui est devenue fausse à la première taille
ajoutée. Elle est remplacée par une **lecture du registre**.

🔴 **ET LA CHAÎNE AVAIT DEUX MOITIÉS CASSÉES, TOUTES DEUX TROUVÉES PAR `dn4-14-2` :**
- `ENTETE_MODELE` **récitait** `LV_FONT_DECLARE(dn_font_14)` et `(dn_font_28)` **en dur** ⇒ une
  taille ajoutée à `TAILLES` produisait un `.c` **jamais déclaré** ;
- `main/CMakeLists.txt` **énumérait** les `.c` à la main ⇒ ce même `.c` n'était **pas compilé**, et
  le seul symptôme était un `undefined reference` **au LINK**, c'est-à-dire *après* avoir payé la
  régénération complète.
⇒ Les deux sont réparées (déclarations **générées**, sources **découvertes** par
`file(GLOB … CONFIGURE_DEPENDS)`), et **la gate le vérifie** (`bloc_polices`) — y compris qu'aucun
`.c` **orphelin** ne traîne, pour qu'un ménage soit *payé* et pas seulement *annoncé*.

⛔ **AUCUN COMPTE N'EST ÉCRIT ICI, ET C'EST DÉLIBÉRÉ.** Le nombre d'icônes, combien sont déjà des
symboles amont, combien de codepoints neufs, et l'union `-r` finale sont **calculés à la génération**
et réinjectés dans `dn_font.h` : **les lire là**, ou dans la sortie de `python3 tools/gen_font_dn.py`.
🔴 **Cette phrase-ci en portait encore deux faux le 2026-08-29** : elle annonçait *« 10 icônes, dont
2 déjà des symboles »* alors qu'il y en avait **11 dont 3** (`cog` 0xF013, `tint` 0xF043 **et**
`save` 0xF0C7, ajouté par dn4-1 sans que cette ligne suive). Les *« 8 neufs / 68 »*, eux, étaient
justes — par coïncidence, les deux erreurs se compensant. C'est **exactement** la classe de défaut
que le générateur ferme depuis 2026-08-18 : *cinq endroits du dépôt en annonçaient trois valeurs
différentes, aucune juste*. **Un compte recopié dérive, et sa dérive est silencieuse.**
⚠️ **« 61 » est le nombre d'entrées BRUTES de la liste amont** : elle contient un **doublon** (61452
deux fois), d'où **60** uniques.

### Régénérer

```bash
# lv_font_conv est appelé PAR SON NOM par le générateur amont de LVGL.
# npx le fournit sans installation globale — il suffit d'un shim sur le PATH :
printf '#!/usr/bin/env bash\nexec npx --yes lv_font_conv@1.5.3 "$@"\n' > ~/.local/bin/lv_font_conv
chmod +x ~/.local/bin/lv_font_conv

python3 tools/gen_font_dn.py            # régénère les 2 .c + dn_font.h
python3 tools/gen_font_dn.py --mesure   # compare les plages et le kerning, ne génère rien
```

- **Mesuré depuis ce WSL le 2026-08-17** : `node v24.14.0`, `npm 11.9.0`,
  `npx --yes lv_font_conv --version` → **1.5.3** (rc=0). **Re-mesuré le 2026-08-29** (dn4-14) :
  toujours **1.5.3**, rc = 0. ⛔ **Ne pas re-supposer que la chaîne est morte** : le ledger l'a
  reportée pendant des semaines sur *« npm + réseau, absents du tableau des versions figées »*,
  et une ligne suffisait à le vérifier.
- 🔴 **dn4-14 : le générateur fait désormais un PRÉ-VOL.** `lv_font_conv` absent du PATH sortait en
  `FileNotFoundError` **nu**, **après** avoir lu la liste amont et construit sa ligne de commande.
  C'est le **premier échec attendu d'un poste neuf**. Il nomme maintenant la dépendance et donne la
  recette ci-dessus. ⚠️ `--entete-seule` passe **avant** ce contrôle, délibérément : c'est le chemin
  qui n'a besoin de rien.
- 🎯 **`--entete-seule` : la porte gardée, et quand elle est légitime.** Ajouter une icône dont le
  codepoint est **déjà** dans les `.c` (parce que l'amont l'injecte avec ses symboles) ne change
  **rien** aux polices. La commande relit les `.c` avec `codepoints_du_c()` et **REFUSE** si un
  codepoint manque. **Mesuré sur `home` U+F015 le 2026-08-29** : les quatre `sha256sum` **identiques
  avant/après**, et **delta de binaire = 0 octet**. ⛔ **Le ratio d'icônes qu'elle imprime n'est pas
  recopié ici** — il se lit dans sa sortie, comme tous les autres comptes de ce paragraphe.
  ⛔ **Elle ne paie JAMAIS un ménage** : elle vérifie que chaque codepoint d'`ICONES` est **porté**.
  Un retrait exige `python3 tools/gen_font_dn.py`, puis `codepoints_du_c()` pour le prouver.
  🔴 **DEPUIS LA REVUE DU 2026-08-29, ELLE REFUSE AUSSI LE SURPLUS** — et ça change ce qui était
  écrit ici. La version d'avant ne regardait que la **présence** : retirer une entrée d'`ICONES`
  la faisait **passer sans toucher un octet**, et `dn_font.h` recevait alors des compteurs
  **diminués** pendant que les `.c` portaient toujours les anciens glyphes. Le raccourci publiait
  donc comme *calculés* des nombres faux. Elle compare désormais les codepoints FontAwesome
  **portés** par les `.c` à ceux qu'`ICONES` demande (amont soustrait) et **nomme les surnuméraires**
  — vérifié le 2026-08-29 en sortant `cube` U+F1B2 et `vr-cardboard` U+F729 : **refus, rc = 1**.
- Le générateur **lit** les codepoints de symboles dans
  `managed_components/lvgl__lvgl/scripts/built_in_font/built_in_font_gen.py` — il ne les recopie
  **jamais**. Une liste recopiée dérive, et sa dérive est **silencieuse** : `LV_SYMBOL_LIST` (bandeau
  MENU) et `LV_SYMBOL_LEFT` (chevron de retour) disparaîtraient sans un mot.
- Il **relit** ensuite le `.c` produit et **échoue bruyamment** si un symbole, une icône ou un témoin
  accentué manque. Une génération qui « réussit » sans ses glyphes est l'étiquette qui ment.
  🔴 **Et cette garde a été aveugle une fois** (corrigée le 2026-08-18, revue de code) : elle testait
  les **bornes** des cmaps au lieu de leur **contenu**, or la cmap qui porte les symboles est de type
  **SPARSE** — elle borne `8226 → 63650` en n'y portant que **69** codepoints. Tout `syms` passait
  donc quoi qu'il arrive, **`fan` (0xF863) compris** — le glyphe absent que ce README documente.
  `codepoints_du_c()` décode maintenant `unicode_list_N` (offsets depuis `range_start`). **Contrôlé
  après correctif** : `fan` → absent, `Ā` (hors latin-1) → absent, les 68 + les témoins → présents,
  **260 codepoints réellement portés** par police.
- ⚠️ **Deux témoins ne viennent PAS de l'amont, et c'est délibéré** : `LV_SYMBOL_LIST` (U+F00B) et
  `LV_SYMBOL_LEFT` (U+F053) sont écrits **en dur** dans `SYMBOLES_TEMOINS`. Un témoin tiré de la
  chose qu'il témoigne n'est pas un témoin — sans eux, un retrait amont serait retiré de la police
  **et** de la liste de contrôle, et le script annoncerait un succès.
- `--mesure` **vérifie aussi** chaque police qu'il chiffre (correctif du 2026-08-18 : il ne
  vérifiait rien, alors que c'est lui qui a produit le tableau ayant tranché **W5**).
- `dn_font.h` (les macros `DN_ICONE_*`) est **généré depuis le même dictionnaire** que la police :
  une macro **ne peut pas** pointer un codepoint que la police n'aurait pas.
- ⚠️ `managed_components/` est **gitignoré mais régénéré** par `idf.py` depuis `main/idf_component.yml`,
  où `lvgl/lvgl: "==9.5.0"` est épinglé. Sans lui, ni générateur, ni TTF, ni WOFF :
  `idf.py reconfigure` d'abord.
- ⚠️ **`--no-compress` est obligatoire** : `CONFIG_LV_USE_FONT_COMPRESSED` n'est **pas** activé dans
  ce build, et la compression coûte de toute façon ~30 % de temps de rendu.

### Pourquoi les `.c` sont VERSIONNÉS et non produits au build

`lv_font_conv` est une dépendance **npm**, absente du tableau des versions figées : un `idf.py build`
sur un clone neuf **sans réseau** échouerait. Ce n'est **pas** le même arbitrage que l'asset Living
PCB, dont le générateur (`gen_living_pcb.py`) est en **stdlib Python pure** — celui-là peut se
regénérer partout, hors ligne.

### Ce que ça coûte, mesuré

Binaire **832 720 → 885 232 o** (+52 512, +6,3 %), partition `factory` libre à **79 %**.
Détail, tableau des plages et les **deux erreurs de la story corrigées par la mesure** :
`hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md` **§15.3**.

### Les icônes, et celle qui manque

🔴 **`0xF863` (`fan`) est ABSENT** du `FontAwesome5-Solid+Brands+Regular.woff` du dépôt : il est
arrivé en **FontAwesome 5.11** et le fichier embarqué est antérieur. **Vérifié en le convertissant
seul**, pas déduit d'une table. Quatre substituts sont embarqués **ensemble** et commutables à chaud
(`widget icone`) ; **`cog` a été retenu** par constat owner — et il est **gratuit**, `0xF013` étant
déjà l'un des 60 symboles injectés par le générateur amont.
⚠️ **`main/fonts/dn_font.h` annonçait `sync-alt` jusqu'au 2026-08-18**, alors que `k_desc[]` pose
`DN_ICONE_COG`. Le `.h` étant **généré**, la phrase revenait à chaque régénération : le correctif est
dans `tools/gen_font_dn.py` (`ENTETE_MODELE`), pas dans le `.h`.

⛔ **Aucun asset image pour les icônes** : `dn_asset` ne gère qu'**un** asset, et la partition
`assets` n'a que ~434 Ko libres — que **dn3-3 réclame déjà**.

**Licences**, **lues** dans les fichiers, pas récitées
(`managed_components/lvgl__lvgl/scripts/built_in_font/font_license/`) :
- `Montserrat/OFL.txt` — *« This Font Software is licensed under the SIL Open Font License,
  Version 1.1 »*, © 2011 The Montserrat Project Authors.
- `FontAwesome5/LICENSE.txt` — Font Awesome Free, © Fonticons Inc. : **icônes CC BY 4.0**,
  **fontes SIL OFL 1.1**, code MIT. Nous n'embarquons que des **glyphes** ⇒ CC BY 4.0 + OFL 1.1.

⚠️ Ces licences vivent dans `managed_components/`, qui est **gitignoré**. Elles sont donc
**absentes d'un clone** tant que `idf.py reconfigure` n'a pas tourné — c'est un fait à connaître
avant toute distribution du binaire, pas un détail d'attribution.

## L'agent PC (dn2-2 → dn4-1 → dn4-8) — CINQ métriques de la tour, à ~1 Hz, par l'USB série

Un seul fichier : `agent/dn_agent.py`. Il tourne sur le **Python Windows 3.13** de la
tour, **sans élévation, sans driver, sans .NET**.
⛔ **Et c'est une FRONTIÈRE, pas une préférence (D8)** : le Ring0 / LibreHardwareMonitor —
donc la **température CPU** et les **RPM ventilateurs** — sort du périmètre V1. C'est ce qui
a fait de la 6ᵉ case un **DISQUE** et de la 2ᵉ grandeur du CPU une **fréquence**.

🔴 **AMENDÉ LE 2026-08-21 PAR D13, ⛔ PAS EFFACÉ — ET LA MOITIÉ QUI COMPTE RESTE VRAIE.**
`LibreHardwareMonitor` **rentre** dans le périmètre V1, **en service permanent sur la tour**
(tâche planifiée `RunLevel = Highest` + driver noyau signé `PawnIO 2.2.0`, **prouvée par un
redémarrage réel**), et l'agent **LIT** son serveur web local.
⛔ **L'agent, lui, n'a toujours ni élévation, ni driver, ni .NET — il ne fait AUCUN Ring0.
C'est exactement ce qui rend la chose acceptable.**
⇒ Le fil porte désormais **`cpu` à QUATRE** (`%` · `GHz` · `c.max` · **`°C`**) et **`disk` à
QUATRE** (`Mo/s` · **extraction moyenne** · **ventilo CPU** · **ventilo boîtier**).
⚠️ **Ce que les CASES affichent ne change PAS ici** — c'est `dn4-9`, et la grille reste à SIX.
⚠️ **ET LE COÛT EST ASSUMÉ, ⛔ PAS OUBLIÉ** : ces **quatre** grandeurs ne marchent que sur une
machine où LHM est installé, élevé et permanent. Le critère owner de D8 (*« générique et libre
de droits, réutilisable sur toutes les configs »*) **ne tient plus pour elles**. Les **onze
autres, si**. ⇒ `sprint-change-proposal-2026-08-21.md` (D13) et `-21b.md`.

### 🔴 ORDRE DE DÉPLOIEMENT : **le firmware D'ABORD, l'agent ENSUITE**

⛔ **Ce n'est pas une préférence de confort — l'ordre inverse fait DISPARAÎTRE deux cases.**
Décision owner du **2026-08-21** (revue de code `dn4-8`) : on **documente l'ordre**, ⛔ on ne pose
**pas** de garde de version — ce serait un changement de protocole, donc une story à part.

L'agent vit sur la tour et le firmware se flashe séparément : **rien ne les synchronise**.
Or `dn_link.c` **rejette la trame ENTIÈRE** si elle porte plus de valeurs que la métrique n'en
publie (`nv > k_metriques[].n_grandeurs` ⇒ `rejets_format`) — doctrine **délibérée** : *« plus de
valeurs que la métrique n'en PUBLIE est un défaut de format, ⛔ pas une donnée en trop qu'on
jetterait en silence »*.

⇒ **Agent `dn4-8` + firmware `dn4-6`** = les trames `cpu` (4 valeurs) et `disk` (4 valeurs) sont
rejetées **en entier** : on ne perd pas seulement la °C et les tr/min, **on perd aussi le `%` CPU
et le `Mo/s`**.

🔴 **ET LE SYMPTÔME DÉPEND DE LHM, CE QUI LE REND DÉROUTANT :**

| État de LHM | Ce que l'agent émet | Ce que la carte affiche |
|---|---|---|
| **arrêté** | `cpu` à 3, `disk` à 1 (les `None` de queue sont **tronqués**) | ✅ tout va bien |
| **démarré** | `cpu` à 4, `disk` à 4 | 🔴 **deux cases sur cinq passent à « -- »** |

⚠️ **Donc : « ça marchait, j'ai lancé LHM, deux cases sont mortes » ⇒ le firmware est en retard sur
l'agent.** ⛔ Ne pas chercher du côté de LHM ni du câble : **reflasher**.
⛔ Et rien dans la trame ne déclare « je porte plus que tu ne sais » — c'est précisément pourquoi
l'ordre doit être **écrit**.


### Les cinq métriques et leurs sources (dn4-1, mesurées le 2026-08-18)

⚠️ **AMENDÉ LE 2026-08-22 (dn4-9), ⛔ PAS RÉÉCRIT.** Ce tableau décrit ce que
**la CASE** affiche, et il valait pour dn4-1. Depuis dn4-9 il faut lire DEUX
comptes par case : ce que la **case** dessine, et ce que le **détail** montre.
La ligne `DISQUE` portait encore « grandeur 1 = — » alors que le fil porte
**quatre** grandeurs depuis dn4-8 ; la case en montre désormais **deux** et le
détail **quatre**. `CPU` montre `[%, GHz, °C]` — ⛔ les grandeurs **0, 1 et 3**,
⛔ pas les trois premières. Le tableau complet est publié **au boot**
(`k_desc[…] : case N […] · detail N […]`) et par `widget`.

| case | grandeur 0 | grandeur 1 | source | droits | coût mesuré |
|---|---|---|---|---|---|
| **CPU** | % | **GHz** | `psutil.cpu_percent` + `cpu_freq` | aucun | ~0 ms/tir |
| **GPU** | % | **°C** | **`atiadlxx.dll` / `ADL2_New_QueryPMLogData_Get`** (ctypes) | aucun | **0,5 ms/tir** |
| **RAM** | % *(+ jauge)* | Go **totaux** | `psutil.virtual_memory` | aucun | 7,8 ms/tir |
| **RÉSEAU** | Mb/s ↓ | Mb/s ↑ | `psutil.net_io_counters` (**deltas**) | aucun | 6,8 ms/tir |
| **DISQUE** | **Mo/s** | **`tr/min` extraction** *(dn4-9)* | `psutil.disk_io_counters` (**deltas**) + **LHM** `fan/0`+`fan/4` | aucun / **LHM requis** | ~0 ms/tir |

🔴 **CE QUE dn4-8 A AJOUTÉ AU FIL (2026-08-21) — ⛔ pas à l'écran :**

| métrique | grandeur ajoutée | `SensorId` LHM | droits | provenance du mapping |
|---|---|---|---|---|
| **CPU** | **`°C`** (index **3**) | `/intelcpu/0/temperature/10` | 🔴 **LHM requis** | **MESURÉ** — « CPU Package », recoupé par le Super I/O `/lpc/nct6792d/0/temperature/0` (40,5 contre 41,0 : **1,2 %**). ⚠️ instantané **n = 1** |
| **DISQUE** | **extraction moyenne** | `fan/0` + `fan/4` | 🔴 **LHM requis** | **MESURÉ** — jointure BIOS↔LHM par RPM, 2026-08-21 |
| **DISQUE** | **ventilo CPU** | `/lpc/nct6792d/0/fan/1` | 🔴 **LHM requis** | **MESURÉ** — idem (`CPU_FAN1`, le ventirad Noctua) |
| **DISQUE** | **ventilo boîtier** | `/lpc/nct6792d/0/fan/2` | 🔴 **LHM requis** | **MESURÉ** — idem. ⚠️ **UN tachy pour DEUX ventilateurs chaînés** |

⚠️ **LA °C EST EN INDEX 3, ⛔ PAS EN INDEX 2, ET CE N'EST PAS UN DÉTAIL** : l'ordre du fil ne
bouge pas sur 0..2, donc le **témoin de non-régression v3** (l'agent de `dn4-6`, non modifié)
**reste valide**. En index 2, son `c.max` (350 dixièmes de %) s'afficherait **« 35,0 degC »**,
et le plafond passant de 1000 à 1500, ⛔ **`rejets_bornes` ne broncherait même pas.**
🔴 **Le témoin fabriquerait lui-même le chiffre faux et plausible qu'il existe pour exclure.**

⛔ **ET UN VENTILATEUR NE SERA JAMAIS PUBLIABLE** : le **200 mm de façade** n'a **pas de fil
tachymétrique** — `0 RPM` **DANS LE BIOS AUSSI**. **Il tourne, il ne le dit pas.** ⇒ c'est du
**matériel**, ⛔ pas une limite logicielle, et aucune version future n'y changera rien.
⚠️ **L'ordre naïf des canaux était FAUX sur les deux premiers** : `fan/0` est `CPU_FAN2`, ⛔ pas
`CPU_FAN1`. Le coder naïvement aurait affiché « CPU » sur l'extraction haute. **C'est la capture
BIOS de l'owner qui l'a attrapé**, ⛔ pas le raisonnement.

🔴 **NVML est INAPPLICABLE sur cette tour** : `Win32_VideoController` rend **un seul**
contrôleur, une **AMD Radeon RX 6800 XT**, et `pynvml` n'est pas installé. Le repli
pré-autorisé (« GPU en % seul ») **n'a pas servi** : ADL rend le % **et** la °C en un appel.
⛔ **Le candidat WMI `GPUEngine` a été ÉCARTÉ PAR LA MESURE** : 720 instances, **342 ms de CPU
par tir** (30,8 % d'un cœur) — **657× plus cher qu'ADL**, au-dessus du critère « < 1 % » du
brief à lui seul, et incapable de tenir 1 Hz.
⚠️ **Le mapping des capteurs PMLog se VÉRIFIE, il ne se croit pas** : l'agent exige que les
mêmes indices rendent une **largeur de lien PCIe légale** et une **horloge mémoire plausible**,
et **refuse de servir** sinon — le témoin est rejoué **à chaque tir**, pas seulement à
l'ouverture. Un mapping décalé publierait une tension comme une température.
🔴 **CE QUE CE TÉMOIN NE PROUVE PAS** (corrigé en revue le 2026-08-18 — ce paragraphe, la
docstring de l'agent et `liaison-pc.md` §13.5 annonçaient tous trois « exige `BUS_LANES = 16`
et `CLK_MEMCLK ≈ 2000 MHz` », ce que le code n'a jamais fait **et a raison de ne pas faire** :
une RX 6000 **abaisserait son lien PCIe au repos** — ⚠️ **HYPOTHÈSE NON MESURÉE**, et la séance
du 2026-08-18 ne la confirme pas : le témoin a lu **`BUS_LANES = 16` · `CLK_MEMCLK = 1988 MHz`**,
soit exactement ce que les quatre textes annonçaient. ⇒ **Ce qui est acquis** : le code vérifie une
plage, et les textes doivent dire ce que le code fait. ⇒ **Ce qui reste ouvert** : faut-il resserrer ?
Il faudrait relever `BUS_LANES` **au repos prolongé**, ce qui n'a pas été fait). C'est une **cohérence de plage**, pas la preuve du bon capteur.
✅ **Ce qui a prouvé le capteur, c'est AC10** : **47 °C à l'écran contre 47 °C au Gestionnaire
des tâches**, lus **en même temps**. Deux instruments, un seul répond à la question.
⚠️ **`ram` porte le TOTAL, pas l'utilisé** : le firmware compose « 22,7 / 34,2 Go » depuis le
pourcentage. Deux nombres échantillonnés séparément finiraient par afficher **deux vérités
contradictoires dans le même rectangle**.
⛔ **`errin`/`errout`/`dropin`/`dropout` ne sont JAMAIS publiés** : cette tour rend
`dropin = 113 558 935 299 979`. On regarde un compteur avant de le publier.

- **Sources : `psutil` + `ctypes`/`atiadlxx.dll`** — ⚠️ **dn4-1 n'ajoute AUCUNE dépendance** : le GPU passe par `ctypes` (stdlib) et une DLL installée par le pilote AMD. Détail du % CPU ⤵
- **Source du % CPU : `psutil`** (`pip install --user psutil` — la SEULE dépendance
  posée par dn2-2 ; `pyserial` et `websockets` étaient déjà là). Ce sont les mêmes
  compteurs noyau que le Gestionnaire des tâches. Raisons chiffrées de l'élimination
  de `Get-Counter` (noms localisés FR) et de WMI (spawn 4,2 s) : en-tête de l'agent.
- **Lancement** (PowerShell, la carte étant **détachée** de WSL — voir plus bas) :

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
& $py \\wsl.localhost\Ubuntu\home\nasbarok\projects\desknode\agent\dn_agent.py --serie COM3
#  ⚠️ dn5-3 (2026-09-04) — EXEMPLE : chemin de la machine de l'auteur.
#     Le vôtre : `wslpath -w ~/projects/desknode`.
#  --temoin     imprime son propre coût CPU toutes les 10 s
#  --duree 60   s'arrête proprement après 60 s (le témoin « arrêt propre » d'AC7)
#  --stdout     trames à l'écran, sans carte (débogage)
#  --stop-si F  s'arrête proprement dès que le FICHIER F apparaît — le seul
#               arrêt propre possible sans console (agent détaché, dn4-17)
#  --tracer-console F   capture BRUTE et HORODATÉE de tout ce que l'agent draine
#               sur le fil (⛔ QU'AVEC --serie). C'est l'instrument de dn4-18 :
#               c'est lui qui a répondu « le bandeau de boot atteint-il l'agent,
#               oui ou non ». ⚠️ MESURÉ sur les captures livrées : **447 à
#               530 o/s, soit 1,6 à 1,9 Mo/h** (35 à 45 % du fichier sont les
#               en-têtes horodatés, écrits à chaque drain, ~5 fois par seconde).
#               ⛔ NE PAS le laisser armé sur un soak : 7 jours ≈ 270 à 320 Mo,
#               sans aucune rotation.
#               ⚠️ Il doit être armé AVANT l'extinction de la tour si on veut
#               capturer la réponse `rtc` ENTIÈRE au rallumage : la tâche au
#               logon ne porte pas cette option.
#  --lhm HOTE:PORT      ou joindre LibreHardwareMonitor (défaut 127.0.0.1:8085)
#                       ⚠️ EXERCE les chemins d'échec ; ⛔ ne REMPLACE pas AC8, qui
#                          exige le VRAI service coupé
#  --lhm-timeout S      plafond de la lecture LHM (défaut 0,60 s)
#                       ⚠️ CE README ANNONÇAIT **0,40 s** JUSQU'AU 2026-08-22
#                          (relevé au cadrage de dn4-9) : `LHM_TIMEOUT_S` vaut
#                          **0.6** depuis la mesure de dn4-8, et un README qui
#                          publie l'ancien défaut fait poser le mauvais budget
#                          dans une campagne.
#                       🔴 C'est un BUDGET pour la lecture ENTIÈRE, ⛔ pas par tentative :
#                          `_get()` retente UNE fois, et un plafond par tentative
#                          doublait le pire cas (802 ms MESURÉES pour 400 posées)
#  --ws URL     branche B (WiFi WebSocket) — ÉCARTÉE par la fourche, gardée pour une
#               re-mesure ; sans firmware branche B en face, elle ne sert à rien
```

- ⚠️ **CES DEUX CHIFFRES NE SONT PAS CEUX DE L'AGENT LIVRÉ** (annotation de revue
  2026-08-19). La séance post-revue mesure l'agent tel qu'il est livré à
  **2,421 % d'un cœur = 0,1513 % machine** (`hardware/…-affichage.md` §17.9), soit
  **+0,26 pt NON EXPLIQUÉ** par rapport aux 2,161 % ci-dessous. L'écart est au
  ledger. ⛔ Les chiffres ci-dessous restent lisibles — ils datent leur firmware —
  mais **ne pas les citer comme le coût de l'agent courant**.
- 🔴 **Coût propre, dn4-1, SUR LE TRANSPORT RÉELLEMENT UTILISÉ (`COM3`, série) :
  2,161 % d'un cœur = 0,135 % machine** — mesuré en séance carte le 2026-08-18,
  agent réel sur le port, **3 000 trames à 5,00/s, 0 erreur · 0 recalage · 0 écrêtage**.
  🔴 **+0,63 pt contre `--stdout` : LE PORT SÉRIE A UN COÛT PROPRE, et il n'existait
  dans AUCUN budget.** ⛔ Ne pas comparer un chiffre `--stdout` à un chiffre `COM3`.
- **Coût propre, dn4-1, sur `--stdout` (témoin, PAS le transport) : 1,528 % d'un cœur
  = 0,0955 % machine** —
  **2,750 s CPU / 180,0 s** de temps mural, 900 trames, **0 écrêtage, 0 recalage**.
  L'augmentation est **attribuée** : 7,8 ms (`virtual_memory`) + 6,8 ms (`net_io_counters`)
  + 0,5 ms (ADL) ≈ **15,1 ms/s = 1,51 % d'un cœur**, soit 1,51 des 1,528 points expliqués.
  🔴 **Ce n'est PAS le GPU qui coûte** — c'est le poste que le cadrage soupçonnait, et il pèse
  **3 %** du total. 🔴 **QUELLE LECTURE DE « < 1 % » ? LA QUESTION EST OUVERTE, ET ELLE
  EST AU LEDGER** (décision owner du 2026-08-18, revue de code) : sur le transport
  retenu, **0,135 % machine** ✅ contre **2,161 % d'un cœur** ❌. ⛔ **Le critère n°4
  du brief n'est donc PAS coché** — ni infirmé. Les deux lectures sont publiées,
  comme dn2-2 le faisait déjà ; ce qui manque, c'est **l'unité que le brief vise**,
  et c'est à écrire dans le brief. ⚠️ D3 affirme que ce critère « se coche ici » :
  tant que l'unité n'est pas énoncée, cette affirmation est sans objet.
- **Coût propre en dn2-2 (1 métrique) : 0,35 % d'un cœur** (0,022 % machine) — 0,141 s CPU pour
  40 s de temps mural, 16 cœurs logiques. ⚠️ **La méthode fait partie du chiffre** : c'est
  le **cumul** `psutil.Process().cpu_times()` rapporté au temps mural, **pas** une fenêtre
  glissante `cpu_percent()` — une fenêtre de 10 s a une résolution de ~0,16 pt (ticks de
  15,6 ms) et ne PEUT PAS voir un coût de cet ordre. Le cumul, lui, affine avec la durée
  (le démarrage domine, la tendance est décroissante). Critère brief « < 1 % » :
  largement dedans, **première mesure**, soldée en dn4-1. *(Ce README et le tracker
  annonçaient 0,23 % sans méthode ni source — corrigé par la revue du 2026-08-16 :
  c'est le chiffre dont la méthode est écrite qui fait foi.)*
- **Le bilan de fin sort dans TOUS les cas, Ctrl+C compris** : trames émises, erreurs
  d'envoi, **recalages de cadence**, bruit d'écho console, et les **refus signalés par le
  firmware** — « n trames émises » ne prouve que n écritures, pas n acceptations.
  ⚠️ **Corrigé par la revue de code du 2026-08-26** : depuis `dn4-18` l'agent envoie aussi
  des commandes console (`rtc`, `rtc set`), et le marqueur `non-zero error code` que ce
  compteur ramasse est rendu par le REPL pour **toute** commande sortie non nulle — ⛔ pas
  seulement pour une trame `pc`. Le bilan annonçait donc « N **trame(s)** REFUSÉE(S) »
  quand **zéro trame** l'avait été. Il publie désormais **« N commande(s) console
  refusée(s) »** et **sa décomposition** (`dont N poses d'horloge ⇒ M imputables aux
  trames`), exacte parce que `rtc` nu sort toujours à 0 et que chaque pose refusée est
  comptée à part, sur le **verdict ancré de la carte** et non sur le marqueur du REPL.

- **Protocole** : `$DN,3,<seq>,<t_ms>,<metrique>,<v1>[,<v2>[,<v3>[,<v4>]]]*<CK>` — ⛔ **l'autorité est `main/dn_link.h`**, ce README renvoie et ne redéfinit pas. ⚠️ **Corrigé par la revue de code du 2026-08-19** : cette ligne publiait encore la **v2** alors que `dn4-6` livre `DN_LINK_PROTO_VERSION = 3` (`NB_CHAMPS_MAX` 7 → 9, `DN_LINK_LIGNE_MAX` 63 → **71**), en extension **ADDITIVE**. Un champ VIDE en position interne = « cette grandeur-là, je ne l'ai pas » (W10) ; un champ vide en **position 0** est refusé. **v1 reste acceptée** (`$DN,1,…,cpu,…`, 6 champs), et l'agent de dn2-2 **non modifié** fait toujours vivre la case CPU : c'est le témoin de non-régression, et il passe **8/8 avec `rejets_version` = 0**. Envoyé en `pc $DN,…` au
  REPL — l'agent parle le dialecte de la console. Autorité : `dn_link.h` et
  `hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md` §12.5.
- **Case CPU du dashboard** : vivante quand la liaison l'est ; **« -- » grisé** dès
  3 s sans trame valide (une valeur figée serait un mensonge d'interface) ; reprise
  sans reboot en ≤ 2 s quand l'agent revient.

### ⚠️ Le port est EXCLUSIF : agent ⇄ boucle de flash — **UN SEUL GESTE** (`dn4-17`)

L'agent (Windows, `COM3`) et la boucle WSL (flash + `dn_console.py`) ne coexistent
JAMAIS — exclusivité usbipd + TIOCEXCL, mesurée.

🔴 **ÉTAPE 0 — TUER LES VEILLEURS `--auto-attach`, AVANT TOUT LE RESTE.** Sinon ils
re-attachent la carte à WSL en quelques secondes après le detach, et l'agent trouve un
COM3 fantôme (`FileNotFoundError`) pendant que l'état usbipd se bloque en « Attached »
orphelin. *(Ce piège a coûté une heure en session dn2-2 ; l'avertissement était écrit
APRÈS le bloc de commandes, soit dans l'ordre inverse de l'exécution — corrigé par la
revue du 2026-08-16.)*
✅ **DEPUIS `dn4-17`, C'EST L'OUTIL QUI LE FAIT** — des DEUX côtés, à chaque appel. C'est
exactement pourquoi il existe : le rituel manuel **échouait**, et le ledger l'avait
consigné (`deferred-work.md:1348`).
🔴 **⚠️ MAIS LE COMPTE DE VEILLEURS TUÉS NE TRANCHE RIEN** — un `usbipd.exe` dont la
`CommandLine` est **illisible** est classé « pas un veilleur » EN SILENCE par
`wsl-attach.sh:75-81` (faux négatif **MESURÉ** le 2026-08-26, PID 6056). L'outil le
**dit** (*« ni tué, ni innocenté »*) et **le verdict reste l'ÉTAT DU PORT** : `STATE`
usbipd + présence de `COM3` / `/dev/ttyACM*`.

```bash
# rendre le port à Windows, pour l'agent   — mesuré 7,349 s · n = 6 · 0 échec
./tools/rendre-port.sh --vers-agent
# reprendre la carte sous WSL, pour flasher — mesuré 8,519 s · n = 3 · 0 échec

> 🔴 **CHIFFRES CORRIGÉS LE 2026-08-26 (revue de code), ET LE MOTIF COMPTE.**
> `--vers-flash` a **DEUX régimes de coût**, et le README publiait le mauvais :
>
> | | n | min | max | **moyenne** |
> |---|---|---|---|---|
> | `--vers-flash` **avec un agent à arrêter** — *ce que vous faites* | 3 | 8,046 | 9,124 | **8,519 s** |
> | `--vers-flash` sans agent (port déjà libre) | 3 | 6,438 | 6,717 | 6,598 s |
> | `--vers-agent` | 6 | 7,232 | 7,480 | **7,349 s** |
>
> L'ancien **6,58 s** mesurait le cas **sans agent** — qui n'arrive jamais quand
> on reprend la carte **pour flasher**. Les **+1,9 s** sont **le coût de l'arrêt
> propre**, celui qui fait sortir le bilan de fin : c'est une fonctionnalité,
> ⛔ pas une perte. **12 passages, 0 échec**, busid `3-5`, SHA au dossier §25.18.

#   (il ARRÊTE l'agent et le PROUVE en rouvrant COM3, ⛔ pas par un code de retour)
./tools/rendre-port.sh --vers-flash
# ne change RIEN, dit tout :
./tools/rendre-port.sh --etat
```

⚠️ **~4 des 7,349 s sont un DÉLAI DE RE-VÉRIFICATION, et il est voulu** : les veilleurs
ressuscitent en ~2 s, donc l'outil **relit `usbipd list` après le délai** et **échoue
bruyamment** si la ligne repasse à `Attached`. On paie 4 s pour ne plus payer une heure.
🔴 **Le busid n'est écrit NULLE PART ici, et c'est délibéré** : il **suit le port
physique**. **TROIS valeurs ont été vraies** — `3-7` (2026-08-20), `3-1` (2026-08-26),
`3-5` (2026-08-27/28) — et sur cette machine **`3-1` porte aujourd'hui un `V31GT`
(`0e8d:201c`)**, ⛔ pas la carte. L'outil le **relit à chaque appel** et **échoue
proprement** si la carte est absente.
⚠️ *Jusqu'au 2026-08-30, cette affirmation était FAUSSE dans son propre fichier* : la
recette d'installation, 1 000 lignes plus haut, écrivait le busid **EN DUR** (`3-1`).
**Deux vérités contradictoires dans un même document** — levée par `dn4-15`.

<details><summary>Le rituel manuel, si l'outil est indisponible — ⛔ il ÉCHOUE, c'est mesuré</summary>

```bash
# 0) tuer les veilleurs DES DEUX CÔTÉS (voir l'avertissement ci-dessus)
ps aux | grep usbip-auto-attach                                   # WSL
powershell.exe -Command "Get-CimInstance Win32_Process -Filter \"Name='usbipd.exe'\""
#    → Stop-Process sur ceux dont la ligne de commande contient auto-attach
# 1) RELIRE le busid — ⛔ jamais une constante :
powershell.exe -Command "& 'C:\Program Files\usbipd-win\usbipd.exe' list"
# 2) detach, puis VÉRIFIER que ça a TENU (STATE doit être « Shared ») — 0,3 s
# 3) retour vers WSL — ~3,1 s :
cd ~/projects/desknode && ./tools/wsl-attach.sh
```
⚠️ **Coût réel de ce rituel** : un `detach` défait en quelques secondes, un `COM3`
fantôme, un « Attached » orphelin, et une récupération qui demande **un RESET physique**.
</details>

### 🆕 Lancer / arrêter l'agent DEPUIS WINDOWS — `dn-agent.bat` (`dn4-17`)

L'agent **vit sur la tour** : `tools/deployer_tour.sh` dépose `dn_agent.py`, `dn-agent.bat`
et `dn_agent_tour.ps1` dans `H:\dev\projets\desknode`. ⛔ **Plus aucun chemin
`\\wsl.localhost`** ⇒ **WSL peut être éteint**.

| geste | ce qu'il fait |
|---|---|
| **double-clic** sur `dn-agent.bat` | `start` — et un second double-clic ne crée **AUCUN doublon** |
| `dn-agent.bat etat` | compte de process **avec PID**, état de `COM3`, état usbipd — **ne change RIEN** |
| `dn-agent.bat stop` | arrêt **propre** (le bilan de fin est écrit), **prouvé** en rouvrant `COM3` |
| `dn-agent.bat permanence COM3 0 -Temoin` | pose la tâche **au logon**, `-RunLevel Limited` (⛔ **pas** `Highest` : l'agent n'a ni élévation, ni driver, ni .NET — D8/D13) |
| `dn-agent.bat retirer` | retire la tâche, et **vérifie** qu'elle est absente |

⚠️ **`stderr` est redirigé vers `dn-agent.log`** (ajouté, jamais tronqué, bascule en `.1`
au-delà de 5 Mo) : une tâche planifiée **n'a pas de console**, et sans ça le **bilan de
fin** — le seul instrument qui dise si la liaison va bien — serait perdu.
🔴 **`taskkill` ne suffit PAS, et c'est mesuré** : le poli ne tue pas l'agent (vivant
après 5 s) et le `/F` est un `TerminateProcess` inarrêtable ⇒ **0 o de bilan**. L'arrêt
propre passe par un **fichier-drapeau** (`--stop-si`) : **1 s, 1 560 o de bilan**.
⇒ Détails et chiffres : `hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md` §25.

🔴 **DTR/RTS : la parade est WINDOWS-ONLY, et sous Linux elle NUIT.** Sous Windows,
pyserial pose DTR/RTS à l'ouverture et la séquence **RESET la carte** (dn2-2, trois
sessions perdues avant le diagnostic) ⇒ `dn_agent.py` force `dtr=False, rts=False`
AVANT `open()` — **mais uniquement si `sys.platform == "win32"`**.
⚠️ **Sous Linux, poser ces lignes PROVOQUE le reset qu'elles prétendent empêcher** :
A/B à une variable sur `/dev/ttyACM0` (2026-08-16) — **avec** la parade, 6 664 o reçus
et `rst:0x15 (USB_UART_CHIP_RESET)` ; **sans**, 38 o et aucun reboot. Témoin négatif :
`dn_console.py` n'y touche jamais et n'a pas reset la carte de vingt invocations.
⇒ **Tout outil série côté WSL ne doit PAS toucher DTR/RTS.** Côté tour, si.

## Matériel

| Module | Rôle | I²C |
|---|---|---|
| ESP32-S3-Touch-LCD-2.8B | carte + écran + tactile (16 MB flash / 8 MB PSRAM, IMU QMI8658, RTC PCF85063, buzzer) | ext. : SCL=GPIO7, SDA=GPIO15 |
| BME680 | température, humidité (pression et VOC non affichés — brief : 6 widgets) | ✅ **`0x77` MESURÉ** · chip id `0x61`, variant `0x00` |
| BH1750 (GY-302) | luminosité ambiante | **`0x23` MESURÉ** ✅ inventorié, branché, **QUALIFIÉ PAR STIMULUS** (dn4-2, 2026-08-19) — il n'a **aucun registre d'identité**, donc aucune lecture ne peut le prouver : 0,0 lx main posée → **23,3 lx** main retirée → **46 148 lx sous une lampe**. ⚠️ *Ces valeurs étaient publiées ÷10 (« 2,3 » et « 4 614,8 ») jusqu'à la revue de code du 2026-08-20 : le firmware calculait `(brut × 10) / 12`, qui **EST déjà la valeur en lux**, puis l'imprimait comme des dixièmes. **AC6 tient** — le stimulus qualifie par le RAPPORT — mais le chiffre absolu était faux ET plausible.* ⚠️ `ADDR` **tiré bas par le breakout** ⇒ `0x23` déterministe **sans fil ajouté** (mesuré). ⛔ **`i2c lire` le PILOTE au hasard** (l'octet est un opcode) : utiliser `i2c ecrire` + `i2c brut` |
| 🔴 **TOF050C-VL6180X** (⛔ **PAS** un VL53L0X) | proximité / présence | **`0x29` MESURÉ** ✅ **QUALIFIÉ PAR LECTURE** (dn4-2, 2026-08-19) : `i2c lire16 29 0000` → **`B4`**, 5 fois sur 5 ; témoin négatif `i2c lire 29 C0/C1/C2` → `01`/`00`/`00`, ⛔ **pas** `EE`/`AA`/`10`. Rév. modèle 1.3, module 2.0. ⚠️ **index de registre sur 16 BITS** ⇒ `i2c lire` ne peut **structurellement pas** le qualifier. ⚠️ **Portée GARANTIE 100 mm** (le « 50 cm » est une annonce revendeur) et **ALS intégré**. `XSHUT` **tiré haut par le breakout** ⇒ **non câblé**, décision mesurée ; `INT` **non câblé** (AC11) |
| INA219 (CJMCU) | tension / courant / puissance | **`0x40` MESURÉ** ✅ **QUALIFIÉ PAR LECTURE** (dn4-2, 2026-08-19) : `i2c lire 40 00 2` → **`39 9F`**, 5 fois sur 5 (reset du registre Configuration, TI SBOS448G) ; contrôle négatif `05` → `00 00`. Cavaliers `A0`/`A1` **non pontés** ⇒ `0x40`. Shunt `R100`. ⛔ **`Vin+`/`Vin-` NON câblés.** 🔴 **`dn4-3` (2026-08-20) A NOMMÉ CE QU'IL MESURE, ET CE N'EST PAS UNE ALIMENTATION** : `02h` rend **`07 0A` = 900 mV, CNVR=1, OVF=0** — le potentiel d'une entrée **flottante**, stable et **parfaitement plausible**, qui n'est le rail de rien. ⛔ Aucun chiffre de D5 ne peut en sortir ; le poser **en série** reste une **question OWNER** (X3). 🔴 **ET UN FAIT DE CETTE LIGNE EST RÉFUTÉ, PAR AJOUT** : le contrôle négatif publié ici (`01h` Shunt Voltage → `00 00`, *« shunt libre »*) est **FAUX**. Mesuré `2992181` le 2026-08-20 : **`FF FB` = −50 µV**, du **bruit**, ce qui est **physiquement attendu** d'une entrée différentielle flottante. ⚠️ **Conséquence, et elle est vicieuse** : ce contrôle ne peut pas fonctionner — **il rendrait « anormal » l'état normal**. ⇒ ⛔ **Ne plus l'employer.** ✅ **Témoin anti-fantôme FORT, ÉPROUVÉ deux fois** : le registre Calibration (`05h`) est inscriptible et relisible, et sa valeur de reset (`0000`) **diffère** de la valeur imposée — vérifié `D7 A4` posé puis relu (dn4-2), puis **`D7 A4` re-vérifié en dn4-3**. 🎯 **`dn_env` y impose désormais `0x1000`**, qui n'est pas un nombre magique mais la **VRAIE calibration** du shunt R100 (0,1 Ω, 3,2 A ⇒ `Current_LSB` 0,1 mA, `Power_LSB` 2 mW, TI SBOS448G §8.5.1) : **un témoin qui est aussi la configuration ne peut pas être oublié au prochain refactor** |

**Occupants du bus MESURÉS le 2026-08-16** (scan stable `5/5`, ~20 passes) : `0x20` TCA9554 ·
**`0x51` PCF85063 — la RTC est vivante, première confirmation** · `0x5D` GT911 ·
**`0x6B` QMI8658 — et c'est `0x6B`, pas `0x6A`**.

🔴 **Le connecteur I²C externe est une EMBASE JST, sérigraphiée `GND · 3V3 · SDA · SCL`.** Le
miroir Spotpear du wiki Waveshare annonçait `GND · 3V3 · SCL · SDA` sur un « header 2,54 mm » :
**deux erreurs dans la même ligne**. ⚠️ Une **seconde embase JST identique** juste à côté porte
l'UART (`GND · 3V3 · TXD · RXD`) — se tromper d'embase alimente correctement le composant et le
laisse muet. Détail et symptômes : `hardware/…-capteurs-i2c.md` §13.1.

### Procédure de câblage des QUATRE capteurs — et les photos qui en font foi

> 🔴 **ÉTENDUE AUX TROIS CAPTEURS DE `dn4-2` PAR LA REVUE DE CODE DU 2026-08-20.** Cette
> section ne parlait que du BME680, de son embase JST et de `0x77`, alors que trois modules de plus
> sont soudés sur le même bus depuis le 2026-08-20 — c'est la moitié « câblage » du **critère n°5
> du brief**, et elle était incomplète.

#### Ce qui change quand on passe de UN à QUATRE capteurs

| Point | Ce qu'il faut savoir |
|---|---|
| **Où ça se raccorde** | Le BME680 reste sur l'**embase JST 4 points** (`GND · 3V3 · SDA · SCL`, côté interrupteur). Les **trois nouveaux** passent par le **header 2×12** (`SCL · SDA · 3V3 · G`), via **4 câbles de dérivation** (2× Y3, 2× Y2) fabriqués par l'owner. ⚠️ **Il n'y a qu'UN header 2×12** — la doc constructeur en annonçait deux, c'est faux (§14.3 de `…-affichage.md`) |
| **ZÉRO GPIO consommé** | L'I²C est un **bus** : les quatre partagent `SDA = GPIO15` et `SCL = GPIO7`. ⇒ Aucune broche de header n'est prise, et le piège `GPIO37/36/35/34/33` (PSRAM interne) **ne peut pas se déclencher** — mais son entrée de ledger **reste OUVERTE** : *une parade n'est pas une réfutation* |
| **Barrettes NON soudées** | Les **trois** breakouts sont livrés barrette **non montée**, comme le BME680. Des broches posées dans leurs trous **ne conduisent pas** — c'est ce qui a coûté la moitié d'une séance |
| **`ADDR` du BH1750** | ⛔ **AUCUN fil.** Le GY-302 le tire **bas** ⇒ `0x23` déterministe (mesuré : répond **5/5** avec les 4 fils de bus seuls). ⚠️ La datasheet ROHM ne définit `0x23` que pour `ADDR ≤ 0,3 × VCC` : c'est le **breakout** qui le garantit, pas la puce |
| **`XSHUT` du ToF** | ⛔ **AUCUN fil.** Le TOF050C le tire **haut** ⇒ la puce répond fil retiré. 🔴 **Mais si le ToF devient un jour intermittent, `XSHUT` est le PREMIER suspect — pas la soudure** |
| **`INT` du ToF** | ⛔ **NON câblé** (AC11) : aucune broche d'interruption, le polling suffit |
| **`Vin+`/`Vin-` de l'INA219** | ⛔ **RIEN.** Ce sont les bornes du **shunt**, pas l'alimentation logique. 🔴 **C'est le pire miroir des quatre** : câbler « dans l'ordre » y envoie le 3V3 **directement sur le shunt** |
| **Tirages de bus** | Mesurés à l'ohmmètre, modules isolés : **BH1750 = AUCUN** (le catalogue le donne à 4,7 kΩ — il aurait menti) · ToF **10 kΩ** · INA219 **10 kΩ**. ⇒ **+2 jeux, pas +3** ⇒ **l'ajout coûte** `+0,66 mA` à l'état bas **sur un budget de 3 mA dont la consommation de départ n'est PAS mesurée** (⚠️ *ce verdict disait « Large » jusqu'à la revue du 2026-08-24 : il comparait un **incrément** à une **limite absolue**, alors que la mesure est prise côté MODULES et que la base côté CARTE est inconnue — Y6 demandait un TOTAL*) |

#### Le miroir — aucun des quatre ne s'aligne « premier avec premier »

```
câble/embase carte  :  GND    3V3    SDA    SCL
BME680              :  VCC    GND    SCL    SDA    SDO   CS
BH1750  (GY-302)    :  VCC    GND    SCL    SDA    ADDR
ToF     (TOF050C)   :  VIN    GND    SDA    SCL    INT   XSHUT
INA219  (CJMCU)     :  Vin+   Vin-   Sda    Scl    Gnd   Vcc
```

⇒ Poser les fils « dans l'ordre » **inverse l'alimentation sur les quatre** et **croise `SDA`/`SCL`
sur deux d'entre eux**.

#### La qualification — une voie PAR capteur, ⛔ jamais le scan

| Capteur | Commande | Attendu |
|---|---|---|
| **BME680** `0x77` | `i2c lire 77 D0` | `61` |
| **INA219** `0x40` | `i2c lire 40 00 2` | **`39 9F`** · contrôle négatif : `05` → `00 00` |
| **VL6180X** `0x29` | `i2c lire16 29 0000` | **`B4`** · témoin négatif : `i2c lire 29 C0` **ne rend pas** `EE` de façon reproductible |
| **BH1750** `0x23` | 🔴 **STIMULUS — il n'a AUCUN registre** : `i2c ecrire 23 01`, puis `i2c ecrire 23 10`, puis **attendre ≥ 180 ms**, puis `i2c brut 23 2` | une valeur **plausible**, **qui CHANGE** quand on masque le capteur de la main |

🔴 **NE JAMAIS enchaîner `i2c ecrire 23 10` et `i2c brut 23 2` dans le MÊME LOT** : le pilote
envoie un lot en quelques **dizaines** de ms, la mesure du BH1750 en demande **jusqu'à 180**. La
lecture rendrait `00 00` et **le capteur serait déclaré mort alors qu'il fonctionne**.
⇒ **Deux invocations séparées**, et la commande l'imprime elle-même quand elle voit l'opcode passer.

🔴 **L'ORDRE DE DIAGNOSTIC EST FIXÉ D'AVANCE — il a déjà coûté une séance entière.** Si un module
ne répond pas, ⛔ **on n'accuse pas la soudure en premier** :
**1.** `XSHUT` / `ADDR` (entrée d'activation ou de sélection mal tirée) → **2.** la bonne embase (les
deux JST sont identiques et adjacentes, **la sérigraphie fait foi**) → **3.** le miroir → **4.** le
protocole (index 8 bits contre 16) → **5.** *et seulement ensuite*, la soudure.

---

### Le montage d'origine du BME680, pas à pas — et les photos qui en font foi

Les photos vivent dans **`docs/cablage/`**, nommées par leur **horodatage EXIF**. Elles sont
décrites une par une en **`hardware/…-capteurs-i2c.md` §13.0**, avec ce qu'elles prouvent **et ce
qu'elles ne prouvent pas** — c'est le critère n°5 du brief (« câblage photographié »).

Le montage, dans l'ordre où il a été fait :

1. 🔴 **Carte DÉBRANCHÉE de l'USB.** Aucun fil ne se pose sur un bus vivant.
2. **Identifier la BONNE embase** des deux jumelles : la sérigraphie fait foi (`SDA · SCL` et non
   `TXD · RXD`), et `docs/cablage/2026-08-16_2228-…` la photographie.
   ⚠️ **Le wiki ne fait PAS foi** — il a été réfuté sur cette ligne même.
3. **Souder la barrette 6 broches** sur le breakout : elle est **fournie NON montée**, et les
   broches simplement posées dans leurs trous **ne conduisent pas** — c'est ce qui a coûté la
   moitié de la séance du 2026-08-16 (§13.5, hypothèse 6). ⛔ Rien à souder côté carte.
4. **Poser les 4 fils un par un** : `GND↔GND`, `3V3↔VCC`, `SCL(GPIO7)↔SCL`, `SDA(GPIO15)↔SDA`.
   ⚠️ **L'ordre du câble JST et celui du breakout sont EN MIROIR sur les deux premières broches** :
   suivre « l'ordre » inverse l'alimentation ET croise les signaux.
5. **Contrôle de continuité au multimètre** (mode bip), fil par fil — c'est ce qui attrape un
   Dupont mal enfoncé, qu'aucun coup d'œil ne voit.
6. **Placer le breakout ÉCARTÉ de la carte**, sur ses fils : collé à la dalle, il mesure la carte
   et non la pièce (§10.2 de la story).
7. **Rebrancher l'USB**, relire le bandeau de boot en entier, puis `i2c` : `0x77` doit sortir
   **`5/5`**, et `i2c lire 77 D0` rendre `61`. ⚠️ **C'est la lecture de registre qui QUALIFIE**, pas
   le scan — il produit des faux positifs ET des faux négatifs (§13.6 bis).

⚠️ **Un front descendant sur `CSB` bascule la puce en SPI jusqu'à la coupure d'alimentation
suivante.** Manipuler les fils sous tension ré-arme donc la panne qu'on vient de purger : la
séquence *bouger → scanner* **ne peut pas converger**, seule *bouger → couper l'alim → rescanner*
le peut. ⛔ Et `reboot` en console **ne coupe PAS le capteur** : `esp_restart()` laisse le rail
3V3 debout. 🔴 Débrancher `VCC` non plus — voir l'alimentation fantôme par les diodes ESD, §13.10.

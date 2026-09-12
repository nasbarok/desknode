#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn7-5 — L'ECART DECLARE SE **RE-DERIVE**, ET LHM EST UN PREREQUIS DUR.

======================= CE QUE CETTE GATE GARDE, ET POURQUOI ================

Mesure du 2026-09-10 : `installeur/index.html`, `installeur/dn_installeur.py`
et `docs/roadmap.md` portaient **ZERO** occurrence de `LHM`, pendant que
`agent/dn_agent.py` en portait **142** (sur 129 lignes) et que son en-tete dit
« C'est LHM qui le fait, ET LUI SEUL ». ⇒ un inconnu qui suivait la page A LA
LETTRE repartait avec un agent qui tourne et une dalle dont la **°C CPU** et
les **trois tr/min** ne se rempliraient JAMAIS. Le seul endroit du produit qui
le disait etait `_bilan()`, une ligne de `stderr` imprimee A L'EXTINCTION
d'une tache planifiee — c'est-a-dire LA OU PERSONNE NE REGARDE.

🔴 CE QUI EST GARDE ICI N'EST ⛔ PAS « LHM EST NOMME ». Ajouter « LHM » a la
   main referme LE CAS D'AUJOURD'HUI et laisse LA MECANIQUE intacte :
   **QUATORZE** endroits publient les prerequis de l'agent, **AUCUN** ne les
   derive, et les **DEUX** enumerations EXECUTABLES (`DEPENDANCES_AGENT` du
   serveur, la sonde `import psutil, serial` de l'outil) ne se sont **jamais**
   parle. ⇒ l'ecart declare se **RE-DERIVE** de `agent/dn_agent.py` **A
   L'AST**, dans les DEUX SENS, et la prochaine dependance absente devient
   impossible a taire.

── LES ONZE CONTROLES DU DOSSIER, ET LEUR NUMERO ICI ───────────────────────

    (a) ⇒ (c1)          (b) ⇒ (c2) **et** (c3)      (c) ⇒ (c4)
    (d) ⇒ (c5)          (e) ⇒ (c6)                  (f) ⇒ (c7)
    (g) ⇒ (c8)          (h) ⇒ (c9) **et** (c10)     (i) ⇒ (c11) **et** (c18)
    (j) ⇒ (c12)         (k) ⇒ (c13)

  🔴 **`(i)` A ETE COUPE EN DEUX LE 2026-09-12 (`dn4-48`), ET LE DOSSIER
     QU'IL SERVAIT A ETE RENVERSE PAR UNE MESURE.** L'item disait « le refus
     LHM sort en `exit 12` ». ⛔ **CE REFUS N'EXISTE PLUS** : au redemarrage du
     2026-09-12 la tache au logon a tire a `18:13:13` et rendu `12` pendant que
     LHM montait a `18:13:34` — **21 s trop tard** —, la reprise
     `RestartCount 3 / RestartInterval PT1M` ⛔ **n'a pas tire** (`LastRunTime`
     fige, releve a `18:25`), et la dalle est restee **morte, en silence**,
     toute la session, sur une machine **SAINE**. Le refus dur allait de
     surcroit **contre la conception du produit** : `agent/dn_agent.py` pose
     ⛔ aucune grandeur LHM en position 0, precisement pour qu'une source LHM
     absente n'empeche RIEN.
     ⇒ le pre-vol **ATTEND** LHM (borne `-AttenteLhm`, 300 s par defaut) puis
       **DEMARRE QUAND MEME**, champs LHM a « -- ».
     ⇒ `(c11)` garde le **COMPORTEMENT** du bloc (il attend, ⛔ il ne refuse
       plus) ; `(c18)` garde le **CODE** `12` — son unicite, et son **nouvel
       emetteur** : le verbe `poser`, ⛔ plus le pre-vol.
     ⚠️ **LES DEUX MOITIES SONT SEPAREES, ET C'EST LA MEME LECON QUE `(b)` ET
        `(h)`** : un controle qui porte deux faits ⛔ ne peut pas dire LEQUEL a
        cede, et un mutant qui le vise ⛔ ne prouve rien de l'autre.

  🔴 **ET UN CONTROLE QUI NE VIENT D'AUCUN ITEM DU DOSSIER : `(c17)`.** Il
     vient de la **matrice d'E/S**, ligne *« LHM monte APRES le logon »* — la
     seule des dix qui n'avait **aucun porteur mecanique**, mesure du
     2026-09-10. Il garde que la parade est **toujours** `-RestartCount 3` a
     `-RestartInterval` 1 minute, et que le bloc date qui nomme la course est
     **toujours** la. C'est la consequence la plus dangereuse de la marche :
     le refus dur transforme un `-RestartCount` retire ou releve en **panne
     silencieuse de TOUTE la session**, sur une machine SAINE.
  ⚠️ **`(c17)` PORTE DEUX FAITS, ET ILS N'ONT PAS LE MEME AGE — c'est ecrit
     ici parce que la MESURE a corrige l'attente.** Le reglage
     `-RestartCount 3 -RestartInterval 1 min` est un **ACQUIS** : il existait
     **avant** cette marche (`dn4-17`, revue du 2026-08-26). Le **bloc date
     qui nomme la course au logon**, lui, est ecrit **par `dn7-5`** — c'est
     le refus dur qui rend la parade load-bearing, et jusque-la personne
     n'avait de raison de l'ecrire.
     🔬 **MESURE, ⛔ pas suppose** : on attendait `(c17)` **VERT** sur le
     temoin negatif *« puisque la reprise existait deja »*. Il en sort
     **ROUGE**, et son detail dit **pourquoi** : ⛔ pas le reglage — **le bloc
     date**. ⇒ le temoin negatif compte **10 `[KO ]`**, ⛔ pas 9.
     ⚠️ Les deux moities restent dans **UN** controle, et c'est voulu : ce
     qu'on garde n'est pas « un nombre » mais « la parade tient **et** on
     sait pourquoi ». Un reglage qui survit sans son motif se fait retirer a
     la revue suivante. ⇒ le detail de la ligne **nomme la moitie qui a
     cede**, pour qu'un rouge ⛔ ne soit jamais ambigu.
     ⛔ **ET LE TEMOIN NEGATIF ⛔ NE PROUVE PAS QUE `(c17)` GARDE LE REGLAGE** —
     il ne prouve que la moitie neuve. Ce qui garde le reglage est le
     **mutant 23**, et lui seul : il retire `-RestartCount` de la tache
     pendant que le README, le CHANGELOG et le ledger continuent de publier
     « 3 reprises a 1 minute ».

  🔴 **ET `(c17)` N'EST PAS SEUL DANS CE CAS — LE TEMOIN NEGATIF NE GARDE PAS
     LA MOITIE DES CONTROLES, ET C'EST ECRIT PLUTOT QUE LAISSE A DEVINER.**
     Mesure du 2026-09-10 contre `git archive c58931d` : **SEPT** controles
     numerotes en sortent **VERTS** — `(c1)(c3)(c5)(c13)(c14)(c15)(c16)` —
     parce qu'ils gardent des **ACQUIS**, ⛔ pas des defauts que cette marche
     repare :
       · `(c1)` la derivation MARCHAIT deja — ce qui manquait, c'est que
         quelqu'un s'en serve ;
       · `(c3)` ⛔ aucun miroir n'existait, faute de sonde ;
       · `(c5)` les deux enumerations etaient d'accord PAR CHANCE — rien ne
         les appariait, et c'est ca que la marche ajoute ;
       · `(c13)` ⛔ aucun jeton d'elevation n'etait entre sous `installeur/` ;
       · `(c14)(c15)(c16)` gardent la campagne elle-meme, ⛔ pas le produit.
     ⇒ **pour ces sept-la, le gardien est LE MUTANT, ⛔ pas le temoin.** Un
     temoin negatif prouve « ce controle voit ce que cette marche a change » ;
     il ⛔ ne prouve **jamais** « ce controle garde quelque chose ». Confondre
     les deux, c'est exactement l'erreur que ce depot a nommee : « N mutants,
     N vus rougir » prouve `mutant ⇒ rouge`, ⛔ jamais `controle ⇒ couvert`.

  ⚠️ DEUX ITEMS DU DOSSIER PORTENT **DEUX FAITS**, ET ILS SONT SEPARES ICI
     PLUTOT QUE FONDUS — un controle qui porte deux faits ne peut pas dire
     LEQUEL a cede, et un mutant qui le vise ne prouve rien de l'autre :
       · `(b)` = « la sonde LIT l'adresse dans le produit » **et** « ⛔ aucun
         miroir chiffre ailleurs » ⇒ `(c2)` et `(c3)` ;
       · `(h)` = « `etat_machine()` EXPOSE LHM a trois positions » **et**
         « `prevol()` l'IMPRIME sans que LHM entre dans `manquantes` » ⇒
         `(c9)` et `(c10)`. Le second garde le `6` : `manquantes` commande A LA
         FOIS le code de sortie ET le bloc qui publie `GESTE_DEPENDANCES`,
         c'est-a-dire `pip install --user psutil pyserial`. Y verser LHM ferait
         imprimer LE MAUVAIS GESTE, et LHM ⛔ n'est pas un module pip.

  Et trois de plus, qui gardent la campagne elle-meme : `(c14)` chaque
  controle est vise par au moins un mutant · `(c15)` chaque cible declaree est
  un controle REEL · `(c16)` `CIBLES` et `MUTANTS` se correspondent.

── CHAQUE AC A SON PORTEUR MECANIQUE, ET IL EST NOMME ──────────────────────

  · `AC7.5.1` — l'ecart declare NOMME LHM sur les trois surfaces, avec ce qui
    tombe sans lui, son geste propre et un etat a TROIS positions :
    `(c7)(c8)(c9)(c10)(c12)`. ⛔ Ce qui le ferme A L'ŒIL reste
    `mesures/dn7-5/T2`, cote Windows.
  · `AC7.5.2` — la RE-DERIVATION, dans les deux sens : `(c1)…(c6)`.
  · `AC7.5.3` — ~~le refus DUR, avec son propre code~~ : `(c11)(c13)`, **et
    `(c17)` pour la piece *(ii)* de son prix**
    🔴 **AMENDE LE 2026-09-12 (`dn4-48`)** : l'AC est devenue *l'ATTENTE
    bornee puis le demarrage DEGRADE*, et son code a change d'emetteur ⇒
    `(c11)(c18)(c13)`. L'ancienne redaction est **barree, ⛔ pas effacee** :
    elle etait exacte du 2026-09-10 au 2026-09-12. — la course au logon, dont la
    parade et la borne sont publiees a trois endroits.
    ⚠️ Que le `6` de l'installeur ⛔ n'ait PAS bouge est garde par `(c28)` de
       `tools/verif_installeur_dn71.py`, qui IMPORTE le produit et JOUE ses
       codes — ⛔ pas par cette gate-ci, qui ne lit que du texte.

── LA TABLE `module → distribution` EST DECLARATIVE, ET C'EST ECRIT ────────

  `serial` ⇒ `pyserial`, `websockets` ⇒ `websockets`, `psutil` ⇒ `psutil`.
  🔴 C'EST IRREDUCTIBLE : aucun arbre syntaxique ne sait qu'on installe
     `pyserial` pour importer `serial`. ⇒ elle est ECRITE plutot que presentee
     comme derivee — et une racine tierce DERIVEE qui n'y figure pas fait
     ROUGIR `(c1)` : c'est la ligne « une dependance neuve apparait » de la
     matrice d'E/S, et elle ⛔ ne peut pas se rejouer en silence.

── LE SENS 2 SE LIT SUR LA TABLE, ⛔ PAS SUR LA PROSE — ET C'EST MESURE ─────

  `(c4)` confronte les deux sens. Le SENS 1 (« toute dependance derivee est
  nommee par la page ET par le README ») se lit sur le derive. Le SENS 2
  (« toute dependance nommee par une surface EXISTE dans le derive ») se lit
  sur le **vocabulaire FERME de la table**, ⛔ pas sur un balayage libre de la
  prose : les deux sections d'ecart citent aussi `pip`, `Python 3`,
  `epic-dn4`, des chemins de fichier et des marqueurs de roadmap. Un balayage
  libre rougirait sur du contenu JUSTE — la faute exacte que
  `verif_licences_dn52.py` documente pour les marqueurs. ⇒ le SENS 2 est
  EXACT sur la population qui compte, et son perimetre est ECRIT ici.

── ⛔ CE QU'ELLE NE PROUVE PAS, ET C'EST ECRIT PLUTOT QUE TU ────────────────

  🔴 **CETTE GATE EST STRUCTURELLE.** Elle ⛔ n'installe pas LHM, ⛔ n'ouvre
     aucun navigateur, ⛔ ne lance aucune tache planifiee et ⛔ n'emet AUCUNE
     requete reseau. Elle prouve que LE MECANISME EST BRANCHE : la sonde
     existe, elle vise CE QUE L'AGENT VISE, le bloc ATTEND au lieu de refuser,
     `12` a SON emetteur, et la prose couvre EXACTEMENT le derive.
  ⛔ Elle ⛔ ne prouve PAS qu'une tour reelle SANS LHM ~~refuse~~ **degrade**.
     ⚠️ `mesures/dn7-5/T2` fermait le REFUS, cote Windows ; depuis `dn4-48`
     (2026-09-12) ce que ferme l'œil owner est l'inverse : **l'agent TOURNE**
     et la dalle **se remplit** alors que LHM est absent, et le POURQUOI
     **atteint** l'humain. La capture de `dn7-5` ⛔ n'est PAS effacee — elle
     dit ce que le produit faisait ce jour-la.
  ⚠️ **ECART DECLARE SUR LA LETTRE DU DOSSIER, ⛔ pas sur sa propriete.** Le
     dossier ecrit « `12` n'apparait nulle part ailleurs dans le fichier ».
     MESURE : `tools/dn_agent_tour.ps1` porte deja un `12` — `Get-Content $LOG
     -Tail 12`, un nombre de LIGNES qui n'a rien d'un code de sortie. La
     propriete qui compte est « `12` n'est le code d'AUCUNE autre sortie », et
     c'est ELLE qui est jouee par `(c11)`. Interdire le chiffre ferait rougir
     du contenu juste ; ⛔ et le taire aurait laisse croire que la lettre du
     dossier est tenue.

Emploi :
    python3 tools/verif_prerequis_dn75.py
    python3 tools/verif_prerequis_dn75.py --liste-mutants
    python3 tools/verif_prerequis_dn75.py --mutant <n>

Sortie : 0 si tout passe · 1 sur un vrai defaut · 2 sur un mutant inconnu ·
         3 si le mutant demande est PERIME (il n'a rien change).
"""

import argparse
import ast
import copy
import io
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGE = "installeur/index.html"
PY = "installeur/dn_installeur.py"
BAT = "installeur/DeskNode-installeur.bat"
OUTIL = "tools/dn_agent_tour.ps1"
AGENT = "agent/dn_agent.py"
LISEZMOI = "README.md"
# 🔴 LE SCRIPT QUE LE GESTE NOMME. Sans lui dans le corpus, renommer `-Poser`
#    en `-Installer` laissait CINQ gates vertes pendant que le geste publie sur
#    QUATRE surfaces devenait injouable d'un coup — mesure du 2026-09-10.
OUTIL_LHM = "tools/dn_lhm_tour.ps1"
# Les deux surfaces de prose qui publient la BORNE de la reprise, a cote du
# README. ⛔ Le ledger, lui, vit dans le cockpit : cette gate ⛔ ne le lit pas.
CHANGELOG = "CHANGELOG.md"
ROADMAP = "docs/roadmap.md"

FIXES = (PAGE, PY, BAT, OUTIL, OUTIL_LHM, AGENT, LISEZMOI, CHANGELOG, ROADMAP)
# Les fichiers de CODE sous `installeur/`, en profondeur 1. ⛔ Les `.md` en
# sont exclus : ce sont de la PROSE, et elle cite forcement ce que le code ne
# doit pas porter. Meme regle que `fichiers_de_code()` de `dn71`.
CODE_INSTALLEUR = (PAGE, PY, BAT)

# ── LA SEULE TABLE DECLARATIVE, ET SON MOTIF EST DANS L'EN-TETE ───────────
DISTRIBUTION = {
    "psutil": "psutil",
    "serial": "pyserial",
    "websockets": "websockets",
}

# ── LES ANCRES LITTERALES ─────────────────────────────────────────────────
# Une ancre qui bouge rend son mutant PERIME (rc=3) ⇒ elle se remarque,
# ⛔ elle ne pourrit pas en silence.
A_SECTION_ECART = '<section id="sec-ecart">'
A_FIN_SECTION = "</section>"
A_GESTE_PIP = "pip install --user psutil pyserial"
A_GESTE_LHM = "dn_lhm_tour.ps1 -Poser"
A_ID_LHM = 'id="v-lhm"'
A_CHAMP_LHM = '"v-lhm"'
A_NOM_LHM = "LibreHardwareMonitor"
A_SANS_GARDE_FR = "sans garde"
A_SANS_GARDE_EN = "without a guard"
A_LHM_DEBUT = "# --- LHM : LE PREREQUIS DUR"
A_LHM_FIN = "# --- fin du prerequis LHM"
A_DEPS = "DEPENDANCES_AGENT = ("
A_SONDE_PS1 = 'import psutil, serial'
A_INSTANCES = "$i = Get-Instances"
# 🔴 LE RANG SE MESURE **DANS LE VERBE**, ⛔ PAS DANS LE FICHIER — ET C'EST UN
#    DEFAUT MESURE LE 2026-09-10, ⛔ pas une precaution. `$i = Get-Instances`
#    apparait CINQ fois dans l'outil, et la PREMIERE (verbe `etat`) precede le
#    pre-vol de cent lignes : un `find()` sur le fichier entier rendait un rang
#    FAUX et faisait rougir un placement JUSTE. Le rang qui compte est celui
#    des branches du `switch`, ⛔ pas celui des declarations.
A_CAS_PREVOL = "'prevol' {"
A_CAS_SUIVANT = "'lancer' {"
# 🔴 dn4-48 — LE VERBE QUI REND `12` DESORMAIS. Le code a CHANGE
#    D'EMETTEUR : il quitte le bloc LHM de `prevol` (qui ⛔ ne refuse plus)
#    pour `poser`, seul appelant qui SACHE lire une table de codes. Le rang se
#    mesure donc dans DEUX regions, ⛔ jamais dans le fichier entier.
A_CAS_POSER = "'poser' {"
A_CAS_APRES_POSER = "'retirer' {"
# Ce que le bloc LHM doit porter depuis `dn4-48` — l'attente BORNEE, sa ligne
# PAR TOUR, et le bandeau du demarrage DEGRADE. ⚠️ Les trois sont cherches
# DANS LE BLOC : les poser ailleurs serait un `grep` vert sur un produit muet.
A_BORNE = "$AttenteLhm"
A_ATTENTE_TOUR = "on ATTEND ("
A_ATTENTE_PAS = "Start-Sleep -Seconds $pas"
# 🔴 ET LE PAS EST **DERIVE DE LA BORNE**, ⛔ pas fige : une borne de 6 s
#    sondee DEUX fois (pas fixe de 5 s) n'est pas une attente, c'est un
#    tirage au sort. `Pas-Attente` garantit AU MOINS DIX TOURS, quelle que
#    soit la borne — et c'est aussi ce qui rend le banc PowerShell payable.
A_PAS_DERIVE = "Pas-Attente $AttenteLhm"
A_DEGRADE = "DEMARRAGE DEGRADE"
# La surface Windows du POURQUOI — `msg.exe`, sans elevation ni .NET (`D8`).
A_SURFACE_WINDOWS = "Prevenir-Windows"
# Ce que la fonction imprime EN PROPRE quand la surface manque, et la forme
# par laquelle l'appelant JETTE son retour — c'est ce `$null =` qui rend
# impossible qu'une surface absente deplace le code de sortie du pre-vol.
A_MOT_SANS_SURFACE = "AUCUNE SURFACE DE NOTIFICATION"
A_SURFACE_DEBUT = "function Prevenir-Windows "
A_SURFACE_FIN = "function Rotation-Journal {"
A_RETOUR_JETE = "$null = Prevenir-Windows"
# ── LA PARADE DE LA COURSE AU LOGON, ET SA BORNE ──────────────────────────
# 🔴 CE QUE (c17) GARDE, ET POURQUOI IL EXISTE. Le refus dur transforme un
#    `-RestartCount` retire ou releve en **PANNE SILENCIEUSE DE TOUTE LA
#    SESSION**, sur une machine SAINE : la tache de LHM demarre ELEVEE au
#    logon, celle de l'agent ⛔ non, les deux tirent sur le MEME evenement,
#    donc elles se courent apres. La parade EXISTE — 3 reprises a 1 minute —
#    et sa BORNE (~3 min, au-dela l'agent est absent toute la session) est
#    publiee au README, au CHANGELOG et au ledger. ⇒ trois surfaces disent le
#    prix, et ⛔ RIEN ne gardait le fait qui le rend supportable.
# ⚠️ LES VALEURS SONT **DERIVEES**, ⛔ pas comparees a une chaine : un
#    `-RestartCount 30` doit rougir en DISANT 30, ⛔ pas « ancre absente ».
A_BLOC_COURSE = "# !!! 2026-09-10 (dn7-5) - LE REFUS DUR CREE UNE **COURSE AU LOGON**"
A_RESTART = "-RestartCount 3 "
RE_RESTART_COUNT = re.compile(r"-RestartCount\s+(\d+)")
RE_RESTART_MINUTES = re.compile(
    r"-RestartInterval\s*\(\s*New-TimeSpan\s+-Minutes\s+(\d+)\s*\)")
REPRISES_ATTENDUES = 3
MINUTES_ATTENDUES = 1
# 🔴 LA BORNE SE **DERIVE** DES TROIS SURFACES QUI LA PUBLIENT, ⛔ elle ne se
#    compare pas aux seules constantes de cette gate. Sans ca, editer le README
#    en « 5 reprises » laissait la passe VERTE — dans la marche dont `AC7.5.2`
#    fait de « re-deriver, dans les deux sens » sa these entiere.
RE_BORNE_FR = re.compile(r"(\d+)\s+reprises?\s+à\s+(\d+)\s+minutes?")
RE_BORNE_EN = re.compile(r"(\d+)\s+restarts?,\s*(\d+)\s+minutes?\s+apart")
SURFACES_BORNE = ((LISEZMOI, RE_BORNE_FR), (CHANGELOG, RE_BORNE_EN),
                  (ROADMAP, RE_BORNE_EN))
# Les commutateurs que le geste publie — DERIVES de la chaine, ⛔ pas ecrits.
RE_COMMUTATEUR = re.compile(r"\s-([A-Za-z][A-Za-z0-9]*)")
RE_PARAM_PS1 = re.compile(r"^param\s*\((.*?)^\)", re.S | re.M)
A_AGENT_PY = 'os.path.join(RACINE, "agent", "dn_agent.py")'
A_SONDE_PY = "lhm_present"
A_CIBLE_PY = "cible_lhm"
A_ECART_README = "### 🔴 Ce que vous devez installer vous-même"

# Le vocabulaire de l'elevation — RECIPROQUE LOCALE de `(c4)` de
# `tools/verif_installeur_dn71.py`. ⛔ IL NE VIT QUE DANS LES GATES : le citer
# dans un fichier garde le ferait rougir sur du contenu JUSTE. Les motifs sont
# repris a l'identique, y compris la lecon du trou mesure le 2026-09-08
# (`runas` cherche COMME MOT, ⛔ pas comme sous-chaine d'une chaine litterale).
MOTIFS_ELEVATION = (
    ("runas", re.compile(r"\brunas\b", re.I)),
    ("RunAsAdministrator", re.compile(r"runasadministrator", re.I)),
    ("RunLevel Highest", re.compile(r"runlevel\s*=?\s*['\"]?highest", re.I)),
    ("requestedExecutionLevel", re.compile(r"requestedexecutionlevel", re.I)),
    ("requireAdministrator", re.compile(r"requireadministrator", re.I)),
    ("ShellExecute + elevation", re.compile(r"shellexecute\w*", re.I)),
    ("Start-Process -Verb", re.compile(r"start-process[^\n]{0,80}-verb", re.I)),
)

# Ce qui signe un verdict pris sur le PROCESSUS et non sur `/metrics`. Un LHM
# lance SANS son serveur web rend « 1 processus » et un `/metrics` MORT : ce
# serait un FAUX VERT, c'est-a-dire la faute que ce depot a nommee quatre fois
# pendant `dn7-4`. Le serveur web de LHM vient de sa CONFIG XML
# (`tools/dn_lhm_tour.ps1:317-320`), ⛔ pas de son lancement.
JETONS_PROCESSUS = ("get-process", "process_iter", "tasklist", "get-ciminstance")
# 🔴 CE QUE LE CORPS DOIT PORTER POUR QUE CE SOIT LHM ET ⛔ PAS UN VOISIN :
#    le prefixe que `agent/dn_agent.py` exige de CHAQUE ligne qu'il retient
#    (`if not ligne.startswith("lhm_")`). ⛔ Ce n'est pas une precaution : c'est
#    LA MEME question que l'agent pose, ⛔ pas une question voisine.
MARQUE_CORPS = "lhm_"
NOM_MARQUE_PY = "RE_MARQUE_LHM"

RE_CHAMPS = re.compile(r"var CHAMPS = \[(.*?)\];", re.S)
RE_LIGNE_PAGE = re.compile(r'<div class="ligne">(.*?)</div>\s*(?=<div|<p|</section)',
                           re.S)
RE_PRE = re.compile(r"<pre[^>]*>(.*?)</pre>", re.S)
RE_CODE = re.compile(r"<code>([^<]*)</code>")
RE_EXIT = re.compile(r"^\s*exit\s+(\d+)\s*$", re.M)

LARGEUR_LIBELLE = 58

ok_total = [0]
ko_total = [0]
ids_emis = []

MUTANTS = {}                      # ⛔ AU NIVEAU MODULE — sinon `--liste-mutants`
CIBLES = {}                       # ⛔ AU NIVEAU MODULE — matiere de (c14)

MUTANTS[1] = ("ajoute a l'agent un import TIERS NEUF ⇒ une "
              "dependance qu'aucune surface ne nomme")
CIBLES[1] = ("c1",)
MUTANTS[2] = ("recopie l'adresse de LHM au lieu de la LIRE dans "
              "l'agent ⇒ une SECONDE source de verite")
CIBLES[2] = ("c2",)
MUTANTS[3] = ("plante le port de LHM EN DUR sous `installeur/` ⇒ "
              "un miroir qui divergera au premier `-Port`")
CIBLES[3] = ("c3",)
MUTANTS[4] = ("retire LHM de la page ⇒ le defaut d'origine, "
              "replante mot pour mot (SENS 1)")
CIBLES[4] = ("c4",)
MUTANTS[5] = ("retire `import serial` de l'agent pendant que la "
              "page nomme `pyserial` ⇒ SENS 2")
CIBLES[5] = ("c4", "c5", "c6")
MUTANTS[6] = ("desapparie les DEUX enumerations executables ⇒ "
              "celles qui ne se sont jamais parle")
CIBLES[6] = ("c5",)
MUTANTS[7] = ("rend la mention « sans garde » a `websockets` "
              "SEUL ⇒ le second defaut, replante")
CIBLES[7] = ("c6",)
MUTANTS[8] = ("nomme LHM dans le geste `pip` ⇒ le mauvais geste "
              "pour une dependance qui n'est pas un module")
CIBLES[8] = ("c7",)
MUTANTS[9] = ("retire `v-lhm` de `CHAMPS` ⇒ le champ reste sur "
              "ses points de suspension POUR TOUJOURS")
CIBLES[9] = ("c8",)
MUTANTS[10] = ("ecrase les trois positions de la sonde LHM en "
               "`bool()` ⇒ une IGNORANCE publiee en constat")
CIBLES[10] = ("c9",)
MUTANTS[11] = ("verse LHM dans `manquantes` ⇒ le `6` bouge et le "
               "geste `pip` s'imprime pour LHM")
CIBLES[11] = ("c10",)
# 🔴 REECRIT LE 2026-09-12 (`dn4-48`) — L'ANCIEN MUTANT REPLANTAIT « le
#    refus sort en 4 au lieu de 12 ». Ce refus ⛔ N'EXISTE PLUS, donc son ancre
#    non plus : garde tel quel, il serait sorti en `rc=3` (PERIME), c'est-a-dire
#    en gardien MORT. ⛔ IL NE DEBRANCHE RIEN : il REPLANTE la faute NEUVE — le
#    refus dur REVIENT dans le bloc LHM —, qui est exactement la forme sous
#    laquelle la regression se reintroduirait un jour (« LHM est un prerequis
#    dur, remettons le refus »). Il fait rougir `(c11)` (le bloc REFUSE de
#    nouveau) ET `(c18)` (`12` n'est plus unique) : les deux sont DECLARES.
MUTANTS[12] = ("REPLANTE le refus dur dans le bloc LHM ⇒ le "
               "pre-vol avorte le lancement qu'il doit permettre")
CIBLES[12] = ("c11", "c18")
MUTANTS[13] = ("fait trancher le PROCESSUS au lieu de `/metrics` "
               "⇒ un LHM sans serveur web passe VERT")
CIBLES[13] = ("c12",)
MUTANTS[14] = ("plante un jeton d'elevation sous `installeur/` ⇒ "
               "la page promet ce qu'elle ne tient plus")
CIBLES[14] = ("c13",)
MUTANTS[15] = ("vide la cible d'un mutant ⇒ un controle garde par "
               "ZERO mutant, et rien ne le dit")
CIBLES[15] = ("c14",)
MUTANTS[16] = ("declare dans `CIBLES` un controle INEXISTANT ⇒ une "
               "cible PERIMEE que « N rouges » ne voit pas")
CIBLES[16] = ("c15",)
MUTANTS[17] = ("declare une cible pour un mutant qui N'EXISTE PAS")
CIBLES[17] = ("c16",)
MUTANTS[18] = ("declare un mutant dont le CORPS LEVE ⇒ un mutant "
               "MORT, qui doit se rendre en KO et ⛔ pas en trace")
CIBLES[18] = ("c0",)
MUTANTS[19] = ("replante une SORTIE ANTICIPEE NON DECLAREE ⇒ le "
               "bilan sort sur une population RETRECIE")
CIBLES[19] = ("z",)
MUTANTS[20] = ("efface le bloc LHM ENTIER de l'outil ⇒ plus "
               "aucune sonde, plus aucune attente, plus rien")
CIBLES[20] = ("c2", "c11", "c12")
# 🔴 dn4-48 — IL REPLANTE LA FAUTE : une SURFACE ABSENTE redevient un ECART.
#    Le pre-vol se remettrait a REFUSER parce que `msg.exe` n'est pas la —
#    c'est-a-dire qu'une edition Familiale de Windows perdrait l'agent que
#    cette marche existe pour lui rendre. ⛔ Ce n'est pas un debranchement.
MUTANTS[31] = ("fait PESER la surface absente sur le code de "
               "sortie ⇒ une ignorance redevient un ECART")
CIBLES[31] = ("c19",)
MUTANTS[30] = ("fait rendre `0` a `poser` sur un agent vivant "
               "SANS LHM ⇒ la page annonce un succes PLEIN")
CIBLES[30] = ("c18",)
MUTANTS[21] = ("retire l'impression de LHM au pre-vol ⇒ l'ecart "
               "existe et ne se dit plus la ou on le lit")
CIBLES[21] = ("c10",)
MUTANTS[22] = ("retire la garde `ImportError` de `psutil` ⇒ une "
               "3e non gardee que la page ne nomme pas")
CIBLES[22] = ("c6",)
MUTANTS[23] = ("retire `-RestartCount` de la tache ⇒ la parade "
               "MEURT pendant que trois surfaces la publient")
CIBLES[23] = ("c17",)
MUTANTS[24] = ("renomme le commutateur du geste dans son propre "
               "script ⇒ 4 surfaces publient un geste INJOUABLE")
CIBLES[24] = ("c7",)
MUTANTS[25] = ("desapparie le geste page ⇄ README ⇒ une surface "
               "sur quatre oubliee, et rien ne le dit")
CIBLES[25] = ("c7",)
MUTANTS[26] = ("rend la moitie ANGLAISE de « sans garde » a "
               "`websockets` seul ⇒ la regression pour eux seuls")
CIBLES[26] = ("c6",)
MUTANTS[27] = ("efface LHM de la seule moitie ANGLAISE de l'ecart "
               "⇒ nomme en francais, tu en anglais")
CIBLES[27] = ("c4",)
MUTANTS[28] = ("publie une AUTRE borne dans la roadmap ⇒ la prose "
               "promet une parade que la tache ne tient pas")
CIBLES[28] = ("c17",)
MUTANTS[29] = ("rend le verdict de la sonde a `status != 500` ⇒ "
               "n'importe quel voisin vaut preuve de LHM")
CIBLES[29] = ("c12",)

# ⚠️ LE COMPTE DU CHEMIN NORMAL : 1 pre-vol + un controle par mutant + les 18
#    controles numerotes. Il se PERIME si on ajoute un controle sans le mettre
#    a jour — et c'est voulu : c'est ce qui rend (z) FALSIFIABLE.
#    ⚠️ PASSE DE 17 A 18 LE 2026-09-12 (`dn4-48`) : `(c11)` a ete COUPE EN
#       DEUX — le comportement du bloc d'un cote, le code `12` de l'autre.
CONTROLES_PREVUS = 1 + len(MUTANTS) + 19

_MUTANT = 0

RE_ID_CTRL = re.compile(r"\((\w+)\)")


def ctrl(ok, libelle, detail=""):
    """UNE assertion, UNE ligne, UN identifiant. ⛔ Aucun controle muet.

    ⚠️ L'IDENTIFIANT VIT DANS LE LIBELLE, ⛔ pas dans un argument a part : la
       campagne de mutants lit les libelles A L'AST en prenant le second
       argument de chaque appel, et A COLONNE FIXE."""
    assert len(libelle) < LARGEUR_LIBELLE, (
        "libelle de %d colonnes (max %d) : %r"
        % (len(libelle), LARGEUR_LIBELLE - 1, libelle))
    m = RE_ID_CTRL.match(libelle)
    ids_emis.append(m.group(1) if m else "?")
    if ok:
        ok_total[0] += 1
    else:
        ko_total[0] += 1
    print("  [%s] %-58s %s" % ("OK " if ok else "KO ", libelle, detail))
    return ok


def bilan(rc, anticipee=""):
    """TOUT CHEMIN QUI REND UN VERDICT passe ici. Une gate qui sort sans
    `BILAN` est indiscernable d'une gate MORTE — et c'est precisement le
    discriminant que la campagne exige de chaque mutant.

    ⚠️ DEUX SORTIES NE PASSENT PAS ICI, ET C'EST ECRIT PLUTOT QUE PROMIS :
       · `--liste-mutants`, qui n'emet AUCUN controle et ne rend AUCUN verdict ;
       · le mutant INCONNU, qui est une ERREUR D'APPEL et rend 2."""
    emis = ok_total[0] + ko_total[0]
    if not anticipee and emis != CONTROLES_PREVUS:
        ctrl(False, "(z) tout controle prevu est EMIS",
             "⛔ %d emis pour %d prevus — une gate qui joue MOINS de controles "
             "qu'annonce sort VERTE sur une population RETRECIE, ⛔ sans le "
             "declarer" % (emis, CONTROLES_PREVUS))
        rc = 1
    print("\n" + "=" * 78)
    if anticipee:
        print("⛔ SORTIE ANTICIPEE — %d controle(s) emis sur %d prevus : %s"
              % (ok_total[0] + ko_total[0], CONTROLES_PREVUS, anticipee))
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return rc


# ═══════════════════════ LIRE, ⛔ JAMAIS SUPPOSER ══════════════════════════

def lire(chemin):
    try:
        with io.open(os.path.join(RACINE, chemin), encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def region(txt, ouvrant, fermant):
    """La portion entre deux bornes, ⛔ pas le fichier entier.

    🔴 UNE FENETRE QUI NE SE REFERME PAS REND **VIDE**, ⛔ jamais « tout ce qui
       suit » : le fermant est cherche APRES l'ouvrant, et son absence est un
       vide, ⛔ pas une permission de balayer la fin du fichier."""
    if not txt or ouvrant not in txt:
        return ""
    apres = txt.split(ouvrant, 1)[1]
    if fermant not in apres:
        return ""
    return apres.split(fermant, 1)[0]


def section_ecart_readme(readme):
    """La section d'ecart declare du README, bornee par SON titre et le
    suivant. ⛔ Pas le README entier : `LibreHardwareMonitor` y est nomme 27
    fois ailleurs, et un controle qui balaie tout serait VERT sans que la
    section que l'inconnu lit ait change d'un mot."""
    if not readme or A_ECART_README not in readme:
        return ""
    apres = readme.split(A_ECART_README, 1)[1]
    m = re.search(r"\n#{2,4} ", apres)
    return apres[:m.start()] if m else apres


# ═══════════ (a) LES DEPENDANCES REELLES DE L'AGENT, A L'AST ══════════════

def deps_agent(src):
    """Les dependances TIERCES de l'agent, DERIVEES a l'AST — ⛔ jamais une
    liste ecrite a la main.

    🔴 `Import` **ET** `ImportFrom`, **Y COMPRIS DANS LES CORPS DE FONCTION** :
       les deux dependances non gardees de ce produit sont importees DANS des
       `__init__` (`serial` dans `SortieSerie`, `websockets.sync.client` dans
       `SortieWebSocket`). Une lecture qui ne regarderait que le module de
       premier niveau les raterait TOUTES LES DEUX.
    🔴 LE TRI STDLIB / TIERS SE FAIT SUR `sys.stdlib_module_names`, ⛔ pas sur
       une liste : c'est le seul inventaire que l'interprete tient lui-meme.
    ⚠️ GARDEE = un `ast.Try` qui ENGLOBE l'import et dont un `ExceptHandler`
       attrape `ImportError` (ou `ModuleNotFoundError`). ⛔ Un `try` nu ne
       garde rien : il avalerait aussi bien une autre faute.

    Rend `{distribution: {"module":…, "gardee":bool, "ligne":int}}`, et la
    liste des racines tierces SANS entree dans la table (⇒ `(c1)` rougit).
    """
    try:
        arbre = ast.parse(src or "")
    except (SyntaxError, ValueError):
        return None, None
    gardes = set()
    for n in ast.walk(arbre):
        if not isinstance(n, ast.Try):
            continue
        attrape = False
        for h in n.handlers:
            noms = []
            if isinstance(h.type, ast.Name):
                noms = [h.type.id]
            elif isinstance(h.type, ast.Tuple):
                noms = [x.id for x in h.type.elts if isinstance(x, ast.Name)]
            if any(x in ("ImportError", "ModuleNotFoundError") for x in noms):
                attrape = True
        if attrape:
            for sub in ast.walk(n):
                gardes.add(id(sub))
    std = sys.stdlib_module_names
    trouves, inconnues = {}, []
    for n in ast.walk(arbre):
        modules = []
        if isinstance(n, ast.Import):
            modules = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            modules = [n.module]
        for mod in modules:
            racine = mod.split(".")[0]
            if racine in std:
                continue
            if racine not in DISTRIBUTION:
                inconnues.append("%s (l.%d)" % (mod, n.lineno))
                continue
            dist = DISTRIBUTION[racine]
            gardee = id(n) in gardes
            vu = trouves.get(dist)
            # ⚠️ UN MODULE IMPORTE DEUX FOIS EST GARDE **SI ET SEULEMENT SI**
            #    TOUS SES IMPORTS LE SONT : une seule occurrence nue suffit a
            #    faire sortir la trace, et c'est ce cas-la qu'on publie.
            if vu is None:
                trouves[dist] = {"module": mod, "gardee": gardee,
                                 "ligne": n.lineno}
            elif not gardee and vu["gardee"]:
                trouves[dist] = {"module": mod, "gardee": False,
                                 "ligne": n.lineno}
    return trouves, sorted(set(inconnues))


def adresse_lhm(src):
    """L'hote, le port et le chemin de LHM, **LUS DANS LE PRODUIT**.

    🎯 LE PATRON EST CELUI DE `tools/dn_lhm_tour.ps1:122-128` : le port de LHM
       est une valeur de L'AGENT, ⛔ pas une constante de plus."""
    if not src:
        return None
    h = re.search(r'^LHM_HOTE\s*=\s*"([^"]+)"', src, re.M)
    p = re.search(r"^LHM_PORT\s*=\s*(\d+)", src, re.M)
    c = re.search(r'^LHM_CHEMIN\s*=\s*"([^"]+)"', src, re.M)
    if not (h and p and c):
        return None
    return h.group(1), int(p.group(1)), c.group(1)


# ═══════════════ LIRE LE PRODUIT — DES NOMS, ⛔ PAS DES LIGNES ════════════

def source_fonction(src, nom):
    """Le SOURCE d'une fonction Python, ⛔ pas le fichier entier.

    🔴 UN CONTROLE QUI BALAIE TOUT LE FICHIER MESURE LE VOISINAGE, ⛔ pas la
       fonction : `manquantes.append` existe DEUX fois dans ce produit, dans
       DEUX fonctions differentes."""
    try:
        arbre = ast.parse(src or "")
    except (SyntaxError, ValueError):
        return "", None
    for n in ast.walk(arbre):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == nom:
            return (ast.get_source_segment(src, n) or ""), n
    return "", None


def cles_du_retour(noeud):
    """Les cles LITTERALES des dicts rendus par une fonction."""
    out = set()
    if noeud is None:
        return out
    for n in ast.walk(noeud):
        if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict):
            for k in n.value.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    out.add(k.value)
    return out


def trois_positions(noeud):
    """La fonction sait-elle rendre `None` **ET** autre chose que `None` ?

    ⚠️ `None` ⛔ N'EST PAS `False`, et c'est le correctif du 2026-09-08 que ce
       controle empeche de perdre : `bool(ok)` ecrasait « la sonde n'a pas pu
       tourner » sur « le module est ABSENT »."""
    if noeud is None:
        return False, False
    nul, autre = False, False
    for n in ast.walk(noeud):
        if not isinstance(n, ast.Return):
            continue
        v = n.value
        if v is None or (isinstance(v, ast.Constant) and v.value is None):
            nul = True
        else:
            autre = True
    return nul, autre


def appends_hors_boucle(noeud, liste, iterable):
    """Les `<liste>.append(...)` de la fonction QUI NE SONT PAS dans la boucle
    sur `<iterable>`.

    🔴 C'EST LE GARDE DU `6` : `manquantes` commande A LA FOIS le code de
       sortie du pre-vol ET le bloc qui publie `GESTE_DEPENDANCES`. Un append
       venu d'ailleurs ferait imprimer `pip install …` pour une dependance qui
       ⛔ n'est PAS un module pip."""
    if noeud is None:
        return None
    dedans, total = set(), []
    for n in ast.walk(noeud):
        if (isinstance(n, ast.For) and isinstance(n.iter, ast.Name)
                and n.iter.id == iterable):
            for sub in ast.walk(n):
                dedans.add(id(sub))
    for n in ast.walk(noeud):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "append"
                and isinstance(n.func.value, ast.Name)
                and n.func.value.id == liste):
            total.append((n.lineno, id(n) in dedans))
    return [l for l, ok in total if not ok]


def bloc_lhm_ps1(ps1):
    """Le bloc LHM de l'outil, borne par SES DEUX marqueurs ASCII."""
    return region(ps1, A_LHM_DEBUT, A_LHM_FIN)


def lignes_de(page, motif):
    """Les `<div class="ligne">` de la section d'ecart qui portent `motif`."""
    out = []
    for m in RE_LIGNE_PAGE.finditer(page or ""):
        if motif in m.group(1):
            out.append(m.group(1))
    return out


def par_langue(fragment, code):
    """Ce que le lecteur d'UNE langue voit, et LUI SEUL.

    🔴 UNE PAGE BILINGUE MISE DANS UN SEUL SAC NE GARDE NI L'UNE NI L'AUTRE, ET
       C'EST MESURE LE 2026-09-10 : remettre **la seule moitie anglaise** de la
       ligne « sans garde » a `websockets` seul laissait le controle VERT — le
       defaut meme que cette marche ferme, rejoue pour les anglophones. C'est
       MOT POUR MOT le constat de `dn7-2-2` (« le texte anglais disait de
       cliquer *Connexion* »). ⇒ la population se DECOUPE, et l'egalite est
       exigee DANS CHAQUE LANGUE.
    ⚠️ Les elements de langue de cette page ⛔ ne s'imbriquent pas : un
       non-greedy jusqu'au premier `</span>` rend donc le contenu ENTIER."""
    return "\n".join(re.findall(
        r'<span lang="%s">(.*?)</span>' % re.escape(code), fragment or "",
        re.S))


def distributions_citees(fragment):
    """Les distributions nommees dans un `<code>` de ce fragment."""
    connues = set(DISTRIBUTION.values())
    return set(j.strip() for j in RE_CODE.findall(fragment or "")
               if j.strip() in connues)


def sans_commentaires_pleine_ligne(txt):
    """Le fichier SANS ses lignes de commentaire — ⛔ ce qui S'EXECUTE.

    🔴 UN MIROIR EST UNE **SECONDE SOURCE DE VERITE**, ⛔ pas une mention. Un
       commentaire qui ECRIT l'adresse pour expliquer pourquoi elle est lue
       ailleurs ⛔ ne divergera jamais de rien : il ne s'execute pas. Sans ce
       retrait, `(c3)` rougissait sur la prose qui documente `(c3)` lui-meme —
       une gate qui epingle sa propre explication prouve un `grep`, ⛔ pas une
       propriete. C'est la meme lecon que `sans_commentaires` cote script.
    ⚠️ SEULES LES LIGNES **ENTIERES** de commentaire tombent (`#` en tete). Un
       `# …` en fin de ligne de code RESTE dans la population : conservateur
       par choix, pour ⛔ ne pas rogner une chaine qui contiendrait un `#`."""
    return "\n".join(l for l in (txt or "").split("\n")
                      if not l.lstrip().startswith("#"))


def commutateurs_du_geste(geste):
    """Les `-Xxx` que le geste publie — DERIVES de la chaine, ⛔ pas ecrits."""
    return [m.group(1) for m in RE_COMMUTATEUR.finditer(" " + (geste or ""))]


# ═══════════════════════ LES MUTANTS ══════════════════════════════════════

def muter(etat):
    """REPLANTE une faute DANS L'ETAT — ⛔ jamais dans un fichier du depot.

    🔴 TOUTE mutation passe par cet unique etat, et `main()` compare l'etat
       AVANT/APRES : la garde du no-op est donc UNIVERSELLE.
    ⚠️ MAIS ELLE N'EST ATTEINTE QUE SI LE CORPS **REND**. Un corps qui `split`,
       indexe ou depaquette sur une ancre disparue LEVE, et le `try` de `main()`
       le rend en `rc=1` + `BILAN` + `[KO ]` — MOT POUR MOT le contrat que la
       campagne appelle « sain » : un mutant PERIME passerait pour un gardien
       vivant. ⇒ tout corps VERIFIE son ancre d'abord et rend `e` INCHANGE.
       ⛔ Le mutant 18 leve EXPRES : il est le temoin de ce cas."""
    e = copy.deepcopy(etat)
    p, r = e["fichiers"], e["regles"]
    page = p.get(PAGE, "")
    py = p.get(PY, "")
    ps1 = p.get(OUTIL, "")
    ps1_lhm = p.get(OUTIL_LHM, "")
    agent = p.get(AGENT, "")

    if _MUTANT == 1:
        a = "\nimport argparse\n"
        if a not in agent:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[AGENT] = agent.replace(a, "\nimport argparse\nimport numpy\n", 1)
    elif _MUTANT == 2:
        if A_AGENT_PY not in py:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = py.replace(A_AGENT_PY, '"/introuvable/dn_agent.py"', 1)
    elif _MUTANT == 3:
        # ⚠️ L'ANCRE EST LA **LIGNE DE CODE**, ⛔ pas la sous-chaine : le
        #    fichier cite `PORT_DEMANDE = 0` DANS UN COMMENTAIRE quatre
        #    lignes plus haut. MESURE le 2026-09-10 : ancre sur la
        #    sous-chaine, l'insertion coupait le commentaire en deux, le
        #    module cessait de s'analyser, et le mutant faisait rougir
        #    QUATRE controles de plus — il ne replantait plus une faute, il
        #    CASSAIT le fichier. Un mutant qui casse ne prouve rien.
        a = "\nPORT_DEMANDE = 0\n"
        if a not in py:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        # ⚠️ LE MIROIR EST POSE DANS DU CODE VIVANT, ⛔ pas dans un commentaire :
        #    un litteral pose en prose prouverait un `grep`, ⛔ pas la propriete.
        p[PY] = py.replace(a, a + "\nLHM_PORT_MIROIR = 8085", 1)
    elif _MUTANT == 4:
        ecart = region(page, A_SECTION_ECART, A_FIN_SECTION)
        if A_NOM_LHM not in ecart:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = page.replace(
            ecart, ecart.replace(A_NOM_LHM, "LibreSondeMoniteur"), 1)
    elif _MUTANT == 5:
        a = "        import serial"
        if a not in agent:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[AGENT] = agent.replace(a, "        serial = None", 1)
    elif _MUTANT == 6:
        a = 'DEPENDANCES_AGENT = ("psutil", "pyserial")'
        if a not in py:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = py.replace(a, 'DEPENDANCES_AGENT = ("psutil",)', 1)
    elif _MUTANT == 7:
        cibles = lignes_de(page, A_SANS_GARDE_FR)
        if not cibles:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        neuf = page
        for bloc in cibles:
            neuf = neuf.replace(bloc, bloc.replace("pyserial", "websockets"), 1)
        if neuf == page:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = neuf
    elif _MUTANT == 8:
        if A_GESTE_PIP not in py:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = py.replace(A_GESTE_PIP, A_GESTE_PIP + " lhm", 1)
    elif _MUTANT == 9:
        m = RE_CHAMPS.search(page)
        if not m or A_CHAMP_LHM not in m.group(1):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        dedans = m.group(1)
        p[PAGE] = page.replace(
            dedans, re.sub(r',\s*"v-lhm"', "", dedans, count=1), 1)
    elif _MUTANT == 10:
        src, _n = source_fonction(py, A_SONDE_PY)
        if not src or "return None" not in src:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = py.replace(src, src.replace("return None", "return False"), 1)
    elif _MUTANT == 11:
        src, _n = source_fonction(py, "prevol")
        if not src or "if manquantes:" not in src:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        neuf = src.replace(
            "    if manquantes:",
            "    if lhm is False:\n        manquantes.append(\"lhm\")\n"
            "    if manquantes:", 1)
        if neuf == src:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = py.replace(src, neuf, 1)
    elif _MUTANT == 12:
        # 🔴 IL **REPLANTE** LE REFUS DUR, ⛔ il ne debranche aucune garde :
        #    le bloc LHM se remet a sortir en `12` au lieu de degrader. C'est
        #    la regression exacte que `dn4-48` repare, et elle est REELLE —
        #    `tools/dn-agent.bat:112` fait `if errorlevel 1 goto :FIN` juste
        #    apres, donc l'agent ne demarrerait PAS.
        bloc = bloc_lhm_ps1(ps1)
        a12 = "            $LhmDegrade = $true"
        if not bloc or a12 not in bloc:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[OUTIL] = ps1.replace(
            bloc, bloc.replace(a12, "            exit 12\n" + a12, 1), 1)
    elif _MUTANT == 13:
        bloc = bloc_lhm_ps1(ps1)
        if not bloc or "Invoke-WebRequest" not in bloc:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        neuf = bloc.replace(
            "Invoke-WebRequest",
            "Get-Process -Name 'LibreHardwareMonitor' #", 1)
        p[OUTIL] = ps1.replace(bloc, neuf, 1)
    elif _MUTANT == 14:
        a = "\nPORT_DEMANDE = 0\n"
        if a not in py:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = py.replace(a, a + '\nARGUMENTS_LHM = ["-Verb", "RunAs"]', 1)
    elif _MUTANT == 15:
        # ⚠️ LA CIBLE EST **VIDEE**, ⛔ la cle n'est pas supprimee : supprimer la
        #    cle ferait AUSSI diverger `CIBLES` et `MUTANTS`, donc rougir (c16)
        #    — un mutant qui vise deux controles a la fois n'en garde bien
        #    aucun. Vider la valeur orpheline le controle vise, et LUI SEUL.
        # ⚠️ LA CLE VISEE EST CELLE D'UN MUTANT **UNIQUE** SUR SON CONTROLE.
        #    MESURE le 2026-09-10 : vider une cible que d'AUTRES mutants
        #    couvrent laisse `(c14)` VERT — le mutant sortait en rc=0 et
        #    ne gardait plus rien. Le mutant 14 est le SEUL a viser `c13`.
        if not e["cibles"].get(14):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        e["cibles"][14] = ()
    elif _MUTANT == 16:
        if 1 not in e["cibles"]:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        e["cibles"][1] = ("c1", "c99")
    elif _MUTANT == 17:
        if 999 in e["cibles"]:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        e["cibles"][999] = ("c1",)
    elif _MUTANT == 18:
        # 🔴 LE TEMOIN DU MUTANT MORT : il LEVE EXPRES. Sans lui, « un corps qui
        #    leve se rend en KO » serait une regle ecrite que rien ne joue.
        raise RuntimeError("temoin : ce mutant LEVE, et c'est son objet")
    elif _MUTANT == 19:
        r["sortie_anticipee"] = True
    elif _MUTANT == 20:
        bloc = bloc_lhm_ps1(ps1)
        if not bloc:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[OUTIL] = ps1.replace(A_LHM_DEBUT + bloc + A_LHM_FIN, "", 1)
    elif _MUTANT == 21:
        src, _n = source_fonction(py, "prevol")
        if not src or "GESTE_LHM" not in src:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        neuf = re.sub(r"(?m)^.*GESTE_LHM.*\n", "", src)
        if neuf == src:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = py.replace(src, neuf, 1)
    elif _MUTANT == 22:
        a = "except ImportError:"
        if a not in agent:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[AGENT] = agent.replace(a, "except OSError:", 1)
    elif _MUTANT == 23:
        # 🔴 IL **REPLANTE** LA FAUTE, ⛔ il ne debranche pas la garde : la
        #    parade DISPARAIT de la tache pendant que le README, le CHANGELOG
        #    et le ledger continuent de publier « 3 reprises a 1 minute ».
        #    C'est exactement la forme sous laquelle le defaut serait
        #    introduit un jour — un reglage retire « parce qu'il ne servait
        #    plus », sur une page qui pretend encore que la parade tient.
        if A_RESTART not in ps1:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[OUTIL] = ps1.replace(A_RESTART, "", 1)
    elif _MUTANT == 24:
        # 🔴 LA FAUTE EST REPLANTEE **DANS LE SCRIPT**, ⛔ pas dans le geste :
        #    c'est ce sens-la qui a ete DEMONTRE vert le 2026-09-10, et c'est
        #    le plus dangereux — quatre surfaces publient un geste qui ne se
        #    branche plus, et aucune d'elles n'a change d'un caractere.
        if "[switch] $Poser," not in ps1_lhm:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[OUTIL_LHM] = ps1_lhm.replace("[switch] $Poser,",
                                       "[switch] $Installer,", 1)
    elif _MUTANT == 25:
        ecart = region(page, A_SECTION_ECART, A_FIN_SECTION)
        a25 = "-Poser -Permanence tache"
        if a25 not in ecart:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = page.replace(ecart, ecart.replace(a25, "-Poser"), 1)
    elif _MUTANT == 26:
        # 🔴 **LA SEULE MOITIE ANGLAISE**, ⛔ pas la ligne : c'est la forme
        #    EXACTE qui sortait verte, et c'est mot pour mot le constat de
        #    `dn7-2-2` (« le texte anglais disait de cliquer *Connexion* »).
        # ⚠️ TOUTES les moities `en` de la ligne, ⛔ pas la premiere : la gate
        #    lit la CONCATENATION de ce qu'un lecteur voit. Un seul
        #    `<code>pyserial</code>` laisse ailleurs suffit a la reverdir —
        #    demontre le 2026-09-10 sur la 1re redaction de ce mutant.
        ecart = region(page, A_SECTION_ECART, A_FIN_SECTION)
        cible26 = None
        for m26 in RE_LIGNE_PAGE.finditer(ecart):
            if A_SANS_GARDE_FR in par_langue(m26.group(1), "fr"):
                cible26 = m26.group(1)
                break
        if not cible26 or "<code>pyserial</code>" not in cible26:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        neuf26 = cible26
        for x in re.findall(r'<span lang="en">(.*?)</span>', cible26, re.S):
            if "<code>pyserial</code>" in x:
                neuf26 = neuf26.replace(
                    x, x.replace("<code>pyserial</code>",
                                 "<code>websockets</code>"), 1)
        if neuf26 == cible26:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = page.replace(cible26, neuf26, 1)
    elif _MUTANT == 27:
        ecart = region(page, A_SECTION_ECART, A_FIN_SECTION)
        neuf27 = ecart
        for x in re.findall(r'<span lang="en">(.*?)</span>', ecart, re.S):
            if A_NOM_LHM in x:
                neuf27 = neuf27.replace(
                    x, x.replace(A_NOM_LHM, "the monitoring tool"), 1)
        if neuf27 == ecart:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = page.replace(ecart, neuf27, 1)
    elif _MUTANT == 28:
        road = p.get(ROADMAP, "")
        m28 = RE_BORNE_EN.search(road)
        if not m28:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[ROADMAP] = road.replace(m28.group(0), "5 restarts, 1 minute apart", 1)
    elif _MUTANT == 31:
        # 🔴 IL REPLANTE LA FAUTE : le retour de la surface cesse d'etre JETE,
        #    et une surface ABSENTE redevient un ECART. Sur une edition
        #    Familiale de Windows — ⛔ pas de `msg.exe` — le pre-vol refuserait
        #    de nouveau, et l'agent serait PERDU exactement comme le 2026-09-12.
        #    ⛔ Ce n'est pas un debranchement : la fonction reste entiere, c'est
        #    l'APPELANT qui se remet a en dependre.
        if A_RETOUR_JETE not in ps1:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[OUTIL] = ps1.replace(
            A_RETOUR_JETE,
            "if (-not (Prevenir-Windows", 1)
    elif _MUTANT == 30:
        # 🔴 LA RECIPROQUE DU 12, ET ELLE REPLANTE UNE **AUTRE** FAUTE :
        #    `poser` cesse de dire que l'agent tourne SANS LHM. La page
        #    annoncerait alors « la tache est POSEE ET VERIFIEE, et l'agent
        #    tourne » sur une machine dont quatre champs resteront a « -- »
        #    pour toujours — un SUCCES FAUX, pire qu'un echec.
        cas = region(ps1, A_CAS_POSER, A_CAS_APRES_POSER)
        if not cas or "            exit 12" not in cas:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[OUTIL] = ps1.replace(
            cas, cas.replace("            exit 12", "            exit 0", 1), 1)
    elif _MUTANT == 29:
        # 🔴 LE DEFAUT EXACT DEMONTRE LE 2026-09-10, REPLANTE MOT POUR MOT :
        #    il laissait TOUTES les gates vertes parce que le mot « status »
        #    suffisait au controle. Un mot ⛔ n'est pas une propriete.
        a29 = "return rep.status == 200 and bool(RE_MARQUE_LHM.search(corps))"
        if a29 not in py:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = py.replace(a29, "return rep.status != 500", 1)
    else:
        raise AssertionError("mutant %d declare mais SANS CORPS" % _MUTANT)
    return e


# ═══════════════════════════ LA RECIPROQUE ═════════════════════════════════

def _texte_litteral(n):
    """La partie LITTERALE d'un libelle, meme construit par formatage."""
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Mod, ast.Add)):
        return _texte_litteral(n.left)
    if isinstance(n, ast.JoinedStr) and n.values:
        return _texte_litteral(n.values[0])
    return None


def ids_par_ast():
    """Les identifiants de TOUS les controles de CE fichier, lus A L'AST.

    🔴 POURQUOI PAS L'ENSEMBLE DES IDENTIFIANTS DEJA EMIS : cet ensemble est
       fige AU MOMENT DE L'APPEL de la reciproque. Tout controle ajoute APRES
       ce bloc en sortirait INVISIBLE."""
    try:
        with io.open(os.path.abspath(__file__), encoding="utf-8") as fh:
            arbre = ast.parse(fh.read())
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    out = set()
    for n in ast.walk(arbre):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "ctrl" and len(n.args) >= 2):
            m = RE_ID_CTRL.match(_texte_litteral(n.args[1]) or "")
            if m:
                out.add(m.group(1))
    return out or None


def main():
    global _MUTANT
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--mutant", type=int, default=None,
                    help="REPLANTE une faute EN MEMOIRE pour prouver que le "
                         "controle correspondant sait ROUGIR")
    ap.add_argument("--liste-mutants", action="store_true",
                    help="dit ce que chaque mutant replante, et sort")
    args = ap.parse_args()
    if args.mutant is not None and args.mutant not in MUTANTS:
        # ⛔ PAS une sortie par exception, qui rendrait 1 et se confondrait
        #    avec un vrai defaut : un mutant inconnu est une ERREUR D'APPEL.
        print("MUTANT %d INCONNU : il n'est pas declare. ⛔ Un mutant qui "
              "n'existe pas ne prouve RIEN — ⛔ ne pas conclure que le "
              "controle est vert." % args.mutant, file=sys.stderr)
        return 2
    _MUTANT = args.mutant or 0

    if args.liste_mutants:
        for n in sorted(MUTANTS):
            print("  %2d  [%s]  %s"
                  % (n, ",".join(CIBLES.get(n, ())) or "—", MUTANTS[n]))
        return 0

    print("=" * 78)
    print("dn7-5 — L'ECART DECLARE SE RE-DERIVE, ET LHM EST UN PREREQUIS DUR"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)
    print("cibles     : %s" % " · ".join(FIXES))
    print("⛔ CETTE GATE EST STRUCTURELLE : elle N'INSTALLE PAS LHM, n'ouvre")
    print("   aucun navigateur, ne lance aucune tache et n'emet AUCUNE requete")
    print("   reseau. Elle prouve que LE MECANISME EST BRANCHE, ⛔ pas qu'une")
    print("   tour sans LHM DEGRADE — ce fait se ferme a l'œil owner, cote")
    print("   Windows, ou l'agent VIVANT est verifie (`mesures/dn4-48`).")
    print("   ⚠️ `mesures/dn7-5/T2` fermait le REFUS : il ⛔ n'est PAS efface,")
    print("      il dit ce que le produit faisait du 09-10 au 09-12.")

    # ── (c0) LE PRE-VOL : LES FICHIERS SE LISENT ────────────────────────
    print("\n── (c0) LE PRE-VOL — ⛔ AUCUN CONTROLE SUR DU VIDE ────────────────")
    fichiers = {}
    illisibles = []
    for c in FIXES:
        x = lire(c)
        if x is None:
            illisibles.append(c)
        else:
            fichiers[c] = x
    if not ctrl(not illisibles, "(c0) tout fichier attendu est LISIBLE",
                "%d fichier(s) lus" % len(fichiers) if not illisibles
                else "⛔ ILLISIBLE(S) : %s" % " ".join(illisibles)):
        return bilan(1, "un fichier attendu est illisible")

    for n in sorted(MUTANTS):
        if not ctrl(bool(CIBLES.get(n)) and bool(MUTANTS.get(n)),
                    "(c0) le mutant %d a une CIBLE et un LIBELLE" % n,
                    "→ %s" % ",".join(CIBLES.get(n, ()))
                    if CIBLES.get(n) else "⛔ cible ou libelle manquant"):
            return bilan(1, "un mutant est declare a moitie")

    etat = {"fichiers": fichiers,
            "regles": {"sortie_anticipee": False},
            "cibles": dict(CIBLES)}

    # 🔴 UN MUTANT QUI MEURT SORTIRAIT EN TRACEBACK, SANS `BILAN` — or « pas
    #    de BILAN » est le discriminant d'une gate MORTE. ⇒ il se rend en KO.
    try:
        neuf = muter(etat) if _MUTANT else etat
    except Exception as exc:                              # noqa: BLE001
        ctrl(False, "(c0) le mutant %d a une CIBLE et un CORPS" % _MUTANT,
             "⛔ %s: %s — la faute est dans le MUTANT, ⛔ pas dans la gate"
             % (type(exc).__name__, str(exc)[:80]))
        return bilan(1, "le mutant %d n'a pas pu s'appliquer" % _MUTANT)
    if _MUTANT and neuf == etat:
        ctrl(False, "(c0) le mutant %d a bien un EFFET" % _MUTANT,
             "⛔ SANS EFFET — son ancre litterale a disparu de la cible. "
             "⛔ Ce n'est PAS un controle vert : rc=3, mutant PERIME.")
        return bilan(3, "le mutant %d n'a eu aucun effet" % _MUTANT)

    page = neuf["fichiers"].get(PAGE, "")
    py = neuf["fichiers"].get(PY, "")
    ps1 = neuf["fichiers"].get(OUTIL, "")
    agent = neuf["fichiers"].get(AGENT, "")
    readme = neuf["fichiers"].get(LISEZMOI, "")
    ps1_lhm = neuf["fichiers"].get(OUTIL_LHM, "")
    regles = neuf["regles"]
    cibles = neuf["cibles"]

    ecart_page = region(page, A_SECTION_ECART, A_FIN_SECTION)
    ecart_readme = section_ecart_readme(readme)
    bloc_ps1 = bloc_lhm_ps1(ps1)

    # ── (c1) LA DERIVATION, A L'AST ─────────────────────────────────────
    print("\n── (c1) LES DEPENDANCES DE L'AGENT SONT **DERIVEES** ─────────────")
    derive, inconnues = deps_agent(agent)
    ok = derive is not None and not inconnues and len(derive) > 0
    ctrl(ok, "(c1) les dependances tierces sont derivees a l'AST",
         "%s" % " · ".join(
             "%s%s" % (d, "" if v["gardee"] else " (SANS GARDE)")
             for d, v in sorted(derive.items())) if ok
         else "⛔ %s — une racine tierce sans entree dans la table `module → "
              "distribution` est une dependance que RIEN ne nomme, et c'est "
              "exactement le defaut qui ⛔ ne doit pas se rejouer en silence"
              % ("`agent/dn_agent.py` ne s'analyse pas a l'AST"
                 if derive is None else
                 "racine(s) tierce(s) HORS TABLE : %s" % " · ".join(inconnues)
                 if inconnues else "AUCUNE dependance tierce derivee"))
    derive = derive or {}

    # ── (c2)(c3) L'ADRESSE DE LHM VIENT DU PRODUIT ──────────────────────
    print("\n── (c2)(c3) L'ADRESSE DE LHM EST **LUE**, ⛔ JAMAIS RECOPIEE ─────")
    cible = adresse_lhm(agent)
    src_cible, n_cible = source_fonction(py, A_CIBLE_PY)
    lit_py = bool(src_cible) and A_AGENT_PY in py and all(
        j in src_cible for j in ("LHM_HOTE", "LHM_PORT", "LHM_CHEMIN"))
    lit_ps1 = bool(bloc_ps1) and "$AGENT" in bloc_ps1 and all(
        j in bloc_ps1 for j in ("LHM_HOTE", "LHM_PORT", "LHM_CHEMIN"))
    ok = cible is not None and lit_py and lit_ps1
    ctrl(ok, "(c2) les 2 sondes LISENT l'adresse dans l'agent",
         "%s:%d%s, lu dans `%s` par les deux" % (cible + (AGENT,)) if ok
         else "⛔ %s — deux sources de verite divergeront, et la seconde "
              "pourrira EN SILENCE le jour ou l'owner joue un autre port"
              % ("`agent/dn_agent.py` ne publie pas LHM_HOTE/PORT/CHEMIN"
                 if cible is None else
                 "`%s` ne relit pas l'agent" % PY if not lit_py else
                 "le bloc LHM de `%s` ne relit pas l'agent" % OUTIL))

    miroirs = []
    if cible is not None:
        hote, port, chemin = cible
        for f in CODE_INSTALLEUR + (OUTIL,):
            txt = sans_commentaires_pleine_ligne(neuf["fichiers"].get(f, ""))
            # ⚠️ LE BLOC QUI **LIT** LE PRODUIT CITE FORCEMENT LES NOMS DES
            #    CONSTANTES ; ce qu'on refuse, ce sont leurs **VALEURS**.
            if re.search(r"(?<![\w.])%d(?![\w.])" % port, txt):
                miroirs.append("%s : le port %d" % (f, port))
            if chemin in txt:
                miroirs.append("%s : le chemin %s" % (f, chemin))
    ctrl(cible is not None and not miroirs,
         "(c3) ⛔ aucun miroir de l'adresse LHM hors du produit",
         "port et chemin cherches dans %d fichier(s)"
         % (len(CODE_INSTALLEUR) + 1) if cible is not None and not miroirs
         else "⛔ %s — le patron du depot est `dn_lhm_tour.ps1:122-128` : "
              "la valeur est LUE dans l'agent, ⛔ jamais recopiee"
              % (" · ".join(miroirs) if miroirs
                 else "l'adresse ne se lit pas dans l'agent"))

    # ── (c4)(c5)(c6) LA PROSE COUVRE EXACTEMENT LE DERIVE ───────────────
    print("\n── (c4)(c5)(c6) LES DEUX SENS, ET LES DEUX ENUMERATIONS ──────────")
    attendu = set(derive) | ({A_NOM_LHM} if cible is not None else set())
    # 🔴 LA PAGE SE LIT **LANGUE PAR LANGUE**, ⛔ pas en bloc : `ecart_page`
    #    entier laisserait passer un nom publie EN FRANCAIS SEULEMENT.
    manque_page = sorted(
        "%s(%s)" % (d, lg) for lg in ("en", "fr") for d in attendu
        if d not in par_langue(ecart_page, lg))
    manque_readme = sorted(d for d in attendu if d not in ecart_readme)
    # SENS 2 : une distribution de la table QUE L'AGENT N'IMPORTE PLUS et
    # qu'une surface nomme encore. Le vocabulaire est la TABLE, ⛔ pas la prose.
    fantomes = sorted(d for d in set(DISTRIBUTION.values()) - set(derive)
                      if d in ecart_page or d in ecart_readme)
    ok = (bool(ecart_page) and bool(ecart_readme) and not manque_page
          and not manque_readme and not fantomes)
    ctrl(ok, "(c4) page ⇄ README ⇄ derive, DANS LES DEUX SENS",
         "%d dependance(s) nommee(s) des deux cotes" % len(attendu) if ok
         else "⛔ %s — un ecart declare INCOMPLET envoie l'inconnu monter un "
              "agent dont une part ne se remplira JAMAIS"
              % ("la section d'ecart de la page ne se delimite pas"
                 if not ecart_page else
                 "celle du README ne se delimite pas" if not ecart_readme else
                 "SENS 2 — nommee(s) mais PLUS importee(s) : %s"
                 % " · ".join(fantomes) if fantomes else
                 "SENS 1 — absente(s) de la page : %s · du README : %s"
                 % (" ".join(manque_page) or "—",
                    " ".join(manque_readme) or "—")))

    m_deps = re.search(re.escape(A_DEPS) + r"([^)]*)\)", py)
    enum_py = set(re.findall(r'"([a-z0-9_]+)"', m_deps.group(1))) if m_deps else set()
    m_ps1 = re.search(r'-c\s+"import ([^"]+)"', ps1)
    enum_ps1 = set()
    if m_ps1:
        enum_ps1 = set(DISTRIBUTION.get(x.strip(), x.strip())
                       for x in m_ps1.group(1).split(","))
    ok = (bool(enum_py) and enum_py == enum_ps1
          and enum_py.issubset(set(derive)))
    ctrl(ok, "(c5) les 2 enumerations EXECUTABLES sont appariees",
         "%s, des deux cotes, et sous-ensemble du derive"
         % " ".join(sorted(enum_py)) if ok
         else "⛔ serveur=%s outil=%s derive=%s — elles ⛔ ne se sont JAMAIS "
              "parle avant cette marche, et une sonde qui teste ce que "
              "l'agent n'importe plus est un chiffre a croire sur parole"
              % (" ".join(sorted(enum_py)) or "—",
                 " ".join(sorted(enum_ps1)) or "—",
                 " ".join(sorted(derive)) or "—"))

    non_gardees = set(d for d, v in derive.items() if not v["gardee"])
    # 🔴 DEUX POPULATIONS, ⛔ PAS UNE : le lecteur anglais et le lecteur
    #    francais ne voient pas le meme texte, et une regression sur UNE moitie
    #    est un defaut ENTIER pour ceux qui la lisent.
    dits = {}
    for lg, marque in (("en", A_SANS_GARDE_EN), ("fr", A_SANS_GARDE_FR)):
        vu = set()
        trouve = False
        for bloc in RE_LIGNE_PAGE.finditer(ecart_page or ""):
            moitie = par_langue(bloc.group(1), lg)
            if marque in moitie:
                trouve = True
                vu |= distributions_citees(moitie)
        dits[lg] = vu if trouve else None
    ecarts_lg = sorted(lg for lg in ("en", "fr")
                       if dits[lg] is None or dits[lg] != non_gardees)
    ok = not ecarts_lg and bool(non_gardees)
    ctrl(ok, "(c6) « sans garde » couvre les non gardees, PAR LANGUE",
         "en=%s · fr=%s" % (" ".join(sorted(dits["en"] or ())),
                            " ".join(sorted(dits["fr"] or ()))) if ok
         else "⛔ derive=%s · %s — la page disait « sans garde » de "
              "`websockets` SEUL, et taisait le MEME defaut sur `pyserial`, "
              "importe dans la branche du REGIME NORMAL. ⛔ Une moitie de "
              "page corrigee ⛔ n'en corrige PAS l'autre"
              % (" ".join(sorted(non_gardees)) or "—",
                 " · ".join(
                     "%s=%s" % (lg, "AUCUNE LIGNE" if dits[lg] is None
                                else " ".join(sorted(dits[lg])) or "—")
                     for lg in ecarts_lg) or "aucune dependance non gardee"))

    # ── (c7)(c8) LE GESTE DE LHM EST LE SIEN, ET LA LIGNE EXISTE ────────
    print("\n── (c7)(c8) LE GESTE PROPRE DE LHM, ET SON CHAMP ─────────────────")
    pres = [x for x in RE_PRE.findall(ecart_page)]
    pip_pur = [x for x in pres if A_GESTE_PIP in x
               and "lhm" not in x.lower() and A_NOM_LHM not in x]
    lhm_pur = [x for x in pres if A_GESTE_LHM in x and "pip" not in x.lower()]
    m_pip = re.search(r'GESTE_DEPENDANCES = "([^"]*)"', py)
    m_lhm = re.search(r'GESTE_LHM = "([^"]*)"', py)
    geste_ref = m_lhm.group(1).replace("\\\\", "\\") if m_lhm else ""
    geste_py = (A_GESTE_LHM in py and m_pip is not None
                and "lhm" not in m_pip.group(1).lower())
    # 🔴 (a) LE GESTE EST **BINDABLE** — chaque commutateur qu'il publie existe
    #    dans le `param(` du script qu'il nomme. DEMONTRE le 2026-09-10 :
    #    renommer `-Poser` en `-Installer` laissait CINQ gates vertes pendant
    #    que le geste devenait injouable sur QUATRE surfaces d'un coup.
    param = RE_PARAM_PS1.search(ps1_lhm)
    inconnus = ([c for c in commutateurs_du_geste(geste_ref)
                 if not re.search(r"\$%s\b" % re.escape(c), param.group(1))]
                if (param and geste_ref) else None)
    # 🔴 (b) LA MEME CHAINE, MOT POUR MOT, SUR LES TROIS SURFACES. `A_GESTE_PIP`
    #    a son appariement page ⇄ README par `(c12)/(c13)` de `dn71` ; celui-ci
    #    n'en avait AUCUN, et quatre surfaces a corriger sans gardien est
    #    exactement la forme sous laquelle on en oublie une.
    surfaces = {"page": bool(geste_ref) and geste_ref in ecart_page,
                "README": bool(geste_ref) and geste_ref in ecart_readme}
    desapp = sorted(k for k, v in surfaces.items() if not v)
    ok = (len(pip_pur) == 1 and len(lhm_pur) == 1 and geste_py
          and inconnus == [] and not desapp)
    ctrl(ok, "(c7) le geste de LHM est LE SIEN, et il est BINDABLE",
         "`%s` — %d commutateur(s) confronte(s) au `param(` de `%s`, chaine "
         "identique page ⇄ README ⇄ serveur"
         % (geste_ref, len(commutateurs_du_geste(geste_ref)), OUTIL_LHM)
         if ok
         else "⛔ %s — LHM ⛔ n'est PAS un module pip, et un geste que le "
              "script nomme ne peut pas reussir s'il ⛔ ne s'y branche pas"
              % ("le geste `pip` de la page nomme LHM"
                 if len(pip_pur) != 1 else
                 "la page ne publie pas le geste PROPRE de LHM"
                 if len(lhm_pur) != 1 else
                 "le serveur ne publie pas `%s`, ou son geste `pip` nomme LHM"
                 % A_GESTE_LHM if not geste_py else
                 "le `param(` de `%s` ne se lit pas" % OUTIL_LHM
                 if inconnus is None else
                 "commutateur(s) ABSENT(S) du `param(` de `%s` : %s"
                 % (OUTIL_LHM, " ".join("-" + c for c in inconnus))
                 if inconnus else
                 "la chaine du geste DIVERGE : absente de %s (le serveur "
                 "publie `%s`)" % (" et ".join(desapp), geste_ref)))

    m_champs = RE_CHAMPS.search(page)
    champs = set(re.findall(r'"([\w-]+)"', m_champs.group(1))) if m_champs else set()
    ids_ecart = set(re.findall(r'id="(v-[\w-]+)"', ecart_page))
    oublies = sorted(ids_ecart - champs)
    pose = 'poserMot("v-lhm", troisEtats(e.lhm,' in re.sub(r"\s+", " ", page)
    ok = (A_ID_LHM in ecart_page and not oublies and bool(champs) and pose)
    ctrl(ok, "(c8) la ligne LHM a son `id`, et il est dans `CHAMPS`",
         "%d champ(s) de l'ecart, tous repris" % len(ids_ecart) if ok
         else "⛔ %s — un `id` neuf oublie dans `CHAMPS` reste sur ses points "
              "de suspension POUR TOUJOURS, ce qui se lit « en cours » alors "
              "que c'est fini : un bug SILENCIEUX qu'⛔ aucune autre gate ne voit"
              % ("la page ne porte pas `%s`" % A_ID_LHM
                 if A_ID_LHM not in ecart_page else
                 "`CHAMPS` ne se lit pas" if not champs else
                 "id(s) HORS `CHAMPS` : %s" % " ".join(oublies) if oublies
                 else "la valeur n'est pas posee par `troisEtats`"))

    # ── (c9)(c10) L'ETAT, LE PRE-VOL, ET LE `6` QUI NE BOUGE PAS ────────
    print("\n── (c9)(c10) TROIS POSITIONS, ET LE `6` QUI ⛔ NE BOUGE PAS ──────")
    src_etat, n_etat = source_fonction(py, "etat_machine")
    src_sonde, n_sonde = source_fonction(py, A_SONDE_PY)
    cles = cles_du_retour(n_etat)
    nul, autre = trois_positions(n_sonde)
    ok = ("lhm" in cles and "geste_lhm" in cles and nul and autre
          and bool(src_sonde))
    ctrl(ok, "(c9) `etat_machine()` expose LHM a TROIS positions",
         "cles `lhm` et `geste_lhm`, sonde a 3 issues" if ok
         else "⛔ %s — `None` ⛔ n'est PAS `False` : publier une IGNORANCE "
              "comme un constat est la faute que `dn7-1` a deja payee pour "
              "`psutil`, et elle ⛔ ne se rejoue pas"
              % ("`%s()` est introuvable" % A_SONDE_PY if not src_sonde else
                 "cle(s) manquante(s) dans l'etat : %s"
                 % " ".join(sorted({"lhm", "geste_lhm"} - cles))
                 if not {"lhm", "geste_lhm"} <= cles else
                 "la sonde ⛔ ne rend pas `None`" if not nul
                 else "la sonde ne rend QUE `None`"))

    src_prevol, n_prevol = source_fonction(py, "prevol")
    hors = appends_hors_boucle(n_prevol, "manquantes", "DEPENDANCES_AGENT")
    imprime = ("GESTE_LHM" in src_prevol and A_SONDE_PY in src_prevol)
    ok = bool(src_prevol) and imprime and hors == []
    ctrl(ok, "(c10) `prevol()` IMPRIME LHM, hors de `manquantes`",
         "LHM a SON bloc et SON geste ; `manquantes` reste derive des modules"
         if ok
         else "⛔ %s — `manquantes` commande A LA FOIS le `6` ET le bloc qui "
              "publie `pip install …` : y verser LHM ferait imprimer LE "
              "MAUVAIS GESTE et bougerait un code que le README publie"
              % ("`prevol()` est introuvable" if not src_prevol else
                 "le pre-vol ⛔ n'imprime pas LHM" if not imprime else
                 "append(s) a `manquantes` HORS de la boucle sur "
                 "`DEPENDANCES_AGENT`, l.%s"
                 % " ".join(str(x) for x in (hors or []))))

    # ── (c11)(c18)(c12) LE PRE-VOL QUI **ATTEND**, ET LE CODE QUI RESTE ──
    # 🔴 AMENDE LE 2026-09-12 (`dn4-48`) — ET C'EST UNE **DECISION QUE
    #    L'OWNER A RENVERSEE SUR UNE MESURE**, ⛔ pas un assouplissement.
    #    `(c11)` gardait « le refus LHM sort en `exit 12` ». Ce refus ⛔
    #    N'EXISTE PLUS : au redemarrage du 2026-09-12 la tache au logon a tire
    #    a 18:13:13 et rendu `12` pendant que LHM montait a 18:13:34 — 21 s
    #    trop tard —, la reprise `RestartCount 3` ⛔ n'a PAS tire, et la dalle
    #    est restee MORTE toute la session sur une machine SAINE.
    #    ⇒ le bloc LHM **ATTEND** (borne `-AttenteLhm`), puis **DEGRADE**.
    # ⚠️ LE CONTROLE EST **COUPE EN DEUX**, ET C'EST LA LECON DEJA PAYEE ICI
    #    (voir `(b)` et `(h)` en tete) : un controle qui porte deux faits ⛔ ne
    #    peut pas dire LEQUEL a cede, et un mutant qui le vise ⛔ ne prouve
    #    rien de l'autre. `(c11)` garde le COMPORTEMENT du bloc ; `(c18)` garde
    #    le CODE `12` — son unicite ET son nouvel emetteur.
    print("\n── (c11)(c18)(c12) L'ATTENTE, LE CODE, ET CE QUI TRANCHE ─────────")
    codes = RE_EXIT.findall(ps1)
    codes_bloc = RE_EXIT.findall(bloc_ps1)
    cas = region(ps1, A_CAS_PREVOL, A_CAS_SUIVANT)
    i_deps = cas.find(A_SONDE_PS1)
    i_bloc = cas.find(A_LHM_DEBUT)
    i_inst = cas.find(A_INSTANCES)
    range_ok = bool(cas) and -1 < i_deps < i_bloc < i_inst
    # Les trois pieces de l'attente, cherchees DANS LE BLOC.
    manque_att = [n for n, a in (("la borne `-AttenteLhm`", A_BORNE),
                                 ("la ligne PAR TOUR", A_ATTENTE_TOUR),
                                 ("le pas de l'attente", A_ATTENTE_PAS),
                                 ("le pas DERIVE de la borne", A_PAS_DERIVE),
                                 ("le bandeau DEGRADE", A_DEGRADE),
                                 ("la surface Windows", A_SURFACE_WINDOWS))
                  if a not in bloc_ps1]
    ok = bool(bloc_ps1) and codes_bloc == [] and not manque_att and range_ok
    ctrl(ok, "(c11) le bloc LHM ATTEND, ⛔ il ne refuse plus",
         "⛔ aucune sortie dans le bloc ; attente bornee, ligne par tour, "
         "bandeau degrade et surface Windows presents" if ok
         else "⛔ %s — un pre-vol qui REFUSE sur LHM fait sauter `:EXEC` dans "
              "`tools/dn-agent.bat` (`if errorlevel 1 goto :FIN`, l.112), "
              "c'est-a-dire EXACTEMENT la panne du 2026-09-12, deplacee d'un "
              "cran : l'agent ne demarre pas, et la dalle reste MORTE"
              % ("le bloc LHM de l'outil ne se delimite pas" if not bloc_ps1
                 else "le bloc LHM porte encore une sortie : exit %s"
                 % ",".join(codes_bloc) if codes_bloc
                 else "piece(s) manquante(s) de l'attente : %s"
                 % " · ".join(manque_att) if manque_att else
                 "le bloc n'est pas ENTRE les dependances et le compte "
                 "d'instances — un pre-vol qui echoue ⛔ ne detruit rien"))

    # 🔴 `(c18)` — `12` A CHANGE D'EMETTEUR, ET IL RESTE **UNIQUE**.
    #    Ce qu'il veut dire a change avec lui : ⛔ plus « REFUS », mais
    #    « posee et **VIVANTE**, mais SANS LHM ». Le sens est garde ailleurs —
    #    `(c20)` de `tools/verif_preconditions_dn76.py` JOUE la table
    #    `CODES_POSER` et exige que `12` **nomme LibreHardwareMonitor**. Ici on
    #    garde la MECANIQUE : un seul `12`, et il sort du bon verbe.
    cas_poser = region(ps1, A_CAS_POSER, A_CAS_APRES_POSER)
    dans_poser = RE_EXIT.findall(cas_poser).count("12")
    ok = (codes.count("12") == 1 and dans_poser == 1 and "12" not in codes_bloc)
    ctrl(ok, "(c18) `12` est UNIQUE, et c'est `poser` qui le rend",
         "12 unique parmi %s, emis par le verbe `poser`"
         % ",".join(sorted(set(codes), key=int)) if ok
         else "⛔ %s — `4` porte DEJA DEUX SENS selon le verbe et `lancer` le "
              "neutralise en `0` ; et `12` rendu par le PRE-VOL avorterait le "
              "lancement, alors que rendu par `poser` il informe un appelant "
              "qui SAIT lire une table de codes"
              % ("le verbe `poser` ne se delimite pas" if not cas_poser
                 else "`12` apparait %d fois dans le fichier (attendu 1)"
                 % codes.count("12") if codes.count("12") != 1
                 else "`12` ⛔ n'est PAS rendu par `poser` (%d occurrence(s))"
                 % dans_poser))

    # 🔴 `(c19)` — UNE SURFACE ABSENTE SE **DIT**, ET ELLE ⛔ NE PESE SUR RIEN.
    #    LIGNE DE LA MATRICE D'E/S : « Surface Windows de notification absente
    #    ⇒ le pre-vol le DIT, `rc` inchange ». Elle ⛔ n'avait AUCUN porteur
    #    mecanique — et le banc `tools/verif_lhm_ps_dn83.py` ⛔ n'en aura
    #    jamais : il DOUBLE `Prevenir-Windows` dans sa copie jetable, pour ⛔ ne
    #    pas pousser une vraie boite de message sur le bureau de qui le joue.
    #    ⇒ la STRUCTURE se garde ICI, le reste se ferme A L'ŒIL.
    # ⚠️ LES DEUX MOITIES SONT LA MEME PROPRIETE, ET ELLES SONT JUGEES
    #    ENSEMBLE : « il le DIT » sans « ca ne pese sur rien » laisserait une
    #    edition Familiale de Windows PERDRE l'agent avec un beau message.
    # ⚠️ `source_fonction()` lit du PYTHON (`def`) — ⛔ pas du PowerShell.
    #    La fonction se borne donc par ses DEUX marqueurs litteraux, comme
    #    `bloc_lhm_ps1()` le fait deja pour le bloc LHM.
    src_surf = region(ps1, A_SURFACE_DEBUT, A_SURFACE_FIN)
    dit = A_MOT_SANS_SURFACE in (src_surf or "")
    rend_faux = "return $false" in (src_surf or "")
    sans_exit = not RE_EXIT.findall(src_surf or "")
    jete = A_RETOUR_JETE in ps1
    ok = bool(src_surf) and dit and rend_faux and sans_exit and jete
    ctrl(ok, "(c19) une surface ABSENTE se DIT, et ⛔ ne pese sur rien",
         "elle NOMME l'absence, rend `$false`, ⛔ ne sort pas, et l'appelant "
         "JETTE son retour" if ok
         else "⛔ %s — une ignorance ⛔ N'EST PAS un ecart : sans cela, une "
              "edition Familiale de Windows (⛔ pas de `msg.exe`) PERDRAIT "
              "l'agent que cette marche existe pour lui rendre"
              % ("`%s` est introuvable" % A_SURFACE_WINDOWS if not src_surf
                 else "elle ⛔ ne NOMME pas l'absence (`%s`)" % A_MOT_SANS_SURFACE
                 if not dit
                 else "elle ⛔ ne rend PAS `$false` sur l'absence"
                 if not rend_faux
                 else "elle porte une SORTIE : exit %s"
                 % ",".join(RE_EXIT.findall(src_surf)) if not sans_exit
                 else "l'appelant ⛔ ne JETTE pas son retour (`%s` absent)"
                 % A_RETOUR_JETE))


    proc_ps1 = [j for j in JETONS_PROCESSUS if j in bloc_ps1.lower()]
    proc_py = [j for j in JETONS_PROCESSUS if j in src_sonde.lower()]
    # 🔴 ET LE VERDICT SE LIE A CE QUI TRANCHE VRAIMENT : **un `200` EXACT** ET
    #    **le corps**. DEMONTRE le 2026-09-10 : `return rep.status != 500`
    #    laissait TOUT vert — « status » apparaissait, donc le controle etait
    #    satisfait par un mot, ⛔ pas par une propriete.
    #    ⚠️ ET LE CORPS EST LOAD-BEARING : `/metrics` sur ce port est l'adresse
    #    la plus banale d'un exportateur Prometheus. Un service voisin rendrait
    #    la sonde VERTE, l'agent demarrerait, et la temperature du CPU resterait
    #    a `--` pour toujours — MEME FAMILLE de faux vert que compter le
    #    processus, et c'est pour ca que les deux vivent dans CE controle.
    http_ps1 = ("Invoke-WebRequest" in bloc_ps1
                and "StatusCode -eq 200" in bloc_ps1
                and MARQUE_CORPS in bloc_ps1)
    http_py = ("HTTPConnection" in src_sonde and "status == 200" in src_sonde
               and NOM_MARQUE_PY in src_sonde and "LHM_CHEMIN" in src_cible)
    ok = http_ps1 and http_py and not proc_ps1 and not proc_py
    ctrl(ok, "(c12) `/metrics` ET SON CORPS tranchent, ⛔ rien d'autre",
         "les 2 sondes exigent un 200 EXACT et le prefixe `%s` du corps"
         % MARQUE_CORPS if ok
         else "⛔ %s — un LHM lance SANS son serveur web rend « 1 processus » "
              "et un `/metrics` MORT ; et n'IMPORTE QUEL 200 sur ce port peut "
              "venir d'un exportateur voisin. Le seul verdict qui a la forme "
              "de ce que l'agent fait est la REQUETE que l'agent fait"
              % ("jeton(s) de processus : %s"
                 % " ".join(sorted(set(proc_ps1 + proc_py)))
                 if proc_ps1 or proc_py else
                 "le bloc de l'outil n'exige pas un 200 EXACT et le prefixe "
                 "`%s` du corps" % MARQUE_CORPS if not http_ps1 else
                 "la sonde du serveur n'exige pas un 200 EXACT et le prefixe "
                 "`%s` du corps" % MARQUE_CORPS))

    # ── (c13) L'ELEVATION RESTE HORS DE `installeur/` ───────────────────
    print("\n── (c13) ⛔ AUCUN JETON D'ELEVATION SOUS `installeur/` ────────────")
    trouves = []
    for f in CODE_INSTALLEUR:
        txt = neuf["fichiers"].get(f, "")
        for nom, motif in MOTIFS_ELEVATION:
            if motif.search(txt):
                trouves.append("%s : %s" % (f, nom))
    ctrl(not trouves, "(c13) ⛔ aucun jeton d'elevation dans `installeur/`",
         "%d motif(s) cherche(s) dans %d fichier(s) de code"
         % (len(MOTIFS_ELEVATION), len(CODE_INSTALLEUR)) if not trouves
         else "⛔ %s — la page doit dire l'elevation de LHM EN PARAPHRASE : "
              "« c'est LHM qui coute l'elevation, ⛔ pas DeskNode », et "
              "`NFR7.5` borne ce que `dn7` LIVRE, ⛔ pas ce que l'inconnu "
              "installe lui-meme" % " · ".join(trouves))

    # ── (c17) LA PARADE DE LA COURSE AU LOGON TIENT TOUJOURS ────────────
    print("\n── (c17) LA REPRISE AU LOGON, ET SA BORNE PUBLIEE ────────────────")
    m_c = RE_RESTART_COUNT.search(ps1)
    m_m = RE_RESTART_MINUTES.search(ps1)
    reprises = int(m_c.group(1)) if m_c else None
    minutes = int(m_m.group(1)) if m_m else None
    bloc_date = A_BLOC_COURSE in ps1
    # 🔴 ET LA BORNE EST **CONFRONTEE AUX TROIS SURFACES QUI LA PUBLIENT**.
    #    Comparer le `.ps1` a ses seules constantes laissait « 5 reprises »
    #    passer VERT dans le README, le CHANGELOG **ou la roadmap** — dans la
    #    marche dont `AC7.5.2` fait de « re-deriver, dans les deux sens » sa
    #    these entiere. ⚠️ LA ROADMAP EST NOMMEE ICI : le message de KO
    #    l'oubliait, et une surface qu'un message oublie ne se corrige pas.
    prose = []
    for nom, motif in SURFACES_BORNE:
        m = motif.search(neuf["fichiers"].get(nom, ""))
        lu = (int(m.group(1)), int(m.group(2))) if m else None
        if lu != (REPRISES_ATTENDUES, MINUTES_ATTENDUES):
            prose.append("%s ⇒ %s" % (nom, "AUCUNE borne lisible" if lu is None
                                      else "%d reprise(s) a %d min" % lu))
    ok = (reprises == REPRISES_ATTENDUES and minutes == MINUTES_ATTENDUES
          and bloc_date and not prose)
    ctrl(ok, "(c17) la reprise au logon tient, et elle est DITE",
         "%d reprise(s) a %d min · bloc date present · %d surface(s) de prose "
         "d'accord" % (reprises, minutes, len(SURFACES_BORNE)) if ok
         else "⛔ %s — la tache de LHM demarre ELEVEE au logon, celle de "
              "l'agent ⛔ non : depuis le refus dur, un `-RestartCount` retire "
              "ou releve devient une PANNE SILENCIEUSE DE TOUTE LA SESSION "
              "sur une machine SAINE, et le README, le CHANGELOG et le ledger "
              "publieraient une borne de ~3 min qui n'existe plus"
              % ("`-RestartCount` ABSENT de la tache" if reprises is None else
                 "`-RestartInterval` ABSENT ou illisible" if minutes is None
                 else "reprises=%d (attendu %d) · intervalle=%d min "
                      "(attendu %d)" % (reprises, REPRISES_ATTENDUES,
                                        minutes, MINUTES_ATTENDUES)
                 if (reprises, minutes) != (REPRISES_ATTENDUES,
                                            MINUTES_ATTENDUES)
                 else "le bloc DATE qui nomme la course au logon a disparu — "
                      "le reglage tiendrait sans que personne sache POURQUOI"
                 if not bloc_date else
                 "la prose PUBLIE une autre borne que la tache : %s (attendu "
                 "%d reprise(s) a %d min) — les trois surfaces confrontees "
                 "sont `%s`, `%s` et `%s`"
                 % (" · ".join(prose), REPRISES_ATTENDUES, MINUTES_ATTENDUES,
                    LISEZMOI, CHANGELOG, ROADMAP)))

    if regles["sortie_anticipee"]:
        return bilan(0)

    # ── (c14)(c15)(c16) LA RECIPROQUE, MECANIQUE ────────────────────────
    print("\n── (c14)(c15)(c16) AUCUN CONTROLE GARDE PAR ZERO MUTANT ──────────")
    # 🔴 « N mutants, N vus rougir » prouve `mutant ⇒ rouge`, ⛔ JAMAIS
    #    `controle ⇒ couvert`. Les deux sens sont mesures, SEPAREMENT.
    lus_ast = ids_par_ast()
    reels = set(ids_emis) | (lus_ast or set())
    vises = set()
    for v in cibles.values():
        vises.update(v)
    nus = sorted(reels - vises, key=lambda s: (len(s), s))
    ctrl(not nus and lus_ast is not None,
         "(c14) chaque controle est vise par >= 1 mutant",
         "%d controle(s) lu(s) a l'AST, %d cible(s) declaree(s)"
         % (len(reels), len(vises)) if not nus and lus_ast is not None
         else ("⛔ %d CONTROLE(S) GARDE(S) PAR RIEN : %s"
               % (len(nus), " · ".join(nus)) if nus
               else "⛔ LA SOURCE NE S'ANALYSE PAS A L'AST — la population de "
                    "ce controle est INCONNUE, ⛔ pas vide"))
    perimees = sorted(vises - reels, key=lambda s: (len(s), s))
    ctrl(not perimees, "(c15) chaque cible de mutant est un controle REEL",
         "%d cible(s) confrontee(s)" % len(vises) if not perimees
         else "⛔ %d CIBLE(S) PERIMEE(S) : %s — un mutant qui vise un controle "
              "inexistant ⛔ ne garde rien"
              % (len(perimees), " · ".join(perimees)))
    orph = sorted(set(cibles) - set(MUTANTS))
    sans_cible = sorted(set(MUTANTS) - set(cibles))
    ctrl(not orph and not sans_cible,
         "(c16) `CIBLES` et `MUTANTS` se correspondent",
         "%d mutant(s), %d cible(s), cle a cle" % (len(MUTANTS), len(cibles))
         if not orph and not sans_cible
         else "⛔ cible(s) SANS mutant : %s · mutant(s) SANS cible : %s"
              % (orph or "—", sans_cible or "—"))

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : qu'une tour SANS LHM degrade.")
    print("   Elle prouve que le mecanisme est BRANCHE — la sonde vise ce que")
    print("   l'agent vise, le bloc ATTEND au lieu de refuser, `12` a SON")
    print("   emetteur (`poser`), la prose couvre EXACTEMENT le derive.")
    print("   Le DEGRADE REEL se ferme a l'œil owner (`mesures/dn4-48`), cote")
    print("   Windows, avec l'AGENT VIVANT verifie — ⛔ pas deduit du message.")
    return bilan(1 if ko_total[0] else 0)


if __name__ == "__main__":
    sys.exit(main())

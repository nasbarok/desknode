#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn7-3 — LE BANC DE LA POSE DE LANGUE EST **JOUE**, ⛔ PAS SEULEMENT ECRIT.

======================= CE QUE CETTE GATE GARDE, ET POURQUOI ================

`tools/banc_langue_dalle_dn73.mjs` EXECUTE le JavaScript de
`installeur/index.html` contre un port bidon, et juge **DIX-HUIT** chemins : les
NEUF lignes de la matrice d'entrees-sorties de `dn7-3`, et NEUF de plus que deux
revues ont nommes. Cette gate existe pour UNE raison, et
elle est ecrite plutot que supposee :

⚠️ ANNOTE LE 2026-09-11 (`dn8-2`) — ⛔ LE PARAGRAPHE CI-DESSUS N'EST PAS EFFACE,
   MAIS SON COMPTE EST **PERIME, ET IL L'ETAIT DEJA**. Releve du 2026-09-11,
   AVANT cette marche : le banc jouait **27** cas, ⛔ pas 18 — `dn7-4` en avait
   ajoute deux et `dn7-6` six, sans que cette phrase ni celle de l'en-tete du
   banc ne bougent. Le compte qui fait foi est `CAS_ATTENDUS` ci-dessous, ⛔
   jamais une phrase de prose. Depuis `dn8-2` : **34** cas sans base HTTP, et
   **37** avec.
⚠️ RE-MESURE LE 2026-09-12, APRES LA BOUCLE DE REVUE 1 — ⛔ LA LIGNE CI-DESSUS
   N'EST PAS EFFACEE : **39** cas sans base et **42** avec. Cinq de plus, et
   ⛔ aucun n'est un supplement de confort : une fermeture de port qui ECHOUE
   (le port bidon ne savait pas la jouer) et QUATRE cas de BLOCS D'AFFICHAGE,
   qui jugent onze bandeaux dans leurs DEUX etats.

🔴 ET CE QUE `dn8-2` AJOUTE, C'EST UN **VRAI SERVEUR**. Jusqu'ici le banc posait
   `fetch: () => Promise.reject("hors banc")` et `tools/verif_installeur_dn71.py`
   appelait le produit **PAR IMPORT** : le trajet HTTP n'etait joue par
   PERSONNE, et une INVERSION entre `ROUTE_DEPENDANCES` et le prefixe
   `/api/agent/` dans `do_POST` serait passee VERTE. Cette gate lie donc
   maintenant le VRAI `ThreadingHTTPServer` du produit sur `127.0.0.1:0`, le
   passe au banc en `--base`, et le FERME dans son `finally`.
   ⛔ AUCUN GESTE REEL N'ATTEINT LA MACHINE : `_powershell`, `localiser_pilote`,
   `_lire`, `lhm_present` et `_jouer_dependances` sont remplaces par des doubles
   de papier — le dernier parce qu'il lance un `pip install` POUR DE VRAI.
   ⚠️ Le serveur est lie **UNE FOIS PAR TIR DE GATE**, ⛔ jamais une fois par
      cas : la campagne rejoue cette gate une fois par mutant, et le cout d'un
      `bind` par cas se paierait 37 fois par mutant.
   🔴 ET `dependance_presente` EST DOUBLEE AUSSI (correctif de revue du
      2026-09-12), pour DEUX raisons MESUREES : elle lance **deux
      interpreteurs** par appel — `GET /api/etat` mesure a **175,2 ms** median
      (146-289, n=8) contre **2,2 ms** doublee — et elle rend l'etat de **CETTE**
      machine (`psutil` absent ici ⇒ `[False, True]`), c'est-a-dire un fait de
      banc que ⛔ rien ne declarait.

  🔴 UN INSTRUMENT QUI A TOURNE **UNE FOIS** NE GARDE **RIEN** DEMAIN. Le banc
     avait d'abord ete joue a la main, hors de l'arbre, et son releve verse. Ce
     releve prouvait l'etat d'un jour, ⛔ pas une propriete. Documenter un piege
     ne protege de rien ; seul le REJOUER protege. ⇒ le banc entre au depot, et
     cette gate le LANCE — decouverte par le glob de `tools/run_gates.sh` et
     rejouee mutant par mutant par `tools/verif_campagne_dn56.py`.

  🔴 ET UNE GATE VERTE SUR UN BANC QUI N'A PAS TOURNE SERAIT **PIRE QUE PAS DE
     GATE**. `node` est un prerequis : s'il manque, cette gate rend **`rc=4`**
     avec son motif, et `tools/run_gates.sh` la declare NON-JOUABLE sur un
     temoin derive de `command -v node`. ⛔ Elle ne sort JAMAIS verte sans avoir
     joue le banc.

── CE QU'ELLE GARDE, LIGNE A LIGNE ─────────────────────────────────────────

  1. **LE BANC TOURNE**, et il rend son bilan. Une sortie sans `BANC :` est la
     signature d'un banc MORT — le meme discriminant que `BILAN` pour une gate.
  2. **LES NEUF LIGNES DE LA MATRICE SONT JOUEES, NOMMEMENT.** Un cas qui
     disparait retrecirait la population SANS RIEN DIRE. Les NEUF autres sont
     comptees, ⛔ pas nommees ici : la matrice fait autorite, ⛔ pas la liste.
  3. **LE BANC JOUE TOUS LES CAS QU'IL DECLARE** — le compte emis egale le
     compte attendu.
  4. **TOUT CAS REND OK.**
  5. **LE BANC EXECUTE LA PAGE, ⛔ IL NE LA RECOPIE PAS.** Un harnais qui
     rejoue une logique recopiee ne mesure que lui-meme.
  6. **LE BANC JUGE LA SUITE DES ISSUES, ⛔ PAS L'ETAT FINAL.** Mesure : un
     succes annonce trop tot puis ECRASE laisse l'ecran final correct, et le
     banc sortait VERT sur du code FAUX.

── CE QU'ELLE NE PROUVE ⛔ PAS, ECRIT PLUTOT QUE TU ─────────────────────────

⛔ Elle n'ouvre AUCUN port serie et ne parle a AUCUNE carte : le banc joue une
   carte BIDON. Que la langue soit VRAIMENT posee, et qu'elle survive a une
   coupure, se lit AU BANDEAU DE LA DALLE — seance carte, portee au ledger.
⛔ Elle ne remplace ⛔ pas `tools/verif_langue_dalle_dn73.py`, qui garde la
   STRUCTURE : les deux se partagent le travail, et le partage est ECRIT. Le
   relachement du verrou d'ecriture sur le chemin d'ECHEC, par exemple, n'est
   PAS exerce ici — ce chemin ne se produit pas contre un port bidon — et c'est
   `(c9)` de la gate statique, avec son mutant, qui le garde.
⛔ Elle ne dit RIEN de la lisibilite de la page.

Emploi :
    python3 tools/verif_banc_langue_dn73.py
    python3 tools/verif_banc_langue_dn73.py --liste-mutants
    python3 tools/verif_banc_langue_dn73.py --mutant <n>

Sortie : 0 si tout passe · 1 sur un vrai defaut · 2 sur un mutant inconnu ·
         3 si le mutant demande est PERIME (il n'a rien change) ·
         4 si `node` est introuvable, ou si la boucle locale REFUSE le `bind` —
           prerequis DECLARES, ⛔ pas des rouges.
⚠️ EN MODE MUTANT, UN PREREQUIS ABSENT DEVIENT UN **ROUGE NOMME** (`rc=1`) :
   `tools/verif_campagne_dn56.py` exige `rc=1` de chaque mutant, et elle ⛔
   n'est PAS `NON_JOUABLE`. C'est le defaut le plus cher de `dn8-1`, et il ⛔
   ne se rejoue pas ici.
"""

import argparse
import ast
import copy
import importlib.util
import io
import os
import re
import errno
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 🔴 `dn_gates` — ⛔ POUR UN SEUL HELPER, ET C'EST DELIBERE : `sans_commentaires`
#    etait LIVRE PAR `dn8-1` SANS AUCUN APPELANT, et c'est exactement ce dont
#    `position_executee` a besoin pour cesser de juger un commentaire au PREFIXE
#    de sa ligne. ⛔ Cette gate garde ses propres `ctrl`/`bilan`/`lire` : elle
#    n'est pas dans le perimetre `dn8`, et les remplacer serait refondre une gate
#    existante par la porte de derriere.
try:
    import dn_gates
except ImportError as _x:                                 # pragma: no cover
    sys.stderr.write(
        "⛔ `tools/dn_gates.py` est INTROUVABLE (%s).\n"
        "   Cette gate lui demande `sans_commentaires`. Le module vit DANS ce\n"
        "   depot, a cote de ce fichier — c'est un defaut, ⛔ pas un prerequis\n"
        "   d'environnement.\n" % _x)
    sys.exit(1)

PAGE = "installeur/index.html"
BANC = "tools/banc_langue_dalle_dn73.mjs"
# 🔴 LE PRODUIT ENTRE DANS LES FIXES (`dn8-2`) : c'est LUI que le banc va
#    joindre par HTTP, et c'est lui qu'un mutant de ROUTAGE doit pouvoir muter.
#    ⛔ Il est CHARGE DEPUIS LE TEXTE, jamais importe du disque : un mutant qui
#    ne pourrait pas le changer ne prouverait rien.
PRODUIT = "installeur/dn_installeur.py"
# 🔴 CE FICHIER LUI-MEME (dn8-2, correctif de revue) : le SECOND prerequis — la
#    boucle locale accepte-t-elle un `bind` — n'etait joue par ⛔ AUCUN des 60
#    mutants. Son bras `if _MUTANT:` pouvait donc disparaitre SANS QUE RIEN NE
#    ROUGISSE, et c'est le defaut le plus cher de `dn8-1` (un `rc=4` sous mutant
#    rend la suite ROUGE en CI, ⛔ invisible a tout tir local).
MOI = "tools/verif_banc_langue_dn73.py"
# 🔴 ET LE WORKFLOW : l'UNIQUE point d'application des seuils de couverture vit
#    dans `.github/workflows/gates.yml`, qu'⛔ AUCUNE gate ne lisait. Supprimer
#    l'etape, ou lui ajouter `continue-on-error`, laissait TOUTE la suite verte.
CI = ".github/workflows/gates.yml"
# Le relevé de couverture, DONT LES SEUILS SONT RELUS PAR (c15) — et dont la
# DECISION est JOUEE par son temoin, que (c15) lance.
COUVERTURE = "tools/banc_couverture_dn82.mjs"
# 🔴 LE MANIFESTE DE LA CHARGE — la version que la page doit AFFICHER y est LUE
#    par le banc. ⛔ Elle n'est ecrite en dur NI ici NI dans le banc : `dn8-7`
#    reconstruira cette charge, et un `40be2c8` grave quelque part rougirait ce
#    jour-la sans rien apprendre a personne. ⚠️ Le chemin passe est celui de
#    l'ARBRE REEL : la copie jetable du banc ⛔ ne porte PAS `charge/`.
MANIFESTE_CHARGE = "installeur/charge/manifest.json"
# Les six scenarios que le temoin du relevé DECIDE, et le code attendu de chacun.
# ⛔ Un seuil dont la decision n'est jouee par personne est un seuil qu'on CROIT
#    avoir : demonstration du 2026-09-12 — `principal()` appelee sans `exitCode`
#    et un seuil a 99 laissaient le relevé sortir **0**, sous son propre seuil.
TEMOINS_DECISION = {"fenetre-absente": 2, "couverture-absente": 2,
                    "banc-rouge": 3, "banc-muet": 3, "banc-un-ko": 3,
                    "sous-fonctions": 1, "sous-blocs": 1, "au-seuil": 0}
# La ligne que le temoin de COMPTAGE doit rendre sur sa fixture — ⛔ une fixture
# dont les comptes sont CONNUS : une fonction morte, un bloc mort.
TEMOIN_COMPTAGE = "TEMOIN COMPTAGE fn=2/3 blk=0/1 morts=1  (attendu)"
RE_TEMOIN_DECISION = re.compile(r"^TEMOIN (\S+)\s+code=(\d+)", re.M)
FIXES = (PAGE, BANC, PRODUIT, COUVERTURE, MOI, CI)
OUTIL = "tools/dn_agent_tour.ps1"

# ⛔ LE DOUBLE DE PAPIER DE L'OUTIL — ⛔ aucune ligne du vrai `.ps1` n'est lue,
#    et ⛔ aucun `powershell` n'est lance. Le patron vient de
#    `tools/verif_installeur_dn71.py`, qui l'a paye : sans lui, cette classe de
#    gate ouvrait de VRAIES connexions et lancait de VRAIS processus.
PS1_DE_PAPIER = ("param(\n"
                 "    [ValidateSet('etat', 'stop', 'retirer')]\n"
                 "    [string]$Action = 'etat'\n)\n")

# 🔴 LES DEUX BORNES D'ENTREE DE LA COUVERTURE, MESUREES LE 2026-09-11 SOUS
#    `NODE_V8_COVERAGE` — ⛔ pas reprises d'un rapport. Elles sont ce que les
#    seuils declares dans `COUVERTURE` doivent STRICTEMENT battre.
BORNE_COUVERTURE_FONCTIONS = 72
BORNE_COUVERTURE_BLOCS = 87
RE_SEUIL_FONCTIONS = re.compile(r"^const SEUIL_FONCTIONS = (\d+);", re.M)
RE_SEUIL_BLOCS = re.compile(r"^const SEUIL_BLOCS = (\d+);", re.M)

# ⚠️ LE DELAI EST LARGE ET DECLARE : le banc joue dix scenarios, chacun avec des
#    attentes armees. Un `rc is None` de depassement est la mesure de CETTE
#    GATE, ⛔ pas le verdict du banc — et il se rend en KO, ⛔ jamais en vert.
DELAI_BANC = 120
# 🔴 LE TEMOIN DE CHAINE A **SA PROPRE BORNE, ET ELLE EST COURTE** — mesure :
#    le mutant qui RETIRE le filet global du banc faisait payer les 120 s
#    ci-dessus a CHAQUE tir, une fois par mutant dans la campagne (121,5 s pour
#    ce seul mutant). Le temoin ne joue AUCUN cas : il ne doit durer que le
#    temps du filet, et son depassement EST le rouge attendu.
DELAI_TEMOIN = 8
# ⚠️ LA BORNE D'UN CAS DU BANC, PASSEE EXPLICITEMENT : un cas normal coute
#    ~130 ms ; un cas qui ne se resout pas paye cette borne EN ENTIER, une fois
#    par mutant. ⛔ On ne la laisse donc pas a la valeur GENEREUSE du banc.
DELAI_CAS = 1500
# ⚠️ CE QUE LA **PAGE** ATTENDRA PENDANT LE BANC. ⛔ Ce n'est PAS une valeur de
#    produit : c'est le reglage que le banc REPOSE apres avoir evalue le script,
#    et il existe parce que la campagne rejoue ce banc UNE FOIS PAR MUTANT.
DELAI_PAGE = 40

# ── LES NEUF LIGNES DE LA MATRICE D'ENTREES-SORTIES DU DOSSIER ────────────
# 🔴 NOMMEES, ⛔ PAS COMPTEES : un compte ne dit pas LAQUELLE a disparu, et
#    c'est toujours celle qu'on n'aurait pas remarquee.
CAS_MATRICE = (
    "defaut-structurel",
    "pose-nominale",
    "deja-en-francais",
    "refus-de-la-carte",
    "pas-d-invite",
    "sans-reponse",
    "port-tenu-par-l-agent",
    "double-clic",
    "pas-d-acces-serie",
)
# ⚠️ QUATRE CAS HORS MATRICE, ET AUCUN N'EST UN SUPPLEMENT DE CONFORT :
#  · `relecture-sans-le-code` — la carte accepte sans le dire, puis la relecture
#    rend une AUTRE langue. Le dossier ne le nomme pas ; il est classe `refusee`
#    par un arbitrage ecrit au journal des changements de la story ;
#  · `pose-par-le-selecteur` — le chemin post-flash ORDINAIRE : le port n'est pas
#    deja ouvert, il s'obtient PAR LE SELECTEUR, et la pose va au bout. C'est LA
#    ligne de code livre que cette marche a changee, et rien ne l'exercait ;
#  · `nvs-refusee` — la CINQUIEME issue : la dalle a change A CHAUD, et ⛔ elle
#    ne gardera pas ce changement ;
#  · `selecteur-deja-en-vol` — un clic qui n'ecrit rien ET n'affiche rien se lit
#    comme une page cassee : la page doit NOMMER ce qui s'est passe.
#  · `fait-de-page-a-la-maison` / `verdict-sous-le-bouton` — DECLARES LE
#    2026-09-10 par `dn7-4`. ⚠️ LES DECLARER **EST** LE GESTE QUE `(c3)` EXIGE :
#    son propre message de KO dit que le compte « voit un cas ajoute SANS ETRE
#    DECLARE ». Ces deux-la mesurent OU se pose `#sortie` — sous le bouton
#    clique apres un verbe, a sa place d'origine apres un fait de PAGE — et
#    c'est la seule moitie d'`AC7.4.1` qu'une machine puisse tenir.
#  · les SIX cas de PRECONDITION — DECLARES LE 2026-09-10 par `dn7-6`, et pour
#    la meme raison que les deux precedents : `(c3)` exige que tout cas ajoute
#    soit DECLARE. ⚠️ ILS FERMENT UN RESIDU QUE `dn7-5` AVAIT LAISSE ECRIT :
#    son `poserMot("v-lhm", …)` n'etait traverse par AUCUN harnais. Ils
#    mesurent quel MOT et quelle FORME chaque etape porte, et quel geste se
#    DESARME avec quel motif — la moitie d'`AC7.6.2` qu'une machine tienne.
#    ⛔ `tout-est-la` est la LIGNE DE REFERENCE : sans elle, « grise » ne se
#    distinguerait de rien. ⛔ `psutil-manquant` porte la ligne de partage qui
#    n'est PAS intuitive : le FLASH ⛔ n'est PAS bloque par une dependance de
#    l'AGENT. ⛔ `lhm-non-testable` porte l'inverse d'un verdict : une
#    IGNORANCE ⛔ ne bloque RIEN — la faute que `dn7-1` a payee pour `psutil`.
CAS_HORS_MATRICE = ("relecture-sans-le-code", "pose-par-le-selecteur",
                    "nvs-refusee", "selecteur-deja-en-vol", "selecteur-annule",
                    "clic-reel-sur-francais", "flash-revele-arme-le-geste",
                    "module-absent-desarme-le-geste",
                    "ecriture-qui-rejette-en-vol",
                    "fait-de-page-a-la-maison", "verdict-sous-le-bouton",
                    "tout-est-la", "psutil-manquant", "lhm-absent",
                    "lhm-non-testable", "hors-windows", "serveur-muet",
                    "outil-absent-etape-bloquee",
                    # ── LES SEPT CAS DE SURFACE MORTE, `dn8-2` ────────────
                    # 🔴 CHACUN EST DECLARE PARCE QUE `(c3)` L'EXIGE, et chacun
                    #    entre dans une fonction que la couverture V8 a relevee
                    #    MORTE le 2026-09-11 — ⛔ pas dans une surface supposee
                    #    faible. `clic-reel-sur-anglais` est le FRERE MANQUANT
                    #    de `clic-reel-sur-francais` : un bouton sur deux etait
                    #    clique. `langue-de-la-page` est la moitie mecanique
                    #    d'`AC8.2.6` — ⛔ pas son verdict de lisibilite.
                    #    `verbes-non-cliques` ferme TROIS gestionnaires et le
                    #    `.catch` de `jouer`. Les QUATRE cas de console ferment
                    #    la boucle de lecture, la fin de lien, la perte de lien
                    #    et le `pagehide` — tout le geste que `dn7-2-2` a livre
                    #    et qu'⛔ AUCUN harnais n'ouvrait.
                    "clic-reel-sur-anglais", "langue-de-la-page",
                    "verbes-non-cliques", "console-ouverte-lue-fermee",
                    "console-fin-de-lien", "console-lien-perdu",
                    "console-pagehide-rend-le-port",
                    # ── LES CINQ CAS DE LA BOUCLE DE REVUE 1 (2026-09-12) ──
                    # 🔴 ILS NE COUVRENT PAS UNE SURFACE DE PLUS : ils JUGENT ce
                    #    que les cas d'avant ne faisaient qu'EXECUTER. 19 sondes
                    #    de mutation ont laisse cette gate a `54 OK / 0 KO` sur
                    #    onze inversions REELLES — dont l'avertissement hors
                    #    Windows que le ledger demontrait le 2026-09-09.
                    #    ⛔ `console-fermeture-qui-echoue` : une fermeture qui
                    #    ECHOUE doit publier « ⛔ pas rendu » et GARDER ses
                    #    references — le port bidon ne savait pas la jouer.
                    #    ⛔ Les QUATRE cas de `blocs-*` observent ONZE bandeaux
                    #    dans leurs DEUX etats, par un vecteur compare EN ENTIER.
                    "console-fermeture-qui-echoue", "blocs-machine-saine",
                    "blocs-machine-en-defaut", "blocs-contexte-refuse",
                    "blocs-sans-web-serial")
# ── LES TROIS CAS **HTTP** — ⛔ JOUES SEULEMENT DERRIERE `--base` ─────────
# 🔴 ILS SONT COMPTES A PART PARCE QU'ILS SE JOUENT A PART : sans serveur ils ne
#    mesureraient RIEN. Cette gate en lie un, donc elle les attend TOUS.
CAS_HTTP = ("http-page-chargee-et-verbe-abouti", "http-routes-du-serveur",
            "http-refus-host-et-origine")
CAS_ATTENDUS = len(CAS_MATRICE) + len(CAS_HORS_MATRICE) + len(CAS_HTTP)

RE_CAS = re.compile(r"^CAS (\S+)\s+(OK|KO)\s*(.*)$", re.M)
RE_BILAN_BANC = re.compile(r"^BANC : (\d+) OK, (\d+) KO$", re.M)

# ── CE QUI FAIT DU BANC UN BANC, ET ⛔ PAS UNE COPIE ──────────────────────
# 🔴 IL DOIT **LIRE LA PAGE ET L'EVALUER**. Un harnais qui redefinirait
#    `poserLangueDalle` chez lui sortirait vert sur une page cassee.
ANCRES_EXECUTION = ("readFileSync", '"<script>', "vm.runInContext")
ANCRE_RECOPIE = "function poserLangueDalle"
# 🔴 ET IL DOIT JUGER LA **SUITE** DES ISSUES : `langue.posee` au plus UNE fois,
#    et EN DERNIER. Mesure : sans ca, un succes annonce trop tot puis ecrase
#    laissait le banc VERT.
ANCRES_SUITE = ("suite.push(cle)", "r.suite[r.suite.length - 1]")
# 🔴 LE BANC DOIT SORTIR EN NON-ZERO QUAND SA CHAINE NE SE RESOUT PAS, ET CA SE
#    JOUE : `--temoin-chaine` REPLANTE le cas, et cette gate exige rc != 0 SANS
#    ligne de bilan. ⛔ Un banc qui rend 0 sur une liste tronquee annonce un
#    succes qu'il n'a pas mesure.
DRAPEAU_TEMOIN = "--temoin-chaine"
# 🔴 ET LE TEMOIN SE JUGE SUR **DEUX** CHOSES, ⛔ pas sur « non nul » : un
#    `Traceback` sort non nul et sans bilan, EXACTEMENT comme un filet qui a
#    joue. ⇒ on exige le code que le filet DECLARE, et la ligne qu'il imprime.
RC_FILET = 3
SIGNATURE_FILET = "BANC ⛔ CHAINE NON RESOLUE"
# 🔴 ET IL DOIT **REPOSER** LES ATTENTES DE LA PAGE : la campagne rejoue ce banc
#    une fois par mutant, et deux attentes de six secondes figees l'ont portee a
#    93 % de son plafond. ⛔ Se rabattre en silence sur la valeur du produit
#    serait pire que l'echec : il ECHOUE FERME.
ANCRES_DELAIS = ("ctx.DELAI_INVITE = DELAI_PAGE;",
                 "ctx.DELAI_REPONSE = DELAI_PAGE;",
                 'typeof ctx.DELAI_INVITE !== "number"')
# 🔴 ET IL DOIT **EXERCER LES CHEMINS DE PRECONDITION** (`dn7-6`), ⛔ pas
#    seulement les declarer. Trois choses, et chacune ferme un trou different :
#     · la FABRIQUE de desarmement est **ENVELOPPEE**, ⛔ jamais remplacee — un
#       harnais qui la remplace fabrique lui-meme la suite qu'il attend, et il
#       sortirait VERT sur une page ou plus rien ne se grise ;
#     · les temoins d'etape sont MONTES **AVANT** `runInContext` — le fichier
#       documente le cas vecu : un element non monte rend le banc VERT sur des
#       branches MORTES ;
#     · le chemin est ROUTE depuis la fonction de cas, sinon il ne se joue pas.
ANCRES_PRECONDITION = (
    "const r = vraiArmer(id, permis, cle);",
    'geste2.insertBefore(doc.getElementById("v-etape-flash"), null);',
    "if (cas.etatMachine !== undefined) { return jouerPrecondition(ctx, els, cas); }",
    "attendTemoins", "attendArmes")
A_MONTAGE_PRECONDITION = 'doc.getElementById("v-etape-flash")'
A_EXECUTION = "vm.runInContext"

# 🔴 L'ASSERTION DE DOM (`dn8-2`) — ELLE SE JOUE, ET ELLE SE JOUE **AVANT**.
#    Les deux moities sont gardees separement : `--temoin-dom` REPLANTE la faute
#    de `dn7-4` (un element monte PRIVE de sa capacite) et exige le code + la
#    signature ; l'ORDRE, lui, se lit dans le fichier — une assertion jouee
#    APRES `runInContext` constaterait un DOM sur lequel la page a DEJA lu ce
#    qu'elle avait a lire, c'est-a-dire trop tard.
DRAPEAU_TEMOIN_DOM = "--temoin-dom"
RC_DOM = 4
SIGNATURE_DOM = "DOM DEGENERE"
A_ASSERTION_DOM = "asserterDom(montes);"
# 🔴 LE PONT HTTP : il EXISTE, et le banc DIT la base qu'il a recue. Le port
#    annonce est confronte a celui que CETTE gate a lie — ⛔ pas seulement
#    « une base non vide », qui serait vrai d'une base inventee.
RE_BASE_BANC = re.compile(r"^base HTTP  : http://127\.0\.0\.1:(\d+)/", re.M)

LARGEUR_LIBELLE = 58

ok_total = [0]
ko_total = [0]
ids_emis = []

MUTANTS = {}                      # ⛔ AU NIVEAU MODULE — sinon `--liste-mutants`
CIBLES = {}                       # ⛔ AU NIVEAU MODULE — matiere de (c9)

MUTANTS[1] = ("PAGE : efface la garde du defaut anglais ⇒ des octets "
              "partent sur le port pour un choix qui n'ecrit rien")
CIBLES[1] = ("c4",)
MUTANTS[2] = ("PAGE : annonce le succes AVANT la relecture ⇒ un succes "
              "prouve par ce qu'on a tape")
CIBLES[2] = ("c4",)
MUTANTS[3] = ("PAGE : ECHANGE « refusee » et « sans reponse » ⇒ une "
              "ignorance publiee comme un constat")
CIBLES[3] = ("c4",)
MUTANTS[4] = ("PAGE : retire l'attente de l'invite ⇒ l'ordre part sur "
              "une carte qui n'a jamais repondu")
CIBLES[4] = ("c4",)
MUTANTS[5] = ("PAGE : retire la garde de re-entrance ⇒ deux clics "
              "envoient DEUX suites d'ordres sur le meme port")
CIBLES[5] = ("c4",)
MUTANTS[6] = ("PAGE : ne relache plus le verrou d'ecriture au succes ⇒ "
              "la fermeture du port partirait en rejet")
CIBLES[6] = ("c4",)
MUTANTS[7] = ("PAGE : rend le geste MUET quand le port n'est pas venu "
              "⇒ un clic qui n'ecrit rien ET n'affiche rien")
CIBLES[7] = ("c4",)
MUTANTS[8] = ("BANC : recopie la logique au lieu d'EVALUER la page ⇒ "
              "un harnais qui ne mesure plus que lui-meme")
# ⚠️ QUATRE CIBLES, MESUREES LE 2026-09-12 : un banc qui RECOPIE la page au
#    lieu de l'evaluer ne casse pas que les cas — il perd AUSSI les chemins
#    de precondition `(c12)` et l'assertion de DOM `(c13)`. ⛔ Declarer deux
#    cibles pour un mutant qui en rougit quatre decrirait un mutant QUI
#    N'EXISTE PAS.
CIBLES[8] = ("c4", "c5", "c12", "c13")
MUTANTS[9] = ("BANC : ne juge plus que l'etat FINAL ⇒ un succes "
              "annonce trop tot puis ECRASE redevient invisible")
CIBLES[9] = ("c6",)
MUTANTS[10] = ("BANC : retire un cas de la matrice ⇒ la population "
               "retrecit, et le banc sortirait VERT sur moins")
CIBLES[10] = ("c2", "c3")
MUTANTS[11] = ("replante une SORTIE ANTICIPEE NON DECLAREE : le bilan "
               "retrecit, et il sortirait VERT")
CIBLES[11] = ("z",)
MUTANTS[12] = ("declare un mutant dont le CORPS LEVE ⇒ un mutant MORT, "
               "qui sortirait en Traceback SANS `BILAN`")
CIBLES[12] = ("c0",)
MUTANTS[13] = ("retire une cible de `CIBLES` ⇒ un controle garde par "
               "ZERO mutant, le risque deja paye ailleurs")
CIBLES[13] = ("c9",)
MUTANTS[14] = ("declare dans `CIBLES` un controle INEXISTANT ⇒ une "
               "cible PERIMEE, que « N mutants, N rouges » ne voit pas")
CIBLES[14] = ("c10",)
MUTANTS[15] = ("declare une cible pour un mutant qui N'EXISTE PAS")
CIBLES[15] = ("c11",)
MUTANTS[16] = ("BANC : le rend MUET — il ne rend plus son bilan, la "
               "signature exacte d'un banc mort")
CIBLES[16] = ("c1",)
MUTANTS[17] = ("PAGE : rend l'ouverture du port bloquante jusqu'a la "
               "MORT du lien ⇒ la pose attend ce qu'elle veut utiliser")
CIBLES[17] = ("c4",)
MUTANTS[18] = ("PAGE : classe l'echec d'ecriture NVS comme un REFUS ⇒ "
               "la page dit l'INVERSE de ce que la carte imprime")
CIBLES[18] = ("c4",)
MUTANTS[19] = ("PAGE : renomme le delai d'invite ⇒ le banc ⛔ ne peut "
               "plus le regler, et il doit ECHOUER FERME")
CIBLES[19] = ("c4",)
MUTANTS[20] = ("BANC : retire le filet global ⇒ une chaine non resolue "
               "sortirait en 0 sur une liste TRONQUEE")
CIBLES[20] = ("c7",)
MUTANTS[21] = ("BANC : cesse de REPOSER les attentes de la page ⇒ la "
               "campagne repaie six secondes par tir")
# ⚠️ DEUX CIBLES : un banc qui ne REPOSE plus les attentes de la page rougit
#    `(c8)` — l'ancre disparue — ET `(c4)`, parce que les cas paient alors
#    six secondes d'attente et tombent sur leur borne. Mesure du 2026-09-12.
CIBLES[21] = ("c4", "c8")
MUTANTS[22] = ("PAGE : ECHANGE les deux gestionnaires de clic du choix "
               "⇒ cliquer « francais » enverrait `langue en`")
CIBLES[22] = ("c4",)
MUTANTS[23] = ("PAGE : INVERSE la polarite de l'armement ⇒ le geste "
               "s'offre justement quand le flash est impossible")
CIBLES[23] = ("c4",)
MUTANTS[24] = ("PAGE : dit TOUJOURS que le port est tenu ⇒ la phrase "
               "cesse d'etre une mesure et devient un ornement")
CIBLES[24] = ("c4",)
MUTANTS[25] = ("PAGE : le filet ne rend plus le geste ⇒ le bouton "
               "reste MORT jusqu'au rechargement de la page")
CIBLES[25] = ("c4",)
MUTANTS[26] = ("PAGE : revele le relais meme VIDE ⇒ un cadre vide "
               "donne a croire qu'on a lu quelque chose")
CIBLES[26] = ("c4",)
MUTANTS[27] = ("PAGE : ecrit une charge VIDE ⇒ trois appels pour "
               "ZERO octet, et « zero octet » cesse de vouloir dire")
CIBLES[27] = ("c4",)
MUTANTS[28] = ("BANC : le filet sort non nul SANS sa signature ⇒ un "
               "`Traceback` serait pris pour un filet qui a joue")
CIBLES[28] = ("c7",)
MUTANTS[29] = ("PAGE : traite « LHM non testable » comme « LHM absent » "
               "⇒ une IGNORANCE publiee comme un verdict, et ca BLOQUE")
CIBLES[29] = ("c4",)
MUTANTS[30] = ("PAGE : fait dependre le FLASH des modules de l'agent ⇒ "
               "le geste PRINCIPAL bloque pour une dependance a lui")
CIBLES[30] = ("c4",)
MUTANTS[31] = ("BANC : REMPLACE la fabrique de desarmement au lieu de "
               "l'envelopper ⇒ il fabrique la suite qu'il attend")
CIBLES[31] = ("c12",)
MUTANTS[32] = ("PAGE : ne repose plus la FORME du temoin ⇒ un mot juste "
               "sous l'aplat de l'etat PRECEDENT")
CIBLES[32] = ("c4",)
# ── LES MUTANTS DE `dn8-2` ───────────────────────────────────────────────
# ⚠️ CE TITRE DISAIT « LES CINQ MUTANTS » ET IL Y EN AVAIT **SIX** (33→38) — la
#    ligne est corrigee, ⛔ pas effacee. La boucle de revue 1 en ajoute
#    **VINGT-DEUX** (39→60), et le seul compte qui fait foi est `len(MUTANTS)`.
# 🔴 DEUX MUTENT LE **BANC**, DEUX LE **PRODUIT**, UN LE PONT. ⛔ Aucun ne
#    DEBRANCHE une garde : chacun REPLANTE l'etat qui existait AVANT la marche
#    — un banc sans assertion de DOM, un routage inverse, une garde sautee.
MUTANTS[33] = ("BANC : retire l'ASSERTION de DOM ⇒ un DOM ampute "
               "repasse SANS un mot, comme avant `dn7-4`")
CIBLES[33] = ("c13",)
MUTANTS[34] = ("BANC : joue l'assertion de DOM **APRES** `runInContext` "
               "⇒ elle constate un DOM deja lu, c'est-a-dire trop tard")
CIBLES[34] = ("c13",)
MUTANTS[35] = ("PRODUIT : ECHANGE `/api/dependances` et le prefixe "
               "`/api/agent/` dans `do_POST` ⇒ le routage est inverse")
CIBLES[35] = ("c4",)
MUTANTS[36] = ("PRODUIT : `do_POST` ne passe plus par `_garde()` ⇒ un "
               "`Host` menteur et une `Origin` etrangere sont SERVIS")
CIBLES[36] = ("c4",)
MUTANTS[37] = ("BANC : ignore `--base` ⇒ le pont HTTP ne se branche pas, "
               "et les cas HTTP disparaissent SANS un mot")
# ⚠️ TROIS CIBLES : ignorer `--base` fait disparaitre les trois cas HTTP, donc
#    `(c2)` (ils manquent PAR LEUR NOM) et `(c3)` (le compte), en plus de
#    `(c14)` (⛔ aucune base annoncee). Mesure du 2026-09-12.
CIBLES[37] = ("c2", "c3", "c14")
MUTANTS[38] = ("COUVERTURE : RABAISSE le seuil declare a sa borne "
               "d'entree ⇒ un seuil qu'on baisse pour reverdir")
CIBLES[38] = ("c15",)
# ── LES VINGT-DEUX MUTANTS DE LA BOUCLE DE REVUE 1 (2026-09-12) ──────────
# 🔴 CHACUN EST UNE SONDE QUI A ETE **VUE VERTE** AVANT CETTE PASSE, ⛔ pas une
#    inquietude : 19 mutations jouees sur une copie jetable ont laisse cette gate
#    a `54 OK / 0 KO`. Les treize premiers replantent l'INVERSION d'un bloc
#    d'affichage — dont `e.windows === false`, la faute que le ledger demontrait
#    le 2026-09-09.
MUTANTS[39] = ("PAGE : INVERSE l'avertissement hors Windows ⇒ il s'affiche "
               "sur une machine Windows et se tait ailleurs")
CIBLES[39] = ("c4",)
MUTANTS[40] = ("PAGE : INVERSE `etat-orphelin` ⇒ le bandeau accuse un "
               "depot COMPLET et se tait sur un dossier recupere seul")
CIBLES[40] = ("c4",)
MUTANTS[41] = ("PAGE : INVERSE `etat-port-tenu` ⇒ la page annonce un port "
               "tenu quand l'agent n'est PAS pose")
CIBLES[41] = ("c4",)
MUTANTS[42] = ("PAGE : `etat-cdn` ne se leve plus ⇒ un bouton de flash "
               "INERTE sans un mot pour le dire")
CIBLES[42] = ("c4",)
MUTANTS[43] = ("PAGE : `etat-inactif` n'est JAMAIS masque ⇒ un bandeau "
               "« boutons inactifs » au-dessus de boutons cliquables")
CIBLES[43] = ("c4",)
MUTANTS[44] = ("PAGE : `etat-not-allowed` ne se leve plus ⇒ hors contexte "
               "securise, la page ne dit RIEN et le serie est mort")
CIBLES[44] = ("c4",)
MUTANTS[45] = ("PAGE : `etat-unsupported` ne se leve plus ⇒ un navigateur "
               "sans Web Serial n'est plus nomme")
CIBLES[45] = ("c4",)
MUTANTS[46] = ("PAGE : `reveler()` ne revele plus ⇒ le bloc d'installation "
               "reste masque sur une machine SAINE")
CIBLES[46] = ("c4",)
MUTANTS[47] = ("PAGE : `chargeInutilisable` ne masque plus le bloc ⇒ on "
               "flasherait un asset dont le CRC32 est FAUX")
CIBLES[47] = ("c4",)
MUTANTS[48] = ("PAGE : `moduleAbsent` ne masque plus le bloc ⇒ un bouton "
               "qui ne peut RIEN faire reste offert")
CIBLES[48] = ("c4",)
MUTANTS[49] = ("PAGE : `etat-charge` n'est jamais revele ⇒ la charge "
               "abimee est SUE et TUE")
CIBLES[49] = ("c4",)
MUTANTS[50] = ("PAGE : INVERSE `etat-deps` ⇒ le bandeau des modules "
               "s'affiche quand tout est la")
CIBLES[50] = ("c4",)
MUTANTS[51] = ("PAGE : INVERSE `etat-lhm` ⇒ le bandeau de LHM s'affiche "
               "sur une machine SAINE et se tait quand il manque")
CIBLES[51] = ("c4",)
MUTANTS[52] = ("PAGE : `consoleFermer` ferme le port **AVANT** d'annuler "
               "et de relacher ⇒ `close()` part en REJET, port tenu")
CIBLES[52] = ("c4",)
MUTANTS[53] = ("PAGE : `consoleFinDeLien` privee de sa garde ⇒ une "
               "fermeture VOULUE annonce un debranchement qui n'a pas eu lieu")
CIBLES[53] = ("c4",)
MUTANTS[54] = ("PAGE : le `.catch` de `jouer` ne rearme plus les boutons "
               "⇒ quatre gestes MORTS jusqu'au rechargement de la page")
CIBLES[54] = ("c4",)
MUTANTS[55] = ("PRODUIT : `_origines_permises` FAUSSEE ⇒ tout `Origin` de "
               "navigateur est refuse, et la page ne pilote plus RIEN")
CIBLES[55] = ("c4",)
MUTANTS[56] = ("BANC : deplace `asserterDom` APRES `runInContext` en "
               "laissant son nom dans un COMMENTAIRE juste avant")
CIBLES[56] = ("c13",)
MUTANTS[57] = ("COUVERTURE : RABAISSE le seuil de BLOCS a sa borne "
               "d'entree — la moitie que le mutant 38 ⛔ ne touche pas")
CIBLES[57] = ("c15",)
MUTANTS[58] = ("COUVERTURE : la DECISION ignore le seuil de fonctions ⇒ "
               "un releve VERT sous son propre seuil")
CIBLES[58] = ("c15",)
MUTANTS[59] = ("COUVERTURE : la DECISION ignore le seuil de blocs ⇒ "
               "l'autre moitie du meme trou")
CIBLES[59] = ("c15",)
MUTANTS[60] = ("COUVERTURE : la DECISION ignore le VERDICT DU BANC ⇒ des "
               "chiffres pris sur une liste de cas TRONQUEE")
CIBLES[60] = ("c15",)
# ── LES TROIS MUTANTS DE LA SECONDE BOUCLE DE REVUE (2026-09-12) ─────────
MUTANTS[61] = ("MOI : retire le bras `if _MUTANT:` du refus de `bind` ⇒ un "
               "`rc=4` sous mutant, et la suite ROUGE en CI seulement")
CIBLES[61] = ("c16",)
MUTANTS[62] = ("CI : ajoute `continue-on-error` a l'etape de couverture ⇒ "
               "les deux seuils ne sont plus appliques par PERSONNE")
CIBLES[62] = ("c17",)
MUTANTS[63] = ("COUVERTURE : `nFe++` INCONDITIONNEL ⇒ 100/100 fonctions, "
               "0 morte, et le plancher cesse d'etre un plancher")
CIBLES[63] = ("c15",)

# ⚠️ LE COMPTE DU CHEMIN NORMAL : 1 pre-vol + un controle par mutant + les 12
#    controles numerotes. Il se PERIME si on ajoute un controle sans le mettre
#    a jour — et c'est voulu : c'est ce qui rend (z) FALSIFIABLE.
# ⚠️ ANNOTE LE 2026-09-10 (`dn7-6`) : il valait ~~40~~ pour 28 mutants et 11
#    controles numerotes ; `(c12)` et quatre mutants s'ajoutent.
# ⚠️ ANNOTE LE 2026-09-11 (`dn8-2`) : ~~12~~ ⇒ **15** controles numerotes —
#    `(c13)` l'assertion de DOM, `(c14)` le pont HTTP, `(c15)` les seuils du
#    relevé de couverture.
# ⚠️ ANNOTE LE 2026-09-12 : ~~15~~ ⇒ **17** controles numerotes — `(c16)` le
#    second prerequis (`bind`), `(c17)` l'etape de CI qui applique les seuils.
CONTROLES_PREVUS = 1 + len(MUTANTS) + 17

_MUTANT = 0

RE_ID_CTRL = re.compile(r"\((\w+)\)")


def ctrl(ok, libelle, detail=""):
    """UNE assertion, UNE ligne, UN identifiant. ⛔ Aucun controle muet."""
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
    `BILAN` est indiscernable d'une gate MORTE.

    ⚠️ TROIS SORTIES NE PASSENT PAS ICI, ET C'EST ECRIT PLUTOT QUE PROMIS :
       · `--liste-mutants`, qui n'emet AUCUN controle et ne rend AUCUN verdict ;
       · le mutant INCONNU, qui est une ERREUR D'APPEL et rend 2 ;
       · `node` INTROUVABLE, qui est un PREREQUIS DECLARE et rend 4 — ⛔ pas un
         rouge, et ⛔ surtout pas un vert."""
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


def lire(chemin):
    try:
        with io.open(os.path.join(RACINE, chemin), encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


# ═══════════ LES PREDICATS — DES FONCTIONS DU PRODUIT ══════════════════════

def _node_dans_copie(fichiers, script, extra, borne):
    """ECRIT les textes donnes dans un repertoire JETABLE et y lance `node`.

    🔴 UN SEUL LANCEUR POUR LES DEUX INSTRUMENTS (dn8-2) : le banc **et** le
       temoin de decision du relevé de couverture. Deux lanceurs, c'etaient deux
       preparations de copie jetable a garder d'accord — et la seconde aurait
       pourri en silence.
    ⚠️ `rc is None` est un DEPASSEMENT DE DELAI **ou un lancement impossible**,
       ⛔ pas un verdict : il remonte tel quel, et l'appelant le rend en KO."""
    try:
        tmp = tempfile.mkdtemp(prefix="dn73-banc-")
    except OSError as e:
        return None, "⛔ REPERTOIRE JETABLE IMPOSSIBLE A CREER : %s" % e
    try:
        try:
            os.makedirs(os.path.join(tmp, "installeur"))
            os.makedirs(os.path.join(tmp, "tools"))
            for rel, texte in fichiers.items():
                # ⛔ LE REPERTOIRE PARENT EST CREE, QUEL QU'IL SOIT — mesure du
                #    2026-09-12 : des que `.github/workflows/gates.yml` est entre
                #    dans les cibles, cette boucle mourait en `No such file or
                #    directory` et TOUS les temoins qui lancent `node` tombaient
                #    avec elle (7 KO). Deux repertoires ecrits en dur, c'etait une
                #    liste qui se perimait au premier fichier d'ailleurs.
                cible = os.path.join(tmp, rel)
                os.makedirs(os.path.dirname(cible), exist_ok=True)
                with io.open(cible, "w", encoding="utf-8") as fh:
                    fh.write(texte)
        except (OSError, UnicodeError) as e:
            return None, "⛔ PREPARATION DU BANC IMPOSSIBLE : %s" % e
        try:
            r = subprocess.run(["node", os.path.join(tmp, script)] + list(extra),
                               cwd=tmp, timeout=borne,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
            return r.returncode, r.stdout.decode("utf-8", "replace")
        except subprocess.TimeoutExpired as e:
            sortie = (e.output or b"").decode("utf-8", "replace")
            return None, sortie + "\n⛔ DEPASSEMENT DE DELAI (%d s)" % borne
        except OSError as e:
            # ⛔ UN MOTEUR PRESENT MAIS NON EXECUTABLE N'EST **PAS** UN BANC
            #    TROP LENT : le rapporter comme un depassement enverrait
            #    chercher une lenteur la ou il y a un droit ou un binaire casse.
            return None, ("⛔ LANCEMENT IMPOSSIBLE (⛔ pas un depassement) : "
                          "%s: %s" % (type(e).__name__, e))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def le_releve_joue_sa_decision(fichiers):
    """Le relevé de couverture DECIDE-t-il ce qu'il DECLARE ?

    🔴 C'EST JOUE, ⛔ PAS LU — et le defaut etait DEMONTRE : le relevé publiait
       ses chiffres et sortait **0** sous son propre seuil, parce que sa decision
       n'etait exercee par PERSONNE. Son temoin joue la decision sur des comptes
       FORCES, ⛔ sans rejouer le banc (un tir de banc par scenario coutait six
       fois le prix d'un tir de gate)."""
    rc, sortie = _node_dans_copie(fichiers, COUVERTURE, ("--temoin-decision",),
                                  DELAI_TEMOIN)
    if rc is None:
        return False, ("⛔ le temoin de decision n'a pas pu etre lance : %s"
                       % (sortie or "").strip()[-90:])
    if rc != 0:
        return False, "⛔ le temoin de decision rend rc=%s" % rc
    vus = dict((m.group(1), int(m.group(2)))
               for m in RE_TEMOIN_DECISION.finditer(sortie or ""))
    ecarts = ["%s=%s au lieu de %d" % (n, vus.get(n, "ABSENT"), c)
              for n, c in sorted(TEMOINS_DECISION.items()) if vus.get(n) != c]
    if ecarts:
        return False, ("⛔ %d SCENARIO(S) MAL DECIDE(S) : %s"
                       % (len(ecarts), " · ".join(ecarts)))
    # ⛔ ET L'INCONNU EST UN KO, ⛔ pas un silence (correctif de revue) : cette
    #    table ne gardait que SES propres cles, si bien qu'un scenario ajoute
    #    COTE OUTIL n'etait juge par PERSONNE.
    inconnus = sorted(set(vus) - set(TEMOINS_DECISION))
    if inconnus:
        return False, ("⛔ %d SCENARIO(S) QUE ⛔ PERSONNE NE JUGE : %s — l'outil "
                       "en declare plus que cette table" % (len(inconnus),
                                                            " · ".join(inconnus)))
    return True, "%d scenarios DECIDES comme declare" % len(TEMOINS_DECISION)


def le_releve_compte_juste(fichiers):
    """Le relevé COMPTE-t-il juste ? ⛔ C'est joue sur une FIXTURE, ⛔ pas cru.

    🔴 DEMONSTRATION DU 2026-09-12 : remplacer les deux `e.count > 0` du relevé
       par `true` — une mutation qui COMPILE — rendait `100/100 fonctions`,
       `190/190 blocs`, `0 bloc mort` et **rc=0**, et cette gate restait a
       `76 OK / 0 KO`. Le plancher 92/120 cessait d'etre un plancher, et ⛔ RIEN
       n'observait le comptage. ⇒ une couverture FIXTURE aux comptes CONNUS
       traverse `lireCouverture` PUIS la boucle, et la ligne est confrontee."""
    rc, sortie = _node_dans_copie(fichiers, COUVERTURE, ("--temoin-comptage",),
                                  DELAI_TEMOIN)
    if rc is None:
        return False, ("⛔ le temoin de comptage n'a pas pu etre lance : %s"
                       % (sortie or "").strip()[-90:])
    if rc != 0 or TEMOIN_COMPTAGE not in (sortie or ""):
        return False, ("⛔ rc=%s et la ligne attendue est ABSENTE : le comptage "
                       "de couverture ⛔ n'est observe par RIEN — lu : %s"
                       % (rc, " ".join((sortie or "").split())[-110:]))
    return True, "la fixture rend %s" % TEMOIN_COMPTAGE.split("TEMOIN COMPTAGE ")[1]


def _refus_de_bind(self, *a, **k):
    """⛔ LE `bind` EST EMPECHE — patron de `verif_entree_dn82.py`."""
    raise OSError(errno.EADDRNOTAVAIL, "bind refuse par le temoin de cette gate")


def le_prerequis_bind_est_joue(fichiers):
    """Le SECOND prerequis est-il JOUE — et rend-il le ROUGE **NOMME** ?

    🔴 ⛔ AUCUN DES 60 MUTANTS NE POUVAIT L'ATTEINDRE : le bras `if _MUTANT:` du
       refus de `bind` pouvait disparaitre sans que rien ne rougisse. Or c'est le
       defaut le plus cher de `dn8-1` — `tools/verif_campagne_dn56.py` exige
       `rc=1` de CHAQUE mutant et ⛔ elle n'est PAS `NON_JOUABLE` : un `rc=4`
       sous mutant rend la suite ROUGE **sur un runner seulement**.
    ⚠️ LE TEMOIN JOUE CE FICHIER-CI DANS UNE COPIE JETABLE, avec
       `DN73_TEMOIN_BIND=1` : le fils patche `socket.socket.bind` et sort AVANT
       de lire le moindre fichier, donc ⛔ aucune recursion et ⛔ aucun port."""
    tmp = tempfile.mkdtemp(prefix="dn73-bind-")
    try:
        os.makedirs(os.path.join(tmp, "tools"))
        with io.open(os.path.join(tmp, MOI), "w", encoding="utf-8") as fh:
            fh.write(fichiers.get(MOI, ""))
        shutil.copy(os.path.join(RACINE, "tools", "dn_gates.py"),
                    os.path.join(tmp, "tools", "dn_gates.py"))
        env = dict(os.environ, DN73_TEMOIN_BIND="1")
        sorties = {}
        for cle, extra in (("normal", ()), ("mutant", ("--mutant", "1"))):
            r = subprocess.run([sys.executable, os.path.join(tmp, MOI)]
                               + list(extra), cwd=tmp, env=env,
                               timeout=DELAI_TEMOIN * 4,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
            sorties[cle] = (r.returncode,
                            r.stdout.decode("utf-8", "replace"))
    except (OSError, subprocess.SubprocessError) as exc:
        return False, "⛔ le temoin de `bind` n'a pas pu etre joue : %s" % exc
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    rc_n = sorties["normal"][0]
    rc_m, out_m = sorties["mutant"]
    if rc_n != 4:
        return False, ("⛔ SANS MUTANT, un `bind` refuse rend rc=%s au lieu de 4 "
                       "— c'est ce 4 que `tools/run_gates.sh` declare" % rc_n)
    if rc_m != 1 or "PREREQUIS ABSENT SOUS MUTANT" not in out_m:
        return False, ("⛔ SOUS MUTANT, un `bind` refuse rend rc=%s %s— `dn56` "
                       "exige rc=1 de CHAQUE mutant, et elle ⛔ n'est PAS "
                       "NON_JOUABLE : c'est le defaut le plus cher de `dn8-1`"
                       % (rc_m, "SANS le KO nomme " if rc_m == 1 else ""))
    return True, "rc=4 sans mutant · rc=1 **NOMME** sous mutant"


def le_ci_joue_le_releve(ci):
    """L'etape de couverture existe-t-elle, et son verdict COMPTE-t-il ?

    🔴 L'UNIQUE POINT D'APPLICATION DES SEUILS VIT DANS CE FICHIER, et ⛔ aucune
       gate ne le lisait : supprimer l'etape — ou lui ajouter `continue-on-error`
       ou un `|| true` — laissait TOUTE la suite verte, seuils compris.
    ⚠️ AVEUGLEMENT DECLARE : ce controle lit du YAML **EN TEXTE**, ⛔ sans
       parseur (`yaml` n'est pas dans la bibliotheque standard, et la CI de ce
       depot interdit `pip install`). Ce qu'il juge est donc une propriete
       TEXTUELLE du bloc de l'etape, et il le DIT ici plutot que de le taire."""
    i = (ci or "").find("banc_couverture_dn82.mjs")
    if i < 0:
        return False, ("⛔ `gates.yml` ⛔ N'INVOQUE PLUS le relevé de couverture "
                       "— les deux seuils ne sont alors appliques par PERSONNE")
    deb = ci.rfind("\n      - name:", 0, i)
    fin = ci.find("\n      - name:", i)
    bloc = ci[deb if deb >= 0 else 0:fin if fin >= 0 else len(ci)]
    ligne = bloc.split("banc_couverture_dn82.mjs")[1].split("\n")[0]
    mauvais = []
    if "continue-on-error" in bloc:
        mauvais.append("`continue-on-error` dans l'etape")
    if "|| true" in ligne:
        mauvais.append("`|| true` sur la ligne du relevé")
    if mauvais:
        return False, ("⛔ %s — un verdict qu'on desarme est un seuil qu'on "
                       "n'applique pas" % " · ".join(mauvais))
    return True, "l'etape invoque le relevé, et son `rc` COMPTE"


def position_executee(texte, jeton):
    """L'offset du jeton sur une ligne qui N'EST PAS un commentaire.

    🔴 POURQUOI, ET C'EST DEMONTRE (2026-09-12) : un `find` nu prenait le PREMIER
       jeton du fichier, commentaires compris. Un mutant qui DEPLACE
       `asserterDom(montes)` apres `runInContext` **en laissant son nom dans un
       commentaire juste avant** sortait donc VERT — la position lue etait celle
       de la CITATION. Un jeton cite en commentaire ⛔ n'est pas du code."""
    # 🔴 LES COMMENTAIRES SONT **RETIRES**, ⛔ plus devines a un PREFIXE de ligne
    #    (correctif de revue du 2026-09-12). DEMONTRE : un `// asserterDom(montes);`
    #    en QUEUE d'une ligne executable, l'assertion deplacee APRES
    #    `runInContext`, et cette gate rendait `76 OK / 0 KO`.
    #    ⚠️ `dn_gates.sans_commentaires` retire les blocs `/* … */` et les lignes
    #       ENTIEREMENT commentees ; la QUEUE de ligne, elle, se retire ici.
    #    ⛔ `://` EST EPARGNE : sinon une URL `http://…` couperait la ligne en
    #       deux, et le jeton qui la suit deviendrait invisible.
    propre = re.sub(r"(?m)(?<!:)//.*$", "", dn_gates.sans_commentaires(texte or ""))
    return propre.find(jeton)


def jouer_le_banc(fichiers, extra=(), delai=None, base=None):
    """ECRIT la page et le banc dans un repertoire JETABLE, hors du depot, et
    LANCE le banc dessus.

    🔴 ⛔ AUCUNE ECRITURE DANS L'ARBRE, JAMAIS — pas meme pour un mutant. La
       page mutee vit dans un temporaire que cette fonction detruit elle-meme.
    ⚠️ `rc is None` est un DEPASSEMENT DE DELAI **ou un lancement impossible**,
       ⛔ pas un verdict du banc : il remonte tel quel, et l'appelant le rend en
       KO. Les deux motifs sont DISTINGUES dans le texte — un moteur present mais
       non executable ⛔ n'est PAS « trop lent », et confondre les deux enverrait
       chercher un banc trop long la ou il y a un droit manquant."""
    # 🔴 LA PREPARATION ECHOUE **FERME**, AVEC SON MOTIF (voir `_node_dans_copie`).
    argv = ["--page", PAGE, "--delai", str(DELAI_PAGE),
            "--delai-cas", str(DELAI_CAS),
            # ⚠️ LE MANIFESTE DE L'ARBRE REEL : la copie jetable ⛔ ne porte pas
            #    `charge/`, et la version attendue ⛔ ne s'invente pas.
            "--manifeste", os.path.join(RACINE, MANIFESTE_CHARGE)] + list(extra)
    # 🔴 LA BASE EST PASSEE PAR LA **GATE**, ⛔ jamais devinee par le banc :
    #    c'est elle qui a lie le port, et c'est elle qui le fermera.
    if base:
        argv += ["--base", base]
    return _node_dans_copie(fichiers, BANC, argv,
                            DELAI_BANC if delai is None else delai)


def le_banc_a_rendu_son_bilan(sortie):
    """Le banc a-t-il rendu son bilan ? ⛔ Une sortie sans `BANC :` est la
    signature d'un banc MORT, ⛔ pas d'un banc vert."""
    m = RE_BILAN_BANC.search(sortie or "")
    if not m:
        return False, None
    return True, (int(m.group(1)), int(m.group(2)))


def les_cas_de_la_matrice_sont_joues(sortie):
    """TOUT cas DECLARE est-il joue, **PAR SON NOM** ?

    🔴 ELARGI LE 2026-09-12, ET L'AC LE DEMANDAIT : seules les NEUF lignes de la
       matrice etaient nommees ; les 33 autres n'etaient que COMPTEES par `(c3)`.
       Un compte dit qu'il manque un cas, ⛔ jamais LEQUEL — et c'est toujours
       celui qu'on n'aurait pas remarque. ⇒ les trois listes declarees sont
       confrontees aux noms REELLEMENT emis."""
    joues = {m.group(1) for m in RE_CAS.finditer(sortie or "")}
    attendus = CAS_MATRICE + CAS_HORS_MATRICE + CAS_HTTP
    manquants = [c for c in attendus if c not in joues]
    return not manquants, (manquants, len(joues))


def le_banc_joue_tous_ses_cas(sortie):
    """Le compte emis egale-t-il le compte attendu ?"""
    n = len(RE_CAS.findall(sortie or ""))
    return n == CAS_ATTENDUS, n


def tout_cas_rend_ok(sortie):
    """Rend `(ok, [cas rouges avec leur motif])`."""
    rouges = [(m.group(1), m.group(3).strip())
              for m in RE_CAS.finditer(sortie or "") if m.group(2) == "KO"]
    return not rouges, rouges


def le_banc_execute_la_page(banc):
    """Le banc LIT-il la page et l'EVALUE-t-il, plutot que de la recopier ?"""
    absentes = [a for a in ANCRES_EXECUTION if a not in (banc or "")]
    recopie = ANCRE_RECOPIE in (banc or "")
    return not absentes and not recopie, (absentes, recopie)


def le_banc_sort_ferme(fichiers):
    """Le banc SORT-IL EN NON-ZERO quand sa chaine ne se resout pas ?

    🔴 C'EST JOUE, ⛔ PAS LU : `--temoin-chaine` REPLANTE le cas — une chaine
       qui ne se resout jamais — et on exige rc != 0 **et** ⛔ AUCUNE ligne de
       bilan. Un banc qui rend 0 sur une liste tronquee annonce un succes qu'il
       n'a pas mesure."""
    rc, sortie = jouer_le_banc(fichiers, (DRAPEAU_TEMOIN,), DELAI_TEMOIN)
    a_bilan = RE_BILAN_BANC.search(sortie or "") is not None
    signe = SIGNATURE_FILET in (sortie or "")
    return (rc == RC_FILET and signe and not a_bilan), (rc, a_bilan, signe, sortie)


def le_banc_regle_les_attentes(banc):
    """Le banc REPOSE-t-il les attentes de la page, et echoue-t-il FERME ?"""
    absentes = [a for a in ANCRES_DELAIS if a not in (banc or "")]
    return not absentes, absentes


def le_banc_exerce_les_preconditions(banc):
    """Le banc EXERCE-t-il les chemins de precondition, ⛔ ou les recopie-t-il ?

    🔴 TROIS TROUS DIFFERENTS, FERMES ENSEMBLE (`dn7-6`) :
       · la fabrique de desarmement est **ENVELOPPEE** — la REMPLACER ferait
         fabriquer au banc la suite qu'il attend, et il sortirait VERT sur une
         page ou plus rien ne se grise ;
       · le temoin d'etape est MONTE **AVANT** `runInContext` — ce fichier
         documente deja le cas vecu, et `dn7-5` en avait laisse le residu ;
       · le chemin est ROUTE depuis la fonction de cas, sinon il ne joue pas."""
    absentes = [a for a in ANCRES_PRECONDITION if a not in (banc or "")]
    if absentes:
        return False, ("ancre(s) absente(s) : %s"
                       % " · ".join(x[:38] for x in absentes[:2]))
    i_montage = position_executee(banc, A_MONTAGE_PRECONDITION)
    i_exec = position_executee(banc, A_EXECUTION)
    if i_montage < 0 or i_exec < 0 or i_montage > i_exec:
        return False, ("le temoin d'etape est monte APRES l'execution — la "
                       "branche serait MORTE, et le banc VERT dessus")
    return True, ("fabrique ENVELOPPEE, temoins montes avant l'execution, "
                  "chemin route")


def le_banc_juge_la_suite(banc):
    """Le banc juge-t-il la SUITE des issues, ⛔ pas seulement la derniere ?"""
    absentes = [a for a in ANCRES_SUITE if a not in (banc or "")]
    return not absentes, absentes


# ══ LE VRAI SERVEUR DU PRODUIT — ⛔ PAS UN DOUBLE ══════════════════════════

def la_boucle_locale_accepte_un_bind():
    """Un `bind` sur `127.0.0.1:0` est-il seulement possible ici ?

    🔴 PRE-VOL, ⛔ PAS UN VERDICT : une boucle locale filtree (politique,
       conteneur durci) ⛔ n'est pas un defaut de ce depot. La sonde prend un
       port ephemere et le rend IMMEDIATEMENT — elle ⛔ ne parle a personne."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", 0))
        finally:
            s.close()
        return True, None
    except OSError as exc:
        return False, "%s: %s" % (type(exc).__name__, exc)


def charger_produit(source):
    """Le produit, COMPILE DEPUIS SON TEXTE — ⛔ jamais importe du disque.

    🔴 DEUX RAISONS, ET LES DEUX SONT MESUREES AILLEURS DANS CE DEPOT :
       · un mutant doit pouvoir CHANGER ce texte, sinon il ne prouve rien ;
       · `import` consulte `__pycache__`, dont la validation repose sur
         (mtime, taille) : une gate a deja juge du BYTECODE PERIME et publie un
         verdict FAUX avec l'autorite d'une mesure.
    ⚠️ `__file__` pointe le fichier REEL : c'est lui qui fixe `ICI`, donc `PAGE`
       et `CHARGE`. Le produit ne fait que LIRE ces chemins."""
    chemin = os.path.join(RACINE, PRODUIT)
    mod = importlib.util.module_from_spec(
        importlib.util.spec_from_loader("dn_installeur_dn82", loader=None))
    mod.__file__ = chemin
    exec(compile(source, chemin, "exec"), mod.__dict__)      # noqa: S102
    return mod


def lier_le_serveur(source):
    """Lie le VRAI `ThreadingHTTPServer` du produit sur `127.0.0.1:0`.

    🔴 ⛔ AUCUN GESTE REEL N'ATTEINT LA MACHINE, ET LA LISTE EST EXHAUSTIVE :
       · `_powershell` — l'UNIQUE porte par laquelle ce serveur lancerait quoi
         que ce soit (`stop`, `retirer`, `poser`, l'enumeration des ports) ;
       · `localiser_pilote` / `_PILOTE` / `_lire` — un double de papier, ⛔ pas
         le vrai `dn_agent_tour.ps1` ;
       · `lhm_present` — sans quoi cette gate ouvrirait de VRAIES connexions TCP
         vers un service qu'elle n'a pas lie (`verif_installeur_dn71.py` en a
         deja paye QUATRE par passe) ;
       · `_jouer_dependances` — ⛔ IL LANCE UN `pip install` POUR DE VRAI. La
         ROUTE reste exercee (le verrou, la reponse, le relais) ; le GESTE, ⛔
         jamais ;
       · `dependance_presente` — deux interpreteurs par appel, et l'etat de CETTE
         machine ;
       · `arbre_parent_present` — AJOUTEE LE 2026-09-12 : cette liste se
         disait EXHAUSTIVE et oubliait cette sonde, si bien que le `/api/etat`
         servi portait un fait de CE CLONE (`README.md` et
         `tools/dn_agent_tour.ps1` presents au-dessus de `installeur/`) au lieu
         d'un fait de BANC declare. `verif_entree_dn82.py` la doublait deja.
    ⚠️ `srv.dn_port` EST LE PORT **RELU**, ⛔ pas `PORT_DEMANDE` (qui vaut 0) :
       c'est lui que `_refus()` compare aux en-tetes `Host` et `Origin`."""
    try:
        m = charger_produit(source)
    except Exception as exc:                              # noqa: BLE001
        return None, None, ("⛔ LE PRODUIT NE SE CHARGE PAS : %s: %s"
                            % (type(exc).__name__, str(exc)[:110]))
    pilote = os.path.join(RACINE, OUTIL)
    # ⚠️ LA COMMANDE RENDUE EST CELLE QUI **AURAIT** ETE LANCEE, ⛔ pas un
    #    texte de remplissage : la page la RELAIE telle quelle a l'ecran, et un
    #    faux « -File x y » ferait mesurer un transcript qui ne ressemble a rien.
    m._powershell = lambda arguments, timeout=90: (
        0, "sortie de papier", ["powershell"] + list(arguments), None)
    m.localiser_pilote = lambda: (pilote, "double de papier")
    m._PILOTE.update(chemin=pilote, origine="double de papier")
    m._lire = lambda _c: PS1_DE_PAPIER
    m.lhm_present = lambda: None
    # 🔴 ET `dependance_presente` — DEUX INTERPRETEURS PAR APPEL, MESURES : `GET
    #    /api/etat` a **175,2 ms** median (146-289, n=8) contre **2,2 ms** une
    #    fois doublee, et elle rendait l'etat de **CETTE** machine (`psutil`
    #    absent ici) au lieu d'un fait de banc DECLARE.
    m.dependance_presente = lambda module, sans_site_utilisateur=False: True
    m.arbre_parent_present = lambda: True
    m._jouer_dependances = lambda: {
        "commande": "pip install --user psutil pyserial",
        "sortie": "sortie de papier", "rc": 0, "rc_pose_par": "l'outil",
        "verdict": "double de papier — ⛔ AUCUN `pip` n'a tourne"}
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", 0), m.Poignee)
    except OSError as exc:
        return None, None, ("⛔ `bind` REFUSE sur 127.0.0.1:0 : %s: %s"
                            % (type(exc).__name__, exc))
    srv.dn_port = srv.server_address[1]
    fil = threading.Thread(target=srv.serve_forever, daemon=True)
    fil.start()
    return srv, m, None


def le_banc_asserte_son_dom(fichiers, banc):
    """Le banc REFUSE-t-il un DOM amputé, et le refuse-t-il **AVANT** ?

    🔴 C'EST JOUE, ⛔ PAS LU : `--temoin-dom` prive un element MONTE de sa
       capacite — la faute EXACTE que `dn7-4` a mesuree, ou le banc rendait
       `18 OK, 0 KO` sur deux branches MORTES — et on exige le code declare, sa
       signature, et ⛔ AUCUNE ligne de bilan.
    ⚠️ ET L'ORDRE EST LU DANS LE FICHIER : une assertion jouee APRES
       `runInContext` constaterait un DOM sur lequel la page a DEJA lu ce
       qu'elle avait a lire. Le temoin ⛔ ne peut PAS voir ca — il rougirait
       pareil — donc la position est gardee a part."""
    rc, sortie = jouer_le_banc(fichiers, (DRAPEAU_TEMOIN_DOM,), DELAI_TEMOIN)
    a_bilan = RE_BILAN_BANC.search(sortie or "") is not None
    signe = SIGNATURE_DOM in (sortie or "")
    # 🔴 SUR DES LIGNES DE **CODE**, ⛔ PAS SUR UNE CITATION : un mutant qui
    #    deplace l'assertion APRES `runInContext` en laissant son nom dans un
    #    commentaire juste avant sortait VERT (demontre le 2026-09-12).
    i_ass = position_executee(banc, A_ASSERTION_DOM)
    i_exe = position_executee(banc, A_EXECUTION)
    avant = 0 <= i_ass < i_exe
    return (rc == RC_DOM and signe and not a_bilan and avant), (
        rc, a_bilan, signe, avant, sortie)


def le_banc_a_joint_le_serveur(sortie, port):
    """Le banc a-t-il recu la base de CETTE gate — le PORT, ⛔ pas « une base » ?

    ⛔ UNE BASE NON VIDE NE PROUVE RIEN : elle serait vraie d'une base inventee.
       Ce qui tranche est l'APPARIEMENT avec le port que cette gate a lie."""
    m = RE_BASE_BANC.search(sortie or "")
    if not m:
        return False, None
    return int(m.group(1)) == port, int(m.group(1))


def les_seuils_de_couverture_battent_les_bornes(couverture):
    """Les seuils DECLARES dans le relevé battent-ils les bornes d'entree ?

    🔴 UN SEUIL QU'ON ABAISSE POUR REVERDIR EST UNE GATE QU'ON DEBRANCHE. Les
       deux bornes (72 fonctions, 87 blocs, mesurees le 2026-09-11 AVANT
       `dn8-2`) sont ce que la marche s'engage a BATTRE ; les redescendre en
       dessous rend ce contrôle ROUGE.
    ⚠️ ET LE SEUIL PORTE SUR LE **NUMERATEUR**, ⛔ pas sur un ratio : V8 n'emet
       les blocs internes d'une fonction QUE LORSQU'ELLE A ETE COMPILEE, donc le
       DENOMINATEUR MONTE avec la couverture (mesure du 2026-09-11 : 93⇒99
       fonctions et 141⇒170 blocs declares, a source INCHANGEE). Un seuil sur un
       ratio baisserait tout seul a mesure qu'on couvre mieux."""
    mf = RE_SEUIL_FONCTIONS.search(couverture or "")
    mb = RE_SEUIL_BLOCS.search(couverture or "")
    if not mf or not mb:
        return False, "⛔ SEUIL(S) NON DECLARE(S) dans %s" % COUVERTURE
    f, b = int(mf.group(1)), int(mb.group(1))
    if f <= BORNE_COUVERTURE_FONCTIONS or b <= BORNE_COUVERTURE_BLOCS:
        return False, ("⛔ SEUIL SOUS SA BORNE : fonctions %d (borne %d) · "
                       "blocs %d (borne %d)"
                       % (f, BORNE_COUVERTURE_FONCTIONS, b,
                          BORNE_COUVERTURE_BLOCS))
    return True, ("fonctions >= %d (borne d'entree %d) · blocs >= %d (borne %d)"
                  % (f, BORNE_COUVERTURE_FONCTIONS, b, BORNE_COUVERTURE_BLOCS))


# ═══════════════════════════ LES MUTANTS ═══════════════════════════════════

def muter(etat):
    """REPLANTE une faute DANS L'ETAT — ⛔ jamais dans un fichier du depot.

    🔴 SEPT MUTANTS SUR SEIZE MUTENT **LA PAGE**, ⛔ pas la gate ni ses
       predicats : ce que ce banc garde, c'est le COMPORTEMENT DU PRODUIT, et
       une faute replantee ailleurs ne le prouverait pas.
    ⚠️ Tout corps VERIFIE son ancre d'abord et rend `e` INCHANGE : un corps qui
       LEVE serait rendu en `rc=1` + `BILAN` + `[KO ]` — mot pour mot le contrat
       que la campagne appelle « sain », et un mutant PERIME passerait pour un
       gardien vivant. ⛔ Le mutant 12 leve EXPRES : il est le temoin de ce cas.
    """
    e = copy.deepcopy(etat)
    p, r = e["fichiers"], e["regles"]

    if _MUTANT == 1:
        a = ('  if (code === LANGUE_DALLE_DEFAUT) {\n'
             '    blocMot("etat-langue", "langue.defaut-anglais");\n'
             '    languePort("langue.defaut-anglais");\n'
             '    return null;\n'
             '  }\n')
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "", 1)
    elif _MUTANT == 2:
        a = ("            var relue = "
             "langueArmer(RE_INVITE_CARTE, DELAI_REPONSE, r2.reste);")
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '            blocMot("etat-langue", "langue.posee");\n' + a, 1)
    elif _MUTANT == 3:
        # 🔴 ON ECHANGE LES **SITES D'APPEL**, ⛔ PAS LES CLES DE LA TABLE.
        #    MESURE : un echange GLOBAL emportait aussi les deux entrees de
        #    `MOTS` — les textes suivaient leurs cles, rien ne changeait a
        #    l'ecran, et le mutant sortait VERT en ayant pourtant change des
        #    octets. ⛔ Un no-op DEGUISE echappe a la garde du no-op.
        t = p.get(PAGE, "")
        a = 'blocMot("etat-langue", "langue.refusee")'
        b = 'blocMot("etat-langue", "langue.sans-reponse")'
        if a not in t or b not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(a, "@@X@@").replace(b, a).replace("@@X@@", b)
    elif _MUTANT == 4:
        a = ('    var invite = langueArmer(RE_INVITE_CARTE, DELAI_INVITE, "");\n'
             '    var reveil = consoleEcrire("");\n'
             '    return reveil.then(function () { return invite; })')
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '    var reveil = consoleEcrire("");\n'
               '    return reveil.then(function () '
               '{ return { texte: "", vu: true, reste: "" }; })', 1)
    elif _MUTANT == 5:
        a = "  if (langueEnVol) { return null; }\n"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "", 1)
    elif _MUTANT == 6:
        a = ('  return w.write(new TextEncoder().encode(ligne + "\\n"))'
             '.then(function () {\n'
             '    w.releaseLock();\n'
             '    return null;\n'
             '  }, function (err) {')
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '  return w.write(new TextEncoder().encode(ligne + "\\n"))'
               '.then(function () {\n'
               '    return null;\n'
               '  }, function (err) {', 1)
    elif _MUTANT == 7:
        # 🔴 LA FAUTE REPLANTEE A CHANGE AVEC LE PRODUIT, ET C'EST ECRIT PLUTOT
        #    QUE TU. Sa 1re redaction retirait `langueMasquer()` pour laisser le
        #    « ⏳ en cours » a cote du refus — ⛔ PERIMEE : depuis que ce chemin
        #    ANNONCE quelque chose, `blocMot` ecrase le temoin de toute facon, et
        #    le mutant etait devenu un NO-OP DEGUISE. ⇒ il replante desormais le
        #    defaut que la revue a trouve : le geste se TAIT quand le port n'est
        #    pas venu, et trois issues laissent le cadre VIDE.
        a = ('    blocMot("etat-langue", "langue.port-indisponible");\n'
             '    languePort("langue.port-indisponible");\n')
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "", 1)
    elif _MUTANT == 8:
        # 🔴 IL **RECOPIE POUR DE VRAI**, ⛔ IL NE CITE PAS LE JETON DANS UN
        #    COMMENTAIRE. MESURE : la version d'avant posait
        #    `function poserLangueDalle` dans un COMMENTAIRE — `(c5)` rougissait
        #    sur la CHAINE pendant que le banc continuait d'evaluer la page et
        #    rendait `10 OK, 0 KO`. Ca prouvait un `grep`, ⛔ pas la propriete.
        #    ⇒ ici, l'evaluation de la page DISPARAIT et le harnais se donne sa
        #      propre logique : la faute est REPLANTEE, et le banc en rougit.
        # ⚠️ ANCRE RECALEE LE 2026-09-11 (`dn8-2`) : `faireContexte` rend
        #    desormais AUSSI les `traces` du pont HTTP. Sans ce recalage le
        #    mutant devenait PERIME (`rc=3`) — un gardien MORT que seul le
        #    rejeu complet de la campagne pouvait voir.
        a = ('  vm.runInContext(src, ctx, { filename: '
             '"installeur/index.html<script>" });\n'
             '  return { ctx, els, traces };')
        if a not in p.get(BANC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BANC] = p[BANC].replace(
            a, "  ctx.blocMot = function () { return null; };\n"
               "  ctx.consoleEcrire = function () "
               "{ return Promise.resolve(null); };\n"
               "  ctx.poserLangueDalle = function poserLangueDalle() "
               "{ return null; };\n"
               "  return { ctx, els, traces };", 1)
    elif _MUTANT == 9:
        # ⚠️ ANCRE RECALEE LE 2026-09-12 : le jugement d'un cas vit desormais
        #    dans `juger()`, parce que les cas se jouent en PARALLELE BORNE.
        #    ⛔ La faute replantee ⛔ n'a pas bouge d'un mot.
        a = "  const succesJuste = posees === 0\n" \
            "    || (posees === 1 && r.suite[r.suite.length - 1] === \"langue.posee\");"
        if a not in p.get(BANC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BANC] = p[BANC].replace(a, "  const succesJuste = true;", 1)
    elif _MUTANT == 10:
        # 🔴 IL **RETIRE** LE CAS, ⛔ IL NE LE RENOMME PAS. MESURE : le renommer
        #    ne faisait rougir que `(c2)` — le banc emettait toujours DIX cas,
        #    donc `(c3)` restait VERT alors que ce mutant le declare pour cible.
        #    ⇒ `(c3)` etait garde par un mutant qui ⛔ NE LE FAISAIT PAS ROUGIR,
        #      et la reciproque `(c7)` ⛔ ne peut PAS voir ca : elle verifie
        #      qu'un controle est NOMME par un mutant, ⛔ pas qu'il ROUGIT.
        #      C'est le trou exact que ce depot a deja nomme : « N mutants, N
        #      vus rougir » prouve `mutant ⇒ rouge`, ⛔ jamais
        #      `controle ⇒ couvert`.
        t = p.get(BANC, "")
        a = '    nom: "sans-reponse",'
        if a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        i = t.rindex("  {", 0, t.index(a))
        j = t.index("  },", i) + len("  },\n")
        p[BANC] = t[:i] + t[j:]
    elif _MUTANT == 11:
        r["sortie_anticipee"] = True
    elif _MUTANT == 12:
        raise RuntimeError("mutant 12 : corps qui LEVE — c'est son role")
    elif _MUTANT == 13:
        # ⚠️ ON RETIRE LA CIBLE D'UN MUTANT **SEUL SUR SON CONTROLE**. MESURE :
        #    viser le mutant 1 ne prouvait RIEN — six autres mutants gardent
        #    `(c4)`, donc le controle restait couvert et `(c7)` restait VERT.
        e["cibles"][8] = ()
    elif _MUTANT == 14:
        e["cibles"][15] = tuple(e["cibles"][15]) + ("c99",)
    elif _MUTANT == 15:
        e["cibles"][99] = ("c1",)      # une cible pour un mutant INEXISTANT
    elif _MUTANT == 16:
        a = '    console.log("BANC : " + ok + " OK, " + ko + " KO");'
        if a not in p.get(BANC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BANC] = p[BANC].replace(a, '    void ok; void ko;', 1)
    elif _MUTANT == 17:
        # 🔴 LA SEULE LIGNE DE CODE LIVRE QUE `dn7-3` A CHANGEE, REPLANTEE :
        #    `consoleOuvrir()` rendait sa promesse a la MORT du lien. Un
        #    appelant qui a besoin du port attendait alors la fin de ce qu'il
        #    voulait utiliser. MESURE : sans le cas `pose-par-le-selecteur`,
        #    cette regression laissait TOUTES les gates vertes.
        a = "      consoleLire();\n      return true;"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "      return consoleLire();", 1)
    elif _MUTANT == 18:
        a = "if (RE_NVS_REFUSEE.test(r2.texte)) {"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, "if (false && RE_NVS_REFUSEE.test(r2.texte)) {", 1)
    elif _MUTANT == 19:
        a = "var DELAI_INVITE = 6000;"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "var DELAI_INVITE_MS = 6000;", 1)
    elif _MUTANT == 20:
        a = "  }, PLAFOND);"
        if a not in p.get(BANC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BANC] = p[BANC].replace(a, "  }, 24 * 3600 * 1000);", 1)
    elif _MUTANT == 21:
        a = "  ctx.DELAI_INVITE = DELAI_PAGE;\n  ctx.DELAI_REPONSE = DELAI_PAGE;"
        if a not in p.get(BANC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BANC] = p[BANC].replace(a, "", 1)
    elif _MUTANT == 22:
        # ⚠️ IL ECHANGE LES **GESTIONNAIRES**, ⛔ pas les identifiants : la gate
        #    STATIQUE reste verte (les deux boutons appellent toujours
        #    `poserDalle`) — c'est exactement le trou que ce cas comble.
        t2 = p.get(PAGE, "")
        a = 'bDalleEn.addEventListener("click", function () { poserDalle("en"); });'
        b = 'bDalleFr.addEventListener("click", function () { poserDalle("fr"); });'
        if a not in t2 or b not in t2:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t2.replace(
            a, 'bDalleEn.addEventListener("click", function () { poserDalle("fr"); });', 1
        ).replace(
            b, 'bDalleFr.addEventListener("click", function () { poserDalle("en"); });', 1)
    elif _MUTANT == 23:
        # ⚠️ ANCRE MISE A JOUR LE 2026-09-10 (`dn7-6`), ⛔ PAS PAR CONFORT : le
        #    desarmement passe desormais par LA fabrique commune, et l'ancre
        #    d'avant — ~~`bLanguePoser.disabled = !(…)`~~ — a disparu du
        #    produit. Un mutant dont l'ancre a disparu rend l'etat INCHANGE,
        #    donc `rc=3`, donc il tombe dans les MUETS de
        #    `tools/verif_campagne_dn56.py` : c'est une gate D'UN AUTRE SUJET
        #    qui rougit sur ce qu'une autre marche a ecrit. La FAUTE
        #    REPLANTEE, elle, ⛔ n'a pas bouge d'un mot : la polarite est
        #    INVERSEE, et le geste s'offre justement quand le flash est
        #    impossible.
        a = ('  armerGeste("b-langue-poser",\n'
             "             !!(blocInstaller && blocInstaller.hidden === false),")
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '  armerGeste("b-langue-poser",\n'
               "             !(blocInstaller && blocInstaller.hidden === false),",
            1)
    elif _MUTANT == 24:
        a = ('  e.appendChild(portConsole ? paire("langue.port-tenu", undefined, true)\n'
             '                            : paire("langue.port-libre", undefined, true));')
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '  e.appendChild(paire("langue.port-tenu", undefined, true));', 1)
    elif _MUTANT == 25:
        a = ("    relacher();\n    langueDesarmer();\n"
             '    blocMot("etat-langue", "langue.sans-reponse");')
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '    langueDesarmer();\n'
               '    blocMot("etat-langue", "langue.sans-reponse");', 1)
    elif _MUTANT == 26:
        a = "  e.hidden = (txt === \"\" || txt === undefined || txt === null);"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "  e.hidden = false;", 1)
    elif _MUTANT == 27:
        a = 'w.write(new TextEncoder().encode(ligne + "\\n"))'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, 'w.write(new TextEncoder().encode(""))', 1)
    elif _MUTANT == 28:
        a = '    console.log("BANC ⛔ CHAINE NON RESOLUE apres " + PLAFOND + " ms — "'
        if a not in p.get(BANC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BANC] = p[BANC].replace(a, '    console.log("BANC interrompu — "', 1)
    elif _MUTANT == 29:
        # 🔴 LA FAUTE QUE `dn7-1` A PAYEE POUR `psutil`, REPLANTEE SUR LHM :
        #    `null` veut dire « la sonde n'a pas pu tourner », ⛔ pas « absent ».
        a = "  var lhmRepond = (e.lhm !== false);"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, "  var lhmRepond = (e.lhm === true);", 1)
    elif _MUTANT == 30:
        # 🔴 LE CONTRESENS QUE `dn7-5` A ECARTE : priver un inconnu du geste
        #    PRINCIPAL pour une dependance de l'AGENT.
        a = ("troisEtats(!!(securise && estLocal && serie && !chargeRefusee\n                            && !moduleAnnonce),")
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, "troisEtats(!!(securise && estLocal && serie && !chargeRefusee "
               "&& !moduleAnnonce && depsCompletes),", 1)
    elif _MUTANT == 31:
        # 🔴 LE HARNAIS QUI SE MESURE LUI-MEME : il REMPLACE la fabrique au lieu
        #    de l'envelopper, et fabrique donc la suite qu'il attend.
        a = ("    const r = vraiArmer(id, permis, cle);\n"
             "    armes.push(id + (permis ? \" ARME\" : \" GRISE=\" + cle));\n"
             "    return r;")
        if a not in p.get(BANC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BANC] = p[BANC].replace(
            a, "    armes.push(id + (permis ? \" ARME\" : \" GRISE=\" + cle));\n"
               "    return null;", 1)
    elif _MUTANT == 32:
        # 🔴 LE MOT SANS SA FORME : le temoin garde l'aplat de l'etat PRECEDENT
        #    sous un texte qui dit autre chose.
        a = '  e.className = "val " + (FORME_ETAPE[cle] || "etat-su-non");'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '  if (FORME_ETAPE[cle]) { e.className = "val "'
               ' + FORME_ETAPE[cle]; }', 1)
    elif _MUTANT == 33:
        a = "  asserterDom(montes);\n"
        if a not in p.get(BANC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BANC] = p[BANC].replace(a, "", 1)
    elif _MUTANT == 34:
        a = ("  asserterDom(montes);\n"
             "\n"
             "  ctx.globalThis = ctx;\n"
             "  vm.createContext(ctx);\n"
             "  vm.runInContext(src, ctx, "
             "{ filename: \"installeur/index.html<script>\" });\n")
        if a not in p.get(BANC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BANC] = p[BANC].replace(
            a, "  ctx.globalThis = ctx;\n"
               "  vm.createContext(ctx);\n"
               "  vm.runInContext(src, ctx, "
               "{ filename: \"installeur/index.html<script>\" });\n"
               "  asserterDom(montes);\n", 1)
    elif _MUTANT == 35:
        # 🔴 L'INVERSION EXACTE QUE `verif_installeur_dn71.py` ⛔ NE PEUT PAS
        #    VOIR : elle appelle le produit PAR IMPORT, donc `do_POST` n'est
        #    traverse par personne chez elle.
        a = ('        if chemin == ROUTE_DEPENDANCES:\n'
             '            self._json(200, jouer_dependances())\n'
             '            return\n'
             '        prefixe = "/api/agent/"\n')
        if a not in p.get(PRODUIT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PRODUIT] = p[PRODUIT].replace(
            a, '        prefixe = ROUTE_DEPENDANCES\n'
               '        if chemin.startswith("/api/agent/"):\n'
               '            self._json(200, jouer_dependances())\n'
               '            return\n', 1)
    elif _MUTANT == 36:
        a = ('    def do_POST(self):\n'
             '        if not self._garde():\n'
             '            return\n')
        if a not in p.get(PRODUIT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PRODUIT] = p[PRODUIT].replace(a, '    def do_POST(self):\n', 1)
    elif _MUTANT == 38:
        # ⛔ L'ANCRE EST **DERIVEE**, ⛔ pas un nombre en dur : un mutant qui
        #    citerait « 80 » deviendrait PERIME le jour ou le seuil monte,
        #    c'est-a-dire le jour ou il compte.
        mm = RE_SEUIL_FONCTIONS.search(p.get(COUVERTURE, ""))
        if not mm:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[COUVERTURE] = p[COUVERTURE].replace(
            mm.group(0), "const SEUIL_FONCTIONS = %d;"
                         % BORNE_COUVERTURE_FONCTIONS, 1)
    elif _MUTANT == 37:
        a = "    BASE = String(v);\n"
        if a not in p.get(BANC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BANC] = p[BANC].replace(
            a, "    BASE = null;   // le pont ⛔ ne se branche pas\n", 1)
    elif _MUTANT == 39:
        a = '  afficher("etat-hors-windows", e.windows === false);'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '  afficher("etat-hors-windows", e.windows !== false);', 1)
    elif _MUTANT == 40:
        a = '      document.getElementById("etat-orphelin").hidden = (e.arbre_parent !== false);'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '      document.getElementById("etat-orphelin").hidden = '
               '(e.arbre_parent === false);', 1)
    elif _MUTANT == 41:
        a = '  afficher("etat-port-tenu", agentPose);'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, '  afficher("etat-port-tenu", !agentPose);', 1)
    elif _MUTANT == 42:
        a = '  afficher("etat-cdn", true);'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, '  afficher("etat-cdn", false);', 1)
    elif _MUTANT == 43:
        a = '      else { bloc.textContent = ""; bloc.hidden = true; }'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '      else { bloc.textContent = ""; bloc.hidden = false; }', 1)
    elif _MUTANT == 44:
        a = '  document.getElementById("etat-not-allowed").hidden = false;\n'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "", 1)
    elif _MUTANT == 45:
        a = '  document.getElementById("etat-unsupported").hidden = false;\n'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "", 1)
    elif _MUTANT == 46:
        a = ('  if (blocInstaller && !moduleAnnonce && !chargeRefusee) {\n'
             '    blocInstaller.hidden = false;\n'
             '  }')
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '  if (blocInstaller && !moduleAnnonce && !chargeRefusee) {\n'
               '    blocInstaller.hidden = true;\n'
               '  }', 1)
    elif _MUTANT == 47:
        a = ('  chargeRefusee = true;\n'
             '  if (blocInstaller) { blocInstaller.hidden = true; }\n')
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, '  chargeRefusee = true;\n', 1)
    elif _MUTANT == 48:
        a = ("     croire qu'on peut le reactiver ; l'encadre, lui, dit le geste. */\n"
             '  if (blocInstaller) { blocInstaller.hidden = true; }\n')
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, "     croire qu'on peut le reactiver ; l'encadre, lui, dit le "
               "geste. */\n", 1)
    elif _MUTANT == 49:
        a = '  e.appendChild(d);\n  e.hidden = false;\n}'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, '  e.appendChild(d);\n  e.hidden = true;\n}', 1)
    elif _MUTANT == 50:
        a = '  afficher("etat-deps", !depsCompletes);'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, '  afficher("etat-deps", depsCompletes);', 1)
    elif _MUTANT == 51:
        a = '  afficher("etat-lhm", !lhmRepond);'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, '  afficher("etat-lhm", lhmRepond);', 1)
    elif _MUTANT == 52:
        # 🔴 L'ORDRE EST LA FAUTE : annuler, RELACHER, puis fermer. Ferme
        #    d'abord, le flux est encore verrouille et `close()` REJETTE.
        a = ('  return fin.then(function () {\n'
             '    return p ? p.close() : null;\n'
             '  }).then(function () {')
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '  return (p ? p.close() : Promise.resolve()).then(function () {\n'
               '    return fin;\n'
               '  }).then(function () {', 1)
    elif _MUTANT == 53:
        a = '  if (consoleFermeture) { return null; }\n'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "", 1)
    elif _MUTANT == 54:
        a = '      boutons.forEach(function (b, i) { if (b) { b.disabled = anciens[i]; } });\n'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "", 1)
    elif _MUTANT == 55:
        # 🔴 CE QUE `verif_installeur_dn71.py` ⛔ NE PEUT PAS VOIR : elle appelle
        #    le produit PAR IMPORT, donc ⛔ aucun en-tete de navigateur ne passe.
        a = '    return tuple("http://" + h for h in _hotes_permis(port))'
        if a not in p.get(PRODUIT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PRODUIT] = p[PRODUIT].replace(
            a, '    return tuple("https://" + h for h in _hotes_permis(port))', 1)
    elif _MUTANT == 61:
        a = ('        if _MUTANT:\n'
             '            ctrl(False, "(c14) le banc parle au VRAI serveur de cette gate",\n'
             '                 "⛔ PREREQUIS ABSENT SOUS MUTANT : %s" % motif_bind)\n'
             '            return bilan(1, "la boucle locale refuse le `bind`")\n')
        if a not in p.get(MOI, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[MOI] = p[MOI].replace(a, "", 1)
    elif _MUTANT == 62:
        a = "        if: always()\n"
        if a not in p.get(CI, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[CI] = p[CI].replace(a, a + "        continue-on-error: true\n", 1)
    elif _MUTANT == 63:
        a = "      if (e.count > 0) { nFe++; }"
        if a not in p.get(COUVERTURE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[COUVERTURE] = p[COUVERTURE].replace(a, "      nFe++;", 1)
    elif _MUTANT == 56:
        # ⛔ IL CITE LE JETON DANS UN COMMENTAIRE : c'est ce qui rendait le
        #    controle VERT quand il lisait la position au premier `find`.
        a = ("  asserterDom(montes);\n"
             "\n"
             "  ctx.globalThis = ctx;\n"
             "  vm.createContext(ctx);\n"
             "  vm.runInContext(src, ctx, "
             "{ filename: \"installeur/index.html<script>\" });\n")
        if a not in p.get(BANC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        # ⛔ LA CITATION EST EN **QUEUE D'UNE LIGNE EXECUTABLE**, ⛔ plus en
        #    tete : c'est la forme DEMONTREE le 2026-09-12 — un `find` qui ne
        #    juge que le PREFIXE de la ligne la prenait pour du code, et la gate
        #    rendait `76 OK / 0 KO` sur une assertion jouee APRES `runInContext`.
        p[BANC] = p[BANC].replace(
            a, "  ctx.globalThis = ctx;   // asserterDom(montes);\n"
               "  vm.createContext(ctx);\n"
               "  vm.runInContext(src, ctx, "
               "{ filename: \"installeur/index.html<script>\" });\n"
               "  asserterDom(montes);\n", 1)
    elif _MUTANT == 57:
        # ⛔ L'ANCRE EST **DERIVEE**, comme celle du mutant 38.
        mm = RE_SEUIL_BLOCS.search(p.get(COUVERTURE, ""))
        if not mm:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[COUVERTURE] = p[COUVERTURE].replace(
            mm.group(0), "const SEUIL_BLOCS = %d;" % BORNE_COUVERTURE_BLOCS, 1)
    elif _MUTANT == 58:
        a = "  const sousF = compte.nFe < SEUIL_FONCTIONS;"
        if a not in p.get(COUVERTURE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[COUVERTURE] = p[COUVERTURE].replace(a, "  const sousF = false;", 1)
    elif _MUTANT == 59:
        a = "  const sousB = compte.nBe < SEUIL_BLOCS;"
        if a not in p.get(COUVERTURE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[COUVERTURE] = p[COUVERTURE].replace(a, "  const sousB = false;", 1)
    elif _MUTANT == 60:
        a = '  const bancSain = banc.rc === 0 && !!m && m[2] === "0";'
        if a not in p.get(COUVERTURE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[COUVERTURE] = p[COUVERTURE].replace(a, "  const bancSain = true;", 1)
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
    """Les identifiants de TOUS les controles de CE fichier, lus A L'AST."""
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


def corps(neuf, regles, cibles, base, port):
    """LE CORPS DU TIR — sorti de `main()` le 2026-09-11 (`dn8-2`).

    🔴 POURQUOI IL EN EST SORTI : le serveur du produit doit etre FERME quoi
       qu'il arrive, et `main()` rend son verdict par SIX chemins differents.
       Un `finally` autour d'un appel unique est la seule forme qui ⛔ ne
       laisse aucun de ces chemins derriere lui — un port laisse ouvert par une
       gate est exactement ce que ce depot reproche a la page.
    """
    # ── (c1)…(c4) LE BANC TOURNE, ET IL REND SES CAS ────────────────────
    print("\n── (c1)…(c4) LE BANC TOURNE, ET CHAQUE CAS REND SON VERDICT ──────")
    rc_banc, sortie = jouer_le_banc(neuf["fichiers"], base=base)
    ok, compte = le_banc_a_rendu_son_bilan(sortie)
    # ⚠️ `rc is None` EST LA MESURE DE **CETTE GATE** (depassement, lancement
    #    impossible), ⛔ pas le verdict du banc. Les deux sont distingues.
    ctrl(ok and rc_banc is not None, "(c1) le banc TOURNE, et il rend son bilan",
         "BANC : %d OK, %d KO (rc=%s)" % (compte[0], compte[1], rc_banc)
         if ok and rc_banc is not None
         else "⛔ %s — une sortie sans `BANC :` est la signature d'un banc MORT, "
              "⛔ pas d'un banc vert"
              % ("le banc n'a pas pu etre lance ou a depasse son delai : %s"
                 % sortie.strip()[-90:] if rc_banc is None
                 else "aucune ligne `BANC :` dans %d octet(s) de sortie"
                      % len(sortie or "")))

    ok, (manquants, joues) = les_cas_de_la_matrice_sont_joues(sortie)
    ctrl(ok, "(c2) tout cas DECLARE est joue, par son NOM",
         "%d cas joues, dont les %d de la matrice et les %d de `--base`"
         % (joues, len(CAS_MATRICE), len(CAS_HTTP)) if ok
         else "⛔ cas DECLARE(S) NON JOUE(S) : %s — un cas qui disparait "
              "retrecit la population SANS RIEN DIRE, et c'est toujours celui "
              "qu'on n'aurait pas remarque" % " ".join(manquants))

    ok, n = le_banc_joue_tous_ses_cas(sortie)
    ctrl(ok, "(c3) le banc joue TOUS les cas qu'il declare",
         "%d cas emis pour %d attendus" % (n, CAS_ATTENDUS) if ok
         else "⛔ %d cas emis pour %d attendus — le compte est la seule chose "
              "qui voit un cas ajoute sans etre declare, ou retire sans etre "
              "dit" % (n, CAS_ATTENDUS))

    ok, rouges = tout_cas_rend_ok(sortie)
    ctrl(ok, "(c4) tout cas du banc rend OK",
         "%d cas, aucun rouge" % n if ok
         else "⛔ %d cas ROUGE(S) : %s"
              % (len(rouges), " · ".join("%s (%s)" % (c, m[:60])
                                         for c, m in rouges[:3])))

    # ── (c5)(c6) CE QUI FAIT DU BANC UN BANC ────────────────────────────
    print("\n── (c5)(c6) LE BANC EXECUTE LA PAGE, ET IL JUGE LA SUITE ─────────")
    banc = neuf["fichiers"].get(BANC, "")
    ok, (absentes, recopie) = le_banc_execute_la_page(banc)
    ctrl(ok, "(c5) le banc EXECUTE la page, ⛔ il ne la recopie pas",
         "il lit le `<script>` et l'evalue" if ok
         else "⛔ %s — un harnais qui rejoue une logique recopiee ne mesure que "
              "lui-meme, et il sortirait VERT sur une page cassee"
              % ("il redefinit chez lui ce qu'il devrait appeler" if recopie
                 else "ancre(s) d'execution absente(s) : %s" % " ".join(absentes)))

    ok, absentes = le_banc_juge_la_suite(banc)
    ctrl(ok, "(c6) le banc juge la SUITE des issues, ⛔ pas la fin",
         "« posee » au plus UNE fois, et EN DERNIER" if ok
         else "⛔ ancre(s) absente(s) : %s — un succes annonce trop tot puis "
              "ECRASE laisse l'ecran final correct et le defaut INVISIBLE ; "
              "c'est mesure, ⛔ pas suppose" % " ".join(absentes))

    # ── (c7)(c8) LE BANC SORT FERME, ET IL REGLE SES ATTENTES ───────────
    print("\n── (c7)(c8) UNE CHAINE NON RESOLUE N'EST PAS UN SUCCES ───────────")
    ok, (rc_t, a_bilan, signe, sortie_t) = le_banc_sort_ferme(neuf["fichiers"])
    ctrl(ok, "(c7) chaine non resolue ⇒ le FILET joue, et il le dit",
         "temoin joue : rc=%d, sa signature imprimee, ⛔ aucun bilan" % RC_FILET
         if ok
         else "⛔ %s — un banc qui rend 0 sur une liste TRONQUEE annonce un "
              "succes qu'il n'a pas mesure, et un `Traceback` sort non nul SANS "
              "bilan exactement comme un filet qui a joue"
              % ("le temoin n'a pas pu etre lance : %s"
                 % (sortie_t or "").strip()[-80:] if rc_t is None
                 else "le temoin a rendu un BILAN alors que sa chaine ⛔ ne "
                      "s'est PAS resolue" if a_bilan
                 else "rc=%s au lieu de %d" % (rc_t, RC_FILET)
                 if rc_t != RC_FILET
                 else "⛔ la SIGNATURE du filet est absente : rc=%d ne prouve "
                      "pas QUI a mis fin au banc" % RC_FILET))

    ok, det = le_banc_exerce_les_preconditions(banc)
    ctrl(ok, "(c12) le banc EXERCE les chemins de precondition", det if ok
         else "⛔ %s — un chemin qu'aucun harnais ne traverse est une gate "
              "verte qui ne garde RIEN, et `dn7-5` en avait laisse le residu "
              "ecrit" % det)

    ok, absentes = le_banc_regle_les_attentes(neuf["fichiers"].get(BANC, ""))
    ctrl(ok, "(c8) le banc REPOSE les attentes de la page",
         "les deux delais sont reposes, et l'absence ECHOUE FERME" if ok
         else "⛔ ancre(s) absente(s) : %s — la campagne rejoue ce banc UNE "
              "FOIS PAR MUTANT, et deux attentes de six secondes figees l'ont "
              "portee a 93 %% de son plafond" % " ".join(absentes))

    # ── (c13)(c14)(c15) CE QUE `dn8-2` AJOUTE ──────────────────────────
    print("\n── (c13)(c14)(c15) LE DOM ASSERTE, LE PONT HTTP, LE SEUIL ───────")
    ok, (rc_d, a_bilan_d, signe_d, avant_d, sortie_d) = le_banc_asserte_son_dom(
        neuf["fichiers"], banc)
    ctrl(ok, "(c13) le banc ASSERTE son DOM, et AVANT d'evaluer",
         "temoin joue : rc=%d, signature imprimee, assertion AVANT "
         "`runInContext`" % RC_DOM if ok
         else "⛔ %s — `dn7-4` a MESURE le cas : sans les trois capacites, DEUX "
              "branches de `montrerSortie()` etaient MORTES et ce banc rendait "
              "`18 OK, 0 KO` dessus"
              % ("le temoin n'a pas pu etre lance : %s"
                 % (sortie_d or "").strip()[-80:] if rc_d is None
                 else "le temoin a rendu un BILAN alors qu'il ⛔ n'a joue AUCUN "
                      "cas" if a_bilan_d
                 else "rc=%s au lieu de %d" % (rc_d, RC_DOM) if rc_d != RC_DOM
                 else "⛔ la SIGNATURE « %s » est absente" % SIGNATURE_DOM
                 if not signe_d
                 else "⛔ L'ASSERTION EST JOUEE **APRES** `runInContext` : elle "
                      "constate un DOM sur lequel la page a DEJA lu ce qu'elle "
                      "avait a lire"))

    ok, vu = le_banc_a_joint_le_serveur(sortie, port)
    ctrl(ok, "(c14) le banc parle au VRAI serveur de cette gate",
         "base annoncee sur le port %d, celui que cette gate a lie" % port
         if ok
         else "⛔ %s — le trajet HTTP ⛔ n'a PAS ete joue, et une INVERSION dans "
              "`do_POST` serait repassee VERTE"
              % ("⛔ AUCUNE base annoncee par le banc" if vu is None
                 else "le banc annonce le port %d, cette gate a lie %d"
                      % (vu, port)))

    ok_s, det_s = les_seuils_de_couverture_battent_les_bornes(
        neuf["fichiers"].get(COUVERTURE, ""))
    ok_t, det_t = le_releve_joue_sa_decision(neuf["fichiers"])
    ok_c, det_c = le_releve_compte_juste(neuf["fichiers"])
    ctrl(ok_s and ok_t and ok_c,
         "(c15) le seuil BAT sa borne, DECIDE, et COMPTE juste",
         "%s · decision : %s · comptage : %s" % (det_s, det_t, det_c)
         if ok_s and ok_t and ok_c
         else "%s%s%s — un seuil qu'on abaisse pour reverdir est une gate qu'on "
              "debranche ; un seuil que ⛔ personne ne joue est un seuil qu'on "
              "CROIT avoir ; et un COMPTAGE que rien n'observe est un plancher "
              "qui n'en est pas un"
              % ("" if ok_s else det_s + " · ", "" if ok_t else det_t + " · ",
                 "" if ok_c else det_c))

    ok, det = le_prerequis_bind_est_joue(neuf["fichiers"])
    ctrl(ok, "(c16) le second prerequis (`bind`) est JOUE", det if ok
         else "%s — un prerequis qu'⛔ aucun mutant n'atteint est un bras de code "
              "qui peut disparaitre SANS QUE RIEN NE ROUGISSE" % det)

    ok, det = le_ci_joue_le_releve(neuf["fichiers"].get(CI, ""))
    ctrl(ok, "(c17) la CI joue le relevé, et son `rc` COMPTE", det if ok
         else "%s — l'UNIQUE point d'application des deux seuils vit dans ce "
              "fichier, et ⛔ aucune gate ne le lisait" % det)

    if regles["sortie_anticipee"]:
        return bilan(0)

    # ── (c9)(c10)(c11) LA RECIPROQUE, MECANIQUE ─────────────────────────
    print("\n── (c9)(c10)(c11) AUCUN CONTROLE GARDE PAR ZERO MUTANT ───────────")
    lus_ast = ids_par_ast()
    reels = set(ids_emis) | (lus_ast or set())
    vises = set()
    for v in cibles.values():
        vises.update(v)
    nus = sorted(reels - vises, key=lambda s: (len(s), s))
    ctrl(not nus and lus_ast is not None,
         "(c9) chaque controle est vise par >= 1 mutant",
         "%d controle(s) lu(s) a l'AST, %d cible(s) declaree(s)"
         % (len(reels), len(vises)) if not nus and lus_ast is not None
         else ("⛔ %d CONTROLE(S) GARDE(S) PAR RIEN : %s"
               % (len(nus), " · ".join(nus)) if nus
               else "⛔ LA SOURCE NE S'ANALYSE PAS A L'AST — la population de "
                    "ce controle est INCONNUE, ⛔ pas vide"))
    perimees = sorted(vises - reels, key=lambda s: (len(s), s))
    ctrl(not perimees, "(c10) chaque cible de mutant est un controle REEL",
         "%d cible(s) confrontee(s)" % len(vises) if not perimees
         else "⛔ %d CIBLE(S) PERIMEE(S) : %s — un mutant qui vise un controle "
              "inexistant ⛔ ne garde rien"
              % (len(perimees), " · ".join(perimees)))
    orph = sorted(set(cibles) - set(MUTANTS))
    sans_cible = sorted(set(MUTANTS) - set(cibles))
    ctrl(not orph and not sans_cible,
         "(c11) `CIBLES` et `MUTANTS` se correspondent",
         "%d mutant(s), %d cible(s), cle a cle" % (len(MUTANTS), len(cibles))
         if not orph and not sans_cible
         else "⛔ cible(s) SANS mutant : %s · mutant(s) SANS cible : %s"
              % (orph or "—", sans_cible or "—"))

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : que la langue soit VRAIMENT")
    print("   posee dans une carte. Le banc joue une carte BIDON ; le bandeau")
    print("   est SUR LA DALLE, et il se lit A L'ŒIL. Et le relachement du")
    print("   verrou sur le chemin d'ECHEC n'est pas exerce ici : c'est la")
    print("   gate STATIQUE qui le garde, avec son mutant.")
    return bilan(1 if ko_total[0] else 0)


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
    print("dn7-3 — LE BANC DE LA POSE EST JOUE, ⛔ PAS SEULEMENT ECRIT"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)

    # ── LE PREREQUIS : `node`. ⛔ PAS UN ROUGE, ⛔ PAS UN VERT ────────────
    # 🔴 UNE GATE VERTE SUR UN BANC QUI N'A PAS TOURNE SERAIT PIRE QUE PAS DE
    #    GATE. ⇒ absence de `node` = rc=4, DECLARE, et `tools/run_gates.sh`
    #    porte la ligne qui l'attend sur un temoin derive de `command -v node`.
    node = shutil.which("node")
    if not node and _MUTANT:
        # 🔴 EN MODE MUTANT, UN PREREQUIS ABSENT EST UN **ROUGE NOMME** (`rc=1`),
        #    ⛔ pas un 4 : `tools/verif_campagne_dn56.py` exige `rc=1` de chaque
        #    mutant et ⛔ elle n'est PAS `NON_JOUABLE`. La docstring le promettait
        #    pour les DEUX prerequis et ⛔ ne le tenait que pour le `bind`
        #    (corrige le 2026-09-12) — une promesse tenue a moitie est un vert
        #    muet sur un runner sans moteur.
        ctrl(False, "(c1) le banc TOURNE, et il rend son bilan",
             "⛔ PREREQUIS ABSENT SOUS MUTANT : `node` est introuvable")
        return bilan(1, "`node` est introuvable")
    if not node:
        print("⛔ PREREQUIS ABSENT : `node` est introuvable dans le PATH.")
        print("   Ce banc EXECUTE le JavaScript de `%s` ; sans moteur, il n'y" % PAGE)
        print("   a rien a jouer. ⛔ Cette gate ⛔ NE SORT PAS VERTE pour")
        print("   autant : elle rend 4, et `tools/run_gates.sh` la declare")
        print("   NON-JOUABLE avec ce motif. Le geste : installer Node.js.")
        return 4
    # ── LE SECOND PREREQUIS : LA BOUCLE LOCALE ACCEPTE UN `bind` ───────
    # 🔴 SONDE **AVANT** LE PREMIER CONTROLE, et pour la meme raison que `node` :
    #    un environnement qui refuse `127.0.0.1:0` (politique, conteneur durci)
    #    ⛔ n'est pas un defaut de ce depot, et une gate VERTE sur un trajet HTTP
    #    qui n'a pas eu lieu serait PIRE que pas de gate.
    # ⚠️ EN MODE MUTANT, C'EST UN **ROUGE NOMME**, ⛔ pas un 4 :
    #    `tools/verif_campagne_dn56.py` exige `rc=1` de chaque mutant et ⛔ elle
    #    n'est PAS `NON_JOUABLE`. C'est le defaut le plus cher de `dn8-1`.
    # 🔴 LE TEMOIN DU SECOND PREREQUIS (`(c16)`) : il FORCE l'echec du `bind`.
    #    ⛔ Il ne DEBRANCHE rien — il replante l'etat « la boucle locale refuse »,
    #    que ⛔ aucun mutant ne pouvait produire.
    if os.environ.get("DN73_TEMOIN_BIND") == "1":
        socket.socket.bind = _refus_de_bind
    liable, motif_bind = la_boucle_locale_accepte_un_bind()
    if not liable:
        if _MUTANT:
            ctrl(False, "(c14) le banc parle au VRAI serveur de cette gate",
                 "⛔ PREREQUIS ABSENT SOUS MUTANT : %s" % motif_bind)
            return bilan(1, "la boucle locale refuse le `bind`")
        print("⛔ PREREQUIS ABSENT : la boucle locale REFUSE le `bind`.")
        print("   %s" % motif_bind)
        print("   Cette gate lie le VRAI serveur de `%s` sur 127.0.0.1:0 pour" % PRODUIT)
        print("   que le banc lui parle. Sans `bind`, il n'y a rien a joindre.")
        print("   ⛔ Elle ⛔ NE SORT PAS VERTE pour autant : elle rend 4, et")
        print("   `tools/run_gates.sh` la declare NON-JOUABLE avec ce motif.")
        print("   Le geste : autoriser la boucle locale (pare-feu, politique).")
        return 4
    print("moteur     : %s" % node)
    print("cibles     : %s" % " · ".join(FIXES))
    # ⚠️ CETTE BANNIERE DISAIT « N'OUVRE AUCUN PORT » **JUSTE AVANT DE LIER UN
    #    PORT TCP** (corrige le 2026-09-12). ⛔ La ligne d'origine n'est pas
    #    effacee : elle est VRAIE du port SERIE, et c'est tout ce qu'elle voulait
    #    dire. Elle etait FAUSSE telle quelle depuis que `dn8-2` lie le serveur.
    print("⛔ CETTE GATE N'OUVRE AUCUN PORT **SERIE** ET NE PARLE A AUCUNE CARTE :")
    print("   le banc joue une carte BIDON. ⚠️ ELLE LIE EN REVANCHE UN PORT TCP")
    print("   sur 127.0.0.1:0 — le VRAI serveur du produit — et elle le FERME")
    print("   dans son `finally`. Que la langue soit VRAIMENT posee se lit AU")
    print("   BANDEAU DE LA DALLE — seance carte, portee au ledger.")

    # ── (c0) LE PRE-VOL ─────────────────────────────────────────────────
    print("\n── (c0) LE PRE-VOL — ⛔ AUCUN CONTROLE SUR DU VIDE ────────────────")
    fichiers = {}
    illisibles = []
    for c in FIXES:
        t = lire(c)
        if t is None:
            illisibles.append(c)
        else:
            fichiers[c] = t
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

    regles = neuf["regles"]
    cibles = neuf["cibles"]

    # ── LE VRAI SERVEUR DU PRODUIT, LIE **UNE FOIS POUR TOUT LE TIR** ──
    # 🔴 UNE FOIS PAR TIR, ⛔ JAMAIS UNE FOIS PAR CAS : la campagne rejoue cette
    #    gate une fois par mutant, et un `bind` par cas se paierait 37 fois par
    #    mutant.
    srv, produit, motif = lier_le_serveur(neuf["fichiers"][PRODUIT])
    if srv is None:
        ctrl(False, "(c14) le banc parle au VRAI serveur de cette gate", motif)
        return bilan(1, "le serveur du produit n'a pas pu etre lie")
    base = "http://127.0.0.1:%d/" % srv.dn_port
    print("serveur    : %s (lie par CETTE gate, ferme dans son `finally`)" % base)
    try:
        return corps(neuf, regles, cibles, base, srv.dn_port)
    finally:
        # 🔴 FERME **QUOI QU'IL ARRIVE** : une gate qui laisse un port ouvert
        #    est le defaut qu'elle reproche a la page.
        srv.shutdown()
        srv.server_close()


if __name__ == "__main__":
    sys.exit(main())

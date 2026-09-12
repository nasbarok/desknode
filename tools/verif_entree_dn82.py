#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn8-2 — LES SIX CODES DU POINT D'ENTREE : **CINQ SONT PROVOQUES**, LE SIXIEME
EST LU DANS LE FLOT.

======================= CE QUE CETTE GATE GARDE, ET POURQUOI ================

`installeur/DeskNode-installeur.bat` est **LE SEUL POINT D'ENTREE** d'un
inconnu, et son en-tete PUBLIE six codes de retour : `0` `2` `3` `4` `5` `6`.
Releve du 2026-09-11, AVANT cette marche : **aucun des six n'etait provoque**.
La seule chose jouee etait `prevol()` **par import**, sur **QUATRE** de ses
issues (`tools/verif_installeur_dn71.py`, `ATTENDU_PREVOL`) — donc `2`, `4` et
`5` n'etaient joues par **RIEN**.

  🔴 ET CE N'EST PAS UNE INQUIETUDE THEORIQUE : LE PRECEDENT EST ECRIT. Sur
     `dn7-1`, remplacer `return 6 if manquantes else 0` par `return 0` laissait
     la gate d'alors a **`25 OK / 0 KO`**. Le `6` est l'instrument MECANIQUE de
     l'ecart declare, publie par le `README` — un code publie que rien ne joue
     est un chiffre a croire sur parole.

── 🔴 CE QUE LA BOUCLE DE REVUE 1 A CHANGE, ET C'ETAIT DEMONTRE ─────────────

La 1re redaction de cette gate appelait `prevol()` **A COTE** de son chemin, et
lisait le `.bat` par BALAYAGE. Quatre mutations l'ont laissee a `36 OK / 0 KO` :

  · `main()` avec `if a.verifier: return 0` — c'est-a-dire le PRECEDENT `dn7-1`
    rejoue UN CRAN PLUS LOIN : `prevol()` rendait toujours ses codes, et
    personne ne regardait ce que le point d'entree en FAISAIT ;
  · `exit /b 0` a la sortie du `.bat` — le relais final EFFACE ;
  · le relais `set "RC=%ERRORLEVEL%"` remplace par `set "RC=0"` — le code du
    Python jete a la poubelle ;
  · une etiquette **HORS TABLE** qui pose `RC=7` — un code que ⛔ personne
    n'annonce, et que l'en-tete ne publie pas.

⇒ les codes sont desormais provoques **PAR `main()` DU PRODUIT**, ⛔ jamais par
  `prevol()` appele a cote. ⚠️ `main()` ⛔ NE PREND AUCUN PARAMETRE : c'est
  `sys.argv` qui est POSE — `--verifier` pour `0`, `3`, `5` et `6`, et
  **`--sans-navigateur`** pour le `4`, parce que sous `--verifier` `main()` REND
  AVANT le `bind` et ⛔ ne peut donc pas le donner. Et le `.bat` est lu comme un
  **FLOT** —
  etiquettes, `goto`, chute d'une ligne sur la suivante, `exit /b` —, ⛔ plus
  comme une suite de lignes.

── COMMENT ELLE S'Y PREND, ET CE QU'ELLE REFUSE DE FAIRE ───────────────────

🔴 **LE PRODUIT EST APPELE, ⛔ JAMAIS RECOPIE.** Un harnais qui rejouerait
   l'arbre de `goto` du `.bat` en Python ne mesurerait que lui-meme — c'est un
   piege que ce depot a deja paye. ⇒ les codes qu'un **Python** rend sont
   provoques en APPELANT `main()` du produit ; ce que **`cmd.exe`** pose est lu
   en **MODELISANT** le flot du `.bat`, etiquette par etiquette.

🔴 **CINQ DES SIX SONT PROVOQUES — `0`, `3`, `4`, `5`, `6` —, ET LE `2` EST LU
   DANS LE FLOT.** ⛔ Cette gate ⛔ ne pretend PAS provoquer le `2` : il est pose
   par `cmd.exe` sur un argument inconnu, et `cmd.exe` n'existe pas sur la CI
   Linux. Ce qu'elle prouve de lui est une propriete de **STRUCTURE** : son
   etiquette `:USAGE` est ATTEIGNABLE depuis la tete du fichier, elle pose
   `RC=2`, et `:FIN` relaie ce `RC` par `exit /b %RC%`.
   ⚠️ Le tir REEL du point d'entree sous `cmd.exe` est **NON JOUE**, et son
      porteur est **AU LEDGER** (`epic-dn8`), ⛔ pas cette gate.

🔴 **TOUT SE JOUE DANS UNE COPIE JETABLE**, ⛔ jamais dans l'arbre : la page est
   REELLEMENT retiree pour provoquer le `3`, la charge REELLEMENT amputee pour
   provoquer le `5`. Une passe de mesure ne chevauche jamais une mutation de
   l'arbre, et la seule facon de le tenir est de muter AILLEURS.

⛔ **AUCUN GESTE REEL N'ATTEINT LA MACHINE** : `_powershell`, `lhm_present`,
   `dependance_presente` (deux interpreteurs par appel) et `_jouer_dependances`
   (qui lance un `pip install` POUR DE VRAI) sont remplaces par des doubles de
   papier. ⛔ AUCUN port n'est lie : le `4` est provoque en **EMPECHANT LE `bind`
   AU NIVEAU `socket`**, ⛔ pas en tentant une liaison, et ⛔ pas en substituant
   le NOM `ThreadingHTTPServer` — un produit qui lierait son port par un autre
   chemin doit rendre `4` quand meme.

── CE QU'ELLE NE PROUVE ⛔ PAS, ECRIT PLUTOT QUE TU ─────────────────────────

⛔ Que `cmd.exe` relaie ces codes (voir ci-dessus : porteur au ledger).
⛔ Que le `0` signifie « ca marche » : il signifie « le pre-vol n'a rien trouve
   a redire ». Ce que la page fait ensuite est le sujet de
   `tools/verif_banc_langue_dn73.py`, qui l'EXECUTE.
⛔ Rien sur la lisibilite de quoi que ce soit — y compris du choix de langue
   dont elle relit pourtant l'etat de depart : ce verdict-la se prend A L'ŒIL
   DE L'OWNER sur la page servie cote Windows.

Emploi :
    python3 tools/verif_entree_dn82.py
    python3 tools/verif_entree_dn82.py --liste-mutants
    python3 tools/verif_entree_dn82.py --mutant <n>

Sortie : 0 si tout passe · 1 sur un vrai defaut · 2 sur un mutant inconnu ·
         3 si le mutant demande est PERIME (il n'a rien change).
"""

import argparse
import ast
import errno
import importlib.util
import io
import os
import re
import shutil
import socket
import sys
import tempfile
import threading
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import dn_gates
except ImportError as _x:                                 # pragma: no cover
    sys.stderr.write(
        "⛔ `tools/dn_gates.py` est INTROUVABLE (%s).\n"
        "   Cette gate importe les helpers partages : sans eux elle ⛔ ne peut\n"
        "   pas compter ses controles. Le module vit DANS ce depot, a cote de\n"
        "   ce fichier — c'est un defaut, ⛔ pas un prerequis d'environnement.\n"
        % _x)
    sys.exit(1)

# ⛔ ALIAS, ⛔ PAS DES RE-DEFINITIONS : `verif_harnais_dn81.py` (c1d) rougit sur
#    toute gate du perimetre `dn8` qui RE-DEFINIT un des huit noms partages,
#    que le corps diverge OU qu'il soit identique. Une copie reste une copie.
ctrl = dn_gates.ctrl
bilan = dn_gates.bilan

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PRODUIT = "installeur/dn_installeur.py"
BAT = "installeur/DeskNode-installeur.bat"
PAGE = "installeur/index.html"
FIXES = (PRODUIT, BAT, PAGE)

# ⚠️ LE PLAFOND D'UN APPEL A `main()` — ⛔ pas un confort : si un produit remanie
#    se mettait a SERVIR au lieu de rendre un code, `serve_forever()` tiendrait
#    ce fil pour toujours et la gate mourrait en DEPASSEMENT, sans bilan. ⇒ le
#    fil est borne, et le depassement est un KO **NOMME**.
DELAI_MAIN = 20

# 🔴 COMBIEN DE FILS N'ONT PAS RENDU LA MAIN. ⛔ Ce n'est pas un compteur de
#    confort : tant qu'il n'est pas NUL, le refus de `bind` reste INSTALLE, parce
#    qu'un fil demon qui survit avec le vrai `bind` rendu peut LIER UN VRAI PORT
#    — ce que l'invariant de cette gate interdit en toutes lettres.
_FILS_VIVANTS = [0]


class _Orphelin(Exception):
    """Un `main()` qui n'a pas rendu la main. ⛔ On ⛔ ne joue RIEN de plus :
    les scenarios suivants RENOMMENT des fichiers de la copie jetable, et les
    faire sous un fil vivant serait muter l'objet qu'on mesure."""


def _refus_de_bind(self, *a, **k):
    """⛔ LE `bind` EST EMPECHE **AU NIVEAU `socket`**, ⛔ pas par un NOM."""
    raise OSError(errno.EADDRNOTAVAIL, "bind refuse par la gate (au niveau socket)")

# ── LES SIX CODES, ET **QUI** LES REND ────────────────────────────────────
# 🔴 UNE TABLE, ⛔ PAS UNE PROSE : c'est elle qui est confrontee a l'en-tete du
#    `.bat`, et c'est elle qui dit de quel cote chaque code se prouve.
#    `python` = PROVOQUE en appelant `main()` · `bat` = LU en modelisant le flot
#    du point d'entree, parce que `cmd.exe` ⛔ n'existe pas sur la CI Linux.
CODES_PUBLIES = {
    "0": "python",   # charge complete, modules presents, pilote present
    "2": "bat",      # argument inconnu ⇒ `:USAGE`  (⛔ LU, ⛔ pas provoque)
    "3": "python",   # page absente · pilote introuvable  (+ `:SANSSCRIPT`)
    "4": "python",   # le serveur local n'a pas pu se lier
    "5": "python",   # la charge est absente ou abimee
    "6": "python",   # une dependance de l'agent manque — l'ecart declare
}
# Les etiquettes du `.bat` qui POSENT un code, et le code qu'elles doivent
# poser. ⛔ Une etiquette qui pose un AUTRE code est un defaut, ⛔ pas un choix.
ETIQUETTES_A_CODE = {
    "SANSPYTHON": "3",
    "SANSSCRIPT": "3",
    "SANSPAGE": "3",
    "SANSCHARGE": "5",
    "USAGE": "2",
}
# 🔴 LA TROISIEME LISTE DE NOMS DE FICHIERS — celle de CETTE gate. Les deux
#    autres sont le `:SANSCHARGE` du `.bat` et le `IMAGES` du serveur, et les
#    TROIS doivent coincider : un nom ajoute d'un seul cote est un fichier que
#    l'un des trois attend et que les deux autres ignorent.
NOMS_DE_CHARGE = ("manifest.json", "bootloader.bin", "partition-table.bin",
                  "desknode.bin", "living_pcb_v0.bin")

# 🔴 L'ETAT DE DEPART DES QUATRE BOUTONS DE CHOIX, ATTENDU **EN ANGLAIS** — et
#    c'est un fait de PRODUIT, ⛔ pas une preference : le defaut anglais de la
#    page tient PAR CE BALISAGE, exactement comme le defaut de la dalle tient
#    par l'ABSENCE d'ecriture en NVS. MESURE DU 2026-09-11 : ⛔ AUCUNE gate ne
#    relisait ces quatre attributs, et le banc epinglait `en=null fr=null` — un
#    etat de depart qui n'appartenait qu'a lui, sur la surface meme dont la
#    LISIBILITE fait le sujet d'`AC8.2.6`.
ARIA_ATTENDU = {"b-langue-en": "true", "b-langue-fr": "false",
                "b-dalle-en": "true", "b-dalle-fr": "false"}

RE_ETIQ = re.compile(r"^:(\w+)\s*$")
# ⚠️ `goto` **ET** `call` : un saut vers une etiquette NON DECLAREE tronquait
#    l'atteignabilite EN SILENCE (correctif de revue du 2026-09-12).
RE_SAUT = re.compile(r"\b(goto|call)\s+:?(\w+)", re.I)
RE_SET_RC = re.compile(r'set\s+"RC=(\d+)"', re.I)
RE_SET_RC_RELAIS = re.compile(r'^set\s+"RC=%ERRORLEVEL%"$', re.I)
RE_EXIT = re.compile(r"^exit\s+/b\b", re.I)
RE_EXIT_RC = re.compile(r"^exit\s+/b\s+%RC%$", re.I)
RE_APPEL_PY = re.compile(r"^%PY%\s")
RE_EXIST_CHARGE = re.compile(r'if not exist "%DN_CHARGE%\\([\w.\-]+)"', re.I)
RE_BLOC_CODES = re.compile(r"CODES DE RETOUR(.*?)(?:\n\s*REM\s*\n|\n\s*REM\s+!!!)",
                           re.S)
RE_CODE_PUBLIE = re.compile(r"(?:^|[.:]\s*)(\d)\s+[a-z]")
RE_IMAGES = re.compile(r"^IMAGES = \((.*?)\)", re.M | re.S)

TETE = "(tete du fichier)"

MUTANTS = {}                      # ⛔ AU NIVEAU MODULE — `--liste-mutants`
CIBLES = {}                       # le controle que chaque mutant doit ROUGIR

MUTANTS[1] = ("PRODUIT : `return 6 if manquantes else 0` devient "
              "`return 0` — LE PRECEDENT `dn7-1`, mot pour mot")
CIBLES[1] = ("c8",)
MUTANTS[2] = ("PRODUIT : la meme ligne rend TOUJOURS 6 ⇒ une machine "
              "SAINE se voit refuser le code du succes")
CIBLES[2] = ("c1",)
MUTANTS[3] = ("PRODUIT : `6` passe AVANT `5` ⇒ une charge absente est "
              "publiee comme un simple ecart de dependance")
CIBLES[3] = ("c7",)
MUTANTS[4] = ("PRODUIT : retire le `return 5` ⇒ une charge amputee ne "
              "se distingue plus d'une machine saine")
CIBLES[4] = ("c6", "c7")
MUTANTS[5] = ("PRODUIT : `3` ne couvre plus l'OUTIL ⇒ sans pilote, le "
              "pre-vol annonce « tout est la » sur deux gestes MORTS")
CIBLES[5] = ("c3",)
MUTANTS[6] = ("PRODUIT : `3` ne couvre plus la PAGE ⇒ un dossier "
              "incomplet passe pour complet")
CIBLES[6] = ("c2",)
MUTANTS[7] = ("PRODUIT : le `bind` refuse rend `0` ⇒ un serveur qui n'a "
              "jamais demarre est annonce comme demarre")
CIBLES[7] = ("c5",)
MUTANTS[8] = ("PRODUIT : le `bind` refuse sort en TRACE NUE ⇒ exactement "
              "ce qu'`AC7.1.6` interdit dans une fenetre double-cliquee")
CIBLES[8] = ("c4",)
MUTANTS[9] = ("BAT : `:SANSPAGE` pose `RC=0` ⇒ une etiquette d'erreur "
              "qui publie un SUCCES")
CIBLES[9] = ("c10",)
MUTANTS[10] = ("BAT : retire le `goto :USAGE` ⇒ le `2` devient "
               "INATTEIGNABLE, et personne ne le voit")
CIBLES[10] = ("c9",)
MUTANTS[11] = ("BAT : retire un nom de fichier de `:SANSCHARGE` ⇒ la "
               "charge peut etre amputee sans que le point d'entree bronche")
CIBLES[11] = ("c12",)
MUTANTS[12] = ("PRODUIT : retire un nom d'`IMAGES` ⇒ le serveur et le "
               "point d'entree ne parlent plus de la meme charge")
CIBLES[12] = ("c12",)
MUTANTS[13] = ("PAGE : casse la balise `<script>` ⇒ la page que le `3` "
               "garde n'est plus un document que quiconque peut jouer")
CIBLES[13] = ("c13",)
MUTANTS[14] = ("BAT : l'en-tete ne publie plus que CINQ codes ⇒ un code "
               "REEL que personne n'annonce")
CIBLES[14] = ("c11",)
MUTANTS[15] = ("deplace la cible du mutant 13 — SEUL sur `(c13)` ⇒ un "
               "controle garde par ZERO mutant, le risque deja paye ailleurs")
CIBLES[15] = ("c14",)
MUTANTS[16] = ("declare dans `CIBLES` un controle INEXISTANT ⇒ une "
               "cible PERIMEE, que « N mutants, N rouges » ne voit pas")
CIBLES[16] = ("c15",)
MUTANTS[17] = ("declare une cible pour un mutant qui N'EXISTE PAS")
CIBLES[17] = ("c16",)
MUTANTS[18] = ("declare un mutant dont le CORPS LEVE ⇒ un mutant MORT, "
               "qui sortirait en Traceback SANS `BILAN`")
CIBLES[18] = ("c0",)
MUTANTS[19] = ("replante une SORTIE ANTICIPEE NON DECLAREE : le bilan "
               "retrecit, et il sortirait VERT")
CIBLES[19] = ("z",)
# ── LES CINQ MUTANTS DE LA BOUCLE DE REVUE 1 (2026-09-12) ────────────────
# 🔴 LES QUATRE PREMIERS ONT ETE **VUS VERTS** SUR LA 1re REDACTION DE CETTE
#    GATE : ⛔ pas des inquietudes, des mesures.
MUTANTS[20] = ("PRODUIT : `main()` rend `0` sur `--verifier` ⇒ les codes "
               "que `prevol()` calcule ne sortent JAMAIS du point d'entree")
CIBLES[20] = ("c2", "c3", "c6", "c7", "c8")
MUTANTS[21] = ("BAT : `:FIN` sort par `exit /b 0` ⇒ le relais final est "
               "EFFACE, et tout code devient un succes")
CIBLES[21] = ("c19",)
MUTANTS[22] = ("BAT : le relais `set \"RC=%ERRORLEVEL%\"` du pre-vol "
               "devient `set \"RC=0\"` ⇒ le code du Python est jete")
# ⚠️ DEUX CIBLES, MESUREES : remplacer le relais par `set "RC=0"` fait de
#    `:VERIFIER` une etiquette qui POSE un code — et elle n'est pas dans la
#    table. `(c17)` rougit donc AUSSI, et c'est juste.
CIBLES[22] = ("c17", "c18")
MUTANTS[23] = ("BAT : une etiquette HORS TABLE pose `RC=7` ⇒ un code que "
               "l'en-tete ⛔ ne publie pas, et que personne ne rend")
CIBLES[23] = ("c17",)
MUTANTS[24] = ("PAGE : le choix de langue part en FRANCAIS ⇒ le defaut "
               "anglais du balisage est retourne EN SILENCE")
CIBLES[24] = ("c20",)

# ⚠️ LE COMPTE DU CHEMIN NORMAL : 1 pre-vol + un controle par mutant + les 20
#    controles numerotes. Il se PERIME si on ajoute un controle sans le mettre
#    a jour — et c'est voulu : c'est ce qui rend `(z)` FALSIFIABLE.
CONTROLES_PREVUS = 1 + len(MUTANTS) + 20

_MUTANT = 0


# ══════════════════ LE `.bat`, LU COMME UN **FLOT** ════════════════════════

def flot_du_bat(texte):
    """Le point d'entree lu comme un FLOT : etiquettes, sauts, chute, sorties.

    🔴 ⛔ PAS UN BALAYAGE, ET C'EST LE CORRECTIF DE LA BOUCLE DE REVUE 1. La 1re
       redaction tenait une etiquette pour « atteignable » des qu'un `goto` la
       CITAIT quelque part — donc une etiquette citee depuis un bloc lui-meme
       inatteignable passait, et une etiquette POSANT UN CODE hors table passait
       aussi. ⇒ on modelise : chaque ligne executable a ses SUCCESSEURS (saut
       inconditionnel, saut conditionnel **plus** la chute, `exit /b` qui
       termine), et « atteignable » veut dire ATTEINT DEPUIS LA TETE DU FICHIER.
    ⚠️ LES LIGNES `REM` SONT ECARTEES, ET C'EST LOAD-BEARING : ce fichier CITE
       ses propres etiquettes et ses propres codes dans sa documentation. Un
       motif nu compterait la prose qui explique la regle — le defaut que ce
       depot a deja paye trois fois."""
    brut = (texte or "").replace("\r\n", "\n").split("\n")
    lignes = []
    for i, l in enumerate(brut):
        nu = l.strip()
        if not nu or nu.upper().startswith("REM") or nu.startswith("::"):
            continue
        lignes.append((i + 1, nu))
    etiquettes = {}
    for k, (_i, nu) in enumerate(lignes):
        m = RE_ETIQ.match(nu)
        if m:
            etiquettes[m.group(1).upper()] = k
    codes, noms, sauts, succ = {}, [], {}, {}
    inconnues = []
    appels_py = []
    courante = TETE
    for k, (_i, nu) in enumerate(lignes):
        m = RE_ETIQ.match(nu)
        if m:
            courante = m.group(1).upper()
            succ[k] = [k + 1]
            continue
        for g in RE_EXIST_CHARGE.finditer(nu):
            noms.append(g.group(1))
        m = RE_SET_RC.search(nu)
        if m:
            codes.setdefault(courante, set()).add(m.group(1))
        if RE_APPEL_PY.match(nu):
            appels_py.append(k)
        g = RE_SAUT.search(nu)
        if g:
            verbe, cible = g.group(1).lower(), g.group(2).upper()
            # ⛔ UNE CIBLE QUI N'EXISTE PAS EST UN SAUT QUI NE SE RESOUT PAS : il
            #    tronque l'atteignabilite, et le taire rendrait « atteignable »
            #    une propriete mesuree sur un flot INCOMPLET.
            if cible not in etiquettes and cible != "EOF":
                inconnues.append("l.%d ⇒ :%s" % (lignes[k][0], cible))
            sauts.setdefault(cible, []).append(k)
            suivants = [etiquettes[cible]] if cible in etiquettes else []
            # ⚠️ UN SAUT **CONDITIONNEL** LAISSE AUSSI LA CHUTE : `if … goto :X`
            #    et `… || goto :X` continuent sur la ligne suivante quand la
            #    condition est fausse. Les confondre avec un `goto` nu ferait
            #    declarer INATTEIGNABLE la moitie du fichier.
            # ⚠️ `call` REVIENT TOUJOURS a la ligne suivante ; un `goto` NU, ⛔ non.
            if verbe == "call" or not nu.lower().startswith("goto "):
                suivants.append(k + 1)
            succ[k] = suivants
            continue
        if RE_EXIT.match(nu):
            succ[k] = []
            continue
        succ[k] = [k + 1]
    vus, pile = set(), ([0] if lignes else [])
    while pile:
        k = pile.pop()
        if k in vus or k < 0 or k >= len(lignes):
            continue
        vus.add(k)
        pile.extend(succ.get(k, []))
    return {"lignes": lignes, "etiquettes": etiquettes, "codes": codes,
            "noms": noms, "sauts": sauts, "succ": succ, "atteignables": vus,
            "appels_py": appels_py, "inconnues": inconnues}


def sorties_depuis(flot, etiquette):
    """Les lignes `exit /b` atteignables DEPUIS une etiquette — ⛔ pas toutes.

    ⛔ C'est ce qui distingue « le point d'entree sort par `exit /b %RC%` » de
       « le fichier porte quelque part un `exit /b %RC%` »."""
    deb = flot["etiquettes"].get(etiquette)
    if deb is None:
        return None
    vus, pile, sorties = set(), [deb], []
    while pile:
        k = pile.pop()
        if k in vus or k < 0 or k >= len(flot["lignes"]):
            continue
        vus.add(k)
        nu = flot["lignes"][k][1]
        if RE_EXIT.match(nu):
            sorties.append((flot["lignes"][k][0], nu))
        pile.extend(flot["succ"].get(k, []))
    return sorties


def codes_de_l_entete(texte):
    """Les codes que l'en-tete du `.bat` PUBLIE — ⛔ pas ceux qu'il pose."""
    m = RE_BLOC_CODES.search((texte or "").replace("\r\n", "\n"))
    if not m:
        return None
    bloc = re.sub(r"(?m)^\s*REM\s?", " ", m.group(1))
    bloc = re.sub(r"\s+", " ", bloc)
    return set(RE_CODE_PUBLIE.findall(bloc))


def images_du_serveur(source):
    """Le tuple `IMAGES` du produit, LU A L'AST — ⛔ pas au motif."""
    try:
        arbre = ast.parse(source or "")
    except SyntaxError:
        return None
    for n in ast.walk(arbre):
        if isinstance(n, ast.Assign):
            for c in n.targets:
                if isinstance(c, ast.Name) and c.id == "IMAGES":
                    try:
                        v = ast.literal_eval(n.value)
                    except (ValueError, SyntaxError):
                        return None
                    return tuple(v)
    return None


# ══════════════════ LA PAGE, LUE PAR UN **PARSEUR** ════════════════════════

class LecteurDePage(HTMLParser):
    """⛔ PAS UN `grep` SUR DU HTML (`NFR14`). Deux choses se lisent ici, et les
    deux sont des proprietes de STRUCTURE : la page que le code `3` garde est-elle
    un document qui porte son script, et dans quel etat le balisage POSE les
    quatre boutons de choix."""

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.balises = 0
        self.scripts_en_ligne = 0
        self.scripts_externes = 0
        self.a_html = False
        self.aria = {}

    def handle_starttag(self, tag, attrs):
        self.balises += 1
        d = dict(attrs)
        if tag == "html":
            self.a_html = True
        if tag == "script":
            if d.get("src"):
                self.scripts_externes += 1
            else:
                self.scripts_en_ligne += 1
        # 🔴 L'ETAT DE DEPART DES QUATRE BOUTONS DE CHOIX — releve SUR LA BALISE,
        #    ⛔ pas cherche au motif : un `aria-pressed` cite dans le `<script>`
        #    voisin ou dans une prose ne dit RIEN de ce que le document POSE.
        if tag == "button" and d.get("id") in ARIA_ATTENDU:
            self.aria[d["id"]] = d.get("aria-pressed")


def la_page_est_un_document(texte):
    """(ok, detail, aria) — la page se PARSE, porte `<html>` et UN script."""
    lp = LecteurDePage()
    try:
        lp.feed(texte or "")
        lp.close()
    except Exception as exc:                              # noqa: BLE001
        return False, "⛔ LE PARSEUR REFUSE LA PAGE : %s: %s" % (
            type(exc).__name__, str(exc)[:70]), {}
    if not lp.a_html:
        return False, "⛔ AUCUNE balise `<html>` : ce n'est pas un document", lp.aria
    if lp.scripts_en_ligne != 1:
        return False, ("⛔ %d `<script>` EN LIGNE (1 attendu) — le banc "
                       "`tools/banc_langue_dalle_dn73.mjs` EXTRAIT celui-la, et "
                       "il echoue ferme sur une fenetre douteuse"
                       % lp.scripts_en_ligne), lp.aria
    return True, ("%d balises · 1 `<script>` en ligne · %d externe(s)"
                  % (lp.balises, lp.scripts_externes)), lp.aria


# ══════════════════ LE PRODUIT, **APPELE** DANS UNE COPIE ══════════════════

def charger_produit(chemin):
    """Le produit COMPILE depuis la COPIE — ⛔ jamais importe du disque reel.

    ⚠️ `__file__` pointe la COPIE : c'est lui qui fixe `ICI`, donc `PAGE` et
       `CHARGE`. Retirer un fichier de la copie change donc ce que le pre-vol
       VOIT, sans qu'⛔ une seule ligne de l'arbre ne bouge."""
    with io.open(chemin, encoding="utf-8") as fh:
        source = fh.read()
    mod = importlib.util.module_from_spec(
        importlib.util.spec_from_loader("dn_installeur_entree", loader=None))
    mod.__file__ = chemin
    exec(compile(source, chemin, "exec"), mod.__dict__)    # noqa: S102
    return mod


def _appeler_main(m, argv):
    """Appelle **`main()`** du produit avec `argv`, dans un fil BORNE.

    🔴 PAR `main()`, ⛔ PAS PAR `prevol()` APPELE A COTE — et c'est LE correctif
       de la boucle de revue 1 : `if a.verifier: return 0` laissait la gate
       VERTE, parce que `prevol()` continuait de rendre ses codes a qui les lui
       demandait. Ce que le point d'entree REND est une propriete de `main()`.
    ⚠️ LE FIL EST BORNE : un produit remanie qui SERVIRAIT au lieu de rendre un
       code tiendrait ce fil pour toujours. Le depassement devient un KO NOMME,
       ⛔ pas une gate morte sans bilan.
    ⚠️ `sys.argv` ET `sys.stdout` SONT RENDUS DANS UN `finally` : une gate qui
       garderait la sortie detournee n'imprimerait plus son propre bilan."""
    garde_argv = list(sys.argv)
    garde_stdout = sys.stdout
    tampon = io.StringIO()
    out = {}
    # ⛔ INITIALISE **AVANT** LE `try` : si `Thread()` ou `start()` levait, le
    #    `finally` passait et `if vivant:` levait un `UnboundLocalError` — masque
    #    ensuite en « le produit n'a pas pu etre joue ». Un fil qu'on n'a pas pu
    #    lancer est traite comme un fil QUI VIT : c'est le sens conservateur.
    vivant = True

    def cible():
        try:
            out["rc"] = m.main()
        except BaseException as exc:                      # noqa: BLE001
            out["exc"] = "%s: %s" % (type(exc).__name__, str(exc)[:90])

    sys.argv = ["dn_installeur.py"] + list(argv)
    sys.stdout = tampon
    try:
        fil = threading.Thread(target=cible, daemon=True)
        fil.start()
        fil.join(DELAI_MAIN)
        vivant = fil.is_alive()
    finally:
        sys.stdout = garde_stdout
        sys.argv = garde_argv
    if vivant:
        _FILS_VIVANTS[0] += 1
        return None, tampon.getvalue(), ("⛔ `main()` ⛔ N'A PAS RENDU LA MAIN "
                                         "en %d s — le fil DEMON vit encore"
                                         % DELAI_MAIN)
    if "exc" in out:
        return None, tampon.getvalue(), out["exc"]
    return out.get("rc"), tampon.getvalue(), None


def provoquer_les_codes(copie):
    """Provoque les CINQ codes qu'un Python rend, et relit CHACUN par son nom.

    🔴 ⛔ AUCUN GESTE REEL : `_powershell`, `lhm_present`, `dependance_presente`
       et `_jouer_dependances` sont remplaces — le dernier parce qu'il lance un
       `pip install` POUR DE VRAI, l'avant-dernier parce qu'il lance DEUX
       interpreteurs par appel. ⛔ AUCUN port n'est lie : le `4` se provoque en
       EMPECHANT le `bind` **au niveau `socket`**, ⛔ pas en substituant le nom
       `ThreadingHTTPServer` — un produit qui lierait son port autrement doit
       rendre `4` quand meme."""
    out = {}
    try:
        m = charger_produit(os.path.join(copie, "dn_installeur.py"))
    except Exception as exc:                              # noqa: BLE001
        return {"__erreur__": "%s: %s" % (type(exc).__name__, str(exc)[:90])}
    m._powershell = lambda arguments, timeout=90: (
        0, "sortie de papier", ["powershell"] + list(arguments), None)
    m.lhm_present = lambda: None
    m.arbre_parent_present = lambda: True
    m.dependance_presente = lambda module, sans_site_utilisateur=False: True
    m._jouer_dependances = lambda: {"commande": "", "sortie": "", "rc": 0,
                                    "rc_pose_par": "l'outil",
                                    "verdict": "double de papier"}
    faux_pilote = os.path.join(copie, "outil-de-papier")
    m.localiser_pilote = lambda: (faux_pilote, "double de papier")
    tout_est_la = lambda mod, sans=False: True            # noqa: E731
    sans_psutil = lambda mod, sans=False: mod != "psutil"  # noqa: E731
    page = os.path.join(copie, "index.html")
    asset = os.path.join(copie, "charge", "living_pcb_v0.bin")

    def jouer(cle, argv):
        rc, texte, motif = _appeler_main(m, argv)
        out[cle] = rc
        out[cle + "__texte"] = texte
        if motif:
            out.setdefault("__ecarts__", []).append("%s : %s" % (cle, motif))
        # 🔴 UN FIL QUI N'A PAS RENDU LA MAIN **ARRETE TOUT** : les scenarios
        #    suivants renomment des fichiers de la copie, et les jouer sous un
        #    fil vivant reviendrait a muter ce qu'on mesure.
        if _FILS_VIVANTS[0]:
            raise _Orphelin(motif or "un fil n'a pas rendu la main")

    # 🔴 LE REFUS DE `bind` EST INSTALLE POUR **TOUTE** CETTE FONCTION, ⛔ plus
    #    seulement autour du scenario du `4` : sur un depassement, le fil demon
    #    SURVIT, et s'il survivait avec le vrai `bind` rendu il pourrait LIER UN
    #    VRAI PORT. ⇒ il n'est RENDU que si ⛔ AUCUN fil n'a survecu.
    vraie_bind = socket.socket.bind
    socket.socket.bind = _refus_de_bind
    try:
        # (1) `0` — tout est la.
        m.dependance_presente = tout_est_la
        jouer("tout_est_la", ["--verifier"])
        # (2) `6` — une dependance de l'agent manque.
        m.dependance_presente = sans_psutil
        jouer("module_manquant", ["--verifier"])
        # (3) `5` — la charge est amputee, POUR DE VRAI.
        m.dependance_presente = tout_est_la
        os.rename(asset, asset + ".ote")
        jouer("charge_absente", ["--verifier"])
        # (4) `5` AVANT `6` — les deux causes a la fois.
        m.dependance_presente = sans_psutil
        jouer("charge_absente_et_module", ["--verifier"])
        os.rename(asset + ".ote", asset)
        # (5) `3` — la page est REELLEMENT retiree.
        m.dependance_presente = tout_est_la
        os.rename(page, page + ".ote")
        jouer("page_absente", ["--verifier"])
        os.rename(page + ".ote", page)
        # (6) `3` — le pilote est introuvable.
        m.localiser_pilote = lambda: (None, "introuvable")
        jouer("pilote_absent", ["--verifier"])
        m.localiser_pilote = lambda: (faux_pilote, "double de papier")
        # (7) `4` — le `bind` est EMPECHE (deja installe plus haut), ⛔ pas tente.
        #     ⚠️ Et `--sans-navigateur`, ⛔ pas `--verifier` : sous `--verifier`,
        #        `main()` REND AVANT le `bind`, donc il ⛔ ne peut pas donner 4.
        jouer("bind_refuse", ["--sans-navigateur"])
    except _Orphelin as exc:
        out["__orphelin__"] = str(exc)
    except Exception as exc:                              # noqa: BLE001
        out["__erreur__"] = "%s: %s" % (type(exc).__name__, str(exc)[:90])
    finally:
        if _FILS_VIVANTS[0] == 0:
            socket.socket.bind = vraie_bind
        else:
            # ⛔ ON NE REND PAS LE VRAI `bind` A UN FIL QUI VIT ENCORE.
            out.setdefault("__ecarts__", []).append(
                "⛔ %d FIL(S) ORPHELIN(S) : le refus de `bind` reste INSTALLE — "
                "c'est la SEULE chose qui tienne encore l'invariant « ⛔ aucun "
                "port n'est lie »" % _FILS_VIVANTS[0])
    return out


def preparer_la_copie(fichiers):
    """Une COPIE JETABLE de `installeur/`, portant les textes (mutes) donnes.

    🔴 ⛔ AUCUNE ECRITURE DANS L'ARBRE, JAMAIS — pas meme pour un mutant."""
    tmp = tempfile.mkdtemp(prefix="dn82-entree-")
    try:
        shutil.copytree(os.path.join(RACINE, "installeur"),
                        os.path.join(tmp, "installeur"))
        for rel, texte in fichiers.items():
            with io.open(os.path.join(tmp, rel), "w", encoding="utf-8",
                         newline="") as fh:
                fh.write(texte)
    except (OSError, UnicodeError) as exc:
        shutil.rmtree(tmp, ignore_errors=True)
        return None, "⛔ COPIE JETABLE IMPOSSIBLE : %s: %s" % (
            type(exc).__name__, exc)
    return tmp, None


# ══════════════════════════ LE MUTANT ══════════════════════════════════════

def muter(etat):
    """REPLANTE une faute DANS L'ETAT — ⛔ jamais dans un fichier du depot.

    ⛔ CHAQUE MUTANT **REPLANTE LA FAUTE**, ⛔ il ne debranche aucune garde : un
       mutant qui coupe le controle ne prouve que l'existence du controle.
    ⚠️ Tout corps VERIFIE son ancre et rend `e` INCHANGE si elle a disparu : le
       corps principal compare l'etat AVANT/APRES, et un mutant sans effet rend
       **`rc=3`**, ⛔ jamais un vert. Le mutant 18 leve EXPRES."""
    import copy as _copy
    e = _copy.deepcopy(etat)
    p, r, c = e["fichiers"], e["regles"], e["cibles"]

    if _MUTANT == 1:
        a = "    return 6 if manquantes else 0\n"
        if a not in p.get(PRODUIT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PRODUIT] = p[PRODUIT].replace(a, "    return 0\n", 1)
    elif _MUTANT == 2:
        a = "    return 6 if manquantes else 0\n"
        if a not in p.get(PRODUIT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PRODUIT] = p[PRODUIT].replace(a, "    return 6\n", 1)
    elif _MUTANT == 3:
        a = ('    if not ch["complete"]:\n'
             '        return 5\n'
             '    return 6 if manquantes else 0\n')
        if a not in p.get(PRODUIT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PRODUIT] = p[PRODUIT].replace(
            a, '    if manquantes:\n'
               '        return 6\n'
               '    return 5 if not ch["complete"] else 0\n', 1)
    elif _MUTANT == 4:
        a = ('    if not ch["complete"]:\n'
             '        return 5\n')
        if a not in p.get(PRODUIT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PRODUIT] = p[PRODUIT].replace(a, "", 1)
    elif _MUTANT == 5:
        a = "    if manque_page or not pilote:\n"
        if a not in p.get(PRODUIT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PRODUIT] = p[PRODUIT].replace(a, "    if manque_page:\n", 1)
    elif _MUTANT == 6:
        a = "    if manque_page or not pilote:\n"
        if a not in p.get(PRODUIT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PRODUIT] = p[PRODUIT].replace(a, "    if not pilote:\n", 1)
    elif _MUTANT == 7:
        a = ('        print("      Rien n\'a ete installe, rien n\'a ete change.")\n'
             "        return 4\n")
        if a not in p.get(PRODUIT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PRODUIT] = p[PRODUIT].replace(
            a, '        print("      Rien n\'a ete installe, rien n\'a ete '
               'change.")\n        return 0\n', 1)
    elif _MUTANT == 8:
        a = ('        print("")\n'
             '        print("  /!\\\\ LE SERVEUR LOCAL N\'A PAS PU DEMARRER.")\n')
        if a not in p.get(PRODUIT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PRODUIT] = p[PRODUIT].replace(a, "", 1)
    elif _MUTANT == 9:
        a = ':SANSPAGE\r\necho.\r\n'
        if a not in p.get(BAT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        i = p[BAT].index(a)
        # ⛔ L'ANCRE SECONDE EST GARDEE AUSSI : sans ce test, un `.index` qui ne
        #    trouve rien LEVE, et le mutant sortait en `rc=1` — un FAUX DEFAUT —
        #    la ou un mutant dont l'ancre a disparu doit rendre `rc=3` (PERIME).
        if 'set "RC=3"' not in p[BAT][i:]:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        j = p[BAT].index('set "RC=3"', i)
        p[BAT] = p[BAT][:j] + 'set "RC=0"' + p[BAT][j + len('set "RC=3"'):]
    elif _MUTANT == 10:
        a = 'if defined VERBE goto :USAGE\r\n'
        if a not in p.get(BAT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BAT] = p[BAT].replace(a, "", 1)
    elif _MUTANT == 11:
        a = 'if not exist "%DN_CHARGE%\\living_pcb_v0.bin" goto :SANSCHARGE\r\n'
        if a not in p.get(BAT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BAT] = p[BAT].replace(a, "", 1)
    elif _MUTANT == 12:
        a = '"living_pcb_v0.bin"'
        if a not in p.get(PRODUIT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        m = RE_IMAGES.search(p[PRODUIT])
        if not m or a not in m.group(0):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        # ⚠️ LE NOM EST RETIRE **AVEC SA VIRGULE ET SON BLANC**, ⛔ pas par une
        #    concatenation devinee : le tuple est ecrit sur DEUX lignes, et un
        #    `a + ","` naif ⛔ n'y correspond a rien — le mutant sortait alors
        #    PERIME (`rc=3`), c'est-a-dire en gardien MORT.
        bloc = m.group(0)
        neuf_bloc = re.sub(r',\s*"living_pcb_v0\.bin"', "", bloc)
        if neuf_bloc == bloc:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PRODUIT] = p[PRODUIT].replace(bloc, neuf_bloc, 1)
    elif _MUTANT == 13:
        a = "<script>\n"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "<scrpit>\n", 1)
    elif _MUTANT == 14:
        a = ". 4 le serveur local"
        if a not in p.get(BAT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BAT] = p[BAT].replace(a, ". le serveur local", 1)
    elif _MUTANT == 15:
        # ⛔ LA CIBLE EST **DEPLACEE**, ⛔ pas supprimee : supprimer l'entiere
        #    ferait AUSSI rougir `(c16)`, et un mutant qui rougit deux controles
        #    ne dit plus lequel il garde.
        # 🔴 ET ELLE EST CELLE D'UN MUTANT **SEUL SUR SON CONTROLE** — MESURE DU
        #    2026-09-12, ⛔ pas une precaution. Vise sur le mutant 1, ce corps
        #    ⛔ ne prouvait PLUS RIEN : depuis que le mutant 20 vise AUSSI
        #    `(c8)`, le controle restait garde, `(c14)` restait VERT, et ce
        #    mutant sortait **rc=0** — un gardien MORT. C'est mot pour mot le
        #    piege que ce depot a deja nomme : « N mutants, N vus rougir »
        #    prouve `mutant ⇒ rouge`, ⛔ JAMAIS `controle ⇒ couvert`.
        if c.get(13) != ("c13",):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        c[13] = ("c2",)
    elif _MUTANT == 16:
        if c.get(1) != ("c8",):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        c[1] = ("c8", "c99")
    elif _MUTANT == 17:
        c[999] = ("c1",)
    elif _MUTANT == 18:
        raise AssertionError("mutant 18 : le CORPS LEVE, et c'est son objet")
    elif _MUTANT == 19:
        r["sortie_anticipee"] = True
    elif _MUTANT == 20:
        # 🔴 LE PRECEDENT `dn7-1` REJOUE **UN CRAN PLUS LOIN** : `prevol()` rend
        #    toujours ses codes, et le point d'entree n'en relaie plus AUCUN.
        a = "    if a.verifier:\n        return rc\n"
        if a not in p.get(PRODUIT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PRODUIT] = p[PRODUIT].replace(
            a, "    if a.verifier:\n        return 0\n", 1)
    elif _MUTANT == 21:
        a = "exit /b %RC%"
        if a not in p.get(BAT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BAT] = p[BAT].replace(a, "exit /b 0", 1)
    elif _MUTANT == 22:
        a = '%PY% "%DN_PY_SCRIPT%" --verifier\r\nset "RC=%ERRORLEVEL%"\r\n'
        if a not in p.get(BAT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BAT] = p[BAT].replace(
            a, '%PY% "%DN_PY_SCRIPT%" --verifier\r\nset "RC=0"\r\n', 1)
    elif _MUTANT == 23:
        # ⚠️ L'ETIQUETTE EST POSEE **SANS AUCUN `goto` VERS ELLE** : c'est le cas
        #    sournois — `(c9)` ne juge que les etiquettes de la table, et une
        #    etiquette inatteignable qui pose un code hors table passerait donc
        #    sans que RIEN ne bouge.
        a = "\r\n:FIN\r\n"
        if a not in p.get(BAT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BAT] = p[BAT].replace(
            a, "\r\n:AUTRECODE\r\necho.\r\nset \"RC=7\"\r\ngoto :FIN\r\n"
               "\r\n:FIN\r\n", 1)
    elif _MUTANT == 24:
        a = '<button id="b-langue-en" type="button" lang="en" aria-pressed="true">'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '<button id="b-langue-en" type="button" lang="en" '
               'aria-pressed="false">', 1)
    else:
        raise AssertionError("mutant %d declare mais SANS CORPS" % _MUTANT)
    return e


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
    print("dn8-2 — CINQ DES SIX CODES SONT PROVOQUES, LE `2` EST LU"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)
    print("cibles     : %s" % " · ".join(FIXES))
    print("⛔ AUCUN GESTE REEL : ⛔ aucun `powershell`, ⛔ aucun `pip`, ⛔ aucun")
    print("   port lie, ⛔ aucune connexion. Tout se joue dans une COPIE")
    print("   JETABLE, et le `4` se provoque en EMPECHANT le `bind` au niveau")
    print("   `socket` — ⛔ pas en substituant un NOM de serveur.")
    print("🔴 LES CODES SONT PROVOQUES PAR `main()` DU PRODUIT, ⛔ PAS PAR")
    print("   `prevol()` APPELE A COTE : sur la 1re redaction de cette gate, un")
    print("   `if a.verifier: return 0` laissait 36 OK / 0 KO.")
    print("⚠️ `main()` NE PREND AUCUN PARAMETRE : `sys.argv` est POSE —")
    print("   `--verifier` pour 0, 3, 5 et 6, et `--sans-navigateur` pour le 4,")
    print("   que `--verifier` ⛔ ne peut PAS donner (il rend AVANT le `bind`).")
    print("⛔ ET LE TIR `cmd.exe` RESTE HORS DE PORTEE : la CI de ce depot")
    print("   tourne sur Linux. Du `.bat`, cette gate MODELISE LE FLOT —")
    print("   etiquette atteignable depuis la tete, code pose, relais du")
    print("   `%ERRORLEVEL%`, sortie par `exit /b %RC%` — ⛔ elle ne prouve PAS")
    print("   que `cmd.exe` les rende. Ce tir-la est NON JOUE, et son porteur")
    print("   est AU LEDGER (`epic-dn8`), ⛔ pas une autre marche.")

    # ── (c0) LE PRE-VOL ─────────────────────────────────────────────────
    print("\n── (c0) LE PRE-VOL — ⛔ AUCUN CONTROLE SUR DU VIDE ────────────────")
    fichiers, illisibles = {}, []
    for rel in FIXES:
        try:
            texte, _emp = dn_gates.lire(os.path.join(RACINE, rel))
            fichiers[rel] = texte
        except (OSError, UnicodeDecodeError):
            illisibles.append(rel)
    if not ctrl(not illisibles, "(c0) tout fichier attendu est LISIBLE",
                "%d fichier(s) lus" % len(fichiers) if not illisibles
                else "⛔ ILLISIBLE(S) : %s" % " ".join(illisibles)):
        return bilan(1, "un fichier attendu est illisible",
                     prevus=CONTROLES_PREVUS)

    for n in sorted(MUTANTS):
        if not ctrl(bool(CIBLES.get(n)) and bool(MUTANTS.get(n)),
                    "(c0) le mutant %d a une CIBLE et un LIBELLE" % n,
                    "→ %s" % ",".join(CIBLES.get(n, ()))
                    if CIBLES.get(n) else "⛔ cible ou libelle manquant"):
            return bilan(1, "un mutant est declare a moitie",
                         prevus=CONTROLES_PREVUS)

    etat = {"fichiers": fichiers, "regles": {"sortie_anticipee": False},
            "cibles": dict(CIBLES)}
    try:
        neuf = muter(etat) if _MUTANT else etat
    except Exception as exc:                              # noqa: BLE001
        ctrl(False, "(c0) le mutant %d a une CIBLE et un CORPS" % _MUTANT,
             "⛔ %s: %s — la faute est dans le MUTANT, ⛔ pas dans la gate"
             % (type(exc).__name__, str(exc)[:80]))
        return bilan(1, "le mutant %d n'a pas pu s'appliquer" % _MUTANT,
                     prevus=CONTROLES_PREVUS)
    if _MUTANT and neuf == etat:
        ctrl(False, "(c0) le mutant %d a bien un EFFET" % _MUTANT,
             "⛔ SANS EFFET — son ancre litterale a disparu de la cible. "
             "⛔ Ce n'est PAS un controle vert : rc=3, mutant PERIME.")
        return bilan(3, "le mutant %d n'a eu aucun effet" % _MUTANT,
                     prevus=CONTROLES_PREVUS)

    copie, motif = preparer_la_copie(neuf["fichiers"])
    if copie is None:
        ctrl(False, "(c1) le code 0 est PROVOQUE, et il vaut 0", motif)
        return bilan(1, "la copie jetable n'a pas pu etre preparee",
                     prevus=CONTROLES_PREVUS)
    try:
        return corps(neuf, copie)
    finally:
        shutil.rmtree(copie, ignore_errors=True)


def corps(neuf, copie):
    """Le tir, une fois la copie jetable prete — ⛔ elle est detruite APRES."""
    regles, cibles = neuf["regles"], neuf["cibles"]
    codes = provoquer_les_codes(os.path.join(copie, "installeur"))
    flot = flot_du_bat(neuf["fichiers"].get(BAT, ""))

    # ── (c1)…(c8) LES CODES QUE LE **PYTHON** REND ──────────────────────
    print("\n── (c1)…(c8) LES CODES RENDUS PAR `main()`, CHACUN NOMME ─────────")
    if "__erreur__" in codes:
        ctrl(False, "(c1) le code 0 est PROVOQUE, et il vaut 0",
             "⛔ LE PRODUIT N'A PAS PU ETRE JOUE : %s" % codes["__erreur__"])
        return bilan(1, "le produit n'a pas pu etre joue",
                     prevus=CONTROLES_PREVUS)
    for ecart in codes.get("__ecarts__", []):
        print("  ⚠️ %s" % ecart)

    # ⛔ LE LIBELLE EST **LITTERAL AU SITE D'APPEL**, ⛔ jamais assemble par un
    #    aide : `dn_gates.ids_par_ast` lit les identifiants A L'AST, et un
    #    libelle construit par formatage sort de sa population EN SILENCE — la
    #    reciproque passerait alors VERTE sur un controle garde par personne.
    #    ⇒ seul le DETAIL est fabrique.
    orphelin = codes.get("__orphelin__")

    def detail(cle, attendu, pourquoi):
        vu = codes.get(cle)
        if vu == attendu:
            return True, "`%s` ⇒ %s" % (cle, attendu)
        # 🔴 UN DEPASSEMENT EST UN KO **CONTRE L'INVARIANT**, ⛔ pas un code
        #    manquant : il dit qu'un fil demon vit encore, et que « ⛔ aucun port
        #    n'est lie » ne tient plus que par le refus reste INSTALLE.
        if orphelin:
            return False, ("⛔ `%s` : %s — ⛔ UN FIL ORPHELIN VIT ENCORE, et "
                           "l'invariant « ⛔ AUCUN PORT N'EST LIE » ne tient que "
                           "parce que le refus de `bind` reste INSTALLE ; ⛔ les "
                           "scenarios suivants ⛔ n'ont PAS ete joues"
                           % (cle, orphelin))
        return False, ("⛔ `%s` rend %r au lieu de %s — %s"
                       % (cle, vu, attendu, pourquoi))

    ok, det = detail("tout_est_la", 0,
                     "une machine SAINE doit pouvoir obtenir le code du succes")
    ctrl(ok, "(c1) le code 0 est PROVOQUE, et il vaut 0", det)
    ok, det = detail("page_absente", 3,
                     "un dossier `installeur/` incomplet ⛔ n'est pas complet")
    ctrl(ok, "(c2) le code 3 — la PAGE absente", det)
    ok, det = detail("pilote_absent", 3,
                     "sans outil, les DEUX gestes exposes sont MORTS ; annoncer "
                     "« tout est la » est un mensonge d'instrument")
    ctrl(ok, "(c3) le code 3 — le PILOTE introuvable", det)
    ok, det = detail("bind_refuse", 4,
                     "un serveur qui n'a jamais demarre ⛔ n'est pas un serveur "
                     "demarre")
    ctrl(ok, "(c5) le code 4 — le `bind` EMPECHE au niveau socket", det)
    ok, det = detail("charge_absente", 5,
                     "sans charge, le geste PRINCIPAL de la page est impossible")
    ctrl(ok, "(c6) le code 5 — la CHARGE amputee", det)
    ok, det = detail("charge_absente_et_module", 5,
                     "l'ordre est une REGLE : le code le plus grave gagne, et "
                     "une charge absente empeche le geste principal la ou un "
                     "module manquant est un ECART DECLARE")
    ctrl(ok, "(c7) le code 5 passe AVANT le code 6", det)
    ok, det = detail("module_manquant", 6,
                     "c'est le PRECEDENT `dn7-1` : un `return 0` au lieu d'un "
                     "`return 6` laissait la gate d'alors a 25 OK / 0 KO")
    ctrl(ok, "(c8) le code 6 — l'ecart declare", det)

    # ⛔ LE `4` NE DOIT PAS ETRE UNE TRACE NUE — `AC7.1.6`, mot pour mot.
    txt = codes.get("bind_refuse__texte", "")
    phrase = "LE SERVEUR LOCAL N'A PAS PU DEMARRER" in txt
    nomme = "OSError" in txt
    nu = "Traceback" in txt
    ctrl(phrase and nomme and not nu,
         "(c4) le code 4 est PHRASE, ⛔ pas une trace nue",
         "la panne est nommee (`OSError`) et expliquee" if phrase and nomme
         and not nu
         else "⛔ %s — une fenetre double-cliquee qui montre une trace nue est "
              "exactement ce qu'`AC7.1.6` interdit"
              % ("un `Traceback` est imprime" if nu
                 else "la phrase d'explication est ABSENTE" if not phrase
                 else "l'exception n'est pas NOMMEE"))

    # ── (c9)(c10)(c11) LE `.bat`, LU COMME UN FLOT ──────────────────────
    print("\n── (c9)…(c11)(c17)…(c19) LE POINT D'ENTREE, MODELISE EN FLOT ──────")
    manquants = []
    for e in sorted(ETIQUETTES_A_CODE):
        k = flot["etiquettes"].get(e)
        if k is None:
            manquants.append("%s ABSENTE" % e)
        elif k not in flot["atteignables"]:
            manquants.append("%s INATTEIGNABLE depuis la tete" % e)
    # ⇒ ET UN SAUT NON RESOLU COMPTE COMME UN MANQUE : il tronque le flot.
    for inc in flot["inconnues"]:
        manquants.append("saut vers une etiquette INCONNUE (%s)" % inc)
    ctrl(not manquants, "(c9) toute etiquette a code est ATTEIGNABLE",
         "%d etiquette(s), chacune ATTEINTE depuis la tete du fichier"
         % len(ETIQUETTES_A_CODE) if not manquants
         else "⛔ %d ETIQUETTE(S) : %s — un code qu'⛔ AUCUN chemin n'atteint "
              "est un code publie que personne ne rend"
              % (len(manquants), " · ".join(manquants)))

    faux = []
    for e, attendu in sorted(ETIQUETTES_A_CODE.items()):
        vus = flot["codes"].get(e, set())
        if vus != {attendu}:
            faux.append("%s pose %s au lieu de %s"
                        % (e, sorted(vus) or "RIEN", attendu))
    ctrl(not faux, "(c10) chaque etiquette pose LE code declare",
         "%d appariement(s) etiquette ⇒ code" % len(ETIQUETTES_A_CODE)
         if not faux
         else "⛔ %s — une etiquette d'erreur qui publie un SUCCES est une "
              "gate qu'on debranche cote inconnu" % " · ".join(faux))

    publies = codes_de_l_entete(neuf["fichiers"].get(BAT, ""))
    attendus = set(CODES_PUBLIES)
    ctrl(publies == attendus,
         "(c11) l'en-tete PUBLIE exactement les codes rendus",
         "les %d codes publies sont ceux qui sont rendus : %s"
         % (len(attendus), " ".join(sorted(attendus))) if publies == attendus
         else "⛔ en-tete %s vs rendus %s — un code REEL que personne n'annonce "
              "est aussi mauvais qu'un code annonce que personne ne rend"
              % (sorted(publies) if publies is not None else "⛔ ILLISIBLE",
                 sorted(attendus)))

    # ── (c17) ⛔ AUCUN CODE HORS TABLE ───────────────────────────────────
    hors = []
    for etiquette, vus in sorted(flot["codes"].items()):
        if etiquette not in ETIQUETTES_A_CODE:
            hors.append("%s pose %s" % (etiquette, sorted(vus)))
    ctrl(not hors, "(c17) ⛔ aucune etiquette HORS table ne pose un code",
         "%d etiquette(s) posent un code, toutes declarees"
         % len(flot["codes"]) if not hors
         else "⛔ %s — un code pose par une etiquette que la table ⛔ ne declare "
              "pas est un code que l'en-tete n'annonce pas, et que ⛔ personne "
              "ne rejoue" % " · ".join(hors))

    # ── (c18) LES DEUX APPELS `%PY%` RELAIENT `%ERRORLEVEL%` ────────────
    relais, lignes = [], flot["lignes"]
    for k in flot["appels_py"]:
        ou = lignes[k][0]
        if k not in flot["atteignables"]:
            relais.append("l.%d INATTEIGNABLE" % ou)
            continue
        suite = lignes[k + 1][1] if k + 1 < len(lignes) else ""
        if not RE_SET_RC_RELAIS.match(suite):
            relais.append("l.%d suivie de %r" % (ou, suite[:40]))
    ctrl(len(flot["appels_py"]) == 2 and not relais,
         "(c18) les deux appels `%PY%` RELAIENT `%ERRORLEVEL%`",
         "2 appels, chacun suivi du relais" if len(flot["appels_py"]) == 2
         and not relais
         else "⛔ %d appel(s) `%%PY%%`%s — le code que le Python rend est jete "
              "si le relais ne le reprend pas IMMEDIATEMENT"
              % (len(flot["appels_py"]),
                 " : " + " · ".join(relais) if relais else ""))

    # ── (c19) `:FIN` SORT PAR `exit /b %RC%` ────────────────────────────
    sorties = sorties_depuis(flot, "FIN")
    if sorties is None:
        det19, ok19 = "⛔ l'etiquette `:FIN` est ABSENTE", False
    else:
        mauvaises = ["l.%d %r" % (n, s) for n, s in sorties
                     if not RE_EXIT_RC.match(s)]
        ok19 = bool(sorties) and not mauvaises
        det19 = ("%d sortie(s) atteignable(s) depuis `:FIN`, toutes en "
                 "`exit /b %%RC%%`" % len(sorties) if ok19
                 else "⛔ %s — le relais final EFFACE fait de tout code un "
                      "succes, et ⛔ aucun des six ne sort plus"
                      % (" · ".join(mauvaises) if mauvaises
                         else "⛔ AUCUNE sortie atteignable depuis `:FIN`"))
    ctrl(ok19, "(c19) `:FIN` sort par `exit /b %RC%`, et par lui seul", det19)

    # ── (c12)(c13)(c20) LES TROIS LISTES, LA PAGE, LES BOUTONS ──────────
    print("\n── (c12)(c13)(c20) LES TROIS LISTES, LA PAGE, LES BOUTONS ────────")
    du_bat = tuple(flot["noms"])
    du_serveur = images_du_serveur(neuf["fichiers"].get(PRODUIT, ""))
    ens_bat = set(du_bat)
    ens_srv = set(du_serveur or ()) | {"manifest.json"}
    ens_moi = set(NOMS_DE_CHARGE)
    ok = du_serveur is not None and ens_bat == ens_srv == ens_moi
    ctrl(ok, "(c12) les TROIS listes de noms de charge coincident",
         "%d noms, identiques des trois cotes" % len(ens_moi) if ok
         else "⛔ bat=%s · serveur=%s · gate=%s — un nom ajoute ou retire d'un "
              "SEUL cote laisse la charge amputee sans que le point d'entree "
              "bronche" % (sorted(ens_bat),
                           sorted(ens_srv) if du_serveur is not None
                           else "⛔ `IMAGES` ILLISIBLE", sorted(ens_moi)))

    ok, det, aria = la_page_est_un_document(neuf["fichiers"].get(PAGE, ""))
    ctrl(ok, "(c13) la page que le `3` garde est un DOCUMENT", det if ok
         else "%s — le `3` garde la PRESENCE du fichier ; s'il n'est plus un "
              "document, la page passe le pre-vol et casse APRES" % det)

    ok = aria == ARIA_ATTENDU
    ctrl(ok, "(c20) les quatre boutons de choix partent en ANGLAIS",
         "%s — l'anglais est PRESSE dans le balisage"
         % " ".join("%s=%s" % (k, aria[k]) for k in sorted(aria)) if ok
         else "⛔ balisage %s au lieu de %s — le defaut anglais de cette page "
              "tient PAR CE BALISAGE, et le banc part de la"
              % (sorted(aria.items()), sorted(ARIA_ATTENDU.items())))

    if regles["sortie_anticipee"]:
        return bilan(0, prevus=CONTROLES_PREVUS)

    # ── (c14)(c15)(c16) LA RECIPROQUE, MECANIQUE ────────────────────────
    print("\n── (c14)(c15)(c16) AUCUN CONTROLE GARDE PAR ZERO MUTANT ──────────")
    lus = dn_gates.ids_par_ast(os.path.abspath(__file__))
    vises = set()
    for v in cibles.values():
        vises.update(v)
    reels = (lus or set()) | {"z"}
    nus = sorted(reels - vises, key=lambda s: (len(s), s))
    ctrl(not nus and lus is not None,
         "(c14) chaque controle est vise par >= 1 mutant",
         "%d controle(s) lu(s) a l'AST, %d cible(s) declaree(s)"
         % (len(reels), len(vises)) if not nus and lus is not None
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

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : que `cmd.exe` relaie ces codes.")
    print("   Elle prouve que `main()` REND cinq d'entre eux — `0` `3` `4` `5`")
    print("   `6` — et que le flot du `.bat` POSE le sixieme sous une etiquette")
    print("   ATTEIGNABLE, relaie le `%ERRORLEVEL%` du Python et sort par")
    print("   `exit /b %RC%`. Le tir reel du point d'entree sous `cmd.exe` est")
    print("   NON JOUE : porteur AU LEDGER, `epic-dn8`.")
    return bilan(1 if dn_gates.ko_total[0] else 0, prevus=CONTROLES_PREVUS)


if __name__ == "__main__":
    sys.exit(main())

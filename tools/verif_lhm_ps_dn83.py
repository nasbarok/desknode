#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dn8-3 / AC8.3.4 — LA POLARITE DE LA SONDE LHM, JOUEE DANS LE **VRAI**
POWERSHELL, ET DANS LES DEUX SENS.

🔴 POURQUOI CETTE GATE EXISTE, ET CE QU'ELLE REFUTE.
   Le ledger a publie **CINQ FOIS** la meme cause pour ne pas jouer ce banc :
   *« ⛔ AUCUN banc PowerShell n'existe dans le depot [...] Il faudrait un hote
   PowerShell, que le WSL de la tour n'a pas »*. Cette cause est **REFUTEE par
   la mesure du 2026-09-12** : `powershell.exe` **5.1.19041.6456** repond
   `rc=0` depuis ce WSL, et un `.ps1` non signe s'y execute.

🔴 LE MECANISME EXACT DU FAUX NEGATIF — C'ETAIT UN **NOM**, ⛔ PAS UNE ABSENCE.
       shutil.which("powershell")     ⇒ None
       shutil.which("powershell.exe") ⇒ /mnt/c/Windows/System32/.../powershell.exe
   ⇒ pendant cinq entrees de ledger, la moitie PowerShell de ces constats a ete
     classee IMPOSSIBLE sur une methode de recherche fautive. C'est la meme
     regle que ce depot a deja payee deux fois : **« NON ATTEINT » est une
     propriete de la METHODE de recuperation, ⛔ pas de l'adresse.**
   ⇒ ON ESSAIE PLUSIEURS NOMS, et la commande s'ecrit A COTE du verdict.

── CE QU'ELLE JOUE, ET LE DISCRIMINANT ─────────────────────────────────────

Elle stagge un dossier jetable **visible de Windows**, y pose le VRAI
`dn_agent_tour.ps1` et un `dn_agent.py` de banc dont le SEUL changement est le
port de LHM, lance `stub_lhm_dn48.py`, puis appelle le pre-vol **dans les deux
sens** :

  · stub en `--mode vide`   (200, corps SANS une seule ligne `lhm_`)
        ⇒ attendu **exit 12** ET la ligne `LibreHardwareMonitor est INJOIGNABLE`
  · stub en `--mode normal` (la capture reelle)
        ⇒ attendu ⛔ **PAS 12** ET la ligne `LHM : <url> repond 200.`

⚠️ **LE DISCRIMINANT EST `12` vs ⛔ PAS `12`, ⛔ JAMAIS `12` vs `0`** — ET C'EST
   MESURE (2026-09-12) : au sens passant, le pre-vol CONTINUE apres le bloc LHM
   et sort en **`5`** sur une machine sans `COM3`. Un banc qui attendrait `0`
   rougirait sur une machine SAINE. ⇒ on vise **l'echec NOMME** et ce que la
   commande **imprime EN PROPRE**, ⛔ pas le `rc` global.

── CE QU'ELLE NE PROUVE ⛔ PAS, ECRIT PLUTOT QUE TU ─────────────────────────

⛔ Elle ⛔ n'installe PAS LibreHardwareMonitor, ⛔ ne pose AUCUNE tache
   planifiee, ⛔ n'ouvre AUCUN navigateur et ⛔ ne touche PAS a la tour reelle.
   Ce qu'elle gagne est un **hote PowerShell reel** et un **stub**, ⛔ pas une
   machine provisionnee. La regle de partage tient : la STRUCTURE aux gates
   statiques, le COMPORTEMENT a ce banc, l'ŒIL a une seance owner.
⛔ Elle ⛔ ne dit RIEN de la tour reelle, de sa tache planifiee, ni de la course
   au logon — ⛔ et rien de ce qui se juge A L'ŒIL.
⛔ Elle ⛔ ne se substitue PAS au vrai LHM : `stub_lhm_dn48.py` **refuse 8085**
   par construction, et ce banc travaille sur **8086**.

Emploi :
    python3 tools/verif_lhm_ps_dn83.py
    python3 tools/verif_lhm_ps_dn83.py --liste-mutants
    python3 tools/verif_lhm_ps_dn83.py --mutant <n>

Sortie : 0 si tout passe · 1 sur un vrai defaut · 2 sur un mutant inconnu ·
         3 si le mutant demande est PERIME (il n'a rien change) ·
         4 si AUCUN hote PowerShell n'est joignable, ou si la boucle locale
           REFUSE le `bind` — prerequis DECLARES, ⛔ pas des rouges.
⚠️ EN MODE MUTANT, UN PREREQUIS ABSENT DEVIENT UN **ROUGE NOMME** (`rc=1`) :
   `tools/verif_campagne_dn56.py` exige `rc=1` de chaque mutant, et elle ⛔
   n'est PAS `NON_JOUABLE`. C'est le defaut le plus cher de `dn8-1`, et il ⛔
   ne se rejoue pas ici.
"""

import argparse
import copy
import io
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time

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

OUTIL = "tools/dn_agent_tour.ps1"
AGENT = "agent/dn_agent.py"
STUB = "tools/stub_lhm_dn48.py"
FIXTURE = "tools/fixtures/lhm_metrics_2026-08-21.txt"
FIXES = (OUTIL, AGENT, STUB)

# ── L'AVEUGLEMENT DE CETTE GATE, DECLARE EN PROPRE (NFR14) ────────────────
# 🔴 `verif_harnais_dn81.py` (c3b) EXIGE CETTE DECLARATION : cette gate JUGE du
#    PowerShell (elle nomme `tools/dn_agent_tour.ps1`) et ⛔ elle ne le PARSE
#    pas. Un parseur PowerShell exigerait un runtime .NET, que la CI ⛔ n'a pas.
AVEUGLEMENT_POWERSHELL = (
    "⛔ CETTE GATE ⛔ NE PARSE PAS LE POWERSHELL — ET C'EST DECLARE. Les "
    "ancres qu'elle plante dans `tools/dn_agent_tour.ps1` (le code de sortie, "
    "le predicat de corps, la ligne passante) sont cherchees et remplacees en "
    "TEXTE. ⚠️ MAIS CE QU'ELLE JUGE, ELLE ⛔ NE LE LIT PAS : elle **EXECUTE** "
    "le script dans un vrai `powershell.exe` et relit son CODE DE SORTIE et sa "
    "SORTIE. L'aveuglement porte donc sur la MUTATION, ⛔ pas sur le verdict — "
    "et un mutant dont l'ancre a disparu rend `rc=3`, ⛔ jamais un vert.")

# 🔴 LE PORT DU BANC — **8086**, ⛔ JAMAIS 8085. `tools/stub_lhm_dn48.py`
#    refuse 8085 PAR CONSTRUCTION : un stub qui ecouterait a la place du vrai
#    LHM ferait mesurer le stub en croyant mesurer la tour. `(c5)` le REJOUE.
PORT_BANC = 8086
PORT_DU_VRAI_LHM = 8085

# 🔴 LE PIEGE DU NOM EST ECRIT **DANS LE FICHIER**, ⛔ pas seulement au ledger.
#    `which("powershell")` rend `None` sur une machine ou il EST la. ⇒ on
#    essaie PLUSIEURS noms, dans l'ordre, et on IMPRIME celui qui a repondu.
NOMS_POWERSHELL = ("powershell.exe", "pwsh.exe", "powershell", "pwsh")

# Ce que la commande imprime EN PROPRE, dans les deux sens. ⚠️ ASCII PUR, et
# c'est load-bearing : la console Windows ⛔ n'est PAS en UTF-8, et un motif
# accentue ne se retrouverait PAS dans la sortie capturee.
MOT_REFUS = "LibreHardwareMonitor est INJOIGNABLE"
MOT_PASSANT = "repond 200."
CODE_REFUS = 12

# ── LES ANCRES LITTERALES DES MUTANTS ─────────────────────────────────────
# Une ancre qui bouge rend son mutant PERIME (rc=3) ⇒ elle se remarque,
# ⛔ elle ne pourrit pas en silence.
A_EXIT_REFUS = "            exit 12"
A_PREDICAT_CORPS = "[string]$rep.Content -cmatch '(?m)^lhm_'"
A_LIGNE_PASSANTE = 'Dire ("LHM : " + $lhmUrl + " repond 200.")'
A_REFUS_8085 = "if a.port == 8085:"
# Les deux ancres du drapeau `-Lhm` dans l'outil — le PRODUIT de cette marche.
A_SURCHARGE = "        if ($null -ne $LhmPortForce) {"
A_ARGL_LHM = "        $argl += @('--lhm', $Lhm)"
# 🔴 LA SONDE DE PORT SERIE, DOUBLEE **DANS LA COPIE JETABLE**, ET POUR LE SEUL
#    TIR DU DRAPEAU : la ligne `args :` n'est imprimee qu'APRES elle, et COM3
#    peut etre TENU (il l'est sur cette tour : par l'agent REEL de l'owner).
#    ⛔ Rien n'est ecrit dans l'arbre, ⛔ aucun port reel n'est libere, et le
#    reste du produit est le VRAI. C'est le patron `PS1_DE_PAPIER` du depot.
A_SWITCH = "# " + "=" * 74 + "\nswitch ($Action) {"
DOUBLE_PORT = "function Get-EtatPort { param($p) return 'libre' }\n"
LHM_DRAPEAU = "127.0.0.1:%d" % PORT_BANC
A_PORT_AGENT = "LHM_PORT = 8085"

DELAI_PREVOL = 90
DELAI_STUB = 20

MUTANTS = {}                      # ⛔ AU NIVEAU MODULE — `--liste-mutants`
CIBLES = {}                       # le controle que chaque mutant doit ROUGIR

MUTANTS[1] = ("OUTIL : le refus LHM sort en `exit 4` au lieu de `exit 12` — "
              "LE PRECEDENT `dn7-5`, et `4` est NEUTRALISE en `0` par `lancer`")
CIBLES[1] = ("c2",)
MUTANTS[2] = ("OUTIL : le predicat de corps `^lhm_` DISPARAIT ⇒ un `200` nu "
              "suffit, et un exportateur VOISIN passerait pour LHM")
CIBLES[2] = ("c2",)
MUTANTS[3] = ("OUTIL : la ligne passante ne dit plus `repond 200.` ⇒ le sens "
              "PASSANT n'est plus ancre sur ce que la commande imprime")
CIBLES[3] = ("c3",)
MUTANTS[4] = ("BANC : le staging ⛔ NE COPIE PAS l'agent ⇒ le pre-vol sort en "
              "`3` EN AMONT, et ⛔ n'atteint JAMAIS le bloc LHM")
CIBLES[4] = ("c2", "c3", "c4", "c7", "c8")  # MESURE : sans agent, les DEUX
#                        stagings sont amputes ⇒ ⛔ aucune URL et ⛔ aucun `args :`
MUTANTS[5] = ("BANC : le stub est lance dans le MAUVAIS mode ⇒ les deux sens "
              "mesurent le meme etat, et la polarite n'est plus eprouvee")
CIBLES[5] = ("c2",)              # MESURE : les 2 modes sains ⇒ SEUL le sens REFUS ment
MUTANTS[6] = ("BANC : le port du banc ⛔ n'est PAS pose dans l'agent stagge ⇒ "
              "la sonde vise le port du VRAI LHM, que ce banc ⛔ ne lie pas")
CIBLES[6] = ("c2", "c4")         # MESURE : le VRAI LHM ecoute ici ⇒ le sens REFUS ne refuse plus
MUTANTS[7] = ("STUB : le refus de `8085` DISPARAIT ⇒ un stub pourrait ecouter "
              "a la place du vrai LHM, et on mesurerait le stub")
CIBLES[7] = ("c5",)
MUTANTS[9] = ("BANC : le plafond d'un tir tombe a ZERO ⇒ le pre-vol est TUE "
              "avant d'avoir rendu un code. Un `rc is None` de depassement est "
              "la mesure de CETTE GATE, ⛔ pas le verdict du sujet")
CIBLES[9] = ("c1", "c2", "c3", "c4", "c7", "c8")  # MESURE : ⛔ aucun code ⇒
#                        ⛔ aucune URL, et ⛔ aucune ligne `args :` non plus
MUTANTS[10] = ("OUTIL : la SURCHARGE par `-Lhm` DISPARAIT ⇒ la sonde reste "
               "sur le port LU dans l'agent, et le drapeau ne pilote RIEN")
CIBLES[10] = ("c7", "c8")        # MESURE : sans surcharge, `$LhmSonde` reste
#                        FAUX ⇒ l'outil REFUSE de passer --lhm ⇒ ⛔ pas d'`args :`
MUTANTS[11] = ("OUTIL : le `--lhm` pose dans `$argl` DISPARAIT ⇒ l'agent ⛔ ne "
               "RECOIT PAS l'adresse, alors que la sonde, elle, l'a vue")
CIBLES[11] = ("c8",)
MUTANTS[8] = ("declare une cible VIDE pour le mutant 7 — SEUL sur `(c5)` ⇒ un "
              "controle garde par ZERO mutant, le risque deja paye ailleurs")
CIBLES[8] = ("c6",)

# ⚠️ LE COMPTE DU CHEMIN NORMAL : un (c0) par mutant declare + les 6 controles
#    numerotes. Il se PERIME si on ajoute un controle sans le mettre a jour —
#    et c'est voulu : c'est ce qui rend `(z)` FALSIFIABLE.
CONTROLES_PREVUS = len(MUTANTS) + 8

_MUTANT = 0


def prerequis():
    """Les prerequis de ce banc, evalues ENSEMBLE : (ps, temp, trace, motif).

    🔴 ILS SONT **TROIS**, ⛔ PAS UN — et `tools/run_gates.sh` derive son temoin
       de leur CONJONCTION. Un seul present ne rend pas ce banc jouable.
    ⚠️ `wslpath` EN EST UN : sans lui ⛔ aucun chemin ne se traduit pour
       PowerShell, et un `pwsh` **Linux** ferait croire le banc jouable."""
    ps, nom_ps, essais = trouver_powershell()
    trace = " · ".join("which(%r)⇒%s" % (n, c or "None") for n, c in essais)
    if not ps:
        return None, None, trace, "⛔ AUCUN hote PowerShell joignable"
    if not shutil.which("wslpath"):
        return None, None, trace, ("⛔ `wslpath` est INTROUVABLE : ⛔ aucun "
                                   "chemin ne se traduit pour PowerShell")
    liable, motif_bind = la_boucle_locale_accepte_un_bind()
    if not liable:
        return None, None, trace, ("⛔ la boucle locale REFUSE le `bind` : %s"
                                   % motif_bind)
    temp = temp_de_windows(ps)
    if temp is None:
        return None, None, trace, ("⛔ AUCUN dossier temporaire VISIBLE DE "
                                   "WINDOWS")
    return ps, temp, trace, None


def trouver_powershell():
    """Le premier hote PowerShell joignable, et LE NOM qui l'a trouve.

    🔴 PLUSIEURS NOMS, ⛔ PAS UN SEUL — ET C'EST LA LECON DE CETTE MARCHE.
       `which("powershell")` rend `None` la ou `which("powershell.exe")` rend
       le chemin. Publier « absent » sur un seul nom, c'est publier une
       propriete de SA PROPRE METHODE."""
    essais = []
    for nom in NOMS_POWERSHELL:
        chemin = shutil.which(nom)
        essais.append((nom, chemin))
        if chemin:
            return chemin, nom, essais
    return None, None, essais


def la_boucle_locale_accepte_un_bind():
    """Le SECOND prerequis : ce banc LIE le stub sur la boucle locale."""
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        return True, "bind accepte"
    except OSError as exc:
        return False, "⛔ %s: %s" % (type(exc).__name__, exc)
    finally:
        if s is not None:
            s.close()


def temp_de_windows(ps):
    """Le dossier temporaire **de Windows**, vu depuis WSL.

    🔴 LE STAGING DOIT ETRE VISIBLE DE WINDOWS, ET C'EST MESURE : un banc qui
       passerait a PowerShell un chemin que PowerShell ne sait pas lire
       echouerait **pour une raison qui n'a rien a voir avec la polarite**, et
       son rouge serait un FAUX.

    🔴 ANNOTE LE 2026-09-12 — ⛔ LE PARAGRAPHE CI-DESSUS N'EST PAS EFFACE, MAIS
       SON MOTIF EST **REFUTE**. `Test-Path` sur un chemin `\\wsl.localhost`
       rend **True** (4 tirs sur 4) et `Get-Content` lit REELLEMENT le fichier :
       PowerShell SAIT lire le depot a son chemin WSL.
       ⇒ LA FONCTION RESTE, ET SA VRAIE RAISON EST PLUS FORTE : `stagger()` pose
         des copies **MUTEES** (un `dn_agent.py` dont le port change, un outil
         dont une faute est REPLANTEE). Les ecrire dans l'arbre serait une
         MUTATION PENDANT UNE PASSE DE MESURE — inacceptable quel que soit ce
         que PowerShell sait lire. Detail : `mesures/dn8-3/T1`."""
    try:
        r = subprocess.run([ps, "-NoProfile", "-Command", "$env:TEMP"],
                           timeout=DELAI_STUB, stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL)
        brut = r.stdout.decode("utf-8", "replace").strip()
    except (OSError, subprocess.TimeoutExpired):
        return None
    if not brut:
        return None
    try:
        u = subprocess.run(["wslpath", "-u", brut], timeout=DELAI_STUB,
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        chemin = u.stdout.decode("utf-8", "replace").strip()
    except (OSError, subprocess.TimeoutExpired):
        return None
    return chemin if chemin and os.path.isdir(chemin) else None


def lire_fixe(rel):
    """Le texte d'un fichier du depot — ⛔ jamais une copie recopiee ici."""
    return io.open(os.path.join(RACINE, rel), encoding="utf-8").read()


def muter(etat):
    """REPLANTE une faute DANS L'ETAT — ⛔ jamais dans un fichier du depot.

    ⛔ CHAQUE MUTANT **REPLANTE LA FAUTE**, ⛔ il ne debranche aucune garde : un
       mutant qui coupe le controle ne prouve que l'existence du controle.
    ⚠️ Tout corps VERIFIE son ancre et rend `e` INCHANGE si elle a disparu : le
       corps principal compare l'etat AVANT/APRES, et un mutant sans effet rend
       **`rc=3`**, ⛔ jamais un vert."""
    e = copy.deepcopy(etat)
    p, r, c = e["fichiers"], e["regles"], e["cibles"]

    if _MUTANT == 1:
        if A_EXIT_REFUS not in p.get(OUTIL, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[OUTIL] = p[OUTIL].replace(A_EXIT_REFUS, "            exit 4", 1)
    elif _MUTANT == 2:
        if A_PREDICAT_CORPS not in p.get(OUTIL, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[OUTIL] = p[OUTIL].replace(A_PREDICAT_CORPS, "$true", 1)
    elif _MUTANT == 3:
        if A_LIGNE_PASSANTE not in p.get(OUTIL, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[OUTIL] = p[OUTIL].replace(
            A_LIGNE_PASSANTE, 'Dire ("LHM : " + $lhmUrl + " est la.")', 1)
    elif _MUTANT == 4:
        if not r.get("stagge_agent"):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        r["stagge_agent"] = False
    elif _MUTANT == 5:
        if r.get("modes") != ("vide", "normal"):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        r["modes"] = ("normal", "normal")
    elif _MUTANT == 6:
        if not r.get("pose_le_port"):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        r["pose_le_port"] = False
    elif _MUTANT == 7:
        if A_REFUS_8085 not in p.get(STUB, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[STUB] = p[STUB].replace(A_REFUS_8085, "if False:", 1)
    elif _MUTANT == 9:
        if r.get("delai") != DELAI_PREVOL:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        r["delai"] = 0
    elif _MUTANT == 10:
        if A_SURCHARGE not in p.get(OUTIL, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[OUTIL] = p[OUTIL].replace(A_SURCHARGE, "        if ($false) {", 1)
    elif _MUTANT == 11:
        if A_ARGL_LHM not in p.get(OUTIL, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[OUTIL] = p[OUTIL].replace(A_ARGL_LHM, "", 1)
    elif _MUTANT == 8:
        # ⚠️ LA CIBLE EST **VIDEE**, ⛔ la cle n'est pas supprimee : supprimer
        #    la cle ferait AUSSI diverger `CIBLES` et `MUTANTS`. Le mutant 7
        #    est le SEUL a viser `(c5)`.
        if not c.get(7):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        c[7] = ()
    return e


class AncreAbsente(Exception):
    """Une ancre du banc a disparu du produit — ⛔ jamais un no-op silencieux."""


def stagger(fichiers, regles, racine_temp, double_le_port=False):
    """Un dossier jetable, AUTO-SUFFISANT, visible de Windows.

    🔴 `dn_agent_tour.ps1` derive sa racine de `$MyInvocation.MyCommand.Path`
       et cherche `dn_agent.py` **A COTE DE LUI** ⇒ un dossier stagge se
       suffit. ⛔ Rien n'est ecrit dans l'arbre du depot, jamais."""
    stage = tempfile.mkdtemp(prefix="dn83-", dir=racine_temp)
    os.makedirs(os.path.join(stage, "tools", "fixtures"))
    outil = fichiers[OUTIL]
    if double_le_port:
        if A_SWITCH not in outil:
            raise AncreAbsente("l'ancre du `switch` est INTROUVABLE dans `%s` : "
                               "la sonde de port ⛔ n'a PAS pu etre doublee"
                               % OUTIL)
        outil = outil.replace(A_SWITCH, DOUBLE_PORT + A_SWITCH, 1)
    with io.open(os.path.join(stage, "dn_agent_tour.ps1"), "w",
                 encoding="utf-8", newline="") as fh:
        fh.write(outil)
    with io.open(os.path.join(stage, "tools", "stub_lhm_dn48.py"), "w",
                 encoding="utf-8", newline="") as fh:
        fh.write(fichiers[STUB])
    shutil.copyfile(os.path.join(RACINE, FIXTURE),
                    os.path.join(stage, "tools", "fixtures",
                                 os.path.basename(FIXTURE)))
    if regles["stagge_agent"]:
        agent = fichiers[AGENT]
        if regles["pose_le_port"]:
            # 🔴 L'ANCRE EST VERIFIEE : un `replace` qui ⛔ ne trouve RIEN est
            #    un NO-OP SILENCIEUX, et le banc sonderait le port du VRAI LHM
            #    de la tour en croyant mesurer son stub.
            if A_PORT_AGENT not in agent:
                raise AncreAbsente(
                    "l'ancre %r est INTROUVABLE dans `%s` — le port du banc ⛔ "
                    "n'a PAS pu etre pose, et la sonde viserait le VRAI LHM"
                    % (A_PORT_AGENT, AGENT))
            agent = agent.replace(A_PORT_AGENT,
                                  "LHM_PORT = %d" % PORT_BANC, 1)
        with io.open(os.path.join(stage, "dn_agent.py"), "w",
                     encoding="utf-8", newline="") as fh:
            fh.write(agent)
    return stage


def attendre_le_stub(stub, port, delai=10.0):
    """Le stub ecoute-t-il ? ⛔ On ne DORT PAS une duree fixe : on SONDE.

    ⚠️ Une attente fixe est un cout paye a CHAQUE mutant, et
       `verif_campagne_dn56.py` rejoue chaque mutant. Le budget est mesure."""
    t0 = time.time()
    while time.time() - t0 < delai:
        # 🔴 LE STUB EST-IL ENCORE VIVANT ? Si le port est DEJA TENU par un
        #    autre ecouteur, le stub MEURT et le `connect()` reussit QUAND
        #    MEME — sur l'ETRANGER. Les deux sens mesureraient alors un
        #    service que ce banc ⛔ n'a PAS lie.
        if stub.poll() is not None:
            return False
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        try:
            s.connect(("127.0.0.1", port))
            return True
        except OSError:
            time.sleep(0.05)
        finally:
            s.close()
    return False


def jouer_un_sens(ps, stage, mode, py_stub, delai):
    """Lance le stub dans `mode`, joue le pre-vol, rend (rc, sortie).

    ⛔ LE STUB EST FERME DANS UN `finally` — un banc qui laisse un serveur
       derriere lui empoisonne le tir suivant."""
    stub = None
    try:
        stub = subprocess.Popen(
            [py_stub, os.path.join(stage, "tools", "stub_lhm_dn48.py"),
             "--port", str(PORT_BANC), "--mode", mode],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not attendre_le_stub(stub, PORT_BANC):
            mort = stub.poll()
            return None, ("⛔ LE STUB N'ECOUTE PAS sur %d (%s)"
                          % (PORT_BANC,
                             "il est MORT, rc=%s — le port est-il DEJA TENU ?"
                             % mort if mort is not None else "delai depasse"))
        try:
            r = subprocess.run(
                [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                 chemin_windows(os.path.join(stage, "dn_agent_tour.ps1")),
                 "prevol", "-Serie", "COM_DE_BANC_INEXISTANT"],
                timeout=delai, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            return r.returncode, r.stdout.decode("utf-8", "replace")
        except subprocess.TimeoutExpired as exc:
            brut = exc.output or b""
            return None, ("⛔ TIMEOUT apres %s s\n%s"
                          % (delai, brut.decode("utf-8", "replace")))
        except OSError as exc:
            return None, "⛔ IMPOSSIBLE A LANCER : %s" % exc
    finally:
        if stub is not None:
            stub.terminate()
            try:
                stub.wait(timeout=5)
            except subprocess.TimeoutExpired:              # pragma: no cover
                stub.kill()


def jouer_le_drapeau(ps, stage, py_stub, delai):
    """Le tir du DRAPEAU : l'agent garde SON port, et `-Lhm` doit le SURCHARGER.

    🔴 SANS CE TIR, `-Lhm` — LE PRODUIT DE CETTE MARCHE — N'EST EXERCE PAR
       AUCUN CONTROLE : retirer le `--lhm` de `$argl` laissait toute la suite
       VERTE (revue du 2026-09-12).
    ⚠️ Le staging de ce tir double la SONDE DE PORT SERIE, et elle seule : la
       ligne `args :` n'est imprimee qu'APRES elle. ⛔ Rien dans l'arbre."""
    stub = None
    try:
        stub = subprocess.Popen(
            [py_stub, os.path.join(stage, "tools", "stub_lhm_dn48.py"),
             "--port", str(PORT_BANC), "--mode", "normal"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not attendre_le_stub(stub, PORT_BANC):
            return None, "⛔ LE STUB N'ECOUTE PAS sur %d" % PORT_BANC
        try:
            r = subprocess.run(
                [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                 chemin_windows(os.path.join(stage, "dn_agent_tour.ps1")),
                 "prevol", "-Serie", "COM3", "-Lhm", LHM_DRAPEAU],
                timeout=delai, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            return r.returncode, r.stdout.decode("utf-8", "replace")
        except subprocess.TimeoutExpired as exc:
            return None, ("⛔ TIMEOUT apres %s s\n%s"
                          % (delai, (exc.output or b"").decode("utf-8", "replace")))
        except OSError as exc:
            return None, "⛔ IMPOSSIBLE A LANCER : %s" % exc
    finally:
        if stub is not None:
            stub.terminate()
            try:
                stub.wait(timeout=5)
            except subprocess.TimeoutExpired:              # pragma: no cover
                stub.kill()


def chemin_windows(chemin):
    """Le chemin, tel que PowerShell sait le lire."""
    try:
        r = subprocess.run(["wslpath", "-w", chemin], timeout=DELAI_STUB,
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        vu = r.stdout.decode("utf-8", "replace").strip()
        return vu or chemin
    except (OSError, subprocess.TimeoutExpired):            # pragma: no cover
        return chemin


def le_stub_refuse_le_vrai_port(stage, py_stub):
    """(c5) Le stub REFUSE-t-il le port du vrai LHM ? ⛔ On le REJOUE."""
    try:
        r = subprocess.run(
            [py_stub, os.path.join(stage, "tools", "stub_lhm_dn48.py"),
             "--port", str(PORT_DU_VRAI_LHM), "--mode", "normal"],
            timeout=DELAI_STUB, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        return r.returncode, r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return None, "⛔ TIMEOUT — le stub a ACCEPTE %d et s'est mis a SERVIR" % PORT_DU_VRAI_LHM
    except OSError as exc:                                  # pragma: no cover
        return None, "⛔ IMPOSSIBLE A LANCER : %s" % exc


def main():
    global _MUTANT
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--mutant", type=int, default=0)
    ap.add_argument("--liste-mutants", action="store_true")
    a = ap.parse_args()

    if a.liste_mutants:
        # 🔴 ⛔ AUCUN MUTANT DECLARE QUAND LE BANC ⛔ NE PEUT PAS TOURNER.
        #    MESURE (revue du 2026-09-12) : sur un PATH sans PowerShell, chaque
        #    mutant rendait `rc=1` + un `BILAN` + un `[KO ]` — EXACTEMENT les
        #    trois conditions de `verif_campagne_dn56.py`. Les mutants
        #    « passaient » donc la campagne SANS que leur faute replantee soit
        #    exercee une seule fois : elle prouvait `mutant ⇒ rouge` POUR UNE
        #    RAISON SANS RAPPORT avec la faute.
        #    ⇒ on ⛔ ne DECLARE RIEN : `dn56` n'en joue alors AUCUN, et elle
        #      ⛔ ne recoit ⛔ ni faux vert ⛔ ni faux rouge.
        _ps, _tmp, _tr, motif = prerequis()
        if motif:
            print("  ⛔ AUCUN MUTANT DECLARE — LE BANC ⛔ NE PEUT PAS TOURNER ICI.")
            print("     %s" % motif)
            print("     Les %d mutants existent dans la table ; ils ⛔ ne sont"
                  % len(MUTANTS))
            print("     PAS declares parce qu'⛔ AUCUN ne serait EXERCE — un")
            print("     mutant rouge sur un prerequis absent ⛔ ne prouve RIEN")
            print("     de la faute qu'il replante.")
            return 0
        for n in sorted(MUTANTS):
            print("  %2d  [%s]  %s"
                  % (n, ",".join(CIBLES.get(n, ())) or "—", MUTANTS[n]))
        return 0
    if a.mutant and a.mutant not in MUTANTS:
        print("⛔ mutant %d inconnu — `--liste-mutants` les donne." % a.mutant)
        return 2
    _MUTANT = a.mutant or 0

    print("=" * 78)
    print("dn8-3 — LA POLARITE DE LA SONDE LHM, DANS LE **VRAI** POWERSHELL"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)
    print(AVEUGLEMENT_POWERSHELL)

    for n in sorted(MUTANTS):
        if not ctrl(bool(CIBLES.get(n)) and bool(MUTANTS.get(n)),
                    "(c0) le mutant %d a une CIBLE et un LIBELLE" % n,
                    "→ %s" % ",".join(CIBLES.get(n, ()))
                    if CIBLES.get(n) else "⛔ cible ou libelle manquant"):
            return bilan(1, "un mutant est declare a moitie",
                         prevus=CONTROLES_PREVUS)

    # ── LES TROIS PREREQUIS, EVALUES ENSEMBLE ─────────────────────────
    ps, racine_temp, trace, motif = prerequis()
    if motif:
        if _MUTANT:
            # 🔴 SOUS MUTANT, UN PREREQUIS ABSENT REND **`rc=3`** — « NON
            #    EXERCE » —, ⛔ JAMAIS `rc=1` AVEC UN `[KO ]`. Un `1`
            #    satisfait les TROIS conditions de `verif_campagne_dn56.py`
            #    et ferait passer le mutant SANS que sa faute soit jouee.
            #    `3` est deja le langage du no-op de ce depot.
            ctrl(False, "(c0) le mutant %d a ete EXERCE" % _MUTANT,
                 "⛔ PREREQUIS ABSENT : %s — la faute replantee ⛔ n'a PAS ete "
                 "jouee, et ce tir ⛔ ne prouve RIEN" % motif)
            return bilan(3, "prerequis absent : le mutant %d ⛔ n'a PAS ete "
                            "exerce" % _MUTANT, prevus=CONTROLES_PREVUS)
        print("\n⛔ PREREQUIS ABSENT : %s" % motif)
        print("   %s" % trace)
        print("   ⚠️ LES %d NOMS ONT ETE ESSAYES, ET C'EST LE POINT : un seul"
              % len(NOMS_POWERSHELL))
        print("      nom essaye rendrait une propriete de la METHODE, ⛔ pas")
        print("      de la machine. Ce depot l'a paye CINQ FOIS au ledger.")
        print("   Cette gate ⛔ NE SORT PAS VERTE pour autant : elle rend 4, et")
        print("   `tools/run_gates.sh` la declare NON-JOUABLE sur un temoin")
        print("   derive de la CONJONCTION des trois prerequis.")
        return 4

    print("\nhote PowerShell : %s" % ps)
    print("               %s" % trace)
    print("staging        : %s   (visible de Windows)" % racine_temp)
    print("port du banc   : %d   (⛔ JAMAIS %d — le stub le refuse)"
          % (PORT_BANC, PORT_DU_VRAI_LHM))

    try:
        fichiers = {rel: lire_fixe(rel) for rel in FIXES}
        # ⚠️ LA FIXTURE EST LUE ICI **AUSSI**, et elle ⛔ n'est PAS dans FIXES :
        #    `stagger()` la COPIE, donc son absence levait HORS de cette garde.
        with open(os.path.join(RACINE, FIXTURE), "rb") as _f:
            _f.read(1)
    except (OSError, UnicodeDecodeError) as exc:
        # 🔴 ECHOUER **FERME** : un fichier du depot introuvable rendait un
        #    Traceback NU et ⛔ AUCUNE ligne `BILAN` — la signature d'une gate
        #    MORTE, que `run_gates.sh` imprime `[ROUGE] rc=1` SANS MOTIF.
        ctrl(False, "(c0) les fichiers du depot se LISENT",
             "⛔ %s: %s — ce banc lit : %s"
             % (type(exc).__name__, exc, " · ".join(FIXES + (FIXTURE,))))
        return bilan(1, "un fichier du depot ne se lit pas",
                     prevus=CONTROLES_PREVUS)
    etat = {
        "fichiers": fichiers,
        "regles": {"stagge_agent": True, "pose_le_port": True,
                   "modes": ("vide", "normal"), "delai": DELAI_PREVOL},
        "cibles": {n: tuple(v) for n, v in CIBLES.items()},
    }
    try:
        neuf = muter(etat) if _MUTANT else etat
    except Exception as exc:                                # noqa: BLE001
        ctrl(False, "(c0) le mutant %d s'applique" % _MUTANT,
             "⛔ IL LEVE : %s: %s" % (type(exc).__name__, exc))
        return bilan(1, "le mutant %d n'a pas pu s'appliquer" % _MUTANT)
    if _MUTANT and neuf == etat:
        ctrl(False, "(c0) le mutant %d a bien un EFFET" % _MUTANT,
             "⛔ SANS EFFET — son ancre litterale a disparu de la cible. "
             "⛔ Ce n'est PAS un controle vert : rc=3, mutant PERIME.")
        return bilan(3, "le mutant %d n'a eu aucun effet" % _MUTANT)

    regles = neuf["regles"]
    stage = None
    stage_lhm = None
    try:
        try:
            stage = stagger(neuf["fichiers"], regles, racine_temp)
            # ⚠️ LE STAGING DU DRAPEAU : l'agent garde SON port (⛔ pas de
            #    `pose_le_port`), pour que `-Lhm` ait quelque chose a SURCHARGER.
            stage_lhm = stagger(neuf["fichiers"],
                                dict(regles, pose_le_port=False),
                                racine_temp, double_le_port=True)
        except AncreAbsente as exc:
            ctrl(False, "(c0) les ancres du banc EXISTENT dans le produit",
                 "⛔ %s" % exc)
            return bilan(1, "une ancre du banc a disparu du produit",
                         prevus=CONTROLES_PREVUS)
        except OSError as exc:
            # 🔴 ⛔ JAMAIS UN TRACEBACK NU : `run_gates.sh` l'imprime
            #    `[ROUGE] rc=1` SANS MOTIF, et c'est la signature d'une gate
            #    MORTE — indiscernable d'un vrai defaut du sujet.
            ctrl(False, "(c0) le staging du banc s'ECRIT",
                 "⛔ %s: %s" % (type(exc).__name__, exc))
            return bilan(1, "le staging du banc ne s'ecrit pas",
                         prevus=CONTROLES_PREVUS)
        mode_refus, mode_passant = regles["modes"]
        py_stub = sys.executable

        print("\n── (c1)(c2)(c3) LES DEUX SENS, JOUES DANS LE VRAI POWERSHELL ──")
        delai = regles["delai"]
        rc_r, out_r = jouer_un_sens(ps, stage, mode_refus, py_stub, delai)
        rc_p, out_p = jouer_un_sens(ps, stage, mode_passant, py_stub, delai)

        joues = rc_r is not None and rc_p is not None
        ctrl(joues, "(c1) les DEUX sens ont ete JOUES",
             "sens REFUS ⇒ rc=%s · sens PASSANT ⇒ rc=%s" % (rc_r, rc_p)
             if joues
             else "⛔ un tir n'a rendu AUCUN code — un `rc is None` de "
                  "depassement est la mesure de CETTE GATE, ⛔ pas le verdict "
                  "du sujet : %s"
                  % (out_r if rc_r is None else out_p).strip()[:160])

        # 🔴 L'ECHEC NOMME, ⛔ PAS LE `rc` GLOBAL.
        dit_refus = MOT_REFUS in (out_r or "")
        ok2 = rc_r == CODE_REFUS and dit_refus
        ctrl(ok2, "(c2) sens REFUS : `exit %d` ET la ligne qui NOMME LHM"
             % CODE_REFUS,
             "rc=%d, et la sortie porte `%s`" % (CODE_REFUS, MOT_REFUS)
             if ok2
             else "⛔ %s — un LHM qui REPOND sans une seule ligne `lhm_` ⛔ "
                  "n'est PAS LUI, et le pre-vol doit REFUSER"
                  % ("rc=%s au lieu de %d" % (rc_r, CODE_REFUS)
                     if rc_r != CODE_REFUS
                     else "rc=%d mais la sortie ⛔ ne porte PAS `%s`"
                          % (CODE_REFUS, MOT_REFUS)))

        # ⚠️ `12` vs ⛔ PAS `12` — ⛔ JAMAIS `12` vs `0` : MESURE le 2026-09-12,
        #    le pre-vol continue et sort en `5` sur une machine sans COM3.
        dit_passant = MOT_PASSANT in (out_p or "")
        ok3 = rc_p is not None and rc_p != CODE_REFUS and dit_passant
        ctrl(ok3, "(c3) sens PASSANT : ⛔ PAS `%d`, ET la ligne passante"
             % CODE_REFUS,
             "rc=%s (⛔ pas %d), et la sortie porte `%s`"
             % (rc_p, CODE_REFUS, MOT_PASSANT) if ok3
             else "⛔ %s — le discriminant est `%d` vs ⛔ PAS `%d`, ⛔ jamais "
                  "`%d` vs `0` : apres le bloc LHM le pre-vol CONTINUE et sort "
                  "en 4/5/6 selon la machine"
                  % ("rc=%s : le sens passant a REFUSE" % rc_p
                     if rc_p == CODE_REFUS
                     else "la sortie ⛔ ne porte PAS `%s`" % MOT_PASSANT,
                     CODE_REFUS, CODE_REFUS, CODE_REFUS))

        # ── (c4) L'ADRESSE EST **LUE DANS L'AGENT**, ⛔ JAMAIS RECOPIEE ──
        print("\n── (c4)(c5) L'ADRESSE LUE, ET LE STUB QUI REFUSE LE VRAI PORT ──")
        url_vue = re.search(r"http://[\d.]+:(\d+)/\S*", out_p or "")
        port_vu = int(url_vue.group(1)) if url_vue else None
        ok4 = port_vu == PORT_BANC
        ctrl(ok4, "(c4) le pre-vol SONDE le port pose dans l'agent stagge",
             "l'URL sondee porte %d — l'adresse est LUE dans `%s`, ⛔ pas "
             "recopiee dans l'outil" % (PORT_BANC, AGENT) if ok4
             else "⛔ %s — si l'outil figeait l'adresse, ce banc mesurerait le "
                  "port du VRAI LHM, que ⛔ personne n'a lie ici"
                  % ("l'URL sondee porte %s au lieu de %d" % (port_vu,
                                                              PORT_BANC)
                     if port_vu is not None
                     else "⛔ AUCUNE URL LHM dans la sortie"))

        rc5, out5 = le_stub_refuse_le_vrai_port(stage, py_stub)
        ok5 = rc5 is not None and rc5 != 0 and str(PORT_DU_VRAI_LHM) in out5
        ctrl(ok5, "(c5) le stub REFUSE %d, et il le DIT" % PORT_DU_VRAI_LHM,
             "rc=%s, et le refus nomme %d" % (rc5, PORT_DU_VRAI_LHM) if ok5
             else "⛔ %s — un stub qui ecoute a la place du vrai LHM ferait "
                  "MESURER LE STUB en croyant mesurer la tour"
                  % ("rc=%s : il a ACCEPTE le port du vrai LHM" % rc5
                     if rc5 == 0 or rc5 is None
                     else "il refuse, mais ⛔ sans nommer %d"
                          % PORT_DU_VRAI_LHM))

        # ── (c7)(c8) LE DRAPEAU `-Lhm` — LE PRODUIT DE CETTE MARCHE ────
        print("\n── (c7)(c8) `-Lhm` SURCHARGE LA SONDE, ET ARRIVE A L'AGENT ───")
        rc_d, out_d = jouer_le_drapeau(ps, stage_lhm, py_stub, regles["delai"])
        m_url = re.search(r"http://[^\s:]+:(\d+)/\S*", out_d or "")
        port_d = int(m_url.group(1)) if m_url else None
        ok7 = port_d == PORT_BANC
        ctrl(ok7, "(c7) `-Lhm` SURCHARGE le port LU dans l'agent",
             "l'agent stagge porte %d, la sonde a vise %d"
             % (PORT_DU_VRAI_LHM, PORT_BANC) if ok7
             else "⛔ %s — le drapeau ⛔ ne pilote alors RIEN, et une tour dont "
                  "LHM ecoute ailleurs resterait refusee"
                  % ("la sonde a vise %s au lieu de %d" % (port_d, PORT_BANC)
                     if port_d is not None
                     else "⛔ AUCUNE URL LHM dans la sortie (rc=%s)" % rc_d))
        m_args = re.search(r"(?m)^\s*args\s*:\s*(.+)$", out_d or "")
        ligne_args = m_args.group(1).strip() if m_args else ""
        attendu = "--lhm " + LHM_DRAPEAU
        ok8 = attendu in ligne_args
        ctrl(ok8, "(c8) l'agent RECOIT `--lhm` — la ligne `args :` le porte",
             "`%s`" % ligne_args if ok8
             else "⛔ %s — la sonde aurait VU l'adresse et l'agent ⛔ ne la "
                  "RECEVRAIT PAS : `DN_ARGS` est ce que `:EXEC` rejoue"
                  % ("la ligne `args :` ⛔ ne porte PAS `%s` : `%s`"
                     % (attendu, ligne_args) if ligne_args
                     else "⛔ AUCUNE ligne `args :` (rc=%s)" % rc_d))

        # ── (c6) LA RECIPROQUE, MECANIQUE ──────────────────────────────
        print("\n── (c6) ⛔ AUCUN CONTROLE GARDE PAR ZERO MUTANT ───────────────")
        lus = dn_gates.ids_par_ast(os.path.abspath(__file__))
        vises = set()
        for v in neuf["cibles"].values():
            vises.update(v)
        reels = (lus or set()) - {"c0", "z"}
        nus = sorted(reels - vises, key=lambda s: (len(s), s))
        ctrl(not nus and lus is not None,
             "(c6) chaque controle est vise par >= 1 mutant",
             "%d controle(s) lu(s) a l'AST, %d cible(s) declaree(s)"
             % (len(reels), len(vises)) if not nus and lus is not None
             else ("⛔ %d CONTROLE(S) GARDE(S) PAR RIEN : %s"
                   % (len(nus), " · ".join(nus)) if nus
                   else "⛔ LA SOURCE NE S'ANALYSE PAS A L'AST — la population "
                        "de ce controle est INCONNUE, ⛔ pas vide"))
    finally:
        # ⛔ ⛔ ON N'AVALE PAS L'ECHEC : un staging abandonne sous le TEMP de
        #    Windows ⛔ ne se dirait NULLE PART avec `ignore_errors=True`.
        for d in (stage, stage_lhm):
            if d is None:
                continue
            try:
                shutil.rmtree(d)
            except OSError as exc:                          # pragma: no cover
                print("⚠️ STAGING ⛔ NON SUPPRIME : %s — %s: %s. Il reste sous "
                      "le TEMP de Windows, et il faut le retirer a la main."
                      % (d, type(exc).__name__, exc))

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : que la TOUR REELLE refuse.")
    print("   Elle ⛔ n'installe pas LHM, ⛔ ne pose aucune tache planifiee et")
    print("   ⛔ n'ouvre aucun navigateur. La tour reelle, sa tache et la course")
    print("   au logon sont NOMMEES au ledger — et ce qui se juge A L'ŒIL y")
    print("   reste : `AC8.3.1` et `AC8.3.3` ⛔ ne se ferment PAS ici.")
    return bilan(1 if dn_gates.ko_total[0] else 0, prevus=CONTROLES_PREVUS)


if __name__ == "__main__":
    sys.exit(main())

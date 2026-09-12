#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn7-6 — LA PAGE INSTALLE CE QU'ELLE PEUT, ET ELLE **BLOQUE**.

======================= CE QUE CETTE GATE GARDE, ET POURQUOI ================

Trois arbitrages owner du 2026-09-10, verbatim, ⛔ aucun deduit :
  1. « elle install dans la mesure du posible sinon elle expose » — ce qui
     AMENDE le fil conducteur de l'epic (« `dn7` EXPOSE, ⛔ elle ne construit
     rien »), vrai de `dn7-1` a `dn7-3`, FAUX a partir d'ici ;
  2. « bloquant veu dire btn grise si conditions non remplis » — ⛔ pas un
     avertissement qu'on peut ignorer ;
  3. « ok pour le nouveau verbe qui lance l'agent ».

Et le trou le plus cher etait NEUF : depuis `dn7-5`, LibreHardwareMonitor est
un prerequis DUR de l'agent (`tools/dn_agent_tour.ps1`, `exit 12`). Un inconnu
pouvait donc poser l'agent et decouvrir AU PROCHAIN LOGON, sans une ligne sur
disque, qu'il refuse de demarrer — alors que la page SAIT que LHM est absent
(cle `lhm` de `etat_machine()`) et ⛔ ne s'en servait pour RIEN.

🔴 **AMENDE LE 2026-09-12 (`dn4-48`), ET LE PARAGRAPHE CI-DESSUS RESTE** : il
   dit ce qui etait vrai du 2026-09-10 au 2026-09-12, et c'est ce trou-la qui a
   fait ecrire les controles de cette gate. ⛔ **LE PRE-VOL NE REFUSE PLUS** :
   il ATTEND LHM (borne `-AttenteLhm`, 300 s par defaut) puis DEMARRE QUAND
   MEME, champs LHM a « -- ». `12` a change d'emetteur — le verbe `poser`, ⛔
   plus le pre-vol — et de sens : « posee et **VIVANTE**, mais SANS LHM ».
   ⇒ CE QUE CETTE GATE GARDE ⛔ NE CHANGE PAS DE NATURE : la page doit RELAYER
     ce code EN NOMMANT LHM, et `(c20)` le JOUE. Ce qui change est le VERDICT
     qu'elle exige de lui, et il est desormais garde **des deux cotes** : ce
     que `12` doit dire (la moitie VIVANTE) et ce qu'il ⛔ ne doit PLUS dire
     (« RIEN n'a ete pose »).

── LES CONTROLES DU DOSSIER, ET LEUR NUMERO ICI ────────────────────────────

    (a) ⇒ (c1)    (b) ⇒ (c2)    (c) ⇒ (c3)    (d) ⇒ (c4)    (e) ⇒ (c5)
    (f) ⇒ (c6)    (g) ⇒ (c7)    (h) ⇒ (c8)    (i) ⇒ (c9)    (j) ⇒ (c10)
    (k) ⇒ (c11)   (l) ⇒ (c12)   (m) ⇒ (c13)

  Et trois de plus, qui gardent la campagne elle-meme : `(c14)` chaque
  controle est vise par au moins un mutant · `(c15)` chaque cible declaree est
  un controle REEL · `(c16)` `CIBLES` et `MUTANTS` se correspondent.

── 🔴 POURQUOI LE TEMOIN N'EST **PAS VERT**, ET POURQUOI (c3) LE REFUSE ─────

  Le verbatim owner dit « pastilles vertes ». TROIS MESURES, ⛔ aucun
  argument, disent que la teinte n'est pas le levier :
   (i)  `installeur/IDENTITE.md` n'est ⛔ pas une charte : c'est une LISTE
        FERMEE DE SEPT ROLES, chacun RELEVE dans le firmware, et le fichier
        ecrit sa propre regle — « les couleurs ne sont pas inventees ici,
        elles sont relevees la-bas ». ⛔ Aucun des sept n'est vert.
   (ii) Le vert EXISTE dans le firmware et il y est **REJETE, DATE** :
        `0x4ade80`, constat owner A L'ŒIL du 2026-08-25 (`dn4-13`), « ca ne
        se voit pas bien » sur un PCB VERT, remplace par `0x3b82f6`. Ses
        occurrences dans `firmware/` sont TOUTES des annotations de rejet, et
        cette gate le RE-MESURE plutot que de le croire.
   (iii) `dn7-4` a deja tranche la question de FORME sur CETTE page, et par la
        mesure : « l'aplat est une difference de FORME, ⛔ pas de teinte »,
        parce que deux teintes voisines avaient fait lire une position pour
        l'autre A L'OWNER, EN SEANCE.
  ⛔ ET LA PORTE MECANIQUE EST FERMEE ICI : citer `dn_ui.c:912` comme source
     d'un jeton `#4ade80` PASSERAIT `(c18)` de `tools/verif_installeur_dn71.py`
     tout en publiant une valeur ABANDONNEE comme identite vivante. C'est
     « une gate verte sur du code faux », la faute que ce depot a sanctionnee
     quatre fois pendant `dn7-4`. ⇒ `(c3)` refuse les valeurs REJETEES
     NOMMEMENT, et il verifie d'abord qu'elles le sont VRAIMENT.

── 🔴 CE QU'ELLE NE PROUVE PAS, ET C'EST ECRIT PLUTOT QUE TU ────────────────

  **CETTE GATE EST STRUCTURELLE.** Elle ⛔ N'OUVRE AUCUN NAVIGATEUR,
  ⛔ N'INSTALLE RIEN, ⛔ NE POSE AUCUNE TACHE PLANIFIEE et ⛔ NE REGARDE
  AUCUNE PASTILLE. Ce qu'elle tient, c'est que **LE MECANISME EST BRANCHE** :
  le temoin existe et il est alimente, le desarmement passe par UNE fabrique,
  le verbe neuf est le meme sur ses TROIS surfaces, la route neuve est GARDEE,
  et ce qui n'est pas installe est NOMME avec son motif.
  ⛔ Ce qu'elle ⛔ NE PEUT PAS tenir — un bouton reellement grise sous les yeux
     de quelqu'un, un agent reellement active — vit dans `mesures/dn7-6/T2`,
     COTE WINDOWS, et son absence est portee au ledger avec un porteur vivant.
  ⚠️ TROIS de ses VINGT ET UNE assertions FONT TOURNER du produit :
     `(c11)` joue la route neuve contre des en-tetes hostiles, `(c18)` joue
     les trois issues du geste `pip`, et `(c20)` joue les codes de `poser`.
     ⚠️ ANNOTE LE 2026-09-10 : cette ligne disait « UNE SEULE de ses SEIZE
        assertions », et les deux chiffres ont bouge quand la verification a
        ajoute `(c17)`→`(c21)`. ⛔ Les valeurs d'avant sont NOMMEES plutot
        qu'effacees — dans ce depot, le bloc « ce que cette gate ne prouve
        pas » FAIT FOI, et un compte faux y sous-declare la couverture.
     importe `installeur/dn_installeur.py` et appelle `do_POST` sur la route
     neuve avec des en-tetes etrangers. ⛔ Rien n'est lance pour autant : les
     deux gestes que cette route peut declencher sont REMPLACES le temps de
     l'appel, et remis en place ensuite.

Emploi :
    python3 tools/verif_preconditions_dn76.py
    python3 tools/verif_preconditions_dn76.py --liste-mutants
    python3 tools/verif_preconditions_dn76.py --mutant <n>

Sortie : 0 si tout passe · 1 sur un vrai defaut · 2 sur un mutant inconnu ·
         3 si le mutant demande est PERIME (il n'a rien change).
"""

import argparse
import ast
import copy
import importlib.util
import io
import os
import re
import sys
import unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGE = "installeur/index.html"
PY = "installeur/dn_installeur.py"
OUTIL = "tools/dn_agent_tour.ps1"
IDENT = "installeur/IDENTITE.md"
UI = "firmware/desknode/main/dn_ui.c"
FIXES = (PAGE, PY, OUTIL, IDENT, UI)

# ── LES NOMS QUE LE PRODUIT PORTE, ⛔ PAS UN NUMERO DE LIGNE ───────────────
# 🔴 UNE ADRESSE `fichier:ligne` SE PERIME AU PREMIER COMMIT. Tout ce qui suit
#    est un NOM ou un MOTIF ; la gate relit, ⛔ elle ne pointe pas.
NOM_FABRIQUE = "armerGeste"
NOM_TEMOIN = "temoinEtape"
NOM_BLOCMOT = "blocMot"
NOM_TROIS = "troisEtats"
VERBE_NEUF = "poser"
# Les deux verbes que le verbe neuf COMPOSE — ⛔ ni l'un ni l'autre seul :
# `permanence` pose la tache mais son declencheur est `-AtLogOn` SEUL (rien ne
# demarre avant la prochaine session) ; `lancer` demarre l'agent mais ne
# touche PAS au Planificateur (rien ne survit a la session).
VERBES_COMPOSES = ("permanence", "lancer")
# 🔴 LES REGLAGES DE LA TACHE SONT **REEMPLOYES**, ⛔ PAS RECOPIES — et c'est
#    ce qui tient `NFR7.5` PAR CONSTRUCTION plutot que par discipline : le
#    verbe neuf herite de `-RunLevel Limited` avec le bloc qu'il invoque, et
#    la garde vivante du meme fichier (`RunLevel != Limited ⇒ exit 9`)
#    rougirait si quelqu'un l'elevait.
REGLAGES_TACHE = ("-RunLevel", "-AtLogOn", "-RestartCount", "-RestartInterval")
# Le code de la DEMI-REUSSITE : la permanence est posee ET verifiee, l'agent
# n'a pas demarre. ⛔ Ni un succes, ni un echec total : les deux seraient FAUX.
# 🔬 MESURE le 2026-09-10 : l'outil emploie 0,3,4,5,6,7,8,9,10,11,12 ; `1` et
#    `2` collisionnent avec PowerShell et `cmd`, et `4` porte DEUX sens selon
#    le verbe. ⇒ `13`.
CODE_DEMI = "13"

# ── LA ROUTE NEUVE, ET CELLE QUI ⛔ N'EXISTE PAS ──────────────────────────
ROUTE_DEPS = "/api/dependances"
GESTE_PIP = "GESTE_DEPENDANCES"
# 🔴 LE GESTE DE LHM ⛔ N'EST PAS EXECUTABLE PAR CETTE PAGE, ET C'EST MESURE :
#    `tools/dn_lhm_tour.ps1` ECRIT LUI-MEME que sans elevation « -Poser et
#    -Permanence NE POURRONT PAS agir », et sa tache est elevee. Le seul
#    chemin d'elevation depuis l'installeur est le jeton n.7 de
#    `MOTIFS_ELEVATION`, interdit dans `installeur/` par `(c4)` de `dn7-1` ET
#    par `(c18)` de `dn7-2`. ⇒ la commande reste A RECOPIER, et la page dit
#    POURQUOI — ⚠️ EN PARAPHRASE : les sept jetons, eux, ⛔ ne sont pas libres.
CLE_LHM = "GESTE_LHM"

# ── LES BOUTONS QUE LES PRECONDITIONS DU WORKFLOW COMMANDENT ──────────────
# ⚠️ CETTE LISTE EST **FERMEE**, ET SON PERIMETRE EST ECRIT PLUTOT QUE
#    SUPPOSE. `b-stop` et `b-retirer` ⛔ N'Y SONT PAS : ils sont desarmes par
#    l'ABSENCE DE L'OUTIL ou par une machine qui n'a pas repondu au
#    planificateur — ⛔ pas par une precondition du workflow —, et ce chemin-la
#    est garde par `(c15)`/`(c16)` de `dn7-1`. Ce que `(c4)` tient ici, c'est
#    que les gestes NEUFS et celui de la langue passent par UNE fabrique
#    plutot que par des `.disabled =` disperses (⚠️ 17 recenses le 2026-09-10).
GESTES_PILOTES = ("b-langue-poser", "b-deps", "b-agent-poser")
SUFFIXE_RAISON = "-raison"

# ── LE VOCABULAIRE D'ETAT, ET LA FORME QUI LE PORTE ───────────────────────
# 🎯 IL EST DEJA CELUI DE LA DALLE : `W_COL_REELLE` / `W_COL_SIMULEE` /
#    `W_COL_ABSENTE` (`firmware/desknode/main/dn_widget.c`), choisies par un
#    `switch` a TROIS branches — miroir exact de `troisEtats()`.
SELECTEURS_DN76 = (".val.etat-prete", ".val.etat-bloquee", ".val.etat-su-non")
PROPS_COULEUR = ("background", "background-color", "border-color", "color")

# 🔴 LE VERT **REJETE** DU FIRMWARE. ⛔ Il n'est pas ecrit ici comme une
#    preference : la gate ROUVRE le firmware, exige d'y trouver cette valeur,
#    et exige que CHACUNE de ses occurrences porte une marque de REJET. Le
#    jour ou quelqu'un la remet en service, `(c3)` le dira — ⛔ il ne se
#    contentera pas de refuser un litteral dans la page.
VERT_REJETE = "0x4ade80"
MARQUES_REJET = ("~~", "mal lisible", "ne se voit pas bien", "etait", "était")
JETONS_ATTENDUS = 7

RE_STYLE = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
RE_NOM_JETON = re.compile(r"var\(\s*(--dn-[\w-]+)\s*\)")
RE_JETON_DECLARE = re.compile(r"^\s*(--dn-[\w-]+)\s*:", re.M)
RE_CHAMPS = re.compile(r"var CHAMPS = \[(.*?)\];", re.S)
RE_TABLE_MOTS = re.compile(r"var MOTS = \{(.*?)\n\};", re.S)
RE_CLE_MOTS = re.compile(r'^\s{2}"([^"]+)"\s*:\s*\[', re.M)
RE_VALIDATESET = re.compile(r"\[ValidateSet\(([^)]*)\)\]")
RE_VERBES_PY = re.compile(r"^VERBES = \(([^)]*)\)", re.M)
# ⚠️ LARGE, ⛔ PAS ANCRE EN FIN DE LIGNE : l'outil ecrit aussi `; exit 3 }` en
#    fin d'instruction, et un motif ancre le raterait — donc il declarerait
#    `3` « code libre » alors qu'il sert deja.
RE_EXIT = re.compile(r"\bexit\s+(\d+)\b")
RE_JETON_IDENT = re.compile(r"^\|\s*`(--dn-[\w-]+)`\s*\|", re.M)

# Le vocabulaire de l'elevation — RECIPROQUE LOCALE de `(c4)` de
# `tools/verif_installeur_dn71.py`, PORTEE SUR `tools/dn_agent_tour.ps1`, que
# `(c4)` (rayon : `installeur/`) et `(c18)` de `dn7-2` (rayon : page, py, bat)
# ⛔ NE BALAIENT NI L'UN NI L'AUTRE. ⛔ Ces motifs ne vivent QUE dans les
# gates : les citer dans un fichier garde le ferait rougir sur du contenu
# JUSTE, et c'est pour ca que le code livre explique l'absence d'elevation
# SANS nommer ces jetons.
MOTIFS_ELEVATION = (
    ("runas", re.compile(r"\brunas\b", re.I)),
    ("RunAsAdministrator", re.compile(r"runasadministrator", re.I)),
    ("RunLevel Highest", re.compile(r"runlevel\s*=?\s*['\"]?highest", re.I)),
    ("requestedExecutionLevel", re.compile(r"requestedexecutionlevel", re.I)),
    ("requireAdministrator", re.compile(r"requireadministrator", re.I)),
    ("ShellExecute + elevation", re.compile(r"shellexecute\w*", re.I)),
    ("Start-Process -Verb", re.compile(r"start-process[^\n]{0,80}-verb", re.I)),
)

# Ce que la page doit ECRIRE de ce qu'elle ⛔ n'installe PAS. ⚠️ Le motif de
# LHM est exige EN PARAPHRASE, ⛔ pas avec un jeton d'elevation.
A_LIEN_PYTHON = "https://www.python.org/downloads/windows/"
A_MOTIF_LHM = ("administrator rights", "droits administrateur")
A_MOTIF_PYTHON = ("without it this page does not exist",
                  "sans lui cette page n'existe pas")

LARGEUR_LIBELLE = 58

ok_total = [0]
ko_total = [0]
ids_emis = []

MUTANTS = {}                      # ⛔ AU NIVEAU MODULE — sinon `--liste-mutants`
CIBLES = {}                       # ⛔ AU NIVEAU MODULE — matiere de (c14)

MUTANTS[1] = ("retire le temoin d'UNE etape du workflow ⇒ trois "
              "etapes portent leur etat, la quatrieme ⛔ non")
CIBLES[1] = ("c1",)
MUTANTS[2] = ("sort un temoin de `CHAMPS` ⇒ il reste sur `…` POUR "
              "TOUJOURS quand le serveur se tait")
CIBLES[2] = ("c1",)
MUTANTS[3] = ("plante un `#rrggbb` dans une regle d'etat ⇒ une "
              "couleur qui echappe a l'identite declaree")
CIBLES[3] = ("c2",)
MUTANTS[4] = ("ecrit un NOM de jeton qui n'existe pas ⇒ l'aplat "
              "disparait EN SILENCE, et aucun `#rrggbb` ne bouge")
CIBLES[4] = ("c2",)
MUTANTS[5] = ("fait entrer le VERT REJETE par la porte mecanique ⇒ "
              "une valeur abandonnee publiee comme identite vivante")
CIBLES[5] = ("c3",)
MUTANTS[6] = ("efface la marque de REJET du vert dans le firmware ⇒ "
              "il redevient une source citable, et rien ne le dit")
CIBLES[6] = ("c3",)
MUTANTS[7] = ("desarme un geste HORS de la fabrique ⇒ le motif ⛔ "
              "n'est ecrit nulle part, et 17 sites redeviennent 18")
CIBLES[7] = ("c4",)
MUTANTS[8] = ("passe a la fabrique une cle de raison qui n'est PAS "
              "dans la table ⇒ le nom de la cle s'affiche a l'ecran")
CIBLES[8] = ("c4",)
MUTANTS[9] = ("fait ecrire la raison en PROSE NUE au lieu de la "
              "fabrique ⇒ un ilot que la bascule ne touche pas")
CIBLES[9] = ("c5",)
MUTANTS[10] = ("retire le verbe neuf du `[ValidateSet]` de l'outil ⇒ "
               "la page poste un verbe que la machine refusera")
CIBLES[10] = ("c6",)
MUTANTS[11] = ("retire le verbe neuf de `VERBES` ⇒ le serveur refuse "
               "en `2` un verbe que l'outil accepte pourtant")
CIBLES[11] = ("c6",)
MUTANTS[12] = ("fait tomber le demarrage du verbe neuf ⇒ « activer » "
               "pose une tache et ⛔ ne demarre RIEN aujourd'hui")
CIBLES[12] = ("c7",)
MUTANTS[13] = ("RECOPIE un reglage de tache dans le verbe neuf ⇒ "
               "deux sources de verite, et `NFR7.5` par discipline")
CIBLES[13] = ("c7",)
MUTANTS[14] = ("rend la demi-reussite en `0` ⇒ « active » annonce sur "
               "un agent qui n'a jamais demarre")
CIBLES[14] = ("c8",)
MUTANTS[15] = ("reemploie le code de la demi-reussite AILLEURS ⇒ deux "
               "issues differentes rendent le MEME code")
CIBLES[15] = ("c8",)
MUTANTS[16] = ("plante une ELEVATION dans le bloc du verbe neuf ⇒ "
               "hors du rayon de `(c4)` et de `(c18)`, personne ne voit")
CIBLES[16] = ("c9",)
MUTANTS[17] = ("ouvre une route qui EXECUTE le geste de LHM ⇒ la page "
               "promet un geste qu'elle ⛔ ne peut pas faire agir")
CIBLES[17] = ("c10",)
MUTANTS[18] = ("sort la route neuve de `do_POST` ⇒ elle cesse "
               "d'heriter de la garde, et rien ne la re-code")
CIBLES[18] = ("c11",)
MUTANTS[19] = ("ecrit une SECONDE chaine `pip` parallele ⇒ le geste "
               "joue cesse d'etre le geste publie")
CIBLES[19] = ("c12",)
MUTANTS[20] = ("efface le motif de ce que la page ⛔ n'installe PAS ⇒ "
               "un ecart sans motif se lit comme un oubli")
CIBLES[20] = ("c13",)
MUTANTS[21] = ("vide la cible d'un mutant ⇒ un controle garde par "
               "ZERO mutant, et rien ne le dit")
CIBLES[21] = ("c14",)
MUTANTS[22] = ("declare dans `CIBLES` un controle INEXISTANT ⇒ une "
               "cible PERIMEE que « N rouges » ne voit pas")
CIBLES[22] = ("c15",)
MUTANTS[23] = ("declare une cible pour un mutant qui N'EXISTE PAS")
CIBLES[23] = ("c16",)
MUTANTS[24] = ("declare un mutant dont le CORPS LEVE ⇒ un mutant "
               "MORT, qui doit se rendre en KO et ⛔ pas en trace")
CIBLES[24] = ("c0",)
MUTANTS[25] = ("replante une SORTIE ANTICIPEE NON DECLAREE ⇒ le "
               "bilan sort sur une population RETRECIE")
CIBLES[25] = ("z",)
MUTANTS[26] = ("referme le commentaire du temoin TROP TOT ⇒ un "
               "`*/` orphelin, et le navigateur AVALE la regle suivante")
CIBLES[26] = ("c17",)
MUTANTS[27] = ("annonce un SUCCES sur un `pip` INDISPONIBLE ⇒ un "
               "geste qui n'a pas eu lieu passe pour fait")
CIBLES[27] = ("c18",)
MUTANTS[28] = ("fait poster la page sur une AUTRE route que celle "
               "que le serveur sert ⇒ 404 au lieu d'une installation")
CIBLES[28] = ("c19",)
MUTANTS[29] = ("aplatit la demi-reussite `13` de `poser` en refus nu "
               "⇒ la page CONTREDIT sa propre sortie brute")
CIBLES[29] = ("c20",)
# 🔴 dn4-48 — IL REPLANTE LE SENS PERIME DE `12`, ⛔ il ne debranche rien :
#    la page redit « RIEN n'a ete pose » sur un geste qui a POSE la tache ET
#    demarre l'agent. C'est la forme EXACTE sous laquelle la faute survivrait :
#    un verdict qu'on oublie de reecrire quand le produit change de sens.
MUTANTS[31] = ("redonne a `12` le verdict PERIME « RIEN n'a "
               "ete pose » ⇒ un ECHEC annonce sur un succes")
CIBLES[31] = ("c20",)
# 🔴 dn4-48 — IL **REPLANTE** LE GRISAGE SUR LHM, ⛔ il ne debranche rien :
#    la page redevient incapable d'activer l'agent sur une tour dont LHM ne
#    repond pas, alors que le pre-vol, lui, l'ATTEND puis DEMARRE. C'est la
#    forme EXACTE sous laquelle la faute reviendrait — une precondition qu'on
#    oublie de retirer quand le refus qu'elle relayait disparait.
MUTANTS[32] = ("REPLANTE le grisage de l'activation sur LHM ⇒ la "
               "page refuse ce que l'outil permet")
CIBLES[32] = ("c22",)
MUTANTS[30] = ("INVERSE la polarite de la fabrique ⇒ tous les "
               "gestes grises A L'ENVERS")
CIBLES[30] = ("c21",)

# ⚠️ LE COMPTE DU CHEMIN NORMAL : 1 pre-vol + un controle par mutant + les 16
#    controles numerotes. Il se PERIME si on ajoute un controle sans le mettre
#    a jour — et c'est voulu : c'est ce qui rend (z) FALSIFIABLE.
CONTROLES_PREVUS = 1 + len(MUTANTS) + 22

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


# ═══════════════════════ LIRE, ⛔ PAS POINTER ══════════════════════════════

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


def sans_commentaires(js):
    """Le script SANS ses commentaires — ⛔ ce qui s'execute, pas ce qui
    l'explique. Un mutant pourrait sinon faire rougir la gate en posant un
    litteral dans un commentaire, et elle prouverait un `grep`."""
    js = re.sub(r"/\*.*?\*/", " ", js or "", flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", " ", js)


def style_de(page):
    """Les feuilles de style, **SANS LEURS COMMENTAIRES** — meme motif : un
    leurre dans un `/* … */` suffirait a reverdir la gate (mesure `dn7-4`)."""
    brut = "\n".join(RE_STYLE.findall(page or ""))
    return re.sub(r"/\*.*?\*/", " ", brut, flags=re.S)


def corps_fonction(js, nom):
    """Le CORPS d'une fonction du script, ⛔ pas le script entier."""
    m = re.search(r"function %s\([^)]*\) \{(.*?)\n\}" % re.escape(nom),
                  js or "", re.S)
    return m.group(1) if m else ""


def signature(js, nom):
    """Les PARAMETRES declares d'une fonction, dans l'ordre. Vide si absente."""
    m = re.search(r"function %s\(([^)]*)\)" % re.escape(nom), js or "")
    if not m:
        return []
    return [p.strip() for p in m.group(1).split(",") if p.strip()]


def bloc_regle(style, selecteur):
    """Le CORPS d'une regle CSS, ⛔ pas le voisinage. Une regle qui ne se
    referme pas rend **VIDE**."""
    m = re.search(re.escape(selecteur) + r"\s*\{([^}]*)\}", style or "")
    return m.group(1) if m else ""


def declarations(corps):
    """Les declarations d'une regle, normalisees en `propriete: valeur`."""
    out = []
    for d in (corps or "").split(";"):
        if ":" not in d:
            continue
        p, v = d.split(":", 1)
        out.append((p.strip().lower(), re.sub(r"\s+", " ", v.strip().lower())))
    return out


def appels(corps, nom):
    """Les ARGUMENTS de chaque appel de `nom(`, decoupes aux virgules de
    PREMIER niveau (guillemets et parentheses suivis).

    ⚠️ Un appel dont la parenthese ne se referme pas est IGNORE — ⛔ jamais
       « tout ce qui suit ». Et ⛔ UN APPEL N'EST PAS UNE FIN DE NOM :
       `xarmerGeste(` n'est pas `armerGeste(`."""
    out = []
    i = 0
    motif = nom + "("
    corps = corps or ""
    while True:
        j = corps.find(motif, i)
        if j < 0:
            return out
        if j and (corps[j - 1].isalnum() or corps[j - 1] in "_$."):
            i = j + len(motif)
            continue
        k = j + len(motif)
        prof, args, cour, quote = 1, [], "", ""
        while k < len(corps):
            c = corps[k]
            if quote:
                if c == "\\":
                    cour += corps[k:k + 2]
                    k += 2
                    continue
                if c == quote:
                    quote = ""
            elif c in "\"'":
                quote = c
            elif c in "([{":
                prof += 1
            elif c in ")]}":
                prof -= 1
                if prof == 0:
                    break
            elif c == "," and prof == 1:
                args.append(cour.strip())
                cour = ""
                k += 1
                continue
            cour += c
            k += 1
        if k >= len(corps):
            return out                    # parenthese non refermee ⇒ IGNORE
        if cour.strip() or args:
            args.append(cour.strip())
        out.append((args, j))
        i = k + 1


def litteral(arg):
    """La valeur d'un argument LITTERAL de chaine, ou `None`."""
    a = (arg or "").strip()
    if len(a) >= 2 and a[0] == a[-1] and a[0] in "\"'":
        return a[1:-1]
    return None


def li_de_premier_niveau(page):
    """Les `<li>` de PREMIER NIVEAU sous `<ol class="gestes">`.

    🔴 LA PROFONDEUR EST SUIVIE, ⛔ PAS SUPPOSEE : le geste 2 porte des listes
       imbriquees, et compter les `<li` a plat en trouverait plus que QUATRE —
       un controle qui juge la mauvaise population n'est pas un controle."""
    ol = region(page, '<ol class="gestes">', "\n    </ol>")
    if not ol:
        return []
    out = []
    prof = 0
    debut = 0
    for m in re.finditer(r"</?li\b", ol):
        if m.group(0) == "<li":
            if prof == 0:
                debut = m.start()
            prof += 1
        else:
            prof -= 1
            if prof == 0:
                out.append(ol[debut:m.end()])
    return out


def champs_declares(js):
    """Les identifiants de `CHAMPS`, lus dans le script."""
    m = RE_CHAMPS.search(js or "")
    if not m:
        return []
    return re.findall(r'"([^"]+)"', m.group(1))


def cles_de_mots(js):
    """Les cles de la table `MOTS`, lues dans le script."""
    m = RE_TABLE_MOTS.search(js or "")
    if not m:
        return set()
    return set(RE_CLE_MOTS.findall(m.group(1)))


def bloc_verbe(ps1, verbe):
    """Le bloc d'un verbe du `switch`, ⛔ pas le fichier.

    ⚠️ LA BORNE EST UNE ACCOLADE **EN COLONNE 0** : les blocs de ce fichier se
       referment ainsi, et une borne plus lache avalerait le verbe suivant."""
    return region(ps1, "'%s' {" % verbe, "\n}\n")


# ═══════════ (a)…(c) — CHAQUE ETAPE PORTE SON ETAT, ET IL N'EST PAS VERT ═══

def chaque_etape_porte_son_temoin(page, js):
    """(a) Les QUATRE `<li>` portent-ils un temoin, et son `id` est-il dans
    `CHAMPS` ?

    🔴 LE BUG SILENCIEUX QUE CE CONTROLE FERME : un `id` oublie dans `CHAMPS`
       reste sur ses points de suspension POUR TOUJOURS quand le serveur se
       tait — ce qui se lit « en cours » alors que c'est fini."""
    lis = li_de_premier_niveau(page)
    if len(lis) != 4:
        return False, ("%d `<li>` de premier niveau sous la liste des gestes "
                       "(⛔ QUATRE attendus)" % len(lis))
    champs = champs_declares(js)
    if not champs:
        return False, "`CHAMPS` ne se lit pas dans le script"
    sans = []
    hors = []
    for i, li in enumerate(lis, 1):
        ids = re.findall(r'class="val" id="([^"]+)"', li)
        if not ids:
            sans.append("geste %d" % i)
            continue
        for x in ids:
            if x not in champs:
                hors.append("geste %d ⇒ %s" % (i, x))
    if sans:
        return False, ("etape(s) SANS temoin d'etat : %s" % " · ".join(sans))
    if hors:
        return False, ("temoin(s) HORS de `CHAMPS` : %s — il resterait sur "
                       "`…` pour toujours" % " · ".join(hors))
    return True, "4 etapes, 4 temoins, tous dans `CHAMPS` (%d)" % len(champs)


def le_temoin_se_peint_dans_les_jetons(style):
    """(b) Les regles d'etat n'emploient-elles QUE des `var(--dn-*)` declares ?

    🔴 RECIPROQUE LOCALE DE `(c13)` DE `dn7-4`, QUI ⛔ NE VOIT QUE QUATRE
       SELECTEURS FIXES : une regle d'etat NEUVE lui echappe entierement.
    ⚠️ Et le NOM du jeton est confronte a `:root` : `(c19)` de `dn7-1` ne
       compare que des litteraux `#rrggbb` et ⛔ ne dit RIEN d'un nom de
       propriete personnalisee — une coquille fait disparaitre l'aplat EN
       SILENCE."""
    declares = set(RE_JETON_DECLARE.findall(style or ""))
    if not declares:
        return False, "aucun jeton `--dn-*` declare dans `:root`"
    absentes, nues, inconnus = [], [], []
    jetons = 0
    for s in SELECTEURS_DN76:
        corps = bloc_regle(style, s)
        if not corps:
            absentes.append(s)
            continue
        for p, v in declarations(corps):
            if p not in PROPS_COULEUR:
                continue
            m = RE_NOM_JETON.search(v)
            if not m:
                nues.append("%s ⇒ %s: %s" % (s, p, v))
                continue
            jetons += 1
            if m.group(1) not in declares:
                inconnus.append("%s ⇒ %s" % (s, m.group(1)))
    if absentes:
        return False, "regle(s) ABSENTE(S) : %s — ⛔ rien a juger" % (
            " · ".join(absentes))
    if nues:
        return False, "valeur(s) HORS jeton : %s" % " · ".join(nues[:2])
    if inconnus:
        return False, ("jeton(s) ⛔ NON DECLARE(S) dans `:root` : %s"
                       % " · ".join(inconnus[:2]))
    return True, "%d regles, %d valeur(s), toutes en jetons declares" % (
        len(SELECTEURS_DN76), jetons)


def les_regles_sont_atteignables(page):
    """(c17) Les regles d'etat sont-elles ATTEIGNABLES PAR UN NAVIGATEUR ?

    🔴 CE CONTROLE EXISTE PARCE QUE LE DEFAUT A ETE COMMIS, ET QUE QUATRE
       GATES SONT RESTEES VERTES DESSUS (mesure du 2026-09-10, `dn7-6`) : le
       commentaire du temoin se refermait TROP TOT, laissant quatorze lignes
       de prose HORS commentaire et un `*/` ORPHELIN derriere elles. Pour un
       navigateur, cette prose devient le PREAMBULE d'un selecteur, et la
       premiere regle qui suit — `.val.etat-prete`, c'est-a-dire l'etat
       « tout va bien » que l'owner voulait VOIR — est AVALEE.
    ⚠️ ET VOICI POURQUOI `(c2)` NE POUVAIT PAS LE VOIR : `style_de()` retire
       les commentaires par une EXPRESSION REGULIERE, c'est-a-dire COMME ON VOUDRAIT
       qu'ils soient ecrits. Un `*/` orphelin ne le derange pas : la regle
       reste dans le texte, `(c2)` la trouve, la juge bien formee, et elle
       est VRAIMENT bien formee — elle est juste INATTEIGNABLE.
       ⇒ un controle qui lit du TEXTE ⛔ ne dit RIEN de ce qu'un PARSEUR
         atteint. Celui-ci balaie les delimiteurs DE GAUCHE A DROITE, comme un
         tokenizer, ⛔ pas avec une expression reguliere.
    ⛔ ET IL NE SE CONTENTE PAS DU BALAYAGE : il verifie AUSSI que chacune des
       regles survit au retrait des commentaires — un controle qui ne
       regarderait que les delimiteurs passerait a cote d'une regle ecrite,
       par megarde, DANS un commentaire."""
    brut = "\n".join(RE_STYLE.findall(page or ""))
    if not brut:
        return False, "⛔ aucun bloc `<style>` — ⛔ rien a juger"
    pos, orphelins, jamais = 0, [], []
    while True:
        a = brut.find("/*", pos)
        b = brut.find("*/", pos)
        if a == -1 and b == -1:
            break
        if a != -1 and (b == -1 or a < b):
            f = brut.find("*/", a + 2)
            if f == -1:
                jamais.append(brut[:a].count("\n") + 1)
                break
            pos = f + 2
        else:
            orphelins.append(brut[:b].count("\n") + 1)
            pos = b + 2
    if orphelins:
        return False, ("`*/` ORPHELIN(S) dans `<style>`, ligne(s) relative(s) "
                       "%s — la regle qui suit est AVALEE"
                       % " · ".join(str(x) for x in orphelins[:3]))
    if jamais:
        return False, ("commentaire JAMAIS ferme, ligne relative %d — tout ce "
                       "qui suit disparait" % jamais[0])
    nu = re.sub(r"/\*.*?\*/", " ", brut, flags=re.S)
    avalees = [s for s in SELECTEURS_DN76 if s not in nu]
    if avalees:
        return False, ("regle(s) ecrite(s) DANS un commentaire : %s"
                       % " · ".join(avalees))
    return True, ("%d delimiteur(s) apparie(s), %d regle(s) atteignable(s)"
                  % (brut.count("/*"), len(SELECTEURS_DN76)))


def aucun_vert_rejete(page, ident, ui):
    """(c) ⛔ AUCUN VERT — et le rejet est **RE-MESURE**, ⛔ pas croyable.

    🔴 TROIS FAITS, DANS CET ORDRE :
       1. la valeur EXISTE dans le firmware (sinon la refuser dans la page ne
          garderait rien — un controle qui passe A VIDE) ;
       2. CHACUNE de ses occurrences porte une marque de REJET (le jour ou
          quelqu'un la remet en service, ce controle le dit) ;
       3. la page ⛔ ne la porte PAS, et `IDENTITE.md` compte TOUJOURS SEPT
          jetons — ⛔ pas huit.
    ⛔ LA PORTE MECANIQUE : citer `dn_ui.c:912` comme source d'un jeton
       `#4ade80` PASSERAIT `(c18)` de `dn7-1`, qui verifie seulement que la
       valeur EST a la ligne citee. Elle y est — dans un commentaire qui dit
       qu'on l'a ABANDONNEE."""
    lignes = [l for l in (ui or "").split("\n") if VERT_REJETE in l]
    if not lignes:
        return False, ("`%s` est INTROUVABLE dans le firmware : ce controle "
                       "passerait A VIDE" % VERT_REJETE)
    vivantes = [l.strip()[:60] for l in lignes
                if not any(x in l for x in MARQUES_REJET)]
    if vivantes:
        return False, ("`%s` a %d occurrence(s) SANS marque de rejet : %s — "
                       "elle redevient une source citable"
                       % (VERT_REJETE, len(vivantes), vivantes[0]))
    porte = VERT_REJETE.replace("0x", "#")
    if porte in (page or "").lower():
        return False, ("la page PORTE `%s` — une valeur ABANDONNEE publiee "
                       "comme identite vivante" % porte)
    jetons = RE_JETON_IDENT.findall(ident or "")
    if len(jetons) != JETONS_ATTENDUS:
        return False, ("`%s` declare %d jeton(s) au lieu de %d"
                       % (IDENT, len(jetons), JETONS_ATTENDUS))
    return True, ("%d occurrence(s) de `%s`, toutes en annotation de REJET ; "
                  "%d jetons, ⛔ aucun vert"
                  % (len(lignes), VERT_REJETE, len(jetons)))


# ═══════════ (d)(e) — LE DESARMEMENT PASSE PAR UNE FABRIQUE ════════════════

def le_desarmement_passe_par_une_fabrique(js):
    """(d) Les gestes du workflow passent-ils TOUS par LA fabrique ?

    ⚠️ CE QUE CE CONTROLE ⛔ NE PRETEND PAS : il ⛔ ne juge PAS les 15
       assignations `.disabled =` que la page portait deja (⚠️ « 17 » etait
       un compte de REFERENCES, ⛔ pas d'assignations — corrige le 2026-09-10) — `b-stop` et
       `b-retirer` sont desarmes par l'ABSENCE DE L'OUTIL, ⛔ pas par une
       precondition du workflow. Ce qu'il tient, c'est que les gestes NEUFS et
       celui de la langue ⛔ n'en ajoutent AUCUNE."""
    corps = corps_fonction(js, NOM_FABRIQUE)
    if not corps:
        return False, "`%s` est introuvable" % NOM_FABRIQUE
    cles = cles_de_mots(js)
    if not cles:
        return False, "la table `MOTS` ne se lit pas"
    # ⛔ LA DECLARATION N'EST PAS UN APPEL : on la masque avant de compter.
    sans_decl = re.sub(r"function\s+%s\(" % re.escape(NOM_FABRIQUE),
                       "function _decl_(", js or "", count=1)
    tous = [a for a, _p in appels(sans_decl, NOM_FABRIQUE)]
    vus = set()
    mal = []
    for args in tous:
        if len(args) != 3:
            mal.append("%d argument(s)" % len(args))
            continue
        ident = litteral(args[0])
        cle = litteral(args[2])
        if ident is None or ident not in GESTES_PILOTES:
            mal.append("geste ⛔ non declare : %s" % (args[0][:24]))
            continue
        if cle is None or cle not in cles:
            mal.append("%s ⇒ raison ABSENTE de la table : %s"
                       % (ident, args[2][:24]))
            continue
        vus.add(ident)
    if mal:
        return False, "appel(s) fautif(s) : %s" % " · ".join(mal[:2])
    manquants = [g for g in GESTES_PILOTES if g not in vus]
    if manquants:
        return False, ("geste(s) ⛔ JAMAIS armes par la fabrique : %s"
                       % " ".join(manquants))
    # 🔴 ET AUCUN DE CES GESTES N'EST DESARME AILLEURS : une seule fabrique,
    #    ⛔ pas une fabrique PLUS des assignations dispersees.
    disperses = []
    hors_fabrique = (js or "").replace(corps, "\n", 1)
    for m in re.finditer(r"(\w+)\.disabled\s*=", hors_fabrique):
        nom = m.group(1)
        for g in GESTES_PILOTES:
            # `b-langue-poser` ⇒ `bLanguePoser` : la variable porte le meme
            # nom, sans tirets et en casse chameau.
            if nom.lower() == g.replace("-", "").lower():
                disperses.append(nom)
    if disperses:
        return False, ("geste(s) desarme(s) HORS de la fabrique : %s"
                       % " ".join(sorted(set(disperses))))
    return True, ("%d appel(s), %d geste(s) pilotes, ⛔ aucun `.disabled` "
                  "disperse" % (len(tous), len(vus)))


def le_motif_est_ecrit_sous_le_bouton(page, js):
    """(e) A tout geste desarmable correspond-il un bloc de raison, POSE PAR
    UNE FABRIQUE, et place APRES son bouton ?

    ⛔ JAMAIS UNE PROSE NUE : un texte ecrit hors des fabriques bilingues est
       un ilot par construction — la bascule ne le touche pas."""
    corps = corps_fonction(js, NOM_FABRIQUE)
    if not corps:
        return False, "`%s` est introuvable" % NOM_FABRIQUE
    if not appels(corps, NOM_BLOCMOT):
        return False, ("la fabrique ⛔ n'ecrit PAS par `%s` : la raison serait "
                       "une prose nue" % NOM_BLOCMOT)
    manquants, mal_places = [], []
    for g in GESTES_PILOTES:
        a_bouton = 'id="%s"' % g
        a_raison = 'id="%s%s"' % (g, SUFFIXE_RAISON)
        if a_bouton not in page or a_raison not in page:
            manquants.append(g)
            continue
        if page.index(a_raison) < page.index(a_bouton):
            mal_places.append(g)
    if manquants:
        return False, ("geste(s) sans bouton ou sans bloc de raison : %s"
                       % " ".join(manquants))
    if mal_places:
        return False, ("bloc(s) de raison AVANT leur bouton : %s — « sous le "
                       "bouton » est la propriete, ⛔ pas « quelque part »"
                       % " ".join(mal_places))
    return True, ("%d bloc(s) de raison, tous sous leur bouton, tous ecrits "
                  "par `%s`" % (len(GESTES_PILOTES), NOM_BLOCMOT))


# ═══════════ (f)(g)(h)(i) — LE VERBE NEUF ══════════════════════════════════

def le_verbe_bouge_sur_ses_trois_surfaces(ps1, py, js):
    """(f) Le verbe neuf est-il dans le `[ValidateSet]`, dans `VERBES`, ET
    appele par la page ? L'absence de l'UN des trois rougit."""
    m = RE_VALIDATESET.search(ps1 or "")
    if not m:
        return False, "aucun `[ValidateSet]` dans l'outil"
    valides = re.findall(r"'([a-z]+)'", m.group(1))
    mv = RE_VERBES_PY.search(py or "")
    exposes = re.findall(r'"([a-z]+)"', mv.group(1)) if mv else []
    appele = [a for a, _p in appels(js, "jouer")
              if a and litteral(a[0]) == VERBE_NEUF]
    absents = []
    if VERBE_NEUF not in valides:
        absents.append("[ValidateSet] de l'outil")
    if VERBE_NEUF not in exposes:
        absents.append("`VERBES` du serveur")
    if not appele:
        absents.append("l'appel de la page")
    if absents:
        return False, ("`%s` manque a : %s — les trois surfaces bougent "
                       "ENSEMBLE ou rien ne marche"
                       % (VERBE_NEUF, " · ".join(absents)))
    return True, ("`%s` sur ses 3 surfaces : %d verbe(s) valides, %d expose(s)"
                  % (VERBE_NEUF, len(valides), len(exposes)))


def le_verbe_compose(ps1):
    """(g) Le bloc du verbe neuf invoque-t-il la POSE **et** le DEMARRAGE, et
    ⛔ ne redeclare-t-il AUCUN reglage de tache ?

    🔴 C'EST LE TROU MESURE : `permanence` pose la tache mais son declencheur
       est `-AtLogOn` SEUL ⇒ rien ne demarre avant la prochaine session ;
       `lancer` demarre l'agent mais ⛔ ne touche PAS au Planificateur ⇒ rien
       ne survit a la session. Aucun des sept verbes ne fait les deux.
    🔴 ET LE REEMPLOI EST LA PROPRIETE : recopier un reglage ferait DEUX
       sources de verite, et `NFR7.5` reposerait sur une consigne qu'on peut
       oublier plutot que sur le bloc invoque."""
    bloc = bloc_verbe(ps1, VERBE_NEUF)
    if not bloc:
        return False, ("le bloc du verbe `%s` ne se delimite pas dans l'outil"
                       % VERBE_NEUF)
    absents = [v for v in VERBES_COMPOSES
               if not re.search(r"-File\s+\$\w+\s+%s\b" % re.escape(v), bloc)]
    if absents:
        return False, ("le bloc ⛔ n'invoque PAS : %s — une moitie seule ne "
                       "veut ⛔ pas dire « activer »" % " · ".join(absents))
    recopies = [r for r in REGLAGES_TACHE if r in bloc]
    if recopies:
        return False, ("reglage(s) de tache RECOPIE(S) : %s — ils viennent "
                       "AVEC le bloc reemploye" % " ".join(recopies))
    return True, ("il compose %s, et ⛔ il recopie 0 des %d reglages de tache"
                  % (" + ".join(VERBES_COMPOSES), len(REGLAGES_TACHE)))


def le_code_de_demi_succes_est_propre(ps1):
    """(h) `13` est-il le code d'AUCUNE autre sortie, et vit-il DANS le bloc ?

    🔴 LE CONTROLE S'ECRIT **EN PROPRIETE**, ⛔ PAS A LA LETTRE. Ecrire
       « 13 n'apparait nulle part ailleurs » ferait rougir sur un
       `Get-Content -Tail 13` parfaitement JUSTE — et c'est EXACTEMENT le
       piege que `dn7-5` a paye sur `12`. ⇒ on extrait les SORTIES, ⛔ pas les
       nombres.
    ⚠️ ET AUCUNE AUTRE SORTIE NEUVE DANS CE BLOC : tout autre code litteral
       qu'il emploie doit DEJA servir ailleurs dans le fichier, sinon le verbe
       neuf invente un vocabulaire que personne ne documente."""
    bloc = bloc_verbe(ps1, VERBE_NEUF)
    if not bloc:
        return False, "le bloc du verbe neuf ne se delimite pas"
    dans = RE_EXIT.findall(bloc)
    reste = (ps1 or "").replace(bloc, "", 1)
    dehors = RE_EXIT.findall(reste)
    if dans.count(CODE_DEMI) != 1:
        return False, ("le bloc rend `%s` %d fois (⛔ UNE attendue) : %s"
                       % (CODE_DEMI, dans.count(CODE_DEMI), ",".join(dans)))
    if CODE_DEMI in dehors:
        return False, ("`%s` sert DEJA ailleurs dans l'outil — deux issues "
                       "differentes rendraient le MEME code" % CODE_DEMI)
    neufs = sorted({c for c in dans if c != CODE_DEMI} - set(dehors), key=int)
    if neufs:
        return False, ("sortie(s) NEUVE(S) non documentee(s) dans le bloc : %s"
                       % ",".join(neufs))
    return True, ("`%s` unique, DANS le bloc ; les autres sorties du bloc "
                  "(%s) servent deja" % (CODE_DEMI,
                                         ",".join(sorted(set(dans) -
                                                         {CODE_DEMI},
                                                         key=int)) or "—"))


def aucune_elevation_dans_le_verbe(ps1):
    """(i) ⛔ AUCUNE ELEVATION dans le bloc du verbe neuf.

    🔴 RECIPROQUE PORTEE LA OU PERSONNE NE REGARDE : `(c4)` de `dn7-1` ne
       balaie que `installeur/`, et `(c18)` de `dn7-2` que la page, le serveur
       et le `.bat`. `tools/dn_agent_tour.ps1` est HORS des deux — la
       contrainte « aucune elevation » y tenait par le CONTRAT, ⛔ pas par une
       gate."""
    bloc = bloc_verbe(ps1, VERBE_NEUF)
    if not bloc:
        return False, "le bloc du verbe neuf ne se delimite pas"
    vus = [nom for nom, mot in MOTIFS_ELEVATION if mot.search(bloc)]
    if vus:
        return False, ("jeton(s) d'elevation dans le bloc : %s — `NFR7.5` dit "
                       "que RIEN de `dn7` n'exige de droits administrateur"
                       % " · ".join(vus))
    return True, "%d motifs cherches, 0 trouve" % len(MOTIFS_ELEVATION)


# ═══════════ (j)(k)(l)(m) — CE QU'ELLE INSTALLE, ET CE QU'ELLE EXPOSE ══════

def pip_executable_lhm_non(py, page):
    """(j) Une route existe pour le geste `pip`, AUCUNE pour celui de LHM, et
    la page ecrit POURQUOI.

    🔴 LA FRONTIERE EST MESUREE, ⛔ PAS CHOISIE : `tools/dn_lhm_tour.ps1`
       ECRIT LUI-MEME que sans elevation « -Poser et -Permanence NE POURRONT
       PAS agir ». Le seul chemin d'elevation depuis l'installeur est interdit
       dans `installeur/` par deux gates. ⇒ la commande reste A RECOPIER."""
    # ⚠️ LE NOM DE LA CONSTANTE EST **DERIVE** DE SA VALEUR, ⛔ pas ecrit ici :
    #    un nom fige se perime au premier renommage, et la gate rougirait sur
    #    une redaction JUSTE.
    m = re.search(r"^(\w+) = \"%s\"" % re.escape(ROUTE_DEPS), py or "", re.M)
    if not m:
        return False, ("aucune route `%s` : le geste `pip` reste a recopier "
                       "alors que la page peut le jouer" % ROUTE_DEPS)
    post = region(py or "", "    def do_POST(self):", "\n\n")
    if m.group(1) not in post and ROUTE_DEPS not in post:
        return False, ("la route `%s` ⛔ n'est PAS servie depuis `do_POST` — "
                       "elle cesserait d'heriter de `_garde()`" % ROUTE_DEPS)
    # ⛔ ET AUCUNE ROUTE NE JOUE LE GESTE DE LHM : on cherche la CONSTANTE du
    #    geste dans le corps du serveur, ⛔ pas son texte dans la prose.
    if re.search(r"(_powershell|subprocess\.\w+)\s*\([^)]*%s" % CLE_LHM,
                 py or "", re.S):
        return False, ("une route EXECUTE `%s` — elle ne pourrait RIEN faire "
                       "sans elevation, et la page promettrait un geste qui "
                       "n'agit pas" % CLE_LHM)
    motifs = [x for x in A_MOTIF_LHM if x.lower() in (page or "").lower()]
    if len(motifs) != len(A_MOTIF_LHM):
        return False, ("la page ⛔ n'ecrit PAS pourquoi il n'y a pas de bouton "
                       "pour LHM, dans les DEUX langues (%d/%d)"
                       % (len(motifs), len(A_MOTIF_LHM)))
    return True, ("route `%s` servie depuis `do_POST` · ⛔ aucune route pour "
                  "LHM, et le motif est ecrit" % ROUTE_DEPS)


def la_route_neuve_est_gardee(produit):
    """(k) `Origin` **et** `Host` etrangers rendent-ils **403** sur la route
    NEUVE ?

    🔴 RECIPROQUE DE `(c27)` DE `dn7-1`, QUI ⛔ NE CONNAIT QUE DEUX ROUTES :
       il verifie que `_garde()` ouvre `do_GET` et `do_POST`, et il nomme
       « les 2 verbes » — une gate scopee epinglerait VERT le meme defaut
       ailleurs. ⇒ celui-ci JOUE la troisieme route.
    ⛔ ET RIEN N'EST LANCE, MEME SI LA GARDE EST CASSEE : les deux gestes que
       cette route peut declencher sont REMPLACES le temps de l'appel — un
       controle qui installerait des paquets pour se prouver juste serait
       pire que pas de controle."""
    if produit is None:
        return False, "le produit n'a pas pu etre importe"
    poignee = getattr(produit, "Poignee", None)
    if poignee is None:
        return False, "`Poignee` est introuvable dans le serveur"
    garde = (getattr(produit, "jouer_dependances", None),
             getattr(produit, "jouer_verbe", None))
    if garde[0] is None:
        return False, "`jouer_dependances` est introuvable"
    faux = {"commande": "", "sortie": "", "rc": 0, "rc_pose_par": "le banc",
            "verdict": "⛔ banc"}
    produit.jouer_dependances = lambda *a, **k: dict(faux)
    produit.jouer_verbe = lambda *a, **k: dict(faux)
    try:
        vus = []
        for quoi, entetes in (
                ("Host", {"Host": "attaquant.example:80"}),
                ("Origin", {"Host": "127.0.0.1:4242",
                            "Origin": "http://attaquant.example"})):
            h = object.__new__(poignee)
            h.headers = entetes
            h.path = ROUTE_DEPS
            h.server = type("S", (), {"dn_port": 4242})()
            recu = {}

            def _rep(code, corps, ctype, _r=recu):
                _r["code"] = code
                _r["corps"] = corps

            h._repondre = _rep
            h._json = lambda code, obj, _r=recu: _r.update(code=code, corps=obj)
            try:
                h.do_POST()
            except Exception as exc:                      # noqa: BLE001
                return False, ("`do_POST` LEVE sur la route neuve : %s: %s"
                               % (type(exc).__name__, str(exc)[:60]))
            vus.append((quoi, recu.get("code")))
        mauvais = [q for q, c in vus if c != 403]
        if mauvais:
            return False, ("en-tete(s) etranger(s) ⛔ NON refuse(s) : %s — %s"
                           % (" ".join(mauvais),
                              " · ".join("%s⇒%s" % (q, c) for q, c in vus)))
        return True, "Host ⇒ 403 · Origin ⇒ 403, sur la route NEUVE"
    finally:
        produit.jouer_dependances, produit.jouer_verbe = garde


def le_geste_joue_est_le_geste_publie(py):
    """(l) La commande jouee est-elle DERIVEE de `GESTE_DEPENDANCES` ?

    ⛔ PAS UNE SECONDE CHAINE PARALLELE : deux redactions du meme geste
       divergent, et c'est la page qui publierait l'une en jouant l'autre."""
    if GESTE_PIP not in (py or ""):
        return False, "`%s` est introuvable" % GESTE_PIP
    m = re.search(r"def arguments_dependances\(\):(.*?)\n\ndef ", py or "",
                  re.S)
    if not m:
        return False, ("aucune derivation nommee : la commande jouee ⛔ ne se "
                       "rattache a rien")
    corps = m.group(1)
    if GESTE_PIP not in corps:
        return False, ("la derivation ⛔ ne LIT PAS `%s` — c'est une seconde "
                       "chaine parallele" % GESTE_PIP)
    if "--user" in corps and "install" in corps:
        return False, ("la derivation RECOPIE les mots du geste (`--user`, "
                       "`install`) au lieu de les DERIVER")
    return True, "la commande jouee sort de `%s`, ⛔ d'aucune copie" % GESTE_PIP


def elle_dit_ce_qu_elle_n_installe_pas(page):
    """(m) La page nomme-t-elle LHM **et** Python, chacun avec sa raison ?

    ⛔ UN ECART SANS MOTIF ECRIT SE LIT COMME UN OUBLI, et quelqu'un le
       « reparera ». ⚠️ Le lien Python est exige PARCE QUE la page ⛔ ne peut
       pas en faire une precondition : sans Python, elle N'EXISTE PAS — le
       `.bat` sort avant d'avoir servi quoi que ce soit."""
    absents = []
    if A_LIEN_PYTHON not in (page or ""):
        absents.append("le lien Python")
    for x in A_MOTIF_PYTHON:
        if x.lower() not in (page or "").lower():
            absents.append("le motif Python (%s)" % x[:28])
    for x in A_MOTIF_LHM:
        if x.lower() not in (page or "").lower():
            absents.append("le motif LHM (%s)" % x[:28])
    if absents:
        return False, ("manque(nt) a la page : %s" % " · ".join(absents[:3]))
    # ⛔ ET LE MOTIF DE LHM ⛔ N'EST PAS ECRIT AVEC UN JETON D'ELEVATION : la
    #    paraphrase est libre, les sept jetons ⛔ non.
    vus = [nom for nom, mot in MOTIFS_ELEVATION if mot.search(page or "")]
    if vus:
        return False, ("la page NOMME un jeton d'elevation : %s — la raison "
                       "s'ecrit EN PARAPHRASE" % " · ".join(vus))
    return True, "LHM et Python nommes, chacun avec sa raison, en paraphrase"


# ═══════════════════════════ LE PRODUIT, IMPORTE ═══════════════════════════

def les_trois_issues_du_geste_sont_jouees(produit):
    """(c18) Les TROIS issues de `jouer_dependances()` sont-elles JOUEES ?

    🔴 CE CONTROLE **EXECUTE**, ⛔ il ne lit pas. `(c12)` confronte le TEXTE de
       la derivation au geste publie — c'est utile, et ⛔ ca ne dit RIEN de ce
       que la fonction REND. Les lignes 5 et 6 de la matrice d'E/S de `dn7-6`
       (« clic sur installer » · « `pip` absent chez l'inconnu ») etaient
       jouees par RIEN : c'est cette absence que ce controle ferme.
    ⛔ ET IL N'INSTALLE RIEN : `subprocess.run` est REMPLACE le temps de
       l'appel. Un controle qui telechargerait des paquets pour se prouver
       juste serait pire que pas de controle.
    ⚠️ CE QUI EST EXIGE, ⛔ pas seulement « ca tourne » : un `pip`
       INDISPONIBLE ⛔ n'est PAS une installation qui a echoue — c'est un geste
       qui n'a PAS COMMENCE, et son remede est AILLEURS. Les confondre
       enverrait recliquer un bouton inutile."""
    if produit is None:
        return False, "le produit n'a pas pu etre importe"
    f = getattr(produit, "jouer_dependances", None)
    if f is None:
        return False, "`jouer_dependances` est introuvable"
    marque = getattr(produit, "MARQUE_SANS_PIP", None)
    if not marque:
        return False, "`MARQUE_SANS_PIP` est introuvable"
    vrai = produit.subprocess.run
    delai = produit.subprocess.TimeoutExpired

    class _R(object):
        def __init__(self, o, e, c):
            self.stdout, self.stderr, self.returncode = o, e, c

    cas = {}
    try:
        produit.subprocess.run = lambda *a, **k: _R("ok\n", "", 0)
        cas["succes"] = f()
        produit.subprocess.run = lambda *a, **k: _R("", marque + "\n", 1)
        cas["sans_pip"] = f()

        def _leve(*a, **k):
            raise delai(cmd="pip", timeout=1)
        produit.subprocess.run = _leve
        cas["delai"] = f()
    except Exception as exc:                              # noqa: BLE001
        return False, "l'appel a LEVE : %s" % type(exc).__name__
    finally:
        produit.subprocess.run = vrai

    manques = [k for k in ("succes", "sans_pip", "delai")
               if not isinstance(cas.get(k), dict)]
    if manques:
        return False, "issue(s) sans dictionnaire : %s" % " · ".join(manques)
    # 🔴 LES TROIS VERDICTS SONT **DISTINCTS**, et le `rc` est RELAYE TEL QUEL.
    if cas["succes"].get("rc") != 0:
        return False, "le succes ⛔ ne relaie pas le `rc` de l'outil"
    v = (cas["sans_pip"].get("verdict") or "").lower()
    if "pip" not in v or "pas eu lieu" not in v:
        return False, ("`pip` indisponible ⛔ n'est pas dit comme un geste qui "
                       "n'a PAS EU LIEU : %r" % v[:60])
    d = (cas["delai"].get("verdict") or "").lower()
    if "delai" not in d and "inconnu" not in d:
        return False, "le delai depasse ⛔ n'est pas distingue : %r" % d[:60]
    verdicts = {k: (cas[k].get("verdict") or "") for k in cas}
    if len(set(verdicts.values())) != 3:
        return False, "deux issues rendent le MEME verdict"
    return True, "3 issues jouees, 3 verdicts distincts, `rc` relaye tel quel"


def la_route_de_la_page_est_celle_du_serveur(page, produit):
    """(c19) La page POSTE-t-elle sur la route que le serveur SERT ?

    🔴 CE TROU A ETE **DEMONTRE**, ⛔ pas suppose : changer la valeur de
       `ROUTES` cote page en `api/dependance` laissait **HUIT gates vertes**,
       et le seul geste que cette marche fait JOUER a la page postait sur un
       chemin que `do_POST` rend en **404**. `r.json()` rejette, et l'inconnu
       recoit un echec de reseau au lieu d'une installation.
    ⚠️ POURQUOI AUCUN CONTROLE EXISTANT NE POUVAIT LE VOIR : `(c10)` ne lit
       que le Python ; `(c11)` EXECUTE la route, mais l'URL vient de LA GATE,
       ⛔ pas de la page ; `(c6)` verifie que `jouer("poser", …)` est APPELE,
       ⛔ pas ce que l'appel resout. Les deux moities du contrat n'ont jamais
       ete confrontees."""
    if produit is None:
        return False, "le produit n'a pas pu etre importe"
    servie = getattr(produit, "ROUTE_DEPENDANCES", None)
    if not servie:
        return False, "`ROUTE_DEPENDANCES` est introuvable dans le serveur"
    m = re.search(r"var\s+ROUTES\s*=\s*\{([^}]*)\}", page or "")
    if not m:
        return False, "`ROUTES` est introuvable dans la page"
    paires = dict(re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', m.group(1)))
    postee = paires.get("dependances")
    if not postee:
        return False, "`ROUTES` ⛔ ne porte aucune entree `dependances`"
    if postee.lstrip("/") != servie.lstrip("/"):
        return False, ("la page POSTE sur %r et le serveur SERT %r — le geste "
                       "tomberait en 404" % (postee, servie))
    return True, "page %r == serveur %r" % (postee, servie)


def les_codes_de_poser_sont_rendus(produit):
    """(c20) `jouer_verbe("poser")` rend-il la demi-reussite COMME TELLE ?

    🔴 MEME PATRON QUE `jouer_codes()` DE `dn7-2`, ET POUR LA MEME RAISON :
       `stop` a une table de codes NOMMEE parce que ses codes veulent dire des
       choses differentes. `poser` en a une aussi maintenant — sans elle, la
       queue de `jouer_verbe()` rendait `13` comme « le refus remonte TEL
       QUEL », pendant que la sortie BRUTE affichee juste au-dessus disait
       « LA PERMANENCE EST POSEE ET VERIFIEE ». La page se contredisait dans
       le MEME panneau.
    ⚠️ `12` EST JOUE AUSSI : la ligne 9 de la matrice d'E/S demande que la
       page RELAIE ce code EN NOMMANT LHM — ⛔ pas seulement dans la sortie
       brute que personne ne lit.
    🔴 ET DEPUIS LE 2026-09-12 (`dn4-48`), `12` A CHANGE DE SENS — SA
       PROPRIETE « il nomme LHM » SURVIT, SON VERDICT NON. Le pre-vol de
       l'agent ⛔ ne refuse plus : il ATTEND LHM, puis il DEMARRE QUAND MEME.
       `12` a change d'emetteur (le verbe `poser`, ⛔ plus le pre-vol) et il
       veut dire « la permanence est POSEE et l'agent **TOURNE**, mais SANS
       LHM ». ⇒ il ⛔ **ne doit PLUS dire « RIEN n'a ete pose »** : ce serait
       FAUX, et un inconnu qui le lirait irait chercher une panne qui n'existe
       pas — la tache EST posee, l'agent EST vivant, la dalle SE REMPLIT.
       ⚠️ C'est la MEME faute que `13` a deja payee dans ce controle, et elle
          est gardee de la MEME facon : on exige que le verdict NOMME la
          moitie qui a REUSSI, et on INTERDIT le vocabulaire du refus total.
    ⛔ RIEN N'EST LANCE : `_powershell` est REMPLACE le temps des appels."""
    if produit is None:
        return False, "le produit n'a pas pu etre importe"
    f = getattr(produit, "jouer_verbe", None)
    if f is None:
        return False, "`jouer_verbe` est introuvable"
    vrai = produit._powershell
    vus = {}
    try:
        for rc in (0, 13, 12, 99):
            produit._powershell = (
                lambda a, timeout=90, _rc=rc: (_rc, "sortie de banc",
                                               ["powershell", "poser"], None))
            vus[rc] = (f("poser") or {}).get("verdict") or ""
    except Exception as exc:                              # noqa: BLE001
        return False, "l'appel a LEVE : %s" % type(exc).__name__
    finally:
        produit._powershell = vrai
    if len(set(vus.values())) != 4:
        return False, "deux codes de `poser` rendent le MEME verdict"
    v13 = vus[13].lower()
    if "posee" not in v13 or "verifiee" not in v13:
        return False, ("`13` ⛔ ne nomme PAS la moitie qui a REUSSI : %r"
                       % vus[13][:70])
    if "refus remonte" in v13:
        return False, "`13` est rendu comme un REFUS NU — il ⛔ n'en est pas un"
    if "lhm" not in vus[12].lower():
        return False, "`12` ⛔ ne nomme PAS LibreHardwareMonitor"
    # 🔴 dn4-48 — LE NOUVEAU SENS DE `12`, GARDE SUR LES DEUX BORDS : ce
    #    qu'il doit DIRE (la moitie vivante) et ce qu'il ⛔ ne doit PLUS dire
    #    (le refus total). Un seul des deux laisserait passer l'autre.
    # ⚠️ LE VERDICT EST NORMALISE (accents, gras, glyphes) AVANT D'ETRE LU :
    #    la table l'ecrit en francais accentue, et un motif accentue se
    #    perimerait a la premiere reecriture de la phrase.
    v12 = unicodedata.normalize("NFKD", vus[12])
    v12 = "".join(c for c in v12 if not unicodedata.combining(c)).lower()
    v12 = v12.replace("*", "").replace("`", "")
    if "rien n'a ete pose" in v12 or "rien n'a ete fait" in v12:
        return False, ("`12` dit encore « RIEN n'a ete pose » — c'est FAUX "
                       "depuis `dn4-48` : la tache EST posee et l'agent TOURNE")
    if not ("posee" in v12 and ("tourne" in v12 or "vivant" in v12)):
        return False, ("`12` ⛔ ne nomme PAS la moitie VIVANTE (posee + "
                       "l'agent tourne) : %r" % vus[12][:70])
    return True, ("4 codes joues, 4 verdicts distincts, `13` nomme sa moitie, "
                  "`12` nomme LHM ET la moitie VIVANTE")


def la_polarite_de_la_fabrique_est_gardee(js):
    """(c21) La fabrique grise-t-elle bien quand le geste ⛔ N'EST PAS permis ?

    🔴 CE QUE `(c4)` ⛔ NE TIENT PAS, ET C'EST ECRIT PLUTOT QUE TU : il verifie
       que la fabrique EXISTE, que chaque appel porte trois arguments, que
       l'identifiant est pilote et que la cle de raison existe — ⛔ RIEN sur
       le SENS. Une fabrique ecrivant `b.disabled = permis` griserait TOUS les
       gestes A L'ENVERS et `(c4)` resterait vert.
    ⚠️ MESURE DU 2026-09-10 : cette inversion laisse cette gate a `0 KO`. Le
       banc l'attrape — mais par un cas PREEXISTANT, herite de `dn7-3`. La
       propriete etait donc gardee PAR HERITAGE, ⛔ pas par l'instrument que
       cette marche a ecrit pour elle."""
    corps = corps_fonction(js, NOM_FABRIQUE)
    if not corps:
        return False, "`%s` est introuvable" % NOM_FABRIQUE
    m = re.search(r"\.disabled\s*=\s*([^;]+);", corps)
    if not m:
        return False, "la fabrique ⛔ n'ecrit JAMAIS `.disabled`"
    val = m.group(1).strip()
    if val != "!permis":
        return False, ("la fabrique ecrit `.disabled = %s` — attendu "
                       "`!permis` : toute autre forme grise A L'ENVERS ou "
                       "sur autre chose" % val)
    return True, "`.disabled = !permis` — la polarite est ancree"


def lhm_arme_le_geste_avec_son_avertissement(js):
    """(c22) LHM absent ⇒ le geste « activer » S'ARME, ⛔ il ne grise PLUS.

    🔴 POURQUOI CE CONTROLE EXISTE, ET CE QU'IL A COUTE. Jusqu'au 2026-09-12
       la page GRISAIT `b-agent-poser` des que la sonde LHM rendait `false`,
       parce que le pre-vol de `tools/dn_agent_tour.ps1` sortait alors en
       `12`. `dn4-48` a supprime ce refus : le pre-vol ATTEND LHM puis DEMARRE
       QUAND MEME. ⇒ garder le grisage faisait REFUSER A LA PAGE exactement ce
       que la marche existe pour permettre, et le bouton gris relayait un
       refus qui n'existe plus nulle part.
    ⚠️ LA PLACE DANS LA CHAINE EST **LA MOITIE DU CONTROLE**, ⛔ pas un detail
       de style : `port_serie` doit griser AVANT que LHM n'arme. Si LHM
       passait en premier, une tour SANS CARTE et SANS LHM s'armerait, et la
       tache serait posee sur un port qui n'existe pas — le defaut MESURE que
       `raison.agent-sans-port` nomme. ⇒ on lit l'ORDRE des appels, ⛔ pas
       seulement leur presence.
    ⚠️ ET C'EST ICI, ⛔ PAS AU BANC : le recorder de
       `tools/banc_langue_dalle_dn73.mjs` ⛔ n'ecrit AUCUNE cle sur un geste
       ARME (`id + (permis ? " ARME" : " GRISE=" + cle)`). Le cas `lhm-absent`
       y discrimine encore par le bandeau `etat-lhm VU`, mais la RAISON portee
       par le bouton arme ⛔ n'y est gardee par RIEN. Elle l'est ici."""
    corps = corps_fonction(sans_commentaires(js), "rafraichirTemoins")
    if not corps:
        return False, "`rafraichirTemoins` est introuvable"
    # ⚠️ `appels()` rend `(arguments, position)`, et la valeur d'un argument
    #    litteral se lit par `litteral()` — ⛔ pas par un `strip` de
    #    guillemets, qui avalerait aussi ceux d'une expression.
    # (permis, cle) dans l'ORDRE DU SOURCE — c'est l'ordre qui est juge.
    suite = [(args[1].strip(), litteral(args[2]))
             for args, _pos in appels(corps, NOM_FABRIQUE)
             if len(args) >= 3 and litteral(args[0]) == "b-agent-poser"]
    if not suite:
        return False, ("⛔ aucun appel de `%s` sur `b-agent-poser`"
                       % NOM_FABRIQUE)
    lhm = [i for i, (permis, cle) in enumerate(suite)
           if cle == "raison.agent-lhm"]
    port = [i for i, (permis, cle) in enumerate(suite)
            if cle == "raison.agent-sans-port"]
    if not lhm:
        return False, "⛔ `raison.agent-lhm` ⛔ n'est portee par AUCUN appel"
    if not port:
        return False, "⛔ `raison.agent-sans-port` ⛔ n'est portee par AUCUN appel"
    permis_lhm = suite[lhm[0]][0]
    if permis_lhm != "true":
        return False, ("le geste est `%s` sous `raison.agent-lhm` — attendu "
                       "`true` : LHM ⛔ n'est PLUS un refus depuis dn4-48, et "
                       "un bouton gris y relaierait un refus DISPARU"
                       % permis_lhm)
    if suite[port[0]][0] != "false":
        return False, ("le geste est `%s` sous `raison.agent-sans-port` — "
                       "attendu `false` : sans carte enumeree la tache serait "
                       "posee sur un port qui n'existe pas"
                       % suite[port[0]][0])
    if not port[0] < lhm[0]:
        return False, ("`raison.agent-lhm` est evaluee AVANT "
                       "`raison.agent-sans-port` : une tour sans carte ET "
                       "sans LHM s'armerait")
    return True, ("LHM arme avec `raison.agent-lhm`, et il est evalue APRES "
                  "le grisage sur `raison.agent-sans-port`")


def charger_produit(source):
    """Importe le serveur — LE PRODUIT, ⛔ pas son texte.

    🔴 LA SOURCE EST **COMPILEE ICI**, ⛔ pas chargee par le mecanisme
       ordinaire : `exec_module()` consulte `__pycache__`, dont la validation
       repose sur (mtime, taille). Une gate qui mesure la version d'hier est
       pire qu'une gate absente — elle publie un verdict FAUX avec l'autorite
       d'une mesure. C'est un piege paye le 2026-09-08, ⛔ pas une precaution.
    ⚠️ Le module ne fait RIEN a l'import : il ne lie aucun port, n'appelle
       aucun PowerShell, n'ouvre aucun navigateur."""
    chemin = os.path.join(RACINE, PY)
    try:
        mod = importlib.util.module_from_spec(
            importlib.util.spec_from_loader("dn_installeur_dn76", loader=None))
        mod.__file__ = chemin
        exec(compile(source, chemin, "exec"), mod.__dict__)   # noqa: S102
        return mod, None
    except Exception as exc:                              # noqa: BLE001
        return None, "%s: %s" % (type(exc).__name__, str(exc)[:90])


# ═══════════════════════════ LES MUTANTS ═══════════════════════════════════

def muter(etat):
    """REPLANTE une faute DANS L'ETAT — ⛔ jamais dans un fichier du depot.

    🔴 TOUTE mutation passe par cet unique etat, et le corps principal compare
       l'etat AVANT/APRES : la garde du no-op est donc UNIVERSELLE.
    ⚠️ MAIS ELLE N'EST ATTEINTE QUE SI LE CORPS **REND**. Un corps qui `split`,
       indexe ou depaquette sur une ancre disparue LEVE, et le `try` du corps
       principal le rend en `rc=1` + `BILAN` + `[KO ]` — MOT POUR MOT le
       contrat que la campagne appelle « sain » : un mutant PERIME passerait
       pour un gardien vivant. ⇒ tout corps VERIFIE son ancre d'abord et rend
       `e` INCHANGE. ⛔ Le mutant 24 leve EXPRES : il est le temoin de ce cas.
    ⛔ ET CHAQUE MUTANT **REPLANTE LA FAUTE**, ⛔ il ne debranche pas la garde :
       un mutant qui coupe le controle ne prouve que l'existence du controle.
    ⛔ AUCUN MUTANT NE POSE SON LITTERAL DANS UN COMMENTAIRE : les controles
       lisent le script SANS ses commentaires, et un mutant qui ferait rougir
       sur de la prose prouverait un `grep`, ⛔ pas une propriete."""
    e = copy.deepcopy(etat)
    p, r = e["fichiers"], e["regles"]
    page = p.get(PAGE, "")
    py = p.get(PY, "")
    ps1 = p.get(OUTIL, "")

    if _MUTANT == 1:
        lis = li_de_premier_niveau(page)
        if len(lis) != 4:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        m = re.search(r'<span class="val" id="v-etape-[\w-]+">…</span>',
                      lis[-1])
        if not m:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = page.replace(m.group(0), '<span class="cle">…</span>', 1)
    elif _MUTANT == 2:
        a = '"v-etape-console"'
        if page.count(a) < 2:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        m = RE_CHAMPS.search(page)
        if not m or a not in m.group(1):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        neuf = m.group(0).replace(",\n              " + a, "", 1)
        if neuf == m.group(0):
            neuf = m.group(0).replace(a + ", ", "", 1)
        if neuf == m.group(0):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = page.replace(m.group(0), neuf, 1)
    elif _MUTANT == 3:
        corps = bloc_regle(style_de(page), SELECTEURS_DN76[0])
        a = SELECTEURS_DN76[0] + " {" + corps + "}"
        if not corps or a not in page:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = page.replace(
            a, SELECTEURS_DN76[0] + " {" + corps.replace(
                "var(--dn-accent)", "#a0d8ff", 1) + "}", 1)
    elif _MUTANT == 4:
        corps = bloc_regle(style_de(page), SELECTEURS_DN76[2])
        a = SELECTEURS_DN76[2] + " {" + corps + "}"
        if not corps or a not in page:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = page.replace(
            a, SELECTEURS_DN76[2] + " {" + corps.replace(
                "var(--dn-trait)", "var(--dn-trai)", 1) + "}", 1)
    elif _MUTANT == 5:
        # 🔴 LA PORTE MECANIQUE, REPLANTEE : la valeur ABANDONNEE entre dans la
        #    page comme un jeton ordinaire — et `(c18)` de `dn7-1` la
        #    laisserait passer, puisqu'elle EST a la ligne de firmware citee.
        a = "--dn-trait: #33404a;"
        if a not in page:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = page.replace(a, a + " --dn-succes: #4ade80;", 1)
    elif _MUTANT == 6:
        ui = p.get(UI, "")
        lignes = [l for l in ui.split("\n") if VERT_REJETE in l
                  and any(x in l for x in MARQUES_REJET)]
        if not lignes:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        a = lignes[0]
        neuf = a
        for x in MARQUES_REJET:
            neuf = neuf.replace(x, "")
        if neuf == a:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[UI] = ui.replace(a, neuf, 1)
    elif _MUTANT == 7:
        a = 'armerGeste("b-deps"'
        if a not in page:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        m = re.search(re.escape(a) + r"[^;]*;", page)
        if not m:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = page.replace(
            m.group(0),
            "bDeps.disabled = !(e.manquantes && e.manquantes.length);", 1)
    elif _MUTANT == 8:
        a = '"raison.agent-lhm"'
        if a not in page:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = page.replace(a, '"raison.agent-lhm-2"', 1)
    elif _MUTANT == 9:
        corps = corps_fonction(sans_commentaires(
            region(page, "<script>", "</script>")), NOM_FABRIQUE)
        args = appels(corps, NOM_BLOCMOT)
        if not corps or not args:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        a = NOM_BLOCMOT + "(" + ", ".join(args[0][0]) + ")"
        if a not in page:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = page.replace(
            a, 'r.textContent = "the gesture is not available"', 1)
    elif _MUTANT == 10:
        a = "'permanence', '%s', 'retirer'" % VERBE_NEUF
        if a not in ps1:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[OUTIL] = ps1.replace(a, "'permanence', 'retirer'", 1)
    elif _MUTANT == 11:
        a = 'VERBES = ("stop", "retirer", "%s")' % VERBE_NEUF
        if a not in py:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = py.replace(a, 'VERBES = ("stop", "retirer")', 1)
    elif _MUTANT == 12:
        bloc = bloc_verbe(ps1, VERBE_NEUF)
        m = re.search(r"^.*-File \$\w+ lancer.*$", bloc, re.M) if bloc else None
        if not m:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        # ⚠️ SCOPE AU BLOC, comme les mutants 13 et 16.
        p[OUTIL] = ps1.replace(bloc, bloc.replace(m.group(0), "", 1), 1)
    elif _MUTANT == 13:
        # 🔴 LA SUBSTITUTION EST **SCOPEE AU BLOC**, ⛔ pas au fichier — ET
        #    C'EST UNE FAUTE MESUREE LE 2026-09-10 : `$i = Get-Instances`
        #    apparait CINQ fois dans l'outil, et un `replace(…, 1)` global
        #    mordait sur le verbe `etat`, cent lignes plus haut. Le mutant
        #    changeait donc bien des octets — donc ⛔ pas de `rc=3` — en visant
        #    A COTE, et il sortait VERT sur une garde INTACTE.
        bloc = bloc_verbe(ps1, VERBE_NEUF)
        a = "    $i = Get-Instances"
        if not bloc or a not in bloc:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[OUTIL] = ps1.replace(bloc, bloc.replace(
            a, "    $reglages = New-ScheduledTaskSettingsSet -RestartCount 3\n"
               + a, 1), 1)
    elif _MUTANT == 14:
        bloc = bloc_verbe(ps1, VERBE_NEUF)
        a = "    exit %s" % CODE_DEMI
        if not bloc or a not in bloc:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[OUTIL] = ps1.replace(a, "    exit 0", 1)
    elif _MUTANT == 15:
        a = "exit 11"
        if a not in ps1:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[OUTIL] = ps1.replace(a, "exit %s" % CODE_DEMI, 1)
    elif _MUTANT == 16:
        # 🔴 SCOPE AU BLOC, POUR LA MEME RAISON QUE LE MUTANT 13.
        bloc = bloc_verbe(ps1, VERBE_NEUF)
        a = "    $i = Get-Instances"
        if not bloc or a not in bloc:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[OUTIL] = ps1.replace(bloc, bloc.replace(
            a, "    Start-Process powershell.exe -Verb RunAs\n" + a, 1), 1)
    elif _MUTANT == 17:
        a = '        if chemin == ROUTE_DEPENDANCES:'
        if a not in py:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = py.replace(
            a, '        if chemin == "/api/lhm":\n'
               '            self._json(200, _powershell(["-Command", '
               'GESTE_LHM]))\n'
               '            return\n' + a, 1)
    elif _MUTANT == 18:
        # 🔴 LA ROUTE SORT DE `do_POST` : elle est servie AVANT la garde, dans
        #    `do_GET`, ou `_garde()` protege bien `do_GET` — mais la route
        #    neuve, elle, repond desormais sur un chemin QUI N'EST PLUS GARDE
        #    parce qu'on l'a sortie du seul endroit qui la voyait.
        a = ("        if chemin == ROUTE_DEPENDANCES:\n"
             "            self._json(200, jouer_dependances())\n"
             "            return\n")
        if a not in py:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = py.replace(a, "", 1).replace(
            "    def do_POST(self):\n",
            "    def _deps(self):\n"
            "        self._json(200, jouer_dependances())\n"
            "        return\n\n"
            "    def do_POST(self):\n"
            "        if self.path.split(\"?\", 1)[0] == ROUTE_DEPENDANCES:\n"
            "            return self._deps()\n", 1)
    elif _MUTANT == 19:
        a = "    mots = GESTE_DEPENDANCES.split()"
        if a not in py:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = py.replace(
            a, '    mots = "pip install --user psutil pyserial".split()', 1)
    elif _MUTANT == 20:
        a = A_MOTIF_LHM[1]
        if a not in page:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = page.replace(a, "un geste a jouer vous-meme")
    elif _MUTANT == 21:
        # ⚠️ LA CIBLE EST **VIDEE**, ⛔ la cle n'est pas supprimee : supprimer la
        #    cle ferait AUSSI diverger `CIBLES` et `MUTANTS`, donc rougir (c16)
        #    — un mutant qui vise deux controles a la fois n'en garde bien
        #    aucun.
        if not e["cibles"].get(9):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        e["cibles"][9] = ()
    elif _MUTANT == 22:
        if 1 not in e["cibles"]:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        e["cibles"][1] = ("c1", "c99")
    elif _MUTANT == 23:
        if 999 in e["cibles"]:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        e["cibles"][999] = ("c1",)
    elif _MUTANT == 24:
        # 🔴 LE TEMOIN DU MUTANT MORT : il LEVE EXPRES. Sans lui, « un corps qui
        #    leve se rend en KO » serait une regle ecrite que rien ne joue.
        raise RuntimeError("temoin : ce mutant LEVE, et c'est son objet")
    elif _MUTANT == 25:
        r["sortie_anticipee"] = True
    elif _MUTANT == 28:
        m = re.search(r'("dependances"\s*:\s*")([^"]+)(")', page)
        if not m:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = page.replace(m.group(0),
                               m.group(1) + m.group(2) + "-x" + m.group(3), 1)
    elif _MUTANT == 29:
        a29 = '    if verbe == "poser":'
        if a29 not in py:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = py.replace(a29, '    if verbe == "poser" and False:', 1)
    elif _MUTANT == 31:
        a31 = "LA PERMANENCE EST **POSEE** ET L'AGENT **TOURNE**, mais **SANS "
        if a31 not in py:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = py.replace(
            a31, "LibreHardwareMonitor est INJOIGNABLE, et ⛔ RIEN n'a ete "
                 "pose. Sans lui, pas de ", 1)
    elif _MUTANT == 32:
        # REPLANTE LA FAUTE : le grisage sur LHM REVIENT, dans la branche
        # qu'il occupait avant `dn4-48`. ⛔ Ce n'est pas un debranchement —
        # c'est la page qui redevient incapable d'activer l'agent sur une tour
        # dont LHM ne repond pas, pendant que le pre-vol, lui, l'ATTEND puis
        # DEMARRE. La faute revient sous SA forme d'origine.
        a32 = '    armerGeste("b-agent-poser", true, "raison.agent-lhm");'
        if a32 not in page:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = page.replace(
            a32, '    armerGeste("b-agent-poser", false, "raison.agent-lhm");',
            1)
    elif _MUTANT == 30:
        a30 = "  b.disabled = !permis;"
        if a30 not in page:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = page.replace(a30, "  b.disabled = permis;", 1)
    elif _MUTANT == 27:
        # REPLANTE LA FAUTE : un `pip` INDISPONIBLE est annonce comme un
        # SUCCES. ⛔ Ce n'est pas un debranchement — c'est la confusion que la
        # ligne 6 de la matrice d'E/S existe pour interdire.
        a = "le geste n'a PAS eu lieu, et il redevient un geste A "
        if a not in py:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = py.replace(a, "l'installation a abouti, et c'est un ", 1)
    elif _MUTANT == 26:
        # REPLANTE LA FAUTE : le commentaire du temoin se referme TROP TOT.
        # ⛔ Ce n'est PAS un debranchement du controle — c'est exactement les
        #    octets qui ont laisse quatre gates vertes le 2026-09-10.
        # ⚠️ L'ANCRE VISE LA **FERMETURE** DU COMMENTAIRE DU TEMOIN, ⛔ plus une
        #    phrase de sa prose : une phrase se reecrit (elle l'a ete le
        #    2026-09-10, « quatre jetons » ⇒ « CINQ »), et le mutant devient
        #    alors un NO-OP qui passe pour un gardien vivant.
        m = re.search(r"(\n\s+⚠️ ET LES APLATS S'ECRIVENT EN)", page)
        if not m:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = page.replace(m.group(0), " */" + m.group(1), 1)
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
    print("dn7-6 — LA PAGE INSTALLE CE QU'ELLE PEUT, ET ELLE BLOQUE"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)
    print("cibles     : %s" % " · ".join(FIXES))
    print("⛔ CETTE GATE EST STRUCTURELLE : elle N'OUVRE AUCUN NAVIGATEUR,")
    print("   N'INSTALLE RIEN et NE POSE AUCUNE TACHE. Elle prouve que LE")
    print("   MECANISME EST BRANCHE, ⛔ pas qu'un bouton soit grise sous les")
    print("   yeux de quelqu'un : ca vit dans `mesures/dn7-6/T2`, COTE")
    print("   WINDOWS, et c'est l'ŒIL DE L'OWNER qui ferme `AC7.6.1`.")

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
    ident = neuf["fichiers"].get(IDENT, "")
    ui = neuf["fichiers"].get(UI, "")
    regles = neuf["regles"]
    cibles = neuf["cibles"]
    style = style_de(page)
    # ⛔ CE QUI S'EXECUTE, ⛔ PAS CE QUI L'EXPLIQUE.
    js = sans_commentaires(region(page, "<script>", "</script>"))

    # ── (c1)(c2)(c3) CHAQUE ETAPE PORTE SON ETAT ────────────────────────
    print("\n── (c1)(c2)(c3) L'ETAT PAR ETAPE, ET ⛔ AUCUN VERT ───────────────")
    ok, det = chaque_etape_porte_son_temoin(page, js)
    ctrl(ok, "(c1) chaque etape porte son temoin, et il est su", det if ok
         else "⛔ %s — une etape sans etat laisse deviner si elle est faisable"
              % det)

    ok, det = le_temoin_se_peint_dans_les_jetons(style)
    ctrl(ok, "(c2) le temoin se peint dans les jetons STATUES", det if ok
         else "⛔ %s — l'identite visuelle est une LISTE FERMEE de sept roles, "
              "et une couleur nue la contourne en une ligne" % det)

    ok, det = les_regles_sont_atteignables(page)
    ctrl(ok, "(c17) les regles d'etat sont ATTEIGNABLES", det if ok
         else "⛔ %s — une regle bien formee mais INATTEIGNABLE laisse quatre "
              "gates vertes : mesure du 2026-09-10" % det)

    ok, det = aucun_vert_rejete(page, ident, ui)
    ctrl(ok, "(c3) ⛔ AUCUN VERT : la valeur rejetee reste dehors", det if ok
         else "⛔ %s — le vert a ete ESSAYE sur le produit et ABANDONNE le "
              "2026-08-25, sur constat owner A L'ŒIL" % det)

    # ── (c4)(c5) LE DESARMEMENT PASSE PAR UNE FABRIQUE ──────────────────
    print("\n── (c4)(c5) GRISE, ⛔ PAS AVERTI — ET LA RAISON EST SOUS LUI ─────")
    ok, det = le_desarmement_passe_par_une_fabrique(js)
    ctrl(ok, "(c4) les gestes passent par UNE fabrique nommee", det if ok
         else "⛔ %s — 15 assignations `.disabled` dispersees existaient deja (mesure du 2026-09-10 ; le « 17 » publie comptait des REFERENCES) ; "
              "en ajouter est le defaut, ⛔ pas la solution" % det)

    ok, det = le_motif_est_ecrit_sous_le_bouton(page, js)
    ctrl(ok, "(c5) le motif du desarmement est ECRIT sous le bouton", det if ok
         else "⛔ %s — un bouton grise sans raison est une panne, ⛔ pas une "
              "precondition" % det)

    # ── (c6)…(c9) LE VERBE NEUF ─────────────────────────────────────────
    print("\n── (c6)…(c9) LE VERBE NEUF COMPOSE, ET IL N'ELEVE RIEN ───────────")
    ok, det = le_verbe_bouge_sur_ses_trois_surfaces(ps1, py, js)
    ctrl(ok, "(c6) le verbe neuf est sur ses TROIS surfaces", det if ok
         else "⛔ %s" % det)

    ok, det = le_verbe_compose(ps1)
    ctrl(ok, "(c7) le verbe neuf COMPOSE, et il REEMPLOIE", det if ok
         else "⛔ %s" % det)

    ok, det = le_code_de_demi_succes_est_propre(ps1)
    ctrl(ok, "(c8) le code de demi-reussite est PROPRE", det if ok
         else "⛔ %s" % det)

    ok, det = aucune_elevation_dans_le_verbe(ps1)
    ctrl(ok, "(c9) ⛔ aucune elevation dans le bloc du verbe neuf", det if ok
         else "⛔ %s" % det)

    # ── (c10)…(c13) CE QU'ELLE INSTALLE, CE QU'ELLE EXPOSE ──────────────
    print("\n── (c10)…(c13) ELLE INSTALLE CE QU'ELLE PEUT, ET ELLE L'ECRIT ────")
    ok, det = pip_executable_lhm_non(py, page)
    ctrl(ok, "(c10) `pip` est EXECUTABLE, LHM ⛔ ne l'est pas", det if ok
         else "⛔ %s" % det)

    produit, err = charger_produit(py)
    ok, det = ((False, err) if produit is None
               else la_route_neuve_est_gardee(produit))
    ctrl(ok, "(c11) la route NEUVE refuse `Origin` et `Host`", det if ok
         else "⛔ %s — `(c27)` de `dn7-1` ⛔ ne connait que DEUX routes" % det)

    ok, det = le_geste_joue_est_le_geste_publie(py)
    ctrl(ok, "(c12) le geste joue est LE geste publie", det if ok
         else "⛔ %s" % det)

    ok, det = ((False, err) if produit is None
               else les_trois_issues_du_geste_sont_jouees(produit))
    ctrl(ok, "(c18) les TROIS issues du geste `pip` sont JOUEES", det if ok
         else "⛔ %s — `(c12)` lit le TEXTE et ⛔ ne dit rien de ce que la "
              "fonction REND" % det)

    ok, det = ((False, err) if produit is None
               else la_route_de_la_page_est_celle_du_serveur(page, produit))
    ctrl(ok, "(c19) la page POSTE sur la route que le serveur SERT", det if ok
         else "⛔ %s — demontre : une route divergente laisse HUIT gates "
              "vertes et rend 404" % det)

    ok, det = ((False, err) if produit is None
               else les_codes_de_poser_sont_rendus(produit))
    ctrl(ok, "(c20) les codes de `poser` sont RENDUS, ⛔ pas aplatis", det if ok
         else "⛔ %s" % det)

    ok, det = la_polarite_de_la_fabrique_est_gardee(js)
    ctrl(ok, "(c21) la fabrique grise DANS LE BON SENS", det if ok
         else "⛔ %s — `(c4)` ⛔ ne juge PAS le sens" % det)

    ok, det = lhm_arme_le_geste_avec_son_avertissement(js)
    ctrl(ok, "(c22) LHM absent ARME le geste, ⛔ il ne le grise plus",
         det if ok else "⛔ %s" % det)

    ok, det = elle_dit_ce_qu_elle_n_installe_pas(page)
    ctrl(ok, "(c13) elle dit ce qu'elle N'INSTALLE PAS, et pourquoi", det if ok
         else "⛔ %s" % det)

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

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : qu'un bouton soit REELLEMENT")
    print("   grise sous les yeux de quelqu'un, ni qu'un agent soit REELLEMENT")
    print("   active. Elle prouve que le mecanisme est BRANCHE. Le reste vit")
    print("   dans `mesures/dn7-6/T2`, cote Windows, et c'est l'ŒIL DE")
    print("   L'OWNER — ⛔ aucune gate de ce depot.")
    return bilan(1 if ko_total[0] else 0)


if __name__ == "__main__":
    sys.exit(main())

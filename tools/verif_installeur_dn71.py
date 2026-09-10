#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn7-1 — L'INSTALLEUR SE LANCE SANS ELEVATION, ET LA PAGE PILOTE DEJA L'AGENT.

======================= CE QUE CETTE GATE GARDE, ET POURQUOI ================

`installeur/` est un dossier NEUF qui porte du code EXECUTABLE et une page que
l'inconnu traverse forcement. Cinq promesses y sont ecrites, et chacune est du
genre a pourrir en silence :

  1. **Le dossier est CLASSE.** `verif_licences_dn52.py` garde la couverture des
     licences DANS LES DEUX SENS : un repertoire de 1er niveau qui n'est nomme
     par aucune des deux listes fait ROUGIR une gate verte. ⇒ le classement est
     un PREALABLE au premier commit, ⛔ pas un controle de fin.
  2. **⛔ AUCUNE ELEVATION.** Ce n'est pas une intention : le code POSE deja sa
     tache en `-RunLevel Limited` et sa propre garde `Stop2` sur tout le reste
     (`tools/dn_agent_tour.ps1:737`). Un installeur eleve ferait ECHOUER l'outil
     qui existe. ⇒ le vocabulaire d'elevation est interdit dans le code livre.
  3. **LE PORT EST TIRE.** Le banc d'essai avait pris `8123`, en dur. Un port
     fixe peut etre DEJA PRIS chez un inconnu — et comme mettre a jour, c'est
     reinstaller, le deuxieme lancement est le cas NOMINAL de tout le monde.
  4. **ON EXPOSE, ⛔ ON NE CONSTRUIT PAS.** Les deux gestes appellent des verbes
     qui EXISTENT. ⇒ cette gate RELIT le `[ValidateSet]` de l'outil, ⛔ elle ne
     recopie aucun nom : le jour ou l'outil en perd un, c'est ici que ca rougit.
  5. **L'IDENTITE VISUELLE EST STATUEE ET ECRITE.** Chaque couleur cite SA ligne
     de firmware, et l'egalite page ⇄ declaration est gardee DANS LES DEUX SENS.

── CE QU'ELLE NE PROUVE ⛔ PAS, ECRIT PLUTOT QUE TU ─────────────────────────

⛔ Elle ne lance rien. Elle ⛔ n'ouvre aucun port, ⛔ n'appelle aucun PowerShell,
   ⛔ ne demande aucune tache planifiee. Elle relit ce que le depot PUBLIE.
   ⇒ qu'un `.bat` DEMARRE vraiment sur une machine Windows, que la page soit
   servie en contexte securise et que le retrait fonctionne sont des MESURES,
   consignees sous `mesures/dn7-1/`, ⛔ pas des proprietes du texte.
⛔ Elle ne juge aucune couleur « jolie ». Elle juge que la couleur employee est
   celle qui est declaree, et que la declaration cite une source ROUVRABLE.

Emploi :
    python3 tools/verif_installeur_dn71.py
    python3 tools/verif_installeur_dn71.py --liste-mutants
    python3 tools/verif_installeur_dn71.py --mutant <n>

Sortie : 0 si tout passe · 1 sur un vrai defaut · 2 sur un mutant inconnu ·
         3 si le mutant demande est PERIME (il n'a rien change).
"""

import argparse
import ast
import contextlib
import copy
import importlib.util
import io
import os
import re
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DOSSIER = "installeur"
BAT = "installeur/DeskNode-installeur.bat"
PY = "installeur/dn_installeur.py"
PAGE = "installeur/index.html"
IDENT = "installeur/IDENTITE.md"
LIC = "LICENSING.md"
LISEZMOI = "README.md"
ROADMAP = "docs/roadmap.md"
OUTIL = "tools/dn_agent_tour.ps1"
ATTRIBUTS = ".gitattributes"

QUATRE = (BAT, PY, PAGE, IDENT)
FIXES = (BAT, PY, PAGE, IDENT, LIC, LISEZMOI, ROADMAP, OUTIL, ATTRIBUTS)


def fichiers_de_code(traces, fichiers):
    """Les fichiers de CODE sous `installeur/`, **DERIVES de l'arbre**.

    🔴 ⛔ PLUS UN TUPLE FIXE, ET C'EST UN CORRECTIF. `CODE = (BAT, PY, PAGE)`
       etait ecrit a la main : un CINQUIEME fichier de code verse sous
       `installeur/` echappait a (c4) — l'elevation — et a (c10) — le flash —,
       qui restaient VERTS sur une population qu'ils ne couvraient plus. C'est
       la classe « gate scopee qui epingle VERT le meme defaut ailleurs », deja
       payee par ce depot.
    ⛔ Les `.md` en sont exclus, et c'est ecrit : ce sont de la PROSE, et elle
       cite forcement ce que le code ne doit pas porter (le vocabulaire de
       l'elevation, celui du flash). Les y inclure ferait rougir la page qui
       explique la regle."""
    return tuple(sorted(f for f in traces
                        if f.startswith(DOSSIER + "/")
                        and not f.lower().endswith(".md")
                        and f in fichiers))

# ── LES ANCRES LITTERALES ─────────────────────────────────────────────────
# Une ancre qui bouge rend son mutant PERIME (rc=3) ⇒ elle se remarque,
# ⛔ elle ne pourrit pas en silence.
A_LIC_LIGNE = ("| `installeur/` — the local install page and the script that "
               "serves it | **GPL-3.0-or-later** | [`LICENSE`](LICENSE) |")
A_PORT0 = "PORT_DEMANDE = 0"
A_ADRESSE = 'ADRESSE = "127.0.0.1"'
A_URL = 'url = "http://%s:%d/" % (ADRESSE, port_reel)'
A_BIND = "ThreadingHTTPServer((ADRESSE, PORT_DEMANDE), Poignee)"
A_LU = "srv.server_address[1]"
# ⚠️ ANCRE MISE A JOUR LE 2026-09-10 (`dn7-6`), ⛔ PAS PAR CONFORT : le
#    serveur expose desormais un TROISIEME verbe (`poser`), et une ancre
#    litterale qui ne suit pas son produit rend ses mutants PERIMES —
#    `rc=3`, donc « muets » pour `tools/verif_campagne_dn56.py`, qui rougit
#    alors sur ce qu'une AUTRE marche a ecrit. Valeur d'avant, nommee :
#    ~~`VERBES = ("stop", "retirer")`~~.
A_VERBES = 'VERBES = ("stop", "retirer", "poser")'
A_RETIRER = 'if verbe == "retirer":'
A_REQUETE = "encore, _rl = tache_presente()"
A_GESTE_PIP = "pip install --user psutil pyserial"
A_GESTE_PATH = "Add python.exe to PATH"
A_PYTHON_ABSENT = "PYTHON 3 EST INTROUVABLE"
A_PORTEUR = "Porteur du retour"
A_RESIDUEL = "RÉSIDUEL DÉCLARÉ"
A_PORTEUR_H2 = "son porteur est\n`dn8`"
A_SECTION_README = "## 🆕 Installer DeskNode"
A_SECTION_SUITE = "## Arborescence"
A_RENVOI = "Lancer / arrêter l'agent DEPUIS WINDOWS"
A_UNSUPPORTED = "etat-unsupported"
A_NOT_ALLOWED = "etat-not-allowed"
A_SERIAL = '("serial" in navigator)'
A_SECURE = "window.isSecureContext === true"
A_NAVIGATEURS = "Microsoft Edge"
A_ADRESSE_PAGE = "http://127.0.0.1:"
A_GARDE_GET = '    def do_GET(self):\n        if not self._garde():\n            return\n'
A_GARDE_POST = '    def do_POST(self):\n        if not self._garde():\n            return\n'
A_BLANCHE = "        if chemin in SERVIS:\n            fichier, ctype = SERVIS[chemin]\n"
A_REGLE_EOL = "*.bat text eol=crlf"
# Ce qui signe un serveur de FICHIERS la ou on veut une liste blanche.
JETONS_ARBORESCENTS = ("simplehttprequesthandler", "translate_path",
                       "os.path.join(racine, chemin", "sendfile", "directory=")

# Le vocabulaire de l'elevation. ⛔ IL NE VIT QUE DANS CETTE GATE : le citer
# dans les fichiers gardes le ferait rougir sur du contenu JUSTE, et c'est
# pour ca que le code livre explique l'absence d'elevation SANS nommer ces
# jetons. Le README, lui, n'est pas dans le rayon de ce controle.
#
# 🔴 DES MOTIFS, ⛔ PAS DES CHAINES LITTERALES — ET C'EST UN TROU MESURE, ⛔ pas
#    une precaution. La 1re version cherchait la chaine `-verb runas` : elle
#    attrapait `powershell -Verb RunAs …` ecrit d'un bloc, et ⛔ RATAIT la
#    forme la plus naturelle en Python, `["powershell", "-Verb", "RunAs"]`,
#    ou les deux jetons sont SEPARES par une virgule et un guillemet. Le mutant
#    5 est sorti VERT sur cette forme, et la question qu'il posait avait pour
#    reponse « la garde a un trou », ⛔ pas « le mutant vise a cote ».
#    ⇒ chaque entree est un MOTIF, et `runas` est cherche COMME MOT.
MOTIFS_ELEVATION = (
    ("runas", re.compile(r"\brunas\b", re.I)),
    ("RunAsAdministrator", re.compile(r"runasadministrator", re.I)),
    ("RunLevel Highest", re.compile(r"runlevel\s*=?\s*['\"]?highest", re.I)),
    ("requestedExecutionLevel", re.compile(r"requestedexecutionlevel", re.I)),
    ("requireAdministrator", re.compile(r"requireadministrator", re.I)),
    ("ShellExecute + elevation", re.compile(r"shellexecute\w*", re.I)),
    ("Start-Process -Verb", re.compile(r"start-process[^\n]{0,80}-verb", re.I)),
)

# Ce qui signe le flash, et qui n'appartient ⛔ PAS a cette marche.
# 🔴 RETOURNE LE 2026-09-08 PAR `dn7-2` — ⛔ LA LIGNE CI-DESSUS N'EST PAS
#    EFFACEE, ET SON MOTIF D'ORIGINE EST GARDE PARCE QU'IL ETAIT **JUSTE** :
#    tant que le perimetre de `dn7-1` excluait le flash, un jeton de flash sous
#    `installeur/` etait un debordement de marche, et (c10) avait raison de le
#    refuser. **LA FRONTIERE A BOUGE, ⛔ PAS LA REGLE** : `dn7-2` livre le
#    branchement, donc ces memes jetons passent d'INTERDITS a EXIGES.
# ⚠️ ⛔ ET LE CONTROLE N'EST PAS SUPPRIME, IL EST INVERSE. Le supprimer aurait
#    perdu la garde : plus rien ne verrait quelqu'un DEBRANCHER le flash de la
#    page. ⇒ le mutant 12, qui replantait « charge esp-web-tools dans la page »,
#    est reecrit A L'ENVERS — c'est desormais RETIRER le branchement qui doit
#    faire rougir.
# 🎯 LA LISTE D'ORIGINE, GARDEE TELLE QUELLE POUR MEMOIRE :
#    ("esp-web-tools", "esp_web_tools", "install-button", "manifest.json",
#     "merge_bin", "chipfamily")
#    ⚠️ `merge_bin` en sort et ⛔ n'est PAS orphelin pour autant : il est
#       INTERDIT par `tools/verif_flash_dn72.py`, qui garde le manifeste — et
#       c'est la qu'il a du sens, puisque c'est le manifeste qui pourrait
#       fusionner les morceaux. Le laisser ici en aurait fait un jeton EXIGE,
#       c'est-a-dire l'inverse exact de ce qu'il faut.
# 🔴 ET LE CONTROLE ANCRE SUR **LE BRANCHEMENT REEL**, ⛔ PAS SUR LA PROSE —
#    CORRECTIF DE REVUE, SUR UNE FAUTE DEMONTREE. La 1re version cherchait ces
#    jetons N'IMPORTE OU dans la page, en casse basse. Or ils vivent aussi dans
#    le commentaire d'en-tete, dans deux commentaires de script et dans l'appel
#    `fetch` : SUPPRIMER PHYSIQUEMENT la balise `<script src=…>` ET l'element
#    d'installation laissait donc le controle **VERT** sur une page qui ne peut
#    plus rien flasher. Et le mutant qui semblait le garder ne rougissait que
#    parce que sa substitution GLOBALE reecrivait aussi les commentaires — il
#    etait plus LARGE que la faute qu'il nomme.
#    ⇒ on lit l'URL REELLEMENT CHARGEE et l'ELEMENT REEL, comme le fait deja la
#      gate de `dn7-2`. La liste ci-dessus n'est plus employee et reste ecrite
#      pour memoire.
RE_SRC_MODULE = re.compile(
    r"<script[^>]*\bsrc\s*=\s*[\"']([^\"']*esp-web-tools[^\"']*)[\"']", re.I)
ANCRE_ELEMENT = "<esp-web-install-button "
ANCRE_MANIFESTE = 'manifest="charge/manifest.json"'

# La palette du BANC D'ESSAI — celle de GitHub, prise sous la main pour une
# soiree. `AC7.1.7` la REMPLACE ; si elle revient, c'est que l'identite a ete
# heritee au lieu d'etre statuee.
PALETTE_BANC = ("#0d1117", "#e6edf3", "#3fb950", "#161b22", "#30363d",
                "#8b949e", "#f85149", "#79c0ff", "#d29922", "#238636")

# Un porteur A NOMMER n'est ⛔ PAS un porteur — lecon de `dn6-4`, rejouee ici.
REFUS_PORTEUR = ("a nommer", "à nommer", "tbd", "a definir", "à définir",
                 "a preciser", "à préciser", "inconnu", "?", "-", "—", "")

RE_VALIDATESET = re.compile(r"\[ValidateSet\(([^)]*)\)\]")
# ⚠️ LA CLASSE DE CARACTERES EST ELARGIE, ET CE N'EST PAS DU CONFORT : bornee a
#    `[a-z]+`, elle laissait tomber en SILENCE un verbe a trait d'union, a
#    majuscule ou a chiffre — l'ensemble compare devenait alors FAUX, et (c7)
#    aurait juge un verbe expose contre une liste amputee.
RE_VERBE_PS = re.compile(r"'([A-Za-z][A-Za-z0-9_-]*)'")
RE_VERBES = re.compile(r"^VERBES\s*=\s*\(([^)]*)\)", re.M)
RE_PORT0 = re.compile(r"^PORT_DEMANDE\s*=\s*0\s*$", re.M)
RE_ADR_PORT = re.compile(r"127\.0\.0\.1\s*:\s*\d")
RE_HEX6 = re.compile(r"#[0-9a-fA-F]{6}\b")
RE_HEX3 = re.compile(r"#[0-9a-fA-F]{3}\b(?![0-9a-fA-F])")
# 🔴 UNE COULEUR N'EST ⛔ PAS FORCEMENT UN `#rrggbb`. L'egalite page ⇄
#    declaration ne connaissait QUE cette notation : un `rgb`, un `hsl` ou
#    ⚠️ ⛔ CES DEUX NOTATIONS S'ECRIVENT SANS PARENTHESES, ET CE N'EST PAS
#       DE LA COQUETTERIE. `verif_harnais_dn413.py` (AC7.4) chasse les
#       RENVOIS FANTOMES : un nom suivi de parentheses, cite entre accents
#       graves dans un commentaire, doit etre une fonction DEFINIE quelque
#       part du depot. Une notation CSS n'en est pas une ⇒ l'ecrire avec ses
#       parentheses a fait ROUGIR cette gate-la. MESURE le 2026-09-08.
#       🔴 ET LA PREMIERE REDACTION DE CE COMMENTAIRE A REPLANTE LA FAUTE
#          QU'IL DECRIT : elle citait les deux notations AVEC parentheses pour
#          les donner en exemple, et la gate a re-rougi sur l'explication
#          elle-meme. ⛔ Documenter un piege ne protege de rien.
#    un simple nom CSS passait sans etre declare nulle part, et l'identite
#    « statuee et ecrite » redevenait une identite qu'on peut contourner.
#    ⚠️ La recherche est bornee aux REGIONS DE STYLE (le bloc `<style>` et les
#       attributs `style="…"`), ⛔ pas au fichier entier : la prose de la page
#       parle de couleurs, et l'y chercher ferait rougir du contenu JUSTE.
RE_FONCTION_COULEUR = re.compile(
    r"\b(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch|color-mix)\s*\(", re.I)
NOMS_CSS = ("red", "blue", "green", "white", "black", "gray", "grey", "silver",
            "yellow", "orange", "purple", "navy", "teal", "olive", "maroon",
            "lime", "aqua", "fuchsia", "cyan", "magenta", "pink", "brown",
            "gold", "beige", "ivory", "khaki", "salmon", "tomato", "violet",
            "indigo", "crimson", "darkblue", "lightblue", "coral", "plum")
RE_NOM_CSS = re.compile(r"(?:^|[:\s,])(" + "|".join(NOMS_CSS) + r")\s*(?:;|\)|$)",
                        re.I | re.M)
RE_STYLE_BLOC = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
RE_STYLE_ATTR = re.compile(r'\sstyle="([^"]*)"')
# 🔴 CE QUE LA PAGE DOIT RENDRE POUR CHAQUE ETAT DE LA TACHE, APRES `retirer`.
#    ⚠️ C'EST UNE CORRESPONDANCE, ⛔ PAS UNE PRESENCE : (c9) ne verifiait que
#       l'existence de la sous-chaine `tache_presente(` dans les 1000 caracteres
#       qui suivent l'ancre. DEMONTRE en worktree : intervertir `if encore is
#       True:` et `if encore is False:` fait dire « la tache est ABSENTE » alors
#       qu'elle SURVIT, `rc` inchange a 0, et la gate restait a 25 OK / 0 KO —
#       exactement l'echec que la marche declare FATAL.
#    ⇒ la gate IMPORTE le produit et le fait JOUER contre un double de papier.
ATTENDU_RETIRER = {
    "survit":   ("ECHEC", 9),          # la tache est ENCORE la  ⇒ echec, rc 9
    "absente":  ("ABSENTE", 0),        # la tache est partie     ⇒ succes
    "inconnue": ("PAS confirme", 0),   # on n'a pas pu redemander ⇒ NON confirme
}
# 🔴 LES CODES DE SORTIE DU PRE-VOL. `README.md` publie le `6` comme
#    « l'instrument mecanique de l'ecart » et `AC7.1.6` se ferme dessus — or
#    DEMONTRE : remplacer `return 6 if manquantes else 0` par `return 0`
#    laissait la gate a 25 OK / 0 KO. Un code publie que rien ne joue est un
#    chiffre a croire sur parole.
ATTENDU_PREVOL = {
    "module_manquant": 6,
    "tout_est_la": 0,
    "page_absente": 3,
    # ⚠️ `3` COUVRE LA PAGE **ET** L'OUTIL. La docstring du produit l'annoncait
    #    (« la page **ou l'outil** ») et le code ne rendait `3` que pour la
    #    page : sans outil, le pre-vol annoncait « tout est la » pendant que
    #    les deux gestes exposes etaient MORTS.
    "pilote_absent": 3,
    # 🔴 dn7-5 — LA **POLARITE** DE LA SONDE LHM EST JOUEE, ⛔ pas seulement
    #    lue. DEMONTRE le 2026-09-10 : replier le ternaire du pre-vol en
    #    `"present" if lhm else "ABSENT"` fait dire **ABSENT** a une sonde qui
    #    n'a **PAS PU TOURNER** — l'ignorance publiee en constat, la faute meme
    #    que les trois positions existent pour empecher — et TOUTES les gates
    #    restaient vertes. Le tampon de `jouer_prevol` etait ECRIT PUIS JETE.
    #    ⚠️ Ce sont des MOTS IMPRIMES, ⛔ pas des codes de retour : LHM ⛔ ne
    #       pese pas sur le `rc`, et c'est precisement ce que `(c28)` garde.
    "lhm_present": "present",
    "lhm_absent": "ABSENT",
    "lhm_non_testable": "non testable",
}
# La ligne que le pre-vol imprime pour LHM — ⛔ un NOM, pas un numero de ligne.
RE_MOT_LHM = re.compile(r"^\s*LibreHardwareMonitor\s*:\s*(.+?)\s*$", re.M)
# `| `--dn-x` | role | `#rrggbb` | `chemin:ligne` | nom |`
RE_JETON = re.compile(
    r"^\|\s*`(--dn-[a-z-]+)`\s*\|\s*([^|]*?)\s*\|\s*`(#[0-9a-fA-F]{6})`\s*\|"
    r"\s*`([^`:]+):(\d+)`\s*\|", re.M)
RE_LIGNE_ROADMAP = re.compile(r"^\|\s*`(dn\d+(?:-\d+)?)`\s*\|(.*)\|\s*([^|]*)\|\s*$",
                              re.M)

LARGEUR_LIBELLE = 58

ok_total = [0]
ko_total = [0]
ids_emis = []

MUTANTS = {}                      # ⛔ AU NIVEAU MODULE — sinon `--liste-mutants`
CIBLES = {}                       # ⛔ AU NIVEAU MODULE — matiere de (c23)

MUTANTS[1] = ("efface de `LICENSING.md` la ligne qui classe `installeur/` "
              "⇒ un dossier neuf couvert par RIEN, dans les deux sens")
CIBLES[1] = ("c2",)
MUTANTS[2] = ("fait annoncer `installeur/` en CC-BY-SA-4.0 ⇒ du code range "
              "sous une licence de documentation")
CIBLES[2] = ("c2",)
MUTANTS[3] = ("convertit le `.bat` en LF ⇒ cmd.exe peut executer une ligne "
              "TRONQUEE, piege deja paye par le depot")
CIBLES[3] = ("c3",)
MUTANTS[4] = ("replante un verbe d'ELEVATION dans le `.bat`")
CIBLES[4] = ("c4",)
MUTANTS[5] = ("replante un verbe d'ELEVATION dans `dn_installeur.py`")
CIBLES[5] = ("c4",)
MUTANTS[6] = ("fige le port du serveur a `8123`, la valeur du banc d'essai "
              "⇒ `H6` se rouvre : un port fixe peut etre DEJA PRIS")
CIBLES[6] = ("c5",)
MUTANTS[7] = ("fait annoncer une adresse `file://` au lieu de l'adresse "
              "servie ⇒ contexte NON securise, Web Serial retire en silence")
CIBLES[7] = ("c6",)
MUTANTS[8] = ("fait ecouter et annoncer une IP ROUTABLE au lieu de la "
              "boucle locale")
CIBLES[8] = ("c6",)
MUTANTS[9] = ("fait exposer par la page un verbe ABSENT du `[ValidateSet]` "
              "de l'outil ⇒ la page REIMPLEMENTE au lieu d'exposer")
CIBLES[9] = ("c7",)
MUTANTS[10] = ("retire `retirer` des verbes exposes ⇒ l'inconnu qui n'aime "
               "pas garde une tache qui se relance a chaque session")
CIBLES[10] = ("c8",)
MUTANTS[11] = ("remplace la RE-REQUETE d'apres le retrait par une constante "
               "⇒ le verdict croit le message de sortie de l'outil")
CIBLES[11] = ("c9",)
# 🔴 MUTANT 12 REECRIT A L'ENVERS LE 2026-09-08, EN MEME TEMPS QUE (c10).
#    Il replantait « charge esp-web-tools dans la page » quand le flash etait
#    HORS perimetre. Le flash etant desormais LE livrable, la faute a replanter
#    est l'inverse : DEBRANCHER le module. ⛔ Un mutant qu'on aurait laisse tel
#    quel serait sorti VERT sur un produit SAIN — un mutant perime deguise en
#    gardien vivant.
MUTANTS[12] = ("DEBRANCHE `esp-web-tools` de la page ⇒ un bouton qui n'a "
               "plus rien a poser, et personne ne le voit")
CIBLES[12] = ("c10",)
MUTANTS[13] = ("efface du `.bat` le geste exact quand Python manque ⇒ un "
               "refus qui n'explique rien, le defaut meme qu'on corrige")
CIBLES[13] = ("c11",)
MUTANTS[14] = ("remplace au README le porteur de l'ecart par « a nommer » "
               "— la faute EXACTE que `dn6-4` a payee")
CIBLES[14] = ("c12",)
MUTANTS[15] = ("efface de la page le geste `pip install` de l'ecart declare")
CIBLES[15] = ("c13",)
MUTANTS[16] = ("prive le residuel de la Marque du Web de son porteur")
CIBLES[16] = ("c14",)
MUTANTS[17] = ("rend la page MUETTE sur ou aller quand l'acces serie manque")
CIBLES[17] = ("c15",)
MUTANTS[18] = ("supprime le test de CONTEXTE SECURISE de la page ⇒ elle se "
               "croit bonne partout")
CIBLES[18] = ("c16",)
MUTANTS[19] = ("prive un jeton de couleur de sa LIGNE source ⇒ une citation "
               "qu'on ne peut plus rouvrir")
# ⚠️ CIBLE DOUBLE, MESUREE : la ligne cesse d'etre lisible par la table
#    (c17) ET sa couleur quitte donc l'ensemble DECLARE, ce que le 2e sens
#    de (c19) voit. La cible dit ce que le mutant FAIT, ⛔ pas ce qu'on
#    aimerait qu'il isole.
CIBLES[19] = ("c17", "c19")
MUTANTS[20] = ("fait citer a un jeton une ligne de firmware qui ne porte "
               "PAS sa couleur ⇒ une source qui a pourri en silence")
CIBLES[20] = ("c18",)
MUTANTS[21] = ("pose dans la page une couleur qui n'est declaree NULLE PART")
CIBLES[21] = ("c19",)
MUTANTS[22] = ("declare un 8e jeton que la page n'emploie PAS ⇒ le SENS "
               "INVERSE : une identite qui a derive de sa page")
CIBLES[22] = ("c19",)
MUTANTS[23] = ("replante la palette du BANC D'ESSAI (celle de GitHub) dans "
               "la page ⇒ l'identite redevient heritee")
# ⚠️ CIBLE DOUBLE, MESUREE : la couleur du banc n'est declaree nulle part
#    (c19) ET elle appartient a la palette interdite (c20). La cible dit ce
#    que le mutant FAIT, ⛔ pas ce qu'on aimerait qu'il isole.
CIBLES[23] = ("c20", "c19")
MUTANTS[24] = ("DUPLIQUE la table des verbes dans la section d'installation "
               "du README au lieu d'y renvoyer ⇒ deux tables qui divergeront")
CIBLES[24] = ("c21",)
MUTANTS[25] = ("remet `dn7` a `not started` dans `docs/roadmap.md` ⇒ un etat "
               "publie qui contredit ce que le meme commit livre")
CIBLES[25] = ("c22",)
MUTANTS[26] = ("retire une cible de `CIBLES` ⇒ un controle garde par ZERO "
               "mutant, le risque que `dn6-1` avait paye")
CIBLES[26] = ("c23",)
MUTANTS[27] = ("declare dans `CIBLES` un controle INEXISTANT (`c99`) ⇒ une "
               "cible PERIMEE, que « N mutants, N rouges » ne verrait pas")
CIBLES[27] = ("c24",)
MUTANTS[28] = ("declare une cible pour un mutant qui N'EXISTE PAS")
CIBLES[28] = ("c25",)
MUTANTS[29] = ("replante une SORTIE ANTICIPEE NON DECLAREE : le bilan "
               "retrecit, et il sortirait VERT")
CIBLES[29] = ("z",)
MUTANTS[30] = ("declare un mutant dont le CORPS LEVE ⇒ un mutant MORT, qui "
               "sortirait en Traceback SANS `BILAN` s'il n'etait pas rattrape")
CIBLES[30] = ("c0",)
MUTANTS[31] = ("rend `installeur/index.html` VIDE (⛔ un vide n'est pas une "
               "absence de defaut)")
CIBLES[31] = ("c1",)
MUTANTS[32] = ("sort `installeur/IDENTITE.md` du corpus ⇒ l'identite cesse "
               "d'etre ECRITE, et plus rien ne garde la palette")
CIBLES[32] = ("c1",)
# 🔴 LES HUIT SUIVANTS SONT NES D'UNE REVUE, ET CHACUN REPLANTE UNE FAUTE QUI
#    A ETE **DEMONTREE VERTE** — ⛔ pas une faute imaginee.
MUTANTS[33] = ("retire de `.gitattributes` la regle `eol=crlf` ⇒ ce que git "
               "LIVRE au cloneur cesse d'etre garanti, l'arbre restant CRLF")
CIBLES[33] = ("c3",)
MUTANTS[34] = ("remplace la LISTE BLANCHE du serveur par un chemin arbitraire "
               "⇒ tout l'arbre du depot devient lisible")
CIBLES[34] = ("c26",)
MUTANTS[35] = ("retire le refus d'`Origin`/`Host` de `do_GET` ET `do_POST` ⇒ "
               "un POST inter-origine SIMPLE peut declencher `retirer`")
CIBLES[35] = ("c27",)
MUTANTS[36] = ("INTERVERTIT la correspondance attendue de `retirer` : « la "
               "tache SURVIT » attendrait le verdict « ABSENTE ». C'est la "
               "faute DEMONTREE en worktree, que (c9) ne voyait pas")
CIBLES[36] = ("c9",)
MUTANTS[37] = ("INTERVERTIT les codes attendus du pre-vol (6 <-> 0) ⇒ le "
               "chiffre que `README.md` publie cesse d'etre celui qui sort")
CIBLES[37] = ("c28",)
MUTANTS[38] = ("verse sous `installeur/` un CINQUIEME fichier de code portant "
               "un verbe d'elevation ⇒ la population fixe le manquait")
CIBLES[38] = ("c4",)
MUTANTS[39] = ("pose dans la page une couleur en `rgb()` ⇒ une couleur qui "
               "n'est declarable NULLE PART, et qui echappait aux deux sens")
CIBLES[39] = ("c19",)
MUTANTS[40] = ("pose un SECOND `[ValidateSet]` dans l'outil ⇒ (c7) comparait "
               "les verbes exposes a un ensemble qui n'est pas le leur")
CIBLES[40] = ("c7",)

# ⚠️ LE COMPTE DU CHEMIN NORMAL. Il se PERIME si on ajoute un controle sans le
#    mettre a jour — et c'est voulu : c'est ce qui rend (z) FALSIFIABLE.
CONTROLES_PREVUS = 28

_MUTANT = 0

RE_ID_CTRL = re.compile(r"\((\w+)\)")


def ctrl(ok, libelle, detail=""):
    """UNE assertion, UNE ligne, UN identifiant. ⛔ Aucun controle muet.

    ⚠️ L'IDENTIFIANT VIT DANS LE LIBELLE, ⛔ pas dans un argument a part :
       `verif_campagne_dn56.py` lit les libelles A L'AST en prenant `args[1]`
       de chaque `ctrl(...)`. Une autre signature retrecirait SILENCIEUSEMENT
       la population de cette gate-la."""
    assert len(libelle) < LARGEUR_LIBELLE, (
        "libelle de %d colonnes (max %d) : %r — il deborderait la cle a "
        "colonne fixe de `verif_campagne_dn56.py`, qui refuse >= %d"
        % (len(libelle), LARGEUR_LIBELLE - 1, libelle, LARGEUR_LIBELLE))
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
    discriminant que `verif_campagne_dn56.py` exige de chaque mutant.

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


# ═══════════════════════ LIRE LE DEPOT ═════════════════════════════════════

def suivis():
    """Les fichiers TRACES, par `git ls-files`. ⛔ Pas un parcours du disque :
    un repertoire ignore n'est pas du depot. Rend `None` si git refuse.

    🔴 `core.quotePath=false` ET `-z` NE SONT ⛔ PAS DU CONFORT — ET LE DEPOT
       EST FRANCOPHONE. Par defaut `git ls-files` ECHAPPE tout chemin non ASCII
       et l'entoure de guillemets : le jeton ne finit alors pas par `.md` et le
       fichier quitte le corpus EN SILENCE.
    ⚠️ `encoding="utf-8"` EST OBLIGATOIRE : sans lui, `text=True` decode avec la
       locale, et sous `LC_ALL=C` un chemin accentue leve `UnicodeDecodeError` —
       un Traceback SANS `BILAN`, la signature d'une gate MORTE."""
    try:
        r = subprocess.run(["git", "-c", "core.quotePath=false",
                            "ls-files", "-z"], cwd=RACINE,
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return None
    if r.returncode != 0:
        return None
    return sorted(x for x in r.stdout.split("\0") if x.strip())


def lire(chemin):
    """Le texte d'un fichier suivi. `newline=""` GARDE les fins de ligne : sans
    lui, Python normalise `\\r\\n` en `\\n` A LA LECTURE et (c3) jurerait qu'un
    `.bat` en LF est en CRLF — un controle qui mesure son propre decodage."""
    try:
        with io.open(os.path.join(RACINE, chemin), encoding="utf-8",
                     errors="replace", newline="") as fh:
            return fh.read()
    except OSError:
        return None


def cellules(ligne):
    t = ligne.strip()
    if not t.startswith("|"):
        return None
    return [c.strip() for c in t.strip("|").split("|")]


def plat(txt):
    """Le texte SANS ses retours a la ligne — un motif ne doit ⛔ pas dependre
    de l'endroit ou la prose a ete coupee."""
    return re.sub(r"\s+", " ", txt or "")


def jetons_declares(ident):
    """Les jetons de couleur declares par `IDENTITE.md`, TABLE SEULE.

    ⚠️ ⛔ PAS UN BALAYAGE DU FICHIER : la page qui explique quelle palette elle
       REMPLACE cite forcement les couleurs remplacees. Les compter comme
       declarees ferait rougir (c19) sur la prose qui dit justement le
       contraire — un faux KO sur du contenu JUSTE."""
    return [(m.group(1), m.group(3).lower(), m.group(4), int(m.group(5)))
            for m in RE_JETON.finditer(ident or "")]


def regions_de_style(page):
    """Le bloc `<style>` et les attributs `style="…"` — ⛔ pas la prose."""
    out = [m.group(1) for m in RE_STYLE_BLOC.finditer(page or "")]
    out += [m.group(1) for m in RE_STYLE_ATTR.finditer(page or "")]
    return out


def couleurs_non_hex(page):
    """Les couleurs ecrites AUTREMENT qu'en `#rrggbb`, dans le style seul."""
    out = []
    for r in regions_de_style(page):
        for m in RE_FONCTION_COULEUR.finditer(r):
            out.append(m.group(0).strip())
        for m in RE_NOM_CSS.finditer(r):
            out.append(m.group(1))
    return sorted(set(out))


def importer_produit():
    """Importe `installeur/dn_installeur.py` — le PRODUIT, ⛔ pas son texte.

    🔴 CE QUE CET IMPORT CHANGE, ET CE QU'IL NE CHANGE PAS — ECRIT PLUTOT QUE TU.
       Les autres controles de cette gate relisent un TEXTE, que les mutants
       mutent en memoire. Celui-ci fait TOURNER le produit : un mutant textuel
       ⛔ ne l'atteint donc PAS. C'est pour ca que les mutants qui le gardent
       INVERSENT la CORRESPONDANCE ATTENDUE (`ATTENDU_*`, portees par l'etat)
       au lieu de muter la source — et c'est le bon sens de la garde : ce qui
       est verifie ici est un COMPORTEMENT, ⛔ pas une chaine de caracteres.
    ⚠️ Le module ne fait RIEN a l'import : il ne lie aucun port, n'appelle
       aucun PowerShell, n'ouvre aucun navigateur. Le patron d'import est celui
       de `tools/verif_decoupe_horloge_dn418.py`.
    🔴 MAIS LA SOURCE EST **COMPILEE ICI**, ⛔ PAS CHARGEE PAR LE MECANISME
       ORDINAIRE — ET C'EST UN PIEGE MESURE LE 2026-09-08. `exec_module()`
       consulte `__pycache__`, dont la validation repose sur (mtime, taille) :
       apres avoir demontre le defaut puis RESTAURE le fichier, la gate a
       continue de juger le BYTECODE PERIME et a rendu le meme rouge sur une
       source SAINE. Une gate qui mesure la version d'hier est pire qu'une gate
       absente : elle publie un verdict FAUX avec l'autorite d'une mesure.
       ⇒ on lit le texte et on le compile, sans jamais toucher au cache."""
    chemin = os.path.join(RACINE, PY)
    try:
        with io.open(chemin, encoding="utf-8") as fh:
            source = fh.read()
        mod = importlib.util.module_from_spec(
            importlib.util.spec_from_loader("dn_installeur_dn71", loader=None))
        mod.__file__ = chemin
        exec(compile(source, chemin, "exec"), mod.__dict__)   # noqa: S102
        return mod, None
    except Exception as exc:                              # noqa: BLE001
        return None, "%s: %s" % (type(exc).__name__, str(exc)[:90])


PS1_DE_PAPIER = ("param(\n"
                 "    [ValidateSet('etat', 'stop', 'retirer')]\n"
                 "    [string]$Action = 'etat'\n)\n")


def jouer_retirer(mod):
    """Fait jouer `retirer` TROIS FOIS contre un double de papier.

    ⛔ Rien n'est lance : `_powershell`, `tache_presente` et `_lire` sont
       remplaces le temps de l'appel, et remis en place ensuite."""
    garde = (mod._powershell, mod.tache_presente, mod._lire,
             dict(mod._PILOTE))
    out = {}
    try:
        mod._PILOTE.update(chemin=os.path.join(RACINE, OUTIL),
                           origine="double de papier")
        mod._lire = lambda _c: PS1_DE_PAPIER
        mod._powershell = lambda *a, **k: (0, "sortie de papier",
                                           ["powershell", "-File", "x", "y"],
                                           None)
        for cle, reponse in (("survit", (True, "Limited")),
                             ("absente", (False, "")),
                             ("inconnue", (None, ""))):
            mod.tache_presente = (lambda r: (lambda: r))(reponse)
            d = mod.jouer_verbe("retirer")
            out[cle] = (d.get("verdict", ""), d.get("rc"))
    except Exception as exc:                              # noqa: BLE001
        out["__erreur__"] = "%s: %s" % (type(exc).__name__, str(exc)[:80])
    finally:
        mod._powershell, mod.tache_presente, mod._lire = garde[:3]
        mod._PILOTE.clear()
        mod._PILOTE.update(garde[3])
    return out


def jouer_prevol(mod):
    """Fait jouer le PRE-VOL trois fois, et relit son CODE DE SORTIE."""
    garde = (mod.dependance_presente, mod.arbre_parent_present, mod.PAGE,
             dict(mod._PILOTE), mod.localiser_pilote, mod.lhm_present)
    out = {}
    try:
        mod._PILOTE.update(chemin=os.path.join(RACINE, OUTIL),
                           origine="double de papier")
        mod.arbre_parent_present = lambda: True
        # 🔴 LA SONDE LHM EST **REMPLACEE**, ET CA FERME DEUX CHOSES A LA FOIS :
        #    (1) sans ca, cette gate ouvrait QUATRE CONNEXIONS TCP REELLES vers
        #        la boucle locale a chaque passe — un resultat qui depend de ce
        #        qui tourne sur la machine du lecteur ⛔ n'est pas une mesure ;
        #    (2) la polarite des TROIS positions devient JOUABLE.
        mod.lhm_present = lambda: None
        tampon = io.StringIO()
        with contextlib.redirect_stdout(tampon):
            mod.dependance_presente = lambda m, s: (m != "psutil")
            out["module_manquant"] = mod.prevol(False)
            mod.dependance_presente = lambda m, s: True
            out["tout_est_la"] = mod.prevol(False)
            mod.PAGE = os.path.join(RACINE, "installeur", "page-inexistante.html")
            out["page_absente"] = mod.prevol(False)
            mod.PAGE = garde[2]
            mod.localiser_pilote = lambda: (None, "introuvable")
            out["pilote_absent"] = mod.prevol(False)
        # ⚠️ ET LE TAMPON EST **RELU**, ⛔ plus jete : ce que le pre-vol IMPRIME
        #    est ce que l'inconnu lit. Un tampon qu'on jette est un controle
        #    qui n'existe pas.
        mod.PAGE = garde[2]
        mod.localiser_pilote = garde[4]
        mod.dependance_presente = lambda m, s: True
        for cle, valeur in (("lhm_present", True), ("lhm_absent", False),
                            ("lhm_non_testable", None)):
            mod.lhm_present = (lambda v: (lambda: v))(valeur)
            vu = io.StringIO()
            with contextlib.redirect_stdout(vu):
                mod.prevol(False)
            m = RE_MOT_LHM.search(vu.getvalue())
            out[cle] = m.group(1) if m else "⛔ AUCUNE LIGNE LHM IMPRIMEE"
    except Exception as exc:                              # noqa: BLE001
        out["__erreur__"] = "%s: %s" % (type(exc).__name__, str(exc)[:80])
    finally:
        mod.dependance_presente, mod.arbre_parent_present, mod.PAGE = garde[:3]
        mod._PILOTE.clear()
        mod._PILOTE.update(garde[3])
        mod.localiser_pilote = garde[4]
        mod.lhm_present = garde[5]
    return out


def bloc_readme(txt):
    """La section d'installation du README, bornee par ses DEUX titres."""
    if A_SECTION_README not in (txt or "") or A_SECTION_SUITE not in (txt or ""):
        return None
    return txt.split(A_SECTION_README, 1)[1].split(A_SECTION_SUITE, 1)[0]


def validatesets(ps1):
    """TOUS les `[ValidateSet]` du fichier — ⛔ pas seulement le premier.

    🔴 `search()` prenait le PREMIER rencontre : le jour ou l'outil en porte un
       second (un autre parametre, une fonction interne), (c7) comparait les
       verbes exposes a un ensemble QUI N'EST PAS CELUI DU VERBE. Un ensemble
       ambigu ⛔ n'est pas un ensemble : on ROUGIT au lieu de choisir."""
    return RE_VALIDATESET.findall(ps1 or "")


def verbes_de_l_outil(ps1):
    """Les verbes que l'outil accepte VRAIMENT — relus dans son `[ValidateSet]`.

    🔴 ⛔ AUCUN NOM N'EST RECOPIE ICI. Une gate qui codait en dur `('stop',
       'retirer')` sortirait verte le jour ou l'outil renomme un verbe, et la
       page appellerait un verbe mort en silence."""
    lots = validatesets(ps1)
    if len(lots) != 1:
        return ()
    return tuple(RE_VERBE_PS.findall(lots[0]))


def verbes_exposes(py):
    m = RE_VERBES.search(py or "")
    if not m:
        return ()
    return tuple(re.findall(r'"([a-z]+)"', m.group(1)))


# ═══════════════════════ LES MUTANTS ═══════════════════════════════════════

def muter(etat):
    """REPLANTE une faute DANS L'ETAT — ⛔ jamais dans un fichier du depot.

    🔴 TOUTE mutation passe par cet unique etat, et `main()` compare l'etat
       AVANT/APRES : la garde du no-op est donc UNIVERSELLE.
    ⚠️ MAIS ELLE N'EST ATTEINTE QUE SI LE CORPS **REND**. Un corps qui `split`,
       indexe ou depaquette sur une ancre disparue LEVE, et le `try` de `main()`
       le rend en `rc=1` + `BILAN` + `[KO ]` — MOT POUR MOT le contrat que la
       campagne appelle « sain » : un mutant PERIME passerait pour un gardien
       vivant. ⇒ tout corps VERIFIE son ancre d'abord et rend `e` INCHANGE.
       ⛔ Le mutant 30 leve EXPRES : il est le temoin de ce cas."""
    e = copy.deepcopy(etat)
    p, r = e["fichiers"], e["regles"]

    if _MUTANT == 1:
        if A_LIC_LIGNE not in p.get(LIC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[LIC] = p[LIC].replace(A_LIC_LIGNE + "\n", "", 1)
    elif _MUTANT == 2:
        if A_LIC_LIGNE not in p.get(LIC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[LIC] = p[LIC].replace(
            "serves it | **GPL-3.0-or-later** | [`LICENSE`](LICENSE) |",
            "serves it | **CC-BY-SA-4.0** | [`docs/LICENSE`](docs/LICENSE) |", 1)
    elif _MUTANT == 3:
        if "\r\n" not in p.get(BAT, ""):
            return e                      # deja en LF ⇒ NO-OP ⇒ rc=3
        p[BAT] = p[BAT].replace("\r\n", "\n")
    elif _MUTANT == 4:
        if BAT not in p:
            return e                      # fichier hors corpus ⇒ NO-OP ⇒ rc=3
        # La forme du `.bat` : les deux jetons ecrits d'un bloc.
        p[BAT] += "\r\npowershell -Verb RunAs -File \"%~dp0dn.ps1\"\r\n"
    elif _MUTANT == 5:
        if PY not in p:
            return e                      # fichier hors corpus ⇒ NO-OP ⇒ rc=3
        # 🔴 LA FORME NATURELLE EN PYTHON — les deux jetons SEPARES par la
        #    virgule d'une liste d'arguments. C'est elle qui a demontre le
        #    trou de la 1re version de (c4).
        p[PY] += ('\ndef elever():\n    return subprocess.run('
                  '["powershell", "Start-Process", "-Verb", "RunAs"])\n')
    elif _MUTANT == 6:
        # 🔴 IL VISE L'AFFECTATION, ⛔ PAS LE COMMENTAIRE QUI LA CITE — ET
        #    C'EST UNE CORRECTION MESUREE : un simple `.replace()` frappait la
        #    PREMIERE occurrence, qui est le commentaire d'a cote. Le mutant
        #    sortait alors VERT sur une gate SAINE — le cas « le mutant vise a
        #    cote », ⛔ pas « la garde a un trou ».
        if not RE_PORT0.search(p.get(PY, "")):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = RE_PORT0.sub("PORT_DEMANDE = 8123", p[PY], count=1)
    elif _MUTANT == 7:
        if A_URL not in p.get(PY, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = p[PY].replace(A_URL, 'url = "file:///%s" % PAGE', 1)
    elif _MUTANT == 8:
        if A_ADRESSE not in p.get(PY, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = p[PY].replace(A_ADRESSE, 'ADRESSE = "192.168.1.20"', 1)
    elif _MUTANT == 9:
        if A_VERBES not in p.get(PY, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = p[PY].replace(
            A_VERBES, 'VERBES = ("stop", "retirer", "desinstaller")', 1)
    elif _MUTANT == 10:
        if A_VERBES not in p.get(PY, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = p[PY].replace(A_VERBES, 'VERBES = ("stop",)', 1)
    elif _MUTANT == 11:
        if A_REQUETE not in p.get(PY, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = p[PY].replace(A_REQUETE, "encore, _rl = (False, '')", 1)
    elif _MUTANT == 12:
        # ⚠️ IL RETIRE LE BRANCHEMENT, ⛔ il ne debranche pas la garde, ET ⛔ il
        #    ne touche PLUS A LA PROSE — correctif de revue. Sa 1re version
        #    substituait GLOBALEMENT les jetons, commentaires compris : elle
        #    rougissait, mais pour une raison plus LARGE que la faute qu'elle
        #    nomme, et masquait que le controle ne regardait pas le branchement.
        #    ⇒ il supprime maintenant EXACTEMENT ce qui flashe : la balise de
        #      module et l'element d'installation. La prose reste intacte.
        src = RE_SRC_MODULE.search(p.get(PAGE, ""))
        if not src or ANCRE_ELEMENT not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = re.sub(
            r"<script[^>]*\bsrc\s*=\s*[\"'][^\"']*esp-web-tools[^\"']*[\"'][^>]*>"
            r"\s*</script>", "", p[PAGE], count=1)
        debut = p[PAGE].index(ANCRE_ELEMENT)
        fin = p[PAGE].index("</esp-web-install-button>", debut)
        p[PAGE] = (p[PAGE][:debut]
                   + '<button type="button">Installer (maison)</button>'
                   + p[PAGE][fin + len("</esp-web-install-button>"):])
    elif _MUTANT == 13:
        if A_GESTE_PATH not in p.get(BAT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BAT] = p[BAT].replace(A_GESTE_PATH, "faire le necessaire")
    elif _MUTANT == 14:
        # 🔴 LA FAUTE EXACTE DE `dn6-4` : le mot « Porteur » est TOUJOURS la.
        cible = "l'agent\nen exécutable autonome, prévu en V0.2"
        if cible not in p.get(LISEZMOI, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[LISEZMOI] = p[LISEZMOI].replace(cible, "à nommer", 1)
    elif _MUTANT == 15:
        if A_GESTE_PIP not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(A_GESTE_PIP, "voir la documentation")
    elif _MUTANT == 16:
        if A_PORTEUR_H2 not in p.get(LISEZMOI, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[LISEZMOI] = p[LISEZMOI].replace(A_PORTEUR_H2,
                                          "son porteur reste\nà nommer", 1)
    elif _MUTANT == 17:
        if A_NAVIGATEURS not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(A_NAVIGATEURS, "un autre navigateur")
    elif _MUTANT == 18:
        if A_SECURE not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(A_SECURE, "true", 1)
    elif _MUTANT == 19:
        jetons = jetons_declares(p.get(IDENT, ""))
        if not jetons:
            return e                      # table disparue ⇒ NO-OP ⇒ rc=3
        src = "`%s:%d`" % (jetons[0][2], jetons[0][3])
        if src not in p[IDENT]:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[IDENT] = p[IDENT].replace(src, "`le firmware`", 1)
    elif _MUTANT == 20:
        jetons = jetons_declares(p.get(IDENT, ""))
        if not jetons:
            return e                      # table disparue ⇒ NO-OP ⇒ rc=3
        src = "`%s:%d`" % (jetons[0][2], jetons[0][3])
        if src not in p[IDENT]:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[IDENT] = p[IDENT].replace(
            src, "`%s:%d`" % (jetons[0][2], jetons[0][3] + 3), 1)
    elif _MUTANT == 21:
        if PAGE not in p:
            return e                      # fichier hors corpus ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace("--dn-fond: #000000;",
                                  "--dn-fond: #000000;\n    --dn-neuf: #1af1ce;",
                                  1)
        if "--dn-neuf" not in p[PAGE]:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
    elif _MUTANT == 22:
        # ⚠️ LA COULEUR AJOUTEE EST **VRAIE** A LA LIGNE CITEE : le mutant vise
        #    le SENS « declaree mais non employee », ⛔ pas la citation.
        ligne = ("| `--dn-fantome` | jamais employé | `#50c0ff` | "
                 "`firmware/desknode/main/dn_ui.c:3460` | *(bordure)* |\n")
        ancre = "| `--dn-alerte` |"
        if ancre not in p.get(IDENT, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[IDENT] = p[IDENT].replace(ancre, ligne + ancre, 1)
    elif _MUTANT == 23:
        if PAGE not in p:
            return e                      # fichier hors corpus ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace("--dn-fond: #000000;",
                                  "--dn-fond: #0d1117;", 1)
        if "#0d1117" not in p[PAGE]:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
    elif _MUTANT == 24:
        if A_SECTION_SUITE not in p.get(LISEZMOI, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[LISEZMOI] = p[LISEZMOI].replace(
            A_SECTION_SUITE,
            "| geste | ce qu'il fait |\n|---|---|\n"
            "| `permanence` | pose la tache au logon |\n"
            "| `prevol` | le pre-vol |\n"
            "| `lancer` | lance l'agent |\n\n" + A_SECTION_SUITE, 1)
    elif _MUTANT == 25:
        cible = "| `dn7` | The install side:"
        if cible not in p.get(ROADMAP, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        lignes = p[ROADMAP].split("\n")
        for i, l in enumerate(lignes):
            if l.startswith(cible):
                lignes[i] = re.sub(r"\|\s*in progress\s*\|\s*$",
                                   "| not started |", l)
                break
        p[ROADMAP] = "\n".join(lignes)
    elif _MUTANT == 26:
        # ⚠️ LA VICTIME EST **DERIVEE**, ⛔ pas codee en dur : viser un mutant
        #    par son numero cesse de marcher le jour ou son controle gagne un
        #    SECOND gardien.
        compte = {}
        for _n, _v in e["cibles"].items():
            for _c in _v:
                compte[_c] = compte.get(_c, 0) + 1
        for _n, _v in sorted(e["cibles"].items()):
            if any(compte[_c] == 1 for _c in _v):
                e["cibles"][_n] = ()
                break
    elif _MUTANT == 27:
        e["cibles"][27] = tuple(e["cibles"][27]) + ("c99",)
    elif _MUTANT == 28:
        e["cibles"][99] = ("c9",)      # une cible pour un mutant INEXISTANT
    elif _MUTANT == 29:
        r["sortie_anticipee"] = True
    elif _MUTANT == 30:
        # 🔴 IL LEVE EXPRES : c'est la faute « un mutant declare qui MEURT ».
        raise AssertionError("mutant 30 : corps volontairement LEVANT")
    elif _MUTANT == 31:
        if PAGE not in p:
            return e                      # fichier hors corpus ⇒ NO-OP ⇒ rc=3
        p[PAGE] = ""
    elif _MUTANT == 32:
        if IDENT not in p:
            return e                      # fichier hors corpus ⇒ NO-OP ⇒ rc=3
        del p[IDENT]
        e["traces"] = tuple(f for f in e["traces"] if f != IDENT)
    elif _MUTANT == 33:
        if A_REGLE_EOL not in p.get(ATTRIBUTS, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[ATTRIBUTS] = p[ATTRIBUTS].replace(A_REGLE_EOL, "*.bat text", 1)
    elif _MUTANT == 34:
        if A_BLANCHE not in p.get(PY, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = p[PY].replace(
            A_BLANCHE,
            "        if True:\n"
            "            fichier = os.path.join(RACINE, chemin.lstrip('/'))\n"
            "            ctype = 'text/plain; charset=utf-8'\n", 1)
    elif _MUTANT == 35:
        if A_GARDE_GET not in p.get(PY, "") or A_GARDE_POST not in p.get(PY, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PY] = p[PY].replace(A_GARDE_GET, "    def do_GET(self):\n", 1)
        p[PY] = p[PY].replace(A_GARDE_POST, "    def do_POST(self):\n", 1)
    elif _MUTANT == 36:
        # ⚠️ IL MUTE LA CORRESPONDANCE ATTENDUE, ⛔ pas la source : le produit
        #    est deja IMPORTE, et un mutant textuel ne l'atteint pas. Le
        #    controle rougit parce que le produit ⛔ ne fait PAS ce que la
        #    correspondance INVERSEE annonce.
        a = e["attendu_retirer"]
        if "survit" not in a or "absente" not in a:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        a["survit"], a["absente"] = a["absente"], a["survit"]
    elif _MUTANT == 37:
        a = e["attendu_prevol"]
        if "module_manquant" not in a or "tout_est_la" not in a:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        a["module_manquant"], a["tout_est_la"] = (a["tout_est_la"],
                                                  a["module_manquant"])
    elif _MUTANT == 38:
        neuf_fichier = DOSSIER + "/dn_outil_neuf.py"
        if neuf_fichier in p:
            return e                      # deja la ⇒ NO-OP ⇒ rc=3
        p[neuf_fichier] = ('# un outil verse plus tard sous installeur/\n'
                           'def elever():\n'
                           '    return ["powershell", "-Verb", "RunAs"]\n')
        e["traces"] = tuple(sorted(set(e["traces"]) | {neuf_fichier}))
    elif _MUTANT == 39:
        ancre = "color: var(--dn-accent);"
        if ancre not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(ancre, "color: rgb(160, 216, 255);", 1)
    elif _MUTANT == 40:
        ancre = "[ValidateSet("
        if ancre not in p.get(OUTIL, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[OUTIL] += ("\n# un second jeu de verbes, ailleurs dans le fichier\n"
                     "# [ValidateSet('alpha', 'beta')]\n"
                     "[ValidateSet('alpha', 'beta')]\n")
    else:
        raise AssertionError("mutant %d declare mais SANS CORPS" % _MUTANT)
    return e


# ═══════════════════════════ LES CONTROLES ═════════════════════════════════

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
    """Les identifiants de TOUS les `ctrl(...)` de CE fichier, lus A L'AST.

    🔴 POURQUOI PAS `set(ids_emis)` : ce set est fige AU MOMENT DE L'APPEL de
       (c23). Tout controle ajoute APRES ce bloc en sortirait INVISIBLE a la
       reciproque."""
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
        # ⛔ PAS `sys.exit(...)`, qui rendrait 1 et se confondrait avec un vrai
        #    defaut : un mutant inconnu est une ERREUR D'APPEL.
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
    print("dn7-1 — L'INSTALLEUR EST NON ELEVE, LOCAL, ET IL EXPOSE CE QUI EXISTE"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)
    print("cibles     : %s/  +  %s  +  %s  +  %s" % (DOSSIER, LIC, LISEZMOI,
                                                     ROADMAP))
    print("⛔ CETTE GATE NE LANCE RIEN : aucun port ouvert, aucun PowerShell "
          "appele,\n   aucune tache demandee. Elle relit ce que le depot "
          "PUBLIE.")

    traces = suivis()
    if traces is None:
        ctrl(False, "(c0) l'arbre trace est LISIBLE",
             "⛔ `git ls-files` a refuse — ⛔ pas de parcours de disque en "
             "remplacement : un repertoire ignore n'est pas du depot")
        return bilan(1, "l'arbre trace est illisible")

    fichiers, illisibles = {}, []
    for f in FIXES:
        t = lire(f)
        if t is None:
            illisibles.append(f)
        else:
            fichiers[f] = t
    # Les fichiers de firmware CITES par l'identite entrent au corpus : (c18)
    # doit pouvoir rouvrir la source, et un mutant doit pouvoir la deplacer.
    for _j, _v, chemin, _l in jetons_declares(fichiers.get(IDENT, "")):
        if chemin not in fichiers:
            t = lire(chemin)
            if t is not None:
                fichiers[chemin] = t
    if illisibles:
        ctrl(False, "(c0) tout fichier attendu est LISIBLE",
             "⛔ ABSENT(S) OU ILLISIBLE(S) : %s — la population des controles "
             "serait RETRECIE en silence" % " · ".join(illisibles))
        return bilan(1, "%d fichier(s) attendu(s) illisible(s)" % len(illisibles))

    etat = {"fichiers": fichiers,
            "traces": tuple(traces),
            "cibles": {n: tuple(v) for n, v in CIBLES.items()},
            # ⚠️ LES CORRESPONDANCES ATTENDUES VIVENT DANS L'ETAT : c'est ce qui
            #    rend les controles FONCTIONNELS mutables — un mutant textuel
            #    ⛔ n'atteint pas un module deja importe.
            "attendu_retirer": {k: tuple(v) for k, v in ATTENDU_RETIRER.items()},
            "attendu_prevol": dict(ATTENDU_PREVOL),
            "regles": {"sortie_anticipee": False}}

    # 🔴 UN MUTANT QUI MEURT SORTIRAIT EN TRACEBACK, SANS `BILAN` — or « pas de
    #    BILAN » est le discriminant d'une gate MORTE. ⇒ il se rend en KO.
    try:
        neuf = muter(etat) if _MUTANT else etat
    except Exception as exc:                              # noqa: BLE001
        ctrl(False, "(c0) le mutant %d a une CIBLE et un CORPS" % _MUTANT,
             "⛔ %s: %s — la faute est dans le MUTANT, ⛔ pas dans la gate"
             % (type(exc).__name__, str(exc)[:80]))
        return bilan(1, "le mutant %d n'a pas pu s'appliquer" % _MUTANT)
    # 🔴 UN MUTANT SANS EFFET EST INVISIBLE AU CONTRAT DE LA CAMPAGNE.
    if _MUTANT and neuf == etat:
        ctrl(False, "(c0) le mutant %d a bien un EFFET" % _MUTANT,
             "⛔ SANS EFFET — son ancre litterale a disparu de la cible. "
             "⛔ Ce n'est PAS un controle vert : rc=3, mutant PERIME.")
        return bilan(3, "le mutant %d n'a eu aucun effet" % _MUTANT)

    f = neuf["fichiers"]
    traces = list(neuf["traces"])
    cibles, regles = neuf["cibles"], neuf["regles"]
    att_ret, att_pre = neuf["attendu_retirer"], neuf["attendu_prevol"]
    bat = f.get(BAT, "")
    py = f.get(PY, "")
    page = f.get(PAGE, "")
    ident = f.get(IDENT, "")
    lic = f.get(LIC, "")
    readme = f.get(LISEZMOI, "")
    roadmap = f.get(ROADMAP, "")
    ps1 = f.get(OUTIL, "")
    attributs = f.get(ATTRIBUTS, "")
    # 🔴 LA POPULATION DU CODE EST **DERIVEE**, ⛔ plus ecrite a la main.
    code = fichiers_de_code(traces, f)

    # ⚠️ LE PRODUIT EST IMPORTE UNE SEULE FOIS. Un echec d'import ⛔ ne fait
    #    PAS taire (c9)/(c26)/(c28) : il les fait ROUGIR avec son motif.
    produit, err_produit = importer_produit()

    # ── (c1) LE DOSSIER EXISTE, IL EST SUIVI, ET IL N'EST PAS VIDE ─────────
    print("\n── (c1) LE DOSSIER `installeur/` EST AU DEPOT ────────────────────")
    absents = [x for x in QUATRE if x not in traces or not f.get(x, "").strip()]
    if not ctrl(not absents,
                "(c1) les quatre fichiers de `installeur/` sont SUIVIS",
                "%s" % " · ".join(QUATRE) if not absents
                else "⛔ ABSENT(S), NON SUIVI(S) OU VIDE(S) : %s — ⛔ un vide "
                     "n'est pas une absence de defaut" % " · ".join(absents)):
        return bilan(1, "le dossier de l'installeur est incomplet")

    # ── (c2) LE CLASSEMENT DE LICENCE, PREALABLE AU PREMIER COMMIT ─────────
    print("\n── (c2) LE DOSSIER NEUF EST CLASSE ───────────────────────────────")
    ligne_lic, licence_lic, fichier_lic = None, None, None
    for m in re.finditer(
            r"^\|\s*`([^`]+)`[^|]*\|\s*\*\*([^*]+)\*\*\s*\|\s*(.*?)\s*\|\s*$",
            lic, re.M):
        if m.group(1).rstrip("/") == DOSSIER:
            ligne_lic = m.group(0)
            licence_lic = m.group(2).strip()
            mf = re.search(r"\[`([^`]+)`\]", m.group(3))
            fichier_lic = mf.group(1) if mf else None
    dit_gpl = False
    if fichier_lic:
        t = lire(fichier_lic) or ""
        dit_gpl = ("GNU GENERAL PUBLIC LICENSE" in t and "Version 3" in t)
    ctrl(bool(ligne_lic) and licence_lic == "GPL-3.0-or-later" and dit_gpl,
         "(c2) `installeur/` est classe dans `LICENSING.md`",
         "%s ⇒ %s" % (licence_lic, fichier_lic)
         if ligne_lic and licence_lic == "GPL-3.0-or-later" and dit_gpl
         else "⛔ %s — un repertoire de 1er niveau non classe fait ROUGIR "
              "`verif_licences_dn52.py`, qui garde DANS LES DEUX SENS"
              % ("aucune ligne de table" if not ligne_lic
                 else "annonce %r, ⛔ pas le copyleft du binaire servi"
                      % licence_lic if licence_lic != "GPL-3.0-or-later"
                 else "le fichier cite (%s) ne DIT pas la GPL-3" % fichier_lic))

    # ── (c3) UN SEUL POINT D'ENTREE, ET IL EST EN CRLF ─────────────────────
    print("\n── (c3) LE POINT D'ENTREE ────────────────────────────────────────")
    bats = [x for x in traces if x.startswith(DOSSIER + "/")
            and x.lower().endswith(".bat")]
    crlf = "\r\n" in bat and "\n" not in bat.replace("\r\n", "")
    # 🔴 ⛔ « IL EST EN CRLF DANS MON ARBRE » NE PROUVE RIEN — le cloneur, lui,
    #    recoit ce que `.gitattributes` fait LIVRER. Mesure du 2026-09-08 :
    #    `git ls-files --eol` rendait `i/lf` pour `tools/dn-agent.bat`, le
    #    precedent que ce fichier cite. Une normalisation au commit resterait
    #    donc VERTE tout en livrant du LF a l'inconnu.
    regle = A_REGLE_EOL in attributs
    livre = ""
    try:
        r = subprocess.run(["git", "ls-files", "--eol", "--", BAT], cwd=RACINE,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        livre = r.stdout if r.returncode == 0 else ""
    except OSError:
        livre = ""
    livraison = "eol=crlf" in livre
    ctrl(bats == [BAT] and crlf and regle and livraison,
         "(c3) le point d'entree est UNIQUE et LIVRE en CRLF",
         "%s — %d ligne(s), `%s`, et git le LIVRE en CRLF"
         % (BAT, bat.count("\r\n"), A_REGLE_EOL)
         if bats == [BAT] and crlf and regle and livraison
         else "⛔ %s" % ("%d fichier(s) `.bat` : %s — ⛔ « UNE chose a lancer » "
                        "veut dire une" % (len(bats), " · ".join(bats) or "—")
                        if bats != [BAT] else
                        "fins de ligne LF dans l'arbre : cmd.exe peut executer "
                        "une ligne TRONQUEE (`tools/dn-agent.bat:29-32`)"
                        if not crlf else
                        "⛔ `%s` ABSENT de `%s` — ce que git LIVRE n'est garanti "
                        "par RIEN" % (A_REGLE_EOL, ATTRIBUTS) if not regle else
                        "`git ls-files --eol` ne rend pas `eol=crlf` : %r"
                        % livre.strip()[:60]))

    # ── (c4) ⛔ AUCUNE ELEVATION, ET C'EST MECANIQUE ───────────────────────
    print("\n── (c4) ⛔ AUCUNE ELEVATION DANS LE CODE LIVRE ───────────────────")
    eleves = []
    for x in code:
        src = f.get(x, "")
        for nom, motif in MOTIFS_ELEVATION:
            if motif.search(src):
                eleves.append("%s ⇒ %s" % (x, nom))
    ctrl(not eleves, "(c4) aucun jeton d'elevation dans le code livre",
         "%d fichier(s) DERIVES relus, %d motif(s) cherches"
         % (len(code), len(MOTIFS_ELEVATION)) if not eleves
         else "⛔ %s — la garde de `%s:737` `Stop2` sur tout RunLevel qui n'est "
              "pas `Limited` : un installeur eleve ferait ECHOUER l'outil qui "
              "existe" % (" · ".join(eleves), OUTIL))

    # ── (c5)(c6) LE PORT EST TIRE, L'ADRESSE EST LA BOUCLE LOCALE ──────────
    print("\n── (c5)(c6) SERVIR EN LOCAL, SUR UN PORT TIRE ────────────────────")
    adr_port = [x for x in code if RE_ADR_PORT.search(f.get(x, ""))]
    tire = bool(RE_PORT0.search(py)) and A_LU in py and A_BIND in py
    ctrl(tire and not adr_port,
         "(c5) le port est TIRE a l'execution, ⛔ pas en dur",
         "`%s` puis relecture de `%s`" % (A_PORT0, A_LU)
         if tire and not adr_port
         else "⛔ %s — `H6` dit qu'un port fixe peut etre DEJA PRIS, et le "
              "deuxieme lancement est le cas NOMINAL de tout le monde"
              % ("port ecrit en dur dans %s" % " · ".join(adr_port)
                 if adr_port else "le `bind` sur 0 ou sa relecture ont disparu"))

    fileurl = [x for x in code if "file://" in f.get(x, "")]
    boucle = A_ADRESSE in py and A_URL in py
    ctrl(boucle and not fileurl,
         "(c6) l'adresse annoncee est la boucle locale + le port lu",
         "`%s`" % A_URL if boucle and not fileurl
         else "⛔ %s — Web Serial n'existe QUE en contexte securise, et "
              "`http://localhost` est le seul chemin MESURE"
              % ("`file://` dans %s" % " · ".join(fileurl) if fileurl
                 else "l'adresse annoncee n'est plus batie sur `127.0.0.1` et "
                      "le port reellement lie"))

    # ── (c7)(c8) EXPOSER, ⛔ PAS CONSTRUIRE ────────────────────────────────
    print("\n── (c7)(c8) LES DEUX GESTES APPELLENT CE QUI EXISTE ──────────────")
    lots = validatesets(ps1)
    valides = verbes_de_l_outil(ps1)
    exposes = verbes_exposes(py)
    inconnus = [v for v in exposes if v not in valides]
    ctrl(len(lots) == 1 and bool(valides) and bool(exposes) and not inconnus,
         "(c7) tout verbe expose est dans le `[ValidateSet]` relu",
         "%d expose(s) sur %d acceptes : %s"
         % (len(exposes), len(valides), " · ".join(exposes))
         if len(lots) == 1 and valides and exposes and not inconnus
         else "⛔ %s" % ("%d `[ValidateSet]` dans %s — un ensemble AMBIGU n'est "
                        "pas un ensemble, et le premier venu n'est pas "
                        "forcement celui du verbe" % (len(lots), OUTIL)
                        if len(lots) != 1 else
                        "le `[ValidateSet]` de %s ne se lit pas" % OUTIL
                        if not valides else
                        "aucun verbe expose ne se lit dans %s" % PY
                        if not exposes else
                        "verbe(s) INEXISTANT(S) : %s — la page REIMPLEMENTE au "
                        "lieu d'exposer" % " · ".join(inconnus)))

    deux = ("stop" in exposes and "retirer" in exposes
            and 'jouer("stop"' in page and 'jouer("retirer"' in page)
    ctrl(deux, "(c8) les DEUX gestes existent : `stop` et `retirer`",
         "la page les appelle tous les deux" if deux
         else "⛔ il en manque un — sans `retirer`, l'inconnu qui essaie et "
              "n'aime pas garde une tache qui se relance a chaque session")

    # ── (c9) LE RETRAIT SE VERIFIE PAR REQUETE — ET IL EST **JOUE** ───────
    print("\n── (c9) LE RETRAIT SE VERIFIE, ⛔ IL NE SE CROIT PAS ─────────────")
    # 🔴 DEUX MOITIES, ET IL EN FALLAIT DEUX. La 1re version ne cherchait que la
    #    PRESENCE de `tache_presente(` apres l'ancre : intervertir les branches
    #    `is True` / `is False` faisait dire « ABSENTE » a une tache qui SURVIT,
    #    `rc` inchange a 0, et la gate restait a 25 OK / 0 KO. Une presence
    #    ⛔ n'est pas une CORRESPONDANCE.
    fenetre = ""
    if A_RETIRER in py:
        fenetre = py.split(A_RETIRER, 1)[1][:1200]
    requete = ("tache_presente(" in fenetre and "Get-ScheduledTask" in py)
    joue = jouer_retirer(produit) if produit else {"__erreur__": err_produit}
    ecarts = []
    if "__erreur__" in joue:
        ecarts.append("le produit n'a pas pu etre joue : %s" % joue["__erreur__"])
    else:
        for cle, (motif, rc_attendu) in sorted(att_ret.items()):
            verdict, rc = joue.get(cle, ("", None))
            if motif not in verdict or rc != rc_attendu:
                ecarts.append("%s ⇒ rc=%r verdict=%r (attendu %r / rc=%r)"
                              % (cle, rc, verdict[:44], motif, rc_attendu))
    ctrl(requete and not ecarts,
         "(c9) le retrait est verifie PAR REQUETE, et c'est JOUE",
         "3 etats joues contre un double de papier : %s"
         % " · ".join("%s→rc %s" % (k, joue[k][1]) for k in sorted(joue))
         if requete and not ecarts
         else "⛔ %s" % ("aucune re-interrogation apres le verbe — le message de "
                        "sortie de l'outil ⛔ ne fait pas foi" if not requete
                        else " · ".join(ecarts)))

    # ── (c26)(c27) LE SERVEUR NE SERT QUE SA PAGE, ET QU'A ELLE ──────────
    print("\n── (c26)(c27) LE SERVEUR LOCAL N'EST PAS UNE PORTE ───────────────")
    # 🔴 UNE LISTE BLANCHE, ⛔ PAS UN SERVEUR DE FICHIERS. Le commentaire du
    #    produit enoncait deja la menace ; ⛔ rien ne la gardait. Un
    #    `SimpleHTTPRequestHandler` a la place, et tout l'arbre du depot devient
    #    lisible par n'importe quelle page ouverte dans ce navigateur.
    arbo = [j for j in JETONS_ARBORESCENTS if j in py.lower()]
    hors = []
    if produit is not None:
        base = os.path.abspath(RACINE) + os.sep
        for _u, (fichier, _c) in getattr(produit, "SERVIS", {}).items():
            if not os.path.abspath(fichier).startswith(base):
                hors.append(fichier)
        mro = [c.__name__ for c in getattr(produit, "Poignee", object).__mro__]
    else:
        mro = []
    blanche = (A_BLANCHE in py and not arbo and not hors
               and "SimpleHTTPRequestHandler" not in mro)
    ctrl(blanche, "(c26) le serveur ne sert qu'une LISTE BLANCHE",
         "%d adresse(s) servies, toutes sous la racine"
         % len(getattr(produit, "SERVIS", {})) if blanche
         else "⛔ %s" % ("jeton(s) de serveur de fichiers : %s" % " · ".join(arbo)
                        if arbo else
                        "chemin(s) servi(s) HORS de la racine : %s"
                        % " · ".join(hors) if hors else
                        "`Poignee` derive de SimpleHTTPRequestHandler"
                        if "SimpleHTTPRequestHandler" in mro else
                        "la recherche `if chemin in SERVIS:` a disparu de "
                        "`do_GET` — un chemin arbitraire serait servi"))

    # 🔴 LE PORT TIRE N'EST PAS UN SECRET, ET UN POST SIMPLE NE FAIT PAS DE
    #    PRE-VOL CORS : sans ce refus, n'importe quelle page ouverte dans le
    #    meme navigateur pourrait declencher `retirer`, et `/api/etat` serait
    #    lisible par re-liaison DNS.
    garde = (A_GARDE_GET in py and A_GARDE_POST in py
             and "def _refus(self):" in py and "403" in py
             and '"Host"' in py and '"Origin"' in py)
    ctrl(garde, "(c27) `Origin` et `Host` sont refuses, sur les 2 verbes",
         "`_garde()` ouvre `do_GET` ET `do_POST`, et rend 403" if garde
         else "⛔ le refus manque a `do_GET`, a `do_POST`, ou `_refus()` ne "
              "confronte plus `Host` ET `Origin` — un POST inter-origine "
              "SIMPLE n'a ⛔ aucun pre-vol CORS a franchir")

    # ── (c28) LES CODES DE SORTIE DU PRE-VOL SONT **JOUES** ──────────────
    print("\n── (c28) LE PRE-VOL REND LES CODES QUE LE README PUBLIE ──────────")
    pv = jouer_prevol(produit) if produit else {"__erreur__": err_produit}
    ecarts_pv = []
    if "__erreur__" in pv:
        ecarts_pv.append("le produit n'a pas pu etre joue : %s" % pv["__erreur__"])
    else:
        for cle, attendu in sorted(att_pre.items()):
            if pv.get(cle) != attendu:
                ecarts_pv.append("%s ⇒ %r (attendu %r)" % (cle, pv.get(cle), attendu))
    ctrl(not ecarts_pv, "(c28) les codes de sortie du pre-vol sont JOUES",
         "%d cas joues : %s" % (len(pv), " · ".join("%s→%s" % (k, pv[k])
                                              for k in sorted(pv)))
         if not ecarts_pv
         else "⛔ %s — `README.md` publie le `6` comme « l'instrument mecanique "
              "de l'ecart », et `AC7.1.6` se ferme dessus"
              % " · ".join(ecarts_pv))

    # ── (c10) LE BRANCHEMENT DU FLASH EST LIVRE — CONTROLE **RETOURNE** ───
    print("\n── (c10) LE PERIMETRE : LE FLASH EST BRANCHE ─────────────────────")
    # 🔴 CE CONTROLE DISAIT L'INVERSE JUSQU'AU 2026-09-08, ET SON MOTIF EST
    #    GARDE A COTE DE `JETONS_FLASH_BRANCHEMENT` : il interdisait ces jetons
    #    tant que `dn7-1` excluait le flash. La frontiere a bouge avec `dn7-2` ;
    #    ⛔ le controle n'est pas SUPPRIME, il est INVERSE — sinon plus rien ne
    #    verrait quelqu'un debrancher le flash de la page.
    src_flash = RE_SRC_MODULE.search(page)
    absents_flash = []
    if not src_flash:
        absents_flash.append("la balise `<script src=…esp-web-tools…>`")
    if ANCRE_ELEMENT not in page:
        absents_flash.append("l'element `%s…`" % ANCRE_ELEMENT)
    elif ANCRE_MANIFESTE not in page:
        absents_flash.append("l'attribut `%s`" % ANCRE_MANIFESTE)
    ctrl(not absents_flash, "(c10) le branchement du flash EST dans la page",
         "module chargé et element present : %s"
         % (src_flash.group(1)[:52] if src_flash else "—")
         if not absents_flash
         else "⛔ ABSENT(S) de %s : %s — la page n'a plus de quoi poser le "
              "firmware, et un inconnu qui la traverse repartirait avec une "
              "carte vierge" % (PAGE, " · ".join(absents_flash)))

    # ── (c11) LE `.bat` DIT LE GESTE, ⛔ IL NE PLANTE PAS ──────────────────
    print("\n── (c11) SANS PYTHON, LE `.bat` DIT QUOI FAIRE ───────────────────")
    geste = (A_PYTHON_ABSENT in bat and A_GESTE_PATH in bat
             and "python.org" in bat and 'set "RC=3"' in bat)
    ctrl(geste, "(c11) le `.bat` donne le geste EXACT sans Python",
         "il nomme l'installeur officiel et la case a cocher" if geste
         else "⛔ le message, la case `%s`, l'adresse officielle ou le code de "
              "retour non nul manquent — un refus qui n'explique rien est le "
              "defaut meme que cette marche corrige" % A_GESTE_PATH)

    # ── (c12)(c13)(c14) LES ECARTS SONT ECRITS, AVEC LEUR PORTEUR ─────────
    print("\n── (c12)(c13)(c14) LES ECARTS PORTENT LEUR PORTEUR ───────────────")
    pl = plat(readme)
    porteur = ""
    if A_PORTEUR in pl:
        apres = pl.split(A_PORTEUR, 1)[1]
        apres = apres.split(":", 1)[1] if ":" in apres[:80] else apres
        # ⚠️ ON COUPE SUR `**`, ⛔ PAS SUR LE POINT : le porteur lui-meme
        #    porte un point (« V0.2 »), et couper dessus rendrait « V0 »
        #    — un controle qui rougirait sur la redaction CORRECTE.
        porteur = apres[:200].split("**")[0].strip(" *«».")
    bon_porteur = (porteur.strip().lower() not in REFUS_PORTEUR
                   and "V0.2" in porteur and A_GESTE_PIP in readme)
    ctrl(bon_porteur, "(c12) le README ecrit l'ecart avec SON PORTEUR",
         "porteur : %s" % porteur[:60] if bon_porteur
         else "⛔ %r — ⛔ un ecart sans porteur ECRIT est un oubli deguise, et "
              "« a nommer » n'est PAS un porteur" % (porteur[:60] or "absent"))

    ecart_page = (A_GESTE_PIP in page and "écart déclaré" in page
                  and "V0.2" in page)
    ctrl(ecart_page, "(c13) la page porte l'ecart, son geste et son porteur",
         "le geste et le porteur sont lisibles sans derouler" if ecart_page
         else "⛔ le geste `%s`, la mention d'ecart declare ou le porteur "
              "manquent a la page" % A_GESTE_PIP)

    residuel = (A_RESIDUEL in readme and "Zone.Identifier" in readme
                and A_PORTEUR_H2 in readme)
    ctrl(residuel, "(c14) le residuel de la Marque du Web a un porteur",
         "reproduit fidelement ; la release, elle, n'existe pas ⇒ porteur ecrit"
         if residuel
         else "⛔ le residuel n'est pas ecrit, ou son porteur a disparu — ⛔ un "
              "« ca marche depuis le depot » ne ferme pas cette moitie")

    # ── (c15)(c16) LES DEUX ETATS D'ECHEC DE LA PAGE ──────────────────────
    print("\n── (c15)(c16) LA PAGE DIT CE QUI NE VA PAS, DANS SES MOTS ────────")
    dit_serie = (A_UNSUPPORTED in page and A_SERIAL in page
                 and A_NAVIGATEURS in page and "Chrome" in page)
    ctrl(dit_serie, "(c15) la page dit l'acces serie ABSENT et ou aller",
         "elle teste `navigator.serial` et nomme deux navigateurs"
         if dit_serie
         else "⛔ l'etat `unsupported`, le test de `navigator.serial` ou le nom "
              "des navigateurs manque — ⛔ une page muette n'est pas un etat")

    dit_contexte = (A_NOT_ALLOWED in page and A_SECURE in page
                    and A_ADRESSE_PAGE in page)
    ctrl(dit_contexte, "(c16) la page dit le contexte non securise et l'adresse",
         "elle teste `isSecureContext` et donne la forme de l'adresse"
         if dit_contexte
         else "⛔ le test de contexte securise ou l'adresse correcte manque — "
              "hors contexte securise le navigateur retire l'acces serie SANS "
              "RIEN DIRE")

    # ── (c17)(c18)(c19)(c20) L'IDENTITE EST STATUEE, ECRITE, ET GARDEE ────
    print("\n── (c17)(c18)(c19)(c20) L'IDENTITE VISUELLE ──────────────────────")
    jetons = jetons_declares(ident)
    ctrl(len(jetons) >= 7,
         "(c17) chaque jeton cite SON fichier ET SA ligne",
         "%d jeton(s) declares : %s" % (len(jetons),
                                        " · ".join(j[0] for j in jetons))
         if len(jetons) >= 7
         else "⛔ %d jeton(s) lisibles dans la table de `%s` — une couleur sans "
              "source rouvrable est une couleur choisie a l'oeil"
              % (len(jetons), IDENT))

    faux = []
    for nom, val, chemin, num in jetons:
        src = f.get(chemin)
        if src is None:
            faux.append("%s ⇒ %s hors corpus" % (nom, chemin))
            continue
        lignes = src.split("\n")
        if num < 1 or num > len(lignes):
            faux.append("%s ⇒ %s:%d hors bornes" % (nom, chemin, num))
            continue
        if val.replace("#", "0x") not in lignes[num - 1].lower():
            faux.append("%s ⇒ %s:%d ne porte pas %s" % (nom, chemin, num, val))
    ctrl(bool(jetons) and not faux,
         "(c18) chaque couleur EST a la ligne de firmware citee",
         "%d source(s) rouverte(s)" % len(jetons) if jetons and not faux
         else "⛔ %s — une citation qui a pourri se remarque ICI, ⛔ pas six "
              "mois plus tard" % (" · ".join(faux) or "aucun jeton a rouvrir"))

    declarees = {j[1] for j in jetons}
    employees = {x.lower() for x in RE_HEX6.findall(page)}
    courtes = RE_HEX3.findall(page)
    nues = sorted(employees - declarees)
    dormantes = sorted(declarees - employees)
    # 🔴 ET LES NOTATIONS QUI NE SONT PAS DU `#rrggbb` : un `rgb`, un `hsl`
    #    ou un nom CSS passait sans etre declare NULLE PART — l'identite
    #    « statuee et ecrite » redevenait contournable en une ligne de style.
    autres = couleurs_non_hex(page)
    ctrl(not nues and not dormantes and not courtes and not autres
         and bool(declarees),
         "(c19) page ⇄ IDENTITE.md : les memes couleurs, 2 sens",
         "%d couleur(s), des deux cotes, et aucune hors `#rrggbb`"
         % len(declarees)
         if declarees and not nues and not dormantes and not courtes
         and not autres
         else "⛔ employees SANS etre declarees : %s · declarees SANS servir : "
              "%s · forme courte : %s · notation NON declarable (rgb/hsl/nom "
              "CSS) : %s"
              % (" ".join(nues) or "—", " ".join(dormantes) or "—",
                 " ".join(courtes) or "—", " ".join(autres) or "—"))

    banc = [c for c in PALETTE_BANC if c in page.lower()]
    ctrl(not banc, "(c20) ⛔ aucune couleur du banc d'essai dans la page",
         "%d couleur(s) de GitHub cherchees, 0 trouvee" % len(PALETTE_BANC)
         if not banc
         else "⛔ %s — l'identite serait HERITEE du prototype au lieu d'etre "
              "statuee" % " ".join(banc))

    # ── (c21) LE README RENVOIE, ⛔ IL NE DUPLIQUE PAS ─────────────────────
    print("\n── (c21) LE README RENVOIE AUX VERBES DEJA DOCUMENTES ────────────")
    bloc = bloc_readme(readme)
    redits = []
    if bloc is not None:
        for v in valides:
            if v not in ("stop", "retirer") and ("`%s`" % v) in bloc:
                redits.append(v)
    ctrl(bloc is not None and A_RENVOI in (bloc or "") and not redits,
         "(c21) le README RENVOIE aux verbes, ⛔ il ne les redit pas",
         "renvoi vers la section existante, %d verbe(s) redit(s)" % len(redits)
         if bloc is not None and A_RENVOI in bloc and not redits
         else "⛔ %s" % ("la section d'installation ne se delimite pas"
                        if bloc is None else
                        "aucun renvoi vers « %s »" % A_RENVOI
                        if A_RENVOI not in bloc else
                        "verbe(s) DUPLIQUE(S) : %s — deux tables des memes "
                        "verbes divergeront" % " · ".join(redits)))

    # ── (c22) LA ROADMAP DIT L'ETAT DU COMMIT QUI LA PUBLIE ───────────────
    print("\n── (c22) `docs/roadmap.md` DIT CE QUE CE COMMIT LIVRE ────────────")
    etats = {}
    for m in RE_LIGNE_ROADMAP.finditer(roadmap):
        etats[m.group(1)] = m.group(3).strip()
    ok_roadmap = ("dn7-1" in etats and etats.get("dn7", "") not in
                  ("", "not started"))
    ctrl(ok_roadmap, "(c22) `docs/roadmap.md` definit la marche et son etat",
         "dn7 = %r · dn7-1 = %r" % (etats.get("dn7"), etats.get("dn7-1"))
         if ok_roadmap
         else "⛔ dn7 = %r, dn7-1 %s — un etat publie qui contredit ce que le "
              "meme commit livre est exactement ce que `dn5-4` a fait ecrire "
              "comme regle" % (etats.get("dn7"),
                               "defini" if "dn7-1" in etats else "ABSENT"))

    if regles["sortie_anticipee"]:
        return bilan(0)

    # ── (c23)(c24)(c25) LA RECIPROQUE, MECANIQUE ──────────────────────────
    print("\n── (c23)(c24)(c25) AUCUN CONTROLE GARDE PAR ZERO MUTANT ──────────")
    # 🔴 « N mutants, N vus rougir » prouve `mutant ⇒ rouge`, ⛔ JAMAIS
    #    `controle ⇒ couvert`. Les deux sens sont mesures, SEPAREMENT.
    lus_ast = ids_par_ast()
    reels = set(ids_emis) | (lus_ast or set())
    vises = set()
    for v in cibles.values():
        vises.update(v)
    nus = sorted(reels - vises, key=lambda s: (len(s), s))
    ctrl(not nus and lus_ast is not None,
         "(c23) chaque controle est vise par >= 1 mutant",
         "%d controle(s) lu(s) a l'AST, %d cible(s) declaree(s)"
         % (len(reels), len(vises)) if not nus and lus_ast is not None
         else ("⛔ %d CONTROLE(S) GARDE(S) PAR RIEN : %s"
               % (len(nus), " · ".join(nus)) if nus
               else "⛔ LA SOURCE NE S'ANALYSE PAS A L'AST — la population de "
                    "ce controle est INCONNUE, ⛔ pas vide"))
    perimees = sorted(vises - reels, key=lambda s: (len(s), s))
    ctrl(not perimees, "(c24) chaque cible de mutant est un controle REEL",
         "%d cible(s) confrontee(s)" % len(vises) if not perimees
         else "⛔ %d CIBLE(S) PERIMEE(S) : %s — un mutant qui vise un controle "
              "inexistant ⛔ ne garde rien"
              % (len(perimees), " · ".join(perimees)))
    orph = sorted(set(cibles) - set(MUTANTS))
    sans_cible = sorted(set(MUTANTS) - set(cibles))
    ctrl(not orph and not sans_cible,
         "(c25) `CIBLES` et `MUTANTS` se correspondent",
         "%d mutant(s), %d cible(s), cle a cle" % (len(MUTANTS), len(cibles))
         if not orph and not sans_cible
         else "⛔ cible(s) SANS mutant : %s · mutant(s) SANS cible : %s"
              % (orph or "—", sans_cible or "—"))

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : que le `.bat` DEMARRE sur une")
    print("   machine Windows, que le navigateur traite la page en contexte")
    print("   securise, ni que le retrait fonctionne. Ca, ce sont des MESURES,")
    print("   et elles vivent sous `mesures/dn7-1/`.")
    return bilan(1 if ko_total[0] else 0)


if __name__ == "__main__":
    sys.exit(main())

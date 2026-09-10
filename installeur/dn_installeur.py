#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dn_installeur.py — SERT la page d'installation, EN LOCAL.          (dn7-1)

============================ CE QU'IL FAIT, ET POURQUOI =====================

Il lie un serveur HTTP sur `127.0.0.1`, **sur un port TIRE A L'EXECUTION**, sert
`index.html`, ouvre le navigateur dessus, et expose **deux** points d'appel qui
invoquent les verbes `stop` et `retirer` de `tools/dn_agent_tour.ps1`.

⛔ IL NE FLASHE RIEN, ⛔ IL N'INSTALLE PAS L'AGENT, ⛔ IL NE DEMANDE AUCUN DROIT
   ADMINISTRATEUR. Poser la tache planifiee, la retirer et arreter l'agent sont
   trois gestes qui se font en session utilisateur — c'est deja ce que fait
   l'outil qu'on appelle ici, et sa propre garde traite le contraire comme un
   DEFAUT. ⇒ ce fichier n'a aucun verbe d'elevation, et une gate le verifie.
⚠️ ANNOTE LE 2026-09-08 PAR `dn7-2` — ⛔ LE PARAGRAPHE CI-DESSUS N'EST PAS
   EFFACE (`NFR3`), MAIS SA PREMIERE PROPOSITION A CESSE D'ETRE VRAIE. Ce
   serveur SERT DESORMAIS LA CHARGE que la page ecrit sur la carte, et il
   LIBERE LE PORT avant. Ce qu'il ne fait toujours pas : ecrire lui-meme sur la
   carte — c'est le navigateur qui le fait, par Web Serial. Les DEUX AUTRES
   propositions restent VRAIES telles quelles : ⛔ il n'installe toujours pas
   l'agent, et ⛔ il ne demande toujours AUCUN droit administrateur.

── POURQUOI UN PORT TIRE, ⛔ PAS UNE CONSTANTE ──────────────────────────────

Le banc d'essai du 2026-08-31 avait pris `8123`, en dur. Sur la machine d'un
inconnu, un port fixe peut etre DEJA PRIS — et « mettre a jour, c'est
reinstaller » (decision owner du 2026-09-08) fait du deuxieme lancement le cas
NOMINAL de tout le monde, ⛔ pas un cas de bord. ⇒ on lie le port **0**, le
systeme en choisit un LIBRE, et on RELIT celui qui a reellement ete lie. La
question « et si le port est pris ? » cesse d'exister au lieu d'etre traitee.
⚠️ L'adresse annoncee est donc TOUJOURS celle du `bind`, ⛔ jamais une constante
   ecrite a cote : c'est la seule forme qui ne peut pas mentir.

── POURQUOI `127.0.0.1` ET RIEN D'AUTRE ────────────────────────────────────

Web Serial n'existe que dans un CONTEXTE SECURISE. `http://localhost` en est
un — c'est le seul chemin MESURE (2026-08-31, Edge + Web Serial). Une page vue
par une adresse routable n'en est pas un, et le navigateur retire l'acces serie
SANS RIEN DIRE. ⇒ on n'ecoute que sur la boucle locale, et la page verifie
elle-meme, avec les objets du navigateur, qu'elle a bien ce qu'elle croit.
⚠️ **ANNOTE LE 2026-09-08 — ⛔ LA PHRASE CI-DESSUS N'EST PAS EFFACEE (`NFR3`),
   MAIS UNE THESE QUI CIRCULAIT AVEC ELLE EST REFUTEE PAR LA MESURE.** Le
   dossier de cadrage ecrivait que `file:` (la page posee sur le disque) « casse deux fois ». **C'est
   faux** : la MEME page, ouverte depuis le disque dans le meme Edge, rend
   `isSecureContext = oui` **et** `navigator.serial = disponible`
   (`mesures/dn7-1/T4-navigateur-et-contexte-securise.txt`) — et l'URL du
   prototype qui devait le prouver est **ABSOLUE**, ⛔ pas protocol-relative.
   ⇒ ce qui casse avec le schema `file:`, c'est **tout ce qui a besoin du serveur
   local** : la page perd `api/etat`, le DIT, et desactive ses deux boutons.
   Servir en local reste donc le bon choix — pour une raison VRAIE.
⚠️ COROLLAIRE DE BANC : servir cette page depuis WSL ne prouve RIEN. Le WSL de
   la tour est en NAT ⇒ `localhost` ne traverse pas, la page serait vue par IP,
   donc hors contexte securise. **Toute mesure se joue cote Windows.**

── L'ECART DECLARE DE `FR7.1`, ET L'INSTRUMENT QUI LE REPRODUIT ────────────

Sans executable autonome, l'inconnu installe **Python 3** puis **`psutil`** et
**`pyserial`**. C'est un ECART DECLARE, son geste est ecrit, et son porteur de
retour est nomme : l'agent en executable autonome, en V0.2.
🔴 ET LA SONDE NE MENT PAS PAR DEFAUT. Elle interroge Python **tel qu'il est**,
   site utilisateur COMPRIS : sur cette tour, `psutil` et `pyserial` vivent
   justement dans `AppData\\Roaming\\...\\site-packages`, et une sonde qui
   ecarterait ce site declarerait ABSENT ce qui est PRESENT — un faux manque,
   affiche a quelqu'un qui a deja fait le geste. ⇒ `--sans-site-utilisateur`
   existe pour REPRODUIRE l'absence a la demande (c'est l'instrument de mesure
   d'`AC7.1.6`), ⛔ il n'est pas le regime normal.

── CE QUE `dn7-2` AJOUTE, ET POURQUOI CHAQUE MORCEAU EST LA ────────────────

⚠️ L'EN-TETE CI-DESSUS DIT « IL NE FLASHE RIEN ». C'ETAIT VRAI DE `dn7-1`, ET
   C'EST ANNOTE PLUS BAS, ⛔ PAS EFFACE (`NFR3`).

1. **La charge est SERVIE, par la liste blanche.** SIX adresses de plus sous
   `/charge/` : le manifeste, les QUATRE images, et `PROVENANCE.md` — vers
   lequel la page pointe DEUX FOIS, parce que c'est lui qui nomme la source de
   la revision exacte (obligation GPL). ⛔ Toujours pas de serveur
   d'arborescence — chaque chemin reste une entree ECRITE de `SERVIS`.
2. **Le port se DECOUVRE.** ⛔ Plus de `COM3` par defaut : on demande a Windows
   quel `COM<n>` porte `VID_303A&PID_1001`, interface `MI_00`. ⛔ Aucune
   dependance, ⛔ pas d'`usbipd` (dont le chemin est en dur dans l'outil, et
   qu'un inconnu n'a pas).
3. **`stop` recoit `-Serie <le port DECOUVERT>`.** L'appel de `dn7-1` etait une
   liste FIXE sans `-Serie` : `stop` tombait donc sur le defaut `COM3` de
   `tools/dn_agent_tour.ps1`, et sur une machine dont la carte est ailleurs il
   rendait `7` ALORS QUE L'ARRET AVAIT EU LIEU.
4. **Les codes de `stop` ne sont ⛔ PAS un booleen.** `0` port rendu · `4` le
   drapeau n'a pas pu s'ecrire · `7` port ABSENT ou FANTOME · `8` toujours tenu
   ou cause inconnue. ⚠️ `7` est le cas NORMAL d'une carte qui vient d'etre
   debranchee ou reprise par WSL : le lire comme un echec ET le lire comme un
   succes sont DEUX FAUTES DIFFERENTES. ⇒ on rend LE FAIT, ⛔ pas un verdict.
5. **Un pre-vol de charge.** Les cinq fichiers, leurs tailles, et la
   bande-annonce d'integrite de l'asset (magie `DNASSET1` + longueur + CRC32) —
   un instrument GRATUIT sur une charge qu'on distribue.

Emploi :
    python dn_installeur.py                       sert la page et l'ouvre
    python dn_installeur.py --verifier            pre-vol seul, puis sort
    python dn_installeur.py --verifier --sans-site-utilisateur
                                                  idem, absence REPRODUITE
    python dn_installeur.py --sans-navigateur     sert sans ouvrir le navigateur

Codes de retour :
    0  tout est la
    3  Python n'a pas trouve la page ou l'outil qu'il doit servir
    4  le serveur local n'a pas pu se lier a la boucle locale
    5  la CHARGE est absente ou abimee (⛔ rien a flasher)
    6  une dependance de l'agent manque (l'ecart declare de `FR7.1`)
"""

import argparse
import http.client
import io
import json
import os
import re
import struct
import subprocess
import sys
import threading
import webbrowser
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# 🔴 `ICI` SE DERIVE DE `__file__`, ET `RACINE` DE `ICI` — ⛔ PAS L'INVERSE.
#    La 1re version reconstruisait le dossier par son NOM litteral a partir du
#    grand-parent (`os.path.join(RACINE, "installeur")`) : renommer le dossier
#    faisait echouer Python sur « re-cloner le depot » alors que le `.bat`,
#    qui utilise `%~dp0`, venait de valider la page A COTE DE LUI. Deux
#    facons de nommer le meme endroit, et une seule survit a un renommage.
ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
PAGE = os.path.join(ICI, "index.html")
PILOTE_DEPOT = os.path.join(RACINE, "tools", "dn_agent_tour.ps1")

# 🔴 LE DOSSIER DE CHARGE S'APPELLE `charge`, ET ⛔ SURTOUT PAS `build`.
#    `.gitignore` porte `build/` et `build-*/` SANS `/` initial : ces motifs
#    mordent A TOUTE PROFONDEUR. Mesure du 2026-09-08 a `git check-ignore` :
#    `installeur/charge/desknode.bin` n'est PAS ignore, `installeur/build/a.bin`
#    l'EST. Les quatre images auraient disparu de `git status` EN SILENCE.
CHARGE = os.path.join(ICI, "charge")
MANIFESTE = os.path.join(CHARGE, "manifest.json")
# ⚠️ Les noms sont ecrits ici parce qu'ils sont des ADRESSES SERVIES (une liste
#    blanche se declare), ⛔ mais les OFFSETS ne le sont nulle part : ils vivent
#    dans le manifeste, qui les tient de `build/flasher_args.json`. ⛔ Aucun des
#    quatre nombres n'est recopie dans du code.
IMAGES = ("bootloader.bin", "partition-table.bin", "desknode.bin",
          "living_pcb_v0.bin")

# ── LA BANDE-ANNONCE D'INTEGRITE DE L'ASSET ───────────────────────────────
# 16 octets colles APRES la charge utile par `tools/gen_living_pcb.py` (l.30-38)
# et relus a l'identique par le firmware (`main/dn_asset.c`) :
#     +0   8 o  magie ASCII « DNASSET1 »
#     +8   4 o  longueur de la charge utile, uint32 little-endian
#     +12  4 o  CRC32 zlib de la charge utile, uint32 little-endian
# ⇒ un instrument d'integrite GRATUIT sur une charge qu'on distribue : le
#   pre-vol s'en sert pour refuser une image tronquee AVANT de la servir.
ASSET_MAGIE = b"DNASSET1"
ASSET_QUEUE = 16

# 🔴 LA CARTE, TELLE QUE WINDOWS LA VOIT — MESURE LE 2026-09-08 SUR LA TOUR.
#    `USB\VID_303A&PID_1001&MI_00\…` ⇒ FriendlyName « Peripherique serie USB
#    (COM3) » (⚠️ LOCALISE), BusReportedDeviceDesc « USB JTAG/serial debug
#    unit ». `MI_02` est l'interface WinUSB (le JTAG), ⛔ PAS un port COM.
#    ⇒ la carte est un composite a DEUX interfaces, et SEULE `MI_00` porte un
#      `COM<n>`. C'est donc `MI_00` qu'on cherche, ⛔ pas le composite parent.
VID_PID = "VID_303A&PID_1001"
INTERFACE_COM = "MI_00"
# ⚠️ ON EXTRAIT LE `COM<n>` DE LA PARENTHESE DU `FriendlyName`, parce que c'est
#    la seule forme presente sur TOUTES les localisations de Windows : le texte
#    autour est traduit, ⛔ le `(COM3)` ne l'est pas.
RE_COM = re.compile(r"\((COM[0-9]+)\)")
# Le pilote refuse tout `-Serie` hors de cette forme (`dn_agent_tour.ps1:625`) :
# on ne lui passe donc QUE ce qu'il accepte, ⛔ jamais une chaine devinee.
# ⚠️ ANCRE PERIMEE, ANNOTEE ET DATEE LE 2026-09-10 (`dn7-6`) — ⛔ LA LIGNE
#    CI-DESSUS N'EST PAS EFFACEE (`NFR3`), ET SON FOND RESTE VRAI. Ce qui a
#    cesse de l'etre, c'est SON ADRESSE : la validation `^COM[0-9]+$` vit
#    desormais a `dn_agent_tour.ps1:703`, dans le verbe `permanence` — `:625`
#    y porte un `exit 4` SANS RAPPORT. ⇒ une adresse `fichier:ligne` se perime
#    au premier commit, et celle-ci pointait un lecteur vers la mauvaise
#    garde.
RE_PORT_VALIDE = re.compile(r"^COM[0-9]+$")

# 🔴 CE QUE `stop` REND, ET CE QUE CHAQUE CODE VEUT DIRE — RELU DANS L'OUTIL
#    (`tools/dn_agent_tour.ps1`, verbe `stop`), ⛔ pas devine.
#    ⚠️ `7` EST LE CAS **NORMAL** d'une carte qui vient d'etre debranchee ou
#       reprise par WSL : l'agent EST arrete, mais la preuve demandee (rouvrir
#       le port) ne peut pas etre produite. Le lire comme un echec et le lire
#       comme un succes sont DEUX FAUTES DIFFERENTES — ⇒ on rend LE FAIT.
# ═══ CE QUE `poser` REND — RELU DANS L'OUTIL, ⛔ PAS DEVINE ═══ (dn7-6) ═══
# 🔴 POURQUOI CETTE TABLE EXISTE, ET C'EST LA MEME RAISON QUE `CODES_STOP` :
#    sans elle, la queue de `jouer_verbe()` rend TOUT code non nul comme « le
#    refus remonte TEL QUEL ». Or `13` ⛔ N'EST PAS UN REFUS : l'outil ecrit
#    lui-meme « Ni un succes ni un echec total : les deux seraient FAUX ».
#    ⇒ la page CONTREDISAIT sa propre sortie dans le meme panneau — la sortie
#    brute disant « LA PERMANENCE EST POSEE ET VERIFIEE » au-dessus d'un
#    verdict disant « refus ».
# ⚠️ `12` EST LE REFUS DUR DE LHM (`dn7-5`), relaye par `permanence` : le
#    nommer ICI est ce que la ligne 9 de la matrice d'E/S demande — « la page
#    relaie ce code EN NOMMANT LHM », ⛔ pas seulement dans la sortie brute.
CODES_POSER = {
    0: "✅ la tache est POSEE ET VERIFIEE, et l'agent tourne MAINTENANT.",
    13: ("⚠️ LA PERMANENCE EST POSEE ET VERIFIEE — seul le DEMARRAGE IMMEDIAT "
         "n'a pas eu lieu. L'agent repartira a la prochaine ouverture de "
         "session. ⛔ Ce n'est ni un succes ni un echec : les deux seraient "
         "FAUX."),
    12: ("⛔ LibreHardwareMonitor est INJOIGNABLE, et le pre-vol de l'agent "
         "REFUSE sans lui. ⛔ RIEN n'a ete pose. Le geste est celui de LHM, "
         "ecrit dans l'ecart declare — ⛔ pas `pip`."),
    3: ("⛔ l'outil, l'agent ou le port n'ont pas ete trouves : RIEN n'a ete "
        "pose. ⛔ Ce n'est pas un succes."),
    9: ("⛔ la tache a ete posee mais elle ⛔ NE PASSE PAS son propre "
        "controle : ⛔ ne pas la croire posee."),
    10: ("⛔ la permanence est POSEE, et AUCUN agent n'etait vivant apres le "
         "delai d'attente. Le journal de l'agent dit pourquoi."),
    11: ("⛔ un AUTRE lancement tenait le verrou : RIEN n'a ete pose par ce "
         "geste-ci. ⛔ Ce n'est pas un succes."),
}

CODES_STOP = {
    0: ("rendu",
        "✅ le port a ete REOUVERT apres l'arret : il est rendu. C'est "
        "l'ouverture qui fait foi, ⛔ pas le code de retour."),
    4: ("drapeau",
        "⛔ le DRAPEAU D'ARRET n'a pas pu etre ECRIT : l'arret propre est "
        "impossible, et RIEN n'a ete force. ⛔ Ce n'est pas un succes."),
    7: ("disparu",
        "⚠️ l'agent est ARRETE, mais le port a DISPARU (carte debranchee, ou "
        "reprise par WSL) : il ne se rouvre pas. ⛔ « rendu » et « disparu » ne "
        "sont PAS la meme chose, et aucun des deux n'est un echec de l'arret."),
    8: ("tenu",
        "⛔ le port est ENCORE TENU (ou sa cause est INCONNUE) : quelque chose "
        "le garde. Le flash echouerait sur « Failed to execute 'open' on "
        "'SerialPort' », qui n'explique rien."),
}

# 🔴 L'ADRESSE ET LE PORT — LA BOUCLE LOCALE, ET LE PORT **TIRE**.
#    `PORT_DEMANDE = 0` demande au systeme un port LIBRE ; le port reellement
#    lie est relu apres coup dans `srv.server_address[1]`. ⛔ Ne jamais ecrire
#    ici le numero qu'on croit avoir : l'annonce se DERIVE du `bind`.
ADRESSE = "127.0.0.1"
PORT_DEMANDE = 0

# 🔴 LES DEUX SEULS VERBES QUE CETTE PAGE EXPOSE — ET ILS EXISTENT DEJA.
#    Ils viennent du `[ValidateSet]` de `tools/dn_agent_tour.ps1` (l.52) :
#      etat · prevol · lancer · tache · stop · permanence · retirer
#    ⛔ On n'en reimplemente aucun, et on n'en invente aucun : une gate relit ce
#    `[ValidateSet]` dans le fichier et refuse tout verbe qui n'y est pas.
# 🎯 ANNOTE ET DATE LE 2026-09-10 (`dn7-6`) — ⛔ RIEN N'EST EFFACE, LE COMPTE
#    CHANGE. Le titre ci-dessus disait « LES DEUX SEULS VERBES », et il en
#    expose desormais **TROIS** : `poser` s'ajoute, sur arbitrage owner du
#    2026-09-10 (« ok pour le nouveau verbe qui lance l'agent »). Ce qui reste
#    vrai, mot pour mot : ⛔ on n'en reimplemente aucun, on n'en invente aucun
#    ICI, et une gate relit le `[ValidateSet]` du fichier pour refuser tout
#    verbe qui n'y est pas. `poser` est la COMPOSITION de `permanence` et de
#    `lancer` — il vit dans l'outil, ⛔ pas dans ce serveur.
VERBES = ("stop", "retirer", "poser")

# Les modules dont l'AGENT a besoin — ⛔ pas ce serveur, qui n'en veut aucun.
DEPENDANCES_AGENT = ("psutil", "pyserial")
IMPORTS_AGENT = {"psutil": "psutil", "pyserial": "serial"}
GESTE_DEPENDANCES = "pip install --user psutil pyserial"
# 🔴 ASCII PUR, ET C'EST MESURE, ⛔ pas une precaution : la console Windows
#    n'est pas en UTF-8 (Python 3.13 ne l'y force pas), et le premier tir du
#    2026-09-08 a rendu « DeskNode ? installeur local » sur un simple tiret
#    cadratin. Une page peut porter des accents ; une CONSOLE qui doit dire
#    un geste exact a quelqu'un de perdu, ⛔ non.
PORTEUR_ECART = ("l'agent en executable autonome, prevu en V0.2 - "
                 "c'est la decision qui a cree l'ecart qui le refermera")

# ══ LE SERVICE LHM : L'ADRESSE EST **LUE DANS LE PRODUIT** (dn7-5) ═════════
# 🔴 LE PATRON EST DEJA ECRIT DANS CE DEPOT : `tools/dn_lhm_tour.ps1` (l.122-128)
#    lit `LHM_PORT` DANS `agent/dn_agent.py` au lieu de le recopier, et il dit
#    pourquoi — figer la valeur ici ferait DEUX sources de verite, et la
#    seconde pourrirait EN SILENCE le jour ou l'owner joue un autre port.
# ⚠️ ⛔ AUCUN REPLI CHIFFRE, ET C'EST UN CHOIX. Si `agent/dn_agent.py` n'est pas
#    la — copie deployee, dossier `installeur/` recupere seul — la sonde ⛔ ne
#    DEVINE pas : elle rend `None`, c'est-a-dire " non testable ici ", ⛔ pas
#    " ABSENT ". Une ignorance publiee comme un constat est exactement ce que
#    `tache_presente()` et `dependance_presente()` se gardent deja de faire.
AGENT_PY = os.path.join(RACINE, "agent", "dn_agent.py")
RE_LHM_HOTE = re.compile(r'^LHM_HOTE\s*=\s*"([^"]+)"', re.M)
RE_LHM_PORT = re.compile(r"^LHM_PORT\s*=\s*(\d+)", re.M)
RE_LHM_CHEMIN = re.compile(r'^LHM_CHEMIN\s*=\s*"([^"]+)"', re.M)
# ⚠️ LE PLAFOND DE **LA SONDE**, ⛔ pas celui du regime de l'agent. L'agent
#    borne sa lecture a 0,6 s parce qu'il CADENCE ; ici personne ne cadence
#    rien : on pose UNE question a la boucle locale, une seule fois.
LHM_SONDE_TIMEOUT_S = 1.5
# Ce que le corps doit porter pour que ce soit LHM et ⛔ pas un voisin :
# le prefixe que `agent/dn_agent.py` exige de CHAQUE ligne qu'il retient
# (`if not ligne.startswith("lhm_")`), ancre EN DEBUT DE LIGNE comme lui.
RE_MARQUE_LHM = re.compile(rb"(?m)^lhm_")
PLAFOND_CORPS_LHM = 65536
# 🔴 LE GESTE DE LHM EXISTE DEJA, ⛔ IL NE S'INVENTE PAS. `tools/dn_lhm_tour.ps1`
#    installe ce qui manque, ecrit la config du serveur web et pose la
#    permanence ; SANS ARGUMENT il VERIFIE et ne change RIEN. ⛔ Ce n'est pas un
#    module pip, et ⛔ pas une ligne d'installateur recopiee.
GESTE_LHM = "tools\\dn_lhm_tour.ps1 -Poser -Permanence tache"
# 🔴 ⛔ ET IL N'Y A **AUCUNE ROUTE** QUI JOUE CE GESTE-LA, ⛔ pas par oubli.
#    `tools/dn_lhm_tour.ps1` ECRIT LUI-MEME (l.186-187, l.233-235, l.456) que
#    sans elevation « -Poser et -Permanence NE POURRONT PAS agir », et la
#    tache qu'il pose est ELEVEE. Le seul chemin d'elevation depuis ce dossier
#    est interdit par DEUX gates vivantes. ⇒ un bouton qui lancerait ce script
#    non eleve promettrait un geste qui ⛔ N'AGIT PAS : la commande reste A
#    RECOPIER, et la page ecrit POURQUOI.
# Ce qui tombe SANS LHM — MESURE dans `agent/dn_agent.py`, ⛔ pas suppose : la
# grandeur 4 (temperature du CPU) et les trois vitesses de ventilateur. Le
# reste ne bouge pas : le % CPU, les GHz, les Mo/s et l'AMBIANCE survivent.
PERTE_LHM = ("la temperature du CPU et les trois vitesses de ventilateur")

# ⚠️ RELU DANS L'OUTIL, ⛔ PAS RECOPIE : le nom de la tache est une valeur de
#    `dn_agent_tour.ps1`. Le figer ici ferait deux sources de verite, et la
#    seconde pourrirait en silence le jour ou la premiere change.
NOM_TACHE_REPLI = "DeskNode agent"
RE_NOM_TACHE = re.compile(r"^\s*\$NOM_TACHE\s*=\s*'([^']+)'", re.M)
RE_VALIDATESET = re.compile(r"\[ValidateSet\(([^)]*)\)\]")
RE_FICHIER_PS1 = re.compile(r'-File\s+"?([^"]+dn_agent_tour\.ps1)"?', re.I)


# ═══════════════════════ LIRE LA MACHINE, ⛔ PAS LA SUPPOSER ═══════════════

def _lire(chemin):
    try:
        with io.open(chemin, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def verbes_de_l_outil(texte):
    """Les verbes que l'outil accepte VRAIMENT, relus dans son `[ValidateSet]`.

    ⛔ Aucune liste recopiee : si l'outil en gagne ou en perd un, c'est ici que
       ca se voit, ⛔ pas six mois plus tard sur un refus incomprehensible.
    🔴 **ET ELLE EST REELLEMENT APPELEE — corrige le 2026-09-08.** Cette
       docstring etait FAUSSE : la fonction n'etait invoquee NULLE PART, et
       `VERBES` restait une liste recopiee que seule la gate confrontait. Un
       verbe renomme dans l'outil serait donc parti en refus PowerShell
       incomprehensible, exactement ce que la phrase ci-dessus promet d'eviter.
       ⇒ `jouer_verbe()` la consulte AVANT d'appeler, et refuse proprement.
    ⚠️ Elle rend `()` si le fichier est illisible ou sans `[ValidateSet]` —
       et un tuple VIDE ⛔ n'est PAS « aucun verbe accepte » : c'est « on ne
       sait pas ». L'appelant traite les deux differemment."""
    if not texte:
        return ()
    m = RE_VALIDATESET.search(texte)
    if not m:
        return ()
    return tuple(re.findall(r"'([a-z]+)'", m.group(1)))


def _powershell(arguments, timeout=90):
    """Un appel PowerShell **NON ELEVE**, en session utilisateur.

    ⚠️ `-ExecutionPolicy Bypass` porte sur CE processus seul et ⛔ ne change
       rien a la machine : c'est exactement ce que fait deja `tools/dn-agent.bat`
       (l.41), et c'est necessaire — la politique mesuree sur cette tour est
       `Restricted`, ce qui refuse tout `.ps1`, Marque du Web ou pas."""
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass"] + arguments
    try:
        r = subprocess.run(cmd, cwd=RACINE, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
    # 🔴 LE DELAI DEPASSE EST RENDU A PART, ET C'EST UN CORRECTIF DU 2026-09-08.
    #    `TimeoutExpired` derive de `SubprocessError` : range avec lui, il
    #    faisait dire a la page « le geste n'a PAS eu lieu » alors que l'outil
    #    A TOURNE et peut AVOIR AGI. ⛔ Il faut donc l'attraper AVANT, et
    #    ⛔ ne jamais le rendre comme un non-lancement.
    except subprocess.TimeoutExpired:
        return (None, "delai de %s s depasse — l'outil a tourne SANS rendre "
                "la main" % timeout, cmd, "delai")
    except (OSError, subprocess.SubprocessError) as exc:
        return None, "%s : %s" % (type(exc).__name__, exc), cmd, "lancement"
    return r.returncode, (r.stdout or "") + (r.stderr or ""), cmd, None


# ⚠️ LE PILOTE RESOLU, MEMORISE POUR LA DUREE DE L'EXECUTION. Voir le motif
#    dans `localiser_pilote()` : ce n'est ⛔ pas un cache de confort.
_PILOTE = {"chemin": None, "origine": None}


def localiser_pilote():
    """Ou vit le `dn_agent_tour.ps1` qui pilote l'agent DE CETTE MACHINE.

    🔴 ⛔ PAS UN CHEMIN EN DUR, ET ⛔ PAS NON PLUS « celui du depot, forcement ».
       Le verbe `stop` est PROPRE parce qu'il pose un fichier-drapeau **a cote de
       l'agent** ; appeler une copie qui vit ailleurs poserait le drapeau la ou
       personne ne le lit, et l'arret retomberait sur le `taskkill` qui PERD le
       bilan de fin. ⇒ on demande au systeme ou est l'outil qu'il lance
       reellement (l'action de la tache planifiee le DIT), et on ne se rabat sur
       la copie du depot que faute de tache.

    🔴 ET LE RESULTAT EST MEMORISE — CORRECTIF DU 2026-09-08, SUR UN CHEMIN
       REEL. Apres un `retirer` REUSSI, la tache n'existe plus : une seconde
       resolution se rabattrait sur `PILOTE_DEPOT`, dont le drapeau
       `dn-agent.stop` vit sous `tools/` — la ou l'agent DEPLOYE ne le lit
       JAMAIS. Un `stop` clique juste apres retomberait donc sur le `taskkill`
       qui PERD le bilan de fin, c'est-a-dire EXACTEMENT ce que le paragraphe
       ci-dessus interdit. ⛔ On ne memorise QUE le succes : un echec de
       resolution doit pouvoir etre retente."""
    if _PILOTE["chemin"] is not None:
        return _PILOTE["chemin"], _PILOTE["origine"]
    rc, sortie, _cmd, _echec = _powershell([
        "-Command",
        "$t = Get-ScheduledTask -TaskName '%s' -ErrorAction SilentlyContinue; "
        "if ($t) { ($t.Actions | Select-Object -First 1).Arguments }"
        % nom_de_la_tache()], timeout=45)
    if rc == 0 and sortie:
        m = RE_FICHIER_PS1.search(sortie)
        if m and os.path.exists(m.group(1)):
            _PILOTE.update(chemin=m.group(1),
                           origine="l'action de la tache planifiee")
            return _PILOTE["chemin"], _PILOTE["origine"]
    if os.path.exists(PILOTE_DEPOT):
        _PILOTE.update(chemin=PILOTE_DEPOT,
                       origine="la copie du depot (aucune tache posee)")
        return _PILOTE["chemin"], _PILOTE["origine"]
    return None, "introuvable"


def nom_de_la_tache():
    texte = _lire(PILOTE_DEPOT)
    m = RE_NOM_TACHE.search(texte or "")
    return m.group(1) if m else NOM_TACHE_REPLI


def tache_presente():
    """`True` / `False` / `None` — et `None` n'est ⛔ PAS `False`.

    Sur une machine qui n'a pas le Planificateur de taches Windows, la question
    n'a pas de reponse ; repondre « absente » ferait passer une IGNORANCE pour
    un constat."""
    rc, sortie, _cmd, _echec = _powershell([
        "-Command",
        "$t = Get-ScheduledTask -TaskName '%s' -ErrorAction SilentlyContinue; "
        "if ($t) { 'PRESENTE|' + $t.Principal.RunLevel } else { 'ABSENTE|' }"
        % nom_de_la_tache()], timeout=45)
    if rc is None or rc != 0 or not sortie:
        return None, ""
    for ligne in sortie.splitlines():
        ligne = ligne.strip()
        if ligne.startswith("PRESENTE|"):
            return True, ligne.split("|", 1)[1].strip()
        if ligne.startswith("ABSENTE|"):
            return False, ""
    return None, ""


def dependance_presente(module, sans_site_utilisateur):
    """`psutil` / `pyserial` sont-ils la, POUR LE PYTHON QUI TOURNE ICI ?"""
    argv = [sys.executable]
    if sans_site_utilisateur:
        # ⚠️ L'INSTRUMENT, ⛔ PAS LE REGIME NORMAL : `-s` ecarte le site
        #    UTILISATEUR, la ou `pip install --user` depose. Il sert a
        #    REPRODUIRE l'absence sur une machine qui a deja tout.
        argv.append("-s")
    argv += ["-c", "import %s" % IMPORTS_AGENT[module]]
    try:
        r = subprocess.run(argv, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.returncode == 0


def cible_lhm():
    """OU LHM repond — hote, port et chemin **LUS DANS L'AGENT**.

    ⛔ RIEN N'EST RECOPIE ICI. C'est `agent/dn_agent.py` qui decide ou il va
       chercher ses sondes ; ce fichier ne fait que RELIRE sa decision. Le
       jour ou l'owner joue un autre port, la page suit toute seule.
    ⚠️ Rend `None` si l'agent n'est pas la ou ne publie pas ses trois
       constantes — et « on ne sait pas » ⛔ n'est PAS « absent »."""
    txt = _lire(AGENT_PY)
    if not txt:
        return None
    h = RE_LHM_HOTE.search(txt)
    p = RE_LHM_PORT.search(txt)
    c = RE_LHM_CHEMIN.search(txt)
    if not (h and p and c):
        return None
    return h.group(1), int(p.group(1)), c.group(1)


def lhm_present():
    """`True` / `False` / `None` — et `None` n'est ⛔ PAS `False`.

    🔴 C'EST LE CHEMIN DE MESURES QUI TRANCHE, ⛔ PAS LE PROCESSUS.
       `tools/dn_lhm_tour.ps1` sait compter les deux et ecrit pourquoi le
       second ne suffit pas : le serveur web de LHM vient de sa **config XML**
       (l.317-320), ⛔ pas de son lancement. Un LHM ouvert SANS son serveur
       rendrait « 1 processus » et un chemin de mesures MORT — un FAUX VERT,
       c'est-a-dire la faute que ce depot a nommee quatre fois pendant `dn7-4`.
    ⚠️ LA QUESTION EST **EXACTEMENT CELLE QUE L'AGENT POSE** : un `GET` sur la
       boucle locale. ⛔ Aucune elevation, ⛔ aucun driver, ⛔ aucun .NET — c'est
       LHM qui coute ces trois-la, ⛔ pas DeskNode."""
    # 🔴 HORS WINDOWS, ⛔ ON NE CONCLUT PAS — ET C'EST LE MEME MOTIF QUE
    #    `tache_presente()` ET QUE « PILOTABLE NE SE DEDUIT PAS DE L'EXISTENCE
    #    DU FICHIER », trois lignes sous le champ que cette sonde remplit.
    #    MESURE sur Linux : sans ce garde, la sonde rendait `False` ⇒ le
    #    pre-vol imprimait « ABSENT » et envoyait jouer un `.ps1` INJOUABLE.
    #    LHM n'existe QUE sur Windows : ailleurs, la question n'a pas de
    #    reponse, et une ignorance ⛔ n'est PAS un constat.
    if os.name != "nt":
        return None
    cible = cible_lhm()
    if cible is None:
        return None
    hote, port, chemin = cible
    conn = None
    try:
        conn = http.client.HTTPConnection(hote, port,
                                          timeout=LHM_SONDE_TIMEOUT_S)
        conn.request("GET", chemin)
        rep = conn.getresponse()
        corps = rep.read(PLAFOND_CORPS_LHM)
        # 🔴 UN `200` NE SUFFIT PAS, ET C'EST MESURE : `/metrics` sur ce port
        #    est **l'adresse la plus banale d'un exportateur Prometheus**. Un
        #    service voisin rendrait la sonde VERTE, l'agent demarrerait, et la
        #    temperature du CPU resterait a `--` pour toujours — meme famille
        #    de FAUX VERT que compter le processus. ⇒ le corps doit porter le
        #    prefixe que l'agent LUI-MEME exige (`ligne.startswith("lhm_")`).
        # ⚠️ UN REFUS DE CONNEXION EST UN **CONSTAT**, ⛔ pas une ignorance :
        #    personne n'ecoute, donc LHM n'est pas debout. C'est bien `False`.
        return rep.status == 200 and bool(RE_MARQUE_LHM.search(corps))
    except (OSError, ValueError, http.client.HTTPException):
        # ⚠️ `ValueError` EST DANS LE TUPLE, ET C'EST MESURE : un `LHM_CHEMIN`
        #    non-ASCII fait lever `UnicodeEncodeError` a `putrequest`, et c'est
        #    un `ValueError`, ⛔ pas un `OSError`. Sans lui, une fenetre
        #    double-cliquee sortait en TRACE NUE.
        return False
    finally:
        if conn is not None:
            try:
                conn.close()
            except OSError:
                pass


def decouvrir_port():
    """Le `COM<n>` REEL de la carte — demande a Windows, ⛔ pas suppose.

    🔴 POURQUOI CETTE FONCTION EXISTE, ET CE QU'ELLE REPARE. `dn7-1` appelait
       le pilote par une liste FIXE d'arguments, SANS `-Serie` : le verbe `stop`
       tombait donc sur le defaut `COM3` code en dur dans l'outil. Sur une
       machine dont la carte est sur un autre port, `stop` pose bien le drapeau
       (c'est un fichier, il ne connait pas le port), puis va rouvrir **COM3**
       comme preuve — et rend `7` ALORS QUE L'ARRET A EU LIEU. Un installeur qui
       lirait « rc != 0 ⇒ echec » compterait un echec pour un succes.
    🔴 ⛔ ET ⛔ PAS PAR `usbipd`. La seule detection de `303a:1001` du depot
       (`tools/dn_agent_tour.ps1`) passe par `usbipd`, dont le chemin est EN DUR
       et qu'un inconnu N'A PAS. `Get-PnpDevice` est dans Windows depuis
       toujours et ne coute AUCUNE dependance.
    ⚠️ ⛔ AUCUN `COM<n>` N'EST DEVINE : sans carte enumeree, cette fonction rend
       `None`, et la page le DIT au lieu de jouer `stop` sur un port suppose."""
    rc, sortie, _cmd, _echec = _powershell([
        "-Command",
        # 🔴 L'ENCODAGE DE SORTIE EST FORCE EN UTF-8, ET C'EST UN DEFAUT MESURE
        #    LE 2026-09-08, ⛔ PAS UNE PRECAUTION. PowerShell 5.1 ecrit dans la
        #    page de code OEM de la console ; or le nom que Windows donne au
        #    port est **LOCALISE** — « Peripherique serie USB (COM3) », avec
        #    deux accents. Sans cette ligne, la lecture en UTF-8 les remplace
        #    par le caractere de remplacement, et la page affichait un nom
        #    ABIME a l'endroit precis ou elle promet de dire le VRAI nom du
        #    port. ⚠️ Le `(COM<n>)` extrait, lui, est de l'ASCII : la
        #    DECOUVERTE marchait deja — c'est l'AFFICHAGE qui mentait.
        "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
        # ⚠️ `-PresentOnly` : une carte DEBRANCHEE laisse son enregistrement PnP
        #    derriere elle. Sans ce filtre on rendrait le port d'une carte qui
        #    n'est plus la — le contraire de « mesurer ».
        "$d = Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue | "
        "Where-Object { $_.InstanceId -like 'USB\\%s&%s\\*' }; "
        "foreach ($x in $d) { 'DN|' + $x.FriendlyName + '|' + $x.InstanceId }"
        % (VID_PID, INTERFACE_COM)], timeout=45)
    # 🔴 DEUX MOTIFS DISTINCTS, ET LES CONFONDRE EST UNE FAUTE DANS LES DEUX
    #    SENS. « la question n'a pas de reponse ici » (pas de PnP, donc hors
    #    Windows) ⛔ n'est PAS « il n'y a pas de carte branchee ». La 1re
    #    redaction rangeait `rc == 0` avec une sortie VIDE — c'est-a-dire une
    #    interrogation qui a REUSSI et n'a rien trouve — sous le motif reserve a
    #    l'ignorance : sur un Windows sans carte, elle publiait une ignorance a
    #    la place d'un constat, et reciproquement.
    if rc is None:
        return None, None, "non interrogeable ici"
    if rc != 0:
        return None, None, ("l'interrogation du gestionnaire de peripheriques a "
                            "rendu %d" % rc)
    trouves = []
    for ligne in (sortie or "").splitlines():
        ligne = ligne.strip()
        if not ligne.startswith("DN|"):
            continue
        _t, nom, instance = (ligne.split("|", 2) + ["", ""])[:3]
        m = RE_COM.search(nom or "")
        if m and RE_PORT_VALIDE.match(m.group(1)):
            trouves.append((m.group(1), nom.strip(), instance.strip()))
    if not trouves:
        return None, None, "aucun %s&%s enumere" % (VID_PID, INTERFACE_COM)
    # 🔴 DEUX CARTES DE MEME `VID:PID` — HYPOTHESE LAISSEE OUVERTE PAR L'EPIC,
    #    ET ⛔ ON NE LA FERME PAS EN CHOISISSANT. Rendre la premiere ligne
    #    ferait jouer `stop` sur une carte ARBITRAIRE et afficherait un port qui
    #    n'est peut-etre pas celui qu'on flashe. Le flash, lui, est sauve : le
    #    navigateur fait choisir le port AU DOIGT. ⇒ on REFUSE de trancher, et
    #    on le DIT — la page n'a alors aucun port a liberer, et elle l'affiche.
    if len(trouves) > 1:
        return None, None, ("%d cartes %s enumerees (%s) — ⛔ cette page REFUSE "
                            "de choisir : debrancher celle qu'on ne flashe pas"
                            % (len(trouves), VID_PID,
                               " et ".join(x[0] for x in trouves)))
    return trouves[0]


def _lire_octets(chemin):
    try:
        with open(chemin, "rb") as fh:
            return fh.read()
    except OSError:
        return None


def etat_charge():
    """La charge est-elle LA, ENTIERE, et l'asset INTACT ?

    ⛔ Ce n'est pas un controle de confort : la page annonce a quelqu'un qu'elle
       va ECRIRE sur sa carte. Servir un `.bin` tronque — flash de la voie A
       interrompue, disque plein pendant la generation, copie a moitie faite —
       poserait un firmware qui ne demarre pas, ou un asset BLANC.
    🎯 L'asset porte une bande-annonce d'integrite (magie + longueur + CRC32)
       que le firmware relit deja : la verifier ICI ne coute rien et attrape
       exactement ce cas."""
    manquants, vides = [], []
    tailles = {}
    for nom in IMAGES + ("manifest.json",):
        chemin = os.path.join(CHARGE, nom)
        if not os.path.exists(chemin):
            manquants.append(nom)
            continue
        taille = os.path.getsize(chemin)
        tailles[nom] = taille
        if taille == 0:
            vides.append(nom)
    version, offsets, ecart_manifeste = None, None, None
    if "manifest.json" not in manquants:
        try:
            with io.open(MANIFESTE, encoding="utf-8") as fh:
                man = json.load(fh)
            b = (man.get("builds") or [{}])[0]
            version = man.get("version")
            offsets = [(p.get("path"), p.get("offset")) for p in b.get("parts", [])]
        # ⚠️ `AttributeError` EST DANS LA LISTE, ET C'EST UN CAS REEL : un
        #    `manifest.json` qui porte un TABLEAU ou un SCALAIRE (JSON valide)
        #    fait lever `.get` sur autre chose qu'un dictionnaire. Sans elle,
        #    l'exception ECHAPPAIT a cette fonction : `/api/etat` rendait 500 et
        #    le pre-vol sortait en trace nue AU LIEU de rendre `5`.
        except (OSError, ValueError, KeyError, IndexError, TypeError,
                AttributeError) as exc:
            ecart_manifeste = "%s : %s" % (type(exc).__name__, str(exc)[:80])
    # ── LA BANDE-ANNONCE DE L'ASSET ───────────────────────────────────────
    asset = "non verifiable"
    if "living_pcb_v0.bin" not in manquants:
        octets = _lire_octets(os.path.join(CHARGE, "living_pcb_v0.bin"))
        if octets is None or len(octets) < ASSET_QUEUE:
            asset = "⛔ ILLISIBLE ou trop court"
        elif octets[-ASSET_QUEUE:-8] != ASSET_MAGIE:
            asset = "⛔ MAGIE ABSENTE (attendu %s)" % ASSET_MAGIE.decode("ascii")
        else:
            longueur, crc = struct.unpack("<II", octets[-8:])
            # ⛔ UNE CHARGE UTILE DE LONGUEUR NULLE N'EST PAS « INTACTE ».
            #    Une queue bien formee annoncant `0` passait les trois tests
            #    suivants — le CRC32 de rien VAUT quelque chose — et l'asset
            #    VIDE partait a la carte, qui demarrait sur une dalle BLANCHE :
            #    exactement l'ecran blanc silencieux que la queue existe pour
            #    refuser.
            if longueur == 0:
                asset = ("⛔ CHARGE UTILE VIDE : la queue annonce 0 octet — "
                         "l'asset ne peut pas etre intact")
            elif longueur + ASSET_QUEUE != len(octets):
                asset = ("⛔ LONGUEUR INCOHERENTE : la queue annonce %d + %d, le "
                         "fichier en fait %d" % (longueur, ASSET_QUEUE, len(octets)))
            elif (zlib.crc32(octets[:longueur]) & 0xFFFFFFFF) != crc:
                asset = "⛔ CRC32 FAUX : l'image est ABIMEE, ⛔ pas seulement vieille"
            else:
                asset = "intact (%d o + %d o de queue, CRC32 verifie)" % (longueur,
                                                                         ASSET_QUEUE)
    return {
        "dossier": CHARGE,
        "manquants": manquants,
        "vides": vides,
        "tailles": tailles,
        "version": version,
        "offsets": offsets,
        "ecart_manifeste": ecart_manifeste,
        "asset": asset,
        "complete": (not manquants and not vides and not ecart_manifeste
                     and asset.startswith("intact")),
    }


def arbre_parent_present():
    """L'`installeur/` est-il DANS son depot, ou a-t-il ete recupere SEUL ?

    🔴 SCENARIO REEL D'`AC7.1.3` : quelqu'un qui TELECHARGE plutot qu'il ne
       clone peut n'avoir que ce dossier. Le `.bat` ne verifie que ses deux
       voisins immediats ; or l'outil de l'agent, le `README.md` et le
       `LICENSING.md` vivent HORS du dossier. Sans ce controle, la page s'ouvre
       avec deux boutons morts et trois liens de pied de page en 404, et
       ⛔ AUCUN niveau ne le dit."""
    return (os.path.exists(PILOTE_DEPOT)
            and os.path.exists(os.path.join(RACINE, "README.md")))


def etat_machine(sans_site_utilisateur=False):
    presente, runlevel = tache_presente()
    pilote, origine = localiser_pilote()
    port, nom_port, motif_port = decouvrir_port()
    charge = etat_charge()
    # 🔴 TROIS ETATS, ⛔ PAS DEUX — CORRECTIF DU 2026-09-08. `bool(ok)` ecrasait
    #    `None` (« la sonde n'a pas pu tourner ») sur `False` (« le module est
    #    ABSENT ») : un module NON TESTE etait annonce absent, et le pre-vol
    #    rendait `6` pour un ecart qui n'existait peut-etre pas. Une IGNORANCE
    #    publiee comme un constat est exactement ce que `tache_presente()` se
    #    garde deja de faire deux fonctions plus haut.
    manquantes, non_testables = [], []
    deps = {}
    for m in DEPENDANCES_AGENT:
        ok = dependance_presente(m, sans_site_utilisateur)
        deps[m] = ok
        if ok is False:
            manquantes.append(m)
        elif ok is None:
            non_testables.append(m)
    return {
        # 🔴 LE SYSTEME EST CELUI DE **CETTE** MACHINE, ⛔ pas une chaine
        #    d'agent utilisateur. Le serveur tourne sur la boucle locale : il
        #    EST la machine que le navigateur regarde. Une detection cote page
        #    (`navigator.platform`) mesurerait ce que le navigateur veut bien
        #    dire de lui ; celle-ci mesure le systeme qui devra faire tourner
        #    l'agent. ⇒ c'est la bonne source pour l'avertissement hors Windows.
        "systeme": sys.platform,
        "windows": os.name == "nt",
        "python_version": "%d.%d.%d" % sys.version_info[:3],
        "python_executable": sys.executable,
        "psutil": deps.get("psutil"),
        "pyserial": deps.get("pyserial"),
        "manquantes": manquantes,
        "non_testables": non_testables,
        "arbre_parent": arbre_parent_present(),
        "geste": GESTE_DEPENDANCES,
        # ── L'AUTRE MOITIE DE L'ECART DECLARE (dn7-5) ─────────────────────
        # 🔴 TROIS POSITIONS, ⛔ PAS DEUX, exactement comme `psutil` : `None`
        #    veut dire « la sonde n'a pas pu tourner », ⛔ pas « absent ».
        # 🔴 ⛔ ET LHM N'ENTRE PAS DANS `manquantes` : cette liste commande A LA
        #    FOIS le code de sortie `6` du pre-vol ET le bloc qui publie
        #    `GESTE_DEPENDANCES`. Y verser LHM ferait imprimer `pip install …`
        #    pour une dependance qui ⛔ n'est PAS un module pip.
        "lhm": lhm_present(),
        "geste_lhm": GESTE_LHM,
        "perte_lhm": PERTE_LHM,
        "porteur_ecart": PORTEUR_ECART,
        "tache_nom": nom_de_la_tache(),
        "tache_presente": presente,
        "tache_runlevel": runlevel,
        "pilote": pilote,
        "pilote_origine": origine,
        "verbes": list(VERBES),
        # ── CE QUE `dn7-2` AJOUTE A L'ETAT ────────────────────────────────
        # ⚠️ LE PORT EST **DECOUVERT**, ⛔ PAS SUPPOSE. `port_serie` vaut `None`
        #    quand aucune carte n'est enumeree : la page le DIT et ⛔ ne joue
        #    AUCUN `stop` sur un port suppose.
        "port_serie": port,
        "port_nom": nom_port,
        "port_motif": motif_port,
        "charge": charge,
    }


# ═════════════════════ LES DEUX GESTES, RELAYES TELS QUELS ════════════════

def jouer_verbe(verbe):
    """Appelle le verbe, RELAIE sa sortie et son `rc`, et ⛔ n'embellit rien.

    🔴 APRES `retirer`, ON REDEMANDE LA TACHE AU SYSTEME. Le message de sortie
       de l'outil ⛔ ne fait pas foi : c'est la re-interrogation qui tranche, et
       si la tache SURVIT, le verdict rendu ici est un ECHEC — meme si l'outil a
       dit « retrait verifie » et rendu 0."""
    if verbe not in VERBES:
        return {"commande": "", "sortie": "", "rc": 2, "rc_pose_par": "la page",
                "verdict": "⛔ verbe non expose par cette page : %s" % verbe}
    pilote, origine = localiser_pilote()
    if not pilote:
        return {"commande": "", "sortie": "", "rc": 4, "rc_pose_par": "la page",
                "verdict": "⛔ `dn_agent_tour.ps1` INTROUVABLE — rien n'a ete "
                           "tente. ⛔ Ce n'est pas un succes."}
    # ⚠️ LE `[ValidateSet]` REEL DE L'OUTIL RESOLU, ⛔ pas la liste d'ici. Un
    #    tuple VIDE veut dire « illisible », ⛔ pas « aucun verbe » : on ne
    #    refuse que sur une liste qu'on a REELLEMENT lue.
    acceptes = verbes_de_l_outil(_lire(pilote))
    if acceptes and verbe not in acceptes:
        return {"commande": "", "sortie": "", "rc": 2, "rc_pose_par": "la page",
                "verdict": "⛔ l'outil de CETTE machine n'accepte pas le verbe "
                           "`%s` (il accepte : %s). Rien n'a ete tente."
                           % (verbe, " · ".join(acceptes))}
    # 🔴 LE PORT EST PASSE, ET C'EST LE CORRECTIF DE `dn7-2`. La liste etait
    #    FIXE (`["-File", pilote, verbe]`) : sans `-Serie`, l'outil retombait
    #    sur son defaut `COM3` code en dur. Sur une machine dont la carte est
    #    ailleurs, `stop` posait bien le drapeau — c'est un fichier — puis
    #    allait rouvrir COM3 comme PREUVE, et rendait `7` alors que l'arret
    #    avait eu lieu. ⛔ On ne laisse plus un defaut decider.
    # ⚠️ ET ON NE PASSE QUE CE QUE L'OUTIL ACCEPTE : sans carte enumeree,
    #    `decouvrir_port()` rend `None`, et on n'invente ⛔ AUCUN `COM<n>` —
    #    l'outil garde alors son propre defaut, et le verdict le DIT.
    port, nom_port, motif_port = decouvrir_port()
    arguments = ["-File", pilote, verbe]
    if port and RE_PORT_VALIDE.match(port):
        arguments += ["-Serie", port]
    # 🔴 LE PLAFOND DE `poser` EST **RE-DERIVE**, ⛔ PAS HERITE (dn7-6).
    #    Les 90 s par defaut de `_powershell()` ont ete choisies pour des
    #    verbes qui INTERROGENT. `poser` COMPOSE : deux `powershell.exe`
    #    imbriques, et `lancer` SEUL peut depenser 30 s d'attente sur son
    #    verrou (`dn_agent_tour.ps1`, `WaitOne(30000)`) PUIS 10 s de scrutation
    #    — avant meme son propre sous-processus de pre-vol. ⇒ un lancement
    #    dispute depasse 90 s a lui tout seul, et la page dirait « etat
    #    INCONNU » d'une tache REELLEMENT POSEE. C'est le meme motif que le
    #    plafond genereux du geste `pip`, applique au verbe le plus cher que
    #    cette page puisse poster.
    rc, sortie, cmd, echec = _powershell(
        arguments, timeout=DELAI_POSER if verbe == "poser" else 90)
    d = {"commande": " ".join(cmd), "sortie": sortie or "",
         "port_serie": port, "port_nom": nom_port, "port_motif": motif_port,
         "rc": rc if rc is not None else -1, "origine_pilote": origine,
         # 🔴 QUI A POSE CE CODE ? La page promet de rendre le code de retour
         #    « tel quel » : elle doit donc dire quand il ⛔ N'EST PAS celui de
         #    l'outil (2, 4, -1 et le 9 d'une tache survivante sont a ELLE).
         "rc_pose_par": "l'outil" if rc is not None else "la page"}
    if echec == "lancement":
        d["verdict"] = ("⛔ l'outil n'a pas pu etre LANCE : le geste n'a PAS eu "
                        "lieu. ⛔ Ce n'est pas un succes.")
        return d
    # 🔴 UN DELAI DEPASSE ⛔ NE REND PAS ICI, ET C'EST LE POINT DU CORRECTIF :
    #    l'outil a tourne, il peut AVOIR AGI, et `retirer` doit passer par la
    #    RE-REQUETE avant de conclure. Sortir avant elle ferait eviter la
    #    question au seul cas ou elle compte le plus.
    if verbe == "retirer":
        encore, _rl = tache_presente()
        if encore is True:
            d["verdict"] = ("⛔ ECHEC : la tache « %s » est TOUJOURS presente "
                            "apres le retrait — verifie PAR REQUETE, ⛔ pas par "
                            "le message ci-dessus." % nom_de_la_tache())
            if not d["rc"] or d["rc"] < 0:
                d["rc"] = 9
                d["rc_pose_par"] = "la page"
            return d
        if encore is False:
            d["verdict"] = ("✅ la tache « %s » est ABSENTE — re-interrogee "
                            "apres coup." % nom_de_la_tache())
            return d
        d["verdict"] = ("⚠️ la tache n'a pas pu etre re-interrogee : le retrait "
                        "n'est ⛔ PAS confirme.")
        if echec == "delai":
            d["verdict"] += (" ⚠️ Et l'outil a DEPASSE son delai : le geste a "
                             "PEUT-ETRE eu lieu, etat INCONNU.")
        return d
    if echec == "delai":
        d["verdict"] = ("⚠️ DELAI DEPASSE : l'outil a tourne mais n'a pas rendu "
                        "la main. Le geste a PEUT-ETRE eu lieu — etat INCONNU. "
                        "⛔ Ce n'est ni un succes ni un echec.")
        return d
    # 🔴 LES CODES DE `stop` NE SONT ⛔ PAS UN BOOLEEN, ET LES LIRE COMME TEL
    #    EST **DEUX FAUTES A LA FOIS**. `7` veut dire « l'agent est arrete, mais
    #    le port a DISPARU » — le cas NORMAL d'une carte debranchee ou reprise
    #    par WSL. Le compter pour un echec ferait renoncer quelqu'un dont le
    #    geste a REUSSI ; le compter pour un succes ferait annoncer « port
    #    rendu » sur un port qui n'existe plus. ⇒ on rend LE FAIT, nomme.
    if verbe == "stop":
        etat, phrase = CODES_STOP.get(rc, (None, None))
        d["etat_port"] = etat or "inattendu"
        if phrase:
            d["verdict"] = phrase
        else:
            d["verdict"] = ("⛔ l'outil a rendu %r, qui n'est AUCUN des codes "
                            "documentes de `stop` (0 · 4 · 7 · 8). ⛔ On ne "
                            "conclut ni « rendu » ni « tenu » : lire la sortie "
                            "ci-dessus." % rc)
        if not port:
            d["verdict"] += (" ⚠️ ET LE PORT N'A PAS ETE DECOUVERT (%s) : "
                             "l'outil a donc joue sur SON defaut, ⛔ pas sur un "
                             "port mesure. Ce verdict porte sur ce defaut."
                             % (motif_port or "motif inconnu"))
        return d
    # 🔴 `poser` A SA TABLE, POUR LA MEME RAISON QUE `stop` A LA SIENNE : sa
    #    demi-reussite `13` ⛔ n'est PAS un refus, et l'aplatir ferait
    #    CONTREDIRE a la page sa propre sortie brute.
    if verbe == "poser":
        phrase = CODES_POSER.get(rc)
        d["verdict"] = phrase if phrase else (
            "⛔ l'outil a rendu %r, qui n'est AUCUN des codes documentes de "
            "`poser`. ⛔ On ne conclut ⛔ ni « pose » ni « rien fait » : lire "
            "la sortie ci-dessus." % rc)
        return d
    d["verdict"] = ("✅ l'outil a rendu 0." if rc == 0 else
                    "⛔ l'outil a rendu %d — le refus remonte TEL QUEL, ⛔ il ne "
                    "devient pas un succes." % rc)
    return d


# ═══ LE GESTE DES DEPENDANCES, **JOUE** — ⛔ PLUS SEULEMENT PUBLIE (dn7-6) ══
# 🔴 ARBITRAGE OWNER DU 2026-09-10, VERBATIM : « elle install dans la mesure
#    du posible sinon elle expose ». `pip install --user …` est NON ELEVE, il
#    tourne avec l'interpreteur QUI SERT DEJA CETTE PAGE, et il n'exige rien
#    d'autre. ⇒ c'est le seul des deux gestes publies que la page PEUT jouer.
ROUTE_DEPENDANCES = "/api/dependances"
# ⚠️ UN PLAFOND **GENEREUX ET EXPLICITE**, ⛔ pas celui d'une sonde : une
#    installation telecharge des roues, peut compiler, et rien ne la cadence.
#    Le confondre avec les 90 s de `_powershell()` ferait rendre « delai
#    depasse » sur un geste qui allait aboutir.
DELAI_DEPENDANCES = 900
# Ce qu'un Python SANS `pip` imprime — MESURE, ⛔ pas suppose : `python -m pip`
# rend un `No module named pip` sur son erreur standard, avec un code non nul.
MARQUE_SANS_PIP = "No module named pip"
# 🔴 LE PLAFOND DE `poser`, NOMME ET SEPARE (dn7-6) — motif a `jouer_verbe()`.
DELAI_POSER = 300
# 🔴 ⛔ DEUX INSTALLATIONS EN MEME TEMPS, JAMAIS. Le serveur est un
#    `ThreadingHTTPServer` : un second onglet, ou un simple rechargement,
#    poste une seconde fois. Deux `pip` concurrents ecrivant dans le MEME
#    `site-packages` utilisateur est une corruption, ⛔ pas une lenteur.
#    ⚠️ Le refus est IMMEDIAT (`blocking=False`) : faire ATTENDRE le second
#       tiendrait une poignee HTTP pendant l'installation entiere.
_VERROU_PIP = threading.Lock()


def arguments_dependances():
    """La commande jouee, **DERIVEE** de `GESTE_DEPENDANCES`.

    🔴 ⛔ PAS UNE SECONDE CHAINE PARALLELE : la page PUBLIE ce geste a
       recopier, et le jouer depuis une autre redaction ferait DEUX sources de
       verite — celle qu'on lit et celle qui tourne. Elles divergeraient, et
       c'est la page qui mentirait.
    🔴 ET LE PREMIER MOT EST **REMPLACE**, ⛔ pas le reste : `pip` nu resout
       vers n'importe quel interpreteur du `PATH` — celui du Store, un
       environnement virtuel oublie, un Python 2. `sys.executable -m` cible
       l'interpreteur QUI SERT CETTE PAGE, c'est-a-dire celui dont l'agent se
       servira. ⚠️ Le reste des mots — le verbe et ses commutateurs — est pris
       TEL QUEL dans la chaine publiee.
    ⚠️ Rend `None` si la chaine publiee ne commence plus par `pip` : ⛔ on ne
       DEVINE pas une commande, on refuse."""
    mots = GESTE_DEPENDANCES.split()
    if not mots or mots[0] != "pip":
        return None
    return [sys.executable, "-m"] + mots


def jouer_dependances():
    """Joue le geste des dependances, NON ELEVE, et relaie tout TEL QUEL.

    🔴 TROIS ISSUES DISTINGUEES, comme `_powershell()` le fait deja :
       reussite · `pip` INDISPONIBLE · DELAI DEPASSE. ⛔ Jamais un succes
       annonce sur un geste qui n'a pas eu lieu, ⛔ jamais une trace nue."""
    if not _VERROU_PIP.acquire(blocking=False):
        return {"commande": "", "sortie": "", "rc": 2, "rc_pose_par": "la page",
                "verdict": "⚠️ une installation TOURNE DEJA (autre onglet, ou "
                           "rechargement) : celle-ci n'a PAS ete lancee. ⛔ Ce "
                           "n'est ni un succes ni un echec — attendre la "
                           "premiere."}
    try:
        return _jouer_dependances()
    finally:
        _VERROU_PIP.release()


def _jouer_dependances():
    """Le geste lui-meme. ⛔ Toujours appele SOUS `_VERROU_PIP`."""
    arguments = arguments_dependances()
    if arguments is None:
        return {"commande": "", "sortie": "", "rc": 2, "rc_pose_par": "la page",
                "verdict": "⛔ le geste publie ne commence pas par `pip` : "
                           "rien n'a ete tente. ⛔ Ce n'est pas un succes."}
    d = {"commande": " ".join(arguments), "rc_pose_par": "l'outil"}
    try:
        r = subprocess.run(arguments, cwd=RACINE, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=DELAI_DEPENDANCES)
    # 🔴 LE DELAI DEPASSE EST RENDU A PART, ET POUR LA MEME RAISON QUE DANS
    #    `_powershell()` : `TimeoutExpired` derive de `SubprocessError`, et le
    #    ranger avec lui ferait dire « le geste n'a PAS eu lieu » alors que
    #    l'installation A TOURNE et peut AVOIR ABOUTI.
    except subprocess.TimeoutExpired:
        d.update(sortie="", rc=-1, rc_pose_par="la page",
                 verdict="⚠️ DELAI DEPASSE (%d s) : l'installation a tourne "
                         "mais n'a pas rendu la main. Elle a PEUT-ETRE abouti "
                         "— etat INCONNU. ⛔ Ce n'est ni un succes ni un "
                         "echec." % DELAI_DEPENDANCES)
        return d
    except (OSError, subprocess.SubprocessError) as exc:
        d.update(sortie="%s : %s" % (type(exc).__name__, exc), rc=-1,
                 rc_pose_par="la page",
                 verdict="⛔ l'installation n'a pas pu etre LANCEE : le geste "
                         "n'a PAS eu lieu. ⛔ Ce n'est pas un succes.")
        return d
    sortie = (r.stdout or "") + (r.stderr or "")
    d.update(sortie=sortie, rc=r.returncode)
    # ⚠️ GARDE SUR LE CODE DE RETOUR, ⛔ pas sur le texte seul (dn7-6) : une
    #    installation qui REUSSIT peut porter cette chaine dans sa sortie (un
    #    journal de construction, les diagnostics d'une roue). La tester sans
    #    le `rc` ferait annoncer « le geste n'a PAS eu lieu » sur un geste
    #    ABOUTI — le MIROIR exact de la faute que ce bloc existe pour eviter.
    if r.returncode != 0 and MARQUE_SANS_PIP in sortie:
        # ⛔ UN PYTHON SANS `pip` N'EST PAS UNE INSTALLATION QUI A ECHOUE :
        #    c'est un geste qui n'a pas pu commencer, et son remede est
        #    AILLEURS. Les confondre enverrait relancer un bouton inutile.
        d["verdict"] = ("⛔ `pip` n'est pas disponible pour cet interpreteur : "
                        "le geste n'a PAS eu lieu, et il redevient un geste A "
                        "RECOPIER. ⛔ Ce n'est pas un succes.")
        return d
    d["verdict"] = ("✅ l'installation a rendu 0. ⚠️ Ce que ca dit : `pip` a "
                    "rendu 0. Ce qui TRANCHE, c'est l'etat re-sonde "
                    "ci-dessus, ⛔ pas ce code." if r.returncode == 0
                    else "⛔ l'installation a rendu %d — le refus remonte TEL "
                         "QUEL, ⛔ il ne devient pas un succes."
                         % r.returncode)
    return d


# ═══════════════════════════ LE SERVEUR ═══════════════════════════════════

# ⚠️ UNE LISTE BLANCHE, ⛔ PAS UN SERVEUR DE FICHIERS. Ce processus tourne dans
#    l'arbre du depot ; servir un chemin arbitraire donnerait a n'importe quelle
#    page ouverte dans ce navigateur de quoi le lire.
SERVIS = {
    "/": (PAGE, "text/html; charset=utf-8"),
    "/index.html": (PAGE, "text/html; charset=utf-8"),
    "/IDENTITE.md": (os.path.join(ICI, "IDENTITE.md"),
                     "text/plain; charset=utf-8"),
    "/README.md": (os.path.join(RACINE, "README.md"),
                   "text/plain; charset=utf-8"),
    "/LICENSING.md": (os.path.join(RACINE, "LICENSING.md"),
                      "text/plain; charset=utf-8"),
    # ── LA CHARGE, ADRESSE PAR ADRESSE ────────────────────────────────────
    # 🔴 SIX ENTREES ECRITES, ⛔ PAS UN PREFIXE OUVERT. La tentation etait de
    #    router `/charge/<n'importe quoi>` vers `CHARGE/<n'importe quoi>` : ce
    #    serait un serveur d'arborescence deguise, et `..` en ferait une porte
    #    sur tout le depot. Le controle qui garde cette liste blanche existe
    #    depuis `dn7-1` ; le contourner « juste pour la charge » aurait rouvert
    #    exactement ce qu'il avait ferme.
    "/charge/manifest.json": (MANIFESTE, "application/json; charset=utf-8"),
    "/charge/bootloader.bin": (os.path.join(CHARGE, "bootloader.bin"),
                               "application/octet-stream"),
    "/charge/partition-table.bin": (os.path.join(CHARGE, "partition-table.bin"),
                                    "application/octet-stream"),
    "/charge/desknode.bin": (os.path.join(CHARGE, "desknode.bin"),
                             "application/octet-stream"),
    "/charge/living_pcb_v0.bin": (os.path.join(CHARGE, "living_pcb_v0.bin"),
                                  "application/octet-stream"),
    "/charge/PROVENANCE.md": (os.path.join(CHARGE, "PROVENANCE.md"),
                              "text/plain; charset=utf-8"),
}

ETAT = {"sans_site_utilisateur": False}


# 🔴 LE PORT TIRE N'EST ⛔ PAS UN SECRET, ET C'EST TOUTE LA RAISON DE CE BLOC.
#    La plage ephemere se balaie en quelques secondes. Or un
#    `fetch(url, {method:"POST"})` SANS en-tete personnalise est une requete
#    SIMPLE : ⛔ aucun pre-vol CORS, donc n'importe quelle page ouverte dans le
#    meme navigateur pourrait declencher `retirer`. Et `/api/etat` est lisible
#    par re-liaison DNS — il rend le nom de la tache, le `RunLevel`, le chemin
#    du pilote et celui de l'interpreteur.
#    ⇒ ON REFUSE SUR DEUX EN-TETES, ET LES DEUX SONT NECESSAIRES :
#      · `Host` ferme la RE-LIAISON DNS — un nom d'attaquant qui resout vers
#        127.0.0.1 arrive avec SON nom dans `Host`, ⛔ pas le notre ;
#      · `Origin`, **quand il est present**, ferme le POST inter-origine — un
#        navigateur le pose sur toute requete non-navigationnelle.
#    ⚠️ `Origin` ABSENT n'est ⛔ pas un refus : une navigation ordinaire vers la
#       page n'en porte pas. C'est `Host` qui garde ce cas-la.
def _hotes_permis(port):
    return ("127.0.0.1:%d" % port, "localhost:%d" % port, "[::1]:%d" % port)


def _origines_permises(port):
    return tuple("http://" + h for h in _hotes_permis(port))


class Poignee(BaseHTTPRequestHandler):
    server_version = "dn-installeur/dn7-1"

    def log_message(self, fmt, *a):          # ⛔ pas de journal sur stderr
        pass

    def _refus(self):
        """Le motif du refus, ou `None`. ⛔ Appele sur les DEUX verbes HTTP.

        ⚠️ Le port reellement lie est TRANSMIS A LA POIGNEE apres le `bind`
           (`srv.dn_port`), ⛔ jamais reconstruit ici : `PORT_DEMANDE` vaut 0."""
        port = getattr(self.server, "dn_port", None)
        if port is None:
            # ⛔ ON REFUSE PLUTOT QUE DE LAISSER PASSER : sans le port reel, la
            #    comparaison n'a pas de sens, et « on ne sait pas » ⛔ n'est pas
            #    « c'est bon ».
            return ("le port reellement lie n'a pas ete transmis a la poignee "
                    "— ⛔ rien ne peut etre compare")
        hote = (self.headers.get("Host") or "").strip()
        if hote not in _hotes_permis(port):
            return ("en-tete `Host` refuse : %r — attendu `127.0.0.1:%d` ou "
                    "`localhost:%d`" % (hote, port, port))
        origine = self.headers.get("Origin")
        if origine is not None and origine.strip() not in _origines_permises(port):
            return ("en-tete `Origin` refuse : %r — cette page ne se pilote que "
                    "depuis elle-meme" % origine.strip())
        return None

    def _garde(self):
        motif = self._refus()
        if not motif:
            return True
        self._repondre(403, "\u26d4 REFUS : %s\n\nCe serveur n'accepte que la page "
                       "qu'il sert lui-meme, sur la boucle locale. Rien n'a ete "
                       "lu, rien n'a ete tente." % motif,
                       "text/plain; charset=utf-8")
        return False

    def _repondre(self, code, corps, ctype):
        b = corps if isinstance(corps, bytes) else corps.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(b)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, code, obj):
        self._repondre(code, json.dumps(obj, ensure_ascii=False),
                       "application/json; charset=utf-8")

    def do_GET(self):
        if not self._garde():
            return
        chemin = self.path.split("?", 1)[0]
        if chemin == "/api/etat":
            self._json(200, etat_machine(ETAT["sans_site_utilisateur"]))
            return
        if chemin in SERVIS:
            fichier, ctype = SERVIS[chemin]
            try:
                with open(fichier, "rb") as fh:
                    self._repondre(200, fh.read(), ctype)
            except OSError as exc:
                self._repondre(404, "introuvable : %s (%s)"
                               % (chemin, type(exc).__name__),
                               "text/plain; charset=utf-8")
            return
        self._repondre(404, "⛔ rien a cette adresse : %s" % chemin,
                       "text/plain; charset=utf-8")

    def do_POST(self):
        if not self._garde():
            return
        chemin = self.path.split("?", 1)[0]
        # 🔴 LA ROUTE NEUVE HERITE DE LA GARDE **SANS UNE LIGNE DE CODE**, et
        #    c'est pour ca qu'elle vit ICI : `_garde()` est appelee en PREMIERE
        #    ligne de `do_POST`, AVANT le moindre parsing de chemin. La sortir
        #    d'ici — dans une methode a elle, dans `do_GET` — la ferait
        #    repondre SANS refus `Origin`/`Host`, et ⚠️ `(c27)` de
        #    `verif_installeur_dn71.py` ⛔ NE CONNAIT QUE LES DEUX VERBES
        #    EXISTANTS : il epinglerait VERT le meme defaut ailleurs.
        if chemin == ROUTE_DEPENDANCES:
            self._json(200, jouer_dependances())
            return
        prefixe = "/api/agent/"
        if chemin.startswith(prefixe):
            self._json(200, jouer_verbe(chemin[len(prefixe):]))
            return
        self._repondre(404, "⛔ rien a cette adresse : %s" % chemin,
                       "text/plain; charset=utf-8")


# ═══════════════════════════ LE PRE-VOL ═══════════════════════════════════

def prevol(sans_site_utilisateur):
    """Dit ce qui manque, AVEC LE GESTE — ⛔ jamais une trace nue."""
    print("=" * 74)
    print("DeskNode - installeur local   (pre-vol)")
    print("=" * 74)
    print("  Python              : %d.%d.%d  (%s)"
          % (sys.version_info[0], sys.version_info[1], sys.version_info[2],
             sys.executable))
    manque_page = not os.path.exists(PAGE)
    if manque_page:
        print("  /!\\ la page        : INTROUVABLE (%s)" % PAGE)
        print("     Le dossier `installeur/` est incomplet : re-telecharger ou")
        print("     re-cloner le depot.")
    else:
        print("  la page             : %s" % PAGE)
    pilote, origine = localiser_pilote()
    print("  l'outil de l'agent  : %s  [%s]" % (pilote or "INTROUVABLE", origine))
    arbre = arbre_parent_present()
    if not arbre:
        print("")
        print("  /!\\ CE DOSSIER A ETE RECUPERE SEUL, HORS DE SON DEPOT.")
        print("      `tools/dn_agent_tour.ps1` et `README.md` ne sont pas au-")
        print("      dessus de lui. La page s'ouvrira, mais ses DEUX BOUTONS")
        print("      seront inactifs et ses liens de bas de page vides.")
        print("      LE GESTE : recuperer le depot ENTIER, puis relancer ce")
        print("      fichier depuis le dossier `installeur/` qu'il contient.")
    if not pilote:
        print("")
        print("  /!\\ SANS `dn_agent_tour.ps1`, LES DEUX GESTES SONT MORTS.")
        print("      La page ne pourra ni arreter ni retirer l'agent : elle")
        print("      n'a rien a appeler. Ce n'est PAS \" tout est la \".")

    manquantes, non_testables = [], []
    for m in DEPENDANCES_AGENT:
        ok = dependance_presente(m, sans_site_utilisateur)
        print("  %-19s : %s" % (m, "present" if ok is True else
                                "ABSENT" if ok is False else "non testable"))
        if ok is False:
            manquantes.append(m)
        elif ok is None:
            non_testables.append(m)
    if non_testables:
        # ⚠️ UNE IGNORANCE N'EST ⛔ PAS UN ECART : on la dit, et elle ⛔ ne pese
        #    PAS sur le code de retour.
        print("")
        print("  (i) sonde impossible pour : %s - ce n'est PAS \" absent \"."
              % " et ".join(non_testables))
    if manquantes:
        print("")
        print("  /!\\ ECART DECLARE - ce n'est PAS une panne de l'installeur.")
        print("     DeskNode ne se telecharge pas encore en UN seul morceau :")
        print("     l'agent a besoin de %s." % " et de ".join(manquantes))
        print("")
        print("       %s" % GESTE_DEPENDANCES)
        print("")
        print("     Porteur du retour a un seul telechargement : %s."
              % PORTEUR_ECART)
        print("     La page s'ouvre quand meme : arreter et retirer l'agent")
        print("        ne demande aucun de ces deux modules.")
    # ── LHM : L'AUTRE MOITIE DE L'ECART, ET ⛔ PAS UN MODULE PYTHON ────────
    # 🔴 IL A **SON** BLOC ET **SON** GESTE, ET IL ⛔ N'ENTRE PAS DANS
    #    `manquantes`. Ce n'est pas une elegance de redaction : `manquantes`
    #    commande A LA FOIS le `6` ET le bloc qui publie `GESTE_DEPENDANCES`,
    #    c'est-a-dire `pip install --user psutil pyserial`. Y verser LHM ferait
    #    imprimer LE MAUVAIS GESTE — un geste qui ⛔ ne peut pas reussir — et
    #    bougerait un code de sortie que `README.md` publie et que `(c28)` de
    #    `tools/verif_installeur_dn71.py` JOUE.
    # ⚠️ CE PRE-VOL-CI **CONSTATE**, il ⛔ ne refuse pas : flasher la carte n'a
    #    rien a voir avec LHM. Celui qui REFUSE est `tools/dn_agent_tour.ps1`,
    #    et il refuse sur son propre code de sortie.
    lhm = lhm_present()
    print("  %-19s : %s" % ("LibreHardwareMonitor",
                            "present" if lhm is True else
                            "ABSENT" if lhm is False else "non testable"))
    if lhm is False:
        print("")
        print("  /!\\ ECART DECLARE (2) - LHM N'EST PAS UN MODULE PYTHON,")
        print("      ET SON GESTE N'EST PAS ` pip `.")
        print("     Sans lui, %s" % PERTE_LHM)
        print("     resteront a \" -- \" sur la dalle, POUR TOUJOURS : c'est")
        print("     LHM qui lit ces sondes-la, et lui seul. Le reste ne bouge")
        print("     pas - le % CPU, les GHz, les Mo/s et l'AMBIANCE n'en")
        print("     dependent pas.")
        print("")
        print("       %s" % GESTE_LHM)
        print("")
        print("     Ce script demande des droits administrateur, et c'est LUI")
        print("     qui les coute : l'agent DeskNode, lui, n'en demande aucun.")
        print("     Sans argument, le meme script VERIFIE et ne change RIEN.")
        print("     La page s'ouvre quand meme, et POSER LE FIRMWARE SUR LA")
        print("        CARTE ne depend pas de LHM.")
    elif lhm is None:
        # ⚠️ UNE IGNORANCE N'EST ⛔ PAS UN ECART : on la dit, et elle ⛔ ne pese
        #    PAS sur le code de retour.
        print("")
        print("  (i) sonde LHM impossible : agent/dn_agent.py ne se lit pas,")
        print("      ou ne publie pas son adresse - ce n'est PAS \" absent \".")
    # ── LA CHARGE : CE QU'ON VA POSER SUR LA CARTE ────────────────────────
    # 🔴 ⛔ PAS UNE TRACE NUE, ET ⛔ PAS UN SILENCE NON PLUS. Sans charge, la
    #    page afficherait un bouton d'installation qui echouerait sur un 404 du
    #    navigateur — c'est-a-dire le defaut meme que cette marche corrige :
    #    un message d'outil qui n'explique rien.
    ch = etat_charge()
    print("")
    print("  la charge a poser    : %s" % ch["dossier"])
    if ch["version"]:
        # ⚠️ C'est ce que le MANIFESTE annonce. Qu'il soit EGAL au champ
        #    `esp_app_desc_t.version` du `desknode.bin` servi a cote est
        #    verifie MECANIQUEMENT par `tools/verif_flash_dn72.py`, ⛔ pas ici :
        #    un pre-vol qui rejouerait la gate donnerait deux sources de verite.
        print("  version au manifeste : %s" % ch["version"])
    for nom in IMAGES + ("manifest.json",):
        taille = ch["tailles"].get(nom)
        print("  %-20s : %s" % (nom, "%d o" % taille if taille is not None
                                else "ABSENT"))
    print("  asset (integrite)    : %s" % ch["asset"])
    if not ch["complete"]:
        print("")
        print("  /!\\ LA CHARGE EST ABSENTE OU ABIMEE - LA PAGE NE POURRA RIEN")
        print("      POSER SUR LA CARTE.")
        if ch["manquants"]:
            print("      manquant(s) : %s" % " ".join(ch["manquants"]))
        if ch["vides"]:
            print("      vide(s)     : %s" % " ".join(ch["vides"]))
        if ch["ecart_manifeste"]:
            print("      manifeste   : %s" % ch["ecart_manifeste"])
        if not ch["asset"].startswith("intact"):
            print("      asset       : %s" % ch["asset"])
        print("      LE GESTE : recuperer le depot ENTIER (le dossier")
        print("        installeur/charge/ en fait partie), ou le reconstruire :")
        print("          . $HOME/esp/esp-idf/export.sh")
        print("          cd firmware/desknode && idf.py reconfigure && idf.py build")
        print("        puis recopier les 4 .bin - voir installeur/charge/")
        print("        PROVENANCE.md, qui donne les commandes exactes.")
    # 🔴 `3` COUVRE LA PAGE **ET** L'OUTIL — la docstring l'annoncait deja
    #    (« Python n'a pas trouve la page **ou l'outil** ») et le code ne le
    #    faisait pas : sur une machine sans outil, le pre-vol annoncait
    #    « tout est la » pendant que les deux gestes exposes etaient morts.
    if manque_page or not pilote:
        return 3
    # ⚠️ `5` PASSE **AVANT** `6`, ET C'EST UN ORDRE, ⛔ PAS UN HASARD : une
    #    charge absente empeche le geste PRINCIPAL de la page (poser le
    #    firmware), tandis qu'un module d'agent manquant est un ECART DECLARE
    #    dont le reste du parcours se moque. Le code le plus grave gagne.
    if not ch["complete"]:
        return 5
    return 6 if manquantes else 0


def _ouvrir(url):
    """Ouvre le navigateur — et ⛔ ne SUPPOSE pas qu'il s'est ouvert.

    ⚠️ `webbrowser.open()` rend `False` quand il n'a trouve personne, et il
       peut lever. Sans ce controle, une machine sans navigateur par defaut
       laissait une fenetre muette devant une adresse que personne n'avait
       ecrite pour etre recopiee."""
    ouvert = False
    try:
        ouvert = bool(webbrowser.open(url))
    except Exception as exc:                              # noqa: BLE001
        print("  /!\\ ouverture du navigateur impossible : %s : %s"
              % (type(exc).__name__, exc))
    if not ouvert:
        print("")
        print("  /!\\ AUCUN NAVIGATEUR N'A PU ETRE OUVERT AUTOMATIQUEMENT.")
        print("      COLLER CETTE ADRESSE dans Edge ou Chrome :")
        print("        %s" % url)


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--verifier", action="store_true",
                    help="joue le pre-vol et sort, sans rien servir")
    ap.add_argument("--sans-site-utilisateur", action="store_true",
                    help="INSTRUMENT DE MESURE : ecarte le site utilisateur de "
                         "Python pour REPRODUIRE l'absence de psutil/pyserial")
    ap.add_argument("--sans-navigateur", action="store_true",
                    help="sert la page mais n'ouvre aucun navigateur")
    a = ap.parse_args()
    ETAT["sans_site_utilisateur"] = a.sans_site_utilisateur

    rc = prevol(a.sans_site_utilisateur)
    if a.verifier:
        return rc
    if rc == 3:
        return rc
    # ⚠️ `5` (charge absente) ⛔ N'ARRETE PAS LE SERVICE ICI, ET C'EST UN CHOIX
    #    ECRIT, ⛔ pas un oubli. Le SEUL POINT D'ENTREE d'un inconnu est le
    #    `.bat`, qui refuse d'aller plus loin sur ce meme etat (`:SANSCHARGE`,
    #    `RC=5`) et lui donne le geste AVANT d'ouvrir quoi que ce soit. Celui
    #    qui arrive jusqu'ici a lance Python A LA MAIN : c'est quelqu'un qui
    #    developpe, et pour lui une page qui OUVRE en nommant precisement ce qui
    #    manque vaut mieux qu'un refus. ⇒ la page porte l'etat de la charge, et
    #    `--verifier` reste l'instrument MECANIQUE qui rend `5`.

    try:
        srv = ThreadingHTTPServer((ADRESSE, PORT_DEMANDE), Poignee)
    except OSError as exc:
        # 🔴 ⛔ PAS UNE TRACE NUE DANS UNE FENETRE DOUBLE-CLIQUEE : c'est
        #    exactement ce qu'`AC7.1.6` interdit. Un `bind` peut echouer
        #    (boucle locale filtree, pare-feu, politique de la machine), et
        #    l'inconnu doit lire une phrase, ⛔ pas un `Traceback`.
        print("")
        print("  /!\\ LE SERVEUR LOCAL N'A PAS PU DEMARRER.")
        print("      %s : %s" % (type(exc).__name__, exc))
        print("      La boucle locale 127.0.0.1 est refusee ou filtree sur")
        print("      cette machine (pare-feu, antivirus, politique).")
        print("      Rien n'a ete installe, rien n'a ete change.")
        return 4
    # 🔴 LE PORT REEL EST **RELU**, ⛔ jamais reaffirme. C'est ce qui rend
    #    l'adresse annoncee vraie par construction.
    port_reel = srv.server_address[1]
    # ⚠️ ET IL EST **TRANSMIS A LA POIGNEE** : c'est lui, ⛔ pas `PORT_DEMANDE`
    #    (qui vaut 0), que `_refus()` compare aux en-tetes `Host` et `Origin`.
    srv.dn_port = port_reel
    url = "http://%s:%d/" % (ADRESSE, port_reel)
    print("")
    print("=" * 74)
    print("  la page est servie ICI  ->  %s" % url)
    print("  (port TIRE au lancement : il change a chaque fois, et c'est voulu)")
    print("  Fermer cette fenetre, ou Ctrl+C, arrete le serveur.")
    print("=" * 74)
    if not a.sans_navigateur:
        threading.Timer(0.4, _ouvrir, args=(url,)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  arret demande.")
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

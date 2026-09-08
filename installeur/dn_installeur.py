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
    6  une dependance de l'agent manque (l'ecart declare de `FR7.1`)
"""

import argparse
import io
import json
import os
import re
import subprocess
import sys
import threading
import webbrowser
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
VERBES = ("stop", "retirer")

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
        "python_version": "%d.%d.%d" % sys.version_info[:3],
        "python_executable": sys.executable,
        "psutil": deps.get("psutil"),
        "pyserial": deps.get("pyserial"),
        "manquantes": manquantes,
        "non_testables": non_testables,
        "arbre_parent": arbre_parent_present(),
        "geste": GESTE_DEPENDANCES,
        "porteur_ecart": PORTEUR_ECART,
        "tache_nom": nom_de_la_tache(),
        "tache_presente": presente,
        "tache_runlevel": runlevel,
        "pilote": pilote,
        "pilote_origine": origine,
        "verbes": list(VERBES),
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
    rc, sortie, cmd, echec = _powershell(["-File", pilote, verbe])
    d = {"commande": " ".join(cmd), "sortie": sortie or "",
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
    d["verdict"] = ("✅ l'outil a rendu 0." if rc == 0 else
                    "⛔ l'outil a rendu %d — le refus remonte TEL QUEL, ⛔ il ne "
                    "devient pas un succes." % rc)
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
    # 🔴 `3` COUVRE LA PAGE **ET** L'OUTIL — la docstring l'annoncait deja
    #    (« Python n'a pas trouve la page **ou l'outil** ») et le code ne le
    #    faisait pas : sur une machine sans outil, le pre-vol annoncait
    #    « tout est la » pendant que les deux gestes exposes etaient morts.
    if manque_page or not pilote:
        return 3
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

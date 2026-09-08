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

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICI = os.path.join(RACINE, "installeur")
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
       ca se voit, ⛔ pas six mois plus tard sur un refus incomprehensible."""
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
    except (OSError, subprocess.SubprocessError) as exc:
        return None, "%s : %s" % (type(exc).__name__, exc), cmd
    return r.returncode, (r.stdout or "") + (r.stderr or ""), cmd


def localiser_pilote():
    """Ou vit le `dn_agent_tour.ps1` qui pilote l'agent DE CETTE MACHINE.

    🔴 ⛔ PAS UN CHEMIN EN DUR, ET ⛔ PAS NON PLUS « celui du depot, forcement ».
       Le verbe `stop` est PROPRE parce qu'il pose un fichier-drapeau **a cote de
       l'agent** ; appeler une copie qui vit ailleurs poserait le drapeau la ou
       personne ne le lit, et l'arret retomberait sur le `taskkill` qui PERD le
       bilan de fin. ⇒ on demande au systeme ou est l'outil qu'il lance
       reellement (l'action de la tache planifiee le DIT), et on ne se rabat sur
       la copie du depot que faute de tache."""
    rc, sortie, _ = _powershell([
        "-Command",
        "$t = Get-ScheduledTask -TaskName '%s' -ErrorAction SilentlyContinue; "
        "if ($t) { ($t.Actions | Select-Object -First 1).Arguments }"
        % nom_de_la_tache()], timeout=45)
    if rc == 0 and sortie:
        m = RE_FICHIER_PS1.search(sortie)
        if m and os.path.exists(m.group(1)):
            return m.group(1), "l'action de la tache planifiee"
    if os.path.exists(PILOTE_DEPOT):
        return PILOTE_DEPOT, "la copie du depot (aucune tache posee)"
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
    rc, sortie, _ = _powershell([
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


def etat_machine(sans_site_utilisateur=False):
    presente, runlevel = tache_presente()
    pilote, origine = localiser_pilote()
    manquantes = []
    deps = {}
    for m in DEPENDANCES_AGENT:
        ok = dependance_presente(m, sans_site_utilisateur)
        deps[m] = bool(ok)
        if not ok:
            manquantes.append(m)
    return {
        "python_version": "%d.%d.%d" % sys.version_info[:3],
        "python_executable": sys.executable,
        "psutil": deps.get("psutil", False),
        "pyserial": deps.get("pyserial", False),
        "manquantes": manquantes,
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
        return {"commande": "", "sortie": "", "rc": 2,
                "verdict": "⛔ verbe non expose par cette page : %s" % verbe}
    pilote, origine = localiser_pilote()
    if not pilote:
        return {"commande": "", "sortie": "", "rc": 4,
                "verdict": "⛔ `dn_agent_tour.ps1` INTROUVABLE — rien n'a ete "
                           "tente. ⛔ Ce n'est pas un succes."}
    rc, sortie, cmd = _powershell(["-File", pilote, verbe])
    d = {"commande": " ".join(cmd), "sortie": sortie or "",
         "rc": rc if rc is not None else -1, "origine_pilote": origine}
    if rc is None:
        d["verdict"] = ("⛔ l'outil n'a pas pu etre lance : le geste n'a PAS eu "
                        "lieu. ⛔ Ce n'est pas un succes.")
        return d
    if verbe == "retirer":
        encore, _rl = tache_presente()
        if encore is True:
            d["verdict"] = ("⛔ ECHEC : la tache « %s » est TOUJOURS presente "
                            "apres le retrait — verifie PAR REQUETE, ⛔ pas par "
                            "le message ci-dessus." % nom_de_la_tache())
            d["rc"] = d["rc"] or 9
            return d
        if encore is False:
            d["verdict"] = ("✅ la tache « %s » est ABSENTE — re-interrogee "
                            "apres coup." % nom_de_la_tache())
            return d
        d["verdict"] = ("⚠️ la tache n'a pas pu etre re-interrogee : le retrait "
                        "n'est ⛔ PAS confirme.")
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


class Poignee(BaseHTTPRequestHandler):
    server_version = "dn-installeur/dn7-1"

    def log_message(self, fmt, *a):          # ⛔ pas de journal sur stderr
        pass

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

    manquantes = []
    for m in DEPENDANCES_AGENT:
        ok = dependance_presente(m, sans_site_utilisateur)
        print("  %-19s : %s" % (m, "present" if ok else
                                "ABSENT" if ok is False else "non testable"))
        if not ok:
            manquantes.append(m)
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
    if manque_page:
        return 3
    return 6 if manquantes else 0


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

    srv = ThreadingHTTPServer((ADRESSE, PORT_DEMANDE), Poignee)
    # 🔴 LE PORT REEL EST **RELU**, ⛔ jamais reaffirme. C'est ce qui rend
    #    l'adresse annoncee vraie par construction.
    port_reel = srv.server_address[1]
    url = "http://%s:%d/" % (ADRESSE, port_reel)
    print("")
    print("=" * 74)
    print("  la page est servie ICI  ->  %s" % url)
    print("  (port TIRE au lancement : il change a chaque fois, et c'est voulu)")
    print("  Fermer cette fenetre, ou Ctrl+C, arrete le serveur.")
    print("=" * 74)
    if not a.sans_navigateur:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  arret demande.")
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

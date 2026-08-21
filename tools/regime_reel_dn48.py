#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""regime_reel_dn48.py — le REGIME REEL, mesure DEPUIS LA TOUR (AC7 + AC8).

🔴 POURQUOI IL EXISTE. `pc` vit sur la console de la carte, et l'agent vit sur
   COM3 : sous Windows le port est EXCLUSIF, les deux NE COEXISTENT PAS. Or AC7
   exige `pc` sur l'agent REEL (⛔ pas seulement par injection) et AC8 exige de
   lire `pc` pendant que LHM est coupe.
⇒ Ce script fait les deux DANS LE MEME PROCESSUS : il lit les compteurs, lance
  l'agent pour une duree bornee, puis rouvre le port IMMEDIATEMENT — dans la
  fenetre de PEREMPTION de 3 s, sinon les valeurs qu'on vient de mesurer sont
  deja mortes et on lirait « -- » partout SANS QUE CE SOIT LE SUJET.

🔴 LA GARDE QUI COMPTE, ET ELLE A DEJA COUTE TROIS SESSIONS : sous Windows,
   `pyserial` pose DTR et RTS a l'ouverture, et cette sequence est EXACTEMENT
   celle d'un reset de puce. Symptome paye : trois sessions serie de suite
   retrouvees « liaison jamais recue », COMPTEURS WIPES, pendant que l'agent
   croyait avoir tout envoye. ⇒ `dtr=False, rts=False` AVANT `open()`.
⚠️ ET LA PARADE EST **WINDOWS-ONLY** : sous Linux elle PROVOQUE le reset qu'elle
   pretend empecher (A/B mesure). D'ou le test sur `sys.platform`, ⛔ pas une
   application inconditionnelle.

⛔ CE QU'IL NE FAIT PAS : il ne coupe ni ne demarre LHM. C'est un GESTE OWNER.

Usage (sur le Python Windows de la tour) :
    python regime_reel_dn48.py --duree 20
    python regime_reel_dn48.py --duree 20 --port COM3
"""
import argparse
import os
import re
import subprocess
import sys
import time

import serial

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT = os.path.join(RACINE, "agent", "dn_agent.py")

COMPTEURS = ("tronquee", "trop longue", "checksum", "version", "format", "bornes")
_LIGNE_REJ = re.compile(
    r"^rejets\s*:\s*tronquee\s+(\d+)\s*\u00b7\s*trop longue\s+(\d+)\s*\u00b7\s*"
    r"checksum\s+(\d+)\s*\u00b7\s*version\s+(\d+)\s*\u00b7\s*format\s+(\d+)\s*"
    r"\u00b7\s*bornes\s+(\d+)\s*$", re.M)


def _extraire(txt):
    m = _LIGNE_REJ.search(txt)
    if not m:
        raise RuntimeError(
            "ligne `rejets :` introuvable dans la sortie de `pc`. \u26d4 REFUS DE "
            "RENDRE DES ZEROS : un parseur permissif ferait conclure « aucun "
            "compteur n'a bouge » sur une carte qui repond parfaitement.")
    return dict(zip(COMPTEURS, (int(g) for g in m.groups())))


def autotest():
    """\U0001f534 Le parseur se prouve sur une ligne FABRIQUEE avant d'etre cru."""
    faux = ("rejets     : tronquee 3 \u00b7 trop longue 1 \u00b7 checksum 4 \u00b7 "
            "version 1 \u00b7 format 5 \u00b7 bornes 9\n")
    if _extraire(faux) != {"tronquee": 3, "trop longue": 1, "checksum": 4,
                           "version": 1, "format": 5, "bornes": 9}:
        sys.exit("\u26d4 AUTO-TEST DU PARSEUR ECHOUE")
    try:
        _extraire("rien ici\n")
    except RuntimeError:
        pass
    else:
        sys.exit("\u26d4 AUTO-TEST : le parseur rend quelque chose sans la ligne")
    print("[regime] auto-test du parseur : OK (il lit une ligne fabriquee, et il "
          "LEVE quand elle manque)")


def ouvrir(port, baud=115200):
    """\U0001f534 DTR/RTS BAS **AVANT** open() — et UNIQUEMENT sous Windows."""
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = baud
    ser.timeout = 0.3
    if sys.platform == "win32":
        ser.dtr = False
        ser.rts = False
    ser.open()
    return ser


def cmd(ser, commande, timeout=5.0):
    ser.reset_input_buffer()
    ser.write((commande + "\n").encode("ascii"))
    ser.flush()
    fin = time.time() + timeout
    buf = b""
    while time.time() < fin:
        buf += ser.read(4096)
        if b"desknode>" in buf:
            break
    return buf.decode("utf-8", "replace")


def main():
    for f in (sys.stdout, sys.stderr):
        try:
            f.reconfigure(encoding="utf-8")
        except Exception:
            pass
    p = argparse.ArgumentParser()
    p.add_argument("--port", default="COM3")
    p.add_argument("--duree", type=int, default=20)
    p.add_argument("--python", default=sys.executable)
    a = p.parse_args()

    print("=" * 88)
    print("dn4-8 / AC7-AC8 — REGIME REEL : l'agent sur %s, puis `pc` DANS la "
          "peremption" % a.port)
    print("=" * 88)
    autotest()

    ser = ouvrir(a.port)
    try:
        cmd(ser, "")                       # reveil
        avant_txt = cmd(ser, "pc")
        avant = _extraire(avant_txt)
        print("[regime] compteurs de rejet AVANT : %s" % avant)
    finally:
        ser.close()
    time.sleep(0.4)                        # laisser Windows relacher le port

    print("[regime] agent : %d s sur %s ..." % (a.duree, a.port))
    t0 = time.time()
    pr = subprocess.run([a.python, AGENT, "--serie", a.port,
                         "--duree", str(a.duree)],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    mur = time.time() - t0
    _ = mur  # duree murale de l'agent, gardee pour le journal

    # \U0001f534 LA COURSE CONTRE LA PEREMPTION COMMENCE ICI. 3 s, pas plus.
    t_reouv = time.time()
    ser = ouvrir(a.port)
    tirs = 0
    try:
        cmd(ser, "")
        # 🔴 LA CAPTURE HOTE PERD DES LIGNES — c'est MESURE, pas suppose : le
        #    2026-08-20 deux captures de `dn_console.py` sont revenues
        #    ENTIEREMENT VIDES, et le 2026-08-21 celle-ci a perdu `cpu` et `gpu`,
        #    c'est-a-dire les PREMIERES lignes du bloc. ⛔ LE MECANISME N'EST PAS
        #    ETABLI, et je ne le nomme pas.
        # ⇒ On RELIT jusqu'a obtenir les cinq metriques, dans la fenetre de
        #   peremption. Un tir supplementaire coute ~0,3 s ; la peremption est a
        #   3,00 s, et le DELAI EST PUBLIE pour que le lecteur juge lui-meme.
        # ⚠️ ⛔ On ne CONCATENE PAS les tirs : deux lectures a des instants
        #    differents melangeraient deux etats. On garde LE tir complet.
        for tirs in range(1, 4):
            vue = cmd(ser, "pc")
            if len([m for m in ("cpu", "gpu", "ram", "net", "disk")
                    if re.search(r"^\s*%s\s+->" % m, vue, re.M)]) == 5:
                break
    finally:
        ser.close()
    print("[regime] capture obtenue au tir %d (\u26a0\ufe0f la capture hote perd "
          "des lignes : defaut MESURE, mecanisme NON etabli)" % tirs)
    # ⚠️ LE DELAI EST MESURE, ⛔ pas suppose : c'est lui qui dit si les valeurs
    #    lues sont encore FRAICHES. Au-dela de 3,00 s elles ont perime et `pc`
    #    montrerait « -- » partout SANS QUE CE SOIT LE SUJET.
    delai = time.time() - t_reouv
    apres = _extraire(vue)

    print("\n" + "-" * 88)
    print("BILAN DE L'AGENT (stderr) :")
    print("-" * 88)
    sys.stdout.write(pr.stderr.decode("utf-8", "replace"))

    print("\n" + "-" * 88)
    print("`pc` RELU %.2f s apres l'arret de l'agent (peremption = 3,00 s) — "
          "%s" % (delai, "FRAIS" if delai < 3.0 else
                  "\u26d4 PERIME : ce releve ne vaut RIEN, refaire"))
    print("-" * 88)
    # \u26a0\ufe0f SORTIE INTEGRALE, \u26d4 PAS FILTREE. Un filtre qui rate une ligne
    #    fait conclure « la metrique est absente » sur une metrique presente —
    #    et gratter au motif une console redigee pour un humain FABRIQUE des
    #    absences aussi bien que des nombres.
    for l in vue.splitlines():
        if l.strip():
            print("  " + l.rstrip())

    # 🔴 COMPTER CE QU'ON A CAPTURE AVANT DE PUBLIER — ET CE N'EST PAS UNE
    #    PRECAUTION THEORIQUE. Le 2026-08-21, une capture de ce meme outil a rendu
    #    QUATRE metriques sur cinq : `disk` manquait. ⛔ Le firmware, lui, l'avait
    #    imprimee — `dn_link_vue()` ne peut PAS rendre `false` pour une metrique
    #    valide (elle ne le fait que hors bornes ou sur `out` NULL, dn_link.c:539).
    #    C'est LA CAPTURE HOTE qui a perdu la ligne, defaut deja MESURE sur
    #    `dn_console.py` (deux captures entierement vides le 2026-08-20).
    # ⚠️ UN INSTRUMENT QUI NE SAIT PAS DISTINGUER « ABSENTE » DE « NON CAPTUREE »
    #    FABRIQUE DES ABSENCES. Celui-ci le dit maintenant.
    vues = [m for m in ("cpu", "gpu", "ram", "net", "disk")
            if re.search(r"^\s*%s\s+->" % m, vue, re.M)]
    if len(vues) != 5:
        manquantes = [m for m in ("cpu", "gpu", "ram", "net", "disk")
                      if m not in vues]
        print("\n\u2716\ufe0f  CAPTURE INCOMPLETE : %d metrique(s) sur 5 dans la sortie "
              "(manquent : %s)." % (len(vues), ", ".join(manquantes)))
        print("   \u26d4 NE PAS CONCLURE « la metrique est absente » : le firmware "
              "imprime les CINQ inconditionnellement.")
        print("   \u21d2 c'est la CAPTURE qui a perdu des lignes. Refaire le tir.")
        return 1
    print("\n[regime] capture COMPLETE : les 5 metriques sont dans la sortie.")

    delta = {k: apres[k] - avant[k] for k in COMPTEURS}
    bouges = {k: v for k, v in delta.items() if v}
    print("\n" + "-" * 88)
    if bouges:
        print("\u2716\ufe0f  DES COMPTEURS DE REJET ONT MONTE : %s" % bouges)
        print("   \u26d4 Une ABSENCE DE DONNEE N'EST PAS UNE ERREUR DE PROTOCOLE.")
        print("   C'est le controle le plus discriminant d'AC8, et il ECHOUE.")
        return 1
    print("\u2705 AUCUN COMPTEUR DE REJET N'A MONTE (les six a zero de delta).")
    print("   \U0001f3af C'est le controle le plus discriminant d'AC8 : une absence de")
    print("   donnee se dit par un CHAMP VIDE, \u26d4 jamais par un rejet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

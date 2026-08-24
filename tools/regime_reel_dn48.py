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

# 🔴 2e REVUE (2026-08-24) — LA LIGNE `trames :` EST CE QUI PROUVE LA RECEPTION,
#    ET ELLE N'ETAIT PAS LUE. Cet instrument ne lisait que `rejets :` et
#    concluait `bouges == {} ⇒ ✅ AUCUN COMPTEUR DE REJET N'A MONTE`, presente
#    comme « le controle le plus discriminant d'AC8 ». Or ce verdict est
#    SATISFAIT PAR L'ETAT MORT : une carte qui n'a RIEN RECU rend exactement
#    zero rejet. Les gardes existantes (`returncode`, `timeout`, duree murale,
#    `vue is None`, peremption) prouvent que l'AGENT A VECU, ⛔ pas que la CARTE
#    A ACCEPTE. Et AC7 le dit lui-meme : « n trames emises ne prouve que n
#    ecritures, pas n acceptations. »
# 🎯 Le firmware publie le chiffre qui tranche UNE LIGNE AU-DESSUS de celle qui
#    etait lue (`dn_console.c:2860`) :
#      trames     : %u valides · %u doublons · %u pertes seq · %u resynchros...
_LIGNE_TRAMES = re.compile(
    r"^trames\s*:\s*(\d+)\s+valides\s*\u00b7\s*(\d+)\s+doublons\s*\u00b7\s*"
    r"(\d+)\s+pertes seq\s*\u00b7\s*(\d+)\s+resynchros", re.M)
_TRAMES = ("valides", "doublons", "pertes seq", "resynchros")


def _extraire_trames(txt):
    """Rend les quatre compteurs de RECEPTION. ⛔ LEVE si la ligne manque —
    ⛔ REFUS DE RENDRE DES ZEROS : c'est exactement le zero qu'on cherche a
    distinguer d'une carte muette."""
    m = _LIGNE_TRAMES.search(txt)
    if not m:
        raise RuntimeError(
            "ligne `trames :` introuvable dans la sortie de `pc`. \u26d4 SANS ELLE, "
            "« aucun rejet » ne prouve RIEN : une carte qui n'a rien recu rend "
            "zero rejet elle aussi.")
    return dict(zip(_TRAMES, (int(g) for g in m.groups())))
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
    fin = time.monotonic() + timeout
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
        avant_tr = _extraire_trames(avant_txt)
        print("[regime] compteurs de rejet AVANT : %s" % avant)
        print("[regime] compteurs de RECEPTION AVANT : %s" % avant_tr)
    finally:
        ser.close()
    time.sleep(0.4)                        # laisser Windows relacher le port

    print("[regime] agent : %d s sur %s ..." % (a.duree, a.port))
    t0 = time.monotonic()
    try:
        pr = subprocess.run([a.python, AGENT, "--serie", a.port,
                             "--duree", str(a.duree)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=a.duree + 60)
    except subprocess.TimeoutExpired:
        print("\n\u2716\ufe0f  L'AGENT N'A PAS RENDU LA MAIN (%d s + 60 s de marge)."
              % a.duree)
        print("   \u26d4 NE PAS CONCLURE SUR AC8 : le tir n'a pas eu lieu.")
        return 1
    mur = time.monotonic() - t0

    # 🔴 DEFAUT TROUVE EN REVUE (code review dn4-8, 2026-08-21) — ET C'EST LA
    #    FAMILLE « subprocess rend 0 sans rien avoir fait », que ce depot a deja
    #    payee. `pr.returncode` n'etait JAMAIS lu et `mur` etait jete (`_ = mur`).
    #    Un agent qui meurt en 0,3 s — COM3 tenu par un autre processus, psutil
    #    manquant sur le Python de la tour, traceback non rattrape — laissait
    #    `avant` et `apres` IDENTIQUES, donc `bouges == {}`, donc l'outil imprimait
    #    « ✅ AUCUN COMPTEUR DE REJET N'A MONTE ... le controle le plus discriminant
    #    d'AC8 » et sortait 0. ⛔ SUR UN TIR OU AUCUN OCTET N'A CIRCULE.
    # ⚠️ La garde de completude ne pouvait pas rattraper ca : le firmware imprime
    #    les CINQ metriques inconditionnellement, meme sans avoir rien recu.
    if pr.returncode != 0:
        print("\n\u2716\ufe0f  L'AGENT S'EST TERMINE EN ECHEC (code %d)." % pr.returncode)
        sys.stdout.write(pr.stderr.decode("utf-8", "replace"))
        print("   \u26d4 NE PAS CONCLURE SUR AC8 : des compteurs qui ne bougent pas "
              "apres un tir MORT ne prouvent rien.")
        return 1
    # 🎯 LA DUREE MURALE EST UN INSTRUMENT, ⛔ PAS UNE LIGNE DE JOURNAL. Un agent
    #    qui rend la main bien avant sa duree demandee n'a pas emis ce qu'on croit.
    print("[regime] l'agent a vecu %.1f s (demande : %d s)" % (mur, a.duree))
    if mur < a.duree * 0.5:
        print("\n\u2716\ufe0f  L'AGENT A VECU %.1f s POUR %d s DEMANDEES." % (mur, a.duree))
        sys.stdout.write(pr.stderr.decode("utf-8", "replace"))
        print("   \u26d4 NE PAS CONCLURE SUR AC8 : le tir est trop court pour porter "
              "un verdict sur les compteurs de rejet.")
        return 1

    # \U0001f534 LA COURSE CONTRE LA PEREMPTION COMMENCE ICI. 3 s, pas plus.
    t_reouv = time.monotonic()
    ser = ouvrir(a.port)
    tirs = 0
    # ⚠️ `vue` n'etait affectee QU'A L'INTERIEUR de la boucle, elle-meme dans le
    #    `try` : si le `cmd(ser, "")` de reveil levait, le `finally` fermait le
    #    port et `_extraire(vue)` partait en `NameError` — un plantage opaque a la
    #    place d'un echec diagnosticable. (revue dn4-8, 2026-08-21)
    vue = None
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
    delai = time.monotonic() - t_reouv
    if vue is None:
        print("\n\u2716\ufe0f  AUCUNE CAPTURE N'A ETE OBTENUE apres l'arret de l'agent.")
        print("   \u26d4 NE PAS CONCLURE SUR AC8 : il n'y a rien a comparer.")
        return 1
    # 🔴 2e REVUE (2026-08-24) : `_extraire` etait appele AVANT le controle de
    #    completude, et `main()` n'a pas de `try`. Une `vue` amputee de la ligne
    #    `rejets :` — ou entierement vide, cas que CE FICHIER documente comme
    #    MESURE (« deux captures de `dn_console.py` revenues ENTIEREMENT VIDES »)
    #    — produisait un TRACEBACK NU a la place du message « c'est la CAPTURE
    #    qui a perdu des lignes. Refaire le tir. » qui existe cinq lignes plus bas.
    #    ⛔ Meme classe que le `NameError` que le correctif `vue = None` venait de
    #    fermer : « un plantage opaque a la place d'un echec diagnosticable ».
    try:
        apres = _extraire(vue)
        apres_tr = _extraire_trames(vue)
    except RuntimeError as exc:
        print("\n\u2716\ufe0f  CAPTURE INEXPLOITABLE : %s" % exc)
        print("   \u26d4 NE PAS CONCLURE SUR AC8. \u21d2 c'est la CAPTURE qui a perdu "
              "des lignes. Refaire le tir.")
        return 1

    print("\n" + "-" * 88)
    print("BILAN DE L'AGENT (stderr) :")
    print("-" * 88)
    sys.stdout.write(pr.stderr.decode("utf-8", "replace"))

    print("\n" + "-" * 88)
    print("`pc` RELU %.2f s apres l'arret de l'agent (peremption = 3,00 s) — "
          "%s" % (delai, "FRAIS" if delai < 3.0 else
                  "\u26d4 PERIME : ce releve ne vaut RIEN, refaire"))
    print("-" * 88)
    # 🔴 CE VERDICT EST MAINTENANT GATANT (revue dn4-8, 2026-08-21). Il etait
    #    IMPRIME puis IGNORE : `delai` ne resservait plus, et un run qui annoncait
    #    lui-meme « ce releve ne vaut RIEN » sortait quand meme 0, avec la
    #    conclusion ✅ d'AC8 quelques lignes plus bas. ⛔ Un instrument qui declare
    #    sa propre mesure nulle et conclut quand meme est pire que pas d'instrument.
    perime = delai >= 3.0
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
    if perime:
        print("\u2716\ufe0f  RELEVE PERIME (%.2f s > 3,00 s) : les valeurs lues ont expire, "
              "`pc` montre « -- » pour une raison qui N'EST PAS le sujet." % delai)
        print("   \u26d4 LES COMPTEURS SONT PEUT-ETRE JUSTES, MAIS CE TIR NE LES PROUVE "
              "PAS. Refaire.")
        return 1
    # 🔴 2e REVUE (2026-08-24) — LA GARDE QUI MANQUAIT. « Zero rejet » est
    #    satisfait A L'IDENTIQUE par une carte qui n'a RIEN RECU. Avant de
    #    publier le verdict d'AC8, on exige donc que la carte ait ACCEPTE des
    #    trames pendant le tir. ⛔ C'est ce qui separe « la carte a tout accepte »
    #    de « la carte etait muette ».
    d_tr = {k: apres_tr[k] - avant_tr[k] for k in _TRAMES}
    print("\ncompteurs de RECEPTION (delta) : %s" % d_tr)
    if d_tr["valides"] <= 0:
        print("\n\u2716\ufe0f  LA CARTE N'A ACCEPTE AUCUNE TRAME PENDANT LE TIR "
              "(delta `valides` = %d)." % d_tr["valides"])
        print("   \u26d4 « aucun rejet » NE PROUVE RIEN ICI : une carte muette rend "
              "zero rejet elle aussi.")
        print("   \u26a0\ufe0f  AC7 le dit : « n trames emises ne prouve que n ECRITURES, "
              "\u26d4 pas n ACCEPTATIONS ». Refaire le tir.")
        return 1
    print("\n\u2705 AUCUN COMPTEUR DE REJET N'A MONTE (les six a zero de delta), ET "
          "LA CARTE A ACCEPTE %d TRAME(S)." % d_tr["valides"])
    print("   \U0001f3af C'est le controle le plus discriminant d'AC8 : une absence de")
    print("   donnee se dit par un CHAMP VIDE, \u26d4 jamais par un rejet.")
    print("   \u26d4 Et il n'est plus satisfiable par l'etat MORT : sans trame "
          "acceptee, ce tir ECHOUE au lieu de conclure.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

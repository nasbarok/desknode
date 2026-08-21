#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""campagne_bruit_dn48.py — chaque cas de bruit sur SON compteur, diff avant/apres.

🔴 CE QU'IL VERIFIE, ET C'EST PLUS DUR QUE « le compteur attendu a monte » :
   pour chaque trame injectee, le compteur ATTENDU monte de 1 **ET TOUS LES
   AUTRES RESTENT A ZERO**. Un cas qui incremente deux compteurs, ou le mauvais,
   est un ECHEC — meme si « le bon » a monte.
⚠️ Motif : « tronquee » et « trop longue » sont des diagnostics CONTRAIRES, et le
   depot a deja eu les deux dans le MEME seau. Un compteur qui compte autre chose
   que ce que son nom dit est la classe de defaut que ce depot traque.

🔴 ET SON PARSEUR SE PROUVE SUR UNE LIGNE FABRIQUEE AVANT D'ETRE CRU. Gratter
   au `grep` une console redigee pour un humain FABRIQUE des nombres plausibles :
   un motif qui ne matche plus rend « 0 » au lieu de lever, et tous les deltas
   deviennent nuls — la campagne conclurait « aucun compteur n'a bouge » sur une
   carte qui repond parfaitement. ⇒ auto-test EN TETE, ⛔ pas en option.

Usage :  python3 tools/campagne_bruit_dn48.py
Sortie : 0 si les N cas tombent chacun dans SON compteur, 1 sinon.
"""
import os
import re
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "tools"))
import dn_console  # noqa: E402

COMPTEURS = ("tronquee", "trop longue", "checksum", "version", "format", "bornes")
_LIGNE_REJ = re.compile(
    r"^rejets\s*:\s*tronquee\s+(\d+)\s*\u00b7\s*trop longue\s+(\d+)\s*\u00b7\s*"
    r"checksum\s+(\d+)\s*\u00b7\s*version\s+(\d+)\s*\u00b7\s*format\s+(\d+)\s*"
    r"\u00b7\s*bornes\s+(\d+)\s*$", re.M)


def ck(corps):
    x = 0
    for o in corps.encode("ascii"):
        x ^= o
    return "%02X" % x


def trame(ver, seq, t, met, vals, ck_faux=False, sans_ck=False):
    """⚠️ `vals` peut contenir `None` (champ VIDE) — c'est le point de plusieurs cas."""
    corps = "DN,%d,%d,%d,%s," % (ver, seq, t, met) + ",".join(
        "" if v is None else str(v) for v in vals)
    if sans_ck:
        return "$" + corps
    return "$" + corps + "*" + ("00" if ck_faux else ck(corps))


def _extraire(txt):
    """Rend le dict des six compteurs. \u26d4 LEVE si le motif ne matche pas."""
    m = _LIGNE_REJ.search(txt)
    if not m:
        raise RuntimeError(
            "la ligne `rejets :` n'a pas ete trouvee dans la sortie de `pc`. "
            "\u26d4 REFUS DE RENDRE DES ZEROS : un parseur permissif ferait "
            "conclure « aucun compteur n'a bouge » sur une carte qui repond.")
    return dict(zip(COMPTEURS, (int(g) for g in m.groups())))


def autotest():
    """\U0001f534 LE PARSEUR SE PROUVE SUR UNE LIGNE FABRIQUEE, ⛔ pas sur la carte."""
    faux = ("liaison PC : VIVANTE\n"
            "rejets     : tronquee 3 \u00b7 trop longue 1 \u00b7 checksum 4 \u00b7 "
            "version 1 \u00b7 format 5 \u00b7 bornes 9\n"
            "latence ...\n")
    got = _extraire(faux)
    att = {"tronquee": 3, "trop longue": 1, "checksum": 4, "version": 1,
           "format": 5, "bornes": 9}
    if got != att:
        sys.exit("\u26d4 AUTO-TEST DU PARSEUR ECHOUE : %s != %s" % (got, att))
    # Et il doit LEVER sur une ligne qui ne contient pas ce qu'il cherche.
    try:
        _extraire("liaison PC : VIVANTE\nrien ici\n")
    except RuntimeError:
        pass
    else:
        sys.exit("\u26d4 AUTO-TEST : le parseur a rendu quelque chose sur une "
                 "sortie SANS ligne `rejets` — il ne peut pas voir le defaut "
                 "qu'il pretend exclure.")
    print("  [OK ] auto-test du parseur : il lit une ligne FABRIQUEE, et il LEVE "
          "quand la ligne manque")


def _cmd(ser, c):
    """⚠️ `envoyer()` rend un DICT, ⛔ pas une chaine — et son timeout est
       EXPLICITE. Un wrapper local plutot que dix appels a trois arguments."""
    return dn_console.envoyer(ser, c, 5.0)["sortie"]


def lire_compteurs(ser):
    return _extraire(_cmd(ser, "pc"))


def main():
    for f in (sys.stdout, sys.stderr):
        try:
            f.reconfigure(encoding="utf-8")
        except Exception:
            pass
    print("=" * 92)
    print("dn4-8 / AC7 — CAMPAGNE DE BRUIT : chaque cas sur SON compteur, diff avant/apres")
    print("=" * 92)
    autotest()

    # \u26a0\ufe0f Les trames sont construites ICI, et leur LONGUEUR est verifiee avant
    #    le tir pour le cas « trop longue » : un cas qui ne tomberait pas dans la
    #    bande 72..124 mesurerait autre chose que son nom.
    CAS = [
        ("version hors [1..3]",
         lambda s, t: trame(9, s, t, "cpu", [520]), "version"),
        ("ver=1 a 7 champs (v1 n'en connait que 6)",
         lambda s, t: trame(1, s, t, "cpu", [520, 320]), "format"),
        ("ver=2 a 9 champs (champ EN TROP)",
         lambda s, t: trame(2, s, t, "cpu", [520, 320, 880, 410]), "format"),
        ("plus de valeurs que la metrique n'en publie (ram=2)",
         lambda s, t: trame(3, s, t, "ram", [660, 340, 100, 200]), "format"),
        ("NOUVELLE grandeur hors plafond : cpu degC 1600 > 1500",
         lambda s, t: trame(3, s, t, "cpu", [520, 320, 880, 1600]), "bornes"),
        ("NOUVELLE grandeur hors plafond : disk tr/min 999999 > 100000",
         lambda s, t: trame(3, s, t, "disk", [4800, 999999, 8000, 14000]), "bornes"),
        ("ligne COMPLETE dans la bande 72..124",
         lambda s, t: trame(3, 4294967295, 4294967295, "disk",
                            [1000000, 100000, 100000, 100000, 100000, 100000]),
         "trop longue"),
        ("ligne SANS *CK",
         lambda s, t: trame(3, s, t, "cpu", [520], sans_ck=True), "tronquee"),
        ("checksum FAUX",
         lambda s, t: trame(3, s, t, "cpu", [520], ck_faux=True), "checksum"),
        ("champ VIDE en position 0",
         lambda s, t: trame(3, s, t, "cpu", [None, 320, 880, 410]), "format"),
    ]

    ser = dn_console.ouvrir(dn_console.DEFAULT_PORT, dn_console.DEFAULT_BAUD)
    echecs = []
    try:
        dn_console.reveiller(ser)
        _cmd(ser, "pc reset")
        seq = 1000
        for nom, fab, attendu in CAS:
            seq += 1
            ligne = fab(seq, seq * 10)
            avant = lire_compteurs(ser)
            _cmd(ser, "pc " + ligne)
            time.sleep(0.15)
            apres = lire_compteurs(ser)
            delta = {k: apres[k] - avant[k] for k in COMPTEURS}
            bouges = {k: v for k, v in delta.items() if v}
            ok = bouges == {attendu: 1}
            n = len(ligne)
            info = "%3d o" % n
            if attendu == "trop longue":
                info += "  (bande 72..124 : %s)" % ("oui" if 72 <= n <= 124 else "NON")
            print("  [%s] %-52s -> %-11s %s %s"
                  % ("OK " if ok else "\u2716\ufe0f ", nom, attendu, info,
                     "" if ok else "  \u26d4 OBSERVE : %s" % (bouges or "AUCUN")))
            if not ok:
                echecs.append(nom)

        # \U0001f3af LE TEMOIN v1 : l'agent de dn2-2, NON MODIFIE, doit rester VALIDE.
        print()
        avant = lire_compteurs(ser)
        _cmd(ser, "pc $DN,1,42,123456,cpu,153*47")
        time.sleep(0.15)
        apres = lire_compteurs(ser)
        delta = {k: apres[k] - avant[k] for k in COMPTEURS}
        vue = _cmd(ser, "pc")
        vivante = "cpu   -> case 0 CPU       VIVANTE" in vue
        ok = not any(delta.values()) and vivante
        print("  [%s] TEMOIN v1 (agent dn2-2 NON MODIFIE) : 6 champs, `cpu` seul"
              % ("OK " if ok else "\u2716\ufe0f "))
        print("        rejets_version = 0 et la case CPU est VIVANTE  ->  %s"
              % ("oui" if ok else "NON : delta=%s vivante=%s" % (delta, vivante)))
        if not ok:
            echecs.append("temoin v1")
    finally:
        try:
            ser.close()
        except Exception:
            pass

    print("\n" + "=" * 92)
    if echecs:
        print("\u2716\ufe0f  %d CAS EN ECHEC : %s" % (len(echecs), echecs))
        return 1
    print("\u2705 %d cas + le temoin v1 : chacun dans SON compteur, et LUI SEUL."
          % len(CAS))
    return 0


if __name__ == "__main__":
    sys.exit(main())

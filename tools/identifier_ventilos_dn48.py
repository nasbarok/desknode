r"""
=============================================================================
 identifier_ventilos_dn48.py -- AC3 de dn4-8 : QUEL `Fan #n` EST QUEL CANAL ?
=============================================================================

 LE PROBLEME. LHM ne livre que des numeros : `Fan #1`..`Fan #6` sur le
 nct6792d. ⛔ UN NUMERO DE CANAL N'EST PAS UNE IDENTITE. Deduire « le plus lent
 doit etre le 200 mm » serait une SUPPOSITION PLAUSIBLE -- exactement la classe
 d'erreur que ce depot traque.

 LA METHODE : STIMULUS / REPONSE, A UNE SEULE VARIABLE.
 On pousse UN canal a 100 %, on regarde QUELLE lecture saute, on rend la main.
 Deux temoins de natures differentes, et c'est ce qu'AC3 exige :
   · l'agent lit les tachymetres ;
   · 🔴 L'OWNER ENTEND lequel rugit. ⛔ CE TEMOIN-LA N'EST PAS PRODUCTIBLE PAR
     L'AGENT, et c'est lui qui ferme l'identification.

 -----------------------------------------------------------------------------
 ⛔ CE QUE CE SCRIPT NE FAIT JAMAIS
 -----------------------------------------------------------------------------
 · Il ne descend AUCUN ventilateur. UNIQUEMENT vers le haut. Un canal peut
   refroidir le CPU, et on ne le decouvre qu'APRES.
 · Il ne laisse JAMAIS un canal sous controle logiciel : la remise en
   automatique est dans un `finally`, ⛔ PAS apres la boucle. Une interruption
   au clavier laisserait sinon des ventilateurs bloques a 100 %.
   (lecon du depot : un nettoyage ecrit APRES la boucle ne s'execute pas)
 · Il ne conclut pas « ce canal est le 200 mm ». Il publie QUI A BOUGE, et
   l'identite se ferme avec l'oreille de l'owner.

 -----------------------------------------------------------------------------
 EMPLOI
 -----------------------------------------------------------------------------
   powershell.exe -NoProfile -Command "& $env:LOCALAPPDATA\Programs\Python\Python313\python.exe \\wsl.localhost\Ubuntu\home\nasbarok\projects\desknode\tools\identifier_ventilos_dn48.py"
     --monte 8      secondes a 100 % par canal
     --repos 6      secondes de retour au calme entre deux canaux
     --seuil 15     % de hausse au-dela duquel une lecture est dite « a bouge »
     --restaurer    NE FAIT QUE remettre tous les canaux en automatique, et sort

 (!) IL ECRIT SUR LE MATERIEL : LHM prend la main sur la courbe BIOS le temps du
     test. C'est bruyant. Accord owner obtenu le 2026-08-21.
=============================================================================
"""

import argparse
import http.client
import json
import sys
import time
import urllib.parse

HOTE, PORT = "localhost", 8085
PUCE = "/lpc/nct6792d/0"
CANAUX = list(range(6))
_TOUS = list(range(6))


def _post(chemin):
    c = http.client.HTTPConnection(HOTE, PORT, timeout=10.0)
    try:
        c.request("POST", chemin)
        return json.loads(c.getresponse().read().decode("utf-8", "replace"))
    finally:
        c.close()


def _get(chemin):
    c = http.client.HTTPConnection(HOTE, PORT, timeout=15.0)
    try:
        c.request("GET", chemin)
        return c.getresponse().read().decode("utf-8", "replace")
    finally:
        c.close()


def lire_tout():
    """Rend {fan: {id: rpm}, ctl: {id: pct}} depuis /data.json."""
    doc = json.loads(_get("/data.json"))
    fan, ctl = {}, {}
    pile = [doc]
    while pile:
        n = pile.pop()
        sid = n.get("SensorId") or ""
        if sid.startswith(PUCE):
            v = n.get("Value") or ""
            num = "".join(ch for ch in v if ch.isdigit() or ch in ",.-").replace(",", ".")
            try:
                x = float(num)
            except ValueError:
                x = None
            if n.get("Type") == "Fan":
                fan[sid] = x
            elif n.get("Type") == "Control":
                ctl[sid] = x
        pile.extend(n.get("Children") or ())
    return fan, ctl


def poser(canal, valeur):
    """valeur = '100' ou 'null' (null => Control.SetDefault(), retour BIOS)."""
    ident = "%s/control/%d" % (PUCE, canal)
    r = _post("/Sensor?action=Set&id=%s&value=%s"
              % (urllib.parse.quote(ident, safe="/"), valeur))
    if r.get("result") != "ok":
        print("  /!\\ Set %s = %s a ECHOUE : %s" % (ident, valeur, r.get("message", r)))
        return False
    return True


def tout_rendre():
    """⛔ APPELE DANS UN `finally`. Rend la main au BIOS sur TOUS les canaux."""
    print("  -- retour en automatique sur les %d canaux --" % len(CANAUX))
    for k in _TOUS:
        poser(k, "null")
    time.sleep(2)
    _, ctl = lire_tout()
    bloques = [i for i, v in sorted(ctl.items()) if v is not None and v >= 99.0]
    if bloques:
        print("  /!\\ CANAUX ENCORE A 100 %% : %s" % ", ".join(bloques))
        print("      ⛔ NE PAS LAISSER LA MACHINE AINSI. Relancer avec --restaurer,")
        print("         ou ouvrir LHM et remettre les controles en 'Default'.")
    else:
        print("  OK : aucun canal bloque a 100 %.")


def main():
    for f in (sys.stdout, sys.stderr):
        try:
            f.reconfigure(encoding="utf-8")
        except Exception:
            pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--monte", type=float, default=8.0)
    ap.add_argument("--repos", type=float, default=6.0)
    ap.add_argument("--seuil", type=float, default=15.0)
    ap.add_argument("--restaurer", action="store_true")
    ap.add_argument("--canal", type=int, default=None,
                    help="ne tester QU'UN canal (le retour auto reste dans le finally)")
    a = ap.parse_args()

    if a.restaurer:
        tout_rendre()
        return 0

    print("=== AC3 -- IDENTIFICATION DES CANAUX PAR STIMULUS / REPONSE ===")
    print("  ⛔ uniquement VERS LE HAUT · retour automatique dans un `finally`")
    print("  %.0f s a 100 %% par canal, %.0f s de repos, seuil de hausse %.0f %%\n"
          % (a.monte, a.repos, a.seuil))

    global CANAUX
    if a.canal is not None:
        CANAUX = [a.canal]
        print("  ⚠️ UN SEUL canal teste : control/%d. Le retour automatique porte" % a.canal)
        print("     quand meme sur les 6, ⛔ au cas ou un passage precedent aurait laisse.\n")

    resultats = []
    try:
        # ⛔ D'ABORD rendre la main : une execution precedente interrompue
        #    aurait pu laisser un canal sous controle logiciel.
        tout_rendre()
        time.sleep(a.repos)

        base_fan, base_ctl = lire_tout()
        print("\n  REPOS (automatique) :")
        for i in sorted(base_fan):
            print("    %-32s %7.0f tr/min   (PWM %.1f %%)"
                  % (i, base_fan[i] or 0, base_ctl.get(i.replace("/fan/", "/control/"), 0) or 0))

        for k in CANAUX:
            print("\n  >>> canal control/%d a 100 %% pendant %.0f s ..." % (k, a.monte))
            if not poser(k, "100"):
                resultats.append((k, None, "Set refuse"))
                continue
            time.sleep(a.monte)
            haut_fan, _ = lire_tout()
            poser(k, "null")

            bouges = []
            for i in sorted(haut_fan):
                av, ap_ = base_fan.get(i) or 0.0, haut_fan.get(i) or 0.0
                if av > 0 and ap_ >= av * (1.0 + a.seuil / 100.0):
                    bouges.append((i, av, ap_, (ap_ / av - 1.0) * 100.0))
                elif av == 0 and ap_ > 0:
                    bouges.append((i, av, ap_, float("inf")))
            for i, av, ap_, pc in bouges:
                print("      A BOUGE : %-32s %5.0f -> %5.0f tr/min  (%+.0f %%)"
                      % (i, av, ap_, pc))
            if not bouges:
                print("      ⛔ AUCUNE lecture n'a bouge.")
            resultats.append((k, bouges, None))
            time.sleep(a.repos)

    finally:
        print()
        tout_rendre()

    print("\n=== SYNTHESE -- ⛔ ce que la MESURE dit, pas une identite ===")
    print("  %-12s %s" % ("canal", "lecture(s) qui ont bouge"))
    print("  " + "-" * 74)
    for k, bouges, err in resultats:
        if err:
            print("  control/%-4d ERREUR : %s" % (k, err))
        elif not bouges:
            print("  control/%-4d ⛔ aucune -- en-tete non peuple, ventilateur sans tachy,"
                  " ou canal non lu" % k)
        else:
            print("  control/%-4d %s" % (k, ", ".join(
                "%s (%+.0f %%)" % (i.rsplit("/", 2)[-2] + "/" + i.rsplit("/", 1)[-1], pc)
                for i, _, _, pc in bouges)))
    print()
    print("  🔴 L'IDENTITE NE SE FERME PAS ICI : il faut le CONSTAT OWNER (quel")
    print("     ventilateur a rugi, et dans quel ordre). ⛔ Un agent ne l'entend pas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stub_lhm_dn48.py — un FAUX LibreHardwareMonitor, pour eprouver l'agent.

🔴 POURQUOI IL EXISTE. AC6 exige un timeout « pose, ecrit **ET MESURE** », et
   AC8 exige que « LHM absent » soit **EPROUVE, ⛔ pas suppose** — dont l'arret
   **en cours de route**, le scenario le plus dur. Aucun des deux ne se joue
   contre le vrai LHM sans le couper, donc sans un geste owner sur la tour.
⇒ Ce serveur rejoue la FORME exacte de `/metrics` depuis une capture REELLE
  (`tools/fixtures/lhm_metrics_2026-08-21.txt`, provenance ecrite a cote), et
  permet de fabriquer les pannes **a une variable a la fois**.

⛔ CE QU'IL N'EST PAS : une source de mesure. Aucun nombre servi ici n'est une
   mesure de la tour -- ils viennent d'un instantane n = 1. Il eprouve des
   CHEMINS DE CODE, ⛔ pas des grandeurs.
⚠️ ET IL NE TOURNE PAS SUR LE PORT DE LHM par defaut (8086, ⛔ pas 8085) : un
   stub qui ecoute a la place du vrai service ferait mesurer le stub en croyant
   mesurer la tour. Le port se passe explicitement.

Usage :
    python3 tools/stub_lhm_dn48.py --port 8086 --mode normal
    python3 tools/stub_lhm_dn48.py --port 8086 --mode lent --retard 2.0
    python3 tools/stub_lhm_dn48.py --port 8086 --mode muette --sonde /lpc/nct6792d/0/fan/2
    python3 tools/stub_lhm_dn48.py --port 8086 --mode negatif --sonde /lpc/nct6792d/0/fan/0
    python3 tools/stub_lhm_dn48.py --port 8086 --mode meurt --apres 3
"""
import argparse
import io
import os
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(RACINE, "tools", "fixtures", "lhm_metrics_2026-08-21.txt")

ETAT = {"mode": "normal", "retard": 0.0, "sonde": None, "apres": 0, "servies": 0}


def _corps():
    """Le corps servi, DERIVE de la capture reelle selon le mode.

    ⚠️ La derivation est faite LIGNE A LIGNE sur la vraie capture, ⛔ pas
       re-synthetisee : une forme re-ecrite a la main ne prouverait rien du
       parseur, elle prouverait qu'il lit ce qu'on lui a ecrit pour lui.
    """
    txt = io.open(FIXTURE, encoding="utf-8", errors="replace").read()
    if ETAT["mode"] == "muette" and ETAT["sonde"]:
        # `/metrics` OMET la ligne d'un capteur sans valeur -- c'est MESURE
        # (AC2) : « la ligne du capteur est OMISE ». On reproduit ca, ⛔ pas un
        # « 0 » ni un jeton invente.
        sid, hid = _decouper(ETAT["sonde"])
        garde = []
        for l in txt.splitlines():
            if ('"sensorId"="%s"' % sid) in l and ('"hardwareId"="%s"' % hid) in l:
                continue
            garde.append(l)
        return "\n".join(garde) + "\n"
    if ETAT["mode"] == "negatif" and ETAT["sonde"]:
        sid, hid = _decouper(ETAT["sonde"])
        garde = []
        for l in txt.splitlines():
            if ('"sensorId"="%s"' % sid) in l and ('"hardwareId"="%s"' % hid) in l:
                l = re.sub(r"(\}\s+)(\S+)\s*$", r"\g<1>-1", l)
            garde.append(l)
        return "\n".join(garde) + "\n"
    return txt


def _decouper(ident):
    """`/lpc/nct6792d/0/fan/2` -> (`/fan/2`, `/lpc/nct6792d/0`).

    ⚠️ La coupure se fait sur les DEUX derniers segments, parce que c'est la
       forme que LHM produit (`sensorId` = `/<type>/<n>`).
    """
    bouts = ident.rstrip("/").split("/")
    return "/" + "/".join(bouts[-2:]), "/".join(bouts[:-2])


class Poignee(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"   # keep-alive, comme LHM

    def log_message(self, *a):
        pass

    def do_GET(self):
        ETAT["servies"] += 1
        if ETAT["mode"] == "meurt" and ETAT["servies"] > ETAT["apres"]:
            print("[stub-lhm] MODE MEURT : %d reponses servies, le serveur "
                  "s'arrete MAINTENANT (AC8 scenario 2)." % (ETAT["servies"] - 1),
                  file=sys.stderr)
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            try:
                self.connection.close()
            except Exception:
                pass
            return
        if ETAT["mode"] == "lent":
            time.sleep(ETAT["retard"])
        if not self.path.startswith("/metrics"):
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        b = _corps().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        # 🔴 MODE `goutte` — AJOUTE EN REVUE (code review dn4-8, 2026-08-21).
        #    Le mode `lent` dort AVANT de composer et envoie le corps EN UN SEUL
        #    `wfile.write` : il n'exerce donc que « retard puis reponse d'un coup »,
        #    que le timeout du socket attrape sans peine. ⛔ AUCUN mode ne pouvait
        #    produire la panne que le timeout RATAIT vraiment — un corps servi par
        #    petits morceaux, chacun arrivant JUSTE avant l'echeance, qui remet le
        #    chrono a zero a chaque paquet et fait courir la lecture sans borne.
        # ⚠️ Un harnais qui ne sait pas produire le defaut ne peut pas prouver
        #    qu'il est corrige : ce mode existe pour EPROUVER `_lire_corps()`.
        if ETAT["mode"] == "goutte":
            pas = max(1, len(b) // 40)
            for i in range(0, len(b), pas):
                self.wfile.write(b[i:i + pas])
                self.wfile.flush()
                time.sleep(ETAT["retard"])
            return
        self.wfile.write(b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8086,
                    help="⛔ PAS 8085 par defaut : ne jamais se substituer au vrai LHM")
    ap.add_argument("--mode", default="normal",
                    choices=["normal", "lent", "muette", "negatif", "meurt",
                             "goutte"])
    ap.add_argument("--retard", type=float, default=2.0)
    ap.add_argument("--sonde", default=None)
    ap.add_argument("--apres", type=int, default=3)
    a = ap.parse_args()
    if a.port == 8085:
        sys.exit("\u26d4 REFUS : 8085 est le port du VRAI LHM. Un stub qui ecoute "
                 "a sa place ferait mesurer le stub en croyant mesurer la tour.")
    if not os.path.exists(FIXTURE):
        sys.exit("fixture absente : %s" % FIXTURE)
    ETAT.update(mode=a.mode, retard=a.retard, sonde=a.sonde, apres=a.apres)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Poignee)
    print("[stub-lhm] \u26a0\ufe0f  FAUX LHM sur 127.0.0.1:%d mode=%s "
          "(fixture n=1, \u26d4 aucune mesure)" % (a.port, a.mode), file=sys.stderr)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
        print("[stub-lhm] arrete apres %d reponse(s)" % ETAT["servies"],
              file=sys.stderr)


if __name__ == "__main__":
    main()

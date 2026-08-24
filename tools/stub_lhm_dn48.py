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
    if ETAT["mode"] == "famille":
        # 🔴 2e REVUE (2026-08-24) — LHM RENOMME L'UNITE. La verification de
        #    famille de `dn_agent._lire()` est presentee comme « LA VERIFICATION
        #    QUI FAIT TENIR LE CHOIX DE /metrics », et AUCUN mode ne pouvait la
        #    declencher : elle a ete eprouvee par une mutation NON COMMITTEE, donc
        #    non rejouable. Ici les lignes se parsent PARFAITEMENT — seule la
        #    famille change — donc `lignes_illisibles` reste a 0 : c'est bien le
        #    QUATRIEME etat, ⛔ pas un desaccord de format.
        return txt.replace("lhm_cpu_temperature_celsius",
                           "lhm_cpu_temperature_fahrenheit").replace(
                           "lhm_motherboard_fan_rpm", "lhm_motherboard_fan_percent")
    if ETAT["mode"] == "doublon":
        # 🔴 2e REVUE — DEUX FAMILLES POUR LA MEME SONDE. Forme exacte d'un
        #    renommage d'unite EN COURS DE DEPLOIEMENT. Avant correctif, le
        #    DERNIER ARRIVE gagnait, sans compteur : le verdict dependait de
        #    l'ORDRE des lignes, que Prometheus ne contractualise PAS.
        sup = [l.replace("lhm_cpu_temperature_celsius",
                         "lhm_cpu_temperature_fahrenheit")
               for l in txt.splitlines()
               if l.startswith("lhm_cpu_temperature_celsius")]
        return txt + "\n".join(sup) + "\n"
    if ETAT["mode"] == "vide":
        # 🔴 2e REVUE — 200 AVEC UN CORPS SANS UNE SEULE LIGNE `lhm_`. Mauvais
        #    endpoint, page d'erreur, ou prefixe de famille renomme. Avant
        #    correctif : `lues = 0`, `illisibles = 0`, cinq « ABSENCES LHM » —
        #    le diagnostic CONTRAIRE de celui que le patch existe pour supprimer.
        return "# HELP rien\n# TYPE rien gauge\nrien 0\n"
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

    # 🔴 MODE `willclose` — 2e REVUE (2026-08-24), ET IL A TROUVE UN VRAI DEFAUT.
    #    TOUS les modes posaient `HTTP/1.1` + `Content-Length`, donc AUCUN ne
    #    produisait une reponse `will_close`. Or CPython fait
    #    `if response.will_close: self.close()` dans `getresponse()`, ce qui met
    #    `HTTPConnection.sock` a None — et le bornage par morceau de `_lire_corps`
    #    devenait un NO-OP SILENCIEUX. MESURE sur arbre mute : **0,902 s pour
    #    0,600 s de budget (150 %)**, contre 0,601 s apres correctif.
    #    ⚠️ 0,902 s > `PERIODE_S` = 1,0 s au pire cas reel : recalage de cadence,
    #       echantillon jete — « le mecanisme le plus dangereux de cette story ».


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
        if ETAT["mode"] == "willclose":
            # ⚠️ PAR REQUETE : `send_response()` ecrit `self.protocol_version`.
            #    HTTP/1.0 sans `keep-alive` ⇒ `HTTPResponse._check_close()` rend
            #    True ⇒ `getresponse()` appelle `HTTPConnection.close()`.
            self.protocol_version = "HTTP/1.0"
            self.close_connection = True
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        # 🔴 `willclose` N'ENVOIE **PAS** `Content-Length`, ET C'EST LOAD-BEARING.
        #    Avec la longueur, `HTTPResponse` sait quand s'arreter : la lecture se
        #    termine sur le 2e `recv` et il n'y a JAMAIS de 3e appel bloquant —
        #    donc l'assertion de temps passait VERTE SUR L'ARBRE MUTE (0,306 s,
        #    51 % du budget, mesure le 2026-08-24). Elle n'atteignait pas la garde
        #    qu'elle pretend couvrir. Sans `Content-Length`, le client lit
        #    JUSQU'A EOF — c'est d'ailleurs la vraie forme d'un serveur HTTP/1.0 —
        #    et le 3e `recv` expose le bornage : 0,902 s (150 %) sur l'arbre mute
        #    contre 0,601 s (100 %) apres correctif.
        if ETAT["mode"] != "willclose":
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
        if ETAT["mode"] == "willclose":
            # 🔴 DEUX `recv` BLOQUANTS SONT NECESSAIRES POUR EXPOSER LE DEFAUT :
            #    le 1er consomme l'essentiel du budget, le 2nd doit alors trouver
            #    un plafond REDUIT. Si le bornage est un no-op, il retrouve le
            #    plafond ENTIER — d'ou le ~2x. Envoyer le corps d'un coup ne
            #    prouverait RIEN (mesure du 2026-08-24 : les deux arbres rendaient
            #    0,602 s, defaut invisible).
            coupe = max(1, len(b) // 2)
            self.wfile.write(b[:coupe])
            self.wfile.flush()
            time.sleep(ETAT["retard"])
            self.wfile.write(b[coupe:])
            self.wfile.flush()
            time.sleep(ETAT["retard"] * 4)
            return
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
                             # 🆕 2e revue (2026-08-24) — quatre etats qu'AUCUN
                             #    mode ne savait produire, donc quatre correctifs
                             #    qui n'etaient eprouves par RIEN de rejouable.
                             "goutte", "willclose", "famille", "doublon", "vide"])
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

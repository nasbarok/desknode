#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn3-3 / AC4.3 — LA CAMPAGNE DES REVEILS AU DOIGT, PILOTEE DEPUIS L'HOTE.

Le geste est a l'owner (toucher la dalle) ; la cadence est a l'agent. Ce script
rebascule en Ambient des qu'un reveil a ete constate, et s'arrete TOUT SEUL au
compte demande.

⛔ IL NE MESURE RIEN LUI-MEME. Les deux latences sont chronometrees DANS le
   firmware, entre le front vu par le `read_cb` et les deux etapes du reveil ;
   ce script ne fait que provoquer les occasions et compter. Un chronometrage
   depuis l'hote ajouterait sa propre latence serie a des valeurs de l'ordre de
   la centaine de microsecondes.

⚠️ IL OUVRE LE PORT UNE SEULE FOIS. Relancer `dn_console.py` a chaque tour
   couterait ~2 s d'ouverture par cycle et rendrait la cadence illisible.
   ⛔ UN SEUL PROCESS A LA FOIS SUR LE PORT : `dn_console.py` pose `TIOCEXCL`,
   et deux lecteurs sur un tty SE VOLENT LES OCTETS.

── CE QU'IL A DEJA PRODUIT (2026-08-25, firmware `dfa8204`, 10 reveils/169 s) ──
   t1  min 86 us · med 107 us · max 178 us     (cible AC4.2 < 50 ms)
   t2  min 25 213 · med 25 454 · max 25 804 us
   D-7 : 12 contacts CONSOMMES, 2 taps de zone, 0 sur MENU.
⚠️ AC4.3 EN DEMANDE 20 : n = 10 est un ECART DECLARE (decision owner). Relancer
   ce script AJOUTE des echantillons — `veille reset` au demarrage les remet a
   zero, donc ⛔ ne pas le rejouer si on veut CUMULER : lire `veille lat` d'abord.

── USAGE ───────────────────────────────────────────────────────────────────────
   python3 tools/campagne_reveils.py [cible=10] [duree_max_s=270]
"""

import re
import sys
import time

import serial

PORT = "/dev/ttyACM0"
CIBLE = int(sys.argv[1]) if len(sys.argv) > 1 else 10
DUREE_MAX = float(sys.argv[2]) if len(sys.argv) > 2 else 270.0


def envoyer(s, cmd, attente=1.2):
    s.reset_input_buffer()
    s.write((cmd + "\r\n").encode("ascii"))
    s.flush()
    t0 = time.time()
    buf = b""
    while time.time() - t0 < attente:
        buf += s.read(4096)
    return buf.decode("utf-8", "replace")


def main():
    s = serial.Serial(PORT, 115200, timeout=0.2)
    t0 = time.time()
    envoyer(s, "veille reset")
    print("compteurs a zero — campagne de %d reveils AU DOIGT" % CIBLE)
    print("touche la dalle des qu'elle s'assombrit.")
    vus = 0
    dernier = -1
    while vus < CIBLE and time.time() - t0 < DUREE_MAX:
        # On rebascule en Ambient : si on y est deja, le firmware repond
        # « rien a faire » et rien ne bouge.
        envoyer(s, "veille now", 0.9)
        time.sleep(1.0)
        sortie = envoyer(s, "veille", 1.4)
        m = re.search(r"reveils\s*:\s*(\d+)", sortie)
        if m:
            vus = int(m.group(1))
            if vus != dernier:
                print("  reveils : %d / %d   (t = %.0f s)"
                      % (vus, CIBLE, time.time() - t0))
                dernier = vus
        time.sleep(2.0)
    print("fin : %d reveil(s) en %.0f s" % (vus, time.time() - t0))
    # Le relevé final, imprimé tel quel — ⛔ pas recalculé ici.
    print(envoyer(s, "veille lat", 2.0))
    s.close()


if __name__ == "__main__":
    main()

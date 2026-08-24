#!/usr/bin/env python3
"""
dn4-4 — LA FENÊTRE D'OBSERVATION, PRÉPARÉE **AVANT** DE DEMANDER LES YEUX.

🔴 POURQUOI CE SCRIPT EXISTE. Deux témoins owner ont déjà été perdus dans ce
   dépôt pour la même raison : *« une vue qui périme en 3 s exige une injection
   CONTINUE pendant l'observation »*. Un `--jeu pire` qui s'arrête, et l'owner
   regarde un écran à `--`.
⚠️ ET `dn_injecteur.py` NE PEUT PAS SERVIR ICI : ses jeux portent des valeurs
   FIXES par métrique. La courbe serait une LIGNE DROITE — c'est-à-dire
   indiscernable d'une courbe qui ne se met pas à jour. L'instrument ne pourrait
   pas montrer ce qu'on demande à l'œil de juger.

⇒ Ce script émet des valeurs qui **VARIENT**, à la cadence de l'historique
  (1 Hz), sur les cinq métriques PC, avec `seq` croissant et checksum
  RECALCULÉ. `AMBIANCE` n'a pas besoin de lui : son BME680 est une source RÉELLE.
"""
import argparse
import math
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import dn_console


def _ck(corps):
    x = 0
    for o in corps.encode("ascii"):
        x ^= o
    return f"{x:02X}"


def trame(seq, t_ms, metrique, valeurs):
    corps = f"DN,3,{seq},{t_ms},{metrique}," + ",".join(str(int(v)) for v in valeurs)
    return f"${corps}*{_ck(corps)}"


def jeu(t):
    """Des formes DIFFÉRENTES par métrique — ⛔ pas la même sinusoïde partout :
    six courbes identiques ne prouveraient pas que chaque page lit SA série."""
    return {
        # cpu : %, GHz, c.max %, °C
        "cpu": (500 + 400 * math.sin(t / 6.0), 30 + 25 * math.sin(t / 9.0),
                600 + 350 * math.sin(t / 5.0), 450 + 200 * math.sin(t / 11.0)),
        # gpu : %, °C, W, tr/min
        "gpu": (400 + 550 * math.sin(t / 8.0 + 1), 600 + 250 * math.sin(t / 13.0),
                1500 + 1200 * math.sin(t / 7.0), 15000 + 8000 * math.sin(t / 10.0)),
        # ram : %, total Go
        "ram": (450 + 400 * math.sin(t / 12.0), 342),
        # net : desc Mb/s, mont Mb/s — une DENT DE SCIE, ⛔ pas une sinusoïde :
        #       c'est la forme la plus lisible pour juger « la courbe bouge ».
        "net": (100 + 9000 * ((t % 20) / 20.0), 5000 - 4500 * ((t % 14) / 14.0)),
        # disk : Mo/s + trois tr/min
        "disk": (2000 + 18000 * abs(math.sin(t / 9.0)),
                 12000 + 8000 * math.sin(t / 6.0),
                 8000 + 4000 * math.sin(t / 8.0),
                 9000 + 5000 * math.sin(t / 10.0)),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", default="/dev/ttyACM0")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--secondes", type=float, default=180)
    p.add_argument("--seq0", type=int, default=10000)
    p.add_argument("--pages", default="",
                   help="indices de page a faire DEFILER, ex. 0,1,2,3,4,5")
    p.add_argument("--par-page", type=float, default=22.0,
                   help="secondes par page (la fenetre d'observation owner)")
    a = p.parse_args()

    ser = dn_console.ouvrir(a.port, a.baud)
    seq = a.seq0
    t0 = time.time()
    n = 0
    try:
        dn_console.reveiller(ser)
        pages = [int(x) for x in a.pages.split(",") if x.strip() != ""]
        if pages:
            # ⚠️ LE MEME PORT SERT A L'INJECTION ET A LA NAVIGATION. Les separer
            #    obligerait a `--force`, dont l'outil dit lui-meme que « les
            #    octets se partagent : mesures tronquees » — une trame `pc`
            #    coupee en deux tomberait en `rejets_tronquee` et creuserait un
            #    trou dans l'historique PENDANT l'observation. ⛔ Un seul
            #    proprietaire du port.
            a.secondes = len(pages) * a.par_page
        page_i = -1
        print(f"injection CONTINUE a 1 Hz pendant {a.secondes:.0f} s "
              f"(⛔ ne pas fermer cette fenetre pendant l'observation)")
        while time.time() - t0 < a.secondes:
            t = time.time() - t0
            if pages:
                k = min(int(t // a.par_page), len(pages) - 1)
                if k != page_i:
                    page_i = k
                    ser.write((f"nav open {pages[k]}\n").encode("ascii"))
                    ser.flush()
                    print(f"  [{t:6.1f} s] page {pages[k]}")
                    time.sleep(0.3)
            for m, vs in jeu(t).items():
                ligne = trame(seq, int(t * 1000), m, vs)
                seq += 1
                # ⛔ On n'attend PAS l'invite : le REPL rend la main, et attendre
                #    ferait deriver la cadence de l'axe des temps.
                ser.write((f"pc {ligne}\n").encode("ascii"))
                ser.flush()
                time.sleep(0.04)  # l'espacement de l'agent reel
                n += 1
            # 🔴 ON DRAINE AU LIEU DE DORMIR : `reset_input_buffer()` jetterait
            #    les logs, et un buffer plein finit par bloquer l'emetteur.
            fin = t0 + t + 1.0
            while time.time() < fin:
                w = ser.in_waiting
                if w:
                    ser.read(w)
                else:
                    time.sleep(0.02)
        print(f"fini — {n} trames emises en {time.time() - t0:.1f} s")
    finally:
        ser.close()


if __name__ == "__main__":
    raise SystemExit(main())

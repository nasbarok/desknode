#!/usr/bin/env python3
"""
dn4-4 / AC2 — LA VUE DÉTAIL PROPAGE, ET C'EST PROUVÉ DANS LES DEUX SENS.

⛔ Ce script ne corrige rien. Il PROUVE quatre propriétés, dont TROIS NÉGATIVES.
   Une propriété prouvée seulement dans le sens positif ne dit pas si la garde
   existe : elle dit seulement que quelque chose bouge.

| Témoin   | Stimulus                                   | Attendu                       |
|----------|--------------------------------------------|-------------------------------|
| POSITIF  | 3 valeurs `net` DIFFÉRENTES, `seq` croissant| les 3 textes, DANS L'ORDRE    |
| PÉREMPTION| injection COUPÉE > 3 s                     | retour à « -- » (AC7 dn2-2)   |
| MOCK     | `widget mock on` sur la case affichée       | ambre 0xffb020 (SIMULÉE)      |
| CROISÉ   | détail sur CPU pendant que `net` bouge      | le détail de CPU NE BOUGE PAS |

🔴 LE TÉMOIN CROISÉ N'EST PAS DÉCORATIF : un correctif qui rafraîchirait le
   détail sur TOUTE mise à jour redessinerait la page 5 fois par seconde pour
   rien — le coût que `dn_ui.c:2779-2783` interdit d'ajouter sur « le chemin le
   plus chaud de la vue détail ».
"""
import argparse
import re
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import dn_console

# 🔴 `nav open <n>` EST 0-BASÉ SUR LES MÉTRIQUES — MESURÉ, ⛔ pas déduit.
#    `nav open 3` -> RÉSEAU · `nav open 4` -> DISQUE · `nav open 5` -> AMBIANCE.
#    Mon premier harnais passait `case + 1` et ouvrait donc DISQUE en croyant
#    ouvrir RÉSEAU : DEUX témoins sont sortis rouges en mesurant la mauvaise
#    page. ⇒ écrit ici pour que le prochain ne le repaie pas.
CASE_NET = 3
CASE_CPU = 0


def _ck(corps):
    x = 0
    for o in corps.encode("ascii"):
        x ^= o
    return f"{x:02X}"


def trame(seq, t_ms, metrique, valeurs):
    corps = f"DN,3,{seq},{t_ms},{metrique}," + ",".join(str(v) for v in valeurs)
    return f"${corps}*{_ck(corps)}"


_TXT = re.compile(r"texte\s*:\s*«\s*(.*?)\s*»", re.S)


def texte(sortie):
    m = _TXT.search(sortie)
    return m.group(1).replace("\n", " | ").strip() if m else "<NON RELU>"


# 🔴 LE RÉGIME SE LIT DANS LA TABLE DE `widget`, ⛔ IL NE SE DÉDUIT PAS DU TEXTE.
#    `widget detail` rend des CARACTÈRES ; la couleur ambre 0xffb020 vit dans
#    `dn_val_regime_couleur()`, et le seul endroit qui la PUBLIE est la colonne
#    `regime` de `widget` (`dn_val_regime_nom(dn_ui_regime(i))`).
_REG = re.compile(r"^\s*(\d)\s+\S+\s+\S+\s+(ABSENTE|RÉELLE|REELLE|SIMULÉE|SIMULEE)\b",
                  re.M)


def regime(sortie, idx):
    for m in _REG.finditer(sortie):
        if int(m.group(1)) == idx:
            return m.group(2)
    return "<NON RELU>"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", default="/dev/ttyACM0")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--seq0", type=int, default=400)
    a = p.parse_args()

    ser = dn_console.ouvrir(a.port, a.baud)
    verdicts = []
    try:
        dn_console.reveiller(ser)

        def cmd(c, timeout=20):
            return dn_console.envoyer(ser, c, timeout)["sortie"]

        seq = a.seq0
        # Le mock ne doit PAS être armé au départ : G3 lui donne la priorité et
        # aucune trame réelle ne passerait. ⛔ Lu, pas supposé.
        cmd("widget mock off")

        # ── TÉMOIN 1 : POSITIF ────────────────────────────────────────────
        print("── TÉMOIN POSITIF — 3 valeurs différentes, `seq` croissant ──────")
        cmd(f"nav open {CASE_NET}")
        vus = []
        for d, u in ((1234, 5678), (4321, 8765), (7777, 1111)):
            cmd(f"pc {trame(seq, 1000, 'net', (d, u))}")
            seq += 1
            time.sleep(0.6)
            t = texte(cmd("widget detail"))
            vus.append(t)
            print(f"   fil « {d/10:.1f} / {u/10:.1f} »".replace(".", ",")
                  + f"  ->  dalle « {t} »")
        ordre_ok = (len(set(vus)) == 3
                    and "123,4" in vus[0] and "432,1" in vus[1]
                    and "777,7" in vus[2])
        verdicts.append(("POSITIF — 3 textes successifs, dans l'ordre", ordre_ok))

        # ── TÉMOIN 2 : NÉGATIF, PÉREMPTION ────────────────────────────────
        print("── TÉMOIN NÉGATIF « PÉREMPTION » — injection coupée > 3 s ───────")
        print("   (on ne touche à RIEN pendant 4,0 s : la péremption est à 3 s)")
        time.sleep(4.0)
        t = texte(cmd("widget detail"))
        print(f"   dalle après 4,0 s de silence : « {t} »")
        verdicts.append(("PÉREMPTION — retour à « -- » (AC7 de dn2-2 ne régresse pas)",
                         t.strip() == "--"))

        # ── TÉMOIN 3 : NÉGATIF, MOCK ──────────────────────────────────────
        print("── TÉMOIN NÉGATIF « MOCK » — régime SIMULÉE, ambre 0xffb020 ─────")
        cmd("widget mock on")
        time.sleep(1.2)
        det = cmd("widget detail")
        reg = cmd("widget")
        arme = "mock : ARME" in reg
        r = regime(reg, CASE_NET)
        t = texte(det)
        print(f"   mock ARMÉ : {arme} · régime de la case RÉSEAU : {r}")
        print(f"   dalle « {t} »")
        time.sleep(1.2)
        t2 = texte(cmd("widget detail"))
        print(f"   1,2 s plus tard : « {t2} »  (un mock FIGÉ serait "
              "indiscernable d'un affichage bloqué)")
        verdicts.append(
            ("MOCK — régime SIMULÉE (ambre 0xffb020), ⛔ jamais blanc, et la "
             "valeur VARIE",
             arme and r.startswith("SIMUL") and t.strip() != "--" and t != t2))
        cmd("widget mock off")

        # ── TÉMOIN 4 : CROISÉ ─────────────────────────────────────────────
        print("── TÉMOIN CROISÉ — détail sur CPU pendant que `net` bouge ───────")
        cmd(f"pc {trame(seq, 1000, 'cpu', (500, 30, 500, 400))}")
        seq += 1
        time.sleep(0.6)
        cmd(f"nav open {CASE_CPU}")
        time.sleep(0.4)
        avant = texte(cmd("widget detail"))
        print(f"   détail CPU avant : « {avant} »")
        for d, u in ((1111, 2222), (3333, 4444), (5555, 6666)):
            cmd(f"pc {trame(seq, 1000, 'net', (d, u))}")
            seq += 1
            time.sleep(0.5)
        apres = texte(cmd("widget detail"))
        print(f"   détail CPU après 3 trames `net` : « {apres} »")
        verdicts.append(("CROISÉ — le détail de CPU NE BOUGE PAS quand `net` bouge",
                         avant == apres and avant.strip() != "--"))

        print()
        print("=" * 72)
        tout = True
        for nom, ok in verdicts:
            print(f"  {'✅' if ok else '🔴'}  {nom}")
            tout = tout and ok
        print("=" * 72)
        return 0 if tout else 1
    finally:
        ser.close()


if __name__ == "__main__":
    raise SystemExit(main())

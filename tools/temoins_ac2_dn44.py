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
   rien — le coût que `dn_ui.c` interdit d'ajouter sur « le chemin le plus chaud
   de la vue détail ».

🔴🔴 dn4-13 / AC7.1 — LE TÉMOIN CROISÉ RENDAIT **VERT SUR DEUX LECTURES RATÉES**.
   `texte()` rend la sentinelle `"<NON RELU>"` quand la regex ne trouve rien, et
   le verdict croisé était `avant == apres and avant.strip() != "--"`.
   ⇒ `"<NON RELU>" == "<NON RELU>"` est **VRAI**, et `"<NON RELU>" != "--"` aussi
     ⇒ **`True and True` = ✅ VERT**, sur un harnais qui n'a RIEN LU.
   ⚠️ Et c'est la garde que le dossier de `dn4-4` CÉLÈBRE (*« le témoin croisé
      n'est valide que si l'avant n'est pas `--` »*) : elle attrape le `--`,
      **pas** le `<NON RELU>`. Les trois autres témoins, eux, tombaient
      correctement au rouge.
   ⇒ LEÇON GÉNÉRALE, ÉCRITE ICI : **une sentinelle de repli qui entre dans une
     comparaison fabrique un verdict.** Toute sentinelle se teste AVANT usage,
     jamais après. Les quatre verdicts sont désormais des FONCTIONS PURES qui
     refusent `NON_RELU` en premier, et `--temoin-negatif` les fait rougir.
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

# 🔴 LA SENTINELLE EST NOMMÉE, ⛔ PLUS ÉCRITE EN DUR À TROIS ENDROITS. Une
#    sentinelle recopiée est une sentinelle qu'on oublie de tester quelque part.
NON_RELU = "<NON RELU>"


def texte(sortie):
    m = _TXT.search(sortie)
    return m.group(1).replace("\n", " | ").strip() if m else NON_RELU


def lu(*valeurs):
    """`True` seulement si TOUTES les valeurs ont été RÉELLEMENT relues.

    ⛔ C'est le premier terme de chaque verdict, et il est le premier
       DÉLIBÉRÉMENT : une comparaison entre deux sentinelles est vraie, donc un
       verdict qui compare d'abord et vérifie ensuite est déjà perdu."""
    return all(v is not None and v != NON_RELU for v in valeurs)


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
    return NON_RELU


# ═══════════════════════════════════════════════════════════════════════════
# LES QUATRE VERDICTS — FONCTIONS PURES, ⛔ AUCUN PORT SÉRIE
# ═══════════════════════════════════════════════════════════════════════════
# 🔴 dn4-13 / AC7.5 — ILS SONT EXTRAITS POUR ÊTRE **APPELÉS** PAR LE TÉMOIN
#    NÉGATIF. Un harnais qui REJOUE au lieu d'EXTRAIRE+APPELER ne peut être
#    éprouvé que sur la carte, c'est-à-dire jamais avant la séance — et une gate
#    qu'aucun test n'a vue échouer est décorative.
def verdict_positif(vus):
    """Les 3 textes relus, DANS L'ORDRE, et tous les trois RÉELLEMENT lus."""
    if not lu(*vus) or len(vus) != 3:
        return False
    return (len(set(vus)) == 3 and "123,4" in vus[0] and "432,1" in vus[1]
            and "777,7" in vus[2])


def verdict_peremption(t):
    """Retour à « -- » après 4 s de silence (AC7 de dn2-2 ne régresse pas)."""
    if not lu(t):
        return False
    return t.strip() == "--"


def verdict_mock(arme, reg, t, t2):
    """Régime SIMULÉE, ⛔ jamais blanc, ET la valeur VARIE."""
    if not lu(reg, t, t2):
        return False
    return bool(arme) and reg.startswith("SIMUL") and t.strip() != "--" and t != t2


def verdict_croise(avant, apres):
    """Le détail de CPU NE BOUGE PAS pendant que `net` bouge.

    ⛔ `lu()` D'ABORD. C'est LE correctif d'AC7.1 : sans lui, deux lectures
       ratées se comparaient égales et rendaient VERT."""
    if not lu(avant, apres):
        return False
    return avant == apres and avant.strip() != "--"


# ═══════════════════════════════════════════════════════════════════════════
# LE TÉMOIN NÉGATIF — ⛔ SANS CARTE, ET IL DOIT VOIR ROUGE
# ═══════════════════════════════════════════════════════════════════════════
def temoin_negatif():
    """On donne aux quatre verdicts des entrées qui DOIVENT les faire rougir.

    🔴 dn4-13 / AC7.5 — LA PREMIÈRE LIGNE EST CELLE QUI COMPTE : c'est le vert
       qu'AC2 a publié le 2026-08-24 sur DEUX LECTURES RATÉES."""
    N = NON_RELU
    cas = [
        # (nom, appel, attendu)
        ("CROISÉ · deux lectures RATÉES", lambda: verdict_croise(N, N), False),
        ("CROISÉ · avant RATÉ seulement", lambda: verdict_croise(N, "12,3"), False),
        ("CROISÉ · après RATÉ seulement", lambda: verdict_croise("12,3", N), False),
        ("CROISÉ · deux « -- » (garde d'origine)",
         lambda: verdict_croise("--", "--"), False),
        ("CROISÉ · la page a BOUGÉ", lambda: verdict_croise("1,0", "2,0"), False),
        ("CROISÉ · cas SAIN", lambda: verdict_croise("50,0 %", "50,0 %"), True),
        ("PÉREMPTION · lecture RATÉE", lambda: verdict_peremption(N), False),
        ("PÉREMPTION · la valeur est RESTÉE",
         lambda: verdict_peremption("123,4 / 567,8"), False),
        ("PÉREMPTION · cas SAIN", lambda: verdict_peremption("--"), True),
        ("MOCK · régime NON RELU",
         lambda: verdict_mock(True, N, "1,0", "2,0"), False),
        ("MOCK · texte NON RELU",
         lambda: verdict_mock(True, "SIMULÉE", N, N), False),
        ("MOCK · mock NON armé",
         lambda: verdict_mock(False, "SIMULÉE", "1,0", "2,0"), False),
        ("MOCK · valeur FIGÉE (mock immobile)",
         lambda: verdict_mock(True, "SIMULÉE", "1,0", "1,0"), False),
        ("MOCK · régime RÉELLE (le mock n'a pas pris)",
         lambda: verdict_mock(True, "RÉELLE", "1,0", "2,0"), False),
        ("MOCK · cas SAIN",
         lambda: verdict_mock(True, "SIMULÉE", "1,0", "2,0"), True),
        ("POSITIF · une lecture RATÉE sur trois",
         lambda: verdict_positif(["123,4", N, "777,7"]), False),
        ("POSITIF · trois fois le MÊME texte",
         lambda: verdict_positif(["123,4", "123,4", "123,4"]), False),
        ("POSITIF · le bon jeu, DANS LE DÉSORDRE",
         lambda: verdict_positif(["777,7", "432,1", "123,4"]), False),
        ("POSITIF · cas SAIN",
         lambda: verdict_positif(["123,4 / 567,8", "432,1 / 876,5",
                                  "777,7 / 111,1"]), True),
    ]
    print("=" * 72)
    print("dn4-13 / AC7.5 — TÉMOIN NÉGATIF de `temoins_ac2_dn44.py` (SANS CARTE)")
    print("=" * 72)
    ko = 0
    for nom, f, attendu in cas:
        obtenu = f()
        ok = (obtenu == attendu)
        ko += 0 if ok else 1
        print("  %s  %-46s attendu %-5s obtenu %s"
              % ("✅" if ok else "🔴", nom, attendu, obtenu))
    print("=" * 72)
    if ko:
        print("⛔ %d cas sur %d ne se comportent pas comme annoncé." % (ko, len(cas)))
        return 1
    print("✅ %d cas — les 4 verdicts refusent la sentinelle AVANT de comparer."
          % len(cas))
    print("⚠️ CE QUE CE TÉMOIN NE PROUVE PAS : que la carte propage. Il prouve que")
    print("   l'INSTRUMENT ne peut plus rendre vert sans avoir lu. Les quatre")
    print("   témoins eux-mêmes se tirent sur la carte, en séance.")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", default="/dev/ttyACM0")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--seq0", type=int, default=400)
    p.add_argument("--temoin-negatif", action="store_true",
                   help="éprouve les VERDICTS hors carte, et exige de les voir "
                        "rougir (dn4-13 / AC7.5)")
    a = p.parse_args()

    if a.temoin_negatif:
        return temoin_negatif()

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
        verdicts.append(("POSITIF — 3 textes successifs, dans l'ordre",
                         verdict_positif(vus)))

        # ── TÉMOIN 2 : NÉGATIF, PÉREMPTION ────────────────────────────────
        print("── TÉMOIN NÉGATIF « PÉREMPTION » — injection coupée > 3 s ───────")
        print("   (on ne touche à RIEN pendant 4,0 s : la péremption est à 3 s)")
        time.sleep(4.0)
        t = texte(cmd("widget detail"))
        print(f"   dalle après 4,0 s de silence : « {t} »")
        verdicts.append(("PÉREMPTION — retour à « -- » (AC7 de dn2-2 ne régresse pas)",
                         verdict_peremption(t)))

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
             "valeur VARIE", verdict_mock(arme, r, t, t2)))
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
                         verdict_croise(avant, apres)))

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

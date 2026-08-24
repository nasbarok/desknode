#!/usr/bin/env python3
"""
dn4-4 / AC1 — RE-DIAGNOSTIC DE `P1` PAR LA MESURE.

⛔ CE SCRIPT N'EST PAS UN CORRECTIF. Il rejoue le symptôme du 2026-08-24
   (« le détail RÉSEAU reste sur les valeurs de l'ouverture pendant que le fil
   porte autre chose ») avec un protocole qui NE PEUT PAS fabriquer le faux
   positif que l'injecteur fabrique.

🔴 POURQUOI `dn_injecteur.py` NE PEUT PAS SERVIR ICI (piège d'instrument n°1) :
   ses jeux portent des valeurs FIXES par métrique ; seul le `seq` incrémente.
   ⇒ une propagation qui marche et une propagation cassée rendent LE MÊME ÉCRAN.
   L'instrument ne peut pas voir le défaut qu'il prétend exclure.

LE PROTOCOLE, ÉCRIT AVANT D'ÊTRE EXÉCUTÉ :
  1. `nav open 3`   -> le détail est ouvert sur RÉSEAU, et il y RESTE.
  2. `widget mock`  -> G3 est lue, ⛔ pas supposée (le mock armé a la priorité
                       et survit à la séance).
  3. `pc`           -> compteurs AVANT : doublons / pertes_seq / rejets_* / seq.
  4. N tours, chacun :
       - une trame `net` dont LES DEUX VALEURS CHANGENT (⛔ pas seulement `seq`),
       - `seq` INCRÉMENTÉ de 1,
       - checksum RECALCULÉ (XOR du corps) — ⛔ jamais tapé,
       - une pause >= la période de la tâche `dn_link` (250 ms) pour que la
         poussée AIT LIEU, et < 3 s pour que la vue NE PÉRIME PAS,
       - `widget detail` : RELECTURE DES OBJETS LVGL, ⛔ pas un constat à l'œil.
  5. `pc`           -> compteurs APRÈS. Un `doublons` qui monte = harnais.

VERDICT ATTENDU, DANS L'UNE DES DEUX FORMES :
  · les N textes relus SUIVENT les N trames        -> le défaut NE se reproduit
                                                      PAS : l'écart du
                                                      2026-08-24 est un défaut
                                                      de harnais, et le compteur
                                                      le dit.
  · un texte relu RESTE sur une valeur périmée      -> le défaut SE REPRODUIT :
                                                      la cause est cherchée avec
                                                      les compteurs de l'étape 5.
"""
import argparse
import re
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import dn_console


def _ck(corps):
    x = 0
    for o in corps.encode("ascii"):
        x ^= o
    return f"{x:02X}"


def trame_net(seq, t_ms, descente_dx, montee_dx):
    """v3, en DIXIÈMES comme le fil. Checksum RECALCULÉ (⛔ jamais tapé)."""
    corps = f"DN,3,{seq},{t_ms},net,{descente_dx},{montee_dx}"
    return f"${corps}*{_ck(corps)}"


_TXT = re.compile(r"texte\s*:\s*«\s*(.*?)\s*»", re.S)


def _entier(sortie, nom):
    """Relit un compteur de `pc` — ⛔ jamais une estimation."""
    m = re.search(r"(\d+)\s+" + re.escape(nom), sortie)
    return int(m.group(1)) if m else -1


def _compteurs(sortie):
    """Les seules lignes de `pc` qui portent une PREUVE pour AC1."""
    gardees = []
    for ligne in sortie.splitlines():
        if (ligne.startswith("trames ") or ligne.startswith("rejets ")
                or ligne.lstrip().startswith("net ")
                or ligne.startswith("latence ")
                or ligne.startswith("poussee ")):
            gardees.append("  " + ligne.rstrip())
    return "\n".join(gardees)


def texte_detail(sortie):
    m = _TXT.search(sortie)
    return m.group(1).replace("\n", " | ") if m else "<NON RELU>"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", default="/dev/ttyACM0")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--tours", type=int, default=6)
    p.add_argument("--seq0", type=int, default=200)
    p.add_argument("--pause", type=float, default=0.6,
                   help="entre l'injection et la relecture (>= 0,25 s, < 3 s)")
    a = p.parse_args()

    if not (0.25 <= a.pause < 3.0):
        print("refuse : --pause doit tenir dans [0,25 ; 3,0[ — sous 0,25 s la "
              "tâche dn_link n'a pas eu son réveil, au-delà de 3 s la vue périme.")
        return 2

    ser = dn_console.ouvrir(a.port, a.baud)
    try:
        dn_console.reveiller(ser)

        def cmd(c, timeout=20):
            # ⚠️ `envoyer()` rend un DICT, ⛔ pas une chaîne : lire `sortie`.
            #    Le harnais s'est planté dessus au premier tir — écrit ici pour
            #    que le prochain ne le repaie pas.
            return dn_console.envoyer(ser, c, timeout)["sortie"]

        print("=" * 72)
        print("dn4-4 / AC1 — RE-DIAGNOSTIC DE P1. Protocole écrit avant exécution.")
        print("=" * 72)
        print(cmd("nav open 3"))
        # 🔴 L'INSTRUMENT DE G3 EST `widget` NU, ⛔ PAS `widget mock`.
        #    Le cadrage de dn4-4 écrit « `widget mock` dit si G3 est armée » :
        #    c'est FAUX — sans `on|off` cette sous-commande imprime son usage et
        #    rend 0x1. Mesuré le 2026-08-24. La ligne « mock : ARME|COUPE » est
        #    imprimée par la branche SANS ARGUMENT de `cmd_widget`.
        print("--- G3 : le mock est-il ARMÉ ? (⛔ lu, pas supposé) --------------")
        etat = cmd("widget")
        for ligne in etat.splitlines():
            if ligne.startswith("mock ") or "demo 7e" in ligne:
                print("  " + ligne)
        print("--- COMPTEURS AVANT ---------------------------------------------")
        avant = cmd("pc")
        print(_compteurs(avant))
        print("  detail RÉSEAU à l'ouverture : « {} »".format(
            texte_detail(cmd("widget detail"))))

        # Les valeurs CHANGENT à chaque tour, et elles sont choisies pour être
        # lisibles à l'œil comme au grep : 111,0/222,0 puis 333,0/444,0, etc.
        lignes = []
        for i in range(a.tours):
            seq = a.seq0 + i
            d = 1110 + i * 2220
            u = 2220 + i * 1110
            t = trame_net(seq, 1000 + i * 250, d, u)
            cmd(f"pc {t}")
            time.sleep(a.pause)
            relu = texte_detail(cmd("widget detail"))
            attendu = f"{d/10:.1f} / {u/10:.1f}".replace(".", ",")
            lignes.append((seq, attendu, relu))
            print(f"  tour {i+1}/{a.tours} · seq {seq} · fil « {attendu} »")
            print(f"      dalle relue : « {relu} »")

        # ══════════════════════════════════════════════════════════════════
        # PHASE 2 — LE TÉMOIN NÉGATIF QU'AC1.4 NOMME : `seq` FIGÉ.
        # ══════════════════════════════════════════════════════════════════
        # 🔴 C'est le seul geste qui DÉMONTRE le défaut de harnais au lieu de
        #    l'affirmer. `dn_link.c:452-456` compte `doublons` et IGNORE la
        #    valeur : à `seq` figé, une propagation qui marche rend un écran
        #    FIGÉ — c'est-à-dire EXACTEMENT le symptôme du 2026-08-24.
        # ⚠️ Les valeurs CHANGENT à chaque tour : si l'écran suivait quand même,
        #    ce serait la garde qui serait cassée, pas le harnais.
        print("--- PHASE 2 : TÉMOIN NÉGATIF « seq FIGÉ » -----------------------")
        seq_fige = a.seq0 + a.tours + 10
        dbl_avant = _entier(cmd("pc"), "doublons")
        neg = []
        for i in range(5):
            d = 9990 - i * 1110
            u = 1110 + i * 999
            cmd(f"pc {trame_net(seq_fige, 5000 + i * 250, d, u)}")
            time.sleep(a.pause)
            relu = texte_detail(cmd("widget detail"))
            neg.append((d, u, relu))
            print(f"  tour {i+1}/5 · seq FIGÉ {seq_fige} · fil « "
                  f"{d/10:.1f} / {u/10:.1f} »".replace(".", ","))
            print(f"      dalle relue : « {relu} »")
        dbl_apres = _entier(cmd("pc"), "doublons")
        distincts = len({r for _, _, r in neg})
        print(f"  doublons : {dbl_avant} -> {dbl_apres} "
              f"(+{dbl_apres - dbl_avant}) · textes DISTINCTS sur la dalle : "
              f"{distincts}")

        print("--- COMPTEURS APRÈS ---------------------------------------------")
        apres = cmd("pc")
        print(_compteurs(apres))

        print("=" * 72)
        print("SYNTHÈSE — le fil, tour par tour, et ce que la DALLE portait")
        print("=" * 72)
        fige = 0
        precedent = None
        for seq, attendu, relu in lignes:
            bouge = "" if relu == precedent else "CHANGE"
            if relu == precedent:
                fige += 1
            print(f"  seq {seq:>4}  fil « {attendu:<20} »  dalle « {relu} »  {bouge}")
            precedent = relu
        print()
        if fige:
            print(f"🔴 LA DALLE EST RESTÉE FIGÉE sur {fige} tour(s) : LE DÉFAUT SE "
                  f"REPRODUIT. Lire les compteurs ci-dessus pour nommer la cause.")
            return 1
        print("✅ PHASE 1 — LA DALLE A SUIVI LES {} TRAMES, DANS L'ORDRE : le "
              "défaut NE se reproduit PAS\n   sous un protocole à `seq` "
              "croissant et valeurs changeantes.".format(len(lignes)))
        print()
        if distincts == 1 and dbl_apres > dbl_avant:
            print("🔴 PHASE 2 — À `seq` FIGÉ, LA DALLE EST RESTÉE SUR UN SEUL "
                  "TEXTE pendant que\n   `doublons` montait de "
                  f"{dbl_apres - dbl_avant}. LE SYMPTÔME DU 2026-08-24 EST "
                  "REPRODUIT\n   À VOLONTÉ, ET SA CAUSE EST LE HARNAIS, ⛔ PAS "
                  "LE FIRMWARE.")
            print("   ⇒ AC1 se solde sur sa SECONDE forme, avec son compteur.")
            return 0
        print("⚠️ PHASE 2 N'A PAS RENDU LA FIGURE ATTENDUE "
              f"(textes distincts = {distincts}, doublons "
              f"+{dbl_apres - dbl_avant}) :\n   ⛔ NE PAS CONCLURE — relire les "
              "compteurs avant d'écrire quoi que ce soit.")
        return 3
    finally:
        ser.close()


if __name__ == "__main__":
    raise SystemExit(main())

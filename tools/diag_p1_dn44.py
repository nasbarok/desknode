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


# 🔴 dn4-13 / AC7.2 — LA SENTINELLE EST NOMMÉE, ET ELLE NE VAUT PLUS `-1` NU.
#    `_entier()` rendait `-1` quand la regex ne trouvait rien. Deux `-1` entraient
#    ensuite dans `dbl_apres - dbl_avant` : **`-1 - (-1) = 0`**, imprimé
#    « doublons +0 » — un ZÉRO FABRIQUÉ, indiscernable d'une vraie absence de
#    doublon, ET QUI PILOTAIT UN VERDICT (`dbl_apres > dbl_avant`).
#    ⇒ La sentinelle se teste AVANT toute soustraction publiée.
NON_RELU_INT = -1
NON_RELU = "<NON RELU>"


def _entier(sortie, nom):
    """Relit un compteur de `pc` — ⛔ jamais une estimation.

    Rend `NON_RELU_INT` si la ligne n'a pas été trouvée. ⛔ Ce nombre N'ENTRE
    JAMAIS dans une soustraction publiée : voir `delta_compteur()`."""
    m = re.search(r"(\d+)\s+" + re.escape(nom), sortie)
    return int(m.group(1)) if m else NON_RELU_INT


def delta_compteur(avant, apres):
    """L'écart entre deux relevés, ou `None` si l'un des deux n'a pas été LU.

    ⛔ `None`, ⛔ pas `0` : « je n'ai pas lu » et « rien n'a bougé » sont deux
       choses, et les confondre a déjà fait publier « doublons +0 »."""
    if avant == NON_RELU_INT or apres == NON_RELU_INT:
        return None
    return apres - avant


def verdict_phase1(lignes):
    """(figes, ok) — la dalle a-t-elle SUIVI les trames ?

    ⛔ Une lecture ratée est un ÉCHEC, ⛔ pas un « pas de changement » : deux
       `NON_RELU` consécutifs se comparaient égaux et comptaient un figement...
       ou, pire selon l'ordre, disparaissaient du décompte. Ici, la moindre
       sentinelle invalide la phase entière."""
    # ⛔ LA GARDE EST **DANS LA FONCTION**, ⛔ pas seulement dans l'argparse.
    #    Sinon le refus de `--tours < 2` ne serait qu'une politesse d'interface :
    #    un futur appelant (ou ce témoin négatif) pourrait obtenir un ✅ sur un
    #    échantillon unique. La propriété testée est « la dalle CHANGE d'un tour
    #    à l'autre » — elle n'a aucun sens sous deux tours.
    if len(lignes) < 2:
        return 0, False
    if any(relu == NON_RELU for _, _, relu in lignes):
        return -1, False
    figes = 0
    precedent = None
    for _seq, _att, relu in lignes:
        if relu == precedent:
            figes += 1
        precedent = relu
    return figes, figes == 0


def verdict_phase2(textes, dbl_avant, dbl_apres):
    """(distincts, delta, ok) — à `seq` FIGÉ, la dalle DOIT rester sur un texte
    pendant que `doublons` monte.

    ⛔ Une sentinelle dans `textes` invalide : `{NON_RELU}` a un cardinal de 1,
       donc « un seul texte distinct » — la figure ATTENDUE, obtenue sans avoir
       rien lu. C'est le même piège que le témoin croisé d'AC2, à un instrument
       de distance."""
    if not textes or any(t == NON_RELU for t in textes):
        return 0, None, False
    delta = delta_compteur(dbl_avant, dbl_apres)
    if delta is None:
        return len(set(textes)), None, False
    return len(set(textes)), delta, (len(set(textes)) == 1 and delta > 0)


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
    return m.group(1).replace("\n", " | ") if m else NON_RELU


# ═══════════════════════════════════════════════════════════════════════════
# LE TÉMOIN NÉGATIF — ⛔ SANS CARTE, ET IL DOIT VOIR ROUGE
# ═══════════════════════════════════════════════════════════════════════════
def temoin_negatif():
    """dn4-13 / AC7.5 — les verdicts de `diag_p1` sont éprouvés HORS CARTE.

    🔴 Les trois lignes qui comptent sont les trois premières : elles rejouent
       les trois façons dont ce script rendait un verdict SUR DU VIDE."""
    N = NON_RELU
    L = lambda *t: [(200 + i, "x", v) for i, v in enumerate(t)]
    cas = [
        ("PHASE 1 · ZÉRO tour (l'ancien `--tours 0`)",
         lambda: verdict_phase1([])[1], False),
        ("PHASE 1 · UN seul tour (l'ancien `--tours 1`)",
         lambda: verdict_phase1(L("123,4"))[1], False),
        ("PHASE 1 · une lecture RATÉE au milieu",
         lambda: verdict_phase1(L("1,0", N, "3,0"))[1], False),
        ("PHASE 1 · deux lectures RATÉES d'affilée",
         lambda: verdict_phase1(L(N, N))[1], False),
        ("PHASE 1 · la dalle FIGE sur un tour",
         lambda: verdict_phase1(L("1,0", "1,0", "3,0"))[1], False),
        ("PHASE 1 · cas SAIN (3 textes distincts)",
         lambda: verdict_phase1(L("1,0", "2,0", "3,0"))[1], True),
        ("PHASE 2 · sentinelle ⇒ « 1 texte distinct » FABRIQUÉ",
         lambda: verdict_phase2([N, N, N], 10, 14)[2], False),
        ("PHASE 2 · les DEUX compteurs non lus (`-1 - (-1) = 0`)",
         lambda: verdict_phase2(["a", "a"], NON_RELU_INT, NON_RELU_INT)[2], False),
        ("PHASE 2 · un seul compteur non lu",
         lambda: verdict_phase2(["a", "a"], 10, NON_RELU_INT)[2], False),
        ("PHASE 2 · doublons N'A PAS monté",
         lambda: verdict_phase2(["a", "a"], 10, 10)[2], False),
        ("PHASE 2 · la dalle a SUIVI (pas la figure attendue)",
         lambda: verdict_phase2(["a", "b"], 10, 14)[2], False),
        ("PHASE 2 · cas SAIN", lambda: verdict_phase2(["a", "a"], 10, 14)[2], True),
        ("DELTA · non lu ⇒ `None`, ⛔ pas `0`",
         lambda: delta_compteur(NON_RELU_INT, NON_RELU_INT), None),
        ("DELTA · lu ⇒ la vraie différence",
         lambda: delta_compteur(10, 14), 4),
    ]
    print("=" * 72)
    print("dn4-13 / AC7.5 — TÉMOIN NÉGATIF de `diag_p1_dn44.py` (SANS CARTE)")
    print("=" * 72)
    ko = 0
    for nom, f, attendu in cas:
        obtenu = f()
        ok = (obtenu == attendu)
        ko += 0 if ok else 1
        print("  %s  %-50s attendu %-5s obtenu %s"
              % ("✅" if ok else "🔴", nom, attendu, obtenu))
    print("=" * 72)
    if ko:
        print("⛔ %d cas sur %d ne se comportent pas comme annoncé." % (ko, len(cas)))
        return 1
    print("✅ %d cas — aucun verdict ne peut plus naître d'une lecture ratée,\n"
          "   d'une soustraction de sentinelles, ni de zéro échantillon." % len(cas))
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", default="/dev/ttyACM0")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--tours", type=int, default=6,
                   help="au moins 2 — voir le refus ci-dessous")
    p.add_argument("--seq0", type=int, default=200)
    p.add_argument("--pause", type=float, default=0.6,
                   help="entre l'injection et la relecture (>= 0,25 s, < 3 s)")
    p.add_argument("--temoin-negatif", action="store_true",
                   help="éprouve les VERDICTS hors carte, et exige de les voir "
                        "rougir (dn4-13 / AC7.5)")
    a = p.parse_args()

    if a.temoin_negatif:
        return temoin_negatif()

    # 🔴 dn4-13 / AC7.2 — `--tours` EST BORNÉ À >= 2, ET C'EST UNE GARDE DE
    #    VACUITÉ, ⛔ pas un confort d'usage.
    #    · `--tours 0` : la boucle ne tourne pas, `lignes` est vide, `fige`
    #      vaut 0 ⇒ le script imprimait « ✅ LA DALLE A SUIVI LES 0 TRAMES »
    #      et rendait **0**. UN VERT SUR ZÉRO ÉCHANTILLON.
    #    · `--tours 1` : un seul texte, `precedent` vaut `None`, donc aucun
    #      figement possible ⇒ vert sur un échantillon UNIQUE, alors que la
    #      propriété testée est « la dalle CHANGE d'un tour à l'autre » : elle
    #      n'a pas de sens sous deux tours.
    #    ⇒ On REFUSE, ⛔ on n'écrête pas : un écrêtage silencieux ferait publier
    #      un verdict sur un protocole que personne n'a demandé.
    if a.tours < 2:
        print("refuse : --tours doit valoir au moins 2. La propriete testee est\n"
              "  « la dalle CHANGE d'un tour a l'autre » : sous deux tours elle\n"
              "  n'a aucun sens, et le script rendait un ✅ VERT SUR ZERO (ou UN)\n"
              "  echantillon. ⛔ Un vert sur rien est pire qu'un rouge.")
        return 2

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
        distincts, delta, phase2_ok = verdict_phase2(
            [r for _, _, r in neg], dbl_avant, dbl_apres)
        # ⛔ LE DELTA NE S'IMPRIME QUE S'IL A ÉTÉ LU. « +0 » sur deux sentinelles
        #    est un zéro FABRIQUÉ, et il pilotait un verdict.
        d_txt = ("+%d" % delta) if delta is not None else "NON LU (⛔ pas « +0 »)"
        print(f"  doublons : {dbl_avant} -> {dbl_apres} "
              f"({d_txt}) · textes DISTINCTS sur la dalle : {distincts}")

        print("--- COMPTEURS APRÈS ---------------------------------------------")
        apres = cmd("pc")
        print(_compteurs(apres))

        print("=" * 72)
        print("SYNTHÈSE — le fil, tour par tour, et ce que la DALLE portait")
        print("=" * 72)
        precedent = None
        for seq, attendu, relu in lignes:
            bouge = "" if relu == precedent else "CHANGE"
            print(f"  seq {seq:>4}  fil « {attendu:<20} »  dalle « {relu} »  {bouge}")
            precedent = relu
        print()
        fige, phase1_ok = verdict_phase1(lignes)
        if fige < 0:
            print("🔴 UNE RELECTURE AU MOINS A ECHOUE (« %s ») : ⛔ AUCUN VERDICT.\n"
                  "   Une lecture ratee n'est pas « pas de changement » — deux\n"
                  "   sentinelles se comparent EGALES, et ce script aurait conclu\n"
                  "   sur du vide." % NON_RELU)
            return 1
        if not phase1_ok:
            print(f"🔴 LA DALLE EST RESTÉE FIGÉE sur {fige} tour(s) : LE DÉFAUT SE "
                  f"REPRODUIT. Lire les compteurs ci-dessus pour nommer la cause.")
            return 1
        print("✅ PHASE 1 — LA DALLE A SUIVI LES {} TRAMES, DANS L'ORDRE : le "
              "défaut NE se reproduit PAS\n   sous un protocole à `seq` "
              "croissant et valeurs changeantes.".format(len(lignes)))
        print()
        if phase2_ok:
            print("🔴 PHASE 2 — À `seq` FIGÉ, LA DALLE EST RESTÉE SUR UN SEUL "
                  "TEXTE pendant que\n   `doublons` montait de "
                  f"{delta}. LE SYMPTÔME DU 2026-08-24 EST "
                  "REPRODUIT\n   À VOLONTÉ, ET SA CAUSE EST LE HARNAIS, ⛔ PAS "
                  "LE FIRMWARE.")
            print("   ⇒ AC1 se solde sur sa SECONDE forme, avec son compteur.")
            return 0
        print("⚠️ PHASE 2 N'A PAS RENDU LA FIGURE ATTENDUE "
              f"(textes distincts = {distincts}, doublons {d_txt}) :\n"
              "   ⛔ NE PAS CONCLURE — relire les compteurs avant d'écrire quoi "
              "que ce soit.")
        return 3
    finally:
        ser.close()


if __name__ == "__main__":
    raise SystemExit(main())

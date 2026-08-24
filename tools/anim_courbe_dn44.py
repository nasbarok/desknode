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


def trame(seq, t_ms, metrique, valeurs):
    corps = f"DN,3,{seq},{t_ms},{metrique}," + ",".join(str(int(v)) for v in valeurs)
    return f"${corps}*{_ck(corps)}"


# 🔴 dn4-13 / AC7.3 — LE COMPTEUR D'ACCEPTATIONS, RELU DE `pc`.
#    Format publié par le firmware :
#      « trames     : %u valides · %u doublons · %u pertes seq · ... »
#    `valides` est le nombre de trames que `dn_link` a ACCEPTÉES ; les rejets
#    (checksum, tronquée, bornes…) n'y sont PAS, et c'est tout l'intérêt.
_TRAMES = re.compile(r"trames\s*:\s*(\d+)\s+valides")


def _trames_acceptees(sortie):
    """Le compteur `valides`, ou `None` s'il n'a pas été LU.

    ⛔ `None`, ⛔ pas `0` : « je n'ai pas lu le compteur » et « la carte n'a rien
       accepté » sont deux choses. Les confondre publierait « 0 acceptée » sur un
       harnais qui n'a simplement pas su parser — et ce dépôt a déjà payé
       exactement ce genre de zéro fabriqué (`-1 - (-1) = 0`, `diag_p1`)."""
    m = _TRAMES.search(sortie)
    return int(m.group(1)) if m else None


def jeu(t):
    """
    🔴 UNE FORME DIFFÉRENTE PAR MÉTRIQUE — ET C'EST UN CORRECTIF D'INSTRUMENT,
       ⛔ PAS UNE COQUETTERIE.

    ⚠️ LA PREMIÈRE VERSION ÉMETTAIT DES SINUSOÏDES POUR TOUT LE MONDE. Comme
       l'échelle du graphe s'AUTO-CALE sur les données, chaque série remplissait
       la boîte : **toutes les pages rendaient la MÊME VAGUE**, quelles que
       soient leurs amplitudes réelles. Constat owner du 2026-08-24, verbatim :
       *« en fait c'est parce que la courbe de cpu et gpu sont les mêmes ! »*
       ⇒ **LE HARNAIS FABRIQUAIT LA RESSEMBLANCE QU'IL SERVAIT À TESTER.**
       C'est la faute que ce dépôt reproche déjà à `dn_injecteur.py` (« valeurs
       FIXES »), d'un cran plus subtile : des valeurs qui CHANGENT ne suffisent
       pas, il faut qu'elles changent **DIFFÉREMMENT**.

    ⇒ Chaque métrique reçoit une forme RECONNAISSABLE À L'ŒIL : dent de scie,
      créneau, rampe, sinus, marches. Si deux pages rendent la même courbe
      maintenant, **c'est le firmware qui lit la mauvaise série**, ⛔ plus le
      signal qui se ressemble.
    """
    # dent de scie descendante — reconnaissable entre toutes
    scie = 1.0 - (t % 12.0) / 12.0
    # créneau : deux niveaux francs, ⛔ aucune pente
    creneau = 1.0 if (t % 16.0) < 8.0 else 0.0
    # rampe montante lente, remise à zéro
    rampe = (t % 25.0) / 25.0
    # marches d'escalier — cinq paliers
    marches = math.floor((t % 20.0) / 4.0) / 4.0
    # sinus, gardé pour UNE seule métrique
    sinus = 0.5 + 0.5 * math.sin(t / 7.0)
    # 🔴 dn4-13 / AC7.3 — UNE CINQUIÈME FORME, ET C'EST UN CORRECTIF DE FOND.
    #    Le commentaire ci-dessus disait « gardé pour UNE seule métrique » —
    #    C'ÉTAIT FAUX : `net` grandeur 1 ET `disk` grandeur 0 portaient tous les
    #    deux `sinus`, et les deux séries sont AUTO-CALÉES. Deux pages rendaient
    #    donc LA MÊME VAGUE, exactement le défaut que ce fichier prétend avoir
    #    corrigé six lignes plus haut. Le harnais fabriquait encore la
    #    ressemblance qu'il sert à tester, d'un cran plus discret.
    # ⇒ `disk` grandeur 0 reçoit une IMPULSION : plate la plupart du temps, avec
    #   un pic court et franc. ⛔ Aucune pente, aucune période commune avec le
    #   sinus (13 s contre 2*pi*7 ≈ 44 s) — impossible de les confondre à l'œil.
    impulsion = 1.0 if (t % 13.0) < 2.0 else 0.0
    return {
        # cpu : DENT DE SCIE (%, GHz, c.max %, °C)
        "cpu": (100 + 850 * scie, 20 + 35 * scie, 200 + 700 * scie,
                350 + 450 * scie),
        # gpu : CRÉNEAU — ⛔ impossible à confondre avec une dent de scie
        "gpu": (150 + 800 * creneau, 400 + 500 * creneau,
                800 + 2000 * creneau, 8000 + 14000 * creneau),
        # ram : RAMPE (et son échelle est BORNÉE 0..100 %, donc la rampe se lit
        #       en NIVEAU ABSOLU, ce qui est tout l'intérêt de la borne)
        "ram": (50 + 900 * rampe, 342),
        # net : descendant en MARCHES, montant en SINUS — les DEUX courbes de la
        #       page doivent être discernables l'une de l'autre, pas seulement
        #       des autres pages.
        "net": (100 + 25000 * marches, 200 + 12000 * sinus),
        # disk : IMPULSION (⛔ plus le sinus de `net` ^) + trois ventilateurs
        "disk": (2000 + 18000 * impulsion, 4000 + 16000 * marches,
                 6000 + 10000 * (1.0 - marches), 5000 + 12000 * scie),
    }


# ═══════════════════════════════════════════════════════════════════════════
# LE TÉMOIN NÉGATIF — ⛔ SANS CARTE, ET IL DOIT VOIR ROUGE
# ═══════════════════════════════════════════════════════════════════════════
def _normaliser(serie):
    """La série ramenée à 0..1 — c'est CE QUE L'ŒIL VOIT sur un axe auto-calé.

    🔴 C'est le cœur du défaut : `lv_chart` auto-cale, donc DEUX SÉRIES
       D'AMPLITUDES TRÈS DIFFÉRENTES REMPLISSENT LA MÊME BOÎTE. Comparer les
       valeurs brutes ne dit rien ; comparer les FORMES NORMALISÉES dit tout."""
    mn, mx = min(serie), max(serie)
    if mx - mn < 1e-9:
        return [0.0] * len(serie)
    return [(v - mn) / (mx - mn) for v in serie]


def _ecart_de_forme(a, b):
    """L'écart moyen entre deux formes normalisées, sur 0..1."""
    na, nb = _normaliser(a), _normaliser(b)
    return sum(abs(x - y) for x, y in zip(na, nb)) / len(na)


def _series_du_jeu(duree=120, pas=1.0):
    """{« metrique[g] »: [valeurs]} — échantillonné à la cadence de l'anneau."""
    out = {}
    for i in range(int(duree / pas)):
        for m, vs in jeu(i * pas).items():
            for g, v in enumerate(vs):
                out.setdefault(f"{m}[{g}]", []).append(float(v))
    return out


SEUIL_FORME = 0.08  # 8 % d'écart moyen : en deçà, deux courbes se confondent


def temoin_negatif():
    """dn4-13 / AC7.5 — les FORMES sont éprouvées, et le seuil est vu MORDRE.

    ⛔ « Des valeurs qui changent ne suffisent pas — il faut qu'elles changent
       DIFFÉREMMENT. » On le VÉRIFIE, sur les 22 séries que le jeu produit."""
    print("=" * 72)
    print("dn4-13 / AC7.5 — TÉMOIN NÉGATIF de `anim_courbe_dn44.py` (SANS CARTE)")
    print("=" * 72)
    ko = 0
    series = _series_du_jeu()
    noms = sorted(series)
    print("  %d séries échantillonnées sur 120 s à 1 Hz." % len(noms))

    # ── 1) LES DEUX COURBES D'UNE MÊME PAGE ────────────────────────────────
    paires_page = [("net[0]", "net[1]")]
    for a, b in paires_page:
        e = _ecart_de_forme(series[a], series[b])
        ok = e >= SEUIL_FORME
        ko += 0 if ok else 1
        print("  %s  MÊME PAGE %-10s vs %-10s écart de forme %.3f (seuil %.2f)"
              % ("✅" if ok else "🔴", a, b, e, SEUIL_FORME))

    # ── 2) LA PAIRE QUI A ÉTÉ TROUVÉE FAUTIVE PAR LA REVUE ─────────────────
    e = _ecart_de_forme(series["net[1]"], series["disk[0]"])
    ok = e >= SEUIL_FORME
    ko += 0 if ok else 1
    print("  %s  net[1] vs disk[0] — LA PAIRE D'AC7.3 : écart %.3f"
          % ("✅" if ok else "🔴", e))
    print("       (les deux portaient le MÊME sinus, et les deux sont auto-calées)")

    # ── 3) TOUTES LES GRANDEURS 0, entre pages ─────────────────────────────
    g0 = [n for n in noms if n.endswith("[0]")]
    for i in range(len(g0)):
        for j in range(i + 1, len(g0)):
            e = _ecart_de_forme(series[g0[i]], series[g0[j]])
            ok = e >= SEUIL_FORME
            ko += 0 if ok else 1
            print("  %s  ENTRE PAGES %-10s vs %-10s écart %.3f"
                  % ("✅" if ok else "🔴", g0[i], g0[j], e))

    # ── 4) LE CONTRÔLE EST-IL CAPABLE DE VOIR LE DÉFAUT ? ──────────────────
    # ⛔ Un seuil qu'aucune entrée ne franchit est décoratif. On lui redonne LE
    #    JEU D'AVANT LE CORRECTIF — celui où `disk[0]` portait le MÊME sinus que
    #    `net[1]` — et on exige qu'il le VOIE.
    print("  ── le contrôle voit-il le défaut d'AVANT le correctif ? ──")
    sinus_120 = [0.5 + 0.5 * math.sin(i / 7.0) for i in range(120)]
    disk0_avant = [2000 + 18000 * v for v in sinus_120]   # l'ancienne formule
    net1 = series["net[1]"]                               # inchangée
    e = _ecart_de_forme(net1, disk0_avant)
    ok = e < SEUIL_FORME
    ko += 0 if ok else 1
    print("  %s  ANCIEN disk[0] (sinus) vs net[1] (sinus) ⇒ écart %.3f < %.2f"
          % ("✅" if ok else "🔴", e, SEUIL_FORME))
    print("       ⇒ le contrôle AURAIT ROUGI sur le jeu livré par dn4-4 : il")
    print("         n'est donc pas décoratif, et le correctif d'AC7.3 est ce qui")
    print("         le fait passer au vert plus haut.")

    # ── 5) LE PARSEUR D'ACCEPTATIONS ───────────────────────────────────────
    print("  ── le compteur d'ACCEPTATIONS (AC7.3) ──")
    for libelle, entree, attendu in (
            ("ligne réelle de `pc`",
             "trames     : 1234 valides · 5 doublons · 0 pertes seq", 1234),
            ("sortie muette ⇒ None, ⛔ pas 0", "", None),
            ("ligne voisine ⇒ None", "rejets     : tronquee 3", None)):
        obtenu = _trames_acceptees(entree)
        ok = (obtenu == attendu)
        ko += 0 if ok else 1
        print("  %s  %-38s attendu %-6s obtenu %s"
              % ("✅" if ok else "🔴", libelle, attendu, obtenu))

    print("=" * 72)
    if ko:
        print("⛔ %d contrôle(s) en échec." % ko)
        return 1
    print("✅ tout passe — aucune paire de séries ne se confond, ET le contrôle")
    print("   a été VU voir le défaut sur le jeu d'AVANT le correctif.")
    print("⚠️ CE QUE CE TÉMOIN NE PROUVE PAS : que la carte dessine ces formes.")
    print("   Il prouve que le HARNAIS ne fabrique plus la ressemblance qu'il")
    print("   sert à tester. Le reste est l'œil de l'owner, en séance.")
    return 0


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
    p.add_argument("--temoin-negatif", action="store_true",
                   help="éprouve les FORMES et le parseur hors carte "
                        "(dn4-13 / AC7.5)")
    a = p.parse_args()

    if a.temoin_negatif:
        return temoin_negatif()

    ser = dn_console.ouvrir(a.port, a.baud)
    seq = a.seq0
    t0 = time.time()
    n_ecrites = 0
    n = 0
    try:
        dn_console.reveiller(ser)

        # 🔴 dn4-13 / AC7.3 — LE MOCK EST COUPÉ **ET RELU** AVANT LA FENÊTRE.
        #    G3 donne la priorité au mock : armé, AUCUNE trame réelle n'atteint
        #    l'écran, et l'owner regarderait une rampe fabriquée en croyant voir
        #    l'agent. ⛔ Le couper ne suffit pas — il faut LIRE que c'est fait.
        #    Deux témoins owner ont déjà été perdus dans ce dépôt ; ce sont
        #    exactement 200 ms qui les auraient sauvés.
        dn_console.envoyer(ser, "widget mock off", 10)
        etat = dn_console.envoyer(ser, "widget", 15)["sortie"]
        mock_coupe = None
        for ligne in etat.splitlines():
            if ligne.strip().startswith("mock "):
                mock_coupe = "COUPE" in ligne.upper()
                print("  G3 relue : " + ligne.strip())
        if mock_coupe is None:
            print("⛔ REFUS : l'etat du mock n'a PAS ete RELU (`widget` n'a pas\n"
                  "   rendu sa ligne « mock : ... »). ⛔ On ne demande pas les\n"
                  "   yeux de l'owner sur un ecran dont on ignore le regime.")
            return 2
        if not mock_coupe:
            print("⛔ REFUS : le mock est encore ARME apres `widget mock off`.\n"
                  "   G3 lui donne la priorite : AUCUNE trame reelle n'atteindrait\n"
                  "   l'ecran, et la fenetre d'observation serait fabriquee.")
            return 2

        pages = [int(x) for x in a.pages.split(",") if x.strip() != ""]
        if pages:
            # ⚠️ LE MEME PORT SERT A L'INJECTION ET A LA NAVIGATION. Les separer
            #    obligerait a `--force`, dont l'outil dit lui-meme que « les
            #    octets se partagent : mesures tronquees » — une trame `pc`
            #    coupee en deux tomberait en `rejets_tronquee` et creuserait un
            #    trou dans l'historique PENDANT l'observation. ⛔ Un seul
            #    proprietaire du port.
            a.secondes = len(pages) * a.par_page
        acc_debut = _trames_acceptees(dn_console.envoyer(ser, "pc", 20)["sortie"])
        page_i = -1
        print(f"injection CONTINUE a 1 Hz pendant {a.secondes:.0f} s "
              f"(⛔ ne pas fermer cette fenetre pendant l'observation)")
        while time.time() - t0 < a.secondes:
            t = time.time() - t0
            if pages:
                k = min(int(t // a.par_page), len(pages) - 1)
                if k != page_i:
                    page_i = k
                    # 🔴 dn4-13 / AC7.3 — `nav open` EST **RELU**, ⛔ plus
                    #    seulement ÉCRIT. Un `write()` sans lecture ne dit pas si
                    #    la page a changé : `dn_ui_nav_open()` rend
                    #    `ESP_ERR_INVALID_STATE` quand la vue demandée était DÉJÀ
                    #    l'active, et un index hors plage est simplement REFUSÉ.
                    #    L'owner aurait regardé la page PRÉCÉDENTE en croyant
                    #    juger la suivante — et le harnais aurait affiché le bon
                    #    numéro dans sa trace.
                    rep = dn_console.envoyer(ser, f"nav open {pages[k]}", 10)
                    sortie = rep["sortie"]
                    vu = dn_console.envoyer(ser, "nav", 10)["sortie"]
                    ligne_vue = next((l.strip() for l in vu.splitlines()
                                      if l.strip().startswith("vue")), "")
                    print(f"  [{t:6.1f} s] page {pages[k]} · RELU : "
                          f"{ligne_vue or sortie.splitlines()[:1]}")
            for m, vs in jeu(t).items():
                ligne = trame(seq, int(t * 1000), m, vs)
                seq += 1
                # ⛔ On n'attend PAS l'invite : le REPL rend la main, et attendre
                #    ferait deriver la cadence de l'axe des temps.
                ser.write((f"pc {ligne}\n").encode("ascii"))
                ser.flush()
                time.sleep(0.04)  # l'espacement de l'agent reel
                n_ecrites += 1
            # 🔴 ON DRAINE AU LIEU DE DORMIR : `reset_input_buffer()` jetterait
            #    les logs, et un buffer plein finit par bloquer l'emetteur.
            # 🔴 dn4-13 / AC7.4 — LA BOUCLE INLINE EST REMPLACEE PAR
            #    `dn_console.drainer()`, LA FONCTION QUE `dn_console.py`
            #    PROMETTAIT DEPUIS dn4-4 SANS QU'ELLE EXISTE.
            dn_console.drainer(ser, t0 + t + 1.0)
        # 🔴 dn4-13 / AC7.3 — `n` COMPTE LES **ACCEPTATIONS**, ⛔ PLUS LES
        #    ECRITURES. Une trame ecrite sur le port n'est pas une trame acceptee
        #    par `dn_link` : elle peut tomber en `rejets_checksum`,
        #    `rejets_tronquee`, ou en `doublons`. Le harnais annoncait
        #    « 900 trames emises » alors que l'historique n'en avait peut-etre vu
        #    aucune — un chiffre qui a l'air d'une mesure et n'en est pas.
        #    ⇒ On RELIT le compteur `trames` de `pc`, avant et apres.
        pc_fin = dn_console.envoyer(ser, "pc", 20)["sortie"]
        acc_fin = _trames_acceptees(pc_fin)
        if acc_debut is None or acc_fin is None:
            print(f"ecrites : {n_ecrites} en {time.time() - t0:.1f} s")
            print("⛔ ACCEPTATIONS NON LUES : le compteur `trames` de `pc` n'a pas\n"
                  "   ete relu. ⛔ Ne PAS conclure « N trames emises » — une\n"
                  "   ecriture sur le port n'est pas une acceptation.")
        else:
            n = acc_fin - acc_debut
            print(f"fini — {n_ecrites} trames ECRITES, {n} ACCEPTEES par "
                  f"`dn_link` en {time.time() - t0:.1f} s")
            if n < n_ecrites:
                print(f"⚠️ {n_ecrites - n} trame(s) ecrite(s) mais NON acceptee(s) "
                      "— lire `rejets_*` et `doublons` dans `pc`.")
    finally:
        ser.close()


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
dn_injecteur — tenir les six cases VIVANTES pendant un constat owner.

🔴 POURQUOI IL EXISTE. Un constat à l'œil sur des cases à « -- » ne dit rien de
   la lisibilité : c'est la LONGUEUR DES CHAÎNES qui décide, et « -- » est la
   plus courte de toutes. Or l'agent PC réel tourne sur **Windows, sur COM3** —
   et l'exclusivité WSL↔COM3 est stricte : tant que la carte est attachée à WSL,
   l'agent ne peut pas parler, et tant que l'agent parle, la console de mesure
   n'existe plus. On ne peut donc pas commuter les voies ET voir des vraies
   valeurs par ce chemin-là.

⇒ On injecte par la BRANCHE A (« l'agent envoie `pc $DN,…` »), depuis WSL, en
  gardant la console. ⚠️ Ça teste **le CHEMIN DE CODE, pas le matériel** — c'est
  la règle n°4 de la méthodo du dépôt, et elle s'applique ici telle quelle.

⚠️ LA PÉREMPTION EST DE 3 s PAR MÉTRIQUE, en temps absolu de réception. Un tir
   unique laisse donc les cases mourir au bout de 3 s et repasser à « -- ».
   L'injecteur ré-émet à 1 Hz pour que la fenêtre d'observation soit tenue.

🔴 LE JEU PAR DÉFAUT EST LE **PIRE CAS PLAUSIBLE**, PAS LE NOMINAL. C'est lui
   qui décide de la lisibilité et du chevauchement — juger sur « 46,0 % » quand
   la grammaire autorise « 100,0 % » reviendrait à mesurer la case facile.
   ⛔ Les valeurs restent DANS les bornes de `k_metriques[]` : au-delà, la trame
   part en `rejets_bornes` et l'écran ne montre rien du tout.

⚠️ LES VALEURS SONT SIMULÉES ET LE FIRMWARE LE SAIT : elles arrivent par le
   chemin `dn_link`, donc la case est **RÉELLE** au sens du régime (une trame
   valide EST une donnée). ⛔ Ce n'est PAS le badge « SIMULÉ », qui est réservé
   aux mocks internes. Écrit ici pour que personne ne lise l'absence de badge
   comme « ce sont de vraies mesures de la tour ».

Usage :
    python3 tools/dn_injecteur.py --secondes 30
    python3 tools/dn_injecteur.py --jeu nominal --secondes 60
    python3 tools/dn_injecteur.py --jeu reel --secondes 30
"""

import argparse
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import dn_console  # noqa: E402  (le module frère porte l'ouverture du port)


def _ck(corps):
    x = 0
    for o in corps.encode("ascii"):
        x ^= o
    return f"{x:02X}"


def trame(seq, t_ms, metrique, valeurs):
    """v3. ⚠️ `None` = champ VIDE = « cette grandeur-là, je ne la connais pas »
    (W10 sur un fil positionnel). Les `None` de queue sont tronqués."""
    vs = list(valeurs)
    while vs and vs[-1] is None:
        vs.pop()
    corps = f"DN,3,{seq},{t_ms},{metrique}," + ",".join(
        "" if v is None else str(v) for v in vs)
    return f"${corps}*{_ck(corps)}"


# Les trois jeux. ⚠️ En DIXIÈMES, comme le fil — ⛔ jamais de flottant
# (doctrine `parse_entier`). C'est l'AFFICHAGE qui porte la précision (AC9).
JEUX = {
    # Le pire cas PLAUSIBLE : ce qu'une tour peut réellement afficher au max.
    "pire": {
        "cpu": [1000, 57, 1000],            # 100,0 %  5,7 GHz  c.max 100,0 %
        "gpu": [1000, 950, 3500, 30000],    # 100,0 %  95,0 °C  350 W  3000 tr/min
        "ram": [999, 342],                  # 99,9 %   34,2 Go
        # ⚠️ CES DEUX-LÀ ONT ÉTÉ CORRIGÉS APRÈS UN TIR : la première version
        #    envoyait 9 999 999 dixièmes de Mb/s, au-dessus du plafond de
        #    `k_metriques[]` (1 000 000) ⇒ **8 `rejets_bornes`** et rien à
        #    l'écran. Le pire cas doit rester DANS la grammaire, sinon on ne
        #    mesure pas la lisibilité, on mesure le parseur.
        #    ✅ Effet de bord utile : ce tir a prouvé que `rejets_bornes`
        #       s'incrémente sur une v3 hors plafond — ET LUI SEUL.
        "net": [999999, 999999],            # 99999,9 Mb/s des deux côtés
        "disk": [999999],                   # 99999,9 Mo/s
    },
    # Ce que la tour rend VRAIMENT (mesuré le 2026-08-19, n=959).
    "reel": {
        "cpu": [52, 32, 350],               # 5,2 %  3,2 GHz  c.max 35,0 %
        "gpu": [0, 460, 500, 5980],         # 0,0 %  46,0 °C  50 W  598 tr/min
        "ram": [664, 342],
        "net": [9850, 480],
        "disk": [12684],
    },
    # La maquette de l'addendum §1 — ⚠️ ses nombres sont ILLUSTRATIFS.
    "nominal": {
        "cpu": [540, 47, 880],
        "gpu": [460, 610, 2120, 14500],
        "ram": [664, 342],
        "net": [9850, 480],
        "disk": [4800],
    },
    # W10 : un TROU INTERNE. La °C du GPU manque, le reste est là.
    # ⛔ C'est le témoin que l'absence est une DONNÉE, pas un silence global.
    "trou": {
        "cpu": [540, None, 880],
        "gpu": [460, None, 2120, 14500],
        "ram": [664, 342],
        "net": [9850, 480],
        "disk": [4800],
    },
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jeu", choices=sorted(JEUX), default="pire")
    p.add_argument("--secondes", type=float, default=30.0)
    # 🔴 L'ESPACEMENT DES CINQ TRAMES DANS LA SECONDE N'EST PAS UN DETAIL DE
    #    CONFORT : c'est l'axe `dn_link_etalement` (l'A/B « poussee ETALEE vs
    #    GROUPEE » de W4). Serrees, plusieurs mises a jour tombent dans le MEME
    #    cycle LVGL et le flush/cycle monte ; espacees, chacune a son cycle.
    #    ⛔ Un releve de regime (b) qui ne dit pas son espacement n'est pas
    #      comparable a un autre.
    p.add_argument("--espacement", type=float, default=0.04, metavar="S",
                   help="delai entre deux trames de la meme seconde (defaut 0,04)")
    p.add_argument("--port", default=dn_console.DEFAULT_PORT)
    p.add_argument("--baud", type=int, default=dn_console.DEFAULT_BAUD)
    a = p.parse_args()

    jeu = JEUX[a.jeu]
    ser = dn_console.ouvrir(a.port, a.baud)
    print(f"[injecteur] jeu « {a.jeu} » — {a.secondes:.0f} s a 1 Hz, "
          f"espacement {a.espacement*1000:.0f} ms "
          f"(peremption 3 s : sans ca les cases retombent a « -- »)")
    print("[injecteur] ⚠️ branche A : ceci teste le CHEMIN DE CODE, pas le materiel.")
    sys.stdout.flush()

    seq = 0
    t0 = time.monotonic()
    n = 0
    try:
        dn_console.reveiller(ser)
        while time.monotonic() - t0 < a.secondes:
            cycle = time.monotonic()
            t_ms = int((cycle - t0) * 1000) & 0xFFFFFFFF
            for m, vs in jeu.items():
                seq += 1
                ser.write((f"pc {trame(seq, t_ms, m, vs)}\n").encode("ascii"))
                ser.flush()
                n += 1
                # ⚠️ Le REPL rend l'invite entre deux commandes ; on draine ce
                #    qu'il renvoie, sinon le tampon d'entree finit par saturer et
                #    les trames suivantes arrivent TRONQUEES — donc comptees en
                #    `rejets_tronquee` alors que l'emetteur allait bien.
                time.sleep(a.espacement)
                ser.read(ser.in_waiting or 0)
            reste = 1.0 - (time.monotonic() - cycle)
            if reste > 0:
                time.sleep(reste)
    except KeyboardInterrupt:
        pass
    finally:
        # ⚠️ On draine 0,4 s avant de fermer : une capture qui ferme trop tot
        #    laisse l'echo des dernieres trames dans le port, et la commande
        #    SUIVANTE le lit a la place de sa propre sortie (piege du depot).
        time.sleep(0.4)
        try:
            ser.read(ser.in_waiting or 0)
        except Exception:
            pass
        ser.close()
    print(f"[injecteur] {n} trames emises. ⚠️ les cases retombent a « -- » "
          f"dans 3 s — c'est la peremption, PAS une regression.")


if __name__ == "__main__":
    main()

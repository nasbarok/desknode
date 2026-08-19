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


def trame(seq, t_ms, metrique, valeurs, version=3):
    """v3. ⚠️ `None` = champ VIDE = « cette grandeur-là, je ne la connais pas »
    (W10 sur un fil positionnel). Les `None` de queue sont tronqués."""
    vs = list(valeurs)
    while vs and vs[-1] is None:
        vs.pop()
    if version <= 2:
        # v1 ne connaît que `cpu` et 6 champs ; v2 plafonne à deux valeurs.
        vs = vs[:1] if version == 1 else vs[:2]
    corps = f"DN,{version},{seq},{t_ms},{metrique}," + ",".join(
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
    # 🔴 CE JEU A MENTI, ET IL A FAIT TIRER UNE CONCLUSION FAUSSE À L'OWNER.
    #    Il était étiqueté « ce que la tour rend VRAIMENT (mesuré, n=959) » alors
    #    que SEULS `cpu` et `gpu` venaient de la mesure : `net`, `ram` et `disk`
    #    avaient été RECOPIÉS de la maquette illustrative de l'addendum §1.
    #    ⚠️ Résultat : l'écran affichait « ↓ 985,0 Mb/s ↑ 48,0 Mb/s » sous une
    #       étiquette « réel », et l'owner a demandé, en séance, *« je suis
    #       étonné que mon PC dl et upload autant, qu'est-ce qu'il fait ? »*.
    #       La tour était en fait à **0,0 Mb/s dans les deux sens** (vérifié par
    #       `psutil.net_io_counters()` sur 5 s, le 2026-08-19).
    # ⛔ C'EST EXACTEMENT LE MENSONGE D'INTERFACE QUE CE DÉPÔT TRAQUE, commis par
    #    l'INSTRUMENT au lieu du produit — et c'est pire, parce qu'un instrument
    #    est là pour être cru.
    # ⇒ RÈGLE : chaque nombre de ce jeu porte SA provenance et SA date. Un
    #   nombre sans provenance n'a rien à faire dans un jeu nommé « reel ».
    "reel": {
        # MESURÉS le 2026-08-19, session de 959 échantillons / 16 min :
        "cpu": [52, 32, 350],               # 5,2 %   3,2 GHz   c.max 35,0 %
        "gpu": [0, 460, 500, 5980],         # 0,0 %   46,0 °C   50 W   598 tr/min
        # MESURÉS le 2026-08-19 par un tir psutil de 5 s sur la tour :
        "ram": [489, 319],                  # 48,9 %  31,9 Gio (⚠️ Windows écrit « Go »)
        "net": [0, 0],                      # 0,0 Mb/s dans LES DEUX SENS — la tour
                                            # ne faisait RIEN sur le réseau
        "disk": [2],                        # 0,2 Mo/s
    },
    # La maquette de l'addendum §1 — 🔴 SES NOMBRES SONT ILLUSTRATIFS, ET C'EST
    # D'ICI QUE `net` ET `disk` AVAIENT ÉTÉ RECOPIÉS DANS « reel » PAR ERREUR.
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
    # 🔴 LE DISCRIMINATEUR DU TRESSAUTEMENT (constat owner, 2026-08-19).
    #    Émet EXACTEMENT le même trafic série, au même rythme, avec le même
    #    travail de REPL et de parseur — mais un CHECKSUM VOLONTAIREMENT FAUX,
    #    donc **AUCUNE mise à jour d'affichage**.
    #    · ça tressaute quand même ⇒ la cause est le TRAFIC (USB / console /
    #      contention de verrou), ⛔ pas le dessin ;
    #    · ça ne tressaute plus  ⇒ la cause est le DESSIN SOUS TRAFIC.
    #    ⚠️ Une seule variable change entre les deux tirs. C'est tout l'intérêt.
    # 🔴 POUR L'A/B CONTRE LE FIRMWARE DE dn4-1 (`cfd1a54`), qui ne connaît que
    #    v1 et v2. Sans ça, toutes les trames partiraient en `rejets_version` et
    #    l'A/B mesurerait DEUX firmwares sous DEUX stimuli différents — c'est-à-
    #    dire rien du tout.
    # ⚠️ En v2 le protocole plafonne à DEUX valeurs : les grandeurs 3 et 4 sont
    #    tronquées. ⛔ Le FLUSH, lui, ne change pas : le groupage invalide LE
    #    CONTENEUR, donc une case repeint la même surface quel que soit le
    #    nombre de labels réécrits. C'est ce qui rend l'A/B honnête.
    p.add_argument("--version", type=int, choices=(1, 2, 3), default=3,
                   help="version de protocole emise (2 pour le firmware dn4-1)")
    p.add_argument("--checksum-faux", action="store_true",
                   help="emet le meme trafic mais SANS aucune mise a jour "
                        "d'affichage (les trames partent en rejets_checksum)")
    p.add_argument("--secondes", type=float, default=30.0)
    # 🔴 L'ESPACEMENT DES CINQ TRAMES DANS LA SECONDE N'EST PAS UN DETAIL DE
    #    CONFORT : c'est l'axe `dn_link_etalement` (l'A/B « poussee ETALEE vs
    #    GROUPEE » de W4). Serrees, plusieurs mises a jour tombent dans le MEME
    #    cycle LVGL et le flush/cycle monte ; espacees, chacune a son cycle.
    #    ⛔ Un releve de regime (b) qui ne dit pas son espacement n'est pas
    #      comparable a un autre.
    p.add_argument("--espacement", type=float, default=0.04, metavar="S",
                   help="delai entre deux trames de la meme seconde (defaut 0,04)")
    # ⚠️ BORNE VERIFIEE AVANT D'OUVRIR LE PORT (revue 2026-08-19) : `time.sleep()`
    #    leve `ValueError` sur un negatif, et il le levait EN PLEIN TIR, port
    #    ouvert — la campagne etait perdue apres avoir consomme sa fenetre.
    #    Une seconde entiere entre deux trames n'a pas de sens non plus : les cinq
    #    ne tiendraient plus dans le cycle de 1 Hz.
    p.add_argument("--port", default=dn_console.DEFAULT_PORT)
    p.add_argument("--baud", type=int, default=dn_console.DEFAULT_BAUD)
    a = p.parse_args()
    if not (0.0 <= a.espacement <= 0.2):
        p.error(f"--espacement {a.espacement} hors de [0 ; 0,2] s : cinq trames "
                f"doivent tenir dans le cycle de 1 Hz, et time.sleep() leverait "
                f"sur un negatif EN PLEIN TIR.")

    jeu = JEUX[a.jeu]
    ser = dn_console.ouvrir(a.port, a.baud)
    if a.checksum_faux:
        print("[injecteur] ⚠️ CHECKSUM FAUX : meme trafic, AUCUNE mise a jour "
              "d'affichage.")
    print(f"[injecteur] protocole v{a.version}")
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
                # 🔴 `seq` N'EST CONSOMME QUE PAR UNE TRAME REELLEMENT EMISE —
                #    CORRECTIF DE REVUE DU 2026-08-19. Il etait incremente AVANT
                #    le `continue` : en v1, une seule metrique sur cinq part, donc
                #    le firmware voyait seq 1, 6, 11... et comptait
                #    `pertes_seq += saut - 1` = QUATRE pertes par cycle
                #    (`dn_link.c`, la branche `saut > 1`).
                # ⛔ Et la v1 est LE TEMOIN DE NON-REGRESSION d'AC7/AC13 :
                #    l'instrument fabriquait des pertes sur la garde meme qu'il
                #    doit valider. Un compteur pollue par l'emetteur ne prouve
                #    rien sur le recepteur.
                if a.version == 1 and m != "cpu":
                    continue  # v1 ne connaît QUE `cpu` — le reste serait rejeté
                seq += 1
                tr = trame(seq, t_ms, m, vs, a.version)
                if a.checksum_faux:
                    # ⛔ On casse le checksum, ⛔ PAS la grammaire : la trame doit
                    #    traverser TOUT le parseur (decoupage, version, metrique)
                    #    et ne tomber qu'a la toute derniere garde. Sinon on ne
                    #    mesurerait pas le meme travail.
                    tr = tr[:-2] + ("00" if not tr.endswith("00") else "11")
                ser.write((f"pc {tr}\n").encode("ascii"))
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

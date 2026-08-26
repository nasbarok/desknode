#!/usr/bin/env python3
"""
DeskNode — TÉMOIN DE DÉCOUPE du lecteur d'horloge.          (dn4-18, 2026-08-26)

🔴 CE QU'IL PROUVE, ET POURQUOI IL EXISTE
=========================================
AC3.5 pose un invariant et exige qu'il soit TESTÉ, pas affirmé :

    « aucun marqueur n'est compté deux fois, et aucun n'est perdu,
      QUELLE QUE SOIT LA POSITION DE LA COUPURE. »

Le fil est lu par `SortieSerie._drainer()`, qui est appelé à chaque envoi de
trame — soit ~5 fois par seconde. Une frontière de `read()` tombant au milieu
d'une ligne est donc BANALE, pas exceptionnelle : le dépôt a déjà payé ce
défaut une fois (`refus_firmware` SOUS-COMPTÉ tant que `count()` portait sur un
seul `read()` sans report, revue du 2026-08-19).

⛔ TROIS POSITIONS CHOISIES À LA MAIN NE PROUVENT RIEN. Ce témoin rejoue un flux
   de référence coupé à **CHAQUE position possible**, puis **octet par octet**,
   puis en coupures multiples tirées au sort, et compare l'empreinte complète à
   celle du flux entier.

🔴 ET IL APPELLE LE VRAI CODE
=============================
⛔ « un harnais qui REJOUE au lieu d'appeler la fonction est décoratif ». Ce
   témoin instancie le VRAI `SortieSerie`, lui donne un port de papier, et
   appelle le VRAI `_drainer()`. Le lecteur d'état est le VRAI
   `LecteurHorloge` — la sous-classe ci-dessous ne fait qu'AJOUTER un journal
   par-dessus des `super()`, elle ne réimplémente aucune décision.

🔴 LE FLUX DE RÉFÉRENCE EST FAIT D'OCTETS RÉELS
===============================================
`mesures/dn4-18/reference-flux.bin` est assemblé de captures de séance :
bandeau de boot et régime (phases A et B du 2026-08-26), réponses de `rtc` et
`rtc set` prises CÔTÉ TOUR, et un vrai `Command returned non-zero error code`
repris de la validation de `dn4-13`. ⛔ Aucun octet inventé.
⚠️ Il porte AUSSI le piège mesuré : la ligne `… N'EST PAS FIABLE …`, qui dit le
   CONTRAIRE de ce qu'un `in` naïf y lirait.

USAGE
=====
    python3 tools/verif_decoupe_horloge_dn418.py
    python3 tools/verif_decoupe_horloge_dn418.py --montrer-l-echec

⛔ `--montrer-l-echec` EST OBLIGATOIRE AVANT DE CROIRE LE VERT : « une gate
   jamais vue CRIER n'est pas une gate ». Il casse volontairement la borne du
   tampon de lignes et montre le témoin qui HURLE.

Code de retour : 0 si l'invariant tient, 1 sinon.
"""

import os
import random
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "agent"))
# ⚠️ `dn_agent` importe psutil, qui n'existe pas en WSL. Le stub du dépôt le
#    remplace — il CRIE qu'il est un stub, et ici ça n'a aucune importance :
#    ce témoin ne lit AUCUNE métrique, il ne touche que le fil.
os.environ.setdefault("DN_STUB_PSUTIL", "1")
sys.path.insert(0, os.path.join(RACINE, "tools", "stub_psutil"))

import dn_agent  # noqa: E402

REFERENCE = os.path.join(RACINE, "mesures", "dn4-18", "reference-flux.bin")


class PortDePapier:
    """Un port série qui rend un flux par MORCEAUX IMPOSÉS.

    ⚠️ Il reproduit EXACTEMENT le contrat que `_drainer()` utilise :
       `in_waiting` puis `read(n)`. ⛔ Rien de plus : ce n'est pas un simulateur
       de carte, c'est une découpeuse.
    """

    def __init__(self, morceaux):
        self._m = [m for m in morceaux if m]

    @property
    def in_waiting(self):
        return len(self._m[0]) if self._m else 0

    def read(self, n):
        if not self._m or n <= 0:
            return b""
        return self._m.pop(0)

    def close(self):
        pass


class LecteurJournalise(dn_agent.LecteurHorloge):
    """Le VRAI lecteur, plus un journal. ⛔ Aucune décision n'est réécrite ici :
    chaque méthode appelle `super()` et se contente d'observer ce qui a changé."""

    def __init__(self):
        super().__init__()
        self.journal = []

    def _poser_etat(self, brut):
        avant = (self.etat, self.etat_texte, self.etats_lus)
        super()._poser_etat(brut)
        if (self.etat, self.etat_texte, self.etats_lus) != avant:
            self.journal.append(("etat", self.etat, self.etat_texte))

    def _heure_depuis(self, ligne):
        avant = self.lue_texte
        super()._heure_depuis(ligne)
        if self.lue_texte != avant:
            # ⛔ On ne journalise PAS `lue_ecart_s` : il dépend de l'horloge de
            #    l'hôte AU MOMENT DE LA LECTURE, donc il varie d'un tir à
            #    l'autre. Un témoin qui comparerait ça crierait au faux.
            self.journal.append(("lue", self.lue_texte, self.lue_naif))

    def _verdict_depuis(self, ligne):
        avant = self.verdict
        super()._verdict_depuis(ligne)
        if self.verdict != avant and self.verdict is not None:
            self.journal.append(("verdict", self.verdict[0]))


def rejouer(morceaux):
    """Rejoue un flux découpé À TRAVERS LE VRAI CHEMIN, et rend son empreinte."""
    s = dn_agent.SortieSerie("PORT_DE_PAPIER")     # ⛔ n'ouvre rien
    s.horloge = LecteurJournalise()
    s._con = PortDePapier(morceaux)
    while s._con.in_waiting:
        s._drainer()
    lect = s.horloge
    return {
        "refus_firmware": s.refus_firmware,
        "echo_octets": s.echo_octets,
        "echo_lignes": s.echo_lignes,
        "lignes_vues": lect.lignes_vues,
        "lignes_tronquees": lect.lignes_tronquees,
        "etat": lect.etat,
        "etat_texte": lect.etat_texte,
        "etats_lus": lect.etats_lus,
        "lue_texte": lect.lue_texte,
        "lue_naif": lect.lue_naif,
        "journal": tuple(lect.journal),
    }


def _ecart(a, b):
    return [k for k in a if a[k] != b[k]]


def temoin_decoupe(flux, arret_au_premier=False):
    """AC3.5 — l'invariant, éprouvé à CHAQUE position de coupure.

    `arret_au_premier` ne sert qu'à `--montrer-l-echec` : on veut voir le témoin
    CRIER vite, pas attendre qu'il ait recompté 10 000 divergences.
    """
    ok = True
    ref = rejouer([flux])
    print("  flux de reference : %d o | %d lignes | refus_firmware=%d | "
          "etats_lus=%d | etat final « %s »"
          % (len(flux), ref["lignes_vues"], ref["refus_firmware"],
             ref["etats_lus"], ref["etat"]))
    print("  journal de reference : %d evenement(s)" % len(ref["journal"]))
    for e in ref["journal"]:
        print("      %s" % (e,))

    # ⛔ Une référence vide validerait n'importe quoi. On EXIGE que le flux porte
    #    de quoi être discriminant.
    exige = {"refus_firmware": 2, "etats_lus": 4}
    for k, mini in exige.items():
        if ref[k] < mini:
            print("  /!\\ FLUX DE REFERENCE NON DISCRIMINANT : %s=%d < %d attendu."
                  % (k, ref[k], mini))
            print("      ⛔ Un temoin qui passe sur un flux vide ne prouve RIEN.")
            return False

    # 1/3 — TOUTES les coupures simples.
    mauvaises = []
    for k in range(1, len(flux)):
        if rejouer([flux[:k], flux[k:]]) != ref:
            mauvaises.append(k)
            if arret_au_premier:
                break
    if mauvaises:
        ok = False
        print("  🔴 COUPURE SIMPLE : %d position(s) sur %d divergent — ex. %s"
              % (len(mauvaises), len(flux) - 1, mauvaises[:8]))
        print("      ecart a la 1re : %s"
              % _ecart(rejouer([flux[:mauvaises[0]], flux[mauvaises[0]:]]), ref))
    else:
        print("  ✅ COUPURE SIMPLE : %d positions, TOUTES identiques au flux entier"
              % (len(flux) - 1))

    # 2/3 — le pire cas absolu : un octet par `read()`.
    octet = rejouer([flux[i:i + 1] for i in range(len(flux))])
    if octet != ref:
        ok = False
        print("  🔴 OCTET PAR OCTET : divergent — %s" % _ecart(octet, ref))
    else:
        print("  ✅ OCTET PAR OCTET : identique (%d read() d'un octet)" % len(flux))

    # 3/3 — coupures MULTIPLES, tirées au sort mais REPRODUCTIBLES.
    alea = random.Random(418)
    rates = 0
    for _ in range(200):
        n = alea.randint(2, 40)
        pts = sorted(alea.sample(range(1, len(flux)), n))
        bouts, prec = [], 0
        for p in pts:
            bouts.append(flux[prec:p])
            prec = p
        bouts.append(flux[prec:])
        if rejouer(bouts) != ref:
            rates += 1
    if rates:
        ok = False
        print("  🔴 COUPURES MULTIPLES : %d tirage(s) sur 200 divergent" % rates)
    else:
        print("  ✅ COUPURES MULTIPLES : 200 tirages (graine 418), tous identiques")
    return ok


def temoin_auto_declenchement():
    """AC3.4 — LE MARQUEUR NE DOIT PAS POUVOIR S'AUTO-DÉCLENCHER.

    `_drainer()` ramasse AUSSI l'écho des lignes que l'agent vient d'écrire. Si
    le texte cherché pouvait apparaître dans ce que l'agent émet, l'agent se
    répondrait à lui-même. ⇒ on lui donne à manger EXACTEMENT ce qu'il écrit —
    ses trames construites par le VRAI `trame()`, et ses deux commandes console
    — et on exige que RIEN ne bouge.
    """
    lignes = []
    for i, (metrique, valeurs) in enumerate([
            ("cpu", [118, 32, 250, 433]), ("gpu", [50, 470, 510, 5950]),
            ("ram", [487, 319]), ("net", [0, 0]), ("disk", [6, 10573, 3583, 9136])]):
        lignes.append(b"pc " + dn_agent.trame(i + 1, 1032, metrique,
                                              valeurs).encode("ascii"))
    # Les DEUX commandes console que ce mécanisme émet, et leur écho de REPL.
    lignes.append(b"rtc\r\n")
    lignes.append(b"rtc set 2026-08-26 13:47:32\r\n")
    lignes.append(b"desknode> rtc set 2026-03-29 03:00:00\r\n")
    lignes.append(b"desknode> ")
    flux = b"".join(lignes)
    r = rejouer([flux])
    ok = (r["refus_firmware"] == 0 and r["etats_lus"] == 0
          and r["etat"] == "INCONNU" and r["lue_texte"] is None
          and r["journal"] == ())
    if ok:
        print("  ✅ AUTO-DECLENCHEMENT : %d o de ce que l'AGENT emet ⇒ 0 etat, "
              "0 heure, 0 refus, etat reste INCONNU" % len(flux))
    else:
        print("  🔴 AUTO-DECLENCHEMENT : l'agent se repond a lui-meme ! %s"
              % {k: r[k] for k in ("refus_firmware", "etats_lus", "etat",
                                   "lue_texte", "journal")})
    return ok


def temoin_piege_fiable(flux):
    """Le piège MESURÉ : « N'EST PAS FIABLE » ne doit JAMAIS se lire `FIABLE`."""
    # ⛔ LA LIGNE-PIÈGE EST EXTRAITE DU FLUX RÉEL, ⛔ pas retapée ici : une
    #    copie à la main dériverait du firmware sans que rien ne le dise —
    #    exactement le défaut que la gate miroir existe pour attraper.
    i = flux.find(b"N'EST PAS FIABLE")
    if i < 0:
        print("  /!\\ le flux de reference ne porte PAS la ligne-piege : "
              "ce temoin ne prouverait rien.")
        return False
    d = flux.rfind(b"\n", 0, i) + 1
    f = flux.find(b"\n", i)
    piege = flux[d:f + 1 if f >= 0 else len(flux)]
    print("  ligne-piege extraite du flux : %r"
          % piege.decode("utf-8", "replace").strip()[:88])
    r = rejouer([piege])
    ok = (r["etats_lus"] == 0 and r["etat"] == "INCONNU")
    print("  %s PIEGE « N'EST PAS FIABLE » : etats_lus=%d, etat « %s » "
          "(attendu 0 / INCONNU)"
          % ("✅" if ok else "🔴", r["etats_lus"], r["etat"]))
    # Et la variante sous-mot : `FIABLE` est contenu dans `NON FIABLE (OS=1)`.
    r2 = rejouer([b"horloge PCF85063A @ 0x51 : NON FIABLE (OS=1)\r\n"])
    ok2 = (r2["etat"] == "OS1")
    print("  %s SOUS-MOT `FIABLE` dans `NON FIABLE (OS=1)` : lu « %s » "
          "(attendu OS1)" % ("✅" if ok2 else "🔴", r2["etat"]))
    return ok and ok2


def main():
    montrer = "--montrer-l-echec" in sys.argv[1:]
    if not os.path.exists(REFERENCE):
        print("ECHEC : %s absent." % REFERENCE)
        return 1
    flux = open(REFERENCE, "rb").read()

    if montrer:
        print("=== ⛔ ECHEC PROVOQUE — on casse la borne du tampon de lignes ===")
        print("    DN_H_LIGNE_MAX : %d -> 8" % dn_agent.DN_H_LIGNE_MAX)
        print("    (une ligne tronquee perd son etat, et la perte DEPEND de la")
        print("     position de la coupure : l'invariant DOIT tomber)")
        dn_agent.DN_H_LIGNE_MAX = 8
        # ⛔ SUR LE FLUX ENTIER, ⛔ pas sur une tranche : une tranche qui aurait
        #    perdu les marqueurs ferait crier la GARDE DE DISCRIMINANCE au lieu
        #    de l'INVARIANT — un echec decoratif, qui ne prouverait pas que le
        #    temoin sait detecter une VRAIE rupture.
        ok = temoin_decoupe(flux, arret_au_premier=True)
        print()
        if ok:
            print("🔴 LE TEMOIN N'A PAS CRIE ALORS QU'ON A CASSE LE CODE.")
            print("   ⛔ Un temoin qui ne peut pas echouer ne prouve rien.")
            return 1
        print("✅ LE TEMOIN A CRIE. Il peut donc etre cru quand il est vert.")
        return 0

    print("=== TEMOIN DE DECOUPE — lecteur d'horloge (dn4-18) ===")
    print()
    print("[1/3] AC3.5 — l'invariant de decoupe")
    a = temoin_decoupe(flux)
    print()
    print("[2/3] AC3.4 — l'agent ne peut pas se repondre a lui-meme")
    b = temoin_auto_declenchement()
    print()
    print("[3/3] Les deux pieges MESURES sur le flux reel")
    c = temoin_piege_fiable(flux)
    print()
    if a and b and c:
        print("✅ TOUT TIENT.")
        return 0
    print("🔴 AU MOINS UN TEMOIN A ECHOUE.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

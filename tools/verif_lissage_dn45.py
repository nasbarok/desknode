#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-5 / T4 — LE LISSAGE NE SURVIT PAS A LA PEREMPTION, ET IL NE TOUCHE QUE CE
QU'IL DOIT TOUCHER.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

⛔ IL NE REJOUE RIEN : il IMPORTE `dn_agent.Lisseur` et l'APPELLE. Et il le
   nourrit avec **LA CAPTURE REELLE DES 960 ECHANTILLONS**, ⛔ pas avec des
   valeurs fabriquees — l'injecteur de ce depot a deja menti d'un facteur 108
   pour avoir emis des valeurs FIXES.

🔴 LES QUATRE PROPRIETES QUI COMPTENT :

  1. **LE JEU LISSE EST EXACTEMENT CELUI QUI A ETE VERDICTE.** Quatre grandeurs,
     ⛔ pas cinq : `CPU %` est « A DISCUTER » depuis §13.7 et AC4.4 le tranche A
     L'OEIL. Le lisser en douce serait trancher a la place de l'owner.

  2. **LA FENETRE EST BORNEE PAR AC4.3, ET LA BORNE EST RELUE DANS LE FIRMWARE.**
     `n - 1 < DN_LINK_PEREMPTION_US`. ⛔ Le 3 s n'est pas recopie ici : il est
     `grep`e dans `dn_link.h`. Si quelqu'un change la peremption, cette gate
     rougit.

  3. **LA FENETRE SE VIDE A LA REPRISE.** C'est LE piege nomme par AC4.3 : « un
     IIR qui garde son etat re-affiche une valeur d'AVANT la coupure des la
     premiere trame de reprise ». Le mutant le montre.

  4. **ON MOYENNE A LA RESOLUTION AFFICHEE.** Les quatre grandeurs lissees sont
     toutes `DN_PREC_DIXIEME` — VERIFIE dans `dn_ui.c`, ⛔ pas suppose. Une
     grandeur `DN_PREC_ENTIER` dans le lot exigerait un autre arrondi, et la
     moyenne en dixiemes fabriquerait des chiffres que l'ecran n'affiche pas.

⚠️ CE QUE CETTE GATE NE PROUVE PAS : que l'ecran est plus agreable. C'est AC4.4,
   et ca se tranche A L'OEIL, sur la carte.

Sortie : exit 0 si tout passe, 1 sinon.
"""

import csv
import io
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(RACINE, "firmware", "desknode", "main")
CAPTURE = os.path.join(RACINE, "mesures", "dn4-5", "T3-AC4.1-lissage-960.csv")

sys.path.insert(0, os.path.join(RACINE, "agent"))
os.environ.setdefault("DN_STUB_PSUTIL", "1")
sys.path.insert(0, os.path.join(RACINE, "tools", "stub_psutil"))

import dn_agent  # noqa: E402

ok_total = [0]
ko_total = [0]

# Les quatre verdictees LISSER (decision owner du 2026-08-26, reponse (a)).
ATTENDU = {("cpu", 1), ("net", 0), ("net", 1), ("disk", 0)}
# ⛔ Celle qu'on ne doit PAS lisser sans l'owner.
INTERDITE = ("cpu", 0)


def ctrl(ok, libelle, detail=""):
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-56s %s" % (libelle, detail))
    else:
        ko_total[0] += 1
        print("  [KO ] %-56s %s" % (libelle, detail))
    return ok


def peremption_us():
    """⛔ RELUE DANS LE FIRMWARE, jamais recopiee."""
    txt = io.open(os.path.join(MAIN, "dn_link.h"), encoding="utf-8").read()
    m = re.search(r'#define\s+DN_LINK_PEREMPTION_US\s+(\d+)', txt)
    return int(m.group(1)) if m else None


def precisions():
    """Les `.prec` de `k_desc[]`, relues dans dn_ui.c — meme parseur d'esprit
    que `mesure_lissage_dn45.py`."""
    txt = io.open(os.path.join(MAIN, "dn_ui.c"), encoding="utf-8").read()
    d = txt.index("static const dn_widget_desc_t k_desc[DN_UI_METRIQUES] = {")
    corps = txt[d:txt.index("\n};", d)]
    noms = [("cpu", "DN_UI_CASE_CPU"), ("gpu", "DN_UI_CASE_GPU"),
            ("ram", "DN_UI_CASE_RAM"), ("net", "DN_UI_CASE_RESEAU"),
            ("disk", "DN_UI_CASE_DISQUE")]
    pos = {c: corps.index("[" + c + "] = {") for _, c in noms
           if ("[" + c + "] = {") in corps}
    out = {}
    for nom, cle in noms:
        deb = pos[cle]
        suiv = [p for p in pos.values() if p > deb]
        bloc = corps[deb:min(suiv) if suiv else len(corps)]
        g = re.search(r'\.grandeurs = \{(.*?)\}\},', bloc, re.S)
        out[nom] = re.findall(r'\.prec = (DN_PREC_\w+)', g.group(1)) if g else []
    # La 16e (RAM Go totaux) est une DONNEE SECONDAIRE, formatee par
    # `fmt_dixiemes()` — voir `mesure_lissage_dn45.py`.
    out["ram"].append("DN_PREC_DIXIEME")
    return out


def capture():
    """La vraie capture, en DIXIEMES ENTIERS (ce que le fil porte)."""
    cols = None
    series = {}
    with io.open(CAPTURE, encoding="utf-8") as f:
        for L in csv.DictReader(f):
            if cols is None:
                cols = [c for c in L if c != "t"]
            for c in cols:
                m, i = c.rsplit(".", 1)
                v = L[c]
                series.setdefault((m, int(i)), []).append(
                    None if v == "" else int(round(float(v) * 10)))
    return series


def rejouer(lis, series, generation=0, coupure_a=None):
    """Fait passer la capture dans le lisseur, photo par photo, EXACTEMENT comme
    la boucle d'emission de l'agent."""
    n = len(next(iter(series.values())))
    sortie = {k: [] for k in series}
    gen = generation
    for t in range(n):
        if coupure_a is not None and t == coupure_a:
            gen += 1          # le port s'est rouvert : nouvelle generation
        photo = []
        for met in ("cpu", "gpu", "ram", "net", "disk"):
            vals = [series[(met, i)][t] for i in range(16)
                    if (met, i) in series]
            photo.append((met, vals))
        for met, vals in lis.appliquer(photo, gen):
            for i, v in enumerate(vals):
                sortie[(met, i)].append(v)
    return sortie


def p95(serie):
    s = sorted(abs(b - a) for a, b in zip(serie, serie[1:])
               if a is not None and b is not None)
    return s[min(len(s) - 1, int(0.95 * len(s)))] if s else None


def main():
    print("=" * 78)
    print("dn4-5 / T4 — LE LISSAGE D'AFFICHAGE")
    print("=" * 78)

    print("\n── 1. LE JEU LISSE EST CELUI QUI A ETE VERDICTE ──────────────────")
    L = dn_agent.Lisseur
    ctrl(set(L.LISSEES) == ATTENDU, "exactement les 4 grandeurs verdictees LISSER",
         "⛔ %s" % sorted(set(L.LISSEES) ^ ATTENDU)
         if set(L.LISSEES) != ATTENDU else sorted(L.LISSEES))
    ctrl(INTERDITE not in L.LISSEES,
         "⛔ `CPU %` n'est PAS lisse", "« A DISCUTER » depuis §13.7 ⇒ AC4.4, A L'OEIL")

    print("\n── 2. LA FENETRE EST BORNEE PAR LA PEREMPTION, RELUE AU FIRMWARE ─")
    per = peremption_us()
    ctrl(per is not None, "`DN_LINK_PEREMPTION_US` relu dans dn_link.h",
         "%s us" % per)
    if per:
        age_max_s = (L.FENETRE - 1)          # a 1 Hz
        ctrl(age_max_s * 1_000_000 < per,
             "aucun echantillon du filtre n'atteint la peremption",
             "n = %d ⇒ le plus vieux a %d s, peremption %d s"
             % (L.FENETRE, age_max_s, per // 1_000_000))

    print("\n── 3. ON MOYENNE A LA RESOLUTION AFFICHEE ────────────────────────")
    prec = precisions()
    mauvaises = [(m, i) for (m, i) in L.LISSEES
                 if prec.get(m, [None] * 9)[i] != "DN_PREC_DIXIEME"]
    ctrl(not mauvaises, "les 4 grandeurs lissees sont toutes DN_PREC_DIXIEME",
         "⛔ %s" % mauvaises if mauvaises
         else "moyenner en dixiemes = moyenner a la resolution affichee")

    print("\n── 4. LE REJEU SUR LA VRAIE CAPTURE (960 echantillons) ───────────")
    if not os.path.exists(CAPTURE):
        ctrl(False, "la capture existe", "⛔ %s introuvable" % CAPTURE)
        return 1
    ser = capture()
    lisse = rejouer(dn_agent.Lisseur(), ser)
    brut = rejouer(dn_agent.Lisseur(actif=False), ser)
    ctrl(True, "capture rejouee dans le PRODUIT",
         "%d echantillons x 16 grandeurs" % len(ser[("cpu", 0)]))
    # ⚠️ Le chiffre publie dans `mesures/dn4-5/T4-choix-fenetre.txt` : CPU GHz
    #    passe de p95 2,0 a p95 0,7 (soit 20 -> 7 dixiemes).
    ctrl(p95(brut[("cpu", 1)]) == 20 and p95(lisse[("cpu", 1)]) == 7,
         "CPU GHz : le chiffre PUBLIE est celui que le code produit",
         "p95 %s -> %s dixiemes (publie : 2,0 -> 0,7 GHz)"
         % (p95(brut[("cpu", 1)]), p95(lisse[("cpu", 1)])))
    intacts = [k for k in ser if k not in L.LISSEES and lisse[k] != brut[k]]
    ctrl(not intacts, "⛔ les 12 autres grandeurs sont INTACTES",
         "⛔ modifiees : %s" % intacts if intacts
         else "seules les 4 verdictees changent")
    bouge = [k for k in L.LISSEES if lisse[k] != brut[k]]
    ctrl(len(bouge) == 4, "et les 4 lissees ont bien CHANGE",
         "⛔ une grandeur declaree lissee qui ne bouge pas serait un lissage MORT")

    print("\n── 5. AC4.3 — LA FENETRE SE VIDE A LA REPRISE ────────────────────")
    # On coupe a t=500 : la generation change, le filtre DOIT repartir de zero.
    coupe = rejouer(dn_agent.Lisseur(), ser, coupure_a=500)
    v_apres = coupe[("cpu", 1)][500]
    v_brut = ser[("cpu", 1)][500]
    ctrl(v_apres == v_brut,
         "la 1re valeur APRES reprise est la valeur BRUTE",
         "%s == %s dixiemes — ⛔ aucune trace de la fenetre d'avant"
         % (v_apres, v_brut))
    # Rupture (source absente) : la fenetre de CETTE grandeur se vide.
    lis = dn_agent.Lisseur()
    lis.appliquer([("cpu", [0, 100, 0, 0])], 0)
    lis.appliquer([("cpu", [0, 300, 0, 0])], 0)
    lis.appliquer([("cpu", [0, None, 0, 0])], 0)
    apres = lis.appliquer([("cpu", [0, 900, 0, 0])], 0)[0][1][1]
    ctrl(apres == 900, "une source ABSENTE vide la fenetre de sa grandeur",
         "%s == 900 — ⛔ moyenner a cheval sur un trou fabriquerait une valeur "
         "qui n'a jamais existe" % apres)

    print("\n── 6. `--lissage off` EST UN VRAI CONTOURNEMENT ──────────────────")
    ctrl(all(brut[k] == [v for v in ser[k]] for k in ser),
         "`actif=False` rend la photo INCHANGEE",
         "c'est la jambe « brut » de l'A/B d'AC4.4")

    print("\n── 7. LES TEMOINS NEGATIFS — ON DOIT LES VOIR ROUGIR ─────────────")
    # A. le filtre NE se vide PAS a la reprise : la valeur d'avant la coupure
    #    ressort — c'est TEXTUELLEMENT le piege nomme par AC4.3.
    class SansVidage(dn_agent.Lisseur):
        def appliquer(self, photo, generation=0):
            return dn_agent.Lisseur.appliquer(self, photo, self._generation
                                              if self._generation is not None
                                              else generation)
    mut = rejouer(SansVidage(), ser, coupure_a=500)
    ctrl(mut[("cpu", 1)][500] != ser[("cpu", 1)][500],
         "mutant A « pas de vidage a la reprise » : VU ROUGIR",
         "publie %s au lieu du brut %s — la valeur d'AVANT la coupure a SURVECU"
         % (mut[("cpu", 1)][500], ser[("cpu", 1)][500]))
    # B. la fenetre depasse la peremption.
    ctrl(not ((6 - 1) * 1_000_000 < (per or 0)),
         "mutant B « fenetre n = 6 » : VU ROUGIR",
         "le plus vieux echantillon aurait 5 s, pour une peremption de %d s"
         % ((per or 0) // 1_000_000))
    # C. `CPU %` glisse dans le lot.
    class AvecCpuPct(dn_agent.Lisseur):
        LISSEES = dn_agent.Lisseur.LISSEES | {("cpu", 0)}
    ctrl(set(AvecCpuPct.LISSEES) != ATTENDU,
         "mutant C « CPU %% lisse en douce » : VU ROUGIR",
         "le controle du §1 le refuserait — AC4.4 n'a pas encore tranche")

    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return 1 if ko_total[0] else 0


if __name__ == "__main__":
    sys.exit(main())

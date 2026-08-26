#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-5 / AC4.1 — LES 8 GRANDEURS QUI N'ONT AUCUN CHIFFRE DE SAUT EN ONT UN.

⚠️ IL TOURNE SUR LE PYTHON **WINDOWS**, comme `dn_agent.py` : `atiadlxx.dll`,
   `psutil` et LibreHardwareMonitor n'existent que la. Depuis WSL :

     powershell.exe -NoProfile -Command "& python \
       \\\\wsl.localhost\\Ubuntu\\home\\nasbarok\\projects\\desknode\\tools\\mesure_lissage_dn45.py \
       --echantillons 960 --csv <chemin>"

═══════════════════════════════════════════════════════════════════════════════
POURQUOI CE TIR EXISTE
═══════════════════════════════════════════════════════════════════════════════

`§13.7` (dn4-1) a tranche le lissage pour **8 grandeurs**, sur 960 echantillons
a 1 Hz. **Le fil en porte 16 aujourd'hui** (dn4-6, dn4-9, D11, D13). ⇒ **8
grandeurs n'ont AUCUN chiffre de saut**, et decider leur lissage « par analogie »
serait tres exactement le *« lissage decide par principe »* que la story
interdit.

═══════════════════════════════════════════════════════════════════════════════
LES QUATRE PIEGES DE METHODE QU'IL FERME
═══════════════════════════════════════════════════════════════════════════════

1. ⛔ **IL NE REJOUE PAS LES SOURCES.** Il IMPORTE `dn_agent` et appelle
   `Collecteur.photo()` — la fonction meme qui alimente le fil. Un harnais qui
   relirait `psutil` et l'ADL a cote mesurerait *une autre chose que le produit*,
   et « un harnais qui REJOUE au lieu d'EXTRAIRE+APPELER est une gate
   decorative ».

2. 🔴 **LA RESOLUTION D'AFFICHAGE EST LUE DANS LE FIRMWARE, ⛔ PAS RECOPIEE.**
   Le critere de §13.7 porte sur **la valeur AFFICHEE**, a la resolution
   REELLEMENT affichee : `tr/min` et `W` sont `DN_PREC_ENTIER`, le reste est
   `DN_PREC_DIXIEME`. Juger le brut mesurerait un bruit que l'ecran ne montrera
   JAMAIS. La table est donc PARSEE dans `dn_ui.c` (`k_desc[]`) : si un jour une
   precision change, ce tir la suit tout seul.

3. ⚠️ **LES RUPTURES SORTENT DU DENOMINATEUR.** Une source qui meurt (LHM
   arrete, TDR du pilote AMD) rend une metrique absente : l'echantillon SUIVANT
   n'a **pas de predecesseur legitime**, il ne peut etre ni un saut ni un
   changement. Meme regle que `dn_w2_t.ruptures` (dn3-3). ⛔ Sans ce retrait, le
   biais irait TOUJOURS vers « ne saute pas ».

4. ⚠️ **LE SEUIL EST ECRIT AVANT LE TIR, ET IL VIENT DE §13.7** :
   **saut p95 >= 40 % de la plage observee ⇒ LISSER**. ⛔ Il ne se renegocie pas
   apres coup en regardant les chiffres.
   🔴 **ET UNE PLAGE NULLE N'EST PAS UN VERDICT** : une grandeur CONSTANTE sur
   la fenetre (plage = 0) ne « ne saute pas », elle **n'a pas ete exercee**. Elle
   est classee `NON EXERCEE`, ⛔ jamais `NE PAS LISSER` — c'est la difference
   entre « mesure » et « absence de mesure ».

⛔ IL N'ECRIT RIEN SUR LE PORT SERIE ET NE TOUCHE PAS LA CARTE. Il peut donc
   tourner pendant que la carte est attachee ailleurs.
"""

import argparse
import csv
import os
import re
import statistics
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "agent"))

DN_UI_C = os.path.join(RACINE, "firmware", "desknode", "main", "dn_ui.c")

# L'ordre des metriques sur le fil, et le nom de la case correspondante.
# ⚠️ LES NOMS D'ENUM SONT CEUX DU FIRMWARE, ⛔ pas ceux du protocole : le fil
#    dit `net`/`disk`, l'UI dit `RESEAU`/`DISQUE` (renommage D8). Se tromper ici
#    ne donne pas un chiffre faux — le parseur CRIE et le tir s'arrete.
CASES = [("cpu", "DN_UI_CASE_CPU"), ("gpu", "DN_UI_CASE_GPU"),
         ("ram", "DN_UI_CASE_RAM"), ("net", "DN_UI_CASE_RESEAU"),
         ("disk", "DN_UI_CASE_DISQUE")]

# Les 8 grandeurs DEJA tranchees par §13.7 (dn4-1) — reconduites TELLES QUELLES,
# ⛔ pas re-mesurees ici. Elles servent de TEMOIN : si l'une d'elles ressortait
# tres differemment, ce serait la SESSION qui est atypique, pas le candidat.
# 🔴 §13.7 A MESURE HUIT GRANDEURS ET N'EN A CLASSE QUE **SIX** — verifie le
#    2026-08-26 en relisant sa prose (`…-liaison-pc.md`, l.541-546), APRES une
#    premiere version de cet outil qui attribuait a tort un verdict a `GPU %` et
#    a `RESEAU haut`. Attribuer a une source un verdict qu'elle n'a pas publie
#    est exactement le defaut que ce depot traque : le motif etait plausible
#    (§13.11.1 dit que l'ADL est deja moins dynamique) mais c'est un FAIT A
#    CONNAITRE AVANT DE DECIDER, ⛔ pas une decision prise.
# ⇒ `GPU %` et `RESEAU haut` sont traitees comme des grandeurs NEUVES : le
#   critere s'y applique, avec le chiffre de dn4-5.
LEGS_13_7 = {
    ("cpu", 0): "A DISCUTER (« un CPU lisse ment sur les pics ») — reste OUVERT",
    ("cpu", 1): "LISSER",
    ("gpu", 1): "NE PAS LISSER",
    ("ram", 0): "NE PAS LISSER",
    ("net", 0): "LISSER",
    ("disk", 0): "LISSER",
}

# ⚠️ Les deux que §13.7 a MESUREES sans les CLASSER — dit explicitement, sinon
#    leur absence de la table ci-dessus se lirait comme un oubli.
NON_CLASSEES_13_7 = {("gpu", 0): "GPU %", ("net", 1): "RESEAU haut"}


def precisions_depuis_firmware():
    """Rend {case: [(unite, prec), ...]} en PARSANT `k_desc[]` de dn_ui.c.

    ⛔ Recopier ces precisions a la main serait exactement le defaut que ce
       depot traque : deux verites qui derivent en silence."""
    txt = open(DN_UI_C, encoding="utf-8").read()
    d = txt.index("static const dn_widget_desc_t k_desc[DN_UI_METRIQUES] = {")
    corps = txt[d:txt.index("\n};", d)]
    out = {}
    for nom, cle in CASES:
        m = re.search(re.escape("[" + cle + "] = {"), corps)
        if not m:
            raise SystemExit("⛔ case %s introuvable dans k_desc[] — le tir "
                             "s'arrete plutot que de deviner." % cle)
        # jusqu'a la case suivante (ou la fin)
        suivants = [corps.index("[" + c + "] = {") for _, c in CASES
                    if ("[" + c + "] = {") in corps
                    and corps.index("[" + c + "] = {") > m.start()]
        bloc = corps[m.start():min(suivants) if suivants else len(corps)]
        g = re.search(r'\.grandeurs = \{(.*?)\}\},', bloc, re.S)
        if not g:
            raise SystemExit("⛔ `.grandeurs` introuvable pour %s." % cle)
        entrees = re.findall(r'\{[^{}]*?\.unite = ("(?:[^"\\]|\\.)*"(?:\s*"(?:[^"\\]|\\.)*")*)'
                             r'[^{}]*?\.prec = (DN_PREC_\w+)', g.group(1), re.S)
        if not entrees:
            raise SystemExit("⛔ aucune grandeur lue pour %s." % cle)
        out[nom] = [(u, p) for u, p in entrees]
    # 🔴 LA 16e GRANDEUR N'EST PAS DANS `k_desc[].grandeurs`, ET CE N'EST PAS UN
    #    OUBLI. `ram` porte DEUX valeurs sur le fil (`%` et `Go TOTAUX`) mais
    #    `k_desc[DN_UI_CASE_RAM].n_grandeurs = 1` : le total est une DONNEE
    #    SECONDAIRE (`DN_SEC_PC_RAM_GO`), pas une grandeur — et c'est structurel,
    #    parce qu'avec `n_grandeurs >= 2` la JAUGE ne serait jamais creee
    #    (`dn_widget.c` teste `desc->indicateur && n == 1`).
    # ⚠️ VERIFIE AVANT D'ECRIRE, ET UNE PREMIERE LECTURE ETAIT FAUSSE : le
    #    chemin `DN_SEC_RAM_GO` (dn_ui.c:8549) affiche « / 32 Go » EN DUR, ce qui
    #    ressemblait a « le total du fil n'est jamais affiche ». C'est le chemin
    #    du MOCK (dn3-2). Le chemin REEL est `DN_SEC_PC_RAM_GO` (dn_ui.c:7600),
    #    qui lit bien `vue->v[1]` et le formate par `fmt_dixiemes()`.
    # ⇒ resolution d'affichage du total : DIXIEME, comme le reste.
    if _sec_pc_ram_go_lit_le_fil(txt):
        out["ram"].append(('"Go"', "DN_PREC_DIXIEME"))
    else:
        raise SystemExit("⛔ `DN_SEC_PC_RAM_GO` ne lit plus `vue->v[1]` : la 16e "
                         "grandeur n'est peut-etre plus affichee. Le tir "
                         "s'arrete plutot que de deviner sa resolution.")
    return out


def _sec_pc_ram_go_lit_le_fil(txt):
    """⛔ On ne SUPPOSE pas que le total du fil est affiche : on le VERIFIE dans
    la branche qui le rend, a chaque tir."""
    i = txt.find("case DN_SEC_PC_RAM_GO:")
    if i < 0:
        return False
    bloc = txt[i:i + 1200]
    return "vue->v[1]" in bloc and "fmt_dixiemes" in bloc


def affichee(dixiemes, prec):
    """La valeur telle que l'ECRAN la montre — ⛔ pas la source."""
    if dixiemes is None:
        return None
    if prec == "DN_PREC_ENTIER":
        return float(int(dixiemes / 10.0 + 0.5))
    return round(dixiemes / 10.0, 1)


def analyser(serie):
    """serie = liste de valeurs affichees, `None` = rupture.

    Rend le bloc de chiffres de §13.7 + le compte de ruptures RETIREES."""
    vals = [v for v in serie if v is not None]
    sauts, ruptures, changements, transitions = [], 0, 0, 0
    for a, b in zip(serie, serie[1:]):
        if a is None or b is None:
            ruptures += 1
            continue
        transitions += 1
        d = abs(b - a)
        sauts.append(d)
        if d > 0:
            changements += 1
    if not vals or not sauts:
        return None
    sauts_tries = sorted(sauts)
    p95 = sauts_tries[min(len(sauts_tries) - 1, int(0.95 * len(sauts_tries)))]
    return {
        "n": len(vals), "min": min(vals), "max": max(vals),
        "plage": max(vals) - min(vals),
        "med": statistics.median(sauts), "p95": p95, "max_saut": max(sauts),
        "pct_change": 100.0 * changements / transitions if transitions else 0.0,
        "ruptures": ruptures, "transitions": transitions,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  §13.7 CONFRONTE A SON PROPRE CRITERE — le tableau publie par dn4-1, RECOPIE
#  VERBATIM depuis `hardware/…-liaison-pc.md` §13.7 (lignes 525-533).
#
#  🔴 POURQUOI CE BLOC EXISTE. AC4.2 dit « LE CRITERE DE §13.7 FAIT FOI — saut
#     p95 >= 40 % de la plage observee ⇒ LISSER » ET « les 8 verdicts de §13.7
#     se reconduisent tels quels ». Avant d'appliquer ce critere a huit
#     grandeurs neuves, on verifie qu'il REPRODUIT les verdicts qu'il pretend
#     resumer. *« Un constat peut etre JUSTE dans ses chiffres et FAUX dans son
#     verdict — relire le critere qu'il invoque, pas seulement recompter. »*
#  ⛔ CE BLOC NE RENVERSE RIEN : les verdicts de §13.7 sont reconduits TELS
#     QUELS, comme la story l'ordonne. Il DIT ce que le critere rendrait.
# ═══════════════════════════════════════════════════════════════════════════
LEGS_TABLE = [
    # (nom, min, max, p95, verdict publie par §13.7)
    ("CPU GHz",      1.2,   3.2,  2.0,  "LISSER"),
    ("CPU %",       14.2,  86.9, 45.7,  "A DISCUTER"),
    ("RESEAU bas",   0.1, 296.1, 86.1,  "LISSER"),
    ("RESEAU haut",  0.2,  28.1,  9.3,  "(non classe)"),
    ("DISQUE Mo/s",  0.0, 268.4,  7.6,  "LISSER"),
    ("GPU %",        0.0,  19.0,  6.0,  "NE PAS LISSER"),
    ("GPU degC",    46.0,  48.0,  1.0,  "NE PAS LISSER"),
    ("RAM %",       60.1,  67.6,  0.1,  "NE PAS LISSER"),
]


def confronter_le_critere():
    """Applique le critere de 40 % au tableau de §13.7 et compare au verdict
    que §13.7 a REELLEMENT publie. Rend la liste des desaccords."""
    print("\n" + "=" * 100)
    print("🔬 LE CRITERE DE §13.7 REPRODUIT-IL LES VERDICTS DE §13.7 ?")
    print("=" * 100)
    print("%-13s %8s %8s %8s %9s  %-15s %-15s %s"
          % ("grandeur", "min", "max", "p95", "p95/plage", "critere 40 %",
             "§13.7 PUBLIE", "accord ?"))
    desaccords = []
    for nom, mn, mx, p95, publie in LEGS_TABLE:
        plage = mx - mn
        r = (p95 / plage * 100.0) if plage else 0.0
        calcule = "LISSER" if r >= 40.0 else "NE PAS LISSER"
        if publie in ("A DISCUTER", "(non classe)"):
            accord = "— (hors binaire)"
        elif calcule == publie:
            accord = "✅ oui"
        else:
            accord = "🔴 NON"
            desaccords.append((nom, r, calcule, publie))
        print("%-13s %8.1f %8.1f %8.1f %8.1f%%  %-15s %-15s %s"
              % (nom, mn, mx, p95, r, calcule, publie, accord))
    print("=" * 100)
    if desaccords:
        print("🔴 LE CRITERE NE REPRODUIT PAS %d DES VERDICTS DE §13.7 :"
              % len(desaccords))
        for nom, r, calc, pub in desaccords:
            print("   · %-13s p95 = %.1f %% de la plage ⇒ le critere dit « %s », "
                  "§13.7 a publie « %s »" % (nom, r, calc, pub))
        print("⇒ ⛔ LE CRITERE, PRIS A LA LETTRE, N'EST PAS CE QUI A TRANCHE §13.7.")
        print("   Les huit verdicts de §13.7 restent RECONDUITS TELS QUELS (la story")
        print("   l'ordonne). Mais appliquer ce critere aux grandeurs NEUVES revient")
        print("   a utiliser une regle PLUS SEVERE que celle qui a servi au legs —")
        print("   et c'est une question OWNER, ⛔ pas un arbitrage d'agent.")
    else:
        print("✅ le critere reproduit tous les verdicts binaires de §13.7.")
    return desaccords


def pas_de_plage(st, prec):
    """La plage observee, exprimee en **PAS D'AFFICHAGE**.

    🔴 POURQUOI CETTE COLONNE EXISTE — LECON `dn3-3`/AC2.1, PAYEE. Le critere de
       §13.7 est un RATIO (`p95 / plage`). Quand la plage ne fait que quelques
       pas d'affichage, ce ratio n'a que quelques crans possibles : « 33,3 % »
       sur une plage de 3 pas ne veut pas dire « la grandeur saute d'un tiers de
       sa plage », il veut dire « 1 pas sur 3 », et le seuil de 40 % tombe ENTRE
       deux crans atteignables. *« Un seuil plus fin que le PAS de son
       denominateur n'est pas tranchable. »*

    ⛔ CETTE COLONNE NE RENVERSE AUCUN VERDICT, ET C'EST DELIBERE : le critere de
       §13.7 fait foi et « ⛔ il ne se renegocie pas apres coup ». Elle DIT le
       conditionnement, pour que le lecteur sache ce que le chiffre vaut."""
    res = 1.0 if prec == "DN_PREC_ENTIER" else 0.1
    return int(round(st["plage"] / res))


def verdict(st):
    """LE CRITERE DE §13.7, ECRIT AVANT LE TIR : saut p95 >= 40 % de la plage
    observee ⇒ LISSER. ⛔ Il ne se renegocie pas en regardant les chiffres."""
    if st is None:
        return "PAS DE DONNEE", "aucun echantillon exploitable"
    if st["plage"] == 0:
        # 🔴 CE N'EST PAS « NE PAS LISSER ». Une grandeur qui n'a pas bouge n'a
        #    pas ete EXERCEE : le tir ne dit rien d'elle, et le dire est la seule
        #    reponse honnete.
        return "NON EXERCEE", "plage NULLE sur la fenetre — ⛔ pas un verdict"
    r = st["p95"] / st["plage"]
    if r >= 0.40:
        return "LISSER", "saut p95 = %.1f %% de la plage (seuil 40 %%)" % (r * 100)
    return "NE PAS LISSER", "saut p95 = %.1f %% de la plage (seuil 40 %%)" % (r * 100)


def publier(prec, series):
    """Le tableau de §13.7. ⚠️ APPELE PAR LES DEUX CHEMINS (tir neuf et
    re-analyse) : deux impressions separees derivent, et un dossier de mesure
    ou la re-analyse ne rend pas le meme format que le tir ne se relit pas."""
    print("\n" + "=" * 108)
    print("dn4-5 / AC4.1 — TABLE DE SAUT, FORMAT §13.7  (valeurs AFFICHEES)")
    print("=" * 108)
    print("%-12s %-9s %10s %10s %9s %9s %9s %8s %6s %6s  %s"
          % ("grandeur", "unite", "min", "max", "saut med", "saut p95",
             "saut MAX", "% chg", "rupt", "pas", "VERDICT"))
    for nom, _ in CASES:
        for i, (u, p) in enumerate(prec[nom]):
            st = analyser(series[(nom, i)])
            legs = LEGS_13_7.get((nom, i))
            v, motif = verdict(st)
            u_txt = u.strip('"').replace('\\xC2\\xB0', "deg")
            if st is None:
                print("%-12s %-9s %s" % ("%s.%d" % (nom, i), u_txt,
                                         "⛔ AUCUNE DONNEE"))
                continue
            marque = ("📎 §13.7" if legs
                      else ("🔶 §13.7 MUETTE" if (nom, i) in NON_CLASSEES_13_7
                            else "🆕 dn4-5"))
            pas = pas_de_plage(st, p)
            mal_conditionne = pas < 10
            print("%-12s %-9s %10.1f %10.1f %9.1f %9.1f %9.1f %7.1f%% %6d %6d  %s %s"
                  % ("%s.%d" % (nom, i), u_txt, st["min"], st["max"], st["med"],
                     st["p95"], st["max_saut"], st["pct_change"], st["ruptures"],
                     pas, marque, legs if legs else "%s — %s" % (v, motif)))
            if mal_conditionne and not legs:
                print("%-12s %s" % ("", "   🔴 RESERVE : la plage ne fait que "
                      "%d pas d'affichage. Le ratio du critere n'a donc que %d "
                      "crans, et le seuil de 40 %% tombe ENTRE deux d'entre eux. "
                      "⛔ Le verdict ci-dessus TIENT (le critere fait foi et ne se "
                      "renegocie pas), mais il est MAL CONDITIONNE : cette "
                      "fenetre n'a pas exerce la grandeur." % (pas, pas)))
    print("=" * 108)
    print("📎 §13.7 = deja tranche par dn4-1, RECONDUIT tel quel, ⛔ pas re-mesure ici.")
    print("🆕 dn4-5 = grandeur qui n'avait AUCUN chiffre de saut avant ce tir.")
    print("🔶 §13.7 MUETTE = §13.7 l'a MESUREE mais ⛔ NE L'A JAMAIS CLASSEE (elle")
    print("   n'apparait dans aucun de ses trois groupes). Le critere s'y applique.")
    print("⚠️ « rupt » = transitions RETIREES du denominateur (source absente).")
    print("⛔ « NON EXERCEE » n'est PAS « NE PAS LISSER » : la grandeur n'a pas bouge,")
    print("   donc ce tir ne dit RIEN d'elle. Il faut une fenetre qui l'exerce.")
    confronter_le_critere()


def main():
    # ⚠️ LA CONSOLE WINDOWS EST EN cp1252, et ce tir a plante dessus au premier
    #    essai (2026-08-26) : `UnicodeEncodeError` sur le premier trait de
    #    tableau, AVANT le moindre echantillon. `dn_agent.py` fait le meme
    #    `reconfigure` pour la meme raison. ⛔ Un tir de 16 min qui meurt a la
    #    ligne 1 sur un caractere d'ornement est une fenetre perdue.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--echantillons", type=int, default=960,
                    help="≥ 960 pour respecter le protocole de §13.7")
    ap.add_argument("--periode", type=float, default=1.0)
    ap.add_argument("--csv", default=None, help="capture BRUTE (exigee avant "
                                               "toute publication de chiffre)")
    # 🎯 REJOUER SUR LA CAPTURE, ⛔ PAS RE-MESURER. Un dossier de mesure doit
    #    pouvoir etre RELU : si l'analyse change (une colonne de plus, un
    #    conditionnement a declarer), on la rejoue sur les MEMES octets. Refaire
    #    un tir donnerait d'autres chiffres et personne ne saurait ce qui a
    #    change — l'analyse ou la tour.
    ap.add_argument("--rejouer", default=None, metavar="CSV",
                    help="re-analyse une capture existante, SANS re-mesurer")
    a = ap.parse_args()

    prec = precisions_depuis_firmware()
    print("── resolutions d'affichage, LUES dans dn_ui.c (k_desc[]) ──")
    for nom, _ in CASES:
        print("  %-5s %s" % (nom, " · ".join(
            "%s:%s" % (u.strip('"').replace('\\xC2\\xB0', 'deg'),
                       p.replace("DN_PREC_", "")) for u, p in prec[nom])))

    series = {}
    for nom, _ in CASES:
        for i in range(len(prec[nom])):
            series[(nom, i)] = []

    if a.rejouer:
        with open(a.rejouer, newline="", encoding="utf-8") as fh:
            r = csv.DictReader(fh)
            # ⚠️ LE COMPTE DE CHAMPS EST VERIFIE A CHAQUE LIGNE : « un lecteur
            #    permissif decale les colonnes EN SILENCE », et ce depot a deja
            #    publie « CPU % max = 1600 » (c'etait la frequence).
            attendus = ["%s.%d" % (n, i) for n, _ in CASES
                        for i in range(len(prec[n]))]
            manquants = [c for c in attendus if c not in (r.fieldnames or [])]
            if manquants:
                raise SystemExit("⛔ colonnes ABSENTES de la capture : %s"
                                 % manquants)
            n_lignes = 0
            for ligne in r:
                n_lignes += 1
                for c in attendus:
                    v = ligne[c]
                    series[tuple(c.rsplit(".", 1)[0:1]) + (int(c.rsplit(".", 1)[1]),)] \
                        .append(None if v in ("", None) else float(v))
        print("\n🎯 RE-ANALYSE de %s — %d echantillon(s), ⛔ AUCUNE nouvelle mesure"
              % (a.rejouer, n_lignes))
        publier(prec, series)
        return 0

    import dn_agent
    col = dn_agent.Collecteur(verbeux=True)

    f = w = None
    if a.csv:
        f = open(a.csv, "w", newline="", encoding="utf-8")
        w = csv.writer(f)
        entete = ["t"] + ["%s.%d" % (n, i) for n, _ in CASES
                          for i in range(len(prec[n]))]
        w.writerow(entete)

    t0 = time.time()
    print("\n── tir : %d echantillons a %.1f Hz (~%.1f min) ──"
          % (a.echantillons, 1.0 / a.periode,
             a.echantillons * a.periode / 60.0))
    for k in range(a.echantillons):
        photo = dict(col.photo())
        ligne = [round(time.time() - t0, 3)]
        for nom, _ in CASES:
            vs = photo.get(nom)
            for i, (_, p) in enumerate(prec[nom]):
                d = None
                if vs is not None and i < len(vs):
                    d = vs[i]
                v = affichee(d, p)
                series[(nom, i)].append(v)
                ligne.append("" if v is None else v)
        if w:
            # ⚠️ Vide a chaque ligne : un tir de 16 min interrompu doit laisser
            #    15 min de donnees, ⛔ pas un tampon perdu.
            w.writerow(ligne)
            f.flush()
        if (k + 1) % 60 == 0:
            print("  %4d/%d …" % (k + 1, a.echantillons), flush=True)
        time.sleep(max(0.0, a.periode - ((time.time() - t0) % a.periode)))
    if f:
        f.close()

    publier(prec, series)
    return 0


if __name__ == "__main__":
    sys.exit(main())

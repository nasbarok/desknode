#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mesure_w2_dn48.py — la qualification W2 des QUATRE grandeurs LHM (AC4).

🔴 CRITERE GELE ET HORODATE LE 2026-08-21T18:09:35Z, COMMITTE EN `c377d2c`,
   ⛔ AVANT QUE CE FICHIER N'EXISTE. Les seuils ci-dessous sont RECOPIES de la
   story ; ⛔ ils ne se renegocient pas, et une divergence entre les deux se
   verrait ici (ils sont ecrits en toutes lettres dans les deux endroits).

🔴 IL NE DEPEND PAS DE `dn_agent.py`, ET C'EST LA DOCTRINE DU DEPOT :
   « l'agent est le PRODUIT, ce script est un INSTRUMENT. Les faire dependre
   l'un de l'autre ferait qu'une mesure change quand le produit change. »
   ⇒ il relit `/metrics` lui-meme. 🎯 Et c'est PLUS correct : ce qu'on
   qualifie est le MOUVEMENT DE LA SOURCE, ⛔ pas le code de l'agent.

⚠️ IL NE TOUCHE PAS AU PORT SERIE : il peut donc tourner pendant que la carte est
   attachee a WSL. C'est deja la propriete de `mesure_grandeurs_dn46.py`.

🔴 CE QUI EST JUGE EST LA VALEUR **AFFICHEE**, ⛔ PAS LA BRUTE :
   · `cpu.degc`  -> DIXIEME de °C   (DN_PREC_DIXIEME)
   · les tr/min  -> ENTIER          (DN_PREC_ENTIER)
   Une meme source qualifie ou non selon sa precision d'affichage.

Usage (Python Windows de la tour) :
    python mesure_w2_dn48.py --minutes 16 --csv w2_dn48.csv
    python mesure_w2_dn48.py --rejuger w2_dn48.csv      # re-juge SANS re-tirer
"""
import argparse
import http.client
import io
import re
import statistics
import sys
import time

HOTE, PORT, CHEMIN = "127.0.0.1", 8085, "/metrics"

# ── LES SONDES — memes identifiants que la table de l'agent, RECOPIES ────────
# ⚠️ RECOPIE ASSUMEE ET NOMMEE : si l'agent change de sonde sans le dire ici, la
#    qualification porterait sur AUTRE CHOSE que ce qui circule. ⇒ les deux se
#    lisent cote a cote, et cette ligne est la pour qu'on y pense.
TEMP_CPU = "/intelcpu/0/temperature/10"      # « CPU Package »
FAN_TOP, FAN_NOCTUA, FAN_CASE, FAN_REAR = (
    "/lpc/nct6792d/0/fan/0", "/lpc/nct6792d/0/fan/1",
    "/lpc/nct6792d/0/fan/2", "/lpc/nct6792d/0/fan/4")

# ── LES SEUILS GELES (story dn4-8, 2026-08-21T18:09:35Z, commit c377d2c) ────
# \U0001f534 AMENDE LE 2026-08-21T18:25:17Z — C2 ETAIT LE PLAFOND LUI-MEME.
#    LHM rafraichit toutes les **4,00 s** (MESURE : 785 lectures a 10 Hz sur 90 s,
#    quatre grandeurs, mediane 4,00-4,01 s). ⇒ a 1 Hz d'echantillonnage, le taux
#    de changement du texte est PLAFONNE A 1/4 = 25,0 %. Or C2 pour la degC etait
#    gele a 25 % : EXACTEMENT LE PLAFOND, donc INATTEIGNABLE, donc incapable de
#    discriminer.
# ⛔ ET LE MOTIF QUE J'AVAIS ECRIT ETAIT FAUX : « la resolution est 10x plus fine,
#    le texte change bien plus souvent ». NON — la resolution ne peut pas faire
#    changer le texte plus souvent que LA SOURCE NE SE RAFRAICHIT.
# ⇒ C2 EST DESORMAIS RELATIF AU PLAFOND MESURE : « le texte change a >= 60 % des
#   OCCASIONS OU IL POUVAIT CHANGER ». \U0001f3af Independant de la cadence
#   d'echantillonnage, donc comparable si LHM ou l'agent changeaient de rythme.
# ⚠️ Amendement OWNER, DATE, POSTERIEUR a la mesure, motive par une FAUTE DE
#    RAISONNEMENT DE L'AGENT — ⛔ pas par un resultat qui deplaisait. Meme
#    traitement que le critere 6 d'AC2.
# ⛔ C1 ET C3 NE BOUGENT PAS : seul C2 etait fautif.
C2_OCCASIONS_MIN = 60.0     # % des occasions, ⛔ pas % des echantillons
SEUILS = {
    # famille    C1 etendue, C3 sigma, unite, precision
    "degc":  (3.0, 0.5, "degC", "dixieme"),
    "rpm":   (5.0, 1.0, "tr/min", "entier"),
}
GRANDEURS = [
    ("cpu.degc",            "degc"),
    ("disk.extraction_moy", "rpm"),
    ("disk.cpu_noctua",     "rpm"),
    ("disk.case_group",     "rpm"),
]
COLONNES = ["t_s", "cpu.degc", "disk.extraction_moy", "disk.cpu_noctua",
            "disk.case_group", "fan.top_out", "fan.rear_out"]

_LIGNE = re.compile(
    r'^lhm_\S+\s+\{.*?"sensorId"="([^"]*)".*?"hardwareId"="([^"]*)".*?\}\s+(\S+)\s*$')


class Lhm(object):
    """Connexion PERSISTANTE — l'ouverture TCP dominait le cout (AC2)."""

    def __init__(self):
        self.c = None

    def lire(self):
        for dernier in (False, True):
            try:
                if self.c is None:
                    self.c = http.client.HTTPConnection(HOTE, PORT, timeout=5.0)
                self.c.request("GET", CHEMIN, headers={"Connection": "keep-alive"})
                r = self.c.getresponse()
                b = r.read()
                if r.will_close:
                    self.c.close(); self.c = None
                t = {}
                for l in b.decode("utf-8", "replace").splitlines():
                    if not l.startswith("lhm_"):
                        continue
                    m = _LIGNE.match(l)
                    if not m:
                        continue
                    try:
                        v = float(m.group(3))
                    except ValueError:
                        continue
                    if v != v or v - v != 0:      # NaN / +-inf
                        continue
                    t[m.group(2) + m.group(1)] = v
                return t
            except Exception:
                try:
                    if self.c:
                        self.c.close()
                except Exception:
                    pass
                self.c = None
                if dernier:
                    raise


def affichee(v, precision):
    """La valeur telle que la DALLE l'ecrirait. ⛔ C'est elle qu'on juge."""
    if v is None:
        return None
    return round(v, 1) if precision == "dixieme" else float(int(round(v)))


def echantillon(t):
    """Rend le dict des grandeurs AFFICHEES, plus les deux canaux bruts."""
    top, rear = t.get(FAN_TOP), t.get(FAN_REAR)
    # ⚠️ MEME REGLE QUE L'AGENT : la moyenne EXIGE LES DEUX canaux. Une moyenne
    #    sur un seul est un AUTRE nombre sous la meme etiquette.
    moy = (top + rear) / 2.0 if (top is not None and rear is not None) else None
    return {
        "cpu.degc": affichee(t.get(TEMP_CPU), "dixieme"),
        "disk.extraction_moy": affichee(moy, "entier"),
        "disk.cpu_noctua": affichee(t.get(FAN_NOCTUA), "entier"),
        "disk.case_group": affichee(t.get(FAN_CASE), "entier"),
        "fan.top_out": affichee(top, "entier"),
        "fan.rear_out": affichee(rear, "entier"),
    }


def cadence_lhm(lhm, secondes=12.0, periode=0.2, toutes=False):
    """\U0001f534 RELEVER LA CADENCE DE LHM, ⛔ NE PAS LA SUPPOSER EGALE A 1 Hz.

    Le critere gele l'exige : « une source cadencee interrogee trois fois en
    100 ms rend TROIS FOIS LA MEME MESURE — et FABRIQUE UNE FAUSSE STABILITE ».
    On sur-echantillonne et on regarde a quel intervalle la valeur CHANGE.
    """
    print("[w2] relevé de la cadence PROPRE de LHM (sur-echantillonnage %.1f Hz, "
          "%.0f s)..." % (1.0 / periode, secondes))
    cles = [n for n, _ in GRANDEURS] if toutes else ["cpu.degc"]
    t0 = time.monotonic()
    suites = {k: [] for k in cles}
    marques = []
    while time.monotonic() - t0 < secondes:
        e = echantillon(lhm.lire())
        for k in cles:
            suites[k].append(e.get(k))
        marques.append(time.monotonic() - t0)
        time.sleep(periode)
    if toutes:
        # \U0001f534 UNE SEULE SONDE NE SUFFIT PAS A ETABLIR UNE CADENCE : si elle
        #    etait figee pour une autre raison, on conclurait « LHM est lent »
        #    sur une observation qui ne parle que d'elle. Les quatre, ou rien.
        print("  n = %d lectures a %.1f Hz" % (len(marques), 1.0 / periode))
        for k in cles:
            v = suites[k]
            ch = [marques[i] for i in range(1, len(v)) if v[i] != v[i - 1]]
            if len(ch) < 3:
                print("  %-22s %d changement(s) — TROP PEU pour conclure" % (k, len(ch)))
                continue
            ec = [b - a for a, b in zip(ch, ch[1:])]
            print("  %-22s %3d chgts | mediane %5.2f s | min %5.2f | max %5.2f | %.3f Hz"
                  % (k, len(ch), statistics.median(ec), min(ec), max(ec),
                     1.0 / statistics.median(ec)))
        return None
    suite = suites["cpu.degc"]
    chg = [marques[i] for i in range(1, len(suite)) if suite[i] != suite[i - 1]]
    # \U0001f534 GARDE CORRIGEE LE 2026-08-21, EN SEANCE : elle exigeait « au moins 2
    #    changements », donc elle acceptait UN SEUL INTERVALLE et publiait sa
    #    « mediane ». Une mediane sur un point n'est pas une mediane. Vu passer
    #    « intervalle median 4,17 s » sur 2 changements, la ou une mesure a 785
    #    lectures donnait 4,00 s. ⛔ FAUSSE D'UN CRAN, et dans le sens dangereux :
    #    elle rendait un chiffre AU LIEU de refuser.
    # ⇒ il faut au moins 5 changements (4 intervalles) pour publier quoi que ce soit.
    if len(chg) < 5:
        print("[w2] ⚠️ %d changement(s) en %.0f s : CADENCE NON DETERMINEE — il en "
              "faut au moins 5 pour qu'une mediane ait un sens. ⛔ Ne pas conclure "
              "« LHM est fige », et ⛔ ne pas publier de plafond." % (len(chg), secondes))
        return None
    ecarts = [b - a for a, b in zip(chg, chg[1:])]
    med = statistics.median(ecarts)
    print("[w2] cadence LHM MESUREE : %d changement(s) en %.0f s, intervalle "
          "median %.2f s (~%.2f Hz)" % (len(chg), secondes, med, 1.0 / med))
    if med > 1.05:
        print("[w2] \U0001f534 LHM RAFRAICHIT PLUS LENTEMENT QUE 1 Hz. ⛔ Echantillonner "
              "a 1 Hz DUPLIQUERAIT des valeurs et FABRIQUERAIT de la stabilite : "
              "le taux de changement du TEXTE serait ARTIFICIELLEMENT BAS.")
    return med


def juger(nom, famille, vals, periode_lhm=None, periode_ech=1.0):
    """⚠️ `periode_lhm` est la cadence MESUREE de la source. Sans elle, C2 ne peut
    pas etre juge : on ne connait pas le nombre d'OCCASIONS."""
    c1min, c3min, unite, _prec = SEUILS[famille]
    v = [x for x in vals if x is not None]
    if len(v) < 2:
        print("  %-22s ⛔ %d echantillon(s) — NON JUGEABLE" % (nom, len(v)))
        return None
    etendue = max(v) - min(v)
    chg = sum(1 for a, b in zip(v, v[1:]) if a != b)
    taux = 100.0 * chg / (len(v) - 1)
    sigma = statistics.pstdev(v)
    # \U0001f534 C2 EST RELATIF AU PLAFOND MESURE. Le nombre d'OCCASIONS de changer
    #    est la duree observee divisee par la periode de rafraichissement de LHM.
    # ⛔ SANS CADENCE MESUREE, C2 N'EST PAS JUGEABLE — et on le DIT, on ne retombe
    #    pas sur un seuil absolu qui mesurerait notre echantillonnage.
    if periode_lhm and periode_lhm > 0:
        occasions = (len(v) - 1) * periode_ech / periode_lhm
        pct_occ = 100.0 * chg / occasions if occasions > 0 else 0.0
        c2 = pct_occ >= C2_OCCASIONS_MIN
    else:
        occasions, pct_occ, c2 = None, None, None
    c1, c3 = etendue >= c1min, sigma >= c3min
    ok = bool(c1) and bool(c2) and bool(c3)
    print("  %-22s n=%-5d %.1f..%.1f %s" % (nom, len(v), min(v), max(v), unite))
    print("     C1 etendue %9.2f >= %-6.1f %s" % (etendue, c1min, "OK" if c1 else "NON"))
    if c2 is None:
        print("     C2 ⛔ NON JUGEABLE : la cadence de LHM n'a pas ete mesuree")
    else:
        print("     C2 %5.1f %% des OCCASIONS (%.0f occ., %d chgt) >= %-5.1f%% %s"
              % (pct_occ, occasions, chg, C2_OCCASIONS_MIN, "OK" if c2 else "NON"))
        print("        (soit %.1f %% des echantillons ; plafond atteignable %.1f %%)"
              % (taux, 100.0 * periode_ech / periode_lhm))
    print("     C3 sigma   %9.2f >= %-6.1f %s" % (sigma, c3min, "OK" if c3 else "NON"))
    # \U0001f534 LE TELL D'UN INSTRUMENT MORT : une valeur EXACTEMENT constante.
    if etendue == 0.0:
        print("     \U0001f534 VALEUR EXACTEMENT CONSTANTE sur toute la session. ⛔ C'est le "
              "TELL D'UN INSTRUMENT MORT, ⛔ pas la preuve d'une grandeur immobile. "
              "VERIFIER L'INSTRUMENT AVANT D'ACCUSER LA SONDE.")
    print("     => %s" % ("\u2705 QUALIFIE" if ok else "\U0001f534 NE QUALIFIE PAS"))
    if not ok and nom == "disk.extraction_moy" and c1 and c2 and not c3:
        print("     \u26a0\ufe0f RESERVE ECRITE D'AVANCE : c'est une grandeur DERIVEE "
              "(moyenne de deux canaux), donc elle LISSE. Echouer C3 en passant C1 et "
              "C2 n'est ⛔ PAS une sonde morte — c'est la moyenne qui fait son travail.")
    return ok


def analyser(lignes, periode_lhm=None):
    print("\n" + "=" * 84)
    print("VERDICT W2 — seuils GELES le 2026-08-21T18:09:35Z (commit c377d2c)")
    print("=" * 84)
    res = {}
    for nom, fam in GRANDEURS:
        res[nom] = juger(nom, fam, [l[nom] for l in lignes], periode_lhm)
    return res


def relire_csv(chemin):
    """⛔ LECTURE STRICTE : un compte de colonnes qui ne correspond pas JETTE la
    session. Motif paye : un lecteur permissif a deja DECALE toutes les colonnes
    en silence, et l'analyse a publie « CPU % max = 1600 » — c'etait la frequence."""
    lignes = []
    with io.open(chemin, encoding="utf-8") as f:
        entete = f.readline().rstrip("\n").split(";")
        if entete != COLONNES:
            sys.exit("\u26d4 SESSION JETEE : en-tete CSV inattendu.\n  attendu : %s\n"
                     "  lu      : %s" % (COLONNES, entete))
        for n, l in enumerate(f, 2):
            ch = l.rstrip("\n").split(";")
            if len(ch) != len(COLONNES):
                sys.exit("\u26d4 SESSION JETEE : ligne %d a %d colonne(s) au lieu de %d. "
                         "⛔ Un lecteur permissif aurait DECALE les colonnes en silence."
                         % (n, len(ch), len(COLONNES)))
            lignes.append({c: (None if v == "" else float(v))
                           for c, v in zip(COLONNES, ch)})
    print("[w2] CSV relu : %d ligne(s), %d colonnes VERIFIEES" % (len(lignes), len(COLONNES)))
    return lignes


def main():
    for f in (sys.stdout, sys.stderr):
        try:
            f.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=16.0)
    ap.add_argument("--csv", default=None)
    ap.add_argument("--rejuger", default=None,
                    help="re-juge un CSV existant SANS re-tirer")
    ap.add_argument("--periode-lhm", type=float, default=0.0, metavar="S",
                    help="periode de rafraichissement de LHM, MESUREE ailleurs, "
                         "a utiliser pour --rejuger (⛔ jamais supposee)")
    ap.add_argument("--cadence", type=float, default=0.0, metavar="S",
                    help="mesure SEULEMENT la cadence propre de LHM, sur S "
                         "secondes, sur les QUATRE grandeurs")
    a = ap.parse_args()

    if a.rejuger:
        if not a.periode_lhm:
            print("[w2] ⚠️ --periode-lhm absente : C2 sera NON JUGEABLE. ⛔ On ne "
                  "suppose pas la cadence.")
        else:
            print("[w2] periode LHM FOURNIE : %.2f s (⚠️ mesuree ailleurs, ⛔ pas "
                  "supposee) => plafond atteignable %.1f %% a 1 Hz"
                  % (a.periode_lhm, 100.0 / a.periode_lhm))
        analyser(relire_csv(a.rejuger), a.periode_lhm or None)
        return 0

    if a.cadence:
        print("=" * 84)
        print("CADENCE PROPRE DE LHM — \u26d4 mesuree, PAS supposee")
        print("=" * 84)
        cadence_lhm(Lhm(), secondes=a.cadence, periode=0.1, toutes=True)
        return 0

    print("=" * 84)
    print("dn4-8 / AC4 — QUALIFICATION W2 des quatre grandeurs LHM")
    print("=" * 84)
    print("[w2] seuils GELES  degC : C1>=3,0 · C2>=25 %% · C3>=0,5"
          .replace("%%", "%"))
    print("[w2] seuils GELES  rpm  : C1>=5   · C2>=10 %% · C3>=1,0"
          .replace("%%", "%"))
    print("[w2] \u26d4 AUCUNE CHARGE N'EST PROVOQUEE PAR CET INSTRUMENT. La phase de "
          "charge, s'il y en a une, est un GESTE OWNER.")
    lhm = Lhm()
    periode = cadence_lhm(lhm)
    if not periode:
        print("[w2] ⛔ CADENCE NON MESUREE : C2 sera NON JUGEABLE. ⛔ On ne retombe "
              "PAS sur un seuil absolu — il mesurerait notre echantillonnage.")

    f = None
    if a.csv:
        f = io.open(a.csv, "w", encoding="utf-8", newline="")
        f.write(";".join(COLONNES) + "\n")
        f.flush()
    print("[w2] tir : %.1f min a 1 Hz (n vise = %d)" % (a.minutes, int(a.minutes * 60)))
    sys.stdout.flush()

    lignes, t0, prochain, pannes = [], time.monotonic(), time.monotonic(), 0
    try:
        while time.monotonic() - t0 < a.minutes * 60.0:
            prochain += 1.0
            try:
                e = echantillon(lhm.lire())
            except Exception as exc:
                pannes += 1
                if pannes == 1:
                    print("[w2] \u26a0\ufe0f lecture LHM en ECHEC (%s) — comptee, la session "
                          "continue" % type(exc).__name__)
                e = {c: None for c in COLONNES if c != "t_s"}
            e["t_s"] = round(time.monotonic() - t0, 2)
            lignes.append(e)
            if f:
                f.write(";".join("" if e[c] is None else repr(e[c])
                                 for c in COLONNES) + "\n")
                f.flush()
            d = prochain - time.monotonic()
            if d > 0:
                time.sleep(d)
    except KeyboardInterrupt:
        print("\n[w2] \u26a0\ufe0f interrompu — la session est JUGEE sur ce qui a ete "
              "capture (n=%d), et le n est PUBLIE" % len(lignes))
    finally:
        if f:
            f.close()

    print("\n[w2] n=%d echantillon(s), %d lecture(s) en echec" % (len(lignes), pannes))
    if len(lignes) < 900:
        print("[w2] \u26a0\ufe0f n < 900 : le critere gele annoncait n >= 900. ⛔ Le verdict "
              "ci-dessous vaut pour CE n, et il est publie avec.")
    analyser(lignes, periode)
    print("\n\u26a0\ufe0f TIR AU REPOS — decision owner du 2026-08-21. La phase de CHARGE "
          "exigee par le critere N'EST PAS couverte.")
    print("   \u26d4 Une NON-qualification est donc NON CONCLUANTE (une session plate "
          "n'est pas une sonde morte).")
    print("   \u2705 Une QUALIFICATION, elle, reste VALIDE : ce qui bouge assez au repos "
          "bouge a fortiori sous charge.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

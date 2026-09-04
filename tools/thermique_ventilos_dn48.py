r"""
=============================================================================
 thermique_ventilos_dn48.py -- AC3 : QUEL CANAL SUIT LA TEMPERATURE CPU ?
=============================================================================

 LE PROBLEME. LHM ne livre que `Fan #1`..`Fan #6`, et il n'existe AUCUNE table
 pour cette carte : MS-7885 est absente de `Model.cs`, et les noms semantiques
 du pilote Nuvoton (CPU FAN, PUMP, SYSFAN1-7) ne valent que pour la puce
 NCT6687DR, pas pour notre NCT6792D. Le code de LHM le dit lui-meme a propos des
 registres MSI : « Not sure of next 8, MSI won't provide info ».

 L'IDEE. Le canal du ventirad est LE SEUL dont le PWM suit la TEMPERATURE CPU.
 ⇒ on n'a rien a provoquer : on ENREGISTRE pendant que l'owner utilise sa
   machine, et le canal asservi se designe par sa CORRELATION.

 🔴 ⛔ CE SCRIPT NE PROVOQUE RIEN, N'ECRIT RIEN, NE TOUCHE A RIEN.
    Pas de charge CPU (refus owner explicite du 2026-08-21, et il a raison :
    ce n'etait pas dans ce qu'il avait autorise), pas de PWM force, aucun
    controle pris. Lecture seule, par /metrics -- l'interface retenue en AC2.
    ⇒ Il exerce donc AUSSI cette interface en regime, ce qui servira a AC9.

 -----------------------------------------------------------------------------
 DEUX GARDES QUE CE DEPOT A DEJA PAYEES
 -----------------------------------------------------------------------------
 · DUREE BORNEE, et bornee EN DUR. ⛔ Jamais de boucle infinie lancee depuis
   WSL : un harnais laisse tourner a survecu a sa session et a laisse des
   dizaines de processus zombies. Ici le script s'arrete SEUL.
 · SON PID EST ECRIT dans un fichier a cote du CSV, pour qu'on puisse l'arreter
   sans le chercher.

 -----------------------------------------------------------------------------
 CE QUE L'ANALYSE REFUSE DE CONCLURE
 -----------------------------------------------------------------------------
 · Si la temperature CPU n'a pas assez BOUGE pendant l'enregistrement, une
   correlation ne veut RIEN dire. Seuil ecrit d'avance : etendue >= 10 degC.
   En dessous : « NON CONCLUANT », et ⛔ pas un classement quand meme.
 · Si PLUSIEURS canaux correlent aussi fort, ca n'identifie PAS : sur MSI, un
   SYS_FAN peut etre asservi a la source CPU. Le script le DIT au lieu de
   designer le premier du classement.
 · Une correlation n'est pas une causalite. Le verdict reste une PRESOMPTION,
   a confirmer par un geste physique.

 EMPLOI
   python thermique_ventilos_dn48.py --heures 6 --periode 5
   python thermique_ventilos_dn48.py --analyser <csv>

 -----------------------------------------------------------------------------
 OU VA LE CSV, ET POURQUOI -- dn5-3 / AC3.2.c, 2026-09-04
 -----------------------------------------------------------------------------
 Le defaut de `--csv` est `tempfile.gettempdir()` + `dn48_thermique.csv`.
 (!) SOUS WINDOWS, `gettempdir()` REND LE `Temp` DE L'UTILISATEUR COURANT --
     c'est-a-dire `C:\Users\<qui-que-ce-soit>\AppData\Local\Temp`. C'EST LE
     MEME DOSSIER QU'AVANT chez l'owner, et un dossier qui existe pour tout le
     monde. Ailleurs, c'est `TMPDIR` s'il est pose sur un repertoire existant,
     et `/tmp` sinon.
     [CORRIGE A LA REVUE DU 2026-09-04 : cette ligne disait « Ailleurs, c'est
      /tmp » sans condition. MESURE : `tempfile.gettempdir()` honore `TMPDIR`.]
 (!) AVANT le 2026-09-04 ce defaut etait ECRIT EN DUR sur le profil Windows de
     l'auteur. Comme `enregistrer()` OUVRE un chemin EN ECRITURE, il mourait sur
     la machine de quelqu'un d'autre.
     [CORRIGE A LA REVUE DU 2026-09-04 -- ⛔ LA LIGNE D'ORIGINE EST FAUSSE ET
      ELLE EST NOMMEE PLUTOT QU'EFFACEE. Elle disait : « l'echec etait TARDIF :
      le script demarrait, imprimait son en-tete et le chemin, puis mourait a la
      premiere ligne ecrite ». IL NE DEMARRE PAS : `enregistrer()` ecrit d'abord
      `<csv>.pid` (l.164-165), AVANT le premier `print` (l.167). MESURE :
      rc=1, stdout VIDE, `FileNotFoundError` sur le `.pid`. ⇒ l'echec est
      IMMEDIAT ET MUET, et la distinction « TROIS comportements, pas deux »
      face a bench_lisseur (muet lui aussi) NE TIENT PAS.]
 (!) L'OPTION `--csv` N'A PAS BOUGE : elle reste le moyen de choisir. Seul son
     DEFAUT a change.
=============================================================================
"""

import argparse
import csv
import tempfile
import http.client
import math
import os
import re
import sys
import time

HOTE, PORT = "localhost", 8085
PUCE = "/lpc/nct6792d/0"
CPU = "/intelcpu/0"

# Ce qu'on enregistre. ⛔ Liste EXPLICITE : un enregistreur qui prend « tout »
# produit un CSV qu'on ne sait plus relire six mois apres.
COLONNES = (
    [("cpu_pkg", CPU + "/temperature/10"), ("cpu_max", CPU + "/temperature/0"),
     ("cpu_moy", CPU + "/temperature/1"), ("cpu_load", CPU + "/load/0"),
     ("gpu_temp", "/gpu-amd/0/temperature/0"), ("gpu_fan", "/gpu-amd/0/fan/0")]
    + [("fan%d" % i, "%s/fan/%d" % (PUCE, i)) for i in range(6)]
    + [("pwm%d" % i, "%s/control/%d" % (PUCE, i)) for i in range(6)]
)

_LIGNE = re.compile(
    r'^lhm_\S+\s+\{.*?"sensorId"="([^"]*)".*?"hardwareId"="([^"]*)".*?\}\s+(\S+)\s*$'
)



def _fini(x):
    """`True` si `x` est un reel utilisable. ⛔ NaN et inf n'en sont pas.

    🔴 UN SEUL ENDROIT (2e revue, 2026-08-24). La regle etait ecrite EN LIGNE
       dans `Lecteur.lire()` et NULLE PART dans `analyser()` — d'ou le
       contournement `nan < 10.0 -> False` reste ouvert sur le chemin
       `--analyser`. La recopier une 2e fois aurait reproduit la classe de defaut
       que ce depot retire ailleurs (« un miroir recopie A LA MAIN »).
    """
    return x == x and x not in (float("inf"), float("-inf"))


class Lecteur:
    """/metrics en connexion PERSISTANTE -- l'interface retenue en AC2.
    Se reconnecte UNE fois : ce chemin-la est aussi le detecteur « LHM absent »."""

    def __init__(self):
        self.c = None

    def lire(self):
        for dernier in (False, True):
            try:
                if self.c is None:
                    self.c = http.client.HTTPConnection(HOTE, PORT, timeout=10.0)
                self.c.request("GET", "/metrics", headers={"Connection": "keep-alive"})
                rep = self.c.getresponse()
                txt = rep.read().decode("utf-8", "replace")
                if rep.will_close:
                    self.c.close()
                    self.c = None
                # 🔴 GARDE `_fini` + `try/float` AJOUTEES EN REVUE (2026-08-21).
                #    `float(m.group(3))` etait NU : un litteral `NaN` passait dans
                #    le CSV et empoisonnait min/max/etendue (imprimes `nan`), et
                #    surtout `nan < 10.0` vaut **False** — donc la porte « NON
                #    CONCLUANT » etait CONTOURNEE et les correlations tournaient
                #    sur des donnees empoisonnees.
                # ⛔ Et un `ValueError` sur une valeur malformee etait avale par
                #    l'`except Exception` de reconnexion : apres la 2e tentative
                #    la fonction rendait `None`, que l'enregistreur compte comme
                #    « LHM etait ABSENT » — un diagnostic FAUX pour un serveur qui
                #    a parfaitement repondu. Deux fautes contraires, meme ligne.
                t = {}
                for l in txt.splitlines():
                    if not l.startswith("lhm_"):
                        continue
                    m = _LIGNE.match(l)
                    if not m:
                        continue
                    try:
                        val = float(m.group(3))
                    except ValueError:
                        continue          # ⛔ pas une panne : une valeur illisible
                    if not _fini(val):
                        continue          # NaN / inf = « la source n'a pas ca »
                    t[m.group(2) + m.group(1)] = val
                return t
            except Exception:
                try:
                    if self.c:
                        self.c.close()
                except Exception:
                    pass
                self.c = None
                if dernier:
                    return None


def enregistrer(heures, periode, chemin):
    heures = min(heures, 12.0)          # ⛔ borne DURE, non negociable
    fin = time.time() + heures * 3600.0
    pid_f = chemin + ".pid"
    with open(pid_f, "w") as f:
        f.write(str(os.getpid()))
    print("=== ENREGISTREUR THERMIQUE (lecture seule) ===")
    print("  csv    : %s" % chemin)
    print("  pid    : %d  (ecrit dans %s)" % (os.getpid(), pid_f))
    print("  duree  : %.1f h, periode %.0f s -- ⛔ il s'arrete SEUL" % (heures, periode))
    print("  ⛔ aucune charge provoquee, aucun controle pris, lecture seule.")
    sys.stdout.flush()

    lec = Lecteur()
    n, absents = 0, 0
    try:
        with open(chemin, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["t"] + [c for c, _ in COLONNES])
            while time.time() < fin:
                t0 = time.time()
                tab = lec.lire()
                if tab is None:
                    absents += 1          # LHM absent : compte, ⛔ pas de ligne inventee
                else:
                    w.writerow(["%.1f" % t0] +
                               ["" if tab.get(i) is None else "%.4f" % tab[i]
                                for _, i in COLONNES])
                    f.flush()
                    n += 1
                time.sleep(max(0.0, periode - (time.time() - t0)))
    except KeyboardInterrupt:
        print("  interrompu au clavier.")
    finally:
        try:
            os.remove(pid_f)
        except OSError:
            pass
        print("  %d echantillons ecrits, %d lectures ou LHM etait ABSENT." % (n, absents))


def _pearson(xs, ys):
    p = [(a, b) for a, b in zip(xs, ys) if a is not None and b is not None]
    if len(p) < 10:
        return None
    mx = sum(a for a, _ in p) / len(p)
    my = sum(b for _, b in p) / len(p)
    sxy = sum((a - mx) * (b - my) for a, b in p)
    sxx = sum((a - mx) ** 2 for a, _ in p)
    syy = sum((b - my) ** 2 for _, b in p)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def analyser(chemin):
    with open(chemin, encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    if len(lignes) < 30:
        print("⛔ %d echantillons : trop peu pour conclure quoi que ce soit." % len(lignes))
        return

    def col(nom):
        # 🔴 2e REVUE (2026-08-24) — LE CONTOURNEMENT `nan < 10.0 -> False` ETAIT
        #    RESTE OUVERT SUR LE CHEMIN D'ANALYSE. La garde `try/float` + `_fini`
        #    n'avait ete posee que dans `Lecteur.lire()` (L'ACQUISITION), avec ce
        #    motif exact : « `nan < 10.0` vaut False — donc la porte NON CONCLUANT
        #    etait CONTOURNEE et les correlations tournaient sur des donnees
        #    empoisonnees ». Or `--analyser <csv>` relit N'IMPORTE QUEL CSV, y
        #    compris ceux enregistres AVANT ce correctif, et faisait `float(v)` nu.
        #    Consequence mesuree : `etendue = nan` ⇒ `nan < 10.0` False ⇒ porte
        #    « NON CONCLUANT » franchie ⇒ `_pearson` rend `nan` ⇒
        #    `valides[0][1] < 0.5` False ⇒ porte « AUCUN canal » franchie ⇒
        #    « 🎯 control/N se detache (r = nan) », sur un tri par cle `nan`.
        # ⇒ UNE VALEUR NON FINIE EST UNE ABSENCE, comme a l'acquisition.
        out = []
        for l in lignes:
            v = l.get(nom, "")
            if v in ("", None):
                out.append(None)
                continue
            try:
                x = float(v)
            except (TypeError, ValueError):
                out.append(None)
                continue
            out.append(x if _fini(x) else None)
        return out

    cpu = col("cpu_pkg")
    vus = [v for v in cpu if v is not None]
    # 🔴 GARDE AJOUTEE EN REVUE (2026-08-21) : une session ou
    #    `/intelcpu/0/temperature/10` n'a JAMAIS ete expose (LHM non eleve tout du
    #    long) ecrit une cellule vide a chaque ligne, PASSE le garde-fou
    #    `len(lignes) < 30`, et mourait sur `max(vus)` en
    #    `ValueError: max() arg is an empty sequence` — sans JAMAIS atteindre le
    #    message « NON CONCLUANT » qui existe precisement pour ce cas.
    # ⛔ Un instrument doit REFUSER DE CONCLURE, ⛔ pas planter : un plantage se lit
    #    comme un bug d'outil, alors que l'information est « la sonde etait muette ».
    if len(vus) < 2:
        print("=== ANALYSE ===")
        print("  🔴 NON CONCLUANT : %d echantillon(s) de `cpu_pkg` sur %d ligne(s)."
              % (len(vus), len(lignes)))
        print("     La sonde de temperature CPU n'a (quasiment) jamais rendu de")
        print("     valeur — LHM non eleve pendant la session ? ⛔ NE PAS conclure")
        print("     sur les ventilateurs : il n'y a pas de variable a correler.")
        return
    etendue = max(vus) - min(vus)
    duree = (float(lignes[-1]["t"]) - float(lignes[0]["t"])) / 3600.0

    print("=== ANALYSE ===")
    print("  %d echantillons sur %.2f h" % (len(lignes), duree))
    print("  temperature CPU : %.1f -> %.1f degC, ETENDUE %.1f degC"
          % (min(vus), max(vus), etendue))
    if etendue < 10.0:
        print()
        print("  🔴 NON CONCLUANT. Le seuil etait ECRIT D'AVANCE : etendue >= 10 degC.")
        print("     Une correlation calculee sur un CPU qui n'a pas bouge ne mesure")
        print("     que du bruit. ⛔ On ne publie PAS un classement quand meme.")
        print("     ⇒ laisser tourner plus longtemps, ou pendant un usage plus charge.")
        return

    print()
    print("  correlation du PWM de chaque canal avec la temperature CPU :")
    scores = []
    for i in range(6):
        r = _pearson(cpu, col("pwm%d" % i))
        rg = _pearson(col("gpu_temp"), col("pwm%d" % i))
        scores.append((i, r, rg))
        print("    control/%d : r(CPU) = %s   r(GPU) = %s"
              % (i, "  n/a" if r is None else "%+.3f" % r,
                 "  n/a" if rg is None else "%+.3f" % rg))

    valides = [(i, r) for i, r, _ in scores if r is not None]
    valides.sort(key=lambda x: -x[1])
    print()
    if not valides or valides[0][1] < 0.5:
        print("  🔴 AUCUN canal ne suit franchement le CPU (meilleur r = %s)."
              % ("n/a" if not valides else "%+.3f" % valides[0][1]))
        print("     ⛔ Ne rien conclure. La courbe BIOS peut etre asservie a une")
        print("        autre sonde (VRM, systeme), ou etre quasi plate.")
        return
    tete = [x for x in valides if x[1] >= valides[0][1] - 0.10]
    if len(tete) > 1:
        print("  🔴 %d canaux correlent a moins de 0,10 d'ecart : %s"
              % (len(tete), ", ".join("control/%d (%+.3f)" % (i, r) for i, r in tete)))
        print("     ⛔ CA N'IDENTIFIE PAS. Sur MSI, un SYS_FAN peut etre asservi a la")
        print("        source CPU comme le CPU_FAN. Un geste physique reste necessaire.")
    else:
        i, r = valides[0]
        print("  🎯 control/%d se detache (r = %+.3f), le suivant est a %+.3f."
              % (i, r, valides[1][1] if len(valides) > 1 else float("nan")))
        print("     ⚠️ PRESOMPTION, ⛔ pas une preuve : une correlation n'est pas une")
        print("        causalite. A confirmer par un geste physique.")


def main():
    for f in (sys.stdout, sys.stderr):
        try:
            f.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--heures", type=float, default=6.0)
    ap.add_argument("--periode", type=float, default=5.0)
    # ── dn5-3 / AC3.2.c — LE DEFAUT DE `--csv` NE NOMME PLUS PERSONNE ──────
    #
    # 🔴 AVANT le 2026-09-04 ce defaut valait
    #    `C:\Users\<le-compte-Windows-de-l-auteur>\AppData\Local\Temp\` — son
    #    profil WINDOWS. ⚠️ ⛔ LE NOM DE COMPTE N'EST PAS RECOPIE ICI : le citer
    #    le REINTRODUIRAIT dans l'arbre publie, et l'inventaire suivant le
    #    compterait. ⛔ Il n'est EFFACE de nulle part pour autant (NFR3) — la
    #    valeur exacte se relit dans l'historique git et dans les captures de
    #    `mesures/dn5-3/`, qui sont gardees precisement pour ca. `enregistrer()` OUVRE ce chemin EN ECRITURE
    #    (`open(chemin, "w", ...)`) ⇒ sur la machine de quelqu'un d'autre,
    #    `FileNotFoundError`.
    # 🔴 CORRIGE A LA REVUE DE CODE DU 2026-09-04 — ⛔ LA LIGNE D'ORIGINE N'EST
    #    PAS EFFACEE, ELLE EST NOMMEE COMME FAUSSE. Elle disait : « son echec
    #    est PIRE que celui des deux autres parce qu'il est TARDIF : celui-ci
    #    DEMARRE, imprime son en-tete, imprime `csv : …`, et ne meurt qu'a la
    #    premiere ecriture ⇒ TROIS comportements, ⛔ pas deux ».
    # ⚠️ MESURE : IL NE DEMARRE PAS. `enregistrer()` ecrit `<csv>.pid` en l.165,
    #    AVANT le premier `print` de l.167. Rejoue avec un `--csv` vers un
    #    repertoire inexistant : rc=1, **stdout VIDE**, `FileNotFoundError` sur
    #    le `.pid`. ⇒ l'echec est IMMEDIAT ET MUET — le MEME comportement
    #    observable que `bench_lisseur_dn45.py`, qui meurt a l'`import`.
    #    ⇒ DEUX comportements, ⛔ pas trois.
    # 🔬 POURQUOI PERSONNE NE L'A VU : l'instrument de `dn5-3` cherchait
    #    `open(chemin, "w"` et n'a JAMAIS regarde `open(pid_f, "w")`. Il est
    #    desormais verse au depot (`tools/inventaire_motif_dn53.py`) et il liste
    #    les DEUX ouvertures.
    # ✅ `tempfile.gettempdir()` rend le meme dossier qu'avant chez l'owner :
    #    sous Windows il resout `TMPDIR`, puis `TEMP`, puis `TMP` — en pratique
    #    `C:\Users\<l-utilisateur-courant>\AppData\Local\Temp`. Ailleurs il
    #    rend `TMPDIR` s'il designe un repertoire existant, et `/tmp` sinon.
    # ⚠️ CORRIGE A LA REVUE DU 2026-09-04 — la ligne d'origine concluait
    #    « ⇒ ⛔ AUCUN changement de comportement sur la tour », au present de
    #    l'indicatif. ⛔ CE N'EST PAS MESURE : `mesures/dn5-3/T7-temoin-apres.txt`
    #    l.145-147 declare elle-meme que cet outil NE SE REJOUE PAS (il lit
    #    /metrics sur la tour, sous Windows). Il n'a donc ete execute NI avant NI
    #    apres, sur aucune machine. ⇒ le comportement identique est PLAUSIBLE et
    #    documente par le comportement de `gettempdir()`, ⛔ il n'est pas mesure,
    #    et ce depot ecrit la difference.
    # ⛔ L'OPTION `--csv` N'EST PAS RETIREE : elle reste le moyen de choisir.
    #    Seul son DEFAUT change.
    ap.add_argument("--csv",
                    default=os.path.join(tempfile.gettempdir(), "dn48_thermique.csv"))
    ap.add_argument("--analyser")
    a = ap.parse_args()
    if a.analyser:
        analyser(a.analyser)
    else:
        enregistrer(a.heures, a.periode, a.csv)
    return 0


if __name__ == "__main__":
    sys.exit(main())

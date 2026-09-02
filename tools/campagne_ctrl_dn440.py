# -*- coding: utf-8 -*-
"""dn4-40 / AC40.2 — AUCUN CONTROLE N'ANNONCE « OK » SANS AVOIR REGARDE.

Un `ctrl(True, …)` **litteral** ne peut pas rougir. Ce n'est pas un defaut en
soi : il peut *publier* un fait deja verifie, quand le chemin d'echec **sort en
amont**. Il en est un des que **un arbre defaillant peut l'atteindre**.

  ⇒ LE CRITERE, ECRIT AVANT LE TRI :
      LEGITIME — le chemin d'echec SORT EN AMONT (echec ferme). Le site publie
                 alors un fait que la gate vient de verifier.
      TROU     — un arbre defaillant ATTEINT le site, et il dit « OK » quand
                 meme. Le bilan enfle sans que rien ne soit garde.

🔴 ET LE CRITERE SE PROUVE PAR MUTANT, ⛔ PAS PAR RAISONNEMENT. C'est le motif
   « la claim etait VRAIE, elle n'etait pas PROUVEE ». Pour chaque site declare
   LEGITIME, on REPLANTE la faute que sa garde amont est censee attraper, et le
   temoin est que **le site n'apparait pas dans la trace** : la gate est sortie
   avant. Pour chaque site declare TROU, on vide sa population et le temoin est
   qu'il est **toujours trace OK**.

⚠️ ⛔ AUCUNE ECRITURE DANS L'ARBRE REEL. Chaque mutant travaille dans un arbre
   TEMPORAIRE monte par `git archive HEAD` — donc **commiter avant de mesurer**.
   `managed_components/` (gitignore, 186 Mo) est LIE, ⛔ pas copie.

Usage :  python3 tools/campagne_ctrl_dn440.py [--cockpit CHEMIN]
"""
import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
REL_LED = "_bmad-output/implementation-artifacts/deferred-work.md"
REL_TRK = "_bmad-output/implementation-artifacts/sprint-status-desknode.yaml"
REL_MAN = "_bmad-output/implementation-artifacts/dn4-16-arbitrage-ledger.md"
LVGL = "firmware/desknode/managed_components"


# ── LES MUTATIONS, une par site ─────────────────────────────────────────────
def m_rien(arbre, ck):
    return []


def m_ledger_absent(arbre, ck):
    os.remove(os.path.join(ck, REL_LED))
    return []


def m_ledger_binaire(arbre, ck):
    with open(os.path.join(ck, REL_LED), "wb") as f:
        f.write(b"# ledger\n\xff\xfe pas de l'UTF-8\n")
    return []


def m_tracker_binaire(arbre, ck):
    with open(os.path.join(ck, REL_TRK), "wb") as f:
        f.write(b"development_status:\n  \xff\xfe: done\n")
    return []


def m_cockpit_absent(arbre, ck):
    return ["--cockpit", os.path.join(ck, "nulle-part")]


def m_hist_casse(arbre, ck):
    """REPLANTE une faute de compilation dans `dn_hist.c` — DANS LA COPIE."""
    p = os.path.join(arbre, "firmware/desknode/main/dn_hist.c")
    s = io.open(p, encoding="utf-8").read()
    io.open(p, "w", encoding="utf-8").write(
        s + "\n// mutant dn4-40 : un jeton qui ne compile pas\n$$$\n")
    return []


def m_capture_absente(arbre, ck):
    p = os.path.join(arbre, "mesures/dn4-5/T3-AC4.1-lissage-960.csv")
    if os.path.isfile(p):
        os.remove(p)
    return []


def m_liste_planchers_absente(arbre, ck):
    p = os.path.join(arbre, "firmware/desknode/main/dn_env.h")
    s = io.open(p, encoding="utf-8").read()
    io.open(p, "w", encoding="utf-8").write(
        re.sub(r"Les trois planchers du d.p.t\s*:", "Les trois seuils :", s))
    return []


def m_exemptions_vides(arbre, ck):
    """Vide la POPULATION du site, ⛔ ne debranche pas la garde."""
    p = os.path.join(arbre, "firmware/desknode/main/dn_ui.c")
    s = io.open(p, encoding="utf-8").read()
    io.open(p, "w", encoding="utf-8").write(
        s.replace("DN_VERROU_EXEMPT", "DN_VERROU_ABSENT"))
    return []


# (gate, site, libelle attendu, verdict attendu, mutation, ce qu'elle replante)
CAS = [
    ("tools/verif_ledger_dn416.py", 796, "LEGITIME", m_ledger_absent,
     "le ledger retire du cockpit ⇒ prerequis absent, rc=4, sortie EN AMONT"),
    ("tools/verif_ledger_dn416.py", 797, "LEGITIME", m_ledger_absent,
     "idem — les 3 sites partagent la meme garde amont"),
    ("tools/verif_ledger_dn416.py", 798, "LEGITIME", m_ledger_absent,
     "idem"),
    ("tools/verif_ledger_dn416.py", 817, "LEGITIME", m_ledger_binaire,
     "le ledger rendu NON-UTF-8 ⇒ ctrl(False) puis ARRET"),
    ("tools/verif_ledger_dn416.py", 824, "LEGITIME", m_tracker_binaire,
     "le tracker rendu NON-UTF-8 ⇒ ctrl(False) puis ARRET"),
    ("tools/verif_dossier_dn415.py", 702, "LEGITIME", m_cockpit_absent,
     "`--cockpit` vers un chemin inexistant ⇒ la branche `absent` est prise"),
    ("tools/verif_hist_dn413.py", 701, "LEGITIME", m_hist_casse,
     "`dn_hist.c` rendu incompilable ⇒ ctrl(False) puis `return 1`"),
    ("tools/verif_lissage_dn45.py", 187, "LEGITIME", m_capture_absente,
     "la capture retiree ⇒ ctrl(False) puis `return 1`"),
    ("tools/verif_paliers_dn441.py", 324, "LEGITIME", m_liste_planchers_absente,
     "la liste canonique retiree ⇒ la branche `dire(False)` est prise"),
    ("tools/verif_verrou_lvgl_dn413.py", 556, "TROU", m_exemptions_vides,
     "population VIDEE : le site disparait avec elle ⇒ il ne GARDE rien"),
    ("tools/verif_dossier_dn415.py", 728, "TROU", m_rien,
     "aucune donnee ne peut le rendre faux — il PUBLIE, il ne controle pas"),
    ("tools/verif_journal_soak_dn45.py", 225, "TROU", m_rien,
     "declaration de limite : aucune donnee ne peut la rendre fausse"),
    ("tools/verif_dossier_d5_dn45.py", 203, "TROU", m_rien,
     "aucune donnee ne peut le rendre faux ; ⚠️ ses chemins sont ABSOLUS "
     "(dn5-3) ⇒ il lit l'arbre REEL meme depuis une copie"),
]


def monte_arbre(tmp):
    a = os.path.join(tmp, "arbre")
    os.makedirs(a)
    tar = subprocess.run(["git", "archive", "HEAD"], cwd=RACINE,
                         capture_output=True)
    subprocess.run(["tar", "-x", "-C", a], input=tar.stdout, check=True)
    src = os.path.join(RACINE, LVGL)
    if os.path.isdir(src):
        os.symlink(src, os.path.join(a, LVGL))
    return a


def monte_cockpit(tmp, ck_src):
    c = os.path.join(tmp, "cockpit")
    os.makedirs(os.path.join(c, os.path.dirname(REL_LED)))
    for rel in (REL_LED, REL_TRK, REL_MAN):
        s = os.path.join(ck_src, rel)
        if os.path.isfile(s):
            shutil.copy(s, os.path.join(c, rel))
    return c


def joue(gate, mutation, ck_src):
    tmp = tempfile.mkdtemp(prefix="dn440ctrl-")
    try:
        a = monte_arbre(tmp)
        c = monte_cockpit(tmp, ck_src)
        extra = mutation(a, c)
        tr = os.path.join(tmp, "trace.txt")
        args = [sys.executable, os.path.join(a, gate)]
        if "--cockpit" in extra:
            args += extra
        elif gate.endswith(("dn416.py", "dn415.py")):
            args += ["--cockpit", c]
        p = subprocess.run(args, capture_output=True, text=True, cwd=a,
                           env=dict(os.environ, DN_TRACE_CTRL=tr))
        vus = {}
        if os.path.isfile(tr):
            for l in io.open(tr, encoding="utf-8"):
                q = l.rstrip("\n").split("\t")
                if len(q) == 3:
                    vus[q[0]] = q[1]
        return p.returncode, vus
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cockpit", default=os.path.join(
        os.environ.get("HOME") or "/nonexistent", "projects", "compagnon_project"))
    a = ap.parse_args()

    print("=" * 78)
    print("dn4-40 / AC40.2 — TRI DES `ctrl(True, …)` LITTERAUX, PROUVE PAR MUTANT")
    print("=" * 78)
    print("critere : LEGITIME = le chemin d'echec SORT EN AMONT ;")
    print("          TROU     = un arbre defaillant ATTEINT le site.")
    print("⛔ aucune ecriture dans l'arbre reel — `git archive HEAD` + copie.")
    print()

    base = {}
    echecs = []
    for gate, site, verdict, mut, quoi in CAS:
        cle = "%s:%d" % (os.path.basename(gate), site)
        if gate not in base:
            rc, vus = joue(gate, m_rien, a.cockpit)
            base[gate] = vus
        atteint_propre = cle in base[gate]
        rc, vus = joue(gate, mut, a.cockpit)
        atteint_mute = cle in vus
        if verdict == "LEGITIME":
            bon = atteint_propre and not atteint_mute
            dit = ("PROUVE — atteint sur l'arbre propre, ⛔ PAS atteint sous"
                   " mutant (rc=%d)" % rc) if bon else \
                  ("⛔ NON PROUVE — propre:%s mute:%s (rc=%d)"
                   % (atteint_propre, atteint_mute, rc))
        else:
            bon = atteint_propre and (atteint_mute or mut is m_exemptions_vides)
            dit = ("CONFIRME TROU — %s" %
                   ("toujours atteint OK sous mutant"
                    if atteint_mute else "population videe, plus rien a garder")) \
                if bon else "⛔ RECLASSER — propre:%s mute:%s" % (atteint_propre,
                                                                 atteint_mute)
        if not bon:
            echecs.append(cle)
        print("  [%s] %-8s %-36s %s" % ("OK" if bon else "!!", verdict, cle, dit))
        print("           mutant : %s" % quoi)

    n_leg = sum(1 for c in CAS if c[2] == "LEGITIME")
    n_trou = sum(1 for c in CAS if c[2] == "TROU")
    print("\n" + "=" * 78)
    print("BILAN TRI : %d site(s) — %d LEGITIME(S), %d TROU(S), %d echec(s)"
          % (len(CAS), n_leg, n_trou, len(echecs)))
    print("=" * 78)
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())

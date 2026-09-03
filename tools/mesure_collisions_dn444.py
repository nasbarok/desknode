# -*- coding: utf-8 -*-
"""dn4-44 — CE QUE LE DISCRIMINANT DE CLE DE TRACE CHANGE, GATE PAR GATE.

🔴 POURQUOI CE FICHIER EXISTE — REVUE DE CODE DU 2026-09-03. La story publiait
`mesures/dn4-44/T1-collisions-cle-de-trace.txt` et ses chiffres (**79**
controles demasques, `verif_verrou_lvgl_dn413.py` : 10 sites ⇒ 60 cles) etaient
JUSTES — ils ont ete reproduits a l'identique a la revue. ⛔ Mais AUCUN RUNNER
DU DEPOT NE LES PRODUISAIT : la capture avait ete faite par un script ad hoc,
absent de l'arbre et absent de la File List.

⚠️ « Un chiffre qui n'est pas adosse a un fichier de mesure NOMME ne s'ecrit
   pas » dit la convention. Elle est incomplete, et la revue l'a montre : un
   fichier de mesure que RIEN NE SAIT REPRODUIRE n'est pas une mesure, c'est
   une capture. ⇒ celui-ci le rejoue.

⛔ CE N'EST PAS UNE GATE : il ne rend aucun verdict et son nom ⛔ ne matche pas
   `tools/verif_*.py`. Il MESURE, il ne garde pas.

Usage :  python3 tools/mesure_collisions_dn444.py
"""
import io
import os
import re
import subprocess
import sys
import tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI)
import dn_trace                                            # noqa: E402

MOTIF_INSTRUMENTEE = "import dn_trace"


def instrumentees():
    """Les gates qui portent l'instrument de trace — ⛔ decouvertes, pas listees."""
    out = []
    for f in sorted(os.listdir(os.path.join(RACINE, "tools"))):
        if not (f.startswith("verif_") and f.endswith(".py")):
            continue
        p = os.path.join(RACINE, "tools", f)
        if MOTIF_INSTRUMENTEE in io.open(p, encoding="utf-8").read():
            out.append(f)
    return out


def trace_de(gate, cockpit):
    """`[lignes de trace]` d'une gate jouee sur l'arbre REEL — lecture seule."""
    d = tempfile.mkdtemp(prefix="dn444col-")
    try:
        tr = os.path.join(d, "trace.txt")
        args = [sys.executable, os.path.join(RACINE, "tools", gate)]
        if gate.endswith(("dn416.py", "dn415.py")):
            args += ["--cockpit", cockpit]
        subprocess.run(args, capture_output=True, text=True, cwd=RACINE,
                       env=dict(os.environ, DN_TRACE_CTRL=tr))
        if not os.path.isfile(tr):
            return []
        return [l.rstrip("\n") for l in io.open(tr, encoding="utf-8")
                if l.strip()]
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


def main():
    cockpit = os.path.join(os.environ.get("HOME") or "/nonexistent",
                           "projects", "compagnon_project")
    for i, a in enumerate(sys.argv):
        if a == "--cockpit" and i + 1 < len(sys.argv):
            cockpit = sys.argv[i + 1]
    print("=" * 78)
    print("dn4-44 — CE QUE LE DISCRIMINANT DE CLE CHANGE, GATE PAR GATE")
    print("=" * 78)
    print("   AVANT = la cle etait `<basename>:<ligne>` SEULE ⇒ deux controles")
    print("           logiquement DIFFERENTS au meme site se REPLIAIENT sur une")
    print("           seule cle, et l'un des deux disparaissait du compte.")
    print("   APRES = la cle porte `(site, libelle)` — `dn_trace.cle()`.")
    print("   ⛔ Ce script MESURE, il ne garde rien. Il n'est pas une gate.")
    print()
    print("   %-32s %7s %7s %7s %8s"
          % ("gate", "lignes", "avant", "apres", "demasq."))
    t_lig = t_av = t_ap = 0
    for gate in instrumentees():
        lignes = trace_de(gate, cockpit)
        avant = {l.split(dn_trace.SEP)[0] for l in lignes
                 if dn_trace.SEP in l}
        # ⚠️ La cle NEUVE est fabriquee par `dn_trace.cle()` — ⛔ pas par un
        #    troisieme decoupage local : la lecture a UN proprietaire (AC5.5).
        apres = {dn_trace.cle(p[0], p[2])
                 for p in (l.split(dn_trace.SEP) for l in lignes)
                 if len(p) == 3}
        t_lig += len(lignes)
        t_av += len(avant)
        t_ap += len(apres)
        print("   %-32s %7d %7d %7d %8d"
              % (gate, len(lignes), len(avant), len(apres),
                 len(apres) - len(avant)))
    print("   %-32s %7d %7d %7d %8d"
          % ("TOTAL", t_lig, t_av, t_ap, t_ap - t_av))
    print()
    print("   ⚠️ « demasq. » = les controles que l'ANCIENNE cle confondait.")
    print("      Un ecart NUL sur une gate ne dit pas qu'elle allait bien : il")
    print("      dit que ses sites ne portent QU'UN libelle chacun.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

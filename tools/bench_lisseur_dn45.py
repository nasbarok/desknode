# -*- coding: utf-8 -*-
import os, sys, time, statistics
sys.stdout.reconfigure(encoding="utf-8")
# ── dn5-3 / AC3.2.a — LE CHEMIN DE L'AGENT SE DERIVE DE `__file__` ──────────
#
# 🔴 AVANT le 2026-09-04, cette ligne etait un chemin UNC ECRIT EN DUR :
#    `\\wsl.localhost\Ubuntu\home\<l-auteur>\projects\desknode\agent`.
#    ⚠️ ⛔ LE NOM D'UTILISATEUR N'EST PAS RECOPIE ICI — le citer le
#    REINTRODUIRAIT dans l'arbre publie. ⛔ Il n'est efface de nulle part
#    (NFR3) : la valeur exacte se relit dans l'historique git et dans
#    `mesures/dn5-3/T1-temoin-negatif.txt`.
#    Depuis un clone quelconque, `import dn_agent` mourait en
#    `ModuleNotFoundError` — MESURE le 2026-09-04, etage (i) du temoin
#    (`mesures/dn5-3/T1-temoin-negatif.txt`), rc **1**.
#    ⚠️ Le defaut etait DOUBLE : le chemin ET le fait que `import dn_agent` soit
#    au NIVEAU MODULE, donc joue a l'`import`. ⛔ L'import RESTE au niveau
#    module : ce qui change, c'est D'OU il vient.
# ⚠️ ⛔ PAS `expanduser("~")`, ⛔ PAS `$HOME` : ce fichier ne cherche pas un
#    foyer, il cherche LE DEPOT D'OU IL EST ATTEINT. `__file__` est la seule
#    source qui suit le clone.
# ⚠️ NUANCE AJOUTEE A LA REVUE DU 2026-09-04 : la ligne d'origine disait
#    « la seule source qui ne peut designer QUE cet arbre-la ». `abspath` ne
#    resout pas les liens symboliques ⇒ atteint par un lien, il designe le
#    parent du LIEN. ⛔ Le code n'est pas change : c'est l'idiome de ~40 outils
#    de ce depot, et aucun n'utilise `realpath`.
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agent"))
import dn_agent
lis = dn_agent.Lisseur()
photo = [("cpu",[152,32,667,425]), ("gpu",[130,450,520,6040]),
         ("ram",[527,319]), ("net",[0,0]), ("disk",[0,10030,3100,8760])]
N = 200000
for _ in range(2000): lis.appliquer(photo, 0)
m = []
for _ in range(5):
    t0 = time.perf_counter()
    for _ in range(N): lis.appliquer(photo, 0)
    m.append((time.perf_counter()-t0)/N)
us = statistics.median(m)*1e6
print("PYTHON DE LA TOUR : %s" % sys.version.split()[0])
print("cout MEDIAN d'un appel a Lisseur.appliquer() : %.2f us" % us)
print("  n = %d appels x 5 series ; etendue des series : %.2f us" % (N, (max(m)-min(m))*1e6))
print("  a 1 Hz ⇒ travail ajoute %.2f us/s = %.6f %% d'un coeur" % (us, us/1e6*100))

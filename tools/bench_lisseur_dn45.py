# -*- coding: utf-8 -*-
import sys, time, statistics
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"\\wsl.localhost\Ubuntu\home\nasbarok\projects\desknode\agent")
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

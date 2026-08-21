#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verif_source_lhm_dn48.py — eprouve `SourceLhm` et la trame, SANS la tour.

🔴 IL IMPORTE ET APPELLE LE CODE DU PRODUIT. ⛔ Il ne le REJOUE pas : une gate
   qui reimplemente ce qu'elle pretend verifier epingle VERT sa propre copie.
   Tout ce qui est mesure ici sort de `agent/dn_agent.py` tel qu'il est livre.

⛔ CE QU'IL NE PROUVE PAS, ET IL FAUT LE LIRE :
   · Il ne mesure AUCUNE grandeur de la tour. Le serveur en face est un STUB qui
     rejoue une capture n = 1. Les nombres servis ne qualifient RIEN (AC4).
   · Il ne solde PAS AC8 : « LHM absent » doit etre eprouve sur le VRAI service,
     coupe pendant que l'agent tourne. Ici on eprouve le CHEMIN DE CODE.
   · Il ne touche ni la carte, ni COM3, ni le vrai LHM.

✅ CE QU'IL PROUVE : la forme de la trame, le compte de grandeurs, le champ vide
   NON DECALE, le refus d'un negatif, le comportement au timeout, l'isolement
   (les autres metriques survivent), la reprise sans redemarrage, et la LONGUEUR
   REELLE des trames contre `DN_LINK_LIGNE_MAX`.

Usage :  python3 tools/verif_source_lhm_dn48.py
"""
import io
import os
import socket
import subprocess
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8086
LIGNE_MAX = 71          # miroir de `DN_LINK_LIGNE_MAX` (main/dn_link.h)

# 🔴 LE STUB `psutil` EST CHARGE ICI, ET IL CRIE. Sans lui, rien de tout ceci ne
#    tourne en WSL. ⚠️ Il fabrique cpu/ram/net/disk : ⛔ aucun de ces nombres n'est
#    une mesure, et c'est pour ca que ce fichier ne publie que des FORMES.
os.environ["DN_STUB_PSUTIL"] = "1"
# \U0001f534 DEFAUT D'INSTRUMENT MESURE LE 2026-08-21, ET IL EST GENERAL A TOUT HARNAIS
#    QUI IMPORTE LE PRODUIT : **PYTHON A SERVI UN BYTECODE PERIME**. Pendant un
#    test de mutation (BORNES 1500 -> 1400 puis restauration), `agent/__pycache__/
#    dn_agent.cpython-312.pyc` a continue de rendre `1400` alors que le `.py` sur
#    le disque disait `1500` — l'outil a donc VERIFIE UN FICHIER QUI N'EXISTAIT
#    PLUS, et il a conclu ROUGE sur un arbre SAIN. ⚠️ Dans l'autre sens il aurait
#    conclu VERT sur un arbre CASSE : c'est la famille « un instrument qui ne peut
#    pas voir ce qu'il pretend lire », et ce depot l'a deja payee (le `head` d'un
#    tube pour `exit 0`, le journal PowerShell en UTF-16LE).
# ⇒ DEUX PARADES, ET LA SECONDE EST LA VRAIE :
#    1. on n'ecrit ni ne lit de bytecode ici, et on purge celui qui traine ;
#    2. \U0001f3af **L'OUTIL PUBLIE L'EMPREINTE DE LA SOURCE QU'IL A REELLEMENT LUE.**
#       Un instrument qui ne nomme pas son sujet ne prouve rien sur ce sujet.
import hashlib
import shutil

sys.dont_write_bytecode = True
for _p in (os.path.join(RACINE, "agent", "__pycache__"),
           os.path.join(RACINE, "tools", "stub_psutil", "__pycache__")):
    shutil.rmtree(_p, ignore_errors=True)

_SRC_AGENT = os.path.join(RACINE, "agent", "dn_agent.py")
_SHA_AGENT = hashlib.sha256(
    io.open(_SRC_AGENT, "rb").read()).hexdigest()[:16]
sys.path.insert(0, os.path.join(RACINE, "tools", "stub_psutil"))
sys.path.insert(0, os.path.join(RACINE, "agent"))
import dn_agent  # noqa: E402  -- LE PRODUIT, importe tel quel

ECHECS = []


def verdict(nom, ok, detail=""):
    print("  [%s] %-52s %s" % ("OK " if ok else "\u2716\ufe0f ", nom, detail))
    if not ok:
        ECHECS.append(nom)


def lancer_stub(mode="normal", **kw):
    cmd = [sys.executable, os.path.join(RACINE, "tools", "stub_lhm_dn48.py"),
           "--port", str(PORT), "--mode", mode]
    for k, v in kw.items():
        cmd += ["--" + k, str(v)]
    p = subprocess.Popen(cmd, stderr=subprocess.DEVNULL)
    # \U0001f534 LA SONDE DE DEMARRAGE TESTE **L'ECOUTE**, ⛔ PAS LA REPONSE. Defaut
    #    d'instrument corrige le 2026-08-21 : la premiere version faisait un
    #    `GET` complet avec un timeout de 1 s, donc en mode `lent --retard 2.0`
    #    elle concluait « le stub n'a pas demarre » sur un stub PARFAITEMENT
    #    demarre — l'instrument mesurait la lenteur qu'il etait cense mettre en
    #    place. ⇒ un `connect()` TCP nu, qui ne depend d'aucune latence applicative.
    for _ in range(100):                      # attente ACTIVE et BORNEE
        time.sleep(0.05)
        try:
            socket.create_connection(("127.0.0.1", PORT), timeout=1.0).close()
            return p
        except OSError:
            if p.poll() is not None:
                break
    p.terminate()
    raise RuntimeError("le stub LHM n'a pas demarre sur %d" % PORT)


def tuer(p):
    if p is not None and p.poll() is None:
        p.terminate()
        try:
            p.wait(timeout=5)
        except Exception:
            p.kill()


def source(timeout_s=dn_agent.LHM_TIMEOUT_S):
    return dn_agent.SourceLhm(hote="127.0.0.1", port=PORT, timeout_s=timeout_s,
                              verbeux=False)


# ═══════════════════════════════════════════════════════════════════════════
def scenario_normal():
    print("\n== 1. LECTURE NOMINALE — les cinq sondes, et la FORME de la trame ==")
    p = lancer_stub("normal")
    try:
        src = source()
        vues = src.lire()
        verdict("les 5 sondes de LHM_SONDES sont rendues",
                sorted(vues) == sorted(c for c, _, _ in dn_agent.LHM_SONDES),
                str(sorted(vues)))
        connues = {k: v for k, v in vues.items() if v is not None}
        verdict("5/5 portent une valeur (fixture reelle)", len(connues) == 5,
                " ".join("%s=%.1f" % (k, v) for k, v in sorted(connues.items())))
        moy = src.extraction_moyenne(vues)
        att = (vues["fan.top_out"] + vues["fan.rear_out"]) / 2.0
        verdict("extraction_moyenne = moyenne des DEUX canaux",
                abs(moy - att) < 1e-9, "%.3f tr/min" % moy)

        col = dn_agent.Collecteur(verbeux=False, lhm_hote="127.0.0.1",
                                  lhm_port=PORT)
        photo = col.photo()
        photo = col.photo()                   # 2e tour : les debits existent
        d = dict(photo)
        verdict("la trame `cpu` porte QUATRE grandeurs", len(d["cpu"]) == 4,
                str(d["cpu"]))
        verdict("la trame `disk` porte QUATRE grandeurs", len(d["disk"]) == 4,
                str(d["disk"]))
        verdict("la °C CPU est en INDEX 3 (⛔ pas 2)",
                d["cpu"][3] is not None and d["cpu"][2] is not None
                and d["cpu"][2] <= 1000,
                "index2(c.max)=%s  index3(degC)=%s" % (d["cpu"][2], d["cpu"][3]))
        verdict("le Mo/s garde la POSITION 0 de `disk`", d["disk"][0] is not None,
                "v1=%s" % d["disk"][0])
        pire = 0
        for m, v in photo:
            t = dn_agent.trame(4294967295, 4294967295, m, v)
            pire = max(pire, len(t.rstrip("\n")))
        verdict("aucune trame REELLE ne depasse DN_LINK_LIGNE_MAX",
                pire <= LIGNE_MAX, "pire = %d o (max %d)" % (pire, LIGNE_MAX))
        col.fermer()
        src.fermer()
    finally:
        tuer(p)


def scenario_muette():
    print("\n== 2. UNE SONDE MUETTE — champ VIDE, et la SUIVANTE non decalee ==")
    p = lancer_stub("muette", sonde="/lpc/nct6792d/0/fan/1")   # CPU_NOCTUA
    try:
        col = dn_agent.Collecteur(verbeux=False, lhm_hote="127.0.0.1",
                                  lhm_port=PORT)
        col.photo()
        d = dict(col.photo())
        v = d["disk"]
        verdict("la grandeur muette est `None` (champ vide)", v[2] is None,
                str(v))
        verdict("la SUIVANTE n'est PAS decalee (boitier toujours en 3)",
                v[3] is not None, "v4=%s" % v[3])
        t = dn_agent.trame(1, 1, "disk", v)
        verdict("la trame porte bien un `,,` (⛔ pas une troncature)",
                ",," in t, t.strip())
        verdict("l'absence est COMPTEE, ⛔ pas silencieuse",
                col.lhm.absences.get("fan.cpu_noctua", 0) >= 1,
                str(col.lhm.absences))
        verdict("⛔ et ce n'est PAS comptee comme une panne",
                not col.pannes, str(col.pannes))
        col.fermer()
    finally:
        tuer(p)


def scenario_negatif():
    print("\n== 3. UNE VALEUR NEGATIVE — « je ne sais pas », ⛔ PAS un 0 ecrete ==")
    p = lancer_stub("negatif", sonde="/lpc/nct6792d/0/fan/2")   # CASE_GROUP
    try:
        col = dn_agent.Collecteur(verbeux=False, lhm_hote="127.0.0.1",
                                  lhm_port=PORT)
        col.photo()
        d = dict(col.photo())
        verdict("la valeur negative devient un champ VIDE", d["disk"][3] is None,
                str(d["disk"]))
        verdict("⛔ elle n'est PAS publiee comme 0 tr/min (fan-stop plausible)",
                d["disk"][3] != 0, "v4=%s" % d["disk"][3])
        verdict("le refus est compte sur SON propre compteur",
                col.lhm.absences.get("fan.case_group:negatif", 0) >= 1,
                str(col.lhm.absences))
        col.fermer()
    finally:
        tuer(p)


def scenario_lent():
    print("\n== 4. LECTURE LENTE — le timeout COUPE, et les 4 autres SURVIVENT ==")
    p = lancer_stub("lent", retard=2.0)
    try:
        col = dn_agent.Collecteur(verbeux=False, lhm_hote="127.0.0.1",
                                  lhm_port=PORT, lhm_timeout_s=0.4)
        t0 = time.perf_counter()
        col.photo()
        d = dict(col.photo())
        dt = time.perf_counter() - t0
        verdict("la lecture est COUPEE au timeout, ⛔ pas au retard du serveur",
                dt < 1.2, "2 cycles en %.2f s (retard servi 2,00 s/tir ; "
                          "2 x budget = 0,80 s)" % dt)
        verdict("la panne est COMPTEE et NOMMEE",
                any(k.startswith("lhm:") for k in col.pannes), str(col.pannes))
        verdict("le message n'est imprime QU'UNE fois par type",
                all(v >= 1 for v in col.pannes.values()),
                "compteur = %s" % col.pannes)
        verdict("🎯 `cpu` SURVIT (3 grandeurs sur 4, la °C dit « -- »)",
                "cpu" in d and d["cpu"][0] is not None and d["cpu"][3] is None,
                str(d.get("cpu")))
        verdict("🎯 `disk` SURVIT (le Mo/s tient la position 0)",
                "disk" in d and d["disk"][0] is not None
                and d["disk"][1] is None, str(d.get("disk")))
        verdict("🎯 `ram` et `net` sont INTACTES",
                d.get("ram") and d.get("net"),
                "ram=%s net=%s" % (d.get("ram"), d.get("net")))
        # \U0001f534 DEUX BORNES, ET C'EST LA SUPERIEURE QUI A TROUVE UN DEFAUT.
        #    La premiere version de ce controle n'avait que « >= 0,35 s » : elle
        #    a epingle VERT une lecture de **802 ms pour un timeout de 400 ms**
        #    (le plafond etait applique PAR TENTATIVE, et `_get` en fait deux).
        #    ⛔ Un controle sans borne superieure ne peut pas voir le defaut qu'il
        #    pretend exclure — c'est la question que ce depot a deja payee six fois.
        verdict("la lecture est coupee AU timeout, borne BASSE **et** HAUTE",
                0.35 <= col.lhm.duree_max <= col.lhm.timeout_s * 1.15,
                "max %.0f ms / timeout %.0f ms (plafond du controle %.0f ms)"
                % (col.lhm.duree_max * 1000, col.lhm.timeout_s * 1000,
                   col.lhm.timeout_s * 1150))
        col.fermer()
    finally:
        tuer(p)


def scenario_absent_puis_reprise():
    print("\n== 5. LHM ABSENT AU DEMARRAGE, PUIS QUI MONTE — reprise SANS "
          "redemarrer l'agent ==")
    col = dn_agent.Collecteur(verbeux=False, lhm_hote="127.0.0.1", lhm_port=PORT)
    d = dict(col.photo())
    verdict("la source n'est PAS condamnee (⛔ divergence voulue d'avec ADL)",
            col.lhm is not None, "lhm.reponses = %d" % col.lhm.reponses)
    verdict("aucune trame ne porte de valeur LHM",
            d["cpu"][3] is None, str(d["cpu"]))
    verdict("les 4 autres metriques vivent", len(d) >= 4, str(sorted(d)))
    p = lancer_stub("normal")
    try:
        col.photo()
        d = dict(col.photo())
        verdict("🎯 la °C CPU REPREND, sans redemarrer l'agent",
                d["cpu"][3] is not None, "index3 = %s" % d["cpu"][3])
        verdict("🎯 les tr/min REPRENNENT aussi",
                d["disk"][1] is not None, str(d["disk"]))
        verdict("les echecs precedents restent COMPTES (⛔ pas effaces)",
                col.lhm.echecs >= 1,
                "%d echec(s), %d reponse(s)" % (col.lhm.echecs, col.lhm.reponses))
        col.fermer()
    finally:
        tuer(p)


def scenario_arret_en_cours():
    print("\n== 6. LHM ARRETE EN COURS DE ROUTE — le cas le plus dur ==")
    p = lancer_stub("normal")
    col = None
    try:
        col = dn_agent.Collecteur(verbeux=False, lhm_hote="127.0.0.1",
                                  lhm_port=PORT)
        col.photo()
        d = dict(col.photo())
        verdict("avant l'arret : la °C est publiee", d["cpu"][3] is not None,
                "index3 = %s" % d["cpu"][3])
    finally:
        tuer(p)
    time.sleep(0.3)
    d = dict(col.photo())
    verdict("apres l'arret : la °C devient un champ VIDE",
            d["cpu"][3] is None, str(d["cpu"]))
    verdict("⛔ AUCUNE valeur figee n'a survecu (pas la derniere connue)",
            d["cpu"][3] is None and d["disk"][1] is None, str(d["disk"]))
    verdict("`ram`/`net`/`disk` continuent", len(d) >= 4, str(sorted(d)))
    col.fermer()


def main():
    for f in (sys.stdout, sys.stderr):
        try:
            f.reconfigure(encoding="utf-8")
        except Exception:
            pass
    print("=" * 76)
    print("dn4-8 / AC6 — EXERCICE DE `SourceLhm` CONTRE UN STUB")
    print("⛔ Aucun nombre de ce rapport n'est une mesure de la tour.")
    print("source exercee : agent/dn_agent.py sha256:%s" % _SHA_AGENT)
    print("=" * 76)
    scenario_normal()
    scenario_muette()
    scenario_negatif()
    scenario_lent()
    scenario_absent_puis_reprise()
    scenario_arret_en_cours()
    print("\n" + "=" * 76)
    if ECHECS:
        print("\u2716\ufe0f  %d CONTROLE(S) EN ECHEC : %s" % (len(ECHECS), ECHECS))
        return 1
    print("\u2705 tous les controles passent.")
    print("\u26a0\ufe0f  RAPPEL : AC8 n'est PAS solde par ce fichier — il exige le VRAI")
    print("   service coupe pendant que l'agent tourne, sur la tour.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

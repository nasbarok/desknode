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

_DN_LINK_H = os.path.join(RACINE, "firmware", "desknode", "main", "dn_link.h")


def _constante_c(nom):
    """🔴 LIT LA CONSTANTE DANS LE HEADER. ⛔ NE PAS LA RECOPIER ICI.

    Defaut trouve en revue (code review dn4-8, 2026-08-21) : ce fichier portait
    `LIGNE_MAX = 71  # miroir de DN_LINK_LIGNE_MAX`. Un miroir recopie A LA MAIN
    est une garde qui continue de verifier l'ANCIENNE valeur apres que la vraie a
    bouge — elle passe VERT sur un arbre ou la propriete est cassee. Son jumeau
    `recompte_trame_dn48.py` lisait deja la source ; celui-ci ne le faisait pas.
    """
    import re
    src = io.open(_DN_LINK_H, encoding="utf-8", errors="replace").read()
    # 🔴 2e REVUE (2026-08-24) — LA REGEX N'ETAIT NI ANCREE NI FERMEE :
    #    `re.search(r"#define\s+%s\s+\(?\s*(\d+)")` sans `^` ni `re.M`, donc LA
    #    PREMIERE OCCURRENCE DU FICHIER GAGNE, **commentaire compris** ; et
    #    `(\d+)` apres `\(?` lisait `64` dans `#define X (64 + 7)`. `dn_link.h`
    #    mentionne `DN_LINK_LIGNE_MAX` six fois AVANT son `#define` : la garde
    #    etait correcte AUJOURD'HUI et silencieusement fausse le jour ou une de
    #    ces lignes citerait la directive. ⛔ C'est la classe meme que le
    #    correctif nomme (« passe VERT sur un arbre ou la propriete est cassee »).
    # ⇒ MEME MOTIF QUE SON JUMEAU `recompte_trame_dn48.py:86`, au caractere pres.
    m = re.search(r"^#define\s+%s\s+(\d+)\s*$" % re.escape(nom), src, re.M)
    if not m:
        raise RuntimeError(
            "%s introuvable dans %s — ⛔ NE PAS RETOMBER SUR UNE VALEUR EN DUR : "
            "l'instrument ne peut pas verifier ce qu'il ne sait pas lire."
            % (nom, _DN_LINK_H))
    return int(m.group(1))

# 🔴 LE STUB `psutil` EST CHARGE ICI, ET IL CRIE. Sans lui, rien de tout ceci ne
#    tourne en WSL. ⚠️ Il fabrique cpu/ram/net/disk : ⛔ aucun de ces nombres n'est
#    une mesure, et c'est pour ca que ce fichier ne publie que des FORMES.
# ⚠️ DEFAUT TROUVE EN REVUE (2026-08-21) : ceci etait pose INCONDITIONNELLEMENT,
#    et `tools/stub_psutil` etait prepend a `sys.path`. Sur la tour — ou le VRAI
#    psutil existe — cet outil masquait donc le vrai module par le stub, dans son
#    propre processus. Or le stub sert justement a tourner LA OU psutil MANQUE.
# ⇒ on n'arme le stub que si le vrai psutil est INTROUVABLE, et ON LE DIT.
try:
    import psutil as _vrai_psutil                    # noqa: F401
    # 🔴 2e REVUE (2026-08-24) : UN IMPORT QUI REUSSIT NE PROUVE PAS LE VRAI
    #    MODULE. Lance de la maniere DOCUMENTEE (`PYTHONPATH=tools/stub_psutil`),
    #    le stub satisfait l'import et cet outil se croyait sur la tour — donc il
    #    prenait la branche AFFAIBLIE de la garde d'ordre la ou l'egalite EXACTE
    #    etait justement possible. ⇒ on lit le MARQUEUR du stub.
    _AVEC_VRAI_PSUTIL = not getattr(_vrai_psutil, "DN_EST_STUB", False)
except ImportError:
    _AVEC_VRAI_PSUTIL = False
if not _AVEC_VRAI_PSUTIL:
    os.environ["DN_STUB_PSUTIL"] = "1"
    print("[verif] ⚠️ psutil ABSENT ⇒ stub arme. ⛔ Aucun nombre cpu/ram/net/disk "
          "n'est une mesure ici.")
else:
    print("[verif] psutil REEL present ⇒ stub ⛔ NON arme.")
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
# ⛔ LE CHEMIN DU STUB N'EST PREPEND QUE SI LE STUB EST ARME. Sinon il masquerait
#    le vrai psutil ET leverait ImportError (le stub refuse de se charger sans
#    `DN_STUB_PSUTIL=1`), ce qui ferait echouer l'outil sur la machine la MIEUX
#    equipee — exactement a l'envers.
if not _AVEC_VRAI_PSUTIL:
    sys.path.insert(0, os.path.join(RACINE, "tools", "stub_psutil"))
sys.path.insert(0, os.path.join(RACINE, "agent"))
import dn_agent  # noqa: E402  -- LE PRODUIT, importe tel quel

LIGNE_MAX = _constante_c("DN_LINK_LIGNE_MAX")
GRANDEURS_MAX = _constante_c("DN_LINK_GRANDEURS_MAX")
print("[verif] constantes LUES dans dn_link.h : LIGNE_MAX=%d GRANDEURS_MAX=%d"
      % (LIGNE_MAX, GRANDEURS_MAX))

# 🔴 2e REVUE (2026-08-24) — `GRANDEURS_MAX` ETAIT LU, IMPRIME, ET N'ENTRAIT DANS
#    **AUCUNE** ASSERTION. Dans un fichier dont le correctif du jour est « ne plus
#    recopier une constante a la main », faire lire une constante pour ne rien en
#    verifier ajoute une APPARENCE de controle. ⇒ elle borne desormais ce que le
#    produit publie : aucune metrique ne peut porter plus de grandeurs que le fil
#    n'en accepte, et c'est LE mur de cette story (« le mur n'est pas l'octet,
#    c'est DN_LINK_GRANDEURS_MAX »).
_TROP = {m: n for m, n in
         ((m, len(dn_agent.BORNES[m])) for m in dn_agent.BORNES)
         if n > GRANDEURS_MAX}
if _TROP:
    raise SystemExit(
        "\u26d4 %d metrique(s) declarent PLUS de grandeurs que "
        "DN_LINK_GRANDEURS_MAX=%d : %s. Le firmware REJETTERAIT la trame entiere "
        "(`nv > n_grandeurs`), et aucun compteur ne dirait pourquoi."
        % (len(_TROP), GRANDEURS_MAX, _TROP))
print("[verif] \u2705 les %d metriques du produit tiennent dans GRANDEURS_MAX=%d"
      % (len(dn_agent.BORNES), GRANDEURS_MAX))

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
                sorted(vues) == sorted(c for c, _, _, _ in dn_agent.LHM_SONDES),
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
        # 🎯 LES DEUX VERITES-TERRAIN DE L'ORDRE, chacune reprise de SA source :
        #    le `c.max` vient de psutil (le stub, deterministe), la °C vient de LHM
        #    (le stub qui rejoue la fixture). ⛔ Aucune des deux n'est recopiee ici.
        import psutil as psutil_du_stub
        # 🔴 2e REVUE (2026-08-24) — DEUX CORRECTIFS DU MEME COMMIT S'ANNULAIENT,
        #    ET LA GARDE NE POUVAIT PLUS PASSER SUR LA TOUR :
        #      (A) le stub n'est plus arme quand le VRAI psutil existe (correct) ;
        #      (B) le plafond tolerant `<= 1000` est devenu une EGALITE EXACTE.
        #    Sur la tour, `psutil_du_stub` EST donc le vrai psutil — la variable
        #    ment sur son contenu — et `cpu_percent(interval=None)` mesure LA
        #    FENETRE DEPUIS LE DERNIER APPEL. L'appel du harnais et les deux
        #    `col.photo()` sont TROIS fenetres differentes, et l'appel du harnais
        #    CONSOMME l'intervalle du sujet. L'egalite y est fausse presque surement.
        # ⇒ LA GARDE SE SCINDE EN DEUX, chacune valide LA OU elle est probante :
        #    - sous STUB (valeurs deterministes) : egalite EXACTE, c'est elle qui
        #      attrape la permutation `_dx(cmax)` <-> `_dx(degc)` ;
        #    - sur PSUTIL REEL : l'egalite est ABANDONNEE et remplacee par une
        #      propriete qui, elle, ne depend pas de la fenetre — la °C vient de
        #      LHM (deterministe ici, c'est le stub qui la sert) et doit se
        #      retrouver EXACTEMENT en index 3, tandis que l'index 2 doit en
        #      DIFFERER. ⛔ On ne rend PAS un verdict qu'on ne peut pas etayer.
        _EXACT = not _AVEC_VRAI_PSUTIL
        vues_lhm = source().lire()
        photo = col.photo()
        photo = col.photo()                   # 2e tour : les debits existent
        d = dict(photo)
        verdict("la trame `cpu` porte QUATRE grandeurs", len(d["cpu"]) == 4,
                str(d["cpu"]))
        verdict("la trame `disk` porte QUATRE grandeurs", len(d["disk"]) == 4,
                str(d["disk"]))
        # 🔴 DEFAUT TROUVE EN REVUE (code review dn4-8, 2026-08-21), ET PROUVE
        #    PAR MUTATION. Cette garde s'ecrivait :
        #        d["cpu"][3] is not None and d["cpu"][2] is not None
        #        and d["cpu"][2] <= 1000
        #    Or `c.max` vaut 625 et la °C 410 : LES DEUX SONT <= 1000. En permutant
        #    `_dx(cmax)` et `_dx(degc)` dans `dn_agent.py`, le harnais imprimait
        #    « [OK ] la °C CPU est en INDEX 3 (⛔ pas 2)  index2(c.max)=410
        #    index3(degC)=625 » — LA LIGNE DE DETAIL AFFIRMAIT ELLE-MEME LE MAUVAIS
        #    MAPPING — et la suite sortait 0.
        # ⛔ C'ETAIT LA SEULE GARDE AUTOMATISEE DE LA DECISION CENTRALE DE LA STORY
        #    (la 4e voie, l'ordre `[%, GHz, c.max, °C]`, le temoin v3 intact).
        # ⇒ ON NE COMPARE PLUS A UN PLAFOND : on compare aux DEUX VALEURS ATTENDUES,
        #   chacune reprise de SA source, et le produit fait la quantification.
        cmax_attendu = dn_agent._dx(
            max(psutil_du_stub.cpu_percent(percpu=True)),
            dn_agent.BORNES["cpu"][2], {}, "verif:c.max")
        degc_attendu = dn_agent._dx(
            vues_lhm["cpu.degc"], dn_agent.BORNES["cpu"][3], {}, "verif:degc")
        # ⚠️ UNE GARDE QUI NE PEUT PAS DISCRIMINER DOIT LE DIRE. Si les deux
        #    grandeurs tombaient par hasard sur la meme valeur, la permutation
        #    redeviendrait invisible — et l'instrument se tairait vert.
        verdict("les deux valeurs DIFFERENT (sinon la garde est aveugle)"
                + ("" if _EXACT else " [psutil REEL]"),
                cmax_attendu != degc_attendu,
                "c.max=%s degC=%s" % (cmax_attendu, degc_attendu))
        if _EXACT:
            verdict("`c.max` est en INDEX 2 (valeur EXACTE, ⛔ pas un plafond)",
                    d["cpu"][2] == cmax_attendu,
                    "index2=%s attendu=%s" % (d["cpu"][2], cmax_attendu))
        else:
            # ⚠️ psutil REEL : `cpu_percent` mesure une fenetre, donc l'egalite
            #    exacte n'est pas etayable. Ce qui reste PROBANT et suffit a
            #    attraper la permutation : l'index 2 ne doit PAS porter la °C.
            verdict("`c.max` est en INDEX 2 (psutil REEL : ⛔ pas d'egalite "
                    "exacte, on verifie qu'il NE porte PAS la °C)",
                    d["cpu"][2] is not None and d["cpu"][2] != degc_attendu,
                    "index2=%s degC=%s (c.max instantane=%s, fenetres "
                    "differentes)" % (d["cpu"][2], degc_attendu, cmax_attendu))
        verdict("la °C CPU est en INDEX 3 (valeur EXACTE, ⛔ pas 2)",
                d["cpu"][3] == degc_attendu,
                "index3=%s attendu=%s" % (d["cpu"][3], degc_attendu))
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
        # 🔴 ON CAPTURE stderr PENDANT LES DEUX CYCLES. Sans ca, l'assertion
        #    « le message n'est imprime QU'UNE fois » ne peut RIEN observer : c'est
        #    le defaut trouve en revue (code review dn4-8, 2026-08-21), ou elle
        #    s'ecrivait `all(v >= 1 for v in col.pannes.values())` — vraie pour
        #    TOUT etat possible du programme, y compris le dictionnaire VIDE, et
        #    portant sur les COMPTEURS alors que son titre parle de L'IMPRESSION.
        journal = io.StringIO()
        vrai_stderr = sys.stderr
        t0 = time.perf_counter()
        try:
            sys.stderr = journal
            col.photo()
            d = dict(col.photo())
        finally:
            sys.stderr = vrai_stderr
        dt = time.perf_counter() - t0
        lignes_echec = [l for l in journal.getvalue().splitlines()
                        if "`lhm` en ECHEC" in l]
        verdict("la lecture est COUPEE au timeout, ⛔ pas au retard du serveur",
                dt < 1.2, "2 cycles en %.2f s (retard servi 2,00 s/tir ; "
                          "2 x budget = 0,80 s)" % dt)
        verdict("la panne est COMPTEE et NOMMEE",
                any(k.startswith("lhm:") for k in col.pannes), str(col.pannes))
        # ⚠️ DEUX CYCLES ONT ECHOUE : le compteur doit dire 2, stderr doit dire 1.
        #    C'est CETTE dissociation qui prouve l'anti-spam — ⛔ pas un `>= 1`.
        verdict("les DEUX cycles sont comptes (⛔ pas un seul)",
                sum(v for k, v in col.pannes.items() if k.startswith("lhm:")) == 2,
                "compteur = %s" % col.pannes)
        verdict("le message n'est imprime QU'UNE fois (stderr CAPTURE)",
                len(lignes_echec) == 1,
                "%d ligne(s) sur stderr pour 2 echecs" % len(lignes_echec))
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
    # 🔴 `len(d) >= 4` passait avec N'IMPORTE LESQUELLES 4 des 5 (revue dn4-8,
    #    2026-08-21) : le run de controle avait DEJA `gpu` absent et l'assertion
    #    restait verte. Elle ne discriminait donc rien — `disk` aurait pu
    #    disparaitre a la place, elle serait restee verte aussi.
    # ⛔ `gpu` EST EXCLU **PAR SON NOM ET AVEC SON MOTIF**, ⛔ pas par un compte
    #    permissif : sans GPU AMD (WSL, ou toute machine sans `atiadlxx.dll`),
    #    `SourceGpuAdl` se desactive POUR LA SESSION et la metrique n'est jamais
    #    emise. C'est une propriete de LA MACHINE, ⛔ pas de LHM — donc hors sujet
    #    ici, et il faut le DIRE plutot que de le laisser passer en silence.
    print("     (gpu %s sur cette machine — exclu par son NOM du controle ci-dessous)"
          % ("PRESENT" if "gpu" in d else "ABSENT"))
    verdict("les metriques non-LHM vivent (NOMMEES, ⛔ pas comptees)",
            {"cpu", "ram", "net", "disk"} <= set(d), str(sorted(d)))
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
    verdict("`ram`/`net`/`disk` continuent (NOMMEES, ⛔ pas comptees)",
            {"ram", "net", "disk"} <= set(d)
            and all(d[m][0] is not None for m in ("ram", "net", "disk")),
            str(sorted(d)))
    col.fermer()



# ═══════════════════════════════════════════════════════════════════════════
# 🔴 QUATRE SCENARIOS AJOUTES EN 2e REVUE (2026-08-24). ILS FERMENT UN TROU
#    NOMME PAR LA REVUE : les trois comportements livres le 2026-08-21 — la
#    verification de FAMILLE, le compteur de lignes ILLISIBLES, et le bornage par
#    morceau de `_lire_corps()` — n'etaient exerces par AUCUN des six scenarios.
#    PROUVE PAR MUTATION : avec `if False and famille != famille_attendue` et un
#    `return rep.read()` en tete de `_lire_corps`, ce fichier imprimait
#    « ✅ tous les controles passent ». Les chiffres publies au tableau des 38
#    patches (« REFUSE et COMPTE par sonde », « 253/253 lignes illisibles »)
#    venaient d'une mutation NON COMMITTEE, donc NON REJOUABLE.
# ⚠️ Le mode `goutte`, ajoute le 2026-08-21 « pour EPROUVER `_lire_corps()` »,
#    n'avait AUCUN appelant dans tout le depot.
# ═══════════════════════════════════════════════════════════════════════════
def scenario_famille():
    print("\n== 7. L'UNITE CHANGE COTE LHM — valeur REFUSEE, et ⛔ PAS une absence ==")
    p = lancer_stub("famille")
    try:
        src = source()
        vues = src.lire()
        verdict("les 5 sondes sont REFUSEES (famille inattendue)",
                all(v is None for v in vues.values()), str(vues))
        verdict("elles sont dans le seau `familles`, ⛔ PAS dans `absences`",
                len(src.familles) == 5 and not src.absences,
                "familles=%s absences=%s" % (sorted(src.familles), sorted(src.absences)))
        # 🎯 LE CONTROLE QUI DISCRIMINE : les lignes se parsent PARFAITEMENT.
        #    Si `lignes_illisibles` montait, on serait sur un desaccord de FORMAT
        #    (3e etat), ⛔ pas sur un changement d'UNITE (4e etat).
        verdict("⛔ AUCUNE ligne illisible : c'est bien le 4e etat, pas le 3e",
                src.lignes_illisibles == 0 and src.lignes_lues > 0,
                "lues=%d illisibles=%d" % (src.lignes_lues, src.lignes_illisibles))
        src.fermer()
    finally:
        tuer(p)


def scenario_doublon():
    print("\n== 8. DEUX FAMILLES POUR LA MEME SONDE — ⛔ pas de tirage au sort ==")
    p = lancer_stub("doublon")
    try:
        src = source()
        vues = src.lire()
        verdict("la sonde en conflit est REFUSEE (⛔ pas « dernier arrive gagne »)",
                vues.get("cpu.degc") is None, "cpu.degc=%s" % vues.get("cpu.degc"))
        verdict("le conflit est COMPTE sur SON compteur", bool(src.doublons),
                "doublons=%s" % sorted(src.doublons))
        verdict("les 4 tr/min, elles, restent LUES", 
                all(vues.get(k) is not None for k in
                    ("fan.top_out", "fan.cpu_noctua", "fan.case_group", "fan.rear_out")),
                str(vues))
        src.fermer()
    finally:
        tuer(p)


def scenario_vide():
    print("\n== 9. 200 SANS UNE SEULE LIGNE `lhm_` — c'est une PANNE, ⛔ pas 5 absences ==")
    p = lancer_stub("vide")
    try:
        src = source()
        leve = None
        try:
            src.lire()
        except Exception as exc:
            leve = exc
        # 🔴 AVANT CORRECTIF : `lues = 0`, `illisibles = 0`, `table = {}` ⇒ les cinq
        #    sondes tombaient dans `absences` ⇒ le bilan imprimait « LHM a REPONDU,
        #    sans cette valeur » et envoyait inspecter LES CAPTEURS. Mot pour mot le
        #    diagnostic CONTRAIRE de celui que le patch existe pour supprimer.
        verdict("la lecture LEVE (⇒ panne COMPTEE ET NOMMEE par `_tenter`)",
                leve is not None, "leve=%r" % (leve,))
        verdict("⛔ AUCUNE absence n'a ete fabriquee", not src.absences,
                "absences=%s" % sorted(src.absences))
        src.fermer()
    finally:
        tuer(p)


def scenario_willclose():
    print("\n== 10. REPONSE `will_close` — LE BUDGET DOIT TENIR QUAND MEME ==")
    # 🔴 CE SCENARIO A TROUVE UN VRAI DEFAUT (2026-08-24). CPython fait
    #    `if response.will_close: self.close()` dans `getresponse()`, ce qui met
    #    `HTTPConnection.sock` a None : `_borner_socket` devenait un NO-OP MUET et
    #    chaque `recv` retrouvait le plafond ENTIER.
    #    MESURE, arbre mute : 0,902 s pour 0,600 s de budget (**150 %**).
    #    MESURE, arbre corrige : 0,601 s (**100 %**).
    #    ⚠️ TOUS les autres modes du stub posent HTTP/1.1 + Content-Length : aucun
    #       ne pouvait produire cet etat.
    budget = 0.600
    p = lancer_stub("willclose", retard=budget * 0.5)
    try:
        src = source(timeout_s=budget)
        t0 = time.perf_counter()
        try:
            src.lire()
        except Exception:
            pass
        d = time.perf_counter() - t0
        # ⚠️ 1,3x et ⛔ pas 1,0 : la marge couvre l'ordonnancement, ⛔ pas un 2e
        #    `recv` a plafond plein (qui donnerait >= 1,5x).
        verdict("la lecture tient dans le budget malgre `will_close`",
                d <= budget * 1.3,
                "%.3f s pour %.3f s de budget (%.0f %%)"
                % (d, budget, 100.0 * d / budget))
        verdict("⛔ aucun bornage impossible (la socket a bien ete capturee)",
                src.bornages_impossibles == 0,
                "bornages_impossibles=%d" % src.bornages_impossibles)
        src.fermer()
    finally:
        tuer(p)


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
    scenario_famille()
    scenario_doublon()
    scenario_vide()
    scenario_willclose()
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-13 / AC2 (+ AC3.2, AC6.3) — `dn_hist` NE MENT NI SUR SON COÛT NI SUR SA
COUVERTURE, ÉPROUVÉ EN **EXÉCUTANT LE PRODUIT**, DEPUIS WSL, SANS CARTE.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

⛔ IL NE RELIT PAS LE SOURCE. Les autres gates de ce dépôt lisent des tables
   dans le `.c` ; celle-ci **compile `dn_hist.c` sur l'hôte et l'APPELLE**. Le
   motif est écrit dans la story : *« un harnais qui REJOUE au lieu
   d'EXTRAIRE+APPELER est une gate décorative »*. Les défauts qu'AC2 solde sont
   des défauts de COMPORTEMENT — un lecteur qui répond `0..0` avant l'init, une
   couverture qui rend l'uptime — et aucune relecture de source ne les voit.

🔬 LE HARNAIS. `dn_hist.c` n'inclut que `<string.h>`, `esp_timer.h` et `lvgl.h`.
   On fournit les deux derniers en coquilles minimales :
     · `esp_timer_get_time()` devient PILOTABLE — c'est ce qui permet de faire
       passer une frontière d'heure sans attendre une heure.
     · `LV_CHART_POINT_NONE` est RELU DU VRAI `lv_chart.h` du dépôt, ⛔ pas
       recopié : une coquille qui définirait la sentinelle « au cas où » ferait
       passer le `_Static_assert` sur une valeur qui n'est pas celle de LVGL, et
       la gate validerait un accord avec elle-même.
   ⚠️ Le reste de `dn_hist.c` est LE FICHIER DU DÉPÔT, non modifié.

🔴 LES TÉMOINS NÉGATIFS SONT DES MUTATIONS **COMPILÉES ET EXÉCUTÉES**. On retire
   le garde, on recompile, on rappelle — et on exige de voir le défaut d'origine
   REVENIR (`0..0`, l'uptime, le seau sauté). Une garde dont on n'a pas vu
   l'absence faire échouer quelque chose ne prouve rien (AC7.5).

Sortie : exit 0 si tout passe, 1 sinon. Publie le sha256 des sources LUES.
"""

import ctypes
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(RACINE, "firmware", "desknode", "main")
DN_HIST_C = os.path.join(MAIN, "dn_hist.c")
DN_HIST_H = os.path.join(MAIN, "dn_hist.h")
LV_CHART_H = os.path.join(RACINE, "firmware", "desknode", "managed_components",
                          "lvgl__lvgl", "src", "widgets", "chart", "lv_chart.h")
MAP = os.path.join(RACINE, "firmware", "desknode", "build", "desknode.map")

# ── dn4-39 / AC39.3.b — ELLE ECHOUE **FERME**, ⛔ PLUS EN TRACEBACK NU ────────
#
# 🔴 MESURE DU 2026-09-02, clone neuf + `HOME` etranger : cette gate PLANTAIT.
#    `sentinelle_lvgl()` ouvrait `lv_chart.h` sans jamais declarer qu'elle en
#    dependait, et rendait un `FileNotFoundError` NU — rc **1**, sans motif,
#    sans remede, et impossible a distinguer d'un vrai defaut.
#    ⚠️ `tools/verif_veille_dn33.py` a EXACTEMENT le meme prerequis et le traite
#      bien depuis toujours : `ECHEC : ... introuvable : <chemin>` **et le
#      remede**. La bonne forme etait deja dans le depot — rien a inventer.
#
# ⛔ POURQUOI 4 : `2` = message d'usage (`verif_sr03.py`), `3` = mutant PERIME
#    (`verif_paliers_dn441.py`). Detail complet dans `verif_dossier_dn415.py`.
RC_PREREQUIS = 4

SEAU_S = 3600
SEAUX = 24
N_POINTS = 120
N_SERIES = 8

ok_total = [0]
ko_total = [0]
_tmp = []


def lire(chemin):
    with open(chemin, "rb") as f:
        brut = f.read()
    return brut.decode("utf-8"), hashlib.sha256(brut).hexdigest()[:16]


# 🔴 dn4-40 / AC40.7.c — L'INSTRUMENT DE CAMPAGNE, ⛔ PAS UN CHANGEMENT DE
# FORMAT. Import DEFENSIF : une gate reste jouable si son instrument manque.
# Sans `DN_TRACE_CTRL`, la console sort a l'octet pres comme avant.
try:
    import dn_trace
except ImportError:                                  # pragma: no cover
    dn_trace = None


def ctrl(ok, libelle, detail=""):
    if dn_trace is not None:
        dn_trace.trace(ok, libelle)
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-56s %s" % (libelle, detail))
    else:
        ko_total[0] += 1
        print("  [KO ] %-56s %s" % (libelle, detail))
    return ok


def sentinelle_lvgl():
    """La valeur de `LV_CHART_POINT_NONE` RELUE du vrai en-tête LVGL."""
    txt, _ = lire(LV_CHART_H)
    m = re.search(r"#define\s+LV_CHART_POINT_NONE\s+\(?([A-Z0-9_]+)\)?", txt)
    return m.group(1) if m else None


SHIM_ESP_TIMER = """#pragma once
#include <stdint.h>
int64_t esp_timer_get_time(void);
"""

SHIM_LVGL = """#pragma once
#include <stdint.h>
#define LV_CHART_POINT_NONE (%s)
"""

SHIM_C = """#include <stdint.h>
int64_t dn_test_horloge_us = 0;
int64_t esp_timer_get_time(void) { return dn_test_horloge_us; }
"""


def construire(source_c, etiquette):
    """Compile `source_c` + la coquille en une `.so`, et rend le handle ctypes."""
    d = tempfile.mkdtemp(prefix="dn_hist_%s_" % etiquette)
    _tmp.append(d)
    shutil.copy(DN_HIST_H, os.path.join(d, "dn_hist.h"))
    with open(os.path.join(d, "dn_hist.c"), "w", encoding="utf-8") as f:
        f.write(source_c)
    with open(os.path.join(d, "esp_timer.h"), "w", encoding="utf-8") as f:
        f.write(SHIM_ESP_TIMER)
    sent = sentinelle_lvgl()
    with open(os.path.join(d, "lvgl.h"), "w", encoding="utf-8") as f:
        f.write(SHIM_LVGL % sent)
    with open(os.path.join(d, "shim.c"), "w", encoding="utf-8") as f:
        f.write(SHIM_C)
    so = os.path.join(d, "dn_hist.so")
    cmd = ["gcc", "-std=c11", "-O0", "-g", "-fPIC", "-shared", "-I", d,
           os.path.join(d, "dn_hist.c"), os.path.join(d, "shim.c"), "-o", so]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return None, r.stderr
    lib = ctypes.CDLL(so)
    lib.dn_hist_points.restype = ctypes.POINTER(ctypes.c_int32)
    lib.dn_hist_points.argtypes = [ctypes.c_int]
    lib.dn_hist_debut.restype = ctypes.c_uint32
    lib.dn_hist_debut.argtypes = [ctypes.c_int]
    lib.dn_hist_reels.restype = ctypes.c_int
    lib.dn_hist_reels.argtypes = [ctypes.c_int]
    lib.dn_hist_couverture_s.restype = ctypes.c_uint32
    lib.dn_hist_couverture_s.argtypes = [ctypes.c_int]
    lib.dn_hist_minmax.restype = ctypes.c_bool
    lib.dn_hist_minmax.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int32),
                                   ctypes.POINTER(ctypes.c_int32)]
    lib.dn_hist_minmax_long.restype = ctypes.c_bool
    lib.dn_hist_minmax_long.argtypes = [ctypes.c_int,
                                        ctypes.POINTER(ctypes.c_int32),
                                        ctypes.POINTER(ctypes.c_int32)]
    lib.dn_hist_octets.restype = ctypes.c_size_t
    lib.dn_hist_octets_detail.restype = ctypes.c_size_t
    lib.dn_hist_octets_detail.argtypes = [ctypes.POINTER(ctypes.c_size_t)] * 3
    lib.dn_hist_poser.argtypes = [ctypes.c_int, ctypes.c_int32, ctypes.c_bool]
    return lib, None


def horloge(lib, secondes):
    ctypes.c_int64.in_dll(lib, "dn_test_horloge_us").value = int(secondes) * 1000000


def minmax(lib, serie, longue=False):
    a, b = ctypes.c_int32(0), ctypes.c_int32(0)
    f = lib.dn_hist_minmax_long if longue else lib.dn_hist_minmax
    ok = f(serie, ctypes.byref(a), ctypes.byref(b))
    return ok, a.value, b.value


# ═══════════════════════════════════════════════════════════════════════════
# LES SYMBOLES DU `.map` — le coût tel que L'ÉDITEUR DE LIENS l'a placé
# ═══════════════════════════════════════════════════════════════════════════
def octets_du_map():
    """{symbole: taille} pour tout `.bss.*` / `.data.*` de `dn_hist.c.obj`.

    ⚠️ Le `.map` coupe la ligne quand le nom de section est long : la taille est
       alors sur la ligne SUIVANTE. Un parseur qui ne lit qu'une ligne rate
       `s_seau_courant` et sous-compte de 4 o — un écart petit, plausible, et
       qui ferait accuser `dn_hist_octets()` À TORT."""
    if not os.path.exists(MAP):
        return None
    with open(MAP, encoding="utf-8", errors="replace") as f:
        lignes = f.read().split("\n")
    out = {}
    for i, l in enumerate(lignes):
        m = re.match(r"\s+\.(bss|data)\.([A-Za-z_][A-Za-z0-9_]*)\s*$", l)
        if m and i + 1 < len(lignes):
            m2 = re.match(r"\s+0x[0-9a-f]+\s+0x([0-9a-f]+)\s+(\S+)", lignes[i + 1])
            if m2 and "dn_hist.c.obj" in m2.group(2):
                out[m.group(2)] = int(m2.group(1), 16)
            continue
        m = re.match(r"\s+\.(bss|data)\.([A-Za-z_][A-Za-z0-9_]*)\s+0x[0-9a-f]+"
                     r"\s+0x([0-9a-f]+)\s+(\S+)", l)
        if m and "dn_hist.c.obj" in m.group(4):
            out[m.group(2)] = int(m.group(3), 16)
    return out


# ═══════════════════════════════════════════════════════════════════════════
def bloc_cout(lib):
    print("\n── AC2.1 — LE COÛT DÉCLARÉ EST LE COÛT RÉEL ───────────────────────")
    p, b, i = (ctypes.c_size_t(0), ctypes.c_size_t(0), ctypes.c_size_t(0))
    tot = lib.dn_hist_octets_detail(ctypes.byref(p), ctypes.byref(b),
                                    ctypes.byref(i))
    print("     points %d o · seaux %d o · index %d o ⇒ TOTAL %d o"
          % (p.value, b.value, i.value, tot))
    ctrl(tot == lib.dn_hist_octets(),
         "`dn_hist_octets()` == la somme des trois termes", "%d o" % tot)
    ctrl(p.value == N_SERIES * N_POINTS * 4, "points = 8 x 120 x 4",
         "%d o" % p.value)
    ctrl(b.value == N_SERIES * SEAUX * (4 + 4 + 1), "seaux = 8 x 24 x (4+4+1)",
         "%d o" % b.value)
    ctrl(tot > p.value,
         "le total DÉPASSE `sizeof(s_pts)` — la sous-déclaration est close",
         "+%d o (+%d %%)" % (tot - p.value, (tot - p.value) * 100 // tot))

    sym = octets_du_map()
    if sym is None:
        # 🔴 REVUE 2026-09-02 — `firmware/desknode/build/` est GITIGNORE
        #    EXACTEMENT COMME `managed_components/`, mais son absence rendait
        #    **1** (un vrai rouge) au lieu de **4** (prerequis absent). Un poste
        #    ou `idf.py reconfigure` a tourne SANS `idf.py build` a donc son
        #    temoin LVGL present ⇒ la gate est jouee ⇒ rouge « lancer idf.py
        #    build », indiscernable d'un defaut du code. C'est la cause B restee
        #    entiere sur le SECOND artefact gitignore.
        print("  [PREREQUIS ABSENT] le `.map` du build n'est pas la")
        print("      MOTIF : firmware/desknode/build/ est GITIGNORE, comme")
        print("              managed_components/. ⛔ Ce n'est pas un verdict")
        print("              sur le code.")
        print("      REMEDE : idf.py build, puis rejouer cette gate.")
        print("      ⛔ rc=%d — prerequis absent, ⛔ pas un rouge." % RC_PREREQUIS)
        return RC_PREREQUIS
    noyau = ["s_pts", "s_smin", "s_smax", "s_svu", "s_w", "s_pret"]
    manquants = [s for s in noyau if s not in sym]
    ctrl(not manquants, "les symboles de stockage sont dans le `.map`",
         "manquants : %s" % (manquants or "aucun"))
    ctrl("s_seaux_ouverts" not in sym,
         "`s_seaux_ouverts` a DISPARU du `.map` (AC2.2)",
         "supprimé, pas seulement débranché")
    ctrl("s_seau_courant" not in sym and "s_seau_abs" in sym,
         "l'index de seau est ABSOLU dans le binaire (AC3.2)",
         "`s_seau_abs` %d o" % sym.get("s_seau_abs", 0))
    somme = sum(sym.values())
    print("     `.map` (%d symboles) : " % len(sym) +
          " · ".join("%s %d" % (k, v) for k, v in sorted(sym.items())))
    ctrl(somme == tot,
         "le coût déclaré == LA SOMME DE **TOUS** les symboles du `.map`",
         "declare %d o, map %d o, ecart %+d o" % (tot, somme, tot - somme))
    print("     ⚠️ On somme TOUT ce que l'éditeur de liens a placé pour")
    print("        `dn_hist.c.obj`, ⛔ pas une liste écrite à la main : une")
    print("        statique ajoutée et oubliée dans `dn_hist_octets_detail()`")
    print("        fait ROUGIR cette ligne, et c'est le seul moyen que le")
    print("        chiffre ne re-périme pas en silence comme les trois")
    print("        précédents (1 344 / 1 536 / 1 728).")


def bloc_avant_init(source, lib_ref):
    print("\n── AC2.3 + AC2.4 — LES SIX LECTEURS AVANT `dn_hist_init()` ────────")
    lib, err = construire(source, "avantinit")
    if lib is None:
        ctrl(False, "la coquille compile", err[:200])
        return
    horloge(lib, 7200)  # 2 h d'uptime, et RIEN n'a été initialisé
    ctrl(not lib.dn_hist_points(0), "`dn_hist_points` rend NULL", "avant init")
    ok, mn, mx = minmax(lib, 0)
    ctrl(not ok, "`dn_hist_minmax` rend false", "⛔ pas `%d..%d`" % (mn, mx))
    okl, lm, lx = minmax(lib, 0, longue=True)
    ctrl(not okl, "`dn_hist_minmax_long` rend false", "⛔ pas `%d..%d`" % (lm, lx))
    ctrl(lib.dn_hist_reels(0) == 0, "`dn_hist_reels` rend 0",
         "⛔ pas 120 zéros comptés comme réels")
    ctrl(lib.dn_hist_couverture_s(0) == 0,
         "`dn_hist_couverture_s` rend 0", "⛔ pas 7 200 s d'uptime")
    ctrl(lib.dn_hist_debut(0) == 0, "`dn_hist_debut` rend 0", "index sans tableau")

    # ── LE TÉMOIN NÉGATIF : on retire les gardes `s_pret` et on RECOMPILE ────
    print("\n     🔴 TÉMOIN NÉGATIF — gardes `s_pret` retirées, RECOMPILÉ, RAPPELÉ")
    motif_garde = "if (!s_pret || serie < 0"
    n = source.count(motif_garde)   # 6 lecteurs + l'écrivain `dn_hist_poser`
    mut = source.replace(motif_garde, "if (serie < 0")
    libm, err = construire(mut, "sanspret")
    if libm is None:
        ctrl(False, "le mutant compile", err[:200])
    else:
        horloge(libm, 7200)
        okm, mnm, mxm = minmax(libm, 0)
        ctrl(okm and mnm == 0 and mxm == 0,
             "sans garde, `minmax` rend bien la plage `0..0` INTERDITE",
             "défaut d'origine REPRODUIT (%d gardes `s_pret` retirées : "
         "les 6 lecteurs + l'écrivain)" % n)
        ctrl(libm.dn_hist_reels(0) == N_POINTS,
             "sans garde, `reels` compte les 120 zéros du `.bss`",
             "%d points « réels » qui n'existent pas" % libm.dn_hist_reels(0))
        ctrl(bool(libm.dn_hist_points(0)),
             "sans garde, `points` rend un tableau de zéros",
             "⇒ `lv_chart` tracerait une ligne plate à zéro")


def bloc_couverture(source):
    print("\n── AC2.2 — LA COUVERTURE EST CE QUI A ÉTÉ OBSERVÉ ─────────────────")
    lib, err = construire(source, "couv")
    if lib is None:
        ctrl(False, "la coquille compile", err[:200])
        return
    lib.dn_hist_init()

    # 1 h d'horloge, l'échantillonneur tourne, mais la source PC est MUETTE.
    for t in range(0, 3700, 60):
        horloge(lib, t)
        lib.dn_hist_poser(0, 0, False)  # `connue = false` ⇒ TROU
    horloge(lib, 3700)
    ctrl(lib.dn_hist_couverture_s(0) == 0,
         "1 h d'uptime, 0 réel ⇒ couverture 0",
         "🔴 c'est le témoin d'AC2.2 : « MIN/MAX sur : 1 h » à côté de « -- »")
    okl, _, _ = minmax(lib, 0, longue=True)
    ctrl(not okl, "…et `minmax_long` rend false au même instant",
         "les deux instruments s'accordent")

    lib.dn_hist_init()
    horloge(lib, 40)
    lib.dn_hist_poser(0, 500, True)
    ctrl(lib.dn_hist_couverture_s(0) == 40,
         "1 réel à t = 40 s ⇒ couverture 40 s",
         "⛔ pas 3 600 s au motif que le seau fait 1 h")

    lib.dn_hist_init()
    horloge(lib, 100)
    lib.dn_hist_poser(0, 500, True)
    horloge(lib, 3 * SEAU_S + 250)
    lib.dn_hist_poser(0, 600, True)
    c = lib.dn_hist_couverture_s(0)
    ctrl(c == 3 * SEAU_S + 250,
         "réel à t=100 s puis t=3 h 4 min ⇒ couverture = 3 h 4 min",
         "%d s" % c)
    ctrl(lib.dn_hist_couverture_s(1) == 0,
         "…et la série 1, jamais alimentée, reste à 0",
         "la couverture est PAR SÉRIE")

    # ── TÉMOIN NÉGATIF : la version « uptime » d'avant le 2026-08-25 ────────
    print("\n     🔴 TÉMOIN NÉGATIF — la version UPTIME est remise, et vue MENTIR")
    corps_uptime = """
    if (!s_pret || serie < 0 || serie >= DN_HIST_N_SERIES) { return 0; }
    int64_t up_s = esp_timer_get_time() / 1000000;
    uint32_t plafond = (uint32_t)DN_HIST_SEAUX * DN_HIST_SEAU_S;
    if (up_s < 0) { return 0; }
    return (uint32_t)up_s < plafond ? (uint32_t)up_s : plafond;
}
"""
    i = source.find("uint32_t dn_hist_couverture_s(int serie)")
    j = source.find("\n}\n", i)
    mut = source[:i] + "uint32_t dn_hist_couverture_s(int serie)\n{" + \
        corps_uptime + source[j + 3:]
    libm, err = construire(mut, "uptime")
    if libm is None:
        ctrl(False, "le mutant compile", err[:300])
        return
    libm.dn_hist_init()
    for t in range(0, 3700, 60):
        horloge(libm, t)
        libm.dn_hist_poser(0, 0, False)
    horloge(libm, 3700)
    ctrl(libm.dn_hist_couverture_s(0) == 3700,
         "l'ancienne version annonce 3 700 s sur ZÉRO observation",
         "le défaut d'AC2.2 est REPRODUIT, donc la gate le voit")


def bloc_axe_temps(source):
    print("\n── AC3.1 — L'AXE DES TEMPS NE SE COMPRIME PAS APRÈS UN `ui off` ───")
    lib, err = construire(source, "axe")
    if lib is None:
        ctrl(False, "la coquille compile", err[:200])
        return
    lib.dn_hist_init()
    lib.dn_hist_rattraper.restype = ctypes.c_int
    for t in range(0, 6):
        horloge(lib, t)
        lib.dn_hist_rattraper()
        lib.dn_hist_poser(0, 100 + t, True)
    avant = lib.dn_hist_debut(0)
    ctrl(lib.dn_hist_reels(0) == 6, "6 s d'échantillonnage ⇒ 6 points réels",
         "position d'écriture = %d" % avant)

    # ── LA PAUSE : 60 s pendant lesquelles LVGL est arrêté ──────────────────
    # Dernier échantillon à t = 5 s ; reprise à t = 66 s. Les secondes 6..65
    # n'ont PAS été échantillonnées : 60 trous, puis l'échantillon de reprise.
    horloge(lib, 66)
    comble = lib.dn_hist_rattraper()
    ctrl(comble == 60,
         "pause t=5 s -> t=66 s ⇒ les 60 s non échantillonnées sont COMBLÉES",
         "comblé %d (secondes 6..65)" % comble)
    lib.dn_hist_poser(0, 999, True)
    pts = lib.dn_hist_points(0)
    ctrl(lib.dn_hist_reels(0) == 7, "7 points réels, pas 7 points COLLÉS",
         "%d réels sur 120" % lib.dn_hist_reels(0))
    ecart = (lib.dn_hist_debut(0) - avant) % N_POINTS
    ctrl(ecart == 61,
         "l'anneau a avancé de 61 positions (60 trous + la reprise)",
         "%d positions — ⛔ la courbe ne recolle PAS les deux bords" % ecart)
    re_, rt = ctypes.c_uint32(0), ctypes.c_uint32(0)
    lib.dn_hist_rattrapages(ctypes.byref(re_), ctypes.byref(rt))
    ctrl(re_.value == 1 and rt.value == 60,
         "le rattrapage est COMPTÉ et publiable par `hist`",
         "%d coupure(s), %d trou(s)" % (re_.value, rt.value))

    # ── LA GIGUE N'EST PAS UNE COUPURE ─────────────────────────────────────
    lib.dn_hist_init()
    horloge(lib, 0)
    lib.dn_hist_rattraper()
    for ms in (1040, 2080, 3150, 4200):
        ctypes.c_int64.in_dll(lib, "dn_test_horloge_us").value = ms * 1000
        ctrl(lib.dn_hist_rattraper() == 0,
             "gigue de timer à t=%d ms ⇒ AUCUN trou creusé" % ms,
             "⛔ une courbe en pointillés sur une carte saine")

    # ── TÉMOIN NÉGATIF : sans rattrapage, les deux bords se recollent ───────
    print("\n     🔴 TÉMOIN NÉGATIF — `dn_hist_rattraper()` neutralisée")
    i = source.find("int dn_hist_rattraper(void)")
    j = source.find("\n}\n", i)
    mut = source[:i] + "int dn_hist_rattraper(void)\n{\n    return 0;\n}\n" + \
        source[j + 3:]
    libm, err = construire(mut, "sansrattr")
    if libm is None:
        ctrl(False, "le mutant compile", err[:300])
        return
    libm.dn_hist_rattraper.restype = ctypes.c_int
    libm.dn_hist_init()
    for t in range(0, 6):
        horloge(libm, t)
        libm.dn_hist_rattraper()
        libm.dn_hist_poser(0, 100 + t, True)
    a = libm.dn_hist_debut(0)
    horloge(libm, 66)
    libm.dn_hist_rattraper()
    libm.dn_hist_poser(0, 999, True)
    d = (libm.dn_hist_debut(0) - a) % N_POINTS
    ctrl(d == 1,
         "sans rattrapage, 60 s de pause avancent l'anneau d'UNE case",
         "le défaut est REPRODUIT : 60 s dessinées comme 1 s")


def bloc_seaux(source):
    print("\n── AC3.2 — `seau_suivre()` NE SAUTE PLUS DE SEAUX ─────────────────")
    lib, err = construire(source, "seaux")
    if lib is None:
        ctrl(False, "la coquille compile", err[:200])
        return

    def scenario(l):
        """3 heures alimentées, puis un saut à l'heure absolue 25.

        L'heure 25 a le MÊME index d'anneau que l'heure 1 : c'est le cas où un
        index modulo 24 répond « même seau » sur deux instants distants d'un
        jour entier."""
        l.dn_hist_init()
        for h, v in ((0, 500), (1, 100), (2, 900)):
            horloge(l, h * SEAU_S + 10)
            l.dn_hist_poser(0, v, True)
        horloge(l, 25 * SEAU_S + 10)
        l.dn_hist_poser(0, 700, True)
        return minmax(l, 0, longue=True)

    ok, mn, mx = scenario(lib)
    ctrl(ok and mn == 700 and mx == 900,
         "après le saut, la fenêtre ne garde que 900 (h=2) et 700 (h=25)",
         "%d..%d" % (mn, mx))
    ctrl(mn != 500,
         "le 500 de l'heure 0, VIEUX DE 25 h, a été vidé par la traversée",
         "⛔ sinon un minimum d'il y a 25 h vit dans une fenêtre de 24 h")
    ctrl(mn != 100,
         "le 100 de l'heure 1 a été vidé lui aussi (seau ré-atteint)",
         "l'heure 25 retombe sur l'index d'anneau de l'heure 1")

    # ── TÉMOIN NÉGATIF : l'ancienne version, index d'anneau, arrivée seule ──
    print("\n     🔴 TÉMOIN NÉGATIF — l'ancien `seau_suivre()` est remis")
    ancien = """
    int64_t up_s = esp_timer_get_time() / 1000000;
    int b = (int)((up_s / DN_HIST_SEAU_S) % DN_HIST_SEAUX);
    if (b == (int)(s_seau_abs % DN_HIST_SEAUX) && s_seau_abs >= 0) { return; }
    s_seau_abs = up_s / DN_HIST_SEAU_S;
    for (int s = 0; s < DN_HIST_N_SERIES; s++) { s_svu[s][b] = false; }
}
"""
    i = source.find("static void seau_suivre(void)")
    j = source.find("\n}\n", i)
    mut = source[:i] + "static void seau_suivre(void)\n{" + ancien + \
        source[j + 3:]
    libm, err = construire(mut, "seausaut")
    if libm is None:
        ctrl(False, "le mutant compile", err[:300])
        return
    ok, mn, mx = scenario(libm)
    ctrl(ok and mn == 500,
         "l'ancienne version garde le 500 de l'heure 0, vieux de 25 h",
         "%d..%d — le défaut d'AC3.2 est REPRODUIT" % (mn, mx))


def bloc_ecrits(source):
    print("\n── AC6.3 — « JAMAIS ÉCRIT » N'EST PAS « TROU » ────────────────────")
    lib, err = construire(source, "ecrits")
    if lib is None:
        ctrl(False, "la coquille compile", err[:200])
        return
    lib.dn_hist_ecrits.restype = ctypes.c_int
    lib.dn_hist_ecrits.argtypes = [ctypes.c_int]
    lib.dn_hist_rattraper.restype = ctypes.c_int
    lib.dn_hist_init()
    ctrl(lib.dn_hist_ecrits(0) == 0, "après l'init, 0 position écrite",
         "l'anneau est plein de TROUS, mais aucun n'a été VÉCU")
    for t in range(10):
        horloge(lib, t)
        lib.dn_hist_poser(0, 500 + t, True)
    e, r = lib.dn_hist_ecrits(0), lib.dn_hist_reels(0)
    ctrl(e == 10 and r == 10,
         "à t = 10 s : 10 écrites, 10 réelles, 0 trou",
         "⛔ l'ancienne table publiait « trous 110 » ici")
    ctrl(N_POINTS - e == 110, "…et 110 positions JAMAIS ATTEINTES",
         "colonne `jamais`, ⛔ pas colonne `trous`")
    for t in range(10, 15):
        horloge(lib, t)
        lib.dn_hist_poser(0, 0, False)  # la source se tait : VRAIS trous
    e, r = lib.dn_hist_ecrits(0), lib.dn_hist_reels(0)
    ctrl(e == 15 and r == 10 and (e - r) == 5,
         "5 s de source muette ⇒ 5 VRAIS trous, `jamais` inchangé",
         "ecrits %d · reels %d · trous %d · jamais %d" % (e, r, e - r,
                                                          N_POINTS - e))
    # Le rattrapage écrit AUSSI : sinon `jamais` ne descendrait pas pendant une
    # pause, et une coupure de 25 s se lirait comme 25 s « jamais atteintes ».
    # ⚠️ IL FAUT L'ARMER : au tout premier appel, `s_tick_us` vaut -1 et la
    #    fonction se contente d'horodater. Sans cet appel d'amorçage, le contrôle
    #    ci-dessous passerait sur `n == 0` — un VERT SUR ZÉRO ÉVÉNEMENT, et c'est
    #    précisément la famille de vacuité que cette story solde.
    horloge(lib, 14)
    lib.dn_hist_rattraper()
    horloge(lib, 40)
    n = lib.dn_hist_rattraper()
    ctrl(n > 0, "le rattrapage a bien été ATTEINT par ce scénario",
         "%d trou(s) comblé(s) — ⛔ un vert sur n == 0 ne prouverait rien" % n)
    ctrl(lib.dn_hist_ecrits(0) == 15 + n,
         "le RATTRAPAGE compte comme des positions écrites",
         "ecrits = 15 + %d = %d" % (n, lib.dn_hist_ecrits(0)))
    # saturation
    lib.dn_hist_init()
    for t in range(0, 200):
        horloge(lib, t)
        lib.dn_hist_poser(0, 700, True)
    ctrl(lib.dn_hist_ecrits(0) == N_POINTS,
         "après un tour complet, `ecrits` SATURE à 120",
         "⛔ pas 200 : il compte des POSITIONS, pas des écritures")

    # ── TÉMOIN NÉGATIF : on retire l'incrément, on RECOMPILE, on RAPPELLE ───
    print("\n     🔴 TÉMOIN NÉGATIF — l'incrément retiré, RECOMPILÉ, RAPPELÉ")
    motif = ("    if (s_ecrits[serie] < DN_HIST_N_POINTS) {\n"
             "        s_ecrits[serie]++;\n    }\n")
    if motif not in source:
        ctrl(False, "le motif d'incrément est trouvable", "mutation impossible")
        return
    libm, err = construire(source.replace(motif, "", 1), "sansecrits")
    if libm is None:
        ctrl(False, "le mutant compile", err[:300])
        return
    libm.dn_hist_ecrits.restype = ctypes.c_int
    libm.dn_hist_ecrits.argtypes = [ctypes.c_int]
    libm.dn_hist_init()
    for t in range(10):
        horloge(libm, t)
        libm.dn_hist_poser(0, 500 + t, True)
    em, rm = libm.dn_hist_ecrits(0), libm.dn_hist_reels(0)
    ctrl(em == 0 and rm == 10,
         "sans l'incrément : 10 réelles pour 0 « écrite »",
         "⇒ `jamais` dirait 120 sur un anneau où 10 cases vivent")


def bloc_revue_2026_08_25(source):
    """🔴 LES TROIS DÉFAUTS QUE LA REVUE DE CODE DU 2026-08-25 A MESURÉS.

    Ils vivaient TOUS LES TROIS sous une gate verte : celle-ci vérifiait les
    invariants d'AC3.1 sur des `dt` de ~1 040 ms et sur une pause de 60 s —
    jamais au-delà de 121 s, donc l'écrêtage n'était jamais exercé ; et jamais
    sans écrivain, donc le gel des seaux ne pouvait pas apparaître.
    """
    print("\n── REVUE 2026-08-25 — PLAFOND, PLANCHER, ET VIEILLISSEMENT ────────")
    lib, err = construire(source, "revue")
    if lib is None:
        ctrl(False, "la coquille compile", err[:200])
        return
    lib.dn_hist_rattraper.restype = ctypes.c_int
    lib.dn_hist_couverture_s.restype = ctypes.c_uint32

    # ── A) LE COMPTEUR PUBLIE L'OBSERVATION, ⛔ PAS LE PLAFOND ──────────────
    releves = {}
    for pause in (600, 3600):
        lib.dn_hist_init()
        horloge(lib, 0)
        lib.dn_hist_rattraper()
        lib.dn_hist_poser(0, 100, True)
        horloge(lib, pause + 1)
        releves[pause] = lib.dn_hist_rattraper()
    ctrl(releves[600] == 600,
         "`ui off` de 10 min ⇒ le compteur publie 600, ⛔ pas 120",
         "obtenu %d" % releves[600])
    ctrl(releves[3600] == 3600,
         "`ui off` d'1 h ⇒ le compteur publie 3600, ⛔ pas 120",
         "obtenu %d" % releves[3600])
    ctrl(releves[600] != releves[3600],
         "deux coupures d'un facteur 6 sont DISCERNABLES",
         "600 vs 3600 — avant le correctif : 120 et 120, MÊME PHRASE")

    # ── B) LE RESTE INFRA-PÉRIODE S'ACCUMULE, ⛔ IL NE SE JETTE PAS ─────────
    lib.dn_hist_init()
    horloge(lib, 0)
    lib.dn_hist_rattraper()
    creuses = 0
    for k in range(1, 9):  # une horloge à 1 500 ms par tick
        ctypes.c_int64.in_dll(lib, "dn_test_horloge_us").value = int(k * 1500 * 1000)
        creuses += lib.dn_hist_rattraper()
    ctrl(creuses == 4,
         "horloge à 1 500 ms/tick sur 12 s ⇒ 4 secondes manquantes VUES",
         "%d creusée(s) — avant le correctif : 0, INDÉFINIMENT" % creuses)

    # ── C) LES SEAUX VIEILLISSENT POUR LES LECTEURS, SANS ÉCRIVAIN ─────────
    def apres_pause(bib, heures):
        bib.dn_hist_init()
        horloge(bib, 300)
        for v in (500, 506):
            bib.dn_hist_poser(0, v, True)
        vif = minmax(bib, 0, longue=True)
        horloge(bib, 300 + heures * 3600)   # ⛔ AUCUN `poser` : plus d'écrivain
        return vif, minmax(bib, 0, longue=True), bib.dn_hist_couverture_s(0)

    vif, gele, couv = apres_pause(lib, 25)
    ctrl(vif[0] and vif[1] == 500,
         "à chaud, le MIN/MAX long voit bien la valeur posée", "min = %d" % vif[1])
    ctrl(not gele[0],
         "après 25 h d'`ui off`, le MIN/MAX long rend FAUX",
         "⛔ pas le minimum du TOUR PRÉCÉDENT de 24 h (obtenu ok=%s, min=%d)"
         % (gele[0], gele[1]))
    ctrl(couv == 0,
         "après 25 h d'`ui off`, la couverture rend 0",
         "obtenu %d s — avant le correctif : 3900 s sur ZÉRO observation" % couv)

    # ── TÉMOIN NÉGATIF : on RÉTABLIT l'ancien calcul d'âge ──────────────────
    print("\n     🔴 TÉMOIN NÉGATIF — l'âge redevient celui d'un seau GELÉ")
    i = source.find("static int seau_age(int b)")
    j = source.find("\n}\n", i)
    if i < 0 or j < 0:
        ctrl(False, "le mutant trouve `seau_age()`", "introuvable")
        return
    mut = (source[:i] + "static int seau_age(int b)\n{\n"
           "    if (s_seau_abs < 0) { return -1; }\n"
           "    return (int)(((s_seau_abs - b) % DN_HIST_SEAUX"
           " + DN_HIST_SEAUX) % DN_HIST_SEAUX);\n}\n" + source[j + 3:])
    libm, err = construire(mut, "gele")
    if libm is None:
        ctrl(False, "le mutant compile", err[:300])
        return
    libm.dn_hist_couverture_s.restype = ctypes.c_uint32
    _, gm, cm = apres_pause(libm, 25)
    ctrl(gm[0] and gm[1] == 500,
         "MUTÉ ⇒ le MIN/MAX long REPUBLIE la valeur vieille de 25 h",
         "le défaut est REPRODUIT : min = %d" % gm[1])
    ctrl(cm > 0,
         "MUTÉ ⇒ la couverture repart de zéro sur du vide",
         "%d s annoncées sans un seul échantillon dans la fenêtre" % cm)


def main():
    src, sha_c = lire(DN_HIST_C)
    _, sha_h = lire(DN_HIST_H)
    print("=" * 78)
    print("dn4-13 / AC2 — `dn_hist` COMPILÉ SUR L'HÔTE ET APPELÉ")
    print("=" * 78)
    print("  dn_hist.c sha256[:16] = %s" % sha_c)
    print("  dn_hist.h sha256[:16] = %s" % sha_h)
    # 🔴 dn4-39 / AC39.3.b — L'ARBRE LVGL EST UN **PREREQUIS**, ET IL SE DIT.
    #    Toute la suite en depend : la sentinelle relue alimente le shim qui
    #    compile `dn_hist.c`. Sans elle la gate n'a rien a exercer — elle le
    #    DECLARE et sort en RC_PREREQUIS, ⛔ elle ne plante plus.
    if not os.path.isfile(LV_CHART_H):
        print("\nECHEC : en-tete LVGL amont introuvable : %s" % LV_CHART_H)
        print("        `managed_components/` est gitignore mais regenere :")
        print("        lancer `idf.py reconfigure` dans firmware/desknode.")
        print("        MOTIF : `LV_CHART_POINT_NONE` se RELIT dans l'arbre LVGL,")
        print("                ⛔ elle n'est jamais recopiee ici — c'est ce qui")
        print("                garantit que `DN_HIST_TROU` vaut le trou de LVGL.")
        print("        ⛔ CE N'EST PAS UN VERDICT SUR `dn_hist.c`, et ⛔ pas un")
        print("           skip : rc=%d, declare dans la table NON_JOUABLES de"
              % RC_PREREQUIS)
        print("           tools/run_gates.sh.")
        return RC_PREREQUIS
    sent = sentinelle_lvgl()
    print("  LV_CHART_POINT_NONE relu de lv_chart.h = %s" % sent)
    if not ctrl(sent == "INT32_MAX",
                "la sentinelle LVGL est bien `INT32_MAX`",
                "⛔ sinon `DN_HIST_TROU` ne vaut plus le trou de LVGL"):
        return 1
    if shutil.which("gcc") is None:
        ctrl(False, "gcc est disponible", "⛔ la gate ne peut RIEN exécuter")
        return 1

    lib, err = construire(src, "base")
    if lib is None:
        ctrl(False, "`dn_hist.c` compile sur l'hôte", err[:400])
        return 1
    ctrl(True, "`dn_hist.c` compile et se charge sur l'hôte", "gcc -O0 -shared")

    rc_cout = bloc_cout(lib)
    bloc_avant_init(src, lib)
    bloc_couverture(src)
    bloc_axe_temps(src)
    bloc_revue_2026_08_25(src)
    bloc_seaux(src)
    bloc_ecrits(src)

    print("\n" + "=" * 78)
    print("⚠️ CE QUE CETTE GATE NE SOLDE PAS : les témoins CARTE — AC2.2")
    print("   (allumée > 1 h sans source PC) et AC3.3 (`ui off` >= 60 s, le")
    print("   verdict à l'œil ET par `hist`) —, et le `.map`")
    print("   qu'elle lit est celui du DERNIER `idf.py build` — pas du binaire")
    print("   flashé. Le SHA au bandeau reste la seule preuve de ce qui tourne.")
    if ko_total[0] == 0:
        # 🔴 REVUE 2026-09-02 — L'ORDRE EST UNE REGLE : un VRAI defaut l'emporte
        #    sur un prerequis absent. Le rc de `bloc_cout` n'etait PAS LU : son
        #    `return` etait mort-ne. Il remonte desormais, APRES les KO.
        if rc_cout == RC_PREREQUIS:
            print("⚠️ %d contrôles passent, 0 échec — mais le `.map` manquait :"
                  " rc=%d (prérequis absent)." % (ok_total[0], RC_PREREQUIS))
            return RC_PREREQUIS
        print("✅ %d contrôles passent, 0 échec." % ok_total[0])
        return 0
    print("⛔ %d ÉCHEC(S) sur %d contrôles."
          % (ko_total[0], ok_total[0] + ko_total[0]))
    return 1


if __name__ == "__main__":
    code = main()
    for d in _tmp:
        shutil.rmtree(d, ignore_errors=True)
    sys.exit(code)

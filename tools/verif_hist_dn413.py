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


def ctrl(ok, libelle, detail=""):
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
        ctrl(False, "le `.map` du build est présent",
             "⛔ absent — lancer `idf.py build` avant cette gate")
        return
    attendus = ["s_pts", "s_smin", "s_smax", "s_svu", "s_w", "s_pret",
                "s_seau_courant"]
    manquants = [s for s in attendus if s not in sym]
    ctrl(not manquants, "les 7 symboles de `dn_hist` sont dans le `.map`",
         "manquants : %s" % (manquants or "aucun"))
    ctrl("s_seaux_ouverts" not in sym,
         "`s_seaux_ouverts` a DISPARU du `.map` (AC2.2)",
         "supprimé, pas seulement débranché")
    somme = sum(sym.get(s, 0) for s in attendus)
    print("     `.map` : " + " · ".join("%s %d" % (s, sym.get(s, 0))
                                        for s in attendus))
    ctrl(somme == tot,
         "le coût déclaré == le coût du `.map`",
         "declare %d o, map %d o, ecart %+d o" % (tot, somme, tot - somme))


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


def main():
    src, sha_c = lire(DN_HIST_C)
    _, sha_h = lire(DN_HIST_H)
    print("=" * 78)
    print("dn4-13 / AC2 — `dn_hist` COMPILÉ SUR L'HÔTE ET APPELÉ")
    print("=" * 78)
    print("  dn_hist.c sha256[:16] = %s" % sha_c)
    print("  dn_hist.h sha256[:16] = %s" % sha_h)
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

    bloc_cout(lib)
    bloc_avant_init(src, lib)
    bloc_couverture(src)

    print("\n" + "=" * 78)
    print("⚠️ CE QUE CETTE GATE NE SOLDE PAS : le témoin d'AC2.2 sur la CARTE")
    print("   (allumée > 1 h sans source PC, l'œil sur la page), et le `.map`")
    print("   qu'elle lit est celui du DERNIER `idf.py build` — pas du binaire")
    print("   flashé. Le SHA au bandeau reste la seule preuve de ce qui tourne.")
    if ko_total[0] == 0:
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

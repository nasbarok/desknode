#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
`dn4-43` / AC5 — LE PREMIER DEMARRAGE SE DIT, ET IL SE TERMINE SUR UN CRITERE
                 RELU.

═══════════════════════════════════════════════════════════════════════════════
🔴 CE QUE CETTE GATE FAIT, ET QUI LA DISTINGUE D'UNE GATE QUI LIT
═══════════════════════════════════════════════════════════════════════════════

Elle **COMPILE `dn_demarrage.c` ET APPELLE SES FONCTIONS**, avec de vrais
chiffres, en ctypes — exactement comme `tools/verif_veille_dn33.py` le fait
pour la veille. ⛔ Elle ne se contente PAS de chercher des motifs : un `grep`
qui trouve `err_i2c` dans un fichier ne prouve pas que le firmware S'EN SERT
pour decider.

✅ **ET LE MODULE N'A AUCUN SHIM A ECRIRE** : `dn_demarrage.c` n'inclut NI LVGL,
   NI ESP-IDF, NI meme `esp_log.h`. La gate de la veille, elle, porte quatre
   coquilles (`esp_err.h`, `esp_log.h`, `esp_timer.h`, `nvs.h`) — c'est-a-dire
   quatre occasions de deriver. Ici il n'y en a **zero**, et le controle n° 14
   garde cette propriete.

═══════════════════════════════════════════════════════════════════════════════
🔴 CE QU'ELLE CONTROLE (AC5.2)
═══════════════════════════════════════════════════════════════════════════════

  1. LA DECISION S'EXECUTE — 12 controles, sur le module COMPILE
  2. LE CRITERE N'EST PAS UN MINUTEUR — 3 controles, sur la source
  3. L'ETAT EST ATTEINT AU BOOT, ET NE SE RE-AFFICHE PAS — 7 controles
  4. LES LIBELLES : table, polices, largeurs, DEUX langues — 5 controles
  5. LE BUDGET EST GARDE PAR LE COMPILATEUR — 3 controles
  6. LA CONSOLE ET LE DOSSIER LE DISENT — 3 controles

Sortie : `BILAN : n OK, m KO`, rc 0 si tout passe, 1 sinon.
Usage  : python3 tools/verif_demarrage_dn443.py [--mutant <n>] [--liste-mutants]
         `--mutant` casse UNE propriete EN MEMOIRE et doit faire ROUGIR (AC5.3).
         ⛔ Aucun fichier du depot n'est modifie.

⚠️ **UN MUTANT QUI DEBRANCHE LA GARDE NE PROUVE RIEN.** Les mutants d'ici
   REPLANTENT la faute (ils suppriment le garde-fou du vide, inversent l'ordre
   critere/plafond, retirent le test d'underflow…) et la gate doit la VOIR.
"""

import argparse
import ctypes
import os
import re
import shutil
import subprocess
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "tools"))
import dn_police  # noqa: E402  — bibliotheque du depot, ⛔ pas une gate

MAIN = os.path.join(RACINE, "firmware", "desknode", "main")
F_DEM_C = os.path.join(MAIN, "dn_demarrage.c")
F_DEM_H = os.path.join(MAIN, "dn_demarrage.h")
F_UI_C = os.path.join(MAIN, "dn_ui.c")
F_UI_H = os.path.join(MAIN, "dn_ui.h")
F_MAIN_C = os.path.join(MAIN, "desknode_main.c")
F_LANGUE_H = os.path.join(MAIN, "dn_langue.h")
F_CONSOLE = os.path.join(MAIN, "dn_console.c")
F_CMAKE = os.path.join(MAIN, "CMakeLists.txt")
F_README = os.path.join(RACINE, "README.md")

# Les cinq cles que cette story ajoute a la table. ⚠️ RELUES du bloc de
# `dn_ui.c`, ⛔ pas recitees ici — voir `cles_de_l_ecran()`.
PREFIXE_CLE = "DEM_"

OK = [0]
KO = [0]
_MUTANT = None
_TMPDIRS = []

# ══════════════════════════════════════════════════════════════════════════════
# LES MUTANTS — DECLARES AU NIVEAU MODULE, ⛔ PAS DANS `main()`.
#
# 🔴 LE MOTIF EST DU VECU : `dn4-42` a trouve que ses mutants etaient declares
#    APRES le retour anticipe de `--liste-mutants`, qui imprimait donc une liste
#    VIDE, en silence. Une campagne qui s'en servait pour boucler ne tirait
#    AUCUN mutant tout en annoncant un bilan.
# 🔴 ET CHAQUE NUMERO DECLARE ICI DOIT ETRE BALAYE (AC5.3) : un mutant declare
#    et JAMAIS APPLIQUE reste VERT, et la campagne annonce un bilan quand meme.
# ══════════════════════════════════════════════════════════════════════════════
MUTANTS = {}
MUTANTS[1] = "supprime le GARDE-FOU DU VIDE (la fenetre conclut sans lectures)"
MUTANTS[2] = "inverse l'ordre CRITERE / PLAFOND dans dn_dem_tick"
MUTANTS[3] = "cesse de casser la fenetre sur une erreur nouvelle (minuteur pur)"
MUTANTS[4] = "retire le REFUS de re-armement (AC1.4 tomberait)"
MUTANTS[5] = "retire le test d'UNDERFLOW des compteurs remis a zero"
MUTANTS[6] = "fait conclure PROPRE quand le tactile est ABSENT"
MUTANTS[7] = "fait rendre au `default` de verdict_nom le mot d'un AUTRE verdict"
MUTANTS[8] = "fait entrer `esp_log.h` dans dn_demarrage.c (la gate ne compile plus)"
MUTANTS[9] = "appelle `dn_dem_reset_pour_gate()` depuis le firmware"
MUTANTS[10] = "construit l'ecran de demarrage AVANT `build_scene()`"
MUTANTS[11] = "ne CHARGE pas l'ecran de demarrage (il existe sans etre atteint)"
MUTANTS[12] = "arme l'observation AVANT `dn_touch_attach_lvgl` (la course)"
MUTANTS[13] = "retire la conclusion en tete de `build_scene()` (AC1.4)"
MUTANTS[14] = "donne un SECOND appelant a `demarrage_construire()`"
MUTANTS[15] = "vide la traduction FR d'une cle de l'ecran de demarrage"
MUTANTS[16] = "remet un `—` (U+2014) dans un libelle de l'ecran"
MUTANTS[17] = "allonge un libelle au-dela de la largeur de la dalle"
MUTANTS[18] = "remet un litteral francais en dur dans l'ecran de demarrage"
MUTANTS[19] = "revele le 2e temps sur un DELAI au lieu des erreurs mesurees"
MUTANTS[20] = "casse l'addition du budget VERTICAL (les lignes se chevauchent)"
MUTANTS[21] = "casse l'arithmetique du budget TEMPOREL (fenetre inatteignable)"
MUTANTS[22] = "retire la relecture de la hauteur de ligne a la construction"
MUTANTS[23] = "cesse de publier un compteur de l'etat de demarrage a la console"
MUTANTS[24] = "efface la ligne Known-issues des 55,5 % auto-retablis"
MUTANTS[25] = "efface, au README, ce que l'etat de demarrage SIGNIFIE"
MUTANTS[26] = "fait ignorer le parametre `lectures` a la decision"
MUTANTS[27] = "retire les `_Static_assert` du budget temporel"


def dire(ok, libelle, detail=""):
    (OK if ok else KO)[0] += 1
    print("  [%s] %-58s %s" % ("OK " if ok else "KO ", libelle, detail))


def lire(chemin):
    with open(chemin, encoding="utf-8", errors="replace") as f:
        return f.read()


def sans_commentaires(src):
    """Retire les commentaires C. ⛔ GARDE les chaines.

    ⚠️ Motif DEJA PAYE par ce depot : *« un jeton cite en commentaire est
       ACCORDE »*. Sans ce retrait, un exemple ecrit dans un commentaire ferait
       rougir — ou VERDIR — un fichier a tort.
    """
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    src = re.sub(r"//[^\n]*", " ", src)
    return src


def M(n, src, avant, apres):
    """Mutation ciblee : si `--mutant n`, remplace `avant` par `apres`."""
    if _MUTANT != n:
        return src
    if avant not in src:
        sys.exit("MUTANT %d INAPPLICABLE : le motif est introuvable. ⛔ Un "
                 "mutant qui ne s'applique pas ne prouve RIEN — il faut le "
                 "reparer, ⛔ pas conclure que le controle est vert." % n)
    return src.replace(avant, apres, 1)


def defini(src, nom, env=None):
    """La valeur ENTIERE d'un `#define <nom> …`, EXPRESSION et suffixe `u`
    compris. Rend None si la gate n'a pas su lire — ⛔ elle ne devine pas."""
    m = re.search(r"^#define\s+%s\s+([^\n/]+)" % re.escape(nom), src, re.M)
    if not m:
        return None
    expr = m.group(1).strip()
    expr = re.sub(r"(\d)[uU]\b", r"\1", expr)
    env = env or {}
    for ident in set(re.findall(r"[A-Za-z_]\w*", expr)):
        if ident not in env or env[ident] is None:
            return None
        expr = re.sub(r"\b%s\b" % re.escape(ident), str(env[ident]), expr)
    if not re.fullmatch(r"[\d\s()+\-*/]+", expr):
        return None
    try:
        return int(eval(expr))  # noqa: S307 — expression BORNEE au motif ci-dessus
    except (SyntaxError, ZeroDivisionError, ValueError):
        return None


def deplier_c(litt):
    r"""Le contenu REEL d'un litteral C, concatenations et `\xHH` compris."""
    morceaux = re.findall(r'"((?:\\.|[^"\\])*)"', litt)
    brut = "".join(morceaux)
    out, i = [], 0
    while i < len(brut):
        c = brut[i]
        if c == "\\" and i + 1 < len(brut):
            n = brut[i + 1]
            if n == "x":
                j = i + 2
                while j < len(brut) and j < i + 4 and brut[j] in "0123456789abcdefABCDEF":
                    j += 1
                out.append(chr(int(brut[i + 2:j], 16)))
                i = j
                continue
            out.append({"n": "\n", "t": "\t", "\\": "\\", '"': '"', "0": "\0"}.get(n, n))
            i += 2
            continue
        out.append(c)
        i += 1
    s = "".join(out)
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


# ══════════════════════════════════════════════════════════════════════════════
# 1. LA DECISION S'EXECUTE — LE MODULE EST COMPILE ET APPELE
# ══════════════════════════════════════════════════════════════════════════════

def construire_module(src_c, src_h, etiquette):
    """Compile `dn_demarrage.c` (ou une MUTATION) en `.so`, rend le handle."""
    d = tempfile.mkdtemp(prefix="dn443_")
    _TMPDIRS.append(d)
    with open(os.path.join(d, "dn_demarrage.h"), "w", encoding="utf-8") as f:
        f.write(src_h)
    with open(os.path.join(d, "dn_demarrage.c"), "w", encoding="utf-8") as f:
        f.write(src_c)
    so = os.path.join(d, "libdem.so")
    r = subprocess.run(
        ["cc", "-shared", "-fPIC", "-O0", "-std=c11", "-I", d, "-o", so,
         os.path.join(d, "dn_demarrage.c")],
        capture_output=True, text=True)
    if r.returncode != 0:
        print("    ⛔ ECHEC DE COMPILATION (%s) :\n%s"
              % (etiquette, r.stderr[:2500]))
        return None
    return ctypes.CDLL(so)


def api(lib):
    """⚠️ UN ECHEC DE COMPILATION DOIT **ROUGIR**, ⛔ PAS EXPLOSER EN TRACEBACK :
    une gate qui plante ne dit pas « KO », elle dit « je n'ai pas tourne ». Les
    deux se lisent tres differemment dans un dossier de mesure."""
    if lib is None:
        return None
    lib.dn_dem_armer.restype = None
    lib.dn_dem_armer.argtypes = [ctypes.c_uint32, ctypes.c_bool,
                                 ctypes.c_uint32, ctypes.c_uint32]
    lib.dn_dem_tick.restype = ctypes.c_int
    lib.dn_dem_tick.argtypes = [ctypes.c_uint32, ctypes.c_uint32,
                                ctypes.c_uint32]
    lib.dn_dem_conclure.restype = None
    lib.dn_dem_conclure.argtypes = [ctypes.c_uint32, ctypes.c_int]
    for nom in ("dn_dem_verdict", "dn_dem_duree_ms", "dn_dem_err_vues",
                "dn_dem_fenetres_cassees", "dn_dem_lectures_vues",
                "dn_dem_rearmements_refuses"):
        getattr(lib, nom).restype = ctypes.c_uint32
        getattr(lib, nom).argtypes = []
    for nom in ("dn_dem_arme", "dn_dem_en_cours"):
        getattr(lib, nom).restype = ctypes.c_bool
        getattr(lib, nom).argtypes = []
    lib.dn_dem_verdict_nom.restype = ctypes.c_char_p
    lib.dn_dem_verdict_nom.argtypes = [ctypes.c_int]
    lib.dn_dem_reset_pour_gate.restype = None
    lib.dn_dem_reset_pour_gate.argtypes = []
    return lib


# Les verdicts, dans l'ordre de l'enum. ⚠️ RELUS de l'en-tete, ⛔ pas recites.
def verdicts_de_l_entete(src_h):
    bloc = re.search(r"typedef enum \{(.*?)\} dn_dem_verdict_t;", src_h, re.S)
    if not bloc:
        return []
    # 🔴 L'INITIALISEUR EST OBLIGATOIRE DANS LE MOTIF, ⛔ PAS OPTIONNEL A
    #    L'OEIL : la premiere entree s'ecrit `DN_DEM_EN_COURS = 0,` et un motif
    #    `(DN_DEM_[A-Z_]+),` la MANQUAIT — la liste rendue commencait alors a
    #    `FIN_PROPRE`, tous les indices etaient DECALES DE UN, et CINQ controles
    #    d'execution rougissaient sur du code JUSTE. Trouve en jouant la gate au
    #    premier tir, ⛔ pas en la relisant.
    return re.findall(r"^\s*(DN_DEM_[A-Z_]+)\s*(?:=\s*\d+\s*)?,",
                      sans_commentaires(bloc.group(1)), re.M)


def jouer(lib, etapes, tactile=True, t0=1000, pas=250):
    """Rejoue une histoire de compteurs. `etapes` = [(n_ticks, d_err, d_lect)].
    Rend (verdict, duree_ms, ticks_joues)."""
    lib.dn_dem_reset_pour_gate()
    t, err, lect, joues = t0, 0, 0, 0
    lib.dn_dem_armer(t, tactile, err, lect)
    for (n, d_err, d_lect) in etapes:
        for _ in range(n):
            t += pas
            err += d_err
            lect += d_lect
            joues += 1
            v = lib.dn_dem_tick(t, err, lect)
            if v != 0:
                return v, lib.dn_dem_duree_ms(), joues
    return lib.dn_dem_verdict(), lib.dn_dem_duree_ms(), joues


def muter_module(src_c):
    """🔴 LES MUTATIONS DU MODULE SONT APPLIQUEES **UNE FOIS**, ET LE RESULTAT
    SERT AUX DEUX SECTIONS QUI LE REGARDENT.

    ⛔ Elles vivaient dans `section_execution()` seule — c'est-a-dire que la
    section 2, qui LIT la source, voyait toujours le fichier SAIN. Le mutant 2
    (ordre critere/plafond inverse) restait donc VERT : la section 1 ne le voit
    que si les deux conditions tombent au MEME tick, et la section 2 ne le
    voyait pas du tout. **Une mutation qui n'atteint pas le controle qu'elle
    vise ne prouve rien.** Trouve en balayant tous les numeros, ⛔ pas en
    relisant.
    """
    src_c = M(1, src_c, "&& s_lectures_vues >= DN_DEM_LECTURES_MIN", "")
    src_c = M(2, src_c,
              """    if ((uint32_t)(t_ms - s_fen_t0_ms) >= DN_DEM_FENETRE_MS
        && s_lectures_vues >= DN_DEM_LECTURES_MIN) {
        conclure(t_ms, DN_DEM_FIN_PROPRE);
        return s_verdict;
    }

    if ((uint32_t)(t_ms - s_t0_ms) >= DN_DEM_PLAFOND_MS) {
        conclure(t_ms, DN_DEM_FIN_PLAFOND);
        return s_verdict;
    }""",
              """    if ((uint32_t)(t_ms - s_t0_ms) >= DN_DEM_PLAFOND_MS) {
        conclure(t_ms, DN_DEM_FIN_PLAFOND);
        return s_verdict;
    }

    if ((uint32_t)(t_ms - s_fen_t0_ms) >= DN_DEM_FENETRE_MS
        && s_lectures_vues >= DN_DEM_LECTURES_MIN) {
        conclure(t_ms, DN_DEM_FIN_PROPRE);
        return s_verdict;
    }""")
    src_c = M(3, src_c, "if (err_i2c != s_fen_err0 || lectures < s_fen_lect0) {",
              "if (0) {")
    src_c = M(4, src_c, """    if (s_verdict != DN_DEM_EN_COURS) {
        s_rearm_refuses++;
        return;
    }
    if (s_arme) {
        s_rearm_refuses++;
        return;
    }""", "")
    src_c = M(5, src_c, "err_i2c != s_fen_err0 || lectures < s_fen_lect0",
              "err_i2c != s_fen_err0")
    src_c = M(6, src_c, "conclure(t_ms, DN_DEM_FIN_SANS_TACTILE);",
              "conclure(t_ms, DN_DEM_FIN_PROPRE);")
    # ⚠️ LE MUTANT 7 REPLANTE LA FAUTE, ⛔ il ne debranche pas la garde : il fait
    #    rendre au `default` **le mot d'un AUTRE verdict**. Sa premiere version
    #    remplacait `default:` par `case 99:` — `verdict_nom(99)` rendait alors
    #    toujours « ? » et le controle restait VERT. *Un mutant qui ne replante
    #    pas la faute ne prouve que son existence.*
    src_c = M(7, src_c, '    default:\n        /* ⛔ NE PAS ENLEVER',
              '    default:\n        return "PROPRE";\n        /* ⛔ NE PAS ENLEVER')
    src_c = M(8, src_c, '#include "dn_demarrage.h"',
              '#include "dn_demarrage.h"\n#include "esp_log.h"')
    src_c = M(26, src_c, "s_lectures_vues = lectures - s_fen_lect0;",
              "s_lectures_vues = DN_DEM_LECTURES_MIN;")
    return src_c


def section_execution(src_c, src_h, cst):
    print("\n── 1. LA DECISION S'EXECUTE — MODULE COMPILE ET APPELE ────────")

    lib = api(construire_module(src_c, src_h, "module du depot"))
    dire(lib is not None, "le module COMPILE — ⛔ et sans un seul shim",
         "cc -std=c11, zero en-tete du framework"
         if lib else "⛔ la gate n'a RIEN pu eprouver")
    if lib is None:
        return

    V = {n: i for i, n in enumerate(verdicts_de_l_entete(src_h))}
    en_cours = V.get("DN_DEM_EN_COURS", 0)
    propre = V.get("DN_DEM_FIN_PROPRE", 1)
    sans_tact = V.get("DN_DEM_FIN_SANS_TACTILE", 2)
    plafond = V.get("DN_DEM_FIN_PLAFOND", 3)

    fen = cst["DN_DEM_FENETRE_MS"]
    lmin = cst["DN_DEM_LECTURES_MIN"]
    plaf = cst["DN_DEM_PLAFOND_MS"]

    # ── Le BOOT SAIN : 5 cas sur 6 (§13.17.1). 25 lectures/s, ZERO erreur. ──
    v, duree, _ = jouer(lib, [(400, 0, 6)])
    dire(v == propre,
         "boot SAIN : conclut PROPRE, ⛔ pas au plafond",
         "verdict=%s" % lib.dn_dem_verdict_nom(v).decode())
    dire(v == propre and duree <= fen + 300,
         "boot SAIN : et il est BREF (AC1.3)",
         "%d ms pour une fenetre de %d ms" % (duree, fen))

    # ── LA FENETRE FROIDE : 55,5 % d'erreurs pendant ~40 s, puis reprise. ──
    v, duree, _ = jouer(lib, [(160, 3, 6)])
    dire(v == en_cours,
         "erreurs CONTINUES : reste EN COURS bien apres la fenetre",
         "40 s d'erreurs, verdict=%s" % lib.dn_dem_verdict_nom(v).decode())
    dire(lib.dn_dem_fenetres_cassees() > 0,
         "…et chaque erreur nouvelle RELANCE la fenetre",
         "%d relance(s)" % lib.dn_dem_fenetres_cassees())
    dire(lib.dn_dem_err_vues() > 0,
         "…et les erreurs vues sont COMPTEES (elles arment le 2e temps)",
         "%d erreur(s)" % lib.dn_dem_err_vues())

    v, duree, _ = jouer(lib, [(160, 3, 6), (400, 0, 6)])
    dire(v == propre and duree < plaf,
         "reprise : conclut PROPRE — le critere est RELU, ⛔ pas minute",
         "%d ms, plafond %d ms" % (duree, plaf))

    # ── 🔴 CRITERE ET PLAFOND AU **MEME TICK** — c'est le SEUL cas ou leur
    #    ordre se voit, et c'est pour ca qu'il est joue. Les erreurs s'arretent
    #    exactement `DN_DEM_FENETRE_MS` avant l'expiration du plafond. ──
    n_err = (plaf - fen) // 250
    v, duree, _ = jouer(lib, [(n_err, 3, 6), (100, 0, 6)])
    dire(v == propre,
         "critere ET plafond au MEME tick : c'est l'ETAT qui tranche",
         "%d ms — un PLAFOND ici lirait « on a cesse d'attendre » sur une "
         "carte RETABLIE (verdict=%s)"
         % (duree, lib.dn_dem_verdict_nom(v).decode()))

    # ── 🔴 LE PIEGE DU VIDE : compteurs FIGES, aucune lecture. ──
    v, duree, _ = jouer(lib, [(500, 0, 0)])
    dire(v != propre,
         "PIEGE DU VIDE : compteurs figes ⇒ ⛔ JAMAIS « PROPRE »",
         "verdict=%s" % lib.dn_dem_verdict_nom(v).decode())
    dire(v == plafond and duree >= plaf,
         "…c'est le PLAFOND qui tranche, et il se NOMME",
         "%d ms >= %d ms" % (duree, plaf))

    # ── Une fenetre PEUPLEE mais trop MAIGRE ne conclut pas non plus. ──
    v, _, _ = jouer(lib, [(400, 0, 0)], pas=int(fen))
    dire(v != propre,
         "fenetre a MOINS de %d lecture(s) ⇒ ⛔ ne conclut pas" % lmin,
         "verdict=%s" % lib.dn_dem_verdict_nom(v).decode())

    # ── Tactile ABSENT : l'observation est IMPOSSIBLE, ⛔ pas concluante. ──
    v, _, joues = jouer(lib, [(10, 0, 0)], tactile=False)
    dire(v == sans_tact,
         "tactile ABSENT : « SANS TACTILE », ⛔ jamais « PROPRE »",
         "verdict=%s des le %de tick" % (lib.dn_dem_verdict_nom(v).decode(), joues))

    # ── UNDERFLOW : `touch reset` remet les compteurs a zero en pleine
    #    observation. Sans garde, `lectures - s_fen_lect0` rendrait ~4e9. ──
    # 🔴 L'ARMEMENT SE FAIT AVEC DES COMPTEURS **DEJA NON NULS**, et ce n'est
    #    pas un detail de scenario : `app_main` arme APRES le branchement de
    #    l'indev, donc LVGL a deja pu lire. Sans ca, `s_fen_lect0` vaut 0 et la
    #    soustraction ne peut PAS deborder — le scenario mesurait du vide, et le
    #    mutant 5 restait VERT sur une garde pourtant absente. Trouve en
    #    balayant, ⛔ pas en relisant.
    lib.dn_dem_reset_pour_gate()
    lib.dn_dem_armer(1000, True, 0, 30)
    t = 1000
    for lect in (36, 42, 48):
        t += 250
        lib.dn_dem_tick(t, 0, lect)
    for _ in range(3):                     # ⇒ `touch reset` : les stats retombent
        t += 250
        v = lib.dn_dem_tick(t, 0, 0)
    dire(v == en_cours,
         "UNDERFLOW : compteurs remis a zero ⇒ ⛔ pas de « PROPRE » par debordement",
         "verdict=%s" % lib.dn_dem_verdict_nom(v).decode())

    # ── AC1.4 : IL NE SE RE-ARME JAMAIS. ──
    jouer(lib, [(400, 0, 6)])
    avant = lib.dn_dem_verdict()
    refus_avant = lib.dn_dem_rearmements_refuses()
    lib.dn_dem_armer(999999, True, 0, 0)
    dire(lib.dn_dem_verdict() == avant
         and lib.dn_dem_rearmements_refuses() == refus_avant + 1,
         "AC1.4 : un 2e armement apres une fin est REFUSE, et COMPTE",
         "refus %d -> %d" % (refus_avant, lib.dn_dem_rearmements_refuses()))

    # ── Le nom d'un verdict hors enum. ⛔ Jamais le mot d'un autre. ──
    hors = lib.dn_dem_verdict_nom(99).decode()
    connus = {lib.dn_dem_verdict_nom(i).decode() for i in V.values()}
    dire(hors == "?" and hors not in connus,
         "verdict HORS ENUM : rend « ? », ⛔ pas le mot d'un autre verdict",
         "rendu « %s »" % hors)


# ══════════════════════════════════════════════════════════════════════════════
# 2. LE CRITERE N'EST PAS UN MINUTEUR
# ══════════════════════════════════════════════════════════════════════════════

def section_critere(src_c, src_h):
    print("\n── 2. LE CRITERE SE RELIT DE L'ETAT, ⛔ IL NE SE MINUTE PAS ────")
    nu = sans_commentaires(src_c)

    sig = re.search(r"dn_dem_tick\(uint32_t t_ms, uint32_t err_i2c,\s*"
                    r"uint32_t lectures\)\s*\{(.*?)\n\}", nu, re.S)
    corps = sig.group(1) if sig else ""
    dire(bool(corps) and "err_i2c" in corps and "lectures" in corps,
         "`dn_dem_tick` LIT les DEUX compteurs, ⛔ pas seulement l'horloge",
         "err_i2c %d fois, lectures %d fois"
         % (corps.count("err_i2c"), corps.count("lectures")))

    i_propre = corps.find("DN_DEM_FIN_PROPRE")
    i_plafond = corps.find("DN_DEM_FIN_PLAFOND")
    dire(0 <= i_propre < i_plafond,
         "le critere RELU est teste **AVANT** le plafond",
         "PROPRE en %d, PLAFOND en %d" % (i_propre, i_plafond))

    includes = re.findall(r'^#include\s+[<"]([^">]+)[">]', src_c, re.M)
    interdits = [h for h in includes
                 if h not in ("dn_demarrage.h", "stdbool.h", "stdint.h")]
    dire(not interdits,
         "⛔ AUCUN en-tete du framework dans `dn_demarrage.c`",
         "sinon la gate ne pourrait plus l'EXECUTER · vus : %s"
         % (", ".join(interdits) if interdits else "aucun"))


# ══════════════════════════════════════════════════════════════════════════════
# 3. L'ETAT EST ATTEINT AU BOOT, ET IL NE SE RE-AFFICHE PAS
# ══════════════════════════════════════════════════════════════════════════════

def section_boot(ui_c, main_c, ui_h):
    print("\n── 3. IL EST ATTEINT AU BOOT, ET ⛔ NE SE RE-AFFICHE PAS ───────")

    ui_c = M(10, ui_c, "    build_scene();\n    /*\n     * 🔴 `dn4-43` — **L'ÉTAT",
             "    demarrage_construire();\n    build_scene();\n    /*\n     * 🔴 `dn4-43` — **L'ÉTAT")
    ui_c = M(11, ui_c, "    lv_screen_load(s_scr_dem);", "")
    ui_c = M(13, ui_c, "    demarrage_conclure_nolock(DN_DEM_FIN_RECONSTRUCTION);", "")
    ui_c = M(14, ui_c, "    dn_touch_set_contact_cb(veille_contact_cb);",
             "    demarrage_construire();\n    dn_touch_set_contact_cb(veille_contact_cb);")
    main_c = M(12, main_c, """    bool tactile_present = false;
    if (touch_err == ESP_OK) {""",
               """    bool tactile_present = false;
    dn_ui_demarrage_armer(tactile_present);
    if (touch_err == ESP_OK) {""")
    ui_c = M(9, ui_c, "static void dem_tick(lv_timer_t *t)\n{\n    (void)t;",
             "static void dem_tick(lv_timer_t *t)\n{\n    (void)t;\n    dn_dem_reset_pour_gate();")

    nu_ui = sans_commentaires(ui_c)
    nu_main = sans_commentaires(main_c)

    init = re.search(r"esp_err_t dn_ui_init\(.*?\n\}", nu_ui, re.S)
    corps_init = init.group(0) if init else ""
    i_build = corps_init.find("build_scene();")
    i_constr = corps_init.find("demarrage_construire();")
    dire(i_build >= 0 and i_constr > i_build,
         "`dn_ui_init` construit l'ecran de demarrage APRES `build_scene()`",
         "⛔ avant, elle le detruirait aussitot (AC1.4)")

    constr = re.search(r"static void demarrage_construire\(void\)\s*\{(.*?)\n\}",
                       nu_ui, re.S)
    dire(bool(constr) and "lv_screen_load(s_scr_dem)" in constr.group(1),
         "…et elle le CHARGE — ⛔ un ecran cree n'est pas un ecran ATTEINT",
         "l'allumage de l'etape 7 doit le porter")

    dire(nu_ui.count("demarrage_construire();") == 1,
         "`demarrage_construire()` n'a qu'UN SEUL appelant (AC1.4)",
         "%d appel(s) dans dn_ui.c" % nu_ui.count("demarrage_construire();"))

    i_attach = nu_main.find("dn_touch_attach_lvgl")
    i_armer = nu_main.find("dn_ui_demarrage_armer")
    dire(i_attach >= 0 and i_armer > i_attach,
         "`app_main` arme APRES `dn_touch_attach_lvgl` — ⛔ la course",
         "arme avant, « SANS TACTILE » tomberait sur une carte SAINE")

    i_bl = nu_main.find("dn_display_backlight_pct(bl_boot)")
    dire(i_armer >= 0 and i_bl > i_armer,
         "…et AVANT l'allumage du retroeclairage (etape 7)",
         "sinon l'inconnu verrait le dashboard trompeur d'abord")

    bs = re.search(r"static void build_scene\(void\)\s*\{(.{0,900})", nu_ui, re.S)
    dire(bool(bs) and "demarrage_conclure_nolock" in bs.group(1),
         "`build_scene()` CONCLUT l'etat de demarrage en tete (AC1.4)",
         "⛔ sinon `s_scr_dem` devient un pointeur PENDANT")

    appels_reset = len(re.findall(r"dn_dem_reset_pour_gate\s*\(", nu_ui + nu_main))
    dire(appels_reset == 0,
         "⛔ `dn_dem_reset_pour_gate()` n'a AUCUN appelant dans le firmware",
         "%d appel(s) — il ne sert QUE la gate" % appels_reset)


# ══════════════════════════════════════════════════════════════════════════════
# 4. LES LIBELLES — TABLE, POLICES, LARGEURS, DEUX LANGUES
# ══════════════════════════════════════════════════════════════════════════════

def cles_de_l_ecran(ui_c):
    """Les cles RELUES du tableau `lignes[]` de `demarrage_construire()`, avec
    leur police. ⛔ Rien n'est recite ici : une cle ajoutee a l'ecran entre dans
    le controle SANS qu'on touche a la gate."""
    bloc = re.search(r"\} lignes\[\] = \{(.*?)\n    \};", ui_c, re.S)
    if not bloc:
        return []
    return re.findall(r"\{DN_T_(\w+),\s*&(dn_font_\d+)", bloc.group(1))


def section_libelles(ui_c, langue_h, polices):
    print("\n── 4. LES LIBELLES : TABLE, POLICES, LARGEURS, 2 LANGUES ──────")

    langue_h = M(15, langue_h, '"DÉMARRAGE..."', '""')
    langue_h = M(16, langue_h, '"contrôle du bus I2C"', '"contrôle — bus I2C"')
    langue_h = M(17, langue_h,
                 '"this is known, and it recovers on its own"',
                 '"this is a known transient condition and it recovers all by itself"')
    ui_c = M(18, ui_c, "{DN_T_DEM_CONTROLE, &dn_font_18, 0xc0d8e8, DEM_Y_CTRL, DEM_LH_18,\n         \"controle\", NULL},",
             "{DN_T_AUCUN, &dn_font_18, 0xc0d8e8, DEM_Y_CTRL, DEM_LH_18,\n         \"controle\", NULL},")
    if _MUTANT == 18:
        ui_c = ui_c.replace(
            "        lv_obj_t *l = texte(s_scr_dem, txt, lignes[i].font,",
            "        lv_obj_t *l = texte(s_scr_dem, \"controle du bus I2C\", lignes[i].font,", 1)
    ui_c = M(19, ui_c, "if (dn_dem_err_vues() > 0 && s_dem_lbl_tact",
             "if (dn_dem_duree_ms() > 3000 && s_dem_lbl_tact")

    cles = cles_de_l_ecran(ui_c)
    dire(len(cles) >= 3,
         "l'ecran de demarrage tire ses lignes de la TABLE",
         "%d ligne(s) : %s" % (len(cles), ", ".join(c for c, _ in cles)))

    # Les traductions, RELUES de la X-macro.
    entrees = {}
    for m in re.finditer(r"X\((\w+),\s*((?:\\\s*\n\s*)?(?:\"(?:\\.|[^\"\\])*\"\s*)+),"
                         r"\s*((?:\\\s*\n\s*)?(?:\"(?:\\.|[^\"\\])*\"\s*)+)\)",
                         langue_h):
        entrees[m.group(1)] = (deplier_c(m.group(2)), deplier_c(m.group(3)))

    manquantes = [c for c, _ in cles if c not in entrees]
    vides = [c for c, _ in cles
             if c in entrees and (not entrees[c][0].strip()
                                  or not entrees[c][1].strip())]
    dire(not manquantes and not vides,
         "chaque ligne a ses DEUX traductions, et aucune n'est VIDE",
         "manquante(s) : %s · vide(s) : %s"
         % (manquantes or "aucune", vides or "aucune"))

    absents = []
    for cle, font in cles:
        if cle not in entrees or font not in polices:
            continue
        for lang, txt in zip(("EN", "FR"), entrees[cle]):
            # 🔴 `absents()` rend des CARACTERES, ⛔ PAS des codepoints — relu de
            #    `dn_police.py`. Un `%04X` dessus faisait PLANTER la gate au
            #    lieu de dire KO, et *une gate qui plante ne dit pas « KO »,
            #    elle dit « je n'ai pas tourne »*. Trouve par le mutant 16.
            for c in polices[font].absents(txt):
                absents.append("%s/%s U+%04X « %s »" % (cle, lang, ord(c), c))
    dire(not absents,
         "⛔ AUCUN glyphe absent des polices (il serait dessine EN BOITE)",
         "; ".join(absents) if absents else "cmaps confrontees, 2 langues")

    largeur_dalle = 480
    trop = []
    for cle, font in cles:
        if cle not in entrees or font not in polices:
            continue
        for lang, txt in zip(("EN", "FR"), entrees[cle]):
            w = polices[font].largeur(txt)
            if w > largeur_dalle:
                trop.append("%s/%s %d px" % (cle, lang, w))
    dire(not trop,
         "les largeurs tiennent sur la dalle dans les DEUX langues",
         "; ".join(trop) if trop
         else "max %d px pour %d de dalle"
              % (max([polices[f].largeur(t)
                      for c, f in cles if c in entrees and f in polices
                      for t in entrees[c]] or [0]), largeur_dalle))

    constr = re.search(r"static void demarrage_construire\(void\)\s*\{(.*?)\n\}",
                       sans_commentaires(ui_c), re.S)
    corps = constr.group(1) if constr else ""
    litteraux = [s for s in re.findall(r'"((?:\\.|[^"\\])*)"', corps)
                 if re.search(r"[A-Za-z]{4}", s)
                 and not re.fullmatch(r"[a-z ]+", s)]
    dire(not litteraux,
         "⛔ aucun libelle EN DUR dans l'ecran — tout passe par `dn_t()`",
         "vus : %s" % (litteraux if litteraux else "aucun"))

    tick = re.search(r"static void dem_tick\(lv_timer_t \*t\)\s*\{(.*?)\n\}",
                     sans_commentaires(ui_c), re.S)
    corps_t = tick.group(1) if tick else ""
    dire("dn_dem_err_vues() > 0" in corps_t,
         "le 2e temps est conditionne a une MESURE, ⛔ pas a un delai",
         "arbitrage owner du 2026-09-01")


# ══════════════════════════════════════════════════════════════════════════════
# 5. LE BUDGET EST GARDE PAR LE COMPILATEUR
# ══════════════════════════════════════════════════════════════════════════════

def section_budget(ui_c, dem_h):
    print("\n── 5. LE BUDGET EST GARDE PAR LE COMPILATEUR (AC2.2) ──────────")

    ui_c = M(20, ui_c, "#define DEM_Y_ETAT 250", "#define DEM_Y_ETAT 210")
    ui_c = M(22, ui_c, "    int lh = (int)lv_font_get_line_height(font);", "    int lh = 0;")
    dem_h = M(21, dem_h, "#define DN_DEM_LECTURES_MIN 20u",
              "#define DN_DEM_LECTURES_MIN 200u")
    dem_h = M(27, dem_h, "_Static_assert(DN_DEM_FENETRE_MS < DN_DEM_PLAFOND_MS,",
              "_Static_assert(1, \"\"); _Static_assert(1,")

    env = {"DN_LCD_V_RES": 640}
    for n in ("DEM_LH_28", "DEM_LH_18", "DEM_Y_TITRE", "DEM_Y_ETAT",
              "DEM_Y_CTRL", "DEM_Y_TACT", "DEM_Y_TACT_FIN"):
        env[n] = defini(ui_c, n, env)
    lu = [n for n in env if env[n] is None]
    empilement = [("DEM_Y_TITRE", "DEM_LH_28", "DEM_Y_ETAT"),
                  ("DEM_Y_ETAT", "DEM_LH_28", "DEM_Y_CTRL"),
                  ("DEM_Y_CTRL", "DEM_LH_18", "DEM_Y_TACT"),
                  ("DEM_Y_TACT", "DEM_LH_18", "DEM_Y_TACT_FIN")]
    chevauche = [a for a, h, b in empilement
                 if None not in (env[a], env[h], env[b])
                 and env[a] + env[h] > env[b]]
    bas = (env["DEM_Y_TACT_FIN"] + env["DEM_LH_18"]
           if None not in (env["DEM_Y_TACT_FIN"], env["DEM_LH_18"]) else None)
    dire(not lu and not chevauche and bas is not None and bas <= 640,
         "le budget VERTICAL est juste — l'addition est REFAITE ici",
         "illisible : %s · chevauchement(s) : %s · bas = %s <= 640"
         % (lu or "aucun", chevauche or "aucun", bas))

    asserts_ui = re.findall(r"_Static_assert\(\s*(DEM_Y_\w+[^,]*),", ui_c)
    dire(len(asserts_ui) >= len(empilement) + 1,
         "…et il est GARDE par `_Static_assert`, ⛔ pas par un commentaire",
         "%d assertion(s) sur la geometrie" % len(asserts_ui))

    cst = {}
    for n in ("DN_DEM_FENETRE_MS", "DN_DEM_LECTURES_MIN", "DN_DEM_PLAFOND_MS",
              "DN_DEM_LECTURES_PAR_S_PLANCHER"):
        cst[n] = defini(dem_h, n)
    asserts_h = re.findall(r"_Static_assert\(\s*(DN_DEM_\w+[^,]*),", dem_h)
    peuplable = (cst["DN_DEM_LECTURES_MIN"] is not None
                 and cst["DN_DEM_FENETRE_MS"] is not None
                 and cst["DN_DEM_LECTURES_MIN"] * 1000
                 <= cst["DN_DEM_FENETRE_MS"] * cst["DN_DEM_LECTURES_PAR_S_PLANCHER"])
    dire(peuplable and cst["DN_DEM_FENETRE_MS"] < cst["DN_DEM_PLAFOND_MS"]
         and len(asserts_h) >= 3,
         "le budget TEMPOREL est juste, et garde par `_Static_assert`",
         "fenetre %s ms porte %s lecture(s) au plancher mesure ; %d assertion(s)"
         % (cst["DN_DEM_FENETRE_MS"],
            (cst["DN_DEM_FENETRE_MS"] * cst["DN_DEM_LECTURES_PAR_S_PLANCHER"]
             // 1000) if cst["DN_DEM_FENETRE_MS"] else "?",
            len(asserts_h)))

    ctrl = re.search(r"static void dem_geometrie_controler\(.*?\n\}",
                     sans_commentaires(ui_c), re.S)
    corps = ctrl.group(0) if ctrl else ""
    dire("lv_font_get_line_height" in corps,
         "la hauteur de ligne budgetee est RELUE a la construction",
         "⛔ un chiffre ecrit se perime au premier changement de police")
    return cst


# ══════════════════════════════════════════════════════════════════════════════
# 6. LA CONSOLE ET LE DOSSIER LE DISENT
# ══════════════════════════════════════════════════════════════════════════════

def section_dossier(console, readme):
    print("\n── 6. LA CONSOLE ET LE DOSSIER LE DISENT (AC7) ────────────────")

    console = M(23, console, 'printf("  err I2C vues    : %" PRIu32 "\\n", dn_dem_err_vues());', "")
    readme = M(24, readme, "55,5", "cinquante-cinq virgule cinq")
    readme = M(25, readme, "L'ÉTAT DE DÉMARRAGE, ET LE DÉFAUT CONNU",
               "AUTRE CHOSE, SANS RAPPORT")

    lecteurs = ["dn_dem_verdict", "dn_dem_duree_ms", "dn_dem_err_vues",
                "dn_dem_fenetres_cassees", "dn_dem_lectures_vues",
                "dn_dem_rearmements_refuses", "dn_ui_demarrage_builds"]
    absents = [l for l in lecteurs if l not in console]
    dire(not absents,
         "la console PUBLIE tout ce que l'etat de demarrage sait",
         "⛔ un instrument qu'on ne peut pas LIRE ne disculpe personne · "
         "manquant(s) : %s" % (absents or "aucun"))

    # ⚠️ AC5.4 — ⛔ AUCUNE CLE DE STORY EN DUR ICI. Le controle porte sur les
    #    FAITS que la ligne doit citer, ⛔ pas sur le numero de celle qui l'a
    #    ecrite : un futur auteur qui deplacerait la ligne ne doit pas la voir
    #    rougir pour une raison de nommage.
    faits = {"le taux mesure": bool(re.search(r"55[,.]5\s*%", readme)),
             "la duree ~40 s": bool(re.search(r"~?\s*40\s*s", readme)),
             "l'auto-retablissement": bool(re.search(
                 r"auto[- ]r[ée]tabli|se r[ée]tablit (?:tout )?seul|recovers",
                 readme, re.I))}
    dire(all(faits.values()),
         "le Known-issues porte les 55,5 %, les ~40 s et l'auto-retablissement",
         "; ".join("%s : %s" % (k, "OK" if v else "⛔ ABSENT")
                   for k, v in faits.items()))

    dire(bool(re.search(r"ETAT DE DEMARRAGE|[ÉE]TAT DE D[ÉE]MARRAGE", readme)),
         "le README dit ce que l'etat de demarrage SIGNIFIE",
         "⛔ sinon l'inconnu le prendra pour une panne (AC7.2)")


def main():
    global _MUTANT
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--mutant", type=int, default=None,
                    help="casse UNE propriete EN MEMOIRE pour prouver que le "
                         "controle correspondant sait ROUGIR (AC5.3)")
    ap.add_argument("--liste-mutants", action="store_true",
                    help="dit ce que chaque mutant casse, et sort")
    args = ap.parse_args()
    _MUTANT = args.mutant

    if args.liste_mutants:
        for n in sorted(MUTANTS):
            print("  %2d  %s" % (n, MUTANTS[n]))
        return 0

    print("=" * 78)
    print("dn4-43 / AC5 — L'ETAT DE DEMARRAGE, ET SON CRITERE DE FIN"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)

    dem_c = lire(F_DEM_C)
    dem_h = lire(F_DEM_H)
    ui_c = lire(F_UI_C)
    ui_h = lire(F_UI_H)
    main_c = lire(F_MAIN_C)
    langue_h = lire(F_LANGUE_H)
    console = lire(F_CONSOLE)
    readme = lire(F_README)
    polices = dn_police.toutes()

    cst = section_budget(ui_c, dem_h)
    dem_c_mute = muter_module(dem_c)
    section_execution(dem_c_mute, dem_h, cst)
    section_critere(dem_c_mute, dem_h)
    section_boot(ui_c, main_c, ui_h)
    section_libelles(ui_c, langue_h, polices)
    section_dossier(console, readme)

    for d in _TMPDIRS:
        shutil.rmtree(d, ignore_errors=True)

    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (OK[0], KO[0]))
    print("=" * 78)
    return 1 if KO[0] else 0


if __name__ == "__main__":
    sys.exit(main())

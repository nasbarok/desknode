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

  1. LA DECISION S'EXECUTE — sur le module COMPILE et APPELE
  2. LE CRITERE N'EST PAS UN MINUTEUR — sur la source
  3. L'ETAT EST ATTEINT AU BOOT, ET NE SE RE-AFFICHE PAS
  4. LES LIBELLES : table, polices, largeurs, DEUX langues
  5. LE BUDGET EST GARDE PAR LE COMPILATEUR
  6. LA CONSOLE ET LE DOSSIER LE DISENT

⚠️ REVUE DU 2026-09-01 — ⛔ **PLUS AUCUN COMPTE DE CONTROLES ICI.** Ce bloc
   annoncait `12+3+7+5+3+3 = 33` quand le tir reel en rendait **38** : trois
   compteurs s'etaient perimes en silence. Un instrument qui ment sur sa propre
   couverture est precisement ce que `dn4-42` a paye. ⇒ le compte qui fait foi
   est celui du BILAN, ⛔ pas une addition ecrite.

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
# 🔴 REVUE DU 2026-09-01 — la geometrie de la dalle se RELIT ici, ⛔ elle ne
#    s'ecrit plus en dur dans la gate.
F_PINS_H = os.path.join(MAIN, "dn_pins.h")
# ⚠️ dn8-4 (2026-09-13) — REPOINTE. Ce chemin valait `README.md` a la racine.
#    Le journal francais que cette gate garde y est parti OCTET POUR OCTET
#    (13 liens rebases, preuve : `tools/scission_readme_dn84.py --verifier`) ;
#    la racine porte desormais une VITRINE anglaise, gardee par
#    `tools/verif_vitrine_dn84.py`. ⛔ Aucune ancre ni aucun mutant touche : la
#    gate garde le JOURNAL, ⛔ plus ce qu'un inconnu lit en premier.
F_README = os.path.join(RACINE, "docs", "journal-de-bord.md")

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

# ══════════════════════════════════════════════════════════════════════════════
# 🔴 MUTANTS 28..48 — AJOUTES PAR LA REVUE DE CODE DU 2026-09-01.
#
# ⛔ LE MOTIF EST MESURE, ⛔ PAS SUPPOSE. Le balayage a ete refait controle par
#    controle : la campagne d'origine annoncait « 27 declares, 27 appliques,
#    27 VUS ROUGIR » — **et c'etait vrai**. Mais AC5.3 demande l'INVERSE :
#    *« AU MOINS UN MUTANT PAR CONTROLE »*. L'union des `[KO ]` ne couvrait que
#    30 controles sur 38 : **8 etaient gardes par rien**, dont celui qui garde
#    les cinq `_Static_assert` de geometrie d'AC2.2.
# 🎯 La campagne prouvait `mutant ⇒ rouge` ; elle ne prouvait pas
#    `controle ⇒ couvert`. Les deux se lisent pareil dans un bilan.
# ══════════════════════════════════════════════════════════════════════════════
MUTANTS[28] = "renomme DN_LCD_V_RES : la gate ne sait plus lire la dalle"
MUTANTS[29] = "retire un `_Static_assert` de la geometrie de l'ecran"
MUTANTS[30] = "renomme le PLANCHER de cadence (la gate plantait au lieu de dire KO)"
MUTANTS[31] = "NEUTRALISE l'assertion du budget en lectures (elle ne mord plus)"
MUTANTS[32] = "rend le seuil de lectures INATTEIGNABLE (le boot sain n'aboutit plus)"
MUTANTS[33] = "cesse de COMPTER les erreurs vues (le 2e temps ne s'armerait plus)"
MUTANTS[34] = "passe la borne du vide de `>=` a `>` (l'off-by-one non garde)"
MUTANTS[35] = "laisse `dn_dem_conclure` poser une fin sur une machine NON ARMEE"
MUTANTS[36] = "laisse `dn_dem_conclure` accepter EN_COURS et les valeurs hors enum"
MUTANTS[37] = "rend `dn_dem_conclure` inoperante (la voie de `build_scene`)"
MUTANTS[38] = "retire l'idempotence : une fin posee peut etre defaite au tick suivant"
MUTANTS[39] = "fait ignorer le PARAMETRE `lectures` a la decision"
MUTANTS[40] = "🎯 RETIRE LE PLAFOND DE LA BRANCHE QUI RELANCE LA FENETRE — le defaut de la revue"
MUTANTS[41] = "arme l'observation APRES l'allumage du retroeclairage"
MUTANTS[42] = "ne SUPPRIME plus le timer a la conclusion (pointeur pendant)"
MUTANTS[43] = "retire la garde `if (!s_scr_dem)` en tete de `dem_tick`"
MUTANTS[44] = "cesse de controler le retour de `lv_timer_create`"
MUTANTS[45] = "retire une declaration de lecteur de `dn_ui.h`"
MUTANTS[46] = "vide la table `lignes[]` de l'ecran de demarrage"
MUTANTS[47] = "RE-OUVRE l'exemption des litteraux minuscules (le trou de la revue)"
MUTANTS[48] = "pose un libelle EN DUR dans `dem_tick` (hors du champ garde)"


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

def construire_module(src_c, src_h, etiquette, silencieux=False):
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
        # ⚠️ `silencieux` sert aux TEMOINS NEGATIFS : une compilation qu'on
        #    ATTEND en echec ⛔ ne doit pas cracher un mur d'erreurs dans un
        #    dossier de mesure — on veut juste savoir qu'elle a echoue.
        if not silencieux:
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


# Les verdicts et LEURS VALEURS. ⚠️ RELUS de l'en-tete, ⛔ pas recites.
def verdicts_de_l_entete(src_h):
    bloc = re.search(r"typedef enum \{(.*?)\} dn_dem_verdict_t;", src_h, re.S)
    if not bloc:
        return {}
    # 🔴 L'INITIALISEUR EST OBLIGATOIRE DANS LE MOTIF, ⛔ PAS OPTIONNEL A
    #    L'OEIL : la premiere entree s'ecrit `DN_DEM_EN_COURS = 0,` et un motif
    #    `(DN_DEM_[A-Z_]+),` la MANQUAIT — la liste rendue commencait alors a
    #    `FIN_PROPRE`, tous les indices etaient DECALES DE UN, et CINQ controles
    #    d'execution rougissaient sur du code JUSTE. Trouve en jouant la gate au
    #    premier tir, ⛔ pas en la relisant.
    # 🔴 REVUE DU 2026-09-01 — **L'INITIALISEUR EST DESORMAIS HONORE, ⛔ PLUS
    #    CAPTURE PUIS JETE.** Le motif acceptait `= \d+` mais l'appelant
    #    numerotait par POSITION : un futur `DN_DEM_FIN_X = 7,` ou une
    #    renumerotation aurait fait diverger SILENCIEUSEMENT les constantes de
    #    la gate des valeurs C, et les controles d'execution auraient compare au
    #    mauvais verdict. C'est le decalage-de-un qui a deja coute CINQ
    #    controles rouges (voir ci-dessus), ré-ouvert par l'autre bout.
    out, suivant = {}, 0
    for nom, val in re.findall(r"^\s*(DN_DEM_[A-Z_]+)\s*(?:=\s*(\d+)\s*)?,",
                               sans_commentaires(bloc.group(1)), re.M):
        suivant = int(val) if val else suivant
        out[nom] = suivant
        suivant += 1
    return out


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
    src_c = M(32, src_c, "s_lectures_vues >= DN_DEM_LECTURES_MIN",
              "s_lectures_vues >= 100000u")
    src_c = M(33, src_c, "s_err_vues += err_i2c - s_fen_err0;", "(void)0;")
    src_c = M(34, src_c, "s_lectures_vues >= DN_DEM_LECTURES_MIN",
              "s_lectures_vues > DN_DEM_LECTURES_MIN")
    src_c = M(35, src_c, "    if (!s_arme || s_verdict != DN_DEM_EN_COURS) {\n        return;\n    }",
              "    if (s_verdict != DN_DEM_EN_COURS) {\n        return;\n    }")
    src_c = M(36, src_c,
              "    if (v <= DN_DEM_EN_COURS || v > DN_DEM_FIN_RECONSTRUCTION) {\n        return;\n    }\n",
              "")
    src_c = M(37, src_c, "    conclure(t_ms, v);\n}", "    (void)t_ms;\n    (void)v;\n}")
    src_c = M(38, src_c,
              "    if (s_verdict != DN_DEM_EN_COURS) {\n        return s_verdict; /* idempotente : une fin est définitive */\n    }\n",
              "")
    # 🔴 Mutant 39 : trois sites, un seul numero — la decision cesse d'utiliser
    #    le PARAMETRE `lectures` sans cesser de compiler.
    src_c = M(39, src_c, "lectures < s_fen_lect0", "0u < s_fen_lect0")
    src_c = M(39, src_c, "        s_fen_lect0 = lectures;", "        s_fen_lect0 = 0u;")
    src_c = M(39, src_c, "s_lectures_vues = lectures - s_fen_lect0;",
              "s_lectures_vues = DN_DEM_LECTURES_MIN;")
    # 🎯 Mutant 40 : LE DEFAUT QUE LA REVUE A TROUVE, REPLANTE TEL QUEL.
    src_c = M(40, src_c,
              "        if ((uint32_t)(t_ms - s_t0_ms) >= DN_DEM_PLAFOND_MS) {\n"
              "            conclure(t_ms, DN_DEM_FIN_PLAFOND);\n"
              "            return s_verdict;\n"
              "        }\n        return DN_DEM_EN_COURS;",
              "        return DN_DEM_EN_COURS;")
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

    V = verdicts_de_l_entete(src_h)
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

    # ══════════════════════════════════════════════════════════════════════════
    # 🔴 LE BUS QUI NE SE RETABLIT **JAMAIS** — LE CONTROLE QUI MANQUAIT, ET
    #    C'EST LUI QUI A LAISSE PASSER LE DEFAUT LE PLUS LOURD DE LA STORY.
    #
    # ⛔ AVANT LA REVUE DU 2026-09-01, LE PLAFOND N'ETAIT EPROUVE QUE SUR DES
    #    COMPTEURS **FIGES** (le piege du vide, plus bas, `d_err = 0`). Le seul
    #    scenario a erreurs continues s'arretait a 40 s — SOUS les 90 s du
    #    plafond — et AFFIRMAIT `EN COURS` comme attendu. Autrement dit : la
    #    gate ENTERINAIT le comportement qui devenait le blocage.
    #
    # 🔴 CE QUE LA MESURE A RENDU (module compile et pilote, avant correctif) :
    #    a une erreur nouvelle par tick, `verdict = EN COURS` encore a 150 s,
    #    puis a 500 s, puis a 1 000 000 ms — plafond declare a 90 s. Le retour
    #    anticipe de la casse de fenetre sautait le test du plafond, qui etait
    #    donc INJOIGNABLE **exactement dans le cas ou il sert**. Sur une carte
    #    dont le GT911 rate durablement, l'ecran de demarrage ne partait JAMAIS.
    #
    # ⚠️ 500 ticks x 250 ms = 125 s, soit bien au-dela du plafond : si le filet
    #    existe, il DOIT tomber ici.
    # ══════════════════════════════════════════════════════════════════════════
    n_apres_plafond = int(plaf // 250) + 40
    v, duree, _ = jouer(lib, [(n_apres_plafond, 3, 6)])
    dire(v == plafond,
         "bus qui ne se retablit JAMAIS : le plafond TOMBE quand meme",
         "%d s d'erreurs continues, verdict=%s — ⛔ un EN COURS ici veut dire "
         "que l'ecran de demarrage ne part JAMAIS (AC1.2 : « en plus », ⛔ pas "
         "« a la place »)"
         % (n_apres_plafond * 250 // 1000, lib.dn_dem_verdict_nom(v).decode()))
    dire(v == plafond and duree >= plaf and duree <= plaf + 500,
         "…et il tombe A L'HEURE, ⛔ pas quand le bus veut bien se taire",
         "%d ms pour un plafond de %d ms" % (duree, plaf))
    dire(lib.dn_dem_lectures_vues() == 0,
         "…et la fenetre finale n'avait RIEN observe (temoin du vide)",
         "%d lecture(s) — ⛔ une valeur PERIMEE ici sur-declarerait ce que la "
         "fenetre courante a vu" % lib.dn_dem_lectures_vues())

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

    # ══════════════════════════════════════════════════════════════════════════
    # 🔴 LA BORNE EXACTE DU GARDE-FOU DU VIDE — `lmin - 1` CONTRE `lmin`.
    #
    # ⛔ AVANT LA REVUE DU 2026-09-01, CE CONTROLE NE JOUAIT QUE `d_lect = 0` :
    #    un etat rigoureusement identique au « piege du vide » teste juste
    #    au-dessus. La borne n'etait donc **jamais exercee**, et c'est MESURE :
    #    remplacer `>= DN_DEM_LECTURES_MIN` par `> DN_DEM_LECTURES_MIN` laissait
    #    la gate a `38 OK, 0 KO`, rc 0. Le seuil que ce controle pretendait
    #    garder n'etait garde par rien.
    # ⚠️ Un seul tick de `fen` ms suffit : la fenetre est alors ECOULEE, et
    #    c'est le COMPTE de lectures — lui seul — qui decide.
    # ══════════════════════════════════════════════════════════════════════════
    v, _, _ = jouer(lib, [(1, 0, lmin - 1)], pas=int(fen))
    dire(v != propre,
         "borne du vide : %d lecture(s) dans la fenetre ⇒ ⛔ ne conclut PAS"
         % (lmin - 1),
         "verdict=%s" % lib.dn_dem_verdict_nom(v).decode())

    v, _, _ = jouer(lib, [(1, 0, lmin)], pas=int(fen))
    dire(v == propre,
         "…et a %d, elle conclut — la borne est en `>=`, ⛔ pas en `>`" % lmin,
         "verdict=%s ⇒ un off-by-one ici couterait UNE lecture de marge sur "
         "TOUTES les cartes" % lib.dn_dem_verdict_nom(v).decode())

    # ── Une fenetre a ZERO lecture ne conclut pas non plus (le vide pur). ──
    v, _, _ = jouer(lib, [(400, 0, 0)], pas=int(fen))
    dire(v != propre,
         "fenetre a ZERO lecture ⇒ ⛔ ne conclut pas",
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

    # ══════════════════════════════════════════════════════════════════════════
    # 🔴 `dn_dem_conclure()` — LA VOIE EXTERNE, ET ELLE N'ETAIT EPROUVEE PAR
    #    AUCUN SCENARIO.
    #
    # ⛔ Sa signature ctypes etait declaree ; la fonction n'etait JAMAIS appelee.
    #    Or c'est **la seule voie qu'utilisent reellement `build_scene()` et
    #    `nav_appliquer()`**. Le mutant 13 verifiait seulement que la LIGNE
    #    existait dans `dn_ui.c`, ⛔ jamais ce qu'elle FAIT.
    # ══════════════════════════════════════════════════════════════════════════
    recons = V.get("DN_DEM_FIN_RECONSTRUCTION", 4)
    lib.dn_dem_reset_pour_gate()
    lib.dn_dem_armer(1000, True, 0, 30)
    lib.dn_dem_tick(1250, 0, 36)
    lib.dn_dem_conclure(1500, recons)
    dire(lib.dn_dem_verdict() == recons and not lib.dn_dem_en_cours(),
         "`dn_dem_conclure(RECONSTRUCTION)` POSE bien la fin",
         "verdict=%s, duree=%d ms"
         % (lib.dn_dem_verdict_nom(lib.dn_dem_verdict()).decode(),
            lib.dn_dem_duree_ms()))

    lib.dn_dem_tick(9999, 0, 999)
    dire(lib.dn_dem_verdict() == recons,
         "…et une fin est DEFINITIVE : le tick d'apres ne la defait pas",
         "verdict=%s"
         % lib.dn_dem_verdict_nom(lib.dn_dem_verdict()).decode())

    lib.dn_dem_reset_pour_gate()
    lib.dn_dem_conclure(1000, propre)
    dire(lib.dn_dem_verdict() == en_cours,
         "`dn_dem_conclure()` sur une machine NON ARMEE ne pose RIEN",
         "⛔ sinon un `build_scene()` avant l'armement inventerait un verdict")

    # 🔴 REVUE DU 2026-09-01 — **UNE FIN QUI N'EN EST PAS UNE EST REFUSEE.**
    #    `dn_dem_conclure()` acceptait `DN_DEM_EN_COURS` et les valeurs hors
    #    enum sans un mot : la machine se serait « conclue » sur le verdict
    #    *pas encore fini*, ou sur un code que `dn_dem_verdict_nom()` rend « ? ». Deux
    #    etiquettes de mesure FAUSSES.
    lib.dn_dem_reset_pour_gate()
    lib.dn_dem_armer(1000, True, 0, 30)
    lib.dn_dem_conclure(1500, en_cours)
    ok_en_cours = lib.dn_dem_en_cours()
    lib.dn_dem_conclure(1500, 99)
    dire(ok_en_cours and lib.dn_dem_en_cours(),
         "…et elle REFUSE `EN_COURS` et les valeurs hors enum",
         "⛔ « conclure » sur EN_COURS ou sur 99 rendrait une etiquette FAUSSE")

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
    # ⚠️ REVUE DU 2026-09-01 — **CE CONTROLE ETAIT QUASI-VACUEL.** Il cherchait
    #    la sous-chaine « lectures », que `s_lectures_vues` contient TOUJOURS :
    #    il ne pouvait donc pas rougir, meme si la decision cessait d'utiliser
    #    le PARAMETRE. Les bornes de mot le rendent testable — et le mutant 31
    #    le prouve.
    n_err = len(re.findall(r"\berr_i2c\b", corps))
    n_lect = len(re.findall(r"\blectures\b", corps))
    dire(bool(corps) and n_err > 0 and n_lect > 0,
         "`dn_dem_tick` LIT les DEUX compteurs, ⛔ pas seulement l'horloge",
         "parametre err_i2c %d fois, parametre lectures %d fois" % (n_err, n_lect))

    # ══════════════════════════════════════════════════════════════════════════
    # 🔴 REVUE DU 2026-09-01 — **CE CONTROLE A EPINGLE UN CORRECTIF JUSTE**, et
    #    c'est ecrit ici plutot que tu.
    #
    # ⛔ Il comparait la PREMIERE occurrence de chaque verdict dans le corps.
    #    Le correctif du plafond injoignable a ajoute une evaluation du plafond
    #    **dans la branche qui casse la fenetre**, donc plus HAUT que le
    #    critere — et la gate a rougi sur du code devenu JUSTE.
    #    (`dn4-24` a deja paye exactement ca : *« une gate N OK / 0 KO peut
    #    epingler du code FAUX »* — ici c'est la symetrie.)
    #
    # ✅ CE QUI EST VRAIMENT LA PROPRIETE : sur le chemin NOMINAL — celui qu'on
    #    atteint quand la fenetre n'a PAS ete cassee — le critere RELU est teste
    #    avant le plafond. On compare donc le critere a la **DERNIERE**
    #    occurrence du plafond, qui est celle du chemin nominal.
    # ══════════════════════════════════════════════════════════════════════════
    i_propre = corps.find("DN_DEM_FIN_PROPRE")
    i_plafond_nominal = corps.rfind("DN_DEM_FIN_PLAFOND")
    dire(0 <= i_propre < i_plafond_nominal,
         "chemin NOMINAL : le critere RELU est teste **AVANT** le plafond",
         "PROPRE en %d, PLAFOND nominal en %d" % (i_propre, i_plafond_nominal))

    # 🔴 ET LE FILET DOIT ETRE ARME SUR **LES DEUX** CHEMINS. C'est le defaut
    #    trouve en revue : la branche qui relance la fenetre rendait la main
    #    AVANT le test du plafond, qui devenait donc injoignable des que le bus
    #    produisait une erreur nouvelle a chaque tick — c'est-a-dire exactement
    #    le regime pour lequel le plafond a ete ecrit.
    casse = re.search(r"s_fen_cassees\+\+;(.*?)return DN_DEM_EN_COURS;",
                      corps, re.S)
    dire(bool(casse) and "DN_DEM_PLAFOND_MS" in casse.group(1),
         "…et la branche qui RELANCE la fenetre evalue le plafond AUSSI",
         "⛔ sinon un bus qui rate a chaque tick ne conclut JAMAIS (mesure : "
         "EN COURS encore a 1 000 000 ms)")

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
    main_c = M(41, main_c, "    dn_ui_demarrage_armer(tactile_present);", "")
    if _MUTANT == 41:
        main_c = main_c.replace(
            "    ESP_ERROR_CHECK(dn_display_backlight_pct(bl_boot));",
            "    ESP_ERROR_CHECK(dn_display_backlight_pct(bl_boot));\n"
            "    dn_ui_demarrage_armer(tactile_present);", 1)
    ui_c = M(42, ui_c, "        lv_timer_delete(s_dem_timer);", "")
    ui_c = M(43, ui_c,
             "static void dem_tick(lv_timer_t *t)\n{\n    (void)t;\n    if (!s_scr_dem) {\n        return;\n    }",
             "static void dem_tick(lv_timer_t *t)\n{\n    (void)t;")
    ui_c = M(44, ui_c, "    if (!s_dem_timer) {", "    if (false) {")
    ui_h = M(45, ui_h, "bool dn_ui_demarrage_a_l_ecran(void);", "")

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

    # ══════════════════════════════════════════════════════════════════════════
    # 🔴 REVUE DU 2026-09-01 — **LA DUREE DE VIE DU TIMER N'ETAIT CONTROLEE PAR
    #    RIEN**, alors que c'est la moitie du danger que cette gate documente.
    #    Le commentaire de `build_scene()` annonce *« le timer `dem_tick`
    #    ecrirait dedans 250 ms plus tard, sur un pointeur PENDANT »* — et un
    #    mutant supprimant `lv_timer_delete(s_dem_timer)` laissait la gate
    #    VERTE.
    # ══════════════════════════════════════════════════════════════════════════
    concl = re.search(r"static void demarrage_conclure_nolock\(.*?\n\}",
                      nu_ui, re.S)
    corps_concl = concl.group(0) if concl else ""
    dire("lv_timer_delete(s_dem_timer)" in corps_concl
         and "s_dem_timer = NULL" in corps_concl,
         "la conclusion SUPPRIME le timer, et oublie son pointeur",
         "⛔ sinon `dem_tick` s'executerait sur un ecran DETRUIT")

    tick_nu = re.search(r"static void dem_tick\(lv_timer_t \*t\)\s*\{(.{0,200})",
                        nu_ui, re.S)
    dire(bool(tick_nu) and "if (!s_scr_dem)" in tick_nu.group(1),
         "…et `dem_tick` SORT si l'ecran n'existe plus (garde en tete)",
         "⛔ la seule barriere si un tick reste en vol")

    creation = re.search(
        r"s_dem_timer = lv_timer_create\([^;]*;(.{0,400})", nu_ui, re.S)
    dire(bool(creation) and "if (!s_dem_timer)" in creation.group(1),
         "…et le RETOUR de `lv_timer_create` est CONTROLE",
         "⛔ sans timer, l'etat de demarrage ne peut ni conclure ni se mesurer "
         "— il resterait sur la dalle sans un mot")

    # ⚠️ `ui_h` est enfin UTILISE : il etait passe a cette section et jamais lu.
    getters = ["dn_ui_demarrage_armer", "dn_ui_demarrage_builds",
               "dn_ui_demarrage_trop_larges", "dn_ui_demarrage_a_l_ecran"]
    non_declares = [g for g in getters if g not in ui_h]
    dire(not non_declares,
         "les lecteurs de l'etat de demarrage sont DECLARES dans `dn_ui.h`",
         "⛔ un instrument qu'aucun en-tete ne publie n'est lisible par "
         "personne · manquant(s) : %s" % (non_declares or "aucun"))

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
    if _MUTANT == 46:
        for _mort in ("DN_T_DEM_TITRE, &dn_font_28, 0xa0d8ff, DEM_Y_TITRE, "
                      "DEM_LH_28,\n         \"titre\", NULL},",
                      "DN_T_DEM_EN_COURS, &dn_font_28, 0xffffff, DEM_Y_ETAT, "
                      "DEM_LH_28,\n         \"etat\", NULL},",
                      "DN_T_DEM_CONTROLE, &dn_font_18, 0xc0d8e8, DEM_Y_CTRL, "
                      "DEM_LH_18,\n         \"controle\", NULL},"):
            if "{" + _mort not in ui_c:
                sys.exit("MUTANT 46 INAPPLICABLE : %r introuvable." % _mort[:40])
            ui_c = ui_c.replace("{" + _mort, "", 1)
    ui_c = M(48, ui_c, "    dn_touch_stats_t st;\n    dn_touch_get_stats(&st);\n    uint32_t t_ms = (uint32_t)(esp_timer_get_time() / 1000);\n    dn_dem_verdict_t v = dn_dem_tick",
             "    lv_label_set_text(s_dem_lbl_tact, \"veuillez patienter\");\n    dn_touch_stats_t st;\n    dn_touch_get_stats(&st);\n    uint32_t t_ms = (uint32_t)(esp_timer_get_time() / 1000);\n    dn_dem_verdict_t v = dn_dem_tick")

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
    # ══════════════════════════════════════════════════════════════════════════
    # 🔴 REVUE DU 2026-09-01 — **LE TROU ETAIT TAILLE SUR LE MUTANT QUI LE
    #    TESTAIT.**
    #
    # ⛔ Le filtre disait `not re.fullmatch(r"[a-z ]+", s)` : il EXEMPTAIT donc
    #    **tout litteral ASCII entierement en minuscules**. MESURE : injecter
    #    `"veuillez patienter"` — la formule qu'AC3.4 interdit NOMMEMENT — dans
    #    `demarrage_construire()` rendait `[OK ] … vus : aucun`, `38 OK, 0 KO`,
    #    rc 0. Passaient aussi les traductions EN reelles (`starting up`,
    #    `touch is not responding yet`). Le mutant 18 ne rougissait que parce
    #    qu'il contenait `I2C` **en majuscules** : il prouvait qu'on attrapait
    #    *ce* mutant, ⛔ pas la classe annoncee.
    #
    # ✅ L'EXEMPTION EST DESORMAIS **NOMMEE ET FERMEE** : seuls les libelles du
    #    champ `quoi` du tableau `lignes[]` — qui ne sont PAS affiches, ils
    #    nomment la ligne pour le journal de geometrie — sont tolerés, et ils
    #    sont RELUS du tableau lui-meme.
    # ══════════════════════════════════════════════════════════════════════════
    bloc_lignes = re.search(r"\} lignes\[\] = \{(.*?)\n    \};", corps, re.S)
    quoi_attendus = set(re.findall(r'"([a-z ]+)",\s*(?:&?s_dem_\w+|NULL)\}',
                                   bloc_lignes.group(1))) if bloc_lignes else set()

    # 🔴 Mutant 47 : re-plante l'exemption qui laissait passer « veuillez
    #    patienter » — la faute est le motif TROP LARGE, ⛔ pas son absence.
    _trou_47 = (_MUTANT == 47)

    def _en_dur(src, quoi_ok):
        # ⚠️ LE JOURNAL N'EST PAS LA DALLE. `ESP_LOGx()` porte legitimement de
        #    la prose francaise : la regle d'AC3.1 vise ce qui est AFFICHE, ⛔
        #    pas ce qui est trace. On retire donc les appels de journal AVANT de
        #    chercher — ⛔ et on ne retire rien d'autre, pour que la garde reste
        #    fermee sur tout le reste.
        src = re.sub(r"ESP_LOG[A-Z]\s*\([^;]*?\);", " ", src, flags=re.S)
        return [x for x in re.findall(r'"((?:\\.|[^"\\])*)"', src)
                if re.search(r"[A-Za-z]{4}", x) and x not in quoi_ok
                and not (_trou_47 and re.fullmatch(r"[a-z ]+", x))]

    litteraux = _en_dur(corps, quoi_attendus)
    dire(not litteraux,
         "⛔ aucun libelle EN DUR dans l'ecran — tout passe par `dn_t()`",
         "exemptes (champ `quoi`, ⛔ non affiche) : %s · vus : %s"
         % (sorted(quoi_attendus) or "aucun", litteraux or "aucun"))

    # 🔴 LE TEMOIN NEGATIF DE CETTE EXEMPTION. ⛔ Sans lui, on ne saurait pas si
    #    le filtre attrape encore quoi que ce soit — un motif trop large se lit
    #    VERT exactement comme un fichier propre.
    appat = 'lv_label_set_text(l, "veuillez patienter");'
    dire(bool(_en_dur(corps + "\n" + appat, quoi_attendus)),
         "…et le filtre ATTRAPE encore un litteral minuscule (temoin negatif)",
         "appat « veuillez patienter » — ⛔ la formule qu'AC3.4 interdit "
         "nommement passait VERTE avant la revue du 2026-09-01")

    tick = re.search(r"static void dem_tick\(lv_timer_t \*t\)\s*\{(.*?)\n\}",
                     sans_commentaires(ui_c), re.S)
    corps_t = tick.group(1) if tick else ""

    # 🔴 ET LA GARDE COUVRE AUSSI `dem_tick()` — c'est LA que le 2e temps est
    #    revele. Le controle etait scope a `demarrage_construire()` SEULE : un
    #    libelle pose ici y echappait entierement (motif « gate scopee a UNE
    #    fonction qui epingle vert le meme defaut ailleurs »).
    litteraux_t = _en_dur(corps_t, set())
    dire(not litteraux_t,
         "⛔ …ni dans `dem_tick()`, ou le 2e temps est REVELE",
         "vus : %s" % (litteraux_t or "aucun"))
    dire("dn_dem_err_vues() > 0" in corps_t,
         "le 2e temps est conditionne a une MESURE, ⛔ pas a un delai",
         "arbitrage owner du 2026-09-01")


# ══════════════════════════════════════════════════════════════════════════════
# 5. LE BUDGET EST GARDE PAR LE COMPILATEUR
# ══════════════════════════════════════════════════════════════════════════════

def section_budget(ui_c, dem_h, dem_c):
    print("\n── 5. LE BUDGET EST GARDE PAR LE COMPILATEUR (AC2.2) ──────────")

    ui_c = M(20, ui_c, "#define DEM_Y_ETAT 250", "#define DEM_Y_ETAT 210")
    ui_c = M(29, ui_c,
             '_Static_assert(DEM_Y_CTRL + DEM_LH_18 <= DEM_Y_TACT,\n'
             '               "dn4-43 : la ligne de controle mord sur le second temps.");',
             "")
    dem_h = M(30, dem_h, "#define DN_DEM_LECTURES_PAR_S_PLANCHER 20u",
              "#define DN_DEM_LECT_PAR_S 20u")
    # ⚠️ Mutant 31 : ici la FAUTE **EST** la neutralisation — la classe de defaut
    #    visee par le temoin negatif est justement « une assertion qui ne mord
    #    plus ». ⛔ Ce n'est pas un mutant qui debranche une garde au hasard.
    dem_h = M(31, dem_h, "_Static_assert(DN_DEM_LECTURES_MIN * 1000u",
              "_Static_assert(1 || DN_DEM_LECTURES_MIN * 1000u")
    ui_c = M(22, ui_c, "    int lh = (int)lv_font_get_line_height(font);", "    int lh = 0;")
    dem_h = M(21, dem_h, "#define DN_DEM_LECTURES_MIN 20u",
              "#define DN_DEM_LECTURES_MIN 200u")
    dem_h = M(27, dem_h, "_Static_assert(DN_DEM_FENETRE_MS < DN_DEM_PLAFOND_MS,",
              "_Static_assert(1, \"\"); _Static_assert(1,")

    # 🔴 REVUE DU 2026-09-01 — **LA GEOMETRIE DE DALLE EST RELUE, ⛔ PLUS
    #    ECRITE EN DUR.** `640` etait un litteral ici alors que le
    #    `_Static_assert` qu'on pretend « refaire » utilise `DN_LCD_V_RES` : un
    #    changement de dalle ou de rotation aurait laisse ce controle VERT sur
    #    une addition devenue fausse.
    display_h = M(28, lire(F_PINS_H), "#define DN_LCD_V_RES 640",
                  "#define DN_LCD_VERT_RES 640")
    v_res = defini(display_h, "DN_LCD_V_RES")
    h_res = defini(display_h, "DN_LCD_H_RES")
    dire(v_res is not None and h_res is not None,
         "la geometrie de la dalle est RELUE de son en-tete",
         "DN_LCD_H_RES=%s, DN_LCD_V_RES=%s ⛔ pas des litteraux"
         % (h_res, v_res))
    env = {"DN_LCD_V_RES": v_res}
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
    dire(not lu and not chevauche and bas is not None and v_res is not None
         and bas <= v_res,
         "le budget VERTICAL est juste — l'addition est REFAITE ici",
         "illisible : %s · chevauchement(s) : %s · bas = %s <= %s"
         % (lu or "aucun", chevauche or "aucun", bas, v_res))

    asserts_ui = re.findall(r"_Static_assert\(\s*(DEM_Y_\w+[^,]*),", ui_c)
    dire(len(asserts_ui) >= len(empilement) + 1,
         "…et il est GARDE par `_Static_assert`, ⛔ pas par un commentaire",
         "%d assertion(s) sur la geometrie" % len(asserts_ui))

    cst = {}
    for n in ("DN_DEM_FENETRE_MS", "DN_DEM_LECTURES_MIN", "DN_DEM_PLAFOND_MS",
              "DN_DEM_LECTURES_PAR_S_PLANCHER"):
        cst[n] = defini(dem_h, n)

    # ══════════════════════════════════════════════════════════════════════════
    # 🔴 REVUE DU 2026-09-01 — **UNE CONSTANTE ILLISIBLE DIT « KO », ⛔ ELLE NE
    #    FAIT PLUS PLANTER LA GATE.**
    #    MESURE : renommer `DN_DEM_LECTURES_PAR_S_PLANCHER` donnait
    #    `TypeError: unsupported operand type(s) for *: 'int' and 'NoneType'`,
    #    un traceback, et **aucune ligne BILAN**. C'est litteralement le mode
    #    d'echec que le docstring de cette gate s'interdit — et le 4e defaut de
    #    gate deja consigne au Debug Log de la story, revenu par un autre bout.
    # ══════════════════════════════════════════════════════════════════════════
    illisibles = [n for n in cst if cst[n] is None]
    dire(not illisibles,
         "le budget TEMPOREL est LISIBLE — ⛔ une gate qui plante ne dit rien",
         "illisible(s) : %s" % (illisibles or "aucune"))

    asserts_h = re.findall(r"_Static_assert\(\s*(DN_DEM_\w+[^,]*),", dem_h)
    if illisibles:
        dire(False,
             "le budget TEMPOREL est juste, et garde par `_Static_assert`",
             "⛔ NON EVALUE : %s illisible(s)" % illisibles)
    else:
        peuplable = (cst["DN_DEM_LECTURES_MIN"] * 1000
                     <= cst["DN_DEM_FENETRE_MS"]
                     * cst["DN_DEM_LECTURES_PAR_S_PLANCHER"])
        dire(peuplable and cst["DN_DEM_FENETRE_MS"] < cst["DN_DEM_PLAFOND_MS"]
             and len(asserts_h) >= 3,
             "le budget TEMPOREL est juste, et garde par `_Static_assert`",
             "fenetre %s ms porte %s lecture(s) au plancher mesure ; "
             "%d assertion(s)"
             % (cst["DN_DEM_FENETRE_MS"],
                cst["DN_DEM_FENETRE_MS"]
                * cst["DN_DEM_LECTURES_PAR_S_PLANCHER"] // 1000,
                len(asserts_h)))

    # ══════════════════════════════════════════════════════════════════════════
    # 🔴 REVUE DU 2026-09-01 — **« GARDE PAR LE COMPILATEUR » EST DESORMAIS
    #    PROUVE PAR LE COMPILATEUR.**
    #
    # ⛔ Cette section REFAISAIT l'arithmetique en Python et COMPTAIT les
    #    `_Static_assert`. Elle ne montrait jamais qu'ils MORDENT. Pire, le
    #    mutant 21 (`DN_DEM_LECTURES_MIN` a 200u) mutait une variable LOCALE :
    #    `main()` passait ensuite le `dem_h` D'ORIGINE au compilateur mais le
    #    `cst` MUTE — si bien que la section d'execution ANNONCAIT
    #    « fenetre a MOINS de 200 lecture(s) » sur un `.so` compile avec 20.
    #    C'est l'image miroir exacte du defaut de gate n° 2 du Debug Log.
    #
    # ✅ Deux tirs, et ils se repondent :
    #    · l'en-tete du depot (ou du mutant) DOIT compiler ⇒ le mutant 21 fait
    #      desormais rougir ICI, en atteignant vraiment `cc` ;
    #    · un en-tete deliberement hors budget DOIT ECHOUER ⇒ **temoin
    #      negatif** : sans lui, une assertion neutralisee se lirait verte
    #      exactement comme une assertion qui mord.
    # ══════════════════════════════════════════════════════════════════════════
    dire(construire_module(dem_c, dem_h, "en-tete tel qu'il est") is not None,
         "l'en-tete du depot COMPILE — les `_Static_assert` passent",
         "⛔ un budget hors clous casserait la compilation, ⛔ pas un test")

    lmin_lu = re.search(r"^#define\s+DN_DEM_LECTURES_MIN\s+.*$", dem_h, re.M)
    if lmin_lu:
        dem_h_faux = dem_h.replace(lmin_lu.group(0),
                                   "#define DN_DEM_LECTURES_MIN 100000u", 1)
        dire(construire_module(dem_c, dem_h_faux, "temoin negatif",
                               silencieux=True) is None,
             "…et un budget HORS CLOUS fait ECHOUER `cc` (temoin negatif)",
             "⛔ sans ce tir, une assertion neutralisee se lirait VERTE")
    else:
        dire(False, "…et un budget HORS CLOUS fait ECHOUER `cc` (temoin negatif)",
             "⛔ NON EVALUE : `DN_DEM_LECTURES_MIN` illisible")

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

    # ⚠️ REVUE DU 2026-09-01 — **CETTE ANCRE ETAIT MORTE.** `cmd_dem` est passe
    #    a un INSTANTANE pris sous verrou : le `printf` ne lit plus le getter,
    #    il lit une variable. Le mutant sortait donc en « INAPPLICABLE » — et
    #    c'est la garde de `M()` qui l'a dit, ⛔ pas une relecture.
    console = M(23, console, "uint32_t v_err = dn_dem_err_vues();",
                "uint32_t v_err = 0;")
    readme = M(24, readme, "55,5", "cinquante-cinq virgule cinq")
    readme = M(25, readme, "L'ÉTAT DE DÉMARRAGE, ET LE DÉFAUT CONNU",
               "AUTRE CHOSE, SANS RAPPORT")

    lecteurs = ["dn_dem_verdict", "dn_dem_duree_ms", "dn_dem_err_vues",
                "dn_dem_fenetres_cassees", "dn_dem_lectures_vues",
                "dn_dem_rearmements_refuses", "dn_ui_demarrage_builds",
                # ⚠️ REVUE DU 2026-09-01 — il etait PUBLIE par `cmd_dem` et
                #    absent de cette liste : le controle « la console publie
                #    tout » ne le gardait donc pas.
                "dn_ui_demarrage_trop_larges"]
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

    cst = section_budget(ui_c, dem_h, dem_c)
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

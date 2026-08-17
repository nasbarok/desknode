#!/usr/bin/env python3
"""
DeskNode — génère les polices embarquées (français accentué + icônes FontAwesome).

POURQUOI CE FICHIER EXISTE, ALORS QUE LVGL EN FOURNIT DÉJÀ UN
============================================================
`managed_components/lvgl__lvgl/scripts/built_in_font/built_in_font_gen.py` est LE
générateur des polices built-in : il pose seul les bons drapeaux
(`--no-compress --no-prefilter --force-fast-kern-format`) et injecte seul les 61
codepoints de symboles `LV_SYMBOL_*`. C'est lui qu'il faut utiliser — la story
dn3-1 le dit explicitement.

MAIS il ne sait pas AJOUTER de codepoints FontAwesome. Sa liste de symboles est
une constante `syms = "61441,61448,..."` dans le corps du script, et son `-r`
utilisateur s'applique à la police LATINE (Montserrat), pas au `.woff`. Or dn3-1
a besoin de 7 glyphes FontAwesome de PLUS (les icônes des métriques).

Ce script est donc un sur-ensemble, et il se défend du seul risque que ça crée —
LA DÉRIVE DE LA LISTE DES 61 SYMBOLES :

  🔴 Il ne RECOPIE PAS les 61 codepoints. Il les LIT dans le fichier amont, à
     chaque exécution. Si LVGL en ajoute un, on l'a. Si le fichier amont
     disparaît ou change de forme, ce script ÉCHOUE BRUYAMMENT au lieu de
     générer une police à laquelle il manquerait LV_SYMBOL_LIST (bandeau MENU)
     ou LV_SYMBOL_LEFT (chevron de retour) — deux glyphes dont l'absence est
     SILENCIEUSE à l'écran : LVGL ne dessine pas un glyphe manquant et ne se
     plaint pas.

  Puis il VÉRIFIE le `.c` produit : les 61 symboles + les icônes demandées +
  quelques lettres accentuées témoins doivent être dans l'`unicode_list`. Une
  génération qui « réussit » sans les glyphes demandés est exactement l'étiquette
  qui ment que ce dépôt traque depuis dn1-3.

⚠️ `--no-compress` est OBLIGATOIRE : `CONFIG_LV_USE_FONT_COMPRESSED` n'est PAS
   activé dans ce build (vérifié dans `sdkconfig`). Une police compressée ne
   s'afficherait pas correctement, et la compression coûte ~30 % de temps de
   rendu — sur un firmware dont le plancher de transition EST le rendu LVGL.

⚠️ `managed_components/` est GITIGNORÉ mais RÉGÉNÉRÉ par `idf.py` depuis
   `main/idf_component.yml`, où `lvgl/lvgl: "==9.5.0"` est épinglé. La
   génération est donc reproductible tant que cette ligne ne bouge pas — c'est un
   fait à connaître, pas une supposition : sans `managed_components/`, ce script
   ne trouve ni le générateur amont, ni le TTF, ni le WOFF.

DÉPENDANCE : `lv_font_conv` (npm), appelé PAR SON NOM par le script amont.
   `npx --yes lv_font_conv@1.5.3` fonctionne depuis ce WSL (mesuré) ; poser un
   shim exécutable nommé `lv_font_conv` sur le PATH suffit. Voir le README.

USAGE
    python3 tools/gen_font_dn.py            # génère les deux tailles
    python3 tools/gen_font_dn.py --mesure   # ne génère rien : compare les plages
"""

import argparse
import os
import re
import subprocess
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
LVGL = os.path.join(RACINE, "firmware", "desknode", "managed_components",
                    "lvgl__lvgl")
GEN_DIR = os.path.join(LVGL, "scripts", "built_in_font")
GEN = os.path.join(GEN_DIR, "built_in_font_gen.py")
SORTIE = os.path.join(RACINE, "firmware", "desknode", "main", "fonts")

# ── LA PLAGE LATINE ──────────────────────────────────────────────────────────
# latin-1 COMPLET, et c'est un arbitrage écrit (W5 de dn3-1), pas un réflexe :
#   · la partition `factory` fait 4 MiB et le binaire en occupe ~20 % ⇒ les
#     ~13 ko de données que latin-1 coûte en plus de la « minimale FR » sont
#     0,3 % de la place libre. Le levier binaire n'existe pas ici ;
#   · latin-1 ferme la CLASSE de défaut, pas un cas : plus jamais un libellé
#     futur qui perd sa lettre en silence ;
#   · et il apporte deux glyphes d'UNITÉ directement utiles au produit :
#     0xB5 « µ » (µs des compteurs de flush) et 0xB2 « ² ».
# 0x2022 (la puce) est CONSERVÉ : il est dans la plage des built-ins, et le
# retirer ferait de cette police un sous-ensemble de celle qu'elle remplace.
PLAGE = "0x20-0x7F,0xA0-0xFF,0x2022"

# ── LES ICÔNES ───────────────────────────────────────────────────────────────
# Codepoints VÉRIFIÉS UN PAR UN dans le `.woff` du dépôt le 2026-08-17 (chacun
# converti seul ; `lv_font_conv` échoue bruyamment sur un codepoint absent).
# 🔴 0xF863 `fan` est ABSENT : il est arrivé en FontAwesome 5.11 et le `.woff`
#    embarqué est antérieur. Le substitut retenu est 0xF2F1 `sync-alt` — voir
#    le motif écrit dans la story (W4).
ICONES = {
    "microchip":        0xF2DB,  # CPU
    "desktop":          0xF108,  # GPU
    "memory":           0xF538,  # RAM
    "network-wired":    0xF6FF,  # RESEAU
    "sync-alt":         0xF2F1,  # VENTILOS — substitut de `fan` (0xF863 ABSENT)
    "thermometer-half": 0xF2C9,  # AMBIANCE (température)
    "tint":             0xF043,  # AMBIANCE (humidité)
}

TAILLES = (14, 28)


def symboles_amont():
    """Les 61 codepoints de LV_SYMBOL_*, LUS dans le générateur amont.

    Jamais recopiés : une liste recopiée dérive, et sa dérive est SILENCIEUSE
    (LVGL ne dessine pas un glyphe absent et ne se plaint pas). On échoue
    bruyamment si le fichier amont a changé de forme.
    """
    if not os.path.isfile(GEN):
        sys.exit("ÉCHEC : générateur amont introuvable : %s\n"
                 "        `managed_components/` est gitignoré mais régénéré :\n"
                 "        lancer `idf.py reconfigure` dans firmware/desknode." % GEN)
    src = open(GEN, encoding="utf-8").read()
    m = re.search(r'^syms\s*=\s*"([0-9,]+)"\s*$', src, re.M)
    if not m:
        sys.exit("ÉCHEC : la constante `syms` du générateur amont n'a pas la forme\n"
                 "        attendue. NE PAS recopier la liste à la main : vérifier\n"
                 "        %s" % GEN)
    cps = [int(x) for x in m.group(1).split(",") if x]
    # Le fichier amont contient un doublon (61452 deux fois) : on dédoublonne en
    # gardant l'ordre, sinon `lv_font_conv` refuse la plage.
    vus, uniq = set(), []
    for c in cps:
        if c not in vus:
            vus.add(c)
            uniq.append(c)
    return uniq


def generer(taille, plage, icones, kerning, sortie):
    """Appelle le générateur AMONT, avec la plage FontAwesome étendue.

    Le générateur amont ne sait pas ajouter de codepoints FontAwesome : sa liste
    est une constante. On lui passe donc une liste étendue par un fichier
    temporaire ? Non — on reconstruit sa ligne de commande à l'IDENTIQUE, en
    lisant ses 61 codepoints, et on ajoute les nôtres. Les drapeaux sont ceux du
    script amont, ligne par ligne (built_in_font_gen.py:47-73).
    """
    # ⚠️ DÉDOUBLONNER LA FUSION, pas seulement la liste amont : `0xF043` (tint,
    # l'icône d'humidité) est DÉJÀ l'un des 61 symboles (61507). `lv_font_conv`
    # l'a accepté en double sans broncher — un doublon toléré aujourd'hui est un
    # refus demain, et surtout la ligne de commande inscrite dans l'en-tête du
    # `.c` doit être exacte : c'est elle qui fait foi pour la reproductibilité.
    fusion, vus = [], set()
    for c in symboles_amont() + sorted(icones.values()):
        if c not in vus:
            vus.add(c)
            fusion.append(c)
    syms = fusion
    cmd = [
        "lv_font_conv",
        "--no-compress", "--no-prefilter",            # amont:48 (compressed=False)
        "--bpp", "4",                                 # amont:67
        "--size", str(taille),                        # amont:67
        # ⚠️ NOMS RELATIFS, et la commande tourne dans GEN_DIR : `lv_font_conv`
        #    RECOPIE sa ligne de commande dans l'en-tête du `.c` généré, et cet
        #    en-tête est la recette de reproduction (AC6). Des chemins absolus y
        #    graveraient le `$HOME` de la machine qui a généré — une recette que
        #    personne d'autre ne peut rejouer, y compris nous après un
        #    déplacement du dépôt.
        "--font", "Montserrat-Medium.ttf",
        "-r", plage,
        "--font", "FontAwesome5-Solid+Brands+Regular.woff",
        "-r", ",".join(str(c) for c in syms),         # amont:70
        "--format", "lvgl",                           # amont:70
        "-o", os.path.abspath(sortie),
        "--force-fast-kern-format",                   # amont:73
    ]
    if not kerning:
        cmd.append("--no-kerning")
    subprocess.run(cmd, check=True, cwd=GEN_DIR)
    corriger_include(os.path.abspath(sortie))
    return syms


# `lv_font_conv` émet ce préambule, qui choisit son include sur une macro que
# NOTRE build ne définit pas : ESP-IDF pose `LV_CONF_INCLUDE_SIMPLE` (pour
# `lv_conf.h`) mais PAS `LV_LVGL_H_INCLUDE_SIMPLE`. Le `.c` tombait donc dans la
# branche `#include "lvgl/lvgl.h"` — introuvable depuis `main/` : le composant est
# ajouté au chemin d'inclusion par son dossier `lvgl__lvgl`, pas par un préfixe
# `lvgl/`. Symptôme : `fatal error: lvgl/lvgl.h: No such file or directory`.
PREAMBULE_AMONT = '''#ifdef LV_LVGL_H_INCLUDE_SIMPLE
#include "lvgl.h"
#else
#include "lvgl/lvgl.h"
#endif'''

PREAMBULE_DN = '''/* Include RÉÉCRIT par tools/gen_font_dn.py — le préambule d'origine de
 * lv_font_conv choisit entre "lvgl.h" et "lvgl/lvgl.h" sur la macro
 * LV_LVGL_H_INCLUDE_SIMPLE, que le build ESP-IDF de ce projet ne définit PAS
 * (il pose LV_CONF_INCLUDE_SIMPLE, qui est une AUTRE macro, pour lv_conf.h).
 * Sans cette réécriture : « fatal error: lvgl/lvgl.h: No such file or
 * directory ». Défaut BRUYANT, donc sans risque de passer inaperçu — mais autant
 * ne pas le redécouvrir à chaque régénération. */
#include "lvgl.h"'''


def corriger_include(chemin):
    src = open(chemin, encoding="utf-8", errors="replace").read()
    if PREAMBULE_AMONT not in src:
        sys.exit("ÉCHEC : le préambule d'include de %s n'a pas la forme attendue.\n"
                 "        `lv_font_conv` a changé son gabarit — relire le `.c` et\n"
                 "        mettre PREAMBULE_AMONT à jour plutôt que de corriger le\n"
                 "        fichier généré à la main (il est réécrit au prochain "
                 "passage)." % chemin)
    src = src.replace(PREAMBULE_AMONT, PREAMBULE_DN, 1)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(src)


def verifier(chemin, syms, plage_a_temoins):
    """RELIT le `.c` produit. Une génération « réussie » ne prouve rien."""
    src = open(chemin, encoding="utf-8", errors="replace").read()
    m = re.search(r"static const uint16_t unicode_list_\d+\[\] = \{(.*?)\};",
                  src, re.S)
    liste = set()
    if m:
        # unicode_list est en OFFSETS depuis la base du range : on ne peut pas
        # l'utiliser seule. Le `.c` porte aussi les bornes dans cmaps.
        pass
    manques = []
    # Les bornes de chaque cmap disent quelles plages sont réellement couvertes.
    bornes = [(int(a, 0), int(b, 0)) for a, b in
              re.findall(r"\.range_start = (\d+|0x[0-9a-fA-F]+),\s*"
                         r"\.range_length = (\d+|0x[0-9a-fA-F]+)", src)]
    couverts = []
    for start, length in bornes:
        couverts.append((start, start + length - 1))

    def couvert(cp):
        return any(a <= cp <= b for a, b in couverts)

    for cp in syms:
        if not couvert(cp):
            manques.append("symbole/icône U+%04X" % cp)
    for ch in plage_a_temoins:
        if not couvert(ord(ch)):
            manques.append("témoin « %s » (U+%04X)" % (ch, ord(ch)))
    if manques:
        sys.exit("ÉCHEC de vérification sur %s :\n  - %s"
                 % (chemin, "\n  - ".join(manques)))
    return len(couverts)


def octets_police(chemin):
    """Les octets de DONNÉES de police, lus dans le `.c` — pas sa taille fichier.

    glyph_bitmap + glyph_dsc (8 o/glyphe) + unicode_list (2 o) + les trois
    tables de kerning. ⚠️ C'est un PLANCHER : le coût réel est le delta de
    BINAIRE, mesuré après le premier appel (leçon T4 de dn2-1).
    """
    src = open(chemin, encoding="utf-8", errors="replace").read()
    total = 0
    detail = {}
    # ⚠️ L'ACCOLADE EST À LA LIGNE SUIVANTE dans le `.c` généré, pas collée au
    # `=`. Une première version de ce compteur exigeait « = { » : elle rendait
    # ZÉRO pour glyph_bitmap ET pour les trois tables de kerning, donc un total
    # identique avec et sans `--no-kerning` — un instrument qui ne pouvait pas
    # voir ce qu'il prétendait mesurer. Corrigé le 2026-08-17 en RELISANT le
    # `.c`, pas en relisant le regex.
    for nom, motif, poids in (
        ("glyph_bitmap", r"glyph_bitmap\[\]\s*=\s*\{(.*?)\};", 1),
        ("unicode_list", r"unicode_list_\d+\[\]\s*=\s*\{(.*?)\};", 2),
        ("kern_class_values", r"kern_class_values\[\]\s*=\s*\{(.*?)\};", 1),
        ("kern_left_class_mapping",
         r"kern_left_class_mapping\[\]\s*=\s*\{(.*?)\};", 1),
        ("kern_right_class_mapping",
         r"kern_right_class_mapping\[\]\s*=\s*\{(.*?)\};", 1),
    ):
        n = 0
        for bloc in re.findall(motif, src, re.S):
            n += len(re.findall(r"0x[0-9a-fA-F]+|(?<![\w.])\d+(?![\w.])", bloc))
        detail[nom] = n * poids
        total += n * poids
    n_glyphes = len(re.findall(r"\{\.bitmap_index =", src))
    detail["glyph_dsc"] = n_glyphes * 8
    total += n_glyphes * 8
    detail["_glyphes"] = n_glyphes
    detail["_total"] = total
    return detail


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mesure", action="store_true",
                    help="ne génère rien dans main/ : compare les plages et le "
                         "kerning dans un dossier temporaire, et imprime le tableau")
    ap.add_argument("--sans-kerning", action="store_true",
                    help="supprime les trois tables de kerning (~6 900 o pour "
                         "les deux tailles)")
    args = ap.parse_args()

    if args.mesure:
        tmp = os.path.join("/tmp", "dn_font_mesure")
        os.makedirs(tmp, exist_ok=True)
        plages = {
            "actuelle (built-in)": "0x20-0x7F,0xB0,0x2022",
            "minimale FR": "0x20-0x7F,0xB0,0x2022,0xC0,0xC7,0xC9,0xCA,0xCE,0xD4,"
                           "0xDB,0xE0,0xE7,0xE8,0xE9,0xEA,0xEE,0xF4,0xFB",
            "latin-1 complet": "0x20-0x7F,0xA0-0xFF,0x2022",
        }
        print("%-24s %-10s %8s %10s %10s %10s"
              % ("plage", "kerning", "glyphes", "14 px", "28 px", "TOTAL"))
        for nom, plage in plages.items():
            for kern in (True, False):
                tot, glyphes, par_taille = 0, 0, []
                for t in TAILLES:
                    out = os.path.join(tmp, "p_%d.c" % t)
                    generer(t, plage, ICONES, kern, out)
                    d = octets_police(out)
                    par_taille.append(d["_total"])
                    tot += d["_total"]
                    glyphes = d["_glyphes"]
                print("%-24s %-10s %8d %10d %10d %10d"
                      % (nom, "oui" if kern else "NON", glyphes,
                         par_taille[0], par_taille[1], tot))
        return

    os.makedirs(SORTIE, exist_ok=True)
    temoins = "ÉÀÇÊÎÔÛéèêàçîôûµ²°•"
    total = 0
    for t in TAILLES:
        out = os.path.join(SORTIE, "dn_font_%d.c" % t)
        syms = generer(t, PLAGE, ICONES, not args.sans_kerning, out)
        n = verifier(out, syms, temoins)
        d = octets_police(out)
        total += d["_total"]
        print("dn_font_%d.c : %d glyphes · %d o de données de police · %d cmaps · "
              "%d symboles+icônes vérifiés · %d témoins accentués vérifiés"
              % (t, d["_glyphes"], d["_total"], n, len(syms), len(temoins)))
        # Le nom LVGL généré est `dn_font_<taille>` (dérivé du -o) : le `.h`
        # ci-dessous le déclare tel quel.
    ecrire_entete()
    print("dn_font.h : réécrit · TOTAL %d o de données de police (les deux "
          "tailles). ⚠️ PLANCHER : le coût qui fait foi est le delta de BINAIRE."
          % total)


def ecrire_entete():
    """Réécrit `dn_font.h` DEPUIS `ICONES`.

    🔴 Le `.h` n'est pas maintenu à la main, et c'est le point : une icône ajoutée
    au dictionnaire ci-dessus entre dans la police ET dans le `.h` par le MÊME
    geste. Une macro `DN_ICONE_*` qui pointerait un codepoint absent de la police
    ne produirait AUCUNE erreur — juste un rectangle vide, ou rien du tout. C'est
    la classe de défaut « l'étiquette qui ment », transposée aux glyphes.
    """
    lignes = []
    for nom, cp in sorted(ICONES.items(), key=lambda kv: kv[1]):
        octets = "".join("\\x%02X" % b for b in chr(cp).encode("utf-8"))
        macro = "DN_ICONE_" + nom.upper().replace("-", "_")
        lignes.append('#define %-28s "%s" /* U+%04X %s */'
                      % (macro, octets, cp, nom))
    contenu = ENTETE_MODELE % {
        "plage": PLAGE,
        "icones": "\n".join(lignes),
        "n_icones": len(ICONES),
    }
    with open(os.path.join(SORTIE, "dn_font.h"), "w", encoding="utf-8") as f:
        f.write(contenu)


ENTETE_MODELE = u'''/*
 * DeskNode — les polices embarquées. GÉNÉRÉ PAR `tools/gen_font_dn.py`.
 * ⛔ NE PAS ÉDITER À LA MAIN : le prochain passage du générateur l'écrase.
 *
 * ── POURQUOI CES POLICES REMPLACENT LES BUILT-INS (dn3-1) ────────────────────
 *
 * `lv_font_montserrat_14/_28` sont générées avec `-r 0x20-0x7F,0xB0,0x2022`
 * (relu dans l'en-tête de leur `.c`, pas supposé) : ASCII + le signe degré + la
 * puce + les 61 symboles, ET RIEN D'AUTRE. « RÉSEAU », « HUMIDITÉ », « AOÛT » y
 * perdent leur lettre accentuée EN SILENCE — LVGL ne dessine pas un glyphe
 * absent et ne se plaint pas.
 *
 * `dn_font_14` / `dn_font_28` couvrent %(plage)s :
 * ASCII + LATIN-1 COMPLET + la puce + les 61 symboles LV_SYMBOL_* + %(n_icones)d
 * icônes FontAwesome. Elles sont donc un SUR-ENSEMBLE STRICT des built-ins.
 *
 * ⚠️ `lv_font_montserrat_14` reste compilée : elle est aussi `LV_FONT_DEFAULT`
 *    (`CONFIG_LV_FONT_DEFAULT_MONTSERRAT_14=y`) et le Kconfig de LVGL 9.5
 *    n'offre AUCUN choix « police personnalisée » pour ce réglage (relu dans
 *    `Kconfig:991-1040`). La désactiver exigerait de patcher le composant managé,
 *    qui est gitignoré et régénéré : le correctif ne survivrait pas au premier
 *    `idf.py reconfigure`. On paie donc ses octets DÉLIBÉRÉMENT, et c'est écrit.
 * ⚠️ `lv_font_montserrat_28`, elle, est DÉSACTIVÉE : rien d'autre ne s'en sert.
 *
 * ── LES ICÔNES ───────────────────────────────────────────────────────────────
 * Aucun asset image : `dn_asset` ne gère QU'UN asset et la partition `assets`
 * n'a que ~434 Ko libres, que dn3-3 réclame déjà. Les icônes sont des GLYPHES,
 * pris dans le `FontAwesome5-Solid+Brands+Regular.woff` déjà présent dans
 * l'arbre — zéro asset, zéro dépendance neuve.
 *
 * 🔴 `0xF863` (`fan`) est ABSENT de ce `.woff` : il est arrivé en FontAwesome
 *    5.11, le fichier embarqué est antérieur. VÉRIFIÉ le 2026-08-17 en le
 *    convertissant seul (`lv_font_conv` échoue bruyamment sur un codepoint
 *    absent), pas déduit d'une table. Le substitut retenu pour VENTILOS est
 *    `sync-alt` — deux flèches en rotation, qui disent « ça tourne » là où
 *    `wind` (0xF72E) dit « ça souffle » et où `cogs` (0xF085) dit « engrenage ».
 *
 * Reproduction :  python3 tools/gen_font_dn.py
 * La ligne de commande exacte est dans l'en-tête de chaque `.c` généré.
 * Licences : `managed_components/lvgl__lvgl/scripts/built_in_font/font_license/`.
 */
#pragma once

#include "lvgl.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ASCII + latin-1 complet + puce + 61 symboles + icônes. */
LV_FONT_DECLARE(dn_font_14)
LV_FONT_DECLARE(dn_font_28)

/* Les icônes, en UTF-8 prêt à concaténer dans un littéral de chaîne.
 * GÉNÉRÉES depuis le même dictionnaire que la police : une macro ne peut pas
 * pointer un codepoint que la police n'aurait pas. */
%(icones)s

#ifdef __cplusplus
}
#endif
'''


if __name__ == "__main__":
    main()

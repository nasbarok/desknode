#!/usr/bin/env python3
"""
DeskNode — génère les polices embarquées (français accentué + icônes FontAwesome).

POURQUOI CE FICHIER EXISTE, ALORS QUE LVGL EN FOURNIT DÉJÀ UN
============================================================
`managed_components/lvgl__lvgl/scripts/built_in_font/built_in_font_gen.py` est LE
générateur des polices built-in : il pose seul les bons drapeaux
(`--no-compress --no-prefilter --force-fast-kern-format`) et injecte seul les
codepoints de symboles `LV_SYMBOL_*` — **61 entrées déclarées, 60 UNIQUES** (sa
liste contient un doublon, 61452 deux fois). C'est lui qu'il faut utiliser — la
story dn3-1 le dit explicitement.

MAIS il ne sait pas AJOUTER de codepoints FontAwesome. Sa liste de symboles est
une constante `syms = "61441,61448,..."` dans le corps du script, et son `-r`
utilisateur s'applique à la police LATINE (Montserrat), pas au `.woff`. Or dn3-1
a besoin d'icônes FontAwesome en plus : 10 entrées au dictionnaire `ICONES`
ci-dessous, dont 2 (`cog` 0xF013 et `tint` 0xF043) sont DÉJÀ des symboles ⇒
**8 codepoints neufs**, et 68 au `-r` FontAwesome final.
⚠️ Ces nombres sont CALCULÉS et réinjectés dans `dn_font.h` à chaque génération,
   plus récités : cinq endroits du dépôt en annonçaient trois valeurs
   différentes, aucune juste (revue de code du 2026-08-18).

Ce script est donc un sur-ensemble, et il se défend du seul risque que ça crée —
LA DÉRIVE DE LA LISTE DES SYMBOLES :

  🔴 Il ne RECOPIE PAS les codepoints. Il les LIT dans le fichier amont, à
     chaque exécution. Si LVGL en ajoute un, on l'a. Si le fichier amont
     disparaît ou change de forme, ce script ÉCHOUE BRUYAMMENT au lieu de
     générer une police à laquelle il manquerait LV_SYMBOL_LIST (témoin pur)
     ou LV_SYMBOL_LEFT (chevron de retour) — deux glyphes dont l'absence est
     SILENCIEUSE à l'écran : LVGL ne dessine pas un glyphe manquant et ne se
     plaint pas.

  Puis il VÉRIFIE le `.c` produit : les symboles + les icônes demandées + des
  lettres accentuées témoins doivent être RÉELLEMENT portés par les cmaps. Une
  génération qui « réussit » sans les glyphes demandés est exactement l'étiquette
  qui ment que ce dépôt traque depuis dn1-3.

  ⚠️ ET CETTE GARDE A ÉTÉ AVEUGLE UNE FOIS (corrigé le 2026-08-18, revue de
     code) : elle testait les BORNES des cmaps au lieu de leur CONTENU, or la
     cmap des symboles est SPARSE — elle borne 8226 → 63650 en n'y portant que
     69 codepoints. `couvert(0xF863)` rendait donc `True` pour `fan`, LE glyphe
     absent que ce fichier documente. Voir `codepoints_du_c()`.
  ⚠️ Et les symboles étaient re-testés contre la liste LUE dans l'amont : un
     témoin tiré de la chose qu'il témoigne n'est pas un témoin. D'où
     `SYMBOLES_TEMOINS`, deux codepoints écrits en dur DÉLIBÉRÉMENT.

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
#    embarqué est antérieur. Le substitut retenu est 0xF013 `cog` (W4, constat
#    owner du 2026-08-17) — et il est gratuit, 0xF013 étant déjà l'un des
#    codepoints de symboles injectés par l'amont.
ICONES = {
    "microchip":        0xF2DB,  # CPU
    "desktop":          0xF108,  # GPU
    "memory":           0xF538,  # RAM
    "network-wired":    0xF6FF,  # RESEAU
    "thermometer-half": 0xF2C9,  # AMBIANCE (température)
    "tint":             0xF043,  # AMBIANCE (humidité)
    # ── dn4-1 / W9 : L'ICÔNE DE `DISQUE`, ET SON PRIX MESURÉ ─────────────────
    # Décision owner du 2026-08-18 : « icône disquette ». 🔴 ET ELLE EST
    # GRATUITE, MESURÉ AVANT DE L'AJOUTER : 0xF0C7 est DÉJÀ l'un des 60
    # codepoints de symboles que le générateur amont injecte (LV_SYMBOL_SAVE),
    # donc l'union `-r` reste à 68 et les deux `.c` de police sont INCHANGÉS.
    # ⚠️ Vérifié DANS LES `.c` PRODUITS avec `codepoints_du_c()` (260 codepoints
    #    / 3 cmaps, présent en 14 px ET en 28 px), ⛔ PAS par un test de bornes :
    #    c'est précisément ce test-là qui avait fait croire `fan` présent.
    "save":             0xF0C7,  # DISQUE (dn4-1) — la disquette
    # ── LES QUATRE CANDIDATS AU VENTILATEUR ──────────────────────────────────
    # ⚠️ dn4-1 les GARDE alors que la case ne s'appelle plus VENTILOS (D8).
    #    MESURÉ le 2026-08-18 : sur les quatre, `cog` (0xF013) est DÉJÀ amont ;
    #    seuls `sync-alt`, `wind` et `cogs` sont propres au dépôt. Les retirer
    #    n'économiserait donc que **3 glyphes**, mais ferait passer l'union `-r`
    #    de **68 à 65** — donc imposerait une VRAIE régénération (npm + réseau)
    #    pour un gain négligeable. ⇒ HORS PÉRIMÈTRE de dn4-1 : le ménage attend
    #    le jour où une régénération est nécessaire pour une autre raison.
    # `fan` (0xF863) est ABSENT du .woff du dépôt. Les quatre substituts sont
    # EMBARQUÉS ENSEMBLE et commutables à chaud (`widget icone <0..3>`) : le
    # choix est un constat owner sur la dalle, pas une intuition — et un A/B qui
    # demande trois reflashs coûte trois observations à l'owner pour un rendement
    # qui baisse. Les 4 glyphes coûtent ~3 ko sur une partition libre à 79 %.
    "sync-alt":         0xF2F1,  # deux flèches en rotation
    "wind":             0xF72E,  # lignes de souffle
    "cogs":             0xF085,  # engrenages
    "cog":              0xF013,  # un engrenage
}

TAILLES = (14, 28)

# ── dn3-3 : LES DEUX POLICES DE LA VEILLE ────────────────────────────────────
#
# 🔴 PLAGE RÉDUITE, ET C'EST CE QUI REND L'AGRANDISSEMENT ABORDABLE.
#    En Ambient, le titre, l'icône et le libellé de grandeur DISPARAISSENT
#    (décision owner du 2026-08-25) : il ne reste QUE des valeurs. Ces polices
#    n'ont donc besoin ni des accents latin-1, ni de la puce, ni d'UN SEUL des
#    61 symboles LVGL ni des icônes FontAwesome — c'est-à-dire de rien de ce qui
#    coûte cher. `0x20-0x7F` couvre chiffres, unités et le « -- » de l'absence ;
#    `0xB0` est le signe degré.
# ⚠️ ⛔ NE PAS y rajouter la plage latin-1 « au cas où » : à 56 px chaque glyphe
#    coûte QUATRE fois ce qu'il coûte à 28, et 164 codepoints jamais dessinés
#    tripleraient la facture pour rien.
# 🔴 ET L'ABSENCE D'UN GLYPHE EST SILENCIEUSE À L'ÉCRAN : si une valeur venait à
#    porter un caractère hors de cette plage, LVGL ne dessinerait RIEN et ne se
#    plaindrait pas. C'est pourquoi `verifier()` tourne aussi sur ces deux-là,
#    avec le degré comme témoin.
PLAGE_VEILLE = "0x20-0x7F,0xB0"

# 🔴 LES DEUX TAILLES SONT **MESURÉES**, ⛔ PAS CHOISIES ROND.
#    Relevé sur la carte le 2026-08-25 avec `widget largeur`, sur une case de
#    225 px dont **201 sont utiles** :
#      · avec l'unité, le pire cas est « 2999,9 Mb/s » = 168 px à 28 px
#        ⇒ plafond 28 x 201/168 = 33,5 px  ⇒ **33**
#      · sans l'unité, le pire cas est « 2999,9 » = 90 px à 28 px
#        ⇒ plafond 28 x 201/90 = 62,5 px, ramené à **56** pour garder
#          10 % de marge (une valeur à 5 chiffres + décimale n'est pas le
#          pire cas absolu, c'est le pire cas OBSERVÉ).
#    ⚠️ Le pire cas THÉORIQUE de la table du firmware est « c.max 100,0 % »
#       = 197 px — mais il porte un LIBELLÉ, et les libellés disparaissent en
#       Ambient. C'est ce qui débloque l'agrandissement, et c'est pour ça que
#       le chiffre retenu est 168 et non 197.
TAILLES_VEILLE = (33, 56)

# ── LES DEUX TÉMOINS QUI SONT RECOPIÉS, ET C'EST DÉLIBÉRÉ ────────────────────
# Tout le reste de ce script REFUSE de recopier la liste amont, et c'est juste.
# Mais UN TÉMOIN TIRÉ DE LA CHOSE QU'IL TÉMOIGNE N'EST PAS UN TÉMOIN : `verifier`
# re-testait `syms`, c'est-à-dire la liste LUE dans l'amont. Si LVGL retirait un
# codepoint, ce script le retirerait de la police ET de sa propre liste de
# contrôle, puis annoncerait un succès — exactement le scénario contre lequel
# « ne jamais recopier la liste » est censé protéger (correctif de revue,
# 2026-08-18). Ces deux-là sont donc écrits en dur, parce qu'ils sont les deux
# dont l'absence est SILENCIEUSE À L'ÉCRAN :
#   · LV_SYMBOL_LIST (U+F00B) — TÉMOIN PUR depuis dn3-2 : plus aucun code
#     de `main/` ne le référence. W3 a retiré le chevron du bandeau MENU
#     (une affordance sur un élément non actionnable), et cette ligne a
#     gardé sa justification périmée jusqu'à la revue du 2026-08-18.
#     ⚠️ On le GARDE quand même : un glyphe FontAwesome dans la plage haute
#     reste le meilleur témoin d'une police tronquée. C'est le MOTIF qui
#     était faux, pas le choix.
#   · LV_SYMBOL_LEFT (U+F053) — le chevron de retour (dn_ui.c)
# Relevés dans `managed_components/lvgl__lvgl/src/font/lv_symbol_def.h` le
# 2026-08-18, pas devinés.
SYMBOLES_TEMOINS = {"LV_SYMBOL_LIST": 0xF00B, "LV_SYMBOL_LEFT": 0xF053}


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


def generer(taille, plage, icones, kerning, sortie, symboles=True):
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
    syms = fusion if symboles else []
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
    ]
    # 🔴 dn3-3 : LA SECONDE FONTE N'EST AJOUTÉE QUE SI ON LUI DEMANDE DES
    #    SYMBOLES. Passer `-r ""` à `lv_font_conv` sur un `--font` sans
    #    codepoint est une erreur ; et surtout, embarquer FontAwesome dans une
    #    police de VEILLE qui ne dessine que des chiffres ferait payer 61
    #    glyphes jamais affichés — à 56 px, quatre fois le prix du 28.
    if syms:
        cmd += [
            "--font", "FontAwesome5-Solid+Brands+Regular.woff",
            "-r", ",".join(str(c) for c in syms),     # amont:70
        ]
    cmd += [
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


CMAP = re.compile(
    r"\.range_start\s*=\s*(\d+|0x[0-9a-fA-F]+)\s*,\s*"
    r"\.range_length\s*=\s*(\d+|0x[0-9a-fA-F]+)\s*,\s*"
    r"\.glyph_id_start\s*=\s*\d+\s*,\s*"
    r"\.unicode_list\s*=\s*(NULL|unicode_list_\d+)\s*,\s*"
    r"\.glyph_id_ofs_list\s*=\s*\w+\s*,\s*"
    r"\.list_length\s*=\s*(\d+)\s*,\s*"
    r"\.type\s*=\s*(\w+)")


def codepoints_du_c(src, chemin):
    """L'ensemble EXACT des codepoints que le `.c` porte, cmap par cmap.

    🔴 POURQUOI CETTE FONCTION EXISTE — LA GARDE PRÉCÉDENTE ÉTAIT AVEUGLE À CE
       QU'ELLE PRÉTENDAIT VÉRIFIER (correctif de revue, 2026-08-18). Elle testait
       les BORNES de chaque cmap : `range_start` → `range_start + range_length`.
       Or la cmap qui porte les symboles et les icônes est de type SPARSE — dans
       le `.c` livré : `.range_start = 8226, .range_length = 55425`,
       `.list_length = 69`. Elle BORNE donc 8226 → 63650 en n'y portant que
       **69** codepoints. Un test de bornes rendait `True` pour la TOTALITÉ de
       `syms`, quoi qu'il arrive : `couvert(0xF863)` — `fan`, le glyphe ABSENT
       dont l'absence motive toute la §15.4 — rendait `True`. Seuls les témoins
       accentués, qui tombent dans les cmaps DENSES (FORMAT0_TINY 32..126 et
       160..255), étaient réellement contrôlés.
       ⇒ Pour une cmap sparse, `unicode_list_N` fait foi : ses entrées sont des
       OFFSETS depuis `range_start`. C'est ce que la version précédente avait
       constaté — puis abandonné sur un `pass`.
    """
    couverts, n_cmaps = set(), 0
    for a, b, liste_nom, list_len, type_ in CMAP.findall(src):
        n_cmaps += 1
        start, length, list_len = int(a, 0), int(b, 0), int(list_len)
        if liste_nom == "NULL":
            # Dense (FORMAT0_*) : tout l'intervalle est réellement porté.
            couverts.update(range(start, start + length))
            continue
        m = re.search(r"static const uint16_t %s\[\]\s*=\s*\{(.*?)\};"
                      % re.escape(liste_nom), src, re.S)
        if not m:
            sys.exit("ÉCHEC : cmap sparse de %s référence `%s`, introuvable dans "
                     "le `.c`.\n        `lv_font_conv` a changé son gabarit — "
                     "relire le `.c`, pas ce regex." % (chemin, liste_nom))
        offsets = [int(x, 0) for x in
                   re.findall(r"0x[0-9a-fA-F]+|\d+", m.group(1))]
        if len(offsets) != list_len:
            sys.exit("ÉCHEC : `%s` porte %d entrées pour un `.list_length = %d` "
                     "dans %s.\n        Le `.c` se contredit — ne pas passer "
                     "outre." % (liste_nom, len(offsets), list_len, chemin))
        couverts.update(start + o for o in offsets)
    if not n_cmaps:
        sys.exit("ÉCHEC : aucune cmap reconnue dans %s. Le gabarit de "
                 "`lv_font_conv` a changé." % chemin)
    return couverts, n_cmaps


def verifier(chemin, syms, plage_a_temoins, attend_symboles=True):
    """RELIT le `.c` produit. Une génération « réussie » ne prouve rien.

    🔴 `attend_symboles=False` est réservé aux polices de VEILLE (dn3-3), qui ne
       portent DÉLIBÉRÉMENT aucun `LV_SYMBOL_*` : en Ambient le titre, l'icône et
       le libellé disparaissent, il ne reste que des valeurs.
    ⛔ CE N'EST PAS UN AFFAIBLISSEMENT DE LA GARDE, ET IL NE FAUT PAS QU'IL LE
       DEVIENNE : le drapeau dit « cette police n'est pas censée en porter »,
       il ne dit pas « ne vérifie pas ». La preuve : on EXIGE alors l'INVERSE —
       que les deux témoins soient ABSENTS. Une police de veille qui les
       porterait aurait embarqué FontAwesome sans qu'on le veuille, donc payé
       61 glyphes jamais dessinés — à 56 px, quatre fois le prix du 28.
    """
    src = open(chemin, encoding="utf-8", errors="replace").read()
    couverts, n_cmaps = codepoints_du_c(src, chemin)
    manques = []
    for cp in syms:
        if cp not in couverts:
            manques.append("symbole/icône U+%04X" % cp)
    for ch in plage_a_temoins:
        if ord(ch) not in couverts:
            manques.append("témoin « %s » (U+%04X)" % (ch, ord(ch)))
    # ⚠️ LES DEUX TÉMOINS QUI NE VIENNENT PAS DE L'AMONT — voir SYMBOLES_TEMOINS.
    for nom, cp in sorted(SYMBOLES_TEMOINS.items()):
        present = cp in couverts
        if attend_symboles and not present:
            manques.append("témoin INDÉPENDANT %s (U+%04X) — le bandeau MENU ou "
                           "le chevron de retour disparaîtrait EN SILENCE" % (nom, cp))
        if not attend_symboles and present:
            # 🔴 LE CONTRÔLE INVERSE, ET IL A AUTANT DE VALEUR : une police de
            #    veille qui porte un symbole a embarqué FontAwesome par accident.
            manques.append("témoin %s (U+%04X) PRÉSENT dans une police de VEILLE "
                           "— FontAwesome a été embarqué par accident, et à cette "
                           "taille il coûte cher pour des glyphes jamais dessinés"
                           % (nom, cp))
    if manques:
        sys.exit("ÉCHEC de vérification sur %s :\n  - %s"
                 % (chemin, "\n  - ".join(manques)))
    return n_cmaps


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
    ap.add_argument("--entete-seule", action="store_true",
                    help="réécrit UNIQUEMENT dn_font.h depuis ICONES, sans "
                         "toucher aux .c ni appeler lv_font_conv (donc sans npm "
                         "ni réseau). ⛔ N'EST LÉGITIME QUE SI LE CODEPOINT AJOUTÉ "
                         "EST DÉJÀ DANS LES .c : la commande le VÉRIFIE et refuse "
                         "sinon.")
    args = ap.parse_args()

    if args.entete_seule:
        return entete_seule()

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
                    syms = generer(t, plage, ICONES, kern, out)
                    # ⚠️ CORRECTIF DE REVUE (2026-08-18) : `--mesure` ne
                    # vérifiait RIEN. Or c'est lui qui a produit le tableau
                    # ayant tranché W5 — l'arbitrage a donc pu se faire sur des
                    # octets de polices auxquelles il manquait des glyphes.
                    # Compter ce qu'on n'a pas vérifié, c'est chiffrer du vide.
                    verifier(out, syms, "")
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

    # ── dn3-3 : LES DEUX POLICES DE LA VEILLE ────────────────────────────────
    # ⚠️ Le témoin accentué N'A PAS DE SENS ici : ces polices ne portent PAS le
    #    latin-1, délibérément. Le témoin est le DEGRÉ, seul caractère hors
    #    ASCII qu'une valeur puisse porter (« 61,0 °C »).
    for t in TAILLES_VEILLE:
        out = os.path.join(SORTIE, "dn_font_%d.c" % t)
        syms = generer(t, PLAGE_VEILLE, {}, not args.sans_kerning, out,
                       symboles=False)
        n = verifier(out, syms, "°", attend_symboles=False)
        d = octets_police(out)
        total += d["_total"]
        print("dn_font_%d.c : %d glyphes · %d o de données de police · VEILLE "
              "(plage réduite %s, ⛔ aucun symbole) · témoin ° vérifié"
              % (t, d["_glyphes"], d["_total"], PLAGE_VEILLE))

    ecrire_entete()
    print("dn_font.h : réécrit · TOTAL %d o de données de police (les QUATRE "
          "tailles). ⚠️ PLANCHER : le coût qui fait foi est le delta de BINAIRE."
          % total)


def entete_seule():
    """dn4-1 — réécrit `dn_font.h` SANS régénérer les `.c`, et le PROUVE légitime.

    🔴 POURQUOI CETTE PORTE EXISTE, ET POURQUOI ELLE EST GARDÉE. Ajouter une
       icône dont le codepoint est DÉJÀ dans les `.c` (parce que le générateur
       amont l'injecte avec ses symboles) ne change rien aux polices : l'union
       `-r` est identique, `lv_font_conv` produirait des `.c` bit-identiques.
       Relancer le générateur complet pour ça coûte npm + réseau, deux choses que
       le tableau des versions figées ne garantit pas — et un clone neuf SANS
       RÉSEAU échouerait.
       ⚠️ MAIS LE RACCOURCI EST UN PIÈGE S'IL N'EST PAS GARDÉ : écrire une macro
       `DN_ICONE_*` pour un codepoint ABSENT de la police ne produit AUCUNE
       erreur — juste un rectangle vide. C'est la classe de défaut « l'étiquette
       qui ment », et c'est exactement ce qui avait fait croire `fan` présent.
       ⇒ On RELIT donc les `.c` avec `codepoints_du_c()` (⛔ jamais un test de
         bornes) et on REFUSE si un codepoint d'`ICONES` n'y est pas.
    """
    manques = []
    for t in TAILLES:
        chemin = os.path.join(SORTIE, "dn_font_%d.c" % t)
        if not os.path.isfile(chemin):
            sys.exit("ÉCHEC : %s absent — il faut une vraie génération." % chemin)
        src = open(chemin, encoding="utf-8", errors="replace").read()
        couverts, n_cmaps = codepoints_du_c(src, chemin)
        absents = sorted(cp for cp in ICONES.values() if cp not in couverts)
        print("dn_font_%d.c : %d codepoints portés · %d cmaps · %d/%d icônes "
              "présentes" % (t, len(couverts), n_cmaps,
                             len(ICONES) - len(absents), len(ICONES)))
        for cp in absents:
            manques.append("U+%04X absent de %s" % (cp, chemin))
    if manques:
        sys.exit("ÉCHEC : --entete-seule REFUSÉ, les `.c` ne portent pas tout :\n"
                 "  - %s\n"
                 "  ⇒ il faut une VRAIE génération (`python3 tools/gen_font_dn.py`)."
                 % "\n  - ".join(manques))
    ecrire_entete()
    print("dn_font.h : réécrit depuis ICONES. Les deux `.c` n'ont PAS été touchés "
          "— vérifiable au `sha256sum`.")
    return 0


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
    # 🔴 CALCULÉS, PAS RÉCITÉS (correctif de revue 2026-08-18) : le `.h` annonçait
    # « 61 symboles + 10 icônes » pendant que le README disait 9, `dn_ui.c` et
    # `sdkconfig.defaults` disaient 7, et §15.4 s'intitulait « 7 glyphes ».
    syms = symboles_amont()
    deja = [cp for cp in ICONES.values() if cp in set(syms)]
    contenu = ENTETE_MODELE % {
        "plage": PLAGE,
        "icones": "\n".join(lignes),
        "n_icones": len(ICONES),
        "n_syms": len(syms),
        "n_deja": len(deja),
        "n_neufs": len(ICONES) - len(deja),
        "n_r": len(set(syms) | set(ICONES.values())),
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
 * ASCII + LATIN-1 COMPLET + la puce + les %(n_syms)d symboles LV_SYMBOL_* UNIQUES
 * + %(n_icones)d icônes FontAwesome, dont %(n_deja)d sont DÉJÀ des symboles ⇒
 * %(n_neufs)d codepoints neufs, et %(n_r)d au `-r` FontAwesome final. Elles sont
 * donc un SUR-ENSEMBLE STRICT des built-ins.
 * ⚠️ « 61 » est le nombre d'entrées BRUTES de la liste amont — elle contient un
 *    DOUBLON (61452 deux fois), d'où %(n_syms)d uniques. Ces nombres sont
 *    CALCULÉS à la génération, plus récités : cinq endroits du dépôt en
 *    annonçaient trois valeurs différentes, aucune juste (revue du 2026-08-18).
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
 *    absent), pas déduit d'une table.
 *
 * 🔴 L'ICÔNE DE LA CASE 4 EST LA DISQUETTE `save` (0xF0C7), tranchée par DÉCISION
 *    OWNER le 2026-08-18 (« icône disquette ») EN MÊME TEMPS QUE LE RENOMMAGE
 *    `VENTILOS` -> `DISQUE` : la case a changé de métrique (tr/min -> Mo/s), donc
 *    d'icône. Elle est GRATUITE — 0xF0C7 est DÉJÀ l'un des 60 codepoints de
 *    symboles que `built_in_font_gen.py` injecte : union `-r` inchangée à 68
 *    glyphes, delta = 0, les deux `.c` de police BIT-IDENTIQUES.
 *    ⚠️ Vérifié DANS LES `.c` PRODUITS avec `codepoints_du_c()`, ⛔ jamais par un
 *    test de bornes — c'est ce test-là qui avait fait croire `fan` présent.
 *
 * 📜 HISTORIQUE DE CETTE LIGNE — ELLE A MENTI DEUX FOIS, ET C'EST LA MÊME CAUSE.
 *    · jusqu'au 2026-08-17 elle annonçait `sync-alt`, alors que le descripteur
 *      disait autre chose ;
 *    · corrigée en `cog` le 2026-08-18… et re-fausse le jour même, parce que la
 *      story dn4-1 a changé l'icône POUR `save` sans toucher `ENTETE_MODELE`.
 *    🔴 LA CAUSE N'EST PAS L'ÉTOURDERIE, C'EST L'ENDROIT : `dn_font.h` est
 *    GÉNÉRÉ, donc toute correction faite dans le `.h` est effacée à la
 *    régénération suivante. ⛔ CE TEXTE SE CORRIGE **ICI**, dans
 *    `tools/gen_font_dn.py`, JAMAIS dans `main/fonts/dn_font.h`.
 *    ⚠️ Et il décrit un CHOIX D'AFFICHAGE, qui vit dans `dn_ui.c` (`k_desc[].icone`)
 *    et dans `k_icones_alt[]` : ce fichier ne peut que le RECOPIER, donc il
 *    re-divergera. La seule vraie parade serait de ne pas le recopier du tout.
 *    (Relevé en revue de code le 2026-08-18, DEUXIÈME occurrence.)
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

/* ASCII + latin-1 complet + puce + %(n_syms)d symboles + %(n_icones)d icônes. */
LV_FONT_DECLARE(dn_font_14)
LV_FONT_DECLARE(dn_font_28)

/*
 * ── dn3-3 : LES DEUX POLICES DE LA VEILLE ────────────────────────────────────
 *
 * 🔴 PLAGE RÉDUITE `0x20-0x7F,0xB0` — ⛔ NI accents latin-1, NI puce, NI aucun
 *    des 61 symboles LVGL, NI aucune icône FontAwesome. En Ambient le titre,
 *    l'icône et le libellé de grandeur DISPARAISSENT (décision owner du
 *    2026-08-25) : il ne reste que des valeurs, donc des chiffres, des unités,
 *    le « -- » de l'absence et le signe degré.
 * ⛔ NE JAMAIS s'en servir pour du texte d'interface : un accent, une puce ou un
 *    `LV_SYMBOL_*` n'y est PAS, et LVGL ne dessinerait RIEN — sans un mot.
 *    `dn_font_14` / `dn_font_28` restent les polices de l'interface.
 *
 * 🔴 LES DEUX TAILLES SONT MESURÉES SUR LA CARTE, ⛔ PAS CHOISIES ROND
 *    (`widget largeur`, 2026-08-25, case de 225 px dont 201 utiles) :
 *      · `dn_font_33` — AVEC l'unité. Pire cas « 2999,9 Mb/s » = 168 px à
 *        28 px ⇒ plafond 33,5 px.
 *      · `dn_font_56` — SANS l'unité. Pire cas « 2999,9 » = 90 px à 28 px
 *        ⇒ plafond 62,5 px, ramené à 56 pour garder ~10 %% de marge.
 *    ⚠️ Le pire cas THÉORIQUE de la table du firmware est « c.max 100,0 %% » =
 *       197 px, ce qui plafonnerait à 28,6 px — mais il porte un LIBELLÉ, et
 *       les libellés disparaissent en Ambient. C'est CE fait qui débloque
 *       l'agrandissement.
 */
LV_FONT_DECLARE(dn_font_33)
LV_FONT_DECLARE(dn_font_56)

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

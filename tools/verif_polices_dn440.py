# -*- coding: utf-8 -*-
"""dn4-40 / AC40.3 — LE CONTROLE D'ORPHELINS EST REJOUE PAR LE HARNAIS.

🔴 LE DEFAUT, MESURE PAR DIFFERENTIEL LE 2026-09-02. `firmware/desknode/main/
CMakeLists.txt` porte trois `FATAL_ERROR` qui empechent le glob des polices de
compiler un `.c` egare. **Rien ne les rejouait.** Trois passages complets du
harnais, arbre propre puis arbre pollue :

    arbre propre                          25 VERTE, 1 ROUGE, 1 NON-JOUABLE
    + un residu de police MAL NOMME       25 VERTE, 1 ROUGE, 1 NON-JOUABLE
                                          ⇒ ZERO occurrence du nom. Pas un mot.

Le cas que le `CMakeLists.txt` **nomme lui-meme** — le residu de sauvegarde —
laissait le bilan IDENTIQUE AU CARACTERE PRES a celui d'un arbre propre. La ou
`cmake` sort en erreur, le harnais rendait le verdict d'un arbre propre.

── ⛔ CE QUE CETTE GATE NE FAIT PAS, ET POURQUOI ─────────────────────────────

⛔ ELLE NE PASSE PAS PAR CMAKE. Le bloc de `CMakeLists.txt` est ecrit pour le
   contexte IDF ; rejoue en mode script, il echoue sur `Unknown arguments
   specified` faute de `CMP0057 NEW` — verifie : ⛔ ni `cmake_policy`, ⛔ ni
   `cmake_minimum_required` dans ce fichier. **Bruyant, mais pour la MAUVAISE
   raison** : un dev qui le rejoue tel quel croirait avoir trouve le defaut.
   ⇒ AC40.3.g laisse deux voies ; celle-ci ne prend pas la peine de poser une
     politique dans un fichier qui appartient au build.

⛔ ELLE NE REVIENT PAS A UNE LISTE MANUELLE. C'est ce que le glob a remplace,
   et l'AC3.3 de `dn4-24` l'interdit. **Rien n'est enumere ici** : ni les
   polices, ni leur compte. Le motif du glob et la forme du nom sont **LUS
   DANS LE `CMakeLists.txt`**, ⛔ pas recopies — si le build change sa regle et
   que cette gate ne suit pas, elle le DIT au lieu de garder l'ancienne.

⚖️ CE QUI FAIT AUTORITE : `fonts/dn_font.h`, et ⛔ JAMAIS l'outil de
   generation. Le `CMakeLists.txt` le recuse en toutes lettres, et la seule
   couverture incidente qui existait s'appuyait precisement dessus — en plus
   d'etre DECLAREE NON-JOUABLE des que l'arbre LVGL manque, c'est-a-dire
   **exactement en CI**. Y loger le controle aurait satisfait l'AC au poste en
   laissant le trou intact la ou il mord.

── ⚠️ LA BORNE DU GLOB EST DECLAREE, ⛔ PAS ELARGIE EN SILENCE ───────────────

Le glob est `dn_font_*.c`. Un suffixe qui **deplace l'extension** —
`dn_font_28.c.orig` — n'est vu **ni par CMake ni par un controle qui copie son
autorite**. Le controle (4) ci-dessous va donc **AU-DELA** de l'autorite qu'il
rejoue, et c'est ECRIT : il ne pretend pas etre le meme controle.

Codes de sortie : 0 vert · 1 vrai defaut · 2 usage.
⚠️ ⛔ AUCUN prerequis : cette gate est jouable dans un CLONE NU — pas d'arbre
   LVGL, pas de cockpit, pas d'ESP-IDF. C'est le poste ou le trou mord.
"""
import io
import os
import re
import sys

# 🔴 dn4-40 / AC40.7.c — l'instrument de campagne. Import DEFENSIF.
try:
    import dn_trace
except ImportError:                                  # pragma: no cover
    dn_trace = None

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(RACINE, "firmware", "desknode", "main")
FONTS = os.path.join(MAIN, "fonts")
CMAKE = os.path.join(MAIN, "CMakeLists.txt")
ENTETE = os.path.join(FONTS, "dn_font.h")

ok_total = [0]
ko_total = [0]


def ctrl(ok, libelle, detail_ok="", detail_ko=None):
    if dn_trace is not None:
        dn_trace.trace(ok, libelle)
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-58s %s" % (libelle[:58], detail_ok[:64]))
    else:
        ko_total[0] += 1
        print("  [KO ] %-58s %s"
              % (libelle[:58], detail_ok if detail_ko is None else detail_ko))
    return ok


def sans_commentaires_c(txt):
    """Retire `/* … */` puis `// …`. ⛔ DANS CET ORDRE — c'est celui du CMake.

    Motif : un `LV_FONT_DECLARE` MORT laisse en commentaire faisait passer un
    `.c` egare pour declare. Le CMake retire les commentaires d'abord ; cette
    gate fait pareil, sinon elle serait PLUS PERMISSIVE que ce qu'elle rejoue.
    """
    txt = re.sub(r"/\*.*?\*/", " ", txt, flags=re.S)
    return re.sub(r"//[^\n]*", " ", txt)


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 2
    print("=" * 78)
    print("dn4-40 / AC40.3 — LE GLOB DES POLICES NE COMPILE AUCUN ORPHELIN")
    print("=" * 78)
    print("\nautorite : firmware/desknode/main/fonts/dn_font.h  (LV_FONT_DECLARE)")
    print("regles   : LUES dans firmware/desknode/main/CMakeLists.txt, ⛔ pas recopiees")

    # ── 0. LE TERRAIN — ⛔ jamais un skip silencieux ─────────────────────────
    print("\n── 0. LE TERRAIN ─────────────────────────────────────────────────")
    for p, quoi in ((FONTS, "le repertoire des polices"),
                    (ENTETE, "l'en-tete qui fait AUTORITE"),
                    (CMAKE, "le CMakeLists qui porte les REGLES")):
        existe = os.path.isdir(p) if quoi.startswith("le repertoire") \
            else os.path.isfile(p)
        if not ctrl(existe, "%s est la" % quoi,
                    os.path.relpath(p, RACINE),
                    "⛔ ABSENT : %s" % os.path.relpath(p, RACINE)):
            print("\n⛔ ARRET : sans son terrain, cette gate ne peut RIEN dire.")
            print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
            return 1

    # ── 1. LES REGLES SONT LUES DANS LE BUILD, ⛔ PAS RECOPIEES ──────────────
    print("\n── 1. LES REGLES VIENNENT DU BUILD (⛔ aucune liste ecrite ici) ───")
    cm = io.open(CMAKE, encoding="utf-8").read()
    m_glob = re.search(r'file\(GLOB\s+DN_FONTS[^)]*?'
                       r'"\$\{CMAKE_CURRENT_LIST_DIR\}/fonts/([^"]+)"', cm, re.S)
    m_forme = re.search(r'nom_complet\s+MATCHES\s+"(\^dn_font_[^"]+)"', cm)
    ctrl(m_glob is not None,
         "le MOTIF du glob est lu dans le CMakeLists",
         "motif : %s" % (m_glob.group(1) if m_glob else "—"),
         "⛔ INTROUVABLE — le build a change sa regle et cette gate ne la "
         "rejoue plus")
    # ⚠️ CMake echappe deux fois : le fichier porte `\\.c$`, la regex Python
    #    veut `\.c$`. On DESECHAPPE, et on imprime la regle EFFECTIVE — ⛔ pas
    #    celle du fichier : un lecteur doit voir ce qui s'applique.
    forme = m_forme.group(1).replace("\\\\", "\\") if m_forme else None
    ctrl(m_forme is not None,
         "la FORME du nom exigee est lue dans le CMakeLists",
         "regle effective : %s" % (forme or "—"),
         "⛔ INTROUVABLE — la gate garderait une regle PERIMEE")
    # 🔴 REVUE 2026-09-03 — LA REGEX CMAKE N'EST PAS FORCEMENT COMPILABLE PAR
    #    PYTHON. Sans ce controle, `re.match(forme, …)` levait une `re.error`
    #    NON ATTRAPEE plus bas : la gate mourait AVANT sa ligne de BILAN, et un
    #    runner ne pouvait pas distinguer ce cas d'un plantage quelconque.
    if forme is not None:
        try:
            re.compile(forme)
            forme_ok = True
        except re.error as x:
            forme_ok = False
            ctrl(False, "la FORME lue est une regex EXPLOITABLE ici", "",
                 "⛔ CMake accepte `%s`, Python la refuse : %s — la gate ⛔ ne "
                 "peut PAS rejouer cette regle" % (forme, x))
        else:
            ctrl(True, "la FORME lue est une regex EXPLOITABLE ici",
                 "compilee sans erreur")
        if not forme_ok:
            print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
            return 1
    if m_glob is None or m_forme is None:
        print("\n⛔ ARRET : ⛔ une gate ne DEVINE pas la regle qu'elle rejoue.")
        print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
        return 1
    motif_glob = m_glob.group(1)

    # ── 2. L'AUTORITE EST LISIBLE — le 1er FATAL_ERROR du CMake ─────────────
    print("\n── 2. L'AUTORITE EST LISIBLE (1er FATAL_ERROR rejoue) ────────────")
    txt = sans_commentaires_c(io.open(ENTETE, encoding="utf-8").read())
    declarees = re.findall(r"LV_FONT_DECLARE[ \t]*\([ \t]*([A-Za-z0-9_]+)[ \t]*\)",
                           txt)
    ctrl(bool(declarees),
         "au moins un LV_FONT_DECLARE est lu dans dn_font.h",
         "%d police(s) declaree(s)" % len(declarees),
         "⛔ AUCUN LV_FONT_DECLARE — le controle ne peut pas s'exercer, et "
         "⛔ il ne passe PAS en silence")
    if not declarees:
        print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
        return 1
    connues = set(declarees)

    # ── 3. LE GLOB, REJOUE — les 2e et 3e FATAL_ERROR ───────────────────────
    print("\n── 3. CE QUE LE GLOB RAMASSE (motif `%s`) ──────" % motif_glob)
    import fnmatch
    # 🔴 REVUE 2026-09-03 — LE GLOB N'AVAIT AUCUNE GARDE DE POPULATION VIDE.
    #    Mesure : sur un arbre sans aucun `.c` de police, cette gate NEUVE
    #    rendait `9 OK, 0 KO`, rc=0 — alors que le build ne compilerait AUCUNE
    #    police. Elle refuse pourtant ce cas pour son AUTORITE (section 2) :
    #    l'oublier pour la POPULATION, c'est le defaut d'AC40.2 dans
    #    l'instrument cree pour le fermer. ⚠️ On ne compte QUE des fichiers :
    #    un REPERTOIRE nomme comme une police n'est pas une police.
    ramasses = sorted(n for n in os.listdir(FONTS)
                      if fnmatch.fnmatch(n, motif_glob)
                      and os.path.isfile(os.path.join(FONTS, n)))
    print("     %d fichier(s) ramasse(s) : %s"
          % (len(ramasses), ", ".join(ramasses) or "(aucun)"))
    ctrl(bool(ramasses),
         "le glob ramasse AU MOINS une police",
         "%d fichier(s) ramasse(s)" % len(ramasses),
         "⛔ 0 fichier ramasse par `%s` dans fonts/ — le build ne compilerait "
         "AUCUNE police, et les deux controles suivants passeraient sur une "
         "population VIDE" % motif_glob)
    if not ramasses:
        print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
        return 1
    mal_nommes = [n for n in ramasses if not re.match(forme, n)]
    ctrl(not mal_nommes,
         "tout `.c` ramasse porte la FORME `dn_font_<n>.c`",
         "%d fichier(s) ramasse(s), 0 mal nomme" % len(ramasses),
         "⛔ %d RESIDU(S) : %s — sauvegarde, essai ou renommage. L'EFFACER "
         "ou le sortir de fonts/."
         % (len(mal_nommes), ", ".join("fonts/" + n for n in mal_nommes)))
    orphelins = [n for n in ramasses
                 if re.match(forme, n) and n[:-2] not in connues]
    ctrl(not orphelins,
         "tout `.c` ramasse est DECLARE dans dn_font.h",
         "%d declaree(s) : %s" % (len(connues), " ".join(sorted(connues))),
         "⛔ %d ORPHELIN(S) : %s — soit un residu a EFFACER, soit dn_font.h "
         "doit le declarer. Le compiler en silence gonfle le binaire sans "
         "qu'aucun code ne puisse l'atteindre."
         % (len(orphelins), ", ".join("fonts/" + n for n in orphelins)))

    # ── 4. ⚠️ AU-DELA DE L'AUTORITE — la BORNE du glob, DECLAREE ────────────
    print("\n── 4. ⚠️ AU-DELA DE L'AUTORITE — la BORNE du glob ────────────────")
    print("     ⛔ CE CONTROLE N'EST PAS DANS LE CMakeLists, et c'est ECRIT.")
    print("     Le glob est `%s` : un suffixe qui DEPLACE l'extension"
          % motif_glob)
    print("     (`dn_font_28.c.orig`) n'est vu ⛔ NI par CMake ⛔ NI par un")
    print("     controle qui copie son autorite. Il serait donc INVISIBLE.")
    # 🔴 REVUE 2026-09-03 — TROIS DEFAUTS DANS CE SEUL FILTRE.
    #    (i) Il n'excluait que L'EN-TETE NOMME : tout autre `dn_font*.h`
    #        LEGITIME etait denonce comme RESIDU, avec la consigne de
    #        L'EFFACER. Un en-tete n'est pas un residu de generation.
    #    (ii) Un REPERTOIRE portant un nom de police comptait comme fichier.
    #    (iii) Le prefixe `^dn_font` rate ce qui ne le porte pas — c'est une
    #        BORNE, et elle est desormais ECRITE plutot que subie.
    hors_glob = [n for n in sorted(os.listdir(FONTS))
                 if not fnmatch.fnmatch(n, motif_glob)
                 and os.path.isfile(os.path.join(FONTS, n))]
    residus = [n for n in hors_glob
               if n != os.path.basename(ENTETE)
               and not n.endswith(".h")
               and re.match(r"^dn_font", n)]
    ctrl(not residus,
         "aucun residu de police n'ECHAPPE au glob",
         "%d fichier(s) hors glob dans fonts/ (%s), 0 residu"
         % (len(hors_glob), ", ".join(hors_glob) or "aucun"),
         "⛔ %d RESIDU(S) HORS GLOB : %s — invisibles du build ET de son "
         "controle. ⇒ les EFFACER."
         % (len(residus), ", ".join("fonts/" + n for n in residus)))

    print("\n" + "=" * 78)
    print("⚠️ CE QUE CETTE GATE NE SOLDE PAS :")
    print("   · la direction INVERSE — une police DECLAREE dont le `.c`")
    print("     manque — reste au compilateur (`dn4-24` l'a laissee la) ;")
    print("   · elle ne compile RIEN : elle ne dit pas qu'une police est")
    print("     VALIDE, seulement qu'aucune n'entre au build sans etre")
    print("     declaree.")
    print("=" * 78)
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return 1 if ko_total[0] else 0


if __name__ == "__main__":
    sys.exit(main())

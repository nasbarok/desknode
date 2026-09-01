#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-42 / AC5 — L'ECRAN PARLE DEUX LANGUES, ET RIEN NE PEUT DIVERGER EN SILENCE.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

Traduire une interface cree QUATRE familles de defauts, et **les quatre sont
MUETTES sur la dalle** — c'est ce qui les rend cheres :

  1. **UN TROU DE TRADUCTION.** Une cle sans chaine : le label affiche du vide,
     et un label vide a l'air d'un espace, ⛔ pas d'une panne.
  2. **UN LITTERAL OUBLIE.** Une chaine restee en dur : elle reste francaise sur
     un ecran anglais, et c'est la SEULE que personne ne pense a chercher.
  3. **UN GLYPHE ABSENT.** `LV_USE_FONT_PLACEHOLDER=y` fait dessiner une BOITE,
     **sans un mot au journal**. C'est ce qui a fait perdre son `U` a « AOUT »
     avec les built-ins — et c'est ce qui dessinait le `—` de `k_source[].nom`
     en boite sur TOUTES les pages de detail, depuis toujours.
  4. **UNE LARGEUR QUI NE TIENT PLUS.** LVGL CLIPPE au bord, sans un mot. Un mot
     qui tient en francais peut deborder en anglais.

======================= ⛔ CE QU'ELLE NE RECITE PAS =========================

⛔ ELLE NE CONNAIT AUCUNE LARGEUR « ATTENDUE ». Elle RECALCULE chaque largeur
   depuis les `adv_w` des `.c` de police, avec la MEME arithmetique que LVGL
   (arrondi PAR GLYPHE + kerning par classes) — voir `tools/dn_police.py`.

⛔ ELLE NE RECITE AUCUNE LISTE DE GLYPHES. Elle LIT les cmaps des `.c` de
   police, denses ET sparses. Une liste ecrite se perimerait au premier
   `gen_font_dn.py`.

⛔ ELLE NE RECITE AUCUNE GEOMETRIE. `MENU_SEL_W`, `MENU_LG_W`, `W_PAD`,
   `W_BADGE_DE_DROITE`, `DN_UI_BARRE_DATE_X`… sont RELUS des `#define` du
   firmware et RE-EVALUES. Un `210` ecrit ici se serait perime au premier
   ajustement de panneau.

⛔ ELLE NE CODE PAS EN DUR LA CLE `dn4-42` (AC5.4). Les seules chaines cherchees
   sont des SYMBOLES DU CODE (`DN_TXT_LISTE`, `k_txt`, `dn_t`, …), qui ne
   portent aucun numero de story. ⇒ un futur auteur qui ajoute une langue ou une
   cle est garde exactement comme celui-ci.

⛔ ELLE NE POSE **AUCUN JETON D'EXEMPTION**, et c'est declare (AC5.4) : ces
   jetons n'ont aucun echappement, et les citer en commentaire les ACCORDE
   (defaut mesure dans ce depot). Aucun controle ci-dessous ne peut donc etre
   desarme par une ligne de commentaire.

======================= ⛔ CE QU'ELLE NE COUVRE PAS =========================

⛔ **LES CHAINES COMPOSEES A CHAUD.** Elle ne connait ni le compteur de veilles
   du jour, ni le code d'erreur NVS reel, ni la valeur d'une case. Ce que le
   firmware COMPOSE est garde a l'execution par `dn_ui_menu_trop_larges()` et
   `dn_widget_trop_larges()` — ⇒ **les deux sont necessaires**, et c'est ecrit
   ici plutot que decouvert.
   ⚠️ Elle contrôle quand meme le PIRE CAS RECOMPOSE de la ligne d'echec NVS,
      parce que celle-la a un pire cas BORNE et CONNU.
⛔ **L'OEIL.** Qu'un mot anglais soit le BON mot ne se calcule pas. AC6 est une
   seance carte, ⛔ pas une gate.
⛔ **LA CONSOLE.** Elle reste FRANCAISE (decision owner du 2026-09-01) — mais la
   gate verifie justement qu'elle le RESTE (controle 8).

Sortie : `BILAN : n OK, m KO`, rc 0 si tout passe, 1 sinon.
Usage  : python3 tools/verif_langues_dn442.py [--mutant <1..N>] [--liste-mutants]
         `--mutant` casse UNE propriete EN MEMOIRE et doit faire ROUGIR (AC5.3).
         ⛔ Aucun fichier n'est modifie.
"""

import argparse
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "tools"))
import dn_police  # noqa: E402  — bibliotheque du depot, ⛔ pas une gate

MAIN = os.path.join(RACINE, "firmware", "desknode", "main")
F_LANGUE_H = os.path.join(MAIN, "dn_langue.h")
F_LANGUE_C = os.path.join(MAIN, "dn_langue.c")
F_UI = os.path.join(MAIN, "dn_ui.c")
F_WIDGET_C = os.path.join(MAIN, "dn_widget.c")
F_WIDGET_H = os.path.join(MAIN, "dn_widget.h")
F_LINK = os.path.join(MAIN, "dn_link.c")
F_CONSOLE = os.path.join(MAIN, "dn_console.c")

# 🔴 LE PLUS LONG DES `ESP_ERR_NVS_*` DE L'IDF, prefixe `ESP_ERR_` RETIRE —
#    c'est ce que le MENU affiche. RELEVE dans
#    `components/nvs_flash/include/` : `ESP_ERR_NVS_KEYS_NOT_INITIALIZED`.
# ⚠️ ⛔ Ce n'est PAS une largeur recitee : c'est une DONNEE d'entree, et la
#    largeur qui en decoule est CALCULEE. Un code plus long ferait rougir la
#    gate — c'est le but.
NVS_ERR_PIRE = "NVS_KEYS_NOT_INITIALIZED"

OK = [0]
KO = [0]
_MUTANT = None
MUTANTS = {}


def dire(ok, libelle, detail=""):
    (OK if ok else KO)[0] += 1
    print("  [%s] %-56s %s" % ("OK " if ok else "KO ", libelle, detail))


def lire(chemin):
    with open(chemin, encoding="utf-8", errors="replace") as f:
        return f.read()


def sans_commentaires(src):
    """Retire les commentaires C. ⛔ GARDE les chaines : ce sont elles qu'on
    controle. C'est l'inverse du `code_nu()` de `verif_paliers_dn441.py`, et
    l'inverse est DELIBERE — ici, une chaine EST la donnee.
    ⚠️ Motif deja paye par ce depot : *« un jeton cite en commentaire est
       ACCORDE »*. Sans ce retrait, un exemple de litteral ecrit dans un
       commentaire ferait rougir un fichier juste.
    """
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    src = re.sub(r"//[^\n]*", " ", src)
    return src


def defini(src, nom, env=None):
    """La valeur ENTIERE d'un `#define <nom> …`, EXPRESSION COMPRISE.

    🔴 UN `\\d+` NU NE SUFFIT PAS, ET C'EST LA GATE QUI L'A DIT AU PREMIER TIR :
       `MENU_PAN_W` vaut `(DN_LCD_H_RES - 2 * DN_UI_MARGE)`, ⛔ pas `460`. Le
       depot ECRIT ses geometries en arithmetique — c'est meme sa doctrine
       (*« CALCULE, ⛔ pas ajuste a l'oeil »*). Une gate qui n'accepte que des
       litteraux forcerait donc a RECITER le resultat ici, c'est-a-dire a
       fabriquer la divergence qu'elle est censee empecher.
    ⚠️ L'evaluation est BORNEE : chiffres, `+ - * / ( )` et noms DEJA connus.
       Tout le reste rend None ⇒ la gate DIT qu'elle n'a pas su lire, ⛔ elle ne
       devine pas.
    """
    m = re.search(r"^#define\s+%s\s+([^\n/]+)" % re.escape(nom), src, re.M)
    if not m:
        return None
    expr = m.group(1).strip()
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
    r"""Le contenu REEL d'un litteral C, concatenations et `\xHH` compris.

    ⛔ Un `str` brut du source dirait que `"\xC2\xB0" "C"` fait 12 signes dont
       aucun n'est `°` — et la gate aurait declare le degre ABSENT de polices
       qui le portent. Mesure faite en ecrivant cette gate.
    """
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
    # Les `\xHH` d'une chaine UTF-8 sont des OCTETS : on les recompose.
    s = "".join(out)
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def M(n, src, avant, apres):
    """Mutation ciblee : si `--mutant n`, remplace `avant` par `apres`."""
    if _MUTANT != n:
        return src
    if avant not in src:
        sys.exit("MUTANT %d INAPPLICABLE : le motif est introuvable. ⛔ Un "
                 "mutant qui ne s'applique pas ne prouve RIEN — il faut le "
                 "reparer, ⛔ pas conclure que le controle est vert." % n)
    return src.replace(avant, apres, 1)


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
    print("dn4-42 / AC5 — LA TABLE DE LANGUES, LES POLICES ET LES LARGEURS"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)

    langue_h = lire(F_LANGUE_H)
    langue_c = lire(F_LANGUE_C)
    ui = lire(F_UI)
    widget_c = lire(F_WIDGET_C)
    widget_h = lire(F_WIDGET_H)
    link = lire(F_LINK)
    console = lire(F_CONSOLE)

    polices = dn_police.toutes()

    # ══ 1. LA TABLE : UNE LIGNE = UNE CLE = TOUTES SES TRADUCTIONS ══════════
    print("\n── 1. LA TABLE EST COMPLETE (AC1.1, AC5.2) ────────────────────")

    MUTANTS[1] = "vide la traduction EN d'une cle (une chaine VIDE compile)"
    MUTANTS[2] = "retire une COLONNE de la liste X (une cle sans traduction)"

    bloc = re.search(r"#define\s+DN_TXT_LISTE\(X\)(.*?)\n\s*\n", langue_h, re.S)
    if not bloc:
        dire(False, "la liste `DN_TXT_LISTE(X)` est lisible",
             "⛔ motif introuvable — le gabarit a change")
        print("\n" + "=" * 78)
        print("BILAN : %d OK, %d KO" % (OK[0], KO[0]))
        print("=" * 78)
        return 1
    corps = bloc.group(1)
    corps = M(1, corps, '"NETWORK",                  "RÉSEAU"',
              '"",                         "RÉSEAU"')
    corps = M(2, corps, 'X(CASE_DISQUE,     "DISK",                     "DISQUE")',
              'X(CASE_DISQUE,     "DISK")')
    corps_nu = sans_commentaires(corps)

    # ⚠️ On lit les APPELS `X(...)`, ⛔ pas les lignes : une entree peut tenir
    #    sur deux lignes (c'est le cas de trois d'entre elles).
    appels = []
    i = 0
    while True:
        m = re.search(r"\bX\(", corps_nu[i:])
        if not m:
            break
        deb = i + m.end()
        prof, j, dedans = 1, deb, False
        while j < len(corps_nu) and prof:
            c = corps_nu[j]
            if c == '"' and corps_nu[j - 1] != "\\":
                dedans = not dedans
            elif not dedans and c == "(":
                prof += 1
            elif not dedans and c == ")":
                prof -= 1
            j += 1
        appels.append(corps_nu[deb:j - 1])
        i = j

    dire(len(appels) >= 40, "la liste porte des cles",
         "%d cle(s) — ⛔ un compte, pas une liste ecrite ici" % len(appels))

    # Chaque appel doit porter EXACTEMENT `1 + n_langues` arguments non vides.
    ordre = re.findall(r"DN_LANGUE_([A-Z]+)\s*(?:=\s*\d+\s*)?,", langue_h)
    langues = [l for l in ordre if l != "N"]
    dire(len(langues) >= 2, "l'enumeration nomme les langues",
         " · ".join(langues))

    trous, noms = [], []
    for a in appels:
        # decoupe au niveau 0 de parenthese, hors chaines
        parts, cur, dedans, prof = [], "", False, 0
        for k, c in enumerate(a):
            if c == '"' and (k == 0 or a[k - 1] != "\\"):
                dedans = not dedans
            if not dedans and c == "(":
                prof += 1
            if not dedans and c == ")":
                prof -= 1
            if not dedans and prof == 0 and c == ",":
                parts.append(cur.strip())
                cur = ""
                continue
            cur += c
        parts.append(cur.strip())
        nom = parts[0]
        noms.append(nom)
        if len(parts) != 1 + len(langues):
            trous.append("%s : %d argument(s) pour %d attendu(s)"
                         % (nom, len(parts), 1 + len(langues)))
            continue
        for idx, p in enumerate(parts[1:]):
            if deplier_c(p) == "":
                trous.append("%s : traduction %s VIDE" % (nom, langues[idx]))
    dire(not trous, "toute cle a une traduction dans TOUTES les langues",
         "%d cle(s) x %d langue(s)" % (len(appels), len(langues))
         if not trous else "⛔ " + " · ".join(trous[:2]))

    MUTANTS[3] = "met le FRANCAIS en index 0 (le defaut cesserait d'etre l'anglais)"
    h3 = M(3, langue_h, "DN_LANGUE_EN = 0,\n    DN_LANGUE_FR,",
           "DN_LANGUE_FR = 0,\n    DN_LANGUE_EN,")
    ordre3 = re.findall(r"DN_LANGUE_([A-Z]+)\s*(?:=\s*\d+\s*)?,", h3)
    dire(ordre3 and ordre3[0] == "EN",
         "⛔ LE DEFAUT EST L'ANGLAIS (AC3.1) — index 0 de l'enum",
         "1er = %s ⇒ une NVS vide rend %s" % (ordre3[0], ordre3[0]))

    # L'ordre des colonnes du `.c` DOIT suivre celui de l'enum.
    MUTANTS[4] = "intervertit les colonnes EN/FR de `k_txt[]` (defaut inverse en silence)"
    c4 = M(4, langue_c, "[DN_LANGUE_EN] = {\n#define X(nom, en, fr) [DN_T_##nom] = en,",
           "[DN_LANGUE_EN] = {\n#define X(nom, en, fr) [DN_T_##nom] = fr,")
    cols = re.findall(r"\[DN_LANGUE_(\w+)\]\s*=\s*\{\s*#define X\(nom, en, fr\)"
                      r"\s*\[DN_T_##nom\]\s*=\s*(\w+),", c4)
    dire(cols == [(l, l.lower()) for l in langues],
         "chaque colonne de `k_txt[]` lit SON argument",
         " · ".join("%s←%s" % (a, b) for a, b in cols) if cols else "⛔ illisible")

    # ══ 2. LES DOUBLONS SONT RESORBES (AC1.2, AC1.3) ════════════════════════
    print("\n── 2. LES DOUBLONS SONT RESORBES (AC1.2, AC1.3) ───────────────")

    MUTANTS[5] = "reintroduit une table `k_nom[]` parallele dans dn_ui.c"
    ui5 = M(5, ui, "static const char *case_nom(int idx)",
            'static const char *const k_nom[DN_UI_METRIQUES] = {"CPU"};\n'
            "static const char *case_nom(int idx)")
    ui5_nu = sans_commentaires(ui5)
    dire("k_nom[" not in ui5_nu,
         "⛔ `k_nom[]` a DISPARU de dn_ui.c (AC1.2)",
         "⇒ les six noms n'ont plus qu'UNE source : `k_desc[].titre_cle`")

    dire(re.search(r"\.titre\s*=", sans_commentaires(ui)) is None,
         "⛔ aucun `.titre = \"…\"` litteral ne subsiste",
         "⇒ le descripteur ne porte plus qu'une CLE")

    # AC1.3 — la 4e liste (console) reste HORS table, et c'est DECLARE.
    MUTANTS[6] = "efface la declaration « hors table » de la 4e liste (console)"
    h6 = M(6, langue_h, "`dn_console.c`, `cmd_hist` (la 4ᵉ liste des noms de case)",
           "une liste quelconque")
    dire("cmd_hist" in h6 and "HORS TABLE" in h6.upper(),
         "la 4e liste (console `cmd_hist`) est DECLAREE hors table (AC1.3)",
         "⇒ 8 series, ⛔ pas 6 cases : elle ne decrit pas la meme chose")

    # ══ 3. AUCUN LITTERAL DANS LES PUITS DE TEXTE DE LA DALLE (AC1.1) ═══════
    print("\n── 3. AUCUN LITTERAL N'ATTEINT LA DALLE (AC1.1, AC5.2) ────────")

    MUTANTS[7] = "remet un libelle francais en dur dans un `texte()` du MENU"
    ui7 = M(7, ui, "menu_titre_panneau(p1, DN_T_MENU_VEILLE);",
            'texte(p1, "VEILLE", &dn_font_14, lv_color_hex(0xa0d8ff), MENU_SEL_X0, 10);')
    #
    # ⚠️ CE QUI EST TOLERE, ET POURQUOI — ⛔ ce n'est pas une exemption, c'est
    #    la definition de « traduisible » :
    #      · une chaine SANS AUCUNE LETTRE (« -- », « ?», « --:-- », "") ne se
    #        traduit pas — il n'y a rien a traduire ;
    #      · `LV_SYMBOL_*` est un glyphe FontAwesome, ⛔ pas un mot.
    #    Un mot francais oublie porte forcement des lettres ⇒ il est ATTRAPE.
    PUITS = r"(?:dn_widget_)?texte\(|lv_label_set_text\("
    litteraux = []
    for src, nomf in ((ui7, "dn_ui.c"), (widget_c, "dn_widget.c")):
        nu = sans_commentaires(src)
        for m in re.finditer(PUITS, nu):
            # l'argument texte : 2e de `texte(parent, txt, …)`, 2e de
            # `lv_label_set_text(obj, txt)`
            reste = nu[m.end():m.end() + 300]
            args, cur, prof, dedans = [], "", 0, False
            for k, c in enumerate(reste):
                if c == '"' and (k == 0 or reste[k - 1] != "\\"):
                    dedans = not dedans
                if not dedans and c in "([":
                    prof += 1
                if not dedans and c in ")]":
                    if prof == 0:
                        args.append(cur.strip())
                        break
                    prof -= 1
                if not dedans and prof == 0 and c == ",":
                    args.append(cur.strip())
                    cur = ""
                    continue
                cur += c
            if len(args) < 2:
                continue
            txt = args[1]
            if '"' not in txt:
                continue
            if "LV_SYMBOL_" in txt:
                continue
            val = deplier_c(txt)
            if not any(ch.isalpha() for ch in val):
                continue
            litteraux.append("%s : « %s »" % (nomf, val[:40]))
    dire(not litteraux,
         "⛔ aucun litteral PORTEUR DE LETTRES n'atteint un label",
         "puits balayes : `texte()`, `dn_widget_texte()`, `lv_label_set_text()`"
         if not litteraux else "⛔ " + " · ".join(litteraux[:2]))

    # ══ 4. LES POLICES PORTENT VRAIMENT CE QU'ON LEUR DEMANDE (AC4.3, AC4.4) ═
    print("\n── 4. LES POLICES PORTENT LES GLYPHES (AC4.3, AC4.4) ──────────")

    MUTANTS[8] = "remet un `—` (U+2014) dans une chaine de la table"
    MUTANTS[10] = "met un accent dans une UNITE (invisible en dn_font_33/56)"

    corps_g = corps
    corps_g = M(8, corps_g, '"NONE - not wired yet"', '"NONE — not wired yet"')
    corps_g = M(10, corps_g, '"rpm",                      "tr/min"',
                '"rpm",                      "tr/mn\\xc3\\xa9"')

    # La table, dépliée : nom -> {langue: chaine}
    table = {}
    for a in re.split(r"\n", sans_commentaires(corps_g)):
        pass
    # (re-decoupe des appels sur le corps MUTE)
    corps_g_nu = sans_commentaires(corps_g)
    i, appels_g = 0, []
    while True:
        m = re.search(r"\bX\(", corps_g_nu[i:])
        if not m:
            break
        deb = i + m.end()
        prof, j, dedans = 1, deb, False
        while j < len(corps_g_nu) and prof:
            c = corps_g_nu[j]
            if c == '"' and corps_g_nu[j - 1] != "\\":
                dedans = not dedans
            elif not dedans and c == "(":
                prof += 1
            elif not dedans and c == ")":
                prof -= 1
            j += 1
        appels_g.append(corps_g_nu[deb:j - 1])
        i = j
    for a in appels_g:
        parts, cur, dedans, prof = [], "", False, 0
        for k, c in enumerate(a):
            if c == '"' and (k == 0 or a[k - 1] != "\\"):
                dedans = not dedans
            if not dedans and c == "(":
                prof += 1
            if not dedans and c == ")":
                prof -= 1
            if not dedans and prof == 0 and c == ",":
                parts.append(cur.strip())
                cur = ""
                continue
            cur += c
        parts.append(cur.strip())
        if len(parts) == 1 + len(langues):
            table[parts[0]] = dict(zip(langues, [deplier_c(p) for p in parts[1:]]))

    # 🔴 LES POLICES D'INTERFACE — toute chaine de la table peut y passer.
    #    ⛔ On ne recite pas laquelle : `fonts/dn_font.h` fait autorite (meme
    #    source que le CMakeLists), et `DN_FONT_LISTE` dit qui est d'INTERFACE.
    fonth = lire(os.path.join(MAIN, "fonts", "dn_font.h"))
    interface = set(re.findall(r"DN_FONT_ENTREE\(\s*(dn_font_\d+)\s*,\s*[^,]*,\s*"
                               r"DN_FONT_ROLE_INTERFACE", fonth))
    veille = set(re.findall(r"DN_FONT_ENTREE\(\s*(dn_font_\d+)\s*,\s*[^,]*,\s*"
                            r"DN_FONT_ROLE_VEILLE", fonth))
    if not interface or not veille:
        # Repli LU, ⛔ pas recite : les polices de VEILLE sont celles dont la
        # couverture n'a PAS de latin-1 (`é` = U+00E9, temoin).
        interface = set(n for n, p in polices.items() if p.porte(0xE9))
        veille = set(polices) - interface
    dire(bool(interface) and bool(veille),
         "les roles de police sont LUS (interface / veille)",
         "interface : %s · veille : %s"
         % (",".join(sorted(interface)), ",".join(sorted(veille))))

    absents = []
    for nom, trads in table.items():
        for lg, txt in trads.items():
            for pf in sorted(interface):
                for ch in polices[pf].absents(txt):
                    absents.append("DN_T_%s/%s : U+%04X « %s » absent de %s"
                                   % (nom, lg, ord(ch), ch, pf))
    dire(not absents,
         "⛔ aucune chaine de la table ne porte un glyphe ABSENT (AC4.3)",
         "%d chaine(s) confrontees aux cmaps RELUES" % (len(table) * len(langues))
         if not absents else "⛔ " + " · ".join(sorted(set(absents))[:2]))

    #
    # ══════════════════════════════════════════════════════════════════════
    # 🔴 LES CHAINES **COMPOSEES** AUSSI — LE TROU QUE LE MUTANT 9 A OUVERT
    # ══════════════════════════════════════════════════════════════════════
    #
    # 🔴 CE CONTROLE N'EXISTAIT PAS, ET C'EST UN MUTANT QUI L'A DIT.
    #    Le mutant 9 (« remettre un `⛔` dans la ligne d'echec NVS ») restait
    #    **VERT** : le controle ci-dessus ne balaie que **la table**, et la
    #    ligne d'echec NVS est un `snprintf` de `dn_ui.c` — c'est-a-dire une
    #    chaine qui atteint la dalle SANS passer par la table.
    #    ⚠️ C'est exactement la lecon *« un mutant qui ne s'applique pas ne
    #       prouve RIEN »* : le mutant avait ete DECLARE et jamais APPLIQUE, et
    #       la gate a repondu vert a une question qu'elle ne posait pas.
    #
    # LA PROPRIETE, ET ELLE N'EST PAS SCOPEE A `dn4-42` :
    #   **dans toute FONCTION qui pose un label**, une chaine litterale hors
    #   journal doit etre rendable par les polices d'INTERFACE.
    #
    # 🔴 LA PORTEE A ETE RESSERREE **PARCE QU'ELLE A ROUGI SUR DU CODE JUSTE**,
    #    et le motif vaut d'etre ecrit. La 1re version balayait TOUT le fichier
    #    hors journaux. Elle a epingle deux choses PARFAITEMENT SAINES :
    #      · les messages de `_Static_assert` — du diagnostic de COMPILATION ;
    #      · `k_icones_alt[].nom` — une table que la CONSOLE imprime, et dont le
    #        commentaire dit en toutes lettres *« l'owner lit cette liste a la
    #        console pendant qu'il regarde la dalle »*.
    #    ⇒ Ni l'un ni l'autre n'atteint jamais un label. Une gate qui rougit sur
    #      du code juste finit desarmee — le depot l'a deja paye (`dn4-14`).
    # ⇒ Le filtre est donc un PROXY DE FLOT DE DONNEES, ⛔ pas un filtre de mot :
    #   une chaine composee dans la MEME fonction que le `lv_label_set_text` qui
    #   la pose. C'est le cas de la ligne d'echec NVS (`menu_reparametrer`), et
    #   c'est le cas de toutes les chaines de la dalle.
    # ⚠️ ⛔ CE QUE CE PROXY NE COUVRE PAS, ET C'EST DECLARE : une chaine composee
    #    dans une fonction et posee dans une AUTRE. Il n'y en a aucune
    #    aujourd'hui ; le jour ou il y en aura une, ce controle ne la verra pas.
    MUTANTS[9] = "remet un `⛔` (U+26D4) dans la ligne d'echec NVS composee"

    def fonctions_a_label(src):
        """Le corps des fonctions qui POSENT un label, commentaires retires.

        ⚠️ Decoupe par accolades depuis la colonne 0 — c'est le style du depot
           (`static void f(...)\n{`), ⛔ pas une heuristique de nom.
        """
        nu = sans_commentaires(src)
        corps = []
        for m in re.finditer(r"^[A-Za-z_][^\n;=]*\)\s*\n\{", nu, re.M):
            j, prof, dedans = m.end(), 1, False
            while j < len(nu) and prof:
                c = nu[j]
                if c == '"' and nu[j - 1] != "\\":
                    dedans = not dedans
                elif not dedans and c == "{":
                    prof += 1
                elif not dedans and c == "}":
                    prof -= 1
                j += 1
            f = nu[m.end():j]
            if re.search(r"lv_label_set_text(_fmt)?\s*\(|(?:dn_widget_)?texte\s*\(", f):
                corps.append(f)
        return corps

    def hors_journaux(src):
        """Le source prive de ses commentaires ET de ses appels de JOURNAL.

        ⚠️ On BLANCHIT l'appel entier, ⛔ on ne retire pas seulement le nom :
           les arguments d'un `ESP_LOGW` portent des chaines, et les garder
           ferait rougir tous les fichiers du depot sur des messages qui vont a
           un terminal, ⛔ pas a la dalle.
        """
        nu = sans_commentaires(src)
        out, i = [], 0
        # 🔴 LA GARDE `(?<![A-Za-z0-9_])` N'EST PAS DU ZELE — SANS ELLE, `printf`
        #    MATCHE DANS **`snprintf`**, et le controle blanchissait donc TOUT
        #    LE TEXTE COMPOSE : il ne restait plus rien a inspecter, et il
        #    rendait VERT sur n'importe quoi.
        # ⚠️ C'est le MUTANT 9 qui l'a dit, ⛔ pas une relecture. Une gate qu'on
        #    n'a pas vue rougir ne prouve rien — celle-ci le prouve deux fois :
        #    le mutant a d'abord revele que le controle N'EXISTAIT PAS, puis
        #    qu'il ne MESURAIT RIEN.
        for m in re.finditer(r"(?<![A-Za-z0-9_])"
                             r"(?:ESP_LOG[EWIDV]|printf|ESP_EARLY_LOG[EWIDV])\s*\(",
                             nu):
            if m.start() < i:
                continue
            out.append(nu[i:m.start()])
            prof, j, dedans = 1, m.end(), False
            while j < len(nu) and prof:
                c = nu[j]
                if c == '"' and nu[j - 1] != "\\":
                    dedans = not dedans
                elif not dedans and c == "(":
                    prof += 1
                elif not dedans and c == ")":
                    prof -= 1
                j += 1
            i = j
        out.append(nu[i:])
        return "".join(out)

    ui9 = M(9, ui, 'snprintf(buf + n, sizeof(buf) - n, "\\n! %s %s (%s)",',
            'snprintf(buf + n, sizeof(buf) - n, "\\n⛔ %s %s (%s)",')
    sales = []
    n_fonc = 0
    for src, nomf in ((ui9, "dn_ui.c"), (widget_c, "dn_widget.c")):
        fs = fonctions_a_label(src)
        n_fonc += len(fs)
        for m in re.finditer(r'"(?:\\.|[^"\\])*"', hors_journaux("\n".join(fs))):
            val = deplier_c(m.group(0))
            for pf in sorted(interface):
                for ch in polices[pf].absents(val):
                    if ch in "\n\t\r":
                        continue
                    sales.append("%s : U+%04X « %s » dans « %s »"
                                 % (nomf, ord(ch), ch, val.strip()[:34]))
    dire(not sales,
         "⛔ aucune chaine COMPOSEE ne porte un glyphe absent (AC4.3)",
         "%d fonction(s) qui posent un label, journaux retires" % n_fonc
         if not sales else "⛔ " + " · ".join(sorted(set(sales))[:2]))

    # 🔴 AC4.4 AMENDE PAR LA MESURE, ET C'EST DECLARE.
    #    La story ecrivait « aucune chaine traduisible ne passe par
    #    dn_font_33/56 ». Or AC1.4 EXIGE les unites dans la table, et les unites
    #    PASSENT par ces polices (`composer()` -> `font_val()`). La propriete
    #    tenable est donc « aucune qui n'y soit RENDABLE ».
    prefixes_veille = ("U_", "P_")
    absents_v = []
    for nom, trads in table.items():
        if not nom.startswith(prefixes_veille):
            continue
        for lg, txt in trads.items():
            for pf in sorted(veille):
                for ch in polices[pf].absents(txt):
                    absents_v.append("DN_T_%s/%s : U+%04X « %s » absent de %s"
                                     % (nom, lg, ord(ch), ch, pf))
    n_v = len([n for n in table if n.startswith(prefixes_veille)])
    dire(not absents_v,
         "⛔ unites et prefixes RENDABLES en police de VEILLE (AC4.4)",
         "%d cle(s) x %d langue(s) confrontees a %s"
         % (n_v, len(langues), ",".join(sorted(veille)))
         if not absents_v else "⛔ " + " · ".join(sorted(set(absents_v))[:2]))

    # ══ 5. LES LARGEURS TIENNENT, DANS LES DEUX LANGUES (AC4.1, AC4.2, AC5.2)
    print("\n── 5. LES LARGEURS TIENNENT DANS LES DEUX LANGUES (AC4) ───────")

    MUTANTS[11] = "allonge un titre de case au-dela de sa place"
    MUTANTS[22] = "RACCOURCIT le titre de la DEMO (desarmerait le temoin dn4-14-2)"
    MUTANTS[12] = "rallonge la ligne d'echec NVS jusqu'au clip"
    MUTANTS[13] = "allonge le titre du MENU jusqu'a mordre le selecteur"

    # ⛔ LA GEOMETRIE EST RELUE DU FIRMWARE, ⛔ pas recitee.
    # ⚠️ L'ORDRE COMPTE : chaque `#define` peut en citer un precedent, et
    #    `defini()` ne resout que ce qu'il connait deja. C'est DELIBERE — une
    #    resolution recursive aurait pu boucler en silence sur une definition
    #    circulaire ; ici elle rend None, et la gate le DIT.
    pins = lire(os.path.join(MAIN, "dn_pins.h"))
    g = {}
    for nom, src in (("DN_LCD_H_RES", pins),
                     ("W_PAD", widget_c), ("W_BADGE_DE_DROITE", widget_c),
                     ("W_ICONE_AV_28", widget_c), ("W_ICONE_AV_14", widget_c),
                     ("DN_UI_MARGE", ui), ("DN_UI_GAP", ui),
                     ("DN_UI_RETOUR_W", ui), ("DN_UI_BARRE_DATE_X", ui),
                     ("MENU_SEL_W", ui), ("MENU_SEL_X0", ui), ("MENU_LBL_X", ui),
                     ("MENU_PAN_W", ui), ("MENU_LG_W", ui),
                     ("MENU_TITRE_W_MAX", ui), ("MENU_ENTETE_H", ui)):
        g[nom] = defini(src, nom, g)
    manque = [k for k, v in g.items() if v is None]
    dire(not manque, "toute la geometrie est RELUE du firmware",
         "%d `#define` relus" % len(g) if not manque
         else "⛔ introuvable(s) : " + ", ".join(manque))
    if manque:
        print("\n" + "=" * 78)
        print("BILAN : %d OK, %d KO" % (OK[0], KO[0]))
        print("=" * 78)
        return 1

    case_w = (g["DN_LCD_H_RES"] - 2 * g["DN_UI_MARGE"] - g["DN_UI_GAP"]) // 2
    menu_txt_utile = g["MENU_PAN_W"] - 2 * g["MENU_SEL_X0"]

    # Les emplacements, chacun avec sa police RELUE et sa place CALCULEE.
    # (cle_prefixe, police, largeur utile, comment on l'a calculee)
    p14, p18, p28 = polices["dn_font_14"], polices["dn_font_18"], polices["dn_font_28"]
    titre_utile = (case_w - g["W_BADGE_DE_DROITE"]) - (g["W_PAD"] + g["W_ICONE_AV_28"])
    date_utile = g["DN_LCD_H_RES"] - g["DN_UI_BARRE_DATE_X"] - g["DN_UI_MARGE"]
    cible_utile = g["MENU_SEL_W"] - g["MENU_LBL_X"] - g["MENU_SEL_X0"]
    lg_utile = g["MENU_LG_W"] - g["MENU_LBL_X"]

    table_m = dict((k, dict(v)) for k, v in table.items())
    if _MUTANT == 11:
        table_m["CASE_RESEAU"]["EN"] = "NETWORK INTERFACE"
    if _MUTANT == 13:
        table_m["MENU_TITRE"]["EN"] = "MENU AND SETTINGS"
    if _MUTANT == 22:
        table_m["CASE_DEMO"] = {lg: "DEMO" for lg in langues}

    #
    # ⛔ `CASE_DEMO` EST EXCLU DE CE CONTROLE, ET C'EST UN TEMOIN, ⛔ PAS UNE
    #    EXEMPTION. Il a son propre controle juste apres — a l'ENVERS.
    HORS_TIENT = {"CASE_DEMO"}
    #
    # ⛔ ET UN **ECART DEJA DECLARE**, ⛔ pas une exemption de confort :
    #    « HEURE NON POSEE » fait 184 px pour 170 utiles et sera CLIPPEE. Ce
    #    conflit a ete POSE A L'OWNER le 2026-08-30 avec ses quatre leviers
    #    (accepter la coupe · redescendre a 16 · deplacer x=300 · bouger
    #    BARRE_H, qui perimerait TOUTE coordonnee tactile publiee), et le
    #    verdict a ete **accepter la coupe** — parce que le PCF85063A a sa
    #    retention (bit OS relu au boot), donc cet etat est TRANSITOIRE.
    # ⚠️ L'ecart porte sur **UNE** langue. Le controle juste apres verifie que
    #    les AUTRES tiennent : une 3e langue verbeuse serait un ecart NEUF, et
    #    un ecart neuf se DECIDE, ⛔ il ne s'herite pas.
    ECART_DATE = ("DATE_INCONNUE", "FR")
    EMPL = [
        ("CASE_", p18, titre_utile, "titre de case (dn_font_18, icone 28)"),
        ("JOUR_", p18, None, None),   # traites en couple avec les mois
        ("MENU_VEILLE", p14, menu_txt_utile, "titre de panneau MENU"),
        ("MENU_DELAI", p14, menu_txt_utile, "titre de panneau MENU"),
        ("MENU_LUM", p14, menu_txt_utile, "titre de panneau MENU"),
        ("MENU_ON", p28, cible_utile, "libelle de cible MENU"),
        ("MENU_OFF", p28, cible_utile, "libelle de cible MENU"),
        ("MENU_AUTO", p28, cible_utile, "libelle de cible MENU"),
        ("MENU_NON_CHOISI", p28, cible_utile, "libelle de cible MENU"),
        ("ET_", p14, menu_txt_utile, "ligne d'etat MENU"),
        ("DATE_INCONNUE", p18, date_utile, "date de barre"),
        ("BADGE_SIMULE", p14, g["W_BADGE_DE_DROITE"], "badge de case"),
    ]
    trop = []
    n_mesures = 0
    for pref, police, utile, quoi in EMPL:
        if utile is None:
            continue
        for nom, trads in table_m.items():
            if not (nom == pref or (pref.endswith("_") and nom.startswith(pref))):
                continue
            if nom in HORS_TIENT:
                continue
            for lg, txt in trads.items():
                if (nom, lg) == ECART_DATE:
                    continue  # ECART DECLARE — voir le controle dedie plus bas
                w = police.largeur_multiligne(txt)
                n_mesures += 1
                if w > utile:
                    trop.append("DN_T_%s/%s : %d px pour %d utiles (%s)"
                                % (nom, lg, w, utile, quoi))
    dire(not trop,
         "chaque libelle tient dans sa place, DANS LES DEUX LANGUES",
         "%d mesure(s), largeurs recalculees depuis les `adv_w`" % n_mesures
         if not trop else "⛔ " + " · ".join(trop[:2]))

    #
    # ══════════════════════════════════════════════════════════════════════
    # 🔴 LE TITRE DE LA DEMO DOIT **DEBORDER** — C'EST LE TEMOIN DE `dn4-14-2`
    # ══════════════════════════════════════════════════════════════════════
    #
    # ⛔ CE N'EST PAS UN DEFAUT A REPARER, et le confondre avec un defaut serait
    #    DESARMER une garde. `dn4-14-2` a pose le controle de largeur du titre
    #    (`s_trop_larges++` dans `dn_widget_creer`) et s'est servie de
    #    « DEMO 2+JAUGE » comme du **plus long titre EXISTANT** — celui qui
    #    EXERCE la garde. `dn_ui_case_titre()` l'inclut dans le balayage
    #    justement pour ca, *« sans etre recite nulle part »*.
    # ⇒ Si quelqu'un le RACCOURCIT pour faire taire une gate, le temoin de
    #   `dn4-14-2` cesse d'exister et **plus rien n'exerce le controle**. Ce
    #   controle-ci refuse ce raccourcissement.
    #
    # 🔴 FAIT NEUF, MESURE LE 2026-09-01 PAR CETTE GATE, ET IL VAUT D'ETRE ECRIT :
    #    `dn4-14-2` avait chiffre **114 px pour 107 utiles**, soit **7 px** de
    #    debordement. Ce nombre etait exact — **en `dn_font_14`**, la police de
    #    titre de l'epoque. Le **verdict owner du 2026-08-30** a fait passer
    #    `font_titre` a `dn_font_18` (`dn_widget.c`), et le debordement est
    #    passe a **147 px pour 107**, soit **40 px** — ⛔ personne ne l'a
    #    re-mesure. Le chiffre du dossier a donc VIEILLI en silence, ce qui est
    #    exactement la classe de defaut que ce depot traque.
    # ⚠️ Le controle porte sur le FAIT (« il deborde »), ⛔ pas sur le nombre :
    #    coder 40 ici le re-perimerait au prochain changement de police.
    demo_w = [(lg, p18.largeur(table_m["CASE_DEMO"][lg])) for lg in langues]
    dire(all(w > titre_utile for _, w in demo_w),
         "le titre de la DEMO DEBORDE encore — TEMOIN de dn4-14-2",
         " · ".join("%s = %d px" % (l, w) for l, w in demo_w)
         + " / %d utiles ⇒ ⛔ le raccourcir DESARMERAIT la garde" % titre_utile)

    #
    # ══════════════════════════════════════════════════════════════════════
    # 🔴 L'ECART DE LA DATE INCONNUE EST **UNIQUE**, ET IL RESTE CELUI DE 2026-08-30
    # ══════════════════════════════════════════════════════════════════════
    #
    # Deux proprietes, ⛔ pas une :
    #   (a) l'ecart EXISTE ENCORE — s'il disparaissait, le commentaire du
    #       firmware qui le declare serait devenu FAUX, et un commentaire faux
    #       est un defaut au meme titre qu'un chiffre faux ;
    #   (b) il est **SEUL** — toute autre langue doit TENIR. C'est ce qui fait
    #       qu'ajouter une langue ne peut pas hériter d'une coupe en silence.
    MUTANTS[23] = "allonge la date inconnue d'une AUTRE langue (2e ecart en silence)"
    di = dict(table_m["DATE_INCONNUE"])
    if _MUTANT == 23:
        di["EN"] = "THE CLOCK HAS NOT BEEN SET YET"
    dates_inc = [(lg, p18.largeur(di[lg])) for lg in langues]
    ecart_lg, ecart_w = ECART_DATE[1], dict(dates_inc)[ECART_DATE[1]]
    autres_deb = [(l, w) for l, w in dates_inc if l != ecart_lg and w > date_utile]
    dire(ecart_w > date_utile and not autres_deb,
         "l'ecart de la date inconnue est UNIQUE et c'est celui de 2026-08-30",
         " · ".join("%s = %d px%s" % (l, w, " ⚠️ ECART DECLARE" if l == ecart_lg
                                      else " ✅")
                    for l, w in dates_inc) + " / %d utiles" % date_utile)

    # 🔴 LA DATE COMPLETE — ⛔ pas ses jetons isoles. C'est « VEN. 06 SEPT. »
    #    qui est dessine, et un jour + un mois qui tiennent SEPARES peuvent
    #    deborder ENSEMBLE. Le pire cas est balaye : 7 x 12.
    pires = []
    for lg in langues:
        pire, pire_txt = 0, ""
        for j in [k for k in table_m if k.startswith("JOUR_")]:
            for mo in [k for k in table_m if k.startswith("MOIS_")]:
                t = "%s 06 %s" % (table_m[j][lg], table_m[mo][lg])
                w = p18.largeur(t)
                if w > pire:
                    pire, pire_txt = w, t
        pires.append((lg, pire, pire_txt))
    deb_date = [x for x in pires if x[1] > date_utile]
    dire(not deb_date,
         "la DATE COMPLETE tient (7 x 12 balayes par langue)",
         " · ".join("%s : « %s » = %d px / %d" % (l, t, w, date_utile)
                    for l, w, t in pires)
         if not deb_date else "⛔ " + str(deb_date[0]))

    # 🔴 LA LIGNE D'ECHEC NVS, RECOMPOSEE DANS SON PIRE CAS (AC4.2)
    #    ⛔ Ce n'est pas une chaine de la table : c'est un ASSEMBLAGE. La gate
    #    le refait avec le plus long code d'erreur NVS de l'IDF et le plus long
    #    nom de reglage, DANS LES DEUX LANGUES.
    nvs_fmt = M(12, '! %s %s (%s)', '! %s %s (%s)',
                '! « %s » %s (%s) : perdu au reboot / lost on reboot.')
    nvs_trop = []
    for lg in langues:
        quoi = max((table_m[k][lg] for k in table_m if k.startswith("NVS_")),
                   key=len)
        ligne = nvs_fmt % (quoi, table_m["ET_NON_ENR"][lg], NVS_ERR_PIRE)
        w = p14.largeur(ligne)
        if w > menu_txt_utile:
            nvs_trop.append("%s : « %s » = %d px pour %d" % (lg, ligne, w,
                                                             menu_txt_utile))
    dire(not nvs_trop,
         "la ligne d'echec NVS tient DANS SON PIRE CAS (AC4.2)",
         "pire code = `%s` (%d signes)" % (NVS_ERR_PIRE, len(NVS_ERR_PIRE))
         if not nvs_trop else "⛔ " + " · ".join(nvs_trop))

    # 🔴 LE TITRE DU MENU CONTRE LE SELECTEUR DE LANGUE (AC2.2)
    #    Le `_Static_assert` du firmware garde `MENU_TITRE_W_MAX` ; ici on
    #    verifie que ce chiffre est VRAI dans les deux langues.
    t_menu = [(lg, p28.largeur(table_m["MENU_TITRE"][lg])) for lg in langues]
    dire(all(w <= g["MENU_TITRE_W_MAX"] for _, w in t_menu),
         "le titre « MENU » tient sous `MENU_TITRE_W_MAX` (AC2.2)",
         " · ".join("%s = %d px" % (l, w) for l, w in t_menu)
         + " / %d annonces" % g["MENU_TITRE_W_MAX"])

    lg_codes = re.findall(r'\[DN_LANGUE_(\w+)\]\s*=\s*"([^"]+)"', langue_c)
    trop_code = [(l, c, p28.largeur(c)) for l, c in lg_codes
                 if p28.largeur(c) > lg_utile]
    dire(not trop_code, "les codes du selecteur tiennent dans leur cible",
         " · ".join("%s=%dpx" % (c, p28.largeur(c)) for _, c in lg_codes)
         + " / %d utiles" % lg_utile)

    # ══ 6. LE SELECTEUR NE SE TRADUIT PAS (AC2.4) ═══════════════════════════
    print("\n── 6. LE SELECTEUR NE SE TRADUIT PAS (AC2.4) ──────────────────")

    MUTANTS[14] = "fait passer le libelle du selecteur par `dn_t()`"
    ui14 = M(14, ui, "dn_langue_code((dn_langue_t)i), on_menu_langue_clic,",
             "dn_t(DN_T_MENU_TITRE), on_menu_langue_clic,")
    m_sel = re.search(r"s_menu_lg\[i\]\s*=\s*menu_sel_creer\((.*?)\);",
                      sans_commentaires(ui14), re.S)
    dire(bool(m_sel) and "dn_langue_code(" in m_sel.group(1)
         and "dn_t(" not in m_sel.group(1),
         "⛔ le libelle du selecteur passe par `dn_langue_code()` (AC2.4)",
         "⇒ « FR » / « EN », ⛔ pas un mot traduit")

    # ══ 7. LES UNITES CONCORDENT DES DEUX COTES (AC1.4) ═════════════════════
    print("\n── 7. LES UNITES CONCORDENT DES DEUX COTES (AC1.4) ────────────")

    MUTANTS[15] = "fait diverger une unite entre dn_link.c et la table"

    link15 = M(15, link, '{"%", "GHz", "%", "degC"}', '{"%", "GHz", "%", "deg"}')
    #
    # 🔴 **PREMISSE D'AC1.4 AMENDEE PAR LA MESURE, ET C'EST DECLARE.**
    #    La story dit « les deux cotes lisent la meme » en supposant que les
    #    deux ALIMENTENT LA DALLE. **Faux, mesure le 2026-09-01** :
    #    `dn_link_metrique_unite()` n'a **qu'un seul consommateur**,
    #    `dn_console.c` — c'est-a-dire la CONSOLE, que l'owner garde en
    #    francais. Les unites de `dn_link.c` ne sont JAMAIS dessinees.
    #    ⇒ La propriete tenable n'est pas « la meme chaine » mais
    #      **« elles ne peuvent pas diverger en silence »** : pour chaque
    #      grandeur, l'unite du FIL doit correspondre a la colonne FRANCAISE de
    #      la cle que la CASE emploie.
    # ⚠️ UNE EXCEPTION, MESUREE ET DECLAREE : `degC` (fil) vs `°C` (dalle). Elle
    #    PREEXISTE — le fil est ASCII par construction — et la corriger
    #    changerait une sortie de console hors perimetre.
    EXCEPTIONS = {("degC", "°C")}
    conso = len(re.findall(r"dn_link_metrique_unite\s*\(", sans_commentaires(console)))
    conso_ui = len(re.findall(r"dn_link_metrique_unite\s*\(", sans_commentaires(ui)))
    dire(conso >= 1 and conso_ui == 0,
         "`dn_link_metrique_unite()` ne sert QUE la console",
         "%d appel(s) dans dn_console.c · %d dans dn_ui.c ⇒ ⛔ jamais dessinee"
         % (conso, conso_ui))

    # cote FIL
    fil = {}
    for m in re.finditer(r"\[DN_LINK_M_(\w+)\]\s*=\s*\{[^{]*\{[^}]*\}\s*,\s*\{([^}]*)\}",
                         sans_commentaires(link15), re.S):
        fil[m.group(1)] = [deplier_c(x) for x in re.findall(r'"[^"]*"', m.group(2))]
    # cote CASE : la cle d'unite de chaque grandeur, dans l'ordre
    ui_nu = sans_commentaires(ui)
    casem = {}
    for m in re.finditer(r"\[DN_UI_CASE_(\w+)\]\s*=\s*\{(.*?)\n    \},", ui_nu, re.S):
        gr = re.search(r"\.grandeurs\s*=\s*\{(.*)", m.group(2), re.S)
        if gr:
            casem[m.group(1)] = re.findall(r"\.unite\s*=\s*(DN_T_\w+)", gr.group(1))
    # la correspondance case -> metrique de fil, RELUE de `k_source[]`
    src2m = dict(re.findall(r"\[DN_UI_CASE_(\w+)\]\s*=\s*\{DN_SRC_LIEN_PC,"
                            r"\s*DN_LINK_M_(\w+),", ui_nu))
    div = []
    n_conf = 0
    for case, met in src2m.items():
        for i, cle in enumerate(casem.get(case, [])):
            if met not in fil or i >= len(fil[met]):
                continue
            nom = cle[len("DN_T_"):]
            attendu = table.get(nom, {}).get("FR")
            recu = fil[met][i]
            n_conf += 1
            if attendu is None or (recu != attendu and (recu, attendu) not in EXCEPTIONS):
                div.append("%s[%d] : fil « %s » vs table FR « %s »"
                           % (case, i, recu, attendu))
    dire(n_conf > 0 and not div,
         "les unites du FIL collent a la colonne FR de la table (AC1.4)",
         "%d grandeur(s) confrontee(s) · %d exception(s) declaree(s)"
         % (n_conf, len(EXCEPTIONS)) if not div else "⛔ " + " · ".join(div[:2]))

    # ══ 8. LA CONSOLE RESTE EN FRANCAIS (decision owner) ════════════════════
    print("\n── 8. LA CONSOLE RESTE EN FRANCAIS (decision owner) ───────────")

    MUTANTS[16] = "fait lire `dn_t()` (langue courante) a la console"
    console16 = M(16, console, "dn_t_fr(dm ? dm->grandeurs[0].unite : DN_T_AUCUN)",
                  "dn_t(dm ? dm->grandeurs[0].unite : DN_T_AUCUN)")
    #
    # ⚠️ `dn_t_fr(` CONTIENT `dn_t(` — on cherche donc `dn_t(` **precede d'un
    #    non-identifiant et non suivi de `_fr`**, sinon le controle serait
    #    toujours rouge. Piege trouve en ecrivant cette gate.
    fautifs = [m.start() for m in
               re.finditer(r"(?<![A-Za-z0-9_])dn_t\s*\(", sans_commentaires(console16))]
    dire(not fautifs,
         "⛔ `dn_console.c` n'appelle JAMAIS `dn_t()` (langue courante)",
         "⇒ il lit `dn_t_fr()` : MEME definition, FRANCAIS constant"
         if not fautifs else "⛔ %d appel(s) a `dn_t(`" % len(fautifs))

    MUTANTS[17] = "fait citer `dn_t()` par un ESP_LOG de dn_ui.c"
    ui17 = M(17, ui, 'ESP_LOGI(TAG, "langue : « %s » posee AU DOIGT depuis le MENU (scene "\n                  "reconstruite).",\n             dn_langue_code(l));',
             'ESP_LOGI(TAG, "langue : « %s » posee AU DOIGT depuis le MENU (scene "\n                  "reconstruite).",\n             dn_t(DN_T_MENU_TITRE));')
    logs = []
    for m in re.finditer(r"ESP_LOG[EWIDV]\s*\(", sans_commentaires(ui17)):
        reste = sans_commentaires(ui17)[m.end():m.end() + 900]
        prof, j, dedans = 1, 0, False
        while j < len(reste) and prof:
            c = reste[j]
            if c == '"' and (j == 0 or reste[j - 1] != "\\"):
                dedans = not dedans
            elif not dedans and c == "(":
                prof += 1
            elif not dedans and c == ")":
                prof -= 1
            j += 1
        appel = reste[:j]
        if re.search(r"(?<![A-Za-z0-9_])dn_t\s*\(", appel):
            logs.append(appel[:60].replace("\n", " "))
    dire(not logs,
         "⛔ aucun `ESP_LOG` de dn_ui.c ne cite `dn_t()`",
         "⇒ les journaux restent francais : `dn_t_fr()`, `case_nom_fr()`"
         if not logs else "⛔ " + logs[0])

    # ══ 9. LE REPEINT NE RECONSTRUIT PAS DEPUIS UN CALLBACK (AC3.4) ═════════
    print("\n── 9. AUCUNE RECONSTRUCTION DEPUIS UN CALLBACK (AC3.4) ────────")

    MUTANTS[18] = "appelle `build_scene()` DIRECTEMENT depuis le tap de langue"
    ui18 = M(18, ui, "    if (lv_async_call(langue_async, (void *)(intptr_t)l) != LV_RESULT_OK) {",
             "    build_scene();\n    if (lv_async_call(langue_async, (void *)(intptr_t)l) != LV_RESULT_OK) {")
    cb = re.search(r"static void on_menu_langue_clic\(lv_event_t \*e\)\s*\{(.*?)\n\}",
                   sans_commentaires(ui18), re.S)
    dire(bool(cb) and "build_scene(" not in cb.group(1)
         and "lv_async_call(" in cb.group(1),
         "⛔ le tap de langue passe par `lv_async_call` (AC3.4)",
         "⇒ ⛔ pas de `build_scene()` dans le callback : use-after-free de dn1-3")

    # Et le retour de l'async est TESTE — sinon un tap refuse passerait pour pris.
    MUTANTS[19] = "jette le retour de `lv_async_call` du tap de langue"
    ui19 = M(19, ui, "if (lv_async_call(langue_async, (void *)(intptr_t)l) != LV_RESULT_OK) {",
             "if (false) {\n        lv_async_call(langue_async, (void *)(intptr_t)l);")
    cb19 = re.search(r"static void on_menu_langue_clic\(lv_event_t \*e\)\s*\{(.*?)\n\}",
                     sans_commentaires(ui19), re.S)
    dire(bool(cb19) and "!= LV_RESULT_OK" in cb19.group(1),
         "le retour de `lv_async_call` est TESTE",
         "⇒ sur file pleine : ⛔ RIEN n'est change, et ca se DIT")

    # ══ 10. LE MENU EST GARDE EN LARGEUR A CHAUD (AC4.2) ════════════════════
    print("\n── 10. LE MENU EST GARDE EN LARGEUR A CHAUD (AC4.2) ───────────")

    MUTANTS[20] = "retire le controle de largeur du bloc d'etat du MENU"
    ui20 = M(20, ui, 'menu_largeur_controler("etat", buf, &dn_font_14, MENU_TXT_UTILE);',
             "/* retire */")
    ui20_nu = sans_commentaires(ui20)
    n_ctrl = len(re.findall(r"menu_largeur_controler\s*\(", ui20_nu))
    dire(n_ctrl >= 3,
         "les libelles du MENU sont MESURES a chaud",
         "%d site(s) : titres de panneau + bloc d'etat compose" % n_ctrl)

    MUTANTS[21] = "cesse de publier le compteur du MENU dans la console"
    console21 = M(21, console, "dn_ui_menu_trop_larges()", "0u")
    dire("dn_ui_menu_trop_larges()" in sans_commentaires(console21),
         "le compteur du MENU est PUBLIE par la console",
         "⇒ `dn4-41` : un instrument qu'on ne peut pas LIRE ne disculpe personne")

    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (OK[0], KO[0]))
    print("=" * 78)
    return 0 if KO[0] == 0 else 1


sys.exit(main())

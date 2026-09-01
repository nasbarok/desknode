#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn_police — LIT les polices LVGL du depot et RECALCULE ce que la dalle dessine.

⛔ CE N'EST PAS UNE GATE. Le glob de `run_gates.sh` est `tools/verif_*.py` ;
   ce fichier est une BIBLIOTHEQUE, importee par `tools/verif_langues_dn442.py`.

════════════════════════════════════════════════════════════════════════════
🔴 POURQUOI CE MODULE EXISTE, ET POURQUOI IL NE RECITE RIEN
════════════════════════════════════════════════════════════════════════════

Deux questions se posent a chaque chaine affichee, et AUCUNE des deux ne se
repond de memoire :

  1. « la police porte-t-elle CE glyphe ? »  Un glyphe absent est dessine par
     LVGL comme un PLACEHOLDER (`LV_USE_FONT_PLACEHOLDER=y` dans le sdkconfig)
     — c'est-a-dire une boite, sans un mot dans le journal. C'est ce qui a fait
     perdre son `U` a « AOUT » avec les built-ins.
  2. « la chaine tient-elle dans sa place ? »  Un texte trop large est CLIPPE
     par LVGL, sans un mot non plus.

⇒ Les deux se calculent DEPUIS LES TABLES DU `.c`, ⛔ jamais depuis une liste
  ecrite a la main : une liste se perime au premier `gen_font_dn.py`.

════════════════════════════════════════════════════════════════════════════
🔴 LA LARGEUR EST CELLE DU FIRMWARE, ⛔ PAS `somme(adv_w)/16`
════════════════════════════════════════════════════════════════════════════

⚠️ ECART MESURE LE 2026-09-01, ET IL COMPTE : le cadrage de `dn4-42` publie des
   largeurs a la decimale (« AMBIANCE = 102,4 px »). Cette forme trahit un
   `somme(adv_w) / 16`. **Ce n'est pas ce que LVGL calcule.**

   `lv_font_fmt_txt.c:244-251` (version vendue au depot) :

       kv    = (kvalue * kern_scale) >> 4        <- kerning PAR PAIRE
       adv_w = (gdsc->adv_w + kv + 8) >> 4       <- ARRONDI, PAR GLYPHE

   puis `lv_text_get_width()` (`misc/lv_text.c:455-459`) SOMME ces entiers.

   ⇒ l'arrondi est PAR GLYPHE, ⛔ pas sur la somme, et le KERNING y entre.
     Deux mots de meme somme brute peuvent donc differer d'un pixel ou deux.

⚠️ ET LE KERNING EST ACTIF. `dn_font_*.c` ne renseigne PAS `.kerning` dans son
   initialiseur ⇒ zero ⇒ `LV_FONT_KERNING_NORMAL` (c'est la valeur 0 de l'enum,
   `lv_font.h:89-92`). Le lire « non renseigne donc desactive » serait faux.

════════════════════════════════════════════════════════════════════════════
"""

import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(RACINE, "firmware", "desknode", "main", "fonts")

# ── Les motifs de lecture du `.c` ───────────────────────────────────────────
# ⚠️ ANCRES PAR MOTIF, ⛔ pas par numero de ligne : `gen_font_dn.py` reordonne.

_RE_CMAP = re.compile(
    r"\.range_start\s*=\s*(\d+)\s*,\s*"
    r"\.range_length\s*=\s*(\d+)\s*,\s*"
    r"\.glyph_id_start\s*=\s*(\d+)\s*,\s*"
    r"\.unicode_list\s*=\s*(NULL|unicode_list_\d+)\s*,\s*"
    r"\.glyph_id_ofs_list\s*=\s*(NULL|glyph_id_ofs_list_\d+)\s*,\s*"
    r"\.list_length\s*=\s*(\d+)\s*,\s*"
    r"\.type\s*=\s*(LV_FONT_FMT_TXT_CMAP_\w+)",
    re.S,
)
_RE_GLYPH = re.compile(
    r"\{\s*\.bitmap_index\s*=\s*\d+\s*,\s*\.adv_w\s*=\s*(\d+)\s*,", re.S)
_RE_TABLEAU_U16 = r"static const uint16_t %s\[\]\s*=\s*\{(.*?)\};"
_RE_TABLEAU_I8 = r"static const int8_t %s\[\]\s*=\s*\{(.*?)\};"
_RE_TABLEAU_U8 = r"static const uint8_t %s\[\]\s*=\s*\{(.*?)\};"
_RE_KERN_CLASSES = re.compile(
    r"kern_classes\s*=\s*\{(.*?)\};", re.S)
_RE_LINE_H = re.compile(r"\.line_height\s*=\s*(\d+)")
_RE_KERN_SCALE = re.compile(r"\.kern_scale\s*=\s*(\d+)")


_RE_JETON = re.compile(r"0[xX][0-9a-fA-F]+|-?\d+")


def _nombres(bloc):
    """Les entiers d'un initialiseur C — HEXA COMPRIS.

    ⛔ Un `\\d+` nu decoupe `0xd004` en « 0 » et « 004 » : la liste sparse de
       `dn_font_14` rendait alors 142 entrees pour `list_length = 67`, et un
       controle de coherence l'a attrape. Le motif hexa passe D'ABORD.
    """
    return [int(x, 0) for x in _RE_JETON.findall(bloc)]


class Police(object):
    """Une police LVGL du depot, RELUE de son `.c`.

    ⛔ Aucun champ n'est ecrit a la main ici : tout vient du fichier.
    """

    def __init__(self, nom, chemin=None):
        self.nom = nom
        self.chemin = chemin or os.path.join(FONTS, nom + ".c")
        if not os.path.exists(self.chemin):
            raise IOError("police introuvable : %s" % self.chemin)
        with open(self.chemin, "r", encoding="utf-8") as fh:
            src = fh.read()
        self._src = src

        m = _RE_LINE_H.search(src)
        if not m:
            raise ValueError("%s : `.line_height` introuvable — le gabarit de "
                             "`gen_font_dn.py` a change." % nom)
        self.line_height = int(m.group(1))

        m = _RE_KERN_SCALE.search(src)
        self.kern_scale = int(m.group(1)) if m else 16

        # ── adv_w bruts, indexes par glyph id ──────────────────────────────
        self.adv_w = [int(x) for x in _RE_GLYPH.findall(src)]
        if len(self.adv_w) < 2:
            raise ValueError("%s : `glyph_dsc[]` illisible." % nom)

        # ── cmaps : codepoint -> glyph id ──────────────────────────────────
        self.gid = {}
        n_cmaps = 0
        for (start, length, gid0, ul, ofs, ll, typ) in _RE_CMAP.findall(src):
            n_cmaps += 1
            start, length, gid0, ll = int(start), int(length), int(gid0), int(ll)
            if ul == "NULL":
                # cmap DENSE : `range_start` .. `range_start + range_length`
                for i in range(length):
                    self.gid[start + i] = gid0 + i
            else:
                mm = re.search(_RE_TABLEAU_U16 % re.escape(ul), src, re.S)
                if not mm:
                    raise ValueError("%s : cmap sparse reference `%s`, "
                                     "introuvable." % (nom, ul))
                liste = _nombres(mm.group(1))
                if len(liste) != ll:
                    raise ValueError(
                        "%s : `%s` porte %d entrees pour `list_length = %d`."
                        % (nom, ul, len(liste), ll))
                if ofs != "NULL":
                    mo = re.search(_RE_TABLEAU_U8 % re.escape(ofs), src, re.S)
                    if not mo:
                        raise ValueError("%s : `%s` introuvable." % (nom, ofs))
                    offs = _nombres(mo.group(1))
                else:
                    offs = None
                for i, e in enumerate(liste):
                    # ⚠️ Les entrees d'une cmap SPARSE sont des OFFSETS depuis
                    #    `range_start`, ⛔ pas des codepoints absolus.
                    self.gid[start + e] = gid0 + (offs[i] if offs else i)
        if not n_cmaps:
            raise ValueError("%s : aucune cmap reconnue." % nom)
        self.n_cmaps = n_cmaps

        # ── kerning par CLASSES ────────────────────────────────────────────
        self._kern = None
        mk = _RE_KERN_CLASSES.search(src)
        if mk:
            bloc = mk.group(1)
            noms = dict(re.findall(r"\.(\w+)\s*=\s*(\w+)", bloc))
            cnt = dict((k, int(v)) for k, v in
                       re.findall(r"\.(\w+_class_cnt)\s*=\s*(\d+)", bloc))
            try:
                mv = re.search(_RE_TABLEAU_I8 % re.escape(noms["class_pair_values"]), src, re.S)
                ml = re.search(_RE_TABLEAU_U8 % re.escape(noms["left_class_mapping"]), src, re.S)
                mr = re.search(_RE_TABLEAU_U8 % re.escape(noms["right_class_mapping"]), src, re.S)
                self._kern = {
                    "values": _nombres(mv.group(1)),
                    "left": _nombres(ml.group(1)),
                    "right": _nombres(mr.group(1)),
                    "right_cnt": cnt["right_class_cnt"],
                }
            except (KeyError, AttributeError):
                self._kern = None  # kern_pairs, ⛔ pas de classes : sans kerning

    # ── L'API ──────────────────────────────────────────────────────────────

    def porte(self, cp):
        """Le codepoint est-il REELLEMENT dans une cmap ?"""
        return cp in self.gid

    def absents(self, texte):
        """Les codepoints de `texte` que cette police NE PORTE PAS.

        ⛔ Rendre une liste, pas un booleen : le message d'une gate doit NOMMER
           le glyphe fautif, sinon l'auteur cherche a l'oeil dans 11 000 lignes.
        """
        return [c for c in texte if not self.porte(ord(c))]

    def _kv(self, g, gn):
        if self._kern is None or not g or not gn:
            return 0
        k = self._kern
        if g >= len(k["left"]) or gn >= len(k["right"]):
            return 0
        lc, rc = k["left"][g], k["right"][gn]
        if lc > 0 and rc > 0:
            i = (lc - 1) * k["right_cnt"] + (rc - 1)
            if 0 <= i < len(k["values"]):
                return k["values"][i]
        return 0

    def largeur(self, texte, letter_space=0):
        """La largeur EXACTE que `dn_widget_largeur()` mesurerait, en px.

        Reproduit `lv_text_get_width()` + `lv_font_get_glyph_dsc_fmt_txt()` :
        arrondi PAR GLYPHE, kerning inclus, `letter_space` retire sur le
        dernier. Un glyphe ABSENT compte pour le PLACEHOLDER que LVGL dessine
        (`line_height / 2 + 2` px) — voir le corps.
        ⚠️ Une largeur qui TIENT ne dit donc RIEN sur la lisibilite :
           `absents()` doit etre appelee AUSSI. Une boite qui remplace un glyphe
           est aussi fausse qu'un texte clippe, et elle, elle tient.
        """
        w = 0
        cps = [ord(c) for c in texte]
        for i, cp in enumerate(cps):
            g = self.gid.get(cp)
            if not g:
                # 🔴 UN GLYPHE ABSENT N'EST PAS DE LARGEUR NULLE.
                #    `LV_USE_FONT_PLACEHOLDER=y` (sdkconfig) ⇒ LVGL rend un dsc
                #    de SUBSTITUTION (`src/font/lv_font.c`, branche finale) :
                #        box_w = line_height / 2 ; adv_w = box_w + 2
                #    ⚠️ Ce `adv_w`-la est DEJA EN PIXELS, ⛔ pas en 1/16 : il ne
                #       passe PAS par le `>> 4`. Le modeliser a zero aurait fait
                #       passer pour ETROITE une chaine pleine de boites.
                w += (self.line_height // 2 + 2) + letter_space
                continue
            gn = self.gid.get(cps[i + 1]) if i + 1 < len(cps) else 0
            kv = (self._kv(g, gn) * self.kern_scale) >> 4
            aw = (self.adv_w[g] + kv + 8) >> 4
            if aw > 0:
                w += aw + letter_space
        if w > 0:
            w -= letter_space
        return w

    def largeur_multiligne(self, texte, letter_space=0):
        """La plus large des lignes de `texte` (separateur `\\n`)."""
        return max([self.largeur(l, letter_space) for l in texte.split("\n")] or [0])


_CACHE = {}


def police(nom):
    if nom not in _CACHE:
        _CACHE[nom] = Police(nom)
    return _CACHE[nom]


def toutes():
    """Toutes les `dn_font_*.c` du depot — DECOUVERTES, ⛔ pas enumerees."""
    out = {}
    for f in sorted(os.listdir(FONTS)):
        m = re.match(r"^(dn_font_\d+)\.c$", f)
        if m:
            out[m.group(1)] = police(m.group(1))
    return out


if __name__ == "__main__":
    # Un mode « dis-moi » : ⛔ pas une gate, un instrument de cadrage.
    ps = toutes()
    for nom, p in ps.items():
        plages = sorted(p.gid)
        print("%-12s  %4d codepoints · %d cmaps · lh %2d · min %d max %d"
              % (nom, len(p.gid), p.n_cmaps, p.line_height, plages[0], plages[-1]))
    for mot in sys.argv[1:]:
        print("── « %s » ──" % mot)
        for nom, p in ps.items():
            abs_ = p.absents(mot)
            print("   %-12s %4d px%s" % (
                nom, p.largeur(mot),
                "   ⛔ ABSENTS : " + " ".join("U+%04X %s" % (ord(c), c) for c in abs_)
                if abs_ else ""))

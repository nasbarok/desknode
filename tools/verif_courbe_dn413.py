#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-13 / AC4 (+ AC8.2) — LES INVARIANTS DE LA COURBE, RELUS DANS LE SOURCE,
JOUABLES DEPUIS WSL SANS CARTE.

======================= CE QUE CET OUTIL EST, ET CE QU'IL N'EST PAS =========

⛔ IL NE PROUVE PAS QUE L'ÉCRAN EST JUSTE. Aucune ligne ici ne dessine quoi que
   ce soit. AC4.6 exige un CONSTAT OWNER À L'ŒIL sur `RÉSEAU` et `AMBIANCE`, et
   le témoin d'AC4.3 (`nav open 0` → `nav open 3` → `widget courbe`) se joue SUR
   LA CARTE. ⇒ Cette gate est un PRÉ-VOL : elle interdit de payer un build, un
   flash et une fenêtre d'observation pour une faute qui se voit dans le source.

⚠️ ET ELLE EST PLUS FAIBLE QUE `verif_hist_dn413.py`, QUI, LUI, **EXÉCUTE** LE
   PRODUIT. La différence est écrite ici pour que personne ne les croie de même
   force : `dn_ui.c` ne se compile pas sur l'hôte (LVGL, esp_*, dn_widget,
   dn_link), donc les invariants de la courbe se relisent au lieu de se jouer.
   ⛔ Ne pas conclure « AC4 est soldé » depuis un vert d'ici.

🔴 CHAQUE CONTRÔLE EST MUTÉ. Pour chaque invariant, on FABRIQUE la version
   fautive (celle d'avant le correctif, ou une négation minimale) et on exige de
   VOIR la gate rougir. Un contrôle qu'aucune mutation n'a fait échouer ne prouve
   rien — c'est la famille exacte que cette story solde (AC7.5).

Sortie : exit 0 si tout passe, 1 sinon. Publie le sha256 des sources LUES.
"""

import hashlib
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(RACINE, "firmware", "desknode", "main")
DN_UI_C = os.path.join(MAIN, "dn_ui.c")
DN_UI_H = os.path.join(MAIN, "dn_ui.h")
DN_HIST_C = os.path.join(MAIN, "dn_hist.c")

ok_total = [0]
ko_total = [0]


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


def decommenter(txt):
    """Retire commentaires et chaînes EN PRÉSERVANT LES LIGNES.
    ⛔ Indispensable : ce dépôt CITE du code dans ses commentaires (« `bornee` en
       `n == 2` »), et un parseur naïf conclurait que la branche existe encore."""
    def blanchir(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    txt = re.sub(r"/\*.*?\*/", blanchir, txt, flags=re.S)
    txt = re.sub(r"//[^\n]*", blanchir, txt)
    txt = re.sub(r'"(?:\\.|[^"\\\n])*"', blanchir, txt)
    return txt


def corps(code, entete):
    """Le corps `{...}` de la DÉFINITION dont la signature commence par `entete`.

    🔴 ⛔ ON SAUTE LES DÉCLARATIONS AVANCÉES. `dn_ui.c` en porte (`static void
       detail_reparametrer(int idx);` l. 2683) : prendre la première occurrence
       renvoyait le corps d'une AUTRE fonction, et la gate concluait « le libellé
       n'est pas posé » sur un fichier où il l'était. Un instrument qui lit au
       mauvais endroit fabrique un rouge PLAUSIBLE — la pire espèce, et
       exactement ce que cette story solde ailleurs."""
    dep = 0
    while True:
        i = code.find(entete, dep)
        if i < 0:
            return None
        dep = i + 1
        j = i + len(entete)
        while j < len(code) and code[j] not in "{;":
            j += 1
        if j >= len(code) or code[j] == ";":
            continue  # déclaration avancée
        prof, k = 0, j
        while k < len(code):
            if code[k] == "{":
                prof += 1
            elif code[k] == "}":
                prof -= 1
                if prof == 0:
                    return code[j:k + 1]
            k += 1
        return None


# ═══════════════════════════════════════════════════════════════════════════
# LES INVARIANTS — chacun est une fonction (code_ui, code_hist) -> (ok, detail)
# ═══════════════════════════════════════════════════════════════════════════
def i_axe_pose_remis(ui, hist):
    """AC4.3 — `s_axe_pose[0]` ET `[1]` remis à FAUX en TÊTE de
    `courbe_reparametrer()`, ⛔ avant toute pose."""
    b = corps(ui, "static void courbe_reparametrer(int idx)")
    if b is None:
        return False, "fonction introuvable"
    i0 = b.find("s_axe_pose[0] = false;")
    i1 = b.find("s_axe_pose[1] = false;")
    ipose = b.find("courbe_axe_poser")
    if i0 < 0 or i1 < 0:
        return False, "un des deux drapeaux n'est pas remis a faux"
    if ipose >= 0 and (i0 > ipose or i1 > ipose):
        return False, "remise a faux APRES une pose d'axe"
    return True, "les deux, avant toute pose"


def i_axes_exposent(ui, hist):
    """AC4.3 — `dn_ui_detail_courbe_axes()` REND les drapeaux."""
    b = corps(ui, "bool dn_ui_detail_courbe_axes(")
    if b is None:
        return False, "fonction introuvable"
    sig_i = ui.find("bool dn_ui_detail_courbe_axes(")
    sig = ui[sig_i:ui.find("{", sig_i)]
    if "pose0" not in sig or "pose1" not in sig:
        return False, "la signature ne porte pas les drapeaux"
    if "*pose0 = s_axe_pose[0]" not in b or "*pose1 = s_axe_pose[1]" not in b:
        return False, "les drapeaux ne sont pas AFFECTES depuis l'etat"
    return True, "signature + affectation"


def i_partage_par_les_donnees(ui, hist):
    """AC4.2 — le partage en moitiés est décidé par `dn_hist_reels()`,
    ⛔ pas par `n == 2` seul."""
    b = corps(ui, "static void courbe_reparametrer(int idx)")
    if b is None:
        return False, "fonction introuvable"
    m = re.search(r"deux_vivantes\s*=\s*\(([^;]*)\)\s*;", b, re.S)
    if not m:
        return False, "`deux_vivantes` introuvable"
    cond = m.group(1)
    if "dn_hist_reels" not in cond:
        return False, "le partage ne consulte pas `dn_hist_reels`"
    if cond.count("dn_hist_reels") < 2:
        return False, "une seule serie est consultee : le partage reste unilateral"
    for a in ("deux_vivantes ? 0 : -1", "deux_vivantes ? 1 : -1"):
        if a not in b:
            return False, "la moitie n'est pas conditionnee (%s)" % a
    return True, "les DEUX series consultees"


def i_echelle_commune(ui, hist):
    """AC4.1 — l'échelle commune existe, elle vise `RÉSEAU`, ET ELLE SEULE.

    ⚠️ Croisé avec `dn_hist.c` : les pages à deux séries y sont `k_s1[]`. Une
       échelle commune posée sur une page mono-courbe serait sans effet ; posée
       sur `AMBIANCE` (°C et %) elle serait un non-sens arithmetique."""
    b = corps(ui, "static bool courbe_echelle_commune(int idx)")
    if b is None:
        return False, "fonction introuvable"
    if "DN_UI_CASE_RESEAU" not in b:
        return False, "`RESEAU` n'est pas la page a echelle commune"
    autres = [c for c in re.findall(r"DN_UI_CASE_[A-Z]+", b)
              if c != "DN_UI_CASE_RESEAU"]
    if autres:
        return False, "d'autres pages sont visees : %s" % sorted(set(autres))
    rb = corps(ui, "static void courbe_reparametrer(int idx)")
    if "courbe_echelle_commune" not in (rb or ""):
        return False, "elle n'est pas CONSULTEE par `courbe_reparametrer`"
    if "courbe_plage_commune" not in (rb or ""):
        return False, "aucune plage commune n'est calculee"
    # les deux axes reçoivent la MÊME plage : une seule paire de variables
    if "a0 = a1 = mn;" not in rb or "b0 = b1 = mx;" not in rb:
        return False, "les deux axes ne recoivent pas la MEME plage"
    if "p0 = p1 = true;" not in rb:
        return False, "les deux drapeaux ne sont pas poses ensemble"
    if "courbe_axe_poser(LV_CHART_AXIS_PRIMARY_Y, a0, b0)" not in rb or \
       "courbe_axe_poser(LV_CHART_AXIS_SECONDARY_Y, a1, b1)" not in rb:
        return False, "la pose n'utilise pas les plages calculees"
    return True, "RESEAU seul, deux axes, une plage"


def i_bornee_retiree(ui, hist):
    """AC8.2 — la branche morte `bornee` du cas `n == 2` a disparu."""
    b = corps(ui, "static void courbe_reparametrer(int idx)")
    if b is None:
        return False, "fonction introuvable"
    if "k_courbe_borne" in b or re.search(r"\bbornee\b", b):
        return False, "`bornee` / `k_courbe_borne` survit dans la fonction"
    sb = corps(ui, "static bool courbe_serie_plage(")
    if sb is None:
        return False, "`courbe_serie_plage` introuvable"
    if "k_courbe_borne" not in sb:
        return False, "la borne a disparu AUSSI des pages mono-courbe (regression)"
    return True, "retiree ici, CONSERVEE la ou elle sert"


def i_minmax_nomme_sa_serie(ui, hist):
    """AC4.4 — le MIN/MAX dit de quelle série il parle, et `hs1` est RELU."""
    b = corps(ui, "static void minmax_porte(")
    if b is None:
        return False, "`minmax_porte` introuvable"
    if "nser < 2" not in b:
        return False, "le libelle ne se tait pas sur une page mono-courbe"
    d = corps(ui, "static void detail_reparametrer(int idx)")
    if d is None:
        return False, "`detail_reparametrer` introuvable"
    if "minmax_porte(" not in d:
        return False, "le libelle n'est pas pose sur la page"
    if "minmax_long_union(hs0, hs1" not in d:
        return False, "`hs1` n'est toujours pas RELU (le defaut d'origine)"
    return True, "libelle derive + `hs1` consomme"


def i_marqueur_temperature(ui, hist):
    """AC4.5 — une grandeur qui a une couleur de courbe MAIS pas d'icône porte
    quand même sa couleur."""
    d = corps(ui, "static void detail_reparametrer(int idx)")
    if d is None:
        return False, "fonction introuvable"
    if "seg_colore" not in d:
        return False, "aucun marqueur pour la grandeur sans icone"
    m = re.search(r"seg_colore\s*=\s*([^;]*);", d)
    if not m:
        return False, "condition introuvable"
    cond = m.group(1)
    if "cc" not in cond or "ic" not in cond:
        return False, "la condition ne croise pas couleur ET icone : %s" % cond
    if "ouvre" not in d or "ferme" not in d:
        return False, "la balise n'est pas emise"
    return True, "segment entier recolore quand `cc && !ic`"


def i_pas_de_symbole_en_font14(ui, hist):
    """Le libellé d'AC4.4 vit en `dn_font_14` : ⛔ aucun `LV_SYMBOL_*` dedans.
    Un codepoint absent de la police serait dessiné en carré vide EN SILENCE."""
    brut, _ = lire(DN_UI_C)
    i = brut.find("static void minmax_porte(")
    j = brut.find("\n}\n", i)
    if i < 0 or j < 0:
        return False, "fonction introuvable"
    seg = brut[i:j]
    if "LV_SYMBOL" in seg:
        return False, "un LV_SYMBOL_* est ecrit dans un libelle en font 14"
    return True, "aucun glyphe FontAwesome dans la ligne d'etat"


def i_invalidation_conditionnee(ui, hist):
    """AC5.1 — l'invalidation est conditionnée au CHANGEMENT, et la condition
    se joue AVANT le premier appel LVGL.

    🔴 L'ORDRE EST LE CŒUR DU CORRECTIF. En LVGL 9, `lv_chart_set_range()`,
       `_set_series_color()`, `_set_x_start_point()` et `_hide_series()`
       invalident TOUTES l'objet. Poser d'abord puis « décider si on
       rafraîchit » aurait payé le redessin qu'on cherche à éviter — le
       correctif aurait été DÉCORATIF. Cette gate le vérifie par les POSITIONS,
       ⛔ pas par la présence du `memcmp`."""
    b = corps(ui, "static void courbe_reparametrer(int idx)")
    if b is None:
        return False, "fonction introuvable"
    i_cmp = b.find("memcmp(&sig, &s_courbe_sig")
    if i_cmp < 0:
        return False, "aucune comparaison de signature"
    if "return;" not in b[i_cmp:i_cmp + 200]:
        return False, "la comparaison ne COURT-CIRCUITE pas"
    premiers = [b.find(x) for x in ("lv_chart_set_range", "lv_chart_set_series_color",
                                    "lv_chart_set_x_start_point",
                                    "lv_chart_hide_series",
                                    "lv_chart_set_series_ext_y_array",
                                    "lv_chart_refresh", "lv_obj_invalidate",
                                    "courbe_axe_poser")]
    premiers = [x for x in premiers if x >= 0]
    if not premiers:
        return False, "aucun appel LVGL : la fonction ne dessine plus rien ?"
    if min(premiers) < i_cmp:
        return False, "un appel LVGL PRECEDE la comparaison (correctif decoratif)"
    return True, "court-circuit avant les %d appels LVGL" % len(premiers)


def i_signature_couvre_les_donnees(ui, hist):
    """AC5.1 — la signature contient `debut`, seul témoin d'une écriture.

    ⚠️ Elle ne hache PAS les 120 points. C'est légitime SEULEMENT parce que les
       deux seuls écrivains de `s_pts[][]` avancent `s_w[]` à chaque écriture.
       Cette gate vérifie les DEUX bouts : `deb0`/`deb1` dans la signature ICI,
       et dans `dn_hist.c` qu'aucune écriture de `s_pts` n'oublie d'avancer
       `s_w`. ⛔ Sans le second, le premier serait une supposition."""
    b = corps(ui, "static void courbe_reparametrer(int idx)")
    if b is None:
        return False, "fonction introuvable"
    for champ in ("sig.deb0", "sig.deb1", "sig.idx", "sig.a0", "sig.p0",
                  "sig.coul0", "sig.chart"):
        if champ not in b:
            return False, "la signature n'inclut pas `%s`" % champ
    # ⛔ Le CHAMP ne suffit pas : il doit VENIR de l'historique. Un `sig.deb0 = 0`
    #    porterait le nom sans porter l'information — une signature decorative.
    for champ in ("deb0", "deb1"):
        m = re.search(r"sig\.%s\s*=\s*([^;]*);" % champ, b)
        if not m or "dn_hist_debut" not in m.group(1):
            return False, "`sig.%s` ne vient pas de `dn_hist_debut()`" % champ
    if "memset(&sig, 0, sizeof(sig))" not in b:
        return False, "le bourrage n'est pas remis a zero avant le memcmp"
    # l'autre bout : toute ecriture de s_pts avance s_w
    ecritures = re.findall(r"s_pts\[[^\]]+\]\[s_w\[[^\]]+\]\]\s*=", hist)
    avances = re.findall(r"s_w\[[^\]]+\]\s*=\s*\(s_w\[[^\]]+\]\s*\+\s*1u?\)", hist)
    if not ecritures:
        return False, "aucune ecriture de `s_pts` trouvee dans dn_hist.c"
    if len(avances) < len(ecritures):
        return False, ("%d ecriture(s) de `s_pts` pour %d avance(s) de `s_w` : "
                       "une ecriture peut passer sous le radar"
                       % (len(ecritures), len(avances)))
    return True, "%d ecriture(s), %d avance(s) de `s_w`" % (len(ecritures),
                                                            len(avances))


def i_compteurs_du_gain(ui, hist):
    """AC5.3 — le gain se CHIFFRE, et le compteur est REMISABLE À ZÉRO.
    ⛔ Un compteur cumulatif ne peut pas servir de témoin rejouable : c'est la
       leçon que `s_gardeh_cris` a coûtée à `dn4-4`."""
    b = corps(ui, "static void courbe_reparametrer(int idx)")
    if "s_courbe_appels++" not in (b or ""):
        return False, "les demandes ne sont pas comptees"
    if "s_courbe_redessins++" not in (b or ""):
        return False, "les redessins reels ne sont pas comptes"
    i_a = b.find("s_courbe_appels++")
    i_cmp = b.find("memcmp(&sig, &s_courbe_sig")
    i_r = b.find("s_courbe_redessins++")
    if not (i_a < i_cmp < i_r):
        return False, "les deux compteurs ne sont pas de part et d'autre du test"
    r = corps(ui, "void dn_ui_reset_compteurs(void)")
    if "s_courbe_appels = 0" not in (r or "") or \
       "s_courbe_redessins = 0" not in (r or ""):
        return False, "les compteurs ne sont pas remis a zero (temoin non rejouable)"
    return True, "comptes de part et d'autre, et remisables"


def i_ironie_levee(ui, hist):
    """AC5.2 — l'ironie de `dn_hist.h` est LEVÉE PAR ÉCRIT, ⛔ pas effacée."""
    brut, _ = lire(os.path.join(MAIN, "dn_hist.h"))
    if "le plus chaud de la vue détail" not in brut:
        return False, "le paragraphe d'origine a ete EFFACE (ce depot n'efface pas)"
    if "dn4-13" not in brut or "L'IRONIE" not in brut:
        return False, "l'ironie n'est pas nommee et datee dans `dn_hist.h`"
    if "courbe_reparametrer" not in brut:
        return False, "le paragraphe ne nomme pas le chemin qui dessinait"
    return True, "paragraphe CONSERVE et amende"


INVARIANTS = [
    ("AC4.3 `s_axe_pose[0..1]` remis a FAUX en tete", i_axe_pose_remis,
     [("    s_axe_pose[0] = false;\n    s_axe_pose[1] = false;\n\n"
       "    /* La série 0 : SON tableau, SA couleur",
       "\n    /* La série 0 : SON tableau, SA couleur")]),
    ("AC4.3 les drapeaux SORTENT de `..._courbe_axes`", i_axes_exposent,
     [("if (pose0) { *pose0 = s_axe_pose[0]; }", "if (pose0) { *pose0 = true; }")]),
    ("AC4.2 le partage est decide par les DONNEES", i_partage_par_les_donnees,
     [("dn_hist_reels(s0) > 0 && dn_hist_reels(s1) > 0", "true"),
      ("dn_hist_reels(s1) > 0", "true")]),
    ("AC4.1 echelle commune : RESEAU, et lui seul", i_echelle_commune,
     [("return idx == DN_UI_CASE_RESEAU;",
       "return idx == DN_UI_CASE_RESEAU || idx == DN_UI_CASE_AMB;"),
      ("            a0 = a1 = mn;\n            b0 = b1 = mx;",
       "            a0 = mn;\n            b0 = mx;")]),
    ("AC8.2 la branche morte `bornee` a disparu", i_bornee_retiree,
     [("bool commune = (n == 2 && courbe_echelle_commune(idx));",
       "bool bornee = k_courbe_borne[idx].actif;\n"
       "    bool commune = (n == 2 && courbe_echelle_commune(idx));")]),
    ("AC4.4 le MIN/MAX nomme sa serie, `hs1` est relu",
     i_minmax_nomme_sa_serie,
     [("minmax_long_union(hs0, hs1", "minmax_long_union(hs0, hs0"),
      ("if (nser < 2) {", "if (nser < 0) {")]),
    ("AC4.5 la temperature d'AMBIANCE porte sa couleur",
     i_marqueur_temperature,
     [("bool seg_colore = (cc != 0u) && (ic == NULL);",
       "bool seg_colore = false;")]),
    ("⛔ aucun LV_SYMBOL_* dans le libelle en font 14",
     i_pas_de_symbole_en_font14, []),
    ("AC5.1 l'invalidation est CONDITIONNEE, et testee AVANT",
     i_invalidation_conditionnee,
     [("if (s_courbe_sig_valide && memcmp(&sig, &s_courbe_sig, sizeof(sig)) == 0) {",
       "if (false) {"),
      ("    s_courbe_appels++;\n",
       "    s_courbe_appels++;\n    lv_chart_refresh(s_det_courbe);\n")]),
    ("AC5.1 la signature couvre les DONNEES (les 2 bouts)",
     i_signature_couvre_les_donnees,
     [("sig.deb0 = (s0 >= 0) ? dn_hist_debut(s0) : 0u;", "sig.deb0 = 0u;"),
      ("memset(&sig, 0, sizeof(sig));", "")]),
    ("AC5.3 le gain se CHIFFRE, et le compteur se remet a zero",
     i_compteurs_du_gain,
     [("    s_courbe_redessins++;\n", ""),
      ("    s_courbe_appels = 0;\n", "")]),
    ("AC5.2 l'ironie de dn_hist.h est LEVEE PAR ECRIT", i_ironie_levee, []),
]


def main():
    ui_brut, sha_ui = lire(DN_UI_C)
    hist_brut, sha_h = lire(DN_HIST_C)
    _, sha_hdr = lire(DN_UI_H)
    print("=" * 78)
    print("dn4-13 / AC4 — LES INVARIANTS DE LA COURBE (PRÉ-VOL, ⛔ pas l'écran)")
    print("=" * 78)
    print("  dn_ui.c   sha256[:16] = %s" % sha_ui)
    print("  dn_ui.h   sha256[:16] = %s" % sha_hdr)
    print("  dn_hist.c sha256[:16] = %s" % sha_h)

    ui = decommenter(ui_brut)
    hist = decommenter(hist_brut)

    print("\n── LES INVARIANTS ─────────────────────────────────────────────────")
    for nom, f, _mut in INVARIANTS:
        ok, det = f(ui, hist)
        ctrl(ok, nom, det)

    print("\n── 🔴 TÉMOIN NÉGATIF — chaque invariant est MUTÉ et doit ROUGIR ────")
    n_mut = 0
    for nom, f, muts in INVARIANTS:
        if not muts:
            print("  [--] %-56s %s" % (nom, "aucune mutation (contrôle textuel)"))
            continue
        for avant, apres in muts:
            if ui_brut.count(avant) < 1:
                ctrl(False, "mutation applicable : %s" % nom,
                     "motif absent : %.50s" % avant.replace("\n", " "))
                continue
            mut_brut = ui_brut.replace(avant, apres, 1)
            ok, det = f(decommenter(mut_brut), hist)
            n_mut += 1
            ctrl(not ok, "muté ⇒ ROUGE : %s" % nom,
                 "«%.40s» → «%.20s»" % (avant.replace("\n", " "),
                                        apres.replace("\n", " ")))
    ctrl(n_mut >= 8, "le témoin a joué assez de mutations",
         "%d mutations" % n_mut)

    print("\n" + "=" * 78)
    print("⚠️ CE QUE CETTE GATE NE SOLDE PAS :")
    print("   · AC4.6 — le CONSTAT OWNER À L'ŒIL sur `RÉSEAU` et `AMBIANCE` ;")
    print("   · le témoin d'AC4.3 sur la carte (`nav open 0` → `nav open 3`")
    print("     avant toute trame `net` → `widget courbe`) ;")
    print("   · le PRIX de la décision n°5 (le montant écrasé en trait plat),")
    print("     qui est ACQUIS et ne se mesure qu'à l'écran.")
    if ko_total[0] == 0:
        print("✅ %d contrôles passent, 0 échec." % ok_total[0])
        return 0
    print("⛔ %d ÉCHEC(S) sur %d contrôles."
          % (ko_total[0], ok_total[0] + ko_total[0]))
    return 1


if __name__ == "__main__":
    sys.exit(main())

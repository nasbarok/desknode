#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-13 / AC4 + AC5 + AC6 (+ AC8.2) — LES INVARIANTS DE LA COURBE **ET DES
INSTRUMENTS**, RELUS DANS LE SOURCE, JOUABLES DEPUIS WSL SANS CARTE.

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


def decommenter(txt, chaines=False):
    """Retire les commentaires EN PRÉSERVANT LES LIGNES.

    ⛔ Indispensable : ce dépôt CITE du code dans ses commentaires (« `bornee` en
       `n == 2` »), et un parseur naïf conclurait que la branche existe encore.
    `chaines=True` GARDE les littéraux : il en faut pour reconnaître un
    `strcmp(argv[1], "jauge")` ou un `#include "..."`. ⚠️ Les blanchir par défaut
    reste le bon choix — sinon un `printf("k_courbe_borne")` compterait comme du
    code."""
    def blanchir(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    txt = re.sub(r"/\*.*?\*/", blanchir, txt, flags=re.S)
    txt = re.sub(r"//[^\n]*", blanchir, txt)
    if not chaines:
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
def i_axe_pose_remis(S):
    ui = S["ui"]
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


def i_axes_exposent(S):
    ui = S["ui"]
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


def i_partage_par_les_donnees(S):
    ui = S["ui"]
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


def i_echelle_commune(S):
    ui = S["ui"]
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


def i_bornee_retiree(S):
    ui = S["ui"]
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


def i_minmax_nomme_sa_serie(S):
    ui = S["ui"]
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


def i_marqueur_temperature(S):
    """AC4.5 — INVARIANT **STRUCTUREL** : sur une page à DEUX courbes, chaque
    grandeur tracée PORTE UNE ICÔNE.

    🔴 CET INVARIANT A REMPLACÉ LE PRÉCÉDENT, ET LA RAISON EST UN CONSTAT OWNER.
       La première version recolorait LE SEGMENT ENTIER quand une grandeur avait
       une couleur de courbe sans icône. Ça marchait, la gate le prouvait — et
       **l'owner n'en a pas voulu** (2026-08-25) : *« remettre le texte blanc
       avec l'icône temp devant le chiffre »*. Le correctif n'était pas dans le
       rendu, il était dans le DESCRIPTEUR.
    ⇒ On ne vérifie plus une branche conditionnelle : on vérifie que la
      situation qui la rendait nécessaire NE PEUT PLUS EXISTER. Une grandeur
      sans icône sur une page à deux courbes n'a AUCUN moyen de porter sa
      couleur — c'est ça, le défaut, et il se ferme dans `k_desc[]`."""
    ui = S["ui_str"]   # ⚠️ chaînes CONSERVÉES : les icônes sont des littéraux
    # les pages à deux courbes viennent de `k_s1[]`, dans dn_hist.c
    hist = S["hist"]
    m = re.search(r"k_s1\[6\]\s*=\s*\{([^}]*)\}", hist, re.S)
    if not m:
        return False, "`k_s1[]` introuvable dans dn_hist.c"
    entrees = [x.strip() for x in m.group(1).split(",") if x.strip()]
    deux = [i for i, e in enumerate(entrees) if not e.startswith("-")]
    if not deux:
        return False, "aucune page a deux courbes : `k_s1[]` est vide ?"
    # ⇒ pour chacune, les grandeurs 0 et 1 de `k_desc[]` doivent avoir `.icone`
    noms = {3: "DN_UI_CASE_RESEAU", 5: "DN_UI_CASE_AMB"}
    manque = []
    for idx in deux:
        cle = noms.get(idx)
        if cle is None:
            manque.append("case %d (nom inconnu de la gate)" % idx)
            continue
        i = ui.find("[%s] = {" % cle)
        if i < 0:
            return False, "descripteur %s introuvable" % cle
        j = ui.find(".grandeurs", i)
        k = ui.find("}},", j)
        if j < 0 or k < 0:
            return False, "grandeurs de %s introuvables" % cle
        bloc = ui[j:k + 3]
        # deux entrées `{...}` : chacune doit porter `.icone`
        parts = re.findall(r"\{([^{}]*)\}", bloc)
        if len(parts) < 2:
            return False, "%s n'expose pas deux grandeurs" % cle
        for g in (0, 1):
            if ".icone" not in parts[g]:
                manque.append("%s grandeur %d" % (cle, g))
    if manque:
        return False, "sans icone, donc sans couleur possible : %s" % ", ".join(manque)
    # et le rendu colore bien l'icone quand la couleur existe
    d = corps(S["ui"], "static void detail_reparametrer(int idx)")
    if d is None or 'if (ic && cc)' not in d:
        return False, "le rendu ne colore pas l'icone"
    if "seg_colore" in (d or ""):
        return False, "le recolorage du SEGMENT survit (l'owner l'a refuse)"
    return True, "%d page(s) a 2 courbes, 2 icones chacune" % len(deux)


def i_pas_de_symbole_en_font14(S):
    """Le libellé d'AC4.4 vit en `dn_font_14` : ⛔ aucun `LV_SYMBOL_*` dedans.
    Un codepoint absent de la police serait dessiné en carré vide EN SILENCE."""
    brut = S["ui_brut"]
    i = brut.find("static void minmax_porte(")
    j = brut.find("\n}\n", i)
    if i < 0 or j < 0:
        return False, "fonction introuvable"
    seg = brut[i:j]
    if "LV_SYMBOL" in seg:
        return False, "un LV_SYMBOL_* est ecrit dans un libelle en font 14"
    return True, "aucun glyphe FontAwesome dans la ligne d'etat"


def i_invalidation_conditionnee(S):
    ui = S["ui"]
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


def i_signature_couvre_les_donnees(S):
    ui, hist = S["ui"], S["hist"]
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


def i_compteurs_du_gain(S):
    ui = S["ui"]
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


def i_ironie_levee(S):
    """AC5.2 — l'ironie de `dn_hist.h` est LEVÉE PAR ÉCRIT, ⛔ pas effacée."""
    brut = S["histh_brut"]
    if "le plus chaud de la vue détail" not in brut:
        return False, "le paragraphe d'origine a ete EFFACE (ce depot n'efface pas)"
    if "dn4-13" not in brut or "L'IRONIE" not in brut:
        return False, "l'ironie n'est pas nommee et datee dans `dn_hist.h`"
    if "courbe_reparametrer" not in brut:
        return False, "le paragraphe ne nomme pas le chemin qui dessinait"
    return True, "paragraphe CONSERVE et amende"


def i_garde_temoin_rejouable(S):
    ui = S["ui"]
    """AC6.1 — le témoin de la garde est REJOUABLE, et le verdict porte sur le
    DERNIER passage."""
    b = corps(ui, "esp_err_t dn_ui_set_detail_panh(int h)")
    if b is None:
        return False, "`dn_ui_set_detail_panh` introuvable"
    for v in ("s_gardeh_n = 0", "s_gardeh_cris = 0", "s_gardeh_cri = false"):
        if v not in b:
            return False, "`%s` n'est pas remis (temoin non rejouable)" % v
    g = corps(ui, "bool dn_ui_garde_hauteur(")
    if g is None or "*cri_dernier = s_gardeh_cri" not in g:
        return False, "le cri DU DERNIER PASSAGE ne sort pas"
    cons = S["cons"]
    if "ncris == 0" in cons:
        return False, "la console tranche encore sur le CUMUL `ncris`"
    if "!gcri" not in cons:
        return False, "la console ne tranche pas sur le dernier passage"
    return True, "remise a zero + verdict sur le dernier passage"


def i_n_series_lit_l_objet(S):
    ui = S["ui"]
    """AC6.2 — `n_series` LIT `hidden`, il ne récite plus la table."""
    b = corps(ui, "bool dn_ui_detail_courbe_axes(")
    if b is None:
        return False, "fonction introuvable"
    m = re.search(r"if \(n_series\) \{(.*?)\n    \}", b, re.S)
    if not m:
        return False, "bloc `n_series` introuvable"
    bloc = m.group(1)
    if "dn_hist_series_de_case" in bloc:
        return False, "il RECITE encore la table"
    if "->hidden" not in bloc:
        return False, "il ne lit pas l'etat POSE (`hidden`)"
    # ⛔ SUR LE TEXTE DÉCOMMENTÉ. `dn_ui.c` NOMME `lv_chart_private.h` dans un
    #    commentaire vingt lignes plus haut : chercher dans le brut aurait rendu
    #    ce contrôle immunisé au retrait de l'`#include`. Trouvé par son propre
    #    témoin, et c'est exactement le piège que cette gate documente en tête.
    if "lv_chart_private.h" not in S["ui_str"]:
        return False, "l'en-tete prive du chart n'est pas inclus"
    return True, "lu de `lv_chart_series_t::hidden`"


def i_jauge_demo_refuse(S):
    """AC6.4 — `widget jauge <DN_UI_METRIQUES>` refuse la formule de case."""
    cons = S["cons_str"]
    i = cons.find('strcmp(argv[1], "jauge")')
    if i < 0:
        return False, "commande `widget jauge` introuvable"
    seg = cons[i:i + 4000]
    j = seg.find("dn_ui_case_rect")
    if j < 0:
        return False, "la formule de case a disparu AUSSI des vraies cases"
    garde = seg.find("idx >= DN_UI_METRIQUES")
    if garde < 0 or garde > j:
        return False, "aucune garde ne precede l'appel a la formule de case"
    return True, "la demo est ecartee AVANT la formule"


def i_detpan_borne(S):
    ui = S["ui"]
    """AC6.5 — `widget detpan` est borné à 262 − 95, et le nombre est DÉRIVÉ."""
    if "#define DET_PANH_MAX (262 - 95)" not in S["ui_brut"]:
        return False, "la borne n'est pas DERIVEE des deux ordonnees"
    b = corps(ui, "esp_err_t dn_ui_set_detail_panh(int h)")
    if b is None:
        return False, "fonction introuvable"
    if "h > DET_PANH_MAX" not in b:
        return False, "la borne n'est pas appliquee"
    if re.search(r"h\s*>\s*200", b):
        return False, "l'ancienne borne 200 survit"
    cons = S["cons_brut"]
    if "40..200" in cons:
        return False, "la console annonce encore `40..200` (usage FAUX)"
    if "40..167" not in cons:
        return False, "la console n'annonce pas la nouvelle plage"
    return True, "167 derive, applique, ET annonce par la console"


def i_connue_un_seul_predicat(S):
    """AC8.1 — « connue » est défini UNE FOIS et lu par la tuile ET l'historique.

    ⛔ Le défaut n'était pas que la garde soit morte — elle ne l'est pas
       (`dn_ui_cpu_maj()` pose `-1`). Le défaut est qu'elle ne s'appliquait qu'à
       UNE des deux surfaces : la tuile aurait affiché « −3,0 °C » pendant que la
       courbe creusait un trou et que MIN/MAX disait « -- »."""
    ui = S["ui"]
    b = corps(ui, "bool dn_ui_pc_maj(")
    if b is None:
        return False, "`dn_ui_pc_maj` introuvable"
    if "bool connues[DN_WIDGET_GRANDEURS_MAX];" not in b:
        return False, "aucun predicat unique `connues[]`"
    m = re.search(r"connues\[i\]\s*=\s*([^;]*);", b)
    if not m or "vue->v[i] >= 0" not in m.group(1):
        return False, "le predicat ne porte pas le test `>= 0`"
    # la tuile lit `connues[]`, ⛔ plus `vue->connue[i]` nu
    tuile = re.search(r"for \(int i = 0; i < n_aff; i\+\+\) \{(.*?)\n        \}",
                      b, re.S)
    if not tuile:
        return False, "boucle de formatage de la tuile introuvable"
    if "connues[i]" not in tuile.group(1):
        return False, "la TUILE ne lit pas le predicat commun"
    if "vue->connue[i]" in tuile.group(1):
        return False, "la TUILE lit encore `vue->connue[i]` nu"
    if "val.dx_connue[i] = connues[i];" not in b:
        return False, "l'HISTORIQUE ne lit pas le predicat commun"
    return True, "un predicat, deux surfaces"


def i_fond_trois_etats(S):
    """AC9 — `fond_poser()` a TROIS états, et `fond off` ne pose RIEN.

    ⛔ Le contrôle porte sur l'ORDRE : la sortie anticipée doit précéder le
       calcul de `px`, sinon les deux cas restent écrasés l'un sur l'autre —
       c'était exactement le défaut (`px = !s_fond_on ? NULL : …`)."""
    ui = S["ui"]
    b = corps(ui, "static void fond_poser(lv_obj_t *scr)")
    if b is None:
        return False, "`fond_poser` introuvable"
    if "!s_fond_on ? NULL" in b:
        return False, "les deux etats sont encore ECRASES l'un sur l'autre"
    i_sortie = b.find("if (!s_fond_on) {")
    if i_sortie < 0:
        return False, "aucune sortie anticipee sur `fond off`"
    if "return;" not in b[i_sortie:i_sortie + 120]:
        return False, "la branche `fond off` ne SORT pas"
    i_px = b.find("const uint16_t *px")
    if i_px < 0 or i_px < i_sortie:
        return False, "`px` est calcule AVANT la sortie : les etats restent lies"
    i_noir = b.find("lv_color_black()")
    if i_noir < 0 or i_noir > i_sortie:
        return False, "le noir n'est pas pose AVANT la sortie"
    # ═══════════════════════════════════════════════════════════════════════
    # 🔴 dn4-24 / AC2.2 — CE CONTROLE ETAIT **FAUX**, ⛔ PAS SON MUTANT.
    #
    # Il s'ecrivait `if "ASSET ABSENT" not in S["ui_str"]` — une PRESENCE
    # GLOBALE dans tout `dn_ui.c`. Le mutant du temoin detruit le libelle du
    # panneau (`lv_label_set_text(t, "ASSET ABSENT")` -> `"rien"`), et le
    # controle restait VERT : depuis `d6123c5` (2026-08-28, revue de `dn3-3` —
    # donc AVANT `dn4-14`, ce que le ledger disait), `dn_ui.c` porte un
    # ESP_LOGW dont le TEXTE cite « ASSET ABSENT » pour expliquer une veille
    # sans voile. Un message de diagnostic satisfaisait donc l'invariant du
    # panneau. La gate sortait ROUGE sur SON PROPRE TEMOIN, ⛔ pas sur le code.
    #
    # ⛔ Le controle n'est PAS supprime : il est LOCALISE. La meme famille que
    #    le manifeste de `dn4-16` (un TOTAL satisfait par une ligne fabriquee)
    #    et que `s_trop_larges++` : on cherchait COMBIEN/SI, il faut chercher
    #    OU. Le libelle doit etre pose DANS `fond_poser()`, sur un label, par
    #    un appel — et n'importe quelle autre mention du fichier est desormais
    #    sans effet sur ce verdict.
    # ═══════════════════════════════════════════════════════════════════════
    b_str = corps(S["ui_str"], "static void fond_poser(lv_obj_t *scr)")
    if b_str is None:
        return False, "`fond_poser` introuvable dans la vue a chaines"
    #
    # 🔴 L'ANCRE A CHANGE LE 2026-09-01 (`dn4-42`), ⛔ PAS LA PROPRIETE.
    #    Le libelle du panneau de panne est passe d'un LITTERAL a une CLE de
    #    langue (`dn_t(DN_T_ASSET_ABSENT)`) : « ASSET ABSENT » n'est plus dans
    #    `dn_ui.c`, il est dans `dn_langue.h`. **La decision n°2 — le panneau
    #    est POSE dans `fond_poser` — est intacte**, et c'est elle qu'on garde.
    # ⛔ ON NE CHERCHE PLUS LE TEXTE, ON CHERCHE **LE GESTE** : un
    #    `lv_label_set_text` dans `fond_poser`, sur la cle du panneau de panne.
    #    C'est plus robuste, ⛔ pas plus laxiste : le mutant du temoin remplace
    #    la cle, et le controle rougit.
    if not re.search(r'lv_label_set_text\(\s*\w+\s*,\s*'
                     r'(?:"ASSET ABSENT"|dn_t\w*\(\s*DN_T_ASSET_ABSENT\s*\))\s*\)',
                     b_str):
        return False, ("le libelle ASSET ABSENT n'est plus POSE dans "
                       "`fond_poser` (decision n°2 violee)")
    return True, "noir → sortie → px → 2 branches, libelle POSE dans `fond_poser`"


def i_borne_option2_declaree(S):
    """AC9.4 — le chiffre publié (139,5 ms) est DÉCLARÉ non comparable.

    ⛔ Corriger le code sans marquer le chiffre laisserait un nombre juste-en-
       apparence circuler dans le dossier. Ce dépôt a déjà payé ça (le −3 512 o
       d'AC5.6)."""
    ok_h = "139,5" in S["uih_brut"] or "139.5" in S["uih_brut"]
    ok_c = "139,5" in S["cons_brut"] or "139.5" in S["cons_brut"]
    if not (ok_h and ok_c):
        return False, ("le chiffre n'est pas marque des deux cotes "
                       "(dn_ui.h %s, dn_console.c %s)" % (ok_h, ok_c))
    if "RE-TIRE" not in S["cons_brut"].upper().replace("É", "E"):
        return False, "la console ne dit pas que le chiffre se RE-TIRE"
    return True, "marque dans `dn_ui.h` ET imprime par la console"


# 🔴 dn4-13 / AC10.4 — LES FORMULATIONS QUI INTERDISENT DE RÉPÉTER UNE VALEUR.
#    Chacune doit être QUALIFIÉE : soit elle nomme la source MORTE/PÉRIMÉE (elle
#    est alors scopée, et la règle est inchangée), soit elle nomme l'EXCEPTION du
#    palier. ⛔ Une interdiction nue condamnerait le palier d'`AMBIANCE`, qui est
#    LÉGITIME — et c'est la décision owner n°3.
RE_INTERDIT_PALIER = re.compile(
    r"derni[eè]re valeur connue"
    r"|stabilit[ée] qui n'a pas [ée]t[ée] mesur[ée]e"
    r"|g[eè]lerait"
    r"|jamais une interpolation", re.I)
RE_QUALIFIE = re.compile(
    r"\bMORTE\b|\bmorte\b|\bmeurt\b|P[ÉE]RIM[ÉE]E|perim|"
    r"PALIER|palier|AC10|LENTE|lente|efface", re.I)


def i_regle_du_trou_scindee(S):
    """AC10.1..AC10.4 — la règle est scindée, et AUCUNE formulation n'interdit
    le palier sans nommer soit la source morte, soit l'exception."""
    for cle, nom in (("ui_brut", "dn_ui.c"), ("histh_brut", "dn_hist.h")):
        t = S[cle]
        if "AC10" not in t:
            return False, "%s ne porte pas la règle scindée" % nom
        if "PALIER" not in t.upper():
            return False, "%s ne nomme pas le PALIER" % nom
    # les cadences réelles, ⛔ pas « c'est lent »
    for cle, nom in (("ui_brut", "dn_ui.c"), ("histh_brut", "dn_hist.h")):
        t = S[cle]
        for jeton in ("DN_CAPT_PERIODE_MS", "5 000", "1 Hz", "15 s"):
            if jeton not in t:
                return False, "%s : la cadence « %s » n'est pas écrite" % (nom, jeton)
    # le motif du REFUS de changer le dessin
    if "24 points isolés" not in S["histh_brut"]:
        return False, "dn_hist.h n'écrit pas le motif du refus (24 points isolés)"
    if "LV_CHART_POINT_NONE" not in S["histh_brut"]:
        return False, "le motif ne nomme pas la cause (`LV_CHART_POINT_NONE`)"
    # ── AC10.4 : le balayage ────────────────────────────────────────────────
    nus = []
    for cle, nom in (("ui_brut", "dn_ui.c"), ("histh_brut", "dn_hist.h"),
                     ("hist_brut", "dn_hist.c")):
        lignes = S[cle].split("\n")
        for i, l in enumerate(lignes):
            if not RE_INTERDIT_PALIER.search(l):
                continue
            fenetre = "\n".join(lignes[max(0, i - 25):i + 26])
            if not RE_QUALIFIE.search(fenetre):
                nus.append("%s:%d" % (nom, i + 1))
    if nus:
        return False, "interdiction NUE du palier : %s" % ", ".join(nus)
    return True, "règle scindée, cadences écrites, 0 interdiction nue"


INVARIANTS = [  # (libelle, invariant, [(fichier, avant, apres), ...])
    ("AC4.3 `s_axe_pose[0..1]` remis a FAUX en tete", i_axe_pose_remis,
     [("ui", "    s_axe_pose[0] = false;\n    s_axe_pose[1] = false;\n\n"
       "    /* La série 0 : SON tableau, SA couleur",
       "\n    /* La série 0 : SON tableau, SA couleur")]),
    ("AC4.3 les drapeaux SORTENT de `..._courbe_axes`", i_axes_exposent,
     [("ui", "if (pose0) { *pose0 = s_axe_pose[0]; }",
       "if (pose0) { *pose0 = true; }")]),
    ("AC4.2 le partage est decide par les DONNEES", i_partage_par_les_donnees,
     [("ui", "dn_hist_reels(s0) > 0 && dn_hist_reels(s1) > 0", "true"),
      ("ui", "dn_hist_reels(s1) > 0", "true")]),
    ("AC4.1 echelle commune : RESEAU, et lui seul", i_echelle_commune,
     [("ui", "return idx == DN_UI_CASE_RESEAU;",
       "return idx == DN_UI_CASE_RESEAU || idx == DN_UI_CASE_AMB;"),
      ("ui", "            a0 = a1 = mn;\n            b0 = b1 = mx;",
       "            a0 = mn;\n            b0 = mx;")]),
    ("AC8.2 la branche morte `bornee` a disparu", i_bornee_retiree,
     [("ui", "bool commune = (n == 2 && courbe_echelle_commune(idx));",
       "bool bornee = k_courbe_borne[idx].actif;\n"
       "    bool commune = (n == 2 && courbe_echelle_commune(idx));")]),
    ("AC4.4 le MIN/MAX nomme sa serie, `hs1` est relu",
     i_minmax_nomme_sa_serie,
     [("ui", "minmax_long_union(hs0, hs1", "minmax_long_union(hs0, hs0"),
      ("ui", "if (nser < 2) {", "if (nser < 0) {")]),
    ("AC4.5 la temperature d'AMBIANCE porte sa couleur",
     i_marqueur_temperature,
     # ⛔ LA MUTATION CIBLE LA GRANDEUR, ⛔ PAS LA CASE. `DN_ICONE_THERMOMETER_HALF`
     #    apparait DEUX FOIS dans le descripteur d'AMBIANCE : au niveau de la CASE
     #    (`.icone` du widget) et au niveau de la GRANDEUR 0. La premiere version
     #    de ce temoin retirait la premiere occurrence — celle de la case — et la
     #    gate restait verte A RAISON. Le motif porte donc son ancre.
     # ⚠️ ANCRES REPRISES LE 2026-09-01 (`dn4-42`) : les unites sont passees
     #    de LITTERAUX a des CLES (`DN_T_U_DEGC`, `DN_T_U_MBPS`). ⛔ Le temoin
     #    vise toujours la MEME chose — l'icone de la GRANDEUR, ⛔ pas celle de
     #    la case — et c'est pour ca que l'ancre porte l'unite qui la precede.
     [("ui", 'DN_T_U_DEGC, .icone = DN_ICONE_THERMOMETER_HALF,', 'DN_T_U_DEGC,'),
      ("ui", ".unite = DN_T_U_MBPS, .icone = LV_SYMBOL_UP,",
       ".unite = DN_T_U_MBPS,"),
      ("ui", "if (ic && cc) {", "if (false) {")]),
    ("⛔ aucun LV_SYMBOL_* dans le libelle en font 14",
     i_pas_de_symbole_en_font14, []),
    ("AC5.1 l'invalidation est CONDITIONNEE, et testee AVANT",
     i_invalidation_conditionnee,
     [("ui", "if (s_courbe_sig_valide && memcmp(&sig, &s_courbe_sig, sizeof(sig)) == 0) {",
       "if (false) {"),
      ("ui", "    s_courbe_appels++;\n",
       "    s_courbe_appels++;\n    lv_chart_refresh(s_det_courbe);\n")]),
    ("AC5.1 la signature couvre les DONNEES (les 2 bouts)",
     i_signature_couvre_les_donnees,
     [("ui", "sig.deb0 = (s0 >= 0) ? dn_hist_debut(s0) : 0u;", "sig.deb0 = 0u;"),
      ("ui", "memset(&sig, 0, sizeof(sig));", ""),
      ("hist", "    s_w[serie] = (s_w[serie] + 1u) % DN_HIST_N_POINTS;",
       "    s_w[serie] = s_w[serie];")]),
    ("AC5.3 le gain se CHIFFRE, et le compteur se remet a zero",
     i_compteurs_du_gain,
     [("ui", "    s_courbe_redessins++;\n", ""),
      ("ui", "    s_courbe_appels = 0;\n", "")]),
    ("AC5.2 l'ironie de dn_hist.h est LEVEE PAR ECRIT", i_ironie_levee,
     [("histh", "🔴 **L'IRONIE DE CE PARAGRAPHE", "⚠️ un paragraphe quelconque")]),
    ("AC6.1 le temoin de la garde est REJOUABLE", i_garde_temoin_rejouable,
     [("ui", "    s_gardeh_cris = 0;\n", ""),
      ("ui", "    if (cri_dernier) { *cri_dernier = s_gardeh_cri; }\n", ""),
      ("cons", "} else if (ghl + gyl > ghp && !gcri) {",
       "} else if (ghl + gyl > ghp && ncris == 0) {")]),
    ("AC6.2 `n_series` LIT `hidden`, il ne recite plus",
     i_n_series_lit_l_objet,
     [("ui", "        if (s_det_serie0 && !s_det_serie0->hidden) {\n            n++;\n        }",
       "        n = dn_hist_series_de_case(s_metrique, NULL, NULL);"),
      ("ui", '#include "widgets/chart/lv_chart_private.h"', "")]),
    ("AC6.4 `widget jauge` refuse la formule pour la demo",
     i_jauge_demo_refuse,
     [("cons", "        if (idx >= DN_UI_METRIQUES) {\n", "        if (false) {\n")]),
    ("AC8.1 « connue » : UN predicat, lu par la tuile ET l'historique",
     i_connue_un_seul_predicat,
     [("ui", "connues[i] = ok && (int)vue->n > i && vue->connue[i] && vue->v[i] >= 0;",
       "connues[i] = ok && (int)vue->n > i && vue->connue[i];"),
      ("ui", "            if (connues[i]) {\n                haute[i] = fmt_echelle(",
       "            if (vue->connue[i]) {\n                haute[i] = fmt_echelle(")]),
    ("AC9 `fond_poser()` a TROIS etats, `off` ne pose RIEN",
     i_fond_trois_etats,
     [("ui", "    if (!s_fond_on) {\n        return; /* état 1", "    if (false) {\n        return; /* état 1"),
      # ⚠️ ANCRE REPRISE LE 2026-09-01 (`dn4-42`) : le libelle est une CLE.
      ("ui", 'lv_label_set_text(t, dn_t(DN_T_ASSET_ABSENT));',
       'lv_label_set_text(t, "rien");')]),
    ("AC9.4 les 139,5 ms sont DECLAREES non comparables",
     i_borne_option2_declaree,
     [("cons", "Il se RE-TIRE (dn4-13 / AC11.1)", "On le garde"),
      ("uih", "**139,5 ms**", "un chiffre")]),
    ("AC10 la regle du trou est SCINDEE, 0 interdiction nue",
     i_regle_du_trou_scindee,
     [("histh", "24 points isolés", "quelques points"),
      ("ui", "DN_CAPT_PERIODE_MS` = **5 000 ms**", "un capteur lent"),
      # ⛔ LA MUTATION DOIT POSER L'INTERDICTION **LOIN** DE TOUTE
      #    QUALIFICATION. La première version déplaçait la ligne de trois lignes,
      #    et le mot « MORTE » restait dans la fenêtre de ±25 : la gate ne
      #    rougissait pas — À RAISON. C'était le témoin qui était faux.
      ("ui", 'static const char *TAG = "dn_ui";',
       'static const char *TAG = "dn_ui";\n'
       '/* on garde toujours la derniere valeur connue */')]),
    ("AC6.5 `widget detpan` borne a 167, derive de 262-95",
     i_detpan_borne,
     [("ui", "#define DET_PANH_MAX (262 - 95)", "#define DET_PANH_MAX 167"),
      ("cons", "widget detpan <0|40..167>", "widget detpan <0|40..200>")]),
]


def contexte(bruts):
    """Le CONTEXTE que voient les invariants — ⛔ AUCUN d'eux ne relit le disque.

    🔴 C'EST UN CORRECTIF DE LA GATE ELLE-MÊME, TROUVÉ PAR SON PROPRE TÉMOIN.
       Plusieurs invariants relisaient `dn_ui.c` / `dn_console.c` / `dn_hist.h`
       avec `lire()`. Une mutation appliquée en mémoire ne les atteignait donc
       PAS : leur ligne « muté ⇒ ROUGE » passait au vert par immunité, ⛔ pas par
       détection. Un témoin qui ne peut pas toucher son sujet ne prouve rien —
       la famille exacte que cette story solde. Tout passe désormais par ici."""
    return {
        "ui_brut": bruts["ui"],
        "ui": decommenter(bruts["ui"]),
        "ui_str": decommenter(bruts["ui"], chaines=True),
        "hist_brut": bruts["hist"],
        "hist": decommenter(bruts["hist"]),
        "histh_brut": bruts["histh"],
        "cons_brut": bruts["cons"],
        "cons": decommenter(bruts["cons"]),
        "cons_str": decommenter(bruts["cons"], chaines=True),
        "uih_brut": bruts["uih"],
    }


def main():
    bruts, shas = {}, {}
    for cle, chemin in (("ui", DN_UI_C), ("hist", DN_HIST_C),
                        ("histh", os.path.join(MAIN, "dn_hist.h")),
                        ("cons", os.path.join(MAIN, "dn_console.c")),
                        ("uih", DN_UI_H)):
        bruts[cle], shas[cle] = lire(chemin)
    print("=" * 78)
    print("dn4-13 / AC4+AC5+AC6 — COURBE ET INSTRUMENTS (PRÉ-VOL, ⛔ pas l'écran)")
    print("=" * 78)
    for cle in ("ui", "uih", "hist", "histh", "cons"):
        print("  %-10s sha256[:16] = %s" % (cle, shas[cle]))

    S = contexte(bruts)
    print("\n── LES INVARIANTS ─────────────────────────────────────────────────")
    for nom, f, _mut in INVARIANTS:
        ok, det = f(S)
        ctrl(ok, nom, det)

    print("\n── 🔴 TÉMOIN NÉGATIF — chaque invariant est MUTÉ et doit ROUGIR ────")
    n_mut = 0
    sans_mutation = []
    for nom, f, muts in INVARIANTS:
        if not muts:
            sans_mutation.append(nom)
            continue
        for fichier, avant, apres in muts:
            if bruts[fichier].count(avant) < 1:
                ctrl(False, "mutation applicable : %s" % nom,
                     "motif absent de %s : %.44s" % (fichier,
                                                     avant.replace("\n", " ")))
                continue
            mb = dict(bruts)
            mb[fichier] = bruts[fichier].replace(avant, apres, 1)
            ok, det = f(contexte(mb))
            n_mut += 1
            ctrl(not ok, "muté (%s) ⇒ ROUGE : %s" % (fichier, nom),
                 "«%.36s» → «%.18s»" % (avant.replace("\n", " "),
                                        apres.replace("\n", " ")))
    if sans_mutation:
        print("\n  ⛔ CONTRÔLES SANS MUTATION — ils ne sont PAS éprouvés, et on le")
        print("     DIT plutôt que de les compter comme prouvés :")
        for nom in sans_mutation:
            print("       · %s" % nom)
    ctrl(n_mut >= 18, "le témoin a joué assez de mutations",
         "%d mutations, %d contrôle(s) non éprouvé(s)"
         % (n_mut, len(sans_mutation)))

    print("\n" + "=" * 78)
    print("⚠️ CE QUE CETTE GATE NE SOLDE PAS :")
    print("   · elle RELIT le source, elle ne l'EXÉCUTE PAS — `dn_ui.c` ne se")
    print("     compile pas sur l'hôte. Elle est donc plus FAIBLE que")
    print("     `verif_hist_dn413.py`. ⛔ Ne pas conclure « AC4/AC6 soldés » ici ;")
    print("   · AC4.6 — le CONSTAT OWNER À L'ŒIL sur `RÉSEAU` et `AMBIANCE` ;")
    print("   · le témoin d'AC4.3 sur la carte (`nav open 0` → `nav open 3`")
    print("     avant toute trame `net` → `widget courbe`) ;")
    print("   · le PRIX de la décision n°5 (le montant écrasé en trait plat),")
    print("     qui est ACQUIS et ne se mesure qu'à l'écran ;")
    print("   · les témoins d'AC6.1 et d'AC6.5, qui se REJOUENT sur la carte.")
    if ko_total[0] == 0:
        print("✅ %d contrôles passent, 0 échec." % ok_total[0])
        return 0
    print("⛔ %d ÉCHEC(S) sur %d contrôles."
          % (ko_total[0], ok_total[0] + ko_total[0]))
    return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-9 / AC1+AC2+AC6 — MIROIR « CE QUE L'ÉCRAN SÉLECTIONNE » <-> « CE QUE LE FIL
PORTE », plus les invariants de la sélection, JOUABLE DEPUIS WSL SANS CARTE.

======================= CE QUE CET OUTIL EST, ET CE QU'IL N'EST PAS =========

⛔ IL NE REMPLACE PAS `selections_auditer()` (firmware, au boot). Celui-là lit
   l'ÉTAT À L'EXÉCUTION et NOMME la case fautive dans la console de la carte ;
   celui-ci lit la TABLE dans le source. Ils ne peuvent pas se substituer l'un
   à l'autre, et c'est écrit ici pour que personne ne coupe l'un au motif que
   l'autre existe.

🎯 CE QU'IL APPORTE, ET QUE LE FIRMWARE **NE PEUT PAS** VOIR :

   M1  LE MIROIR ÉCRAN <-> FIL. Le firmware n'a aucun accès à ce que l'agent
       publie : il ne peut pas savoir qu'une case SÉLECTIONNE une grandeur que
       `k_metriques[]` ne porte pas. Cette grandeur s'afficherait « -- » gris À
       VIE, et rien ne le dirait — ni compteur, ni log, ni audit.

   M2  LE MIROIR DES TAMPONS. Le producteur du texte de détail et l'instrument
       qui le relit doivent prendre LA MÊME taille. C'est une propriété de
       SOURCE : à l'exécution, le second tronque simplement en silence. C'est
       exactement le défaut trouvé au cadrage de dn4-9 (128 o pour 168
       produits, `snprintf` sans test de retour) — « un instrument faux accuse
       le sujet sain ».

   M3  UN PRÉ-VOL. Les invariants A/B/C, l'union distincte et les indices
       peuplés sont vérifiés AVANT de payer un build + un flash + une séance
       carte pour une faute de descripteur. ⚠️ C'est un DOUBLON ASSUMÉ de
       l'audit de boot, et le doublon est le point : deux lectures
       indépendantes de la même table, l'une en Python sur le source, l'autre
       en C sur la structure compilée.

⛔ IL NE CALCULE AUCUNE LARGEUR. Une largeur de texte ne se déduit PAS d'un
   nombre de caractères : elle dépend des glyphes et du crénage. L'outil ÉMET
   les commandes `widget largeur` à jouer sur la carte, construites depuis les
   descripteurs RÉELS — pour que la liste des lignes à mesurer ne puisse pas
   diverger de ce que le firmware dessine.

Sortie : exit 0 si tout passe, 1 sinon. Publie le sha256 des sources LUES
(piège n°11 : un `.pyc` périmé a déjà fait conclure ROUGE sur un arbre SAIN).
"""

import hashlib
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(RACINE, "firmware", "desknode", "main")
DN_UI_C = os.path.join(MAIN, "dn_ui.c")
DN_UI_H = os.path.join(MAIN, "dn_ui.h")
DN_LINK_C = os.path.join(MAIN, "dn_link.c")
DN_CONSOLE_C = os.path.join(MAIN, "dn_console.c")

GRANDEURS_MAX = 4

ok_total = [0]
ko_total = [0]


def lire(chemin):
    with open(chemin, "rb") as f:
        brut = f.read()
    return brut.decode("utf-8"), hashlib.sha256(brut).hexdigest()[:16]


def ctrl(ok, libelle, detail=""):
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-58s %s" % (libelle, detail))
    else:
        ko_total[0] += 1
        print("  [KO ] %-58s %s" % (libelle, detail))
    return ok


def decommenter(txt):
    """Retire les commentaires C. ⛔ INDISPENSABLE : ce dépôt écrit des
    commentaires qui CITENT du code (« `.n_grandeurs = 1` RESTE À UN »), et un
    parseur naïf les lirait comme des déclarations. Le défaut serait un chiffre
    FAUX MAIS PLAUSIBLE — la pire espèce."""
    txt = re.sub(r"/\*.*?\*/", " ", txt, flags=re.S)
    txt = re.sub(r"//[^\n]*", " ", txt)
    return txt


def bloc_table(txt, entete):
    """Le corps `{ ... };` d'une table nommée, accolades ÉQUILIBRÉES."""
    i = txt.find(entete)
    if i < 0:
        return None
    j = txt.find("{", i)
    if j < 0:
        return None
    prof = 0
    for k in range(j, len(txt)):
        if txt[k] == "{":
            prof += 1
        elif txt[k] == "}":
            prof -= 1
            if prof == 0:
                return txt[j + 1:k]
    return None


def entrees_designees(corps, motif_cle):
    """Découpe un corps de table en entrées `[CLE] = { ... }`."""
    out = {}
    for m in re.finditer(r"\[\s*(" + motif_cle + r")\s*\]\s*=\s*\{", corps):
        cle = m.group(1)
        prof = 0
        deb = m.end() - 1
        for k in range(deb, len(corps)):
            if corps[k] == "{":
                prof += 1
            elif corps[k] == "}":
                prof -= 1
                if prof == 0:
                    out[cle] = corps[deb + 1:k]
                    break
    return out


def champ_str(corps, nom):
    m = re.search(r"\." + nom + r"\s*=\s*((?:\"(?:[^\"\\]|\\.)*\"\s*)+)", corps)
    if not m:
        return None
    morceaux = re.findall(r"\"((?:[^\"\\]|\\.)*)\"", m.group(1))
    s = "".join(morceaux)
    s = s.replace("\\xC2\\xB0", "°").replace("\\xc2\\xb0", "°")
    return s


def champ_int(corps, nom, defaut=0):
    m = re.search(r"\." + nom + r"\s*=\s*(\d+)", corps)
    return int(m.group(1)) if m else defaut


def champ_ident(corps, nom):
    m = re.search(r"\." + nom + r"\s*=\s*([A-Za-z_][A-Za-z0-9_]*)", corps)
    return m.group(1) if m else None


def parser_grandeurs(corps):
    """Les initialiseurs de `.grandeurs = { {...}, {...} }`, DANS L'ORDRE."""
    m = re.search(r"\.grandeurs\s*=\s*\{", corps)
    if not m:
        return []
    deb = m.end() - 1
    prof = 0
    fin = None
    for k in range(deb, len(corps)):
        if corps[k] == "{":
            prof += 1
        elif corps[k] == "}":
            prof -= 1
            if prof == 0:
                fin = k
                break
    if fin is None:
        return []
    interieur = corps[deb + 1:fin]
    out = []
    prof = 0
    cur = []
    for ch in interieur:
        if ch == "{":
            prof += 1
            if prof == 1:
                cur = []
                continue
        elif ch == "}":
            prof -= 1
            if prof == 0:
                out.append("".join(cur))
                continue
        if prof >= 1:
            cur.append(ch)
    return out


def parser_sel(corps):
    """`.sel_p1 = DN_SEL3(0, 1, 3)` -> [0, 1, 3]. Absent -> []."""
    m = re.search(r"\.sel_p1\s*=\s*DN_SEL(\d)\s*\(([^)]*)\)", corps)
    if not m:
        return []
    vals = [int(v.strip()) for v in m.group(2).split(",") if v.strip() != ""]
    if len(vals) != int(m.group(1)):
        return None  # signalé par l'appelant
    return vals


def main():
    src_ui, sha_ui = lire(DN_UI_C)
    src_uih, sha_uih = lire(DN_UI_H)
    src_link, sha_link = lire(DN_LINK_C)
    src_cons, sha_cons = lire(DN_CONSOLE_C)

    print("=" * 78)
    print("dn4-9 — MIROIR SELECTION D'ECRAN <-> FIL, ET INVARIANTS DE SELECTION")
    print("sources LUES : dn_ui.c sha256:%s · dn_ui.h sha256:%s" % (sha_ui, sha_uih))
    print("               dn_link.c sha256:%s · dn_console.c sha256:%s"
          % (sha_link, sha_cons))
    print("=" * 78)

    nu = decommenter(src_ui)
    nl = decommenter(src_link)

    # ── k_desc[] ─────────────────────────────────────────────────────────────
    corps_desc = bloc_table(nu, "k_desc[DN_UI_METRIQUES]")
    if corps_desc is None:
        print("⛔ `k_desc[DN_UI_METRIQUES]` INTROUVABLE — le parseur ne peut RIEN")
        return 1
    cases = entrees_designees(corps_desc, r"DN_UI_CASE_[A-Z]+")

    # ── k_metriques[] ────────────────────────────────────────────────────────
    corps_met = bloc_table(nl, "k_metriques[DN_LINK_METRIQUES]")
    if corps_met is None:
        print("⛔ `k_metriques[DN_LINK_METRIQUES]` INTROUVABLE")
        return 1
    # ⚠️ `k_metriques[]` initialise POSITIONNELLEMENT (`{"cpu", 4, {…}, {…}}`),
    #    ⛔ pas par champs designes comme `k_desc[]`. Deux tables, deux styles :
    #    un parseur unique aurait lu ZERO grandeur sur le fil et conclu que
    #    TOUTES les cases affichent du vide. C'est le piege « un instrument faux
    #    accuse le sujet sain », et il a ete attrape au premier tir.
    metriques = {}
    for m in re.finditer(
            r'\[\s*(DN_LINK_M_[A-Z]+)\s*\]\s*=\s*\{\s*"([a-z]+)"\s*,\s*'
            r'(\d+)\s*,\s*\{([^}]*)\}\s*,\s*\{([^}]*)\}', corps_met):
        plaf = [int(v.strip().rstrip("uU"))
                for v in m.group(4).split(",") if v.strip()]
        unites = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(5))
        metriques[m.group(1)] = {
            "nom": m.group(2), "n": int(m.group(3)),
            "plafonds": plaf, "unites": unites,
        }

    # ── k_pc[] : la correspondance métrique -> case ───────────────────────────
    corps_pc = bloc_table(nu, "k_pc[DN_LINK_METRIQUES]")
    m2c = {}
    if corps_pc:
        for m in re.finditer(
                r"\[\s*(DN_LINK_M_[A-Z]+)\s*\]\s*=\s*\{\s*(DN_UI_CASE_[A-Z]+)\s*\+\s*1",
                corps_pc):
            m2c[m.group(1)] = m.group(2)

    # ── extraction ───────────────────────────────────────────────────────────
    d = {}
    for nom, corps in cases.items():
        gs = parser_grandeurs(corps)
        sel = parser_sel(corps)
        d[nom] = {
            "n_case": champ_int(corps, "n_grandeurs", 0),
            "n_detail_brut": champ_int(corps, "n_detail", 0),
            "detail_cols": champ_int(corps, "detail_cols", 0) or 2,
            "sel": sel,
            "titre": champ_str(corps, "titre"),
            "indicateur": champ_ident(corps, "indicateur") == "true",
            "g": [{
                "unite": champ_str(g, "unite"),
                "prefixe": champ_str(g, "prefixe"),
                "icone": champ_ident(g, "icone") or champ_str(g, "icone"),
                "prec": champ_ident(g, "prec"),
                "unite_haute": champ_str(g, "unite_haute"),
                "seuil_haut": champ_int(g, "seuil_haut", 0),
                "diviseur_haut": champ_int(g, "diviseur_haut", 0),
                "detail_seul":
                    champ_ident(g, "prefixe_detail_seul") == "true",
            } for g in gs],
        }
        d[nom]["n_detail"] = d[nom]["n_detail_brut"] or d[nom]["n_case"]

    print("\n-- 0. CE QUE LE PARSEUR A LU (⛔ RELU, jamais recite) --")
    print("   %-18s %-5s %-14s %-7s %s" % ("case", "case", "indices", "detail",
                                           "grandeurs (unite/prefixe)"))
    for nom in cases:
        e = d[nom]
        sel = e["sel"] if e["sel"] else list(range(e["n_case"]))
        libelles = " · ".join(
            "%s%s" % ((g["prefixe"] + " ") if g["prefixe"] else "", g["unite"])
            for g in e["g"])
        print("   %-18s %-5d %-14s %-7d %s"
              % (e["titre"], e["n_case"], str(sel), e["n_detail"], libelles))

    # ── M3 : invariants A / B / C ────────────────────────────────────────────
    print("\n-- M3. LES INVARIANTS DE LA SELECTION (pre-vol de l'audit de boot) --")
    for nom in cases:
        e = d[nom]
        t = e["titre"]
        if e["sel"] is None:
            ctrl(False, "%s : DN_SELn(...) mal forme" % t,
                 "l'arite de la macro ne correspond pas au nombre d'arguments")
            continue
        declare = len(e["sel"])
        # C — declaration entiere ou nulle
        ctrl(declare in (0, e["n_case"]),
             "%s : invariant C (sel declaree en entier ou pas du tout)" % t,
             "%d rang(s) declare(s) pour n_case = %d" % (declare, e["n_case"]))
        sel = e["sel"] if declare else list(range(e["n_case"]))
        # A — sous-ensemble de ce que le detail montre
        hors = [g for g in sel if g >= e["n_detail"]]
        ctrl(not hors, "%s : invariant A (case ⊆ detail)" % t,
             "sel = %s, n_detail = %d%s"
             % (sel, e["n_detail"],
                "" if not hors else "  ⛔ hors detail : %s" % hors))
        # B — indices deux a deux distincts
        ctrl(len(set(sel)) == len(sel),
             "%s : invariant B (indices distincts)" % t, "sel = %s" % sel)
        # bornes
        ctrl(all(0 <= g < GRANDEURS_MAX for g in sel),
             "%s : tout indice < DN_WIDGET_GRANDEURS_MAX" % t, "sel = %s" % sel)
        ctrl(e["n_detail"] <= GRANDEURS_MAX,
             "%s : n_detail <= DN_WIDGET_GRANDEURS_MAX" % t,
             "n_detail = %d" % e["n_detail"])

    # ── M3 (suite) : union peuplee et DISTINCTE ──────────────────────────────
    print("\n-- M3. L'UNION (= la plage du DETAIL) EST PEUPLEE ET DISTINCTE --")
    for nom in cases:
        e = d[nom]
        t = e["titre"]
        nd = e["n_detail"]
        vides = [g for g in range(nd)
                 if g >= len(e["g"]) or not e["g"][g]["prec"]
                 or e["g"][g]["prec"] == "DN_PREC_NON_RENSEIGNEE"]
        ctrl(not vides, "%s : les %d entrees de l'union sont PEUPLEES" % (t, nd),
             "" if not vides else "⛔ prec NON RENSEIGNEE en %s" % vides)
        # 🔴 dn4-9 (2026-08-22) : CHAQUE VUE AVEC **SES** ETIQUETTES.
        #    Depuis `prefixe_detail_seul`, une paire peut etre DISTINCTE au
        #    detail (il affiche les prefixes) et INDISTINCTE dans la case (qui
        #    ne les affiche pas). Juger « l'union » avec un seul jeu
        #    d'etiquettes ferait exactement l'erreur que la garde empeche.
        def etiquette(g, detail):
            gg = e["g"][g]
            if not detail and gg["detail_seul"]:
                return None
            return gg["prefixe"]

        def flou_de(indices, detail):
            for ia_ in range(len(indices)):
                for ib_ in range(ia_ + 1, len(indices)):
                    a, b = indices[ia_], indices[ib_]
                    if a >= len(e["g"]) or b >= len(e["g"]):
                        continue
                    ua, ub = e["g"][a]["unite"], e["g"][b]["unite"]
                    if not ua or not ub or ua != ub:
                        continue
                    pa, pb = etiquette(a, detail), etiquette(b, detail)
                    if pa and pb and pa != pb:
                        continue
                    if (pa is None) != (pb is None):
                        continue
                    ica, icb = e["g"][a]["icone"], e["g"][b]["icone"]
                    if ica and icb and ica != icb:
                        continue
                    if (ica is None) != (icb is None):
                        continue
                    return (a, b, ua)
            return None

        sel_case = e["sel"] if e["sel"] else list(range(e["n_case"]))
        fc = flou_de(sel_case, False)
        ctrl(fc is None, "%s : la CASE n'a aucune paire INDISTINGUABLE" % t,
             "indices %s, etiquettes de CASE" % sel_case if fc is None
             else "⛔ grandeurs %d et %d portent « %s » sans prefixe NI ICONE "
                  "AFFICHE DANS LA CASE" % fc)
        fd = flou_de(list(range(nd)), True)
        ctrl(fd is None, "%s : le DETAIL n'a aucune paire INDISTINGUABLE" % t,
             "indices [0..%d], etiquettes de DETAIL" % (nd - 1) if fd is None
             else "⛔ grandeurs %d et %d portent « %s » sans prefixe ni icone" % fd)

    # ── M4 : LA REGLE DES UNITES — owner, 2026-08-22 ─────────────────────────
    print("\n-- M4. « ON NE DEPASSE PAS 3 000 » (decision owner du 2026-08-22) --")
    print("   ⚠️ Elle NE SE VERIFIE PAS a l'oeil : le plafond d'une grandeur vit")
    print("      dans `k_metriques[]` (le FIL) et la bascule dans `k_desc[]`")
    print("      (l'ECRAN). Deux tables, deux fichiers — c'est un MIROIR.")
    SEUIL = 30000  # en DIXIEMES : 3000,0
    exemptions = []
    for met, case in sorted(m2c.items()):
        if case not in d or met not in metriques:
            continue
        e = d[case]
        t = e["titre"]
        pl = metriques[met]["plafonds"]
        for g, gg in enumerate(e["g"]):
            if g >= len(pl) or g >= e["n_detail"]:
                continue
            plaf = pl[g]
            if gg["seuil_haut"]:
                # une echelle ARMEE doit basculer AU PLUS a 3000
                ctrl(gg["seuil_haut"] <= SEUIL,
                     "%s g%d (%s) : la bascule est <= 3000" % (t, g, gg["unite"]),
                     "seuil_haut = %d dixiemes (= %d,%d %s)"
                     % (gg["seuil_haut"], gg["seuil_haut"] // 10,
                        gg["seuil_haut"] % 10, gg["unite"]))
                # et l'unite HAUTE ne doit pas depasser 3000 non plus
                if gg["diviseur_haut"]:
                    haut = plaf // gg["diviseur_haut"]
                    ctrl(haut <= SEUIL,
                         "%s g%d : l'unite HAUTE ne depasse pas 3000 non plus"
                         % (t, g),
                         "plafond %d / %d = %d,%d %s"
                         % (plaf, gg["diviseur_haut"], haut // 10, haut % 10,
                            gg["unite_haute"] or "?"))
            elif plaf > SEUIL:
                if gg["unite_haute"]:
                    ctrl(False,
                         "%s g%d (%s) : echelle NON ARMEE alors qu'elle existe"
                         % (t, g, gg["unite"]),
                         "⛔ plafond %d,%d depasse 3000 et `unite_haute` = « %s »"
                         % (plaf // 10, plaf % 10, gg["unite_haute"]))
                else:
                    exemptions.append((t, g, gg["unite"], plaf))
    if exemptions:
        print("   ⚠️ EXEMPTIONS — grandeurs qui PEUVENT depasser 3000 et qui n'ont")
        print("      AUCUNE unite superieure declaree. ⛔ Ce n'est PAS un echec :")
        print("      c'est une liste, pour que l'exemption reste VISIBLE et")
        print("      re-decidable, ⛔ pas silencieuse.")
        for t, g, u, plaf in exemptions:
            print("      · %-9s grandeur %d : plafond %d %s"
                  % (t, g, (plaf + 5) // 10, u))
        print("      (`tr/min` n'a pas de prefixe M/G qui se lise : « 10,0 k tr/min »")
        print("       serait PLUS LONG que « 10000 tr/min », mesure a l'appui.)")

    # ── M1 : LE MIROIR ECRAN <-> FIL ─────────────────────────────────────────
    print("\n-- M1. MIROIR ECRAN <-> FIL (⛔ le firmware ne peut PAS le voir) --")
    ctrl(len(m2c) > 0, "la correspondance metrique -> case a ete LUE",
         "%d entree(s)" % len(m2c))
    for met, case in sorted(m2c.items()):
        if case not in d:
            ctrl(False, "%s -> %s : case INCONNUE de k_desc[]" % (met, case))
            continue
        if met not in metriques:
            ctrl(False, "%s : metrique absente de k_metriques[]" % met)
            continue
        n_fil = metriques[met]["n"]
        e = d[case]
        t = e["titre"]
        sel = e["sel"] if e["sel"] else list(range(e["n_case"]))
        pires = [g for g in sel if g >= n_fil]
        ctrl(not pires,
             "%s : la CASE ne selectionne que des grandeurs du fil" % t,
             "sel = %s, le fil en porte %d%s"
             % (sel, n_fil,
                "" if not pires
                else "  ⛔ %s ne sera JAMAIS alimentee — « -- » gris A VIE" % pires))
        ctrl(e["n_detail"] <= n_fil,
             "%s : le DETAIL ne montre que des grandeurs du fil" % t,
             "n_detail = %d, le fil en porte %d" % (e["n_detail"], n_fil))

    # ── M2 : LE MIROIR DES TAMPONS ───────────────────────────────────────────
    print("\n-- M2. MIROIR DES TAMPONS (producteur du detail <-> instrument) --")
    ctrl("#define DN_UI_DETAIL_TXT_MAX" in src_uih,
         "DN_UI_DETAIL_TXT_MAX est DEFINI dans dn_ui.h")
    ctrl("char buf[DN_UI_DETAIL_TXT_MAX]" in src_ui,
         "le PRODUCTEUR (detail_reparametrer) prend la constante")
    ctrl("char t[DN_UI_DETAIL_TXT_MAX]" in src_cons,
         "l'INSTRUMENT (widget detail) prend LA MEME constante")
    # ⚠️ SUR LE SOURCE DECOMMENTE : l'amendement date CITE l'ancienne taille
    #    (« ⛔ PLUS `DN_WIDGET_TXT_MAX * 4 + 64` »), et le depot ANNOTE au lieu
    #    d'effacer. Une gate qui grepperait le brut epinglerait ROUGE le
    #    commentaire qui documente le correctif.
    ctrl("DN_WIDGET_TXT_MAX * 4 + 64" not in decommenter(src_cons),
         "⛔ l'ancienne taille de l'instrument (128 o) a DISPARU du CODE",
         "elle tronquait EN SILENCE un texte de 168 o")
    ctrl("int besoin = snprintf(txt, txt_n" in src_ui,
         "la copie de l'instrument TESTE le retour de snprintf",
         "sans ce test, un texte amputé serait rendu comme complet")

    # ── LES LIGNES A MESURER SUR LA CARTE ────────────────────────────────────
    print("\n-- LES LIGNES A MESURER (⛔ AUCUNE LARGEUR N'EST CALCULEE ICI) --")
    print("   Une largeur depend des GLYPHES et du crenage, ⛔ pas d'un nombre de")
    print("   caracteres. Ces commandes se jouent SUR LA CARTE, en dn_font_28 :")
    print("     python3 tools/dn_console.py \"widget detail\"   # rend w, wp et x")
    print("   ⚠️ Les « 446 px utiles » des commentaires sont un chiffre de")
    print("      COMMENTAIRE : `utile = wp - 2*x`. RELIRE, ⛔ ne pas croire.")
    c2m = dict((c, m) for m, c in m2c.items())

    def plafond_de(nom_case, g):
        """Le plafond RÉEL de la grandeur, LU dans `k_metriques[]`.
        ⛔ Jamais un « 100000 » inventé : un pire cas SURESTIMÉ ferait
           raccourcir un libellé pour une largeur qui ne peut pas se produire —
           un instrument faux dans l'autre sens."""
        met = c2m.get(nom_case)
        if not met or met not in metriques:
            return None
        pl = metriques[met]["plafonds"]
        return pl[g] if g < len(pl) else None

    def pire(nom_case, e, g, detail=True):
        """Le pire cas RENDU d'une grandeur, dans la vue demandee.
        ⚠️ Trois choses s'y jouent, et les rater fabrique un faux pire cas :
           l'ECHELLE HAUTE (elle RACCOURCIT le texte), la PRECISION, et
           l'ETIQUETTE, qui depend de la VUE (`prefixe_detail_seul`)."""
        gg = e["g"][g]
        p = plafond_de(nom_case, g)
        if p is None:
            return None
        unite = gg["unite"]
        if gg["seuil_haut"] and gg["diviseur_haut"] and p >= gg["seuil_haut"]:
            # au-dela du seuil, c'est l'unite HAUTE qui s'affiche ; le pire cas
            # en unite de BASE est donc `seuil - 1`.
            bas = gg["seuil_haut"] - 1
            haut = p // gg["diviseur_haut"]
            p, unite = (bas, gg["unite"]) if bas > haut else (haut,
                                                              gg["unite_haute"])
        if gg["prec"] == "DN_PREC_ENTIER":
            val = "%d" % ((p + 5) // 10)
        else:
            val = "%d,%d" % (p // 10, p % 10)
        pfx = gg["prefixe"]
        if not detail and gg["detail_seul"]:
            pfx = None
        px = (pfx + " ") if pfx else ""
        return "%s%s %s" % (px, val, unite)

    print("   ⛔ Le REPL de la carte MANGE les octets non-ASCII (mesure le")
    print("      2026-08-22) : le « · » et le « ° » n'arrivent PAS. Les chiffres")
    print("      rendus sont donc des BORNES BASSES pour les lignes qui en")
    print("      portent. Le seul instrument EXACT est `widget detail`, qui relit")
    print("      le texte REELLEMENT compose par le firmware.")
    for nom in cases:
        e = d[nom]
        nd = e["n_detail"]
        cols = e["detail_cols"]
        if nd < 1:
            continue
        ligne, cur = 1, []
        for i in range(nd):
            ti = pire(nom, e, i, detail=True)
            if ti is None:
                continue
            cur.append(ti)
            if len(cur) == cols or i == nd - 1:
                print("   widget largeur \"%s\"   # detail %s l%d (cols=%d)"
                      % ("   ·   ".join(cur), e["titre"], ligne, cols))
                cur = []
                ligne += 1
    print("   -- et les lignes de CASE, avec les etiquettes DE LA CASE --")
    for nom in cases:
        e = d[nom]
        sel = e["sel"] if e["sel"] else list(range(e["n_case"]))
        for g in sel:
            t = pire(nom, e, g, detail=False)
            if t:
                print("   widget largeur \"%s\"   # CASE %s, grandeur %d"
                      % (t, e["titre"], g))
    # ⚠️ L'ECHELLE HAUTE CHANGE LE PIRE CAS, ET ON NE LE DEVINE PAS ICI.
    for nom in cases:
        e = d[nom]
        for g, gg in enumerate(e["g"]):
            if gg.get("unite_haute"):
                print("   ⚠️ %s grandeur %d a une ECHELLE HAUTE (« %s ») : le "
                      "texte le plus large n'est PAS forcement le plafond en "
                      "unite de base. A relire par `widget detail`."
                      % (e["titre"], g, gg["unite_haute"]))

    print("\n" + "=" * 78)
    if ko_total[0] == 0:
        print("✅ %d controles passent, 0 echec." % ok_total[0])
        print("⚠️  RAPPEL : ce fichier ne solde NI AC5 NI AC8. Les largeurs se")
        print("   MESURENT sur la carte, et les constats sensoriels sont l'OWNER.")
        return 0
    print("⛔ %d ECHEC(S) sur %d controles." % (ko_total[0], ok_total[0] + ko_total[0]))
    return 1


if __name__ == "__main__":
    sys.exit(main())

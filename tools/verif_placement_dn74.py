#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn7-4 — LA PAGE DIT LE VRAI **LA OU L'ŒIL EST**.

======================= CE QUE CETTE GATE GARDE, ET POURQUOI ================

Trois constats releves **A L'ŒIL PAR L'OWNER** le 2026-09-10, sur
`installeur/index.html`. ⛔ AUCUN DES TROIS N'EST UN MENSONGE DE LA PAGE :
c'est du PLACEMENT et de la LISIBILITE.

  1. **LE VERDICT D'UN VERBE S'ECRIVAIT QUATRE GESTES PLUS BAS.** `b-stop` vit
     au GESTE 1, `b-retirer` en SECTION 4, et `#sortie` n'avait qu'UNE place —
     apres la fermeture de la liste des gestes. Tout choix FIXE sert l'un et
     trahit l'autre : c'est pour ca que le defaut de « retirer », corrige par
     `dn7-2-2`, a SURVECU pour « arreter », DANS L'AUTRE SENS. ⇒ la place
     devient MOBILE, et cette gate garde le mecanisme.
  2. **LA SUPPOSITION S'AFFICHAIT LA OU L'ŒIL EST, LE FAIT EXACT UNE ETAPE PLUS
     BAS.** `consoleOuvrir()` NOMME deja ses trois refus dans `#etat-console`
     (geste 4) ; le geste de langue, geste 3, ecrivait « le plus souvent, un
     selecteur est deja ouvert ». ⇒ le refus NOMME est enregistre, puis relaye
     tel quel, et `langue.port-indisponible` retrecit a son SEUL cas vrai — le
     retour MUET de `consoleOuvrir()`. ⛔ Aucune cle neuve.
  3. **LA SELECTION N'ETAIT PAS LISIBLE.** La regle d'etat des deux selecteurs
     portait EXACTEMENT les declarations de `button:hover:enabled` ⇒ survoler
     une position inactive la faisait passer pour active. ⇒ l'etat actif se
     dessine en APLAT — une difference de FORME, ⛔ pas de teinte.

── LES TREIZE CONTROLES DU DOSSIER, ET LEUR NUMERO ICI ─────────────────────

    (a) ⇒ (c1)    (b) ⇒ (c2)    (c) ⇒ (c3)    (d) ⇒ (c4)    (e) ⇒ (c5)
    (f) ⇒ (c6)    (g) ⇒ (c7)    (h) ⇒ (c8)    (i) ⇒ (c9)    (j) ⇒ (c10)
    (k) ⇒ (c11)   (l) ⇒ (c12)   (m) ⇒ (c13)

  Et trois de plus, qui gardent la campagne elle-meme : `(c14)` chaque
  controle est vise par au moins un mutant · `(c15)` chaque cible declaree est
  un controle REEL · `(c16)` `CIBLES` et `MUTANTS` se correspondent.

── CHAQUE LIGNE DE LA MATRICE D'E/S A SON PORTEUR, ET IL EST NOMME ─────────

  · verbe joue depuis le geste 1 .................. (c1)(c2)(c3)
  · verbe joue depuis la section 4 ................ (c1)(c2)(c3)
  · echec reseau du verbe ......................... (c3)(c4)
  · panne page-niveau, ⛔ sans clic ................ (c5) — et (c1) pour le
    retour a la place d'origine
  · selecteur de port ANNULE au geste de langue ... (c6)(c7)(c8)(c9), **et**
    `tools/verif_banc_langue_dn73.py`, qui EXECUTE ce chemin (cas
    `selecteur-annule`)
  · port TENU PAR L'AGENT au geste de langue ...... (c6)(c8)(c9)
  · navigateur SANS acces serie au geste de langue  (c6)(c8)(c9)
  · ouverture REELLEMENT deja en vol .............. (c8) — le repli est
    CONSERVE, et le banc le joue (cas `selecteur-deja-en-vol`)
  · deuxieme tentative apres un refus ............. (c7)
  · position ACTIVE d'un selecteur ................ (c10)(c11)(c13), **et** le
    releve `mesures/dn7-4/T2` cote Windows, qui seul ferme `AC7.4.3`
  · SURVOL d'une position inactive ................ (c11)
  · position active DESARMEE ...................... (c12)

  ⚠️ `(c5)` porte DEUX faits, ⛔ pas un : l'appel de DEMARRAGE part **sans
     ancre** (personne n'a clique) et celui de `jouer` part **avec** (le
     rafraichissement fait partie du clic, et sans ancre il renvoyait le verdict
     d'un verbe REUSSI quatre gestes plus bas).

── ⛔ CE QU'ELLE NE PROUVE PAS, ET C'EST ECRIT PLUTOT QUE TU ────────────────

  🔴 **CETTE GATE EST STRUCTURELLE : elle ⛔ N'EXECUTE PAS le JavaScript de la
     page, et elle ⛔ ne dessine rien.** Elle prouve que le MECANISME EST
     BRANCHE — que la place est mobile, que le refus nomme remonte, que la
     regle d'etat existe, porte un fond, differe du survol et traite le cas
     desarme. Elle ⛔ ne prouve PAS que l'œil le voie.
  ⛔ Le seul instrument de ce depot qui EXECUTE ce script est
     `tools/verif_banc_langue_dn73.py`, et son perimetre est le GESTE DE
     LANGUE. Il n'est ⛔ pas etendu ici.
  ⛔ `AC7.4.3` se ferme **A L'ŒIL DE L'OWNER**, ⛔ par aucune gate — meme
     famille qu'`AC7.2.2.2`. L'instrument nomme est `mesures/dn7-4/T2`.
  ⛔ Elle ne juge AUCUNE **valeur** de couleur : l'egalite page ⇄
     `installeur/IDENTITE.md`, dans les deux sens, reste gardee par `(c19)` de
     `tools/verif_installeur_dn71.py`. Ici on refuse qu'un `#rrggbb` entre dans
     les regles que cette marche ajoute, **et** qu'un `--dn-*` y soit employe
     sans etre DECLARE dans `:root` — `(c19)` ne compare que des litteraux
     `#rrggbb` et ⛔ ne dit rien d'un NOM de propriete personnalisee : une
     coquille comme `var(--dn-accnt)` fait disparaitre le fond EN SILENCE.
  ⚠️ **`#sec-langue button[aria-pressed="true"]:disabled` EST POSEE PAR
     SYMETRIE, ET ELLE ⛔ NE PEUT PAS SE DECLENCHER AUJOURD'HUI** : les deux
     boutons du selecteur **de la page** ne sont jamais mis `disabled` — seuls
     ceux **de la dalle** le sont, par `langueBoutons()` pendant `langueEnVol`.
     ⇒ `(c12)` garde DEUX regles mais ⛔ n'en exerce qu'UNE en pratique ; l'autre
     existe pour que la paire reste symetrique le jour ou le selecteur de page
     se desarmera. C'est ecrit plutot que tu, pour que `(c12)` ⛔ ne surestime
     pas ce qu'elle couvre. Les mutants 22 et 23 mutent LES DEUX regles.

Emploi :
    python3 tools/verif_placement_dn74.py
    python3 tools/verif_placement_dn74.py --liste-mutants
    python3 tools/verif_placement_dn74.py --mutant <n>

Sortie : 0 si tout passe · 1 sur un vrai defaut · 2 sur un mutant inconnu ·
         3 si le mutant demande est PERIME (il n'a rien change).
"""

import argparse
import ast
import copy
import io
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGE = "installeur/index.html"
FIXES = (PAGE,)

# ── LES NOMS QUE LA PAGE PORTE, ⛔ PAS UN NUMERO DE LIGNE ──────────────────
# 🔴 UNE ADRESSE `fichier:ligne` SE PERIME AU PREMIER COMMIT. Tout ce qui suit
#    est un NOM ou un MOTIF ; la gate relit, ⛔ elle ne pointe pas.
ELEMENT_SORTIE = "sortie"
NOM_MONTRER = "montrerSortie"
NOM_ECRIRE_MOT = "ecrireMot"
NOM_JOUER = "jouer"
NOM_RAFRAICHIR = "rafraichirEtat"
NOM_REFUS = "consoleRefus"
NOM_OUVRIR = "consoleOuvrir"
NOM_POSE = "poserLangueDalle"
# La fenetre de `sansPort`, qui est une EXPRESSION de fonction, ⛔ pas une
# declaration : elle vit DANS le corps de la pose.
OUVRANT_SANS_PORT = "var sansPort = function () {"
FERMANT_SANS_PORT = "\n  };"

BLOC_LANGUE = "etat-langue"
CLE_REPLI = "langue.port-indisponible"
# Les TROIS refus que la console nomme deja — ⛔ aucune cle neuve n'est
# introduite par cette marche, et c'est la propriete.
CLES_REFUS = ("console.sans-serial", "console.port-refuse", "console.aucun-port")

# ── LES DEUX SELECTEURS, ET LE SURVOL AUQUEL L'ETAT NE DOIT PLUS RESSEMBLER ─
SEL_SURVOL = "button:hover:enabled"
SEL_DESARME = "button:disabled"
# 🔴 LE FOND **DE REPOS** D'UN BOUTON — c'est-a-dire celui d'une position ⛔ NON
#    SELECTIONNEE. Un « aplat » qui vaut ce fond-la ne dessine RIEN : c'est
#    exactement l'etat qu'il pretend distinguer. ⇒ il est LU dans la page, ⛔ pas
#    ecrit ici, et l'egalite est un KO.
SEL_REPOS = "button"
SEL_ACTIF = ('#sec-langue button[aria-pressed="true"]',
             '#sec-langue-dalle button[aria-pressed="true"]')
SEL_ACTIF_DESARME = tuple(s + ":disabled" for s in SEL_ACTIF)
# ⚠️ LE CORPS ATTENDU DES DEUX REGLES DESARMEES — il sert AUX MUTANTS, ⛔ a
#    aucun controle : ce que les controles lisent, ils le CONFRONTENT a la page
#    (`button:disabled`, `button`), ⛔ ils ne le comparent pas a ce litteral.
DECL_DESARME = (" { border-color: var(--dn-trait); background: var(--dn-trait);"
                " color: var(--dn-eteint); }")

RE_STYLE = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
RE_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RE_JETON = re.compile(r"var\(\s*--dn-[\w-]+\s*\)")
# Le NOM du jeton employe, et le nom de ceux qui sont DECLARES.
RE_NOM_JETON = re.compile(r"var\(\s*(--dn-[\w-]+)\s*\)")
RE_JETON_DECLARE = re.compile(r"^\s*(--dn-[\w-]+)\s*:", re.M)
# Les proprietes qui POSENT UN FOND. ⛔ Liste FERMEE : `background-image` ne
# pose pas un aplat de couleur, et l'admettre rendrait le controle vacant.
PROPS_FOND = ("background", "background-color")
# Les proprietes qui PORTENT UNE COULEUR dans les regles de cette marche.
# ⛔ Liste FERMEE : ce sont celles que les quatre regles declarent.
PROPS_COULEUR = ("background", "background-color", "border-color", "color")
# Un fond qui n'en est pas un — ⛔ la regle doit poser une couleur, pas rien.
FONDS_NULS = ("none", "transparent", "initial", "unset", "inherit")

LARGEUR_LIBELLE = 58

ok_total = [0]
ko_total = [0]
ids_emis = []

MUTANTS = {}                      # ⛔ AU NIVEAU MODULE — sinon `--liste-mutants`
CIBLES = {}                       # ⛔ AU NIVEAU MODULE — matiere de (c14)

MUTANTS[1] = ("recode la place d'origine EN DUR au lieu de la LIRE "
              "⇒ une seconde definition, qui divergera")
CIBLES[1] = ("c1",)
MUTANTS[2] = ("revele le bloc AVANT de le deplacer ⇒ il apparait a "
              "son ancienne place, puis saute")
CIBLES[2] = ("c2",)
MUTANTS[3] = ("retire l'ancre a UN SEUL site de `jouer` (le verdict) "
              "⇒ la forme EXACTE qui a survecu a dn7-2-2")
CIBLES[3] = ("c3",)
MUTANTS[4] = ("fait AVALER son ancre par la fabrique d'ecriture ⇒ "
              "trois appelants la passent pour rien")
CIBLES[4] = ("c4",)
MUTANTS[5] = ("ancre l'appel de DEMARRAGE sur un bouton ⇒ une cause "
              "FAUSSE publiee sans que personne ait clique")
CIBLES[5] = ("c5",)
MUTANTS[6] = ("cesse d'ENREGISTRER le refus que la console vient de "
              "nommer ⇒ le geste de langue n'a plus rien a relayer")
CIBLES[6] = ("c6",)
MUTANTS[7] = ("fait ecrire un refus HORS de la fabrique de refus ⇒ "
              "il s'affiche mais n'est plus nomme")
CIBLES[7] = ("c6",)
MUTANTS[8] = ("n'efface plus le refus au DEBUT de la tentative ⇒ un "
              "refus PERIME est relaye comme un fait du tir")
CIBLES[8] = ("c7",)
MUTANTS[9] = ("ecrit la SUPPOSITION inconditionnellement ⇒ le defaut "
              "d'origine, replante mot pour mot")
CIBLES[9] = ("c8",)
MUTANTS[10] = ("passe DEUX cles pour UN fait ⇒ le cadre se dessine "
               "sur une issue, le texte sur une autre")
CIBLES[10] = ("c9",)
MUTANTS[11] = ("retire le fond de la position active du selecteur de "
               "page ⇒ elle redevient un simple contour")
CIBLES[11] = ("c10",)
MUTANTS[12] = ("remet les declarations du SURVOL dans la regle "
               "d'etat ⇒ selectionne et survole indiscernables")
CIBLES[12] = ("c10", "c11")
MUTANTS[13] = ("retire le cas ACTIF + DESARME ⇒ la specificite "
               "l'emporte et un bouton grise se lit actionnable")
CIBLES[13] = ("c12", "c13")
MUTANTS[14] = ("plante un `#rrggbb` dans la regle d'etat ⇒ une "
               "couleur qui echappe a l'identite declaree")
CIBLES[14] = ("c13",)
MUTANTS[15] = ("vide la cible d'un mutant ⇒ un controle garde par "
               "ZERO mutant, et rien ne le dit")
CIBLES[15] = ("c14",)
MUTANTS[16] = ("declare dans `CIBLES` un controle INEXISTANT ⇒ une "
               "cible PERIMEE que « N rouges » ne voit pas")
CIBLES[16] = ("c15",)
MUTANTS[17] = ("declare une cible pour un mutant qui N'EXISTE PAS")
CIBLES[17] = ("c16",)
MUTANTS[18] = ("declare un mutant dont le CORPS LEVE ⇒ un mutant "
               "MORT, qui doit se rendre en KO et ⛔ pas en trace")
CIBLES[18] = ("c0",)
MUTANTS[19] = ("replante une SORTIE ANTICIPEE NON DECLAREE ⇒ le "
               "bilan sort sur une population RETRECIE")
CIBLES[19] = ("z",)
MUTANTS[20] = ("pose l'aplat dans un COMMENTAIRE et rend la vraie "
               "regle au survol ⇒ un leurre qui reverdit la gate")
CIBLES[20] = ("c10", "c11")
MUTANTS[21] = ("peint l'aplat avec le FOND DE REPOS d'un bouton ⇒ "
               "l'actif est peint comme une position NON choisie")
CIBLES[21] = ("c10",)
MUTANTS[22] = ("retire la BORDURE des deux regles desarmees ⇒ le "
               "bouton grise garde sa bordure d'accent")
CIBLES[22] = ("c12",)
MUTANTS[23] = ("rend au desarme le fond de repos ⇒ la langue "
               "choisie DISPARAIT pendant que le geste est en vol")
CIBLES[23] = ("c12",)
MUTANTS[24] = ("ecrit un NOM de jeton qui n'existe pas ⇒ le fond "
               "disparait EN SILENCE, et aucun `#rrggbb` ne bouge")
CIBLES[24] = ("c13",)
MUTANTS[25] = ("retire l'ancre au rafraichissement de `jouer` ⇒ un "
               "verbe REUSSI voit son verdict fuir sous l'etape 4")
CIBLES[25] = ("c5",)

# ⚠️ LE COMPTE DU CHEMIN NORMAL : 1 pre-vol + un controle par mutant + les 16
#    controles numerotes. Il se PERIME si on ajoute un controle sans le mettre
#    a jour — et c'est voulu : c'est ce qui rend (z) FALSIFIABLE.
CONTROLES_PREVUS = 1 + len(MUTANTS) + 16

_MUTANT = 0

RE_ID_CTRL = re.compile(r"\((\w+)\)")


def ctrl(ok, libelle, detail=""):
    """UNE assertion, UNE ligne, UN identifiant. ⛔ Aucun controle muet.

    ⚠️ L'IDENTIFIANT VIT DANS LE LIBELLE, ⛔ pas dans un argument a part : la
       campagne de mutants lit les libelles A L'AST en prenant le second
       argument de chaque appel, et A COLONNE FIXE."""
    assert len(libelle) < LARGEUR_LIBELLE, (
        "libelle de %d colonnes (max %d) : %r"
        % (len(libelle), LARGEUR_LIBELLE - 1, libelle))
    m = RE_ID_CTRL.match(libelle)
    ids_emis.append(m.group(1) if m else "?")
    if ok:
        ok_total[0] += 1
    else:
        ko_total[0] += 1
    print("  [%s] %-58s %s" % ("OK " if ok else "KO ", libelle, detail))
    return ok


def bilan(rc, anticipee=""):
    """TOUT CHEMIN QUI REND UN VERDICT passe ici. Une gate qui sort sans
    `BILAN` est indiscernable d'une gate MORTE — et c'est precisement le
    discriminant que la campagne exige de chaque mutant.

    ⚠️ DEUX SORTIES NE PASSENT PAS ICI, ET C'EST ECRIT PLUTOT QUE PROMIS :
       · `--liste-mutants`, qui n'emet AUCUN controle et ne rend AUCUN verdict ;
       · le mutant INCONNU, qui est une ERREUR D'APPEL et rend 2."""
    emis = ok_total[0] + ko_total[0]
    if not anticipee and emis != CONTROLES_PREVUS:
        ctrl(False, "(z) tout controle prevu est EMIS",
             "⛔ %d emis pour %d prevus — une gate qui joue MOINS de controles "
             "qu'annonce sort VERTE sur une population RETRECIE, ⛔ sans le "
             "declarer" % (emis, CONTROLES_PREVUS))
        rc = 1
    print("\n" + "=" * 78)
    if anticipee:
        print("⛔ SORTIE ANTICIPEE — %d controle(s) emis sur %d prevus : %s"
              % (ok_total[0] + ko_total[0], CONTROLES_PREVUS, anticipee))
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return rc


# ═══════════════════════ LIRE LA PAGE ══════════════════════════════════════

def lire(chemin):
    try:
        with io.open(os.path.join(RACINE, chemin), encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def region(txt, ouvrant, fermant):
    """La portion entre deux bornes, ⛔ pas le fichier entier.

    🔴 UNE FENETRE QUI NE SE REFERME PAS REND **VIDE**, ⛔ jamais « tout ce qui
       suit » : le fermant est cherche APRES l'ouvrant, et son absence est un
       vide, ⛔ pas une permission de balayer la fin du fichier."""
    if not txt or ouvrant not in txt:
        return ""
    apres = txt.split(ouvrant, 1)[1]
    if fermant not in apres:
        return ""
    return apres.split(fermant, 1)[0]


def sans_commentaires(js):
    """Le script SANS ses commentaires — ⛔ ce qui s'execute, pas ce qui
    l'explique. Une gate qui compte la prose de ses propres commentaires
    rougirait sur sa documentation, et un mutant pourrait la faire rougir en
    posant un litteral dans un commentaire."""
    js = re.sub(r"/\*.*?\*/", " ", js or "", flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", " ", js)


def style_de(page):
    """Les feuilles de style de la page, **SANS LEURS COMMENTAIRES**.

    🔴 MESURE DU 2026-09-10 — SANS CE RETRAIT, UN LEURRE DANS UN `/* … */`
       SUFFIT A REVERDIR LA GATE. Demontre : la regle REELLE remise aux
       declarations EXACTES du survol, et un commentaire portant l'aplat pose
       juste avant ⇒ `bloc_regle` appariait le COMMENTAIRE, `(c10)` et `(c11)`
       sortaient VERTS sur une page ou « selectionne » et « survole » etaient
       redevenus indiscernables. C'est le meme piege que `sans_commentaires`
       ferme cote script — une gate qui lit de la prose prouve un `grep`,
       ⛔ pas une propriete. Le mutant 20 le REPLANTE."""
    brut = "\n".join(RE_STYLE.findall(page or ""))
    return re.sub(r"/\*.*?\*/", " ", brut, flags=re.S)


RE_FONCTION = r"function %s\([^)]*\) \{(.*?)\n\}"


def corps_fonction(js, nom):
    """Le CORPS d'une fonction du script, ⛔ pas le script entier.

    🔴 UN CONTROLE DE RANG QUI BALAIE TOUT LE SCRIPT MESURE L'ORDRE DES
       DECLARATIONS, ⛔ pas celui des branches."""
    m = re.search(RE_FONCTION % re.escape(nom), js or "", re.S)
    return m.group(1) if m else ""


def signature(js, nom):
    """Les PARAMETRES declares d'une fonction, dans l'ordre. Vide si absente."""
    m = re.search(r"function %s\(([^)]*)\)" % re.escape(nom), js or "")
    if not m:
        return []
    return [p.strip() for p in m.group(1).split(",") if p.strip()]


def bloc_regle(style, selecteur):
    """Le CORPS d'une regle CSS, ⛔ pas le voisinage.

    ⚠️ LE SELECTEUR EST SUIVI D'UNE ACCOLADE, ⛔ pas de n'importe quoi : sans
       cette borne, `…[aria-pressed="true"]` mordrait sur
       `…[aria-pressed="true"]:disabled` et les deux regles se confondraient.
    🔴 Une regle qui ne se referme pas rend **VIDE**."""
    m = re.search(re.escape(selecteur) + r"\s*\{([^}]*)\}", style or "")
    return m.group(1) if m else ""


def declarations(corps):
    """Les declarations d'une regle, normalisees en `propriete:valeur`."""
    out = []
    for d in (corps or "").split(";"):
        if ":" not in d:
            continue
        p, v = d.split(":", 1)
        out.append((p.strip().lower(), re.sub(r"\s+", " ", v.strip().lower())))
    return out


def valeur(corps, prop):
    """La DERNIERE valeur declaree pour une propriete, ou `None`."""
    v = None
    for p, x in declarations(corps):
        if p == prop:
            v = x
    return v


def fond_de(corps):
    """La valeur de fond declaree par une regle, ou `None`.

    ⚠️ `background: X` et `background-color: X` posent le meme aplat ; les
       confondre serait faux, les separer ferait rougir une redaction juste."""
    for prop in PROPS_FOND:
        v = valeur(corps, prop)
        if v is not None:
            return v
    return None


def appels_ranges(corps, nom):
    """Chaque appel de `nom(` : ses ARGUMENTS, et la position OU IL SE FERME.

    Rend une liste de `(arguments, fin)` — les arguments sont le texte brut,
    decoupe aux virgules de PREMIER niveau (guillemets et parentheses suivis).
    ⚠️ Un appel dont la parenthese ne se referme pas est IGNORE — ⛔ jamais
       « tout ce qui suit ».
    🔴 LA CLE D'UNE FABRIQUE EST SON **N-IEME ARGUMENT**, ⛔ pas « tout ce qui
       suit la premiere virgule » : `blocMot` en prend un TROISIEME (le
       suffixe), et un motif qui avale la parenthese entiere confondrait la cle
       avec le couple cle+suffixe.
    """
    out = []
    i = 0
    motif = nom + "("
    corps = corps or ""
    while True:
        j = corps.find(motif, i)
        if j < 0:
            return out
        # ⛔ UN APPEL, ⛔ PAS UNE FIN DE NOM : `xconsoleRefus(` n'est pas
        #    `consoleRefus(`.
        if j and (corps[j - 1].isalnum() or corps[j - 1] in "_$."):
            i = j + len(motif)
            continue
        k = j + len(motif)
        prof, args, cour, quote = 1, [], "", ""
        while k < len(corps):
            c = corps[k]
            if quote:
                if c == "\\":
                    cour += corps[k:k + 2]
                    k += 2
                    continue
                if c == quote:
                    quote = ""
            elif c in "\"'":
                quote = c
            elif c in "([{":
                prof += 1
            elif c in ")]}":
                prof -= 1
                if prof == 0:
                    break
            elif c == "," and prof == 1:
                args.append(cour.strip())
                cour = ""
                k += 1
                continue
            cour += c
            k += 1
        if k >= len(corps):
            return out                    # parenthese non refermee ⇒ IGNORE
        if cour.strip() or args:
            args.append(cour.strip())
        out.append((args, k + 1))
        i = k + 1


def appels(corps, nom):
    """Les ARGUMENTS de chaque appel, sans les positions."""
    return [a for a, _ in appels_ranges(corps, nom)]


# ═══════════════════════ (a)…(e) — LA PLACE DU VERDICT ═════════════════════

def place_origine_memorisee(js):
    """(a) La place d'origine est-elle LUE dans le document, et RELUE ?

    🔴 UN `appendChild` VERS UN IDENTIFIANT ECRIT EN JAVASCRIPT SERAIT UNE
       SECONDE DEFINITION de la place de `#sortie`, qui divergerait de celle du
       HTML a la premiere reorganisation. ⇒ le document est la seule source."""
    m_p = re.search(r"var (\w+)\s*=\s*[^;\n]*\.parentNode[^;\n]*;", js or "")
    m_f = re.search(r"var (\w+)\s*=\s*[^;\n]*\.nextSibling[^;\n]*;", js or "")
    if not m_p or not m_f:
        return False, ("la place d'origine n'est LUE nulle part : "
                       "parentNode=%s · nextSibling=%s"
                       % (bool(m_p), bool(m_f)))
    i_fn = (js or "").find("function %s(" % NOM_MONTRER)
    if i_fn < 0:
        return False, "`%s` est introuvable" % NOM_MONTRER
    if m_p.start() > i_fn or m_f.start() > i_fn:
        return False, "la lecture de la place vit APRES `%s`" % NOM_MONTRER
    corps = corps_fonction(js, NOM_MONTRER)
    absents = [n for n in (m_p.group(1), m_f.group(1)) if n not in corps]
    if absents:
        return False, ("`%s` ⛔ ne relit pas : %s"
                       % (NOM_MONTRER, " ".join(absents)))
    return True, ("`%s` et `%s`, lus au document et relus"
                  % (m_p.group(1), m_f.group(1)))


def le_deplacement_precede_la_revelation(js):
    """(b) Le bloc est-il DEPLACE avant d'etre revele ?

    ⛔ Reveler d'abord ferait apparaitre le transcript a son ANCIENNE place,
       puis sauter — le saut meme que ce correctif existe pour supprimer."""
    corps = corps_fonction(js, NOM_MONTRER)
    if not corps:
        return False, "`%s` est introuvable" % NOM_MONTRER
    poses = [m.start() for m in re.finditer(r"\.insertBefore\(", corps)]
    i_rev = corps.find("hidden = false")
    if len(poses) < 2:
        return False, ("%d relocalisation(s) : il en faut DEUX — sous l'ancre, "
                       "et le retour a la maison" % len(poses))
    if i_rev < 0:
        return False, "le bloc n'est revele nulle part"
    if max(poses) > i_rev:
        return False, "le bloc est REVELE avant d'etre deplace"
    return True, "2 relocalisations, toutes AVANT la revelation"


def les_trois_ecritures_passent_leur_bouton(js):
    """(c) Dans `jouer`, les TROIS ecritures passent-elles leur bouton ?

    🔴 C'EST LA FORME EXACTE SOUS LAQUELLE LE DEFAUT A SURVECU A `dn7-2-2` :
       un seul site d'appel qui perd son ancre suffit a rendre un verdict hors
       champ, et le reste de la page continue de bien se comporter."""
    corps = corps_fonction(js, NOM_JOUER)
    if not corps:
        return False, "`%s` est introuvable" % NOM_JOUER
    params = signature(js, NOM_JOUER)
    if len(params) < 2:
        return False, "`%s` ne recoit pas son bouton" % NOM_JOUER
    ancre = params[-1]
    nus = []
    sites = 0
    for args in appels(corps, NOM_MONTRER):
        sites += 1
        if len(args) != 1 or args[0] != ancre:
            nus.append("%s(%s)" % (NOM_MONTRER, ", ".join(args) or ""))
    for args in appels(corps, NOM_ECRIRE_MOT):
        sites += 1
        if len(args) != 3 or args[-1] != ancre:
            nus.append("%s(%s)" % (NOM_ECRIRE_MOT, ", ".join(args) or ""))
    if sites != 3:
        return False, "%d site(s) d'ecriture au lieu de TROIS" % sites
    if nus:
        return False, "site(s) SANS ancre : %s" % " · ".join(nus[:2])
    return True, "3 sites, tous ancres sur `%s`" % ancre


def la_fabrique_transmet_son_ancre(js):
    """(d) `ecrireMot` transmet-il son ancre, ⛔ ou l'avale-t-il ?"""
    params = signature(js, NOM_ECRIRE_MOT)
    if len(params) != 3:
        return False, ("`%s` declare %d parametre(s) : l'ancre n'y est pas"
                       % (NOM_ECRIRE_MOT, len(params)))
    corps = corps_fonction(js, NOM_ECRIRE_MOT)
    for args in appels(corps, NOM_MONTRER):
        if args == [params[-1]]:
            return True, "`%s` ⇒ `%s(%s)`" % (NOM_ECRIRE_MOT, NOM_MONTRER,
                                              params[-1])
    return False, ("`%s` recoit `%s` et ⛔ ne le passe pas"
                   % (NOM_ECRIRE_MOT, params[-1]))


def un_fait_de_page_n_a_pas_de_bouton(js):
    """(e) L'ancre de `rafraichirEtat` suit-elle le FAIT, ⛔ pas la fonction ?

    🔴 DEUX APPELS, DEUX FAITS DIFFERENTS, ET C'EST MESURE :
       · AU DEMARRAGE, personne n'a clique. `sortie.pas-de-serveur` est un fait
         de PAGE : il part SANS ancre, et le transcript revient a sa place.
         L'attribuer au dernier bouton publierait une CAUSE FAUSSE.
       · DEPUIS `jouer`, le rafraichissement fait PARTIE du clic. Sans ancre, un
         verbe REUSSI dont le rafraichissement echoue ensuite voyait son verdict
         ECRASE **et renvoye quatre gestes plus bas** — le defaut que cette
         marche ferme, recree sur le clic qui vient de le fermer.
    ⛔ ET CE CONTROLE NE PASSE PAS **A VIDE** : sans parametre d'ancre sur
       `rafraichirEtat`, il n'y a rien a suivre, et il refuse de conclure."""
    params = signature(js, NOM_RAFRAICHIR)
    if not params:
        return False, ("`%s` ne declare aucune ancre : ce controle passerait "
                       "A VIDE" % NOM_RAFRAICHIR)
    anc = params[0]
    corps = corps_fonction(js, NOM_RAFRAICHIR)
    if not corps:
        return False, "`%s` est introuvable" % NOM_RAFRAICHIR
    ecr = appels(corps, NOM_ECRIRE_MOT)
    if not ecr:
        return False, "`%s` n'ecrit rien dans le transcript" % NOM_RAFRAICHIR
    mal = [a for a in ecr if len(a) != 3 or a[-1] != anc]
    if mal:
        return False, ("l'ecriture de page ⛔ ne passe pas son ancre : %s"
                       % ", ".join(mal[0]))
    # ⛔ LA DECLARATION N'EST PAS UN APPEL : sans ce masque, `function
    #    rafraichirEtat(ancre)` compterait pour un appel ancre.
    sans_decl = re.sub(r"function\s+%s\(" % re.escape(NOM_RAFRAICHIR),
                       "function _decl_(", js or "")
    tous = appels(sans_decl, NOM_RAFRAICHIR)
    nus = [a for a in tous if not a]
    ancres = [a for a in tous if a]
    if not nus:
        return False, ("⛔ AUCUN appel nu : le fait de PAGE serait attribue a "
                       "un bouton que personne n'a clique")
    dans_jouer = appels(corps_fonction(js, NOM_JOUER), NOM_RAFRAICHIR)
    if not dans_jouer:
        return False, "`%s` ne repose pas l'etat : rien a ancrer" % NOM_JOUER
    bouton = (signature(js, NOM_JOUER) or ["?"])[-1]
    sourds = [a for a in dans_jouer if a != [bouton]]
    if sourds:
        return False, ("`%s` repose l'etat SANS son bouton : %s(%s)"
                       % (NOM_JOUER, NOM_RAFRAICHIR, ", ".join(sourds[0])))
    if len(ancres) != len(dans_jouer):
        return False, ("%d appel(s) ancre(s) HORS de `%s`"
                       % (len(ancres) - len(dans_jouer), NOM_JOUER))
    return True, ("%d appel nu (demarrage) · %d ancre(s) depuis `%s`"
                  % (len(nus), len(dans_jouer), NOM_JOUER))


# ═══════════════════════ (f)…(i) — LE REFUS EXACT ══════════════════════════

def refus_enregistre(js):
    """(f) `consoleRefus` enregistre-t-il sa cle, et les TROIS sites y
    passent-ils ?"""
    corps = corps_fonction(js, NOM_REFUS)
    if not corps:
        return None, "`%s` est introuvable" % NOM_REFUS
    params = signature(js, NOM_REFUS)
    if not params:
        return None, "`%s` ne recoit aucune cle" % NOM_REFUS
    m = re.search(r"(\w+)\s*=\s*%s\s*;" % re.escape(params[0]), corps)
    if not m:
        return None, ("`%s` ⛔ n'ENREGISTRE pas la cle qu'il vient de nommer"
                      % NOM_REFUS)
    nom = m.group(1)
    i_decl = re.search(r"var %s\s*=\s*null\s*;" % re.escape(nom), js or "")
    i_fn = (js or "").find("function %s(" % NOM_REFUS)
    if not i_decl or i_decl.start() > i_fn:
        return None, "`%s` n'est pas declare au niveau du module" % nom
    ouvrir = corps_fonction(js, NOM_OUVRIR)
    if not ouvrir:
        return None, "`%s` est introuvable" % NOM_OUVRIR
    vus = []
    for args in appels(ouvrir, NOM_REFUS):
        if args:
            vus.append(args[0].strip('"\''))
    manquantes = [c for c in CLES_REFUS if c not in vus]
    if manquantes or len(vus) != len(CLES_REFUS):
        return None, ("%d refus nomme(s) sur %d ; absent(s) : %s"
                      % (len(vus), len(CLES_REFUS),
                         " ".join(manquantes) or "—"))
    return nom, "`%s` retenu, et les %d refus y passent" % (nom, len(vus))


def l_oubli_precede_le_chemin_du_port(js, nom):
    """(g) La tentative efface-t-elle le refus AU DEBUT, ⛔ pas a la fin ?

    🔴 UN REFUS RELAYE APRES COUP EST UN FAIT **D'UN AUTRE TIR**. L'effacement
       a l'ouverture rend le lien CAUSAL : ce qui remonte a ete nomme PENDANT
       cette tentative-ci."""
    corps = corps_fonction(js, NOM_POSE)
    if not corps:
        return False, "`%s` est introuvable" % NOM_POSE
    # Les fonctions du module qui REMETTENT le temoin a zero.
    oublieuses = []
    for m in re.finditer(r"function (\w+)\([^)]*\) \{(.*?)\n\}", js or "", re.S):
        if re.search(r"\b%s\s*=\s*null\s*;" % re.escape(nom), m.group(2)):
            oublieuses.append(m.group(1))
    positions = [m.start() for m in
                 re.finditer(r"\b%s\s*=\s*null\s*;" % re.escape(nom), corps)]
    for f in oublieuses:
        positions += [m.start() for m in
                      re.finditer(r"\b%s\s*\(" % re.escape(f), corps)]
    if not positions:
        return False, ("`%s` ⛔ n'efface JAMAIS le refus enregistre" % NOM_POSE)
    i_port = corps.find("%s(" % NOM_OUVRIR)
    if i_port < 0:
        return False, "`%s` n'ouvre aucun chemin de port" % NOM_POSE
    if min(positions) > i_port:
        return False, "l'effacement vient APRES le chemin du port"
    return True, "efface avant `%s(`" % NOM_OUVRIR


def le_repli_est_un_repli(js, nom):
    """(h) Le refus enregistre passe-t-il D'ABORD, la supposition EN REPLI ?

    ⚠️ `langue.port-indisponible` ⛔ NE DISPARAIT PAS : elle reste le message du
       SEUL cas ou sa phrase est VRAIE — le retour MUET de `consoleOuvrir()`.
       ⇒ le controle RETRECIT un domaine, il ⛔ n'exige pas une suppression."""
    corps = region(corps_fonction(js, NOM_POSE),
                   OUVRANT_SANS_PORT, FERMANT_SANS_PORT)
    if not corps:
        return False, "la fenetre de `sansPort` ne se referme pas"
    i_repli = -1
    i_exact = -1
    # ⚠️ LA CLE EST LE **DEUXIEME** ARGUMENT, ⛔ pas « tout ce qui suit la
    #    virgule » : `blocMot` en prend un TROISIEME (le suffixe), et un motif
    #    qui avale la parenthese entiere confondrait la cle avec le couple.
    for args, i in appels_ranges(corps, "blocMot"):
        if len(args) < 2 or args[0].strip('"\'') != BLOC_LANGUE:
            continue
        cle = args[1].strip()
        if cle == '"%s"' % CLE_REPLI:
            i_repli = i if i_repli < 0 else i_repli
        elif cle == nom:
            i_exact = i if i_exact < 0 else i_exact
    if i_exact < 0:
        return False, "le refus enregistre n'est JAMAIS relaye au geste"
    if i_repli < 0:
        return False, ("`%s` a DISPARU : son cas residuel resterait MUET"
                       % CLE_REPLI)
    if i_exact > i_repli:
        return False, "la supposition passe AVANT le fait exact"
    i_test = -1
    for m in re.finditer(r"if\s*\(([^)]*)\)", corps):
        if nom in m.group(1):
            i_test = m.start()
            break
    if i_test < 0 or i_test > i_exact:
        return False, "le relais du refus n'est garde par AUCUN test"
    return True, "fait exact d'abord, supposition EN REPLI"


def une_cle_pour_un_fait(js, nom):
    """(i) La cle remise au cadre et celle remise au port sont-elles LA MEME ?

    ⛔ Deux cles pour un fait feraient dessiner le cadre sur une issue et
       ecrire le texte sur une autre."""
    corps = region(corps_fonction(js, NOM_POSE),
                   OUVRANT_SANS_PORT, FERMANT_SANS_PORT)
    if not corps:
        return False, "la fenetre de `sansPort` ne se referme pas"
    paires = 0
    desaccords = []
    for args, i in appels_ranges(corps, "blocMot"):
        if len(args) < 2 or args[0].strip('"\'') != BLOC_LANGUE:
            continue
        cle = args[1].strip()
        suite = corps[i:i + 220]
        p = appels(suite, "languePort")
        if not p or not p[0]:
            desaccords.append("%s ⇒ le port n'est pas dit" % cle)
        elif p[0][0].strip() != cle:
            desaccords.append("%s ⇒ %s" % (cle, p[0][0].strip()))
        else:
            paires += 1
    if desaccords:
        return False, " · ".join(desaccords[:2])
    if paires < 1:
        return False, "⛔ aucun couple cadre ⇄ port dans `sansPort`"
    return True, "%d couples, meme cle des deux cotes" % paires


# ═══════════════════════ (j)…(m) — LA SELECTION ════════════════════════════

def l_etat_pose_un_fond(style):
    """(j) Les DEUX selecteurs posent-ils un APLAT sur leur position active ?

    🔴 ET « UN FOND » NE SUFFIT PAS : IL DOIT DIFFERER DU FOND DE REPOS.
       MESURE du 2026-09-10 — `background: var(--dn-fond)` est **le fond que
       `button` porte deja** : une position active peinte avec lui est peinte
       EXACTEMENT comme une position NON selectionnee, et le controle sortait
       VERT dessus. ⇒ le fond de repos est **LU dans la page** (regle `button`),
       ⛔ pas ecrit ici, et l'egalite est un KO."""
    repos = fond_de(bloc_regle(style, SEL_REPOS))
    if repos is None:
        return False, ("`%s` ne declare aucun fond : ⛔ rien a confronter"
                       % SEL_REPOS)
    sans, plats, jumeaux = [], [], []
    for s in SEL_ACTIF:
        corps = bloc_regle(style, s)
        if not corps:
            sans.append(s)
            continue
        f = fond_de(corps)
        if f is None or f in FONDS_NULS:
            plats.append("%s ⇒ %s" % (s, f or "aucun fond"))
        elif f == repos:
            jumeaux.append("%s ⇒ %s" % (s, f))
    if sans:
        return False, "regle(s) ABSENTE(S) : %s" % " · ".join(sans)
    if plats:
        return False, "sans aplat : %s" % " · ".join(plats)
    if jumeaux:
        return False, ("fond IDENTIQUE au repos de `%s` (%s) : %s"
                       % (SEL_REPOS, repos, " · ".join(jumeaux)))
    return True, ("%d regles d'etat, fond ⛔ different du repos (%s)"
                  % (len(SEL_ACTIF), repos))


def l_etat_ne_ressemble_plus_au_survol(style):
    """(k) La regle d'etat DIFFERE-T-ELLE du jeu de declarations du survol ?

    🔴 LE CONTROLE COMPARE LES DEUX REGLES, ⛔ il ne cherche pas une chaine :
       c'est l'EGALITE de leurs declarations qui rendait « selectionne » et
       « survole » indiscernables, et une egalite ne se voit qu'en confrontant."""
    survol = declarations(bloc_regle(style, SEL_SURVOL))
    if not survol:
        return False, "`%s` est introuvable : ⛔ rien a confronter" % SEL_SURVOL
    jumelles = []
    for s in SEL_ACTIF:
        d = declarations(bloc_regle(style, s))
        if not d:
            return False, "regle d'etat ABSENTE : %s" % s
        if set(d) == set(survol):
            jumelles.append(s)
    if jumelles:
        return False, ("MEME jeu que le survol : %s" % " · ".join(jumelles))
    return True, "%d declaration(s) au survol, ⛔ aucune regle identique" % len(survol)


def l_actif_desarme_est_ecrit(style):
    """(l) Le cas ACTIF + DESARME est-il ecrit EXPLICITEMENT, ET ENTIER ?

    🔴 LE PIEGE DE SPECIFICITE, MESURE ET CORRIGE LE 2026-09-10 : la regle
       d'aplat pese `(1,1,1)`, `button:disabled` pese `(0,1,1)` et
       `button:hover:enabled` `(0,2,1)`. ⚠️ Cette docstring ecrivait ~~`0,2,0`~~
       pour `button:disabled` — le chiffre etait FAUX, ⛔ il n'est pas efface, et
       **la conclusion est INCHANGEE** : `(1,1,1)` l'emporte sur les deux.
    ⇒ TOUTES les declarations que `button:disabled` porte doivent etre
      REECRITES : la BORDURE autant que le TEXTE. MESURE : retirer la seule
      `border-color` des deux regles laissait la gate verte pendant qu'un bouton
      grise gardait sa bordure d'ACCENT — le prejudice exact que ce controle dit
      exister pour empecher.
    🔴 ET LE DESARME RESTE **DISTINGUABLE D'UNE POSITION INACTIVE** : lui donner
       le fond de repos rendrait la langue choisie INVISIBLE pendant que le
       geste est en vol — une REGRESSION de ce correctif meme, puisque la regle
       `(1,1,1)` distinguait au moins les deux teintes avant lui."""
    desarme = bloc_regle(style, SEL_DESARME)
    eteint = valeur(desarme, "color")
    trait = valeur(desarme, "border-color")
    repos = fond_de(bloc_regle(style, SEL_REPOS))
    if eteint is None or trait is None:
        return False, ("`%s` ne declare pas texte ET bordure : ⛔ rien a "
                       "confronter" % SEL_DESARME)
    manques = []
    for s, a in zip(SEL_ACTIF_DESARME, SEL_ACTIF):
        corps = bloc_regle(style, s)
        if not corps:
            manques.append("%s ⇒ ABSENTE" % s)
            continue
        if valeur(corps, "color") != eteint:
            manques.append("%s ⇒ texte %s au lieu de %s"
                           % (s, valeur(corps, "color"), eteint))
        if valeur(corps, "border-color") != trait:
            manques.append("%s ⇒ bordure %s au lieu de %s"
                           % (s, valeur(corps, "border-color"), trait))
        f = fond_de(corps)
        if f == fond_de(bloc_regle(style, a)):
            manques.append("%s ⇒ garde l'aplat de la position active" % s)
        elif f is None or f == repos:
            manques.append("%s ⇒ fond %s : ⛔ indiscernable d'une position "
                           "INACTIVE desarmee" % (s, f or "aucun"))
    if manques:
        return False, " · ".join(manques[:2])
    return True, "2 regles desarmees : texte %s, bordure %s" % (eteint, trait)


def aucune_couleur_neuve(style):
    """(m) Les QUATRE regles n'emploient-elles QUE des jetons declares ?

    ⛔ L'egalite page ⇄ `IDENTITE.md` DANS LES DEUX SENS reste gardee par
       `(c19)` de `tools/verif_installeur_dn71.py` — elle n'est ⛔ pas refaite
       ici. Ce controle-ci refuse qu'une couleur NUE entre par la porte que
       cette marche vient d'ouvrir, et il ⛔ ne passe pas a vide : il exige que
       les quatre regles EXISTENT, sans quoi il ne juge rien."""
    declares = set(RE_JETON_DECLARE.findall(region(style, ":root {", "}")))
    if not declares:
        return False, "⛔ aucun jeton declare dans `:root` : rien a confronter"
    absentes, nues, inconnus, jetons = [], [], [], 0
    for s in SEL_ACTIF + SEL_ACTIF_DESARME:
        corps = bloc_regle(style, s)
        if not corps:
            absentes.append(s)
            continue
        vus = RE_HEX.findall(corps)
        if vus:
            nues.append("%s ⇒ %s" % (s, " ".join(sorted(set(vus)))))
            continue
        for p, v in declarations(corps):
            if p not in PROPS_COULEUR:
                continue
            if not RE_JETON.fullmatch(v):
                nues.append("%s ⇒ %s: %s" % (s, p, v))
                continue
            jetons += 1
            nom = RE_NOM_JETON.search(v).group(1)
            if nom not in declares:
                inconnus.append("%s ⇒ %s: %s" % (s, p, nom))
    if absentes:
        return False, ("regle(s) ABSENTE(S) : %s — ⛔ rien a juger"
                       % " · ".join(absentes[:2]))
    if nues:
        return False, "valeur(s) HORS jeton : %s" % " · ".join(nues[:2])
    if inconnus:
        return False, ("jeton(s) ⛔ NON DECLARE(S) dans `:root` : %s — une "
                       "coquille de NOM disparait EN SILENCE au rendu, et "
                       "`(c19)` de `dn7-1` ne lit que des `#rrggbb`"
                       % " · ".join(inconnus[:2]))
    return True, "%d regles, %d valeur(s), %d jeton(s) declare(s)" % (
        len(SEL_ACTIF) + len(SEL_ACTIF_DESARME), jetons, len(declares))


# ═══════════════════════════ LES MUTANTS ═══════════════════════════════════

def muter(etat):
    """REPLANTE une faute DANS L'ETAT — ⛔ jamais dans un fichier du depot.

    🔴 TOUTE mutation passe par cet unique etat, et le corps principal compare
       l'etat AVANT/APRES : la garde du no-op est donc UNIVERSELLE.
    ⚠️ MAIS ELLE N'EST ATTEINTE QUE SI LE CORPS **REND**. Un corps qui `split`,
       indexe ou depaquette sur une ancre disparue LEVE, et le `try` du corps
       principal le rend en `rc=1` + `BILAN` + `[KO ]` — MOT POUR MOT le
       contrat que la campagne appelle « sain » : un mutant PERIME passerait
       pour un gardien vivant. ⇒ tout corps VERIFIE son ancre d'abord et rend
       `e` INCHANGE. ⛔ Le mutant 18 leve EXPRES : il est le temoin de ce cas.
    ⛔ ET CHAQUE MUTANT **REPLANTE LA FAUTE**, ⛔ il ne debranche pas la garde :
       un mutant qui coupe le controle ne prouve que l'existence du controle.
    ⛔ AUCUN MUTANT NE POSE SON LITTERAL DANS UN COMMENTAIRE : les controles
       lisent le script SANS ses commentaires, et un mutant qui ferait rougir
       sur de la prose prouverait un `grep`, ⛔ pas une propriete."""
    e = copy.deepcopy(etat)
    p, r = e["fichiers"], e["regles"]
    t = p.get(PAGE, "")

    if _MUTANT == 1:
        a = ("var sortieParent = sortie ? sortie.parentNode : null;\n"
             "var sortieFrere = sortie ? sortie.nextSibling : null;")
        if a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(
            a, "var sortieParent = document.getElementById(\"sec-suite\");\n"
               "var sortieFrere = null;", 1)
    elif _MUTANT == 2:
        a = ("  sortie.hidden = false;\n"
             "  sortie.scrollTop = 0;")
        b = "  if (ancre && ancre.parentNode) {"
        if a not in t or b not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(a, "  sortie.scrollTop = 0;", 1).replace(
            b, "  sortie.hidden = false;\n" + b, 1)
    elif _MUTANT == 3:
        a = "      montrerSortie(bouton);"
        if a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(a, "      montrerSortie();", 1)
    elif _MUTANT == 4:
        a = "  montrerSortie(ancre);"
        if a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(a, "  montrerSortie();", 1)
    elif _MUTANT == 5:
        a = "  return rafraichirEtat().then(appliquerFlash);\n});"
        if a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(
            a, "  return rafraichirEtat(bStop).then(appliquerFlash);\n});", 1)
    elif _MUTANT == 6:
        a = "  consoleRefusNomme = cle;"
        if a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(a, "", 1)
    elif _MUTANT == 7:
        a = 'consoleRefus("console.aucun-port", " (" + String(err) + ")");'
        if a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(
            a, 'blocMot("etat-console", "console.aucun-port");', 1)
    elif _MUTANT == 8:
        a = ("  consoleOublierRefus();\n"
             "  var code = langueDalleChoisie();")
        if a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(a, "  var code = langueDalleChoisie();", 1)
    elif _MUTANT == 9:
        a = ("    if (consoleRefusNomme) {\n"
             "      blocMot(\"etat-langue\", consoleRefusNomme,"
             " consoleRefusSuffixe);\n"
             "      languePort(consoleRefusNomme);\n"
             "      return null;\n"
             "    }\n")
        if a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(a, "", 1)
    elif _MUTANT == 10:
        a = "      languePort(consoleRefusNomme);"
        if a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(
            a, '      languePort("langue.port-indisponible");', 1)
    elif _MUTANT == 11:
        # ⚠️ LA REGLE **ENTIERE** EST L'ANCRE, ⛔ pas son corps : les deux aplats
        #    sont TEXTUELLEMENT IDENTIQUES, et muter « le corps » toucherait le
        #    premier venu — un mutant qui vise a cote.
        corps = bloc_regle(style_de(t), SEL_ACTIF[0])
        a = SEL_ACTIF[0] + " {" + corps + "}"
        if not corps or a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        neuf = re.sub(r"\s*background:[^;]*;", "", corps, count=1)
        if neuf == corps:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(a, SEL_ACTIF[0] + " {" + neuf + "}", 1)
    elif _MUTANT == 12:
        corps = bloc_regle(style_de(t), SEL_ACTIF[1])
        survol = bloc_regle(style_de(t), SEL_SURVOL)
        a = SEL_ACTIF[1] + " {" + corps + "}"
        if not corps or not survol or a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(a, SEL_ACTIF[1] + " {" + survol + "}", 1)
    elif _MUTANT == 13:
        corps = bloc_regle(style_de(t), SEL_ACTIF_DESARME[1])
        if not corps:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        a = SEL_ACTIF_DESARME[1] + " {" + corps + "}"
        if a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(a, "", 1)
    elif _MUTANT == 14:
        a = "background: var(--dn-accent); color: var(--dn-fond)"
        if a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(a, "background: #a0d8ff; color: var(--dn-fond)", 1)
    elif _MUTANT == 15:
        # ⚠️ LA CIBLE EST **VIDEE**, ⛔ la cle n'est pas supprimee : supprimer la
        #    cle ferait AUSSI diverger `CIBLES` et `MUTANTS`, donc rougir (c16)
        #    — un mutant qui vise deux controles a la fois n'en garde bien
        #    aucun. Vider la valeur orpheline le controle vise, et LUI SEUL.
        if not e["cibles"].get(9):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        e["cibles"][9] = ()
    elif _MUTANT == 16:
        if 1 not in e["cibles"]:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        e["cibles"][1] = ("c1", "c99")
    elif _MUTANT == 17:
        if 999 in e["cibles"]:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        e["cibles"][999] = ("c1",)
    elif _MUTANT == 18:
        # 🔴 LE TEMOIN DU MUTANT MORT : il LEVE EXPRES. Sans lui, « un corps qui
        #    leve se rend en KO » serait une regle ecrite que rien ne joue.
        raise RuntimeError("temoin : ce mutant LEVE, et c'est son objet")
    elif _MUTANT == 19:
        r["sortie_anticipee"] = True
    elif _MUTANT == 20:
        # 🔴 LE LEURRE **DANS UN COMMENTAIRE**, ⛔ pas a cote : la vraie regle
        #    redevient le jeu du survol, et l'aplat n'existe plus que dans de la
        #    prose. Une gate qui lit les commentaires sort VERTE dessus.
        corps = bloc_regle(style_de(t), SEL_ACTIF[0])
        survol = bloc_regle(style_de(t), SEL_SURVOL)
        a = SEL_ACTIF[0] + " {" + corps + "}"
        if not corps or not survol or a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(
            a, "/* " + a + " */\n  " + SEL_ACTIF[0] + " {" + survol + "}", 1)
    elif _MUTANT == 21:
        a = "background: var(--dn-accent); color: var(--dn-fond)"
        if t.count(a) != 2:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(
            a, "background: var(--dn-fond); color: var(--dn-accent)")
    elif _MUTANT == 22:
        a = DECL_DESARME
        if t.count(a) != 2:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(
            a, " { background: var(--dn-trait); color: var(--dn-eteint); }")
    elif _MUTANT == 23:
        a = DECL_DESARME
        if t.count(a) != 2:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(
            a, " { border-color: var(--dn-trait); background: var(--dn-fond);"
               " color: var(--dn-eteint); }")
    elif _MUTANT == 24:
        a = "background: var(--dn-accent)"
        if a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(a, "background: var(--dn-accnt)", 1)
    elif _MUTANT == 25:
        a = "return rafraichirEtat(bouton).then(appliquerFlash);"
        if a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(
            a, "return rafraichirEtat().then(appliquerFlash);", 1)
    else:
        raise AssertionError("mutant %d declare mais SANS CORPS" % _MUTANT)
    return e


# ═══════════════════════════ LA RECIPROQUE ═════════════════════════════════

def _texte_litteral(n):
    """La partie LITTERALE d'un libelle, meme construit par formatage."""
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Mod, ast.Add)):
        return _texte_litteral(n.left)
    if isinstance(n, ast.JoinedStr) and n.values:
        return _texte_litteral(n.values[0])
    return None


def ids_par_ast():
    """Les identifiants de TOUS les controles de CE fichier, lus A L'AST.

    🔴 POURQUOI PAS L'ENSEMBLE DES IDENTIFIANTS DEJA EMIS : cet ensemble est
       fige AU MOMENT DE L'APPEL de la reciproque. Tout controle ajoute APRES
       ce bloc en sortirait INVISIBLE."""
    try:
        with io.open(os.path.abspath(__file__), encoding="utf-8") as fh:
            arbre = ast.parse(fh.read())
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    out = set()
    for n in ast.walk(arbre):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "ctrl" and len(n.args) >= 2):
            m = RE_ID_CTRL.match(_texte_litteral(n.args[1]) or "")
            if m:
                out.add(m.group(1))
    return out or None


def main():
    global _MUTANT
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--mutant", type=int, default=None,
                    help="REPLANTE une faute EN MEMOIRE pour prouver que le "
                         "controle correspondant sait ROUGIR")
    ap.add_argument("--liste-mutants", action="store_true",
                    help="dit ce que chaque mutant replante, et sort")
    args = ap.parse_args()
    if args.mutant is not None and args.mutant not in MUTANTS:
        # ⛔ PAS une sortie par exception, qui rendrait 1 et se confondrait
        #    avec un vrai defaut : un mutant inconnu est une ERREUR D'APPEL.
        print("MUTANT %d INCONNU : il n'est pas declare. ⛔ Un mutant qui "
              "n'existe pas ne prouve RIEN — ⛔ ne pas conclure que le "
              "controle est vert." % args.mutant, file=sys.stderr)
        return 2
    _MUTANT = args.mutant or 0

    if args.liste_mutants:
        for n in sorted(MUTANTS):
            print("  %2d  [%s]  %s"
                  % (n, ",".join(CIBLES.get(n, ())) or "—", MUTANTS[n]))
        return 0

    print("=" * 78)
    print("dn7-4 — LA PAGE DIT LE VRAI LA OU L'ŒIL EST"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)
    print("cibles     : %s" % " · ".join(FIXES))
    print("⛔ CETTE GATE EST STRUCTURELLE : elle N'EXECUTE PAS le JavaScript de")
    print("   la page et ne dessine RIEN. Elle prouve que le MECANISME EST")
    print("   BRANCHE, ⛔ pas que l'œil le voit. `AC7.4.3` se ferme A L'ŒIL DE")
    print("   L'OWNER, avec le releve `mesures/dn7-4/T2` cote Windows.")

    # ── (c0) LE PRE-VOL : LES FICHIERS SE LISENT ────────────────────────
    print("\n── (c0) LE PRE-VOL — ⛔ AUCUN CONTROLE SUR DU VIDE ────────────────")
    fichiers = {}
    illisibles = []
    for c in FIXES:
        x = lire(c)
        if x is None:
            illisibles.append(c)
        else:
            fichiers[c] = x
    if not ctrl(not illisibles, "(c0) tout fichier attendu est LISIBLE",
                "%d fichier(s) lus" % len(fichiers) if not illisibles
                else "⛔ ILLISIBLE(S) : %s" % " ".join(illisibles)):
        return bilan(1, "un fichier attendu est illisible")

    for n in sorted(MUTANTS):
        if not ctrl(bool(CIBLES.get(n)) and bool(MUTANTS.get(n)),
                    "(c0) le mutant %d a une CIBLE et un LIBELLE" % n,
                    "→ %s" % ",".join(CIBLES.get(n, ()))
                    if CIBLES.get(n) else "⛔ cible ou libelle manquant"):
            return bilan(1, "un mutant est declare a moitie")

    etat = {"fichiers": fichiers,
            "regles": {"sortie_anticipee": False},
            "cibles": dict(CIBLES)}

    # 🔴 UN MUTANT QUI MEURT SORTIRAIT EN TRACEBACK, SANS `BILAN` — or « pas
    #    de BILAN » est le discriminant d'une gate MORTE. ⇒ il se rend en KO.
    try:
        neuf = muter(etat) if _MUTANT else etat
    except Exception as exc:                              # noqa: BLE001
        ctrl(False, "(c0) le mutant %d a une CIBLE et un CORPS" % _MUTANT,
             "⛔ %s: %s — la faute est dans le MUTANT, ⛔ pas dans la gate"
             % (type(exc).__name__, str(exc)[:80]))
        return bilan(1, "le mutant %d n'a pas pu s'appliquer" % _MUTANT)
    if _MUTANT and neuf == etat:
        ctrl(False, "(c0) le mutant %d a bien un EFFET" % _MUTANT,
             "⛔ SANS EFFET — son ancre litterale a disparu de la cible. "
             "⛔ Ce n'est PAS un controle vert : rc=3, mutant PERIME.")
        return bilan(3, "le mutant %d n'a eu aucun effet" % _MUTANT)

    page = neuf["fichiers"].get(PAGE, "")
    regles = neuf["regles"]
    cibles = neuf["cibles"]
    style = style_de(page)
    # ⛔ CE QUI S'EXECUTE, ⛔ PAS CE QUI L'EXPLIQUE.
    js = sans_commentaires(region(page, "<script>", "</script>"))

    # ── (c1)…(c5) LA PLACE DU VERDICT EST MOBILE ────────────────────────
    print("\n── (c1)…(c5) LE VERDICT S'ECRIT SOUS LE BOUTON CLIQUE ────────────")
    ok, det = place_origine_memorisee(js)
    ctrl(ok, "(c1) la place d'origine est LUE, et RELUE", det if ok
         else "⛔ %s — une place recodee en JavaScript est une SECONDE "
              "definition, qui divergera du document" % det)

    ok, det = le_deplacement_precede_la_revelation(js)
    ctrl(ok, "(c2) le bloc est DEPLACE avant d'etre revele", det if ok
         else "⛔ %s — reveler d'abord le fait apparaitre a son ancienne "
              "place, puis sauter" % det)

    ok, det = les_trois_ecritures_passent_leur_bouton(js)
    ctrl(ok, "(c3) les 3 ecritures du verbe passent leur bouton", det if ok
         else "⛔ %s — un SEUL site sans ancre suffit : c'est la forme exacte "
              "sous laquelle le defaut a survecu a `dn7-2-2`" % det)

    ok, det = la_fabrique_transmet_son_ancre(js)
    ctrl(ok, "(c4) la fabrique TRANSMET son ancre", det if ok
         else "⛔ %s — une ancre avalee rend les trois appelants vains" % det)

    ok, det = un_fait_de_page_n_a_pas_de_bouton(js)
    ctrl(ok, "(c5) un fait de PAGE n'est ancre sur aucun bouton", det if ok
         else "⛔ %s — personne n'a clique : l'attribuer au dernier bouton "
              "serait publier une CAUSE FAUSSE" % det)

    # ── (c6)…(c9) LE REFUS EXACT REMONTE ────────────────────────────────
    print("\n── (c6)…(c9) LE FAIT EXACT REMONTE LA OU L'ŒIL EST ───────────────")
    nom, det = refus_enregistre(js)
    ctrl(nom is not None, "(c6) le refus nomme est ENREGISTRE", det
         if nom is not None
         else "⛔ %s — la console nomme deja ses trois refus ; sans "
              "enregistrement, le geste de langue n'a rien a relayer" % det)

    ok, det = (l_oubli_precede_le_chemin_du_port(js, nom) if nom
               else (False, "aucun temoin de refus a suivre"))
    ctrl(ok, "(c7) le refus est efface AU DEBUT de la tentative", det if ok
         else "⛔ %s — un refus relaye apres coup est un fait D'UN AUTRE TIR"
              % det)

    ok, det = (le_repli_est_un_repli(js, nom) if nom
               else (False, "aucun temoin de refus a suivre"))
    ctrl(ok, "(c8) la supposition n'est plus qu'un REPLI", det if ok
         else "⛔ %s — `%s` ⛔ ne disparait pas : elle reste le message du seul "
              "cas ou sa phrase est VRAIE" % (det, CLE_REPLI))

    ok, det = (une_cle_pour_un_fait(js, nom) if nom
               else (False, "aucun temoin de refus a suivre"))
    ctrl(ok, "(c9) une SEULE cle par fait, cadre et port", det if ok
         else "⛔ %s — deux cles feraient dessiner le cadre sur une issue et "
              "ecrire le texte sur une autre" % det)

    # ── (c10)…(c13) LA SELECTION SE VOIT ────────────────────────────────
    print("\n── (c10)…(c13) LA POSITION ACTIVE SE DESSINE EN APLAT ────────────")
    ok, det = l_etat_pose_un_fond(style)
    ctrl(ok, "(c10) les 2 selecteurs posent un APLAT quand actifs", det if ok
         else "⛔ %s — un contour d'une teinte voisine ne se distingue ni du "
              "repos ni du survol" % det)

    ok, det = l_etat_ne_ressemble_plus_au_survol(style)
    ctrl(ok, "(c11) l'etat DIFFERE du jeu de declarations du survol", det if ok
         else "⛔ %s — a declarations egales, survoler une position inactive "
              "la fait passer pour active" % det)

    ok, det = l_actif_desarme_est_ecrit(style)
    ctrl(ok, "(c12) le cas ACTIF + DESARME est ecrit explicitement", det if ok
         else "⛔ %s — la regle d'aplat pese `(1,1,1)`, `%s` pese `(0,1,1)` : "
              "sans ce cas ENTIER, un bouton grise se lit actionnable"
              % (det, SEL_DESARME))

    ok, det = aucune_couleur_neuve(style)
    ctrl(ok, "(c13) ⛔ aucun `#rrggbb` dans les regles ajoutees", det if ok
         else "⛔ %s — l'identite visuelle est STATUEE et ECRITE ; une couleur "
              "nue la contourne en une ligne" % det)

    if regles["sortie_anticipee"]:
        return bilan(0)

    # ── (c14)(c15)(c16) LA RECIPROQUE, MECANIQUE ────────────────────────
    print("\n── (c14)(c15)(c16) AUCUN CONTROLE GARDE PAR ZERO MUTANT ──────────")
    # 🔴 « N mutants, N vus rougir » prouve `mutant ⇒ rouge`, ⛔ JAMAIS
    #    `controle ⇒ couvert`. Les deux sens sont mesures, SEPAREMENT.
    lus_ast = ids_par_ast()
    reels = set(ids_emis) | (lus_ast or set())
    vises = set()
    for v in cibles.values():
        vises.update(v)
    nus = sorted(reels - vises, key=lambda s: (len(s), s))
    ctrl(not nus and lus_ast is not None,
         "(c14) chaque controle est vise par >= 1 mutant",
         "%d controle(s) lu(s) a l'AST, %d cible(s) declaree(s)"
         % (len(reels), len(vises)) if not nus and lus_ast is not None
         else ("⛔ %d CONTROLE(S) GARDE(S) PAR RIEN : %s"
               % (len(nus), " · ".join(nus)) if nus
               else "⛔ LA SOURCE NE S'ANALYSE PAS A L'AST — la population de "
                    "ce controle est INCONNUE, ⛔ pas vide"))
    perimees = sorted(vises - reels, key=lambda s: (len(s), s))
    ctrl(not perimees, "(c15) chaque cible de mutant est un controle REEL",
         "%d cible(s) confrontee(s)" % len(vises) if not perimees
         else "⛔ %d CIBLE(S) PERIMEE(S) : %s — un mutant qui vise un controle "
              "inexistant ⛔ ne garde rien"
              % (len(perimees), " · ".join(perimees)))
    orph = sorted(set(cibles) - set(MUTANTS))
    sans_cible = sorted(set(MUTANTS) - set(cibles))
    ctrl(not orph and not sans_cible,
         "(c16) `CIBLES` et `MUTANTS` se correspondent",
         "%d mutant(s), %d cible(s), cle a cle" % (len(MUTANTS), len(cibles))
         if not orph and not sans_cible
         else "⛔ cible(s) SANS mutant : %s · mutant(s) SANS cible : %s"
              % (orph or "—", sans_cible or "—"))

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : que l'œil VOIE quoi que ce")
    print("   soit. Elle prouve que le mecanisme est BRANCHE. Ce qui ferme")
    print("   `AC7.4.3` est le releve `mesures/dn7-4/T2`, cote Windows, et")
    print("   c'est l'ŒIL DE L'OWNER — ⛔ aucune gate de ce depot.")
    return bilan(1 if ko_total[0] else 0)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn6-1 — LA BOM NE PEUT PAS POURRIR EN SILENCE.

======================= CE QUE CETTE GATE FAIT, ET POURQUOI =================

`docs/bom.md` publie des prix. Un prix est ce qui se perime le plus vite dans
un depot, et il se perime SANS RIEN DIRE. La page a donc une regle : ⛔ AUCUN
PRIX SANS SA DATE ET SA SOURCE. Cette gate garde cette regle, et rien d'autre.

🔴 ELLE EXISTE PARCE QUE LE PRECEDENT DU DEPOT NE SUFFISAIT PAS. `dn5-1`
   verifiait une propriete de prose par une CAPTURE UNIQUE sous `mesures/`
   (`mesures/dn5-1/T4-comptage-clone-neuf.txt`). Une capture dit ce qui etait
   vrai LE JOUR OU ON A REGARDE ; elle ne dit rien du jour ou quelqu'un ajoute
   une ligne sans date. C'est exactement ce que `dn5-6` puis `dn4-47` ont paye
   deux fois — *« les campagnes de mutants cessent d'etre des captures
   uniques »*. ⇒ ici, la propriete est REJOUEE a chaque passe.

── ⛔ CE QU'ELLE NE FAIT PAS, ET C'EST LA MOITIE DU SUJET ──────────────────

⛔ **ELLE NE JUGE AUCUN PRIX.** Elle ne sait pas si 26,77 € est vrai, ni s'il
   l'est encore. Elle ne va sur AUCUN reseau. Un prix faux mais date et source
   la laisse VERTE — et c'est voulu : la verite d'un prix se verifie en
   rouvrant la source, ⛔ pas en relisant le fichier.
⛔ Elle ne dit rien du cablage, rien du firmware, et n'ouvre aucun port.
⛔ Elle ne lit AUCUN fichier hors de `docs/bom.md`.

── CE QU'ELLE GARDE, CONTROLE PAR CONTROLE ─────────────────────────────────

  (c1) le document EXISTE, n'est pas vide, et porte au moins une TABLE DE BOM
       — une table est « de BOM » quand son en-tete nomme lui-meme
       `Date du releve` ET `Source`. ⛔ Aucune table n'est reconnue par sa
       position : une table qui ne declare pas ses colonnes n'est pas gardee,
       et c'est ECRIT plutot que tu ;
  (c2) les DEUX paliers sont nommes LITTERALEMENT, aux noms de `D19` ;
  (c3) toute ligne de BOM portant un PRIX porte une DATE de releve ;
  (c4) ... et une URL SOURCE ;
  (c5) toute ligne SANS prix porte une DECLARATION dans sa colonne Prix —
       ⛔ le silence n'est pas une declaration, et `—` non plus ;
  (c6) `VL6180X` et `INA219` sont NOMMES, et ils le sont HORS des sections de
       palier — le controle joue DANS LES DEUX SENS : absents = defaut,
       ranges dans un palier = defaut ;
  (c7) chacun porte un MOTIF d'exclusion substantiel ;
  (c8) `dn4-41` est CITEE avec son STATUT et une DATE ⛔ au lieu d'etre
       affirmee acquise ;
  (c9) la page DECLARE si elle porte des liens affilies ;
  (c10) ⛔ AUCUN JALON CHIFFRE — decision owner du 2026-09-06. Ils sont sortis
       du perimetre ; le sujet est porte par `dn6-5`.

Sortie : `BILAN : n OK, m KO`, rc 0 si tout passe, 1 sinon.
Usage  : python3 tools/verif_bom_dn61.py [--mutant <n>] [--liste-mutants]
         `--mutant` REPLANTE UNE FAUTE EN MEMOIRE et doit faire ROUGIR.
         ⛔ Aucun fichier du depot n'est modifie — la substitution vit dans
         une chaine, et le fichier n'est ouvert qu'en LECTURE.

⚠️ **UN MUTANT QUI DEBRANCHE LA GARDE NE PROUVE QUE SON EXISTENCE.** Les
   mutants d'ici replantent la faute REELLE — une date qui disparait, une URL
   qui disparait, un palier renomme, un composant hors palier range DANS un
   palier, une citation d'etat remplacee par une affirmation, un jalon qui
   revient — et la gate doit la VOIR.
"""

import argparse
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F_BOM = os.path.join(RACINE, "docs", "bom.md")
BOM_REL = "docs/bom.md"

# Les deux paliers de D19. ⛔ Ce sont des NOMS, pas des descriptions : les
# ecrire ici en dur est le sujet du controle, ⛔ pas un raccourci.
PALIERS = ("DeskNode", "DeskNode + Ambiance")

RE_PRIX = re.compile(r"\d+[,.]\d{2}\s*(?:€|EUR)")
RE_DATE = re.compile(r"20\d{2}-\d{2}-\d{2}")
RE_URL = re.compile(r"https?://\S+")
# ⚠️ « non releve » est la SEULE formule qui vaut declaration. Une gate qui
#    accepterait « ⛔ » ou « ? » laisserait passer un trou decore.
RE_NON_RELEVE = re.compile(r"non\s+relev", re.I)

ok_total = [0]
ko_total = [0]

MUTANTS = {}                      # ⛔ AU NIVEAU MODULE — sinon `--liste-mutants`
MUTANTS[1] = ("retire la DATE de la 1re ligne de BOM qui porte un prix "
              "(un prix nu se perime sans le dire)")
MUTANTS[2] = ("retire l'URL SOURCE de la 1re ligne de BOM qui porte un prix")
MUTANTS[3] = ("vide la colonne Prix d'une ligne qui n'en a pas "
              "(le trou MUET, ⛔ plus la declaration)")
MUTANTS[4] = ("renomme le palier « DeskNode + Ambiance » en « DeskNode Pro »")
MUTANTS[5] = ("supprime la ligne INA219 "
              "(un composant du prototype absent SANS motif)")
MUTANTS[6] = ("vide le motif d'exclusion du VL6180X "
              "(present, mais sans le POURQUOI)")
MUTANTS[7] = ("remplace la citation d'etat de `dn4-41` par une affirmation "
              "acquise (statut et date retires)")
MUTANTS[8] = ("supprime la declaration de liens affilies")
MUTANTS[9] = ("reintroduit un JALON CHIFFRE, sorti du perimetre le 2026-09-06")
MUTANTS[10] = ("deplace l'INA219 DANS une table de palier "
               "(le mensonge dans l'autre sens)")
MUTANTS[11] = ("rend le document VIDE "
               "(une gate qui ne trouve rien ⛔ ne sort pas verte)")
# 🔴 LES SIX SUIVANTS SONT NES D'UNE MESURE, ⛔ PAS D'UNE INTUITION. La 1re
#    campagne a rendu **11 mutants sur 11 vus rougir** — et le controle de la
#    RECIPROQUE a montre que **cinq controles n'etaient gardes par RIEN** :
#    la table qui se declare, le palier 1, les DEUX sens du VL6180X, et la
#    presence meme de la citation `dn4-41`. « N vus rougir » prouve
#    `mutant ⇒ rouge`, ⛔ jamais `controle ⇒ couvert`.
MUTANTS[12] = ("retire `Date du releve` de l'en-tete d'une table "
               "(elle cesse de SE DECLARER table de BOM, et sort du controle)")
MUTANTS[13] = ("renomme le palier 1 « DeskNode » en « DeskNode Solo » "
               "⛔ sans toucher au palier 2")
MUTANTS[14] = ("supprime la ligne VL6180X (l'autre composant hors palier)")
MUTANTS[15] = ("deplace le VL6180X DANS une table de palier")
MUTANTS[16] = ("efface toute mention de `dn4-41` "
               "(le palier 1 redevient affirme sans source)")
MUTANTS[17] = ("retire la date de la SEULE fenetre de citation de `dn4-41` "
               "⛔ sans toucher aux autres dates du document")
# 🔴 LE JETON D'EXEMPTION EST UNE ECHAPPATOIRE — donc il se teste LUI AUSSI.
#    Sans ce mutant, n'importe qui refermerait (c1c) en posant un jeton VIDE
#    au-dessus d'une table a prix : l'exception doit rester FALSIFIABLE.
MUTANTS[18] = ("vide le MOTIF du jeton d'exemption "
               "(une exception sans motif ⛔ n'exempte RIEN)")
# ⚠️ Le mutant 12 n'en retire qu'UNE : deux tables restaient declarees, donc
#    (c1b) — « au moins une table se declare » — n'etait garde par RIEN. Il
#    faut les retirer TOUTES pour l'atteindre. Ecrit parce que la difference
#    entre « une » et « toutes » est exactement ce qui rendait le controle nu.
MUTANTS[19] = ("retire `Date du releve` de TOUTES les tables "
               "(⛔ plus AUCUNE table de BOM — la gate ne trouve plus sa cible)")
_MUTANT = 0


def ctrl(ok, libelle, detail=""):
    """UNE assertion, UNE ligne. ⛔ Aucun controle muet."""
    if ok:
        ok_total[0] += 1
    else:
        ko_total[0] += 1
    print("  [%s] %-58s %s" % ("OK " if ok else "KO ", libelle, detail))
    return ok


def bilan(rc):
    """⛔ TOUS LES CHEMINS DE SORTIE PASSENT ICI. Une gate qui sort sans
    `BILAN` est indiscernable d'une gate MORTE — et c'est precisement le
    discriminant que `verif_campagne_dn56.py` exige de chaque mutant."""
    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return rc


def cellules(ligne):
    """Les cellules d'une ligne de tableau markdown, bords retires."""
    return [c.strip() for c in ligne.strip().strip("|").split("|")]


def est_separateur(ligne):
    return bool(re.fullmatch(r"\|[\s:|-]+\|", ligne.strip()))


# 🔴 CE JETON EST L'EXCEPTION **FALSIFIABLE** — voir `toutes_les_tables()`.
#    Il porte un MOTIF, et un motif vide ne vaut pas exemption.
RE_EXEMPT = re.compile(r"<!--\s*⛔ PAS UNE TABLE DE BOM\s*:\s*(.+?)-->", re.S)


def toutes_les_tables(texte):
    """TOUTES les tables markdown du document, ⛔ pas seulement celles de BOM.

    Rend `[(entetes, [lignes], amont)]` ou `amont` est le texte des 3 lignes
    qui precedent la table — c'est la ou vit le jeton d'exemption.

    🔴 ELLE EXISTE PARCE QUE LA 1re REDACTION NE VOYAIT QUE LES TABLES DE BOM,
       ET C'ETAIT LE DEFAUT (mesure du 2026-09-06, mutant 12). Une table est
       « de BOM » quand son en-tete nomme `Date` ET `Source` — donc **retirer
       cet en-tete faisait SORTIR la table du controle**, avec ses lignes, et
       la gate restait **VERTE** : elle retrecissait sa propre population EN
       SILENCE. Le mutant 12 sortait `rc=0`, `18 OK, 0 KO`.
       ⇒ on regarde maintenant TOUTE table qui porte un PRIX, et on exige
         qu'elle soit **declaree** BOM **ou exemptee AVEC MOTIF**."""
    out = []
    lignes = texte.split("\n")
    i = 0
    while i < len(lignes) - 1:
        if (lignes[i].strip().startswith("|")
                and est_separateur(lignes[i + 1])):
            ent = cellules(lignes[i])
            corps = []
            j = i + 2
            while j < len(lignes) and lignes[j].strip().startswith("|"):
                corps.append(lignes[j])
                j += 1
            # ⚠️ SIX lignes, ⛔ pas trois : MESURE du 2026-09-06 — le jeton
            #    d'exemption tient sur 3 lignes PLUS la ligne vide qui le
            #    separe de la table, soit 4 au minimum. Une fenetre de 3 le
            #    ratait, et la gate rougissait sur une table LEGITIMEMENT
            #    exemptee. La fenetre est ECRITE ici plutot que devinee.
            out.append((ent, corps, "\n".join(lignes[max(0, i - 6):i])))
            i = j
            continue
        i += 1
    return out


def est_table_de_bom(entetes):
    """Une table SE DECLARE de BOM quand son en-tete nomme `Date` ET `Source`.
    ⛔ Aucune reconnaissance par position : la position se perime au premier
    paragraphe insere."""
    bas = [c.lower() for c in entetes]
    return any("date" in c for c in bas) and any("source" in c for c in bas)


def tables_de_bom(texte):
    """Les tables de BOM seules — `(entetes, [lignes])`."""
    return [(e, c) for e, c, _a in toutes_les_tables(texte)
            if est_table_de_bom(e)]


def colonne(entetes, motif):
    """L'index de la colonne dont l'en-tete contient `motif`, ou None."""
    for k, c in enumerate(entetes):
        if motif in c.lower():
            return k
    return None


def sections(texte):
    """Le document decoupe par titres `## `. Rend [(titre, corps)]."""
    out = []
    titre, corps = "(preambule)", []
    for l in texte.split("\n"):
        if l.startswith("## "):
            out.append((titre, "\n".join(corps)))
            titre, corps = l[3:].strip(), []
        else:
            corps.append(l)
    out.append((titre, "\n".join(corps)))
    return out


# ═══════════════════════════ LES MUTANTS ═══════════════════════════════════
# ⛔ Chacun REPLANTE une faute dans le TEXTE. Aucun ne debranche un controle,
#    aucun ne touche le disque : la substitution vit dans une chaine.

def _ligne_avec_prix(texte):
    """La 1re ligne de BOM portant un prix — la cible des mutants 1 et 2."""
    for _ent, corps in tables_de_bom(texte):
        for l in corps:
            if RE_PRIX.search(l):
                return l
    return None


def _ligne_sans_prix(texte):
    for _ent, corps in tables_de_bom(texte):
        for l in corps:
            if not RE_PRIX.search(l) and RE_NON_RELEVE.search(l):
                return l
    return None


def muter(texte):
    if not _MUTANT:
        return texte
    if _MUTANT == 1:
        l = _ligne_avec_prix(texte)
        return texte.replace(l, RE_DATE.sub("le jour du releve", l), 1)
    if _MUTANT == 2:
        l = _ligne_avec_prix(texte)
        return texte.replace(l, RE_URL.sub("(la source habituelle)", l), 1)
    if _MUTANT == 3:
        l = _ligne_sans_prix(texte)
        return texte.replace(l, RE_NON_RELEVE.sub("", l), 1)
    if _MUTANT == 4:
        return texte.replace("DeskNode + Ambiance", "DeskNode Pro")
    if _MUTANT == 5:
        return "\n".join(l for l in texte.split("\n") if "INA219" not in l)
    if _MUTANT == 6:
        out = []
        for l in texte.split("\n"):
            if "VL6180X" in l and l.strip().startswith("|"):
                c = cellules(l)
                c[-1] = "—"
                l = "| " + " | ".join(c) + " |"
            out.append(l)
        return "\n".join(out)
    if _MUTANT == 7:
        # ⚠️ CHIRURGICAL, ⛔ PAS UN SED GLOBAL. La 1re redaction faisait
        #    `RE_DATE.sub(...)` sur TOUT le document : elle rougissait AUSSI
        #    (c3) et (c8c), c'est-a-dire qu'elle synchronisait la faute et sa
        #    fixture. Un mutant qui casse trois choses n'en prouve aucune.
        return texte.replace("statut `in-progress`", "et elle est acquise")
    if _MUTANT == 12:
        return texte.replace("Date du relevé", "Quand", 1)
    if _MUTANT == 13:
        return texte.replace("« DeskNode »", "« DeskNode Solo »")
    if _MUTANT == 14:
        return "\n".join(l for l in texte.split("\n") if "VL6180X" not in l)
    if _MUTANT == 15:
        lignes = texte.split("\n")
        vl = next(l for l in lignes
                  if "VL6180X" in l and l.strip().startswith("|"))
        lignes.remove(vl)
        t = "\n".join(lignes)
        _e, corps = tables_de_bom(t)[0]
        return t.replace(corps[-1], corps[-1] + "\n" + vl, 1)
    if _MUTANT == 16:
        return texte.replace("dn4-41", "cette marche")
    if _MUTANT == 19:
        return texte.replace("Date du relevé", "Quand")
    if _MUTANT == 18:
        return RE_EXEMPT.sub("<!-- ⛔ PAS UNE TABLE DE BOM : -->", texte)
    if _MUTANT == 17:
        # La date DISPARAIT DE LA SEULE FENETRE que (c8) regarde — le reste du
        # document garde les siennes, sinon (c3) tomberait avec.
        m = re.search(r"`?dn4-41`?", texte)
        a, b = max(0, m.start() - 200), m.start() + 600
        return texte[:a] + RE_DATE.sub("recemment", texte[a:b]) + texte[b:]
    if _MUTANT == 8:
        return texte.replace("ne porte aucun lien affilié", "est ce qu'elle est")
    if _MUTANT == 9:
        return texte + ("\n\n⚠️ Jalons de reevaluation : 75 €, 250 €, "
                        "1 000 € et 5 000 €.\n")
    if _MUTANT == 10:
        # La ligne INA219 est DEPLACEE : retiree de sa table, reinjectee dans
        # la 1re table de BOM d'une section de palier.
        lignes = texte.split("\n")
        ina = next(l for l in lignes if "INA219" in l and l.strip().startswith("|"))
        lignes.remove(ina)
        t = "\n".join(lignes)
        _e, corps = tables_de_bom(t)[0]
        return t.replace(corps[-1], corps[-1] + "\n" + ina, 1)
    if _MUTANT == 11:
        return ""
    raise AssertionError("mutant %d declare mais SANS CORPS" % _MUTANT)


# ═══════════════════════════ LES CONTROLES ═════════════════════════════════

def main():
    global _MUTANT
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--mutant", type=int, default=None,
                    help="REPLANTE une faute EN MEMOIRE pour prouver que le "
                         "controle correspondant sait ROUGIR")
    ap.add_argument("--liste-mutants", action="store_true",
                    help="dit ce que chaque mutant replante, et sort")
    args = ap.parse_args()
    # ⛔ Un mutant qui n'existe pas ne prouve RIEN : il doit sortir en ERREUR,
    #    ⛔ jamais en vert. Une campagne pilotee sur une liste perimee compterait
    #    sinon un mutant INEXISTANT comme « vu rougir ».
    if args.mutant is not None and args.mutant not in MUTANTS:
        sys.exit("MUTANT %d INCONNU : il n'est pas declare. ⛔ Un mutant qui "
                 "n'existe pas ne prouve RIEN — ⛔ ne pas conclure que le "
                 "controle est vert." % args.mutant)
    _MUTANT = args.mutant

    if args.liste_mutants:
        for n in sorted(MUTANTS):
            print("  %2d  %s" % (n, MUTANTS[n]))
        return 0

    print("=" * 78)
    print("dn6-1 — LA BOM NE PEUT PAS POURRIR EN SILENCE"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)
    print("cible      : %s" % BOM_REL)
    print("⛔ CETTE GATE NE JUGE AUCUN PRIX — elle garde qu'un prix porte sa "
          "date et sa source.")

    # ── (c1) le document existe, n'est pas vide, et se declare ─────────────
    print("\n── (c1) LE DOCUMENT EXISTE ET PORTE UNE TABLE DE BOM ─────────────")
    if not os.path.isfile(F_BOM):
        ctrl(False, "le document d'achat existe",
             "⛔ %s est ABSENT — ⛔ pas de trace nue, un KO nomme" % BOM_REL)
        return bilan(1)
    with open(F_BOM, encoding="utf-8") as fh:
        texte = muter(fh.read())

    if not ctrl(bool(texte.strip()), "le document n'est pas vide",
                "%d caractere(s)" % len(texte.strip())):
        return bilan(1)
    tables = tables_de_bom(texte)
    if not ctrl(bool(tables),
                "au moins une table SE DECLARE table de BOM",
                "%d table(s) portant `Date` ET `Source` en en-tete" % len(tables)
                if tables else
                "⛔ AUCUNE — une table non declaree n'est gardee par RIEN"):
        return bilan(1)

    # ── (c1c) 🔴 AUCUNE TABLE A PRIX NE SORT DU CONTROLE EN SILENCE ────────
    #     Ne pas ecrire ce controle laissait la gate RETRECIR sa population :
    #     une table qui perd son en-tete `Date`/`Source` cessait d'etre lue,
    #     avec toutes ses lignes, et la gate restait VERTE (mutant 12).
    print("\n── (c1c) TOUTE TABLE A PRIX EST DECLAREE, OU EXEMPTEE AVEC MOTIF ──")
    orphelines = []
    for ent, corps, amont in toutes_les_tables(texte):
        if not any(RE_PRIX.search(l) for l in corps):
            continue
        if est_table_de_bom(ent):
            continue
        ex = RE_EXEMPT.search(amont)
        if not (ex and len(ex.group(1).strip()) >= 20):
            orphelines.append(" / ".join(ent)[:52])
    ctrl(not orphelines,
         "aucune table a prix hors du controle",
         "toutes declarees ou exemptees avec motif" if not orphelines
         else "⛔ %d TABLE(S) A PRIX NI DECLAREE(S) NI EXEMPTEE(S) : %s"
              % (len(orphelines), " · ".join(orphelines)))

    # ── (c2) les deux paliers, aux noms de D19 ─────────────────────────────
    print("\n── (c2) LES DEUX PALIERS SONT NOMMES LITTERALEMENT ───────────────")
    for p in PALIERS:
        ctrl(("« %s »" % p) in texte,
             "le palier « %s » est nomme" % p,
             "trouve" if ("« %s »" % p) in texte
             else "⛔ ABSENT — ⛔ un synonyme n'est pas un nom")

    # ── (c3)/(c4)/(c5) chaque ligne de BOM ─────────────────────────────────
    print("\n── (c3)(c4)(c5) CHAQUE LIGNE DE BOM REND SES COMPTES ─────────────")
    sans_date, sans_url, muettes, avec_prix, sans_prix = [], [], [], 0, 0
    for ent, corps in tables:
        i_prix = colonne(ent, "prix")
        for l in corps:
            c = cellules(l)
            cel = c[i_prix] if (i_prix is not None and i_prix < len(c)) else l
            nom = c[0][:34] if c else "?"
            if RE_PRIX.search(cel):
                avec_prix += 1
                if not RE_DATE.search(l):
                    sans_date.append(nom)
                if not RE_URL.search(l):
                    sans_url.append(nom)
            else:
                sans_prix += 1
                if not RE_NON_RELEVE.search(cel):
                    muettes.append(nom)

    ctrl(not sans_date, "toute ligne a prix porte sa DATE de releve",
         "%d ligne(s) a prix, toutes datees" % avec_prix if not sans_date
         else "⛔ SANS DATE : %s" % " · ".join(sans_date))
    ctrl(not sans_url, "toute ligne a prix porte son URL SOURCE",
         "%d ligne(s) a prix, toutes sourcees" % avec_prix if not sans_url
         else "⛔ SANS SOURCE : %s" % " · ".join(sans_url))
    ctrl(not muettes, "toute ligne SANS prix le DECLARE",
         "%d ligne(s) sans prix, toutes declarees" % sans_prix if not muettes
         else "⛔ MUETTE(S) : %s — le silence n'est pas une declaration"
              % " · ".join(muettes))

    # ── (c6)/(c7) le hors-palier, dans les DEUX sens ───────────────────────
    print("\n── (c6)(c7) LE HORS-PALIER EST NOMME, ET IL EST DEHORS ───────────")
    secs = sections(texte)
    corps_paliers = "\n".join(b for t, b in secs if t.startswith("Palier «"))
    for comp in ("VL6180X", "INA219"):
        ctrl(comp in texte, "%s est NOMME dans le document" % comp,
             "present" if comp in texte
             else "⛔ ABSENT — un composant du prototype absent SANS motif "
                  "ecrit est un defaut")
        ctrl(comp not in corps_paliers,
             "%s est HORS des sections de palier" % comp,
             "dehors" if comp not in corps_paliers
             else "⛔ RANGE DANS UN PALIER — il n'entre dans aucun palier V1")
        ligne = next((l for l in texte.split("\n")
                      if comp in l and l.strip().startswith("|")), None)
        motif = cellules(ligne)[-1] if ligne else ""
        ctrl(len(motif) >= 40, "%s porte un MOTIF d'exclusion" % comp,
             "%d caractere(s) de motif" % len(motif) if len(motif) >= 40
             else "⛔ motif VIDE OU CREUX (%d caractere(s))" % len(motif))

    # ── (c8) dn4-41 est CITEE, ⛔ pas affirmee acquise ──────────────────────
    print("\n── (c8) `dn4-41` EST CITEE AVEC SON ETAT ─────────────────────────")
    m = re.search(r"`?dn4-41`?", texte)
    fen = texte[max(0, m.start() - 200):m.start() + 600] if m else ""
    ctrl(m is not None, "la BOM cite la marche `dn4-41`",
         "citee" if m else "⛔ ABSENTE — le palier 1 serait affirme acquis")
    ctrl("in-progress" in fen, "elle cite son STATUT",
         "`in-progress`" if "in-progress" in fen
         else "⛔ le statut n'est pas cite dans la fenetre de la citation")
    d = RE_DATE.search(fen)
    ctrl(d is not None, "elle cite une DATE de relecture",
         d.group(0) if d else "⛔ aucune date — un statut sans date se perime")

    # ── (c9) la declaration d'affiliation ──────────────────────────────────
    print("\n── (c9) LA PAGE DECLARE SES LIENS AFFILIES ───────────────────────")
    decl = re.search(r"(ne porte aucun lien affilié|porte des liens affiliés)",
                     texte)
    ctrl(decl is not None, "la page DECLARE si elle porte des liens affilies",
         "« %s »" % decl.group(0) if decl
         else "⛔ AUCUNE declaration — ⛔ le silence ne vaut pas « non »")

    # ── (c10) ⛔ aucun jalon chiffre ────────────────────────────────────────
    print("\n── (c10) ⛔ AUCUN JALON CHIFFRE (decision owner 2026-09-06) ───────")
    jalons = [w.group(0) for w in re.finditer(r"[Jj]alons?[^.\n]{0,200}", texte)
              if re.search(r"\d[\d\s  ]*(?:€|EUR)", w.group(0))]
    ctrl(not jalons, "⛔ aucun jalon CHIFFRE n'est publie",
         "aucun" if not jalons
         else "⛔ %d — ils sont SORTIS du perimetre, le sujet est `dn6-5` : %s"
              % (len(jalons), jalons[0][:60]))

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : elle ne dit RIEN de la")
    print("   VERITE d'un prix ni de sa fraicheur. Un prix faux mais date et")
    print("   source la laisse VERTE. Rouvrir la source est le seul chemin.")
    return bilan(1 if ko_total[0] else 0)


if __name__ == "__main__":
    sys.exit(main())

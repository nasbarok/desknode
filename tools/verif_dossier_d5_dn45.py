#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-5 / AC7.2 — LE DOSSIER NE PUBLIE PLUS UNE QUESTION QUI EST FERMEE.
BALAYAGE SUR **TOUT L'ARBRE DES DEUX DEPOTS**, ⛔ PAS SUR LE DIFF.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

Le constat owner du **2026-08-25** (tour eteinte ⇒ la dalle DeskNode reste
allumee) a ferme D5 **et** la portee du « Battery Power Control Switch » — d'un
seul geste. Le dossier, lui, continuait de publier la question.

🔴 **LE CADRAGE EN NOMMAIT QUATRE. CE BALAYAGE EN A TROUVE SIX.** Les deux
   supplementaires sont exactement le genre d'endroit qu'une liste ecrite a la
   main rate :
     · `deferred-work.md` (~l.1550) — une SECONDE entree de ledger, ouverte
       depuis `dn4-2`, qui disait encore « L'entree RESTE OUVERTE » ;
     · `sprint-status-desknode.yaml` (~l.63) — la section des DECISIONS du
       tracker, dans le COCKPIT.
   ⚠️ *« L'angle mort est ce qui vit HORS du diff et que le diff rend faux »*, et
   *« la 3e publication d'un chiffre faux est dans le COCKPIT, pas dans le depot
   de code »*. Les deux lecons se verifient ici, dans le meme tir.

── LA REGLE DE CLASSEMENT, ET ELLE EST DECLAREE ────────────────────────────

  **FAISANT AUTORITE** — le dossier materiel, le README, le ledger, le tracker.
  Ces fichiers disent CE QUI EST VRAI AUJOURD'HUI : une question fermee qui y
  reste ouverte est un mensonge actif. ⇒ **chacun doit porter une annotation.**

  **ARCHIVE** — les stories deja livrees, les epics, les propositions de
  correct-course, les patches de revue. Ils disent CE QUI ETAIT VRAI ALORS.
  ⛔ Les reecrire effacerait l'histoire, et le depot l'interdit. Ils sont
  COMPTES et LISTES, ⛔ jamais exiges annotes — l'exclusion est DECLAREE, pas
  silencieuse.

⚠️ ET LA STORY `dn4-5` ELLE-MEME EST UNE ARCHIVE EN COURS : elle CITE les six
   endroits pour les traiter. L'exiger annotee serait circulaire.

Sortie : exit 0 si tout passe, 1 sinon.
"""

import io
import os
import re
import sys

DESKNODE = "/home/nasbarok/projects/desknode"
COCKPIT = "/home/nasbarok/projects/compagnon_project"

# ── dn4-39 / AC39.2.a-bis + AC39.3.a — LA CAUSE **C**, TRAITEE SANS ETRE VUE ──
#
# 🔴 LES DEUX CONSTANTES CI-DESSUS SONT **ABSOLUES**, et ⛔ `HOME` n'y peut rien.
#    ⇒ cette gate est **VERTE dans un clone neuf** (elle en sort et atteint les
#      vrais depots de cette machine) et sera **ROUGE sur un runner**, ou ces
#      chemins n'existent pas. C'est le seul des six rouges qu'AUCUNE mesure
#      prise depuis ce poste ne pouvait montrer : il se **LIT dans le code**.
#    🔬 Reproduit au cadrage de `dn4-39` en pointant les deux constantes sur un
#      chemin inexistant : `BILAN : 1 OK, 7 KO`, rc **1** — c'est-a-dire, la
#      encore, le meme `rc` que son vrai rouge.
#
# ⛔ CE CORRECTIF NE TOUCHE PAS AUX CHEMINS EUX-MEMES — c'est `dn5-3` qui porte
#    « les outils sortent du clone ». Il rend seulement DISTINGUABLE « je ne
#    suis pas sur la machine de l'auteur » de « j'ai trouve un defaut ».
#
# ⛔ POURQUOI 4 : `2` est le message d'usage de `verif_sr03.py` (publie dans le
#    README), `3` est deja rendu par `verif_paliers_dn441.py` sur un MUTANT
#    PERIME. Le detail complet est ecrit dans `tools/verif_dossier_dn415.py`.
RC_PREREQUIS = 4

# Ce qu'on cherche : les formulations qui PUBLIENT ENCORE la question.
MOTIFS = [
    "Battery Power Control",
    "DEVRA MESURER LA CONSOMMATION",
]

# Faisant autorite : ces fichiers disent ce qui est vrai AUJOURD'HUI.
AUTORITE = [
    (DESKNODE, "hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md"),
    (DESKNODE, "hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md"),
    (DESKNODE, "hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md"),
    (DESKNODE, "README.md"),
    (COCKPIT, "_bmad-output/implementation-artifacts/deferred-work.md"),
    (COCKPIT, "_bmad-output/implementation-artifacts/sprint-status-desknode.yaml"),
]

# ── LA MARQUE D'ANNOTATION, ET LA FENETRE — HEURISTIQUE DECLAREE ───────────
#
# ⚠️ LA FENETRE EST SYMETRIQUE, ET CE N'ETAIT PAS LE CAS AU PREMIER TIR. Elle ne
#    regardait qu'EN AVAL, et la gate a rougi sur `affichage.md:1915` et `:1984`
#    — deux lignes qui vivent A L'INTERIEUR d'un bloc d'annotation, donc marquees
#    EN AMONT. Une annotation peut precéder son objet aussi bien que le suivre.
#
# ⛔ CE QUE CETTE HEURISTIQUE NE PEUT PAS FAIRE, et c'est ecrit plutot que tu :
#    elle ne comprend pas le texte. Une occurrence qui tomberait a moins de 40
#    lignes d'une annotation VOISINE serait acceptee a tort. Elle prouve donc
#    « aucune occurrence n'est ISOLEE », ⛔ pas « chaque occurrence est
#    correctement annotee » — cette derniere lecture reste humaine.
RE_ANNOT = re.compile(r"dn4-5", re.I)
FENETRE = 40   # lignes AVANT et APRES l'occurrence

ok_total = [0]
ko_total = [0]


# 🔴 dn4-40 / AC40.7.c — L'INSTRUMENT DE CAMPAGNE, ⛔ PAS UN CHANGEMENT DE
# FORMAT. Import DEFENSIF : une gate reste jouable si son instrument manque.
# Sans `DN_TRACE_CTRL`, la console sort a l'octet pres comme avant.
try:
    import dn_trace
except ImportError:                                  # pragma: no cover
    dn_trace = None


def ctrl(ok, libelle, detail=""):
    if dn_trace is not None:
        dn_trace.trace(ok, libelle)
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-58s %s" % (libelle, detail))
    else:
        ko_total[0] += 1
        print("  [KO ] %-58s %s" % (libelle, detail))
    return ok


def occurrences(chemin):
    if not os.path.exists(chemin):
        return None
    lignes = io.open(chemin, encoding="utf-8", errors="replace").read().split("\n")
    out = []
    for i, l in enumerate(lignes):
        if any(m in l for m in MOTIFS):
            fen = "\n".join(lignes[max(0, i - FENETRE):i + FENETRE])
            out.append((i + 1, bool(RE_ANNOT.search(fen))))
    return out


def balayage_arbre(racine, exclus):
    """Toutes les occurrences de l'arbre, pour COMPTER ce qu'on ecarte."""
    trouves = []
    for base, dirs, fichiers in os.walk(racine):
        dirs[:] = [d for d in dirs if d not in (".git", "build", "managed_components",
                                                "node_modules", "__pycache__")]
        for f in fichiers:
            if not f.endswith((".md", ".yaml", ".c", ".h", ".py", ".patch")):
                continue
            p = os.path.join(base, f)
            rel = os.path.relpath(p, racine)
            if rel in exclus:
                continue
            try:
                txt = io.open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            n = sum(txt.count(m) for m in MOTIFS)
            if n:
                trouves.append((rel, n))
    return trouves


def main():
    print("=" * 78)
    print("dn4-5 / AC7.2 — LE DOSSIER RATTRAPE LE CONSTAT OWNER DU 2026-08-25")
    print("=" * 78)
    print("\nmotifs cherches : %s" % " · ".join("« %s »" % m for m in MOTIFS))
    print("perimetre : les DEUX depots, arbre ENTIER (⛔ pas le diff)")

    # 🔴 dn4-39 — LES DEUX DEPOTS SONT DES **PREREQUIS**, ⛔ PAS DES CONTROLES.
    absents = [c for c in (DESKNODE, COCKPIT) if not os.path.isdir(c)]
    if absents:
        print("\n  [PREREQUIS ABSENT] cette gate lit DEUX depots par chemin ABSOLU")
        for c in absents:
            print("      introuvable : %s" % c)
        print("      MOTIF : ces deux chemins sont ecrits EN DUR (l. 47-48) et")
        print("              n'existent que sur la machine de l'auteur. Hors")
        print("              d'elle, la gate n'a RIEN a balayer — elle ne peut")
        print("              ni rougir ni verdir.")
        print("      REMEDE : `dn5-3` porte la reparation (« les outils sortent")
        print("              du clone »). ⛔ dn4-39 ne la fait PAS ici.")
        print("      ⛔ CE N'EST PAS UN VERDICT SUR LE DOSSIER, et ⛔ pas un skip :")
        print("         rc=%d, declare dans la table NON_JOUABLES de"
              " tools/run_gates.sh." % RC_PREREQUIS)
        return RC_PREREQUIS

    print("\n── 1. LES FICHIERS FAISANT AUTORITE — CHACUN DOIT ETRE ANNOTE ────")
    total, annotes = 0, 0
    for racine, rel in AUTORITE:
        p = os.path.join(racine, rel)
        occ = occurrences(p)
        if occ is None:
            ctrl(False, "%s" % rel[-52:], "⛔ FICHIER INTROUVABLE")
            continue
        if not occ:
            print("  [ -- ] %-58s aucune occurrence" % rel[-58:])
            continue
        total += len(occ)
        nus = [n for n, a in occ if not a]
        annotes += len(occ) - len(nus)
        ctrl(not nus, "%s" % rel[-52:],
             "⛔ NON ANNOTEE(S) l.%s" % nus if nus
             else "%d occurrence(s), toutes annotees (l.%s)"
             % (len(occ), ",".join(str(n) for n, _ in occ)))
    ctrl(total > 0, "le balayage a bien trouve des occurrences",
         "%d occurrence(s) faisant autorite, %d annotee(s)" % (total, annotes))

    print("\n── 2. CE QUI EST ECARTE, ET C'EST DECLARE ────────────────────────")
    exclus_dn = {r for _, r in AUTORITE if _ == DESKNODE}
    exclus_ck = {r for _, r in AUTORITE if _ == COCKPIT}
    arch_dn = balayage_arbre(DESKNODE, exclus_dn)
    arch_ck = balayage_arbre(COCKPIT, exclus_ck)
    print("  ARCHIVES (⛔ NON exigees annotees — elles disent ce qui etait vrai ALORS) :")
    for rel, n in sorted(arch_dn + arch_ck):
        print("     %-72s %d" % (rel[-72:], n))

# ⚠️ dn4-40 / AC40.2 — CE N'ETAIT PAS UN CONTROLE. Un `ctrl(True, …)`
#    litteral qu'aucun arbre defaillant ne peut faire rougir ne GARDE rien :
#    il gonfle le bilan. Le tri (`tools/campagne_ctrl_dn440.py`) l'a classe
#    par MUTANT, ⛔ pas par raisonnement. Le fait qu'il publiait reste dit —
#    il est imprime, ⛔ il n'est plus compte.
    print("     ⇒ les archives sont LISTEES, ⛔ pas ecartees en silence"
          " — %d fichier(s) d'archive" % (len(arch_dn) + len(arch_ck)))

    print("\n── 3. LE FAIT QUI FERME, ET IL EST ECRIT PARTOUT PAREIL ──────────")
    for racine, rel in AUTORITE:
        p = os.path.join(racine, rel)
        if not os.path.exists(p):
            continue
        txt = io.open(p, encoding="utf-8", errors="replace").read()
        if not any(m in txt for m in MOTIFS):
            continue
        ctrl("2026-08-25" in txt,
             "%s date le constat" % rel[-46:],
             "⛔ une annotation sans date ne se relit pas"
             if "2026-08-25" not in txt else "constat owner du 2026-08-25")

    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return 1 if ko_total[0] else 0


if __name__ == "__main__":
    sys.exit(main())

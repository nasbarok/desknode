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

import argparse
import io
import os
import re
import sys

# ── dn4-39 / AC39.2.a-bis + AC39.3.a — LA CAUSE **C**, TRAITEE SANS ETRE VUE ──
#
# ⚠️ 🔴 CE BLOC EST **DATE, ⛔ PAS EFFACE** (NFR3) — dn5-3, 2026-09-04. Il decrit
#    l'etat d'AVANT : deux constantes ABSOLUES,
#      DESKNODE = "/home/<auteur>/projects/desknode"
#      COCKPIT  = "/home/<auteur>/projects/compagnon_project"
#    ⇒ ce qu'il annoncait etait JUSTE, et le voici SOLDE juste en dessous.
#
# 🔴 LES DEUX CONSTANTES ETAIENT **ABSOLUES**, et ⛔ `HOME` n'y pouvait rien.
#    ⇒ cette gate etait **VERTE dans un clone neuf** (elle en sortait et
#      atteignait les vrais depots de cette machine) et **ROUGE sur un runner**,
#      ou ces chemins n'existent pas. C'etait le seul des six rouges qu'AUCUNE
#      mesure prise depuis ce poste ne pouvait montrer : il se **LIT dans le
#      code**.
#    🔬 Reproduit au cadrage de `dn4-39` en pointant les deux constantes sur un
#      chemin inexistant : `BILAN : 1 OK, 7 KO`, rc **1** — c'est-a-dire, la
#      encore, le meme `rc` que son vrai rouge.
#
# ⛔ LE CORRECTIF DE `dn4-39` NE TOUCHAIT PAS AUX CHEMINS EUX-MEMES — c'est
#    `dn5-3` qui porte « les outils sortent du clone ». Il rendait seulement
#    DISTINGUABLE « je ne suis pas sur la machine de l'auteur » de « j'ai trouve
#    un defaut ».
#
# ═══ dn5-3 / AC3.3 — 2026-09-04 : LES DEUX CHEMINS SONT SOLDES ══════════════
#
# ✅ `DESKNODE` SE DERIVE DE `__file__`. Elle designe l'arbre ou ce script est
#    ATTEINT — un second clone ou un `git worktree` designe donc bien le sien.
#    ⚠️ NUANCE AJOUTEE A LA REVUE DU 2026-09-04 : la ligne d'origine disait
#    « elle ne peut plus designer QUE l'arbre ou ce script vit ». C'est trop
#    fort — `os.path.abspath` NE RESOUT PAS LES LIENS SYMBOLIQUES. MESURE : le
#    script atteint par un lien pose ailleurs rend `depot code` = le parent du
#    LIEN, et 4 KO `⛔ FICHIER INTROUVABLE` (echec FERME, ⛔ pas un faux vert).
#    ⛔ LE CODE N'EST PAS CHANGE ICI, ET C'EST DELIBERE :
#    `dirname(dirname(abspath(__file__)))` est l'idiome de ~40 outils de ce
#    depot, `verif_dossier_dn415.py` et `verif_ledger_dn416.py` compris, et
#    AUCUN n'utilise `realpath`. Le corriger dans ce seul fichier romprait la
#    convention qu'AC3.3.a demandait justement de copier. ⇒ c'est l'AFFIRMATION
#    qui se nuance ; le passage a `realpath` est une story a lui seul. ⇒ ca ferme AUSSI, **par construction**, l'entree de
#    ledger issue de la revue de `dn4-39` : « cette gate PEUT CERTIFIER VERT UN
#    AUTRE ARBRE QUE CELUI QU'ON VERIFIE ». MESURE le 2026-09-04, AVANT
#    correction, depuis un clone pose dans `/tmp` : elle rendait
#    `BILAN : 9 OK, 0 KO`, rc 0 — sur l'arbre de l'AUTEUR et sur le cockpit
#    PRIVE, ⛔ pas sur le clone qu'on verifiait
#    (`mesures/dn5-3/T1-temoin-negatif.txt`, etage (i)).
#    ⚠️ ⛔ PAS `expanduser("~")`, ⛔ PAS `$HOME` : cette constante ne cherche pas
#    un FOYER, elle cherche LE DEPOT OU LE SCRIPT VIT.
#
# ✅ `COCKPIT` DEVIENT UN **ARGUMENT**, avec un defaut derive de `HOME`.
#    ⚠️ `expanduser("~")` ET `${HOME}` NE DISENT PAS LA MEME CHOSE quand `HOME`
#    est absent : le shell de `run_gates.sh` retombe sur `${HOME:-/nonexistent}`
#    tandis que Python interroge `/etc/passwd` et rend le vrai foyer. ⇒ **ON LIT
#    `os.environ.get("HOME")`, avec la MEME valeur de repli que le shell** —
#    piege deja paye et deja ecrit dans `tools/verif_dossier_dn415.py` (l. 168).
#
# 🔴 ET LE CONTRAT DE `rc` NE BOUGE PAS, LA CI EN DEPEND. Sans cockpit la gate
#    rend **4**, et **1** si elle trouve un vrai KO — dans CET ORDRE. Rendre 0
#    sans cockpit ferait sortir `run_gates.sh` en 1 sur `DECLARATION DEMENTIE`
#    et rougirait la CI, qui est verte PRECISEMENT parce que les gates non
#    exercables sur un runner y rendent leur `rc` declare.
DESKNODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COCKPIT_DEFAUT = os.path.join(os.environ.get("HOME") or "/nonexistent",
                              "projects", "compagnon_project")
#
# ⛔ POURQUOI 4 : `2` est le message d'usage de `verif_sr03.py` (publie dans le
#    README), `3` est deja rendu par `verif_paliers_dn441.py` sur un MUTANT
#    PERIME. Le detail complet est ecrit dans `tools/verif_dossier_dn415.py`.
RC_PREREQUIS = 4


# 🔴 dn5-6 / CONSTAT (7) — 2026-09-05 : LA REGLE DE `rc` A DESORMAIS **UNE
#    SEULE SOURCE**, ET LA PHRASE IMPRIMEE EN DECOULE.
#
# ⚠️ ⛔ LA LIGNE D'ORIGINE N'EST PAS EFFACEE, ELLE EST NOMMEE COMME FAUSSE
#    (NFR3). Elle disait, mot pour mot :
#      « ⛔ rc=4 (prerequis) UNIQUEMENT si la moitie jouee est MUETTE ; »
#    MESURE du 2026-09-05 (`mesures/dn5-6/T1-filtre-10-constats.txt`) :
#      `--cockpit <absent>` rend `BILAN : 5 OK, 0 KO` et **rc=4**, alors que la
#      moitie jouee a rendu **5 verdicts** et n'a rien de « muette ».
#    ⇒ LA VRAIE REGLE EST : « 4 des que le cockpit manque ET qu'aucun KO n'a
#      ete trouve » — la MUTITE n'y entre pour rien.
#
# 🔴 POURQUOI UNE FONCTION ET ⛔ PAS UNE PHRASE CORRIGEE : une phrase corrigee
#    peut re-diverger au prochain changement de regle, et c'est exactement
#    comme ca que celle-ci est devenue fausse. Ici la phrase est **DERIVEE** du
#    code qui decide ⇒ elles ⛔ NE PEUVENT PLUS diverger.
#
# ⛔ LE CONTRAT DE `rc` NE BOUGE PAS, LA CI DE `dn4-39` EN DEPEND :
#    un vrai KO rend **1** et l'emporte ; sinon, cockpit absent rend **4**.
def regle_rc(ko, cockpit_absent):
    """Rend `(rc, phrase)`. La phrase DECRIT le rc, elle ne le commente pas."""
    if ko:
        return 1, ("⛔ rc=1 : un KO a ete trouve dans la moitie jouee — un vrai"
                   " defaut l'emporte TOUJOURS sur un prerequis absent.")
    if cockpit_absent:
        return RC_PREREQUIS, (
            "⛔ rc=%d (prerequis) des que le cockpit manque ET qu'aucun KO n'a"
            " ete trouve." % RC_PREREQUIS)
    return 0, "rc=0 : cockpit atteignable, aucun KO."

# Ce qu'on cherche : les formulations qui PUBLIENT ENCORE la question.
MOTIFS = [
    "Battery Power Control",
    "DEVRA MESURER LA CONSOMMATION",
]

# Faisant autorite : ces fichiers disent ce qui est vrai AUJOURD'HUI.
# ⚠️ dn5-3 — LE DEPOT EST DESORMAIS UN **MARQUEUR**, ⛔ plus un chemin. Le
#    cockpit n'est connu qu'a l'execution (il vient de `--cockpit`), donc il ne
#    peut PLUS etre fige ici. 4 de ces 6 fichiers vivent dans le depot CODE :
#    sans cockpit, LES DEUX TIERS DU BALAYAGE RESTENT CONTROLABLES.
AUTORITE = [
    ("DESKNODE", "hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md"),
    ("DESKNODE", "hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md"),
    ("DESKNODE", "hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md"),
    ("DESKNODE", "README.md"),
    # ⚠️ dn8-4 (2026-09-13) — AJOUTE, ⛔ le README ci-dessus n'est PAS retire.
    #    Le journal qui portait ces occurrences est parti OCTET POUR OCTET dans
    #    `docs/journal-de-bord.md` ; la racine porte une vitrine anglaise. Sans
    #    cette ligne, la couverture de ce balayage se serait REDUITE EN SILENCE :
    #    le README aurait sorti « aucune occurrence », et la gate serait restee
    #    verte sur un fichier qui ne dit plus rien.
    #    ⚠️ Le « 4 de ces 6 fichiers » ecrit plus haut devient 5 de ces 7 ; il
    #    n'est PAS reecrit, et le compte qui fait foi est la ligne `somme = N / 7`.
    ("DESKNODE", "docs/journal-de-bord.md"),
    ("COCKPIT", "_bmad-output/implementation-artifacts/deferred-work.md"),
    ("COCKPIT", "_bmad-output/implementation-artifacts/sprint-status-desknode.yaml"),
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

# ═══ dn5-6 / NFR7 + regle `dn4-44` — LES MUTANTS QUI **REPLANTENT** ═══════
#
# ⛔ UN MUTANT QUI **DEBRANCHE** LA GARDE NE PROUVE QUE SON EXISTENCE.
#    Chacun des trois ci-dessous REMET LA FAUTE HISTORIQUE, celle qui a ete
#    MESUREE le 2026-09-05 dans `mesures/dn5-6/T1-filtre-10-constats.txt`, et
#    le controle qui la garde DOIT rougir.
# ⚠️ La mutation est EN MEMOIRE : ⛔ aucun fichier n'est modifie, ⛔ aucun
#    droit n'est change sur le disque.
MUTANTS = {
    1: ("rend ILLISIBLE tout fichier faisant autorite du depot code "
        "(constat 1 : la gate mourait en PermissionError NU, sans BILAN)"),
    2: ("fait DISPARAITRE un fichier faisant autorite du balayage "
        "(constat 2 : le `N OK / 0 KO` se calculait sur une population fondue)"),
    3: ("re-redige a la main la phrase de la regle de `rc` "
        "(constat 7 : la gate imprimait une regle qu'elle ne suivait pas)"),
}
_MUTANT = 0


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


# 🔴 dn5-6 / CONSTAT (1) — 2026-09-05 : UN FICHIER FAISANT AUTORITE **ILLISIBLE**
#    TUAIT LA GATE EN `PermissionError` NU, **SANS LIGNE `BILAN`**.
#    MESURE (A/B, `mesures/dn5-6/T1-filtre-10-constats.txt`) : le MEME cockpit
#    de synthese rend `BILAN : 9 OK, 0 KO` quand il est lisible, et un
#    **traceback nu, rc=1, AUCUN `BILAN`** quand UN de ses fichiers est a
#    `chmod 000`. `balayage_arbre()` attrapait deja `OSError` ; celle-ci ⛔ pas.
#    ⇒ ⚠️ « SORTIE EN AMONT » N'IMPRIME AUCUN `BILAN` : le discriminant d'une
#      gate morte est le **`Traceback`**, ⛔ pas l'absence de bilan. Une gate qui
#      meurt avant son bilan ne peut ni verdir ni rougir — elle ne GARDE RIEN.
#    ⛔ L'ILLISIBLE N'EST PAS SAUTE : il devient un **KO nomme**, sinon on
#      remplacerait une mort bruyante par un silence vert.
ILLISIBLE = object()   # sentinelle : le fichier EXISTE mais ne se lit pas


# 🔴 dn5-6 / REVUE DU 2026-09-05 — LE SEUL POINT DE LECTURE, ET C'EST DELIBERE.
#    ⛔ LE PREMIER JET DU MUTANT 1 NE PROUVAIT RIEN : il posait `occ = ILLISIBLE`
#    **apres** l'appel, donc il ne traversait JAMAIS le `except OSError` neuf.
#    MESURE de la revue : une variante SANS ce `try/except` rendait des verdicts
#    IDENTIQUES A L'OCTET sous `--mutant 1` (`rc=1 · 8 OK, 8 KO` des deux cotes)
#    ⇒ ⛔ un mutant qui DEBRANCHE le resultat, ⛔ pas qui REPLANTE la faute —
#    exactement ce qu'AC6.4 interdit, paye dans le geste qui l'invoque.
# ⇒ ICI LE MUTANT FAIT ECHOUER **LA LECTURE**. Retirer l'un des deux
#   `except OSError` fait desormais mourir la gate sur un traceback nu.
# 🔴 dn5-6 / REVUE DU 2026-09-05 — LE CONTROLE COMPARAIT UNE VALEUR A
#    ELLE-MEME. Il faisait `phrase = regle_rc(...)` puis
#    `ctrl(phrase == regle_rc(...)[1], …)` : les MEMES arguments, deux lignes
#    plus loin. Il n'observait ⛔ RIEN de ce qui etait REELLEMENT imprime.
#    MESURE de la revue : en reinjectant la phrase fausse historique a l'un OU
#    l'autre des deux sites d'impression, le controle disait `[OK ]` **dans les
#    deux cas** pendant que la sortie portait la phrase refutee.
# ⇒ TOUTE REGLE DE `rc` SORT DESORMAIS D'ICI, ET ON ENREGISTRE CE QUI SORT.
#   Le controle confronte les phrases EMISES a l'ensemble de celles que
#   `regle_rc()` peut produire. Une phrase redigee ailleurs — a n'importe quel
#   site — devient une INTRUSE et rougit.
_EMISES = []


def dire_regle(ko, cockpit_absent, prefixe="      "):
    rc, phrase = regle_rc(ko, cockpit_absent)
    if _MUTANT == 3:
        # REPLANTE la faute historique : une phrase REDIGEE A LA MAIN, au site
        # d'emission — c'est ainsi qu'elle avait derive.
        phrase = ("⛔ rc=%d (prerequis) UNIQUEMENT si la moitie jouee est"
                  " MUETTE ; un KO trouve ici rend 1." % RC_PREREQUIS)
    _EMISES.append(phrase)
    print(prefixe + phrase)
    return rc


def _ouvrir(chemin):
    if _MUTANT == 1:
        raise PermissionError(13, "Permission denied (mutant 1 : lecture "
                                  "REPLANTEE, ⛔ pas debranchee)", chemin)
    return io.open(chemin, encoding="utf-8", errors="replace")


def occurrences(chemin):
    if not os.path.exists(chemin):
        return None
    try:
        brut = _ouvrir(chemin).read()
    except OSError:
        return ILLISIBLE
    lignes = brut.split("\n")
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
    global _MUTANT
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--cockpit", default=COCKPIT_DEFAUT)
    # ⚠️ dn5-6 — `--mutant` REPLANTE une faute EN MEMOIRE et doit faire ROUGIR.
    #    ⛔ Il n'est jamais passe par `run_gates.sh` ni par la CI : ils jouent
    #    la gate SANS argument. C'est un outil de PREUVE, ⛔ pas un mode.
    ap.add_argument("--mutant", type=int, default=0)
    ap.add_argument("--liste-mutants", action="store_true")
    a = ap.parse_args()
    if a.liste_mutants:
        for n in sorted(MUTANTS):
            print("  %2d  %s" % (n, MUTANTS[n]))
        return 0
    _MUTANT = a.mutant
    if _MUTANT and _MUTANT not in MUTANTS:
        print("⛔ mutant %d inconnu — `--liste-mutants` les donne." % _MUTANT)
        return 2
    racines = {"DESKNODE": DESKNODE, "COCKPIT": a.cockpit}

    print("=" * 78)
    print("dn4-5 / AC7.2 — LE DOSSIER RATTRAPE LE CONSTAT OWNER DU 2026-08-25")
    print("=" * 78)
    print("\nmotifs cherches : %s" % " · ".join("« %s »" % m for m in MOTIFS))
    print("perimetre : les DEUX depots, arbre ENTIER (⛔ pas le diff)")
    print("depot code    : %s" % DESKNODE)
    print("depot cockpit : %s" % a.cockpit)

    # 🔴 dn4-39 — LE COCKPIT EST UN **PREREQUIS**, ⛔ PAS UN CONTROLE.
    # ⚠️ dn5-3, 2026-09-04 — LA LISTE DES ABSENTS N'EN CONTIENT PLUS QU'UN.
    #    `DESKNODE` derive de `__file__` : il EXISTE toujours, par construction,
    #    puisque c'est le repertoire d'ou ce fichier est atteint. ⚠️ REVUE DU
    #    2026-09-04 : « existe » reste vrai — ⛔ « c'est l'arbre ou ce fichier
    #    vit » ne l'est pas sous un lien symbolique (voir l. 73). L'echec y est
    #    FERME (4 KO), donc le prerequis ci-dessous reste juste. ⇒ le seul prerequis qui peut
    #    manquer est le cockpit.
    # 🔴 ET ON NE REND PLUS LA MAIN TOUT DE SUITE. Le `return` immediat
    #    ABANDONNAIT la moitie que n'importe quel clone peut voir : sur les 6
    #    fichiers faisant autorite, **4 vivent dans le depot CODE**. C'est la
    #    correction que `verif_dossier_dn415.py` a deja payee (revue du
    #    2026-09-02) : « ON JOUE LA MOITIE ATTEIGNABLE, et on ne rend 4 QUE SI
    #    ELLE EST MUETTE ».
    cockpit_absent = not os.path.isdir(a.cockpit)
    hors = [r for d, r in AUTORITE if d == "COCKPIT"]
    dedans = [r for d, r in AUTORITE if d == "DESKNODE"]
    if cockpit_absent:
        print("\n  [PREREQUIS PARTIEL] le depot cockpit n'est pas atteignable")
        print("      chemin attendu : %s" % a.cockpit)
        print("      MOTIF : le cockpit est un depot PRIVE de planification,")
        print("              ⛔ jamais clone a cote du code. C'est le cas")
        print("              NORMAL sur un runner et chez un contributeur.")
        print("      ⇒ LA MOITIE `desknode` EST JOUEE QUAND MEME : %d des %d"
              " fichiers" % (len(dedans), len(AUTORITE)))
        print("        faisant autorite vivent dans CE depot.")
        print("      ⇒ CE QUE CETTE PASSE N'A PAS PU CONTROLER — les %d fichier(s)"
              % len(hors))
        print("        du cockpit sont HORS de portee, ⛔ pas fantomes :")
        for r in hors:
            print("           · %s" % r)
        print("      REMEDE : `--cockpit <chemin>` si le depot est ailleurs.")
        # 🔴 dn5-6 / CONSTAT (7) — LES DEUX BRANCHES SONT IMPRIMEES DEPUIS
        #    `regle_rc()`, ⛔ plus redigees a la main. Ici le `rc` final n'est
        #    pas encore connu (les controles n'ont pas tourne) : on annonce
        #    donc LES DEUX cas, chacun avec la phrase que la regle produit.
        dire_regle(True, True)
        dire_regle(False, True)
        print("      ⛔ CE N'EST PAS UN VERDICT SUR LE DOSSIER, et ⛔ pas un skip :")
        print("         rc=%d est declare dans la table NON_JOUABLES de"
              " tools/run_gates.sh." % RC_PREREQUIS)

    print("\n── 1. LES FICHIERS FAISANT AUTORITE — CHACUN DOIT ETRE ANNOTE ────")
    total, annotes = 0, 0
    n_hors, n_muet, n_verdict, n_illisible = 0, 0, 0, 0
    # 🔴 dn5-6 / REVUE DU 2026-09-05 — LE MUTANT 2 RETIRE UN FICHIER **DU
    #    BALAYAGE**, ⛔ il ne soustrait plus 1 au total apres coup. La premiere
    #    version faisait `rendus -= 1` : elle cassait le RESULTAT, ⛔ pas la
    #    garde. ⇒ ici le danger annonce — « un fichier qui disparaitrait du
    #    balayage » — se produit REELLEMENT, et le controle doit le voir.
    balayes = ([a for a in AUTORITE if a[1] != "README.md"]
               if _MUTANT == 2 else AUTORITE)
    for depot, rel in balayes:
        if depot == "COCKPIT" and cockpit_absent:
            print("  [ ×× ] %-58s HORS de portee (cockpit absent)" % rel[-58:])
            n_hors += 1
            continue
        p = os.path.join(racines[depot], rel)
        occ = occurrences(p)
        if occ is None:
            ctrl(False, "%s" % rel[-52:], "⛔ FICHIER INTROUVABLE")
            n_verdict += 1
            continue
        if occ is ILLISIBLE:
            # ⇒ un KO NOMME, ⛔ pas un saut, ⛔ pas une mort en amont.
            ctrl(False, "%s" % rel[-52:],
                 "⛔ ILLISIBLE (il EXISTE mais ne se lit pas — droits, ACL)")
            n_illisible += 1
            n_verdict += 1
            continue
        if not occ:
            print("  [ -- ] %-58s aucune occurrence" % rel[-58:])
            n_muet += 1
            continue
        total += len(occ)
        n_verdict += 1
        nus = [n for n, a in occ if not a]
        annotes += len(occ) - len(nus)
        ctrl(not nus, "%s" % rel[-52:],
             "⛔ NON ANNOTEE(S) l.%s" % nus if nus
             else "%d occurrence(s), toutes annotees (l.%s)"
             % (len(occ), ",".join(str(n) for n, _ in occ)))
    ctrl(total > 0, "le balayage a bien trouve des occurrences",
         "%d occurrence(s) faisant autorite, %d annotee(s)" % (total, annotes))

    # ═══ dn5-6 / CONSTAT (2) — 2026-09-05 ══════════════════════════════════
    # 🔴 `le balayage a bien trouve des occurrences` EST LA SEULE GARDE
    #    GLOBALE, ET **UNE** OCCURRENCE LA SATISFAIT.
    #    MESURE : `--cockpit <absent>` ⇒ **2 fichiers HORS de portee, 2 MUETS,
    #    2 verdicts** sur les 6 faisant autorite — soit **4 sur 6 qui n'ont
    #    RIEN controle** — et le bilan sort quand meme en `5 OK, 0 KO`, `rc=4`
    #    « conforme a la declaration ».
    # ⛔ LE LIBELLE CI-DESSUS N'EST PAS TOUCHE : `verif_campagne_dn440.py` cible
    #    ses mutants PAR LIBELLE. Le remede est un controle **EN PLUS**, qui
    #    rend la population VISIBLE au lieu de la laisser se fondre.
    # ⇒ CE QU'IL GARDE : que chacun des 6 fichiers soit RENDU COMPTE d'une des
    #   quatre facons (verdict, muet, hors de portee, illisible). Un fichier qui
    #   disparaitrait du balayage — le vrai danger — le fait rougir.
    # ⚠️ dn5-6 / REVUE DU 2026-09-05 — LES QUATRE NOMBRES SOMMAIENT AU-DELA DE
    #    `len(AUTORITE)` : `n_verdict` COMPTAIT DEJA les illisibles. Mesure sous
    #    `--mutant 1` : « 6 verdict(s) · 0 muet · 0 hors · 4 illisible(s) » pour
    #    **6** fichiers. ⇒ les lus et les illisibles sont desormais DISJOINTS.
    n_lus = n_verdict - n_illisible
    print("\n   POPULATION REELLEMENT CONTROLEE — ⛔ elle ne se fond plus")
    print("     %d lu(s) · %d muet(s) · %d hors de portee · %d illisible(s)"
          "   [somme = %d / %d]"
          % (n_lus, n_muet, n_hors, n_illisible,
             n_lus + n_muet + n_hors + n_illisible, len(AUTORITE)))
    rendus = n_verdict + n_muet + n_hors
    ctrl(rendus == len(AUTORITE),
         "chaque fichier faisant autorite est RENDU COMPTE",
         "%d/%d rendus compte" % (rendus, len(AUTORITE))
         if rendus == len(AUTORITE)
         else "⛔ %d fichier(s) faisant autorite ont DISPARU du balayage "
              "(%d/%d)" % (len(AUTORITE) - rendus, rendus, len(AUTORITE)))
    # 🔴 dn5-6 / REVUE DU 2026-09-05 — IL COMPTAIT LES ILLISIBLES COMME DES
    #    FICHIERS « QUI ONT CONTROLE QUELQUE CHOSE ». Un fichier qu'on n'a pas
    #    LU n'a rien controle, quel que soit le verdict qu'il a fait ecrire.
    #    Mesure : sous `--mutant 1`, il annoncait « 6 fichier(s) ont controle
    #    quelque chose ; 0 n'ont rien controle » alors que **4 etaient
    #    illisibles**. ⇒ il compte les LUS, et le mutant 1 le fait rougir.
    ctrl(n_lus > 0,
         "au moins un fichier ATTEIGNABLE a rendu un verdict",
         "%d fichier(s) LU(S) ont controle quelque chose ; %d n'ont rien "
         "controle (%d muet(s), %d hors de portee, %d illisible(s))"
         % (n_lus, n_muet + n_hors + n_illisible, n_muet, n_hors, n_illisible))

    print("\n── 2. CE QUI EST ECARTE, ET C'EST DECLARE ────────────────────────")
    exclus_dn = {r for d, r in AUTORITE if d == "DESKNODE"}
    exclus_ck = {r for d, r in AUTORITE if d == "COCKPIT"}
    arch_dn = balayage_arbre(DESKNODE, exclus_dn)
    # ⚠️ dn5-3 — SANS COCKPIT, CE BALAYAGE-LA N'A PAS D'ARBRE. Il rend une liste
    #    VIDE, et la ligne ci-dessous le DIT — ⛔ pas un zero silencieux qu'on
    #    lirait comme « rien a signaler ».
    arch_ck = [] if cockpit_absent else balayage_arbre(racines["COCKPIT"], exclus_ck)
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
    if cockpit_absent:
        print("     ⚠️ ⛔ CE COMPTE NE PORTE QUE SUR LE DEPOT CODE : l'arbre du")
        print("        cockpit n'a PAS ete balaye (il est HORS de portee).")

    print("\n── 3. LE FAIT QUI FERME, ET IL EST ECRIT PARTOUT PAREIL ──────────")
    for depot, rel in AUTORITE:
        if depot == "COCKPIT" and cockpit_absent:
            print("  [ ×× ] %-58s HORS de portee (cockpit absent)" % rel[-58:])
            continue
        p = os.path.join(racines[depot], rel)
        if not os.path.exists(p):
            continue
        # 🔴 dn5-6 / CONSTAT (1) — LE **SECOND** SITE DE LECTURE, ET IL A ETE
        #    TROUVE PAR LE T2 DE CETTE MEME MARCHE, ⛔ pas par le cadrage.
        #    Le premier correctif n'avait garde que `occurrences()` : la gate
        #    imprimait bien son `[KO ] ILLISIBLE` en section 1, PUIS mourait
        #    ICI en `PermissionError` nu, toujours **sans ligne `BILAN`**.
        #    ⇒ « une gate scopee a UNE fonction epingle VERT le meme defaut
        #      ailleurs » — mesure du 2026-09-05, capture `T2-correctifs.txt`.
        try:
            txt = io.open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            txt = None
        if _MUTANT == 1 and depot == "DESKNODE":
            txt = None               # REPLANTE la faute SUR CE SITE AUSSI
        if txt is None:
            ctrl(False, "%s date le constat" % rel[-46:],
                 "⛔ ILLISIBLE — ⛔ on ne conclut RIEN sur un fichier qu'on "
                 "n'a pas lu")
            continue
        if not any(m in txt for m in MOTIFS):
            continue
        ctrl("2026-08-25" in txt,
             "%s date le constat" % rel[-46:],
             "⛔ une annotation sans date ne se relit pas"
             if "2026-08-25" not in txt else "constat owner du 2026-08-25")

    # ═══ dn5-6 / CONSTAT (7) — LA PHRASE EST DERIVEE, ⛔ PLUS REDIGEE ═══════
    # ⇒ CE QUE CE CONTROLE GARDE : que la phrase imprimee soit CELLE QUE LA
    #   REGLE PRODUIT pour ce `(ko, cockpit_absent)`-la. Une phrase re-redigee
    #   a la main — le defaut historique, mesure le 2026-09-05 — le fait
    #   rougir. ⛔ Il ne verifie PAS « la phrase est jolie » : il verifie
    #   qu'elle n'a PAS ete ecrite ailleurs que dans `regle_rc`.
    print("\n── LA REGLE DE `rc`, ET ELLE EST DERIVEE DU CODE QUI DECIDE ──────")
    dire_regle(ko_total[0], cockpit_absent, prefixe="  ")
    # ⇒ ON CONFRONTE CE QUI A ETE **EMIS**, ⛔ pas une variable a son producteur.
    #   L'ensemble de reference couvre les quatre etats possibles de la regle.
    attendues = {regle_rc(k, c)[1] for k in (0, 1) for c in (False, True)}
    intruses = [x for x in _EMISES if x not in attendues]
    ctrl(not intruses,
         "toute regle de rc imprimee sort de regle_rc",
         "%d phrase(s) emise(s), toutes produites par la regle" % len(_EMISES)
         if not intruses
         else "⛔ %d phrase(s) REDIGEE(S) hors de regle_rc : %r — c'est ainsi "
              "qu'elle avait derive (mesure du 2026-09-05)"
              % (len(intruses), intruses[0][:70]))

    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    # 🔴 dn5-3 / AC3.3.b — L'ORDRE EST UNE REGLE, ⛔ pas une preference de forme :
    #    UN VRAI DEFAUT L'EMPORTE SUR UN PREREQUIS ABSENT. Sans ca, `rc=4`
    #    MASQUERAIT un rouge trouve dans la moitie atteignable, et « rc attendu
    #    = 4 » redeviendrait satisfiable par un defaut — exactement ce que
    #    `dn4-39` a voulu rendre impossible. Forme copiee de
    #    `tools/verif_dossier_dn415.py`.
    # ⚠️ dn5-6, 2026-09-05 — LE MOTIF CITE ICI EST RE-ANCRE : l'ancien,
    #    `return RC_PREREQUIS if cockpit_absent`, resolvait sur **0 fichier**
    #    apres cette marche (2 avant). Un porteur ⛔ ne peut pas suivre un motif
    #    qui ne resout pas. ⇒ motif VIVANT : `def regle_rc(ko, cockpit_absent)`.
    # ⛔ LE CONTRAT NE BOUGE PAS — il vient desormais de `regle_rc()`, la MEME
    #    fonction qui a produit la phrase ci-dessus ⇒ elles ⛔ NE PEUVENT PLUS
    #    diverger. `rc_final` a ete calcule AVANT le dernier `ctrl` ; on le
    #    recalcule ici pour que ce dernier KO compte, lui aussi.
    return regle_rc(ko_total[0], cockpit_absent)[0]


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-15 / AC6 — LE DOSSIER NE MENT PLUS SUR CE QU'IL DECRIT.
BALAYAGE SUR **LES DEUX DEPOTS**, ⛔ PAS SUR LE DIFF.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

Quatre motifs de dossier ont ete signales comme perimes par l'epic `dn4` du
2026-08-25. Cinq jours plus tard, TROIS DES QUATRE COMPTES DE L'EPIC ETAIENT
FAUX, et DEUX JEUX D'ADRESSES NE POINTAIENT RIEN. Cette gate existe pour que
ca ne recommence pas : elle re-compte l'arbre a chaque tir et exige qu'un
MANIFESTE porte un VERDICT pour chaque occurrence trouvee.

── ⛔ CE QUE CETTE GATE NE VOIT PAS, ET C'EST ECRIT PLUTOT QUE TU (AC6.7) ───

  🔴 ELLE COMPTE DES MOTIFS. ELLE NE LIT PAS LE SENS.
     Elle ne peut PAS distinguer un `VL53L0X` legitime (il y en a 28 sur 29 :
     des refutations, des temoins negatifs, un piege de source) d'un vrai
     defaut (il y en a UN, `sdkconfig.defaults:71`, un INVENTAIRE de bus).
     ⇒ Elle **EXIGE un verdict**, elle ne le **REND pas**. Le verdict est un
     acte de lecture humaine, consigne au manifeste.

  🔴 ELLE EST INSENSIBLE A LA CASSE ET AUX DIACRITIQUES, ET C'EST MESURE.
     5 occurrences sur 29 echappent a un motif sensible a la casse :
     `vl53l0x` x1 (`capteurs-i2c.md`), `facade` x3 (`agent/`, `tools/fixtures/`),
     `Facade` x1 (`dn_display.h`). Et `dn4-14` a PERDU UNE GATE ENTIERE sur ce
     defaut exact (`/* orange */` en minuscules faisait sauter une case sur six,
     EN SILENCE).

  🔴 ELLE EST ECRITE EN PYTHON, ⛔ JAMAIS EN SHELL, ET LE MOTIF EST MESURE.
     `grep -c` SORT EN 1 QUAND LE COMPTE EST 0 — ce qui a rendu la gate CRLF de
     `deployer_tour.sh` MUETTE PENDANT DEUX REVUES. Une gate de COMPTAGE est le
     pire endroit du monde pour ce piege.

  🔴 ELLE CLE SUR (depot, fichier, ligne, motif). Une occurrence DEPLACEE sort
     en ROUGE, meme si son texte n'a pas bouge. C'est VOULU : le manifeste doit
     etre RE-LU, pas recite. C'est aussi le cout de cette gate, il est declare.

  ⚠️ UNE LIGNE SOURCE PEUT PORTER PLUSIEURS OCCURRENCES DU MEME MOTIF. Le
     manifeste porte alors UNE ligne avec une colonne `n` — c'est UN SEUL acte
     d'arbitrage (meme phrase, meme verdict). La gate verifie que la SOMME DES
     `n` egale le compte de l'arbre, ⛔ pas le nombre de lignes du manifeste.

── LE PERIMETRE, ET IL EST DECLARE ─────────────────────────────────────────

  La regle de classement est celle que le depot a deja posee (`verif_dossier_d5_dn45.py`) :

  **FAISANT AUTORITE** — ils disent CE QUI EST VRAI AUJOURD'HUI. Une affirmation
    perimee y est un mensonge ACTIF. ⇒ **chaque occurrence porte un VERDICT.**
      · depot `desknode` : arbre ENTIER (code, dossier materiel, README, outils) ;
      · depot `cockpit`  : le brief + son addendum + son memlog, l'epic, le
        ledger `deferred-work.md`, le tracker `sprint-status-desknode.yaml`.

  **ARCHIVE** — les stories DEJA LIVREES et les investigations. Elles disent CE
    QUI ETAIT VRAI ALORS ; les reecrire effacerait l'histoire, et le depot
    l'interdit. ⇒ elles sont **COMPTEES et LISTEES**, ⛔ jamais exigees arbitrees.

  🔴 UNE EXCEPTION, ET ELLE EST MESUREE : le motif `busid-en-dur` est arbitre
     **PARTOUT, ARCHIVES COMPRISES**. Motif : une RECETTE se copie-colle, meme
     depuis une story fermee — et `3-1` n'est pas seulement perime, il est
     OCCUPE (il porte un `V31GT 0e8d:201c`) ⇒ la suivre DETACHE LE MAUVAIS
     PERIPHERIQUE. Un fait date se lit ; une commande s'execute.

  EXCLUSIONS, ⛔ AUCUNE N'EST SILENCIEUSE — elles sont IMPRIMEES a chaque tir :
    · le manifeste lui-meme et CETTE gate — ils CITENT les motifs, les exiger
      arbitres serait circulaire ;
    · la story `dn4-15-*.md` et LA LIGNE `dn4-15-*` DU TRACKER — c'est la SPEC
      qui decrit les defauts, et son bilan de cloture les re-cite ;
    · `mesures/` et `sprint-board-desknode.html` — captures datees et fichier
      GENERE, ils ne se reecrivent pas ;
    · `.git/`, `build/`, `managed_components/`, `__pycache__/`, binaires.

Usage :
    python3 tools/verif_dossier_dn415.py [--cockpit CHEMIN] [--compte]

  --compte   : mode COMPTE SEUL (T0). N'exige pas le manifeste, imprime le
               releve fichier par fichier ET ligne par ligne.
  --cockpit  : racine du depot cockpit. ⛔ S'IL EST ABSENT, LA GATE SORT EN
               ROUGE EN LE DISANT — ⛔ JAMAIS un `skip` silencieux (AC6.5).
               Motif : « une gate scopee epingle vert le meme defaut ailleurs ».

Sortie : exit 0 si tout passe, 1 sinon.
"""

import argparse
import io
import os
import re
import sys
import unicodedata

DESKNODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COCKPIT_DEFAUT = os.path.expanduser("~/projects/compagnon_project")

MANIFESTE = "docs/dn4-15-arbitrage.md"

VERDICTS = ("FAUX", "VRAI", "HISTORIQUE", "SANS-RAPPORT")

# ── LES QUATRE MOTIFS ───────────────────────────────────────────────────────
# Ils sont appliques sur une ligne NORMALISEE : NFD, marques diacritiques
# retirees, minuscules. ⇒ `Façade`, `FACADE`, `facade`, `façade` = un seul motif.
MOTIFS = [
    # (cle, regex sur ligne normalisee, libelle)
    ("facade", re.compile(r"facade"), "le module « en facade » (3 homonymes)"),
    ("vl53l0x", re.compile(r"vl53l0x"), "la puce VL53L0X (le module est un VL6180X)"),
    ("340..350", re.compile(r"340\s*\.\.\s*350"), "la coordonnee morte y = 340..350"),
    # Le busid EN DUR DANS UNE RECETTE. ⛔ Pas les mentions narratives :
    # « le busid a valu `3-1` le 26/08 » est un FAIT DATE, pas une consigne.
    # La forme de recette est la forme NUE : `--busid 3-1`, `busid 3-1`, `ici : 3-1`.
    ("busid-en-dur", re.compile(r"(?:--busid|\bbusid|\bici\s*:)\s+\d+-\d+"),
     "un busid CONSTANT dans une recette (3 valeurs ont ete vraies)"),
]

EXT_TEXTE = (".md", ".yaml", ".yml", ".c", ".h", ".py", ".sh", ".ps1", ".bat",
             ".txt", ".defaults", ".json", ".cfg", ".in", ".scad", ".patch")

DIRS_EXCLUS = {".git", "build", "managed_components", "node_modules",
               "__pycache__", "mesures", "venv", ".venv", "assets", "cablage"}

# Auto-reference : ces fichiers CITENT les motifs pour les traiter.
EXCLUS_DESKNODE = {
    MANIFESTE,
    "tools/verif_dossier_dn415.py",
}
EXCLUS_COCKPIT = {
    "_bmad-output/implementation-artifacts/dn4-15-le-dossier-ne-ment-plus-sur-ce-qu-il-decrit.md",
    "_bmad-output/implementation-artifacts/sprint-board-desknode.html",
}

# Ligne AUTO-REFERENTE du tracker : son commentaire de cadrage/cloture CITE les
# quatre motifs pour les traiter. L'exiger arbitree serait circulaire, et son
# bilan de cloture (AC7.5) casserait la gate le jour meme ou elle est ecrite.
CLE_STORY = "dn4-15-le-dossier-ne-ment-plus-sur-ce-qu-il-decrit"

# ── FAISANT AUTORITE cote cockpit : ils disent ce qui est VRAI AUJOURD'HUI ──
AUTORITE_COCKPIT = [
    "_bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14",
    "_bmad-output/planning-artifacts/epics-desknode-v1.md",
    "_bmad-output/implementation-artifacts/deferred-work.md",
    "_bmad-output/implementation-artifacts/sprint-status-desknode.yaml",
    ".claude/skills/desknode-board",
]

# ── ARCHIVE cote cockpit : les stories livrees et les investigations ────────
ARCHIVE_COCKPIT = ["_bmad-output/implementation-artifacts"]

ok_total = [0]
ko_total = [0]


def ctrl(ok, libelle, detail=""):
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-56s %s" % (libelle[:56], detail))
    else:
        ko_total[0] += 1
        print("  [KO ] %-56s %s" % (libelle[:56], detail))
    return ok


def normalise(s):
    """NFD + retrait des marques diacritiques + minuscules."""
    d = unicodedata.normalize("NFD", s)
    return "".join(c for c in d if unicodedata.category(c) != "Mn").lower()


def fichiers_desknode(racine):
    for base, dirs, fics in os.walk(racine):
        dirs[:] = [d for d in dirs if d not in DIRS_EXCLUS]
        for f in sorted(fics):
            if not f.endswith(EXT_TEXTE) and f != "sdkconfig.defaults":
                continue
            rel = os.path.relpath(os.path.join(base, f), racine)
            if rel in EXCLUS_DESKNODE:
                continue
            yield rel


def fichiers_cockpit(racine, surface):
    vus = set()
    for entree in surface:
        chemin = os.path.join(racine, entree)
        if os.path.isfile(chemin):
            rel = os.path.relpath(chemin, racine)
            if rel not in vus and rel not in EXCLUS_COCKPIT:
                vus.add(rel)
                yield rel
        elif os.path.isdir(chemin):
            for base, dirs, fics in os.walk(chemin):
                dirs[:] = [d for d in dirs if d not in DIRS_EXCLUS
                           and not d.startswith("deferred")]
                for f in sorted(fics):
                    if not (f.endswith(EXT_TEXTE) or f == ".memlog.md"):
                        continue
                    rel = os.path.relpath(os.path.join(base, f), racine)
                    # Le dossier `implementation-artifacts` est vaste (KidSat) :
                    # on n'y prend que les stories DeskNode `dn*.md`.
                    if entree.endswith("implementation-artifacts"):
                        if not os.path.basename(rel).startswith("dn"):
                            continue
                    if rel in vus or rel in EXCLUS_COCKPIT:
                        continue
                    vus.add(rel)
                    yield rel


def balaye(racine, rels, motifs=None, saut_ligne=None):
    """Rend [(rel, ligne_1based, cle_motif, n, citation)] — n par LIGNE."""
    motifs = motifs or [c for c, _, _ in MOTIFS]
    out = []
    for rel in rels:
        p = os.path.join(racine, rel)
        try:
            txt = io.open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if "\x00" in txt[:4096]:
            continue
        for i, ligne in enumerate(txt.split("\n")):
            if saut_ligne and saut_ligne(rel, ligne):
                continue
            norm = normalise(ligne)
            for cle, rx, _lib in MOTIFS:
                if cle not in motifs:
                    continue
                n = len(rx.findall(norm))
                if n:
                    out.append((rel, i + 1, cle, n, ligne.strip()[:120]))
    return out


RE_LIGNE_MANIF = re.compile(
    r"^\|\s*(?P<depot>desknode|cockpit)\s*\|"
    r"\s*(?P<fichier>[^|]+?)\s*\|"
    r"\s*(?P<ligne>\d+)\s*\|"
    r"\s*(?P<motif>[^|]+?)\s*\|"
    r"\s*(?P<n>\d+)\s*\|"
    r"\s*(?P<cit>.*?)\s*\|"
    r"\s*(?P<verdict>FAUX|VRAI|HISTORIQUE|SANS-RAPPORT)\s*\|"
    r"\s*(?P<pourquoi>.*?)\s*\|\s*$")


def lit_manifeste(chemin):
    """Rend {(depot, fichier, ligne, motif): (n, verdict, pourquoi)} + erreurs."""
    entrees, erreurs = {}, []
    if not os.path.exists(chemin):
        return None, ["MANIFESTE INTROUVABLE : %s" % chemin]
    for n, l in enumerate(io.open(chemin, encoding="utf-8").read().split("\n"), 1):
        ls = l.strip()
        if not ls.startswith("|"):
            continue
        if set(ls) <= set("|-: "):
            continue
        m = RE_LIGNE_MANIF.match(ls)
        if not m:
            # ⛔ Une ligne de tableau qui RESSEMBLE a une entree et ne parse pas
            #    n'est PAS ignoree en silence : c'est le pire mode de panne
            #    d'une gate de comptage.
            champs = [c.strip() for c in ls.strip("|").split("|")]
            if champs and champs[0] in ("desknode", "cockpit"):
                erreurs.append("l.%d — entree NON PARSEE (%d champs) : %s"
                               % (n, len(champs), ls[:90]))
            continue
        cle = (m.group("depot"), m.group("fichier"),
               int(m.group("ligne")), m.group("motif"))
        if not m.group("pourquoi"):
            erreurs.append("l.%d — verdict SANS MOTIF" % n)
        if m.group("motif") not in [c for c, _, _ in MOTIFS]:
            erreurs.append("l.%d — motif INCONNU : %s" % (n, m.group("motif")))
        if cle in entrees:
            erreurs.append("l.%d — DOUBLON : %s" % (n, cle))
        entrees[cle] = (int(m.group("n")), m.group("verdict"), m.group("pourquoi"))
    return entrees, erreurs


def imprime_compte(trouves, titre, flux):
    par_fichier = {}
    for rel, ln, cle, n, cit in trouves:
        par_fichier.setdefault(rel, []).append((ln, cle, n, cit))
    total = sum(t[3] for t in trouves)
    flux.write("\n%s\n%s\n  %d occurrence(s) sur %d ligne(s) et %d fichier(s)\n"
               % (titre, "-" * len(titre), total, len(trouves), len(par_fichier)))
    for rel in sorted(par_fichier):
        occ = sorted(par_fichier[rel])
        flux.write("\n  %s  (%d occ.)\n" % (rel, sum(o[2] for o in occ)))
        for ln, cle, n, cit in occ:
            flux.write("     l.%-6d [%-12s] x%-2d %s\n" % (ln, cle, n, cit))
    par_motif = {}
    for _r, _l, cle, n, _c in trouves:
        par_motif[cle] = par_motif.get(cle, 0) + n
    flux.write("\n  -- par motif --\n")
    for cle, _rx, lib in MOTIFS:
        flux.write("     %-14s %3d   %s\n" % (cle, par_motif.get(cle, 0), lib))
    return total


def saut_autoreference(rel, ligne):
    """La ligne du tracker qui PARLE de dn4-15 : auto-reference declaree."""
    return rel.endswith("sprint-status-desknode.yaml") and CLE_STORY in ligne


def collecte(cockpit):
    """Rend (occ_arbitrees, occ_archive) — cles ('desknode'|'cockpit', ...)."""
    dn = [("desknode",) + t for t in
          balaye(DESKNODE, list(fichiers_desknode(DESKNODE)))]
    ck_aut = [("cockpit",) + t for t in
              balaye(cockpit, list(fichiers_cockpit(cockpit, AUTORITE_COCKPIT)),
                     saut_ligne=saut_autoreference)]
    # Les ARCHIVES : comptees pour les 4 motifs, mais seul `busid-en-dur` est
    # EXIGE arbitre — une recette se copie-colle, un fait date se lit.
    arch_tout = balaye(cockpit, list(fichiers_cockpit(cockpit, ARCHIVE_COCKPIT)))
    ck_arch_busid = [("cockpit",) + t for t in arch_tout if t[2] == "busid-en-dur"]
    ck_arch_reste = [("cockpit",) + t for t in arch_tout if t[2] != "busid-en-dur"]
    return dn + ck_aut + ck_arch_busid, ck_arch_reste


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--cockpit", default=COCKPIT_DEFAUT)
    ap.add_argument("--compte", action="store_true")
    ap.add_argument("--sortie", default=None)
    a = ap.parse_args()

    print("=" * 78)
    print("dn4-15 / AC6 — CHAQUE OCCURRENCE PORTE UN VERDICT")
    print("=" * 78)
    print("\ndepot code    : %s" % DESKNODE)
    print("depot cockpit : %s" % a.cockpit)
    print("motifs        : %s" % " · ".join(c for c, _, _ in MOTIFS))
    print("normalisation : NFD + diacritiques retires + minuscules"
          "   (⇒ `Facade` == `FACADE` == `facade`)")

    # ── AC6.5 : le cockpit est un ARGUMENT, et son absence est ROUGE ────────
    print("\n── 0. LES DEUX DEPOTS SONT LA (⛔ jamais un skip silencieux) ──────")
    cockpit_ok = ctrl(os.path.isdir(a.cockpit),
                      "le depot cockpit est atteignable",
                      a.cockpit if os.path.isdir(a.cockpit)
                      else "⛔ ABSENT — une gate scopee epingle VERT le meme defaut ailleurs")
    ctrl(os.path.isdir(DESKNODE), "le depot code est atteignable", DESKNODE)
    if not cockpit_ok:
        print("\n" + "=" * 78)
        print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
        print("=" * 78)
        return 1

    arbitre, archive = collecte(a.cockpit)

    print("\n── 1. CE QUI EST ECARTE, ET C'EST IMPRIME ────────────────────────")
    for rel in sorted(EXCLUS_DESKNODE):
        print("     desknode : %-62s auto-reference" % rel[-62:])
    for rel in sorted(EXCLUS_COCKPIT):
        print("     cockpit  : %-62s auto-ref. / genere" % rel[-62:])
    print("     cockpit  : la ligne `%s` du tracker" % CLE_STORY[:40])
    print("     dossiers : %s" % ", ".join(sorted(DIRS_EXCLUS)))
    print("     cockpit  : tout ce qui est HORS surface DeskNode (= KidSat)")
    print("     ARCHIVES : %d occurrence(s) sur %d ligne(s) — COMPTEES et LISTEES,"
          % (sum(t[4] for t in archive), len(archive)))
    print("                ⛔ non exigees arbitrees (⛔ sauf `busid-en-dur`) :")
    par_f = {}
    for _d, rel, _l, _c, n, _cit in archive:
        par_f[rel] = par_f.get(rel, 0) + n
    for rel in sorted(par_f):
        print("                  %-62s %d" % (rel[-62:], par_f[rel]))
    ctrl(True, "les exclusions sont DECLAREES, ⛔ pas silencieuses",
         "%d fichier(s), %d dossier(s), %d occ. d'archive"
         % (len(EXCLUS_DESKNODE) + len(EXCLUS_COCKPIT), len(DIRS_EXCLUS),
            sum(t[4] for t in archive)))

    if a.compte:
        flux = io.open(a.sortie, "w", encoding="utf-8") if a.sortie else sys.stdout
        flux.write("=" * 78 + "\n")
        flux.write("dn4-15 / T0 — COMPTE DE DEPART, PRODUIT PAR LE SCRIPT\n")
        flux.write("=" * 78 + "\n")
        dn = [t[1:] for t in arbitre if t[0] == "desknode"]
        ck = [t[1:] for t in arbitre if t[0] == "cockpit"]
        t1 = imprime_compte(dn, "A. DEPOT desknode — FAISANT AUTORITE, arbre ENTIER", flux)
        t2 = imprime_compte(ck, "B. DEPOT cockpit — FAISANT AUTORITE (+ busid-en-dur des archives)", flux)
        t3 = imprime_compte([t[1:] for t in archive],
                            "C. DEPOT cockpit — ARCHIVES : comptees, ⛔ non arbitrees", flux)
        flux.write("\n" + "=" * 78 + "\n")
        flux.write("A ARBITRER (A + B) : %d occurrence(s)\n" % (t1 + t2))
        flux.write("ARCHIVE   (C)      : %d occurrence(s), listees et non arbitrees\n" % t3)
        flux.write("TOTAL BALAYE       : %d occurrence(s)\n" % (t1 + t2 + t3))
        flux.write("=" * 78 + "\n")
        if a.sortie:
            flux.close()
            print("\n  compte ecrit dans %s" % a.sortie)
            print("  A ARBITRER : %d   ·   ARCHIVE : %d   ·   TOTAL : %d"
                  % (t1 + t2, t3, t1 + t2 + t3))
        print("\n  MODE COMPTE SEUL — le manifeste n'est pas exige.")
        print("=" * 78)
        return 0

    # ── AC6.3 : toute occurrence de l'arbre est au manifeste, avec un verdict ─
    print("\n── 2. LE MANIFESTE COUVRE L'ARBRE, LIGNE PAR LIGNE ───────────────")
    manif, erreurs = lit_manifeste(os.path.join(DESKNODE, MANIFESTE))
    if manif is None:
        for e in erreurs:
            ctrl(False, "manifeste", e)
        print("\n" + "=" * 78)
        print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
        print("=" * 78)
        return 1
    for e in erreurs:
        ctrl(False, "manifeste mal forme", e)
    ctrl(bool(manif), "le manifeste est lisible et non vide",
         "%d entree(s)" % len(manif))

    arbre = {(d, r, l, c): (n, cit) for d, r, l, c, n, cit in arbitre}

    manquantes = sorted(set(arbre) - set(manif))
    for cle in manquantes[:40]:
        ctrl(False, "occurrence NOUVELLE ou DEPLACEE",
             "%s:%s:%d [%s] %s" % (cle[0], cle[1][-34:], cle[2], cle[3],
                                   arbre[cle][1][:52]))
    if len(manquantes) > 40:
        ctrl(False, "… et d'autres", "%d au total" % len(manquantes))
    ctrl(not manquantes, "toute occurrence de l'arbre est AU MANIFESTE",
         "%d ligne(s) arbitree(s)" % len(arbre))

    fantomes = sorted(set(manif) - set(arbre))
    for cle in fantomes[:40]:
        ctrl(False, "ligne de manifeste SANS occurrence dans l'arbre",
             "%s:%s:%d [%s]" % (cle[0], cle[1][-40:], cle[2], cle[3]))
    ctrl(not fantomes, "le manifeste ne cite aucune occurrence FANTOME",
         "%d ligne(s) de manifeste" % len(manif))

    ecarts_n = [(k, manif[k][0], arbre[k][0]) for k in sorted(set(manif) & set(arbre))
                if manif[k][0] != arbre[k][0]]
    for k, a_, b_ in ecarts_n[:20]:
        ctrl(False, "le `n` du manifeste ne colle pas a l'arbre",
             "%s:%s:%d [%s] manifeste=%d arbre=%d" % (k[0], k[1][-28:], k[2], k[3], a_, b_))
    ctrl(not ecarts_n, "le `n` de chaque ligne colle a l'arbre", "%d ligne(s)" % len(manif))

    # ── AC2.4 : la somme des verdicts = le compte ───────────────────────────
    print("\n── 3. LA SOMME DES VERDICTS = LE COMPTE (AC2.4) ──────────────────")
    compte = {v: 0 for v in VERDICTS}
    for n, v, _p in manif.values():
        compte[v] += n
    total_arbre = sum(n for n, _c in arbre.values())
    for v in VERDICTS:
        print("     %-14s %3d" % (v, compte[v]))
    ctrl(sum(compte.values()) == total_arbre,
         "somme des verdicts == occurrences de l'arbre",
         "%d vs %d" % (sum(compte.values()), total_arbre))

    # ── AC6.4 : la console n'enseigne plus le chiffre mort ──────────────────
    print("\n── 4. LA CONSOLE N'ENSEIGNE PLUS UN CHIFFRE MORT (AC5) ───────────")
    csl = os.path.join(DESKNODE, "firmware/desknode/main/dn_console.c")
    txt = io.open(csl, encoding="utf-8", errors="replace").read()
    n340 = len(re.findall(r"340\s*\.\.\s*350", txt))
    ctrl(n340 == 0, "dn_console.c ne contient plus la litterale 340..350",
         "%d occurrence(s)" % n340)
    ui = io.open(os.path.join(DESKNODE, "firmware/desknode/main/dn_ui.c"),
                 encoding="utf-8", errors="replace").read()
    n340u = len(re.findall(r"340\s*\.\.\s*350", ui))
    ctrl(n340u == 0, "dn_ui.c ne contient plus la litterale 340..350",
         "%d occurrence(s)" % n340u)

    # ⛔ AC5.2 : et on ne lui SUBSTITUE pas `337..347`. Les seules mentions
    #    admises sont celles qui racontent la LECON (elles vivent deja dans
    #    `dn_ui.c:217-245` et `dn_console.c:4538`, ⛔ pas dans un `printf`).
    for nom, contenu in (("dn_console.c", txt), ("dn_ui.c", ui)):
        subst = [l.strip()[:70] for l in contenu.split("\n")
                 if re.search(r"337\s*\.\.\s*347", l) and "printf" in l]
        ctrl(not subst, "%s : ⛔ 337..347 n'est SUBSTITUE dans aucun printf" % nom,
             "%d ligne(s) : %s" % (len(subst), subst[:2]) if subst
             else "aucune substitution")

    for nom, contenu, mini in (("dn_console.c", txt, 2), ("dn_ui.c", ui, 2)):
        n = len(re.findall(r"widget jauge", normalise(contenu)))
        ctrl(n >= mini, "%s renvoie a `widget jauge`" % nom,
             "%d renvoi(s), %d attendu(s) au minimum" % (n, mini))

    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return 1 if ko_total[0] else 0


if __name__ == "__main__":
    sys.exit(main())

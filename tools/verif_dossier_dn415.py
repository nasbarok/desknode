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
     ⚠️ LE RATIO PUBLIE JUSQU'AU 2026-08-30 (« 5 sur 29 ») ADDITIONNAIT DEUX
     POPULATIONS DISJOINTES, et la revue l'a repris : `29` est le compte des
     `VL53L0X`, or QUATRE des cinq citees sont des `facade`/`Facade`.
     LES RATIOS VRAIS, RE-MESURES :
       · `vl53l0x` : 1 sur 29  — `capteurs-i2c.md`, en casse basse ;
       · `facade`  : 4 sur 16  — `agent/dn_agent.py` x2, `tools/fixtures/`, et
         `dn_display.h` (`Facade` = le PATRON DE CONCEPTION, SANS-RAPPORT).
     ⇒ Une story dont la these est « un `grep` mesure LE MOT, pas LE DEFAUT »
     avait publie un ratio qui melange deux comptes. Le defaut vise reste entier :
     `dn4-14` a PERDU UNE GATE ENTIERE dessus (`/* orange */` en minuscules
     faisait sauter une case sur six, EN SILENCE).

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

  ── AJOUTS DE LA REVUE DE CODE 3 COUCHES DU 2026-08-30 ───────────────────

  ✅ ELLE CONFRONTE DESORMAIS LA CITATION AU TEXTE DE L'ARBRE. C'etait LE trou
     central : la cle ne portait pas le texte, si bien qu'une INVERSION DE SENS
     SUR PLACE passait au vert. Mesure : `capteurs-i2c.md:380` retourne de
     « LE 3e CAPTEUR N'EST PAS UN VL53L0X » en « … EST BIEN UN VL53L0X »
     ⇒ 14 OK / 0 KO, rc=0. Le dossier affirmait l'inverse de ce que la story
     protege, et l'instrument certifiait que tout allait bien.
     ⚠️ COUT DECLARE : les deux citations sont des troncatures a 120 caracteres,
     on compare donc le PREFIXE COMMUN. Une inversion qui n'arriverait qu'APRES
     ~110 caracteres de la ligne echapperait encore au controle.

  ✅ `FAUX > 0` FAIT ROUGIR (decision owner du 2026-08-30). Le manifeste ecrit
     « FAUX VAUT ZERO, ET C'EST LE RESULTAT » — c'etait de la PROSE que rien ne
     tenait. Consigner un defaut AVANT de le corriger : c'est le role du LEDGER.

  ⚠️ ELLE NE LIT TOUJOURS PAS CE QUI EST HORS DE SON PERIMETRE DE FICHIERS.
     Le perimetre est une LISTE BLANCHE d'extensions + quelques noms explicites,
     et elle est IMPRIMEE a chaque tir. Trois defauts plantes y echappaient
     avant le 2026-08-30 (`.rst`, `Kconfig.projbuild`, `docs/cablage/`).
     ⇒ Un motif depose dans un type de fichier NON LISTE reste invisible.

  ⚠️ CE QU'ELLE NE VOIT TOUJOURS PAS, ET C'EST ECRIT :
       · une reformulation qui n'emploie AUCUN des cinq motifs (« la bande de
         dix pixels sous la jauge ») — elle compte des motifs, pas des idees ;
       · un busid ecrit en toutes lettres (« trois tiret un ») ;
       · le SENS d'un verdict : `HISTORIQUE` pose sur une phrase qui affirme au
         present reste `HISTORIQUE`. Le verdict est un acte humain.

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

  ✅ LES CORRECT-COURSES QUI PARLENT DE DESKNODE FONT AUTORITE (ajout du
     2026-08-30). Ils PORTENT les decisions D4/D6/D9/D12, et ils etaient hors
     surface : `sprint-change-proposal-2026-08-20.md` porte 14 lignes a motif —
     dont le §1.1 « monte sur la facade » — ET A ETE EDITE PAR CETTE STORY, sans
     jamais etre ni compte, ni liste, ni arbitre.

  EXCLUSIONS, ⛔ AUCUNE N'EST SILENCIEUSE — elles sont IMPRIMEES a chaque tir :
    · le manifeste lui-meme et CETTE gate — ils CITENT les motifs, les exiger
      arbitres serait circulaire ;
    · la story `dn4-15-*.md` (GLOB) et LA LIGNE DE STATUT YAML `dn4-15-*` DU
      TRACKER — c'est la SPEC qui decrit les defauts. ⚠️ Le filtre porte sur la
      CLE EN DEBUT DE LIGNE : `CLE_STORY in ligne` etait une PORTE DEROBEE (une
      recette `--busid 3-1` suffixee de la cle passait au vert) ;
    · `mesures/` et `sprint-board-desknode.html` — captures datees et fichier
      GENERE, ils ne se reecrivent pas ;
    · `_bmad-output/implementation-artifacts/deferred*/` — ledger deporte ;
    · `.git/`, `build*/` (⚠️ PREFIXE : le depot genere `build-ac5/`, `build-xip/`
      que `.gitignore` ignore et que la gate BALAYAIT — 76 fichiers d'artefacts,
      donc un compte NON REPRODUCTIBLE d'une machine a l'autre),
      `managed_components/`, `__pycache__/`, `venv/`, binaires.
    ⛔ `assets/` ET `cablage/` NE SONT PLUS EXCLUS : ils ne portent que des
      binaires, deja ecartes par le filtre d'extension — les exclure cachait le
      texte qu'on y deposerait (mesure : `docs/cablage/note.md` passait au vert).

Usage :
    python3 tools/verif_dossier_dn415.py [--cockpit CHEMIN] [--compte [--sortie F]]

  --compte   : mode COMPTE SEUL (T0). N'exige pas le manifeste, imprime le
               releve fichier par fichier ET ligne par ligne. ⚠️ Il rend
               desormais 1 si un controle a rougi — son `return 0` etait
               INCONDITIONNEL, donc un appelant cablant `--compte` obtenait un
               VERT PERPETUEL.
  --sortie   : fichier ou ecrire le releve de `--compte` (le dossier est cree).
               ⛔ Sans `--compte`, il est IGNORE — et il ne l'etait pas dit.
  --cockpit  : racine du depot cockpit. ⛔ S'IL EST ABSENT, LA GATE SORT EN
               ROUGE EN LE DISANT — ⛔ JAMAIS un `skip` silencieux (AC6.5).
               Motif : « une gate scopee epingle vert le meme defaut ailleurs ».

OU ELLE EST TIREE : etape de la skill `/desknode-board` (decision owner du
  2026-08-30). ⚠️ CONTREPARTIE ECRITE : c'est un FILET DE SEANCE, ⛔ PAS un
  filet de commit — elle ne voit pas un commit fait hors seance.

Sortie : exit 0 si tout passe, 1 sinon.
"""

import argparse
import fnmatch
import glob
import io
import os
import re
import sys
import unicodedata

DESKNODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COCKPIT_DEFAUT = os.path.expanduser("~/projects/compagnon_project")

MANIFESTE = "docs/dn4-15-arbitrage.md"

VERDICTS = ("FAUX", "VRAI", "HISTORIQUE", "SANS-RAPPORT")

# ── LES MOTIFS ──────────────────────────────────────────────────────────────
# Ils sont appliques sur une ligne NORMALISEE : NFD, marques diacritiques
# retirees, minuscules. ⇒ `Façade`, `FACADE`, `facade`, `façade` = un seul motif.
#
# 🔴 REVUE DE CODE 3 COUCHES DU 2026-08-30 — LES MOTIFS ETAIENT CONTOURNABLES,
#    ET C'EST MESURE. Toutes les formes ci-dessous rendaient 0 avant correctif :
#      · `340...350`, `340-350`, `340 a 350`  (le litteral ne voyait que `340..350`)
#      · `--busid=3-1`, `-b 3-1`, `--busid "3-1"`, `BUSID=3-1`, `busid : 3-1`
#        ⇒ une recette qui DETACHE LE MAUVAIS PERIPHERIQUE passait au VERT.
#      · `506..516` — la SECONDE coordonnee morte. AC5.3 la met au « meme
#        traitement, meme renvoi », et la gate ne la surveillait PAS DU TOUT :
#        filet asymetrique, defaut a moitie ferme.
#
# La 4e case est une GARDE DE LIGNE (ou None). Elle voit la ligne normalisee
# ENTIERE, la ou un lookahead de regex ne peut pas regarder en arriere.


def _garde_busid(norm):
    """`ici : 3-1` n'est une RECETTE que dans un contexte busid/usbipd.
    Mesure : sans cette garde, `ici : 2026-08-30` et `ici : 5-8 mini-posters`
    etaient epingles comme des busid (faux positifs vus a la revue)."""
    return "busid" in norm or "usbipd" in norm


# Une plage de coordonnees, quelle que soit sa graphie : `..`, `...`, `-`, ` a `.
RX_PLAGE = r"(?<!\d)%s\s*(?:\.{2,3}|-|a)\s*%s(?!\d)"

MOTIFS = [
    # (cle, regex sur ligne normalisee, libelle, garde de ligne | None)
    ("facade", re.compile(r"facade"),
     "le module « en facade » (3 homonymes)", None),
    ("vl53l0x", re.compile(r"vl53l0x"),
     "la puce VL53L0X (le module est un VL6180X)", None),
    ("340..350", re.compile(RX_PLAGE % ("340", "350")),
     "la coordonnee morte y = 340..350 (jauge RAM, dn4-1)", None),
    ("506..516", re.compile(RX_PLAGE % ("506", "516")),
     "la coordonnee morte y = 506..516 (VENTILOS, dn3-2) — AC5.3", None),
    # Le busid EN DUR DANS UNE RECETTE. ⛔ Pas les mentions narratives :
    # « le busid a valu `3-1` le 26/08 » est un FAIT DATE, pas une consigne.
    # ⛔ Les annees sont exclues par lookahead : `ici : 2026-08` n'est pas un busid.
    ("busid-en-dur", re.compile(
        r"(?:--busid|(?<![a-z0-9-])-b|\bbusid|\bici)\s*[:=]?\s*[`'\"]?"
        r"(?!(?:19|20)\d\d-)\d+-\d+"),
     "un busid CONSTANT dans une recette (3 valeurs ont ete vraies)",
     _garde_busid),
]

CLES_MOTIFS = [m[0] for m in MOTIFS]

# 🔴 REVUE 2026-08-30 — LA LISTE BLANCHE ETAIT UNE FUITE, ET C'EST MESURE.
#    Trois defauts plantes passaient au VERT en un seul tir :
#      `docs/RECETTE-FLASH.rst` (`--busid=3-1`), `firmware/desknode/Kconfig.projbuild`
#      (`VL53L0X`), `docs/cablage/note.md` (`340..350`).
#    ⛔ `assets/` et `cablage/` NE SONT PLUS EXCLUS : ils ne portent que des
#    binaires, que le filtre d'extension ecarte deja — les exclure cachait le
#    texte qu'on y deposerait.
EXT_TEXTE = (".md", ".yaml", ".yml", ".c", ".h", ".cpp", ".hpp", ".py", ".sh",
             ".ps1", ".bat", ".txt", ".defaults", ".json", ".cfg", ".in",
             ".scad", ".patch", ".rst", ".csv", ".cmake", ".toml", ".ini",
             ".conf", ".projbuild", ".rules", ".service")

# Fichiers de texte SANS extension utile, ou a extension composee. `sdkconfig`
# fait 85 Ko et c'est celui que la chaine LIT REELLEMENT ; les variantes
# `sdkconfig.defaults.*` sont SUIVIES PAR GIT et vivent dans le fichier meme ou
# vivait LE SEUL vrai defaut du lot (`sdkconfig.defaults:71`).
NOMS_TEXTE = {"sdkconfig", "Makefile", "CMakeLists.txt", "Dockerfile", "LICENSE"}
PREFIXES_TEXTE = ("sdkconfig", "Kconfig", "partitions")

# ⛔ `build` ETAIT LITTERAL alors que le depot genere `build-ac5/`, `build-xip/`
#    — que `.gitignore:6` ignore (`build-*/`). Mesure : 76 fichiers d'artefacts
#    entraient dans le compte, qui n'etait donc PAS reproductible d'une machine
#    a l'autre. Le prefixe ferme le trou.
DIRS_EXCLUS = {".git", "managed_components", "node_modules",
               "__pycache__", "mesures", "venv", ".venv"}
DIRS_EXCLUS_PREFIXES = ("build",)

# Auto-reference : ces fichiers CITENT les motifs pour les traiter.
EXCLUS_DESKNODE = {
    MANIFESTE,
    "tools/verif_dossier_dn415.py",
}
# ⚠️ Des GLOBS, ⛔ pas des chemins litteraux : le manifeste declare l'exclusion
#    en `dn4-15-*.md` et la gate ne l'honorait que mot pour mot. Un
#    `dn4-15-…-review.md` aurait ete exige arbitre alors que le manifeste le
#    dit exclu ; et renommer le slug de la story y faisait rentrer SA PROPRE SPEC.
EXCLUS_COCKPIT = {
    "_bmad-output/implementation-artifacts/dn4-15-*.md",
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

# 🔴 REVUE 2026-08-30 — LES CORRECT-COURSES ETAIENT HORS SURFACE, ET ILS
#    PORTENT LES DECISIONS (D4/D6/D9/D12). Mesure :
#    `sprint-change-proposal-2026-08-20.md` porte 14 lignes a motif — dont le
#    §1.1 « monte sur la facade » — ET A ETE EDITE PAR CETTE STORY, sans jamais
#    etre ni compte, ni liste, ni arbitre. La gate qui se reclame de « une gate
#    scopee epingle vert le meme defaut ailleurs » reproduisait la faute.
#    ⇒ Le filtre est le CONTENU, ⛔ pas une liste de dates qui vieillira : un
#    correct-course qui parle de DeskNode fait autorite pour DeskNode.
AUTORITE_COCKPIT_GLOBS = [
    ("_bmad-output/planning-artifacts/sprint-change-proposal-*.md", "desknode"),
]

ok_total = [0]
ko_total = [0]

# ── CE QUI A ETE SAUTE PENDANT LE TIR — ⛔ PLUS AUCUN SAUT N'EST SILENCIEUX ──
# Revue 2026-08-30 : trois sauts se faisaient SANS UN MOT, en contradiction avec
# l'en-tete (« AUCUNE EXCLUSION N'EST SILENCIEUSE ») : un fichier illisible
# comptait 0 occurrence, une entree de surface qui ne resout pas etait ignoree
# (renommer `.claude/skills/desknode-board` retirait la surface d'audit sans
# qu'aucun fantome ne trahisse la perte), et `deferred*/` n'etait pas declare.
illisibles = []
surface_absente = []


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


def est_texte(nom):
    """Un fichier de DOSSIER, ⛔ pas un artefact binaire."""
    return (nom.endswith(EXT_TEXTE) or nom in NOMS_TEXTE
            or nom.startswith(PREFIXES_TEXTE) or nom == ".memlog.md")


def dossier_exclu(d):
    return d in DIRS_EXCLUS or d.startswith(DIRS_EXCLUS_PREFIXES)


def exclu_cockpit(rel):
    """EXCLUS_COCKPIT accepte des GLOBS — le manifeste en declare un
    (`dn4-15-*.md`) que la gate n'honorait que comme chemin LITTERAL."""
    return any(fnmatch.fnmatch(rel, g) for g in EXCLUS_COCKPIT)


def fichiers_desknode(racine):
    for base, dirs, fics in os.walk(racine):
        dirs[:] = [d for d in dirs if not dossier_exclu(d)]
        for f in sorted(fics):
            if not est_texte(f):
                continue
            rel = os.path.relpath(os.path.join(base, f), racine)
            if rel in EXCLUS_DESKNODE:
                continue
            yield rel


def fichiers_cockpit(racine, surface, globs=None):
    vus = set()
    for motif_glob, exige in (globs or []):
        trouves = sorted(glob.glob(os.path.join(racine, motif_glob)))
        if not trouves:
            surface_absente.append(motif_glob)
            continue
        for chemin in trouves:
            rel = os.path.relpath(chemin, racine)
            if rel in vus or exclu_cockpit(rel):
                continue
            try:
                contenu = io.open(chemin, encoding="utf-8", errors="replace").read()
            except OSError as e:
                illisibles.append((rel, str(e)))
                continue
            if exige and exige not in normalise(contenu):
                continue
            vus.add(rel)
            yield rel
    for entree in surface:
        chemin = os.path.join(racine, entree)
        if not os.path.exists(chemin):
            # ⛔ PLUS DE SAUT SILENCIEUX : une surface declaree qui ne resout
            #    ni en fichier ni en dossier est un TROU D'AUDIT, pas un detail.
            surface_absente.append(entree)
            continue
        if os.path.isfile(chemin):
            rel = os.path.relpath(chemin, racine)
            if rel not in vus and not exclu_cockpit(rel):
                vus.add(rel)
                yield rel
        elif os.path.isdir(chemin):
            for base, dirs, fics in os.walk(chemin):
                dirs[:] = [d for d in dirs if not dossier_exclu(d)
                           and not d.startswith("deferred")]
                for f in sorted(fics):
                    if not est_texte(f):
                        continue
                    rel = os.path.relpath(os.path.join(base, f), racine)
                    # Le dossier `implementation-artifacts` est vaste (KidSat) :
                    # on n'y prend que les artefacts DeskNode. ⛔ `dn*` seul
                    # ratait `code-reviews/cr-dn4-17-desknode.patch`, qui porte
                    # `detach --busid 3-1` — LITTERALEMENT le cas d'usage
                    # invoque pour justifier l'exception « archives comprises ».
                    if entree.endswith("implementation-artifacts"):
                        bn = os.path.basename(rel)
                        if not (bn.startswith("dn") or "-dn" in bn):
                            continue
                    if rel in vus or exclu_cockpit(rel):
                        continue
                    vus.add(rel)
                    yield rel


def balaye(racine, rels, motifs=None, saut_ligne=None):
    """Rend [(rel, ligne_1based, cle_motif, n, citation)] — n par LIGNE."""
    motifs = motifs or list(CLES_MOTIFS)
    out = []
    for rel in rels:
        p = os.path.join(racine, rel)
        try:
            txt = io.open(p, encoding="utf-8", errors="replace").read()
        except OSError as e:
            # ⛔ PLUS DE SAUT SILENCIEUX : un fichier illisible (droits, lien
            #    symbolique casse, supprime pendant le balayage) comptait
            #    0 occurrence et la gate restait VERTE.
            illisibles.append((rel, str(e)))
            continue
        if "\x00" in txt[:4096]:
            continue
        for i, ligne in enumerate(txt.split("\n")):
            if saut_ligne and saut_ligne(rel, ligne):
                continue
            norm = normalise(ligne)
            for cle, rx, _lib, garde in MOTIFS:
                if cle not in motifs:
                    continue
                if garde and not garde(norm):
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
    """Rend {(depot, fichier, ligne, motif): (n, verdict, pourquoi, cit)} + erreurs.

    🔴 `cit` EST DESORMAIS CONSERVEE. Elle etait parsee puis JETEE : la gate
       clait sur (depot, fichier, ligne, motif) SANS LE TEXTE, si bien qu'une
       INVERSION DE SENS SUR PLACE passait au vert. Mesure du 2026-08-30 :
       `capteurs-i2c.md:380` edite de « LE 3e CAPTEUR N'EST PAS UN VL53L0X » en
       « … EST BIEN UN VL53L0X » ⇒ BILAN 14 OK / 0 KO, rc=0. Le manifeste
       promettait pourtant « si le texte change, le verdict est a refaire ».
    """
    entrees, erreurs = {}, []
    if not os.path.isfile(chemin):
        # ⛔ `os.path.exists` laissait passer un REPERTOIRE ⇒ IsADirectoryError
        #    en traceback, sans bilan et sans message.
        return None, ["MANIFESTE INTROUVABLE OU NON REGULIER : %s" % chemin]
    try:
        # ⛔ `errors="replace"` comme le balayage : un manifeste enregistre en
        #    latin-1 levait un UnicodeDecodeError NON RATTRAPE — un traceback
        #    la ou la gate promet un [KO].
        brut = io.open(chemin, encoding="utf-8", errors="replace").read()
    except OSError as e:
        return None, ["MANIFESTE ILLISIBLE : %s (%s)" % (chemin, e)]
    for n, l in enumerate(brut.split("\n"), 1):
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
        if m.group("motif") not in CLES_MOTIFS:
            erreurs.append("l.%d — motif INCONNU : %s" % (n, m.group("motif")))
        if cle in entrees:
            erreurs.append("l.%d — DOUBLON : %s" % (n, cle))
        entrees[cle] = (int(m.group("n")), m.group("verdict"),
                        m.group("pourquoi"), m.group("cit"))
    return entrees, erreurs


def cit_comparable(s):
    """Les citations traversent un tableau Markdown : les `|` y sont echappes,
    et les espaces se normalisent. On compare le SENS, ⛔ pas la mise en forme."""
    s = normalise(s).replace("\\|", "|")
    return re.sub(r"\s+", " ", s).strip()


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
    for cle, _rx, lib, _g in MOTIFS:
        flux.write("     %-14s %3d   %s\n" % (cle, par_motif.get(cle, 0), lib))
    return total


# ⛔ LA LIGNE DE STATUT YAML DE LA STORY, ⛔ PAS « LA CLE QUELQUE PART ».
#    L'ancien filtre etait `CLE_STORY in ligne` — une PORTE DEROBEE sur une
#    chaine publique et devinable. Mesure du 2026-08-30 : une ligne portant les
#    quatre motifs ET une recette `usbipd bind --busid 3-1` EXECUTABLE, suffixee
#    de la cle, passait a `14 OK / 0 KO`. Desormais la cle doit ouvrir la ligne
#    (indentation + `cle:`), ce qu'un commentaire ne peut pas faire.
RE_LIGNE_STATUT_STORY = re.compile(r"^\s*" + re.escape(CLE_STORY) + r"\s*:")


def saut_autoreference(rel, ligne):
    """La LIGNE DE STATUT de dn4-15 au tracker : auto-reference declaree."""
    return (rel.endswith("sprint-status-desknode.yaml")
            and RE_LIGNE_STATUT_STORY.match(ligne) is not None)


def collecte(cockpit):
    """Rend (occ_arbitrees, occ_archive) — cles ('desknode'|'cockpit', ...)."""
    dn = [("desknode",) + t for t in
          balaye(DESKNODE, list(fichiers_desknode(DESKNODE)))]
    ck_aut = [("cockpit",) + t for t in
              balaye(cockpit,
                     list(fichiers_cockpit(cockpit, AUTORITE_COCKPIT,
                                           AUTORITE_COCKPIT_GLOBS)),
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
    print("motifs        : %s" % " · ".join(CLES_MOTIFS))
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
    print("     cockpit  : `%s*/` sous implementation-artifacts (ledger deporte)"
          % "deferred")
    print("     extensions balayees : %s" % ", ".join(EXT_TEXTE))
    print("     noms de texte sans extension : %s"
          % ", ".join(sorted(NOMS_TEXTE) + [p + "*" for p in PREFIXES_TEXTE]))
    ctrl(True, "les exclusions sont DECLAREES, ⛔ pas silencieuses",
         "%d fichier(s), %d dossier(s), %d occ. d'archive"
         % (len(EXCLUS_DESKNODE) + len(EXCLUS_COCKPIT), len(DIRS_EXCLUS),
            sum(t[4] for t in archive)))

    # ⛔ LES SAUTS SUBIS — ils etaient SILENCIEUX, ils sont maintenant ROUGES.
    for rel, err in illisibles[:10]:
        ctrl(False, "fichier ILLISIBLE — il comptait 0 occurrence en silence",
             "%s (%s)" % (rel[-40:], err[:40]))
    if len(illisibles) > 10:
        ctrl(False, "… et d'autres fichiers illisibles",
             "%d au total" % len(illisibles))
    for entree in surface_absente[:10]:
        ctrl(False, "surface d'audit DECLAREE mais ABSENTE — trou d'audit",
             entree[-56:])
    ctrl(not illisibles and not surface_absente,
         "aucun saut subi (illisible / surface absente)",
         "%d illisible(s), %d surface(s) absente(s)"
         % (len(illisibles), len(surface_absente)))

    if a.compte:
        if a.sortie:
            try:
                rep = os.path.dirname(os.path.abspath(a.sortie))
                if rep:
                    os.makedirs(rep, exist_ok=True)
            except OSError as e:
                ctrl(False, "le dossier de --sortie est creable", str(e)[:50])
                print("\n" + "=" * 78)
                print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
                print("=" * 78)
                return 1
        try:
            flux = io.open(a.sortie, "w", encoding="utf-8") if a.sortie else sys.stdout
        except OSError as e:
            ctrl(False, "--sortie est ouvrable en ecriture", str(e)[:50])
            print("\n" + "=" * 78)
            print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
            print("=" * 78)
            return 1
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
        print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
        print("=" * 78)
        # ⛔ `return 0` etait INCONDITIONNEL : un appelant qui cablerait
        #    `--compte` (le mode documente en tete de l'usage) obtenait un VERT
        #    PERPETUEL, meme avec des fichiers illisibles ou une surface absente.
        return 1 if ko_total[0] else 0

    # ── AC6.3 : toute occurrence de l'arbre est au manifeste, avec un verdict ─
    print("\n── 2. LE MANIFESTE COUVRE L'ARBRE, LIGNE PAR LIGNE ───────────────")
    chemin_manif = os.path.join(DESKNODE, MANIFESTE)
    manif, erreurs = lit_manifeste(chemin_manif)
    try:
        brut_manif = io.open(chemin_manif, encoding="utf-8",
                             errors="replace").read()
    except OSError:
        brut_manif = ""
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
    if len(fantomes) > 40:
        ctrl(False, "… et d'autres fantomes", "%d au total" % len(fantomes))
    ctrl(not fantomes, "le manifeste ne cite aucune occurrence FANTOME",
         "%d ligne(s) de manifeste" % len(manif))

    ecarts_n = [(k, manif[k][0], arbre[k][0]) for k in sorted(set(manif) & set(arbre))
                if manif[k][0] != arbre[k][0]]
    for k, a_, b_ in ecarts_n[:20]:
        ctrl(False, "le `n` du manifeste ne colle pas a l'arbre",
             "%s:%s:%d [%s] manifeste=%d arbre=%d" % (k[0], k[1][-28:], k[2], k[3], a_, b_))
    if len(ecarts_n) > 20:
        ctrl(False, "… et d'autres ecarts de `n`", "%d au total" % len(ecarts_n))
    ctrl(not ecarts_n, "le `n` de chaque ligne colle a l'arbre", "%d ligne(s)" % len(manif))

    # 🔴 LA CITATION EST CONFRONTEE A LA SOURCE — LE TROU CENTRAL DE LA REVUE.
    #    La cle ne porte pas le texte : une INVERSION DE SENS SUR PLACE passait
    #    au vert. Mesure : « LE 3e CAPTEUR N'EST PAS UN VL53L0X » retourne en
    #    « … EST BIEN UN VL53L0X » ⇒ 14 OK / 0 KO. Le verdict restait colle a un
    #    texte qui avait change de sens.
    derives = []
    for k in sorted(set(manif) & set(arbre)):
        a_cit, b_cit = cit_comparable(manif[k][3]), cit_comparable(arbre[k][1])
        # ⚠️ Les DEUX citations sont des troncatures a 120 car. de la MEME
        #    ligne, mais le manifeste echappe ses `|` : la troncature ne tombe
        #    donc pas au meme endroit. On compare le PREFIXE COMMUN, ⛔ pas les
        #    longueurs. Cout declare : une inversion de sens qui n'arriverait
        #    qu'APRES ~110 caracteres echapperait au controle.
        n = min(len(a_cit), len(b_cit))
        if n and a_cit[:n] != b_cit[:n]:
            derives.append(k)
    for k in derives[:20]:
        ctrl(False, "le TEXTE a change sous un verdict inchange",
             "%s:%s:%d [%s]\n         manifeste : %s\n         arbre     : %s"
             % (k[0], k[1][-28:], k[2], k[3],
                manif[k][3][:70], arbre[k][1][:70]))
    if len(derives) > 20:
        ctrl(False, "… et d'autres textes derives", "%d au total" % len(derives))
    ctrl(not derives,
         "la citation du manifeste colle au TEXTE de l'arbre",
         "%d ligne(s) confrontee(s) — le verdict suit le sens, ⛔ pas la ligne"
         % len(set(manif) & set(arbre)))

    # ── AC2.4 : la somme des verdicts = le compte ───────────────────────────
    print("\n── 3. LA SOMME DES VERDICTS = LE COMPTE (AC2.4) ──────────────────")
    compte = {v: 0 for v in VERDICTS}
    for n, v, _p, _c in manif.values():
        compte[v] += n
    total_arbre = sum(n for n, _c in arbre.values())
    for v in VERDICTS:
        print("     %-14s %3d" % (v, compte[v]))
    ctrl(sum(compte.values()) == total_arbre,
         "somme des verdicts == occurrences de l'arbre",
         "%d vs %d" % (sum(compte.values()), total_arbre))

    # 🔴 DECISION OWNER DU 2026-08-30 : `FAUX > 0` DOIT ROUGIR.
    #    Le manifeste ecrit « FAUX VAUT ZERO, ET C'EST LE RESULTAT » — c'etait
    #    une affirmation de PROSE que rien ne tenait : basculer un verdict en
    #    `FAUX` affichait `FAUX 1` PUIS `14 OK / 0 KO`, rc=0.
    #    Motif : un `FAUX` au manifeste EST un mensonge connu reste dans le
    #    dossier — ce que cette story existe pour interdire. Consigner un defaut
    #    AVANT de le corriger, c'est le role du LEDGER, ⛔ pas du manifeste.
    faux = sorted(k for k, v in manif.items() if v[1] == "FAUX")
    for k in faux[:20]:
        ctrl(False, "occurrence encore verdictee FAUX",
             "%s:%s:%d [%s]" % (k[0], k[1][-40:], k[2], k[3]))
    ctrl(not faux, "⛔ AUCUNE occurrence ne reste `FAUX` (decision owner)",
         "FAUX = %d" % compte["FAUX"])

    # ── LES RECAPITULATIFS DU MANIFESTE COLLENT-ILS A SON PROPRE DETAIL ? ───
    # Ils n'etaient controles par RIEN : la gate recompte depuis les lignes
    # detaillees et ne lisait jamais la prose de tete. Au premier ajout/retrait,
    # ces chiffres derivaient EN SILENCE — dans le fichier meme dont la raison
    # d'etre est que le dossier ne mente plus sur ses chiffres.
    par_motif_manif = {}
    for k, v in manif.items():
        par_motif_manif[k[3]] = par_motif_manif.get(k[3], 0) + v[0]
    annonces, ecarts_recap = {}, []
    for l in brut_manif.split("\n"):
        m = re.match(r"^\|\s*[`*]*([A-Za-z0-9._-]+)[`*]*\s*\|\s*\**(\d+)\**\s*\|\s*$",
                     l.strip())
        if m:
            annonces[m.group(1)] = int(m.group(2))
    for cle_a, val in sorted(annonces.items()):
        reel = compte.get(cle_a, par_motif_manif.get(cle_a))
        if reel is not None and reel != val:
            ecarts_recap.append("%s : annonce %d, detail %d" % (cle_a, val, reel))
    if "TOTAL" in annonces and annonces["TOTAL"] != sum(compte.values()):
        ecarts_recap.append("TOTAL : annonce %d, detail %d"
                            % (annonces["TOTAL"], sum(compte.values())))
    for e in ecarts_recap:
        ctrl(False, "le recapitulatif du manifeste ne colle pas au detail", e)
    ctrl(not ecarts_recap,
         "les recapitulatifs du manifeste collent a son detail",
         "%d chiffre(s) annonce(s) confronte(s)" % len(annonces))

    # ── AC6.4 : la console n'enseigne plus le chiffre mort ──────────────────
    print("\n── 4. LA CONSOLE N'ENSEIGNE PLUS UN CHIFFRE MORT (AC5) ───────────")
    # ⛔ CES `open()` ETAIENT HORS GARDE : `dn_console.c` renomme ⇒
    #    FileNotFoundError, rc=1 mais ZERO ligne BILAN. Le depot a deja paye ce
    #    mode de panne (`dn4-14` : « la gate MOURAIT avant le BILAN »).
    SRC = "firmware/desknode/main/%s"
    sources = {}
    for nom in ("dn_console.c", "dn_ui.c", "dn_ui.h"):
        p = os.path.join(DESKNODE, SRC % nom)
        try:
            sources[nom] = io.open(p, encoding="utf-8", errors="replace").read()
        except OSError as e:
            sources[nom] = None
            ctrl(False, "%s est lisible" % nom, "⛔ %s" % e)

    RX340 = re.compile(RX_PLAGE % ("340", "350"))
    for nom in ("dn_console.c", "dn_ui.c"):
        if sources[nom] is None:
            continue
        n = len(RX340.findall(normalise(sources[nom])))
        ctrl(n == 0, "%s ne contient plus la coordonnee morte 340..350" % nom,
             "%d occurrence(s)" % n)

    # ⛔ AC5.2 : et on ne lui SUBSTITUE pas `337..347`.
    # 🔴 L'ANCIEN CONTROLE EXIGEAIT `printf` SUR LA MEME LIGNE — or `dn_ui.c`
    #    ne fait AUCUN `printf` (controle structurellement VIDE), un `ESP_LOGI`
    #    passait, et un `printf(` dont la chaine est sur la ligne suivante
    #    (style dominant de `dn_console.c`) aussi. `dn_ui.h` n'etait JAMAIS lu,
    #    alors qu'il porte deja `y = 337..347` en docblock.
    # ⇒ On cherche la substitution DANS UNE SORTIE (chaine litterale), quel que
    #   soit l'appel, et on admet les docblocks qui racontent la LECON.
    RX337 = re.compile(RX_PLAGE % ("337", "347"))
    for nom in ("dn_console.c", "dn_ui.c", "dn_ui.h"):
        if sources[nom] is None:
            continue
        subst = []
        for i, l in enumerate(sources[nom].split("\n"), 1):
            if not RX337.search(normalise(l)):
                continue
            # Une SORTIE = le nombre vit dans une chaine litterale "…".
            for chaine in re.findall(r'"(?:[^"\\]|\\.)*"', l):
                if RX337.search(normalise(chaine)):
                    subst.append("l.%d %s" % (i, l.strip()[:60]))
                    break
        ctrl(not subst, "%s : ⛔ 337..347 n'est SUBSTITUE dans aucune sortie" % nom,
             "%d ligne(s) : %s" % (len(subst), subst[:2]) if subst
             else "aucune substitution")

    # 🔴 AC6.4 EXIGE « il nomme `widget jauge` AUX DEUX SITES » — l'ancien
    #    controle comptait la sous-chaine SUR TOUT LE FICHIER avec un seuil >= 2.
    #    Mesure au baseline b361434 : `dn_console.c` en portait DEJA 4 (la
    #    commande `widget jauge` vit dans ce fichier) ⇒ CONTROLE VIDE : retirer
    #    les deux renvois d'AC5.1 laissait la gate VERTE.
    # ⇒ On verifie la PROXIMITE du renvoi a chaque site ou vivait le chiffre mort.
    # Un SITE = la peremption AFFIRMEE (« periment », « est perimee »),
    # ⛔ pas evoquee au conditionnel (« perimerait ») : `dn_ui.c` parle ailleurs
    # de ce QUI ARRIVERAIT si `BARRE_H` bougeait — ce n'est pas un enseignement.
    RX_SITE = re.compile(r"coordonnees?\s+tactiles?\s+publiees?")
    RX_AFFIRME = re.compile(r"perim(?:ent|ee|ees|e)\b")
    RX_COND = re.compile(r"perimerai")
    RX_JAUGE = re.compile(r"widget\s+jauge")
    for nom in ("dn_console.c", "dn_ui.c"):
        if sources[nom] is None:
            continue
        lignes = sources[nom].split("\n")
        sites = []
        for i, l in enumerate(lignes):
            if not RX_SITE.search(normalise(l)):
                continue
            # La peremption peut etre sur la ligne SUIVANTE (printf coupe).
            voisin = normalise("\n".join(lignes[max(0, i - 2):i + 3]))
            if RX_COND.search(voisin) or not RX_AFFIRME.search(voisin):
                continue
            sites.append(i)
        sans = [i + 1 for i in sites
                if not RX_JAUGE.search(normalise(
                    "\n".join(lignes[max(0, i - 14):i + 15])))]
        ctrl(len(sites) >= 2 and not sans,
             "%s : chaque site d'avertissement renvoie a `widget jauge`" % nom,
             "%d site(s), %d sans renvoi%s (2 sites attendus au minimum)"
             % (len(sites), len(sans),
                (" : l." + ", l.".join(str(x) for x in sans)) if sans else ""))

    # ── LES RENVOIS `dn_pins.h` POINTENT-ILS ENCORE LA REFUTATION ? ─────────
    # AC3.1/AC3.4 posent 5 renvois vers `dn_pins.h:165`. C'est un NUMERO DE
    # LIGNE EN DUR — le piege n°2 des Dev Notes (« re-localiser par motif, ⛔
    # jamais par numero »), et le defaut que la story constate elle-meme
    # (la recette visait `dn_pins.h:136`, la vraie adresse etait `:165`).
    # ⇒ La gate verifie que l'adresse citee PORTE ENCORE la refutation.
    pins = os.path.join(DESKNODE, SRC % "dn_pins.h")
    try:
        lp = io.open(pins, encoding="utf-8", errors="replace").read().split("\n")
    except OSError as e:
        lp = None
        ctrl(False, "dn_pins.h est lisible", "⛔ %s" % e)
    if lp is not None:
        # ⚠️ SEULS les renvois qui PROMETTENT LA REFUTATION sont controles.
        #    `dn_pins.h:31-32` (SDA/SCL) est un renvoi legitime vers autre chose.
        cites = {}
        for rel in list(fichiers_desknode(DESKNODE)):
            try:
                c = io.open(os.path.join(DESKNODE, rel),
                            encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            for i, l in enumerate(c.split("\n"), 1):
                n_l = normalise(l)
                if not re.search(r"vl6180x|vl53l0x|tof050c|refutation", n_l):
                    continue
                for m in re.finditer(r"dn_pins\.h:(\d+)", l):
                    cites.setdefault(int(m.group(1)), []).append("%s:%d" % (rel, i))
        mauvais = []
        for ln in sorted(cites):
            fenetre = normalise("\n".join(lp[max(0, ln - 4):ln + 4]))
            if "vl6180x" not in fenetre:
                mauvais.append("dn_pins.h:%d (cite par %s)"
                               % (ln, cites[ln][0][-40:]))
        ctrl(not mauvais,
             "les renvois `dn_pins.h:<ligne>` portent ENCORE la refutation",
             "%d adresse(s) : %s" % (len(cites), sorted(cites))
             if not mauvais else "⛔ PERIME(S) : %s" % " · ".join(mauvais))

    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return 1 if ko_total[0] else 0


if __name__ == "__main__":
    sys.exit(main())

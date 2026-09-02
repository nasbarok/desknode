#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
`dn5-2` — LE DEPOT TIENT LES PROMESSES QU'IL A DEJA PUBLIEES.

===============================================================================
CE QUE CET OUTIL FAIT, ET POURQUOI
===============================================================================

Le depot publie trois choses qu'il ne pouvait pas prouver :

  (a) une COUVERTURE DE LICENCES — `LICENSING.md` range chaque partie de l'arbre
      sous une licence, par DEUX listes (une table + une phrase de repli) ;
  (b) un INVENTAIRE DE DEPENDANCES — `THIRD-PARTY.md` epingle des versions que
      `firmware/desknode/main/idf_component.yml` est seul a decider ;
  (c) des PROMESSES DE PROSE — `CONTRIBUTING.md` et les autres fichiers que lit
      un inconnu affirment des capacites, citent des outils, des sections, des
      marqueurs et des COMPTES.

Aucune des trois n'etait gardee. `THIRD-PARTY.md` l'ecrivait meme lui-meme.

===============================================================================
🔴 CE QU'ELLE CONTROLE — LES DEUX SENS, TOUJOURS
===============================================================================

  (a) LICENCES, BIDIRECTIONNEL
      · tout chemin ANNONCE par l'une des deux listes EXISTE dans l'arbre ;
      · tout repertoire trace de PREMIER NIVEAU qui existe est NOMME par l'une
        des deux listes — c'est le sens qui etait ROUGE : `assets/` n'etait dans
        aucune des deux, et le silence n'est pas une couverture ;
      · le fichier de licence annonce EXISTE **et son TEXTE dit bien la licence
        annoncee** — ⛔ pas seulement « il est la ».

  (b) `idf_component.yml` ⇄ `THIRD-PARTY.md`, DANS LES DEUX SENS
      TROIS classes, ⛔ pas une, et 10 ≠ 12 N'EST PAS un defaut :
      · EPINGLE  — present des deux cotes, version EXACTE. L'operateur `==` du
        manifeste se RETIRE avant comparaison, ⛔ il ne se compare pas ;
      · ALIAS    — la cle `idf` du manifeste et la ligne `ESP-IDF` du tableau
        sont le meme composant. L'appariement se DECLARE ici (voir ALIAS) :
        un appariement litteral ROUGIRAIT SUR UN FICHIER JUSTE ;
      · TRANSITIF — *(transitive)* au tableau ⟺ ABSENT du manifeste.
        L'equivalence est FALSIFIABLE DANS LES DEUX SENS : une ligne marquee
        transitive qui APPARAITRAIT au manifeste est un mensonge (elle y est
        epinglee, donc elle n'est plus transitive), et elle rougit.

  (c) CHAQUE PROMESSE A SON ARTEFACT, OU SON ECART DECLARE AVEC PORTEUR
      · les liens sortants RESOLVENT ;
      · la section citee PAR SON TITRE existe dans le fichier cite ;
      · l'outil cite AVEC SON DRAPEAU existe **et accepte ce drapeau** — la
        gate l'INVOQUE, ⛔ elle ne lit pas son code ;
      · tout marqueur cite COMME marqueur est DEFINI dans `docs/roadmap.md` ;
      · tout COMPTE annonce sur une page ("… — six entries") EGALE le nombre
        d'entrees de cette page ;
      · la promesse d'automatisation du CLA a son ARTEFACT (un workflow, une
        version EPINGLEE, et un DOCUMENT A SIGNER qui existe reellement) ;
      · ⛔ AUCUN fichier lu ici n'AFFIRME ce que l'arbre REFUTE.

===============================================================================
⛔ CE QU'ELLE NE RECITE PAS
===============================================================================

⛔ ELLE NE CONNAIT AUCUNE LISTE DE CHEMINS « ATTENDUS ». Les repertoires sont
   DECOUVERTS par `git ls-files` a chaque tir. Une liste ecrite se perime le
   jour ou l'on ajoute un repertoire — c'est-a-dire le jour ou elle compte le
   plus. C'est la regle (1) de `tools/run_gates.sh`, appliquee ici.

⛔ ELLE NE CODE EN DUR AUCUNE CLE DE STORY dans un motif de format. Le compte
   d'entrees, les marqueurs et les porteurs sont trouves par leur FORME
   (`dnE-N`, "<nombre> entries"), ⛔ jamais par la cle de la story qui a ecrit
   la gate. Defaut paye par `dn4-16` : une gate qui codait SA PROPRE cle
   laissait passer la premiere entree de tout autre auteur.

⛔ ELLE NE POSE **AUCUN JETON D'EXEMPTION**, et c'est declare. Ces jetons n'ont
   aucun echappement : les CITER, meme dans un commentaire qui explique la
   regle, les ACCORDE. Ce depot l'a paye quatre fois. Aucun controle ci-dessous
   ne peut donc etre desarme par une ligne de commentaire.

⛔ ELLE NE CHERCHE PAS « le mot NVIDIA est absent ». Ce serait interdire d'en
   PARLER, donc interdire de le DEMENTIR — et `verif_paliers_dn441.py` a deja
   paye cette erreur exacte (sa premiere version rougissait sur le README qui
   cite la promesse POUR LA DEMOLIR). La propriete est : **toute ligne qui
   nomme NVIDIA ou NVML porte sa REFUTATION**.

===============================================================================
⛔ CE QU'ELLE NE COUVRE PAS — dit ici, ⛔ pas saute en silence
===============================================================================

⛔ **LA COLONNE « License » DE `THIRD-PARTY.md` N'EST PAS CONTROLEE.** Sa seule
   source est `managed_components/`, qui est GITIGNORE : il existe chez qui a
   lance `idf.py reconfigure`, et **il n'existe pas dans un clone**. Une gate
   qui passerait sur la machine de l'auteur et pas ailleurs est le defaut
   entier de `dn5-3`. ⇒ cette gate **NE LIT PAS `managed_components/`, meme
   s'il est la**, et elle DIT ce qu'elle n'a pas pu controler. Un vert
   silencieux sur une colonne non controlee serait le defaut, ⛔ pas la limite.
   Le controle (b) confronte donc PRESENCE et VERSION EPINGLEE — les deux cotes
   versionnes — et le controle b8 garde le FAIT qui fonde cette limite.

⛔ **ELLE NE GARDE PAS LE PERIMETRE DE `.github/`.** La frontiere « le CLA et
   lui seul » est une regle de STORY (le repertoire est partage avec la CI, qui
   appartient a `dn4-39`, et les templates d'issues, qui appartiennent a `dn8`).
   Une gate qui l'imposerait rougirait sur le travail JUSTE de ces deux
   marches. C'est verifie a la sortie de la story, ⛔ pas ici.

⛔ **ELLE NE LIT NI `mesures/` NI `hardware/`.** Ce sont des captures et des
   dossiers de mesure : y chercher des affirmations FABRIQUERAIT des faux
   rouges, puisqu'ils CITENT les sorties qu'ils enregistrent.

⛔ **UN MARQUEUR CITE SANS RENVOI A `docs/roadmap.md` N'EST PAS CONTROLE**, et
   la limite est mesuree, ⛔ pas theorique : en ecrivant cette story, une
   citation `dn7` est passee VERTE parce qu'elle ne renvoyait a rien.
   Le motif est que la page ne liste QUE le travail A VENIR — les marqueurs de
   travail PASSE (`dn1-*`..`dn4-*`, partout dans `README.md`) sont decrits la
   ou ils sont cites, et `dn5-1` n'y est deliberement pas. Exiger que TOUT
   `dnE-N` y soit ROUGIRAIT SUR DU CONTENU JUSTE. Le seul signal disponible
   est donc le renvoi lui-meme. ⇒ la convention du depot — un ecart s'ecrit
   AVEC le marqueur qui le porte, et le marqueur renvoie a la page — est ce
   qui rend le controle possible ; sans elle il ne l'est pas.

⛔ Elle ne dit rien du materiel, rien du firmware, et n'ouvre aucun port.

Sortie : `BILAN : n OK, m KO`, rc 0 si tout passe, 1 sinon.
Usage  : python3 tools/verif_licences_dn52.py [--mutant <n>] [--liste-mutants]
         `--mutant` REPLANTE UNE FAUTE en memoire et doit faire ROUGIR.
         ⛔ Aucun fichier du depot n'est modifie.

⚠️ **UN MUTANT QUI DEBRANCHE LA GARDE NE PROUVE QUE SON EXISTENCE.** Les
   mutants d'ici replantent la faute reelle — un chemin qui disparait de
   `LICENSING.md`, une version qui diverge, une ligne transitive qui remonte au
   manifeste, un compte qui se desaccorde, un porteur mis a `TBD`, une
   affirmation NVIDIA sans sa refutation — et la gate doit la VOIR.
"""

import argparse
import os
import re
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

F_LICENSING = os.path.join(RACINE, "LICENSING.md")
F_THIRDPARTY = os.path.join(RACINE, "THIRD-PARTY.md")
F_MANIFESTE = os.path.join(RACINE, "firmware", "desknode", "main",
                           "idf_component.yml")
F_ROADMAP = os.path.join(RACINE, "docs", "roadmap.md")
F_AGENT = os.path.join(RACINE, "agent", "dn_agent.py")
F_GITIGNORE = os.path.join(RACINE, ".gitignore")

# ── L'ALIAS SE DECLARE, ⛔ IL NE SE DEVINE PAS ──────────────────────────────
# Le manifeste ESP-IDF nomme sa propre version `idf` ; `THIRD-PARTY.md` ecrit
# `ESP-IDF`, qui est le nom que lit un humain. Les deux designent LE MEME
# composant. Un appariement litteral rougirait sur un fichier JUSTE.
ALIAS = {"idf": "ESP-IDF"}

# ── LE TEXTE QUI PROUVE QU'UN FICHIER DE LICENCE EST BIEN CELUI ANNONCE ─────
# ⛔ Ce n'est pas « le fichier existe » : un `agent/LICENSE` qui contiendrait la
#    GPL passerait ce test-la et mentirait quand meme.
SIGNATURE_LICENCE = {
    "GPL-3.0-or-later": ("GNU GENERAL PUBLIC LICENSE", "Version 3"),
    "MIT": ("MIT License",),
    "CC-BY-SA-4.0": ("Attribution-ShareAlike 4.0 International",),
}

# ── LA REFUTATION, EN DEUX LANGUES ─────────────────────────────────────────
# Une ligne qui nomme NVIDIA/NVML doit porter l'un de ces marqueurs. ⛔ La liste
# reste COURTE a dessein : chaque entree de plus est une porte de sortie de
# plus, et une porte de sortie trop large rendrait le controle vert sur du faux.
REFUTATIONS = (
    "not implemented", "NON IMPLÉMENT", "NON IMPLEMENT",
    "no NVML", "aucun NVML", "INAPPLICABLE", "inapplicable",
    "refutes", "refute", "réfute", "ne le promet pas", "c'est faux",
    "is not a dependency", "n'est même pas installé",
)

# ── UN PORTEUR QUI N'EN EST PAS UN ─────────────────────────────────────────
# ⚠️ Le vide LITTERAL n'est pas le seul cas : un porteur `TBD` passe vert quand
#    le controle ne teste que le vide. Defaut mesure dans ce depot.
PORTEURS_CREUX = ("tbd", "todo", "to be defined", "à définir", "a definir",
                  "???", "xxx", "n/a", "na", "-", "—", "")

NOMBRES = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20,
}

OK = [0]
KO = [0]
_MUTANT = None

MUTANTS = {}                      # ⛔ AU NIVEAU MODULE — sinon `--liste-mutants`
MUTANTS[1] = ("retire `docs/` de la TABLE de LICENSING.md "
              "(un repertoire trace cesse d'etre couvert)")
MUTANTS[2] = ("annonce dans LICENSING.md un chemin `plans/` "
              "QUI N'EXISTE PAS dans l'arbre")
MUTANTS[3] = ("fait annoncer MIT au chemin `docs/` "
              "alors que docs/LICENSE porte la CC-BY-SA")
MUTANTS[4] = ("fait pointer `agent/` vers un fichier de licence ABSENT")
MUTANTS[5] = ("fait diverger la version de `lvgl/lvgl` "
              "entre le manifeste et THIRD-PARTY.md")
MUTANTS[6] = ("marque *(transitive)* une ligne qui EST epinglee au manifeste "
              "(le mensonge dans l'autre sens)")
MUTANTS[7] = ("retire du tableau une ligne PRESENTE au manifeste")
MUTANTS[8] = ("sort `managed_components/` du .gitignore "
              "(le FAIT qui fonde la limite declaree tombe)")
MUTANTS[9] = ("casse un lien sortant de CONTRIBUTING.md")
MUTANTS[10] = ("cite une section de README.md par un titre INEXISTANT")
MUTANTS[11] = ("cite l'outil du depot avec un drapeau QU'IL N'ACCEPTE PAS")
MUTANTS[12] = ("cite un marqueur `dn9-9` absent de docs/roadmap.md")
MUTANTS[13] = ("desaccorde le COMPTE annonce d'entrees de la page d'ecart")
MUTANTS[14] = ("met le porteur de l'ecart CLA a `TBD` "
               "(⛔ pas au vide : le vide seul ne prouve rien)")
MUTANTS[15] = ("efface le document a signer que le workflow CLA fait signer")
MUTANTS[16] = ("fait flotter la version de l'action CLA (`@main`)")
MUTANTS[17] = ("remet une affirmation NVIDIA SANS sa refutation dans "
               "un fichier racine")
MUTANTS[18] = ("laisse THIRD-PARTY.md ecrire que RIEN ne le garde "
               "alors que cette gate le garde")
# ── AJOUTES APRES LA 1re CAMPAGNE, QUI A MESURE 13 CONTROLES GARDES PAR RIEN
MUTANTS[19] = ("rend la TABLE de LICENSING.md ILLISIBLE "
               "(toutes ses lignes, ⛔ pas la premiere)")
MUTANTS[20] = ("efface la phrase de REPLI de LICENSING.md "
               "(la 2e liste ne se devine pas)")
MUTANTS[21] = ("annonce une licence dont aucune signature n'est connue")
MUTANTS[22] = ("rend le manifeste `idf_component.yml` ILLISIBLE")
MUTANTS[23] = ("rend la table § Firmware de THIRD-PARTY.md ILLISIBLE")
MUTANTS[24] = ("ajoute au tableau une ligne qui n'est NI epinglee, "
               "NI alias, NI transitive")
MUTANTS[25] = ("fait diverger la version de l'ALIAS `idf` ⇄ `ESP-IDF`")
MUTANTS[26] = ("rend la table de docs/roadmap.md ILLISIBLE "
               "(plus aucun marqueur defini)")
MUTANTS[27] = ("retire la promesse de bot de CONTRIBUTING.md "
               "alors que le workflow, lui, est bien la")
MUTANTS[28] = ("fait CHECKOUTER le code de la PR par le workflow "
               "`pull_request_target`")


def dire(ok, libelle, detail=""):
    (OK if ok else KO)[0] += 1
    print("  [%s] %-58s %s" % ("OK " if ok else "KO ", libelle, detail))


def note(texte):
    """Une LIMITE declaree. ⛔ Ce n'est pas un controle : elle ne compte pas au
    bilan. Elle est imprimee pour qu'un lecteur voie ce qui N'EST PAS garde."""
    print("  [⚠️ ] %s" % texte)


def M(n, src, avant, apres, tous=False):
    """Mutation ciblee, EN MEMOIRE. ⛔ Aucun fichier n'est modifie.

    `tous=True` remplace TOUTES les occurrences : replanter « le fichier est
    devenu illisible » exige de casser toutes ses lignes, ⛔ pas la premiere —
    en casser une seule laisserait la structure lisible et le mutant serait
    MUET, ce qui ne prouverait rien."""
    if _MUTANT != n:
        return src
    if avant not in src:
        sys.exit("MUTANT %d INAPPLICABLE : le motif est introuvable. ⛔ Un "
                 "mutant qui ne s'applique pas ne prouve RIEN — il faut le "
                 "reparer, ⛔ pas conclure que le controle est vert." % n)
    return src.replace(avant, apres) if tous else src.replace(avant, apres, 1)


def lire(chemin):
    with open(chemin, encoding="utf-8", errors="replace") as f:
        return f.read()


def suivis():
    """Les fichiers TRACES, par `git ls-files`. ⛔ Pas un parcours du disque :
    un repertoire ignore (build/, managed_components/) n'est pas du depot."""
    r = subprocess.run(["git", "ls-files"], cwd=RACINE,
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return [x for x in r.stdout.splitlines() if x.strip()]


def prose_du_depot(fichiers):
    """Les fichiers de PROSE que lit un inconnu : la racine et `docs/`.
    ⛔ `mesures/` et `hardware/` sont exclus — ce sont des captures et des
    dossiers de mesure, ils CITENT les sorties qu'ils enregistrent."""
    return [f for f in fichiers
            if f.endswith(".md") and ("/" not in f or f.startswith("docs/"))]


# ═══════════════════════════════════════════════════════════════════════════
# (a) LES LICENCES — BIDIRECTIONNEL
# ═══════════════════════════════════════════════════════════════════════════

def lire_les_deux_listes(lic):
    """La TABLE et la phrase de REPLI. Les deux, ⛔ pas seulement la table."""
    table = []
    for m in re.finditer(
            r"^\|\s*`([^`]+)`[^|]*\|\s*\*\*([^*]+)\*\*\s*\|\s*(.*?)\s*\|\s*$",
            lic, re.M):
        chemin, licence, cellule = m.group(1), m.group(2).strip(), m.group(3)
        mf = re.search(r"\[`([^`]+)`\]", cellule)
        table.append((chemin, licence, mf.group(1) if mf else None))
    mr = re.search(r"Anything not covered above\s*\((.*?)\)\s*\n?\s*follows",
                   lic, re.S)
    repli = re.findall(r"`([^`]+)`", mr.group(1)) if mr else None
    return table, repli


def section_licences(lic, traces):
    print("\n── (a) LES LICENCES, DANS LES DEUX SENS ──────────────────────────")

    lic = M(1, lic,
            "| `docs/` — documentation, wiring photos, schematics, "
            "enclosure plans | **CC-BY-SA-4.0** | [`docs/LICENSE`]"
            "(docs/LICENSE) |\n", "")
    lic = M(2, lic, "| `assets/` — mockups and other visuals |",
            "| `plans/` — mockups and other visuals |")
    lic = M(3, lic,
            "| `docs/` — documentation, wiring photos, schematics, "
            "enclosure plans | **CC-BY-SA-4.0** |",
            "| `docs/` — documentation, wiring photos, schematics, "
            "enclosure plans | **MIT** |")
    lic = M(4, lic, "[`agent/LICENSE`](agent/LICENSE)",
            "[`agent/LICENCE`](agent/LICENCE)")
    lic = M(19, lic, "** | [`", "* | [`", tous=True)
    lic = M(20, lic, "Anything not covered above", "Everything else")
    lic = M(21, lic, "| **MIT** | [`agent/LICENSE`]",
            "| **BSD-2-Clause** | [`agent/LICENSE`]")

    table, repli = lire_les_deux_listes(lic)

    # ⛔ UN CONTROLE QUI NE PEUT PAS LIRE NE DIT PAS « rien a signaler ».
    dire(bool(table), "la TABLE de LICENSING.md se lit",
         "%d ligne(s)" % len(table) if table else "⛔ ILLISIBLE")
    dire(repli is not None, "la phrase de REPLI de LICENSING.md se lit",
         "%d chemin(s) + la racine" % len(repli) if repli is not None
         else "⛔ INTROUVABLE — la 2e liste ne se devine pas")
    if not table or repli is None:
        return
    if traces is None:
        dire(False, "l'arbre trace se lit (`git ls-files`)", "⛔ ECHEC de git")
        return

    dirs = sorted({f.split("/")[0] for f in traces if "/" in f})
    annonces = {p.rstrip("/") for p, _, _ in table} | \
               {p.rstrip("/") for p in repli}

    # ── SENS 1 : un chemin ANNONCE mais ABSENT fait rougir ────────────────
    fantomes = sorted(p for p in annonces if p and p not in dirs)
    dire(not fantomes, "tout chemin ANNONCE existe dans l'arbre",
         "%d repertoire(s) annonce(s)" % len(annonces) if not fantomes
         else "⛔ annonce(s) sans arbre : " + " ".join(fantomes))

    # ── SENS 2 : un repertoire QUI EXISTE sans etre nomme fait rougir ─────
    # 🔴 C'EST LE SENS QUI ETAIT ROUGE. `assets/` n'etait dans aucune des deux
    #    listes, et personne ne l'avait vu : le silence n'est pas une couverture.
    orphelins = [d for d in dirs if d not in annonces]
    dire(not orphelins,
         "tout repertoire TRACE est nomme par l'une des 2 listes",
         "%d repertoire(s) de 1er niveau" % len(dirs) if not orphelins
         else "⛔ couvert par RIEN : " + " ".join(orphelins))

    # ── LE FICHIER DE LICENCE EXISTE, ET IL DIT BIEN CETTE LICENCE ────────
    manquants, menteurs, inconnues = [], [], []
    for chemin, licence, fichier in table:
        if licence not in SIGNATURE_LICENCE:
            inconnues.append("%s=%s" % (chemin, licence))
            continue
        if not fichier:
            manquants.append("%s (aucun fichier cite)" % chemin)
            continue
        plein = os.path.join(RACINE, fichier)
        if not os.path.exists(plein):
            manquants.append("%s -> %s" % (chemin, fichier))
            continue
        texte = lire(plein)
        if not all(s in texte for s in SIGNATURE_LICENCE[licence]):
            menteurs.append("%s -> %s ne dit pas %s" % (chemin, fichier,
                                                        licence))
    dire(not manquants, "le fichier de licence annonce EXISTE",
         "%d ligne(s) de table" % len(table) if not manquants
         else "⛔ " + " · ".join(manquants))
    dire(not menteurs, "le fichier de licence DIT BIEN la licence annoncee",
         "⛔ pas seulement « il est la »" if not menteurs
         else "⛔ " + " · ".join(menteurs))
    dire(not inconnues, "chaque licence annoncee a une signature connue",
         "%d licence(s) distinctes" % len({l for _, l, _ in table})
         if not inconnues
         else "⛔ signature inconnue : " + " · ".join(inconnues))


# ═══════════════════════════════════════════════════════════════════════════
# (b) `idf_component.yml` ⇄ `THIRD-PARTY.md`
# ═══════════════════════════════════════════════════════════════════════════

def lire_manifeste(src):
    """Les dependances du manifeste. ⛔ Pas un parseur YAML : le commentaire
    est retire, et seules les deux formes reellement utilisees sont lues."""
    deps, dans, courant = {}, False, None
    for ligne in src.splitlines():
        if re.match(r"^dependencies:\s*$", ligne):
            dans = True
            continue
        if not dans:
            continue
        s = ligne.split("#")[0].rstrip()
        if not s.strip():
            continue
        m = re.match(r'^  ([A-Za-z0-9_./-]+):\s*"([^"]+)"\s*$', s)
        if m:
            deps[m.group(1)] = m.group(2)
            courant = None
            continue
        m = re.match(r"^  ([A-Za-z0-9_./-]+):\s*$", s)
        if m:
            courant = m.group(1)
            deps.setdefault(courant, None)
            continue
        m = re.match(r'^    version:\s*"([^"]+)"\s*$', s)
        if m and courant:
            deps[courant] = m.group(1)
            courant = None
    return deps


def lire_tableau_tiers(src):
    """Les lignes de la table § Firmware de THIRD-PARTY.md."""
    if "## Firmware" not in src:
        return None
    bloc = src.split("## Firmware", 1)[1].split("\n## ", 1)[0]
    lignes = []
    for ligne in bloc.splitlines():
        if not ligne.startswith("|"):
            continue
        cellules = [c.strip() for c in ligne.strip("|").split("|")]
        if len(cellules) < 3:
            continue
        if cellules[0] == "Component" or set(cellules[0]) <= set("-: "):
            continue
        lignes.append(cellules)
    return lignes


def _nu(s):
    return s.strip().strip("`*").strip()


def section_tiers(manifeste, tiers, gitignore, traces):
    print("\n── (b) LE MANIFESTE ⇄ L'INVENTAIRE, DANS LES DEUX SENS ───────────")

    manifeste = M(5, manifeste, 'lvgl/lvgl: "==9.5.0"', 'lvgl/lvgl: "==9.6.0"')
    tiers = M(6, tiers, "| `lvgl/lvgl` | `9.5.0` |",
              "| `lvgl/lvgl` | *(transitive)* |")
    tiers = M(7, tiers,
              "| `espressif/esp_lcd_touch` | `1.2.1` | Apache-2.0 |\n", "")
    gitignore = M(8, gitignore, "managed_components/\n", "")
    manifeste = M(22, manifeste, "dependencies:\n", "deps:\n")
    tiers = M(23, tiers, "## Firmware\n", "## Fw\n")
    tiers = M(24, tiers, "| `lvgl/lvgl` | `9.5.0` | MIT |\n",
              "| `lvgl/lvgl` | `9.5.0` | MIT |\n"
              "| `acme/widget` | `1.0.0` | MIT |\n")
    tiers = M(25, tiers, "| ESP-IDF | `~5.5.0` |", "| ESP-IDF | `~5.4.0` |")

    deps = lire_manifeste(manifeste)
    lignes = lire_tableau_tiers(tiers)

    dire(bool(deps), "le manifeste `idf_component.yml` se lit",
         "%d entree(s)" % len(deps) if deps else "⛔ ILLISIBLE")
    dire(bool(lignes), "la table § Firmware de THIRD-PARTY.md se lit",
         "%d ligne(s)" % len(lignes) if lignes else "⛔ ILLISIBLE")
    if not deps or not lignes:
        return

    inv_alias = {v: k for k, v in ALIAS.items()}
    table = {_nu(c[0]): _nu(c[1]) for c in lignes}

    # ── CHAQUE LIGNE TOMBE DANS **UNE SEULE** CLASSE ─────────────────────
    # ⚠️ Un composant ALIAS est aussi « present au manifeste » : le compter
    #    dans les deux classes ferait annoncer 13 la ou le tableau en porte 12.
    #    Un instrument qui ment sur sa propre couverture est ce que `dn4-42` a
    #    paye — les classes sont donc EXCLUSIVES, et leur somme est verifiee.
    epingles, alias_vus, transitifs = [], [], []
    menteurs_trans, divergences, sans_classe = [], [], []
    for nom, version in table.items():
        cle = inv_alias.get(nom, nom)
        au_manifeste = cle in deps
        est_transitif = version.replace("(", "").replace(")", "") == "transitive"
        if nom in inv_alias:
            alias_vus.append(nom)
        elif est_transitif:
            transitifs.append(nom)
            # 🎯 FALSIFIABLE DANS LES DEUX SENS : une ligne marquee transitive
            #    qui EST au manifeste y est EPINGLEE — donc elle ment.
            if au_manifeste:
                menteurs_trans.append("%s (epingle a %s)" % (nom, deps[cle]))
        elif au_manifeste:
            epingles.append(nom)
        else:
            sans_classe.append(nom)
        if au_manifeste and not est_transitif:
            attendue = (deps[cle] or "").replace("==", "").strip()
            if attendue != version:
                divergences.append("%s : table=%s manifeste=%s"
                                   % (nom, version, deps[cle]))

    # ── SENS 1 : tout ce qui est au MANIFESTE est au TABLEAU ──────────────
    absents_du_tableau = sorted(k for k in deps
                                if k not in table and ALIAS.get(k) not in table)
    dire(not absents_du_tableau,
         "toute entree du manifeste figure au tableau",
         "%d entree(s) confrontee(s)" % len(deps) if not absents_du_tableau
         else "⛔ absente(s) du tableau : " + " ".join(absents_du_tableau))

    # ── SENS 2 : toute ligne du TABLEAU est justifiee ─────────────────────
    somme = len(epingles) + len(alias_vus) + len(transitifs)
    dire(not sans_classe and somme == len(table),
         "toute ligne du tableau est EPINGLEE, ALIAS ou TRANSITIVE",
         "%d epinglee(s) + %d alias + %d transitive(s) = %d ligne(s)"
         % (len(epingles), len(alias_vus), len(transitifs), len(table))
         if not sans_classe and somme == len(table)
         else "⛔ sans classe : %s (somme %d ≠ %d)"
              % (" ".join(sans_classe) or "(aucune)", somme, len(table)))

    # ── LES VERSIONS, `==` RETIRE AVANT COMPARAISON ───────────────────────
    dire(not divergences, "les versions EPINGLEES concordent (`==` retire)",
         "%d comparaison(s), alias compris" % (len(epingles) + len(alias_vus))
         if not divergences else "⛔ " + " · ".join(divergences))

    # ── L'ALIAS EST DECLARE, ET IL DOIT ETRE VRAI DES DEUX COTES ──────────
    alias_ok = []
    for cle, nom in ALIAS.items():
        if cle in deps and nom in table:
            a = (deps[cle] or "").replace("==", "").strip()
            alias_ok.append(a == table[nom])
        else:
            alias_ok.append(False)
    dire(all(alias_ok) and bool(alias_ok),
         "l'ALIAS declare apparie les deux cotes",
         " · ".join("%s⇄%s" % (k, v) for k, v in ALIAS.items()))

    # ── TRANSITIF ⟺ ABSENT DU MANIFESTE, DANS LES DEUX SENS ───────────────
    dire(not menteurs_trans,
         "*(transitive)* ⟺ ABSENT du manifeste (les 2 sens)",
         "%d ligne(s) transitive(s)" % len(transitifs) if not menteurs_trans
         else "⛔ marquee transitive ET epinglee : " + " · ".join(menteurs_trans))

    # ── b8 — LE FAIT QUI FONDE LA LIMITE DECLAREE ─────────────────────────
    # ⛔ La colonne « License » n'est pas controlable DEPUIS UN CLONE parce que
    #    `managed_components/` est gitignore. Si ce fait cessait d'etre vrai,
    #    la limite ci-dessous devrait etre rouverte — donc il se GARDE.
    ignore = ("managed_components/" in gitignore
              and "dependencies.lock" in gitignore)
    trace = traces is not None and any(
        f.startswith("managed_components/") or f == "dependencies.lock"
        for f in traces)
    dire(ignore and not trace,
         "`managed_components/` hors du clone (fonde la limite)",
         "gitignore=%s · trace=%s" % ("oui" if ignore else "⛔ NON",
                                      "⛔ OUI" if trace else "non"))
    note("⛔ NON CONTROLE — la colonne « License » du tableau : sa seule source "
         "est\n       `managed_components/`, absent d'un clone. Cette gate NE "
         "LE LIT PAS, meme\n       s'il est la : une gate qui passe chez "
         "l'auteur et pas ailleurs est le\n       defaut entier de `dn5-3`. "
         "La verifier est une MESURE, ⛔ pas un controle.")


# ═══════════════════════════════════════════════════════════════════════════
# (c) CHAQUE PROMESSE A SON ARTEFACT
# ═══════════════════════════════════════════════════════════════════════════

def section_liens(textes):
    print("\n── (c1) LES LIENS SORTANTS RESOLVENT ─────────────────────────────")
    casses, total = [], 0
    for nom, src in textes.items():
        for m in re.finditer(r"\[([^\]]*)\]\(([^)]+)\)", src):
            cible = m.group(2).strip()
            if cible.startswith(("http", "#", "mailto")):
                continue
            total += 1
            chemin = cible.split("#")[0]
            plein = os.path.normpath(
                os.path.join(RACINE, os.path.dirname(nom), chemin))
            if not os.path.exists(plein):
                casses.append("%s:%d -> %s"
                              % (nom, src[:m.start()].count("\n") + 1, cible))
    dire(not casses, "tout lien local des fichiers de prose resout",
         "%d lien(s) local(aux), %d fichier(s)" % (total, len(textes))
         if not casses else "⛔ " + " · ".join(casses[:3]))


def section_citations(textes):
    print("\n── (c2/c3) LES SECTIONS ET LES OUTILS CITES EXISTENT ─────────────")

    # ── UNE SECTION CITEE PAR SON TITRE ───────────────────────────────────
    absentes, vues = [], 0
    for nom, src in textes.items():
        plat = re.sub(r"\s+", " ", src)
        for m in re.finditer(
                r"\[`([^`]+\.md)`\]\([^)]+\),?\s*section\s*\*«\s*(.+?)\s*»\*",
                plat):
            vues += 1
            cible = os.path.normpath(
                os.path.join(RACINE, os.path.dirname(nom), m.group(1)))
            titre = m.group(2)
            if not os.path.exists(cible) or titre not in lire(cible):
                absentes.append("%s : « %s » dans %s"
                                % (nom, titre, m.group(1)))
    dire(not absentes, "la section citee PAR SON TITRE existe",
         "%d citation(s)" % vues if not absentes
         else "⛔ " + " · ".join(absentes))

    # ── UN OUTIL CITE AVEC SON DRAPEAU : LA GATE L'INVOQUE ────────────────
    # ⛔ Elle ne lit PAS le code de l'outil : un `--reset` present dans une
    #    chaine ne prouve pas qu'argparse l'accepte.
    refuses, essayes = [], set()
    for nom, src in textes.items():
        for m in re.finditer(r"python3\s+(tools/[\w./-]+\.py)\s+(--[\w-]+)",
                             src):
            outil, drapeau = m.group(1), m.group(2)
            if (outil, drapeau) in essayes:
                continue
            essayes.add((outil, drapeau))
            plein = os.path.join(RACINE, outil)
            if not os.path.exists(plein):
                refuses.append("%s ABSENT" % outil)
                continue
            r = subprocess.run([sys.executable, plein, "--help"], cwd=RACINE,
                               capture_output=True, text=True)
            if r.returncode != 0 or drapeau not in (r.stdout + r.stderr):
                refuses.append("%s n'accepte pas %s (rc=%d)"
                               % (outil, drapeau, r.returncode))
    dire(not refuses and bool(essayes),
         "l'outil cite AVEC SON DRAPEAU l'accepte (invoque)",
         "%d couple(s) outil/drapeau" % len(essayes) if not refuses
         else "⛔ " + " · ".join(refuses))


def section_marqueurs(textes, roadmap):
    print("\n── (c4) LES MARQUEURS CITES SONT DEFINIS ─────────────────────────")
    definis = set(re.findall(r"^\|\s*`(dn\d+(?:-\d+)?)`\s*\|", roadmap, re.M))
    dire(bool(definis), "docs/roadmap.md definit des marqueurs",
         "%d marqueur(s)" % len(definis) if definis else "⛔ table ILLISIBLE")

    # 🔴 PIEGE MESURE — ⛔ NE PAS ANCRER SUR TOUTE SOUS-CHAINE `dnE-N`.
    #    `dn5-1` n'apparait que dans un NOM DE FICHIER, et `docs/roadmap.md` ne
    #    le liste pas — DELIBEREMENT : cette page ne liste que le travail A
    #    VENIR. Un controle naif ROUGIRAIT SUR DU CONTENU JUSTE. L'ancrage est
    #    donc : marqueur cite COMME marqueur, c'est-a-dire renvoye a la page.
    inconnus, cites = [], 0
    for nom, src in textes.items():
        plat = re.sub(r"\s+", " ", src)
        for m in re.finditer(r"`(dn\d+(?:-\d+)?)`", plat):
            fenetre = plat[m.end():m.end() + 140]
            avant = plat[max(0, m.start() - 60):m.start()]
            if "roadmap.md" not in fenetre and "tracked as" not in avant:
                continue
            cites += 1
            if m.group(1) not in definis:
                inconnus.append("%s cite `%s`" % (nom, m.group(1)))
    dire(not inconnus, "tout marqueur cite COMME marqueur est defini",
         "%d citation(s) ancree(s) sur la page" % cites if not inconnus
         else "⛔ " + " · ".join(sorted(set(inconnus))))


def section_comptes(textes):
    print("\n── (c5) LES COMPTES ANNONCES EGALENT CE QU'ILS COMPTENT ──────────")
    # 🎯 CE CONTROLE NE CODE EN DUR AUCUNE CLE DE STORY : il trouve un LIEN vers
    #    une page, puis un NOMBRE suivi de « entries » dans ce qui suit. Il
    #    attrapera l'ecriture d'un auteur futur exactement comme celle d'ici.
    faux, vus = [], 0
    for nom, src in textes.items():
        plat = re.sub(r"\s+", " ", src).replace("*", "")
        for m in re.finditer(r"\[`?([^\]`]+\.md)`?\]\(([^)]+)\)", plat):
            fenetre = plat[m.end():m.end() + 120]
            mn = re.search(r"\b([A-Za-z]+|\d+)\s+entr(?:ies|y)\b", fenetre)
            if not mn:
                continue
            mot = mn.group(1).lower()
            annonce = NOMBRES.get(mot, int(mot) if mot.isdigit() else None)
            if annonce is None:
                continue
            vus += 1
            cible = os.path.normpath(os.path.join(
                RACINE, os.path.dirname(nom), m.group(2).split("#")[0]))
            if not os.path.exists(cible):
                faux.append("%s : cible %s absente" % (nom, m.group(2)))
                continue
            reel = len(re.findall(r"^\|\s*\*\*(\d+)\*\*\s*\|", lire(cible),
                                  re.M))
            if reel != annonce:
                faux.append("%s annonce %d, %s en porte %d"
                            % (nom, annonce, m.group(1), reel))
    dire(not faux and vus > 0, "le COMPTE annonce egale le nombre d'entrees",
         "%d compte(s) confronte(s)" % vus if not faux and vus
         else ("⛔ " + " · ".join(faux) if faux
               else "⛔ AUCUN compte trouve — le controle ne peut pas etre vert "
                    "sur du vide"))


def section_cla(contrib, roadmap):
    print("\n── (c6) LA PROMESSE D'AUTOMATISATION DU CLA A SON ARTEFACT ───────")

    # ⚠️ CE CONTROLE N'EST PAS UN COMPTAGE DE MOTS. Traquer « bot » ou « CLA »
    #    ferait rougir la gate sur la prose qui EXPLIQUE la regle — et le depot
    #    a deja paye « citer le jeton l'accorde ». Il apparie une PROMESSE (une
    #    phrase qui affirme qu'un mecanisme automatique existe) a son ARTEFACT.
    plat = re.sub(r"\s+", " ", contrib)
    promet = re.search(r"[Aa] bot (handles|signs|checks)", plat) is not None

    wf_dir = os.path.join(RACINE, ".github", "workflows")
    workflows = []
    if os.path.isdir(wf_dir):
        for f in sorted(os.listdir(wf_dir)):
            if f.endswith((".yml", ".yaml")):
                workflows.append((f, lire(os.path.join(wf_dir, f))))
    cla_wf = [(f, s) for f, s in workflows if re.search(r"cla", s, re.I)]

    dire(promet == bool(cla_wf),
         "la promesse de bot et son workflow disent la meme chose",
         "promesse=%s · workflow(s) CLA=%d"
         % ("oui" if promet else "non", len(cla_wf)))

    if cla_wf:
        _, wf = cla_wf[0]
        wf = M(15, wf, "path-to-document:", "path-to-document-absent:")
        wf = M(16, wf, "github-action@v2.6.1", "github-action@main")
        wf = M(28, wf, '      - name: "Signature du CLA"',
               "      - uses: actions/checkout@v4\n"
               "        with:\n"
               "          ref: ${{ github.event.pull_request.head.sha }}\n"
               '      - name: "Signature du CLA"')

        # ── LA VERSION EST EPINGLEE, ⛔ JAMAIS UN TAG FLOTTANT ─────────────
        actions = re.findall(r"uses:\s*([\w.-]+/[\w.-]+)@([\w.-]+)", wf)
        FLOTTANTS = ("main", "master", "latest", "HEAD")
        flottantes = ["%s@%s" % (a, v) for a, v in actions if v in FLOTTANTS]
        dire(bool(actions) and not flottantes,
             "chaque action du workflow CLA est EPINGLEE",
             " · ".join("%s@%s" % a for a in actions) if not flottantes
             else "⛔ version FLOTTANTE : " + " ".join(flottantes))

        # ── LE DOCUMENT A SIGNER EXISTE VRAIMENT ──────────────────────────
        # 🔴 Un bot qui fait signer un document ABSENT est exactement la
        #    promesse creuse que cette story solde.
        md = re.search(r"path-to-document:\s*['\"]?([^'\"\s]+)", wf)
        chemin = None
        if md:
            brut = md.group(1)
            mb = re.search(r"blob/[^/]+/(.+)$", brut)
            chemin = mb.group(1) if mb else brut.lstrip("./")
        dire(chemin is not None and os.path.exists(
                 os.path.join(RACINE, chemin)),
             "le document que le bot fait signer EXISTE",
             chemin or "⛔ `path-to-document` absent du workflow")

        # ── ⛔ LE CODE DE LA PR N'EST JAMAIS CHECKOUTE ─────────────────────
        # `pull_request_target` s'execute avec le jeton du depot de BASE.
        danger = re.search(r"uses:\s*actions/checkout@[^\n]*\n(?:[^\n]*\n)"
                           r"{0,6}?[^\n]*ref:\s*\$\{\{\s*github\.event\."
                           r"pull_request\.head", wf)
        dire(danger is None,
             "⛔ le workflow ne checkoute JAMAIS le code de la PR",
             "`pull_request_target` tourne avec le jeton du depot de BASE")

    # ── L'ECART RESIDUEL EST DECLARE AVEC UN PORTEUR, ET IL EST VRAI ──────
    # ⚠️ Un porteur `TBD` doit ROUGIR — ⛔ pas seulement le vide LITTERAL.
    definis = set(re.findall(r"^\|\s*`(dn\d+(?:-\d+)?)`\s*\|", roadmap, re.M))
    mp = re.search(r"external contributor[^.]*?carried by\s*`([^`]*)`", plat)
    porteur = mp.group(1).strip() if mp else ""
    valide = (porteur.lower() not in PORTEURS_CREUX) and (porteur in definis)
    dire(valide, "l'ecart residuel du CLA a un PORTEUR reel",
         "porteur = `%s`" % porteur if valide
         else "⛔ porteur creux ou inconnu : « %s »" % porteur)


def section_refutations(textes, agent):
    print("\n── (c7) ⛔ AUCUN FICHIER N'AFFIRME CE QUE L'ARBRE REFUTE ─────────")

    # L'arbre dit ce que l'agent SAIT faire. Si NVML entrait un jour dans
    # l'agent, l'affirmation deviendrait VRAIE et ce controle changerait de
    # sens — donc il LIT l'agent, ⛔ il ne suppose pas.
    a_nvml = re.search(r"^\s*import\s+pynvml", agent, re.M) is not None
    # ⛔ CE N'EST PAS UN CONTROLE, DONC CE N'EST PAS UN `dire()`. Un `dire(True,
    #    ...)` inconditionnel ne peut PAS rougir : il gonfle le bilan sans rien
    #    garder. La campagne de mutants l'a epingle — c'est elle qui l'a vu.
    note("l'arbre est LU, ⛔ pas suppose — `import pynvml` dans l'agent : %s"
         % ("OUI ⇒ l'affirmation serait VRAIE" if a_nvml
            else "NON ⇒ toute affirmation de couverture est FAUSSE"))
    if a_nvml:
        note("l'agent importe NVML : le controle ci-dessous est SANS OBJET.")
        return

    nues = []
    for nom, src in textes.items():
        for i, ligne in enumerate(src.splitlines(), 1):
            if "NVIDIA" not in ligne and "NVML" not in ligne:
                continue
            if any(r in ligne for r in REFUTATIONS):
                continue
            nues.append("%s:%d %s" % (nom, i, ligne.strip()[:60]))
    dire(not nues,
         "toute ligne qui nomme NVIDIA/NVML porte sa REFUTATION",
         "⛔ la propriete n'est PAS « le mot est absent »" if not nues
         else "⛔ ligne SANS refutation : " + " · ".join(nues[:3]))


def section_auto_coherence(tiers):
    print("\n── (c8) LE DEPOT NE SE CONTREDIT PAS SUR SES PROPRES GARDES ──────")
    # 🔴 POSER CETTE GATE REND FAUSSE UNE PHRASE PUBLIEE. `THIRD-PARTY.md`
    #    ecrivait « nothing enforces this table automatically ». Des que le
    #    controle (b) existe, c'est FAUX — et la laisser fabriquerait une
    #    instance NEUVE du defaut que la story solde.
    tiers = M(18, tiers,
              "This table is checked by",
              "Nothing enforces this table automatically, so")
    plat = re.sub(r"\s+", " ", tiers)
    nie = re.search(r"nothing enforces this table automatically", plat, re.I)
    moi = os.path.relpath(os.path.abspath(__file__), RACINE).replace(os.sep, "/")
    cite = moi in plat
    dire(nie is None and cite,
         "THIRD-PARTY.md dit que cette gate le garde",
         "il cite %s" % moi if nie is None and cite
         else "⛔ il ecrit encore que RIEN ne le garde"
              if nie else "⛔ il ne cite pas la gate qui le garde")


def main():
    global _MUTANT
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--mutant", type=int, default=None,
                    help="REPLANTE une faute EN MEMOIRE pour prouver que le "
                         "controle correspondant sait ROUGIR")
    ap.add_argument("--liste-mutants", action="store_true",
                    help="dit ce que chaque mutant replante, et sort")
    args = ap.parse_args()
    _MUTANT = args.mutant

    if args.liste_mutants:
        for n in sorted(MUTANTS):
            print("  %2d  %s" % (n, MUTANTS[n]))
        return 0

    print("=" * 78)
    print("dn5-2 — LE DEPOT TIENT LES PROMESSES QU'IL A DEJA PUBLIEES"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)

    traces = suivis()
    lic = lire(F_LICENSING)
    tiers = lire(F_THIRDPARTY)
    manifeste = lire(F_MANIFESTE)
    roadmap = lire(F_ROADMAP)
    agent = lire(F_AGENT)
    gitignore = lire(F_GITIGNORE)

    section_licences(lic, traces)
    section_tiers(manifeste, tiers, gitignore, traces)

    prose = {} if traces is None else {
        f: lire(os.path.join(RACINE, f)) for f in prose_du_depot(traces)}
    prose = dict(prose)
    if "CONTRIBUTING.md" in prose:
        prose["CONTRIBUTING.md"] = M(
            9, prose["CONTRIBUTING.md"], "[`LICENSING.md`](LICENSING.md)",
            "[`LICENSING.md`](LICENSING-absent.md)")
        prose["CONTRIBUTING.md"] = M(
            10, prose["CONTRIBUTING.md"],
            "section *« Les deux paliers matériels »*",
            "section *« Les trois paliers matériels »*")
        prose["CONTRIBUTING.md"] = M(
            11, prose["CONTRIBUTING.md"], "dn_console.py --reset",
            "dn_console.py --redemarre")
        prose["CONTRIBUTING.md"] = M(
            12, prose["CONTRIBUTING.md"], "(`dn4-39` — see",
            "(`dn9-9` — see")
        prose["CONTRIBUTING.md"] = M(
            13, prose["CONTRIBUTING.md"], "**six** entries", "**five** entries")
        prose["CONTRIBUTING.md"] = M(
            14, prose["CONTRIBUTING.md"], "carried by\n   `dn8`",
            "carried by\n   `TBD`")
        prose["CONTRIBUTING.md"] = M(
            27, prose["CONTRIBUTING.md"], "and **a bot handles it**",
            "and the maintainer handles it")
    if "CHANGELOG.md" in prose:
        # ⚠️ CE MUTANT A DEJA ETE VU MUET, ET LE MOTIF VAUT D'ETRE ECRIT :
        #    sa 1re version laissait « no NVML » sur la ligne mutee, donc la
        #    REFUTATION y etait encore et le controle avait RAISON de rester
        #    vert. C'est la campagne qui l'a epingle. Il replante desormais la
        #    phrase REELLEMENT publiee jusqu'au 2026-09-02.
        prose["CHANGELOG.md"] = M(
            17, prose["CHANGELOG.md"],
            "- **The false claim that NVIDIA GPUs are covered.** NVIDIA is "
            "**not implemented**:\n  there is no NVML in the agent.",
            "- NVIDIA and AMD GPUs are covered.\n  That is what this file "
            "said, word for word.")
    roadmap = M(26, roadmap, "| `dn", "| dn", tous=True)

    section_liens(prose)
    section_citations(prose)
    section_marqueurs(prose, roadmap)
    section_comptes(prose)
    section_cla(prose.get("CONTRIBUTING.md", ""), roadmap)
    section_refutations(prose, agent)
    section_auto_coherence(tiers)

    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (OK[0], KO[0]))
    print("=" * 78)
    return 1 if KO[0] else 0


if __name__ == "__main__":
    sys.exit(main())

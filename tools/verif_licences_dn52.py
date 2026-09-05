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
   ⚠️ ANNOTE LE 2026-09-04 A LA REVUE DE CODE — LA DEUXIEME MOITIE DE LA
   PHRASE CI-DESSUS N'EST PLUS VRAIE, ET ELLE EST ⛔ NON EFFACEE (NFR3) :
   `docs/roadmap.md` a ete AMENDEE le 2026-09-04 (« un marqueur CITE DANS CET
   ARBRE reste liste apres sa cloture, avec l'etat `done` ») et `dn5-1`,
   `dn5-2`, `dn5-3` et `dn5` y ont donc RETROUVE une ligne. La premiere moitie,
   elle, TIENT : les `dn1-*`..`dn4-*` restent decrits la ou ils sont cites — ils
   sont 26, mesures le 2026-09-04. ⇒ le motif de la limite est INCHANGE, seule
   son illustration a bouge.
   `dnE-N` y soit ROUGIRAIT SUR DU CONTENU JUSTE. Le seul signal disponible
   est donc le renvoi lui-meme. ⇒ la convention du depot — un ecart s'ecrit
   AVEC le marqueur qui le porte, et le marqueur renvoie a la page — est ce
   qui rend le controle possible ; sans elle il ne l'est pas.

⛔ **LE CONTROLE (c7) RAISONNE A LA **LIGNE PHYSIQUE**.** La refutation doit tenir
   sur la MEME ligne que `NVIDIA`/`NVML`. Mesure du 2026-09-04 : re-flouer un
   paragraphe du `CHANGELOG` SANS CHANGER UN MOT de son sens, de sorte que
   `NVIDIA` finisse une ligne et `not implemented` commence la suivante, rend
   `⛔ ligne SANS refutation`. ⇒ un reformatage de prose ENTIEREMENT VRAIE fait
   rougir. La propriete par PARAGRAPHE serait plus juste et plus large — donc
   plus facile a satisfaire par accident. Le choix de la ligne est assume, et il
   est ECRIT ici plutot que decouvert par celui qui reformate.

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

# ── CE QUE LE TIR A REELLEMENT EMIS, ET CE QU'IL A DECLARE NE PAS EMETTRE ───
# 🔴 MESURE DU 2026-09-04 : en retirant `.github/workflows/`, le bilan tombait a
#    `23 OK, 2 KO` — soit **25 controles emis, ⛔ pas 28** — et AUCUNE ligne ne le
#    disait. Or la liste des controles du TIR SAIN est la reference contre
#    laquelle AC2.6.a confronte l'union des `[KO ]` : elle changeait avec la
#    FORME DE L'ARBRE, en silence. Un bilan qui retrecit sans le dire ment sur sa
#    propre couverture.
EMIS = []
DECLARES = set()

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
# ── AJOUTES LE 2026-09-04 PAR LA REVUE DE CODE, QUI A TROUVE CINQ CONTROLES
#    QUE RIEN NE GARDAIT (dont deux qui n'existaient pas encore)
# ── AJOUTE LE 2026-09-05 PAR `dn5-6` / CONSTAT (9) — NFR7 : IL **REPLANTE**
#    LA FAUTE, ⛔ IL NE DEBRANCHE RIEN. Le cas reel a disparu (les 4 marqueurs
#    cites sous `.github/` sont definis) ⇒ c'est le SEUL instrument qui peut
#    montrer que la portee elargie garde vraiment quelque chose.
MUTANTS[34] = ("cite dans `.github/workflows/gates.yml` un marqueur `dn9-9` "
               "ABSENT de docs/roadmap.md, en le renvoyant a la page "
               "(constat 9 : les `.yml` n'etaient JAMAIS balayes)")
# ── dn5-7 / NFR7 — LES TROIS MUTANTS QUI **REPLANTENT** (⛔ aucun ne debranche)
#    🔴 POURQUOI ILS SONT LA SEULE PREUVE POSSIBLE, ET C'EST MESURE :
#       les 5 renvois `§ *Titre*` de l'arbre RESOLVENT tous, et les chiffres
#       publies de `CONTRIBUTING.md` sont JUSTES a l'octet (mesure du
#       2026-09-05, `mesures/dn5-7/T1-filtre-8-reports.txt`). Un controle
#       elargi passe donc VERT — et vert ⛔ ne distingue pas « il garde » de
#       « il ne regarde rien ». ⛔ Un mutant qui DEBRANCHE la garde ne
#       prouverait que son existence : `dn5-6` a paye exactement ca, trois
#       fois.
MUTANTS[35] = ("falsifie un chiffre PUBLIE qui nomme son commit "
               "(`428 files` de `mesures/` a `76b031a` ⇒ 429)")
# ⚠️ LIBELLE CORRIGE LE 2026-09-05 (revue) : il annoncait « la forme SANS
#    lien markdown » alors qu'il mute `docs/roadmap.md`, dont le renvoi est
#    ECRIT AVEC son lien (`[`CONTRIBUTING.md`](../CONTRIBUTING.md) § *Titre*`).
#    ⇒ `--liste-mutants` publiait la MAUVAISE branche comme prouvee. C'est le
#    MUTANT 38 qui couvre la forme sans lien — son libelle ⛔ ne bouge pas.
MUTANTS[36] = ("plante un renvoi `§ *Titre*` vers une section INEXISTANTE "
               "(la forme **AVEC** lien markdown)")
MUTANTS[37] = ("remplace l'ancre COMMIT d'un chiffre publie par `HEAD` "
               "(l'ancre MOUVANTE : un arbre different chaque jour)")
# 🔴 LES DEUX FORKS DE LA RE-DERIVATION ETAIENT **COMPTES** ET GARDES PAR
#    RIEN — lacune trouvee a la revue du 2026-09-05. Le mutant 35 ne falsifie
#    qu'un chiffre en `files` de portee `mesures/` ; les 5 chiffres re-derives
#    incluent des OCTETS et l'ARBRE ENTIER, et rien ne prouvait que ces
#    branches-la rougissent. « Un compte n'est pas une garde. »
MUTANTS[39] = ("falsifie un chiffre publie en **OCTETS** "
               "(`10 234 634 bytes` de `mesures/` a `76b031a` ⇒ …635)")
MUTANTS[40] = ("falsifie un chiffre publie de l'**ARBRE ENTIER** "
               "(`46 254 844 bytes` a `76b031a` ⇒ …845)")
MUTANTS[38] = ("plante un renvoi `§ *Titre*` INEXISTANT dans la forme "
               "**SANS lien markdown** — le mutant 36 ne mute que la forme "
               "AVEC lien, et la branche sans lien restait sans preuve")

MUTANTS[29] = ("pose un SECOND workflow qui porte le signal du CLA et qui trie "
               "AVANT `cla.yml`, avec une action NON EPINGLEE")
MUTANTS[30] = ("checkoute le code de la PR par `github.head_ref` "
               "(l'orthographe que l'ancienne forme ne voyait pas)")
MUTANTS[31] = ("redescend la condition du workflow CLA hors du niveau JOB "
               "(le runner redevient ALLOUE et FACTURE)")
MUTANTS[32] = ("fait pointer `path-to-document` vers un AUTRE depot "
               "(le chemin resout EN LOCAL et mentait)")
MUTANTS[33] = ("ecrit une version du manifeste en guillemets SIMPLES "
               "(le parseur ne la lit pas, et se taisait)")


def dire(ok, libelle, detail=""):
    (OK if ok else KO)[0] += 1
    EMIS.append(libelle)
    print("  [%s] %-58s %s" % ("OK " if ok else "KO ", libelle, detail))


def declarer(motif, *libelles):
    """Un controle PREVU qui n'est PAS emis, et qui le DIT. ⛔ Ce n'est pas une
    exemption : le controle final (« tout controle prevu est EMIS ou DECLARE »)
    rougit sur tout libelle de l'INVENTAIRE qui manque SANS passer par ici."""
    DECLARES.update(libelles)
    note("⛔ %d CONTROLE(S) NON EMIS — %s" % (len(libelles), motif))
    for l in libelles:
        print("       · %s" % l)


def note(texte):
    """Une LIMITE declaree. ⛔ Ce n'est pas un controle : elle ne compte pas au
    bilan. Elle est imprimee pour qu'un lecteur voie ce qui N'EST PAS garde."""
    print("  [⚠️ ] %s" % texte)


# ── L'INVENTAIRE DES CONTROLES D'UN TIR NOMINAL ────────────────────────────
# ⚠️ OUI, C'EST UNE LISTE ECRITE, ET C'EST LE SEUL CAS OU LA REGLE (1) DE
#    `run_gates.sh` NE S'APPLIQUE PAS : ce n'est pas une liste de chemins
#    ATTENDUS dans un arbre qui bouge, c'est la SPECIFICATION de ce que cette
#    gate emet. Elle est gardee DANS LES DEUX SENS — un libelle de l'inventaire
#    qui n'est pas emis et n'est pas declare rougit ; un libelle emis qui n'est
#    pas a l'inventaire rougit aussi ⇒ ajouter un controle sans l'inscrire ici
#    fait rougir le tir suivant, ⛔ elle ne peut pas se perimer en silence.
INVENTAIRE = (
    "la TABLE de LICENSING.md se lit",
    "la phrase de REPLI de LICENSING.md se lit",
    "tout chemin ANNONCE existe dans l'arbre",
    "tout repertoire TRACE est nomme par l'une des 2 listes",
    "le fichier de licence annonce EXISTE",
    "le fichier de licence DIT BIEN la licence annoncee",
    "chaque licence annoncee a une signature connue",
    "le manifeste `idf_component.yml` se lit",
    "la table § Firmware de THIRD-PARTY.md se lit",
    "toute ligne du bloc `dependencies` est LUE",
    "toute entree du manifeste figure au tableau",
    "toute ligne du tableau est EPINGLEE, ALIAS ou TRANSITIVE",
    "les versions EPINGLEES concordent (`==` retire)",
    "l'ALIAS declare apparie les deux cotes",
    "*(transitive)* ⟺ ABSENT du manifeste (les 2 sens)",
    "`managed_components/` hors du clone (fonde la limite)",
    "tout lien local des fichiers de prose resout",
    "la section citee PAR SON TITRE existe",
    "l'outil cite AVEC SON DRAPEAU l'accepte (invoque)",
    "docs/roadmap.md definit des marqueurs",
    "tout marqueur cite COMME marqueur est defini",
    "le COMPTE annonce egale le nombre d'entrees",
    # ── dn5-7 / report (1) de `dn5-5` ───────────────────────────────────
    "tout chiffre ANCRE sur un commit se re-derive",
    "⛔ aucun chiffre publie n'ancre sur une ref MOUVANTE",
    "la promesse de bot et son workflow disent la meme chose",
    "chaque action du workflow CLA est EPINGLEE",
    "le document que le bot fait signer EXISTE",
    "`path-to-document` designe CE depot",
    "la condition du workflow CLA est au niveau du JOB",
    "⛔ le workflow ne checkoute JAMAIS le code de la PR",
    "l'ecart residuel du CLA a un PORTEUR reel",
    "toute ligne qui nomme NVIDIA/NVML porte sa REFUTATION",
    "THIRD-PARTY.md dit que cette gate le garde",
    "tout controle prevu est EMIS ou DECLARE",
)

# Emis UNIQUEMENT quand le prerequis tombe : ⛔ pas un controle du tir nominal.
DIAGNOSTICS = ("l'arbre trace se lit (`git ls-files`)",)

# Les controles qui n'existent QUE si un workflow porte le CLA.
CONDITIONNELS_CLA = (
    "chaque action du workflow CLA est EPINGLEE",
    "le document que le bot fait signer EXISTE",
    "`path-to-document` designe CE depot",
    "la condition du workflow CLA est au niveau du JOB",
    "⛔ le workflow ne checkoute JAMAIS le code de la PR",
)


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
    dossiers de mesure, ils CITENT les sorties qu'ils enregistrent.

    ⚠️ dn5-6, 2026-09-05 — SA PORTEE N'A **PAS** CHANGE, ET C'EST VOULU : le
       constat (9) est traite par `prose_marqueurs()` juste en dessous, qui
       ajoute les workflows **pour le seul controle des marqueurs**.

    🔴 dn5-6 / CONSTAT (9) — 2026-09-05 : LA PORTEE DU CONTROLE DES MARQUEURS
       ETAIT PLUS ETROITE QUE CE QUE LE DEPOT DISAIT D'ELLE. Elle ne rendait que des `.md` ⇒ un marqueur
       cite dans `.github/workflows/*.yml` n'etait **JAMAIS** controle, alors
       que `gates.yml` affirmait de ce controle qu'il « exige que tout marqueur
       cite comme marqueur soit defini dans `docs/roadmap.md` », sans dire
       « les `.md` de la racine et de `docs/` seulement ».

       ⚠️ **LE CAS DE DEMONSTRATION EST TOMBE ENTRE-TEMPS, ET C'EST ECRIT.**
       `dn5-4` l'avait etabli sur « `gates.yml` renvoie vers `dn4-45`, absent
       de `docs/roadmap.md` ». MESURE DU 2026-09-05
       (`mesures/dn5-6/T1-filtre-10-constats.txt`, constat 9) : les **4**
       marqueurs cites sous `.github/` — `dn4-39`, `dn4-45`, `dn5-2`, `dn5-4` —
       sont **TOUS** definis dans la roadmap (`dn5-5` y a ajoute `dn4-45`).
       ⇒ elargir la portee **laisse la gate VERTE aujourd'hui** : ⛔ AUCUN
       rouge ne peut etablir ce trou. Seul le **mutant 34**, qui REPLANTE la
       faute, le peut — et c'est pour ca qu'il existe.

    ⚠️ LES WORKFLOWS SONT DE LA PROSE QUI POINTE UN LECTEUR : ils portent des
       renvois, des marqueurs et des porteurs, exactement comme les pages. Ce
       qui les distingue d'une capture, c'est qu'ils s'ADRESSENT a quelqu'un.
    """
    return [f for f in fichiers
            if f.endswith(".md") and ("/" not in f or f.startswith("docs/"))]


def prose_marqueurs(fichiers):
    """La prose de `prose_du_depot()` **PLUS les workflows**.

    🔴 dn5-6 / REVUE DU 2026-09-05 — L'ELARGISSEMENT ETAIT TROP LARGE.
       Le premier jet elargissait `prose_du_depot()` elle-meme, or elle
       alimente **SIX** sections : `section_liens`, `section_citations`,
       `section_marqueurs`, `section_comptes`, `section_cla`,
       `section_refutations`. ⇒ un commentaire de workflow portant un lien
       markdown local, un titre de section cite, un compte annonce ou une
       invocation `python3 tools/x.py --drapeau` serait tombe **en silence**
       sous des controles qui n'ont jamais ete ecrits pour du YAML.
       ⛔ Le constat (9) porte sur **les marqueurs**, ⛔ pas sur tout le reste.
    ⇒ SEULE `section_marqueurs` recoit la portee elargie.
    """
    return prose_du_depot(fichiers) + [
        f for f in fichiers
        if f.startswith(".github/workflows/") and f.endswith((".yml", ".yaml"))]


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
    est retire, et seules les deux formes reellement utilisees sont lues.

    🔴 REND AUSSI LES LIGNES QU'IL N'A PAS SU LIRE. Sans ca, une version en
    guillemets SIMPLES, nue, ou indentee a quatre espaces sortait du dictionnaire
    SANS UN MOT — et si le composant etait AUSSI absent de `THIRD-PARTY.md`, le
    controle bidirectionnel passait VERT sur une dependance invisible, ce qui est
    tres exactement ce que cette gate existe pour attraper.

    ⚠️ Et le bloc se QUITTE sur la premiere cle de premier niveau qui suit :
    `dependencies:` est la derniere aujourd'hui, mais un bloc frere dont les cles
    sont a deux espaces aurait ete lu comme des dependances — un faux rouge sur
    un manifeste JUSTE."""
    deps, non_lues, dans, courant = {}, [], False, None
    for ligne in src.splitlines():
        if re.match(r"^dependencies:\s*$", ligne):
            dans = True
            continue
        if not dans:
            continue
        if re.match(r"^[A-Za-z_.]", ligne):        # cle de 1er niveau ⇒ on SORT
            dans = False
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
            continue
        non_lues.append(s.strip())
    return deps, non_lues


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
    manifeste = M(33, manifeste, 'lvgl/lvgl: "==9.5.0"', "lvgl/lvgl: '==9.5.0'")

    deps, non_lues = lire_manifeste(manifeste)
    lignes = lire_tableau_tiers(tiers)

    dire(bool(deps), "le manifeste `idf_component.yml` se lit",
         "%d entree(s)" % len(deps) if deps else "⛔ ILLISIBLE")
    dire(bool(lignes), "la table § Firmware de THIRD-PARTY.md se lit",
         "%d ligne(s)" % len(lignes) if lignes else "⛔ ILLISIBLE")
    if not deps or not lignes:
        return

    # ── TOUTE LIGNE DU BLOC EST LUE — ⛔ une ligne muette n'est pas une ligne
    #    absente. C'est le seul controle qui garde le PARSEUR lui-meme.
    dire(not non_lues, "toute ligne du bloc `dependencies` est LUE",
         "%d entree(s) lue(s)" % len(deps) if not non_lues
         else "⛔ ligne(s) NON LUE(S) : " + " · ".join(non_lues[:3]))

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
    # ⛔ `traces is None` rendait `trace` FAUX, donc ce controle annoncait `OK`
    #    sur un arbre qu'il n'avait JAMAIS PU LIRE. Un vert sur une lecture
    #    ratee est pire qu'un rouge : il affirme.
    dire(traces is not None and ignore and not trace,
         "`managed_components/` hors du clone (fonde la limite)",
         "gitignore=%s · trace=%s" % ("oui" if ignore else "⛔ NON",
                                      "⛔ OUI" if trace else "non")
         if traces is not None else "⛔ arbre trace ILLISIBLE")
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
    # ⛔ `not casses` etait VRAI sur zero fichier. c3 et c5 portaient deja leur
    #    garde de non-vacuite (`bool(essayes)`, `vus > 0`) ; c1 et c2 non.
    dire(not casses and bool(textes),
         "tout lien local des fichiers de prose resout",
         "%d lien(s) local(aux), %d fichier(s)" % (total, len(textes))
         if not casses and textes
         else ("⛔ " + " · ".join(casses[:3]) if casses
               else "⛔ AUCUN fichier de prose — ⛔ pas vert sur du vide"))


def section_citations(textes):
    print("\n── (c2/c3) LES SECTIONS ET LES OUTILS CITES EXISTENT ─────────────")

    # ── UNE SECTION CITEE PAR SON TITRE ───────────────────────────────────
    # 🔴 dn5-7 / REPORT (2) DE `dn5-5`, RE-MESURE LE 2026-09-05 — LA PORTEE
    #    ETAIT PLUS ETROITE QUE LE DEPOT NE L'ECRIVAIT, ET LE TRACKER S'ETAIT
    #    TROMPE SUR L'AMPLEUR. Le report parlait de **2** renvois `§ *Titre*` ;
    #    le tracker a mesure `CONTRIBUTING.md` SEUL, y a trouve 0 renvoi, et a
    #    conclu « le cas a disparu ». MESURE sur les **10** fichiers de prose
    #    que cette gate balaie : il y a **5** renvois `§ *Titre*` **CROISES**
    #    (vers un AUTRE fichier) — 3 dans `docs/dn5-1-ecart-promesses.md`, 2
    #    dans `docs/roadmap.md` — et la gate n'en confrontait **1**.
    # ⚠️ LE LIBELLE NE CHANGE PAS : `verif_campagne_dn440.py` et
    #    `verif_campagne_dn56.py` ciblent PAR LIBELLE.
    # ⚠️ LES 5 RESOLVENT TOUS ⇒ ⛔ aucun rouge naturel n'est possible ici : le
    #    MUTANT 36, qui REPLANTE un titre inexistant, est la SEULE preuve.
    # ⛔ CE QUE CE CONTROLE NE VOIT PAS, ET C'EST ECRIT : un renvoi `§ *Titre*`
    #    qui ne cite AUCUN fichier cible (le renvoi INTERNE — il y en a 1 dans
    #    l'arbre) n'est pas confronte. Sa cible est la page elle-meme ; le
    #    controle est ecrit pour le renvoi CROISE, celui qui pourrit quand un
    #    AUTRE fichier bouge.
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
        # ── LA FORME `§ *Titre*`, AVEC **OU SANS** LIEN MARKDOWN ───────────
        for fichier, titre in renvois_section(plat):
            vues += 1
            cible = resout_prose(nom, fichier)
            if cible is None:
                absentes.append("%s : `%s` INTROUVABLE (§ *%s*)"
                                % (nom, fichier, titre))
            elif titre not in lire(cible):
                absentes.append("%s : « %s » dans %s"
                                % (nom, titre, fichier))
    # 🔴 MESURE DU 2026-09-04 : en reformulant l'UNIQUE citation hors de la forme
    #    reconnue et en pointant un titre INEXISTANT, ce controle rendait
    #    `[OK ] … 0 citation(s)` et le bilan restait `28 OK, 0 KO`. Le mutant 10
    #    change le titre A L'INTERIEUR de la forme : il ne pouvait pas le voir.
    dire(not absentes and vues > 0, "la section citee PAR SON TITRE existe",
         "%d citation(s)" % vues if not absentes and vues
         else ("⛔ " + " · ".join(absentes) if absentes
               else "⛔ AUCUNE citation trouvee — ⛔ pas vert sur du vide"))

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


# ═══════════════════════════════════════════════════════════════════════════
# (c5-bis) UN CHIFFRE PUBLIE SE RE-DERIVE **AU COMMIT QU'IL NOMME** — dn5-7
#
# 🔴 LE REPORT (1) DE `dn5-5`, REJOUE LE 2026-09-05 : `grep -rn ls-tree` sur
#    les 30 gates + `run_gates.sh` rend **rc=1, sortie VIDE**. AUCUNE gate ne
#    confronte le chiffre publie de `mesures/` a l'arbre — et il a deja pourri
#    QUATRE fois (les cinq figures historiques datees de `CONTRIBUTING.md`).
#
# 🎯 POURQUOI CE CONTROLE EST POSSIBLE ALORS QUE `CONTRIBUTING.md` DECLARE LE
#    PROBLEME INSATISFIABLE. La page a raison sur ce qu'elle REFUTE : « le
#    chiffre publie ici est celui que l'arbre qui le porte rend » est un POINT
#    FIXE — la taille de l'arbre inclut ce fichier, dont la taille depend du
#    chiffre ecrit dedans. Mais elle publie aussi la regle qui s'en sort :
#    **nommer le commit**. `git ls-tree -r -l <commit>` est DETERMINISTE et
#    INDEPENDANT de l'arbre de travail. ⇒ ce controle ne demande pas « ce
#    chiffre decrit-il aujourd'hui ? » (indecidable) mais « ce chiffre
#    decrit-il LE COMMIT QU'IL NOMME ? » (falsifiable).
# ⛔ IL NE RE-DERIVE JAMAIS A `HEAD` : `HEAD` designe un arbre different chaque
#    jour ⇒ il n'y aurait plus de point fixe du tout.
#
# ⚠️ LA POPULATION EST LA CONVENTION D'ANCRAGE DU DEPOT, ⛔ PAS « TOUT NOMBRE » :
#    un chiffre entre en population quand sa PHRASE porte une ancre ecrite
#    ``**`<ref>`**`` (gras + accents graves — la forme que `CONTRIBUTING.md`
#    emploie deja) ET que le chiffre porte son UNITE (`bytes`/`files`) ET
#    qu'une PORTEE le precede dans la meme phrase (un chemin suivi en accents
#    graves, ou « tracked files » / « this repository »).
# ⛔ CE QUI RESTE DONC HORS GARDE, ET C'EST ECRIT PLUTOT QUE TU : un chiffre
#    qui nomme son commit HORS de cette convention (par exemple « on `main` at
#    `7246f52` … the largest file … is **5 071 848 bytes** » — ancre en accents
#    graves SANS gras, et grandeur « le plus gros blob », qui n'est ⛔ pas la
#    somme d'un chemin) n'est pas confronte. L'elargir A L'AVEUGLE fabriquerait
#    un FAUX KO : la mesure du 2026-09-05 l'a montre sur `docs/roadmap.md`, ou
#    « `docs/` pese **27 992 816 bytes** des **46 254 844** » attribuerait le
#    second chiffre a `docs/` par simple proximite. ⇒ portee ETROITE et
#    DECLAREE, ⛔ pas large et fausse.
# ═══════════════════════════════════════════════════════════════════════════

# 🔴 UNE ANCRE SE RECONNAIT A SA **POSITION**, ⛔ pas au fait d'etre en gras :
#    `on **`X`**` / `at **`X`**` — la forme que `CONTRIBUTING.md` emploie deja.
#    Sans la position, `**`1`**` d'une phrase de `README.md` entrait en
#    population (mesure du 2026-09-05) et rougissait sur de la prose JUSTE.
RE_ANCRE_COMMIT = re.compile(
    r"\b(?:on|at|au|commit)\s+\*\*`([^`]{1,60})`\*\*", re.I)
RE_SHA = re.compile(r"^[0-9a-f]{7,40}$")


def sha_de_forme(a):
    """L'ancre a-t-elle la FORME d'un SHA abrege ?

    🔴 REVUE DU 2026-09-05 — `RE_SHA` SEUL ACCEPTE UN **DECIMAL** : mesure,
    `RE_SHA.match("46254844")` rend `True`. Une phrase publiant
    ``at **`46254844`**`` faisait donc prendre au controle la branche « commit
    absent du clone » ⇒ `declarer()` + `return`, et **toute la re-derivation se
    desarmait sur une ancre bidon**. ⇒ un SHA porte au moins une LETTRE
    hexadecimale ; un nombre qui n'en porte aucune n'est ⛔ pas un commit, il
    est MOUVANT et il rougit.
    """
    return bool(RE_SHA.match(a)) and bool(re.search(r"[a-f]", a))
_ESP = "\u0020\u00a0\u202f\u2009"
RE_GRANDEUR = re.compile(
    r"\*\*\s*([0-9][0-9" + _ESP + r"]*?)\s*"
    r"(bytes|files|octets|fichiers)?\s*\*\*"
    r"(?:\s*(bytes|files|octets|fichiers)\b)?")
RE_CHEMIN_SUIVI = re.compile(r"`([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*/)`")
RE_ARBRE_ENTIER = re.compile(r"tracked files|this repository|whole tree"
                             r"|arbre entier")
UNITES_FICHIERS = ("files", "fichiers")

# ── dn5-7 / report (2) : le renvoi `§ *Titre*`, AVEC **ou sans** lien ───────
RE_REF_MD = re.compile(r"\[`([^`]+\.md)`\]\([^)]*\)|`([^`]+\.md)`")
RE_SECTION_TITRE = re.compile(r"§\s*\*([^*]{1,90})\*")
GAP_RENVOI = 40


def renvois_section(plat):
    """`[(fichier, titre)]` — les renvois `§ *Titre*` et LEUR fichier.

    🔴 REVUE DU 2026-09-05 — L'APPARIEMENT SE FAISAIT PAR SIMPLE PROXIMITE,
    SANS EXIGER QUE LES DEUX SOIENT LE MEME RENVOI, et il avait DEUX trous :
      *(i)* un paragraphe qui NOMME un fichier puis fait un renvoi **INTERNE**
            moins de 40 caracteres plus loin produisait un FAUX KO (le titre
            interne confronte au mauvais fichier) — et
            `docs/dn5-1-ecart-promesses.md` porte deja les DEUX formes ;
      *(ii)* un **SECOND** `§ *Titre*` apres la meme reference n'etait JAMAIS
            confronte.
    ⇒ LA REGLE : une reference gouverne les `§ *Titre*` qui la suivent
      **jusqu'a la reference suivante**, EN CHAINE — chacun a moins de
      `GAP_RENVOI` caracteres du precedent. ⛔ Aucun appariement par-dessus une
      reference intercalee.
    """
    refs = [(m.start(), m.end(), m.group(1) or m.group(2))
            for m in RE_REF_MD.finditer(plat)]
    out = []
    for k, (_s0, e0, fichier) in enumerate(refs):
        fin = refs[k + 1][0] if k + 1 < len(refs) else len(plat)
        pos = e0
        for m in RE_SECTION_TITRE.finditer(plat, e0, fin):
            if m.start() - pos > GAP_RENVOI:
                break
            out.append((fichier, m.group(1).strip()))
            pos = m.end()
    return out


def resout_prose(depuis, fichier):
    """Le chemin REEL d'un `x.md` cite depuis `depuis` — ⛔ jamais devine.

    Un lecteur resout `README.md` cite depuis `docs/…` d'abord a cote du
    fichier citant, puis A LA RACINE (c'est la seule autre lecture possible :
    ces pages sont a la racine). Rend `None` si aucune des deux n'existe —
    ⛔ pas un chemin fabrique.
    """
    proche = os.path.normpath(os.path.join(RACINE, os.path.dirname(depuis),
                                           fichier))
    if os.path.exists(proche):
        return proche
    racine = os.path.normpath(os.path.join(RACINE, fichier))
    return racine if os.path.exists(racine) else None


def _entier(s):
    return int(re.sub(r"[^0-9]", "", s))


def ls_tree(rev, chemin=None):
    """`(n_fichiers, octets)` de l'arbre `rev` — ⛔ jamais de l'arbre de travail.

    Rend `None` si `git` refuse (commit absent du clone, `git` indisponible) :
    l'appelant en fait une DECLARATION, ⛔ pas un Traceback ⛔ ni un vert.
    """
    args = ["git", "ls-tree", "-r", "-l", rev]
    if chemin:
        args += ["--", chemin]
    # ⚠️ `subprocess.run` **LEVE** `FileNotFoundError` quand l'executable
    #    manque — il ⛔ ne rend PAS un `rc` non nul. Sans ce `except`, la
    #    promesse « ⛔ pas un Traceback » de la ligne (1-bis) etait fausse.
    try:
        r = subprocess.run(args, cwd=RACINE, capture_output=True, text=True)
    except OSError:
        return None
    if r.returncode != 0:
        return None
    n = tot = 0
    for l in r.stdout.splitlines():
        m = re.match(r"^\d+ blob [0-9a-f]+\s+(\d+)\t", l)
        if m:
            n += 1
            tot += int(m.group(1))
    return n, tot


def commit_present(rev):
    """L'ancre designe-t-elle un **OBJET REEL** de CE clone ?

    ⚠️ `.github/workflows/gates.yml` checkoute en `fetch-depth: 1` ⇒ la reponse
    y est NON pour un commit ancien, et c'est NORMAL.
    ⛔ Elle n'est appelee QU'APRES `sha_de_forme()` : `git rev-parse --verify
    HEAD^{commit}` REUSSIT, et traiter `HEAD` comme un commit verifie
    desarmerait exactement le controle (1-ter).
    ⚠️ `except OSError` : `git` absent LEVE, il ne rend pas un `rc`.
    """
    try:
        r = subprocess.run(["git", "rev-parse", "--verify", "--quiet",
                            rev + "^{commit}"],
                           cwd=RACINE, capture_output=True, text=True)
    except OSError:
        return False
    return r.returncode == 0


def figures_ancrees(textes):
    """Les chiffres PUBLIES qui NOMMENT leur commit, avec leur portee.

    ⚠️ L'ANCRE SE PREND DANS LA **PHRASE**, LA PORTEE AUSSI. Mesure du
    2026-09-05 : pris au PARAGRAPHE, l'ancre `76b031a` capturait les CINQ
    figures historiques que `CONTRIBUTING.md` garde DELIBEREMENT sans ancre
    (« 395 files / 9 900 692 bytes », etc.) et les declarait fausses. ⛔ Une
    figure sans ancre n'entre pas en population : elle n'affirme rien sur un
    commit.
    """
    out = []
    for nom, src in sorted(textes.items()):
        for para in re.split(r"\n\s*\n", src):
            plat = re.sub(r"\s+", " ", para)
            # ⚠️ Le point d'un nombre decimal (`10.23 MB`) ⛔ ne coupe pas une
            #    phrase : la coupe exige un caractere NON CHIFFRE avant le `.`.
            for phrase in re.split(r"(?<=[^\d])\.\s+", plat):
                # 🔴 LA GARDE DE CITATION, IDENTIQUE A CELLE DE
                #    `designations_de()` DANS LA GATE DU LEDGER : dans un code
                #    span, c'est une CITATION, ⛔ pas une ancre. Sans elle, une
                #    phrase de documentation du type
                #    ``⛔ ne jamais ancrer **603 files** sur **`HEAD`**``
                #    faisait rougir « aucun chiffre publie n'ancre sur une ref
                #    MOUVANTE » sur de la prose PARFAITEMENT JUSTE — et
                #    `docs/roadmap.md` porte une regle d'admission qui pousse
                #    a ecrire ce genre de phrase. ⛔ Ce n'est pas une liste
                #    d'exclusion : la garde est structurelle.
                ancres = [m.group(1)
                          for m in RE_ANCRE_COMMIT.finditer(phrase)
                          if not phrase[:m.start()].count("`") % 2]
                if not ancres:
                    continue
                for m in RE_GRANDEUR.finditer(phrase):
                    unite = m.group(2) or m.group(3)
                    if not unite:
                        continue
                    if phrase[:m.start()].count("`") % 2:
                        continue
                    avant = phrase[:m.start()]
                    pc = list(RE_CHEMIN_SUIVI.finditer(avant))
                    pa = list(RE_ARBRE_ENTIER.finditer(avant))
                    ic = pc[-1].start() if pc else -1
                    ia = pa[-1].start() if pa else -1
                    if ic < 0 and ia < 0:
                        portee = None          # ⛔ hors population : rien a derive
                    elif ic > ia:
                        portee = pc[-1].group(1)
                    else:
                        portee = ""            # l'arbre ENTIER
                    out.append({
                        "fichier": nom,
                        "ancres": sorted(set(ancres)),
                        "ancre": ancres[0],
                        "unite": unite,
                        "valeur": _entier(m.group(1)),
                        "portee": portee,
                        "brut": m.group(0).strip(),
                    })
    return out


def section_ancrages(textes):
    print("\n── (c5-bis) UN CHIFFRE PUBLIE SE RE-DERIVE A SON COMMIT ──────────")
    figures = figures_ancrees(textes)

    # ── (1-ter) L'ANCRE MOUVANTE EST **REFUSEE** ──────────────────────────
    # 🔴 REGLE **INVERSEE** A LA REVUE DU 2026-09-05. `REFS_MOUVANTES` etait
    #    une liste d'exclusion EN DUR : une ancre `HEAD~2`, `origin/dev`, un nom
    #    de branche ou un tag DEPLACABLE (`v0.1.0-beta`, que la ligne 2 de la
    #    liste AC5.6 prevoit de poser) n'etait ⛔ ni refusee ⛔ ni confrontee —
    #    elle quittait la population EN SILENCE, et le libelle promettait plus
    #    large que ce que le code decidait.
    # ⇒ TOUT CE QUI N'A PAS LA FORME D'UN SHA EST **MOUVANT**, ET ROUGIT.
    mouvants = ["%s : « %s » ancre sur `%s`" % (f["fichier"], f["brut"],
                                                f["ancre"])
                for f in figures if not sha_de_forme(f["ancre"])]
    ambigus = ["%s : « %s » entre %d ancres (%s)"
               % (f["fichier"], f["brut"], len(f["ancres"]),
                  ", ".join(f["ancres"]))
               for f in figures if len(f["ancres"]) > 1]
    dire(not mouvants and not ambigus and bool(figures),
         "⛔ aucun chiffre publie n'ancre sur une ref MOUVANTE",
         "%d chiffre(s) ancre(s), tous sur un COMMIT" % len(figures)
         if figures and not mouvants and not ambigus
         else ("⛔ " + " · ".join((mouvants + ambigus)[:3])
               if (mouvants or ambigus)
               else "⛔ AUCUN chiffre ancre trouve — ⛔ pas vert sur du vide"))

    # ── (1) LE CHIFFRE SE RE-DERIVE **AU COMMIT NOMME** ───────────────────
    # ⚠️ LE LIBELLE EST ECRIT **EN TOUTES LETTRES** DANS `dire()` ET DANS
    #    `declarer()`, ⛔ pas par cette variable — mesure du 2026-09-05 :
    #    `dn_sites.py` lit le SOURCE au tokenizer, et un 2e argument qui n'est
    #    pas un LITTERAL de chaine sort « illisible » ⇒ le libelle n'entre dans
    #    AUCUN index, et toute campagne qui ciblerait par libelle le raterait.
    #    La meme faute a rendu `⛔ CIBLE INTROUVABLE AU SOURCE` sur la gate du
    #    ledger, le meme jour. La variable ne sert plus qu'aux messages.
    LIB = "tout chiffre ANCRE sur un commit se re-derive"
    par_ancre = {}
    for f in figures:
        if sha_de_forme(f["ancre"]) and f["portee"] is not None:
            par_ancre.setdefault(f["ancre"], []).append(f)
    sans_portee = [f for f in figures if f["portee"] is None]
    if sans_portee:
        note("%d chiffre(s) ancre(s) ne nomment AUCUNE portee suivie ⇒ ⛔ pas "
             "derivables par `git ls-tree` (ex. `du -sb .git`) : %s"
             % (len(sans_portee),
                " · ".join("%s « %s »" % (f["fichier"], f["brut"])
                           for f in sans_portee[:2])))
    absents = sorted(a for a in par_ancre if not commit_present(a))
    confrontables = [f for a in par_ancre if a not in absents
                     for f in par_ancre[a]]
    if absents and not confrontables and _MUTANT is not None:
        # 🔴 REVUE DU 2026-09-05 — UN MUTANT ARME NE SE **DECLARE** JAMAIS NON
        #    EMIS, ET LA CI LE PROUVAIT. MESURE dans un vrai
        #    `git clone --depth 1` : `--mutant 35` sortait **rc=0 / 33 OK,
        #    0 KO** (l'ancre `76b031a` y est absente ⇒ sortie anticipee AVANT
        #    toute confrontation), et `verif_campagne_dn56.py` — qui n'est
        #    ⛔ PAS dans `NON_JOUABLES` et tourne donc en CI sur un checkout
        #    `fetch-depth: 1` — rendait `[KO ] tout mutant rend rc=1 ⛔ NE
        #    ROUGISSENT PLUS : tools/verif_licences_dn52.py#35`. La CI aurait
        #    ete ROUGE au premier push, avec un motif qui accuse a tort le
        #    mutant.
        # ⇒ UNE FAUTE REPLANTEE RESTE UNE FAUTE, MEME NON CONFRONTABLE ICI.
        #    ⛔ Pas d'exception dans `EXCEPTIONS` de `verif_campagne_dn56.py` :
        #    elle serait PERIMEE sur un clone complet et ferait rougir (c3).
        dire(False, "tout chiffre ANCRE sur un commit se re-derive",
             "⛔ MUTANT %d ARME et ancre(s) %s absente(s) de ce clone : une "
             "faute REPLANTEE ne se DECLARE pas non emise"
             % (_MUTANT, ", ".join("`%s`" % a for a in absents)))
        return
    if absents and not confrontables:
        # ⇒ (1-bis) LE CAS DE LA CI : `actions/checkout` avec `fetch-depth: 1`.
        #    ⛔ Pas un Traceback, ⛔ pas un vert sur du vide, ⛔ pas un saut muet.
        declarer("le(s) commit(s) nomme(s) %s ne sont pas dans CE clone "
                 "(`.github/workflows/gates.yml` checkoute en `fetch-depth: 1`)"
                 " ⇒ la grandeur ne peut pas etre re-derivee ICI. ⛔ Le `rc` du"
                 " contrat ne bouge pas." % ", ".join("`%s`" % a for a in absents),
                 "tout chiffre ANCRE sur un commit se re-derive")
        return
    if absents:
        note("%d ancre(s) absente(s) de ce clone, ⛔ non confrontee(s) : %s"
             % (len(absents), ", ".join("`%s`" % a for a in absents)))
    faux = []
    for f in confrontables:
        d = ls_tree(f["ancre"], f["portee"] or None)
        if d is None:
            faux.append("%s : `git ls-tree` refuse `%s`"
                        % (f["fichier"], f["ancre"]))
            continue
        reel = d[0] if f["unite"] in UNITES_FICHIERS else d[1]
        if reel != f["valeur"]:
            faux.append("%s publie %d %s pour `%s` a `%s` — l'arbre rend %d"
                        % (f["fichier"], f["valeur"], f["unite"],
                           f["portee"] or "(arbre entier)", f["ancre"], reel))
    dire(not faux and bool(confrontables),
         "tout chiffre ANCRE sur un commit se re-derive",
         "%d chiffre(s) re-derive(s) a leur commit (%s)"
         % (len(confrontables),
            ", ".join("`%s`" % a for a in sorted(par_ancre) if a not in absents))
         if confrontables and not faux
         else ("⛔ " + " · ".join(faux[:2]) if faux
               else "⛔ AUCUN chiffre confrontable — ⛔ pas vert sur du vide"))


# ── LE LEURRE DU MUTANT 29 : un workflow qui porte VRAIMENT le signal du CLA
#    et qui trie AVANT `cla.yml`. ⛔ Aucun fichier n'est ecrit.
LEURRE_CLA = """name: Leurre
on: [push]
jobs:
  leurre:
    runs-on: ubuntu-latest
    if: >-
      github.event_name == 'push'
    steps:
      - uses: contributor-assistant/github-action@main
        with:
          path-to-signatures: '.github/cla-signatures.json'
          path-to-document: 'https://github.com/nasbarok/desknode/blob/main/CLA.md'
"""


def porte_le_cla(wf):
    """🔴 ⛔ PAS `re.search("cla", corps, re.I)`. MESURE DU 2026-09-04 :
    `.github/workflows/gates.yml` porte NEUF fois la sous-chaine `cla`
    (`DECLAREES`, `cla.yml` cite en commentaire) ⇒ la gate annoncait
    `workflow(s) CLA=2`, et le TRI ALPHABETIQUE (`c` < `g`) etait la SEULE chose
    qui designait encore le bon fichier. Un `ci.yml` portant `clang-format`
    aurait fait auditer un AUTRE fichier pendant que le libelle s'affichait
    quand meme — et le controle de surete (« ne checkoute jamais le code de la
    PR ») aurait cesse de regarder `cla.yml`. Le signal est ce qui fait qu'un
    workflow EST celui du CLA : l'action, ou le magasin de signatures."""
    return (re.search(r"contributor-assistant/", wf) is not None
            or re.search(r"^\s*path-to-signatures:", wf, re.M) is not None)


def muter_cla(wf):
    """Les mutants qui visent `cla.yml` — ⛔ ils ne s'appliquent qu'a LUI."""
    wf = M(15, wf, "path-to-document:", "path-to-document-absent:")
    wf = M(16, wf, "github-action@v2.6.1", "github-action@main")
    wf = M(28, wf, '      - name: "Signature du CLA"',
           "      - uses: actions/checkout@v4\n"
           "        with:\n"
           "          ref: ${{ github.event.pull_request.head.sha }}\n"
           '      - name: "Signature du CLA"')
    wf = M(30, wf, '      - name: "Signature du CLA"',
           "      - uses: actions/checkout@v4\n"
           "        with:\n"
           "          ref: ${{ github.head_ref }}\n"
           '      - name: "Signature du CLA"')
    wf = M(31, wf, "    if: >-\n", "    # if: >-\n")
    wf = M(32, wf, "https://github.com/nasbarok/desknode/blob/main/CLA.md",
           "https://github.com/acme/autre-depot/blob/main/CLA.md")
    return wf


def if_au_niveau_job(wf):
    """La condition doit vivre sous `jobs.<id>:`, AVANT `steps:`. MESURE T3 §4 :
    a l'ETAPE, GitHub ALLOUE le runner et DECOMPTE les minutes avant de sauter
    l'etape — sur un depot PRIVE, un commentaire d'issue SANS RAPPORT etait
    facture. Le fichier appelle cette propriete « une MESURE, ⛔ pas un style »
    et, jusqu'au 2026-09-04, AUCUN controle et AUCUN mutant ne la lisaient :
    supprimer le bloc sortait en `28 OK, 0 KO`."""
    m = re.search(r"^jobs:\s*$", wf, re.M)
    if not m:
        return False
    bloc = wf[m.end():]
    fin = re.search(r"^\s{4}steps:\s*$", bloc, re.M)
    tete = bloc[:fin.start()] if fin else bloc
    return re.search(r"^\s{4}if:", tete, re.M) is not None


def depot_canonique():
    """`owner/repo` du remote `origin`. ⛔ Pas une constante ecrite : un fork
    legitime porte un autre nom, et une constante ferait rougir du travail
    JUSTE. Rend `None` sans remote — le controle est alors DECLARE, ⛔ pas
    saute en silence."""
    r = subprocess.run(["git", "remote", "get-url", "origin"], cwd=RACINE,
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    m = re.search(r"[:/]([\w.-]+/[\w.-]+?)(?:\.git)?\s*$", r.stdout.strip())
    return m.group(1) if m else None


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

    # ── MUTANT 29 : un SECOND workflow qui porte VRAIMENT le signal, et qui
    #    trie AVANT `cla.yml`. ⛔ Rien n'est ecrit sur le disque.
    if _MUTANT == 29:
        workflows.insert(0, ("ci.yml", LEURRE_CLA))

    cla_wf = [(f, w) for f, w in workflows if porte_le_cla(w)]
    cla_wf = [(f, muter_cla(w)) if f == "cla.yml" else (f, w) for f, w in cla_wf]

    dire(promet == bool(cla_wf),
         "la promesse de bot et son workflow disent la meme chose",
         "promesse=%s · workflow(s) CLA=%d"
         % ("oui" if promet else "non", len(cla_wf)))

    if cla_wf:
        # 🔴 TOUS LES WORKFLOWS QUI PORTENT LE SIGNAL SONT AUDITES, ⛔ PAS LE
        #    PREMIER PAR ORDRE ALPHABETIQUE. `cla_wf[0]` faisait dependre trois
        #    garanties du NOM d'un fichier que personne ne controlait.
        canon = depot_canonique()
        flottantes, sans_doc, hors_depot, sans_if, checkouts = [], [], [], [], []
        actions_vues = []
        for nom_wf, wf in cla_wf:
            # ── LA VERSION EST EPINGLEE, ⛔ JAMAIS UN TAG FLOTTANT ─────────
            actions = re.findall(r"uses:\s*([\w.-]+/[\w.-]+)@([\w.-]+)", wf)
            actions_vues += ["%s@%s" % a for a in actions]
            FLOTTANTS = ("main", "master", "latest", "HEAD")
            flottantes += ["%s → %s@%s" % (nom_wf, a, v)
                           for a, v in actions if v in FLOTTANTS]
            if not actions:
                flottantes.append("%s → ⛔ AUCUNE action" % nom_wf)

            # ── LE DOCUMENT A SIGNER EXISTE VRAIMENT, ET IL EST D'ICI ──────
            # 🔴 Un bot qui fait signer un document ABSENT est la promesse creuse
            #    que cette story solde. Et un `blob/<ref>/…` d'un AUTRE depot
            #    resolvait EN LOCAL : le chemin seul ne dit pas d'ou il vient.
            md = re.search(r"path-to-document:\s*['\"]?([^'\"\s]+)", wf)
            if not md:
                sans_doc.append("%s → `path-to-document` absent" % nom_wf)
            else:
                brut = md.group(1)
                mb = re.search(r"blob/[^/]+/(.+)$", brut)
                chemin = mb.group(1) if mb else brut.lstrip("./")
                if not os.path.exists(os.path.join(RACINE, chemin)):
                    sans_doc.append("%s → %s" % (nom_wf, chemin))
                if canon and brut.startswith("http") and canon not in brut:
                    hors_depot.append("%s → %s" % (nom_wf, brut))

            # ── LA CONDITION EST AU NIVEAU DU JOB ─────────────────────────
            if not if_au_niveau_job(wf):
                sans_if.append(nom_wf)

            # ── ⛔ LE CODE DE LA PR N'EST JAMAIS CHECKOUTE ─────────────────
            # `pull_request_target` s'execute avec le jeton du depot de BASE.
            # ⛔ L'ancienne forme ne reconnaissait QU'UNE orthographe
            #    (`github.event.pull_request.head`, a moins de six lignes) :
            #    `github.head_ref` et `refs/pull/N/merge` passaient. L'en-tete du
            #    workflow declare qu'il n'y a DELIBEREMENT aucun `checkout` ⇒ la
            #    propriete controlee est celle-la, et elle n'a pas d'orthographe.
            if re.search(r"uses:\s*actions/checkout@", wf):
                checkouts.append(nom_wf)

        dire(not flottantes, "chaque action du workflow CLA est EPINGLEE",
             " · ".join(actions_vues) if not flottantes
             else "⛔ version FLOTTANTE : " + " ".join(flottantes))

        dire(not sans_doc, "le document que le bot fait signer EXISTE",
             "%d workflow(s) audite(s)" % len(cla_wf) if not sans_doc
             else "⛔ " + " · ".join(sans_doc))

        if canon:
            dire(not hors_depot, "`path-to-document` designe CE depot",
                 "origin = %s" % canon if not hors_depot
                 else "⛔ document HORS depot : " + " · ".join(hors_depot))
        else:
            declarer("⛔ pas de remote `origin` — l'identite du depot ne peut "
                     "pas etre confrontee au lien du document",
                     "`path-to-document` designe CE depot")

        dire(not sans_if, "la condition du workflow CLA est au niveau du JOB",
             "⛔ a l'ETAPE, le runner est ALLOUE et FACTURE" if not sans_if
             else "⛔ condition absente du niveau job : " + " ".join(sans_if))

        dire(not checkouts,
             "⛔ le workflow ne checkoute JAMAIS le code de la PR",
             "`pull_request_target` tourne avec le jeton du depot de BASE"
             if not checkouts
             else "⛔ `actions/checkout` present : " + " ".join(checkouts))
    else:
        declarer("aucun workflow ne porte le signal du CLA "
                 "(`contributor-assistant/` ou `path-to-signatures:`)",
                 *CONDITIONNELS_CLA)

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
    # ⛔ `import pynvml` n'est PAS la seule forme : `from pynvml import …` la
    #    manquait, et le jour ou l'agent gagne NVML sous cette forme la gate
    #    continuerait d'exiger une refutation sur une doc devenue JUSTE.
    a_nvml = re.search(r"^\s*(?:import\s+pynvml|from\s+pynvml\s+import)",
                       agent, re.M) is not None
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
    # 🔴 MESURE DU 2026-09-04 : `--mutant 99` sortait en `28 OK, 0 KO`, `rc=0`,
    #    avec la banniere `[MUTANT 99]`. AC2.6.c exige qu'un mutant qui ne
    #    s'applique pas SORTE EN ERREUR — une campagne pilotee sur une liste
    #    perimee aurait compte un mutant INEXISTANT comme « vu rougir ».
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
    # 🔴 REVUE DU 2026-09-05 — LES MUTANTS DE `CONTRIBUTING.md` N'AVAIENT ⛔ PAS
    #    LA GARDE FATALE QUE 36 ET 38 ONT : si le fichier n'est pas dans la
    #    prose lue, le `if` les SAUTAIT et le mutant tournait **NON MUTE**, en
    #    sortant vert — exactement le silence contre lequel 34/36/38 existent.
    _cm = "CONTRIBUTING.md"
    if _MUTANT in (35, 37, 39, 40) and _cm not in prose:
        sys.exit("MUTANT %d INAPPLICABLE : %s n'est pas dans la prose lue par "
                 "`section_ancrages`. ⛔ Un mutant qui ne s'applique pas ne "
                 "prouve RIEN — c'est la portee qu'il faut regarder."
                 % (_MUTANT, _cm))
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
        # ⚠️ L'ANCRE NE DEPEND PAS DE LA CESURE. Sa 1re version portait le saut
        #    de ligne du paragraphe ; une reformulation l'a decalee et le mutant
        #    est devenu INAPPLICABLE — il l'a DIT, ⛔ il n'est pas passe vert en
        #    silence, et c'est tout l'interet de sortir en erreur.
        prose["CONTRIBUTING.md"] = M(
            14, prose["CONTRIBUTING.md"], "contributor is carried by `dn8`",
            "contributor is carried by `TBD`")
        prose["CONTRIBUTING.md"] = M(
            27, prose["CONTRIBUTING.md"], "and **a bot handles it**",
            "and the maintainer handles it")
        # ⚠️ ANCRES COURTES ET SUR **UNE SEULE LIGNE** — le motif paye par le
        #    mutant 14 : une ancre qui porte la cesure d'un paragraphe devient
        #    INAPPLICABLE des qu'une reformulation la decale.
        prose["CONTRIBUTING.md"] = M(
            35, prose["CONTRIBUTING.md"], "**428 files**", "**429 files**")
        prose["CONTRIBUTING.md"] = M(
            37, prose["CONTRIBUTING.md"],
            "measured on **`76b031a`**", "measured on **`HEAD`**")
        # ⇒ LES DEUX FORKS QUE LE 35 NE TOUCHE PAS : l'unite OCTETS, et la
        #   portee ARBRE ENTIER.
        prose["CONTRIBUTING.md"] = M(
            39, prose["CONTRIBUTING.md"],
            "**10 234 634 bytes**", "**10 234 635 bytes**")
        prose["CONTRIBUTING.md"] = M(
            40, prose["CONTRIBUTING.md"],
            "**46 254 844 bytes**", "**46 254 845 bytes**")
    # 🔴 LE MUTANT 36 MUTE **LA OU LA SECTION LIT** — motif paye par le mutant
    #    34 de `dn5-6` : sa 1re version mutait un dict ou le fichier n'etait
    #    pas, et un `if` la SAUTAIT EN SILENCE ⇒ le mutant sortait VERT en
    #    pretendant prouver quelque chose. Son absence est donc FATALE.
    _rm = "docs/roadmap.md"
    if _MUTANT == 36 and _rm not in prose:
        sys.exit("MUTANT 36 INAPPLICABLE : %s n'est pas dans la prose lue par "
                 "`section_citations`. ⛔ Un mutant qui ne s'applique pas ne "
                 "prouve RIEN — c'est la portee qu'il faut regarder." % _rm)
    if _rm in prose:
        prose[_rm] = M(
            36, prose[_rm],
            "§ *Conventions in this repository*",
            "§ *Conventions that do not exist in that file*")
    # 🔴 LE MUTANT 38 VISE **L'AUTRE MOITIE DE LA FORME**, ET C'EST UNE
    #    LACUNE TROUVEE A LA VERIFICATION DE `dn5-7` : le mutant 36 mute un
    #    renvoi ecrit AVEC son lien markdown. La branche SANS lien (`x.md` nu
    #    suivi de `§ *Titre*`) etait COMPTEE dans les 6 citations mais rien ne
    #    prouvait qu'elle ROUGIT. ⇒ elle a son mutant, sur le meme patron.
    _ep = "docs/dn5-1-ecart-promesses.md"
    if _MUTANT == 38 and _ep not in prose:
        sys.exit("MUTANT 38 INAPPLICABLE : %s n'est pas dans la prose lue par "
                 "`section_citations`. ⛔ Un mutant qui ne s'applique pas ne "
                 "prouve RIEN — c'est la portee qu'il faut regarder." % _ep)
    if _ep in prose:
        prose[_ep] = M(
            38, prose[_ep],
            "§ *Les deux paliers matériels*",
            "§ *Une section qui n'existe pas dans ce fichier*")
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
    # ⇒ dn5-6 / constat (9) : SEULE cette section voit les workflows. Les
    #   textes deja charges (et deja mutes) sont conserves tels quels.
    prose_m = {f: prose.get(f) if f in prose else lire(os.path.join(RACINE, f))
               for f in prose_marqueurs(traces or [])}
    # 🔴 dn5-6 / CONSTAT (9) — LE MUTANT QUI PROUVE QUE LES `.yml` SONT BALAYES.
    # ⚠️ REVUE DU 2026-09-05 : sa 1re version mutait `prose`, ou le workflow
    #    n'est PAS — et un `if _wf in prose:` la SAUTAIT EN SILENCE ⇒
    #    `--mutant 34` sortait **VERT** (`32 OK, 0 KO`) en pretendant prouver
    #    quelque chose. ⛔ Un mutant qui ne s'applique pas ne prouve RIEN.
    # ⇒ IL MUTE LA OU LA SECTION LIT, ET SON ABSENCE EST **FATALE**.
    _wf = ".github/workflows/gates.yml"
    if _MUTANT == 34 and _wf not in prose_m:
        sys.exit("MUTANT 34 INAPPLICABLE : %s n'est pas dans la portee du "
                 "controle des marqueurs. ⛔ Un mutant qui ne s'applique pas ne "
                 "prouve RIEN — c'est la portee qu'il faut regarder." % _wf)
    if _wf in prose_m:
        prose_m[_wf] = M(
            34, prose_m[_wf],
            "\nname: Gates\n",
            "\n# le marqueur `dn9-9` est suivi dans docs/roadmap.md\n"
            "name: Gates\n")
    section_marqueurs(prose_m, roadmap)
    section_comptes(prose)
    section_ancrages(prose)
    section_cla(prose.get("CONTRIBUTING.md", ""), roadmap)
    section_refutations(prose, agent)
    section_auto_coherence(tiers)

    print("\n── (z) LE BILAN NE RETRECIT PAS EN SILENCE ───────────────────────")
    manquants = [l for l in INVENTAIRE
                 if l not in EMIS and l not in DECLARES
                 and l != "tout controle prevu est EMIS ou DECLARE"]
    intrus = [l for l in EMIS if l not in INVENTAIRE and l not in DIAGNOSTICS]
    dire(not manquants and not intrus,
         "tout controle prevu est EMIS ou DECLARE",
         "%d emis + %d declare(s) = %d prevus"
         % (len(EMIS) + 1, len(DECLARES), len(INVENTAIRE))
         if not manquants and not intrus
         else ("⛔ MANQUANT sans declaration : " + " · ".join(manquants[:3])
               if manquants
               else "⛔ EMIS hors inventaire : " + " · ".join(intrus[:3])))

    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (OK[0], KO[0]))
    print("=" * 78)
    return 1 if KO[0] else 0


if __name__ == "__main__":
    sys.exit(main())

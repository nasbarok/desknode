#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn6-4 — LA PLACE DU BOITIER NE PEUT PLUS MENTIR SUR CE QU'ELLE CONTIENT.

======================= CE QUE CETTE GATE FAIT, ET POURQUOI =================

Ce depot PROMETTAIT des plans de boitier a trois endroits — la table de
`LICENSING.md`, sa phrase de repli, et la ligne `dn6` de `docs/roadmap.md` —
et n'en portait AUCUN. Mesure du 2026-09-07 : **0 fichier CAO sur 670 fichiers
suivis** (`.stl` `.3mf` `.step` `.stp` `.f3d` `.scad`). La creation du coffrage
etant rangee APRES la premiere version publique, le dessin n'existera pas de
sitot ⇒ ce qui est livre est **la place, le format, la licence, la notice et
le MANQUE DECLARE**.

Cette gate garde ce constat **DANS LES DEUX SENS**, et c'est la moitie du
sujet :

  · tant qu'aucun plan n'est depose, la page doit le **DIRE** — un dossier
    vide et muet laisserait un lecteur chercher ;
  · le jour ou un plan arrive, la phrase « aucun plan n'est depose » devient
    FAUSSE et la gate **ROUGIT** — et chaque plan depose doit etre CITE.

⇒ elle ne peut donc etre verte ni sur un depot qui se tait, ni sur un depot
  qui a change sans le dire.

── 🔴 ELLE S'ANCRE SUR LES **CHEMINS**, ⛔ JAMAIS SUR LE MOT `boitier` ───────

MESURE DU 2026-09-07 **SUR L'ARBRE D'AVANT CETTE MARCHE** : le mot
`bo[iî]tier` apparaissait **24 fois** dans les **25** `.md` suivis, et **UNE
SEULE** de ces occurrences designait le coffrage (`docs/cablage/PHOTOS.md`).
Les 23 autres etaient :
  · le **ventilateur de boitier** de la telemetrie PC (`CASE_GROUP`) ;
  · des **boitiers de composants** (SOP8, SOIC-8, SC70-6, metallique, optique) ;
  · une collision lexicale deja documentee (`CONTRIBUTING.md`, `entier` /
    `boitier` / `chantier` / `tiers`) ;
  · une ligne BARREE et declaree annulee dans `docs/dn4-15-arbitrage.md`.
⇒ **une gate qui aurait greppe `boitier` ce jour-la aurait ete fausse a 23
  sur 24.** Celle-ci s'ancre sur `docs/boitier/`, sur `docs/boitier.md`, et
  sur des TITRES DE SECTION litteraux.

⚠️ **ET LE COMMIT QUI PUBLIE CETTE PHRASE LA PERIME — c'est ecrit plutot que
   tu.** Les deux pages neuves parlent du coffrage a longueur de ligne : le
   ratio n'est plus celui-la des qu'elles entrent. Le chiffre ci-dessus est
   donc DATE (l'arbre d'avant), et le ratio d'apres est RE-PRIS dans
   `mesures/dn6-4/T7-bornes-arrivee.txt` — ⛔ pas recopie ici, ou il se
   reperimerait au prochain document. Ce que l'argument etablit ne bouge pas :
   le mot est un PIEGE DE MOTIF, et l'ancrage est le CHEMIN.

── 🔴 LE COMPTE SE PREND SUR `git ls-files`, ⛔ PAS SUR L'ARBRE DE TRAVAIL ──

`firmware/` porte **6 726** fichiers `.obj` de compilation, NON SUIVIS. Un
detecteur de plans qui lirait le disque **et** rangerait `.obj` parmi les
formats CAO annoncerait **6 726 plans** la ou il y en a **zero**.
⇒ la population vient de `git ls-files`, et `.obj` ⛔ n'est PAS un format de
  plan dans ce depot. Le temoin negatif est `tools/fixtures/dn64-temoin-obj.obj`
  et il est joue A CHAQUE PASSE, dans les deux sens : il est **VU** (il est
  suivi) et il est **ECARTE** (il n'entre pas en population).

⚠️ POURQUOI CE TEMOIN EST **VERSE AU DEPOT** PLUTOT QUE PRIS DANS `firmware/` :
   les 6 726 `.obj` n'existent PAS dans un clone neuf (le repertoire de build
   est gitignore). Un mutant ancre sur eux serait SANS EFFET en CI — donc
   `rc=3`, mutant PERIME — et `verif_campagne_dn56.py` accuserait la gate.
   Un temoin qui ne survit pas au clone n'est pas un temoin.

── LA MOITIE COCKPIT EST **DECLAREE**, ⛔ JAMAIS UN VERT SILENCIEUX ─────────

Deux controles — (c23) le report au ledger, (c24) la dependance ecrite au
tracker — vivent dans le depot de planification, qui est PRIVE et ⛔ jamais
clone a cote du code. Sans lui, ils ne sont **ni joues ni comptes VERTS** :
ils sont **DECLARES non joues avec leur motif**, et la gate rend `rc=4`
(prerequis absent), ⛔ pas 0.
🔴 ET LE CONTRAT DE `rc` NE BOUGE PAS : un vrai KO trouve dans la moitie jouee
   rend **1** et l'emporte TOUJOURS sur un prerequis absent.

⚠️ LEURS MUTANTS, EUX, JOUENT DANS N'IMPORTE QUEL CLONE — et c'est voulu :
   ils **SUBSTITUENT** un cockpit fautif (un report sans disposition, une
   ligne `epic-dn8` muette) au lieu de muter un fichier absent. Un mutant qui
   dependrait du cockpit serait no-op en CI, donc `rc=3`, donc une campagne
   rouge sur une gate saine. Ce que le mutant prouve est la LOGIQUE du
   controle ; ⛔ ce qu'il ne prouve pas, c'est la lecture du vrai fichier.

── ⛔ CE QU'ELLE NE FAIT PAS, ET C'EST ECRIT PLUTOT QUE PROMIS ──────────────

⛔ **ELLE NE JUGE AUCUN DESSIN.** Ni cote, ni epaisseur de paroi, ni
   imprimabilite : ca demande un TIRAGE, et il n'y en a eu aucun.
⛔ Elle ne MODIFIE aucun fichier : tout est ouvert en LECTURE SEULE et les
   mutants vivent en MEMOIRE.
⛔ Elle ne dit RIEN de la QUALITE d'une notice : qu'un parametre porte une
   disposition ne prouve pas que la disposition soit bonne. Le sens garde est
   qu'elle EXISTE, qu'elle nomme un PORTEUR, et qu'⛔ aucune valeur chiffree
   n'est publiee sans citer la mesure d'ou elle sort.
⛔ Elle ne touche ⛔ ni `hardware/`, ⛔ ni `firmware/`, ⛔ ni le protocole, et
   elle ne reorganise ⛔ aucun element du harnais.

── LA RECIPROQUE EST MECANIQUE, ⛔ PAS TENUE A LA MAIN ─────────────────────

Chaque mutant DECLARE le ou les controles qu'il vise (`CIBLES`), et TROIS
controles finaux confrontent cette table aux identifiants REELLEMENT ecrits
dans la source (lus A L'AST, ⛔ pas dans `ids_emis`, qui est fige au moment de
l'appel) : (c30) aucun controle garde par ZERO mutant · (c31) aucune cible
vers un controle inexistant · (c32) `CIBLES` et `MUTANTS` cle a cle.
⚠️ CE QUE (c30) NE PROUVE PAS : que le mutant rougisse BIEN le controle qu'il
   declare. Ca, c'est la campagne — `mesures/dn6-4/T2`, qui relit les lignes
   de signalement A COLONNE FIXE.

── LA GARDE DU NO-OP EST UNIVERSELLE, ⛔ PAS UNE LISTE D'EXCEPTIONS ────────

🔴 TOUTE mutation passe par un SEUL etat, compare AVANT/APRES. Un mutant
   devenu sans effet — parce que son ancre litterale a bouge — se declare
   lui-meme en `rc=3` (mutant PERIME), ⛔ pas en `rc=1` : `rc=1` + `BILAN` +
   un `[KO ]` est EXACTEMENT ce que `verif_campagne_dn56.py` appelle « sain »,
   et un no-op le remplirait mot pour mot pendant que le controle qu'il garde
   perdrait son seul gardien EN SILENCE.

Sortie : `BILAN : n OK, m KO` · rc 0 vert · 1 vrai defaut · 2 usage ·
         3 mutant PERIME · 4 prerequis (cockpit) absent.
Usage  : python3 tools/verif_boitier_dn64.py [--cockpit CHEMIN]
                                             [--mutant N] [--liste-mutants]

⚠️ **UN MUTANT QUI DEBRANCHE LA GARDE NE PROUVE QUE SON EXISTENCE.** Ceux
   d'ici REPLANTENT la faute REELLE : un plan depose sans que la page le dise,
   un plan range ailleurs que dans sa place, un parametre qui recoit une
   valeur plausible sans source, un repertoire de haut niveau neuf, un report
   sans disposition.
"""

import argparse
import ast
import copy
import os
import re
import subprocess
import sys
import unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGE_REL = "docs/boitier.md"
PLANS_REL = "docs/boitier/PLANS.md"
PLACE = "docs/boitier"
# ⚠️ dn8-4 (2026-09-13) — DELIBEREMENT ⛔ PAS REPOINTE. Ce `README.md` n'est plus le
#    journal francais (parti octet pour octet dans `docs/journal-de-bord.md`) :
#    c'est la VITRINE anglaise. Cette gate continue de la lire parce que ce
#    qu'elle garde — le lien `](docs/boitier.md)` — est la
#    decouvrabilite depuis la page d'accueil, et la vitrine porte ce(s) lien(s)
#    MOT POUR MOT. Repointer sur le journal garderait un lien qu'un inconnu ⛔ ne
#    lit plus en premier.
README_REL = "README.md"
CABLAGE_REL = "docs/cablage.md"
ROADMAP_REL = "docs/roadmap.md"
LICENCE_REL = "LICENSING.md"
CHANGELOG_REL = "CHANGELOG.md"
TEMOIN_OBJ = "tools/fixtures/dn64-temoin-obj.obj"

# Les six formats de plan de ce depot. ⛔ `.obj` N'EN FAIT PAS PARTIE, et c'est
# le temoin negatif ci-dessus qui le prouve a chaque passe.
EXT_CAO = (".stl", ".3mf", ".step", ".stp", ".f3d", ".scad")

# 🔴 UNE BORNE EPINGLEE, ⛔ PAS UNE LISTE DERIVEE D'UN AUTRE FICHIER. Les 9
#    repertoires de 1er niveau mesures le 2026-09-07. `verif_licences_dn52.py`
#    garde deja « tout repertoire de 1er niveau est nomme par LICENSING.md » ;
#    ce controle-ci garde autre chose : qu'AUCUN n'apparaisse. Motif ecrit :
#    la place « evidente » (`cad/`, `plans/`, `enclosure/`) est litteralement
#    le mutant 2 de cette autre gate, et le reflexe se reprend tout seul.
#    ⚠️ C'EST UN ENGAGEMENT : une marche future qui ajoute legitimement un
#       repertoire de 1er niveau DOIT mettre cette table a jour dans le meme
#       geste — et c'est exactement le but, le changement devient un GESTE
#       ECRIT plutot qu'une derive.
#    🆕 **`installeur/` AJOUTE LE 2026-09-08, ET C'EST L'ENGAGEMENT CI-DESSUS
#       QUI S'EXECUTE — ⛔ pas un contournement.** La marche `dn7-1` verse le
#       dossier `installeur/` (le `.bat` a double-cliquer, le serveur local, la
#       page, son identite visuelle), et elle le CLASSE dans `LICENSING.md`
#       **avant** son premier commit, en `GPL-3.0-or-later` : du code qui sert
#       un binaire GPL, ⛔ pas de la prose. Les deux sens de
#       `verif_licences_dn52.py` restent donc verts (34 OK / 0 KO, re-mesure le
#       meme jour). ⛔ La ligne d'origine n'est pas effacee : elle disait « les
#       9 repertoires mesures le 2026-09-07 », et c'est toujours ce qu'elle
#       mesurait ce jour-la. Ils sont **10** depuis le 2026-09-08.
REPERTOIRES_T0 = (".github", "agent", "assets", "docs", "firmware",
                  "hardware", "installeur", "mesures", "tests", "tools")

# La phrase que la page DOIT porter tant que rien n'est depose — et qu'elle
# ⛔ NE PEUT PLUS porter des qu'un plan arrive.
# 🔴 C'EST L'**AFFIRMATION** QUI EST LUE, ⛔ PAS LA PHRASE NUE — ET C'EST UNE
#    MESURE DU 2026-09-07 : les deux pages CITENT aussi cette phrase pour
#    expliquer la regle (« le jour ou un plan arrive, la phrase … devient
#    fausse »). Ancre sur la phrase nue, le mutant 1 effacait l'affirmation et
#    la gate restait VERTE sur la CITATION — un controle qui se satisfait de
#    sa propre glose. ⇒ l'ancre porte le `⇒` et le gras : c'est la POSITION
#    d'assertion, ⛔ pas le vocabulaire.
PHRASE_ZERO = "aucun plan n'est déposé"
AFFIRMATION_ZERO = "⇒ **aucun plan n'est déposé**"

# Les ancres LITTERALES des pages. Une ancre qui bouge rend son mutant PERIME
# (rc=3) ⇒ elle se remarque, ⛔ elle ne pourrit pas en silence.
A_PAS_OBLIGATOIRE = "Aucun boîtier n'est obligatoire"
A_PAS_ESSAYE = "Ce qui n'a PAS été essayé"
A_MANQUE = "Le manque, déclaré — et son porteur"
A_REMESURE = "Comment ces nombres se re-mesurent"
A_ANNOT_DN6 = "deferred past the first public release"
A_LICENCE_DOCS = "enclosure plans"

# Les deux comptes PUBLIES, lus a l'identique dans les DEUX pages.
RE_N_PLACE = re.compile(
    r"plans CAO suivis sous `docs/boitier/` \| \*\*(\d+)\*\*")
RE_N_AILLEURS = re.compile(
    r"plans CAO suivis ailleurs dans le dépôt \| \*\*(\d+)\*\*")

# La notice : quatre parametres, dans cet ordre, chacun avec sa disposition.
PARAMS = ("matériau", "hauteur de couche", "remplissage", "supports")
JETON_NON_MESURE = "non mesuré"
JETON_SOURCE = "mesures/"
# 🔴 UN CHIFFRE DANS LA COLONNE « VALEUR », **AVEC OU SANS UNITE**.
#    ⛔ CE N'EST PLUS UNE LISTE D'UNITES, ET C'EST UNE MESURE : ecrit
#    `\d+…(?:mm|µm|%|°C|g)\b`, le `\b` ne mordait PAS apres `%` (il n'y a pas
#    de frontiere de mot entre `%` et une espace, une virgule ou un `|`) ⇒
#    `20 %`, `20 %,` et `20%` passaient TOUS. Le contre-exemple canonique
#    « PLA, 0,2 mm, 20 %, sans supports » n'y rendait que `0,2 mm` — et le
#    remplissage est justement le parametre qui s'ecrit en `%`. La liste
#    ratait aussi les valeurs NUES (`0,2`, `3 perimetres`).
#    ⇒ la regle est : une valeur PUBLIEE qui porte un chiffre et ⛔ ne cite pas
#      `mesures/` est refusee. L'echappement reste le RENVOI A LA MESURE.
#    ⚠️ La colonne « disposition », elle, n'est ⛔ PAS concernee : elle peut
#      parfaitement citer « 1,6 mm » pour expliquer pourquoi elle ne tranche
#      pas — c'est la case « valeur » qui engage le depot.
RE_VALEUR_CHIFFREE = re.compile(r"\d")
MIN_DISPOSITION = 80      # ce qu'il faut pour qu'une case DISE quelque chose
MIN_PLANS = 1200          # ⛔ un bouchon muet n'est pas une page

RE_PORTEUR = re.compile(r"epic-dn\d+")

# ── LA MOITIE COCKPIT ───────────────────────────────────────────────────────
# ⚠️ `HOME` EST LU COMME LE SHELL LE LIT, avec la MEME valeur de repli que
#    `run_gates.sh` : `expanduser("~")` interroge `/etc/passwd` et rend le
#    vrai foyer meme quand `HOME` est absent (cron, conteneur, `env -i`), ce
#    qui ferait diverger la gate de son lanceur.
COCKPIT_DEFAUT = os.path.join(os.environ.get("HOME") or "/nonexistent",
                              "projects", "compagnon_project")
REL_LEDGER = "_bmad-output/implementation-artifacts/deferred-work.md"
REL_TRACKER = "_bmad-output/implementation-artifacts/sprint-status-desknode.yaml"
A_REPORT = "LA PLACE DU BOITIER EXISTE, LE PLAN N'EXISTE PAS"
# 🔴 LES CINQ VERDICTS ET LES CINQ FORMES DE PORTEUR SONT CELLES QUE LE
#    LEDGER PUBLIE — ⛔ pas un sous-ensemble commode. Mesure : ancre sur
#    `RE_PORTEUR.fullmatch`, (c23) n'acceptait QUE la forme 1 (cle nue) et
#    aurait rougi sur un report PARFAITEMENT CONFORME ecrit en
#    `bloquee par : <fait>` — 12 dispositions du ledger sont dans ce cas.
#    Un controle qui refuse une forme legale fabrique un faux rouge, et le
#    prochain auteur apprendra a ne plus l'employer.
VERDICTS_LEDGER = ("PORTEE", "RE-HEBERGEE", "CLOSE", "BLOQUEE", "CONNAISSANCE")
RE_F2 = re.compile(r"^backlog\s+nomme?\s*:\s*(.+)$", re.I)
RE_F3 = re.compile(r"^bloquee?\s+par\s*:\s*(.+)$", re.I)
RE_F4 = re.compile(r"^clos\s+par\s*:\s*(.{8,})$", re.I)


def sans_accents(x):
    """`PORTÉE` == `PORTEE`, `RE-HÉBERGÉE` == `RE-HEBERGEE`."""
    return "".join(c for c in unicodedata.normalize("NFD", x)
                   if unicodedata.category(c) != "Mn")


def forme_du_porteur(champ):
    """Le NUMERO de la forme declaree, `0` si le champ n'en releve d'AUCUNE.

    ⛔ `0` n'est pas un repli silencieux vers « cle nue » : c'est un KO."""
    t = re.sub(r"[`*_]", "", sans_accents(champ)).strip()
    if RE_F2.match(t):
        return 2
    if RE_F3.match(t):
        return 3
    if RE_F4.match(t):
        return 4
    if t.strip("—–-. ") == "":
        return 5
    return 1 if re.fullmatch(r"(?:dn\d+-\d+(?:-[\w.]+)*"
                             r"|epic-dn\d+(?:-[\w.]+)*)", t, re.I) else 0


def corps_du_commentaire(ligne):
    """Le COMMENTAIRE d'une ligne YAML — ⛔ jamais la cle qui la commence.

    🔴 MESURE : `(c24)` cherchait son porteur dans la ligne ENTIERE, qui
       commence par `epic-dn8:` ⇒ `RE_PORTEUR` matchait TOUJOURS, la
       conjonction « porteur » ne pouvait ⛔ jamais etre fausse, et sa branche
       d'echec etait INATTEIGNABLE. Une ligne portant le boitier et le
       re-tournage SANS aucun porteur passait `28 OK, 0 KO`."""
    return ligne.split("#", 1)[1] if "#" in ligne else ligne.split(":", 1)[-1]


RE_DISPO = re.compile(
    r"⇒\s*\[([A-Za-z][\w.\-]*)\s+(\d{4}-\d{2}-\d{2})\]\s*"
    r"([A-ZÀ-ÿ\-]+)\s*·\s*porteur\s*:\s*(.*?)\s*·\s*preuve\s*:\s*(.+)")
RC_PREREQUIS = 4

LARGEUR_LIBELLE = 58   # la colonne de `ctrl()` — la cle que `T2` relit

ok_total = [0]
ko_total = [0]
ids_emis = []
_PREVUS = [0]

MUTANTS = {}                    # ⛔ AU NIVEAU MODULE — sinon `--liste-mutants`
CIBLES = {}                     # ⛔ AU NIVEAU MODULE — matiere de (c30)

MUTANTS[1] = ("efface de la page la phrase « aucun plan n'est depose » : le "
              "depot se tait sur son propre vide")
CIBLES[1] = ("c5",)
MUTANTS[2] = ("DEPOSE un plan CAO suivi sous `docs/boitier/` ⇒ la phrase "
              "« aucun plan » devient FAUSSE, et nul ne cite le plan")
CIBLES[2] = ("c4", "c5", "c6", "c8")
MUTANTS[3] = ("depose un plan CAO suivi HORS de la place (`assets/`) : la "
              "place existe pour etre utilisee")
CIBLES[3] = ("c4", "c5", "c6", "c7")
MUTANTS[4] = ("compte les plans sur l'ARBRE DE TRAVAIL et range `.obj` en "
              "CAO — la faute qui rendrait 6 726 plans pour zero")
CIBLES[4] = ("c9", "c4", "c5", "c6", "c7")
MUTANTS[5] = ("vide la case « valeur » du parametre « materiau » : il est "
              "liste, il ne dit plus rien")
CIBLES[5] = ("c10",)
MUTANTS[6] = ("donne a « hauteur de couche » une valeur PLAUSIBLE et SANS "
              "SOURCE (`0,2 mm`) — le defaut que la marche existe pour eviter")
CIBLES[6] = ("c11", "c14")
MUTANTS[7] = ("vide la DISPOSITION de « remplissage » : la case est vide et "
              "plus personne ne dit pourquoi")
CIBLES[7] = ("c12",)
MUTANTS[8] = ("retire du tableau la ligne entiere de « supports »")
CIBLES[8] = ("c13",)
MUTANTS[9] = ("retire la section « ce qui n'a PAS ete essaye » — la moitie "
              "utile de la notice")
CIBLES[9] = ("c15",)
MUTANTS[10] = ("retire le porteur du manque declare : il reste un constat "
               "sans personne pour le porter")
CIBLES[10] = ("c16",)
MUTANTS[11] = ("efface « Aucun boitier n'est obligatoire » ⇒ la page laisse "
               "croire que le coffrage conditionne le fonctionnement")
CIBLES[11] = ("c17",)
MUTANTS[12] = ("retire la section qui dit comment les nombres se re-mesurent")
CIBLES[12] = ("c18",)
MUTANTS[13] = ("efface la licence de la page : les plans arriveraient sans "
               "regime de reutilisation ecrit")
CIBLES[13] = ("c19",)
MUTANTS[14] = ("retire le lien du README vers la page ⇒ elle devient "
               "INVISIBLE depuis la porte d'entree")
CIBLES[14] = ("c20",)
MUTANTS[15] = ("retire le renvoi de `docs/cablage.md` vers la page")
CIBLES[15] = ("c20",)
MUTANTS[16] = ("retire de `docs/roadmap.md` la ligne du marqueur cite par la "
               "page ⇒ un renvoi qui ne se resout plus")
CIBLES[16] = ("c21",)
MUTANTS[17] = ("retire l'entree de `CHANGELOG.md` : le depot livre sans le "
               "dire")
CIBLES[17] = ("c22",)
MUTANTS[18] = ("reduit `PLANS.md` a un BOUCHON MUET — le `.gitkeep` deguise "
               "que cette marche refuse, qui ne publie plus AUCUN compte")
CIBLES[18] = ("c2", "c6")
MUTANTS[19] = ("vide la page du boitier")
CIBLES[19] = ("c1",)
MUTANTS[20] = ("fait entrer un REPERTOIRE DE 1er NIVEAU NEUF dans l'arbre — "
               "le reflexe `plans/`, qui est un mutant d'une autre gate")
CIBLES[20] = ("c3",)
MUTANTS[21] = ("fait MENTIR la page sur le nombre de plans deposes")
CIBLES[21] = ("c4",)
MUTANTS[22] = ("SUBSTITUE un ledger ou le report du boitier n'a AUCUNE ligne "
               "de disposition — un report sans porteur meurt en silence")
CIBLES[22] = ("c23",)
MUTANTS[23] = ("SUBSTITUE un tracker ou la ligne `epic-dn8` ne dit RIEN du "
               "boitier ni du re-tournage — l'etat mesure avant la marche")
CIBLES[23] = ("c24",)
MUTANTS[24] = ("vide les CIBLES du mutant qui garde SEUL un controle ⇒ ce "
               "controle n'est plus garde par personne")
CIBLES[24] = ("c30",)
MUTANTS[25] = ("fait viser a un mutant un controle INEXISTANT")
CIBLES[25] = ("c31",)
MUTANTS[26] = ("declare une cible pour un mutant qui N'EXISTE PAS")
CIBLES[26] = ("c32",)
MUTANTS[27] = ("fait SAUTER le bloc de la notice ⇒ la gate joue MOINS de "
               "controles qu'annonce, et sort verte sur une population "
               "retrecie")
CIBLES[27] = ("z",)
MUTANTS[28] = ("LEVE volontairement : c'est la faute « un mutant declare qui "
               "MEURT », qui doit rendre un BILAN et ⛔ pas un Traceback")
CIBLES[28] = ("c0",)
MUTANTS[29] = ("efface de `docs/roadmap.md` l'annotation qui range le "
               "coffrage apres la premiere version publique")
CIBLES[29] = ("c25",)
MUTANTS[30] = ("fait diverger `PLANS.md` de la mesure sur le nombre de plans")
CIBLES[30] = ("c6",)
MUTANTS[31] = ("depose un plan dont le NOM EST ACCENTUE — le chemin que "
               "`git ls-files` rendait ECHAPPE, donc invisible")
CIBLES[31] = ("c4", "c5", "c6", "c8")
MUTANTS[32] = ("SUBSTITUE un tracker ou `epic-dn8` nomme le boitier ET le "
               "re-tournage mais AUCUN porteur")
CIBLES[32] = ("c24",)
MUTANTS[33] = ("depose sous la place un format CAO HORS LISTE (`.dxf`) : il "
               "n'est ni compte, ni refuse, et `PLANS.md` l'interdit")
CIBLES[33] = ("c26",)
MUTANTS[34] = ("glisse un POURCENTAGE dans une valeur qui garde le jeton "
               "« non mesure » — la forme qui passait les DEUX controles")
CIBLES[34] = ("c14",)
MUTANTS[35] = ("retire la CLE d'epic d'une disposition en la laissant "
               "longue : « Porteur : a nommer » n'est PAS un porteur")
CIBLES[35] = ("c13",)

# ⚠️ LE COMPTE DU CHEMIN NORMAL, hors le controle final qui le confronte. Il
#    se PERIME si on ajoute un controle sans le mettre a jour — et c'est
#    voulu : c'est ce qui rend (z) FALSIFIABLE.
CONTROLES_PREVUS = 29
CONTROLES_COCKPIT = ("c23", "c24")

_MUTANT = 0

RE_ID_CTRL = re.compile(r"\((\w+)\)")


def ctrl(ok, libelle, detail=""):
    """UNE assertion, UNE ligne, UN identifiant. ⛔ Aucun controle muet.

    ⚠️ L'IDENTIFIANT VIT DANS LE LIBELLE, ⛔ pas dans un argument a part :
       `verif_campagne_dn56.py` lit les libelles A L'AST en prenant `args[1]`
       de chaque `ctrl(...)`. Une signature `ctrl(cid, ok, libelle)` mettrait
       le booleen en `args[1]` et retrecirait SILENCIEUSEMENT la population de
       cette gate-la. ⛔ Une gate ne retrecit pas l'instrument d'une autre.
    ⚠️ Le libelle est imprime a COLONNE FIXE (58) : c'est la cle que la
       campagne de `mesures/dn6-4/T2` relit pour attribuer chaque signalement
       a son controle."""
    assert len(libelle) <= LARGEUR_LIBELLE, (
        "libelle de %d colonnes (max %d) : %r"
        % (len(libelle), LARGEUR_LIBELLE, libelle))
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
    discriminant que `verif_campagne_dn56.py` exige de chaque mutant.

    ⚠️ DEUX SORTIES NE PASSENT PAS ICI, ET C'EST ECRIT PLUTOT QUE PROMIS :
       · `--liste-mutants`, qui n'emet AUCUN controle et ne rend AUCUN
         verdict ;
       · `sys.exit(\"MUTANT %d INCONNU\")`, qui est une ERREUR D'APPEL."""
    emis = ok_total[0] + ko_total[0]
    if not anticipee and emis != _PREVUS[0]:
        ctrl(False, "(z) tout controle prevu est EMIS",
             "⛔ %d emis pour %d prevus — une gate qui joue MOINS de controles "
             "qu'annonce sort VERTE sur une population RETRECIE, ⛔ sans le "
             "declarer" % (emis, _PREVUS[0]))
        rc = 1
    print("\n" + "=" * 78)
    if anticipee:
        print("⛔ SORTIE ANTICIPEE — %d controle(s) emis sur %d prevus : %s"
              % (ok_total[0] + ko_total[0], _PREVUS[0], anticipee))
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return rc


# 🔴 LE CONTRAT DE `rc` NE BOUGE PAS, LA CI EN DEPEND : un vrai KO rend 1 et
#    l'emporte ; sinon, cockpit absent rend 4. Ecrit dans UNE fonction pour que
#    la phrase imprimee SORTE de la regle, ⛔ ne la commente pas.
def regle_rc(ko, cockpit_absent):
    if ko:
        return 1, ("⛔ rc=1 : un KO a ete trouve dans la moitie jouee — un vrai"
                   " defaut l'emporte TOUJOURS sur un prerequis absent.")
    if cockpit_absent:
        return RC_PREREQUIS, (
            "⛔ rc=%d (prerequis) des que le cockpit manque ET qu'aucun KO n'a"
            " ete trouve." % RC_PREREQUIS)
    return 0, "rc=0 : cockpit atteignable, aucun KO."


# ═══════════════════════════ LIRE LE DEPOT ═════════════════════════════════

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
    """Les identifiants de TOUS les `ctrl(...)` de CE fichier, lus A L'AST.

    🔴 POURQUOI PAS `set(ids_emis)` : ce set est fige AU MOMENT DE L'APPEL de
       (c30). Tout controle ajoute APRES ce bloc en sortait INVISIBLE a la
       reciproque — et les controles de cockpit, non emis quand le cockpit
       manque, en sortiraient AUSSI. ⛔ Rend `None` si la source ne s'analyse
       pas : (c30) en fait un KO NOMME, ⛔ pas un vert par defaut."""
    try:
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            arbre_ast = ast.parse(fh.read())
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    out = set()
    for n in ast.walk(arbre_ast):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "ctrl" and len(n.args) >= 2):
            m = RE_ID_CTRL.match(_texte_litteral(n.args[1]) or "")
            if m:
                out.add(m.group(1))
    return out or None


def suivis():
    """Les fichiers TRACES, par `git ls-files`. ⛔ Pas un parcours du disque :
    un repertoire ignore n'est pas du depot. Rend `None` si git refuse.

    🔴 `core.quotePath=false` ET `-z` NE SONT ⛔ PAS DU CONFORT — ET LE DEPOT
       EST FRANCOPHONE. Par defaut `git ls-files` ECHAPPE tout chemin non
       ASCII et l'entoure de guillemets :
         `"docs/boitier/coffrage-bo\303\256tier.stl"`
       Ce jeton ⛔ ne finit PAS par `.stl` ⇒ `plans_de()` le rate, (c4) (c5)
       (c7) (c8) restent VERTS, et la page continue de dire « aucun plan n'est
       depose » alors qu'un plan EST depose. Un nom de plan accentue est
       ORDINAIRE ici : c'est le second sens d'`AC-G1` qui tombait.
       ⇒ `-z` separe au NUL, ce qui rend aussi un nom contenant un retour a la
         ligne — que `splitlines()` aurait coupe en deux."""
    try:
        r = subprocess.run(["git", "-c", "core.quotePath=false",
                            "ls-files", "-z"], cwd=RACINE,
                           capture_output=True, text=True)
    except OSError:
        return None
    if r.returncode != 0:
        return None
    return sorted(x for x in r.stdout.split("\0") if x.strip())


def sur_le_disque():
    """Tous les fichiers de l'arbre de travail — ⛔ CE N'EST PAS LE DEPOT.
    Il n'existe que pour que le mutant 4 puisse REPLANTER la faute mesuree."""
    out = []
    for base, dirs, fichiers in os.walk(RACINE):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in fichiers:
            out.append(os.path.relpath(os.path.join(base, f), RACINE))
    return sorted(out)


def plans_de(etat):
    """La population des plans, DERIVEE DES REGLES — ⛔ pas codee en dur."""
    r = etat["regles"]
    base = etat["arbre"] if r["source"] == "suivis" else etat["disque"]
    ext = tuple(r["ext"])
    return sorted(p for p in base if p.lower().endswith(ext))


def lit(rel):
    try:
        with open(os.path.join(RACINE, rel), encoding="utf-8",
                  errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def lit_hors(chemin):
    try:
        with open(chemin, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def cellules(ligne):
    """Les cases d'une ligne de table markdown."""
    l = ligne.strip()
    if l.startswith("|"):
        l = l[1:]
    if l.endswith("|"):
        l = l[:-1]
    return [c.strip() for c in l.split("|")]


def tables(texte):
    """`[(entete, [ligne_de_corps])]` — les tables markdown du texte."""
    out, lignes = [], texte.split("\n")
    i = 0
    while i < len(lignes) - 1:
        if lignes[i].strip().startswith("|") and re.match(
                r"^\s*\|[\s:|-]+\|\s*$", lignes[i + 1]):
            ent, corps, j = cellules(lignes[i]), [], i + 2
            while j < len(lignes) and lignes[j].strip().startswith("|"):
                corps.append(lignes[j])
                j += 1
            out.append((ent, corps))
            i = j
        else:
            i += 1
    return out


def colonne(entete, mot):
    """L'indice de la colonne dont l'intitule contient `mot`. ⛔ Pas une
    position codee en dur : une colonne inseree ne doit pas decaler la
    lecture EN SILENCE."""
    for k, c in enumerate(entete):
        if mot in c.lower():
            return k
    return None


def table_notice(page):
    """La table de la notice — reconnue par SES INTITULES, ⛔ pas par son rang.

    ⚠️ La page porte TROIS tables (l'etat mesure, la notice, le manque). Les
       reperer par leur position les melangerait au premier ajout."""
    for ent, corps in tables(page):
        if (colonne(ent, "paramètre") is not None
                and colonne(ent, "valeur") is not None
                and colonne(ent, "disposition") is not None):
            return ent, corps
    return None, []


def table_manque(page):
    for ent, corps in tables(page):
        if (colonne(ent, "qui le porte") is not None
                and colonne(ent, "manque") is not None):
            return ent, corps
    return None, []


def bloc_section(texte, ancre):
    """Le corps de la section dont le TITRE contient `ancre`. ⛔ Rend `\"\"` si
    le titre n'existe pas — une section absente est un fait, ⛔ pas une
    exception."""
    lignes = texte.split("\n")
    debut = None
    for i, l in enumerate(lignes):
        if l.startswith("#") and ancre in l:
            debut = i
            break
    if debut is None:
        return ""
    for j in range(debut + 1, len(lignes)):
        if lignes[j].startswith("## "):
            return "\n".join(lignes[debut:j])
    return "\n".join(lignes[debut:])


def liens_de(texte):
    return [m.group(1) for m in re.finditer(r"\]\(([^)]+)\)", texte)]


def comptes_publies(texte):
    """`(n_place, n_ailleurs)` tels que la page les PUBLIE — `None` si absent."""
    plat = re.sub(r"\s+", " ", texte)
    a = RE_N_PLACE.search(plat)
    b = RE_N_AILLEURS.search(plat)
    return (int(a.group(1)) if a else None,
            int(b.group(1)) if b else None)


def dispo_du_report(ledger):
    """La ligne de disposition du report du boitier — `None` si absente."""
    i = ledger.find(A_REPORT)
    if i < 0:
        return None
    m = RE_DISPO.search(ledger[i:i + 3000])
    return m.groups() if m else None


def ligne_epic_dn8(tracker):
    for l in tracker.split("\n"):
        if re.match(r"\s*epic-dn8\s*:", l):
            return l
    return ""


# ═══════════════════ LES FAUX COCKPITS DES MUTANTS 22 ET 23 ════════════════
# 🔴 ILS SUBSTITUENT, ⛔ ILS NE MUTENT PAS UN FICHIER ABSENT. Un mutant qui
#    dependrait du cockpit serait SANS EFFET dans un clone neuf ⇒ `rc=3`, et
#    `verif_campagne_dn56.py` — qui tourne en CI — accuserait cette gate d'un
#    mutant perime alors qu'elle est saine. Ce qu'ils prouvent est la LOGIQUE
#    de (c23)/(c24) ; ⛔ ce qu'ils ne prouvent pas, c'est la lecture du vrai
#    fichier, et c'est ecrit plutot que promis.
LEDGER_SANS_DISPOSITION = """
## Deferred from: dn6-4 — faux ledger du mutant 22 (⛔ pas le vrai)

- 🔴 **[DeskNode] %s**
  Le report est ecrit, il decrit le manque, et il ⛔ N'A AUCUNE LIGNE DE
  DISPOSITION : ni verdict, ni porteur, ni preuve. C'est exactement la faute
  mesuree a `epic-dn6` — 14 reports ecrits, 0 arrive au ledger.
""" % A_REPORT

TRACKER_MUET = """
  epic-dn7: backlog  # (faux tracker du mutant 23)
  epic-dn8: backlog  # LA VITRINE, LA RELEASE, ET DE QUOI RECEVOIR. Porte : le
    README scinde, le tag, les templates d'issues. ⛔ RIEN sur le coffrage.
"""

# ⚠️ LES DEUX MOITIES SAINES SONT FOURNIES AVEC, ET C'EST DELIBERE : un mutant
#    qui ne substituerait QUE sa moitie fautive laisserait l'autre a "" quand
#    le cockpit manque, et ferait rougir DEUX controles au lieu d'un. Sa cible
#    declaree dependrait alors de la machine — or « la cible declaree dit ce
#    que le mutant FAIT ». ⇒ chaque mutant pose un cockpit COMPLET avec
#    EXACTEMENT une faute.
LEDGER_BON = """
## Deferred from: dn6-4 — faux ledger SAIN (⛔ pas le vrai)

- 🔵 **[DeskNode] %s**
  Le meme report, avec sa ligne de disposition.
  ⇒ [dn6-4 2026-09-07] PORTÉE · porteur : epic-dn6 · preuve : moitie saine du
  faux cockpit des mutants — ⛔ ce n'est PAS le vrai ledger.
""" % A_REPORT

# ⚠️ **UNE SEULE LIGNE, ET C'EST LE SUJET** : le tracker est un YAML dont
#    chaque cle tient sur UNE ligne, et (c24) lit CETTE ligne. Ecrit sur deux
#    lignes, ce faux cockpit SAIN faisait rougir (c24) — le mutant 22 visait
#    alors DEUX controles au lieu d'un, et sa cible declaree devenait fausse.
# ⚠️ IL PORTE LE BOITIER **ET** LE RE-TOURNAGE, ET ⛔ AUCUNE cle d'epic : c'est
#    la seule facon de faire tomber la TROISIEME conjonction de (c24) toute
#    seule. Ecrite sur la ligne ENTIERE, elle etait INATTEIGNABLE.
TRACKER_SANS_PORTEUR = (
    "\n  epic-dn8: backlog  # (faux tracker du mutant 32) le boitier "
    "CONDITIONNE le re-tournage media. ⛔ Personne ne porte l'arbitrage.\n")

TRACKER_BON = (
    "\n  epic-dn8: backlog  # (faux tracker SAIN) le boitier CONDITIONNE le "
    "re-tournage media ⇒ dependance vers `dn6`, porteur `epic-dn8`.\n")


def muter(etat):
    """REPLANTE une faute DANS L'ETAT — ⛔ jamais dans un fichier du depot."""
    e = copy.deepcopy(etat)
    p, r = e["prose"], e["regles"]

    if _MUTANT == 1:
        p[PAGE_REL] = p[PAGE_REL].replace(
            "⇒ **aucun plan n'est déposé**. La place est prête",
            "⇒ la place est prête")
    elif _MUTANT == 2:
        e["arbre"].append("docs/boitier/desknode-coffrage-v1.stl")
        e["disque"].append("docs/boitier/desknode-coffrage-v1.stl")
    elif _MUTANT == 3:
        e["arbre"].append("assets/coffrage-desknode.stl")
        e["disque"].append("assets/coffrage-desknode.stl")
    elif _MUTANT == 4:
        r["source"] = "disque"
        r["ext"] = tuple(r["ext"]) + (".obj",)
    elif _MUTANT == 5:
        p[PAGE_REL] = p[PAGE_REL].replace(
            "| **matériau** | ⛔ **non mesuré** |", "| **matériau** |  |")
    elif _MUTANT == 6:
        p[PAGE_REL] = p[PAGE_REL].replace(
            "| **hauteur de couche** | ⛔ **non mesuré** |",
            "| **hauteur de couche** | 0,2 mm |")
    elif _MUTANT == 7:
        p[PAGE_REL] = re.sub(
            r"(?m)^(\| \*\*remplissage\*\* \|[^|]*\|)[^|]*\|",
            r"\1  |", p[PAGE_REL])
    elif _MUTANT == 8:
        p[PAGE_REL] = re.sub(r"(?m)^\| \*\*supports\*\* \|.*\n", "",
                             p[PAGE_REL])
    elif _MUTANT == 9:
        p[PAGE_REL] = p[PAGE_REL].replace(A_PAS_ESSAYE, "Quelques remarques")
    elif _MUTANT == 10:
        p[PAGE_REL] = p[PAGE_REL].replace(
            "porteur : `epic-dn6` — le territoire matériel, `backlog` au "
            "2026-09-07", "porteur à nommer")
    elif _MUTANT == 11:
        p[PAGE_REL] = p[PAGE_REL].replace(A_PAS_OBLIGATOIRE,
                                          "Le boîtier de DeskNode")
    elif _MUTANT == 12:
        p[PAGE_REL] = p[PAGE_REL].replace(A_REMESURE, "Pour aller plus loin")
    elif _MUTANT == 13:
        p[PAGE_REL] = p[PAGE_REL].replace("CC-BY-SA-4.0", "sous licence")
    elif _MUTANT == 14:
        p[README_REL] = p[README_REL].replace("](docs/boitier.md)",
                                              "](le dossier du boîtier)")
    elif _MUTANT == 15:
        p[CABLAGE_REL] = p[CABLAGE_REL].replace("](boitier.md)",
                                                "](la page du boîtier)")
    elif _MUTANT == 16:
        p[ROADMAP_REL] = re.sub(r"(?m)^\| `dn6-4` \|.*\n", "", p[ROADMAP_REL])
    elif _MUTANT == 17:
        p[CHANGELOG_REL] = p[CHANGELOG_REL].replace(
            "[`docs/boitier.md`](docs/boitier.md)", "la page du boîtier")
    elif _MUTANT == 18:
        p[PLANS_REL] = "# Plans\n\nRien pour l'instant.\n"
    elif _MUTANT == 19:
        p[PAGE_REL] = ""
    elif _MUTANT == 20:
        e["arbre"].append("plans/coffrage-a-imprimer.txt")
        e["disque"].append("plans/coffrage-a-imprimer.txt")
    elif _MUTANT == 21:
        p[PAGE_REL] = p[PAGE_REL].replace(
            "| plans CAO suivis sous `docs/boitier/` | **0** |",
            "| plans CAO suivis sous `docs/boitier/` | **7** |")
    elif _MUTANT == 22:
        e["cockpit_absent"] = False
        e["ledger"] = LEDGER_SANS_DISPOSITION
        e["tracker"] = TRACKER_BON
    elif _MUTANT == 23:
        e["cockpit_absent"] = False
        e["ledger"] = LEDGER_BON
        e["tracker"] = TRACKER_MUET
    elif _MUTANT == 24:
        # ⚠️ LA VICTIME EST **DERIVEE**, ⛔ pas codee en dur : viser un mutant
        #    par son numero cesse de marcher le jour ou son controle gagne un
        #    SECOND gardien. On cherche un controle garde par EXACTEMENT UN
        #    mutant, et on vide CE gardien-la.
        compte = {}
        for _n, _v in e["cibles"].items():
            for _c in _v:
                compte[_c] = compte.get(_c, 0) + 1
        for _n, _v in sorted(e["cibles"].items()):
            if any(compte[_c] == 1 for _c in _v):
                e["cibles"][_n] = ()
                break
    elif _MUTANT == 25:
        e["cibles"][25] = tuple(e["cibles"][25]) + ("c99",)
    elif _MUTANT == 26:
        e["cibles"][99] = ("c9",)      # une cible pour un mutant INEXISTANT
    elif _MUTANT == 27:
        r["sortie_anticipee"] = True
    elif _MUTANT == 28:
        # 🔴 IL LEVE EXPRES : c'est la faute « un mutant declare qui MEURT ».
        #    `main()` la rattrape et rend un `BILAN` — sans ce rattrapage, la
        #    gate sortirait en Traceback NU, indiscernable d'une gate morte.
        raise AssertionError("mutant 28 : corps volontairement LEVANT")
    elif _MUTANT == 29:
        p[ROADMAP_REL] = p[ROADMAP_REL].replace(A_ANNOT_DN6,
                                                "planned for later")
    elif _MUTANT == 31:
        # ⚠️ NOM ACCENTUE : `git ls-files` SANS `core.quotePath=false` rend
        #    `"docs/boitier/coffrage-bo\303\256tier-v1.stl"` — un jeton qui
        #    ⛔ ne finit PAS par `.stl`. Le plan devenait INVISIBLE et les
        #    quatre controles restaient VERTS sur un depot qui ment.
        cible = "docs/boitier/coffrage-boîtier-v1.stl"
        e["arbre"].append(cible)
        e["disque"].append(cible)
    elif _MUTANT == 32:
        e["cockpit_absent"] = False
        e["ledger"] = LEDGER_BON
        e["tracker"] = TRACKER_SANS_PORTEUR
    elif _MUTANT == 33:
        cible = "docs/boitier/coffrage.dxf"
        e["arbre"].append(cible)
        e["disque"].append(cible)
    elif _MUTANT == 34:
        p[PAGE_REL] = p[PAGE_REL].replace(
            "| **remplissage** | ⛔ **non mesuré** |",
            "| **remplissage** | ⛔ **non mesuré** (≈ 20 % attendu) |")
    elif _MUTANT == 35:
        p[PAGE_REL] = re.sub(
            r"(?m)^(\| \*\*supports\*\* \|.*?)Porteur : `epic-dn6`\.",
            r"\1Porteur : a nommer, personne pour l'instant.", p[PAGE_REL])
    elif _MUTANT == 30:
        p[PLANS_REL] = p[PLANS_REL].replace(
            "| plans CAO suivis ailleurs dans le dépôt | **0** |",
            "| plans CAO suivis ailleurs dans le dépôt | **3** |")
    else:
        raise AssertionError("mutant %d declare mais SANS CORPS" % _MUTANT)
    return e


# ═══════════════════════════ LES CONTROLES ═════════════════════════════════

def main():
    global _MUTANT
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--cockpit", default=COCKPIT_DEFAUT,
                    help="racine du depot de planification. ⛔ S'IL EST "
                         "ABSENT la gate le DECLARE et rend 4 — ⛔ jamais un "
                         "skip silencieux")
    ap.add_argument("--mutant", type=int, default=None,
                    help="REPLANTE une faute EN MEMOIRE pour prouver que le "
                         "controle correspondant sait ROUGIR")
    ap.add_argument("--liste-mutants", action="store_true",
                    help="dit ce que chaque mutant replante, et sort")
    args = ap.parse_args()
    if args.mutant is not None and args.mutant not in MUTANTS:
        sys.exit("MUTANT %d INCONNU : il n'est pas declare. ⛔ Un mutant qui "
                 "n'existe pas ne prouve RIEN — ⛔ ne pas conclure que le "
                 "controle est vert." % args.mutant)
    _MUTANT = args.mutant or 0

    if args.liste_mutants:
        for n in sorted(MUTANTS):
            print("  %2d  %s" % (n, MUTANTS[n]))
        return 0

    print("=" * 78)
    print("dn6-4 — LA PLACE DU BOITIER NE PEUT PLUS MENTIR SUR SON CONTENU"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)
    print("cible      : %s/  +  %s" % (PLACE, PAGE_REL))
    print("⛔ CETTE GATE NE JUGE AUCUN DESSIN — ni cote, ni epaisseur, ni "
          "imprimabilite.\n   Ca demande un TIRAGE, et il n'y en a eu AUCUN.")

    # ── la matiere ─────────────────────────────────────────────────────────
    _PREVUS[0] = CONTROLES_PREVUS
    arbre = suivis()
    if arbre is None:
        ctrl(False, "(c0) l'arbre trace est LISIBLE",
             "⛔ `git ls-files` a refuse — ⛔ pas de parcours de disque en "
             "remplacement : un repertoire ignore n'est pas du depot")
        return bilan(1, "l'arbre trace est illisible")

    cockpit_absent = not os.path.isdir(args.cockpit)
    prose = {}
    for rel in (PAGE_REL, PLANS_REL, README_REL, CABLAGE_REL, ROADMAP_REL,
                LICENCE_REL, CHANGELOG_REL):
        prose[rel] = lit(rel)

    etat = {"prose": prose,
            "arbre": arbre,
            "disque": sur_le_disque(),
            "ledger": "" if cockpit_absent
                      else lit_hors(os.path.join(args.cockpit, REL_LEDGER)),
            "tracker": "" if cockpit_absent
                       else lit_hors(os.path.join(args.cockpit, REL_TRACKER)),
            "cockpit_absent": cockpit_absent,
            "cibles": {n: tuple(v) for n, v in CIBLES.items()},
            "regles": {"ext": EXT_CAO, "source": "suivis",
                       "sortie_anticipee": False}}

    # 🔴 UN MUTANT QUI MEURT SORTIRAIT EN TRACEBACK, SANS `BILAN` — or « pas
    #    de BILAN » est le discriminant d'une gate MORTE. ⇒ il se rend en KO.
    try:
        neuf = muter(etat) if _MUTANT else etat
    except Exception as exc:                              # noqa: BLE001
        ctrl(False, "(c0) le mutant %d a une CIBLE et un CORPS" % _MUTANT,
             "⛔ %s: %s — la faute est dans le MUTANT, ⛔ pas dans la gate"
             % (type(exc).__name__, str(exc)[:80]))
        return bilan(1, "le mutant %d n'a pas pu s'appliquer" % _MUTANT)
    # 🔴 UN MUTANT SANS EFFET EST INVISIBLE AU CONTRAT DE LA CAMPAGNE : le
    #    jour ou son ancre litterale bouge, la gate sort VERTE et la campagne
    #    accuse LA GATE. ⇒ il se declare lui-meme, et en `rc=3`.
    if _MUTANT and neuf == etat:
        ctrl(False, "(c0) le mutant %d a bien un EFFET" % _MUTANT,
             "⛔ SANS EFFET — son ancre litterale a disparu de la cible. "
             "⛔ Ce n'est PAS un controle vert : rc=3, mutant PERIME.")
        return bilan(3, "le mutant %d n'a eu aucun effet" % _MUTANT)

    prose = neuf["prose"]
    cibles, regles = neuf["cibles"], neuf["regles"]
    cockpit_absent = neuf["cockpit_absent"]
    if cockpit_absent:
        _PREVUS[0] = CONTROLES_PREVUS - len(CONTROLES_COCKPIT)
    page = prose[PAGE_REL]
    plans_pl = prose[PLANS_REL]

    # ── (c1)(c2) LES DEUX PAGES EXISTENT ET DISENT QUELQUE CHOSE ───────────
    print("\n── (c1)(c2) LA PLACE EST PEUPLEE, ET ELLE PARLE ──────────────────")
    if not ctrl(bool(page.strip()), "(c1) la page du boitier n'est pas vide",
                "%d caractere(s)" % len(page) if page.strip()
                else "⛔ `%s` est VIDE ou ABSENTE — ⛔ un vide n'est pas une "
                     "absence de defaut" % PAGE_REL):
        return bilan(1, "la page du boitier est VIDE")
    manquantes = [x for x in EXT_CAO if x not in plans_pl]
    assez = len(plans_pl) >= MIN_PLANS
    ctrl(assez and not manquantes,
         "(c2) `PLANS.md` DIT ce qui se depose, ⛔ pas un bouchon",
         "%d caractere(s), les %d formats nommes" % (len(plans_pl),
                                                     len(EXT_CAO))
         if assez and not manquantes
         else ("⛔ %d format(s) NON NOMME(S) : %s" % (len(manquantes),
                                                     " ".join(manquantes))
               if manquantes else
               "⛔ %d caractere(s) pour %d attendus — un placeholder muet est "
               "le defaut que cette page refuse" % (len(plans_pl), MIN_PLANS)))

    # ── (c3) LES REPERTOIRES DE 1er NIVEAU SONT CEUX DE T0 ────────────────
    # 🔴 LES **DEUX** SENS, ET LE LIBELLE NE PROMET QUE CE QU'IL FAIT.
    #    Il ne comptait que les AJOUTS tout en imprimant « les memes qu'a T0 » :
    #    un repertoire DISPARU passait, sous une phrase qui affirmait qu'il ne
    #    pouvait pas. Et sa seconde conjonction, `PLACE.startswith("docs/")`,
    #    portait sur une CONSTANTE DE MODULE — toujours vraie, ⛔ inatteignable
    #    par un mutant : elle annoncait une confrontation qui n'avait pas lieu.
    print("\n── (c3) LES REPERTOIRES DE 1er NIVEAU SONT CEUX DE T0 ────────────")
    rep1 = sorted({f.split("/")[0] for f in neuf["arbre"] if "/" in f})
    neufs = [d for d in rep1 if d not in REPERTOIRES_T0]
    disparus = [d for d in REPERTOIRES_T0 if d not in rep1]
    ctrl(not neufs and not disparus,
         "(c3) les repertoires de 1er niveau sont CEUX de T0",
         "%d repertoire(s), aucun neuf, aucun disparu" % len(rep1)
         if not neufs and not disparus
         else "⛔ %d NEUF(S) : %s · %d DISPARU(S) : %s — "
              "`verif_licences_dn52.py` rougit sur tout premier segment que "
              "`LICENSING.md` ne nomme pas, et c'est litteralement son "
              "mutant 2" % (len(neufs), " · ".join(neufs) or "—",
                            len(disparus), " · ".join(disparus) or "—"))

    # ── (c4)(c5)(c6) LE COMPTE, ET CE QUE LES DEUX PAGES EN DISENT ─────────
    print("\n── (c4)(c5)(c6) LE COMPTE EST PUBLIE, ET IL EST VRAI ─────────────")
    plans = plans_de(neuf)
    prefixe = PLACE + "/"
    m_place = [p for p in plans if p.startswith(prefixe)]
    m_ailleurs = [p for p in plans if not p.startswith(prefixe)]
    a_place, a_ailleurs = comptes_publies(page)
    juste = (a_place == len(m_place) and a_ailleurs == len(m_ailleurs))
    ctrl(juste, "(c4) la page PUBLIE les deux comptes, et ils collent",
         "sous la place %d · ailleurs %d" % (len(m_place), len(m_ailleurs))
         if juste
         else "⛔ la page annonce %s/%s, la mesure rend %d/%d — un compte "
              "publie se RE-DERIVE, il ne se recopie pas"
              % (a_place, a_ailleurs, len(m_place), len(m_ailleurs)))
    dit = AFFIRMATION_ZERO in page
    ctrl(dit == (not plans),
         "(c5) la page DIT l'etat du depot, dans les deux sens",
         "0 plan depose, et la page le dit" if dit and not plans
         else ("%d plan(s) depose(s), la page ne dit plus « %s »"
               % (len(plans), PHRASE_ZERO) if not dit and plans
               else ("⛔ %d PLAN(S) DEPOSE(S) et la page dit encore « %s » — "
                     "la phrase est devenue FAUSSE : %s"
                     % (len(plans), PHRASE_ZERO, " · ".join(plans[:2]))
                     if plans else
                     "⛔ 0 plan depose et la page ⛔ NE LE DIT PAS — un "
                     "dossier vide et muet laisse un lecteur chercher")))
    b_place, b_ailleurs = comptes_publies(plans_pl)
    dit_p = AFFIRMATION_ZERO in plans_pl
    accord = (b_place == len(m_place) and b_ailleurs == len(m_ailleurs)
              and dit_p == (not plans))
    ctrl(accord, "(c6) `PLANS.md` dit la MEME chose que la mesure",
         "les deux pages et l'arbre s'accordent" if accord
         else "⛔ `PLANS.md` annonce %s/%s et « %s »=%s ; la mesure rend "
              "%d/%d — deux pages du meme dossier ⛔ ne peuvent pas diverger"
              % (b_place, b_ailleurs, PHRASE_ZERO, dit_p,
                 len(m_place), len(m_ailleurs)))

    # ── (c7)(c8)(c9) OU LES PLANS VIVENT, ET CE QUI N'EN EST PAS UN ───────
    print("\n── (c7)(c8)(c9) LA PLACE EXISTE POUR ETRE UTILISEE ───────────────")
    ctrl(not m_ailleurs, "(c7) tout plan suivi vit SOUS `docs/boitier/`",
         "%d plan(s) hors de la place" % len(m_ailleurs) if not m_ailleurs
         else "⛔ %d PLAN(S) MAL RANGE(S) : %s — la place existe pour etre "
              "utilisee" % (len(m_ailleurs), " · ".join(m_ailleurs[:3])))
    non_cites = [p for p in m_place if os.path.basename(p) not in page]
    ctrl(not non_cites, "(c8) tout plan depose est CITE par la page",
         "%d plan(s) depose(s) ⇒ %d a citer ; le VIDE est garde par (c5), "
         "⛔ pas ici" % (len(m_place), len(m_place)) if not non_cites
         else "⛔ %d PLAN(S) QUE PERSONNE NE CITE : %s"
              % (len(non_cites), " · ".join(os.path.basename(x)
                                            for x in non_cites[:3])))
    intrus = [f for f in neuf["arbre"]
              if f.startswith(prefixe) and f != PLANS_REL
              and not f.lower().endswith(EXT_CAO)]
    ctrl(not intrus, "(c26) la place ne porte QUE des plans (et `PLANS.md`)",
         "%d fichier(s) sous la place, tous au format" % (len(m_place) + 1)
         if not intrus
         else "⛔ %d MAL RANGE(S) : %s — `PLANS.md` ecrit la regle « un "
              "fichier depose ici qui n'est pas un plan est un fichier mal "
              "range », et RIEN ne la tenait : un format CAO hors liste "
              "s'y posait pendant que les deux pages publiaient 0"
              % (len(intrus), " · ".join(os.path.basename(x)
                                         for x in intrus[:3])))
    vu = TEMOIN_OBJ in neuf["arbre"]
    ecarte = TEMOIN_OBJ not in plans
    ctrl(vu and ecarte, "(c9) le temoin `.obj` est VU **et** ECARTE",
         "`%s` suivi, ⛔ pas mis en population" % os.path.basename(TEMOIN_OBJ)
         if vu and ecarte
         else ("⛔ `.obj` EST EN POPULATION — un objet de compilation n'est "
               "pas un plan, et `firmware/` en porte des milliers" if vu
               else "⛔ TEMOIN ABSENT DE L'ARBRE SUIVI — l'instrument ne "
                    "rencontre plus le jeton qu'il pretend ecarter"))

    # ── (c10..c14) LA NOTICE — QUATRE PARAMETRES, QUATRE DISPOSITIONS ─────
    if not regles["sortie_anticipee"]:
        print("\n── (c10..c13) CHAQUE PARAMETRE PORTE SA DISPOSITION ──────────────")
        ent, corps = table_notice(page)
        k_val = colonne(ent or [], "valeur")
        k_dis = colonne(ent or [], "disposition")
        rangs = {}
        for l in corps:
            c = cellules(l)
            cle = re.sub(r"[*`]", "", c[0]).strip().lower()
            rangs[cle] = c
        chiffrees = []

        def _param(nom):
            """`(ok, detail)` pour UN parametre — ⛔ le libelle reste LITTERAL.

            🔴 MESURE DU 2026-09-07 : bati au `%` (`\"(c%d) …\" % (10 + idx)`),
               le libelle ne rendait AUCUN identifiant a l'AST — `RE_ID_CTRL`
               ne reconnait pas `(c%d)`. Ces quatre controles n'existaient
               donc que dans `ids_emis`, et le mutant 27, qui SAUTE ce bloc,
               les faisait disparaitre de la reciproque : (c31) rougissait
               « 4 cibles perimees » sur une gate parfaitement saine. Un
               libelle construit est un identifiant INVISIBLE."""
            c = rangs.get(nom)
            if not c:
                return False, "⛔ LIGNE ABSENTE de la notice"
            val = c[k_val] if k_val is not None and k_val < len(c) else None
            dis = c[k_dis] if k_dis is not None and k_dis < len(c) else ""
            if val and RE_VALEUR_CHIFFREE.search(val) and JETON_SOURCE not in val:
                chiffrees.append("%s = %s" % (nom, val))
            if not val or (JETON_NON_MESURE not in val
                           and JETON_SOURCE not in val):
                return False, ("⛔ valeur « %s » : ni « %s » ni renvoi vers "
                               "`%s`" % (val, JETON_NON_MESURE, JETON_SOURCE))
            # 🔴 UN **VRAI** PORTEUR, ⛔ PAS LE MOT. Le test etait la
            #    sous-chaine `"orteur"` : « Porteur : a nommer » passait, et
            #    « porteur a nommer » = PAS de porteur. C'est la regression
            #    REALISTE — quelqu'un reformule la case et la cle tombe.
            porteur = RE_PORTEUR.search(dis)
            if len(dis) < MIN_DISPOSITION or porteur is None:
                return False, ("⛔ disposition de %d caractere(s) pour %d "
                               "attendus, porteur %s — une case qui ne dit "
                               "rien, ou qui ne nomme AUCUNE cle d'epic, "
                               "n'est pas une disposition"
                               % (len(dis), MIN_DISPOSITION,
                                  porteur.group(0) if porteur
                                  else "⛔ ABSENT"))
            return True, ("valeur « %s », disposition de %d caracteres"
                          % (re.sub(r"[*⛔ ]", "", val), len(dis)))

        # ⚠️ LE **NOM CHERCHE** VIENT DE `PARAMS`, LE **LIBELLE** EST LITTERAL,
        #    et la tension entre les deux est assumee : `PARAMS` fixe la
        #    population (c'est elle que (c14) compte), le litteral rend
        #    l'identifiant lisible A L'AST. Les faire diverger ferait rougir
        #    (c10..c13) sur « LIGNE ABSENTE » — un echec BRUYANT, ⛔ pas muet.
        _ok, _d = _param(PARAMS[0])
        ctrl(_ok, "(c10) « matériau » porte sa disposition", _d)
        _ok, _d = _param(PARAMS[1])
        ctrl(_ok, "(c11) « hauteur de couche » porte sa disposition", _d)
        _ok, _d = _param(PARAMS[2])
        ctrl(_ok, "(c12) « remplissage » porte sa disposition", _d)
        _ok, _d = _param(PARAMS[3])
        ctrl(_ok, "(c13) « supports » porte sa disposition", _d)
        print("\n── (c14) ⛔ AUCUNE VALEUR PUBLIEE SANS SA MESURE ─────────────────")
        ctrl(not chiffrees, "(c14) ⛔ aucun parametre chiffre SANS sa source",
             "%d parametre(s) confronte(s)" % len(PARAMS) if not chiffrees
             else "⛔ %d VALEUR(S) SANS SOURCE : %s — une valeur plausible et "
                  "non mesuree est EXACTEMENT le defaut que cette page existe "
                  "pour eviter" % (len(chiffrees), " · ".join(chiffrees[:2])))

    # ── (c15)(c16)(c17)(c18) CE QUE LA PAGE DOIT DIRE ─────────────────────
    print("\n── (c15..c18) LA PAGE DIT AUSSI CE QU'ELLE NE SAIT PAS ───────────")
    b_essai = bloc_section(page, A_PAS_ESSAYE)
    ctrl(len(b_essai) >= 300, "(c15) la page ecrit ce qui n'a PAS ete essaye",
         "%d caractere(s)" % len(b_essai) if len(b_essai) >= 300
         else "⛔ SECTION ABSENTE OU MUETTE (%d caractere(s)) — dire ce qui "
              "n'a jamais tourne est la moitie utile d'une notice"
              % len(b_essai))
    b_manque = bloc_section(page, A_MANQUE)
    _e, corps_m = table_manque(page)
    sans_porteur = [l for l in corps_m if not RE_PORTEUR.search(l)]
    ok_manque = (bool(corps_m) and not sans_porteur and "orteur" in b_manque)
    ctrl(ok_manque, "(c16) le manque declare NOMME son porteur",
         "%d manque(s), chacun avec sa cle d'epic" % len(corps_m)
         if ok_manque
         else ("⛔ %d LIGNE(S) SANS PORTEUR NOMME — « porteur a nommer » "
               "n'est PAS un porteur" % len(sans_porteur) if sans_porteur
               else "⛔ SECTION OU TABLE DU MANQUE ABSENTE"))
    ctrl(A_PAS_OBLIGATOIRE in page,
         "(c17) la page dit qu'aucun boitier n'est OBLIGATOIRE",
         "la phrase est la" if A_PAS_OBLIGATOIRE in page
         else "⛔ ABSENTE — sans elle, la page laisse croire que le coffrage "
              "conditionne le fonctionnement, ce qu'aucune mesure ne dit")
    b_rem = bloc_section(page, A_REMESURE)
    ctrl("verif_boitier_dn64.py" in b_rem,
         "(c18) la page dit comment ses nombres se re-mesurent",
         "%d caractere(s), la commande est citee" % len(b_rem)
         if "verif_boitier_dn64.py" in b_rem
         else "⛔ SECTION ABSENTE, ou elle ne cite pas la verification — un "
              "chiffre qu'on ne sait pas rejouer est a croire sur parole")

    # ── (c19)(c20) LA LICENCE, ET LA DECOUVRABILITE ───────────────────────
    print("\n── (c19)(c20) LICENCIEE, ET ATTEIGNABLE EN UN CLIC ───────────────")
    lic = prose[LICENCE_REL]
    ligne_docs = [l for l in lic.split("\n")
                  if l.startswith("| `docs/`") and A_LICENCE_DOCS in l]
    ok_lic = ("CC-BY-SA-4.0" in page and LICENCE_REL in " ".join(liens_de(page))
              and bool(ligne_docs) and "CC-BY-SA-4.0" in (ligne_docs or [""])[0])
    ctrl(ok_lic, "(c19) la licence est NOMMEE et `LICENSING.md` la porte",
         "la ligne `docs/` nomme deja les plans du boitier" if ok_lic
         else ("⛔ `LICENSING.md` ne porte plus « %s » sur sa ligne `docs/` — "
               "⛔ CETTE LIGNE NE SE REFORMULE PAS : sa chaine est codee en "
               "dur dans deux mutants de `verif_licences_dn52.py`"
               % A_LICENCE_DOCS if not ligne_docs
               else "⛔ la page ne nomme pas sa licence, ou ne lie pas "
                    "`LICENSING.md`"))
    lu_readme = "docs/boitier.md" in " ".join(liens_de(prose[README_REL]))
    lu_cablage = "boitier.md" in " ".join(liens_de(prose[CABLAGE_REL]))
    ctrl(lu_readme and lu_cablage,
         "(c20) la page est ATTEIGNABLE (README et cablage)",
         "liee depuis les deux" if lu_readme and lu_cablage
         else "⛔ NON LIEE depuis %s — sans lien, la page est INVISIBLE"
              % (" et ".join([x for x, o in ((README_REL, lu_readme),
                                             (CABLAGE_REL, lu_cablage))
                              if not o])))

    # ── (c21)(c25)(c22) LE MARQUEUR, SON ANNOTATION, ET LE JOURNAL ────────
    print("\n── (c21)(c25)(c22) LA ROADMAP ET LE CHANGELOG SUIVENT ────────────")
    rm = prose[ROADMAP_REL]
    a_ligne = bool(re.search(r"(?m)^\| `dn6-4` \|", rm))
    ctrl(a_ligne, "(c21) `docs/roadmap.md` definit le marqueur cite",
         "la ligne existe" if a_ligne
         else "⛔ ABSENTE — la page renvoie un lecteur a cette roadmap pour ce "
              "marqueur, et la regle d'admission publiee est « cite dans cet "
              "arbre »")
    ligne_dn6 = [l for l in rm.split("\n") if l.startswith("| `dn6` |")]
    annote = bool(ligne_dn6) and A_ANNOT_DN6 in ligne_dn6[0]
    pas_neuve = bool(ligne_dn6) and not ligne_dn6[0].rstrip().endswith(
        "| not started |")
    ctrl(annote and pas_neuve, "(c25) la ligne `dn6` est ANNOTEE, ⛔ pas effacee",
         "l'etat est corrige et le report du coffrage est ecrit"
         if annote and pas_neuve
         else ("⛔ elle dit encore `not started` alors que trois de ses quatre "
               "pieces sont livrees" if annote
               else "⛔ l'annotation du report du coffrage a disparu — la "
                    "ligne promet le coffrage sans dire quand"))
    chl = prose[CHANGELOG_REL]
    ok_chl = ("docs/boitier.md" in chl and "verif_boitier_dn64.py" in chl)
    ctrl(ok_chl, "(c22) `CHANGELOG.md` porte l'entree de cette marche",
         "la page et sa verification y sont nommees" if ok_chl
         else "⛔ ABSENTE — livrer sans l'ecrire est ce que ce fichier existe "
              "pour empecher")

    # ── (c23)(c24) LA MOITIE COCKPIT — JOUEE, OU DECLAREE NON JOUEE ───────
    print("\n── (c23)(c24) LE REPORT AU LEDGER ET LA LIGNE DU TRACKER ─────────")
    if cockpit_absent:
        for cid, quoi in (("c23", "le report du manque au ledger"),
                          ("c24", "la dependance ecrite au tracker")):
            print("  [ ×× ] (%s) %-46s ⛔ NON JOUE" % (cid, quoi))
        print("      motif : le depot de planification est PRIVE et ⛔ jamais "
              "clone a cote du code.")
        print("      ⛔ CE N'EST PAS UN VERT : la gate rend %d (prerequis "
              "absent), et le dira plus bas." % RC_PREREQUIS)
    else:
        d = dispo_du_report(neuf["ledger"])
        forme = forme_du_porteur(d[3]) if d else 0
        verdict = sans_accents(d[2]).upper() if d else ""
        v_ok = verdict in VERDICTS_LEDGER
        ctrl(bool(d) and forme != 0 and v_ok,
             "(c23) le manque est PORTE au ledger, avec sa forme",
             "[%s %s] %s · porteur %s (forme %d)"
             % (d[0], d[1], d[2], d[3], forme) if d and forme and v_ok
             else ("⛔ REPORT SANS LIGNE DE DISPOSITION — un report ecrit "
                   "ailleurs qu'au ledger meurt en silence : 14 l'ont fait "
                   "dans cette epic" if not d
                   else ("⛔ verdict « %s » HORS des cinq publies (%s)"
                         % (d[2], " · ".join(VERDICTS_LEDGER)) if not v_ok
                         else "⛔ porteur « %s » : il ne releve d'AUCUNE des "
                              "cinq formes publiees (cle nue · backlog nomme "
                              "· bloquee par · clos par · —)" % d[3])))
        ldn8 = ligne_epic_dn8(neuf["tracker"])
        # 🔴 LE PORTEUR SE CHERCHE DANS LE **CORPS DU COMMENTAIRE** : la ligne
        #    COMMENCE par `epic-dn8:`, donc `RE_PORTEUR` y matchait TOUJOURS
        #    et cette conjonction ne pouvait ⛔ jamais etre fausse.
        corps = corps_du_commentaire(ldn8)
        dit_b = re.search("bo[iî]tier", corps, re.I) is not None
        dit_t = "tournage" in corps.lower()
        dit_p = RE_PORTEUR.search(corps) is not None
        ctrl(dit_b and dit_t and dit_p,
             "(c24) la ligne `epic-dn8` porte la dependance",
             "le boitier, le re-tournage et le porteur y sont nommes"
             if dit_b and dit_t and dit_p
             else "⛔ MUETTE sur %s — la vitrine DEPEND du boitier pose, et "
                  "c'est la ligne qui devrait le dire qui n'en parle pas"
                  % (" et ".join([x for x, o in (("le boitier", dit_b),
                                                 ("le re-tournage", dit_t),
                                                 ("le porteur", dit_p))
                                  if not o]) or "rien"))

    # ── (c30)(c31)(c32) LA RECIPROQUE, MECANIQUE ──────────────────────────
    print("\n── (c30)(c31)(c32) AUCUN CONTROLE GARDE PAR ZERO MUTANT ──────────")
    # 🔴 « N mutants, N vus rougir » prouve `mutant ⇒ rouge`, ⛔ JAMAIS
    #    `controle ⇒ couvert`. Les deux sens sont mesures, SEPAREMENT.
    # 🔴 `reels` SE LIT DANS LA SOURCE : `set(ids_emis)` est fige au moment de
    #    cet appel, et il ⛔ NE CONTIENDRAIT PAS les controles de cockpit le
    #    jour ou le cockpit manque — la reciproque deviendrait plus indulgente
    #    sur un runner que sur le poste.
    lus_ast = ids_par_ast()
    reels = set(ids_emis) | (lus_ast or set())
    vises = set()
    for v in cibles.values():
        vises.update(v)
    nus = sorted(reels - vises, key=lambda s: (len(s), s))
    ctrl(not nus and lus_ast is not None,
         "(c30) chaque controle est vise par >= 1 mutant",
         "%d controle(s) lu(s) a l'AST, %d cible(s) declaree(s)"
         % (len(reels), len(vises)) if not nus and lus_ast is not None
         else ("⛔ %d CONTROLE(S) GARDE(S) PAR RIEN : %s"
               % (len(nus), " · ".join(nus)) if nus
               else "⛔ LA SOURCE NE S'ANALYSE PAS A L'AST — la population de "
                    "ce controle est INCONNUE, ⛔ pas vide"))
    perimees = sorted(vises - reels, key=lambda s: (len(s), s))
    ctrl(not perimees, "(c31) chaque cible de mutant est un controle REEL",
         "%d cible(s) confrontee(s)" % len(vises) if not perimees
         else "⛔ %d CIBLE(S) PERIMEE(S) : %s — un mutant qui vise un controle "
              "inexistant ⛔ ne garde rien"
              % (len(perimees), " · ".join(perimees)))
    orphelins = sorted(set(cibles) - set(MUTANTS))
    sans_cible = sorted(set(MUTANTS) - set(cibles))
    ctrl(not orphelins and not sans_cible,
         "(c32) `CIBLES` et `MUTANTS` se correspondent",
         "%d mutant(s), %d cible(s), cle a cle" % (len(MUTANTS), len(cibles))
         if not orphelins and not sans_cible
         else "⛔ cible(s) SANS mutant : %s · mutant(s) SANS cible : %s"
              % (orphelins or "—", sans_cible or "—"))

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : qu'un plan depose ici soit")
    print("   IMPRIMABLE. Aucune cote n'est lue, aucun maillage n'est ouvert.")
    print("⛔ Ni que le mutant rougisse BIEN le controle qu'il declare : ca,")
    print("   c'est `mesures/dn6-4/T2`, qui relit A COLONNE FIXE les lignes")
    print("   de signalement de defaut.")
    # 🔴 LA REGLE S'IMPRIME **APRES** `bilan()`, ET C'EST UNE MESURE :
    #    `bilan()` peut AJOUTER le KO de (z) et forcer `rc=1`. Imprimee avant,
    #    la phrase disait « rc=0 … aucun KO » pendant que la gate sortait en 1
    #    — la gate se contredisait dans UNE SEULE sortie, sous le mutant 27.
    #    ⇒ elle est re-derivee des compteurs FINAUX, et le `rc` REELLEMENT
    #      rendu est imprime a cote d'elle.
    rc = bilan(regle_rc(ko_total[0], cockpit_absent)[0])
    print("\n── LA REGLE DE `rc`, DERIVEE DU CODE QUI DECIDE ──────────────────")
    print("  " + regle_rc(ko_total[0], cockpit_absent)[1])
    print("  ⇒ rc REELLEMENT rendu : %d" % rc)
    return rc


if __name__ == "__main__":
    sys.exit(main())

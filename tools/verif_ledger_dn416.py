#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-16 / AC6 — LE LEDGER DIT CE QUI RESTE, ET A QUI.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

Le 2026-08-25, l'epic `dn4` publiait : « 388 entrees, dont 160 ouvertes cote
DeskNode, et 27 adressees a des stories deja `done` ». Cinq jours plus tard,
AUCUN de ces chiffres n'a pu etre reproduit — ⛔ PAS parce qu'ils etaient faux,
mais parce que LA CONVENTION DE COMPTAGE N'ETAIT ECRITE NULLE PART. Trois
passes du cadrage ont rendu 233 / 240 / 258 selon la regle de decoupe : l'ecart
entre deux conventions non ecrites vaut 10 %.

⇒ CETTE GATE EST LA CONVENTION. Elle ne CITE pas un nombre : elle le PRODUIT.
   Le manifeste `dn4-16-arbitrage-ledger.md` cite CE script, jamais l'inverse.
   Motif mesure (`dn4-14-2` / `W_SEC_H`) : un nombre ECRIT a cote d'un nombre
   CALCULE finit par diverger.

Et elle exige, pour CHAQUE entree DeskNode ouverte, une LIGNE DE DISPOSITION :

    ⇒ [dn4-16 AAAA-MM-JJ] <VERDICT> · porteur : <...> · preuve : <motif>

------------------------------------------------------------------------------
── ⛔ CE QUE CETTE GATE NE VOIT PAS, ET C'EST ECRIT PLUTOT QUE TU (AC6.9) ─────
------------------------------------------------------------------------------

  🔴 ELLE EXIGE UN VERDICT. ELLE NE PEUT PAS JUGER S'IL EST JUSTE.
     Elle verifie qu'une ligne de disposition existe, que son verdict est l'un
     des CINQ, que son porteur est VIVANT et que sa preuve est un MOTIF. Elle
     ne lit pas le code cite, ne rejoue aucun constat, et ne sait pas si
     `CLOSE` a ete pose sur une entree encore vraie. Le verdict est un acte de
     lecture humaine, consigne au manifeste. ⇒ Elle EXIGE un arbitrage, elle
     ne le REND pas.

  🔴 ELLE NE COMPTE PAS DES BORNES, ET C'EST LE POINT (AC6.6).
     Mesure de cadrage (2026-08-30) : les 240 entrees ouvertes citent 192
     adresses
     `fichier:ligne` ; **ZERO** tombe hors de son fichier. Un controle « la
     ligne existe-t-elle ? » sortirait `192 OK / 0 KO` sur un ledger
     INTEGRALEMENT DERIVE — et `dn_ui.c:3733`, cite comme designant
     `dn_ui_icone_alt()`, porte aujourd'hui `desc_effectif()`, du code sans
     rapport. La correction de l'epic (`:7346`) a derive a son tour en cinq
     jours (`:9948` le 2026-08-30). ⇒ CETTE GATE NE VALIDE AUCUNE ADRESSE
     `fichier:ligne`. Elle REFUSE une preuve qui n'est QU'un numero.
     A rapprocher de « une gate `N OK / 0 KO` peut epingler du code FAUX ».

  🔴 ELLE NE DIT RIEN DES ENTREES KIDSAT — 174 sur 453, hors perimetre PAR
     CONSTRUCTION. Ce n'est pas un oubli : `dn4-16` ne les compte pas, ne les
     arbitre pas, ne les deplace pas. Une passe KidSat aura sa propre story.

  🔴 ELLE NE JUGE PAS LA VIVACITE D'UN `clos par :` NI D'UN `bloquee par :`.
     ⚠️ ECART DECLARE AVEC UNE LECTURE LITTERALE D'AC6.5 : celui-ci exige que
     « le porteur soit vivant ». Or AC3.4 exige qu'une entree `CLOSE` dise
     POURQUOI elle se ferme — et ce qui l'a fermee est, PAR DEFINITION, dans
     le passe (une story `done`, un commit). Exiger qu'un fossoyeur soit
     vivant serait une contradiction. ⇒ La regle appliquee est : **tout
     porteur qui designe du TRAVAIL A VENIR doit etre vivant** (`PORTEE`,
     `RE-HEBERGEE`, et la part story d'une `BLOQUEE`) ; un `clos par :`
     designe du passe et n'est pas soumis a la vivacite. C'est ECRIT ici
     plutot que resolu en silence.

  🔴 ~~ELLE NE LIT QU'UN SEUL FICHIER : `deferred-work.md`.~~
     ⚠️ **CETTE PHRASE EST FAUSSE DEPUIS LE 2026-09-05 (`dn5-7`), ET ELLE EST
     DATEE PLUTOT QU'EFFACEE.** Elle lit desormais **DEUX** fichiers du
     cockpit : `deferred-work.md` **et** le tracker
     `sprint-status-desknode.yaml`. Le tracker etait deja OUVERT avant
     `dn5-7` — mais seulement pour RESOUDRE des statuts (`statut_effectif`) ;
     il est desormais une **POPULATION** a part entiere : la liste AC5.6 y est
     deposee, et le controle « tout porteur de la liste AC5.6 du tracker est
     VIVANT » l'itere (section 3). ⇒ une gate qui affirmerait encore ne lire
     qu'un fichier MENTIRAIT SUR ELLE-MEME, ce qui est le defaut exact du
     constat (9) de `dn5-6` — repete d'un cran.
     ⛔ Elle ne regarde toujours
     JAMAIS `_bmad-output/implementation-artifacts/deferred/*.md` (14
     fichiers thematiques). ⚠️ MESURE DE REVUE (2026-08-30) : 30 entrees
     DeskNode ouvertes deplacees vers un `deferred/desknode.md` ⇒ la gate
     imprime `DeskNode OUVERTES : 218` puis `15 OK, 0 KO`. Trente entrees
     quittent le perimetre EN SILENCE et la gate annonce la pleine sante.
     Le drain est hors-scope de `dn4-16` et porte par une entree BLOQUEE —
     mais AC6.9 exige que la limite soit ECRITE, et elle ne l'etait pas.
     ⇒ Le jour ou le drain se fait, CETTE GATE DOIT APPRENDRE A LIRE
       `deferred/`, sinon elle epinglera VERT un ledger vide de sa substance.

  ⚠️ ELLE NE VOIT PAS LES AUTRES ECRIVAINS DU LEDGER. `bmad-code-review`
     (step-04) est corrige par AC4 ; `bmad-dev-auto` et `bmad-quick-dev`
     ecrivent aussi au ledger par d'autres chemins et NE SONT PAS couverts.

  ⚠️ ELLE NE SAIT PAS QU'UN SECOND FORMAT EXISTE. `bmad-loop-sweep` definit
     `### DW-<n>:` pour CE MEME FICHIER, et son `--migrate` exige ZERO prose
     residuelle ⇒ il detruirait les 443 entrees en prose et les 14 fichiers
     thematiques qu'il ne connait pas. La collision est DECLAREE en tete du
     ledger ; ⛔ elle n'est pas tranchee ici.

------------------------------------------------------------------------------
── LA CONVENTION, ET C'EST DU CODE (AC1.3) ───────────────────────────────────
------------------------------------------------------------------------------

  (1) UNE ENTREE = une puce de PREMIER NIVEAU (`^- `, zero indentation) dans
      une section `## Deferred from: ...`. Son texte court jusqu'a la puce de
      premier niveau suivante, le prochain titre `^#`, ou la fin du fichier.
      ⇒ Les puces INDENTEES (`^  - `) sont des CONTINUATIONS, ⛔ pas des
        entrees. C'est cette regle-la qui separe 240 de 258.
      ⇒ Une puce hors section `## Deferred from:` (index, legende, bandeau)
        n'est PAS une entree. C'est cette regle-la qui separe 443 de 484.

  (2) PERIMETRE DESKNODE = l'entree porte le tag `[DeskNode]` EN TETE DE PUCE,
      OU le titre de sa section cite `dnN-M` / contient `desknode` (insensible
      a la casse). ⛔ Le contenu technique n'entre pas dans la regle : un
      constat sur `dn_ui.c` range dans une section KidSat resterait KidSat.

  (3) UNE ENTREE OUVERTE = une entree dont la puce NE COMMENCE PAS par `✅`
      (apres `- ` et espaces). Le `✅` est la marque de solde du depot.
      ⚠️ La ligne de disposition NE ferme PAS l'entree : une entree arbitree
        `CLOSE` reste OUVERTE au sens du compte. Motif : si l'arbitrage
        retirait les entrees du perimetre, la gate cesserait de les surveiller
        et le compte deviendrait non reproductible d'un tir a l'autre.

  (4) LE MARQUEUR = le PREMIER glyphe de marqueur EN TETE de puce, apres `- `,
      les espaces, un `**` d'ouverture et un tag `[DeskNode]`. Sinon `(sans)`.
      🔴 MESURE DE CADRAGE (2026-08-30, sur 240 entrees ouvertes) : un glyphe
      compte PARTOUT DANS LA LIGNE rend 45 🔴 / 23 ⚠️ / 15 🆕 ; EN TETE il rend
      42 🔴 / 14 ⚠️ / 2 🆕. La regle « en tete » est donc la PLUS SOBRE des
      deux, et elle n'avait jamais ete ecrite.
      ⛔ CORRECTIF DE REVUE (2026-08-30) : la version precedente de ce
      commentaire ajoutait « soit exactement le releve du 2026-08-25 ». C'EST
      FAUX. L'epic releve 28 🔴 · 40 🟠 · 35 ⚪ · 17 🟢 · 13 🟡 · 13 (sans) ;
      la regle « en tete » rend 42 / 55 / 66 / 25 / 13 / 20 sur le meme
      perimetre. SEUL 🟡 coincide ; 🔴 est ecarte de 14. La regle n'a donc PAS
      ete validee en reproduisant l'epic — elle a ete CHOISIE, et l'ecart avec
      l'epic reste entier. C'est ecrit ici plutot que de faire dire a une
      mesure ce qu'elle ne dit pas.

------------------------------------------------------------------------------
Usage :
    python3 tools/verif_ledger_dn416.py [--cockpit CHEMIN] [--compte]
                                        [--manifeste] [--sortie F]

  (defaut)     : la GATE. Exige une disposition valide sur chaque entree
                 ouverte. Sort en 1 des qu'un controle rougit.
  --compte     : mode COMPTE SEUL (T0). N'exige aucune disposition ; imprime
                 la convention, les totaux et l'histogramme des marqueurs.
                 ⚠️ Il sort quand meme en 1 si un controle STRUCTUREL rougit
                 (depot absent, ledger illisible) — ⛔ jamais un 0 inconditionnel.
  --manifeste  : emet le TABLEAU du manifeste (une ligne par entree ouverte),
                 pour que `dn4-16-arbitrage-ledger.md` ne recopie AUCUN chiffre.
==============================================================================
"""

import argparse
import datetime
import io
import os
import re
import sys
import unicodedata

# >>> DN8-REGION — tout ce qui suit jusqu'au marqueur de fin est ECRIT PAR dn8,
#     et c'est a ce titre que `tools/verif_harnais_dn81.py` (c3) le juge. ⛔ Le
#     RESTE de ce fichier appartient a `dn4` et n'est PAS dans le perimetre :
#     `epic-dn8` installe le garde-fou pour ce qu'elle ECRIT.
# ══ dn8-1 / AC8.1.2 — LE TRACKER SE **PARSE**, ⛔ IL NE SE BALAIE PLUS SEUL ══
#
# 🔴 CE QUE CETTE GATE LAISSAIT PASSER, ET C'EST MESURE LE 2026-09-11 sur une
#    COPIE JETABLE du cockpit (⛔ jamais sur le cockpit vivant) :
#    la cle `dn8-6-la-version-se-voit-sur-la-dalle` RE-INDENTEE DE 2 A 4
#    ESPACES rend le tracker **ILLISIBLE pour tout parseur YAML**
#    (`yaml.ParserError`) — et cette gate rendait **`BILAN : 35 OK, 0 KO`,
#    rc=0**. Un caractere. Zero rouge.
#    ⚠️ ET LE TEMOIN PRESCRIT PAR LE DOSSIER (`epic-dn8` re-indentee) ROUGIT,
#       LUI — mais **POUR LE MAUVAIS MOTIF** : 3 KO qui disent tous
#       « 13 CLE(S) FANTOME(S) : epic-dn8 », ⛔ jamais « le tracker ne se
#       parse pas ». Il ne rougit que parce que `epic-dn8` se trouve etre cite
#       13 fois comme PORTEUR. Une cle que personne ne cite — et il y en a —
#       casse le fichier EN SILENCE. ⇒ le temoin honnete est la cle NON CITEE,
#       et les deux sont joues dans `mesures/dn8-1/`.
#
# ⚠️ `yaml` N'EST PAS DANS LA STDLIB, ET LA CI S'INTERDIT `pip install`
#    (`.github/workflows/gates.yml`). ⇒ L'IMPORT EST **GARDE**, et son absence
#    fait DECLARER L'AVEUGLEMENT EN PROPRE dans la sortie — ⛔ jamais un vert
#    muet, ⛔ jamais un `Traceback`. C'est l'issue que `NFR14` fournit
#    elle-meme : *« ou il declare son aveuglement EN PROPRE »*.
# ⚠️ LES DEUX CHEMINS SONT REELS, ET LES DEUX DOIVENT ETRE VUS : le parse REEL
#    est le chemin du POSTE DE L'AUTEUR ; l'aveuglement declare est le chemin
#    CI — ou cette gate est de toute facon NON-JOUABLE (`rc=4`, cockpit prive).
try:
    import yaml
    _YAML = True
    _YAML_MOTIF = ""
except ImportError as _x:                                # pragma: no cover
    yaml = None
    _YAML = False
    _YAML_MOTIF = str(_x)

# ⚠️ LA DECLARATION D'AVEUGLEMENT, ⛔ PAS UN COMMENTAIRE : `NFR14` autorise un
#    controle sans parseur A CONDITION qu'il nomme EN PROPRE ce qu'il ne sait
#    pas voir. Un commentaire ne s'imprime pas — celle-ci est une DONNEE, elle
#    est LUE par le code ci-dessous et ECRITE sur la console. C'est ce que
#    `verif_harnais_dn81.py` (c3) exige : une declaration qu'un `grep` ne
#    puisse pas fabriquer depuis de la prose.
AVEUGLEMENT_YAML = (
    "⛔ PyYAML ABSENT (%s) — le controle de parse du tracker n'est PAS JOUE. "
    "Ce que cette gate ne voit alors PAS : une indentation qui rend le "
    "tracker illisible pour tout parseur, sans changer une seule ligne au "
    "balayage textuel. ⛔ Ce n'est ⛔ NI un OK ⛔ NI un KO : c'est un trou "
    "DECLARE, et il se referme avec `pip install PyYAML` hors CI.")
# <<< DN8-REGION — fin de la region ecrite par dn8 (import garde + aveuglement)

DESKNODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 🔴 REVUE 2026-09-02 — `expanduser("~")` ET `${HOME}` NE DISENT PAS LA MEME
#    CHOSE QUAND `HOME` EST ABSENT. Le shell de `run_gates.sh` retombe sur
#    `${HOME:-/nonexistent}` ; Python, lui, interroge `/etc/passwd` et rend le
#    vrai foyer de l'utilisateur. Mesure : `env -u HOME bash tools/run_gates.sh`
#    rendait `23 VERTE, 3 ROUGE, 1 NON-JOUABLE`, rc 1 — deux gates qui rendent
#    **0** comptees ROUGES en « DECLARATION DEMENTIE ». Contextes reels : cron,
#    conteneur, `sudo` sans `-E`, `env -i`.
#    ⇒ ON LIT `HOME` COMME LE SHELL LE LIT, avec la MEME valeur de repli.
COCKPIT_DEFAUT = os.path.join(os.environ.get("HOME") or "/nonexistent",
                              "projects", "compagnon_project")

# ── dn4-39 / AC39.3.a — LE `rc` « PREREQUIS ABSENT », DISTINCT DU ROUGE ─────
# Meme motif et meme choix que `tools/verif_dossier_dn415.py`, ou il est ecrit
# en entier : `2` est le message d'usage de `verif_sr03.py`, `3` est deja rendu
# par `verif_paliers_dn441.py` sur un MUTANT PERIME. Mesure du 2026-09-02 en
# clone neuf + `HOME` etranger : cette gate rendait `1 OK, 3 KO`, rc **1** —
# le meme `rc` que son rouge. La declaration NON-JOUABLE etait invérifiable.
# 🔴 ORDRE : un VRAI defaut l'emporte — rc **1** des qu'un KO existe, meme si un
#    prerequis manque. Sinon un prerequis absent masquerait un rouge.
RC_PREREQUIS = 4

REL_LEDGER = "_bmad-output/implementation-artifacts/deferred-work.md"
REL_TRACKER = "_bmad-output/implementation-artifacts/sprint-status-desknode.yaml"
REL_MANIFESTE = "_bmad-output/implementation-artifacts/dn4-16-arbitrage-ledger.md"

# ── dn4-39 / AC39.5.a — LE §9 S'ANCRE PAR **BORNE**, ⛔ PLUS PAR NUMERO DE LIGNE
#
# 🔴 CE QUE LE LEDGER REPROCHAIT, ET QUI EST MESURE : le tableau du §9 porte une
#    colonne `ligne` qui est le NUMERO DE LIGNE dans `deferred-work.md`. Toute
#    ecriture EN AMONT du ledger decale ces numeros ⇒ le controle #5 rougit.
#    Mesure du 2026-09-02, sur une COPIE du cockpit : **une** entree ordinaire
#    inseree EN TETE fait passer la gate de `23 OK / 0 KO` (rc 0) a `rc 1`,
#    **266 lignes divergentes**. ⚠️ 266, ⛔ pas les 250 de `dn4-24` : le chiffre
#    se RE-MESURE. Un ajout en QUEUE, lui, ne decale rien.
# 🎯 CE QUE CA COUTAIT : **NFR5 de `epic-dn5`** s'interdisait d'ecrire dans
#    `deferred-work.md` A CAUSE DE CE CONTROLE. Une epic entiere contournait une
#    gate. Rendre la regeneration a UNE commande RETIRE ce motif.
#
# ⛔ ET LE REPORT NE SE FAIT PLUS A LA MAIN. Le mode `--manifeste --sortie` ne
#    produisait qu'un tableau brut qu'un humain devait coller — c'est le « geste
#    manuel de plus » que l'entree nomme. `--en-place` ecrit ENTRE CES BORNES.
#    ⚠️ Des BORNES, ⛔ pas un numero de ligne : ancrer la reecriture sur « la
#    ligne 390 » reproduirait EXACTEMENT le defaut qu'on solde.
BORNE_DEBUT = "<!-- dn4-39 MANIFESTE DEBUT — GENERE, ⛔ ne rien ecrire entre ces deux bornes -->"
BORNE_FIN = "<!-- dn4-39 MANIFESTE FIN -->"
# 🔴 REVUE 2026-09-02 — LA COMMANDE PUBLIEE N'ETAIT PAS COLLABLE, ET ELLE
#    CODAIT EN DUR UN CHEMIN PERSONNEL :
#      · `~/projects/desknode/` etait ecrit en dur alors que ce script CONNAIT
#        sa racine (DESKNODE, plus bas) — le defaut de `dn5-3` reintroduit a neuf
#        dans la story qui ecrit « ⛔ AUCUN CHEMIN ABSOLU ICI » ;
#      · le gabarit `<cockpit>` est parse par bash comme une PAIRE DE
#        REDIRECTIONS : coller la commande cree un fichier nomme `--manifeste`.
#    ⇒ la racine est DERIVEE, et le trou se nomme en majuscules sans chevrons.
#    ⚠️ AC39.5 vend « ⛔ aucun copier-coller » : la commande a copier se colle.
def cmd_regen():
    return ("python3 %s --cockpit CHEMIN_DU_COCKPIT --manifeste --en-place"
            % os.path.join(DESKNODE, "tools", "verif_ledger_dn416.py"))

VERDICTS = ("PORTEE", "RE-HEBERGEE", "CLOSE", "BLOQUEE", "CONNAISSANCE")

# Les verdicts qui designent du TRAVAIL A VENIR ⇒ leur porteur doit etre VIVANT.
VERDICTS_A_VENIR = ("PORTEE", "RE-HEBERGEE", "BLOQUEE")

STATUTS_VIVANTS = ("backlog", "in-progress", "ready-for-dev", "review",
                   "blocked", "optional")
STATUTS_MORTS = ("done", "superseded")
# 🔴 dn4-40 — `optional` AJOUTE, ET ⛔ PAS PAR CONFORT : IL FALLAIT LES DEUX
# TABLES DANS LE MEME GESTE. Tant que `lit_tracker()` repliait sur
# `^dn\d+-\d+`, les 16 cles `epic-*` etaient INVISIBLES et leur statut ne
# pouvait rien casser. Les faire entrer sans classer `optional` aurait fait
# rougir le controle « statut CONNU » sur des cles PARFAITEMENT VALIDES.
# MESURE (2026-09-02) : les 8 `optional` du tracker sont TOUS des
# `epic-<n>-retrospective` — ⛔ zero story ordinaire. Une retrospective
# `optional` n'est ni faite ni annulee : elle ne CLOT rien, donc elle ne peut
# pas rejoindre `done`/`superseded`. La prescription n'interdit comme porteur
# que `done`/`superseded` (§ « Interdit comme porteur ») ⇒ `optional` est
# VIVANT. ⚠️ Ce classement ne change AUCUN verdict au 2026-09-02 : zero
# disposition ne nomme aujourd'hui une cle `epic-*`. Il ouvre une capacite,
# et c'est le mutant `epic-*` de la campagne qui la prouve.

MARQUEURS = ("🔴", "🟠", "⚪", "🟢", "🟡", "⚠️", "🆕", "🎯", "⚫", "🔵",
             "🧹", "📋", "🗺️", "✅", "⏳", "⏸️")
# ⚠️ `⏳` et `⏸️` AJOUTES A LA REVUE (2026-08-30). Le controle « aucun marqueur
# de tete n'est HORS LISTE », neuf lui aussi, les a fait apparaitre : trois
# entrees (l.3098, l.3617, l.4075) etaient rangees dans « (sans) » et
# faussaient l'histogramme PUBLIE. La liste fermee ne se voyait pas elle-meme.

# 🔴 dn4-40 / AC40.7.c — L'INSTRUMENT DE CAMPAGNE, ⛔ PAS UN CHANGEMENT DE
# FORMAT. Import DEFENSIF : une gate doit rester jouable si son instrument
# manque. Sans `DN_TRACE_CTRL`, la console sort a l'octet pres comme avant.
try:
    import dn_trace
except ImportError:                                  # pragma: no cover
    dn_trace = None

ok_total = [0]
ko_total = [0]


def ctrl(ok, libelle, detail_ok="", detail_ko=None):
    """Un controle, imprime, compte. ⛔ Jamais un skip silencieux.

    ⚠️ CORRECTIF DE REVUE (2026-08-30) : `detail_ok` et `detail_ko` sont
    DISTINCTS. L'ancienne signature n'avait qu'un `detail`, si bien qu'un
    ECHEC imprimait la justification du SUCCES — une ligne `[KO ]` qui se
    lisait comme une explication de reussite. Et le detail d'un KO n'est
    PLUS tronque : c'est lui qui porte les numeros de ligne fautifs.
    """
    if dn_trace is not None:
        dn_trace.trace(ok, libelle)
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-62s %s" % (libelle[:62], detail_ok[:60]))
    else:
        ko_total[0] += 1
        d = detail_ok if detail_ko is None else detail_ko
        print("  [KO ] %-62s %s" % (libelle[:62], d))
    return ok


def sans_accents(s):
    """PORTÉE == PORTEE, RE-HÉBERGÉE == RE-HEBERGEE, BLOQUÉE == BLOQUEE."""
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


# ═══════════════════════════════════════════════════════════════════════════
#  LA CONVENTION, IMPLEMENTEE  (AC1.3 / AC6.3)
# ═══════════════════════════════════════════════════════════════════════════

RE_FENCE = re.compile(r"^\s*(?:```|~~~)")


def decoupe(texte):
    """Convention (1) : sections `## Deferred from:` + puces de PREMIER niveau.

    🔴 CORRECTIF DE REVUE (2026-08-30) — AUCUNE CONSCIENCE DES BLOCS DE CODE.
    Une puce `- ` a l'interieur d'un bloc ``` (un extrait de diff, un exemple
    de format) devenait une ENTREE FANTOME : elle gonflait le compte et
    tronquait le texte de l'entree reelle avant sa ligne de disposition, d'ou
    un « SANS DISPOSITION » sur une entree qui en portait une. Les fences sont
    desormais suivies, a la DECOUPE comme a l'ABSORPTION.

    ⚠️ LIMITE DECLAREE, ⛔ non corrigee (voir l'en-tete) : une puce de premier
    niveau sous une rubrique `### ` INTERNE a une section satisfait la
    convention et compte donc comme une entree, meme quand c'est de la prose
    narrative. Six cas mesures au 2026-08-30. Redefinir la regle ferait
    rebouger le perimetre et invaliderait le manifeste ⇒ la rubrique est
    REMONTEE (`rubrique`) et SOUS-COMPTEE, pas escamotee.
    """
    lignes = texte.split("\n")
    fence = [False] * len(lignes)
    dedans = False
    for i, l in enumerate(lignes):
        if RE_FENCE.match(l):
            dedans = not dedans
            fence[i] = True
            continue
        fence[i] = dedans
    sections = []
    cur = None
    rubrique = None
    for i, l in enumerate(lignes):
        if fence[i]:
            continue
        if l.startswith("## Deferred from:"):
            cur = {"titre": l[len("## Deferred from:"):].strip(),
                   "ligne": i + 1, "entrees": []}
            rubrique = None
            sections.append(cur)
        elif l.startswith("## "):
            cur = None
            rubrique = None
        elif l.startswith("#"):
            rubrique = l.lstrip("#").strip()[:48]
        elif cur is not None and re.match(r"^- ", l):
            j = i
            while (j + 1 < len(lignes)
                   and not (not fence[j + 1] and re.match(r"^- ", lignes[j + 1]))
                   and not (not fence[j + 1] and lignes[j + 1].startswith("#"))):
                j += 1
            cur["entrees"].append({
                "ligne": i + 1,
                "txt": "\n".join(lignes[i:j + 1]),
                "tete": l,
                "sec": cur["titre"],
                "sec_ligne": cur["ligne"],
                "rubrique": rubrique,
            })
    return sections


def est_desknode(e):
    """Convention (2).

    🔴 CORRECTIF DE REVUE (2026-08-30) — LE TAG ETAIT CHERCHE EN SOUS-CHAINE
    SUR TOUT LE TEXTE ABSORBE. Une entree KidSat qui se contente de CITER
    `[DeskNode]` (dans une prose, un exemple de format, une comparaison)
    basculait la frontiere des 174 entrees hors-perimetre. Le tag est une
    marque de TETE de puce : il se lit la.
    """
    return ("[DeskNode]" in e["tete"]
            or re.search(r"\bdn\d|desknode", e["sec"], re.I) is not None)


def sous_marque_de_solde(e):
    """L'entree porte-t-elle une marque de solde HISTORIQUE du depot ?

    ⚠️ LIMITE DECLAREE, ⛔ non corrigee. La convention (3) ne connait que le
    `✅` de tete. Or le depot clot AUSSI par `~~...~~ — SOLDE par dnX` et par
    `[SOLDE]`. Ces entrees restent donc OUVERTES au sens du compte — ce qui
    est COHERENT avec la regle (3) (« une entree arbitree CLOSE reste ouverte
    au sens du compte », pour que le compte soit reproductible d'un tir a
    l'autre), et elles ont bien recu un verdict `CLOSE`. On les SOUS-COMPTE
    plutot que de redefinir le perimetre en cours de route.
    """
    return re.search(r"SOLD[ÉE]E?\b|~~", e["tete"]) is not None


def est_ouverte(e):
    """Convention (3)."""
    return re.match(r"^-\s*✅", e["txt"]) is None


def marqueur(e):
    """Convention (4) : le PREMIER glyphe EN TETE de puce."""
    t = e["tete"][2:]
    t = re.sub(r"^\s*", "", t)
    t = re.sub(r"^\*\*", "", t)
    t = re.sub(r"^\[DeskNode\]\s*", "", t)
    t = re.sub(r"^\*\*", "", t)
    t = re.sub(r"^\s*", "", t)
    for m in MARQUEURS:
        if t.startswith(m):
            return m
    return "(sans)"


def titre_court(e, n=58):
    """Le libelle de l'entree, nettoye — pour le manifeste. ⛔ Jamais une preuve."""
    t = e["tete"][2:]
    t = re.sub(r"^\s*", "", t)
    for m in MARQUEURS:
        t = t.replace(m, "")
    t = t.replace("[DeskNode]", "")
    t = re.sub(r"[*`«»\"]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:n]


# ═══════════════════════════════════════════════════════════════════════════
#  dn4-40 — LE §9 CESSE D'ETRE ANCRE PAR NUMERO DE LIGNE  (DECISION OWNER (b))
# ═══════════════════════════════════════════════════════════════════════════
#
# 🔴 LA CONTRADICTION QUE CECI SOLDE. Cette gate REFUSE une preuve qui se
#    reduit a une adresse `fichier:ligne` (« il derive, et il se lit vert pour
#    tout controle de bornes »). Et elle IMPOSAIT un NUMERO DE LIGNE comme 1re
#    colonne de son manifeste, comparee AU CARACTERE PRES. Le manifeste
#    l'ecrivait lui-meme : « la colonne `ligne` est un repere de navigation,
#    ⛔ pas une preuve » — alors que le controle en faisait exactement une
#    preuve.
#    MESURE : une entree temoin ORDINAIRE inseree en amont du ledger faisait
#    sortir **267 lignes DIVERGENTES sur 267**, sans qu'un seul sens ait change.
#
# ⇒ L'ANCRE EST DESORMAIS DERIVEE DU CONTENU, comme `dn4-24` l'a fait pour la
#   gate du dossier : (section · marqueur · titre court · RANG parmi les
#   homonymes). Le numero de ligne DISPARAIT du tableau — il n'y avait
#   d'utilite que de navigation, et `--en-place` le regenere de toute facon.
#
# ⚠️ LE RANG EST INDISPENSABLE : deux entrees peuvent partager section,
#    marqueur et titre court. Sans lui, deux lignes du manifeste porteraient la
#    MEME ancre et la comparaison deviendrait ambigue — le defaut que la cle
#    d'ancrage de `dn4-24` a deja paye. Un controle dedie le verifie.
#
# ⚠️ 8 CARACTERES HEXA : sur 267 entrees, la probabilite de collision est
#    negligeable, ET elle est CONTROLEE plutot que supposee.


def ancres(ouvertes):
    """{id(entree): ancre} — derivee du CONTENU, a UNE reserve ECRITE.

    ⚠️ REVUE 2026-09-03 — LA PHRASE D'ORIGINE (« ⛔ jamais de la position »)
    SUR-AFFIRMAIT. Le `base` (section · marqueur · titre court) est bien du
    CONTENU, mais le RANG parmi les homonymes est attribue DANS L'ORDRE DU
    DOCUMENT : inserer un homonyme EN AMONT renumerote celui qui existait et
    CHANGE SON ANCRE. Latent aujourd'hui (aucun groupe d'homonymes sur les
    entrees ouvertes), mais `titre_court` tronque — et c'est precisement la
    troncature qui FABRIQUE des homonymes.
    ⛔ Le controle « chaque ancre designe UNE seule entree » ne peut PAS voir
    cela : le rang rend l'entree du hachage unique PAR CONSTRUCTION, si bien
    que ce controle ne garde que la collision de hachage 32 bits. Le vrai
    risque est donc garde par le controle de DOUBLON D'ANCRE cote manifeste,
    ⛔ pas ici — c'est ecrit plutot que tu.
    """
    import hashlib
    rangs = {}
    out = {}
    for e in ouvertes:
        base = "%s|%s|%s" % (e["sec"][:46], marqueur(e), titre_court(e))
        r = rangs.get(base, 0)
        rangs[base] = r + 1
        h = hashlib.sha256(("%s|%d" % (base, r)).encode("utf-8")).hexdigest()
        out[id(e)] = h[:8]
    return out


_ANCRES = {}

# ⚠️ L'EN-TETE DU §9 — UNE SEULE SOURCE POUR LES DEUX MODES D'ECRITURE
#    (`--en-place` et `--sortie`). Les avoir ecrits deux fois les avait fait
#    diverger : l'un annoncait `ancre`, l'autre `ligne`.
EN_TETE_MANIFESTE = ("| ancre | section d'origine | marq. | titre court |"
                     " verdict | porteur | preuve |\n"
                     "|:-:|---|:-:|---|---|---|---|\n")


def ligne_manifeste(e):
    r"""La ligne de tableau d'UNE entree — la SEULE fabrique.

    🔴 CORRECTIF DE REVUE (2026-08-30) : `--manifeste` et le controle #5
    ne partageaient rien. Le controle comparait un NOMBRE DE LIGNES
    (`len(findall(r"^\| *\d+ *\|"))`), donc une ligne FABRIQUEE le
    satisfaisait, et le manifeste livre divergeait deja d'une ligne (la 5575)
    sans que rien ne rougisse. Les deux passent desormais par ici, et le
    controle compare le CONTENU.
    """
    d = dispo(e)
    return "| %s | `%s` | %s | %s | %s | %s | %s |" % (
        _ANCRES.get(id(e), "????????"), e["sec"][:46], marqueur(e),
        titre_court(e).replace("|", "\\|"),
        ("**%s**" % d["verdict_brut"]) if d else "⛔ ABSENT",
        (d["porteur"].replace("|", "\\|")) if d else "⛔ ABSENT",
        (d["preuve"].replace("|", "\\|")) if d else "⛔ ABSENT")


# ═══════════════════════════════════════════════════════════════════════════
#  LA LIGNE DE DISPOSITION  (AC3.1)
# ═══════════════════════════════════════════════════════════════════════════

# 🔴 CORRECTIF DE REVUE (2026-08-30) — LA CLE DE STORY N'EST PLUS CODEE EN DUR.
# Defaut mesure : la regex exigeait `[dn4-16ELLE-MEME ...]`, alors que le format
# prescrit au producteur (`step-04-present.md`) est `⇒ [<story-key> <date>]`.
# La MEME entree, au format prescrit, avec la cle `dn4-32` sortait
# « ⛔ 1 SANS DISPOSITION » — un rouge au diagnostic FAUX. La gate ne gardait
# donc que les 248 lignes de `dn4-16`, ⛔ pas le format qu'elle installe.
RE_DISPO = re.compile(
    r"^\s*⇒\s*\[([A-Za-z][\w.\-]*)\s+(\d{4}-\d{2}-\d{2})\]\s*"
    r"([A-ZÀ-ÿ\-]+)\s*·\s*"
    r"porteur\s*:\s*(.*?)\s*·\s*"
    r"preuve\s*:\s*(.*?)\s*$",
    re.M)

# Une preuve qui n'est QU'une adresse `fichier:123` (ou `fichier:12-34`) est
# REFUSEE — AC6.6. Motif mesure : 0 adresse sur 192 tombe hors fichier.
#
# 🔴 CORRECTIF DE REVUE (2026-08-30) — LE GARDE-FOU ETAIT UNE FORMALITE.
# L'ancienne regex, entierement ancree et sans tolerance, ne refusait que le
# cas ou la preuve valait EXACTEMENT `fichier:123`. Passaient donc :
#   `preuve : voir dn_ui.c:9948`   `preuve : \`dn_ui.c:9948\` (derive)`
#   `preuve : **dn_ui.c:3733**`    `preuve : dn_ui.c : 9948`
# Un seul mot suffisait pour continuer d'ecrire les preuves par numero de
# ligne qu'AC6.6 existe pour interdire. On NORMALISE d'abord (gras, backticks,
# guillemets, amorces « voir »/« cf. »/« cf »), puis on refuse.
RE_AMORCE = re.compile(r"^(?:voir|cf\.?|see|→|⇒)\s+", re.I)


def preuve_est_nue(p):
    """True si la preuve se REDUIT a une adresse `fichier:ligne`."""
    s = p.strip()
    s = re.sub(r"[`'\"*_]", "", s)          # gras, backticks, guillemets
    s = RE_AMORCE.sub("", s).strip()
    s = re.sub(r"\s*:\s*", ":", s)          # `dn_ui.c : 9948` ⇒ `dn_ui.c:9948`
    return re.fullmatch(r"[\w./+-]+:\d+(?:[-–]\d+)?", s) is not None

RE_STORY = re.compile(r"\b(dn\d+-\d+(?:-\d+)?)\b", re.I)

# ═══════════════════════════════════════════════════════════════════════════
#  LES CINQ FORMES DU PORTEUR  (dn4-40 / AC40.1)
# ═══════════════════════════════════════════════════════════════════════════
#
# 🔴 CE QUE CE BLOC REMPLACE, ET POURQUOI IL EXISTE.
# `porteurs_a_venir()` appliquait `RE_STORY.findall()` au champ porteur
# ENTIER. Rien ne disait a la gate QUEL segment designe le porteur ⇒ DEUX
# echecs OPPOSES sortaient de la MEME extraction, prouves par mutant au
# cadrage du 2026-09-02 :
#
#   · un porteur EN PROSE (`bloquee par : <fait externe>`) ne rendait AUCUNE
#     cle ⇒ les 3 controles de vivacite tournaient sur une population VIDE et
#     annoncaient « OK » sans avoir rien regarde. MESURE : 12 dispositions
#     sur les 164 « a venir » (7,3 %), toutes de FORME 3, donc toutes
#     PARFAITEMENT LEGITIMES. Le remede n'etait pas d'interdire la prose.
#   · une story CLOSE citee en INCISE dans un champ dont la cle vivante est
#     ailleurs faisait rougir « PORTEUR MORT » sans qu'aucun porteur ne soit
#     mort. Un tel faux rouge etait deja ARME dans le ledger (une prose qui
#     cite une story `in-progress` comme FAIT BLOQUANT) : il attendait que
#     cette story passe `done`.
#
# ⇒ Le porteur se lit DESORMAIS par la FORME qu'il declare — les cinq de
#   `docs/bmad/deferred-work-ligne-porteur.md` § « Les cinq formes ».
#
# ⚠️ TRAP MESURE : la reconnaissance travaille sur un champ NORMALISE
# (accents retires, gras et backticks retires). C'est indispensable —
# `bloquée par` s'ecrit avec un accent dans les 13 champs reels — mais ca
# veut dire qu'⛔ AUCUNE marque accentuee ou casse-sensible ne peut servir de
# separateur ici.
#
# ⚠️ CE QUE LA SEGMENTATION NE DOIT PAS DEVENIR : plus PERMISSIVE. Restreindre
# ce qui est extrait sans rien mettre a la place rendrait les controles muets
# SOUS UNE AUTRE FORME. C'est pourquoi chaque forme recoit son propre
# controle ci-dessous, et pourquoi la forme 0 (AUCUNE des cinq) est un KO.

# Une cle de story, ou une cle d'EPIC. ⚠️ Les deux ecritures coexistent
# REELLEMENT : 143 porteurs sur 151 s'ecrivent en COURT (`dn4-27`), 8 en
# PLEIN (`dn4-40-les-gates-...`). `lit_tracker()` indexe donc les deux.
RE_CLE_PORTEUR = re.compile(r"^(?:dn\d+-\d+(?:-[\w.]+)*"
                            r"|epic-dn\d+(?:-[\w.]+)*)$", re.I)

RE_F2 = re.compile(r"^backlog\s+nomme?\s*:\s*(.*)$", re.I)
RE_F3 = re.compile(r"^bloquee?\s+par\s*:\s*(.*)$", re.I)
RE_F4 = re.compile(r"^clos\s+par\s*:\s*(.*)$", re.I)

FORME_LIBELLE = {
    0: "⛔ AUCUNE des cinq",
    1: "1 cle nue",
    2: "2 backlog nomme",
    3: "3 bloquee par",
    4: "4 clos par",
    5: "5 tiret (CONNAISSANCE)",
}


def forme_du_porteur(p):
    """Rend `(numero, argument)` — la forme DECLAREE, ⛔ jamais devinee.

    `0` = le champ ne releve d'AUCUNE des cinq formes. ⛔ Ce n'est pas un
    repli silencieux vers « cle nue » : c'est un KO. Sans lui, un champ
    inconnu serait reclasse en forme 1, ne resoudrait aucune cle, et la gate
    RETOMBERAIT MUETTE sous un autre nom — exactement le defaut qu'on repare.
    """
    s = sans_accents(p.strip())
    s = re.sub(r"[`*_]", "", s).strip()
    m = RE_F2.match(s)
    if m:
        return 2, m.group(1).strip()
    m = RE_F3.match(s)
    if m:
        return 3, m.group(1).strip()
    m = RE_F4.match(s)
    if m:
        return 4, m.group(1).strip()
    if s.strip("—–-. ") == "":
        return 5, ""
    if RE_CLE_PORTEUR.match(s):
        return 1, s.lower()
    return 0, s


# ⚠️ AC40.1.h — TRANCHE, ET ECRIT, PARCE QUE LE DEV FERAIT ROUGIR SA PROPRE
# STORY EN L'IGNORANT. La forme 2 dit « ecris-la au tracker EN `backlog` dans
# le meme geste ». Quatre dispositions du ledger nomment `dn4-40` en forme 2 ;
# elles ont ete ecrites quand elle etait `backlog`, et elle ne l'est plus.
# ⇒ ARBITRAGE RETENU : **la forme 2 contraint l'EXTRACTION, ⛔ pas le statut.**
# Son exigence reelle est celle que la prescription donne elle-meme comme
# motif — « une intention qui ne vit nulle part n'est pas un porteur » : la
# cle doit EXISTER au tracker et y etre VIVANTE. Un porteur qui DEMARRE
# reste un porteur. ⛔ Durcir la forme 2 jusqu'au statut `backlog` ferait
# rougir toute story des qu'elle commence — c'est-a-dire pile quand son
# porteur devient le plus reel.


def _dispo_de(m):
    return {"cle": m.group(1),
            "date": m.group(2),
            "verdict": sans_accents(m.group(3)).upper(),
            "verdict_brut": m.group(3),
            "porteur": m.group(4).strip(),
            "preuve": m.group(5).strip()}


def dispos(e):
    """TOUTES les dispositions de l'entree.

    🔴 CORRECTIF DE REVUE (2026-08-30) : `dispo()` ne rendait que la PREMIERE
    (`.search`). Une seconde ligne de disposition portant un verdict hors
    liste, un porteur bouchon ou une preuve nue etait donc INVISIBLE.
    """
    return [_dispo_de(m) for m in RE_DISPO.finditer(e["txt"])]


def dispo(e):
    """La disposition FAISANT FOI (la premiere), ou None."""
    ds = dispos(e)
    return ds[0] if ds else None


def date_valide(s):
    try:
        datetime.date.fromisoformat(s)
        return True
    except ValueError:
        return False


# 🔴 CORRECTIF DE REVUE (2026-08-30) — UN PORTEUR BOUCHON PASSAIT VERT.
# Le controle ne testait que le VIDE LITTERAL. Mutation mesuree :
#   `RE-HEBERGEE · porteur : —`   ⇒ 15 OK, 0 KO
#   `PORTEE · porteur : TBD`      ⇒ 15 OK, 0 KO
# Or `TBD` est NOMMEMENT interdit par le texte que `dn4-16` a elle-meme ecrit
# dans `step-04-present.md`. La gate laissait donc passer vert ce que le
# producteur qu'elle accompagne declare interdit.
# ⚠️ EXCEPTION ASSUMEE : `CONNAISSANCE` ne designe AUCUN travail — c'est le
# motif meme du 5e verdict. Son porteur vaut `—` par construction (37 entrees
# au 2026-08-30), et c'est la seule forme ou un bouchon est LEGITIME.
BOUCHONS = ("tbd", "todo", "n/a", "na", "?", "a decider", "a definir",
            "a voir", "voir plus tard", "a traiter plus tard", "plus tard",
            "a faire", "later", "to be handled later", "-", "--", "...")


def porteur_est_bouchon(p):
    """True si le champ porteur ne DESIGNE personne."""
    s = sans_accents(p.strip()).lower()
    s = re.sub(r"[`'\"*_]", "", s).strip()
    s = s.strip("—–-.").strip()
    return s == "" or s in BOUCHONS


def statut_effectif(cle, tracker):
    """Le statut qui TRANCHE la vivacite d'un porteur.

    🔴 REVUE 2026-09-03 — LA DECISION OWNER N'ETAIT PAS CE QUE LE CODE FAISAIT.
    Decision (3) du 2026-09-02 : « une cle `epic-*` est un porteur legitime,
    VIVANTE TANT QUE L'EPIC EST OUVERT ». Or la gate lisait le statut DE LA CLE,
    ⛔ pas celui de l'epic. Mesure : `epic-dn1` est `done` tandis que
    `epic-dn1-retrospective` est `optional` ⇒ un porteur nommant la
    retrospective d'une epic CLOSE ressortait VIVANT, et aucun mutant ne
    couvrait ce cas (la campagne ne jouait que `epic-dn1` lui-meme).
    ⚠️ Le repli sur le statut de la cle est CONSERVE : une cle `epic-*` dont
    l'epic n'est pas au tracker reste jugee sur elle-meme, ⛔ pas declaree morte
    par absence.
    """
    m = re.match(r"^(epic-dn\d+)(?:-|$)", cle)
    if m and m.group(1) in tracker:
        return tracker[m.group(1)]
    return tracker.get(cle)


def porteurs_a_venir(d):
    """Les cles de story que la disposition designe comme TRAVAIL A VENIR.

    🔴 dn4-40 — LIT LA FORME, ⛔ PLUS LE CHAMP ENTIER. Seules les formes 1 et
    2 DESIGNENT quelqu'un. Les formes 3 (`bloquee par :`), 4 (`clos par :`)
    et 5 (`—`) ne nomment aucun porteur — ⛔ et ce n'est PAS un trou : chacune
    a desormais son propre controle (voir la section 2bis). Une story citee
    dans la PROSE d'un fait bloquant n'est donc plus prise pour un porteur.
    """
    if d["verdict"] not in VERDICTS_A_VENIR:
        return []
    n, arg = forme_du_porteur(d["porteur"])
    if n == 1:
        return [arg]
    if n == 2 and RE_CLE_PORTEUR.match(arg):
        return [arg.lower()]
    # ⛔ Une forme 2 dont l'argument n'est PAS une cle ne rend rien ICI —
    #    elle est attrapee par son controle dedie, ⛔ pas laissee muette.
    return []


# ═══════════════════════════════════════════════════════════════════════════
#  LE TRACKER
# ═══════════════════════════════════════════════════════════════════════════

def lit_tracker(chemin):
    """Rend (statuts, collisions, cles_pleines) — ⛔ jamais None en cas
    d'illisibilite : la
    lecture est faite par l'appelant, qui en fait un CONTROLE.

    🔴 CORRECTIF DE REVUE (2026-08-30) — `setdefault` REPLIAIT DES CLES
    DISTINCTES ET GARDAIT LA PREMIERE. Reel : `dn4-1-tout-branche-tenue-h24`
    (superseded) masquait `dn4-1-donnees-pc-reelles-quatre-cases` (done).
    Inoffensif tant que les deux sont mortes ; mais un futur `dn4-N-a` mort
    devant un `dn4-N-b` vivant rend un faux ROUGE, et l'inverse un faux VERT
    sur un porteur `done` — la seule chose qu'AC6.5 existe pour attraper.
    Les collisions sont desormais REMONTEES et controlees.

    🔴 dn4-40 — 16 CLES ETAIENT SILENCIEUSEMENT IGNOREES. Le repli sur
    `^dn\\d+-\\d+` jetait les 16 cles `epic-*` : la gate annoncait
    « 57 story(s) connue(s) » sur **74 cles reelles**. Une disposition dont le
    porteur etait `epic-dn4` sortait donc « INCONNU », et un mutant plante au
    cadrage passait `24 OK, 0 KO` — a vide. DECISION OWNER (2026-09-02) :
    **une cle `epic-*` est un porteur legitime, vivante tant que l'epic est
    ouvert**, et son statut se lit au tracker comme celui de n'importe qui.

    ⚠️ LES DEUX ECRITURES SONT INDEXEES, et c'est une MESURE, ⛔ pas un
    confort : 143 porteurs sur 151 s'ecrivent en COURT (`dn4-27`), 8 en PLEIN
    (`dn4-40-les-gates-...`). N'indexer que l'une des deux ferait rougir
    l'autre. ⛔ AUCUN repli n'est fabrique pour `epic-*` : `epic-dn4` EXISTE
    deja comme cle pleine, et replier `epic-dn4-retrospective` dessus
    ecraserait un statut par un autre.

    Rend `(statuts, collisions, cles_pleines)`. ⚠️ `len(statuts)` n'est PLUS
    un compte de stories (il porte les deux ecritures) — le compte publie se
    lit sur `cles_pleines`.
    """
    txt = io.open(chemin, encoding="utf-8").read()
    st = {}
    collisions = {}
    pleines = []

    def pose(cle, statut):
        if cle in st and st[cle] != statut:
            collisions.setdefault(cle, [st[cle]]).append(statut)
        st.setdefault(cle, statut)

    for l in txt.split("\n"):
        m = re.match(r"^  ([a-z0-9][a-z0-9\-]*):\s*([a-z\-]+)", l)
        if not m:
            continue
        cle, statut = m.group(1).lower(), m.group(2)
        pleines.append(cle)
        pose(cle, statut)
        # 🔴 REVUE 2026-09-03 — REGRESSION INTRODUITE PAR dn4-40, MESUREE.
        #    L'ecriture d'AVANT (`^(dn\d+-\d+(?:-\d+)?)`, prefixe NON ancre)
        #    indexait la cle INTERMEDIAIRE `dnN-M-P`. La nouvelle exigeait un
        #    match COMPLET ou coupait a deux segments ⇒ un porteur ecrit
        #    `dn4-14-2` sortait « INCONNU », et la story `dn4-14-2-…` ne posait
        #    plus que l'alias `dn4-14`, en COLLISION avec `dn4-14-…`.
        #    ⇒ on pose TOUS les prefixes de forme `dnN-M` et `dnN-M-P`.
        for c in re.finditer(r"^(dn\d+-\d+(?:-\d+)?)(?:-|$)", cle):
            court = c.group(1)
            if court != cle:
                pose(court, statut)
        c2 = re.match(r"^(dn\d+-\d+)-\d+(?:-|$)", cle)
        if c2 and c2.group(1) != cle:
            pose(c2.group(1), statut)
    return st, collisions, pleines


# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
#  LA LISTE AC5.6 DU TRACKER — dn5-7, report (3) de `dn5-5`
#
#  🔴 CE QUE LE REPORT DISAIT, ET CE QUE LA MESURE A TROUVE EN PLUS. Le report
#     notait que « la regle de vivacite est deja mecanisee pour le ledger »
#     mais que la liste AC5.6, deposee au TRACKER, n'etait la population
#     d'AUCUN controle — en ajoutant « les 13 porteurs sont vivants
#     aujourd'hui ». MESURE DU 2026-09-05 : la liste porte **16**
#     designations, dont **UNE EST DEJA MORTE** (l'item 15 designe
#     `dn5-6-…`, passe `done` le 2026-09-05). ⇒ le trou n'est ⛔ pas theorique.
#
#  ⚠️ LA POPULATION SE PREND SUR LA **DESIGNATION**, ⛔ PAS SUR LA MENTION.
#     Le bloc cite `dn4-39` **EN NEGATION** (« ⛔ **PAS `dn4-39-…`** : elle est
#     `done` ⇒ elle ne peut plus rien porter »). Un controle qui compterait
#     toute cle citee rougirait sur du texte JUSTE. La designation est la forme
#     ``⇒ **`cle`**`` — le `⇒` en fait partie.
#
#  ⚠️ L'ANCRAGE EST PAR **CLE**, ⛔ JAMAIS PAR NUMERO DE LIGNE — et c'est le
#     bloc lui-meme qui l'ecrit, apres avoir paye QUATRE ancres de ligne
#     fausses. Le bloc est donc borne par ses DEUX fences `═══`, ⛔ pas par
#     des index.
# ═══════════════════════════════════════════════════════════════════════════

# 🔴 LE LIBELLE EST ECRIT **EN TOUTES LETTRES** DANS CHAQUE `ctrl()`, ⛔ PAS
#    PAR CETTE CONSTANTE — ET C'EST UNE MESURE, ⛔ pas un gout. `dn_sites.py`
#    lit le SOURCE au tokenizer : un second argument qui n'est pas un LITTERAL
#    de chaine sort « illisible » et n'entre dans aucun index. MESURE DU
#    2026-09-05 : passe par la constante, la campagne de `verif_campagne_dn440`
#    rendait `⛔ CIBLE INTROUVABLE AU SOURCE` pour les DEUX mutants neufs, puis
#    `1 controle garde par rien` — un controle livre que RIEN ne gardait, dans
#    la marche qui existe pour compter ca.
# ⇒ La constante ci-dessous ne sert qu'a la PROSE et aux messages.
LIB_AC56 = "tout porteur de la liste AC5.6 du tracker est VIVANT"

RE_AC56_TETE = re.compile(r"AC5\.6")
RE_AC56_FENCE = re.compile(r"^\s*#\s*[═=]{20,}\s*$")
RE_AC56_ITEM = re.compile(r"^\s*#\s+(\d+)\.\s")
RE_AC56_DESIGNATION = re.compile(r"⇒\s*\*\*`([^`]+)`\*\*")


def solde_de(ligne):
    """La date de cloture PORTEE par cette ligne — ⛔ pas celle qu'elle CITE.

    🔴 REVUE DU 2026-09-05 — LA CLOTURE SE LISAIT SUR **TOUT LE BLOC DE
    L'ITEM**, ET UNE SIMPLE MENTION SUFFISAIT A SORTIR UN ITEM DE LA
    POPULATION. Mesure : en injectant dans l'item 7 la tournure que le
    preambule emploie deja (« ⚠️ la ligne 15 est **SOLDEE LE 2026-09-05**,
    voir plus bas. »), l'item 7 passait `close=None` → `close=2026-09-05`,
    son porteur sortait, les designations soumises tombaient de 17 a 16 —
    **et le controle restait `[OK ]`**. C'est « citer le jeton l'ACCORDE »,
    que `designations_de()` gardait deja et que la cloture ne gardait pas.
    ⇒ **UNE CLOTURE CLOT LA DESIGNATION SUR LAQUELLE ELLE EST ECRITE**, et
      elle est soumise a la MEME parite d'accents graves. Une phrase qui
      PARLE de la cloture d'une autre ligne ne clot ⛔ RIEN.
    """
    # ⚠️ LA PARITE SE COMPTE SUR **LA CHAINE OU LE MOTIF A MATCHE**, ⛔ pas sur
    #    l'originale : `sans_accents().upper()` peut decaler un index, et un
    #    index decale ferait juger la parite au mauvais endroit.
    plat = sans_accents(ligne).upper()
    m = RE_AC56_SOLDE.search(plat)
    if not m:
        return None
    # ⚠️ MEME GARDE QUE LA DESIGNATION : dans un code span, c'est une CITATION.
    if plat[:m.start()].count("`") % 2:
        return None
    return m.group(1)


def designations_de(ligne):
    """Les `(debut, fin, cle)` DESIGNEES par une ligne — ⛔ pas celles qu'elle
    CITE.

    🔴 MESURE DU 2026-09-05, ET C'EST LE MOTIF LE PLUS PAYE DE CE DEPOT :
    « citer le jeton l'ACCORDE ». Le preambule du bloc AC5.6 explique le
    mecanisme et doit donc ECRIRE la forme — il porte
    ``lit les `⇒ **`cle`**` de ce bloc``. Sans cette garde, la gate lisait un
    porteur nomme `cle`, le declarait INCONNU DU TRACKER, et rougissait sur
    une phrase PARFAITEMENT JUSTE.
    ⇒ LA REGLE : une occurrence a l'INTERIEUR d'un code span n'est pas une
      designation. Elle se decide a la PARITE des accents graves qui la
      precedent sur la ligne — impair ⇒ on est DANS un span.
    ⛔ Ce n'est ⛔ pas une liste d'exclusion : la garde est structurelle et vaut
      pour tout auteur futur, ⛔ pas pour la phrase d'ici.
    """
    out = []
    for m in RE_AC56_DESIGNATION.finditer(ligne):
        if ligne[:m.start()].count("`") % 2:
            continue
        out.append((m.start(1), m.end(1), m.group(1)))
    return out
# ⚠️ UNE LIGNE CLOSE EST UNE LIGNE **DATEE**. `SOLDEE` sans date ne clot rien :
#    ce serait exactement le « porteur mort invisible » sous un autre nom.
RE_AC56_SOLDE = re.compile(r"SOLDEE?\s+LE\s+(\d{4}-\d{2}-\d{2})")


def bloc_ac56(txt):
    """Le CORPS de la liste AC5.6 du tracker, borne par ses deux fences.

    Rend `(lignes, offset, None)` ou `(None, None, motif)` — ⛔ jamais une
    liste vide qui se lirait comme « tout va bien » : une structure illisible
    est un MOTIF, et l'appelant en fait un KO.

    `offset` est l'index, DANS LE FICHIER, de la 1re ligne du corps. Il est
    rendu pour que `verif_campagne_dn440.py` n'ait ⛔ PAS a recopier ce
    bornage : une constante a UN proprietaire, et un bornage recopie ne suit
    pas son original.

    🔴 REVUE DU 2026-09-05 — LES DEUX HYPOTHESES ETAIENT PRISES SANS ETRE
    VERIFIEES : *(i)* plusieurs en-tetes `AC5.6`+`LISTE` ⇒ seul `tetes[0]`
    servait, en silence ; *(ii)* une fence ajoutee DANS la liste ⇒ le corps lu
    s'arretait avant, et les items du dessous quittaient la population **sans
    motif et sans KO**. Le cas (ii) se voit desormais au controle de
    CONTIGUITE des numeros, chez l'appelant.
    """
    lig = txt.split("\n")
    # 🔴 L'EN-TETE SE RECONNAIT A SA **STRUCTURE**, ⛔ PAS A SES MOTS. Mesure du
    #    2026-09-05 : « une ligne de commentaire qui porte `AC5.6` et `LISTE` »
    #    matchait **SIX** lignes — la vraie, et cinq lignes de PROSE qui parlent
    #    de la liste (dont celles que `dn5-7` vient d'ecrire). Le bloc s'ouvre
    #    par `fence / en-tete / … / fence` : l'en-tete est donc une ligne de
    #    commentaire portant `AC5.6` et **PRECEDEE D'UNE FENCE**. Une phrase qui
    #    PARLE de la liste n'est jamais precedee d'une fence.
    tetes = [i for i, l in enumerate(lig)
             if l.lstrip().startswith("#") and RE_AC56_TETE.search(l)
             and i > 0 and RE_AC56_FENCE.match(lig[i - 1])]
    if not tetes:
        return None, None, ("aucun en-tete `AC5.6` PRECEDE D'UNE FENCE dans"
                            " %s" % REL_TRACKER)
    if len(tetes) > 1:
        return None, None, ("%d en-tetes `AC5.6` (lignes %s) — le"
                            " bornage n'est plus DECIDABLE, et en choisir un"
                            " en silence ferait sortir l'autre liste de la"
                            " population"
                            % (len(tetes),
                               ", ".join(str(t + 1) for t in tetes)))
    i0 = tetes[0]
    fences = [j for j in range(i0, len(lig)) if RE_AC56_FENCE.match(lig[j])]
    if len(fences) < 2:
        return None, None, ("l'en-tete AC5.6 est la mais le bloc n'est pas"
                            " BORNE par deux fences `═══` (vu : %d)"
                            % len(fences))
    return lig[fences[0] + 1:fences[1]], fences[0] + 1, None


def items_ac56(corps):
    """Les ITEMS de la liste AC5.6 : `[{numero, debut, fin, cles, close_le}]`.

    🔴 LA CLOTURE SE LIT SUR L'**ITEM**, ⛔ PAS SUR LA LIGNE — et c'est une
    faute que ce controle a faite avant d'etre livre. Une ligne de liste tient
    sur PLUSIEURS lignes de commentaire, et la mention de solde n'est pas sur
    la meme ligne que la designation `⇒ **`cle`**`. Lu ligne a ligne, un item
    CLOS ET DATE ressortait encore soumis a la vivacite ⇒ un FAUX ROUGE que
    rien n'aurait pu eteindre.
    ⚠️ `debut`/`fin` sont des index DANS `corps`, ⛔ pas dans le fichier : ils
    servent au mutant de `verif_campagne_dn440.py`, qui ajoute son propre
    decalage. Un index de fichier deriverait a la premiere ecriture en amont —
    le piege que ce bloc du tracker ecrit lui-meme avoir paye quatre fois.
    """
    bornes = [i for i, l in enumerate(corps) if RE_AC56_ITEM.match(l)]
    blocs = []
    if not bornes:
        blocs.append(("preambule", 0, len(corps)))
    else:
        if bornes[0] > 0:
            blocs.append(("preambule", 0, bornes[0]))
        for k, i in enumerate(bornes):
            fin = bornes[k + 1] if k + 1 < len(bornes) else len(corps)
            blocs.append((RE_AC56_ITEM.match(corps[i]).group(1), i, fin))
    out = []
    for num, deb, fin in blocs:
        cles = [(j, d0, d1, cle, solde_de(corps[j]))
                for j in range(deb, fin)
                for d0, d1, cle in designations_de(corps[j])]
        sautees = sum(len(RE_AC56_DESIGNATION.findall(corps[j]))
                      - len(designations_de(corps[j]))
                      for j in range(deb, fin))
        out.append({"numero": num, "debut": deb, "fin": fin, "cles": cles,
                    "sautees": sautees})
    return out


def imprime_convention():
    print("\n── LA CONVENTION QUE CE SCRIPT IMPLEMENTE (AC1.3) ────────────────")
    print("   (1) entree   = puce `^- ` de PREMIER niveau, en section"
          " `## Deferred from:`")
    print("       (les puces indentees sont des CONTINUATIONS — c'est cette regle-la"
          " qui a separe 240 de 258 au cadrage)")
    print("   (2) DeskNode = tag `[DeskNode]` EN TETE DE PUCE OU"
          " `dnN-M`/`desknode` au titre de section")
    print("       (⛔ plus en sous-chaine du texte absorbe : une entree KidSat"
          " qui CITE le tag basculait la frontiere)")
    print("   (3) ouverte  = la puce ne commence PAS par `✅`")
    print("       ⚠️ une entree arbitree `CLOSE` reste OUVERTE au sens du compte")
    print("   (4) marqueur = premier glyphe EN TETE de puce (⛔ pas ailleurs"
          " dans la ligne)")
    print("   ⚠️ (1) ne distingue PAS une puce de constat d'une puce de PROSE")
    print("       sous une rubrique `###` — sous-compte ci-dessous, ⛔ non")
    print("       redefini : rebouger le perimetre invaliderait le manifeste.")


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--cockpit", default=COCKPIT_DEFAUT)
    ap.add_argument("--compte", action="store_true")
    ap.add_argument("--manifeste", action="store_true")
    ap.add_argument("--sortie", default=None)
    # dn4-39 / AC39.5 — ecrit le tableau EN PLACE, entre les bornes du §9.
    ap.add_argument("--en-place", dest="en_place", action="store_true",
                    help="reecrit le §9 du manifeste ENTRE SES BORNES "
                         "(exige --manifeste ; s'exclut de --sortie)")
    a = ap.parse_args()

    # 🔴 CORRECTIF DE REVUE (2026-08-30) — LES DRAPEAUX SE CONTREDISAIENT EN
    # SILENCE. `--compte --manifeste` rendait 0 sans emettre de table (la
    # branche `--compte` sortait la premiere) et `--sortie` sans `--manifeste`
    # n'ecrivait rien sans le dire : une chaine de regeneration produisait
    # zero octet en croyant avoir reussi.
    if a.compte and a.manifeste:
        ap.error("--compte et --manifeste s'excluent (l'un compte, l'autre emet)")
    if a.sortie and not a.manifeste:
        ap.error("--sortie exige --manifeste (rien d'autre n'ecrit de fichier)")
    # dn4-39 — les memes gardes que ci-dessus, pour le meme motif : deux
    # drapeaux qui se contredisent en silence produisent un fichier vide en
    # croyant avoir reussi.
    if a.en_place and not a.manifeste:
        ap.error("--en-place exige --manifeste")
    if a.en_place and a.sortie:
        ap.error("--en-place et --sortie s'excluent (l'un ecrit le manifeste "
                 "a sa place, l'autre un fichier a part)")

    print("=" * 78)
    print("dn4-16 / AC6 — CHAQUE ENTREE OUVERTE PORTE UN VERDICT ET UN PORTEUR")
    print("=" * 78)
    print("\ndepot code    : %s" % DESKNODE)
    print("depot cockpit : %s" % a.cockpit)

    # ── 0. LES DEUX DEPOTS (AC6.7) — ⛔ jamais un skip silencieux ────────────
    print("\n── 0. LES DEUX DEPOTS SONT LA (AC6.7) ────────────────────────────")
    # 🔴 CORRECTIF DE REVUE (2026-08-30) — CE CONTROLE ETAIT UNE TAUTOLOGIE.
    # `DESKNODE = dirname(dirname(__file__))` : si le script tourne, le
    # repertoire existe. Un des « 15 OK » etait structurellement incapable
    # d'etre autre chose — dans une story dont la lecon est qu'un
    # `N OK / 0 KO` peut epingler du FAUX. On verifie desormais que c'est
    # bien LE depot desknode, ⛔ pas n'importe quel parent.
    temoins = [os.path.join(DESKNODE, x) for x in ("firmware", "tools")]
    dn_ok = ctrl(all(os.path.isdir(x) for x in temoins),
                 "le depot code est le depot DESKNODE",
                 "firmware/ + tools/ presents",
                 "⛔ %s ne porte pas firmware/ + tools/ — script deplace ?"
                 % DESKNODE[-46:])
    # 🔴 dn4-39 — LE COCKPIT, LE LEDGER ET LE TRACKER SONT DES **PREREQUIS**,
    #    ⛔ PAS DES CONTROLES. Leur absence ne dit rien du code : elle dit que la
    #    gate n'a pas son terrain. ⚠️ `dn_ok`, LUI, RESTE UN CONTROLE : « le
    #    depot code est le depot DESKNODE » est une propriete du code, et son
    #    echec reste un ROUGE.
    p_led = os.path.join(a.cockpit, REL_LEDGER)
    p_trk = os.path.join(a.cockpit, REL_TRACKER)
    manquants = []
    if not os.path.isdir(a.cockpit):
        manquants.append("le depot cockpit : %s" % a.cockpit)
    else:
        if not os.path.isfile(p_led):
            manquants.append("le ledger : %s" % REL_LEDGER)
        if not os.path.isfile(p_trk):
            manquants.append("le tracker : %s" % REL_TRACKER)
    if manquants:
        # ⛔ Un VRAI defaut l'emporte : si `dn_ok` est deja tombe, c'est ROUGE.
        if not dn_ok:
            print("\n" + "=" * 78)
            print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
            print("⛔ ARRET : le depot code n'est pas le depot DESKNODE.")
            print("=" * 78)
            return 1
        print("  [PREREQUIS ABSENT] le cockpit de planification n'est pas la")
        for m in manquants:
            print("      manque : %s" % m)
        print("      MOTIF : le cockpit est un depot PRIVE de planification,")
        print("              ⛔ jamais clone a cote du code. Sans lui il n'y a")
        print("              ni ledger ni tracker a confronter.")
        print("      REMEDE : `--cockpit <chemin>` si le depot est ailleurs.")
        print("      ⛔ CE N'EST PAS UN VERDICT SUR LE CODE, et ⛔ pas un skip :")
        print("         rc=%d, declare dans la table NON_JOUABLES de"
              " tools/run_gates.sh." % RC_PREREQUIS)
        return RC_PREREQUIS
    ctrl(True, "le depot cockpit est atteignable", a.cockpit[-58:])
    ctrl(True, "le ledger est present", REL_LEDGER)
    ctrl(True, "le tracker est present", REL_TRACKER)
    if not dn_ok:
        print("\n" + "=" * 78)
        print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
        print("⛔ ARRET : le depot code n'est pas le depot DESKNODE.")
        print("=" * 78)
        return 1

    # 🔴 CORRECTIF DE REVUE (2026-08-30) — « est lisible » ne testait que
    # `isfile`, jamais la LECTURE ni l'ENCODAGE ; et `errors="replace"`
    # transformait un ledger latin-1 en U+FFFD, si bien que la gate
    # diagnostiquait « SANS DISPOSITION » au lieu de « le ledger n'est pas
    # UTF-8 ». Le vrai motif est desormais nomme.
    try:
        texte = io.open(p_led, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as x:
        ctrl(False, "le ledger se LIT en UTF-8", "", "⛔ %s" % x)
        print("\n⛔ ARRET : le ledger est illisible. ⛔ JAMAIS un skip.")
        return 1
    ctrl(True, "le ledger se LIT en UTF-8", "%d caractere(s)" % len(texte))
    try:
        tracker, collisions_trk, cles_trk = lit_tracker(p_trk)
        # dn5-7 / REVUE — LE TEXTE DU TRACKER EST LU **SOUS LA MEME GARDE**.
        # ⛔ Une seconde lecture nue ici ferait un Traceback SANS ligne
        #    `BILAN` si le fichier changeait entre les deux — le defaut exact
        #    que ce dossier traque.
        txt_trk = io.open(p_trk, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as x:
        ctrl(False, "le tracker se LIT en UTF-8", "", "⛔ %s" % x)
        print("\n⛔ ARRET : le tracker est illisible. ⛔ JAMAIS un skip.")
        return 1
    ctrl(True, "le tracker se LIT en UTF-8",
         "%d cle(s) au tracker" % len(cles_trk))

    # >>> DN8-REGION — LE CONTROLE DE PARSE DU TRACKER (dn8-1 / AC8.1.2).
    #     ⛔ UN SEUL controle est ajoute a cette gate, et c'est l'EXCEPTION
    #     NOMMEE a la frontiere de `epic-dn8` : `NFR14` designe le tracker
    #     comme « le premier sujet de ce garde-fou ». ⛔ Cette gate n'est PAS
    #     le depotoir des controles neufs de `dn8` — les trois autres vivent
    #     dans `tools/verif_harnais_dn81.py`.
    #
    # 🔴 CE QU'IL TIENT, ET QUE `lit_tracker` NE PEUT PAS TENIR : `lit_tracker`
    #    apparie `^  ([a-z0-9][a-z0-9\-]*):\s*([a-z\-]+)` LIGNE A LIGNE. Une
    #    cle re-indentee SORT DE LA POPULATION sans un mot — mesure du
    #    2026-09-11 : 101 cles vues avant, **100 apres**, `35 OK / 0 KO` dans
    #    les deux cas. Le balayage ne peut pas voir ce qu'il ne balaie plus.
    # ⇒ LE CONTROLE VISE SON ECHEC **NOMME** : il compare l'ensemble des cles
    #   que le PARSEUR trouve dans `development_status` a celles que le
    #   BALAYAGE a vues. Une cle que le parseur connait et que le balayage a
    #   perdue est un KO — c'est exactement la classe de defaut que `dn4-40` a
    #   payee (16 cles `epic-*` silencieusement ignorees).
    # ⚠️ LA COMPARAISON EST **A SENS UNIQUE**, ET C'EST DELIBERE : le balayage
    #    ramasse toute ligne a 2 espaces, y compris celle d'une FUTURE section
    #    voisine. Exiger l'egalite ferait rougir le jour ou quelqu'un ajoute
    #    une section — un faux rouge, ⛔ pas un defaut. Le sens qui compte est
    #    `parseur ⇒ balayage`.
    if not _YAML:
        print("  [NON JOUE] le tracker se PARSE en YAML (%s)" % REL_TRACKER)
        print("      %s" % (AVEUGLEMENT_YAML % _YAML_MOTIF))
    else:
        _ds, _err = None, ""
        try:
            _doc = yaml.safe_load(txt_trk)
            _ds = (_doc or {}).get("development_status")
        except Exception as _e:                          # noqa: BLE001
            # ⛔ L'ERREUR DU PARSEUR EST **CITEE**, ⛔ pas avalee : c'est elle
            #    qui dit OU le fichier casse, et c'est la seule chose qu'un
            #    balayage textuel ne saura jamais produire.
            _err = "%s: %s" % (type(_e).__name__,
                               " ".join(str(_e).split())[:150])
        if _err:
            _detail = "⛔ LE TRACKER NE SE PARSE PAS — %s" % _err
        elif not isinstance(_ds, dict) or not _ds:
            _detail = ("⛔ `development_status` ABSENT ou VIDE dans %s — le "
                       "tracker se parse mais n'arbitre plus rien"
                       % REL_TRACKER)
        else:
            _perdues = sorted(set(_ds) - set(cles_trk))
            if _perdues:
                _detail = ("⛔ %d CLE(S) VUE(S) PAR LE PARSEUR ET PERDUE(S) "
                           "PAR LE BALAYAGE : %s"
                           % (len(_perdues), ", ".join(_perdues[:6])))
            else:
                _detail = ("development_status : %d cle(s), toutes vues aussi "
                           "par le balayage" % len(_ds))
        ctrl(not _err and isinstance(_ds, dict) and bool(_ds)
             and not (set(_ds) - set(cles_trk)),
             "le tracker se PARSE en YAML", _detail, _detail)
    # <<< DN8-REGION — fin de la region ecrite par dn8 (controle de parse)

    # ── 1. LE COMPTE, PRODUIT ICI (AC1.2 / AC6.3) ───────────────────────────
    imprime_convention()
    sections = decoupe(texte)
    toutes = [e for s in sections for e in s["entrees"]]
    dn = [e for e in toutes if est_desknode(e)]
    ouvertes = [e for e in dn if est_ouverte(e)]
    sec_dn = [s for s in sections
              if re.search(r"\bdn\d|desknode", s["titre"], re.I)]

    # dn4-40 — les ancres du §9, DERIVEES DU CONTENU (decision owner (b)).
    _ANCRES.clear()
    _ANCRES.update(ancres(ouvertes))

    print("\n── 1. LE COMPTE — ⛔ AUCUN CHIFFRE N'EST RECOPIE (AC1.2) ──────────")
    print("     ledger              : %s (%d lignes)"
          % (REL_LEDGER, texte.count("\n") + 1))
    print("     sections            : %4d   dont DeskNode : %d (%.0f %%)"
          % (len(sections), len(sec_dn), 100.0 * len(sec_dn) / max(1, len(sections))))
    print("     entrees             : %4d   dont DeskNode : %d (%.0f %%)"
          % (len(toutes), len(dn), 100.0 * len(dn) / max(1, len(toutes))))
    print("     DeskNode OUVERTES   : %4d   <= LE PERIMETRE DE CETTE GATE"
          % len(ouvertes))
    print("     KidSat (hors champ) : %4d" % (len(toutes) - len(dn)))

    hist = {}
    for e in ouvertes:
        hist[marqueur(e)] = hist.get(marqueur(e), 0) + 1
    print("     marqueurs (regle 4) : %s"
          % "  ".join("%s %d" % (k, v)
                      for k, v in sorted(hist.items(), key=lambda x: -x[1])))
    # 🔴 dn4-40 — L'ANCRE DOIT DESIGNER UNE SEULE ENTREE, SINON ELLE NE
    #    REMPLACE PAS LE NUMERO DE LIGNE : elle le remplace MAL.
    _vues = {}
    for e in ouvertes:
        _vues.setdefault(_ANCRES[id(e)], []).append(e["ligne"])
    _coll = {k: v for k, v in _vues.items() if len(v) > 1}
    ctrl(not _coll,
         "chaque ancre du §9 designe UNE seule entree",
         "%d ancre(s) distincte(s) pour %d entree(s) — derivees du CONTENU"
         % (len(_vues), len(ouvertes)),
         "⛔ %d COLLISION(S) : %s"
         % (len(_coll), ", ".join("%s→l.%s" % (k, v) for k, v in
                                  list(_coll.items())[:4])))
    ctrl(len(ouvertes) > 0, "le perimetre n'est pas vide",
         "%d entree(s) ouverte(s)" % len(ouvertes),
         "⛔ AUCUNE entree ouverte — ledger vide ?")

    # 🔴 CORRECTIF DE REVUE (2026-08-30) — `MARQUEURS` EST UNE LISTE FERMEE :
    # un glyphe de tete hors liste (`⏳`, `⏸️`) tombait dans « (sans) » et
    # faussait l'histogramme PUBLIE, sans que rien ne le signale.
    inconnus_m = []
    for e in ouvertes:
        tete = e["tete"][2:].lstrip()
        tete = re.sub(r"^\*\*", "", tete)
        tete = re.sub(r"^\[DeskNode\]\s*", "", tete).lstrip()
        tete = re.sub(r"^\*\*", "", tete).lstrip()
        if tete[:1] and unicodedata.category(tete[:1]) == "So" \
                and marqueur(e) == "(sans)":
            inconnus_m.append((e, tete[:2]))
    ctrl(not inconnus_m, "aucun marqueur de tete n'est HORS LISTE",
         "%d marqueur(s) connu(s)" % len(MARQUEURS),
         "⛔ %d HORS LISTE : %s"
         % (len(inconnus_m),
            ", ".join("l.%d `%s`" % (e["ligne"], m) for e, m in inconnus_m)))

    # ⚠️ LES DEUX SOUS-COMPTES DECLARES (voir l'en-tete). Ils ne changent PAS
    # le perimetre — les redefinir invaliderait le manifeste et les comptes de
    # porteurs. Ils le rendent VISIBLE, ce que l'absence de sous-compte
    # empechait.
    sous_rubrique = [e for e in ouvertes if e.get("rubrique")]
    soldees_hist = [e for e in ouvertes if sous_marque_de_solde(e)]
    print("     ⚠️ dont sous rubrique `###` : %d (prose narrative possible)"
          % len(sous_rubrique))
    print("     ⚠️ dont marquees SOLDE/~~ .. ~~ : %d (closes par le depot,"
          " gardees au compte)" % len(soldees_hist))

    # ── mode COMPTE SEUL ────────────────────────────────────────────────────
    if a.compte:
        print("\n" + "=" * 78)
        print("MODE --compte : aucune disposition n'est exigee.")
        print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
        print("=" * 78)
        return 1 if ko_total[0] else 0

    # ── mode MANIFESTE ──────────────────────────────────────────────────────
    if a.manifeste and a.en_place:
        # dn4-39 / AC39.5.a — REECRITURE EN PLACE, ENTRE LES BORNES.
        p_man = os.path.join(a.cockpit, REL_MANIFESTE)
        try:
            src = io.open(p_man, encoding="utf-8", newline="").read()
        except (OSError, UnicodeDecodeError) as x:
            ctrl(False, "le manifeste se LIT", "", "⛔ %s" % x)
            return 1
        # 🔴 REVUE 2026-09-02 — `find()` PRENAIT LA PREMIERE OCCURRENCE ET RIEN
        #    NE COMPTAIT LES DOUBLONS. Mesure : UNE ligne de documentation citant
        #    la borne verbatim, inseree 300 lignes plus haut — le geste le plus
        #    naturel de ce depot — faisait passer le manifeste de 661 a 352
        #    lignes. Les sections 4, 5, 6, 7, 7 bis, 8 et 8 bis EFFACEES, la
        #    sortie annoncant « §9 REECRIT EN PLACE ⛔ Aucun copier-coller », et
        #    LA GATE REJOUEE DERRIERE RENDANT 23 OK / 0 KO : la destruction etait
        #    invisible a l'instrument cense garder ce fichier.
        #    ⚠️ AGGRAVANT : le message de KO ci-dessous IMPRIME les deux bornes
        #       verbatim — coller cette sortie dans le document ARME le piege.
        #    ⇒ on exige UNE seule occurrence de chaque borne, et on echoue FERME.
        n_deb, n_fin = src.count(BORNE_DEBUT), src.count(BORNE_FIN)
        if n_deb != 1 or n_fin != 1:
            ctrl(False, "chaque borne du §9 apparait EXACTEMENT une fois", "",
                 "⛔ borne DEBUT vue %d fois, borne FIN vue %d fois" % (n_deb, n_fin))
            print("\n     ⛔ ARRET : ⛔ RIEN N'A ETE ECRIT.")
            print("        Une borne en double ferait ecrire entre la MAUVAISE paire")
            print("        et EFFACERAIT tout ce qui se trouve entre les deux — mesure")
            print("        le 2026-09-02 : 661 lignes ⇒ 352, en annoncant un succes.")
            print("        ⇒ ne citer les bornes NULLE PART ailleurs dans ce fichier.")
            return 1
        i = src.find(BORNE_DEBUT)
        j = src.find(BORNE_FIN)
        # ⛔ ECHEC FERME, avec le remede : sans bornes on ne devine pas ou
        #    ecrire, et ecrire au jugé serait pire que ne rien faire.
        if i < 0 or j < 0 or j < i:
            ctrl(False, "le §9 porte ses DEUX bornes, dans l'ordre",
                 "", "⛔ bornes absentes ou inversees dans %s" % REL_MANIFESTE)
            print("\n     ⛔ ARRET : poser les deux bornes autour du tableau du §9 :")
            print("        %s" % BORNE_DEBUT)
            print("        %s" % BORNE_FIN)
            print("     ⛔ ⛔ ⛔ ET SURTOUT PAS un ancrage par NUMERO DE LIGNE :")
            print("        c'est precisement le defaut que cette commande solde.")
            return 1
        table = EN_TETE_MANIFESTE
        table += "".join(ligne_manifeste(e) + "\n" for e in ouvertes)
        # ⛔ FILET DE NON-REGRESSION (revue 2026-09-02). Le mode rendait la main
        #    AVANT les sections 2 a 5 : il reecrivait donc le §9 a partir
        #    d'entrees dont ni la disposition, ni le verdict, ni le porteur
        #    n'avaient ete controles. Et `ctrl(len(ouvertes) > 0, ...)` n'ARRETE
        #    pas : un ledger restructure ou tronque aurait remplace les 266
        #    lignes par un tableau VIDE, sans confirmation.
        if not ouvertes:
            ctrl(False, "le ledger rend au moins une entree ouverte", "",
                 "⛔ 0 entree lue — ⛔ RIEN N'A ETE ECRIT")
            print("\n     ⛔ ARRET : ecrire un tableau VIDE effacerait le §9 en entier.")
            print("        Le ledger est-il au bon chemin, et sa structure intacte ?")
            return 1
        # ⛔ Une ligne generee qui contiendrait une borne casserait le prochain
        #    tir (la borne tomberait DANS le tableau) : on refuse de l'ecrire.
        if BORNE_DEBUT in table or BORNE_FIN in table:
            ctrl(False, "aucune ligne generee ne contient une borne", "",
                 "⛔ une entree du ledger cite une borne — ⛔ RIEN N'A ETE ECRIT")
            return 1
        neuf = src[:i + len(BORNE_DEBUT)] + "\n\n" + table + "\n" + src[j:]
        if neuf == src:
            print("\n     §9 DEJA d'accord : %d ligne(s), rien a ecrire."
                  % len(ouvertes))
            return 1 if ko_total[0] else 0
        # ⛔ ECRITURE ATOMIQUE (revue 2026-09-02). L'ancienne forme tronquait
        #    puis ecrivait, sans temporaire ni `rename`, sans `close()` explicite
        #    et sans sauvegarde : une interruption ou un disque plein laissait le
        #    manifeste TRONQUE — et la troncature emporte la borne de FIN, qui
        #    est en queue de fichier, donc la seule commande de reparation se
        #    detruisait elle-meme.
        #    ⚠️ `newline=""` DES DEUX COTES : sans lui, un manifeste en CRLF etait
        #       reecrit INTEGRALEMENT en LF — un diff de 3 000 lignes pour une
        #       regeneration de 267, invisible dans son propre message de succes.
        tmp = p_man + ".dn439.tmp"
        try:
            with io.open(tmp, "w", encoding="utf-8", newline="") as f:
                f.write(neuf)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, p_man)
        except OSError as x:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            ctrl(False, "le manifeste est inscriptible", "", "⛔ %s" % x)
            return 1
        print("\n     §9 REECRIT EN PLACE : %s" % REL_MANIFESTE)
        print("     %d ligne(s) de tableau, entre les bornes."
              " ⛔ Aucun copier-coller." % len(ouvertes))
        return 1 if ko_total[0] else 0

    if a.manifeste:
        # 🔴 CORRECTIF DE REVUE : sans `--sortie`, la table partait sur stdout
        # APRES le rapport, donc `--manifeste > f.md` produisait un manifeste
        # CORROMPU (rapport + table). Et le mode rendait 0 meme apres un KO.
        try:
            flux = (io.open(a.sortie, "w", encoding="utf-8") if a.sortie
                    else sys.stdout)
        except OSError as x:
            ctrl(False, "la sortie du manifeste est inscriptible",
                 "", "⛔ %s" % x)
            return 1
        # 🔴 REVUE 2026-09-03 — CET EN-TETE DIVERGEAIT DE CELUI D'`--en-place`.
        #    Il annoncait une colonne `ligne` alignee a DROITE au-dessus
        #    d'ancres hexadecimales — c'est-a-dire exactement le repere que le
        #    re-ancrage de dn4-40 SUPPRIME. Les deux chemins produisent le meme
        #    tableau : ils doivent donc produire le meme en-tete, et il n'y en a
        #    plus qu'UNE source.
        flux.write(EN_TETE_MANIFESTE)
        for e in ouvertes:
            flux.write(ligne_manifeste(e) + "\n")
        if a.sortie:
            flux.close()
            print("\n     manifeste ecrit : %s (%d lignes de tableau)"
                  % (a.sortie, len(ouvertes)))
        else:
            print("\n⚠️ table emise sur STDOUT, APRES le rapport ci-dessus."
                  " ⛔ Ne redirige pas : utilise --sortie.", file=sys.stderr)
        return 1 if ko_total[0] else 0

    # ── 2. CHAQUE ENTREE OUVERTE PORTE UNE DISPOSITION (AC6.4) ──────────────
    print("\n── 2. CHAQUE ENTREE OUVERTE PORTE UNE DISPOSITION (AC6.4) ────────")
    sans_dispo = []
    mauvais_verdict = []
    sans_porteur = []
    dates_ko = []
    multi = []
    for e in ouvertes:
        ds = dispos(e)
        if not ds:
            sans_dispo.append(e)
            continue
        if len(ds) > 1:
            multi.append((e, len(ds)))
        # ⚠️ TOUTES les dispositions sont validees, ⛔ plus seulement la 1re.
        for d in ds:
            if d["verdict"] not in VERDICTS:
                mauvais_verdict.append((e, d["verdict_brut"]))
            if not date_valide(d["date"]):
                dates_ko.append((e, d["date"]))
            # `CONNAISSANCE` ne designe aucun travail ⇒ `—` y est ATTENDU.
            if d["verdict"] != "CONNAISSANCE" and porteur_est_bouchon(d["porteur"]):
                sans_porteur.append((e, d["porteur"] or "(vide)"))

    ctrl(not sans_dispo,
         "toute entree ouverte a une ligne de disposition",
         "%d entree(s) arbitree(s)" % len(ouvertes),
         "⛔ %d SANS DISPOSITION : l.%s"
         % (len(sans_dispo), ", l.".join(str(e["ligne"]) for e in sans_dispo)))
    ctrl(not mauvais_verdict,
         "tout verdict est l'un des CINQ",
         " · ".join(VERDICTS),
         "⛔ %d HORS LISTE : %s"
         % (len(mauvais_verdict),
            ", ".join("l.%d `%s`" % (e["ligne"], v)
                      for e, v in mauvais_verdict)))
    # ── L'HISTOGRAMME DES VERDICTS — produit ICI, cite par le manifeste ──────
    hv = {}
    for e in ouvertes:
        d = dispo(e)
        hv[d["verdict_brut"] if d else "⛔ ABSENT"] = \
            hv.get(d["verdict_brut"] if d else "⛔ ABSENT", 0) + 1
    print("     verdicts (AC2.2)    : %s"
          % "  ".join("%s %d" % (k, v)
                      for k, v in sorted(hv.items(), key=lambda x: -x[1])))
    # 🔴 dn4-40 — LE MISLABEL ETAIT DANS L'HISTOGRAMME DE LA GATE ELLE-MEME.
    #    `sum(porteurs.values())` est une somme d'OCCURRENCES ; elle etait
    #    publiee sous l'etiquette « entree(s) ». Une entree qui citait deux
    #    cles y comptait DEUX FOIS. Les deux comptes sont desormais
    #    DISTINCTS et nommes pour ce qu'ils sont.
    porteurs = {}
    entrees_portees = set()
    for e in ouvertes:
        d = dispo(e)
        for cle in porteurs_a_venir(d) if d else []:
            porteurs[cle] = porteurs.get(cle, 0) + 1
            entrees_portees.add(e["ligne"])
    print("     porteurs A VENIR    : %d story(s) distincte(s) · %d designation(s)"
          " · %d entree(s)"
          % (len(porteurs), sum(porteurs.values()), len(entrees_portees)))
    print("       %s" % "  ".join("%s:%d" % (k, v)
                                  for k, v in sorted(porteurs.items(),
                                                     key=lambda x: -x[1])))

    ctrl(not sans_porteur,
         "tout porteur DESIGNE quelqu'un (⛔ ni vide ni bouchon)",
         "aucun bouchon ; `—` admis sur CONNAISSANCE seulement",
         "⛔ %d BOUCHON(S) : %s"
         % (len(sans_porteur),
            ", ".join("l.%d `%s`" % (e["ligne"], p) for e, p in sans_porteur)))
    ctrl(not dates_ko, "toute date de disposition est une date reelle",
         "aucune date invalide",
         "⛔ %d DATE(S) INVALIDE(S) : %s"
         % (len(dates_ko),
            ", ".join("l.%d `%s`" % (e["ligne"], d) for e, d in dates_ko)))
    ctrl(not multi, "une entree porte UNE seule ligne de disposition",
         "aucune entree n'en porte deux",
         "⛔ %d ENTREE(S) MULTI-DISPOSITION : %s"
         % (len(multi),
            ", ".join("l.%d (%d)" % (e["ligne"], n) for e, n in multi)))

    # ── 2bis. LE PORTEUR RELEVE D'UNE DES CINQ FORMES (dn4-40 / AC40.1) ─────
    #
    # 🔴 CETTE SECTION EXISTE PARCE QUE 12 DISPOSITIONS TRAVERSAIENT LA GATE
    #    SANS QU'AUCUN CONTROLE NE LES REGARDE. Elles sont toutes de FORME 3
    #    (`bloquee par : <fait externe>`), toutes LEGITIMES, et l'ancienne
    #    extraction leur rendait zero cle ⇒ les 3 controles de vivacite
    #    tournaient a vide et annoncaient « OK ».
    #    ⇒ L'INVARIANT QUE CETTE SECTION POSE, et qui ⛔ n'est PAS un chiffre :
    #      « aucune disposition a verdict A VENIR ne traverse cette gate sans
    #        etre soumise a au moins un controle. »
    #      Il est VERIFIE ci-dessous, ⛔ pas seulement affirme.
    print("\n── 2bis. LE PORTEUR RELEVE D'UNE DES CINQ FORMES (AC40.1) ────────")
    print("     prescription : docs/bmad/deferred-work-ligne-porteur.md")
    formes = {}
    hors_forme = []
    f2_sans_cle = []
    f3 = []
    f3_muets = []
    f3_cle_nue = []
    f5_hors_connaissance = []
    f4_hors_close = []
    f4_muets = []
    cles_fantomes = []
    soumis = {}
    for e in ouvertes:
        d = dispo(e)
        if d is None:
            continue
        n, arg = forme_du_porteur(d["porteur"])
        formes[n] = formes.get(n, 0) + 1
        avenir = d["verdict"] in VERDICTS_A_VENIR
        if avenir:
            soumis.setdefault(e["ligne"], set())
        if n == 0:
            hors_forme.append((e, d["porteur"]))
            if avenir:
                soumis[e["ligne"]].add("forme")
        elif n == 2:
            if avenir:
                soumis[e["ligne"]].add("forme2")
            if not RE_CLE_PORTEUR.match(arg):
                f2_sans_cle.append((e, arg))
        elif n == 3:
            f3.append((e, arg))
            if avenir:
                soumis[e["ligne"]].add("forme3")
            # 🔴 L'ORDRE DE CES DEUX TESTS EST UN CORRECTIF, ⛔ PAS UN DETAIL.
            #    Ecrits dans l'autre sens, le plancher de longueur avalait le
            #    cas PLUS PRECIS : le mutant `bloquee par : dn4-16` (7
            #    caracteres) sortait « FAIT MUET » au lieu de « PORTEUR
            #    DEGUISE ». La campagne l'a vu rougir — sur le MAUVAIS
            #    controle. ⇒ le cas nomme passe EN PREMIER.
            #
            # 🔴 UN FAIT BLOQUANT QUI SE REDUIT A UNE CLE DE STORY EST UN
            #    PORTEUR DEGUISE : il esquiverait toute la vivacite. ⚠️ Une
            #    story CITEE DANS la prose reste legitime — c'est la
            #    REDUCTION qui est refusee, ⛔ pas la mention. (C'est
            #    exactement le faux rouge qui etait ARME dans le ledger.)
            if RE_CLE_PORTEUR.match(sans_accents(arg).strip(" `*_.")):
                f3_cle_nue.append((e, arg))
            # ⛔ NI VIDE NI BOUCHON : « nomme le fait » est la lettre de la
            #    prescription, et c'est falsifiable. ⚠️ Le `< 8` est un
            #    PLANCHER assume, ⛔ pas une mesure : un fait externe nomme en
            #    moins de 8 caracteres n'est pas nomme. Il ne mord aujourd'hui
            #    sur aucun des 13 champs reels.
            elif porteur_est_bouchon(arg) or len(arg.strip()) < 8:
                f3_muets.append((e, arg))
        elif n == 4:
            if d["verdict"] != "CLOSE":
                f4_hors_close.append((e, d["verdict"]))
            # 🔴 REVUE 2026-09-03 — LA FORME 4 N'ETAIT GARDEE QUE SUR SON
            #    VERDICT, ⛔ JAMAIS SUR SON ARGUMENT. Mesure : `clos par : TBD`,
            #    `clos par :` (vide) et `clos par : a traiter plus tard`
            #    rendaient tous `32 OK, 0 KO`, rc=0 — alors qu'AC40.1.e dit
            #    « TBD, un champ vide … RESTENT des KO » et que la prescription
            #    les range parmi les porteurs INTERDITS, sans distinguer la
            #    forme. La segmentation avait rendu la gate PERMISSIVE
            #    exactement la ou l'AC l'interdit. Meme plancher que la forme 3.
            if porteur_est_bouchon(arg) or len(arg.strip()) < 8:
                f4_muets.append((e, arg))
        elif n == 5:
            if d["verdict"] != "CONNAISSANCE":
                f5_hors_connaissance.append((e, d["verdict"]))
        elif n == 1 and avenir:
            soumis[e["ligne"]].add("forme1")
        if n in (1, 2) and RE_CLE_PORTEUR.match(arg) and arg.lower() not in tracker:
            # 🔴 REVUE 2026-09-03 — SOUS UN VERDICT `CLOSE`/`CONNAISSANCE`, LA
            #    CLE N'ETAIT JAMAIS VERIFIEE : `porteurs_a_venir()` rend []
            #    hors des verdicts A VENIR, et le seul controle d'existence
            #    vivait en aval. Une forme 2 nommant une story qui n'existe
            #    nulle part passait donc VERTE. ⚠️ On verifie l'EXISTENCE pour
            #    tous les verdicts ; ⛔ la VIVACITE reste reservee aux verdicts
            #    A VENIR — exiger qu'un fossoyeur soit vivant serait la
            #    contradiction que la prescription ecarte en toutes lettres.
            cles_fantomes.append((e, arg))
    print("     formes (AC40.1.a)   : %s"
          % "  ".join("%s %d" % (FORME_LIBELLE[k], v)
                      for k, v in sorted(formes.items())))
    ctrl(not hors_forme,
         "tout porteur releve de l'UNE des CINQ formes",
         "%d disposition(s) triee(s), 0 hors forme" % len(ouvertes),
         "⛔ %d HORS FORME : %s"
         % (len(hors_forme),
            ", ".join("l.%d `%s`" % (e["ligne"], p[:34]) for e, p in hors_forme)))
    ctrl(not f2_sans_cle,
         "toute forme 2 `backlog nomme :` nomme UNE cle",
         "%d forme(s) 2, toutes avec cle" % formes.get(2, 0),
         "⛔ %d SANS CLE : %s"
         % (len(f2_sans_cle),
            ", ".join("l.%d `%s`" % (e["ligne"], a[:34]) for e, a in f2_sans_cle)))
    # 🎯 LES DEUX CONTROLES QUI FERMENT LE TROU DES 12 — leur population EST
    #    celle qui ne rendait aucune cle. ⛔ Ils ne « voient » pas : ils
    #    verifient, et un mutant les fait rougir.
    ctrl(not f3_muets,
         "tout `bloquee par :` NOMME un fait (⛔ ni vide ni bouchon)",
         "%d fait(s) bloquant(s) nomme(s)" % len(f3),
         "⛔ %d FAIT(S) MUET(S) : %s"
         % (len(f3_muets),
            ", ".join("l.%d `%s`" % (e["ligne"], a[:34]) for e, a in f3_muets)))
    ctrl(not f3_cle_nue,
         "aucun fait bloquant ne se REDUIT a une cle de story",
         "%d fait(s) examine(s) — une cle nue serait un porteur deguise"
         % len(f3),
         "⛔ %d PORTEUR(S) DEGUISE(S) : %s"
         % (len(f3_cle_nue),
            ", ".join("l.%d `%s`" % (e["ligne"], a[:34]) for e, a in f3_cle_nue)))
    ctrl(not f4_hors_close,
         "la forme 4 `clos par :` ne porte que le verdict CLOSE",
         "%d forme(s) 4" % formes.get(4, 0),
         "⛔ %d HORS CLOSE : %s"
         % (len(f4_hors_close),
            ", ".join("l.%d %s" % (e["ligne"], v) for e, v in f4_hors_close)))
    ctrl(not f4_muets,
         "toute forme 4 `clos par :` NOMME ce qui a clos",
         "%d forme(s) 4, toutes nommees" % formes.get(4, 0),
         "⛔ %d FOSSOYEUR(S) MUET(S) : %s"
         % (len(f4_muets),
            ", ".join("l.%d `%s`" % (e["ligne"], a[:34]) for e, a in f4_muets)))
    ctrl(not cles_fantomes,
         "toute cle de porteur EXISTE au tracker (⛔ tous verdicts)",
         "%d cle(s) nommee(s) en forme 1 ou 2, toutes au tracker"
         % (formes.get(1, 0) + formes.get(2, 0)),
         "⛔ %d CLE(S) FANTOME(S) : %s"
         % (len(cles_fantomes),
            ", ".join("l.%d `%s`" % (e["ligne"], a[:34])
                      for e, a in cles_fantomes)))
    ctrl(not f5_hors_connaissance,
         "la forme 5 `—` est reservee a CONNAISSANCE",
         "%d forme(s) 5" % formes.get(5, 0),
         "⛔ %d HORS CONNAISSANCE : %s"
         % (len(f5_hors_connaissance),
            ", ".join("l.%d %s" % (e["ligne"], v) for e, v in f5_hors_connaissance)))
    # 🔴 L'INVARIANT LUI-MEME, CONTROLE — ⛔ pas un chiffre-cible.
    muettes = [n for n, v in soumis.items() if not v]
    ctrl(not muettes,
         "aucune disposition A VENIR ne traverse la gate sans controle",
         "%d disposition(s) A VENIR, toutes soumises" % len(soumis),
         "⛔ %d MUETTE(S) : l.%s"
         % (len(muettes), ", l.".join(str(x) for x in sorted(muettes))))
    # ⚠️ CONSTAT PUBLIE, ⛔ PAS UN VERDICT — voir les notes de dn4-40 : la
    #    prescription demande aussi « nomme CE QUI LE DEBLOQUERAIT ». Ce
    #    compte est rendu VISIBLE ; il n'est ⛔ pas arme en KO, parce qu'il
    #    condamnerait des entrees que cette story ne porte pas.
    RE_DEBLOC = re.compile(r"debloqu|deblocage|levee?\b|des que|lorsque|quand |"
                           r"une fois|il faut que|attend que|suffit", re.I)
    sans_debl = [e for e, a in f3 if not RE_DEBLOC.search(sans_accents(a))]
    print("     ⚠️ %d des %d faits bloquants ne nomment AUCUN deblocage"
          % (len(sans_debl), len(f3)))
    print("        (constat PUBLIE, ⛔ pas un KO — reporte au tracker)")

    # ── 3. LE PORTEUR EST VIVANT (AC6.5) ────────────────────────────────────
    print("\n── 3. LE PORTEUR EST VIVANT (AC6.5) ──────────────────────────────")
    print("     ⚠️ un `clos par :` designe le PASSE ⇒ non soumis (voir en-tete)")
    morts = []
    inconnus = []
    soumis_vivacite = 0
    for e in ouvertes:
        d = dispo(e)
        if d is None:
            continue
        for cle in porteurs_a_venir(d):
            soumis_vivacite += 1
            if cle not in tracker:
                inconnus.append((e, cle))
                continue
            st = statut_effectif(cle, tracker)
            if st in STATUTS_MORTS:
                morts.append((e, cle, st))
    ctrl(not morts,
         "aucun porteur A VENIR n'est `done`/`superseded`",
         "tracker : %d cle(s), %d porteur(s) soumis"
         % (len(cles_trk), soumis_vivacite),
         "⛔ %d MORT(S) : %s"
         % (len(morts),
            ", ".join("l.%d→%s(%s)" % (e["ligne"], c, s) for e, c, s in morts)))
    ctrl(not inconnus,
         "tout porteur A VENIR existe au tracker",
         "sprint-status-desknode.yaml",
         "⛔ %d INCONNU(S) : %s"
         % (len(inconnus),
            ", ".join("l.%d→%s" % (e["ligne"], c) for e, c in inconnus)))
    # 🔴 CORRECTIF DE REVUE (2026-08-30) — `STATUTS_VIVANTS` N'ETAIT JAMAIS
    # REFERENCE : seuls `done`/`superseded` etaient refuses, donc un statut
    # `cancelled`, `abandoned` ou mal orthographie passait pour VIVANT.
    etranges = []
    for e in ouvertes:
        d = dispo(e)
        if d is None:
            continue
        for cle in porteurs_a_venir(d):
            st = statut_effectif(cle, tracker)
            if st is not None and st not in STATUTS_VIVANTS + STATUTS_MORTS:
                etranges.append((e, cle, st))
    ctrl(not etranges,
         "tout statut de porteur est un statut CONNU",
         "statuts admis : %s" % " · ".join(STATUTS_VIVANTS),
         "⛔ %d STATUT(S) HORS LISTE : %s"
         % (len(etranges),
            ", ".join("l.%d→%s(%s)" % (e["ligne"], c, s) for e, c, s in etranges)))
    # ⚠️ Une collision de prefixe ne fausse le verdict que si les statuts en
    # collision ne sont pas TOUS vivants ou TOUS morts : `dn4-1` replie
    # `superseded` et `done`, deux MORTS — une reference nue `dn4-1` est donc
    # refusee de la meme facon dans les deux cas, et le verdict ne change pas.
    # Ce sont les collisions VIVANT/MORT qui rendent un faux vert.
    ambigues = {k: v for k, v in collisions_trk.items()
                if len({s in STATUTS_MORTS for s in v}) > 1}
    ctrl(not ambigues,
         "aucune collision de cle ne peut CHANGER un verdict",
         "%d cle(s) distincte(s)%s" % (len(cles_trk),
                                       ", %d collision(s) benigne(s)"
                                       % len(collisions_trk) if collisions_trk else ""),
         "⛔ %d COLLISION(S) VIVANT/MORT : %s"
         % (len(ambigues),
            ", ".join("%s=%s" % (k, "/".join(v)) for k, v in ambigues.items())))

    # ── 3-bis. LA LISTE AC5.6 DU **TRACKER** (dn5-7) ────────────────────────
    print("\n── 3-bis. LES PORTEURS DE LA LISTE AC5.6 DU TRACKER (dn5-7) ──────")
    print("     ⚠️ SECONDE POPULATION DE CETTE GATE, ET LA DECLARATION DE")
    print("        PORTEE EN TETE DE FICHIER EST DATEE EN CONSEQUENCE.")
    print("     ⇒ population = la DESIGNATION `⇒ **`cle`**`, ⛔ pas la mention")
    print("        (le bloc cite `dn4-39` EN NEGATION : il ⛔ ne compte pas).")
    # 🔴 dn5-7 / REVUE — LA PORTEE DE CETTE GARDE EST DECLAREE ICI, LA OU ELLE
    #    EST POSEE, ⛔ pas seulement dans le dossier. CETTE GATE EST DECLAREE
    #    `NON_JOUABLE` (rc=4) SANS COCKPIT dans `tools/run_gates.sh`, et ses
    #    DEUX mutants vivent dans `verif_campagne_dn440.py`, `NON_JOUABLE`
    #    aussi ⇒ **NI cette garde NI ses mutants ne s'executent en CI**
    #    (`.github/workflows/gates.yml` n'a pas le cockpit). C'est la MEME
    #    ligne qui fait refuser `epic-dn8` au report (4) ; elle vaut donc
    #    aussi pour la garde construite au report (3), et elle est ECRITE.
    print("     ⚠️ PORTEE DECLAREE : cette gate est `NON_JOUABLE` (rc=4) sans")
    print("        cockpit, et ses mutants aussi ⇒ ⛔ NI cette garde NI ses")
    print("        mutants ne tournent en CI. Elle garde le poste, ⛔ pas la CI.")
    corps56, offset56, motif56 = bloc_ac56(txt_trk)
    if corps56 is None:
        ctrl(False, "tout porteur de la liste AC5.6 du tracker est VIVANT",
             "", "⛔ %s" % motif56)
    else:
        items = items_ac56(corps56)
        morts56, inconnus56, closes56, etranges56, soumis56 = [], [], [], [], 0
        for it in items:
            for _j, _d0, _d1, cle, close_le in it["cles"]:
                if close_le:
                    closes56.append((it["numero"], cle, close_le))
                    continue
                soumis56 += 1
                st = statut_effectif(cle, tracker)
                if st is None:
                    inconnus56.append((it["numero"], cle))
                elif st in STATUTS_MORTS:
                    morts56.append((it["numero"], cle, st))
                elif st not in STATUTS_VIVANTS:
                    # ⇒ MEME TRAITEMENT QU'EN SECTION 3 : un statut hors liste
                    #   (`cancelled`, une faute de frappe) comptait pour VIVANT.
                    etranges56.append((it["numero"], cle, st))
        desig = [c for it in items for c in it["cles"]]
        numeros = [it["numero"] for it in items if it["numero"] != "preambule"]
        # ⇒ LE BLOC EST-IL ENTIER ? Une fence ajoutee DANS la liste tronque le
        #   corps et fait sortir les items du dessous SANS MOTIF.
        attendus = [str(k) for k in range(1, len(numeros) + 1)]
        tronque = [] if numeros == attendus else [
            "⛔ bloc TRONQUE ou renumerote : items lus %s, attendus %s"
            % (",".join(numeros) or "aucun", ",".join(attendus) or "aucun")]
        # ⇒ Un item numerote SANS designation passe vert : la gate sœur
        #   enforce deja « toute entree ouverte a une ligne de disposition ».
        muets = ["item %s" % it["numero"] for it in items
                 if it["numero"] != "preambule" and not it["cles"]]
        sautees = sum(it["sautees"] for it in items)
        print("     ⚠️ une occurrence DANS un code span est une CITATION, ⛔ pas")
        print("        une designation — la garde est la PARITE des accents graves.")
        print("     ⚠️ designation(s) SAUTEE(S) par cette garde : %d" % sautees)
        print("        (⛔ un skip SILENCIEUX ferait disparaitre une vraie")
        print("         designation de la population sans laisser de trace)")
        for item, cle, close_le in closes56:
            print("     [close] item %-10s ⇒ %-52s CLOSE LE %s"
                  % (item, cle[:52], close_le))
        print("     %d item(s), %d designation(s) : %d soumise(s) a la"
              " vivacite, %d close(s) et datee(s)"
              % (len(items), len(desig), soumis56, len(closes56)))
        # 🔴 LE KO **NOMME LA LIGNE ET LA CLE**, ⛔ IL NE PROPOSE PAS DE REMEDE.
        #    Un porteur peut mourir de DEUX facons, et ce controle ⛔ ne peut
        #    pas les distinguer : `done` PARCE QUE LE TRAVAIL EST FAIT (la
        #    ligne se SOLDE) ou `done` AVEC DU TRAVAIL DEBOUT (il faut la
        #    RE-ROUTER vers quelqu'un de vivant). ⇒ il signale, l'humain
        #    tranche.
        # 🔴 REVUE DU 2026-09-05 — LES MOTIFS SE **CONCATENENT**, ⛔ NE
        #    S'ALTERNENT PLUS. Chaines en `if/else`, les INCONNUS
        #    disparaissaient des que des MORTS existaient, alors que la ligne
        #    (3-ter) de la matrice promet qu'ils ⛔ ne sont pas confondus.
        motifs56 = []
        if morts56:
            motifs56.append("⛔ %d MORT(S) : %s"
                            % (len(morts56),
                               ", ".join("item %s→%s(%s)" % (i, c, s)
                                         for i, c, s in morts56)))
        if inconnus56:
            motifs56.append("⛔ %d INCONNU(S) DU TRACKER : %s"
                            % (len(inconnus56),
                               ", ".join("item %s→%s" % (i, c)
                                         for i, c in inconnus56)))
        if etranges56:
            motifs56.append("⛔ %d STATUT(S) HORS LISTE : %s"
                            % (len(etranges56),
                               ", ".join("item %s→%s(%s)" % (i, c, s)
                                         for i, c, s in etranges56)))
        motifs56 += tronque
        if muets:
            motifs56.append("⛔ %d item(s) numerote(s) SANS designation : %s"
                            % (len(muets), ", ".join(muets)))
        # ⇒ LE TEMOIN DE NON-VACUITE COMPTE LES **SOUMISES**, ⛔ pas les
        #   designations : une liste dont TOUT serait solde rendrait
        #   `[OK ] … 0 porteur(s) VIVANT(S)` — vert sur du vide.
        if soumis56 <= 0:
            motifs56.append("⛔ AUCUNE designation SOUMISE a la vivacite"
                            " (%d close(s)) — ⛔ pas vert sur du vide"
                            % len(closes56))
        ctrl(not motifs56,
             "tout porteur de la liste AC5.6 du tracker est VIVANT",
             "%d porteur(s) VIVANT(S) au tracker, %d close(s) et datee(s)"
             % (soumis56, len(closes56)),
             " || ".join(motifs56))

    # ── 4. LA PREUVE EST UN MOTIF, ⛔ PAS UN NUMERO (AC6.6) ──────────────────
    print("\n── 4. LA PREUVE EST UN MOTIF, ⛔ PAS UN NUMERO DE LIGNE (AC6.6) ───")
    print("     motif mesure : 0 adresse sur 192 tombe hors fichier ⇒ un")
    print("     controle de bornes rendrait `192 OK / 0 KO` sur du derive")
    nues = []
    vides = []
    for e in ouvertes:
        d = dispo(e)
        if d is None:
            continue
        if not d["preuve"]:
            vides.append(e)
        elif preuve_est_nue(d["preuve"]):
            nues.append((e, d["preuve"]))
    ctrl(not vides, "tout champ preuve est non vide",
         "aucun champ preuve vide",
         "⛔ %d VIDE(S) : l.%s"
         % (len(vides), ", l.".join(str(e["ligne"]) for e in vides)))
    ctrl(not nues,
         "aucune preuve ne se REDUIT a un `fichier:ligne`",
         "aucune adresse nue (gras, backticks et « voir » compris)",
         "⛔ %d ADRESSE(S) NUE(S) : %s"
         % (len(nues),
            ", ".join("l.%d `%s`" % (e["ligne"], p) for e, p in nues)))

    # ── 5. LE MANIFESTE EXISTE ET CITE CE SCRIPT ────────────────────────────
    print("\n── 5. LE MANIFESTE EXISTE ET NE RECOPIE AUCUN CHIFFRE ────────────")
    p_man = os.path.join(a.cockpit, REL_MANIFESTE)
    man_ok = ctrl(os.path.isfile(p_man), "le manifeste d'arbitrage est livre",
                  REL_MANIFESTE, "⛔ ABSENT : %s" % REL_MANIFESTE)
    if man_ok:
        man = io.open(p_man, encoding="utf-8", errors="replace").read()
        ctrl("verif_ledger_dn416.py" in man,
             "le manifeste cite le script qui produit son compte",
             "⇒ un seul compte, ⛔ pas deux qui divergent",
             "⛔ le manifeste NE CITE PAS le script ⇒ deux comptes qui divergent")
        # 🔴 CORRECTIF DE REVUE (2026-08-30) — LE CONTROLE COMPARAIT UN
        # NOMBRE DE LIGNES. Une ligne FABRIQUEE (`| 9999 | ... | TBD | ... |`)
        # le satisfaisait, et le manifeste livre divergeait DEJA d'une ligne
        # (la 5575, champ `preuve`) sans que rien ne rougisse. On compare
        # desormais chaque ligne a celle que la fabrique produit.
        # 🔴 REVUE 2026-09-02 — LE CONTROLE LISAIT TOUT LE FICHIER, LA COMMANDE
        #    N'EN ECRIT QU'UNE TRANCHE. Une ligne numerotee posee HORS des bornes
        #    (un autre tableau du manifeste dont la 1re cellule est un nombre)
        #    faisait rougir la gate POUR TOUJOURS : la commande repondait « §9
        #    DEJA d'accord » et le rouge ne bougeait pas — une boucle sans issue,
        #    et le « geste manuel de plus » que ce controle est cense solder.
        #    ⇒ LE CONTROLE SE BORNE A CE QUE `--en-place` ECRIT. Hors bornes,
        #      c'est de la prose : ⛔ pas au controle.
        i_b, j_b = man.find(BORNE_DEBUT), man.find(BORNE_FIN)
        if i_b >= 0 and j_b > i_b:
            perimetre = man[i_b + len(BORNE_DEBUT):j_b]
        else:
            perimetre = man   # bornes absentes : on retombe sur l'ancien comportement
        ctrl(i_b >= 0 and j_b > i_b,
             "le §9 porte ses deux bornes (le controle se borne a elles)",
             "bornes vues aux offsets %d et %d" % (i_b, j_b),
             "⛔ bornes absentes ou inversees — le controle retombe sur TOUT le fichier")
        vues = re.findall(r"^\| *[0-9a-f]{8} *\|.*$", perimetre, re.M)
        attendues = [ligne_manifeste(e) for e in ouvertes]
        # 🔴 dn4-40 — LA COMPARAISON S'ANCRE SUR L'ANCRE, ⛔ PLUS SUR LA
        #    POSITION. Poser une ancre stable ne suffisait PAS : le `zip()`
        #    comparait la ligne n du manifeste a l'entree n du ledger. Inserer
        #    UNE entree en amont decalait donc tout, et la mesure restait
        #    « 267 lignes DIVERGENTES sur 267 » — le defaut survivait sous une
        #    autre forme, exactement le risque n°1 de cette story.
        #    ⇒ On indexe les deux cotes PAR ANCRE. Une insertion rend alors
        #      « 1 ABSENTE », ⛔ pas 267 divergentes.
        def _cle(l):
            m = re.match(r"^\| *([0-9a-f]{8}) *\|", l)
            return m.group(1) if m else None
        # 🔴 REVUE 2026-09-03 — LE PASSAGE A L'APPARIEMENT PAR ANCRE AVAIT
        #    RETIRE LA COMPARAISON DES COMPTES, et `setdefault` gardait la
        #    PREMIERE ligne par ancre. Une ligne FABRIQUEE portant l'ancre d'une
        #    ligne existante, inseree APRES elle, ne produisait donc ni absente
        #    ni surnumeraire ⇒ le controle passait VERT en imprimant, dans son
        #    propre detail, « 268 ligne(s) pour 267 entree(s) ». La detection de
        #    falsification dependait de L'ORDRE DES LIGNES. ⇒ les doublons
        #    d'ancre sont collectes, et le compte est de nouveau compare.
        i_vues = {}
        doublons = []
        for l in vues:
            k = _cle(l)
            if k:
                if k in i_vues:
                    doublons.append(k)
                else:
                    i_vues[k] = l.strip()
        i_att = {_cle(l): l.strip() for l in attendues}
        absentes = [k for k in i_att if k not in i_vues]
        surnum = [k for k in i_vues if k not in i_att]
        ctrl(not absentes and not surnum and not doublons
             and len(vues) == len(attendues),
             "le manifeste couvre 100 % des entrees ouvertes (AC2.7)",
             "%d ligne(s) pour %d entree(s), appariees PAR ANCRE"
             % (len(vues), len(attendues)),
             "⛔ %d entree(s) SANS ligne (%s) · %d ligne(s) SANS entree (%s)"
             " · %d ancre(s) EN DOUBLE (%s) · %d ligne(s) pour %d entree(s)"
             % (len(absentes), ", ".join(absentes[:5]) or "—",
                len(surnum), ", ".join(surnum[:5]) or "—",
                len(doublons), ", ".join(sorted(set(doublons))[:5]) or "—",
                len(vues), len(attendues)))
        ecarts = [(i_vues[k], i_att[k]) for k in i_att
                  if k in i_vues and i_vues[k] != i_att[k]]
        ctrl(not ecarts and not absentes and not surnum and not doublons,
             "chaque ligne du manifeste REPRODUIT ce que le script produit",
             "%d ligne(s) identiques au caractere pres" % len(attendues),
             "⛔ %d ligne(s) DIVERGENTE(S) — la 1re : %s"
             % (len(ecarts), (ecarts[0][1][:120] + " …") if ecarts
                else "(appariement incomplet : %d absente(s), %d surnumeraire(s),"
                     " %d ancre(s) en double)"
                     % (len(absentes), len(surnum), len(doublons))))
        # 🔴 dn4-39 / AC39.5.b — LA GATE DIT LA COMMANDE, ⛔ ELLE NE LA JOUE PAS.
        #    Une gate qui repare ce qu'elle mesure ne mesure plus rien.
        if ecarts or doublons or len(vues) != len(attendues):
            print("     ⇒ UNE commande remet le §9 d'accord :")
            print("       %s" % cmd_regen())
            print("       ⛔ La gate ne la joue PAS : elle MESURE. Une gate qui")
            print("          repare ce qu'elle mesure ne mesure plus rien.")

    # ── 6. BILAN ────────────────────────────────────────────────────────────
    print("\n" + "=" * 78)
    print("⚠️ CE QUE CETTE GATE NE SOLDE PAS :")
    print("   · elle EXIGE un verdict, elle ne peut pas juger s'il est JUSTE ;")
    print("   · elle ne valide AUCUNE adresse `fichier:ligne` — par decision ;")
    print("   · elle ignore les %d entrees KidSat, hors perimetre ;"
          % (len(toutes) - len(dn)))
    print("   · elle ne couvre ni `bmad-dev-auto` ni `bmad-quick-dev`, qui")
    print("     ecrivent aussi au ledger par d'autres chemins ;")
    print("   · 🔴 ~~elle ne lit QUE `deferred-work.md`~~ — ⚠️ FAUX DEPUIS LE")
    print("     2026-09-05 (`dn5-7`) : elle lit AUSSI la liste AC5.6 du")
    print("     tracker, comme POPULATION et ⛔ plus seulement pour resoudre")
    print("     un statut. La phrase est DATEE, ⛔ pas effacee ;")
    print("   · 🔴 les 14 fichiers `deferred/*.md` lui sont INVISIBLES : le")
    print("     jour du drain, elle epinglerait VERT un ledger vide de sa")
    print("     substance ;")
    print("   · ⚠️ %d entree(s) ouverte(s) sont sous une rubrique `###` et"
          % len(sous_rubrique))
    print("     peuvent etre de la prose narrative, ⛔ pas des constats ;")
    print("   · ⚠️ %d entree(s) portent une marque de solde du depot"
          % len(soldees_hist))
    print("     (`~~..~~ — SOLDE`, `[SOLDE]`) et restent AU COMPTE, par")
    print("     coherence avec la regle (3) — ⛔ ce n'est pas un oubli.")
    print("=" * 78)
    if ko_total[0]:
        print("⛔ %d ECHEC(S) sur %d controles."
              % (ko_total[0], ok_total[0] + ko_total[0]))
    else:
        print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return 1 if ko_total[0] else 0


if __name__ == "__main__":
    sys.exit(main())

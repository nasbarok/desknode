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

  🔴 ELLE NE LIT QU'UN SEUL FICHIER : `deferred-work.md`. Elle ne regarde
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

DESKNODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COCKPIT_DEFAUT = os.path.expanduser("~/projects/compagnon_project")

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
CMD_REGEN = ("python3 ~/projects/desknode/tools/verif_ledger_dn416.py"
             " --cockpit <cockpit> --manifeste --en-place")

VERDICTS = ("PORTEE", "RE-HEBERGEE", "CLOSE", "BLOQUEE", "CONNAISSANCE")

# Les verdicts qui designent du TRAVAIL A VENIR ⇒ leur porteur doit etre VIVANT.
VERDICTS_A_VENIR = ("PORTEE", "RE-HEBERGEE", "BLOQUEE")

STATUTS_VIVANTS = ("backlog", "in-progress", "ready-for-dev", "review", "blocked")
STATUTS_MORTS = ("done", "superseded")

MARQUEURS = ("🔴", "🟠", "⚪", "🟢", "🟡", "⚠️", "🆕", "🎯", "⚫", "🔵",
             "🧹", "📋", "🗺️", "✅", "⏳", "⏸️")
# ⚠️ `⏳` et `⏸️` AJOUTES A LA REVUE (2026-08-30). Le controle « aucun marqueur
# de tete n'est HORS LISTE », neuf lui aussi, les a fait apparaitre : trois
# entrees (l.3098, l.3617, l.4075) etaient rangees dans « (sans) » et
# faussaient l'histogramme PUBLIE. La liste fermee ne se voyait pas elle-meme.

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
    return "| %d | `%s` | %s | %s | %s | %s | %s |" % (
        e["ligne"], e["sec"][:46], marqueur(e),
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


def porteurs_a_venir(d):
    """Les cles de story que la disposition designe comme TRAVAIL A VENIR.

    ⛔ Un `clos par :` designe le PASSE ⇒ exclu de la vivacite (voir l'en-tete).
    """
    if d["verdict"] not in VERDICTS_A_VENIR:
        return []
    p = d["porteur"]
    if re.match(r"^\s*clos par\s*:", p, re.I):
        return []
    return [x.lower() for x in RE_STORY.findall(p)]


# ═══════════════════════════════════════════════════════════════════════════
#  LE TRACKER
# ═══════════════════════════════════════════════════════════════════════════

def lit_tracker(chemin):
    """Rend (statuts, collisions) — ⛔ jamais None en cas d'illisibilite : la
    lecture est faite par l'appelant, qui en fait un CONTROLE.

    🔴 CORRECTIF DE REVUE (2026-08-30) — `setdefault` REPLIAIT DES CLES
    DISTINCTES ET GARDAIT LA PREMIERE. Reel : `dn4-1-tout-branche-tenue-h24`
    (superseded) masquait `dn4-1-donnees-pc-reelles-quatre-cases` (done).
    Inoffensif tant que les deux sont mortes ; mais un futur `dn4-N-a` mort
    devant un `dn4-N-b` vivant rend un faux ROUGE, et l'inverse un faux VERT
    sur un porteur `done` — la seule chose qu'AC6.5 existe pour attraper.
    Les collisions sont desormais REMONTEES et controlees.
    """
    txt = io.open(chemin, encoding="utf-8").read()
    st = {}
    collisions = {}
    for l in txt.split("\n"):
        m = re.match(r"^  ([a-z0-9\-]+):\s*([a-z\-]+)", l)
        if m:
            c = re.match(r"^(dn\d+-\d+(?:-\d+)?)", m.group(1))
            if c:
                cle = c.group(1).lower()
                if cle in st and st[cle] != m.group(2):
                    collisions.setdefault(cle, [st[cle]]).append(m.group(2))
                st.setdefault(cle, m.group(2))
    return st, collisions


# ═══════════════════════════════════════════════════════════════════════════

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
        tracker, collisions_trk = lit_tracker(p_trk)
    except (OSError, UnicodeDecodeError) as x:
        ctrl(False, "le tracker se LIT en UTF-8", "", "⛔ %s" % x)
        print("\n⛔ ARRET : le tracker est illisible. ⛔ JAMAIS un skip.")
        return 1
    ctrl(True, "le tracker se LIT en UTF-8",
         "%d story(s) connue(s)" % len(tracker))

    # ── 1. LE COMPTE, PRODUIT ICI (AC1.2 / AC6.3) ───────────────────────────
    imprime_convention()
    sections = decoupe(texte)
    toutes = [e for s in sections for e in s["entrees"]]
    dn = [e for e in toutes if est_desknode(e)]
    ouvertes = [e for e in dn if est_ouverte(e)]
    sec_dn = [s for s in sections
              if re.search(r"\bdn\d|desknode", s["titre"], re.I)]

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
            src = io.open(p_man, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError) as x:
            ctrl(False, "le manifeste se LIT", "", "⛔ %s" % x)
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
        table = ("| ligne | section d'origine | marq. | titre court |"
                 " verdict | porteur | preuve |\n"
                 "|---:|---|:-:|---|---|---|---|\n")
        table += "".join(ligne_manifeste(e) + "\n" for e in ouvertes)
        neuf = src[:i + len(BORNE_DEBUT)] + "\n\n" + table + "\n" + src[j:]
        if neuf == src:
            print("\n     §9 DEJA d'accord : %d ligne(s), rien a ecrire."
                  % len(ouvertes))
            return 1 if ko_total[0] else 0
        try:
            io.open(p_man, "w", encoding="utf-8").write(neuf)
        except OSError as x:
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
        flux.write("| ligne | section d'origine | marq. | titre court |"
                   " verdict | porteur | preuve |\n")
        flux.write("|---:|---|:-:|---|---|---|---|\n")
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
    porteurs = {}
    for e in ouvertes:
        d = dispo(e)
        for cle in porteurs_a_venir(d) if d else []:
            porteurs[cle] = porteurs.get(cle, 0) + 1
    print("     porteurs A VENIR    : %d story(s) distincte(s) pour %d entree(s)"
          % (len(porteurs), sum(porteurs.values())))
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

    # ── 3. LE PORTEUR EST VIVANT (AC6.5) ────────────────────────────────────
    print("\n── 3. LE PORTEUR EST VIVANT (AC6.5) ──────────────────────────────")
    print("     ⚠️ un `clos par :` designe le PASSE ⇒ non soumis (voir en-tete)")
    morts = []
    inconnus = []
    for e in ouvertes:
        d = dispo(e)
        if d is None:
            continue
        for cle in porteurs_a_venir(d):
            st = tracker.get(cle)
            if st is None:
                inconnus.append((e, cle))
            elif st in STATUTS_MORTS:
                morts.append((e, cle, st))
    ctrl(not morts,
         "aucun porteur A VENIR n'est `done`/`superseded`",
         "tracker : %d story(s) connue(s)" % len(tracker),
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
            st = tracker.get(cle)
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
         "%d cle(s) distincte(s)%s" % (len(tracker),
                                       ", %d collision(s) benigne(s)"
                                       % len(collisions_trk) if collisions_trk else ""),
         "⛔ %d COLLISION(S) VIVANT/MORT : %s"
         % (len(ambigues),
            ", ".join("%s=%s" % (k, "/".join(v)) for k, v in ambigues.items())))

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
        vues = re.findall(r"^\| *\d+ *\|.*$", man, re.M)
        attendues = [ligne_manifeste(e) for e in ouvertes]
        ctrl(len(vues) == len(attendues),
             "le manifeste couvre 100 % des entrees ouvertes (AC2.7)",
             "%d ligne(s) pour %d entree(s)" % (len(vues), len(attendues)),
             "⛔ %d ligne(s) de tableau pour %d entree(s) ouverte(s)"
             % (len(vues), len(attendues)))
        ecarts = [(v, at) for v, at in zip(vues, attendues) if v.strip() != at.strip()]
        ctrl(not ecarts and len(vues) == len(attendues),
             "chaque ligne du manifeste REPRODUIT ce que le script produit",
             "%d ligne(s) identiques au caractere pres" % len(attendues),
             "⛔ %d ligne(s) DIVERGENTE(S) — la 1re : %s"
             % (len(ecarts), (ecarts[0][1][:120] + " …") if ecarts else "(compte different)"))
        # 🔴 dn4-39 / AC39.5.b — LA GATE DIT LA COMMANDE, ⛔ ELLE NE LA JOUE PAS.
        #    Une gate qui repare ce qu'elle mesure ne mesure plus rien.
        if ecarts or len(vues) != len(attendues):
            print("     ⇒ UNE commande remet le §9 d'accord :")
            print("       %s" % CMD_REGEN)
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
    print("   · 🔴 elle ne lit QUE `deferred-work.md` — les 14 fichiers")
    print("     `deferred/*.md` lui sont INVISIBLES : le jour du drain, elle")
    print("     epinglerait VERT un ledger vide de sa substance ;")
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

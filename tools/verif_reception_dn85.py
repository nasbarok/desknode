#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dn8-5 / AC8.5.1 → AC8.5.5 — LE DEPOT SAIT RECEVOIR, ET CE QUI LE LUI DIT EST
GARDE.

🎯 POURQUOI CETTE GATE EXISTE. Le 2026-09-13, `.github/` ne portait que la
   signature du CLA et deux workflows : un inconnu devait DEVINER comment
   rapporter un bug, et un chercheur n'avait NULLE PART ou envoyer une faille
   — une faille annoncee dans un ticket public est une faille PUBLIEE. La
   marche `dn8-5` pose les formulaires d'issues, le modele de PR, `SECURITY.md`,
   `CODE_OF_CONDUCT.md`, et complete EN PLACE la section de statut de
   `CONTRIBUTING.md`. 🔴 Et AUCUNE gate du depot ne lisait
   `.github/ISSUE_TEMPLATE/` : `verif_licences_dn52.py` ne lit que les
   workflows. ⇒ c'est celle-ci.

── CE QU'ELLE PARSE, ET CE QU'ELLE ⛔ NE VOIT PAS — DECLARE EN PROPRE ───────
   Les trois YAML passent par `yaml.safe_load` (`NFR14`), ⛔ jamais par un
   motif. PyYAML est importe APRES l'analyse des arguments : `--help` et
   `--liste-mutants` repondent `rc=0` sans lui (`verif_licences_dn52.py` (c3)
   les appelle). ⛔ SANS PyYAML, LA GATE ECHOUE FERMEE : (c1) rougit « YAML NON
   LU », chaque controle qui juge un YAML rougit avec lui, et `AVEUGLEMENT_YAML`
   est IMPRIME — ⛔ jamais un vert sur un YAML non lu.
   Les regles confrontees sont celles que la documentation GitHub ECRIT (citees
   mot pour mot dans `mesures/dn8-5/T1-sources-github.md`). Ce qu'aucune regle
   ecrite ne liste, elle ⛔ ne le voit pas, et elle l'IMPRIME a chaque tir
   (`AVEUGLEMENTS`) : la validation reelle de GitHub (mots interdits dans un
   label, labels « trop proches »), le rendu du selecteur d'issues, l'effet de
   `validations.required` (depots PUBLICS seulement), l'activation du
   signalement prive de failles (reglage d'un depot public).
   Les ancres `#fragment` sont calculees depuis les titres ATX, a la maniere de
   GitHub ; le HTML reellement rendu est releve a la main
   (`mesures/dn8-5/T3-rendu-github.txt`).

── LES SEIZE CONTROLES ──────────────────────────────────────────────────────
   (c1)  chaque YAML de `.github/ISSUE_TEMPLATE/` existe et SE PARSE — les
         formulaires sont LUS DANS LE DOSSIER (`*.yml`/`*.yaml` hors
         `config.yml`), ⛔ pas seulement les deux que la marche a ecrits
   (c2)  chaque formulaire du dossier respecte les regles documentees : cles
         de tete, `name` > 3 car. et unique, types, `value`/`label` requis,
         `id` et labels uniques, `options` non vides, distinctes, ⛔ booleen
         YAML, ⛔ « None », >= 1 champ de saisie, ⛔ cle non-chaine
   (c3)  le bug report porte les 8 `id` avec leur type, `required` sur 5, et un
         `markdown` qui renvoie a `SECURITY.md` (le lien direct
         `?template=bug_report.yml` CONTOURNE le selecteur)
   (c4)  la feature request CITE la section de statut par lien, dit qu'aucune
         date n'est livree, ⛔ sans recopier les mots du statut
   (c5)  `config.yml` : `blank_issues_enabled` BOOLEEN explicite, liens complets en
         `https`, un vers le formulaire prive de CE depot, un vers le code de
         conduite
   (c6)  le modele de PR existe et lie `CLA.md`, qui existe
   (c7)  `SECURITY.md` lie le formulaire prive, interdit le ticket public, et
         il est ATTEIGNABLE depuis la vitrine et `CONTRIBUTING.md`
   (c8)  `CODE_OF_CONDUCT.md` : ⛔ `[INSERT`, ⛔ « promptly », ⛔ l'avertissement
         prive ecrit ; *Report abuse* nomme ; l'absence de canal prive DITE ;
         attribution 2.1 + CC BY 4.0 + modifications ; atteignable
   (c9)  ⛔ adresse e-mail (fichiers neufs ET modifies par la marche) · ⛔
         promesse de delai (fichiers neufs)
   (c10) la section source dit PUBLIC BETA, best effort, community supported,
         No SLA, qu'aucune date n'est promise sur une feature request — et ⛔
         aucune promesse de delai n'y est ecrite
   (c11) « public beta » (casse et emphase ignorees) n'est ecrit que dans UN
         fichier du corpus public, et DANS la section
   (c12) tout lien des fichiers neufs et de la vitrine designe un fichier qui
         EXISTE (liens `blob/main/` absolus compris — `verif_licences_dn52.py` ne
         les resout pas), un `#fragment` designe un titre qui EXISTE, et ⛔ aucun
         lien RELATIF dans `.github/` (GitHub le resout contre la page de l'issue)
   (c13) `THIRD-PARTY.md` nomme le Covenant HORS du bloc `## Firmware`
   (c14) chaque controle est vise par >= 1 mutant (ids lus a l'AST)
   (c15) chaque cible declaree est un controle REEL
   (c16) `CIBLES` et `MUTANTS` se correspondent, cle a cle

── CODES DE RETOUR ─────────────────────────────────────────────────────────
    0  N OK / 0 KO · 1  au moins un KO (PyYAML absent compris)
    2  mutant inconnu
    3  mutant SANS EFFET (ancre absente, etat inchange) — AVEC son `BILAN`,
       ⛔ jamais un vert
"""

import argparse
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import dn_gates
except ImportError as _x:                                 # pragma: no cover
    sys.stderr.write(
        "⛔ `tools/dn_gates.py` est INTROUVABLE (%s) : il vit DANS ce depot —\n"
        "   c'est un defaut, ⛔ pas un prerequis.\n" % _x)
    sys.exit(1)

# ⛔ ALIAS, ⛔ PAS DES RE-DEFINITIONS (`verif_harnais_dn81.py` (c1d)).
ctrl = dn_gates.ctrl
bilan = dn_gates.bilan

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEPOT = "https://github.com/nasbarok/desknode"
BLOB = "https://github.com/nasbarok/desknode/blob/main/"
URL_FAILLE = "https://github.com/nasbarok/desknode/security/advisories/new"
URL_ISSUE_PUBLIQUE = "https://github.com/nasbarok/desknode/issues/new"

BUG = ".github/ISSUE_TEMPLATE/bug_report.yml"
DEMANDE = ".github/ISSUE_TEMPLATE/feature_request.yml"
CONFIG = ".github/ISSUE_TEMPLATE/config.yml"
MODELE_PR = ".github/pull_request_template.md"
SECURITE = "SECURITY.md"
CONDUITE = "CODE_OF_CONDUCT.md"
CONTRIB = "CONTRIBUTING.md"
VITRINE = "README.md"
CLA = "CLA.md"
TIERS = "THIRD-PARTY.md"
JOURNAL = "docs/journal-de-bord.md"

DOSSIER_FORMULAIRES = ".github/ISSUE_TEMPLATE"
# ⚠️ LES DEUX FORMULAIRES NOMMES, ⛔ PAS LA POPULATION : (c1)(c2) jugent tout
#    formulaire du DOSSIER (revue du 2026-09-13 — une gate qui code en dur ses
#    propres fichiers ne voit pas le troisieme). (c3)(c4) restent sur leur nom.
FORMULAIRES = (BUG, DEMANDE)
NEUFS = (BUG, DEMANDE, CONFIG, MODELE_PR, SECURITE, CONDUITE)
# ⛔ « Aucune adresse e-mail dans un fichier neuf ou modifie » : les fichiers
#    que la marche MODIFIE sont confrontes au motif d'adresse, ⛔ pas a celui de
#    promesse (un « within 3 days » MESURE a sa place dans un CHANGELOG futur).
MODIFIES = (CONTRIB, VITRINE, "LICENSING.md", TIERS, "CHANGELOG.md",
            "docs/roadmap.md")
LUS = NEUFS + (CONTRIB, VITRINE, TIERS)

# ── LES REGLES ECRITES DE GITHUB (citees dans T1, ⛔ reprises de memoire) ────
TYPES = ("checkboxes", "dropdown", "input", "markdown", "textarea", "upload")
CLES_TETE = ("name", "description", "body", "assignees", "labels", "title",
             "type", "projects")
CLES_TETE_REQUISES = ("name", "description", "body")
CLES_ELEMENT = ("type", "id", "attributes", "validations")
RE_ID = re.compile(r"^[A-Za-z0-9_-]+$")
NOM_PLUS_DE = 3

# ── LE BUG REPORT : id → (type, required) ──────────────────────────────────
CHAMPS_BUG = {
    "hardware": ("dropdown", True),
    "gpu": ("input", False),
    "lhm": ("dropdown", False),
    "desknode-version": ("input", True),
    "windows-version": ("input", True),
    "what-happened": ("textarea", True),
    "steps": ("textarea", True),
    "logs": ("textarea", False),
}
PALIERS = ("DeskNode", "DeskNode + Ambiance")

# ── LE STATUT : UNE SEULE SOURCE ───────────────────────────────────────────
STATUT_TITRE = "What this project is, honestly"
STATUT_FRAGMENT = "what-this-project-is-honestly"
STATUT_URL = BLOB + CONTRIB + "#" + STATUT_FRAGMENT
STATUT_CASSE = "PUBLIC BETA"
STATUT_PHRASES = ("best effort", "community supported", "no sla",
                  "no date is promised on a feature request")
# ⚠️ LUES A FRONTIERE DE MOT : « no sla » est une sous-chaine de « no slack »
#    et de « no slash » (revue du 2026-09-13).
SANS_DATE = "does not come with a delivery date"

CONSIGNE_SECURITE = "do not open a public issue"
PAS_DE_CANAL = "there is no private channel to the maintainer"
COVENANT_URL = "contributor-covenant.org/version/2/1"
COVENANT_NOM = "Contributor Covenant"
LICENCE_ORIGINE = "CC BY 4.0"
LICENCE_ADAPTATION = "CC-BY-SA-4.0"
TITRE_MODIFS = "Changes made in this adaptation"
INTERDITS_CONDUITE = ("[insert", "promptly", "private, written warning",
                      "official e-mail address")

RE_MAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# ⚠️ ELARGI A LA REVUE DU 2026-09-13 : la 1re forme ne voyait que « within <chiffres>
#    hours/days/weeks » — « within a week », « within 72h », « We'll respond within
#    two business days » passaient VERTS. ⛔ Et une duree SANS engagement (« for 24
#    hours, 3 days, 1 week… », les limites d'interaction du code de conduite) ⛔ ne
#    doit PAS mordre : le motif exige « within », un verbe de reponse + « in », ou
#    « we will / we'll » + un verbe de reponse.
_NOMBRE = (r"(?:\d+(?:\s*(?:-|–|to|or)\s*\d+)?|an?|one|two|three|four|five|six|"
           r"seven|eight|nine|ten|eleven|twelve|fourteen|twenty-four|forty-eight|"
           r"seventy-two|(?:a\s+)?few|a\s+couple\s+(?:of\s+)?)")
_UNITE = r"(?:(?:business|working|calendar)\s+)?(?:hours?|hrs?|h|days?|weeks?|months?)"
RE_PROMESSE = re.compile(
    r"\bwithin\s+(?:the\s+(?:next\s+|first\s+)?)?" + _NOMBRE + r"\s*" + _UNITE + r"\b"
    r"|\b(?:respond|reply|answer|acknowledge|review|triage)\w*\s+(?:\w+\s+){0,3}?in\s+"
    + _NOMBRE + r"\s*" + _UNITE + r"\b"
    r"|\bwe(?:\s+will|\s+shall|'ll|’ll)\s+(?:\w+\s+){0,2}?"
    r"(?:respond|reply|review|acknowledge|answer|get\s+back)\b"
    r"|\bpromptly\b", re.I)
RE_BETA = re.compile(r"public[\s-]+beta")

RE_ATX = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
RE_CLOTURE = re.compile(r"^ {0,3}(```|~~~)")
RE_LIEN = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
# Une URL `blob/main/` NUE (`url:` de `config.yml`), hors lien Markdown.
RE_BLOB_NU = re.compile(re.escape(BLOB) + r"[^\s)\]\"'<>`]+")

AVEUGLEMENT_YAML = (
    "⛔ PyYAML ABSENT (%s) — les YAML de `.github/ISSUE_TEMPLATE/` ⛔ NE "
    "SONT PAS LUS. Ce que la gate ne voit alors PAS : un formulaire que GitHub "
    "refuserait, un champ retire, un lien de securite perdu. ⛔ Ce n'est PAS un "
    "vert : (c1)(c2)(c3)(c4)(c5) ROUGISSENT, et le trou se referme avec le "
    "`python3-yaml` du systeme (present sur le poste de l'auteur ; etaye, ⛔ non "
    "mesure, sur le runner — ledger, `dn8-8`).")
AVEUGLEMENTS = (
    "⛔ AVEUGLEMENT DECLARE — cette gate confronte les formulaires aux regles "
    "que la documentation GitHub ECRIT. Elle ⛔ ne voit PAS : (1) la validation "
    "REELLE de GitHub (mots interdits dans un label, labels « trop proches ») ; "
    "(2) le RENDU du selecteur d'issues ; (3) l'EFFET de `validations.required`, "
    "qui n'agit que sur un depot PUBLIC ; (4) l'ACTIVATION du signalement prive "
    "de failles, reglage d'un depot public. Les quatre attendent la bascule "
    "(ledger, porteur `dn8-8`).")

# ══ LES MUTANTS — chacun REPLANTE une faute nommee ══════════════════════════
MUTANTS = {}
CIBLES = {}
MUTANTS[1] = "retire le champ `windows-version` du bug report"
CIBLES[1] = ("c3",)
MUTANTS[2] = ("casse l'indentation de la feature request ⇒ un YAML que GitHub "
              "ne lit pas")
CIBLES[2] = ("c1", "c2", "c4")
MUTANTS[3] = "duplique un `id` dans la feature request"
CIBLES[3] = ("c2",)
MUTANTS[4] = "donne un type INCONNU a un champ de la feature request"
CIBLES[4] = ("c2",)
MUTANTS[5] = ("ramene le `name` de la feature request a 3 caracteres ⇒ GitHub "
              "ne l'affiche pas")
CIBLES[5] = ("c2",)
MUTANTS[6] = "retire le lien de statut de la feature request"
CIBLES[6] = ("c4",)
MUTANTS[7] = "retire le lien de securite de `config.yml`"
CIBLES[7] = ("c5",)
MUTANTS[8] = "retire le lien vers `CLA.md` du modele de PR"
CIBLES[8] = ("c6",)
MUTANTS[9] = "ajoute « within 48 hours » a `SECURITY.md`"
CIBLES[9] = ("c9",)
MUTANTS[10] = ("restaure la case `[INSERT CONTACT METHOD]` du Covenant dans le "
               "code de conduite")
CIBLES[10] = ("c8",)
MUTANTS[11] = "restaure « promptly » dans le code de conduite"
CIBLES[11] = ("c8", "c9")
MUTANTS[12] = "ajoute une adresse e-mail a `SECURITY.md`"
CIBLES[12] = ("c9",)
MUTANTS[13] = "recopie « PUBLIC BETA » dans la vitrine ⇒ deux sources"
CIBLES[13] = ("c11",)
MUTANTS[14] = "retire « community supported » de la section de statut"
CIBLES[14] = ("c10",)
MUTANTS[15] = "casse le fragment du lien de statut de la vitrine"
CIBLES[15] = ("c12",)
MUTANTS[16] = "retire l'attribution du Covenant 2.1 du code de conduite"
CIBLES[16] = ("c8",)
MUTANTS[17] = ("fait envoyer `SECURITY.md` vers un ticket PUBLIC au lieu du "
               "formulaire prive")
CIBLES[17] = ("c7",)
MUTANTS[18] = ("deplace le Covenant dans la table `## Firmware` de "
               "`THIRD-PARTY.md` ⇒ une ligne que la table epinglee refuse")
CIBLES[18] = ("c13",)
# ⚠️ REECRIT A LA REVUE DU 2026-09-13 : sa 1re forme videait `CIBLES[1]` (c3) et
#    sortait VERTE des que les mutants 25 et 33 ont vise (c3) aussi — un mutant
#    PERIME, ⛔ un trou de la reciproque. Il retire desormais (c13) de TOUTES
#    les cibles : le controle est garde par ZERO mutant quel que soit leur nombre.
MUTANTS[19] = "retire (c13) de TOUTES les cibles ⇒ un controle garde par ZERO mutant"
CIBLES[19] = ("c14",)
MUTANTS[20] = ("declare dans `CIBLES` un controle INEXISTANT ⇒ une cible "
               "PERIMEE que « N rouges » ne voit pas")
CIBLES[20] = ("c15",)
MUTANTS[21] = "declare une cible pour un mutant qui N'EXISTE PAS"
CIBLES[21] = ("c16",)
# ⚠️ 22 → 38 : AJOUTES A LA REVUE DU 2026-09-13. Elle a DEMONTRE que six regles de
#    (c2)(c3)(c4)(c5) et trois proprietes de (c8) n'etaient epinglees par AUCUN
#    mutant (leurs branches supprimees, le nominal et les 21 mutants restaient
#    inchanges), et que (c9)(c10)(c12) avaient des trous. Chacun REPLANTE sa faute.
MUTANTS[22] = "une option de dropdown `No` ⇒ un BOOLEEN YAML, ⛔ une chaine"
CIBLES[22] = ("c2",)
MUTANTS[23] = "une option de dropdown « None » ⇒ le mot RESERVE"
CIBLES[23] = ("c2",)
MUTANTS[24] = "duplique un `label` dans le bug report"
CIBLES[24] = ("c2",)
MUTANTS[25] = "retire `required` du champ `desknode-version`"
CIBLES[25] = ("c3",)
MUTANTS[26] = "`blank_issues_enabled` devient une CHAINE, ⛔ un booleen"
CIBLES[26] = ("c5",)
MUTANTS[27] = "recopie « best effort » dans la feature request"
CIBLES[27] = ("c4",)
MUTANTS[28] = "retire la phrase « no private channel » du code de conduite"
CIBLES[28] = ("c8",)
MUTANTS[29] = "retire « Report abuse » du code de conduite"
CIBLES[29] = ("c8",)
MUTANTS[30] = "restaure l'avertissement « private, written warning »"
CIBLES[30] = ("c8",)
MUTANTS[31] = "ajoute « within a week » a `SECURITY.md` (nombre en LETTRES)"
CIBLES[31] = ("c9",)
MUTANTS[32] = "plante une promesse de delai dans la section de statut"
CIBLES[32] = ("c10",)
MUTANTS[33] = ("retire le lien vers `SECURITY.md` du bug report ⇒ le lien direct "
               "du formulaire contourne la securite")
CIBLES[33] = ("c3",)
MUTANTS[34] = ("change « version 2.1 » en « version 3.0 » dans le paragraphe "
               "d'attribution (la liste des changements dit encore 2.1)")
CIBLES[34] = ("c8",)
MUTANTS[35] = "restaure « official e-mail address » dans le perimetre"
CIBLES[35] = ("c8",)
MUTANTS[36] = ("ajoute en memoire un 3e formulaire INVALIDE (nom duplique, que "
               "du markdown)")
CIBLES[36] = ("c2",)
MUTANTS[37] = "fait pointer un lien `blob/main/` du modele de PR sur un fichier ABSENT"
CIBLES[37] = ("c12",)
MUTANTS[38] = "ajoute un lien RELATIF dans le modele de PR"
CIBLES[38] = ("c12",)

CONTROLES_PREVUS = 16
RC_SANS_EFFET = 3

_MUTANT = 0


class NonExerce(Exception):
    """L'ancre du mutant est absente : il ne change rien. ⇒ `rc=3`."""


def remplace(texte, ancre, par, n):
    if texte is None or ancre not in texte:
        raise NonExerce("MUTANT %d NON EXERCE : l'ancre %r est ABSENTE"
                        % (n, ancre[:60]))
    return texte.replace(ancre, par, 1)


def muter(fichiers, cibles):
    """REPLANTE une faute DANS DES COPIES — ⛔ jamais dans un fichier du depot.

    🔴 La garde du no-op est UNIVERSELLE : le corps principal compare les copies
       AVANT/APRES ; un mutant sans effet rend `rc=3` AVEC son `BILAN`."""
    f = dict(fichiers)
    c = dict(cibles)
    if _MUTANT == 1:
        t = f.get(BUG) or ""
        m = re.search(r"\n  - type: input\n    id: windows-version\n.*?(?=\n  - type:)",
                      t, re.S)
        if not m:
            raise NonExerce("MUTANT 1 NON EXERCE : le bloc `windows-version` est absent")
        f[BUG] = t[:m.start()] + t[m.end():]
    elif _MUTANT == 2:
        f[DEMANDE] = remplace(f.get(DEMANDE), "\n    id: problem",
                              "\n   id: problem", 2)
    elif _MUTANT == 3:
        f[DEMANDE] = remplace(f.get(DEMANDE), "id: alternatives", "id: proposal", 3)
    elif _MUTANT == 4:
        t = f.get(DEMANDE) or ""
        i = t.find("id: alternatives")
        j = t.rfind("type: textarea", 0, i)
        if i < 0 or j < 0:
            raise NonExerce("MUTANT 4 NON EXERCE : le champ `alternatives` est absent")
        f[DEMANDE] = t[:j] + "type: longtext" + t[j + len("type: textarea"):]
    elif _MUTANT == 5:
        f[DEMANDE] = remplace(f.get(DEMANDE), "name: Feature request\n",
                              "name: Req\n", 5)
    elif _MUTANT == 6:
        t = f.get(DEMANDE) or ""
        m = re.search(r"\[([^\]]*)\]\(%s\)" % re.escape(STATUT_URL), t)
        if not m:
            raise NonExerce("MUTANT 6 NON EXERCE : le lien de statut est absent")
        f[DEMANDE] = t[:m.start()] + m.group(1) + t[m.end():]
    elif _MUTANT == 7:
        t = f.get(CONFIG) or ""
        m = re.search(r"\n  - name: [^\n]*\n    url: %s\n    about: [^\n]*"
                      % re.escape(URL_FAILLE), t)
        if not m:
            raise NonExerce("MUTANT 7 NON EXERCE : le lien de securite est absent")
        f[CONFIG] = t[:m.start()] + t[m.end():]
    elif _MUTANT == 8:
        t = f.get(MODELE_PR) or ""
        m = re.search(r"\[([^\]]*)\]\(%s\)" % re.escape(BLOB + CLA), t)
        if not m:
            raise NonExerce("MUTANT 8 NON EXERCE : le lien vers le CLA est absent")
        f[MODELE_PR] = t[:m.start()] + m.group(1) + t[m.end():]
    elif _MUTANT == 9:
        f[SECURITE] = remplace(f.get(SECURITE), "## What happens after you report\n",
                               "## What happens after you report\n\nWe answer "
                               "within 48 hours.\n", 9)
    elif _MUTANT == 10:
        f[CONDUITE] = remplace(f.get(CONDUITE), "## Reporting\n",
                               "## Reporting\n\nInstances of abusive behavior may be "
                               "reported at [INSERT CONTACT METHOD].\n", 10)
    elif _MUTANT == 11:
        f[CONDUITE] = remplace(f.get(CONDUITE), "## Enforcement\n",
                               "## Enforcement\n\nAll complaints will be reviewed "
                               "promptly and fairly.\n", 11)
    elif _MUTANT == 12:
        # ⚠️ L'ADRESSE EST CONSTRUITE, ⛔ ECRITE : ecrite en toutes lettres,
        #    elle ferait de CE fichier neuf un fichier qui publie une adresse.
        adresse = "@".join(("security", "desknode.example.org"))
        f[SECURITE] = remplace(f.get(SECURITE), "## What to include\n",
                               "## What to include\n\nOr write to %s.\n" % adresse, 12)
    elif _MUTANT == 13:
        f[VITRINE] = remplace(f.get(VITRINE), "## Status and help\n",
                              "## Status and help\n\nDeskNode is a **PUBLIC "
                              "BETA**.\n", 13)
    elif _MUTANT == 14:
        t = f.get(CONTRIB) or ""
        neuf = re.sub(r"(?i)community[\s*_]*supported", "", t)
        if neuf == t:
            raise NonExerce("MUTANT 14 NON EXERCE : « community supported » absent")
        f[CONTRIB] = neuf
    elif _MUTANT == 15:
        f[VITRINE] = remplace(f.get(VITRINE), "](%s#%s)" % (CONTRIB, STATUT_FRAGMENT),
                              "](%s#what-this-project-is)" % CONTRIB, 15)
    elif _MUTANT == 16:
        t = f.get(CONDUITE) or ""
        i = t.find("## Attribution\n")
        j = t.find("### License of the original\n")
        if i < 0 or j < i:
            raise NonExerce("MUTANT 16 NON EXERCE : la section d'attribution est absente")
        f[CONDUITE] = t[:i] + t[j:]
    elif _MUTANT == 17:
        f[SECURITE] = remplace(f.get(SECURITE), "](%s)" % URL_FAILLE,
                               "](%s)" % URL_ISSUE_PUBLIQUE, 17)
    elif _MUTANT == 18:
        t = f.get(TIERS) or ""
        i = t.find("\n## Code of conduct\n")
        j = t.find("\n## ", i + 1) if i >= 0 else -1
        if i < 0 or j < 0 or "| ESP-IDF |" not in t:
            raise NonExerce("MUTANT 18 NON EXERCE : la section du Covenant ou la "
                            "table `## Firmware` est absente")
        t = t[:i] + t[j:]
        f[TIERS] = t.replace("| ESP-IDF |", "| %s | `2.1` | %s |\n| ESP-IDF |"
                             % (COVENANT_NOM, LICENCE_ORIGINE), 1)
    elif _MUTANT == 19:
        c = {k: tuple(x for x in v if x != "c13") for k, v in c.items()}
        if c == dict(cibles):
            raise NonExerce("MUTANT 19 NON EXERCE : aucune cible ne vise (c13)")
    elif _MUTANT == 20:
        if 1 not in c:
            raise NonExerce("MUTANT 20 NON EXERCE : `CIBLES[1]` absent")
        c[1] = tuple(c[1]) + ("c99",)
    elif _MUTANT == 21:
        if 999 in c:
            raise NonExerce("MUTANT 21 NON EXERCE : `CIBLES[999]` existe deja")
        c[999] = ("c1",)
    elif _MUTANT == 22:
        f[BUG] = remplace(f.get(BUG), "        - Not installed\n", "        - No\n", 22)
    elif _MUTANT == 23:
        f[BUG] = remplace(f.get(BUG), "        - Installed, not running\n",
                          "        - None\n", 23)
    elif _MUTANT == 24:
        f[BUG] = remplace(f.get(BUG), "      label: Steps to reproduce\n",
                          "      label: What happened\n", 24)
    elif _MUTANT == 25:
        t = f.get(BUG) or ""
        m = re.search(r"id: desknode-version\n.*?(?=\n  - type:)", t, re.S)
        v = "\n    validations:\n      required: true"
        if not m or v not in m.group(0):
            raise NonExerce("MUTANT 25 NON EXERCE : `desknode-version` sans `required`")
        f[BUG] = t[:m.start()] + m.group(0).replace(v, "") + t[m.end():]
    elif _MUTANT == 26:
        t = f.get(CONFIG) or ""
        m = re.search(r"(?m)^blank_issues_enabled: (true|false)$", t)
        if not m:
            raise NonExerce("MUTANT 26 NON EXERCE : `blank_issues_enabled` absent")
        f[CONFIG] = t[:m.start()] + 'blank_issues_enabled: "%s"' % m.group(1) + t[m.end():]
    elif _MUTANT == 27:
        f[DEMANDE] = remplace(f.get(DEMANDE), "A request is read and may be kept",
                              "DeskNode is maintained best effort. A request is "
                              "read and may be kept", 27)
    elif _MUTANT == 28:
        t = f.get(CONDUITE) or ""
        neuf = re.sub(r"(?i)there is no private channel to the maintainer",
                      "Reports can be sent to the maintainer", t)
        if neuf == t:
            raise NonExerce("MUTANT 28 NON EXERCE : la phrase est absente")
        f[CONDUITE] = neuf
    elif _MUTANT == 29:
        t = f.get(CONDUITE) or ""
        neuf = re.sub(r"(?i)report abuse", "Flag it", t)
        if neuf == t:
            raise NonExerce("MUTANT 29 NON EXERCE : « Report abuse » est absent")
        f[CONDUITE] = neuf
    elif _MUTANT == 30:
        f[CONDUITE] = remplace(f.get(CONDUITE), "**Consequence**: A comment from the "
                               "maintainer, in public,", "**Consequence**: A private, "
                               "written warning from the maintainer,", 30)
    elif _MUTANT == 31:
        f[SECURITE] = remplace(f.get(SECURITE), "## What happens after you report\n",
                               "## What happens after you report\n\nWe answer "
                               "within a week.\n", 31)
    elif _MUTANT == 32:
        f[CONTRIB] = remplace(f.get(CONTRIB), "- Important bugs get fixed. Good pull "
                              "requests get merged.\n", "- Important bugs get fixed. "
                              "Good pull requests get merged.\n- We'll respond to every "
                              "report within two business days.\n", 32)
    elif _MUTANT == 33:
        t = f.get(BUG) or ""
        m = re.search(r"\[([^\]]*)\]\(%s\)" % re.escape(BLOB + SECURITE), t)
        if not m:
            raise NonExerce("MUTANT 33 NON EXERCE : le lien vers SECURITY.md est absent")
        f[BUG] = t[:m.start()] + m.group(1) + t[m.end():]
    elif _MUTANT == 34:
        f[CONDUITE] = remplace(f.get(CONDUITE), "**version 2.1**, available at",
                               "**version 3.0**, available at", 34)
    elif _MUTANT == 35:
        f[CONDUITE] = remplace(f.get(CONDUITE), "for example when speaking in the name of",
                               "for example when using an official e-mail address "
                               "in the name of", 35)
    elif _MUTANT == 36:
        tiers_form = ".github/ISSUE_TEMPLATE/question.yml"
        if tiers_form in f:
            raise NonExerce("MUTANT 36 NON EXERCE : %s existe deja" % tiers_form)
        f[tiers_form] = ("name: Bug report\ndescription: A question.\nbody:\n"
                         "  - type: markdown\n    attributes:\n      value: Ask here.\n")
    elif _MUTANT == 37:
        f[MODELE_PR] = remplace(f.get(MODELE_PR), "](%sLICENSING.md)" % BLOB,
                                "](%sLICENSING-absent.md)" % BLOB, 37)
    elif _MUTANT == 38:
        t = f.get(MODELE_PR)
        if t is None:
            raise NonExerce("MUTANT 38 NON EXERCE : le modele de PR est absent")
        f[MODELE_PR] = t + "\nSee also [the guide](../CONTRIBUTING.md).\n"
    return f, c


# ══ LA LECTURE ══════════════════════════════════════════════════════════════

def charge_fichier(rel):
    """Le texte d'un fichier du depot, ou `None` — ⛔ jamais une exception :
    l'absence devient un controle NOMME chez l'appelant."""
    try:
        return dn_gates.lire(os.path.join(RACINE, rel))[0]
    except (OSError, UnicodeDecodeError):
        return None


def aplati(txt):
    """Minuscules, sans emphase ni accents graves, blancs repliés : un motif ⛔
    ne depend ni du gras ni de l'endroit ou la prose a ete coupee."""
    t = re.sub(r"[*`]", "", txt or "").replace("_", " ")
    return dn_gates.plat(t).lower()


def section_md(txt, titre, niveau=2):
    """Le texte d'une section `## titre` jusqu'au titre de meme niveau suivant
    (ou de niveau superieur), `None` si absente."""
    if txt is None:
        return None
    m = re.search(r"(?m)^%s +%s\s*$" % ("#" * niveau, re.escape(titre)), txt)
    if not m:
        return None
    suite = re.search(r"(?m)^#{1,%d} " % niveau, txt[m.end():])
    return txt[m.end():m.end() + suite.start()] if suite else txt[m.end():]


def ancres(txt):
    """Les ancres que GitHub pose sur les titres ATX hors blocs de code : texte
    en minuscules, liens reduits a leur texte, ponctuation et symboles retires
    (lettres, chiffres, marques, `-`, `_` et espaces gardes), espaces ⇒ `-`,
    doublons suffixes `-1`, `-2`… ⚠️ C'est une MODELISATION du rendu : le HTML
    reel est releve dans `T3`, ⛔ pas ici."""
    out, vus, code = set(), {}, False
    for l in (txt or "").split("\n"):
        if RE_CLOTURE.match(l):
            code = not code
            continue
        if code:
            continue
        m = RE_ATX.match(l)
        if not m:
            continue
        t = RE_LIEN.sub(lambda x: x.group(1), m.group(2)).lower()
        s = "".join(ch for ch in t if ch.isalnum() or ch in "-_ "
                    or unicodedata.category(ch).startswith("M")).replace(" ", "-")
        n = vus.get(s, 0)
        out.add(s if n == 0 else "%s-%d" % (s, n))
        vus[s] = n + 1
    return out


def cibles_de_liens(txt):
    return [m.group(2) for m in RE_LIEN.finditer(txt or "")]


def parse(txt, yaml_mod):
    """(objet, erreur) — `yaml.safe_load`, ⛔ jamais un motif (`NFR14`)."""
    if txt is None:
        return None, "fichier ABSENT"
    try:
        return yaml_mod.safe_load(txt), None
    except yaml_mod.YAMLError as x:
        return None, " ".join(str(x).split())[:110]


def markdown_de(obj):
    """Le texte des elements `markdown` d'un formulaire parse (`""` sinon)."""
    if not isinstance(obj, dict) or not isinstance(obj.get("body"), list):
        return ""
    return "\n".join(e["attributes"]["value"] for e in obj["body"]
                     if isinstance(e, dict) and e.get("type") == "markdown"
                     and isinstance(e.get("attributes"), dict)
                     and isinstance(e["attributes"].get("value"), str))


def contient(texte_aplati, phrase):
    """La phrase A FRONTIERE DE MOT — « no sla » ⛔ dans « no slack »."""
    return re.search(r"(?<!\w)%s(?!\w)" % re.escape(phrase), texte_aplati) is not None


def cles_non_chaines(obj, chemin="$"):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str):
                out.append("%s.%r" % (chemin, k))
            out += cles_non_chaines(v, "%s.%s" % (chemin, k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += cles_non_chaines(v, "%s[%d]" % (chemin, i))
    return out


def chaine_pleine(x):
    return isinstance(x, str) and bool(x.strip())


def fautes_formulaire(rel, obj):
    """Les ecarts d'UN formulaire aux regles ECRITES de GitHub (T1 § 1)."""
    court = os.path.basename(rel)
    if not isinstance(obj, dict):
        return ["%s : la racine n'est pas une table" % court]
    f = ["%s : cle NON-CHAINE %s" % (court, k) for k in cles_non_chaines(obj)]
    f += ["%s : cle de tete `%s` ABSENTE" % (court, k)
          for k in CLES_TETE_REQUISES if k not in obj]
    f += ["%s : cle de tete `%s` NON PERMISE" % (court, k)
          for k in obj if isinstance(k, str) and k not in CLES_TETE]
    nom = obj.get("name")
    if not (isinstance(nom, str) and len(nom.strip()) > NOM_PLUS_DE):
        f.append("%s : `name` %r n'a pas PLUS DE %d caracteres" % (court, nom, NOM_PLUS_DE))
    if not chaine_pleine(obj.get("description")):
        f.append("%s : `description` vide ou non-chaine" % court)
    corps = obj.get("body")
    if not isinstance(corps, list) or not corps:
        f.append("%s : `body` n'est pas une liste NON VIDE" % court)
        return f
    ids, labels, saisies = [], [], 0
    for i, el in enumerate(corps):
        o = "%s body[%d]" % (court, i)
        if not isinstance(el, dict):
            f.append("%s n'est pas une table" % o)
            continue
        f += ["%s : cle `%s` NON PERMISE" % (o, k) for k in el
              if isinstance(k, str) and k not in CLES_ELEMENT]
        ty = el.get("type")
        at = el.get("attributes")
        if ty not in TYPES:
            f.append("%s : type %r INCONNU" % (o, ty))
            continue
        if not isinstance(at, dict):
            f.append("%s : `attributes` absent" % o)
            continue
        if ty == "markdown":
            if not chaine_pleine(at.get("value")):
                f.append("%s : `markdown` sans `value`" % o)
            continue
        saisies += 1
        if not chaine_pleine(at.get("label")):
            f.append("%s : `label` absent ou vide" % o)
        else:
            labels.append(at["label"])
        if "id" in el:
            if not (isinstance(el["id"], str) and RE_ID.match(el["id"])):
                f.append("%s : `id` %r hors [A-Za-z0-9_-]" % (o, el["id"]))
            else:
                ids.append(el["id"])
        va = el.get("validations")
        if va is not None and not (isinstance(va, dict)
                                   and isinstance(va.get("required", False), bool)):
            f.append("%s : `validations.required` n'est pas un booleen" % o)
        if ty in ("dropdown", "checkboxes"):
            op = at.get("options")
            if not isinstance(op, list) or not op:
                f.append("%s : `options` vide" % o)
                continue
            if ty == "dropdown":
                noms = op
                if not all(isinstance(x, str) for x in op):
                    f.append("%s : option NON-CHAINE (booleen YAML ?)" % o)
                if any(isinstance(x, str) and x.strip().lower() == "none" for x in op):
                    f.append("%s : option reservee « None »" % o)
            else:
                noms = [x.get("label") if isinstance(x, dict) else None for x in op]
                if not all(chaine_pleine(x) for x in noms):
                    f.append("%s : case sans `label`" % o)
                labels += [x for x in noms if isinstance(x, str)]
            if len(set(map(str, noms))) != len(noms):
                f.append("%s : `options` NON DISTINCTES" % o)
    f += ["%s : `id` DUPLIQUE %r" % (court, x) for x in sorted(set(ids))
          if ids.count(x) > 1]
    f += ["%s : label DUPLIQUE %r" % (court, x) for x in sorted(set(labels))
          if labels.count(x) > 1]
    if not saisies:
        f.append("%s : AUCUN champ de saisie (que du markdown)" % court)
    return f


def corps():
    global _MUTANT
    ap = argparse.ArgumentParser(
        description="dn8-5 — le depot sait recevoir : formulaires, securite, "
                    "conduite, statut sans promesse.")
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

    print("=" * 78)
    print("dn8-5 — LE DEPOT SAIT RECEVOIR" + ("   [MUTANT %d]" % _MUTANT
                                             if _MUTANT else ""))
    print("=" * 78)
    print(AVEUGLEMENTS)

    # ⚠️ L'IMPORT VIENT **APRES** L'ANALYSE DES ARGUMENTS : `--help` et
    #    `--liste-mutants` repondent sans PyYAML.
    try:
        import yaml as yaml_mod
        motif_yaml = ""
    except ImportError as x:
        yaml_mod = None
        motif_yaml = str(x)
        print("\n" + AVEUGLEMENT_YAML % motif_yaml)

    # ⚠️ LES FORMULAIRES SONT LUS DANS LE DOSSIER, ⛔ PAS DANS UNE LISTE : un 3e
    #    formulaire pose a cote des deux de la marche est parse et juge.
    try:
        noms_dossier = sorted(os.listdir(os.path.join(RACINE, DOSSIER_FORMULAIRES)))
    except OSError:
        noms_dossier = []
    du_dossier = tuple(DOSSIER_FORMULAIRES + "/" + n for n in noms_dossier
                       if n.endswith((".yml", ".yaml"))
                       and DOSSIER_FORMULAIRES + "/" + n != CONFIG)
    base = {rel: charge_fichier(rel) for rel in LUS + du_dossier}
    try:
        fichiers, cibles = muter(base, CIBLES)
    except NonExerce as x:
        print("\n⛔ %s" % x)
        print("   ⇒ rc=3 : un mutant qui ne change rien ⛔ ne prouve rien.")
        return bilan(RC_SANS_EFFET, anticipee="mutant %d sans effet" % _MUTANT,
                     prevus=CONTROLES_PREVUS)
    if _MUTANT and fichiers == base and cibles == CIBLES:
        print("\n⛔ MUTANT %d SANS EFFET : aucune copie ne differe." % _MUTANT)
        print("   ⇒ rc=3 : un mutant qui ne change rien ⛔ ne prouve rien.")
        return bilan(RC_SANS_EFFET, anticipee="mutant %d sans effet" % _MUTANT,
                     prevus=CONTROLES_PREVUS)
    for rel in sorted(set(fichiers) | set(base)):
        if fichiers.get(rel) != base.get(rel):
            print("  ⚠️ %s MUTE en memoire" % rel)
    formulaires = sorted(set(FORMULAIRES) | {
        k for k in fichiers if k.startswith(DOSSIER_FORMULAIRES + "/")
        and k.endswith((".yml", ".yaml")) and k != CONFIG})
    yamls = formulaires + [CONFIG]

    # ── (c1) CHAQUE YAML DU DOSSIER SE PARSE ───────────────────────────────
    print("\n── (c1)(c2) LES FORMULAIRES, PARSES ET CONFRONTES ────────────────")
    objets, f1 = {}, []
    for rel in yamls:
        if yaml_mod is None:
            f1.append("%s YAML NON LU (PyYAML absent)" % os.path.basename(rel))
            continue
        obj, err = parse(fichiers[rel], yaml_mod)
        if err:
            f1.append("%s : %s" % (os.path.basename(rel), err))
        else:
            objets[rel] = obj
    ctrl(not f1, "(c1) chaque YAML du dossier existe et SE PARSE",
         "yaml.safe_load : %s" % ", ".join(os.path.basename(r) for r in yamls)
         if not f1 else "⛔ " + " · ".join(f1))

    def non_lu(rel):
        return "%s NON JUGE : YAML NON LU (voir (c1))" % os.path.basename(rel)

    # ── (c2) LES REGLES ECRITES ────────────────────────────────────────────
    f2 = []
    for rel in formulaires:
        if rel not in objets:
            f2.append(non_lu(rel))
        else:
            f2 += fautes_formulaire(rel, objets[rel])
    noms = [objets[r].get("name") for r in formulaires
            if isinstance(objets.get(r), dict)]
    if len(noms) != len(set(map(str, noms))):
        f2.append("`name` NON UNIQUE entre formulaires : %r" % noms)
    ctrl(not f2, "(c2) chaque formulaire suit les regles ECRITES",
         "%d formulaire(s) du dossier · cles, types, id, labels, options, "
         ">= 1 saisie" % len(formulaires) if not f2 else "⛔ " + " · ".join(f2[:4]))

    # ── (c3) LE BUG REPORT ─────────────────────────────────────────────────
    print("\n── (c3)(c4)(c5) BUG REPORT, FEATURE REQUEST, SELECTEUR ───────────")
    f3 = []
    bug = objets.get(BUG)
    if BUG not in objets:
        f3.append(non_lu(BUG))
    else:
        els = {e.get("id"): e for e in (bug.get("body") or [])
               if isinstance(bug, dict) and isinstance(e, dict) and "id" in e} \
            if isinstance(bug, dict) and isinstance(bug.get("body"), list) else {}
        for i, (ty, req) in CHAMPS_BUG.items():
            e = els.get(i)
            if e is None:
                f3.append("`%s` ABSENT" % i)
                continue
            if e.get("type") != ty:
                f3.append("`%s` est %r, attendu %r" % (i, e.get("type"), ty))
            vreq = (e.get("validations") or {}).get("required") \
                if isinstance(e.get("validations"), dict) else None
            if req and vreq is not True:
                f3.append("`%s` sans `required: true`" % i)
        hw = ((els.get("hardware") or {}).get("attributes") or {}).get("options") \
            if isinstance((els.get("hardware") or {}).get("attributes"), dict) else None
        if not isinstance(hw, list) or any(p not in hw for p in PALIERS):
            f3.append("`hardware` ne propose pas %s" % " / ".join(PALIERS))
        rendu = ((els.get("logs") or {}).get("attributes") or {}).get("render") \
            if isinstance((els.get("logs") or {}).get("attributes"), dict) else None
        if rendu != "text":
            f3.append("`logs` sans `render: text`")
        # ⚠️ LA VITRINE ET `CONTRIBUTING.md` LIENT `?template=bug_report.yml` EN
        #    DIRECT : le lien de securite du selecteur est CONTOURNE. ⇒ le
        #    formulaire lui-meme doit renvoyer a `SECURITY.md` (revue 2026-09-13).
        if BLOB + SECURITE not in cibles_de_liens(markdown_de(bug)):
            f3.append("aucun `markdown` ne lie %s" % (BLOB + SECURITE))
    ctrl(not f3, "(c3) bug report : 8 id, required x5, lien securite",
         "%s · required : %s · lien %s" % (
             ", ".join(CHAMPS_BUG),
             ", ".join(i for i, (_, r) in CHAMPS_BUG.items() if r), SECURITE)
         if not f3 else "⛔ " + " · ".join(f3[:4]))

    # ── (c4) LA FEATURE REQUEST CITE LE STATUT ─────────────────────────────
    f4 = []
    dem = objets.get(DEMANDE)
    if DEMANDE not in objets:
        f4.append(non_lu(DEMANDE))
    else:
        texte = markdown_de(dem)
        if STATUT_URL not in cibles_de_liens(texte):
            f4.append("aucun lien vers la section de statut dans un `markdown`")
        if SANS_DATE not in aplati(texte):
            f4.append("« %s » absent" % SANS_DATE)
        recopies = [p for p in STATUT_PHRASES + (STATUT_CASSE.lower(),)
                    if contient(aplati(fichiers[DEMANDE]), p)]
        if recopies:
            f4.append("RECOPIE les mots du statut : %s" % recopies)
    ctrl(not f4, "(c4) feature request : statut CITE par lien, sans date",
         "lien `…#%s` · « %s »" % (STATUT_FRAGMENT, SANS_DATE)
         if not f4 else "⛔ " + " · ".join(f4))

    # ── (c5) LE SELECTEUR ──────────────────────────────────────────────────
    f5 = []
    cfg = objets.get(CONFIG)
    if CONFIG not in objets:
        f5.append(non_lu(CONFIG))
    elif not isinstance(cfg, dict):
        f5.append("la racine de config.yml n'est pas une table")
    else:
        f5 += ["cle NON-CHAINE %s" % k for k in cles_non_chaines(cfg)]
        # ⚠️ UN BOOLEEN EXPLICITE, ⛔ PLUS « false » : la revue du 2026-09-13 a
        #    rendu les tickets vierges (seule route generique d'une QUESTION —
        #    Discussions coupees, aucun formulaire de question).
        if not isinstance(cfg.get("blank_issues_enabled"), bool):
            f5.append("`blank_issues_enabled` = %r, attendu un booleen explicite"
                      % (cfg.get("blank_issues_enabled"),))
        liens = cfg.get("contact_links")
        if not isinstance(liens, list) or not liens:
            f5.append("`contact_links` vide")
            liens = []
        urls = []
        for i, l in enumerate(liens):
            if not isinstance(l, dict) or not all(chaine_pleine(l.get(k))
                                                  for k in ("name", "url", "about")):
                f5.append("contact_links[%d] sans name/url/about" % i)
                continue
            if not l["url"].startswith("https://"):
                f5.append("contact_links[%d] hors https : %r" % (i, l["url"]))
            urls.append(l["url"].strip())
        if URL_FAILLE not in urls:
            f5.append("aucun lien vers le formulaire PRIVE de CE depot")
        if BLOB + CONDUITE not in urls:
            f5.append("aucun lien vers %s" % CONDUITE)
    ctrl(not f5, "(c5) config.yml : booleen explicite, securite dehors",
         "blank_issues_enabled %r · %s · %s" % (
             cfg.get("blank_issues_enabled") if isinstance(cfg, dict) else None,
             URL_FAILLE[len(DEPOT):], CONDUITE)
         if not f5 else "⛔ " + " · ".join(f5[:4]))

    # ── (c6) LE MODELE DE PR ───────────────────────────────────────────────
    print("\n── (c6)(c7)(c8) PR, SECURITE, CONDUITE ───────────────────────────")
    pr = fichiers[MODELE_PR]
    f6 = []
    if pr is None:
        f6.append("%s ABSENT" % MODELE_PR)
    else:
        if BLOB + CLA not in cibles_de_liens(pr):
            f6.append("aucun lien vers %s" % (BLOB + CLA))
        if not os.path.isfile(os.path.join(RACINE, CLA)):
            f6.append("%s ABSENT du disque" % CLA)
    ctrl(not f6, "(c6) modele de PR present, lie CLA.md qui existe",
         "%s → %s" % (MODELE_PR, CLA) if not f6 else "⛔ " + " · ".join(f6))

    # ── (c7) SECURITY.md ───────────────────────────────────────────────────
    sec = fichiers[SECURITE]
    f7 = []
    if sec is None:
        f7.append("%s ABSENT de la racine" % SECURITE)
    else:
        if URL_FAILLE not in cibles_de_liens(sec):
            f7.append("aucun lien vers le formulaire prive")
        if CONSIGNE_SECURITE not in aplati(sec):
            f7.append("la consigne « %s » est absente" % CONSIGNE_SECURITE)
    for rel in (VITRINE, CONTRIB):
        if SECURITE not in cibles_de_liens(fichiers[rel]):
            f7.append("%s ne lie pas %s" % (rel, SECURITE))
    ctrl(not f7, "(c7) SECURITY.md : formulaire prive, pas de ticket",
         "lien prive · « %s » · lie depuis %s et %s"
         % (CONSIGNE_SECURITE, VITRINE, CONTRIB) if not f7
         else "⛔ " + " · ".join(f7))

    # ── (c8) CODE_OF_CONDUCT.md ────────────────────────────────────────────
    coc = fichiers[CONDUITE]
    f8 = []
    if coc is None:
        f8.append("%s ABSENT de la racine" % CONDUITE)
    else:
        nu = aplati(coc)
        f8 += ["promet ENCORE « %s »" % x for x in INTERDITS_CONDUITE if x in nu]
        if "report abuse" not in nu:
            f8.append("*Report abuse* n'est pas nomme")
        if PAS_DE_CANAL not in nu:
            f8.append("l'absence de canal prive n'est pas DITE")
        attrib = section_md(coc, "Attribution")
        # ⚠️ COUPEE AU PREMIER `###` : lue jusqu'a la fin du fichier, la LISTE DES
        #    CHANGEMENTS (qui dit aussi « version 2.1 ») satisfaisait le controle
        #    a la place du paragraphe d'attribution (revue du 2026-09-13).
        if attrib is not None:
            attrib = re.split(r"(?m)^### ", attrib, 1)[0]
        if attrib is None or not any(COVENANT_URL in c for c in cibles_de_liens(attrib)) \
                or "version 2.1" not in aplati(attrib):
            f8.append("attribution au Covenant 2.1 (lien + version) absente")
        if LICENCE_ORIGINE.lower() not in nu or LICENCE_ADAPTATION.lower() not in nu:
            f8.append("licences %s / %s non dites" % (LICENCE_ORIGINE, LICENCE_ADAPTATION))
        modifs = section_md(coc, TITRE_MODIFS, niveau=3)
        if modifs is None or not re.search(r"(?m)^\d+\. ", modifs):
            f8.append("la liste « %s » est absente ou vide" % TITRE_MODIFS)
    for rel in (VITRINE, CONTRIB):
        if CONDUITE not in cibles_de_liens(fichiers[rel]):
            f8.append("%s ne lie pas %s" % (rel, CONDUITE))
    ctrl(not f8, "(c8) conduite : ni canal invente, ni promesse",
         "Report abuse · pas de canal prive DIT · 2.1 · %s · modifications"
         % LICENCE_ORIGINE if not f8 else "⛔ " + " · ".join(f8[:4]))

    # ── (c9) ⛔ ADRESSE, ⛔ PROMESSE DE DELAI ───────────────────────────────
    print("\n── (c9)(c10)(c11) AUCUNE PROMESSE, UNE SEULE SOURCE ──────────────")
    f9 = []
    for rel in NEUFS + MODIFIES:
        txt = fichiers.get(rel)
        if txt is None:
            txt = charge_fichier(rel)
        if txt is None:
            f9.append("%s ILLISIBLE" % rel)
            continue
        f9 += ["%s publie une ADRESSE" % rel for _ in RE_MAIL.findall(txt)[:1]]
        if rel in NEUFS:
            f9 += ["%s promet « %s »" % (rel, m.group(0))
                   for m in list(RE_PROMESSE.finditer(dn_gates.plat(txt)))[:1]]
    ctrl(not f9, "(c9) ⛔ adresse e-mail, ⛔ promesse de delai",
         "%d fichier(s) neufs (adresse + delai) · %d modifies (adresse)"
         % (len(NEUFS), len(MODIFIES)) if not f9 else "⛔ " + " · ".join(f9[:4]))

    # ── (c10) LA SECTION SOURCE ────────────────────────────────────────────
    statut = section_md(fichiers[CONTRIB], STATUT_TITRE)
    f10 = []
    if statut is None:
        f10.append("section « %s » ABSENTE de %s" % (STATUT_TITRE, CONTRIB))
    else:
        if STATUT_CASSE not in statut.replace("*", ""):
            f10.append("« %s » absent" % STATUT_CASSE)
        f10 += ["« %s » absent" % p for p in STATUT_PHRASES
                if not contient(aplati(statut), p)]
        f10 += ["la section PROMET « %s »" % m.group(0)
                for m in list(RE_PROMESSE.finditer(dn_gates.plat(statut)))[:1]]
    ctrl(not f10, "(c10) la section de statut dit tout, sans promesse",
         "%s · %s" % (STATUT_CASSE, " · ".join(STATUT_PHRASES))
         if not f10 else "⛔ " + " · ".join(f10))

    # ── (c11) UNE SEULE SOURCE ─────────────────────────────────────────────
    corpus = sorted(set(
        [n for n in os.listdir(RACINE) if n.endswith(".md")]
        + [os.path.relpath(os.path.join(d, n), RACINE)
           for d, _, ns in os.walk(os.path.join(RACINE, ".github")) for n in ns]
        + ["docs/" + n for n in os.listdir(os.path.join(RACINE, "docs"))
           if n.endswith(".md")]) - {JOURNAL})
    porteurs = []
    for rel in corpus:
        txt = fichiers[rel] if rel in fichiers else charge_fichier(rel)
        if txt is not None and RE_BETA.search(aplati(txt)):
            porteurs.append(rel)
    dans = statut is not None and bool(RE_BETA.search(aplati(statut)))
    ctrl(porteurs == [CONTRIB] and dans,
         "(c11) « public beta » : UN fichier, DANS la section",
         "%d fichier(s) balayes (racine, .github/, docs/ hors journal) · "
         "seul porteur : %s" % (len(corpus), CONTRIB)
         if porteurs == [CONTRIB] and dans
         else "⛔ porteur(s) : %s · dans la section : %s" % (porteurs or "AUCUN", dans))

    # ── (c12) LES LIENS : FICHIER PRESENT, TITRE PRESENT, ⛔ RELATIF DANS .github/
    print("\n── (c12)(c13) LES CITATIONS, ET LE COVENANT HORS DE LA TABLE ─────")
    # ⚠️ ELARGI A LA REVUE DU 2026-09-13 : la 1re forme sautait tout lien SANS `#`.
    #    Or les liens `blob/main/` ABSOLUS (bug report → SECURITY.md, modele de PR
    #    → CLA.md, LICENSING.md…) ne sont resolus par AUCUNE autre gate
    #    (`verif_licences_dn52.py` saute les `http`), et un lien RELATIF dans un
    #    gabarit de `.github/` est resolu par GitHub contre la page de l'issue.
    f12, vus12, frag12 = [], 0, 0
    for rel in NEUFS + (VITRINE,):
        txt = fichiers[rel] or ""
        visees = set(cibles_de_liens(txt)) | {
            u.rstrip(".,;:") for u in RE_BLOB_NU.findall(txt)}
        for cible in sorted(visees):
            chemin, _, frag = cible.partition("#")
            if cible.startswith(BLOB):
                visee = chemin[len(BLOB):]
            elif cible.startswith(("http:", "https:", "mailto:")):
                continue
            elif rel.startswith(".github/"):
                f12.append("%s : lien RELATIF %r" % (rel, cible))
                continue
            elif not chemin:
                visee = rel
            else:
                visee = os.path.normpath(os.path.join(os.path.dirname(rel), chemin))
            vus12 += 1
            if visee not in fichiers and not os.path.exists(os.path.join(RACINE, visee)):
                f12.append("%s → %s INTROUVABLE" % (rel, visee))
                continue
            if not frag or not visee.endswith(".md"):
                continue
            frag12 += 1
            txt_v = fichiers[visee] if visee in fichiers else charge_fichier(visee)
            if txt_v is None:
                f12.append("%s → %s ILLISIBLE" % (rel, visee))
            elif frag not in ancres(txt_v):
                f12.append("%s → %s#%s : AUCUN titre" % (rel, visee, frag))
    ctrl(vus12 > 0 and frag12 > 0 and not f12,
         "(c12) liens : cible presente, titre present, 0 relatif",
         "%d lien(s) resolu(s) dont %d a fragment ; 0 relatif dans .github/"
         % (vus12, frag12) if vus12 and frag12 and not f12
         else "⛔ " + (" · ".join(f12[:3]) if f12 else "AUCUN lien a confronter"))

    # ── (c13) LE COVENANT HORS DU BLOC `## Firmware` ───────────────────────
    tiers = fichiers[TIERS]
    f13 = []
    if tiers is None:
        f13.append("%s ILLISIBLE" % TIERS)
    else:
        bloc = section_md(tiers, "Firmware") or ""
        if not bloc:
            f13.append("bloc `## Firmware` INTROUVABLE")
        if COVENANT_NOM in bloc:
            f13.append("le Covenant est DANS la table `## Firmware`")
        hors_table = tiers.replace(bloc, "") if bloc else ""
        if COVENANT_NOM not in hors_table:
            f13.append("le Covenant n'est nomme NULLE PART hors de la table")
    ctrl(not f13, "(c13) THIRD-PARTY.md nomme le Covenant hors table",
         "en prose, hors `## Firmware`" if not f13 else "⛔ " + " · ".join(f13))

    # ── (c14)(c15)(c16) LA RECIPROQUE ──────────────────────────────────────
    print("\n── (c14)(c15)(c16) AUCUN CONTROLE GARDE PAR ZERO MUTANT ──────────")
    reels = dn_gates.ids_par_ast(os.path.abspath(__file__))
    vises = set()
    for v in cibles.values():
        vises.update(v)
    nus = sorted((reels or set()) - vises, key=lambda x: (len(x), x))
    ctrl(not nus and reels is not None,
         "(c14) chaque controle est vise par >= 1 mutant",
         "%d controle(s) lu(s) a l'AST, %d cible(s) declaree(s)"
         % (len(reels), len(vises)) if not nus and reels is not None
         else ("⛔ %d CONTROLE(S) GARDE(S) PAR RIEN : %s"
               % (len(nus), " · ".join(nus)) if nus
               else "⛔ LA SOURCE NE S'ANALYSE PAS A L'AST — population INCONNUE"))
    perimees = sorted(vises - (reels or set()), key=lambda x: (len(x), x))
    ctrl(not perimees, "(c15) chaque cible de mutant est un controle REEL",
         "%d cible(s) confrontee(s)" % len(vises) if not perimees
         else "⛔ %d CIBLE(S) PERIMEE(S) : %s" % (len(perimees),
                                                " · ".join(perimees)))
    orph = sorted(set(cibles) - set(MUTANTS))
    sans_cible = sorted(set(MUTANTS) - set(cibles))
    ctrl(not orph and not sans_cible,
         "(c16) `CIBLES` et `MUTANTS` se correspondent",
         "%d mutant(s), %d cible(s), cle a cle" % (len(MUTANTS), len(cibles))
         if not orph and not sans_cible
         else "⛔ cible(s) SANS mutant : %s · mutant(s) SANS cible : %s"
              % (orph or "—", sans_cible or "—"))

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : qu'un inconnu ATTEINT le formulaire")
    print("   prive (le depot est prive, le reglage n'existe que sur un depot public)")
    print("   ni que GitHub ACCEPTE les formulaires — voir AVEUGLEMENT DECLARE en tete.")
    return bilan(1 if dn_gates.ko_total[0] else 0, prevus=CONTROLES_PREVUS)


def main():
    # 🔴 UNE GATE QUI MEURT SORTIRAIT EN TRACE, SANS `BILAN` — or « pas de
    #    BILAN » est le discriminant d'une gate MORTE. ⇒ l'exception imprevue
    #    se rend en sortie anticipee NOMMEE, `rc=1`.
    try:
        return corps()
    except SystemExit:
        raise
    except Exception as x:                                # noqa: BLE001
        print("\n⛔ EXCEPTION IMPREVUE : %s: %s" % (type(x).__name__, str(x)[:120]))
        return bilan(1, anticipee="exception imprevue — la faute est dans la "
                                  "GATE, ⛔ pas un verdict", prevus=CONTROLES_PREVUS)


if __name__ == "__main__":
    sys.exit(main())

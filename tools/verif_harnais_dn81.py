# -*- coding: utf-8 -*-
"""dn8-1 — LES GATES PARSENT CE QU'ELLES JUGENT, ET LEURS HELPERS VIVENT EN UN
SEUL ENDROIT.

Trois familles de controles, et ⛔ AUCUNE refonte des 44 gates existantes :

  (c1)  un des 8 helpers de `dn_gates.py` RE-DEFINI dans un fichier du
        perimetre `dn8` — que le corps DIVERGE ou qu'il soit IDENTIQUE.
  (c2)  une ancre `📍` du ledger sans cible atteignable, ou dont le motif ne
        se retrouve pas dans sa cible APRES normalisation.
  (c3)  un controle ECRIT PAR `dn8` qui juge du YAML / HTML / CSS / PowerShell
        sans parseur **et** sans declaration d'aveuglement.

── 🔴 LA FRONTIERE, ET POURQUOI ELLE EST LA ────────────────────────────────

⛔ CETTE GATE NE JUGE PAS LES 44 GATES EXISTANTES. `epic-dn8` installe le
   garde-fou **pour ce qu'elle ECRIT** ; l'hygiene des 44 est le territoire
   `dn4`. ⚠️ ET CE N'EST PAS UN VŒU : le perimetre est DERIVE (voir
   `perimetre_dn8()`), il s'etend tout seul aux gates que `dn8-2` et `dn8-4`
   ecriront, et il ⛔ ne peut pas etre elargi par distraction aux autres.

⚠️ **UNE SEULE EXCEPTION, ET ELLE EST NOMMEE** : les REGIONS delimitees par
   `>>> DN8-REGION` / `<<< DN8-REGION` dans un fichier qui appartient a une
   autre marche. Aujourd'hui il y en a deux, toutes dans
   `tools/verif_ledger_dn416.py`, ou `dn8-1` a ajoute **un seul controle**.
   ⇒ (c3) juge ces regions ; (c1) ⛔ NON — une region ne definit pas de
     helper, et exiger d'un fichier `dn4` qu'il importe `dn_gates` serait
     refondre les 44 gates par la porte de derriere.

── 🔴 CE QUE (c1) PUBLIE SANS LE JUGER, ET POURQUOI C'EST ECRIT ────────────

Les **101 copies / 57 implementations distinctes** mesurees le 2026-09-11 dans
les 44 gates sont **INVENTORIEES ET IMPRIMEES** a chaque passe, ⛔ jamais
comptees KO. Un inventaire imprime est falsifiable (il bouge quand l'arbre
bouge) ; un silence ne l'est pas. ⛔ Ce n'est ⛔ NI un OK ⛔ NI un KO : c'est
un ECART DECLARE dont le porteur est `epic-dn4`.

── ⚠️ CE QUE CETTE GATE NE SAIT PAS VOIR, DIT EN PROPRE ────────────────────

Elle cherche les motifs d'ancre **EN TEXTE**, y compris dans des fichiers
HTML, CSS et PowerShell — ⛔ sans aucun parseur. Une ancre qui vise une
STRUCTURE (un selecteur, un attribut, un bloc) est donc verifiee comme de la
prose. C'est exactement l'aveuglement que `NFR14` autorise A CONDITION qu'il
soit nomme : il l'est, dans `AVEUGLEMENT_HTML` et `AVEUGLEMENT_POWERSHELL`,
et ces deux declarations sont IMPRIMEES, ⛔ pas seulement ecrites.

⚠️ ⛔ AUCUN LITTERAL DE CE FICHIER NE PORTE UN NOM DE FICHIER SUIVI D'UNE
   EXTENSION `.yaml/.html/.css/.ps1` HORS DOCSTRING ET HORS COMMENTAIRE, sauf
   ceux que (c3) doit VRAIMENT voir. C'est une contrainte de ce fichier sur
   lui-meme, et elle est ecrite parce qu'elle est INVISIBLE : la violer ferait
   rougir (c3) sur la documentation de (c3).

Usage :
    python3 tools/verif_harnais_dn81.py [--cockpit <chemin>]
    python3 tools/verif_harnais_dn81.py --liste-mutants
    python3 tools/verif_harnais_dn81.py --mutant <n>

Codes de sortie : 0 vert · 1 vrai defaut · 2 usage / mutant inconnu ·
                  3 mutant PERIME (il n'a rien change) · 4 prerequis absent.
"""
import argparse
import ast
import copy
import glob
import hashlib
import io
import os
import re
import sys
import unicodedata

# 🔴 dn8-1 / AC8.1.3 — LES HELPERS VIVENT DANS `dn_gates`. Import FRERE, patron
#    `dn_trace.py`. ⛔ L'IMPORT N'EST PAS DEFENSIF ICI, ET C'EST UN CHOIX :
#    cette gate ne fait rien sans le module qu'elle garde. Mais elle ⛔ ne
#    plante pas non plus — elle NOMME le motif et sort en 1. Un `Traceback` est
#    indiscernable d'une gate morte.
try:
    import dn_gates
except ImportError as _x:                                # pragma: no cover
    sys.stderr.write(
        "⛔ `tools/dn_gates.py` est INTROUVABLE (%s).\n"
        "   Cette gate garde ce module : sans lui elle n'a rien a juger.\n"
        "   ⛔ Ce n'est PAS un prerequis d'environnement (rc=4) : le module\n"
        "      vit DANS ce depot, a cote de ce fichier. C'est un defaut.\n" % _x)
    sys.exit(1)

ctrl = dn_gates.ctrl
bilan = dn_gates.bilan
plat = dn_gates.plat

DESKNODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ⚠️ `HOME` LU COMME LE SHELL LE LIT, avec la MEME valeur de repli que
#    `run_gates.sh` — `expanduser("~")` interroge `/etc/passwd` et diverge en
#    cron / conteneur / `env -i`. Le precedent est mesure dans
#    `verif_ledger_dn416.py`.
COCKPIT_DEFAUT = os.path.join(os.environ.get("HOME") or "/nonexistent",
                              "projects", "compagnon_project")
RC_PREREQUIS = 4
RC_MUTANT_PERIME = 3

REL_LEDGER = "_bmad-output/implementation-artifacts/deferred-work.md"

# Le prefixe de depot qu'une ancre peut nommer, et ou il se resout.
PREFIXES = ("desknode", "compagnon_project", "compagnon", "cockpit")

# ── (c3) LES QUATRE STRUCTURES, LEURS EXTENSIONS ET LEURS PARSEURS ─────────
# ⚠️ LES EXTENSIONS SONT ECRITES **SANS TIGE** (`.yaml`, ⛔ pas `un.yaml`) :
#    le detecteur de sujet exige une tige, si bien que cette table ⛔ ne se
#    designe pas elle-meme. C'est la contrainte annoncee en tete de fichier.
STRUCTURES = {
    "yaml": ((".yaml", ".yml"),
             ("yaml.safe_load", "yaml.load", "yaml.full_load")),
    "html": ((".html", ".htm"),
             ("html.parser", "HTMLParser", "ElementTree.fromstring",
              "etree.HTML")),
    "css": ((".css",),
            ("tinycss", "cssutils", "css_parser")),
    "powershell": ((".ps1", ".psm1"),
                   ("System.Management.Automation.Language",
                    "PSParser", "Language.Parser")),
}
# Un SUJET est un chemin, ⛔ pas une extension nue : il faut une tige devant le
# point. C'est ce qui empeche la table ci-dessus d'etre son propre sujet.
RE_SUJET = re.compile(r"[\w~][\w.\-]*\.(yaml|yml|html|htm|css|ps1|psm1)\b",
                      re.I)
# 🔴 LES MARQUEURS SONT ANCRES **EN TETE DE COMMENTAIRE**, ⛔ PAS N'IMPORTE OU
#    DANS LA LIGNE — ET C'EST UNE MESURE, ⛔ PAS UNE PRECAUTION. Premiere
#    ecriture : un motif NU. La toute premiere passe a rendu
#    `1 ouverture / 0 fermeture` **sur CE fichier-ci** : le docstring de tete
#    cite les deux marqueurs SUR LA MEME LIGNE pour les expliquer, la branche
#    d'ouverture matchait et `continue`-ait, et la fermeture n'etait jamais
#    comptee. ⇒ le controle rougissait sur la DOCUMENTATION de sa propre regle
#    — exactement le defaut que `sans_commentaires` ferme cote script.
#    ⛔ Un motif qui classe une reponse s'ancre sur ce que la commande imprime
#      EN PROPRE : ici, sur la FORME que le marqueur a quand il est reel.
RE_REGION_DEB = re.compile(r"^\s*#\s*>>>\s*DN8-REGION", re.M)
RE_REGION_FIN = re.compile(r"^\s*#\s*<<<\s*DN8-REGION", re.M)

# ── LES DEUX AVEUGLEMENTS DE CETTE GATE, DECLARES EN PROPRE (NFR14) ───────
AVEUGLEMENT_HTML = (
    "⛔ LES MOTIFS D'ANCRE SONT CHERCHES EN TEXTE, ⛔ PAS PARSES. Une ancre "
    "qui vise une structure de page (un selecteur, un attribut, un bloc) est "
    "verifiee comme de la prose : elle passe si la chaine existe QUELQUE "
    "PART, meme dans un commentaire, meme coupee de son sens. ⛔ Ce depot n'a "
    "AUCUN parseur CSS (mesure : 44 gates, 0 parseur CSS) et n'en pose pas "
    "un ici — le sujet de cette marche est l'INSTRUMENT, ⛔ pas la page.")
AVEUGLEMENT_POWERSHELL = (
    "⛔ IDEM POUR LE POWERSHELL : un motif d'ancre qui designe une fonction "
    "ou un parametre est cherche en TEXTE. Un parseur PowerShell exigerait "
    "un runtime .NET, que la CI ⛔ n'a pas — et `pip install` y est interdit.")

# ── (c2d) LES TEMOINS DE LA NORMALISATION — ⛔ PAS UNE POPULATION VIDE ─────
# 🔴 POURQUOI UNE TABLE ECRITE PLUTOT QUE LE SEUL LEDGER : le ledger prouve
#    que la normalisation SERT (7 ancres ne se trouvent QU'apres elle) ; il ⛔
#    ne prouve PAS qu'elle ne soit pas un TAMIS. Une normalisation qui jette
#    tout sauf les lettres ferait passer le ledger entier — et rendrait le
#    controle inutile sans qu'une seule ligne rougisse.
# ⇒ LES DEUX SENS SONT ECRITS. `DOIT` : ce que la normalisation doit
#   RAPPROCHER. `REFUSE` : ce qu'elle ⛔ ne doit PAS rapprocher.
# ⚠️ CE QUE CETTE TABLE PROUVE, ET CE QU'ELLE NE PROUVE PAS : elle attrape une
#    normalisation devenue trop large sur CES cas-la. ⛔ Elle ne demontre pas
#    l'absence de tout tamis — aucune table finie ne le peut, et le pretendre
#    serait le defaut que cette marche denonce.
NORM_DOIT = (
    ("accents", "deja sur la tour", "déjà sur la tour"),
    ("casse", "AUCUNE CHAINE", "aucune chaine"),
    ("tirets", "pyserial -- deja", "pyserial — déjà"),
    ("apostrophe", "n'est mecanisee", "n\u2019est mécanisée"),
    ("marqueur", "aucun tag et aucune release", "⛔ aucun tag et ⛔ aucune release"),
    ("espaces", "propriete de la METHODE", "propriété  de\n   la MÉTHODE"),
)
NORM_REFUSE = (
    ("une lettre", "autoportance", "autoportanse"),
    ("un mot en moins", "def citations du dossier", "def citations"),
    ("chiffre", "epic-dn8", "epic-dn9"),
    ("negation", "aucun tag", "un tag"),
)

MUTANTS = {}                       # ⛔ AU NIVEAU MODULE — `--liste-mutants`
CIBLES = {}                        # le controle que chaque mutant doit ROUGIR

MUTANTS[1] = ("REPLANTE une re-definition DIVERGENTE de `ctrl` dans un "
              "fichier du perimetre dn8")
CIBLES[1] = ("c1d",)
MUTANTS[2] = ("REPLANTE une re-definition IDENTIQUE de `plat` (meme corps "
              "que le module) — une copie reste une copie")
CIBLES[2] = ("c1d",)
MUTANTS[3] = ("REPLANTE une DERIVE du corps de `plat` dans `dn_gates` : il "
              "est declare VERBATIM, il ne l'est plus")
CIBLES[3] = ("c1b",)
MUTANTS[4] = ("REPLANTE la divergence entre `NOMS_PARTAGES` et `__all__` — "
              "une liste recopiee qui a decroche")
CIBLES[4] = ("c1a",)
MUTANTS[5] = ("REPLANTE une DECLARATION DE TRANSFORMATION PERIMEE : le corps "
              "redevient le modal, la declaration reste")
CIBLES[5] = ("c1c",)
MUTANTS[6] = ("REPLANTE une ancre `📍` dont le CHEMIN n'existe pas")
CIBLES[6] = ("c2a",)
MUTANTS[7] = ("REPLANTE une ancre `📍` dont le MOTIF a disparu de sa cible")
CIBLES[7] = ("c2b",)
MUTANTS[8] = ("REPLANTE une ancre `📍` dont le motif ne differe du vrai que "
              "d'UNE LETTRE — le piege d'une normalisation-tamis")
CIBLES[8] = ("c2b",)
MUTANTS[9] = ("REPLANTE la population VIDE de (c2c) : dans LE LEDGER, tout "
              "motif qui n'est trouve qu'apres normalisation est reecrit en "
              "un motif LITTERAL de sa propre cible")
CIBLES[9] = ("c2c",)
MUTANTS[10] = ("REPLANTE un TEMOIN NEGATIF qui n'en est pas un : une paire "
               "`REFUSE` dont le motif est REELLEMENT present")
CIBLES[10] = ("c2d",)
MUTANTS[11] = ("REPLANTE un controle de `dn8` qui juge du YAML SANS parseur "
               "et SANS declaration d'aveuglement")
CIBLES[11] = ("c3b",)
MUTANTS[12] = ("REPLANTE un marqueur de region NON APPARIE (l'ouverture "
               "reste, la fermeture disparait)")
CIBLES[12] = ("c3a",)
MUTANTS[13] = ("REPLANTE la population VIDE de (c3c) : plus aucune region "
               "de `dn8` ne nomme une structure")
CIBLES[13] = ("c3c",)
MUTANTS[14] = ("REPLANTE une gate qui joue MOINS de controles qu'elle "
               "n'annonce : un controle de fond est SAUTE")
CIBLES[14] = ("z",)
MUTANTS[15] = ("REPLANTE une region de `dn8` en `grep` PUR **A COTE** de la "
               "region qui parse — le cas que le mutant 11 ⛔ ne peut PAS "
               "atteindre, puisqu'il remplace sur tout le fichier")
CIBLES[15] = ("c3b",)

# ⚠️ **LE SEUL IDENTIFIANT QUE ⛔ AUCUN MUTANT NE VISE, ET SON MOTIF.**
#    `(c0)` est le PRE-VOL : c'est lui qui garde les mutants eux-memes (cible
#    et libelle declares, mutant sans EFFET ⇒ `rc=3`, mutant qui LEVE ⇒ `rc=1`).
#    Un mutant qui le viserait devrait se saboter lui-meme. ⚠️ Ce qui le garde
#    a la place est un TEMOIN REEL, ⛔ pas une promesse : une copie de `tools/`
#    ou l'ancre litterale d'un mutant est cassee fait sortir la gate en
#    **`rc=3`** — releve dans `mesures/dn8-1/T2`.
IDS_SANS_MUTANT = {
    "c0": "le pre-vol GARDE les mutants ; temoin rc=3 dans mesures/dn8-1/T2",
}

# ⚠️ ⛔ Il est ECRIT parce que `bilan()` le VERIFIE : une gate qui joue MOINS
#    de controles qu'annonce sort VERTE sur une population RETRECIE.
# ⚠️ LE COMPTE DU CHEMIN NORMAL, ET IL SE LIT : **2** pre-vols fixes (le
#    terrain, puis la reciproque cibles/identifiants) + **un controle par
#    mutant declare** + les **11** controles de fond (`c1a`-`c1d`, `c2a`-`c2d`,
#    `c3a`-`c3c`). ⚠️ Le commentaire d'origine disait « 12 controles de fond »
#    alors que le code en comptait 11 et que le tir en emettait 11 : le chiffre
#    ecrit ⛔ ne decrivait pas le code. Corrige, ⛔ pas efface.
CONTROLES_PREVUS = 2 + len(MUTANTS) + 11

_MUTANT = 0


# ══ LECTURE, EMPREINTE, NORMALISATION ═══════════════════════════════════════

def empreinte(node, avec_prose=True):
    """L'empreinte d'un CORPS de fonction, positions exclues.

    ⚠️ `include_attributes=False` : deux corps identiques a l'indentation et
    aux numeros de ligne pres rendent la MEME empreinte. C'est ce qui permet
    de distinguer « copie a l'identique » de « copie divergente », au lieu de
    les confondre dans un `!=` textuel qui aurait rougi sur un espace.

    🔴 **DEUX EMPREINTES, ET LE CHOIX EST MESURE.** `avec_prose=True` inclut
       le DOCSTRING ; `False` l'ecarte. Les deux existent parce qu'elles
       repondent a deux questions differentes, et les confondre a coute une
       passe entiere le 2026-09-11 :
       · **l'INVENTAIRE** des 44 gates se publie AVEC la prose — c'est la
         mesure que le dossier de `dn8-1` porte (**101 copies / 57
         implementations**), et la reproduire a l'identique est ce qui permet
         de dire que rien n'a bouge ;
       · **la COMPARAISON** au module se fait SANS la prose. `dn_gates.py`
         ajoute a chaque helper une section `PROVENANCE` qui NOMME sa
         population : avec la prose, les 8 corps auraient tous diverge du
         modal, et (c1b) aurait rougi sur la DOCUMENTATION qu'il exige.
         ⛔ « la meme implementation » est une propriete du CODE, ⛔ pas de ce
         qui l'explique — c'est la regle que `sans_commentaires` applique au
         script et que `style_de` a payee cote CSS.
    """
    n = copy.deepcopy(node)
    n.name = "_"                       # le NOM ne fait pas le corps
    if not avec_prose:
        corps = list(n.body)
        if corps and isinstance(corps[0], ast.Expr) \
                and isinstance(corps[0].value, ast.Constant) \
                and isinstance(corps[0].value.value, str):
            corps = corps[1:] or [ast.Pass()]
        n.body = corps
    return hashlib.sha256(
        ast.dump(n, annotate_fields=True,
                 include_attributes=False).encode()).hexdigest()[:10]


def defs_de(source, noms, avec_prose=True):
    """{nom: [empreintes]} des fonctions de `source` qui portent un `nom`."""
    out = {}
    try:
        arbre = ast.parse(source)
    except SyntaxError:
        return None
    for n in ast.walk(arbre):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and n.name in noms:
            out.setdefault(n.name, []).append(empreinte(n, avec_prose))
    return out


def norm(t):
    """La forme NORMALISEE d'un texte, pour qu'une ancre soit trouvee TELLE
    QU'ELLE EST ECRITE.

    🔴 CE QU'ELLE RAPPROCHE, ET C'EST MESURE SUR LE LEDGER DU 2026-09-11 :
       · les ACCENTS (`deja` ⇄ `déjà`) — 3 ancres ;
       · la CASSE (`METHODE` ⇄ `méthode`) — 2 ancres ;
       · les TIRETS de toute longueur, et leurs REPETITIONS (`--` ⇄ `—`) ;
       · les APOSTROPHES typographiques ;
       · les MARQUEURS (`⛔`, `⚠️`, `🔴`) que la prose du depot seme partout ;
       · les BLANCS, retours a la ligne compris — un motif ⛔ ne doit pas
         dependre de l'endroit ou la prose a ete coupee.
    ⛔ CE QU'ELLE NE RAPPROCHE PAS, ET C'EST LE POINT : les LETTRES et les
       CHIFFRES. `autoportance` ⛔ n'est pas `autoportanse`, `epic-dn8` ⛔
       n'est pas `epic-dn9`. La table `NORM_REFUSE` le tient.
    """
    t = unicodedata.normalize("NFD", t or "")
    t = "".join(c for c in t
                if unicodedata.category(c) not in ("Mn", "So", "Cf"))
    t = t.lower()
    t = re.sub(r"[\u2010-\u2015\u2212]", "-", t)
    t = re.sub(r"[\u2018\u2019\u201b\u2032]", "'", t)
    t = re.sub(r"[\u201c\u201d]", '"', t)
    t = re.sub(r"-+", "-", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


# ══ LE PERIMETRE — DERIVE, ⛔ PAS RECOPIE ═══════════════════════════════════

def perimetre_dn8():
    """Les fichiers ECRITS PAR `dn8`, en chemins relatifs au depot.

    🔴 DERIVE, ⛔ PAS UNE LISTE EN DUR. Une liste en dur ne couvrirait pas les
       gates que `dn8-2` et `dn8-4` vont ecrire — et c'est precisement pour
       elles que ce garde-fou existe. ⚠️ Le prix est ecrit : le perimetre
       depend d'une CONVENTION DE NOM (`*dn8*`). Une gate de `dn8` nommee
       autrement sortirait du perimetre EN SILENCE ; (c0) rougit si le
       perimetre est vide, ⛔ il ne peut pas dire ce qu'il ne voit pas.
    """
    vus = {"tools/dn_gates.py"}
    for p in sorted(glob.glob(os.path.join(DESKNODE, "tools", "*dn8*.py"))):
        vus.add(os.path.relpath(p, DESKNODE).replace(os.sep, "/"))
    return sorted(vus)


def regions_dn8(source):
    """Les REGIONS `dn8` d'un fichier, et les marqueurs NON APPARIES.

    Rend `(regions, deb, fin)` — `regions` est une liste de textes, `deb` et
    `fin` les comptes de marqueurs d'ouverture et de fermeture. ⛔ On ⛔ ne
    « repare » pas un marqueur orphelin : (c3a) le fait rougir.
    """
    lignes = (source or "").split("\n")
    regions, courante, deb, fin = [], None, 0, 0
    for l in lignes:
        if RE_REGION_DEB.search(l):
            deb += 1
            courante = []
            continue
        if RE_REGION_FIN.search(l):
            fin += 1
            if courante is not None:
                regions.append("\n".join(courante))
            courante = None
            continue
        if courante is not None:
            courante.append(l)
    return regions, deb, fin


def fichiers_a_regions():
    """Les fichiers de `tools/` qui portent au moins un marqueur de region."""
    out = []
    for p in sorted(glob.glob(os.path.join(DESKNODE, "tools", "*.py"))):
        rel = os.path.relpath(p, DESKNODE).replace(os.sep, "/")
        try:
            t = io.open(p, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        if RE_REGION_DEB.search(t) or RE_REGION_FIN.search(t):
            out.append(rel)
    return out


# ══ (c1) L'INVENTAIRE DES 44 GATES — PUBLIE, ⛔ PAS JUGE ════════════════════

def inventaire_legacy(hors):
    """{nom: (copies, implementations distinctes, [fichiers])} sur les gates
    QUI NE SONT PAS DANS LE PERIMETRE `dn8`.

    ⚠️ `hors` EXCLUT LE PERIMETRE, ET C'EST LOAD-BEARING : sans cette
       exclusion, un mutant qui plante une copie dans une gate `dn8`
       DEPLACERAIT le corps modal, et (c1b) rougirait pour le mauvais motif.
    """
    par = {}
    for p in sorted(glob.glob(os.path.join(DESKNODE, "tools", "verif_*.py"))):
        rel = os.path.relpath(p, DESKNODE).replace(os.sep, "/")
        if rel in hors:
            continue
        try:
            src = io.open(p, encoding="utf-8").read()
            arbre = ast.parse(src)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        for n in ast.walk(arbre):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and n.name in dn_gates.NOMS_PARTAGES:
                par.setdefault(n.name, []).append(
                    (rel, empreinte(n, True), empreinte(n, False)))
    return par


# ⚠️ **LE DEPARTAGE DES EGALITES, DECLARE — ⛔ PAS ARBITRE PAR UN TRI DE
#    HACHAGE.** Mesure du 2026-09-11 : `ctrl` a **DEUX** corps a **5 copies**
#    chacun. « L'implementation la plus jouee » ⛔ n'existe donc pas pour lui :
#    c'est une EGALITE, et la trancher par l'ordre alphabetique d'un sha256
#    serait un choix pris par personne, invisible, et qui bougerait au premier
#    octet change. ⇒ le fichier PORTEUR du corps retenu est ECRIT ici, et
#    (c1b) rougit sur toute egalite qui n'est PAS departagee.
#    🔴 MOTIF DU CHOIX POUR `ctrl` : le corps retenu est celui des 5 gates de
#       `dn4-5`/`dn4-13`, qui n'ont ⛔ AUCUNE dependance de contexte. Le groupe
#       concurrent (`verif_campagne_dn56.py` & co) en a. A egalite de
#       popularite, le corps PORTABLE est le seul des deux qu'un module
#       partage puisse porter sans lever une lecture de contexte de plus.
#    ⚠️ TROIS EGALITES SUR HUIT, MESUREES LE 2026-09-11 : `ctrl` (5-5),
#       `bloc_regle` (1-1) et `style_de` (1-1). ⛔ Aucune n'etait visible avant
#       que ce controle ne la nomme — le premier tri les avait tranchees par
#       l'ordre alphabetique d'un sha256, et la passe suivante aurait pu les
#       trancher AUTREMENT sans qu'une ligne ne bouge.
#    🔴 MOTIF DU CHOIX POUR `bloc_regle` ET `style_de` : le corps de
#       `verif_placement_dn74.py` est celui dont le docstring PORTE LA MESURE
#       du 2026-09-10 (le leurre en commentaire CSS qui reverdissait la gate).
#       A egalite de popularite, le corps qui porte la preuve de sa propre
#       regle est celui qu'un module partage doit publier.
DEPARTAGE = {
    "ctrl": "tools/verif_bme680_retard_dn45.py",
    "bloc_regle": "tools/verif_placement_dn74.py",
    "style_de": "tools/verif_placement_dn74.py",
}


class Modal(object):
    """Le verdict de `modal()` — nomme, ⛔ pas un tuple a indexer de tete.

    ⚠️ UN TUPLE A 6 CHAMPS INDEXE PAR POSITION EST UN PIEGE MESURE : le
    passage de 3 a 5 champs, le 2026-09-11, a fait lire `[0]` (l'empreinte
    AVEC la prose) la ou `[1]` (SANS) etait attendue — et (c1b) a rougi sur un
    corps qui etait pourtant le bon.
    """

    __slots__ = ("prose", "code", "copies", "impl_prose", "impl_code",
                 "ex_aequo")

    def __init__(self, prose, code, copies, impl_prose, impl_code, ex_aequo):
        self.prose, self.code, self.copies = prose, code, copies
        self.impl_prose, self.impl_code = impl_prose, impl_code
        self.ex_aequo = ex_aequo


def modal(par, nom):
    """Le corps LE PLUS JOUE de `nom`, et ses deux empreintes.

    Rend un `Modal` : `.prose`, `.code`, `.copies`, `.impl_prose`,
    `.impl_code`, `.ex_aequo` (les empreintes A EGALITE, vide s'il n'y en a
    pas).

    🔴 **LE GROUPE MODAL EST CHOISI SUR LA MESURE ⊕ (prose comprise), ET LA
       COMPARAISON SE FAIT SUR ⊖.** C'est un choix, il a un motif, et le
       motif est une MESURE du 2026-09-11 :
       · ⊕ est la mesure que le dossier de `dn8-1` publie (**101 / 57**) et
         que ce module reproduit a l'identique — c'est elle qui a designe les
         corps retenus dans `dn_gates.py` ;
       · ⊖ est la seule qui puisse dire « meme implementation » une fois que
         `dn_gates.py` a ajoute sa section `PROVENANCE`.
    ⚠️ **ET LES DEUX MESURES ⛔ NE DESIGNENT PAS LE MEME CORPS.** Mesure :
       pour `ctrl`, ⊕ designe un corps a **5 porteuses** (le corps simple,
       retenu par `dn_gates`) ; ⊖ en designe un autre, a **7 porteuses** —
       celui qui assert la LARGEUR du libelle et enregistre les identifiants
       emis (`LARGEUR_LIBELLE`, `ids_emis`). ⛔ « l'implementation la plus
       jouee » n'est donc PAS une propriete du corpus : c'est une propriete
       de la METRIQUE. Les deux sont imprimees a chaque passe plutot que
       tranchees en silence.
    """
    lst = par.get(nom, [])
    if not lst:
        return Modal(None, None, 0, 0, 0, ())
    comptes, porteuses = {}, {}
    for rel, ep, ec in lst:
        comptes.setdefault(ep, [0, ec])[0] += 1
        porteuses.setdefault(ep, []).append(rel)
    haut = max(v[0] for v in comptes.values())
    tetes = sorted(e for e, v in comptes.items() if v[0] == haut)
    ep = tetes[0]
    choix = DEPARTAGE.get(nom)
    if choix:
        for e in tetes:
            if choix in porteuses[e]:
                ep = e
                break
    return Modal(ep, comptes[ep][1], comptes[ep][0], len(comptes),
                 len({ec for _, _, ec in lst}),
                 tuple(tetes) if len(tetes) > 1 else ())


# ⚠️ LES TROIS HELPERS DONT LE CORPS A ETE TRANSFORME, ET **LA LECTURE DE
#    CONTEXTE QUI L'A EXIGE**. ⛔ Ce n'est pas une liste d'exemptions : (c1c)
#    verifie que chaque nom cite ici a VRAIMENT un corps different du modal.
#    Une declaration qui a cesse d'etre vraie est un KO — c'est le mutant 5.
TRANSFORMES = {
    "style_de": "RE_STYLE",
    "bilan": "CONTROLES_PREVUS",
    "ids_par_ast": "__file__",
}


# ══ (c2) LES ANCRES DU LEDGER ═══════════════════════════════════════════════

def ancres_du(texte):
    """Les CIBLES des ancres `📍` : (ligne, texte, depot, chemin, [motifs]).

    ⚠️ UNE LIGNE QUI **MENTIONNE** `📍` N'EST PAS UNE ANCRE. Mesure du
       2026-09-11 : sur 87 lignes portant le glyphe, **une** est de la prose
       qui le cite entre accents graves. ⇒ l'ancre est la ligne dont le
       glyphe est EN TETE apres depouillement — ⛔ pas n'importe ou.
    ⚠️ LE MOTIF EST CE QUI EST ENTRE ACCENTS GRAVES, ⛔ pas la parenthese
       entiere : le ledger y ecrit aussi des listes (`constats 2, 4, 6, 8`) et
       des gloses. La prescription du ledger dit la meme chose — *« preuve
       doit etre un MOTIF : un symbole, une chaine, un titre de docblock »*.
    """
    out = []
    for i, l in enumerate((texte or "").split("\n"), 1):
        st = l.strip()
        if not st.startswith("\U0001F4CD"):
            continue
        for part in re.split(r"\s+·\s+", st[1:].strip()):
            part = part.strip()
            if not part:
                continue
            m = re.match(r"^(?:(%s):)?\s*([^\s()`]+)(.*)$"
                         % "|".join(PREFIXES), part)
            if not m:
                out.append((i, part, None, None, []))
                continue
            out.append((i, part, m.group(1) or "cockpit", m.group(2),
                        re.findall(r"`([^`]+)`", m.group(3))))
    return out


def resout(depot, chemin, cockpit):
    """Le chemin REEL d'une cible d'ancre, ou None."""
    base = DESKNODE if depot == "desknode" else cockpit
    cands = [os.path.join(base, chemin)]
    if depot != "desknode":
        cands.append(os.path.join(base, "_bmad-output",
                                  "implementation-artifacts", chemin))
    for c in cands:
        if os.path.exists(c):
            return c
    return None


# ══ (c3) LE SUJET, LE PARSEUR, L'AVEUGLEMENT ════════════════════════════════

def _constantes_hors_docstring(source):
    """Les chaines LITTERALES d'un source, docstrings EXCLUES.

    🔴 POURQUOI EXCLURE LES DOCSTRINGS : ce depot documente ses regles dans
       ses propres fichiers. Une gate qui compte la prose de sa documentation
       rougirait sur l'explication de sa regle — le defaut exact que
       `sans_commentaires` ferme cote script, et que `style_de` a paye cote
       CSS. ⛔ Un `grep` ne sait pas faire cette difference ; l'AST, si.
    """
    try:
        arbre = ast.parse(source)
    except SyntaxError:
        return None
    docs = set()
    for n in ast.walk(arbre):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef,
                          ast.AsyncFunctionDef)):
            corps = getattr(n, "body", None) or []
            if corps and isinstance(corps[0], ast.Expr) \
                    and isinstance(corps[0].value, ast.Constant) \
                    and isinstance(corps[0].value.value, str):
                docs.add(id(corps[0].value))
    return [n.value for n in ast.walk(arbre)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and id(n) not in docs]


def sujets_de(bloc, source_entier, fichier_entier=False):
    """Les structures que ce bloc JUGE : {langue} — ⛔ vide s'il n'en juge
    aucune.

    Un bloc JUGE une structure s'il emet un verdict (`ctrl(`) **et** qu'il
    nomme un chemin de cette structure — soit directement, soit par une
    CONSTANTE DE MODULE dont la valeur en porte un.

    🔴 **LA MATIERE EST CE QUI S'EXECUTE, ⛔ PAS CE QUI L'EXPLIQUE — ET C'EST
       UNE MESURE DU 2026-09-11.** Premiere ecriture : le bloc etait balaye en
       TEXTE BRUT. Resultat : ce fichier-ci se declarait juge de HTML et de
       YAML **a cause de sa propre documentation**, la population de (c3c)
       etait artificiellement gonflee, et le mutant 13 — qui vide cette
       population — sortait **VERT**. ⛔ Un mutant vert n'est pas une bonne
       nouvelle : celui-la disait que le controle ⛔ ne gardait pas ce qu'il
       annoncait.
    ⇒ DEUX LECTURES, parce que les deux objets ne sont pas de meme nature :
      · un FICHIER ENTIER s'analyse a l'AST — seules ses chaines LITTERALES
        HORS DOCSTRING comptent ;
      · une REGION est un fragment de texte qu'aucun parseur ne peut prendre
        seul : ses lignes de COMMENTAIRE sont retirees, et le reste (du code)
        est lu tel quel, plus les constantes de module qu'il nomme.
    ⚠️ LA RESOLUTION DE CONSTANTE EST **A UN NIVEAU**, et c'est ecrit : une
       constante qui en cite une autre ⛔ n'est pas suivie. Le jour ou ce
       depot en aura besoin, ce controle le dira en MANQUANT le sujet — ⛔ il
       ne le devinera pas.
    """
    if "ctrl(" not in bloc:
        return set()
    consts = {}
    try:
        for n in ast.walk(ast.parse(source_entier)):
            if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) \
                    and isinstance(n.value.value, str):
                for c in n.targets:
                    if isinstance(c, ast.Name):
                        consts[c.id] = n.value.value
    except SyntaxError:
        pass
    if fichier_entier:
        matiere = _constantes_hors_docstring(bloc)
        if matiere is None:
            matiere = []
    else:
        matiere = [re.sub(r"(?m)^\s*#.*$", " ", bloc)]
    # 🔴 ⛔ UNE TABLE DE DETECTION N'EST PAS SON PROPRE SUJET — MESURE DU
    #    2026-09-11, ET C'EST LA **DEUXIEME** FOIS DANS CE FICHIER. Les
    #    extensions de `STRUCTURES` avaient deja ete ecrites sans tige pour
    #    cette raison ; le nom de parseur `etree.HTML` porte une tige et un
    #    point, et se declarait donc lui-meme sujet HTML. Ce fichier se voyait
    #    « juge de HTML » a cause de la table qui sert a juger. ⇒ tout
    #    litteral EGAL a un jeton de parseur declare sort de la matiere.
    #    ⚠️ EGAL, ⛔ pas « contenant » : un chemin reel qui contiendrait le nom
    #       d'un parseur resterait un sujet.
    _jetons = {j for _, ps in STRUCTURES.values() for j in ps}
    matiere = [t for t in matiere if t not in _jetons]
    nu = " ".join(matiere)
    for nom, val in consts.items():
        if re.search(r"\b%s\b" % re.escape(nom), bloc):
            matiere = list(matiere) + [val]
    trouve = set()
    for t in list(matiere) + [nu]:
        for m in RE_SUJET.finditer(t):
            ext = "." + m.group(1).lower()
            for langue, (exts, _) in STRUCTURES.items():
                if ext in exts:
                    trouve.add(langue)
    return trouve


def _sans_jetons(texte, fichier_entier=False):
    """La matiere ou l'on cherche un parseur — ⛔ pas le texte brut.

    🔴 CORRECTIF DE REVUE (2026-09-11) — **LA PRECAUTION ETAIT PRISE D'UN SEUL
       COTE.** `sujets_de` ecartait deja les litteraux EGAUX a un jeton declare
       (« une table de detection n'est pas son propre sujet ») ; la recherche
       de PARSEUR, elle, lisait le texte brut. Deux trous mesures :
       · `"yaml.safe_load"`, ecrit dans la table `STRUCTURES` de CE fichier,
         lui accordait l'exemption YAML **sur sa propre table** ;
       · une region en `grep` pur greffee dans `verif_ledger_dn416.py` sortait
         `(True, True)` **parce qu'une AUTRE region du meme fichier** porte
         `yaml.safe_load` — (c3b) restait vert sur un controle aveugle.
    ⇒ les litteraux EGAUX a un jeton declare sortent de la matiere, et les
      lignes de COMMENTAIRE d'une region aussi (elles ⛔ ne s'executent pas).
    """
    t = texte if fichier_entier else re.sub(r"(?m)^\s*#.*$", " ", texte)
    for j in {j for _, ps in STRUCTURES.values() for j in ps}:
        t = t.replace('"%s"' % j, " ").replace("'%s'" % j, " ")
    return t


def parse_ou_declare(langue, bloc, source_entier, fichier_entier=False):
    """(a un parseur, declare son aveuglement) pour cette langue.

    ⚠️ **LES DEUX SE JUGENT DANS LE BLOC**, ⛔ pas dans le module : un controle
       ⛔ n'herite ni du parseur ni de l'aveuglement de son voisin. Le module ne
       sert qu'a une chose — constater que la constante d'aveuglement est bien
       POSEE quelque part (une affectation de module ⛔ ne peut pas vivre dans
       une region), sa **CHARGE** devant, elle, etre DANS le bloc.
    """
    _, parseurs = STRUCTURES[langue]
    matiere = _sans_jetons(bloc, fichier_entier)
    a_parseur = any(p in matiere for p in parseurs)
    # ⛔ LA DECLARATION EST UNE **DONNEE LUE PAR LE CODE**, ⛔ pas un
    #    commentaire ni une prose de docstring : elle doit etre AFFECTEE au
    #    niveau module ET **CHARGEE** quelque part. Sans la charge, une
    #    constante morte suffirait a acheter l'exemption — c'est le motif que
    #    ce depot a deja paye (« le jeton d'exemption n'a aucun echappement :
    #    le citer dans un commentaire l'ACCORDE »).
    attendu = "AVEUGLEMENT_%s" % langue.upper()
    posee = False
    try:
        arbre = ast.parse(source_entier)
    except SyntaxError:
        return a_parseur, False
    for n in ast.walk(arbre):
        if isinstance(n, ast.Assign):
            for c in n.targets:
                if isinstance(c, ast.Name) and c.id == attendu:
                    posee = True
    chargee = re.search(r"\b%s\b" % re.escape(attendu), matiere) is not None
    return a_parseur, (posee and chargee)


# ══ LE MUTANT — IL **REPLANTE**, ⛔ IL NE DEBRANCHE PAS ═════════════════════

def muter(etat):
    """REPLANTE une faute DANS L'ETAT — ⛔ jamais dans un fichier du depot.

    🔴 TOUTE mutation passe par cet unique etat, et le corps principal compare
       l'etat AVANT/APRES : la garde du no-op est donc UNIVERSELLE, et un
       mutant sans effet rend **`rc=3`**, ⛔ jamais un vert.
    ⛔ ET CHAQUE MUTANT **REPLANTE LA FAUTE**, ⛔ il ne debranche aucune garde :
       un mutant qui coupe le controle ne prouve que l'existence du controle.
    ⚠️ TOUT CORPS VERIFIE SON ANCRE D'ABORD et rend `e` INCHANGE si elle a
       disparu — un corps qui `split` ou indexe sur une ancre absente LEVE, et
       une levee rendrait `rc=1` + `BILAN`, mot pour mot le contrat d'une gate
       SAINE : un mutant perime passerait pour un gardien vivant.
    """
    e = copy.deepcopy(etat)
    s, moi = e["sources"], "tools/verif_harnais_dn81.py"

    if _MUTANT == 1:
        if moi not in s:
            return e
        s[moi] = s[moi] + (
            "\n\ndef ctrl(ok, libelle, detail=\"\"):\n"
            "    print(libelle)\n    return ok\n")
    elif _MUTANT == 2:
        if moi not in s:
            return e
        s[moi] = s[moi] + (
            "\n\ndef plat(txt):\n"
            "    return re.sub(r\"\\s+\", \" \", txt or \"\")\n")
    elif _MUTANT == 3:
        a = "    return re.sub(r\"\\s+\", \" \", txt or \"\")"
        if a not in s.get("tools/dn_gates.py", ""):
            return e
        s["tools/dn_gates.py"] = s["tools/dn_gates.py"].replace(
            a, "    return re.sub(r\"[ \\t]+\", \" \", txt or \"\").strip()", 1)
    elif _MUTANT == 4:
        e["noms"] = tuple(n for n in e["noms"] if n != "plat")
    elif _MUTANT == 5:
        # La declaration `bilan est TRANSFORME` devient FAUSSE : on rend a
        # `bilan` le corps modal exact des 6 gates qui le portent.
        src = s.get("tools/dn_gates.py", "")
        a = "def bilan(rc, anticipee=\"\", prevus=None):"
        if a not in src:
            return e
        i = src.index(a)
        j = src.index("\ndef plat(", i)
        s["tools/dn_gates.py"] = src[:i] + e["modal_bilan"] + src[j:]
    elif _MUTANT == 6:
        e["ledger"] = _plante_ancre(
            e["ledger"], "  📍 desknode:tools/il-n-existe-pas-dn81.py")
    elif _MUTANT == 7:
        e["ledger"] = _plante_ancre(
            e["ledger"],
            "  📍 desknode:tools/dn_gates.py (motif `CE MOTIF N EXISTE PAS`)")
    elif _MUTANT == 8:
        # ⚠️ `NOMS_PARTAGEZ` ⛔ n'est PAS `NOMS_PARTAGES` : une lettre. Une
        #    normalisation devenue tamis l'accepterait.
        e["ledger"] = _plante_ancre(
            e["ledger"],
            "  📍 desknode:tools/dn_gates.py (motif `NOMS_PARTAGEZ`)")
    elif _MUTANT == 9:
        # 🔴 CORRECTIF DE REVUE (2026-09-11) — CE MUTANT **DEBRANCHAIT** LA
        #    GARDE AU LIEU DE REPLANTER LA FAUTE, ce que l'en-tete de ce
        #    fichier interdit en toutes lettres. Son corps entier etait
        #    `e["normalisation_forcee_vide"] = True`, un drapeau lu au SEUL
        #    endroit qui remplit la population de (c2c) : ⛔ aucune ancre
        #    n'etait touchee, et son libelle pretendait le contraire.
        #    ⚠️ DEMONTRE : en deplacant l'`append` AU-DESSUS du test de
        #       normalisation, (c2c) comptait **94** ancres en restant vert
        #       alors qu'il ne prouvait plus rien — et le mutant sortait rouge
        #       **quand meme**. Un mutant qui rougit sur une garde debranchee
        #       ne prouve que l'existence du drapeau.
        # ⇒ IL REECRIT MAINTENANT LE LEDGER : tout motif qui ⛔ ne se trouve
        #   QU'APRES normalisation est remplace par un motif **LITTERAL de sa
        #   propre cible**. Les ancres restent donc toutes VIVANTES — (c2b)
        #   reste vert — et c'est la POPULATION de (c2c) qui se vide, pour de
        #   vrai. C'est la faute REELLE : un ledger ou plus rien n'exige la
        #   normalisation rend le controle (c2b) vert PAR CONSTRUCTION.
        e["ledger"] = _delitteralise(e["ledger"], e["cockpit"])
    elif _MUTANT == 10:
        # Un temoin `REFUSE` dont le motif est REELLEMENT present : le temoin
        # ne refute plus rien, et (c2d) doit le dire.
        e["norm_refuse"] = e["norm_refuse"] + (
            ("temoin creux", "aucun tag", "il n'y a aucun tag ici"),)
    elif _MUTANT == 11:
        cible = "tools/verif_ledger_dn416.py"
        src = s.get(cible, "")
        if "yaml.safe_load" not in src or "AVEUGLEMENT_YAML" not in src:
            return e
        s[cible] = (src.replace("yaml.safe_load", "re.findall")
                       .replace("AVEUGLEMENT_YAML", "_MOTIF_MORT"))
    elif _MUTANT == 12:
        cible = "tools/verif_ledger_dn416.py"
        src = s.get(cible, "")
        m = RE_REGION_FIN.search(src)
        if not m:
            return e
        deb = src.rfind("\n", 0, m.start()) + 1
        fin = src.find("\n", m.end())
        s[cible] = src[:deb] + src[fin + 1:]
    elif _MUTANT == 14:
        # 🔴 CORRECTIF DE REVUE — `(z)` AVAIT UN CONSOMMATEUR VIVANT ET ⛔ AUCUN
        #    TIR NE LE FAISAIT TOMBER : les 13 mutants basculaient un controle
        #    SANS changer le compte, et les sorties anticipees passent
        #    `anticipee`, qui desarme `(z)` par construction. Retirer le
        #    `rc = 1` de `dn_gates.bilan` laissait la gate VERTE en emettant
        #    moins de controles qu'annonce — c'est-a-dire exactement ce que
        #    `(z)` est cense empecher.
        # ⇒ CE MUTANT REPLANTE LA FAUTE, ⛔ il ne debranche pas `(z)` : il fait
        #   SAUTER un controle de fond. Le compte emis tombe a %d-1, `bilan`
        #   le voit, et `(z)` rougit.
        e["controles_sautes"] = ("c2d",)
    elif _MUTANT == 15:
        # 🔴 LE CAS QUE LE MUTANT 11 ⛔ NE PEUT PAS ATTEINDRE : il remplace
        #    `yaml.safe_load` sur TOUT le fichier, donc il enleve le parseur a
        #    la seule region qui en a un. Le vrai trou est ailleurs — une
        #    NOUVELLE region, en `grep` pur, **a cote** d'une region qui parse.
        #    Avant le correctif, elle heritait du parseur de sa voisine et
        #    (c3b) restait VERT sur un controle aveugle.
        # ⛔ Le code injecte ⛔ ne s'execute JAMAIS : il vit dans l'etat.
        cible = "tools/verif_ledger_dn416.py"
        src = s.get(cible, "")
        m = RE_REGION_DEB.search(src, src.find("le tracker se LIT"))
        if not m:
            return e
        greffe = (
            "    # >>> DN8-REGION — mutant 15 : un controle de `dn8` qui juge\n"
            "    #     le tracker AU MOTIF, sans parseur et sans aveuglement.\n"
            "    ctrl(\"dn8-1:\" in txt_trk, \"(m15) le tracker cite dn8-1\",\n"
            "         \"lu au motif dans %s\" % REL_TRACKER)\n"
            "    # <<< DN8-REGION\n")
        s[cible] = src[:m.start()] + greffe + src[m.start():]
    elif _MUTANT == 13:
        # ⚠️ LA MUTATION NE PORTE QUE **DANS LA REGION** : renommer la
        #    constante PARTOUT renommait aussi sa DEFINITION, la valeur
        #    `…-desknode.yaml` restait resoluble, et le sujet survivait. Le
        #    mutant sortait alors VERT — mesure du 2026-09-11.
        cible = "tools/verif_ledger_dn416.py"
        src = s.get(cible, "")
        m1 = RE_REGION_DEB.search(src, src.find("ctrl(True, \"le tracker se LIT"))
        if not m1:
            return e
        m2 = RE_REGION_FIN.search(src, m1.end())
        if not m2 or "REL_TRACKER" not in src[m1.start():m2.end()]:
            return e
        s[cible] = (src[:m1.start()]
                    + src[m1.start():m2.end()].replace(
                        "REL_TRACKER", "\"(le tracker)\"")
                    + src[m2.end():])
    return e


def _delitteralise(ledger, cockpit):
    """Reecrit, DANS LE LEDGER, tout motif d'ancre qui ⛔ ne se trouve QU'APRES
    normalisation, en un motif **LITTERAL de sa propre cible**.

    ⛔ CE N'EST PAS UN DEBRANCHEMENT : les ancres restent toutes ATTEIGNABLES
    et tous leurs motifs restent TROUVABLES — (c2a) et (c2b) restent verts.
    C'est la POPULATION de (c2c) qui se vide, et c'est la faute reelle : un
    ledger dont plus aucun motif n'exige la normalisation rend (c2b) vert par
    construction, et ⛔ personne ne le dirait.
    ⚠️ SI RIEN N'EST REECRIT, le texte ressort INCHANGE ⇒ no-op ⇒ `rc=3`.
    """
    for lig, _txt, dep, chem, motifs in ancres_du(ledger):
        if dep is None or not motifs:
            continue
        reel = resout(dep, chem, cockpit)
        if reel is None or not os.path.isfile(reel):
            continue
        try:
            cont = io.open(reel, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        ncont = norm(cont)
        for mo in motifs:
            if mo in cont or norm(mo) not in ncont:
                continue
            lit = _litteral_de(cont)
            if lit is None:
                continue
            lignes = ledger.split("\n")
            lignes[lig - 1] = lignes[lig - 1].replace("`%s`" % mo,
                                                      "`%s`" % lit, 1)
            ledger = "\n".join(lignes)
    return ledger


def _litteral_de(contenu):
    """Un fragment de la cible qui s'y trouve **LITTERALEMENT**, et qui ⛔ ne
    perturbe pas la grammaire d'une ancre (⛔ ni accent grave, ⛔ ni `·`, ⛔ ni
    parenthese, ⛔ ni marqueur que la normalisation retire)."""
    for l in contenu.split("\n"):
        t = l.strip()
        if len(t) >= 20 and not re.search(r"[`·()]", t) and norm(t) != "":
            frag = t[:30].strip()
            if frag and frag in contenu and frag != norm(frag):
                return frag
            if frag and frag in contenu:
                return frag
    return None


def _plante_ancre(ledger, ligne):
    """Insere une ancre JUSTE APRES la premiere ancre reelle du ledger.

    ⛔ La mutation VERIFIE son ancre : sans `📍` dans le ledger, elle rend le
    texte INCHANGE ⇒ no-op ⇒ `rc=3`.
    """
    lignes = ledger.split("\n")
    for i, l in enumerate(lignes):
        if l.strip().startswith("\U0001F4CD"):
            return "\n".join(lignes[:i + 1] + [ligne] + lignes[i + 1:])
    return ledger


# ══ LE CORPS ════════════════════════════════════════════════════════════════

def main():
    global _MUTANT
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--cockpit", default=COCKPIT_DEFAUT,
                    help="le depot de planification (PRIVE, jamais clone a "
                         "cote du code)")
    ap.add_argument("--mutant", type=int, default=None,
                    help="REPLANTE une faute EN MEMOIRE pour prouver que le "
                         "controle correspondant sait ROUGIR")
    ap.add_argument("--liste-mutants", action="store_true",
                    help="dit ce que chaque mutant replante, et sort")
    a = ap.parse_args()

    if a.mutant is not None and a.mutant not in MUTANTS:
        # ⛔ PAS une sortie par exception, qui rendrait 1 et se confondrait
        #    avec un vrai defaut : un mutant inconnu est une ERREUR D'APPEL.
        print("MUTANT %d INCONNU : il n'est pas declare. ⛔ Un mutant qui "
              "n'existe pas ne prouve RIEN — ⛔ ne pas conclure que le "
              "controle est vert." % a.mutant, file=sys.stderr)
        return 2
    _MUTANT = a.mutant or 0

    if a.liste_mutants:
        for n in sorted(MUTANTS):
            print("  %2d  [%s]  %s"
                  % (n, ",".join(CIBLES.get(n, ())) or "—", MUTANTS[n]))
        return 0

    print("=" * 78)
    print("dn8-1 — LES GATES PARSENT CE QU'ELLES JUGENT, ET LEURS HELPERS"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("        VIVENT EN UN SEUL ENDROIT")
    print("=" * 78)

    # ── LE PREREQUIS : LE COCKPIT, ⛔ PAS UN CONTROLE ────────────────────
    # 🔴 Le ledger vit dans un depot PRIVE qui n'est JAMAIS clone a cote du
    #    code. Son absence ne dit RIEN du code : elle dit que la gate n'a pas
    #    son terrain. ⇒ rc=4, et la table NON_JOUABLES de `run_gates.sh` le
    #    declare — sinon la CI casse au premier tir.
    p_led = os.path.join(a.cockpit, REL_LEDGER)
    manquants = []
    if not os.path.isdir(a.cockpit):
        manquants.append("le depot cockpit : %s" % a.cockpit)
    elif not os.path.isfile(p_led):
        manquants.append("le ledger : %s" % REL_LEDGER)
    if manquants:
        print("  [PREREQUIS ABSENT] le cockpit de planification n'est pas la")
        for m in manquants:
            print("      manque : %s" % m)
        print("      MOTIF : le cockpit est un depot PRIVE de planification,")
        print("              ⛔ jamais clone a cote du code. Sans lui il n'y")
        print("              a AUCUNE ancre `📍` a rejouer.")
        print("      REMEDE : `--cockpit <chemin>` si le depot est ailleurs.")
        # 🔴 dn8-1 / CORRECTIF DE REVUE — **EN MODE MUTANT, UN PREREQUIS ABSENT
        #    EST UN ROUGE, ⛔ PAS UN 4.** Mesure du 2026-09-11 :
        #    `verif_campagne_dn56.py` ⛔ n'est PAS dans `NON_JOUABLES`, elle
        #    TOURNE EN CI ; elle decouvre a l'AST toute gate qui declare
        #    `--liste-mutants`, joue chacun de ses mutants, et classe tout
        #    `rc != 1` en « NE ROUGISSENT PLUS ». Sur un runner (cockpit
        #    absent) les 13 mutants rendaient 4 ⇒ `BILAN : 7 OK, 1 KO` la ou le
        #    parent rendait `8 OK, 0 KO`. **La suite etait ROUGE EN CI.**
        # ⇒ C'est la convention que `verif_temoin_filtre_dn447.py` publie deja :
        #   « 1 si un controle rougit OU si un prerequis manque ». Elle ne vaut
        #   QUE pour le mode mutant : demander a une gate de prouver qu'un
        #   mutant rougit alors qu'elle n'a pas de terrain, c'est une demande
        #   IMPOSSIBLE — et une demande impossible se refuse en ROUGE NOMME,
        #   ⛔ jamais par un code qui veut dire « pas un rouge ».
        # ⛔ ET LE CHEMIN SANS `--mutant` GARDE SON 4 : c'est LUI que la table
        #   `NON_JOUABLES` de `run_gates.sh` declare, et le declarer autrement
        #   ferait rougir la passe entiere en « DECLARATION DEMENTIE ».
        # ⛔ ⛔ PAS PAR LES `EXCEPTIONS` DE dn56 : elles sont a DOUBLE SENS et
        #   ressortiraient `PERIMEE` partout ou le cockpit EST present.
        if _MUTANT:
            ctrl(False, "(c0) le cockpit est la — REQUIS en mode mutant",
                 "⛔ mutant %d demande SANS terrain : la gate ⛔ ne peut pas "
                 "prouver qu'il rougit. ⛔ rc=1, ⛔ pas 4." % _MUTANT)
            return bilan(1, "mutant %d demande sans cockpit" % _MUTANT,
                         prevus=CONTROLES_PREVUS)
        print("      ⛔ CE N'EST PAS UN VERDICT SUR LE CODE, et ⛔ pas un skip :")
        print("         rc=%d, declare dans la table NON_JOUABLES de"
              " tools/run_gates.sh." % RC_PREREQUIS)
        return RC_PREREQUIS

    # ── (c0) LE PRE-VOL — ⛔ AUCUN CONTROLE SUR DU VIDE ──────────────────
    print("\n── (c0) LE PRE-VOL ───────────────────────────────────────────────")
    perim = perimetre_dn8()
    sources, illisibles = {}, []
    for rel in sorted(set(perim) | set(fichiers_a_regions())):
        try:
            sources[rel] = io.open(os.path.join(DESKNODE, rel),
                                   encoding="utf-8").read()
        except (OSError, UnicodeDecodeError) as x:
            illisibles.append("%s (%s)" % (rel, x))
    try:
        ledger = io.open(p_led, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as x:
        illisibles.append("%s (%s)" % (REL_LEDGER, x))
        ledger = ""
    if not ctrl(bool(perim) and not illisibles and bool(ledger),
                "(c0) le perimetre dn8 est NON VIDE et tout se LIT",
                "%d fichier(s) du perimetre, %d a regions, ledger %d car."
                % (len(perim), len(fichiers_a_regions()), len(ledger))
                if not illisibles and perim and ledger
                else "⛔ perimetre=%d illisible(s)=%s"
                     % (len(perim), " ".join(illisibles) or "(ledger vide)")):
        return bilan(1, "le pre-vol n'a pas de terrain",
                     prevus=CONTROLES_PREVUS)

    for n in sorted(MUTANTS):
        if not ctrl(bool(CIBLES.get(n)) and bool(MUTANTS.get(n)),
                    "(c0) le mutant %d a une CIBLE et un LIBELLE" % n,
                    "→ %s" % ",".join(CIBLES.get(n, ()))
                    if CIBLES.get(n) else "⛔ cible ou libelle manquant"):
            return bilan(1, "un mutant est declare a moitie",
                         prevus=CONTROLES_PREVUS)

    # 🔴 CORRECTIF DE REVUE — **LA TABLE `CIBLES` N'ETAIT REJOUEE PAR
    #    PERSONNE.** `(c0)` n'assertait que `bool(CIBLES.get(n))` : une cible
    #    pouvait nommer `c9z`, un identifiant qui n'existe nulle part, et la
    #    colonne « cible » du releve n'etait qu'une CAPTURE que rien ne
    #    rejouait. ⚠️ `verif_campagne_dn440.py` applique deja exactement cette
    #    propriete (`attendus` / `touche` / `surplus`) : elle est reprise ici.
    # ⇒ LES DEUX SENS, et c'est le point : « tout id vise EXISTE » ⛔ ne dit
    #   RIEN de « tout controle EST vise ». Le second est celui qui manque
    #   toujours — « N mutants, N vus rougir » prouve `mutant ⇒ rouge`, ⛔ pas
    #   `controle ⇒ couvert ».
    # ⚠️ ET C'EST `dn_gates.ids_par_ast` QUI LES LIT, ⛔ pas un `grep` : le
    #    helper existait pour ca et n'avait **ZERO appelant**. `(z)` vit dans
    #    `dn_gates.bilan`, ⛔ pas ici — les deux fichiers sont donc lus.
    ids_moi = dn_gates.ids_par_ast(os.path.abspath(__file__)) or set()
    ids_mod = dn_gates.ids_par_ast(dn_gates.__file__) or set()
    vises = {c for cs in CIBLES.values() for c in cs}
    fantomes = sorted(vises - (ids_moi | ids_mod))
    nus = sorted(ids_moi - vises - set(IDS_SANS_MUTANT))
    ctrl(bool(ids_moi) and not fantomes and not nus,
         "(c0) les cibles de mutants et les ID se recouvrent",
         "%d id(s) lus a l'AST, %d vise(s), %d exempte(s) declaree(s)"
         % (len(ids_moi), len(vises), len(IDS_SANS_MUTANT))
         if not fantomes and not nus and ids_moi
         else "⛔ cible(s) FANTOME(S) : %s · controle(s) vise(s) par AUCUN "
              "mutant : %s" % (fantomes or "∅", nus or "∅"))

    par = inventaire_legacy(set(perim))
    emp_bilan_modal = None
    cible_bilan = modal(par, "bilan").prose
    for p in sorted(glob.glob(os.path.join(DESKNODE, "tools", "verif_*.py"))):
        rel = os.path.relpath(p, DESKNODE).replace(os.sep, "/")
        if rel in set(perim) or emp_bilan_modal is not None:
            continue
        src = io.open(p, encoding="utf-8").read()
        try:
            arbre = ast.parse(src)
        except SyntaxError:
            continue
        for n in ast.walk(arbre):
            if isinstance(n, ast.FunctionDef) and n.name == "bilan" \
                    and empreinte(n, True) == cible_bilan:
                emp_bilan_modal = ast.get_source_segment(src, n) + "\n\n"
                break

    etat = {
        "sources": sources,
        "ledger": ledger,
        "noms": tuple(dn_gates.NOMS_PARTAGES),
        "norm_doit": NORM_DOIT,
        "norm_refuse": NORM_REFUSE,
        "modal_bilan": emp_bilan_modal or "def bilan(rc, a=\"\"):\n    pass\n",
        "cockpit": a.cockpit,
        "controles_sautes": (),
    }

    # 🔴 UN MUTANT QUI MEURT SORTIRAIT EN TRACEBACK, SANS `BILAN` — or « pas
    #    de BILAN » est le discriminant d'une gate MORTE. ⇒ il se rend en KO.
    try:
        neuf = muter(etat) if _MUTANT else etat
    except Exception as exc:                              # noqa: BLE001
        ctrl(False, "(c0) le mutant %d a une CIBLE et un CORPS" % _MUTANT,
             "⛔ %s: %s — la faute est dans le MUTANT, ⛔ pas dans la gate"
             % (type(exc).__name__, str(exc)[:80]))
        return bilan(1, "le mutant %d n'a pas pu s'appliquer" % _MUTANT,
                     prevus=CONTROLES_PREVUS)
    if _MUTANT and neuf == etat:
        ctrl(False, "(c0) le mutant %d a bien un EFFET" % _MUTANT,
             "⛔ SANS EFFET — son ancre litterale a disparu de la cible. "
             "⛔ Ce n'est PAS un controle vert : rc=3, mutant PERIME.")
        return bilan(RC_MUTANT_PERIME,
                     "le mutant %d n'a eu aucun effet" % _MUTANT,
                     prevus=CONTROLES_PREVUS)

    src_gates = neuf["sources"].get("tools/dn_gates.py", "")
    noms = neuf["noms"]

    # ══ (c1) LES HELPERS VIVENT EN UN SEUL ENDROIT ══════════════════════
    print("\n── (c1) LES HELPERS PARTAGES — UN SEUL ENDROIT ───────────────────")
    print("     ⚠️ INVENTAIRE DES GATES HORS PERIMETRE `dn8` — ⛔ PUBLIE, ⛔ PAS")
    print("        JUGE. L'hygiene des 44 gates est le territoire `dn4` ; ce")
    print("        qui suit est un ECART DECLARE, porteur `epic-dn4`.")
    print("        %-20s %7s %7s %7s  %s"
          % ("helper", "copies", "impl/⊕", "impl/⊖", "corps modal ⊖ ×N"))
    tot_c = tot_p = tot_i = 0
    for nom in sorted(noms):
        md = modal(par, nom)
        c = len(par.get(nom, []))
        tot_c += c
        tot_p += md.impl_prose
        tot_i += md.impl_code
        print("        %-20s %7d %7d %7d  %s ×%d%s"
              % (nom, c, md.impl_prose, md.impl_code, md.code or "—",
                 md.copies,
                 "   ⚠️ EGALITE a %d, departagee par %s"
                 % (len(md.ex_aequo), DEPARTAGE.get(nom, "⛔ PERSONNE"))
                 if md.ex_aequo else ""))
    print("        %-20s %7d %7d %7d" % ("TOTAL", tot_c, tot_p, tot_i))
    print("        ⊕ = corps AVEC la prose — LA MESURE DU DOSSIER (%d/%d),"
          % (tot_c, tot_p))
    print("            reproduite ici a l'identique. C'est elle qui a DESIGNE")
    print("            les corps retenus dans `dn_gates.py`.")
    print("        ⊖ = corps SANS la prose — la seule qui puisse dire « meme")
    print("            implementation » une fois la section PROVENANCE")
    print("            ajoutee. C'est elle que (c1b)…(c1d) COMPARENT.")
    print("        ⚠️ LES DEUX ⛔ NE DESIGNENT PAS LE MEME CORPS : pour `ctrl`,")
    print("           ⊕ en designe un a 5 porteuses et ⊖ un autre a 7. ⛔ « la")
    print("           plus jouee » est une propriete de la METRIQUE, ⛔ pas du")
    print("           corpus — les deux sont ecrites, ⛔ aucune n'est tranchee")
    print("           en silence.")

    # (c1a) — la liste que le module publie et celle qu'il exporte coincident
    par_ast = defs_de(src_gates, set(noms) | set(dn_gates.NOMS_PARTAGES),
                      avec_prose=False)
    exportes = set()
    try:
        for n in ast.walk(ast.parse(src_gates)):
            if isinstance(n, ast.Assign) and isinstance(n.value, ast.List):
                for c in n.targets:
                    if isinstance(c, ast.Name) and c.id == "__all__":
                        exportes = {x.value for x in n.value.elts
                                    if isinstance(x, ast.Constant)}
    except SyntaxError:
        exportes = set()
    definis = set(par_ast or {})
    ctrl(bool(exportes) and set(noms) == exportes == definis,
         "(c1a) `NOMS_PARTAGES` == `__all__` == les defs du module",
         "%d nom(s) : %s" % (len(exportes), ", ".join(sorted(exportes)))
         if set(noms) == exportes == definis
         else "⛔ NOMS_PARTAGES-__all__=%s · __all__-defs=%s · defs-__all__=%s"
              % (sorted(set(noms) ^ exportes) or "∅",
                 sorted(exportes - definis) or "∅",
                 sorted(definis - exportes) or "∅"))

    # (c1b) — les corps repris VERBATIM portent bien l'empreinte MODALE
    verbatim = [n for n in sorted(noms) if n not in TRANSFORMES]
    derives = []
    for nom in verbatim:
        md = modal(par, nom)
        emp_mine = (par_ast or {}).get(nom, [None])[0]
        if md.ex_aequo and nom not in DEPARTAGE:
            derives.append("%s (⛔ EGALITE a %d corps, ⛔ DEPARTAGEE PAR "
                           "PERSONNE : %s)"
                           % (nom, len(md.ex_aequo), ", ".join(md.ex_aequo)))
        elif md.code is None or emp_mine != md.code:
            derives.append("%s (module %s ≠ modal %s)"
                           % (nom, emp_mine or "—", md.code or "—"))
    ctrl(bool(verbatim) and not derives,
         "(c1b) les corps VERBATIM sont bien les corps MODAUX",
         "%d/%d nom(s) verbatim, empreinte identique au corps le plus joue "
         "des gates" % (len(verbatim), len(noms)) if not derives
         else "⛔ %d DERIVE(S) : %s" % (len(derives), " · ".join(derives)))

    # (c1c) — les corps TRANSFORMES le sont VRAIMENT, et la lecture est nommee
    creuses = []
    for nom, lecture in sorted(TRANSFORMES.items()):
        md = modal(par, nom)
        emp_mod = md.code
        emp_mine = (par_ast or {}).get(nom, [None])[0]
        if nom not in noms:
            creuses.append("%s (⛔ pas dans NOMS_PARTAGES)" % nom)
        elif md.ex_aequo and nom not in DEPARTAGE:
            # ⛔ UNE TRANSFORMATION N'EXEMPTE PAS DU DEPARTAGE : si le corps
            #    de depart est une EGALITE non tranchee, « transforme depuis
            #    le plus joue » ⛔ ne designe rien.
            creuses.append("%s (⛔ EGALITE a %d corps de depart, ⛔ DEPARTAGEE "
                           "PAR PERSONNE : %s)"
                           % (nom, len(md.ex_aequo), ", ".join(md.ex_aequo)))
        elif emp_mine is not None and emp_mine == emp_mod:
            creuses.append("%s (declare TRANSFORME, corps IDENTIQUE au modal "
                           "%s)" % (nom, emp_mod))
        elif emp_mod is None:
            creuses.append("%s (⛔ aucun corps modal a comparer)" % nom)
    ctrl(bool(TRANSFORMES) and not creuses,
         "(c1c) toute TRANSFORMATION declaree en est VRAIMENT une",
         "%d transformation(s), lectures de contexte : %s"
         % (len(TRANSFORMES), ", ".join("%s→%s" % (k, v)
                                        for k, v in sorted(TRANSFORMES.items())))
         if not creuses
         else "⛔ %d DECLARATION(S) CREUSE(S) : %s"
              % (len(creuses), " · ".join(creuses)))

    # (c1d) — aucun fichier du perimetre `dn8` ne re-definit un des 8 noms
    copies = []
    for rel in perim:
        if rel == "tools/dn_gates.py":
            continue
        d = defs_de(neuf["sources"].get(rel, ""), set(noms), avec_prose=False)
        if d is None:
            copies.append("%s (⛔ ne s'analyse pas)" % rel)
            continue
        for nom, emps in sorted(d.items()):
            emp_mod = (par_ast or {}).get(nom, [None])[0]
            for e in emps:
                copies.append("%s::%s [%s vs module %s — %s]"
                              % (rel, nom, e, emp_mod or "—",
                                 "IDENTIQUE, donc une COPIE" if e == emp_mod
                                 else "DIVERGENT"))
    ctrl(not copies,
         "(c1d) aucun fichier de dn8 ne RE-DEFINIT un helper",
         "%d fichier(s) balaye(s) : %s" % (len(perim), ", ".join(perim))
         if not copies
         else "⛔ %d COPIE(S) — elle(s) doivent IMPORTER `dn_gates` : %s"
              % (len(copies), " · ".join(copies)))

    # ══ (c2) LES ANCRES `📍` DU LEDGER ══════════════════════════════════
    print("\n── (c2) LES ANCRES `📍` DU LEDGER ────────────────────────────────")
    print("     %s" % AVEUGLEMENT_HTML)
    print("     %s" % AVEUGLEMENT_POWERSHELL)
    cibles = ancres_du(neuf["ledger"])
    lignes_ancres = len({c[0] for c in cibles})
    inatteignables, motifs_absents, apres_norm = [], [], []
    for lig, txt, dep, chem, motifs in cibles:
        if dep is None:
            inatteignables.append("l.%d ⛔ FORME non reconnue : %s"
                                  % (lig, txt[:60]))
            continue
        reel = resout(dep, chem, a.cockpit)
        if reel is None:
            inatteignables.append("l.%d %s" % (lig, txt[:70]))
            continue
        if not motifs or not os.path.isfile(reel):
            continue
        try:
            cont = io.open(reel, encoding="utf-8", errors="replace").read()
        except OSError as x:
            inatteignables.append("l.%d ⛔ %s" % (lig, x))
            continue
        ncont = norm(cont)
        for mo in motifs:
            if mo in cont:
                continue
            if norm(mo) in ncont:
                apres_norm.append("l.%d `%s` → %s" % (lig, mo[:40], chem))
                continue
            motifs_absents.append("l.%d `%s` → %s" % (lig, mo[:40], chem))

    ctrl(bool(cibles) and not inatteignables,
         "(c2a) chaque cible d'ancre `📍` est ATTEIGNABLE",
         "%d cible(s) sur %d ligne(s) d'ancre" % (len(cibles), lignes_ancres)
         if not inatteignables
         else "⛔ %d ANCRE(S) MORTE(S) : %s"
              % (len(inatteignables), " · ".join(inatteignables[:5])))

    ctrl(not motifs_absents,
         "(c2b) chaque MOTIF d'ancre se retrouve dans sa cible",
         "0 motif perdu (apres normalisation accents/casse/tirets)"
         if not motifs_absents
         else "⛔ %d MOTIF(S) ABSENT(S) : %s"
              % (len(motifs_absents), " · ".join(motifs_absents[:5])))

    ctrl(bool(apres_norm),
         "(c2c) la normalisation SERT — population NON VIDE",
         "%d ancre(s) ne se trouvent QU'APRES normalisation : %s"
         % (len(apres_norm), " · ".join(a2.split(" → ")[0]
                                        for a2 in apres_norm[:4]))
         if apres_norm
         else "⛔ AUCUNE ancre n'exige la normalisation — le controle (c2b) "
              "tournerait a VIDE sur ce volet, et son verdict ne prouverait "
              "plus rien. ⛔ Un contrôle sur une population vide est vert par "
              "construction.")

    faux_temoins = []
    for etiq, motif, cible in neuf["norm_doit"]:
        if norm(motif) not in norm(cible):
            faux_temoins.append("DOIT/%s : `%s` ⛔ pas rapproche de `%s`"
                                % (etiq, motif[:30], cible[:30]))
    for etiq, motif, cible in neuf["norm_refuse"]:
        if norm(motif) in norm(cible):
            faux_temoins.append("REFUSE/%s : `%s` RAPPROCHE de `%s` — la "
                                "normalisation est un TAMIS"
                                % (etiq, motif[:30], cible[:30]))
    # ⚠️ LE SEUL SITE `sautable` DE LA GATE, et il est ECRIT : c'est la faute
    #    que le mutant 14 REPLANTE — une gate qui joue moins de controles
    #    qu'elle n'annonce. ⛔ Il ⛔ ne debranche PAS `(z)`, qui vit dans
    #    `dn_gates.bilan` et reste entier : il rend la POPULATION fautive.
    if "c2d" not in neuf["controles_sautes"]:
        ctrl(bool(neuf["norm_doit"]) and bool(neuf["norm_refuse"])
             and not faux_temoins,
             "(c2d) la normalisation rapproche, et ⛔ elle ne TAMISE pas",
             "%d temoin(s) DOIT + %d temoin(s) REFUSE, tous tenus"
             % (len(neuf["norm_doit"]), len(neuf["norm_refuse"]))
             if not faux_temoins
             else "⛔ %d TEMOIN(S) EN ECHEC : %s"
                  % (len(faux_temoins), " · ".join(faux_temoins[:4])))

    # ══ (c3) UN CONTROLE DE `dn8` QUI JUGE UNE STRUCTURE LA FAIT PARSER ══
    print("\n── (c3) CE QUE `dn8` JUGE, `dn8` LE PARSE ────────────────────────")
    blocs = []          # (origine, texte du bloc, source entier)
    deb_tot = 0
    depareilles = []
    for rel in sorted(neuf["sources"]):
        src = neuf["sources"][rel]
        if rel in perim:
            blocs.append((rel, src, src))
        regs, d, f = regions_dn8(src)
        deb_tot += d
        if d != f:
            depareilles.append("%s (%d ouverture(s) / %d fermeture(s))"
                               % (rel, d, f))
        for i, r in enumerate(regs, 1):
            blocs.append(("%s#region%d" % (rel, i), r, src))

    ctrl(deb_tot > 0 and not depareilles,
         "(c3a) les marqueurs de region `DN8-REGION` sont APPARIES",
         "%d region(s) delimitee(s) dans %d fichier(s)"
         % (deb_tot, len(fichiers_a_regions()))
         if deb_tot and not depareilles
         else "⛔ %s" % (" · ".join(depareilles) if depareilles
                        else "AUCUNE region — l'exception nommee a disparu"))

    aveugles, population = [], []
    for origine, bloc, entier in blocs:
        for langue in sorted(sujets_de(bloc, entier,
                                       fichier_entier=origine in perim)):
            population.append("%s→%s" % (origine, langue))
            a_p, a_d = parse_ou_declare(langue, bloc, entier,
                                        fichier_entier=origine in perim)
            if not a_p and not a_d:
                aveugles.append("%s juge du %s SANS parseur et SANS "
                                "`AVEUGLEMENT_%s`"
                                % (origine, langue.upper(), langue.upper()))
    ctrl(not aveugles,
         "(c3b) tout controle de dn8 PARSE, ou DECLARE son trou",
         "%d couple(s) (bloc, structure) : %s"
         % (len(population), ", ".join(population[:6]))
         if not aveugles
         else "⛔ %d AVEUGLE(S) MUET(S) : %s"
              % (len(aveugles), " · ".join(aveugles[:4])))

    ctrl(bool(population),
         "(c3c) (c3b) a une POPULATION — ⛔ pas un vert sur du vide",
         "%d couple(s) juges" % len(population) if population
         else "⛔ AUCUN bloc de `dn8` ne nomme une structure YAML/HTML/CSS/"
              "PowerShell ⇒ (c3b) est vert PAR CONSTRUCTION, et ne garde RIEN.")

    return bilan(1 if dn_gates.ko_total[0] else 0,
                 prevus=CONTROLES_PREVUS)


if __name__ == "__main__":
    sys.exit(main())

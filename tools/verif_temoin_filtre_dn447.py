#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-47 — LE TEMOIN DE `filtre_constats_dn56.py` ENTRE DANS LE HARNAIS.

======================= CE QUE CETTE GATE FAIT, ET POURQUOI =================

`tools/filtre_constats_dn56.py` est un INSTRUMENT DE MESURE, ⛔ pas une gate :
il classe des constats en VRAI / DEJA FAUX / NON REPRODUCTIBLE, et un verdict
`VRAI` n'est ⛔ PAS un defaut du harnais. C'est la decision `D1` de `dn5-3`, et
elle tient : **l'instrument RESTE hors du glob `tools/verif_*.py`.**

🔴 MAIS IL PORTE SON PROPRE TEMOIN, ET **RIEN NE LE JOUAIT**.
   Mesure du cadrage, 2026-09-06 (`mesures/dn4-47/T1-instrument-hors-harnais.txt`)
   `git grep -l -F -- filtre_constats_dn56 HEAD --`, hors `mesures/`, rendait
   **0 fichier** : ni `tools/run_gates.sh`, ni `.github/workflows/gates.yml`, ni
   un hook ne l'invoquaient ; `--temoin-seul` n'etait cite que par sa propre
   declaration argparse.
   ⇒ LE COUT EST **PAYE**, ⛔ pas hypothetique : du commit `360a5c2` a `dn5-8`
     l'instrument etait **MORT** — `main()` sortait avant de publier — et le
     harnais est reste **VERT** a chaque tir. Le garde-fou « 0 KO de plus, gate
     par gate » lui est **aveugle par construction**, puisqu'il n'est pas une
     gate.

⇒ CETTE GATE EST **MINCE** : elle ne re-mesure rien, elle **JOUE** l'instrument
  par `subprocess` et lit ce qu'il publie. L'instrument reste dehors (`D1`), le
  harnais l'invoque (`D22`). Decision owner `D23` du 2026-09-05.

── LES DEUX DISCRIMINANTS SONT **IMPOSES** PAR `D23` ────────────────────────

  (c2) la ligne `⇒ TEMOIN :` a ete PUBLIEE — son **ABSENCE** signale un
       instrument **MORT** ;
  (c3) le compte publie annonce **`0`** temoin tombe.

⛔ LE `rc` DE L'INSTRUMENT N'ENTRE DANS **AUCUN** VERDICT. Il est imprime comme
   OBSERVATION, et c'est tout. Motif MESURE : un banc qui juge sur le `rc`
   global reste vert des qu'un AUTRE echec rend la meme valeur — et ici
   l'instrument mort rend precisement `1`, la valeur d'un vrai rouge. Le
   discriminant d'un outil mort est **l'absence de son bilan**, ⛔ pas son code
   de retour. L'instrument l'ecrit lui-meme en tete de son fichier.

── TROIS CONTROLES DE PLUS, ET POURQUOI CHACUN EXISTE ──────────────────────

  (c1) la cible EXISTE au chemin NOMME. Une cible disparue ⛔ ne sort pas
       verte : la gate echoue FERME. ⚠️ La cible est **NOMMEE**, ⛔ pas globee —
       `D23` ne tranche que pour UN instrument, et un glob elargirait en
       silence une portee declaree.
  (c4) le temoin a AFFIRME quelque chose (`n OK` avec `n > 0`). Motif `dn4-40` :
       « les gates cessent de passer a vide » — un temoin qui n'affirme rien ne
       garde rien.
  (c5) le compte PUBLIE s'accorde avec les lignes `[KO ]` COMPTEES, dans les
       DEUX SENS. Motif `dn5-6` constat (2) : un `N OK / 0 KO` calcule sur une
       population fondue.

⛔ AUCUN COMPTE N'EST FIGE ICI — ni le nombre de temoins de l'instrument, ni une
   duree. Un nombre ecrit se perime le jour ou il compte. Seule la ligne que
   l'instrument PUBLIE fait foi, et cette gate la RECOPIE.

── CE QUE CETTE GATE NE FAIT PAS ───────────────────────────────────────────

⛔ Elle ne verse PAS l'instrument sous le glob — ce serait `D1` violee.
⛔ Elle ne traite QU'UN SEUL instrument. `inventaire_motif_dn53.py` et
   `campagne_ctrl_dn440.py` restent hors du harnais, et la question generale —
   « quel instrument hors glob merite un temoin joue ? » — n'est ⛔ pas tranchee
   ici. Porteur : `epic-dn4`.
⛔ Elle ne declare PAS `--cockpit` : elle n'en a pas besoin, et le declarer
   ajouterait une occurrence au motif litteral que le constat (4) de `dn5-6`
   compte.

Sortie : `0` si tout passe · `1` si un controle rougit ou si un prerequis
manque · `2` sur un `--mutant` inconnu (message d'usage).

⚠️ LA LIGNE `BILAN` EST IMPRIMEE SUR **TOUS LES CHEMINS QUI RENDENT UN
   VERDICT** — ⛔ pas sur ceux qui n'en rendent aucun. MESURE le 2026-09-06 :
   `--liste-mutants` (rc=0) et `--mutant <inconnu>` (rc=2) n'impriment ⛔ AUCUN
   `BILAN`, et c'est **voulu** : `verif_campagne_dn56.py` se comporte a
   l'identique, et son parseur de `--liste-mutants` attend la liste **NUE**. La
   1re redaction affirmait « TOUS les chemins de sortie » — c'etait FAUX, et
   affirme deux fois. ⇒ la PHRASE est corrigee, ⛔ pas le comportement.
"""

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

# ⛔ AUCUN CHEMIN ABSOLU : la racine derive de `__file__`
# (`inventaire_motif_dn53.py` compte les chemins personnels du depot).
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── LA CIBLE EST **NOMMEE**, ⛔ PAS GLOBEE ──────────────────────────────────
CIBLE_REL = os.path.join("tools", "filtre_constats_dn56.py")
ARG_CIBLE = "--temoin-seul"
DELAI = 300
# ⚠️ LE DELAI FAIT PARTIE DE CE QUE LE MUTANT 7 **SUBSTITUE**, au meme titre
#    que le chemin : « une cible qui n'en finit pas » est une SITUATION, et on
#    la monte avec une cible qui dort ET l'echeance qu'elle depasse. ⛔ Ce n'est
#    pas debrancher la garde — la garde doit toujours NOMMER le depassement
#    plutot que de le laisser sortir en exception.
DELAI_MUTANT_7 = 2

# La ligne que l'instrument publie sur TOUS les chemins de `temoins()`.
# ⚠️ `⇒ TEMOIN :` et ⛔ PAS `⇒ TEMOIN DE L'INSTRUMENT :` — la seconde n'est
#    imprimee que par le tir COMPLET, que cette gate ne demande pas.
RE_TEMOIN = re.compile(r"^\s*⇒ TEMOIN\s*:\s*(\d+)\s+OK,\s*(\d+)\s+KO\s*$", re.M)
RE_KO = re.compile(r"^\s*\[KO \].*$", re.M)

ok_total = [0]
ko_total = [0]

# 🔴 dn4-40 / AC40.7.c — instrument de campagne, import DEFENSIF : une gate ne
#    meurt pas parce qu'un module de trace manque.
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


def git_injouable():
    """LE DEPOT PEUT-IL SEULEMENT REPONDRE A UNE QUESTION `git` ?

    🔴 UN PREREQUIS ABSENT PORTAIT LE MASQUE D'UN VRAI DEFAUT (revue du
    2026-09-06). Les temoins (a1)..(a4) de l'instrument interrogent
    `git grep <motif> HEAD` : dans un arbre SANS `.git` — un `git archive`
    deplie, par exemple — ils tombent, et cette gate rougissait en disant « un
    temoin est tombe ». C'est vrai, et ca ne dit ⛔ PAS la verite : le depot
    n'avait pas pu REPONDRE. C'est la meme classe d'absence non nommee que
    `run()` vient d'etre durci contre, un etage plus bas.

    ⇒ ON LE NOMME, ET C'EST TOUT. ⛔ Aucune declaration `NON_JOUABLE`, ⛔ aucun
      passage au vert : la gate rougit toujours, mais son motif dit ce qui est
      vrai. Rend `None` quand `git` repond, sinon LA PHRASE A IMPRIMER."""
    try:
        r = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=RACINE,
                           timeout=60, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    except (OSError, subprocess.SubprocessError) as e:
        return "⛔ `git` EST INJOUABLE ICI : %s" % e
    if r.returncode != 0:
        return ("⛔ CET ARBRE N'EST PAS UN DEPOT `git` "
                "(`git rev-parse --git-dir` rend %d)" % r.returncode)
    return None


def bilan(rc):
    """⛔ ELLE EST IMPRIMEE SUR **TOUS LES CHEMINS QUI RENDENT UN VERDICT**.
    C'est le contrat de `run_gates.sh`, et c'est le discriminant d'une gate
    morte. ⚠️ `--liste-mutants` et l'usage `rc=2` ne rendent AUCUN verdict et
    n'impriment donc AUCUN `BILAN` — voir l'en-tete du fichier.

    ⇒ ET SI LA GATE ROUGIT, ELLE DIT D'ABORD SI LE DEPOT POUVAIT REPONDRE."""
    if ko_total[0]:
        motif = git_injouable()
        if motif:
            print("\n⚠️ AVANT DE LIRE CE ROUGE — UN PREREQUIS MANQUE :")
            print("   %s" % motif)
            print("   ⇒ les temoins de l'instrument interrogent `git grep "
                  "<motif> HEAD` ; ils NE PEUVENT PAS repondre ici. Ce rouge "
                  "peut donc etre")
            print("     un PREREQUIS ABSENT, ⛔ pas un defaut du depot. "
                  "⛔ Il n'est ni tu, ni declare NON_JOUABLE, ni verdi.")
    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return rc


# ═══ NFR7 / regle `dn4-44` — LES MUTANTS **REPLANTENT**, ⛔ ILS NE ═══════════
#     DEBRANCHENT RIEN.
#
# ⛔ UN MUTANT QUI DEBRANCHE LA GARDE NE PROUVE QUE SON EXISTENCE. Chacun de
#    ceux-ci **SUBSTITUE** a la cible un instrument BIDON ecrit dans un
#    temporaire (patron `BIDON`/`CORPS_BIDON` de `verif_campagne_dn56.py`) :
#    ⛔ aucun ne falsifie une variable interne de cette gate.
#
# ⚠️ LE MUTANT 7 SUBSTITUE **DEUX** CHOSES, ET C'EST DIT : la cible (un bidon
#    qui dort) **ET** l'echeance (`DELAI_MUTANT_7`). « Une cible qui n'en finit
#    pas » est une SITUATION — la monter demande les deux moities. ⛔ Ce n'est
#    pas debrancher la garde : la garde doit toujours NOMMER le depassement.
#
# ⚠️ CE QUE LA CAMPAGNE NE PROUVE PAS, ET QUI S'ECRIT : « N mutants, N vus
#    rougir » prouve `mutant ⇒ rouge`, ⛔ **PAS** `controle ⇒ couvert`.
MUTANTS = {
    1: ("substitue a la cible un instrument BIDON qui MEURT avant de publier "
        "(trace nue, rc=1) — REPLANTE la panne `360a5c2` → `dn5-8`"),
    2: ("substitue a la cible un instrument BIDON qui meurt avant de publier "
        "MAIS sort en rc=0 — prouve que le `rc` ne sauve pas"),
    3: ("substitue a la cible un instrument BIDON qui publie `1 OK, 2 KO` "
        "avec ses 2 lignes [KO ] (un temoin de l'instrument est TOMBE)"),
    4: ("substitue a la cible un instrument BIDON qui publie `0 OK, 0 KO` "
        "(un temoin qui n'affirme rien ne garde rien)"),
    5: ("substitue a la cible un instrument BIDON qui publie `1 OK, 0 KO` "
        "ET imprime quand meme 1 ligne [KO ] (le compte MENT)"),
    6: ("fait pointer la cible sur un chemin ABSENT "
        "(une cible introuvable ⛔ ne sort pas verte)"),
    7: ("substitue a la cible un instrument BIDON qui DORT au-dela de son "
        "echeance — le depassement doit etre NOMME, ⛔ pas leve en exception"),
}
_MUTANT = 0

# ── L'INSTRUMENT BIDON DES MUTANTS 1-5 ET 7 ────────────────────────────────
# ⛔ Il n'ecrit ⛔ NI la sentinelle ⛔ NI la banniere de l'instrument reel : un
#    second porteur ferait tomber ses temoins (a3)/(a4), c'est-a-dire
#    recreerait d'un cran la panne que `dn5-8` vient de reparer.
BIDON = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, sys
ap = argparse.ArgumentParser()
ap.add_argument("--temoin-seul", action="store_true")
ap.parse_args()
print("=" * 78)
print("INSTRUMENT BIDON — substitue par un mutant de verif_temoin_filtre_dn447")
print("=" * 78)
%s
'''
_L_TEMOIN = 'print("\\n  \\u21d2 TEMOIN : %d OK, %d KO")'
_L_TRACE = ('print("Traceback (most recent call last):")\n'
            'print("  File \\"bidon\\", line 1, in <module>")\n'
            'print("FileNotFoundError: [Errno 2] No such file or directory")')
_L_OK = 'print("  [OK ] un temoin qui passe%s")'
_L_KO = 'print("  [KO ] un temoin qui tombe%s")'

CORPS_BIDON = {
    1: _L_TRACE + "\nsys.exit(1)",
    2: _L_TRACE + "\nsys.exit(0)",
    3: "\n".join([_L_OK % " a", _L_KO % " b", _L_KO % " c",
                  _L_TEMOIN % (1, 2), "sys.exit(1)"]),
    4: "\n".join([_L_TEMOIN % (0, 0), "sys.exit(0)"]),
    5: "\n".join([_L_OK % " a", _L_KO % " b",
                  _L_TEMOIN % (1, 0), "sys.exit(0)"]),
    # ⚠️ IL DORT **LONGTEMPS** DEVANT UNE ECHEANCE COURTE, et ⛔ pas l'inverse :
    #    un bidon qui dort « juste un peu plus » rendrait le mutant sensible a
    #    la charge de la machine. Le tir coute `DELAI_MUTANT_7` secondes.
    7: "import time\ntime.sleep(300)",
}

# ── LES MUTANTS QUI NE PASSENT **PAS** PAR UN INSTRUMENT BIDON ──────────────
# Ils substituent autre chose que le CORPS de la cible ; ils sont DECLARES ici,
# ⛔ pas devines dans une branche de `cible()`.
MUTANTS_SANS_BIDON = {
    6: "substitue au CHEMIN de la cible un chemin ABSENT",
}

# 🔴 UN MUTANT DECLARE SANS CORPS NI BRANCHE JOUERAIT LE **VRAI** INSTRUMENT ET
#    SORTIRAIT **VERT** — un mutant silencieusement inoffensif, c'est-a-dire une
#    campagne qui compte une preuve qu'elle n'a pas. Le mutant 7 en etait a UNE
#    FRAPPE (revue du 2026-09-06). ⇒ l'incoherence est un **ROUGE**, ⛔ pas un
#    silence, et elle se voit AU PREMIER TIR, meme sans `--mutant`.
MUTANTS_ORPHELINS = sorted(set(MUTANTS) - set(CORPS_BIDON)
                           - set(MUTANTS_SANS_BIDON))
MUTANTS_FANTOMES = sorted((set(CORPS_BIDON) | set(MUTANTS_SANS_BIDON))
                          - set(MUTANTS))


def cible():
    """Le chemin joue. Sous mutant, c'est une SUBSTITUTION — ⛔ jamais une
    variable interne falsifiee. Rend (chemin, etiquette, jetable, echeance)."""
    reel = os.path.join(RACINE, CIBLE_REL)
    if _MUTANT in CORPS_BIDON:
        d = tempfile.mkdtemp(prefix="dn447-bidon-")
        try:
            faux = os.path.join(d, "instrument_bidon.py")
            # ⚠️ `with` : ⛔ ne pas confier la fermeture au compte de references.
            with io.open(faux, "w", encoding="utf-8") as f:
                f.write(BIDON % CORPS_BIDON[_MUTANT])
        except OSError:
            shutil.rmtree(d, ignore_errors=True)   # ⛔ aucun temporaire fuite
            raise
        return (faux, ("<instrument BIDON du mutant %d, substitue a %s>"
                       % (_MUTANT, CIBLE_REL)), d,
                DELAI_MUTANT_7 if _MUTANT == 7 else DELAI)
    if _MUTANT in MUTANTS_SANS_BIDON:
        d = tempfile.mkdtemp(prefix="dn447-absent-")
        faux = os.path.join(d, "n-existe-pas", CIBLE_REL)
        return (faux, ("<chemin ABSENT du mutant %d, substitue a %s>"
                       % (_MUTANT, CIBLE_REL)), d, DELAI)
    return reel, CIBLE_REL, None, DELAI


def lance(chemin, delai):
    """⛔ RIEN NE SORT D'ICI EN EXCEPTION. Une gate qui meurt sur un timeout ou
    une trace nue est exactement ce que cette gate existe pour NOMMER — elle
    ⛔ ne doit pas mourir de la meme facon.

    ⚠️ LE DEPASSEMENT EST EXERCE par le mutant 7, qui le REPLANTE. La branche
    `OSError`, elle, est DEFENSIVE et ⛔ n'est exercee par aucun mutant : la
    monter demanderait de casser l'interpreteur ou le `cwd`, c'est-a-dire de
    debrancher autre chose que ce que ce controle garde. C'est ECRIT plutot
    que tu — elle rend la MEME forme que la branche du timeout, qui, elle,
    est vue rougir."""
    try:
        r = subprocess.run([sys.executable, chemin, ARG_CIBLE], cwd=RACINE,
                           timeout=delai, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        return r.returncode, r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired as e:
        # 🔴 LA SORTIE PARTIELLE EST **RENDUE**, ⛔ pas jetee (revue du
        #    2026-09-06). Un instrument qui PUBLIE son `⇒ TEMOIN :` puis se fige
        #    etait sinon rapporte par (c2) comme « MORT en amont » — le mauvais
        #    motif sur un fait vrai.
        vu = e.output.decode("utf-8", "replace") if e.output else ""
        return None, ("⛔ TIMEOUT apres %d s — l'instrument n'en finit pas.\n%s"
                      % (delai, vu))
    except OSError as e:
        return None, "⛔ IMPOSSIBLE A LANCER : %s" % e


def recopie(txt, n=12):
    """Les dernieres lignes de l'instrument, RECOPIEES sous un filet.

    ⚠️ Le filet `│ ` n'est pas decoratif : sans lui, une ligne `[KO ]` de
    l'instrument se lirait comme un verdict DE CETTE GATE — et
    `verif_campagne_dn56.py` compte les `^\\s*\\[KO \\]` pour decider qu'un
    mutant a vraiment trouve la faute replantee."""
    # ⚠️ ON TESTE LE **VIDE DU TEXTE**, ⛔ pas la verite du join : mesure du
    #    2026-09-06 — `"".rstrip("\n").split("\n")` vaut `[""]`, donc le join
    #    vaut `"        │ "`, qui est VRAI. Le repli etait donc MORT.
    txt = txt.rstrip("\n")
    if not txt.strip():
        return "        │ (rien)"
    return "\n".join("        │ %s" % l for l in txt.split("\n")[-n:])


def main():
    global _MUTANT
    ap = argparse.ArgumentParser(add_help=True)
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
    print("dn4-47 — LE TEMOIN DE L'INSTRUMENT DE FILTRAGE EST JOUE PAR LE HARNAIS"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)
    print("  mutants declares : %d · corps BIDON : %d · sans bidon : %d"
          % (len(MUTANTS), len(CORPS_BIDON), len(MUTANTS_SANS_BIDON)))

    # 🔴 UN MUTANT DECLARE SANS MONTAGE JOUERAIT LE **VRAI** INSTRUMENT ET
    #    SORTIRAIT VERT. ⇒ le desaccord rougit, AU PREMIER TIR, meme sans
    #    `--mutant`. ⛔ Il ne se decouvre pas le jour ou quelqu'un joue le
    #    mutant orphelin.
    if MUTANTS_ORPHELINS or MUTANTS_FANTOMES:
        ctrl(False, "tout mutant declare a un montage, et reciproquement",
             "⛔ ORPHELIN(S) (declare(s) sans montage ⇒ joueraient la VRAIE "
             "cible et sortiraient VERTS) : %s · ⛔ FANTOME(S) (montage sans "
             "declaration ⇒ invisibles a `--liste-mutants`) : %s"
             % (MUTANTS_ORPHELINS or "aucun", MUTANTS_FANTOMES or "aucun"))
        return bilan(1)

    # ⚠️ `cible()` ETAIT APPELEE HORS DU `try` : un `OSError` de `mkdtemp` ou de
    #    l'ecriture rendait une TRACE NUE, ⛔ sans `BILAN`, et laissait fuir le
    #    temporaire — exactement ce que cette gate existe pour interdire.
    try:
        chemin, etiq, jetable, delai = cible()
    except OSError as e:
        ctrl(False, "la substitution du mutant a pu etre montee",
             "⛔ %s — ⛔ une gate ne meurt pas en trace nue, pas meme en "
             "montant son propre mutant" % e)
        return bilan(1)

    try:
        print("\n── (c1) LA CIBLE EST **NOMMEE**, ET ELLE EXISTE ──────────────────")
        print("  cible      : %s" % etiq)
        existe = os.path.isfile(chemin)
        if not ctrl(existe, "la cible nommee existe au depot",
                    "un fichier lisible" if existe
                    else "⛔ INTROUVABLE — ⛔ une cible disparue ne sort PAS verte"):
            # ⇒ SORTIE **FERMEE**, ⛔ jamais verte. Et la ligne BILAN est
            #   imprimee quand meme : c'est le contrat.
            return bilan(1)

        print("\n── L'INSTRUMENT EST JOUE — ⛔ RIEN N'EST RE-MESURE ICI ───────────")
        print("  commande   : python3 %s %s   (echeance %d s)"
              % (etiq, ARG_CIBLE, delai))
        rc, sortie = lance(chemin, delai)
        # 🔴 LE `rc` EST UNE **OBSERVATION**, ⛔ JAMAIS UN VERDICT. Un banc qui
        #    juge sur le `rc` global reste vert des qu'un AUTRE echec rend la
        #    meme valeur — et l'instrument MORT rend precisement `1`.
        print("  rc observe : %s   ⛔ OBSERVATION — il n'entre dans AUCUN verdict"
              % ("mort ou timeout" if rc is None else rc))

        print("\n── (c2) L'INSTRUMENT A **PUBLIE** SON TEMOIN ─────────────────────")
        m = RE_TEMOIN.search(sortie)
        if not ctrl(m is not None, "l'instrument a publie sa ligne `⇒ TEMOIN :`",
                    "ligne trouvee : %s" % m.group(0).strip() if m
                    else "⛔ L'INSTRUMENT N'A PAS JUGE — aucune ligne publiee, "
                         "il est MORT en amont ; dernieres lignes ci-dessous"):
            if m is None:
                print(recopie(sortie))
            return bilan(1)

        publies_ok, publies_ko = int(m.group(1)), int(m.group(2))
        comptees = RE_KO.findall(sortie)

        print("\n── (c3) LE COMPTE PUBLIE ANNONCE **0** TEMOIN TOMBE ──────────────")
        if not ctrl(publies_ko == 0, "aucun temoin de l'instrument n'est tombe",
                    "%d OK, %d KO — ⛔ le compte n'est PAS fige ici, il est RECOPIE"
                    % (publies_ok, publies_ko) if publies_ko == 0
                    else "⛔ %d TEMOIN(S) TOMBE(S) sur %d — ⛔ ON NE CONCLUT RIEN "
                         "du depot ; les [KO ] de l'instrument :"
                         % (publies_ko, publies_ok + publies_ko)):
            print(recopie("\n".join(comptees) or "(aucune ligne [KO ] imprimee)",
                          n=20))

        print("\n── (c4) LE TEMOIN A **AFFIRME** QUELQUE CHOSE ────────────────────")
        ctrl(publies_ok > 0, "le temoin de l'instrument n'est pas VIDE",
             "%d controle(s) affirme(s)" % publies_ok if publies_ok > 0
             else "⛔ `0 OK` — un temoin qui n'affirme rien ne garde rien "
                  "(motif `dn4-40`)")

        print("\n── (c5) LE COMPTE PUBLIE S'ACCORDE AVEC LES LIGNES COMPTEES ──────")
        accord = (len(comptees) == publies_ko)
        ctrl(accord, "le compte publie s'accorde avec les [KO ] imprimes",
             "%d ligne(s) [KO ] comptee(s) pour %d annonce(s)"
             % (len(comptees), publies_ko) if accord
             else "⛔ DIVERGENCE — l'instrument ANNONCE %d KO et IMPRIME %d "
                  "ligne(s) [KO ] : %s" % (publies_ko, len(comptees),
                                           "il en cache" if len(comptees) > publies_ko
                                           else "il en annonce plus qu'il n'en montre"))
        if not accord:
            print(recopie("\n".join(comptees) or "(aucune ligne [KO ] imprimee)",
                          n=20))

        print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : elle garde que le temoin de")
        print("   l'instrument est JOUE et qu'il tient. ⛔ Elle ne dit RIEN des")
        print("   verdicts que l'instrument publie — un constat `VRAI` est son")
        print("   RESULTAT, ⛔ pas un defaut du harnais (`D1`).")
        return bilan(1 if ko_total[0] else 0)
    finally:
        if jetable:
            shutil.rmtree(jetable, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

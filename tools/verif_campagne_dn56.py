#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn5-6 / CONSTAT (10) — LES CAMPAGNES DE MUTANTS CESSENT D'ETRE DES CAPTURES
UNIQUES.

======================= CE QUE CETTE GATE FAIT, ET POURQUOI =================

Plusieurs gates de ce depot portent une campagne de mutants : chacun REPLANTE
une faute en memoire et doit faire ROUGIR le controle qui la garde. Ces
campagnes ont ete jouees UNE FOIS, a la main, et leur resultat vit dans une
capture sous `mesures/`.

🔴 ET RIEN NE LES REJOUAIT. MESURE DU 2026-09-05
   (`mesures/dn5-6/T1-filtre-10-constats.txt`, constat 10) :
     · `tools/run_gates.sh` ne cite ⛔ PAS `--mutant` ;
     · `.github/workflows/gates.yml` ne le cite ⛔ PAS non plus ;
       — les deux jouent chaque gate **une fois, sans argument** ;
     · `tools/verif_campagne_dn440.py` est scopee au **ledger et au tracker du
       cockpit**, ⛔ pas aux campagnes des gates.
   ⇒ la preuve `controle ⇒ couvert` reposait sur une **CAPTURE UNIQUE**.

── LES CIBLES SONT **DECOUVERTES**, ⛔ JAMAIS ENUMEREES ─────────────────────

🔴 REVUE DU 2026-09-05 — LA PREMIERE VERSION CODAIT SA CIBLE EN DUR
   (`verif_licences_dn52.py`). Elle reproduisait donc d'un cran le defaut
   qu'elle repare : les **8 mutants** que `dn5-6` ajoute ailleurs n'etaient
   rejoues par personne. ⇒ on decouvre par **ARBRE SYNTAXIQUE** toute gate du
   glob `tools/verif_*.py` qui DECLARE `--liste-mutants` a argparse.
   ⛔ Pas un `grep` : ce depot CITE ses propres drapeaux en prose, et un grep
   les compterait (defaut mesure sur `run_gates.sh`, constat 4).

── CE QU'ELLE VERIFIE, ET POURQUOI CHAQUE CONDITION EST NECESSAIRE ─────────

Pour CHAQUE mutant que chaque cible declare :

  (a) **`rc` == 1.** ⛔ Necessaire, ⛔ pas suffisant.
  (b) **Une ligne `BILAN` a ete imprimee.** 🔴 C'EST LE DISCRIMINANT D'UNE
      GATE MORTE. Un mutant INAPPLICABLE sort en `sys.exit("MUTANT n
      INAPPLICABLE …")` — donc `rc=1` AUSSI, sans avoir rien controle. Juger
      sur le `rc` global laisserait passer ce cas exact ; il est REEL et
      MESURE, voir la table des exceptions ci-dessous.
  (c) **Au moins une ligne `[KO ]`.** Seul signe que la gate a REELLEMENT
      trouve la faute replantee, et ⛔ pas echoue pour autre chose.

── LES EXCEPTIONS SONT **DECLAREES ET FALSIFIABLES** ───────────────────────

Un defaut PRE-EXISTANT, ⛔ non cause par `dn5-6`, ne doit ⛔ ni faire rougir
cette marche ⛔ ni disparaitre en silence. ⇒ il est INSCRIT ci-dessous avec sa
date, sa mesure et son porteur — et **l'exception elle-meme est un controle** :
le jour ou le mutant recommence a rougir correctement, l'exception devient
PERIMEE et **c'est elle qui fait rougir la gate**. Une exception ne peut donc
pas survivre au defaut qu'elle excuse.

── (c2) LA CLE DE CAMPAGNE RESTE VALIDE ────────────────────────────────────

`dn5-2` / AC2.6.d posait une hypothese : **aucun libelle de controle ne fait
58 caracteres ou plus**. Elle fonde la lecture A COLONNE FIXE des lignes
`[OK ] <libelle-58> <detail>`. Elle n'etait re-controlee NULLE PART : elle ne
vivait que dans une capture. Elle est desormais un controle.
⚠️ REVUE DU 2026-09-05 : la 1re version ne lisait que les libelles LITTERAUX
   et ratait ceux construits par formatage — dont **un dans ce fichier meme**.

Sortie : 0 si tout passe, 1 sinon.
"""

import argparse
import ast
import glob
import io
import os
import re
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOI = os.path.basename(os.path.abspath(__file__))
LARGEUR_LIBELLE = 58     # la colonne de `dire()` — AC2.6.d de `dn5-2`
DELAI_LISTE = 120
DELAI_MUTANT = 300

# ── LES EXCEPTIONS, DATEES, MESUREES, AVEC LEUR PORTEUR ────────────────────
# clef : (fichier de gate, numero de mutant) ⇒ (motif, porteur)
# ⚠️ CHACUNE EST UN CONTROLE A DOUBLE SENS : si le mutant redevient sain,
#    l'exception est PERIMEE et fait rougir. ⛔ Elle ne peut pas rot.
EXCEPTIONS = {
    ("tools/verif_langues_dn442.py", 17): (
        "MESURE le 2026-09-05 : `--mutant 17` sort en rc=1 SANS ligne BILAN et "
        "SANS aucun [KO ] — `MUTANT 17 INAPPLICABLE : le motif est "
        "introuvable`. Son ancre est une chaine source VERBATIM multi-lignes "
        "d'un ESP_LOGI de `dn_ui.c` qui a ete reformate. ⛔ PRE-EXISTANT, ⛔ non "
        "cause par `dn5-6` : c'est cette gate-ci qui le REVELE. Le corriger "
        "exige de choisir une ancre neuve dans `firmware/`, hors du perimetre "
        "de cette marche (NFR8).",
        "dn4-42-l-ecran-parle-deux-langues"),
}

ok_total = [0]
ko_total = [0]

# 🔴 dn4-40 / AC40.7.c — instrument de campagne, import DEFENSIF.
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


# ═══ NFR7 / regle `dn4-44` — LES MUTANTS QUI **REPLANTENT** ════════════════
#
# ⛔ UN MUTANT QUI DEBRANCHE LA GARDE NE PROUVE QUE SON EXISTENCE.
# ⚠️ REVUE DU 2026-09-05 : les trois premiers DEBRANCHAIENT (ils falsifiaient
#    `rc`/`bilan`/`kos` dans `joue()`, et ecrasaient `longs` apres coup). Ils
#    REPLANTENT desormais la faute **dans la matiere que le controle lit**.
MUTANTS = {
    1: ("substitue a une cible une gate BIDON dont le mutant sort en rc=0 "
        "(un mutant qui NE ROUGIT PLUS)"),
    2: ("substitue a une cible une gate BIDON dont le mutant sort en rc=1 "
        "SANS ligne BILAN (le cas `MUTANT INAPPLICABLE`, mort en amont)"),
    3: ("substitue a une cible une gate BIDON dont le mutant sort en rc=1 "
        "avec un BILAN mais SANS aucun [KO ] nomme"),
    4: ("plante un libelle de 58 caracteres, construit PAR FORMATAGE "
        "(la forme que le controle de cle ne voyait pas)"),
    5: ("declare une exception pour un mutant qui rougit correctement "
        "(une exception PERIMEE doit rougir, ⛔ pas se taire)"),
}
_MUTANT = 0

# ── LA GATE BIDON DES MUTANTS 1-3 — elle REPLANTE un comportement reel ─────
BIDON = '''#!/usr/bin/env python3
import argparse, sys
ap = argparse.ArgumentParser()
ap.add_argument("--mutant", type=int, default=0)
ap.add_argument("--liste-mutants", action="store_true")
a = ap.parse_args()
if a.liste_mutants:
    print("   1  mutant de synthese")
    sys.exit(0)
%s
'''
CORPS_BIDON = {
    1: 'print("BILAN : 1 OK, 0 KO")\nsys.exit(0)',
    2: 'sys.exit("MUTANT 1 INAPPLICABLE : le motif est introuvable.")',
    3: 'print("BILAN : 1 OK, 0 KO")\nsys.exit(1)',
}


def cibles():
    """Les gates qui DECLARENT `--liste-mutants` a argparse. ⛔ Pas au grep."""
    out = []
    for g in sorted(glob.glob(os.path.join(RACINE, "tools", "verif_*.py"))):
        if os.path.basename(g) == MOI:
            continue                      # ⛔ jamais soi-meme : recursion
        try:
            a = ast.parse(io.open(g, encoding="utf-8", errors="replace").read(),
                          filename=g)
        except (SyntaxError, OSError, UnicodeDecodeError):
            continue
        for n in ast.walk(a):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "add_argument"
                    and any(isinstance(x, ast.Constant)
                            and x.value == "--liste-mutants" for x in n.args)):
                out.append(g)
                break
    return out


def _lance(argv, delai):
    """⛔ RIEN NE SORT D'ICI EN EXCEPTION. Une gate qui meurt sur un timeout
    ou une trace nue est exactement ce que cette gate existe pour NOMMER —
    elle ⛔ ne doit pas mourir de la meme facon."""
    try:
        r = subprocess.run(argv, cwd=RACINE, timeout=delai,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return r.returncode, r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return None, "⛔ TIMEOUT apres %d s" % delai
    except OSError as e:
        return None, "⛔ IMPOSSIBLE A LANCER : %s" % e


def liste_mutants(gate):
    rc, out = _lance([sys.executable, gate, "--liste-mutants"], DELAI_LISTE)
    if rc != 0:
        return None, out
    return sorted(int(m.group(1))
                  for m in re.finditer(r"^\s*(\d+)\s+\S", out, re.M)), out


def joue(gate, n, bidon=None):
    if bidon is not None:
        rc, out = _lance([sys.executable, bidon, "--mutant", str(n)], DELAI_MUTANT)
    else:
        rc, out = _lance([sys.executable, gate, "--mutant", str(n)], DELAI_MUTANT)
    if rc is None:
        return None, False, 0, out
    return (rc,
            bool(re.search(r"^BILAN\s*:", out, re.M)),
            len(re.findall(r"^\s*\[KO \]", out, re.M)),
            out)


def libelles_de(chemin):
    """Les libelles passes a `dire(...)` / `ctrl(...)`, lus a l'AST.

    ⚠️ REVUE DU 2026-09-05 — LA 1re VERSION NE VOYAIT QUE LES LITTERAUX. Elle
       ratait les libelles construits par formatage — dont **celui du controle
       de cle, dans ce fichier meme** (`"cle valide (aucun libelle >= %d)" %
       LARGEUR_LIBELLE`). ⇒ on resout aussi les `%`, les `+` et les f-strings,
       en remplacant les parties non constantes par un jeton de LONGUEUR
       PLAUSIBLE, ⛔ pas par du vide : sous-estimer une longueur ferait passer
       vert un libelle qui deborde.
    """
    try:
        arbre = ast.parse(io.open(chemin, encoding="utf-8",
                                  errors="replace").read(), filename=chemin)
    except (SyntaxError, OSError, UnicodeDecodeError):
        return None

    def resout(n):
        if isinstance(n, ast.Constant):
            return str(n.value)
        if isinstance(n, ast.JoinedStr):
            return "".join(resout(v) or "??" for v in n.values)
        if isinstance(n, ast.FormattedValue):
            return "??"
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Mod, ast.Add)):
            g, d = resout(n.left), resout(n.right)
            if isinstance(n.op, ast.Add):
                return (g or "") + (d or "")
            # `%` : on substitue un jeton de longueur plausible aux marqueurs.
            return re.sub(r"%[-0-9.]*[sdrfx]", "9999", g) if g else None
        return None

    out = []
    for n in ast.walk(arbre):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id in ("dire", "ctrl")):
            continue
        if len(n.args) >= 2:
            v = resout(n.args[1])
            if v is not None:
                out.append(v)
    return out


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
    print("dn5-6 — LES CAMPAGNES DE MUTANTS SONT REJOUEES"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)

    # ── la gate BIDON des mutants 1-3, ecrite dans un temporaire ────────────
    bidon = None
    if _MUTANT in CORPS_BIDON:
        import tempfile
        d = tempfile.mkdtemp(prefix="dn56-bidon-")
        bidon = os.path.join(d, "verif_bidon.py")
        io.open(bidon, "w", encoding="utf-8").write(BIDON % CORPS_BIDON[_MUTANT])

    print("\n── (c1) LES CIBLES SONT DECOUVERTES, ⛔ JAMAIS ENUMEREES ─────────")
    cs = cibles()
    rel = [os.path.relpath(c, RACINE) for c in cs]
    if not ctrl(bool(cs), "des gates declarent une campagne de mutants",
                "%d cible(s) : %s" % (len(cs), ", ".join(rel)) if cs
                else "⛔ AUCUNE — le glob ou la detection AST sont casses"):
        print("\n" + "=" * 78)
        print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
        print("=" * 78)
        return 1

    print("\n── (c2) CHAQUE MUTANT ROUGIT, AVEC UN BILAN ET UN [KO ] NOMME ────")
    muets, sans_bilan, sans_ko, morts = [], [], [], []
    exc_utilisees, exc_perimees = [], []
    total = 0
    for c in cs:
        r = os.path.relpath(c, RACINE)
        nums, sortie = liste_mutants(c)
        if nums is None:
            morts.append("%s (⛔ `--liste-mutants` a echoue : %s)"
                         % (r, sortie.strip()[:60]))
            continue
        for n in nums:
            total += 1
            # les mutants 1-3 detournent LA PREMIERE cible vers la gate bidon
            b = bidon if (bidon and c == cs[0] and n == nums[0]) else None
            rc, bilan, kos, _ = joue(c, n, bidon=b)
            cle = (r, n)
            # ⚠️ NOMMER LA SUBSTITUTION, ⛔ PAS LA VRAIE CIBLE : sinon la sortie
            #    accuse une gate SAINE d'un defaut que la bidon a joue pour elle.
            etiq = ("<gate BIDON du mutant %d, substituee a %s#%d>"
                    % (_MUTANT, r, n)) if b else "%s#%d" % (r, n)
            sain = (rc == 1 and bilan and kos > 0)
            if cle in EXCEPTIONS or (_MUTANT == 5 and cle == (r, nums[0])):
                # ⇒ L'EXCEPTION EST UN CONTROLE A DOUBLE SENS.
                (exc_perimees if sain else exc_utilisees).append(
                    "%s#%d" % (r, n))
                continue
            if rc is None:
                morts.append("%s (%s)" % (etiq, "mort ou timeout"))
            elif rc != 1:
                muets.append("%s (rc=%s)" % (etiq, rc))
            elif not bilan:
                sans_bilan.append(etiq)
            elif kos == 0:
                sans_ko.append(etiq)
    if bidon:
        import shutil
        shutil.rmtree(os.path.dirname(bidon), ignore_errors=True)

    ctrl(not morts, "toute cible repond, et aucun mutant ne meurt",
         "%d mutant(s) confronte(s) sur %d cible(s)" % (total, len(cs))
         if not morts else "⛔ " + " · ".join(morts))
    ctrl(not muets, "tout mutant rend rc=1",
         "aucun mutant devenu MUET" if not muets
         else "⛔ NE ROUGISSENT PLUS : " + " · ".join(muets))
    ctrl(not sans_bilan, "tout mutant rouge a bien imprime un BILAN",
         "aucune sortie en amont" if not sans_bilan
         else "⛔ rc=1 SANS BILAN (mort en amont) : " + " · ".join(sans_bilan))
    ctrl(not sans_ko, "tout mutant rouge porte au moins un [KO ] nomme",
         "chaque mutant vise un controle" if not sans_ko
         else "⛔ rouge SANS [KO ] : " + " · ".join(sans_ko))

    print("\n── (c3) LES EXCEPTIONS SONT DECLAREES ET ⛔ NE PEUVENT PAS ROT ───")
    for (f, n), (motif, porteur) in sorted(EXCEPTIONS.items()):
        print("  · %s#%d ⇒ porteur **%s**" % (f, n, porteur))
        print("      %s" % motif[:150])
    ctrl(not exc_perimees,
         "aucune exception n'a survecu au defaut qu'elle excuse",
         "%d exception(s) declaree(s), %d encore justifiee(s)"
         % (len(EXCEPTIONS), len(exc_utilisees)) if not exc_perimees
         else "⛔ PERIMEE(S) — ce(s) mutant(s) rougi(ssen)t correctement, "
              "l'exception doit etre RETIREE : " + " · ".join(exc_perimees))

    print("\n── (c4) LA CLE DE CAMPAGNE RESTE LISIBLE A COLONNE FIXE ──────────")
    # 🔴 LA PORTEE DE L'HYPOTHESE EST CELLE QU'AC2.6.d LUI A DONNEE, ⛔ PAS
    #    « toutes les gates ». Elle fonde la CLE DE CAMPAGNE de
    #    `verif_licences_dn52.py`, lue A COLONNE FIXE. MESURE du 2026-09-05 :
    #    l'appliquer aux 4 cibles rend **44 libelles >= 58** dans
    #    `verif_demarrage_dn443.py` et `verif_langues_dn442.py` — un fait REEL,
    #    ⛔ mais qui ne dit rien de la cle qu'AC2.6.d protege : ces gates-la ne
    #    sont lues par aucune cle a colonne fixe. ⇒ elargir le CONTROLE aurait
    #    fabrique un rouge ; on elargit donc la MESURE, ⛔ pas le verdict.
    PORTEE_CLE = [os.path.join(RACINE, "tools", "verif_licences_dn52.py"),
                  os.path.abspath(__file__)]
    libs, illisibles = [], []
    for c in PORTEE_CLE:
        l = libelles_de(c)
        if l is None:
            illisibles.append(os.path.relpath(c, RACINE))
        else:
            libs += l
    if _MUTANT == 4:
        libs.append("cle : %s" % ("x" * (LARGEUR_LIBELLE - 6)))
    ctrl(not illisibles, "toute cible s'analyse a l'AST",
         "%d fichier(s) lu(s) dans la portee de la cle" % len(PORTEE_CLE)
         if not illisibles
         else "⛔ ILLISIBLE(S) : " + " · ".join(illisibles))
    # ⇒ LA MESURE HORS PORTEE EST **PUBLIEE**, ⛔ pas tue : un lecteur doit
    #   savoir que l'hypothese ne vaut PAS partout, et pourquoi elle n'a pas
    #   a valoir partout.
    for c in cs:
        if c in PORTEE_CLE:
            continue
        l = libelles_de(c) or []
        n = len([x for x in l if len(x) >= LARGEUR_LIBELLE])
        print("     [hors portee] %-38s %d libelle(s) >= %d sur %d"
              % (os.path.relpath(c, RACINE), n, LARGEUR_LIBELLE, len(l)))
    longs = [l for l in libs if len(l) >= LARGEUR_LIBELLE]
    ctrl(not longs, "cle valide (aucun libelle >= %d)" % LARGEUR_LIBELLE,
         "%d libelle(s) lu(s) a l'AST, le plus long fait %d"
         % (len(libs), max(len(l) for l in libs) if libs else 0)
         if not longs
         else "⛔ %d libelle(s) debordent la colonne : %s"
              % (len(longs), " · ".join(repr(l[:40]) for l in longs[:3])))

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : « N mutants, N vus rougir »")
    print("   prouve `mutant ⇒ rouge`, ⛔ PAS `controle ⇒ couvert`. Un controle")
    print("   qu'AUCUN mutant ne vise reste garde par rien, et ⛔ elle ne le")
    print("   verra pas. Elle garde que les campagnes DEJA ECRITES ne")
    print("   pourrissent pas.")

    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return 1 if ko_total[0] else 0


if __name__ == "__main__":
    sys.exit(main())

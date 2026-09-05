#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn5-6 / T0-T1 — LE FILTRE : LES CONSTATS REPORTES SONT REJOUES AVANT D'ETRE CRUS.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

Dix constats ont ete rendus par les revues de code de `dn5-2`, `dn5-3` et
`dn5-4`, chacun mesure **une seule fois**, entre le 2026-09-02 et le
2026-09-04 — et l'arbre a bouge depuis. Les corriger « au cas ou » depenserait
du travail sur des faits perimes ; les croire sans les rejouer publierait des
correctifs qui ne gardent rien.

⇒ Cet outil les REJOUE UN PAR UN et les classe :
     **VRAI**              — le mauvais comportement se produit ENCORE, ici,
                             et la sortie qui le montre est imprimee ;
     **DEJA FAUX**         — le mauvais comportement NE SE PRODUIT PLUS ;
     **NON REPRODUCTIBLE** — il ne peut pas etre exerce depuis ce poste, et
                             le MOTIF est ecrit (⛔ jamais « on suppose »).

⚠️ TOUTE MESURE PAR `subprocess`, ⛔ JAMAIS PAR LE SHELL DE SESSION.
   Motif : mesure `dn5-1` du 2026-09-02 — le proxy de session reecrit les
   sorties (il rendait 76/24 la ou `subprocess` rend 73/21).

⛔ CE FICHIER EST **HORS DU GLOB `tools/verif_*.py`**, ET C'EST DELIBERE.
   Une gate est jouee par `tools/run_gates.sh` et par la CI. Cet outil n'est
   pas une gate : c'est un INSTRUMENT DE MESURE. Le piege a deja ete paye par
   `dn5-3` (decision D1) : un instrument verse sous le glob devient une gate.

🔴 ET IL PORTE SON TEMOIN EN TETE, PARCE QUE `dn5-3` A PAYE CE PIEGE AUSSI.
   L'instrument de `dn5-3` a MENTI DEUX FOIS, dans le sens rassurant : un `\\`
   de trop faisait repondre « ✅ NON » sur une chaine qui portait le defaut.
   ⇒ ICI, CHAQUE PRIMITIVE DE MESURE EST EXERCEE SUR UN CAS OU LA FAUTE EST
     **REPLANTEE** — elle DOIT la voir — ET sur un cas ou elle est absente —
     elle NE DOIT PAS la voir. Si un seul temoin tombe, ⛔ ON NE CONCLUT RIEN.

Sortie : 0 si tous les temoins passent, 1 si un temoin tombe — ⚠️ ET AUSSI 1
si l'instrument MEURT (trace nue). Un lecteur qui voit `rc=1` doit donc
regarder si la ligne `⇒ TEMOIN :` a ete imprimee : sans elle, l'instrument
n'a pas juge, il est mort. C'est le meme discriminant que pour une gate —
l'absence de bilan, ⛔ pas le code de retour.
⛔ Le `rc` ne dit RIEN des verdicts : un constat VRAI n'est pas une erreur de
   cet outil, c'est son resultat.
"""

import argparse
import ast
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

DESKNODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COCKPIT_DEFAUT = os.path.join(os.environ.get("HOME") or "/nonexistent",
                              "projects", "compagnon_project")

ok_temoins = [0]
ko_temoins = [0]


def titre(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)


def temoin(attendu, obtenu, libelle):
    """Un temoin qui REPLANTE : il dit ce qu'il attend ET ce qu'il a eu."""
    bon = (attendu == obtenu)
    if bon:
        ok_temoins[0] += 1
        print("  [OK ] %-56s %r" % (libelle, obtenu))
    else:
        ko_temoins[0] += 1
        print("  [KO ] %-56s attendu %r, obtenu %r" % (libelle, attendu, obtenu))
    return bon


def run(cmd, cwd=None, timeout=600):
    """⛔ JAMAIS le shell de session. Toujours ici."""
    t0 = time.time()
    p = subprocess.run(cmd, cwd=cwd, timeout=timeout,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (p.returncode,
            p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"),
            time.time() - t0)


# ═══════════════════════════════════════════════════════════════════════════
# LES PRIMITIVES DE MESURE — chacune a son temoin plus bas
# ═══════════════════════════════════════════════════════════════════════════

def motif_resout(motif, depot=None):
    """Combien de fichiers portent ce motif A `HEAD`. ⛔ pas dans l'arbre de
    travail : un motif se verifie sur ce qui est COMMITE."""
    rc, out, _, _ = run(["git", "grep", "-l", "-F", "--", motif, "HEAD", "--"],
                        cwd=depot or DESKNODE)
    if rc not in (0, 1):
        return None
    return len([l for l in out.split("\n") if l.strip()])


def porte_bilan(txt):
    """Une gate qui MEURT n'imprime pas de ligne `BILAN`. C'est le
    discriminant d'une gate morte — ⛔ pas l'absence de sortie."""
    return bool(re.search(r"^BILAN\s*:", txt, re.M))


def est_traceback(txt):
    return "Traceback (most recent call last)" in txt


def declare_cockpit_ast(chemin):
    """LA VERITE : `--cockpit` est-il declare a argparse, quelle que soit la
    FORME d'ecriture (guillemets simples, chaine coupee sur deux lignes) ?"""
    try:
        arbre = ast.parse(io.open(chemin, encoding="utf-8", errors="replace").read())
    except (SyntaxError, OSError):
        return None
    for n in ast.walk(arbre):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        if not (isinstance(f, ast.Attribute) and f.attr == "add_argument"):
            continue
        for a in n.args:
            if isinstance(a, ast.Constant) and a.value == "--cockpit":
                return True
    return False


def declare_cockpit_litteral(chemin):
    """CE QUE LE RUNNER VOIT : `run_gates.sh` epingle la CHAINE LITTERALE
    `add_argument("--cockpit"`. Toute autre forme lui est invisible."""
    try:
        txt = io.open(chemin, encoding="utf-8", errors="replace").read()
    except OSError:
        return None
    return 'add_argument("--cockpit"' in txt


def bilan_de(txt):
    m = re.search(r"^BILAN\s*:\s*(\d+)\s*OK,\s*(\d+)\s*KO", txt, re.M)
    return (int(m.group(1)), int(m.group(2))) if m else None


def section1(txt):
    """🔴 LA SECTION 1 SEULEMENT — ⛔ PAS TOUTE LA SORTIE.

    Le premier jet de cet instrument comptait sur l'output ENTIER : les
    `[ ×× ]` de la section 3 et les `[OK ]` du controle de date etaient
    comptes une SECONDE fois, et le total depassait les 6 fichiers de
    `AUTORITE`. ⇒ un nombre FABRIQUE, exactement le defaut que cette epic
    paie depuis quatre marches. La borne est le titre de section, ⛔ pas un
    numero de ligne."""
    m = re.search(r"^── 1\..*?$(.*?)^── 2\.", txt, re.M | re.S)
    return m.group(1) if m else ""


def compte_lignes_section1(txt):
    """Ce que la section 1 de `verif_dossier_d5_dn45.py` a REELLEMENT fait.
    ⇒ separe « fichiers qui ont rendu un verdict » de « fichiers muets ».
    ⚠️ La garde globale `total > 0` est imprimee DANS la section 1 : elle est
    comptee a part, sinon elle passerait pour un verdict de fichier."""
    s = section1(txt) or txt
    hors = len(re.findall(r"^\s*\[ ×× \]", s, re.M))
    muets = len(re.findall(r"^\s*\[ -- \]", s, re.M))
    verdicts = len(re.findall(r"^\s*\[(?:OK |KO )\]", s, re.M))
    return hors, muets, verdicts


# ═══════════════════════════════════════════════════════════════════════════
# LE TEMOIN — IL REPLANTE LA FAUTE, ⛔ IL NE DEBRANCHE RIEN
# ═══════════════════════════════════════════════════════════════════════════

def temoins():
    titre("TEMOIN DE L'INSTRUMENT — ⛔ SI UN SEUL TOMBE, ON NE CONCLUT RIEN")
    print("""
Chaque primitive est exercee sur un cas ou la faute est REPLANTEE (elle DOIT
la voir) ET sur un cas ou elle est absente (elle NE DOIT PAS la voir). C'est
la lecon de `dn5-3` : son instrument repondait « ✅ NON » sur une chaine qui
portait le defaut, et le temoin qui le gardait ne regardait que le MOTIF.
""")

    # (a) `motif_resout` — un motif present, un motif absent.
    temoin(True, (motif_resout("def occurrences") or 0) > 0,
           "motif_resout voit un motif PRESENT")
    temoin(0, motif_resout("dn56-motif-qui-n-existe-nulle-part-8f3a1c"),
           "motif_resout ne voit PAS un motif absent")

    # (b) `porte_bilan` — une sortie qui en porte une, une qui n'en porte pas.
    temoin(True, porte_bilan("bla\nBILAN : 5 OK, 0 KO\nbla"),
           "porte_bilan voit une ligne BILAN")
    temoin(False, porte_bilan("Traceback (most recent call last):\n  ...\n"),
           "porte_bilan ne voit PAS de BILAN dans un traceback")
    temoin(False, porte_bilan("le mot BILAN cite en milieu de ligne"),
           "porte_bilan n'est pas dupe d'une citation en prose")

    # (c) `est_traceback`
    temoin(True, est_traceback("Traceback (most recent call last):\n"),
           "est_traceback voit un traceback")
    temoin(False, est_traceback("BILAN : 5 OK, 0 KO"),
           "est_traceback ne voit pas de traceback dans un bilan")

    # (d) LE CŒUR DU CONSTAT (4) : ast vs chaine litterale.
    #     Trois fichiers de synthese, la faute REPLANTEE dans le 2e.
    d = tempfile.mkdtemp(prefix="dn56-temoin-")
    try:
        cas = {
            "litteral.py": 'import argparse\nap = argparse.ArgumentParser()\n'
                           'ap.add_argument("--cockpit", default="x")\n',
            "coupe.py":    'import argparse\nap = argparse.ArgumentParser()\n'
                           'ap.add_argument(\n    "--cockpit",\n    default="x")\n',
            "simple.py":   "import argparse\nap = argparse.ArgumentParser()\n"
                           "ap.add_argument('--cockpit', default='x')\n",
            "prose.py":    'import argparse\n# on cite add_argument("--cockpit" en prose\n'
                           'ap = argparse.ArgumentParser()\n',
        }
        for nom, src in cas.items():
            io.open(os.path.join(d, nom), "w", encoding="utf-8").write(src)
        p = lambda n: os.path.join(d, n)

        temoin(True, declare_cockpit_ast(p("litteral.py")),
               "ast voit la forme LITTERALE")
        temoin(True, declare_cockpit_ast(p("coupe.py")),
               "ast voit la forme COUPEE sur deux lignes")
        temoin(True, declare_cockpit_ast(p("simple.py")),
               "ast voit la forme en guillemets SIMPLES")
        temoin(False, declare_cockpit_ast(p("prose.py")),
               "ast n'est PAS dupe d'une citation en prose")

        temoin(True, declare_cockpit_litteral(p("litteral.py")),
               "le grep du runner voit la forme LITTERALE")
        temoin(False, declare_cockpit_litteral(p("coupe.py")),
               "🔴 le grep du runner est AVEUGLE a la forme coupee")
        temoin(False, declare_cockpit_litteral(p("simple.py")),
               "🔴 le grep du runner est AVEUGLE aux guillemets simples")
        temoin(True, declare_cockpit_litteral(p("prose.py")),
               "🔴 le grep du runner est DUPE par une citation en prose")
    finally:
        shutil.rmtree(d, ignore_errors=True)

    # (e) `compte_lignes_section1`
    faux = ("── 1. LES FICHIERS ────\n"
            "  [ ×× ] a  HORS de portee\n  [ -- ] b  aucune occurrence\n"
            "  [OK ] c  ok\n  [KO ] d  ko\n"
            "── 2. CE QUI EST ECARTE ────\n"
            "  [ ×× ] a  HORS de portee\n  [OK ] c  date le constat\n")
    temoin((1, 1, 2), compte_lignes_section1(faux),
           "compte_lignes_section1 separe hors/muet/verdict")
    temoin(True, "[ ×× ] a" in section1(faux),
           "section1 garde ce qui est AVANT la borne 2")
    temoin(False, "date le constat" in section1(faux),
           "🔴 section1 ne compte PAS la section 3 (defaut du 1er jet)")

    # (f) `bilan_de`
    temoin((22, 10), bilan_de("BILAN : 22 OK, 10 KO"), "bilan_de lit un bilan")
    temoin(None, bilan_de("pas de bilan ici"), "bilan_de ne fabrique pas de bilan")

    print("\n  ⇒ TEMOIN : %d OK, %d KO" % (ok_temoins[0], ko_temoins[0]))
    return ko_temoins[0] == 0


# ═══════════════════════════════════════════════════════════════════════════
# LES CONSTATS
# ═══════════════════════════════════════════════════════════════════════════

VERDICTS = []


def constat(n, titre_c, motif, corps):
    print("\n" + "─" * 78)
    print("CONSTAT (%d) — %s" % (n, titre_c))
    print("─" * 78)
    r = motif_resout(motif)
    print("  preuve par motif : %r" % motif)
    print("  ⇒ resout sur %s fichier(s) a HEAD%s"
          % (r, "   🔴 LE MOTIF EST MORT" if r == 0 else ""))
    verdict, pourquoi = corps()
    print("\n  ┏━ VERDICT : %s" % verdict)
    print("  ┗━ motif   : %s" % pourquoi)
    VERDICTS.append((n, verdict, pourquoi))
    return verdict


def faux_cockpit(illisible=None):
    """Un cockpit de SYNTHESE : les 2 fichiers faisant autorite, et rien
    d'autre. ⛔ Le vrai cockpit n'est jamais modifie."""
    d = tempfile.mkdtemp(prefix="dn56-cockpit-")
    sous = os.path.join(d, "_bmad-output", "implementation-artifacts")
    os.makedirs(sous)
    for nom in ("deferred-work.md", "sprint-status-desknode.yaml"):
        src = os.path.join(COCKPIT_DEFAUT, "_bmad-output",
                           "implementation-artifacts", nom)
        dst = os.path.join(sous, nom)
        if os.path.exists(src):
            shutil.copyfile(src, dst)
        else:
            io.open(dst, "w", encoding="utf-8").write("")
    if illisible:
        os.chmod(os.path.join(sous, illisible), 0)
    return d


def c1():
    """(1) un fichier faisant autorite ILLISIBLE tue la gate en PermissionError
    NU, sans ligne BILAN."""
    gate = os.path.join(DESKNODE, "tools", "verif_dossier_d5_dn45.py")

    # A — TEMOIN POSITIF : le MEME cockpit de synthese, LISIBLE.
    a = faux_cockpit()
    try:
        rc_a, out_a, err_a, _ = run(["python3", gate, "--cockpit", a])
    finally:
        shutil.rmtree(a, ignore_errors=True)
    print("\n  A · cockpit de synthese LISIBLE (temoin positif)")
    print("      rc=%d · BILAN present : %s · traceback : %s"
          % (rc_a, porte_bilan(out_a), est_traceback(err_a)))
    print("      BILAN lu : %r" % (bilan_de(out_a),))

    # B — LA FAUTE REPLANTEE : le meme, avec UN fichier a chmod 000.
    b = faux_cockpit(illisible="sprint-status-desknode.yaml")
    # ⚠️ LE `chmod 000` PEUT ETRE INOPERANT — root, ou un systeme de fichiers
    #    qui ignore les modes. Sans ce controle, l'A/B conclurait « DEJA FAUX »
    #    alors que RIEN n'aura jamais ete illisible.
    _cible = os.path.join(b, "_bmad-output", "implementation-artifacts",
                          "sprint-status-desknode.yaml")
    _mord = False
    try:
        io.open(_cible, encoding="utf-8").read()
    except OSError:
        _mord = True
    print("\n  ⚠️ le `chmod 000` mord-il sur ce systeme ? %s" % _mord)
    if not _mord:
        os.chmod(_cible, 0o600)
        shutil.rmtree(b, ignore_errors=True)
        return ("NON REPRODUCTIBLE",
                "le `chmod 000` ne rend PAS le fichier illisible ici (uid=%d) "
                "⇒ l'A/B ne peut pas etre monte, ⛔ on ne conclut RIEN."
                % os.getuid())
    try:
        rc_b, out_b, err_b, _ = run(["python3", gate, "--cockpit", b])
    finally:
        os.chmod(os.path.join(b, "_bmad-output", "implementation-artifacts",
                              "sprint-status-desknode.yaml"), 0o600)
        shutil.rmtree(b, ignore_errors=True)
    print("\n  B · MEME cockpit, `sprint-status-desknode.yaml` a chmod 000")
    print("      rc=%d · BILAN present : %s · traceback : %s"
          % (rc_b, porte_bilan(out_b), est_traceback(err_b)))
    derniere = [l for l in err_b.strip().split("\n") if l.strip()]
    print("      derniere ligne de stderr : %r"
          % (derniere[-1] if derniere else ""))

    if est_traceback(err_b) and not porte_bilan(out_b) and porte_bilan(out_a):
        return ("VRAI",
                "l'A/B isole la seule variable : cockpit LISIBLE ⇒ BILAN ; "
                "MEME cockpit avec un fichier a chmod 000 ⇒ traceback NU, "
                "⛔ AUCUNE ligne BILAN. `balayage_arbre` attrape `OSError`, "
                "`occurrences` ⛔ pas.")
    if porte_bilan(out_b):
        return ("DEJA FAUX",
                "la gate rend un BILAN malgre le fichier illisible ⇒ "
                "l'exception est desormais traitee.")
    return ("NON REPRODUCTIBLE",
            "le temoin positif lui-meme ne rend pas de BILAN (rc=%d) ⇒ "
            "l'A/B ne discrimine rien, ⛔ on ne conclut pas." % rc_a)


def _sans_cockpit():
    gate = os.path.join(DESKNODE, "tools", "verif_dossier_d5_dn45.py")
    absent = os.path.join(tempfile.gettempdir(), "dn56-cockpit-absent-8f3a1c")
    return run(["python3", gate, "--cockpit", absent])


def c2():
    """(2) la SEULE garde globale est satisfaite par UNE occurrence : le
    `N OK / 0 KO` peut se calculer sur une population fondue."""
    rc, out, err, _ = _sans_cockpit()
    hors, muets, verdicts = compte_lignes_section1(out)
    b = bilan_de(out)
    garde = re.search(r"^\s*\[(OK |KO )\]\s*le balayage a bien trouve des occurrences.*$",
                      out, re.M)
    print("\n  commande : verif_dossier_d5_dn45.py --cockpit <absent>")
    print("  rc = %d · BILAN = %r" % (rc, b))
    print("  section 1 : %d fichier(s) HORS de portee · %d MUET(s) · "
          "%d verdict(s) de fichier" % (hors, muets, verdicts - 1 if garde else verdicts))
    print("  la SEULE garde globale : %s"
          % (garde.group(0).strip() if garde else "⛔ ABSENTE"))
    controlants = verdicts - (1 if garde else 0)
    print("  ⇒ sur les 6 fichiers faisant autorite, %d ont rendu un verdict "
          "et %d n'ont RIEN controle" % (controlants, hors + muets))

    if b and b[1] == 0 and (hors + muets) >= 3 and garde:
        return ("VRAI",
                "%d des 6 fichiers faisant autorite n'ont RIEN controle "
                "(%d hors de portee + %d muets), et le bilan sort quand meme "
                "en `%d OK, %d KO` : la seule garde globale "
                "(`total > 0`) est satisfaite par UNE occurrence."
                % (hors + muets, hors, muets, b[0], b[1]))
    if not garde:
        return ("NON REPRODUCTIBLE",
                "la garde globale n'apparait plus dans la sortie ⇒ la forme "
                "du constat a change, ⛔ on ne conclut pas sans la relire.")
    return ("DEJA FAUX",
            "le bilan ne se calcule plus sur une population fondue : %r" % (b,))


def c3():
    """(3) `--cockpit` relatif : la validation tombe APRES le `cd`, et ne
    normalise jamais."""
    runner = os.path.join(DESKNODE, "tools", "run_gates.sh")
    parent = os.path.dirname(DESKNODE)          # ~/projects
    rel_vrai = os.path.basename(COCKPIT_DEFAUT)  # compagnon_project

    existe = os.path.isdir(os.path.join(parent, rel_vrai))
    print("\n  A · depuis %s, `--cockpit %s`" % (parent, rel_vrai))
    print("      ce chemin existe-t-il depuis ce cwd ? %s" % existe)
    # 🔴 REVUE DU 2026-09-05 — CE `run()` LEVAIT `TimeoutExpired` ET TUAIT TOUT
    #    L'INSTRUMENT. Motif : le correctif du constat (3) fait desormais
    #    ACCEPTER le chemin relatif ⇒ la passe ENTIERE demarre (~130 s) au lieu
    #    de sortir en 2 en une seconde. Mesure : l'instrument ne rendait plus
    #    aucun tableau de verdicts. ⇒ meme forme que le cas B : on borne, on
    #    TUE, et on lit CE QUI A ETE IMPRIME — « la passe a demarre » EST
    #    l'observable, ⛔ pas le `rc`.
    pa = subprocess.Popen(["bash", runner, "--cockpit", rel_vrai],
                          cwd=parent, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    try:
        oa, ea = pa.communicate(timeout=25)
        rc_a, exp_a = pa.returncode, False
    except subprocess.TimeoutExpired:
        pa.kill()
        oa, ea = pa.communicate()
        rc_a, exp_a = None, True
    out_a = oa.decode("utf-8", "replace")
    err_a = ea.decode("utf-8", "replace")
    demarre_a = "gates decouvertes par glob" in out_a
    print("      rc = %s%s" % (rc_a, "  (expire, tue)" if exp_a else ""))
    print("      la passe a-t-elle DEMARRE ? %s" % demarre_a)
    print("      stderr : %r" % (err_a.strip().split("\n")[0][:120]
                                 if err_a.strip() else ""))

    # B — l'homonyme SOUS la racine : `tools` n'existe pas depuis ~/projects,
    #     mais existe sous la racine du depot ⇒ accepte EN SILENCE.
    homonyme = "tools"
    existe_ici = os.path.isdir(os.path.join(parent, homonyme))
    existe_racine = os.path.isdir(os.path.join(DESKNODE, homonyme))
    print("\n  B · depuis %s, `--cockpit %s` (homonyme)" % (parent, homonyme))
    print("      existe depuis ce cwd : %s · existe sous la racine : %s"
          % (existe_ici, existe_racine))
    # ⚠️ ON CAPTURE LA SORTIE PARTIELLE : « il a expire » ne prouve rien tout
    #    seul. Ce qui prouve, c'est que la passe a DEMARRE — donc que la
    #    validation a ACCEPTE le chemin.
    p = subprocess.Popen(["bash", runner, "--cockpit", homonyme, "--silencieux"],
                         cwd=parent, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        o, e = p.communicate(timeout=25)
        rc_b, expire = p.returncode, False
    except subprocess.TimeoutExpired:
        p.kill()
        o, e = p.communicate()
        rc_b, expire = None, True
    out_b = o.decode("utf-8", "replace")
    err_b = e.decode("utf-8", "replace")
    demarre = "gates decouvertes par glob" in out_b
    print("      rc = %s%s" % (rc_b, "  (expire, tue)" if expire else ""))
    print("      la passe a-t-elle DEMARRE ? %s" % demarre)
    prem = [l for l in out_b.split("\n") if l.strip()]
    print("      1re ligne de stdout : %r" % (prem[0][:100] if prem else ""))
    print("      1re ligne de stderr : %r"
          % (err_b.strip().split("\n")[0][:120] if err_b.strip() else ""))

    accepte_homonyme = demarre and rc_b != 2
    if existe and rc_a == 2 and "inexistant" in err_a and not demarre_a:
        return ("VRAI",
                "un chemin QUI EXISTE depuis le `cwd` de l'appelant sort en 2 "
                "sur « chemin inexistant » (la validation tombe APRES le `cd` a "
                "la racine, et ⛔ ne normalise jamais)%s."
                % (" ; et l'homonyme `tools`, qui n'existe PAS depuis ce cwd "
                   "mais existe SOUS la racine, est accepte en silence"
                   if accepte_homonyme else ""))
    if existe and (demarre_a or rc_a != 2):
        return ("DEJA FAUX",
                "le chemin relatif QUI EXISTE depuis le cwd de l'appelant est "
                "desormais ACCEPTE (la passe a demarre : %s ; rc=%s) ⇒ il est "
                "resolu contre ce cwd puis normalise%s."
                % (demarre_a, rc_a,
                   " ; et l'homonyme sous la racine est REFUSE FERME"
                   if not accepte_homonyme else
                   " ⚠️ MAIS l'homonyme sous la racine passe ENCORE"))
    return ("NON REPRODUCTIBLE",
            "le cockpit n'est pas un voisin du depot depuis %s ⇒ l'A/B ne "
            "peut pas etre monte ici." % parent)


def c4():
    """(4) la capacite `--cockpit` se detecte par CHAINE LITTERALE."""
    import glob as _glob
    gates = sorted(_glob.glob(os.path.join(DESKNODE, "tools", "verif_*.py")))
    ecarts, declarantes, vues = [], [], []
    for g in gates:
        a = declare_cockpit_ast(g)
        l = declare_cockpit_litteral(g)
        if a:
            declarantes.append(os.path.basename(g))
        if l:
            vues.append(os.path.basename(g))
        if a != l:
            ecarts.append((os.path.basename(g), a, l))
    print("\n  %d gates au glob `tools/verif_*.py`" % len(gates))
    print("  declarent `--cockpit` a argparse (ast, LA VERITE) : %d ⇒ %s"
          % (len(declarantes), ", ".join(declarantes)))
    print("  vues par le grep litteral du runner                : %d ⇒ %s"
          % (len(vues), ", ".join(vues)))
    print("  ECARTS entre les deux : %d" % len(ecarts))
    for nom, a, l in ecarts:
        print("     · %-40s ast=%s  runner=%s" % (nom, a, l))

    # ⚠️ LA CONVENTION CITEE PAR `dn5-3` EST-ELLE VRAIMENT DANGEREUSE ?
    #    La revue ecrivait : « `dn5-3` a introduit la forme coupee ailleurs
    #    (`add_argument("--csv",`), donc la convention existe dans l'arbre ».
    #    ⇒ ON LE MESURE, ⛔ on ne le reprend pas. Pour CHAQUE option declaree a
    #      argparse dans `tools/`, on demande : la forme litterale
    #      `add_argument("<opt>"` serait-elle vue par un grep comme celui du
    #      runner ? Si non, la declaration est INVISIBLE a ce style de detection.
    invisibles = {}
    tous = sorted(set(gates + [os.path.join(DESKNODE, "tools", f)
                               for f in os.listdir(os.path.join(DESKNODE, "tools"))
                               if f.endswith(".py")]))
    n_opts = 0
    for g in tous:
        try:
            src = io.open(g, encoding="utf-8", errors="replace").read()
            arbre = ast.parse(src)
        except (SyntaxError, OSError, UnicodeDecodeError):
            continue
        for n in ast.walk(arbre):
            if not (isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "add_argument"):
                continue
            for a in n.args:
                if not (isinstance(a, ast.Constant) and isinstance(a.value, str)
                        and a.value.startswith("--")):
                    continue
                n_opts += 1
                if ('add_argument("%s"' % a.value) not in src:
                    invisibles.setdefault(os.path.basename(g), []).append(a.value)
    n_inv = sum(len(v) for v in invisibles.values())
    print("\n  ⚠️ LA « FORME COUPEE » CITEE PAR `dn5-3` EST-ELLE VRAIMENT")
    print("     INVISIBLE AU GREP ? ⇒ MESURE, ⛔ pas repris.")
    print("     %d option(s) longue(s) declaree(s) a argparse dans `tools/`" % n_opts)
    print("     declarations qu'un grep `add_argument(\"<opt>\"` NE VERRAIT PAS : %d"
          % n_inv)
    for nom, opts in sorted(invisibles.items()):
        print("        · %-38s %s" % (nom, ", ".join(opts)))
    csv_vu = 'add_argument("--csv"' in io.open(
        os.path.join(DESKNODE, "tools", "thermique_ventilos_dn48.py"),
        encoding="utf-8", errors="replace").read()
    print("     🔴 LE PRECEDENT QUE LA REVUE CITAIT — `add_argument(\"--csv\",`")
    print("        de `thermique_ventilos_dn48.py` — est-il vu par le grep ? %s"
          % csv_vu)
    print("        ⇒ il replie ses ARGUMENTS SUIVANTS, ⛔ pas le nom de l'option.")

    if ecarts:
        return ("VRAI",
                "%d gate(s) declarent `--cockpit` sous une forme que le grep "
                "litteral du runner ne voit pas ⇒ elles mesurent leur "
                "COCKPIT_DEFAUT en silence." % len(ecarts))
    return ("VRAI (structurel — le bord ⛔ n'est PAS atteint)",
            "les %d gates qui declarent `--cockpit` portent TOUTES la forme "
            "litterale aujourd'hui ⇒ ⛔ AUCUN rouge ne peut le montrer, et le "
            "detecteur du runner est bien AVEUGLE aux formes coupee et "
            "guillemets simples (prouve par le temoin de cet instrument). "
            "🔴 LE PRECEDENT QUE LA REVUE CITAIT EST REFUTE : "
            "`add_argument(\"--csv\",` replie ses ARGUMENTS, ⛔ pas le nom de "
            "l'option ⇒ le grep LA VOIT (mesure : %s). 🎯 MAIS UN PRECEDENT "
            "REEL EXISTE AILLEURS, et il est PIRE : sur %d options declarees "
            "dans `tools/`, %d echappent au grep — %s, en GUILLEMETS SIMPLES. "
            "⇒ la convention dangereuse vit bien dans l'arbre, ⛔ pas la ou la "
            "revue la designait."
            % (len(declarantes), csv_vu, n_opts, n_inv,
               " · ".join("%s (%s)" % (n, ", ".join(o))
                          for n, o in sorted(invisibles.items())) or "aucune"))


def c5():
    """(5) `--analyser <absent>` rend un Traceback NU."""
    outil = os.path.join(DESKNODE, "tools", "thermique_ventilos_dn48.py")
    absent = os.path.join(tempfile.gettempdir(), "dn56-csv-absent-8f3a1c.csv")
    if os.path.exists(absent):
        os.remove(absent)
    rc_a, out_a, err_a, _ = run(["python3", outil, "--analyser", absent])
    print("\n  A · `--analyser <ABSENT>`")
    print("      rc=%d · stdout=%r · traceback : %s"
          % (rc_a, out_a.strip()[:80], est_traceback(err_a)))
    d = [l for l in err_a.strip().split("\n") if l.strip()]
    print("      derniere ligne de stderr : %r" % (d[-1] if d else ""))

    # TEMOIN NEGATIF : le fichier VIDE, lui, est traite proprement.
    vide = os.path.join(tempfile.gettempdir(), "dn56-csv-vide-8f3a1c.csv")
    io.open(vide, "w", encoding="utf-8").write("")
    try:
        rc_b, out_b, err_b, _ = run(["python3", outil, "--analyser", vide])
    finally:
        os.remove(vide)
    print("\n  B · `--analyser <VIDE>` (temoin negatif : ce cas est propre)")
    print("      rc=%d · stdout=%r · traceback : %s"
          % (rc_b, out_b.strip()[:80], est_traceback(err_b)))

    if est_traceback(err_a) and not out_a.strip():
        return ("VRAI",
                "un chemin ABSENT rend `rc=%d`, `stdout` VIDE et un traceback "
                "nu, alors que le fichier VIDE est traite proprement "
                "(rc=%d, message nomme) ⇒ l'ecart est dans le traitement de "
                "l'absence, ⛔ pas du contenu." % (rc_a, rc_b))
    return ("DEJA FAUX",
            "l'absence est desormais nommee : rc=%d, stdout=%r"
            % (rc_a, out_a.strip()[:120]))


def c6():
    """(6) le defaut de `--csv` est un nom FIXE dans un repertoire PARTAGE
    sous Linux."""
    outil = os.path.join(DESKNODE, "tools", "thermique_ventilos_dn48.py")
    rc, out, err, _ = run(["python3", outil, "--help"])
    m = re.search(r"(--csv[^\n]*\n(?:\s+[^\n]*\n)*)", out)
    tmp = tempfile.gettempdir()
    defaut = os.path.join(tmp, "dn48_thermique.csv")
    st = os.stat(tmp)
    partage = bool(st.st_mode & 0o002)   # world-writable ⇒ partage
    sticky = bool(st.st_mode & 0o1000)
    print("\n  `tempfile.gettempdir()` sur CE poste : %r" % tmp)
    print("  TMPDIR dans l'environnement            : %r" % os.environ.get("TMPDIR"))
    print("  chemin par defaut de `--csv`           : %r" % defaut)
    print("  mode du repertoire : %s · world-writable : %s · sticky : %s"
          % (oct(st.st_mode & 0o7777), partage, sticky))
    print("  ⇒ le nom est FIXE (⛔ pas de pid, ⛔ pas d'utilisateur) : %s"
          % ("dn48_thermique.csv" in defaut))
    print("  temoin `.pid` : `enregistrer()` ecrit `<csv>.pid` puis le "
          "supprime en `finally`")
    print("  aide de l'outil pour `--csv` :\n      %s"
          % (m.group(1).strip().replace("\n", "\n      ") if m else "⛔ non trouvee"))

    # ⛔ L'outil n'est PAS exercable ici : il lit `/metrics` sur la tour.
    print("\n  ⚠️ CE QUI N'EST **PAS** MESURE, ET C'EST ECRIT : la COLLISION "
          "elle-meme.\n     Elle exigerait DEUX comptes Unix jouant "
          "`enregistrer()` en meme temps ;\n     ⛔ l'outil ne s'execute pas "
          "sur ce poste (il lit `/metrics` sur la tour).")

    if partage and "dn48_thermique.csv" in defaut and not os.environ.get("TMPDIR"):
        return ("VRAI (structurel — atteignable, ⛔ pas atteint)",
                "sous Linux `gettempdir()` rend %r, world-writable et partage "
                "par tous les comptes, et le nom du defaut est FIXE ⇒ deux "
                "comptes visent le MEME csv et le MEME `.pid`. ⛔ La collision "
                "n'est pas jouee ici : l'outil est Windows-only en pratique."
                % tmp)
    return ("DEJA FAUX",
            "le defaut n'est plus partage : %r (world-writable=%s)"
            % (defaut, partage))


def c7():
    """(7) la gate IMPRIME une regle de `rc` qu'elle ⛔ ne suit pas."""
    rc, out, err, _ = _sans_cockpit()
    b = bilan_de(out)
    regle = re.search(r"^.*UNIQUEMENT si la moitie jouee est.*$", out, re.M)
    suite = re.search(r"^\s*MUETTE\s*;.*$", out, re.M)
    print("\n  commande : verif_dossier_d5_dn45.py --cockpit <absent>")
    print("  regle IMPRIMEE : %r" % (regle.group(0).strip() if regle else None))
    print("  rc REELLEMENT rendu : %d · BILAN : %r" % (rc, b))
    muette = (b is None) or (b == (0, 0))
    print("  la moitie jouee est-elle MUETTE ? %s (elle a rendu %s verdict(s))"
          % (muette, b[0] + b[1] if b else "aucun"))

    # Le JUMEAU : la meme formulation, heritee VERBATIM.
    jumeau = os.path.join(DESKNODE, "tools", "verif_dossier_dn415.py")
    src = io.open(jumeau, encoding="utf-8", errors="replace").read()
    a_jumeau = "UNIQUEMENT si la moitie jouee est" in src
    print("  la MEME formulation vit-elle dans `verif_dossier_dn415.py` ? %s"
          % a_jumeau)
    print("     ⚠️ `AC3.3.a` de `dn5-3` EXIGEAIT la copie ⇒ si elle se corrige, "
          "elle se corrige AUX DEUX ENDROITS.")

    if regle and rc == 4 and not muette:
        return ("VRAI",
                "la gate imprime « rc=4 UNIQUEMENT si la moitie jouee est "
                "MUETTE » et rend `rc=4` alors que la moitie jouee a rendu "
                "%d verdict(s) (`BILAN : %d OK, %d KO`)%s."
                % (b[0] + b[1], b[0], b[1],
                   " — et la MEME formulation vit dans `verif_dossier_dn415.py`"
                   if a_jumeau else ""))
    return ("DEJA FAUX",
            "la regle imprimee decrit le `rc` rendu : rc=%d, BILAN=%r" % (rc, b))


def c8():
    """(8) `T2-hors-ligne.txt` ne declare ni chemin ni HEAD pour ses 3 essais."""
    t1 = os.path.join(DESKNODE, "mesures", "dn5-4", "T1-build-froid.txt")
    t2 = os.path.join(DESKNODE, "mesures", "dn5-4", "T2-hors-ligne.txt")
    lire = lambda p: io.open(p, encoding="utf-8", errors="replace").read()
    s1, s2 = lire(t1), lire(t2)
    m = "CONSTATE AVANT LE BUILD"
    print("\n  motif %r" % m)
    print("     · T1-build-froid.txt : %d occurrence(s)" % s1.count(m))
    print("     · T2-hors-ligne.txt  : %d occurrence(s)" % s2.count(m))
    # Le fait non ecrit : T2 declare-t-il un chemin d'arbre ou un HEAD ?
    a_head = bool(re.search(r"\b[0-9a-f]{7,40}\b", s2))
    a_chemin = ("/home/" in s2) or ("cwd" in s2.lower()) or ("arbre" in s2.lower())
    print("  T2 declare-t-il un SHA (motif hexa >=7) ? %s" % a_head)
    print("  T2 declare-t-il un chemin d'arbre / un `cwd` ? %s" % a_chemin)
    print("  ⛔ UNE CAPTURE NE SE RETOUCHE PAS ⇒ le remede est un NOUVEAU TIR, "
          "⛔ pas une edition.")

    # Le nouveau tir est-il jouable ICI ?
    rc_u, _, err_u, _ = run(["unshare", "-r", "-n", "true"], timeout=20)
    idf = os.environ.get("IDF_PATH") or os.path.expanduser("~/esp/esp-idf")
    a_idf = os.path.isdir(idf)
    print("\n  LE NOUVEAU TIR EST-IL JOUABLE DEPUIS CE POSTE ?")
    print("     · `unshare -r -n true` ⇒ rc=%d %s"
          % (rc_u, "" if rc_u == 0 else "(%r)" % err_u.strip()[:80]))
    print("     · ESP-IDF present a %r ⇒ %s" % (idf, a_idf))

    if s1.count(m) > 0 and s2.count(m) == 0 and not a_head:
        if rc_u == 0 and a_idf:
            return ("VRAI",
                    "l'ecart est mesure (motif present 1x dans T1, 0x dans T2) "
                    "et T2 ne declare AUCUN SHA ⇒ le `rc=0` de "
                    "`hello-desknode`, qui porte tout le discriminant, reste "
                    "conditionne a un fait non ecrit. Le nouveau tir est "
                    "jouable ici.")
        return ("VRAI (⛔ le remede n'est PAS jouable depuis ce poste)",
                "l'ecart est mesure (motif 1x dans T1, 0x dans T2 ; aucun SHA "
                "dans T2). ⛔ Mais le nouveau tir exige `unshare -r -n` "
                "(rc=%d) ET ESP-IDF (%s) ⇒ ECART DECLARE, ⛔ pas simule."
                % (rc_u, a_idf))
    return ("DEJA FAUX",
            "T2 declare desormais son arbre (motif=%d, SHA=%s)"
            % (s2.count(m), a_head))


def _portee_marqueurs():
    """Ce que la gate des marqueurs balaie REELLEMENT — on le lui DEMANDE.
    ⛔ Pas un booleen ecrit a la main : c'est ainsi que l'instrument devenait
    incapable de voir une reparation."""
    gate = os.path.join(DESKNODE, "tools", "verif_licences_dn52.py")
    rc, out, _, _ = run([sys.executable, "-c",
                         "import importlib.util as u,subprocess,sys;"
                         "s=u.spec_from_file_location('g',%r);"
                         "m=u.module_from_spec(s);s.loader.exec_module(m);"
                         "f=subprocess.run(['git','ls-files'],cwd=%r,"
                         "capture_output=True,text=True).stdout.split();"
                         "fn=getattr(m,'prose_marqueurs',m.prose_du_depot);"
                         "print(chr(10).join(fn(f)))" % (gate, DESKNODE)])
    return [l.strip() for l in out.split("\n") if l.strip()]


def c9():
    """(9) la gate des marqueurs ne balaie que les `.md` de la racine et de
    `docs/` ⇒ un marqueur cite dans `.github/workflows/*.yml` echappe."""
    gate = os.path.join(DESKNODE, "tools", "verif_licences_dn52.py")
    src = io.open(gate, encoding="utf-8", errors="replace").read()
    m = re.search(r"def prose_du_depot.*?\n\n", src, re.S)
    print("\n  la PORTEE REELLE, lue dans le code :")
    print("      " + (m.group(0).strip().replace("\n", "\n      ") if m else "⛔ non trouvee"))

    # Les marqueurs cites sous `.github/` sont-ils definis dans la roadmap ?
    rc, out, _, _ = run(["git", "grep", "-h", "-o", "-E",
                         r"dn[0-9]+-[0-9]+", "HEAD", "--", ".github"])
    cites = sorted(set(l.strip() for l in out.split("\n") if l.strip()))
    roadmap = io.open(os.path.join(DESKNODE, "docs", "roadmap.md"),
                      encoding="utf-8", errors="replace").read()
    definis = set(re.findall(r"^\|\s*`(dn[0-9]+(?:-[0-9]+)*)`", roadmap, re.M))
    manquants = [c for c in cites if c not in definis]
    print("\n  marqueurs cites sous `.github/` : %s" % (", ".join(cites) or "aucun"))
    print("  definis dans `docs/roadmap.md`  : %d" % len(definis))
    print("  ⇒ MANQUANTS (ce qui ferait rougir la gate SI elle regardait) : %s"
          % (", ".join(manquants) or "AUCUN"))

    # Ce que `gates.yml` AFFIRME de la portee de ce controle.
    gy = io.open(os.path.join(DESKNODE, ".github", "workflows", "gates.yml"),
                 encoding="utf-8", errors="replace").read()
    aff = re.search(r"^.*exige que tout marqueur cit.*$", gy, re.M)
    print("\n  ce que `.github/workflows/gates.yml` AFFIRME de sa portee :")
    print("      %s" % (aff.group(0).strip() if aff else "⛔ non trouve"))
    plus_large = bool(aff) and ("docs/" not in (aff.group(0) if aff else ""))

    # La gate est-elle verte aujourd'hui ?
    rc_g, out_g, _, _ = run(["python3", gate])
    print("\n  la gate aujourd'hui : rc=%d · BILAN=%r" % (rc_g, bilan_de(out_g)))

    # 🔴 REVUE DU 2026-09-05 — CE BOOLEEN ETAIT UN **LITTERAL**. L'instrument
    #    ne pouvait donc PAS voir sa propre reparation : rejoue apres correctif,
    #    il rendait encore « VRAI PAR MOITIE » sur un constat REPARE. ⇒ il se
    #    MESURE : la gate balaie-t-elle les `.yml`, oui ou non ?
    yml_hors_portee = not any(
        f.startswith(".github/workflows/")
        for f in _portee_marqueurs())
    if manquants:
        return ("VRAI",
                "%d marqueur(s) cite(s) sous `.github/` ne sont pas definis "
                "dans `docs/roadmap.md` et la gate reste VERTE (rc=%d) ⇒ le "
                "cas se reproduit tel quel." % (len(manquants), rc_g))
    if yml_hors_portee and plus_large:
        return ("VRAI PAR MOITIE — le CAS est tombe, le TROU tient",
                "🔴 LE CAS DE DEMONSTRATION EST **DEJA FAUX** : les %d "
                "marqueurs cites sous `.github/` sont TOUS definis dans la "
                "roadmap (`dn5-5` y a ajoute `dn4-45`) ⇒ elargir la portee "
                "aujourd'hui laisserait la gate VERTE. 🔴 LE TROU STRUCTUREL "
                "TIENT : `prose_du_depot` filtre sur `.md` (racine + `docs/`), "
                "donc `.github/workflows/*.yml` n'est JAMAIS balaye, et "
                "`gates.yml` affirme de ce controle une portee plus large que "
                "la sienne. ⇒ ⛔ AUCUN rouge ne peut l'etablir : seul un "
                "mutant qui REPLANTE la faute le peut." % len(cites))
    return ("DEJA FAUX",
            "la portee couvre desormais les fichiers hors `.md`, ou "
            "`gates.yml` ne sur-declare plus.")


def c10():
    """(10) la preuve `controle ⇒ couvert` de `verif_licences_dn52.py` est une
    CAPTURE UNIQUE : rien ne rejoue ses mutants."""
    gate = os.path.join(DESKNODE, "tools", "verif_licences_dn52.py")
    runner = io.open(os.path.join(DESKNODE, "tools", "run_gates.sh"),
                     encoding="utf-8", errors="replace").read()
    gy = io.open(os.path.join(DESKNODE, ".github", "workflows", "gates.yml"),
                 encoding="utf-8", errors="replace").read()
    camp = io.open(os.path.join(DESKNODE, "tools", "verif_campagne_dn440.py"),
                   encoding="utf-8", errors="replace").read()

    print("\n  QUI REJOUE LES MUTANTS DE CETTE GATE ?")
    print("     · `tools/run_gates.sh` cite-t-il `--mutant` ? %s"
          % ("--mutant" in runner))
    print("     · `.github/workflows/gates.yml` cite-t-il `--mutant` ? %s"
          % ("--mutant" in gy))
    vise = "verif_licences_dn52" in camp
    print("     · `tools/verif_campagne_dn440.py` vise-t-il cette gate ? %s"
          % vise)
    cibles = re.findall(r'^REL_\w+\s*=\s*"([^"]+)"', camp, re.M)
    print("       (ses cibles declarees : %s)" % ", ".join(cibles))

    # Le compte de mutants : la ligne du tracker dit 28.
    rc_l, out_l, _, _ = run(["python3", gate, "--liste-mutants"])
    nums = sorted(int(m) for m in re.findall(r"^\s*(\d+)\s+\S", out_l, re.M))
    print("\n  `--liste-mutants` ⇒ %d mutant(s) : %s..%s"
          % (len(nums), nums[0] if nums else "-", nums[-1] if nums else "-"))
    # 🔴 REVUE DU 2026-09-05 — LE « 28 » ETAIT UN LITTERAL, REINJECTE DANS LE
    #    VERDICT SANS QUE LE TRACKER SOIT JAMAIS LU. ⇒ on le LIT.
    _trk = os.path.join(COCKPIT_DEFAUT, "_bmad-output",
                        "implementation-artifacts", "sprint-status-desknode.yaml")
    _annonce = None
    try:
        _txt = io.open(_trk, encoding="utf-8", errors="replace").read()
        _m = re.search(r"re-joue les (\d+) mutants|les (\d+) mutants de cette gate",
                       _txt)
        if _m:
            _annonce = _m.group(1) or _m.group(2)
    except OSError:
        pass
    print("  ⚠️ CE QUE LA LIGNE DU TRACKER ANNONCE, **LU** : %s"
          % (_annonce if _annonce else "⛔ non trouve dans le tracker"))

    rouges, verts = [], []
    for n in nums:
        rc_m, out_m, _, _ = run(["python3", gate, "--mutant", str(n)])
        (rouges if rc_m == 1 else verts).append((n, rc_m))
    print("  rejeu de TOUS les mutants a HEAD : %d ROUGE(S), %d NON-ROUGE(S)"
          % (len(rouges), len(verts)))
    if verts:
        print("     ⛔ NON-ROUGES : %s" % ", ".join("%d(rc=%d)" % v for v in verts))

    # L'hypothese qui rend la cle de campagne valide.
    hyp = motif_resout("cle valide (aucun libelle >= 58)")
    rc_h, out_h, _, _ = run(["git", "grep", "-l", "-F", "--",
                             "cle valide (aucun libelle >= 58)", "HEAD", "--"])
    print("\n  l'hypothese `cle valide (aucun libelle >= 58)` resout dans "
          "%s fichier(s) :" % hyp)
    for l in out_h.strip().split("\n"):
        if l.strip():
            print("     · %s" % l.strip())
    print("     ⇒ elle ne vit que dans une CAPTURE, ⛔ dans aucun controle.")

    # 🔴 REVUE DU 2026-09-05 — CE PREDICAT NE POUVAIT PAS VOIR SA REPARATION.
    #    Il cherchait `--mutant` dans `run_gates.sh` / `gates.yml`, que le
    #    correctif n'y ajoute PAS : la campagne est rejouee par une GATE du
    #    glob, donc jouee par le runner SANS argument. ⇒ la vraie question est
    #    « une gate du glob rejoue-t-elle des campagnes ? », et on la MESURE.
    import glob as _g
    rejoueurs = []
    for _gate in sorted(_g.glob(os.path.join(DESKNODE, "tools", "verif_*.py"))):
        _src = io.open(_gate, encoding="utf-8", errors="replace").read()
        # une gate REJOUEUSE lance D'AUTRES gates avec `--mutant`
        if "--mutant" in _src and "subprocess.run" in _src and \
                "liste-mutants" in _src and os.path.basename(_gate) != \
                os.path.basename(gate):
            rejoueurs.append(os.path.basename(_gate))
    print("\n  UNE GATE DU GLOB REJOUE-T-ELLE DES CAMPAGNES ? %s"
          % (", ".join(rejoueurs) if rejoueurs else "⛔ AUCUNE"))
    rien_ne_rejoue = (("--mutant" not in runner) and ("--mutant" not in gy)
                      and not vise and not rejoueurs)
    if rien_ne_rejoue:
        return ("VRAI",
                "⛔ NI `run_gates.sh` ⛔ NI `gates.yml` ne citent `--mutant`, et "
                "`verif_campagne_dn440.py` est scopee au ledger/tracker du "
                "cockpit (%s) ⇒ la preuve `controle ⇒ couvert` repose sur une "
                "CAPTURE UNIQUE. ⚠️ Elle n'a pas encore pourri (%d/%d mutants "
                "rougissent a HEAD), mais rien ne le verra le jour ou ca "
                "changera. 🔴 ET LE COMPTE A DEJA BOUGE : %d mutants "
                "aujourd'hui, contre %s annonces au tracker (LU, ⛔ pas recopie)."
                % (", ".join(cibles), len(rouges), len(nums), len(nums),
                   _annonce or "un nombre introuvable"))
    return ("DEJA FAUX",
            "un chemin automatique rejoue desormais les mutants : %s — "
            "elle est DANS le glob `tools/verif_*.py`, donc jouee par "
            "`run_gates.sh` ET par la CI, sans argument."
            % (", ".join(rejoueurs) or "voie non identifiee"))


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--temoin-seul", action="store_true",
                    help="ne joue que le temoin de l'instrument")
    a = ap.parse_args()

    print("=" * 78)
    print("dn5-6 / T1 — LE FILTRE : LES 10 CONSTATS REJOUES UN PAR UN")
    print("=" * 78)
    rc, out, _, _ = run(["git", "rev-parse", "HEAD"])
    print("date       : %s" % time.strftime("%Y-%m-%dT%H:%M:%S"))
    print("desknode   : %s" % out.strip())
    rc, out, _, _ = run(["git", "rev-parse", "HEAD"], cwd=COCKPIT_DEFAUT)
    print("cockpit    : %s" % out.strip())
    print("mesures    : ⛔ TOUTES par `subprocess`, ⛔ jamais le shell de session")

    if not temoins():
        print("\n🔴 UN TEMOIN EST TOMBE ⇒ ⛔ AUCUN VERDICT N'EST PUBLIE.")
        return 1
    if a.temoin_seul:
        return 0

    titre("LES 10 CONSTATS")
    print("""
⚠️ LE PERIMETRE EST **10**, ⛔ PAS 13. Les constats 11, 12 et 13 sont des
   CONDITIONS DE PUBLICATION : ils portent deja LEUR PROPRE LIGNE dans la
   liste AC5.6 deposee au tracker par `dn5-5` (lignes 8, 9, 10), porteur
   `epic-dn8`. La ligne 15 de cette meme liste l'ecrit.
""")

    constat(1, "un fichier faisant autorite ILLISIBLE tue la gate sans BILAN",
            "def occurrences", c1)
    constat(2, "le `N OK / 0 KO` se calcule sur une population fondue",
            "le balayage a bien trouve des occurrences", c2)
    constat(3, "`--cockpit` relatif : validation APRES le `cd`, jamais normalisee",
            "--cockpit attend un chemin", c3)
    constat(4, "la capacite `--cockpit` se detecte par CHAINE LITTERALE",
            'add_argument("--cockpit"', c4)
    constat(5, "`--analyser <absent>` rend un Traceback NU",
            "def analyser", c5)
    constat(6, "le defaut de `--csv` : nom FIXE dans un repertoire PARTAGE",
            "dn48_thermique.csv", c6)
    constat(7, "la gate imprime une regle de `rc` qu'elle ne suit pas",
            "UNIQUEMENT si la moitie jouee est", c7)
    constat(8, "`T2-hors-ligne.txt` ne declare ni chemin ni HEAD",
            "CONSTATE AVANT LE BUILD", c8)
    constat(9, "la gate des marqueurs est aveugle aux fichiers hors `.md`",
            "tout marqueur cite COMME marqueur est defini", c9)
    constat(10, "rien ne rejoue les mutants : preuve par CAPTURE UNIQUE",
            "cle valide (aucun libelle >= 58)", c10)

    titre("LE TABLEAU DES VERDICTS")
    for n, v, _ in VERDICTS:
        print("  (%2d)  %s" % (n, v))
    vrais = [n for n, v, _ in VERDICTS if v.startswith("VRAI")]
    faux = [n for n, v, _ in VERDICTS if v.startswith("DEJA FAUX")]
    nr = [n for n, v, _ in VERDICTS if v.startswith("NON REPRODUCTIBLE")]
    print("\n  VRAI              : %d ⇒ %s" % (len(vrais), vrais))
    print("  DEJA FAUX         : %d ⇒ %s" % (len(faux), faux))
    print("  NON REPRODUCTIBLE : %d ⇒ %s" % (len(nr), nr))
    print("\n  ⛔ SEULS LES VRAIS OUVRENT UN CORRECTIF.")
    print("  ⇒ TEMOIN DE L'INSTRUMENT : %d OK, %d KO" % (ok_temoins[0], ko_temoins[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

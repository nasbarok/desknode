# -*- coding: utf-8 -*-
"""dn4-40 / AC40.2 — AUCUN CONTROLE N'ANNONCE « OK » SANS AVOIR REGARDE.

Un `ctrl(True, …)` **litteral** ne peut pas rougir. Ce n'est pas un defaut en
soi : il peut *publier* un fait deja verifie, quand le chemin d'echec **sort en
amont**. Il en est un des que **un arbre defaillant peut l'atteindre**.

  ⇒ LE CRITERE, ECRIT AVANT LE TRI :
      LEGITIME — le chemin d'echec SORT EN AMONT (echec ferme). Le site publie
                 alors un fait que la gate vient de verifier.
      TROU     — un arbre defaillant ATTEINT le site, et il dit « OK » quand
                 meme. Le bilan enfle sans que rien ne soit garde.

🔴 ET LE CRITERE SE PROUVE PAR MUTANT, ⛔ PAS PAR RAISONNEMENT. C'est le motif
   « la claim etait VRAIE, elle n'etait pas PROUVEE ». Pour chaque site declare
   LEGITIME, on REPLANTE la faute que sa garde amont est censee attraper, et le
   temoin est que **le site n'apparait pas dans la trace** : la gate est sortie
   avant. Pour chaque site declare TROU, on vide sa population et le temoin est
   qu'il est **toujours trace OK**.

⚠️ ⛔ AUCUNE ECRITURE DANS L'ARBRE REEL. Chaque mutant travaille dans un arbre
   TEMPORAIRE monte par `git archive HEAD` — donc **commiter avant de mesurer**.
   `managed_components/` (gitignore, 186 Mo) est LIE, ⛔ pas copie.

Usage :  python3 tools/campagne_ctrl_dn440.py [--cockpit CHEMIN]
"""
import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
REL_LED = "_bmad-output/implementation-artifacts/deferred-work.md"
REL_TRK = "_bmad-output/implementation-artifacts/sprint-status-desknode.yaml"
REL_MAN = "_bmad-output/implementation-artifacts/dn4-16-arbitrage-ledger.md"
LVGL = "firmware/desknode/managed_components"


# ── LES MUTATIONS, une par site ─────────────────────────────────────────────
def m_rien(arbre, ck):
    return []


def m_ledger_absent(arbre, ck):
    os.remove(os.path.join(ck, REL_LED))
    return []


def m_ledger_binaire(arbre, ck):
    with open(os.path.join(ck, REL_LED), "wb") as f:
        f.write(b"# ledger\n\xff\xfe pas de l'UTF-8\n")
    return []


def m_tracker_binaire(arbre, ck):
    with open(os.path.join(ck, REL_TRK), "wb") as f:
        f.write(b"development_status:\n  \xff\xfe: done\n")
    return []


def m_cockpit_absent(arbre, ck):
    return ["--cockpit", os.path.join(ck, "nulle-part")]


def m_hist_casse(arbre, ck):
    """REPLANTE une faute de compilation dans `dn_hist.c` — DANS LA COPIE."""
    p = os.path.join(arbre, "firmware/desknode/main/dn_hist.c")
    s = io.open(p, encoding="utf-8").read()
    io.open(p, "w", encoding="utf-8").write(
        s + "\n// mutant dn4-40 : un jeton qui ne compile pas\n$$$\n")
    return []


def m_capture_absente(arbre, ck):
    p = os.path.join(arbre, "mesures/dn4-5/T3-AC4.1-lissage-960.csv")
    if os.path.isfile(p):
        os.remove(p)
    return []


def m_liste_planchers_absente(arbre, ck):
    p = os.path.join(arbre, "firmware/desknode/main/dn_env.h")
    s = io.open(p, encoding="utf-8").read()
    io.open(p, "w", encoding="utf-8").write(
        re.sub(r"Les trois planchers du d.p.t\s*:", "Les trois seuils :", s))
    return []


def m_exemptions_vides(arbre, ck):
    """Vide la POPULATION du site, ⛔ ne debranche pas la garde."""
    p = os.path.join(arbre, "firmware/desknode/main/dn_ui.c")
    s = io.open(p, encoding="utf-8").read()
    io.open(p, "w", encoding="utf-8").write(
        s.replace("DN_VERROU_EXEMPT", "DN_VERROU_ABSENT"))
    return []


# 🔴 LES CAS S'ANCRENT PAR **MOTIF**, ⛔ PLUS PAR NUMERO DE LIGNE — ET CE
#    CORRECTIF EST LUI-MEME UNE MESURE. Premiere version : ce tableau citait
#    les 13 sites par `fichier:ligne`. Poser l'instrument de trace dans les 7
#    gates a decale leurs lignes ⇒ **7 cas sur 13** sont sortis « NON PROUVE »
#    en n'ayant simplement plus la bonne adresse. C'est le defaut que
#    AC40.4.g vise, paye ici, dans l'outil qui le denonce.
#    ⇒ Le site est RESOLU A L'EXECUTION en balayant le source de la gate
#      (commentaires masques), et la cle est le LIBELLE.
#
# (gate, libelle du site, verdict attendu, mutation, ce qu'elle replante)
CAS = [
    ("tools/verif_ledger_dn416.py", "le depot cockpit est atteignable",
     "LEGITIME", m_ledger_absent,
     "le ledger retire du cockpit ⇒ prerequis absent, rc=4, sortie EN AMONT"),
    ("tools/verif_ledger_dn416.py", "le ledger est present",
     "LEGITIME", m_ledger_absent, "idem — meme garde amont"),
    ("tools/verif_ledger_dn416.py", "le tracker est present",
     "LEGITIME", m_ledger_absent, "idem"),
    ("tools/verif_ledger_dn416.py", "le ledger se LIT en UTF-8",
     "LEGITIME", m_ledger_binaire,
     "le ledger rendu NON-UTF-8 ⇒ ctrl(False) puis ARRET"),
    ("tools/verif_ledger_dn416.py", "le tracker se LIT en UTF-8",
     "LEGITIME", m_tracker_binaire,
     "le tracker rendu NON-UTF-8 ⇒ ctrl(False) puis ARRET"),
    ("tools/verif_dossier_dn415.py", "le depot cockpit est atteignable",
     "LEGITIME", m_cockpit_absent,
     "`--cockpit` vers un chemin inexistant ⇒ la branche `absent` est prise"),
    ("tools/verif_hist_dn413.py", "`dn_hist.c` compile et se charge sur l'hôte",
     "LEGITIME", m_hist_casse,
     "`dn_hist.c` rendu incompilable ⇒ ctrl(False) puis `return 1`"),
    ("tools/verif_lissage_dn45.py", "capture rejouee dans le PRODUIT",
     "LEGITIME", m_capture_absente,
     "la capture retiree ⇒ ctrl(False) puis `return 1`"),
    ("tools/verif_paliers_dn441.py",
     "la liste CANONIQUE des trois planchers est lisible",
     "LEGITIME", m_liste_planchers_absente,
     "la liste canonique retiree ⇒ la branche `dire(False)` est prise"),
    # ⚠️ TROISIEME CLASSE, TROUVEE PAR LA MESURE ⛔ PAS PREVUE AU CADRAGE :
    #    le site vit dans une boucle sur une population VIDE aujourd'hui. Il
    #    n'est donc ni LEGITIME (aucune garde amont ne le protege) ni TROU
    #    (aucun arbre ne l'atteint) : il est INERTE. ⇒ Le temoin est
    #    l'ABSENCE de la trace sur l'arbre PROPRE, et c'est falsifiable : le
    #    jour ou une exemption est declaree, il redevient un TROU qui publie
    #    un OK par exemption — le bilan enflerait avec la donnee.
    ("tools/verif_verrou_lvgl_dn413.py", "exemption motivée : ",
     "INERTE", m_rien,
     "population VIDE au 2026-09-02 (`(aucune)` a la console) ⇒ le site "
     "n'est JAMAIS execute"),
    ("tools/verif_dossier_dn415.py",
     "les exclusions sont DECLAREES, ⛔ pas silencieuses",
     "TROU", m_rien,
     "aucune donnee ne peut le rendre faux — il PUBLIE, il ne controle pas"),
    ("tools/verif_journal_soak_dn45.py",
     "⚠️ et la limite de ce calcul est DECLAREE",
     "TROU", m_rien,
     "declaration de limite : aucune donnee ne peut la rendre fausse"),
    ("tools/verif_dossier_d5_dn45.py",
     "les archives sont LISTEES, ⛔ pas ecartees en silence",
     "TROU", m_rien,
     "aucune donnee ne peut le rendre faux ; ⚠️ ses chemins sont ABSOLUS "
     "(dn5-3) ⇒ il lit l'arbre REEL meme depuis une copie"),
]


def site_de(arbre, gate, libelle):
    """L'adresse du site `ctrl(True, …)`, RESOLUE au source, ⛔ pas citee.

    🔴 TOKENISE, ⛔ PAS UNE FENETRE DE CARACTERES. Premiere version : on
    cherchait le libelle dans les 400 caracteres suivant le `ctrl(True,`. Les
    trois sites voisins de la gate du ledger tombaient tous sur le PREMIER, et
    deux cas sur treize sortaient « NON PROUVE » en visant le mauvais site.
    ⇒ On lit le **2e argument litteral** de l'appel, ⛔ rien d'autre.

    ⚠️ Les commentaires ne peuvent pas mentir ici : `tokenize` distingue un
    `ctrl(True, …)` d'un `ctrl(True, …)` CITE dans un commentaire. Ce depot a
    deja paye ce motif, et le premier balayage de cette story l'a repaye.
    """
    import tokenize
    p = os.path.join(arbre, gate)
    with open(p, "rb") as fh:
        toks = [t for t in tokenize.tokenize(fh.readline)
                if t.type not in (tokenize.COMMENT, tokenize.NL,
                                  tokenize.NEWLINE, tokenize.INDENT,
                                  tokenize.DEDENT)]
    for i, t in enumerate(toks[:-5]):
        if t.type != tokenize.NAME or t.string not in ("ctrl", "dire"):
            continue
        if (toks[i + 1].string == "(" and toks[i + 2].string == "True"
                and toks[i + 3].string == ","
                and toks[i + 4].type == tokenize.STRING):
            lit = toks[i + 4].string
            lit = lit[1:-1] if lit[:1] in "\"'" else lit
            if lit.startswith(libelle) or libelle.startswith(lit):
                return "%s:%d" % (os.path.basename(gate), t.start[0])
    return None


def compte_sites(chemin):
    """Les SITES `ctrl()`/`dire()` d'un source — tokenises, ⛔ pas grattes.

    ⚠️ Un premier comptage au motif de ligne rendait 15 sites la ou la gate
    du verrou en porte bien plus : le motif exigeait un debut de ligne et
    ratait tout appel imbrique. Un compte grate n'est pas un compte.
    """
    import tokenize
    with open(chemin, "rb") as fh:
        toks = [t for t in tokenize.tokenize(fh.readline)
                if t.type not in (tokenize.COMMENT, tokenize.NL,
                                  tokenize.NEWLINE, tokenize.INDENT,
                                  tokenize.DEDENT)]
    n = 0
    for i, t in enumerate(toks[:-1]):
        if (t.type == tokenize.NAME and t.string in ("ctrl", "dire")
                and toks[i + 1].string == "("):
            n += 1
    return n


def invocations_reelles(gate, cockpit):
    """Les invocations d'une gate SUR L'ARBRE REEL — lecture seule.

    ⛔ Surtout PAS depuis l'arbre temporaire : il n'a ni les fichiers
    gitignores ni le meme voisinage, et la gate y compte AUTRE CHOSE.
    """
    tmp = tempfile.mkdtemp(prefix="dn440inv-")
    try:
        tr = os.path.join(tmp, "trace.txt")
        args = [sys.executable, os.path.join(RACINE, gate)]
        if gate.endswith(("dn416.py", "dn415.py")):
            args += ["--cockpit", cockpit]
        subprocess.run(args, capture_output=True, text=True, cwd=RACINE,
                       env=dict(os.environ, DN_TRACE_CTRL=tr))
        if not os.path.isfile(tr):
            return []
        return [l for l in io.open(tr, encoding="utf-8") if l.strip()]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def libelles_ctrl_true(arbre, gate):
    """Tous les libelles de `ctrl(True, …)` / `dire(True, …)` d'une gate.

    ⚠️ Meme tokenisation que `site_de` : un site CITE dans un commentaire
    ⛔ n'en est pas un.
    """
    import tokenize
    out = []
    p = os.path.join(arbre, gate)
    with open(p, "rb") as fh:
        toks = [t for t in tokenize.tokenize(fh.readline)
                if t.type not in (tokenize.COMMENT, tokenize.NL,
                                  tokenize.NEWLINE, tokenize.INDENT,
                                  tokenize.DEDENT)]
    for i, t in enumerate(toks[:-5]):
        if (t.type == tokenize.NAME and t.string in ("ctrl", "dire")
                and toks[i + 1].string == "(" and toks[i + 2].string == "True"
                and toks[i + 3].string == ","
                and toks[i + 4].type == tokenize.STRING):
            lit = toks[i + 4].string
            out.append(lit[1:-1] if lit[:1] in "\"'" else lit)
    return out


def monte_arbre(tmp):
    a = os.path.join(tmp, "arbre")
    os.makedirs(a)
    tar = subprocess.run(["git", "archive", "HEAD"], cwd=RACINE,
                         capture_output=True)
    subprocess.run(["tar", "-x", "-C", a], input=tar.stdout, check=True)
    src = os.path.join(RACINE, LVGL)
    if os.path.isdir(src):
        os.symlink(src, os.path.join(a, LVGL))
    return a


def monte_cockpit(tmp, ck_src):
    c = os.path.join(tmp, "cockpit")
    os.makedirs(os.path.join(c, os.path.dirname(REL_LED)))
    for rel in (REL_LED, REL_TRK, REL_MAN):
        s = os.path.join(ck_src, rel)
        if os.path.isfile(s):
            shutil.copy(s, os.path.join(c, rel))
    return c


def joue(gate, mutation, ck_src, ck_reel=False):
    tmp = tempfile.mkdtemp(prefix="dn440ctrl-")
    try:
        a = monte_arbre(tmp)
        c = monte_cockpit(tmp, ck_src)
        extra = mutation(a, c)
        tr = os.path.join(tmp, "trace.txt")
        args = [sys.executable, os.path.join(a, gate)]
        if "--cockpit" in extra:
            args += extra
        elif gate.endswith(("dn416.py", "dn415.py")):
            # ⚠️ `ck_reel` : pour COMPTER les invocations, il faut le cockpit
            #    REEL. Le cockpit temporaire ne porte que 3 fichiers ⇒ la gate
            #    du dossier y rend 21 invocations la ou elle en rend 26 au
            #    poste. Un compte pris sur le montage mesure LE MONTAGE.
            #    ⛔ Lecture seule : aucune mutation n'est appliquee dans ce mode.
            args += ["--cockpit", ck_src if ck_reel else c]
        p = subprocess.run(args, capture_output=True, text=True, cwd=a,
                           env=dict(os.environ, DN_TRACE_CTRL=tr))
        vus = {}
        if os.path.isfile(tr):
            for l in io.open(tr, encoding="utf-8"):
                q = l.rstrip("\n").split("\t")
                if len(q) == 3:
                    vus[q[0]] = q[1]
        return p.returncode, vus
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cockpit", default=os.path.join(
        os.environ.get("HOME") or "/nonexistent", "projects", "compagnon_project"))
    a = ap.parse_args()

    print("=" * 78)
    print("dn4-40 / AC40.2 — TRI DES `ctrl(True, …)` LITTERAUX, PROUVE PAR MUTANT")
    print("=" * 78)
    print("critere : LEGITIME = le chemin d'echec SORT EN AMONT ;")
    print("          TROU     = un arbre defaillant ATTEINT le site.")
    print("⛔ aucune ecriture dans l'arbre reel — `git archive HEAD` + copie.")
    print()

    base = {}
    echecs = []
    tmp0 = tempfile.mkdtemp(prefix="dn440src-")
    arbre0 = monte_arbre(tmp0)
    for gate, libelle, verdict, mut, quoi in CAS:
        cle = site_de(arbre0, gate, libelle)
        if cle is None:
            # 🎯 POUR UN TROU OU UN INERTE, L'ABSENCE **EST** LE VERDICT : le
            #    remede a ete applique (le site publie desormais par `print`,
            #    ⛔ il ne compte plus). Pour un LEGITIME, c'est un echec.
            if verdict in ("TROU", "INERTE"):
                print("  [OK] %-8s %-36s REMEDE APPLIQUE — le site ne COMPTE"
                      " plus (il imprime)" % (verdict, libelle[:34]))
                print("           constat : %s" % quoi)
            else:
                echecs.append(gate + "/" + libelle)
                print("  [!!] %-8s %-36s ⛔ SITE INTROUVABLE au source"
                      % (verdict, libelle[:34]))
            continue
        if gate not in base:
            rc, vus = joue(gate, m_rien, a.cockpit)
            base[gate] = vus
        atteint_propre = cle in base[gate]
        rc, vus = joue(gate, mut, a.cockpit)
        atteint_mute = cle in vus
        if verdict == "INERTE":
            bon = not atteint_propre
            dit = ("CONFIRME INERTE — ⛔ jamais atteint sur l'arbre propre"
                   if bon else "⛔ RECLASSER — il EST atteint")
        elif verdict == "LEGITIME":
            bon = atteint_propre and not atteint_mute
            dit = ("PROUVE — atteint sur l'arbre propre, ⛔ PAS atteint sous"
                   " mutant (rc=%d)" % rc) if bon else \
                  ("⛔ NON PROUVE — propre:%s mute:%s (rc=%d)"
                   % (atteint_propre, atteint_mute, rc))
        else:
            bon = atteint_propre and (atteint_mute or mut is m_exemptions_vides)
            dit = ("CONFIRME TROU — %s" %
                   ("toujours atteint OK sous mutant"
                    if atteint_mute else "population videe, plus rien a garder")) \
                if bon else "⛔ RECLASSER — propre:%s mute:%s" % (atteint_propre,
                                                                 atteint_mute)
        if not bon:
            echecs.append(cle)
        print("  [%s] %-8s %-36s %s" % ("OK" if bon else "!!", verdict, cle, dit))
        print("           mutant : %s" % quoi)

    # ── L'INVENTAIRE : ⛔ AUCUN SITE NON CLASSE ─────────────────────────────
    #    Sans lui, la campagne prouverait le passe et laisserait entrer le
    #    futur : un `ctrl(True, …)` ajoute demain passerait inapercu.
    print("\n── INVENTAIRE : tout `ctrl(True, …)` du depot est-il CLASSE ? ─")
    import glob as _g
    connus = set()
    for gate, libelle, _v, _m, _q in CAS:
        connus.add((os.path.basename(gate), libelle))
    inconnus = []
    for f in sorted(_g.glob(os.path.join(arbre0, "tools", "verif_*.py"))):
        rel = os.path.join("tools", os.path.basename(f))
        for lib in libelles_ctrl_true(arbre0, rel):
            if not any(b == os.path.basename(rel)
                       and (lib.startswith(l) or l.startswith(lib))
                       for b, l in connus):
                inconnus.append("%s :: %s" % (os.path.basename(rel), lib[:44]))
    if inconnus:
        echecs.append("inventaire")
        print("   ⛔ %d SITE(S) NON CLASSE(S) :" % len(inconnus))
        for x in inconnus:
            print("        %s" % x)
    else:
        print("   ✅ aucun site non classe — %d site(s) au tableau" % len(CAS))

    # ── AC40.2.c — LE COMPTE DES CONTROLES REELLEMENT EXERCES ──────────────
    #
    # 🔴 DIRE D'ABORD CE QU'ON COMPTE, SINON LES COMPTES NE SE COMPARENT PAS.
    #    LA CONVENTION, ECRITE UNE FOIS :
    #      SITE       = un appel `ctrl()` / `dire()` dans le SOURCE (statique).
    #                   Certains vivent HORS du chemin par defaut (modes
    #                   `--manifeste`, `--mutant`, branches d'echec).
    #      INVOCATION = un `ctrl()` REELLEMENT EXECUTE dans une passe
    #                   (dynamique) — c'est-a-dire UNE ligne `[OK ]`/`[KO ]`.
    #    ⇒ Le compte publie par une gate sur sa ligne de BILAN est un compte
    #      d'INVOCATIONS. L'ECART avec les sites est publie ici, ⛔ pas tu :
    #      c'est lui qui dit combien de code n'est pas exerce par defaut.
    print("\n── AC40.2.c — CONTROLES EXERCES, PAR GATE TOUCHEE ─────────────")
    print("   convention : SITE = appel au SOURCE · INVOCATION = ligne imprimee")
    print("   ⚠️ MESURE PRISE SUR L'ARBRE REEL ET LE COCKPIT REEL, en lecture")
    print("      seule. Deux montages ont ete essayes avant, et tous deux")
    print("      mesuraient LE MONTAGE : le cockpit temporaire (3 fichiers)")
    print("      fait rendre 21 invocations a la gate du dossier, et l'arbre")
    print("      temporaire 19, la ou le poste en rend 26. ⛔ Un compte pris")
    print("      sur un decor mesure le decor.")
    print("   %-30s %6s %6s %6s %6s"
          % ("gate", "sites", "invoc", "distin", "ecart"))
    touchees = sorted({g for g, _l, _v, _m, _q in CAS})
    for gate in touchees:
        sites = compte_sites(os.path.join(arbre0, gate))
        lignes = invocations_reelles(gate, a.cockpit)
        n = len(lignes)
        distincts = len({l.split("\t")[0] for l in lignes})
        print("   %-30s %6d %6d %6d %6d"
              % (os.path.basename(gate), sites, n, distincts, sites - distincts))
    print("   ⚠️ TROIS COLONNES, ⛔ PAS DEUX — et c'est la mesure qui l'impose.")
    print("      `invoc` peut DEPASSER `sites` : un site dans une boucle")
    print("      s'execute autant de fois que sa population a d'elements.")
    print("      C'est `distincts` (sites REELLEMENT atteints) qui se compare")
    print("      a `sites`, et leur ecart compte le code HORS du chemin par")
    print("      defaut (modes `--manifeste`/`--mutant`, branches d'echec).")
    print("      ⇒ Cet ecart devient un DEFAUT le jour ou rien ne l'exerce —")
    print("        c'est ce que mesure « gardes par rien » (campagne_dn440).")

    shutil.rmtree(tmp0, ignore_errors=True)
    n_leg = sum(1 for c in CAS if c[2] == "LEGITIME")
    n_trou = sum(1 for c in CAS if c[2] == "TROU")
    n_in = sum(1 for c in CAS if c[2] == "INERTE")
    print("\n" + "=" * 78)
    print("BILAN TRI : %d site(s) — %d LEGITIME(S), %d TROU(S), %d INERTE(S),"
          " %d echec(s)" % (len(CAS), n_leg, n_trou, n_in, len(echecs)))
    print("=" * 78)
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())

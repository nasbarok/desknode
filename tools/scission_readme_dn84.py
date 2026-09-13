#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dn8-4 / AC8.4.2 — LA SCISSION DU README EST UNE **SEPARATION**, ET ELLE SE
PROUVE OCTET POUR OCTET.

⛔ CE N'EST PAS UNE GATE, ET LE NOM LE DIT (⛔ pas `verif_`) : le glob de
   `tools/run_gates.sh` ne la ramasse pas, et c'est voulu. La CI clone en
   profondeur 1 — la revision de base n'y existe pas — et le journal CONTINUERA
   d'etre ecrit par les marches suivantes : une gate d'identite rougirait a la
   premiere annotation legitime. ⇒ la preuve porte sur le COUPLE (revision de
   base, commit de scission), et elle est rejouable POUR TOUJOURS en local
   parce que l'historique ne se reecrit jamais (`NFR9`).

── CE QUE L'OUTIL FAIT ─────────────────────────────────────────────────────

    --ecrire   --avant <BASE> --entete <fichier>
        ecrit `docs/journal-de-bord.md` = l'en-tete (le fichier donne) + UNE
        ligne-marqueur qui nomme la base + T(git show BASE:README.md).

    --verifier --avant <BASE> --apres WORKTREE|<fichier>|<revision>
        refait T sur `git show BASE:README.md`, coupe le journal a sa
        ligne-marqueur, et compare le corps **octet pour octet**. Imprime les
        tailles et les `sha256`, chacun des rebasages avec sa ligne, puis
        `IDENTIQUE` ou `DIFFERENT` et la premiere position divergente.
        `--apres` : `WORKTREE` = le fichier sur le disque ; un chemin de
        fichier existant = une copie jetable ; sinon, une revision git.

── T, LA SEULE TRANSFORMATION ADMISE — ET ELLE ECHOUE FERMEE ───────────────

`REBASAGES` ci-dessous est **exhaustif**, et c'est verifie a chaque tir, dans
les deux sens :
  · chaque rebasage doit s'appliquer **EXACTEMENT UNE FOIS**, a SA ligne ;
  · chaque lien LOCAL de la base — lu avec la meme expression que
    `tools/verif_licences_dn52.py` (c1), qui resout un lien DEPUIS LE DOSSIER
    DU FICHIER — doit etre couvert par un rebasage.
Un lien que la table ne couvre pas, ou un rebasage qui ne s'applique pas,
rend `rc=1` NOMME. ⛔ Jamais un repli silencieux sur « on laisse tel quel ».

🔴 LE PIEGE DE LA PREUVE AUTO-REFERENTE, ECRIT ICI PLUTOT QUE TU : `--ecrire`
   et `--verifier` partagent T. Si T est fausse, les deux s'accordent. ⇒ cet
   outil ⛔ ne se prouve PAS seul. Les deux garde-fous independants sont hors
   de lui : un `diff` brut entre la base et le corps du journal doit tomber
   sur les lignes de la table ET RIEN D'AUTRE, et `verif_licences_dn52.py`
   (c1) doit resoudre chaque lien depuis `docs/`.

── CODES DE RETOUR ─────────────────────────────────────────────────────────
    0  IDENTIQUE (verifier) · journal ecrit (ecrire) · `--help`
    1  DIFFERENT, rebasage non applique, lien non couvert, marqueur absent ou
       double, journal introuvable (y compris un `--apres` qui a la forme d'un
       chemin et n'existe pas), `--ecrire` sur un journal qui existe deja
    2  appel invalide (argparse)
    4  revision de base ABSENTE — clone sans historique, ou revision inconnue
"""

import argparse
import hashlib
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import dn_gates
except ImportError as _x:                                 # pragma: no cover
    sys.stderr.write("⛔ `tools/dn_gates.py` est INTROUVABLE (%s) : cet outil "
                     "importe ses helpers, il ⛔ ne les recopie pas.\n" % _x)
    sys.exit(1)

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AVANT_REL = "README.md"
JOURNAL_REL = "docs/journal-de-bord.md"

# La ligne-marqueur : UNIQUE dans le journal, derniere ligne de l'en-tete. Elle
# NOMME la base, et `--verifier` exige que ce soit celle qu'on lui passe.
MARQUEUR_TETE = "<!-- dn8-4 · FIN DE L'EN-TETE · corps = README.md@"
MARQUEUR_QUEUE = " hormis les rebasages de liens -->"
RE_MARQUEUR = re.compile(r"^" + re.escape(MARQUEUR_TETE) + r"([0-9a-f]{40})"
                         + re.escape(MARQUEUR_QUEUE) + r"$")

# (ligne dans README@BASE, cible avant, cible apres). ⚠️ DERIVEE A `T0` SUR
# `README.md@baf4265a292a7db1ae9f6bc8673779f2e743d45b` (2026-09-13) :
# `mesures/dn8-4/T0-borne-entree.txt`. ⛔ Ne pas l'appliquer a une autre base
# sans la re-deriver — c'est exactement ce que le controle d'exhaustivite
# refuse de laisser passer.
REBASAGES = (
    (5, "LICENSING.md", "../LICENSING.md"),
    (6, "THIRD-PARTY.md", "../THIRD-PARTY.md"),
    (7, "CONTRIBUTING.md", "../CONTRIBUTING.md"),
    (7, "CHANGELOG.md", "../CHANGELOG.md"),
    (40, "docs/bom.md", "bom.md"),
    (44, "docs/cablage.md", "cablage.md"),
    (46, "docs/boitier.md", "boitier.md"),
    (1058, "docs/roadmap.md", "roadmap.md"),
    (1064, "installeur/charge/", "../installeur/charge/"),
    (1081, "docs/roadmap.md", "roadmap.md"),
    (1082, "installeur/charge/PROVENANCE.md",
     "../installeur/charge/PROVENANCE.md"),
    (1214, "installeur/IDENTITE.md", "../installeur/IDENTITE.md"),
    (1951, "hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md",
     "../hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md"),
)

# ⚠️ LA MEME EXPRESSION QUE `verif_licences_dn52.py` (c1) — ⛔ pas une plus
#    etroite : un lien que la gate de licences voit et que cet outil ne verrait
#    pas serait un lien que la scission casse sans que la preuve bronche.
RE_LIEN = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


class Echec(Exception):
    """Un echec NOMME de la preuve : `rc=1`."""


class BaseAbsente(Exception):
    """La revision de base n'existe pas ici : `rc=4`."""


def git(*args):
    try:
        r = subprocess.run(["git"] + list(args), cwd=RACINE,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as x:
        raise BaseAbsente("`git` ne se lance pas (%s)" % x)
    return r.returncode, r.stdout, r.stderr.decode("utf-8", "replace").strip()


def resout_base(rev):
    rc, out, err = git("rev-parse", "--verify", "--quiet", rev + "^{commit}")
    if rc != 0:
        raise BaseAbsente("revision de base absente : `%s` ne resout vers aucun "
                          "commit de ce clone (clone sans historique ?) %s"
                          % (rev, err))
    return out.decode("ascii").strip()


def contenu_a(rev, rel):
    rc, out, err = git("show", "%s:%s" % (rev, rel))
    if rc != 0:
        raise Echec("`%s` absent a la revision `%s` : %s" % (rel, rev, err))
    return out


def empreinte(b):
    return "%d o · sha256 %s" % (len(b), hashlib.sha256(b).hexdigest())


def liens_locaux(texte):
    """[(ligne, cible)] — les liens que `dn52 (c1)` resout sur le disque."""
    out = []
    for m in RE_LIEN.finditer(texte):
        cible = m.group(2).strip()
        if cible.startswith(("http", "#", "mailto")):
            continue
        out.append((texte[:m.start()].count("\n") + 1, cible))
    return out


def transforme(avant):
    """T(README@BASE) → (octets, journal des rebasages). ⛔ Echoue FERMEE."""
    try:
        texte = avant.decode("utf-8")
    except UnicodeDecodeError as x:
        raise Echec("la base ne se decode pas en UTF-8 : %s" % x)
    lignes = texte.split("\n")          # ⚠️ `split`, ⛔ pas `splitlines` :
    #                                     aucun octet de fin de ligne ne bouge
    faits = []
    fautes = []
    for num, de, vers in REBASAGES:
        if not 1 <= num <= len(lignes):
            fautes.append("l.%d hors du fichier (%d lignes) pour `%s`"
                          % (num, len(lignes), de))
            continue
        motif = "](%s)" % de
        n = lignes[num - 1].count(motif)
        if n != 1:
            fautes.append("l.%d : `%s` s'y trouve %d fois (attendu EXACTEMENT 1)"
                          % (num, motif, n))
            continue
        lignes[num - 1] = lignes[num - 1].replace(motif, "](%s)" % vers)
        faits.append((num, de, vers))
    # L'EXHAUSTIVITE, DANS L'AUTRE SENS : tout lien local de la base est couvert.
    couverts = {}
    for num, de, _v in REBASAGES:
        couverts[(num, de)] = couverts.get((num, de), 0) + 1
    vus = {}
    for num, cible in liens_locaux(texte):
        vus[(num, cible)] = vus.get((num, cible), 0) + 1
    for cle, n in sorted(vus.items()):
        if couverts.get(cle, 0) != n:
            fautes.append("l.%d : lien local `%s` NON COUVERT par la table "
                          "(%d dans la base, %d rebasage(s))"
                          % (cle[0], cle[1], n, couverts.get(cle, 0)))
    if fautes:
        raise Echec("T ne s'applique pas — " + " · ".join(fautes))
    return "\n".join(lignes).encode("utf-8"), faits


def coupe(journal, base):
    """(en-tete, corps) du journal, coupe a SA ligne-marqueur unique."""
    lignes = journal.split(b"\n")
    idx = [i for i, l in enumerate(lignes)
           if l.startswith(MARQUEUR_TETE.encode("utf-8"))]
    if len(idx) != 1:
        raise Echec("ligne-marqueur trouvee %d fois (attendu EXACTEMENT 1)"
                    % len(idx))
    m = RE_MARQUEUR.match(lignes[idx[0]].decode("utf-8", "replace"))
    if not m:
        raise Echec("ligne-marqueur MALFORMEE l.%d : %r"
                    % (idx[0] + 1, lignes[idx[0]][:120]))
    if m.group(1) != base:
        raise Echec("la ligne-marqueur nomme la base %s, ⛔ pas %s"
                    % (m.group(1), base))
    tete = b"\n".join(lignes[:idx[0] + 1]) + b"\n"
    return tete, journal[len(tete):], idx[0] + 1


def premiere_divergence(a, b):
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n if len(a) != len(b) else None


def lit_apres(apres):
    if apres == "WORKTREE":
        chemin = os.path.join(RACINE, JOURNAL_REL)
        origine = "arbre de travail : %s" % JOURNAL_REL
    elif os.path.isfile(apres):
        chemin = apres
        origine = "fichier : %s" % apres
    elif "/" in apres or apres.endswith(".md"):
        # ⚠️ UNE VALEUR QUI A LA FORME D'UN CHEMIN ET N'EXISTE PAS EST UN JOURNAL
        #    INTROUVABLE, ⛔ pas une revision : sans cette branche, une faute de
        #    frappe tombait dans `resout_base` et sortait en `4` « revision de
        #    base absente » — le mauvais diagnostic (revue du 2026-09-13).
        raise Echec("journal introuvable : `%s` a la forme d'un chemin et "
                    "n'existe pas" % apres)
    else:
        rev = resout_base(apres)
        return contenu_a(rev, JOURNAL_REL), "revision %s : %s" % (rev,
                                                                    JOURNAL_REL)
    try:
        with open(chemin, "rb") as f:
            return f.read(), origine
    except OSError as x:
        raise Echec("journal ILLISIBLE (%s) : %s" % (origine, x))


def verifier(a):
    base = resout_base(a.avant)
    avant = contenu_a(base, AVANT_REL)
    journal, origine = lit_apres(a.apres)
    print("base   : %s" % base)
    print("avant  : README.md@%s — %s" % (base[:12], empreinte(avant)))
    print("apres  : %s — %s" % (origine, empreinte(journal)))
    attendu, faits = transforme(avant)
    print("\n── LES %d REBASAGES (chacun EXACTEMENT une fois, a sa ligne) ──"
          % len(faits))
    for num, de, vers in faits:
        print("   l.%-5d ](%s)  →  ](%s)" % (num, de, vers))
    print("   couverture : %d lien(s) local(aux) dans la base, %d rebasage(s)"
          % (len(liens_locaux(avant.decode("utf-8"))), len(faits)))
    tete, corps, l_marq = coupe(journal, base)
    print("\nen-tete : %d ligne(s) — %s" % (l_marq, empreinte(tete)))
    print("corps   : %s" % empreinte(corps))
    print("T(base) : %s" % empreinte(attendu))
    pos = premiere_divergence(attendu, corps)
    if pos is None:
        print("\nIDENTIQUE — le corps du journal est T(README@%s), octet pour "
              "octet." % base[:12])
        return 0
    ligne = attendu[:pos].count(b"\n") + 1
    print("\nDIFFERENT — premiere divergence a l'octet %d du corps (octet %d "
          "du journal), ligne %d de la base" % (pos, pos + len(tete), ligne))
    print("   attendu : %r" % attendu[max(0, pos - 20):pos + 40])
    print("   trouve  : %r" % corps[max(0, pos - 20):pos + 40])
    # ⚠️ LE REBASAGE MANQUANT EST **NOMME**, ⛔ pas seulement situe : T garde le
    #    nombre de lignes, donc la ligne `num` du corps est la ligne `num` de la
    #    base. Un lien reste ecrit depuis la racine s'y voit tel quel.
    lignes = corps.split(b"\n")
    for num, de, vers in REBASAGES:
        l = lignes[num - 1] if num <= len(lignes) else b""
        motif_de = ("](%s)" % de).encode("utf-8")
        motif_vers = ("](%s)" % vers).encode("utf-8")
        if motif_de in l and motif_vers not in l:
            print("   ⛔ REBASAGE NON APPLIQUE dans le journal : l.%d `](%s)` "
                  "y est reste (attendu `](%s)`)" % (num, de, vers))
    return 1


def ecrire(a):
    base = resout_base(a.avant)
    avant = contenu_a(base, AVANT_REL)
    tete_txt, emp_tete = dn_gates.lire(a.entete)
    if not tete_txt.endswith("\n"):
        raise Echec("l'en-tete doit finir par un retour a la ligne")
    if MARQUEUR_TETE in tete_txt:
        raise Echec("l'en-tete porte DEJA la ligne-marqueur : elle serait double")
    corps, faits = transforme(avant)
    marq = MARQUEUR_TETE + base + MARQUEUR_QUEUE + "\n"
    sortie = tete_txt.encode("utf-8") + marq.encode("utf-8") + corps
    chemin = os.path.join(RACINE, JOURNAL_REL)
    # 🔴 ⛔ JAMAIS PAR-DESSUS UN JOURNAL EXISTANT : le journal CONTINUE d'etre
    #    annote apres la scission, et reecrire le fichier detruirait ces
    #    annotations EN SILENCE (revue du 2026-09-13). `--ecrire` sert UNE fois.
    if os.path.exists(chemin):
        raise Echec("`%s` EXISTE DEJA — `--ecrire` refuse de l'ecraser : il "
                    "porterait la perte de toute annotation posee depuis la "
                    "scission. Pour la preuve, c'est `--verifier`." % JOURNAL_REL)
    with open(chemin, "wb") as f:
        f.write(sortie)
    print("ecrit : %s — %s" % (JOURNAL_REL, empreinte(sortie)))
    print("        en-tete %s (sha256[:16] %s) · %d rebasage(s) · base %s"
          % (a.entete, emp_tete, len(faits), base))
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="dn8-4 — la scission du README, prouvee octet pour octet. "
                    "⛔ Pas une gate.")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--ecrire", action="store_true",
                      help="ecrit docs/journal-de-bord.md (exige --avant, --entete)")
    mode.add_argument("--verifier", action="store_true",
                      help="compare le corps du journal a T(README@BASE)")
    ap.add_argument("--avant", required=True,
                    help="la revision de base (README.md d'avant la scission)")
    ap.add_argument("--apres", default="WORKTREE",
                    help="WORKTREE (defaut), un fichier, ou une revision git")
    ap.add_argument("--entete", help="le fichier d'en-tete (avec --ecrire)")
    a = ap.parse_args()
    if a.ecrire and not a.entete:
        ap.error("--ecrire exige --entete")
    try:
        return ecrire(a) if a.ecrire else verifier(a)
    except BaseAbsente as x:
        print("⛔ %s" % x)
        print("   ⇒ rc=4 : la preuve exige l'historique. ⛔ Aucun bilan n'est "
              "rendu sur une base qu'on ne peut pas lire.")
        return 4
    except Echec as x:
        print("⛔ ECHEC NOMME : %s" % x)
        return 1


if __name__ == "__main__":
    sys.exit(main())

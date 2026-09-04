# -*- coding: utf-8 -*-
r"""
inventaire_motif_dn53 — QUI NOMME ENCORE UNE MACHINE, ET DANS QUELLE CLASSE.

═══════════════════════════════════════════════════════════════════════════════
POURQUOI CE FICHIER EXISTE — dn5-3, revue de code du 2026-09-04
═══════════════════════════════════════════════════════════════════════════════
Les chiffres publies par `dn5-3` (CONTRIBUTING.md, l'epic, le tracker) ont ete
produits par un script JETABLE, jamais verse au depot. Mesure a la revue :
`git grep -l -F 'ce defaut nomme-t-il un profil utilisateur' HEAD --` ne trouvait
QUE sa propre sortie, dans les DEUX depots.
 ⇒ l'inventaire par classe et le controle `--csv` n'etaient **ni reproductibles
   ni falsifiables**, alors que le tableau `git grep` de `CONTRIBUTING.md`, lui,
   l'etait. Le depot pose la regle « a count without its pattern means nothing » :
   un motif qu'on peut lire mais pas REJOUER ne la satisfait qu'a moitie.
 ⇒ decision owner du 2026-09-04 : **verser l'instrument, et le reparer**.

⛔ IL EST HORS DU GLOB `tools/verif_*.py`, ET C'EST DELIBERE. `run_gates.sh`
   decouvre les gates par ce glob et les JOUE toutes. Cet outil n'est pas une
   gate : il ne rend aucun verdict sur le depot, il COMPTE. L'entrer au glob en
   ferait une gate que la CI joue, avec un `rc` a declarer dans NON_JOUABLES.

═══════════════════════════════════════════════════════════════════════════════
LES DEUX DEFAUTS DU SCRIPT JETABLE, ET CE QUI LES REMPLACE
═══════════════════════════════════════════════════════════════════════════════
(1) L'EXTRACTEUR NE LISAIT QU'UNE LIGNE. Le correctif de `dn5-3` a replie
    `ap.add_argument("--csv",` sur deux lignes ⇒ l'extracteur rendait `?`, et le
    controle repondait « ✅ NON » **sur la chaine `?`**. Capture :
    `mesures/dn5-3/T7-temoin-apres.txt`, l. 150-152.
    ⚠️ Le temoin a 5 lignes pose dessous gardait le MOTIF (on lui donnait des
    chaines litterales), ⛔ JAMAIS l'extracteur — il etait scope a la moitie du
    controle qui n'avait pas casse.
    ⇒ `defaut_argparse()` equilibre les parentheses depuis `add_argument("<opt>"`
      jusqu'a l'appel fermant. Le temoin ci-dessous le REPLANTE sur les DEUX
      formes (une ligne / deux lignes), ⛔ il ne le debranche pas (NFR7).

(2) LA DETECTION « OUVERT EN ECRITURE » MORDAIT SUR LES COMMENTAIRES. Elle a
    compte une 2e fois un commentaire que `dn5-3` venait d'ecrire, parce qu'il
    CITAIT le jeton `open(chemin, "w", ...)` en prose. Meme famille que le jeton
    d'exemption cite en commentaire, deja paye par ce depot.
    ⇒ `ouvertures_en_ecriture()` ignore les lignes dont la forme nue commence
      par `#`. Temoin : le commentaire connu ⛔ NE DOIT PAS ressortir.

═══════════════════════════════════════════════════════════════════════════════
CE QU'IL NE FAIT PAS
═══════════════════════════════════════════════════════════════════════════════
⛔ Il ne rejoue PAS le temoin a trois etages (clone deplace, `unshare -r -m`) :
   c'est une recette d'environnement, ecrite dans le dossier de `dn5-3` § « LA
   RECETTE DU TEMOIN ». Elle demande a etre jouee a la main.
⛔ Il n'ecrit rien, nulle part. Il lit et il imprime.

 EMPLOI
   python3 tools/inventaire_motif_dn53.py               # l'arbre de travail
   python3 tools/inventaire_motif_dn53.py --rev 3325c39 # un commit
   python3 tools/inventaire_motif_dn53.py --sans-temoin # ⛔ deconseille

 SORTIE : 0 si le temoin d'instrument passe, 1 s'il echoue.
   🔴 AC3.1.c APPLIQUEE A L'INSTRUMENT LUI-MEME : si le temoin ne retrouve pas
      ce qu'il sait vrai, ⛔ ON NE CONCLUT RIEN DU DEPOT. Le `rc` porte sur
      l'INSTRUMENT, ⛔ jamais sur les chiffres.
"""

import argparse
import os
import re
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── LE MOTIF, ECRIT UNE FOIS ────────────────────────────────────────────────
# ⛔ UN COMPTE SANS SON MOTIF NE VEUT RIEN DIRE. Celui-ci est le motif retenu par
#    `dn5-3` ; ⛔ ce n'est PAS le seul possible, et c'est pour ca qu'il s'imprime.
MOTIF = r"nasbarok|naoua|~/projects|wsl\.localhost"

# ── LA CLASSE 5 EST UNE EXCLUSION **DECLAREE**, ⛔ JAMAIS SILENCIEUSE ────────
# AC3.4.b : compter le motif dans une page qui PARLE du motif, c'est mesurer sa
# propre prose. Chacun de ces fichiers porte le motif parce qu'il l'ENONCE.
# ⚠️ CE FICHIER-CI EN FAIT PARTIE, et c'est le premier a le declarer : il ecrit
#    le motif l. 62. Un instrument qui s'oublie lui-meme se compte comme defaut.
CLASSE5 = {
    ".github/workflows/cla.yml":
        "un LOGIN GitHub dans l'URL du CLA — le retirer CASSE le bot",
    "docs/dn5-1-ecart-promesses.md":
        "la page qui DOCUMENTE l'ecart — la censurer rendrait le releve illisible",
    "CONTRIBUTING.md":
        "la page qui ENONCE le motif et publie ses comptes (le `git grep`, la"
        " phrase sur le motif seul, la declaration des exclusions)",
    "tools/inventaire_motif_dn53.py":
        "CET INSTRUMENT — il ecrit le motif pour pouvoir le chercher",
}

# ── LA CLASSE 1 EST **CONTROLEE**, ⛔ pas declaree d'autorite ────────────────
# Chaque entree porte le controle qui dit si la dependance FONCTIONNELLE est
# encore la. Rejouable : replanter la faute fait remonter le fichier en classe 1.
CLASSE1 = ["tools/verif_dossier_d5_dn45.py",
           "tools/bench_lisseur_dn45.py",
           "tools/thermique_ventilos_dn48.py"]

RE_PROFIL = re.compile(r"[A-Za-z]:\\Users\\")
RE_RACINE_ABS = re.compile(r"""["']/home/[A-Za-z0-9._-]+/""")
RE_UNC = re.compile(r"\\\\wsl\.localhost\\", re.I)


# ══ LECTURE DE L'ARBRE ══════════════════════════════════════════════════════

def _git(args):
    r = subprocess.run(["git", "-C", RACINE] + args,
                       capture_output=True, text=True)
    return r.stdout


def fichiers(rev):
    """Les fichiers de l'arbre. `rev=None` ⇒ l'ARBRE DE TRAVAIL.

    ⚠️ `--cached --others --exclude-standard` rend exactement ce que `HEAD`
       portera apres `git add -A` : c'est ce qu'un relecteur veut voir AVANT
       que le commit existe. ⛔ Un compte pris sur `HEAD` seul ignore le travail
       en cours, et c'est precisement comme ca que `dn5-3` a publie un chiffre
       que son propre arbre refutait.
    """
    if rev:
        return [l for l in _git(["ls-tree", "-r", "--name-only", rev]).split("\n") if l]
    vus, out = set(), []
    for l in _git(["ls-files", "--cached", "--others", "--exclude-standard"]).split("\n"):
        if l and l not in vus:
            vus.add(l)
            out.append(l)
    return out


def contenu(rev, rel):
    if rev:
        r = subprocess.run(["git", "-C", RACINE, "show", "%s:%s" % (rev, rel)],
                           capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else None
    p = os.path.join(RACINE, rel)
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except (OSError, UnicodeError):
        return None


def sites(txt):
    """Nombre de LIGNES portant le motif. ⛔ pas le nombre d'occurrences."""
    rx = re.compile(MOTIF)
    return sum(1 for l in txt.split("\n") if rx.search(l))


# ══ LES DEUX CONTROLES REPARES ══════════════════════════════════════════════

def defaut_argparse(txt, option):
    """Le `default=` d'une option argparse, **peu importe le nombre de lignes**.

    🔴 C'EST LE CORRECTIF (1). L'ancien instrument lisait la ligne du
       `add_argument` et rien d'autre : replier l'appel le rendait aveugle, et
       il repondait quand meme.
    ⇒ rend la chaine du defaut, ou None si l'option n'est pas declaree.
      ⛔ Il ne rend JAMAIS un jeton bouchon comme `?` : l'absence se dit None,
      et l'appelant DOIT la traiter.
    """
    depart = txt.find('add_argument("%s"' % option)
    if depart < 0:
        depart = txt.find("add_argument('%s'" % option)
    if depart < 0:
        return None
    i = txt.find("(", depart)
    prof, j, n = 0, i, len(txt)
    while j < n:
        c = txt[j]
        if c in "\"'":
            q = c
            j += 1
            while j < n and txt[j] != q:
                j += 2 if txt[j] == "\\" else 1
        elif c == "(":
            prof += 1
        elif c == ")":
            prof -= 1
            if prof == 0:
                break
        j += 1
    appel = txt[i:j + 1]
    m = re.search(r"default\s*=\s*(r?)(['\"])(.*?)\2", appel, re.S)
    if m:
        return m.group(3)
    m = re.search(r"default\s*=\s*([A-Za-z_][\w.]*\s*\([^)]*\)|[A-Za-z_][\w.]*)",
                  appel, re.S)
    return ("⟨calcule⟩ " + " ".join(m.group(1).split())) if m else ""


def ouvertures_en_ecriture(txt):
    """Les lignes qui OUVRENT vraiment un chemin en ecriture.

    🔴 C'EST LE CORRECTIF (2). Une ligne de COMMENTAIRE qui cite `open(x, "w")`
       n'ouvre rien. L'ancien instrument la comptait, et publiait donc deux fois
       la meme conclusion — la seconde sur une prose que `dn5-3` venait d'ecrire.
    """
    out = []
    for i, l in enumerate(txt.split("\n"), 1):
        nu = l.strip()
        if nu.startswith("#"):
            continue
        if re.search(r'\bopen\(\s*[A-Za-z_][\w.]*\s*,\s*["\']w', l):
            out.append((i, nu))
    return out


def dependance_fonctionnelle(rel, txt):
    """Le fichier depend-il ENCORE d'une machine en particulier ? (motif, ⛔ pas
    un `fichier:ligne`). Rend une liste de motifs constates — vide = solde."""
    faits = []
    if rel == "tools/thermique_ventilos_dn48.py":
        d = defaut_argparse(txt, "--csv")
        if d is None:
            faits.append("l'option --csv a DISPARU — ⛔ le controle ne dit plus rien")
        elif RE_PROFIL.search(d) or RE_RACINE_ABS.search('"%s"' % d):
            faits.append("defaut --csv = un profil utilisateur : %s" % d)
    if rel == "tools/bench_lisseur_dn45.py":
        for l in txt.split("\n"):
            if "sys.path.insert" in l and ("__file__" not in l):
                if RE_UNC.search(l) or RE_RACINE_ABS.search(l):
                    faits.append("sys.path.insert vers un chemin ecrit en dur")
    if rel == "tools/verif_dossier_d5_dn45.py":
        for i, l in enumerate(txt.split("\n"), 1):
            if l.strip().startswith("#"):
                continue
            if RE_RACINE_ABS.search(l):
                faits.append("racine ABSOLUE en dur, l.%d" % i)
    return faits


# ══ LE TEMOIN DE L'INSTRUMENT — il REPLANTE, ⛔ il ne debranche pas ═════════

def temoin():
    """AC3.1.c appliquee a l'instrument. ⛔ Rien ne se conclut s'il echoue.

    Chaque cas REPLANTE une faute connue dans un texte, et exige que le controle
    la VOIE. ⛔ Aucun cas ne retire une garde pour la voir disparaitre : un
    mutant qui debranche ne prouve que l'existence de la garde.
    """
    cas = []

    # (a) L'EXTRACTEUR, SUR LES DEUX FORMES. C'est le defaut mesure : la forme
    #     repliee rendait `?`, et le controle repondait « NON » dessus.
    une_ligne = 'ap.add_argument("--csv", default=r"C:\\Users\\quiconque\\T\\x.csv")\n'
    repliee = ('ap.add_argument("--csv",\n'
               '                default=r"C:\\Users\\quiconque\\T\\x.csv")\n')
    calculee = ('ap.add_argument("--csv",\n'
                '                default=os.path.join(tempfile.gettempdir(),\n'
                '                                     "dn48_thermique.csv"))\n')
    for nom, src, attendu in (
            ("defaut sur UNE ligne          ", une_ligne, True),
            ("defaut REPLIE sur deux lignes ", repliee, True),
            ("defaut CALCULE, replie        ", calculee, False)):
        d = defaut_argparse(src, "--csv")
        vu = d is not None and bool(RE_PROFIL.search(d))
        cas.append(("extracteur : %s" % nom, attendu, vu, repr(d)[:46]))
    cas.append(("extracteur : option ABSENTE ⇒ None, ⛔ pas un jeton bouchon",
                True, defaut_argparse("ap.add_argument('--autre')", "--csv") is None,
                "None"))

    # (b) LA DETECTION D'ECRITURE, ET LE TEMOIN **NEGATIF** QUI MANQUAIT.
    reel = 'with open(chemin, "w", newline="") as f:\n'
    cite = '#    (`open(chemin, "w", ...)`) ⇒ sur la machine de quelqu\'un d\'autre,\n'
    cas.append(("ecriture : une vraie ouverture est VUE", True,
                len(ouvertures_en_ecriture(reel)) == 1, "1 site"))
    cas.append(("ecriture : la MEME citee en COMMENTAIRE ⛔ n'est PAS vue", True,
                len(ouvertures_en_ecriture(cite)) == 0, "0 site"))
    cas.append(("ecriture : les deux ensemble ⇒ UN seul site", True,
                len(ouvertures_en_ecriture(reel + cite)) == 1, "1 site"))

    # (c) LA CLASSE 1 REMONTE QUAND ON REPLANTE LA FAUTE.
    sain = contenu(None, "tools/thermique_ventilos_dn48.py") or ""
    malade = sain.replace('default=os.path.join(tempfile.gettempdir(), "dn48_thermique.csv")',
                          'default=r"C:\\Users\\quiconque\\AppData\\Local\\Temp\\x.csv"')
    cas.append(("classe 1 : l'arbre du jour est SOLDE", True,
                dependance_fonctionnelle("tools/thermique_ventilos_dn48.py", sain) == [],
                "0 fait"))
    cas.append(("classe 1 : faute REPLANTEE ⇒ elle REMONTE", True,
                (malade != sain
                 and dependance_fonctionnelle("tools/thermique_ventilos_dn48.py",
                                              malade) != []),
                "≥1 fait"))
    return cas


# ══ SORTIE ══════════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--rev", default=None,
                    help="commit a mesurer ; par defaut l'ARBRE DE TRAVAIL")
    ap.add_argument("--sans-temoin", action="store_true")
    a = ap.parse_args()

    print("=" * 78)
    print("dn5-3 — INVENTAIRE PAR CLASSE DU MOTIF « machine nommee »")
    print("=" * 78)
    print("arbre mesure : %s" % (a.rev if a.rev else
                                 "ARBRE DE TRAVAIL (git ls-files --cached --others)"))
    print("motif        : %s" % MOTIF)
    print("⛔ un compte sans son motif ne veut rien dire — et un AUTRE motif rend")
    print("   un AUTRE compte. Dire lequel fait partie du chiffre.")

    rc = 0
    if not a.sans_temoin:
        print("\n── 0. TEMOIN DE L'INSTRUMENT — ⛔ AVANT TOUT CHIFFRE ──────────────")
        print("   🔴 AC3.1.c : s'il echoue, ⛔ ON NE CONCLUT RIEN DU DEPOT.")
        for nom, attendu, vu, detail in temoin():
            ok = (attendu == vu)
            rc |= 0 if ok else 1
            print("  [%s] %-56s %s" % ("OK " if ok else "KO ", nom, detail))
        if rc:
            print("\n⛔ LE TEMOIN A ECHOUE — les chiffres ci-dessous ne valent RIEN.")

    tous = fichiers(a.rev)
    cl = {1: [], 2: [], 3: [], 4: [], 5: []}
    rx = re.compile(MOTIF)
    for rel in sorted(tous):
        txt = contenu(a.rev, rel)
        if txt is None or not rx.search(txt):
            continue
        n = sites(txt)
        if rel in CLASSE5:
            cl[5].append((rel, n))
        elif rel.startswith("mesures/"):
            cl[4].append((rel, n))
        elif re.match(r"firmware/.*/fonts/dn_font_.*\.c$", rel):
            cl[3].append((rel, n))
        elif rel in CLASSE1 and dependance_fonctionnelle(rel, txt):
            cl[1].append((rel, n))
        else:
            cl[2].append((rel, n))

    titres = {1: "dependance FONCTIONNELLE  (le seul defaut)",
              2: "exemple d'usage          (declare au site)",
              3: "trace de generation      (polices — INTACTES)",
              4: "registre de preuves      (mesures/ — INTACT)",
              5: "le motif est le SUJET    (EXCLUSION DECLAREE)"}
    print("\n── 1. LES CINQ CLASSES ───────────────────────────────────────────")
    tf = ts = 0
    for k in (1, 2, 3, 4, 5):
        f, s = len(cl[k]), sum(n for _, n in cl[k])
        tf, ts = tf + f, ts + s
        print("  %d. %-44s %4d fichiers %6d sites" % (k, titres[k], f, s))
    print("  %-47s %4d fichiers %6d sites" % ("     TOTAL", tf, ts))

    print("\n── 2. LA CLASSE 1, CONTROLEE ⛔ PAS DECLAREE D'AUTORITE ───────────")
    for rel in CLASSE1:
        txt = contenu(a.rev, rel)
        faits = dependance_fonctionnelle(rel, txt) if txt is not None else ["ABSENT"]
        print("  [%s] %-46s %s" % ("KO " if faits else "OK ", rel,
                                   " · ".join(faits) if faits else "solde"))

    print("\n── 3. LES EXCLUSIONS, ECRITES ⛔ PAS SILENCIEUSES ─────────────────")
    for rel, motif in sorted(CLASSE5.items()):
        n = dict(cl[5]).get(rel)
        print("  %-42s %s site(s)" % (rel, n if n is not None else "0 (absent)"))
        print("      %s" % motif)

    print("\n── 4. LE CONTROLE `--csv`, AVEC CE QU'IL A VRAIMENT LU ────────────")
    rel = "tools/thermique_ventilos_dn48.py"
    txt = contenu(a.rev, rel) or ""
    d = defaut_argparse(txt, "--csv")
    print("  defaut lu : %s" % ("⛔ OPTION ABSENTE" if d is None else repr(d)))
    print("  ⇒ nomme-t-il un profil utilisateur ? %s"
          % ("⛔ INDECIDABLE (rien lu)" if d is None
             else ("🔴 OUI" if RE_PROFIL.search(d) else "✅ NON")))
    ouv = ouvertures_en_ecriture(txt)
    print("  ouvertures en ECRITURE (⛔ commentaires exclus) : %d" % len(ouv))
    for i, l in ouv:
        print("      l.%-5d %s" % (i, l[:58]))

    print("\n── 5. CE QUE CE COMPTE NE DIT PAS ────────────────────────────────")
    print("  ⛔ Il BOUGE des qu'une declaration ou une capture s'ajoute — et une")
    print("     declaration est precisement ce que ce depot demande. Ce qui est")
    print("     STABLE, c'est la classe 1 : plus aucun outil ne depend d'une")
    print("     machine en particulier.")
    print("  ⛔ Il ne voit PAS une LETTRE DE LECTEUR (`H:\\...`) : le motif ne la")
    print("     porte pas. Site connu : `tools/rendre-port.sh`, declare au site.")
    print("=" * 78)
    return rc


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-23 / AC8 — LES INSTRUMENTS DISENT QUAND ILS MENTENT, ET C'EST GARDÉ.
Jouable depuis WSL, ⛔ SANS CARTE.

======================= CE QUE CET OUTIL FAIT ==============================

Il garde les DEUX ÉTAGES de la chaîne, parce que le défaut est de FAMILLE et
qu'il vit sur les deux :

  · **l'hôte** (`tools/dn_console.py`, `tools/dn_injecteur.py`) — le pilote ne
    lisait NI le refus NI la perte de lignes ; deux fenêtres de 90 s ont rendu
    **0** sur un stimulus qui n'a JAMAIS tourné ;
  · **la carte** (`firmware/desknode/main/dn_console.c`) — la commande RÉCITAIT
    au lieu de RELIRE (`6 × 35 100 px` sur une aire de 36 675), ou BLOQUAIT ce
    qu'elle mesure (`cpu N` publiait 0,8 % sous trafic contre 0,9 % au repos).

⇒ **Les deux se gardent ensemble ou pas du tout** : un compteur de lignes
  imprimé par la carte ne sert à rien si le pilote ne le lit pas, et
  réciproquement. Le contrôle du MIROIR (`bloc_miroir`) est celui-là.

============ LES QUATRE RÈGLES QUE CETTE GATE S'APPLIQUE À ELLE-MÊME =========

(1) 🔴 **CHAQUE CONTRÔLE DOIT POUVOIR ROUGIR.** La question posée de chaque
    ligne est *« qu'est-ce qui la ferait rougir ? »*. Si rien, elle ne compte
    pas. ⛔ Un `N OK / 0 KO` peut épingler du code FAUX — mesuré **trois fois**
    sur cette base de code. Les mutants sont au PV : `mesures/dn4-23/T8-mutants.txt`.

(2) ⛔ **NE PAS CODER EN DUR CE QUI SE GARDE GÉNÉRIQUEMENT.** `dn4-16` a payé
    exactement ça : une gate qui exigeait SA propre clé rendait « SANS
    DISPOSITION » sur la première entrée d'un autre auteur — un rouge au
    diagnostic FAUX. Ici les bornes de `k_metriques[]` sont **RELUES** de
    `dn_link.c`, le format du compteur est **EXTRAIT** du `printf` du firmware,
    et la règle du `35 100` est une **forme** (« etait 35 100 a … »), ⛔ pas une
    liste de lignes.

(3) ⛔ **NE PAS COMPARER UN TOTAL.** Un contrôle qui teste `count(motif) == 3`
    est satisfait par une ligne fabriquée n'importe où. Ici tout se **localise**
    dans une FONCTION ou dans une BRANCHE (`corps_fonction`, `branche_argv1`),
    et le mutant le démontre.

(4) ⛔ **`grep -c` sort en 1 quand le compte est 0** — d'où le Python pur, sans
    dépendance.

Sortie : `[OK ]` / `[KO ]`, `BILAN : n OK, m KO`, rc 0 / 1.
Option : `--racine <chemin>` — joue la gate sur un ARBRE MUTÉ (c'est ainsi que
le PV des mutants est produit). Défaut : le dépôt qui la contient.
"""

import argparse
import os
import re
import subprocess
import sys

OK = [0]
KO = [0]

# dn4-40 / AC40.6.b — CE QUE CHAQUE EXTRACTION A REELLEMENT VU.
# (signature, occurrences_dans_la_source, corps_trouve)
extractions = []


def ctrl(bon, libelle, detail=""):
    if bon:
        OK[0] += 1
        print("  [OK ] %-58s %s" % (libelle, detail))
    else:
        KO[0] += 1
        print("  [KO ] %-58s %s" % (libelle, detail))
    return bon


def lire(chemin):
    # 🔴 REVUE DU 2026-08-31 — `except OSError` NE COUVRAIT PAS L'ENCODAGE.
    #    `open(..., encoding="utf-8")` lève `UnicodeDecodeError`, qui est une
    #    `ValueError` : sur une source en latin-1 ou portant un octet mojibake,
    #    l'exception ÉCHAPPAIT ⇒ le chemin ci-dessous — écrit précisément pour
    #    que « un contrôle qui ne peut pas LIRE ne dise PAS rien à signaler » —
    #    n'était JAMAIS atteint, et il n'y avait NI `[KO]` NI `BILAN`. Sous
    #    `--mutants`, ce même plantage était rapporté `[VERT!] CE CONTRÔLE NE
    #    GARDE RIEN` : un faux diagnostic SUR UN CRASH. Ce dépôt imprime de
    #    l'accentué partout — le cas n'a rien de théorique.
    try:
        with open(chemin, encoding="utf-8") as f:
            return f.read()
    except (OSError, ValueError) as e:
        # ⛔ Un contrôle qui ne peut pas LIRE ne dit PAS « rien à signaler ».
        print("  [KO ] fichier ILLISIBLE : %s" % chemin)
        print("        %s" % e)
        KO[0] += 1
        return None


# ── LOCALISATION : ⛔ on ne cherche JAMAIS dans le fichier entier ────────────
def _hors_litteral(src, depart):
    """Parcourt du C en SAUTANT chaines, caracteres et commentaires.

    🔴 dn4-40 / AC40.6 — CE QUE CE PARCOURS REPARE. `corps_fonction()`
    comptait les accolades NAIVEMENT et le declarait : « il suffit ici parce
    qu'aucune de ces fonctions ne porte d'accolade dans une chaine ». C'etait
    vrai le jour ou c'etait ecrit — ⛔ ce n'est pas un invariant. Une accolade
    ajoutee dans un `printf` d'une des fonctions visees DEPLACE le corps
    extrait, et TOUS les controles qui lisent ce corps changent de sujet SANS
    QUE RIEN NE LE DISE.

    ⚠️ CE N'EST PAS UN PARSEUR C. Il ne connait ⛔ ni le preprocesseur ⛔ ni
    les trigraphes ⛔ ni les chaines brutes (il n'y en a pas en C). Ce qu'il
    fait est ce dont l'extraction a besoin, et rien de plus : ne jamais
    prendre pour du CODE une accolade qui vit dans un LITTERAL.

    Rend un iterateur de `(index, caractere)` sur le code SEUL.
    """
    k = len(src)
    i = depart
    while i < k:
        c = src[i]
        if c == "/" and i + 1 < k and src[i + 1] == "/":
            j = src.find("\n", i)
            i = k if j < 0 else j
            continue
        if c == "/" and i + 1 < k and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            i = k if j < 0 else j + 2
            continue
        if c in "\"'":
            q = c
            i += 1
            while i < k:
                if src[i] == "\\":
                    i += 2
                    continue
                if src[i] == q:
                    i += 1
                    break
                if src[i] == "\n" and q == "'":
                    break          # ⛔ un `'` isole (apostrophe) ⛔ n'ouvre rien
                i += 1
            continue
        yield i, c
        i += 1


def corps_fonction(src, signature):
    """Le corps `{ … }` de la fonction dont la SIGNATURE est donnee (le texte
    exact qui precede l'accolade ouvrante).

    🔴 dn4-40 / AC40.6.a — LES ACCOLADES DES LITTERAUX SONT IGNOREES. Le
    comptage etait NAIF et s'en justifiait par un fait DATE (« aucune de ces
    fonctions ne porte d'accolade dans une chaine »), ⛔ pas par un invariant.

    ⚠️ AC40.6.b — CE QUE CETTE FONCTION PROUVE, ET CE QU'ELLE NE PROUVE PAS.
    Rendre un corps prouve QU'UNE fermeture a profondeur 0 a ete trouvee.
    ⛔ Ca ne prouve PAS que c'etait LA BONNE : si la signature est le PREFIXE
    d'une autre signature, `find()` peut tomber sur la mauvaise fonction et
    rendre un corps parfaitement equilibre — celui de quelqu'un d'autre.
    ⇒ Le controle d'unicite ci-dessous existe pour ca ; le libelle ne dit plus
      « le corps se referme » comme si ca suffisait.
    """
    n = src.count(signature)
    extractions.append((signature, n))
    i = src.find(signature)
    if i < 0:
        return None
    j = -1
    for idx, c in _hors_litteral(src, i):
        if c == "{":
            j = idx
            break
    if j < 0:
        return None
    prof = 0
    for idx, c in _hors_litteral(src, j):
        if c == "{":
            prof += 1
        elif c == "}":
            prof -= 1
            if prof == 0:
                return src[j:idx + 1]
    return None


def signature_ambigue(src, signature):
    """La signature designe-t-elle UNE fonction, ou plusieurs ?

    🔴 dn4-40 / AC40.6.b — LE CONTROLE QUI MANQUAIT. Une signature qui
    apparait deux fois, ou qui est le PREFIXE d'une autre signature du meme
    fichier, fait extraire un corps ARBITRAIREMENT (`str.find` prend le
    premier). Le corps se refermait quand meme ⇒ la gate se declarait
    satisfaite en lisant la MAUVAISE fonction.
    ⚠️ MESURE DU 2026-09-02 : 21 appels, 15 signatures LITTERALES, 14
    DISTINCTES, et 1 signature qui est le prefixe d'une autre. ⛔ Compter les
    signatures, ⛔ pas recopier un chiffre : le ledger en annoncait 15.
    """
    n = src.count(signature)
    return n if n != 1 else 0


def corps_python(src, signature):
    """Le corps d'une fonction PYTHON, par INDENTATION.

    🔴 PREMIÈRE RÉDACTION FAUSSE, ET ELLE A ÉTÉ VUE ROUGIR : cette gate
       appliquait `corps_fonction()` (comptage d'ACCOLADES, écrit pour le C) à
       `dn_console.py`. Sur du Python, la première `{` rencontrée est un dict —
       le « corps » extrait était donc un littéral, et **onze contrôles
       rougissaient sur du code JUSTE**. ⛔ C'est « une gate `N OK / 0 KO` peut
       épingler du code FAUX », dans l'autre sens : un ROUGE au diagnostic FAUX.
    """
    m = re.search(r"^" + re.escape(signature), src, re.M)
    if not m:
        return None
    lignes = src[m.start():].split("\n")
    out = [lignes[0]]
    for l in lignes[1:]:
        if l.strip() and not l.startswith((" ", "\t")):
            break
        out.append(l)
    return "\n".join(out)


def printfs(src):
    """Les LITTÉRAUX que le firmware IMPRIME — ⛔ pas ses commentaires.

    🔴 MOTIF PAYÉ PAR CE DÉPÔT : *« le jeton d'exemption d'une gate n'a aucun
       échappement — le citer dans un commentaire l'accorde »*. Le symétrique
       est vrai : un contrôle qui cherche dans le fichier entier ROUGIT sur le
       commentaire qui EXPLIQUE le correctif. Vu ici sur `dn3-3` : le message
       est retiré, et le commentaire qui dit pourquoi le nommait encore.

    🔴 **CORRIGÉE DEUX FOIS PAR LA REVUE DU 2026-08-31, ET LES DEUX DÉFAUTS
       RENDAIENT LA GATE VERTE SUR LE DÉFAUT QU'ELLE NOMME.**
      (a) **LE DOCSTRING MENTAIT.** L'ancienne regex cherchait `printf("…` dans
          le fichier ENTIER, commentaires COMPRIS — l'exclusion annoncée était
          ACCIDENTELLE. Et `sans_commentaires_c()`, la fonction qui l'aurait
          faite, était du **CODE MORT** : une seule occurrence dans le fichier,
          sa propre définition. ⇒ elle est APPELÉE.
      (b) **ELLE NE CAPTURAIT QUE LE PREMIER LITTÉRAL DE CHAQUE `printf`.** Or
          le multi-littéral (`printf("a\\n" "b\\n")`) est le style DOMINANT de
          `dn_console.c`. Reproduit : réinsérer une aire récitée dans un
          littéral de continuation de `widget rafale` laissait
          `[OK] aucune AIRE RÉCITÉE … fautifs : aucun` et `107 OK / 0 KO`.
          ⇒ on concatène TOUS les littéraux adjacents d'un même appel.
    """
    src = sans_commentaires_c(src)
    out = []
    for m in re.finditer(r'printf\(\s*((?:"(?:[^"\\]|\\.)*"\s*)+)', src):
        morceaux = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))
        out.append("".join(morceaux))
    return out


def branches_argv1(src, fonction_sig, mot):
    """TOUTES les branches `strcmp(argv[1], "<mot>")` d'une fonction, avec leur
    garde. Rend une liste de `(tete, corps)`.

    🔴 AJOUTÉE PAR LA REVUE DU 2026-08-31. `branche_argv1()` rend LA PREMIÈRE
       qui matche, et `dn_console.c` porte **quatre** branches `largeur`
       (`mur`, `reset`, et deux qui mesurent une chaîne libre). Un contrôle qui
       prend la première épingle donc une branche AU HASARD — c'est la famille
       « gate scopée à UNE fonction épingle vert le même défaut ailleurs »,
       appliquée un cran plus bas.
    """
    corps = corps_fonction(src, fonction_sig)
    if corps is None:
        return []
    out = []
    motif = r'strcmp\(argv\[1\],\s*"%s"\)\s*==\s*0' % re.escape(mot)
    for m in re.finditer(motif, corps):
        deb = corps.rfind("if (", 0, m.start())
        j = corps.find("{", m.end())
        if j < 0:
            continue
        # ⛔ LA GARDE VA JUSQU'A L'ACCOLADE : `strcmp(argv[2], "mur")` vit APRES
        #   le `strcmp(argv[1], ...)`, donc une tete coupee a `m.end()` ne voyait
        #   pas le mot-cle et rendait les 4 branches « libres ». Attrape par le
        #   controle qui suit — un localisateur trop court est un localisateur
        #   faux.
        tete = corps[deb:j]
        prof, k = 0, j
        while k < len(corps):
            if corps[k] == "{":
                prof += 1
            elif corps[k] == "}":
                prof -= 1
                if prof == 0:
                    out.append((tete, corps[j:k + 1]))
                    break
            k += 1
    return out


def branche_argv1(src, fonction_sig, mot, argc=None):
    """Le corps d'une branche `if (… strcmp(argv[1], "<mot>") == 0)` DANS une
    fonction donnée. C'est l'unité de localisation des sous-commandes : sans
    elle, un contrôle sur `widget piste` serait satisfait par n'importe quelle
    autre branche du même fichier de 11 000 lignes."""
    corps = corps_fonction(src, fonction_sig)
    if corps is None:
        return None
    motif = r'strcmp\(argv\[1\],\s*"%s"\)\s*==\s*0' % re.escape(mot)
    for m in re.finditer(motif, corps):
        if argc is not None:
            # remonter au `if (` de la branche pour lire sa garde d'argc
            deb = corps.rfind("if (", 0, m.start())
            tete = corps[deb:m.start()]
            if ("argc == %d" % argc) not in tete and \
               ("argc >= %d" % argc) not in tete:
                continue
        j = corps.find("{", m.end())
        if j < 0:
            continue
        prof, k = 0, j
        while k < len(corps):
            if corps[k] == "{":
                prof += 1
            elif corps[k] == "}":
                prof -= 1
                if prof == 0:
                    return corps[j:k + 1]
            k += 1
    return None


def sans_commentaires_py(src):
    """Le code Python SANS ses commentaires ni ses docstrings.

    🔴 **QUATRIEME OCCURRENCE DE LA MEME FAMILLE DANS CE DEPOT, ET ELLE S'EST
       PRODUITE PENDANT LA REVUE QUI LA NOMME.** Le controle « `--no-wait` ne
       plafonne plus sa lecture a 2 s » cherchait le motif fautif dans le corps
       de `envoyer()` — et il a rougi sur le **commentaire qui EXPLIQUE le
       correctif**, lequel cite forcement ce motif. Les trois precedentes : le
       jeton d'exemption du verrou LVGL cite dans un commentaire l'ACCORDAIT
       (`dn4-24`) · une gate codant en dur la cle de sa story ne gardait pas le
       format qu'elle installe (`dn4-16`) · parler d'un motif comptait comme une
       occurrence (`dn4-24`).
    ⇒ La parade n'est pas d'interdire d'expliquer : c'est de donner a la gate
      un **echappement**, comme un langage donne le sien. Ici : on lit LE CODE.
    ⚠️ Decoupage LEXICAL simple — il suffit pour le Python de ce depot, et ⛔ ce
       n'est pas presente comme un analyseur complet.
    """
    src = re.sub(r'"""' + "(?:.|\n)*?" + '"""', " ", src)
    src = re.sub(r"'''" + "(?:.|\n)*?" + "'''", " ", src)
    src = re.sub(r"(?m)^\s*#[^\n]*$", " ", src)
    src = re.sub(r"(?m)(\s)#[^\n]*$", r"\1", src)
    return src


def sans_commentaires_c(src):
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    src = re.sub(r"//[^\n]*", " ", src)
    return src


def joue(argv, cwd):
    """Joue un témoin en SOUS-PROCESSUS et rend (rc, sortie)."""
    try:
        p = subprocess.run([sys.executable] + argv, cwd=cwd,
                           capture_output=True, text=True, timeout=300)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:      # noqa: BLE001 — on veut le MOTIF, pas le type
        return 99, "exception : %s" % e


# ═══════════════════════════════════════════════════════════════════════════
def bloc_refus(py):
    """AC1 — LE REFUS EST LU, ET IL ARME LE CODE DE RETOUR."""
    print("\n── AC1 : un harnais qui pose une commande LIT LE REFUS ─────────")
    tbl = re.search(r"MOTIFS_REFUS\s*=\s*\((.*?)\n\)", py, re.S)
    ctrl(tbl is not None, "`MOTIFS_REFUS` est une table LOCALISABLE",
         "⛔ pas des `in` dispersés")
    corps = tbl.group(1) if tbl else ""
    # 🔴 REVUE DU 2026-08-31 — CES CONTRÔLES ÉTAIENT DES TESTS DE SOUS-CHAÎNE, ET
    #    ILS NE DISTINGUAIENT PAS UNE REGEX D'UNE PROSE. `"ESP_ERR_"` était
    #    satisfait par le LIBELLÉ du tuple, pas par le motif. Reproduit : typo la
    #    regex en `Commmand returned non-zero error code` ⇒ `[OK] …et elle porte
    #    « non-zero error code »`, et le témoin du pilote restait `31 OK / 0 KO`
    #    (les deux témoins REPL portaient `ESP_ERR_`, qui tirait EN PREMIER).
    # ⇒ ON COMPILE LES MOTIFS ET ON LES FAIT MORDRE SUR UNE LIGNE FABRIQUÉE.
    # ⚠️ ET L'EXTRACTEUR CONCATÈNE LES LITTÉRAUX ADJACENTS — même leçon que
    #    `printfs()` : un motif écrit sur deux lignes (`r"a" r"|b"`) était
    #    INVISIBLE à un extracteur qui n'en lit qu'un, donc NON ÉPROUVÉ. La
    #    gate l'a attrapé sur elle-même en posant l'épreuve ci-dessous.
    motifs = ["".join(re.findall(r'r"((?:[^"\\]|\\.)*)"', m.group(1)))
              for m in re.finditer(
                  r're\.compile\(((?:\s*r"(?:[^"\\]|\\.)*"\s*)+)\)', corps)]
    ctrl(len(motifs) >= 5, "…et elle porte au moins 5 motifs COMPILABLES",
         "%d trouvé(s)" % len(motifs))
    epreuves = [
        ("Unrecognized command", "REPL — commande inconnue"),
        ("Command returned non-zero error code: 0x1 (ERROR)",
         "REPL — `return 1` NU, ⛔ sans ESP_ERR_"),
        ("Internal error: la console n'a pas pu executer",
         "REPL — erreur interne, ⛔ sans ESP_ERR_"),
        ("refusé : ESP_ERR_INVALID_ARG", "notre convention"),
        ("⛔ NE PAS CONCLURE SUR CE CHIFFRE.", "la carte se désavoue"),
    ]
    compiles = []
    for src in motifs:
        try:
            compiles.append(re.compile(src))
        except re.error:
            pass
    ctrl(len(compiles) == len(motifs), "…et TOUS compilent", "⛔ aucune régression")
    for ligne, quoi in epreuves:
        ctrl(any(rx.search(ligne) for rx in compiles),
             "🔴 un motif MORD sur « %s »" % ligne[:34], quoi)
    # ⛔ ET LA CONTRE-ÉPREUVE : la phrase pédagogique NE doit PAS mordre.
    vert = "usage : widget opa <0..255>  (refuse hors bornes, jamais ecrete)"
    ctrl(not any(rx.search(vert) for rx in compiles),
         "…et AUCUN ne mord sur la phrase pédagogique de `widget opa`",
         "⛔ « refuse » SANS « : » n'est pas un refus")

    # ══ REVUE DU 2026-08-31 — CE QUE RIEN NE GARDAIT ═══════════════════════
    # ⛔ LU DANS LE CODE, ⛔ PAS DANS LA PROSE : le commentaire qui explique ce
    #   correctif CITE le motif fautif, et ce contrôle a rougi dessus — 4e
    #   occurrence de cette famille dans le dépôt (voir `sans_commentaires_py`).
    env = sans_commentaires_py(corps_python(py, "def envoyer(") or "")
    ctrl("nettoyer(brut, commande), None)" in env,
         "🔴 `--no-wait` retire l'ÉCHO avant de chercher un refus",
         "⛔ sinon la commande se dénonce elle-même")
    ctrl("min(timeout, 2.0)" not in env,
         "🔴 …et il lit sur TOUTE la fenêtre, ⛔ pas 2 s en dur",
         "un refus à t=2,5 s rendait 0")
    ctrl("while time.monotonic() < fin:" in env,
         "…en DRAINANT au fil de l'eau", "⛔ pas un `sleep` aveugle")
    cd_ = corps_python(py, "def completude(") or ""
    ctrl("SOMME SIGNÉE PAR CAPTURE" in cd_,
         "…et l'ANGLE MORT de l'invariant est ÉCRIT là où il se produit",
         "perte + étrangère = OK")
    ic = corps_python(py, "def imprimer_completude(") or ""
    ctrl("s'annulent" in ic,
         "…et IMPRIMÉ sur un compteur `OK`",
         "⛔ un commentaire ne retient personne")
    rt = corps_python(py, "def refus_tolere(") or ""
    ctrl("_MOTIFS_JAMAIS_TOLERES" in rt,
         "…et DEUX motifs ne se tolèrent JAMAIS",
         "commande inconnue · erreur interne")

    res = corps_python(py, "def _resultat(")
    ctrl(res is not None, "`_resultat()` est localisable", "")
    res = res or ""
    ctrl("chercher_refus(" in res,
         "`_resultat()` APPELLE `chercher_refus`", "⛔ pas seulement défini")
    ctrl('"refus"' in res and '"refus_motifs"' in res,
         "…et pose `refus` (LE MOTIF) et `refus_motifs`",
         "⛔ pas un booléen nu")
    ctrl("completude(" in res, "…et `completude()` y est appelée aussi",
         "AC2.2 : un compteur non lu ne compte pas")

    mn = corps_python(py, "def main(")
    ctrl(mn is not None, "`main()` est localisable", "")
    mn = mn or ""
    ctrl(re.search(r'if r\["refus"\][^\n]*\n\s*code = 1', mn) is not None
         or re.search(r'if r\["refus"\].*?:\s*\n\s*code = 1', mn, re.S) is not None,
         "…et un refus ARME le code de retour dans `main()`",
         "au même titre qu'une invite non rendue")
    ctrl('r["completude"]["etat"] == "PERTE"' in mn and "code = 1" in mn,
         "…et une PERTE de lignes l'arme aussi", "⛔ pas les étrangères")
    ctrl('--refus-tolere' in mn and 'default=[]' in mn,
         "`--refus-tolere` existe et vaut `[]` PAR DÉFAUT",
         "⛔ jamais désarmé par défaut")
    # AC1.4 — le refus est imprimé EN TÊTE : l'ordre dans le source fait foi.
    i_ref = mn.find('print("🔴 REFUS')
    i_sor = mn.find('print(r["sortie"])')
    ctrl(0 <= i_ref < i_sor,
         "AC1.4 : le refus s'imprime AVANT la sortie",
         "⛔ pas noyé dans 90 s de capture")


def bloc_completude(py, c):
    """AC2 — LA COMPLÉTUDE EST VISIBLE, DES DEUX CÔTÉS."""
    print("\n── AC2 : l'instrument dit s'il a TOUT lu ───────────────────────")
    tr = corps_fonction(c, "static int dn_cmd_tracer(")
    ctrl(tr is not None, "le firmware a un shim `dn_cmd_tracer()`", "")
    tr = tr or ""
    ctrl("lignes emises" in tr, "…qui imprime le compteur en FIN de commande",
         "l'invariant par capture")
    # ⛔ Le compteur DOIT être lu AVANT de s'imprimer lui-même.
    i_lu = tr.find("= s_lignes_cmd;")
    i_pr = tr.find("lignes emises")
    ctrl(0 <= i_lu < i_pr,
         "…et il LIT `s_lignes_cmd` AVANT de l'imprimer",
         "⛔ sinon il se compterait lui-même")
    pf = corps_fonction(c, "static int dn_console_printf(const char *fmt, ...)\n{")
    ctrl(pf is not None, "`dn_console_printf()` existe", "")
    pf = pf or ""
    ctrl("'\\n'" in pf and "s_lignes_cmd++" in pf,
         "…et il compte les passages à la ligne", "⛔ pas les appels")
    ctrl("#define printf dn_console_printf" in c,
         "…et TOUT `printf` du fichier passe par lui",
         "⛔ pas 32 branches à instrumenter")
    st = corps_fonction(c, "esp_err_t dn_console_start(void)")
    ctrl(st is not None, "`dn_console_start()` est localisable", "")
    st = st or ""
    ctrl("s_shims[i]" in st and "s_cmd_reelle[i]" in st,
         "…et il enregistre le SHIM à la place de la commande",
         "toute commande est instrumentée")
    ctrl("_Static_assert" in st,
         "…avec un `_Static_assert` sur le nombre de shims",
         "⛔ échoue à la COMPILATION, pas au boot")

    cp = corps_python(py, "def completude(")
    ctrl(cp is not None, "l'hôte a `completude()`", "")
    cp = cp or ""
    for etat in ("PERTE", "LIGNES_ETRANGERES", "SANS_COMPTEUR"):
        ctrl('"%s"' % etat in cp, "…et il distingue l'état %s" % etat,
             "⛔ « pas de compteur » ≠ « 0 perte »")
    ctrl("coupees_avant_echo" in cp,
         "AC2.3 : ce que `nettoyer()` coupe AVANT l'écho est compté",
         "le SECOND mécanisme candidat")
    ctrl("VIDE_NE_PROUVE_RIEN" in py and py.count("VIDE_NE_PROUVE_RIEN") >= 2,
         "AC2.5 : la règle « vide ≠ muet » est POSÉE ET UTILISÉE",
         "⛔ pas un commentaire de dossier")
    ctrl(re.search(r"(?i)parade.{0,80}dn4-2.{0,400}insuffisan", py, re.S)
         is not None
         or re.search(r"(?i)dn4-2.{0,200}INSUFFISANTE", py, re.S) is not None,
         "AC2.4 : la parade `dn4-2` est dite INSUFFISANTE dans le pilote",
         "la perte existe AUSSI en solo (1/7)")
    ctrl(re.search(r"(?i)(2 A/B|30 passes).{0,200}(reproduit|reproduction)",
                   py, re.S) is not None,
         "AC2.6 : la cause est déclarée NON INSTRUITE",
         "⛔ ne pas inventer un mécanisme")


def bloc_miroir(py, c):
    """🎯 LE MIROIR — LE CONTRÔLE QUI TIENT LES DEUX BOUTS DU PROTOCOLE.

    ⛔ ANGLE MORT CONNU DE CE DÉPÔT : une gate qui lit UN SEUL fichier laisse
       passer un désaccord de format entre deux fichiers. Ici on EXTRAIT le
       `printf` du firmware, on FABRIQUE la ligne qu'il produirait, et on la
       passe à la regex de l'hôte. Un des deux qui bouge ⇒ rouge.
    """
    print("\n── LE MIROIR : le format du compteur, des DEUX côtés ───────────")
    m = re.search(r'printf\("(--- fin : [^"]*?)"', c)
    ctrl(m is not None, "le format du compteur est EXTRAIT du firmware",
         "⛔ pas recopié dans la gate")
    fmt = m.group(1) if m else ""
    exemple = (fmt.replace("%u", "12").replace("%s", "").replace("\\n", "")
               .strip())
    rx = re.search(r'RE_COMPTEUR\s*=\s*re\.compile\(r"([^"]+)"\)', py)
    ctrl(rx is not None, "…et la regex de l'hôte est EXTRAITE du pilote", "")
    if fmt and rx:
        try:
            mm = re.compile(rx.group(1)).match(exemple)
        except re.error as e:
            mm = None
            print("        regex illisible : %s" % e)
        # 🔴 REVUE DU 2026-08-31 — `mm.group(1)` ÉTAIT APPELÉ SANS GARDE : une
        #    `RE_COMPTEUR` réécrite sans groupe de capture faisait sortir la
        #    gate en `IndexError` — ⛔ ni `[KO]`, ni `BILAN`. Un contrôle dont le
        #    TEST ERRE ne dit pas « rien à signaler » : il ne dit RIEN.
        ctrl(mm is not None and mm.lastindex is not None and mm.group(1) == "12",
             "🎯 la ligne du FIRMWARE est lue par la regex de l'HÔTE",
             repr(exemple)[:34])
        # 🔴 REVUE DU 2026-08-31 — LE MARQUEUR « COMPTE NON FIABLE » ÉTAIT
        #    **FABRIQUÉ ICI**, ⛔ pas extrait du firmware, et sa SÉMANTIQUE
        #    (`fiable = "NON FIABLE" not in …`) n'était jamais testée. Reproduit :
        #    renommer la chaîne côté carte en « (compte douteux : …) » laissait la
        #    gate à `107 OK / 0 KO` PENDANT que le pilote rendait
        #    `{'etat': 'PERTE'}` et criait `🔴 PERTE ⇒ RE-JOUER` **à tort** sur une
        #    capture que la carte déclarait elle-même non fiable. C'est la règle
        #    (2) que cette gate s'écrit à elle-même : ⛔ NE PAS CODER EN DUR CE
        #    QUI SE GARDE GÉNÉRIQUEMENT.
        mfia = re.search(r'printf\("(\s*\(COMPTE[^"]*?)"', c) or \
            re.search(r'"(\s*\([A-Z][^"]*NON FIABLE[^"]*)"', c)
        ctrl(mfia is not None,
             "le marqueur d'INFIABILITÉ est EXTRAIT du firmware",
             "⛔ plus fabriqué dans la gate")
        suffixe = mfia.group(1).replace("\\n", "").rstrip() if mfia else ""
        ex2 = exemple.replace(" ---", "") + suffixe + " ---"
        try:
            m2 = re.compile(rx.group(1)).match(ex2)
        except re.error:
            m2 = None
        ctrl(m2 is not None, "…y compris quand la carte déclare son compte faux",
             "l'autre branche du même printf")
        # 🎯 ET LA SÉMANTIQUE, ⛔ pas seulement la forme : ce que l'hôte CONCLUT
        #    de ce marqueur doit être « non fiable », pas « perte ».
        cpl = corps_python(py, "def completude(") or ""
        mfi = re.search(r'fiable\s*=\s*"([^"]+)"\s+not\s+in', cpl)
        ctrl(mfi is not None and mfi.group(1) in ex2,
             "🎯 …et le mot que l'HÔTE cherche est DANS ce que la CARTE écrit",
             "%r" % (mfi.group(1) if mfi else "?"))
        ctrl(m2 is not None and m2.lastindex is not None
             and (mfi is not None and mfi.group(1) in (m2.group(2) or "")),
             "…et il tombe dans le GROUPE que l'hôte inspecte",
             "⛔ pas ailleurs dans la ligne")


def bloc_injecteur(racine, inj):
    """AC3 — L'INJECTEUR A UN JEU QUI VARIE, ET IL DÉCLARE LES JEUX FIXES."""
    print("\n── AC3 : le jeu variable, et la bannière des jeux FIXES ────────")
    ctrl("JEUX_RAMPES" in inj, "`JEUX_RAMPES` existe", "")
    ctrl(re.search(r'"rampe"', inj) is not None
         and 'choices=sorted(list(JEUX) + ["rampe"])' in inj,
         "…et `--jeu rampe` est offert", "")
    for j in ("pire", "reel", "nominal", "trou"):
        ctrl(re.search(r'^\s{4}"%s":\s*\{' % j, inj, re.M) is not None,
             "⛔ le jeu témoin « %s » est INTACT" % j,
             "il ne remplace aucun jeu")
    b = corps_python(inj, "def banniere_jeu(")
    ctrl(b is not None, "`banniere_jeu()` existe", "")
    b = b or ""
    ctrl("FIXE" in b and ("94 645" in b or "128 613" in b) and "108" in b,
         "…et elle NOMME la conséquence, chiffrée",
         "36 % de stimulus en moins, ×108")
    mn = corps_python(inj, "def main(")
    ctrl(mn is not None and "banniere_jeu(" in (mn or ""),
         "…et `main()` l'APPELLE", "⛔ pas seulement définie")
    ctrl("bornes_relues(" in inj and "dn_link.c" in inj,
         "les bornes sont RELUES de `dn_link.c`",
         "⛔ jamais recopiées dans l'outil")
    inject = corps_python(inj, "def injecter(")
    ctrl(inject is not None and "valeurs_rampes(" in (inject or ""),
         "…et le tir CALCULE les valeurs à chaque cycle",
         "⛔ pas un dict figé de plus")
    # 🔴 REVUE DU 2026-08-31 — L'INJECTEUR ÉCRIVAIT ET JETAIT LA RÉPONSE.
    #    « N trames emises » était un compte d'ÉCRITURES côté hôte, et `main()`
    #    rendait 0 quoi qu'il arrive : le défaut d'AC1 recréé dans l'outil qui
    #    PRODUIT le stimulus.
    ctrl("echo.extend(" in (inject or ""),
         "🔴 …et il GARDE ce que la carte répond",
         "⛔ plus `ser.read(...)` jeté")
    ctrl("chercher_refus(" in (inject or ""),
         "🔴 …et il y CHERCHE un refus", "⛔ un compte d'écritures n'est pas un accord")
    ctrl("trames ECRITES" in inj,
         "…et il dit « ECRITES », ⛔ plus « emises »",
         "le mot portait la confusion")
    cl = corps_python(inj, "def campagne_latence(") or ""
    ctrl('cpl.get("etat") in ("PERTE", "COMPTE_NON_FIABLE")' in cl,
         "🔴 …et la campagne LIT `completude` de la capture `pc`",
         "⛔ elle ne lisait que `refus`")
    ctrl('r["invite_rendue"] is False' in cl,
         "…et refuse une fenêtre dont l'invite n'est pas rendue", "")
    vd_ = corps_python(inj, "def verbe_latence_delta(") or ""
    ctrl("ecarts_stim" in vd_ and "secondes_par_fenetre" in vd_,
         "🔴 …et `--latence-delta` REFUSE deux STIMULI différents",
         "il publiait « +294 ms » et rc 0")
    ctrl("except ValueError" in vd_ and "REFUS" in vd_,
         "…et un relevé ILLISIBLE est un REFUS, ⛔ pas une trace", "")
    ctrl("a.secondes <= 0" in (mn or "") and "a.latence < 0" in (mn or ""),
         "…et `--secondes` / `--latence` sont BORNÉS avant le port",
         "0 trames + rc 0 était indiscernable d'un tir")
    rc, out = joue(["tools/dn_injecteur.py", "--temoin-negatif"], racine)
    ctrl(rc == 0 and re.search(r"BILAN : \d+ OK, 0 KO", out) is not None,
         "🔴 LE TÉMOIN DE L'INJECTEUR PASSE (joué, ⛔ pas supposé)",
         out.strip().splitlines()[-1][:30] if out.strip() else "rc=%d" % rc)


def bloc_cpu(c):
    """AC4 — `cpu` MESURE SANS BLOQUER LE TRANSPORT QU'IL MESURE."""
    print("\n── AC4 : `cpu` ne bloque plus son propre transport ─────────────")
    d = corps_fonction(c, "static int cpu_delta(void)")
    ctrl(d is not None, "`cpu_delta()` existe", "")
    d = d or ""
    ctrl("vTaskDelay" not in d,
         "🔴 …et il ne contient AUCUN `vTaskDelay`",
         "⛔ le REPL EST le transport")
    dep = corps_fonction(c, "static int cpu_depart(void)")
    ctrl(dep is not None and "vTaskDelay" not in (dep or ""),
         "…ni `cpu_depart()`", "")
    ctrl("DN_CPU_DELTA_HORIZON_US" in d and "REFUS DE PUBLIER" in d,
         "…et le rebouclage ~71 min est GARDÉ, pas commenté",
         "il REFUSE plutôt que de publier faux")
    i_g = d.find("DN_CPU_DELTA_HORIZON_US")
    i_p = d.find("charge CPU sur la SESSION")
    ctrl(0 <= i_g < i_p, "…et la garde tombe AVANT toute publication", "")
    cm = corps_fonction(c, "static int cmd_cpu(int argc, char **argv)\n{\n    if (argc >= 2 && strcmp(argv[1], \"brut\")")
    ctrl(cm is not None, "`cmd_cpu()` (variante instrumentée) est localisable", "")
    cm = cm or ""
    ctrl('"depart"' in cm and '"delta"' in cm,
         "…et il route `depart` / `delta`", "")
    i_dit = cm.find("CETTE COMMANDE BLOQUE LE REPL")
    i_dort = cm.find("vTaskDelay")
    ctrl(0 <= i_dit < i_dort,
         "AC4.3 : `cpu N` dit ce qu'il ne peut pas mesurer AVANT de dormir",
         "⛔ après, l'opérateur a déjà son chiffre")
    ctrl("0,8" in cm and "0,9" in cm,
         "…et il NOMME le symptôme qui l'a trahi",
         "0,8 % sous trafic vs 0,9 % au repos")


def bloc_auto_epreuve():
    """🎯 LA GATE S'ÉPROUVE SUR DES SOURCES FABRIQUÉES.

    🔴 POURQUOI CE BLOC EXISTE — REVUE DU 2026-08-31. Trois de ses propres
       défauts étaient INVISIBLES aux mutants : les muter ne changeait RIEN,
       parce qu'aucun fichier livré n'exerçait le chemin fautif (aucun `printf`
       commenté ne cite `35 100`, aucune consigne vivante ne récite `36 675`).
       Un contrôle dont le mutant reste vert n'est pas gardé — il est SUPPOSÉ.
    ⇒ On lui donne des sources qui EXERCENT le chemin, et on exige le verdict.
    """
    print("\n── LA GATE S'ÉPROUVE ELLE-MÊME (sources FABRIQUÉES) ────────────")
    faux = ('/* printf("aire de 35 100 px, commentaire historique\\n"); */\n'
            'static void f(void) {\n'
            '    printf("vrai message\\n");\n'
            '}\n')
    ctrl(printfs(faux) == ["vrai message\\n"],
         "🔴 `printfs()` IGNORE un `printf` en COMMENTAIRE",
         "⛔ sinon la doc du correctif fait rougir")
    multi = 'static void g(void) {\n    printf("a\\n" "b 35 100 c\\n");\n}\n'
    ctrl(any("35 100" in t for t in printfs(multi)),
         "🔴 …et elle VOIT le littéral de CONTINUATION",
         "⛔ le défaut d'AC5.2 y était invisible")
    ctrl(sans_commentaires_py("x = 1  # min(timeout, 2.0)\n").strip() == "x = 1",
         "🔴 `sans_commentaires_py()` retire la prose",
         "4e occurrence : citer un motif l'accordait")
    src = ('static int cmd_x(int argc, char **argv) {\n'
           '    if (argc == 3 && strcmp(argv[1], "m") == 0 &&\n'
           '        strcmp(argv[2], "mur") == 0) { A(); }\n'
           '    if (argc == 3 && strcmp(argv[1], "m") == 0) { B(); }\n'
           '}\n')
    brs = branches_argv1(src, "static int cmd_x(", "m")
    ctrl(len(brs) == 2 and 'strcmp(argv[2], "mur")' in brs[0][0]
         and 'strcmp(argv[2], "mur")' not in brs[1][0],
         "🔴 `branches_argv1()` distingue une branche À MOT-CLÉ",
         "une tête trop courte les confondait")


def bloc_revue_firmware(c, ui, wifi_h):
    """Les défauts firmware trouvés par la REVUE DE CODE du 2026-08-31."""
    print("\n── REVUE : les défauts firmware que RIEN ne gardait ────────────")
    cd_ = corps_fonction(c, "static int cpu_delta(void)") or ""
    mt = corps_fonction(
        c, "static bool cpu_meme_tache(const TaskStatus_t *a, const TaskStatus_t *b)") or ""
    ctrl("pcTaskName" in mt and "xHandle" in mt,
         "🔴 `cpu delta` apparie sur le HANDLE **ET** LE NOM",
         "FreeRTOS recycle les TCB")
    # ⛔ LE CONTRÔLE PORTE SUR CE QUI FIXE `base`, ⛔ pas sur la présence du mot
    #   `xHandle` : la comparaison de handle NUE reste légitime — c'est elle qui
    #   DÉTECTE le recyclage. Ce qui est interdit, c'est d'en tirer une origine.
    nu = sans_commentaires_c(cd_)
    fautifs = [m.group(0) for m in re.finditer(
        r"if \([^\n]*\.xHandle == [^\n]*\) \{\s*\n\s*base = ", nu)]
    ctrl(not fautifs,
         "…et AUCUNE origine `base` ne vient d'un handle SEUL",
         "⛔ l'enroulement publiait « CHARGE 100 % »")
    ctrl(nu.count("cpu_meme_tache(") >= 3,
         "…les TROIS boucles d'appariement passent par le prédicat",
         "somme · impression · disparues")
    ctrl("recyclees" in cd_ and "TCB RECYCLE" in cd_,
         "…et un TCB recyclé est DÉCLARÉ", "⛔ plus silencieux")
    ctrl("NEE **ET**" in cd_ or "MORTE dans la fenetre" in cd_,
         "…et le biais « née ET morte dans la fenêtre » est écrit",
         "deux relevés ne voient pas ce qui vit entre eux")
    ctrl("s_cpu_dep_cap" not in sans_commentaires_c(c),
         "…et la variable morte `s_cpu_dep_cap` est RETIRÉE",
         "affectée, jamais lue")

    # 🔴 dn4-40 / AC40.6.b — LA SIGNATURE ETAIT AMBIGUE, ET ELLE TOMBAIT JUSTE
    #    PAR CHANCE. Sans le `\n{`, elle matche AUSSI la declaration avancee
    #    (`… __attribute__((format(printf, 1, 2)));`), qui vient DEUX LIGNES
    #    AVANT la definition. `str.find` prenait donc la declaration — et le
    #    premier `{` rencontre ensuite se trouvait etre celui de la definition.
    #    ⇒ Le corps extrait etait le BON, mais ⛔ pour aucune raison : intercaler
    #      quoi que ce soit portant une accolade entre les deux aurait fait
    #      extraire autre chose EN SILENCE, et « le corps se referme » aurait
    #      continue de dire oui. Le controle d'ambiguite l'a epingle.
    pf = corps_fonction(
        c, "static int dn_console_printf(const char *fmt, ...)\n{") or ""
    ctrl("0xC0) == 0x80" in pf and "pile[n] = " in pf,
         "🔴 la troncature de FAMINE recule sur une tête UTF-8",
         "un octet orphelin cassait le motif de refus")

    ce = corps_fonction(c, "void dn_console_compter_externes(int lignes)") or ""
    ctrl(ce != "", "🔴 `dn_console_compter_externes()` existe",
         "les modules frères imprimaient HORS du compteur")
    ctrl("s_lignes_cmd +=" in ce,
         "…et elle alimente le MÊME compteur", "")
    ctrl("dn_console_compter_externes(dn_ui_log_mem())" in sans_commentaires_c(c),
         "…et les appels à `dn_ui_log_mem()` la traversent",
         "6 lignes non annoncées ×4 sites")
    ctrl("dn_console_compter_externes((int)dn_wifi_lignes_emises())"
         in sans_commentaires_c(c),
         "…et `wifi on` / `wifi off` aussi", "13 printf hors compteur")
    ctrl("int dn_ui_log_mem(void)" in ui,
         "…et `dn_ui_log_mem()` REND son nombre de lignes",
         "⛔ pas un compte recopié en face")
    ctrl("dn_wifi_lignes_emises" in wifi_h,
         "…et les STUBS de `dn_wifi.h` comptent aussi",
         "🔴 c'est le chemin RÉELLEMENT compilé")

    dt = corps_fonction(c, "static bool largeur_original_probable(const char *recu, char *out, size_t n_out)") or ""
    ctrl("(js == 7) != (mo == 0)" not in sans_commentaires_c(dt),
         "🔴 le balayage de dates couvre les formes MIXTES",
         "`??? 15 AOUT` était injoignable")

    bb = branche_argv1(c, "static int cmd_widget(", "barre", 3) or ""
    ctrl("dn_ui_geom_bandes(" in bb and "RAPPORT NON PUBLIE" in bb,
         "🔴 `widget barre` REFUSE son rapport hors de sa hauteur de mesure",
         "le numérateur 6 334 est DATÉ")


def bloc_sorties(c):
    """AC5 — TROIS SORTIES CESSENT DE MESURER AUTRE CHOSE."""
    print("\n── AC5 : relire au lieu de réciter, et mesurer ce qu'on annonce ─")
    col = corps_fonction(c, "static void colonnes(const char *s, int largeur)")
    ctrl(col is not None, "`colonnes()` est localisable", "")
    col = col or ""
    # 🔴 REVUE DU 2026-08-31 — CE CONTRÔLE EXIGEAIT « octets de TÊTE », ET
    #    C'ÉTAIT LE DÉFAUT : compter les têtes n'est PAS compter des colonnes.
    #    Ce fichier imprime des glyphes DOUBLE LARGEUR partout ⇒ un champ
    #    « tronqué à 10 colonnes » en rendait 12 à 20 et décalait la ligne — le
    #    symptôme même que la troncature existe pour arrêter. Et « attention »
    #    (base + sélecteur de variation) comptait DEUX colonnes et pouvait être
    #    coupé ENTRE LES DEUX.
    ctrl("dn_cp_colonnes(" in col,
         "🔴 …et elle mesure une LARGEUR D'AFFICHAGE, ⛔ pas des octets",
         "les glyphes doubles comptent 2")
    lw = corps_fonction(c, "static int dn_cp_colonnes(unsigned cp)") or ""
    ctrl("0xFE0F" in lw and "return 0" in lw,
         "…et le sélecteur de variation vaut ZÉRO colonne",
         "⛔ jamais coupé de sa base")
    ctrl("0x1F300" in lw and "return 2" in lw,
         "…et les émojis en valent DEUX", "⛔ pas une par octet de tête")
    ctrl(re.search(r"cols > largeur", col) is not None and "return;" in col,
         "🔴 …et elle TRONQUE quand `cols > largeur`",
         "le défaut qu'elle existe pour fermer")
    ctrl('">"' in col or '">"' in col or '%.*s>' in col,
         "…et la coupe se VOIT (dernier caractère « > »)",
         "⛔ tronquer en silence est un autre mensonge")

    # 🎯 LA RÈGLE DU `35 100` EST UNE **FORME**, ⛔ PAS UNE LISTE DE LIGNES :
    #    « etait 35 100 a … » est un REPÈRE DATÉ (le patron du fichier) ; toute
    #    autre occurrence est une CONSIGNE D'ACTION qui récite une géométrie.
    #    Deux formes de REPÈRE DATÉ existent dans ce fichier, et les deux sont
    #    légitimes : « (etait 35 100 a 156) » et « (35 100 -> 36 675 px) ».
    #    Toute autre occurrence IMPRIMÉE est une consigne d'action qui envoie
    #    l'opérateur vérifier un nombre que la géométrie ne rend plus.
    #    ⛔ On regarde les LITTÉRAUX IMPRIMÉS : les commentaires historiques du
    #      fichier citent `35 100` et ont le DROIT de le faire — les réécrire
    #      referait la faute que `dn4-15` a nommée (« une réfutation ne vaut que
    #      son périmètre »).
    recitees = [t for t in printfs(c)
                if re.search(r"35\s?100", t)
                and not re.search(r"etait\s+35\s?100|35\s?100\s*->", t)]
    ctrl(not recitees,
         "🔴 aucune AIRE RÉCITÉE dans un printf hors REPÈRE DATÉ",
         "fautifs : %s" % ((recitees[0][:26] if recitees else "aucun")))
    # 🔴 REVUE DU 2026-08-31 — CE CONTRÔLE COMPARAIT UN **TOTAL SUR TOUT LE
    #    FICHIER**, c'est-à-dire exactement ce que la règle (3) de cette gate
    #    interdit. UN SEUL `printf` fabriqué le satisfaisait. ⇒ on LOCALISE les
    #    deux repères datés dans LEURS branches.
    for mot, argc in (("rafale", 2), ("barre", 3)):
        b = branche_argv1(c, "static int cmd_widget(", mot, argc) or ""
        ctrl(any(re.search(r"etait\s+35\s?100", t) for t in printfs(b)),
             "…et `widget %s` garde SON repère daté" % mot,
             "⛔ on ne réécrit pas les comptes rendus")
    # 🔴 ET AC5.2 DIT « ⛔ NI 35 100 NI 36 675 » — `36 675` N'ÉTAIT JAMAIS
    #    CHERCHÉ. Replanter cette aire-là dans une consigne vivante laissait la
    #    gate à `107 OK / 0 KO`. La règle est la MÊME : une aire dans une
    #    consigne d'action est un dénominateur qui se périmera.
    recitees2 = [t for t in printfs(c)
                 if re.search(r"36\s?675", t)
                 and not re.search(r"etait\s+36\s?675|->\s*36\s?675", t)]
    ctrl(not recitees2,
         "🔴 …et AUCUNE occurrence de `36 675` non plus (AC5.2, mot pour mot)",
         "fautifs : %s" % (recitees2[0][:26] if recitees2 else "aucun"))
    for mot, argc in (("rafale", 2), ("barre", 3)):
        br = branche_argv1(c, "static int cmd_widget(", mot, argc)
        ctrl(br is not None, "la branche `widget %s` est localisable" % mot, "")
        ctrl(br is not None and "dn_ui_case_dim(" in br,
             "…et elle RELIT l'aire par `dn_ui_case_dim()`" ,
             "⛔ ni 35 100 ni 36 675 ne sont écrivables")
    br = branche_argv1(c, "static int cmd_widget(", "barre", 3)
    ctrl(br is not None and "6334" in br and "/ aire_b" in br,
         "…et `widget barre` CALCULE son pourcentage",
         "18 % récité valait 17,3 %")

    fl = corps_fonction(c, "static void largeur_drapeau_repl(const char *recu)")
    ctrl(fl is not None, "AC5.3 : `largeur_drapeau_repl()` existe", "")
    fl = fl or ""
    ctrl("0x80" in fl and "largeur_original_probable(" in fl,
         "…et il NOMME l'original probable, ⛔ pas seulement la règle",
         "`RÉSEAU` privé de ses octets ≥ 0x80")
    op = corps_fonction(c, "static bool largeur_original_probable(")
    ctrl(op is not None and "dn_ui_metrique_nom(" in (op or "")
         and "dn_ui_barre_date_forme(" in (op or ""),
         "…sur un vocabulaire ENGENDRÉ, ⛔ pas une table locale",
         "métriques + formes de date")
    # 🔴 REVUE DU 2026-08-31 — CE CONTRÔLE COMPTAIT `== 2` SUR `cmd_widget`,
    #    UNE FONCTION DE ~2 000 LIGNES. Déplacer l'un des deux appels hors de la
    #    branche `widget largeur` laissait le compte à 2, la gate VERTE, et la
    #    commande SANS son drapeau. La règle (3) que cette gate s'écrit —
    #    « localise (fonction + ancre), ⛔ ne compare pas un TOTAL » — était
    #    violée par le bloc qui applique AC5.3.
    brs = branches_argv1(c, "static int cmd_widget(", "largeur")
    ctrl(len(brs) >= 2, "les branches `widget largeur` sont TOUTES localisées",
         "%d trouvée(s)" % len(brs))
    # Celles qui mesurent une CHAÎNE LIBRE sont celles qui ne comparent pas
    # `argv[2]` à un mot-clé (`mur`, `reset`). ⛔ Ce sont exactement celles-là
    # qui doivent lever le drapeau — les autres ne reçoivent pas de texte.
    libres = [(t, b) for t, b in brs
              if not re.search(r'strcmp\(argv\[2\],\s*"', t)]
    mots_cles = [(t, b) for t, b in brs
                 if re.search(r'strcmp\(argv\[2\],\s*"', t)]
    ctrl(len(libres) == 2,
         "…dont DEUX mesurent une chaîne libre", "%d" % len(libres))
    ctrl(all("largeur_drapeau_repl(argv[2])" in b for _, b in libres),
         "🔴 …et CHACUNE de ces deux lève le drapeau REPL",
         "⛔ localisé, ⛔ pas un total sur 2 000 lignes")
    ctrl(not any("largeur_drapeau_repl(argv[2])" in b for _, b in mots_cles),
         "…et AUCUNE branche à mot-clé ne le lève",
         "`mur` / `reset` ne reçoivent pas de texte")


def bloc_leviers(c, w):
    """AC6 — LES LEVIERS À CHAUD DISENT CE QU'ILS CASSENT."""
    print("\n── AC6 : les leviers à chaud, et le verdict de contraste ───────")
    br = branche_argv1(c, "static int cmd_widget(", "piste", 3)
    ctrl(br is not None, "la branche `widget piste` est localisable", "")
    br = br or ""
    # 🔴 REVUE DU 2026-08-31 — CE CONTRÔLE LISAIT LE TEXTE **BRUT** DE LA
    #    BRANCHE, COMMENTAIRES COMPRIS, alors que le contrôle `dn3-3` deux lignes
    #    plus bas utilise correctement `printfs(br)`. L'incohérence était DANS LE
    #    FICHIER. Reproduit : supprimer les trois `printf` de l'avertissement et
    #    laisser `/* TODO: reposer l'avertissement … */` rendait `[OK]` et
    #    `107 OK / 0 KO` — le défaut d'AC6.1, vert.
    dits_br = " ".join(printfs(br))
    ctrl("SI LA CARTE EST EN VEILLE" in dits_br,
         "🔴 …et elle AVERTIT `veille off` comme ses trois voisines",
         "la jauge se pose 27 px trop haut · ⛔ lu dans ce qui est IMPRIMÉ")
    # ⛔ ON CHERCHE DANS CE QUI EST **IMPRIMÉ**, pas dans le fichier : le
    #    commentaire qui EXPLIQUE le correctif nomme forcément `dn3-3`, et un
    #    contrôle naïf rougirait sur sa propre documentation. Vu, ici même.
    dits = dits_br
    ctrl("dn3-3" not in dits,
         "🔴 …et le renvoi vers `dn3-3` (`done`) n'est plus IMPRIMÉ",
         "⛔ un renvoi mort est un instrument qui ment")
    ctrl("dn4-29" in dits,
         "…redirigé vers le porteur VIVANT `dn4-29`",
         "statut vérifié au tracker")

    vc = corps_fonction(c, "static void verdict_contraste(void)")
    ctrl(vc is not None, "`verdict_contraste()` existe", "")
    vc = vc or ""
    ctrl("dn_widget_piste()" in vc and "dn_widget_amb_case_bg()" in vc,
         "…et il RELIT la piste ET l'aplat", "⛔ aucune copie locale")
    ctrl("dn_widget_desaturer(" in vc and "dn_ui_case_couleur(" in vc,
         "…et l'accent par la MÊME fonction que l'écran",
         "⛔ pas une copie de la formule")
    # 🔴 REVUE DU 2026-08-31 — CE CONTRÔLE EXIGEAIT « ECART NUL » COMME UNE
    #    « certitude ARITHMÉTIQUE, aucun œil requis ». C'ÉTAIT LE DÉFAUT : l'écart
    #    se calcule sur une LUMINANCE (`lum601`), qui écrase trois canaux en un.
    #    `widget piste 0x960000` et `veille case 0x004D00` rendent tous deux
    #    `lum 45` ⇒ écart 0 sur un rouge sombre contre un vert sombre. La gate
    #    ÉPINGLAIT donc une sur-annonce — elle exige désormais l'inverse.
    cb = corps_fonction(
        c, "static const char *contraste_bande_paire(int ecart, bool meme_couleur,") or ""
    ctrl(cb != "", "`contraste_bande_paire()` est localisable",
         "⛔ la version SANS paire est retirée")
    ctrl("ecart == 0 && meme_couleur" in cb,
         "🔴 …et « même couleur » exige les TROIS CANAUX",
         "⛔ pas une égalité de LUMINANCE")
    ctrl("LUMINANCE IDENTIQUE" in cb and "A VERIFIER A L'OEIL" in cb,
         "…et une luminance égale à teintes DIFFÉRENTES renvoie À L'ŒIL",
         "⛔ elle n'affirme plus la disparition")
    ctrl("DN_CONTRASTE_REPERE" in cb,
         "…et le repère 24 est NOMMÉ, ⛔ pas écrit en dur",
         "emprunté à `bloc_gris`")
    ctrl(len(re.findall(r"contraste_bande\(", sans_commentaires_c(c))) == 0,
         "…et l'ANCIENNE bande (sans paire) n'existe plus",
         "⛔ une morte se recopie")
    ctrl("piste == fond_amb" in vc and "acc == piste" in vc,
         "…et les DEUX paires passent leur égalité de couleur",
         "piste↔case ET indicateur↔piste")
    ctrl("comparee" in vc and "pire == 255" not in vc,
         "…et la sentinelle n'est plus prise DANS le domaine mesuré",
         "255 est un écart LÉGAL")
    ctrl("NI un plafond NI un plancher" in vc,
         "🔴 …et le « PLAFOND » de l'ACTIF est déclaré pour ce qu'il est",
         "`widget opa 0` le fait monter à 255 − lp")
    ctrl("ON NE REFUSE PAS" in vc,
         "…et le verdict AVERTIT, ⛔ ne refuse pas",
         "doctrine explicite de ces commandes")
    for mot, sig, argc in (("piste", "static int cmd_widget(", 3),
                           ("couleur", "static int cmd_widget(", 4),
                           ("opa", None, None),
                           ("case", "static int cmd_veille(", None)):
        if mot == "opa":
            # 🔴 REVUE DU 2026-08-31 — CE MOTIF CODAIT EN DUR L'INDENTATION
            #    (`\n    }`) ET S'ARRÊTAIT AU PREMIER `return 0;`. Un `return 0;`
            #    anticipé (un chemin d'usage) rétrécissait la portée à AVANT
            #    l'appel, et une ré-indentation faisait que l'ancre ne matchait
            #    plus : `[KO]` sur du code CORRECT, avec un détail qui NOMME LA
            #    MAUVAISE CAUSE (« un verdict non appelé ne garde rien »).
            #    ⇒ on utilise le même localisateur de branche que les voisins.
            b = branche_argv1(c, "static int cmd_widget(", "opa")
            trouve = b is not None and "verdict_contraste()" in b
        else:
            b = branche_argv1(c, sig, mot, argc)
            trouve = b is not None and "verdict_contraste()" in b
        ctrl(trouve, "…et la branche `%s` l'APPELLE" % mot,
             "⛔ un verdict non appelé ne garde rien")

    tr = branche_argv1(c, "static int cmd_touch(", "reset")
    ctrl(tr is not None, "AC6.3 : la branche `touch reset` est localisable", "")
    tr = tr or ""
    ctrl("s_base_consommes" in tr and "veille" in tr,
         "…et elle AVERTIT qu'elle casse le compteur de `veille`",
         "« reveils : 3 » à côté de « CONSOMMES : 0 »")

    # ── AC8.7 : LA GATE LIT `W_COL_PISTE_DEFAUT` **ET** `s_piste` ───────────
    #    C'est l'écart déclaré de `dn4-29` : « aucun des 22 verif_*.py ne les
    #    lit ». Elle les lit, et elle en CALCULE le contraste par défaut.
    print("\n── AC8.7 : la paire piste ↔ fond, que RIEN ne gardait ──────────")
    mp = re.search(r"#define W_COL_PISTE_DEFAUT\s+0x([0-9A-Fa-f]{6})", w)
    ms = re.search(r"static uint32_t s_piste\s*=\s*(\w+);", w)
    mb = re.search(r"#define W_AMB_CASE_BG\s+0x([0-9A-Fa-f]{6})", w)
    ctrl(mp is not None, "`W_COL_PISTE_DEFAUT` est LU dans `dn_widget.c`",
         "0x%s" % (mp.group(1) if mp else "?"))
    ctrl(ms is not None and ms.group(1) == "W_COL_PISTE_DEFAUT",
         "…et `s_piste` en dérive", ms.group(1) if ms else "?")
    ctrl(mb is not None, "`W_AMB_CASE_BG` est LU aussi",
         "0x%s" % (mb.group(1) if mb else "?"))
    if mp and mb:
        def lum(h):
            v = int(h, 16)
            return ((v >> 16 & 255) * 77 + (v >> 8 & 255) * 150 +
                    (v & 255) * 29) >> 8
        lp, lf = lum(mp.group(1)), lum(mb.group(1))
        e = abs(lp - lf)
        ctrl(e != 0,
             "🔴 la paire LIVRÉE piste ↔ aplat n'est PAS de l'écart NUL",
             "lum %d vs %d ⇒ écart %d" % (lp, lf, e))
        # 🔴 REVUE DU 2026-08-31 — CETTE PHRASE ÉTAIT IMPRIMÉE **EN DUR**,
        #    « SOUS le repère 24 », quel que soit l'écart qui venait d'être
        #    calculé. Une palette future donnant `e = 97` aurait fait dire à la
        #    gate « écart 97 — SOUS le repère 24 ». Une gate d'HONNÊTETÉ qui
        #    énonce une fausseté dans sa propre sortie : c'est le défaut de
        #    famille de cette story, commis par l'outil qui la garde.
        rep24 = re.search(r"#define DN_CONTRASTE_REPERE\s+(\d+)", c)
        seuil = int(rep24.group(1)) if rep24 else 24
        ctrl(rep24 is not None,
             "…et le repère est RELU du firmware, ⛔ pas écrit ici",
             "DN_CONTRASTE_REPERE = %d" % seuil)
        print("        ⚠️ écart %d — %s le repère %d emprunté à `bloc_gris`, qui"
              % (e, "SOUS" if e < seuil else "AU-DESSUS DE", seuil))
        print("           gouverne LES TROIS GRIS DE RÉGIME entre eux et ⛔ ne se")
        print("           transpose pas. Éprouvé À L'ŒIL sur la carte le 2026-08-31")
        print("           (« oui, une barre vert foncé ») ⇒ FAIT CONSIGNÉ, ⛔ pas")
        print("           un défaut ouvert. Seul l'écart NUL est un rouge ici.")
        print("        ⛔ ET « écart NUL » NE VEUT PAS DIRE « même couleur » : il se")
        print("           calcule sur une LUMINANCE. La certitude, c'est l'égalité")
        print("           des TROIS CANAUX — vérifiée par `contraste_bande_paire`.")


def bloc_latence(py, inj):
    """AC7 — LA DISPERSION AVANT TOUT DELTA."""
    print("\n── AC7 : la latence publie sa dispersion, et refuse le delta ───")
    vd = corps_python(py, "def verdict_delta(")
    ctrl(vd is not None, "`verdict_delta()` existe", "")
    vd = vd or ""
    ctrl("LATENCE_FENETRES_MIN" in vd and "REFUS" in vd,
         "🔴 …et il REFUSE un delta sur UNE fenêtre",
         "⛔ pas un commentaire déconseillant")
    ctrl("chevauche" in vd,
         "…et il refuse aussi deux étendues qui SE CHEVAUCHENT",
         "le delta serait dans le bruit")
    ctrl("dn4-2" in vd,
         "AC7.4 : la conséquence rétroactive NOMME `dn4-2`",
         "ses écarts sur fenêtre unique aussi")
    d = corps_python(py, "def dispersion(")
    ctrl(d is not None and "etendue" in (d or "") and "ecart_type" in (d or ""),
         "`dispersion()` publie étendue ET écart-type",
         "⛔ jamais une moyenne seule")
    ctrl(re.search(r"(?i)225/225.{0,300}(DÉMOLIE|demolie)", py, re.S) is not None,
         "AC7.3 : la règle réfutée est ÉCRITE comme réfutée",
         "la 5ᵉ fenêtre l'a démolie")
    ctrl(re.search(r"(?i)(RÉFUTÉ|REFUTE).{0,200}(tas LVGL|fragmentation)",
                   py, re.S) is not None,
         "AC7.5 : les deux hypothèses réfutées sont NOMMÉES",
         "⛔ ne pas les rejouer")
    mn = corps_python(inj, "def main(") or ""
    ctrl("--latence exige --firmware" in mn or
         ("a.latence and not a.firmware" in mn),
         "…et `--latence` EXIGE `--firmware`",
         "un relevé sans binaire ne se compare à rien")
    ctrl("campagne_latence(" in mn,
         "…et la campagne joue N fenêtres CONSÉCUTIVES", "")


def bloc_latence_execute(racine):
    """🔴 AC7.2 **EXÉCUTÉ**, ⛔ PAS LU.

    LE MUTANT QUI A OUVERT CE BLOC : `LATENCE_FENETRES_MIN = 1` passait la gate
    en VERT. Les contrôles d'AC7 étaient TEXTUELS — ils vérifiaient que le refus
    est ÉCRIT, pas qu'il a lieu. ⛔ *« Demande-toi de chaque ligne : qu'est-ce
    qui la ferait rougir ? »* — celles-là, rien.
    ⇒ On IMPORTE le pilote de l'arbre sous test et on lui POSE la question.
    """
    print("\n── AC7 : le refus du delta, EXÉCUTÉ sur l'arbre sous test ──────")
    prog = (
        "import sys; sys.path.insert(0, 'tools'); import dn_console as d\n"
        "u = d.dispersion([10]); v = d.dispersion([300, 310, 305, 299])\n"
        "r1, _ = d.verdict_delta(u, v)\n"
        "r2, _ = d.verdict_delta(d.dispersion([86, 138, 220, 86, 260]),\n"
        "                        d.dispersion([90, 250, 130]))\n"
        "r3, _ = d.verdict_delta(d.dispersion([10, 12, 11, 13, 10]),\n"
        "                        d.dispersion([300, 310, 305, 299, 302]))\n"
        "print('R', int(r1), int(r2), int(r3))\n")
    import tempfile
    fd, chemin = tempfile.mkstemp(suffix=".py")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(prog)
        rc, out = joue([chemin], racine)
    finally:
        os.unlink(chemin)
    m = re.search(r"^R (\d) (\d) (\d)$", out, re.M)
    ctrl(m is not None, "le pilote sous test s'importe et répond",
         (out.strip().splitlines() or ["rc=%d" % rc])[-1][:30])
    if m:
        ctrl(m.group(1) == "0",
             "🔴 UNE fenêtre, étendues DISJOINTES ⇒ REFUSÉ",
             "⛔ le chevauchement ne rattrape pas ce cas")
        ctrl(m.group(2) == "0",
             "🔴 étendues qui SE CHEVAUCHENT ⇒ REFUSÉ", "delta dans le bruit")
        ctrl(m.group(3) == "1",
             "✅ …et un delta LISIBLE reste recevable",
             "⛔ une gate qui refuse tout ne garde rien")


def bloc_temoin_pilote(racine):
    print("\n── LE TÉMOIN DU PILOTE, JOUÉ (⛔ pas supposé) ──────────────────")
    rc, out = joue(["tools/dn_console.py", "--temoin-negatif"], racine)
    ctrl(rc == 0 and re.search(r"BILAN : \d+ OK, 0 KO", out) is not None,
         "🔴 `dn_console.py --temoin-negatif` PASSE",
         (out.strip().splitlines() or ["rc=%d" % rc])[-1][:30])
    # ⛔ Et il doit être NON TRIVIAL : un témoin à 3 contrôles ne prouve rien.
    m = re.search(r"BILAN : (\d+) OK", out)
    ctrl(m is not None and int(m.group(1)) >= 20,
         "…et il joue au moins 20 contrôles",
         "%s contrôles" % (m.group(1) if m else "?"))


# ═══════════════════════════════════════════════════════════════════════════
# AC8.6 — LES MUTANTS : **CETTE GATE A ÉTÉ VUE ROUGIR**
# ═══════════════════════════════════════════════════════════════════════════
#
# 🔴 *« Une gate qu'aucun test n'a vue échouer est décorative »*. ⛔ Et un
#    `N OK / 0 KO` peut épingler du code FAUX — mesuré TROIS fois sur cette base
#    de code. La falsification vit donc DANS la gate, ⛔ pas dans un compte rendu
#    qu'on ne rejoue jamais.
#
# Chaque mutant remet le défaut D'ORIGINE de son AC, sur un ARBRE COPIÉ (⛔ le
# dépôt n'est jamais modifié), et la gate doit **sortir en 1**.
FICHIERS_MUTABLES = (
    "tools/dn_console.py",
    "tools/dn_injecteur.py",
    # 🔴 AJOUTÉE PAR LA REVUE DU 2026-08-31 — **LA GATE SE MUTE ELLE-MÊME.**
    #    Trois de ses défauts (commentaires lus comme du code imprimé, un seul
    #    littéral par `printf`, `36 675` jamais cherché) la laissaient VERTE sur
    #    le défaut qu'elle nomme. Aucun mutant ne pouvait le montrer tant qu'elle
    #    n'était pas dans cette liste — et tant que le mutant jouait la gate
    #    D'ORIGINE au lieu de la COPIE (voir `jouer_mutants`).
    "tools/verif_instruments_dn423.py",
    "firmware/desknode/main/dn_console.c",
    "firmware/desknode/main/dn_widget.c",
    "firmware/desknode/main/dn_link.c",
    "firmware/desknode/main/dn_ui.c",
)

MUTANTS = (
    ("AC1", "le motif REPL universel est retiré de la table",
     "tools/dn_console.py",
     '    ("REPL: commande inconnue", re.compile(r"Unrecognized command")),\n',
     ""),
    ("AC1", "un refus n'arme plus le code de retour",
     "tools/dn_console.py",
     'if r["refus"] and not refus_tolere(\n',
     'if False and not refus_tolere(\n'),
    ("AC2", "le compteur de lignes est retiré du firmware",
     "firmware/desknode/main/dn_console.c",
     'printf("--- fin : %u lignes emises%s ---\\n", (unsigned)n,',
     'printf("fin%s%s\\n", "", (const char *)'),
    ("AC2", "l'hôte ne distingue plus la PERTE",
     "tools/dn_console.py",
     '        r["etat"] = "PERTE"',
     '        r["etat"] = "OK"'),
    ("AC3", "le jeu « variable » redevient FIXE (rampe plate)",
     "tools/dn_injecteur.py",
     '"cpu": [(30, 1000, 7), (20, 57, 11), (30, 1000, 13), (300, 900, 17)],\n'
     '    "gpu": [(0, 1000, 19)',
     '"cpu": [(30, 30, 7), (20, 57, 11), (30, 1000, 13), (300, 900, 17)],\n'
     '    "gpu": [(0, 1000, 19)'),
    ("AC4", "`vTaskDelay` est réintroduit dans `cpu_delta`",
     "firmware/desknode/main/dn_console.c",
     "    UBaseType_t capacite = uxTaskGetNumberOfTasks() + 8;\n"
     "    TaskStatus_t *apres = calloc(capacite, sizeof(TaskStatus_t));",
     "    vTaskDelay(pdMS_TO_TICKS(1000));\n"
     "    UBaseType_t capacite = uxTaskGetNumberOfTasks() + 8;\n"
     "    TaskStatus_t *apres = calloc(capacite, sizeof(TaskStatus_t));"),
    ("AC5", "une constante de géométrie est replantée dans une consigne",
     "firmware/desknode/main/dn_console.c",
     'printf("   delta vaut %u flushes pour UN SEUL cycle (et %u x %d px,\\n",',
     'printf("   delta vaut %u flushes pour UN SEUL cycle (et %u x 35 100 px,%d\\n",'),
    ("AC6", "l'avertissement `veille off` est retiré de `widget piste`",
     "firmware/desknode/main/dn_console.c",
     '        printf("⛔ SI LA CARTE EST EN VEILLE : `veille off` D\'ABORD. Une scene\\n");\n'
     '        printf("   reconstruite en Ambient pose la jauge 27 px TROP HAUT, et\\n");\n'
     '        printf("   AUCUN compteur ne le dit (ledger, 2026-08-29).\\n");\n'
     '        /* 🔴 dn4-23 / AC6.1 — LE RENVOI ETAIT MORT.',
     '        /* 🔴 dn4-23 / AC6.1 — LE RENVOI ETAIT MORT.'),
    ("AC6", "le verdict de contraste disparaît de `veille case`",
     "firmware/desknode/main/dn_console.c",
     "        verdict_contraste();\n        return 0;\n    }\n\n    if (strcmp(argv[1], \"unite\")",
     "        return 0;\n    }\n\n    if (strcmp(argv[1], \"unite\")"),
    ("AC6", "la piste par défaut retombe sur l'aplat (écart NUL)",
     "firmware/desknode/main/dn_widget.c",
     "#define W_COL_PISTE_DEFAUT 0x141820",
     "#define W_COL_PISTE_DEFAUT 0x000000"),
    ("AC7", "un delta sur UNE SEULE fenêtre redevient publiable",
     "tools/dn_console.py",
     "LATENCE_FENETRES_MIN = 2",
     "LATENCE_FENETRES_MIN = 1"),
    # ══ LES DÉFAUTS TROUVÉS PAR LA REVUE DE CODE DU 2026-08-31 ═══════════════
    #    ⛔ Chacun de ceux-là était PRÉSENT dans l'arbre livré pendant que la
    #    gate imprimait `107 OK / 0 KO`. Les remettre est la seule preuve que
    #    la correction tient.
    ("RC1", "le compteur redevient une SOMME SIGNÉE (surplus structurel)",
     "firmware/desknode/main/dn_console.c",
     "    s_lignes_cmd += (unsigned)lignes;\n    s_fin_de_ligne = true;",
     "    (void)lignes;"),
    ("RC2", "`--no-wait` rescanne l'ÉCHO de la commande",
     "tools/dn_console.py",
     "        return _resultat(commande, brut, nettoyer(brut, commande), None)",
     "        return _resultat(commande, brut, brut.strip(), None)"),
    ("RC3", "`--no-wait` replafonne sa lecture à 2 s",
     "tools/dn_console.py",
     "        fin = time.monotonic() + timeout",
     "        fin = time.monotonic() + min(timeout, 2.0)"),
    ("RC4", "la carte se désavoue et le pilote ne le voit plus",
     "tools/dn_console.py",
     '    ("carte : verdict NON CRÉDIBLE",',
     '    ("carte : verdict JAMAIS VU",'),
    ("RC5", "`chercher_refus` re-déduplique par TEXTE (dégonfle)",
     "tools/dn_console.py",
     "                vus.append((nom, ligne.strip(), i))",
     "                vus.append((nom, ligne.strip(), i)) if not [\n"
     "                    x for x in vus if x[1] == ligne.strip()] else None"),
    ("RC6", "`cpu delta` réapparie par HANDLE seul (TCB recyclé)",
     "firmware/desknode/main/dn_console.c",
     "           && strncmp(a->pcTaskName, b->pcTaskName, configMAX_TASK_NAME_LEN) == 0;",
     "           && true;"),
    ("RC7", "le « PLAFOND » de l'ACTIF redevient une affirmation",
     "firmware/desknode/main/dn_console.c",
     '    printf("     — ⛔ ce n\'est NI un plafond NI un plancher, et le pire cas est\\n");',
     '    printf("     — (PLAFOND, fond noir pur)\\n");'),
    ("RC8", "`contraste_bande_paire` reconclut « même couleur » d'une luminance",
     "firmware/desknode/main/dn_console.c",
     "    if (ecart == 0 && meme_couleur) {",
     "    if (ecart == 0) {"),
    ("RC9", "`colonnes()` recompte des OCTETS DE TÊTE",
     "firmware/desknode/main/dn_console.c",
     "        int w = dn_cp_colonnes(cp);",
     "        int w = 1;"),
    ("RC10", "l'injecteur rejette la réponse de la carte",
     "tools/dn_injecteur.py",
     "            echo.extend(ser.read(ser.in_waiting or 0))",
     "            ser.read(ser.in_waiting or 0)"),
    ("RC11", "`--latence-delta` recompare deux STIMULI différents",
     "tools/dn_injecteur.py",
     "    if ecarts_stim:",
     "    if False:"),
    ("RC12", "la bannière récite à nouveau la prémisse RÉFUTÉE",
     "tools/dn_injecteur.py",
     '    print("[injecteur]    0,005 corruption/s contre 0,54 /s sous agent réel — "',
     '    print("[injecteur]    94 645 contre 128 613, soit 36 % de moins — "'),
    # ⛔ CES DEUX-LÀ **PLANTENT LE DÉFAUT** dans le firmware au lieu de
    #    désactiver le contrôle : un mutant qui débranche la garde ne prouve que
    #    l'existence de la garde ; un mutant qui remet la faute prouve qu'elle
    #    l'ATTRAPE. (Les deux versions ont été jouées : la première restait
    #    VERTE, parce qu'aucun fichier livré n'exerçait le chemin.)
    ("RC13", "une AIRE RÉCITÉE est replantée dans un littéral de CONTINUATION",
     "firmware/desknode/main/dn_console.c",
     '        printf("cadence de la barre : %s\\n",',
     '        printf("verifier le delta de\\n"\n'
     '               "   6 x 35 100 px sur la scene livree\\n");\n'
     '        printf("cadence de la barre : %s\\n",'),
    ("RC14", "la gate ne lit à nouveau QUE le premier littéral",
     "tools/verif_instruments_dn423.py",
     '        morceaux = re.findall(r\'"((?:[^"\\\\]|\\\\.)*)"\', m.group(1))\n'
     "        out.append(\"\".join(morceaux))",
     '        morceaux = re.findall(r\'"((?:[^"\\\\]|\\\\.)*)"\', m.group(1))\n'
     "        out.append(morceaux[0] if morceaux else \"\")"),
    ("RC15", "l'AUTRE aire (`36 675`) est replantée dans une consigne",
     "firmware/desknode/main/dn_console.c",
     '        printf("cadence de la barre : %s\\n",',
     '        printf("   verifier les 36 675 px de la case\\n");\n'
     '        printf("cadence de la barre : %s\\n",'),
)


def jouer_mutants(racine, sortie_pv):
    import shutil
    import tempfile
    lignes_pv = []

    def dire(t=""):
        print(t)
        lignes_pv.append(t)

    dire("=" * 78)
    dire("dn4-23 / AC8.6 — LES MUTANTS, VUS ROUGIR")
    dire("=" * 78)
    dire("⛔ Le dépôt n'est JAMAIS modifié : chaque mutant vit dans un arbre")
    dire("   COPIÉ, et la gate y est rejouée telle quelle.")
    dire("")
    moi = os.path.abspath(__file__)
    rc_ref, out_ref = joue([moi, "--racine", racine], racine)
    dire("TÉMOIN POSITIF — l'arbre LIVRÉ : rc=%d   %s"
         % (rc_ref, (out_ref.strip().splitlines() or ["?"])[-1]))
    if rc_ref != 0:
        dire("⛔ L'arbre livré n'est pas vert : ⛔ aucun mutant n'est concluant.")
        # 🔴 REVUE DU 2026-08-31 — `os.makedirs` N'EXISTAIT QUE SUR LE CHEMIN
        #    NOMINAL, plus bas. Sur un clone frais (pas de `mesures/dn4-23/`)
        #    dont l'arbre est DÉJÀ ROUGE, cette branche sortait en
        #    `FileNotFoundError` au lieu de produire le rapport qu'elle est
        #    écrite pour produire — l'outil plantait exactement quand il avait
        #    quelque chose à dire.
        os.makedirs(os.path.dirname(sortie_pv) or ".", exist_ok=True)
        with open(sortie_pv, "w", encoding="utf-8") as f:
            f.write("\n".join(lignes_pv) + "\n")
        return 1
    dire("")
    n_ok = n_rate = 0
    for ac, quoi, fichier, avant, apres in MUTANTS:
        tmp = tempfile.mkdtemp(prefix="dn423-mutant-")
        try:
            for rel in FICHIERS_MUTABLES:
                dst = os.path.join(tmp, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy(os.path.join(racine, rel), dst)
            cible = os.path.join(tmp, fichier)
            with open(cible, encoding="utf-8") as f:
                txt = f.read()
            if txt.count(avant) != 1:
                dire("[RATÉ ] %-4s %-52s ancre introuvable (%d)"
                     % (ac, quoi, txt.count(avant)))
                n_rate += 1
                continue
            with open(cible, "w", encoding="utf-8") as f:
                f.write(txt.replace(avant, apres, 1))
            # 🔴 REVUE DU 2026-08-31 — LE MUTANT JOUAIT LA GATE **D'ORIGINE**
            #    contre l'arbre muté. Un défaut planté DANS LA GATE était donc
            #    structurellement invisible : c'est pour ça que ses trois trous
            #    ont survécu à `11 mutants vus rougir`. Quand la cible EST la
            #    gate, on joue LA COPIE.
            gate = os.path.join(tmp, "tools/verif_instruments_dn423.py") \
                if fichier.endswith("verif_instruments_dn423.py") else moi
            rc, out = joue([gate, "--racine", tmp], tmp)
            kos = [l.strip() for l in out.splitlines() if "[KO ]" in l]
            bilan = ([l for l in out.splitlines() if l.startswith("BILAN")]
                     or ["(pas de bilan)"])[-1]
            a_bilan = any(l.startswith("BILAN") for l in out.splitlines())
            if rc == 1 and kos:
                dire("[ROUGE] %-4s %-52s rc=1  %s" % (ac, quoi, bilan))
                for k in kos[:3]:
                    dire("          ↳ %s" % k[:96])
                if len(kos) > 3:
                    dire("          ↳ … et %d autre(s)" % (len(kos) - 3))
                n_ok += 1
            elif not a_bilan:
                # 🔴 REVUE DU 2026-08-31 — UNE GATE QUI **PLANTE** ÉTAIT
                #    RAPPORTÉE `[VERT!] CE CONTRÔLE NE GARDE RIEN`. C'est un
                #    FAUX DIAGNOSTIC SUR UN CRASH : le contrôle n'a pas laissé
                #    passer le défaut, il n'a pas pu s'exécuter. Confondre les
                #    deux envoie chercher au mauvais endroit — et c'était
                #    atteignable (une source illisible faisait échapper
                #    `UnicodeDecodeError` hors de `lire()`).
                dire("[PLANTE] %-4s %-52s rc=%d — ⛔ NI KO NI BILAN"
                     % (ac, quoi, rc))
                dire("          ⛔ La gate n'a pas CONCLU : elle a ERRÉ. ⛔ Ce")
                dire("             n'est PAS « le contrôle ne garde rien ».")
                for l in (out.strip().splitlines() or [""])[-2:]:
                    dire("          ↳ %s" % l[:96])
                n_rate += 1
            else:
                dire("[VERT!] %-4s %-52s rc=%d  %s" % (ac, quoi, rc, bilan))
                dire("          ⛔ CE CONTRÔLE NE GARDE RIEN — le défaut passe.")
                n_rate += 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    dire("")
    dire("BILAN MUTANTS : %d vus ROUGIR, %d non concluant(s) sur %d"
         % (n_ok, n_rate, len(MUTANTS)))
    dire("⛔ CE QUE CE PV NE PROUVE PAS : que la gate attrape TOUS les défauts.")
    # 🔴 REVUE DU 2026-08-31 — « ces ONZE-LÀ » ÉTAIT ÉCRIT EN DUR ICI, et mon
    #    propre ajout de mutants l'a périmé sur-le-champ. Un compte récité dans
    #    l'outil qui installe « relire, ⛔ pas réciter » : le compte est RELU.
    dire("   Il prouve que chacun de ces %d-là ne passe plus. Une gate se juge"
         % len(MUTANTS))
    dire("   à ce qu'elle a été vue REFUSER, ⛔ pas à son compte de contrôles.")
    os.makedirs(os.path.dirname(sortie_pv), exist_ok=True)
    with open(sortie_pv, "w", encoding="utf-8") as f:
        f.write("\n".join(lignes_pv) + "\n")
    print("\nPV écrit : %s" % sortie_pv)
    return 0 if n_rate == 0 else 1


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("--racine", default=None,
                   help="jouer sur un ARBRE MUTÉ (production du PV des mutants)")
    p.add_argument("--mutants", action="store_true",
                   help="AC8.6 — remet le défaut d'origine de chaque AC sur un "
                        "arbre COPIÉ et EXIGE que la gate sorte en 1. ⛔ Le "
                        "dépôt n'est jamais modifié.")
    p.add_argument("--pv", default=None, metavar="FICHIER",
                   help="où écrire le PV des mutants "
                        "(défaut : mesures/dn4-23/T8-mutants.txt)")
    a = p.parse_args()
    racine = a.racine or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if a.mutants:
        return jouer_mutants(
            racine,
            a.pv or os.path.join(racine, "mesures", "dn4-23", "T8-mutants.txt"))

    print("=" * 78)
    print("dn4-23 / AC8 — LES INSTRUMENTS DE LA CONSOLE, GARDÉS SUR LES DEUX ÉTAGES")
    print("=" * 78)
    print("  racine : %s" % racine)

    py = lire(os.path.join(racine, "tools", "dn_console.py"))
    inj = lire(os.path.join(racine, "tools", "dn_injecteur.py"))
    c = lire(os.path.join(racine, "firmware", "desknode", "main", "dn_console.c"))
    w = lire(os.path.join(racine, "firmware", "desknode", "main", "dn_widget.c"))
    ui = lire(os.path.join(racine, "firmware", "desknode", "main", "dn_ui.c"))
    wifi_h = lire(os.path.join(racine, "firmware", "desknode", "main", "dn_wifi.h"))
    if None in (py, inj, c, w, ui, wifi_h):
        print("\nBILAN : %d OK, %d KO" % (OK[0], KO[0]))
        return 1

    bloc_refus(py)
    bloc_completude(py, c)
    bloc_miroir(py, c)
    bloc_injecteur(racine, inj)
    bloc_cpu(c)
    bloc_sorties(c)
    bloc_leviers(c, w)
    bloc_revue_firmware(c, ui, wifi_h)
    bloc_auto_epreuve()
    bloc_latence(py, inj)
    bloc_latence_execute(racine)
    bloc_temoin_pilote(racine)

    # ── dn4-40 / AC40.6.b — L'EXTRACTION NE SUR-AFFIRME PLUS ───────────────
    print("\n── dn4-40 / AC40.6 — L'EXTRACTION DIT CE QU'ELLE PROUVE ──────────")
    print("     ⚠️ Trouver un corps prouve QU'UNE fermeture a profondeur 0 a été")
    print("        vue. ⛔ Ça ne prouve PAS que c'était LA BONNE : une signature")
    print("        ambiguë rend un corps parfaitement équilibré — celui d'un")
    print("        AUTRE. C'est ce que ce contrôle-ci ferme.")
    absentes = [sig for sig, n in extractions if n == 0]
    ambigues = [(sig, n) for sig, n in extractions if n > 1]
    print("     %d extraction(s) · %d signature(s) distincte(s)"
          % (len(extractions), len({s_ for s_, _ in extractions})))
    # ⚠️ Le `ctrl()` de cette gate n'a QU'UN champ de detail (le correctif a
    #    deux champs vit dans les gates du ledger et du dossier). On compose
    #    donc le detail ici — ⛔ un KO n'imprime pas la justification du VERT.
    ctrl(not absentes,
         "toute signature d'extraction est TROUVÉE dans sa source",
         ("%d extraction(s), 0 signature absente" % len(extractions))
         if not absentes else
         ("⛔ %d ABSENTE(S) : %s"
          % (len(absentes), " · ".join(repr(x[:44]) for x in absentes[:4]))))
    ctrl(not ambigues,
         "toute signature d'extraction désigne UNE seule fonction",
         ("%d extraction(s) — ⛔ aucune signature n'apparaît deux fois"
          % len(extractions)) if not ambigues else
         ("⛔ %d AMBIGUË(S) : %s"
          % (len(ambigues), " · ".join("%r ×%d" % (x[:40], n)
                                       for x, n in ambigues[:4]))))

    print("\n" + "=" * 78)
    print("⛔ CE QUE CETTE GATE NE SOLDE PAS, ET C'EST ÉCRIT : elle ne parle pas à")
    print("   la carte. Elle prouve que les INSTRUMENTS ne peuvent plus conclure")
    print("   sur du vide — ⛔ pas qu'une perte réelle a été attrapée, ⛔ pas que le")
    print("   jeu variable atteint le régime réel, ⛔ pas que le contraste est")
    print("   lisible à l'œil. Ces cinq constats-là se tirent EN SÉANCE.")
    print("BILAN : %d OK, %d KO" % (OK[0], KO[0]))
    return 0 if KO[0] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

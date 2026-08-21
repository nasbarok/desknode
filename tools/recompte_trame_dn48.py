#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""recompte_trame_dn48.py — recompte le PIRE CAS de trame, et garde le MIROIR.

🔴 IL FAIT DEUX CHOSES, ET LA SECONDE EST LA PLUS UTILE.

1. IL RECOMPTE LE PIRE CAS **CARACTERE PAR CARACTERE**, en construisant la trame
   avec `dn_agent.trame()` — ⛔ pas en additionnant des longueurs a la main. Un
   comptage a la main est exactement ce que dn4-6 a refuse de faire.

2. 🎯 IL COMPARE `k_metriques[]` (firmware) A `BORNES` (agent). Ces deux tables
   sont RECOPIEES l'une de l'autre, ⛔ pas derivees — le fil n'a pas de canal de
   negociation. Le depot l'assume et l'ecrit : « les deux tables bougent dans le
   MEME geste ». ⚠️ Mais le SEUL temoin de la derive etait jusqu'ici
   `rejets_bornes` qui monte **cote carte**, donc APRES un flash et une seance.
   ⇒ Ce controle-la se joue en WSL, en une seconde, AVANT la seance.

⛔ CE QU'IL NE PROUVE PAS : que le firmware compile, que la carte recoit, ni
   qu'une grandeur bouge. Il compare des TABLES et compte des OCTETS.

Usage :  python3 tools/recompte_trame_dn48.py
Sortie : 0 si tout concorde, 1 sinon.
"""
import io
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ⚠️ Le stub n'est arme que si le VRAI psutil manque — sinon cet outil masquerait
#    le vrai module dans son propre processus, y compris SUR LA TOUR ou il existe.
#    (revue dn4-8, 2026-08-21 ; meme correctif que `verif_source_lhm_dn48.py`)
try:
    import psutil as _vrai_psutil  # noqa: F401
    _AVEC_VRAI_PSUTIL = True
except ImportError:
    _AVEC_VRAI_PSUTIL = False
if not _AVEC_VRAI_PSUTIL:
    os.environ["DN_STUB_PSUTIL"] = "1"
# \U0001f534 DEFAUT D'INSTRUMENT MESURE LE 2026-08-21, ET IL EST GENERAL A TOUT HARNAIS
#    QUI IMPORTE LE PRODUIT : **PYTHON A SERVI UN BYTECODE PERIME**. Pendant un
#    test de mutation (BORNES 1500 -> 1400 puis restauration), `agent/__pycache__/
#    dn_agent.cpython-312.pyc` a continue de rendre `1400` alors que le `.py` sur
#    le disque disait `1500` — l'outil a donc VERIFIE UN FICHIER QUI N'EXISTAIT
#    PLUS, et il a conclu ROUGE sur un arbre SAIN. ⚠️ Dans l'autre sens il aurait
#    conclu VERT sur un arbre CASSE : c'est la famille « un instrument qui ne peut
#    pas voir ce qu'il pretend lire », et ce depot l'a deja payee (le `head` d'un
#    tube pour `exit 0`, le journal PowerShell en UTF-16LE).
# ⇒ DEUX PARADES, ET LA SECONDE EST LA VRAIE :
#    1. on n'ecrit ni ne lit de bytecode ici, et on purge celui qui traine ;
#    2. \U0001f3af **L'OUTIL PUBLIE L'EMPREINTE DE LA SOURCE QU'IL A REELLEMENT LUE.**
#       Un instrument qui ne nomme pas son sujet ne prouve rien sur ce sujet.
import hashlib
import shutil

sys.dont_write_bytecode = True
for _p in (os.path.join(RACINE, "agent", "__pycache__"),
           os.path.join(RACINE, "tools", "stub_psutil", "__pycache__")):
    shutil.rmtree(_p, ignore_errors=True)

_SRC_AGENT = os.path.join(RACINE, "agent", "dn_agent.py")
_SHA_AGENT = hashlib.sha256(
    io.open(_SRC_AGENT, "rb").read()).hexdigest()[:16]
# ⛔ chemin du stub prepend UNIQUEMENT s'il est arme : sinon il masquerait le vrai
#    psutil ET leverait ImportError (le stub refuse de se charger sans la variable).
if not _AVEC_VRAI_PSUTIL:
    sys.path.insert(0, os.path.join(RACINE, "tools", "stub_psutil"))
sys.path.insert(0, os.path.join(RACINE, "agent"))
import dn_agent  # noqa: E402  -- LE PRODUIT

LINK_C = os.path.join(RACINE, "firmware", "desknode", "main", "dn_link.c")
LINK_H = os.path.join(RACINE, "firmware", "desknode", "main", "dn_link.h")

ECHECS = []


def dire(ok, quoi, detail=""):
    print("  [%s] %-56s %s" % ("OK " if ok else "\u2716\ufe0f ", quoi, detail))
    if not ok:
        ECHECS.append(quoi)


def constante(nom):
    """Lit un `#define <nom> <entier>` dans `dn_link.h`. ⛔ Pas une valeur recopiee."""
    src = io.open(LINK_H, encoding="utf-8").read()
    m = re.search(r"^#define\s+%s\s+(\d+)\s*$" % re.escape(nom), src, re.M)
    if not m:
        sys.exit("\u26d4 `%s` introuvable dans dn_link.h — ⛔ ne PAS supposer sa "
                 "valeur : c'est elle qu'on verifie." % nom)
    return int(m.group(1))


def k_metriques():
    """Extrait `k_metriques[]` de `dn_link.c`.

    ⚠️ C'est un parseur de C par expression reguliere, donc FRAGILE — et il le
       DIT : s'il ne retrouve pas exactement `DN_LINK_METRIQUES` entrees, il
       s'arrete. ⛔ Un parseur permissif qui rend 3 metriques sur 5 conclurait
       « tout concorde » sur ce qu'il a su lire.
    """
    src = io.open(LINK_C, encoding="utf-8").read()
    dep = src.index("k_metriques[DN_LINK_METRIQUES] = {")
    corps = src[dep:src.index("\n};", dep)]
    out = {}
    for m in re.finditer(
            r"\[DN_LINK_M_\w+\]\s*=\s*\{\s*\"(\w+)\"\s*,\s*(\d+)\s*,"
            r"\s*\{([^}]*)\}", corps):
        nom, n, plaf = m.group(1), int(m.group(2)), m.group(3)
        vals = [int(x) for x in re.findall(r"(\d+)u", plaf)]
        out[nom] = (n, vals)

    # 🔴 LA GARDE QUE LA DOCSTRING PROMETTAIT — ELLE N'EXISTAIT PAS.
    #    Defaut trouve en revue (code review dn4-8, 2026-08-21) : le texte disait
    #    « s'il ne retrouve pas exactement `DN_LINK_METRIQUES` entrees, IL
    #    S'ARRETE », mais la fonction ne lisait JAMAIS cette constante et ne
    #    comptait rien — elle rendait ce que `re.finditer` avait bien voulu
    #    trouver. Le controle `sorted(fw) == sorted(ag)` ne rattrapait le cas que
    #    par accident, parce que `BORNES` est complete ; si les DEUX tables
    #    perdaient une metrique dans la meme edition — LE defaut pour lequel ce
    #    miroir existe — l'outil aurait imprime « ✅ les deux tables concordent ».
    # ⚠️ `DN_LINK_METRIQUES` est un membre d'ENUM (dn_link.h), ⛔ pas un `#define` :
    #    on compte les membres de l'enumeration qui le precedent.
    attendu = _n_metriques_enum()
    if len(out) != attendu:
        sys.exit(
            "\u26d4 PARSEUR ARRETE : %d entree(s) extraite(s) de `k_metriques[]` "
            "pour %d annoncee(s) par l'enum `DN_LINK_METRIQUES`.\n"
            "   \u26d4 NE PAS CONCLURE SUR CE QUI A ETE LU : un parseur de C par "
            "regex qui rate une entree ferait dire « tout concorde » a un arbre "
            "incoherent.\n   entrees vues : %s"
            % (len(out), attendu, sorted(out)))
    return out


def _n_metriques_enum():
    """Le nombre de metriques, COMPTE dans l'enum de `dn_link.h`.

    ⛔ `DN_LINK_METRIQUES` n'est pas un `#define` : c'est le membre terminal de
       l'enumeration `dn_link_metrique_t`. On compte donc les membres `DN_LINK_M_*`
       qui le precedent, ⛔ on ne recopie pas 5 ici.
    """
    src = io.open(LINK_H, encoding="utf-8").read()
    m = re.search(r"typedef\s+enum\s*\{(.*?)\}\s*dn_link_metrique_t\s*;",
                  src, re.S)
    if not m:
        sys.exit("\u26d4 enum `dn_link_metrique_t` introuvable dans %s" % LINK_H)
    membres = re.findall(r"\bDN_LINK_M_\w+", m.group(1))
    if not membres:
        sys.exit("\u26d4 aucun membre `DN_LINK_M_*` dans l'enum de %s" % LINK_H)
    return len(membres)


def main():
    for f in (sys.stdout, sys.stderr):
        try:
            f.reconfigure(encoding="utf-8")
        except Exception:
            pass
    print("=" * 78)
    print("dn4-8 / AC5 — RECOMPTE DU PIRE CAS + GARDE DU MIROIR k_metriques[] <-> BORNES")
    print("source verifiee : agent/dn_agent.py sha256:%s" % _SHA_AGENT)
    print("=" * 78)

    LIGNE_MAX = constante("DN_LINK_LIGNE_MAX")
    GRAND_MAX = constante("DN_LINK_GRANDEURS_MAX")
    REPL = constante("DN_LINK_REPL_LIGNE_MESUREE")
    fw = k_metriques()
    ag = dn_agent.BORNES

    print("\n-- 1. LE MIROIR --")
    dire(sorted(fw) == sorted(ag), "les deux tables portent les MEMES metriques",
         "%s / %s" % (sorted(fw), sorted(ag)))
    for nom in sorted(set(fw) & set(ag)):
        n, plaf = fw[nom]
        dire(n == len(plaf), "%-5s : n_grandeurs == nb de plafonds declares" % nom,
             "n=%d plafonds=%s" % (n, plaf))
        dire(plaf == ag[nom],
             "%-5s : plafonds firmware == plafonds agent" % nom,
             "fw=%s ag=%s" % (plaf, ag[nom]))
        dire(n <= GRAND_MAX, "%-5s : tient dans DN_LINK_GRANDEURS_MAX" % nom,
             "%d <= %d" % (n, GRAND_MAX))

    print("\n-- 2. LE PIRE CAS, CARACTERE PAR CARACTERE (plafonds REELS) --")
    pire_r, qui_r = 0, None
    for nom in sorted(fw):
        _n, plaf = fw[nom]
        t = dn_agent.trame(4294967295, 4294967295, nom, plaf).rstrip("\n")
        print("     %-5s %3d o  %s" % (nom, len(t), t))
        if len(t) > pire_r:
            pire_r, qui_r = len(t), nom

    print("\n-- 3. LE PIRE CAS AU GABARIT (convention dn4-6 : %d x 1000000) --"
          % GRAND_MAX)
    pire_g, qui_g = 0, None
    for nom in sorted(fw):
        n, _plaf = fw[nom]
        if n < GRAND_MAX:
            continue                      # ⛔ un gabarit ne se joue qu'a plein
        t = dn_agent.trame(4294967295, 4294967295, nom,
                           [1000000] * GRAND_MAX).rstrip("\n")
        print("     %-5s %3d o  %s" % (nom, len(t), t))
        if len(t) > pire_g:
            pire_g, qui_g = len(t), nom

    print("\n-- 4. L'INVARIANT --")
    dire(pire_r <= LIGNE_MAX, "pire cas ATTEIGNABLE <= DN_LINK_LIGNE_MAX",
         "%s = %d o (max %d, marge %d)" % (qui_r, pire_r, LIGNE_MAX,
                                           LIGNE_MAX - pire_r))
    # 🔴 UN INVARIANT SATISFAIT PAR RIEN N'EST PAS SATISFAIT (revue 2026-08-21).
    #    La boucle du gabarit saute toute metrique avec `n < GRAND_MAX` ; si
    #    AUCUNE n'atteint le plafond, `pire_g` reste 0 et `qui_g` reste `None`, et
    #    ce controle imprimait « ✅ None = 0 o (max 71, marge 71) » — vert, sur un
    #    ensemble VIDE. C'est l'invariant qui DIMENSIONNE `DN_LINK_LIGNE_MAX`.
    dire(qui_g is not None,
         "au moins UNE metrique atteint le gabarit (sinon rien n'est verifie)",
         "%s" % (qui_g if qui_g else "\u26d4 AUCUNE : l'invariant ci-dessous ne "
                                     "porterait sur RIEN"))
    dire(qui_g is not None and pire_g <= LIGNE_MAX,
         "pire cas AU GABARIT <= DN_LINK_LIGNE_MAX",
         "%s = %d o (max %d, marge %d)" % (qui_g, pire_g, LIGNE_MAX,
                                           LIGNE_MAX - pire_g))
    # \U0001f534 « UN COMPTEUR DECORATIF EST UN INSTRUMENT QUI MENT » : la bande
    #    `LIGNE_MAX+1 .. REPL` doit rester ATTEIGNABLE, sinon `rejets_trop_longue`
    #    ne peut plus jamais s'incrementer et le diagnostic disparait EN SILENCE.
    bande = REPL - LIGNE_MAX
    dire(bande > 0, "la bande « COMPLETE mais trop longue » reste ATTEIGNABLE",
         "%d..%d = %d octets" % (LIGNE_MAX + 1, REPL, bande))
    dire(pire_g + len("pc ") <= REPL, "budget cote REPL",
         "%d + 3 = %d <= %d" % (pire_g, pire_g + 3, REPL))

    print("\n" + "=" * 78)
    if ECHECS:
        print("\u2716\ufe0f  %d CONTROLE(S) EN ECHEC : %s" % (len(ECHECS), ECHECS))
        return 1
    print("\u2705 les deux tables concordent et l'invariant tient.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

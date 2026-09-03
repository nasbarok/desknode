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

═══════════════════════════════════════════════════════════════════════════
 dn4-44 — CE QUE CETTE MARCHE A CHANGE. ⛔ Rien n'est efface.
═══════════════════════════════════════════════════════════════════════════

🔴 (1) ELLE A SON **T0** (AC4.2). Elle n'en avait AUCUN : son `rc` etait
   imprime nulle part et jete, et une gate MORTE faisait sortir un cas
   `INERTE` **vert gratuitement** (`bon = not atteint_propre` — une trace vide
   satisfait « jamais atteint »). Mesure du cadrage : **4 verdicts sur 13**
   sortaient `[OK]` sans qu'aucune gate n'ait tourne.

🔴 (2) UN LIBELLE INTROUVABLE AU SOURCE NE SORT PLUS **VERT** (AC5.3). Un
   `TROU`/`INERTE` dont le site avait disparu etait declare
   `[OK] REMEDE APPLIQUE` — et une **faute de frappe** dans le libelle
   produisait EXACTEMENT la meme sortie verte. Le remede se PROUVE desormais :
   le libelle doit SURVIVRE au source hors d'un `ctrl()`.

🔴 (3) LA LECTURE DES SITES ET DE LA TRACE PASSE PAR `dn_sites` / `dn_trace`
   (AC5.5, AC5.1) — la MEME que la campagne de mutants, et la cle porte son
   discriminant.

🔴 (4) LES DEUX `ctrl(True, …)` QUE `f4848e4` A LAISSES NON CLASSES SONT
   TRIES (AC1.4) — et ils ont impose une **QUATRIEME classe**, `BRANCHE`.

Usage :  python3 tools/campagne_ctrl_dn440.py [--cockpit CHEMIN]
"""
import argparse
import atexit
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI)
import dn_sites                                            # noqa: E402
import dn_trace                                            # noqa: E402
REL_LED = "_bmad-output/implementation-artifacts/deferred-work.md"
REL_TRK = "_bmad-output/implementation-artifacts/sprint-status-desknode.yaml"
REL_MAN = "_bmad-output/implementation-artifacts/dn4-16-arbitrage-ledger.md"
LVGL = "firmware/desknode/managed_components"


class MutationMorte(Exception):
    """Une mutation dont le motif est introuvable — ⛔ un REFUS, pas un rouge.

    🔴 AJOUTEE PAR LA REVUE DE CODE dn4-44 (2026-09-03). « Un mutant qui ne
    s'applique pas ne prouve RIEN » est la regle du depot ; elle etait tenue
    dans les gates (`MUTANT %d INAPPLICABLE`) et dans la campagne de mutants
    (garde AC5.2), ⛔ pas ici.
    """


# 🔴 REVUE DE CODE dn4-44 — HISSES AU NIVEAU MODULE. Ils vivaient dans
#    `main()`, donc ⛔ AUCUN banc ne pouvait les exercer : le T0 de cette
#    campagne — le correctif central d'AC4.2 — etait lui-meme garde par rien.
#    C'est le defaut que cette story existe pour compter, dans son instrument.
#
# ⚠️ CE QUE LE PREMIER TIR DU T0 A TROUVE, ET QUI A CORRIGE SON PROPRE CRITERE
#    — mesure du 2026-09-03. Ecrit `rc in (0, 1)`, le T0 declarait
#    `verif_hist_dn413.py` ININTERPRETABLE : elle rend **4** dans l'arbre
#    jetable. Verification faite : elle y joue ses **52** controles, 0 KO — le
#    `4` vient de son `.map`, un artefact de BUILD que `git archive` ne porte
#    pas. ⇒ `4` n'est PAS « la gate n'a pas tourne » : c'est « le terrain est
#    incomplet », et le contrat de gate le distingue justement.
#    ⛔ On ne l'avale pas en silence : il est IMPRIME, et le verdict d'un site
#      ne tient que s'il est ATTEINT et **VERT** au T0.
RC_INTERPRETABLES = (0, 1, 4)
RC_TERRAIN_INCOMPLET = 4

# 🔴 REVUE DE CODE dn4-44 (2026-09-03) — LE DISCRIMINANT « LA GATE A-T-ELLE
#    TOURNE ? », ET IL A FALLU DEUX ESSAIS POUR LE TROUVER. ⛔ Le premier
#    correctif exigeait une ligne `BILAN` : **il etait FAUX**, et la mesure l'a
#    dit tout de suite — une gate qui sort EN AMONT (prerequis absent, ou
#    `ctrl(False, …)` puis `return 1`) n'imprime PAS de bilan, et c'est
#    exactement ce qu'un `LEGITIME` doit faire. Ecrit ainsi, le correctif
#    faisait rougir 6 cas legitimes et rendait `verif_hist_dn413.py`
#    ININTERPRETABLE. ⛔ Ce n'est pas le bilan qui separe les deux.
# ⇒ CE QUI LES SEPARE EST LE **TRACEBACK** : une sortie en amont est un CHEMIN
#   DU PROGRAMME (stderr vide) ; un plantage est une exception non rattrapee.
#   C'est le cas mesure a la revue : une gate rendue **non compilable** rendait
#   `rc=1, 0 controle trace` ⇒ verdict `[OK] PROUVE`.
_TRACE_PY = "Traceback (most recent call last)"


def a_plante(rc, err):
    """La gate est-elle MORTE — ⛔ par opposition a « sortie en amont » ?"""
    return rc not in RC_INTERPRETABLES or _TRACE_PY in (err or "")


def t0_de(gate, cockpit, joueur=None):
    """Le T0 d'UNE gate : elle a tourne, et elle a rendu un verdict.

    Rend `(rc, vus, motif)` — `motif` non nul ⇒ campagne ININTERPRETABLE.

    ⚠️ `joueur` EXISTE POUR SON BANC (dn4-44 / AC5.7), ⛔ pas pour la
    production. Il permet de REPLANTER l'etat d'avant correctif — une gate qui
    plante, une trace vide — sans monter un arbre jetable par cas. ⛔ Il ne
    debranche rien : c'est la MEME fonction, sur des donnees fautives.
    """
    rc, vus, _out, err = (joueur or joue)(gate, m_rien, cockpit)
    motif = None
    if a_plante(rc, err):
        motif = ("rc=%d ⛔ la gate a PLANTE (hors {0,1,4}, ou exception non"
                 " rattrapee) — ⛔ elle n'est pas « sortie en amont »" % rc)
    elif not vus:
        motif = "⛔ AUCUN controle trace — la gate n'a pas tourne"
    return rc, vus, motif


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
    """Vide la POPULATION du site, ⛔ ne debranche pas la garde.

    ⚠️ REVUE 2026-09-03 — ELLE N'EST PLUS REFERENCEE PAR AUCUN CAS, et elle est
    GARDEE VOLONTAIREMENT : c'est la seule mutation qui sache vider une
    population sans debrancher sa garde. Le jour ou un site TROU est REPARE au
    lieu d'etre demonte en `print`, c'est elle qu'il faudra rebrancher. ⛔ Ne
    pas la supprimer sans lire le docstring de tete."""
    p = os.path.join(arbre, "firmware/desknode/main/dn_ui.c")
    s = io.open(p, encoding="utf-8").read()
    io.open(p, "w", encoding="utf-8").write(
        s.replace("DN_VERROU_EXEMPT", "DN_VERROU_ABSENT"))
    return []


def m_forme_cmake_incompilable(arbre, ck):
    """REPLANTE : le CMakeLists porte une regex que **Python refuse**.

    🎯 CMake et Python ne parlent pas le meme dialecte de regex. La gate LIT la
    regle dans le build plutot que de la recopier — c'est bien —, mais elle
    doit alors survivre a une regle qu'elle ne sait pas rejouer. Le `**` est
    accepte tel quel par CMake et leve `multiple repeat` chez Python.
    """
    p = os.path.join(arbre, "firmware/desknode/main/CMakeLists.txt")
    s = io.open(p, encoding="utf-8").read()
    t = s.replace('nom_complet MATCHES "^dn_font_[0-9]+',
                  'nom_complet MATCHES "^dn_font_[0-9]+**')
    # 🔴 REVUE DE CODE dn4-44 — UNE MUTATION QUI NE MORD PAS REND UN ROUGE AU
    #    MAUVAIS MOTIF. Si le motif bouge dans le build, le fichier etait
    #    reecrit A L'IDENTIQUE, la gate jouait un arbre SAIN, et le cas sortait
    #    `⛔ NON PROUVE` en accusant la CLASSIFICATION — alors que la mutation
    #    etait morte. La campagne sœur porte cette garde depuis AC5.2 ; ici
    #    elle n'avait aucun equivalent.
    if t == s:
        raise MutationMorte("le motif de regex du CMakeLists n'est plus la —"
                            " la mutation n'a RIEN change")
    io.open(p, "w", encoding="utf-8").write(t)
    return []


def m_bloc_refutation_non_ferme(arbre, ck):
    """REPLANTE : l'en-tete du bloc de refutation n'a plus de `*/` apres lui.

    🎯 On DEPLACE la ligne de marqueur en fin de fichier — ⛔ on ne supprime
    aucun `*/`, pour que le marqueur reste UNIQUE (son propre controle amont
    l'exige) et que la faute soit exactement celle qui est gardee : une borne
    de bloc qui filerait jusqu'a la fin du fichier, rendant le controle vrai
    PAR CONSTRUCTION.
    """
    p = os.path.join(arbre, "firmware/desknode/main/dn_pins.h")
    lp = io.open(p, encoding="utf-8").read().split("\n")
    marq = "Les 3 capteurs de dn4-2"
    garde = [l for l in lp if marq not in l]
    perdue = [l for l in lp if marq in l]
    # 🔴 REVUE DE CODE dn4-44 — MEME GARDE QUE CI-DESSUS : sans marqueur, le
    #    fichier ressortait identique et le rouge accusait le mauvais coupable.
    if not perdue:
        raise MutationMorte("le marqueur du bloc de refutation n'est plus dans"
                            " `dn_pins.h` — la mutation n'a RIEN change")
    io.open(p, "w", encoding="utf-8").write("\n".join(garde + perdue))
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
    # 🔴 RECLASSE `LEGITIME` ⇒ `BRANCHE` PAR LA REVUE DE CODE dn4-44
    #    (2026-09-03), ⛔ PAR LA MESURE ET NON PAR ARBITRAGE. Le critere
    #    `LEGITIME` etait ecrit `vert_propre and not atteint_mute` : il ne
    #    testait JAMAIS le discriminant que le commentaire de `BRANCHE`
    #    enonce pourtant (« un LEGITIME ne trace plus rien du tout »).
    #    Le controle rendu strict, ce site a rendu son jumeau KO : la gate
    #    ⛔ NE SORT PAS en amont, elle prend sa branche d'echec.
    ("tools/verif_ledger_dn416.py", "le ledger se LIT en UTF-8",
     "BRANCHE", m_ledger_binaire,
     "le ledger rendu NON-UTF-8 ⇒ la branche `ctrl(False, <MEME LIBELLE>)` "
     "est prise, PUIS `return 1`"),
    ("tools/verif_ledger_dn416.py", "le tracker se LIT en UTF-8",
     "BRANCHE", m_tracker_binaire,
     "le tracker rendu NON-UTF-8 ⇒ la branche `ctrl(False, <MEME LIBELLE>)` "
     "est prise, PUIS `return 1`"),
    ("tools/verif_dossier_dn415.py", "le depot cockpit est atteignable",
     "LEGITIME", m_cockpit_absent,
     "`--cockpit` vers un chemin inexistant ⇒ la branche `absent` est prise"),
    ("tools/verif_hist_dn413.py", "`dn_hist.c` compile et se charge sur l'hôte",
     "LEGITIME", m_hist_casse,
     "`dn_hist.c` rendu incompilable ⇒ ctrl(False) puis `return 1`"),
    ("tools/verif_lissage_dn45.py", "capture rejouee dans le PRODUIT",
     "LEGITIME", m_capture_absente,
     "la capture retiree ⇒ ctrl(False) puis `return 1`"),
    # 🔴 RECLASSE `LEGITIME` ⇒ `BRANCHE` PAR LA REVUE DE CODE dn4-44
    #    (2026-09-03), ⛔ PAR LA MESURE ET NON PAR ARBITRAGE. Le critere
    #    `LEGITIME` etait ecrit `vert_propre and not atteint_mute` : il ne
    #    testait JAMAIS le discriminant que le commentaire de `BRANCHE`
    #    enonce pourtant (« un LEGITIME ne trace plus rien du tout »).
    #    Le controle rendu strict, ce site a rendu son jumeau KO : la gate
    #    ⛔ NE SORT PAS en amont, elle prend sa branche d'echec.
    ("tools/verif_paliers_dn441.py",
     "la liste CANONIQUE des trois planchers est lisible",
     "BRANCHE", m_liste_planchers_absente,
     "la liste canonique retiree ⇒ la branche `dire(False, <MEME LIBELLE>)` "
     "est prise — le constat d'origine le disait DEJA, et le tri le classait "
     "quand meme LEGITIME"),
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
    # ⚠️ QUATRIEME CLASSE, IMPOSEE PAR LA MESURE DE dn4-44 ⛔ PAS PAR UN
    #    ARBITRAGE — et decouverte comme `INERTE` l'avait ete : par un site que
    #    le critere existant ne savait pas ranger.
    #    Ces deux `ctrl(True, …)` sont la BRANCHE DE SUCCES d'une alternative
    #    dont la branche d'echec porte `ctrl(False, <LE MEME LIBELLE>, …)`.
    #    ⇒ Le `True` n'affirme rien gratuitement : il PUBLIE le resultat du
    #      test qui vient d'etre fait, et exactement UNE des deux branches
    #      s'execute — le bilan ⛔ n'enfle pas.
    #    ⇒ TEMOIN : sous le mutant, le site `True` n'est PLUS atteint **et** le
    #      MEME libelle est trace **KO**. C'est ce couple qui distingue une
    #      `BRANCHE` d'un `LEGITIME` (ou plus rien n'est trace du tout).
    #    🔴 LES DEUX VIENNENT DE `f4848e4` LUI-MEME — le commit qui annonce
    #       solder les 27 correctifs de la revue de `dn4-40`. Personne ne l'a
    #       vu parce que RIEN N'INVOQUE LES CAMPAGNES : `T2-tri-ctrl.txt` est
    #       donc PERIME depuis ce commit.
    ("tools/verif_polices_dn440.py",
     "la FORME lue est une regex EXPLOITABLE ici",
     "BRANCHE", m_forme_cmake_incompilable,
     "le CMakeLists porte `^dn_font_[0-9]+**…` : CMake l'accepte, Python la "
     "refuse ⇒ la branche `ctrl(False, …)` est prise"),
    ("tools/verif_dossier_dn415.py",
     "le bloc de refutation SE FERME dans dn_pins.h",
     "BRANCHE", m_bloc_refutation_non_ferme,
     "l'en-tete du bloc DEPLACE en fin de fichier ⇒ plus aucun `*/` apres "
     "lui ⇒ la branche `ctrl(False, …)` est prise"),
]


# 🔴 dn4-44 / AC5.5 — LA LECTURE DES SITES VIT DANS `dn_sites`, ⛔ PLUS ICI.
#    Elle etait ecrite DEUX FOIS dans ce depot : tokenisee ici, au regex dans
#    `verif_campagne_dn440.py`. Les deux comptes coincidaient le 2026-09-03 (43 = 43)
#    ⛔ sans qu'aucun controle ne le tienne ; re-mesure du meme jour sur les 28
#    gates : le regex rendait **0 libelle** sur `verif_demarrage_dn443.py` et
#    fabriquait des libelles faux ailleurs (`'e'`, `'mur'`, `' '`).
#    ⚠️ CE QUI EST CONSERVE DE L'ANCIENNE LECTURE, ET QUI EST DE LA MEMOIRE :
#      · **f-string** — Python 3.12 la tokenise en `FSTRING_START`, ⛔ pas
#        `STRING` : le site etait INVISIBLE, ⛔ pas « non classe » ;
#      · **concatenation implicite** — `"un " "libelle"` ne rendait que son
#        PREMIER fragment, donc ne matchait plus rien ;
#      · **prefixe / triple quote** — `r"…"` et `'''…'''` ressortaient avec
#        leurs guillemets parce qu'on coupait `[1:-1]` a la main ;
#      · `a.startswith(b) or b.startswith(a)` rendait TOUJOURS vrai des que
#        l'un des deux etait VIDE ⇒ un `ctrl(True, "")` se declarait « deja
#        classe » et sortait de l'inventaire sans que personne ne le voie.
#    ⛔ Les commentaires ne peuvent pas mentir : `tokenize` distingue un
#      `ctrl(True, …)` d'un `ctrl(True, …)` CITE dans un commentaire.


def site_de(arbre, gate, libelle):
    """`(adresse, libelle AU SOURCE)` du site, RESOLU au source, ⛔ pas cite.

    🔴 TOKENISE, ⛔ PAS UNE FENETRE DE CARACTERES. Premiere version : on
    cherchait le libelle dans les 400 caracteres suivant le `ctrl(True,`. Les
    trois sites voisins de la gate du ledger tombaient tous sur le PREMIER, et
    deux cas sur treize sortaient « NON PROUVE » en visant le mauvais site.
    ⇒ On lit le **2e argument litteral** de l'appel, ⛔ rien d'autre.

    ⚠️ LE LIBELLE **DU SOURCE** EST RENDU, ⛔ pas celui du tableau `CAS` : le
    tableau cite des libelles TRONQUES, et la cle de trace porte le libelle
    ENTIER. Les apparier sur le libelle tronque ferait manquer la cle.
    """
    for ligne, est_true, lib, forme in dn_sites.sites(os.path.join(arbre, gate)):
        if est_true and forme == "litteral" and dn_sites.apparie(lib, libelle):
            return "%s:%d" % (os.path.basename(gate), ligne), lib
    return None, None


def compte_sites(chemin):
    """Les SITES `ctrl()`/`dire()` d'un source — tokenises, ⛔ pas grattes.

    ⚠️ Un premier comptage au motif de ligne rendait 15 sites la ou la gate
    du verrou en porte bien plus : le motif exigeait un debut de ligne et
    ratait tout appel imbrique. Un compte grate n'est pas un compte.
    """
    return dn_sites.compte(chemin)


def libelles_ctrl_true(arbre, gate):
    """`[(libelle, forme, ligne)]` des `ctrl(True, …)` — pour l'INVENTAIRE."""
    return [(lib, forme, ligne)
            for ligne, lib, forme in dn_sites.true_litteraux(
                os.path.join(arbre, gate))]


def _appariel(a, b):
    return dn_sites.apparie(a, b)


def survit_au_source(arbre, gate, libelle):
    """Le libelle EXISTE-t-il encore au source, hors d'un site `ctrl()` ?

    🔴 dn4-44 / AC5.3 — LE REMEDE SE **PROUVE**. Un `TROU`/`INERTE` dont le
    site avait disparu etait declare `[OK] REMEDE APPLIQUE` **sans qu'aucune
    gate ne soit jouee** — et une FAUTE DE FRAPPE dans le libelle produisait
    exactement la meme sortie verte. Le remede d'AC40.2 est « le site cesse de
    compter comme un controle : IL IMPRIME » ⇒ le libelle doit donc SURVIVRE
    au source. S'il a disparu tout court, ce n'est pas un remede : c'est un
    cas qui ne designe plus rien.

    🔴 REVUE DE CODE dn4-44 (2026-09-03) — IL CHERCHAIT DANS LE **TEXTE
    BRUT**, DONC IL NE TENAIT PAS SON PROPRE DOCSTRING. Deux sorties vertes
    MESUREES, toutes deux sur un controle qui avait purement DISPARU :
      · le libelle laisse dans un **COMMENTAIRE** ⇒ `[OK] REMEDE APPLIQUE`.
        C'est le motif « citer le jeton l'ACCORDE », deja paye deux fois ici ;
      · le libelle encore porte par un `ctrl(cond, "<le meme>")` ⇒ le site est
        toujours un CONTROLE, ⛔ pas le `print` que le remede d'AC40.2 exige.
    ⚠️ Et les deux moities du test n'etaient pas d'accord sur ce qu'est un
       commentaire : `site_de` tokenise (donc les retire), celui-ci lisait le
       brut (donc les gardait).
    ⇒ On lit les LITTERAUX CHAINE (commentaires exclus par le tokenizer) et on
      ECARTE ceux qui sont le libelle d'un `ctrl()`/`dire()`. Ce qui reste est
      du texte de CODE qui publie — c'est-a-dire le remede.
    """
    chemin = os.path.join(arbre, gate)
    try:
        lignes_ctrl = {ligne for ligne, _t, lib, _f in dn_sites.sites(chemin)
                       if lib and libelle in lib}
        for ligne, val in dn_sites.chaines(chemin):
            if libelle in val and ligne not in lignes_ctrl:
                return True
    except dn_sites.SourceIllisible:
        return False
    return False


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
        # 🔴 REVUE DE CODE dn4-44 (2026-09-03) — LE `rc` ET `stderr` ETAIENT
        #    JETES. Une gate MORTE (absente, qui ne compile plus, qui meurt
        #    avant son 1er controle) rendait `[]`, et le tableau publiait donc
        #    `invoc=0 · distin=0 · ecart=sites` : **son chiffre le plus
        #    alarmant**, au lieu de dire que la gate n'a pas tourne. C'est le
        #    defaut §(1) que le T0 de cette meme campagne vient de fermer,
        #    laisse debout 150 lignes plus bas.
        r = subprocess.run(args, capture_output=True, text=True, cwd=RACINE,
                           env=dict(os.environ, DN_TRACE_CTRL=tr))
        morte = a_plante(r.returncode, r.stderr)
        if not os.path.isfile(tr):
            return [], r.returncode, morte
        return ([l for l in io.open(tr, encoding="utf-8") if l.strip()],
                r.returncode, morte)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def monte_arbre(tmp):
    a = os.path.join(tmp, "arbre")
    os.makedirs(a)
    tar = subprocess.run(["git", "archive", "HEAD"], cwd=RACINE,
                         capture_output=True)
    # ⛔ REVUE 2026-09-03 — UN `git archive` EN ECHEC (pas de HEAD, pas un
    #    depot) rendait un flux VIDE, et `tar` mourait ensuite sur un message
    #    qui ne nommait pas la cause. On DIT la cause, a l'endroit ou elle est.
    if tar.returncode != 0 or not tar.stdout:
        raise RuntimeError(
            "⛔ `git archive HEAD` a echoue dans %s (rc=%d) : %s"
            % (RACINE, tar.returncode,
               (tar.stderr or b"").decode("utf-8", "replace").strip()[:200]
               or "flux vide"))
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
        # 🔴 REVUE 2026-09-03 — MEME AGREGATION QUE verif_campagne_dn440 : un site
        #    trace plusieurs fois (boucle sur une population) est KO des qu'UNE
        #    de ses lignes est KO. « Derniere gagne » rendait invisible une
        #    regression sur un seul element.
        # 🔴 dn4-44 / AC5.1 + AC5.5 — CETTE AGREGATION ETAIT **RECOPIEE** dans
        #    les deux campagnes, sans fonction partagee : l'une pouvait
        #    regresser sans que l'autre le dise. Elle vit dans `dn_trace.lit`,
        #    et la cle y porte desormais son DISCRIMINANT (le libelle).
        # 🔴 REVUE DE CODE dn4-44 — LA SORTIE EST RENDUE, ET C'EST LE TEMOIN
        #    QU'UNE GATE A **TOURNE**. Sans elle, `LEGITIME` etait satisfait
        #    par une TRACE VIDE : une gate qui ne compile plus rend 0 controle
        #    trace, donc « ⛔ PAS atteint sous mutant », donc `[OK] PROUVE`.
        #    MESURE : mutation de syntaxe sur la gate ⇒ `rc=1, 0 controles
        #    traces` ⇒ verdict `[OK] PROUVE`. Le contrat de gate impose une
        #    ligne `BILAN` a toute passe menee a son terme : c'est elle qui
        #    separe « sortie EN AMONT » (ce qu'un LEGITIME doit faire) de
        #    « morte » (ce qui ne prouve rien).
        return p.returncode, dn_trace.lit(tr), (p.stdout or ""), (p.stderr or "")
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
    print("          TROU     = un arbre defaillant ATTEINT le site ;")
    print("          INERTE   = la population du site est VIDE ;")
    print("          BRANCHE  = branche de SUCCES d'une alternative dont la")
    print("                     branche d'echec porte `ctrl(False, MEME LIBELLE)`")
    print("                     ⇒ exactement UNE des deux s'execute (dn4-44).")
    print("⛔ aucune ecriture dans l'arbre reel — `git archive HEAD` + copie.")
    print()

    base = {}
    echecs = []
    tmp0 = tempfile.mkdtemp(prefix="dn440src-")
    # ⛔ REVUE 2026-09-03 — L'ARBRE TEMPORAIRE N'ETAIT RENDU QU'AU CHEMIN
    #    NOMINAL : la moindre exception (gate absente, `git archive` en echec,
    #    interruption) laissait une copie COMPLETE du depot sur le disque.
    atexit.register(shutil.rmtree, tmp0, True)
    arbre0 = monte_arbre(tmp0)
    # ── LE T0 DE CETTE CAMPAGNE — dn4-44 / AC4.2 ────────────────────────────
    #
    # 🔴 ELLE N'EN AVAIT AUCUN, ET LE DEFAUT MORDAIT DEJA. Son `rc` etait jete,
    #    sa trace n'etait jamais controlee, et `bon = not atteint_propre` fait
    #    d'une TRACE VIDE la preuve d'un `INERTE`. ⇒ une gate MORTE rendait des
    #    verdicts `[OK]` gratuitement. Mesure du cadrage : **4 sur 13**.
    # ⚠️ CE QUE LE T0 NE PEUT PAS EXIGER ICI, ET POURQUOI — ECART DECLARE :
    #    la campagne de mutants joue UNE gate, verte ; celle-ci en joue HUIT,
    #    dont `verif_dossier_dn415.py` qui est ROUGE au depot (22 OK / 10 KO,
    #    rouge PRE-EXISTANT, ⛔ pas de cette marche). « Aucun KO sur l'arbre
    #    propre » ferait donc sortir la campagne ININTERPRETABLE a HEAD, en
    #    imputant un rouge qui ne lui appartient pas.
    #    ⇒ LE CRITERE EST PORTE **AU SITE**, la ou il mord vraiment : le site
    #      teste doit etre ATTEINT et **VERT** au T0. Un site deja KO sur
    #      l'arbre propre ne peut rien prouver — c'est exactement ce que « pas
    #      de KO au T0 » protege, applique a la bonne granularite.
    for gate, libelle, verdict, mut, quoi in CAS:
        adr, lib_src = site_de(arbre0, gate, libelle)
        if adr is None:
            # 🎯 POUR UN TROU OU UN INERTE, L'ABSENCE **PEUT** ETRE LE VERDICT :
            #    le remede d'AC40.2 est que le site publie desormais par
            #    `print`, ⛔ il ne compte plus. Pour un LEGITIME ou une BRANCHE,
            #    c'est un echec.
            # 🔴 dn4-44 / AC5.3 — MAIS LE REMEDE SE **PROUVE**. Il sortait
            #    `[OK]` sans qu'aucune gate ne soit jouee, et une FAUTE DE
            #    FRAPPE dans le libelle produisait la meme sortie verte.
            if verdict in ("TROU", "INERTE"):
                if survit_au_source(arbre0, gate, libelle):
                    print("  [OK] %-8s %-36s REMEDE APPLIQUE — le libelle"
                          " SURVIT au source hors d'un `ctrl()`"
                          % (verdict, libelle[:34]))
                    print("           constat : %s" % quoi)
                else:
                    echecs.append(gate + "/" + libelle)
                    print("  [!!] %-8s %-36s ⛔ LIBELLE INTROUVABLE AU SOURCE —"
                          " ⛔ PAS un remede : faute de frappe, ou le controle"
                          " a disparu" % (verdict, libelle[:34]))
            else:
                echecs.append(gate + "/" + libelle)
                print("  [!!] %-8s %-36s ⛔ SITE INTROUVABLE au source"
                      % (verdict, libelle[:34]))
            continue
        cle = dn_trace.cle(adr, lib_src)
        if gate not in base:
            rc, vus, motif = t0_de(gate, a.cockpit)
            if motif:
                echecs.append("T0/" + gate)
                print("  [!!] %-8s %-36s ⛔ %s — campagne ININTERPRETABLE"
                      % ("T0", os.path.basename(gate), motif))
                base[gate] = None
            else:
                base[gate] = vus
                print("  [T0] %-8s %-36s rc=%d · %d controle(s) traces · %d KO%s"
                      % ("", os.path.basename(gate), rc, len(vus),
                         sum(1 for v in vus.values() if v[0] == "KO"),
                         "  ⚠️ TERRAIN INCOMPLET (prerequis absent) — le tri ne"
                         " vaut que pour les sites ATTEINTS et VERTS ci-dessous"
                         if rc == RC_TERRAIN_INCOMPLET else ""))
        if base[gate] is None:
            continue
        atteint_propre = cle in base[gate]
        vert_propre = atteint_propre and base[gate][cle][0] == "OK"
        rc, vus, _sortie, err = joue(gate, mut, a.cockpit)
        atteint_mute = cle in vus
        if atteint_propre and not vert_propre:
            bon = False
            dit = ("⛔ DEJA KO AU T0 — un site rouge sur l'arbre propre ne peut"
                   " RIEN prouver")
        elif verdict == "INERTE":
            bon = not atteint_propre
            dit = ("CONFIRME INERTE — ⛔ jamais atteint sur l'arbre propre"
                   if bon else "⛔ RECLASSER — il EST atteint")
        elif verdict == "LEGITIME":
            # 🔴 REVUE DE CODE dn4-44 (2026-09-03) — CE TEST ETAIT SATISFAIT
            #    PAR UNE **TRACE VIDE**, ET IL N'ETAIT PAS DISJOINT DE
            #    `BRANCHE`. Deux trous MESURES :
            #    (a) une gate qui **ne compile plus** rend 0 controle trace ⇒
            #        « ⛔ PAS atteint sous mutant » ⇒ `[OK] PROUVE`. Le
            #        verdict le plus rassurant, au-dessus d'une gate morte.
            #        ⇒ on exige la ligne `BILAN` du contrat de gate : elle
            #          separe « sortie EN AMONT » de « morte ».
            #    (b) le commentaire de `BRANCHE` juste en dessous ENONCE le
            #        critere discriminant (« Un LEGITIME ne trace plus rien du
            #        tout ») — il n'etait **jamais teste** de ce cote. Mesure :
            #        des sites declares LEGITIME portaient la signature
            #        `BRANCHE` complete. ⇒ un jumeau KO **reclasse**.
            ko_jumeau = [k for k, v in vus.items()
                         if v[0] == "KO" and v[2] == dn_trace.aplati(lib_src)]
            a_tourne = not a_plante(rc, err)
            bon = (vert_propre and a_tourne and not atteint_mute
                   and not ko_jumeau)
            if bon:
                dit = ("PROUVE — atteint sur l'arbre propre, ⛔ PAS atteint"
                       " sous mutant, ⛔ aucun jumeau KO (rc=%d)" % rc)
            elif not a_tourne:
                dit = ("⛔ NON PROUVE — la gate mutee a PLANTE (exception non"
                       " rattrapee) : elle est MORTE, ⛔ pas sortie en amont"
                       " (rc=%d)" % rc)
            elif ko_jumeau:
                dit = ("⛔ RECLASSER EN `BRANCHE` — le MEME libelle ressort KO"
                       " en %s : la branche d'echec parle, la gate n'est ⛔ pas"
                       " sortie en amont"
                       % ", ".join(sorted(dn_trace.parts(k)[0]
                                          for k in ko_jumeau)))
            else:
                dit = ("⛔ NON PROUVE — propre:%s mute:%s (rc=%d)"
                       % (atteint_propre, atteint_mute, rc))
        elif verdict == "BRANCHE":
            # ⚠️ LE TEMOIN EST UN **COUPLE**, et c'est ce qui separe une
            #    BRANCHE d'un LEGITIME : sous le mutant, le site `True` n'est
            #    plus atteint (comme un LEGITIME) MAIS le MEME libelle ressort
            #    **KO** — la branche d'echec a parle. Un LEGITIME, lui, ne
            #    trace plus rien du tout : sa gate est sortie en amont.
            # 🔴 REVUE DE CODE dn4-44 — LA COMPARAISON PASSE PAR `aplati()`.
            #    Elle confrontait le libelle LU AU SOURCE a celui de la TRACE,
            #    qui est aplati a l'ecriture : un libelle portant une
            #    tabulation ou un saut de ligne ne s'appariait jamais, et le
            #    cas sortait `⛔ NON PROUVE` pour une raison TYPOGRAPHIQUE.
            #    `dn_trace` expose `aplati()` exactement pour ca.
            ko_jumeau = [k for k, v in vus.items()
                         if v[0] == "KO" and v[2] == dn_trace.aplati(lib_src)]
            bon = vert_propre and not atteint_mute and bool(ko_jumeau)
            dit = ("PROUVE — sous mutant la BRANCHE D'ECHEC parle : %s"
                   % ", ".join(sorted(dn_trace.parts(k)[0] for k in ko_jumeau))) \
                if bon else \
                ("⛔ NON PROUVE — propre:%s mute:%s jumeau KO:%d (rc=%d)"
                 % (atteint_propre, atteint_mute, len(ko_jumeau), rc))
        else:
            bon = vert_propre and (atteint_mute or mut is m_exemptions_vides)
            dit = ("CONFIRME TROU — %s" %
                   ("toujours atteint OK sous mutant"
                    if atteint_mute else "population videe, plus rien a garder")) \
                if bon else "⛔ RECLASSER — propre:%s mute:%s" % (atteint_propre,
                                                                 atteint_mute)
        if not bon:
            echecs.append(cle)
        print("  [%s] %-8s %-36s %s" % ("OK" if bon else "!!", verdict, adr, dit))
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
        # 🔴 REVUE DE CODE dn4-44 — UNE SEULE GATE ILLISIBLE TUAIT TOUT
        #    L'INVENTAIRE par traceback, sans `BILAN TRI`. Un fichier a erreur
        #    de syntaxe, tronque, ou porteur d'un conflit de fusion non resolu
        #    suffisait. ⇒ elle est DECLAREE non classable et l'inventaire
        #    continue : un outil qui meurt parce qu'UN de ses sujets est casse
        #    ne mesure pas les autres.
        try:
            trouves = libelles_ctrl_true(arbre0, rel)
        except dn_sites.SourceIllisible as e:
            inconnus.append("%s :: ⛔ SOURCE ILLISIBLE — %s"
                            % (os.path.basename(rel), str(e)[:60]))
            continue
        for lib, forme, ligne in trouves:
            if forme != "litteral" or not lib:
                motif = "vide" if forme == "litteral" else forme
                inconnus.append("%s:%d :: ⛔ libelle %s — le site EXISTE, il est"
                                " INCLASSABLE en l'etat"
                                % (os.path.basename(rel), ligne, motif))
                continue
            if not any(b == os.path.basename(rel) and _appariel(lib, l)
                       for b, l in connus):
                inconnus.append("%s:%d :: %s"
                                % (os.path.basename(rel), ligne, lib[:44]))
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
        lignes, rc_inv, morte = invocations_reelles(gate, a.cockpit)
        n = len(lignes)
        # 🔴 REVUE DE CODE dn4-44 — LA CLE PASSE PAR `dn_trace`, ⛔ PLUS PAR UN
        #    `split` LITTERAL : c'etait le TROISIEME lecteur du format, en dur,
        #    apres qu'AC5.5 a declare que la lecture vit dans `dn_trace`. Une
        #    ligne malformee y devenait un SITE FANTOME.
        distincts = len({dn_trace.parts(dn_trace.cle(l.split(dn_trace.SEP)[0],
                                                     ""))[0]
                         for l in lignes if dn_trace.SEP in l})
        if morte:
            echecs.append("invocations/" + gate)
            print("   %-30s %6d %6s %6s %6s   ⛔ GATE MORTE (rc=%s) — l'ecart"
                  " ci-contre serait FABRIQUE"
                  % (os.path.basename(gate), sites, "—", "—", "—", rc_inv))
        else:
            print("   %-30s %6d %6d %6d %6d"
                  % (os.path.basename(gate), sites, n, distincts,
                     sites - distincts))
    print("   ⚠️ TROIS COLONNES, ⛔ PAS DEUX — et c'est la mesure qui l'impose.")
    print("      `invoc` peut DEPASSER `sites` : un site dans une boucle")
    print("      s'execute autant de fois que sa population a d'elements.")
    print("      C'est `distincts` (sites REELLEMENT atteints) qui se compare")
    print("      a `sites`, et leur ecart compte le code HORS du chemin par")
    print("      defaut (modes `--manifeste`/`--mutant`, branches d'echec).")
    print("      ⇒ Cet ecart devient un DEFAUT le jour ou rien ne l'exerce —")
    print("        c'est ce que mesure « gardes par rien » (verif_campagne_dn440).")

    # ⚠️ COMPTE PRIS **AVANT** LA DESTRUCTION DE L'ARBRE — il le lit.
    vivants = sum(1 for c in CAS if site_de(arbre0, c[0], c[1])[0])
    shutil.rmtree(tmp0, ignore_errors=True)
    n_leg = sum(1 for c in CAS if c[2] == "LEGITIME")
    n_trou = sum(1 for c in CAS if c[2] == "TROU")
    n_in = sum(1 for c in CAS if c[2] == "INERTE")
    n_br = sum(1 for c in CAS if c[2] == "BRANCHE")
    print("\n" + "=" * 78)
    # 🔴 REVUE DE CODE dn4-44 — « 15 site(s) » ANNONCAIT `len(CAS)`, ET LE
    #    DEPOT N'EN PORTE PAS 15. Les cas dont le site a ete REMEDIE (il
    #    `print` desormais) restent au tableau — c'est voulu, ils gardent le
    #    remede — mais ce ne sont **plus des sites**. Un lecteur en concluait
    #    que le depot porte 15 `ctrl(True, …)` dont 3 trous ouverts ; il en
    #    porte moins, et 0 trou ouvert. ⇒ on publie les DEUX comptes.
    print("BILAN TRI : %d cas au tableau — dont %d SITE(S) VIVANT(S) et %d"
          " FICHE(S) de remede — %d LEGITIME(S), %d TROU(S), %d INERTE(S),"
          " %d BRANCHE(S), %d echec(s)"
          % (len(CAS), vivants, len(CAS) - vivants,
             n_leg, n_trou, n_in, n_br, len(echecs)))
    print("=" * 78)
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())

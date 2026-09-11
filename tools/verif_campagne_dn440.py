# -*- coding: utf-8 -*-
"""dn4-40 / AC40.7 — LA CAMPAGNE PROUVE `controle ⇒ couvert`, ⛔ PAS `mutant ⇒ rouge`.

🔴 LE SENS DE LA PREUVE EST LE SUJET. Une campagne « N mutants, N vus rougir »
prouve `mutant ⇒ rouge` : elle dit que les mutants qu'on a ecrits sont
attrapes. Elle ⛔ NE DIT RIEN des controles que RIEN ne garde. Ce script
publie donc les DEUX faces :

  (1) chaque mutant REPLANTE une faute et doit etre vu rougir ;
  (2) le COMPTE DES CONTROLES GARDES PAR RIEN — ceux qu'aucun mutant de la
      campagne ne fait passer de OK a KO.

⛔ UN MUTANT QUI DEBRANCHE LA GARDE NE PROUVE QUE SON EXISTENCE. Tous les
mutants ci-dessous replantent la faute DANS LES DONNEES (ledger, tracker,
manifeste), ⛔ jamais dans le code de la gate.

⚠️ UN SEUL SITE A LA FOIS. Muter par remplacement global synchroniserait la
faute ET sa fixture : la gate verrait un monde coherent et resterait verte
pour la mauvaise raison.

⚠️ INDEXATION : sur la CLE `(site d'appel, libelle)` (`dn_trace`), ⛔ jamais sur
la console — la console tronque a 62 caracteres et des KO y collident.

⚠️ ⛔ AUCUNE ECRITURE DANS LE COCKPIT VIVANT. Chaque mutant travaille dans une
COPIE jetable, montee sous un repertoire temporaire.

═══════════════════════════════════════════════════════════════════════════
 dn4-44 — CE QUE CETTE MARCHE A CHANGE, ET POURQUOI. ⛔ Rien n'est efface.
═══════════════════════════════════════════════════════════════════════════

🔴 (1) LE COMPTE « GARDES PAR RIEN » **GARDE** (AC4.1). Il rendait `rc=0` en
   publiant 15 controles nus — c'est tres exactement pourquoi AC40.7.a a pu
   etre REFUTEE sans que rien ne rougisse. Un controle nu est desormais un
   ECHEC, sauf EXEMPTION DECLAREE et FALSIFIABLE (table `EXEMPTIONS`).

🔴 (2) LE VERDICT D'UN MUTANT EST **STRICT** (AC2.4). Il ne suffisait pas que
   la cible rougisse : mesure du 2026-09-03, **10 mutants sur 22** faisaient
   rougir des sites QU'ILS NE VISAIENT PAS, et la campagne n'en disait rien.
   Un refus qui tombe ailleurs ne prouve rien sur sa cible — motif paye a la
   revue de `dn4-23`. ⇒ tout rouge non declare (`cible` ou `aussi`) est un
   ECHEC, et cinq fixtures ont ete CORRIGEES plutot que declarees : elles
   nommaient un porteur `done` sans le vouloir.

🔴 (3) LA CAMPAGNE SE GARDE ELLE-MEME (AC1.3). Les trois correctifs de la
   revue du 2026-09-03 TENAIENT — il a fallu les exercer A LA MAIN pour
   l'etablir. Un correctif que rien ne garde est le defaut meme que cette
   campagne existe pour compter. ⇒ section `LES BANCS`.

🔴 (4) LE COMPTE ANNONCE EST LE COMPTE **JOUE** (AC5.4). Le bilan annoncait
   `len(MUTANTS) + 1` : il aurait dit « 23 » meme si le 23e n'avait pas ete
   tire. On compte les tirs.

🔴 (5) LE `rc` DE LA REGENERATION DU MANIFESTE EST **TESTE** (AC5.6). Son
   propre commentaire dit que sans elle « LA CAMPAGNE NE MESURE RIEN », et il
   etait jete.

🔴 (6) LA GARDE DE MUTATION NULLE VERIFIE **CE QUI** A CHANGE (AC5.2), ⛔ plus
   « que quelque chose a change ». Un `re.sub` mordant sur une AUTRE cle
   rendait la mutation non nulle et restait vert.

🔴 (7) LA RESOLUTION DES CIBLES PASSE PAR `dn_sites` (AC5.5) — la MEME lecture
   que la campagne du tri. L'ancienne lisait au regex : mesure du 2026-09-03,
   elle rendait **0 libelle** sur `verif_demarrage_dn443.py` (guillemets
   simples) et fabriquait des libelles faux ailleurs (`'e'`, `'mur'`).

🔴 (8) ELLE S'APPELAIT `campagne_dn440.py` JUSQU'AU 2026-09-03, ET RIEN NE
   L'INVOQUAIT (AC4.5). Elle n'etait pas dans le glob `tools/verif_*.py` : ni
   la CI, ni `run_gates.sh`, ni un hook ne la jouaient. Le compte qui REFUTE
   AC40.7.a n'existait donc que si quelqu'un tapait la commande — et personne
   n'a vu `campagne_ctrl_dn440.py` devenir ROUGE a `f4848e4`.
   ⇒ DECISION OWNER DU 2026-09-03 (question n°1) : elle entre au glob sous le
     nom `verif_campagne_dn440.py`, et elle est declaree NON_JOUABLE en CI avec
     son temoin (le cockpit est absent du clone) et son `rc` attendu — le
     mecanisme construit et valide par `dn4-39`. ⛔ Aucun concept neuf.
   ⚠️ Les mesures d'archive (`mesures/dn4-40/*.txt`) portent l'ANCIEN nom, et
     ⛔ elles ne se reecrivent pas : ce sont des captures datees.

Usage :
    python3 tools/verif_campagne_dn440.py --cockpit ~/projects/compagnon_project
    python3 tools/verif_campagne_dn440.py --liste
"""
import argparse
import collections
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
DESKNODE = os.path.dirname(ICI)
sys.path.insert(0, ICI)
import dn_sites                                            # noqa: E402
import dn_trace                                            # noqa: E402

# 🔴 dn4-44 / AC4.5 — CE SCRIPT EST DESORMAIS UNE **GATE** (decision owner du
#    2026-09-03, question n°1). Il entre donc dans le glob `tools/verif_*.py`,
#    et il doit rendre le CONTRAT : `rc` 0/1 (+ `2` usage, `4` prerequis
#    absent). ⛔ En CI le cockpit est ABSENT — il mourait alors sur une trace
#    Python, ⛔ pas sur un refus declare. Le `4` est ce qui rend la ligne
#    `NON_JOUABLE` de `run_gates.sh` VERIFIABLE : la gate est jouee quand meme
#    et doit rendre EXACTEMENT ce code.
RC_PREREQUIS = 4

REL_LEDGER = "_bmad-output/implementation-artifacts/deferred-work.md"
REL_TRACKER = "_bmad-output/implementation-artifacts/sprint-status-desknode.yaml"
REL_MANIFESTE = "_bmad-output/implementation-artifacts/dn4-16-arbitrage-ledger.md"
GATE = os.path.join(ICI, "verif_ledger_dn416.py")
# ⚠️ `--gate` sert a jouer la MEME campagne contre la version d'AVANT le
# correctif (extraite par `git archive HEAD`). C'est le seul moyen de
# prouver le defaut « a vide » plutot que de l'affirmer : les mutants A et C
# doivent y sortir VERTS SANS avoir ete regardes.

# Une disposition TEMOIN, insérée en tete de la section DeskNode. ⛔ Elle
# n'existe que dans la copie.
# 🔴 dn4-40 / REVUE 2026-09-03 — LE TAG `[DeskNode]` EST POSE, ⛔ PLUS DEDUIT.
#    `est_desknode()` lit le tag DANS LA TETE de puce, sinon elle retombe sur
#    la SECTION. Tant que le temoin ne portait pas le tag, sa DeskNode-ite
#    dependait de l'endroit ou l'ancre etait tombee — un chemin non exerce
#    rendait les mutants VERTS pour rien. Le tag rend la chose VRAIE PAR
#    DECLARATION, ⛔ plus par inference.
TETE = ("- %s **[DeskNode] Entree TEMOIN de campagne dn4-40%s** — inseree par "
        "`verif_campagne_dn440.py` dans une COPIE.\n")
DISPO = ("  ⇒ [dn4-40 %s] %s · porteur : %s · preuve : %s\n")
PREUVE_PAR_DEFAUT = "le motif `TEMOIN de campagne dn4-40`"
# 🔴 dn4-44 — UN PORTEUR **VIVANT** PAR DEFAUT, ET C'EST UN CORRECTIF DE
#    FIXTURE, ⛔ pas un confort. Mesure du 2026-09-03 : cinq mutants (`G1`,
#    `G2`, `G3`, `G4`, `G6`) nommaient `dn4-40` comme porteur — une story
#    `done`. Ils faisaient donc rougir `aucun porteur A VENIR n'est
#    done/superseded` EN PLUS de leur cible, sans que personne ne le voie.
#    ⇒ le porteur par defaut se LIT au tracker : la 1re cle DeskNode vivante.
# 🔴 REVUE DE CODE dn4-44 (2026-09-03) — LE COMMENTAIRE CI-DESSUS ANNONCAIT UNE
#    LECTURE, ET LA LIGNE D'EN DESSOUS ETAIT UNE **CONSTANTE**. La fixture
#    redevenait donc fausse le jour ou `dn4-41` passerait `done` — c'est-a-dire
#    la faute meme que ce bloc dit avoir corrigee, DEPLACEE DANS LE FUTUR.
#    🔬 MESURE : `dn4-41` bascule `done` dans une copie ⇒ **12 echecs**, dont 9
#       « ROUGE NON DECLARE ailleurs », sans qu'aucune gate n'ait change.
# ⇒ ELLE SE LIT MAINTENANT. La ligne d'origine est ⛔ NON EFFACEE, ci-dessous.
# ⚠️ LA LISTE DES STATUTS VIVANTS A **UN** PROPRIETAIRE, ET C'EST LA GATE
#    (`verif_ledger_dn416.STATUTS_VIVANTS`). La recopier ici la ferait deriver
#    en silence — c'est la regle que `_borne_debut` applique deja a la borne du
#    manifeste, et la revue de code dn4-44 a failli la casser en la dupliquant.
PORTEUR_VIVANT = "dn4-41"        # ← ligne d'origine, DATEE et ⛔ NON EFFACEE


class _Auto(object):
    """Le porteur « la 1re story vivante », RESOLU AU TIR.

    ⛔ Ce n'est pas une chaine, et c'est deliberé : une chaine se figerait a
    l'import, ce qui est exactement le defaut corrige ici.
    """
    def __repr__(self):
        return "<porteur vivant, lu au tracker>"


AUTO = _Auto()


def porteur_vivant(trk):
    """La 1re cle de story DeskNode VIVANTE au tracker — ⛔ pas une constante.

    ⚠️ Rend la cle **LONGUE** (celle que le tracker porte), qui est aussi la
    forme qu'un porteur doit avoir. ⛔ Leve si le tracker n'en porte AUCUNE :
    une fixture batie sur un porteur mort ne prouve pas ce qu'elle croit.
    """
    vivants = charge_gate().STATUTS_VIVANTS
    for m in re.finditer(r"^  (dn\d+-\d+[a-z0-9\-]*):\s*([a-z\-]+)", trk,
                         flags=re.M):
        if m.group(2) in vivants:
            return m.group(1)
    raise RuntimeError("⛔ aucune cle de story DeskNode VIVANTE au tracker —"
                       " la fixture ne peut pas nommer de porteur valide")


def _resolu(ch, trk):
    """La declaration, porteur RESOLU au tracker si elle demande `AUTO`."""
    if ch.get("porteur") is AUTO:
        return dict(ch, porteur=porteur_vivant(trk))
    return ch


def ancre_desknode(txt):
    """L'offset de la puce d'une entree DeskNode OUVERTE — le site d'insertion.

    🔴 CE QUE CETTE FONCTION REPARE, ET QUI EST LE PIEGE N°1 D'UNE CAMPAGNE.
    Premiere version : on inserait avant la 1re puce `- ⚪ ` du fichier. Les
    14 mutants sortaient alors « KO neufs : aucun » — VERTS, et pour rien :
    la puce tombait HORS d'une section DeskNode, donc `est_desknode()` la
    rejetait et le mutant N'ATTEIGNAIT JAMAIS la garde qu'il pretend couvrir.
    ⛔ Un mutant vert sur un chemin non exerce ne prouve RIEN.

    ⇒ On ancre desormais sur une entree qui porte DEJA une disposition
      DeskNode : la section est alors la bonne PAR CONSTRUCTION.

    ⚠️ REVUE 2026-09-03 — `rindex` LEVAIT UN `ValueError` NON ATTRAPE quand la
    1re ligne `⇒` du fichier n'a aucune puce au-dessus d'elle (l'EXEMPLE DE
    FORMAT de l'en-tete est exactement ce cas). La campagne mourait au lieu de
    dire qu'elle n'a pas d'ancre. On rend None, et l'appelant sort en 1.
    """
    for m in re.finditer(r"^\s*⇒\s*\[dn\d", txt, re.M):
        j = txt.rfind("\n- ", 0, m.start())
        if j >= 0:
            return j + 1
    return None


def _bloc(ch, suffixe=""):
    """Le texte d'UNE entree temoin — tete + (0, 1 ou 2) ligne(s) de dispo."""
    bloc = TETE % (ch.get("marqueur", "⚪"), suffixe)
    if ch.get("verdict") is not None:
        d = DISPO % (ch.get("date", "2026-09-02"), ch["verdict"], ch["porteur"],
                     ch.get("preuve", PREUVE_PAR_DEFAUT))
        bloc += d
        if ch.get("double"):
            bloc += d
    return bloc


def _mute_ledger(txt, ch, j):
    """Insere UNE entree temoin a l'offset `j`. ⛔ Un seul site."""
    return txt[:j] + _bloc(ch) + txt[j:]


# ═══════════════════════════════════════════════════════════════════════════
#  LA DECLARATION D'UN MUTANT — dn4-44
# ═══════════════════════════════════════════════════════════════════════════
#
# `muteur(led, trk, faux)` rend `(led, trk)` et peut TOUCHER LA COPIE `faux`
#   (le manifeste, par exemple). Il s'applique AVANT la regeneration du §9.
# `apres(faux)` s'applique APRES elle — pour les fautes que la regeneration
#   effacerait aussitot (une borne retiree, une ligne du §9 falsifiee).
# `cible`  = le libelle du controle vise. ⛔ Jamais une adresse (AC40.4.g).
# `aussi`  = les libelles STRUCTURELLEMENT COUPLES qui rougissent avec lui.
#            ⚠️ Ils se DECLARENT : un rouge non declare est un ECHEC.
# `change` = ce que le mutant pretend modifier (`ledger`/`tracker`/`manifeste`).
#            ⚠️ C'est la garde d'AC5.2 : « quelque chose a change » ne dit pas
#            que LA BONNE chose a change.
# `regen`  = le `rc` attendu de la regeneration du manifeste (AC5.6).
# `gate`   = jouer une AUTRE copie de la gate (pour muter l'ARBORESCENCE).
# `motif` = un texte qui DOIT apparaitre dans les lignes ajoutees (AC5.2).
#           ⚠️ C'est ce qui fait passer la garde du grain « quel ARTEFACT a
#           bouge » au grain « la BONNE chose a bouge ». Sans lui, le detail
#           etait calcule a chaque tir puis JETE (revue de code dn4-44).
Mut = collections.namedtuple(
    "Mut", "nom quoi muteur cible aussi change apres regen gate motif")


def M(nom, quoi, muteur, cible=None, aussi=(), change=("ledger",),
      apres=None, regen=0, gate=None, motif=None):
    return Mut(nom, quoi, muteur, cible, tuple(aussi), tuple(change),
               apres, regen, gate,
               motif if motif is not None else getattr(muteur, "_motif", None))


def ins(**ch):
    """Un muteur qui INSERE une entree temoin — la forme historique."""
    def _f(led, trk, faux, ch=ch):
        return _mute_ledger(led, _resolu(ch, trk), ancre_desknode(led)), trk
    # 🔴 REVUE DE CODE dn4-44 / AC5.2 — LE MOTIF QUE LA MUTATION DOIT POSER.
    #    `change` disait QUEL ARTEFACT bouge ; le DETAIL des lignes etait
    #    calcule a chaque tir puis **jete**. La garde restait donc au grain du
    #    NOM D'ARTEFACT : un muteur qui inserait au mauvais endroit passait.
    _f._motif = "TEMOIN de campagne"
    return _f


# ── LES MUTEURS LIBRES — dn4-44 ─────────────────────────────────────────────
# ⛔ Chacun replante une faute REELLE dans les DONNEES. Aucun ne debranche.

def m_ledger_vide(led, trk, faux):
    """Le ledger perd toutes ses entrees — la faute que garde `le perimetre
    n'est pas vide` : un ledger tronque, ou une section renommee."""
    return ("# Deferred Work\n\n## Deferred from: (aucune)\n\n"
            "(ce ledger a ete VIDE par le mutant dn4-44 dans une COPIE)\n"), trk


def m_statut_inconnu(led, trk, faux):
    """Le statut du porteur devient un statut HORS DES DEUX LISTES.

    Faute replantee : une faute de frappe au tracker (`in-progres`), ou un
    statut invente. Le porteur EXISTE, il est simplement ININTERPRETABLE.
    """
    court = porteur_vivant(trk)
    led = _mute_ledger(led, dict(verdict="PORTEE", porteur=court),
                       ancre_desknode(led))
    trk = re.sub(r"^(  %s(?:-[a-z0-9\-]*)?:)\s*[a-z\-]+" % re.escape(court),
                 r"\1 en-attente", trk, count=1, flags=re.M)
    return led, trk


def m_collision_vivant_mort(led, trk, faux):
    """Deux cles longues repliees sur la MEME cle courte, l'une VIVANTE et
    l'autre MORTE — la collision qui peut CHANGER un verdict.

    ⚠️ On ajoute la 2e ecriture JUSTE APRES la 1re : `lit_tracker` garde la
    premiere vue, donc l'ambiguite est reelle et le verdict devient un
    tirage sur l'ordre du fichier. C'est exactement la faute gardee.
    """
    court = porteur_vivant(trk)

    def _pose(m):
        return "%s\n  %s-un-homonyme-mort: done" % (m.group(0), court)
    trk = re.sub(r"^  %s(?:-[a-z0-9\-]*)?:\s*[a-z\-]+" % re.escape(court),
                 _pose, trk, count=1, flags=re.M)
    return led, trk


def m_manifeste_absent(led, trk, faux):
    """Le manifeste n'est pas livre — la faute que garde son controle."""
    p = os.path.join(faux, REL_MANIFESTE)
    if os.path.isfile(p):
        os.remove(p)
    return led, trk


NOM_GATE = "verif_ledger_dn416.py"
NOM_RENOMME = "verif_ledger_dn416_RENOMME.py"


def m_ledger_sans_citation(led, trk, faux):
    """Le ledger cesse de nommer la gate dans ses PREUVES.

    🔴 CE QUE LA MESURE A IMPOSE, ET QUI N'ETAIT PAS PREVU : sur les **10**
    occurrences du nom de la gate dans le manifeste, **7 vivent DANS le §9** —
    ce sont des champs `preuve` que la regeneration recopie depuis le ledger.
    Retirer la citation du seul texte HORS bornes ne rend donc pas le controle
    faux : les 7 du tableau le satisfont encore. Et la retirer du fichier
    ENTIER falsifie 7 lignes du §9 ⇒ le mutant rougissait AUSSI sur « chaque
    ligne REPRODUIT », donc pour la mauvaise raison.
    ⇒ On mute LA SOURCE (le ledger). La regeneration reecrit alors un §9
      COHERENT avec elle, et le seul rouge restant est la citation absente.
      🎯 C'est exactement le patron « construire la fixture de sorte que SEUL
      le controle vise puisse la refuser ».
    """
    return led.replace(NOM_GATE, NOM_RENOMME), trk


def a_manifeste_sans_citation(faux):
    """…et la prose du manifeste cesse elle aussi de la citer.

    ⚠️ APRES la regeneration : appliquee avant, elle serait sans effet sur le
    §9, que `--en-place` reecrit juste derriere.
    """
    p = os.path.join(faux, REL_MANIFESTE)
    s = io.open(p, encoding="utf-8").read()
    io.open(p, "w", encoding="utf-8").write(s.replace(NOM_GATE, NOM_RENOMME))


def a_borne_retiree(faux):
    """La borne de debut du §9 disparait ⇒ le controle retombe sur TOUT le
    fichier. ⚠️ APRES la regeneration : appliquee avant, `--en-place` sortirait
    en 1 et le mutant ne mesurerait plus rien."""
    p = os.path.join(faux, REL_MANIFESTE)
    s = io.open(p, encoding="utf-8").read()
    io.open(p, "w", encoding="utf-8").write(
        s.replace(_borne_debut(), "<!-- borne retiree par le mutant dn4-44 -->", 1))


def a_ligne_du_manifeste_supprimee(faux):
    """UNE ligne du §9 disparait ⇒ une entree ouverte SANS ligne de manifeste."""
    p = os.path.join(faux, REL_MANIFESTE)
    s = io.open(p, encoding="utf-8").read()
    lignes = s.split("\n")
    for i, l in enumerate(lignes):
        if re.match(r"^\| *[0-9a-f]{8} *\|", l):
            del lignes[i]
            break
    io.open(p, "w", encoding="utf-8").write("\n".join(lignes))


def a_ligne_du_manifeste_falsifiee(faux):
    """UNE cellule du §9 est reecrite, l'ancre INCHANGEE ⇒ la ligne ne
    REPRODUIT plus ce que le script produit, et rien d'autre ne bouge.

    🎯 C'est le seul mutant du manifeste qui n'entraine AUCUN couplage : le
    controle de couverture ne regarde que l'appariement, ⛔ pas le contenu.
    """
    p = os.path.join(faux, REL_MANIFESTE)
    s = io.open(p, encoding="utf-8").read()
    lignes = s.split("\n")
    for i, l in enumerate(lignes):
        m = re.match(r"^(\| *[0-9a-f]{8} *\|)(.*)$", l)
        if m:
            lignes[i] = m.group(1) + " `SECTION FALSIFIEE PAR LE MUTANT` |" \
                + "|".join(m.group(2).split("|")[2:])
            break
    io.open(p, "w", encoding="utf-8").write("\n".join(lignes))


def _borne_debut():
    """La borne de debut du §9, LUE DANS LA GATE — ⛔ jamais recopiee ici.

    ⚠️ La gate ELLE-MEME refuse d'ecrire si la borne apparait deux fois dans
    le manifeste. La recopier dans ce fichier serait sans effet sur elle, mais
    c'est la meme faute de principe : une constante a UN proprietaire.
    """
    return charge_gate().BORNE_DEBUT


_GATE_MOD = [None, None]


def charge_gate(chemin=None):
    """Le module de la gate, importe — pour LIRE ses constantes et ses
    fonctions plutot que de les recopier.

    ⚠️ ⛔ Aucun effet de bord : la gate garde son travail derriere
    `if __name__ == "__main__"`.
    """
    chemin = chemin or GATE
    if _GATE_MOD[0] != chemin:
        import importlib.util
        spec = importlib.util.spec_from_file_location("dn_gate_ledger", chemin)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _GATE_MOD[0], _GATE_MOD[1] = chemin, mod
    return _GATE_MOD[1]


# ── LA COLLISION D'ANCRE, **FORGEE** (AC2.5, issue (a)) ─────────────────────
#
# 🔴 CE QUE LE DOCSTRING D'`ancres()` ECRIT DEJA, ET QUI EST LE NŒUD : le RANG
#    parmi les homonymes rend l'entree du hachage unique PAR CONSTRUCTION, si
#    bien que le controle « chaque ancre designe UNE seule entree » ne garde
#    plus que la collision de hachage **32 bits**.
# ⇒ Un mutant qui RACCOURCIRAIT l'ancre ou retirerait le rang DEBRANCHERAIT la
#   garde : il ne prouverait que son existence. ⛔ Refuse.
# ⇒ On FORGE donc une vraie collision — anniversaire sur 8 hexadecimaux.
#   🔬 MESURE. ⚠️ LE CHIFFRE DU CADRAGE (`0,14 s`, `37 670` essais) EST
#      **REFUTE PAR LE CODE LIVRE** — revue de code du 2026-09-03, deux tirs
#      concordants : **131 036 essais**, ~2,4 s. La conclusion tient (la
#      recherche est deterministe et tient DANS le mutant, ⛔ elle n'a pas
#      besoin d'etre pre-calculee) ; c'est le CHIFFRE qui etait faux, et il
#      n'etait adosse a aucun fichier de mesure. ⛔ Ligne d'origine non
#      effacee, elle est juste au-dessus de celle-ci dans l'historique.
# ⚠️ ELLE FAIT ROUGIR TROIS CONTROLES, ET C'EST LE RESULTAT ATTENDU : deux
#    entrees de meme ancre produisent deux LIGNES de manifeste de meme ancre.
#    Le controle de DOUBLON D'ANCRE cote manifeste — celui que le docstring
#    designe comme portant le VRAI risque — recoit donc son mutant DANS LE
#    MEME GESTE.
ESSAIS_MAX = 400000


def forge_collision(led, sec):
    """Deux titres de temoin dont l'ancre 8-hexa COLLIDE reellement.

    Rend `(titre_a, titre_b, ancre, essais)`. ⛔ Leve si la recherche echoue —
    un mutant qui ne s'applique pas ne prouve RIEN.
    """
    # 🔴 REVUE DE CODE dn4-44 (2026-09-03) — ELLE **RECOPIAIT** LA FORMULE
    #    D'ANCRE DE LA GATE : la troncature `[:46]`, le separateur et le rang
    #    `0` etaient dupliques ici, trente lignes apres le `_borne_debut` qui
    #    proclame « une constante a UN proprietaire » et va, lui, LIRE dans la
    #    gate. Le jour ou la gate change sa troncature, la « vraie collision
    #    d'anniversaire » n'en est plus une — et ⛔ aucun banc ne le dirait.
    # ⇒ ON APPELLE `ancres()` DE LA GATE. Plus une seule constante recopiee :
    #   la formule a UN proprietaire, et c'est celui qu'on cherche a piéger.
    G = charge_gate()
    vus = {}
    for n in range(ESSAIS_MAX):
        suffixe = " #%d" % n
        e = {"tete": TETE % ("⚪", suffixe), "sec": sec, "ligne": 0, "txt": ""}
        h = list(G.ancres([e]).values())[0][:8]
        if h in vus and vus[h] != suffixe:
            return vus[h], suffixe, h, n + 1
        vus[h] = suffixe
    raise RuntimeError("⛔ aucune collision d'ancre trouvee en %d essais"
                       % ESSAIS_MAX)


def m_ancre_collision(led, trk, faux):
    """Deux entrees ouvertes dont l'ancre du §9 est LA MEME — pour de vrai."""
    G = charge_gate()
    j = ancre_desknode(led)
    # La SECTION du site d'insertion, lue par la MEME decoupe que la gate.
    pv = porteur_vivant(trk)
    sonde = _mute_ledger(led, dict(verdict="PORTEE", porteur=pv), j)
    sec = None
    for s in G.decoupe(sonde):
        for e in s["entrees"]:
            if "Entree TEMOIN de campagne" in e["tete"]:
                sec = e["sec"]
    if sec is None:
        raise RuntimeError("⛔ le temoin n'est pas retrouve a la decoupe")
    ta, tb, _h, _n = forge_collision(led, sec)
    ch = dict(verdict="PORTEE", porteur=pv)
    return led[:j] + _bloc(ch, ta) + _bloc(ch, tb) + led[j:], trk


def premiere_designation_ouverte(trk):
    """`(ligne, d0, d1, lignes, debut_item)` de la 1re designation OUVERTE.

    🎯 LE BORNAGE VIENT DE `bloc_ac56()` **DE LA GATE**, ⛔ il n'est plus
    RECOPIE ici — revue du 2026-09-05. Le docstring de `mute_ac56()` promettait
    deja « il relit les regex de la gate, ⛔ il ne les recopie pas », pendant que
    dix lignes de bornage vivaient ici : un changement de bornage ⛔ ne se serait
    pas propage au mutant. Une constante a UN proprietaire — meme raison que
    `_borne_debut()`.
    """
    g = charge_gate()
    lignes = trk.split("\n")
    corps, offset, motif = g.bloc_ac56(trk)
    if corps is None:
        raise RuntimeError("bloc AC5.6 illisible : %s" % motif)
    for it in g.items_ac56(corps):
        ouvertes = [c for c in it["cles"] if c[4] is None]
        if not ouvertes:
            continue
        j, d0, d1, _cle, _cl = ouvertes[0]
        return j + offset, d0, d1, lignes, it["debut"] + offset
    raise RuntimeError("aucune designation OUVERTE dans le bloc AC5.6")


def mute_ac56(cle_neuve, avec_solde=None):
    """dn5-7 / report (3) — REPLANTE un porteur FAUTIF dans la liste AC5.6 du
    tracker, DANS LA COPIE jetable.

    ⛔ IL NE DEBRANCHE RIEN. Il ne retire ⛔ ni le controle ⛔ ni le bloc : il
    remplace la CLE d'une designation `⇒ **`cle`**` par une cle fautive —
    exactement la faute que le controle existe pour voir, et exactement celle
    que la mesure du 2026-09-05 a trouvee VIVANTE (l'item 15 designait une
    story `done`).

    🎯 IL RELIT LES REGEX **DE LA GATE**, ⛔ il ne les recopie pas. Un muteur
    qui redefinirait la borne du bloc pourrait mordre HORS de ce que la gate
    lit : la campagne le verrait (« NON VU »), mais le motif serait faux. Une
    constante a UN proprietaire — meme raison que `_borne_debut()`.

    ⚠️ Il saute les lignes DEJA CLOSES : une ligne close est hors de la
    population de vivacite, donc y planter la faute ne prouverait RIEN.

    `avec_solde` REPLANTE en plus une marque de cloture :
      · `"sur-la-ligne"` — `SOLDEE` **SANS DATE** sur la designation ⇒ elle ne
        clot RIEN, l'item RESTE dans la population et le porteur mort ressort ;
      · `"ailleurs"`     — la MENTION de la cloture d'une AUTRE ligne, sur une
        autre ligne du MEME item ⇒ elle ne clot RIEN non plus.
    ⛔ Aucun des deux ne DEBRANCHE : ils replantent la faute que la revue du
      2026-09-05 a mesuree (un item OUVERT sortait de la population sur une
      simple mention, et le controle restait `[OK ]`).
    """
    def _f(led, trk, faux, k=cle_neuve, avec=avec_solde):
        j, d0, d1, lignes, deb = premiere_designation_ouverte(trk)
        lignes[j] = lignes[j][:d0] + k + lignes[j][d1:]
        if avec == "sur-la-ligne":
            # ⇒ REPLANTE `SOLDEE` **SANS DATE** sur la ligne de la designation.
            #   Une cloture sans date ne clot RIEN : l'item RESTE dans la
            #   population, et le porteur mort doit ressortir.
            lignes[j] += " — SOLDEE PAR `dn5-7`"
        elif avec == "ailleurs":
            # ⇒ REPLANTE la MENTION de la cloture d'une AUTRE ligne, dans le
            #   MEME item mais sur une AUTRE ligne — la tournure exacte que le
            #   preambule du bloc emploie deja. Elle ⛔ ne doit rien clore.
            lignes.insert(deb + 1,
                          "  #      ⚠️ la ligne 15 est **SOLDEE LE 2026-09-05**,"
                          " voir plus bas.")
        return led, "\n".join(lignes)
    return _f


# Les deux cles fautives que les mutants replantent.
CLE_AC56_MORTE = "dn5-1-ce-qui-est-pousse-est-ce-qui-tourne"
CLE_AC56_INCONNUE = "dn9-9-une-cle-qui-n-existe-pas-au-tracker"


def cle_morte_est_morte(cockpit):
    """⇒ `(ok, dit)` — `CLE_AC56_MORTE` est-elle ENCORE morte AU TRACKER ?

    🔴 REVUE DU 2026-09-05 — LE COMMENTAIRE PROMETTAIT « resolue AU TRACKER,
    ⛔ pas ecrite en dur au hasard », ET RIEN NE LE VERIFIAIT. Si cette cle est
    renommee, ou repasse VIVANTE, le mutant `M1` teste alors **silencieusement**
    la branche INCONNU (ou ne rougit plus du tout) et « porteur mort » n'est
    plus garde par rien — le defaut que cette campagne existe pour compter.
    ⇒ ECHEC FERME, ⛔ pas un avertissement.
    """
    # ⚠️ LA GATE **CANONIQUE**, ⛔ pas celle de `--gate` : ce temoin porte sur le
    #    TRACKER et sur la semantique de statut du depot, ⛔ pas sur la gate mise
    #    a l'essai. Mesure du 2026-09-05 : lu depuis `--gate <stub>`, il sortait
    #    en ECHEC FERME **avant** le T0 et les trois bancs `B2*` — qui exigent
    #    justement de VOIR le T0 refuser — tombaient tous les trois.
    g = charge_gate(os.path.join(ICI, NOM_GATE))
    try:
        tracker, _c, _p = g.lit_tracker(os.path.join(cockpit, REL_TRACKER))
    except (OSError, UnicodeDecodeError) as x:
        return False, "⛔ tracker illisible : %s" % x
    st = g.statut_effectif(CLE_AC56_MORTE, tracker)
    if st is None:
        return False, ("⛔ `%s` est INCONNUE du tracker — le mutant `M1` ne"
                       " teste plus « porteur mort » mais « porteur inconnu »"
                       % CLE_AC56_MORTE)
    if st not in g.STATUTS_MORTS:
        return False, ("⛔ `%s` est `%s`, ⛔ pas morte — le mutant `M1` ne"
                       " rougirait plus, et « porteur mort » ne serait garde"
                       " par RIEN" % (CLE_AC56_MORTE, st))
    return True, "`%s` = `%s` ⇒ MORTE" % (CLE_AC56_MORTE, st)


def m_hors_depot(led, trk, faux):
    """⛔ AUCUNE mutation de donnees : c'est l'ARBORESCENCE qui est mutee.

    Voir `gate=` — la gate est jouee depuis un faux depot sans `firmware/`.
    """
    return led, trk


def gate_hors_depot(tmp, base=None):
    """Une copie de la gate posee dans un arbre qui N'EST PAS DeskNode.

    🎯 Faute replantee : le script deplace (copie dans un autre depot, dans un
    `site-packages`, dans un dossier de sauvegarde). `DESKNODE` est alors un
    repertoire qui existe — le controle d'origine, tautologique, passait —
    mais qui ne porte ni `firmware/` ni `tools/`.
    ⛔ Ce n'est PAS un debranchement : le code de la gate est copie A L'OCTET.
    """
    # 🔴 REVUE DE CODE dn4-44 — IL RECOPIAIT LE NOM DE LA GATE **EN DUR**,
    #    donc `--gate <version d'avant correctif>` etait IGNORE par ce mutant :
    #    il jouait la gate COURANTE. Or `--gate` existe precisement pour
    #    prouver un defaut « a vide ». ⇒ il copie LA GATE SOUS TEST.
    base = base or GATE
    faux = os.path.join(tmp, "hors-depot", "tools")
    if not os.path.isdir(faux):
        os.makedirs(faux)
        shutil.copy(base, os.path.join(faux, os.path.basename(base)))
        for f in ("dn_trace.py", "dn_sites.py"):
            shutil.copy(os.path.join(ICI, f), os.path.join(faux, f))
    return os.path.join(faux, os.path.basename(base))


# ── LES MUTANTS ──────────────────────────────────────────────────────────────
# ── dn8-1 / AC8.1.2 — LES DEUX TEMOINS DE L'INDENTATION ────────────────────
# 🔴 LA FAUTE REPLANTEE : une cle de `development_status` RE-INDENTEE de 2 a 4
#    espaces. Le fichier devient ILLISIBLE POUR TOUT PARSEUR YAML
#    (`yaml.ParserError`) — et le balayage textuel de `lit_tracker`, lui, ⛔ ne
#    voit RIEN : il apparie `^  cle:` ligne a ligne, la ligne re-indentee sort
#    simplement de la population. Mesure du 2026-09-11 : **101 cles vues avant,
#    100 apres**, et la gate rendait `BILAN : 35 OK, 0 KO` dans les deux cas.
# ⚠️ DEUX TEMOINS, ⛔ PAS UN, ET LA DIFFERENCE EST LA MESURE :
#    · une cle CITEE comme porteur (`epic-dn8`, 13 citations au ledger) faisait
#      DEJA rougir — mais **POUR LE MAUVAIS MOTIF** : « 13 CLE(S) FANTOME(S) »,
#      ⛔ jamais « le tracker ne se parse pas » ;
#    · une cle que PERSONNE ne cite ne faisait rougir RIEN. C'est elle le vrai
#      temoin du trou, et c'est elle qui prouve que le controle neuf porte.
#    ⛔ Garder seulement le premier aurait donne un mutant qui rougit sans que
#      le controle neuf serve a quoi que ce soit — « un banc qui juge sur le
#      `rc` global reste vert des qu'un AUTRE echec donne le meme `rc` ».
# ⚠️ **LE NOM D'UN MUTANT TIENT EN 28 CARACTERES**, et ce n'est ecrit NULLE
#    PART AILLEURS : le banc `B9-compte-joue` relit les noms A COLONNE FIXE
#    (`l[8:36]`). Un nom plus long ressort TRONQUE, ne s'apparie plus a la
#    liste, et le banc rougit en accusant le COMPTE. Mesure du 2026-09-11 :
#    `Y2-tracker-indente-cle-non-citee` (32) a fait sortir `annonce : 38 ·
#    verdicts : 37`. ⛔ Le banc avait raison, et il visait bien SON echec.
def mute_trk_indentation(court):
    """RE-INDENTE une cle de `development_status` de 2 a 4 espaces.

    ⛔ ELLE NE DEBRANCHE RIEN : elle replante, dans les DONNEES, la faute
    exacte qui a casse ce tracker deux fois en une journee.
    ⚠️ Si la cle a disparu, la mutation rend le tracker INCHANGE — la garde
       `change=("tracker",)` de la campagne le voit et ROUGIT, ⛔ elle ne
       laisse pas passer un mutant mort pour un gardien vivant.
    """
    def _f(led, trk, faux, c=court):
        return led, re.sub(
            r"^(  )(%s(?:-[a-z0-9\-]*)?:\s*[a-z\-]+)" % re.escape(c),
            r"  \1\2", trk, count=1, flags=re.M)
    return _f


MUTANTS = [
    # ── Les trois du cadrage, rejoues ───────────────────────────────────────
    M("A-porteur-en-prose",
      "un porteur EN PROSE qui ne releve d'AUCUNE des cinq formes",
      ins(verdict="PORTEE", porteur="a traiter quand on aura le temps"),
      cible="tout porteur releve de l'UNE des CINQ formes"),
    M("C-porteur-epic",
      "un porteur `epic-*` — INVISIBLE avant dn4-40, donc a vide",
      ins(verdict="PORTEE", porteur="epic-dn4")),
    # ⇒ doit rester VERT : `epic-dn4` est `in-progress`
    M("C2-porteur-epic-mort",
      "un porteur `epic-*` dont l'EPIC est clos ⇒ doit rougir",
      ins(verdict="PORTEE", porteur="epic-dn1"),
      cible="aucun porteur A VENIR n'est `done`/`superseded`"),
    M("B-incise-story-close",
      "une cle VIVANTE + une story CLOSE citee en incise",
      ins(verdict="BLOQUEE",
          porteur="bloquee par : le materiel decrit en dn4-1, absent du poste")),
    # ⇒ doit rester VERT : l'incise n'est plus un porteur
    # ── Les temoins NEGATIFS : la segmentation ⛔ ne rend pas permissif ──────
    M("E1-bouchon-tbd",
      "un porteur bouchon `TBD`",
      ins(verdict="PORTEE", porteur="TBD"),
      cible="tout porteur DESIGNE quelqu'un (⛔ ni vide ni bouchon)",
      aussi=["tout porteur releve de l'UNE des CINQ formes"]),
    M("E2-porteur-vide",
      "un champ porteur VIDE",
      ins(verdict="PORTEE", porteur=""),
      cible="tout porteur DESIGNE quelqu'un (⛔ ni vide ni bouchon)",
      aussi=["la forme 5 `—` est reservee a CONNAISSANCE",
             "aucune disposition A VENIR ne traverse la gate sans controle"]),
    M("E3-story-done",
      "un porteur qui est une story `done`",
      ins(verdict="RE-HEBERGEE", porteur="dn4-16"),
      cible="aucun porteur A VENIR n'est `done`/`superseded`"),
    M("E4-story-inconnue",
      "un porteur absent du tracker",
      ins(verdict="PORTEE", porteur="dn9-99"),
      cible="tout porteur A VENIR existe au tracker",
      aussi=["toute cle de porteur EXISTE au tracker (⛔ tous verdicts)"]),
    # ── Les formes, une par une ─────────────────────────────────────────────
    M("F2-sans-cle",
      "une forme 2 dont l'argument n'est PAS une cle",
      ins(verdict="PORTEE", porteur="backlog nomme : une story a creer un jour"),
      cible="toute forme 2 `backlog nomme :` nomme UNE cle"),
    M("F3-fait-muet",
      "un `bloquee par :` dont le fait est un bouchon",
      ins(verdict="BLOQUEE", porteur="bloquee par : TBD"),
      cible="tout `bloquee par :` NOMME un fait (⛔ ni vide ni bouchon)"),
    M("F3-porteur-deguise",
      "un `bloquee par :` qui se REDUIT a une cle de story",
      ins(verdict="BLOQUEE", porteur="bloquee par : dn4-16"),
      cible="aucun fait bloquant ne se REDUIT a une cle de story"),
    M("F4-hors-close",
      "une forme 4 `clos par :` sur un verdict qui n'est pas CLOSE",
      ins(verdict="PORTEE", porteur="clos par : dn4-16, motif eteint"),
      cible="la forme 4 `clos par :` ne porte que le verdict CLOSE",
      aussi=["aucune disposition A VENIR ne traverse la gate sans controle"]),
    # ── Les deux controles POSES PAR LA REVUE DU 2026-09-03, avec leur mutant.
    #    ⛔ On ne livre pas un controle « garde par rien » : c'est le defaut
    #    meme que cette campagne existe pour compter.
    M("F4-fossoyeur-muet",
      "une forme 4 `clos par :` dont l'argument est un BOUCHON",
      ins(verdict="CLOSE", porteur="clos par : TBD"),
      cible="toute forme 4 `clos par :` NOMME ce qui a clos"),
    M("F2-cle-fantome-sous-close",
      "une forme 2 nommant une story qui n'existe NULLE PART, sous CLOSE",
      ins(verdict="CLOSE", porteur="backlog nomme : dn9-99"),
      cible="toute cle de porteur EXISTE au tracker (⛔ tous verdicts)"),
    M("F5-hors-connaissance",
      "une forme 5 `—` sur un verdict qui n'est pas CONNAISSANCE",
      ins(verdict="BLOQUEE", porteur="—"),
      cible="la forme 5 `—` est reservee a CONNAISSANCE",
      aussi=["tout porteur DESIGNE quelqu'un (⛔ ni vide ni bouchon)",
             "aucune disposition A VENIR ne traverse la gate sans controle"]),
    M("V-verdict-hors-liste",
      "un verdict qui n'est pas l'un des CINQ",
      ins(verdict="REPORTEE", porteur=AUTO),
      cible="tout verdict est l'un des CINQ"),
    # ── Les controles voisins, pour retrecir « gardes par rien » ────────────
    M("G1-preuve-vide",
      "un champ preuve VIDE",
      ins(verdict="PORTEE", porteur=AUTO, preuve=""),
      cible="tout champ preuve est non vide"),
    M("G2-preuve-adresse-nue",
      "une preuve qui se REDUIT a un `fichier:ligne`",
      ins(verdict="PORTEE", porteur=AUTO, preuve="dn_ui.c:9948"),
      cible="aucune preuve ne se REDUIT a un `fichier:ligne`"),
    M("G3-date-invalide",
      "une date de disposition qui n'existe pas",
      ins(verdict="PORTEE", porteur=AUTO, date="2026-13-45"),
      cible="toute date de disposition est une date reelle"),
    M("G4-marqueur-hors-liste",
      "un marqueur de tete hors de la liste fermee",
      ins(verdict="PORTEE", porteur=AUTO, marqueur="🥕"),
      cible="aucun marqueur de tete n'est HORS LISTE", regen=1),
    M("G5-sans-disposition",
      "une entree ouverte SANS ligne de disposition",
      ins(verdict=None, porteur=None),
      cible="toute entree ouverte a une ligne de disposition"),
    M("G6-multi-disposition",
      "une entree qui porte DEUX lignes de disposition",
      ins(verdict="PORTEE", porteur=AUTO, double=True),
      cible="une entree porte UNE seule ligne de disposition"),

    # ═══ dn4-44 — LES MUTANTS NEUFS (AC2, AC3) ═══════════════════════════════
    M("H-ancre-collision",
      "DEUX entrees dont l'ancre 8-hexa du §9 COLLIDE — collision FORGEE",
      m_ancre_collision,
      cible="chaque ancre du §9 designe UNE seule entree",
      aussi=["le manifeste couvre 100 % des entrees ouvertes (AC2.7)",
             "chaque ligne du manifeste REPRODUIT ce que le script produit"],
      regen=1),
    M("H2-manifeste-ligne-absente",
      "UNE ligne du §9 retiree APRES regeneration ⇒ une entree SANS ligne",
      ins(verdict="PORTEE", porteur=AUTO),
      cible="le manifeste couvre 100 % des entrees ouvertes (AC2.7)",
      aussi=["chaque ligne du manifeste REPRODUIT ce que le script produit"],
      change=("ledger", "manifeste"), apres=a_ligne_du_manifeste_supprimee),
    M("H3-manifeste-ligne-falsifiee",
      "UNE cellule du §9 reecrite, l'ancre INCHANGEE ⇒ elle ne REPRODUIT plus",
      ins(verdict="PORTEE", porteur=AUTO),
      cible="chaque ligne du manifeste REPRODUIT ce que le script produit",
      change=("ledger", "manifeste"), apres=a_ligne_du_manifeste_falsifiee),
    M("H4-manifeste-absent",
      "le manifeste d'arbitrage n'est PAS livre",
      m_manifeste_absent,
      cible="le manifeste d'arbitrage est livre",
      change=("manifeste",), regen=None),
    M("H5-manifeste-sans-citation",
      "le manifeste ne cite plus le script qui produit son compte",
      m_ledger_sans_citation,
      cible="le manifeste cite le script qui produit son compte",
      change=("ledger", "manifeste"), apres=a_manifeste_sans_citation),
    M("H6-borne-retiree",
      "la borne de DEBUT du §9 disparait ⇒ le controle retombe sur TOUT le"
      " fichier",
      ins(verdict="PORTEE", porteur=AUTO),
      cible="le §9 porte ses deux bornes (le controle se borne a elles)",
      change=("ledger", "manifeste"), apres=a_borne_retiree),
    M("I-perimetre-vide",
      "le ledger perd toutes ses entrees ouvertes",
      m_ledger_vide,
      cible="le perimetre n'est pas vide",
      aussi=["le manifeste couvre 100 % des entrees ouvertes (AC2.7)",
             "chaque ligne du manifeste REPRODUIT ce que le script produit"],
      regen=1),
    M("J-statut-inconnu",
      "le statut d'un porteur n'est NI vivant NI mort (faute de frappe)",
      m_statut_inconnu,
      cible="tout statut de porteur est un statut CONNU",
      change=("ledger", "tracker")),
    M("K-collision-vivant-mort",
      "deux cles longues repliees sur la MEME cle courte, l'une VIVANTE et"
      " l'autre MORTE",
      m_collision_vivant_mort,
      cible="aucune collision de cle ne peut CHANGER un verdict",
      change=("tracker",)),
    M("L-hors-depot",
      "la gate jouee depuis un arbre qui n'est PAS le depot DeskNode",
      m_hors_depot,
      cible="le depot code est le depot DESKNODE",
      change=(), regen=None, gate=gate_hors_depot),
    # ── dn5-7 / report (3) de `dn5-5` — LA SECONDE POPULATION DE LA GATE ────
    #    ⚠️ LE ROUGE NATUREL NE REMPLACE PAS CES MUTANTS, ET C'EST LA
    #       DISTINCTION QUI COMPTE : le rouge naturel du 2026-09-05 (item 15
    #       ⇒ `dn5-6-…`, `done`) prouve que le controle voit **CE CAS-CI** ;
    #       ces mutants prouvent qu'il voit **LE CAS EN GENERAL**. Le premier
    #       disparait des que la ligne est soldee — les seconds, jamais.
    M("M1-ac56-porteur-mort",
      "un porteur de la liste AC5.6 du tracker qui est une story `done`",
      mute_ac56(CLE_AC56_MORTE),
      cible="tout porteur de la liste AC5.6 du tracker est VIVANT",
      change=("tracker",), motif=CLE_AC56_MORTE),
    M("M2-ac56-porteur-inconnu",
      "un porteur de la liste AC5.6 qui n'existe PAS au tracker",
      mute_ac56(CLE_AC56_INCONNUE),
      cible="tout porteur de la liste AC5.6 du tracker est VIVANT",
      change=("tracker",), motif=CLE_AC56_INCONNUE),
    # ── dn5-7 / REVUE DU 2026-09-05 — LA CLOTURE NE DOIT PAS ETRE UNE PORTE ──
    #    Mesuree AVANT correctif : la cloture se lisait sur TOUT le bloc de
    #    l'item ⇒ une simple MENTION (« la ligne 15 est SOLDEE LE … ») sortait
    #    un item OUVERT de la population, son porteur avec, **et le controle
    #    restait `[OK ]`**. Ces deux mutants replantent les DEUX variantes que
    #    rien n'exercait.
    M("M3-ac56-solde-cite-ailleurs",
      "un porteur MORT, + la MENTION de la cloture d'une AUTRE ligne dans le"
      " meme item ⇒ elle ne clot RIEN, le mort doit ressortir",
      mute_ac56(CLE_AC56_MORTE, avec_solde="ailleurs"),
      cible="tout porteur de la liste AC5.6 du tracker est VIVANT",
      change=("tracker",), motif=CLE_AC56_MORTE),
    M("M4-ac56-solde-sans-date",
      "un porteur MORT, + `SOLDEE` **SANS DATE** sur la ligne de la"
      " designation ⇒ une cloture sans date ne clot RIEN",
      mute_ac56(CLE_AC56_MORTE, avec_solde="sur-la-ligne"),
      cible="tout porteur de la liste AC5.6 du tracker est VIVANT",
      change=("tracker",), motif=CLE_AC56_MORTE),
    # ── dn8-1 / AC8.1.2 — LE TRACKER SE PARSE ────────────────────────────────
    M("Y1-tracker-indente-cite",
      "la cle `epic-dn8` RE-INDENTEE 2 ⇒ 4 espaces — le temoin PRESCRIT par"
      " le dossier. ⚠️ Il rougit DEJA sans le controle neuf, mais pour le"
      " MAUVAIS motif : `epic-dn8` est cite 13 fois comme porteur.",
      mute_trk_indentation("epic-dn8"),
      cible="le tracker se PARSE en YAML",
      aussi=["toute cle de porteur EXISTE au tracker (⛔ tous verdicts)",
             "tout porteur A VENIR existe au tracker",
             "tout porteur de la liste AC5.6 du tracker est VIVANT"],
      change=("tracker",), motif="    epic-dn8:",
      # ⚠️ `regen=1` : un tracker que le parseur REFUSE fait sortir la gate
      #    en 1, donc la REGENERATION du manifeste sort en 1 aussi. Attendre
      #    0 ferait rougir le mutant pour un effet qui est precisement celui
      #    qu'il replante. ⛔ Ce n'est pas une tolerance : c'est le rc ATTENDU.
      regen=1),
    M("Y2-tracker-indente-non-cite",
      "une cle que PERSONNE ne cite, RE-INDENTEE 2 ⇒ 4. ⛔ AVANT le controle"
      " neuf, la gate rendait `35 OK, 0 KO` sur un tracker que plus aucun"
      " parseur ne lit. C'est LE temoin du trou.",
      mute_trk_indentation("dn8-6-la-version-se-voit-sur-la-dalle"),
      cible="le tracker se PARSE en YAML",
      change=("tracker",),
      motif="    dn8-6-la-version-se-voit-sur-la-dalle:", regen=1),
]

# ── LE MUTANT DE TRACKER — le FAUX ROUGE ARME (AC40.1.d) ─────────────────────
# ⚠️ Il ne touche PAS le ledger : il fait passer a `done`, DANS LA COPIE, la
# story que la prose d'une entree parfaitement conforme cite comme FAIT
# BLOQUANT. Avant dn4-40, cette entree rougissait le jour ou cette story
# passait `done` — sans qu'un seul sens ait change.
MUTANT_TRACKER = "D-faux-rouge-arme"


# ═══════════════════════════════════════════════════════════════════════════
#  LES EXEMPTIONS — dn4-44 / AC4.3
#  ⛔ NI LISTE D'EXCLUSION MUETTE, NI `continue-on-error`, NI SEUIL TOLERE.
#  Chaque exemption porte son MOTIF et son TEMOIN. Le temoin est une MESURE :
#  le jour ou la raison disparait, l'exemption se DEMENT et la campagne rougit.
# ═══════════════════════════════════════════════════════════════════════════

def _legitime_au_tri(libelle):
    """Temoin : ce libelle est-il classe LEGITIME **et prouve par mutant** dans
    `campagne_ctrl_dn440.py` ?

    🎯 C'EST LA FALSIFIABILITE DE L'EXEMPTION. Si quelqu'un retire le cas du
    tableau `CAS`, ou le reclasse, l'exemption tombe ET LA CAMPAGNE ROUGIT.
    ⛔ Elle ne se contente pas de citer `T2-tri-ctrl.txt` : ce fichier est
    PERIME (mesure du 2026-09-03), et une capture ne garde rien.
    """
    try:
        import campagne_ctrl_dn440 as CC
    except Exception:
        return False, "⛔ `campagne_ctrl_dn440.py` INTROUVABLE"
    # 🔴 REVUE DE CODE dn4-44 (2026-09-03) — `BRANCHE` EST ACCEPTE, ET C'EST
    #    LA MESURE QUI L'IMPOSE, ⛔ pas un assouplissement. Le tri rendu strict
    #    a reclasse deux de ces cinq libelles de `LEGITIME` en `BRANCHE` : leur
    #    chemin d'echec ⛔ ne sort pas en amont, il prend une branche qui trace
    #    le MEME libelle **KO**. ⚠️ Le motif d'exemption ecrit juste en dessous
    #    DISAIT DEJA cela (« le `except` juste au-dessus fait `ctrl(False, …)`
    #    PUIS `return 1` ») — c'est le TRI qui avait tort, ⛔ pas le motif.
    # 🎯 CE QUE ÇA NE RELACHE PAS : les deux classes prouvent que le controle
    #    ⛔ ne peut pas rester vert quand sa propriete est fausse — un
    #    `LEGITIME` parce que la gate sort avant, une `BRANCHE` parce que le
    #    meme libelle ressort KO. Un `TROU`, un `INERTE`, ou l'ABSENCE du cas
    #    font toujours TOMBER l'exemption.
    for gate, lib, verdict, _m, _q in CC.CAS:
        if (os.path.basename(gate) == os.path.basename(GATE)
                and dn_sites.apparie(lib, libelle)
                and verdict in ("LEGITIME", "BRANCHE")):
            return True, "classe %s au tableau `CAS` du tri" % verdict
    return False, ("⛔ plus classe LEGITIME ni BRANCHE dans"
                   " `campagne_ctrl_dn440.CAS`")


EXEMPTIONS = [
    # (libelle, motif de l'exemption, temoin)
    ("le depot cockpit est atteignable",
     "PREREQUIS, ⛔ pas un controle : son chemin d'echec sort EN AMONT"
     " (rc=4, `PREREQUIS ABSENT`). Prouve par mutant au tri d'AC40.2.",
     _legitime_au_tri),
    ("le ledger est present",
     "idem — meme garde amont, meme mutant (`m_ledger_absent`).",
     _legitime_au_tri),
    ("le tracker est present",
     "idem.",
     _legitime_au_tri),
    ("le ledger se LIT en UTF-8",
     "le chemin d'echec est le `except` juste au-dessus : il fait `ctrl(False,"
     " …)` PUIS `return 1`. Prouve par `m_ledger_binaire`.",
     _legitime_au_tri),
    ("le tracker se LIT en UTF-8",
     "idem — prouve par `m_tracker_binaire`.",
     _legitime_au_tri),
]


# ═══════════════════════════════════════════════════════════════════════════
#  LE TIR
# ═══════════════════════════════════════════════════════════════════════════

def _lignes(a, b):
    """Les lignes de `b` qui ne sont pas dans `a`, au meme rang — le DETAIL du
    changement. ⛔ Un diff paresseux : il suffit a dire CE QUI a change."""
    la, lb = a.split("\n"), b.split("\n")
    sa = set(la)
    return [l for l in lb if l not in sa]


def joue(cockpit_src, mutant, tmp):
    """Monte une COPIE du cockpit, applique UNE mutation, joue la gate.

    Rend `(rc, trace, change, rc_regen, gate_jouee)`.
      `trace`  = `{cle: (verdict, site, libelle)}` — cle = `(site, libelle)`.
      `change` = `{artefact: [lignes ajoutees]}` — ce qui a REELLEMENT change.
    """
    gate = GATE
    if mutant is not None and mutant.gate is not None:
        gate = mutant.gate(tmp, GATE)
    faux = os.path.join(tmp, "cockpit")
    shutil.rmtree(faux, ignore_errors=True)
    os.makedirs(os.path.join(faux, os.path.dirname(REL_LEDGER)))
    led = io.open(os.path.join(cockpit_src, REL_LEDGER), encoding="utf-8").read()
    trk = io.open(os.path.join(cockpit_src, REL_TRACKER), encoding="utf-8").read()
    man_src = os.path.join(cockpit_src, REL_MANIFESTE)
    p_man = os.path.join(faux, REL_MANIFESTE)
    man0 = None
    if os.path.isfile(man_src):
        shutil.copy(man_src, p_man)
        man0 = io.open(p_man, encoding="utf-8").read()
    change = {}
    if mutant is not None and mutant.muteur is not None:
        led_a, trk_a = led, trk
        led, trk = mutant.muteur(led, trk, faux)
        # 🔴 REVUE 2026-09-03 — UNE MUTATION QUI NE CHANGE RIEN REND UN VERT
        #    QUI NE PROUVE RIEN. Mesure : le mutant de tracker visait une cle
        #    COURTE la ou le tracker porte la cle LONGUE ⇒ le `re.sub` ne
        #    mordait pas, le fichier ressortait identique A L'OCTET, et la
        #    campagne imprimait « VERT (attendu) » quoi que fasse la gate.
        # 🔴 dn4-44 / AC5.2 — ⛔ « QUELQUE CHOSE A CHANGE » NE DIT PAS QUE **LA
        #    BONNE CHOSE** A CHANGE. On rend le DETAIL, et l'appelant le
        #    confronte a ce que le mutant DECLARE toucher.
        if led != led_a:
            change["ledger"] = _lignes(led_a, led)
        if trk != trk_a:
            change["tracker"] = _lignes(trk_a, trk)
        if man0 is not None:
            man1 = io.open(p_man, encoding="utf-8").read() \
                if os.path.isfile(p_man) else None
            if man1 != man0:
                change["manifeste"] = _lignes(man0, man1 or "")
    io.open(os.path.join(faux, REL_LEDGER), "w", encoding="utf-8").write(led)
    io.open(os.path.join(faux, REL_TRACKER), "w", encoding="utf-8").write(trk)
    # 🔴 SANS CETTE REGENERATION, LA CAMPAGNE NE MESURE RIEN — MESURE.
    #    Le manifeste est ancre par NUMERO DE LIGNE : inserer une entree
    #    temoin decale les 267 reperes, le controle « chaque ligne du
    #    manifeste REPRODUIT ce que le script produit » rougit, et il
    #    MASQUE le controle que le mutant visait. Premiere passe reelle :
    #    14 mutants sur 14 ne faisaient rougir QUE ce controle-la.
    #    ⇒ On regenere le manifeste DANS LA COPIE (la commande de dn4-39),
    #      pour que le seul rouge restant soit celui qu'on cherche.
    # 🔴 dn4-44 / AC5.6 — SON `rc` EST DESORMAIS RENDU, ET TESTE. Il etait
    #    JETE : une regeneration en echec laissait la campagne mesurer un
    #    manifeste perime, en annoncant un bilan.
    rc_regen = None
    man2 = io.open(p_man, encoding="utf-8").read() if os.path.isfile(p_man) else None
    if man2 is not None:
        # 🔴 REVUE DE CODE dn4-44 — CE SOUS-PROCESSUS N'AVAIT PAS D'`env=`,
        #    donc il HERITAIT d'un `DN_TRACE_CTRL` pose par l'appelant et
        #    ecrivait HORS du repertoire jetable. MESURE : 293 lignes versees
        #    dans un fichier externe. Si ce fichier est la trace d'une autre
        #    campagne, l'agregation « un KO l'emporte » rend la pollution
        #    IRREVERSIBLE pour les cles touchees.
        r = subprocess.run([sys.executable, gate, "--cockpit", faux,
                            "--manifeste", "--en-place"],
                           capture_output=True, text=True,
                           env=dict(os.environ,
                                    DN_TRACE_CTRL=os.path.join(tmp, "regen.txt")))
        rc_regen = r.returncode
        man2 = io.open(p_man, encoding="utf-8").read()
    if mutant is not None and mutant.apres is not None:
        mutant.apres(faux)
        man3 = io.open(p_man, encoding="utf-8").read() \
            if os.path.isfile(p_man) else None
        if man3 is None:
            change.setdefault("manifeste", []).append("(retire)")
        elif man3 != man2:
            change.setdefault("manifeste", []).extend(_lignes(man2 or "", man3))
    tr = os.path.join(tmp, "trace.txt")
    if os.path.isfile(tr):
        os.remove(tr)
    env = dict(os.environ, DN_TRACE_CTRL=tr)
    p = subprocess.run([sys.executable, gate, "--cockpit", faux],
                       capture_output=True, text=True, env=env)
    return p.returncode, dn_trace.lit(tr), change, rc_regen, gate


def cles_du_libelle(libelle, par_lib, gate=None):
    """Les cles de trace attendues pour un libelle — ⛔ jamais une adresse."""
    base = os.path.basename(gate or GATE)
    return {dn_trace.cle("%s:%d" % (base, l), libelle)
            for l in par_lib.get(libelle, [])}


def _fmt(k):
    s, l = dn_trace.parts(k)
    return "%s « %s »" % (s, l[:44])


# ═══════════════════════════════════════════════════════════════════════════
#  LES BANCS — dn4-44 / AC1.3
#
#  🔴 UN CORRECTIF QUI TIENT MAIS QUE **RIEN NE GARDE** EST LE DEFAUT MEME DE
#     CETTE CAMPAGNE. Les trois correctifs de la revue du 2026-09-03 tenaient —
#     il a fallu les exercer A LA MAIN pour l'etablir, et le troisieme se
#     debranchait sans que rien ne bouge.
#  ⛔ CHAQUE BANC **REPLANTE** LA FAUTE D'ORIGINE. Aucun ne debranche une garde.
# ═══════════════════════════════════════════════════════════════════════════

STUBS = {
    # nom : (source de la fausse gate, ce que le T0 doit refuser)
    "B2a-T0-rc-non-nul": (
        "import os, sys\n"
        "f = os.environ.get('DN_TRACE_CTRL')\n"
        "if f:\n"
        "    open(f, 'a').write('faux.py:1\\tOK\\tun controle qui passe\\n')\n"
        "sys.exit(1)\n",
        "rc=1 ⛔ non nul"),
    "B2b-T0-trace-vide": (
        "import sys\nsys.exit(0)\n",
        "⛔ AUCUN controle trace — la gate n'a pas tourne"),
    "B2c-T0-deja-rouge": (
        "import os, sys\n"
        "f = os.environ.get('DN_TRACE_CTRL')\n"
        "if f:\n"
        "    open(f, 'a').write('faux.py:1\\tKO\\tun controle deja rouge\\n')\n"
        "sys.exit(0)\n",
        "l'arbre propre n'est pas vert"),
}

SOURCE_4_FORMES = '''# -*- coding: utf-8 -*-
def ctrl(ok, libelle, d=""):
    return ok
def f(a, b, n):
    ctrl(True, f"un libelle en f-string {n}")
    ctrl(True, 'un libelle en guillemets simples')
    ctrl(True, "un libelle en deux " "fragments implicites")
    ctrl(all(a, b), "un libelle apres une virgule dans le premier argument")
'''


# Le mutant que le banc `B6` retire pour prouver que le compte GARDE. Il est
# NOMME ici : un banc qui piocherait « le premier de la liste » changerait de
# sujet a chaque reordonnancement du tableau.
TEMOIN_RETIRE = "G5-sans-disposition"


def bancs(cockpit, tmp, moi):
    """Les gardes de la campagne elle-meme. Rend `[(nom, ok, dit)]`."""
    out = []

    # ── B1 : LA GARDE DE MUTATION NULLE ─────────────────────────────────────
    nul = M("banc", "un muteur qui ne mord sur RIEN",
            lambda led, trk, faux: (led, trk))
    _rc, _tr, ch, _rg, _g = joue(cockpit, nul, tmp)
    out.append(("B1-mutation-nulle", not ch,
                "la mutation ne change RIEN ⇒ `change` doit etre VIDE"
                " (vu : %s)" % (sorted(ch) or "vide")))

    # ── B1b : UNE MUTATION QUI MORD LE MAUVAIS FICHIER ──────────────────────
    faux_cible = M("banc", "un muteur qui declare le tracker et mord le ledger",
                   lambda led, trk, faux: (led + "\n- ⚪ mordu\n", trk),
                   change=("tracker",))
    _rc, _tr, ch, _rg, _g = joue(cockpit, faux_cible, tmp)
    out.append(("B1b-mutation-hors-cible", set(ch) != set(faux_cible.change),
                "declare `tracker`, mord `%s` ⇒ l'ecart doit se VOIR"
                % (", ".join(sorted(ch)) or "rien")))

    # ── B1c : LE PREFIXE SANS BORNE MORD LA MAUVAISE CLE ────────────────────
    #    🎯 REPLANTE la faute exacte du mutant de tracker : `dn4-41` matchait
    #       `dn4-410-…` aussi bien que `dn4-41-…`, et `count=1` prend la
    #       PREMIERE. Latent au 2026-09-03 (aucune cle `dn4-41x`), et c'est
    #       precisement pourquoi il faut un banc : le jour ou elle existe,
    #       plus personne ne regarde.
    trk_piege = ("development_status:\n"
                 "  dn4-410-un-piege-en-amont: backlog\n"
                 "  dn4-41-la-vraie-cible: in-progress\n")
    # 🔴 REVUE DE CODE dn4-44 — CE BANC N'INTERROGEAIT QUE **L'ORACLE**
    #    (`_mute_trk_cle`), qui ne mute RIEN : la mutation reelle est faite par
    #    `mute_tracker`, et le motif borne est ecrit dans les DEUX. Une
    #    regression posee dans `mute_tracker` seul laissait donc le banc VERT,
    #    et la campagne imprimait « cle mutee : `dn4-41-la-vraie-cible` » —
    #    une phrase FAUSSE, calculee depuis l'oracle et jamais depuis la
    #    mutation. ⇒ le banc lit CE QUI A REELLEMENT ETE MUTE.
    k1 = _mute_trk_cle(trk_piege, "dn4-41")
    _l, trk_apres = mute_tracker("dn4-41")("", trk_piege, None)
    mutees = [l.strip() for l in trk_apres.split("\n") if l.endswith(": done")]
    out.append(("B1c-prefixe-sans-borne",
                k1 == "dn4-41-la-vraie-cible"
                and mutees == ["dn4-41-la-vraie-cible: done"],
                "l'oracle ET le muteur doivent viser `dn4-41-la-vraie-cible`,"
                " ⛔ pas `dn4-410-…` (oracle : %s · mute : %s)"
                % (k1, mutees or "rien")))

    # ── B2 : LE T0 QUI GARDE ────────────────────────────────────────────────
    for nom, (src, attendu) in sorted(STUBS.items()):
        d = os.path.join(tmp, "stubs")
        if not os.path.isdir(d):
            os.makedirs(d)
        p = os.path.join(d, nom.replace("-", "_") + ".py")
        io.open(p, "w", encoding="utf-8").write(src)
        r = subprocess.run([sys.executable, moi, "--cockpit", cockpit,
                            "--gate", p, "--sans-bancs"],
                           capture_output=True, text=True)
        vu = ("campagne ININTERPRETABLE" in r.stdout) and r.returncode == 1
        out.append((nom, vu, "%s ⇒ `campagne ININTERPRETABLE`, rc=1"
                             " (rc vu : %d)" % (attendu, r.returncode)))

    # ── B3 : L'AGREGATION « UN KO L'EMPORTE » ───────────────────────────────
    ftr = os.path.join(tmp, "banc-trace.txt")
    io.open(ftr, "w", encoding="utf-8").write(
        "g.py:10\tKO\tun controle dans une boucle\n"
        "g.py:10\tOK\tun controle dans une boucle\n")
    d = dn_trace.lit(ftr)
    k = dn_trace.cle("g.py:10", "un controle dans une boucle")
    out.append(("B3-ko-l-emporte", d.get(k, ("?",))[0] == "KO",
                "KO puis OK sur la MEME cle ⇒ la lecture doit rendre KO"
                " (vu : %s)" % d.get(k, ("(absent)",))[0]))

    # ── B3b : LE DISCRIMINANT — deux controles DIFFERENTS au meme site ──────
    #    🎯 REPLANTE la faute mesuree sur la gate du dossier : un site dans une
    #       boucle, un libelle par fichier balaye. Sans discriminant, les deux
    #       se replient sur UNE cle et l'un des deux DISPARAIT du compte.
    io.open(ftr, "w", encoding="utf-8").write(
        "g.py:20\tOK\tle fichier A est conforme\n"
        "g.py:20\tOK\tle fichier B est conforme\n")
    d = dn_trace.lit(ftr)
    out.append(("B3b-discriminant", len(d) == 2,
                "deux libelles au MEME site ⇒ DEUX cles, ⛔ pas une"
                " (vu : %d)" % len(d)))

    # ── B4 : LA RESOLUTION DES CIBLES, LES QUATRE FORMES ────────────────────
    p = os.path.join(tmp, "banc_formes.py")
    io.open(p, "w", encoding="utf-8").write(SOURCE_4_FORMES)
    par = dn_sites.par_libelle(p)
    manque = [x for x in ("un libelle en guillemets simples",
                          "un libelle en deux fragments implicites",
                          "un libelle apres une virgule dans le premier"
                          " argument") if x not in par]
    fstr = [ligne for ligne, t, lib, forme in dn_sites.sites(p)
            if forme == "illisible"]
    out.append(("B4-quatre-formes", not manque and len(fstr) == 1,
                "3 formes LUES + la f-string DITE illisible"
                " (manquent : %s · illisibles : %d)"
                % (", ".join(manque) or "aucune", len(fstr))))

    # ── B5 : LE `rc` DE LA REGENERATION ─────────────────────────────────────
    #    REPLANTE : un manifeste sans bornes ⇒ `--en-place` sort en 1. La
    #    campagne DOIT le voir, ⛔ pas mesurer un manifeste perime.
    def _casse_bornes(led, trk, faux):
        p = os.path.join(faux, REL_MANIFESTE)
        if os.path.isfile(p):
            s = io.open(p, encoding="utf-8").read()
            io.open(p, "w", encoding="utf-8").write(
                s.replace(_borne_debut(), "<!-- borne mangee par le banc -->"))
        return led, trk
    b5 = M("banc", "manifeste sans borne de debut", _casse_bornes,
           change=("manifeste",))
    _rc, _tr, _ch, rg, _g = joue(cockpit, b5, tmp)
    out.append(("B5-rc-regeneration", rg not in (0, None),
                "une regeneration en echec doit RENDRE son rc (vu : %s)" % rg))

    # ── B6 : LE COMPTE « GARDES PAR RIEN » **GARDE** (AC4.1) ────────────────
    #    🎯 REPLANTE la faute exacte : un controle a qui personne n'a donne de
    #       mutant. On retire UN mutant et la campagne DOIT sortir en echec.
    #    ⛔ Ce n'est pas un debranchement : la garde reste entiere, c'est la
    #       DONNEE (la couverture) qui redevient fautive.
    #    ⚠️ Elle coutait `rc=0` en publiant 15 nus : c'est tres exactement
    #       pourquoi AC40.7.a a pu etre refutee sans que rien ne rougisse.
    # ⚠️ UN SEUL TIR POUR B6 **ET** B9 — mesure de la revue : chaque
    #    sous-campagne coute ~30 s, et le script des temoins la rejoue 16 fois.
    #    Deux tirs separes portaient la suite de temoins a ~15 min. Les deux
    #    leviers sont ORTHOGONAUX (`--sans-mutant` retire de la liste,
    #    `--mutant-fantome` ajoute un declare-non-joue) ⇒ ils se composent sans
    #    se masquer, et chaque banc lit ce qui le regarde dans la MEME sortie.
    r = subprocess.run([sys.executable, moi, "--cockpit", cockpit,
                        "--sans-bancs", "--sans-mutant", TEMOIN_RETIRE,
                        "--mutant-fantome"],
                       capture_output=True, text=True)
    #    ⚠️ IL VISE **SON** ECHEC, ⛔ PAS LE `rc`. Le `rc` vaut 1 des qu'un
    #       echec QUELCONQUE survient : teste ainsi, ce banc est reste VERT
    #       alors que la garde etait debranchee, parce que le balayage du
    #       mutant fantome fournissait le meme `rc`. Mesure de la revue.
    echecs6 = re.search(r"^⛔ ECHECS : (.*)$", r.stdout, flags=re.M)
    vu = (r.returncode == 1
          and re.search(r"GARDES PAR RIEN\s*:\s*1\b", r.stdout) is not None
          and echecs6 is not None
          and "gardes-par-rien" in echecs6.group(1))
    out.append(("B6-le-compte-garde", vu,
                "sans le mutant `%s` ⇒ 1 controle nu, et `gardes-par-rien`"
                " DANS la liste des echecs (rc : %d · echecs : %s)"
                % (TEMOIN_RETIRE, r.returncode,
                   echecs6.group(1)[:60] if echecs6 else "aucun")))

    # ── B9 : AC5.4 — LE COMPTE ANNONCE EST LE COMPTE **JOUE** ───────────────
    #    🎯 FAUTE REPLANTEE : le bilan annoncait `len(MUTANTS) + 1` — il disait
    #       donc « 23 » meme quand le 23e n'etait pas tire.
    #    🔴 CE BANC A DEMANDE UN LEVIER NEUF, ET C'EST UN CONSTAT DE LA REVUE :
    #       avec `--sans-mutant`, l'entree quitte LA LISTE, donc le compte
    #       DECLARE et le compte JOUE bougent ENSEMBLE et la faute d'origine
    #       reste **INOBSERVABLE**. Il faut un mutant qui soit DANS la liste et
    #       qui ⛔ ne soit PAS joue ⇒ `--mutant-fantome`. ⛔ Cocher ce banc sans
    #       ce levier aurait donne un vert qui ne prouve rien — le defaut meme
    #       que cette story compte.
    #    ⚠️ Parse a COLONNE FIXE : `"   [XX] "` fait EXACTEMENT 8 caracteres,
    #       puis 28 de nom. Ce banc est sorti rouge a son premier tir sur un
    #       decoupage decale d'UN caractere — le piege n°6 des Dev Notes, paye
    #       ici meme.
    m9 = re.search(r"BILAN CAMPAGNE\s*:\s*(\d+) mutant", r.stdout)
    noms9 = {l[8:36].strip() for l in r.stdout.split("\n")
             if re.match(r"^   \[(OK|!!)\] ", l)}
    joues9 = {n for n in noms9
              if n in {m.nom for m in MUTANTS} | {MUTANT_TRACKER}}
    out.append(("B9-compte-joue", bool(m9) and int(m9.group(1)) == len(joues9),
                "un mutant DECLARE et non joue ⇒ le bilan annonce le nombre"
                " VERDICTE, ⛔ pas le nombre declare (annonce : %s ·"
                " verdicts : %d)"
                % (m9.group(1) if m9 else "aucun", len(joues9))))

    # ── B7 : UNE EXEMPTION SE **DEMENT** QUAND SA RAISON DISPARAIT (AC4.3) ──
    #    ⛔ Une liste d'exclusion muette passerait ce banc ; une exemption
    #       falsifiable, non. Le temoin negatif est le seul qui prouve quelque
    #       chose : ce depot a deja paye deux fois un jeton d'exemption ACCORDE
    #       par sa simple citation.
    faux_ok, _d = _legitime_au_tri("un libelle qui n'est classe NULLE PART")
    vrai_ok, _d2 = _legitime_au_tri(EXEMPTIONS[0][0])
    # ⚠️ REVUE DE CODE dn4-44 — B7 NE TESTAIT QUE LE CAS LOINTAIN (un libelle
    #    totalement etranger). Il prouvait donc que le temoin n'est pas la
    #    constante `True`, ⛔ pas qu'il est FALSIFIABLE. Le QUASI-MISS est le
    #    vrai test : tant qu'`apparie()` etait un prefixe symetrique,
    #    `_legitime_au_tri("l")` rendait `True` — un joker. Il est desormais
    #    une egalite stricte, et ce banc le TIENT.
    joker_ok, _d3 = _legitime_au_tri(EXEMPTIONS[0][0][:1])
    tronque_ok, _d4 = _legitime_au_tri(EXEMPTIONS[0][0][:-3])
    out.append(("B7b-exemption-sans-joker",
                (not joker_ok) and (not tronque_ok),
                "un PREFIXE du libelle exempte ⇒ temoin FAUX (vus : %s / %s)"
                % (joker_ok, tronque_ok)))

    out.append(("B7-exemption-falsifiable", (not faux_ok) and vrai_ok,
                "un libelle hors du tri ⇒ temoin FAUX ; un libelle classe"
                " LEGITIME ⇒ temoin VRAI (vus : %s / %s)" % (faux_ok, vrai_ok)))

    # ═══════════════════════════════════════════════════════════════════════
    #  B8 · B9 · B10 — LES TROIS CORRECTIFS QUE **RIEN NE GARDAIT**
    #
    #  🔴 TROUVES PAR LA REVUE DE CODE DU 2026-09-03, ET C'EST LE DEFAUT MEME
    #     DE CETTE STORY DANS SON PROPRE INSTRUMENT : les 12 bancs vivaient
    #     TOUS dans ce fichier, et `campagne_ctrl_dn440.py` n'en recevait
    #     AUCUN. AC5.3, AC5.4 et le T0 neuf du tri etaient donc des correctifs
    #     « gardes par rien » — dans la marche qui existe pour les compter.
    #     ⇒ DECISION OWNER DU 2026-09-03 : les ARMER, ⛔ pas fermer avec ecart.
    #  ⛔ Chacun REPLANTE l'etat d'avant correctif. Aucun ne debranche.
    # ═══════════════════════════════════════════════════════════════════════
    import campagne_ctrl_dn440 as CC

    # ── B8 : AC5.3 — UN LIBELLE QUI NE SURVIT QUE DANS UN COMMENTAIRE, OU QUE
    #    DANS UN `ctrl()`, N'EST **PAS** UN REMEDE.
    #    🎯 FAUTE REPLANTEE : `libelle in dn_sites.texte(...)` sur le texte
    #       BRUT. Elle rendait `[OK] REMEDE APPLIQUE` pour un controle
    #       PUREMENT SUPPRIME dont le libelle trainait en commentaire — le
    #       motif « citer le jeton l'ACCORDE », deja paye deux fois ici.
    d8 = os.path.join(tmp, "b8")
    if not os.path.isdir(d8):
        os.makedirs(d8)
    LIB8 = "un libelle temoin du banc B8"
    cas8 = {
        "commentaire": "# ctrl(True, \"%s\")\nx = 1\n" % LIB8,
        "dans-un-ctrl": "def ctrl(a, b):\n    return a\nctrl(True, \"%s\")\n" % LIB8,
        "un-print": "def ctrl(a, b):\n    return a\nprint(\"%s\")\n" % LIB8,
    }
    attendu8 = {"commentaire": False, "dans-un-ctrl": False, "un-print": True}
    vu8 = {}
    for nom8, src8 in cas8.items():
        f8 = "g_%s.py" % nom8.replace("-", "_")
        io.open(os.path.join(d8, f8), "w", encoding="utf-8").write(src8)
        vu8[nom8] = CC.survit_au_source(d8, f8, LIB8)
    out.append(("B8-remede-prouve", vu8 == attendu8,
                "commentaire ⇒ False · dans un `ctrl()` ⇒ False · `print` ⇒"
                " True (vu : %s)" % vu8))

    # ── B10 : AC4.2 — LE T0 DU TRI REFUSE UNE GATE MORTE.
    #    🎯 FAUTE REPLANTEE : le tri n'avait AUCUN T0 — le `rc` etait imprime
    #       nulle part et jete, si bien qu'une gate morte faisait sortir un cas
    #       `INERTE` VERT gratuitement (une trace vide satisfait « jamais
    #       atteint »). Mesure du cadrage : 4 verdicts sur 13.
    #    ⛔ On ne debranche rien : on donne au T0 REEL des donnees fautives.
    #    ⚠️ LE CAS « MORT » TRACE DES CONTROLES **AVANT** DE PLANTER, ET
    #       C'EST CE QUI ISOLE LA GARDE. Ecrit avec une trace VIDE, il etait
    #       rattrape par la branche « aucun controle trace » : debrancher
    #       `a_plante` laissait alors le banc VERT, et son temoin negatif l'a
    #       montre. Une gate qui meurt EN COURS DE ROUTE est le seul cas que
    #       SEULE la detection de plantage attrape.
    def _mort(_g, _m, _c):
        return 1, {dn_trace.cle("g.py:1", "un controle avant le plantage"):
                   ("OK", "g.py:1", "un controle avant le plantage")}, \
            "", "Traceback (most recent call last)\n  RuntimeError\n"

    def _muet(_g, _m, _c):
        return 0, {}, "BILAN : 0 OK, 0 KO\n", ""

    def _sain(_g, _m, _c):
        return 0, {dn_trace.cle("g.py:1", "un controle"): ("OK", "g.py:1",
                                                           "un controle")}, \
            "BILAN : 1 OK, 0 KO\n", ""
    m_mort = CC.t0_de("g.py", cockpit, joueur=_mort)[2]
    m_muet = CC.t0_de("g.py", cockpit, joueur=_muet)[2]
    m_sain = CC.t0_de("g.py", cockpit, joueur=_sain)[2]
    out.append(("B10-T0-du-tri",
                bool(m_mort) and bool(m_muet) and not m_sain,
                "gate PLANTEE et gate MUETTE ⇒ ININTERPRETABLE ; gate saine ⇒"
                " aucun motif (vus : %s / %s / %s)"
                % (bool(m_mort), bool(m_muet), bool(m_sain))))

    return out


def _mute_trk_cle(trk, court):
    """La cle LONGUE que le mutant de tracker mute reellement — ⛔ pas celle
    qu'il croit muter.

    🔴 dn4-44 / AC5.2 — LE MOTIF EST BORNE. `dn4-41[a-z0-9\\-]*:` matchait
    `dn4-410-…` aussi bien que `dn4-41-…`, et `count=1` prend la PREMIERE du
    fichier. La borne `(?:-…)?` exige que ce qui suit la cle courte soit un
    tiret ou les deux points. ⛔ Un `re.sub` qui mord ailleurs reste vert.
    """
    m = re.search(r"^  (%s(?:-[a-z0-9\-]*)?):\s*[a-z\-]+" % re.escape(court),
                  trk, flags=re.M)
    return m.group(1) if m else None


def mute_tracker(court):
    """Le muteur du faux rouge ARME, avec son motif BORNE."""
    def _f(led, trk, faux, c=court):
        return led, re.sub(
            r"^(  %s(?:-[a-z0-9\-]*)?:)\s*[a-z\-]+" % re.escape(c),
            r"\1 done", trk, count=1, flags=re.M)
    return _f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cockpit", default=os.path.join(
        os.environ.get("HOME") or "/nonexistent", "projects", "compagnon_project"))
    ap.add_argument("--liste", action="store_true")
    ap.add_argument("--bancs-seuls", dest="bancs_seuls", action="store_true",
                    help="ne jouer QUE les bancs (⇒ temoins negatifs)")
    ap.add_argument("--mutant-fantome", dest="mutant_fantome",
                    action="store_true",
                    help="⛔ USAGE INTERNE : DECLARER un mutant sans le jouer,"
                         " pour rendre OBSERVABLE l'ecart entre le compte"
                         " ANNONCE et le compte JOUE (banc B9)")
    ap.add_argument("--sans-mutant", dest="sans_mutant", default=None,
                    help="⛔ USAGE INTERNE : retirer UN mutant, pour prouver"
                         " que le compte « gardes par rien » GARDE (banc B6)")
    ap.add_argument("--sans-bancs", dest="sans_bancs", action="store_true",
                    help="⛔ USAGE INTERNE : evite la recursion quand un banc"
                         " rejoue la campagne contre une fausse gate")
    ap.add_argument("--gate", default=None,
                    help="jouer contre une AUTRE version de la gate "
                         "(⇒ prouver l'etat AVANT correctif)")
    a = ap.parse_args()

    global GATE, MUTANTS
    if a.gate:
        GATE = os.path.abspath(a.gate)
    if a.sans_mutant:
        avant = len(MUTANTS)
        MUTANTS = [m for m in MUTANTS if m.nom != a.sans_mutant]
        if len(MUTANTS) == avant:
            print("⛔ `--sans-mutant %s` ne designe AUCUN mutant declare"
                  % a.sans_mutant)
            return 2

    if a.mutant_fantome:
        # 🔴 LE LEVIER QUI REND AC5.4 MESURABLE — REVUE DE CODE dn4-44.
        #    ⚠️ Sans lui la faute d'origine (`len(MUTANTS) + 1`) est
        #    INOBSERVABLE : `--sans-mutant` retire l'entree de LA LISTE, donc
        #    le compte declare et le compte joue bougent ENSEMBLE. Il faut un
        #    mutant qui soit DANS la liste et ⛔ pas joue — exactement la
        #    situation que le balayage d'AC2.6 existe pour attraper, et que le
        #    bilan annoncait quand meme.
        MUTANTS.append(M("Z-fantome-de-banc",
                         "DECLARE et jamais joue — le levier du banc B9",
                         None))
    if a.liste:
        for m in MUTANTS:
            print("%-28s %s" % (m.nom, m.quoi))
            print("%-28s   cible : %s" % ("", m.cible or "⇒ doit rester VERT"))
        print("%-28s %s" % (MUTANT_TRACKER,
                            "le faux rouge ARME : la story bloquante passe `done`"))
        for nom, motif, _t in EXEMPTIONS:
            print("%-28s EXEMPTE : %s" % (nom[:28], motif.split(".")[0]))
        return 0

    print("=" * 78)
    print("dn4-40 / AC40.7 — CAMPAGNE DE MUTANTS SUR verif_ledger_dn416.py")
    print("=" * 78)
    # ── 0. LE TERRAIN — ⛔ jamais un skip silencieux ─────────────────────────
    manquants = []
    if not os.path.isdir(a.cockpit):
        manquants.append("le depot cockpit : %s" % a.cockpit)
    else:
        # 🔴 REVUE DE CODE dn4-44 — LE MANIFESTE MANQUAIT A CETTE LISTE, ET
        #    SON ABSENCE RENDAIT AC5.6 **VACUOUS** : sans lui la regeneration
        #    n'est jamais lancee, `rg` vaut `None` pour TOUS les mutants, et le
        #    `None` du tuple attendu faisait passer le controle de chacun.
        #    Le T0 rattrapait — en rendant `rc=1`, c'est-a-dire un ROUGE, la ou
        #    le defaut est un TERRAIN incomplet (rc=4). ⛔ Un prerequis absent
        #    n'est pas un verdict sur le code.
        for rel in (REL_LEDGER, REL_TRACKER, REL_MANIFESTE):
            if not os.path.isfile(os.path.join(a.cockpit, rel)):
                manquants.append(rel)
    if manquants:
        print("  [PREREQUIS ABSENT] le cockpit de planification n'est pas la")
        for m in manquants:
            print("      manque : %s" % m)
        print("      MOTIF : cette campagne MUTE le ledger et le tracker dans")
        print("              une COPIE. Sans eux elle n'a rien a muter — ⛔ et")
        print("              elle ne peut pas non plus compter les controles")
        print("              gardes par rien, puisque aucune gate ne tourne.")
        print("      REMEDE : `--cockpit <chemin>` si le depot est ailleurs.")
        print("      ⛔ CE N'EST PAS UN VERDICT SUR LE CODE, et ⛔ pas un skip :")
        print("         rc=%d, declare dans la table NON_JOUABLES de"
              " tools/run_gates.sh." % RC_PREREQUIS)
        print("BILAN : 0 OK, 0 KO")
        return RC_PREREQUIS
    print("⛔ AUCUNE ecriture dans le cockpit vivant : chaque mutant joue")
    print("   dans une COPIE jetable. Indexation : (site, libelle), ⛔ pas console.")
    # 🔴 dn5-7 / REVUE — LA CLE QUE `M1` REPLANTE DOIT ETRE **ENCORE MORTE**.
    ok_morte, dit_morte = cle_morte_est_morte(a.cockpit)
    print("   temoin de la cle morte de `M1`/`M3`/`M4` : %s" % dit_morte)
    if not ok_morte:
        print("   ⛔ ECHEC FERME : le mutant testerait une AUTRE branche que"
              " celle qu'il annonce, en silence.")
        print("BILAN CAMPAGNE : 0 mutant(s) JOUE(S), 1 echec(s), 0 controle(s)"
              " gardes par rien")
        print("⛔ ECHECS : cle-morte-plus-morte")
        print("BILAN : 0 OK, 1 KO")
        return 1

    par_lib = dn_sites.par_libelle(GATE)
    tmp = tempfile.mkdtemp(prefix="dn440-")
    try:
        led0 = io.open(os.path.join(a.cockpit, REL_LEDGER), encoding="utf-8").read()
        ancre = ancre_desknode(led0)
        if ancre is None:
            print("⛔ ancre introuvable dans le ledger — campagne ININTERPRETABLE")
            return 1

        print("\n── T0 : L'ARBRE PROPRE ───────────────────────────────────────")
        rc0, tr0, _ch, rg0, _g = joue(a.cockpit, None, tmp)
        ko0 = {k for k, v in tr0.items() if v[0] == "KO"}
        print("   rc=%d · %d controle(s) traces · %d KO · regeneration rc=%s"
              % (rc0, len(tr0), len(ko0), rg0))
        # 🔴 REVUE 2026-09-03 — LE `rc` ETAIT IMPRIME ET JAMAIS TESTE, ET UNE
        #    TRACE VIDE PASSAIT. Une gate qui meurt avant son premier controle
        #    laissait la campagne se derouler ENTIEREMENT et rendre
        #    « 0 echec(s), 0 controle(s) gardes par rien » — la sortie la plus
        #    rassurante possible AU-DESSUS D'UNE MESURE MORTE.
        # 🔴 dn4-44 / AC5.6 — LE `rc` DE LA REGENERATION ENTRE DANS LE T0.
        if rc0 != 0 or not tr0 or ko0 or rg0 not in (0, None):
            motif = ("rc=%d ⛔ non nul" % rc0) if rc0 != 0 else (
                "⛔ AUCUN controle trace — la gate n'a pas tourne" if not tr0
                else ("l'arbre propre n'est pas vert (%d KO)" % len(ko0))
                if ko0 else
                "la regeneration du manifeste a echoue (rc=%s)" % rg0)
            print("   ⛔ %s — campagne ININTERPRETABLE" % motif)
            return 1

        echecs = []
        n_bancs = 0
        # ── LES BANCS — les gardes de la campagne elle-meme (AC1.3) ─────────
        if not a.sans_bancs:
            print("\n── LES BANCS : CE QUI GARDE LA CAMPAGNE ELLE-MEME ────────────")
            print("   ⛔ chacun REPLANTE la faute d'origine. Un banc qui")
            print("      debrancherait la garde ne prouverait que son existence.")
            for nom, ok, dit in bancs(a.cockpit, tmp, os.path.abspath(__file__)):
                n_bancs += 1
                if not ok:
                    echecs.append(nom)
                print("   [%s] %-28s %s" % ("OK" if ok else "!!", nom, dit))
            if a.bancs_seuls:
                print("\n" + "=" * 78)
                print("BILAN BANCS : %d echec(s)" % len(echecs))
                print("=" * 78)
                return 1 if echecs else 0

        print("\n── LES MUTANTS ───────────────────────────────────────────────")
        vus = {}
        tirs = []
        for m in MUTANTS:
            if m.muteur is None:
                # DECLARE, ⛔ pas joue : il ⛔ n'entre PAS dans `tirs`, et le
                # balayage d'AC2.6 le rattrape juste apres. C'est le SEUL
                # chemin par lequel « annonce » et « joue » peuvent diverger.
                continue
            # 🔴 REVUE DE CODE dn4-44 — UNE EXCEPTION DANS UN MUTEUR TUAIT LA
            #    CAMPAGNE **SANS AUCUNE LIGNE `BILAN`**, et les mutants deja
            #    joues disparaissaient du rapport. MESURE : recherche de
            #    collision bornee trop bas ⇒ traceback nu, rc=1, 20 tirs
            #    perdus. La regle du depot est pourtant ecrite partout
            #    ailleurs : « un mutant qui ne s'applique pas ne prouve RIEN »
            #    — c'est un REFUS DECLARE, ⛔ pas un plantage.
            try:
                rc, tr, ch, rg, gate_j = joue(a.cockpit, m, tmp)
            except Exception as e:
                tirs.append(m.nom)
                echecs.append(m.nom)
                print("   [!!] %-28s ⛔ MUTANT INAPPLICABLE — %s : %s"
                      % (m.nom, type(e).__name__, str(e)[:90]))
                print("        %s" % m.quoi)
                continue
            tirs.append(m.nom)
            # ── AC5.2 : CE QUI A CHANGE, ⛔ PAS « QUELQUE CHOSE » ────────────
            if set(ch) != set(m.change):
                echecs.append(m.nom)
                print("   [!!] %-28s ⛔ MUTATION HORS CIBLE — declare %s,"
                      " a change %s" % (m.nom, list(m.change) or "rien",
                                        sorted(ch) or "rien"))
                print("        %s" % m.quoi)
                continue
            # ── AC5.6 : la regeneration du manifeste a-t-elle tenu ? ────────
            if m.regen is not None and rg not in (m.regen, None):
                echecs.append(m.nom)
                print("   [!!] %-28s ⛔ REGENERATION rc=%s (attendu %s) — le"
                      " manifeste mesure est PERIME" % (m.nom, rg, m.regen))
                print("        %s" % m.quoi)
                continue
            # ── AC5.2 (suite) : LE **DETAIL**, ⛔ PLUS SEULEMENT L'ARTEFACT ──
            #    🔴 REVUE DE CODE dn4-44 — LE DETAIL ETAIT CALCULE A CHAQUE TIR
            #       PUIS **JETE** : les seuls usages de `change` etaient
            #       `not ch` et `set(ch)`. La garde restait donc au grain du
            #       NOM D'ARTEFACT (« le ledger a change »), ⛔ pas « la BONNE
            #       chose a change » — ce que le docstring promettait pourtant.
            #       Un muteur qui inserait son temoin AU MAUVAIS ENDROIT
            #       passait. ⇒ le motif declare doit se LIRE dans les lignes.
            if m.motif and not any(m.motif in l
                                   for lignes in ch.values() for l in lignes):
                echecs.append(m.nom)
                print("   [!!] %-28s ⛔ MUTATION SANS SON MOTIF — `%s` n'est"
                      " dans AUCUNE ligne ajoutee : l'artefact a bouge, ⛔ pas"
                      " la bonne chose" % (m.nom, m.motif))
                print("        %s" % m.quoi)
                continue
            kos = {k for k, v in tr.items() if v[0] == "KO"}
            neufs = kos - ko0
            # ── AC2.4 : LE VERDICT EST STRICT ───────────────────────────────
            attendus = cles_du_libelle(m.cible, par_lib, gate_j) if m.cible else set()
            couples = set()
            for lib in m.aussi:
                couples |= cles_du_libelle(lib, par_lib, gate_j)
            manque_au_source = ([m.cible] if m.cible and not attendus else []) \
                + [l for l in m.aussi if not cles_du_libelle(l, par_lib, gate_j)]
            surplus = neufs - attendus - couples
            touche = attendus & neufs
            if manque_au_source:
                bon = False
                verdict = "⛔ CIBLE INTROUVABLE AU SOURCE : %s" \
                    % " · ".join(x[:40] for x in manque_au_source)
            elif m.cible is None:
                bon = not neufs
                verdict = "VERT (attendu)" if bon else \
                    "⛔ ROUGE INATTENDU : %s" % ", ".join(sorted(_fmt(k) for k in neufs))
            elif not touche:
                bon = False
                verdict = "⛔ NON VU (KO neufs : %s)" \
                    % (", ".join(sorted(_fmt(k) for k in neufs)) or "aucun")
            elif surplus:
                bon = False
                verdict = "⛔ ROUGE NON DECLARE ailleurs : %s" \
                    % ", ".join(sorted(_fmt(k) for k in surplus))
            else:
                bon = True
                verdict = "VU ROUGE sur %s%s" % (
                    ", ".join(sorted(dn_trace.parts(k)[0] for k in touche)),
                    (" (+ %d couple(s) declare(s))" % len(neufs & couples))
                    if (neufs & couples) else "")
            # 🔴 REVUE DE CODE dn4-44 — `vus` ETAIT ALIMENTE **AVANT** CE
            #    VERDICT, PAR TOUS LES KO NEUFS. Un rouge que la campagne
            #    DECLARE fautif (`⛔ ROUGE NON DECLARE ailleurs`) comptait donc
            #    quand meme comme COUVERTURE : le compte « gardes par rien »
            #    etait gonfle **dans le sens rassurant**, par exactement la
            #    classe de rouge que la campagne rejette. 🎯 C'est le compte
            #    qui REFUTE ou CONFIRME AC40.7.a — le seul qu'il ne fallait pas
            #    laisser mentir. ⇒ seul un mutant JUSTE couvre, et seulement
            #    sur ce qu'il a DECLARE (sa cible et ses couples).
            if bon:
                for k in (touche | (neufs & couples)):
                    vus.setdefault(k, []).append(m.nom)
            else:
                echecs.append(m.nom)
            print("   [%s] %-28s %s" % ("OK" if bon else "!!", m.nom, verdict))
            print("        %s" % m.quoi)

        # ── LE MUTANT DE TRACKER : le faux rouge ARME (AC40.1.d) ────────────
        cible_arme = _story_bloquante(led0)
        if cible_arme:
            # 🔴 REVUE 2026-09-03 — CE MUTANT NE MUTAIT RIEN, ET C'ETAIT LA
            #    PREUVE MAITRESSE D'AC40.1.d. `_story_bloquante()` rend une cle
            #    COURTE (`dnN-M`) ; le tracker porte la cle LONGUE
            #    (`dnN-M-un-titre-en-slug`). Le motif `^(  <court>:)` ne pouvait
            #    donc JAMAIS mordre : le tracker ressortait identique a l'octet
            #    et la campagne imprimait « VERT (attendu) » quoi que fasse la
            #    gate. ⇒ on matche la cle COMPLETE par son prefixe BORNE, et le
            #    banc `B1c` garde la borne.
            trk0 = io.open(os.path.join(a.cockpit, REL_TRACKER),
                           encoding="utf-8").read()
            cle_mutee = _mute_trk_cle(trk0, cible_arme)
            mt = M(MUTANT_TRACKER, "la story bloquante passe `done`",
                   mute_tracker(cible_arme), change=("tracker",))
            rc, tr, ch, rg, _g = joue(a.cockpit, mt, tmp)
            tirs.append(MUTANT_TRACKER)
            neufs = {k for k, v in tr.items() if v[0] == "KO"} - ko0
            juste = (cle_mutee is not None
                     and (cle_mutee == cible_arme
                          or cle_mutee.startswith(cible_arme + "-")))
            # 🔴 REVUE DE CODE dn4-44 — LE `rc` DE LA REGENERATION ETAIT LIE
            #    PUIS **IGNORE** ICI, alors que la boucle des MUTANTS le teste
            #    depuis AC5.6. Or ce mutant-ci est la « preuve maitresse »
            #    d'AC40.1.d : une regeneration en echec y laissait la campagne
            #    mesurer un manifeste PERIME en imprimant « VERT (attendu) ».
            regen_ok = rg in (0, None)
            bon = set(ch) == {"tracker"} and juste and regen_ok and not neufs
            if not bon:
                echecs.append(MUTANT_TRACKER)
            if not regen_ok:
                dit = ("⛔ REGENERATION rc=%s — le manifeste mesure est PERIME"
                       % rg)
            elif set(ch) != {"tracker"}:
                dit = "⛔ MUTATION HORS CIBLE — a change %s" % (sorted(ch) or "rien")
            elif not juste:
                dit = "⛔ MUTATION MAL CIBLEE — a mute `%s`, pas une cle `%s-…`" \
                    % (cle_mutee, cible_arme)
            elif neufs:
                dit = "⛔ ROUGE : %s" % ", ".join(sorted(_fmt(k) for k in neufs))
            else:
                dit = "VERT (attendu) — cle mutee : `%s`" % cle_mutee
            print("   [%s] %-28s %s" % ("OK" if bon else "!!", MUTANT_TRACKER, dit))
            print("        `%s` passee `done` DANS LA COPIE ⇒ la gate doit"
                  " rester verte" % cible_arme)
        else:
            echecs.append(MUTANT_TRACKER)
            print("   [!!] %-28s ⛔ aucune prose ne cite de story comme fait"
                  " bloquant — le mutant N'A PAS ETE JOUE" % MUTANT_TRACKER)

        # ── AC2.6 / AC5.4 : LE BALAYAGE DES MUTANTS DECLARES ────────────────
        declares = [m.nom for m in MUTANTS] + [MUTANT_TRACKER]
        jamais = [n for n in declares if n not in tirs]
        if jamais:
            echecs.append("balayage")
            print("\n   ⛔ %d MUTANT(S) DECLARE(S) ET JAMAIS JOUE(S) : %s"
                  % (len(jamais), ", ".join(jamais)))
            print("      ⛔ Un mutant declare et jamais applique reste VERT, et")
            print("         le bilan s'imprime quand meme. Mesure de `dn4-42`.")

        # ── LA SECONDE FACE : LES CONTROLES GARDES PAR RIEN ─────────────────
        print("\n── `controle ⇒ couvert` : LES CONTROLES GARDES PAR RIEN ───────")
        print("   ⛔ « N mutants, N vus rougir » prouve `mutant ⇒ rouge`.")
        print("      Ce compte-ci est l'AUTRE sens, et c'est celui qui manque.")
        tous = sorted(tr0)
        nus = [k for k in tous if k not in vus]
        # ── AC4.3 : LES EXEMPTIONS, DECLAREES ET FALSIFIABLES ───────────────
        exempts = {}
        for lib, motif, temoin in EXEMPTIONS:
            ok, dit = temoin(lib)
            # 🔴 REVUE DE CODE dn4-44 — UNE EXEMPTION DONT LE **CONTROLE**
            #    DISPARAIT NE DEMENTAIT RIEN. Son temoin relit le tableau du
            #    tri, ⛔ jamais la gate : supprimer le `ctrl()` exempte rendait
            #    `rc=0`, « exemptes : 4 » au lieu de 5, et pas un mot. Une
            #    exemption qui ne designe plus aucun site est une ligne morte
            #    — et une ligne morte dans une table d'exemptions, c'est
            #    exactement la « liste d'exclusion muette » qu'AC4.3 interdit.
            cles = cles_du_libelle(lib, par_lib)
            if not cles:
                ok, dit = False, ("⛔ AUCUN site `%s` dans la gate — l'exemption"
                                  " ne designe plus rien" % lib[:40])
            if not ok:
                echecs.append("exemption:%s" % lib[:30])
                print("   [!!] EXEMPTION TOMBEE : %s" % dit)
            for k in cles:
                exempts[k] = (motif, ok, dit)
        nus_exemptes = [k for k in nus if k in exempts]
        nus_reels = [k for k in nus if k not in exempts]
        print("   controles traces          : %d" % len(tous))
        print("   controles vus rougir      : %d" % len(vus))
        print("   exemptes (declares)       : %d" % len(nus_exemptes))
        for k in sorted(nus_exemptes):
            motif, ok, dit = exempts[k]
            print("        [%s] %s" % ("temoin OK" if ok else "⛔ TEMOIN TOMBE",
                                       _fmt(k)))
            print("              motif  : %s" % motif)
            print("              temoin : %s" % dit)
        print("   ⚠️ GARDES PAR RIEN        : %d" % len(nus_reels))
        for k in sorted(nus_reels):
            print("        %s" % _fmt(k))
        # 🔴 dn4-44 / AC4.1 — LE COMPTE **GARDE**. Il rendait `rc=0` en publiant
        #    15 controles nus : c'est tres exactement pourquoi AC40.7.a a pu
        #    etre refutee sans que rien ne rougisse. Une regle que rien
        #    n'applique est une regle qui pourrira.
        if nus_reels:
            echecs.append("gardes-par-rien")
            print("   ⛔ UN CONTROLE QUE RIEN NE GARDE EST UN ECHEC. ⇒ lui donner")
            print("      son mutant, ou l'EXEMPTER avec son motif et son temoin")
            print("      (table `EXEMPTIONS`). ⛔ Ni liste muette, ni seuil.")

        # ── AC4.4 : CE QUE « NEUF » VEUT DIRE, ECRIT DANS L'OUTIL ───────────
        print("\n── LA REGLE QUE CETTE CAMPAGNE APPLIQUE (AC4.4) ───────────────")
        print("   « AUCUN CONTROLE **NEUF** NE SORT SANS SON MUTANT. »")
        print("   NEUF = un site `ctrl()` **pose ou reecrit** par la marche")
        print("          courante, etabli au `git blame` sur la gate — ⛔ pas")
        print("          « ajoute au fichier » : reecrire la CONDITION d'un")
        print("          controle existant le rend neuf, deplacer sa ligne non.")
        print("   ⇒ Ce que cette campagne applique est PLUS FORT : tout controle")
        print("     TRACE doit etre couvert ou EXEMPTE, neuf ou pas.")

        print("\n" + "=" * 78)
        print("BILAN CAMPAGNE : %d mutant(s) JOUE(S), %d echec(s), %d controle(s)"
              " gardes par rien" % (len(tirs), len(echecs), len(nus_reels)))
        # 🔴 REVUE DE CODE dn4-44 — LES ECHECS SONT **NOMMES**. Sans cette
        #    ligne, un banc ne peut viser que le `rc`, et le `rc` est vrai des
        #    qu'UN echec quelconque survient : le banc `B6` est reste VERT
        #    parce qu'un AUTRE echec fournissait le meme `rc=1` — le motif
        #    « un mutant qui passe POUR LA MAUVAISE RAISON », paye ici meme.
        if echecs:
            print("⛔ ECHECS : %s" % ", ".join(sorted(set(echecs))))
        # ⚠️ dn4-44 — LA LIGNE DE BILAN **DU CONTRAT DE GATE**, en plus de celle
        #    de la campagne. Elle est lue par qui balaie les gates ; celle
        #    au-dessus est lue par qui conduit la campagne. ⛔ Les deux, ⛔ pas
        #    l'une a la place de l'autre : ecraser le bilan de campagne ferait
        #    perdre le compte qui REFUTE ou CONFIRME AC40.7.a.
        # 🔴 REVUE DE CODE dn4-44 — CETTE LIGNE FAISAIT `len(tirs) - len(echecs)`
        #    ALORS QUE `echecs` AGREGE DES BANCS, DES EXEMPTIONS, LE BALAYAGE
        #    ET LE COMPTE DES NUS — dont aucun n'est un tir. MESURE : `31 OK`
        #    annonces sur 32 tirs dont ZERO n'avait echoue ; et en cumulant,
        #    **`BILAN : -2 OK, 35 KO`**. C'est la ligne du CONTRAT DE GATE,
        #    celle que lit qui balaie les gates. ⇒ elle compte TOUS les
        #    controles que la campagne rend, ⛔ pas les seuls mutants.
        controles = len(tirs) + n_bancs + len(EXEMPTIONS) + 2
        print("BILAN : %d OK, %d KO"
              % (max(0, controles - len(echecs)), len(echecs)))
        print("=" * 78)
        return 1 if echecs else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _story_bloquante(led):
    """La story citee dans la PROSE d'un `bloquee par :` — le faux rouge ARME.

    ⛔ Ce n'est PAS un porteur : c'est un FAIT. Avant dn4-40, `findall` la
    ramassait quand meme ⇒ l'entree rougissait le jour ou elle passait `done`.

    ⚠️ REVUE 2026-09-03 — ELLE REND UNE CLE **COURTE** (`dnN-M`), et le tracker
    porte la cle **LONGUE**. Tout appelant qui la compare a une cle de tracker
    doit donc matcher PAR PREFIXE **BORNE** — voir `_mute_trk_cle` et le banc
    `B1c`. C'est ecrit ici parce que l'ignorer a rendu le mutant d'AC40.1.d
    entierement INOPERANT sans qu'aucune sortie ne le dise.
    """
    for m in re.finditer(r"porteur\s*:\s*(bloqu\w*\s+par\s*:[^·]*)·", led):
        c = re.search(r"\b(dn\d+-\d+)\b", m.group(1), re.I)
        if c:
            return c.group(1).lower()
    return None


if __name__ == "__main__":
    sys.exit(main())

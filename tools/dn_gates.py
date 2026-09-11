# -*- coding: utf-8 -*-
"""dn8-1 / AC8.1.3 — LES HELPERS PARTAGES DES GATES VIVENT **ICI**, EN UN SEUL
ENDROIT.

🔬 LA MESURE QUI JUSTIFIE CE FICHIER — AST, CORPS NORMALISE, 2026-09-11, sur
   les 44 gates `tools/verif_*.py` :

       helper                copies   implementations distinctes
       ctrl                      33        19
       lire                      26        11
       bilan                     14         8
       ids_par_ast               11         6
       sans_commentaires          9         8
       plat                       4         1
       style_de                   2         2
       bloc_regle                 2         2
       ─────────────────────────────────────────
       TOTAL                    101        57

⚠️ CE CHIFFRE DIVERGE DU CADRAGE, ET LES DEUX SONT ECRITS (NFR3 : annoter,
   ⛔ pas effacer). Le cadrage de `epic-dn8` annoncait **51 copies** et
   `sans_commentaires` en **5** implementations. La mesure a l'AST du
   2026-09-11 rend **101** et **8**. ⛔ Aucun des deux n'est efface : le
   cadrage a ete ecrit sur un comptage textuel, celui-ci sur l'arbre syntaxique
   — et c'est precisement la difference que `dn8` existe pour installer.

── CE QUE CE MODULE EST, ET CE QU'IL N'EST PAS ──────────────────────────────

✅ IL EST **LE PATRON `dn_trace.py`**, ⛔ PAS UN PAQUET. Import frere depuis
   `tools/` — `import dn_gates` — parce que Python met le repertoire du script
   en tete de `sys.path`. **17 fichiers** utilisent deja ce patron avec
   `dn_trace` / `dn_police` / `dn_sites` : il est PROUVE dans cet arbre.

⛔ IL NE REFOND PAS LES 44 GATES EXISTANTES. La frontiere de `epic-dn8` est
   explicite — *« `dn8` installe le garde-fou pour ce qu'elle ECRIT »* — et
   l'hygiene des 44 gates est le territoire `dn4`. Les 101 copies restent en
   place ; elles sont **INVENTORIEES ET DECLAREES** par
   `tools/verif_harnais_dn81.py`, ⛔ jamais reecrites en silence.
   🔴 POURQUOI CE N'EST PAS DE LA TIMIDITE, ET C'EST MESURE : `ctrl` existe en
      **19 implementations distinctes** pour 33 copies. ⛔ Presumer qu'un seul
      corps les remplace toutes, c'est refondre 44 gates par la porte de
      derriere — et une gate refondue au jugé est une gate dont plus personne
      n'a vu le rouge.

── LE CORPS RETENU EST **LE PLUS JOUE**, ET SA POPULATION EST ECRITE ────────

Chaque helper ci-dessous porte, dans son docstring, **le corps modal** (celui
que le plus grand nombre de gates portent a l'identique) et la LISTE des gates
qui le portent. ⛔ Aucun corps n'a ete « ameliore » au passage : un corps
different de celui qui a ete mesure ne serait plus l'implementation la plus
jouee, et l'empreinte que `verif_harnais_dn81.py` compare ne voudrait plus
rien dire.

⚠️ **LES SEULES DIVERGENCES SONT LES DEPENDANCES DE CONTEXTE, ET ELLES SONT
   TOUTES ECRITES.** Quatre corps modaux lisent une variable de LEUR module
   d'origine (`__file__`, `CONTROLES_PREVUS`, `RE_STYLE`, `RE_ID_CTRL`). Portes
   tels quels ici, ils liraient le contexte de CE fichier — c'est-a-dire le
   mauvais. ⇒ ces lectures deviennent des **PARAMETRES**, et chaque
   transformation est nommee dans le docstring du helper concerne. ⛔ Rien
   d'autre n'a bouge.

── CE QUE LES CORPS MODAUX **NE FONT PAS**, ET QUI EST DECLARE ──────────────

⛔ `ctrl` MODAL N'APPELLE PAS `dn_trace`. 12 gates sur 44 enveloppent leur
   `ctrl` d'un `dn_trace.trace(ok, libelle)` ; les 5 porteuses du corps modal,
   non. ⇒ le corps modal est repris SANS la trace, et une gate qui a besoin
   d'entrer dans la campagne `dn4-40` continue d'ecrire son propre `ctrl`.
   ⚠️ C'est un ECART DECLARE, ⛔ pas un oubli.

⛔ `ctrl` MODAL N'A QU'UN SEUL `detail`. La variante a `detail_ok` /
   `detail_ko` (celle de `verif_ledger_dn416.py`) existe parce qu'un `[KO ]`
   imprimait la justification du SUCCES. Elle est MEILLEURE, et elle n'est
   ⛔ PAS majoritaire. ⇒ le module retient la modale et le dit.

Codes de sortie : ce fichier n'est pas un executable. Il ne s'appelle pas.
"""
import ast
import hashlib
import io
import os
import re

__all__ = [
    "sans_commentaires",
    "style_de",
    "bloc_regle",
    "lire",
    "ctrl",
    "bilan",
    "plat",
    "ids_par_ast",
]

# ⚠️ LES HUIT NOMS QUE CE MODULE POSSEDE. `verif_harnais_dn81.py` lit CETTE
#    liste, ⛔ il ne la recopie pas : une liste recopiee diverge le jour ou on
#    ajoute un helper, c'est-a-dire le jour ou elle compte.
NOMS_PARTAGES = tuple(__all__)

# ── L'ETAT DE COMPTAGE, PARTAGE PAR `ctrl` ET `bilan` ───────────────────────
# ⚠️ DES LISTES, ⛔ pas des entiers : c'est la forme QUE LES 44 GATES PORTENT
#    (`ok_total = [0]`), et la seule qui laisse `ctrl` incrementer sans
#    `global`. Une gate qui importe ce module lit ses comptes ici.
ok_total = [0]
ko_total = [0]

# Le motif d'identifiant de controle, `(c12)` en tete de libelle. Corps modal
# de `RE_ID_CTRL`, identique dans les 6 gates qui portent `ids_par_ast` modal.
RE_ID_CTRL = re.compile(r"\((\w+)\)")

# Corps modal de `RE_STYLE` (`verif_placement_dn74.py`).
RE_STYLE = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)


def sans_commentaires(js):
    """Le script SANS ses commentaires — ⛔ ce qui s'execute, pas ce qui
    l'explique. Une gate qui compte la prose des commentaires rougirait sur la
    documentation de sa propre regle.

    ── PROVENANCE ──────────────────────────────────────────────────────────
    Corps modal : **2 copies sur 9**, en **8** implementations distinctes.
    Porteuses : `verif_langue_dalle_dn73.py`, `verif_page_dn722.py`.
    ⚠️ C'est le helper le plus DISPERSE du lot (8 corps pour 9 copies) : le
       corps retenu est majoritaire par UNE voix. ⛔ Ne pas le lire comme un
       consensus — le lire comme une mesure.
    ⛔ Aucune transformation : le corps est repris tel quel.
    """
    js = re.sub(r"/\*.*?\*/", " ", js or "", flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", " ", js)


def style_de(page, rx=None):
    """Les feuilles de style de la page, **SANS LEURS COMMENTAIRES**.

    🔴 MESURE DU 2026-09-10 — SANS CE RETRAIT, UN LEURRE DANS UN `/* … */`
       SUFFIT A REVERDIR LA GATE. Demontre : la regle REELLE remise aux
       declarations EXACTES du survol, et un commentaire portant l'aplat pose
       juste avant ⇒ `bloc_regle` appariait le COMMENTAIRE, `(c10)` et `(c11)`
       sortaient VERTS sur une page ou « selectionne » et « survole » etaient
       redevenus indiscernables. C'est le meme piege que `sans_commentaires`
       ferme cote script — une gate qui lit de la prose prouve un `grep`,
       ⛔ pas une propriete. Le mutant 20 le REPLANTE.

    ── PROVENANCE ──────────────────────────────────────────────────────────
    Corps modal : **1 copie sur 2**, **2** implementations distinctes.
    Porteuse : `verif_placement_dn74.py`.
    ⚠️ TRANSFORMATION DECLAREE : le corps modal lit `RE_STYLE` DANS SON MODULE.
       Porte ici tel quel, il lirait le `RE_STYLE` de CE fichier — donc le
       mauvais le jour ou une gate en definit un autre. ⇒ `rx` est un
       PARAMETRE, dont le defaut est le `RE_STYLE` modal. ⛔ Rien d'autre n'a
       bouge.
    """
    brut = "\n".join((rx or RE_STYLE).findall(page or ""))
    return re.sub(r"/\*.*?\*/", " ", brut, flags=re.S)


def bloc_regle(style, selecteur):
    """Le CORPS d'une regle CSS, ⛔ pas le voisinage.

    ⚠️ LE SELECTEUR EST SUIVI D'UNE ACCOLADE, ⛔ pas de n'importe quoi : sans
       cette borne, `…[aria-pressed="true"]` mordrait sur
       `…[aria-pressed="true"]:disabled` et les deux regles se confondraient.
    🔴 Une regle qui ne se referme pas rend **VIDE**.

    ── PROVENANCE ──────────────────────────────────────────────────────────
    Corps modal : **1 copie sur 2**, **2** implementations distinctes.
    Porteuse : `verif_placement_dn74.py`.
    ⛔ Aucune transformation.
    🔴 ⚠️ ET C'EST UNE LECTURE **AU MOTIF**, ⛔ PAS UN PARSEUR CSS : ce depot
       n'en a AUCUN (mesure : 44 gates, 0 parseur CSS). La regle `NFR14` de
       `dn8` exige alors que l'aveuglement soit DECLARE EN PROPRE — c'est ce
       que fait cette ligne-ci, et c'est ce que `verif_harnais_dn81.py` (c3)
       verifie chez tout controle ECRIT PAR `dn8`.
    """
    m = re.search(re.escape(selecteur) + r"\s*\{([^}]*)\}", style or "")
    return m.group(1) if m else ""


def lire(chemin):
    """Le texte d'un fichier **et son empreinte** — ⛔ jamais l'un sans l'autre.

    ── PROVENANCE ──────────────────────────────────────────────────────────
    Corps modal : **7 copies sur 26**, en **11** implementations distinctes.
    Porteuses : `verif_courbe_dn413.py`, `verif_cumul_ambient_dn45.py`,
    `verif_harnais_dn413.py`, `verif_hist_dn413.py`, `verif_rebouclage_dn45.py`,
    `verif_selection_dn49.py`, `verif_verrou_lvgl_dn413.py`.
    ⛔ Aucune transformation.
    ⚠️ LE CORPS MODAL LEVE sur un fichier absent ou non-UTF-8, et c'est VOULU
       chez ses 7 porteuses : l'appelant en fait un CONTROLE nomme. Les corps
       minoritaires qui rendent `None` en silence ⛔ ne sont PAS retenus — un
       repli muet est exactement ce que ce depot paie depuis trois marches.
    """
    with open(chemin, "rb") as f:
        brut = f.read()
    return brut.decode("utf-8"), hashlib.sha256(brut).hexdigest()[:16]


def ctrl(ok, libelle, detail=""):
    """Un controle : imprime, compte, rend son verdict. ⛔ Jamais un skip.

    ── PROVENANCE ──────────────────────────────────────────────────────────
    Corps modal : **5 copies sur 33**, en **19** implementations distinctes.
    Porteuses : `verif_bme680_retard_dn45.py`, `verif_courbe_dn413.py`,
    `verif_cumul_ambient_dn45.py`, `verif_d4_nvs_dn45.py`,
    `verif_rebouclage_dn45.py`.
    ⛔ Aucune transformation.
    🔴 **19 CORPS POUR 33 COPIES** : ce corps-ci n'est majoritaire qu'a 5/33.
       ⛔ Il ne pretend PAS remplacer les 18 autres, et c'est ecrit en tete de
       module. Les deux variantes les plus utiles qu'il ne porte PAS —
       `dn_trace` et le couple `detail_ok`/`detail_ko` — sont nommees en tete.
    """
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-56s %s" % (libelle, detail))
    else:
        ko_total[0] += 1
        print("  [KO ] %-56s %s" % (libelle, detail))
    return ok


def bilan(rc, anticipee="", prevus=None):
    """TOUT CHEMIN QUI REND UN VERDICT passe ici. Une gate qui sort sans
    `BILAN` est indiscernable d'une gate MORTE — et c'est precisement le
    discriminant que la campagne exige de chaque mutant.

    ⚠️ DEUX SORTIES NE PASSENT PAS ICI, ET C'EST ECRIT PLUTOT QUE PROMIS :
       · `--liste-mutants`, qui n'emet AUCUN controle et ne rend AUCUN verdict ;
       · le mutant INCONNU, qui est une ERREUR D'APPEL et rend 2.

    ── PROVENANCE ──────────────────────────────────────────────────────────
    Corps modal : **6 copies sur 14**, en **8** implementations distinctes.
    Porteuses : `verif_flash_dn72.py`, `verif_langue_dalle_dn73.py`,
    `verif_page_dn722.py`, `verif_placement_dn74.py`,
    `verif_preconditions_dn76.py`, `verif_prerequis_dn75.py`.
    ⚠️ TRANSFORMATION DECLAREE : le corps modal lit `CONTROLES_PREVUS` DANS SON
       MODULE. Porte ici tel quel, il lirait une constante de CE fichier, qui
       n'a aucun sens pour l'appelant. ⇒ `prevus` est un PARAMETRE.
       ⛔ `None` DESARME le controle `(z)` — et c'est une capacite qu'il faut
       voir : une gate qui ne declare pas son compte prevu n'a pas de `(z)`,
       ⛔ elle n'a pas un `(z)` qui passe. ⚠️ Cette distinction est exactement
       le genre de trou que ce depot a deja paye ; elle est ecrite ici pour
       qu'un futur appelant la voie avant de l'utiliser.
    """
    emis = ok_total[0] + ko_total[0]
    if not anticipee and prevus is not None and emis != prevus:
        ctrl(False, "(z) tout controle prevu est EMIS",
             "⛔ %d emis pour %d prevus — une gate qui joue MOINS de controles "
             "qu'annonce sort VERTE sur une population RETRECIE, ⛔ sans le "
             "declarer" % (emis, prevus))
        rc = 1
    print("\n" + "=" * 78)
    if anticipee:
        print("⛔ SORTIE ANTICIPEE — %d controle(s) emis sur %s prevus : %s"
              % (ok_total[0] + ko_total[0],
                 "?" if prevus is None else prevus, anticipee))
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return rc


def plat(txt):
    """Le texte SANS ses retours a la ligne — un motif ne doit ⛔ pas dependre
    de l'endroit ou la prose a ete coupee.

    ── PROVENANCE ──────────────────────────────────────────────────────────
    Corps modal : **4 copies sur 4**, **1** seule implementation.
    Porteuses : `verif_flash_dn72.py`, `verif_installeur_dn71.py`,
    `verif_langue_dalle_dn73.py`, `verif_page_dn722.py`.
    ✅ LE SEUL DES HUIT QUI NE DIVERGE PAS. ⛔ Ce n'est pas une raison de
       croire les sept autres : c'est la preuve que la divergence n'est pas
       fatale, et donc qu'elle a ete SUBIE.
    """
    return re.sub(r"\s+", " ", txt or "")


def _texte_litteral(n):
    """La partie LITTERALE d'un libelle, meme construit par formatage.

    ⚠️ PRIVE, ⛔ pas dans `__all__` : ce n'est pas un des 8 noms mesures. Il
    accompagne `ids_par_ast`, qui ne marche pas sans lui.
    """
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Mod, ast.Add)):
        return _texte_litteral(n.left)
    if isinstance(n, ast.JoinedStr) and n.values:
        return _texte_litteral(n.values[0])
    return None


def ids_par_ast(fichier, motif=None, appelee="ctrl"):
    """Les identifiants de TOUS les controles d'un fichier, lus A L'AST.

    🔴 POURQUOI PAS L'ENSEMBLE DES IDENTIFIANTS DEJA EMIS : cet ensemble est
       fige AU MOMENT DE L'APPEL de la reciproque. Tout controle ajoute APRES
       ce bloc en sortirait INVISIBLE.

    ── PROVENANCE ──────────────────────────────────────────────────────────
    Corps modal : **6 copies sur 11**, en **6** implementations distinctes.
    Porteuses : `verif_flash_dn72.py`, `verif_langue_dalle_dn73.py`,
    `verif_page_dn722.py`, `verif_placement_dn74.py`,
    `verif_preconditions_dn76.py`, `verif_prerequis_dn75.py`.
    🔴 TRANSFORMATION DECLAREE, ET C'EST **LA** RAISON POUR LAQUELLE CE HELPER
       NE POUVAIT PAS ETRE PARTAGE TEL QUEL : le corps modal lit
       `os.path.abspath(__file__)`. Dans un module partage, `__file__` est
       `dn_gates.py` — ⛔ le fichier de l'INSTRUMENT, jamais celui de la gate
       qui appelle. Un portage naif aurait rendu les identifiants de CE
       fichier (c'est-a-dire AUCUN) et **toute reciproque appelante serait
       passee VERTE sur une population VIDE**. C'est la faute exacte que
       `dn4-40` a payee. ⇒ `fichier` est un PARAMETRE OBLIGATOIRE.
    ⚠️ `motif` et `appelee` sont les deux autres lectures de contexte
       (`RE_ID_CTRL`, le nom `ctrl`), rendues explicites au meme titre.
    """
    try:
        with io.open(os.path.abspath(fichier), encoding="utf-8") as fh:
            arbre = ast.parse(fh.read())
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    out = set()
    for n in ast.walk(arbre):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == appelee and len(n.args) >= 2):
            m = (motif or RE_ID_CTRL).match(_texte_litteral(n.args[1]) or "")
            if m:
                out.add(m.group(1))
    return out or None

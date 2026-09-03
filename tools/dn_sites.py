# -*- coding: utf-8 -*-
"""dn4-44 / AC5.5 — LES SITES `ctrl()` D'UNE GATE, LUS **UNE SEULE FOIS**.

🔴 LE MOTIF, MESURE AU CADRAGE DE dn4-44 : LES DEUX CAMPAGNES DU DEPOT
RESOLVAIENT LEURS CIBLES **AUTREMENT**. `campagne_ctrl_dn440.py` TOKENISE le
source ; `verif_campagne_dn440.py` lisait AU REGEX :

    ctrl\\(\\s*(?:not\\s+)?[^,]+?,\\s*\\n?\\s*("[^"]*")

Ce motif est aveugle a quatre formes que ce depot ecrit deja :

  · **f-string** — Python 3.12 la tokenise en `FSTRING_START`, ⛔ pas `STRING` ;
  · **guillemets simples** — `'…'` n'est pas `"…"` ;
  · **concatenation implicite** — `"un " "libelle"` ne rendait que son 1er
    fragment ⇒ la cible ne matchait plus rien, et le mutant sortait « NON VU » ;
  · **une virgule dans le PREMIER argument** — `ctrl(all(a, b), "…")` : le
    `[^,]+?` coupe a la 1re virgule et lit `b)` comme libelle.

⚠️ LES DEUX COMPTES COINCIDAIENT LE 2026-09-03 (43 = 43). ⛔ CE N'EST PAS UNE
GARANTIE — c'est une coincidence qu'aucun controle ne tenait. Ce module la
remplace par une seule lecture, et le banc `B4` de `verif_campagne_dn440.py` la garde
en REPLANTANT chacune des quatre formes.

⚠️ CE MODULE NE LIT QUE DU SOURCE. Il ⛔ n'execute rien, ⛔ n'importe aucune
gate, et ⛔ ne depend d'aucun chemin absolu.
"""
import ast
import io
import os
import tokenize

# Les deux noms sous lesquels ce depot appelle un controle. `dire` est la
# forme de `verif_paliers_dn441.py`. ⛔ Toute gate qui en inventerait un
# troisieme devrait l'ajouter ICI, ⛔ pas dans un des appelants.
NOMS = ("ctrl", "dire")

_IGNORES = (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE,
            tokenize.INDENT, tokenize.DEDENT)

_OUVRANTS = ("(", "[", "{")
_FERMANTS = (")", "]", "}")


class SourceIllisible(Exception):
    """Un source que le tokenizer refuse — ⛔ un REFUS DECLARE, pas un plantage.

    🔴 REVUE DE CODE dn4-44 (2026-09-03) — `tokenize` LEVE sur un fichier a
    erreur de syntaxe, a parenthese non fermee, tronque, ou porteur d'un
    conflit de fusion non resolu. L'INVENTAIRE du tri balaie **toutes** les
    gates : **une seule** gate incassable tuait le balayage entier par
    traceback, sans `BILAN TRI`. ⇒ l'appelant attrape et le DIT gate par gate.
    ⛔ Un outil qui meurt parce qu'UN de ses sujets est casse ne mesure pas les
    autres — et c'est le sujet meme de cette story.
    """


def _toks(chemin):
    """Les jetons SIGNIFIANTS d'un source.

    ⚠️ Les commentaires sont retires : un `ctrl(True, …)` CITE dans un
    commentaire ⛔ n'est pas un site. Ce depot a deja paye ce motif.

    ⚠️ Leve `SourceIllisible` — ⛔ jamais une exception de la bibliotheque nue.
    """
    try:
        with open(chemin, "rb") as fh:
            return [t for t in tokenize.tokenize(fh.readline)
                    if t.type not in _IGNORES]
    except (tokenize.TokenError, SyntaxError, IndentationError,
            UnicodeDecodeError, ValueError) as e:
        raise SourceIllisible("%s : %s" % (os.path.basename(chemin), e))


def _valeur(arg):
    """La VALEUR d'une suite de jetons si c'est un litteral chaine.

    Rend `(valeur, "litteral")`, `(None, "illisible")` — le site EXISTE mais son
    libelle n'est pas un litteral (f-string, variable, appel) — ou
    `(None, "absent")` quand il n'y a pas de 2e argument du tout.
    """
    if not arg:
        return None, "absent"
    if any(t.type != tokenize.STRING for t in arg):
        return None, "illisible"
    try:
        val = ast.literal_eval(" ".join(t.string for t in arg))
    except Exception:
        return None, "illisible"
    if not isinstance(val, str):
        return None, "illisible"
    return val, "litteral"


def sites(chemin):
    """Tous les sites d'appel `ctrl()`/`dire()` d'un source.

    Rend une liste de `(ligne, premier_arg_est_True, libelle, forme)`.

    ⚠️ `premier_arg_est_True` distingue le `ctrl(True, …)` LITTERAL — celui
    qu'AC40.2 trie — de tous les autres. ⛔ Un `ctrl(ok, …)` n'en est pas un.
    ⛔ La DEFINITION `def ctrl(...)` n'est pas un appel : la compter gonflait
    le compte de +1 par gate, et avec lui les colonnes `sites` et `ecart`
    PUBLIEES par la campagne du tri.
    """
    toks = _toks(chemin)
    out = []
    for i, t in enumerate(toks[:-2]):
        if t.type != tokenize.NAME or t.string not in NOMS:
            continue
        if toks[i + 1].string != "(":
            continue
        if i and toks[i - 1].type == tokenize.NAME and toks[i - 1].string == "def":
            continue
        # ── decoupe des arguments AU NIVEAU 1 ────────────────────────────────
        args = [[]]
        prof = 1
        j = i + 2
        while j < len(toks) and prof:
            s = toks[j].string
            if toks[j].type == tokenize.OP and s in _OUVRANTS:
                prof += 1
            elif toks[j].type == tokenize.OP and s in _FERMANTS:
                prof -= 1
                if not prof:
                    break
            if prof == 1 and toks[j].type == tokenize.OP and s == ",":
                args.append([])
            else:
                args[-1].append(toks[j])
            j += 1
        a1 = args[0] if args else []
        a2 = args[1] if len(args) > 1 else []
        est_true = (len(a1) == 1 and a1[0].type == tokenize.NAME
                    and a1[0].string == "True")
        lib, forme = _valeur(a2)
        out.append((t.start[0], est_true, lib, forme))
    return out


def compte(chemin):
    """Le nombre de SITES d'appel — ⛔ pas d'invocations."""
    return len(sites(chemin))


def par_libelle(chemin):
    """{libelle litteral: [lignes]} — la resolution d'une CIBLE de mutant.

    ⛔ Le libelle est lu AU SOURCE, jamais a la console : la console le tronque
    (62 caracteres dans la gate du ledger, 56 dans celle du dossier) et des KO
    y collident.
    """
    par = {}
    for ligne, _t, lib, forme in sites(chemin):
        if forme == "litteral" and lib:
            par.setdefault(lib, []).append(ligne)
    return par


def true_litteraux(chemin):
    """Les `ctrl(True, …)` — `[(ligne, libelle, forme)]`, forme comprise.

    ⚠️ Un site dont le libelle n'est PAS un litteral est rendu quand meme,
    avec sa forme : il EXISTE, il est INCLASSABLE en l'etat, et l'inventaire
    d'AC40.2 doit le DIRE plutot que de ne pas le voir.
    """
    return [(ligne, lib, forme) for ligne, est_true, lib, forme in sites(chemin)
            if est_true]


def chaines(chemin):
    """`[(ligne, valeur)]` de TOUS les litteraux chaine — commentaires EXCLUS.

    🔴 AJOUTEE PAR LA REVUE DE CODE dn4-44 (2026-09-03). `survit_au_source` du
    tri cherchait son libelle dans le TEXTE BRUT : un libelle qui ne survivait
    que dans un **commentaire**, ou que dans le `ctrl()` qu'il etait cense
    avoir quitte, sortait « REMEDE APPLIQUE ». Le remede d'AC40.2 est que le
    site **PUBLIE** (`print`) au lieu de controler ⇒ il faut savoir distinguer
    une chaine de code d'une chaine de commentaire, et l'une d'un libelle de
    controle. `_toks` retire deja les commentaires : c'est la meme porte.
    """
    out = []
    for t in _toks(chemin):
        if t.type != tokenize.STRING:
            continue
        try:
            v = ast.literal_eval(t.string)
        except Exception:
            continue
        if isinstance(v, str):
            out.append((t.start[0], v))
    return out


def apparie(a, b):
    """Deux libelles designent-ils le meme controle ? — EGALITE STRICTE.

    🔴 REVUE DE CODE dn4-44 (2026-09-03) — CETTE FONCTION ETAIT UN PREFIXE
    **SYMETRIQUE**, ET C'ETAIT UN TROU DANS LA SEULE SECTION QUI PROTEGE
    L'AVENIR. `a.startswith(b) or b.startswith(a)` fait qu'un libelle NEUF qui
    **etend** un libelle deja classe sort « deja classe » de l'INVENTAIRE :
    ajouter `ctrl(True, "le ledger est present, et personne ne l'a jamais
    regarde")` ne faisait rougir personne. Et le meme prefixe faisait du temoin
    d'exemption un **joker** : `_legitime_au_tri("l")` rendait `True`.
    ⛔ La garde anti-vide qui etait ecrite ici ne couvrait que le cas `""`.

    🔬 MESURE QUI AUTORISE LE DURCISSEMENT, ⛔ pas un raisonnement : les cas
       declares au tableau `CAS` du tri ont ete confrontes aux libelles LUS au
       source — **11 exacts, 0 par prefixe**. ⛔ Aucune declaration ne dependait
       de la tolerance ⇒ l'egalite ne casse rien et ferme les deux trous.

    ⚠️ SI UN JOUR UNE DECLARATION DOIT ETRE TRONQUEE, elle ⛔ ne se rattrape
       pas ici : c'est la DECLARATION qui se corrige. Une tolerance de
       comparaison ne se remet pas « juste pour un cas » — elle rouvre les deux
       trous ci-dessus pour tous les autres.
    """
    return bool(a) and bool(b) and a == b


def texte(chemin):
    """Le source brut, lu avec L'ENCODAGE QUE PYTHON LUI-MEME LIRAIT.

    🔴 REVUE DE CODE dn4-44 (2026-09-03) — IL IMPOSAIT L'UTF-8 LA OU `sites()`
    RESPECTE LE COOKIE (`# -*- coding: … -*-`). Un source `latin-1`
    parfaitement legal se lisait donc d'un cote et levait `UnicodeDecodeError`
    de l'autre : les deux moities du meme test n'etaient pas d'accord sur le
    fichier. ⚠️ Et le descripteur n'etait **jamais ferme** — une fuite par gate
    balayee. ⇒ `tokenize.open` fait les deux, et c'est la MEME porte d'entree
    que le tokenizer.

    ⚠️ ELLE NE LEVE **PAS** SUR UNE ERREUR DE SYNTAXE, ET C'EST VOULU : elle
    rend le TEXTE, ⛔ pas une analyse. Un source casse a toujours un texte, et
    `survit_au_source` doit pouvoir y chercher un libelle. Elle ne leve que
    lorsque le fichier ⛔ ne se DECODE pas.
    """
    try:
        with tokenize.open(chemin) as fh:
            return fh.read()
    except (SyntaxError, UnicodeDecodeError, ValueError) as e:
        raise SourceIllisible("%s : %s" % (os.path.basename(chemin), e))

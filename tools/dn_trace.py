# -*- coding: utf-8 -*-
"""dn4-40 / AC40.7.c — LA CLE STABLE D'UN CONTROLE, POUR UNE CAMPAGNE.

🔴 LE MOTIF, MESURE LE 2026-09-02 : LES LIBELLES SONT TRONQUES A L'IMPRESSION
(56 caracteres dans `verif_dossier_dn415.py`, 62 dans `verif_ledger_dn416.py`),
et **4 lignes de KO de la sortie du jour portent un libelle tronque
IDENTIQUE**. Une campagne de mutants qui s'indexe sur la console ne peut donc
pas distinguer ces quatre-la : son compte de « controles gardes par rien »
serait FAUX, et faux dans le sens rassurant.

⇒ C'est la regle du depot appliquee a sa propre campagne :
  **une sortie redigee pour un humain n'est pas un format de donnees.**

La cle retenue est le SITE D'APPEL — `<fichier>:<ligne>` du `ctrl()` dans le
SOURCE. Elle ne bouge pas quand le libelle est tronque, et elle designe le
controle meme quand deux controles se ressemblent.

🔴 CORRIGE PAR LA REVUE DU 2026-09-03 — CE DOCSTRING DISAIT « ⛔ elle ne collide
   pas ». C'EST FAUX, ET C'EST MESURE : sur `verif_dossier_dn415.py`, une passe
   rend **30 lignes de trace pour 23 sites distincts, dont 4 COLLIDENT**. Un
   site dans une boucle s'execute une fois par element de sa population — et sur
   trois de ces quatre sites, les entrees collidees sont des controles
   LOGIQUEMENT DIFFERENTS (un par fichier balaye), la ou c'est le LIBELLE qui
   les distingue. Le defaut d'AC40.7.c etait donc DEPLACE du libelle vers le
   site, ⛔ pas supprime.
⇒ LA REGLE POUR QUI LIT CETTE TRACE : un site est KO des qu'UNE de ses lignes
  est KO. ⛔ JAMAIS « la derniere gagne » — une regression sur un seul element
  de la population deviendrait invisible. Les deux campagnes du depot
  appliquent cette agregation.

🔴 dn4-44 / AC5.1 — LA CLE RECOIT SON DISCRIMINANT, ET LE REPLIEMENT CESSE.
   L'agregation ci-dessus etait une MITIGATION, ⛔ pas le correctif : elle rend
   conservateur le verdict de sites REPLIES, elle ne les separe pas. Mesure du
   2026-09-03 sur les 9 gates instrumentees : **7 collident**, jusqu'a 8
   collisions sur `verif_paliers_dn441.py`, et sur 3 des 4 sites de la gate du
   dossier les entrees repliees sont des controles LOGIQUEMENT DIFFERENTS —
   un par fichier balaye, que **seul le libelle** distingue.
   ⇒ LA CLE EST DESORMAIS `(site, libelle)`. Le discriminant etait DEJA dans la
     trace : le 3e champ. ⛔ Aucun octet de plus n'est ecrit — c'est le LECTEUR
     qui repliait, ⛔ pas l'ecrivain.
   ⚠️ L'agregation « un KO l'emporte » RESTE, et elle garde toujours quelque
     chose : deux elements d'une population qui portent le MEME libelle (une
     boucle dont le libelle ne cite pas l'element) collident encore, et c'est
     alors le bon repliement.
   ⚠️ CONSEQUENCE MESUREE : les comptes « traces » et « gardes par rien » d'une
     campagne BOUGENT le jour ou elle lit par cette cle. Sur
     `verif_ledger_dn416.py` ils ne bougent pas (34 lignes / 34 sites / 0
     collision) ; sur la gate du dossier, ils bougent.

🔴 dn4-44 / AC5.5 — LA LECTURE VIT **ICI**, ⛔ PLUS EN DOUBLE DANS LES DEUX
   CAMPAGNES. Les deux portaient la meme agregation, recopiee mot pour mot,
   sans fonction partagee : l'une pouvait regresser sans que l'autre le dise.

⚠️ CE MODULE NE CHANGE PAS LA CONSOLE D'UN OCTET. Il n'ecrit que si
`DN_TRACE_CTRL` nomme un fichier. Sans la variable, `trace()` sort au premier
test — le format que le depot publie reste intact.

⚠️ IMPORT DEFENSIF chez l'appelant : une gate doit rester JOUABLE si ce
fichier manque (`try: import dn_trace / except ImportError:`). Une gate qui
refuse de demarrer parce que son INSTRUMENT manque rendrait un prerequis pour
un defaut.
"""
import io
import os
import sys

_FIC = os.environ.get("DN_TRACE_CTRL")


def actif():
    return bool(_FIC)


def trace(ok, libelle):
    """Ecrit une ligne indexee sur le SITE D'APPEL du `ctrl()`.

    Pile : frame 0 = `trace`, frame 1 = `ctrl`, **frame 2 = le site d'appel**.
    ⚠️ C'est bien le site d'appel qu'on veut, ⛔ pas le corps de `ctrl` : deux
    controles differents partagent le meme corps mais ⛔ jamais la meme ligne
    d'appel.
    """
    if not _FIC:
        return
    f = sys._getframe(2)
    # ⛔ REVUE 2026-09-03 — UN LIBELLE PORTANT UNE TABULATION OU UN SAUT DE
    #    LIGNE CASSAIT LE FORMAT A 3 CHAMPS : le lecteur jetait la ligne, et le
    #    controle DISPARAISSAIT de la trace ET du compte « gardes par rien »,
    #    sans qu'aucune sortie ne le dise. On aplatit — la trace est un format
    #    de DONNEES, elle se protege comme tel.
    # 🔴 REVUE DE CODE dn4-44 (2026-09-03) — L'APLATISSEMENT ETAIT ECRIT DEUX
    #    FOIS DANS LE FICHIER QUI VIENT DE DE-DUPLIQUER LA LECTURE. L'ECRIVAIN
    #    et le fabricant de cle doivent aplatir **IDENTIQUEMENT** : deux copies
    #    peuvent diverger, et la cle cesserait alors de s'apparier a sa propre
    #    ligne de trace, en silence. ⇒ un seul proprietaire : `aplati()`.
    plat = aplati(libelle)
    ligne = "%s:%d\t%s\t%s\n" % (os.path.basename(f.f_code.co_filename),
                                   f.f_lineno, "OK" if ok else "KO", plat)
    with io.open(_FIC, "a", encoding="utf-8") as fh:
        fh.write(ligne)


# ═══════════════════════════════════════════════════════════════════════════
#  LA LECTURE — dn4-44 / AC5.1 + AC5.5
#  ⛔ UNE SEULE implementation, pour les deux campagnes.
# ═══════════════════════════════════════════════════════════════════════════

SEP = "\t"


def aplati(libelle):
    """La forme du libelle TELLE QU'ELLE EST ECRITE dans la trace.

    ⚠️ Exposee parce qu'un appelant qui resout une cible AU SOURCE doit
    comparer a la MEME forme : un libelle source portant un saut de ligne
    ⛔ ne s'apparierait jamais a sa ligne de trace.
    """
    return (str(libelle).replace("\t", " ").replace("\r", " ")
            .replace("\n", " "))


def cle(site, libelle):
    """La cle d'un CONTROLE : `(site, libelle)`, ⛔ plus le site seul.

    ⚠️ Le libelle est APLATI ici aussi — un appelant qui passe le libelle lu
    au source obtient donc la meme cle que le lecteur de la trace.
    """
    return "%s%s%s" % (site, SEP, aplati(libelle))


def parts(k):
    """`(site, libelle)` — l'inverse de `cle()`, pour imprimer."""
    i = k.find(SEP)
    return (k, "") if i < 0 else (k[:i], k[i + 1:])


def lit(fic):
    """`{cle: (verdict, site, libelle)}` — l'agregation, ECRITE UNE FOIS.

    ⛔ « LA DERNIERE GAGNE » REND LES REGRESSIONS INVISIBLES : si le 1er
    element d'une population rougit et le dernier passe, une lecture naive
    retient « OK ». ⇒ UNE CLE EST KO DES QU'UNE DE SES LIGNES EST KO.

    ⚠️ Une ligne qui n'a pas EXACTEMENT 3 champs est ignoree — c'est le
    contrat du format, et `trace()` aplatit pour qu'il tienne.
    """
    d = {}
    if not os.path.isfile(fic):
        return d
    for l in io.open(fic, encoding="utf-8"):
        p = l.rstrip("\n").split(SEP)
        if len(p) != 3:
            continue
        k = cle(p[0], p[2])
        if k in d and d[k][0] == "KO":
            continue
        d[k] = (p[1], p[0], p[2])
    return d

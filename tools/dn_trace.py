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
    plat = str(libelle).replace("\t", " ").replace("\r", " ").replace("\n", " ")
    ligne = "%s:%d\t%s\t%s\n" % (os.path.basename(f.f_code.co_filename),
                                   f.f_lineno, "OK" if ok else "KO", plat)
    with io.open(_FIC, "a", encoding="utf-8") as fh:
        fh.write(ligne)

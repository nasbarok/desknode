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
SOURCE. Elle ne bouge pas quand le libelle est tronque, ⛔ elle ne collide pas,
et elle designe le controle meme quand deux controles se ressemblent.

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
    ligne = "%s:%d\t%s\t%s\n" % (os.path.basename(f.f_code.co_filename),
                                   f.f_lineno, "OK" if ok else "KO", libelle)
    with io.open(_FIC, "a", encoding="utf-8") as fh:
        fh.write(ligne)

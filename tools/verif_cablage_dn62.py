#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn6-2 — LA PAGE DE CABLAGE NE PEUT PAS POURRIR EN SILENCE.

======================= CE QUE CETTE GATE FAIT, ET POURQUOI =================

`docs/cablage.md` dit a un inconnu OU BRANCHER et QUOI CONCLURE de ce que le
bus repond. Une page de cablage FAUSSE est la pire chose que ce depot puisse
publier : elle envoie quelqu'un souder au mauvais endroit. Cette gate garde la
FORME de cette page, et rien d'autre.

🔴 ELLE EXISTE PARCE QU'UNE CAPTURE UNIQUE NE SUFFIT PAS. `dn5-6` puis
   `dn4-47` ont paye deux fois le meme prix : une propriete de prose verifiee
   UNE FOIS sous `mesures/` dit ce qui etait vrai LE JOUR OU ON A REGARDE.
   ⇒ ici, la propriete est REJOUEE a chaque passe.

── ⛔ CE QU'ELLE NE FAIT PAS, ET C'EST LA MOITIE DU SUJET ──────────────────

⛔ **ELLE NE JUGE AUCUNE VALEUR ELECTRIQUE.** Elle ne sait pas si `SCL` est
   sur GPIO7. Elle sait que la page l'ECRIT et qu'elle CITE une mesure qui
   EXISTE. La verite d'un brochage se verifie a la serigraphie, ⛔ pas en
   relisant un fichier.
⛔ Elle n'ouvre aucun port, ne touche ⛔ ni `firmware/` ⛔ ni `agent/`, et ne
   MODIFIE ⛔ aucun fichier — `hardware/` est ouvert en LECTURE SEULE, pour
   resoudre les sections citees.
⛔ Elle ne touche ⛔ pas aux photos de `docs/cablage/` : elle verifie que
   celles que la page CITE existent. Leur poids est le sujet de `dn6-3`.

── 🔴 LE § NU NE DESIGNE RIEN, ET C'EST MESURE ─────────────────────────────

Les trois fichiers de `hardware/` portent des sections HOMONYMES dont les
contenus n'ont AUCUN rapport. Mesure du 2026-09-07 :

  §13.1 · §13.2 · §13.3 · §13.4 · §13.10   ⇒ `…-capteurs-i2c.md` ET `…-liaison-pc.md`
  §16.6 · §17.2 · §17.4 · §17.5            ⇒ `…-affichage.md`   ET `…-liaison-pc.md`

⇒ Une citation au NUMERO NU designe deux choses. Cette gate resout donc la
  PAIRE (fichier, §), dans les deux sens :
    · elle REFUSE un § qui ne nomme pas son fichier             — (c2)
    · elle confronte la paire au dossier reel                   — (c3)
    · elle confronte la paire a la liste des sections FAUSSES   — (c4)

🔴 ET LA LISTE DES SECTIONS FAUSSES EST UNE LISTE DE PAIRES, ⛔ PAS DE
   NUMEROS. `dn4-34` nomme QUATRE sections fausses, et elles sont TOUTES dans
   `…-affichage.md`. Leurs homonymes de `…-liaison-pc.md` ⛔ ne sont PAS sur
   la liste : rougir dessus serait un FAUX POSITIF — exactement la classe de
   defaut que cette epic passe son temps a payer (`NFR6.3` contient `FR6.3`).
   ⇒ **le TEMOIN NEGATIF est un CONTROLE du chemin normal — (c32)**, joue a
     chaque passe : la paire `…-liaison-pc.md` §17.2 doit exister, ⛔ NE PAS
     etre retenue par la regle de (c4), et son homonyme de `…-affichage.md`
     DOIT l'etre. Les deux sens, ⛔ pas un.
   🔴 IL VIVAIT DERRIERE `--temoin-negatif`, ET **RIEN NE LE REJOUAIT** :
     `run_gates.sh` lance la gate SANS argument, et `verif_campagne_dn56.py`
     ne decouvre que `--liste-mutants`. La propriete CENTRALE de cette marche
     n'etait donc gardee que par une **capture unique** — precisement ce que
     `dn5-6` puis `dn4-47` ont paye deux fois. Corrige le 2026-09-07.
   ⚠️ `--temoin-negatif` SURVIT, et c'est un AUTRE objet : il rejoue le
     temoin **de bout en bout sur la page reelle** (la citation est injectee,
     puis les 37 controles tournent dessus). ⛔ Il n'est PAS declare dans
     `MUTANTS` — le contrat de la campagne exige de CHAQUE mutant qu'il
     ROUGISSE, et un temoin qui doit sortir VERT n'y a pas sa place.

── LA RECIPROQUE EST MECANIQUE, ⛔ PAS TENUE A LA MAIN ─────────────────────

🔴 `verif_bom_dn61.py` — le modele — tient `CONTROLES_PREVUS` a la main et
   mesure la reciproque A LA MAIN dans sa capture `T2` : qui ajoute un
   controle sans mutant ⛔ ne recoit AUCUN signal. C'est le risque nomme qui a
   valu a `dn6-1` sa `followup_review_recommended`.
⇒ ici, chaque mutant DECLARE le ou les controles qu'il vise (`CIBLES`), et
  DEUX controles finaux confrontent cette table aux identifiants REELLEMENT
  emis par la passe :
    · (c30) aucun controle n'est garde par ZERO mutant ;
    · (c31) aucun mutant ne vise un controle INEXISTANT (cible perimee).
  ⛔ Ce n'est pas reorganiser le harnais : c'est ecrire correctement SA
    PROPRE gate.
⚠️ CE QUE (c30) NE PROUVE PAS : que le mutant rougisse BIEN le controle
   qu'il declare. Ca, c'est la campagne — `mesures/dn6-2/T2`, qui relit les
   `[KO ]` a colonne fixe et confronte la cible declaree a la cible REELLE.

Sortie : `BILAN : n OK, m KO`, rc 0 si tout passe, 1 sinon.
Usage  : python3 tools/verif_cablage_dn62.py [--mutant <n>] [--liste-mutants]
                                             [--temoin-negatif]
         `--mutant` REPLANTE UNE FAUTE EN MEMOIRE et doit faire ROUGIR.
         ⛔ Aucun fichier du depot n'est modifie — la substitution vit dans
         une chaine, et les fichiers ne sont ouverts qu'en LECTURE.

⚠️ **UN MUTANT QUI DEBRANCHE LA GARDE NE PROUVE QUE SON EXISTENCE** (NFR7).
   Ceux d'ici REPLANTENT la faute REELLE — un § qui perd son fichier, une
   valeur qui perd sa citation, un piege d'embase qui disparait, une
   procedure ramenee a une passe, un `TESTED` muet, un lien de README retire.
"""

import argparse
import glob
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE_REL = "docs/cablage.md"
# ⚠️ dn8-4 (2026-09-13) — DELIBEREMENT ⛔ PAS REPOINTE. Ce `README.md` n'est plus le
#    journal francais (parti octet pour octet dans `docs/journal-de-bord.md`) :
#    c'est la VITRINE anglaise. Cette gate continue de la lire parce que ce
#    qu'elle garde — les liens `docs/cablage.md` et `docs/bom.md` — est la
#    decouvrabilite depuis la page d'accueil, et la vitrine porte ce(s) lien(s)
#    MOT POUR MOT. Repointer sur le journal garderait un lien qu'un inconnu ⛔ ne
#    lit plus en premier.
README_REL = "README.md"
DOSSIER_PHOTOS = "docs/cablage"
DOSSIER_HW = "hardware"

# Les deux paliers de D19 — ce sont des NOMS, ⛔ pas des descriptions.
PALIERS = ("DeskNode", "DeskNode + Ambiance")

# 🔴 LA LISTE `dn4-34`, PAR PAIRE (fichier, §) — ⛔ JAMAIS PAR NUMERO.
#    Relue au tracker le 2026-09-07 : `dn4-34-le-dossier-materiel-rattrape-
#    ses-tables`, statut `backlog`, PORTEUR VIVANT. Les quatre § sont ceux de
#    `…-affichage.md` ; leurs homonymes de `…-liaison-pc.md` ⛔ n'y sont PAS.
FICHIER_LISTE_DN434 = "ESP32-S3-Touch-LCD-2.8B-affichage.md"
LISTE_DN434 = {(FICHIER_LISTE_DN434, s)
               for s in ("16.6", "17.2", "17.4", "17.5")}
PORTEUR_DN434 = "dn4-34-le-dossier-materiel-rattrape-ses-tables"

# Le temoin negatif : une paire LEGITIME dont le § est homonyme d'un § faux.
TEMOIN_NEGATIF = ("ESP32-S3-Touch-LCD-2.8B-liaison-pc.md", "17.2")
# Le temoin negatif du comptage d'autoportance : une notion qui n'existe
# NULLE PART. Sans lui, un compteur MORT rendrait « 0 introuvable » et
# passerait pour sain (defaut nomme par `mesures/dn6-1/T3`).
TEMOIN_NOTION = "DeskNode Turbo"

RE_CITATION = re.compile(
    r"`([^`\s]*\.md)`\s*§\s*(\d+(?:\.\d+)+)((?:\s+(?:bis|ter|quater))?)")
RE_PARAGRAPHE = re.compile(r"\n\s*\n")
RE_DATE = re.compile(r"20\d{2}-\d{2}-\d{2}")
RE_SHA = re.compile(r"`([0-9a-f]{7,40})`")
RE_DUREE = re.compile(r"\d[\d\s  ]*\s*(?:s\b|secondes?|min\b|minutes?|h\b|"
                      r"heures?|j\b|jours?)", re.I)
RE_PALIER_CITE = re.compile(r"palier\s*«\s*([^»\n]{2,40}?)\s*»", re.I)

LARGEUR_LIBELLE = 58  # la colonne de `ctrl()` — la cle que `T2` relit
MIN_GLOSE = 15        # ce qu'il faut apres un terme pour que ce soit une GLOSE
MIN_TESTED_TROU = 60  # ce qu'il faut pour qu'un « jamais essaye » soit ecrit
# 🔴 UNE LONGUEUR NE FAIT PAS UN TROU DECLARE — MESURE DU 2026-09-07 :
#    remplacer les DEUX cellules « ce qui n'a JAMAIS ete essaye » par les 66
#    caracteres de « Rien de particulier a signaler, tout est nominal. »
#    laissait `31 OK, 0 KO`. Une cellule qui dit « tout va bien » a la place
#    d'un trou est EXACTEMENT le silence que `AC6.2.4` interdit. ⇒ la cellule
#    doit porter une NEGATION DE TEST, ⛔ pas seulement du volume.
RE_NEGATION_TESTED = re.compile(
    r"jamais|n'a pas|n'ont pas|non observ|pas (?:ete |été )?"
    r"(?:exerc|essay|mesur|tenu|reproduit)", re.I)

ok_total = [0]
ko_total = [0]
ids_emis = []

MUTANTS = {}                      # ⛔ AU NIVEAU MODULE — sinon `--liste-mutants`
CIBLES = {}                       # ⛔ AU NIVEAU MODULE — c'est la matiere de (c30)

MUTANTS[1] = ("retire le NOM DU FICHIER d'une citation : le `§` reste NU, "
              "et un § nu designe DEUX sections sans rapport")
CIBLES[1] = ("c2",)
MUTANTS[2] = ("fait pointer une citation sur un § INEXISTANT du fichier "
              "qu'elle nomme (`§13.99`)")
CIBLES[2] = ("c3",)
MUTANTS[3] = ("remplace le fichier d'une citation par `…-affichage.md` en "
              "gardant `§17.2` ⇒ la PAIRE tombe sur la liste `dn4-34`")
CIBLES[3] = ("c4",)
MUTANTS[4] = ("rend `GPIO7` NU — la citation disparait de toutes ses lignes")
CIBLES[4] = ("c5",)
MUTANTS[5] = ("rend `GPIO15` NU — la citation disparait de toutes ses lignes")
CIBLES[5] = ("c6",)
MUTANTS[6] = ("rend l'ALIMENTATION nue — `3V3` et `GND` perdent leur citation")
CIBLES[6] = ("c7",)
MUTANTS[7] = ("rend `0x77` NU (l'adresse du BME680 sans sa mesure)")
CIBLES[7] = ("c8",)
MUTANTS[8] = ("rend `0x23` NU (l'adresse du BH1750 sans sa mesure)")
CIBLES[8] = ("c9",)
MUTANTS[9] = ("supprime l'avertissement d'INVERSION `SDA`/`SCL` de la source "
              "tierce (le lecteur ne sait plus laquelle est mesuree)")
# ⚠️ CIBLE DOUBLE, ET C'EST MESURE, ⛔ pas suppose : (c11) cherche une DATE
#    DANS les fenetres d'avertissement de (c10). Retirer l'avertissement vide
#    donc la population de (c11), qui rougit avec. La cible declaree dit la
#    VERITE de ce que le mutant fait ; le mutant 10, lui, isole (c11) seul.
CIBLES[9] = ("c10", "c11")
MUTANTS[10] = ("retire la DATE de l'avertissement d'inversion, ⛔ sans "
               "toucher aux dates des noms de photos")
CIBLES[10] = ("c11",)
MUTANTS[11] = ("supprime le piege des DEUX EMBASES JST jumelles "
               "(elles restent nommees, le danger disparait)")
CIBLES[11] = ("c12",)
MUTANTS[12] = ("supprime le piege de la RANGEE A (`RXD`/`TXD` derriere "
               "`SCL`/`SDA`) — le jumeau du precedent a 2,54 mm")
CIBLES[12] = ("c13",)
MUTANTS[13] = ("ramene la procedure a UNE SEULE PASSE "
               "(§13.2 en a fabrique une quinzaine de faux positifs)")
CIBLES[13] = ("c14",)
MUTANTS[14] = ("remplace « a ne pas croire sur parole » par « faux positif "
               "prouve » — la nuance qui separe un doute d'un verdict")
CIBLES[14] = ("c15",)
MUTANTS[15] = ("retire le DEPARTAGE par lecture de registre "
               "(il ne reste plus que le scan, qui ne qualifie rien)")
CIBLES[15] = ("c16",)
MUTANTS[16] = ("fait dire a la page qu'un TIMEOUT vaut ABSENCE")
CIBLES[16] = ("c17",)
MUTANTS[17] = ("retire le mot MESURE de la fenetre `0x76` : le faux positif "
               "devient une hypothese")
CIBLES[17] = ("c18",)
MUTANTS[18] = ("retire `0x77` de la fenetre `0x76` ⇒ le lecteur peut "
               "conclure « le capteur repond »")
CIBLES[18] = ("c19",)
MUTANTS[19] = ("remet « bouger → scanner », qui ⛔ ne peut PAS converger "
               "(alimentation fantome, §13.10)")
CIBLES[19] = ("c20",)
MUTANTS[20] = ("renomme le palier d'un bloc `TESTED` ⇒ un palier se retrouve "
               "SANS bloc, et rien ne le dit")
CIBLES[20] = ("c21",)
MUTANTS[21] = ("vide la cellule « Combien de temps » d'un bloc `TESTED`")
CIBLES[21] = ("c22",)
MUTANTS[22] = ("vide la cellule « Sur quel SHA » d'un bloc `TESTED`")
CIBLES[22] = ("c23",)
MUTANTS[23] = ("vide la cellule « ce qui n'a JAMAIS ete essaye » "
               "(le SILENCE, qui n'est pas un `TESTED`)")
CIBLES[23] = ("c24",)
MUTANTS[24] = ("retire du README le lien vers `docs/cablage.md` "
               "(la page devient INTROUVABLE)")
CIBLES[24] = ("c25",)
MUTANTS[25] = ("retire du README le lien vers `docs/bom.md` "
               "(la decouvrabilite n'etait gardee par AUCUNE gate)")
CIBLES[25] = ("c26",)
MUTANTS[26] = ("fait pointer une photo citee sur un fichier INEXISTANT")
CIBLES[26] = ("c27",)
MUTANTS[27] = ("retire TOUTES les citations de photos ⇒ la population de "
               "(c27) se vide, et ⛔ un vide n'est pas une absence de defaut")
CIBLES[27] = ("c28",)
MUTANTS[28] = ("fait nommer au lecteur un palier « DeskNode Turbo » qui "
               "n'est DEFINI nulle part dans le clone")
CIBLES[28] = ("c29",)
MUTANTS[29] = ("rend la page VIDE (une gate qui ne trouve rien ⛔ ne sort "
               "pas verte)")
CIBLES[29] = ("c1",)
# 🔴 LES DEUX DERNIERS NE MUTENT ⛔ PAS LE TEXTE : ils replantent la faute
#    DANS LA MATIERE QUE (c30)/(c31) LISENT — la table `CIBLES`. C'est
#    exactement ce qu'une future marche ferait en ajoutant un controle sans
#    mutant, ou en retirant un mutant sans retirer sa cible.
#    ⛔ Ils ne DEBRANCHENT rien : la garde reste entiere, la faute est reelle.
MUTANTS[30] = ("retire une cible de la table `CIBLES` ⇒ un controle garde "
               "par ZERO mutant, exactement le risque herite de `dn6-1`")
CIBLES[30] = ("c30",)
MUTANTS[31] = ("declare dans `CIBLES` un controle INEXISTANT (`c99`) ⇒ une "
               "cible PERIMEE, que « N mutants, N rouges » ne verrait pas")
CIBLES[31] = ("c31",)
# 🔴 LES NEUF SUIVANTS SONT NES DE LA REVUE DU 2026-09-07. Chacun REPLANTE la
#    faute que son controle venait de rater — ⛔ aucun ne DEBRANCHE une garde.
MUTANTS[32] = ("ecrit la liste `dn4-34` AU NUMERO au lieu de la PAIRE ⇒ le "
               "temoin `…-liaison-pc.md` §17.2 se fait prendre a tort")
CIBLES[32] = ("c32",)
MUTANTS[33] = ("declare une cible pour un mutant qui N'EXISTE PAS "
               "(`CIBLES` et `MUTANTS` cessent de se correspondre)")
CIBLES[33] = ("c33",)
MUTANTS[34] = ("retire de la page que les DEUX TEMOINS POSITIFS manquants "
               "signent un INSTRUMENT CASSE")
CIBLES[34] = ("c34",)
MUTANTS[35] = ("fait dire a la page de laisser `ADDR` EN L'AIR "
               "(l'adresse du BH1750 redevient INDEFINIE)")
CIBLES[35] = ("c35",)
MUTANTS[36] = ("supprime le PIEGE DU MIROIR : poser les fils « dans l'ordre » "
               "redevient sans consequence ecrite")
CIBLES[36] = ("c36",)
# ⚠️ CIBLE TRIPLE, ET C'EST MESURE : (c18) et (c19) selectionnent leur matiere
#    DANS cette section. La renommer les prive de matiere — elles le DISENT
#    desormais au lieu de parler de `0x76`, ce qui etait un vrai rouge pour un
#    faux motif.
MUTANTS[37] = ("renomme la SECTION D'ANCRAGE de la procedure ⇒ (c18)/(c19) "
               "perdent leur matiere, et (c37) nomme la vraie cause")
CIBLES[37] = ("c37", "c18", "c19")
MUTANTS[38] = ("replante une SORTIE ANTICIPEE NON DECLAREE : le bilan "
               "retrecit, et il sortirait VERT")
CIBLES[38] = ("z",)
MUTANTS[39] = ("raccourcit une GLOSE REELLE sous le seuil ⇒ la notion n'est "
               "plus DEFINIE, seulement MENTIONNEE")
CIBLES[39] = ("c29",)
MUTANTS[40] = ("remplace un trou `TESTED` par « tout est nominal » a la bonne "
               "LONGUEUR (le silence DECORE, qui sortait vert)")
CIBLES[40] = ("c24",)

# ⛔ LES MUTANTS QUI NE TOUCHENT PAS AU TEXTE : leur matiere est une table de
#    la gate, ⛔ pas la page. La garde du no-op les excepte NOMMEMENT.
SANS_TEXTE = (30, 31, 32, 33, 38)

# ⚠️ LE COMPTE DU CHEMIN NORMAL, hors le controle final qui le confronte.
#    Il se PERIME si on ajoute un controle sans le mettre a jour — et c'est
#    voulu : c'est ce qui rend (z) FALSIFIABLE.
CONTROLES_PREVUS = 37

_MUTANT = 0
_TEMOIN = False


RE_ID_CTRL = re.compile(r"\((\w+)\)")


def ctrl(ok, libelle, detail=""):
    """UNE assertion, UNE ligne, UN identifiant. ⛔ Aucun controle muet.

    ⚠️ L'IDENTIFIANT VIT DANS LE LIBELLE, ⛔ pas dans un argument a part —
       et c'est une MESURE, ⛔ pas un gout : `verif_campagne_dn56.py` lit les
       libelles A L'AST en prenant `args[1]` de chaque `ctrl(...)` — et ce
       qu'il en MESURE est leur LONGUEUR. Avec une signature
       `ctrl(cid, ok, libelle)`, `args[1]` etait le booleen : il ne resolvait
       que **5 libelles sur 31** et publiait cette population RETRECIE sans
       rougir (mesure du 2026-09-07). ⛔ Une gate ne retrecit pas l'instrument
       d'une autre.
    ⚠️ ⛔ CE QUE CA NE DONNE PAS, ET C'EST ECRIT : **neuf** libelles d'ici sont
       formates au `%` A L'EXECUTION — les cinq de (c5)→(c9), (c25), (c26) et
       les deux `(c0)` du chemin des mutants. L'AST y substitue un jeton de
       longueur plausible : il en tire donc une LONGUEUR juste, ⛔ mais AUCUN
       identifiant litteral. La cle de campagne s'en satisfait ; ⛔ un lecteur
       qui chercherait `(c5)` dans la source ne le trouvera pas ecrit la.
    ⚠️ Le libelle est imprime a COLONNE FIXE (58) : c'est la cle que la
       campagne de `mesures/dn6-2/T2` relit pour attribuer chaque signalement
       de defaut a son controle. ⛔ Un libelle qui deborde casse cette lecture
       EN SILENCE — d'ou l'assertion ci-dessous, qui est le seul endroit du
       fichier ou un defaut de PROGRAMMATION s'arrete bruyamment."""
    assert len(libelle) <= LARGEUR_LIBELLE, (
        "libelle de %d colonnes (max %d) : %r — il deborderait la cle a "
        "colonne fixe" % (len(libelle), LARGEUR_LIBELLE, libelle))
    m = RE_ID_CTRL.match(libelle)
    ids_emis.append(m.group(1) if m else "?")
    if ok:
        ok_total[0] += 1
    else:
        ko_total[0] += 1
    print("  [%s] %-58s %s" % ("OK " if ok else "KO ", libelle, detail))
    return ok


def bilan(rc, anticipee=""):
    """TOUT CHEMIN QUI REND UN VERDICT passe ici. Une gate qui sort sans
    `BILAN` est indiscernable d'une gate MORTE — et c'est precisement le
    discriminant que `verif_campagne_dn56.py` exige de chaque mutant.

    ⚠️ DEUX SORTIES NE PASSENT PAS ICI, ET C'EST ECRIT PLUTOT QUE PROMIS :
       · `--liste-mutants`, qui n'emet AUCUN controle et ne rend AUCUN
         verdict — la campagne ne s'en sert que pour enumerer ;
       · `sys.exit("MUTANT %d INCONNU")`, qui est une ERREUR D'APPEL.
       ⛔ Aucune des deux ne peut etre prise pour un verdict vert."""
    emis = ok_total[0] + ko_total[0]
    if not anticipee and emis != CONTROLES_PREVUS:
        ctrl(False, "(z) tout controle prevu est EMIS",
             "⛔ %d emis pour %d prevus — une gate qui joue MOINS de controles "
             "qu'annonce sort VERTE sur une population RETRECIE, ⛔ sans le "
             "declarer" % (emis, CONTROLES_PREVUS))
        rc = 1
    print("\n" + "=" * 78)
    if anticipee:
        print("⛔ SORTIE ANTICIPEE — %d controle(s) emis sur %d prevus : %s"
              % (ok_total[0] + ko_total[0], CONTROLES_PREVUS, anticipee))
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return rc


# ═══════════════════════ LIRE LE DOSSIER MATERIEL ══════════════════════════

def dispo_hw():
    """Alias lisible de `fichiers_hw()` — les `.md` de `hardware/`."""
    return fichiers_hw()


def fichiers_hw():
    """Les `.md` de `hardware/`, en LECTURE SEULE. Rend `[basename]`."""
    return sorted(os.path.basename(p) for p in
                  glob.glob(os.path.join(RACINE, DOSSIER_HW, "*.md")))


RE_TITRE_SECTION = re.compile(
    r"^#{1,6}\s*(?:[^\w\s]|\s)*?(\d+(?:\.\d+)+)\s*(bis|ter|quater)?\b")


def sections_de(basename):
    """`{numero: [ligne]}` — les sections que le fichier DECLARE en titre.

    ⛔ Aucune reconnaissance par position : un titre qui ne porte pas son
    numero n'est pas une section, et c'est ecrit plutot que devine."""
    out = {}
    chemin = os.path.join(RACINE, DOSSIER_HW, basename)
    try:
        with open(chemin, encoding="utf-8", errors="replace") as fh:
            lignes = fh.read().split("\n")
    except OSError:
        return out
    for i, l in enumerate(lignes, 1):
        if not l.startswith("#"):
            continue
        m = RE_TITRE_SECTION.match(l)
        if m:
            cle = m.group(1) + (" " + m.group(2) if m.group(2) else "")
            out.setdefault(cle, []).append(i)
    return out


def resout_fichier(jeton, dispo):
    """Le fichier de `hardware/` qu'un jeton de citation designe.

    Le depot ecrit ses renvois en forme ABREGEE (`…-capteurs-i2c.md`) — c'est
    sa convention, y compris dans ses propres cadrages. On l'accepte, ⛔ mais
    seulement quand elle designe **EXACTEMENT UN** fichier : une abreviation
    ambigue ⛔ ne nomme rien, et elle rend `None` comme une absence."""
    reste = jeton.lstrip("….").lstrip("/")
    if reste.startswith("hardware/"):
        reste = reste[len("hardware/"):]
    cands = [f for f in dispo if f == reste or f.endswith(reste)]
    return cands[0] if len(cands) == 1 else None


# ═══════════════════════ LIRE LA PAGE ══════════════════════════════════════

def duree_ecrite(v):
    """Une duree ECRITE, ⛔ pas un nombre nu.

    ⚠️ Elle s'appelait `RE_DURE_OK` — un prefixe `RE_` reserve, dans ce
       fichier, aux MOTIFS COMPILES — et elle etait declaree APRES son
       appelant. Deux facons de se faire lire pour ce qu'elle n'est pas."""
    return bool(RE_DUREE.search(v))


def paragraphes(texte):
    return [p for p in RE_PARAGRAPHE.split(texte) if p.strip()]


def cellules(ligne):
    return [c.strip() for c in ligne.strip().strip("|").split("|")]


def est_separateur(ligne):
    return bool(re.fullmatch(r"\|[\s:|-]+\|", ligne.strip()))


def tables(texte):
    """`[(entetes, [lignes])]` — toutes les tables markdown du texte."""
    out, lignes, i = [], texte.split("\n"), 0
    while i < len(lignes) - 1:
        if (lignes[i].strip().startswith("|")
                and est_separateur(lignes[i + 1])):
            ent, corps, j = cellules(lignes[i]), [], i + 2
            while j < len(lignes) and lignes[j].strip().startswith("|"):
                corps.append(lignes[j])
                j += 1
            out.append((ent, corps))
            i = j
            continue
        i += 1
    return out


def colonne(entetes, motif):
    for k, c in enumerate(entetes):
        if motif in c.lower():
            return k
    return None


def nom_nu(s):
    """Un nom DEBARRASSE de sa decoration, pour comparer des NOMS.
    ⚠️ Mesure heritee de `dn6-1` : exiger la forme A GUILLEMETS mesurait la
       DECORATION, ⛔ pas le nom — le README ecrit les paliers EN GRAS."""
    return re.sub(r"\s+", " ", re.sub(r"[*`«»\"'']", " ", s)).strip().lower()


def palier_du_titre(titre):
    """Le palier qu'un titre nomme — le PLUS LONG, ⛔ jamais le premier.

    🔴 LE PIEGE DE SOUS-CHAINE : « DeskNode » est CONTENU dans « DeskNode +
       Ambiance », exactement comme `FR6.3` est contenu dans `NFR6.3`. Le nom
       doit etre DELIMITE : ⛔ ni suivi d'un mot, ⛔ ni d'un `+` qui le
       prolonge en un palier PLUS LONG."""
    tn = nom_nu(titre)
    cands = [q for q in PALIERS
             if re.search(re.escape(nom_nu(q)) + r"(?!\s*[\w+])", tn)]
    return max(cands, key=len) if cands else None


def blocs_tested(texte):
    """`[(titre, corps)]` — les blocs dont le TITRE porte `TESTED`.

    🔴 UN BLOC SE FERME AU PROCHAIN TITRE **DE N'IMPORTE QUEL NIVEAU** OU SUR
       UN `---`. Mesure du 2026-09-07 : la 1re redaction ne fermait que sur
       `### `, si bien que le corps du DERNIER bloc courait jusqu'a la fin du
       fichier et absorbait `## Ou lire la mesure complete` et `## Licence`.
       Consequence : SUPPRIMER la ligne `| **Sur quel SHA** | … |` d'un bloc
       et poser n'importe quelle table portant ce libelle PLUS BAS dans la
       page laissait (c23) VERT. Le mutant 22 ne fait que VIDER la cellule ;
       la ligne SUPPRIMEE n'etait couverte par rien."""
    out, titre, corps = [], None, []
    for l in texte.split("\n"):
        if l.startswith("#"):
            if titre is not None:
                out.append((titre, "\n".join(corps)))
                titre, corps = None, []
            if l.startswith("### "):
                t = l[4:].strip()
                if "TESTED" in t.upper():
                    titre, corps = t, []
        elif l.strip().startswith("---") and titre is not None:
            out.append((titre, "\n".join(corps)))
            titre, corps = None, []
        elif titre is not None:
            corps.append(l)
    if titre is not None:
        out.append((titre, "\n".join(corps)))
    return out


def ligne_de_bloc(corps, motif):
    """La cellule VALEUR d'une ligne `| **Libelle** | valeur |` du bloc."""
    for l in corps.split("\n"):
        if not l.strip().startswith("|") or est_separateur(l):
            continue
        c = cellules(l)
        if len(c) >= 2 and motif.search(nom_nu(c[0])):
            return c[1]
    return None


def glose(notion, textes):
    """Les lignes ou `notion` est **DEFINIE**, ⛔ pas seulement mentionnee.

    🔴 C'EST LE DEFAUT QUE `mesures/dn6-1/T3` A DECLARE SUR LUI-MEME : son
       comptage comptait des OCCURRENCES — *« un mot present dix fois sans
       jamais etre explique sortirait a 10 »*. Ici, un site de DEFINITION est
       une ligne ou le terme est **suivi d'une glose** : un ouvreur (`—`,
       `:`, `(` ou la cellule suivante d'un tableau) puis au moins
       `MIN_GLOSE` caracteres. ⛔ Une mention en prose courante ne compte pas.
    ⚠️ BORNES DE MOT des deux cotes : sans elles, « DeskNode » serait defini
       par « DeskNode Turbo », et le temoin negatif ⛔ ne pourrait jamais
       sortir a 0."""
    # ⚠️ LE GUILLEMET FERMANT EST ACCEPTE ENTRE LE TERME ET SON OUVREUR —
    #    mesure du 2026-09-07 : sans lui, `glose("DeskNode", page)` rendait []
    #    alors que la page ecrit `### Palier « DeskNode » — la carte seule…`.
    #    La page ne definissait AUCUN de ses propres paliers aux yeux de son
    #    propre instrument, et (c29) reposait entierement sur les DEUX AUTRES
    #    fichiers. `nom_nu()` retire deja ces guillemets pour les titres.
    rx = re.compile(r"(?<![\w-])\*{0,2}`?" + re.escape(notion)
                    + r"`?\*{0,2}\s*[»\"\']*\s*(?:—|–|:|\(|\|)"
                      r"\s*([^|\n]{%d,})" % MIN_GLOSE, re.I)
    out = []
    for nom, src in textes.items():
        for l in src.split("\n"):
            if rx.search(l):
                out.append("%s: %s" % (nom, l.strip()[:48]))
    return out


# ═══════════════════════════ LES MUTANTS ═══════════════════════════════════
# ⛔ Chacun REPLANTE une faute dans la MATIERE QUE LE CONTROLE LIT. Aucun ne
#    debranche un controle, aucun ne touche le disque.

def _premiere_citation(t):
    m = RE_CITATION.search(t)
    return m.group(0) if m else None


def _sans_citation(t, jeton):
    """Retire la CITATION de toutes les lignes portant `jeton`."""
    out = []
    for l in t.split("\n"):
        if jeton in l:
            l = RE_CITATION.sub("le dossier materiel", l)
        out.append(l)
    return "\n".join(out)


def _pose_cellule(t, motif, valeur):
    """Ecrit `valeur` dans la cellule VALEUR de la 1re ligne qui matche."""
    for l in t.split("\n"):
        if not l.strip().startswith("|") or est_separateur(l):
            continue
        c = cellules(l)
        if len(c) >= 2 and motif.search(nom_nu(c[0])):
            c[1] = valeur
            return t.replace(l, "| " + " | ".join(c) + " |", 1)
    return t


def _vide_cellule(t, motif):
    """Vide la cellule VALEUR de la 1re ligne `| **Libelle** | valeur |`."""
    for l in t.split("\n"):
        if not l.strip().startswith("|") or est_separateur(l):
            continue
        c = cellules(l)
        if len(c) >= 2 and motif.search(nom_nu(c[0])):
            c[1] = " "
            return t.replace(l, "| " + " | ".join(c) + " |", 1)
    return t


# Les ancres LITTERALES des mutants de prose. ⛔ Elles vivent ici pour qu'un
# mutant devenu SANS EFFET se voie : la garde du no-op le declare en KO.
A_PIEGE_JST = ("les deux embases sont physiquement IDENTIQUES et ADJACENTES")
A_PIEGE_RANG = ("**exactement derrière** `SCL` et `SDA`. Se tromper de "
                "rangée alimente correctement le\ncapteur (`3V3` et `G` "
                "sont en 11-12 **des deux rangées**) et lui envoie l'UART "
                ": muet, sans\nsignal, encore une fois.")
A_PASSES = "plusieurs passes"
A_PASSES2 = "re-sonde 5 fois"
A_PAROLE = "à ne pas croire sur parole"
A_REGISTRE = ("Une lecture de **registre**. Un faux positif n'a aucun\n"
              "registre à rendre")
A_TIMEOUT = "Un timeout n'est PAS une absence"
A_MESURE76 = "C'est un faux positif\n**mesuré** sur cette carte"
A_77 = "**le BME680 de ce montage est à `0x77`**"
A_COUPER = ("**La seule séquence valable est : bouger → COUPER L'ALIMENTATION → rescanner.** Couper\n"
            "l'alimentation veut dire **débrancher le câble USB** — ⛔ ni un `reboot`, qui laisse le rail 3V3\n"
            "debout, ⛔ ni le retrait du fil `VCC`")
A_INSTRUMENT = "est un\ninstrument cassé"
A_ADDR = "**souder `ADDR` à `GND`**"
A_MIROIR = ("**Aucun des deux modules ne s'aligne « premier avec premier », "
            "sur AUCUN des deux accès.** Poser\nles quatre fils dans l'ordre "
            "**inverse l'alimentation** (`VCC` sur `GND`) **et croise "
            "`SDA`/`SCL`**\n— sur les deux modules.")
A_SECTION_PROC = "## 🔴 LA PROCÉDURE DE VÉRIFICATION"
A_GLOSE = "| PCF85063A | soudé sur la carte (horloge) |"
# ⚠️ 66 CARACTERES — la longueur EXACTE mesuree le 2026-09-07, celle qui
#    passait (c24) quand il ne comptait que du volume.
A_NOMINAL = "Rien de particulier a signaler, tout est nominal. Aucune reserve."


def muter(textes):
    """Rend le dict `{chemin: texte}` MUTE. ⛔ Aucun fichier n'est ouvert en
    ecriture : la substitution vit dans une chaine."""
    if not _MUTANT:
        return textes
    t = dict(textes)
    p, r = PAGE_REL, README_REL
    if _MUTANT == 1:
        c = _premiere_citation(t[p])
        t[p] = t[p].replace(c, "§" + RE_CITATION.match(c).group(2), 1)
    elif _MUTANT == 2:
        c = _premiere_citation(t[p])
        m = RE_CITATION.match(c)
        t[p] = t[p].replace(c, "`%s` §13.99" % m.group(1), 1)
    elif _MUTANT == 3:
        c = _premiere_citation(t[p])
        t[p] = t[p].replace(c, "`…-affichage.md` §17.2", 1)
    elif _MUTANT == 4:
        t[p] = _sans_citation(t[p], "GPIO7")
    elif _MUTANT == 5:
        t[p] = _sans_citation(t[p], "GPIO15")
    elif _MUTANT == 6:
        t[p] = _sans_citation(_sans_citation(t[p], "3V3"), "GND")
    elif _MUTANT == 7:
        t[p] = _sans_citation(t[p], "0x77")
    elif _MUTANT == 8:
        t[p] = _sans_citation(t[p], "0x23")
    elif _MUTANT == 9:
        t[p] = t[p].replace("permutées", "reprises").replace(
            "inversés", "repris")
    elif _MUTANT == 10:
        # ⚠️ CHIRURGICAL : la meme date vit dans DEUX NOMS DE PHOTO
        #    (`2026-08-16_2228-…jpg`). Un `sed` global casserait AUSSI (c27)
        #    — il synchroniserait la faute et sa fixture.
        t[p] = re.sub(r"2026-08-16(?!_)", "récemment", t[p])
    elif _MUTANT == 11:
        t[p] = t[p].replace(A_PIEGE_JST, "l'embase I²C est repérable")
    elif _MUTANT == 12:
        t[p] = t[p].replace(A_PIEGE_RANG, "un peu plus loin.")
    elif _MUTANT == 13:
        t[p] = t[p].replace(A_PASSES, "une seule passe").replace(
            A_PASSES2, "sonde une fois")
    elif _MUTANT == 14:
        t[p] = t[p].replace(A_PAROLE, "un faux positif prouvé")
    elif _MUTANT == 15:
        t[p] = t[p].replace(A_REGISTRE, "Un second scan suffit")
    elif _MUTANT == 16:
        t[p] = t[p].replace(A_TIMEOUT, "Un timeout vaut absence")
    elif _MUTANT == 17:
        t[p] = t[p].replace(A_MESURE76, "C'est peut-être un artefact")
    elif _MUTANT == 18:
        t[p] = t[p].replace(A_77, "**le BME680 est ailleurs**")
    elif _MUTANT == 19:
        t[p] = t[p].replace(A_COUPER,
                            "**Bouge le fil et rescanne** jusqu'à ce que "
                            "l'adresse apparaisse")
    elif _MUTANT == 20:
        # ⚠️ IL VISE LE **TITRE DU BLOC**, ⛔ plus « la 1re occurrence » : la
        #    page nomme aussi ce palier dans sa prose, et une substitution
        #    positionnelle y frappait — le mutant avait un EFFET (donc la
        #    garde du no-op se taisait) mais ⛔ pas sur (c21). Mesure du
        #    2026-09-07 : un mutant peut viser A COTE sans etre un no-op.
        t[p] = t[p].replace("### `TESTED` — palier « DeskNode + Ambiance »",
                            "### `TESTED` — option capteurs", 1)
    elif _MUTANT == 21:
        t[p] = _vide_cellule(t[p], re.compile("combien de temps"))
    elif _MUTANT == 22:
        t[p] = _vide_cellule(t[p], re.compile("sur quel sha"))
    elif _MUTANT == 23:
        t[p] = _vide_cellule(t[p], re.compile("jamais"))
    elif _MUTANT == 24:
        t[r] = t[r].replace("(docs/cablage.md)", "(le dossier matériel)")
    elif _MUTANT == 25:
        t[r] = t[r].replace("(docs/bom.md)", "(la place de marché)")
    elif _MUTANT == 26:
        t[p] = t[p].replace("](cablage/2026-08-16_2228",
                            "](cablage/2026-08-16_9999", 1)
    elif _MUTANT == 27:
        t[p] = t[p].replace("](cablage/", "](https://example.invalid/")
    elif _MUTANT == 28:
        t[p] = t[p].replace(
            "## Licence",
            "⇒ **Si tu construis le palier « DeskNode Turbo », câble comme "
            "ci-dessus.**\n\n## Licence", 1)
    elif _MUTANT == 29:
        t[p] = ""
    elif _MUTANT == 34:
        t[p] = t[p].replace(A_INSTRUMENT, "mérite un\nsecond essai")
    elif _MUTANT == 35:
        t[p] = t[p].replace(A_ADDR, "le laisser en l'air")
    elif _MUTANT == 36:
        t[p] = t[p].replace(A_MIROIR, "**Pose les quatre fils dans l'ordre.**")
    elif _MUTANT == 37:
        t[p] = t[p].replace(A_SECTION_PROC, "## 🔴 QUELQUES CONSEILS", 1)
    elif _MUTANT == 39:
        t[p] = t[p].replace(A_GLOSE, "| PCF85063A | RTC |", 1)
    elif _MUTANT == 40:
        t[p] = _pose_cellule(t[p], re.compile(r"jamais"), A_NOMINAL)
    elif _MUTANT in SANS_TEXTE:
        # ⛔ CEUX-LA NE MUTENT PAS LE TEXTE : leur matiere est une table de la
        #    gate (`CIBLES`, `LISTE_DN434`) ou un chemin de sortie, mutes dans
        #    `main()`. Le texte revient INTACT, et la garde du no-op les
        #    excepte NOMMEMENT.
        return t
    else:
        raise AssertionError("mutant %d declare mais SANS CORPS" % _MUTANT)
    return t


# ═══════════════════════════ LES CONTROLES ═════════════════════════════════

def main():
    global _MUTANT, _TEMOIN
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--mutant", type=int, default=None,
                    help="REPLANTE une faute EN MEMOIRE pour prouver que le "
                         "controle correspondant sait ROUGIR")
    ap.add_argument("--liste-mutants", action="store_true",
                    help="dit ce que chaque mutant replante, et sort")
    ap.add_argument("--temoin-negatif", action="store_true",
                    help="injecte la citation LEGITIME `…-liaison-pc.md` "
                         "§17.2 — homonyme d'un § faux de `…-affichage.md`. "
                         "La gate doit rester VERTE : rougir dessus serait "
                         "un FAUX POSITIF")
    args = ap.parse_args()
    if args.mutant is not None and args.mutant not in MUTANTS:
        sys.exit("MUTANT %d INCONNU : il n'est pas declare. ⛔ Un mutant qui "
                 "n'existe pas ne prouve RIEN — ⛔ ne pas conclure que le "
                 "controle est vert." % args.mutant)
    _MUTANT = args.mutant or 0
    _TEMOIN = args.temoin_negatif

    if args.liste_mutants:
        for n in sorted(MUTANTS):
            print("  %2d  %s" % (n, MUTANTS[n]))
        return 0

    print("=" * 78)
    print("dn6-2 — LA PAGE DE CABLAGE NE PEUT PAS POURRIR EN SILENCE"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else "")
          + ("   [TEMOIN NEGATIF]" if _TEMOIN else ""))
    print("=" * 78)
    print("cible      : %s  +  %s" % (PAGE_REL, README_REL))
    print("⛔ CETTE GATE NE JUGE AUCUNE VALEUR ELECTRIQUE — elle garde qu'une "
          "valeur CITE\n   une mesure qui EXISTE, par la PAIRE (fichier, §).")

    # ── la matiere ─────────────────────────────────────────────────────────
    brut = {}
    for rel in (PAGE_REL, README_REL):
        chemin = os.path.join(RACINE, rel)
        if not os.path.isfile(chemin):
            ctrl(False, "(c0) la cible existe",
                 "⛔ %s est ABSENT — ⛔ pas de trace nue, un KO nomme" % rel)
            return bilan(1, "%s est ABSENT" % rel)
        try:
            with open(chemin, encoding="utf-8") as fh:
                brut[rel] = fh.read()
        except (OSError, UnicodeDecodeError) as e:
            ctrl(False, "(c0) la cible est LISIBLE",
                 "⛔ %s: %s" % (type(e).__name__, str(e)[:80]))
            return bilan(1, "%s est illisible" % rel)

    # 🔴 UN MUTANT QUI MEURT SORTIRAIT EN TRACEBACK, SANS `BILAN` — or « pas
    #    de BILAN » est le discriminant d'une gate MORTE. ⇒ il se rend en KO.
    try:
        textes = muter(brut)
    except Exception as e:                                # noqa: BLE001
        ctrl(False, "(c0) le mutant %d a une CIBLE et un CORPS" % _MUTANT,
             "⛔ %s: %s — la faute est dans le MUTANT, ⛔ pas dans la gate"
             % (type(e).__name__, str(e)[:80]))
        return bilan(1, "le mutant %d n'a pas pu s'appliquer" % _MUTANT)
    # 🔴 UN MUTANT SANS EFFET EST INVISIBLE AU CONTRAT DE LA CAMPAGNE : le
    #    jour ou son ancre litterale bouge dans la page, la gate sort VERTE
    #    et la campagne accuse LA GATE. ⇒ il se declare lui-meme.
    if _MUTANT and _MUTANT not in SANS_TEXTE and textes == brut:
        # 🔴 rc=3, ⛔ PAS rc=1 — ET C'EST MESURE. Le contrat que
        #    `verif_campagne_dn56.py` appelle « sain » est exactement
        #    `rc=1` + `BILAN` + un `[KO ]` : un mutant devenu no-op le
        #    remplissait donc MOT POUR MOT et sortait COMPTE CONFORME, pendant
        #    que le controle qu'il gardait perdait son seul mutant EN SILENCE.
        #    Mesure du 2026-09-07 : re-emballer une phrase de la page sans
        #    changer un mot rend le mutant 12 no-op — et « conforme ».
        #    `3` est le code du lanceur pour **mutant perime** (`run_gates.sh`),
        #    et il ⛔ ne satisfait plus le contrat de la campagne.
        #    ⛔ `verif_campagne_dn56.py` n'est PAS touchee : l'hygiene du
        #    harnais est hors perimetre et n'a aucun porteur vivant.
        ctrl(False, "(c0) le mutant %d a bien un EFFET" % _MUTANT,
             "⛔ SANS EFFET — son ancre litterale a disparu de la cible. "
             "⛔ Ce n'est PAS un controle vert : rc=3, mutant PERIME.")
        return bilan(3, "le mutant %d n'a eu aucun effet" % _MUTANT)

    page, readme = textes[PAGE_REL], textes[README_REL]
    if _TEMOIN:
        page += ("\n\n⚠️ Renvoi de qualification : "
                 "[`…-liaison-pc.md` §17.2]"
                 "(../hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md).\n")

    cibles = {n: tuple(v) for n, v in CIBLES.items()}
    if _MUTANT == 30:
        # ⚠️ LA VICTIME EST **DERIVEE**, ⛔ pas codee en dur : viser le mutant
        #    28 a cesse de marcher le jour ou (c29) a gagne un SECOND gardien
        #    (le mutant 39). Un mutant qui code en dur sa victime se perime
        #    en silence. On cherche donc un controle garde par EXACTEMENT UN
        #    mutant, et on vide CE gardien-la.
        compte = {}
        for _n, _v in cibles.items():
            for _c in _v:
                compte[_c] = compte.get(_c, 0) + 1
        for _n, _v in sorted(cibles.items()):
            if any(compte[_c] == 1 for _c in _v):
                cibles[_n] = ()
                break
    if _MUTANT == 31:
        cibles[31] = cibles[31] + ("c99",)
    if _MUTANT == 33:
        cibles[99] = ("c29",)    # une cible pour un mutant INEXISTANT
    # 🔴 LE MUTANT 32 REECRIT LA LISTE `dn4-34` AU NUMERO NU — c'est la faute
    #    REELLE que (c32) garde : ecrite ainsi, elle attrape les HOMONYMES.
    liste = set(LISTE_DN434)
    if _MUTANT == 32:
        liste |= {(f, TEMOIN_NEGATIF[1]) for f in dispo_hw()}

    # ── (c1) la page existe et n'est pas vide ──────────────────────────────
    print("\n── (c1) LA PAGE EXISTE ET N'EST PAS VIDE ─────────────────────────")
    if not ctrl(bool(page.strip()), "(c1) la page de cablage n'est pas vide",
                "%d caractere(s)" % len(page.strip())):
        return bilan(1, "la page de cablage est VIDE")

    # ── (c2)(c3)(c4) LA PAIRE (fichier, §), DANS LES DEUX SENS ─────────────
    print("\n── (c2)(c3)(c4) CHAQUE § NOMME SON FICHIER, ET LA PAIRE RESOUT ───")
    dispo = fichiers_hw()
    cits = list(RE_CITATION.finditer(page))
    couvert = set()
    for m in cits:
        couvert.update(range(m.start(), m.end()))
    nus = [page[max(0, m.start() - 30):m.start() + 12].replace("\n", " ")
           for m in re.finditer("§", page) if m.start() not in couvert]
    ctrl(not nus, "(c2) aucun § n'est cite SANS son fichier",
         "%d citation(s), toutes appariees" % len(cits) if not nus
         else "⛔ %d § NU(S) — un § nu designe DEUX sections sans rapport : %s"
              % (len(nus), " · ".join(repr(x) for x in nus[:2])))

    cache, paires, introuvables = {}, [], []
    for m in cits:
        f = resout_fichier(m.group(1), dispo)
        num = m.group(2) + (" " + m.group(3).strip() if m.group(3).strip()
                            else "")
        if f is None:
            introuvables.append("%s (jeton ⛔ non resolu)" % m.group(1))
            continue
        if f not in cache:
            cache[f] = sections_de(f)
        if num not in cache[f]:
            introuvables.append("%s §%s" % (f, num))
            continue
        paires.append((f, num))
    ctrl(not introuvables and bool(paires),
         "(c3) chaque paire (fichier, §) EXISTE dans hardware/",
         "%d paire(s), %d fichier(s) lu(s)" % (len(paires), len(cache))
         if not introuvables and paires
         else ("⛔ INTROUVABLE(S) : %s" % " · ".join(sorted(set(introuvables))[:3])
               if introuvables else "⛔ AUCUNE citation — ⛔ pas vert sur du vide"))

    fausses = sorted({"%s §%s" % (f, n) for f, n in paires
                      if (f, n) in liste})
    ctrl(not fausses,
         "(c4) aucune paire citee n'est sur la liste `dn4-34`",
         "%d paire(s) confrontee(s) a %d section(s) fausse(s)"
         % (len(paires), len(liste)) if not fausses
         else "⛔ SECTION(S) NOMMEE(S) FAUSSE(S) : %s — declarer l'ecart et "
              "son porteur (%s)" % (" · ".join(fausses), PORTEUR_DN434))

    # ── (c32) 🔴 LE TEMOIN DE LA PAIRE, JOUE **A CHAQUE PASSE** ────────────
    # 🔴 IL ETAIT DERRIERE `--temoin-negatif`, QUE **RIEN** NE REJOUAIT :
    #    `run_gates.sh` lance la gate SANS argument et `verif_campagne_dn56.py`
    #    ne decouvre que `--liste-mutants`. La propriete CENTRALE de cette
    #    marche — la PAIRE, ⛔ pas le numero nu — n'etait donc gardee que par
    #    une CAPTURE UNIQUE, c'est-a-dire par ce que `dn5-6` et `dn4-47` ont
    #    paye deux fois. ⇒ il vit ici, sous son propre identifiant, comme
    #    `TEMOIN_NOTION` le fait deja pour (c29).
    # ⚠️ IL SE JOUE DANS LES **DEUX SENS** : la paire temoin ⛔ NE DOIT PAS
    #    etre retenue, et son HOMONYME de `…-affichage.md` DOIT l'etre. Un
    #    seul sens laisserait passer une regle qui ne retient JAMAIS rien.
    f_neg, s_neg = TEMOIN_NEGATIF
    neg_pris = (f_neg, s_neg) in liste
    pos_pris = (FICHIER_LISTE_DN434, s_neg) in liste
    neg_existe = s_neg in sections_de(f_neg)
    ctrl(neg_existe and not neg_pris and pos_pris,
         "(c32) la regle de (c4) distingue les HOMONYMES",
         "temoin `…%s` §%s : existe, ⛔ NON retenu ; son homonyme "
         "`…-affichage.md` : retenu" % (f_neg[-14:], s_neg)
         if neg_existe and not neg_pris and pos_pris
         else ("⛔ LE TEMOIN N'EXISTE PLUS dans hardware/" if not neg_existe
               else ("⛔ FAUX POSITIF — la regle attrape l'homonyme LEGITIME : "
                     "elle est ecrite au NUMERO, ⛔ pas a la PAIRE"
                     if neg_pris else
                     "⛔ LA REGLE NE RETIENT RIEN — meme le § FAUX passe")))

    # ── (c5)…(c9) CHAQUE VALEUR PUBLIEE CITE SA MESURE ─────────────────────
    print("\n── (c5)…(c9) CHAQUE VALEUR PUBLIEE CITE SA MESURE ────────────────")
    lignes_citees = [l for l in page.split("\n") if RE_CITATION.search(l)]
    VALEURS = (("c5", "SCL = GPIO7", ("GPIO7",)),
               ("c6", "SDA = GPIO15", ("GPIO15",)),
               ("c7", "l'alimentation 3V3 / GND", ("3V3", "GND")),
               ("c8", "BME680 a l'adresse 0x77", ("0x77",)),
               ("c9", "BH1750 a l'adresse 0x23", ("0x23",)))
    for cid, lib, jetons in VALEURS:
        absents = [j for j in jetons if j not in page]
        nues = [j for j in jetons
                if j not in absents
                and not any(j in l for l in lignes_citees)]
        ctrl(not absents and not nues, "(%s) %s cite sa mesure" % (cid, lib),
             "publiee et citee" if not absents and not nues
             else ("⛔ ABSENTE de la page : %s" % " · ".join(absents)
                   if absents else
                   "⛔ NUE — publiee SANS (fichier, §) : %s" % " · ".join(nues)))

    # ── (c10)(c11) L'AVERTISSEMENT SUR LA SOURCE TIERCE, ET SA DATE ────────
    print("\n── (c10)(c11) L'AVERTISSEMENT D'INVERSION, ET IL EST DATE ────────")
    fenetres = []
    for m in re.finditer(r"invers|permut", page, re.I):
        f = page[max(0, m.start() - 500):m.start() + 500]
        if "SDA" in f and "SCL" in f and re.search(
                r"source tierce|spotpear|wiki|constructeur|autre source",
                f, re.I):
            fenetres.append(f)
    ctrl(bool(fenetres),
         "(c10) la page porte l'inversion `SDA`/`SCL` de la source",
         "%d fenetre(s) d'avertissement" % len(fenetres) if fenetres
         else "⛔ AUCUNE — un lecteur qui croise une autre source ⛔ ne sait "
              "plus laquelle est mesuree")
    datees = [f for f in fenetres if RE_DATE.search(f)]
    ctrl(bool(datees), "(c11) cet avertissement porte SA DATE",
         "%s" % RE_DATE.search(datees[0]).group(0) if datees
         else "⛔ SANS DATE — un releve sans sa date ⛔ ne se re-confronte pas")

    # ── (c12)(c13) LES DEUX POINTS D'ACCES, ET LEUR PIEGE ──────────────────
    print("\n── (c12)(c13) LES DEUX ACCES AU BUS PORTENT CHACUN SON PIEGE ─────")
    paras = paragraphes(page)
    jst = [p for p in paras
           if re.search(r"embase", p, re.I) and "UART" in p
           and re.search(r"adjacent|identique|jumel", p, re.I)]
    ctrl(bool(jst), "(c12) l'embase JST porte son piege (jumelle UART)",
         "%d paragraphe(s)" % len(jst) if jst
         else "⛔ ABSENT — se tromper d'embase ALIMENTE correctement et laisse "
              "le capteur MUET, ⛔ sans rien signaler")
    rang = [p for p in paras
            if "RXD" in p and "TXD" in p and "SCL" in p and "SDA" in p
            and re.search(r"derri|muet|signal", p, re.I)]
    ctrl(bool(rang), "(c13) le header 2x12 porte son piege (rangee A)",
         "%d paragraphe(s)" % len(rang) if rang
         else "⛔ ABSENT — `RXD`/`TXD` sont EXACTEMENT derriere `SCL`/`SDA`, "
              "et c'est le jumeau du piege JST a 2,54 mm")

    # ── (c34)(c35)(c36) LES TROIS FAITS QUE LA PAGE DECLARE DECISIFS ──────
    # 🔴 LES TROIS POUVAIENT ETRE SUPPRIMES DE LA PAGE SANS QUE LA GATE BOUGE
    #    (mesure du 2026-09-07). Une page de cablage qui perd « le scan qui ne
    #    voit pas les temoins est casse », « `ADDR` va a la masse » ou « ⛔ ne
    #    pose pas les fils dans l'ordre » envoie quelqu'un souder de travers.
    print("\n── (c34)(c35)(c36) LES TROIS FAITS DECISIFS SONT ECRITS ──────────")
    tem = [x for x in paras
           if "0x20" in x and "0x5D" in x
           and re.search(r"instrument cass", x, re.I)]
    ctrl(bool(tem), "(c34) les DEUX temoins positifs et leur portee",
         "%d paragraphe(s)" % len(tem) if tem
         else "⛔ ABSENT — sans eux, un scan casse rend un verdict recevable "
              "sur un composant neuf")
    addr = [x for x in paras
            if "ADDR" in x and "GND" in x and re.search(r"soud", x, re.I)
            and re.search(r"s[ée]lection|ind[ée]fini", x, re.I)]
    ctrl(bool(addr), "(c35) `ADDR` du BH1750 va a la MASSE",
         "%d paragraphe(s)" % len(addr) if addr
         else "⛔ ABSENT — `ADDR` est une ENTREE DE SELECTION : flottant, "
              "l'adresse est INDEFINIE")
    mir = [x for x in paras
           if re.search(r"premier avec premier|miroir", x, re.I)
           and re.search(r"invers|croise", x, re.I)
           and re.search(r"alimentation", x, re.I)]
    ctrl(bool(mir), "(c36) le PIEGE DU MIROIR est ecrit",
         "%d paragraphe(s)" % len(mir) if mir
         else "⛔ ABSENT — poser les fils « dans l'ordre » INVERSE "
              "l'alimentation et CROISE `SDA`/`SCL`")

    # ── (c37) LA SECTION D'ANCRAGE DE (c18)(c19) EXISTE ───────────────────
    # 🔴 (c18)/(c19) SELECTIONNENT LEUR MATIERE DANS CETTE SECTION. Sans ce
    #    controle, la RENOMMER faisait rougir les deux avec des messages sur
    #    `0x76`/`0x77` : un VRAI rouge pour un FAUX motif, c'est-a-dire la
    #    ligne qu'un operateur lit envoyee chercher au mauvais endroit.
    print("\n── (c37) LA SECTION D'ANCRAGE DE LA PROCEDURE EXISTE ─────────────")
    proc = ""
    for corps in re.split(r"\n(?=## )", page):
        if re.search(r"PROC[EÉ]DURE", corps.split("\n")[0], re.I):
            proc = corps
    ctrl(bool(proc), "(c37) la section d'ancrage de la procedure existe",
         "%d caractere(s)" % len(proc) if proc
         else "⛔ AUCUNE section `## …PROCEDURE…` — (c18) et (c19) n'ont plus "
              "de matiere, et ⛔ ce n'est PAS un defaut de `0x76`")

    # ⚠️ LE MUTANT 38 NE TOUCHE PAS AU DOCUMENT : il replante une SORTIE
    #    ANTICIPEE NON DECLAREE — la seule forme que prend, dans le code, le
    #    defaut que (z) garde. Sans lui, (z) n'etait atteint par AUCUN chemin :
    #    le SUPPRIMER laissait la passe saine, le temoin et tous les mutants
    #    VERTS (mesure du 2026-09-07). ⛔ Il ne debranche aucune garde : il
    #    fait exactement ce qu'une future refonte maladroite ferait.
    if _MUTANT == 38:
        return bilan(0)

    # ── (c14)…(c20) LA PROCEDURE DE VERIFICATION ───────────────────────────
    print("\n── (c14)…(c20) LA PROCEDURE DIT QUOI CONCLURE ────────────────────")
    # ⚠️ LE DETAIL SE DERIVE DU VERDICT, ⛔ PAS D'UNE DE SES MOITIES. Mesure
    #    du 2026-09-07 : sous `--mutant 13` la gate imprimait
    #    `[KO ] (c14) … \`n/5\` publie` — la SEULE ligne qu'un operateur lit
    #    pour savoir POURQUOI c'est rouge affirmait que la chose est publiee.
    passes = bool(re.search(r"plusieurs passes|re-sond\w*\s+5\s+fois",
                            page, re.I))
    ratio = "n/5" in page
    ctrl(passes and ratio, "(c14) la procedure prescrit PLUSIEURS passes",
         "plusieurs passes prescrites, `n/5` publie" if passes and ratio
         else "⛔ %s — un scan a UNE passe FABRIQUE des faux positifs"
              % ("`n/5` n'est PAS publie" if passes
                 else ("PLUSIEURS passes ne sont PAS prescrites"
                       if ratio else
                       "⛔ ni plusieurs passes prescrites ⛔ ni `n/5` publie")))
    mp = re.search(r"croire sur parole", page, re.I)
    mf = re.search(r"faux positif prouv", page, re.I)
    nuance = bool(mp and mf and abs(mf.start() - mp.start()) < 200
                  and "⛔" in page[min(mp.start(), mf.start()):
                                  max(mp.end(), mf.end())])
    ctrl(nuance, "(c15) un desaccord n'est PAS un verdict",
         "« a ne pas croire sur parole » ⛔ pas « prouve »" if nuance
         else "⛔ LA NUANCE MANQUE — `n/5 < 5` veut dire « a ne pas croire "
              "sur parole », ⛔ pas « faux positif prouve »")
    dep = [p for p in paras
           if re.search(r"tranche|départage|departage", p, re.I)
           and re.search(r"registre", p, re.I)]
    ctrl(bool(dep), "(c16) le departage est la LECTURE DE REGISTRE",
         "%d paragraphe(s)" % len(dep) if dep
         else "⛔ ABSENT — le scan DECOUVRE, seule une transaction de DONNEE "
              "qualifie")
    tmo = any(re.search(r"pas une absence", page[m.start():m.start() + 140],
                        re.I)
              for m in re.finditer(r"timeout", page, re.I))
    ctrl(tmo, "(c17) un TIMEOUT n'est pas une absence",
         "ecrit" if tmo
         else "⛔ ABSENT — une adresse JAMAIS SONDEE, comptee nulle part, "
              "dans une liste qui se lit comme exhaustive")
    p76 = [x for x in paragraphes(proc)
           if "0x76" in x and re.search(r"faux positif", x, re.I)
           and re.search(r"mesur", x, re.I)]
    ctrl(bool(p76), "(c18) `0x76` est nomme FAUX POSITIF MESURE",
         "%d paragraphe(s) dans la procedure" % len(p76) if p76
         else ("⛔ SECTION D'ANCRAGE ABSENTE — voir (c37), ⛔ ce n'est pas un "
               "defaut de `0x76`" if not proc else
               "⛔ ABSENT — il a ete rendu par un scan alors qu'AUCUN capteur "
               "n'etait branche"))
    p77 = [x for x in paragraphes(proc) if "0x76" in x and "0x77" in x]
    ctrl(bool(p77), "(c19) la fenetre `0x76` renvoie a `0x77`",
         "%d paragraphe(s)" % len(p77) if p77
         else ("⛔ SECTION D'ANCRAGE ABSENTE — voir (c37)" if not proc else
               "⛔ ABSENT — sans `0x77`, le lecteur conclut « le capteur "
               "repond » sur un faux positif"))
    coup = [p for p in paras
            if re.search(r"alimentation", p, re.I)
            and re.search(r"rescann", p, re.I)
            and re.search(r"débranch|debranch", p, re.I)]
    ctrl(bool(coup), "(c20) bouger ⇒ COUPER L'ALIM ⇒ rescanner",
         "%d paragraphe(s)" % len(coup) if coup
         else "⛔ ABSENT — « bouger → scanner » ⛔ ne peut PAS converger : "
              "l'alimentation fantome garde le capteur bavard")

    # ── (c21)…(c24) LES BLOCS `TESTED` ─────────────────────────────────────
    print("\n── (c21)…(c24) UN `TESTED` PAR PALIER, ET IL DIT LES TROUS ───────")
    blocs = blocs_tested(page)
    par_palier = {}
    for titre, corps in blocs:
        q = palier_du_titre(titre)
        if q:
            par_palier.setdefault(q, []).append((titre, corps))
    manque = [q for q in PALIERS if len(par_palier.get(q, [])) != 1]
    ctrl(not manque, "(c21) chaque palier a UN bloc `TESTED`",
         "%d bloc(s) pour %d palier(s)" % (len(blocs), len(PALIERS))
         if not manque
         else "⛔ %d PALIER(S) SANS bloc UNIQUE : %s — ⛔ un synonyme n'est "
              "pas un nom" % (len(manque), " · ".join(manque)))
    sans_duree, sans_sha, muets = [], [], []
    for q, vs in sorted(par_palier.items()):
        for titre, corps in vs:
            v = ligne_de_bloc(corps, re.compile(r"combien de temps|dur[ée]e"))
            if not (v and duree_ecrite(v)):
                sans_duree.append(q)
            v = ligne_de_bloc(corps, re.compile(r"sha"))
            # ⚠️ ⛔ AUCUNE EXIGENCE DE LETTRE HEXA : une abreviation de commit
            #    TOUT EN CHIFFRES est parfaitement legitime, et l'exiger
            #    ferait rougir une page JUSTE. C'est la FORME (7 a 40 chiffres
            #    hexa entre accents graves) qui est gardee, ⛔ pas le hasard
            #    d'un `a`..`f`.
            if not (v and RE_SHA.findall(v)):
                sans_sha.append(q)
            v = ligne_de_bloc(corps, re.compile(r"jamais"))
            if not (v and len(v.strip(" —-–*`")) >= MIN_TESTED_TROU):
                muets.append("%s (creux)" % q)
            elif not RE_NEGATION_TESTED.search(v):
                muets.append("%s (⛔ sans negation de test)" % q)
    ctrl(not sans_duree and bool(blocs),
         "(c22) chaque `TESTED` dit COMBIEN DE TEMPS",
         "%d bloc(s) chronometre(s)" % len(blocs)
         if not sans_duree and blocs
         else "⛔ SANS DUREE : %s" % (" · ".join(sans_duree) or "aucun bloc"))
    ctrl(not sans_sha and bool(blocs),
         "(c23) chaque `TESTED` dit SUR QUEL SHA",
         "%d bloc(s) ancre(s) sur un binaire" % len(blocs)
         if not sans_sha and blocs
         else "⛔ SANS SHA : %s" % (" · ".join(sans_sha) or "aucun bloc"))
    ctrl(not muets and bool(blocs),
         "(c24) chaque `TESTED` ecrit ce qui n'a JAMAIS tourne",
         "%d bloc(s), trous ecrits" % len(blocs) if not muets and blocs
         else "⛔ MUET(S) : %s — ⛔ ni le silence ⛔ ni « tout est nominal » "
              "ne sont un `TESTED`" % (" · ".join(muets) or "aucun bloc"))

    # ── (c25)(c26) LA PAGE EST DECOUVRABLE ─────────────────────────────────
    print("\n── (c25)(c26) LE README MENE AUX DEUX PAGES ──────────────────────")
    # 🔴 CE CONTROLE VIT ICI, ⛔ PAS DANS `verif_paliers_dn441.py`. Cette
    #    gate-la ne lit QUE `README.md` et pourrait l'accueillir — mais elle
    #    appartient a `dn4-41`, qui est `in-progress` : y ajouter un controle,
    #    c'est modifier l'instrument d'une marche EN VOL (`NFR6.5`). Le cout
    #    est ECRIT : deux gates lisent le README, et c'est assume.
    liens = set(re.findall(r"\]\(([^)]+)\)", readme))
    for cid, cible in (("c25", PAGE_REL), ("c26", "docs/bom.md")):
        vu = cible in liens
        ctrl(vu, "(%s) le README lie `%s`" % (cid, cible),
             "lien present" if vu
             else "⛔ ABSENT — sans lien, la page est INVISIBLE, et ⛔ aucune "
                  "gate ne gardait cette decouvrabilite")

    # ── (c27)(c28) LES PHOTOS CITEES EXISTENT ──────────────────────────────
    print("\n── (c27)(c28) TOUTE PHOTO CITEE EXISTE SUR LE DISQUE ─────────────")
    # ⛔ CETTE GATE NE TOUCHE AUCUNE PHOTO : leur poids est `dn6-3`.
    photos = re.findall(r"\]\((cablage/[^)]+)\)", page)
    absentes = [c for c in photos
                if not os.path.isfile(os.path.join(RACINE, "docs", c))]
    ctrl(not absentes, "(c27) toute photo citee existe",
         "%d photo(s) citee(s)" % len(photos) if not absentes
         else "⛔ %d LIEN(S) MORT(S) : %s" % (len(absentes),
                                             " · ".join(absentes[:2])))
    ctrl(bool(photos), "(c28) la page MONTRE au moins une photo",
         "%d citation(s) de `%s/`" % (len(photos), DOSSIER_PHOTOS) if photos
         else "⛔ AUCUNE — ⛔ un vide n'est pas une absence de defaut")

    # ── (c29) AUTOPORTANCE — LA DEFINITION, ⛔ PAS L'OCCURRENCE ─────────────
    print("\n── (c29) TOUTE NOTION A NOMMER EST DEFINIE DANS LE CLONE ─────────")
    prose = {PAGE_REL: page, README_REL: readme}
    for extra in ("docs/bom.md",):
        try:
            with open(os.path.join(RACINE, extra), encoding="utf-8") as fh:
                prose[extra] = fh.read()
        except OSError:
            pass
    notions = set(RE_PALIER_CITE.findall(page))
    for ent, corps in tables(page):
        k_a, k_c = colonne(ent, "adresse"), colonne(ent, "composant")
        if k_a is None or k_c is None:
            continue
        for l in corps:
            c = cellules(l)
            if k_c < len(c) and c[k_c].strip(" —-–*`"):
                notions.add(c[k_c].strip(" —-–*`").split()[0])
    orphelines = sorted(n for n in notions if not glose(n, prose))
    temoin_ok = not glose(TEMOIN_NOTION, prose)
    ctrl(not orphelines and temoin_ok and bool(notions),
         "(c29) chaque notion a nommer est DEFINIE dans le clone",
         "%d notion(s), temoin negatif « %s » a 0" % (len(notions),
                                                      TEMOIN_NOTION)
         if not orphelines and temoin_ok and notions
         else ("⛔ SANS DEFINITION : %s" % " · ".join(orphelines[:3])
               if orphelines else
               ("⛔ LE TEMOIN NEGATIF EST DEFINI — l'instrument compte des "
                "OCCURRENCES, ⛔ pas des DEFINITIONS" if not temoin_ok
                else "⛔ AUCUNE notion — ⛔ pas vert sur du vide")))

    # ── (c30)(c31) LA RECIPROQUE, MECANIQUE ────────────────────────────────
    print("\n── (c30)(c31) AUCUN CONTROLE N'EST GARDE PAR ZERO MUTANT ─────────")
    # 🔴 LE RISQUE HERITE DE `verif_bom_dn61.py`, FERME ICI. « N mutants, N
    #    vus rougir » prouve `mutant ⇒ rouge`, ⛔ JAMAIS `controle ⇒ couvert`.
    # 🔴 `"z"` EN FAIT PARTIE, ET C'EST UNE MESURE : (z) — « tout controle
    #    prevu est EMIS » — n'etait atteint par AUCUN chemin. Le supprimer
    #    entierement laissait tout vert, et (c30) ⛔ ne pouvait pas le voir
    #    parce que `reels` est calcule AVANT que (z) soit emis (il ne l'est
    #    que dans `bilan()`, et seulement en cas de defaut). ⇒ il est nomme
    #    ici, et le mutant 38 le fait rougir.
    reels = set(ids_emis) | {"c30", "c31", "c33", "z"}
    vises = set()
    for v in cibles.values():
        vises.update(v)
    nus_ctrl = sorted(reels - vises, key=lambda s: (len(s), s))
    ctrl(not nus_ctrl, "(c30) chaque controle est vise par >= 1 mutant",
         "%d controle(s), %d cible(s) declaree(s)" % (len(reels), len(vises))
         if not nus_ctrl
         else "⛔ %d CONTROLE(S) GARDE(S) PAR RIEN : %s"
              % (len(nus_ctrl), " · ".join(nus_ctrl)))
    # ── (c33) `CIBLES` ET `MUTANTS` SE CORRESPONDENT, DANS LES DEUX SENS ──
    # 🔴 MESURE DU 2026-09-07 : `CIBLES[99] = ("c29",)` pose sans `CIBLES[28]`
    #    rendait toujours `31 OK, 0 KO`. (c30) voyait c29 « garde », (c31)
    #    voyait c29 « reel » — et personne ne voyait que le gardien nomme
    #    N'EXISTE PAS. Les deux tables sont confrontees CLE A CLE.
    orphelins = sorted(set(cibles) - set(MUTANTS))
    sans_cible = sorted(set(MUTANTS) - set(cibles))
    ctrl(not orphelins and not sans_cible,
         "(c33) `CIBLES` et `MUTANTS` se correspondent",
         "%d mutant(s), %d cible(s), cle a cle" % (len(MUTANTS), len(cibles))
         if not orphelins and not sans_cible
         else "⛔ cible(s) SANS mutant : %s · mutant(s) SANS cible : %s"
              % (orphelins or "—", sans_cible or "—"))

    perimees = sorted(vises - reels, key=lambda s: (len(s), s))
    ctrl(not perimees, "(c31) chaque cible de mutant est un controle REEL",
         "%d cible(s) confrontee(s)" % len(vises) if not perimees
         else "⛔ %d CIBLE(S) PERIMEE(S) : %s — un mutant qui vise un "
              "controle inexistant ⛔ ne garde rien"
              % (len(perimees), " · ".join(perimees)))

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : elle ne dit RIEN de la")
    print("   JUSTESSE d'un brochage ni d'une adresse. Une valeur fausse mais")
    print("   citee la laisse VERTE. La serigraphie et la mesure font foi.")
    print("⛔ Ni que le mutant rougisse BIEN le controle qu'il declare : ca,")
    print("   c'est `mesures/dn6-2/T2`, qui relit a colonne fixe les lignes de")
    print("   signalement de defaut. ⚠️ Leur jeton n'est PAS ecrit ici : ce")
    print("   depot a deja paye « citer le jeton, c'est poser le fait ».")
    return bilan(1 if ko_total[0] else 0)


if __name__ == "__main__":
    sys.exit(main())

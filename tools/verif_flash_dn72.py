#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn7-2 — LA CARTE SE FLASHE, CE QUI COINCE SE COMPREND, ET ON SAIT D'OU CA VIENT.

======================= CE QUE CETTE GATE GARDE, ET POURQUOI ================

`installeur/charge/` porte **quatre images binaires** qu'une page ecrit sur la
carte de quelqu'un, et un manifeste qui dit ou chacune se pose. Cinq promesses y
sont ecrites, et chacune est du genre a pourrir en silence :

  1. **LA VERSION ANNONCEE EST CELLE DU BINAIRE SERVI.** ⛔ Pas une chaine
     recopiee a cote : le champ `version` de `esp_app_desc_t`, LU dans
     `desknode.bin`. Le prototype de flash du 2026-08-31 annoncait
     `0.1.0-beta-essai` — la valeur de son BANC D'ESSAI — sur des images que
     plus personne ne savait dater. ⇒ ici, les deux se CONFRONTENT.
  2. **LES QUATRE MORCEAUX, AUX OFFSETS DE LA SOURCE DE VERITE.** ⛔ Pas quatre
     nombres recopies : ceux de `flasher_args.json`, que l'IDF ecrit lui-meme,
     et a defaut de build dans le clone, ceux de la table de partitions.
     ⛔ Et SANS binaire fusionne.
  3. **LA CHARGE EST ENTIERE.** L'asset porte une bande-annonce d'integrite —
     magie, longueur, CRC32 — que le firmware relit deja au demarrage. La
     reverifier ICI attrape une image tronquee AVANT qu'elle soit servie.
  4. **LA PAGE DIT CE QUI COINCE, AVEC LES MOTS QUI SONT VRAIS.** Le nom REEL
     du port (dans ses deux formes), les DEUX gestes de selection, la
     recuperation MESUREE, le refus des pilotes reclames a tort, et
     l'avertissement hors Windows — AVANT le flash, ⛔ pas apres.
  5. **ON SAIT D'OU CA VIENT, ET ON SAIT CE QUE PERSONNE NE VERIFIE.** La
     provenance de ces images n'est mecanisee par RIEN, et `PROVENANCE.md` doit
     l'ECRIRE, avec un porteur NOMME pour chacun des deux manques.

── CE QU'ELLE NE PROUVE ⛔ PAS, ECRIT PLUTOT QUE TU ─────────────────────────

⛔ Elle ne flashe RIEN. Elle n'ouvre aucun port serie, ⛔ n'appelle aucun
   PowerShell, ⛔ ne demande aucune carte. Que le dialogue de port aille au bout
   est un DIALOGUE NATIF DU NAVIGATEUR, qu'aucun drapeau de ligne de commande ne
   pilote : ca se joue EN SEANCE CARTE, avec une main humaine, et ca vit sous
   `mesures/dn7-2/`.
⛔ Elle ne dit pas que le firmware FONCTIONNE. Elle dit que ce qui est servi est
   ce qui est annonce, entier, et aux bons endroits.

Emploi :
    python3 tools/verif_flash_dn72.py
    python3 tools/verif_flash_dn72.py --liste-mutants
    python3 tools/verif_flash_dn72.py --mutant <n>

Sortie : 0 si tout passe · 1 sur un vrai defaut · 2 sur un mutant inconnu ·
         3 si le mutant demande est PERIME (il n'a rien change).
"""

import argparse
import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DOSSIER = "installeur"
CHARGE = "installeur/charge"
MANIFESTE = "installeur/charge/manifest.json"
PROVENANCE = "installeur/charge/PROVENANCE.md"
PY = "installeur/dn_installeur.py"
PAGE = "installeur/index.html"
BAT = "installeur/DeskNode-installeur.bat"
TIERS = "THIRD-PARTY.md"
ATTRIBUTS = ".gitattributes"
LISEZMOI = "README.md"
PARTITIONS = "firmware/desknode/partitions.csv"
# ⚠️ `build/` EST GITIGNORE : ce fichier peut TRES BIEN ne pas exister dans un
#    clone neuf, et c'est le cas NORMAL. La gate a donc DEUX sources de verite,
#    et elle DIT laquelle elle a employee — ⛔ elle ne se tait pas et ⛔ elle ne
#    devient pas aveugle.
FLASHER_ARGS = "firmware/desknode/build/flasher_args.json"

# Les quatre images, DANS L'ORDRE DES OFFSETS CROISSANTS.
IMAGES = ("bootloader.bin", "partition-table.bin", "desknode.bin",
          "living_pcb_v0.bin")
CINQ = tuple("%s/%s" % (CHARGE, n) for n in IMAGES) + (MANIFESTE,)

JOURNAL = "CHANGELOG.md"
ROADMAP = "docs/roadmap.md"
FIXES = (MANIFESTE, PROVENANCE, PY, PAGE, BAT, TIERS, ATTRIBUTS, LISEZMOI,
         JOURNAL, ROADMAP, PARTITIONS)

# ── L'EN-TETE `esp_app_desc_t`, RELUE DANS LE BINAIRE ─────────────────────
# Structure ESP-IDF, a l'offset `0x20` de l'image applicative :
#     +0   4 o  magie `0xABCD5432`
#     +4   4 o  secure_version
#     +8   8 o  reserve
#     +16 32 o  version[32]        ⇒ offset absolu `0x30`
#     +48 32 o  project_name[32]   ⇒ offset absolu `0x50`
# ⚠️ Le champ `version` vient de `git describe`, EVALUE AU DERNIER *configure*
#    — ⛔ pas au dernier *build*. C'est le piege qui a fait ecrire « la carte
#    porte telle revision » pendant trois jours : sans un `reconfigure`
#    prealable, l'etiquette nomme le commit PRECEDENT. Cette gate ne peut pas
#    voir ce piege ; elle voit l'ECART entre le manifeste et le binaire, qui est
#    l'autre moitie du meme probleme.
APP_DESC_OFFSET = 0x20
APP_DESC_MAGIE = 0xABCD5432
APP_DESC_VERSION = 0x30
APP_DESC_PROJET = 0x50

# ── LA BANDE-ANNONCE D'INTEGRITE DE L'ASSET ───────────────────────────────
# Ecrite par `tools/gen_living_pcb.py`, relue par
# `firmware/desknode/main/dn_asset.c` : magie 8 o + longueur uint32 LE +
# CRC32 zlib uint32 LE. ⇒ 614 416 o pour 614 400 o utiles, ⛔ pas 614 400.
ASSET_MAGIE = b"DNASSET1"
ASSET_QUEUE = 16
ASSET_FICHIER = "living_pcb_v0.bin"

# 🔴 LA VALEUR DU BANC D'ESSAI. Elle est INTERDITE, nommement, parce que c'est
#    elle qui a ete publiee — `CHANGELOG.md` revendique « Browser flashing works
#    end to end » sur une charge qui la portait. ⛔ Une gate qui se contenterait
#    de « la version n'est pas vide » l'aurait laissee passer.
VERSION_DU_BANC = "0.1.0-beta-essai"

CHIP_ATTENDU = "ESP32-S3"

# Ce qui signe un binaire FUSIONNE, la ou on veut quatre morceaux separes.
JETONS_FUSION = ("merge_bin", "merge-bin", "merged.bin", "merged_flash")

# Le vocabulaire de l'elevation. ⛔ IL NE VIT QUE DANS CETTE GATE : le citer
# dans les fichiers gardes les ferait rougir sur du contenu JUSTE.
# 🔴 DES MOTIFS, ⛔ PAS DES CHAINES : la lecon est de `dn7-1`, ou une liste de
#    chaines litterales ratait `["powershell", "-Verb", "RunAs"]`, la forme la
#    plus naturelle en Python — les deux jetons y sont SEPARES par une virgule
#    et un guillemet, et le mutant qui l'a montre etait sorti VERT.
MOTIFS_ELEVATION = (
    ("runas", re.compile(r"\brunas\b", re.I)),
    ("RunAsAdministrator", re.compile(r"runasadministrator", re.I)),
    ("RunLevel Highest", re.compile(r"runlevel\s*=?\s*['\"]?highest", re.I)),
    ("requestedExecutionLevel", re.compile(r"requestedexecutionlevel", re.I)),
    ("requireAdministrator", re.compile(r"requireadministrator", re.I)),
    ("Start-Process -Verb", re.compile(r"start-process[^\n]{0,80}-verb", re.I)),
)

# Un porteur A NOMMER n'est ⛔ PAS un porteur — lecon de `dn6-4`, rejouee ici.
REFUS_PORTEUR = ("a nommer", "à nommer", "tbd", "a definir", "à définir",
                 "a preciser", "à préciser", "inconnu", "?", "-", "—", "")

# ── CE QUE LA PAGE DOIT DIRE, ET QUI SE MESURE ────────────────────────────
# 🔴 LE NOM DU PORT SE DIT DANS SES **DEUX** FORMES, ET C'EST UNE MESURE.
#    Sur la tour, le 2026-09-08, `Get-PnpDevice` rend pour `MI_00` un
#    `FriendlyName` LOCALISE (« Peripherique serie USB (COM3) ») tandis que la
#    chaine PRODUIT de la puce est « USB JTAG/serial debug unit ». Le cadrage
#    n'ecrivait que la seconde. ⇒ la page nomme LES DEUX, et ⛔ jamais
#    « DeskNode », qui n'est le nom de rien cote systeme.
FORME_WINDOWS = "Périphérique série USB"
FORME_PUCE = "USB JTAG/serial debug unit"
# Les DEUX gestes du selecteur de port : sans le second, on sort sur un ecran
# qui n'explique pas qu'il manquait un clic.
GESTE_1 = "cliquer la ligne"
GESTE_2 = "Se connecter"
ECHEC_SELECTION = "No port selected"
# 🔴 LA RECUPERATION, TELLE QU'ELLE EST **ECRITE ET MESUREE** DANS LE DEPOT :
#    `README.md` ne connait qu'un geste, « BOOT maintenu + RESET ». La formule
#    du cadrage — « BOOT maintenu pendant le branchement » — n'est ecrite NULLE
#    PART et n'a jamais ete mesuree. ⇒ la page ecrit ce qui est VRAI, et l'ecart
#    entre les deux SE DIT au lieu de se recopier.
RECUP_BOOT = "BOOT"
RECUP_RESET = "RESET"
# Les pilotes que le dialogue de secours reclame A TORT sur un USB natif.
PILOTES_INUTILES = ("CP2102", "CH340", "CH342")
USB_NATIF = "303A:1001"
# L'avertissement hors Windows, DIT AVANT le flash.
ANCRE_HORS_WINDOWS = "etat-hors-windows"
ANCRE_CDN = "etat-cdn"
ANCRE_PORT_TENU = "etat-port-tenu"
ANCRE_PILOTES = "etat-pilotes"

# ── LE BRANCHEMENT D'ESP WEB TOOLS, EPINGLE ───────────────────────────────
# ⚠️ MESURE LE 2026-09-08 : `unpkg.com/esp-web-tools@10/…` rend un **302** vers
#    `/esp-web-tools@10.4.0/…`. Une plage epingle donc RIEN : le code qui ECRIT
#    SUR LA CARTE de quelqu'un changerait en silence a la prochaine publication
#    amont. ⇒ on exige une version EXACTE, des deux cotes.
# 🔴 LA RECHERCHE EST BORNEE A L'ATTRIBUT `src` DU MODULE, ⛔ PAS AU FICHIER
#    ENTIER — ET C'EST UNE CORRECTION PAYEE SUR PLACE. La 1re redaction
#    cherchait la forme de PLAGE PARTOUT dans la page : elle a rougi sur le
#    COMMENTAIRE qui explique justement pourquoi la plage est interdite, en
#    citant la mesure du 302. ⛔ Documenter un piege ne doit pas replanter le
#    piege — et surtout, ce qui compte n'est pas ce que la prose CITE, c'est ce
#    que le navigateur CHARGE. ⇒ on lit l'URL, ⛔ pas le texte autour.
RE_SRC_MODULE = re.compile(
    r"<script[^>]*\bsrc\s*=\s*[\"']([^\"']*esp-web-tools[^\"']*)[\"']", re.I)
RE_EWT_PAGE = re.compile(r"esp-web-tools@(\d+\.\d+\.\d+)")
RE_EWT_TIERS = re.compile(r"esp-web-tools@(\d+\.\d+\.\d+)")
RE_EWT_PLAGE = re.compile(r"esp-web-tools@(\d+)(?![.\d])")
# La forme sous laquelle la PROSE publie le meme numero : « ESP Web Tools
# epingle `10.4.0` », « pinned to `10.4.0` ».
# ⚠️ LE MOTIF EST **BORNE AU VOISINAGE DU NOM**, ⛔ pas au fichier entier — et
#    ce n'est pas de la prudence : `THIRD-PARTY.md` porte NEUF autres versions
#    entre accents graves (LVGL, les composants geres…). Un motif qui prendrait
#    tout numero entre accents graves ferait rougir cette gate sur une version
#    qui n'a RIEN a voir, le jour ou quelqu'un en cite une dans le `README.md`.
#    ⇒ on ne compare que ce qui suit le NOM du composant, a 120 caracteres.
RE_VERSION_EWT = re.compile(
    r"ESP Web Tools.{0,120}?`(\d+\.\d+\.\d+)`", re.S)
# L'element lui-meme, ⛔ pas son nom cite dans un commentaire : c'est sa
# POSITION dans le document qui decide de ce qui vient « avant le flash ».
ANCRE_ELEMENT = "<esp-web-install-button "

# La table de `PROVENANCE.md` : `| `fichier` | offset | taille | sha |`
RE_PROV_LIGNE = re.compile(
    r"^\|\s*`([^`]+\.bin)`\s*\|\s*`(\d+)`\s*\|\s*`(\d+)`\s*\|\s*`([0-9a-f]{64})`\s*\|",
    re.M)
# La table de partitions : `nom, type, soustype, offset, taille,`
RE_PARTITION = re.compile(
    r"^\s*([a-z_0-9]+)\s*,\s*([a-z]+)\s*,\s*([^,]+),\s*(0x[0-9a-fA-F]+)\s*,", re.M)

LARGEUR_LIBELLE = 58

ok_total = [0]
ko_total = [0]
ids_emis = []

MUTANTS = {}                      # ⛔ AU NIVEAU MODULE — sinon `--liste-mutants`
CIBLES = {}                       # ⛔ AU NIVEAU MODULE — matiere de (c24)

MUTANTS[1] = ("sort `desknode.bin` de l'arbre suivi ⇒ une charge que le "
              "cloneur n'aura pas, et rien ne le dirait")
CIBLES[1] = ("c1",)
MUTANTS[2] = ("vide le manifeste ⇒ un JSON illisible la ou la page attend "
              "quatre offsets")
CIBLES[2] = ("c2",)
MUTANTS[3] = ("fait annoncer `ESP32` au lieu de `ESP32-S3` ⇒ la mauvaise "
              "famille de puce, et un flash refuse ou fatal")
CIBLES[3] = ("c3",)
MUTANTS[4] = ("decale l'offset de l'application dans le manifeste ⇒ une app "
              "ecrite AILLEURS que dans sa partition")
CIBLES[4] = ("c4",)
MUTANTS[5] = ("replante un binaire FUSIONNE dans le manifeste ⇒ le contraire "
              "exact des quatre morceaux mesures")
CIBLES[5] = ("c5",)
MUTANTS[6] = ("fait mentir `PROVENANCE.md` sur la taille d'une image ⇒ des "
              "empreintes publiees qui ne sont plus celles servies")
CIBLES[6] = ("c6",)
MUTANTS[7] = ("fait annoncer au manifeste une version qui n'est PAS celle du "
              "binaire servi ⇒ l'inconnu croit poser autre chose")
CIBLES[7] = ("c7",)
MUTANTS[8] = ("remet la version du BANC D'ESSAI dans le manifeste — la faute "
              "EXACTE que le prototype du 2026-08-31 a publiee")
CIBLES[8] = ("c8",)
MUTANTS[9] = ("abime la bande-annonce d'integrite de l'asset ⇒ une image "
              "tronquee servie sans que rien ne rougisse")
CIBLES[9] = ("c9",)
MUTANTS[10] = ("remet une PLAGE de version pour ESP Web Tools ⇒ le code qui "
               "ecrit sur la carte peut changer en silence")
CIBLES[10] = ("c10",)
MUTANTS[11] = ("fait diverger la version epinglee dans la page de celle "
               "declaree a `THIRD-PARTY.md` ⇒ l'inventaire ment")
CIBLES[11] = ("c10",)
# 🔴 MUTANT 12 CORRIGE APRES ETRE SORTI **VERT** — ET LA QUESTION QU'IL POSAIT
#    AVAIT POUR REPONSE « LE MUTANT VISE A COTE », ⛔ PAS « LA GARDE A UN TROU ».
#    Sa 1re version mutait le TEXTE de `installeur/dn_installeur.py`. Or le
#    controle qu'il vise fait JOUER le produit IMPORTE : une mutation textuelle
#    ⛔ ne l'atteint pas, exactement comme le dit la note d'importation plus
#    haut. ⇒ il mute desormais la LISTE ATTENDUE, portee par l'etat — meme
#    patron que les mutants 21, 22 et 24, et pour la meme raison.
MUTANTS[12] = ("exige du serveur une adresse de charge qu'il ne sert PAS ⇒ "
               "un 404 au milieu du flash, et un message qui n'explique rien")
CIBLES[12] = ("c11",)
MUTANTS[13] = ("ne laisse a la page QU'UNE forme du nom du port ⇒ celui qui "
               "voit l'autre forme ne reconnait pas sa carte")
CIBLES[13] = ("c12",)
MUTANTS[14] = ("efface de la page le SECOND geste de selection du port ⇒ on "
               "sort sur un ecran qui ne dit pas qu'il manquait un clic")
CIBLES[14] = ("c13",)
MUTANTS[15] = ("efface de la page la procedure de recuperation ⇒ elle "
               "redevient enterree dans un README de 200 Ko")
CIBLES[15] = ("c14",)
MUTANTS[16] = ("efface l'avertissement hors Windows ⇒ un flash REUSSI vers "
               "une dalle qui n'aura jamais rien a afficher")
CIBLES[16] = ("c15",)
MUTANTS[17] = ("fait pointer la page vers « le depot » au lieu de la "
               "revision exacte ⇒ l'obligation GPL cesse d'etre tenue")
CIBLES[17] = ("c16",)
MUTANTS[18] = ("remplace le porteur d'un manque de `PROVENANCE.md` par « a "
               "nommer » — la faute EXACTE que `dn6-4` a payee")
CIBLES[18] = ("c17",)
MUTANTS[19] = ("replante un verbe d'ELEVATION dans le code de l'installeur")
CIBLES[19] = ("c18",)
MUTANTS[20] = ("efface de la page le refus des pilotes reclames a tort ⇒ "
               "l'inconnu part installer un pilote dont il n'a pas besoin")
CIBLES[20] = ("c19",)
MUTANTS[21] = ("INTERVERTIT la correspondance attendue de la decouverte de "
               "port : `-Serie` ne serait plus passe, et rien ne le verrait")
CIBLES[21] = ("c20",)
MUTANTS[22] = ("INTERVERTIT deux codes de `stop` : « port rendu » et « port "
               "disparu » deviendraient la meme chose")
CIBLES[22] = ("c21",)
MUTANTS[23] = ("retire de `.gitattributes` la regle qui declare les images "
               "BINAIRES ⇒ une substitution de fins de ligne les tuerait")
CIBLES[23] = ("c22",)
MUTANTS[24] = ("INTERVERTIT les codes attendus du pre-vol de charge ⇒ une "
               "charge absente sortirait comme « tout est la »")
CIBLES[24] = ("c23",)
MUTANTS[25] = ("retire une cible de `CIBLES` ⇒ un controle garde par ZERO "
               "mutant, le risque que `dn6-1` avait paye")
CIBLES[25] = ("c24",)
MUTANTS[26] = ("declare dans `CIBLES` un controle INEXISTANT (`c99`) ⇒ une "
               "cible PERIMEE, que « N mutants, N rouges » ne verrait pas")
CIBLES[26] = ("c25",)
MUTANTS[27] = ("declare une cible pour un mutant qui N'EXISTE PAS")
CIBLES[27] = ("c26",)
MUTANTS[28] = ("replante une SORTIE ANTICIPEE NON DECLAREE : le bilan "
               "retrecit, et il sortirait VERT")
CIBLES[28] = ("z",)
MUTANTS[29] = ("declare un mutant dont le CORPS LEVE ⇒ un mutant MORT, qui "
               "sortirait en Traceback SANS `BILAN` s'il n'etait pas repris")
CIBLES[29] = ("c0",)
# 🔴 LES SEPT SUIVANTS SONT NES D'UNE REVUE, ET CHACUN REPLANTE UNE FAUTE QUI A
#    ETE **DEMONTREE VERTE** — ⛔ pas une faute imaginee.
MUTANTS[30] = ("change la SEULE colonne d'empreinte de `PROVENANCE.md` ⇒ une "
               "image echangee a taille EGALE restait verte")
CIBLES[30] = ("c6",)
MUTANTS[31] = ("efface de la page l'etat « le module de flash n'arrive pas » "
               "⇒ un bouton inerte remplace une explication")
CIBLES[31] = ("c27",)
MUTANTS[32] = ("efface de la page l'etat « l'agent est pose » ⇒ le deuxieme "
               "lancement de tout le monde n'est plus explique")
CIBLES[32] = ("c27",)
MUTANTS[33] = ("CASSE le motif d'extraction du port DANS LE PRODUIT (parentheses "
               "⇒ crochets) : la decouverte rendrait `None` a chaque appel")
CIBLES[33] = ("c28",)
MUTANTS[34] = ("NEUTRALISE le test de CRC32 DANS LE PRODUIT ⇒ un asset "
               "retourne se declare INTACT et part a la carte")
CIBLES[34] = ("c29",)
MUTANTS[35] = ("fait proposer l'EFFACEMENT au premier flash ⇒ une carte au "
               "decoupage etranger serait ecrasee, sans que ce soit ecrit")
CIBLES[35] = ("c30",)
MUTANTS[36] = ("fait DERIVER la version epinglee publiee dans la prose ⇒ trois "
               "copies annoncent un numero que la page ne charge pas")
CIBLES[36] = ("c10",)

# ⚠️ LE COMPTE DU CHEMIN NORMAL. Il se PERIME si on ajoute un controle sans le
#    mettre a jour — et c'est voulu : c'est ce qui rend (z) FALSIFIABLE.
CONTROLES_PREVUS = 30

_MUTANT = 0

RE_ID_CTRL = re.compile(r"\((\w+)\)")


def ctrl(ok, libelle, detail=""):
    """UNE assertion, UNE ligne, UN identifiant. ⛔ Aucun controle muet.

    ⚠️ L'IDENTIFIANT VIT DANS LE LIBELLE, ⛔ pas dans un argument a part :
       `verif_campagne_dn56.py` lit les libelles A L'AST en prenant `args[1]`
       de chaque appel, et a COLONNE FIXE. Une autre signature retrecirait
       SILENCIEUSEMENT la population de cette gate-la."""
    assert len(libelle) < LARGEUR_LIBELLE, (
        "libelle de %d colonnes (max %d) : %r"
        % (len(libelle), LARGEUR_LIBELLE - 1, libelle))
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
    discriminant que la campagne exige de chaque mutant.

    ⚠️ DEUX SORTIES NE PASSENT PAS ICI, ET C'EST ECRIT PLUTOT QUE PROMIS :
       · `--liste-mutants`, qui n'emet AUCUN controle et ne rend AUCUN verdict ;
       · le mutant INCONNU, qui est une ERREUR D'APPEL et rend 2."""
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


# ═══════════════════════ LIRE LE DEPOT ═════════════════════════════════════

def suivis():
    """Les fichiers TRACES, par `git ls-files`. ⛔ Pas un parcours du disque :
    un repertoire ignore n'est pas du depot. Rend `None` si git refuse.

    🔴 `core.quotePath=false` ET `-z` NE SONT ⛔ PAS DU CONFORT — ET LE DEPOT
       EST FRANCOPHONE. Par defaut `git ls-files` ECHAPPE tout chemin non ASCII
       et l'entoure de guillemets : le jeton ne finit alors pas par `.bin` et le
       fichier quitte le corpus EN SILENCE."""
    try:
        r = subprocess.run(["git", "-c", "core.quotePath=false",
                            "ls-files", "-z"], cwd=RACINE,
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return None
    if r.returncode != 0:
        return None
    return sorted(x for x in r.stdout.split("\0") if x.strip())


def lire(chemin):
    """Le texte d'un fichier suivi. `newline=""` GARDE les fins de ligne."""
    try:
        with io.open(os.path.join(RACINE, chemin), encoding="utf-8",
                     errors="replace", newline="") as fh:
            return fh.read()
    except OSError:
        return None


def lire_octets(chemin):
    try:
        with open(os.path.join(RACINE, chemin), "rb") as fh:
            return fh.read()
    except OSError:
        return None


def plat(txt):
    """Le texte SANS ses retours a la ligne — un motif ne doit ⛔ pas dependre
    de l'endroit ou la prose a ete coupee."""
    return re.sub(r"\s+", " ", txt or "")


def version_du_binaire(octets):
    """La chaine `version` de `esp_app_desc_t`, LUE dans l'image applicative.

    ⛔ Ce n'est pas « ce que quelqu'un a ecrit a cote » : c'est ce que le
       compilateur a scelle DANS le binaire qui sera flashe. Rend `(version,
       projet)` ou `(None, motif)`."""
    if not octets or len(octets) < APP_DESC_PROJET + 32:
        return None, "image trop courte pour porter un descripteur"
    magie = struct.unpack("<I", octets[APP_DESC_OFFSET:APP_DESC_OFFSET + 4])[0]
    if magie != APP_DESC_MAGIE:
        return None, ("magie %#010x a l'offset %#x — attendu %#010x"
                      % (magie, APP_DESC_OFFSET, APP_DESC_MAGIE))
    brut = octets[APP_DESC_VERSION:APP_DESC_VERSION + 32].split(b"\x00")[0]
    projet = octets[APP_DESC_PROJET:APP_DESC_PROJET + 32].split(b"\x00")[0]
    try:
        return brut.decode("ascii"), projet.decode("ascii")
    except UnicodeDecodeError:
        return None, "le champ version n'est pas de l'ASCII"


def offsets_de_reference(fichiers):
    """Les offsets qui font FOI, et **d'ou ils viennent**.

    🔴 DEUX SOURCES, ET LA GATE DIT LAQUELLE ELLE A EMPLOYEE.
       (a) `build/flasher_args.json` — ce que l'IDF ecrit lui-meme a la fin du
           build. C'est la source de verite, et elle couvre les QUATRE.
       (b) a defaut — et c'est le cas NORMAL d'un clone neuf, ou `build/` est
           gitignore — la TABLE DE PARTITIONS, qui couvre les deux offsets qui
           dependent d'un choix (l'application et l'asset). Les deux autres
           sont des constantes de la plateforme : le bootloader d'un ESP32-S3
           demarre a `0`, et la table de partitions est a `0x8000` tant que
           `sdkconfig.defaults` ne pose pas d'`CONFIG_PARTITION_TABLE_OFFSET`.
    ⚠️ ⛔ ON NE SE TAIT PAS SUR LA DIFFERENCE : la voie (b) est declaree PLUS
       FAIBLE dans le detail du controle, ⛔ pas presentee comme equivalente."""
    brut = fichiers.get(FLASHER_ARGS)
    if brut:
        try:
            fa = json.loads(brut)
            ff = fa["flash_files"]
            return ({os.path.basename(v): int(k, 16) for k, v in ff.items()},
                    FLASHER_ARGS, "forte")
        except (ValueError, KeyError, TypeError):
            pass
    csv = fichiers.get(PARTITIONS) or ""
    par = {}
    for m in RE_PARTITION.finditer(csv):
        par[m.group(1)] = int(m.group(4), 16)
    if "factory" not in par or "assets" not in par:
        return None, PARTITIONS, "absente"
    return ({"bootloader.bin": 0,
             "partition-table.bin": 0x8000,
             "desknode.bin": par["factory"],
             ASSET_FICHIER: par["assets"]},
            PARTITIONS, "faible")


def importer_produit():
    """Importe `installeur/dn_installeur.py` — le PRODUIT, ⛔ pas son texte.

    🔴 LA SOURCE EST **COMPILEE ICI**, ⛔ PAS CHARGEE PAR LE MECANISME
       ORDINAIRE — ET C'EST UN PIEGE MESURE LE 2026-09-08 SUR `dn7-1`. Le
       chargement ordinaire consulte `__pycache__`, dont la validation repose
       sur (mtime, taille) : apres avoir demontre un defaut puis RESTAURE le
       fichier, la gate continuait de juger le BYTECODE PERIME et rendait le
       meme rouge sur une source SAINE. Une gate qui mesure la version d'hier
       est pire qu'une gate absente.
    ⚠️ Le module ne fait RIEN a l'import : il ne lie aucun port, n'appelle aucun
       PowerShell, n'ouvre aucun navigateur.
    🔴 CONSEQUENCE A LIRE : les controles qui font JOUER ce module ne sont ⛔ PAS
       atteints par une mutation TEXTUELLE. C'est pour ca que leurs mutants
       INVERSENT la CORRESPONDANCE ATTENDUE, portee par l'etat — ce qui est
       verifie la est un COMPORTEMENT, ⛔ pas une chaine de caracteres."""
    chemin = os.path.join(RACINE, PY)
    try:
        with io.open(chemin, encoding="utf-8") as fh:
            source = fh.read()
        mod = importlib.util.module_from_spec(
            importlib.util.spec_from_loader("dn_installeur_dn72", loader=None))
        mod.__file__ = chemin
        exec(compile(source, chemin, "exec"), mod.__dict__)   # noqa: S102
        return mod, None
    except Exception as exc:                              # noqa: BLE001
        return None, "%s: %s" % (type(exc).__name__, str(exc)[:90])


PS1_DE_PAPIER = ("param(\n"
                 "    [ValidateSet('etat', 'stop', 'retirer')]\n"
                 "    [string]$Action = 'etat'\n)\n")

# 🔴 CE QUE LE PRODUIT DOIT FAIRE DE LA DECOUVERTE DE PORT, ET DES CODES.
#    ⚠️ C'EST UNE CORRESPONDANCE, ⛔ PAS UNE PRESENCE. Chercher la sous-chaine
#       `-Serie` dans la source prouverait qu'elle est ECRITE, ⛔ pas qu'elle
#       est PASSEE : une condition inversee la rendrait morte, et le controle
#       resterait vert. ⇒ on IMPORTE le produit et on le fait JOUER.
# 🔴 LES **SIX** ADRESSES QUE LE SERVEUR DOIT SERVIR. ⚠️ Ce controle fait jouer
#    le PRODUIT IMPORTE : une mutation TEXTUELLE ⛔ ne l'atteindrait pas, donc
#    la liste attendue vit dans l'etat et c'est ELLE que le mutant deplace.
# 🔴 `PROVENANCE.md` EN FAIT PARTIE, ET SON OUBLI ETAIT UN TROU DEMONTRE : la
#    page y renvoie DEUX FOIS — c'est le pointeur de source qu'exige la
#    GPL-3.0 — et le retirer de la liste blanche cassait les deux liens sans
#    qu'aucun controle ne bouge.
ATTENDU_SERVIS = (("/charge/manifest.json", "/charge/PROVENANCE.md")
                  + tuple("/charge/%s" % n for n in IMAGES))

ATTENDU_PORT = {
    # port decouvert ⇒ `-Serie <port>` DOIT etre dans la ligne de commande
    "decouvert": ("-Serie COM7", True),
    # ⛔ aucun port decouvert ⇒ ⛔ AUCUN `-Serie` invente
    "absent": ("-Serie", False),
}
# 🔴 LES CODES DE `stop`, ET CE QU'ILS VEULENT DIRE — RELUS DANS L'OUTIL.
#    ⚠️ `7` est le cas NORMAL d'une carte partie : le lire comme un echec ET le
#       lire comme un succes sont DEUX FAUTES DIFFERENTES.
ATTENDU_CODES = {
    0: "rendu",
    4: "drapeau",
    7: "disparu",
    8: "tenu",
}
# Le pre-vol de charge : `5` quand il n'y a rien a poser.
ATTENDU_PREVOL = {
    "charge_absente": 5,
    "charge_entiere": 0,
}

# 🔴 CE QUE `decouvrir_port` DOIT RENDRE, ET IL EST **REELLEMENT EXECUTE**.
#    ⚠️ TROU DEMONTRE A LA REVUE : les deux controles qui parlaient du port
#    REMPLACAIENT cette fonction par un double. Elle n'etait donc jouee par
#    RIEN — et changer son motif d'extraction de `(COM3)` a `[COM3]` faisait
#    rendre `None` a chaque appel SANS qu'aucune gate ne bouge, c'est-a-dire
#    que la regression que cette marche declare corriger pouvait revenir EN
#    SILENCE. ⇒ ici, seul `_powershell` est double : la fonction, elle, tourne.
#    La 1re ligne est celle MESUREE sur la tour le 2026-09-08.
LIGNE_PNP_MESUREE = ("DN|Peripherique serie USB (COM3)|"
                     "USB\\VID_303A&PID_1001&MI_00\\6&3B8496F8&0&0000")
LIGNE_PNP_SECONDE = ("DN|Peripherique serie USB (COM9)|"
                     "USB\\VID_303A&PID_1001&MI_00\\6&AAAAAAAA&0&0000")
ATTENDU_DECOUVERTE = {
    # cle           : (rc, sortie PowerShell, port attendu)
    "mesuree":  (0, LIGNE_PNP_MESUREE, "COM3"),
    "aucune":   (0, "", None),
    "muette":   (None, "", None),
    # ⚠️ DEUX CARTES DE MEME `VID:PID` : on REFUSE de choisir. Rendre la
    #    premiere ferait jouer `stop` sur une carte ARBITRAIRE.
    "deux":     (0, LIGNE_PNP_MESUREE + "\n" + LIGNE_PNP_SECONDE, None),
}

# 🔴 LES PATCHS QUI REPLANTENT UNE FAUTE **DANS LE PRODUIT IMPORTE**.
#    ⚠️ Les controles fonctionnels ne se mutent pas par le texte — le module
#    est deja compile. Muter la CORRESPONDANCE ATTENDUE prouve que le controle
#    compare ; muter LE PRODUIT prouve qu'il attrape la VRAIE faute. Les deux
#    tags ci-dessous replantent EXACTEMENT les deux regressions demontrees a la
#    revue, ⛔ pas des fautes imaginees.
PATCHS_PRODUIT = ("re_com_casse", "crc_neutralise")


def jouer_port(mod, att):
    """Fait jouer `stop` contre un double de papier, DEUX FOIS.

    ⛔ Rien n'est lance : PowerShell, la decouverte de port et la lecture de
       l'outil sont remplaces le temps de l'appel, et remis en place ensuite."""
    garde = (mod._powershell, mod.decouvrir_port, mod._lire, dict(mod._PILOTE))
    out = {}
    try:
        mod._PILOTE.update(chemin=os.path.join(RACINE, "tools",
                                               "dn_agent_tour.ps1"),
                           origine="double de papier")
        mod._lire = lambda _c: PS1_DE_PAPIER
        vues = {}

        def _ps(arguments, timeout=90):
            vues["cmd"] = list(arguments)
            return (0, "sortie de papier", ["powershell"] + list(arguments),
                    None)
        mod._powershell = _ps
        for cle, reponse in (("decouvert", ("COM7", "un nom", "une instance")),
                             ("absent", (None, None, "aucune carte"))):
            mod.decouvrir_port = (lambda r: (lambda: r))(reponse)
            vues.clear()
            d = mod.jouer_verbe("stop")
            out[cle] = " ".join(vues.get("cmd") or []) + " || " + d.get("commande", "")
    except Exception as exc:                              # noqa: BLE001
        out["__erreur__"] = "%s: %s" % (type(exc).__name__, str(exc)[:80])
    finally:
        mod._powershell, mod.decouvrir_port, mod._lire = garde[:3]
        mod._PILOTE.clear()
        mod._PILOTE.update(garde[3])
    return out


def jouer_codes(mod):
    """Fait jouer `stop` QUATRE FOIS, une par code documente, et relit le mot
    que le produit emploie pour chacun."""
    garde = (mod._powershell, mod.decouvrir_port, mod._lire, dict(mod._PILOTE))
    out = {}
    try:
        mod._PILOTE.update(chemin=os.path.join(RACINE, "tools",
                                               "dn_agent_tour.ps1"),
                           origine="double de papier")
        mod._lire = lambda _c: PS1_DE_PAPIER
        mod.decouvrir_port = lambda: ("COM7", "un nom", "une instance")
        for code in sorted(ATTENDU_CODES):
            mod._powershell = (lambda c: (lambda a, timeout=90: (
                c, "sortie de papier", ["powershell"] + list(a), None)))(code)
            d = mod.jouer_verbe("stop")
            out[code] = (d.get("etat_port"), d.get("verdict", "")[:60])
    except Exception as exc:                              # noqa: BLE001
        out["__erreur__"] = "%s: %s" % (type(exc).__name__, str(exc)[:80])
    finally:
        mod._powershell, mod.decouvrir_port, mod._lire = garde[:3]
        mod._PILOTE.clear()
        mod._PILOTE.update(garde[3])
    return out


def jouer_decouverte(mod, att):
    """Fait tourner **LA VRAIE** `decouvrir_port`, PowerShell double.

    ⛔ Ici, ⛔ on ne remplace PAS la fonction : on double seulement l'appel
       systeme sous elle. C'est la seule facon de faire jouer son motif
       d'extraction, sa distinction des deux motifs d'echec, et son refus de
       choisir entre deux cartes."""
    garde = mod._powershell
    out = {}
    try:
        for cle in sorted(att):
            rc, sortie, _attendu = att[cle]
            mod._powershell = (lambda r, s: (
                lambda a, timeout=90: (r, s, ["powershell"], None)))(rc, sortie)
            out[cle] = mod.decouvrir_port()[0]
    except Exception as exc:                              # noqa: BLE001
        out["__erreur__"] = "%s: %s" % (type(exc).__name__, str(exc)[:80])
    finally:
        mod._powershell = garde
    return out


def jouer_charge_abimee(mod):
    """Copie la charge, RETOURNE UN OCTET, et relit ce que le produit en dit.

    🔴 CE CONTROLE EXISTE PARCE QUE LA BRANCHE ABIMEE N'ETAIT JOUEE PAR RIEN.
       Le cas « charge absente » du pre-vol REMPLACE `etat_charge` par un
       dictionnaire fabrique : neutraliser le test de CRC32 dans le produit
       laissait donc un asset retourne se declarer INTACT, et le `5` que le
       `README.md` et le `.bat` publient comme instrument mecanique devenait un
       chiffre a croire sur parole. ⇒ ici, la charge est VRAIE, abimee sur le
       disque, et c'est le produit qui la juge."""
    garde = (mod.CHARGE, mod.MANIFESTE)
    out = {}
    tmp = tempfile.mkdtemp(prefix="dn72-")
    try:
        cible = os.path.join(tmp, "charge")
        shutil.copytree(os.path.join(RACINE, CHARGE), cible)
        chemin = os.path.join(cible, ASSET_FICHIER)
        with open(chemin, "rb") as fh:
            brut = bytearray(fh.read())
        if len(brut) < 200:
            out["__erreur__"] = "l'asset copie est trop court pour etre abime"
            return out
        brut[100] ^= 0xFF                 # ⛔ la CHARGE UTILE, ⛔ pas la queue
        with open(chemin, "wb") as fh:
            fh.write(bytes(brut))
        mod.CHARGE = cible
        mod.MANIFESTE = os.path.join(cible, "manifest.json")
        tampon = io.StringIO()
        with contextlib.redirect_stdout(tampon):
            etat = mod.etat_charge()
            garde2 = (mod.dependance_presente, mod.arbre_parent_present,
                      mod.localiser_pilote)
            try:
                mod.dependance_presente = lambda m, s: True
                mod.arbre_parent_present = lambda: True
                mod.localiser_pilote = lambda: (
                    os.path.join(RACINE, "tools", "dn_agent_tour.ps1"),
                    "double de papier")
                out["rc_prevol"] = mod.prevol(False)
            finally:
                (mod.dependance_presente, mod.arbre_parent_present,
                 mod.localiser_pilote) = garde2
        out["complete"] = etat.get("complete")
        out["asset"] = etat.get("asset", "")
    except Exception as exc:                              # noqa: BLE001
        out["__erreur__"] = "%s: %s" % (type(exc).__name__, str(exc)[:80])
    finally:
        mod.CHARGE, mod.MANIFESTE = garde
        shutil.rmtree(tmp, ignore_errors=True)
    return out


class _ZlibComplaisant(object):
    """Un `zlib` qui dit toujours « le CRC est bon » — ⛔ le patch du mutant.

    Il REPLANTE la faute demontree a la revue : neutraliser le test de CRC32
    fait declarer INTACT un asset retourne."""

    def __init__(self, vrai, valeur):
        self._vrai = vrai
        self._valeur = valeur

    def crc32(self, donnees, *a):
        return self._valeur


def jouer_prevol(mod):
    """Fait jouer le PRE-VOL deux fois et relit son CODE DE SORTIE."""
    garde = (mod.dependance_presente, mod.arbre_parent_present,
             mod.localiser_pilote, mod.etat_charge)
    out = {}
    try:
        mod.arbre_parent_present = lambda: True
        mod.localiser_pilote = lambda: (os.path.join(RACINE, "tools",
                                                     "dn_agent_tour.ps1"),
                                        "double de papier")
        mod.dependance_presente = lambda m, s: True
        tampon = io.StringIO()
        with contextlib.redirect_stdout(tampon):
            reelle = garde[3]
            mod.etat_charge = reelle
            out["charge_entiere"] = mod.prevol(False)
            manquee = dict(reelle())
            manquee.update(complete=False, manquants=["desknode.bin"])
            mod.etat_charge = lambda: manquee
            out["charge_absente"] = mod.prevol(False)
    except Exception as exc:                              # noqa: BLE001
        out["__erreur__"] = "%s: %s" % (type(exc).__name__, str(exc)[:80])
    finally:
        (mod.dependance_presente, mod.arbre_parent_present,
         mod.localiser_pilote, mod.etat_charge) = garde
    return out


# ═══════════════════════════ LES MUTANTS ═══════════════════════════════════

def muter(etat):
    """REPLANTE une faute DANS L'ETAT — ⛔ jamais dans un fichier du depot.

    🔴 TOUTE mutation passe par cet unique etat, et le corps principal compare
       l'etat AVANT/APRES : la garde du no-op est donc UNIVERSELLE.
    ⚠️ MAIS ELLE N'EST ATTEINTE QUE SI LE CORPS **REND**. Un corps qui `split`,
       indexe ou depaquette sur une ancre disparue LEVE, et le `try` du corps
       principal le rend en `rc=1` + `BILAN` + `[KO ]` — MOT POUR MOT le contrat
       que la campagne appelle « sain » : un mutant PERIME passerait pour un
       gardien vivant. ⇒ tout corps VERIFIE son ancre d'abord et rend `e`
       INCHANGE. ⛔ Le mutant 29 leve EXPRES : il est le temoin de ce cas."""
    e = copy.deepcopy(etat)
    p, r = e["fichiers"], e["regles"]
    o = e["octets"]

    if _MUTANT == 1:
        cible = "%s/desknode.bin" % CHARGE
        if cible not in e["traces"]:
            return e                      # deja hors arbre ⇒ NO-OP ⇒ rc=3
        e["traces"] = tuple(x for x in e["traces"] if x != cible)
    elif _MUTANT == 2:
        if not p.get(MANIFESTE, "").strip():
            return e                      # deja vide ⇒ NO-OP ⇒ rc=3
        p[MANIFESTE] = "{"
    elif _MUTANT == 3:
        if CHIP_ATTENDU not in p.get(MANIFESTE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[MANIFESTE] = p[MANIFESTE].replace('"%s"' % CHIP_ATTENDU,
                                            '"ESP32"', 1)
    elif _MUTANT == 4:
        if '"offset": 65536' not in p.get(MANIFESTE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[MANIFESTE] = p[MANIFESTE].replace('"offset": 65536',
                                            '"offset": 69632', 1)
    elif _MUTANT == 5:
        if MANIFESTE not in p:
            return e                      # fichier hors corpus ⇒ NO-OP ⇒ rc=3
        p[MANIFESTE] = p[MANIFESTE].replace(
            '"builds"', '"merge_bin": true,\n  "builds"', 1)
        if "merge_bin" not in p[MANIFESTE]:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
    elif _MUTANT == 6:
        lignes = RE_PROV_LIGNE.findall(p.get(PROVENANCE, ""))
        if not lignes:
            return e                      # table disparue ⇒ NO-OP ⇒ rc=3
        nom, off, taille, sha = lignes[0]
        avant = "| `%s` | `%s` | `%s` |" % (nom, off, taille)
        if avant not in p[PROVENANCE]:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PROVENANCE] = p[PROVENANCE].replace(
            avant, "| `%s` | `%s` | `%d` |" % (nom, off, int(taille) + 8), 1)
    elif _MUTANT == 7:
        m = re.search(r'"version": "([^"]+)"', p.get(MANIFESTE, ""))
        if not m:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[MANIFESTE] = p[MANIFESTE].replace(
            '"version": "%s"' % m.group(1), '"version": "9f9f9f9"', 1)
    elif _MUTANT == 8:
        m = re.search(r'"version": "([^"]+)"', p.get(MANIFESTE, ""))
        if not m or m.group(1) == VERSION_DU_BANC:
            return e                      # deja la valeur du banc ⇒ NO-OP
        p[MANIFESTE] = p[MANIFESTE].replace(
            '"version": "%s"' % m.group(1),
            '"version": "%s"' % VERSION_DU_BANC, 1)
    elif _MUTANT == 9:
        cle = "%s/%s" % (CHARGE, ASSET_FICHIER)
        brut = o.get(cle)
        if not brut or len(brut) < ASSET_QUEUE + 32:
            return e                      # image absente ⇒ NO-OP ⇒ rc=3
        # ⛔ ON ABIME LA CHARGE UTILE, ⛔ PAS LA QUEUE : c'est exactement la
        #    faute que le CRC existe pour attraper — une image qui a l'air
        #    entiere et dont le contenu a bouge.
        o[cle] = brut[:100] + bytes([brut[100] ^ 0xFF]) + brut[101:]
    elif _MUTANT == 10:
        m = RE_EWT_PAGE.search(p.get(PAGE, ""))
        if not m:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace("esp-web-tools@" + m.group(1),
                                  "esp-web-tools@10")
    elif _MUTANT == 11:
        m = RE_EWT_PAGE.search(p.get(PAGE, ""))
        if not m:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace("esp-web-tools@" + m.group(1),
                                  "esp-web-tools@9.1.0")
    elif _MUTANT == 12:
        a = e["attendu_servis"]
        if "/charge/desknode.bin" not in a:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        e["attendu_servis"] = tuple("/charge/desknode-absent.bin"
                                    if x == "/charge/desknode.bin" else x
                                    for x in a)
    elif _MUTANT == 13:
        if FORME_PUCE not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(FORME_PUCE, "le port de la carte")
    elif _MUTANT == 14:
        if GESTE_2 not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(GESTE_2, "valider")
    elif _MUTANT == 15:
        if RECUP_RESET not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(RECUP_RESET, "redemarrage")
    elif _MUTANT == 16:
        if ANCRE_HORS_WINDOWS not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(ANCRE_HORS_WINDOWS, "etat-sans-objet")
    elif _MUTANT == 17:
        if "PROVENANCE.md" not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace("charge/PROVENANCE.md", "https://exemple")
        p[PAGE] = p[PAGE].replace("PROVENANCE.md", "le dépôt")
    elif _MUTANT == 18:
        if "`dn4-45`" not in p.get(PROVENANCE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PROVENANCE] = p[PROVENANCE].replace("`dn4-45`", "à nommer")
    elif _MUTANT == 19:
        if PY not in p:
            return e                      # fichier hors corpus ⇒ NO-OP ⇒ rc=3
        # 🔴 LA FORME NATURELLE EN PYTHON — les deux jetons SEPARES par la
        #    virgule d'une liste d'arguments. C'est elle qui avait demontre le
        #    trou de la 1re version de la garde equivalente, sur `dn7-1`.
        p[PY] += ('\ndef elever():\n    return subprocess.run('
                  '["powershell", "Start-Process", "-Verb", "RunAs"])\n')
    elif _MUTANT == 20:
        if PILOTES_INUTILES[0] not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        for nom in PILOTES_INUTILES:
            p[PAGE] = p[PAGE].replace(nom, "un pilote")
    elif _MUTANT == 21:
        # ⚠️ IL MUTE LA CORRESPONDANCE ATTENDUE, ⛔ pas la source : le produit
        #    est deja IMPORTE, et un mutant textuel ne l'atteint pas.
        a = e["attendu_port"]
        if "decouvert" not in a or "absent" not in a:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        a["decouvert"], a["absent"] = a["absent"], a["decouvert"]
    elif _MUTANT == 22:
        a = e["attendu_codes"]
        if 0 not in a or 7 not in a:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        a[0], a[7] = a[7], a[0]
    elif _MUTANT == 23:
        regle = "installeur/charge/*.bin binary"
        if regle not in p.get(ATTRIBUTS, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[ATTRIBUTS] = p[ATTRIBUTS].replace(regle, "installeur/charge/*.bin text")
    elif _MUTANT == 24:
        a = e["attendu_prevol"]
        if "charge_absente" not in a or "charge_entiere" not in a:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        a["charge_absente"], a["charge_entiere"] = (a["charge_entiere"],
                                                    a["charge_absente"])
    elif _MUTANT == 25:
        # ⚠️ LA VICTIME EST **DERIVEE**, ⛔ pas codee en dur : viser un mutant
        #    par son numero cesse de marcher le jour ou son controle gagne un
        #    SECOND gardien.
        compte = {}
        for _n, _v in e["cibles"].items():
            for _c in _v:
                compte[_c] = compte.get(_c, 0) + 1
        for _n, _v in sorted(e["cibles"].items()):
            if any(compte[_c] == 1 for _c in _v):
                e["cibles"][_n] = ()
                break
    elif _MUTANT == 26:
        e["cibles"][26] = tuple(e["cibles"][26]) + ("c99",)
    elif _MUTANT == 27:
        e["cibles"][99] = ("c1",)      # une cible pour un mutant INEXISTANT
    elif _MUTANT == 28:
        r["sortie_anticipee"] = True
    elif _MUTANT == 29:
        # 🔴 IL LEVE EXPRES : c'est la faute « un mutant declare qui MEURT ».
        raise AssertionError("mutant 29 : corps volontairement LEVANT")
    elif _MUTANT == 30:
        # ⚠️ IL NE TOUCHE QUE L'EMPREINTE : la taille et l'offset restent
        #    JUSTES. C'est exactement le cas qu'une verification de taille
        #    seule ne peut pas voir.
        lignes = RE_PROV_LIGNE.findall(p.get(PROVENANCE, ""))
        if not lignes:
            return e                      # table disparue ⇒ NO-OP ⇒ rc=3
        sha = lignes[0][3]
        if sha not in p[PROVENANCE]:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        faux = ("0" if sha[0] != "0" else "1") + sha[1:]
        p[PROVENANCE] = p[PROVENANCE].replace(sha, faux, 1)
    elif _MUTANT == 31:
        if ANCRE_CDN not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(ANCRE_CDN, "etat-sans-objet-cdn")
    elif _MUTANT == 32:
        if ANCRE_PORT_TENU not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(ANCRE_PORT_TENU, "etat-sans-objet-port")
    elif _MUTANT == 33:
        if e["patch_produit"] is not None:
            return e                      # deja patche ⇒ NO-OP ⇒ rc=3
        e["patch_produit"] = "re_com_casse"
    elif _MUTANT == 34:
        if e["patch_produit"] is not None:
            return e                      # deja patche ⇒ NO-OP ⇒ rc=3
        e["patch_produit"] = "crc_neutralise"
    elif _MUTANT == 35:
        if '"new_install_prompt_erase": false' not in p.get(MANIFESTE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[MANIFESTE] = p[MANIFESTE].replace(
            '"new_install_prompt_erase": false',
            '"new_install_prompt_erase": true', 1)
    elif _MUTANT == 36:
        m = RE_EWT_PAGE.search(p.get(PAGE, ""))
        if not m or m.group(1) not in p.get(LISEZMOI, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[LISEZMOI] = p[LISEZMOI].replace(m.group(1), "9.9.9", 1)
    else:
        raise AssertionError("mutant %d declare mais SANS CORPS" % _MUTANT)
    return e


# ═══════════════════════════ LA RECIPROQUE ═════════════════════════════════

def _texte_litteral(n):
    """La partie LITTERALE d'un libelle, meme construit par formatage."""
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Mod, ast.Add)):
        return _texte_litteral(n.left)
    if isinstance(n, ast.JoinedStr) and n.values:
        return _texte_litteral(n.values[0])
    return None


def ids_par_ast():
    """Les identifiants de TOUS les controles de CE fichier, lus A L'AST.

    🔴 POURQUOI PAS L'ENSEMBLE DES IDENTIFIANTS DEJA EMIS : cet ensemble est
       fige AU MOMENT DE L'APPEL de la reciproque. Tout controle ajoute APRES
       ce bloc en sortirait INVISIBLE."""
    try:
        with io.open(os.path.abspath(__file__), encoding="utf-8") as fh:
            arbre = ast.parse(fh.read())
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    out = set()
    for n in ast.walk(arbre):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "ctrl" and len(n.args) >= 2):
            m = RE_ID_CTRL.match(_texte_litteral(n.args[1]) or "")
            if m:
                out.add(m.group(1))
    return out or None


def main():
    global _MUTANT
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--mutant", type=int, default=None,
                    help="REPLANTE une faute EN MEMOIRE pour prouver que le "
                         "controle correspondant sait ROUGIR")
    ap.add_argument("--liste-mutants", action="store_true",
                    help="dit ce que chaque mutant replante, et sort")
    args = ap.parse_args()
    if args.mutant is not None and args.mutant not in MUTANTS:
        # ⛔ PAS une sortie par exception, qui rendrait 1 et se confondrait avec
        #    un vrai defaut : un mutant inconnu est une ERREUR D'APPEL.
        print("MUTANT %d INCONNU : il n'est pas declare. ⛔ Un mutant qui "
              "n'existe pas ne prouve RIEN — ⛔ ne pas conclure que le "
              "controle est vert." % args.mutant, file=sys.stderr)
        return 2
    _MUTANT = args.mutant or 0

    if args.liste_mutants:
        for n in sorted(MUTANTS):
            print("  %2d  [%s]  %s"
                  % (n, ",".join(CIBLES.get(n, ())) or "—", MUTANTS[n]))
        return 0

    print("=" * 78)
    print("dn7-2 — LA CHARGE EST VRAIE, ENTIERE, ET LA PAGE DIT CE QUI COINCE"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)
    print("cibles     : %s/  +  %s  +  %s" % (CHARGE, PAGE, TIERS))
    print("⛔ CETTE GATE NE FLASHE RIEN : aucun port serie ouvert, aucun "
          "PowerShell\n   appele, aucune carte demandee. Elle relit ce que le "
          "depot PUBLIE.")

    traces = suivis()
    if traces is None:
        ctrl(False, "(c0) l'arbre trace est LISIBLE",
             "⛔ `git ls-files` a refuse — ⛔ pas de parcours de disque en "
             "remplacement : un repertoire ignore n'est pas du depot")
        return bilan(1, "l'arbre trace est illisible")

    fichiers, illisibles = {}, []
    for f in FIXES:
        t = lire(f)
        if t is None:
            illisibles.append(f)
        else:
            fichiers[f] = t
    # ⚠️ `flasher_args.json` EST OPTIONNEL, ET C'EST ECRIT : `build/` est
    #    gitignore, donc un clone neuf ne l'a PAS. Son absence fait basculer la
    #    source de verite des offsets, ⛔ elle ne fait pas rougir la gate.
    fa = lire(FLASHER_ARGS)
    if fa is not None:
        fichiers[FLASHER_ARGS] = fa
    if illisibles:
        ctrl(False, "(c0) tout fichier attendu est LISIBLE",
             "⛔ ABSENT(S) OU ILLISIBLE(S) : %s — la population des controles "
             "serait RETRECIE en silence" % " · ".join(illisibles))
        return bilan(1, "%d fichier(s) attendu(s) illisible(s)" % len(illisibles))

    octets = {}
    for nom in IMAGES:
        cle = "%s/%s" % (CHARGE, nom)
        brut = lire_octets(cle)
        if brut is not None:
            octets[cle] = brut

    etat = {"fichiers": fichiers,
            "octets": octets,
            "traces": tuple(traces),
            "cibles": {n: tuple(v) for n, v in CIBLES.items()},
            # ⚠️ LES CORRESPONDANCES ATTENDUES VIVENT DANS L'ETAT : c'est ce qui
            #    rend les controles FONCTIONNELS mutables — un mutant textuel
            #    ⛔ n'atteint pas un module deja importe.
            "attendu_servis": tuple(ATTENDU_SERVIS),
            "attendu_port": {k: tuple(v) for k, v in ATTENDU_PORT.items()},
            "attendu_codes": dict(ATTENDU_CODES),
            "attendu_prevol": dict(ATTENDU_PREVOL),
            "attendu_decouverte": {k: tuple(v)
                                   for k, v in ATTENDU_DECOUVERTE.items()},
            # ⚠️ ⛔ PAS UN OBJET : un simple JETON, pour que la comparaison
            #    avant/apres de la garde du no-op reste triviale.
            "patch_produit": None,
            "regles": {"sortie_anticipee": False}}

    # 🔴 UN MUTANT QUI MEURT SORTIRAIT EN TRACEBACK, SANS `BILAN` — or « pas de
    #    BILAN » est le discriminant d'une gate MORTE. ⇒ il se rend en KO.
    try:
        neuf = muter(etat) if _MUTANT else etat
    except Exception as exc:                              # noqa: BLE001
        ctrl(False, "(c0) le mutant %d a une CIBLE et un CORPS" % _MUTANT,
             "⛔ %s: %s — la faute est dans le MUTANT, ⛔ pas dans la gate"
             % (type(exc).__name__, str(exc)[:80]))
        return bilan(1, "le mutant %d n'a pas pu s'appliquer" % _MUTANT)
    # 🔴 UN MUTANT SANS EFFET EST INVISIBLE AU CONTRAT DE LA CAMPAGNE.
    if _MUTANT and neuf == etat:
        ctrl(False, "(c0) le mutant %d a bien un EFFET" % _MUTANT,
             "⛔ SANS EFFET — son ancre litterale a disparu de la cible. "
             "⛔ Ce n'est PAS un controle vert : rc=3, mutant PERIME.")
        return bilan(3, "le mutant %d n'a eu aucun effet" % _MUTANT)

    f = neuf["fichiers"]
    o = neuf["octets"]
    traces = list(neuf["traces"])
    cibles, regles = neuf["cibles"], neuf["regles"]
    att_servis = list(neuf["attendu_servis"])
    att_port = neuf["attendu_port"]
    att_codes = neuf["attendu_codes"]
    att_prevol = neuf["attendu_prevol"]
    att_dec = neuf["attendu_decouverte"]
    page = f.get(PAGE, "")
    py = f.get(PY, "")
    prov = f.get(PROVENANCE, "")
    tiers = f.get(TIERS, "")
    attributs = f.get(ATTRIBUTS, "")

    produit, err_produit = importer_produit()
    # 🔴 LE PATCH REPLANTE UNE FAUTE **DANS LE PRODUIT**, ⛔ pas dans un texte.
    #    C'est ce qui distingue « le controle compare » de « le controle attrape
    #    la VRAIE regression » : les deux fautes ci-dessous ont ete DEMONTREES
    #    a la revue, et elles laissaient la gate VERTE.
    if produit is not None and neuf["patch_produit"] == "re_com_casse":
        produit.RE_COM = re.compile(r"\[(COM[0-9]+)\]")
    elif produit is not None and neuf["patch_produit"] == "crc_neutralise":
        brut_ref = lire_octets("%s/%s" % (CHARGE, ASSET_FICHIER)) or b""
        attendu_crc = (struct.unpack("<II", brut_ref[-8:])[1]
                       if len(brut_ref) >= 8 else 0)
        produit.zlib = _ZlibComplaisant(zlib, attendu_crc)

    # ── (c1) LES CINQ FICHIERS DE CHARGE SONT AU DEPOT ────────────────────
    print("\n── (c1) LA CHARGE EST **VERSIONNEE** ─────────────────────────────")
    # 🔴 ⛔ « ELLE EST SUR MON DISQUE » NE PROUVE RIEN. Un inconnu qui telecharge
    #    n'a QUE ce que git suit. Et le dossier ne s'appelle ⛔ pas `build` :
    #    `.gitignore` porte `build/` SANS `/` initial, donc a toute profondeur —
    #    mesure du 2026-09-08, les images auraient disparu EN SILENCE.
    absents = [x for x in CINQ if x not in traces]
    vides = [x for x in CINQ
             if x in traces and not (o.get(x) or f.get(x, "").strip())]
    ctrl(not absents and not vides,
         "(c1) les 5 fichiers de charge sont SUIVIS",
         "%d fichier(s), tous traces" % len(CINQ)
         if not absents and not vides
         else "⛔ NON SUIVI(S) : %s · VIDE(S) : %s — un inconnu n'a QUE ce que "
              "git suit, et un vide n'est pas une absence de defaut"
              % (" ".join(absents) or "—", " ".join(vides) or "—"))

    # ── (c2) LE MANIFESTE SE LIT ──────────────────────────────────────────
    print("\n── (c2)(c3)(c4)(c5) LE MANIFESTE, MORCEAU PAR MORCEAU ────────────")
    manifeste, err_manifeste, parts, chip = None, None, [], None
    try:
        manifeste = json.loads(f.get(MANIFESTE, ""))
        build = (manifeste.get("builds") or [{}])[0]
        parts = list(build.get("parts") or [])
        chip = build.get("chipFamily")
    # ⚠️ `AttributeError` EST DANS LA LISTE, ET C'EST UN CAS REEL : un
    #    `manifest.json` qui porte un TABLEAU ou un SCALAIRE (JSON parfaitement
    #    valide) fait lever `.get` sur autre chose qu'un dictionnaire. Sans
    #    elle, la gate mourait en Traceback SANS `BILAN` — c'est-a-dire avec
    #    la signature exacte d'une gate MORTE, qu'elle existe pour nommer.
    except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
        err_manifeste = "%s: %s" % (type(exc).__name__, str(exc)[:70])
    ctrl(err_manifeste is None and len(parts) == 4,
         "(c2) le manifeste se LIT et declare 4 morceaux",
         "4 morceaux declares" if err_manifeste is None and len(parts) == 4
         else "⛔ %s — la page n'aurait rien a poser"
              % (err_manifeste or "%d morceau(x) declare(s), attendu 4"
                 % len(parts)))

    # ── (c3) LA FAMILLE DE PUCE ───────────────────────────────────────────
    ctrl(chip == CHIP_ATTENDU, "(c3) `chipFamily` vaut exactement `ESP32-S3`",
         chip if chip == CHIP_ATTENDU
         else "⛔ %r — une autre famille fait refuser le flash, ou le rend "
              "fatal" % chip)

    # ── (c4) LES QUATRE OFFSETS, CONFRONTES A LEUR SOURCE DE VERITE ───────
    ref, source_ref, force = offsets_de_reference(f)
    ecarts_off = []
    if ref is None:
        ecarts_off.append("aucune source de verite lisible (%s)" % source_ref)
    else:
        vus = {}
        for pa in parts:
            vus[os.path.basename(pa.get("path") or "")] = pa.get("offset")
        for nom in IMAGES:
            if nom not in ref:
                ecarts_off.append("%s absent de la source de verite" % nom)
            elif vus.get(nom) != ref[nom]:
                ecarts_off.append("%s ⇒ %r au manifeste, %d (%#x) attendu"
                                  % (nom, vus.get(nom), ref[nom], ref[nom]))
    ctrl(not ecarts_off, "(c4) les 4 offsets EGALENT leur source de verite",
         "%s (confrontation %s) : %s"
         % (source_ref, force,
            " · ".join("%s=%d" % (n, ref[n]) for n in IMAGES) if ref else "—")
         if not ecarts_off
         else "⛔ %s — ⛔ ces quatre nombres ne se recopient pas, ils se LISENT"
              % " · ".join(ecarts_off))

    # ── (c5) ⛔ AUCUN BINAIRE FUSIONNE ────────────────────────────────────
    fusion = []
    for cible in (MANIFESTE, PAGE, PY, BAT):
        bas = f.get(cible, "").lower()
        for j in JETONS_FUSION:
            if j in bas:
                fusion.append("%s ⇒ %s" % (cible, j))
    ctrl(not fusion, "(c5) ⛔ aucun binaire FUSIONNE nulle part",
         "%d jeton(s) de fusion cherches, 0 trouve" % len(JETONS_FUSION)
         if not fusion
         else "⛔ %s — ce qui a ete mesure le 2026-08-31, ce sont QUATRE "
              "morceaux poses separement" % " · ".join(fusion))

    # ── (c6) CHAQUE CHEMIN EXISTE, ET SA TAILLE EST CELLE QUI EST PUBLIEE ─
    print("\n── (c6)(c7)(c8)(c9) LA CHARGE EST CELLE QUI EST ANNONCEE ─────────")
    publiees = {m.group(1): (int(m.group(2)), int(m.group(3)), m.group(4))
                for m in RE_PROV_LIGNE.finditer(prov)}
    ecarts_taille = []
    for pa in parts:
        nom = os.path.basename(pa.get("path") or "")
        brut = o.get("%s/%s" % (CHARGE, nom))
        if brut is None:
            ecarts_taille.append("%s : le fichier servi est ABSENT" % nom)
            continue
        if nom not in publiees:
            ecarts_taille.append("%s : aucune ligne dans `PROVENANCE.md`" % nom)
            continue
        off_pub, taille_pub, sha_pub = publiees[nom]
        if taille_pub != len(brut):
            ecarts_taille.append("%s : %d o servis, %d o publies"
                                 % (nom, len(brut), taille_pub))
        # 🔴 L'EMPREINTE, ⛔ PAS SEULEMENT LA TAILLE — ET C'EST UN TROU
        #    DEMONTRE. La 1re version depaquetait le SHA-256 publie puis ne
        #    s'en servait PAS : une image ECHANGEE a taille identique restait
        #    verte, pendant que `CHANGELOG.md` publiait que chaque image est
        #    verifiee « a la taille ET a l'empreinte ». Une propriete annoncee
        #    que rien ne joue est un chiffre a croire sur parole.
        sha_reel = hashlib.sha256(brut).hexdigest()
        if sha_reel != sha_pub:
            ecarts_taille.append("%s : sha256 servi %s…, publie %s…"
                                 % (nom, sha_reel[:12], sha_pub[:12]))
        if off_pub != pa.get("offset"):
            ecarts_taille.append("%s : offset %r au manifeste, %d publie"
                                 % (nom, pa.get("offset"), off_pub))
    ctrl(bool(parts) and not ecarts_taille,
         "(c6) chaque morceau fait sa taille ET son empreinte",
         "%d morceau(x) confrontes a `PROVENANCE.md` (taille + sha256)"
         % len(parts)
         if parts and not ecarts_taille
         else "⛔ %s — une provenance qui a pourri est pire qu'une provenance "
              "absente" % (" · ".join(ecarts_taille) or "aucun morceau"))

    # ── (c7) LA VERSION EST **LUE DANS LE BINAIRE SERVI** ─────────────────
    # 🔴 C'EST LE CONTROLE CENTRAL DE CETTE MARCHE. Une version annoncee est une
    #    intention ; le champ `esp_app_desc_t` est le PRODUIT. Les confronter,
    #    c'est la seule facon de refuser qu'une page annonce autre chose que ce
    #    qu'elle pose — et c'est exactement ce que le prototype a fait.
    binaire = o.get("%s/desknode.bin" % CHARGE)
    lue, projet = version_du_binaire(binaire)
    annoncee = (manifeste or {}).get("version")
    ctrl(lue is not None and annoncee == lue,
         "(c7) la version annoncee EST celle du binaire servi",
         "%s (projet %s), lue a l'offset %#x" % (lue, projet, APP_DESC_VERSION)
         if lue is not None and annoncee == lue
         else "⛔ %s — ⛔ une version se LIT dans le binaire, elle ne se recopie "
              "pas a cote"
              % (("le descripteur ne se lit pas : %s" % projet) if lue is None
                 else "manifeste %r, binaire %r" % (annoncee, lue)))

    # ── (c8) ⛔ JAMAIS LA VALEUR DU BANC D'ESSAI ──────────────────────────
    banc = (annoncee == VERSION_DU_BANC) or (VERSION_DU_BANC in f.get(MANIFESTE, ""))
    ctrl(not banc, "(c8) ⛔ la version n'est PAS celle du banc d'essai",
         "`%s` cherchee, absente" % VERSION_DU_BANC if not banc
         else "⛔ le manifeste porte `%s` — la valeur du BANC, publiee par le "
              "prototype du 2026-08-31 sur des images que plus personne ne "
              "savait dater" % VERSION_DU_BANC)

    # ── (c9) LA BANDE-ANNONCE D'INTEGRITE DE L'ASSET ─────────────────────
    brut_asset = o.get("%s/%s" % (CHARGE, ASSET_FICHIER))
    motif_asset = None
    if not brut_asset or len(brut_asset) < ASSET_QUEUE:
        motif_asset = "l'image est absente ou plus courte que sa queue"
    elif brut_asset[-ASSET_QUEUE:-8] != ASSET_MAGIE:
        motif_asset = "la magie %s manque" % ASSET_MAGIE.decode("ascii")
    else:
        longueur, crc = struct.unpack("<II", brut_asset[-8:])
        if longueur + ASSET_QUEUE != len(brut_asset):
            motif_asset = ("longueur incoherente : %d + %d annonces, %d o reels"
                           % (longueur, ASSET_QUEUE, len(brut_asset)))
        elif (zlib.crc32(brut_asset[:longueur]) & 0xFFFFFFFF) != crc:
            motif_asset = "CRC32 FAUX : l'image est ABIMEE"
    ctrl(motif_asset is None,
         "(c9) la bande-annonce de l'asset est VALIDE",
         "magie + longueur + CRC32 verifies sur %d o"
         % (len(brut_asset) if brut_asset else 0) if motif_asset is None
         else "⛔ %s — une image tronquee passait TOUS les controles du "
              "firmware avant que cette queue existe" % motif_asset)

    # ── (c10) LA VERSION D'ESP WEB TOOLS, EPINGLEE DES DEUX COTES ────────
    print("\n── (c10)(c11) CE QUE LA PAGE CHARGE, ET CE QU'ELLE SERT ──────────")
    src = RE_SRC_MODULE.search(page)
    url = src.group(1) if src else ""
    v_page = RE_EWT_PAGE.search(url)
    v_tiers = RE_EWT_TIERS.search(tiers)
    plage = RE_EWT_PLAGE.search(url)
    # 🔴 ET LES COPIES DE **PROSE** ENTRENT DANS L'EGALITE. Le numero epingle
    #    est publie dans CINQ endroits ; n'en garder que deux laissait les trois
    #    autres DERIVER en silence, et un lecteur du `README.md` aurait cru
    #    charger une version que la page ne charge pas.
    prose, copies = [], 0
    if v_page is not None:
        for cible in (LISEZMOI, JOURNAL, ROADMAP):
            for m in RE_VERSION_EWT.finditer(f.get(cible) or ""):
                copies += 1
                if m.group(1) != v_page.group(1):
                    prose.append("%s annonce %s" % (cible, m.group(1)))
    accord = (v_page is not None and v_tiers is not None
              and v_page.group(1) == v_tiers.group(1) and plage is None
              and not prose)
    ctrl(accord, "(c10) ESP Web Tools est EPINGLE, page ⇄ prose",
         "%s partout : page, inventaire, %d copie(s) de prose"
         % (v_page.group(1), copies) if accord
         else "⛔ %s — mesure du 2026-09-08 : la forme de PLAGE rend un 302 "
              "vers une version precise, donc elle epingle RIEN"
              % ("aucun `src` de module dans %s" % PAGE if not src
                 else "l'URL chargee ne porte aucune version exacte : %s" % url
                 if v_page is None else
                 "aucune version exacte dans %s" % TIERS if v_tiers is None
                 else "l'URL chargee porte une PLAGE : %s" % plage.group(0)
                 if plage is not None else
                 "copie(s) de prose DERIVANTE(S) : %s" % " · ".join(prose)
                 if prose else
                 "page %s, inventaire %s"
                 % (v_page.group(1), v_tiers.group(1))))

    # ── (c11) LES CHEMINS SERVIS SONT DANS LA LISTE BLANCHE ─────────────
    servis = getattr(produit, "SERVIS", {}) if produit else {}
    hors_liste = [a for a in att_servis if a not in servis]
    hors_racine = []
    base = os.path.abspath(RACINE) + os.sep
    for _u, valeur in servis.items():
        chemin = valeur[0] if isinstance(valeur, (tuple, list)) else valeur
        if not os.path.abspath(chemin).startswith(base):
            hors_racine.append(chemin)
    ctrl(bool(servis) and not hors_liste and not hors_racine,
         "(c11) les 6 adresses de charge sont dans SERVIS",
         "%d adresse(s) servies, toutes sous la racine" % len(servis)
         if servis and not hors_liste and not hors_racine
         else "⛔ %s — un chemin que la page demande et que le serveur ne "
              "connait pas rend un 404 AU MILIEU du flash"
              % (("le produit ne s'importe pas : %s" % err_produit)
                 if not servis else
                 "ABSENTE(S) de la liste blanche : %s" % " ".join(hors_liste)
                 if hors_liste else
                 "chemin(s) HORS racine : %s" % " ".join(hors_racine)))

    # ── (c12)…(c15) CE QUE LA PAGE DIT, ET QUAND ────────────────────────
    print("\n── (c12)…(c15) LA PAGE DIT CE QUI COINCE, AVANT QUE CA COINCE ────")
    pl_page = plat(page)
    deux_formes = (FORME_WINDOWS in pl_page and FORME_PUCE in pl_page)
    ctrl(deux_formes, "(c12) la page nomme les DEUX formes du nom du port",
         "« %s » et « %s »" % (FORME_WINDOWS, FORME_PUCE) if deux_formes
         else "⛔ il en manque une — Windows AFFICHE un nom traduit, la puce "
              "en annonce un autre, et ⛔ aucun des deux n'est « DeskNode »")

    deux_gestes = (GESTE_1 in pl_page.lower() and GESTE_2 in pl_page
                   and ECHEC_SELECTION in pl_page)
    ctrl(deux_gestes, "(c13) la page dit les DEUX gestes, et leur echec",
         "cliquer la ligne, puis `%s`" % GESTE_2 if deux_gestes
         else "⛔ le premier geste, le second, ou l'ecran de sortie qui les "
              "sanctionne manque — sans le second clic, le bouton reste grise")

    # ⚠️ LA RECUPERATION EST CELLE QUI EST **MESUREE** : `BOOT` maintenu PUIS
    #    `RESET`. La formule du cadrage — BOOT maintenu pendant le branchement —
    #    n'est ecrite NULLE PART au depot, et une page qui la recopierait
    #    publierait un geste que personne n'a joue.
    recup = (RECUP_BOOT in page and RECUP_RESET in page
             and "download" in pl_page.lower())
    ctrl(recup, "(c14) la page porte la recuperation MESUREE",
         "`%s` maintenu + `%s`, et le mode download nomme"
         % (RECUP_BOOT, RECUP_RESET) if recup
         else "⛔ la recuperation manque a la page — enterree dans un README "
              "de 200 Ko, elle n'existe pas au moment ou on en a besoin")

    # ⚠️ ON COMPARE A L'ELEMENT, ⛔ PAS A SON NOM CITE DANS UN COMMENTAIRE :
    #    le commentaire d'en-tete de la page le nomme, et une recherche naive le
    #    trouvait AVANT tout le corps du document — le controle jugeait alors
    #    « place apres » un avertissement qui est en realite juste au-dessus du
    #    bouton. Un controle qui mesure la prose ⛔ ne mesure pas la page.
    hors_win = (ANCRE_HORS_WINDOWS in page and "Windows" in page
                and ANCRE_ELEMENT in page
                and page.index(ANCRE_HORS_WINDOWS) < page.index(ANCRE_ELEMENT))
    ctrl(hors_win, "(c15) l'avertissement hors Windows precede le flash",
         "`%s` est place AVANT le bouton d'installation" % ANCRE_HORS_WINDOWS
         if hors_win
         else "⛔ absent, ou place APRES le bouton — un flash qui REUSSIT vers "
              "une dalle qui n'aura jamais rien a afficher")

    # ── (c16)(c17) D'OU VIENT CE QU'ON INSTALLE ─────────────────────────
    print("\n── (c16)(c17) LA PROVENANCE, ET CE QUE PERSONNE NE MECANISE ──────")
    # 🔴 L'OBLIGATION GPL-3.0 PORTE SUR **CETTE REVISION**, ⛔ pas sur « le
    #    depot » en general. Le pointeur est la revision LUE dans le binaire, et
    #    la page doit mener a l'endroit qui la nomme.
    pointe = ("PROVENANCE.md" in page and "GPL" in page)
    revision_ecrite = bool(lue) and lue in prov
    ctrl(pointe and revision_ecrite,
         "(c16) la page pointe la source de CETTE revision",
         "`PROVENANCE.md` nomme %s" % lue if pointe and revision_ecrite
         else "⛔ %s — « le depot » en general ⛔ n'est pas un pointeur de "
              "source au sens de la GPL-3.0"
              % ("la page ne mene pas a la provenance" if not pointe
                 else "la revision %r du binaire n'est pas ecrite dans %s"
                      % (lue, PROVENANCE)))

    # ⚠️ UN PORTEUR « A NOMMER » N'EST ⛔ PAS UN PORTEUR — lecon de `dn6-4`.
    pl_prov = plat(prov)
    porteurs = re.findall(r"[Pp]orteur[^:]{0,40}:\s*([^\n.·]{3,80})", pl_prov)
    # 🔴 CORRIGE APRES UN MUTANT SORTI **VERT**, ET SA QUESTION AVAIT POUR
    #    REPONSE « LA GARDE A UN TROU ». La 1re version comparait la clause
    #    ENTIERE a la liste des refus : « a nommer (la CI construit le
    #    firmware), aujourd'hui » n'y est EGAL a rien, donc elle passait — un
    #    porteur qui dit « a nommer » suivi de n'importe quoi echappait a la
    #    garde meme que `dn6-4` a payee. ⇒ on normalise la clause, puis on
    #    refuse aussi bien l'EGALITE que le DEBUT.
    def _normaliser(x):
        return re.sub(r"^[\s*`«»\u00ab\u00bb]+", "",
                      x.strip()).strip("*`« »").strip().lower()
    mauvais = []
    for x in porteurs:
        n = _normaliser(x)
        for refus in REFUS_PORTEUR:
            if not refus:
                continue
            if n == refus or n.startswith(refus + " ") or n.startswith(refus):
                mauvais.append(x.strip()[:40])
                break
    if not porteurs:
        mauvais = mauvais or []
    dit_non_mecanise = ("mécanisée par" in pl_prov or "mecanisee par" in pl_prov)
    ctrl(len(porteurs) >= 2 and not mauvais and dit_non_mecanise,
         "(c17) la non-mecanisation est ECRITE, avec ses porteurs",
         "%d porteur(s) nomme(s)" % len(porteurs)
         if len(porteurs) >= 2 and not mauvais and dit_non_mecanise
         else "⛔ %s — ⛔ un ecart sans porteur ECRIT est un oubli deguise, et "
              "« a nommer » n'est PAS un porteur"
              % ("la non-mecanisation n'est pas dite" if not dit_non_mecanise
                 else "porteur(s) refuse(s) : %s" % " · ".join(mauvais)
                 if mauvais else "%d porteur(s), il en faut 2 (la CI de build, "
                 "et la source publiquement atteignable)" % len(porteurs)))

    # ── (c18) ⛔ AUCUNE ELEVATION ────────────────────────────────────────
    print("\n── (c18)(c19) ⛔ PAS D'ELEVATION, ⛔ PAS DE PILOTE INUTILE ────────")
    eleves = []
    for cible in (PY, PAGE, BAT):
        for nom, motif in MOTIFS_ELEVATION:
            if motif.search(f.get(cible, "")):
                eleves.append("%s ⇒ %s" % (cible, nom))
    ctrl(not eleves, "(c18) ⛔ aucun jeton d'elevation dans le livre",
         "%d motif(s) cherches sur 3 fichiers" % len(MOTIFS_ELEVATION)
         if not eleves
         else "⛔ %s — la garde de l'outil de tache s'arrete sur tout niveau "
              "qui n'est pas limite : un installeur eleve ferait ECHOUER "
              "l'outil qui existe" % " · ".join(eleves))

    # ── (c19) LE MESSAGE PAR-DESSUS LE DIALOGUE DE PILOTES ──────────────
    pilotes = (all(x in page for x in PILOTES_INUTILES)
               and USB_NATIF.lower() in page.lower()
               and ANCRE_PILOTES in page)
    ctrl(pilotes, "(c19) la page refuse les pilotes reclames a tort",
         "les 3 pilotes sont nommes, et l'USB natif aussi" if pilotes
         else "⛔ le dialogue de secours envoie installer %s ; sans le message "
              "de la page par-dessus, un inconnu y perd du temps pour un "
              "probleme QU'IL N'A PAS" % " / ".join(PILOTES_INUTILES))

    # ── (c20)(c21) LE PORT SE DECOUVRE, ET LES CODES SONT DES FAITS ─────
    print("\n── (c20)(c21) LE PORT DECOUVERT, ET LES CODES DE `stop` ──────────")
    joue_port = jouer_port(produit, att_port) if produit else {
        "__erreur__": err_produit}
    ecarts_port = []
    if "__erreur__" in joue_port:
        ecarts_port.append("le produit n'a pas pu etre joue : %s"
                           % joue_port["__erreur__"])
    else:
        for cle, (motif, doit_etre_la) in sorted(att_port.items()):
            vu = motif in joue_port.get(cle, "")
            if vu != doit_etre_la:
                ecarts_port.append("%s ⇒ %r %s dans la commande"
                                   % (cle, motif, "absent" if doit_etre_la
                                      else "PRESENT"))
    ctrl(not ecarts_port, "(c20) `-Serie` est PASSE, et sur le port decouvert",
         "2 cas joues contre un double de papier" if not ecarts_port
         else "⛔ %s — sans `-Serie`, l'outil retombe sur son defaut code en "
              "dur, et rend « port disparu » alors que l'arret a eu lieu"
              % " · ".join(ecarts_port))

    joue_codes = jouer_codes(produit) if produit else {"__erreur__": err_produit}
    ecarts_codes = []
    if "__erreur__" in joue_codes:
        ecarts_codes.append("le produit n'a pas pu etre joue : %s"
                            % joue_codes["__erreur__"])
    else:
        for code, attendu in sorted(att_codes.items()):
            vu = (joue_codes.get(code) or (None, ""))[0]
            if vu != attendu:
                ecarts_codes.append("rc=%d ⇒ %r (attendu %r)"
                                    % (code, vu, attendu))
        etats = [v[0] for v in joue_codes.values() if isinstance(v, tuple)]
        if len(set(etats)) != len(etats):
            ecarts_codes.append("deux codes rendent le MEME etat : %s"
                                % " ".join(str(x) for x in etats))
    ctrl(not ecarts_codes, "(c21) les 4 codes de `stop` sont DISTINCTS",
         "0 rendu · 4 drapeau · 7 disparu · 8 tenu" if not ecarts_codes
         else "⛔ %s — `7` est le cas NORMAL d'une carte partie : le lire comme "
              "un echec et le lire comme un succes sont DEUX fautes"
              % " · ".join(ecarts_codes))

    # ── (c22) LES IMAGES SONT DECLAREES BINAIRES ────────────────────────
    print("\n── (c22)(c23) CE QUE GIT LIVRE, ET CE QUE LE PRE-VOL REND ────────")
    # ⚠️ RIEN NE DECLARAIT `*.bin` DANS CE DEPOT avant cette marche — mesure du
    #    2026-09-08. L'auto-detection de git est une HEURISTIQUE sur les
    #    premiers octets, ⛔ pas une garantie ; une substitution de fins de ligne
    #    rendrait les images INFLASHABLES, et personne ne le verrait avant la
    #    carte.
    regle_bin = re.search(r"^installeur/charge/\*\.bin\s+binary\s*$",
                          attributs, re.M)
    livre = ""
    try:
        r = subprocess.run(["git", "check-attr", "text", "--",
                            "%s/desknode.bin" % CHARGE], cwd=RACINE,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        livre = r.stdout if r.returncode == 0 else ""
    except OSError:
        livre = ""
    ctrl(bool(regle_bin) and "text: unset" in livre,
         "(c22) les images sont declarees BINAIRES a git",
         "`installeur/charge/*.bin binary`, et git le confirme"
         if regle_bin and "text: unset" in livre
         else "⛔ %s — l'auto-detection de git est une heuristique, ⛔ pas une "
              "garantie" % ("la regle manque a %s" % ATTRIBUTS
                            if not regle_bin
                            else "git rend %r" % livre.strip()[:60]))

    # ── (c23) LE PRE-VOL DE CHARGE REND SON CODE ────────────────────────
    pv = jouer_prevol(produit) if produit else {"__erreur__": err_produit}
    ecarts_pv = []
    if "__erreur__" in pv:
        ecarts_pv.append("le produit n'a pas pu etre joue : %s" % pv["__erreur__"])
    else:
        for cle, attendu in sorted(att_prevol.items()):
            if pv.get(cle) != attendu:
                ecarts_pv.append("%s ⇒ %r (attendu %r)" % (cle, pv.get(cle),
                                                           attendu))
    ctrl(not ecarts_pv, "(c23) le pre-vol rend `5` sur une charge absente",
         "2 cas joues : %s" % " · ".join("%s→%s" % (k, pv[k])
                                        for k in sorted(pv))
         if not ecarts_pv
         else "⛔ %s — un code publie que rien ne joue est un chiffre a croire "
              "sur parole" % " · ".join(ecarts_pv))

    # ── (c27) LES DEUX ETATS D'ECHEC NEUFS SONT DANS LA PAGE ────────────
    print("\n── (c27)…(c30) LES ETATS, LE PORT REEL, LA CHARGE, L'EFFACEMENT ──")
    # ⚠️ CES DEUX ANCRES ETAIENT DECLAREES ET GARDEES PAR RIEN — releve a la
    #    revue. Une constante qui a l'air d'un garde-fou et n'en est pas est
    #    pire qu'une absence : effacer l'un ou l'autre bloc de la page laissait
    #    la gate a 26 OK / 0 KO.
    etats = [n for n in (ANCRE_CDN, ANCRE_PORT_TENU) if n not in page]
    ctrl(not etats, "(c27) la page porte les etats `CDN` et `agent pose`",
         "`%s` et `%s`" % (ANCRE_CDN, ANCRE_PORT_TENU) if not etats
         else "⛔ ABSENT(S) : %s — sans le premier, une panne de module laisse "
              "un bouton inerte ; sans le second, le deuxieme lancement de tout "
              "le monde n'est explique nulle part" % " · ".join(etats))

    # ── (c28) `decouvrir_port` EST **REELLEMENT EXECUTEE** ──────────────
    # 🔴 TROU DEMONTRE A LA REVUE : (c20) et (c21) REMPLACENT cette fonction.
    #    Elle n'etait donc jouee par RIEN, et casser son motif d'extraction la
    #    faisait rendre `None` a chaque appel sans qu'aucune gate ne bouge —
    #    c'est-a-dire que la regression que cette marche declare corriger
    #    pouvait revenir EN SILENCE. Ici, seul l'appel systeme est double.
    jd = jouer_decouverte(produit, att_dec) if produit else {
        "__erreur__": err_produit}
    ecarts_dec = []
    if "__erreur__" in jd:
        ecarts_dec.append("le produit n'a pas pu etre joue : %s"
                          % jd["__erreur__"])
    else:
        for cle in sorted(att_dec):
            attendu = att_dec[cle][2]
            if jd.get(cle) != attendu:
                ecarts_dec.append("%s ⇒ %r (attendu %r)"
                                  % (cle, jd.get(cle), attendu))
    ctrl(not ecarts_dec, "(c28) `decouvrir_port` est REELLEMENT jouee",
         "%d cas joues sur la VRAIE fonction : %s"
         % (len(jd), " · ".join("%s→%r" % (k, jd[k]) for k in sorted(jd)))
         if not ecarts_dec
         else "⛔ %s — une fonction que tous les controles REMPLACENT n'est "
              "gardee par aucun d'eux" % " · ".join(ecarts_dec))

    # ── (c29) LA BRANCHE « CHARGE ABIMEE » EST **JOUEE SUR LE DISQUE** ──
    ja = jouer_charge_abimee(produit) if produit else {
        "__erreur__": err_produit}
    ecarts_ab = []
    if "__erreur__" in ja:
        ecarts_ab.append("le produit n'a pas pu etre joue : %s"
                         % ja["__erreur__"])
    else:
        if ja.get("complete") is not False:
            ecarts_ab.append("`complete` vaut %r sur une charge ABIMEE"
                             % ja.get("complete"))
        if "CRC32" not in (ja.get("asset") or ""):
            ecarts_ab.append("le verdict de l'asset ne nomme pas le CRC32 : %r"
                             % (ja.get("asset") or "")[:40])
        if ja.get("rc_prevol") != att_prevol.get("charge_absente"):
            ecarts_ab.append("le pre-vol rend %r (attendu %r)"
                             % (ja.get("rc_prevol"),
                                att_prevol.get("charge_absente")))
    ctrl(not ecarts_ab, "(c29) une charge ABIMEE est refusee, sur le disque",
         "un octet retourne ⇒ %r, pre-vol %r"
         % ((ja.get("asset") or "")[:34], ja.get("rc_prevol"))
         if not ecarts_ab
         else "⛔ %s — le `5` que le README et le `.bat` publient comme "
              "instrument mecanique deviendrait un chiffre a croire sur parole"
              % " · ".join(ecarts_ab))

    # ── (c30) L'EFFACEMENT AU PREMIER FLASH EST **EPINGLE** ────────────
    # ⚠️ Cette valeur decide si l'outil de flash PROPOSE d'effacer la carte au
    #    premier passage. Dans une marche qui justifie par la mesure la famille
    #    de puce, les quatre offsets, les 16 octets de queue et le numero
    #    epingle, elle etait la seule que rien n'expliquait et rien ne gardait.
    efface = (manifeste or {}).get("new_install_prompt_erase")
    dit = "new_install_prompt_erase" in prov
    ctrl(efface is False and dit,
         "(c30) l'effacement au 1er flash est epingle et ECRIT",
         "`false`, et `PROVENANCE.md` dit pourquoi" if efface is False and dit
         else "⛔ %s — une carte au decoupage etranger serait ecrasee EN PLACE, "
              "ou epargnee, sans que le motif soit ecrit nulle part"
              % ("le manifeste porte %r" % efface if efface is not False
                 else "`PROVENANCE.md` n'ecrit pas le motif"))

    if regles["sortie_anticipee"]:
        return bilan(0)

    # ── (c24)(c25)(c26) LA RECIPROQUE, MECANIQUE ────────────────────────
    print("\n── (c24)(c25)(c26) AUCUN CONTROLE GARDE PAR ZERO MUTANT ──────────")
    # 🔴 « N mutants, N vus rougir » prouve `mutant ⇒ rouge`, ⛔ JAMAIS
    #    `controle ⇒ couvert`. Les deux sens sont mesures, SEPAREMENT.
    lus_ast = ids_par_ast()
    reels = set(ids_emis) | (lus_ast or set())
    vises = set()
    for v in cibles.values():
        vises.update(v)
    nus = sorted(reels - vises, key=lambda s: (len(s), s))
    ctrl(not nus and lus_ast is not None,
         "(c24) chaque controle est vise par >= 1 mutant",
         "%d controle(s) lu(s) a l'AST, %d cible(s) declaree(s)"
         % (len(reels), len(vises)) if not nus and lus_ast is not None
         else ("⛔ %d CONTROLE(S) GARDE(S) PAR RIEN : %s"
               % (len(nus), " · ".join(nus)) if nus
               else "⛔ LA SOURCE NE S'ANALYSE PAS A L'AST — la population de "
                    "ce controle est INCONNUE, ⛔ pas vide"))
    perimees = sorted(vises - reels, key=lambda s: (len(s), s))
    ctrl(not perimees, "(c25) chaque cible de mutant est un controle REEL",
         "%d cible(s) confrontee(s)" % len(vises) if not perimees
         else "⛔ %d CIBLE(S) PERIMEE(S) : %s — un mutant qui vise un controle "
              "inexistant ⛔ ne garde rien"
              % (len(perimees), " · ".join(perimees)))
    orph = sorted(set(cibles) - set(MUTANTS))
    sans_cible = sorted(set(MUTANTS) - set(cibles))
    ctrl(not orph and not sans_cible,
         "(c26) `CIBLES` et `MUTANTS` se correspondent",
         "%d mutant(s), %d cible(s), cle a cle" % (len(MUTANTS), len(cibles))
         if not orph and not sans_cible
         else "⛔ cible(s) SANS mutant : %s · mutant(s) SANS cible : %s"
              % (orph or "—", sans_cible or "—"))

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : que le dialogue de port aille")
    print("   au bout. C'est un dialogue NATIF du navigateur, qu'aucun drapeau")
    print("   de ligne de commande ne pilote : il exige une main humaine, et il")
    print("   se joue en seance carte. Les relevés vivent sous `mesures/dn7-2/`.")
    return bilan(1 if ko_total[0] else 0)


if __name__ == "__main__":
    sys.exit(main())

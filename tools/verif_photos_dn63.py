#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn6-3 — LES PHOTOS NE PEUVENT PLUS DEVENIR ORPHELINES EN SILENCE.

======================= CE QUE CETTE GATE FAIT, ET POURQUOI =================

`docs/cablage/` porte les 20 photographies qui servent de BASE PROBANTE au
cablage : des serigraphies, des etats soudes, des pieges d'embase. Elles ne
valent que par ce qu'un document en DIT. Cette gate garde le LIEN entre les
fichiers et la prose, DANS LES DEUX SENS, et la COHERENCE des nombres que
`docs/cablage/PHOTOS.md` publie sur elles.

🔴 ELLE EXISTE PARCE QU'UN SENS N'ETAIT GARDE PAR PERSONNE. Mesure du
   2026-09-07 :
     · `verif_cablage_dn62.py` (c27) garde « toute photo CITEE existe », et
       seulement pour les photos que `docs/cablage.md` LIE ;
     · le sens inverse — « toute photo EXISTANTE est citee » — n'etait garde
       par RIEN ;
     · et **11 photos sur 20 ne sont citees QUE par `hardware/`**, que
       `verif_licences_dn52.py` (`prose_du_depot`) EXCLUT par ecrit.
   ⇒ deposer un fichier dans ce dossier sans le citer, ou retirer une photo
     que seul le journal de mesure nomme, ne faisait rougir AUCUNE gate.

── 🔴 ELLE CHERCHE LE **BASENAME**, ⛔ PAS LE CHEMIN — ET C'EST MESURE ──────

`hardware/…-capteurs-i2c.md` §13.0 cite ses photos comme des NOMS NUS entre
accents graves, dans des tables :

    | `2026-08-19_1720-….jpg` | 17:20:58 | … |

⛔ PAS comme des liens `](docs/cablage/…)`. Un controle ancre sur le prefixe
de chemin en raterait **20 sur 20** et declarerait **20 orphelines** — un
« N OK / 0 KO » sur une population FAUSSE, la classe de defaut que cette epic
a deja payee trois fois.

── LES DEUX TEMOINS NEGATIFS SONT DES CONTROLES DU CHEMIN NORMAL ───────────

⛔ Ils ne vivent PAS derriere un drapeau : `run_gates.sh` lance la gate SANS
   argument et `verif_campagne_dn56.py` ne decouvre que `--liste-mutants`.
   Un temoin derriere un drapeau n'est rejoue par PERSONNE — lecon `dn6-2`.

  (c4) LA CITATION TRONQUEE. `hardware/…-capteurs-i2c.md:2098` porte
       `docs/cablage/2026-08-16_2228-…jpg` : le nom y est coupe par une
       ELLIPSE, et il a meme perdu le point avant `jpg`. La citation
       COMPLETE de la l.209 suffit a cette photo. ⇒ un controle naif y verrait
       un LIEN MORT. Elle doit rester VERTE, et les DEUX sens sont verifies :
       elle est VUE, et elle est ECARTEE.
  (c5) LE NOM HORS DU DOSSIER. Le meme fichier cite `install_01.jpg` deux
       fois entre accents graves (l.4021 et l.4681) — une photo que l'owner a
       ENVOYEE, jamais versee au depot. Mettre « tout `*.jpg` cite » en
       population rougirait dessus : un FAUX KO sur de la prose JUSTE. ⇒ la
       population des noms nus est celle des noms A LA CONVENTION DU DOSSIER
       (`AAAA-MM-JJ_HHMM-<slug>.jpg`), et ce temoin le prouve DANS LES DEUX
       SENS lui aussi.

── ⛔ CE QU'ELLE NE FAIT PAS, ET C'EST LA MOITIE DU SUJET ──────────────────

⛔ **ELLE NE JUGE AUCUNE QUALITE D'IMAGE.** Elle ne sait pas si une
   serigraphie reste lisible apres recompression — c'est un jugement A L'OEIL,
   il appartient a l'owner, et `PHOTOS.md` le lui POSE au lieu de le supposer
   acquis. Elle ne lit ⛔ ni le PSNR ⛔ ni la qualite JPEG.
⛔ Elle ne MODIFIE aucun fichier : les photos et les `.md` sont ouverts en
   LECTURE SEULE, et les mutants vivent en MEMOIRE.
⛔ Elle ne dit RIEN de la PERTINENCE d'une citation : qu'un `.md` nomme une
   photo ne prouve pas qu'il la MONTRE. Le sens garde est l'EXISTENCE du
   lien, dans les deux directions.
⛔ Elle ne touche ⛔ ni `hardware/`, ⛔ ni `firmware/`, ⛔ ni `agent/`, et elle
   ne reorganise ⛔ aucun element du harnais.

── 🔴 POURQUOI `PHOTOS.md` EST EXCLUE DU CORPUS DE (c2) ────────────────────

`PHOTOS.md` NOMME les 20 photos : l'inclure rendrait (c2) VERTE POUR TOUJOURS,
sur n'importe quel dossier, y compris un dossier de photos que plus personne
n'utilise. ⇒ elle est EXCLUE, et (c2) mesure donc les citations REELLES. C'est
la meme classe de piege que « un vide n'est pas une absence de defaut » :
une gate qui se cite elle-meme ne garde plus rien.

── LA RECIPROQUE EST MECANIQUE, ⛔ PAS TENUE A LA MAIN ─────────────────────

Chaque mutant DECLARE le ou les controles qu'il vise (`CIBLES`), et TROIS
controles finaux confrontent cette table aux identifiants REELLEMENT emis :
  · (c20) aucun controle n'est garde par ZERO mutant ;
  · (c21) aucun mutant ne vise un controle INEXISTANT ;
  · (c22) `CIBLES` et `MUTANTS` se correspondent CLE A CLE.
⚠️ CE QUE (c20) NE PROUVE PAS : que le mutant rougisse BIEN le controle qu'il
   declare. Ca, c'est la campagne — `mesures/dn6-3/T2`, qui relit les lignes
   de signalement A COLONNE FIXE.

── CE QUE LA REVUE DU 2026-09-07 A AJOUTE, ET CE QUI RESTAIT VERT AVANT ────

Chaque controle ci-dessous ferme un trou MESURE, ⛔ pas suppose :

  (c23) un `.jpg` NON SUIVI copie dans le dossier faisait rougir (c16) avec
        « ANNONCE 12097898, MESURE 11659950 » : la gate accusait LE CHIFFRE
        PUBLIE alors que le parasite etait le fichier. La population vient de
        `git ls-files` ⇒ un intrus se NOMME comme intrus.
  (c24) un `.png` NON CITE laissait `22 OK, 0 KO` : le sens « toute photo du
        dossier est citee » ne couvrait AUCUN autre format.
  (c25) (c12) confronte la definition PUBLIEE a l'arbre ⇒ un
        redimensionnement ACCOMPAGNE d'une mise a jour de l'index restait
        VERT. Les 20 definitions de `T0` sont EPINGLEES ici, et c'est
        l'ARBRE qui leur est confronte.
  (c26) les deux chiffres d'OUVERTURE de la page n'etaient lus par personne :
        les reecrire en `99 860 048` / `1 octet` laissait `22 OK, 0 KO`.
  (c27) `PHOTOS.md` pouvait devenir la page ORPHELINE que `AC-G4` de `dn6-2`
        vient d'interdire : retirer ses deux liens entrants laissait les
        trois gates VERTES.
  (c28) les quatre chiffres que `CONTRIBUTING.md` REPUBLIE n'etaient gardes
        par rien : on pouvait y ecrire que le clone avait RETRECI — ce que
        (c18) interdit sur l'index — sans qu'aucune gate ne rougisse.
        🔴 REPUBLIER UN CHIFFRE ⛔ N'EST PAS LE RE-MESURER.

⚠️ ET DEUX MUTANTS MUTENT LES **OCTETS**, ⛔ PAS LE DICT PARSE :
   `lit_jpeg()`/`lit_ifd0()` sont l'instrument UNIQUE derriere (c12) a (c15)
   et (c25), et AUCUN mutant ne les touchait. Le 13 retire le segment APP1
   des octets, le 28 ecrit une definition fausse dans le SOF.
⚠️ ET (c15) PEUT SE CLORE : ecrit `bool(bloc) and …`, il rougissait « LA
   SECTION D'ECART A DISPARU » le jour ou l'owner reverse les deux EXIF
   manquants et retire une section devenue sans objet — il accusait un depot
   DEVENU CORRECT. « Pas d'ecart » est une reponse VALIDE.

── LA GARDE DU NO-OP EST UNIVERSELLE, ⛔ PAS UNE LISTE D'EXCEPTIONS ────────

🔴 TOUTE mutation passe par un SEUL etat (`prose`, `arbre`, `cibles`,
   `regles`), compare AVANT/APRES. Un mutant devenu sans effet — parce que son
   ancre litterale a bouge — se declare lui-meme en `rc=3` (mutant PERIME),
   ⛔ pas en `rc=1`. C'est mesure : `rc=1` + `BILAN` + un `[KO ]` est
   EXACTEMENT le contrat que `verif_campagne_dn56.py` appelle « sain » — un
   no-op le remplissait donc mot pour mot pendant que le controle qu'il
   gardait perdait son seul mutant EN SILENCE.
⛔ `verif_campagne_dn56.py` n'est PAS touchee : l'hygiene du harnais est hors
   perimetre.

Sortie : `BILAN : n OK, m KO`, rc 0 si tout passe, 1 sinon, 3 si le mutant
         demande n'a plus d'effet.
Usage  : python3 tools/verif_photos_dn63.py [--mutant <n>] [--liste-mutants]

⚠️ **UN MUTANT QUI DEBRANCHE LA GARDE NE PROUVE QUE SON EXISTENCE** (NFR7).
   Ceux d'ici REPLANTENT la faute REELLE — une photo qui perd sa citation, une
   citation qui perd sa cible, un index qui ment sur une taille, un EXIF
   efface, un gain annonce sans son cout.
"""

import argparse
import ast
import copy
import os
import re
import struct
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_PHOTOS = "docs/cablage"
INDEX_REL = "docs/cablage/PHOTOS.md"
JOURNAL = "hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md"

# Le nom d'une photo de CE dossier : horodatage + slug. ⛔ Pas « tout .jpg ».
# ⚠️ `re.I` N'EST PAS UN CONFORT : le dossier est peuple par EXTENSION insensible
#    a la casse (`.JPG` compte comme photo). Sans le drapeau, une photo `.JPG`
#    entrait dans l'arbre mais AUCUNE de ses citations n'etait reconnue ⇒ (c2)
#    la declarait ORPHELINE et le KO etait INSOLUBLE. ⛔ Les deux bouts du meme
#    controle doivent accepter la MEME population.
RE_CONVENTION = re.compile(
    r"(\d{4}-\d{2}-\d{2}_\d{4}-[A-Za-z0-9._+-]+\.jpe?g)\b", re.I)
# La forme LARGE que le mutant 5 replante : n'importe quel nom d'image.
RE_TOUT_JPG = re.compile(r"([A-Za-z0-9._+-]+\.jpe?g)\b", re.I)
# La forme CHEMIN : `docs/cablage/x.jpg` ou `](cablage/x.jpg)`.
RE_CHEMIN = re.compile(r"(?:docs/)?cablage/([^\s)`\"'\]]+)")
# Ce qui signe une TRONCATURE — l'ellipse typographique ou trois points.
MARQUES_TRONCATURE = ("…", "...")

# Les deux temoins negatifs, NOMMES : ils sont joues a CHAQUE passe.
TEMOIN_TRONQUEE = "2026-08-16_2228-"
TEMOIN_HORS_DOSSIER = "install_01.jpg"
# 🔴 LE TEMOIN DE (c5) EST ANCRE DANS UNE FIXTURE **DE CETTE MARCHE**, ⛔ PAS
#    DANS `hardware/`. Mesure du 2026-09-07 : `install_01.jpg` n'apparaissait
#    que dans `hardware/…-capteurs-i2c.md` (2 occurrences). Or `dn4-34` est un
#    porteur VIVANT dont le travail est de corriger ce dossier, et `AC6.2.5`
#    interdit a `dn6` d'y ecrire ⇒ le jour ou `dn4-34` passe, (c5) sortirait
#    « JAMAIS VU » et cette marche N'AURAIT PAS LE DROIT DE LA REPARER.
#    Patron : `tools/fixtures/`, deja employe par `verif_sr03.py`.
#    ⚠️ (c4) n'est PAS concerne : son temoin est aussi vu dans `README.md`.
FIXTURE_TEMOINS = "tools/fixtures/dn63-citations-temoins.md"

# Les ancres LITTERALES de `PHOTOS.md`. Une ancre qui bouge rend son mutant
# PERIME (rc=3) ⇒ elle se remarque, ⛔ elle ne pourrit pas en silence.
A_SECTION_CLONE = "Ce que cette curation N'A PAS allégé"
A_SECTION_EXIF = "deux photos ont déjà perdu leur EXIF"
A_SECTION_RETRAITS = "Les photos RETIRÉES"
A_PORTEUR = "Porteur de la réparation"
A_SEPARATEUR_INDEX = "|---|---|---|---|---|---:|---:|"
A_SECTION_ARBRE = "Ce que la curation a RENDU"
RE_LIEN_INDEX = re.compile(r"\]\(([^)]*PHOTOS\.md)\)")

# ── LES CHIFFRES QUE `CONTRIBUTING.md` REPUBLIE ───────────────────────────
# 🔴 ILS N'ETAIENT GARDES PAR RIEN : demontre le 2026-09-07, on pouvait y
#    ecrire que le clone avait RETRECI — exactement ce que (c18) interdit sur
#    `PHOTOS.md` — sans qu'aucune gate ne rougisse. Une page qui republie un
#    chiffre le REPUBLIE : elle ne le re-derive pas.
RE_CONTRIB_DOSSIER = re.compile(
    r"`docs/cablage/` went from \*\*[\d ]+ bytes\*\* to \*\*([\d ]+)\*\*")
RE_CONTRIB_PLUS_GROSSE = re.compile(
    r"largest file in the current tree is now that same photograph at "
    r"\*\*([\d ]+) bytes\*\*")
RE_CONTRIB_RENDU = re.compile(
    r"the working tree dropped by \*\*([\d ]+) bytes\*\*")
RE_CONTRIB_BUNDLE = re.compile(
    r"the isolated curation went from \*\*([\d ]+) bytes\*\* to "
    r"\*\*([\d ]+)\*\*, i\.e\. \*\*\+([\d ]+) bytes")

# 🔴 LA BORNE `T0` DES DEFINITIONS, EPINGLEE DANS LA GATE — ⛔ PAS DERIVEE DE
#    L'INDEX. (c12) confronte la definition PUBLIEE a l'arbre : un
#    redimensionnement futur accompagne d'une mise a jour de l'index resterait
#    VERT, alors que la contrainte est « la definition en pixels ⛔ ne change
#    pas » — parce que la SERIGRAPHIE est la valeur probante. (c25) confronte
#    donc l'arbre a une BORNE, ⛔ pas a ce que la page dit d'elle-meme.
#    ⚠️ Cette table est un ENGAGEMENT : une marche future qui redimensionne
#       DOIT la mettre a jour, et c'est exactement le but — le changement
#       devient un GESTE ECRIT, ⛔ pas une derive.
DEFINITIONS_T0 = {
    "2026-08-16_2140-bme680-recto-barrette-non-soudee.jpg": (4096, 3072),
    "2026-08-16_2228-carte-embases-jst-jumelles-i2c-uart.jpg": (3072, 4096),
    "2026-08-17_0012-breakout-ecarte-barrette-inseree.jpg": (3072, 4096),
    "2026-08-17_0012-cablage-4-fils-sous-tension.jpg": (3072, 4096),
    "2026-08-19_1718-tof050c-vl6180x-face-capteur-et-sachet-2.jpg":
        (3072, 4096),
    "2026-08-19_1718-tof050c-vl6180x-face-capteur-et-sachet.jpg": (3072, 4096),
    "2026-08-19_1719-ina219-cjmcu-recto-cavaliers-a0-a1-shunt-r100.jpg":
        (4096, 3072),
    "2026-08-19_1719-tof050c-vl6180x-face-broches-deux-barrettes.jpg":
        (3072, 4096),
    "2026-08-19_1719-tof050c-vl6180x-face-broches-et-sachet.jpg": (3072, 4096),
    "2026-08-19_1720-bh1750-gy302-face-broches-vcc-gnd-scl-sda-addr.jpg":
        (4096, 3072),
    "2026-08-19_1720-bh1750-gy302-face-composants-et-sachet.jpg": (4096, 3072),
    "2026-08-19_1720-bh1750-gy302-face-composants-serigraphie-v322.jpg":
        (4096, 3072),
    "2026-08-19_1720-ina219-cjmcu-verso-caracteristiques.jpg": (4096, 3072),
    "2026-08-20_0038-derivation-premier-pin-deux-fils-soudes.jpg":
        (2600, 1733),
    "2026-08-20_0058-derivation-quatre-cables-en-cours.jpg": (2600, 1733),
    "2026-08-20_0110-derivation-quatre-cables-finis-gaines.jpg": (2600, 1733),
    "2026-08-20_0116-bh1750-et-ina219-barrettes-SOUDEES.jpg": (2600, 1733),
    "2026-08-20_0116-ina219-et-tof050c-barrettes-SOUDEES.jpg": (2600, 1733),
    "2026-08-20_0951-montage-final-8-devices-grille-six-cases.jpg":
        (2600, 1733),
    "2026-08-20_0951-montage-final-en-main-les-quatre-modules.jpg":
        (2600, 1733),
}
RE_ECART_ARBRE = re.compile(r"l'arbre de travail \*\*rend ([\d ]+) octets\*\*")
RE_ECART_CLONE = re.compile(r"le clone \*\*COÛTE ([\d ]+) octets de plus\*\*")

LARGEUR_LIBELLE = 58  # la colonne de `ctrl()` — la cle que `T2` relit
MIN_GLOSE = 30        # ce qu'il faut pour qu'une case DISE ce qu'elle etablit

ok_total = [0]
ko_total = [0]
ids_emis = []

MUTANTS = {}                      # ⛔ AU NIVEAU MODULE — sinon `--liste-mutants`
CIBLES = {}                       # ⛔ AU NIVEAU MODULE — c'est la matiere de (c20)

MUTANTS[1] = ("efface d'un `.md` TOUTES les occurrences du nom d'une photo "
              "⇒ elle devient ORPHELINE, et personne ne le voyait")
# ⚠️ CIBLE DOUBLE, MESUREE : effacer les citations d'une photo rend AUSSI
#    fausse la case « qui la cite » de sa ligne d'index. La cible declaree
#    dit ce que le mutant FAIT, ⛔ pas ce qu'on aimerait qu'il isole.
CIBLES[1] = ("c2", "c10")
MUTANTS[2] = ("fait pointer une citation sur une photo INEXISTANTE "
              "(l'horodatage du nom est remplace)")
# ⚠️ CIBLE DOUBLE, MESUREE : deplacer la citation vers un nom inexistant
#    retire `docs/cablage.md` de la liste des citants de cette photo.
CIBLES[2] = ("c3", "c10")
# ⚠️ CIBLE DOUBLE, ET C'EST MESURE : desarmer la regle de troncature met la
#    citation coupee EN POPULATION — elle n'y resout pas. (c3) rougit avec
#    (c4), et la cible declaree dit la VERITE de ce que le mutant fait.
MUTANTS[3] = ("desarme la regle de TRONCATURE : la citation coupee de "
              "`hardware/` est prise pour un nom complet")
CIBLES[3] = ("c4", "c3")
MUTANTS[4] = ("ancre la population des citations sur le CHEMIN au lieu du "
              "BASENAME ⇒ les noms nus de `hardware/` ne comptent plus")
# ⚠️ CIBLE TRIPLE, MESUREE : sans l'ancrage par basename, les noms nus ne
#    sont plus RENCONTRES du tout — (c5) le dit alors sur sa branche
#    « instrument mort », et les listes de citants retrecissent avec.
CIBLES[4] = ("c2", "c5", "c10")
# ⚠️ CIBLE DOUBLE, MESUREE : elargir la convention fait entrer un nom qui
#    n'est PAS du dossier — il n'y resout donc pas non plus.
MUTANTS[5] = ("elargit la CONVENTION de nommage a « tout .jpg cite » ⇒ une "
              "photo qui n'est pas du depot entre en population")
CIBLES[5] = ("c5", "c3")
MUTANTS[6] = ("retire une photo de l'INDEX de `PHOTOS.md` (le fichier reste, "
              "plus personne ne dit ce qu'il etablit)")
# ⚠️ CIBLE TRIPLE, MESUREE : la ligne retiree portait aussi son `T0`, donc
#    l'ecart annonce cesse d'egaler la difference — dans l'index (c16) ET dans
#    la page qui le republie (c28).
CIBLES[6] = ("c7", "c16", "c28")
MUTANTS[7] = ("ajoute a l'INDEX une ligne pour une photo qui N'EXISTE PAS")
CIBLES[7] = ("c8",)
MUTANTS[8] = ("vide la case « ce qu'elle etablit » d'une ligne d'index "
              "(la photo est listee, elle n'est plus EXPLIQUEE)")
CIBLES[8] = ("c9",)
MUTANTS[9] = ("fait MENTIR une ligne d'index sur QUI cite la photo")
CIBLES[9] = ("c10",)
MUTANTS[10] = ("publie une TAILLE fausse dans l'index")
CIBLES[10] = ("c11",)
MUTANTS[11] = ("publie une DEFINITION fausse ⇒ un redimensionnement "
               "passerait inapercu, et c'est la valeur probante qui part")
CIBLES[11] = ("c12",)
MUTANTS[12] = ("publie un COMPTE DE TAGS EXIF faux")
CIBLES[12] = ("c13",)
# 🔴 IL MUTE LES **OCTETS**, ⛔ PAS LE DICT DEJA PARSE — et c'est une mesure :
#    ecrit sur le dict, il laissait `lit_jpeg()`/`lit_ifd0()`, instrument
#    UNIQUE de (c12) a (c15) et (c25), garde par RIEN.
MUTANTS[13] = ("RETIRE LE SEGMENT APP1 des octets d'une photo — la faute "
               "qu'une passe d'allegement anterieure a DEJA commise deux fois")
# ⚠️ CIBLE SEPTUPLE, MESUREE — ET C'EST LE SIGNE QUE LE MUTANT EST REALISTE :
#    retirer le segment APP1 des OCTETS ne supprime pas que des tags, ca ALLEGE
#    LE FICHIER. Une vraie passe d'effacement d'EXIF fait exactement ca. ⇒ le
#    compte de tags (c13), le bloc lui-meme (c14), l'horodatage (c15), la
#    taille publiee (c11), l'arithmetique (c16), les chiffres d'ouverture
#    (c26) et ceux que republie `CONTRIBUTING.md` (c28) rougissent TOUS. La
#    cible declaree dit ce que le mutant FAIT, ⛔ pas ce qu'on aimerait.
CIBLES[13] = ("c14", "c13", "c15", "c11", "c16", "c26", "c28")
MUTANTS[14] = ("retire le PORTEUR de l'ecart des deux photos sans "
               "horodatage ⇒ l'ecart n'est plus adresse a personne")
CIBLES[14] = ("c15",)
MUTANTS[15] = ("publie un ECART D'ARBRE qui ne tombe pas juste "
               "(le gain annonce cesse d'egaler la difference)")
CIBLES[15] = ("c16",)
MUTANTS[16] = ("supprime la section qui declare le COUT SUR LE CLONE ⇒ la "
               "page n'annonce plus qu'un gain")
# ⚠️ CIBLE DOUBLE, MESUREE : la table des bundles vit DANS cette section —
#    la supprimer prive (c18) de sa matiere, et il le DIT.
CIBLES[16] = ("c17", "c18")
MUTANTS[17] = ("publie un bundle d'APRES plus PETIT que celui d'AVANT — "
               "le gain fantasme que `NFR6.3` rend impossible")
# ⚠️ CIBLE DOUBLE, MESUREE : la paire de bundles est republiee dans
#    `CONTRIBUTING.md`, et (c28) confronte les deux pages entre elles.
CIBLES[17] = ("c18", "c28")
MUTANTS[18] = ("vide le MOTIF de la liste des retraits ⇒ une case cochee "
               "sur du vide")
CIBLES[18] = ("c19",)
MUTANTS[19] = ("rend `PHOTOS.md` VIDE (une gate qui ne trouve rien ⛔ ne "
               "sort pas verte)")
CIBLES[19] = ("c6",)
MUTANTS[20] = ("rend le dossier de photos VIDE ⇒ ⛔ un vide n'est pas une "
               "absence de defaut")
CIBLES[20] = ("c1",)
# 🔴 LES QUATRE DERNIERS NE MUTENT ⛔ PAS LA PROSE : ils replantent la faute
#    DANS LA MATIERE QUE (c20)/(c21)/(c22)/(z) LISENT. C'est exactement ce
#    qu'une future marche ferait en ajoutant un controle sans mutant.
#    ⛔ Ils ne DEBRANCHENT rien : la garde reste entiere, la faute est reelle.
MUTANTS[21] = ("retire une cible de `CIBLES` ⇒ un controle garde par ZERO "
               "mutant, le risque que `dn6-1` avait paye")
CIBLES[21] = ("c20",)
MUTANTS[22] = ("declare dans `CIBLES` un controle INEXISTANT (`c99`) ⇒ une "
               "cible PERIMEE, que « N mutants, N rouges » ne verrait pas")
CIBLES[22] = ("c21",)
MUTANTS[23] = ("declare une cible pour un mutant qui N'EXISTE PAS "
               "(`CIBLES` et `MUTANTS` cessent de se correspondre)")
CIBLES[23] = ("c22",)
MUTANTS[24] = ("replante une SORTIE ANTICIPEE NON DECLAREE : le bilan "
               "retrecit, et il sortirait VERT")
CIBLES[24] = ("z",)
MUTANTS[25] = ("depose dans le dossier un fichier NON SUIVI ⇒ un parasite "
               "que la gate doit NOMMER, ⛔ pas convertir en faux calcul")
CIBLES[25] = ("c23",)
# ⚠️ CIBLE QUINTUPLE, MESUREE : un fichier d'un autre format verse au dossier
#    n'est pas qu'un format inconnu — il n'est CITE nulle part, il n'a PAS de
#    ligne d'index, et il change les sommes. Les cinq rougissent, et c'est la
#    VERITE de ce que le mutant fait. C'est exactement le defaut mesure : un
#    `.png` non cite ne faisait rougir PERSONNE.
MUTANTS[26] = ("verse au dossier un fichier d'un AUTRE FORMAT (un `.png`) "
               "⇒ hors du sens « toute photo du dossier est citee »")
CIBLES[26] = ("c24", "c2", "c7", "c16", "c26", "c28")
MUTANTS[27] = ("declare un mutant dont le CORPS LEVE ⇒ un mutant MORT, qui "
               "sortirait en Traceback SANS `BILAN` s'il n'etait pas rattrape")
CIBLES[27] = ("c0",)
# ⚠️ CIBLE DOUBLE, MESUREE : une definition lue FAUSSE dans les octets ment a
#    la fois a l'index (c12) et a la borne epinglee (c25).
MUTANTS[28] = ("ALTERE LES OCTETS du segment SOF d'une photo ⇒ le parseur "
               "rend une definition FAUSSE, et c'est lui qui est garde ici")
CIBLES[28] = ("c12", "c25")
MUTANTS[29] = ("fausse le POIDS DU DOSSIER annonce en ouverture de la page "
               "(§1) — un chiffre que ⛔ personne ne confrontait")
CIBLES[29] = ("c26",)
MUTANTS[30] = ("fausse LA PLUS GROSSE PHOTO annoncee en ouverture (§1)")
CIBLES[30] = ("c26",)
MUTANTS[31] = ("retire de la prose TOUS les liens entrants vers l'index ⇒ "
               "la page orpheline que `AC-G4` de `dn6-2` vient d'interdire")
CIBLES[31] = ("c27",)
MUTANTS[32] = ("fait dire a `CONTRIBUTING.md` que le clone a RETRECI — ce "
               "que (c18) interdit sur l'index, et que rien ne gardait ici")
CIBLES[32] = ("c28",)

# ⚠️ LE COMPTE DU CHEMIN NORMAL, hors le controle final qui le confronte.
#    Il se PERIME si on ajoute un controle sans le mettre a jour — et c'est
#    voulu : c'est ce qui rend (z) FALSIFIABLE.
CONTROLES_PREVUS = 28

_MUTANT = 0

RE_ID_CTRL = re.compile(r"\((\w+)\)")


def ctrl(ok, libelle, detail=""):
    """UNE assertion, UNE ligne, UN identifiant. ⛔ Aucun controle muet.

    ⚠️ L'IDENTIFIANT VIT DANS LE LIBELLE, ⛔ pas dans un argument a part :
       `verif_campagne_dn56.py` lit les libelles A L'AST en prenant `args[1]`
       de chaque `ctrl(...)`. Une signature `ctrl(cid, ok, libelle)` mettrait
       le booleen en `args[1]` et retrecirait SILENCIEUSEMENT la population
       de cette gate-la. ⛔ Une gate ne retrecit pas l'instrument d'une autre.
    ⚠️ Le libelle est imprime a COLONNE FIXE (58) : c'est la cle que la
       campagne de `mesures/dn6-3/T2` relit pour attribuer chaque signalement
       a son controle. ⛔ Un libelle qui deborde casse cette lecture EN
       SILENCE — d'ou l'assertion ci-dessous, seul endroit du fichier ou un
       defaut de PROGRAMMATION s'arrete bruyamment."""
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


# ═══════════════════ LIRE UN JPEG — STDLIB SEULE ═══════════════════════════
# ⚠️ ⛔ AUCUN `pip install` DANS CE DEPOT, et c'est ECRIT dans le workflow de
#    CI : « les gates tournent sur la stdlib ». Pillow et ImageMagick sont
#    presents sur le poste de l'auteur et ABSENTS du runner ⇒ les utiliser ici
#    ferait une gate qui passe chez l'auteur et pas ailleurs, c'est-a-dire le
#    defaut entier de `dn5-3`. L'en-tete JPEG se lit en 40 lignes.

SOF = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
       0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
TAG_DATETIME = 0x0132


def lit_ifd0(exif):
    """`(n_tags, horodatage)` du premier IFD — ⛔ rend `(0, "")` sur tout
    doute plutot que de deviner. Un EXIF illisible n'est pas un EXIF."""
    if len(exif) < 8:
        return 0, ""
    bo = exif[:2]
    if bo == b"II":
        e = "<"
    elif bo == b"MM":
        e = ">"
    else:
        return 0, ""
    try:
        off = struct.unpack(e + "I", exif[4:8])[0]
        n = struct.unpack(e + "H", exif[off:off + 2])[0]
    except (struct.error, IndexError):
        return 0, ""
    dt = ""
    for k in range(n):
        p = off + 2 + k * 12
        if p + 12 > len(exif):
            return 0, ""
        try:
            tag, _typ, cnt = struct.unpack(e + "HHI", exif[p:p + 8])
        except struct.error:
            return 0, ""
        if tag == TAG_DATETIME:
            try:
                vo = (struct.unpack(e + "I", exif[p + 8:p + 12])[0]
                      if cnt > 4 else p + 8)
            except struct.error:
                return 0, ""
            dt = exif[vo:vo + cnt].split(b"\x00")[0].decode("ascii", "replace")
    return n, dt.strip()


def lit_jpeg(octets):
    """`(largeur, hauteur, n_tags_exif, horodatage)` — ⛔ `None` si ce n'est
    pas un JPEG. Les marqueurs sont parcourus, ⛔ pas cherches au hasard."""
    if octets[:2] != b"\xff\xd8":
        return None
    i, w, h, exif, n = 2, 0, 0, b"", len(octets)
    while i + 3 < n:
        if octets[i] != 0xFF:
            i += 1
            continue
        m = octets[i + 1]
        if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        if m in (0xD9, 0xDA):
            break
        taille = struct.unpack(">H", octets[i + 2:i + 4])[0]
        corps = octets[i + 4:i + 2 + taille]
        if m in SOF and len(corps) >= 5:
            h, w = struct.unpack(">HH", corps[1:5])
        elif m == 0xE1 and corps[:6] == b"Exif\x00\x00":
            exif = corps[6:]
        i += 2 + taille
    tags, dt = lit_ifd0(exif)
    return w, h, tags, dt


# ═══════════════════════ LIRE LE DEPOT ═════════════════════════════════════

def _texte_litteral(n):
    """La partie LITTERALE d'un libelle, meme construit par formatage.

    ⚠️ Les libelles `(c0)` sont bati au `%` A L'EXECUTION : sans cette
       resolution, l'AST n'en tirerait AUCUN identifiant, et (c20) declarerait
       `c0` inexistant alors qu'il est bien emis."""
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Mod, ast.Add)):
        return _texte_litteral(n.left)
    if isinstance(n, ast.JoinedStr) and n.values:
        return _texte_litteral(n.values[0])
    return None


def ids_par_ast():
    """Les identifiants de TOUS les `ctrl(...)` de CE fichier, lus A L'AST.

    🔴 POURQUOI PAS `set(ids_emis)` : ce set est fige AU MOMENT DE L'APPEL de
       (c20). Tout controle ajoute APRES ce bloc en sortait INVISIBLE a la
       reciproque — et `CONTROLES_PREVUS` ⛔ ne le rattrape pas, puisque
       l'auteur qui ajoute un controle l'incremente dans le meme geste.
       ⇒ la population de (c20) se lit dans la SOURCE, comme
         `verif_campagne_dn56.py` le fait deja pour les libelles.
    ⛔ Rend `None` si la source ne s'analyse pas : (c20) en fait un KO NOMME,
       ⛔ pas un vert par defaut."""
    try:
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            arbre_ast = ast.parse(fh.read())
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    out = set()
    for n in ast.walk(arbre_ast):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "ctrl" and len(n.args) >= 2):
            m = RE_ID_CTRL.match(_texte_litteral(n.args[1]) or "")
            if m:
                out.add(m.group(1))
    return out or None


def suivis():
    """Les fichiers TRACES, par `git ls-files`. ⛔ Pas un parcours du disque :
    un repertoire ignore n'est pas du depot. Rend `None` si git refuse."""
    try:
        r = subprocess.run(["git", "ls-files"], cwd=RACINE,
                           capture_output=True, text=True)
    except OSError:
        return None
    if r.returncode != 0:
        return None
    return [x for x in r.stdout.splitlines() if x.strip()]


def lit_octets(traces):
    """`{nom: octets}` — les fichiers du dossier **QUI SONT SUIVIS**.

    🔴 LA POPULATION EST CELLE DE `git ls-files`, ⛔ PAS `os.listdir` — ET
       C'EST UNE MESURE. Peuplee par le disque, un `.jpg` non suivi copie dans
       le dossier faisait rougir (c16) avec « ANNONCE 12097898, MESURE
       11659950 » : la gate accusait LE CHIFFRE PUBLIE alors que c'est le
       FICHIER PARASITE qui etait en trop. ⇒ un intrus se nomme comme intrus
       — (c23) — ⛔ il ne fait pas declarer l'arithmetique fausse.
    ⚠️ ⛔ AUCUN FILTRE D'EXTENSION ICI : le sens « toute photo du dossier est
       citee » doit couvrir TOUT fichier verse dans ce dossier, ⛔ pas les
       seuls `.jpg`. Un `.png` non cite y entrait sans faire rougir personne.
       C'est (c24) qui dit si le fichier est un JPEG lisible.
    """
    out = {}
    prefixe = DOSSIER_PHOTOS + "/"
    for rel in traces:
        if not rel.startswith(prefixe) or "/" in rel[len(prefixe):]:
            continue
        nom = rel[len(prefixe):]
        if nom.endswith(".md"):
            continue                      # l'index est de la prose, ⛔ pas une photo
        try:
            with open(os.path.join(RACINE, rel), "rb") as fh:
                out[nom] = fh.read()
        except OSError:
            out[nom] = b""
    return out


def lit_intrus(traces):
    """Les fichiers PRESENTS dans le dossier et ⛔ PAS SUIVIS — nommes comme
    tels. ⛔ Ils n'entrent dans AUCUN calcul : un parasite ⛔ ne rend pas fausse
    l'arithmetique d'une page qui, elle, dit vrai sur le depot."""
    plein = os.path.join(RACINE, DOSSIER_PHOTOS)
    if not os.path.isdir(plein):
        return []
    connus = {r[len(DOSSIER_PHOTOS) + 1:] for r in traces
              if r.startswith(DOSSIER_PHOTOS + "/")}
    try:
        return sorted(n for n in os.listdir(plein) if n not in connus)
    except OSError:
        return []


def arbre_de(octets):
    """`{nom: (w, h, tags, horodatage, taille, est_jpeg)}` — LU AUX OCTETS.

    ⚠️ C'est ici, et NULLE PART AILLEURS, que `lit_jpeg()`/`lit_ifd0()` sont
       exerces : ils sont l'instrument UNIQUE derriere (c12) a (c15) et (c25).
       ⇒ deux mutants (13 et 28) mutent les OCTETS **avant** ce parsing, pour
         que le parseur lui-meme soit garde et ⛔ pas seulement ses sorties."""
    out = {}
    for nom, brut in sorted(octets.items()):
        lu = lit_jpeg(brut)
        out[nom] = ((lu[0], lu[1], lu[2], lu[3], len(brut), True) if lu
                    else (0, 0, 0, "", len(brut), False))
    return out


def entier(s):
    """Un entier ECRIT — les espaces de milliers sont du FORMATAGE."""
    chiffres = re.sub(r"[^0-9]", "", s or "")
    return int(chiffres) if chiffres else None


def cellules(ligne):
    """Les cases d'une ligne de table markdown."""
    l = ligne.strip()
    if l.startswith("|"):
        l = l[1:]
    if l.endswith("|"):
        l = l[:-1]
    return [c.strip() for c in l.split("|")]


def tables(texte):
    """`[(entete, [ligne_de_corps])]` — les tables markdown du texte."""
    out, lignes = [], texte.split("\n")
    i = 0
    while i < len(lignes) - 1:
        if lignes[i].strip().startswith("|") and re.match(
                r"^\s*\|[\s:|-]+\|\s*$", lignes[i + 1]):
            ent, corps, j = cellules(lignes[i]), [], i + 2
            while j < len(lignes) and lignes[j].strip().startswith("|"):
                corps.append(lignes[j])
                j += 1
            out.append((ent, corps))
            i = j
        else:
            i += 1
    return out


def colonne(entete, mot):
    """L'indice de la colonne dont l'intitule contient `mot`. ⛔ Pas une
    position codee en dur : une colonne inseree ne doit pas decaler la
    lecture EN SILENCE."""
    for k, c in enumerate(entete):
        if mot in c.lower():
            return k
    return None


def bloc_section(texte, ancre):
    """Le corps de la section `## …` dont le TITRE contient `ancre`.
    ⛔ Rend `""` si le titre n'existe pas — une section absente est un fait,
    ⛔ pas une exception."""
    lignes = texte.split("\n")
    debut = None
    for i, l in enumerate(lignes):
        if l.startswith("#") and ancre in l:
            debut = i
            break
    if debut is None:
        return ""
    for j in range(debut + 1, len(lignes)):
        if lignes[j].startswith("## "):
            return "\n".join(lignes[debut:j])
    return "\n".join(lignes[debut:])


# ═══════════════ LA POPULATION DES CITATIONS, DANS LES DEUX SENS ═══════════

def citations(prose, regles, sauf=()):
    """`(resolvables, tronquees, hors_convention)`.

    · `resolvables`  : `{basename: [fichier]}` — ce qui DOIT exister.
    · `tronquees`    : les jetons coupes par une ellipse, ECARTES.
    · `hors_convention` : les noms d'image qui ⛔ n'appartiennent pas au
                       dossier — ECARTES eux aussi.
    ⚠️ Les trois sont RENDUS, ⛔ pas seulement le premier : un temoin negatif
       doit pouvoir prouver qu'un jeton a ete VU **et** ECARTE. Un jeton
       silencieusement ignore est indiscernable d'un jeton jamais rencontre.
    """
    resolvables, tronquees, hors = {}, [], []
    # ⚠️ 🔴 LE SCANNER EST LARGE, C'EST LA **REGLE** QUI FILTRE — ⛔ pas
    #    l'inverse. Mesure du 2026-09-07 : en scannant directement au motif
    #    ETROIT, `install_01.jpg` n'etait jamais RENCONTRE, et (c5) ne pouvait
    #    plus prouver qu'il etait ECARTE — il sortait « jamais vu », ce qui
    #    est indiscernable d'un instrument MORT. Un temoin negatif exige de
    #    VOIR le jeton pour temoigner qu'on l'ecarte.
    for nom, src in sorted(prose.items()):
        if nom in sauf:
            continue
        jetons = [(m.group(1), m.group(0)) for m in RE_CHEMIN.finditer(src)]
        if regles["basename"]:
            jetons += [(m.group(1), m.group(0))
                       for m in RE_TOUT_JPG.finditer(src)]
        for base, brut in jetons:
            base = base.rsplit("/", 1)[-1]
            coupe = any(t in brut or t in base for t in MARQUES_TRONCATURE)
            if coupe and regles["troncature"]:
                tronquees.append((nom, brut))
                continue
            if not coupe and not RE_CONVENTION.fullmatch(base):
                # ⛔ Un nom hors convention n'est PAS une citation de ce
                #    dossier — mais on le NOMME, pour que (c5) puisse le voir.
                hors.append((nom, base))
                if regles["convention"]:
                    continue
            resolvables.setdefault(base, []).append(nom)
    return resolvables, tronquees, hors


# ═══════════════════════════ LES MUTANTS ═══════════════════════════════════

def _sans_app1(brut):
    """Les memes octets, **SANS le segment APP1** (le bloc EXIF).

    ⛔ Ce n'est pas « mettre le compte de tags a zero » : c'est retirer la
       piece DES OCTETS, exactement ce qu'une passe d'allegement mal reglee
       fait. Le parseur doit le VOIR."""
    i, n, out = 2, len(brut), bytearray(brut[:2])
    while i + 3 < n:
        if brut[i] != 0xFF:
            out.append(brut[i])
            i += 1
            continue
        m = brut[i + 1]
        if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
            out += brut[i:i + 2]
            i += 2
            continue
        if m in (0xD9, 0xDA):
            break
        taille = struct.unpack(">H", brut[i + 2:i + 4])[0]
        if not (m == 0xE1 and brut[i + 4:i + 10] == b"Exif\x00\x00"):
            out += brut[i:i + 2 + taille]
        i += 2 + taille
    out += brut[i:]
    return bytes(out)


def _sof_menteur(brut):
    """Les memes octets, avec une DEFINITION FAUSSE ecrite dans le SOF."""
    i, n, out = 2, len(brut), bytearray(brut[:2])
    while i + 3 < n:
        if brut[i] != 0xFF:
            out.append(brut[i])
            i += 1
            continue
        m = brut[i + 1]
        if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
            out += brut[i:i + 2]
            i += 2
            continue
        if m in (0xD9, 0xDA):
            break
        taille = struct.unpack(">H", brut[i + 2:i + 4])[0]
        bloc = bytearray(brut[i:i + 2 + taille])
        if m in SOF and len(bloc) >= 9:
            bloc[5:9] = struct.pack(">HH", 1234, 5678)
        out += bloc
        i += 2 + taille
    out += brut[i:]
    return bytes(out)


# Un `.png` MINIMAL — signature + `IHDR` : assez pour n'etre PAS un JPEG.
PNG_BIDON = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
             b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00")


def muter(etat):
    """REPLANTE une faute DANS L'ETAT — ⛔ jamais dans un fichier du depot.

    🔴 TOUTE mutation passe par cet unique etat, et `main()` compare l'etat
       AVANT/APRES : la garde du no-op est donc UNIVERSELLE, ⛔ pas une liste
       d'exceptions a tenir a jour. Un mutant dont l'ancre litterale a bouge
       se declare PERIME (`rc=3`) au lieu de sortir « conforme ».
    """
    e = copy.deepcopy(etat)
    p, r = e["prose"], e["regles"]
    idx = INDEX_REL

    if _MUTANT == 1:
        # ⚠️ ⛔ PAS dans `PHOTOS.md` : la photo doit devenir orpheline pour
        #    (c2), ⛔ pas disparaitre de l'index — ca, c'est le mutant 6.
        cible = "2026-08-20_0951-montage-final-en-main-les-quatre-modules.jpg"
        for f in list(p):
            if f != idx:
                p[f] = p[f].replace(cible, "la photo du montage en main")
    elif _MUTANT == 2:
        p["docs/cablage.md"] = p["docs/cablage.md"].replace(
            "cablage/2026-08-16_2140-bme680-recto-barrette-non-soudee.jpg",
            "cablage/2026-08-16_9999-bme680-recto-barrette-non-soudee.jpg")
    elif _MUTANT == 3:
        r["troncature"] = False
    elif _MUTANT == 4:
        r["basename"] = False
    elif _MUTANT == 5:
        r["convention"] = False
    elif _MUTANT == 6:
        p[idx] = re.sub(
            r"(?m)^\| `2026-08-20_0058-derivation-quatre-cables-en-cours"
            r"\.jpg`.*\n", "", p[idx])
    elif _MUTANT == 7:
        # 🔴 IL VISE LE **SEPARATEUR DE L'INDEX**, ⛔ plus « la 1re occurrence
        #    d'un nom de photo » — ET C'EST UNE MESURE DU 2026-09-07 : ecrit
        #    ainsi, il inserait sa fausse ligne dans la table de l'ECART EXIF
        #    (§5), qui nomme la meme photo PLUS HAUT dans la page. La ligne
        #    partait donc dans une table SANS entete d'index, (c8) ne la lisait
        #    pas, et le mutant sortait **VERT** — ⛔ pas parce que la garde
        #    avait un trou, mais parce qu'il VISAIT A COTE. Un mutant a effet
        #    n'est ⛔ pas un mutant a effet UTILE.
        p[idx] = p[idx].replace(
            A_SEPARATEUR_INDEX,
            A_SEPARATEUR_INDEX
            + "\n| `2026-08-17_9999-photo-qui-n-existe-pas.jpg` | ce qu'elle "
              "etablit, en assez de mots pour passer le seuil de la glose | "
              "`cablage.md` | 100x100 | 0 | 1 | 1 |", 1)
    elif _MUTANT == 8:
        p[idx] = p[idx].replace(
            "Les **quatre câbles en cours** : on y compte les fils "
            "convergents de chaque faisceau.", "voir la photo")
    elif _MUTANT == 9:
        p[idx] = p[idx].replace(
            "| `2026-08-20_0058-derivation-quatre-cables-en-cours.jpg` | Les "
            "**quatre câbles en cours** : on y compte les fils convergents de "
            "chaque faisceau. | `ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md` |",
            "| `2026-08-20_0058-derivation-quatre-cables-en-cours.jpg` | Les "
            "**quatre câbles en cours** : on y compte les fils convergents de "
            "chaque faisceau. | `README.md` |")
    elif _MUTANT == 10:
        p[idx] = p[idx].replace("| 12 | 622912 | 622912 |",
                                "| 12 | 622912 | 999999 |")
    elif _MUTANT == 11:
        p[idx] = p[idx].replace("| 2600x1733 | 12 | 611092 |",
                                "| 1300x866 | 12 | 611092 |")
    elif _MUTANT == 12:
        p[idx] = p[idx].replace("| 2600x1733 | 12 | 491132 |",
                                "| 2600x1733 | 7 | 491132 |")
    elif _MUTANT == 13:
        cible = "2026-08-19_1720-ina219-cjmcu-verso-caracteristiques.jpg"
        e["brut"][cible] = _sans_app1(e["brut"][cible])
    elif _MUTANT == 14:
        p[idx] = p[idx].replace("**%s : l'owner**" % A_PORTEUR,
                                "la question reste ouverte")
    elif _MUTANT == 15:
        p[idx] = p[idx].replace("**rend 12 097 898 octets**",
                                "**rend 20 000 000 octets**")
    elif _MUTANT == 16:
        p[idx] = p[idx].replace(A_SECTION_CLONE, "Quelques remarques")
    elif _MUTANT == 17:
        p[idx] = p[idx].replace("| **33 548 491** octets | **43 713 244** "
                                "octets |",
                                "| **33 548 491** octets | **23 713 244** "
                                "octets |")
    elif _MUTANT == 18:
        p[idx] = p[idx].replace(
            "*(sans objet — 0 orpheline sur 20 au 2026-09-07)*", "—")
    elif _MUTANT == 19:
        p[idx] = ""
    elif _MUTANT == 20:
        e["brut"] = {}
    elif _MUTANT == 21:
        # ⚠️ LA VICTIME EST **DERIVEE**, ⛔ pas codee en dur : viser un mutant
        #    par son numero cesse de marcher le jour ou son controle gagne un
        #    SECOND gardien. On cherche un controle garde par EXACTEMENT UN
        #    mutant, et on vide CE gardien-la.
        compte = {}
        for _n, _v in e["cibles"].items():
            for _c in _v:
                compte[_c] = compte.get(_c, 0) + 1
        for _n, _v in sorted(e["cibles"].items()):
            if any(compte[_c] == 1 for _c in _v):
                e["cibles"][_n] = ()
                break
    elif _MUTANT == 22:
        e["cibles"][22] = tuple(e["cibles"][22]) + ("c99",)
    elif _MUTANT == 23:
        e["cibles"][99] = ("c9",)      # une cible pour un mutant INEXISTANT
    elif _MUTANT == 24:
        r["sortie_anticipee"] = True
    elif _MUTANT == 25:
        e["intrus"].append("2026-09-07_1200-copie-de-travail.jpg")
    elif _MUTANT == 26:
        e["brut"]["schema-du-cablage.png"] = PNG_BIDON
    elif _MUTANT == 27:
        # 🔴 IL LEVE EXPRES : c'est la faute « un mutant declare qui MEURT ».
        #    `main()` la rattrape et rend un `BILAN` — sans ce rattrapage, la
        #    gate sortirait en Traceback NU, indiscernable d'une gate morte.
        raise AssertionError("mutant 27 : corps volontairement LEVANT")
    elif _MUTANT == 28:
        cible = "2026-08-20_0110-derivation-quatre-cables-finis-gaines.jpg"
        e["brut"][cible] = _sof_menteur(e["brut"][cible])
    elif _MUTANT == 29:
        p[idx] = p[idx].replace("| **27 860 048** octets | **15 762 150** "
                                "octets |",
                                "| **27 860 048** octets | **9 999 999** "
                                "octets |")
    elif _MUTANT == 30:
        p[idx] = p[idx].replace("| **5 071 848** octets | **2 708 418** "
                                "octets |",
                                "| **5 071 848** octets | **1** octet |")
    elif _MUTANT == 31:
        for f in list(p):
            if f != idx:
                p[f] = p[f].replace("](cablage/PHOTOS.md)", "](le dossier)")
                p[f] = p[f].replace("](docs/cablage/PHOTOS.md)",
                                    "](le dossier)")
    elif _MUTANT == 32:
        # ⚠️ ANCRE **CONTIGUE** : la phrase est repliee sur trois lignes, et
        #    un litteral qui enjambe un retour a la ligne ⛔ ne matche pas —
        #    il rendait le mutant no-op (`rc=3`), ⛔ pas vert.
        p["CONTRIBUTING.md"] = p["CONTRIBUTING.md"].replace(
            "**43 713 244**, i.e. **+10 164 753 bytes",
            "**23 713 244**, i.e. **+10 164 753 bytes")
    else:
        raise AssertionError("mutant %d declare mais SANS CORPS" % _MUTANT)
    return e


# ═══════════════════════════ LES CONTROLES ═════════════════════════════════

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
        sys.exit("MUTANT %d INCONNU : il n'est pas declare. ⛔ Un mutant qui "
                 "n'existe pas ne prouve RIEN — ⛔ ne pas conclure que le "
                 "controle est vert." % args.mutant)
    _MUTANT = args.mutant or 0

    if args.liste_mutants:
        for n in sorted(MUTANTS):
            print("  %2d  %s" % (n, MUTANTS[n]))
        return 0

    print("=" * 78)
    print("dn6-3 — LES PHOTOS NE PEUVENT PLUS DEVENIR ORPHELINES EN SILENCE"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)
    print("cible      : %s/  +  %s" % (DOSSIER_PHOTOS, INDEX_REL))
    print("⛔ CETTE GATE NE JUGE AUCUNE QUALITE D'IMAGE — la lisibilite d'une "
          "serigraphie\n   est un jugement A L'OEIL, et il appartient a "
          "l'owner.")

    # ── la matiere ─────────────────────────────────────────────────────────
    traces = suivis()
    if traces is None:
        ctrl(False, "(c0) l'arbre trace est LISIBLE",
             "⛔ `git ls-files` a refuse — ⛔ pas de parcours de disque en "
             "remplacement : un repertoire ignore n'est pas du depot")
        return bilan(1, "l'arbre trace est illisible")
    prose = {}
    for f in traces:
        if not f.endswith(".md"):
            continue
        try:
            with open(os.path.join(RACINE, f), encoding="utf-8",
                      errors="replace") as fh:
                prose[f] = fh.read()
        except OSError:
            continue

    etat = {"prose": prose,
            "brut": lit_octets(traces),
            "intrus": lit_intrus(traces),
            "cibles": {n: tuple(v) for n, v in CIBLES.items()},
            "regles": {"basename": True, "troncature": True,
                       "convention": True, "sortie_anticipee": False}}

    # 🔴 UN MUTANT QUI MEURT SORTIRAIT EN TRACEBACK, SANS `BILAN` — or « pas
    #    de BILAN » est le discriminant d'une gate MORTE. ⇒ il se rend en KO.
    try:
        neuf = muter(etat) if _MUTANT else etat
    except Exception as exc:                              # noqa: BLE001
        ctrl(False, "(c0) le mutant %d a une CIBLE et un CORPS" % _MUTANT,
             "⛔ %s: %s — la faute est dans le MUTANT, ⛔ pas dans la gate"
             % (type(exc).__name__, str(exc)[:80]))
        return bilan(1, "le mutant %d n'a pas pu s'appliquer" % _MUTANT)
    # 🔴 UN MUTANT SANS EFFET EST INVISIBLE AU CONTRAT DE LA CAMPAGNE : le
    #    jour ou son ancre litterale bouge, la gate sort VERTE et la campagne
    #    accuse LA GATE. ⇒ il se declare lui-meme, et en `rc=3` — ⛔ pas
    #    `rc=1`, qui est MOT POUR MOT ce que la campagne appelle « sain ».
    if _MUTANT and neuf == etat:
        ctrl(False, "(c0) le mutant %d a bien un EFFET" % _MUTANT,
             "⛔ SANS EFFET — son ancre litterale a disparu de la cible. "
             "⛔ Ce n'est PAS un controle vert : rc=3, mutant PERIME.")
        return bilan(3, "le mutant %d n'a eu aucun effet" % _MUTANT)

    prose = neuf["prose"]
    # ⚠️ L'ARBRE EST DERIVE **APRES** LA MUTATION : c'est ce qui fait passer
    #    les mutants 13 et 28 PAR le parseur au lieu de le contourner.
    arbre = arbre_de(neuf["brut"])
    intrus, cibles, regles = neuf["intrus"], neuf["cibles"], neuf["regles"]

    # ── (c1) LE DOSSIER PORTE DES PHOTOS ───────────────────────────────────
    print("\n── (c1) LE DOSSIER DE PHOTOS N'EST PAS VIDE ──────────────────────")
    if not ctrl(bool(arbre), "(c1) le dossier de photos n'est pas vide",
                "%d photo(s), %d octets" % (len(arbre),
                                            sum(v[4] for v in arbre.values()))
                if arbre else
                "⛔ AUCUNE photo dans %s/ — ⛔ un vide n'est pas une absence "
                "de defaut" % DOSSIER_PHOTOS):
        return bilan(1, "le dossier de photos est VIDE")

    # ── (c2)(c3) LES DEUX SENS ─────────────────────────────────────────────
    print("\n── (c2)(c3) TOUTE PHOTO EST CITEE · TOUTE CITATION RESOUT ────────")
    # ⚠️ `PHOTOS.md` est EXCLUE : elle nomme les 20 par construction, et
    #    l'inclure rendrait (c2) verte pour toujours — y compris sur un
    #    dossier que plus personne n'utilise.
    resolvables, tronquees, hors = citations(prose, regles, sauf=(INDEX_REL,))
    orphelines = sorted(n for n in arbre if n not in resolvables)
    ctrl(not orphelines, "(c2) toute photo du dossier est CITEE quelque part",
         "%d photo(s), %d citee(s) hors de l'index" % (len(arbre),
                                                       len(resolvables))
         if not orphelines
         else "⛔ %d ORPHELINE(S) — ⛔ personne ne gardait ce sens : %s"
              % (len(orphelines), " · ".join(orphelines[:3])))

    mortes = sorted({"%s (cite par %s)" % (b, f[0])
                     for b, f in resolvables.items() if b not in arbre})
    ctrl(not mortes and bool(resolvables),
         "(c3) toute citation de photo RESOUT",
         "%d citation(s) distincte(s) confrontee(s)" % len(resolvables)
         if not mortes and resolvables
         else ("⛔ %d LIEN(S) MORT(S) : %s" % (len(mortes),
                                              " · ".join(sorted(mortes)[:3]))
               if mortes else "⛔ AUCUNE citation — ⛔ pas vert sur du vide"))

    # ── (c4)(c5) LES DEUX TEMOINS NEGATIFS, JOUES A CHAQUE PASSE ───────────
    print("\n── (c4)(c5) LES TEMOINS NEGATIFS — VUS **ET** ECARTES ────────────")
    vue = [t for t in tronquees if TEMOIN_TRONQUEE in t[1]]
    ctrl(bool(vue) and not any(TEMOIN_TRONQUEE in m for m in mortes),
         "(c4) la citation TRONQUEE est vue et ECARTEE",
         "%d citation(s) TRONQUEE(S) ecartee(s), dont le temoin (%s)"
         % (len(tronquees), os.path.basename(vue[0][0]))
         if vue and not any(TEMOIN_TRONQUEE in m for m in mortes)
         else ("⛔ VUE MAIS COMPTEE COMME LIEN MORT — un nom coupe par une "
               "ellipse ⛔ n'est pas une citation manquante" if vue
               else "⛔ JAMAIS VUE — l'instrument ne rencontre plus le jeton "
                    "qu'il pretend ecarter"))
    vu_hors = [h for h in hors if h[1] == TEMOIN_HORS_DOSSIER]
    # 🔴 LE TEMOIN DOIT ETRE VU **DEPUIS LA FIXTURE DE CETTE MARCHE** : ancre
    #    sur `hardware/` seul, il s'evaporait le jour ou `dn4-34` corrige ce
    #    dossier — et `AC6.2.5` interdit a `dn6` de l'y remettre.
    depuis_fixture = any(f == FIXTURE_TEMOINS for f, _b in vu_hors)
    ctrl(bool(vu_hors) and depuis_fixture
         and TEMOIN_HORS_DOSSIER not in resolvables,
         "(c5) un nom hors convention reste HORS population",
         "`%s` vu %d fois (dont la fixture), ⛔ pas mis en population"
         % (TEMOIN_HORS_DOSSIER, len(vu_hors))
         if vu_hors and depuis_fixture
         and TEMOIN_HORS_DOSSIER not in resolvables
         else ("⛔ `%s` EST EN POPULATION — il n'est pas de ce dossier, le "
               "faire resoudre est un FAUX KO sur de la prose JUSTE"
               % TEMOIN_HORS_DOSSIER if vu_hors and depuis_fixture
               else ("⛔ ABSENT DE `%s` — le temoin ne doit ⛔ PAS dependre "
                     "d'un fichier que cette marche n'a pas le droit "
                     "d'ecrire" % FIXTURE_TEMOINS if vu_hors
                     else "⛔ JAMAIS VU — l'instrument ne rencontre plus le "
                          "jeton qu'il pretend ecarter")))

    # ── (c23)(c24) LE DOSSIER NE PORTE QUE DES PHOTOS SUIVIES ET LISIBLES ──
    print("\n── (c23)(c24) NI INTRUS NON SUIVI, NI FORMAT INCONNU ─────────────")
    ctrl(not intrus, "(c23) le dossier ne porte AUCUN fichier NON SUIVI",
         "%d fichier(s) suivi(s), 0 intrus" % len(arbre) if not intrus
         else "⛔ %d INTRUS : %s — ⛔ il n'entre dans AUCUN calcul : un "
              "parasite ne rend pas fausse l'arithmetique d'une page qui dit "
              "vrai sur le DEPOT" % (len(intrus), " · ".join(intrus[:3])))
    inconnus = sorted(n for n, v in arbre.items() if not v[5])
    ctrl(not inconnus, "(c24) tout fichier suivi du dossier est un JPEG",
         "%d fichier(s), tous lus aux octets" % len(arbre) if not inconnus
         else "⛔ %d FORMAT(S) INCONNU(S) : %s — la definition et l'EXIF n'y "
              "sont ⛔ pas mesurables, et l'index ne sait pas les decrire"
              % (len(inconnus), " · ".join(inconnus[:3])))

    # ── (c6) L'INDEX EXISTE ────────────────────────────────────────────────
    print("\n── (c6) L'INDEX EXISTE ET N'EST PAS VIDE ─────────────────────────")
    page = prose.get(INDEX_REL, "")
    if not ctrl(bool(page.strip()), "(c6) PHOTOS.md existe et n'est pas vide",
                "%d caractere(s)" % len(page.strip()) if page.strip()
                else "⛔ %s est ABSENT ou VIDE — ⛔ pas de trace nue, un KO "
                     "nomme" % INDEX_REL):
        return bilan(1, "%s est absent ou vide" % INDEX_REL)

    if regles["sortie_anticipee"]:
        # 🔴 CE CHEMIN N'EXISTE QUE POUR ETRE VU ROUGIR : il rend un verdict
        #    SANS declarer qu'il a joue moins de controles que prevu. (z) le
        #    rattrape dans `bilan()`, et c'est ce qui le rend FALSIFIABLE.
        return bilan(0)

    # ── (c7)..(c13) L'INDEX DIT VRAI SUR CHAQUE PHOTO ──────────────────────
    print("\n── (c7)..(c13) L'INDEX DIT VRAI, LIGNE PAR LIGNE ─────────────────")
    lignes_idx = {}
    for ent, corps in tables(page):
        k_p = colonne(ent, "photo")
        k_e = colonne(ent, "établit")
        k_c = colonne(ent, "cite")
        k_d = colonne(ent, "définition")
        k_x = colonne(ent, "exif")
        k_0 = colonne(ent, "t0")
        k_7 = colonne(ent, "t7")
        if None in (k_p, k_e, k_c, k_d, k_x, k_0, k_7):
            continue
        for l in corps:
            c = cellules(l)
            if len(c) <= max(k_p, k_e, k_c, k_d, k_x, k_0, k_7):
                continue
            m = RE_TOUT_JPG.search(c[k_p])
            if not m:
                continue
            lignes_idx[m.group(1)] = dict(
                glose=c[k_e], cite=c[k_c], defi=c[k_d], tags=c[k_x],
                t0=c[k_0], t7=c[k_7])

    manquantes = sorted(n for n in arbre if n not in lignes_idx)
    ctrl(not manquantes and bool(lignes_idx),
         "(c7) l'index nomme TOUTES les photos de l'arbre",
         "%d ligne(s) d'index pour %d photo(s)" % (len(lignes_idx), len(arbre))
         if not manquantes and lignes_idx
         else ("⛔ %d PHOTO(S) SANS LIGNE : %s" % (len(manquantes),
                                                  " · ".join(manquantes[:3]))
               if manquantes else "⛔ INDEX ILLISIBLE — aucune ligne reconnue"))

    fantomes = sorted(n for n in lignes_idx if n not in arbre)
    ctrl(not fantomes, "(c8) l'index ne nomme AUCUNE photo absente",
         "%d ligne(s) confrontee(s) au dossier" % len(lignes_idx)
         if not fantomes
         else "⛔ %d LIGNE(S) FANTOME(S) : %s" % (len(fantomes),
                                                 " · ".join(fantomes[:3])))

    muettes = sorted(n for n, d in lignes_idx.items()
                     if n in arbre and len(re.sub(r"[`*🔴⚠️⛔ ]", "",
                                                  d["glose"])) < MIN_GLOSE)
    ctrl(not muettes, "(c9) chaque ligne dit CE QUE la photo etablit",
         "%d glose(s), seuil %d caracteres" % (len(lignes_idx), MIN_GLOSE)
         if not muettes
         else "⛔ %d LIGNE(S) MUETTE(S) : %s — une photo listee sans ce "
              "qu'elle etablit est un fichier, ⛔ pas une piece"
              % (len(muettes), " · ".join(muettes[:3])))

    # ⚠️ LA CLE DE COMPARAISON EST LE BASENAME : la gate le verifie UNIQUE
    #    avant de s'en servir. Deux `.md` homonymes rendraient la confrontation
    #    ambigue, et une ambiguite silencieuse est pire qu'un KO.
    # 🔴 LA POPULATION EST CELLE DES FICHIERS **QUI CITENT**, ⛔ PAS TOUTE LA
    #    PROSE — ET C'EST UNE MESURE, ⛔ pas un confort. Ce depot porte
    #    `README.md` DEUX fois (racine et `tests/`) et `PROVENANCE.md` DEUX
    #    fois (`mesures/dn4-8/` et `tools/fixtures/`) : la garde large
    #    ROUGISSAIT sur quatre fichiers qui ne citent AUCUNE photo, c'est-a-
    #    dire sur une population ou l'ambiguite ⛔ n'existe pas. Ce qui doit
    #    etre univoque, c'est la cle de CETTE confrontation — les noms qui
    #    peuvent apparaitre dans la colonne « qui la cite ».
    citants = sorted({f for v in resolvables.values() for f in v})
    bases = [os.path.basename(f) for f in citants]
    homonymes = sorted({b for b in bases if bases.count(b) > 1})
    faux_cite = []
    for n, d in sorted(lignes_idx.items()):
        if n not in arbre:
            continue
        reel = {os.path.basename(f) for f in resolvables.get(n, [])}
        dit = set(re.findall(r"`([^`]+\.md)`", d["cite"]))
        if reel != dit:
            faux_cite.append("%s : dit %s, mesure %s"
                             % (n, sorted(dit) or "—", sorted(reel) or "—"))
    ctrl(not faux_cite and not homonymes,
         "(c10) chaque ligne dit QUI la cite, et c'est vrai",
         "%d ligne(s), %d nom(s) de prose distincts" % (len(lignes_idx),
                                                        len(set(bases)))
         if not faux_cite and not homonymes
         else ("⛔ %d LIGNE(S) FAUSSE(S) : %s" % (len(faux_cite),
                                                 " · ".join(faux_cite[:2]))
               if faux_cite
               else "⛔ NOM(S) DE PROSE HOMONYME(S) : %s — la confrontation "
                    "par basename devient AMBIGUE" % " · ".join(homonymes)))

    faux_t, faux_d, faux_x, sans_exif = [], [], [], []
    for n, (w, h, tg, dt, oc, jpeg) in sorted(arbre.items()):
        d = lignes_idx.get(n)
        if d:
            if entier(d["t7"]) != oc:
                faux_t.append("%s : dit %s, pese %d" % (n, d["t7"], oc))
            # ⛔ La definition et l'EXIF ne se mesurent que sur un JPEG : les
            #    juger sur un autre format serait accuser (c12)/(c13) d'un
            #    defaut que (c24) nomme deja, et mieux.
            if jpeg and (d["defi"].strip().lower().replace("×", "x")
                         != "%dx%d" % (w, h)):
                faux_d.append("%s : dit %s, mesure %dx%d"
                              % (n, d["defi"], w, h))
            if jpeg and entier(d["tags"]) != tg:
                faux_x.append("%s : dit %s, porte %d" % (n, d["tags"], tg))
        if jpeg and tg == 0:
            sans_exif.append(n)
    ctrl(not faux_t, "(c11) la taille publiee EGALE celle de l'arbre",
         "%d taille(s) confrontee(s)" % len(lignes_idx) if not faux_t
         else "⛔ %d FAUSSE(S) : %s" % (len(faux_t), " · ".join(faux_t[:2])))
    ctrl(not faux_d, "(c12) la definition publiee EGALE celle de l'arbre",
         "%d definition(s) confrontee(s)" % len(lignes_idx) if not faux_d
         else "⛔ %d FAUSSE(S) : %s — une definition qui derive, c'est la "
              "SERIGRAPHIE qui part" % (len(faux_d), " · ".join(faux_d[:2])))
    ctrl(not faux_x, "(c13) le compte de tags EXIF publie EGALE le fichier",
         "%d compte(s) confronte(s)" % len(lignes_idx) if not faux_x
         else "⛔ %d FAUX : %s" % (len(faux_x), " · ".join(faux_x[:2])))

    # ── (c25) LA DEFINITION SE CONFRONTE A UNE **BORNE**, ⛔ PAS A LA PAGE ──
    # 🔴 (c12) confronte la definition PUBLIEE a l'arbre : un redimensionnement
    #    futur ACCOMPAGNE d'une mise a jour de l'index resterait VERT. Or la
    #    contrainte de cette marche est « la definition en pixels ⛔ ne change
    #    pas », parce que la SERIGRAPHIE est la valeur probante. ⇒ ici c'est
    #    l'arbre qui est confronte a la borne `T0` epinglee dans la gate.
    derive, absentes_t0 = [], []
    for n, (w, h) in sorted(DEFINITIONS_T0.items()):
        v = arbre.get(n)
        if v is None:
            absentes_t0.append(n)
        elif (v[0], v[1]) != (w, h):
            derive.append("%s : %dx%d, borne %dx%d" % (n, v[0], v[1], w, h))
    ctrl(not derive and not absentes_t0,
         "(c25) la definition de l'arbre EGALE la borne T0",
         "%d definition(s) epinglee(s) confrontee(s)" % len(DEFINITIONS_T0)
         if not derive and not absentes_t0
         else ("⛔ %d DEFINITION(S) DERIVEE(S) : %s — la serigraphie est la "
               "valeur probante" % (len(derive), " · ".join(derive[:2]))
               if derive
               else "⛔ %d PHOTO(S) DE LA BORNE ABSENTE(S) : %s"
                    % (len(absentes_t0), " · ".join(absentes_t0[:2]))))

    # ── (c14)(c15) L'EXIF EST UNE PIECE, ⛔ PAS UNE METADONNEE ─────────────
    print("\n── (c14)(c15) L'EXIF EST UNE PIECE — ET L'ECART SE DECLARE ───────")
    ctrl(not sans_exif, "(c14) chaque photo porte un bloc EXIF",
         "%d photo(s), toutes porteuses" % len(arbre) if not sans_exif
         else "⛔ %d SANS EXIF : %s — le journal de mesure publie leur "
              "horodatage et dit qu'elles en sont NOMMEES"
              % (len(sans_exif), " · ".join(sans_exif[:3])))
    # 🔴 DEUX PHOTOS ONT DEJA PERDU LEUR HORODATAGE AVANT CETTE MARCHE. La
    #    gate ⛔ ne le repare pas (les originaux sont chez l'owner) : elle
    #    exige que l'ecart soit DECLARE, avec un PORTEUR.
    sans_dt = sorted(n for n, v in arbre.items() if v[5] and not v[3])
    bloc = bloc_section(page, A_SECTION_EXIF)
    non_declarees = [n for n in sans_dt if n not in bloc]
    # 🔴 « PAS D'ECART » EST UNE REPONSE VALIDE. Ecrit `bool(bloc) and …`, ce
    #    controle rougissait « LA SECTION D'ECART A DISPARU » le jour ou
    #    l'owner reverse les deux EXIF manquants et retire une section devenue
    #    sans objet : la gate accusait un depot DEVENU CORRECT, et l'ecart ne
    #    pouvait JAMAIS se clore. ⇒ la section n'est exigee QUE s'il reste des
    #    photos sans horodatage.
    ok15 = (not sans_dt) or (bool(bloc) and not non_declarees
                             and A_PORTEUR in bloc)
    ctrl(ok15,
         "(c15) les photos SANS horodatage sont DECLAREES",
         ("aucune photo sans horodatage — l'ecart est CLOS, la section "
          "n'a plus d'objet" if not sans_dt
          else "%d photo(s) sans horodatage, toutes declarees avec leur "
               "porteur" % len(sans_dt))
         if ok15
         else ("⛔ LA SECTION D'ECART A DISPARU — un ecart tu n'est pas un "
               "ecart resolu" if not bloc
               else ("⛔ NON DECLAREE(S) : %s" % " · ".join(non_declarees[:3])
                     if non_declarees
                     else "⛔ AUCUN PORTEUR NOMME — un ecart sans porteur "
                          "n'est adresse a personne")))

    # ── (c16)..(c18) LE GAIN S'ECRIT AVEC SON COUT ─────────────────────────
    print("\n── (c16)(c17)(c18) LE GAIN S'ECRIT AVEC SON COUT ─────────────────")
    somme0 = sum(entier(d["t0"]) or 0 for n, d in lignes_idx.items()
                 if n in arbre)
    somme7 = sum(v[4] for v in arbre.values())
    m_arbre = RE_ECART_ARBRE.search(page)
    annonce = entier(m_arbre.group(1)) if m_arbre else None
    juste = annonce is not None and annonce == somme0 - somme7
    ctrl(juste, "(c16) le bilan T0 -> T7 est arithmetiquement juste",
         "%d - %d = %d octets rendus" % (somme0, somme7, annonce or 0)
         if juste
         else ("⛔ ANNONCE %s, MESURE %d — un gain annonce se DERIVE, ⛔ il ne "
               "se recopie pas" % (annonce, somme0 - somme7)
               if annonce is not None
               else "⛔ AUCUN ECART ANNONCE — la page ne chiffre pas ce "
                    "qu'elle a rendu"))

    bloc_clone = bloc_section(page, A_SECTION_CLONE)
    bundles = []
    for ent, corps in tables(bloc_clone):
        if colonne(ent, "avant") is None or colonne(ent, "après") is None:
            continue
        for l in corps:
            c = cellules(l)
            if "bundle" in c[0].lower() and len(c) >= 3:
                bundles = [entier(c[1]), entier(c[2])]
    ctrl(bool(bloc_clone) and len(bundles) == 2 and None not in bundles,
         "(c17) la page DECLARE le cout sur le clone",
         "bundle avant %d, apres %d" % tuple(bundles)
         if bloc_clone and len(bundles) == 2 and None not in bundles
         else ("⛔ LA SECTION A DISPARU — annoncer un gain sans son cout est "
               "exactement ce que cette marche existe pour empecher"
               if not bloc_clone
               else "⛔ LES DEUX BUNDLES NE SONT PAS LISIBLES — un cout "
                    "sans nombre n'est pas un cout"))
    m_clone = RE_ECART_CLONE.search(page)
    dit_clone = entier(m_clone.group(1)) if m_clone else None
    ok18 = (len(bundles) == 2 and None not in bundles
            and bundles[1] > bundles[0]
            and dit_clone == bundles[1] - bundles[0])
    ctrl(ok18, "(c18) le bundle publie APRES est PLUS GROS qu'AVANT",
         "+%d octets, et c'est le nombre annonce" % dit_clone if ok18
         else "⛔ %s — l'historique ne se reecrivant JAMAIS, alleger AJOUTE "
              "des objets : un clone qui retrecit signale un chiffre FAUX, "
              "⛔ pas un exploit"
              % ("apres <= avant" if len(bundles) == 2 and None not in bundles
                 and bundles[1] <= bundles[0]
                 else "l'ecart annonce %s ne vaut pas la difference"
                      % dit_clone))

    # ── (c19) LA LISTE DES RETRAITS PORTE SON MOTIF, MEME VIDE ─────────────
    print("\n── (c19) LA LISTE DES RETRAITS PORTE SON MOTIF ───────────────────")
    bloc_r = bloc_section(page, A_SECTION_RETRAITS)
    sans_motif, lues = [], 0
    for ent, corps in tables(bloc_r):
        k_m = colonne(ent, "motif")
        if k_m is None:
            continue
        for l in corps:
            c = cellules(l)
            lues += 1
            if k_m >= len(c) or len(re.sub(r"[`*—– ]", "", c[k_m])) < 5:
                sans_motif.append(c[0] if c else "?")
    ctrl(bool(bloc_r) and lues > 0 and not sans_motif,
         "(c19) la liste des retraits porte son MOTIF",
         "%d ligne(s), motif ecrit sur chacune" % lues
         if bloc_r and lues and not sans_motif
         else ("⛔ LA SECTION A DISPARU" if not bloc_r
               else ("⛔ %d SANS MOTIF : %s — ⛔ pas de case cochee sur du "
                     "vide" % (len(sans_motif), " · ".join(sans_motif[:2]))
                     if sans_motif
                     else "⛔ TABLE VIDE — meme zero retrait s'ecrit avec son "
                          "motif")))

    # ── (c26) LES CHIFFRES D'OUVERTURE DE LA PAGE ──────────────────────────
    print("\n── (c26) LES CHIFFRES D'OUVERTURE EGALENT L'ARBRE ────────────────")
    # 🔴 ILS N'ETAIENT CONFRONTES PAR RIEN — demontre le 2026-09-07 : les
    #    reecrire en `99 860 048` / `1 octet` laissait `22 OK, 0 KO`. (c11) ne
    #    lit que les lignes du §6, et (c16) que la phrase « rend … octets ».
    #    Un lecteur, lui, lit d'abord CES trois nombres-la.
    bloc_a = bloc_section(page, A_SECTION_ARBRE)
    lus, faux_ouverture = {}, []
    for ent, corps in tables(bloc_a):
        k7 = colonne(ent, "après")
        if k7 is None:
            continue
        for l in corps:
            c = cellules(l)
            if k7 >= len(c):
                continue
            cle = ("compte" if "fichiers" in c[0] else
                   "poids" if "poids" in c[0] else
                   "plus_grosse" if "plus grosse" in c[0] else None)
            if cle:
                lus[cle] = entier(c[k7])
    attendu = {"compte": len(arbre),
               "poids": sum(v[4] for v in arbre.values()),
               "plus_grosse": max((v[4] for v in arbre.values()), default=0)}
    for cle in sorted(attendu):
        if lus.get(cle) != attendu[cle]:
            faux_ouverture.append("%s : dit %s, mesure %d"
                                  % (cle, lus.get(cle), attendu[cle]))
    ctrl(not faux_ouverture and len(lus) == 3,
         "(c26) les chiffres d'ouverture EGALENT l'arbre",
         "%d chiffre(s) confronte(s) au dossier" % len(lus)
         if not faux_ouverture and len(lus) == 3
         else ("⛔ %d FAUX : %s" % (len(faux_ouverture),
                                   " · ".join(faux_ouverture[:3]))
               if faux_ouverture
               else "⛔ %d chiffre(s) d'ouverture LU(S) sur 3 — ⛔ pas vert "
                    "sur ce qu'on n'a pas trouve" % len(lus)))

    # ── (c27) L'INDEX N'EST PAS UNE PAGE ORPHELINE ─────────────────────────
    print("\n── (c27) L'INDEX EST LIE PAR UNE AUTRE PAGE ──────────────────────")
    # 🔴 `AC-G4` de `dn6-2` vient d'interdire la page orpheline, et rien ne
    #    l'appliquait a CELLE-CI : demontre, retirer ses deux seuls liens
    #    entrants laissait les trois gates VERTES.
    entrants = sorted(f for f, src in prose.items()
                      if f != INDEX_REL and RE_LIEN_INDEX.search(src))
    ctrl(bool(entrants), "(c27) l'index est LIE par au moins une autre page",
         "%d lien(s) entrant(s) : %s" % (len(entrants),
                                         " · ".join(entrants[:3]))
         if entrants
         else "⛔ AUCUN — sans lien, l'index est INTROUVABLE, et une page que "
              "personne ne lie est exactement ce que `dn6-2` vient d'interdire")

    # ── (c28) `CONTRIBUTING.md` REPUBLIE LES MEMES CHIFFRES ────────────────
    print("\n── (c28) LES CHIFFRES REPUBLIES AILLEURS SONT LES MEMES ──────────")
    # 🔴 DEMONTRE LE 2026-09-07 : on pouvait ecrire dans `CONTRIBUTING.md` que
    #    le clone avait RETRECI — exactement ce que (c18) interdit sur l'index
    #    — sans qu'AUCUNE des trois gates ne rougisse. Une page qui REPUBLIE un
    #    chiffre ne le re-derive pas : c'est ici qu'elle est confrontee.
    plat_c = re.sub(r"\s+", " ", prose.get("CONTRIBUTING.md", ""))
    faux_c = []
    for motif, cle, attend in (
            (RE_CONTRIB_DOSSIER, "poids du dossier", attendu["poids"]),
            (RE_CONTRIB_PLUS_GROSSE, "plus grosse", attendu["plus_grosse"]),
            (RE_CONTRIB_RENDU, "octets rendus", somme0 - somme7)):
        m = motif.search(plat_c)
        if m is None:
            faux_c.append("%s : ⛔ PHRASE ABSENTE" % cle)
        elif entier(m.group(1)) != attend:
            faux_c.append("%s : dit %s, mesure %d"
                          % (cle, m.group(1).strip(), attend))
    mb = RE_CONTRIB_BUNDLE.search(plat_c)
    if mb is None:
        faux_c.append("bundle : ⛔ PHRASE ABSENTE")
    else:
        av, ap, ec = (entier(mb.group(1)), entier(mb.group(2)),
                      entier(mb.group(3)))
        if len(bundles) == 2 and [av, ap] != bundles:
            faux_c.append("bundle : dit %s→%s, l'index dit %s→%s"
                          % (av, ap, bundles[0], bundles[1]))
        elif ap <= av or ec != ap - av:
            faux_c.append("bundle : %s→%s, ecart annonce %s" % (av, ap, ec))
    ctrl(not faux_c, "(c28) `CONTRIBUTING.md` republie les MEMES chiffres",
         "4 chiffre(s) republie(s) confronte(s)" if not faux_c
         else "⛔ %d DIVERGENCE(S) : %s — un chiffre republie ailleurs doit "
              "etre le MEME, ⛔ ou il n'est plus mesure"
              % (len(faux_c), " · ".join(faux_c[:2])))

    # ── (c20)(c21)(c22) LA RECIPROQUE, MECANIQUE ───────────────────────────
    print("\n── (c20)(c21)(c22) AUCUN CONTROLE GARDE PAR ZERO MUTANT ──────────")
    # 🔴 « N mutants, N vus rougir » prouve `mutant ⇒ rouge`, ⛔ JAMAIS
    #    `controle ⇒ couvert`. Les deux sens sont mesures, SEPAREMENT.
    # 🔴 `"z"` EN FAIT PARTIE : il n'est atteint par AUCUN chemin normal (il
    #    n'est emis que dans `bilan()`, et seulement en cas de defaut) ⇒ il
    #    est nomme ici, et le mutant 24 le fait rougir.
    # 🔴 `reels` SE LIT DANS LA SOURCE, ⛔ PAS DANS `ids_emis` — ET C'EST UNE
    #    MESURE : `set(ids_emis)` est fige AU MOMENT DE CET APPEL, donc tout
    #    controle ajoute APRES ce bloc en sortait INVISIBLE a la reciproque.
    #    Et `CONTROLES_PREVUS` ⛔ ne le rattrapait pas : l'auteur qui ajoute un
    #    controle l'incremente dans le meme geste. `verif_campagne_dn56.py`
    #    lit deja les libelles a l'AST ; on lit les identifiants de la meme
    #    facon, et `ids_emis` reste en UNION (un id emis mais illisible a
    #    l'AST reste compte).
    lus_ast = ids_par_ast()
    reels = set(ids_emis) | (lus_ast or set())
    vises = set()
    for v in cibles.values():
        vises.update(v)
    nus = sorted(reels - vises, key=lambda s: (len(s), s))
    ctrl(not nus and lus_ast is not None,
         "(c20) chaque controle est vise par >= 1 mutant",
         "%d controle(s) lu(s) a l'AST, %d cible(s) declaree(s)"
         % (len(reels), len(vises)) if not nus and lus_ast is not None
         else ("⛔ %d CONTROLE(S) GARDE(S) PAR RIEN : %s"
               % (len(nus), " · ".join(nus)) if nus
               else "⛔ LA SOURCE NE S'ANALYSE PAS A L'AST — la population de "
                    "ce controle est INCONNUE, ⛔ pas vide"))
    perimees = sorted(vises - reels, key=lambda s: (len(s), s))
    ctrl(not perimees, "(c21) chaque cible de mutant est un controle REEL",
         "%d cible(s) confrontee(s)" % len(vises) if not perimees
         else "⛔ %d CIBLE(S) PERIMEE(S) : %s — un mutant qui vise un "
              "controle inexistant ⛔ ne garde rien"
              % (len(perimees), " · ".join(perimees)))
    orphelins = sorted(set(cibles) - set(MUTANTS))
    sans_cible = sorted(set(MUTANTS) - set(cibles))
    ctrl(not orphelins and not sans_cible,
         "(c22) `CIBLES` et `MUTANTS` se correspondent",
         "%d mutant(s), %d cible(s), cle a cle" % (len(MUTANTS), len(cibles))
         if not orphelins and not sans_cible
         else "⛔ cible(s) SANS mutant : %s · mutant(s) SANS cible : %s"
              % (orphelins or "—", sans_cible or "—"))

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : que les photos soient")
    print("   LISIBLES. Une serigraphie illisible la laisse VERTE — c'est")
    print("   l'oeil de l'owner qui tranche, et `PHOTOS.md` le lui pose.")
    print("⛔ Ni que le mutant rougisse BIEN le controle qu'il declare : ca,")
    print("   c'est `mesures/dn6-3/T2`, qui relit A COLONNE FIXE les lignes")
    print("   de signalement de defaut.")
    return bilan(1 if ko_total[0] else 0)


if __name__ == "__main__":
    sys.exit(main())

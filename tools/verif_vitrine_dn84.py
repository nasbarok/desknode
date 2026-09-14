#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dn8-4 / AC8.4.3 · AC8.4.4 · AC8.4.6 — LA VITRINE EST LA SURFACE QU'UN INCONNU
TRAVERSE, ET ELLE EST GARDEE.

🎯 POURQUOI CETTE GATE EXISTE, ET C'EST UN PRIX ECRIT, ⛔ PAS UNE CONFIANCE.
   Le 2026-09-13, le `README.md` de la racine — un journal francais de
   257 192 o — est parti dans `docs/journal-de-bord.md`, octet pour octet. Les
   sept gates qui le lisaient ont ete REPOINTEES sur le journal, parce qu'elles
   gardent des phrases francaises EXACTES et portent des mutants ancres dessus.
   ⇒ elles ⛔ ne gardent PLUS ce qu'un inconnu lit. La vitrine anglaise qui
   prend la place a la racine n'etait gardee par RIEN : c'est cette gate.

── CE QU'ELLE LIT, ET CE QU'ELLE ⛔ NE LIT PAS — DECLARE EN PROPRE ──────────
   Elle lit la vitrine HORS BLOCS DE CODE : les titres ATX (`# …`), les images
   Markdown `![…](…)`, les paragraphes et les puces. Elle ⛔ ne lit NI le HTML
   brut, NI les titres setext, NI les liens de reference — et comme un
   aveuglement declare ⛔ ne doit pas etre EXERCE, (c3) ROUGIT des que la
   vitrine en contient. ⚠️ Le HTML se detecte a son OUVRANT (`<` suivi d'une
   lettre, `!` ou `/`), ⛔ pas a la balise entiere : une balise coupee sur deux
   lignes passait VERTE (revue du 2026-09-13). Cette declaration est IMPRIMEE a chaque tir
   (`AVEUGLEMENT_VITRINE`), ⛔ pas seulement ecrite ici.
   TOUTE image locale que la vitrine cite est lue OCTET PAR OCTET, par ses
   marqueurs JPEG : `SOF0/SOF2` pour les pixels ; ⛔ tout `APPn` autre qu'un
   `APP0 JFIF`, et tout segment `COM`, sont refuses (l'EXIF, l'XMP, un
   commentaire d'appareil). ⛔ Aucun Pillow : il est chez l'auteur, ⛔ pas sur
   le runner.
   🆕 AMENDE LE 2026-09-14 PAR `dn8-9` — le paragraphe ci-dessus est ⛔ NON
   EFFACE, et il n'est PLUS la regle entiere : « par ses marqueurs JPEG »
   decrivait une vitrine qui ne citait que des JPEG. La section `## Demo`
   cite trois GIF, et un GIF faisait ROUGIR (c5) (« pas un JPEG lisible »).
   ⇒ l'image est DISPATCHEE PAR SES OCTETS MAGIQUES, ⛔ par son extension :
     · `FF D8` ⇒ le chemin JPEG ci-dessus, A L'IDENTIQUE ;
     · `GIF87a` / `GIF89a` ⇒ lue BLOC PAR BLOC jusqu'au trailer `0x3B`
       (`structure_gif`) : ecran logique ET chaque image <= `PIXELS_MAX` ;
       extensions en LISTE BLANCHE — controle graphique `0xF9`, et
       application `NETSCAPE2.0` (la boucle) SEULE. ⛔ Tout le reste est
       refuse PAR SON NOM : commentaire `0xFE`, texte brut `0x01`, une autre
       application (un paquet XMP), une etiquette inconnue. C'est
       l'equivalent exact de « APP0 JFIF seul, 0 COM » : ce qui n'est ni des
       pixels ni la boucle est refuse, qu'on l'ait prevu ou non. Une structure
       TRONQUEE ou INCOHERENTE sort « pas un GIF lisible » ;
     · ni l'un ni l'autre ⇒ un KO NOMME (« ni JPEG ni GIF »).
   ⛔ AVEUGLEMENT DECLARE, ⛔ exerce par personne : les octets APRES le
   trailer `0x3B` ne sont pas lus — comme ceux apres `SOS` cote JPEG.

── LES SEIZE CONTROLES ──────────────────────────────────────────────────────
   (c1)  l'ORDRE statue : `# DeskNode` → la photo ACTIVE → la phrase
         « physical desktop dashboard » → les trois licences + `LICENSING.md`
         → ESP32-S3 + tactile + telemetrie PC + capteurs
   (c2)  ⛔ « CPU monitor » — le message n'est PAS celui-la (lu aussi sur le
         texte APLATI, sans `*` `_` ni accents graves)
   (c3)  ⛔ HTML brut · titre setext · lien de reference (l'aveuglement)
   (c4)  la vitrine tient sous `PLAFOND_VITRINE` octets
   (c5)  toute image locale citee est un JPEG lisible, ⛔ sans `APPn` hors
         `APP0 JFIF` ni `COM`, grand cote <= `PIXELS_MAX`
         🆕 amende le 2026-09-14 (`dn8-9`), la ligne ci-dessus ⛔ non effacee :
         JPEG **ou** GIF, dispatche par octets magiques — un GIF lisible
         jusqu'a son trailer, ⛔ sans extension hors `0xF9` et `NETSCAPE2.0`,
         ecran et images <= `PIXELS_MAX` ; ni JPEG ni GIF ⇒ KO nomme
   (c6)  toute image locale citee existe et pese moins de `PLAFOND_PHOTO` o
   (c7)  la photo de CONTEXTE suit la photo active, et sa legende ASSUME le
         prototype cable a nu et l'ecran en francais (`D24`, voie a)
   (c8)  les deux paliers, le point d'entree (cite ET present sur le disque),
         et la langue (anglais par defaut, francais selectionnable)
   (c9)  les known issues VRAIS : ~40 s, 335.8 ms contre 300 ms, AMD, Intel
         Arc — ⛔ « not perceptible »
   (c10) toute ligne qui nomme NVIDIA porte « not implemented » SUR ELLE
   (c11) le lien vers le journal existe, et sa cible aussi
   (c12) ⛔ aucun motif de `tools/verif_dossier_dn415.py` (sa clef est un
         CHEMIN : un motif dans la vitrine serait un fantome neuf)
   (c13) `## Install` porte la commande `GESTE_DEPENDANCES` du serveur local,
         LUE A L'AST (⛔ pas importee), et « V0.2 »
   (c14) chaque controle est vise par >= 1 mutant (ids lus a l'AST)
   (c15) chaque cible declaree est un controle REEL
   (c16) `CIBLES` et `MUTANTS` se correspondent, cle a cle

── CODES DE RETOUR ─────────────────────────────────────────────────────────
    0  N OK / 0 KO · 1  au moins un KO · 2  mutant inconnu
    3  mutant SANS EFFET (son ancre est absente) — ⛔ jamais un vert
"""

import argparse
import ast
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import dn_gates
    import verif_dossier_dn415 as dn415
except ImportError as _x:                                 # pragma: no cover
    sys.stderr.write(
        "⛔ un module FRERE est INTROUVABLE (%s) : `tools/dn_gates.py` porte les\n"
        "   helpers, `tools/verif_dossier_dn415.py` porte les motifs. Les deux\n"
        "   vivent DANS ce depot — c'est un defaut, ⛔ pas un prerequis.\n" % _x)
    sys.exit(1)

# ⛔ ALIAS, ⛔ PAS DES RE-DEFINITIONS (`verif_harnais_dn81.py` (c1d)).
ctrl = dn_gates.ctrl
bilan = dn_gates.bilan

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VITRINE = "README.md"
JOURNAL = "docs/journal-de-bord.md"
PHOTO_ACTIVE = "docs/photos/2026-08-30-1804-desknode-etat-actif-gros-plan.jpg"
PHOTO_CONTEXTE = "docs/photos/2026-08-30-1818-desknode-ambient-sur-la-tour.jpg"
PHOTOS = (PHOTO_ACTIVE, PHOTO_CONTEXTE)
ENTREE = "installeur/DeskNode-installeur.bat"
SERVEUR = "installeur/dn_installeur.py"
INSTALL_TITRE = "Install"
VERSION_EXE = "V0.2"

PLAFOND_VITRINE = 16000
# ⚠️ `CONTRIBUTING.md` publie « the largest file in the current tree … 2 708 418
#    bytes » : sous ce plafond, la phrase reste vraie.
PLAFOND_PHOTO = 600000
# Le grand cote PRESCRIT par le dossier de la marche (1 600 px).
PIXELS_MAX = 1600
# 🆕 dn8-9 — le GIF, lu par ses marqueurs. Les deux en-tetes de la norme, et
#    l'UNIQUE extension d'application admise : la boucle que `ffmpeg -loop 0`
#    ecrit (mesure le 2026-09-13 : `GIF89a`, 1 `NETSCAPE2.0`, un bloc `0xF9`
#    par image, 0 commentaire).
MAGIE_GIF = (b"GIF87a", b"GIF89a")
APPLI_GIF_PERMISE = b"NETSCAPE2.0"
NOMS_EXTENSIONS_GIF = {0xFE: "extension de commentaire 0xFE",
                       0x01: "extension de texte brut 0x01"}

AVEUGLEMENT_VITRINE = (
    "⛔ AVEUGLEMENT DECLARE : cette gate lit la vitrine HORS blocs de code — "
    "titres ATX, images `![…](…)`, paragraphes et puces. Elle ⛔ ne lit NI le "
    "HTML brut, NI les titres setext, NI les liens de reference : (c3) rougit "
    "des que la vitrine en contient, pour que ce trou ⛔ ne soit jamais EXERCE.")

LICENCES = ("GPL-3.0-or-later", "MIT", "CC-BY-SA-4.0")
PHRASE = "physical desktop dashboard"
MATERIEL = ("ESP32-S3", "touchscreen", "telemetry", "sensors")
PALIERS = ("**DeskNode**", "DeskNode + Ambiance")
LANGUE_TITRE = "Language"
LANGUE = ("starts in English", "French can be selected")
LEGENDE = ("prototype", "bare wiring", "no enclosure", "French")
KNOWN_ISSUES_TITRE = "Known issues"
KNOWN_ISSUES = ("~40 s", "335.8 ms", "300 ms", "AMD", "Intel Arc")
INTERDITS = {"c2": "cpu monitor", "c9": "not perceptible"}

RE_ATX = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
RE_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
RE_LIEN = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)\)")
RE_CLOTURE = re.compile(r"^ {0,3}(```|~~~)")
# ⚠️ L'OUVRANT SEUL, ⛔ pas `<…>` : une balise coupee sur deux lignes ⛔ ne porte
#    pas son `>` sur la ligne de son `<`, et passait VERTE (revue 2026-09-13).
RE_HTML = re.compile(r"<[A-Za-z!/]")
RE_SETEXT = re.compile(r"^ {0,3}(=+|-+)\s*$")
RE_CODE_EN_LIGNE = re.compile(r"`[^`]*`")
RE_REFERENCE = re.compile(r"^ {0,3}\[[^\]]+\]:\s*\S")
RE_AUTOLIEN = re.compile(r"<https?://")

# ══ LES MUTANTS — chacun REPLANTE une faute nommee ══════════════════════════
MUTANTS = {}
CIBLES = {}
MUTANTS[1] = "la photo passe APRES la phrase ⇒ l'ordre statue est inverse"
CIBLES[1] = ("c1",)
MUTANTS[2] = ("ajoute « a **CPU** monitor » a la phrase ⇒ le message qu'on "
              "refuse, CASSE par du gras — seul le texte APLATI le voit")
CIBLES[2] = ("c2",)
MUTANTS[3] = ("ajoute une balise `<img` COUPEE SUR DEUX LIGNES ⇒ du HTML que "
              "la gate ne lit pas, et dont le `>` n'est pas sur la ligne du `<`")
CIBLES[3] = ("c3",)
MUTANTS[4] = "gonfle la vitrine au-dela du plafond ⇒ ⛔ plus une vitrine"
CIBLES[4] = ("c4",)
MUTANTS[5] = "remplace la photo active par une version AVEC `APP1 Exif`"
CIBLES[5] = ("c5",)
MUTANTS[6] = "alourdit la photo de contexte au-dela du plafond"
CIBLES[6] = ("c6",)
MUTANTS[7] = "retire « French » de la legende ⇒ l'ecran francais n'est plus assume"
CIBLES[7] = ("c7",)
MUTANTS[8] = "fait demarrer l'ecran en francais ⇒ le defaut anglais disparait"
CIBLES[8] = ("c8",)
MUTANTS[9] = "retire la known issue des ~40 s a froid"
CIBLES[9] = ("c9",)
MUTANTS[10] = "deplace « not implemented » sur la ligne suivante de NVIDIA"
CIBLES[10] = ("c10",)
MUTANTS[11] = "casse le lien du journal ⇒ l'engineering log devient introuvable"
CIBLES[11] = ("c11",)
MUTANTS[12] = ("plante le 1er motif de la table de dn415 ⇒ une occurrence sous "
               "un chemin que son manifeste cle")
CIBLES[12] = ("c12",)
MUTANTS[13] = ("tronque la commande d'installation des modules ⇒ une vitrine "
               "qui fait installer la MOITIE de ce que l'agent importe")
CIBLES[13] = ("c13",)
MUTANTS[14] = ("vide la cible du mutant 1 ⇒ un controle garde par ZERO mutant")
CIBLES[14] = ("c14",)
MUTANTS[15] = ("declare dans `CIBLES` un controle INEXISTANT ⇒ une cible "
               "PERIMEE que « N rouges » ne voit pas")
CIBLES[15] = ("c15",)
MUTANTS[16] = ("declare une cible pour un mutant qui N'EXISTE PAS")
CIBLES[16] = ("c16",)
# 🆕 dn8-9 — QUATRE mutants pour les QUATRE regles neuves de (c5), chacun
#    REPLANTE sa faute dans le PREMIER GIF cite. ⚠️ (c14) garde « chaque
#    controle a un mutant », ⛔ pas « chaque regle » : un seul mutant aurait
#    laisse trois regles gardees par rien. Sans GIF cite ⇒ rc=3.
MUTANTS[17] = ("insere une EXTENSION DE COMMENTAIRE `21 FE` dans le 1er GIF "
               "cite ⇒ du texte hors pixels, que la liste blanche refuse")
CIBLES[17] = ("c5",)
MUTANTS[18] = ("insere une extension d'APPLICATION ETRANGERE `XMP DataXMP` "
               "dans le 1er GIF cite ⇒ ⛔ pas la boucle NETSCAPE2.0")
CIBLES[18] = ("c5",)
MUTANTS[19] = ("porte la LARGEUR DE L'ECRAN LOGIQUE du 1er GIF cite a "
               "PIXELS_MAX + 1 ⇒ grand cote au-dela du plafond")
CIBLES[19] = ("c5",)
MUTANTS[20] = ("TRONQUE le 1er GIF cite juste AVANT son trailer 0x3B ⇒ "
               "une structure qui ne se termine pas")
CIBLES[20] = ("c5",)
# 🆕 AMENDE LE 2026-09-14 A LA REVUE DE `dn8-9` — le commentaire ci-dessus
#    (« QUATRE mutants ») est ⛔ non efface, et il etait FAUX sur le fond : la
#    revue a affaibli deux branches de la lecture GIF sans qu'aucun des 20
#    mutants ne rougisse, et une NETSCAPE2.0 ou un 0xF9 portant une CHARGE en
#    plus passaient (c5) vert (seul le NOM de l'extension etait lu). ⇒ ONZE
#    mutants GIF (17 a 27), un par regle de la lecture, chacun REPLANTE sa
#    faute dans le 1er GIF cite.
MUTANTS[21] = ("ajoute un SOUS-BLOC DE CHARGE a la NETSCAPE2.0 du 1er GIF "
               "cite ⇒ la boucle transporte autre chose que la boucle")
CIBLES[21] = ("c5",)
MUTANTS[22] = ("ajoute un SOUS-BLOC DE CHARGE au 1er controle graphique 0xF9 "
               "du 1er GIF cite ⇒ plus que ses 4 octets")
CIBLES[22] = ("c5",)
MUTANTS[23] = ("porte la LARGEUR DU 1er DESCRIPTEUR D'IMAGE 0x2C du 1er GIF "
               "cite a PIXELS_MAX + 1, l'ecran logique restant valide")
CIBLES[23] = ("c5",)
MUTANTS[24] = ("insere une extension d'ETIQUETTE INCONNUE 0x77 dans le 1er "
               "GIF cite ⇒ ni controle, ni application, ni commentaire")
CIBLES[24] = ("c5",)
MUTANTS[25] = ("RETIRE tous les blocs du 1er GIF cite entre sa table globale "
               "et son trailer ⇒ un GIF a 0 image")
CIBLES[25] = ("c5",)
MUTANTS[26] = ("insere un OCTET DE TETE INCOHERENT 0x42 avant le 1er bloc du "
               "1er GIF cite")
CIBLES[26] = ("c5",)
MUTANTS[27] = ("remplace les 6 OCTETS MAGIQUES du 1er GIF cite par le debut de "
               "la signature PNG ⇒ ni JPEG ni GIF")
CIBLES[27] = ("c5",)
MUTANTS_GIF = tuple(range(17, 28))

CONTROLES_PREVUS = 16

_MUTANT = 0


class NonExerce(Exception):
    """Le mutant n'a rien change : son ancre est absente. ⇒ `rc=3`."""


def remplace(texte, ancre, par, n):
    if ancre not in texte:
        raise NonExerce("MUTANT %d NON EXERCE : l'ancre %r est ABSENTE de la "
                        "vitrine" % (n, ancre[:60]))
    return texte.replace(ancre, par, 1)


def muter_vitrine(txt):
    if _MUTANT == 1:
        m = RE_IMAGE.search(txt)
        i = txt.find(PHRASE)
        if not m or i < 0:
            raise NonExerce("MUTANT 1 NON EXERCE : image ou phrase absente")
        img = m.group(0)
        sans = txt[:m.start()] + txt[m.end():]
        fin_para = sans.find("\n\n", sans.find(PHRASE))
        return sans[:fin_para] + "\n\n" + img + sans[fin_para:]
    if _MUTANT == 2:
        return remplace(txt, PHRASE, PHRASE + " — a **CPU** monitor", 2)
    if _MUTANT == 3:
        return remplace(txt, "\n## ",
                        "\n<img\nsrc=\"%s\">\n\n## " % PHOTO_ACTIVE, 3)
    if _MUTANT == 4:
        return txt + "\n" + ("More prose. " * (PLAFOND_VITRINE // 12 + 1)) + "\n"
    if _MUTANT == 7:
        return remplace(txt, "speaks **French**", "speaks **English**", 7)
    if _MUTANT == 8:
        return remplace(txt, "The screen starts in **English**",
                        "The screen starts in **French**", 8)
    if _MUTANT == 9:
        lignes = txt.split("\n")
        garde = [l for l in lignes if "~40 s" not in l]
        if len(garde) == len(lignes):
            raise NonExerce("MUTANT 9 NON EXERCE : aucune ligne ne porte « ~40 s »")
        return "\n".join(garde)
    if _MUTANT == 10:
        return remplace(txt, "NVIDIA GPUs: **not implemented**",
                        "NVIDIA GPUs: see below\n  **not implemented**", 10)
    if _MUTANT == 11:
        return remplace(txt, "](docs/journal-de-bord.md)",
                        "](docs/journal-de-bord-ABSENT.md)", 11)
    if _MUTANT == 12:
        # ⚠️ LE MOTIF EST **LU** DANS LA TABLE DE dn415, ⛔ pas ecrit ici : ecrit
        #    en toutes lettres, il faisait de CE FICHIER une occurrence neuve que
        #    `verif_dossier_dn415.py` rougissait (mesure a la 1re redaction :
        #    23 OK / 12 KO au lieu de 10).
        return remplace(txt, "sits next to your PC",
                        "sits on the %s of your PC" % dn415.MOTIFS[0][0], 12)
    if _MUTANT == 13:
        return remplace(txt, "`pip install --user psutil pyserial`",
                        "`pip install --user psutil`", 13)
    return txt


def muter_cibles(cibles):
    """Les mutants de la RECIPROQUE, sur une COPIE de `CIBLES` — ⛔ jamais la table."""
    c = dict(cibles)
    if _MUTANT == 14:
        if not c.get(1):
            raise NonExerce("MUTANT 14 NON EXERCE : `CIBLES[1]` est deja vide")
        c[1] = ()
    if _MUTANT == 15:
        if 1 not in c:
            raise NonExerce("MUTANT 15 NON EXERCE : `CIBLES[1]` absent")
        c[1] = tuple(c[1]) + ("c99",)
    if _MUTANT == 16:
        if 999 in c:
            raise NonExerce("MUTANT 16 NON EXERCE : `CIBLES[999]` existe deja")
        c[999] = ("c1",)
    return c


def geste_du_serveur(source):
    """La valeur de `GESTE_DEPENDANCES`, LUE A L'AST — ⛔ jamais importee :
    importer le serveur local executerait son module, et une gate ⛔ ne lance
    pas le produit pour lire une constante."""
    try:
        arbre = ast.parse(source or "")
    except SyntaxError:
        return None
    for n in ast.walk(arbre):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) \
                and isinstance(n.value.value, str):
            for cible in n.targets:
                if isinstance(cible, ast.Name) and cible.id == "GESTE_DEPENDANCES":
                    return n.value.value
    return None


def aplati(txt):
    """Le texte sans retours a la ligne NI emphase NI accents graves : « **CPU**
    monitor » ou une phrase coupee en fin de ligne ⛔ n'echappent plus au motif."""
    return dn_gates.plat(re.sub(r"[*_`]", "", txt or "")).lower()


def muter_photo(rel, brut, premier_gif=None):
    if _MUTANT in MUTANTS_GIF and rel == premier_gif:
        return muter_gif(brut)
    if _MUTANT == 5 and rel == PHOTO_ACTIVE:
        if brut[:2] != b"\xff\xd8":
            raise NonExerce("MUTANT 5 NON EXERCE : la photo n'a pas de SOI")
        charge = b"Exif\x00\x00MM\x00*\x00\x00\x00\x08\x00\x00"
        return brut[:2] + b"\xff\xe1" + struct.pack(">H", len(charge) + 2) \
            + charge + brut[2:]
    if _MUTANT == 6 and rel == PHOTO_CONTEXTE:
        manque = PLAFOND_PHOTO - len(brut) + 1
        return brut + b"\x00" * max(manque, 1)
    return brut


def muter_gif(brut):
    """Les mutants 17 a 20 — chacun REPLANTE sa faute dans le 1er GIF cite.
    ⚠️ La position d'insertion et celle du trailer sont LUES par
    `structure_gif`, ⛔ supposees : un GIF sans table globale, ou suivi
    d'octets, deplacerait une position ecrite en dur.
    🆕 2026-09-14, revue : et les mutants 21 a 27 (`MUTANTS_GIF`) — leurs
    positions (fin de la NETSCAPE2.0, fin du 1er 0xF9, 1er descripteur 0x2C)
    sont celles que `structure_gif` a trouvees en MARCHANT les blocs."""
    g, _raison = structure_gif(brut)
    manque = g is None or (_MUTANT == 21 and g["fin_netscape"] is None) \
        or (_MUTANT == 22 and g["fin_controle"] is None) \
        or (_MUTANT == 23 and g["descripteur"] is None)
    if manque:
        raise NonExerce("MUTANT %d NON EXERCE : le 1er GIF cite n'est pas un "
                        "GIF lisible, ou n'a pas le bloc vise — la faute ne "
                        "peut pas etre REPLANTEE" % _MUTANT)
    p = g["debut_blocs"]
    if _MUTANT == 17:
        texte = b"dn8-9 mutant 17"
        return brut[:p] + b"\x21\xfe" + bytes([len(texte)]) + texte \
            + b"\x00" + brut[p:]
    if _MUTANT == 18:
        return brut[:p] + b"\x21\xff\x0bXMP DataXMP" + b"\x03xmp" + b"\x00" \
            + brut[p:]
    if _MUTANT == 19:
        return brut[:6] + struct.pack("<H", PIXELS_MAX + 1) + brut[8:]
    if _MUTANT in (21, 22):
        # le sous-bloc de charge s'insere JUSTE AVANT le terminal 0x00
        t = (g["fin_netscape"] if _MUTANT == 21 else g["fin_controle"]) - 1
        charge = b"dn8-9 mutant %d : charge hors pixels et hors boucle" % _MUTANT
        return brut[:t] + bytes([len(charge)]) + charge + brut[t:]
    if _MUTANT == 23:
        d = g["descripteur"]
        return brut[:d + 5] + struct.pack("<H", PIXELS_MAX + 1) + brut[d + 7:]
    if _MUTANT == 24:
        return brut[:p] + b"\x21\x77\x02ab\x00" + brut[p:]
    if _MUTANT == 25:
        return brut[:p] + brut[g["fin"]:]
    if _MUTANT == 26:
        return brut[:p] + b"\x42" + brut[p:]
    if _MUTANT == 27:
        return b"\x89PNG\r\n" + brut[6:]
    return brut[:g["fin"]]


# ══ LA LECTURE ══════════════════════════════════════════════════════════════

def elements(txt):
    """Les elements de la vitrine HORS blocs de code, dans l'ordre.

    Rend `(elements, horsportee)` : `elements` = [(ligne, genre, charge)] avec
    genre ∈ {"titre", "image", "texte"} ; `horsportee` = [(ligne, quoi)] — ce
    que la gate ⛔ ne sait pas lire, et qui ne doit donc PAS etre la."""
    out, hors = [], []
    dans_code = False
    lignes = txt.split("\n")
    precedente_texte = False
    for i, l in enumerate(lignes, 1):
        if RE_CLOTURE.match(l):
            dans_code = not dans_code
            precedente_texte = False
            continue
        if dans_code:
            continue
        if not l.strip():
            precedente_texte = False
            continue
        # ⚠️ LE CODE EN LIGNE N'EST PAS DU HTML : `http://127.0.0.1:<port>`
        #    n'est rendu que comme du texte par GitHub. ⇒ on le retire AVANT.
        nu_code = RE_CODE_EN_LIGNE.sub("", l)
        for m in RE_HTML.finditer(nu_code):
            if not RE_AUTOLIEN.match(nu_code, m.start()):
                hors.append((i, "HTML brut %r" % nu_code[m.start():m.start() + 40]))
        if RE_REFERENCE.match(l):
            hors.append((i, "lien de reference %r" % l.strip()[:40]))
        if precedente_texte and RE_SETEXT.match(l):
            hors.append((i, "titre setext %r" % l.strip()[:20]))
            precedente_texte = False
            continue
        m = RE_ATX.match(l)
        if m:
            out.append((i, "titre", (len(m.group(1)), m.group(2))))
            precedente_texte = False
            continue
        pos = 0
        for im in RE_IMAGE.finditer(l):
            if l[pos:im.start()].strip():
                out.append((i, "texte", l[pos:im.start()]))
            out.append((i, "image", (im.group(1), im.group(2))))
            pos = im.end()
        reste = l[pos:]
        if reste.strip():
            if l.lstrip().startswith("|"):
                out.append((i, "texte", reste))
            elif out and out[-1][1] == "texte" and out[-1][0] == i - 1 \
                    and not re.match(r"^\s*([-*+]|\d+\.)\s", l):
                out[-1] = (i, "texte", out[-1][2] + " " + reste)
            else:
                out.append((i, "texte", reste))
            precedente_texte = not l.lstrip().startswith("|")
        else:
            precedente_texte = False
    return out, hors


def segments_jpeg(brut):
    """[(marqueur, charge)] jusqu'a SOS — ⛔ Pillow n'est pas sur le runner."""
    if brut[:2] != b"\xff\xd8":
        return None
    out, i = [], 2
    while i + 4 <= len(brut):
        if brut[i] != 0xFF:
            return None
        m = brut[i + 1]
        if m == 0xFF:
            i += 1
            continue
        if m == 0x01 or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        (n,) = struct.unpack(">H", brut[i + 2:i + 4])
        out.append((m, brut[i + 4:i + 2 + n]))
        if m == 0xDA:
            return out
        i += 2 + n
    return None


def pixels(segs):
    for m, c in segs or ():
        if m in (0xC0, 0xC1, 0xC2) and len(c) >= 5:
            h, w = struct.unpack(">HH", c[1:5])
            return w, h
    return None


def _taille_table(packe):
    """Octets d'une table de couleurs, si le bit 7 du champ tasse la declare."""
    return 3 * 2 ** ((packe & 7) + 1) if packe & 0x80 else 0


def structure_gif(brut):
    """Le GIF lu BLOC PAR BLOC jusqu'a son trailer — 🆕 dn8-9, ⛔ Pillow n'est
    pas sur le runner.

    Rend ⛔ `None` si ce n'est pas un GIF LISIBLE : en-tete hors `GIF87a` /
    `GIF89a`, structure TRONQUEE (un bloc, un sous-bloc ou le trailer manque),
    octet de tete INCOHERENT, ou 0 image. Sinon un dict : `version`, `ecran`
    (largeur, hauteur de l'ecran logique), `images` [(largeur, hauteur)],
    `controles` (blocs `0xF9`), `netscape`, `intrus` (les extensions HORS
    liste blanche, NOMMEES), `debut_blocs` (1er octet apres la table globale)
    et `fin` (position du trailer `0x3B`).
    ⛔ Les octets APRES le trailer ne sont pas lus (aveuglement declare dans
    l'en-tete de ce fichier).
    🆕 AMENDE LE 2026-09-14 A LA REVUE — le paragraphe ci-dessus est ⛔ non
    efface, et deux de ses phrases ont change :
      · la fonction rend un COUPLE `(dict, None)` ou `(None, raison)` : les
        trois fautes « illisibles » (coupe, octet incoherent, 0 image)
        sortaient sous le MEME libelle, et un KO doit nommer SA faute ;
      · la liste blanche lit la FORME, ⛔ plus seulement le nom : `0xF9` =
        exactement un sous-bloc de 4 o ; `NETSCAPE2.0` = l'identifiant de
        11 o puis exactement un sous-bloc de 3 o dont le 1er octet vaut 0x01.
        Une charge en plus y passait VERTE (mesure par la revue). Tout autre
        forme est un intrus NOMME « malforme(e) ».
      · le dict porte aussi `fin_netscape`, `fin_controle` (position apres le
        terminal de la 1re NETSCAPE2.0 / du 1er 0xF9) et `descripteur` (le 1er
        0x2C), trouves en marchant — les positions des mutants 21 a 23."""
    if brut[:6] not in MAGIE_GIF or len(brut) < 13:
        return None, "en-tete ou ecran logique TRONQUE"
    largeur, hauteur, packe = struct.unpack("<HHB", brut[6:11])
    i = 13 + _taille_table(packe)
    g = {"version": brut[:6].decode("ascii"), "ecran": (largeur, hauteur),
         "images": [], "controles": 0, "netscape": 0, "intrus": [],
         "debut_blocs": i, "fin": None, "fin_netscape": None,
         "fin_controle": None, "descripteur": None}

    def sous_blocs(j):
        """(position apres le bloc terminal `0x00`, [sous-blocs]) — ou
        (None, …) si la chaine est coupee avant son terminal."""
        blocs = []
        while j < len(brut):
            n = brut[j]
            j += 1
            if n == 0:
                return j, blocs
            if j + n > len(brut):
                return None, blocs
            blocs.append(brut[j:j + n])
            j += n
        return None, blocs

    while True:
        if i >= len(brut):
            return None, "coupe AVANT le trailer 0x3B"
        tete = brut[i]
        if tete == 0x3B:
            g["fin"] = i
            break
        if tete == 0x2C:
            if i + 11 > len(brut):
                return None, "descripteur d'image 0x2C TRONQUE"
            _x, _y, iw, ih, p = struct.unpack("<HHHHB", brut[i + 1:i + 10])
            if g["descripteur"] is None:
                g["descripteur"] = i
            # descripteur (10 o), table locale, 1 o de taille LZW, sous-blocs
            i, _ = sous_blocs(i + 10 + _taille_table(p) + 1)
            if i is None:
                return None, "donnees d'image TRONQUEES"
            g["images"].append((iw, ih))
        elif tete == 0x21:
            if i + 2 > len(brut):
                return None, "extension TRONQUEE"
            etiquette = brut[i + 1]
            i, blocs = sous_blocs(i + 2)
            if i is None:
                return None, "extension 0x%02X TRONQUEE" % etiquette
            if etiquette == 0xF9:
                if len(blocs) == 1 and len(blocs[0]) == 4:
                    g["controles"] += 1
                else:
                    g["intrus"].append("controle graphique 0xF9 malforme "
                                       "(%s octets de sous-blocs)"
                                       % "+".join(str(len(x)) for x in blocs))
                if g["fin_controle"] is None:
                    g["fin_controle"] = i
            elif etiquette == 0xFF:
                ident = blocs[0] if blocs else b""
                if ident != APPLI_GIF_PERMISE:
                    g["intrus"].append("extension d'application %r"
                                       % ident[:11].decode("latin-1"))
                elif len(blocs) == 2 and len(blocs[1]) == 3 \
                        and blocs[1][0] == 0x01:
                    g["netscape"] += 1
                else:
                    g["intrus"].append("NETSCAPE2.0 malformee (%s octets de "
                                       "sous-blocs)"
                                       % "+".join(str(len(x)) for x in blocs))
                if ident == APPLI_GIF_PERMISE and g["fin_netscape"] is None:
                    g["fin_netscape"] = i
            else:
                g["intrus"].append(NOMS_EXTENSIONS_GIF.get(
                    etiquette, "extension inconnue 0x%02X" % etiquette))
        else:
            return None, "octet de tete incoherent 0x%02X a l'octet %d" % (tete, i)
    if not g["images"]:
        return None, "0 image avant le trailer"
    return g, None


def verdict_hors_jpeg(rel, brut):
    """(faute, detail) pour une image citee qui ⛔ n'ouvre pas sur `FF D8`.
    Exactement un des deux est `None`. Un GIF est juge par `structure_gif` ;
    tout autre fichier est une faute NOMMEE, ⛔ un « pas un JPEG » generique."""
    court = rel[-40:]
    if brut[:6] not in MAGIE_GIF:
        return ("%s ⛔ ni JPEG (SOI FF D8) ni GIF (GIF87a/GIF89a) : octets %r"
                % (court, brut[:6]), None)
    g, raison = structure_gif(brut)
    if g is None:
        return "%s ⛔ pas un GIF lisible : %s" % (court, raison), None
    if g["intrus"]:
        return "%s ⛔ porte %s" % (court, " + ".join(g["intrus"])), None
    grand = max([g["ecran"]] + g["images"], key=max)
    if max(grand) > PIXELS_MAX:
        return ("%s ⛔ %s %dx%d, grand cote > %d"
                % (court, "ecran logique" if grand == g["ecran"] else "image",
                   grand[0], grand[1], PIXELS_MAX), None)
    return None, "%dx%d (%s, %d images, %d NETSCAPE2.0)" % (
        g["ecran"] + (g["version"], len(g["images"]), g["netscape"]))


def section(txt, titre):
    """Le texte d'une section `## titre`, jusqu'au `## ` suivant."""
    m = re.search(r"(?m)^## +%s\s*$" % re.escape(titre), txt)
    if not m:
        return None
    suite = re.search(r"(?m)^## ", txt[m.end():])
    return txt[m.end():m.end() + suite.start()] if suite else txt[m.end():]


def main():
    global _MUTANT
    ap = argparse.ArgumentParser(description="dn8-4 — la vitrine est gardee.")
    ap.add_argument("--mutant", type=int, default=0)
    ap.add_argument("--liste-mutants", action="store_true")
    a = ap.parse_args()
    if a.liste_mutants:
        for n in sorted(MUTANTS):
            print("  %2d  %s" % (n, MUTANTS[n]))
        return 0
    _MUTANT = a.mutant
    if _MUTANT and _MUTANT not in MUTANTS:
        print("⛔ mutant %d inconnu — `--liste-mutants` les donne." % _MUTANT)
        return 2

    print("=" * 78)
    print("dn8-4 — LA VITRINE EST GARDEE" + ("   [MUTANT %d]" % _MUTANT
                                            if _MUTANT else ""))
    print("=" * 78)
    print(AVEUGLEMENT_VITRINE)

    try:
        brut_txt, emp = dn_gates.lire(os.path.join(RACINE, VITRINE))
    except (OSError, UnicodeDecodeError) as x:
        ctrl(False, "(c1) la vitrine se LIT", "⛔ %s : %s" % (VITRINE, x))
        return bilan(1, anticipee="vitrine illisible", prevus=CONTROLES_PREVUS)
    try:
        txt = muter_vitrine(brut_txt)
        cibles = muter_cibles(CIBLES)
        # ⚠️ TOUTE IMAGE LOCALE CITEE, ⛔ pas deux constantes : une troisieme
        #    image posee dans la vitrine echappait a (c5)/(c6) (revue 2026-09-13).
        cites = [e[2][1] for e in elements(txt)[0] if e[1] == "image"
                 and not re.match(r"^[a-z]+:", e[2][1])]
        # 🆕 dn8-9 — la cible des mutants 17-20 : le PREMIER `.gif` cite.
        premier_gif = next((r for r in cites
                            if r.split("#")[0].lower().endswith(".gif")), None)
        if _MUTANT in MUTANTS_GIF and premier_gif is None:
            raise NonExerce("MUTANT %d NON EXERCE : la vitrine ne cite AUCUN "
                            "GIF — la faute n'a nulle part ou etre replantee"
                            % _MUTANT)
        photos = {}
        for rel in list(dict.fromkeys(cites + list(PHOTOS))):
            try:
                with open(os.path.join(RACINE, rel.split("#")[0]), "rb") as f:
                    photos[rel] = muter_photo(rel, f.read(), premier_gif)
            except OSError:
                photos[rel] = None
        if _MUTANT in MUTANTS_GIF and photos.get(premier_gif) is None:
            raise NonExerce("MUTANT %d NON EXERCE : le 1er GIF cite (%s) est "
                            "ABSENT du disque" % (_MUTANT, premier_gif))
    except NonExerce as x:
        print("⛔ %s" % x)
        print("   ⇒ rc=3 : un mutant qui ne change rien ⛔ ne prouve rien.")
        return 3
    print("vitrine : %s — %d o · sha256[:16] %s%s"
          % (VITRINE, len(txt.encode("utf-8")), emp,
             "  (⚠️ texte MUTE en memoire)" if txt != brut_txt else ""))

    els, hors = elements(txt)
    textes = [e for e in els if e[1] == "texte"]

    # ── (c1) L'ORDRE STATUE ────────────────────────────────────────────────
    print("\n── (c1) L'ORDRE DE LECTURE STATUE (UX-DR8.1) ─────────────────────")
    fautes = []
    if not els or els[0][1] != "titre" or els[0][2] != (1, "DeskNode"):
        fautes.append("le 1er element n'est pas `# DeskNode` (%r)"
                      % (els[0][2] if els else None,))
    if len(els) < 2 or els[1][1] != "image" or els[1][2][1] != PHOTO_ACTIVE:
        fautes.append("le 2e element n'est pas la photo ACTIVE (%r)"
                      % (els[1][2] if len(els) > 1 else None,))
    suite = [e for e in els[2:6] if e[1] == "texte"][:3]
    if len(suite) < 3:
        fautes.append("moins de trois paragraphes apres la photo")
    else:
        if PHRASE not in suite[0][2]:
            fautes.append("le 1er paragraphe apres la photo ne dit pas « %s »"
                          " (l.%d)" % (PHRASE, suite[0][0]))
        manque = [x for x in LICENCES if x not in suite[1][2]]
        if manque or "](LICENSING.md)" not in suite[1][2]:
            fautes.append("le 2e paragraphe ne porte pas les trois licences et "
                          "le lien `LICENSING.md` (manque %s)"
                          % (manque or ["le lien"]))
        manque = [x for x in MATERIEL if x not in suite[2][2]]
        if manque:
            fautes.append("le 3e paragraphe ne dit pas %s" % manque)
    ctrl(not fautes, "(c1) nom → photo → phrase → licences → materiel",
         "l.%s — dans cet ordre" % ",".join(str(e[0]) for e in els[:5])
         if not fautes else "⛔ " + " · ".join(fautes))

    # ── (c2) ⛔ CPU MONITOR ────────────────────────────────────────────────
    vus = [n for n, l in enumerate(txt.split("\n"), 1)
           if INTERDITS["c2"] in l.lower()]
    aplat = INTERDITS["c2"] in aplati(txt)
    ctrl(not vus and not aplat,
         "(c2) ⛔ « CPU monitor » — le message n'est pas celui-la",
         "0 occurrence, ligne a ligne ET sur le texte aplati"
         if not vus and not aplat
         else "⛔ l.%s" % vus if vus
         else "⛔ present dans le texte APLATI (emphase ou saut de ligne)")

    # ── (c3) L'AVEUGLEMENT N'EST PAS EXERCE ────────────────────────────────
    print("\n── (c3)(c4) CE QUE LA GATE NE LIT PAS, ET LA TAILLE ──────────────")
    ctrl(not hors, "(c3) ⛔ HTML brut, setext, lien de reference",
         "0 construction hors de portee" if not hors
         else "⛔ %s" % " · ".join("l.%d %s" % h for h in hors[:4]))

    # ── (c4) LA TAILLE ─────────────────────────────────────────────────────
    taille = len(txt.encode("utf-8"))
    ctrl(taille <= PLAFOND_VITRINE,
         "(c4) la vitrine tient sous %d o" % PLAFOND_VITRINE,
         "%d o" % taille if taille <= PLAFOND_VITRINE
         else "⛔ %d o — ⛔ ce n'est plus une vitrine" % taille)

    # ── (c5)(c6) LES PHOTOS, LUES PAR LEURS MARQUEURS ──────────────────────
    print("\n── (c5)(c6) LES PHOTOS, LUES OCTET PAR OCTET ─────────────────────")
    f5, d5, f6, d6 = [], [], [], []
    for rel in photos:
        b = photos[rel]
        if b is None:
            f5.append("%s ABSENTE" % rel)
            f6.append("%s ABSENTE" % rel)
            continue
        # 🆕 dn8-9 — DISPATCH PAR OCTETS MAGIQUES, ⛔ par extension : un GIF
        #    renomme `.jpg` est lu comme un GIF, et un PNG renomme `.gif` sort
        #    « ni JPEG ni GIF ». Le chemin JPEG ci-dessous est INCHANGE.
        # 🆕 2026-09-14, revue : (c6) UNE SEULE FOIS, pour TOUTE image, AVANT
        #    le dispatch — sa copie dans la branche GIF n'etait gardee par aucun
        #    mutant (un GIF de 680 000 o sortait 16/0 sans elle).
        (f6 if len(b) >= PLAFOND_PHOTO else d6).append(
            "%s %d o" % (os.path.basename(rel)[:16], len(b)))
        if b[:6] in MAGIE_GIF or b[:2] != b"\xff\xd8":
            faute, detail = verdict_hors_jpeg(rel, b)
            (f5 if faute else d5).append(faute or detail)
            continue
        segs = segments_jpeg(b)
        px = pixels(segs)
        intrus = ["APP%d" % (m - 0xE0) if m != 0xFE else "COM"
                  for m, c in (segs or ())
                  if (0xE0 <= m <= 0xEF or m == 0xFE)
                  and not (m == 0xE0 and c.startswith(b"JFIF\x00"))]
        if segs is None or px is None:
            f5.append("%s ⛔ pas un JPEG lisible (SOI/SOF)" % rel[-40:])
        elif intrus:
            f5.append("%s ⛔ porte %s" % (rel[-40:], "+".join(intrus)))
        elif max(px) > PIXELS_MAX:
            f5.append("%s ⛔ %dx%d, grand cote > %d" % (rel[-40:], px[0], px[1],
                                                       PIXELS_MAX))
        else:
            d5.append("%dx%d" % px)
    ctrl(not f5 and bool(photos),
         # ⚠️ < 58 CARACTERES UNE FOIS FORMATE (56) : la cle de campagne se lit
         #    A COLONNE FIXE (`verif_campagne_dn56.py` (c4), `LARGEUR_LIBELLE`).
         #    La 1re redaction en faisait 74, et (c4) l'a compte « >= 58 ».
         "(c5) JPEG (JFIF seul) ou GIF (liste blanche), <= %d px" % PIXELS_MAX,
         "%d image(s) citee(s) · pixels %s · ⛔ 0 APPn hors JFIF, 0 COM, "
         "0 extension GIF hors liste blanche"
         % (len(photos), " et ".join(d5)) if not f5 and photos
         else "⛔ " + " · ".join(f5 or ["AUCUNE image citee"]))
    ctrl(not f6, "(c6) toute image citee existe, < %d o" % PLAFOND_PHOTO,
         " · ".join(d6) if not f6 else "⛔ " + " · ".join(f6))

    # ── (c7) LA PHOTO DE CONTEXTE ET SA LEGENDE ────────────────────────────
    print("\n── (c7) LE CONTEXTE, ET CE QUE LA LEGENDE ASSUME (D24, voie a) ───")
    imgs = [(i, e) for i, e in enumerate(els) if e[1] == "image"]
    f7 = []
    if len(imgs) < 2 or imgs[0][1][2][1] != PHOTO_ACTIVE \
            or imgs[1][1][2][1] != PHOTO_CONTEXTE:
        f7.append("images %s — attendu la photo active PUIS le contexte"
                  % [os.path.basename(e[2][1]) for _, e in imgs])
    else:
        apres = [e for e in els[imgs[1][0] + 1:] if e[1] == "texte"][:1]
        legende = apres[0][2] if apres else ""
        manque = [x for x in LEGENDE if x not in legende]
        if manque:
            f7.append("la legende sous le contexte ne dit pas %s" % manque)
    ctrl(not f7, "(c7) contexte apres la photo active, legende assumee",
         "prototype · bare wiring · no enclosure · French" if not f7
         else "⛔ " + " · ".join(f7))

    # ── (c8) PALIERS, POINT D'ENTREE, LANGUE ───────────────────────────────
    print("\n── (c8) LES PALIERS, LE POINT D'ENTREE, LA LANGUE ────────────────")
    # ⚠️ LA LANGUE SE LIT DANS **SA** SECTION, ⛔ pas dans toute la page. MESURE
    #    a la premiere redaction : le mutant 8 (l'ecran demarre en francais)
    #    sortait VERT, parce que la legende des photos dit AUSSI « starts in
    #    English ». Un motif cherche partout est satisfait par son voisin.
    langue = section(txt, LANGUE_TITRE)
    nu = dn_gates.plat((langue or "").replace("*", ""))
    present = os.path.isfile(os.path.join(RACINE, ENTREE))
    manque = [x for x in PALIERS if x not in txt] \
        + ([ENTREE] if ENTREE not in txt else []) \
        + ([] if present else ["%s SUR LE DISQUE" % ENTREE]) \
        + ([] if langue is not None else ["## %s" % LANGUE_TITRE]) \
        + [x for x in LANGUE if x not in nu]
    ctrl(not manque, "(c8) deux paliers, point d'entree, anglais par defaut",
         "%s · %s · `## %s` : %s" % (" / ".join(PALIERS), ENTREE, LANGUE_TITRE,
                                      " / ".join(LANGUE))
         if not manque else "⛔ absent(s) : %s" % manque)

    # ── (c9)(c10) LES KNOWN ISSUES ─────────────────────────────────────────
    print("\n── (c9)(c10) LES KNOWN ISSUES VRAIS (FR20) ───────────────────────")
    ki = section(txt, KNOWN_ISSUES_TITRE)
    f9 = []
    if ki is None:
        f9.append("section `## %s` ABSENTE" % KNOWN_ISSUES_TITRE)
    else:
        f9 += ["« %s » absent" % x for x in KNOWN_ISSUES if x not in ki]
    f9 += ["l.%d promet « not perceptible »" % n
           for n, l in enumerate(txt.split("\n"), 1)
           if INTERDITS["c9"] in l.lower()]
    if INTERDITS["c9"] in aplati(txt) and not any("promet" in f for f in f9):
        f9.append("« not perceptible » dans le texte APLATI")
    ctrl(not f9, "(c9) ~40 s · 335.8/300 ms · AMD · Intel Arc",
         "dans `## %s`, ⛔ 0 « not perceptible »" % KNOWN_ISSUES_TITRE
         if not f9 else "⛔ " + " · ".join(f9))

    nv = [(n, l) for n, l in enumerate(txt.split("\n"), 1)
          if "nvidia" in l.lower()]
    f10 = ["l.%d" % n for n, l in nv if "not implemented" not in l]
    dans_ki = bool(ki) and "NVIDIA" in ki
    ctrl(bool(nv) and not f10 and dans_ki,
         "(c10) NVIDIA porte « not implemented » SUR SA LIGNE",
         "%d ligne(s) NVIDIA, toutes refutees sur place" % len(nv)
         if nv and not f10 and dans_ki
         else "⛔ %s" % ("ligne(s) sans refutation : %s" % f10 if f10
                         else "NVIDIA absent des known issues"))

    # ── (c11) LE JOURNAL ───────────────────────────────────────────────────
    print("\n── (c11)(c12) LE JOURNAL, ET LES MOTIFS D'UN AUTRE SUJET ─────────")
    liens = [m.group(2) for m in RE_LIEN.finditer(txt)]
    ok11 = JOURNAL in liens and os.path.isfile(os.path.join(RACINE, JOURNAL))
    ctrl(ok11, "(c11) le lien vers le journal existe, sa cible aussi",
         "`%s` lie et present" % JOURNAL if ok11
         else "⛔ lien(s) vers docs/ : %s — cible presente : %s"
              % ([l for l in liens if l.startswith("docs/j")],
                 os.path.isfile(os.path.join(RACINE, JOURNAL))))

    # ── (c12) ⛔ AUCUN MOTIF DE dn415 ──────────────────────────────────────
    hits = []
    for n, l in enumerate(txt.split("\n"), 1):
        norm = dn415.normalise(l)
        for cle, rx, _lib, garde in dn415.MOTIFS:
            if garde and not garde(norm):
                continue
            if rx.search(norm):
                hits.append("l.%d `%s`" % (n, cle))
    ctrl(bool(dn415.MOTIFS) and not hits,
         "(c12) ⛔ aucun motif de verif_dossier_dn415.py",
         "%d motif(s) confronte(s), 0 occurrence" % len(dn415.MOTIFS)
         if not hits and dn415.MOTIFS else "⛔ " + " · ".join(hits[:4]))

    # ── (c13) LA COMMANDE D'INSTALLATION EST CELLE DU PRODUIT ────────────
    print("\n── (c13) LA COMMANDE D'INSTALLATION EST CELLE DU PRODUIT ─────────")
    try:
        with open(os.path.join(RACINE, SERVEUR), encoding="utf-8") as f:
            geste = geste_du_serveur(f.read())
    except (OSError, UnicodeDecodeError):
        geste = None
    inst = section(txt, INSTALL_TITRE)
    f13 = []
    if geste is None:
        f13.append("`GESTE_DEPENDANCES` ILLISIBLE dans %s" % SERVEUR)
    if inst is None:
        f13.append("section `## %s` ABSENTE" % INSTALL_TITRE)
    else:
        if geste is not None and "`%s`" % geste not in inst:
            f13.append("`%s` absent de `## %s`" % (geste, INSTALL_TITRE))
        if VERSION_EXE not in inst:
            f13.append("« %s » absent de `## %s`" % (VERSION_EXE, INSTALL_TITRE))
    ctrl(not f13, "(c13) `## Install` porte GESTE_DEPENDANCES et V0.2",
         "`%s` (lu a l'AST dans %s) · %s" % (geste, SERVEUR, VERSION_EXE)
         if not f13 else "⛔ " + " · ".join(f13))

    # ── (c14)(c15)(c16) LA RECIPROQUE, MECANIQUE ────────────────────────
    print("\n── (c14)(c15)(c16) AUCUN CONTROLE GARDE PAR ZERO MUTANT ──────────")
    # 🔴 « N mutants, N vus rougir » prouve `mutant ⇒ rouge`, ⛔ JAMAIS
    #    `controle ⇒ couvert`. Porte de `verif_prerequis_dn75.py` : les
    #    identifiants sont LUS A L'AST de ce fichier, ⛔ pas ceux deja emis.
    reels = dn_gates.ids_par_ast(os.path.abspath(__file__))
    vises = set()
    for v in cibles.values():
        vises.update(v)
    nus = sorted((reels or set()) - vises, key=lambda x: (len(x), x))
    ctrl(not nus and reels is not None,
         "(c14) chaque controle est vise par >= 1 mutant",
         "%d controle(s) lu(s) a l'AST, %d cible(s) declaree(s)"
         % (len(reels), len(vises)) if not nus and reels is not None
         else ("⛔ %d CONTROLE(S) GARDE(S) PAR RIEN : %s"
               % (len(nus), " · ".join(nus)) if nus
               else "⛔ LA SOURCE NE S'ANALYSE PAS A L'AST — population INCONNUE"))
    perimees = sorted(vises - (reels or set()), key=lambda x: (len(x), x))
    ctrl(not perimees, "(c15) chaque cible de mutant est un controle REEL",
         "%d cible(s) confrontee(s)" % len(vises) if not perimees
         else "⛔ %d CIBLE(S) PERIMEE(S) : %s" % (len(perimees),
                                                " · ".join(perimees)))
    orph = sorted(set(cibles) - set(MUTANTS))
    sans_cible = sorted(set(MUTANTS) - set(cibles))
    ctrl(not orph and not sans_cible,
         "(c16) `CIBLES` et `MUTANTS` se correspondent",
         "%d mutant(s), %d cible(s), cle a cle" % (len(MUTANTS), len(cibles))
         if not orph and not sans_cible
         else "⛔ cible(s) SANS mutant : %s · mutant(s) SANS cible : %s"
              % (orph or "—", sans_cible or "—"))

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : qu'un inconnu COMPREND DeskNode en")
    print("   quinze secondes. Elle garde l'ORDRE et la VERITE de ce qu'il lit ;")
    print("   le verdict « compris » est l'oeil d'un inconnu, et il est au ledger.")
    print("   Elle ⛔ ne garde pas non plus le RENDU de GitHub : `T4` le releve a la")
    print("   main (`mesures/dn8-4/T4-rendu-github.txt`).")
    return bilan(1 if dn_gates.ko_total[0] else 0, prevus=CONTROLES_PREVUS)


if __name__ == "__main__":
    sys.exit(main())

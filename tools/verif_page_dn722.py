#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn7-2-2 — LA PAGE DIT LE VRAI NOM DU PORT, ET ON SAIT QUOI Y FAIRE.

======================= CE QUE CETTE GATE GARDE, ET POURQUOI ================

`installeur/index.html` est la SEULE surface qu'un inconnu traverse
forcement. Le 2026-09-09 elle a ete regardee par son premier lecteur reel, et
cinq ecarts en sont sortis — dont un que la MESURE a refute alors que la marche
precedente l'avait publie comme ferme. Cette gate garde les cinq corrections,
et elle existe pour une raison ecrite plutot que supposee :

  🔴 RIEN DANS CE DEPOT N'EXECUTE LE JAVASCRIPT DE CETTE PAGE. Le seul tir DOM
     qui ait jamais tourne est un navigateur sans fenetre, cote Windows, HORS
     du glob de `tools/run_gates.sh`. ⇒ sans une garde STATIQUE, tout ce que
     cette marche ecrit dans la page n'est rejoue par PERSONNE — c'est
     exactement le risque que la marche precedente a nomme en cloturant.

  1. **LE SELECTEUR N'EST NOMME QUE PAR CE QU'IL MONTRE.** Il affiche UNE
     ligne, la chaine PRODUIT USB de la puce. La forme LOCALISEE de Windows
     reste ecrite — un lecteur la verra dans le Gestionnaire de peripheriques —
     mais ATTRIBUEE, ⛔ plus offerte comme une forme concurrente.
  2. **LE LIBELLE DU BOUTON EST CELUI QUI S'AFFICHE.** « Connexion ». Le
     libelle perime reste dans la page, BARRE et date (⛔ on annote, on
     n'efface pas) — et aucune de ses occurrences n'est VIVE.
  3. **UN SEUL BOUTON POSTE `stop`.** Deux boutons postaient le meme verbe sur
     le meme port et rendaient la meme sortie : le choix ne se pose plus.
  4. **RELIRE SA CARTE NE PASSE PLUS PAR LE BOUTON QUI LA REFLASHE.** Une
     entree distincte, un debit qui n'est pas suppose, trois refus nommes
     separement, et un geste qui REND le port.
  5. **LA PAGE PARLE DEUX LANGUES, ET LE DEFAUT ANGLAIS EST STRUCTUREL.** Il
     tient a l'attribut de la racine et a une regle de style — ⛔ pas a un
     script qui aurait pu ne pas tourner. Une cle sans jumelle est un DEFAUT.

── CE QU'ELLE NE PROUVE ⛔ PAS, ECRIT PLUTOT QUE TU ─────────────────────────

⛔ Elle n'execute PAS le JavaScript de la page. Elle lit sa STRUCTURE : elle
   prouve que le mecanisme est en place et complet, ⛔ pas qu'il se leve au bon
   moment dans un vrai navigateur. Cette moitie-la reste au ledger.
⛔ Elle ne dit RIEN de la lisibilite. « Le geste suivant est identifiable sans
   rien derouler » se ferme A L'ŒIL DE L'OWNER, et par rien d'autre : un ratio
   de texte ou un compte de sections ne dit pas si quelqu'un a su quoi faire.
⛔ Elle n'ouvre aucun port serie et ne parle a aucune carte.

Emploi :
    python3 tools/verif_page_dn722.py
    python3 tools/verif_page_dn722.py --liste-mutants
    python3 tools/verif_page_dn722.py --mutant <n>

Sortie : 0 si tout passe · 1 sur un vrai defaut · 2 sur un mutant inconnu ·
         3 si le mutant demande est PERIME (il n'a rien change).
"""

import argparse
import ast
import copy
import io
import os
import re
import sys
from html.parser import HTMLParser

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGE = "installeur/index.html"
FIXES = (PAGE,)

# ── CE QUE LE SELECTEUR MONTRE, RELEVE A L'ŒIL LE 2026-09-09 ──────────────
# 🔴 UNE SEULE LIGNE, ET C'EST LA CHAINE PRODUIT USB DE LA PUCE. Le
#    `FriendlyName` LOCALISE que Windows fabrique — « Peripherique serie USB
#    (COM3) » — est ce que montre le GESTIONNAIRE DE PERIPHERIQUES, ⛔ pas le
#    navigateur. La marche precedente avait mesure le premier et l'avait
#    generalise au second, que personne n'avait ouvert.
FORME_SELECTEUR = "USB JTAG/serial debug unit"
FORME_GESTIONNAIRE = "Périphérique série USB"
ATTRIBUTIONS = ("Gestionnaire de périphériques", "Device Manager")
# 🔴 LA FENETRE EST L'**ELEMENT DE LANGUE** QUI PORTE LA MENTION, ⛔ PLUS UN
#    RAYON DE CARACTERES. Un rayon plat sur le texte aplati laisse
#    l'attribution de l'AUTRE langue tomber dans la fenetre : retirer celle
#    d'un seul cote laissait donc le controle VERT, alors que le lecteur de ce
#    cote-la lit la forme localisee SANS savoir d'ou elle sort. Or c'est
#    exactement la propriete pour laquelle ce controle existe.
RE_ELEMENT_LANGUE = re.compile(
    r'<(\w+)[^>]*\blang="(en|fr)"[^>]*>(.*?)</\1>', re.S)
# Ce que le selecteur ecrit sur son bouton, et ce qu'il n'ecrit pas.
LIBELLE_BOUTON = "Connexion"
LIBELLE_PERIME = "Se connecter"

# ── LE VERBE `stop`, ET LE FAIT QU'IL N'EST POSTE QU'UNE FOIS ─────────────
# ⚠️ ON COMPTE L'APPEL, ⛔ PAS LE MOT : `stop` paraît dans la prose, dans les
#    commentaires et dans le nom du drapeau. Ce qui decide, c'est le nombre de
#    fois ou un bouton POSTE le verbe.
RE_JOUER_STOP = re.compile(r'jouer\(\s*"stop"')
RE_ECOUTE_STOP = re.compile(
    r'(\w+)\.addEventListener\(\s*"click"[\s\S]{0,160}?jouer\(\s*"stop"')
# Le bouton survivant est nomme par TOUT son effet : arreter l'agent ET rendre
# le port. Les deux moities, dans les deux langues.
EFFET_STOP = (("Stop the agent", "hand the port back"),
              ("Arrêter l'agent", "rendre le port"))
# ⛔ CE QUI NE DOIT PLUS EXISTER : le second bouton, celui qui postait le meme
#    verbe sous un autre nom.
BOUTON_DISPARU = "b-liberer"

# ── LA CONSOLE, DISTINCTE DU FLASH ────────────────────────────────────────
# 🔴 « DISTINCTE » SE MESURE SUR L'ELEMENT, ⛔ PAS SUR LE LIBELLE : un
#    renommage du bouton de flash ne suffit pas, et l'AC le dit mot pour mot.
BOUTON_CONSOLE = "b-console"
BOUTON_CONSOLE_FERMER = "b-console-fermer"
ELEMENT_FLASH = "<esp-web-install-button "
# ⚠️ LE DEBIT N'EST PAS SUPPOSE : trois sources concordantes du depot le
#    donnent — la configuration du firmware, l'agent, et l'ouverture de l'outil
#    de flash lui-meme, celle qui a produit le battement lu en seance.
DEBIT = "115200"
RE_OUVERTURE = re.compile(r"baudRate\s*:\s*(\w+)")
RE_DEBIT_DECLARE = re.compile(r"DEBIT_CONSOLE\s*=\s*(\d+)")
# Les TROIS refus, nommes SEPAREMENT. ⛔ Jamais « aucune carte » pour un port
# REFUSE : le port existe et il a ete choisi ; ce qui echoue est son OUVERTURE.
# 🔴 CHAQUE CLE EST ANCREE DANS **SA** BRANCHE, ⛔ pas seulement PRESENTE
#    quelque part. DEMONTRE : en ECHANGEANT deux cles entre leurs branches —
#    « aucun port choisi » sur l'echec d'OUVERTURE et « port refuse » sur le
#    selecteur ferme — la gate restait VERTE, et le lecteur dont l'agent tient
#    le port lisait « aucun port choisi ». C'est le message qui n'explique
#    rien, celui que cette page existe pour cesser de rendre.
#    ⇒ `(cle, motif d'ancrage dans le script)`, l'ancre etant ce qui DECIDE de
#      la branche : le test de disponibilite, le refus d'OUVERTURE, le refus
#      du SELECTEUR.
#    ⇒ chaque cle porte *(a)* LE MARQUEUR DE SA BRANCHE, qui doit la preceder,
#      et *(b)* SON RANG. Le rang n'est ⛔ pas une convention : le refus
#      d'OUVERTURE vit dans un gestionnaire IMBRIQUE DANS le succes du
#      selecteur, donc il precede forcement le refus du selecteur dans le
#      source. Echanger les deux cles inverse ce rang, et rien d'autre ne le
#      ferait.
ANCRES_REFUS = (
    ("console.sans-serial", '"serial" in navigator'),
    ("console.port-refuse", ".open({"),
    ("console.aucun-port", "requestPort()"),
)
CLES_REFUS = tuple(c for c, _ in ANCRES_REFUS)
# Le geste qui REND le port, et la page qui le dit.
CLE_RENDU = "console.rendue"
# 🔴 L'ORDRE EST LA PROPRIETE, ⛔ PAS LA PRESENCE DE `close`. Un flux encore
#    VERROUILLE fait partir `close()` en rejet : sans relachement, le lecteur
#    reste verrouille, la fermeture echoue, et la page annoncerait quand meme
#    la restitution. DEMONTRE : retirer le bloc d'annulation-relachement
#    laissait la gate VERTE. ⇒ on exige `cancel` puis `releaseLock` puis
#    `close`, dans CET ordre, dans le code — ⛔ pas dans les commentaires.
RE_SEQUENCE_RENDU = re.compile(
    r"\.cancel\(\)[\s\S]{0,400}?\.releaseLock\(\)[\s\S]{0,400}?\.close\(\)")

# ── LES DEUX LANGUES ──────────────────────────────────────────────────────
LANGUES = ("en", "fr")
# 🔴 LA BALISE RACINE, LUE **AU DEBUT DU DOCUMENT** — ⛔ PAS CHERCHEE PARTOUT.
#    C'est un piege deja paye deux fois dans ce depot : la page CITE
#    `<html lang="en">` dans un commentaire qui explique pourquoi le defaut est
#    structurel, et un motif non ancre trouvait cette CITATION. Le mutant qui
#    retournait la vraie balise sortait alors VERT — une gate qui mesure la
#    prose ⛔ ne mesure pas la page.
RE_BALISE_RACINE = re.compile(r"\A\s*(?:<!doctype[^>]*>\s*)?<html([^>]*)>", re.I)
RE_LANG_ATTR = re.compile(r"\blang\s*=\s*[\"']([^\"']*)[\"']", re.I)
RE_DEFAUT = re.compile(
    r":root:not\(\[data-langue=\"fr\"\]\)\s*\[lang=\"fr\"\]\s*\{[^}]*display\s*:\s*none")
RE_BASCULE = re.compile(
    r":root\[data-langue=\"fr\"\]\s*\[lang=\"en\"\]\s*\{[^}]*display\s*:\s*none")
SELECTEUR_LANGUE = "sec-langue"
# 🔴 LA REGLE QUI GARDE LA BASCULE **ATTEIGNABLE DANS LES DEUX SENS**. Sans
#    elle, la regle generale masque le bouton de l'autre langue : en anglais,
#    `#b-langue-fr` disparait, et le choix devient A SENS UNIQUE — offert une
#    fois, puis inatteignable. ⛔ Ni la regle de defaut ni la position du
#    selecteur ne disent quoi que ce soit de ca.
RE_SELECTEUR_TOUJOURS = re.compile(
    r'#' + SELECTEUR_LANGUE + r'\s*\[lang="en"\]\s*,\s*'
    r'#' + SELECTEUR_LANGUE + r'\s*\[lang="fr"\]\s*\{[^}]*display\s*:\s*'
    r'(?!none)')
# 🔴 TOUTE PROSE ECRITE PAR LE SCRIPT VIT DANS CETTE TABLE, ET CHAQUE CLE Y
#    PORTE **EXACTEMENT DEUX** VALEURS. C'est ce qui rend « aucun ilot reste
#    dans l'autre langue » MECANIQUE plutot que promis.
RE_TABLE_MOTS = re.compile(r"var MOTS = \{(.*?)\n\};", re.S)
RE_CLE_MOTS = re.compile(r'^\s{2}"([^"]+)"\s*:\s*\[', re.M)
# Une lettre, au sens Unicode. ⚠️ Un texte SANS la moindre lettre — « … »,
# « ⛔ », « · », un nombre — n'a PAS de langue : l'exiger bilingue ferait
# rougir la gate sur une redaction JUSTE.
RE_LETTRE = re.compile(r"[^\W\d_]", re.UNICODE)
# 🔴 DU TEXTE VISIBLE PEUT VIVRE DANS UN **ATTRIBUT**, ET LA FEUILLE DE STYLE
#    N'Y PEUT RIEN : une infobulle, un libelle d'accessibilite, un texte de
#    remplacement s'affichent sans etre un noeud de texte. C'est par la que la
#    prose sortait du mecanisme sans que rien ne le voie.
ATTRIBUTS_TEXTE = ("title", "aria-label", "alt", "placeholder")
# 🔴 LES FABRIQUES PAR LESQUELLES **TOUTE** PROSE DU SCRIPT DOIT PASSER — ET
#    CETTE CONSTANTE EST DESORMAIS **LUE**, ⛔ plus seulement declaree. Elle
#    nommait la vraie regle sans qu'aucun controle ne la joue : `(c14)` ne
#    filtrait que les litteraux ACCENTUES, donc elle laissait passer les ilots
#    ANGLAIS. DEMONTRE : remplacer un appel de fabrique par une ecriture nue
#    (« port handed back, nothing holds it ») laissait la gate VERTE, et cet
#    ilot restait ANGLAIS quand le lecteur bascule en francais.
FABRIQUES = ("paire(", "poserMot(", "blocMot(", "ecrireMot(",
             "consoleAjouterMot(", "consoleRefus(")
# ⚠️ OU VIT LA CLE DANS L'APPEL, ⛔ pas « au premier litteral » : deux
#    fabriques prennent d'abord l'IDENTIFIANT de l'element a remplir, et la
#    cle vient EN SECOND. Prendre le premier litteral partout ferait rougir la
#    gate sur des identifiants parfaitement justes.
FABRIQUES_CLE_2 = ("poserMot(", "blocMot(")
# Les litteraux du script qui ne sont PAS de la prose : identifiants, cles de
# table, chemins, unites. ⚠️ La liste est FERMEE et courte, et chaque entree
# est une chose que le navigateur lit — ⛔ pas une phrase que quelqu'un lit.
RE_NON_PROSE = re.compile(
    r"^(?:"
    r"[\w.\-/#:?=&]*"                 # un jeton : cle, id, chemin, unite
    r"|[A-Za-z\-]+\s*:\s*[\w\-]+"    # une option : `cache: no-store`
    r")$")
# Les sequences d'echappement du SOURCE (`\n`, `\t`) : elles portent une
# lettre a la lecture du fichier, ⛔ pas a l'ecran.
RE_ECHAPPEMENT = re.compile(r"\\.")
# ⚠️ Un litteral COMPARE n'est pas affiche : c'est une valeur que le SERVEUR
#    rend, et la page la teste. La distinguer se fait sur ce qui PRECEDE.
RE_COMPARAISON = re.compile(r"(?:===|!==|==|!=)\s*$")
# La seule directive du langage, et elle n'est lue par personne d'autre que le
# moteur. Liste FERMEE : ⛔ pas une porte, une exception NOMMEE.
DIRECTIVES = ("use strict",)
# Ce qui signe de la prose FRANCAISE ecrite en dur : une lettre accentuee dans
# un litteral de chaine, hors des commentaires et hors de la table.
RE_ACCENT = re.compile(r"[àâäçéèêëîïôöùûüÀÂÄÇÉÈÊËÎÏÔÖÙÛÜ]")

LARGEUR_LIBELLE = 58

ok_total = [0]
ko_total = [0]
ids_emis = []

MUTANTS = {}                      # ⛔ AU NIVEAU MODULE — sinon `--liste-mutants`
CIBLES = {}                       # ⛔ AU NIVEAU MODULE — matiere de (c16)

MUTANTS[1] = ("efface de la page la forme que le selecteur montre "
              "VRAIMENT ⇒ personne ne reconnait la ligne qu'il voit")
CIBLES[1] = ("c1",)
MUTANTS[2] = ("retire l'ATTRIBUTION de la forme localisee ⇒ la page la "
              "re-offre comme une forme CONCURRENTE du selecteur")
CIBLES[2] = ("c2",)
MUTANTS[3] = ("efface de la page la forme LOCALISEE ⇒ celui qui la lit "
              "dans le Gestionnaire ne la relie plus a sa carte")
CIBLES[3] = ("c2",)
MUTANTS[4] = ("remet le libelle PERIME du bouton du selecteur ⇒ on "
              "cherche un bouton qui ne s'appelle plus comme ca")
CIBLES[4] = ("c3",)
MUTANTS[5] = ("DEBARRE le libelle perime ⇒ la page l'offre a nouveau "
              "comme une instruction vivante, sans le dire")
CIBLES[5] = ("c4",)
MUTANTS[6] = ("replante un SECOND bouton qui poste `stop` ⇒ le choix "
              "entre deux commandes identiques revient")
CIBLES[6] = ("c5",)
MUTANTS[7] = ("ne laisse au bouton survivant que la MOITIE de son effet "
              "⇒ « il rend le port » cesse d'etre dit")
CIBLES[7] = ("c6",)
MUTANTS[8] = ("renomme le bouton de flash en « console » au lieu d'une "
              "entree distincte ⇒ le renommage que l'AC refuse")
CIBLES[8] = ("c7",)
MUTANTS[9] = ("fait ouvrir la console a un debit AUTRE que celui des "
              "trois sources ⇒ un battement illisible")
CIBLES[9] = ("c8",)
MUTANTS[10] = ("confond deux refus de console ⇒ « aucune carte » pour un "
               "port qui existe et que l'agent tient")
CIBLES[10] = ("c9",)
MUTANTS[11] = ("retire la fermeture du port ⇒ la console garde le port EN "
               "SILENCE et l'agent ne repart pas")
CIBLES[11] = ("c10",)
MUTANTS[12] = ("plante dans la page un texte visible HORS du mecanisme "
               "des deux langues ⇒ un ilot dans une seule langue")
CIBLES[12] = ("c11",)
MUTANTS[13] = ("retire a un element sa JUMELLE ⇒ la bascule laisse un "
               "trou, et rien ne s'affiche dans l'autre langue")
CIBLES[13] = ("c12",)
MUTANTS[14] = ("laisse une cle de `MOTS` SANS sa jumelle ⇒ la faute que "
               "cette table existe pour rendre visible")
CIBLES[14] = ("c13",)
MUTANTS[15] = ("ecrit de la prose francaise EN DUR hors des fabriques ⇒ "
               "un ilot que la bascule ne touche pas")
CIBLES[15] = ("c14",)
MUTANTS[16] = ("remet `lang=\"fr\"` a la racine ⇒ le defaut anglais cesse "
               "d'etre STRUCTUREL")
CIBLES[16] = ("c15",)
MUTANTS[17] = ("retire la regle de style qui cache le francais ⇒ les DEUX "
               "langues s'affichent l'une sous l'autre")
CIBLES[17] = ("c16",)
MUTANTS[18] = ("cache le selecteur de langue ⇒ le choix existe et "
               "personne ne peut l'atteindre")
CIBLES[18] = ("c17",)
MUTANTS[19] = ("replante une SORTIE ANTICIPEE NON DECLAREE : le bilan "
               "retrecit, et il sortirait VERT")
CIBLES[19] = ("z",)
MUTANTS[20] = ("declare un mutant dont le CORPS LEVE ⇒ un mutant MORT, "
               "qui sortirait en Traceback SANS `BILAN`")
CIBLES[20] = ("c0",)
MUTANTS[21] = ("retire une cible de `CIBLES` ⇒ un controle garde par "
               "ZERO mutant, le risque deja paye ailleurs")
CIBLES[21] = ("c18",)
MUTANTS[22] = ("declare dans `CIBLES` un controle INEXISTANT ⇒ une cible "
               "PERIMEE, que « N mutants, N rouges » ne verrait pas")
CIBLES[22] = ("c19",)
MUTANTS[23] = ("declare une cible pour un mutant qui N'EXISTE PAS")
CIBLES[23] = ("c20",)
# 🔴 AJOUTE LE 2026-09-09 A LA VERIFICATION DE LA MARCHE : `(c21)` etait la
#    SEULE ligne de la matrice d'entrees-sorties du dossier a n'avoir aucun
#    controle qui TOURNE. ⛔ Un geste replie est exactement ce que l'AC
#    interdit, et c'est MECANIQUE — ⛔ contrairement a la lisibilite.
MUTANTS[24] = ("replie le geste de la console derriere un depliant ⇒ "
               "il faut DEROULER pour voir quoi faire")
CIBLES[24] = ("c21",)
# 🔴 LES SEPT SUIVANTS SONT NES D'UNE VERIFICATION, ET CHACUN REPLANTE UNE
#    FAUTE QUI A ETE **DEMONTREE VERTE** — ⛔ pas une faute imaginee.
MUTANTS[25] = ("pose l'id de la console SUR l'element de flash ⇒ le "
               "RENOMMAGE que l'AC refuse mot pour mot")
CIBLES[25] = ("c7",)
MUTANTS[26] = ("replante un second poste de `stop` derriere une FONCTION "
               "NOMMEE ⇒ le compte d'ecouteurs ne le voit pas")
CIBLES[26] = ("c5",)
MUTANTS[27] = ("ECHANGE deux refus de console entre leurs branches ⇒ "
               "« aucun port choisi » sur un port que l'agent tient")
CIBLES[27] = ("c9",)
MUTANTS[28] = ("DEBRANCHE le relachement du lecteur ⇒ la fermeture part "
               "en rejet et le port reste tenu EN SILENCE")
CIBLES[28] = ("c10",)
MUTANTS[29] = ("plante dans le script un ilot ANGLAIS hors des fabriques "
               "⇒ il reste anglais quand le lecteur bascule")
CIBLES[29] = ("c14",)
MUTANTS[30] = ("DESACCORDE une cle de `MOTS` de son site d'appel ⇒ le "
               "lecteur lit le NOM DE LA CLE a l'ecran, deux fois")
CIBLES[30] = ("c22",)
MUTANTS[31] = ("retire la regle qui garde les DEUX entrees du selecteur "
               "visibles ⇒ la bascule devient A SENS UNIQUE")
CIBLES[31] = ("c23",)
# 🔴 ⛔ IL N'EN RETIRE QU'**UNE**, la ou le mutant 2 les retire TOUTES : c'est
#    le seul qui distingue une fenetre PAR ELEMENT DE LANGUE d'un rayon plat.
MUTANTS[32] = ("retire l'attribution d'UNE SEULE langue ⇒ ce lecteur-la "
               "lit la forme localisee sans savoir d'ou elle sort")
CIBLES[32] = ("c2",)

# ⚠️ LE COMPTE DU CHEMIN NORMAL. Il se PERIME si on ajoute un controle sans le
#    mettre a jour — et c'est voulu : c'est ce qui rend (z) FALSIFIABLE.
CONTROLES_PREVUS = 56

_MUTANT = 0

RE_ID_CTRL = re.compile(r"\((\w+)\)")


def ctrl(ok, libelle, detail=""):
    """UNE assertion, UNE ligne, UN identifiant. ⛔ Aucun controle muet.

    ⚠️ L'IDENTIFIANT VIT DANS LE LIBELLE, ⛔ pas dans un argument a part :
       la campagne de mutants lit les libelles A L'AST en prenant le second
       argument de chaque appel, et A COLONNE FIXE. Une autre signature
       retrecirait SILENCIEUSEMENT la population de cette gate-la."""
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

def lire(chemin):
    try:
        with io.open(os.path.join(RACINE, chemin), encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def plat(txt):
    """Le texte SANS ses retours a la ligne — un motif ne doit ⛔ pas dependre
    de l'endroit ou la prose a ete coupee."""
    return re.sub(r"\s+", " ", txt or "")


def region(txt, ouvrant, fermant):
    """La portion entre deux balises, ⛔ pas le fichier entier."""
    if not txt or ouvrant not in txt or fermant not in txt:
        return ""
    return txt.split(ouvrant, 1)[1].split(fermant, 1)[0]


def sans_commentaires(js):
    """Le script SANS ses commentaires — ⛔ ce qui s'execute, pas ce qui
    l'explique. Une gate qui compte la prose des commentaires rougirait sur la
    documentation de sa propre regle."""
    js = re.sub(r"/\*.*?\*/", " ", js or "", flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", " ", js)


def litteraux(js):
    """Les chaines litterales d'un script, avec leur position."""
    out = []
    for m in re.finditer(r'"((?:[^"\\\n]|\\.)*)"', js or ""):
        out.append((m.start(), m.group(1)))
    return out


def membres_tableau(corps):
    """Le nombre de MEMBRES de premier niveau d'un tableau JavaScript.

    ⚠️ ⛔ PAS UN COMPTE DE VIRGULES : les valeurs de la table de mots sont des
       CONCATENATIONS sur plusieurs lignes, virgules comprises DANS les
       chaines. Un compte naif rendrait « trois valeurs » sur une cle
       parfaitement jumelee — un controle qui rougirait sur la redaction
       JUSTE."""
    n = 1
    prof = 0
    i = 0
    while i < len(corps):
        c = corps[i]
        if c == "\\":
            i += 2
            continue
        if c == '"':
            i += 1
            while i < len(corps) and corps[i] != '"':
                i += 2 if corps[i] == "\\" else 1
        elif c in "([{":
            prof += 1
        elif c in ")]}":
            prof -= 1
        elif c == "," and prof == 0:
            n += 1
        i += 1
    return n


class Arbre(HTMLParser):
    """Un lecteur de structure — ⛔ pas un moteur de rendu.

    Il repond a DEUX questions, et a rien d'autre : *(1)* tout texte VISIBLE
    porteur d'au moins une lettre est-il sous un element de langue ; *(2)* les
    elements de langue vont-ils PAR PAIRES sous chaque parent."""

    VIDES = ("br", "hr", "img", "meta", "input", "link", "source", "track")

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.pile = []
        self.muet = 0
        self.orphelins = []
        self.desapparies = []
        self.vides = []
        self.compte_langue = {"en": 0, "fr": 0}
        self.enfants = [{"en": 0, "fr": 0, "tag": "#racine"}]
        # La pile des elements de langue OUVERTS, pour savoir si chacun a fini
        # par porter au moins une lettre.
        self.langues_ouvertes = []

    def handle_starttag(self, tag, attrs):
        if tag in self.VIDES:
            self._attributs(tag, dict(attrs))
            return
        d = dict(attrs)
        lang = d.get("lang")
        if lang in LANGUES:
            self.compte_langue[lang] += 1
            self.enfants[-1][lang] += 1
        if tag in ("script", "style"):
            self.muet += 1
        self.pile.append((tag, lang))
        self.enfants.append({"en": 0, "fr": 0, "tag": tag})
        if lang in LANGUES:
            self.langues_ouvertes.append([tag, lang, len(self.pile), False])
        self._attributs(tag, d)

    def _attributs(self, tag, d):
        """Le texte pose en ATTRIBUT compte comme du texte visible.

        🔴 `title`, `aria-label`, `alt`, `placeholder` s'AFFICHENT, et la
           feuille de style ne peut pas les cacher : un attribut ne se replie
           pas. Les laisser hors du test faisait sortir de la prose du
           mecanisme par une porte que rien ne gardait."""
        for nom in ATTRIBUTS_TEXTE:
            val = d.get(nom)
            if not val or not RE_LETTRE.search(val):
                continue
            self._marquer_non_vide()
            if not any(l in LANGUES for _, l in self.pile):
                self.orphelins.append("<%s %s=…> : %r"
                                      % (tag, nom, val.strip()[:36]))

    def _marquer_non_vide(self):
        if self.langues_ouvertes:
            self.langues_ouvertes[-1][3] = True

    def handle_endtag(self, tag):
        if tag in self.VIDES:
            return
        for k in range(len(self.pile) - 1, -1, -1):
            if self.pile[k][0] == tag:
                # 🔴 UN FRERE **VIDE** PASSAIT : l'appariement se comptait, il
                #    ne se LISAIT pas. Le lecteur de ce cote-la voyait un blanc.
                while (self.langues_ouvertes
                       and self.langues_ouvertes[-1][2] > k):
                    bal, lg, _prof, plein = self.langues_ouvertes.pop()
                    if not plein:
                        self.vides.append("<%s lang=\"%s\">" % (bal, lg))
                if self.pile[k][0] in ("script", "style") and self.muet:
                    self.muet -= 1
                # Tout ce qui restait ouvert au-dessus se ferme avec lui.
                while len(self.enfants) > k + 1:
                    c = self.enfants.pop()
                    if c["en"] != c["fr"]:
                        self.desapparies.append(
                            "<%s> : %d en / %d fr" % (c["tag"], c["en"], c["fr"]))
                del self.pile[k:]
                return

    def handle_data(self, data):
        if self.muet or not RE_LETTRE.search(data):
            return
        self._marquer_non_vide()
        if not any(l in LANGUES for _, l in self.pile):
            ctx = " > ".join(t for t, _ in self.pile[-3:]) or "#racine"
            self.orphelins.append("%s : %r" % (ctx, data.strip()[:44]))

    def close(self):
        HTMLParser.close(self)
        while self.langues_ouvertes:
            bal, lg, _prof, plein = self.langues_ouvertes.pop()
            if not plein:
                self.vides.append("<%s lang=\"%s\">" % (bal, lg))
        while len(self.enfants) > 1:
            c = self.enfants.pop()
            if c["en"] != c["fr"]:
                self.desapparies.append(
                    "<%s> : %d en / %d fr" % (c["tag"], c["en"], c["fr"]))
        c = self.enfants[0]
        if c["en"] != c["fr"]:
            self.desapparies.append(
                "<%s> : %d en / %d fr" % (c["tag"], c["en"], c["fr"]))


class Replis(HTMLParser):
    """A quelle profondeur de `<details>` chaque GESTE se trouve-t-il ?

    ⚠️ CONDITION NECESSAIRE, ⛔ PAS SUFFISANTE. Qu'aucun bouton ne soit
       replie ⛔ ne dit PAS que la page est lisible — cela dit seulement
       qu'aucun geste n'exige de DEROULER quelque chose, ce qui est la
       moitie MECANIQUE de l'exigence. L'autre moitie reste l'oeil owner.
    """

    VIDES = ("br", "hr", "img", "meta", "input", "link", "source", "track")

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.prof = 0
        self.replies = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "details":
            self.prof += 1
        elif self.prof and ((tag == "button" and d.get("id"))
                            or tag == "esp-web-install-button"):
            self.replies.append(d.get("id") or tag)

    def handle_endtag(self, tag):
        if tag == "details" and self.prof:
            self.prof -= 1


def gestes_replies(page):
    """Rend la liste des gestes qui vivent SOUS un depliant."""
    corps = region(page, "<body>", "</body>")
    if not corps:
        return ["⛔ le corps de la page est introuvable"]
    r = Replis()
    try:
        r.feed(corps)
        r.close()
    except Exception as exc:                              # noqa: BLE001
        return ["⛔ la page ne se lit pas : %s" % exc]
    return r.replies


def lire_structure(page):
    """Rend `(orphelins, desapparies, comptes)` ou `None` si le corps manque."""
    corps = region(page, "<body>", "</body>")
    if not corps:
        return None
    a = Arbre()
    try:
        a.feed(corps)
        a.close()
    except Exception as exc:                              # noqa: BLE001
        return (("⛔ la page ne se lit pas : %s" % exc,), (), (),
                {"en": 0, "fr": 0})
    return a.orphelins, a.desapparies, a.vides, a.compte_langue


def elements_de_langue(page):
    """Les blocs `[lang="en"]` / `[lang="fr"]` du corps, avec leur contenu.

    ⚠️ MOTIF NON GOURMAND ET FERMETURE HOMONYME : il suffit pour la page de
       cette marche, ou aucun element de langue n'en contient un autre du
       MEME nom de balise. Rend `[(langue, contenu), …]`."""
    corps = region(page, "<body>", "</body>")
    return [(m.group(2), m.group(3)) for m in RE_ELEMENT_LANGUE.finditer(corps)]


def attribution_par_element(page, forme, attributions):
    """La forme est-elle ATTRIBUEE **dans chaque element de langue** qui la porte ?

    🔴 C'EST LA FENETRE QUI CHANGE, ⛔ PAS LA PROPRIETE. Un rayon de caracteres
       sur le texte aplati faisait tomber l'attribution de l'AUTRE langue dans
       la fenetre de celle-ci : retirer l'attribution d'UN SEUL cote laissait
       le controle VERT. La fenetre est donc l'element de langue LUI-MEME.
    Rend `(total, orphelins, detail)`."""
    total, orphelins, detail = 0, 0, []
    for langue, contenu in elements_de_langue(page):
        pl = plat(contenu)
        n = pl.count(forme)
        if not n:
            continue
        total += n
        if not any(a in pl for a in attributions):
            orphelins += n
            detail.append("lang=%s" % langue)
    return total, orphelins, detail


def occurrences_barrees(page, chaine):
    """Rend `(total, vives)` pour une chaine dont chaque occurrence doit vivre
    DANS un `<s>…</s>`.

    🔴 « BARRE » EST LA FORME QUE `NFR3` IMPOSE : on annote, on n'efface pas.
       Une occurrence hors barre est une instruction VIVANTE, et c'est
       exactement ce que la mesure du 2026-09-09 a refute."""
    spans = [(m.start(), m.end()) for m in re.finditer(r"<s>.*?</s>", page,
                                                       re.S | re.I)]
    total, vives = 0, 0
    for m in re.finditer(re.escape(chaine), page):
        total += 1
        if not any(a <= m.start() and m.end() <= b for a, b in spans):
            vives += 1
    return total, vives


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
       INCHANGE. ⛔ Le mutant 20 leve EXPRES : il est le temoin de ce cas."""
    e = copy.deepcopy(etat)
    p, r = e["fichiers"], e["regles"]

    if _MUTANT == 1:
        if FORME_SELECTEUR not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(FORME_SELECTEUR, "le port de la carte")
    elif _MUTANT == 2:
        vus = [a for a in ATTRIBUTIONS if a in p.get(PAGE, "")]
        if not vus:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        for a in vus:
            p[PAGE] = p[PAGE].replace(a, "le sélecteur du navigateur")
    elif _MUTANT == 3:
        if FORME_GESTIONNAIRE not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(FORME_GESTIONNAIRE, "un périphérique")
    elif _MUTANT == 4:
        if LIBELLE_BOUTON not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(LIBELLE_BOUTON, "valider")
    elif _MUTANT == 5:
        # ⚠️ IL **DEBARRE**, ⛔ il n'ajoute rien : le texte perime reste le
        #    meme, c'est son statut qui change — de citation datee a
        #    instruction vivante. C'est la faute EXACTE de la page d'avant.
        m = re.search(r"<s>((?:(?!</s>).)*?%s(?:(?!</s>).)*?)</s>"
                      % re.escape(LIBELLE_PERIME), p.get(PAGE, ""), re.S)
        if not m:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(m.group(0), m.group(1), 1)
    elif _MUTANT == 6:
        if 'jouer("stop", bStop)' not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            'bStop.addEventListener("click", function () { jouer("stop", bStop); });',
            'bStop.addEventListener("click", function () { jouer("stop", bStop); });\n'
            'bLiberer.addEventListener("click", function () { jouer("stop", bLiberer); });',
            1)
        if "bLiberer" not in p[PAGE]:
            return e                      # substitution sans effet ⇒ NO-OP
    elif _MUTANT == 7:
        moitie = EFFET_STOP[1][1]
        if moitie not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(moitie, "poser le drapeau")
    elif _MUTANT == 8:
        if BOUTON_CONSOLE not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        # 🔴 IL REPLANTE LE **RENOMMAGE** QUE L'AC REFUSE : l'entree de console
        #    disparait, et c'est le bouton de flash qui herite du mot.
        p[PAGE] = p[PAGE].replace(BOUTON_CONSOLE, "b-installer-et-console")
    elif _MUTANT == 9:
        if ("DEBIT_CONSOLE = " + DEBIT) not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace("DEBIT_CONSOLE = " + DEBIT,
                                  "DEBIT_CONSOLE = 9600", 1)
    elif _MUTANT == 10:
        if CLES_REFUS[2] not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(CLES_REFUS[2], CLES_REFUS[1])
    elif _MUTANT == 11:
        # ⚠️ IL RETIRE LA **FERMETURE** ; le mutant 28, lui, retire le
        #    RELACHEMENT. Deux fautes distinctes du meme controle.
        if ".close()" not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(".close()", ".closeQuandMeme()")
    elif _MUTANT == 12:
        ancre = "</main>"
        if ancre not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            ancre, "  <p>Un texte visible que personne n'a traduit.</p>\n"
                   + ancre, 1)
    elif _MUTANT == 13:
        m = re.search(r'<span lang="fr">', p.get(PAGE, ""))
        if not m:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace('<span lang="fr">', "<span>", 1)
    elif _MUTANT == 14:
        # ⚠️ IL LAISSE LA CLE AVEC **UNE SEULE** VALEUR, ⛔ il ne la supprime
        #    pas et ⛔ il n'ouvre aucun commentaire : le trou doit ressembler a
        #    un oubli de redaction, ⛔ pas a une table cassee. Sa 1re version
        #    ouvrait un `/*` qui AVALAIT la fin de la table : la gate lisait
        #    alors 7 cles au lieu de 48, toutes jumelees, et sortait VERTE.
        m = re.search(r'^(  "[^"]+"\s*:\s*\[)("(?:[^"\\]|\\.)*")\s*,\s*'
                      r'("(?:[^"\\]|\\.)*")(\],)$', p.get(PAGE, ""), re.M)
        if not m:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(m.group(0),
                                  m.group(1) + m.group(2) + m.group(4), 1)
    elif _MUTANT == 15:
        ancre = "function reveler() {"
        if ancre not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            ancre, 'function annoncer(e) { e.textContent = '
                   '"le port a été rendu"; }\n' + ancre, 1)
    elif _MUTANT == 16:
        m = RE_BALISE_RACINE.search(p.get(PAGE, ""))
        if not m or not RE_LANG_ATTR.search(m.group(1)):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        neuve = RE_LANG_ATTR.sub('lang="fr"', m.group(1), count=1)
        p[PAGE] = p[PAGE].replace(m.group(0),
                                  m.group(0).replace(m.group(1), neuve, 1), 1)
    elif _MUTANT == 17:
        m = RE_DEFAUT.search(p.get(PAGE, ""))
        if not m:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(m.group(0),
                                  ':root[data-langue="xx"] [lang="fr"] { display: none', 1)
    elif _MUTANT == 18:
        if SELECTEUR_LANGUE not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace('<p id="%s">' % SELECTEUR_LANGUE,
                                  '<p id="%s" hidden>' % SELECTEUR_LANGUE, 1)
        if 'id="%s" hidden' % SELECTEUR_LANGUE not in p[PAGE]:
            return e                      # substitution sans effet ⇒ NO-OP
    elif _MUTANT == 19:
        r["sortie_anticipee"] = True
    elif _MUTANT == 20:
        # 🔴 IL LEVE EXPRES : c'est la faute « un mutant declare qui MEURT ».
        raise AssertionError("mutant 20 : corps volontairement LEVANT")
    elif _MUTANT == 21:
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
    elif _MUTANT == 32:
        if ATTRIBUTIONS[0] not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(ATTRIBUTIONS[0], "sélecteur du navigateur")
    elif _MUTANT == 25:
        # 🔴 IL REPLANTE LE **RENOMMAGE**, ⛔ il ne supprime pas la console :
        #    le bouton disparait et son id migre SUR l'element de flash —
        #    exactement la regression que l'AC refuse.
        m = re.search(r'<button[^>]*\bid="%s"[^>]*>.*?</button>'
                      % re.escape(BOUTON_CONSOLE), p.get(PAGE, ""), re.S)
        if not m or ELEMENT_FLASH not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(m.group(0), "", 1)
        p[PAGE] = p[PAGE].replace(
            ELEMENT_FLASH, ELEMENT_FLASH + 'id="%s" ' % BOUTON_CONSOLE, 1)
    elif _MUTANT == 26:
        # ⚠️ ⛔ PAS UN ECOUTEUR ADJACENT (deja couvert) : l'appel vit derriere
        #    une FONCTION NOMMEE, si bien que le compte d'ecouteurs reste a 1.
        ancre = "function consoleBoutons(ouverte) {"
        if ancre not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            ancre,
            'function libererLePort(b) { jouer("stop", b); }\n' + ancre, 1)
    elif _MUTANT == 27:
        a, b = CLES_REFUS[1], CLES_REFUS[2]
        if ('"%s"' % a) not in p.get(PAGE, "") or ('"%s"' % b) not in p[PAGE]:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = (p[PAGE].replace('"%s"' % a, '"__DN_ECHANGE__"')
                          .replace('"%s"' % b, '"%s"' % a)
                          .replace('"__DN_ECHANGE__"', '"%s"' % b))
    elif _MUTANT == 28:
        # ⚠️ ⛔ IL NE TOUCHE PAS `close` (deja garde) : il DEBRANCHE le
        #    relachement, si bien que la fermeture part sur un flux verrouille.
        ancre = "try { l.releaseLock(); }"
        if ancre not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(ancre, "try { var _ = l; }", 1)
    elif _MUTANT == 29:
        ancre = 'consoleAjouterMot("console.rendue");'
        if ancre not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            ancre, 'consoleAjouter("port handed back, nothing holds it");', 1)
    elif _MUTANT == 30:
        ancre = '  "%s": [' % CLE_RENDU
        if ancre not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        # ⚠️ LA CLE DE TABLE SEULE EST RENOMMEE ; le SITE D'APPEL reste intact.
        p[PAGE] = p[PAGE].replace(ancre, '  "%s-desaccordee": [' % CLE_RENDU, 1)
    elif _MUTANT == 31:
        m = RE_SELECTEUR_TOUJOURS.search(p.get(PAGE, ""))
        if not m:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            m.group(0),
            '#%s-eteint [lang="en"] { display: ' % SELECTEUR_LANGUE, 1)
    elif _MUTANT == 24:
        t = p.get(PAGE, "")
        i = t.find('<button id="%s"' % BOUTON_CONSOLE)
        j = t.find('<button id="%s"' % BOUTON_CONSOLE_FERMER)
        if i < 0 or j < 0 or j <= i:
            return e                  # ancre disparue ⇒ NO-OP ⇒ rc=3
        # ⚠️ LE DEPLIANT EST **BILINGUE** : le mutant doit replanter UNE
        #    faute — le repli — ⛔ pas en trainer une seconde (un ilot de
        #    langue) qui ferait rougir un AUTRE controle pour rien.
        p[PAGE] = (t[:i] + '<details><summary><span lang="en">Console</span>'
                   + '<span lang="fr">Console</span></summary>'
                   + t[i:j] + "</details>" + t[j:])
    elif _MUTANT == 22:
        e["cibles"][22] = tuple(e["cibles"][22]) + ("c99",)
    elif _MUTANT == 23:
        e["cibles"][99] = ("c1",)      # une cible pour un mutant INEXISTANT
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
    print("dn7-2-2 — LA PAGE DIT LE VRAI NOM DU PORT, ET ON SAIT QUOI Y FAIRE"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)
    print("cible      : %s" % PAGE)
    print("⛔ CETTE GATE N'EXECUTE PAS LE JAVASCRIPT DE LA PAGE : elle lit sa")
    print("   STRUCTURE. Et ⛔ elle ne dit RIEN de la lisibilite — cet")
    print("   arbitrage-la se ferme A L'ŒIL, par une seance owner.")

    # ── (c0) LE PRE-VOL : L'ARBRE EST LISIBLE ───────────────────────────
    print("\n── (c0) LE PRE-VOL — ⛔ AUCUN CONTROLE SUR DU VIDE ────────────────")
    fichiers = {}
    illisibles = []
    for c in FIXES:
        t = lire(c)
        if t is None:
            illisibles.append(c)
        else:
            fichiers[c] = t
    if not ctrl(not illisibles, "(c0) tout fichier attendu est LISIBLE",
                "%d fichier(s) lus" % len(fichiers) if not illisibles
                else "⛔ ILLISIBLE(S) : %s" % " ".join(illisibles)):
        return bilan(1, "un fichier attendu est illisible")

    for n in sorted(MUTANTS):
        if not ctrl(bool(CIBLES.get(n)) and bool(MUTANTS.get(n)),
                    "(c0) le mutant %d a une CIBLE et un LIBELLE" % n,
                    "→ %s" % ",".join(CIBLES.get(n, ()))
                    if CIBLES.get(n) else "⛔ cible ou libelle manquant"):
            return bilan(1, "un mutant est declare a moitie")

    etat = {"fichiers": fichiers,
            "regles": {"sortie_anticipee": False},
            "cibles": dict(CIBLES)}

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

    page = neuf["fichiers"].get(PAGE, "")
    regles = neuf["regles"]
    cibles = neuf["cibles"]
    pl = plat(page)
    script = region(page, "<script>", "</script>")
    style = region(page, "<style>", "</style>")
    # ⛔ CE QUI S'EXECUTE, ⛔ PAS CE QUI L'EXPLIQUE : une gate qui compte la
    #    prose de ses propres commentaires rougit sur sa documentation.
    js = sans_commentaires(script)
    # ⚠️ LE SCRIPT **SANS SA TABLE DE MOTS** : les cles y sont DECLAREES en
    #    tete, avant tout appel. Chercher un site d'appel dans le script
    #    entier trouverait la DECLARATION — et un controle qui mesure une
    #    declaration ⛔ ne mesure aucun branchement.
    _t = RE_TABLE_MOTS.search(js)
    js_appels = js.replace(_t.group(0), " ") if _t else js

    # ── (c1)(c2) LE NOM DU PORT, ET QUI L'AFFICHE ───────────────────────
    print("\n── (c1)(c2) LE SELECTEUR MONTRE UNE LIGNE, ET LA PAGE LE DIT ─────")
    ctrl(FORME_SELECTEUR in pl, "(c1) la page nomme la forme que le selecteur MONTRE",
         "« %s »" % FORME_SELECTEUR if FORME_SELECTEUR in pl
         else "⛔ absente — le selecteur n'affiche QU'ELLE, releve a l'oeil le "
              "2026-09-09, et la page ne la nomme pas")

    total_g, orphelines, ou = attribution_par_element(page, FORME_GESTIONNAIRE,
                                                      ATTRIBUTIONS)
    attribuee = total_g > 0 and orphelines == 0
    ctrl(attribuee, "(c2) la forme localisee est ATTRIBUEE, ⛔ pas offerte",
         "%d mention(s), toutes rendues au Gestionnaire" % total_g if attribuee
         else "⛔ %s — la forme localisee est ce que montre le GESTIONNAIRE DE "
              "PERIPHERIQUES, ⛔ pas le navigateur : l'offrir sans le dire "
              "renvoie chercher une ligne qui n'existe pas"
              % ("elle a ete EFFACEE au lieu d'etre attribuee" if not total_g
                 else "%d occurrence(s) sur %d dans un element de langue qui "
                      "⛔ n'attribue RIEN (%s) — l'attribution de l'AUTRE "
                      "langue ⛔ n'attribue pas celle-ci"
                      % (orphelines, total_g, " ".join(ou))))

    # ── (c3)(c4) LE LIBELLE DU BOUTON, ET CELUI QUI EST PERIME ──────────
    print("\n── (c3)(c4) LE BOUTON S'APPELLE COMME IL S'AFFICHE ───────────────")
    ctrl(LIBELLE_BOUTON in pl, "(c3) la page ecrit le libelle RELEVE du bouton",
         "« %s »" % LIBELLE_BOUTON if LIBELLE_BOUTON in pl
         else "⛔ absent — le selecteur ecrit « %s » sur son bouton, et une "
              "page qui en nomme un autre envoie chercher ce qui n'y est pas"
              % LIBELLE_BOUTON)

    tot_p, vives = occurrences_barrees(page, LIBELLE_PERIME)
    ctrl(tot_p > 0 and vives == 0,
         "(c4) le libelle PERIME est BARRE, ⛔ pas efface",
         "%d occurrence(s), toutes barrees" % tot_p if tot_p and not vives
         else "⛔ %s — `NFR3` : on annote, on n'efface pas ; et une occurrence "
              "hors barre redevient une instruction VIVANTE"
              % ("il a ete EFFACE : l'ancienne formulation doit rester "
                 "lisible, datee" if not tot_p
                 else "%d occurrence(s) sur %d hors d'un `<s>`" % (vives, tot_p)))

    # ── (c5)(c6) UN SEUL BOUTON POSTE `stop` ────────────────────────────
    print("\n── (c5)(c6) LE CHOIX NE SE POSE PLUS : UNE SEULE COMMANDE ────────")
    # 🔴 LE COMPTE DES **POSTES** ENTRE DANS LE PREDICAT, ⛔ il ne decore plus
    #    le message d'echec. Mesure : un second bouton dont l'appel vit
    #    derriere une FONCTION NOMMEE laisse `len(ecoutes) == 1` — l'ecart que
    #    cette marche vient de fermer pouvait donc revenir, gate VERTE.
    postes = RE_JOUER_STOP.findall(js)
    ecoutes = RE_ECOUTE_STOP.findall(js)
    unique = (len(ecoutes) == 1 and len(postes) == 1
              and BOUTON_DISPARU not in page)
    ctrl(unique, "(c5) UN SEUL bouton poste le verbe `stop`",
         "1 branchement, et `%s` a disparu de la page" % BOUTON_DISPARU
         if unique
         else "⛔ %s — deux boutons qui postent le MEME verbe sur le MEME port "
              "et rendent la MEME sortie font choisir entre deux commandes "
              "qu'on croit distinctes"
              % ("%d branchement(s) de `stop` sur un clic, %d appel(s) du "
                 "verbe" % (len(ecoutes), len(postes))
                 if len(ecoutes) != 1 or len(postes) != 1
                 else "`%s` est encore dans la page" % BOUTON_DISPARU))

    moities = []
    for a, b in EFFET_STOP:
        if a not in pl or b not in pl:
            moities.append("%s / %s" % (a, b))
    ctrl(not moities, "(c6) le bouton nomme TOUT son effet, 2 langues",
         "arreter l'agent ET rendre le port, des deux cotes" if not moities
         else "⛔ moitie(s) manquante(s) : %s — couper l'effet en deux libelles "
              "est EXACTEMENT ce qui a cree l'ecart" % " · ".join(moities))

    # ── (c7)(c8)(c9)(c10) LA CONSOLE, DISTINCTE DU FLASH ────────────────
    print("\n── (c7)…(c10) RELIRE SA CARTE SANS LA REFLASHER ──────────────────")
    # 🔴 ON MESURE LA **CONTENANCE**, ⛔ PLUS DEUX OFFSETS. Comparer
    #    `page.index(a) != page.index(b)` sur deux sous-chaines DIFFERENTES est
    #    une TAUTOLOGIE : elles ne peuvent jamais tomber au meme offset.
    #    DEMONTRE : poser l'id de console SUR l'element de flash laissait la
    #    gate verte — c'est-a-dire le renommage que l'AC refuse mot pour mot.
    id_console = 'id="%s"' % BOUTON_CONSOLE
    bloc_flash = region(page, ELEMENT_FLASH, "</esp-web-install-button>")
    dans_le_flash = id_console in bloc_flash
    sur_l_element = re.search(
        re.escape(ELEMENT_FLASH.rstrip()) + r"[^>]*" + re.escape(id_console),
        page) is not None
    distincte = (id_console in page and ELEMENT_FLASH in page
                 and not dans_le_flash and not sur_l_element)
    ctrl(distincte, "(c7) l'entree de console est DISTINCTE du flash",
         "`%s` vit HORS de l'element de flash" % BOUTON_CONSOLE
         if distincte
         else "⛔ %s — ⛔ un renommage du bouton de flash ne suffit pas : le "
              "geste doit etre SEPARE, et l'AC le dit mot pour mot"
              % ("le bouton de console manque a la page"
                 if id_console not in page
                 else "l'element de flash manque a la page"
                 if ELEMENT_FLASH not in page
                 else "l'id de console est PORTE PAR l'element de flash"
                 if sur_l_element
                 else "l'id de console vit DANS l'element de flash"))

    # ⚠️ **TOUTES** LES OUVERTURES, ⛔ PAS LA PREMIERE : le detail affirme
    #    « declare une fois », et un `.search` laissait une SECONDE ouverture a
    #    un autre debit parfaitement invisible plus bas dans le script.
    declare = RE_DEBIT_DECLARE.search(js)
    ouvertures = RE_OUVERTURE.findall(js)
    hors_constante = [x for x in ouvertures if x != "DEBIT_CONSOLE"]
    bon_debit = (declare is not None and declare.group(1) == DEBIT
                 and len(ouvertures) >= 1 and not hors_constante)
    ctrl(bon_debit, "(c8) la console lit a %s bauds, ⛔ pas suppose" % DEBIT,
         "declare une fois, et les %d ouverture(s) s'y referent"
         % len(ouvertures) if bon_debit
         else "⛔ %s — le debit vient de TROIS sources concordantes du depot, "
              "⛔ pas d'une habitude"
              % ("aucun debit declare" if not declare
                 else "declare a %s" % declare.group(1) if declare.group(1) != DEBIT
                 else "aucune ouverture de port" if not ouvertures
                 else "ouverture(s) HORS de la constante declaree : %s"
                      % " ".join(hors_constante)))

    manquants = [c for c in CLES_REFUS if ('"%s"' % c) not in js_appels]
    deplacees = []
    rangs = []
    for cle, marqueur in ANCRES_REFUS:
        if cle in manquants:
            continue
        i = js_appels.index('"%s"' % cle)
        rangs.append((cle, i))
        if marqueur not in js_appels or js_appels.index(marqueur) > i:
            deplacees.append("%s (hors de `%s`)" % (cle, marqueur))
    ordre = [c for c, _ in sorted(rangs, key=lambda x: x[1])]
    attendu = [c for c, _ in ANCRES_REFUS if c not in manquants]
    if ordre != attendu:
        deplacees.append("rang ECHANGE : %s au lieu de %s"
                         % (" < ".join(ordre), " < ".join(attendu)))
    ctrl(not manquants and not deplacees,
         "(c9) les TROIS refus sont ANCRES dans LEUR branche",
         "%d cle(s), chacune dans la branche qui la decide" % len(CLES_REFUS)
         if not manquants and not deplacees
         else "⛔ %s — ⛔ jamais « aucune carte » pour un port REFUSE : le port "
              "existe et il a ete choisi, c'est son OUVERTURE qui echoue"
              % ("cle(s) absente(s) : %s" % " ".join(manquants) if manquants
                 else "cle(s) hors de LEUR branche : %s" % " · ".join(deplacees)))

    # ⚠️ ON CHERCHE DANS `js`, ⛔ PAS DANS `script` : la prose des commentaires
    #    n'est pas du code, et une gate qui la compte peut sortir verte sur un
    #    mecanisme ABSENT mais bien DOCUMENTE.
    sequence = RE_SEQUENCE_RENDU.search(js) is not None
    rend = (sequence and ('"%s"' % CLE_RENDU) in js
            and ('id="%s"' % BOUTON_CONSOLE_FERMER) in page)
    ctrl(rend, "(c10) le port est RELACHE puis FERME, dans cet ordre",
         "annuler ⇒ relacher ⇒ fermer, et un message" if rend
         else "⛔ %s — un flux encore VERROUILLE fait partir la fermeture en "
              "rejet : le port reste tenu EN SILENCE, et l'agent ne repart pas"
              % ("la sequence annuler ⇒ relacher ⇒ fermer manque au code"
                 if not sequence
                 else "le message de restitution manque"
                 if ('"%s"' % CLE_RENDU) not in js
                 else "le bouton de fermeture manque a la page"))

    # ── (c11)(c12) LA STRUCTURE DES DEUX LANGUES ────────────────────────
    print("\n── (c11)…(c14) LES DEUX LANGUES, ET AUCUN ILOT ───────────────────")
    lu = lire_structure(page)
    if lu is None:
        ctrl(False, "(c11) tout texte visible est SOUS le mecanisme",
             "⛔ la page n'a pas de corps lisible")
        ctrl(False, "(c12) chaque element de langue a sa JUMELLE",
             "⛔ la page n'a pas de corps lisible")
    else:
        orphelins, desapparies, vides, comptes = lu
        ctrl(not orphelins, "(c11) tout texte visible est SOUS le mecanisme",
             "%d element(s) `en` et %d `fr`, et 0 ilot"
             % (comptes["en"], comptes["fr"]) if not orphelins
             else "⛔ %d texte(s) visible(s) HORS des deux langues : %s — un "
                  "seul suffit a laisser un ilot que la bascule ne touche pas"
                  % (len(orphelins), " · ".join(orphelins[:3])))
        ctrl(not desapparies and not vides
             and comptes["en"] == comptes["fr"] and comptes["en"] > 0,
             "(c12) chaque element de langue a sa JUMELLE, PLEINE",
             "%d paire(s), appariees parent par parent, et toutes portent du "
             "texte" % comptes["en"]
             if not desapparies and not vides
             and comptes["en"] == comptes["fr"]
             else "⛔ %s — ⛔ une cle sans jumelle est un DEFAUT, pas une "
                  "approximation, et une jumelle VIDE n'est pas une jumelle : "
                  "le lecteur de ce cote-la voit un blanc"
                  % ("parent(s) desapparie(s) : %s" % " · ".join(desapparies[:3])
                     if desapparies
                     else "element(s) de langue VIDE(S) : %s"
                          % " · ".join(vides[:3]) if vides
                     else "%d `en` pour %d `fr`" % (comptes["en"], comptes["fr"])))

    # ── (c13)(c14) LA PROSE DU SCRIPT ───────────────────────────────────
    table = RE_TABLE_MOTS.search(js)
    if not table:
        ctrl(False, "(c13) chaque cle de `MOTS` porte DEUX valeurs",
             "⛔ la table de mots ne se lit pas dans le script")
    else:
        corps_table = table.group(1)
        cles = RE_CLE_MOTS.findall(corps_table)
        boiteuses = []
        for m in re.finditer(r'^\s{2}"([^"]+)"\s*:\s*\[(.*?)\](?=\s*[,}])',
                             corps_table + "\n}", re.S | re.M):
            n = membres_tableau(m.group(2))
            if n != len(LANGUES):
                boiteuses.append("%s ⇒ %d" % (m.group(1), n))
        ctrl(bool(cles) and not boiteuses,
             "(c13) chaque cle de `MOTS` porte DEUX valeurs",
             "%d cle(s), toutes jumelees" % len(cles)
             if cles and not boiteuses
             else "⛔ %s — ⛔ UNE CLE SANS JUMELLE EST UN DEFAUT : c'est la "
                  "seule facon de rendre « aucun ilot » mecanique"
                  % ("la table est vide" if not cles
                     else "cle(s) boiteuse(s) : %s" % " · ".join(boiteuses[:4])))

    # ⚠️ LA TABLE SE RETIRE DU SCRIPT **DEJA NETTOYE** : elle porte elle-meme
    #    un commentaire, et retrancher la forme BRUTE d'un texte nettoye ne
    #    retranche RIEN — la gate rougissait alors sur sa propre table.
    js_hors = js_appels
    # 🔴 LA REGLE EST « TOUTE PROSE PASSE PAR UNE FABRIQUE », ⛔ PAS « toute
    #    prose est accentuee » : un ilot ANGLAIS reste anglais quand le lecteur
    #    bascule en francais, et c'est exactement ce que l'AC de langue
    #    interdit. ⇒ tout litteral PORTEUR D'UNE LETTRE qui n'est ni un jeton
    #    technique ni l'argument d'une fabrique est un ilot.
    hors = []
    for pos, texte in litteraux(js_hors):
        brut = texte.strip()
        if brut in DIRECTIVES:
            continue
        # ⚠️ `\n` porte une lettre DANS LE FICHIER, ⛔ pas a l'ecran.
        if not RE_LETTRE.search(RE_ECHAPPEMENT.sub("", brut)):
            continue
        amont = js_hors[max(0, pos - 40):pos]
        # Le litteral est-il CONSOMME par une fabrique ? On regarde ce qui
        # precede immediatement son ouverture.
        if any(f in amont for f in FABRIQUES):
            continue
        # ⛔ Une valeur COMPAREE n'est pas affichee : elle vient du serveur.
        if RE_COMPARAISON.search(amont):
            continue
        if RE_NON_PROSE.match(brut) and not RE_ACCENT.search(brut):
            continue
        hors.append(brut[:44])
    ctrl(not hors, "(c14) toute prose du script passe par une FABRIQUE",
         "0 litteral de prose hors des %d fabriques" % len(FABRIQUES)
         if not hors
         else "⛔ %d litteral(aux) de prose hors du mecanisme : %s — la "
              "bascule ne les toucherait pas, et l'ilot serait invisible"
              % (len(hors), " · ".join(hors[:3])))

    # ── (c15)(c16)(c17) LE DEFAUT ANGLAIS EST STRUCTUREL ────────────────
    print("\n── (c15)(c16)(c17) LE DEFAUT ANGLAIS, ⛔ PAS PROMIS ──────────────")
    balise = RE_BALISE_RACINE.search(page)
    attr = RE_LANG_ATTR.search(balise.group(1)) if balise else None
    racine = attr is not None and attr.group(1).lower() == "en"
    ctrl(racine, "(c15) la racine du document est `lang=\"en\"`",
         "le defaut est porte par le DOCUMENT" if racine
         else "⛔ absente — le defaut anglais doit tenir AVANT que le moindre "
              "script tourne : porte par un script, il ne serait plus "
              "structurel, il serait promis")

    defaut = RE_DEFAUT.search(style) is not None
    bascule = RE_BASCULE.search(style) is not None
    ctrl(defaut and bascule, "(c16) la feuille de style cache l'autre langue",
         "le francais est cache PAR DEFAUT, et l'anglais a la bascule"
         if defaut and bascule
         else "⛔ %s — sans elle, les DEUX langues s'afficheraient l'une sous "
              "l'autre, et la page serait illisible dans les deux"
              % ("la regle de defaut manque" if not defaut
                 else "la regle de bascule manque"))

    # ⚠️ ⛔ AUCUN `index` NU : une page sans `<h2` levait un `ValueError`, donc
    #    un Traceback SANS ligne `BILAN` — la signature exacte d'une gate MORTE,
    #    que ce depot a deja nommee et payee.
    id_langue = 'id="%s"' % SELECTEUR_LANGUE
    visible = (id_langue in page
               and ('id="%s" hidden' % SELECTEUR_LANGUE) not in page
               and "<h2" in page
               and page.index(id_langue) < page.index("<h2"))
    ctrl(visible, "(c17) le selecteur de langue est VISIBLE, en tete",
         "avant la premiere section" if visible
         else "⛔ %s — un choix qu'il faut trouver n'est pas un choix offert"
              % ("absent de la page" if id_langue not in page
                 else "la page ne porte AUCUN `<h2` : le controle refuse de "
                      "conclure plutot que de lever" if "<h2" not in page
                 else "masque, ou pose apres le contenu"))

    # ── (c22) LES CLES DE LA TABLE ⇄ LES CLES DEMANDEES ────────────────
    # 🔴 UNE CLE DESACCORDEE DE SON SITE D'APPEL EST **VISIBLE A L'ECRAN** :
    #    le repli de la fabrique ecrit `⛔ <nom de la cle>` — DANS LES DEUX
    #    LANGUES — au moment precis ou la page doit dire quelque chose d'utile.
    #    DEMONTRE : renommer la cle de table sans toucher l'appel laissait la
    #    gate VERTE.
    demandees = set()
    for f in FABRIQUES:
        motif = (re.escape(f) + r'\s*"[^"]*"\s*,\s*"([^"]+)"'
                 if f in FABRIQUES_CLE_2
                 else re.escape(f) + r'\s*"([^"]+)"')
        for m in re.finditer(motif, js):
            demandees.add(m.group(1))
    table2 = RE_TABLE_MOTS.search(js)
    posees = set(RE_CLE_MOTS.findall(table2.group(1))) if table2 else set()
    orphelines = sorted(demandees - posees)
    ctrl(bool(demandees) and bool(posees) and not orphelines,
         "(c22) toute cle demandee EXISTE dans la table",
         "%d cle(s) demandee(s), toutes posees parmi %d"
         % (len(demandees), len(posees))
         if demandees and posees and not orphelines
         else "⛔ %s — le repli de la fabrique ecrit le NOM DE LA CLE a "
              "l'ecran, dans les DEUX langues"
              % ("la table de mots ne se lit pas" if not posees
                 else "aucune cle n'est demandee : les fabriques ne sont "
                      "appelees NULLE PART" if not demandees
                 else "cle(s) demandee(s) et ABSENTE(S) de la table : %s"
                      % " ".join(orphelines[:4])))

    # ── (c23) LA BASCULE RESTE ATTEIGNABLE **DANS LES DEUX SENS** ──────
    toujours = RE_SELECTEUR_TOUJOURS.search(style) is not None
    ctrl(toujours, "(c23) les 2 entrees du selecteur restent VISIBLES",
         "la regle de style les soustrait au masquage general" if toujours
         else "⛔ sans elle, la regle generale masque le bouton de l'AUTRE "
              "langue : le choix est offert UNE fois, puis inatteignable — "
              "une bascule a sens unique n'est pas une bascule")

    if regles["sortie_anticipee"]:
        return bilan(0)

    # ── (c18)(c19)(c20) LA RECIPROQUE, MECANIQUE ────────────────────────
    print("\n── (c18)(c19)(c20) AUCUN CONTROLE GARDE PAR ZERO MUTANT ──────────")
    # 🔴 « N mutants, N vus rougir » prouve `mutant ⇒ rouge`, ⛔ JAMAIS
    #    `controle ⇒ couvert`. Les deux sens sont mesures, SEPAREMENT.
    lus_ast = ids_par_ast()
    reels = set(ids_emis) | (lus_ast or set())
    vises = set()
    for v in cibles.values():
        vises.update(v)
    nus = sorted(reels - vises, key=lambda s: (len(s), s))
    # 🔴 `(c21)` — LA MOITIE MECANIQUE DE `AC7.2.2.2`, ET ⛔ RIEN DE PLUS.
    #    L'AC dit « le geste suivant est identifiable SANS DEROULER QUOI QUE
    #    CE SOIT ». Qu'un geste soit lisible ne se calcule pas ; qu'il soit
    #    derriere un depliant, SI. ⇒ ce controle garde la condition
    #    NECESSAIRE, et la suffisante reste l'oeil de l'owner — c'est ecrit
    #    en toutes lettres au bas de cette gate.
    replies = gestes_replies(page)
    ctrl(not replies, "(c21) ⛔ aucun geste n'est derriere un repli",
         "tous les gestes sont a profondeur 0 de `<details>`" if not replies
         else "⛔ %d geste(s) REPLIE(S) : %s — il faut DEROULER pour voir quoi "
              "faire, ce que l'AC interdit mot pour mot"
              % (len(replies), " · ".join(replies)))

    ctrl(not nus and lus_ast is not None,
         "(c18) chaque controle est vise par >= 1 mutant",
         "%d controle(s) lu(s) a l'AST, %d cible(s) declaree(s)"
         % (len(reels), len(vises)) if not nus and lus_ast is not None
         else ("⛔ %d CONTROLE(S) GARDE(S) PAR RIEN : %s"
               % (len(nus), " · ".join(nus)) if nus
               else "⛔ LA SOURCE NE S'ANALYSE PAS A L'AST — la population de "
                    "ce controle est INCONNUE, ⛔ pas vide"))
    perimees = sorted(vises - reels, key=lambda s: (len(s), s))
    ctrl(not perimees, "(c19) chaque cible de mutant est un controle REEL",
         "%d cible(s) confrontee(s)" % len(vises) if not perimees
         else "⛔ %d CIBLE(S) PERIMEE(S) : %s — un mutant qui vise un controle "
              "inexistant ⛔ ne garde rien"
              % (len(perimees), " · ".join(perimees)))
    orph = sorted(set(cibles) - set(MUTANTS))
    sans_cible = sorted(set(MUTANTS) - set(cibles))
    ctrl(not orph and not sans_cible,
         "(c20) `CIBLES` et `MUTANTS` se correspondent",
         "%d mutant(s), %d cible(s), cle a cle" % (len(MUTANTS), len(cibles))
         if not orph and not sans_cible
         else "⛔ cible(s) SANS mutant : %s · mutant(s) SANS cible : %s"
              % (orph or "—", sans_cible or "—"))

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : que la page soit LISIBLE.")
    print("   « Le geste suivant est identifiable sans rien derouler » se")
    print("   ferme A L'ŒIL DE L'OWNER, et par rien d'autre — un ratio de")
    print("   texte ne dit pas si quelqu'un a su quoi faire.")
    return bilan(1 if ko_total[0] else 0)


if __name__ == "__main__":
    sys.exit(main())

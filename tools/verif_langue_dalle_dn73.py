#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn7-3 — LA LANGUE SE CHOISIT A L'INSTALLATION, ET LA CARTE L'A AU 1er BOOT.

======================= CE QUE CETTE GATE GARDE, ET POURQUOI ================

Le mecanisme de langue est LIVRE cote firmware — commande console `langue`,
cle NVS, table a une definition par chaine, gate dediee. Ce que `dn7-3` ajoute
n'est ⛔ PAS un mecanisme : c'est **LE CHOIX**, pose la ou l'inconnu passe, et
le geste qui l'ecrit dans la carte. Cette gate garde ce choix et ce geste, pour
une raison ecrite plutot que supposee :

  🔴 RIEN DANS CE DEPOT N'EXECUTE LE JAVASCRIPT DE `installeur/index.html`.
     ⇒ sans une garde STATIQUE, tout ce que cette marche ecrit dans la page
     n'est rejoue par PERSONNE.

  1. **LE CHOIX EXISTE, A DEUX POSITIONS, ET IL PRECEDE LE FLASH.** Il est
     visible sans rien derouler, et l'anglais y est marque **DANS LE
     DOCUMENT** — ⛔ pas pose par un script qui aurait pu ne pas tourner.
  2. **DEUX LANGUES DIFFERENTES SONT EN JEU.** Celle de la PAGE (livree par
     `dn7-2-2`) et celle de la DALLE (ici). La page le DIT, dans les deux
     langues, et les deux mecanismes restent DISTINCTS.
  3. **LE DEFAUT ANGLAIS EST STRUCTUREL** : il se prouve **par l'ABSENCE
     d'ecriture**, ⛔ pas par une ecriture qui vaudrait « anglais ». La garde
     qui l'assure PRECEDE tout appel d'ecriture sur le port.
  4. **LE TRANSPORT REND SON VERROU SUR LES DEUX CHEMINS**, et l'attente est
     alimentee par l'entonnoir de lecture DEJA en place — ⛔ pas par un second
     lecteur, que `port.readable` n'admettrait pas.
  5. **CINQ ISSUES, CINQ CLES DISTINCTES** : posee · refusee · posee A CHAUD
     mais ⛔ NON PERSISTEE · sans reponse · pas d'invite — plus DEUX cles qui ne
     classent rien et disent ce qu'il advient du PORT, et une septieme pour le
     port qu'on n'a pas pu prendre. **SEPT ancres**, donc, ⛔ pas quatre.
     Chacune est ANCREE dans SA branche, et le succes n'est atteignable que
     **depuis la relecture** — ⛔ jamais depuis l'ordre envoye. Publier une
     ignorance comme un constat est la ligne interdite.
     ⚠️ `(c11)` compte les QUATRE de la matrice du dossier ; `(c21)` garde la
     cinquieme, `(c12)` garde les sept ancres, et `(c23)` les cadres.
  6. **LES REPONSES DE LA CARTE SONT RELUES DANS `firmware/`.** Si le firmware
     cesse d'imprimer ce que la page attend, cette gate ROUGIT — et la page,
     elle, ne cite ⛔ AUCUN numero de ligne, qui se perimerait au 1er commit.

── CE QU'ELLE NE PROUVE ⛔ PAS, ECRIT PLUTOT QUE TU ─────────────────────────

⛔ Elle n'execute PAS le JavaScript de la page : elle lit sa STRUCTURE.
⛔ Elle n'ouvre AUCUN port serie et ne parle a AUCUNE carte. Que la langue soit
   VRAIMENT posee, et qu'elle survive a un cycle d'alimentation, se lit AU
   BANDEAU DE LA DALLE — une seance carte, et rien d'autre.
⛔ Elle ne mesure pas le delai entre la fin du flash et la reponse du REPL :
   il est NON MESURE, et c'est precisement pourquoi le geste est EXPLICITE.
⛔ Elle ne touche pas au choix de langue de la PAGE, qui est un autre sujet.

Emploi :
    python3 tools/verif_langue_dalle_dn73.py
    python3 tools/verif_langue_dalle_dn73.py --liste-mutants
    python3 tools/verif_langue_dalle_dn73.py --mutant <n>

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
# 🔴 LE FIRMWARE EST LU, ⛔ JAMAIS ECRIT (`NFR7.2`). Cette gate relit les
#    litteraux de reponse que la page ancre : si le firmware cesse de les
#    imprimer, la page attendrait une phrase que la carte ne dit plus.
CONSOLE_C = "firmware/desknode/main/dn_console.c"
LANGUE_C = "firmware/desknode/main/dn_langue.c"
# 🔴 CES DEUX-LA SONT LUS POUR UNE RAISON PRECISE : ils portent des journaux qui
#    disent `REFUS` **sans aucun rapport avec la langue**, sur la MEME console.
#    Ils sont le TEMOIN NEGATIF du classement, et ⛔ ils ne sont pas inventes.
CAPTEURS_C = "firmware/desknode/main/dn_capteurs.c"
RTC_C = "firmware/desknode/main/dn_rtc.c"
FIXES = (PAGE, CONSOLE_C, LANGUE_C, CAPTEURS_C, RTC_C)

# ── LE CHOIX DE LA DALLE, ET CELUI DE LA PAGE — ⛔ A NE PAS CONFONDRE ──────
SECTION_DALLE = "sec-langue-dalle"
# La borne BASSE du bloc de choix — elle sert au mutant qui le DEPLACE.
MARQUE_FIN_CHOIX = "<!-- fin du choix de la langue de la dalle -->"
BOUTON_DALLE_EN = "b-dalle-en"
BOUTON_DALLE_FR = "b-dalle-fr"
BOUTON_POSER = "b-langue-poser"
# ⛔ CEUX-CI APPARTIENNENT A `dn7-2-2` ET NE SE TOUCHENT PAS : ils sont ici
#    pour que la gate puisse EXIGER qu'ils restent DISTINCTS.
SECTION_PAGE = "sec-langue"
BOUTON_PAGE_EN = "b-langue-en"
BOUTON_PAGE_FR = "b-langue-fr"
ELEMENT_FLASH = "<esp-web-install-button "

# ── CE QUE LA PAGE DOIT ECRIRE, DANS LES DEUX LANGUES ─────────────────────
# 🔴 « LA PAGE LE DIT » N'EST PAS UNE FORMULE : le lecteur doit apprendre, DANS
#    SA LANGUE, que ce choix-la est celui de la DALLE et ⛔ pas celui de la
#    page qu'il lit. Une mention posee d'un SEUL cote laisse l'autre lecteur
#    devant deux selecteurs qu'il croira identiques.
MENTION_DALLE = {"en": "The language of the panel",
                 "fr": "La langue de la dalle"}
MENTION_PAS_LA_PAGE = {"en": "not the language of this page",
                       "fr": "pas celle de cette page"}

# ── L'ORDRE ENVOYE, ET LES CODES QUE LE BINAIRE PORTE ─────────────────────
RE_CMD_DECLAREE = re.compile(r'var CMD_LANGUE = "([^"]*)";')
CMD_ATTENDUE = "langue"
RE_CODES_DECLARES = re.compile(r"var CODES_DALLE = \[([^\]]*)\];")
RE_ENVOI_ORDRE = re.compile(r'consoleEcrire\(\s*CMD_LANGUE \+ " " \+ code\s*\)')
# La RELECTURE : `langue` SANS argument. ⛔ Relire l'ordre envoye ne prouverait
# que l'ordre — c'est l'ETAT qu'on relit.
RE_RELECTURE = re.compile(r"consoleEcrire\(\s*CMD_LANGUE\s*\)")
# Les codes que le binaire porte VRAIMENT, lus dans `dn_langue.c`.
RE_CODE_FIRMWARE = re.compile(r'\[DN_LANGUE_(\w+)\]\s*=\s*"(\w+)"')

# ── LE DEFAUT ANGLAIS, ECRIT DANS LE DOCUMENT ─────────────────────────────
RE_DALLE_EN_PRESSE = re.compile(
    r'<button id="' + BOUTON_DALLE_EN + r'"[^>]*aria-pressed="true"')
RE_DALLE_FR_RELACHE = re.compile(
    r'<button id="' + BOUTON_DALLE_FR + r'"[^>]*aria-pressed="false"')
RE_POSER_DALLE_APPEL = re.compile(r'poserDalle\(\s*"')
RE_CLIC = re.compile(r'addEventListener\(\s*"click"')
GARDE_DEFAUT = "if (code === LANGUE_DALLE_DEFAUT) {"

# ── LE TRANSPORT ──────────────────────────────────────────────────────────
RE_FONCTION = r"function %s\([^)]*\) \{(.*?)\n\}"
NOM_ECRIRE = "consoleEcrire"
NOM_POSE = "poserLangueDalle"
RE_GET_WRITER = re.compile(r"\.getWriter\(\)")
RE_RELACHE = re.compile(r"\.releaseLock\(\)")
# 🔴 UN SEUL LECTEUR, ET C'EST CELUI DE LA CONSOLE. `port.readable` n'admet
#    QU'UN lecteur : en prendre un second pour l'attente echouerait, et le
#    liberer casserait l'affichage du journal. ⇒ l'attente est alimentee par
#    `consoleAjouter`, l'entonnoir UNIQUE ou atterrit chaque morceau decode.
RE_GET_READER = re.compile(r"\.getReader\(\)")
RE_NOURRIR_DEPUIS_AJOUT = re.compile(
    r"function consoleAjouter\(txt\) \{[\s\S]{0,400}?langueNourrir\(txt\)")
GARDE_REENTRANCE = "if (langueEnVol) { return null; }"
ANCRE_ATTENTE_INVITE = 'langueArmer(RE_INVITE_CARTE, DELAI_INVITE, "")'
# 🔴 ET LES **VALEURS** SONT ANCREES, ⛔ pas seulement les identifiants : une page
#    livree avec `0` laisserait cette gate ET le banc VERTS, et l'attente de
#    l'invite deviendrait un no-op — l'ordre partirait sur une carte muette,
#    exactement ce que `(c10)` existe pour interdire. ⚠️ Le plancher est une
#    BORNE BASSE, ⛔ pas la valeur : le banc les repose a la baisse, et c'est
#    voulu ; ce qui est interdit, c'est de LIVRER un delai qui n'attend rien.
RE_DELAI = re.compile(r"var (DELAI_INVITE|DELAI_REPONSE) = (\d+);")
PLANCHER_DELAI = 1000
ANCRE_REVEIL = 'var reveil = consoleEcrire("");'

# ── LES QUATRE ISSUES, ET LA CINQUIEME QUI N'EN EST PAS UNE ───────────────
# 🔴 ELLES SONT QUATRE, ⛔ PAS UNE. « posee » pour un silence, ou « refusee »
#    pour une absence d'invite, publierait une IGNORANCE comme un CONSTAT.
#    ⇒ chaque cle porte *(a)* LE MARQUEUR DE SA BRANCHE, qui doit la preceder,
#      et *(b)* SON RANG dans le source. Echanger deux cles inverse le rang, et
#      rien d'autre ne le ferait.
CLE_DEFAUT = "langue.defaut-anglais"
# 🔴 LA CINQUIEME ISSUE. La carte imprime son avertissement, PUIS
#    reconstruit la scene, PUIS imprime la ligne de succes, et rend un code
#    NON NUL : elle doit donc etre reconnue par SON litteral, AVANT celui du
#    succes, et ⛔ ne retomber ni sur « refusee » (faux : la dalle a change)
#    ni sur « posee » (faux : ca ne survivra pas).
CLE_NON_PERSISTEE = "langue.non-persistee"
# ⛔ LE PORT N'A PAS PU ETRE PRIS, ET PERSONNE D'AUTRE NE L'A DIT.
CLE_SANS_PORT = "langue.port-indisponible"
ANCRES_ISSUES = (
    (CLE_DEFAUT, "code === LANGUE_DALLE_DEFAUT"),
    (CLE_SANS_PORT, "var sansPort = function ()"),
    ("langue.pas-d-invite", "DELAI_INVITE"),
    ("langue.sans-reponse", "DELAI_REPONSE"),
    (CLE_NON_PERSISTEE, "RE_NVS_REFUSEE.test("),
    ("langue.refusee", "RE_REFUS_CARTE.test("),
    ("langue.posee", "RE_LECTURE_CARTE.exec("),
)
# Les QUATRE issues au sens de la matrice — le defaut anglais n'en est pas une :
# il ⛔ n'ecrit rien, donc il ne peut ni reussir ni echouer. La CINQUIEME, elle,
# a son propre controle : voir `la_cinquieme_issue_a_sa_cle`.
CLES_ISSUES = ("langue.posee", "langue.refusee",
               "langue.sans-reponse", "langue.pas-d-invite")
RE_ANNONCE = r'blocMot\(\s*"etat-langue"\s*,\s*"%s"'
# 🔴 CE QUE LE GESTE FAIT DU PORT SE DIT A CHAQUE ISSUE. ⛔ Un port tenu en
#    silence empeche l'agent de repartir, et `dn7-2` l'a deja nomme.
# ⚠️ L'APPEL PORTE **SA CLE**, et le controle la CONFRONTE a celle qui vient
#    d'etre annoncee : sans ca, une issue pourrait se dessiner comme une autre.
APPEL_PORT = "languePort("
CLES_PORT = ("langue.port-tenu", "langue.port-libre")
# La SEULE annonce qui ⛔ ne dit PAS le port : le temoin de travail EN COURS,
# qui n'est pas une issue. ⛔ Liste FERMEE — toute autre annonce du geste doit
# dire ce qu'il advient du port, **le defaut anglais COMPRIS** : lui non plus
# n'a pas le droit de laisser le lecteur deviner si la page tient le port.
ANNONCES_SANS_PORT = ("langue.envoi",)

# ── CE QUE LA CARTE REPOND, ET OU C'EST ECRIT ─────────────────────────────
# 🔴 LA PAGE ANCRE DES PHRASES QUE LE **FIRMWARE** IMPRIME. Si l'une disparait
#    du firmware, la page attendrait une reponse qui n'arrive plus — et rien ne
#    le dirait. ⇒ chacune est RELUE ICI, dans le fichier qui la produit.
# ⚠️ `Command returned non-zero error code` vient du REPL d'ESP-IDF, ⛔ pas de
#    ce depot : elle est mesuree dans `mesures/dn4-18/reference-flux.bin` et
#    ⛔ elle n'est donc PAS cherchee dans `firmware/`.
# 🔴 L'APPARIEMENT EST **BIUNIVOQUE**, ET C'EST LE CORRECTIF D'UNE MESURE : des
#    cinq litteraux relus dans `firmware/`, la version d'avant n'en appariait
#    reellement que DEUX, et le jeton que la page matchait pour le refus
#    (`REFUS`) n'etait relu par RIEN. Un litteral relu que personne n'apparie ne
#    garde rien ; un motif de la page que rien ne relit pourrit en silence.
# ⇒ CHAQUE LIGNE PORTE LES QUATRE MEMBRES DE LA CHAINE :
#      (nom) · le fichier du firmware · le LITTERAL qui doit y rester ·
#      un TEMOIN de la ligne que la carte IMPRIME.
#   Et la gate verifie les trois maillons, ⛔ pas un seul :
#      (1) le litteral est ENCORE dans le firmware ;
#      (2) le temoin CONTIENT ce litteral (`%s` rendu) — ⛔ il n'est donc pas
#          libre d'etre ecrit a cote de la plaque ;
#      (3) le MOTIF DE LA PAGE, lu dans la page, MATCHE ce temoin.
# 🔴 ET LA RELECTURE EST **BORNEE AU CORPS DE `cmd_langue`**, ⛔ pas au fichier :
#    deux de ces phrases ne lui sont PAS propres — `ECRITURE NVS REFUSEE` est un
#    prefixe que d'AUTRES reglages impriment sur le MEME flux. Relire au fichier
#    laisserait la gate verte le jour ou `cmd_langue` cesse d'imprimer la sienne,
#    parce qu'une autre commande l'imprime encore. ⇒ `None` = tout le fichier
#    (l'invite est une configuration du REPL, ⛔ pas une ligne de `cmd_langue`).
FONCTION_LANGUE = "cmd_langue"
APPARIEMENT = (
    ("invite", CONSOLE_C, None, "desknode>",
     "\ndesknode> "),
    ("lecture", CONSOLE_C, FONCTION_LANGUE, "langue de l'ecran : %s",
     "langue de l'ecran : FR   (⛔ defaut = EN)"),
    ("refus", CONSOLE_C, FONCTION_LANGUE, "n'est pas une langue connue.",
     "🔴 REFUS : « xx » n'est pas une langue connue."),
    ("no-op", CONSOLE_C, FONCTION_LANGUE, "rien a faire : la langue est DEJA",
     "rien a faire : la langue est DEJA FR."),
    ("succes", CONSOLE_C, FONCTION_LANGUE, "(scene reconstruite)",
     "langue : FR   (scene reconstruite)"),
    ("nvs", CONSOLE_C, FONCTION_LANGUE, "— la langue est posee A CHAUD",
     "⚠️ ECRITURE NVS REFUSEE (ESP_ERR_NVS_NO_FREE_PAGES) — la langue est "
     "posee A CHAUD mais ⛔ elle NE survivra PAS au reboot."),
)
# Le NOM que la page donne a chaque motif. ⛔ La reciproque est controlee : tout
# `var RE_…` declare dans le script doit etre ICI, et inversement.
NOMS_MOTIFS_PAGE = {
    "invite": "RE_INVITE_CARTE",
    "lecture": "RE_LECTURE_CARTE",
    "refus": "RE_REFUS_CARTE",
    "no-op": "RE_NOOP_CARTE",
    "succes": "RE_SUCCES_CARTE",
    "nvs": "RE_NVS_REFUSEE",
}
RE_DECL_MOTIF = re.compile(r"var (RE_[A-Z_]+) = /(.*?)/;")
# 🔴 CE QUE LA CARTE DIT **SANS RAPPORT** AVEC LA LANGUE, ET QUI PORTE `REFUS`.
#    Ces lignes sont REELLES, elles sortent sur la MEME console, et le geste se
#    joue dans la fenetre de demarrage a froid ou ces erreurs se produisent
#    VRAIMENT. ⇒ un motif de classement qui les matche classerait un journal
#    etranger comme un refus de langue. Elles sont RELUES dans `firmware/`,
#    ⛔ pas inventees ici.
# 🔴 ET LE TROISIEME EST CELUI QUI MORD VRAIMENT : `ECRITURE NVS REFUSEE` est un
#    prefixe **PARTAGE** que d'AUTRES commandes de la MEME console impriment. Les
#    deux premiers temoins ne pouvaient etre matches par AUCUN motif de
#    classement — le controle passait donc **A VIDE**. Celui-ci, lui, est
#    exactement ce qu'un motif ancre sur le prefixe classerait « langue non
#    persistee » alors que la langue n'a rien a voir avec lui.
TEMOINS_ETRANGERS = (
    (CAPTEURS_C, "ouverture REFUSEE : le bus I2C n'existe pas",
     "E (2317) dn_capteurs: ouverture REFUSEE : le bus I2C n'existe pas "
     "(aucun peripherique)\n"),
    (RTC_C, "pose REFUSEE",
     "E (1180) dn_rtc: relecture : secondes non BCD (0x00) — pose REFUSEE\n"),
    (CONSOLE_C, "ECRITURE NVS REFUSEE (%s) : le reglage s'applique A CHAUD",
     "⚠️ ECRITURE NVS REFUSEE (ESP_ERR_NVS_NO_FREE_PAGES) : le reglage "
     "s'applique A CHAUD\n   mais NE SURVIVRA PAS au reboot.\n"),
)
# Les motifs qui CLASSENT une reponse — ⛔ pas ceux qui bornent une fenetre.
# `RE_INVITE_CARTE` delimite ; les autres decident, et ⛔ aucun d'eux n'a le
# droit de matcher un journal etranger.
MOTIFS_QUI_CLASSENT = ("refus", "nvs", "no-op", "succes", "lecture")
# ⛔ UNE ADRESSE `fichier:ligne` SE PERIME AU PREMIER COMMIT. La gate en cite,
#    parce qu'elle RELIT ; la page, elle, ⛔ n'en cite aucune.
RE_ADRESSE_FIRMWARE = re.compile(r"\bdn_\w+\.[ch]:\d+")

LARGEUR_LIBELLE = 58

ok_total = [0]
ko_total = [0]
ids_emis = []

MUTANTS = {}                      # ⛔ AU NIVEAU MODULE — sinon `--liste-mutants`
CIBLES = {}                       # ⛔ AU NIVEAU MODULE — matiere de (c18)

MUTANTS[1] = ("efface la seconde position du choix ⇒ un « choix » "
              "a une seule entree, qui ne choisit rien")
CIBLES[1] = ("c1",)
MUTANTS[2] = ("deplace le choix APRES le bouton de flash ⇒ on le "
              "decouvre quand la carte est deja ecrite")
CIBLES[2] = ("c2",)
MUTANTS[3] = ("relache l'anglais dans le document ⇒ le defaut cesse "
              "d'etre ECRIT, et plus rien ne le porte")
CIBLES[3] = ("c3",)
MUTANTS[4] = ("fait POSER le defaut par un script au chargement ⇒ il "
              "n'est plus structurel, il est promis")
CIBLES[4] = ("c3",)
MUTANTS[5] = ("branche le choix de la DALLE sur la bascule de la PAGE "
              "⇒ les deux langues se melangent")
CIBLES[5] = ("c4",)
MUTANTS[6] = ("retire d'UNE SEULE langue la mention « c'est la dalle » "
              "⇒ ce lecteur-la croit revoir le meme choix")
CIBLES[6] = ("c5",)
MUTANTS[7] = ("replie le geste de pose derriere un depliant ⇒ il faut "
              "DEROULER pour poser la langue")
CIBLES[7] = ("c6",)
MUTANTS[8] = ("envoie un code que le binaire NE PORTE PAS ⇒ la carte "
              "refuse, et c'est la marche qui l'a fabrique")
CIBLES[8] = ("c7",)
MUTANTS[9] = ("efface la garde du defaut anglais ⇒ « anglais » est "
              "ECRIT en NVS au lieu de n'etre rien")
CIBLES[9] = ("c8",)
MUTANTS[10] = ("deplace la garde APRES le reveil ⇒ des octets partent "
               "sur le port pour un choix qui n'ecrit rien")
CIBLES[10] = ("c8",)
MUTANTS[11] = ("ne relache plus le verrou d'ecriture sur le chemin "
               "d'ECHEC ⇒ la fermeture du port part en rejet")
CIBLES[11] = ("c9",)
MUTANTS[12] = ("envoie l'ordre AVANT d'attendre l'invite ⇒ la ligne se "
               "perd, et le succes serait annonce sur du vide")
CIBLES[12] = ("c10",)
MUTANTS[13] = ("fond « pas d'invite » dans « sans reponse » ⇒ une carte "
               "muette et une carte absente disent la meme chose")
CIBLES[13] = ("c11",)
MUTANTS[14] = ("ECHANGE deux issues entre leurs branches ⇒ « sans "
               "reponse » sur une carte qui n'a jamais rendu l'invite")
CIBLES[14] = ("c12",)
MUTANTS[15] = ("relit L'ORDRE ENVOYE au lieu de l'ETAT ⇒ le succes se "
               "prouve par ce qu'on a tape")
CIBLES[15] = ("c13",)
MUTANTS[16] = ("prend un SECOND lecteur pour l'attente ⇒ `readable` "
               "n'en admet qu'un, et le journal se casse")
CIBLES[16] = ("c14",)
MUTANTS[17] = ("retire la garde de re-entrance ⇒ deux clics envoient "
               "deux ordres et se volent leurs lignes")
CIBLES[17] = ("c15",)
MUTANTS[18] = ("retire du firmware une reponse que la page ATTEND ⇒ la "
               "page guette une phrase que la carte ne dit plus")
CIBLES[18] = ("c16",)
MUTANTS[19] = ("plante dans la page un numero de ligne du firmware ⇒ "
               "une adresse qui se perime au premier commit")
CIBLES[19] = ("c17",)
MUTANTS[20] = ("replante une SORTIE ANTICIPEE NON DECLAREE : le bilan "
               "retrecit, et il sortirait VERT")
CIBLES[20] = ("z",)
MUTANTS[21] = ("declare un mutant dont le CORPS LEVE ⇒ un mutant MORT, "
               "qui sortirait en Traceback SANS `BILAN`")
CIBLES[21] = ("c0",)
MUTANTS[22] = ("retire une cible de `CIBLES` ⇒ un controle garde par "
               "ZERO mutant, le risque deja paye ailleurs")
CIBLES[22] = ("c18",)
MUTANTS[23] = ("declare dans `CIBLES` un controle INEXISTANT ⇒ une "
               "cible PERIMEE, que « N mutants, N rouges » ne voit pas")
CIBLES[23] = ("c19",)
MUTANTS[24] = ("declare une cible pour un mutant qui N'EXISTE PAS")
CIBLES[24] = ("c20",)
MUTANTS[25] = ("fait reconnaitre la 5e issue par le litteral du REFUS "
               "⇒ elle n'a plus de litteral a elle")
CIBLES[25] = ("c12", "c21")
MUTANTS[26] = ("rend le motif de refus TRAVERSANT ⇒ un journal du bus "
               "I2C serait classe « refus de langue »")
CIBLES[26] = ("c22",)
MUTANTS[27] = ("tait ce qu'il advient du port sur une issue ⇒ un port "
               "tenu EN SILENCE, et l'agent ne repart pas")
CIBLES[27] = ("c23",)
MUTANTS[28] = ("arme le geste dans le document ⇒ il s'offre avant que "
               "le flash soit seulement possible")
CIBLES[28] = ("c24",)
MUTANTS[29] = ("masque le bloc de flash SANS desarmer le geste ⇒ poser "
               "une langue pour un flash qui n'aura pas lieu")
CIBLES[29] = ("c24",)
MUTANTS[30] = ("jette les octets lus quand l'invite ne vient pas ⇒ un "
               "diagnostic sans piece")
CIBLES[30] = ("c25",)
MUTANTS[31] = ("jette ce qui suit l'invite ⇒ la reponse suivante part "
               "tronquee, et une ligne de langue se perd")
CIBLES[31] = ("c26",)
MUTANTS[32] = ("met le delai d'invite a ZERO ⇒ l'attente n'attend "
               "rien, et l'ordre part sur une carte muette")
CIBLES[32] = ("c10",)
MUTANTS[33] = ("retire du CORPS DE `cmd_langue` la ligne NVS ⇒ le "
               "prefixe reste au fichier, imprime par d'autres")
CIBLES[33] = ("c16",)
MUTANTS[34] = ("re-ancre la 5e issue sur le PREFIXE PARTAGE ⇒ un "
               "reglage voisin serait classe « langue non gardee »")
CIBLES[34] = ("c22",)

# ⚠️ LE COMPTE DU CHEMIN NORMAL : 1 pre-vol + un controle par mutant + les 26
#    controles numerotes. Il se PERIME si on ajoute un controle sans le mettre
#    a jour — et c'est voulu : c'est ce qui rend (z) FALSIFIABLE.
CONTROLES_PREVUS = 61

_MUTANT = 0

RE_ID_CTRL = re.compile(r"\((\w+)\)")


def ctrl(ok, libelle, detail=""):
    """UNE assertion, UNE ligne, UN identifiant. ⛔ Aucun controle muet.

    ⚠️ L'IDENTIFIANT VIT DANS LE LIBELLE, ⛔ pas dans un argument a part : la
       campagne de mutants lit les libelles A L'AST en prenant le second
       argument de chaque appel, et A COLONNE FIXE."""
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
    """La portion entre deux balises, ⛔ pas le fichier entier.

    🔴 LA FENETRE EST L'ELEMENT, ⛔ PAS UN VOISINAGE — et la garde d'origine
       cherchait le fermant dans le texte ENTIER : un fermant place AVANT
       l'ouvrant la passait, et la fenetre rendait TOUT CE QUI SUIT l'ouvrant.
       ⛔ C'est le meme defaut que `bloc_section` a paye, et la tache 7 dit
       « **tout** extracteur de fenetre ». ⇒ le fermant est cherche **APRES**
       l'ouvrant, et son absence rend **VIDE**."""
    if not txt or ouvrant not in txt:
        return ""
    apres = txt.split(ouvrant, 1)[1]
    if fermant not in apres:
        return ""
    return apres.split(fermant, 1)[0]


def sans_commentaires(js):
    """Le script SANS ses commentaires — ⛔ ce qui s'execute, pas ce qui
    l'explique. Une gate qui compte la prose des commentaires rougirait sur la
    documentation de sa propre regle."""
    js = re.sub(r"/\*.*?\*/", " ", js or "", flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", " ", js)


def porte_le_litteral(temoin, litteral):
    """Le temoin porte-t-il le litteral du firmware, `%s` rendu ?

    ⚠️ LES FRAGMENTS SE CONSOMMENT **DANS L'ORDRE** : un `%s` est un trou, ⛔ pas
       une permission de melanger. Sans ca, un temoin ecrit a l'envers passerait,
       et les deux controles qui s'appuient dessus deviendraient vacuement vrais."""
    i = 0
    for morceau in (litteral or "").split("%s"):
        if not morceau:
            continue
        j = temoin.find(morceau, i)
        if j < 0:
            return False
        i = j + len(morceau)
    return True


def corps_c(txt, nom):
    """Le CORPS d'une fonction C, ⛔ pas le fichier entier.

    🔴 MEME REGLE QUE LES DEUX AUTRES EXTRACTEURS : une fenetre qui ne se
       referme pas rend **VIDE**, ⛔ jamais « tout ce qui suit »."""
    m = re.search(r"^static\s+int\s+%s\s*\([^)]*\)\s*\n\{\n" % re.escape(nom),
                  txt or "", re.M)
    if not m:
        return ""
    apres = txt[m.end():]
    f = apres.find("\n}\n")
    return apres[:f] if f >= 0 else ""


def corps_fonction(js, nom):
    """Le CORPS d'une fonction du script, ⛔ pas le script entier.

    🔴 UN CONTROLE DE RANG QUI BALAIE TOUT LE SCRIPT MESURE L'ORDRE DES
       DECLARATIONS, ⛔ pas celui des branches. Les constantes de delai vivent
       en tete du fichier : les chercher globalement ferait passer VERT un
       envoi place avant l'attente."""
    m = re.search(RE_FONCTION % re.escape(nom), js or "", re.S)
    return m.group(1) if m else ""


class Replis(HTMLParser):
    """A quelle profondeur de `<details>` chaque GESTE se trouve-t-il ?

    ⚠️ CONDITION NECESSAIRE, ⛔ PAS SUFFISANTE : qu'aucun bouton ne soit replie
       ⛔ ne dit PAS que la page est lisible — cela dit seulement qu'aucun
       geste n'exige de DEROULER quelque chose."""

    VIDES = ("br", "hr", "img", "meta", "input", "link", "source", "track")

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.prof = 0
        self.replies = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "details":
            self.prof += 1
        elif self.prof and tag == "button" and d.get("id"):
            self.replies.append(d.get("id"))

    def handle_endtag(self, tag):
        if tag == "details" and self.prof:
            self.prof -= 1


def gestes_replies(page):
    """Les boutons qui vivent SOUS un depliant."""
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


def bloc_section(page, ident):
    """Le contenu du `<div id="…">` demande, ⛔ pas un rayon de caracteres.

    🔴 LA FENETRE EST L'ELEMENT, ⛔ PAS UN VOISINAGE : un rayon plat laisserait
       la prose d'a cote satisfaire le controle."""
    ouvrant = '<div id="%s">' % ident
    if not page or ouvrant not in page:
        return ""
    apres = page.split(ouvrant, 1)[1]
    prof = 1
    for m in re.finditer(r"<(/?)div\b", apres):
        prof += -1 if m.group(1) else 1
        if prof == 0:
            return apres[:m.start()]
    # 🔴 LA FENETRE NE SE REFERME PAS ⇒ ELLE EST **VIDE**, ⛔ JAMAIS « tout ce
    #    qui suit ». MESURE : le repli d'origine rendait la fin du fichier, donc
    #    la prose d'AILLEURS pouvait satisfaire les controles qui lisent cette
    #    fenetre — et le libelle de la fonction disait deja l'inverse
    #    (« LA FENETRE EST L'ELEMENT, ⛔ PAS UN VOISINAGE »).
    return ""


def elements_de_langue(fragment):
    """Les blocs `[lang="en"]` / `[lang="fr"]` d'un fragment, avec leur
    contenu. Rend `[(langue, contenu), …]`."""
    return [(m.group(2), m.group(3)) for m in re.finditer(
        r'<(\w+)[^>]*\blang="(en|fr)"[^>]*>(.*?)</\1>', fragment or "", re.S)]


# ═══════════ LES PREDICATS — DES FONCTIONS DU PRODUIT ══════════════════════
# 🔴 CHAQUE CONTROLE APPELLE UNE FONCTION NOMMEE, ET LE TEMOIN NEGATIF IMPORTE
#    CE MODULE POUR APPELER **LES MEMES**. Une garde reecrite dans le temoin ne
#    prouverait que le temoin.

def choix_a_deux_positions(page):
    """Le choix de la dalle existe-t-il, et porte-t-il DEUX entrees ?"""
    bloc = bloc_section(page, SECTION_DALLE)
    vus = [b for b in (BOUTON_DALLE_EN, BOUTON_DALLE_FR)
           if ('id="%s"' % b) in bloc]
    return len(vus) == 2, vus


def choix_precede_le_flash(page):
    """Le choix est-il OFFERT AVANT que la carte soit ecrite ?"""
    a = '<div id="%s">' % SECTION_DALLE
    if not page or a not in page or ELEMENT_FLASH not in page:
        return False, "%s%s" % (
            "" if a in (page or "") else "le choix est absent de la page ",
            "" if ELEMENT_FLASH in (page or "")
            else "l'element de flash est absent de la page")
    if page.index(a) < page.index(ELEMENT_FLASH):
        return True, "le choix est offert AVANT le bouton qui ecrit"
    return False, "le choix vient APRES le bouton qui ecrit"


def defaut_anglais_dans_le_document(page, js):
    """Le defaut est-il ECRIT dans le document, ⛔ pas pose par un script ?

    🔴 IL SE PROUVE DANS LE FICHIER : un attribut pose par un script qui n'a
       pas tourne ne porte RIEN, exactement comme une NVS jamais ecrite ne
       porte pas « anglais » — elle ne porte rien, et c'est le defaut."""
    ecrit = (RE_DALLE_EN_PRESSE.search(page or "") is not None
             and RE_DALLE_FR_RELACHE.search(page or "") is not None)
    poses = []
    for m in RE_POSER_DALLE_APPEL.finditer(js or ""):
        amont = js[max(0, m.start() - 90):m.start()]
        if not RE_CLIC.search(amont):
            poses.append(js[m.start():m.start() + 24])
    return ecrit and not poses, (ecrit, poses)


def deux_choix_restent_distincts(page, js):
    """Le choix de la DALLE et celui de la PAGE sont-ils DEUX mecanismes ?"""
    ids = (SECTION_DALLE, SECTION_PAGE, BOUTON_DALLE_EN, BOUTON_DALLE_FR,
           BOUTON_PAGE_EN, BOUTON_PAGE_FR)
    absents = [i for i in ids if ('id="%s"' % i) not in (page or "")]
    # ⛔ LE GESTE DE LA DALLE NE TOUCHE PAS A LA LANGUE DE LA PAGE : un
    #    `poserLangue(` dans ce chemin ferait basculer la prose sous les yeux
    #    du lecteur au moment ou il choisit AUTRE CHOSE.
    fuites = []
    for m in re.finditer(r'(\w+)\.addEventListener\(\s*"click"[\s\S]{0,120}?'
                         r"(poserLangue|poserDalle)\(", js or ""):
        if m.group(1) in ("bDalleEn", "bDalleFr") and m.group(2) != "poserDalle":
            fuites.append(m.group(1))
    corps = corps_fonction(js, NOM_POSE)
    if re.search(r"\bposerLangue\(", corps):
        fuites.append(NOM_POSE)
    return not absents and not fuites, (absents, fuites)


def la_page_dit_que_c_est_la_dalle(page):
    """La distinction est-elle ECRITE, dans les DEUX langues ?"""
    bloc = bloc_section(page, SECTION_DALLE)
    vues = {}
    for langue, contenu in elements_de_langue(bloc):
        pl = plat(contenu)
        if MENTION_DALLE[langue] in pl and MENTION_PAS_LA_PAGE[langue] in pl:
            vues[langue] = True
    absentes = [l for l in ("en", "fr") if not vues.get(l)]
    return not absentes, absentes


def le_geste_est_atteignable(page):
    """Le geste de pose a-t-il SON bouton, et ⛔ hors de tout depliant ?"""
    present = ('id="%s"' % BOUTON_POSER) in (page or "")
    replies = [b for b in gestes_replies(page)
               if b in (BOUTON_POSER, BOUTON_DALLE_EN, BOUTON_DALLE_FR)]
    return present and not replies, (present, replies)


def ordre_forme_de_la_table(js, langue_c):
    """L'ordre envoye est-il `langue` + un code que le BINAIRE porte ?"""
    m = RE_CMD_DECLAREE.search(js or "")
    cmd = m.group(1) if m else None
    c = RE_CODES_DECLARES.search(js or "")
    codes = tuple(sorted(x.strip().strip('"').lower()
                         for x in c.group(1).split(",") if x.strip())) if c else ()
    firmware = tuple(sorted(v.lower() for _, v
                            in RE_CODE_FIRMWARE.findall(langue_c or "")))
    envoi = RE_ENVOI_ORDRE.search(js or "") is not None
    ok = (cmd == CMD_ATTENDUE and envoi and bool(firmware)
          and codes == firmware)
    return ok, (cmd, codes, firmware, envoi)


def rien_n_est_ecrit_pour_l_anglais(js):
    """La garde du defaut anglais existe-t-elle, et PRECEDE-T-ELLE l'ecriture ?

    🔴 LE DEFAUT SE PROUVE PAR L'ABSENCE D'ECRITURE. Une garde posee APRES le
       premier octet ecrit n'est plus une garde : c'est un commentaire."""
    corps = corps_fonction(js, NOM_POSE)
    if GARDE_DEFAUT not in corps:
        return False, "la garde du defaut anglais est ABSENTE"
    if ('"%s"' % CLE_DEFAUT) not in corps:
        return False, "la garde n'annonce rien : le lecteur ne saura pas "\
                      "pourquoi rien ne s'est passe"
    i = corps.index(GARDE_DEFAUT)
    e = corps.find("consoleEcrire(")
    if e < 0:
        return False, "aucune ecriture sur le port : le geste n'envoie rien"
    if i < e:
        return True, "la garde precede la 1re ecriture (%d < %d)" % (i, e)
    return False, "la garde vient APRES la 1re ecriture (%d > %d)" % (i, e)


def le_verrou_est_rendu_deux_fois(js):
    """Le verrou d'ecriture est-il relache SUR LES DEUX CHEMINS ?"""
    corps = corps_fonction(js, NOM_ECRIRE)
    if not corps:
        return False, (0, 0)
    pris = len(RE_GET_WRITER.findall(corps))
    rendus = len(RE_RELACHE.findall(corps))
    return pris == 1 and rendus >= 2, (pris, rendus)


def l_invite_precede_l_envoi(js):
    """L'invite est-elle ATTENDUE avant que l'ordre parte, et l'attente a-t-elle
    une DUREE qui attend vraiment ?"""
    valeurs = {n: int(v) for n, v in RE_DELAI.findall(js or "")}
    if len(valeurs) != 2:
        return False, ("les deux delais ne sont pas declares en clair : %s"
                       % (sorted(valeurs) or "aucun"))
    trop_court = sorted(n for n in valeurs if valeurs[n] < PLANCHER_DELAI)
    if trop_court:
        return False, ("%s vaut %d ms, sous le plancher de %d — une attente qui "
                       "n'attend pas est un no-op"
                       % (trop_court[0], valeurs[trop_court[0]], PLANCHER_DELAI))
    corps = corps_fonction(js, NOM_POSE)
    a = corps.find(ANCRE_ATTENTE_INVITE)
    m = RE_ENVOI_ORDRE.search(corps)
    if a < 0 or m is None:
        return False, ("l'attente de l'invite est absente" if a < 0
                       else "l'ordre n'est envoye nulle part")
    if a < m.start():
        return True, ("le reveil precede l'ordre, et les deux delais sont >= %d ms"
                      % PLANCHER_DELAI)
    return False, "l'ordre part AVANT que l'invite soit revenue"


def quatre_issues_distinctes(js):
    """Les quatre issues sont-elles NOMMEES SEPAREMENT, et annoncees ?"""
    absentes = [c for c in CLES_ISSUES
                if not re.search(RE_ANNONCE % re.escape(c), js or "")]
    table = region(js or "", "var MOTS = {", "\n};")
    sans_mot = [c for c in CLES_ISSUES if ('"%s"' % c) not in table]
    return not absentes and not sans_mot, (absentes, sans_mot)


def chaque_issue_dans_sa_branche(js):
    """Chaque issue est-elle ANCREE dans SA branche, et A SON RANG ?"""
    corps = corps_fonction(js, NOM_POSE)
    manquants, deplacees, rangs = [], [], []
    for cle, ancre in ANCRES_ISSUES:
        ic = corps.find('"%s"' % cle)
        ia = corps.find(ancre)
        if ic < 0 or ia < 0:
            manquants.append(cle)
            continue
        if ia > ic:
            deplacees.append("%s ⛔ avant son marqueur" % cle)
        rangs.append((ic, cle))
    ordre = [c for _, c in sorted(rangs)]
    attendu = [c for c, _ in ANCRES_ISSUES if c in ordre]
    if ordre != attendu:
        deplacees.append("rang ECHANGE : %s au lieu de %s"
                         % (" < ".join(ordre), " < ".join(attendu)))
    return not manquants and not deplacees, (manquants, deplacees)


def le_succes_vient_de_la_relecture(js):
    """« Posee » n'est-il atteignable QUE depuis la relecture ?

    🔴 ON RELIT L'ACCEPTATION, PUIS L'ETAT — ⛔ JAMAIS L'ORDRE ENVOYE. Un
       succes prouve par ce qu'on a tape est un succes annonce sur du vide."""
    corps = corps_fonction(js, NOM_POSE)
    m = RE_RELECTURE.search(corps)
    annonces = [x.start() for x in
                re.finditer(RE_ANNONCE % re.escape("langue.posee"), corps)]
    if m is None:
        return False, "aucune relecture : `langue` sans argument n'est jamais "\
                      "envoye"
    if not annonces:
        return False, "le succes n'est annonce nulle part"
    if len(annonces) > 1:
        return False, "%d annonces de succes : au moins une hors relecture" \
                      % len(annonces)
    if annonces[0] > m.start():
        return True, "1 annonce, APRES la relecture de l'etat"
    return False, "le succes est annonce AVANT la relecture"


def un_seul_lecteur(js):
    """L'attente passe-t-elle par l'entonnoir, ⛔ pas par un second lecteur ?"""
    lecteurs = len(RE_GET_READER.findall(js or ""))
    branchee = RE_NOURRIR_DEPUIS_AJOUT.search(js or "") is not None
    return lecteurs == 1 and branchee, (lecteurs, branchee)


def le_geste_garde_sa_re_entrance(js):
    """Un second clic pendant le vol est-il IGNORE ?"""
    corps = corps_fonction(js, NOM_POSE)
    return (GARDE_REENTRANCE in corps and "langueEnVol = true" in corps), corps


def motifs_declares_par_la_page(js):
    """Les motifs `var RE_… = /…/;` du script, par NOM. Rend `{nom: source}`."""
    return {m.group(1): m.group(2) for m in RE_DECL_MOTIF.finditer(js or "")}


def l_appariement_est_biunivoque(fichiers, js):
    """Chaque litteral relu au firmware est-il APPARIE par un motif de la page,
    et chaque motif de la page est-il RELU au firmware ?

    🔴 LES TROIS MAILLONS SONT VERIFIES, ⛔ PAS UN SEUL. Un litteral relu que
       personne n'apparie ne garde rien ; un motif que rien ne relit pourrit en
       silence ; et un temoin ecrit a cote de la plaque rendrait les deux
       vacuement vrais."""
    declares = motifs_declares_par_la_page(js)
    attendus = set(NOMS_MOTIFS_PAGE.values())
    orphelins = sorted(set(declares) - attendus)      # la page en declare un de trop
    absents = sorted(attendus - set(declares))        # la page n'en declare pas assez
    perdus, muets, boiteux = [], [], []
    for nom, fichier, portee, litteral, temoin in APPARIEMENT:
        # ⛔ BORNE A LA FONCTION QUAND ELLE EST DECLAREE : un prefixe partage
        #    reste dans le fichier alors que la commande a cesse de l'imprimer.
        ou = (corps_c(fichiers.get(fichier), portee) if portee
              else (fichiers.get(fichier) or ""))
        if litteral not in ou:
            perdus.append(nom)
            continue
        if not porte_le_litteral(temoin, litteral):
            boiteux.append(nom)
            continue
        src = declares.get(NOMS_MOTIFS_PAGE[nom])
        if src is None:
            continue                                  # deja compte dans `absents`
        try:
            if re.search(src, temoin) is None:
                muets.append(nom)
        except re.error:
            muets.append(nom)
    return (not orphelins and not absents and not perdus and not muets
            and not boiteux), (orphelins, absents, perdus, muets, boiteux)


def le_classement_est_ancre(fichiers, js):
    """Un journal ETRANGER portant `REFUS` peut-il etre classe comme un refus ?

    🔴 LA CONSOLE DE LA CARTE EST BAVARDE ET ASYNCHRONE, et le geste se joue
       dans la fenetre de demarrage a froid ou le bus I2C fait de VRAIES
       erreurs. Un motif de classement qui traverse tout le flux classerait un
       journal sans rapport comme un refus de langue.
    ⚠️ LES TEMOINS SONT RELUS DANS `firmware/`, ⛔ pas inventes ici : un temoin
       que le firmware n'imprime plus ne prouverait rien."""
    declares = motifs_declares_par_la_page(js)
    # ⛔ ECHEC FERME : une page qui ne declare AUCUN motif de classement n'est
    #    pas « ancree », elle est MUETTE. Rendre vrai sur une population VIDE
    #    ferait passer pour gardee une page ou rien ne classe quoi que ce soit.
    if not [n for n in MOTIFS_QUI_CLASSENT if declares.get(NOMS_MOTIFS_PAGE[n])]:
        return False, ([], [], ["⛔ la page ne declare AUCUN motif de classement"])
    disparus = [f for f, litteral, _ in TEMOINS_ETRANGERS
                if litteral not in (fichiers.get(f) or "")]
    boiteux = [f for f, litteral, temoin in TEMOINS_ETRANGERS
               if not porte_le_litteral(temoin, litteral)]
    mordus = []
    for nom in MOTIFS_QUI_CLASSENT:
        src = declares.get(NOMS_MOTIFS_PAGE[nom])
        if not src:
            continue
        for _, _, temoin in TEMOINS_ETRANGERS:
            try:
                if re.search(src, temoin) is not None:
                    mordus.append("%s ⇒ %s" % (nom, temoin.strip()[:48]))
            except re.error:
                mordus.append("%s (motif illisible)" % nom)
    return (not disparus and not boiteux and not mordus,
            (disparus, boiteux, mordus))


def la_cinquieme_issue_a_sa_cle(js):
    """« Posee A CHAUD mais ⛔ NON PERSISTEE » a-t-elle SA cle, SON litteral, et
    est-elle examinee AVANT le succes ?

    🔴 LA CARTE IMPRIME SON AVERTISSEMENT, **PUIS** LA LIGNE DE SUCCES, et rend
       un code non nul. Tester le succes d'abord classerait « pose » ce qui ne
       survivra pas ; retomber sur « refusee » dirait que la dalle n'a pas
       change, ce qui est faux."""
    corps = corps_fonction(js, NOM_POSE)
    if not re.search(RE_ANNONCE % re.escape(CLE_NON_PERSISTEE), corps):
        return False, "la 5e issue n'est annoncee nulle part"
    table = region(js or "", "var MOTS = {", "\n};")
    if ('"%s"' % CLE_NON_PERSISTEE) not in table:
        return False, "la 5e issue n'a aucun texte dans `MOTS`"
    i = corps.find("RE_NVS_REFUSEE.test(")
    if i < 0:
        return False, "elle n'est reconnue par AUCUN litteral qui lui soit propre"
    for autre in ("RE_SUCCES_CARTE.test(", "RE_REFUS_CARTE.test(",
                  "RE_NOOP_CARTE.test("):
        j = corps.find(autre)
        if 0 <= j < i:
            return False, "`%s` est examine AVANT elle" % autre.rstrip("(.test")
    ic = corps.find('"%s"' % CLE_NON_PERSISTEE)
    for cle in ("langue.refusee", "langue.posee"):
        k = corps.find('"%s"' % cle)
        if 0 <= k < ic:
            return False, "elle retombe sur `%s`, annoncee avant elle" % cle
    return True, "cle propre, litteral propre, examinee avant le succes"


def chaque_issue_dit_le_port(js):
    """Chaque annonce du geste dit-elle ce qu'il advient du PORT ?

    ⛔ Un port tenu EN SILENCE est ce que `dn7-2` a nomme comme empechant
       l'agent de repartir : le verbe `stop` prouve son travail EN ROUVRANT le
       port, et il echouerait sur un port que cette page tient elle-meme."""
    corps = corps_fonction(js, NOM_POSE)
    muettes = []
    for m in re.finditer(r'blocMot\(\s*"etat-langue"\s*,\s*"([^"]+)"[^;]*;', corps):
        if m.group(1) in ANNONCES_SANS_PORT:
            continue
        suite = corps[m.end():m.end() + 120]
        # ⛔ ET LA CLE PASSEE EST **CELLE QU'ON VIENT D'ANNONCER** : c'est elle
        #    qui decide du cadre, et un cadre faux fait lire un succes comme un
        #    refus. Un appel « quelque part » ne dit rien.
        if ('%s"%s"' % (APPEL_PORT, m.group(1))) not in suite:
            muettes.append(m.group(1))
    table = region(js or "", "var MOTS = {", "\n};")
    sans_mot = [c for c in CLES_PORT if ('"%s"' % c) not in table]
    return not muettes and not sans_mot, (muettes, sans_mot)


def le_geste_suit_le_bloc_de_flash(page, js):
    """Le geste ⛔ ne s'offre PAS quand le bloc de flash est masque ?

    🔴 PROPOSER DE POSER UNE LANGUE POUR UN FLASH QUI NE PEUT PAS AVOIR LIEU
       est une promesse que la page SAIT fausse. ⇒ le bouton porte `disabled`
       DANS LE DOCUMENT, et les TROIS fonctions qui decident de la visibilite du
       bloc d'installation appellent toutes `langueOffrir()`."""
    desarme = re.search(
        r'<button id="' + BOUTON_POSER + r'"[^>]*\bdisabled\b', page or "") is not None
    sourdes = [n for n in ("reveler", "chargeInutilisable", "moduleAbsent")
               if "langueOffrir(" not in corps_fonction(js, n)]
    lit = "blocInstaller.hidden" in corps_fonction(js, "langueOffrir")
    return desarme and not sourdes and lit, (desarme, sourdes, lit)


def les_octets_lus_sont_relayes(js):
    """Quand l'invite ne vient pas, les octets REELLEMENT lus sont-ils rendus ?

    🔴 C'EST LE SEUL CAS OU LE TEXTE BRUT NOMME LE VRAI OBSTACLE — boucle de
       demarrage, mode `download`, invite changee. Les jeter laisserait le
       lecteur devant un diagnostic sans piece."""
    corps = corps_fonction(js, NOM_POSE)
    i = corps.find('"langue.pas-d-invite"')
    if i < 0:
        return False, "l'issue « pas d'invite » n'est annoncee nulle part"
    amont = corps[max(0, i - 400):i]
    if "langueRelais(r.texte)" not in amont:
        return False, "les octets lus sont JETES au lieu d'etre relayes"
    return True, "les octets lus partent au relais avant l'annonce"


def le_reste_de_lecture_est_repris(js):
    """Ce qui suit l'invite est-il REPRIS par l'attente suivante ?

    🔴 LA CARTE ECRIT EN TRAMES DE TAILLE ARBITRAIRE. Jeter ce qui suit l'invite
       perdrait la premiere moitie de la reponse suivante — une ligne de langue
       manquee, donc un verdict rendu sur un texte TRONQUE."""
    if "reste: a.tampon.slice(i)" not in (js or ""):
        return False, "l'attente ⛔ ne rend PAS ce qui suit son motif"
    corps = corps_fonction(js, NOM_POSE)
    amorces = re.findall(r"langueArmer\([^)]*,\s*(r\d?\.reste|\"\")\s*\)", corps)
    if len(amorces) < 3:
        return False, "%d attente(s) sur 3 recoivent une amorce" % len(amorces)
    if amorces[1:] != ["r.reste", "r2.reste"]:
        return False, "les amorces reprises sont %s" % amorces
    return True, "3 attentes, et les 2 suivantes reprennent le reste"


def les_reponses_sont_encore_au_firmware(fichiers):
    """Les phrases que la page ATTEND sont-elles ENCORE imprimees ?"""
    perdues = []
    for nom, fichier, portee, litteral, _ in APPARIEMENT:
        ou = (corps_c(fichiers.get(fichier), portee) if portee
              else (fichiers.get(fichier) or ""))
        if litteral not in ou:
            perdues.append(nom)
    return not perdues, perdues


def la_page_ne_cite_aucune_ligne(page):
    """La page cite-t-elle une adresse `fichier:ligne` du firmware ?"""
    vues = RE_ADRESSE_FIRMWARE.findall(page or "")
    return not vues, vues


# ═══════════════════════════ LES MUTANTS ═══════════════════════════════════

def muter(etat):
    """REPLANTE une faute DANS L'ETAT — ⛔ jamais dans un fichier du depot.

    🔴 TOUTE mutation passe par cet unique etat, et le corps principal compare
       l'etat AVANT/APRES : la garde du no-op est donc UNIVERSELLE.
    ⚠️ MAIS ELLE N'EST ATTEINTE QUE SI LE CORPS **REND**. Un corps qui `split`,
       indexe ou depaquette sur une ancre disparue LEVE, et le `try` du corps
       principal le rend en `rc=1` + `BILAN` + `[KO ]` — MOT POUR MOT le
       contrat que la campagne appelle « sain » : un mutant PERIME passerait
       pour un gardien vivant. ⇒ tout corps VERIFIE son ancre d'abord et rend
       `e` INCHANGE. ⛔ Le mutant 21 leve EXPRES : il est le temoin de ce cas.
    ⛔ ET CHAQUE MUTANT **REPLANTE LA FAUTE**, ⛔ il ne debranche pas la garde :
       un mutant qui coupe le controle ne prouve que l'existence du controle."""
    e = copy.deepcopy(etat)
    p, r = e["fichiers"], e["regles"]

    if _MUTANT == 1:
        a = '<button id="%s" type="button" aria-pressed="false">' % BOUTON_DALLE_FR
        t = p.get(PAGE, "")
        if a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        j = t.index(a)
        k = t.find("</button>", j)
        p[PAGE] = t[:j] + t[k + len("</button>"):]
    elif _MUTANT == 2:
        t = p.get(PAGE, "")
        a = '<div id="%s">' % SECTION_DALLE
        f = MARQUE_FIN_CHOIX
        if a not in t or f not in t or ELEMENT_FLASH not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        i = t.index(a)
        k = t.index(f) + len(f)
        bloc = t[i:k]
        t = t[:i] + t[k:]
        j = t.index("</esp-web-install-button>") + len("</esp-web-install-button>")
        p[PAGE] = t[:j] + bloc + t[j:]
    elif _MUTANT == 3:
        a = '<button id="%s" type="button" aria-pressed="true">' % BOUTON_DALLE_EN
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '<button id="%s" type="button" aria-pressed="false">'
               % BOUTON_DALLE_EN, 1)
    elif _MUTANT == 4:
        a = 'if (bLanguePoser) {'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, 'poserDalle("en");\n' + a, 1)
    elif _MUTANT == 5:
        a = 'bDalleFr.addEventListener("click", function () { poserDalle("fr"); });'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, 'bDalleFr.addEventListener("click", function () '
               '{ poserLangue("fr"); });', 1)
    elif _MUTANT == 6:
        a = MENTION_PAS_LA_PAGE["fr"]
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "et c'est un choix", 1)
    elif _MUTANT == 7:
        t = p.get(PAGE, "")
        a = '<button id="%s" type="button" disabled>' % BOUTON_POSER
        if a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        i = t.index(a)
        k = t.find("</button>", i) + len("</button>")
        # ⚠️ LE DEPLIANT EST **BILINGUE** : le mutant replante UNE faute — le
        #    repli — ⛔ il n'en traine pas une seconde (un ilot de langue).
        p[PAGE] = (t[:i] + '<details><summary><span lang="en">Language</span>'
                   + '<span lang="fr">Langue</span></summary>' + t[i:k]
                   + "</details>" + t[k:])
    elif _MUTANT == 8:
        a = 'var CODES_DALLE = ["en", "fr"];'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, 'var CODES_DALLE = ["en", "francais"];', 1)
    elif _MUTANT == 9:
        t = p.get(PAGE, "")
        if GARDE_DEFAUT not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        i = t.index(GARDE_DEFAUT)
        k = t.index("  }\n", i) + len("  }\n")
        p[PAGE] = t[:i] + t[k:]
    elif _MUTANT == 10:
        t = p.get(PAGE, "")
        if GARDE_DEFAUT not in t or ANCRE_REVEIL not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        i = t.index(GARDE_DEFAUT)
        k = t.index("  }\n", i) + len("  }\n")
        bloc = t[i:k]
        t = t[:i] + t[k:]
        j = t.index(ANCRE_REVEIL) + len(ANCRE_REVEIL)
        p[PAGE] = t[:j] + "\n    " + bloc.strip() + t[j:]
    elif _MUTANT == 11:
        a = "  }, function (err) {\n    w.releaseLock();\n    throw err;\n  });"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, "  }, function (err) {\n    throw err;\n  });", 1)
    elif _MUTANT == 12:
        a = ("    var invite = " + ANCRE_ATTENTE_INVITE + ";\n    "
             + ANCRE_REVEIL + "\n    return reveil.then(function () "
             "{ return invite; })")
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '    return consoleEcrire(CMD_LANGUE + " " + code)'
               ".then(function () { return "
               + ANCRE_ATTENTE_INVITE + "; })", 1)
    elif _MUTANT == 13:
        a = '"langue.pas-d-invite"'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, '"langue.sans-reponse"')
    elif _MUTANT == 14:
        # 🔴 ON ECHANGE LES **SITES D'APPEL**, ⛔ PAS LES CLES DE LA TABLE : un
        #    echange global emporterait aussi les deux entrees de `MOTS`, les
        #    textes suivraient leurs cles, et le mutant replanterait MOINS
        #    qu'il n'en a l'air. ⛔ Un mutant replante UNE faute, ⛔ pas zero.
        t = p.get(PAGE, "")
        a = 'blocMot("etat-langue", "langue.pas-d-invite")'
        b = 'blocMot("etat-langue", "langue.sans-reponse")'
        if a not in t or b not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(a, "@@X@@").replace(b, a).replace("@@X@@", b)
    elif _MUTANT == 15:
        a = "consoleEcrire(CMD_LANGUE)"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, 'consoleEcrire(CMD_LANGUE + " " + code)', 1)
    elif _MUTANT == 16:
        a = "    var a = { motif: motif, tampon: t, resoudre: resoudre,"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, "    var second = portConsole.readable.getReader();\n" + a, 1)
    elif _MUTANT == 17:
        if GARDE_REENTRANCE not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(GARDE_REENTRANCE, "", 1)
    elif _MUTANT == 18:
        a = "rien a faire : la langue est DEJA"
        if a not in p.get(CONSOLE_C, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[CONSOLE_C] = p[CONSOLE_C].replace(a, "deja fait pour la langue", 1)
    elif _MUTANT == 19:
        a = "var CMD_LANGUE ="
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, "/* voir dn_console.c:1015 */ " + a, 1)
    elif _MUTANT == 20:
        r["sortie_anticipee"] = True
    elif _MUTANT == 21:
        raise RuntimeError("mutant 21 : corps qui LEVE — c'est son role")
    elif _MUTANT == 22:
        e["cibles"][1] = ()
    elif _MUTANT == 23:
        e["cibles"][24] = tuple(e["cibles"][24]) + ("c99",)
    elif _MUTANT == 24:
        e["cibles"][99] = ("c1",)      # une cible pour un mutant INEXISTANT
    elif _MUTANT == 25:
        # 🔴 LA FAUTE EXACTE QUE LA REVUE A TROUVEE, REPLANTEE : la 5e issue
        #    cesse d'avoir SON litteral et partage celui du refus ⇒ une vraie
        #    langue inconnue serait annoncee « posee a chaud, non persistee ».
        a = "if (RE_NVS_REFUSEE.test(r2.texte)) {"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "if (RE_REFUS_CARTE.test(r2.texte)) {", 1)
    elif _MUTANT == 26:
        a = "var RE_REFUS_CARTE = /n'est pas une langue connue/;"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, "var RE_REFUS_CARTE = /REFUS|Command returned non-zero error "
               "code/;", 1)
    elif _MUTANT == 27:
        a = ('blocMot("etat-langue", "langue.refusee");\n'
             '              languePort("langue.refusee");\n')
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, 'blocMot("etat-langue", "langue.refusee");\n', 1)
    elif _MUTANT == 28:
        a = '<button id="%s" type="button" disabled>' % BOUTON_POSER
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '<button id="%s" type="button">' % BOUTON_POSER, 1)
    elif _MUTANT == 29:
        # ⚠️ IL VISE LE SITE DE `moduleAbsent`, ⛔ pas un autre : c'est celui qui
        #    masque le flash quand le module distant ne vient PAS.
        a = ("  if (blocInstaller) { blocInstaller.hidden = true; }\n"
             "  langueOffrir();                                 "
             "/* dn7-3 — le geste suit */\n"
             "  var e = document.getElementById(\"etat-cdn\");")
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, "  if (blocInstaller) { blocInstaller.hidden = true; }\n"
               "  var e = document.getElementById(\"etat-cdn\");", 1)
    elif _MUTANT == 30:
        a = "          langueRelais(r.texte);\n"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "", 1)
    elif _MUTANT == 31:
        a = "reste: a.tampon.slice(i)"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, 'reste: ""', 1)
    elif _MUTANT == 32:
        a = "var DELAI_INVITE = 6000;"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "var DELAI_INVITE = 0;", 1)
    elif _MUTANT == 33:
        # ⚠️ IL RETIRE LA LIGNE DE **`cmd_langue` SEULE** : le prefixe partage
        #    reste dans le fichier, imprime par d'autres reglages. Une relecture
        #    au FICHIER resterait donc VERTE — c'est tout l'objet du correctif.
        corps = corps_c(p.get(CONSOLE_C, ""), FONCTION_LANGUE)
        a = "— la langue est posee A CHAUD"
        if not corps or a not in corps:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        i = p[CONSOLE_C].index(corps)
        p[CONSOLE_C] = (p[CONSOLE_C][:i] + corps.replace(a, " — le reglage tient", 1)
                        + p[CONSOLE_C][i + len(corps):])
    elif _MUTANT == 34:
        a = "var RE_NVS_REFUSEE = /— la langue est posee A CHAUD/;"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, "var RE_NVS_REFUSEE = /ECRITURE NVS REFUSEE/;", 1)
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
        # ⛔ PAS une sortie par exception, qui rendrait 1 et se confondrait
        #    avec un vrai defaut : un mutant inconnu est une ERREUR D'APPEL.
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
    print("dn7-3 — LA LANGUE SE CHOISIT A L'INSTALLATION, ET LA CARTE L'A"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)
    print("cibles     : %s" % " · ".join(FIXES))
    print("⛔ CETTE GATE N'EXECUTE PAS LE JAVASCRIPT DE LA PAGE, N'OUVRE AUCUN")
    print("   PORT ET NE PARLE A AUCUNE CARTE. Que la langue soit VRAIMENT")
    print("   posee, et qu'elle SURVIVE au reboot, se lit AU BANDEAU DE LA")
    print("   DALLE — une seance carte, et rien d'autre.")

    # ── (c0) LE PRE-VOL : LES FICHIERS SE LISENT ────────────────────────
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

    # 🔴 UN MUTANT QUI MEURT SORTIRAIT EN TRACEBACK, SANS `BILAN` — or « pas
    #    de BILAN » est le discriminant d'une gate MORTE. ⇒ il se rend en KO.
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
    script = region(page, "<script>", "</script>")
    # ⛔ CE QUI S'EXECUTE, ⛔ PAS CE QUI L'EXPLIQUE : une gate qui compte la
    #    prose de ses propres commentaires rougit sur sa documentation.
    js = sans_commentaires(script)

    # ── (c1)(c2)(c3) LE CHOIX, ET SON DEFAUT ────────────────────────────
    print("\n── (c1)(c2)(c3) LE CHOIX EXISTE, IL PRECEDE, IL A SON DEFAUT ─────")
    ok, vus = choix_a_deux_positions(page)
    ctrl(ok, "(c1) le choix de la DALLE a DEUX positions",
         "`%s` et `%s`, sous `#%s`" % (BOUTON_DALLE_EN, BOUTON_DALLE_FR,
                                       SECTION_DALLE) if ok
         else "⛔ %d position(s) : %s — un choix a une seule entree ⛔ ne "
              "choisit rien, et l'inconnu repart avec le defaut sans l'avoir "
              "voulu" % (len(vus), " ".join(vus) or "aucune"))

    ok, det = choix_precede_le_flash(page)
    ctrl(ok, "(c2) le choix PRECEDE l'element de flash", det if ok
         else "⛔ %s — `UX-DR7.2` exige le choix VISIBLE AVANT le flash : "
              "offert apres, il arrive quand la carte est deja ecrite" % det)

    ok, (ecrit, poses) = defaut_anglais_dans_le_document(page, js)
    ctrl(ok, "(c3) le defaut ANGLAIS est ECRIT dans le document",
         "`aria-pressed` pose dans le fichier, ⛔ par aucun script" if ok
         else "⛔ %s — le defaut anglais est STRUCTUREL : il tient AVANT que "
              "le moindre script tourne, comme celui de la dalle tient par "
              "l'ABSENCE d'ecriture en NVS"
              % ("l'attribut n'est pas ECRIT sur les deux boutons" if not ecrit
                 else "%d pose(s) par script hors d'un clic : %s"
                      % (len(poses), " · ".join(poses[:2]))))

    # ── (c4)(c5) DEUX LANGUES DIFFERENTES, ET LA PAGE LE DIT ────────────
    print("\n── (c4)(c5) LA DALLE ET LA PAGE, ⛔ PAS LA MEME LANGUE ────────────")
    ok, (absents, fuites) = deux_choix_restent_distincts(page, js)
    ctrl(ok, "(c4) le choix de la DALLE ⛔ n'est pas celui de la PAGE",
         "4 boutons, 2 sections, 2 mecanismes disjoints" if ok
         else "⛔ %s — deux langues DIFFERENTES sont en jeu, et une marche qui "
              "les melange en casse une"
              % ("identifiant(s) absent(s) : %s" % " ".join(absents) if absents
                 else "le geste de la dalle touche a la langue de la PAGE : %s"
                      % " ".join(fuites)))

    ok, absentes = la_page_dit_que_c_est_la_dalle(page)
    ctrl(ok, "(c5) la page DIT que c'est la dalle, en 2 langues",
         "la distinction est ecrite des DEUX cotes" if ok
         else "⛔ mention absente en %s — un lecteur qui ne l'a pas dans SA "
              "langue voit deux selecteurs et croira qu'ils font la meme chose"
              % "/".join(absentes))

    # ── (c6) LE GESTE, ET SON BOUTON ────────────────────────────────────
    print("\n── (c6) LE GESTE EST EXPLICITE, ET ATTEIGNABLE ───────────────────")
    ok, (present, replies) = le_geste_est_atteignable(page)
    ctrl(ok, "(c6) le geste de pose a SON bouton, hors repli",
         "`%s`, a profondeur 0 de `<details>`" % BOUTON_POSER if ok
         else "⛔ %s — le geste est EXPLICITE parce que le delai fin-de-flash "
              "⇒ REPL est NON MESURE ; replie, il devient introuvable"
              % ("le bouton de pose est absent de la page" if not present
                 else "REPLIE(S) : %s" % " · ".join(replies)))

    # ── (c7)(c8) L'ORDRE, ET CE QUI N'EST PAS ENVOYE ────────────────────
    print("\n── (c7)(c8) L'ORDRE, ET LE DEFAUT QUI N'EN ENVOIE AUCUN ──────────")
    ok, (cmd, codes, firmware, envoi) = ordre_forme_de_la_table(
        js, neuf["fichiers"].get(LANGUE_C, ""))
    ctrl(ok, "(c7) l'ordre est `langue` + un code de la table",
         "`%s` + %s, et le binaire porte %s"
         % (cmd, "/".join(codes), "/".join(firmware)) if ok
         else "⛔ %s — une valeur hors bornes est REFUSEE par la carte, ⛔ pas "
              "ecretee : fabriquer un code que le binaire ne porte pas, c'est "
              "fabriquer le refus"
              % ("la commande declaree est %r, ⛔ pas %r" % (cmd, CMD_ATTENDUE)
                 if cmd != CMD_ATTENDUE
                 else "l'ordre n'est envoye nulle part" if not envoi
                 else "codes de la page %s ⇔ codes du binaire %s"
                      % (list(codes), list(firmware))))

    ok, det = rien_n_est_ecrit_pour_l_anglais(js)
    ctrl(ok, "(c8) anglais ⇒ ⛔ AUCUNE ecriture, et la garde PRECEDE",
         det if ok
         else "⛔ %s — le defaut se prouve PAR L'ABSENCE D'ECRITURE, ⛔ pas "
              "par une ecriture qui vaudrait « anglais »" % det)

    # ── (c9)(c10) LE TRANSPORT ──────────────────────────────────────────
    print("\n── (c9)(c10) LE VERROU EST RENDU, ET L'INVITE PRECEDE ────────────")
    ok, (pris, rendus) = le_verrou_est_rendu_deux_fois(js)
    ctrl(ok, "(c9) le verrou d'ecriture est rendu sur les 2 chemins",
         "1 prise, %d restitutions" % rendus if ok
         else "⛔ %d prise(s) pour %d restitution(s) — un verrou d'ecriture "
              "non relache fait partir `close()` en rejet, et le port reste "
              "tenu EN SILENCE" % (pris, rendus))

    ok, det = l_invite_precede_l_envoi(js)
    ctrl(ok, "(c10) l'invite est ATTENDUE avant l'envoi", det if ok
         else "⛔ %s — un envoi trop tot perd la ligne, et une ligne perdue "
              "produit « un succes annonce sur une langue non posee »" % det)

    # ── (c11)(c12)(c13) LES QUATRE ISSUES ───────────────────────────────
    print("\n── (c11)…(c13) QUATRE ISSUES, ET UN SUCCES QUI SE RELIT ──────────")
    ok, (absentes, sans_mot) = quatre_issues_distinctes(js)
    ctrl(ok, "(c11) les QUATRE issues sont nommees SEPAREMENT",
         "posee · refusee · sans reponse · pas d'invite" if ok
         else "⛔ %s — ⛔ jamais « posee » pour un silence, ⛔ jamais "
              "« refusee » pour une absence d'invite"
              % ("issue(s) sans annonce : %s" % " ".join(absentes) if absentes
                 else "issue(s) sans texte dans `MOTS` : %s"
                      % " ".join(sans_mot)))

    ok, (manquants, deplacees) = chaque_issue_dans_sa_branche(js)
    ctrl(ok, "(c12) chaque issue est ANCREE dans SA branche",
         "%d issue(s), chacune dans la branche qui la decide"
         % len(ANCRES_ISSUES) if ok
         else "⛔ %s — une cle presente « quelque part » ne dit rien : c'est "
              "la BRANCHE qui decide de ce que le lecteur lira"
              % ("issue(s) absente(s) : %s" % " ".join(manquants) if manquants
                 else "issue(s) hors de LEUR branche : %s"
                      % " · ".join(deplacees)))

    ok, det = le_succes_vient_de_la_relecture(js)
    ctrl(ok, "(c13) le succes ne vient QUE de la relecture", det if ok
         else "⛔ %s — on relit l'ACCEPTATION puis l'ETAT, ⛔ jamais l'ordre "
              "envoye" % det)

    # ── (c14)(c15) L'ATTENTE, ET LE SECOND CLIC ─────────────────────────
    print("\n── (c14)(c15) UN SEUL LECTEUR, ET UN SEUL GESTE EN VOL ───────────")
    ok, (lecteurs, branchee) = un_seul_lecteur(js)
    ctrl(ok, "(c14) l'attente ⛔ ne prend PAS un second lecteur",
         "1 lecteur, et l'attente est alimentee par l'entonnoir" if ok
         else "⛔ %s — `port.readable` n'admet QU'UN lecteur : en prendre un "
              "second echoue, et le liberer casse le journal"
              % ("%d lecteurs pris" % lecteurs if lecteurs != 1
                 else "l'attente n'est branchee sur aucun entonnoir"))

    ok, _ = le_geste_garde_sa_re_entrance(js)
    ctrl(ok, "(c15) le geste porte sa garde de RE-ENTRANCE",
         "un second clic en vol est IGNORE" if ok
         else "⛔ absente — deux clics envoient deux ordres sur le meme port, "
              "et les deux attentes se volent leurs lignes")

    # ── (c16)(c17) CE QUE LA CARTE REPOND, ET OU C'EST ECRIT ────────────
    print("\n── (c16)(c17) LES REPONSES SONT RELUES AU FIRMWARE ───────────────")
    ok, (orphelins, absents, perdus, muets, boiteux) = \
        l_appariement_est_biunivoque(neuf["fichiers"], js)
    ctrl(ok, "(c16) page ⇄ firmware : l'appariement est BIUNIVOQUE",
         "%d reponse(s) relues, appariees, et matchees par la page"
         % len(APPARIEMENT) if ok
         else "⛔ %s — un litteral relu que personne n'apparie ne garde rien, "
              "et un motif de la page que rien ne relit pourrit en silence"
              % ("motif(s) de la page RELU(S) par personne : %s"
                 % " ".join(orphelins) if orphelins
                 else "motif(s) attendu(s) ABSENT(S) de la page : %s"
                      % " ".join(absents) if absents
                 else "reponse(s) DISPARUE(S) du firmware : %s" % " ".join(perdus)
                 if perdus
                 else "temoin(s) qui ne portent pas leur litteral : %s"
                      % " ".join(boiteux) if boiteux
                 else "motif(s) de la page qui ⛔ ne MATCHENT PAS la reponse "
                      "du firmware : %s" % " ".join(muets)))

    ok, vues = la_page_ne_cite_aucune_ligne(page)
    ctrl(ok, "(c17) ⛔ la page ne cite AUCUN numero de ligne",
         "0 adresse `fichier:ligne` du firmware dans la page" if ok
         else "⛔ %d adresse(s) : %s — une adresse se perime au premier "
              "commit ; c'est la GATE qui relit, ⛔ pas la page qui pointe"
              % (len(vues), " ".join(sorted(set(vues))[:3])))

    # ── (c21)(c22) LA CINQUIEME ISSUE, ET L'ANCRAGE DU CLASSEMENT ───────
    print("\n── (c21)(c22) LA 5e ISSUE, ET UN CLASSEMENT QUI NE DERIVE PAS ────")
    ok, det = la_cinquieme_issue_a_sa_cle(js)
    ctrl(ok, "(c21) « posee A CHAUD, ⛔ non persistee » a SA cle", det if ok
         else "⛔ %s — la dalle A change et elle ⛔ ne gardera PAS ce "
              "changement : ⛔ jamais « refusee », ⛔ jamais « posee »" % det)

    ok, (disparus, boiteux, mordus) = le_classement_est_ancre(neuf["fichiers"], js)
    ctrl(ok, "(c22) ⛔ aucun motif ne classe un journal ETRANGER",
         "%d temoin(s) etranger(s) relus au firmware, ⛔ aucun mordu par les "
         "%d motifs de classement" % (len(TEMOINS_ETRANGERS),
                                      len(MOTIFS_QUI_CLASSENT)) if ok
         else "⛔ %s — la console est BAVARDE, et le geste se joue dans la "
              "fenetre de demarrage a froid ou ces erreurs sont REELLES"
              % ("temoin(s) DISPARU(S) du firmware : %s" % " ".join(disparus)
                 if disparus
                 else "temoin(s) qui ne portent pas leur litteral : %s"
                      % " ".join(boiteux) if boiteux
                 else "motif(s) qui MORDENT sur un journal etranger : %s"
                      % " · ".join(mordus)))

    # ── (c23)(c24)(c25) LE PORT, LE GESTE, ET LES OCTETS LUS ────────────
    print("\n── (c23)…(c25) LE PORT SE DIT, LE GESTE SUIT, LES OCTETS SORTENT ─")
    ok, (muettes, sans_mot) = chaque_issue_dit_le_port(js)
    ctrl(ok, "(c23) chaque issue DIT ce qu'il advient du port",
         "toute annonce du geste est suivie de `%s`" % APPEL_PORT if ok
         else "⛔ %s — un port tenu EN SILENCE empeche l'agent de repartir, et "
              "rien ne l'expliquerait"
              % ("annonce(s) MUETTE(S) sur le port : %s" % " ".join(muettes)
                 if muettes
                 else "cle(s) sans texte dans `MOTS` : %s" % " ".join(sans_mot)))

    ok, (desarme, sourdes, lit) = le_geste_suit_le_bloc_de_flash(page, js)
    ctrl(ok, "(c24) le geste ⛔ ne s'offre pas sans le bloc de flash",
         "`disabled` ecrit dans le document, et les 3 sites l'arment" if ok
         else "⛔ %s — proposer de poser une langue pour un flash qui ne peut "
              "pas avoir lieu est une promesse que la page SAIT fausse"
              % ("le bouton ⛔ ne porte PAS `disabled` dans le document"
                 if not desarme
                 else "site(s) qui masquent le flash SANS rearmer le geste : %s"
                      % " ".join(sourdes) if sourdes
                 else "`langueOffrir` ⛔ ne LIT PAS l'etat du bloc de flash"))

    ok, det = les_octets_lus_sont_relayes(js)
    ctrl(ok, "(c25) sans invite, les octets LUS sont relayes", det if ok
         else "⛔ %s — c'est le SEUL cas ou le texte brut nomme le vrai "
              "obstacle : boucle de demarrage, mode download, invite changee"
              % det)

    # ── (c26) CE QUI SUIT L'INVITE N'EST PAS JETE ───────────────────────
    print("\n── (c26) LE RESTE DE LA LECTURE EST REPRIS, ⛔ PAS JETE ───────────")
    ok, det = le_reste_de_lecture_est_repris(js)
    ctrl(ok, "(c26) le reste de la lecture est REPRIS, ⛔ pas jete", det if ok
         else "⛔ %s — la carte ecrit en trames arbitraires : jeter ce qui suit "
              "l'invite rendrait un verdict sur un texte TRONQUE" % det)

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

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : que la langue soit VRAIMENT")
    print("   posee dans la carte, ni qu'elle SURVIVE a une coupure. Le")
    print("   bandeau est SUR LA DALLE, et il se lit A L'ŒIL — une seance")
    print("   carte, portee au ledger avec son instrument.")
    return bilan(1 if ko_total[0] else 0)


if __name__ == "__main__":
    sys.exit(main())

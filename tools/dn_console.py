#!/usr/bin/env python3
"""
DeskNode — pilote de la console de mesure, côté machine.

POURQUOI CET OUTIL EXISTE
=========================
La console de `firmware/desknode` est interactive : elle sert à rejouer une
campagne de mesure (AC4/AC5/AC6) sans reflasher entre chaque branche. Mais
`idf.py monitor` est un terminal HUMAIN : il ne rend rien d'exploitable, et une
campagne de 20 commandes tapées à la main est un endroit à erreurs — on oublie
une branche, on relit un chiffre de travers, on ne sait plus quelle
configuration était active.

Cet outil sépare ce qui doit l'être :
  - la MACHINE tape les commandes, attend l'invite, capture la sortie ;
  - l'HUMAIN fait les gestes physiques (BOOT+RESET, câble) et surtout REGARDE
    la dalle. Aucune capture série ne dira jamais si la barre déchire.

⚠️ DEUX LECTEURS SUR LE MÊME PORT NE S'EXCLUENT PAS — ils se VOLENT LES OCTETS.
   MESURÉ le 2026-08-15 : deux processus ont lu /dev/ttyACM0 simultanément sans
   la moindre erreur. Linux ne pose pas de verrou sur un tty par défaut. Le
   danger n'est donc pas un échec bruyant, c'est une campagne SILENCIEUSEMENT
   fausse : un `idf.py monitor` resté ouvert avale une partie des réponses, et
   on relève des chiffres tronqués sans jamais savoir qu'il en manquait.
   Ce script se défend en deux temps : il REFUSE de démarrer s'il trouve déjà un
   détenteur du port (scan de /proc/*/fd), puis il pose TIOCEXCL pour que
   personne ne vienne se greffer après lui.

⚠️ CETTE CARTE EST EN USB NATIF (ESP32-S3 USB-Serial/JTAG). Ouvrir le port ne la
   redémarre PAS — contrairement aux adaptateurs CH343/CP2102, où le DTR/RTS
   provoque un reset. On ne touche donc volontairement ni à `dtr` ni à `rts` :
   une campagne peut s'ouvrir et se fermer sans perturber la mesure en cours.

⚠️ APRÈS UN `reboot` (ou un reset de puce), l'USB se ré-énumère et l'attachement
   usbipd TOMBE : le port revient en root:root et toute lecture sort
   « [Errno 13] Permission denied ». Rejouer `./tools/wsl-attach.sh`. Ce script
   le détecte et le dit plutôt que de laisser une trace obscure.

USAGE
=====
    python3 tools/dn_console.py aide
    python3 tools/dn_console.py "cfg" "mem"
    python3 tools/dn_console.py --timeout 40 "cpu 30"
    python3 tools/dn_console.py --listen 15            # écoute seule, rien envoyé
    python3 tools/dn_console.py --reset                # reset RTS + bandeau de BOOT
    python3 tools/dn_console.py --reset "cfg" "mem"    # reset, puis on enchaîne
    python3 tools/dn_console.py --json "fps 15"        # sortie machine
    python3 tools/dn_console.py --capture session.log "tear on"
    python3 tools/dn_console.py --temoin-negatif          # AC1.5, SANS carte
    python3 tools/dn_console.py --refus-tolere i2c "i2c scan"

🔴 CODE DE RETOUR — IL A CHANGÉ AVEC `dn4-23`, ET C'EST LE CŒUR DE LA STORY.
   Il vaut 0 seulement si, pour CHAQUE commande :
     · l'invite a été rendue (inchangé) ;
     · **AUCUN REFUS n'a été lu** dans la sortie (`refusé :` · `ESP_ERR_` ·
       `Unrecognized command` · `non-zero error code` · `Internal error:`) ;
     · **le compteur de lignes de la carte correspond** à ce qui est arrivé.
   ⇒ **UN « 0 » VEUT DIRE « ZÉRO MESURÉ », JAMAIS « la commande a été refusée
     à l'écran et personne ne l'a lu ».** Avant dn4-23, deux fenêtres de 90 s
     ont rendu 0 sur un stimulus qui n'avait JAMAIS tourné.
   ⚠️ `--refus-tolere <commande>` désarme le rc pour les campagnes où le refus
      EST l'objet de la mesure. ⛔ Jamais par défaut, et le refus reste IMPRIMÉ.
   ⚠️ Un timeout n'est PAS forcément une erreur — `tear on` ne rend pas la main,
      c'est normal ; utiliser --no-wait pour ces commandes-là.
"""

import argparse
import contextlib
import glob
import io
import json
import os
import re
import statistics
import sys
import time

try:
    import serial
except ImportError:
    sys.stderr.write(
        "pyserial absent. Installer : python3 -m pip install --user pyserial\n")
    raise SystemExit(2)

PROMPT = b"desknode>"
DEFAULT_PORT = "/dev/ttyACM0"
DEFAULT_BAUD = 115200

# ═══════════════════════════════════════════════════════════════════════════
# dn4-23 / AC1 — UN HARNAIS QUI POSE UNE COMMANDE **LIT LE REFUS**
# ═══════════════════════════════════════════════════════════════════════════
#
# 🔴 LE DÉFAUT, MESURÉ, ⛔ PAS SUPPOSÉ. Deux fenêtres de 90 s ont rendu **0**
#    sur un stimulus QUI N'A JAMAIS TOURNÉ :
#      · `anim on 10`  ⇒ `refusé : ESP_ERR_INVALID_ARG`
#      · `flash on`    ⇒ `refusé : ESP_ERR_INVALID_STATE`
#    La carte avait refusé À L'ÉCRAN, en clair, et le pilote a conclu « 0 ».
#    ⇒ **Un « 0 » doit vouloir dire « zéro mesuré », jamais « la commande a été
#      refusée et personne ne l'a lu ».**
#
# ⛔ NE PAS SE CONTENTER DU FRANÇAIS. La convention `refusé : <ESP_ERR_…>` est
#    la NÔTRE, mais une commande peut rendre non
#    zéro **sans rien imprimer du tout**. Les deux derniers motifs viennent du
#    REPL d'ESP-IDF lui-même (`components/console/esp_console_common.c`) et
#    valent pour TOUTE commande :
#      · `Unrecognized command`                       (err == ESP_ERR_NOT_FOUND)
#      · `Command returned non-zero error code: 0x…`  (ret != ESP_OK)
#      · `Internal error: …`                          (err != ESP_OK)
#    ✅ Le deuxième est DÉJÀ lu par `tools/sonde_horloge_dn418.py`, qui sort en 1
#       dessus. Cette parade existait donc, à UN endroit, et nulle part ailleurs.
#
# ⚠️ POURQUOI `ESP_ERR_` EST DANS LA LISTE ALORS QU'IL PEUT ÊTRE INFORMATIF :
#    un scan I²C imprime `ECHEC (ESP_ERR_NOT_FOUND)` sur une adresse absente,
#    et c'est un résultat NORMAL. Le drapeau est levé quand même, et c'est
#    voulu : pour ces campagnes-là le refus EST l'objet de la mesure, et
#    `--refus-tolere <commande>` le désarme **explicitement, commande par
#    commande**. ⛔ Jamais par défaut : un instrument qui se tait par confort
#    est exactement ce que cette story supprime.
MOTIFS_REFUS = (
    # ⛔ Le « : » est OBLIGATOIRE dans le motif français. Sans lui, la phrase
    #    pédagogique « (refuse hors bornes, jamais ecrete) » — imprimée par
    #    l'USAGE de `widget opa`, donc sur un succès — deviendrait un refus.
    # 🔴 CORRIGÉ PAR LA REVUE DU 2026-08-31 — CETTE LIGNE DISAIT « Vérifié : les
    #    66 refus réels portent tous le « : » ». **C'EST FAUX**, et le compte
    #    était déjà périmé par le commit qui l'entourait. Mesuré sur les
    #    LITTÉRAUX IMPRIMÉS, commentaires retirés : **85** portent `refus*`,
    #    **56** portent le « : », **29 ne le portent pas** — dont des chemins de
    #    refus RÉELS en parenthèses (`refuse (%s) — RIEN n'a change`,
    #    `voie refusee (%s)`). Ceux-là ne sont vus que par `ESP_ERR_` ou par la
    #    ligne du REPL. ⛔ Le « : » reste obligatoire DANS CE MOTIF-CI (sans lui
    #    la phrase pédagogique deviendrait un refus) ; ce qui change, c'est
    #    qu'on ne prétend plus qu'il couvre tout.
    # ⛔ ET ON NE RÉCITE PLUS DE COMPTE ICI. Un nombre recopié dans le fichier
    #    qui installe « relire, ⛔ pas réciter » se périme au commit suivant —
    #    celui-ci l'a fait dans la story même qui l'écrivait.
    ("refus firmware",
     re.compile(r"(?i)\brefus(?:ées|ees|és|es|ée|ee|é|e)\s*:")),
    ("ESP_ERR_", re.compile(r"\bESP_ERR_[A-Z0-9_]+")),
    # 🔴 dn4-23 / REVUE DU 2026-08-31 — **LA CARTE DÉCLARE SES PROPRES RÉSULTATS
    #    NON CRÉDIBLES, ET PERSONNE NE LES LISAIT.** Mesuré : `widget largeur`
    #    imprime `🔴 … DRAPEAU LEVE` puis `⛔ NE PAS CONCLURE SUR CE CHIFFRE`,
    #    puis LE CHIFFRE, et rendait **rc 0** — une campagne qui lit `rc`
    #    consommait 63 px comme une mesure valide de `RÉSEAU`. Même forme sur le
    #    scan I²C (`🔴 TEMOIN POSITIF EN ECHEC`, `🔴 SCAN INTERROMPU a 0x..`),
    #    qui rend 0 lui aussi. ⇒ Un instrument qui écrit « ne pas conclure » et
    #    rend 0 dit DEUX choses opposées ; c'est exactement le vide sur lequel
    #    cette story interdit de conclure.
    ("carte : verdict NON CRÉDIBLE",
     re.compile(r"NE PAS CONCLURE|DRAPEAU LEVE|TEMOIN POSITIF EN ECHEC"
                r"|SCAN INTERROMPU")),
    ("REPL: commande inconnue", re.compile(r"Unrecognized command")),
    ("REPL: code de retour non nul",
     re.compile(r"Command returned non-zero error code")),
    ("REPL: erreur interne", re.compile(r"Internal error:")),
)


def _lignes(texte):
    """Découpe en lignes **comme la carte compte** : sur `\\n`, ⛔ rien d'autre.

    🔴 dn4-23 / REVUE DU 2026-08-31 — `str.splitlines()` COUPE AUSSI sur `\\r`,
       `\\x0b`, `\\x0c`, `\\x1c`–`\\x1e` et `\\u2028`. Le firmware, lui, ne compte
       que `if (*q == '\\n') { s_lignes_cmd++; }`. Un simple retour-chariot de
       rafraîchissement d'invite (linenoise en émet) fabriquait donc chez l'hôte
       une frontière que la carte n'avait pas comptée ⇒ `LIGNES_ETRANGERES`, et
       **une seule de ces fausses frontières suffisait à annuler une VRAIE perte**
       (voir l'angle mort écrit dans `completude()`).
    """
    return [l.rstrip("\r") for l in texte.split("\n")]


def chercher_refus(texte):
    """Rend la liste des `(motif, ligne)` de refus trouvés dans `texte`.

    🔴 FONCTION **PURE**, ET C'EST LA CONDITION DU TÉMOIN NÉGATIF. Le verdict
       d'AC1 se joue donc **sans carte**, sur des sorties FABRIQUÉES
       (`--temoin-negatif`). *« Une gate qu'aucun test n'a vue échouer est
       décorative »* — dn4-13 / AC7.5.
    ⚠️ Une même ligne peut porter deux motifs (« refusé : ESP_ERR_… ») : elle
       n'est comptée qu'UNE fois, sous le premier motif qui la reconnaît. Un
       compte gonflé ferait croire à deux refus là où il y en a un.
    🔴 CORRIGÉ PAR LA REVUE DU 2026-08-31 — LA DÉDUPLICATION SE FAISAIT SUR LE
       **TEXTE** DE LA LIGNE, DONC ELLE **DÉGONFLAIT** AUSSI. Reproduit : six
       lignes `ECHEC (ESP_ERR_NOT_FOUND)` d'un scan I²C rendaient **UN** refus,
       et `🔴 REFUS [...]` s'imprimait une fois pour six adresses refusées. Le
       docstring ne justifiait que la direction inverse. ⇒ on déduplique
       désormais par **POSITION** : deux motifs sur LA MÊME ligne comptent pour
       un ; la même phrase à deux endroits compte pour deux.
    """
    vus = []
    for i, ligne in enumerate(_lignes(texte)):
        for nom, rx in MOTIFS_REFUS:
            if rx.search(ligne):
                vus.append((nom, ligne.strip(), i))
                break
    return [(nom, ligne) for nom, ligne, _ in vus]


# ═══════════════════════════════════════════════════════════════════════════
# dn4-23 / AC2 — L'INSTRUMENT DIT S'IL A TOUT LU
# ═══════════════════════════════════════════════════════════════════════════
#
# 🔴 CE PILOTE PERD DES LIGNES. Mesuré : **6 captures sur 20 en lot** violaient
#    l'invariant `N == X + Y` du scan I²C (dont une où le témoin positif `0x5D`
#    était ABSENT sous un verdict « ✅ témoin positif OK ») — **et 1 sur 7 en
#    invocation SOLO**.
#
# ⛔ LA PARADE DE `dn4-2` EST DONC **INSUFFISANTE**, ET C'EST ÉCRIT ICI PARCE
#    QUE C'EST ICI QU'ON S'EN SERT. Elle disait : *« 1. toute passe publiée
#    vient d'une invocation SOLO ; 2. l'invariant est vérifié sur chaque
#    capture »*. Le point 1 **ne suffit pas** : la perte existe AUSSI en solo.
#    Le point 2 reste bon — mais il n'existait que pour le scan I²C, et lui
#    seul. C'est cette forme-là qu'on généralise à TOUTE commande.
#
# ⚠️ LA CAUSE RESTE **NON INSTRUITE**, et ⛔ on n'en invente pas une : **2 A/B
#    et 30 passes de contrôle** (15 avec `--capture`, 15 sans) n'ont RIEN
#    reproduit. Les deux mécanismes candidats sont toujours là, délibérément :
#      · `ser.reset_input_buffer()` AVANT l'écriture — ⛔ il ne se retire PAS,
#        c'est lui qui garantit que la sortie rendue appartient à LA commande
#        envoyée (voir le pavé de `envoyer()`) ;
#      · `nettoyer()`, qui coupe « jusqu'à la première ligne qui se termine par
#        la commande » — couvert par `corps_de_capture()` ci-dessous, qui rend
#        `coupees_avant_echo`.
#        🔴 CE RENVOI DÉSIGNAIT UNE FONCTION QUI N'EXISTE NULLE PART — un nom
#           de brouillon resté dans la prose. C'est EXACTEMENT le défaut que
#           `dn4-13` a payé (le renvoi vers une fonction de drainage des
#           harnais de dn4-4, qui n'existait pas), et il a été attrapé par la
#           gate faite pour ça, `verif_harnais_dn413.py`, DANS LA STORY MÊME
#           qui répare les instruments qui nomment ce qui n'est pas.
#           ⚠️ Et le nom fautif n'est PAS recopié ici : cette gate n'a AUCUN
#              échappement — le citer, même pour expliquer, le recrée.
#    ⇒ **CE CODE REND LA PERTE VISIBLE. Il ne la supprime pas.**
RE_COMPTEUR = re.compile(r"^-{3} fin : (\d+) lignes emises(.*?)-{3}$")


def corps_de_capture(brut, commande):
    """Le tampon BRUT réduit à ce que la commande a émis : sans l'écho, sans
    l'invite finale. Rend `(corps, coupees_avant_echo, echo_vu)`.

    ⚠️ `coupees_avant_echo` est le SECOND mécanisme candidat de perte : tout ce
       que `nettoyer()` jette avant l'écho. En régime sain il vaut 0 —
       `reset_input_buffer()` a vidé le tampon juste avant l'écriture.
    """
    lignes = _lignes(brut)
    i_echo = None
    for i, l in enumerate(lignes):
        if l.strip().endswith(commande):
            i_echo = i
            break
    if i_echo is None:
        corps = list(lignes)
    else:
        corps = lignes[i_echo + 1:]
    while corps and not corps[-1].strip().rstrip(">").strip():
        corps.pop()
    if corps and corps[-1].strip().endswith("desknode>"):
        corps.pop()
    return corps, (i_echo or 0), (i_echo is not None)


def completude(brut, commande):
    """AC2.1/2.2/2.3 — confronte le COMPTEUR DE LIGNES de la carte à ce qui a
    été reçu, et signale ce que `nettoyer()` a coupé en plus.

    🔴 FONCTION **PURE** : elle se joue sur des captures FABRIQUÉES, sans carte.
    ⛔ **Un compteur que personne ne lit ne compte pas.** C'est cette fonction
       qui fait exister celui que le firmware imprime.

    États rendus :
      `OK`               reçu == annoncé
      `PERTE`            reçu <  annoncé  ⇒ 🔴 des lignes MANQUENT
      `LIGNES_ETRANGERES` reçu >  annoncé ⇒ ⚠️ des lignes se sont INVITÉES
                         (log asynchrone d'une autre tâche : `ESP_LOGx` ne
                         passe pas par le `printf` compté). ⛔ Ce n'est PAS une
                         perte, et les confondre ferait crier au mauvais endroit.
      `SANS_COMPTEUR`    la carte n'en imprime pas ⇒ firmware antérieur à
                         dn4-23, ou commande enregistrée hors `k_cmds[]`.
                         ⛔ **Ce n'est pas « 0 perte » — c'est « on ne sait pas ».**
      `COMPTE_NON_FIABLE` la carte elle-même déclare son compte invalide
                         (sortie tronquée faute de RAM).

    🔴 **L'ANGLE MORT DE CET INVARIANT, ÉCRIT ICI PARCE QUE C'EST ICI QU'IL SE
       PRODUIT** — trouvé par les TROIS couches de la revue du 2026-08-31, et
       reproduit. L'invariant est une **SOMME SIGNÉE PAR CAPTURE** : un seul
       nombre reçu contre un seul nombre annoncé. ⇒ **une ligne PERDUE et une
       ligne ÉTRANGÈRE dans la même capture s'ANNULENT et rendent `OK`**, sans
       le moindre avertissement, rc 0. Reproduit : un `i2c scan` amputé de
       `0x23 vue` ET enrichi d'un `I (123) dn_link: trame` rend
       `{'annonce': 6, 'recu': 6, 'etat': 'OK'}` — c'est-à-dire le défaut
       d'origine (« l'adresse 0x23 n'est pas là sur un capteur QUI RÉPOND »)
       reconstruit dans le mécanisme qui existe pour l'attraper.
    ✅ **CE QUI A ÉTÉ FAIT** (décision owner du 2026-08-31) : la source
       STRUCTURELLE de surplus est tarie côté carte — `dn_ui_log_mem()` et les
       sorties de `dn_wifi.c` passaient par le `printf` de la libc, donc HORS du
       compteur (6 et 13 lignes) ; elles passent désormais par le compteur. Sans
       ça, `LIGNES_ETRANGERES` était **permanent** sur ces commandes — ce qui
       apprend à ignorer le signal — et le surplus était TOUJOURS disponible
       pour absorber une perte.
    ⛔ **CE QUI RESTE, ET QU'ON NE CACHE PAS** : un log asynchrone (`ESP_LOGx`)
       qui tombe pendant une capture reste du surplus légitime, et il peut
       encore masquer une perte simultanée. Deux nombres ne peuvent pas
       distinguer « 1 perdue + 1 invitée » de « rien ». Le remède complet est
       de NUMÉROTER les lignes côté carte ; il n'est pas pris ici, et cette
       limite est **imprimée** par `imprimer_completude()` au lieu d'être tue.
    """
    corps, coupees, echo_vu = corps_de_capture(brut, commande)
    i_cpt, annonce, fiable = None, None, True
    for i in range(len(corps) - 1, -1, -1):
        m = RE_COMPTEUR.match(corps[i].strip())
        if m:
            i_cpt = i
            annonce = int(m.group(1))
            fiable = "NON FIABLE" not in m.group(2)
            break
    r = {"coupees_avant_echo": coupees, "echo_vu": echo_vu,
         "annonce": annonce, "recu": None, "etat": None}
    if annonce is None:
        r["etat"] = "SANS_COMPTEUR"
        r["recu"] = len(corps)
        return r
    r["recu"] = i_cpt
    if not fiable:
        r["etat"] = "COMPTE_NON_FIABLE"
    elif i_cpt == annonce:
        r["etat"] = "OK"
    elif i_cpt < annonce:
        r["etat"] = "PERTE"
    else:
        r["etat"] = "LIGNES_ETRANGERES"
    return r


# 🔴 AC2.5 — **UNE CAPTURE VIDE NE PROUVE PAS UNE CARTE MUETTE.** La règle est
#    ÉCRITE ICI, au point même où le vide est rendu, ⛔ pas seulement dans un
#    commentaire de dossier : aux cycles 1 et 6 de l'A/B du 2026-08-24,
#    RE-SONDER a rendu la sortie COMPLÈTE. Une capture vide est un ÉTAT DE
#    L'INSTRUMENT, pas un état de la carte.
VIDE_NE_PROUVE_RIEN = (
    "⛔ CAPTURE VIDE — et ça ne prouve PAS que la carte est muette.\n"
    "   Mesuré (A/B du 2026-08-24) : aux cycles 1 et 6, RE-SONDER a rendu la\n"
    "   sortie COMPLÈTE. ⇒ RE-JOUER la commande avant toute conclusion.\n"
    "   ⚠️ Et la parade « invocation SOLO » de dn4-2 NE SUFFIT PAS : la perte\n"
    "      a été mesurée en solo aussi (1 sur 7)."
)


# ═══════════════════════════════════════════════════════════════════════════
# dn4-23 / AC7 — LA LATENCE PUBLIE SA DISPERSION **AVANT** TOUT DELTA
# ═══════════════════════════════════════════════════════════════════════════
#
# 🔴 CE QUE LA MESURE DIT, ET C'EST TOUT CE QU'ELLE DIT : la latence
#    `acceptation→label` vaut **86 · 138 · 220 · 86 · 260 ms** sur le MÊME
#    firmware (`fd959f2`). **Facteur 3.** ⇒ ⛔ cet instrument n'est PAS
#    utilisable comme instrument de delta tant que sa variance n'est pas isolée.
#
# ⛔ LA RÈGLE RÉFUTÉE EST ÉCRITE COMME RÉFUTÉE, ET ⛔ ON NE LA RESSUSCITE PAS.
#    Publiée puis démolie le même jour : *« un relevé n'est recevable que si
#    l'injecteur a placé 225/225 avec 0 perte seq »*. **La 5ᵉ fenêtre l'a
#    démolie : 225/225, 0 perte seq, et 260 ms** — la plus haute de toutes.
#    La corrélation sur quatre points était une **COÏNCIDENCE**.
#
# ✅ DEUX HYPOTHÈSES SONT **RÉFUTÉES**, ⛔ ne pas les rejouer :
#      · fragmentation du tas LVGL — `20 500 o / 40 752 / 2 %` AVANT ET APRÈS
#        une fenêtre complète, relevé identique ;
#      · compteurs de liaison — ils ne discriminent pas (cf. la 5ᵉ fenêtre).
#
# ⚠️ **CONSÉQUENCE RÉTROACTIVE, ET ELLE S'ÉCRIT PLUTÔT QU'ELLE NE SE CORRIGE** :
#    tout écart de latence publié sur UNE FENÊTRE UNIQUE est **non recevable**,
#    **y compris ceux de `dn4-2`**.
#
# ⛔ CETTE STORY N'ISOLE PAS LA VARIANCE. Elle empêche de conclure sans elle.
RE_LATENCE = re.compile(
    r"latence acceptation->label\s*:\s*n=(\d+)\s*·\s*min\s+(-?\d+)\s*ms"
    r"\s*·\s*moy\s+(-?\d+)\s*ms\s*·\s*max\s+(-?\d+)\s*ms")

# Nombre PLANCHER de fenêtres pour qu'un relevé soit recevable. ⚠️ 2 est le
# minimum ARITHMÉTIQUE (une dispersion demande deux points) ; le repère MESURÉ
# est 5, et l'outil le dit quand on lui en donne moins.
LATENCE_FENETRES_MIN = 2
LATENCE_FENETRES_REPERE = 5


class LatenceAmbigue(Exception):
    """Plusieurs fenêtres de latence dans une seule capture — ⛔ on ne choisit
    pas à la place de l'opérateur."""


def lire_latence(sortie):
    """Extrait `(n, min_ms, moy_ms, max_ms)` d'une sortie de `pc`, ou None.

    ⚠️ **La console de ce dépôt est RÉDIGÉE POUR UN HUMAIN** — mots-clés répétés
       dans la prose, chiffres au milieu des phrases. *La gratter au `grep`
       fabrique des nombres plausibles.* ⇒ le motif est ANCRÉ sur la ligne
       entière et sur ses quatre champs, et il est éprouvé sur une ligne
       FABRIQUÉE par `--temoin-negatif` avant d'être cru sur une ligne réelle.
    """
    # 🔴 REVUE DU 2026-08-31 — `search()` PRENAIT LA **PREMIÈRE** DE PLUSIEURS.
    #    Une capture qui porte deux lignes de latence (ré-impression asynchrone,
    #    ou reliquat d'un `--no-wait` qui déborde sur la commande suivante)
    #    faisait lire les quatre nombres de la PLUS ANCIENNE comme ceux de la
    #    courante — une mesure périmée publiée comme fraîche, sans un mot.
    #    ⛔ On ne « prend pas la dernière » : on ne sait pas laquelle appartient
    #      à la commande envoyée. On REFUSE, et on le dit.
    ms = RE_LATENCE.findall(sortie)
    if not ms:
        return None
    if len(ms) > 1:
        raise LatenceAmbigue(
            "🔴 REFUS : %d lignes de latence dans UNE capture. ⛔ Impossible de\n"
            "   savoir laquelle appartient à la commande envoyée — une ligne\n"
            "   asynchrone ou un reliquat de `--no-wait` en fabrique une\n"
            "   deuxième. ⇒ RE-JOUER la capture, seule." % len(ms))
    g = ms[0]
    return (int(g[0]), int(g[1]), int(g[2]), int(g[3]))


def dispersion(moyennes, bornes=None):
    """La dispersion d'une série de moyennes de fenêtres. ⛔ Jamais une moyenne
    seule : c'est exactement ce qui a fait publier un critère de validité qu'il
    a fallu rétracter devant l'owner.

    🔴 REVUE DU 2026-08-31 — `min`/`max` SONT CEUX DES **MOYENNES DE FENÊTRE**,
       ⛔ PAS L'ÉTENDUE OBSERVÉE, et le verdict les imprimait sous le mot
       « étendues ». Mesuré sur un cas fabriqué : `A [10 ; 12] ms` affiché pour
       des fenêtres dont le relevé portait **5** et **20**. Un lecteur prend ces
       crochets pour la plage mesurée ; ils sont **6× plus étroits**, donc le
       test de chevauchement tire bien plus rarement que le texte ne le promet.
       ⇒ `bornes` (les `(min, max)` par fenêtre, quand on les a) alimente
       `observe_min`/`observe_max`, et le verdict imprime **les deux**.
    """
    if not moyennes:
        return None
    lo, hi = min(moyennes), max(moyennes)
    obs = [x for mm in (bornes or []) for x in mm]
    return {
        "n_fenetres": len(moyennes),
        "min": lo,
        "max": hi,
        "observe_min": min(obs) if obs else None,
        "observe_max": max(obs) if obs else None,
        "etendue": hi - lo,
        "facteur": (hi / lo) if lo > 0 else None,
        "mediane": statistics.median(moyennes),
        "ecart_type": statistics.pstdev(moyennes) if len(moyennes) > 1 else 0.0,
        "fenetres": list(moyennes),
    }


def verdict_delta(a, b):
    """AC7.2 — LE DELTA ENTRE DEUX RELEVÉS, **REFUSÉ** quand il n'est pas lisible.

    ⛔ **REFUSÉ PAR L'OUTIL**, ⛔ pas déconseillé dans un commentaire : un
       commentaire ne retient personne, et celui-ci n'a retenu personne.

    Rend `(recevable, lignes)`. Trois refus, dans cet ordre :
      1. moins de deux fenêtres d'un côté ⇒ **aucune dispersion n'existe** ;
      2. les deux étendues SE CHEVAUCHENT ⇒ le delta des médianes est DANS le
         bruit du même firmware — c'est le cas mesuré (86..260 ms) ;
      3. sinon, recevable, et l'outil publie QUAND MÊME les deux dispersions.
    """
    lignes = []
    for nom, d in (("A", a), ("B", b)):
        if d is None or d["n_fenetres"] < LATENCE_FENETRES_MIN:
            n = 0 if d is None else d["n_fenetres"]
            lignes.append(
                "🔴 REFUS : le relevé %s ne porte que %d fenêtre(s). Un delta sur\n"
                "   UNE SEULE FENÊTRE est NON RECEVABLE — la latence\n"
                "   `acceptation→label` varie d'un FACTEUR 3 sur le MÊME firmware\n"
                "   (86 · 138 · 220 · 86 · 260 ms, `fd959f2`).\n"
                "   ⚠️ Conséquence rétroactive : tout écart publié sur une fenêtre\n"
                "      unique est non recevable, Y COMPRIS ceux de `dn4-2`."
                % (nom, n))
    if lignes:
        return False, lignes
    if a["n_fenetres"] < LATENCE_FENETRES_REPERE or \
       b["n_fenetres"] < LATENCE_FENETRES_REPERE:
        lignes.append(
            "⚠️ Moins de %d fenêtres d'un côté : le repère MESURÉ de dispersion\n"
            "   demande %d fenêtres consécutives. Le verdict ci-dessous est donc\n"
            "   FAIBLE, ⛔ pas faux." % (LATENCE_FENETRES_REPERE,
                                        LATENCE_FENETRES_REPERE))
    def _obs(d):
        if d.get("observe_min") is None:
            return ("\n   ⚠️ étendue OBSERVÉE non transmise par ce relevé — ⛔ ne pas\n"
                    "      lire les crochets ci-dessus comme la plage mesurée.")
        return ("\n   étendue OBSERVÉE, toutes fenêtres confondues : [%d ; %d] ms."
                % (d["observe_min"], d["observe_max"]))

    chevauche = not (a["max"] < b["min"] or b["max"] < a["min"])
    if chevauche:
        lignes.append(
            "🔴 REFUS : les DISPERSIONS DES MOYENNES DE FENÊTRE se chevauchent —\n"
            "   A [%d ; %d] ms, B [%d ; %d] ms. L'écart des médianes (%.1f ms) est\n"
            "   DANS le bruit du même firmware. ⛔ Aucun delta n'est publiable.%s%s"
            % (a["min"], a["max"], b["min"], b["max"],
               b["mediane"] - a["mediane"], _obs(a), _obs(b)))
        return False, lignes
    lignes.append(
        "✅ Les DISPERSIONS DES MOYENNES DE FENÊTRE sont DISJOINTES —\n"
        "   A [%d ; %d] ms, B [%d ; %d] ms. Écart des médianes : %+.1f ms.\n"
        "   ⚠️ Recevable NE VEUT PAS DIRE expliqué : la variance de cet\n"
        "      instrument n'est TOUJOURS PAS isolée. Deux hypothèses sont\n"
        "      RÉFUTÉES (fragmentation du tas LVGL · compteurs de liaison) et le\n"
        "      champ reste OUVERT.%s%s"
        % (a["min"], a["max"], b["min"], b["max"], b["mediane"] - a["mediane"],
           _obs(a), _obs(b)))
    return True, lignes


class ConsoleErreur(RuntimeError):
    """Échec diagnostiqué — le message est destiné à l'opérateur, pas à un log."""


def detenteurs(port):
    """Qui tient déjà ce port ? Rend [(pid, nom)]. Scan de /proc, sans dépendance
    externe (`fuser` et `lsof` ne sont pas garantis présents sous WSL).

    C'est un CONTRÔLE AVANT MESURE, pas du confort : deux lecteurs sur un tty ne
    s'excluent pas, ils se partagent les octets. Sans ce test, un moniteur oublié
    ouvert produit des réponses tronquées qu'on relèverait comme des mesures."""
    trouves = []
    for entree in glob.glob("/proc/[0-9]*/fd/*"):
        try:
            if os.readlink(entree) != port:
                continue
            pid = entree.split("/")[2]
            if int(pid) == os.getpid():
                continue
            try:
                with open(f"/proc/{pid}/cmdline", "rb") as f:
                    nom = f.read().replace(b"\0", b" ").decode(
                        "utf-8", "replace").strip() or f"pid {pid}"
            except OSError:
                nom = f"pid {pid}"
            trouves.append((pid, nom))
        except OSError:
            continue  # le processus a disparu pendant le scan — sans importance
    return trouves


def ouvrir(port, baud, ignorer_detenteurs=False):
    if not ignorer_detenteurs:
        occupants = detenteurs(port)
        if occupants:
            liste = "\n".join(f"    - [{p}] {n}" for p, n in occupants)
            raise ConsoleErreur(
                f"{port} est DÉJÀ tenu par un autre processus :\n{liste}\n"
                "  Deux lecteurs sur un tty ne s'excluent pas : ils se volent les\n"
                "  octets. La campagne rendrait des réponses TRONQUÉES sans erreur.\n"
                "  ⇒ fermer le moniteur (Ctrl+]) puis relancer.\n"
                "  (--force passe outre, à n'utiliser que si on sait ce qu'on fait.)")
    try:
        # exclusive=True pose TIOCEXCL : personne ne viendra se greffer APRÈS nous.
        return serial.Serial(port, baud, timeout=0.2, exclusive=True)
    except serial.SerialException as e:
        txt = str(e)
        if "Permission denied" in txt or "Errno 13" in txt:
            raise ConsoleErreur(
                f"{port} : permission refusée. C'est la signature d'un reset de "
                "puce (ou d'un `reboot` console) : l'USB s'est ré-énuméré et "
                "l'attachement usbipd est tombé.\n"
                "  ⇒ rejouer : cd ~/projects/desknode && ./tools/wsl-attach.sh")
        if "busy" in txt.lower():
            raise ConsoleErreur(
                f"{port} est déjà pris — très probablement `idf.py monitor`.\n"
                "  ⇒ fermer le moniteur (Ctrl+]) puis relancer.")
        if "No such file" in txt or "Errno 2" in txt:
            raise ConsoleErreur(
                f"{port} n'existe pas. La carte n'est pas attachée à WSL.\n"
                "  ⇒ rejouer : cd ~/projects/desknode && ./tools/wsl-attach.sh")
        raise ConsoleErreur(f"{port} : {txt}")


def lire_jusqu_invite(ser, timeout):
    """Lit jusqu'à revoir l'invite, ou jusqu'au timeout. Rend (texte, invite_vue)."""
    fin = time.monotonic() + timeout
    tampon = bytearray()
    while time.monotonic() < fin:
        n = ser.in_waiting
        morceau = ser.read(n if n else 1)
        if morceau:
            tampon.extend(morceau)
            # L'invite peut arriver sans passage à la ligne derrière : on la
            # cherche en queue de tampon, pas en fin de ligne.
            if tampon.rstrip().endswith(PROMPT):
                return tampon.decode("utf-8", "replace"), True
    return tampon.decode("utf-8", "replace"), False


def nettoyer(texte, commande):
    """Retire l'écho de la commande et l'invite finale — garde la SORTIE."""
    lignes = texte.splitlines()
    # L'écho de la commande est la première ligne qui la contient telle quelle.
    for i, l in enumerate(lignes):
        if l.strip().endswith(commande):
            lignes = lignes[i + 1:]
            break
    while lignes and not lignes[-1].strip().rstrip(">").strip():
        lignes.pop()
    if lignes and lignes[-1].strip().endswith("desknode>"):
        lignes.pop()
    return "\n".join(lignes).strip("\n")


def drainer(ser, jusqu_a, pas=0.02):
    """Vide le flux série JUSQU'À l'instant `jusqu_a` (temps absolu `time.time()`).

    🔴 ⛔ CE N'EST PAS UN `sleep()`, ET CE N'EST PAS UN `reset_input_buffer()`.
       · Dormir laisse le tampon d'entrée se remplir ; plein, il finit par
         BLOQUER L'ÉMETTEUR côté carte, et l'injection perd sa cadence — donc
         l'axe des temps de l'historique ment sur la durée.
       · `reset_input_buffer()` JETTE les logs asynchrones. La garde de hauteur
         a déjà « compté 8 déclenchements pendant que ce chemin-ci rendait 0
         message » (voir `envoyer()`).
       ⇒ On LIT et on jette au fil de l'eau : le tampon reste vide, la carte
         n'est jamais bloquée, et rien n'est jeté en bloc.

    Rend le nombre d'octets drainés — ⛔ pas `None` : un drainage qui ne draine
    RIEN pendant 22 s dit quelque chose (la carte est muette, ou le port est
    volé par un second lecteur), et un harnais doit pouvoir le publier.
    """
    n = 0
    while time.time() < jusqu_a:
        w = ser.in_waiting
        if w:
            n += len(ser.read(w))
        else:
            time.sleep(pas)
    return n


def envoyer(ser, commande, timeout, attendre_invite=True):
    # 🔴 PIÈGE D'INSTRUMENT MESURÉ LE 2026-08-24 (dn4-4/AC4.3) — À LIRE AVANT DE
    #    CHERCHER UN `ESP_LOG` AVEC CET OUTIL.
    #
    #    Le `reset_input_buffer()` ci-dessous JETTE tout ce que la carte a émis
    #    ENTRE deux commandes. Les logs asynchrones (ceux des tâches `dn_link`,
    #    LVGL, `dn_rtc`…) ne sont donc capturés QUE s'ils tombent PENDANT
    #    l'exécution d'une commande — la fenêtre où `lire_jusqu_invite()` lit.
    #
    #    ⇒ Un harnais qui envoie une commande, DORT, puis envoie la suivante ne
    #      verra JAMAIS le log émis pendant son sommeil. Il conclura « la garde
    #      est muette » sur une garde qui a crié six fois. **C'est arrivé**, et
    #      ça a coûté un aller-retour de diagnostic entier :
    #      la garde de hauteur du détail comptait 8 déclenchements pendant que
    #      ce chemin-ci rendait 0 message.
    #
    #    ⛔ NE PAS retirer le `reset_input_buffer()` : il est ce qui garantit que
    #      la sortie rendue appartient bien à LA commande envoyée (sinon un
    #      reliquat de la précédente se ferait passer pour la réponse).
    #    ✅ LA PARADE, côté appelant : écrire soi-même sur le port et DRAINER le
    #      flux (`ser.read(ser.in_waiting)` en boucle) pendant la fenêtre
    #      d'observation, au lieu de dormir. ⇒ `drainer()`, juste au-dessus.
    #    🔴 dn4-13 / AC7.4 — CETTE PHRASE RENVOYAIT À « la fonction `drainer()` des
    #      harnais de dn4-4 ». **ELLE N'EXISTAIT NULLE PART** : le drainage était
    #      INLINÉ dans `anim_courbe_dn44.py`, et un lecteur qui suivait le renvoi
    #      cherchait une fonction fantôme. Elle est désormais ÉCRITE ICI, et le
    #      harnais l'APPELLE — ⛔ on n'a pas corrigé la phrase, on a créé ce
    #      qu'elle promettait. Une référence à du code inexistant est de la même
    #      famille que `widget reset` : un instrument qui nomme ce qui n'est pas.
    ser.reset_input_buffer()
    ser.write((commande + "\n").encode("utf-8"))
    ser.flush()
    if not attendre_invite:
        # 🔴 dn4-23 / REVUE DU 2026-08-31 — CETTE BRANCHE ÉTAIT CASSÉE DEUX FOIS,
        #    ET C'EST LE DRAPEAU DES COMMANDES QUI NE RENDENT PAS LA MAIN.
        #    (a) `time.sleep(min(timeout, 2.0))` PLAFONNAIT LA LECTURE À 2 s en
        #        ignorant `--timeout` : avec `--no-wait --timeout 60 "tear on"`,
        #        un `refusé : ESP_ERR_INVALID_STATE` arrivé à t=2,5 s n'entrait
        #        JAMAIS dans `brut`, `invite_rendue` valait `None` (donc le test
        #        `is False` ne tirait pas) et la sortie était **0**. C'est
        #        verbatim la défaillance qu'AC1 existe pour fermer, restée
        #        ouverte sur ce drapeau-ci.
        #    (b) `sortie` valait `brut.strip()`, ÉCHO COMPRIS, alors que le pavé
        #        de `_resultat` interdit nommément de chercher un motif dans un
        #        brut qui porte encore son écho : une commande dont le TEXTE
        #        contient un motif se dénonçait elle-même (reproduit sur une
        #        trame `pc $DN,…,ESP_ERR_X*00`, qui armait rc 1).
        #    ⛔ On ne peut pas attendre l'invite ici — c'est tout l'objet du
        #      drapeau. On LIT donc au fil de l'eau pendant TOUTE la fenêtre
        #      demandée (comme `drainer()`, mais en GARDANT les octets), ce qui
        #      est aussi la parade écrite plus haut contre le sommeil aveugle.
        fin = time.monotonic() + timeout
        buf = bytearray()
        while time.monotonic() < fin:
            w = ser.in_waiting
            if w:
                buf.extend(ser.read(w))
            else:
                time.sleep(0.02)
        brut = buf.decode("utf-8", "replace")
        return _resultat(commande, brut, nettoyer(brut, commande), None)
    brut, invite = lire_jusqu_invite(ser, timeout)
    return _resultat(commande, brut, nettoyer(brut, commande), invite)


def _fusionner_refus(a, b):
    """Fusionne deux relevés de refus **sans en perdre les occurrences**."""
    def compte(v):
        d = {}
        for nom, ligne in v:
            d.setdefault(ligne, [nom, 0])[1] += 1
        return d
    ca, cb = compte(a), compte(b)
    ordre = [l for _, l in a] + [l for _, l in b]
    vus, faits = [], set()
    for ligne in ordre:
        if ligne in faits:
            continue
        faits.add(ligne)
        nom = (ca.get(ligne) or cb.get(ligne))[0]
        n = max(ca.get(ligne, [None, 0])[1], cb.get(ligne, [None, 0])[1])
        vus.extend([(nom, ligne)] * n)
    return vus


def _resultat(commande, brut, sortie, invite, compter=True):
    """dn4-23 / AC1 + AC2 — LE DICT QUE TOUT APPELANT REÇOIT, ET CE QU'IL PORTE
    DÉSORMAIS EN PLUS.

    🔴 `refus` porte **LE MOTIF EXACT TROUVÉ**, ⛔ pas un booléen nu : « la
       commande a été refusée » n'aide personne ; « refusé : ESP_ERR_INVALID_ARG »
       dit QUOI rejouer.
    ⚠️ Le refus est cherché dans la sortie NETTOYÉE **et** dans le tampon BRUT
       privé de son écho : si `nettoyer()` a coupé la ligne de refus, le brut la
       porte encore. ⛔ Chercher dans le brut SANS retirer l'écho ferait qu'une
       commande dont le TEXTE contient un motif se dénoncerait elle-même.
    """
    # 🔴 REVUE DU 2026-08-31 — `--listen` ET `--reset` ÉCHAPPAIENT ENTIÈREMENT
    #    AU DISPOSITIF : leurs dicts ne portaient NI `refus`, NI `refus_motifs`,
    #    NI `completude`, donc aucune ligne 🔴 REFUS, rc 0, et `--json` émettait
    #    pour eux un SCHÉMA DIFFÉRENT. Un `--reset` sur une carte repartie en
    #    panique, ou un `--listen 30` qui attrape un `ESP_ERR_` asynchrone,
    #    rendaient 0. Ils passent désormais ici — avec `compter=False`, parce
    #    qu'un flux passif n'a ni écho ni compteur de commande à confronter.
    hors_echo = "\n".join(
        l for l in _lignes(brut)
        if not (compter and l.strip().endswith(commande)))
    # 🔴 REVUE DU 2026-08-31 — LA FUSION DÉDUPLIQUAIT PAR TEXTE, donc elle
    #    reperdait ce que `chercher_refus` venait de compter. Les deux vues sont
    #    deux lectures du MÊME tampon : on garde, pour chaque ligne distincte, le
    #    plus grand nombre d'OCCURRENCES vu par l'une des deux.
    vus = _fusionner_refus(chercher_refus(sortie), chercher_refus(hors_echo))
    r = {"commande": commande, "sortie": sortie, "invite_rendue": invite,
         "brut": brut,
         "refus": vus[0][1] if vus else None,
         "refus_motifs": [{"motif": n, "ligne": l} for n, l in vus]}
    r["completude"] = completude(brut, commande) if (compter and commande) \
        else None
    return r


def reset_puce(ser, attente):
    """Reset de la puce par impulsion RTS, EN GARDANT LE PORT OUVERT.

    ⚠️ MESURÉ le 2026-08-15, et ça corrige une croyance du README : **ce
    reset-là ne fait PAS tomber l'attachement usbipd.** Le bouton RESET et la
    commande console `reboot` le font (`reboot` passe par `esp_restart()`, qui
    réinitialise le périphérique USB, donc l'USB se ré-énumère) ; une impulsion
    RTS, non. Le même descripteur continue de servir, et on capture donc le
    bandeau de boot DEPUIS SA PREMIÈRE LIGNE.

    À quoi ça sert, concrètement : `idf.py flash` puis une écoute rate le
    bandeau à tous les coups — le temps de lancer l'écoute, `app_main` est déjà
    passé. Or c'est dans ce bandeau que vivent `SPI Flash Size : 16MB` (la
    preuve d'AC2), la table de partitions et l'init PSRAM. Sans ce geste, on ne
    peut pas les relever sans reflasher.

    ⛔ DTR est laissé BAS, délibérément : sur cette carte DTR pilote GPIO0. Le
    lever pendant le reset ferait entrer la puce en MODE DOWNLOAD — c'est-à-dire
    exactement la panne « carte muette » qu'on passe son temps à éviter.
    """
    ser.dtr = False
    ser.rts = True
    time.sleep(0.25)
    ser.rts = False
    fin = time.monotonic() + attente
    buf = bytearray()
    while time.monotonic() < fin:
        d = ser.read(ser.in_waiting or 1)
        if d:
            buf.extend(d)
    return buf.decode("utf-8", "replace")


def reveiller(ser):
    """Un \\n à vide : confirme que la console répond AVANT de mesurer quoi que
    ce soit. Une carte en mode download accepte l'écriture et ne rend rien."""
    ser.reset_input_buffer()
    ser.write(b"\n")
    ser.flush()
    _, invite = lire_jusqu_invite(ser, 3.0)
    if not invite:
        raise ConsoleErreur(
            "le port s'ouvre mais la console ne rend pas l'invite en 3 s.\n"
            "  C'est le symptôme « carte muette » : l'application ne tourne pas,\n"
            "  la carte est probablement restée en mode download.\n"
            "  ⇒ recette du README § « La carte est muette ? » — et ATTENTION,\n"
            "    `--after hard_reset` NE SUFFIT PAS, il faut `watchdog_reset`.")


_MOTIFS_JAMAIS_TOLERES = ("REPL: commande inconnue", "REPL: erreur interne")


def refus_tolere(commande, liste, motifs=None):
    """AC1.3 — `--refus-tolere` agit **commande par commande**.

    `*` couvre tout ; sinon la tolérance vaut pour la commande EXACTE ou pour
    tout ce qui la prolonge (`i2c` couvre `i2c 0x23`). ⛔ Un préfixe libre
    (`i` couvrant `i2c`) serait une porte ouverte : la frontière est l'espace.

    🔴 dn4-23 / REVUE DU 2026-08-31 — **DEUX MOTIFS NE SE TOLÈRENT JAMAIS**, quoi
       qu'on tape. Le drapeau est documenté pour « un scan I²C sur une adresse
       absente », c'est-à-dire pour un échec ATTENDU de la commande. Il avalait
       aussi `Unrecognized command` (**la commande n'existe pas dans ce
       firmware** — le contraire d'un échec attendu : la mesure n'a pas eu lieu)
       et `Internal error:` (la carte n'a pas pu exécuter). Ces deux-là ne sont
       pas l'objet d'une mesure, ils sont son ABSENCE.
    """
    for nom, _ligne in (motifs or []):
        if nom in _MOTIFS_JAMAIS_TOLERES:
            return False
    for motif in liste or []:
        if motif == "*" or commande == motif or \
           (commande or "").startswith(motif + " "):
            return True
    return False


def imprimer_completude(r):
    """AC2.2 — LE COMPTEUR EST **LU**, ET LE DÉSACCORD EST **CRIÉ**."""
    c = r.get("completude")
    if not c:
        return
    if c["etat"] == "OK" and c["annonce"]:
        # ⛔ `OK` NE VEUT PAS DIRE « RIEN N'A ÉTÉ PERDU ». Voir l'angle mort
        #    écrit dans `completude()` : l'invariant est une somme signée.
        print("✅ compteur : %d annoncées, %d reçues.\n"
              "   ⚠️ `OK` = les DEUX COMPTES S'ACCORDENT, ⛔ pas « rien n'a été\n"
              "      perdu » : une ligne perdue et un log asynchrone arrivés dans\n"
              "      la MÊME capture s'annulent. Cet instrument ne sait pas les\n"
              "      distinguer, et il le dit plutôt que de le taire."
              % (c["annonce"], c["recu"]))
    if c["coupees_avant_echo"]:
        # AC2.3 — le SECOND mécanisme candidat, celui que le compteur ne voit pas.
        print("⚠️ `nettoyer()` a coupé %d ligne(s) AVANT l'écho de la commande.\n"
              "   ⛔ Ce n'est pas couvert par le compteur : ces lignes-là sont\n"
              "   jetées AVANT d'être comptées. En régime sain il y en a ZÉRO —\n"
              "   `reset_input_buffer()` vient de vider le tampon."
              % c["coupees_avant_echo"])
    if not c["echo_vu"]:
        print("⚠️ ÉCHO INTROUVABLE dans le tampon brut : soit la sortie ci-dessus\n"
              "   contient encore l'écho, soit l'écho lui-même a été PERDU.\n"
              "   ⛔ Ne pas lire cette capture comme une capture propre.")
    e = c["etat"]
    if e == "OK":
        return
    if e == "SANS_COMPTEUR":
        # 🔴 REVUE DU 2026-08-31 — CET ÉTAT A **DEUX** CAUSES, ET L'UNE D'ELLES
        #    EST UNE PERTE. Perdre la ligne de compteur ELLE-MÊME (perte en
        #    queue d'UNE ligne) faisait tomber ici — un ⚠️, rc 0 — là où toute
        #    autre perte d'une seule ligne arme `PERTE` et rc 1. La perte en
        #    queue était donc MOINS CHÈRE que la perte en tête. On ne peut pas
        #    les distinguer depuis l'hôte : on les NOMME toutes les deux, et
        #    `--exiger-compteur` arme le rc pour les campagnes qui savent que le
        #    firmware en imprime un.
        print("⚠️ AUCUN compteur de lignes dans cette sortie (%d ligne(s) reçues).\n"
              "   ⛔ Ce n'est PAS « 0 perte », c'est « ON NE SAIT PAS ». DEUX causes,\n"
              "   et l'une est une PERTE :\n"
              "     · firmware antérieur à dn4-23, ou commande hors `k_cmds[]` ;\n"
              "     · 🔴 la ligne de compteur elle-même a été PERDUE (perte en\n"
              "       queue d'UNE ligne).\n"
              "   ⇒ `--exiger-compteur` fait de cet état un ÉCHEC (rc 1)."
              % c["recu"])
    elif e == "PERTE":
        print("🔴 PERTE DE LIGNES : la carte en annonce %d, %d sont arrivées\n"
              "   (%d MANQUENT). ⛔ Ne rien conclure de cette capture — une ligne\n"
              "   perdue produit « l'adresse 0x23 n'est pas là » sur un capteur\n"
              "   QUI RÉPOND. ⇒ RE-JOUER.\n"
              "   ⚠️ La cause reste NON INSTRUITE (2 A/B, 30 passes sans\n"
              "      reproduction) : cet instrument REND LA PERTE VISIBLE, il ne\n"
              "      la supprime pas."
              % (c["annonce"], c["recu"], c["annonce"] - c["recu"]))
    elif e == "LIGNES_ETRANGERES":
        print("⚠️ %d ligne(s) ÉTRANGÈRE(S) : la carte en annonce %d, %d sont\n"
              "   arrivées. ⛔ Ce n'est PAS une perte — `ESP_LOGx` d'une autre\n"
              "   tâche ne passe pas par le compteur. C'est un log ASYNCHRONE\n"
              "   tombé pendant la commande, et il est dans la capture."
              % (c["recu"] - c["annonce"], c["annonce"], c["recu"]))
    elif e == "COMPTE_NON_FIABLE":
        print("⚠️ LA CARTE DÉCLARE SON PROPRE COMPTE INVALIDE (sortie tronquée,\n"
              "   RAM insuffisante pour une ligne longue). ⛔ L'invariant ne\n"
              "   s'applique pas à cette capture.")


# ═══════════════════════════════════════════════════════════════════════════
# dn4-23 / AC1.5 — LE TÉMOIN NÉGATIF, JOUABLE **SANS CARTE**
# ═══════════════════════════════════════════════════════════════════════════
#
# 🔴 *« Une gate qu'aucun test n'a vue échouer est décorative »* (dn4-13/AC7.5).
#    Chaque motif est éprouvé sur une sortie **FABRIQUÉE**, et le témoin porte
#    aussi ses **contre-épreuves** : des sorties propres qui NE DOIVENT PAS
#    rougir. ⛔ Sans elles, un `chercher_refus` qui rendrait toujours vrai
#    passerait ce témoin haut la main.
# 🔴 CORRIGÉ PAR LA REVUE DU 2026-08-31 — **DEUX DES CINQ MOTIFS N'ÉTAIENT
#    JAMAIS EXERCÉS**, dont celui qui est le SEUL détecteur d'un refus muet.
#    Les témoins REPL portaient `0x102 (ESP_ERR_INVALID_ARG)` et
#    `Internal error: ESP_ERR_NO_MEM` : tous deux contiennent `ESP_ERR_`, qui
#    est PLUS HAUT dans `MOTIFS_REFUS`, et la boucle `break` au premier motif
#    reconnu. Le témoin n'assertant que `len(vus) == 1`, il passait quel que
#    soit le motif qui avait tiré. **Reproduit** : typo les deux regexes REPL en
#    `Commmand` / `Internnal` ⇒ `--temoin-negatif` rendait toujours
#    `BILAN : 31 OK, 0 KO`.
# ⇒ Chaque témoin NOMME désormais le motif qu'il doit déclencher, et les cas
#   REPL sont écrits SANS `ESP_ERR_` — c'est-à-dire tels qu'ils arrivent quand
#   une commande rend non zéro **sans rien imprimer**, le cas que le README met
#   en avant et que rien ne gardait.
_TEMOINS_ROUGES = [
    ("refusé : ESP_ERR_INVALID_ARG", "refus firmware",
     "anim on 10 — le stimulus n'a JAMAIS tourné (mesuré, 2 fenêtres de 90 s)"),
    ("refusé : ESP_ERR_INVALID_STATE", "refus firmware",
     "flash on — la fenêtre a mesuré un stimulus qu'elle croyait avoir démarré"),
    ("Unrecognized command", "REPL: commande inconnue",
     "REPL ESP-IDF — commande inconnue, AUCUN message de nous"),
    ("Command returned non-zero error code: 0x1 (ERROR)",
     "REPL: code de retour non nul",
     "REPL — un `return 1;` NU, sans ESP_ERR_ : le seul détecteur"),
    ("Command returned non-zero error code: 0x102 (ESP_ERR_INVALID_ARG)",
     "ESP_ERR_",
     "la même ligne AVEC ESP_ERR_ : un seul refus, sous le 1er motif"),
    ("Internal error: la console n'a pas pu executer",
     "REPL: erreur interne",
     "REPL — quatrième cas de `esp_console_common.c`, sans ESP_ERR_"),
    ("refuse : entre 1 et 2000 ms", "refus firmware",
     "la convention SANS accent, elle existe aussi"),
    ("REFUSE : index hors plage (0..5) OU couleur > 0xFFFFFF.", "refus firmware",
     "la convention en CAPITALES, `widget couleur`"),
    ("valeurs refusées : hors bornes", "refus firmware",
     "🔴 REVUE — le PLURIEL, que l'alternance ne couvrait pas"),
    ("🔴 LE TEXTE MESURE N'EST PAS CELUI QUI A ETE TAPE — DRAPEAU LEVE.",
     "carte : verdict NON CRÉDIBLE",
     "🔴 REVUE — `widget largeur` publiait 63 px avec rc 0"),
    ("   ⛔ NE PAS CONCLURE SUR CE CHIFFRE. ⇒ `widget largeur mur`,",
     "carte : verdict NON CRÉDIBLE",
     "🔴 REVUE — la carte écrit « ne concluez pas » et rendait 0"),
    ("🔴 TEMOIN POSITIF EN ECHEC : expander KO · tactile OK.",
     "carte : verdict NON CRÉDIBLE",
     "🔴 REVUE — le scan I²C se déclare non crédible et rend 0"),
]
_TEMOINS_VERTS = [
    ("usage : widget opa <0..255>  (refuse hors bornes, jamais ecrete)",
     "une phrase PÉDAGOGIQUE — « refuse » SANS « : ». ⛔ Ce n'est pas un refus."),
    ("piste de jauge = 0x141820 — SCENE RECONSTRUITE",
     "un succès ordinaire"),
    ("⚠️ Ce refus REMPLACE un blocage silencieux.",
     "le mot « refus » dans une explication, sans « : »"),
]


def temoin_negatif():
    ok = ko = 0

    def ctrl(bon, libelle, detail=""):
        nonlocal ok, ko
        if bon:
            ok += 1
            print("  [OK ] %-56s %s" % (libelle, detail))
        else:
            ko += 1
            print("  [KO ] %-56s %s" % (libelle, detail))

    print("=" * 78)
    print("dn4-23 / AC1.5 + AC2 + AC7 — LES TÉMOINS, JOUÉS SANS CARTE")
    print("=" * 78)

    print("\n── AC1 : chaque motif de refus fait ROUGIR ────────────────────")
    for ligne, motif_attendu, pourquoi in _TEMOINS_ROUGES:
        vus = chercher_refus("bla bla\n" + ligne + "\nbla")
        # ⛔ ON N'ASSERTE PLUS SEULEMENT LE COMPTE : un témoin qui ne vérifie que
        #   `len(vus) == 1` passe quel que soit le motif qui a tiré, et laisse
        #   deux regexes mourir sans bruit. On exige LE MOTIF ATTENDU.
        ctrl(len(vus) == 1 and vus[0][0] == motif_attendu,
             "ROUGE : %s" % ligne[:44],
             "%s · %s" % (motif_attendu[:22], pourquoi[:24]))
    print("\n── AC1 : les CONTRE-ÉPREUVES ne rougissent PAS ────────────────")
    for ligne, pourquoi in _TEMOINS_VERTS:
        vus = chercher_refus(ligne)
        ctrl(not vus, "VERT  : %s" % ligne[:44], pourquoi[:28])
    ctrl(len(chercher_refus("refusé : ESP_ERR_INVALID_ARG")) == 1,
         "une ligne à DEUX motifs compte pour UN refus", "⛔ pas deux")

    print("\n── AC1 : le refus est LU par `envoyer()`, pas seulement trouvé ─")
    brut = ("desknode> anim on 10\r\nrefusé : ESP_ERR_INVALID_ARG\r\n"
            "--- fin : 1 lignes emises ---\r\ndesknode> ")
    r = _resultat("anim on 10", brut, nettoyer(brut, "anim on 10"), True)
    ctrl(r["refus"] == "refusé : ESP_ERR_INVALID_ARG",
         "`_resultat` pose le MOTIF EXACT dans `refus`", repr(r["refus"])[:26])
    ctrl(r["completude"]["etat"] == "OK",
         "…et l'invariant de complétude est SATISFAIT", "1 annoncée, 1 reçue")

    print("\n── AC1.3 : `--refus-tolere` agit COMMANDE PAR COMMANDE ────────")
    ctrl(refus_tolere("i2c 0x23", ["i2c"]), "`i2c` couvre `i2c 0x23`", "")
    ctrl(not refus_tolere("i2connerie", ["i2c"]),
         "…et NE couvre PAS `i2connerie`", "la frontière est l'espace")
    ctrl(not refus_tolere("anim on 10", ["i2c"]),
         "…ni une autre commande", "⛔ jamais global par accident")
    ctrl(refus_tolere("n'importe quoi", ["*"]), "`*` couvre tout", "explicite")
    ctrl(not refus_tolere("anim on 10", []), "et la liste VIDE ne tolère rien",
         "⛔ jamais par défaut")

    print("\n── AC2 : le compteur de lignes ATTRAPE une perte ──────────────")
    plein = ("desknode> i2c scan\r\n" + "".join("0x%02X vue\r\n" % a
                                                for a in range(0x20, 0x26))
             + "--- fin : 6 lignes emises ---\r\ndesknode> ")
    ampute = plein.replace("0x5D vue\r\n", "").replace("0x23 vue\r\n", "")
    c = completude(plein, "i2c scan")
    ctrl(c["etat"] == "OK", "capture COMPLÈTE ⇒ OK", "%d/%d" % (c["recu"], c["annonce"]))
    c = completude(ampute, "i2c scan")
    ctrl(c["etat"] == "PERTE", "capture AMPUTÉE ⇒ 🔴 PERTE",
         "%d reçues / %d annoncées" % (c["recu"], c["annonce"]))
    intrus = plein.replace("0x22 vue\r\n", "0x22 vue\r\nI (123) tache: bla\r\n")
    c = completude(intrus, "i2c scan")
    ctrl(c["etat"] == "LIGNES_ETRANGERES",
         "log ASYNCHRONE ⇒ ⚠️ étrangères, ⛔ pas une perte",
         "%d/%d" % (c["recu"], c["annonce"]))
    c = completude(plein.replace("--- fin : 6 lignes emises ---\r\n", ""),
                   "i2c scan")
    ctrl(c["etat"] == "SANS_COMPTEUR",
         "firmware SANS compteur ⇒ « on ne sait pas »", "⛔ pas « 0 perte »")
    c = completude(plein.replace("emises ---",
                                 "emises (COMPTE NON FIABLE : sortie tronquee) ---"),
                   "i2c scan")
    ctrl(c["etat"] == "COMPTE_NON_FIABLE",
         "la carte déclare son compte invalide ⇒ dit", "")
    c = completude("bruit residuel\r\n" + plein, "i2c scan")
    ctrl(c["coupees_avant_echo"] == 1,
         "AC2.3 : ce que `nettoyer()` coupe AVANT l'écho est VU", "1 ligne")

    print("\n── AC7 : la latence, sa dispersion, et le REFUS du delta ──────")
    l = lire_latence("latence acceptation->label : n=225 · min 4 ms · "
                     "moy 260 ms · max 316 ms")
    ctrl(l == (225, 4, 260, 316), "la ligne de `pc` est lue EXACTEMENT", str(l))
    ctrl(lire_latence("latence acceptation->label : aucune poussee encore") is None,
         "…et « aucune poussee » ne fabrique PAS un nombre",
         "⛔ gratter au grep fabrique des nombres")
    mesure = [86, 138, 220, 86, 260]  # `fd959f2`, MESURÉ — ⛔ pas inventé
    d = dispersion(mesure)
    ctrl(d["etendue"] == 174 and abs(d["facteur"] - 260 / 86) < 1e-9,
         "la dispersion MESURÉE est reproduite", "facteur %.2f" % d["facteur"])
    rec, _ = verdict_delta(dispersion([120]), dispersion(mesure))
    ctrl(not rec, "🔴 delta sur UNE FENÊTRE ⇒ REFUSÉ", "AC7.2")
    # 🔴 ET LE CAS QUE LA RÈGLE DE CHEVAUCHEMENT NE RATTRAPE PAS — trouvé par
    #    le mutant `LATENCE_FENETRES_MIN = 1` de la gate d'AC8, qui passait
    #    VERT. Une fenêtre unique BIEN LOIN de l'autre relevé aurait été
    #    publiée : les étendues sont disjointes, donc seul le PLANCHER de
    #    fenêtres peut la refuser. ⛔ Un témoin qui n'exerce qu'un chemin
    #    laisse l'autre sans garde.
    rec, _ = verdict_delta(dispersion([10]), dispersion([300, 310, 305, 299]))
    ctrl(not rec,
         "🔴 …même DISJOINTE : une fenêtre unique reste REFUSÉE",
         "⛔ le chevauchement ne la rattrape pas")
    rec, _ = verdict_delta(dispersion(mesure), dispersion([90, 250, 130]))
    ctrl(not rec, "🔴 étendues qui SE CHEVAUCHENT ⇒ REFUSÉ", "dans le bruit")
    rec, _ = verdict_delta(dispersion([10, 12, 11, 13, 10]),
                           dispersion([300, 310, 305, 299, 302]))
    ctrl(rec, "✅ étendues DISJOINTES ⇒ recevable", "et la dispersion est publiée")

    print("\n── REVUE 2026-08-31 : les trous que la revue a trouvés ────────")
    # (1) LA DÉDUPLICATION DÉGONFLAIT — six refus identiques n'en rendaient qu'UN.
    six = "\n".join(["ECHEC (ESP_ERR_NOT_FOUND)"] * 6)
    ctrl(len(chercher_refus(six)) == 6,
         "six refus IDENTIQUES comptent pour SIX", "⛔ pas un seul")
    ctrl(len(chercher_refus("refusé : ESP_ERR_INVALID_ARG")) == 1,
         "…et DEUX motifs sur UNE ligne comptent pour UN", "⛔ pas deux")
    # (2) LE DÉCOUPEUR S'ALIGNE SUR CE QUE LA CARTE COMPTE (`\n` SEUL).
    ctrl(len(_lignes("a\rb\nc")) == 2,
         "un `\\r` NE FABRIQUE PLUS une ligne", "la carte ne compte que `\\n`")
    ctrl(len("a\rb\nc".splitlines()) == 3,
         "…et c'est bien ce que `splitlines()` faisait", "3 lignes, ⛔ 2")
    # (3) `--no-wait` NE SE DÉNONCE PLUS LUI-MÊME.
    brut = "desknode> pc $DN,3,1,0,cpu,ESP_ERR_X*00\r\nOK\r\n"
    r = _resultat("pc $DN,3,1,0,cpu,ESP_ERR_X*00", brut,
                  nettoyer(brut, "pc $DN,3,1,0,cpu,ESP_ERR_X*00"), None)
    ctrl(r["refus"] is None,
         "une commande dont le TEXTE porte un motif ne s'accuse pas",
         "⛔ l'écho n'est plus scanné")
    # (4) DEUX MOTIFS NE SE TOLÈRENT JAMAIS — la mesure n'a pas eu lieu.
    ctrl(not refus_tolere("i2c scan", ["*"],
                          [("REPL: commande inconnue", "Unrecognized command")]),
         "`--refus-tolere *` n'avale PAS « commande inconnue »",
         "⛔ c'est l'ABSENCE de mesure")
    ctrl(refus_tolere("i2c scan", ["i2c"],
                      [("ESP_ERR_", "ECHEC (ESP_ERR_NOT_FOUND)")]),
         "…mais il avale bien l'échec ATTENDU d'un scan", "AC1.3 intact")
    # (5) DEUX FENÊTRES DE LATENCE DANS UNE CAPTURE ⇒ ON REFUSE DE CHOISIR.
    deux = ("latence acceptation->label : n=10 · min 4 ms · moy 12 ms · max 20 ms\n"
            "latence acceptation->label : n=11 · min 5 ms · moy 99 ms · max 120 ms")
    try:
        lire_latence(deux)
        ambigu = False
    except LatenceAmbigue:
        ambigu = True
    ctrl(ambigu, "🔴 DEUX lignes de latence ⇒ REFUS, ⛔ pas « la première »",
         "une mesure périmée publiée comme fraîche")
    # (6) L'ANGLE MORT DE `OK` EST **IMPRIMÉ**, ⛔ pas seulement commenté.
    #     ⚠️ Un commentaire ne retient personne — c'est écrit trois fois dans ce
    #        dépôt. On CAPTURE la sortie et on vérifie qu'elle porte la phrase.
    tampon = io.StringIO()
    brut_ok = ("desknode> cfg\r\nligne A\r\n--- fin : 1 lignes emises ---\r\n"
               "desknode> ")
    with contextlib.redirect_stdout(tampon):
        imprimer_completude(_resultat("cfg", brut_ok,
                                      nettoyer(brut_ok, "cfg"), True))
    vu = tampon.getvalue()
    ctrl("s'annulent" in vu and "OK" in vu,
         "un compteur `OK` IMPRIME son angle mort",
         "⛔ « OK » n'est pas « rien n'a été perdu »")

    # (7) L'ÉTENDUE OBSERVÉE N'EST PLUS CELLE DES MOYENNES.
    d = dispersion([10, 12], bornes=[(5, 18), (6, 20)])
    ctrl(d["min"] == 10 and d["observe_min"] == 5 and d["observe_max"] == 20,
         "les moyennes [10;12] ne masquent plus l'observé [5;20]",
         "6× plus étroit")

    print("\n" + "=" * 78)
    print("⛔ CE QUE CE TÉMOIN NE PROUVE PAS : que la carte a raison. Il prouve "
          "que\n   L'INSTRUMENT ne peut plus conclure sur du vide. Les constats "
          "de la\n   carte (perte réelle attrapée, dispersion réelle) se tirent "
          "EN SÉANCE.")
    if ko == 0:
        print("BILAN : %d OK, 0 KO" % ok)
        return 0
    print("BILAN : %d OK, %d KO" % (ok, ko))
    return 1


def main():
    p = argparse.ArgumentParser(
        description="Pilote la console de mesure de firmware/desknode.")
    p.add_argument("commandes", nargs="*", help="commandes à envoyer, dans l'ordre")
    p.add_argument("--port", default=DEFAULT_PORT)
    p.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    p.add_argument("--timeout", type=float, default=20.0,
                   help="attente de l'invite, par commande (défaut 20 s)")
    p.add_argument("--listen", type=float, metavar="N",
                   help="écoute passive N secondes, n'envoie RIEN")
    p.add_argument("--reset", action="store_true",
                   help="impulsion RTS = reset de puce SANS fermer le port "
                        "(l'attachement usbipd survit — mesuré), puis capture "
                        "du bandeau de boot depuis sa première ligne")
    p.add_argument("--reset-wait", type=float, default=10.0, metavar="N",
                   help="durée de capture après le reset (défaut 10 s)")
    p.add_argument("--no-wait", action="store_true",
                   help="ne pas attendre l'invite (commandes qui ne rendent pas "
                        "la main, ex. `tear on`)")
    p.add_argument("--json", action="store_true", help="sortie machine")
    p.add_argument("--capture", metavar="FICHIER",
                   help="append du flux brut, horodaté")
    p.add_argument("--force", action="store_true",
                   help="ouvrir même si un autre processus tient le port "
                        "(⚠️ les octets se partagent : mesures tronquées)")
    # ── dn4-23 / AC1.3 — LE DÉSARMEMENT EST **EXPLICITE**, ⛔ JAMAIS PAR DÉFAUT
    p.add_argument("--refus-tolere", action="append", default=[],
                   metavar="COMMANDE",
                   help="ne pas armer le code de retour sur le refus de CETTE "
                        "commande (répétable ; `*` = toutes). Pour les campagnes "
                        "où le refus EST l'objet de la mesure — un scan I²C sur "
                        "une adresse absente, par exemple. ⛔ Le refus reste "
                        "IMPRIMÉ : on désarme le rc, jamais l'instrument.")
    p.add_argument("--exiger-compteur", action="store_true",
                   help="dn4-23/REVUE — faire de `SANS_COMPTEUR` un ÉCHEC (rc 1). "
                        "Cet état a DEUX causes et l'une est une perte (la ligne "
                        "de compteur elle-même). ⛔ Pas par défaut : un firmware "
                        "antérieur à dn4-23 n'en imprime pas.")
    p.add_argument("--temoin-negatif", action="store_true",
                   help="dn4-23/AC1.5 — joue les témoins SANS CARTE : des "
                        "sorties FABRIQUÉES qui DOIVENT faire rougir le "
                        "verdict. ⛔ Une gate qu'aucun test n'a vue échouer est "
                        "décorative.")
    args = p.parse_args()

    if args.temoin_negatif:
        return temoin_negatif()

    try:
        ser = ouvrir(args.port, args.baud, ignorer_detenteurs=args.force)
    except ConsoleErreur as e:
        sys.stderr.write(f"\n✗ {e}\n")
        return 1

    # 🔴 REVUE DU 2026-08-31 — `--listen 0` ÉTAIT **FALSY**, donc la branche
    #    `elif args.commandes` était prise et la commande ÉTAIT ENVOYÉE sur un
    #    tir explicitement demandé silencieux. Et `--listen 15 "cfg" "mem"`
    #    JETAIT les commandes sans un mot, rc 0 — une campagne mesurait
    #    silencieusement rien.
    ecoute = args.listen is not None
    if ecoute and args.commandes:
        sys.stderr.write(
            "\n✗ `--listen` et des commandes en même temps : ce pilote ne peut\n"
            "  pas faire les deux, et les JETER SANS RIEN DIRE est exactement ce\n"
            "  que cette story supprime. ⇒ deux invocations.\n"
            "  commandes ignorées : %s\n" % ", ".join(args.commandes))
        ser.close()
        return 2

    resultats = []
    code = 0
    # 🔴 REVUE DU 2026-08-31 — UNE EXCEPTION SÉRIE JETAIT TOUTE LA CAMPAGNE DÉJÀ
    #    CAPTURÉE : le `finally` fermait le port et l'exception passait PAR-DESSUS
    #    l'écriture de `--capture` et la boucle d'impression. Une ré-énumération
    #    USB (un `reboot` dans la liste, un coup dans le câble) ne laissait qu'une
    #    trace. Idem pour le `return 1` du handler de `reveiller()`, qui jetait le
    #    bandeau de boot QUI VENAIT D'ÊTRE CAPTURÉ — le seul diagnostic de
    #    « carte muette ». ⇒ ce qui est capturé est ÉCRIT, quoi qu'il arrive.
    incident = None
    try:
        if args.reset:
            brut = reset_puce(ser, args.reset_wait)
            resultats.append(_resultat("(reset RTS + bandeau de boot)",
                                       brut, brut.strip(), None,
                                       compter=False))
        if args.reset and resultats[-1]["refus"]:
            code = 1
        if ecoute:
            brut, _ = lire_jusqu_invite(ser, args.listen)
            resultats.append(_resultat("(écoute passive)", brut,
                                       brut.strip(), None, compter=False))
            if resultats[-1]["refus"]:
                code = 1
        elif args.commandes:
            try:
                reveiller(ser)
            except ConsoleErreur as e:
                incident = e
                args.commandes = []
            for cmd in args.commandes:
                r = envoyer(ser, cmd, args.timeout, not args.no_wait)
                resultats.append(r)
                if r["invite_rendue"] is False:
                    code = 1
                # 🔴 AC1.3 — UN REFUS VAUT UNE INVITE NON RENDUE. Jusqu'ici le
                #    SEUL signal d'échec de ce pilote était `invite_rendue is
                #    False` : une commande refusée à l'écran rendait 0.
                if r["refus"] and not refus_tolere(
                        cmd, args.refus_tolere,
                        [(m["motif"], m["ligne"])
                         for m in r["refus_motifs"]]):
                    code = 1
                # 🔴 AC2.2 — ET UNE PERTE DE LIGNES AUSSI. ⛔ Seule la PERTE arme
                #    le rc : des lignes ÉTRANGÈRES (log asynchrone) sont un fait
                #    normal de cette carte, et crier dessus apprendrait à
                #    ignorer le cri.
                if r["completude"] and r["completude"]["etat"] == "PERTE":
                    code = 1
                # 🔴 REVUE DU 2026-08-31 — TROIS ÉTATS IMPRIMAIENT « NE CONCLUEZ
                #    PAS » ET RENDAIENT 0. Un instrument qui écrit « ⇒ RE-JOUER »
                #    et sort en 0 dit deux choses opposées ; la seconde est celle
                #    que lit une campagne.
                if r["completude"] and \
                        r["completude"]["etat"] == "COMPTE_NON_FIABLE":
                    code = 1
                if args.exiger_compteur and r["completude"] and \
                        r["completude"]["etat"] == "SANS_COMPTEUR":
                    code = 1
                if not (r["sortie"] or "").strip():
                    code = 1
    except OSError as e:
        # ⚠️ `serial.SerialException` DÉRIVE de `OSError` (pyserial ≥ 3.0), et
        #    `serial` n'est importé que dans `ouvrir()` : attraper `OSError`
        #    couvre les deux sans dépendre d'un import de portée.
        incident = e
    finally:
        ser.close()

    if args.capture:
        with open(args.capture, "a", encoding="utf-8") as f:
            for r in resultats:
                f.write(f"\n===== {r['commande'] or '(écoute)'} =====\n")
                f.write(r["brut"])

    if args.json:
        print(json.dumps(
            [{k: v for k, v in r.items() if k != "brut"} for r in resultats],
            ensure_ascii=False, indent=2))
    else:
        for r in resultats:
            if r["commande"]:
                print(f"\n$ {r['commande']}")
            # 🔴 AC1.4 — LE REFUS EST IMPRIMÉ **EN TÊTE**, ⛔ PAS NOYÉ. Un
            #    opérateur qui relit une capture doit le voir sans le chercher :
            #    les deux refus de la mesure d'origine étaient bel et bien
            #    À L'ÉCRAN, au milieu de 90 s de sortie.
            for m in r.get("refus_motifs") or []:
                tol = refus_tolere(
                    r["commande"], args.refus_tolere,
                    [(x["motif"], x["ligne"])
                     for x in (r.get("refus_motifs") or [])])
                print("🔴 REFUS [%s] : %s%s"
                      % (m["motif"], m["ligne"],
                         "   (toléré : --refus-tolere)" if tol else ""))
            print(r["sortie"])
            if r["commande"] and not (r["sortie"] or "").strip():
                print(VIDE_NE_PROUVE_RIEN)
            imprimer_completude(r)
            if r["invite_rendue"] is False:
                print(f"⚠️ invite NON rendue en {args.timeout:.0f} s — "
                      "commande longue (augmenter --timeout) ou console bloquée.")
    if incident is not None:
        sys.stderr.write(
            "\n✗ %s\n  ⚠️ Ce qui avait été capturé AVANT l'incident est ci-dessus,\n"
            "     et dans `--capture` s'il était demandé — ⛔ plus jeté.\n"
            % incident)
        return 1
    return code


if __name__ == "__main__":
    raise SystemExit(main())

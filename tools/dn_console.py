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
import glob
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
#    la NÔTRE (66 sites dans `dn_console.c`), mais une commande peut rendre non
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
    #    Vérifié : les 66 refus réels portent tous le « : ».
    ("refus firmware", re.compile(r"(?i)\brefus(?:é|e|ée|ee)\s*:")),
    ("ESP_ERR_", re.compile(r"\bESP_ERR_[A-Z0-9_]+")),
    ("REPL: commande inconnue", re.compile(r"Unrecognized command")),
    ("REPL: code de retour non nul",
     re.compile(r"Command returned non-zero error code")),
    ("REPL: erreur interne", re.compile(r"Internal error:")),
)


def chercher_refus(texte):
    """Rend la liste des `(motif, ligne)` de refus trouvés dans `texte`.

    🔴 FONCTION **PURE**, ET C'EST LA CONDITION DU TÉMOIN NÉGATIF. Le verdict
       d'AC1 se joue donc **sans carte**, sur des sorties FABRIQUÉES
       (`--temoin-negatif`). *« Une gate qu'aucun test n'a vue échouer est
       décorative »* — dn4-13 / AC7.5.
    ⚠️ Une même ligne peut porter deux motifs (« refusé : ESP_ERR_… ») : elle
       n'est comptée qu'UNE fois, sous le premier motif qui la reconnaît. Un
       compte gonflé ferait croire à deux refus là où il y en a un.
    """
    vus = []
    deja = set()
    for ligne in texte.splitlines():
        for nom, rx in MOTIFS_REFUS:
            if rx.search(ligne):
                if ligne not in deja:
                    deja.add(ligne)
                    vus.append((nom, ligne.strip()))
                break
    return vus


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
    lignes = brut.splitlines()
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


def lire_latence(sortie):
    """Extrait `(n, min_ms, moy_ms, max_ms)` d'une sortie de `pc`, ou None.

    ⚠️ **La console de ce dépôt est RÉDIGÉE POUR UN HUMAIN** — mots-clés répétés
       dans la prose, chiffres au milieu des phrases. *La gratter au `grep`
       fabrique des nombres plausibles.* ⇒ le motif est ANCRÉ sur la ligne
       entière et sur ses quatre champs, et il est éprouvé sur une ligne
       FABRIQUÉE par `--temoin-negatif` avant d'être cru sur une ligne réelle.
    """
    m = RE_LATENCE.search(sortie)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))


def dispersion(moyennes):
    """La dispersion d'une série de moyennes de fenêtres. ⛔ Jamais une moyenne
    seule : c'est exactement ce qui a fait publier un critère de validité qu'il
    a fallu rétracter devant l'owner."""
    if not moyennes:
        return None
    lo, hi = min(moyennes), max(moyennes)
    return {
        "n_fenetres": len(moyennes),
        "min": lo,
        "max": hi,
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
    chevauche = not (a["max"] < b["min"] or b["max"] < a["min"])
    if chevauche:
        lignes.append(
            "🔴 REFUS : les deux étendues SE CHEVAUCHENT — A [%d ; %d] ms,\n"
            "   B [%d ; %d] ms. L'écart des médianes (%.1f ms) est DANS le bruit\n"
            "   du même firmware. ⛔ Aucun delta n'est publiable."
            % (a["min"], a["max"], b["min"], b["max"],
               b["mediane"] - a["mediane"]))
        return False, lignes
    lignes.append(
        "✅ Les étendues sont DISJOINTES — A [%d ; %d] ms, B [%d ; %d] ms.\n"
        "   Écart des médianes : %+.1f ms.\n"
        "   ⚠️ Recevable NE VEUT PAS DIRE expliqué : la variance de cet\n"
        "      instrument n'est TOUJOURS PAS isolée. Deux hypothèses sont\n"
        "      RÉFUTÉES (fragmentation du tas LVGL · compteurs de liaison) et le\n"
        "      champ reste OUVERT."
        % (a["min"], a["max"], b["min"], b["max"], b["mediane"] - a["mediane"]))
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
        time.sleep(min(timeout, 2.0))
        brut = ser.read(ser.in_waiting or 1).decode("utf-8", "replace")
        return _resultat(commande, brut, brut.strip(), None)
    brut, invite = lire_jusqu_invite(ser, timeout)
    return _resultat(commande, brut, nettoyer(brut, commande), invite)


def _resultat(commande, brut, sortie, invite):
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
    hors_echo = "\n".join(
        l for l in brut.splitlines() if not l.strip().endswith(commande))
    vus = chercher_refus(sortie)
    deja = {l for _, l in vus}
    for nom, ligne in chercher_refus(hors_echo):
        if ligne not in deja:
            vus.append((nom, ligne))
            deja.add(ligne)
    r = {"commande": commande, "sortie": sortie, "invite_rendue": invite,
         "brut": brut,
         "refus": vus[0][1] if vus else None,
         "refus_motifs": [{"motif": n, "ligne": l} for n, l in vus]}
    r["completude"] = completude(brut, commande) if commande else None
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


def refus_tolere(commande, liste):
    """AC1.3 — `--refus-tolere` agit **commande par commande**.

    `*` couvre tout ; sinon la tolérance vaut pour la commande EXACTE ou pour
    tout ce qui la prolonge (`i2c` couvre `i2c 0x23`). ⛔ Un préfixe libre
    (`i` couvrant `i2c`) serait une porte ouverte : la frontière est l'espace.
    """
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
        print("⚠️ AUCUN compteur de lignes dans cette sortie (%d ligne(s) reçues).\n"
              "   ⛔ Ce n'est PAS « 0 perte », c'est « ON NE SAIT PAS » : firmware\n"
              "   antérieur à dn4-23, ou commande enregistrée hors `k_cmds[]`."
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
_TEMOINS_ROUGES = [
    ("refusé : ESP_ERR_INVALID_ARG",
     "anim on 10 — le stimulus n'a JAMAIS tourné (mesuré, 2 fenêtres de 90 s)"),
    ("refusé : ESP_ERR_INVALID_STATE",
     "flash on — la fenêtre a mesuré un stimulus qu'elle croyait avoir démarré"),
    ("Unrecognized command",
     "REPL ESP-IDF — commande inconnue, AUCUN message de nous"),
    ("Command returned non-zero error code: 0x102 (ESP_ERR_INVALID_ARG)",
     "REPL ESP-IDF — vaut pour TOUTE commande, y compris muette"),
    ("Internal error: ESP_ERR_NO_MEM",
     "REPL ESP-IDF — le quatrième cas de `esp_console_common.c`"),
    ("refuse : entre 1 et 2000 ms",
     "la convention SANS accent, elle existe aussi (8 sites)"),
    ("REFUSE : index hors plage (0..5) OU couleur > 0xFFFFFF.",
     "la convention en CAPITALES, `widget couleur`"),
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
    for ligne, pourquoi in _TEMOINS_ROUGES:
        vus = chercher_refus("bla bla\n" + ligne + "\nbla")
        ctrl(len(vus) == 1, "ROUGE : %s" % ligne[:44], pourquoi[:28])
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

    resultats = []
    code = 0
    try:
        if args.reset:
            brut = reset_puce(ser, args.reset_wait)
            resultats.append({"commande": "(reset RTS + bandeau de boot)",
                              "sortie": brut.strip(), "invite_rendue": None,
                              "brut": brut})
        if args.listen:
            brut, _ = lire_jusqu_invite(ser, args.listen)
            resultats.append({"commande": None, "sortie": brut.strip(),
                              "invite_rendue": None, "brut": brut})
        elif args.commandes:
            try:
                reveiller(ser)
            except ConsoleErreur as e:
                sys.stderr.write(f"\n✗ {e}\n")
                return 1
            for cmd in args.commandes:
                r = envoyer(ser, cmd, args.timeout, not args.no_wait)
                resultats.append(r)
                if r["invite_rendue"] is False:
                    code = 1
                # 🔴 AC1.3 — UN REFUS VAUT UNE INVITE NON RENDUE. Jusqu'ici le
                #    SEUL signal d'échec de ce pilote était `invite_rendue is
                #    False` : une commande refusée à l'écran rendait 0.
                if r["refus"] and not refus_tolere(cmd, args.refus_tolere):
                    code = 1
                # 🔴 AC2.2 — ET UNE PERTE DE LIGNES AUSSI. ⛔ Seule la PERTE arme
                #    le rc : des lignes ÉTRANGÈRES (log asynchrone) sont un fait
                #    normal de cette carte, et crier dessus apprendrait à
                #    ignorer le cri.
                if r["completude"] and r["completude"]["etat"] == "PERTE":
                    code = 1
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
                tol = refus_tolere(r["commande"], args.refus_tolere)
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
    return code


if __name__ == "__main__":
    raise SystemExit(main())

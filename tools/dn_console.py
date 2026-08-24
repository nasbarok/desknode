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

Code de retour : 0 si toutes les commandes ont rendu l'invite, 1 sinon (timeout,
port occupé, port muet). Un timeout n'est PAS forcément une erreur — `tear on`
ne rend pas la main, c'est normal ; utiliser --no-wait pour ces commandes-là.
"""

import argparse
import glob
import json
import os
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
        return {"commande": commande, "sortie": brut.strip(),
                "invite_rendue": None, "brut": brut}
    brut, invite = lire_jusqu_invite(ser, timeout)
    return {"commande": commande, "sortie": nettoyer(brut, commande),
            "invite_rendue": invite, "brut": brut}


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
    args = p.parse_args()

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
            print(r["sortie"])
            if r["invite_rendue"] is False:
                print(f"⚠️ invite NON rendue en {args.timeout:.0f} s — "
                      "commande longue (augmenter --timeout) ou console bloquée.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
DeskNode — SONDE D'HORLOGE, l'INSTRUMENT de dn4-18.        (dn4-18, 2026-08-26)

🔴 ⛔ CE FICHIER N'EST PAS LE MÉCANISME. Il ne pose rien tout seul, il ne tourne
   pas en permanence, et il n'est PAS déposé sur la tour par
   `tools/deployer_tour.sh` (dont la liste ne porte que cinq fichiers). C'est
   l'instrument qui prend les mesures d'AC1 — celles que la story exige AVANT
   d'écrire une ligne du mécanisme.

POURQUOI IL EXISTE (et pourquoi le journal de l'agent ne suffit PAS)
===================================================================
AC1.1 demande trois choses que `dn-agent.log` ne peut PAS rendre :

  1. **le texte drainé**, verbatim. `SortieSerie._drainer()` COMPTE les octets
     (`echo_octets`, `echo_lignes`) et les JETTE. Le bandeau de boot, s'il
     arrive, ne laisse aucune trace lisible — seulement quelques centaines
     d'octets de plus dans un compteur cumulatif.
  2. **un délai chiffré**. Les lignes `[agent] …` de stderr ne portent AUCUN
     horodatage : le journal de la tour dit *dans quel ordre*, jamais *quand*.
     Un délai ne s'en déduit pas.
  3. **la distinction « la carte n'a pas parlé » / « l'agent n'écoutait pas ».**
     `_drainer()` n'est appelé QUE depuis `envoyer()` après une écriture
     réussie (`dn_agent.py:1957`) et depuis `fermer()` (`:2012`). Pendant le
     backoff — c'est-à-dire exactement après un débranchement — l'agent est
     AVEUGLE au fil. Un écouteur qui, lui, ne dort jamais est le seul moyen de
     savoir si la carte a parlé dans le vide.

⇒ Le verbe `tracer` est cet écouteur : il rouvre le port en boucle SERRÉE et
  horodate chaque bloc lu, ainsi que chaque ouverture réussie ou refusée.

LES DEUX PLATEFORMES, ET POURQUOI ELLES NE S'OUVRENT PAS PAREIL
==============================================================
🔴 MESURÉ (dn2-2, 2026-08-16, A/B à une variable) : sous **Windows**, pyserial
   pose DTR/RTS à l'ouverture, et la séquence RESET LA PUCE ⇒ il faut forcer
   `dtr=False; rts=False` AVANT `open()`. Sous **Linux**, la même parade
   PROVOQUE le reset qu'elle prétend empêcher (6 664 o reçus et
   `rst:0x15 (USB_UART_CHIP_RESET)` dans le flux, contre 38 o sans y toucher).
   ⇒ Cette sonde fait donc DEUX choses différentes selon la plateforme, et le
   dit dans son en-tête de capture. ⛔ Ne pas « unifier » les deux chemins.

USAGE
=====
    # AC1.2 — l'écart entre l'heure posée et l'heure de la tour, ENCADRÉ
    python3 tools/sonde_horloge_dn418.py lire   --capture mesures/dn4-18/x.log
    python3 tools/sonde_horloge_dn418.py poser  --capture mesures/dn4-18/x.log

    # AC1.1 — l'écouteur qui ne dort jamais (⇒ « la carte a-t-elle parlé ? »)
    python3 tools/sonde_horloge_dn418.py tracer --duree 180 \
            --capture mesures/dn4-18/ac1-1-tracer.log

Code de retour : 0 si la mesure a abouti, 1 sinon. ⚠️ Un `tracer` qui n'a RIEN
lu rend 1 : « aucun octet en 180 s » est un résultat, pas un succès silencieux.
"""

import argparse
import os
import sys
import time

try:
    import serial  # pyserial
except ImportError:  # pragma: no cover - dépend de l'hôte
    print("ECHEC : pyserial absent. `pip install pyserial`.", file=sys.stderr)
    raise SystemExit(2)

PROMPT = b"desknode>"
BAUD = 115200
# Port par défaut : la carte n'a pas le même nom des deux côtés du même câble.
PORT_DEFAUT = "COM3" if sys.platform == "win32" else "/dev/ttyACM0"

# Pas de la boucle de réouverture du traceur. ⚠️ CE CHIFFRE EST LA RÉSOLUTION DE
# LA MESURE DE DÉLAI d'AC1.1 : on ne peut pas dater la reprise du port plus
# finement que le pas auquel on la tente. 50 ms est très en dessous du plus
# petit palier de backoff de l'agent (500 ms), donc l'instrument est plus fin
# que ce qu'il mesure.
PAS_REOUVERTURE_S = 0.05


def _ouvrir(port, exclusif=True):
    """Ouvre le port, avec la parade DTR/RTS du BON côté (voir en-tête)."""
    if sys.platform == "win32":
        con = serial.Serial()
        con.port = port
        con.baudrate = BAUD
        con.timeout = 0.2
        con.write_timeout = 2
        con.dtr = False
        con.rts = False
        con.open()
        return con
    # POSIX : ⛔ on ne touche NI dtr NI rts. `exclusive` pose TIOCEXCL.
    return serial.Serial(port, BAUD, timeout=0.2, exclusive=exclusif)


class Capture:
    """Le fichier de capture BRUTE. ⛔ Un chiffre publié sans sa capture n'est
    pas recevable (AC7.5) — donc tout ce que la sonde lit part ici, tel quel."""

    def __init__(self, chemin):
        self.chemin = chemin
        self._f = None
        self.octets = 0
        if chemin:
            # 'ab' : on AJOUTE. Une session de mesure enchaîne plusieurs verbes,
            # et écraser la capture précédente perdrait la moitié du témoin.
            self._f = open(chemin, "ab")

    def entete(self, texte):
        self.ecrire(("\n===== " + texte + "\n").encode("utf-8"))

    def ecrire(self, octets):
        self.octets += len(octets)
        if self._f is not None:
            self._f.write(octets)
            self._f.flush()

    def fermer(self):
        if self._f is not None:
            self._f.close()
            self._f = None


def _horloge():
    """L'horloge de l'hôte, sous ses DEUX formes, prises au MÊME instant.

    ⚠️ `time.time()` sert à l'arithmétique (l'écart), la chaîne locale sert à
    composer la commande. Les relire séparément introduirait un décalage qu'on
    imputerait ensuite à la carte.
    """
    t = time.time()
    return t, time.localtime(t)


def _txt_horloge(t, lt):
    return "%04d-%02d-%02d %02d:%02d:%02d.%03d" % (
        lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec,
        int((t % 1.0) * 1000))


def _lire_jusqu_invite(con, timeout_s):
    """Lit jusqu'à revoir l'invite, ou jusqu'au timeout. Rend (octets, vue)."""
    fin = time.monotonic() + timeout_s
    tampon = bytearray()
    while time.monotonic() < fin:
        n = con.in_waiting
        morceau = con.read(n if n else 1)
        if morceau:
            tampon.extend(morceau)
            if bytes(tampon).rstrip().endswith(PROMPT):
                return bytes(tampon), True
    return bytes(tampon), False


def _analyser_rtc(brut):
    """Extrait de la réponse de `rtc` les trois faits qui nous intéressent.

    ⚠️ TRAVAIL SUR LES OCTETS, décodé en `replace` — ⛔ JAMAIS `.decode('ascii')` :
       `rtc` imprime `🔴`, `⛔`, `é` (dn_console.c:7446-7452), et un décodage
       ASCII LÈVE. C'est le piège n°4 des Dev Notes de la story.
    """
    txt = brut.decode("utf-8", "replace")
    etat, os_bit, lue = None, None, None
    for ligne in txt.splitlines():
        s = ligne.strip()
        if s.startswith("horloge PCF85063A") and " : " in s:
            etat = s.split(" : ", 1)[1].strip()
        elif s.startswith("bit OS"):
            # `bit OS     : 1 — 🔴 …`
            corps = s.split(":", 1)[1].strip()
            if corps[:1] in ("0", "1"):
                os_bit = int(corps[0])
        elif s.startswith("lue"):
            # `lue        : 2000-01-01 01:14:49 (jour de semaine 6) — …`
            corps = s.split(":", 1)[1].strip()
            morceaux = corps.split()
            if len(morceaux) >= 2:
                lue = morceaux[0] + " " + morceaux[1]
    return etat, os_bit, lue


def _epoch_de(lue):
    """`AAAA-MM-JJ HH:MM:SS` (heure LOCALE, A4) -> epoch. Rend None si illisible.

    ⚠️ `mktime` interprète en heure LOCALE — c'est EXACTEMENT ce qu'il faut :
       `rtc set` prend de l'heure locale décomposée, ⛔ pas un epoch UTC.
       `tm_isdst = -1` laisse la libc trancher le fuseau du jour.
    """
    try:
        d, h = lue.split()
        a, mo, j = (int(x) for x in d.split("-"))
        hh, mi, ss = (int(x) for x in h.split(":"))
    except Exception:
        return None
    return time.mktime((a, mo, j, hh, mi, ss, 0, 0, -1))


def _envoyer(con, commande, timeout_s):
    """Envoie une commande console et rend (brut, invite_vue, duree_s).

    ⛔ PAS de `reset_input_buffer()` ici, contrairement à `dn_console.envoyer` :
       cette sonde MESURE le flux, elle n'a pas le droit d'en jeter un morceau.
       En contrepartie la réponse rendue peut porter un reliquat de ce qui
       précédait — c'est assumé, et la capture brute permet de le voir.
    """
    t0 = time.monotonic()
    con.write((commande + "\n").encode("ascii"))
    con.flush()
    brut, vue = _lire_jusqu_invite(con, timeout_s)
    return brut, vue, time.monotonic() - t0


# ── VERBE `lire` ────────────────────────────────────────────────────────────
def verbe_lire(args, cap):
    """AC1.2 / AC2.1 — `rtc`, ENCADRÉ par deux lectures d'horloge hôte.

    Publie aussi le COÛT CONSOLE de l'interrogation (octets et lignes rendus par
    la carte) : c'est la case « ~30 lignes par interrogation » du tableau C1/C2
    d'AC2.1, mesurée au lieu d'être estimée.
    """
    con = _ouvrir(args.port)
    try:
        t_avant, lt_avant = _horloge()
        brut, vue, duree = _envoyer(con, "rtc", args.timeout)
        t_apres, lt_apres = _horloge()
    finally:
        con.close()

    cap.entete("lire  hote_avant=%s  hote_apres=%s  plateforme=%s"
               % (_txt_horloge(t_avant, lt_avant),
                  _txt_horloge(t_apres, lt_apres), sys.platform))
    cap.ecrire(brut)

    etat, os_bit, lue = _analyser_rtc(brut)
    lignes = brut.count(b"\n")
    print("  hote avant  : %s" % _txt_horloge(t_avant, lt_avant))
    print("  hote apres  : %s   (fenetre %.3f s)"
          % (_txt_horloge(t_apres, lt_apres), t_apres - t_avant))
    print("  reponse     : %d o, %d lignes, %.3f s, invite %s"
          % (len(brut), lignes, duree, "RENDUE" if vue else "NON RENDUE"))
    print("  etat        : %s" % etat)
    print("  bit OS      : %s" % os_bit)
    print("  lue         : %s" % lue)

    ecart = None
    if lue is not None:
        e = _epoch_de(lue)
        if e is not None:
            # Le milieu de la fenêtre d'encadrement est le meilleur estimateur
            # de l'instant de la lecture ; la fenêtre elle-même EST la
            # quantification, et on la publie avec l'écart.
            milieu = (t_avant + t_apres) / 2.0
            ecart = e - milieu
            print("  ecart carte-hote : %+.1f s   (+/- %.1f s de fenetre, "
                  "+/- 1 s de quantification de la carte)"
                  % (ecart, (t_apres - t_avant) / 2.0))
    return 0 if vue else 1


# ── VERBE `poser` ───────────────────────────────────────────────────────────
def verbe_poser(args, cap):
    """AC1.2 — pose l'heure LOCALE de l'hôte, encadrée, puis RELIT.

    ⛔ Ce verbe est un INSTRUMENT de mesure de l'écart, ⛔ pas le mécanisme de
       la story : il ne se déclenche sur rien, il est tapé à la main.
    """
    con = _ouvrir(args.port)
    try:
        t_avant, lt_avant = _horloge()
        # 🔴 LA SONDE COMPOSE COMME LE MECANISME, ⛔ PAS AUTREMENT — CORRECTIF
        #    DE REVUE 2026-08-26. Elle composait depuis `localtime(time.time())`,
        #    donc TRONQUE : biais systematiquement dans [-1 s, 0]. Le mecanisme,
        #    lui, arrondit (`dn_agent.py`, `ReprisHorloge._poser` : `t + 0,5`),
        #    biais CENTRE dans [-0,5 s, +0,5 s].
        # ⇒ un instrument qui ne compose pas comme le produit ne mesure plus le
        #   produit : tout rejeu de `sonde … poser` pour verifier le seuil de
        #   « ≤ 2 s » d'AC1.2 aurait caracterise la variante TRONQUANTE.
        # ⚠️ Les chiffres publies au dossier (-0,4 s WSL, -0,2 s tour) ont ete
        #    pris AVANT ce correctif, avec la composition tronquante — ils
        #    bornent donc le PIRE cas, et le seuil tient a plus forte raison.
        lt_pose = time.localtime(t_avant + 0.5)
        cmd = "rtc set %04d-%02d-%02d %02d:%02d:%02d" % (
            lt_pose.tm_year, lt_pose.tm_mon, lt_pose.tm_mday,
            lt_pose.tm_hour, lt_pose.tm_min, lt_pose.tm_sec)
        brut, vue, duree = _envoyer(con, cmd, args.timeout)
        t_apres, lt_apres = _horloge()
    finally:
        con.close()

    cap.entete("poser cmd=%r hote_avant=%s hote_apres=%s plateforme=%s"
               % (cmd, _txt_horloge(t_avant, lt_avant),
                  _txt_horloge(t_apres, lt_apres), sys.platform))
    cap.ecrire(brut)

    lignes = brut.count(b"\n")
    refus = b"non-zero error code" in brut
    print("  commande    : %s" % cmd)
    print("  hote avant  : %s" % _txt_horloge(t_avant, lt_avant))
    print("  hote apres  : %s   (fenetre %.3f s)"
          % (_txt_horloge(t_apres, lt_apres), t_apres - t_avant))
    print("  reponse     : %d o, %d lignes, %.3f s, invite %s"
          % (len(brut), lignes, duree, "RENDUE" if vue else "NON RENDUE"))
    print("  refus firmware : %s" % ("OUI" if refus else "non"))
    return 1 if (refus or not vue) else 0


# ── VERBE `tracer` ──────────────────────────────────────────────────────────
def verbe_tracer(args, cap):
    """AC1.1 — L'ÉCOUTEUR QUI NE DORT JAMAIS.

    🔴 C'est le témoin qui répond à « la carte a-t-elle parlé ? », face au
       journal de l'agent qui ne répond qu'à « l'agent a-t-il entendu ? ».
       Il rouvre le port toutes les `PAS_REOUVERTURE_S` tant qu'il est absent,
       et HORODATE : chaque bloc lu, chaque ouverture réussie, chaque échec
       d'ouverture (seulement le PREMIER de chaque série — cinq lignes par
       seconde noieraient le témoin, la leçon de `LiaisonEnAttente`).
    """
    fin = time.monotonic() + args.duree if args.duree > 0 else None
    con = None
    octets = 0
    blocs = 0
    ouvertures = 0
    echec_signale = None
    t_debut, lt_debut = _horloge()
    cap.entete("tracer debut=%s duree=%ss port=%s plateforme=%s pas_reouv=%.0fms"
               % (_txt_horloge(t_debut, lt_debut), args.duree, args.port,
                  sys.platform, PAS_REOUVERTURE_S * 1000))
    print("  tracage demarre : %s  (port %s, %s)"
          % (_txt_horloge(t_debut, lt_debut), args.port,
             "duree %d s" % args.duree if args.duree > 0 else "sans fin"))
    sys.stdout.flush()
    try:
        while fin is None or time.monotonic() < fin:
            if args.stop_si and os.path.exists(args.stop_si):
                print("  arret : drapeau %s" % args.stop_si)
                break
            if con is None:
                try:
                    con = _ouvrir(args.port, exclusif=False)
                except Exception as exc:
                    if echec_signale != str(exc):
                        echec_signale = str(exc)
                        t, lt = _horloge()
                        cap.entete("PORT ABSENT %s : %s"
                                   % (_txt_horloge(t, lt), exc))
                        print("  [%s] port ABSENT : %s"
                              % (_txt_horloge(t, lt), exc))
                        sys.stdout.flush()
                    time.sleep(PAS_REOUVERTURE_S)
                    continue
                ouvertures += 1
                echec_signale = None
                t, lt = _horloge()
                cap.entete("PORT OUVERT %s (ouverture n.%d)"
                           % (_txt_horloge(t, lt), ouvertures))
                print("  [%s] port OUVERT (n.%d)"
                      % (_txt_horloge(t, lt), ouvertures))
                sys.stdout.flush()
            try:
                n = con.in_waiting
                morceau = con.read(n if n else 1)
            except Exception as exc:
                t, lt = _horloge()
                cap.entete("PORT PERDU %s : %s" % (_txt_horloge(t, lt), exc))
                print("  [%s] port PERDU : %s" % (_txt_horloge(t, lt), exc))
                sys.stdout.flush()
                try:
                    con.close()
                finally:
                    con = None
                continue
            if morceau:
                blocs += 1
                octets += len(morceau)
                t, lt = _horloge()
                cap.ecrire(("\n--- %s (+%d o) ---\n"
                            % (_txt_horloge(t, lt), len(morceau))).encode("utf-8"))
                cap.ecrire(morceau)
    except KeyboardInterrupt:
        print("  arret demande (Ctrl+C)")
    finally:
        if con is not None:
            try:
                con.close()
            except Exception:
                pass
    t_fin, lt_fin = _horloge()
    mur = max(t_fin - t_debut, 1e-6)
    cap.entete("tracer fin=%s octets=%d blocs=%d ouvertures=%d"
               % (_txt_horloge(t_fin, lt_fin), octets, blocs, ouvertures))
    print("  tracage fini    : %s" % _txt_horloge(t_fin, lt_fin))
    print("  lu              : %d o, %d blocs en %.1f s = %.1f o/s"
          % (octets, blocs, mur, octets / mur))
    print("  ouvertures      : %d" % ouvertures)
    # ⛔ « aucun octet » est un RÉSULTAT, pas un succès : on le dit ET on le
    #    rend en code de retour, pour qu'un harnais ne puisse pas le rater.
    if octets == 0:
        print("  /!\\ AUCUN OCTET LU : la carte est muette, ou le port est tenu "
              "ailleurs (l'agent ?).")
        return 1
    return 0


def main():
    p = argparse.ArgumentParser(
        description="Sonde d'horloge DeskNode — INSTRUMENT de dn4-18 "
                    "(⛔ pas le mecanisme).")
    p.add_argument("verbe", choices=("lire", "poser", "tracer"))
    p.add_argument("--port", default=PORT_DEFAUT,
                   help="port serie (defaut : %s)" % PORT_DEFAUT)
    p.add_argument("--timeout", type=float, default=20.0,
                   help="attente de l'invite, en secondes (defaut 20)")
    p.add_argument("--duree", type=int, default=0, metavar="S",
                   help="`tracer` : duree en secondes (0 = sans fin)")
    p.add_argument("--stop-si", metavar="FICHIER", default=None,
                   help="`tracer` : s'arrete des que FICHIER apparait")
    p.add_argument("--capture", metavar="FICHIER", default=None,
                   help="capture BRUTE (ajoutee, jamais ecrasee)")
    args = p.parse_args()

    # Les messages portent des accents ; la console Windows est en cp1252
    # jusqu'a Python 3.14. On force l'UTF-8, comme dn_agent.py.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    cap = Capture(args.capture)
    try:
        if args.verbe == "lire":
            return verbe_lire(args, cap)
        if args.verbe == "poser":
            return verbe_poser(args, cap)
        return verbe_tracer(args, cap)
    finally:
        cap.fermer()


if __name__ == "__main__":
    raise SystemExit(main())

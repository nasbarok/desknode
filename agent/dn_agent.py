#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""dn_agent.py — l'agent PC de DeskNode (dn2-2) : publie le % CPU de la tour à ~1 Hz.

UN SEUL FICHIER, lancé à la main, SANS élévation, SANS driver (le Ring0 est dn4-1).
Tourne sur le Python Windows 3.13.4 de la tour :
    python \\wsl.localhost\Ubuntu\home\nasbarok\projects\desknode\agent\dn_agent.py --stdout

── LA SOURCE DU % CPU, ET POURQUOI (arbitrage dn2-2, mesuré le 2026-08-16) ──────────────
Retenu : psutil.cpu_percent() — les compteurs noyau GetSystemTimes(), ceux-là même que lit
le Gestionnaire des tâches (onglet Performance, « % temps processeur »).
  · Get-Counter '\\Processor(_Total)\\% Processor Time' — ÉLIMINÉ PAR SYMPTÔME : sur ce
    Windows FRANÇAIS, « L'objet spécifié n'a pas été trouvé sur l'ordinateur » (les noms de
    compteurs sont localisés ; la parade par IDs numériques est illisible et fragile).
  · WMI Win32_PerfFormattedData_PerfOS_Processor — MARCHE (18 % rendu, neutre en langue)
    mais impose soit un spawn PowerShell par échantillon (4,2 s mesurées — incompatible
    1 Hz), soit un agent résident PowerShell 5.1, qui n'a ni pyserial ni websockets.
  · psutil 7.2.2 — dépendance ASSUMÉE (`pip install --user psutil`, écrite au README) :
    même chiffre que le noyau, échantillonnage deux-temps géré, et couvre déjà RAM/réseau/
    disque pour dn4-1. `websockets` et `pyserial` étaient déjà sur la tour.
⚠️ Piège nommé par la story : Win32_Processor.LoadPercentage n'est PAS le même chiffre
   (moyenne grossière) — jamais utilisé ici.
⚠️ Piège du premier échantillon : le premier cpu_percent() vaut 0.0 (pas d'intervalle de
   référence). L'agent fait UN appel d'amorçage jeté avant de publier quoi que ce soit.

── LE PROTOCOLE DE TRAME (version 1) — fait foi ici et dans dn_link.h ───────────────────
Une trame = UNE ligne ASCII terminée par '\n', inspirée NMEA :

    $DN,<ver>,<seq>,<t_ms>,cpu,<dixiemes>*<CK>\n

  $DN        marqueur de début (résistance au bruit : tout ce qui ne commence pas
             par « $DN, » est ignoré sans compteur — ce n'est pas une trame).
  <ver>      version du protocole, entier. Ici : 1. Version inconnue ⇒ trame REJETÉE
             et comptée, jamais interprétée à moitié.
  <seq>      compteur de trames de l'agent, uint32, croissant. Détecte doublons et pertes.
  <t_ms>     horodatage AGENT : millisecondes depuis le démarrage de l'agent, uint32
             (déborde à 49,7 j — sans effet : le firmware ne fait foi que de SON horodatage
             de réception, cf. AC2/AC7 ; t_ms sert au diagnostic et à la latence).
  cpu        nom de la métrique (dn2-2 n'en publie qu'une seule).
  <dixiemes> valeur en DIXIÈMES de % (entier 0..1000) : « 153 » = 15,3 %.
             Entier pour les gabarits parse_entier() du firmware — pas de float sur le fil.
  *<CK>      étoile + checksum : XOR de tous les octets entre '$' (exclu) et '*' (exclu),
             deux chiffres hexadécimaux MAJUSCULES. Trame sans '*' ou checksum faux ⇒
             REJETÉE et comptée.

  Exemple :  $DN,1,42,123456,cpu,153*29

  Cadence : ~1 Hz, tenue en TEMPS ABSOLU (pas de dérive de sleep cumulée). Le firmware
  ne suppose JAMAIS cette cadence : une trame en retard est simplement une donnée
  périmée à ses yeux (délai de péremption côté firmware, AC7).

── SORTIES ─────────────────────────────────────────────────────────────────────────────
  --stdout          : imprime les trames (témoin, mesure du coût, débogage)
  --serie PORT      : branche A — trames vers un port série (COM3 côté Windows)
  --ws URL          : branche B — client WebSocket (l'ESP est SERVEUR : pas de règle
                      de pare-feu entrante sur la tour, cf. §8 de la story)
  --temoin          : ajoute sur stderr, toutes les 10 s, le coût CPU de l'AGENT lui-même
                      (psutil.Process().cpu_percent) — le critère « < 1 % » du brief.

Reconnexions : minimum honnête (dn4-1 solde le backoff propre) — en cas d'échec d'envoi,
l'agent tente de rouvrir la sortie à chaque nouvelle trame, et le dit sur stderr.
"""

import argparse
import sys
import time

try:
    import psutil
except ImportError:
    sys.exit("psutil manquant : pip install --user psutil (dépendance assumée, cf. README)")

PROTO_VERSION = 1
PERIODE_S = 1.0
BORNE_MAX_DIXIEMES = 1000


def checksum(corps: str) -> str:
    """XOR NMEA des octets du corps (entre '$' exclu et '*' exclu), hex majuscule."""
    ck = 0
    for octet in corps.encode("ascii"):
        ck ^= octet
    return f"{ck:02X}"


def trame(seq: int, t_ms: int, dixiemes: int) -> str:
    corps = f"DN,{PROTO_VERSION},{seq},{t_ms},cpu,{dixiemes}"
    return f"${corps}*{checksum(corps)}\n"


class SortieStdout:
    nom = "stdout"

    def envoyer(self, ligne: str) -> None:
        sys.stdout.write(ligne)
        sys.stdout.flush()


class SortieSerie:
    """Branche A — le port série (COM3 sous Windows quand la carte n'est PAS attachée à WSL).
    ⚠️ Exclusivité WSL↔COM3 : si `usbipd attach` tient la carte, COM3 N'EXISTE PAS ici.
    Un agent qui ne trouve pas son port n'est pas un bug de l'agent (trap n°4 de la story)."""

    nom = "serie"

    # ── LE DIALECTE (branche A) ─────────────────────────────────────────────────────
    # Le port EST le REPL `desknode>` (chemin console unique). L'agent parle donc le
    # dialecte de la console : chaque trame part en `pc $DN,…` — une commande comme
    # une autre, que le firmware route vers dn_link. Pas de canal séparé, pas de
    # préfixe consommé en amont : « l'agent parle le même dialecte que l'humain ».
    #
    # ── L'ÉCHO, DRAINÉ ET COMPTÉ ────────────────────────────────────────────────────
    # Le REPL RENVOIE des octets pour chaque ligne reçue (écho + invite + logs +
    # battement 10 s). L'agent les DRAINE à chaque cycle et les COMPTE : ce compte
    # EST la mesure du bruit de cohabitation d'AC3 (octets/s et lignes/s ajoutés au
    # flux console par le régime 1 Hz).

    def __init__(self, port: str):
        import serial  # pyserial — déjà sur la tour

        self._serial_mod = serial
        self._port = port
        self._con = None
        self.echo_octets = 0
        self.echo_lignes = 0

    def _ouvrir(self):
        # ⚠️ CROYANCE §7.3 CORRIGÉE PAR LA MESURE (dn2-2, 2026-08-16) : « ouvrir ne
        # reset pas la carte » était vrai DEPUIS LINUX (dn_console.py ne touche ni
        # dtr ni rts). Sous WINDOWS, pyserial pose DTR/RTS à l'ouverture et les
        # relâche à la fermeture — et l'état transitoire (DTR bas, RTS qui retombe)
        # est EXACTEMENT la recette du reset de puce de `dn_console.py --reset`.
        # Symptôme mesuré : trois sessions série de suite retrouvées « liaison
        # jamais recue » — la carte REBOOTAIT à la fermeture du port, compteurs
        # wipés, pendant que l'agent croyait avoir tout envoyé. Parade : forcer
        # DTR/RTS BAS AVANT d'ouvrir, et ne plus jamais y toucher.
        con = self._serial_mod.Serial()
        con.port = self._port
        con.baudrate = 115200
        con.timeout = 1
        con.dtr = False
        con.rts = False
        con.open()
        self._con = con

    def envoyer(self, ligne: str) -> None:
        if self._con is None:
            self._ouvrir()
        try:
            self._con.write(b"pc " + ligne.encode("ascii"))
            retour = self._con.read(self._con.in_waiting or 0)
            self.echo_octets += len(retour)
            self.echo_lignes += retour.count(b"\n")
        except Exception:
            try:
                self._con.close()
            finally:
                self._con = None
            raise


class SortieWebSocket:
    """Branche B — client WebSocket vers l'ESP SERVEUR (sortant : pas de règle de
    pare-feu entrante ; reste la question des tunnels — constatée en T4, pas supposée)."""

    nom = "websocket"

    def __init__(self, url: str):
        from websockets.sync.client import connect  # websockets — déjà sur la tour

        self._connect = connect
        self._url = url
        self._con = None

    def _ouvrir(self):
        self._con = self._connect(self._url, open_timeout=3)

    def envoyer(self, ligne: str) -> None:
        if self._con is None:
            self._ouvrir()
        try:
            self._con.send(ligne)
        except Exception:
            try:
                self._con.close()
            finally:
                self._con = None
            raise


def principal() -> int:
    ap = argparse.ArgumentParser(description="Agent DeskNode : % CPU de la tour à ~1 Hz.")
    sortie_grp = ap.add_mutually_exclusive_group(required=True)
    sortie_grp.add_argument("--stdout", action="store_true", help="trames sur stdout (témoin)")
    sortie_grp.add_argument("--serie", metavar="PORT", help="branche A : port série (ex. COM3)")
    sortie_grp.add_argument("--ws", metavar="URL", help="branche B : URL WebSocket (ex. ws://IP:80/dn)")
    ap.add_argument("--temoin", action="store_true",
                    help="coût CPU de l'agent lui-même sur stderr toutes les 10 s")
    ap.add_argument("--duree", type=int, default=0, metavar="S",
                    help="s'arrête PROPREMENT après S secondes (0 = infini) — "
                         "c'est le témoin « arrêt propre » d'AC7")
    args = ap.parse_args()

    if args.serie:
        sortie = SortieSerie(args.serie)
    elif args.ws:
        sortie = SortieWebSocket(args.ws)
    else:
        sortie = SortieStdout()

    # Les trames sont ASCII pur, mais les messages français passent par la console
    # Windows (cp1252 par défaut jusqu'à Python 3.14) : on force l'UTF-8.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    moi = psutil.Process()

    # Amorçage deux-temps : le premier échantillon vaut toujours 0.0 — il est JETÉ.
    psutil.cpu_percent(interval=None)

    depart = time.monotonic()
    seq = 0
    erreurs_envoi = 0
    prochain = depart + PERIODE_S

    while args.duree <= 0 or (time.monotonic() - depart) < args.duree:
        # Cadence en temps absolu : on vise depart + n*PERIODE, pas « sleep(1) cumulés ».
        maintenant = time.monotonic()
        if maintenant < prochain:
            time.sleep(prochain - maintenant)
        prochain += PERIODE_S

        # % CPU depuis le DERNIER appel — la fenêtre est donc exactement notre période.
        pct = psutil.cpu_percent(interval=None)
        dixiemes = max(0, min(BORNE_MAX_DIXIEMES, round(pct * 10)))
        seq += 1
        t_ms = int((time.monotonic() - depart) * 1000) & 0xFFFFFFFF

        try:
            sortie.envoyer(trame(seq, t_ms, dixiemes))
        except Exception as exc:
            erreurs_envoi += 1
            print(f"[agent] envoi {sortie.nom} en échec ({erreurs_envoi}) : {exc}",
                  file=sys.stderr)

        if args.temoin and seq % 10 == 0:
            # Coût de l'agent LUI-MÊME : cumul cpu_times() depuis le lancement, rapporté
            # au temps mural écoulé. ⚠️ Une fenêtre glissante de 10 s a une résolution de
            # ~0,16 pt (ticks de 15,6 ms) — le CUMUL, lui, affine avec la durée : c'est
            # l'instrument qui PEUT voir un coût inférieur au brief (« < 1 % »).
            t = moi.cpu_times()
            cpu_s = t.user + t.system
            mur_s = time.monotonic() - depart
            pct_un_coeur = 100.0 * cpu_s / mur_s
            print(f"[agent] témoin coût cumulé : {cpu_s:.3f} s CPU / {mur_s:.1f} s mur "
                  f"= {pct_un_coeur:.3f} % d'un cœur "
                  f"({pct_un_coeur / psutil.cpu_count():.4f} % machine) — seq={seq}",
                  file=sys.stderr)

    # Arrêt PROPRE (--duree) : on dit ce qu'on a fait, et le bruit d'écho série
    # (cohabitation AC3) est rapporté ici — c'est une MESURE, pas un au revoir.
    mur = time.monotonic() - depart
    print(f"[agent] arrêt propre après {mur:.1f} s — {seq} trames émises, "
          f"{erreurs_envoi} erreurs d'envoi", file=sys.stderr)
    if isinstance(sortie, SortieSerie):
        print(f"[agent] écho console draîné : {sortie.echo_octets} o, "
              f"{sortie.echo_lignes} lignes en {mur:.1f} s "
              f"= {sortie.echo_octets / mur:.1f} o/s, "
              f"{sortie.echo_lignes / mur:.2f} lignes/s", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(principal())
    except KeyboardInterrupt:
        print("[agent] arrêt demandé (Ctrl+C)", file=sys.stderr)
        sys.exit(0)

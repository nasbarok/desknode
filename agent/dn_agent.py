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

  Exemple :  $DN,1,42,123456,cpu,153*47
             ⚠️ « *29 » jusqu'au 2026-08-16 : l'exemple publié était la seule trame que
             le firmware REJETTE (rejets_checksum). Corrigé en revue de code.

  Cadence : ~1 Hz, tenue en TEMPS ABSOLU (pas de dérive de sleep cumulée). Le firmware
  ne suppose JAMAIS cette cadence : une trame en retard est simplement une donnée
  périmée à ses yeux (délai de péremption côté firmware, AC7).

── SORTIES ─────────────────────────────────────────────────────────────────────────────
  --stdout          : imprime les trames (témoin, mesure du coût, débogage)
  --serie PORT      : branche A — trames vers un port série (COM3 côté Windows)
  --ws URL          : branche B — client WebSocket (l'ESP est SERVEUR : pas de règle
                      de pare-feu entrante sur la tour, cf. §8 de la story)
  --temoin          : ajoute sur stderr, toutes les 10 s, le coût CPU de l'AGENT lui-même
                      — le critère « < 1 % » du brief. ⚠️ La méthode est le CUMUL
                      `psutil.Process().cpu_times()` rapporté au temps mural, PAS une
                      fenêtre glissante `cpu_percent()` : une fenêtre de 10 s a une
                      résolution de ~0,16 pt (ticks de 15,6 ms) et ne PEUT PAS voir le
                      coût de l'ordre de 0,35 % qu'elle prétend établir. Le cumul, lui,
                      affine avec la durée. (L'en-tête annonçait `cpu_percent` alors que
                      le code fait `cpu_times` — étiquette corrigée en revue 2026-08-16.)
  --duree S         : s'arrête PROPREMENT après S secondes (0 = infini) — c'est le
                      témoin « arrêt propre » d'AC7.

Reconnexions : minimum honnête (dn4-1 solde le backoff propre) — en cas d'échec d'envoi,
l'agent tente de rouvrir la sortie à chaque nouvelle trame, et le dit sur stderr.

Bilan de fin : trames émises, erreurs d'envoi, RECALAGES DE CADENCE, et pour la branche A
le bruit d'écho console d'AC3 + les refus signalés par le firmware. Il sort sur stderr
dans TOUS les cas de sortie, **Ctrl+C compris** (correctif de revue 2026-08-16 : il
n'était imprimé qu'en sortie `--duree`, donc perdu sur la plupart des sessions).
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
        # ⚠️ BrokenPipeError est une SOUS-CLASSE d'Exception : redirigé vers un
        # consommateur qui se ferme (`| head`, un pipe coupé), l'agent tournait en
        # imprimant une erreur PAR SECONDE au lieu de sortir. On la distingue.
        sys.stdout.write(ligne)
        sys.stdout.flush()

    def fermer(self) -> None:
        pass


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
        # ⚠️ Le firmware REFUSE des trames en silence pour l'agent : le REPL renvoie
        # « Command returned non-zero error code » sur le fil. L'agent lisait cet
        # écho et ne le REGARDAIT PAS — il pouvait donc annoncer « 0 erreur d'envoi »
        # pendant que 100 % des trames tombaient en rejets_version ou _checksum et
        # que l'écran restait à « -- ». Un « 35/35 trames » prouvait 35 ÉCRITURES,
        # pas 35 acceptations (correctif de revue 2026-08-16).
        self.refus_firmware = 0

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
        # ⚠️ `timeout` de pyserial est le timeout de LECTURE seulement ;
        # `write_timeout` vaut None par défaut = BLOQUANT SANS LIMITE. Sur une carte
        # en PANIQUE HALTÉE (CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT, le « troisième état »
        # du README : le CPU est halté, l'USB n'est plus servi), le buffer TX se
        # remplit et write() ne rend JAMAIS la main : l'agent se fige, --duree
        # n'arrête plus rien, --temoin ne sort plus, et erreurs_envoi reste à 0.
        # Correctif de revue 2026-08-16.
        con.write_timeout = 2
        con.dtr = False
        con.rts = False
        con.open()
        self._con = con

    def envoyer(self, ligne: str) -> None:
        if self._con is None:
            self._ouvrir()
        try:
            trame_octets = b"pc " + ligne.encode("ascii")
            ecrits = self._con.write(trame_octets)
            if ecrits is not None and ecrits != len(trame_octets):
                # Une demi-trame atteint le REPL : elle corrompt SA ligne et la
                # suivante. Mieux vaut le dire que de compter un envoi réussi.
                raise IOError(f"ecriture partielle {ecrits}/{len(trame_octets)} o")
            self._drainer()
        except Exception:
            try:
                self._con.close()
            finally:
                self._con = None
            raise

    def _drainer(self) -> None:
        """Draine l'écho console et le COMPTE — c'est l'instrument d'AC3.

        ⚠️ CE QUE CE CHIFFRE EST, ET CE QU'IL N'EST PAS (correctif de revue) : le
        drain est AVEUGLE, il ramasse l'écho de la ligne, l'invite, le battement
        10 s ET tout ESP_LOGx émis par n'importe quel module. C'est donc un
        PLAFOND du bruit console, pas la contribution propre du régime 1 Hz.
        """
        retour = self._con.read(self._con.in_waiting or 0)
        if retour:
            self.echo_octets += len(retour)
            self.echo_lignes += retour.count(b"\n")
            # Le REPL signale un refus du firmware sur le fil : on le compte.
            self.refus_firmware += retour.count(b"non-zero error code")

    def fermer(self) -> None:
        """Dernier drain (l'écho du dernier envoi n'était pas encore revenu) puis
        fermeture explicite. Sans ce drain final, le compte d'AC3 perdait
        systématiquement un cycle."""
        if self._con is None:
            return
        try:
            time.sleep(0.05)  # ~33 o à 115 200 bauds ≈ 3 ms ; 50 ms est confortable
            self._drainer()
        except Exception:
            pass
        try:
            self._con.close()
        finally:
            self._con = None


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

    def fermer(self) -> None:
        if self._con is None:
            return
        try:
            self._con.close()
        finally:
            self._con = None


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

    if args.duree < 0:
        ap.error("--duree doit etre >= 0 (0 = infini)")

    # ⚠️ `if args.serie:` testait la VÉRACITÉ, pas la présence : un `--serie ""`
    # (variable vide développée par un script de lancement) retombait EN SILENCE
    # sur stdout, la carte restait « jamais recue », et rien ne le signalait.
    if args.serie is not None:
        if not args.serie.strip():
            ap.error("--serie attend un port (ex. COM3), pas une chaine vide")
        sortie = SortieSerie(args.serie)
    elif args.ws is not None:
        if not args.ws.strip():
            ap.error("--ws attend une URL (ex. ws://192.168.3.19/dn), pas une chaine vide")
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
    rattrapages = 0
    prochain = depart + PERIODE_S

    # ⚠️ try/finally : le bilan EST l'instrument d'AC3 (octets/s, lignes/s de bruit
    # console) et il doit sortir MÊME sur Ctrl+C — qui est le mode de lancement le
    # plus naturel. Avant, il n'était imprimé qu'en sortie `--duree` : sur la
    # majorité des sessions le chiffre était perdu, et le port jamais fermé
    # explicitement (correctif de revue 2026-08-16).
    try:
        while args.duree <= 0 or (time.monotonic() - depart) < args.duree:
            # Cadence en temps absolu : on vise depart + n*PERIODE, pas « sleep(1) cumulés ».
            maintenant = time.monotonic()
            if maintenant < prochain:
                time.sleep(prochain - maintenant)
            prochain += PERIODE_S

            # 🔴 RESYNCHRONISATION — LE CORRECTIF LE PLUS IMPORTANT DE LA REVUE (2026-08-16).
            # `prochain` n'était JAMAIS recalé sur l'horloge. Après une veille du PC, une
            # reconnexion VPN, un `_ouvrir()` WS à open_timeout=3 ou une écriture série qui
            # traîne, `prochain` se retrouvait N secondes dans le passé : la boucle tournait
            # alors SANS DORMIR pour rattraper, et `cpu_percent(interval=None)` appelé sur
            # un intervalle ~nul rend 0.0. Résultat : une RAFALE de trames parfaitement
            # VALIDES (checksum bon, seq croissant, horodatage frais) toutes à 0 — la carte
            # affichait « 0,0 % » et déclarait la liaison VIVANTE.
            # ⚠️ AC7 protège contre une valeur PÉRIMÉE ; là, la valeur était FRAÎCHE ET
            # FAUSSE — le mensonge d'interface entrait par la porte de derrière, et l'AC1
            # nomme précisément « un agent qui publie 0,0 % » comme le défaut interdit.
            if prochain < maintenant:
                rattrapages += 1
                print(f"[agent] ⚠️ cadence recalee apres {maintenant - prochain + PERIODE_S:.1f} s "
                      f"de retard (veille PC, blocage d'envoi ?) — la fenetre "
                      f"d'echantillonnage repart propre", file=sys.stderr)
                prochain = maintenant + PERIODE_S
                psutil.cpu_percent(interval=None)  # ré-amorce la fenêtre, comme au départ
                continue  # on ne publie PAS un échantillon pris sur une fenêtre nulle

            # % CPU depuis le DERNIER appel — la fenêtre est donc exactement notre période.
            pct = psutil.cpu_percent(interval=None)
            dixiemes = max(0, min(BORNE_MAX_DIXIEMES, int(pct * 10 + 0.5)))
            seq += 1
            t_ms = int((time.monotonic() - depart) * 1000) & 0xFFFFFFFF

            try:
                sortie.envoyer(trame(seq, t_ms, dixiemes))
            except BrokenPipeError:
                # stdout redirigé vers un consommateur qui s'est fermé : boucler en
                # imprimant une erreur par seconde n'a aucun sens, on sort.
                print("[agent] stdout ferme par le consommateur — arret", file=sys.stderr)
                break
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
                coeurs = psutil.cpu_count() or 1  # cpu_count() PEUT rendre None
                print(f"[agent] témoin coût cumulé : {cpu_s:.3f} s CPU / {mur_s:.1f} s mur "
                      f"= {pct_un_coeur:.3f} % d'un cœur "
                      f"({pct_un_coeur / coeurs:.4f} % machine) — seq={seq}",
                      file=sys.stderr)

    except KeyboardInterrupt:
        print("[agent] arrêt demandé (Ctrl+C)", file=sys.stderr)
    finally:
        _bilan(sortie, depart, seq, erreurs_envoi, rattrapages)
    return 0


def _bilan(sortie, depart: float, seq: int, erreurs_envoi: int, rattrapages: int) -> None:
    """Le récapitulatif — et c'est une MESURE, pas un au revoir.

    ⚠️ Il n'était imprimé qu'en sortie `--duree` : un Ctrl+C (le mode de lancement
    le plus naturel) sortait par le handler KeyboardInterrupt sans jamais l'écrire,
    et le port n'était jamais fermé explicitement. Le chiffre d'AC3 était donc perdu
    sur la majorité des sessions (correctif de revue 2026-08-16).
    """
    mur = max(time.monotonic() - depart, 1e-6)
    print(f"[agent] arrêt après {mur:.1f} s — {seq} trames émises, "
          f"{erreurs_envoi} erreurs d'envoi, {rattrapages} recalages de cadence",
          file=sys.stderr)
    if isinstance(sortie, SortieSerie):
        sortie.fermer()  # dernier drain AVANT de publier le chiffre
        print(f"[agent] écho console draîné : {sortie.echo_octets} o, "
              f"{sortie.echo_lignes} lignes en {mur:.1f} s "
              f"= {sortie.echo_octets / mur:.1f} o/s, "
              f"{sortie.echo_lignes / mur:.2f} lignes/s "
              f"(PLAFOND du bruit console : inclut le battement 10 s et tout ESP_LOGx)",
              file=sys.stderr)
        # Le firmware a-t-il ACCEPTÉ ce qu'on lui a envoyé ? « n trames émises » ne
        # l'a jamais dit — seul ce compteur distingue un envoi d'une acceptation.
        if sortie.refus_firmware:
            print(f"[agent] 🔴 {sortie.refus_firmware} trame(s) REFUSÉE(S) par le "
                  f"firmware (le compteur dit pourquoi : `pc` sur la console)",
                  file=sys.stderr)
        else:
            print("[agent] aucun refus signalé par le firmware sur le fil",
                  file=sys.stderr)
    else:
        sortie.fermer()


if __name__ == "__main__":
    try:
        sys.exit(principal())
    except KeyboardInterrupt:
        # Filet pour un Ctrl+C AVANT l'entrée dans la boucle (ouverture du port,
        # amorçage psutil) : la boucle, elle, a son propre try/finally qui imprime
        # le bilan et ferme la sortie.
        print("[agent] arrêt demandé (Ctrl+C)", file=sys.stderr)
        sys.exit(0)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""dn_agent.py — l'agent PC de DeskNode : publie CINQ métriques de la tour à ~1 Hz.

UN SEUL FICHIER, lancé à la main, SANS élévation, SANS driver, SANS .NET (D8 —
et c'est une FRONTIÈRE, pas une préférence : Ring0 / LibreHardwareMonitor sortent
du périmètre V1).
Tourne sur le Python Windows 3.13.4 de la tour :
    python \\wsl.localhost\Ubuntu\home\nasbarok\projects\desknode\agent\dn_agent.py --stdout

── CE QUE dn4-1 A CHANGÉ, ET CE QU'IL N'A PAS CHANGÉ ───────────────────────────
dn2-2 publiait UNE métrique (`cpu`) en protocole v1. dn4-1 en publie CINQ en v2 —
et v1 CONTINUE d'être acceptée par le firmware : l'agent de dn2-2, NON MODIFIÉ,
fait toujours vivre la case CPU. C'est le témoin de non-régression d'AC2, et sans
lui « extension additive » n'est qu'un mot.
⛔ La cadence, la resynchronisation, le drain d'écho et la méthode de mesure du
   coût propre ne changent PAS : ce sont les correctifs de la revue dn2-2, et
   chacun a été payé par un défaut réel.

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

── LE PROTOCOLE DE TRAME — L'AUTORITÉ EST `main/dn_link.h` ─────────────────────
⛔ CE BLOC NE REDÉFINIT RIEN, IL RÉSUME. Le dépôt a déjà publié un checksum FAUX
   dans TROIS fichiers à la fois (ici, `dn_link.h` et §12.5 de liaison-pc.md), et
   l'« exemple valide » du projet était la seule trame que le firmware REFUSE.
   Une grammaire recopiée dérive ; celle qui fait foi vit dans `dn_link.h`.

    $DN,2,<seq>,<t_ms>,<metrique>,<v1>[,<v2>]*<CK>

  <metrique>  cpu · gpu · ram · net · disk
  <v1>,<v2>   ENTIERS, en DIXIÈMES de l'unité de la métrique. Pas de flottant sur
              le fil (doctrine `parse_entier` du firmware).
  <v2>        OPTIONNELLE, et son absence EST une donnée : « je connais v1, je ne
              connais PAS v2 ». C'est le seul moyen honnête de publier un GPU dont
              le % est lisible et la température non. ⛔ Pas de jeton « inconnu » :
              `parse_u32_strict` refuse un champ vide, délibérément.
  *<CK>       XOR des octets entre '$' (exclu) et '*' (exclu), 2 hexa MAJUSCULES.

  Exemple :  $DN,1,42,123456,cpu,153*47      (v1, toujours acceptée)
             ⚠️ « *29 » jusqu'au 2026-08-16 : recalculer le XOR avant d'accuser
             la carte. XOR(« DN,1,42,123456,cpu,153 ») = 0x47.

  UNE TRAME PAR MÉTRIQUE (W3, tranché en dn4-1) : chaque métrique a ainsi son
  propre horodatage de réception côté firmware, donc sa propre péremption —
  gratuitement. Une source qui meurt seule meurt seule et honnêtement.
  ⚠️ LE PRIX EST RÉEL : ×5 sur l'écho console de la branche A. Il se MESURE
     (bilan de fin, octets/s et lignes/s), il ne se suppose pas.

  Cadence : ~1 Hz, tenue en TEMPS ABSOLU (pas de dérive de sleep cumulée), avec
  RESYNCHRONISATION. Le firmware ne suppose JAMAIS cette cadence.

── LES SOURCES, ET POURQUOI CELLES-LÀ (mesuré sur la tour le 2026-08-18) ───────
  cpu   psutil.cpu_percent()  +  psutil.cpu_freq().current
        La fréquence remplace la TEMPÉRATURE que la maquette dessinait : la °C
        CPU exige le Ring0, que D8 sort du périmètre. Elle est libre de droits ET
        elle bouge (mesuré : 1,2 à 3,2 GHz sur 960 échantillons).
  gpu   atiadlxx.dll / ADL2_New_QueryPMLogData_Get, en ctypes, SANS élévation.
        🔴 LE CADRAGE ANNONÇAIT NVML : INAPPLICABLE, la tour est une AMD Radeon
           RX 6800 XT (Win32_VideoController : UN SEUL contrôleur, 0x73BF), et
           `pynvml` n'est même pas installé.
        🔴 LE REPLI PRÉ-AUTORISÉ (« % seul, °C absente ») N'A PAS SERVI : ADL rend
           le % ET la °C en UN appel, pour 0,5 ms de CPU (0,052 % d'un cœur).
        ⛔ ET LE CANDIDAT DE REPLI POUR LE % A ÉTÉ ÉCARTÉ PAR LA MESURE : les 720
           instances WMI `GPUEngine` coûtent 342 ms de CPU PAR TIR (30,8 % d'un
           cœur, 1,93 % machine) — 657x plus cher, au-dessus du critère n°4 du
           brief à lui seul, et incapable de tenir 1 Hz (33,3 s pour 30 tirs).
        ⚠️ Le mapping des capteurs PMLog n'est pas devinable : il se VÉRIFIE par
           deux valeurs invariantes — BUS_LANES doit rendre 16 et CLK_MEMCLK
           ~1990 sur cette carte. `SourceGpuAdl` refuse de servir sinon.
  ram   psutil.virtual_memory() — le % ET LE TOTAL (pas l'utilisé), en GIO
        BINAIRES (2^30). 🔴 CONSTAT OWNER DU 2026-08-18 : en Go décimaux l'écran
        annonçait 34,3 quand le Gestionnaire des tâches de la même machine
        annonçait 31,9 — mêmes octets, deux conventions. Le module est posé à
        côté de la tour : les deux chiffres se lisent côte à côte.
        🔴 LE TOTAL, PAS L'UTILISÉ, ET C'EST STRUCTUREL : le firmware compose
           « 22,7 / 34,2 Go » en calculant utilisé = % x total. Envoyer deux
           nombres échantillonnés séparément afficherait tôt ou tard deux vérités
           contradictoires dans le même rectangle — c'est le motif écrit du mock
           « 12,1 / 32 Go » de dn3-2, et il vaut plus encore pour du réel.
  net   psutil.net_io_counters() — DELTAS de compteurs CUMULÉS / Δt.
        ⛔ `errin`/`errout`/`dropin`/`dropout` NE SONT PAS PUBLIÉS : cette tour
           rend `dropin = 113 558 935 299 979`, une valeur impossible. On regarde
           un compteur avant de le publier.
  disk  psutil.disk_io_counters() — DÉBIT (lecture + écriture), pas occupation.
        W2 tranché PAR LA MESURE, critère écrit AVANT : sur 16 min à 1 Hz, le
        débit change de texte 93,3 % du temps (étendue 268,4 Mo/s) et
        l'occupation 0,0 % (54,9 %, étendue NULLE au dixième de point).
        Une case de six doit BOUGER.

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

import ctypes

PROTO_VERSION = 2
PERIODE_S = 1.0

# ── LES BORNES, MIROIR DE `k_metriques[]` DANS main/dn_link.c ─────────────────
# ⚠️ ELLES SONT RECOPIÉES, ET C'EST UN RISQUE ASSUMÉ ET NOMMÉ : le firmware
#    REJETTE (rejets_bornes) ce qui les dépasse, donc une dérive entre les deux
#    tables se verrait comme un compteur qui monte — pas comme un silence. Le
#    plafond côté agent existe pour ÉCRÊTER PROPREMENT et le DIRE (compteur
#    `ecretages` au bilan), pas pour se substituer au firmware.
# ⛔ Un écrêtage muet serait un mensonge : la valeur affichée ne serait plus la
#    valeur mesurée, et rien ne le signalerait.
BORNES = {
    "cpu": (1000, 1000),        # % · GHz
    "gpu": (1000, 1500),        # % · °C
    "ram": (1000, 40000),       # % · Go TOTAUX
    "net": (1000000, 1000000),  # Mb/s ↓ · Mb/s ↑
    "disk": (1000000, 0),       # Mo/s · (pas de 2e grandeur)
}


def checksum(corps: str) -> str:
    """XOR NMEA des octets du corps (entre '$' exclu et '*' exclu), hex majuscule."""
    ck = 0
    for octet in corps.encode("ascii"):
        ck ^= octet
    return f"{ck:02X}"


def trame(seq: int, t_ms: int, metrique: str, v1: int, v2=None) -> str:
    """Une trame v2. `v2 = None` ⇒ 6 champs : « je ne connais pas v2 » (W10)."""
    corps = f"DN,{PROTO_VERSION},{seq},{t_ms},{metrique},{v1}"
    if v2 is not None:
        corps += f",{v2}"
    return f"${corps}*{checksum(corps)}\n"


# ═════════════════════════════════════════════════════════════════════════════
# LA SOURCE GPU — AMD ADL, EN ctypes, SANS ÉLÉVATION NI DRIVER
# ═════════════════════════════════════════════════════════════════════════════

_ADL_OK = 0
# Indices de l'énumération ADLSensorType du SDK ADL. ⚠️ NON DEVINABLES : ils se
# VÉRIFIENT par deux valeurs invariantes de la carte (voir `_coherent`).
_PM_TEMP_EDGE = 8
_PM_ACTIVITY_GFX = 19
_PM_TEMP_HOTSPOT = 27
_PM_CLK_MEMCLK = 2
_PM_BUS_LANES = 41


class _AdapterInfo(ctypes.Structure):
    _fields_ = [("iSize", ctypes.c_int), ("iAdapterIndex", ctypes.c_int),
                ("strUDID", ctypes.c_char * 256), ("iBusNumber", ctypes.c_int),
                ("iDeviceNumber", ctypes.c_int), ("iFunctionNumber", ctypes.c_int),
                ("iVendorID", ctypes.c_int), ("strAdapterName", ctypes.c_char * 256),
                ("strDisplayName", ctypes.c_char * 256), ("iPresent", ctypes.c_int),
                ("iExist", ctypes.c_int), ("strDriverPath", ctypes.c_char * 256),
                ("strDriverPathExt", ctypes.c_char * 256),
                ("strPNPString", ctypes.c_char * 256),
                ("iOSDisplayIndex", ctypes.c_int)]


class _PMLogOut(ctypes.Structure):
    _fields_ = [("size", ctypes.c_int), ("sensors", (ctypes.c_int * 2) * 256)]


class SourceGpuAdl:
    """% et °C du GPU par `ADL2_New_QueryPMLogData_Get`. UN appel, DEUX grandeurs.

    ⚠️ CETTE CLASSE REFUSE DE SERVIR SI SON MAPPING N'EST PAS CONFIRMÉ. Les
       indices de capteur ne sont pas lisibles dans la DLL : les prendre pour
       argent comptant, c'est risquer de publier la tension du SOC comme une
       température. Le témoin est deux invariants de la carte lus par les MÊMES
       indices : BUS_LANES doit valoir 16 et CLK_MEMCLK ~2000 MHz sur une RX 6800
       XT. Un mapping décalé ne les rendrait pas.
    ⚠️ Cette tour expose SEPT `iAdapterIndex` pour UN SEUL GPU physique (une
       entrée par sortie d'affichage) : on prend le premier qui RÉPOND à PMLog,
       pas « le premier présent » — ce serait un pari.
    """

    def __init__(self):
        self._bufs = []
        self.dll = ctypes.CDLL("atiadlxx.dll")

        @ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_int)
        def _alloc(n):
            b = ctypes.create_string_buffer(n)
            self._bufs.append(b)
            return ctypes.cast(b, ctypes.c_void_p).value

        self._alloc = _alloc  # garder la référence vivante
        self.ctx = ctypes.c_void_p()
        rc = self.dll.ADL2_Main_Control_Create(_alloc, 1, ctypes.byref(self.ctx))
        if rc != _ADL_OK:
            raise RuntimeError(f"ADL2_Main_Control_Create rc={rc}")
        self.adaptateur, self.nom = self._choisir()

    def _adaptateurs(self):
        n = ctypes.c_int(0)
        if self.dll.ADL2_Adapter_NumberOfAdapters_Get(
                self.ctx, ctypes.byref(n)) != _ADL_OK:
            raise RuntimeError("ADL2_Adapter_NumberOfAdapters_Get")
        infos = (_AdapterInfo * max(n.value, 1))()
        if self.dll.ADL2_Adapter_AdapterInfo_Get(
                self.ctx, ctypes.byref(infos), ctypes.sizeof(infos)) != _ADL_OK:
            raise RuntimeError("ADL2_Adapter_AdapterInfo_Get")
        return [infos[i] for i in range(n.value)]

    def _brut(self, idx):
        out = _PMLogOut()
        out.size = ctypes.sizeof(out)
        rc = self.dll.ADL2_New_QueryPMLogData_Get(self.ctx, idx, ctypes.byref(out))
        return out if rc == _ADL_OK else None

    def _choisir(self):
        for a in self._adaptateurs():
            if not a.iPresent:
                continue
            out = self._brut(a.iAdapterIndex)
            if out is None:
                continue
            lanes = out.sensors[_PM_BUS_LANES]
            memclk = out.sensors[_PM_CLK_MEMCLK]
            # LE TÉMOIN DE MAPPING, et il est éliminatoire.
            if not (lanes[0] and lanes[1] in (1, 2, 4, 8, 16, 32)):
                continue
            if not (memclk[0] and 100 <= memclk[1] <= 20000):
                continue
            return a.iAdapterIndex, a.strAdapterName.decode("latin-1", "replace")
        raise RuntimeError(
            "aucun adaptateur ne repond a PMLog avec un mapping COHERENT "
            "(BUS_LANES / CLK_MEMCLK invraisemblables)")

    def temoin(self):
        out = self._brut(self.adaptateur)
        if out is None:
            return None, None
        return out.sensors[_PM_BUS_LANES][1], out.sensors[_PM_CLK_MEMCLK][1]

    def lire(self):
        """Rend (pct, degc) en unités entières, ou (None, None) si l'appel échoue.
        `degc` peut être None seul : c'est le cas W10, et il doit rester possible."""
        out = self._brut(self.adaptateur)
        if out is None:
            return None, None
        act = out.sensors[_PM_ACTIVITY_GFX]
        edge = out.sensors[_PM_TEMP_EDGE]
        return (act[1] if act[0] else None), (edge[1] if edge[0] else None)

    def fermer(self):
        try:
            self.dll.ADL2_Main_Control_Destroy(self.ctx)
        except Exception:
            pass


# ═════════════════════════════════════════════════════════════════════════════
# LE COLLECTEUR — CINQ MÉTRIQUES, UNE PHOTO PAR SECONDE
# ═════════════════════════════════════════════════════════════════════════════


def _dx(valeur, plafond, compteur, nom):
    """Un réel -> DIXIÈMES entiers, borné. Compte et NOMME chaque écrêtage.

    ⛔ Un écrêtage muet serait un mensonge : l'écran afficherait autre chose que
       ce qui a été mesuré, sans que rien ne le dise. Le firmware, lui, rejette
       (rejets_bornes) — les deux bouts sont donc bruyants.
    """
    d = int(valeur * 10 + 0.5)
    if d < 0:
        compteur[nom] = compteur.get(nom, 0) + 1
        return 0
    if d > plafond:
        compteur[nom] = compteur.get(nom, 0) + 1
        return plafond
    return d


class Collecteur:
    """Prend la photo des cinq métriques et rend une liste de trames à émettre.

    ⚠️ LES DÉBITS SONT DES DELTAS DE COMPTEURS CUMULÉS. `psutil` rend des totaux
       depuis le boot : publier le total tel quel afficherait un nombre qui ne
       redescend jamais. Le Δt est mesuré, pas supposé égal à la période — un
       recalage de cadence ou un hoquet d'ordonnanceur fausserait le débit.
    """

    def __init__(self, verbeux=True):
        self.ecretages = {}
        self.gpu = None
        self.gpu_motif = None
        try:
            self.gpu = SourceGpuAdl()
            lanes, memclk = self.gpu.temoin()
            if verbeux:
                print(f"[agent] GPU : {self.gpu.nom} via ADL PMLog "
                      f"(adaptateur {self.gpu.adaptateur}) — temoin de mapping "
                      f"BUS_LANES={lanes} CLK_MEMCLK={memclk} MHz",
                      file=sys.stderr)
        except Exception as exc:
            self.gpu_motif = f"{type(exc).__name__}: {exc}"
            if verbeux:
                # ⚠️ UN MODULE OPTIONNEL NE DOIT PAS BRIQUER L'AGENT — même patron
                #    que `dn_link_init`/`dn_capteurs_init` côté firmware, qui sont
                #    NON FATALES. Sans GPU, les quatre autres métriques vivent.
                print(f"[agent] ⚠️ source GPU INDISPONIBLE ({self.gpu_motif}) — "
                      f"la case GPU restera « -- ». Les quatre autres metriques "
                      f"continuent : une source morte meurt SEULE.", file=sys.stderr)

        psutil.cpu_percent(interval=None)  # amorçage : le 1er appel vaut 0.0
        self._d0 = psutil.disk_io_counters()
        self._n0 = psutil.net_io_counters()
        self._t0 = time.monotonic()

    def reamorcer(self):
        """Après un recalage de cadence : la fenêtre repart PROPRE, comme au
        départ. Sans ça, le premier débit d'après-veille serait calculé sur un
        Δt énorme et rendrait un chiffre FRAIS ET FAUX — le défaut exact que la
        resynchronisation de dn2-2 a corrigé pour le % CPU."""
        psutil.cpu_percent(interval=None)
        self._d0 = psutil.disk_io_counters()
        self._n0 = psutil.net_io_counters()
        self._t0 = time.monotonic()

    def photo(self):
        """Rend [(metrique, v1, v2|None), ...] — v2 None = « je ne sais pas »."""
        t = time.monotonic()
        dt = max(t - self._t0, 1e-6)
        e = self.ecretages
        out = []

        # ── cpu : % + fréquence ──────────────────────────────────────────────
        pct = psutil.cpu_percent(interval=None)
        fr = psutil.cpu_freq()
        # MHz -> dixièmes de GHz, en ENTIER : 3201 MHz -> 32 -> « 3,2 GHz ».
        # ⛔ Pas de flottant sur le fil (doctrine `parse_entier` du firmware).
        ghz_dx = round(fr.current / 100.0) if fr and fr.current else None
        out.append(("cpu", _dx(pct, BORNES["cpu"][0], e, "cpu.pct"),
                    min(ghz_dx, BORNES["cpu"][1]) if ghz_dx is not None else None))

        # ── gpu : % + °C, et l'absence de °C est une DONNÉE (W10) ────────────
        if self.gpu is not None:
            g_pct, g_c = self.gpu.lire()
            if g_pct is not None:
                out.append(("gpu", _dx(g_pct, BORNES["gpu"][0], e, "gpu.pct"),
                            _dx(g_c, BORNES["gpu"][1], e, "gpu.degc")
                            if g_c is not None else None))
            # g_pct None ⇒ ON N'ÉMET RIEN : la case périmera d'elle-même en 3 s
            # et dira « -- ». ⛔ Émettre une valeur inventée serait le mensonge
            # que tout ce projet traque.

        # ── ram : % + TOTAL (pas l'utilisé — voir l'en-tête) ─────────────────
        # 🔴 EN GIO BINAIRES (2^30), PAS EN GO DECIMAUX (1e9) — CONSTAT OWNER DU
        #    2026-08-18, ET C'EST UN DEFAUT D'HONNETETE, PAS UN ARRONDI.
        #    L'ecran affichait « 34,3 Go » pendant que le Gestionnaire des taches
        #    de la MEME machine affichait « 31,9 Go » : memes octets
        #    (34 254 475 264), deux conventions. Windows affiche des GIO et les
        #    etiquette « Go ».
        #    ⚠️ Le module est POSE A COTE DE LA TOUR : les deux chiffres sont lus
        #       cote a cote, tous les jours. Une divergence de 7,4 % entre l'ecran
        #       et sa propre source est exactement le mensonge d'interface que ce
        #       depot traque — en plus discret, parce qu'il a l'air d'un arrondi.
        #    ⚠️ La maquette de l'addendum §1 ecrivait deja « 12.1 / 32 Go », soit
        #       la convention BINAIRE arrondie : la spec etait du cote de Windows.
        #    ⛔ L'ETIQUETTE RESTE « Go » et c'est DELIBERE : c'est ce que Windows
        #       ecrit en francais. Mettre « Gio » serait plus pur et rendrait le
        #       module le SEUL afficheur de la machine a le dire autrement.
        #       La convention est ecrite ici pour que personne ne la « corrige ».
        vm = psutil.virtual_memory()
        out.append(("ram", _dx(vm.percent, BORNES["ram"][0], e, "ram.pct"),
                    _dx(vm.total / 2**30, BORNES["ram"][1], e, "ram.total")))

        # ── net : ↓ et ↑ en Mb/s (BITS — c'est l'unité du descripteur) ───────
        n1 = psutil.net_io_counters()
        rx = (n1.bytes_recv - self._n0.bytes_recv) * 8 / 1e6 / dt
        tx = (n1.bytes_sent - self._n0.bytes_sent) * 8 / 1e6 / dt
        out.append(("net", _dx(max(rx, 0.0), BORNES["net"][0], e, "net.rx"),
                    _dx(max(tx, 0.0), BORNES["net"][1], e, "net.tx")))
        # ⛔ errin/errout/dropin/dropout NE SONT PAS PUBLIÉS : cette tour rend
        #    `dropin = 113 558 935 299 979`, une valeur impossible. On regarde un
        #    compteur avant de le publier.

        # ── disk : DÉBIT total en Mo/s (OCTETS — l'unité d'un disque) ────────
        d1 = psutil.disk_io_counters()
        mo_s = ((d1.read_bytes - self._d0.read_bytes) +
                (d1.write_bytes - self._d0.write_bytes)) / 1e6 / dt
        out.append(("disk", _dx(max(mo_s, 0.0), BORNES["disk"][0], e, "disk"), None))

        self._d0, self._n0, self._t0 = d1, n1, t
        return out

    def fermer(self):
        if self.gpu is not None:
            self.gpu.fermer()


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
        # 🔴 LA PARADE EST **WINDOWS-ONLY**, ET C'EST MESURÉ (session de validation
        # du 2026-08-16, A/B à une variable sur /dev/ttyACM0) :
        #   · AVEC `dtr=False; rts=False` avant open()  -> 6 664 o reçus,
        #     `rst:0x15 (USB_UART_CHIP_RESET)` dans le flux : LA CARTE REDÉMARRE.
        #   · SANS y toucher                            -> 38 o, aucun reboot.
        # Autrement dit, sous Linux la parade PROVOQUE exactement le reset qu'elle
        # prétend empêcher — et `dn_console.py`, qui ne touche jamais ces lignes,
        # n'a jamais reset la carte de toute une session de vingt invocations.
        # Elle reste posée sous Windows, où dn2-2 l'a mesurée nécessaire (pyserial
        # y pose DTR/RTS à l'ouverture et la séquence reset la puce : trois sessions
        # perdues avant le diagnostic). ⚠️ Le côté Windows n'a PAS été re-vérifié
        # depuis WSL — impossible, COM3 n'existe pas quand la carte est attachée.
        if sys.platform == "win32":
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

    # Amorçage deux-temps (le 1er cpu_percent vaut 0.0) + ouverture de la source
    # GPU. ⚠️ NON FATALE : sans GPU, les quatre autres métriques vivent.
    collecteur = Collecteur()

    depart = time.monotonic()
    seq = 0
    erreurs_envoi = 0
    rattrapages = 0
    trames_emises = 0
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
                # ⚠️ dn4-1 : le ré-amorçage couvre MAINTENANT LES CINQ MÉTRIQUES.
                #    Ré-amorcer le seul cpu_percent aurait laissé les DÉBITS
                #    (réseau, disque) se calculer sur un Δt de plusieurs minutes
                #    au premier tour d'après-veille : un chiffre FRAIS ET FAUX,
                #    exactement le défaut que cette resynchronisation corrige.
                collecteur.reamorcer()
                continue  # on ne publie PAS un échantillon pris sur une fenêtre nulle

            # La photo des cinq métriques, prise en UNE fois. La fenêtre des
            # débits et celle du % CPU sont donc la MÊME.
            photo = collecteur.photo()
            t_ms = int((time.monotonic() - depart) * 1000) & 0xFFFFFFFF

            rompu = False
            for metrique, v1, v2 in photo:
                # ⚠️ `seq` numérote les TRAMES, pas les cycles : cinq trames par
                #    seconde consomment cinq seq. C'est ce que le firmware
                #    attend (suivi de seq GLOBAL, jamais par métrique — sinon il
                #    compterait 4 « pertes » à chaque tour de cinq).
                seq += 1
                try:
                    sortie.envoyer(trame(seq, t_ms, metrique, v1, v2))
                    trames_emises += 1
                except BrokenPipeError:
                    # stdout redirigé vers un consommateur qui s'est fermé : boucler en
                    # imprimant une erreur par seconde n'a aucun sens, on sort.
                    print("[agent] stdout ferme par le consommateur — arret",
                          file=sys.stderr)
                    rompu = True
                    break
                except Exception as exc:
                    erreurs_envoi += 1
                    print(f"[agent] envoi {sortie.nom} en échec ({erreurs_envoi}) : {exc}",
                          file=sys.stderr)
            if rompu:
                break

            if args.temoin and (seq // max(len(photo), 1)) % 10 == 0:
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
        _bilan(sortie, depart, trames_emises, erreurs_envoi, rattrapages,
               collecteur)
        collecteur.fermer()
    return 0


def _bilan(sortie, depart: float, seq: int, erreurs_envoi: int, rattrapages: int,
           collecteur=None) -> None:
    """Le récapitulatif — et c'est une MESURE, pas un au revoir.

    ⚠️ Il n'était imprimé qu'en sortie `--duree` : un Ctrl+C (le mode de lancement
    le plus naturel) sortait par le handler KeyboardInterrupt sans jamais l'écrire,
    et le port n'était jamais fermé explicitement. Le chiffre d'AC3 était donc perdu
    sur la majorité des sessions (correctif de revue 2026-08-16).
    """
    mur = max(time.monotonic() - depart, 1e-6)
    print(f"[agent] arrêt après {mur:.1f} s — {seq} trames émises "
          f"({seq / mur:.2f} trames/s), {erreurs_envoi} erreurs d'envoi, "
          f"{rattrapages} recalages de cadence", file=sys.stderr)
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
    if collecteur is not None:
        # ⛔ UN ÉCRÊTAGE NE SORT JAMAIS EN SILENCE. S'il y en a, la valeur
        #    affichée n'est plus la valeur mesurée — c'est une information, pas
        #    un détail d'implémentation.
        if collecteur.ecretages:
            détail = " · ".join(f"{k}={v}" for k, v in
                                sorted(collecteur.ecretages.items()))
            print(f"[agent] 🔴 ECRETAGES (valeur AFFICHEE != valeur MESUREE) : "
                  f"{détail}", file=sys.stderr)
        else:
            print("[agent] aucun ecretage : toute valeur emise est la valeur mesuree",
                  file=sys.stderr)
        if collecteur.gpu is None:
            print(f"[agent] ⚠️ source GPU restee INDISPONIBLE toute la session "
                  f"({collecteur.gpu_motif}) — aucune trame `gpu` emise",
                  file=sys.stderr)


if __name__ == "__main__":
    try:
        sys.exit(principal())
    except KeyboardInterrupt:
        # Filet pour un Ctrl+C AVANT l'entrée dans la boucle (ouverture du port,
        # amorçage psutil) : la boucle, elle, a son propre try/finally qui imprime
        # le bilan et ferme la sortie.
        print("[agent] arrêt demandé (Ctrl+C)", file=sys.stderr)
        sys.exit(0)

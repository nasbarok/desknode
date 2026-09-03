#!/usr/bin/env python3
"""
mesure_grandeurs_dn46 — l'échantillonnage de T6/AC6 et le chrono de T8/AC8.

⚠️ IL TOURNE SUR LE PYTHON **WINDOWS**, comme `dn_agent.py` : `atiadlxx.dll` et
   `psutil` n'existent que là. Depuis WSL :

     powershell.exe -NoProfile -Command "& python \\
       \\\\wsl.localhost\\Ubuntu\\home\\nasbarok\\projects\\desknode\\tools\\mesure_grandeurs_dn46.py \\
       --minutes 16 --csv <chemin>"
 (!) dn5-3 (2026-09-04) -- LA RECETTE CI-DESSUS EST UN EXEMPLE : le chemin UNC
     qu'elle porte est celui de la machine de l'auteur. Le votre s'obtient dans
     WSL par `wslpath -w ~/projects/desknode`. Il n'est PAS generalise : c'est
     ce qu'il faut taper cote Windows, et une recette generalisee a l'aveugle
     ne marche plus.

═══════════════════════════════════════════════════════════════════════════════
CE QU'IL MESURE, ET POURQUOI CHACUN
═══════════════════════════════════════════════════════════════════════════════

1. **`FAN_RPM` (index ADL 14)** — LA question ouverte X1. Son *mouvement* n'a
   jamais été échantillonné. Le critère (C1/C2/C3) est ÉCRIT ET HORODATÉ dans la
   story AVANT ce tir : ⛔ il ne se renégocie pas ici.

2. **`ASIC_POWER` (index 23)** — LE TÉMOIN, pas un bonus. Sa valeur attendue est
   CONNUE (41,4 % de changements, n=29, 2026-08-18). S'il s'effondre lui aussi,
   c'est la SESSION qui est plate, pas le candidat. Sans lui, un `FAN_RPM` à 0 %
   ne dit pas si le capteur est mort ou si la tour ne fait rien.

3. **`max(cpu_percent(percpu=True))`** — la 3ᵉ grandeur du CPU (D11), dont le
   ledger écrivait qu'elle n'existait pas. On la mesure sur la MÊME session.

4. **LE COÛT** de chaque appel, ⚠️ **EN ALTERNANT L'ORDRE** — piège de méthode
   au ledger : « la PREMIÈRE boucle chronométrée d'un processus paie son
   amorçage », et un tir a déjà publié `cpu_percent()` six fois plus cher que
   `percpu`, ce qui est invraisemblable. Ici l'ordre s'inverse à chaque cycle, et
   la première série est publiée SÉPARÉMENT au lieu d'être fondue dans la
   moyenne.

═══════════════════════════════════════════════════════════════════════════════
LES PIÈGES D'INSTRUMENT QU'IL FERME
═══════════════════════════════════════════════════════════════════════════════

⚠️ **Le CSV est écrit avec un compte de champs VÉRIFIÉ à chaque ligne.** Un
   lecteur permissif décale les colonnes EN SILENCE — `csv.DictReader` a déjà
   produit « CPU % max = 1600 » (c'était la fréquence).
⚠️ **Le critère porte sur la valeur AFFICHÉE**, à la résolution réellement
   affichée. Pour `FAN_RPM` c'est l'ENTIER (AC9 a tranché `DN_PREC_ENTIER`) :
   juger le brut mesurerait un bruit que l'écran ne montrera jamais.
⚠️ **Le fichier est vidé (`flush`) à chaque ligne.** Une session de 16 min
   interrompue doit laisser 15 min de données, pas un tampon perdu.
⛔ **Il n'écrit RIEN sur le port série et ne touche pas la carte.** Il peut donc
   tourner PENDANT que la carte est attachée à WSL — l'exclusivité WSL↔COM3 n'est
   pas en jeu.
"""

import argparse
import ctypes
import statistics
import sys
import time

try:
    import psutil
except ImportError:  # pragma: no cover
    print("psutil absent — ce script tourne sur le Python WINDOWS", file=sys.stderr)
    raise

# ── ADL, transposé de `agent/dn_agent.py` ────────────────────────────────────
# ⛔ NE PAS « factoriser » avec l'agent : l'agent est le PRODUIT, ce script est un
#    INSTRUMENT. Les faire dépendre l'un de l'autre ferait qu'une mesure change
#    quand le produit change — et c'est l'inverse de ce qu'on veut.
_ADL_OK = 0
_PM_CLK_MEMCLK = 2
_PM_TEMP_EDGE = 8
_PM_FAN_RPM = 14
_PM_ACTIVITY_GFX = 19
_PM_ASIC_POWER = 23
_PM_TEMP_HOTSPOT = 27
_PM_BUS_LANES = 41
_PM_MAX = 256


# 🔴 LA STRUCTURE EST CELLE DE `dn_agent.py`, AU CHAMP PRÈS — ET C'EST UNE LEÇON
#    PAYÉE À LA PREMIÈRE EXÉCUTION. Ce fichier avait d'abord été écrit avec un
#    en-tête « plausible » (`ulVersion` / `ulActiveSampleRate` / `ulLastUpdated`,
#    16 octets) au lieu du `size` de 4 octets que la DLL attend : tous les
#    indices étaient donc DÉCALÉS de trois entiers.
#    ⚠️ ET LE SYMPTÔME ÉTAIT PLAUSIBLE, PAS ABSURDE : `FAN_RPM` rendait **0**, ce
#       qu'une RX 6800 XT en fan-stop au repos rend VRAIMENT, et `ASIC_POWER`
#       rendait « non supporté ». On était à un cheveu de conclure « FAN_RPM ne
#       qualifie pas » sur un instrument cassé. ⛔ « Un chiffre faux mais
#       PLAUSIBLE est plus dangereux qu'un chiffre absurde. »
#    ⇒ La structure ne se DEVINE pas : elle se RECOPIE de l'appelant qui, lui, a
#      été validé sur la carte (dn4-1, § témoin de cohérence).
class _PMLogOut(ctypes.Structure):
    _fields_ = [("size", ctypes.c_int), ("sensors", (ctypes.c_int * 2) * _PM_MAX)]


class _AdapterInfo(ctypes.Structure):
    _fields_ = [("iSize", ctypes.c_int), ("iAdapterIndex", ctypes.c_int),
                ("strUDID", ctypes.c_char * 256), ("iBusNumber", ctypes.c_int),
                ("iDeviceNumber", ctypes.c_int), ("iFunctionNumber", ctypes.c_int),
                ("iVendorID", ctypes.c_int), ("strAdapterName", ctypes.c_char * 256),
                ("strDisplayName", ctypes.c_char * 256),
                ("iPresent", ctypes.c_int), ("iExist", ctypes.c_int),
                ("strDriverPath", ctypes.c_char * 256),
                ("strDriverPathExt", ctypes.c_char * 256),
                ("strPNPString", ctypes.c_char * 256),
                ("iOSDisplayIndex", ctypes.c_int)]


_ALLOC = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_int)


@_ALLOC
def _alloc(n):
    return ctypes.cast(ctypes.create_string_buffer(n), ctypes.c_void_p).value


_BUFS = []


@_ALLOC
def _alloc_keep(n):
    b = ctypes.create_string_buffer(n)
    _BUFS.append(b)
    return ctypes.cast(b, ctypes.c_void_p).value


class Adl:
    def __init__(self):
        self.dll = ctypes.CDLL("atiadlxx.dll")
        self.ctx = ctypes.c_void_p()
        if self.dll.ADL2_Main_Control_Create(_alloc_keep, 1,
                                             ctypes.byref(self.ctx)) != _ADL_OK:
            raise RuntimeError("ADL2_Main_Control_Create a echoue")
        n = ctypes.c_int(0)
        if self.dll.ADL2_Adapter_NumberOfAdapters_Get(
                self.ctx, ctypes.byref(n)) != _ADL_OK or n.value <= 0:
            raise RuntimeError("aucun adaptateur ADL")
        infos = (_AdapterInfo * n.value)()
        if self.dll.ADL2_Adapter_AdapterInfo_Get(
                self.ctx, infos, ctypes.sizeof(infos)) != _ADL_OK:
            raise RuntimeError("ADL2_Adapter_AdapterInfo_Get a echoue")
        self.idx = None
        for a in infos:
            if a.iPresent:
                self.idx = a.iAdapterIndex
                self.nom = a.strAdapterName.decode("latin-1", "replace").strip()
                break
        if self.idx is None:
            raise RuntimeError("aucun adaptateur PRESENT")

    def lire(self):
        """Rend le dict des capteurs suivis, ou None. UN SEUL appel ADL."""
        out = _PMLogOut()
        out.size = ctypes.sizeof(out)
        if self.dll.ADL2_New_QueryPMLogData_Get(
                self.ctx, self.idx, ctypes.byref(out)) != _ADL_OK:
            return None

        def v(i):
            c = out.sensors[i]
            return c[1] if c[0] else None

        # ⚠️ LE TÉMOIN DE COHÉRENCE EST REJOUÉ À CHAQUE TIR (doctrine de l'agent) :
        #    une mise à jour de pilote peut décaler le mapping en cours de session.
        #    ⛔ Ce n'est PAS la preuve du bon capteur — c'est un garde-fou.
        lanes, memclk = v(_PM_BUS_LANES), v(_PM_CLK_MEMCLK)
        coherent = (lanes is not None and 1 <= lanes <= 16 and
                    memclk is not None and 100 <= memclk <= 5000)
        return {
            "coherent": coherent,
            "lanes": lanes, "memclk": memclk,
            "gfx_pct": v(_PM_ACTIVITY_GFX), "edge_c": v(_PM_TEMP_EDGE),
            "hotspot_c": v(_PM_TEMP_HOTSPOT),
            "asic_w": v(_PM_ASIC_POWER), "fan_rpm": v(_PM_FAN_RPM),
        }


# ── Les critères, RECOPIÉS de la story et NON modifiables par ce script ──────
# ⛔ Ils sont ÉCRITS ET HORODATÉS dans
#    `_bmad-output/implementation-artifacts/dn4-6-…md` à 2026-08-19T11:17:55Z,
#    AVANT ce tir. Les changer ici serait choisir le seuil après avoir vu les
#    chiffres — exactement ce qu'AC6 interdit.
C1_ETENDUE_MIN = 5     # unités AFFICHÉES
C2_TAUX_MIN = 10.0     # % de transitions où le TEXTE change
C3_SIGMA_MIN = 1.0     # unités AFFICHÉES

COLONNES = ["t_s", "fan_rpm", "asic_w", "gfx_pct", "edge_c", "hotspot_c",
            "cpu_pct", "cpu_cmax", "cpu_mhz", "us_pct", "us_percpu", "ordre"]


def juger(nom, textes, unite, attendu=None):
    """Applique C1/C2/C3 à la suite des valeurs AFFICHÉES."""
    vals = [t for t in textes if t is not None]
    if len(vals) < 2:
        print(f"  {nom:<12} ⛔ {len(vals)} echantillon(s) — NON JUGEABLE")
        return False
    etendue = max(vals) - min(vals)
    chg = sum(1 for a, b in zip(vals, vals[1:]) if a != b)
    taux = 100.0 * chg / (len(vals) - 1)
    sigma = statistics.pstdev(vals)
    c1, c2, c3 = (etendue >= C1_ETENDUE_MIN, taux >= C2_TAUX_MIN,
                  sigma >= C3_SIGMA_MIN)
    marque = "✅ QUALIFIE" if (c1 and c2 and c3) else "🔴 NE QUALIFIE PAS"
    print(f"  {nom:<12} n={len(vals):<5} {min(vals)}..{max(vals)} {unite}")
    print(f"     C1 etendue  {etendue:>8.1f} >= {C1_ETENDUE_MIN}   {'OK' if c1 else 'NON'}")
    print(f"     C2 taux     {taux:>7.1f} %% >= {C2_TAUX_MIN} %%  {'OK' if c2 else 'NON'}"
          .replace("%%", "%"))
    print(f"     C3 sigma    {sigma:>8.2f} >= {C3_SIGMA_MIN}   {'OK' if c3 else 'NON'}")
    if attendu is not None:
        print(f"     ⚠️ attendu (2026-08-18, n=29) : {attendu} — "
              f"{'coherent' if abs(taux - attendu) < 25 else '🔴 ECART : la SESSION est suspecte'}")
    print(f"     => {marque}")
    return c1 and c2 and c3


def main():
    # ⚠️ LA CONSOLE WINDOWS EST EN cp1252 PAR DÉFAUT, ET ELLE FAIT TOMBER LE
    #    SCRIPT **APRÈS** LA BOUCLE — c'est-à-dire au moment précis où il publie
    #    son verdict, une session de 16 min déjà consommée. Le CSV, lui, était
    #    intact (chaque ligne est `flush`ée). ⇒ On force UTF-8 sur les deux flux :
    #    un instrument qui meurt en imprimant son résultat est un instrument qui
    #    ne rend rien.
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=16.0)
    ap.add_argument("--csv", default=None)
    a = ap.parse_args()

    adl = Adl()
    print(f"[mesure] adaptateur ADL : {adl.nom}")
    print(f"[mesure] duree {a.minutes:.1f} min a 1 Hz — TOUR EN USAGE NORMAL")
    print(f"[mesure] criteres GELES : C1 >= {C1_ETENDUE_MIN} · "
          f"C2 >= {C2_TAUX_MIN} %% · C3 >= {C3_SIGMA_MIN}".replace("%%", "%"))
    sys.stdout.flush()

    f = open(a.csv, "w", encoding="utf-8", newline="") if a.csv else None
    if f:
        f.write(",".join(COLONNES) + "\n")
        f.flush()

    # ⚠️ AMORÇAGE : le PREMIER `cpu_percent(interval=None)` rend une moyenne
    #    depuis le boot du process, pas depuis le tour précédent. On l'appelle
    #    une fois À VIDE et on ne le publie pas.
    psutil.cpu_percent(interval=None)
    psutil.cpu_percent(interval=None, percpu=True)

    lignes = []
    t0 = time.monotonic()
    fin = t0 + a.minutes * 60.0
    n = 0
    while time.monotonic() < fin:
        cycle = time.monotonic()
        d = adl.lire()

        # ── LE CHRONO, ORDRE ALTERNÉ (piège n°12) ────────────────────────────
        ordre = n % 2
        if ordre == 0:
            t1 = time.perf_counter()
            pct = psutil.cpu_percent(interval=None)
            t2 = time.perf_counter()
            per = psutil.cpu_percent(interval=None, percpu=True)
            t3 = time.perf_counter()
            us_pct, us_per = (t2 - t1) * 1e6, (t3 - t2) * 1e6
        else:
            t1 = time.perf_counter()
            per = psutil.cpu_percent(interval=None, percpu=True)
            t2 = time.perf_counter()
            pct = psutil.cpu_percent(interval=None)
            t3 = time.perf_counter()
            us_per, us_pct = (t2 - t1) * 1e6, (t3 - t2) * 1e6

        try:
            mhz = psutil.cpu_freq().current
        except Exception:
            mhz = None

        ligne = [
            round(time.monotonic() - t0, 3),
            d["fan_rpm"] if d else None,
            d["asic_w"] if d else None,
            d["gfx_pct"] if d else None,
            d["edge_c"] if d else None,
            d["hotspot_c"] if d else None,
            round(pct, 1),
            round(max(per), 1) if per else None,
            round(mhz) if mhz else None,
            round(us_pct, 1), round(us_per, 1), ordre,
        ]
        # ⚠️ LE COMPTE DE CHAMPS EST VÉRIFIÉ, PAS ESPÉRÉ. Un décalage de colonne
        #    est SILENCIEUX à la relecture, et il a déjà produit un chiffre faux
        #    mais plausible (« CPU % max = 1600 », qui était la fréquence).
        assert len(ligne) == len(COLONNES), (
            f"ligne a {len(ligne)} champs pour {len(COLONNES)} colonnes")
        lignes.append(ligne)
        if f:
            f.write(",".join("" if v is None else str(v) for v in ligne) + "\n")
            f.flush()  # une session interrompue laisse ses donnees

        n += 1
        if n % 60 == 0:
            print(f"[mesure] {n} echantillons ({n / 60.0:.0f} min) — "
                  f"fan {ligne[1]} · asic {ligne[2]} W · cmax {ligne[7]} %")
            sys.stdout.flush()

        reste = 1.0 - (time.monotonic() - cycle)
        if reste > 0:
            time.sleep(reste)

    col = {c: [l[i] for l in lignes] for i, c in enumerate(COLONNES)}

    print(f"\n══ RESULTAT — {n} echantillons sur {a.minutes:.1f} min ══")
    print("\nT6 / AC6 — LE CANDIDAT ET SON TEMOIN, juges sur la valeur AFFICHEE :")
    # ⚠️ `FAN_RPM` est juge sur l'ENTIER : AC9 a tranche DN_PREC_ENTIER pour
    #    cette grandeur, et le critere porte sur ce que l'ecran montrera.
    ok_fan = juger("FAN_RPM", [None if v is None else round(v) for v in col["fan_rpm"]],
                   "tr/min")
    ok_asic = juger("ASIC_POWER", [None if v is None else round(v) for v in col["asic_w"]],
                    "W", attendu=41.4)

    print("\nT8 / AC8 — LA 3e GRANDEUR DU CPU (le ledger la disait inexistante) :")
    juger("cpu c.max", [None if v is None else round(v) for v in col["cpu_cmax"]], "%")
    juger("cpu moyen", [None if v is None else round(v) for v in col["cpu_pct"]], "%")

    print("\nT8 / AC8 — LE COUT, ORDRE ALTERNE (la 1re serie est publiee A PART) :")
    # 🔴 UN INSTRUMENT QUI MEURT EN IMPRIMANT SON RESULTAT NE REND RIEN — et
    #    celui-ci mourait (revue de code du 2026-08-19). `prem[0]` levait
    #    `IndexError` sur une session vide, et `statistics.median(reste)` levait
    #    `StatisticsError` des que n <= 1 : la session etait DEJA consommee quand
    #    ca tombait. L'en-tete de ce fichier dit avoir ferme ce mode de
    #    defaillance pour l'ENCODAGE ; il ne l'etait pas pour le COMPTAGE.
    # ⛔ On ne fabrique aucun chiffre : on dit ce qu'on n'a pas.
    for nom, cle in (("cpu_percent()", "us_pct"), ("percpu=True", "us_percpu")):
        v = [x for x in col[cle] if x is not None]
        if not v:
            print(f"  {nom:<16} ⛔ AUCUN echantillon exploitable — rien a publier.")
            continue
        prem, reste = v[:1], v[1:]
        if not reste:
            print(f"  {nom:<16} 1re serie {prem[0]:7.1f} us  |  "
                  f"⚠️ n=1 : PAS de mediane. La 1re boucle chronometree d'un "
                  f"processus paie son amorcage — ce chiffre seul ne vaut rien.")
            continue
        print(f"  {nom:<16} 1re serie {prem[0]:7.1f} us  |  "
              f"n={len(reste)} mediane {statistics.median(reste):7.1f} us  "
              f"max {max(reste):7.1f} us")
    tot = [a_ + b_ for a_, b_ in zip(col["us_pct"], col["us_percpu"])
           if a_ is not None and b_ is not None]
    if len(tot) > 1:
        med = statistics.median(tot[1:])
        print(f"  les DEUX ensemble : mediane {med:.1f} us/cycle "
              f"= {med / 10000.0:.4f} %% d'un coeur a 1 Hz".replace("%%", "%"))
    else:
        print("  les DEUX ensemble : ⛔ moins de 2 cycles complets — le cout "
              "n'est PAS mesure. ⚠️ Relancer avec --minutes plus grand.")

    print("\n══ VERDICT ══")
    if ok_fan:
        print("  ✅ FAN_RPM QUALIFIE — `GPU` reste a QUATRE grandeurs.")
    elif ok_asic:
        print("  🔴 FAN_RPM NE QUALIFIE PAS. Le repli ECRIT D'AVANCE s'applique :")
        print("     ASIC_POWER qualifie ⇒ `GPU` a TROIS (% · °C · W).")
    else:
        print("  ⛔ NI L'UN NI L'AUTRE. ⚠️ ASIC_POWER avait ete mesure a 41,4 % :")
        print("     s'il s'effondre ici, c'est la SESSION qui est plate, pas le")
        print("     capteur. ⇒ REMONTEE OWNER, pas un choix de dev.")
    if f:
        f.close()
        print(f"\n  CSV : {a.csv}  ({n} lignes + en-tete)")


if __name__ == "__main__":
    main()

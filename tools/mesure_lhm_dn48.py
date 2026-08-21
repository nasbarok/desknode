r"""
=============================================================================
 mesure_lhm_dn48.py -- AC2 de dn4-8 : QUELLE INTERFACE LHM, ET COMBIEN ELLE COUTE
=============================================================================

 (!) IL TOURNE SUR LE PYTHON WINDOWS DE LA TOUR, comme dn_agent.py et
     mesure_grandeurs_dn46.py. Depuis WSL :
       powershell.exe -NoProfile -Command "& $env:LOCALAPPDATA\Programs\Python\Python313\python.exe \\wsl.localhost\Ubuntu\home\nasbarok\projects\desknode\tools\mesure_lhm_dn48.py --sonder"

 (!) C'EST UN INSTRUMENT, PAS LE PRODUIT. Meme regle que mesure_grandeurs_dn46 :
     ⛔ NE PAS le factoriser avec dn_agent.py. Les lectures sont VOLONTAIREMENT
     dupliquees ici : une mesure ne doit pas changer quand le produit change.

 ⛔ IL N'ECRIT RIEN SUR LE PORT SERIE et ne touche pas la carte.

 -----------------------------------------------------------------------------
 LE CRITERE EST GELE ET COMMITTE AVANT CE FICHIER (831f619, 2026-08-21T13:30:23Z)
 -----------------------------------------------------------------------------
 C1  CPU median, jeu A (3 grandeurs)  <= 3,0 ms/tir
 C2  CPU median, jeu B (8 grandeurs)  <= 8,0 ms/tir
 C3  mural median, jeu A              <= 100 ms
 C4  mural p95, jeu A                 <= 250 ms
 ⛔ Les seuils NE SE RENEGOCIENT PAS. Ce script les RELIT, il ne les rejuge pas.

 -----------------------------------------------------------------------------
 🔴 ECART DE METHODE N°1, DECLARE -- ⛔ pas un ajustement de seuil
 -----------------------------------------------------------------------------
 `cpu_times()` avance par TICKS de ~15,625 ms : UN TIR DE 3 ms Y EST INVISIBLE.
 C'est ce que dn_agent.py ecrit deja de `cpu_percent()`. On publie donc :
   · MOYENNE DE BLOC (somme des deltas par tir / n) -- LE CHIFFRE QUI DECIDE ;
   · MEDIANE ET p95 DE LOT -- la dispersion, a precision grossiere ;
   · L'ERREUR D'ECHANTILLONNAGE, sqrt(ticks) x 15,625 / n, IMPRIMEE a cote,
     et le verdict REFUSE DE TRANCHER quand l'ecart au seuil est plus petit.
 ⚠️ Le CPU d'un lot s'accumule PAR DELTAS DE TIR, ⛔ pas depuis un instantane de
    debut de lot : entre deux tirs d'un lot, LES AUTRES CANDIDATS TOURNENT.
    (defaut trouve AVANT la 1re campagne)

 -----------------------------------------------------------------------------
 🔴 ECART DE METHODE N°2 -- « SANS VALEUR » N'EST PAS UN ECHEC
    (corrige APRES la campagne n=1000 du 2026-08-21, qui l'avait mal compte)
 -----------------------------------------------------------------------------
 La version precedente comptait en ECHEC un capteur momentanement SANS VALEUR.
 C'ETAIT MON DEFAUT, et il CONTREDISAIT mon propre critere, qui exige justement
 de SAVOIR DISTINGUER « LHM absent » de « sonde absente ».
 MESURE : chaque interface le DIT, et differemment --
     /data.json          la valeur vaut la chaine  "-"
     /Sensor?action=Get  la valeur vaut JSON       null
     /metrics            la ligne du capteur est OMISE (une NaN y devient un
                         commentaire « # HELP ... skipped »)
 ⇒ Une lecture rend desormais `float | None`. `None` = « la source le DIT ».
   C'est exactement W10 (le CHAMP VIDE), et c'est compte a part, ⛔ pas en echec.
   Reste un ECHEC : une exception, ou un compte de valeurs different du demande.

 -----------------------------------------------------------------------------
 🔴 CONNEXION PERSISTANTE -- ⛔ ce n'est PAS deplacer le seuil
 -----------------------------------------------------------------------------
 La campagne n=1000 ouvrait une connexion TCP NEUVE a chaque tir. Un agent reel
 ne ferait pas ca. On mesure donc chaque candidat DANS LES DEUX FORMES, dans la
 MEME campagne alternee : A/B a UNE variable sur l'IMPLEMENTATION du candidat,
 ⛔ pas un amendement du critere.

 -----------------------------------------------------------------------------
 GARDE ANTI-« INSTRUMENT QUI MENT »
 -----------------------------------------------------------------------------
 Un candidat qui echouerait en silence paraitrait le MOINS CHER. Chaque tir doit
 rendre EXACTEMENT le nombre de valeurs demande. Une exception ou un compte faux
 => ECHEC, et le candidat est DISQUALIFIE -- ⛔ jamais « rapide ».
=============================================================================
"""

import argparse
import http.client
import json
import re
import statistics
import sys
import time
import urllib.parse
import urllib.request

HOTE, PORT = "localhost", 8085
BASE = "http://%s:%d" % (HOTE, PORT)

# --- Les deux jeux, au sens du critere ---------------------------------------
# (!) QUEL ventilateur est le boitier et lequel le CPU est AC3, ⛔ pas AC2.
TEMP_CPU = "/intelcpu/0/temperature/10"          # CPU Package
FANS_SIO = ["/lpc/nct6792d/0/fan/%d" % i for i in range(6)]
FAN_GPU = "/gpu-amd/0/fan/0"

JEU_A = [TEMP_CPU, FANS_SIO[0], FANS_SIO[2]]      # 3 grandeurs -- le besoin FERME
JEU_B = [TEMP_CPU] + FANS_SIO + [FAN_GPU]         # 8 grandeurs -- le majorant dn4-9
JEUX = {"A": JEU_A, "B": JEU_B}


# ============================================================================
# LES DEUX TRANSPORTS -- l'A/B a une variable
# ============================================================================
def get_neuf(chemin):
    """Une connexion TCP NEUVE a chaque tir (ce que faisait la campagne n=1000)."""
    with urllib.request.urlopen(BASE + chemin, timeout=10.0) as r:
        return r.read().decode("utf-8", "replace")


class GetPersistant:
    """Connexion gardee ouverte. Se reconnecte UNE fois si elle est tombee --
    ⛔ sans quoi une coupure ferait passer le candidat pour defaillant."""

    def __init__(self):
        self.c = None

    def __call__(self, chemin):
        for dernier in (False, True):
            try:
                if self.c is None:
                    self.c = http.client.HTTPConnection(HOTE, PORT, timeout=10.0)
                self.c.request("GET", chemin, headers={"Connection": "keep-alive"})
                rep = self.c.getresponse()
                corps = rep.read()
                if rep.will_close:
                    self.c.close()
                    self.c = None
                return corps.decode("utf-8", "replace")
            except Exception:
                try:
                    if self.c:
                        self.c.close()
                except Exception:
                    pass
                self.c = None
                if dernier:
                    raise


# ============================================================================
# CANDIDAT 1 -- /data.json
# ⚠️ En 0.9.6, `Value` ET `RawValue` sont des CHAINES LOCALISEES : « 41,0 °C ».
#    Le desossage de la locale FAIT PARTIE DU COUT, et c'est voulu.
# ⚠️ Une valeur absente s'y ecrit "-" => None, ⛔ pas une erreur.
# ============================================================================
_NOMBRE = re.compile(r"-?\d+(?:[.,]\d+)?")


def _delocaliser(txt):
    if txt is None:
        return None
    m = _NOMBRE.search(txt)
    if not m:
        return None          # « - » : la source DIT qu'elle n'a pas de valeur
    return float(m.group(0).replace(",", "."))


def lire_data_json(get, ids):
    doc = json.loads(get("/data.json"))
    voulus = set(ids)
    trouve = {}
    pile = [doc]
    while pile:
        n = pile.pop()
        sid = n.get("SensorId")
        if sid in voulus:
            trouve[sid] = _delocaliser(n.get("Value"))
        pile.extend(n.get("Children") or ())
    return [trouve.get(i) for i in ids]


# ============================================================================
# CANDIDAT 2 -- /metrics
# ✅ Vrais flottants, point decimal, unites de base (InvariantCulture).
# ⚠️ Un capteur NaN n'a PAS de ligne : son absence de la table = None.
# ============================================================================
_LIGNE = re.compile(
    r'^lhm_\S+\s+\{.*?"sensorId"="([^"]*)".*?"hardwareId"="([^"]*)".*?\}\s+(\S+)\s*$'
)


def _fini(x):
    """`True` si `x` est un flottant FINI (⛔ ni NaN ni inf). Miroir du produit."""
    return x == x and x not in (float("inf"), float("-inf"))


def lire_metrics(get, ids):
    txt = get("/metrics")
    table = {}
    for ligne in txt.splitlines():
        if not ligne.startswith("lhm_"):
            continue
        m = _LIGNE.match(ligne)
        if not m:
            continue
        # 🔴 GARDE `_fini` AJOUTEE EN REVUE (code review dn4-8, 2026-08-21).
        #    SANS ELLE, LES TROIS CANDIDATS N'ETAIENT PAS JUGES PAR LA MEME REGLE,
        #    DANS L'A/B QUI A CHOISI L'INTERFACE. L'en-tete de ce fichier pose la
        #    regle : « None = la source le DIT ; reste un ECHEC : une exception,
        #    ou un compte de valeurs different du demande ».
        #      · `lire_data_json` l'honore (`_delocaliser("-") -> None`)
        #      · `lire_sensor`    l'honore (`None if v is None`)
        #      · `lire_metrics`   faisait `float(...)` NU : un litteral `NaN`
        #        rendait `nan`, `_juger` repondait « valeur non finie », donc
        #        ECHEC, donc DISQUALIFIE.
        #    ⇒ La MEME condition physique etait « sans valeur » pour deux
        #      candidats et disqualifiante pour le troisieme : PLUS D'UNE VARIABLE
        #      dans un A/B dont la sortie a ferme AC2.
        # ⚠️ Et le produit (`dn_agent.SourceLhm`) A cette garde : l'instrument
        #    etait donc PLUS STRICT que le code qu'il a certifie.
        try:
            v = float(m.group(3))
        except ValueError:
            continue                 # ligne illisible = capteur absent de la table
        if not _fini(v):
            continue                 # NaN/inf = « la source n'a pas de valeur »
        table[m.group(2) + m.group(1)] = v
    return [table.get(i) for i in ids]


# ============================================================================
# CANDIDAT 3 -- /Sensor?action=Get, UNE REQUETE PAR CAPTEUR
# 🎯 C'est LUI qui monte lineairement en N : tout l'objet du jeu B.
# ⚠️ Une valeur absente y vaut JSON null => None.
# ============================================================================
def lire_sensor(get, ids):
    out = []
    for i in ids:
        d = json.loads(get("/Sensor?action=Get&id=" + urllib.parse.quote(i, safe="/")))
        v = d.get("value")
        out.append(None if v is None else float(v))
    return out


LECTEURS = [("data.json", lire_data_json),
            ("metrics", lire_metrics),
            ("sensor_xN", lire_sensor)]


def batir_combos():
    """Chaque lecteur x chaque transport x chaque jeu. Le transport persistant a
    SON PROPRE etat par combinaison : deux combinaisons ne partagent PAS une
    connexion, sinon on mesurerait le voisin."""
    combos = []
    for nom, fn in LECTEURS:
        for tr in ("neuf", "keepalive"):
            for jeu in ("A", "B"):
                get = get_neuf if tr == "neuf" else GetPersistant()
                combos.append(("%s/%s" % (nom, tr), nom, get, jeu, JEUX[jeu], fn))
    return combos


# ============================================================================
# 🔴 LE HANDLE EST CONSTRUIT **UNE FOIS**, HORS DES FENETRES MESUREES.
#    Defaut trouve en revue (2026-08-21) : `_cpu_ms()` faisait
#    `psutil.Process().cpu_times()`, donc un `Process()` NEUF a chaque appel —
#    sous Windows un `OpenProcess` + `GetProcessTimes` pour `create_time()`. Pour
#    l'appel de FIN (`c1`), cette construction tombe AVANT sa propre lecture,
#    donc SON COUT ENTRE DANS LA FENETRE `c0 -> c1` et s'ajoute a CHAQUE tir.
# ⛔ Et le verdict se joue contre des seuils ABSOLUS (C1 <= 3,0 ms ; les gagnants
#    keep-alive etaient a 1,13-2,19 ms). Un biais additif constant deplace donc
#    directement la ligne succes/echec, meme s'il s'annule dans les deltas A/B.
import psutil as _psutil  # noqa: E402
_MOI = _psutil.Process()


def _cpu_ms():
    """CPU cumule du processus, en ms. ⛔ PAS cpu_percent : voir l'en-tete."""
    t = _MOI.cpu_times()
    return (t.user + t.system) * 1000.0


def _juger(vals, ids):
    """(bon, nb_sans_valeur, cause). « sans valeur » n'est PAS un echec."""
    if not isinstance(vals, list) or len(vals) != len(ids):
        return False, 0, "compte de valeurs faux: %d attendu %d" % (
            len(vals) if isinstance(vals, list) else -1, len(ids))
    sv = 0
    for v in vals:
        if v is None:
            sv += 1
        elif not (isinstance(v, float) and v == v and abs(v) != float("inf")):
            return False, sv, "valeur non finie: %r" % (v,)
    return True, sv, None


def sonder():
    print("=== SONDAGE (n=1 par combinaison) -- ⛔ AUCUNE CONCLUSION N'EN SORT ===")
    combos = batir_combos()
    total = 0.0
    for etiq, _nom, get, jeu, ids, fn in combos:
        t0 = time.perf_counter()
        try:
            vals = fn(get, ids)
            d = (time.perf_counter() - t0) * 1000.0
            bon, sv, cause = _juger(vals, ids)
            print("  %-20s jeu %s (%d) : %7.1f ms  %-5s s.val=%d  %s"
                  % (etiq, jeu, len(ids), d, "OK" if bon else "ECHEC", sv,
                     cause or " ".join("--" if v is None else "%.4g" % v for v in vals)))
        except Exception as e:
            d = (time.perf_counter() - t0) * 1000.0
            print("  %-20s jeu %s (%d) : %7.1f ms  EXCEPTION %s: %s"
                  % (etiq, jeu, len(ids), d, type(e).__name__, str(e)[:80]))
        total += d
    print("  ---")
    print("  duree d'UN TOUR complet (%d combinaisons) : %.0f ms" % (len(combos), total))


def campagne(n, lot, periode, jeter):
    combos = batir_combos()
    cles = [(c[0], c[3]) for c in combos]
    murs = {k: [] for k in cles}
    lots_cpu = {k: [] for k in cles}
    bloc_cpu = {k: 0.0 for k in cles}
    lot_cpu = {k: 0.0 for k in cles}
    bloc_n = {k: 0 for k in cles}
    echecs = {k: 0 for k in cles}
    sans_val = {k: 0 for k in cles}
    causes = {k: {} for k in cles}
    depassements = 0

    print("=== CAMPAGNE ===")
    print("  n=%d tirs par combinaison · lots de %d · periode %.2f s · %d combinaisons"
          % (n, lot, periode, len(combos)))
    print("  %d premiers tours JETES (amorcage : TCP, JIT, 1er sondage LHM)" % jeter)
    print("  ORDRE ALTERNE : la rotation avance d'un cran a chaque tour.")
    t_debut = time.perf_counter()

    for tour in range(n + jeter):
        t_tour = time.perf_counter()
        r = tour % len(combos)
        for etiq, _nom, get, jeu, ids, fn in combos[r:] + combos[:r]:
            cle = (etiq, jeu)
            c0 = _cpu_ms()
            t0 = time.perf_counter()
            sv = 0
            try:
                vals = fn(get, ids)
                mur = (time.perf_counter() - t0) * 1000.0
                bon, sv, cause = _juger(vals, ids)
            except Exception as e:
                mur = (time.perf_counter() - t0) * 1000.0
                bon = False
                cause = "%s: %s" % (type(e).__name__, str(e)[:100])
            c1 = _cpu_ms()
            if tour < jeter:
                continue
            if not bon:
                echecs[cle] += 1
                causes[cle][cause] = causes[cle].get(cause, 0) + 1
            sans_val[cle] += sv
            # 🔴 ⛔ LES TIRS EN ECHEC N'ENTRENT PLUS DANS `murs` (revue 2026-08-21).
            #    C3/C4 sont « mur median » et « mur p95 » : les calculer sur un
            #    MELANGE de succes et d'exceptions compare des durees qui ne
            #    mesurent pas la meme chose — une exception peut sortir en 0,1 ms
            #    (connexion refusee) et tirer la mediane vers le bas, ou en
            #    plusieurs secondes (timeout) et la tirer vers le haut. Les deux
            #    faussent, dans des sens opposes.
            # ⚠️ Le compte d'echecs est deja publie separement : rien n'est perdu.
            if bon:
                murs[cle].append(mur)
            d = c1 - c0
            bloc_cpu[cle] += d
            lot_cpu[cle] += d
            bloc_n[cle] += 1
            if bloc_n[cle] % lot == 0:
                lots_cpu[cle].append(lot_cpu[cle] / lot)
                lot_cpu[cle] = 0.0
        reste = periode - (time.perf_counter() - t_tour)
        if reste > 0:
            time.sleep(reste)
        else:
            depassements += 1
        if (tour + 1) % 100 == 0:
            print("  ... tour %d/%d" % (tour + 1, n + jeter))

    print("  campagne finie en %.0f s" % (time.perf_counter() - t_debut))
    if depassements:
        print("  /!\\ %d tour(s) ont DEPASSE la periode : cadence non tenue, et c'est ecrit."
              % depassements)

    def p95(xs):
        xs = sorted(xs)
        return xs[min(len(xs) - 1, int(round(0.95 * (len(xs) - 1))))]

    def err(cle):
        t = bloc_cpu[cle] / 15.625
        return (t ** 0.5) * 15.625 / bloc_n[cle] if t > 0 and bloc_n[cle] else float("nan")

    print()
    print("=== RESULTATS ===")
    print("  %-20s %-3s %6s | %9s %9s | %7s %7s | %5s %s"
          % ("candidat/transport", "jeu", "n", "CPU/tir", "err +-", "mur md", "mur p95",
             "s.val", "echecs"))
    print("  " + "-" * 104)
    res = {}
    for etiq, _nom, _g, jeu, _ids, _fn in combos:
        cle = (etiq, jeu)
        if bloc_n[cle] == 0:
            continue
        # ⛔ CONSEQUENCE DIRECTE DE `murs` FILTRE SUR LES SUCCES (revue 2026-08-21) :
        #    un candidat qui echoue A TOUS LES TIRS n'a plus AUCUNE duree. On le
        #    DIT — ⛔ on ne fabrique pas une mediane sur rien, et ⛔ on ne le fait
        #    pas disparaitre du tableau, ce qui le ferait passer pour non teste.
        if not murs[cle]:
            print("  %-20s %-3s %6d | %8s  %8s  | %6s  %6s  | %5d %d   "
                  "⛔ AUCUN TIR REUSSI : aucune duree n'est publiable"
                  % (etiq, jeu, bloc_n[cle], "--", "--", "--", "--",
                     sans_val[cle], echecs[cle]))
            continue
        res[cle] = dict(cpu=bloc_cpu[cle] / bloc_n[cle], err=err(cle),
                        mur_md=statistics.median(murs[cle]), mur_p95=p95(murs[cle]),
                        sv=sans_val[cle], ech=echecs[cle], n_mur=len(murs[cle]))
        x = res[cle]
        print("  %-20s %-3s %6d | %8.3f  %8.3f  | %6.1f  %6.1f  | %5d %d"
              % (etiq, jeu, bloc_n[cle], x["cpu"], x["err"], x["mur_md"],
                 x["mur_p95"], x["sv"], x["ech"]))
        # ⚠️ Les durees ne portent QUE sur les tirs reussis : le dire, sinon le
        #    lecteur croit que `n` et le nombre de durees sont le meme nombre.
        if len(murs[cle]) != bloc_n[cle]:
            print("  %-20s %-3s   (durees sur %d tir(s) REUSSI(S) sur %d — les "
                  "echecs sont exclus des medianes)"
                  % ("", "", len(murs[cle]), bloc_n[cle]))

    if any(causes[k] for k in causes):
        print()
        print("=== CAUSES DES ECHECS -- ⛔ un echec sans sa cause n'est pas un resultat ===")
        for k in causes:
            for c, q in sorted(causes[k].items(), key=lambda x: -x[1]):
                print("  %-20s %-3s x%-4d %s" % (k[0], k[1], q, c))

    print()
    print("=== A/B DU TRANSPORT -- une seule variable ===")
    for nom, _fn in LECTEURS:
        for jeu in ("A", "B"):
            a = res.get(("%s/neuf" % nom, jeu))
            b = res.get(("%s/keepalive" % nom, jeu))
            if not a or not b:
                continue
            d = a["cpu"] - b["cpu"]
            e = (a["err"] ** 2 + b["err"] ** 2) ** 0.5
            v = ("gain %+.3f ms" % d) if abs(d) > e else "⛔ NON DISCRIMINANT"
            print("  %-10s jeu %s : neuf %6.3f -> keepalive %6.3f  (%s, erreur combinee %.3f)"
                  % (nom, jeu, a["cpu"], b["cpu"], v, e))

    print()
    print("=== VERDICT CONTRE LE CRITERE GELE (831f619) ===")
    print("  ⛔ Seuils RELUS, ⛔ pas rejuges. ⛔ « sans valeur » n'est PAS un echec.")
    for etiq in sorted({c[0] for c in combos}):
        a, b = res.get((etiq, "A")), res.get((etiq, "B"))
        if not a or not b:
            continue
        if a["ech"] or b["ech"]:
            print("  %-20s : DISQUALIFIE -- %d+%d tir(s) en ECHEC (⛔ pas 'sans valeur')"
                  % (etiq, a["ech"], b["ech"]))
            continue
        for lib, val, seuil, e in (("C1 CPU jeu A <= 3,0", a["cpu"], 3.0, a["err"]),
                                   ("C2 CPU jeu B <= 8,0", b["cpu"], 8.0, b["err"]),
                                   ("C3 mur md A  <= 100", a["mur_md"], 100.0, 0.0),
                                   ("C4 mur p95 A <= 250", a["mur_p95"], 250.0, 0.0)):
            etat = "OK" if val <= seuil else "DEPASSE"
            note = ""
            if e and abs(val - seuil) < e:
                note = "   ⛔ NON DISCRIMINANT (ecart %.2f < erreur %.2f)" % (abs(val - seuil), e)
            print("  %-20s %-22s %8.3f  %s%s" % (etiq, lib, val, etat, note))


def main():
    # (!) Console Windows en cp1252 jusqu'a Python 3.14 : sans ca, un caractere
    #     hors table fait CRASHER l'instrument au premier print. Remede repris
    #     de dn_agent.py, qui le documente deja.
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8")
        except Exception:
            pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--sonder", action="store_true")
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--lot", type=int, default=50)
    ap.add_argument("--periode", type=float, default=1.0)
    ap.add_argument("--jeter", type=int, default=5)
    a = ap.parse_args()
    try:
        import psutil  # noqa: F401
    except ImportError:
        print("psutil manquant : pip install --user psutil (l'instrument en depend, pas l'agent)")
        return 2
    sonder() if a.sonder else campagne(a.n, a.lot, a.periode, a.jeter)
    return 0


if __name__ == "__main__":
    sys.exit(main())

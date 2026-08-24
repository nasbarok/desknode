#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mesure_w2_dn48.py — la qualification W2 des QUATRE grandeurs LHM (AC4).

🔴 CRITERE GELE ET HORODATE LE 2026-08-21T18:09:35Z, COMMITTE EN `c377d2c`,
   ⛔ AVANT QUE CE FICHIER N'EXISTE. Les seuils ci-dessous sont RECOPIES de la
   story ; ⛔ ils ne se renegocient pas, et une divergence entre les deux se
   verrait ici (ils sont ecrits en toutes lettres dans les deux endroits).

🔴 IL NE DEPEND PAS DE `dn_agent.py`, ET C'EST LA DOCTRINE DU DEPOT :
   « l'agent est le PRODUIT, ce script est un INSTRUMENT. Les faire dependre
   l'un de l'autre ferait qu'une mesure change quand le produit change. »
   ⇒ il relit `/metrics` lui-meme. 🎯 Et c'est PLUS correct : ce qu'on
   qualifie est le MOUVEMENT DE LA SOURCE, ⛔ pas le code de l'agent.

⚠️ IL NE TOUCHE PAS AU PORT SERIE : il peut donc tourner pendant que la carte est
   attachee a WSL. C'est deja la propriete de `mesure_grandeurs_dn46.py`.

🔴 CE QUI EST JUGE EST LA VALEUR **AFFICHEE**, ⛔ PAS LA BRUTE :
   · `cpu.degc`  -> DIXIEME de °C   (DN_PREC_DIXIEME)
   · les tr/min  -> ENTIER          (DN_PREC_ENTIER)
   Une meme source qualifie ou non selon sa precision d'affichage.

Usage (Python Windows de la tour) :
    python mesure_w2_dn48.py --minutes 16 --csv w2_dn48.csv
    python mesure_w2_dn48.py --rejuger w2_dn48.csv      # re-juge SANS re-tirer
"""
import argparse
import http.client
import io
import os
import re
import statistics
import sys
import time

HOTE, PORT, CHEMIN = "127.0.0.1", 8085, "/metrics"

# ── LES SONDES — LUES DANS LA TABLE DE L'AGENT, ⛔ PLUS RECOPIEES ────────────
# 🔴 Ce bloc portait les cinq identifiants EN DUR, avec sa propre mise en garde :
#    « RECOPIE ASSUMEE ET NOMMEE : si l'agent change de sonde sans le dire ici, la
#    qualification porterait sur AUTRE CHOSE que ce qui circule ». Le risque etait
#    donc CONNU et laisse ouvert. Maintenant que ce fichier importe le produit
#    (voir `affichee()` plus bas), il n'y a plus de raison de le courir.
#    ⇒ les identifiants sont DERIVES de `dn_agent.LHM_SONDES`. (revue 2026-08-21)
# ⚠️ Definis apres l'import du produit, plus bas — ⛔ pas ici.

# ── LES SEUILS GELES (story dn4-8, 2026-08-21T18:09:35Z, commit c377d2c) ────
# \U0001f534 AMENDE LE 2026-08-21T18:25:17Z — C2 ETAIT LE PLAFOND LUI-MEME.
#    LHM rafraichit toutes les **4,00 s** (MESURE : 785 lectures a 10 Hz sur 90 s,
#    quatre grandeurs, mediane 4,00-4,01 s). ⇒ a 1 Hz d'echantillonnage, le taux
#    de changement du texte est PLAFONNE A 1/4 = 25,0 %. Or C2 pour la degC etait
#    gele a 25 % : EXACTEMENT LE PLAFOND, donc INATTEIGNABLE, donc incapable de
#    discriminer.
# ⛔ ET LE MOTIF QUE J'AVAIS ECRIT ETAIT FAUX : « la resolution est 10x plus fine,
#    le texte change bien plus souvent ». NON — la resolution ne peut pas faire
#    changer le texte plus souvent que LA SOURCE NE SE RAFRAICHIT.
# ⇒ C2 EST DESORMAIS RELATIF AU PLAFOND MESURE : « le texte change a >= 60 % des
#   OCCASIONS OU IL POUVAIT CHANGER ». \U0001f3af Independant de la cadence
#   d'echantillonnage, donc comparable si LHM ou l'agent changeaient de rythme.
# ⚠️ Amendement OWNER, DATE, POSTERIEUR a la mesure, motive par une FAUTE DE
#    RAISONNEMENT DE L'AGENT — ⛔ pas par un resultat qui deplaisait. Meme
#    traitement que le critere 6 d'AC2.
# ⛔ C1 ET C3 NE BOUGENT PAS : seul C2 etait fautif.
C2_OCCASIONS_MIN = 60.0     # % des occasions, ⛔ pas % des echantillons
SEUILS = {
    # famille    C1 etendue, C3 sigma, unite, precision
    "degc":  (3.0, 0.5, "degC", "dixieme"),
    "rpm":   (5.0, 1.0, "tr/min", "entier"),
}
GRANDEURS = [
    ("cpu.degc",            "degc"),
    ("disk.extraction_moy", "rpm"),
    ("disk.cpu_noctua",     "rpm"),
    ("disk.case_group",     "rpm"),
]
COLONNES = ["t_s", "cpu.degc", "disk.extraction_moy", "disk.cpu_noctua",
            "disk.case_group", "fan.top_out", "fan.rear_out"]

# ⚠️ La famille est CAPTUREE (groupe 1) — miroir de `_LHM_LIGNE` du produit.
_LIGNE = re.compile(
    r'^(lhm_\S+)\s+\{.*?"sensorId"="([^"]*)".*?"hardwareId"="([^"]*)".*?\}'
    r'\s+(\S+)\s*$')


class Lhm(object):
    """Connexion PERSISTANTE — l'ouverture TCP dominait le cout (AC2)."""

    def __init__(self):
        self.c = None

    def lire(self):
        for dernier in (False, True):
            try:
                if self.c is None:
                    self.c = http.client.HTTPConnection(HOTE, PORT, timeout=5.0)
                self.c.request("GET", CHEMIN, headers={"Connection": "keep-alive"})
                r = self.c.getresponse()
                b = r.read()
                if r.will_close:
                    self.c.close(); self.c = None
                t = {}
                for l in b.decode("utf-8", "replace").splitlines():
                    if not l.startswith("lhm_"):
                        continue
                    m = _LIGNE.match(l)
                    if not m:
                        continue
                    try:
                        v = float(m.group(4))
                    except ValueError:
                        continue
                    if v != v or v - v != 0:      # NaN / +-inf
                        continue
                    ident = m.group(3) + m.group(2)
                    # 🔴 L'UNITE VIT DANS LE NOM DE FAMILLE, et c'est la raison
                    #    pour laquelle `/metrics` a ete retenu contre
                    #    `/data.json`. Cet instrument la VERIFIE maintenant :
                    #    juger une qualification sur une grandeur dont l'unite a
                    #    change en cours de campagne serait un verdict sur autre
                    #    chose. (revue dn4-8, 2026-08-21)
                    att = _FAMILLE_ATTENDUE.get(ident)
                    if att is not None and m.group(1) != att:
                        # 🔴 2e REVUE (2026-08-24) — « SESSION JETEE » NE JETAIT
                        #    RIEN. Ce `raise` est A L'INTERIEUR du `try` de la
                        #    boucle de reconnexion `for dernier in (False, True)`:
                        #    il etait donc (a) rattrape par l'`except Exception`
                        #    ci-dessous, la connexion fermee, LA LECTURE RETENTEE ;
                        #    puis (b) au 2e passage il remontait dans
                        #    `except Exception as exc: pannes += 1`, qui n'imprime
                        #    que `type(exc).__name__` — LE TEXTE QUI PORTE LE
                        #    DIAGNOSTIC ETAIT JETE — et la session CONTINUAIT
                        #    jusqu'au bout, puis publiait un verdict W2 sur la
                        #    moitie d'avant le renommage. A partir du 2e evenement,
                        #    `if pannes == 1` faisait qu'il ne s'imprimait plus RIEN.
                        # ⇒ EXCEPTION DEDIEE : elle traverse la reconnexion ET la
                        #   boucle de tir, et elle ABORTE. Une session dont l'unite
                        #   a change en cours de route n'est pas une session.
                        raise UniteChangee(
                            "⛔ SESSION JETEE : `%s` arrive en famille `%s` au "
                            "lieu de `%s` — L'UNITE A CHANGE. Un verdict W2 sur "
                            "cette grandeur porterait sur autre chose."
                            % (ident, m.group(1), att))
                    t[ident] = v
                return t
            except UniteChangee:
                # ⛔ ON NE RETENTE PAS : rien ne se repare en relisant.
                try:
                    if self.c:
                        self.c.close()
                except Exception:
                    pass
                self.c = None
                raise
            except Exception:
                try:
                    if self.c:
                        self.c.close()
                except Exception:
                    pass
                self.c = None
                if dernier:
                    raise



class UniteChangee(Exception):
    """L'unite d'une sonde a change EN COURS DE SESSION.

    ⛔ CE N'EST PAS UNE PANNE DE LECTURE, et ca ne se retente pas : les
       echantillons d'avant et d'apres ne mesurent pas la meme chose. Exception
       DEDIEE pour qu'elle traverse la boucle de reconnexion sans etre avalee —
       defaut trouve en 2e revue, 2026-08-24.
    """


# 🔴 LE PRODUIT EST IMPORTE, ⛔ SA QUANTIFICATION N'EST PLUS RECOPIEE.
#    Defaut trouve en revue (code review dn4-8, 2026-08-21) : `affichee()`
#    s'ecrivait `round(v, 1)` / `float(int(round(v)))`. Or `round()` de Python
#    arrondit AU PAIR (banquier) tandis que le produit fait `int(v*10 + 0.5)`
#    (`dn_agent._dx`) puis le firmware `(mag + 5) / 10` — DEMI-HAUT tous les deux.
#    Le capteur Intel a une grille native de 0,25 degC (fixture : 40,875 · 35,5625
#    · 62,75 · 41 ...), donc UN ECHANTILLON SUR DEUX tombe sur une egalite :
#    40,25 -> instrument 40,2 / produit 40,3.
# ⛔ ET C2 EST UN TAUX DE CHANGEMENT DE **TEXTE** : c'est la statistique la PLUS
#    sensible qui soit a ces egalites. Le harnais jugeait donc une valeur que la
#    dalle n'ecrit jamais, sur la moitie de l'espace des echantillons — alors que
#    sa propre docstring dit « CE QUI EST JUGE EST LA VALEUR AFFICHEE ».
# ⚠️ Famille maison : « un harnais qui REJOUE au lieu d'EXTRAIRE et d'APPELER ».
# ⚠️ IMPORTER LE PRODUIT TIRE SA DEPENDANCE `psutil`, et `dn_agent` SORT si elle
#    manque. Cet outil tourne sur LA TOUR, ou psutil est installe — mais il doit
#    rester REPETABLE en WSL. ⇒ si psutil manque, on arme le stub, ET ON LE DIT.
# ⛔ AUCUN nombre de psutil n'entre dans ce que cet outil mesure : seule
#    `dn_agent._dx()` est utilisee, et elle est PUREMENT ARITHMETIQUE. Le stub ne
#    peut donc pas contaminer un verdict d'AC4.
_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    import psutil as _p  # noqa: F401
except ImportError:
    os.environ["DN_STUB_PSUTIL"] = "1"
    sys.path.insert(0, os.path.join(_RACINE, "tools", "stub_psutil"))
    print("[w2] ⚠️ psutil ABSENT ⇒ stub arme POUR L'IMPORT SEULEMENT. ⛔ Aucune "
          "valeur psutil n'entre dans ce que cet outil juge.")
sys.path.insert(0, os.path.join(_RACINE, "agent"))
import dn_agent  # noqa: E402  -- LE PRODUIT (pour `_dx`, la quantification REELLE)

# 🎯 LES SONDES, DERIVEES DE LA TABLE DU PRODUIT. Si l'agent change un
#    identifiant, cet instrument SUIT — ⛔ il ne qualifie plus une autre grandeur
#    sous la meme etiquette. Et la 4e colonne donne la FAMILLE attendue, donc
#    l'unite : un `..._celsius` devenu `..._fahrenheit` est REFUSE ici aussi.
_PAR_CLE = {c: (ident, fam) for c, ident, fam, _prov in dn_agent.LHM_SONDES}
TEMP_CPU = _PAR_CLE["cpu.degc"][0]
FAN_TOP = _PAR_CLE["fan.top_out"][0]
FAN_NOCTUA = _PAR_CLE["fan.cpu_noctua"][0]
FAN_CASE = _PAR_CLE["fan.case_group"][0]
FAN_REAR = _PAR_CLE["fan.rear_out"][0]
_FAMILLE_ATTENDUE = {ident: fam for ident, fam in _PAR_CLE.values()}


def affichee(v, precision, borne=None):
    """La valeur telle que la DALLE l'ecrirait. ⛔ C'est elle qu'on juge.

    Chaine COMPLETE et REELLE : `dn_agent._dx()` (reel -> dixiemes entiers, ce qui
    circule sur le fil) puis l'arrondi du firmware `fmt_grandeur()` pour la
    precision demandee. ⛔ Aucune de ces deux etapes n'est reimplementee ici.
    """
    if v is None:
        return None
    # 🔴 2e REVUE (2026-08-24) — DEUX ETAPES DU PRODUIT ETAIENT COURT-CIRCUITEES,
    #    ET L'INSTRUMENT ACCUSAIT UNE SONDE QUE LE PRODUIT AVAIT BIEN CLASSEE.
    #  (a) LE SIGNE. `_dx()` ECRETE un negatif a **0** et le compte. Mais le
    #      produit, lui, transforme d'abord une valeur LHM negative en `None`
    #      (`dn_agent._lire()`, compteur `:negatif`) — donc la dalle ecrit « -- ».
    #      Un tachymetre a -1 (cas assez reel pour que le stub ait un
    #      `--mode negatif` DEDIE) faisait enregistrer `0.0` par l'instrument : une
    #      serie de zeros constants ecrase sigma (C3) et le taux (C2) ⇒ 🔴 NE
    #      QUALIFIE PAS, sur une sonde qui disait honnetement « je ne sais pas ».
    #  (b) LE PLAFOND. `10 ** 9` au lieu des `BORNES` de la metrique, alors que le
    #      firmware REJETTE au-dela (`rejets_bornes`) : l'instrument jugeait une
    #      valeur que la dalle n'ecrirait jamais.
    # ⛔ La docstring promet « la valeur telle que la DALLE l'ecrirait » : elle est
    #    tenue, ou elle est fausse.
    if v < 0:
        return None
    mag = dn_agent._dx(v, borne if borne is not None else 10 ** 9, {}, "w2")
    if precision == "dixieme":
        return mag / 10.0
    # ⚠️ firmware `fmt_grandeur()` en precision ENTIERE : (mag + 5) / 10,
    #    demi-haut sur des entiers. ⛔ Pas `round()`, qui arrondit au pair.
    return float((mag + 5) // 10)


def echantillon(t):
    """Rend le dict des grandeurs AFFICHEES, plus les deux canaux bruts."""
    top, rear = t.get(FAN_TOP), t.get(FAN_REAR)
    # ⚠️ MEME REGLE QUE L'AGENT : la moyenne EXIGE LES DEUX canaux. Une moyenne
    #    sur un seul est un AUTRE nombre sous la meme etiquette.
    moy = (top + rear) / 2.0 if (top is not None and rear is not None) else None
    # ⚠️ LES PLAFONDS VIENNENT DU PRODUIT (`dn_agent.BORNES`), ⛔ pas d'un
    #    `10 ** 9` qui laisserait passer ce que le firmware REJETTE. Indices :
    #    `cpu[3]` = la °C ; `disk[1..3]` = extraction / noctua / boitier.
    _b = dn_agent.BORNES
    return {
        "cpu.degc": affichee(t.get(TEMP_CPU), "dixieme", _b["cpu"][3]),
        "disk.extraction_moy": affichee(moy, "entier", _b["disk"][1]),
        "disk.cpu_noctua": affichee(t.get(FAN_NOCTUA), "entier", _b["disk"][2]),
        "disk.case_group": affichee(t.get(FAN_CASE), "entier", _b["disk"][3]),
        # ⚠️ `top`/`rear` ne sont PAS publies tels quels sur le fil (seule leur
        #    moyenne l'est) : ils gardent donc le plafond de la grandeur derivee.
        "fan.top_out": affichee(top, "entier", _b["disk"][1]),
        "fan.rear_out": affichee(rear, "entier", _b["disk"][1]),
    }


def cadence_lhm(lhm, secondes=40.0, periode=0.2, toutes=True):
    """\U0001f534 RELEVER LA CADENCE DE LHM, ⛔ NE PAS LA SUPPOSER EGALE A 1 Hz.

    Le critere gele l'exige : « une source cadencee interrogee trois fois en
    100 ms rend TROIS FOIS LA MEME MESURE — et FABRIQUE UNE FAUSSE STABILITE ».
    On sur-echantillonne et on regarde a quel intervalle la valeur CHANGE.
    """
    # 🔴 DEUX DEFAUTS TROUVES EN REVUE (code review dn4-8, 2026-08-21) :
    #
    #   (1) LA FENETRE NE POUVAIT PAS VOIR CE QU'ELLE EXIGE. Le defaut valait
    #       `secondes=12.0` pendant que la garde plus bas refuse de publier sous
    #       5 changements. A la cadence LHM MESUREE — 4,00 s, n=785 — une fenetre
    #       de 12 s en donne AU MIEUX 3. `cadence_lhm()` rendait donc TOUJOURS
    #       `None` sur la ligne de commande documentee, donc C2 etait
    #       structurellement « NON JUGEABLE », donc les pourcentages d'AC4
    #       reposaient sur `--rejuger --periode-lhm 4.00` : un denominateur TAPE
    #       A LA MAIN que le tir de jugement n'a jamais verifie.
    #       ⇒ 40 s : ~10 changements attendus a 4,00 s, avec de la marge si LHM
    #         ralentit. ⛔ Une garde dont la fenetre ne peut pas la satisfaire
    #         n'est pas une garde, c'est un refus deguise.
    #
    #   (2) « LES QUATRE, OU RIEN » N'ETAIT PAS APPLIQUE. Le texte vit dans la
    #       branche `toutes=True`, mais le tir reel appelait le defaut
    #       `toutes=False` — donc `cpu.degc` SEULE — et cette mesure d'UNE sonde
    #       devenait le denominateur de C2 pour les trois autres. Pire : la
    #       branche `toutes=True` finissait par `return None`, donc elle ne
    #       pouvait JAMAIS servir a mesurer quoi que ce soit.
    #       ⇒ le defaut est `toutes=True`, et cette branche PUBLIE maintenant.
    print("[w2] relevé de la cadence PROPRE de LHM (sur-echantillonnage %.1f Hz, "
          "%.0f s, %s)..." % (1.0 / periode, secondes,
                              "LES QUATRE sondes" if toutes else "cpu.degc SEULE"))
    cles = [n for n, _ in GRANDEURS] if toutes else ["cpu.degc"]
    t0 = time.monotonic()
    suites = {k: [] for k in cles}
    marques = []
    while time.monotonic() - t0 < secondes:
        e = echantillon(lhm.lire())
        for k in cles:
            suites[k].append(e.get(k))
        marques.append(time.monotonic() - t0)
        time.sleep(periode)
    if toutes:
        # 🔴 UNE SEULE SONDE NE SUFFIT PAS A ETABLIR UNE CADENCE : si elle etait
        #    figee pour une autre raison, on conclurait « LHM est lent » sur une
        #    observation qui ne parle que d'elle. Les quatre, ou rien.
        print("  n = %d lectures a %.1f Hz" % (len(marques), 1.0 / periode))
        medianes = []
        for k in cles:
            vk = suites[k]
            ch = [marques[i] for i in range(1, len(vk)) if vk[i] != vk[i - 1]]
            if len(ch) < 5:
                print("  %-22s %d changement(s) — TROP PEU pour conclure (il en "
                      "faut 5)" % (k, len(ch)))
                continue
            ec = [b - a for a, b in zip(ch, ch[1:])]
            med_k = statistics.median(ec)
            medianes.append((k, med_k))
            print("  %-22s %3d chgts | mediane %5.2f s | min %5.2f | max %5.2f | %.3f Hz"
                  % (k, len(ch), med_k, min(ec), max(ec), 1.0 / med_k))
        # 🔴 2e REVUE (2026-08-24) — « LES QUATRE, OU RIEN » N'ETAIT TOUJOURS PAS
        #    APPLIQUE. Le commentaire au-dessus de ce bloc dit mot pour mot « UNE
        #    SEULE SONDE NE SUFFIT PAS A ETABLIR UNE CADENCE … Les quatre, ou
        #    rien », et le commentaire de revue du 2026-08-21 affirmait l'avoir
        #    corrige. Le code ecrivait `if not medianes:` — c'est-a-dire AU MOINS
        #    UNE. PawnIO decharge pendant la fenetre ⇒ les trois `tr/min` ne
        #    changent jamais ⇒ seule `cpu.degc` qualifie ⇒ SA cadence devient le
        #    DENOMINATEUR DE C2 POUR LES QUATRE GRANDEURS. Et le garde-fou
        #    « les sondes ne s'accordent pas » ne peut pas tirer non plus
        #    (`len(vals) > 1` est faux).
        if len(medianes) < len(cles):
            muettes = sorted(set(cles) - {k for k, _ in medianes})
            print("[w2] ⚠️ %d/%d sonde(s) seulement ont rendu 5 changements en "
                  "%.0f s (muettes : %s) : CADENCE NON DETERMINEE. ⛔ Ne pas "
                  "conclure « LHM est fige », ⛔ ne pas publier de plafond, et "
                  "⛔ SURTOUT ne pas faire de la cadence d'UNE sonde le "
                  "denominateur de C2 pour LES QUATRE."
                  % (len(medianes), len(cles), secondes, ", ".join(muettes)))
            return None
        vals = [m for _, m in medianes]
        med = statistics.median(vals)
        # ⚠️ SI LES SONDES NE S'ACCORDENT PAS, ON LE DIT — une cadence commune qui
        #    n'est pas commune serait une moyenne sur deux phenomenes differents.
        if len(vals) > 1 and (max(vals) - min(vals)) > 0.25 * med:
            print("[w2] ⚠️ LES SONDES NE S'ACCORDENT PAS SUR LA CADENCE "
                  "(%.2f..%.2f s, mediane %.2f s). ⛔ Le denominateur de C2 est "
                  "donc INCERTAIN, et c'est publie AVEC le verdict."
                  % (min(vals), max(vals), med))
        # 🔴 PLEINE PRECISION — 2e REVUE (2026-08-24), ET LE TROU EST MESURE.
        #    La cadence n'etait imprimee QU'ARRONDIE a 2 decimales, et le CSV ne
        #    la porte pas : `--rejuger` ne pouvait donc PAS reproduire un verdict
        #    publie. Constate en re-jugeant le tir de §19 avec `--periode-lhm 4.01`
        #    (la valeur LUE dans le log) : `disk.cpu_noctua` rendait **96,1 %**
        #    contre **96,0 %** publie. Les deux formules donnent pourtant
        #    exactement 96,0554 % sur ces donnees — l'ecart venait UNIQUEMENT de
        #    l'ARRONDI de l'entree qu'on relit.
        # ⛔ Un instrument dont on ne peut pas rejouer le verdict publie n'est pas
        #    reproductible, meme s'il est juste.
        print("[w2] cadence LHM MESUREE sur %d/%d sonde(s) : mediane des medianes "
              "%.2f s (~%.2f Hz)" % (len(medianes), len(cles), med, 1.0 / med))
        print("[w2] \U0001f3af CADENCE A REPORTER TELLE QUELLE dans `--periode-lhm` "
              "pour rejouer CE verdict : %.9f  (\u26d4 pas la valeur arrondie "
              "ci-dessus)" % med)
        if med > 1.05:
            print("[w2] 🔴 LHM RAFRAICHIT PLUS LENTEMENT QUE 1 Hz. ⛔ Echantillonner "
                  "a 1 Hz DUPLIQUERAIT des valeurs et FABRIQUERAIT de la stabilite.")
        return med
    suite = suites["cpu.degc"]
    chg = [marques[i] for i in range(1, len(suite)) if suite[i] != suite[i - 1]]
    # \U0001f534 GARDE CORRIGEE LE 2026-08-21, EN SEANCE : elle exigeait « au moins 2
    #    changements », donc elle acceptait UN SEUL INTERVALLE et publiait sa
    #    « mediane ». Une mediane sur un point n'est pas une mediane. Vu passer
    #    « intervalle median 4,17 s » sur 2 changements, la ou une mesure a 785
    #    lectures donnait 4,00 s. ⛔ FAUSSE D'UN CRAN, et dans le sens dangereux :
    #    elle rendait un chiffre AU LIEU de refuser.
    # ⇒ il faut au moins 5 changements (4 intervalles) pour publier quoi que ce soit.
    if len(chg) < 5:
        print("[w2] ⚠️ %d changement(s) en %.0f s : CADENCE NON DETERMINEE — il en "
              "faut au moins 5 pour qu'une mediane ait un sens. ⛔ Ne pas conclure "
              "« LHM est fige », et ⛔ ne pas publier de plafond." % (len(chg), secondes))
        return None
    ecarts = [b - a for a, b in zip(chg, chg[1:])]
    med = statistics.median(ecarts)
    print("[w2] cadence LHM MESUREE : %d changement(s) en %.0f s, intervalle "
          "median %.2f s (~%.2f Hz)" % (len(chg), secondes, med, 1.0 / med))
    print("[w2] \U0001f3af CADENCE A REPORTER TELLE QUELLE dans `--periode-lhm` : "
          "%.9f  (\u26d4 pas la valeur arrondie ci-dessus)" % med)
    if med > 1.05:
        print("[w2] \U0001f534 LHM RAFRAICHIT PLUS LENTEMENT QUE 1 Hz. ⛔ Echantillonner "
              "a 1 Hz DUPLIQUERAIT des valeurs et FABRIQUERAIT de la stabilite : "
              "le taux de changement du TEXTE serait ARTIFICIELLEMENT BAS.")
    return med


def juger(nom, famille, vals, periode_lhm=None, periode_ech=None, n_lignes=None):
    """⚠️ `periode_lhm` est la cadence MESUREE de la source. Sans elle, C2 ne peut
    pas etre juge : on ne connait pas le nombre d'OCCASIONS.

    🔴 `n_lignes` AJOUTE EN 2e REVUE (2026-08-24) — SANS LUI, C2 POUVAIT DEPASSER
       100 % ET QUALIFIER QUAND MEME. `occasions` se calculait
       `(len(v) - 1) * periode_ech / periode_lhm` ou `v` est la liste des valeurs
       **PRESENTES**, ⛔ pas le nombre de lignes : des qu'une sonde est absente sur
       une partie de la session, le denominateur retrecit pendant que `chg` reste
       compte A TRAVERS LES TROUS. MESURE sur le CSV reel avec `cpu.degc` videe une
       ligne sur deux :
           C2 181.2 % des OCCASIONS (119 occ., 216 chgt) >= 60.0 % OK
              (soit 45.2 % des echantillons ; plafond atteignable 24.9 %)
           => ✅ QUALIFIE
       Trois nombres impossibles cote a cote, et un verdict vert sur une grandeur
       qui change a 45 % de ses occasions REELLES, donc SOUS le seuil.
    ⇒ La duree observee vient du nombre de LIGNES de la session, ⛔ pas du nombre
      de valeurs presentes. Et un `pct_occ > 100` est desormais IMPOSSIBLE par
      construction : s'il survient, c'est un DEFAUT D'INSTRUMENT et il se DIT.
    """
    c1min, c3min, unite, _prec = SEUILS[famille]
    v = [x for x in vals if x is not None]
    if len(v) < 2:
        print("  %-22s ⛔ %d echantillon(s) — NON JUGEABLE" % (nom, len(v)))
        return None
    etendue = max(v) - min(v)
    chg = sum(1 for a, b in zip(v, v[1:]) if a != b)
    taux = 100.0 * chg / (len(v) - 1)
    sigma = statistics.pstdev(v)
    # \U0001f534 C2 EST RELATIF AU PLAFOND MESURE. Le nombre d'OCCASIONS de changer
    #    est la duree observee divisee par la periode de rafraichissement de LHM.
    # ⛔ SANS CADENCE MESUREE, C2 N'EST PAS JUGEABLE — et on le DIT, on ne retombe
    #    pas sur un seuil absolu qui mesurerait notre echantillonnage.
    # ⚠️ LES **DEUX** CADENCES SONT REQUISES (2e revue) : celle de LHM ET
    #    l'espacement MESURE des echantillons. Il manquait la seconde.
    if periode_lhm and periode_lhm > 0 and periode_ech and periode_ech > 0:
        # 🔴 LA DUREE OBSERVEE EST CELLE DE LA SESSION, ⛔ pas celle des valeurs
        #    presentes. `n_lignes` par defaut retombe sur `len(vals)` — la liste
        #    COMPLETE, trous compris — donc jamais sur `len(v)`.
        etendue_n = (n_lignes if n_lignes is not None else len(vals))
        occasions = max(etendue_n - 1, 0) * periode_ech / periode_lhm
        pct_occ = 100.0 * chg / occasions if occasions > 0 else 0.0
        c2 = pct_occ >= C2_OCCASIONS_MIN
        # ⛔ UN TAUX D'OCCASIONS > 100 % EST ARITHMETIQUEMENT IMPOSSIBLE : il y
        #    aurait plus de changements que d'occasions de changer. S'il apparait,
        #    c'est l'INSTRUMENT qui est faux, ⛔ pas la sonde qui est excellente.
        #    On refuse de juger plutot que de publier un verdict impossible.
        if pct_occ > 100.0 + 1e-9:
            print("  %-22s ⛔ C2 IMPOSSIBLE : %.1f %% des occasions (%.0f occ., "
                  "%d chgt) — un taux > 100 %% signale un DEFAUT D'INSTRUMENT "
                  "(trous dans la serie ?), \u26d4 PAS une sonde exceptionnelle. "
                  "NON JUGEABLE." % (nom, pct_occ, occasions, chg))
            c2 = None
    else:
        if periode_lhm and periode_lhm > 0 and not periode_ech:
            print("  %-22s ⛔ C2 NON JUGEABLE : espacement des echantillons NON "
                  "MESURE. \u26d4 On ne retombe PAS sur 1,0 s suppose." % nom)
        occasions, pct_occ, c2 = None, None, None
    c1, c3 = etendue >= c1min, sigma >= c3min
    # 🔴 `ok` valait `bool(c1) and bool(None) and bool(c3)` = **False** quand C2
    #    n'etait pas jugeable : le code imprimait « C2 ⛔ NON JUGEABLE » puis, deux
    #    lignes plus bas, « NE QUALIFIE PAS ». Il convertissait donc en ECHEC ce
    #    que son propre commentaire exige de ne PAS conclure. Corrige en revue
    #    (2026-08-21) : ⛔ NON JUGEABLE n'est ni un succes ni un echec.
    ok = None if c2 is None else (bool(c1) and bool(c2) and bool(c3))
    print("  %-22s n=%-5d %.1f..%.1f %s" % (nom, len(v), min(v), max(v), unite))
    print("     C1 etendue %9.2f >= %-6.1f %s" % (etendue, c1min, "OK" if c1 else "NON"))
    if c2 is None:
        print("     C2 ⛔ NON JUGEABLE : la cadence de LHM n'a pas ete mesuree")
    else:
        print("     C2 %5.1f %% des OCCASIONS (%.0f occ., %d chgt) >= %-5.1f%% %s"
              % (pct_occ, occasions, chg, C2_OCCASIONS_MIN, "OK" if c2 else "NON"))
        print("        (soit %.1f %% des echantillons ; plafond atteignable %.1f %%)"
              % (taux, 100.0 * periode_ech / periode_lhm))
    print("     C3 sigma   %9.2f >= %-6.1f %s" % (sigma, c3min, "OK" if c3 else "NON"))
    # \U0001f534 LE TELL D'UN INSTRUMENT MORT : une valeur EXACTEMENT constante.
    if etendue == 0.0:
        print("     \U0001f534 VALEUR EXACTEMENT CONSTANTE sur toute la session. ⛔ C'est le "
              "TELL D'UN INSTRUMENT MORT, ⛔ pas la preuve d'une grandeur immobile. "
              "VERIFIER L'INSTRUMENT AVANT D'ACCUSER LA SONDE.")
    print("     => %s" % ("\u2705 QUALIFIE" if ok else
                          ("\U0001f534 NE QUALIFIE PAS" if ok is False else
                           "\u26d4 NON JUGEABLE (cadence LHM non mesuree) — "
                           "⛔ NI qualifie NI disqualifie")))
    if ok is False and nom == "disk.extraction_moy" and c1 and c2 and not c3:
        print("     \u26a0\ufe0f RESERVE ECRITE D'AVANCE : c'est une grandeur DERIVEE "
              "(moyenne de deux canaux), donc elle LISSE. Echouer C3 en passant C1 et "
              "C2 n'est ⛔ PAS une sonde morte — c'est la moyenne qui fait son travail.")
    return ok


def periode_mesuree(lignes):
    """L'espacement REEL des echantillons, LU dans la colonne `t_s`.

    🔴 DEFAUT TROUVE EN REVUE (2026-08-21) : `juger()` derivait le nombre
       d'OCCASIONS d'un `periode_ech = 1.0` CODE EN DUR, et `analyser()` ne le
       passait jamais. La colonne `t_s` — que l'outil ECRIT lui-meme — n'etait
       donc jamais relue. Consequence : toute session recalee, et tout
       `--rejuger` d'un CSV qui n'etait pas exactement a 1 Hz, calculait C2 sur
       un denominateur FAUX. ⛔ Un instrument qui ecrit son horodatage puis
       l'ignore mesure son intention, pas la realite.
    """
    ts = [l["t_s"] for l in lignes if l.get("t_s") is not None]
    if len(ts) < 2:
        return None
    ec = [b - a for a, b in zip(ts, ts[1:]) if b > a]
    if not ec:
        return None
    return statistics.median(ec)


def _pearson(xs, ys):
    """r de Pearson sur les paires COMPLETES. `None` si moins de 3 paires."""
    paires = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(paires) < 3:
        return None
    px = [p[0] for p in paires]
    py = [p[1] for p in paires]
    mx, my = statistics.fmean(px), statistics.fmean(py)
    num = sum((x - mx) * (y - my) for x, y in paires)
    dx = sum((x - mx) ** 2 for x in px) ** 0.5
    dy = sum((y - my) ** 2 for y in py) ** 0.5
    if dx == 0.0 or dy == 0.0:
        return None
    return num / (dx * dy)


def analyser(lignes, periode_lhm=None):
    print("\n" + "=" * 84)
    print("VERDICT W2 — seuils GELES le 2026-08-21T18:09:35Z (commit c377d2c)")
    print("=" * 84)
    pe = periode_mesuree(lignes)
    if pe is None:
        print("[w2] ⛔ ESPACEMENT DES ECHANTILLONS NON MESURABLE (colonne `t_s`) — "
              "C2 ne sera pas juge.")
    else:
        print("[w2] espacement des echantillons MESURE dans `t_s` : %.3f s "
              "(⛔ pas suppose)" % pe)
        if abs(pe - 1.0) > 0.05:
            print("[w2] ⚠️ ce n'est PAS 1,00 s : le denominateur de C2 en tient "
                  "compte. Un `periode_ech` code en dur aurait fausse le verdict.")
    res = {}
    for nom, fam in GRANDEURS:
        # 🔴 2e REVUE (2026-08-24) : `pe if pe else 1.0` REINTRODUISAIT LE 1.0 EN
        #    DUR QUE LE MESSAGE VENAIT D'INTERDIRE. Quand `periode_mesuree()` rend
        #    `None`, l'outil imprimait « ⛔ ESPACEMENT NON MESURABLE — C2 ne sera
        #    pas juge », puis appelait `juger` avec 1.0, et `juger` ne conditionnait
        #    C2 qu'a `periode_lhm` : **C2 etait donc juge sur un espacement SUPPOSE**
        #    — exactement le defaut que la docstring de `periode_mesuree` dit fermer.
        # ⇒ ON PASSE `None`, ET `juger` REFUSE DE JUGER C2. Une annonce et un
        #   comportement qui se contredisent, c'est l'annonce qui ment.
        res[nom] = juger(nom, fam, [l[nom] for l in lignes], periode_lhm,
                         periode_ech=pe, n_lignes=len(lignes))

    # 🔴 σ PAR CANAL SUR **LES SIX**, ET LA CORRELATION — ajoutes en revue
    #    (2026-08-21). §17.3 publiait un σ par canal et un `r = 0,955` presentes
    #    comme « ce qui valide la disposition d'AC5 PAR LA MESURE » : AUCUN
    #    instrument commite ne les produisait. `juger()` ne calcule σ que sur les
    #    quatre entrees de `GRANDEURS` — donc SANS `fan.top_out` ni
    #    `fan.rear_out`, les deux canaux dont `extraction_moy` est la moyenne —
    #    et n'a aucun code de correlation. ⛔ Un nombre publie doit etre
    #    reproductible par un outil du depot, sinon il n'est pas une mesure.
    print("\n" + "-" * 84)
    print("σ PAR CANAL — LES SIX, y compris les deux que `extraction_moy` moyenne")
    print("-" * 84)
    for c in COLONNES:
        if c == "t_s":
            continue
        v = [l[c] for l in lignes if l.get(c) is not None]
        if len(v) < 2:
            print("  %-22s n=%-5d ⛔ trop peu pour un sigma" % (c, len(v)))
            continue
        print("  %-22s n=%-5d sigma %8.3f | etendue %8.3f (%.2f..%.2f)"
              % (c, len(v), statistics.pstdev(v), max(v) - min(v), min(v), max(v)))
    print("\n" + "-" * 84)
    print("CORRELATIONS — `extraction_moy` contre les DEUX canaux qu'elle moyenne")
    print("-" * 84)
    xs = [l.get("disk.extraction_moy") for l in lignes]
    for c in ("fan.top_out", "fan.rear_out", "cpu.degc", "disk.cpu_noctua"):
        r = _pearson(xs, [l.get(c) for l in lignes])
        print("  extraction_moy ~ %-16s r = %s"
              % (c, "%.3f" % r if r is not None else "⛔ non calculable"))
    print("  ⚠️ UN r ELEVE ENTRE `extraction_moy` ET SES PROPRES CANAUX EST "
          "ATTENDU — c'est leur moyenne. ⛔ Ce n'est PAS une decouverte, c'est un "
          "controle de coherence de l'instrument.")
    return res


def relire_csv(chemin):
    """⛔ LECTURE STRICTE : un compte de colonnes qui ne correspond pas JETTE la
    session. Motif paye : un lecteur permissif a deja DECALE toutes les colonnes
    en silence, et l'analyse a publie « CPU % max = 1600 » — c'etait la frequence."""
    lignes = []
    with io.open(chemin, encoding="utf-8") as f:
        entete = f.readline().rstrip("\n").split(";")
        if entete != COLONNES:
            sys.exit("\u26d4 SESSION JETEE : en-tete CSV inattendu.\n  attendu : %s\n"
                     "  lu      : %s" % (COLONNES, entete))
        for n, l in enumerate(f, 2):
            ch = l.rstrip("\n").split(";")
            if len(ch) != len(COLONNES):
                sys.exit("\u26d4 SESSION JETEE : ligne %d a %d colonne(s) au lieu de %d. "
                         "⛔ Un lecteur permissif aurait DECALE les colonnes en silence."
                         % (n, len(ch), len(COLONNES)))
            lignes.append({c: (None if v == "" else float(v))
                           for c, v in zip(COLONNES, ch)})
    print("[w2] CSV relu : %d ligne(s), %d colonnes VERIFIEES" % (len(lignes), len(COLONNES)))
    return lignes


def _sortie(res):
    """Traduit le verdict W2 en CODE DE SORTIE. ⛔ Il n'y en avait AUCUN.

    🔴 2e REVUE (2026-08-24) — CET INSTRUMENT NE POUVAIT PAS ECHOUER, ET LA STORY
       CITAIT SON `exit 0` COMME UN CONTROLE D'AC4. `analyser()` construisait
       `res[nom] = juger(...)` et le RENDAIT ; `main()` le JETAIT et faisait
       `return 0` sur les trois branches. La revue du 2026-08-21 avait patche
       `juger()` pour rendre `None` sur « NON JUGEABLE » — mais PERSONNE NE LISAIT
       LE VERDICT. `exit 0` etait satisfait par : les quatre grandeurs en echec ·
       C2 non jugeable sur les quatre · `n = 2` · un CSV de deux lignes.
    ⚠️ Les quatre autres instruments du meme lot rendent bien 1 sur echec
       (`campagne_bruit:353`, `verif_source:427`, `recompte_trame:234`,
       `regime_reel:283`). La correction avait oublie celui dont la sortie PORTE
       le verdict d'AC4.
    ⛔ ET « NON JUGEABLE » N'EST NI UN SUCCES NI UN ECHEC — c'est la doctrine
       ecrite dans `juger()`. Il sort donc en **2**, ⛔ pas en 0 : un tir qui ne
       peut pas juger ne prouve pas un AC.
    """
    if not res:
        print("\n\u2716\ufe0f  AUCUNE GRANDEUR JUGEE — \u26d4 ce tir ne prouve rien.")
        return 2
    echecs = sorted(k for k, v in res.items() if v is False)
    indecis = sorted(k for k, v in res.items() if v is None)
    if echecs:
        print("\n\u2716\ufe0f  %d GRANDEUR(S) NE QUALIFIENT PAS : %s"
              % (len(echecs), ", ".join(echecs)))
        return 1
    if indecis:
        print("\n\u26a0\ufe0f  %d GRANDEUR(S) NON JUGEABLE(S) : %s"
              % (len(indecis), ", ".join(indecis)))
        print("   \u26d4 NI succes NI echec — mais ce tir ne solde PAS AC4.")
        return 2
    print("\n\u2705 LES %d GRANDEURS QUALIFIENT." % len(res))
    return 0


def main():
    for f in (sys.stdout, sys.stderr):
        try:
            f.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=16.0)
    ap.add_argument("--csv", default=None)
    ap.add_argument("--rejuger", default=None,
                    help="re-juge un CSV existant SANS re-tirer")
    ap.add_argument("--periode-lhm", type=float, default=0.0, metavar="S",
                    help="periode de rafraichissement de LHM, MESUREE ailleurs, "
                         "a utiliser pour --rejuger (⛔ jamais supposee)")
    ap.add_argument("--cadence", type=float, default=0.0, metavar="S",
                    help="mesure SEULEMENT la cadence propre de LHM, sur S "
                         "secondes, sur les QUATRE grandeurs")
    a = ap.parse_args()

    if a.rejuger:
        if not a.periode_lhm:
            print("[w2] ⚠️ --periode-lhm absente : C2 sera NON JUGEABLE. ⛔ On ne "
                  "suppose pas la cadence.")
        else:
            print("[w2] periode LHM FOURNIE : %.2f s (⚠️ mesuree ailleurs, ⛔ pas "
                  "supposee) => plafond atteignable %.1f %% a 1 Hz"
                  % (a.periode_lhm, 100.0 / a.periode_lhm))
        return _sortie(analyser(relire_csv(a.rejuger), a.periode_lhm or None))

    if a.cadence:
        print("=" * 84)
        print("CADENCE PROPRE DE LHM — \u26d4 mesuree, PAS supposee")
        print("=" * 84)
        med = cadence_lhm(Lhm(), secondes=a.cadence, periode=0.1, toutes=True)
        # ⚠️ `--cadence` MESURE : si la cadence n'est pas determinee, il n'y a rien
        #    a publier, et ⛔ ca ne se dit pas par `exit 0`.
        if med is None:
            print("\n\u2716\ufe0f  CADENCE NON DETERMINEE — \u26d4 rien a publier.")
            return 2
        return 0

    print("=" * 84)
    print("dn4-8 / AC4 — QUALIFICATION W2 des quatre grandeurs LHM")
    print("=" * 84)
    # 🔴 CE BANDEAU ANNONÇAIT `C2>=25 %` / `C2>=10 %` — les seuils AVANT
    #    amendement — pendant que `juger()` appliquait `C2_OCCASIONS_MIN = 60 %`
    #    des OCCASIONS. Deux criteres « GELES » CONTRADICTOIRES dans une meme
    #    sortie de session, et ce sont ces transcriptions qui portent le verdict
    #    d'AC4. Corrige en revue (2026-08-21) : le bandeau LIT les constantes.
    # ⛔ Les deux formes ne sont meme pas comparables : 60 % des occasions a la
    #    cadence LHM mesuree (4,00 s) valent ~15 % des echantillons a 1 Hz.
    print("[w2] seuils GELES  degC : C1>=%.1f · C3>=%.1f  (unite %s)"
          % (SEUILS["degc"][0], SEUILS["degc"][1], SEUILS["degc"][2]))
    print("[w2] seuils GELES  rpm  : C1>=%.1f · C3>=%.1f  (unite %s)"
          % (SEUILS["rpm"][0], SEUILS["rpm"][1], SEUILS["rpm"][2]))
    print("[w2] seuil GELE   C2   : >= %.1f %% des OCCASIONS (⛔ pas des "
          "echantillons) — amendement owner DATE du 2026-08-21 (5773e85)"
          % C2_OCCASIONS_MIN)
    print("[w2] \u26d4 AUCUNE CHARGE N'EST PROVOQUEE PAR CET INSTRUMENT. La phase de "
          "charge, s'il y en a une, est un GESTE OWNER.")
    lhm = Lhm()
    periode = cadence_lhm(lhm)
    if not periode:
        print("[w2] ⛔ CADENCE NON MESUREE : C2 sera NON JUGEABLE. ⛔ On ne retombe "
              "PAS sur un seuil absolu — il mesurerait notre echantillonnage.")

    f = None
    if a.csv:
        f = io.open(a.csv, "w", encoding="utf-8", newline="")
        f.write(";".join(COLONNES) + "\n")
        f.flush()
    print("[w2] tir : %.1f min a 1 Hz (n vise = %d)" % (a.minutes, int(a.minutes * 60)))
    sys.stdout.flush()

    lignes, t0, prochain, pannes, recalages = \
        [], time.monotonic(), time.monotonic(), 0, 0
    try:
        while time.monotonic() - t0 < a.minutes * 60.0:
            prochain += 1.0
            # 🔴 RATTRAPAGE — DEFAUT TROUVE EN REVUE (2026-08-21). `prochain`
            #    avancait de 1,0 s INCONDITIONNELLEMENT : quand une lecture
            #    debordait la periode (LHM lent, timeout), `d` restait negatif et
            #    les iterations suivantes s'enchainaient DOS A DOS pour rattraper
            #    — donc a une cadence qui n'est plus 1 Hz, sans que rien ne le
            #    dise. Le produit a exactement cette garde (`dn_agent.py`), pas
            #    cet instrument. ⛔ Et C2 se calcule sur une periode supposee.
            retard = time.monotonic() - prochain
            if retard > 1.0:
                sauts = int(retard)
                prochain += sauts
                recalages += 1
                if recalages == 1:
                    print("[w2] ⚠️ CADENCE RECALEE (retard %.2f s) — l'espacement "
                          "reel n'est plus 1,00 s. Compte publie au bilan, et "
                          "C2 utilisera l'espacement MESURE dans `t_s`." % retard)
            try:
                e = echantillon(lhm.lire())
            except UniteChangee as exc:
                # 🔴 LA SESSION EST JETEE POUR DE BON, ET LE MOTIF EST IMPRIME
                #    EN ENTIER — c'est lui qui dit QUELLE famille a change.
                print("\n\u2716\ufe0f  %s" % exc)
                print("   \u26d4 AUCUN VERDICT W2 N'EST PUBLIE : la moitie d'avant le "
                      "renommage porterait sur une AUTRE grandeur.")
                if f:
                    f.close()
                return 1
            except Exception as exc:
                pannes += 1
                if pannes == 1:
                    print("[w2] \u26a0\ufe0f lecture LHM en ECHEC (%s) — comptee, la session "
                          "continue" % type(exc).__name__)
                e = {c: None for c in COLONNES if c != "t_s"}
            e["t_s"] = round(time.monotonic() - t0, 2)
            lignes.append(e)
            if f:
                f.write(";".join("" if e[c] is None else repr(e[c])
                                 for c in COLONNES) + "\n")
                f.flush()
            d = prochain - time.monotonic()
            if d > 0:
                time.sleep(d)
    except KeyboardInterrupt:
        print("\n[w2] \u26a0\ufe0f interrompu — la session est JUGEE sur ce qui a ete "
              "capture (n=%d), et le n est PUBLIE" % len(lignes))
    finally:
        if f:
            f.close()

    print("\n[w2] n=%d echantillon(s), %d lecture(s) en echec, %d recalage(s) de "
          "cadence" % (len(lignes), pannes, recalages))
    if len(lignes) < 900:
        print("[w2] \u26a0\ufe0f n < 900 : le critere gele annoncait n >= 900. ⛔ Le verdict "
              "ci-dessous vaut pour CE n, et il est publie avec.")
    res = analyser(lignes, periode)
    print("\n\u26a0\ufe0f TIR AU REPOS — decision owner du 2026-08-21. La phase de CHARGE "
          "exigee par le critere N'EST PAS couverte.")
    print("   \u26d4 Une NON-qualification est donc NON CONCLUANTE (une session plate "
          "n'est pas une sonde morte).")
    print("   \u2705 Une QUALIFICATION, elle, reste VALIDE : ce qui bouge assez au repos "
          "bouge a fortiori sous charge.")
    return _sortie(res)


if __name__ == "__main__":
    sys.exit(main())

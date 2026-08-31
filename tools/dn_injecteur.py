#!/usr/bin/env python3
"""
dn_injecteur — tenir les six cases VIVANTES pendant un constat owner.

🔴 POURQUOI IL EXISTE. Un constat à l'œil sur des cases à « -- » ne dit rien de
   la lisibilité : c'est la LONGUEUR DES CHAÎNES qui décide, et « -- » est la
   plus courte de toutes. Or l'agent PC réel tourne sur **Windows, sur COM3** —
   et l'exclusivité WSL↔COM3 est stricte : tant que la carte est attachée à WSL,
   l'agent ne peut pas parler, et tant que l'agent parle, la console de mesure
   n'existe plus. On ne peut donc pas commuter les voies ET voir des vraies
   valeurs par ce chemin-là.

⇒ On injecte par la BRANCHE A (« l'agent envoie `pc $DN,…` »), depuis WSL, en
  gardant la console. ⚠️ Ça teste **le CHEMIN DE CODE, pas le matériel** — c'est
  la règle n°4 de la méthodo du dépôt, et elle s'applique ici telle quelle.

⚠️ LA PÉREMPTION EST DE 3 s PAR MÉTRIQUE, en temps absolu de réception. Un tir
   unique laisse donc les cases mourir au bout de 3 s et repasser à « -- ».
   L'injecteur ré-émet à 1 Hz pour que la fenêtre d'observation soit tenue.

🔴 LE JEU PAR DÉFAUT EST LE **PIRE CAS PLAUSIBLE**, PAS LE NOMINAL. C'est lui
   qui décide de la lisibilité et du chevauchement — juger sur « 46,0 % » quand
   la grammaire autorise « 100,0 % » reviendrait à mesurer la case facile.
   ⛔ Les valeurs restent DANS les bornes de `k_metriques[]` : au-delà, la trame
   part en `rejets_bornes` et l'écran ne montre rien du tout.

⚠️ LES VALEURS SONT SIMULÉES ET LE FIRMWARE LE SAIT : elles arrivent par le
   chemin `dn_link`, donc la case est **RÉELLE** au sens du régime (une trame
   valide EST une donnée). ⛔ Ce n'est PAS le badge « SIMULÉ », qui est réservé
   aux mocks internes. Écrit ici pour que personne ne lise l'absence de badge
   comme « ce sont de vraies mesures de la tour ».

🔴 dn4-23 — LES QUATRE JEUX HISTORIQUES SONT DES **CONSTANTES**, ET C'EST UN
   DÉFAUT DE MESURE, ⛔ PAS UN DÉTAIL. Une valeur qui ne change pas ne change
   pas le TEXTE ; un texte qui ne change pas n'invalide rien ; LVGL ne redessine
   que ce qui est invalidé.
🔴 **CORRIGÉ PAR LA REVUE DU 2026-08-31 — CE PARAGRAPHE CONCLUAIT « un jeu figé
   produit du TRAFIC sans produire du DESSIN », sur « 94 645 px/cycle contre
   128 613 (−36 %) ». LA SÉANCE DU MÊME JOUR A MESURÉ L'INVERSE** : l'aire
   cumulée est **LA MÊME**, jeu fixe ou jeu variable (**11,37 M px** à 1 % près,
   **3 passes chacun**). L'écart mesurait **LA CADENCE** (1 Hz contre
   14/20/26/34 s), ⛔ pas la fixité. Et le repère `94 645` **ne se reproduit
   pas** (46 572 · 71 984 · 74 576) ; celui de `widget mock on`, si (124 750).
✅ CE QUI RESTE MESURÉ, ET C'EST UNE **AUTRE** MESURE : **0,005 corruption/s**
   contre **0,54 /s** sous agent réel — **×108**. C'est ça, et ça seul, qui rend
   un jeu figé impropre à décrire un régime réel.
   ⇒ ⛔ **TOUT CHIFFRE OÙ LE DESSIN EST LA VARIABLE SE MESURE SOUS AGENT RÉEL,
     OU AVEC `--jeu rampe`.** Les quatre jeux figés restent JUSTES pour ce à quoi
     ils servent : la mise en page et le pire cas de longueur de chaîne.

Usage :
    python3 tools/dn_injecteur.py --secondes 30
    python3 tools/dn_injecteur.py --jeu nominal --secondes 60
    python3 tools/dn_injecteur.py --jeu reel --secondes 30
    python3 tools/dn_injecteur.py --jeu rampe --secondes 60      # dn4-23, VARIABLE
    python3 tools/dn_injecteur.py --temoin-negatif               # AC3, SANS carte
    python3 tools/dn_injecteur.py --jeu rampe --latence 5 --secondes 20 \
            --firmware <SHA au bandeau> --releve mesures/dn4-23/lat-A.json
    python3 tools/dn_injecteur.py --latence-delta lat-A.json lat-B.json
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import dn_console  # noqa: E402  (le module frère porte l'ouverture du port)


def _ck(corps):
    x = 0
    for o in corps.encode("ascii"):
        x ^= o
    return f"{x:02X}"


# 🔴 CE QUE CHAQUE MÉTRIQUE PUBLIAIT EN v2 — relevé sur `k_metriques[]` de
#    dn4-1/dn4-6, ⛔ pas supposé. Sert au témoin de non-régression : une trame v2
#    doit rester EXACTEMENT celle que l'agent de l'époque émettait, sinon le
#    « témoin » mesure la modification et non la compatibilité.
# ⚠️ Le plafond de version reste 2 valeurs (`dn_link.c` : `ver <= 2 && nv > 2`
#    ⇒ rejet) : ce tableau ne fait que descendre EN DESSOUS quand c'est le cas.
_V2_GRANDEURS = {"cpu": 2, "gpu": 2, "ram": 2, "net": 2, "disk": 1}


def trame(seq, t_ms, metrique, valeurs, version=3):
    """v3. ⚠️ `None` = champ VIDE = « cette grandeur-là, je ne la connais pas »
    (W10 sur un fil positionnel). Les `None` de queue sont tronqués."""
    vs = list(valeurs)
    while vs and vs[-1] is None:
        vs.pop()
    if version <= 2:
        # v1 ne connaît que `cpu` et 6 champs ; v2 plafonne à deux valeurs.
        # 🔴 LE LEVIER A/B A CHANGÉ DE STIMULUS SOUS NOS PIEDS — défaut trouvé en
        #    revue (code review dn4-8, 2026-08-21). `--version 2` tronque à
        #    `vs[:2]` ; avant dn4-8 la table `disk` ne portait QU'UNE valeur, donc
        #    `--version 2` émettait `disk,999999`. Depuis que `disk` en porte
        #    QUATRE, la même option émet `disk,999999,24390`.
        # ⛔ CONSÉQUENCE : contre le firmware dn4-1 que ce levier vise (`disk`
        #    `n_grandeurs = 1`), `nv = 2 > 1` ⇒ **`rejets_format`**. Les trames
        #    `disk` qui étaient ACCEPTÉES avant sont maintenant REJETÉES — donc la
        #    propriété « une seule variable change entre les deux tirs » ne tient
        #    plus, et l'A/B ne compare plus ce qu'il croit.
        # ⇒ En v1/v2 on ne tronque plus à l'aveugle : on borne CHAQUE métrique à
        #   ce que cette version-là en publiait RÉELLEMENT.
        vs = vs[:1] if version == 1 else vs[:_V2_GRANDEURS.get(metrique, 2)]
    corps = f"DN,{version},{seq},{t_ms},{metrique}," + ",".join(
        "" if v is None else str(v) for v in vs)
    return f"${corps}*{_ck(corps)}"


# Les trois jeux. ⚠️ En DIXIÈMES, comme le fil — ⛔ jamais de flottant
# (doctrine `parse_entier`). C'est l'AFFICHAGE qui porte la précision (AC9).
JEUX = {
    # Le pire cas PLAUSIBLE : ce qu'une tour peut réellement afficher au max.
    "pire": {
        # 🔴 dn4-8 : la 4ᵉ valeur de `cpu` et les 3 de `disk` viennent de MESURES,
        #    ⛔ pas d'une invention « plausible » — et c'est mieux : les plafonds
        #    de ventilateur ont été RELEVÉS canal par canal le 2026-08-21, en
        #    poussant un canal à 100 % à la fois (stimulus/réponse, AC3).
        # ⚠️ ILS RESTENT DANS LA GRAMMAIRE : plafond `cpu` grandeur 4 = 1500
        #    (150,0 °C) et `disk` grandeurs 2..4 = 100000 (10 000 tr/min).
        #    ⛔ Au-dessus, on ne mesurerait pas la lisibilité, on mesurerait le
        #    parseur — la leçon du tir à 9 999 999 ci-dessous.
        "cpu": [1000, 57, 1000, 1000],      # 100,0 %  5,7 GHz  c.max 100,0 %
                                            # 100,0 °C — un CPU à 100 °C bride
                                            # déjà : c'est le pire cas PLAUSIBLE,
                                            # ⛔ pas le plafond de 150,0
        "gpu": [1000, 950, 3500, 30000],    # 100,0 %  95,0 °C  350 W  3000 tr/min
        "ram": [999, 342],                  # 99,9 %   34,2 Go
        # ⚠️ CES DEUX-LÀ ONT ÉTÉ CORRIGÉS APRÈS UN TIR : la première version
        #    envoyait 9 999 999 dixièmes de Mb/s, au-dessus du plafond de
        #    `k_metriques[]` (1 000 000) ⇒ **8 `rejets_bornes`** et rien à
        #    l'écran. Le pire cas doit rester DANS la grammaire, sinon on ne
        #    mesure pas la lisibilité, on mesure le parseur.
        #    ✅ Effet de bord utile : ce tir a prouvé que `rejets_bornes`
        #       s'incrémente sur une v3 hors plafond — ET LUI SEUL.
        "net": [999999, 999999],            # 99999,9 Mb/s des deux côtés
        # MESURÉS le 2026-08-21 (AC3, un canal poussé à 100 % à la fois) :
        #   fan/0 TOP_OUT 2432 · fan/4 REAR_OUT 2446 ⇒ moyenne 2439
        #   fan/1 CPU_NOCTUA 1112 · fan/2 CASE_GROUP 2424
        # ⚠️ `CPU_NOCTUA` plafonne BAS (1112) et ce n'est pas une anomalie : un
        #    gros Noctua bi-ventilateur plafonne vers 1200-1500, JAMAIS 2432.
        #    C'est même l'inférence qui a tenu quand l'ordre naïf a été réfuté.
        "disk": [999999, 24390, 11120, 24240],
    },
    # 🔴 CE JEU A MENTI, ET IL A FAIT TIRER UNE CONCLUSION FAUSSE À L'OWNER.
    #    Il était étiqueté « ce que la tour rend VRAIMENT (mesuré, n=959) » alors
    #    que SEULS `cpu` et `gpu` venaient de la mesure : `net`, `ram` et `disk`
    #    avaient été RECOPIÉS de la maquette illustrative de l'addendum §1.
    #    ⚠️ Résultat : l'écran affichait « ↓ 985,0 Mb/s ↑ 48,0 Mb/s » sous une
    #       étiquette « réel », et l'owner a demandé, en séance, *« je suis
    #       étonné que mon PC dl et upload autant, qu'est-ce qu'il fait ? »*.
    #       La tour était en fait à **0,0 Mb/s dans les deux sens** (vérifié par
    #       `psutil.net_io_counters()` sur 5 s, le 2026-08-19).
    # ⛔ C'EST EXACTEMENT LE MENSONGE D'INTERFACE QUE CE DÉPÔT TRAQUE, commis par
    #    l'INSTRUMENT au lieu du produit — et c'est pire, parce qu'un instrument
    #    est là pour être cru.
    # ⇒ RÈGLE : chaque nombre de ce jeu porte SA provenance et SA date. Un
    #   nombre sans provenance n'a rien à faire dans un jeu nommé « reel ».
    "reel": {
        # MESURÉS le 2026-08-19, session de 959 échantillons / 16 min :
        "cpu": [52, 32, 350, 410],          # 5,2 %   3,2 GHz   c.max 35,0 %
        # ⚠️ LA 4ᵉ VALEUR N'A PAS LA MÊME PROVENANCE QUE LES TROIS PREMIÈRES, ET
        #    ÇA S'ÉCRIT : 41,0 °C vient de `/intelcpu/0/temperature/10`
        #    (« CPU Package ») relevé le **2026-08-21**, et c'est un **INSTANTANÉ
        #    n = 1**, ⛔ pas une session de 959 échantillons.
        #    ✅ Recoupé par un chemin INDÉPENDANT le même jour : le Super I/O
        #       `/lpc/nct6792d/0/temperature/0` rendait 40,5 °C (1,2 % d'écart).
        #    ⛔ Ça conforte le MAPPING, ça ne QUALIFIE PAS le mouvement (AC4).
        "gpu": [0, 460, 500, 5980],         # 0,0 %   46,0 °C   50 W   598 tr/min
        # MESURÉS le 2026-08-19 par un tir psutil de 5 s sur la tour :
        "ram": [489, 319],                  # 48,9 %  31,9 Gio (⚠️ Windows écrit « Go »)
        "net": [0, 0],                      # 0,0 Mb/s dans LES DEUX SENS — la tour
                                            # ne faisait RIEN sur le réseau
        "disk": [2, 9795, 2839, 8615],      # 0,2 Mo/s (2026-08-19)
        # MESURÉS le 2026-08-21, LHM 0.9.6 via /metrics — ⚠️ INSTANTANÉ n = 1 :
        #   extraction moyenne 979,5 tr/min  (TOP_OUT 667,4 + REAR_OUT 1291,6)/2
        #   CPU_NOCTUA         283,9 tr/min  (`fan/1`)
        #   CASE_GROUP         861,5 tr/min  (`fan/2`)
        # ⛔ CES QUATRE NOMBRES N'ONT PAS LA MÊME DATE NI LA MÊME MÉTHODE que le
        #    `0,2 Mo/s`. Un jeu « reel » dont les provenances sont mélangées SANS
        #    LE DIRE est exactement ce qui a fait tirer une conclusion fausse à
        #    l'owner en séance. ⇒ chaque ligne porte la sienne.
    },
    # La maquette de l'addendum §1 — 🔴 SES NOMBRES SONT ILLUSTRATIFS, ET C'EST
    # D'ICI QUE `net` ET `disk` AVAIENT ÉTÉ RECOPIÉS DANS « reel » PAR ERREUR.
    "nominal": {
        # ⚠️ dn4-8 : la °C du CPU est le VERBATIM de la maquette (« CPU 54°C »).
        #    Les trois `tr/min` de `disk`, eux, sont ILLUSTRATIFS — la maquette
        #    ne montrait qu'une case `VENTILOS` sans chiffres. ⛔ Ne jamais les
        #    citer comme une mesure : ce jeu sert à REGARDER une mise en page.
        "cpu": [540, 47, 880, 540],
        "gpu": [460, 610, 2120, 14500],
        "ram": [664, 342],
        "net": [9850, 480],
        "disk": [4800, 12000, 8000, 14000],
    },
    # W10 : un TROU INTERNE. La °C du GPU manque, le reste est là.
    # ⛔ C'est le témoin que l'absence est une DONNÉE, pas un silence global.
    # 🔴 dn4-8 : LE TROU EST DÉSORMAIS SUR LES GRANDEURS **LHM**, et c'est le
    #    témoin d'AC8 en version INJECTÉE — celui qu'on peut rejouer sans
    #    toucher au service sur la tour.
    #    · `cpu` : la °C manque (index 3, en QUEUE) ⇒ la trame est TRONQUÉE à 3
    #      valeurs. ⚠️ C'est le comportement voulu : « je n'ai que trois
    #      grandeurs » et « ma quatrième est inconnue » sont le MÊME fait ici.
    #    · `disk` : le `CPU_NOCTUA` manque (index 2, INTERNE) ⇒ **champ VIDE**,
    #      et 🎯 **la valeur SUIVANTE ne doit PAS être décalée** — c'est LE
    #      contrôle discriminant, celui qu'un `strtok` aurait raté en silence.
    "trou": {
        "cpu": [540, None, 880, None],
        "gpu": [460, None, 2120, 14500],
        "ram": [664, 342],
        "net": [9850, 480],
        "disk": [4800, 12000, None, 14000],
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# dn4-23 / AC3 — UN JEU DONT LES VALEURS **VARIENT**
# ═══════════════════════════════════════════════════════════════════════════
#
# 🔴 LE DÉFAUT, ATTRAPÉ PAR L'ŒIL DE L'OWNER, DEUX FOIS, ET IL EST DE FAMILLE :
#    **les QUATRE jeux ci-dessus sont des dictionnaires de CONSTANTES.** Une
#    valeur qui ne change pas ne change pas le TEXTE ; un texte qui ne change
#    pas n'invalide RIEN ; et LVGL ne redessine que ce qui est invalidé.
#    ⇒ Un injecteur à valeurs figées produit du TRAFIC sans produire du DESSIN.
#
#    📊 CE QUE ÇA A COÛTÉ, MESURÉ :
#      · jeu `reel` figé  ⇒  **94 645 px/cycle**   contre **128 613** avec
#        `widget mock on` — stimulus **36 % plus faible** ;
#      · corruption       ⇒  **0,005 /s** à l'injecteur contre **0,54 /s** sous
#        agent réel — **FACTEUR 108.**
#
# 🔴 LA RÈGLE, ÉCRITE LÀ OÙ ELLE S'APPLIQUE :
#    ⛔ **TOUT CHIFFRE OÙ LE *DESSIN* EST LA VARIABLE SE MESURE SOUS AGENT
#      RÉEL, OU AVEC UN JEU VARIABLE.** Jamais avec `pire`/`reel`/`nominal`/
#      `trou`, qui sont des témoins de MISE EN PAGE, ⛔ pas des régimes.
#
# ⛔ CE JEU NE REMPLACE AUCUN DES QUATRE. `pire` garde son rôle de pire cas
#    plausible, `reel` ses provenances datées ligne par ligne, `nominal` la
#    maquette, `trou` le témoin du champ vide. Les retirer ferait perdre quatre
#    témoins pour en gagner un.
#
# ⚠️ LES BORNES SONT CELLES DE `k_metriques[]` (`dn_link.c`), ⛔ pas des
#    arrondis : au-delà, la trame part en `rejets_bornes` et on mesurerait LE
#    PARSEUR, pas le dessin. C'est la leçon du tir à 9 999 999.
#      cpu  {1000, 1000, 1000, 1500}   gpu  {1000, 1500, 10000, 100000}
#      ram  {1000, 40000}              net  {1000000, 1000000}
#      disk {1000000, 100000, 100000, 100000}
#
# ⚠️ LES PÉRIODES SONT PREMIÈRES ENTRE ELLES — **16** d'entre elles, de 7 à
#    67 s (la table ci-dessus fait foi ; ⛔ ce commentaire ne les récite plus :
#    il en listait SIX, périmées par la table qui les suit de trois lignes.
#    Corrigé par la revue du 2026-08-31 — même famille que les autres chiffres
#    récités de cette story). ET
#    CE N'EST PAS UNE COQUETTERIE : des rampes en phase feraient changer les six
#    cases dans le MÊME cycle LVGL, donc un flush groupé — c'est-à-dire
#    exactement l'artefact que `dn_link_etalement` sert à mesurer. Un stimulus
#    qui synchronise ce que le réel désynchronise n'est pas un stimulus réel.
#
# ⛔ LES SIX SOURCES RÉELLES NE SONT PAS SYNCHRONISÉES NON PLUS (liaison ~1 s,
#    capteur 5 s, mocks 14/20/26/34 s, barre à la minute). Ces rampes ne
#    PRÉTENDENT PAS reproduire ce régime — elles font VARIER, ce qu'aucun jeu
#    ne faisait. Le rapport au réel se mesure sur la carte (AC3.5).
JEUX_RAMPES = {
    #  métrique : [(bas, haut, période_s), … une par grandeur]
    #  ⚠️ SEIZE PÉRIODES, SEIZE NOMBRES PREMIERS **TOUS DIFFÉRENTS**. La
    #     première rédaction en réutilisait (7 et 11 sur `cpu` ET sur `net`) et
    #     le témoin l'a laissée passer : sa garde exemptait les périodes ÉGALES,
    #     qui sont pourtant LE pire cas de synchronisation. ⇒ garde corrigée,
    #     table corrigée. **Une gate scopée plus étroit que la propriété qu'elle
    #     annonce épingle vert le défaut qu'elle existe pour attraper.**
    "cpu": [(30, 1000, 7), (20, 57, 11), (30, 1000, 13), (300, 900, 17)],
    "gpu": [(0, 1000, 19), (350, 950, 23), (100, 3500, 29), (0, 30000, 31)],
    "ram": [(200, 999, 37), (100, 342, 41)],
    "net": [(0, 999999, 43), (0, 999999, 47)],
    "disk": [(0, 999999, 53), (0, 24390, 59), (0, 11120, 61), (0, 24240, 67)],
}

# Les jeux dont les valeurs NE BOUGENT PAS. ⛔ Relu de `JEUX`, ⛔ pas recopié :
# une liste écrite se périmerait au premier jeu ajouté — la thèse de `dn4-16`.
JEUX_FIXES = tuple(sorted(JEUX))


def _rampe(t, bas, haut, periode):
    """Rampe TRIANGULAIRE (monte puis descend), en dixièmes comme le fil.

    ⛔ Pas une dent de scie : le saut de `haut` à `bas` en une trame produirait
       un écart que le réel ne produit jamais, et `dn_link` le compterait
       comme une donnée légitime — on mesurerait le pire cas de rafraîchissement
       en croyant mesurer un régime.
    """
    x = (t % periode) / float(periode)
    tri = 2.0 * x if x < 0.5 else 2.0 * (1.0 - x)
    return int(round(bas + (haut - bas) * tri))


def valeurs_rampes(metrique, t):
    """Les valeurs de `metrique` à l'instant `t` (secondes, relatif au tir)."""
    return [_rampe(t, b, h, p) for (b, h, p) in JEUX_RAMPES[metrique]]


def hors_bornes(bornes):
    """TÉMOIN, jouable SANS CARTE : aucune rampe ne sort de `k_metriques[]`.

    ⛔ Une rampe hors bornes ferait partir la trame en `rejets_bornes` et
       l'écran ne montrerait RIEN — on mesurerait le parseur. `bornes` est le
       dict `{métrique: [max, …]}` relu de `dn_link.c` par l'appelant.
    """
    fautes = []
    for m, rampes in JEUX_RAMPES.items():
        if m not in bornes:
            fautes.append("%s : métrique absente de k_metriques[]" % m)
            continue
        if len(rampes) != len(bornes[m]):
            fautes.append("%s : %d rampe(s) pour %d grandeur(s) déclarées"
                          % (m, len(rampes), len(bornes[m])))
            continue
        for i, (bas, haut, per) in enumerate(rampes):
            if bas < 0 or haut > bornes[m][i]:
                fautes.append("%s[%d] : [%d ; %d] hors de [0 ; %d]"
                              % (m, i, bas, haut, bornes[m][i]))
            if haut <= bas:
                fautes.append("%s[%d] : rampe PLATE (%d..%d) — elle ne varie pas"
                              % (m, i, bas, haut))
            if per <= 0:
                fautes.append("%s[%d] : période %d s" % (m, i, per))
    return fautes


def bornes_relues(texte=None):
    """Les plafonds de `k_metriques[]`, **RELUS de `dn_link.c`**.

    ⛔ ⛔ PAS RECOPIÉS ICI. Un témoin qui compare une copie des bornes à une
       copie des rampes mesure l'accord de deux copies entre elles — et il
       resterait VERT le jour où `dn_link.c` baisse un plafond. C'est le même
       motif que `veille_accents_collisions()`, qui RELIT les couleurs au lieu
       de les recomposer.
    ⚠️ Rend `None` si le fichier est introuvable : le témoin le DIT et rougit,
       ⛔ il ne se tait pas.
    ⚠️ `texte` n'existe QUE pour le témoin : sans lui, la garde anti-commentaire
       ci-dessous serait invérifiable (aucun `k_metriques[]` livré ne porte de
       commentaire aujourd'hui, donc la muter ne changerait RIEN et le témoin
       resterait vert sur une garde morte — c'est le défaut que la revue du
       2026-08-31 a trouvé sur trois gates de ce dépôt).
    """
    import re as _re
    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(racine, "firmware", "desknode", "main", "dn_link.c")
    if texte is None:
        if not os.path.exists(src):
            return None
        with open(src, encoding="utf-8") as f:
            texte = f.read()
    txt = texte
    # 🔴 REVUE DU 2026-08-31 — `\{([^}]*)\}` PUIS « TOUS LES CHIFFRES » RECOLTAIT
    #    AUSSI CE QUI EST DANS LES COMMENTAIRES. Un `{1000u, /* 100,0 % */ 1000u}`
    #    (ou un hexa `0x3E8`, qui rend `0`, `3`, `8`) DECALE la liste ⇒
    #    `hors_bornes()` compare alors les rampes a des nombres qui NE SONT PAS
    #    les plafonds : exactement la defaillance « copie contre copie » que le
    #    docstring de cette fonction existe pour empecher.
    txt = _re.sub(r"/\*.*?\*/", " ", txt, flags=_re.S)
    txt = _re.sub(r"//[^\n]*", " ", txt)
    out = {}
    for m in _re.finditer(
            r'\[DN_LINK_M_[A-Z]+\]\s*=\s*\{\s*"(\w+)"\s*,\s*(\d+)\s*,\s*\{([^}]*)\}',
            txt):
        nom, n, maxs = m.group(1), int(m.group(2)), m.group(3)
        # ⛔ Et on refuse l'hexa plutot que de le hacher en morceaux.
        if _re.search(r"0[xX][0-9a-fA-F]+", maxs):
            return None
        vals = [int(x) for x in _re.findall(r'(\d+)u?', maxs)]
        out[nom] = vals[:n]
    return out or None


def _ecrire_brut(d, nom, contenu):
    """Écrit un fichier tel quel — pour les témoins de relevé ILLISIBLE."""
    c = os.path.join(d, nom)
    with open(c, "w", encoding="utf-8") as f:
        f.write(contenu)
    return c


def temoin_negatif_rampes():
    """AC3.1 — LE TÉMOIN, JOUABLE **SANS CARTE**.

    ⛔ *« Une gate qu'aucun test n'a vue échouer est décorative »*. Il porte donc
       ses DEUX sens : les rampes livrées doivent PASSER, et une rampe
       délibérément fautive doit ROUGIR.
    """
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
    print("dn4-23 / AC3 — LE JEU VARIABLE, ÉPROUVÉ SANS CARTE")
    print("=" * 78)
    bornes = bornes_relues()
    ctrl(bornes is not None,
         "les bornes sont RELUES de `dn_link.c`",
         "⛔ jamais recopiées ici")
    if bornes is None:
        print("BILAN : %d OK, %d KO" % (ok, ko + 1))
        return 1
    print("  bornes relues : %s"
          % " · ".join("%s%s" % (k, v) for k, v in sorted(bornes.items())))
    fautes = hors_bornes(bornes)
    ctrl(not fautes, "AUCUNE rampe ne sort de `k_metriques[]`",
         "; ".join(fautes)[:30] or "0 faute")
    ctrl(sorted(JEUX_RAMPES) == sorted(bornes),
         "les 5 métriques du fil sont TOUTES rampées",
         "%d / %d" % (len(JEUX_RAMPES), len(bornes)))

    # ⛔ LE TÉMOIN QUI DOIT ROUGIR — sans lui, `hors_bornes()` pourrait rendre
    #    la liste vide en toute circonstance et ce bloc resterait vert.
    garde = dict(JEUX_RAMPES)
    try:
        JEUX_RAMPES["cpu"] = [(30, 99999, 7), (20, 57, 11), (30, 1000, 13),
                              (300, 900, 17)]
        ctrl(bool(hors_bornes(bornes)),
             "MUTANT : une rampe HORS bornes fait ROUGIR", "cpu[1] à 99 999")
        JEUX_RAMPES["cpu"] = [(500, 500, 7), (20, 57, 11), (30, 1000, 13),
                              (300, 900, 17)]
        f = hors_bornes(bornes)
        ctrl(any("PLATE" in x for x in f),
             "MUTANT : une rampe PLATE fait ROUGIR",
             "⛔ c'est le défaut d'origine")
    finally:
        JEUX_RAMPES.clear()
        JEUX_RAMPES.update(garde)
    ctrl(not hors_bornes(bornes), "…et l'état livré est RESTAURÉ", "")

    # Les valeurs VARIENT réellement — ⛔ un jeu « variable » constant serait
    #    le même défaut sous un autre nom.
    for m in sorted(JEUX_RAMPES):
        vues = {tuple(valeurs_rampes(m, t)) for t in range(0, 60)}
        ctrl(len(vues) >= 30, "« %s » prend >= 30 valeurs distinctes en 60 s" % m,
             "%d" % len(vues))
    # Les périodes sont premières entre elles, sinon les cases changent en phase.
    # 🔴 CETTE GARDE A ÉTÉ CORRIGÉE PAR SON PROPRE ÉCHEC. Elle exemptait les
    #    périodes ÉGALES (`per[i] != per[j]`) — c'est-à-dire le cas le PLUS
    #    synchronisé de tous. Elle rendait donc « 0 paire liée » sur une table
    #    qui réutilisait 7 et 11 deux fois. ⛔ Deux rampes de même période sont
    #    en phase PAR CONSTRUCTION.
    from math import gcd
    per = [p for r in JEUX_RAMPES.values() for (_, _, p) in r]
    paires_liees = sum(1 for i in range(len(per)) for j in range(i + 1, len(per))
                       if gcd(per[i], per[j]) != 1)
    ctrl(paires_liees == 0,
         "les périodes sont premières entre elles deux à deux",
         "%d paire(s) liée(s) — égales INCLUSES" % paires_liees)
    ctrl(len(set(per)) == len(per),
         "…et les %d périodes sont TOUTES DIFFÉRENTES" % len(per),
         "%d distinctes" % len(set(per)))
    ctrl("rampe" not in JEUX,
         "`rampe` ne REMPLACE aucun des quatre jeux témoins",
         "pire/reel/nominal/trou intacts")
    ctrl(len(JEUX) == 4 and set(JEUX) == {"pire", "reel", "nominal", "trou"},
         "…et les quatre sont toujours là", " · ".join(sorted(JEUX)))

    print("\n── REVUE 2026-08-31 : les trous que la revue a trouvés ────────")
    # (1) LA BANNIÈRE NE RÉCITE PLUS LA PRÉMISSE RÉFUTÉE.
    import contextlib as _c
    import io as _io
    for j in ("pire", "rampe"):
        t = _io.StringIO()
        with _c.redirect_stdout(t):
            banniere_jeu(j)
        v = t.getvalue()
        # ⛔ LE TEST N'EST PAS « le nombre a disparu » : nommer un repère RÉFUTÉ
        #   pour dire de ne PAS s'y comparer est exactement ce qu'on veut. Le
        #   test est : s'il apparaît, il apparaît AVEC sa réfutation.
        ctrl("36 %" not in v and "presque pas.**" not in v
             and ("94 645" not in v or "NE SE REPRODUIT PAS" in v),
             "bannière « %s » ne VEND plus le repère réfuté" % j,
             "⛔ « 36 % de stimulus en moins » a disparu")
    t = _io.StringIO()
    with _c.redirect_stdout(t):
        banniere_jeu("rampe")
    ctrl("MÊME" in t.getvalue() and "11,37 M px" in t.getvalue(),
         "…et elle publie CE QUI A ÉTÉ MESURÉ à la place",
         "aire cumulée IDENTIQUE, 3 passes chacun")
    t = _io.StringIO()
    with _c.redirect_stdout(t):
        banniere_jeu("pire")
    ctrl("108" in t.getvalue(),
         "…mais le facteur 108 (corruption) SURVIT",
         "c'est une AUTRE mesure, ⛔ pas réfutée")

    # (2) `--latence-delta` REFUSE DEUX STIMULI DIFFÉRENTS.
    import json as _j
    import tempfile as _tf
    def _releve(d, jeu, esp, sec, moys):
        c = os.path.join(d, "%s.json" % jeu)
        with open(c, "w", encoding="utf-8") as f:
            _j.dump({"firmware": "aaaaaaa", "jeu": jeu, "espacement": esp,
                     "secondes_par_fenetre": sec,
                     "fenetres": [{"fenetre": i + 1, "n": 9, "min": m - 5,
                                   "moy": m, "max": m + 5}
                                  for i, m in enumerate(moys)]}, f)
        return c
    with _tf.TemporaryDirectory() as d:
        a1 = _releve(d, "pire", 0.2, 10, [10, 12, 11, 13, 10])
        b1 = _releve(d, "rampe", 0.01, 120, [300, 310, 305, 299, 302])
        t = _io.StringIO()
        with _c.redirect_stdout(t):
            rc = verbe_latence_delta(a1, b1)
        ctrl(rc == 1 and "PAS ÉTÉ PRIS SOUS LE MÊME" in t.getvalue(),
             "🔴 deux STIMULI différents ⇒ delta REFUSÉ",
             "⛔ publiait « +294,0 ms » et rc 0")
        b2 = _releve(d, "pire2", 0.2, 10, [300, 310, 305, 299, 302])
        os.replace(b2, os.path.join(d, "b2.json"))
        with open(os.path.join(d, "b2.json"), encoding="utf-8") as f:
            o = _j.load(f)
        o["jeu"] = "pire"
        o["firmware"] = "bbbbbbb"
        with open(os.path.join(d, "b2.json"), "w", encoding="utf-8") as f:
            _j.dump(o, f)
        t = _io.StringIO()
        with _c.redirect_stdout(t):
            rc = verbe_latence_delta(a1, os.path.join(d, "b2.json"))
        ctrl(rc == 0, "…et le MÊME stimulus reste comparable", "AC7.2 intact")
        # ⛔ ON EXIGE LES VALEURS, ⛔ pas le libellé : « étendue OBSERVÉE non
        #   transmise » contient aussi les mots « étendue OBSERVÉE ».
        ctrl("[5 ; 18]" in t.getvalue() and "non transmise" not in t.getvalue(),
             "…et l'étendue OBSERVÉE est publiée AVEC ses valeurs",
             "observé [5 ; 18] ⛔ pas moyennes [10 ; 13]")
        # (3) UN RELEVÉ ILLISIBLE EST UN REFUS, ⛔ PAS UNE TRACE.
        # ⛔ CES TROIS-LÀ PORTENT LE **MÊME** STIMULUS QUE `a1` : sinon le
        #   refus tombe sur l'écart de stimulus et le témoin passe POUR LA
        #   MAUVAISE RAISON — vérifié, c'était le cas.
        _stim = '"jeu":"pire","espacement":0.2,"secondes_par_fenetre":10'
        for mauvais, quoi in ((os.path.join(d, "absent.json"), "chemin ABSENT"),
                              (_ecrire_brut(d, "tronque.json",
                                            '{%s,"fenetres":' % _stim),
                               "JSON TRONQUÉ"),
                              (_ecrire_brut(d, "vide.json",
                                            '{%s,"fenetres":[]}' % _stim),
                               "relevé SANS fenêtre"),
                              (_ecrire_brut(d, "vieux.json",
                                            '{%s,"fenetres":[{"n":9}]}' % _stim),
                               "relevé SANS `moy`")):
            t = _io.StringIO()
            with _c.redirect_stdout(t):
                rc = verbe_latence_delta(mauvais, a1)
            ctrl(rc == 1 and "REFUS" in t.getvalue(),
                 "🔴 %s ⇒ REFUS" % quoi, "⛔ pas une trace Python")

    # (4) LES BORNES NE SE RÉCOLTENT PLUS DANS LES COMMENTAIRES.
    poison = ('[DN_LINK_M_CPU] = { "cpu", 4, {1000u, /* 100,0 % */ 1000u,'
              ' 1000u, 1000u} },')
    b_poison = bornes_relues(poison)
    ctrl(b_poison == {"cpu": [1000, 1000, 1000, 1000]},
         "un COMMENTAIRE dans `k_metriques[]` ne décale plus les bornes",
         "lu : %s" % (b_poison or {}).get("cpu"))
    hexa = '[DN_LINK_M_CPU] = { "cpu", 2, {0x3E8, 1000u} },'
    ctrl(bornes_relues(hexa) is None,
         "…et un plafond en HEXA fait RENDRE `None`, ⛔ pas 3 morceaux",
         "0x3E8 donnait 0 · 3 · 8")

    if ko == 0:
        print("BILAN : %d OK, 0 KO" % ok)
        return 0
    print("BILAN : %d OK, %d KO" % (ok, ko))
    return 1


def injecter(ser, a):
    """Le tir lui-même : `a.secondes` a 1 Hz. Rend `(emises, refus)`.

    🔴 CORRIGÉ PAR LA REVUE DU 2026-08-31 — **CET OUTIL ÉCRIVAIT ET JETAIT LA
       RÉPONSE.** « N trames emises » était un COMPTE D'ÉCRITURES CÔTÉ HÔTE, ⛔
       pas un compte d'acceptations : le tampon rendu par la carte était lu
       (`ser.read`) uniquement pour ne pas saturer, puis **jeté sans être
       regardé**, et `main()` rendait 0 quoi qu'il arrive. C'est exactement le
       défaut d'AC1/AC2 — celui des deux fenêtres de 90 s qui ont rendu « 0 »
       sur un stimulus jamais démarré — **recréé dans l'outil qui PRODUIT le
       stimulus**. Un compteur que personne ne lit ne compte pas ; une réponse
       que personne ne lit non plus.

    ⚠️ EXTRAIT DE `main()` PAR dn4-23 SANS UNE LIGNE DE CHANGEMENT DE
       COMPORTEMENT : la campagne de latence a besoin de tirer N fois, et
       recopier la boucle en aurait fait DEUX qui derivent. Le depot a deja paye
       ca (le balayage de date ecrit trois fois, trois valeurs, aucune juste).
    """
    variable = (a.jeu == "rampe")
    jeu = JEUX_RAMPES if variable else JEUX[a.jeu]
    seq = 0
    t0 = time.monotonic()
    n = 0
    echo = bytearray()
    while time.monotonic() - t0 < a.secondes:
        cycle = time.monotonic()
        t_ms = int((cycle - t0) * 1000) & 0xFFFFFFFF
        for m in jeu:
            # dn4-23/AC3 : sur `rampe`, les valeurs sont CALCULEES a chaque
            # cycle. ⛔ Sur les quatre autres, elles sont figees — et c'est
            # tout le defaut que ce jeu-ci existe pour fermer.
            vs = valeurs_rampes(m, cycle - t0) if variable else jeu[m]
            # 🔴 `seq` N'EST CONSOMME QUE PAR UNE TRAME REELLEMENT EMISE —
            #    CORRECTIF DE REVUE DU 2026-08-19. Il etait incremente AVANT
            #    le `continue` : en v1, une seule metrique sur cinq part, donc
            #    le firmware voyait seq 1, 6, 11... et comptait
            #    `pertes_seq += saut - 1` = QUATRE pertes par cycle
            #    (`dn_link.c`, la branche `saut > 1`).
            # ⛔ Et la v1 est LE TEMOIN DE NON-REGRESSION d'AC7/AC13 :
            #    l'instrument fabriquait des pertes sur la garde meme qu'il
            #    doit valider. Un compteur pollue par l'emetteur ne prouve
            #    rien sur le recepteur.
            if a.version == 1 and m != "cpu":
                continue  # v1 ne connaît QUE `cpu` — le reste serait rejeté
            seq += 1
            tr = trame(seq, t_ms, m, vs, a.version)
            if a.checksum_faux:
                # ⛔ On casse le checksum, ⛔ PAS la grammaire : la trame doit
                #    traverser TOUT le parseur (decoupage, version, metrique)
                #    et ne tomber qu'a la toute derniere garde. Sinon on ne
                #    mesurerait pas le meme travail.
                tr = tr[:-2] + ("00" if not tr.endswith("00") else "11")
            ser.write((f"pc {tr}\n").encode("ascii"))
            ser.flush()
            n += 1
            # ⚠️ Le REPL rend l'invite entre deux commandes ; on draine ce
            #    qu'il renvoie, sinon le tampon d'entree finit par saturer et
            #    les trames suivantes arrivent TRONQUEES — donc comptees en
            #    `rejets_tronquee` alors que l'emetteur allait bien.
            time.sleep(a.espacement)
            # ⛔ CE QUI EST LU EST DÉSORMAIS **REGARDÉ**, ⛔ plus jeté.
            echo.extend(ser.read(ser.in_waiting or 0))
        reste = 1.0 - (time.monotonic() - cycle)
        if reste > 0:
            time.sleep(reste)
    refus = dn_console.chercher_refus(echo.decode("utf-8", "replace"))
    print(f"[injecteur] {n} trames ECRITES. ⚠️ les cases retombent a « -- » "
          f"dans 3 s — c'est la peremption, PAS une regression.")
    if refus:
        print("[injecteur] 🔴 %d REFUS LU(S) DANS LA RÉPONSE DE LA CARTE — ⛔ ces"
              % len(refus))
        print("[injecteur]    trames-là n'ont PAS été acceptées. « %d écrites »"
              % n)
        print("[injecteur]    ⛔ ne veut donc PAS dire « %d reçues »." % n)
        for nom, ligne in refus[:6]:
            print("[injecteur]      · [%s] %s" % (nom, ligne[:60]))
        if len(refus) > 6:
            print("[injecteur]      · … et %d autre(s)." % (len(refus) - 6))
    else:
        print("[injecteur] ✅ aucun refus lu dans la réponse de la carte.")
        print("[injecteur]    ⚠️ « aucun refus LU » ⛔ n'est pas « tout accepté » :"
              " seul")
        print("[injecteur]       `pc` (compteurs de liaison) dit ce qui est"
              " ENTRÉ.")
    sys.stdout.flush()
    return n, refus


def banniere_jeu(nom):
    """AC3.3 — L'INJECTEUR DIT AU DÉMARRAGE SI SON JEU EST **FIXE**, ET CE QUE
    ÇA INTERDIT DE CONCLURE.

    ⛔ Pas un avertissement de confort : sans lui, un opérateur relève un
       px/cycle sous un jeu figé et le compare à un relevé sous agent réel. Les
       deux chiffres existent, ils sont justes, et leur COMPARAISON est fausse
       d'un facteur qui a été mesuré jusqu'à **108**.

    🔴 **CORRIGÉ PAR LA REVUE DU 2026-08-31 — CETTE BANNIÈRE RÉCITAIT COMME
       « MESURÉ » CE QUE LA SÉANCE DU MÊME JOUR AVAIT RÉFUTÉ.** Elle affirmait
       *« le dessin ne se déclenche presque pas »* et *« 94 645 px/cycle (figé)
       contre 128 613, soit 36 % de stimulus en moins »*. La séance a mesuré
       l'inverse : **l'aire cumulée est LA MÊME, jeu fixe ou jeu variable**
       (11,37 M px à 1 % près, 3 passes chacun) ⇒ **le jeu variable ne fait PAS
       dessiner plus**, et l'écart 94 645 ⇄ 128 613 mesurait **LA CADENCE**
       (1 Hz contre 14/20/26/34 s), ⛔ pas la fixité.
    ⛔ ET LE REPÈRE `94 645` NE SE REPRODUIT PAS : le même `--jeu reel` a rendu
       **46 572 · 71 984 · 74 576** px/cycle, soit −21 % à −51 %. Il n'est donc
       plus cité comme repère. Le repère `mock`, lui, TIENT (124 750 contre
       128 613, deux fois à 250 px près).
    ✅ CE QUI SURVIT, ET C'EST UNE **AUTRE** MESURE : **0,005 corruption/s
       contre 0,54 /s sous agent réel — facteur 108**. C'est ça, et ça seul, qui
       rend un jeu figé impropre à décrire un régime réel.
    ⚠️ Cette bannière était **capturée dans la preuve d'AC7 de la story**,
       imprimée APRÈS la réfutation. Un instrument qui SUR-annonce est du même
       genre que celui qui se tait.
    """
    if nom == "rampe":
        print("[injecteur] ✅ JEU VARIABLE (rampes triangulaires, périodes "
              "premières entre elles).")
        print("[injecteur]    Les valeurs changent à chaque cycle ⇒ le TEXTE "
              "change ⇒ LVGL invalide.")
        print("[injecteur]    ⚠️ MESURÉ le 2026-08-31 : ça ne fait PAS dessiner "
              "PLUS — l'aire cumulée")
        print("[injecteur]    est la MÊME qu'en jeu figé (11,37 M px à 1 % "
              "près, 3 passes chacun).")
        print("[injecteur]    Ce que ça change, c'est la CADENCE d'invalidation,"
              " ⛔ pas le total.")
        print("[injecteur]    ⚠️ Le rapport au régime RÉEL reste à mesurer sur "
              "la carte. Repère qui")
        print("[injecteur]    TIENT : 124 750 px/cycle avec `widget mock on` "
              "(contre 128 613 attendus).")
        print("[injecteur]    ⛔ Le repère « 94 645 en jeu figé » NE SE "
              "REPRODUIT PAS (46 572 · 71 984 ·")
        print("[injecteur]    74 576) — ⛔ ne pas s'y comparer. ⇒ Publier "
              "l'ESPACEMENT avec le chiffre :")
        print("[injecteur]    un relevé de régime sans son espacement n'est "
              "comparable à rien.")
        return
    print("[injecteur] 🔴 JEU **FIXE** — ses valeurs NE CHANGENT PAS.")
    print("[injecteur]    ⇒ le texte des cases ne change pas ⇒ LVGL invalide à "
          "une CADENCE")
    print("[injecteur]      bien plus basse (⛔ et NON : « il ne dessine "
          "presque pas » est RÉFUTÉ —")
    print("[injecteur]      l'aire CUMULÉE est la même qu'en jeu variable, "
          "11,37 M px, mesuré")
    print("[injecteur]      3 fois chacun le 2026-08-31).")
    print("[injecteur]    ⛔ NE RIEN CONCLURE SUR UN RÉGIME RÉEL avec ce jeu. "
          "CE QUI LE MESURE :")
    print("[injecteur]    0,005 corruption/s contre 0,54 /s sous agent réel — "
          "**facteur 108**.")
    print("[injecteur]    ⇒ RÈGLE : tout chiffre où le DESSIN est la variable "
          "se mesure sous")
    print("[injecteur]      AGENT RÉEL, ou avec `--jeu rampe`.")
    print("[injecteur]    ✅ Ce jeu reste JUSTE pour ce à quoi il sert : la "
          "MISE EN PAGE, la")
    print("[injecteur]      lisibilité, le pire cas de longueur de chaîne.")


# ═══════════════════════════════════════════════════════════════════════════
# dn4-23 / AC7 — LA CAMPAGNE DE LATENCE : **N FENÊTRES, ET SA DISPERSION**
# ═══════════════════════════════════════════════════════════════════════════
#
# 🔴 POURQUOI C'EST ICI ET PAS DANS `dn_console.py` : **il n'y a qu'UN port.**
#    Deux lecteurs sur le même tty ne s'excluent pas, ils se volent les octets.
#    L'instrument qui produit le stimulus DOIT donc être celui qui lit la
#    latence. Les fonctions PURES (lecture de la ligne, dispersion, refus du
#    delta) vivent, elles, dans `dn_console.py` — elles se jouent sans carte.
#
# ⛔ CE MODE N'ISOLE PAS LA VARIANCE. Il empêche de conclure sans elle.
def campagne_latence(ser, a):
    """N fenêtres consécutives sur le MÊME firmware, puis la dispersion."""
    moyennes, brut = [], []
    for k in range(a.latence):
        r = dn_console.envoyer(ser, "pc reset", 10.0)
        if r["refus"]:
            print("[latence] 🔴 REFUS sur `pc reset` : %s" % r["refus"])
            print("[latence] ⛔ La fenêtre %d n'a PAS d'origine — campagne ARRÊTÉE."
                  % (k + 1))
            return None
        n, refus_tir = injecter(ser, a)
        if refus_tir:
            print("[latence] 🔴 %d REFUS pendant le TIR de la fenêtre %d — le\n"
                  "          stimulus n'a pas été posé en entier. ⛔ Une latence\n"
                  "          mesurée sur un stimulus incomplet ne décrit rien.\n"
                  "          Campagne ARRÊTÉE." % (len(refus_tir), k + 1))
            return None
        r = dn_console.envoyer(ser, "pc", 15.0)
        if r["refus"]:
            print("[latence] 🔴 REFUS sur `pc` : %s" % r["refus"])
            return None
        # 🔴 REVUE DU 2026-08-31 — CETTE CAMPAGNE LISAIT `refus` ET IGNORAIT
        #    `completude` ET L'INVITE. Les quatre nombres de latence étaient donc
        #    acceptés d'une capture que le pilote VENAIT DE DÉCLARER INCOMPLÈTE,
        #    puis publiés, puis versés au relevé, puis comparés par
        #    `--latence-delta`. « Un compteur que personne ne lit ne compte pas »
        #    s'appliquait mot pour mot à cet appelant-ci.
        if r["invite_rendue"] is False:
            print("[latence] 🔴 fenêtre %d : l'invite n'a PAS été rendue par `pc`.\n"
                  "          ⛔ La capture est tronquée par construction.\n"
                  "          Campagne ARRÊTÉE." % (k + 1))
            return None
        cpl = r.get("completude") or {}
        if cpl.get("etat") in ("PERTE", "COMPTE_NON_FIABLE"):
            print("[latence] 🔴 fenêtre %d : la capture de `pc` est INCOMPLÈTE\n"
                  "          (%s — %s annoncées, %s reçues). ⛔ On ne lit pas une\n"
                  "          latence dans une capture dont l'instrument dit\n"
                  "          lui-même qu'il lui manque des lignes.\n"
                  "          Campagne ARRÊTÉE."
                  % (k + 1, cpl.get("etat"), cpl.get("annonce"),
                     cpl.get("recu")))
            return None
        try:
            lat = dn_console.lire_latence(r["sortie"])
        except dn_console.LatenceAmbigue as e:
            print("[latence] fenêtre %d :\n%s" % (k + 1, e))
            return None
        if lat is None:
            print("[latence] 🔴 fenêtre %d : la ligne « latence acceptation->label »\n"
                  "          est INTROUVABLE dans la sortie. ⛔ Ne rien inventer :\n"
                  "          campagne ARRÊTÉE." % (k + 1))
            return None
        n_lat, lmin, lmoy, lmax = lat
        if n_lat == 0:
            print("[latence] 🔴 fenêtre %d : n=0 poussée. Le stimulus n'a RIEN\n"
                  "          placé — ⛔ une moyenne sur zéro échantillon n'est pas\n"
                  "          une mesure. Campagne ARRÊTÉE." % (k + 1))
            return None
        moyennes.append(lmoy)
        brut.append({"fenetre": k + 1, "n": n_lat, "min": lmin, "moy": lmoy,
                     "max": lmax, "trames_emises": n})
        print("[latence] fenêtre %d/%d : n=%d · min %d · moy %d · max %d ms "
              "(%d trames émises)"
              % (k + 1, a.latence, n_lat, lmin, lmoy, lmax, n))
        sys.stdout.flush()
    return moyennes, brut


def imprimer_dispersion(d, firmware, jeu, espacement):
    print("\n" + "=" * 74)
    print("RELEVÉ DE LATENCE `acceptation→label` — firmware %s" % firmware)
    print("=" * 74)
    print("  jeu « %s » · espacement %.0f ms · %d fenêtre(s) consécutive(s)"
          % (jeu, espacement * 1000, d["n_fenetres"]))
    print("  moyennes par fenêtre : %s ms"
          % " · ".join(str(x) for x in d["fenetres"]))
    print("  min %d · médiane %.0f · max %d ms   étendue %d ms   σ %.1f ms"
          % (d["min"], d["mediane"], d["max"], d["etendue"], d["ecart_type"]))
    if d["facteur"]:
        print("  FACTEUR max/min : ×%.2f" % d["facteur"])
    print("⛔ CE RELEVÉ NE SE PUBLIE JAMAIS EN MOYENNE SEULE. Repère MESURÉ sur")
    print("   `fd959f2` : 86 · 138 · 220 · 86 · 260 ms — **facteur 3 sur le MÊME**")
    print("   **firmware**. ⇒ tant que cette variance n'est pas isolée, cet")
    print("   instrument n'est PAS un instrument de delta.")
    print("⛔ LA RÈGLE RÉFUTÉE RESTE RÉFUTÉE : « un relevé n'est recevable que si")
    print("   l'injecteur a placé 225/225 avec 0 perte seq » a été publiée puis")
    print("   DÉMOLIE par la 5ᵉ fenêtre (225/225, 0 perte seq, 260 ms — la plus")
    print("   haute). La corrélation sur quatre points était une COÏNCIDENCE.")
    print("   ⛔ Ne pas la ressusciter.")
    print("✅ DEUX HYPOTHÈSES RESTENT RÉFUTÉES, ⛔ ne pas les rejouer : la")
    print("   fragmentation du tas LVGL (relevé identique avant et après) et les")
    print("   compteurs de liaison (ils ne discriminent pas).")
    print("⚠️ CONSÉQUENCE RÉTROACTIVE : tout écart de latence publié sur UNE")
    print("   FENÊTRE UNIQUE est NON RECEVABLE, **y compris ceux de `dn4-2`**.")
    if d["n_fenetres"] < dn_console.LATENCE_FENETRES_REPERE:
        print("⚠️ %d fenêtres seulement : le repère mesuré en demande %d."
              % (d["n_fenetres"], dn_console.LATENCE_FENETRES_REPERE))


def verbe_latence_delta(chemin_a, chemin_b):
    """AC7.2 — LE DELTA ENTRE DEUX FIRMWARES, **REFUSÉ PAR L'OUTIL** quand il
    n'est pas lisible. ⛔ Pas déconseillé dans un commentaire."""
    # 🔴 REVUE DU 2026-08-31 — CE VERBE N'AVAIT **AUCUNE GARDE SUR SES DEUX
    #    FICHIERS**, alors que tout son contrat est « REFUSE le delta quand il
    #    n'est pas lisible ». Un chemin absent, un JSON tronqué, ou un relevé
    #    écrit par un outil antérieur (sans `fenetres` / `moy`) sortait en
    #    FileNotFoundError / JSONDecodeError / KeyError — c'est-à-dire en trace,
    #    ⛔ pas en refus.
    releves = []
    for c in (chemin_a, chemin_b):
        try:
            with open(c, encoding="utf-8") as f:
                releves.append(json.load(f))
        except OSError as e:
            print("🔴 REFUS : relevé ILLISIBLE — %s" % e)
            return 1
        except ValueError as e:
            print("🔴 REFUS : `%s` n'est pas un JSON exploitable — %s" % (c, e))
            return 1
        r = releves[-1]
        fen = r.get("fenetres")
        if not isinstance(fen, list) or not fen:
            print("🔴 REFUS : `%s` ne porte aucune fenêtre. ⛔ Un relevé sans\n"
                  "   fenêtres ne se compare à rien." % c)
            return 1
        if any(not isinstance(f, dict) or "moy" not in f for f in fen):
            print("🔴 REFUS : `%s` porte des fenêtres SANS champ `moy` — relevé\n"
                  "   écrit par un outil antérieur. ⛔ Ne rien deviner." % c)
            return 1
    print("A = %s (firmware %s)" % (chemin_a, releves[0].get("firmware", "?")))
    print("B = %s (firmware %s)" % (chemin_b, releves[1].get("firmware", "?")))
    if releves[0].get("firmware") == releves[1].get("firmware"):
        print("⚠️ LES DEUX RELEVÉS PORTENT LE MÊME FIRMWARE : ce n'est pas un")
        print("   delta entre firmwares, c'est une mesure de la VARIANCE. Utile,")
        print("   mais ⛔ ne pas l'étiqueter autrement.")
    # 🔴 REVUE DU 2026-08-31 — **IL REFUSAIT UN DELTA SUR UNE FENÊTRE UNIQUE ET
    #    COMPARAIT VOLONTIERS DEUX STIMULI DIFFÉRENTS.** Seul `firmware` était
    #    confronté ; `jeu`, `espacement` et `secondes_par_fenetre` sont écrits
    #    DANS LE RELEVÉ précisément pour ça, et rien ne les lisait. Reproduit :
    #    A = `pire`/0,2/10 contre B = `rampe`/0,01/120 rendait « ✅ étendues
    #    DISJOINTES … +294,0 ms », rc 0 — c'est-à-dire l'écart de stimulus
    #    ×108 qu'AC3 a mesuré, PUBLIÉ COMME UN DELTA DE FIRMWARE.
    ecarts_stim = [(cle, releves[0].get(cle), releves[1].get(cle))
                   for cle in ("jeu", "espacement", "secondes_par_fenetre")
                   if releves[0].get(cle) != releves[1].get(cle)]
    if ecarts_stim:
        print("🔴 REFUS : LES DEUX RELEVÉS N'ONT PAS ÉTÉ PRIS SOUS LE MÊME")
        print("   STIMULUS. Un delta entre eux mesure le stimulus, ⛔ pas le")
        print("   firmware — c'est l'écart ×108 qu'AC3 a mesuré.")
        for cle, va, vb in ecarts_stim:
            print("     · %-20s A = %-12s   B = %s" % (cle, va, vb))
        print("   ⇒ RE-JOUER les deux relevés avec le MÊME `--jeu`, le MÊME")
        print("     `--espacement` et les MÊMES `--secondes`.")
        return 1
    ds = [dn_console.dispersion(
              [f["moy"] for f in r["fenetres"]],
              bornes=[(f["min"], f["max"]) for f in r["fenetres"]
                      if "min" in f and "max" in f])
          for r in releves]
    for nom, d in zip("AB", ds):
        if d:
            print("  %s : %s ms  (étendue %d, σ %.1f, n=%d)"
                  % (nom, " · ".join(str(x) for x in d["fenetres"]),
                     d["etendue"], d["ecart_type"], d["n_fenetres"]))
    recevable, lignes = dn_console.verdict_delta(ds[0], ds[1])
    for l in lignes:
        print(l)
    return 0 if recevable else 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jeu", choices=sorted(list(JEUX) + ["rampe"]),
                   default="pire",
                   help="dn4-23 : « rampe » = le SEUL jeu dont les valeurs "
                        "VARIENT. Les quatre autres sont des CONSTANTES ⇒ le "
                        "dessin ne se declenche presque pas.")
    # 🔴 LE DISCRIMINATEUR DU TRESSAUTEMENT (constat owner, 2026-08-19).
    #    Émet EXACTEMENT le même trafic série, au même rythme, avec le même
    #    travail de REPL et de parseur — mais un CHECKSUM VOLONTAIREMENT FAUX,
    #    donc **AUCUNE mise à jour d'affichage**.
    #    · ça tressaute quand même ⇒ la cause est le TRAFIC (USB / console /
    #      contention de verrou), ⛔ pas le dessin ;
    #    · ça ne tressaute plus  ⇒ la cause est le DESSIN SOUS TRAFIC.
    #    ⚠️ Une seule variable change entre les deux tirs. C'est tout l'intérêt.
    # 🔴 POUR L'A/B CONTRE LE FIRMWARE DE dn4-1 (`cfd1a54`), qui ne connaît que
    #    v1 et v2. Sans ça, toutes les trames partiraient en `rejets_version` et
    #    l'A/B mesurerait DEUX firmwares sous DEUX stimuli différents — c'est-à-
    #    dire rien du tout.
    # ⚠️ En v2 le protocole plafonne à DEUX valeurs : les grandeurs 3 et 4 sont
    #    tronquées. ⛔ Le FLUSH, lui, ne change pas : le groupage invalide LE
    #    CONTENEUR, donc une case repeint la même surface quel que soit le
    #    nombre de labels réécrits. C'est ce qui rend l'A/B honnête.
    p.add_argument("--version", type=int, choices=(1, 2, 3), default=3,
                   help="version de protocole emise (2 pour le firmware dn4-1)")
    p.add_argument("--checksum-faux", action="store_true",
                   help="emet le meme trafic mais SANS aucune mise a jour "
                        "d'affichage (les trames partent en rejets_checksum)")
    p.add_argument("--secondes", type=float, default=30.0)
    # 🔴 L'ESPACEMENT DES CINQ TRAMES DANS LA SECONDE N'EST PAS UN DETAIL DE
    #    CONFORT : c'est l'axe `dn_link_etalement` (l'A/B « poussee ETALEE vs
    #    GROUPEE » de W4). Serrees, plusieurs mises a jour tombent dans le MEME
    #    cycle LVGL et le flush/cycle monte ; espacees, chacune a son cycle.
    #    ⛔ Un releve de regime (b) qui ne dit pas son espacement n'est pas
    #      comparable a un autre.
    p.add_argument("--espacement", type=float, default=0.04, metavar="S",
                   help="delai entre deux trames de la meme seconde (defaut 0,04)")
    # ⚠️ BORNE VERIFIEE AVANT D'OUVRIR LE PORT (revue 2026-08-19) : `time.sleep()`
    #    leve `ValueError` sur un negatif, et il le levait EN PLEIN TIR, port
    #    ouvert — la campagne etait perdue apres avoir consomme sa fenetre.
    #    Une seconde entiere entre deux trames n'a pas de sens non plus : les cinq
    #    ne tiendraient plus dans le cycle de 1 Hz.
    p.add_argument("--port", default=dn_console.DEFAULT_PORT)
    p.add_argument("--baud", type=int, default=dn_console.DEFAULT_BAUD)
    # ── dn4-23 / AC7 — LA CAMPAGNE DE LATENCE ─────────────────────────────
    p.add_argument("--latence", type=int, default=0, metavar="N",
                   help="dn4-23/AC7 : N FENETRES CONSECUTIVES sur le MEME "
                        "firmware (`pc reset` · tir · `pc`), puis la "
                        "DISPERSION. ⛔ Une moyenne seule ne se publie pas : "
                        "cette latence varie d'un FACTEUR 3 sur le meme "
                        "firmware (86 · 138 · 220 · 86 · 260 ms).")
    p.add_argument("--firmware", default="", metavar="SHA",
                   help="le SHA du binaire EPROUVE, LU AU BANDEAU. ⛔ Exige par "
                        "--latence : un releve sans firmware ne se compare a "
                        "rien.")
    p.add_argument("--releve", metavar="FICHIER.json",
                   help="ecrit le releve, pour `--latence-delta`")
    p.add_argument("--latence-delta", nargs=2, metavar=("A.json", "B.json"),
                   help="dn4-23/AC7.2 : compare DEUX releves et REFUSE le delta "
                        "s'il n'est pas lisible (une seule fenetre, ou etendues "
                        "qui se chevauchent). ⛔ Ne touche pas au port.")
    p.add_argument("--temoin-negatif", action="store_true",
                   help="dn4-23/AC3 : verifie SANS CARTE que les rampes tiennent "
                        "dans les bornes de `k_metriques[]`, et qu'aucune n'est "
                        "PLATE.")
    a = p.parse_args()
    if a.latence_delta:
        return verbe_latence_delta(a.latence_delta[0], a.latence_delta[1])
    if a.temoin_negatif:
        return temoin_negatif_rampes()
    if a.latence and not a.firmware:
        p.error("--latence exige --firmware <SHA lu au bandeau> : un releve "
                "qui ne dit pas QUEL binaire il a mesure ne se compare a rien.")
    if a.latence and a.jeu != "rampe":
        print("[injecteur] 🔴 --latence avec un jeu FIXE : le stimulus ne fait "
              "presque pas dessiner,")
        print("[injecteur]    donc la latence mesuree ne decrit PAS un regime "
              "de dessin. ⇒ `--jeu rampe`.")
    if not (0.0 <= a.espacement <= 0.2):
        p.error(f"--espacement {a.espacement} hors de [0 ; 0,2] s : cinq trames "
                f"doivent tenir dans le cycle de 1 Hz, et time.sleep() leverait "
                f"sur un negatif EN PLEIN TIR.")
    # 🔴 REVUE DU 2026-08-31 — `--espacement` ETAIT BORNE AVANT L'OUVERTURE DU
    #    PORT, PAS SES DEUX VOISINS. `--secondes 0` (ou negatif) faisait une
    #    boucle qui ne tourne pas : « 0 trames ECRITES », **rc 0**, INDISCERNABLE
    #    d'un tir complet. Et `--latence -1` est *truthy* : `range(-1)` est vide,
    #    la campagne rendait `([], [])` — ⛔ pas `None`, donc la garde le
    #    manquait — `dispersion([])` rendait `None`, et l'impression plantait sur
    #    `d["n_fenetres"]`, APRES avoir consomme la fenetre.
    if a.secondes <= 0:
        p.error(f"--secondes {a.secondes} : une fenetre nulle ou negative ne "
                f"tire RIEN et rendrait « 0 trames » avec rc 0, ce qui ne se "
                f"distingue pas d'un tir complet.")
    if a.latence < 0:
        p.error(f"--latence {a.latence} : un nombre de fenetres negatif est "
                f"*truthy*, donc il ouvrait le port, consommait la fenetre, et "
                f"plantait a l'impression de la dispersion.")

    variable = (a.jeu == "rampe")
    jeu = JEUX_RAMPES if variable else JEUX[a.jeu]
    rc_final = 0
    # 🔴 REVUE DU 2026-08-31 — `ConsoleErreur` N'ÉTAIT PAS ATTRAPÉE ICI. Les
    #    recettes opérateur soigneusement rédigées dans `ouvrir()` / `reveiller()`
    #    (port tenu par `idf.py monitor`, usbipd détaché après un `reboot`, carte
    #    muette) sortaient en TRACE PYTHON, alors que `dn_console.py`, lui, les
    #    imprime. Le même diagnostic, illisible d'un outil à l'autre.
    try:
        ser = dn_console.ouvrir(a.port, a.baud)
    except dn_console.ConsoleErreur as e:
        sys.stderr.write("\n✗ %s\n" % e)
        return 1
    if a.checksum_faux:
        print("[injecteur] ⚠️ CHECKSUM FAUX : meme trafic, AUCUNE mise a jour "
              "d'affichage.")
    print(f"[injecteur] protocole v{a.version}")
    print(f"[injecteur] jeu « {a.jeu} » — {a.secondes:.0f} s a 1 Hz, "
          f"espacement {a.espacement*1000:.0f} ms "
          f"(peremption 3 s : sans ca les cases retombent a « -- »)")
    banniere_jeu(a.jeu)
    print("[injecteur] ⚠️ branche A : ceci teste le CHEMIN DE CODE, pas le materiel.")
    sys.stdout.flush()

    try:
        try:
            dn_console.reveiller(ser)
        except dn_console.ConsoleErreur as e:
            sys.stderr.write("\n✗ %s\n" % e)
            return 1
        if a.latence:
            r = campagne_latence(ser, a)
            if r is None:
                return 1
            moyennes, brut = r
            d = dn_console.dispersion(
                moyennes, bornes=[(f["min"], f["max"]) for f in brut])
            imprimer_dispersion(d, a.firmware, a.jeu, a.espacement)
            if a.releve:
                with open(a.releve, "w", encoding="utf-8") as f:
                    json.dump({"firmware": a.firmware, "jeu": a.jeu,
                               "espacement": a.espacement,
                               "secondes_par_fenetre": a.secondes,
                               "fenetres": brut}, f, ensure_ascii=False, indent=2)
                print("[latence] relevé écrit : %s" % a.releve)
                print("[latence] ⇒ `--latence-delta A.json B.json` compare DEUX")
                print("          relevés, et REFUSE le delta quand il n'est pas")
                print("          lisible.")
            return 0
        _n, refus_tir = injecter(ser, a)
        if refus_tir:
            rc_final = 1
    except KeyboardInterrupt:
        pass
    finally:
        # ⚠️ On draine 0,4 s avant de fermer : une capture qui ferme trop tot
        #    laisse l'echo des dernieres trames dans le port, et la commande
        #    SUIVANTE le lit a la place de sa propre sortie (piege du depot).
        time.sleep(0.4)
        try:
            ser.read(ser.in_waiting or 0)
        except Exception:
            pass
        ser.close()
    return rc_final


if __name__ == "__main__":
    sys.exit(main() or 0)

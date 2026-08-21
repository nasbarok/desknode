#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""dn_agent.py — l'agent PC de DeskNode : publie CINQ métriques de la tour à ~1 Hz.

UN SEUL FICHIER, lancé à la main, SANS élévation, SANS driver, SANS .NET (D8 —
et c'est une FRONTIÈRE, pas une préférence : Ring0 / LibreHardwareMonitor sortent
du périmètre V1).
🔴 AMENDÉ LE 2026-08-21 PAR **D13**, ⛔ PAS EFFACÉ — LE PÉRIMÈTRE A CHANGÉ.
   `LibreHardwareMonitor` RENTRE dans le périmètre V1, **en service permanent sur
   la tour**, et cet agent LIT ses valeurs par HTTP. ⛔ MAIS LA MOITIÉ DE LA PHRASE
   QUI COMPTE RESTE VRAIE, ET C'EST ELLE QUI REND LA CHOSE ACCEPTABLE : **l'agent
   n'a toujours ni élévation, ni driver, ni .NET** — il ne fait AUCUN Ring0. C'est
   LHM qui le fait, et lui seul (tâche `RunLevel = Highest` + `PawnIO 2.2.0`).
⚠️ LE COÛT EST ASSUMÉ, ⛔ PAS OUBLIÉ : le critère owner de D8 (« générique et libre
   de droits, réutilisable sur toutes les configs ») NE TIENT PLUS pour la °C CPU
   ni pour les tr/min de boîtier. Elles ne marchent que là où LHM est installé.
   Les onze autres grandeurs, elles, restent libres de droits.
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

    $DN,3,<seq>,<t_ms>,<metrique>,<v1>[,<v2>[,<v3>[,<v4>]]]*<CK>

  🔴 9ᵉ TEXTE PÉRIMÉ, TROUVÉ EN dn4-8 (⛔ il n'était PAS dans la liste des huit).
     Ce résumé montrait encore la grammaire **v2** — deux valeurs — alors que le
     fil est en v3 depuis dn4-6 (quatre) et que `cpu` en porte quatre depuis
     dn4-8. ⚠️ Il est dans le fichier qui se déclare « document d'autorité côté
     PC », six lignes sous un avertissement qui dit qu'une grammaire recopiée
     dérive. **Elle avait dérivé.** Corrigé le 2026-08-21.

  <metrique>  cpu · gpu · ram · net · disk
  <v1>..<v4> ENTIERS, en DIXIÈMES de l'unité de la métrique. Pas de flottant sur
              le fil (doctrine `parse_entier` du firmware). Combien la métrique en
              publie est déclaré par `k_metriques[]` : cpu 4 · gpu 4 · ram 2 ·
              net 2 · disk 4.
  <v2>..<v4> OPTIONNELLES, et leur absence EST une donnée. ⛔ Pas de jeton
              « inconnu », et la règle a DEUX bouts : une grandeur absente en
              position INTERNE est un **champ VIDE** (`…,gpu,460,,530,6040*CK`) ;
              en position 0, la métrique n'est PAS ÉMISE et sa case périme seule
              en 3 s. Les `None` de QUEUE sont tronqués, pas rendus vides.
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
        🔴 AMENDÉ LE 2026-08-21 (dn4-8 / D13), ⛔ PAS EFFACÉ : « la °C CPU exige le
           Ring0 » reste VRAI — c'est le Ring0 qui est revenu, par service tiers.
           ⇒ La °C ARRIVE, en grandeur 4 (`/intelcpu/0/temperature/10`, LHM).
           ⛔ ET LA FRÉQUENCE NE PART PAS : elle a qualifié, elle est libre de
           droits, elle reste la grandeur 2. Ce que la case montrera est `dn4-9`.
        + 🔴 `max(cpu_percent(percpu=True))` (dn4-6, grandeur 3, « c.max »)
        + 🔴 `SourceLhm` (dn4-8, grandeur 4, °C) — ⚠️ EN INDEX **3** DU FIL, ⛔ PAS 2 :
             l'ordre des trois premières ne bouge pas, sinon le `c.max` d'un agent
             v3 non modifié s'afficherait comme une température **sans qu'aucun
             compteur ne bronche**. Le témoin de non-régression fabriquerait le
             mensonge qu'il est censé exclure.
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
        🔴 dn4-8 / D13 : `disk` porte MAINTENANT TROIS `tr/min` DE PLUS, lus chez
           LHM — extraction MOYENNE (`TOP_OUT`+`REAR_OUT`), `CPU_NOCTUA`,
           `CASE_GROUP`. ⛔ Le `Mo/s` GARDE la position 0 : c'est la seule des
           quatre qui survive à l'arrêt de LHM, et une position 0 absente fait que
           la métrique n'est PAS émise du tout.
        ⚠️ CE QUI TOMBE DE D13 §4.4 : la séparation LECTURE / ÉCRITURE. D13
           demandait SIX grandeurs, `DN_LINK_GRANDEURS_MAX` en donne QUATRE.
           ⇒ réduction de périmètre, portée à l'owner et au ledger — ⛔ pas un
           rognage silencieux.
  lhm   http.client -> GET /metrics sur 127.0.0.1:8085, connexion PERSISTANTE.
        ⛔ AUCUNE DÉPENDANCE NOUVELLE : `http.client` et `re` sont la stdlib.
        ✅ `/metrics` retenu PAR LA MESURE et par sa FORME (AC2, 3 campagnes) :
           l'unité y vit dans la CLÉ (`lhm_motherboard_fan_rpm`), donc un
           changement d'unité CHANGE LE NOM et SE VOIT. Dans `/data.json` elle vit
           dans la chaîne (« 43,0 °C ») : un parseur qui retire le suffixe
           accepterait « 110,0 °F » sans broncher.
        🔴 ET LE VRAI RÉSULTAT D'AC2 N'EST PAS « QUELLE INTERFACE » : c'est que
           **l'ouverture de connexion TCP dominait le coût**. Les trois candidats
           échouent le seuil C1 en connexion neuve et passent LES QUATRE en
           keep-alive. ⛔ Aucun seuil n'a bougé — l'implémentation était mauvaise.
        ⚠️ WMI éliminé PAR SYMPTÔME : `root\LibreHardwareMonitor` N'EXISTE PAS et
           `root\OpenHardwareMonitor` rend **0 instance** (issue #2143). 🔴 La
           CLASSE, elle, existe : un harnais qui aurait vérifié « la classe est-elle
           là ? » aurait conclu « WMI marche ».

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

# 🔴 dn4-8 / AC6 : DEUX MODULES DE LA **STDLIB**, ⛔ AUCUNE DEPENDANCE NOUVELLE.
#    `http.client` (⛔ pas `requests`) parce qu'il expose la CONNEXION, donc le
#    keep-alive — et l'A/B d'AC2 a montre que **l'ouverture de connexion TCP
#    dominait le cout** : les trois candidats echouent le seuil C1 en connexion
#    neuve (2,98 / 3,52 / 4,77 ms) et passent LES QUATRE seuils en keep-alive
#    (1,84 / 2,19 / 1,13 ms). `urllib.request` ne garde pas la connexion.
import http.client
import re

try:
    import psutil
except ImportError:
    sys.exit("psutil manquant : pip install --user psutil (dépendance assumée, cf. README)")

import ctypes

PROTO_VERSION = 3
PERIODE_S = 1.0

# ── LE TÉMOIN DE MAPPING PMLog — CE QU'IL VÉRIFIE, EXACTEMENT ────────────────
# 🔴 CORRECTIF DE REVUE 2026-08-18 : QUATRE textes du dépôt affirmaient que
#    l'agent « exige BUS_LANES = 16 et CLK_MEMCLK ≈ 2000 MHz » et « REFUSE de
#    servir sinon ». LE CODE N'A JAMAIS FAIT ÇA, et il a RAISON de ne pas le
#    faire — ⚠️ MAIS LE MOTIF EXACT N'EST PAS MESURÉ, ET C'EST À DIRE : l'hypothèse
#    posée en revue était qu'une Radeon RX 6000 **abaisse son lien PCIe** au repos
#    (ASPM / downtraining), donc que `BUS_LANES` rendrait 1, 4 ou 8 sur une carte
#    saine, et qu'exiger 16 ferait refuser la source GPU.
#    🔴 LA SÉANCE DU 2026-08-18 NE CONFIRME PAS CETTE HYPOTHÈSE : le témoin a rendu
#    `BUS_LANES = 16` et `CLK_MEMCLK = 1988 MHz` — soit exactement ce que les quatre
#    textes annonçaient. Un durcissement à `== 16` serait donc PASSÉ ce jour-là.
#    ⇒ Ce qui reste ACQUIS : le code vérifie une PLAGE, et les textes doivent dire
#      ce que le code fait — c'était le vrai défaut, et il est corrigé.
#    ⇒ Ce qui reste OUVERT : faut-il resserrer ? La réponse demande de relever
#      `BUS_LANES` **au repos prolongé**, ce qui n'a pas été fait. ⛔ Ne pas
#      resserrer sur la foi de l'hypothèse ci-dessus : elle n'est pas mesurée.
# ⇒ Ce qui est vérifié est une COHÉRENCE DE PLAGE, et c'est écrit tel quel
#   partout désormais : les indices doivent rendre une largeur de lien PCIe
#   LÉGALE et une horloge mémoire PLAUSIBLE. ⛔ Ce n'est PAS la preuve du bon
#   capteur — c'est AC10 qui l'a apportée (47 °C écran contre 47 °C Windows).
# ⚠️ Ne pas resserrer sans un relevé de la carte concernée : le durcissement
#    « évident » casse la source au repos, et ça ne se verrait qu'à l'usage.
_LANES_LEGALES = (1, 2, 4, 8, 16, 32)
_MEMCLK_MIN_MHZ = 100
_MEMCLK_MAX_MHZ = 20000

# ── LES BORNES, MIROIR DE `k_metriques[]` DANS main/dn_link.c ─────────────────
# ⚠️ ELLES SONT RECOPIÉES, ET C'EST UN RISQUE ASSUMÉ ET NOMMÉ : le firmware
#    REJETTE (rejets_bornes) ce qui les dépasse, donc une dérive entre les deux
#    tables se verrait comme un compteur qui monte — pas comme un silence. Le
#    plafond côté agent existe pour ÉCRÊTER PROPREMENT et le DIRE (compteur
#    `ecretages` au bilan), pas pour se substituer au firmware.
# ⛔ Un écrêtage muet serait un mensonge : la valeur affichée ne serait plus la
#    valeur mesurée, et rien ne le signalerait.
# 🔴 dn4-6 : LA TABLE DEVIENT UNE LISTE PAR MÉTRIQUE. Le tuple à deux places
#    portait DEUX grandeurs dans sa FORME même — à quatre, il aurait fallu
#    `(a, b, c, d)` partout et des `BORNES[m][2]` que rien ne garde.
# ⚠️ ELLE EST LE MIROIR DE `k_metriques[]` DANS `dn_link.c`, ET C'EST UN RISQUE
#    ASSUMÉ ET NOMMÉ : les deux tables sont recopiées, pas dérivées l'une de
#    l'autre (le fil n'a pas de canal de négociation). Une dérive ne serait PAS
#    silencieuse — elle se verrait en `rejets_bornes` qui monte côté firmware.
#    ⇒ LES DEUX TABLES BOUGENT DANS LE MÊME GESTE. Si vous éditez celle-ci sans
#      l'autre, la campagne de bruit d'AC7 le dira.
# 🔴 dn4-8 / D13 : `cpu` ET `disk` PASSENT A QUATRE, ET LES DEUX TABLES BOUGENT
#    DANS LE MEME GESTE (voir `k_metriques[]`, `main/dn_link.c`). Recompte
#    caractere par caractere : pire cas ATTEIGNABLE `disk` = 64 o, pire cas au
#    GABARIT `disk` = 67 o ⇒ `DN_LINK_LIGNE_MAX = 71` NE BOUGE PAS.
# ⚠️ L'ORDRE DE `cpu` EST INCHANGE SUR 0..2 — la °C est en index **3**, ⛔ pas 2.
#    Mettre la °C en 2 ferait afficher le `c.max` d'un agent v3 NON MODIFIE comme
#    une temperature, et le plafond passant de 1000 a 1500, `rejets_bornes` ne
#    broncherait meme pas. Le temoin de non-regression fabriquerait le mensonge.
# ⛔ AUCUNE GRANDEUR LHM EN POSITION 0 : une valeur principale absente fait que la
#    metrique n'est PAS emise. Le `Mo/s` de `disk` vient de `psutil` et survit a
#    l'arret de LHM ; les trois `tr/min` sont en positions INTERNES, donc champ vide.
BORNES = {
    "cpu": [1000, 1000, 1000, 1500],      # % · GHz · % (c.max) · °C  (LHM)
    "gpu": [1000, 1500, 10000, 100000],   # % · °C · W · tr/min
    "ram": [1000, 40000],                 # % · Go TOTAUX
    "net": [1000000, 1000000],            # Mb/s ↓ · Mb/s ↑
    "disk": [1000000, 100000, 100000, 100000],  # Mo/s · extr.moy · CPU · boitier (LHM)
}


def checksum(corps: str) -> str:
    """XOR NMEA des octets du corps (entre '$' exclu et '*' exclu), hex majuscule."""
    ck = 0
    for octet in corps.encode("ascii"):
        ck ^= octet
    return f"{ck:02X}"


def trame(seq: int, t_ms: int, metrique: str, valeurs) -> str:
    """Une trame v3 : 5 champs fixes + 1 à 4 valeurs.

    ⛔ `valeurs` EST UNE LISTE, PAS `v2, v3, v4` EMPILÉS. Empiler les paramètres
       aurait mis la borne du protocole dans la SIGNATURE d'une fonction, c'est-
       à-dire à l'endroit le plus coûteux à élargir — et ce fichier vient de le
       payer sur `BORNES`.

    🔴 W10 SURVIT À N GRANDEURS PAR LE **CHAMP VIDE**. Une source qui rend
       `[46, None, 53, 604]` publie les TROIS qu'elle connaît et TAIT la
       deuxième — sur un fil POSITIONNEL, ça ne peut pas être un décalage (la
       puissance s'afficherait dans la case de la température) ni une
       troncature (deux valeurs VRAIES seraient perdues). C'est donc un champ
       VIDE : `$DN,3,…,gpu,460,,530,6040*CK`.
    ✅ ET LE PARSEUR SAIT DÉJÀ LE VOIR : il découpe le corps À LA MAIN et non
       par `strtok`, précisément parce que `strtok` fusionne les séparateurs
       consécutifs et que « ,, » lui serait invisible. La capacité existait
       depuis dn2-2, elle n'était pas exploitée.
    ⚠️ LES `None` DE QUEUE SONT TRONQUÉS, pas rendus vides : « je n'ai que trois
       grandeurs » et « ma quatrième est inconnue » sont le même fait ici, et la
       forme courte économise des octets sur une ligne déjà bornée à 71.
    ⛔ UN `None` EN POSITION 0 EST REFUSÉ : une trame sans sa valeur principale
       ne dit rien. L'appelant ne doit alors PAS émettre la métrique — sa case
       périme d'elle-même en 3 s et dit « -- ».
    ⚠️ `valeurs = [v1]` ⇒ 6 champs, exactement la trame v1/v2 mono-grandeur.
    """
    vs = list(valeurs)
    while vs and vs[-1] is None:
        vs.pop()
    if not vs:
        raise ValueError(
            "trame sans aucune valeur — la métrique ne doit pas être émise")
    if vs[0] is None:
        raise ValueError(
            f"trame `{metrique}` : valeur PRINCIPALE absente — ne pas emettre "
            "cette metrique du tout (sa case perimera en 3 s)")
    corps = f"DN,{PROTO_VERSION},{seq},{t_ms},{metrique}," + ",".join(
        "" if v is None else str(v) for v in vs)
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
# 🔴 dn4-6 / D11 : DEUX INDICES DE PLUS, ET ILS SONT GRATUITS. Ils sortent de la
#    MÊME structure que `_brut()` remplit déjà — ⛔ AUCUN appel supplémentaire à
#    `ADL2_New_QueryPMLogData_Get` (0,976 ms, mesuré n=30). Le budget de dn4-6
#    est LE PIXEL, pas le CPU.
# ✅ `ASIC_POWER` est MESURÉ : 53 W instantané, étendue 52..57, texte changé
#    12/29 (41,4 %) — il qualifie déjà au critère W2, c'est le repli écrit
#    d'avance si `FAN_RPM` échoue.
# ⚠️ `FAN_RPM` ENTRE AVEC UNE DETTE DE MESURE : son MOUVEMENT n'a jamais été
#    échantillonné (six indices suivis le 2026-08-18, pas celui-là). Son critère
#    de qualification est écrit et horodaté AVANT la session (AC6 de dn4-6).
_PM_ASIC_POWER = 23
_PM_FAN_RPM = 14


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

    ⚠️ CETTE CLASSE REFUSE DE SERVIR SI SON MAPPING EST INCOHÉRENT. Les indices
       de capteur ne sont pas lisibles dans la DLL : les prendre pour argent
       comptant, c'est risquer de publier la tension du SOC comme une température.
       Le témoin (`_coherent`) lit deux capteurs par les MÊMES indices et vérifie
       qu'ils rendent une **largeur de lien PCIe légale** et une **horloge mémoire
       plausible**. ⛔ ATTENTION À CE QU'IL EST : une COHÉRENCE DE PLAGE, pas une
       égalité. Trois textes du dépôt ont affirmé le contraire jusqu'au 2026-08-18.
    ⛔ CE PARAGRAPHE AFFIRMAIT « `BUS_LANES` n'est PAS toujours 16, la carte abaisse
       son lien au repos ». C'ÉTAIT UNE HYPOTHÈSE, PAS UNE MESURE, et la séance du
       2026-08-18 NE LA CONFIRME PAS : le témoin a rendu `BUS_LANES = 16` et
       `CLK_MEMCLK = 1988 MHz`. Retiré le 2026-08-19 — le fichier la déclarait non
       mesurée cent cinquante lignes plus haut et la publiait comme un fait ici.
    ⇒ CE QUI RESTE VRAI : le code vérifie une PLAGE, ce qui est le bon choix tant
      que le comportement au repos prolongé n'est pas relevé (entrée au ledger).
    🔴 CE QUI A RÉELLEMENT PROUVÉ LE MAPPING, C'EST AC10 : 47 °C à l'écran contre
       47 °C au Gestionnaire des tâches, lus EN MÊME TEMPS. Le témoin de plage
       garde la session ; la confrontation à Windows a fermé la question.
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
            if not self._coherent(out):
                continue
            return a.iAdapterIndex, a.strAdapterName.decode("latin-1", "replace")
        raise RuntimeError(
            "aucun adaptateur ne repond a PMLog avec un mapping COHERENT "
            "(BUS_LANES / CLK_MEMCLK invraisemblables)")

    def _coherent(self, out):
        """LE TÉMOIN DE MAPPING, ET IL EST ÉLIMINATOIRE — pour de bon.

        🔴 CORRECTIF DE REVUE 2026-08-18 — ET C'EST LE TEXTE QUI AVAIT TORT, PAS
           LE CODE. Quatre textes (cette docstring, `README.md`, `liaison-pc.md`
           §13.5, la story dn4-1) affirmaient que l'agent « exige BUS_LANES = 16
           et CLK_MEMCLK ≈ 2000 MHz » et « REFUSE de servir sinon ». Le code
           vérifie en réalité une **plage**. ⛔ LA JUSTIFICATION PUBLIÉE ICI —
           « il a RAISON : une RX 6000 abaisse son lien PCIe au repos, donc 16
           n'est PAS un invariant ; exiger 16 aurait fait refuser la source GPU
           sur une carte saine » — ÉTAIT UNE HYPOTHÈSE NON MESURÉE, et la séance
           du 2026-08-18 ne l'a PAS confirmée (`BUS_LANES = 16`,
           `CLK_MEMCLK = 1988 MHz` : un durcissement serait passé ce jour-là).
           Retirée le 2026-08-19. ⇒ La plage reste le bon choix, mais pour une
           raison qui se dit autrement : ON N'A PAS MESURÉ le comportement au
           repos prolongé, donc on ne resserre pas. C'est au ledger.
        ⇒ Les quatre textes disent désormais ce qui est réellement vérifié.
        ⚠️ CE QUE CE TÉMOIN PROUVE, ET CE QU'IL NE PROUVE PAS : il rend improbable
           qu'on interroge un adaptateur qui ne répond pas à PMLog, ou dont la
           structure est décalée au point de rendre des valeurs illégales. Il ne
           prouve **PAS** que l'indice 8 soit bien la température : un mapping
           décalé tombant sur un autre capteur d'horloge pourrait le franchir.
        🔴 **C'est AC10 qui a fermé cette question-là, et par la mesure directe :
           47 °C à l'écran contre 47 °C au Gestionnaire des tâches, lus EN MÊME
           TEMPS le 2026-08-18.** ⛔ Ne jamais présenter le témoin de plage comme
           la preuve du capteur — c'est deux instruments, et un seul répond.
        """
        lanes = out.sensors[_PM_BUS_LANES]
        memclk = out.sensors[_PM_CLK_MEMCLK]
        if not (lanes[0] and lanes[1] in _LANES_LEGALES):
            return False
        if not (memclk[0] and _MEMCLK_MIN_MHZ <= memclk[1] <= _MEMCLK_MAX_MHZ):
            return False
        return True

    def temoin(self):
        """Rend `(lanes, memclk)` — un 2-uplet, et il le RESTE : c'est un témoin
        de mapping, pas une lecture de grandeurs. ⛔ Ne pas l'aligner sur `lire()`
        « par symétrie » : les deux ne publient pas la même chose."""
        out = self._brut(self.adaptateur)
        if out is None:
            return None, None
        return out.sensors[_PM_BUS_LANES][1], out.sensors[_PM_CLK_MEMCLK][1]

    def lire(self):
        """Rend `(pct, degc, watts, tr_min)` en unités entières — QUATRE valeurs,
        TOUJOURS, y compris sur les chemins d'échec.

        N'importe laquelle peut valoir `None` seule : c'est le cas W10, et il doit
        rester possible. Un tuple entièrement `None` = la source n'a pas répondu ;
        `_tenter()` le convertit en panne COMPTÉE ET NOMMÉE.

        🔴 CORRECTIF DE REVUE DU 2026-08-19 — L'ARITÉ ÉTAIT MIXTE, ET C'ÉTAIT UNE
           MINE. Les trois chemins d'échec rendaient `(None, None)` — un 2-uplet
           hérité de la v2 — face à un appelant qui déballe QUATRE valeurs
           (`g_pct, g_c, g_w, g_rpm = lu`). Ça ne cassait pas : la garde
           tuple-tout-`None` de `_tenter()` les interceptait avant le déballage.
           ⛔ Mais elle a été posée pour une AUTRE raison (compter la panne), et
           la boucle principale ne rattrape que `KeyboardInterrupt` : le jour où
           un chemin d'échec devient PARTIEL — `return None, 0` — le `ValueError`
           du déballage emporte l'agent ENTIER, donc les CINQ métriques. C'est
           exactement ce que l'isolement des sources existe pour empêcher.
        ⚠️ Et le docstring annonçait encore « Rend (pct, degc) », c'est-à-dire le
           contrat de la v2, dans le fichier qui EST le document d'autorité côté PC.

        ⚠️ LE TÉMOIN EST RE-JOUÉ À CHAQUE TIR (correctif de revue 2026-08-18) : il
           n'était vérifié qu'au constructeur, alors qu'une mise à jour de pilote
           ou une ré-énumération des adaptateurs en cours de session peut décaler
           le mapping. Un témoin qui ne regarde qu'une fois garde une carte, pas
           une session. Le coût est nul : les deux capteurs sont dans la structure
           que `_brut()` vient déjà de remplir, aucun appel supplémentaire.
        """
        out = self._brut(self.adaptateur)
        if out is None:
            return None, None, None, None
        if not self._coherent(out):
            return None, None, None, None
        # 🔴 QUATRE GRANDEURS, UN SEUL APPEL. `out` est déjà rempli : lire deux
        #    capteurs de plus dans la MÊME structure coûte deux déréférencements.
        # ⚠️ Chaque capteur porte SON drapeau de validité (`[0]`) : un capteur
        #    invalide rend `None` POUR LUI SEUL. ⛔ Jamais un tout-ou-rien — les
        #    quatre grandeurs du GPU sont indépendantes au sens de W10, même si
        #    elles viennent du même appel.
        def _v(idx):
            c = out.sensors[idx]
            return c[1] if c[0] else None

        return (_v(_PM_ACTIVITY_GFX), _v(_PM_TEMP_EDGE), _v(_PM_ASIC_POWER),
                _v(_PM_FAN_RPM))

    def fermer(self):
        try:
            self.dll.ADL2_Main_Control_Destroy(self.ctx)
        except Exception:
            pass


# ═════════════════════════════════════════════════════════════════════════════
# LA SOURCE LHM — LES SONDES Ring0 DE LA TOUR, *LUES*, JAMAIS PRISES (D13)
# ═════════════════════════════════════════════════════════════════════════════

LHM_HOTE = "127.0.0.1"
LHM_PORT = 8085          # defaut de LHM, VERIFIE sur la tour (`listenerPort`)
LHM_CHEMIN = "/metrics"
# 🔴 LE TIMEOUT EST POSE ICI, ET SON MOTIF EST CHIFFRE (AC6).
#    · Mural p95 MESURE de `/metrics` en keep-alive, jeu A : **16,5 ms** (AC2,
#      campagne 3, n=1000) ⇒ 0,4 s = **24x** la marge.
#    · La resynchronisation de cadence se declenche quand un cycle a plus d'UNE
#      PERIODE ENTIERE de retard (`prochain < maintenant`, boucle principale).
#      Un plafond a 0,4 s laisse 0,6 s aux cinq autres postes et aux cinq
#      ecritures serie ⇒ ⛔ une lecture LHM bloquee ne peut pas, A ELLE SEULE,
#      declencher le recalage — lequel JETTE l'echantillon et re-amorce LES CINQ
#      METRIQUES. 🎯 C'est le mecanisme le plus dangereux de cette story.
# 🔴 ET CE MOTIF A ETE FAUX PENDANT UNE HEURE, LE 2026-08-21 : le timeout etait
#    applique PAR TENTATIVE, et `_get()` en fait DEUX. Le pire cas reel etait donc
#    **802 ms mesurees pour 400 ms posees** — la moitie de la marge annoncee.
#    ⇒ Corrige : le budget est desormais celui de la lecture ENTIERE (`_get`).
#    ⚠️ Le defaut n'a PAS ete trouve par le controle qui portait sur lui : celui-ci
#       n'avait qu'une borne INFERIEURE (« la lecture a bien ete coupee »), donc il
#       epinglait VERT un depassement du DOUBLE. **Un controle sans borne
#       superieure ne peut pas voir le defaut qu'il pretend exclure.** Il porte
#       maintenant les deux bornes.
# ⚠️ CE N'EST PAS UNE PREUVE, C'EST UN DIMENSIONNEMENT. La duree reelle des
#    lectures est MESUREE en regime et publiee au bilan (n, moyenne, MAX).
LHM_TIMEOUT_S = 0.4

# ── LA TABLE DES SONDES — UNE CONFIGURATION DE *CETTE* TOUR ─────────────────
# 🔴 DECISION OWNER DU 2026-08-21, VERBATIM : « on code comme ca de facon a plus
#    tard ajouter des menus de personnalisation et aussi changer les liens si
#    mauvais ». ⇒ La correspondance `SensorId` → grandeur est une propriete de
#    CETTE machine, ⛔ pas du produit. Elle vit donc COTE AGENT, jamais dans le
#    firmware — c'est exactement le cout que D13 assume deja.
# 🔴 TROIS EXIGENCES, pour que « configurable » ne devienne pas « etiquette qui
#    ment » : (1) une TABLE, ⛔ pas des `if` ; (2) chaque entree porte sa
#    **PROVENANCE** ; (3) ⛔ le nom ne depasse JAMAIS ce qui est etabli.
# ⚠️ L'ORDRE NAIF ETAIT FAUX SUR LES DEUX PREMIERS CANAUX : `fan/0` est `CPU_FAN2`,
#    ⛔ pas `CPU_FAN1`. Le coder naivement aurait affiche « CPU » sur l'extraction
#    haute et « TOP » sur le ventirad. C'est la capture BIOS de l'owner qui l'a
#    attrape, ⛔ pas le raisonnement de l'agent.
# ⛔ `FRONT_IN` (200 mm facade, `fan/3` ou `fan/5`) N'EST PAS DANS CETTE TABLE ET
#    N'Y SERA JAMAIS : il n'a pas de fil tachymetrique et rend `0 RPM` **DANS LE
#    BIOS AUSSI**. Aucun logiciel ne pourra publier sa vitesse. ⚠️ Il tourne — il
#    ne le dit pas. ⇒ A ECRIRE POUR dn4-9, qui doit « nommer chaque ventilateur ».
# ⚠️ `CASE_GROUP` = UN tachymetre pour DEUX ventilateurs CHAINES. Si celui du bas
#    s'arrete, RIEN NE LE DIRA. ⛔ Ne pas le rebaptiser « TOP » ni « BOTTOM ».
LHM_SONDES = (
    # (cle interne, identifiant LHM complet, PROVENANCE)
    ("cpu.degc", "/intelcpu/0/temperature/10",
     "MESURE (LHM 0.9.6, 2026-08-21) — « CPU Package », 41,0 degC ; recoupee par un "
     "chemin INDEPENDANT, le Super I/O /lpc/nct6792d/0/temperature/0 a 40,5 degC "
     "(1,2 %). ⚠️ instantane n=1 : conforte le mapping, ⛔ ne qualifie pas le mouvement"),
    ("fan.top_out", "/lpc/nct6792d/0/fan/0",
     "MESURE (jointure BIOS<->LHM par RPM, 2026-08-21) — en-tete CPU_FAN2, "
     "extraction HAUTE. ⚠️ l'ordre naif en faisait CPU_FAN1 : REFUTE"),
    ("fan.cpu_noctua", "/lpc/nct6792d/0/fan/1",
     "MESURE (jointure BIOS<->LHM par RPM, 2026-08-21) — en-tete CPU_FAN1, "
     "ventirad Noctua bi-ventilateur (repos 305, plafond 1112)"),
    ("fan.case_group", "/lpc/nct6792d/0/fan/2",
     "MESURE (jointure BIOS<->LHM par RPM, 2026-08-21) — en-tete SYS_FAN1, DEUX "
     "ventilateurs chaines sur UN tachy"),
    ("fan.rear_out", "/lpc/nct6792d/0/fan/4",
     "MESURE (jointure BIOS<->LHM par RPM, 2026-08-21) — en-tete SYS_FAN3, "
     "140 mm arriere, extraction"),
)

# Une ligne `/metrics` : `lhm_<famille> {..."sensorId"="/fan/0"...,
# "hardwareId"="/lpc/nct6792d/0"...} 667.408447265625`
# 🎯 L'IDENTIFIANT COMPLET EST `hardwareId + sensorId` — ⛔ pas `sensorId` seul,
#    qui vaut `/fan/0` sur DEUX puces differentes (la carte-mere ET le GPU).
# ✅ ET C'EST `/metrics` QUI EST RETENU, PAS `/data.json` : l'unite y vit dans la
#    CLE (`lhm_motherboard_fan_rpm`), donc un changement d'unite CHANGE LE NOM et
#    SE VOIT. Dans `/data.json` elle vit dans la chaine (« 43,0 °C ») : un parseur
#    qui retire le suffixe accepterait « 110,0 °F » sans broncher. ⚠️ Ce depot a
#    deja paye cette classe de defaut — le « 34,3 Go » contre « 31,9 » de dn4-1.
_LHM_LIGNE = re.compile(
    r'^lhm_\S+\s+\{.*?"sensorId"="([^"]*)".*?"hardwareId"="([^"]*)".*?\}\s+(\S+)\s*$')


def _fini(x):
    """`True` si `x` est un flottant FINI.

    ⛔ `float("NaN")` de la stdlib **REUSSIT** et rend `nan` : un `try/except
       ValueError` autour de `float()` NE VOIT PAS le NaN. Il se propagerait
       jusqu'a un `int()` (qui leve) ou jusqu'au format — le « chiffre faux mais
       plausible » que ce depot traque.
    ⚠️ `x != x` attrape NaN ; `x - x != 0` attrape en plus ±inf.
    ⚠️ Le serialiseur de LHM autorise les litteraux flottants nommes, et
       `/metrics` remplace normalement une NaN par une ligne `# HELP … skipped`.
       Ce test est la garde du cas ou il ne le ferait pas — ⛔ pas une hypothese.
    """
    return x == x and x - x == 0


class SourceLhm:
    """La °C CPU et les tr/min des ventilateurs, LUS chez LibreHardwareMonitor.

    🔴 L'AGENT NE FAIT AUCUN Ring0 LUI-MEME, ET C'EST CE QUI REND LA CHOSE
       ACCEPTABLE (D13). LHM tourne en service permanent sur la tour (tache
       planifiee `RunLevel = Highest`, **prouvee par un redemarrage reel** le
       2026-08-21) avec son driver noyau signe `PawnIO 2.2.0` ; cette classe se
       contente de LIRE son serveur web local. ⛔ Aucun driver, aucune elevation,
       aucun .NET du cote de l'agent.
    ⚠️ LE COUT EST ASSUME, ⛔ PAS OUBLIE : ces grandeurs ne marchent que sur une
       machine ou LHM est installe et configure ainsi. Le critere owner de D8
       (« generique et libre de droits ») NE TIENT PLUS pour elles.

    🔴 ELLE SUIT LE PATRON DE `SourceGpuAdl` SAUF SUR **UN** POINT, ET C'EST
       DELIBERE. `SourceGpuAdl.__init__` qui echoue ⇒ `self.gpu = None`, source
       desactivee POUR TOUTE LA SESSION — correct pour une **DLL** : si
       `atiadlxx.dll` manque au demarrage, elle manquera aussi a la fin.
       ⛔ FAUX POUR UN **SERVICE** : LHM peut demarrer apres l'agent, ou etre
       arrete puis relance. Le scenario 3 d'AC8 exige explicitement la reprise
       **sans redemarrer l'agent**. ⇒ Cette source ne se desactive JAMAIS : un
       echec est un ETAT, ⛔ pas une condamnation, et chaque cycle retente.
    🎯 LE CHEMIN DE RECONNEXION **EST** LE DETECTEUR « LHM ABSENT » D'AC8,
       ⛔ pas un detail d'implementation.

    ⛔ PAS DE JETON « INCONNU » — LA REGLE EXISTE ET ELLE EST TRANCHEE (W10) :
       une grandeur absente en position INTERNE est un **champ VIDE** ; en
       position 0, la metrique n'est PAS EMISE. Cette source rend donc
       `float | None` par sonde, et **`None` EST UNE DONNEE**, ⛔ pas une panne.
    ⚠️ Ce point a coute un defaut d'instrument en AC2 : le harnais comptait
       « capteur sans valeur » en ECHEC, ce qui CONTREDISAIT son propre critere.
    """

    def __init__(self, hote=LHM_HOTE, port=LHM_PORT, timeout_s=LHM_TIMEOUT_S,
                 verbeux=True):
        self.hote = hote
        self.port = port
        self.timeout_s = timeout_s
        self._c = None
        self.motif = None          # le DERNIER symptome, republie au bilan
        self.reponses = 0          # lectures REUSSIES
        self.echecs = 0            # lectures qui ont LEVE
        self._echecs_suite = 0
        # 🔴 CHAQUE CAS SUR **SON** COMPTEUR, et une ABSENCE n'est pas une PANNE.
        #    Les mettre dans le meme seau est exactement le defaut « tronquee /
        #    trop longue » que le firmware a du dedoubler : deux diagnostics
        #    CONTRAIRES (« LHM ne repond pas » / « LHM repond et dit qu'il n'a pas
        #    cette valeur ») envoient chercher a deux endroits differents.
        self.absences = {}
        self.duree_n = 0
        self.duree_somme = 0.0
        self.duree_max = 0.0
        # ⚠️ LA SONDE D'ANNONCE EST UNE VRAIE LECTURE, ET ELLE EST COMPTEE COMME
        #    TELLE. ⛔ Pas un tir fantome hors compteurs : un instrument qui
        #    s'exclut de ses propres chiffres ment sur la premiere seconde.
        try:
            vues = self.lire()
            if verbeux:
                connues = sum(1 for v in vues.values() if v is not None)
                print("[agent] LHM : %s:%d%s — %d/%d sonde(s) avec valeur "
                      "(timeout %.2f s, connexion PERSISTANTE)"
                      % (self.hote, self.port, LHM_CHEMIN, connues, len(vues),
                         self.timeout_s), file=sys.stderr)
        except Exception as exc:
            self.motif = "%s: %s" % (type(exc).__name__, exc)
            if verbeux:
                # ⛔ ON NE FERME PAS LA SOURCE. Voir la docstring : LHM est un
                #    SERVICE, il peut monter apres nous. AC8 scenario 1.
                print("[agent] ⚠️ LHM INJOIGNABLE au demarrage (%s) — la °C CPU et "
                      "les tr/min diront « -- », les autres grandeurs continuent. "
                      "⚠️ La source RESTE ARMEE : elle retente a chaque cycle et "
                      "reprendra seule si LHM demarre." % self.motif,
                      file=sys.stderr)

    def _fermer_connexion(self):
        if self._c is not None:
            try:
                self._c.close()
            except Exception:
                pass
        self._c = None

    def _chrono(self, dt):
        self.duree_n += 1
        self.duree_somme += dt
        if dt > self.duree_max:
            self.duree_max = dt

    def _get(self):
        """UNE requete `GET /metrics` sur une connexion PERSISTANTE.

        Se reconnecte **UNE** fois si elle est tombee, puis leve.
        🎯 C'est CE chemin qui detecte « LHM absent » (AC8), et c'est aussi lui
           qui fait la reprise du scenario 3 — les deux sont le meme code.
        ⚠️ `rep.read()` est TOUJOURS appele avant de rendre la main : une reponse
           non drainee casse la connexion persistante au tir suivant.
        """
        # 🔴 LE TIMEOUT EST UN BUDGET POUR LA LECTURE **ENTIÈRE**, ⛔ PAS PAR
        #    TENTATIVE — ET C'EST UN CORRECTIF, PAS UNE ÉLÉGANCE. Mesuré le
        #    2026-08-21 par `tools/verif_source_lhm_dn48.py` scénario « lent » :
        #    avec un timeout PAR TENTATIVE, une lecture a duré **802 ms pour un
        #    plafond posé à 400 ms** — la reconnexion doublait le pire cas.
        #    ⇒ Le motif écrit sur `LHM_TIMEOUT_S` (« 0,4 s laisse 0,6 s aux cinq
        #      autres postes ») était donc **FAUX** : il en laissait 0,2.
        # ✅ ET LA SECONDE TENTATIVE GARDE SON UTILITÉ. Elle existe pour la
        #    connexion PÉRIMÉE (le serveur a fermé de son côté), qui échoue
        #    IMMÉDIATEMENT — il reste alors presque tout le budget. Un serveur
        #    trop LENT, lui, ne le sera pas moins au second essai : ⛔ ne pas le
        #    retenter est le comportement correct, pas une perte.
        fin = time.perf_counter() + self.timeout_s
        for dernier in (False, True):
            reste = fin - time.perf_counter()
            if reste <= 0.0:
                raise TimeoutError(
                    "budget de lecture LHM epuise (%.0f ms)"
                    % (self.timeout_s * 1000.0))
            try:
                if self._c is None:
                    self._c = http.client.HTTPConnection(
                        self.hote, self.port, timeout=reste)
                self._c.request("GET", LHM_CHEMIN,
                                headers={"Connection": "keep-alive"})
                rep = self._c.getresponse()
                corps = rep.read()
                if rep.status != 200:
                    raise IOError("HTTP %d sur %s" % (rep.status, LHM_CHEMIN))
                if rep.will_close:
                    self._fermer_connexion()
                return corps.decode("utf-8", "replace")
            except Exception:
                self._fermer_connexion()
                if dernier:
                    raise

    def lire(self):
        """Rend `{cle: float | None}` — UNE entree par sonde, TOUJOURS.

        ⛔ LEVE si LHM ne repond pas : c'est `_tenter()` qui en fera une panne
           COMPTEE ET NOMMEE, une seule fois par type.
        ⚠️ Rendre `None` pour une sonde n'est PAS lever : LHM a repondu et a dit
           qu'il n'avait pas cette valeur. Les deux se comptent SEPAREMENT.
        """
        t0 = time.perf_counter()
        try:
            txt = self._get()
        except Exception as exc:
            self.echecs += 1
            self._echecs_suite += 1
            self.motif = "%s: %s" % (type(exc).__name__, exc)
            raise
        finally:
            self._chrono(time.perf_counter() - t0)

        table = {}
        for ligne in txt.splitlines():
            if not ligne.startswith("lhm_"):
                continue
            m = _LHM_LIGNE.match(ligne)
            if not m:
                continue
            try:
                v = float(m.group(3))
            except ValueError:
                continue
            if not _fini(v):
                continue
            table[m.group(2) + m.group(1)] = v

        vues = {}
        for cle, ident, _prov in LHM_SONDES:
            v = table.get(ident)
            # 🔴 UNE VALEUR NEGATIVE DEVIENT « JE NE SAIS PAS », ⛔ PAS UN ZERO
            #    ECRETE, ET LE MOTIF EST MESURE. `_dx()` ecrete a 0 et le COMPTE —
            #    correct pour un % ou un Mo/s. Pour un tachymetre, « 0 tr/min » est
            #    une **VRAIE valeur** (fan-stop), donc un -1 ecrete a 0 fabriquerait
            #    « ventilateur a l'arret » : indistinguable de la verite a l'ecran.
            #    ⚠️ Ce depot a DEJA failli conclure « FAN_RPM ne qualifie pas » sur
            #       un instrument casse qui rendait 0. ⇒ W10 sait dire « je ne sais
            #       pas » ; c'est la seule sortie honnete.
            # ⚠️ ASYMETRIE ASSUMEE ET NOMMEE : la regle ne vaut QUE pour les
            #    grandeurs LHM. Les autres gardent l'ecretage historique de `_dx()`.
            #    La question generale est AU LEDGER, ⛔ pas tranchee ici.
            if v is not None and v < 0:
                self.absences[cle + ":negatif"] = \
                    self.absences.get(cle + ":negatif", 0) + 1
                v = None
            elif v is None:
                self.absences[cle] = self.absences.get(cle, 0) + 1
            vues[cle] = v

        self.reponses += 1
        if self._echecs_suite:
            print("[agent] ✅ source `lhm` a REPRIS apres %d echec(s) consecutif(s) "
                  "— la connexion persistante s'est retablie SANS redemarrer "
                  "l'agent." % self._echecs_suite, file=sys.stderr)
            self._echecs_suite = 0
        return vues

    def extraction_moyenne(self, vues):
        """La moyenne des DEUX canaux d'extraction — et elle **exige les deux**.

        🔴 UNE MOYENNE CALCULEE SUR UN SEUL CANAL EST UN AUTRE NOMBRE SOUS LA
           MEME ETIQUETTE. C'est la famille exacte du « 34,3 Go » contre « 31,9 » :
           « le pire genre de mensonge, celui qui a l'air d'un arrondi ».
           ⇒ Un canal manquant ⇒ `None` ⇒ champ VIDE. ⛔ Jamais l'autre canal seul.
        ⚠️ LE COUT EST REEL ET NOMME : la grandeur derivee est PLUS FRAGILE que
           ses composantes. Le cas se compte sur SON propre compteur, parce que
           le fil, lui, ne peut pas distinguer « les deux absents » de « un seul ».
        ⚠️ « MOYENNE ENTRANT/SORTANT » ETAIT LA DEMANDE OWNER, ET LA MESURE L'A
           AMENDEE : **il n'existe AUCUN flux entrant mesurable** — le 200 mm de
           facade n'a pas de tachy (0 RPM dans le BIOS aussi) et le ventilateur du
           bas est CHAINE avec un extracteur sur un seul tachy. Une « moyenne
           entrante » serait calculee sur RIEN. ⇒ Seule la SORTANTE existe.
        """
        a = vues.get("fan.top_out")
        b = vues.get("fan.rear_out")
        if a is None and b is None:
            return None
        if a is None or b is None:
            self.absences["extraction_moy:un_seul_canal"] = \
                self.absences.get("extraction_moy:un_seul_canal", 0) + 1
            return None
        return (a + b) / 2.0

    def reamorcer(self):
        """Apres un recalage de cadence : la connexion est JETEE, pas reutilisee.

        ⚠️ `reamorcer()` n'est appelee qu'apres une SORTIE DE VEILLE, une
           reconnexion ou un blocage d'envoi — precisement les instants ou une
           socket TCP ouverte depuis des minutes est morte sans le dire. La
           refermer ici fait payer la reconnexion AU TOUR SUIVANT, ⛔ pas un
           timeout de 0,4 s au milieu du premier cycle d'apres-veille.
        """
        self._fermer_connexion()

    def fermer(self):
        self._fermer_connexion()


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


def _borner(dixiemes, plafond, compteur, nom):
    """Borne une valeur DÉJÀ exprimée en dixièmes, et COMPTE l'écrêtage.

    🔴 CORRECTIF DE REVUE 2026-08-18. La fréquence CPU était la SEULE des NEUF
       grandeurs à être écrêtée par un `min()` nu, HORS de `_dx()` — donc sans
       incrémenter `ecretages`, pendant que le bilan imprimait « aucun ecretage :
       toute valeur emise est la valeur mesuree ». ⛔ C'est exactement l'écrêtage
       muet que l'en-tête de ce fichier interdit dix lignes plus haut.
    ⚠️ Et une valeur NÉGATIVE n'était pas bornée du tout : elle partait sur le
       fil et le firmware rejetait la trame CPU ENTIÈRE en `rejets_format`.
       Déclencheur documenté dans ce fichier même : cette tour rend déjà
       `dropin = 113 558 935 299 979` — les compteurs Windows savent mentir.
    """
    if dixiemes < 0:
        compteur[nom] = compteur.get(nom, 0) + 1
        return 0
    if dixiemes > plafond:
        compteur[nom] = compteur.get(nom, 0) + 1
        return plafond
    return dixiemes


class Collecteur:
    """Prend la photo des cinq métriques et rend une liste de trames à émettre.

    ⚠️ LES DÉBITS SONT DES DELTAS DE COMPTEURS CUMULÉS. `psutil` rend des totaux
       depuis le boot : publier le total tel quel afficherait un nombre qui ne
       redescend jamais. Le Δt est mesuré, pas supposé égal à la période — un
       recalage de cadence ou un hoquet d'ordonnanceur fausserait le débit.
    """

    def __init__(self, verbeux=True, lhm_hote=LHM_HOTE, lhm_port=LHM_PORT,
                 lhm_timeout_s=LHM_TIMEOUT_S):
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
            # 🔴 CORRECTIF DE REVUE 2026-08-18 : `self.gpu` avait DÉJÀ été assigné
            #    quand `temoin()` levait ⇒ on annonçait « INDISPONIBLE », puis
            #    `photo()` appelait quand même `self.gpu.lire()` et l'écran
            #    affichait des valeurs GPU, pendant que le bilan (`if gpu is None`)
            #    ne réconciliait RIEN. Le démarrage disait une chose, l'écran une
            #    autre. ⇒ la source est REFERMÉE et remise à None, dans cet ordre.
            if self.gpu is not None:
                try:
                    self.gpu.fermer()
                except Exception:
                    pass
                self.gpu = None
            self.gpu_motif = f"{type(exc).__name__}: {exc}"
            if verbeux:
                # ⚠️ UN MODULE OPTIONNEL NE DOIT PAS BRIQUER L'AGENT — même patron
                #    que `dn_link_init`/`dn_capteurs_init` côté firmware, qui sont
                #    NON FATALES. Sans GPU, les quatre autres métriques vivent.
                print(f"[agent] ⚠️ source GPU INDISPONIBLE ({self.gpu_motif}) — "
                      f"la case GPU restera « -- ». Les quatre autres metriques "
                      f"continuent : une source morte meurt SEULE.", file=sys.stderr)

        # Pannes de source, comptées ET nommées. ⛔ Isoler une source sans
        # compter ses échecs remplacerait une mort bruyante par un silence.
        self.pannes = {}
        # 🔴 dn4-8 / D13 : LA SOURCE LHM N'EST **JAMAIS** MISE À `None`, ⛔ et c'est
        #    une divergence DÉLIBÉRÉE d'avec `SourceGpuAdl` ci-dessus. ADL est une
        #    DLL : absente au démarrage, absente à la fin — la désactiver est
        #    correct. LHM est un SERVICE : il peut monter APRÈS l'agent, ou être
        #    arrêté puis relancé, et AC8 scénario 3 exige la reprise **sans
        #    redémarrer l'agent**. ⇒ le constructeur est non fatal ET non
        #    condamnatoire ; l'échec est un ÉTAT que chaque cycle retente.
        # ⚠️ Le bilan ne peut donc pas tester `self.lhm is None` : il teste
        #    `self.lhm.reponses == 0`, qui est le fait réel (« LHM n'a JAMAIS
        #    répondu de toute la session »).
        self.lhm = SourceLhm(hote=lhm_hote, port=lhm_port,
                             timeout_s=lhm_timeout_s, verbeux=verbeux)
        psutil.cpu_percent(interval=None)  # amorçage : le 1er appel vaut 0.0
        # 🔴 ET `percpu=True` A SON PROPRE ÉTAT INTERNE — CORRECTIF DE REVUE DU
        #    2026-08-19. `psutil` garde DEUX derniers relevés séparés
        #    (`_last_cpu_times` et `_last_per_cpu_times`) : amorcer la forme
        #    globale n'amorce PAS la forme par cœur. Sans cette ligne, le premier
        #    cycle publiait `c.max 0,0 %` (la liste vaut `[0.0] x N`, donc elle
        #    est NON VIDE et `max()` rend 0.0) pendant que le % moyen, lui, était
        #    juste. ⛔ Une 3ᵉ ligne CPU clouée à zéro au démarrage est exactement
        #    le symptôme que ce fichier décrit — il l'attribuait à une autre cause.
        psutil.cpu_percent(interval=None, percpu=True)
        self._d0 = psutil.disk_io_counters()
        self._n0 = psutil.net_io_counters()
        self._t0 = time.monotonic()
        # 🔴 UN HORODATAGE PAR COMPTEUR CUMULÉ (correctif de revue 2026-08-18).
        #    Avec une fenêtre unique, une source qui échoue puis revient voyait
        #    son delta divisé par un Δt qui, lui, avait continué d'avancer : un
        #    débit GONFLÉ, frais et faux. Les compteurs sont cumulatifs, donc le
        #    Δt doit être celui de LEUR dernière lecture réussie.
        # ⚠️ En régime nominal les trois valent la même chose : la propriété
        #    « la fenêtre des débits et celle du % CPU sont la MÊME » tient.
        self._nt0 = self._t0
        self._dt0 = self._t0

    def reamorcer(self):
        """Après un recalage de cadence : la fenêtre repart PROPRE, comme au
        départ. Sans ça, le premier débit d'après-veille serait calculé sur un
        Δt énorme et rendrait un chiffre FRAIS ET FAUX — le défaut exact que la
        resynchronisation de dn2-2 a corrigé pour le % CPU.

        🔴 CHAQUE APPEL EST ISOLÉ (correctif de revue 2026-08-19). `photo()` isolait
           ses cinq sources ; CETTE fonction, non — et c'est le SEUL chemin où
           l'omission tuait l'agent ENTIER : la boucle ne rattrape que
           `KeyboardInterrupt`, donc une exception ici produisait un traceback, un
           code de retour non nul, et LES CINQ CASES À « -- » ENSEMBLE. C'est
           exactement ce que `photo()` déclare avoir corrigé, et le différenciateur
           D6 qui tombe pour une raison qui n'est pas « le PC éteint ».
        ⚠️ LA COÏNCIDENCE EST STRUCTURELLE : `reamorcer()` n'est appelée qu'après un
           recalage de cadence — donc après une SORTIE DE VEILLE, une reconnexion ou
           un blocage d'envoi, précisément les instants où l'état matériel vient de
           changer et où `disk_io_counters()` / `net_io_counters()` peuvent lever.
        ⚠️ Un ré-amorçage qui échoue laisse son compteur à `None` : le tour suivant
           tombe dans la branche « premier tour après une panne » et ne publie rien,
           ce qui est le comportement voulu — pas de débit calculé sur un Δt faux."""
        def _sur(nom, lecture):
            try:
                return lecture()
            except Exception as exc:
                self._panne(nom, type(exc).__name__, f"reamorcage : {exc}")
                return None
        _sur("cpu", lambda: psutil.cpu_percent(interval=None))
        # ⚠️ MÊME MOTIF QU'AU CONSTRUCTEUR, ET C'EST ICI QUE ÇA COMPTE LE PLUS :
        #    sans ce ré-amorçage, les trois autres compteurs repartaient propres
        #    et `_last_per_cpu_times` restait celui d'AVANT la veille — le `c.max`
        #    du tour suivant était donc calculé sur une fenêtre de plusieurs
        #    minutes. « Frais et faux », c'est-à-dire précisément ce que
        #    `reamorcer()` existe pour empêcher (revue 2026-08-19).
        _sur("cpu.percpu", lambda: psutil.cpu_percent(interval=None, percpu=True))
        self._d0 = _sur("disk", psutil.disk_io_counters)
        self._n0 = _sur("net", psutil.net_io_counters)
        # 🔴 dn4-8 : LA CONNEXION LHM EST JETÉE ICI, **PAR `_sur()`** comme les
        #    autres. Motif structurel, le même que celui écrit juste au-dessus :
        #    `reamorcer()` n'est appelée qu'après une SORTIE DE VEILLE, une
        #    reconnexion ou un blocage d'envoi — précisément les instants où une
        #    socket TCP ouverte depuis des minutes est morte SANS LE DIRE. La
        #    refermer ici fait payer la reconnexion au tour suivant, ⛔ pas un
        #    timeout de 0,4 s au milieu du premier cycle d'après-veille.
        # ⚠️ `_sur()` et pas un appel nu : ce chemin est le SEUL où une exception
        #    tuerait l'agent ENTIER (la boucle ne rattrape que `KeyboardInterrupt`).
        _sur("lhm", self.lhm.reamorcer)
        self._t0 = time.monotonic()
        self._nt0 = self._t0
        self._dt0 = self._t0

    def _tenter(self, nom, lecture):
        """Lit UNE source. Si elle lève, la panne est COMPTÉE et NOMMÉE, et
        `None` est rendu ⇒ la métrique n'est pas émise, sa case périme d'elle-même
        en 3 s et dit « -- ».

        ⛔ JAMAIS une valeur inventée, JAMAIS la dernière connue — c'est AC7 de
           dn2-2, et il ne se re-négocie pas.
        ⚠️ Le message n'est imprimé qu'au PREMIER échec de chaque type : une
           source morte à 1 Hz produirait sinon 3 600 lignes de stderr par heure,
           ce qui noierait précisément ce qu'on veut voir.
        """
        try:
            valeur = lecture()
        except Exception as exc:
            return self._panne(nom, type(exc).__name__, str(exc))
        # 🔴 UN TUPLE DE `None` N'EST PAS `None` (revue 2026-08-19). `SourceGpuAdl.lire()`
        #    rend `(None, None)` quand `_brut()` échoue OU quand le témoin de mapping
        #    rejoué par tir refuse : le test `valeur is None` ne le voyait PAS. La case
        #    GPU passait à « -- », `pannes` restait vide, et `_bilan` imprimait
        #    « aucune panne de source : les cinq ont repondu a chaque cycle ». Comme
        #    `self.gpu is not None`, la ligne « source GPU INDISPONIBLE » était sautée
        #    aussi : SILENCE SUR LES DEUX INSTRUMENTS. ⛔ C'est la classe de défaut que
        #    le correctif du 2026-08-18 déclarait fermer, déplacée d'un cran de plus —
        #    et son propre commentaire, dix lignes plus bas, la décrit mot pour mot.
        if isinstance(valeur, tuple) and valeur and all(v is None for v in valeur):
            return self._panne(nom, "None", "la source rend un tuple entierement vide "
                                            "(pas d'exception)")
        if valeur is None:
            # 🔴 UNE SOURCE PEUT MOURIR SANS LEVER (trouvé par le harnais de revue,
            #    2026-08-18, en testant le correctif lui-même) : `disk_io_counters()`
            #    rend `None` — c'est DOCUMENTÉ, pas exceptionnel. Sans ce test,
            #    isoler les sources aurait remplacé une mort BRUYANTE (l'agent
            #    entier tombait) par une DISPARITION SILENCIEUSE : la case passe à
            #    « -- », le bilan imprime « aucune panne de source », et personne
            #    ne sait pourquoi. ⛔ C'est la classe de défaut que ce correctif
            #    était censé fermer, déplacée d'un cran.
            return self._panne(nom, "None", "la source rend None (pas d'exception)")
        return valeur

    def _panne(self, nom, genre, message):
        cle = f"{nom}:{genre}"
        self.pannes[cle] = self.pannes.get(cle, 0) + 1
        if self.pannes[cle] == 1:
            print(f"[agent] ⚠️ source `{nom}` en ECHEC ({message}) — cette metrique "
                  f"n'est plus emise, sa case dira « -- ». Les autres "
                  f"continuent : une source morte meurt SEULE.", file=sys.stderr)
        return None

    def photo(self):
        """Rend [(metrique, [v1, v2, …]), ...] — un `None` = « je ne sais pas ».

        🔴 CHAQUE SOURCE EST ISOLÉE (correctif de revue 2026-08-18). Avant, UNE
           seule exception ici remontait jusqu'à la boucle principale, qui ne
           rattrape que `KeyboardInterrupt` : **L'AGENT ENTIER MOURAIT, et les
           CINQ cases passaient à « -- » ensemble.** Les trois chemins mesurés :
             · `psutil.disk_io_counters()` rend `None` (documenté quand aucun
               disque n'est exposé) -> `self._d0.read_bytes` -> AttributeError ;
             · `psutil.cpu_freq()` peut LEVER (NotImplementedError) — le
               `if fr and fr.current` ne protégeait que le retour `None` ;
             · `self.gpu.lire()` -> ctypes sur `atiadlxx.dll` : un **TDR du
               pilote AMD** (redémarrage du pilote graphique, banal sur une tour
               de jeu) ou une mise à jour de pilote en cours de session.
        ⛔ C'était le contraire exact de ce que ce fichier promet DEUX FOIS
           (« UN MODULE OPTIONNEL NE DOIT PAS BRIQUER L'AGENT », « une source
           morte meurt SEULE ») : la garde n'existait qu'au `__init__`, JAMAIS à
           la lecture. Et c'est le différenciateur de D6 qui tombait avec :
           « PC éteint, une seule case sur six est vivante » ne se voit plus si
           les cinq meurent d'un coup pour une raison qui n'est pas le PC éteint.
        """
        # 🔴 LA LECTURE LHM EST LA PREMIÈRE, ET ELLE EST **AVANT** `t = monotonic()`.
        #    ⛔ CE N'EST PAS COSMÉTIQUE — C'EST CE QUI EMPÊCHE UN DÉBIT FAUX.
        #    `net` et `disk` sont des DELTAS de compteurs cumulés divisés par
        #    `t_now - t_prev`. Si la lecture LHM se plaçait ENTRE `t` et les
        #    lectures `psutil`, sa latence entrerait dans la fenêtre **à une seule
        #    extrémité** : un tir à 400 ms (le timeout) sur un cycle nominal à
        #    16 ms rendrait un Δt sous-estimé de 0,38 s, donc **un débit disque
        #    surestimé de ~38 %** — un chiffre FRAIS ET FAUX, la famille exacte que
        #    la resynchronisation de dn2-2 existe pour empêcher.
        # ✅ PLACÉE AVANT `t`, sa latence est hors fenêtre DES DEUX CÔTÉS (elle
        #    décale `t` et les compteurs du même montant) et s'annule.
        # ⚠️ `_tenter` : un LHM injoignable est une panne COMPTÉE ET NOMMÉE, une
        #    seule fois par type. ⛔ Et elle n'emporte AUCUNE autre grandeur : les
        #    valeurs LHM sont toutes en positions INTERNES.
        lhm = self._tenter("lhm", self.lhm.lire)

        t = time.monotonic()
        e = self.ecretages
        out = []

        # ── cpu : % + fréquence ──────────────────────────────────────────────
        # 🔴 LES DEUX GRANDEURS SONT LUES SÉPARÉMENT (correctif de revue 2026-08-19).
        #    Elles étaient dans la MÊME lambda, donc dans le même tout-ou-rien : un
        #    `psutil.cpu_freq()` qui LÈVE — `NotImplementedError`, nommée trois lignes
        #    plus bas comme un chemin MESURÉ — emportait le **%** CPU avec lui, et la
        #    métrique `cpu` n'était pas émise du tout. Or `cpu` est la seule métrique
        #    de v1, celle du témoin de non-régression d'AC2 : la case restait à « -- »
        #    PC ALLUMÉ, ce qui INVERSE le différenciateur D6.
        # ⇒ W10 existe exactement pour ça : `v2 = None` = « je ne sais pas », et la
        #   grandeur principale continue. C'est déjà ce qu'on fait pour la °C du GPU.
        pct = self._tenter("cpu", lambda: psutil.cpu_percent(interval=None))
        if pct is not None:
            # ⚠️ PAS `_tenter` ICI : `cpu_freq()` rendant `None` est un retour
            #    LÉGITIME sur certaines plateformes (« je ne sais pas »), pas une
            #    panne — le compter en ferait 3 600 par heure et noierait les vraies.
            #    Seule l'EXCEPTION est une panne, et elle est comptée sous sa propre
            #    clé pour ne pas contaminer le compteur de la métrique `cpu`.
            try:
                fr = psutil.cpu_freq()
            except Exception as exc:
                fr = self._panne("cpu.freq", type(exc).__name__, str(exc))
            # MHz -> dixièmes de GHz, en ENTIER : 3201 MHz -> 32 -> « 3,2 GHz ».
            # ⛔ Pas de flottant sur le fil (doctrine `parse_entier` du firmware).
            ghz_dx = round(fr.current / 100.0) if fr and fr.current else None
            # ⚠️ `fr is None` couvre les DEUX cas : `cpu_freq()` a levé (compté par
            #    `_tenter` sous la clé `cpu.freq`), ou elle rend une fréquence nulle.
            #    Dans les deux cas la case affiche le % et « -- » pour la fréquence.
            # ⚠️ `_borner`, PAS un `min()` nu : l'écrêtage doit être COMPTÉ.
            # 🔴 dn4-6 / D11 : LE CŒUR LE PLUS CHARGÉ.
            #    `cpu_percent(percpu=True)` lit LE MÊME COMPTEUR SYSTÈME que
            #    `cpu_percent()` — MESURÉ à 0,07..0,10 ms (n=29), contre 8,4 ms
            #    pour `len(pids())`, écarté DEUX FOIS : case morte (1/28 de
            #    changements) ET hors budget (0,84 % d'un cœur).
            # ⚠️ C'EST BIEN UN SECOND APPEL psutil, ⛔ pas « le même appel » : ce
            #    qui est partagé est le COMPTEUR NOYAU, pas l'appel. Et les deux
            #    formes gardent des états internes SÉPARÉS (`_last_cpu_times` vs
            #    `_last_per_cpu_times`) — sans quoi le second appel mesurerait un
            #    intervalle nul et rendrait 0,0 % sur tous les cœurs, en boucle.
            #    ⇒ HYPOTHÈSE FALSIFIABLE, et elle se falsifie À L'ŒIL sur la
            #      dalle : une 3ᵉ ligne CPU clouée à « 0,0 % » pendant que la
            #      moyenne bouge est exactement ce symptôme.
            # ⚠️ ET SON MOUVEMENT EST MESURÉ, PAS ESPÉRÉ : étendue 25,0..73,9 %,
            #    texte changé 28/28 (100 %), σ = 13,2. C'est ce qui RÉFUTE la
            #    conclusion écrite du ledger (« le CPU n'aurait rien à mettre en
            #    troisième »).
            # ⚠️ `_tenter`, pas un appel nu : `percpu=True` peut lever là où
            #    l'agrégat passe. Une demi-panne reste une DEMI-panne — le % et
            #    la fréquence continuent, seule la 3ᵉ ligne dit « -- » (W10).
            percpu = self._tenter("cpu.percpu",
                                  lambda: psutil.cpu_percent(interval=None,
                                                             percpu=True))
            cmax = max(percpu) if percpu else None
            # 🔴 dn4-8 / D13 : LA °C CPU, EN INDEX **3**. ⛔ Pas en index 2 —
            #    l'ordre du fil ne bouge pas, sinon le `c.max` d'un agent v3 non
            #    modifié s'afficherait comme une température sans qu'aucun
            #    compteur ne bronche (motif complet dans `k_metriques[]`).
            # ⚠️ `lhm` peut valoir `None` (LHM injoignable, panne déjà comptée) ou
            #    porter `None` pour cette sonde (LHM répond et dit qu'il n'a pas
            #    la valeur). LES DEUX donnent le MÊME champ vide sur le fil, et
            #    c'est voulu : le fil n'a pas de jeton « inconnu ». La DIFFÉRENCE,
            #    elle, se lit au bilan — `pannes` d'un côté, `absences` de l'autre.
            degc = lhm.get("cpu.degc") if lhm else None
            out.append(("cpu", [
                _dx(pct, BORNES["cpu"][0], e, "cpu.pct"),
                _borner(ghz_dx, BORNES["cpu"][1], e, "cpu.ghz")
                if ghz_dx is not None else None,
                _dx(cmax, BORNES["cpu"][2], e, "cpu.cmax")
                if cmax is not None else None,
                _dx(degc, BORNES["cpu"][3], e, "cpu.degc")
                if degc is not None else None,
            ]))

        # ── gpu : % + °C, et l'absence de °C est une DONNÉE (W10) ────────────
        if self.gpu is not None:
            lu = self._tenter("gpu", self.gpu.lire)
            if lu is not None:
                g_pct, g_c, g_w, g_rpm = lu
                if g_pct is not None:
                    # ⚠️ CHAQUE GRANDEUR PORTE SON PROPRE `None` (W10) : un
                    #    capteur invalide tait SA ligne, pas les trois autres.
                    #    Le firmware écrit « -- » en gris sur CETTE ligne-là et
                    #    la case reste RÉELLE.
                    out.append(("gpu", [
                        _dx(g_pct, BORNES["gpu"][0], e, "gpu.pct"),
                        _dx(g_c, BORNES["gpu"][1], e, "gpu.degc")
                        if g_c is not None else None,
                        _dx(g_w, BORNES["gpu"][2], e, "gpu.w")
                        if g_w is not None else None,
                        _dx(g_rpm, BORNES["gpu"][3], e, "gpu.rpm")
                        if g_rpm is not None else None,
                    ]))
                # g_pct None ⇒ ON N'ÉMET RIEN : la case périmera d'elle-même en
                # 3 s et dira « -- ». ⛔ Émettre une valeur inventée serait le
                # mensonge que tout ce projet traque.

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
        vm = self._tenter("ram", psutil.virtual_memory)
        if vm is not None:
            out.append(("ram", [_dx(vm.percent, BORNES["ram"][0], e, "ram.pct"),
                                _dx(vm.total / 2**30, BORNES["ram"][1], e,
                                    "ram.total")]))

        # ── net : ↓ et ↑ en Mb/s (BITS — c'est l'unité du descripteur) ───────
        n1 = self._tenter("net", psutil.net_io_counters)
        if n1 is not None:
            dtn = max(t - self._nt0, 1e-6)
            if self._n0 is None:
                pass  # premier tour après une panne : on ré-amorce, sans publier
            elif (n1.bytes_recv < self._n0.bytes_recv or
                  n1.bytes_sent < self._n0.bytes_sent):
                # 🔴 UN COMPTEUR CUMULÉ QUI RECULE (correctif de revue 2026-08-18).
                #    Interface désactivée/réactivée, pilote réinitialisé : l'ancien
                #    `max(delta, 0)` publiait alors un **0 Mb/s FABRIQUÉ**, hors
                #    du compteur d'écrêtages ⇒ le bilan certifiait « toute valeur
                #    emise est la valeur mesuree » sur une valeur inventée.
                #    ⇒ On ne publie RIEN, on ré-amorce, et ON LE COMPTE.
                # ⚠️ PAR `_panne()`, PAS PAR UN INCRÉMENT NU (revue 2026-08-19) :
                #    l'incrément direct sautait la ligne de stderr du premier
                #    événement, donc l'information n'apparaissait QU'AU BILAN — à la
                #    fin de la session. Asymétrique avec toutes les autres pannes de
                #    source, et avec la doctrine « une source morte meurt SEULE »,
                #    qui est bruyante partout ailleurs.
                self._panne("net", "recul",
                            "un compteur cumule a RECULE (interface reactivee ? "
                            "pilote reinitialise ?) — rien n'est publie ce tour")
            else:
                rx = (n1.bytes_recv - self._n0.bytes_recv) * 8 / 1e6 / dtn
                tx = (n1.bytes_sent - self._n0.bytes_sent) * 8 / 1e6 / dtn
                out.append(("net", [_dx(rx, BORNES["net"][0], e, "net.rx"),
                                    _dx(tx, BORNES["net"][1], e, "net.tx")]))
            self._n0, self._nt0 = n1, t
        # ⛔ errin/errout/dropin/dropout NE SONT PAS PUBLIÉS : cette tour rend
        #    `dropin = 113 558 935 299 979`, une valeur impossible. On regarde un
        #    compteur avant de le publier.

        # ── disk : DÉBIT total en Mo/s (OCTETS — l'unité d'un disque) ────────
        d1 = self._tenter("disk", psutil.disk_io_counters)
        if d1 is not None:
            dtd = max(t - self._dt0, 1e-6)
            if self._d0 is None:
                pass
            elif (d1.read_bytes < self._d0.read_bytes or
                  d1.write_bytes < self._d0.write_bytes):
                # ⚠️ Idem `net:recul` — par `_panne()`, pour que le PREMIER
                #    événement soit dit sur stderr et pas seulement au bilan.
                self._panne("disk", "recul",
                            "un compteur cumule a RECULE (disque retire ? reset de "
                            "pilote ?) — rien n'est publie ce tour")
            else:
                mo_s = ((d1.read_bytes - self._d0.read_bytes) +
                        (d1.write_bytes - self._d0.write_bytes)) / 1e6 / dtd
                # 🔴 dn4-8 / D13 : TROIS `tr/min` S'AJOUTENT, EN POSITIONS
                #    INTERNES. Le `Mo/s` GARDE la position 0 parce qu'il est la
                #    seule grandeur de cette métrique qui SURVIT à l'arrêt de LHM :
                #    une valeur principale absente fait que la métrique n'est PAS
                #    émise, donc un ventilateur en position 0 ferait disparaître le
                #    débit disque avec les ventilateurs.
                # ⚠️ CE QUI TOMBE DE D13 §4.4, ET IL FAUT L'ÉCRIRE : la séparation
                #    LECTURE / ÉCRITURE. D13 demandait SIX grandeurs sur `disk`,
                #    `DN_LINK_GRANDEURS_MAX` en donne QUATRE. ⇒ réduction de
                #    périmètre portée à l'owner et au ledger, ⛔ pas un rognage.
                extr = self.lhm.extraction_moyenne(lhm) if lhm else None
                noctua = lhm.get("fan.cpu_noctua") if lhm else None
                boitier = lhm.get("fan.case_group") if lhm else None
                out.append(("disk", [
                    _dx(mo_s, BORNES["disk"][0], e, "disk"),
                    _dx(extr, BORNES["disk"][1], e, "disk.extraction")
                    if extr is not None else None,
                    _dx(noctua, BORNES["disk"][2], e, "disk.cpu_noctua")
                    if noctua is not None else None,
                    _dx(boitier, BORNES["disk"][3], e, "disk.case_group")
                    if boitier is not None else None,
                ]))
            self._d0, self._dt0 = d1, t

        self._t0 = t
        return out

    def fermer(self):
        if self.gpu is not None:
            self.gpu.fermer()
        # ⚠️ La source LHM n'est jamais `None` (voir `__init__`) : elle porte une
        #    CONNEXION, et une socket non fermée survivrait au processus le temps
        #    du TIME_WAIT. ⛔ Un `fermer()` incomplet est la moitié du patron.
        if self.lhm is not None:
            self.lhm.fermer()


class LiaisonEnAttente(IOError):
    """Le port est en backoff : la trame n'est pas envoyée, et ce n'est PAS une
    nouvelle panne — c'est la panne déjà signalée qui dure.

    ⚠️ Type DISTINCT pour que la boucle d'émission puisse dédoublonner (revue
       2026-08-19). Sans lui, chaque trame produisait une ligne de stderr, soit
       CINQ PAR SECONDE sans fin, alors que le correctif du 2026-08-18 promettait
       précisément d'éviter « cinq tentatives ET cinq lignes de stderr par seconde ».
    """


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
        # Backoff de réouverture — voir `envoyer()`. ⛔ Un port qui a disparu en
        # cours de session (usbipd attach, carte débranchée) ne doit pas produire
        # cinq tentatives et cinq lignes de stderr par seconde, sans fin.
        self._echecs_ouverture = 0
        # ⚠️ COMPTEUR SÉPARÉ DES ÉCHECS D'ENVOI (revue 2026-08-19) : c'est lui qui
        #    arme le backoff quand le port s'ouvre mais que `write()` expire — la
        #    carte en panique haltée, le pire cas que le correctif précédent nommait
        #    sans le couvrir. Deux compteurs, parce que les deux pannes sont
        #    différentes : port absent contre carte muette.
        self._echecs_envoi = 0
        self._prochain_essai = 0.0
        # Queue du dernier drain — voir `_drainer()` (revue 2026-08-19).
        self._queue_drain = b""
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
            # 🔴 BACKOFF (correctif de revue 2026-08-18). Sans lui, une panne de
            #    liaison était AMPLIFIÉE ×5 par dn4-1 : dn2-2 émettait 1 trame/s
            #    donc 1 tentative/s ; dn4-1 en émet CINQ, et `envoyer` referme le
            #    port à la moindre exception ⇒ **5 close()/open() PAR SECONDE**,
            #    chacun re-posant `dtr=False; rts=False` sous Windows — cinq fois
            #    par seconde la séquence dont §13.11.5 dit précisément qu'on n'a
            #    JAMAIS prouvé qu'elle n'était pas nécessaire pour éviter un reset.
            # ⚠️ PIRE CAS MESURABLE : carte en panique haltée, `write_timeout = 2` s
            #    ⇒ 5 × 2 s = **10 s bloquées dans un seul cycle**, ce qui déclenche
            #    `rattrapages` + `reamorcer()` à chaque tour et fait monter
            #    `erreurs_envoi` à 5/s sur stderr. Le budget `write_timeout` de
            #    dn2-2 a été dimensionné pour UNE trame par seconde, pas cinq.
            maintenant = time.monotonic()
            if maintenant < self._prochain_essai:
                # ⚠️ PAS DE COMPTE À REBOURS DANS CE MESSAGE (revue 2026-08-19) : il
                #    changeait à chaque ligne, donc AUCUN dédoublonnage n'était
                #    possible en aval, et la boucle imprimait cinq lignes par seconde
                #    sans fin — la moitié exacte de ce que le correctif du 2026-08-18
                #    promettait d'éviter (« cinq tentatives ET cinq lignes de stderr
                #    par seconde »). Le texte est désormais STABLE et l'appelant le
                #    dédoublonne.
                raise LiaisonEnAttente(
                    f"port {self._port} en attente de reouverture "
                    f"({self._echecs_ouverture + self._echecs_envoi} echec(s) "
                    f"consecutif(s))")
            try:
                self._ouvrir()
            except Exception:
                self._echecs_ouverture += 1
                # Paliers 0,5 · 1 · 2 · 4 s, plafonnés à 5 s — soit AU PLUS une
                # tentative d'ouverture par cycle de cinq trames, jamais cinq.
                delai = min(0.5 * (2 ** min(self._echecs_ouverture - 1, 4)), 5.0)
                self._prochain_essai = time.monotonic() + delai
                raise
            self._echecs_ouverture = 0
            self._prochain_essai = 0.0
        try:
            trame_octets = b"pc " + ligne.encode("ascii")
            ecrits = self._con.write(trame_octets)
            if ecrits is not None and ecrits != len(trame_octets):
                # Une demi-trame atteint le REPL : elle corrompt SA ligne et la
                # suivante. Mieux vaut le dire que de compter un envoi réussi.
                raise IOError(f"ecriture partielle {ecrits}/{len(trame_octets)} o")
            self._drainer()
            self._echecs_envoi = 0
        except Exception:
            # 🔴 LE BACKOFF S'ARME AUSSI SUR L'ÉCHEC D'ENVOI — correctif de revue
            #    2026-08-19, ET C'EST LE PIRE CAS QUE LE CORRECTIF DU 2026-08-18
            #    NOMMAIT SANS LE COUVRIR. Sur une carte en PANIQUE HALTÉE, le port
            #    reste énuméré : `_ouvrir()` RÉUSSIT (donc `_prochain_essai` était
            #    remis à 0,0), et c'est `write()` qui expire sur `write_timeout = 2`.
            #    Le backoff n'était armé que dans l'`except` de l'ouverture ⇒ la
            #    trame suivante rouvrait IMMÉDIATEMENT : les 5 × 2 s = 10 s bloquées
            #    par cycle et les 5 `close()/open()` par seconde — chacun re-posant
            #    `dtr=False; rts=False` — SUBSISTAIENT INTÉGRALEMENT.
            self._echecs_envoi += 1
            delai = min(0.5 * (2 ** min(self._echecs_envoi - 1, 4)), 5.0)
            self._prochain_essai = time.monotonic() + delai
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
            # 🔴 LE MARQUEUR PEUT ÊTRE COUPÉ ENTRE DEUX DRAINS (revue 2026-08-19).
            #    `count()` portait sur le résultat d'UN SEUL `read()`, sans report :
            #    à 5 drains/s et 115 200 bauds, une frontière de `read()` tombant à
            #    l'intérieur des 22 octets du marqueur est banale. ⇒ refus
            #    SOUS-COMPTÉS, et si tous les marqueurs sont coupés le bilan imprime
            #    « aucun refus signalé par le firmware sur le fil » pendant que
            #    100 % des trames sont rejetées — le défaut exact que ce compteur a
            #    été créé pour fermer. On garde la queue du tampon précédent.
            MARQUEUR = b"non-zero error code"
            fenetre = self._queue_drain + retour
            self.refus_firmware += fenetre.count(MARQUEUR)
            # On ne conserve que ce qui pourrait être un début de marqueur coupé.
            self._queue_drain = fenetre[-(len(MARQUEUR) - 1):] if len(MARQUEUR) > 1 else b""

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
    ap.add_argument("--lhm", metavar="HOTE:PORT", default=None,
                    help="ou joindre LibreHardwareMonitor (defaut 127.0.0.1:8085). "
                         "⚠️ EXERCE les chemins d'echec ; ⛔ ne remplace PAS AC8, "
                         "qui exige le VRAI service coupe")
    ap.add_argument("--lhm-timeout", type=float, default=LHM_TIMEOUT_S,
                    metavar="S", help="timeout de lecture LHM en secondes "
                                      "(defaut %.2f, motif chiffre dans le code)"
                                      % LHM_TIMEOUT_S)
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
    # ⚠️ `--lhm` est un point d'ENTREE d'exercice, ⛔ pas une option de confort :
    #    sans lui, eprouver « lecture lente » ou « service muet » exigerait de
    #    couper le VRAI LHM de la tour, donc un geste owner, pour un chemin de
    #    code. ⛔ Il ne dispense de RIEN : AC8 se joue sur le vrai service.
    lhm_hote, lhm_port = LHM_HOTE, LHM_PORT
    if args.lhm:
        bout = args.lhm.rsplit(":", 1)
        lhm_hote = bout[0] or LHM_HOTE
        if len(bout) == 2:
            lhm_port = int(bout[1])
        print("[agent] ⚠️ LHM pointe sur %s:%d par --lhm — ⛔ ce n'est PAS la "
              "configuration de regime." % (lhm_hote, lhm_port), file=sys.stderr)
    collecteur = Collecteur(lhm_hote=lhm_hote, lhm_port=lhm_port,
                            lhm_timeout_s=args.lhm_timeout)

    depart = time.monotonic()
    seq = 0
    erreurs_envoi = 0
    # ⚠️ Le dernier message d'attente DÉJÀ IMPRIMÉ — pour ne pas répéter cinq fois
    #    par seconde que le port est en backoff (revue 2026-08-19). Les VRAIES
    #    erreurs, elles, restent imprimées une par une.
    attente_signalee = None
    rattrapages = 0
    cycles = 0  # cycles de photo RÉELLEMENT effectués (cadence de `--temoin`)
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
            for metrique, valeurs in photo:
                # ⚠️ `seq` numérote les TRAMES, pas les cycles : cinq trames par
                #    seconde consomment cinq seq. C'est ce que le firmware
                #    attend (suivi de seq GLOBAL, jamais par métrique — sinon il
                #    compterait 4 « pertes » à chaque tour de cinq).
                seq += 1
                try:
                    sortie.envoyer(trame(seq, t_ms, metrique, valeurs))
                    trames_emises += 1
                except BrokenPipeError:
                    # stdout redirigé vers un consommateur qui s'est fermé : boucler en
                    # imprimant une erreur par seconde n'a aucun sens, on sort.
                    print("[agent] stdout ferme par le consommateur — arret",
                          file=sys.stderr)
                    rompu = True
                    break
                except LiaisonEnAttente as exc:
                    # La panne a DÉJÀ été signalée : on compte, on n'imprime qu'au
                    # changement d'état. ⛔ Cinq lignes par seconde noieraient
                    # précisément ce qu'on veut voir.
                    erreurs_envoi += 1
                    if attente_signalee != str(exc):
                        attente_signalee = str(exc)
                        print(f"[agent] {exc} — les trames sont ABANDONNEES tant que "
                              f"le backoff court (compte total : {erreurs_envoi})",
                              file=sys.stderr)
                except Exception as exc:
                    erreurs_envoi += 1
                    attente_signalee = None
                    print(f"[agent] envoi {sortie.nom} en échec ({erreurs_envoi}) : {exc}",
                          file=sys.stderr)
            if rompu:
                break

            cycles += 1
            # 🔴 UN COMPTEUR DE CYCLES, PAS `seq // len(photo)` (correctif de revue
            #    2026-08-18). `seq` numérote les TRAMES et `len(photo)` vaut 5 OU
            #    MOINS selon que les sources ont répondu : le quotient n'était donc
            #    pas le numéro de cycle. Après un cycle à 4 trames il pouvait
            #    STAGNER (ligne de témoin répétée) ou BONDIR de 2 (ligne sautée).
            #    ⇒ l'instrument qui publie le coût propre de l'agent — LE CHIFFRE
            #    DU CRITÈRE N°4 DU BRIEF — avait un pas qui dépendait de la santé
            #    d'une source. Une variable coûte moins cher qu'un doute.
            if args.temoin and cycles % 10 == 0:
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
        # ⛔ UNE SOURCE QUI EST MORTE EN COURS DE ROUTE NE SORT PAS EN SILENCE
        #    NON PLUS. Isoler les sources (correctif de revue 2026-08-18) évite
        #    que l'agent meure entier ; sans ce bilan, ça remplacerait une mort
        #    BRUYANTE par un silence — la case dirait « -- » et personne ne
        #    saurait pourquoi.
        if collecteur.pannes:
            détail = " · ".join(f"{k}={v}" for k, v in
                                sorted(collecteur.pannes.items()))
            print(f"[agent] 🔴 PANNES DE SOURCE (metrique NON emise, case a « -- ») : "
                  f"{détail}", file=sys.stderr)
        else:
            print("[agent] aucune panne de source : les cinq ont repondu a chaque cycle",
                  file=sys.stderr)
        if collecteur.gpu is None:
            print(f"[agent] ⚠️ source GPU restee INDISPONIBLE toute la session "
                  f"({collecteur.gpu_motif}) — aucune trame `gpu` emise",
                  file=sys.stderr)
        # ── LHM (dn4-8) ──────────────────────────────────────────────────────
        # 🔴 TROIS FAITS DISTINCTS, TROIS LIGNES — ⛔ jamais fondus en une.
        #    « LHM n'a pas repondu » (panne), « LHM a repondu sans cette valeur »
        #    (absence, W10) et « la lecture a coute X » sont trois diagnostics qui
        #    envoient chercher a trois endroits differents. Les confondre est le
        #    defaut « tronquee / trop longue » que le firmware a du dedoubler.
        lhm = getattr(collecteur, "lhm", None)
        if lhm is not None:
            if lhm.duree_n:
                moy = lhm.duree_somme / lhm.duree_n * 1000.0
                print(f"[agent] LHM : {lhm.reponses} lecture(s) reussie(s), "
                      f"{lhm.echecs} en echec — duree moyenne {moy:.1f} ms, "
                      f"MAX {lhm.duree_max * 1000.0:.1f} ms "
                      f"(timeout pose : {lhm.timeout_s * 1000.0:.0f} ms)",
                      file=sys.stderr)
                # ⛔ UN MAX AU RAS DU TIMEOUT NE SORT PAS EN SILENCE : c'est le
                #    signe que la lecture a ete COUPEE, pas qu'elle a fini.
                if lhm.duree_max >= lhm.timeout_s * 0.9:
                    print(f"[agent] 🔴 la lecture LHM la plus longue "
                          f"({lhm.duree_max * 1000.0:.0f} ms) atteint 90 % du "
                          f"timeout — le plafond a probablement COUPE une lecture. "
                          f"⚠️ Le dimensionnement du timeout est a revoir, ⛔ pas a "
                          f"supposer suffisant.", file=sys.stderr)
            if lhm.reponses == 0:
                print(f"[agent] ⚠️ LHM est reste INJOIGNABLE toute la session "
                      f"({lhm.motif}) — la °C CPU et les tr/min n'ont JAMAIS ete "
                      f"publies. ⛔ Ce n'est pas « zero », c'est « inconnu » : le "
                      f"fil porte un champ VIDE et la carte affiche « -- ».",
                      file=sys.stderr)
            if lhm.absences:
                détail = " · ".join(f"{k}={v}" for k, v in
                                    sorted(lhm.absences.items()))
                print(f"[agent] ⚠️ ABSENCES LHM (LHM a REPONDU, sans cette "
                      f"valeur — champ VIDE sur le fil, ⛔ PAS une panne) : "
                      f"{détail}", file=sys.stderr)
            elif lhm.reponses:
                print("[agent] aucune absence LHM : les cinq sondes ont rendu une "
                      "valeur a chaque lecture reussie", file=sys.stderr)


if __name__ == "__main__":
    try:
        sys.exit(principal())
    except KeyboardInterrupt:
        # Filet pour un Ctrl+C AVANT l'entrée dans la boucle (ouverture du port,
        # amorçage psutil) : la boucle, elle, a son propre try/finally qui imprime
        # le bilan et ferme la sortie.
        print("[agent] arrêt demandé (Ctrl+C)", file=sys.stderr)
        sys.exit(0)

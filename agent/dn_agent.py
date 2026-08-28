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
import os
import sys
import threading
import time

# 🔴 dn4-8 / AC6 : DEUX MODULES DE LA **STDLIB**, ⛔ AUCUNE DEPENDANCE NOUVELLE.
#    `http.client` (⛔ pas `requests`) parce qu'il expose la CONNEXION, donc le
#    keep-alive — et l'A/B d'AC2 a montre que **l'ouverture de connexion TCP
#    dominait le cout**.
# 🔴 CHIFFRES REPRIS DE **LA CAMPAGNE 3**, LES DEUX COLONNES, ⛔ PLUS COUSUS.
#    Corrige en revue (dn4-8, 2026-08-21) : ce texte citait le keep-alive de la
#    campagne 3 (1,844 / 2,188 / 1,125) a cote d'un « neuve » pris dans la
#    campagne **2** (2,984 / 3,516 / 4,766) — deux tirs differents presentes comme
#    UN A/B. ⛔ L'A/B cite n'a jamais produit ces nombres-la ensemble, et c'est
#    exactement le « a service rendu egal » que ce depot exige ailleurs.
#      · connexion NEUVE     3,27 / 3,39 / 4,13 ms  -> C1 (3,0 ms) DEPASSE
#      · keep-alive          1,84 / 2,19 / 1,13 ms  -> LES QUATRE seuils passes
#    (ordre : /data.json · /metrics · /Sensor. Campagne 2, tout-neuf, avait rendu
#     2,98 / 3,52 / 4,77 — meme conclusion, autre tir : ⛔ ne pas melanger.)
#
# 🔴🔴 CES SIX NOMBRES SONT **MORTS** — 2e revue, 2026-08-24. ⛔ NE PAS LES CITER.
#    La story dn4-8 declare elle-meme AC2 MORT : l'instrument de mesure a ete
#    CORRIGE apres le tir (`_cpu_ms`, filtrage de `murs` sur les seuls succes),
#    et la regle du depot est « quand une revue a change un INSTRUMENT, les
#    chiffres publies sont MORTS ». Ils ont pourtant ete CORRIGES ET REPUBLIES
#    ici, dans le meme intervalle de commits qui les declarait morts — la classe
#    exacte que la revue venait de fermer trois commits plus tot.
# ✅ CE QUI SURVIT, ET C'EST TOUT : **LA DECISION**. `/metrics` en connexion
#    PERSISTANTE, `http.client` pour le keep-alive, WMI elimine PAR SYMPTOME
#    (`root\LibreHardwareMonitor` n'existe pas ; `root\OpenHardwareMonitor` rend
#    0 instance). Le CLASSEMENT tient ; les MILLISECONDES, non.
# ⚠️ Aucun re-tir d'AC2 n'a eu lieu. Tant qu'il n'a pas eu lieu, ces nombres sont
#    des reperes historiques dates, ⛔ pas des mesures opposables.
#    `urllib.request` ne garde pas la connexion.
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


# =============================================================================
# 🔴 L'HORLOGE DE LA CARTE (dn4-18) — LES LITTÉRAUX, ET POURQUOI ILS SONT ANCRÉS
# =============================================================================
# ⛔ CE QUE L'AGENT CHERCHE SUR LE FIL EST ÉCRIT ICI, EN UN SEUL ENDROIT, PARCE
#    QUE C'EST CE QU'UNE GATE PEUT RELIRE. `tools/verif_miroir_horloge_dn418.py`
#    vérifie que CHACUN de ces octets existe TEL QUEL dans `dn_console.c` /
#    `dn_rtc.c`. Motif : « les deux tables sont recopiées, pas dérivées » est
#    déjà le risque assumé de `BORNES` ↔ `k_metriques[]` — mais LÀ-BAS une
#    dérive se verrait en `rejets_bornes`. ICI, rien ne la signalerait : un
#    libellé retouché ferait retomber l'agent en INCONNU EN SILENCE, et la barre
#    resterait « --:-- » pour toujours.
#
# 🔴 DEUX PIÈGES MESURÉS SUR LE FLUX RÉEL (captures du 2026-08-26), ⛔ PAS DEUX
#    PRÉCAUTIONS THÉORIQUES :
#
#  1. `FIABLE` APPARAÎT 6 FOIS DANS UN SEUL BOOT, ET 3 DE CES 6 DISENT LE
#     CONTRAIRE. Le firmware journalise aussi :
#         W (3309) dn_rtc: 🔴 OS = 1 — … l'heure lue (…) N'EST PAS FIABLE. …
#     ⇒ un `if b"FIABLE" in ligne` lirait « N'EST PAS FIABLE » comme FIABLE :
#       l'agent croirait l'horloge bonne AU MOMENT EXACT où elle ne l'est pas.
#     ⇒ ET `FIABLE` est aussi un SOUS-MOT de `NON FIABLE (OS=1)`.
#     ⛔ PARADE : l'état n'est JAMAIS cherché en sous-chaîne. Il est extrait
#       d'une POSITION ANCRÉE, puis comparé À L'IDENTIQUE à la table ci-dessous.
#
#  2. LA CONSOLE ÉMET DU CRLF (471 CRLF sur 471 LF, mesuré) et sa ligne la plus
#     longue fait 483 o. ⇒ on rstrip le `\r`, et la borne du tampon de lignes
#     est posée AU-DESSUS de ce maximum mesuré, ⛔ pas au jugé.
#
# ⚠️ CE QU'ON NE LIT PAS, ET POURQUOI : la ligne `W (…) dn_rtc: 🔴 OS = 1 …` dit
#    pourtant la vérité. ⛔ On ne la lit pas : c'est un ESP_LOGW (donc filtrable
#    par le niveau de log, donc pas un contrat), et c'est précisément elle qui
#    porte le piège n°1. Trois sources ANCRÉES suffisent.

# Les cinq états, VERBATIM (`dn_rtc.c:442-456` pour quatre, `dn_console.c` pour
# « NON ARMEE », qui n'est pas un état du driver mais l'absence de driver).
DN_H_ETATS = {
    b"JAMAIS LUE":        "INCONNU",    # armée, mais aucune lecture valide encore
    b"FIABLE":            "OS0",
    b"MUETTE":            "MUET",       # elle ne répond plus : ⛔ rien à poser
    b"NON FIABLE (OS=1)": "OS1",
    b"NON ARMEE":         "NON_ARMEE",  # ⛔ TERMINAL : le device I2C n'existe pas
}

# Les trois ANCRES d'état. Chacune existe telle quelle dans le firmware.
DN_H_ANCRE_RTC = b"horloge PCF85063A @ 0x"   # dn_console.c — reponse de `rtc`
DN_H_ANCRE_BARRE = b"\xc2\xb7 horloge "      # « · horloge » — bandeau de boot
DN_H_ANCRE_OS = b"bit OS     : "             # dn_console.c — le bit, en clair
# 🔴 LA RECEVABILITE DE L'HEURE LUE, IMPRIMEE SUR LA MEME LIGNE QU'ELLE
#    (correctif de revue 2026-08-26). `dn_console.c:7432` accole deliberement
#    « — AFFICHABLE » / « — ⛔ NON AFFICHABLE » a la valeur, et son commentaire
#    dit pourquoi : « imprimer l'heure sans lui, c'est exactement le mensonge
#    que la barre a interdiction de commettre ». ⛔ Prendre la valeur en jetant
#    son verdict, c'est commettre ce mensonge sur l'AUTRE surface de rendu.
# ⚠️ « AFFICHABLE » est un SOUS-MOT de « NON AFFICHABLE » : ⛔ on ne teste QUE
#    la forme negative, jamais la positive.
DN_H_NON_AFFICHABLE = b"NON AFFICHABLE"
DN_H_ANCRE_LUE = b"lue        : "            # dn_console.c — l'heure de la carte
# Les quatre verdicts de `rtc set`, VERBATIM (`dn_console.c`, cmd_rtc).
DN_H_POSE_OK = b"heure posee : "
DN_H_POSE_ETAT = b"\xe2\x80\x94 etat "       # « — etat » sur la MEME ligne
DN_H_POSE_REFUS = (
    b"horloge NON ARMEE",
    b"date ou heure INVALIDE",
    b"ECRITURE REFUSEE ou OS RESTE A 1",
    b"valeur HORS PLAGE",
)

# ── LES CADENCES, ET LEUR MOTIF CHIFFRÉ (AC4.3) ──────────────────────────────
# 🔴 LE PIRE CAS À FERMER EST MESURÉ : une interrogation `rtc` rend **2 273 à
#    2 648 o** et une pose **376 o** (2026-08-26), face à **272,9 o/s** d'écho
#    console en régime. Une boucle serrée NOIERAIT `echo_octets` — l'instrument
#    d'AC3 de dn2-2, sur le fil qui EST le transport des cinq métriques.
# ⚠️ En régime : 2 598 / 600 = **4,3 o/s**, soit **+1,6 %** du bruit console.
# ⚠️ Pire cas (port qui bat, une reprise toutes les 30 s) : (2 598 + 376) / 30
#    = **99 o/s**, soit **+36 %** — et un port qui bat est DÉJÀ visible en
#    `erreurs_envoi`. ⛔ Le plancher est ce qui empêche « plusieurs Ko/s ».
DN_H_PERIODE_S = 600.0     # interrogation de régime (aussi le filet d'AC6)
DN_H_PLANCHER_S = 30.0     # ⛔ JAMAIS deux interrogations plus près que ça
DN_H_ATTENTE_VERDICT_S = 10.0   # au-delà, la pose est comptée SANS RÉPONSE
DN_H_BACKOFF_S = 60.0      # 1er palier après un refus ; double à chaque fois
DN_H_BACKOFF_MAX_S = 3600.0

# 🔴 LE SEUIL D'ÉCART (AC6.3) — IL EST ENTRE DEUX GRANDEURS MESURÉES :
#    · la dérive est bornée à |dérive| < 280 ppm ⇒ **≤ ~24 s/jour**
#      (…-capteurs-i2c.md §13.15.5) ⇒ 120 s = **5 jours** de dérive : un seul
#      jour ne peut PAS le déclencher ;
#    · un décalage de fuseau vaut **3 600 s** ⇒ 30× le seuil : un changement
#      été/hiver le déclenche TOUJOURS.
#    · et il est très au-dessus de la quantification de la lecture (la carte
#      rend des secondes ENTIÈRES, ±1 s, plus ~50 ms d'aller-retour série).
#    ⇒ **il ne peut pas confondre les deux.**
DN_H_SEUIL_ECART_S = 120.0

# 🔴 LE TAMPON DE LIGNES EST BORNÉ, ET LA BORNE EST MESURÉE (AC3.6). La plus
#    longue ligne vue sur le flux réel fait **483 o** ; 1 024 laisse un facteur
#    2. ⛔ Un tampon non borné est une fuite mémoire sur 7 jours — et dn4-5 fait
#    tourner cet agent 7 jours.
DN_H_LIGNE_MAX = 1024


def _jours_civils(a: int, m: int, j: int) -> int:
    """Jours depuis 1970-01-01 pour une date civile (algorithme de Hinnant).

    ⛔ PAS `time.mktime`, ET C'EST LE CŒUR D'AC6. `mktime` interprète une date
       LOCALE, donc il applique le fuseau — et au changement d'heure la même
       heure locale est AMBIGUË. Or ce qu'on compare ici, ce sont deux lectures
       de PENDULE : celle de la carte et celle de la tour. Les traiter en
       calendrier NAÏF (sans fuseau) rend un écart de **exactement 3 600 s** au
       passage été/hiver, ⛔ au lieu d'un 0 ou d'un 3 600 selon l'humeur de la
       libc.
    """
    a -= m <= 2
    ere = (a if a >= 0 else a - 399) // 400
    aoe = a - ere * 400
    joa = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + j - 1
    joe = aoe * 365 + aoe // 4 - aoe // 100 + joa
    return ere * 146097 + joe - 719468


def _secondes_naives(a, mo, j, h, mi, s) -> int:
    """Une date/heure LOCALE décomposée, en secondes, SANS fuseau (voir ci-dessus)."""
    return _jours_civils(a, mo, j) * 86400 + h * 3600 + mi * 60 + s


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
# 🔴 PORTE DE 0,40 A 0,60 s LE 2026-08-21, **PAR LA MESURE EN SEANCE CARTE**,
#    ⛔ pas par prudence. Ce que le regime reel a rendu, LHM DEBOUT :
#      · duree MOYENNE          26,7 ms   (n=61, agent sur COM3, 60 s)
#      · duree MAX              454,7 ms  -> **1 lecture COUPEE** par le plafond
#      · un tir precedent       377,5 ms  -> 0 echec, mais 94 % du plafond
#    ⚠️ LA QUEUE DE DISTRIBUTION EST BIEN AU-DELA DU p95 D'AC2 (16,5 ms). Le
#       critere gele avait mesure `/metrics` avec un instrument DEDIE, qui ne
#       faisait que ca ; l'agent, lui, lit LHM au milieu de cinq sources et de
#       cinq ecritures serie. ⛔ Le p95 d'un instrument dedie ne predit pas la
#       queue d'un regime charge — et c'est une lecon, pas un ajustement.
#    🔴 2e REVUE (2026-08-24) : **LE « 16,5 ms » EST UN NOMBRE MORT D'AC2** (voir
#       le bloc en tete de fichier). ⛔ IL NE JUSTIFIE PLUS RIEN. Ce qui dimensionne
#       `LHM_TIMEOUT_S`, ce sont les TROIS mesures de REGIME ci-dessus (26,7 ms
#       moyen, 454,7 ms max, 377,5 ms sur un tir precedent) — elles, elles ont ete
#       prises sur l'agent, sur COM3, et elles suffisent. Le 16,5 ms n'est garde
#       que pour dire ce qu'un instrument dedie NE predit PAS.
#    ⇒ 0,60 s couvre le max observe (455 ms) avec 32 % de marge.
# ✅ ET LA CONTRAINTE DE CADENCE TIENT TOUJOURS : la resynchronisation ne se
#    declenche qu'au-dela d'UNE PERIODE ENTIERE de retard (1,00 s). A 0,60 s il
#    reste 0,40 s aux cinq autres postes (15,1 ms mesures) et aux cinq ecritures.
#    ⚠️ MESURE, ⛔ PAS SUPPOSE : le scenario « LHM absent » brule le budget ENTIER
#       a CHAQUE cycle, et il a rendu **0 recalage de cadence** a 0,40 s. Le
#       controle est REJOUE a 0,60 s — voir la seance.
LHM_TIMEOUT_S = 0.6

# ⚠️ PLAFOND DE TAILLE DU CORPS `/metrics`. La capture reelle du 2026-08-21 fait
#    75,1 Ko (253 lignes `lhm_`) ; 8 Mo laissent deux ordres de grandeur de marge
#    et bornent le cas « flux sans fin » que le timeout NE PEUT PAS voir (chaque
#    morceau arrivant a l'heure, aucune attente ne depasse jamais le budget).
LHM_CORPS_MAX = 8 * 1024 * 1024

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
# 🎯 4e COLONNE = LA FAMILLE `/metrics` ATTENDUE, ajoutee en revue (2026-08-21).
#    C'est elle qui porte l'UNITE. Sans elle, la raison d'avoir choisi `/metrics`
#    contre `/data.json` restait une intention ecrite, ⛔ jamais un controle.
LHM_SONDES = (
    # (cle interne, identifiant LHM complet, FAMILLE attendue, PROVENANCE)
    ("cpu.degc", "/intelcpu/0/temperature/10", "lhm_cpu_temperature_celsius",
     "MESURE (LHM 0.9.6, 2026-08-21) — « CPU Package », 41,0 degC ; recoupee par un "
     "chemin INDEPENDANT, le Super I/O /lpc/nct6792d/0/temperature/0 a 40,5 degC "
     "(1,2 %). ⚠️ instantane n=1 : conforte le mapping, ⛔ ne qualifie pas le mouvement"),
    ("fan.top_out", "/lpc/nct6792d/0/fan/0", "lhm_motherboard_fan_rpm",
     "MESURE (jointure BIOS<->LHM par RPM, 2026-08-21) — en-tete CPU_FAN2, "
     "extraction HAUTE. ⚠️ l'ordre naif en faisait CPU_FAN1 : REFUTE"),
    ("fan.cpu_noctua", "/lpc/nct6792d/0/fan/1", "lhm_motherboard_fan_rpm",
     "MESURE (jointure BIOS<->LHM par RPM, 2026-08-21) — en-tete CPU_FAN1, "
     "ventirad Noctua bi-ventilateur (repos 305, plafond 1112)"),
    ("fan.case_group", "/lpc/nct6792d/0/fan/2", "lhm_motherboard_fan_rpm",
     "MESURE (jointure BIOS<->LHM par RPM, 2026-08-21) — en-tete SYS_FAN1, DEUX "
     "ventilateurs chaines sur UN tachy"),
    ("fan.rear_out", "/lpc/nct6792d/0/fan/4", "lhm_motherboard_fan_rpm",
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
# 🔴 DEFAUT TROUVE EN REVUE (code review dn4-8, 2026-08-21) : LA PROPRIETE
#    CI-DESSUS N'ETAIT PAS CODEE. La regex s'ecrivait `^lhm_\S+` — elle MATCHAIT
#    le nom de famille et LE JETAIT, la cle etant `hardwareId + sensorId` seuls.
#    Donc `lhm_cpu_temperature_fahrenheit` atterrissait dans la case °C sans que
#    rien ne bronche : EXACTEMENT le defaut pour lequel `/data.json` a ete
#    elimine, et pour lequel toute la campagne d'AC2 a ete payee.
# ⇒ LA FAMILLE EST CAPTUREE (groupe 1) ET VERIFIEE contre celle que la sonde
#   ATTEND (4e colonne de `LHM_SONDES`). Un renommage d'unite se voit MAINTENANT.
_LHM_LIGNE = re.compile(
    r'^(lhm_\S+)\s+\{.*?"sensorId"="([^"]*)".*?"hardwareId"="([^"]*)".*?\}'
    r'\s+(\S+)\s*$')


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

    ───────────────────────────────────────────────────────────────────────────
    🔴 AC3 — GARDE DE COHERENCE PAR TIR : **DECISION, ET ELLE EST « OUI »**
    ───────────────────────────────────────────────────────────────────────────
    AC3 exigeait litteralement de *« decider si une garde equivalente est due
    ici, et d'ECRIRE LE MOTIF DANS LES DEUX CAS »*. La revue du 2026-08-21 a
    constate que la phrase n'apparaissait QU'UNE FOIS dans tout le depot : dans
    l'AC lui-meme. AC3 etait donc marque solde sans que sa derniere exigence ait
    ete honoree. 🔴 **AC3 A ETE ROUVERT PAR L'OWNER LE 2026-08-21.** Voici le
    motif, qui manquait.

    LE RISQUE EST REEL ET IL EST NOMME. `SourceGpuAdl` rejoue `_coherent()` a
    CHAQUE tir parce que ses indices PMLog peuvent glisser d'un pilote a l'autre :
    un decalage y publierait une tension comme une temperature. La question se
    pose ICI AUSSI, et meme plus fort — c'est CETTE story qui a prouve que
    l'ordre naif des canaux `/lpc/nct6792d/0/fan/N` etait FAUX sur les deux
    premiers (`fan/0` = `CPU_FAN2`, ⛔ pas `CPU_FAN1`).

    ⚠️ MAIS LE MECANISME DE DERIVE N'EST PAS LE MEME, ET C'EST CE QUI DECIDE :
      · ADL adresse par **INDICE NUMERIQUE** dans une structure binaire. Un
        indice qui glisse ne se voit PAS — d'ou le temoin de plage.
      · LHM adresse par **CHAINE COMPLETE** (`hardwareId + sensorId`). Un capteur
        qui disparait ou se renomme ne rend pas une AUTRE valeur : il ne rend
        RIEN, et l'absence est deja COMPTEE ET NOMMEE, par sonde.
    ⇒ La permutation silencieuse d'ADL n'a pas d'equivalent ici : pour qu'un
      `fan/2` devienne le tachy d'un autre ventilateur, il faudrait que l'owner
      RECABLE la tour. Ce n'est pas une derive logicielle, et aucune garde
      logicielle ne l'attraperait.

    🎯 CE QUI EST DONC POSE A LA PLACE, ET QUI COUVRE LE VRAI RISQUE : la
       verification de **FAMILLE** (4e colonne de `LHM_SONDES`, voir `_LHM_LIGNE`).
       Elle attrape ce qui, ici, PEUT effectivement changer sous nos pieds sans
       prevenir : **l'UNITE**. Un `..._celsius` devenu `..._fahrenheit`, un
       `..._rpm` devenu `..._percent` — meme identifiant, meme forme, autre
       grandeur. C'est l'exact analogue de « publier une tension comme une
       temperature », et c'est la seule forme que la derive prend sur `/metrics`.
    ⛔ UNE GARDE DE PLAGE SUR LES RPM EST EXPLICITEMENT REFUSEE, avec motif :
       les valeurs legales vont de 0 (fan-stop, une VRAIE valeur) au plafond, sans
       trou. Une plage n'y separe rien — elle ne ferait qu'epingler VERT en
       donnant l'illusion d'un controle. Ce depot a deja paye les gardes
       decoratives.
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
        # 🔴 AJOUTES EN REVUE (2026-08-21) : un desaccord de FORMAT n'est ni une
        #    panne ni une absence de capteur — c'est un TROISIEME etat, et sans
        #    compteur il se deguisait en second.
        self.lignes_lues = 0
        self.lignes_illisibles = 0
        self._illisibles_dit = False
        self._familles_dites = set()
        # 🔴 AJOUTES EN 2e REVUE (2026-08-24) — CHACUN FERME UN ETAT QUI SE
        #    DEGUISAIT EN UN AUTRE :
        #  - `familles` : LHM A RENDU la valeur, sous une AUTRE unite. C'est un
        #    QUATRIEME etat, et il etait range dans `absences`, donc imprime sous
        #    « LHM a REPONDU, SANS cette valeur » — qui envoie inspecter le
        #    capteur alors que le fautif est la config d'unites de LHM.
        #  - `doublons` : deux lignes `lhm_` de familles DIFFERENTES sur la meme
        #    cle. Le dernier arrive gagnait, sans compteur — donc le verdict
        #    dependait de l'ORDRE des lignes, que ce fichier declare lui-meme non
        #    contractualise par Prometheus. C'est la forme exacte d'un renommage
        #    d'unite EN COURS DE DEPLOIEMENT, c'est-a-dire le cas meme que la
        #    verification de famille existe pour attraper.
        #  - `bornages_impossibles` : voir `_borner_socket()`.
        self.familles = {}
        self.doublons = {}
        self._doublons_dits = set()
        self.bornages_impossibles = 0
        self._bornage_dit = False
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
        # 🔴 DEUX DEFAUTS TROUVES EN REVUE (code review dn4-8, 2026-08-21), ET LE
        #    COMMENTAIRE CI-DESSUS AFFIRMAIT DEJA LE CONTRAIRE DU CODE :
        #
        #    (1) LE BUDGET N'EN ETAIT PAS UN. `reste` n'etait verifie QU'ENTRE les
        #        deux tentatives ; a l'interieur d'une tentative, le timeout du
        #        socket est un delai PAR `recv`, pas pour la lecture. Un serveur
        #        qui sert le corps au GOUTTE-A-GOUTTE (75 Ko, 253 lignes `lhm_`)
        #        remettait donc le chrono a zero a chaque paquet et courait SANS
        #        BORNE. Le correctif de 802 ms n'avait ferme que la dimension
        #        « deux tentatives », ⛔ pas celle-la.
        #        ⇒ consequence : depassement d'UNE PERIODE ENTIERE, donc recalage
        #          de cadence, donc echantillon JETE et les cinq metriques
        #          re-amorcees — « le mecanisme le plus dangereux de cette story ».
        #
        #    (2) LE KEEP-ALIVE HERITAIT DU RELIQUAT. La connexion etait creee avec
        #        `timeout=reste` A L'INTERIEUR de la boucle : si la 1re tentative
        #        brulait le budget, la connexion RETENUE gardait quelques
        #        millisecondes de timeout POUR TOUS LES CYCLES SUIVANTS, et rien
        #        ne restaurait jamais `timeout_s`. Le scenario « lent » du harnais
        #        ne pouvait pas le voir : les deux tentatives y echouent, donc
        #        aucune connexion n'est conservee.
        #
        # ⇒ LE PLAFOND EST MAINTENANT APPLIQUE AVANT CHAQUE OPERATION BLOQUANTE,
        #   avec le RESTE du budget — donc la lecture entiere est bornee par `fin`,
        #   quel que soit le nombre de morceaux.
        #
        # 🔴 CORRECTIF DE 2e REVUE (2026-08-24), ET LE COMMENTAIRE PRECEDENT ETAIT
        #    FAUX. Il affirmait « la connexion nait TOUJOURS avec `timeout_s`,
        #    jamais avec un reliquat ». Vrai pour une connexion NEUVE ; FAUX pour la
        #    connexion RETENUE, qui est le chemin NOMINAL :
        #      - `_borner_socket(fin)` etait appele APRES `request()`, donc l'envoi
        #        du cycle N+1 tournait sous le reliquat laisse par la fin de lecture
        #        du cycle N. MESURE : 0,0994 s puis 0,5034 s au lieu de 0,600.
        #      - rien ne restaurait jamais `timeout_s` sur la socket conservee.
        #    ⇒ on borne DES QUE la socket existe, donc AVANT `request()` aussi. Sur
        #    une connexion neuve c'est un no-op (la socket n'existe pas encore) ;
        #    sur une connexion retenue c'est precisement le trou qu'on ferme.
        # ⚠️ `timeout=min(reste, self.timeout_s)` est CONSERVE et c'est VOULU : la
        #    2e tentative ne doit pas depasser `fin`. Ce qui etait faux, c'etait la
        #    PHRASE, ⛔ pas le calcul. Elle est corrigee, pas le code.
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
                        self.hote, self.port, timeout=min(reste, self.timeout_s))
                # 🔴 AVANT L'ENVOI : sur une connexion RETENUE la socket existe
                #    deja et porte le reliquat du cycle precedent (defaut (2)).
                #    ⚠️ `exiger=False` — sur une connexion NEUVE il n'y a pas encore
                #    de socket, et c'est normal.
                self._borner_socket(fin, exiger=False)
                self._c.request("GET", LHM_CHEMIN,
                                headers={"Connection": "keep-alive"})
                self._borner_socket(fin)
                # 🔴 LA SOCKET SE CAPTURE **AVANT** `getresponse()`, ET C'EST LE
                #    CORRECTIF LE PLUS IMPORTANT DE CETTE PASSE. Defaut trouve en
                #    2e revue (2026-08-24), MESURE : CPython fait
                #    `if response.will_close: self.close()` dans `getresponse()`,
                #    ce qui met `HTTPConnection.sock` a **None**. `_borner_socket`
                #    lisait `getattr(self._c, "sock", None)` et devenait donc un
                #    NO-OP SILENCIEUX pour toute la lecture : chaque `recv` gardait
                #    le plafond ENTIER pose avant `getresponse()`.
                #    ⇒ HTTP/1.1 keep-alive : 0,601 s pour 0,600 de budget.
                #    ⇒ HTTP/1.0 `will_close` : **1,102 s, soit 184 % du budget**.
                #    Or 1,102 s > `PERIODE_S` = 1,0 s : c'est exactement le
                #    « depassement d'UNE PERIODE ENTIERE » que ce bloc existe pour
                #    empecher, et aucun mode du stub ne le produisait
                #    (`stub_lhm_dn48.py` pose `HTTP/1.1` + `Content-Length`).
                sock = getattr(self._c, "sock", None)
                rep = self._c.getresponse()
                corps = self._lire_corps(rep, fin, sock)
                if rep.status != 200:
                    raise IOError("HTTP %d sur %s" % (rep.status, LHM_CHEMIN))
                if rep.will_close:
                    self._fermer_connexion()
                return corps.decode("utf-8", "replace")
            except Exception:
                self._fermer_connexion()
                if dernier:
                    raise

    def _borner_socket(self, fin, sock=None, exiger=True):
        """Pose sur le socket le RESTE du budget. ⛔ Jamais `timeout_s` entier.

        🔴 `sock` EXPLICITE (2e revue, 2026-08-24). `getattr(self._c, "sock")`
           rend `None` des que `getresponse()` a ferme la connexion sur une
           reponse `will_close` — le bornage devenait alors un NO-OP MUET et le
           budget etait depasse de 184 % (MESURE). L'appelant capture donc la
           socket AVANT `getresponse()` et nous la passe.
        ⚠️ ⛔ UN BORNAGE IMPOSSIBLE NE SE TAIT PLUS. Si aucune socket n'est
           joignable, la lecture n'est plus bornee : c'est un DEFAUT
           D'INSTRUMENT, il se compte et se dit une fois — ⛔ il ne se devine pas
           a posteriori sur un `duree_max` inexplique.
        """
        reste = fin - time.perf_counter()
        if reste <= 0.0:
            raise TimeoutError("budget de lecture LHM epuise (%.0f ms)"
                               % (self.timeout_s * 1000.0))
        s = sock if sock is not None else getattr(self._c, "sock", None)
        if s is not None:
            s.settimeout(reste)
            return
        # ⚠️ `exiger=False` : AVANT `request()` sur une connexion NEUVE, la socket
        #    n'existe PAS ENCORE (`HTTPConnection` se connecte paresseusement) —
        #    c'est un etat SAIN, et le `timeout=` du constructeur couvre le
        #    `connect()`. ⛔ Compter ce cas fabriquerait une alerte sur un chemin
        #    normal : DEFAUT INTRODUIT PUIS CORRIGE le 2026-08-24, attrape par un
        #    smoke test qui a vu « 8 bornages impossibles » sur un simple
        #    ConnectionRefused. Une alarme qui accuse un etat sain est pire que
        #    pas d'alarme.
        if not exiger:
            return
        self.bornages_impossibles += 1
        if not self._bornage_dit:
            self._bornage_dit = True
            print("[agent] \U0001f534 BORNAGE LHM IMPOSSIBLE : aucune socket joignable "
                  "— la lecture n'est PAS bornee par le budget de %.0f ms. \u26d4 Un "
                  "`duree_max` au-dela du plafond viendra de LA, ⛔ pas du parse."
                  % (self.timeout_s * 1000.0), file=sys.stderr)

    def _lire_corps(self, rep, fin, sock=None):
        """Draine le corps PAR MORCEAUX, chaque attente bornee par le reste.

        🔴 C'est ce qui transforme le plafond en BUDGET : `reste` decroit a
           chaque tour, donc un serveur qui sert un octet a la fois ne peut pas
           faire durer la lecture au-dela de `fin`. ⛔ Un `rep.read()` nu ne le
           garantit pas — il fait N `recv`, chacun avec le plafond ENTIER.
        ⚠️ Le corps est aussi BORNE EN TAILLE : `--lhm` laisse pointer l'agent sur
           n'importe quel hote, et un flux sans fin remplirait la memoire sans
           qu'aucun timeout ne se declenche (chaque morceau arrive a l'heure).
        """
        # 🔴 `read1`, ⛔ PAS `read` — ET C'EST LA MESURE QUI L'A IMPOSE. Avec
        #    `rep.read(65536)`, le `BufferedReader` sous-jacent BOUCLE jusqu'a
        #    remplir les 65536 octets : une seule iteration enchaine donc des
        #    dizaines de `recv`, chacun avec le timeout pose AVANT la boucle, et
        #    le plafond ne se represente qu'a l'iteration SUIVANTE.
        #    Mesure au stub `--mode goutte --retard 0.05` (75 Ko en 40 morceaux) :
        #    **1,71 s pour un budget de 0,60 s.** Borne, mais pas au budget.
        # ✅ `read1(n)` rend ce qu'UN seul `recv` a donne, sans boucler : le
        #    plafond est donc represente entre CHAQUE morceau, et la lecture
        #    entiere est reellement bornee par `fin`.
        # ⚠️ Repli sur `read` si `read1` manque : ⛔ on ne casse pas la lecture, mais
        #    la borne redevient « au morceau pres » — et c'est ECRIT, pas tu.
        lire_un = getattr(rep, "read1", None) or rep.read
        morceaux, total = [], 0
        while True:
            self._borner_socket(fin, sock)
            bout = lire_un(65536)
            if not bout:
                break
            total += len(bout)
            morceaux.append(bout)
            if total > LHM_CORPS_MAX:
                raise IOError("corps /metrics au-dela de %d o — \u26d4 tronque, "
                              "⛔ pas interprete" % LHM_CORPS_MAX)
        return b"".join(morceaux)

    def lire(self):
        """Rend `{cle: float | None}` — UNE entree par sonde, TOUJOURS.

        ⛔ LEVE si LHM ne repond pas : c'est `_tenter()` qui en fera une panne
           COMPTEE ET NOMMEE, une seule fois par type.
        ⚠️ Rendre `None` pour une sonde n'est PAS lever : LHM a repondu et a dit
           qu'il n'avait pas cette valeur. Les deux se comptent SEPAREMENT.
        """
        # 🔴 LE CHRONO COUVRE LA LECTURE **ET** LE PARSE (revue dn4-8, 2026-08-21).
        #    Il ne couvrait que `_get()` : la passe regex sur 253 lignes / 75 Ko
        #    tombait APRES le `finally`. Or `duree_moyenne`/`duree_max` sont
        #    exactement ce qui justifie le dimensionnement a 0,60 s et les « 0,40 s
        #    laisses aux cinq autres postes ». Sur une tour mieux equipee, le parse
        #    grossit — et il etait invisible AU TIMEOUT COMME AU BILAN.
        # ⚠️ Le budget de `_get()`, lui, reste celui du RESEAU : on ne coupe pas un
        #    parse en cours. Ce qui change, c'est qu'on ne PRETEND plus l'ignorer.
        t0 = time.perf_counter()
        try:
            return self._lire(t0)
        finally:
            self._chrono(time.perf_counter() - t0)

    def _lire(self, _t0):
        try:
            txt = self._get()
        except Exception as exc:
            self.echecs += 1
            self._echecs_suite += 1
            self.motif = "%s: %s" % (type(exc).__name__, exc)
            raise

        # 🔴 LES LIGNES `lhm_` ILLISIBLES SONT COMPTEES, ⛔ PLUS JETEES EN SILENCE.
        #    Defaut trouve en revue (2026-08-21) : `if not m: continue` sans
        #    compteur. Une derive de format — ordre des labels inverse (Prometheus
        #    ne le contractualise PAS), absence d'espace avant `{`, virgule
        #    decimale — faisait echouer TOUTES les lignes, donc `table` vide, donc
        #    les cinq sondes a `None`. Le bilan imprimait alors « ABSENCES LHM (LHM
        #    a REPONDU, sans cette valeur — ⛔ PAS une panne) » et envoyait
        #    l'operateur inspecter SES CAPTEURS alors que le fautif est LE PARSEUR.
        # ⚠️ « Deux diagnostics CONTRAIRES qui envoient chercher a deux endroits
        #    differents » — c'est la classe que ce depot a deja payee.
        table = {}
        lues = illisibles = 0
        for ligne in txt.splitlines():
            if not ligne.startswith("lhm_"):
                continue
            lues += 1
            m = _LHM_LIGNE.match(ligne)
            if not m:
                illisibles += 1
                continue
            try:
                v = float(m.group(4))
            except ValueError:
                illisibles += 1
                continue
            if not _fini(v):
                illisibles += 1
                continue
            # ⚠️ On garde la FAMILLE a cote de la valeur : c'est elle qui porte
            #    l'unite, et c'est elle qu'on va confronter a l'attendu.
            ident = m.group(3) + m.group(2)
            # 🔴 2e REVUE (2026-08-24) : « DERNIER ARRIVE GAGNE » EST UN VERDICT
            #    QUI DEPEND DE L'ORDRE DES LIGNES — et ce fichier ecrit lui-meme
            #    que Prometheus ne le contractualise PAS. Si /metrics publie
            #    `..._celsius` ET `..._fahrenheit` pour la meme sonde (forme exacte
            #    d'un renommage d'unite en cours de deploiement, donc LE cas que la
            #    verification de famille existe pour attraper), la valeur retenue
            #    etait tiree au sort par l'ordre du corps.
            # ⇒ ⛔ ON NE TRANCHE PAS : la cle devient CONFLICTUELLE, la valeur est
            #    refusee, et le cas est COMPTE ET NOMME. Une ambiguite se dit,
            #    elle ne se resout pas au hasard.
            precedent = table.get(ident)
            if precedent is not None and precedent[0] != m.group(1):
                table[ident] = (None, None)
                self.doublons[ident] = self.doublons.get(ident, 0) + 1
                if ident not in self._doublons_dits:
                    self._doublons_dits.add(ident)
                    print("[agent] \U0001f534 `%s` : DEUX familles pour la meme sonde "
                          "(`%s` et `%s`) — \u26d4 valeur REFUSEE, le fil ne tranche pas "
                          "un conflit d'unite au hasard." % (ident, precedent[0],
                                                             m.group(1)),
                          file=sys.stderr)
                continue
            if precedent is not None and precedent[0] is None:
                continue                      # cle deja marquee conflictuelle
            table[ident] = (m.group(1), v)
        self.lignes_lues += lues
        self.lignes_illisibles += illisibles
        # 🔴 2e REVUE (2026-08-24) — `lues == 0` REPRODUISAIT LE DIAGNOSTIC QUE CE
        #    BLOC EXISTE POUR SUPPRIMER. Le compteur `lignes_illisibles` n'est arme
        #    que pour des lignes qui commencent DEJA par `lhm_` : un /metrics qui
        #    repond **200 avec un corps sans une seule ligne `lhm_`** (corps vide,
        #    page d'erreur, mauvais endpoint, ou PREFIXE DE FAMILLE RENOMME — la
        #    derive meme qu'on traque) donnait `lues = 0`, `illisibles = 0`,
        #    `table = {}` ⇒ les cinq sondes tombaient dans `absences` ⇒ le bilan
        #    imprimait « LHM a REPONDU, sans cette valeur » et envoyait l'operateur
        #    inspecter SES CAPTEURS. Mot pour mot le diagnostic contraire.
        # ⇒ C'est une PANNE DE SOURCE, pas une absence : on LEVE, et `_tenter()`
        #   la compte et la nomme UNE fois. ⛔ Une reponse 200 qui ne porte aucune
        #   donnee du domaine attendu n'est pas une reponse.
        if lues == 0:
            raise IOError(
                "/metrics a repondu 200 mais ne porte AUCUNE ligne `lhm_` "
                "(%d ligne(s) recues) — \u26d4 CE N'EST PAS une absence de capteur : "
                "mauvais endpoint, corps vide, ou prefixe de famille renomme."
                % len(txt.splitlines()))
        if illisibles and not self._illisibles_dit:
            self._illisibles_dit = True
            print("[agent] \u26a0\ufe0f %d ligne(s) `lhm_` sur %d ILLISIBLES par le parseur "
                  "— \u26d4 CE N'EST PAS une absence de capteur, c'est un desaccord de "
                  "FORMAT. Regarder /metrics, \u26d4 pas les sondes." % (illisibles, lues),
                  file=sys.stderr)

        vues = {}
        for cle, ident, famille_attendue, _prov in LHM_SONDES:
            trouve = table.get(ident)
            v = None
            if trouve is not None:
                famille, v = trouve
                # 🎯 LA VERIFICATION QUI FAIT TENIR LE CHOIX DE `/metrics`.
                #    L'unite vit dans le nom de famille : si LHM renomme
                #    `..._celsius` en `..._fahrenheit` (ou `..._rpm` en
                #    `..._percent`), la valeur est REFUSEE et l'ecart est COMPTE
                #    ET NOMME. ⛔ Jamais publiee sous l'ancienne etiquette.
                if famille != famille_attendue:
                    # 🔴 2e REVUE (2026-08-24) : SON PROPRE SEAU. C'etait
                    #    `absences[cle + ":famille_inattendue"]`, donc imprime au
                    #    bilan sous « ABSENCES LHM (LHM a REPONDU, SANS cette
                    #    valeur) » — faux : LHM A RENDU la valeur, sous une AUTRE
                    #    unite. Le message dedie ne sort qu'UNE fois sur stderr ;
                    #    le bilan, lui, est l'artefact DURABLE, et il envoyait
                    #    inspecter un capteur parfaitement sain.
                    # ⚠️ Le meme delta creait `Collecteur.non_publiees` pour le 3e
                    #    etat en invoquant « chaque cas sur SON compteur », et
                    #    rangeait le 4e dans `absences` par suffixe de cle.
                    self.familles[cle] = self.familles.get(cle, 0) + 1
                    k = cle
                    if k not in self._familles_dites:
                        self._familles_dites.add(k)
                        print("[agent] \U0001f534 `%s` : famille `%s` au lieu de `%s` — "
                              "L'UNITE A CHANGE. Valeur REFUSEE, \u26d4 pas republiee "
                              "sous l'ancienne etiquette." % (cle, famille,
                                                              famille_attendue),
                              file=sys.stderr)
                    v = None
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
            elif trouve is None:
                # ⚠️ SEULE UNE VRAIE ABSENCE compte ici. Une valeur refusee pour
                #    famille inattendue a DEJA son compteur : la compter deux fois
                #    ferait lire « le capteur n'a rien rendu » sur un capteur qui a
                #    parfaitement rendu, sous une unite qui a change.
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
           timeout de `LHM_TIMEOUT_S` (0,60 s) au milieu du premier cycle
           d'apres-veille.
        ⚠️ Ce texte disait « 0,4 s » : valeur MORTE depuis que la mesure a porte
           le plafond a 0,60 s. Corrige en revue (dn4-8, 2026-08-21) — c'est la
           classe de defaut qu'AC10 existe pour fermer.
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
        # 🔴 SEAU DEDIE (revue dn4-8, 2026-08-21) : « une grandeur LHM a ete LUE
        #    mais N'A PAS ETE PUBLIEE parce que la position 0 de sa metrique
        #    manquait ». ⛔ Ce n'est NI un ecretage (la valeur n'est pas deformee),
        #    NI une absence LHM (LHM l'a bien rendue), NI une panne de source.
        #    Les melanger enverrait chercher au mauvais endroit — la doctrine du
        #    depot est « chaque cas sur SON compteur ».
        self.non_publiees = {}
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
        #    timeout de `LHM_TIMEOUT_S` (0,60 s) au milieu du premier cycle
        #    d'après-veille. (« 0,4 s » ici était une valeur MORTE — revue 2026-08-21)
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
            # 🔴 CE MESSAGE DISAIT « cette metrique n'est plus emise, sa case dira
            #    « -- » ». C'EST LE CONTRAIRE DE CE QUE LA STORY A ACHETE, et il a
            #    reellement ete imprime sur la tour pendant AC8 (revue dn4-8,
            #    2026-08-21). La regle W10 est POSITIONNELLE : une grandeur absente
            #    en position INTERNE devient un CHAMP VIDE et la metrique CONTINUE
            #    d'etre emise — c'est exactement pourquoi le `Mo/s` garde la
            #    position 0 et pourquoi aucune grandeur LHM n'y est admise.
            # ⛔ `_panne()` ne connait pas la position de la grandeur perdue : elle
            #    ne doit donc AFFIRMER NI L'UN NI L'AUTRE, et dire la regle.
            # ⚠️ Famille dn4-7 : « une cause plausible imprimee par le produit qui
            #    tourne ». Un message qui contredit le comportement reel envoie
            #    chercher une panne d'affichage la ou il n'y a qu'un champ vide.
            print(f"[agent] ⚠️ source `{nom}` en ECHEC ({message}) — la ou elle "
                  f"remplissait une grandeur, le fil porte un CHAMP VIDE et la "
                  f"ligne dit « -- » ; SI elle tenait la position 0, c'est la "
                  f"metrique entiere qui n'est pas emise. Les autres continuent : "
                  f"une source morte meurt SEULE.", file=sys.stderr)
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
        #    extrémité** : un tir à 600 ms (`LHM_TIMEOUT_S`) sur un cycle nominal
        #    à 16 ms rendrait un Δt sous-estimé de 0,58 s, donc **un débit disque
        #    surestimé de ~58 %** — un chiffre FRAIS ET FAUX, la famille exacte que
        #    la resynchronisation de dn2-2 existe pour empêcher.
        # ⚠️ CE CALCUL DISAIT « 400 ms ⇒ 0,38 s ⇒ ~38 % » : il était DÉRIVÉ d'un
        #    plafond mort. Recalculé en revue (dn4-8, 2026-08-21) sur la valeur
        #    réelle — et le chiffre corrigé est PIRE, ce qui renforce l'argument.
        # ✅ PLACÉE AVANT `t`, sa latence est hors fenêtre DES DEUX CÔTÉS (elle
        #    décale `t` et les compteurs du même montant) et s'annule.
        # ⚠️ `_tenter` : un LHM injoignable est une panne COMPTÉE ET NOMMÉE, une
        #    seule fois par type. ⛔ Et elle n'emporte AUCUNE autre grandeur : les
        #    valeurs LHM sont toutes en positions INTERNES.
        lhm = self._tenter("lhm", self.lhm.lire)
        # 🔴 2e REVUE (2026-08-24) — `if lhm:` ETAIT VRAI MEME QUAND LES CINQ
        #    VALEURS SONT `None`, ET LE BILAN EN TIRAIT UNE AFFIRMATION FAUSSE.
        #    `SourceLhm.lire()` rend TOUJOURS un dict de cinq cles ; `_tenter()`
        #    ne traite en panne qu'un **tuple** entierement `None`
        #    (`isinstance(valeur, tuple)`), ⛔ pas un dict. Donc sur une tour ou
        #    LHM tourne SANS elevation ou sans PawnIO — pas de Super I/O, les
        #    quatre `/lpc/nct6792d/0/fan/N` absentes de /metrics — le seau
        #    `non_publiees` se remplissait quand meme, et le bilan imprimait
        #    « ⛔ ce n'est PAS une absence LHM, LHM les a rendues » DIX LIGNES
        #    au-dessus du bloc ABSENCES qui disait correctement l'inverse.
        #    Deux diagnostics contraires dans la meme sortie, et le neuf est le faux.
        # ⇒ LE PREDICAT PORTE SUR CE QUI A REELLEMENT ETE RENDU, ⛔ pas sur le fait
        #   que LHM ait repondu. Par METRIQUE, parce que « non publiee » n'a de sens
        #   que pour les grandeurs que CETTE metrique aurait portees.
        _lhm_rendu = (lambda *cles: bool(lhm) and any(
            lhm.get(c) is not None for c in cles))
        lhm_disk = _lhm_rendu("fan.top_out", "fan.rear_out", "fan.cpu_noctua",
                              "fan.case_group")

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
        #
        # 🔴 CE QUE CETTE STRUCTURE COÛTE, ET C'EST UNE DÉCISION OWNER DU
        #    2026-08-21 (revue de code dn4-8) : **LES TROIS `tr/min` SONT OTAGES
        #    DE `psutil.disk_io_counters()`.** Ils sont calculés DANS le `else:`
        #    ci-dessous, donc trois chemins les font taire alors qu'ils n'ont RIEN
        #    à voir avec le disque :
        #      · `d1 is None` — un retour `None` DOCUMENTÉ de psutil ;
        #      · un recul de compteur cumulé (disque retiré, reset de pilote) ;
        #      · le premier cycle après chaque `reamorcer()` (`_d0 is None`).
        # ⛔ CE N'EST PAS UN OUBLI, ET ON NE LE CORRIGE PAS : la règle « aucune
        #    grandeur LHM en position 0 » INTERDIT de publier `disk` sans son
        #    `Mo/s`. Publier les ventilos quand le débit manque violerait
        #    exactement la propriété qu'AC5 a achetée. Le prix est donc assumé.
        # ⚠️ LA STORY ARGUMENTE LE SENS INVERSE (« la mort de LHM ne doit pas
        #    emporter le Mo/s ») et jamais celui-ci. Il est écrit ici pour que
        #    personne ne le redécouvre en pensant avoir trouvé un bug.
        # 🎯 CE QUI CHANGE : l'événement est désormais COMPTÉ ET NOMMÉ. Il était
        #    SILENCIEUX, et le bilan pouvait imprimer « aucune absence LHM : les
        #    cinq sondes ont rendu une valeur » pendant que trois ventilateurs
        #    n'étaient pas publiés — vrai sur LHM, trompeur sur l'écran.
        # ⛔ Même forme sur `cpu` : la °C est dans `if pct is not None:`, donc un
        #    échec de `cpu_percent()` emporte aussi la température. Même motif,
        #    même règle de position 0.
        d1 = self._tenter("disk", psutil.disk_io_counters)
        if d1 is None and lhm_disk:
            self.non_publiees["disk:source_morte"] = \
                self.non_publiees.get("disk:source_morte", 0) + 1
        if d1 is not None:
            dtd = max(t - self._dt0, 1e-6)
            if self._d0 is None:
                # ⚠️ Premier cycle (ou premier d'après-veille) : pas de delta, donc
                #    pas de `Mo/s`, donc pas de trame `disk` — donc PAS DE VENTILOS.
                #    Compté, ⛔ pas silencieux (décision owner, revue 2026-08-21).
                if lhm_disk:
                    self.non_publiees["disk:amorcage"] = \
                        self.non_publiees.get("disk:amorcage", 0) + 1
            elif (d1.read_bytes < self._d0.read_bytes or
                  d1.write_bytes < self._d0.write_bytes):
                # ⚠️ Idem `net:recul` — par `_panne()`, pour que le PREMIER
                #    événement soit dit sur stderr et pas seulement au bilan.
                self._panne("disk", "recul",
                            "un compteur cumule a RECULE (disque retire ? reset de "
                            "pilote ?) — rien n'est publie ce tour, ⛔ Y COMPRIS "
                            "LES TROIS tr/min qui voyagent dans cette metrique")
                if lhm_disk:
                    self.non_publiees["disk:recul"] = \
                        self.non_publiees.get("disk:recul", 0) + 1
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


class LecteurHorloge:
    """Lit l'état d'horloge de la carte SUR LE FIL — et ⛔ ne le DEVINE JAMAIS.

    🔴 TROIS ÉTATS, ⛔ PAS DEUX. L'ABSENCE D'INFORMATION N'EST PAS « TOUT VA
       BIEN » (AC3.2). `INCONNU` — rien lu, ou texte non reconnu — n'est traité
       ⛔ NI comme `OS0` (ce serait le mode de panne du capteur fantôme
       transposé : « il répond » n'est pas « il dit vrai »), ⛔ NI comme `OS1`
       (ce serait une boucle de pose sur une carte qui n'a peut-être pas
       d'horloge).

    ⚠️ IL TRAVAILLE SUR LES OCTETS, ET IL DÉCODE EN `replace` QUAND IL DOIT
       PARLER. La console imprime `🔴`, `⛔`, `é` (dn_console.c:7446-7452) :
       ⛔ un `.decode("ascii")` LÈVE. C'est le piège n°4 des Dev Notes.

    🔴 SON INVARIANT, ET IL EST TESTABLE (AC3.5) : la suite des lignes qu'il
       voit est EXACTEMENT celle du flux entier, **quelle que soit la position
       de la coupure** entre deux `read()`. Le témoin
       `tools/verif_decoupe_horloge_dn418.py` rejoue une capture RÉELLE coupée
       à CHAQUE position et compare.
    ⚠️ ⛔ IL N'AJOUTE AUCUN MARQUEUR À `_drainer()` — et c'est délibéré. Passer
       la queue du drain à `max(len) - 1` pour un marqueur plus long ferait
       tenir le marqueur COURT (`non-zero error code`, 19 o) entièrement dans
       la queue de 18 o, donc RECOMPTÉ au drain suivant : `refus_firmware`
       gonflé, sur le compteur même qui existe pour dire « le firmware a-t-il
       ACCEPTÉ ». Le piège se ferme en n'y entrant pas.
    """

    def __init__(self):
        self._tampon = b""
        # 🔴 L'ANCRE — LE VERDICT DU DRIVER POUR LA REPONSE EN COURS (correctif
        #    de revue 2026-08-26). Voir la source 4 : le bit `OS` imprime en
        #    clair vient de `dn_rtc_os()`, qui rend le dernier bit LU **sans
        #    controle de peremption** (dn_rtc.c:616). Il ne peut donc que
        #    CORROBORER ce que le driver a deja declare recevable — ⛔ jamais le
        #    contredire.
        self._ancre = None           # None | OS0 | OS1 | MUET | NON_ARMEE | INCONNU
        # ⚠️ UNE LIGNE TROP LONGUE NE COMPTE QU'UNE FOIS, quel que soit le
        #    nombre de `read()` sur lesquels elle s'etale (correctif de revue).
        self._en_troncature = False
        # ── ce que la carte a DIT ────────────────────────────────────────────
        self.etat = "INCONNU"        # INCONNU | OS0 | OS1 | MUET | NON_ARMEE
        self.etat_texte = None       # le littéral firmware, VERBATIM
        self.etat_instant = None     # time.monotonic() de la lecture
        self.etats_lus = 0
        # ── l'heure de la carte, pour AC6 (elle vient de la MÊME réponse) ────
        self.lue_texte = None
        self.lue_affichable = None   # ⛔ la carte declare-t-elle sa valeur RECEVABLE ?
        self.lue_naif = None         # secondes naïves (⛔ pas un epoch)
        self.lue_instant = None      # time.monotonic()
        self.lue_ecart_s = None      # carte − tour, en secondes
        # ⚠️ UN COMPTEUR, ⛔ PAS UN HORODATAGE. C'est lui qui permet à
        #    l'orchestrateur d'exiger une lecture PLUS RÉCENTE QUE SA DERNIÈRE
        #    POSE sans jamais mélanger deux horloges.
        self.heures_lues = 0
        # ── le verdict de la dernière pose (AC4.5) ───────────────────────────
        self.verdict = None          # None | ("OK", txt) | ("REFUS", motif)
        # ── santé de l'instrument lui-même ───────────────────────────────────
        self.lignes_vues = 0
        self.lignes_tronquees = 0
        # ⚠️ Le fil s'est rompu : le fragment de ligne en cours est JETE, ⛔ pas
        #    recolle au premier octet du flux suivant. Publie au bilan.
        self.ruptures = 0

    # ------------------------------------------------------------------ flux
    def alimenter(self, octets: bytes) -> None:
        """Consomme un morceau de flux. ⛔ Ne suppose AUCUNE frontière de ligne."""
        self._tampon += octets
        while True:
            i = self._tampon.find(b"\n")
            if i < 0:
                break
            ligne, self._tampon = self._tampon[:i], self._tampon[i + 1:]
            self.lignes_vues += 1
            # ⚠️ La ligne trop longue est FINIE : le prochain depassement sera
            #    une AUTRE ligne (correctif de revue 2026-08-26).
            self._en_troncature = False
            # ⚠️ CRLF MESURÉ SUR LE FLUX RÉEL (471/471) — ⛔ pas supposé.
            self._ligne(ligne.rstrip(b"\r"))
        if len(self._tampon) > DN_H_LIGNE_MAX and not self._en_troncature:
            # ⛔ BORNÉ. On garde la QUEUE : c'est là que se trouvent l'état et
            #    l'heure sur les lignes qui nous intéressent (elles finissent
            #    par eux). ⚠️ Et une troncature ne sort JAMAIS en silence : le
            #    bilan la publie.
            self._tampon = self._tampon[-DN_H_LIGNE_MAX:]
            self.lignes_tronquees += 1
            # 🔴 UNE FOIS PAR LIGNE, ⛔ PAS UNE FOIS PAR `read()`. Le compteur
            #    s'incrementait a CHAQUE appel en depassement : une seule ligne
            #    de 1 200 o arrivee 5 o a la fois en comptait ~176, et le bilan
            #    les annoncait comme « N ligne(s) TRONQUEE(S) ». Un compteur
            #    doit compter ce que sa phrase dit qu'il compte.
            self._en_troncature = True
        elif len(self._tampon) > DN_H_LIGNE_MAX:
            self._tampon = self._tampon[-DN_H_LIGNE_MAX:]

    # ----------------------------------------------------------------- ligne
    def _ligne(self, ligne: bytes) -> None:
        self._etat_depuis(ligne)
        self._heure_depuis(ligne)
        self._verdict_depuis(ligne)

    def _poser_etat(self, brut: bytes) -> None:
        """⛔ COMPARAISON À L'IDENTIQUE, JAMAIS EN SOUS-CHAÎNE.

        C'est ce qui ferme les deux pièges mesurés : « N'EST PAS FIABLE » ne
        peut pas se lire `FIABLE`, et `FIABLE` ne peut pas se lire à
        l'intérieur de `NON FIABLE (OS=1)`.
        """
        etat = DN_H_ETATS.get(brut.strip())
        if etat is None:
            # ⛔ TEXTE NON RECONNU ⇒ ON NE CHANGE RIEN — mais l'ancre RETIENT
            #    qu'une source ancree a parle sans etre comprise. Sinon la
            #    source 4 comblerait le trou avec un bit non peremptionne, et
            #    un libelle firmware retouche redeviendrait INVISIBLE : c'est
            #    exactement le mode de panne que la gate miroir existe pour
            #    fermer, et il ne doit pas se rouvrir par en dessous.
            self._ancre = "INCONNU"
            return
        # 🔴 CETTE METHODE N'EST APPELEE QUE PAR LES SOURCES ANCREES (1, 2, 3).
        #    La source 4 la contourne — c'est precisement pourquoi l'ancre est
        #    posee ICI et lue LA-BAS.
        self._ancre = etat
        self.etat = etat
        self.etat_texte = brut.strip().decode("utf-8", "replace")
        self.etat_instant = time.monotonic()
        self.etats_lus += 1

    def _etat_depuis(self, ligne: bytes) -> None:
        # Source 1 — la réponse de `rtc` : « horloge PCF85063A @ 0x51 : ÉTAT »
        i = ligne.find(DN_H_ANCRE_RTC)
        if i >= 0:
            j = ligne.find(b" : ", i)
            if j >= 0:
                self._poser_etat(ligne[j + 3:])
                return
        # Source 2 — le bandeau de boot : « … · horloge ÉTAT » (l'état est en
        # FIN de ligne ; on prend la DERNIÈRE ancre, le bandeau en porte deux).
        i = ligne.rfind(DN_H_ANCRE_BARRE)
        if i >= 0:
            self._poser_etat(ligne[i + len(DN_H_ANCRE_BARRE):])
            return
        # Source 3 — la confirmation de pose : « heure posee : … — etat ÉTAT ».
        # 🔴 ELLE EST ICI, ⛔ PAS DANS `_verdict_depuis`, ET C'EST UN DÉFAUT
        #    ATTRAPÉ PAR L'ÉPREUVE FONCTIONNELLE (scène 1, 2026-08-26) : la
        #    fenêtre de verdict se ferme sur la PREMIÈRE ligne qui dit
        #    « heure posee », et cette première ligne est un `ESP_LOGI` de
        #    `dn_rtc` qui ne porte PAS l'état. Couplées, l'état de la ligne
        #    SUIVANTE — celle de la console, qui le porte — n'était JAMAIS lu :
        #    l'agent restait à `OS1` après une pose RÉUSSIE, et reposait
        #    l'heure une seconde fois. ⇒ les deux lectures sont INDÉPENDANTES.
        i = ligne.find(DN_H_POSE_OK)
        if i >= 0:
            j = ligne.find(DN_H_POSE_ETAT, i)
            if j >= 0:
                self._poser_etat(ligne[j + len(DN_H_POSE_ETAT):])
                return
        # Source 4 — le bit lui-même : « bit OS     : 0|1 — … »
        # 🔴 CORRECTIF DE REVUE 2026-08-26 — ⛔ ELLE NE PEUT PLUS ECRASER LE
        #    VERDICT ANCRE DE LA MEME REPONSE, ET LE FIRMWARE DIT POURQUOI.
        #    `dn_rtc_etat()` fait un controle de PEREMPTION avant de regarder
        #    `OS`, et son commentaire (dn_rtc.c:470) est explicite : « l'ordre
        #    compte : la peremption d'abord, OS ensuite. UNE PUCE MUETTE DONT
        #    LA DERNIERE LECTURE DISAIT OS=0 NE DOIT PAS PASSER POUR FIABLE ».
        #    Mais `dn_rtc_os()` (dn_rtc.c:616), qui alimente CETTE ligne, rend
        #    le bit CACHE **sans aucun controle de peremption**.
        # ⇒ traiter les lignes independamment, la derniere gagnant, INVERSAIT
        #   cet invariant cote agent :
        #     · `MUETTE`    devenait `OS0` — « tout va bien » sur une puce morte,
        #       et l'ecart d'AC6 se mesurait alors sur une valeur GELEE, qui
        #       derive de 1 s/s ⇒ pose parasite au bout du seuil ;
        #     · `JAMAIS LUE` devenait `OS1` (`s_os = true` au boot, dn_rtc.c:31).
        #   Les deux sont nommement interdits par AC3.2 : « il repond » n'est
        #   pas « il dit vrai », et l'absence d'information n'est ni l'un ni
        #   l'autre. ⇒ LE BIT NE PEUT QUE CORROBORER UN VERDICT DEJA RECEVABLE.
        i = ligne.find(DN_H_ANCRE_OS)
        if i >= 0:
            if self._ancre not in (None, "OS0", "OS1"):
                return           # ⛔ MUET / NON_ARMEE / INCONNU : on GARDE l'ancre
            c = ligne[i + len(DN_H_ANCRE_OS):i + len(DN_H_ANCRE_OS) + 1]
            if c == b"1":
                self.etat, self.etat_texte = "OS1", "bit OS = 1"
                self.etat_instant = time.monotonic()
                self.etats_lus += 1
            elif c == b"0":
                self.etat, self.etat_texte = "OS0", "bit OS = 0"
                self.etat_instant = time.monotonic()
                self.etats_lus += 1

    def _heure_depuis(self, ligne: bytes) -> None:
        """AC6.2 — l'heure de la carte arrive DANS LA MÊME RÉPONSE que le bit OS.

        ⇒ la comparer à l'heure de la tour ne coûte **rien de plus** que ce que
          l'agent lit déjà. C'est tout le mécanisme d'AC6.
        """
        # 🔴 UNIQUEMENT LA LIGNE `lue` — ⛔ JAMAIS LA CONFIRMATION DE POSE, ET
        #    C'EST UN DÉFAUT ATTRAPÉ PAR L'ÉPREUVE FONCTIONNELLE (2026-08-26).
        #    La ligne « heure posee : … » rend l'heure QUE L'AGENT VIENT
        #    D'ÉCRIRE : la comparer à l'horloge de la tour donnerait un écart
        #    ~0 PAR CONSTRUCTION. C'est l'instrument qui récite sa propre
        #    écriture — il masquerait exactement ce qu'AC6 existe pour voir.
        #    ⇒ l'écart ne se mesure que sur ce que la CARTE a LU dans sa puce.
        i = ligne.find(DN_H_ANCRE_LUE)
        if i < 0:
            return
        i += len(DN_H_ANCRE_LUE)
        brut = ligne[i:i + 19]
        try:
            txt = brut.decode("ascii")
            a, mo, j = (int(x) for x in txt[0:10].split("-"))
            h, mi, s = (int(x) for x in txt[11:19].split(":"))
        except Exception:
            return               # ⛔ non lisible ⇒ on ne change RIEN
        t = time.time()
        lt = time.localtime(t)
        self.lue_texte = txt
        # 🔴 LA VALEUR ET SA RECEVABILITE SONT PRISES ENSEMBLE (correctif de
        #    revue 2026-08-26). Le firmware les imprime sur la MEME ligne, et
        #    exprès. En jetant le suffixe, l'agent comparait a l'horloge de la
        #    tour une heure que la carte declarait elle-meme NON AFFICHABLE.
        self.lue_affichable = DN_H_NON_AFFICHABLE not in ligne
        self.heures_lues += 1
        self.lue_naif = _secondes_naives(a, mo, j, h, mi, s)
        self.lue_instant = time.monotonic()
        # ⛔ DEUX PENDULES, COMPARÉES EN CALENDRIER NAÏF (voir `_jours_civils`).
        self.lue_ecart_s = self.lue_naif - _secondes_naives(
            lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec)

    def _verdict_depuis(self, ligne: bytes) -> None:
        """AC4.5 — la pose est vérifiée PAR LA RÉPONSE DE LA CARTE.

        ⛔ Pas par le fait d'avoir écrit : `dn_rtc_poser()` RELIT et COMPARE les
           sept registres, et la console rend le verdict. « n trames émises » ne
           prouve pas n acceptations.
        ⚠️ Le succès est annoncé DEUX fois (un `ESP_LOGI` de `dn_rtc`, puis la
           ligne de la console). Le premier qui arrive ferme la fenêtre ; le
           second ne peut donc pas compter une seconde pose.
        """
        if self.verdict is not None:
            return               # fenêtre déjà close
        if DN_H_POSE_OK in ligne:
            self.verdict = ("OK", ligne.decode("utf-8", "replace").strip())
            # ⛔ ET RIEN DE PLUS ICI. L'état résultant est lu par
            #    `_etat_depuis`, qui tourne sur TOUTES les lignes — voir le
            #    défaut nommé là-bas.
            return
        for motif in DN_H_POSE_REFUS:
            if motif in ligne:
                self.verdict = ("REFUS", motif.decode("ascii"))
                return

    def rupture(self) -> None:
        """Le fil s'est rompu (fermeture / reouverture du port).

        🔴 CORRECTIF DE REVUE 2026-08-26, ET LE DEBRANCHEMENT EST LE SUJET MEME
           D'AC7. `LecteurHorloge` vit sur `SortieSerie`, ⛔ pas sur la
           connexion : il SURVIVAIT donc a la fermeture avec, dans son tampon,
           le fragment de la ligne coupee en vol. Au rebranchement ce fragment
           etait RECOLLE au premier octet du nouveau flux, fabriquant une ligne
           que ni le firmware ni la capture n'ont jamais emise.
        ⚠️ L'ancre et la fenetre de verdict tombent avec lui : ils decrivaient
           une reponse dont la fin n'arrivera jamais.
        """
        if self._tampon or self._ancre is not None:
            self.ruptures += 1
        self._tampon = b""
        self._en_troncature = False
        self._ancre = None
        self.verdict = None

    def armer_verdict(self) -> None:
        """Ouvre une fenêtre d'attente de verdict (appelé JUSTE avant `rtc set`)."""
        self.verdict = None


class SortieStdout:
    nom = "stdout"
    # ⛔ PAS DE FIL ICI, ET C'EST UN ÉTAT DÉCLARÉ (AC2.4) — ⛔ jamais un
    #    `AttributeError`, jamais un silence.
    canal_console = False
    # 🔴 dn4-5/AC4.3 (correctif de revue 2026-08-28) — `ouvertures` EST DESORMAIS
    #    UN CONTRAT DE TOUS LES TRANSPORTS. Il n'existait que sur `SortieSerie`,
    #    et l'appelant faisait `getattr(sortie, "ouvertures", 0)` : sur `--ws` et
    #    sur stdout, le defaut `0` figeait la generation ⇒ `Lisseur.vider()`
    #    n'etait PLUS JAMAIS appele apres le premier cycle. La garde d'AC4.3
    #    etait donc SPECIFIQUE AU SERIE alors que le lissage, lui, est GLOBAL
    #    (« UN SEUL lisseur, quel que soit le transport »).
    #    ⛔ stdout n'a pas de connexion : le compteur reste a 0 par NATURE, ⛔ pas
    #      par absence d'attribut — et c'est ecrit.
    ouvertures = 0

    def envoyer(self, ligne: str) -> None:
        # ⚠️ BrokenPipeError est une SOUS-CLASSE d'Exception : redirigé vers un
        # consommateur qui se ferme (`| head`, un pipe coupé), l'agent tournait en
        # imprimant une erreur PAR SECONDE au lieu de sortir. On la distingue.
        sys.stdout.write(ligne)
        sys.stdout.flush()

    def fermer(self) -> None:
        pass


class Lisseur:
    """dn4-5 / T4 — LE LISSAGE D'AFFICHAGE. ⛔ PAS le lissage de bruit de capteur.

    ⚠️ ⛔ NE PAS LE CONFONDRE AVEC L'IIR DE `dn_capteurs.c`. Celui-là lisse le
       BRUIT DE CONVERSION d'un capteur, sur 3 échantillons, et il est
       explicitement déclaré « ce n'est PAS le lissage du brief ». Celui-ci est
       la **moyenne d'affichage** que le critère n°2 du brief demande :
       « des valeurs vivantes ET LISSÉES ».

    ═══ POURQUOI CÔTÉ AGENT, ET PAS CÔTÉ FIRMWARE ═══════════════════════════

    🔴 **AC4.3 TRANCHE, ET C'EST UNE CONTRAINTE, PAS UNE PRÉFÉRENCE.** « Aucune
       valeur lissée ne doit survivre à la péremption de 3 s, sinon AC7 de
       `dn2-2` tombe. »
         · **Côté agent** : l'agent coupé, plus aucune trame n'arrive, et la
           péremption du firmware tire **exactement comme avant** — le firmware
           n'est pas touché, donc le délai est IDENTIQUE PAR CONSTRUCTION.
         · **Côté firmware** : il faudrait vider l'état du filtre à la
           péremption **ET** à la reprise, **par grandeur** (règle W10 :
           `connue[]` est PAR GRANDEUR), dans le module même dont AC7 est la
           contrainte non négociable. Plus d'endroits où se tromper, sur le seul
           code qu'on n'a pas le droit de casser.
    ⚠️ **ET LA RAM NE DÉPARTAGE PAS** : 4 grandeurs x 3 échantillons x 4 o = 48 o
       côté carte. ⛔ Prétendre que la mesure de RAM a tranché serait faux — ce
       qui tranche est AC4.3.
    ⚠️ **CE QUE ÇA COÛTE, ET C'EST DIT** : le fil ne porte plus la valeur BRUTE
       des quatre grandeurs lissées. ⇒ pour l'A/B d'AC4.4, `--lissage off`
       rétablit le brut **sans reflasher**.

    ═══ LA FENÊTRE : n = 3, ET LA BORNE VIENT D'AC4.3 ═══════════════════════

    🔴 Une fenêtre de `n` échantillons à 1 Hz porte un échantillon vieux de
       `(n-1)` s. Exiger qu'**aucun échantillon du filtre ne soit plus vieux que
       la péremption** (`DN_LINK_PEREMPTION_US` = 3 s) donne `n - 1 < 3`, soit
       **n <= 3**. ⛔ Ce n'est pas un réglage de goût.
    ⚠️ **CETTE DÉRIVATION EST VRAIE À 1 Hz EXACT, ET LA BOUCLE N'OFFRE PAS ÇA**
       (revue du 2026-08-28) : elle ne resynchronise qu'**au-delà de 1,0 s de
       retard**, donc elle tolère un intervalle de **2,0 s** ⇒ la fenêtre peut
       couvrir **3,0 s**, soit exactement la péremption. **La marge était NULLE.**
       ⇒ `n = 3` reste la borne de COMPTE, mais ce qui garantit AC4.3 est
       désormais `AGE_MAX_S` — voir ci-dessous. ⛔ Ne plus lire `n <= 3` comme
       la preuve d'AC4.3 : c'est une condition nécessaire, ⛔ pas suffisante.
    ✅ **VÉRIFIÉ SUR LES 960 ÉCHANTILLONS** (`mesures/dn4-5/T4-choix-fenetre.txt`) :
       la seule grandeur qui ÉCHOUAIT au critère, `CPU GHz`, passe de **100 %**
       à **35 %** de sa plage (seuil 40 %), pour **1,0 s** de retard ajouté.

    ⚠️ **LES QUATRE GRANDEURS LISSÉES SONT TOUTES `DN_PREC_DIXIEME`**, et c'est
       ce qui rend la moyenne honnête : on moyenne EN DIXIÈMES, c'est-à-dire
       **à la résolution que l'écran affiche**. Une grandeur `DN_PREC_ENTIER`
       exigerait un arrondi différent — une gate refuse qu'on en ajoute une ici.
    """

    FENETRE = 3

    # ── 🔴 LA BORNE D'AGE — CORRECTIF DE REVUE DU 2026-08-28 ────────────────
    #    AC4.3 dit « aucune valeur lissee ne doit survivre a la peremption de
    #    3 s ». La derivation `n - 1 < 3` ci-dessus SUPPOSE UNE CADENCE DE 1 Hz
    #    SANS GIGUE — et la revue a montre que la boucle n'en offre pas :
    #    elle ne resynchronise QU'AU-DELA de 1,0 s de retard, donc elle tolere
    #    SANS RIEN DIRE un intervalle inter-echantillons de 2,0 s. Avec n = 3 la
    #    fenetre peut alors couvrir 1,0 + 2,0 = 3,0 s, soit EXACTEMENT
    #    `DN_LINK_PEREMPTION_US`. La marge annoncee etait NULLE.
    #    ⚠️ PIRE : le chemin de resynchronisation (`rattrapages` -> `reamorcer()`
    #    -> `continue`) ne vidait PAS le lisseur — `vider()` n'etait declenche
    #    que par une REOUVERTURE DU PORT. Un decrochage qui laisse le port
    #    ouvert (un `gel` de la carte, un TDR du pilote GPU, une famine
    #    d'ordonnancement) republiait donc, a la premiere trame de reprise,
    #    une moyenne dont DEUX TIERS dataient d'AVANT la peremption.
    # ⇒ ON NE COMPTE PLUS LES ECHANTILLONS, ON BORNE LEUR AGE. Chaque
    #   echantillon porte son heure ; tout echantillon d'age >= AGE_MAX_S sort
    #   de la fenetre. L'AC devient vraie PAR CONSTRUCTION, quelle que soit la
    #   gigue et quel que soit le chemin de rupture — ⛔ plus par enumeration
    #   des chemins, qui laissait passer ceux qu'on n'avait pas nommes.
    # ⛔ MIROIR DU FIRMWARE : `DN_LINK_PEREMPTION_US` = 3 000 000 us
    #   (`firmware/desknode/main/dn_link.h`). Une gate verifie l'egalite.
    AGE_MAX_S = 3.0

    # ── LE JEU LISSÉ, ARRÊTÉ PAR LA DÉCISION OWNER DU 2026-08-26 (réponse (a) :
    #    « le critère écrit fait foi ») ────────────────────────────────────────
    #    `CPU GHz` · `RÉSEAU bas` · `RÉSEAU haut` · `DISQUE Mo/s`
    #    ⛔ `CPU %` N'EN EST PAS : §13.7 le classe « À DISCUTER » depuis dn4-1
    #      (« un CPU lissé ment sur les pics ») et AC4.4 le tranche À L'ŒIL.
    LISSEES = {("cpu", 1), ("net", 0), ("net", 1), ("disk", 0)}

    def __init__(self, fenetre: int = FENETRE, actif: bool = True):
        self.fenetre = fenetre
        self.actif = actif
        self._buf = {}
        self._generation = None

    def vider(self) -> None:
        """⛔ TOUT l'état part. Appelé à chaque reprise de liaison.

        ⚠️ Ce vidage reste la garde EXPLICITE de la réouverture de port ; il
           n'est plus la SEULE. La borne d'âge (`AGE_MAX_S`) couvre les ruptures
           qui ne ferment pas le port, et que cette méthode ne voyait pas.
        """
        self._buf.clear()

    def appliquer(self, photo, generation=0, maintenant=None):
        """Rend la photo, les quatre grandeurs lissées remplacées.

        🔴 LE VIDAGE À LA REPRISE EST LE PIÈGE NOMMÉ PAR AC4.3 : « un IIR qui
           garde son état ré-affiche une valeur d'AVANT la coupure dès la
           première trame de reprise ». On se cale sur un COMPTEUR D'OUVERTURES
           du port, ⛔ pas sur `reprise_liaison` — ce drapeau-là est CONSOMMÉ par
           le reposeur d'horloge, et deux lecteurs d'un même drapeau se le
           volent.
        """
        if not self.actif:
            return photo
        # ⛔ `time.monotonic()` : l'horloge murale peut RECULER (NTP, changement
        #    d'heure), et un echantillon d'age NEGATIF ne sortirait jamais de la
        #    fenetre. L'injection par parametre existe pour les gates.
        if maintenant is None:
            maintenant = time.monotonic()
        if generation != self._generation:
            self._generation = generation
            self.vider()
        out = []
        for metrique, valeurs in photo:
            neuves = list(valeurs)
            for i, v in enumerate(neuves):
                if (metrique, i) not in self.LISSEES:
                    continue
                cle = (metrique, i)
                if v is None:
                    # ⚠️ UNE SOURCE ABSENTE EST UNE RUPTURE : elle vide la
                    #    fenêtre. Moyenner à cheval sur un trou fabriquerait une
                    #    valeur qui n'a jamais existé — même règle que les
                    #    `ruptures` de `dn_w2_t` (dn3-3).
                    self._buf.pop(cle, None)
                    continue
                b = self._buf.setdefault(cle, [])
                b.append((maintenant, v))
                # 🔴 LA BORNE D'AGE PASSE AVANT LA BORNE DE COMPTE. Tout
                #    echantillon dont l'age ATTEINT la peremption sort — donc
                #    l'echantillon le plus vieux de la fenetre est TOUJOURS
                #    strictement plus jeune que `DN_LINK_PEREMPTION_US`.
                #    C'est l'enonce d'AC4.3, verifie ici a chaque trame.
                limite = maintenant - self.AGE_MAX_S
                while b and b[0][0] <= limite:
                    b.pop(0)
                if len(b) > self.fenetre:
                    del b[:len(b) - self.fenetre]
                # Les valeurs sont des DIXIÈMES ENTIERS, et les quatre grandeurs
                # lissées sont toutes DN_PREC_DIXIEME : moyenner ici, c'est
                # moyenner À LA RÉSOLUTION AFFICHÉE.
                neuves[i] = int(sum(x[1] for x in b) / len(b) + 0.5)
            out.append((metrique, neuves))
        return out


class JournalSoak:
    """dn4-5 / AC2.5 — LA BOITE NOIRE DU SOAK, CÔTÉ TOUR.

    🔴 POURQUOI CE CANAL EXISTE À CÔTÉ DE `--tracer-console`, ET NE LE REMPLACE
       PAS. `--tracer-console` capture TOUT le fil, brut : le dépôt chiffre
       lui-même son débit à **447-530 o/s**, soit **270 à 320 Mo sur 7 jours,
       sans aucune rotation**, et il écrit « ⛔ Ne pas le laisser armé sur un
       soak ». Il reste l'instrument de diagnostic (dn4-18) ; il n'est pas
       l'instrument d'une semaine. ⚠️ Le cadrage de dn4-5 annonçait ~140 Mo :
       c'est le chiffre de §13.11.1 (232,0 o/s), que le code a déjà corrigé d'un
       facteur ~1,9 — vérifié le 2026-08-26 dans `dn_agent.py` lui-même.

    🎯 CE QUE CE JOURNAL GARDE, ET RIEN D'AUTRE :
       · le BATTEMENT (une ligne / 10 s) — c'est lui qui porte la triade
         `up`/`vsync`/`flush`, l'heure MURALE, et la raison du dernier reset ;
       · toute trace de REDÉMARRAGE (bandeau du bootloader `rst:0x…`) ;
       · toute trace de PANIQUE ou de WATCHDOG ;
       · les ÉVÉNEMENTS DE PORT de l'agent (ouverture, perte, fermeture), parce
         que « l'agent a perdu le port » et « la carte est haltée » se
         ressemblent trait pour trait, et qu'AC2.3 exige de les séparer.

    ⚠️ VOLUME BORNÉ **AVANT** DE LANCER, ⛔ pas constaté après : une ligne de
       battement toutes les 10 s pèse ~180 o ⇒ **~18 o/s, soit ~11 Mo sur
       7 jours** — deux ordres de grandeur sous la trace brute. Le plafond +
       rotation sont une CEINTURE, pas le mécanisme principal.
       ⛔ « Un instrument qui remplit le disque de la tour casse ce qu'il
       observe. »

    ⚠️ ET CE JOURNAL NE VOIT PAS TOUT, C'EST ÉCRIT ICI : il ne voit que ce que
       la carte ÉMET. Une carte haltée par `PANIC_PRINT_HALT` n'émet plus rien —
       elle se lit donc comme un SILENCE, ⛔ jamais comme un événement. C'est
       exactement pour ça que le battement est journalisé : son absence EST le
       signal.
    """

    # Un quota sur les lignes qui ne sont ni battement ni redémarrage : une
    # tempête d'erreurs ne doit pas noyer la boîte noire. ⛔ Les lignes écartées
    # sont COMPTÉES et DITES — un écrêtage silencieux est un mensonge.
    QUOTA_AUTRES_PAR_MIN = 60

    # 🔴 CE QUE LA CARTE A APPRIS AU JOURNAL, LE 2026-08-26 — ET C'ETAIT UN
    #    DEFAUT GRAVE POUR LE SOAK. Sur 120 s de regime reel, le journal a ecrit
    #    18 873 o (157 o/s, ⇒ ~95 Mo sur 7 j) la ou j'avais PREDIT 18,3 o/s a
    #    partir du battement seul — faux d'un facteur ~8,6. Et surtout : le
    #    quota a jete **437 lignes en deux minutes**.
    # ⛔ CE QUI SATURAIT LE QUOTA ETAIT L'AGENT LUI-MEME. Le REPL RENVOIE en
    #    echo chaque trame `pc $DN,...` qu'on lui envoie — cinq par seconde —
    #    entrelacees d'invites `desknode> `. C'est du bruit PUR pour une boite
    #    noire, et il ecrasait le quota.
    # 🔴 LA CONSEQUENCE ETAIT LA VRAIE FAUTE : une anomalie REELLE pouvait etre
    #    ECARTEE par le quota parce que l'echo l'avait sature. Un instrument qui
    #    jette le signal pour garder son propre bruit ne protege rien.
    # ⇒ ON FILTRE L'ECHO, ⛔ ON NE L'ECRETE PAS. Le quota reste, mais il ne
    #   garde plus que ce qui n'est pas nous.
    # ⚠️ ANCRE SUR `$DN,` N'IMPORTE OU DANS LA LIGNE, ⛔ PAS SUR UN DEBUT DE
    #    LIGNE — corrige le 2026-08-26, sur la carte. La version ancree ratait
    #    `desknode> desknode> c $DN,3,126,...` : la trame avait ete COUPEE entre
    #    deux `read()` et le `p` de `pc` etait parti dans l'autre morceau. Un
    #    filtre qui ne tient pas sur un fragment ne tient pas du tout : le fil
    #    en produit en permanence (le REPL entrelace ses invites au milieu des
    #    echos).
    RE_ECHO_AGENT = re.compile(rb"\$DN,\d")
    RE_INVITE_SEULE = re.compile(rb"^(desknode>\s*)+$")

    RE_BATTEMENT = re.compile(rb"desknode: up \d+ s")
    RE_REBOOT = re.compile(rb"rst:0x|boot: ESP-IDF|cpu_start:")
    RE_ALARME = re.compile(rb"Guru Meditation|Task watchdog|abort\(\)|"
                           rb"assert failed|Backtrace:|Brownout")

    def __init__(self, chemin: str, max_octets: int = 32 * 1024 * 1024,
                 rotations: int = 4):
        self._chemin = chemin
        self._max = max_octets
        self._rot = rotations
        self._f = None
        self._reste = b""
        # 🔴 CORRECTIF DE REVUE 2026-08-28 — `_ecrits` REPREND LA TAILLE DU
        #    FICHIER. Il etait remis a 0 a chaque construction alors que le
        #    fichier est ouvert en 'a' : le compteur etait PAR PROCESSUS, le
        #    fichier CUMULATIF. Chaque relance de l'agent (extinction/rallumage
        #    de la tour = la fin NORMALE de cet agent) repartait de zero sur un
        #    fichier existant ⇒ avec N relances par cycle, le fichier vivant
        #    atteignait N x max_octets, SANS AUCUNE BORNE EN N. L'aide de
        #    `--journal-max-mo` promettait « 160 Mo au pire » : c'etait faux des
        #    la premiere relance.
        try:
            self._ecrits = os.path.getsize(chemin)
        except Exception:
            self._ecrits = 0
        self._fenetre_min = -1
        self._autres = 0
        self._ecartees = 0
        self._echos = 0
        # 🔴 CE QUI MANQUAIT POUR QUE LA BOITE NOIRE DISE QU'ELLE EST CASSEE.
        self._echecs_ecriture = 0
        self._echecs_rotation = 0
        self._tronquees = 0
        self._rotations = 0

    # ── l'écriture, best-effort comme `_tracer` et POUR LA MÊME RAISON ──────
    def _ecrire(self, etiquette: str, texte: str) -> None:
        try:
            if self._f is None:
                # 'a' : on AJOUTE. Une reprise après interruption ne doit pas
                # écraser la fenêtre précédente — AC3.6 exige de PUBLIER ce
                # qu'on a, y compris les épisodes rompus.
                self._f = open(self._chemin, "a", encoding="utf-8")
            t = time.time()
            lt = time.localtime(t)
            ligne = ("%04d-%02d-%02d %02d:%02d:%02d.%03d  %-9s %s\n"
                     % (lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min,
                        lt.tm_sec, int((t % 1.0) * 1000), etiquette, texte))
            self._f.write(ligne)
            self._f.flush()
            # ⚠️ EN OCTETS, ⛔ pas en caracteres : les lignes portent `—`, `⛔`,
            #    `·`, `⚠️` (2 a 4 o chacun). Compter les caracteres faisait
            #    franchir le plafond au FICHIER avant le COMPTEUR.
            self._ecrits += len(ligne.encode("utf-8", "replace"))
            if self._ecrits >= self._max:
                self._rotationner()
        except Exception as exc:
            # ⛔ UN INSTRUMENT QUI CASSE CE QU'IL OBSERVE N'EST PAS UN
            #    INSTRUMENT. Même arbitrage que `SortieSerie._tracer`.
            # 🔴 MAIS CORRECTIF DE REVUE 2026-08-28 : `self._f` RESTE POSE et
            #    l'echec etait avale SANS TRACE ⇒ la boite noire devenait muette
            #    A VIE des le premier echec, et sur un disque plein l'enchainement
            #    etait pire : `_ecrits` n'etait plus incremente, donc
            #    `_ecrits >= _max` ne devenait jamais vrai, donc `_rotationner()`
            #    n'etait JAMAIS appele, donc `os.remove(<le plus vieux>)` — la
            #    seule ligne qui aurait rendu de la place — etait INATTEIGNABLE.
            #    Le disque plein VERROUILLAIT le mecanisme cense lui survivre.
            #    ⚠️ Et c'est le defaut exact que la validation d'option refuse au
            #    lancement (« une boite noire qu'on decouvre muette au jour 7 est
            #    une fenetre d'observation PERDUE ») : le code le construisait
            #    APRES le controle.
            self._echecs_ecriture += 1
            try:
                self._f.close()
            except Exception:
                pass
            self._f = None  # ⇒ une REOUVERTURE sera tentee au prochain appel
            if self._echecs_ecriture == 1:
                print("[agent] 🔴 JOURNAL DU SOAK — premiere ECHEC D'ECRITURE "
                      "sur %r (%s). La boite noire retentera d'ouvrir a chaque "
                      "ligne ; le compte final est publie au bilan."
                      % (self._chemin, exc), file=sys.stderr)

    def _rotationner(self) -> None:
        """🔴 CORRECTIF DE REVUE 2026-08-28 — `_ecrits` N'EST REMIS A ZERO QUE
        SI LA ROTATION A REUSSI.

        Il etait pose a 0 AVANT le `try:`. Sous Windows — la plateforme cible —
        `os.replace` leve `PermissionError` des qu'un antivirus, un editeur
        ouvert par l'operateur ou une indexation tient le fichier. L'exception
        etait avalee, le fichier vivant restait intact, MAIS le compteur etait
        deja a zero : `_ecrire()` le rouvrait en 'a' et il grossissait de
        `max_octets` de plus avant la tentative suivante, qui echouait pareil
        tant que le verrou tenait. Croissance NON BORNEE, et pas un mot.
        ⚠️ Et le dossier affirmait « L'ECRETAGE EST DIT, JAMAIS SILENCIEUX »
        alors que cette methode n'ecrivait RIEN et n'exposait AUCUN compteur.
        """
        try:
            self._f.close()
        except Exception:
            pass
        self._f = None
        try:
            plus_vieux = "%s.%d" % (self._chemin, self._rot)
            if os.path.exists(plus_vieux):
                os.remove(plus_vieux)
            for i in range(self._rot - 1, 0, -1):
                a, b = "%s.%d" % (self._chemin, i), "%s.%d" % (self._chemin, i + 1)
                if os.path.exists(a):
                    os.replace(a, b)
            if os.path.exists(self._chemin):
                os.replace(self._chemin, "%s.1" % self._chemin)
        except Exception as exc:
            # ⛔ L'ECHEC NE REMET PAS LE COMPTEUR A ZERO : le fichier vivant est
            #    toujours la, a sa taille reelle. On re-tentera au prochain
            #    franchissement, ⛔ pas apres `max_octets` de plus.
            self._echecs_rotation += 1
            if self._echecs_rotation == 1:
                print("[agent] 🔴 JOURNAL DU SOAK — ROTATION REFUSEE sur %r "
                      "(%s). Le fichier vivant N'EST PLUS BORNE tant que le "
                      "verrou tient (antivirus ? editeur ouvert ?)."
                      % (self._chemin, exc), file=sys.stderr)
            return
        # ✅ La rotation a REUSSI : le fichier vivant est neuf.
        self._ecrits = 0
        self._rotations += 1
        # ⛔ L'ECRETAGE EST DIT, ET IL L'EST DANS LE JOURNAL LUI-MEME : la
        #    premiere ligne du fichier neuf nomme ce qui vient d'etre pousse
        #    d'un cran, et combien de crans ont deja tourne.
        self._ecrire("ROTATION", "fichier plein (%d o) — rotation n°%d, le plus "
                                 "vieux des %d crans est DETRUIT. ⛔ Si le soak "
                                 "depasse %d crans, le DEBUT de la fenetre "
                                 "n'existe plus."
                     % (self._max, self._rotations, self._rot, self._rot))

    def evenement(self, etiquette: str, texte: str) -> None:
        """Un fait de l'AGENT (port ouvert/perdu/fermé, départ, arrêt).
        ⛔ Jamais soumis au quota : ce sont eux qui séparent « l'agent a perdu
        le port » de « la carte est haltée »."""
        self._ecrire(etiquette, texte)

    # ⛔ LE PLAFOND DU REPORT DE FRAGMENT — 512 o A L'ORIGINE, ET IL TRONQUAIT
    #    PAR LA TETE (`[-512:]`, on gardait la FIN). Or `RE_ALARME` ancre sur
    #    `Backtrace:`, `Guru Meditation`, `Brownout` : TOUS EN DEBUT DE LIGNE.
    #    Une ligne de panique plus longue que le plafond perdait donc son
    #    prefixe, etait retrogradee en ligne « fil », passait sous le quota de
    #    60/min et pouvait etre ECARTEE — sur une carte ou
    #    `COREDUMP_ENABLE_TO_NONE=y` fait de cette ligne LE SEUL post-mortem.
    #    ⇒ On garde la TETE, et le plafond passe a 4 ko pour qu'un backtrace
    #      entier tienne. Toute troncature est COMPTEE et publiee au bilan.
    MAX_FRAGMENT = 4096

    def rincer(self) -> None:
        """🔴 LE RECAP DE MINUTE EST PILOTE PAR LE TEMPS, ⛔ PLUS PAR L'ARRIVEE
        D'OCTETS (correctif de revue 2026-08-28).

        Il n'etait ecrit qu'a la bascule de minute SUIVANTE, elle-meme declenchee
        par un appel a `alimenter()` AVEC des octets — or `_drainer()` n'appelle
        `alimenter()` que `if retour:`. Consequence : carte haltee
        (`PANIC_PRINT_HALT=y`) ou debranchee ⇒ plus un octet ⇒ le decompte des
        lignes jetees par le quota pour la minute EN COURS n'etait JAMAIS publie.
        C'est-a-dire LA MINUTE DE L'INCIDENT — la seule qu'on relira. Le journal
        promet « ⛔ rien n'est jete en silence » : il rompait cette promesse
        exactement la ou elle compte.
        """
        minute = int(time.time() // 60)
        if minute == self._fenetre_min:
            return
        if self._ecartees or self._echos:
            self._ecrire("MINUTE", "%d ligne(s) ECARTEE(S) par le quota "
                                   "(plafond %d) · %d echo(s) de l'agent "
                                   "filtre(s) — ⛔ rien n'est jete en "
                                   "silence"
                         % (self._ecartees, self.QUOTA_AUTRES_PAR_MIN,
                            self._echos))
        self._fenetre_min = minute
        self._autres = 0
        self._ecartees = 0
        self._echos = 0

    def alimenter(self, octets: bytes) -> None:
        """Le flux DRAINÉ, filtré. ⚠️ Alimenté par le MÊME `_drainer()` que le
        compteur d'écho : ⛔ pas un second lecteur du port — « deux lecteurs sur
        un tty se VOLENT les octets »."""
        if not octets:
            return
        # 🔴 LE REPORT DE FRAGMENT. Une ligne de battement peut être coupée
        #    entre deux `read()` : sans ce reste, on la perdrait ~une fois sur
        #    N, en silence, et le journal aurait des trous qu'aucun compteur ne
        #    signalerait. Même piège que le marqueur de dn4-18.
        tampon = self._reste + octets
        morceaux = tampon.split(b"\n")
        reste = morceaux[-1]
        if len(reste) > self.MAX_FRAGMENT:
            # ⛔ ON GARDE LA TETE : c'est elle qui porte le motif d'alarme.
            reste = reste[:self.MAX_FRAGMENT]
            self._tronquees += 1
        self._reste = reste
        self.rincer()
        for ligne in morceaux[:-1]:
            ligne = ligne.rstrip(b"\r")
            if not ligne:
                continue
            txt = ligne.decode("utf-8", "replace")
            if self.RE_BATTEMENT.search(ligne):
                self._ecrire("BATTEMENT", txt)
            elif self.RE_REBOOT.search(ligne):
                self._ecrire("REBOOT", txt)
            elif self.RE_ALARME.search(ligne):
                self._ecrire("ALARME", txt)
            elif self.RE_ECHO_AGENT.search(ligne) or self.RE_INVITE_SEULE.match(ligne):
                # ⛔ NOTRE PROPRE ECHO. ⚠️ Il est COMPTE, pas jete en silence :
                #    un echo qui s'effondrerait dirait que la carte ne recoit
                #    plus rien, et ce serait une information.
                self._echos += 1
            elif self._autres < self.QUOTA_AUTRES_PAR_MIN:
                self._autres += 1
                self._ecrire("fil", txt)
            else:
                self._ecartees += 1

    def fermer(self) -> None:
        """⚠️ CETTE METHODE N'ETAIT APPELEE NULLE PART — c'etait du code mort
        (constat de revue 2026-08-28). Elle l'est desormais depuis
        `SortieSerie.fermer()`, et elle RINCE avant de fermer : sans ca, le
        decompte de la minute en cours et le fragment en vol (potentiellement le
        DEBUT d'un `Guru Meditation` coupe par le halt) partaient a la poubelle.
        """
        # ⛔ Le recap de la minute EN COURS, meme si la minute n'a pas bascule.
        if self._ecartees or self._echos:
            self._ecrire("MINUTE", "%d ligne(s) ECARTEE(S) par le quota "
                                   "(plafond %d) · %d echo(s) filtre(s) — "
                                   "MINUTE INCOMPLETE, close par l'arret de "
                                   "l'agent"
                         % (self._ecartees, self.QUOTA_AUTRES_PAR_MIN,
                            self._echos))
            self._ecartees = 0
            self._echos = 0
        # ⛔ Le fragment EN VOL. Une ligne non terminee au moment de l'arret est
        #    peut-etre la plus interessante du fichier.
        if self._reste:
            self._ecrire("FRAGMENT", self._reste.decode("utf-8", "replace")
                         + "   ⚠️ LIGNE NON TERMINEE au moment de l'arret")
            self._reste = b""
        if self._echecs_ecriture or self._echecs_rotation or self._tronquees:
            self._ecrire("SANTE", "boite noire : %d echec(s) d'ecriture · %d "
                                  "rotation(s) REFUSEE(S) · %d fragment(s) "
                                  "tronque(s) · %d rotation(s) reussie(s)"
                         % (self._echecs_ecriture, self._echecs_rotation,
                            self._tronquees, self._rotations))
        if self._f is None:
            return
        try:
            self._f.close()
        except Exception:
            pass
        finally:
            self._f = None

    def sante(self) -> str:
        """Ce que le bilan doit publier — ⛔ une boite noire cassee ne doit pas
        se decouvrir en ouvrant le fichier au jour 7."""
        return ("%d echec(s) d'ecriture · %d rotation(s) refusee(s) · %d "
                "rotation(s) reussie(s) · %d fragment(s) tronque(s)"
                % (self._echecs_ecriture, self._echecs_rotation,
                   self._rotations, self._tronquees))


class SortieSerie:
    """Branche A — le port série (COM3 sous Windows quand la carte n'est PAS attachée à WSL).
    ⚠️ Exclusivité WSL↔COM3 : si `usbipd attach` tient la carte, COM3 N'EXISTE PAS ici.
    Un agent qui ne trouve pas son port n'est pas un bug de l'agent (trap n°4 de la story)."""

    nom = "serie"
    # ✅ LE SEUL CANAL CONSOLE QUI EXISTE (AC2.4).
    canal_console = True

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

    def __init__(self, port: str, tracer: str = None, journal=None):
        import serial  # pyserial — déjà sur la tour

        self._serial_mod = serial
        self._port = port
        self._con = None
        # 🔬 INSTRUMENT dn4-18 (2026-08-26) — ⛔ CE N'EST PAS LE MÉCANISME.
        #    AC1.1 demande « le texte DRAINÉ pendant la fenêtre », verbatim.
        #    `_drainer()` COMPTE les octets et les JETTE : le bandeau de boot,
        #    s'il arrive, ne laisse que quelques centaines d'unités de plus
        #    dans un compteur cumulatif. Et les lignes `[agent] …` de stderr ne
        #    portent AUCUN horodatage, donc aucun délai ne s'en déduit.
        # ⚠️ ⛔ NE PAS le remplacer par un harnais qui rejouerait le drain à
        #    côté : « un harnais qui REJOUE au lieu d'appeler la fonction est
        #    décoratif ». Le seul témoin recevable de ce que l'AGENT entend est
        #    pris DANS l'agent.
        # ⚠️ COÛT QUAND L'OPTION N'EST PAS POSÉE : un `is None` par drain.
        self._tracer_chemin = tracer
        self._tracer_f = None
        # 🔴 dn4-5 / AC2.5 — LA BOITE NOIRE DU SOAK. ⛔ Canal DISTINCT de
        #    `--tracer-console` : celui-ci filtre (battement, reboots,
        #    alarmes, evenements de port) et TOURNE, l'autre capture tout
        #    et ne tourne pas. Voir `JournalSoak`.
        self._journal = journal
        # 🔴 dn4-5/T4 — COMPTEUR MONOTONE D'OUVERTURES. Le lisseur s'y cale
        #    pour vider sa fenetre a chaque reprise (AC4.3). ⛔ Il ne peut PAS
        #    se caler sur `reprise_liaison` : ce drapeau est CONSOMME par le
        #    reposeur d'horloge (il le remet a False), et deux lecteurs d'un
        #    meme drapeau se le VOLENT — exactement le piege que dn4-18 a paye
        #    sur `NON ARMEE`.
        self.ouvertures = 0
        # 🔴 dn4-18 — LE LECTEUR D'ÉTAT D'HORLOGE. Il est alimenté par le MÊME
        #    `_drainer()` qui compte déjà l'écho : ⛔ pas un second lecteur du
        #    port (« deux lecteurs sur un tty se VOLENT les octets »).
        self.horloge = LecteurHorloge()
        # 🔴 AC4.2 — LE DRAPEAU DE REPRISE DE LIAISON. Posé à CHAQUE ouverture
        #    RÉUSSIE du port : le lancement de l'agent, et chaque sortie de
        #    backoff. C'est ce qui couvre « la tour (ou l'agent) redémarre
        #    pendant que la carte reste allumée » — le cas que le bandeau de
        #    boot ne couvre PAS, mesuré 0/2 le 2026-08-26.
        self.reprise_liaison = False
        # Ce que le chemin de commande console a fait — ⛔ SÉPARÉ de
        # `trames_emises`, voir `commande_console()`.
        self.commandes_console = 0
        self.commandes_echouees = 0
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

    def _tracer(self, etiquette: str, octets: bytes = b"") -> None:
        """La trace BRUTE et HORODATÉE d'AC1.1 — ⛔ best-effort, par construction.

        ⛔ UN INSTRUMENT QUI CASSE CE QU'IL OBSERVE N'EST PAS UN INSTRUMENT :
           toute panne d'écriture de la trace est avalée. La liaison, elle,
           n'est pas best-effort — c'est pourquoi ce `except` est ICI et
           nulle part ailleurs.
        """
        if self._tracer_chemin is None:
            return
        try:
            if self._tracer_f is None:
                # 'ab' : on AJOUTE. Trois débranchements dans une même fenêtre
                # d'observation écriraient sinon l'un sur l'autre.
                self._tracer_f = open(self._tracer_chemin, "ab")
            t = time.time()
            lt = time.localtime(t)
            entete = ("\n--- %04d-%02d-%02d %02d:%02d:%02d.%03d  %s (%d o) ---\n"
                      % (lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour,
                         lt.tm_min, lt.tm_sec, int((t % 1.0) * 1000),
                         etiquette, len(octets)))
            self._tracer_f.write(entete.encode("utf-8"))
            if octets:
                self._tracer_f.write(octets)
            self._tracer_f.flush()
        except Exception:
            pass

    def _ouvrir(self):
        # 🔴 dn4-18, correctif de revue 2026-08-26 — LE FRAGMENT DE LIGNE COUPE
        #    EN VOL EST JETE ICI, ⛔ pas recolle au flux suivant. Le lecteur vit
        #    sur la sortie, pas sur la connexion : sans ça, un debranchement au
        #    milieu d'une ligne fabriquait, au rebranchement, une ligne que ni
        #    le firmware ni la capture n'ont jamais emise. ⚠️ Le debranchement
        #    EST le sujet d'AC7 : ce chemin est le plus emprunte de la story.
        self.horloge.rupture()
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
        # 🔬 dn4-18 : l'instant EXACT où l'hôte a repris le port. C'est le
        #    point de départ du délai d'AC1.1 — celui que stderr ne date pas.
        self._tracer("PORT OUVERT (%s)" % self._port)
        if self._journal is not None:
            self._journal.evenement("PORT", "OUVERT (%s)" % self._port)
        # 🔴 AC4.2 — TOUTE ouverture réussie est une reprise de liaison, y
        #    compris LA PREMIÈRE. ⛔ Ce n'est pas « au démarrage de l'agent »
        #    (décision n°1, réfutée) : le déclencheur reste l'ÉTAT de la carte.
        #    C'est seulement le MOMENT où l'agent va aller le LIRE.
        self.reprise_liaison = True
        self.ouvertures += 1  # dn4-5/T4 : le lisseur vide sa fenetre ici

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
            except Exception as exc:
                self._echecs_ouverture += 1
                # Paliers 0,5 · 1 · 2 · 4 s, plafonnés à 5 s — soit AU PLUS une
                # tentative d'ouverture par cycle de cinq trames, jamais cinq.
                delai = min(0.5 * (2 ** min(self._echecs_ouverture - 1, 4)), 5.0)
                self._prochain_essai = time.monotonic() + delai
                # 🔬 dn4-18 : chaque tentative d'ouverture REFUSÉE est datée.
                #    C'est ce qui borne, par le haut, l'instant où le port est
                #    redevenu ouvrable — donc le délai d'AC1.1.
                self._tracer("OUVERTURE REFUSEE — backoff %.1f s "
                             "(echecs_ouverture=%d) : %s"
                             % (delai, self._echecs_ouverture, exc))
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
        except Exception as exc:
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
            # 🔬 dn4-18 : l'instant EXACT où le fil s'est rompu, et le palier de
            #    backoff qui s'arme. ⇒ la fenêtre d'AVEUGLEMENT de l'agent est
            #    datée des deux bouts (celle-ci et « PORT OUVERT »).
            self._tracer("PORT PERDU — backoff %.1f s (echecs_envoi=%d) : %s"
                         % (delai, self._echecs_envoi, exc))
            # 🔴 dn4-5/AC2.5 — CET EVENEMENT EST CE QUI SEPARE « l'agent a perdu
            #    le port » de « la carte est HALTEE ». Les deux se ressemblent
            #    trait pour trait vus du fil (plus rien n'arrive) ; seul le
            #    JOURNAL peut dire lequel des deux s'est produit, et quand.
            if self._journal is not None:
                self._journal.evenement(
                    "PORT", "PERDU — backoff %.1f s (echecs_envoi=%d) : %s"
                            % (delai, self._echecs_envoi, exc))
            try:
                self._con.close()
            finally:
                self._con = None
            raise

    def commande_console(self, commande: str) -> None:
        """dn4-18 — envoie UNE commande console (`rtc`, `rtc set …`).

        🔴 CE N'EST PAS `envoyer()`, ET ÇA NE PEUT PAS L'ÊTRE : `envoyer()`
           préfixe `b"pc "` EN DUR (le dialecte des trames), donc il n'existe
           AUCUN chemin pour envoyer une commande console autre que `pc …`.

        LES QUATRE CONTRAINTES D'AC2.4, ET COMMENT CHACUNE EST TENUE :
        ⛔ 1. N'INCRÉMENTE NI `trames_emises` NI `seq`. Ces deux-là vivent dans
              `principal()` et ne sont touchés que par `sortie.envoyer()` :
              cette méthode ne les voit même pas. Sinon le débit de trames
              publié au bilan — ET le chiffre du critère n°4 du brief —
              décrirait autre chose que ce qu'il prétend décrire.
        ✅ 2. PASSE PAR LE MÊME BACKOFF ET LE MÊME `write_timeout`. Elle
              n'ouvre pas le port elle-même : si le port est fermé (backoff en
              cours), elle lève `LiaisonEnAttente` comme le reste. ⛔ Aucune
              attente nouvelle et non bornée : une carte en PANIQUE HALTÉE ne
              peut pas figer l'agent par ce chemin non plus.
        ✅ 3. N'EXISTE QUE SUR `SortieSerie` (voir `canal_console`).
        ✅ 4. DRAINE APRÈS AVOIR ÉCRIT, comme `envoyer()` : sans ça la réponse
              de la carte n'atteindrait le lecteur qu'au prochain envoi de
              trame — et le verdict de pose arriverait « en retard » sans que
              rien ne le dise.

        ⚠️ `max_cmdline_length = 128` (dn_console.c) ; les ~28 caractères de
           `rtc set AAAA-MM-JJ HH:MM:SS` passent très largement. On le VÉRIFIE
           quand même : une commande trop longue serait tronquée par le REPL et
           exécutée AMPUTÉE.
        """
        if len(commande) + 1 > 128:
            raise ValueError("commande console de %d o : le REPL tronque au-dela "
                             "de 128 (max_cmdline_length)" % (len(commande) + 1))
        if self._con is None:
            # ⛔ ON N'OUVRE PAS LE PORT ICI. Ouvrir depuis ce chemin
            #    court-circuiterait le backoff : une commande console pourrait
            #    déclencher un `close()/open()` — donc, sous Windows, la
            #    séquence DTR/RTS — hors de tout compteur d'échecs.
            raise LiaisonEnAttente(
                "port %s ferme (backoff) : commande console ABANDONNEE" % self._port)
        octets = (commande + "\n").encode("ascii")
        try:
            ecrits = self._con.write(octets)
            if ecrits is not None and ecrits != len(octets):
                raise IOError("ecriture partielle %s/%d o" % (ecrits, len(octets)))
            self._tracer("COMMANDE CONSOLE : %s" % commande)
            self._drainer()
            self.commandes_console += 1
        except Exception:
            # ⚠️ MÊME TRAITEMENT QUE `envoyer()` : le backoff s'arme, le port se
            #    ferme. ⛔ Un chemin d'envoi qui échouerait sans armer le
            #    backoff rouvrirait immédiatement — le défaut exact que le
            #    correctif du 2026-08-19 a fermé pour les trames.
            self.commandes_echouees += 1
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
        # 🔴 LE RINCAGE PASSE AVANT LE `if retour:` — c'est tout l'objet du
        #    correctif : `alimenter()` n'etait appele QUE s'il arrivait des
        #    octets, donc une carte haltee ou debranchee gelait le recap de
        #    minute pour toujours. Or c'est exactement la minute qu'on relira.
        if self._journal is not None:
            self._journal.rincer()
        if retour:
            # 🔬 dn4-18 : LE TEXTE, pas seulement son compte. C'est la seule
            #    réponse recevable à « la ligne `barre : … · horloge …` du
            #    bandeau de boot est-elle drainée, oui ou non » (AC1.1).
            self._tracer("DRAIN", retour)
            # dn4-5/AC2.5 : LE MEME flux, filtre pour la boite noire du
            # soak. ⛔ Pas un second `read()` sur le port.
            if self._journal is not None:
                self._journal.alimenter(retour)
            # 🔴 dn4-18 — LE MÊME FLUX, LU UNE SECONDE FOIS PAR LE LECTEUR
            #    D'HORLOGE. ⛔ Pas un second `read()` : deux lecteurs sur un
            #    tty ne s'excluent pas, ils se VOLENT les octets (dn_console.py).
            self.horloge.alimenter(retour)
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
            # 🔴 CORRECTIF DE REVUE 2026-08-28 — L'ARRET SE DIT MEME EN BACKOFF.
            #    Cette sortie anticipee n'ecrivait RIEN dans la boite noire.
            #    Scenario : la carte tombe a J+3, l'agent entre en backoff
            #    (`_con = None`), puis l'agent est arrete (ou la session Windows
            #    se ferme) ⇒ le journal s'arretait sur un `PORT PERDU` et rien
            #    d'autre. A la relecture au jour 7, on ne distinguait plus :
            #    (a) l'agent a tourne en aveugle 4 jours ; (b) l'agent est mort
            #    a J+3 ; (c) la tour s'est eteinte. C'est TEXTUELLEMENT la
            #    discrimination que `JournalSoak` donne comme sa raison d'exister,
            #    et l'evenement `DEPART` n'avait alors aucun pendant.
            if self._journal is not None:
                self._journal.evenement(
                    "ARRET", "agent arrete ALORS QUE LE PORT ETAIT DEJA PERDU "
                             "(backoff en cours) — ⚠️ le silence qui suit est "
                             "celui de L'AGENT, ⛔ pas forcement celui de la carte")
                self._journal.fermer()
            self._fermer_tracer()
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
            self._tracer("PORT FERME (arret de l'agent)")
            if self._journal is not None:
                self._journal.evenement("PORT", "FERME (arret de l'agent)")
                self._journal.evenement(
                    "ARRET", "agent arrete PROPREMENT, port rendu — le silence "
                             "qui suit est celui de L'AGENT")
                self._journal.fermer()  # ⛔ etait du code mort avant la revue
            self._fermer_tracer()

    def _fermer_tracer(self) -> None:
        """⚠️ `_bilan` appelle `fermer()` AVANT de publier le chiffre d'écho, et
        `fermer()` peut être appelé deux fois. La fermeture du fichier de trace
        est donc IDEMPOTENTE, et elle ne remonte jamais d'exception."""
        if self._tracer_f is None:
            return
        try:
            self._tracer_f.close()
        except Exception:
            pass
        finally:
            self._tracer_f = None


class SortieWebSocket:
    """Branche B — client WebSocket vers l'ESP SERVEUR (sortant : pas de règle de
    pare-feu entrante ; reste la question des tunnels — constatée en T4, pas supposée)."""

    nom = "websocket"
    # ⛔ PAS DE CONSOLE SUR CETTE BRANCHE : le WebSocket porte les trames, ⛔ pas
    #    le REPL. L'absence de canal est un ÉTAT DÉCLARÉ (AC2.4), et le bilan le
    #    DIT — ⛔ il ne se tait pas.
    canal_console = False

    def __init__(self, url: str):
        from websockets.sync.client import connect  # websockets — déjà sur la tour

        self._connect = connect
        self._url = url
        self._con = None
        # 🔴 dn4-5/AC4.3 (correctif de revue 2026-08-28). Cette branche
        #    RECONNECTE bel et bien — `envoyer()` pose `_con = None` sur
        #    exception et `_ouvrir()` repart au tour suivant — mais SANS
        #    COMPTEUR. Le lisseur ne voyait donc jamais la reprise et
        #    republiait, apres une coupure WiFi, une moyenne dont deux tiers
        #    dataient d'avant. Le compteur est le MEME contrat que sur le serie.
        self.ouvertures = 0

    def _ouvrir(self):
        self._con = self._connect(self._url, open_timeout=3)
        self.ouvertures += 1  # ⇒ le lisseur vide sa fenetre ici (AC4.3)

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


class ReprisHorloge:
    """dn4-18 — l'agent pose l'heure, et SEULEMENT quand la carte le demande.

    🔴 LE DÉCLENCHEUR EST L'ÉTAT DE LA CARTE (le bit `OS`), ⛔ PAS LE CYCLE DE
       VIE DE L'AGENT. Tranché par la mesure du 2026-08-26 : ce qui avait
       redémarré, c'était LA CARTE, pendant que l'agent continuait de tourner.
       ⇒ « l'agent envoie l'heure une fois à son démarrage » est exactement la
         conception qui ÉCHOUE sur le cas observé.

    ⚠️ CE QUE CETTE CLASSE REND DÉPENDANT, ET QUI S'ÉCRIT (AC4.4) : l'heure de
       la carte devient dépendante de celle de la TOUR. **Une tour à l'heure
       fausse fait une carte à l'heure fausse — et la carte dira `OS = 0`, donc
       FIABLE.** C'est un fait de conception, ⛔ pas un défaut caché.
    """

    def __init__(self, sortie):
        self.sortie = sortie
        self.actif = bool(getattr(sortie, "canal_console", False))
        self.interrogations = 0
        self.derniere_interro = None      # monotonic
        self.motif_derniere_interro = None
        self.poses_tentees = 0
        self.poses_reussies = 0
        self.poses_refusees = 0
        self.poses_sans_reponse = 0
        self.motifs_refus = {}
        self.motifs_pose = {}             # pourquoi on a posé : OS=1 / ecart
        self.echecs_consecutifs = 0
        # 🔴 CORRECTIF DE REVUE 2026-08-26 — L'ANTI-RAFALE NE COUVRAIT QUE LES
        #    REFUS. Une pose ACCEPTEE remettait `echecs_consecutifs` a 0, donc
        #    l'escalade 60·120·240 ne s'armait JAMAIS sur le chemin du succes :
        #    une carte qui REPERD l'heure apres chaque pose (oscillateur qui
        #    redecroche — `CAP_SEL` est consigne INCONNU depuis dn3-2) rejouait
        #    `rtc` + `rtc set` toutes les ~31 s INDEFINIMENT, a ~89 o/s de bruit
        #    console permanent, avec deux lignes de stderr par tour.
        # ⚠️ Ca restait SOUS le plafond publie (99 o/s, capteurs-i2c.md §13.15.7.1)
        #    — ⛔ mais un regime PERMANENT n'est pas un transitoire, et le fil
        #    EST le transport des cinq metriques.
        self.poses_rapprochees = 0
        self._derniere_pose_ok = None     # monotonic
        self.prochaine_pose = 0.0         # monotonic
        self._pose_en_cours = None        # monotonic de l'envoi
        self.derniere_pose_texte = None
        self.ecart_max_vu = None
        self.erreurs_canal = 0
        # 🔴 « CE QUE J'AI DÉJÀ TRAITÉ » — EN COMPTEURS DE LECTURE, ⛔ PAS EN
        #    SECONDES. Sans ça, l'agent reposait l'heure une SECONDE fois sur
        #    la MÊME lecture (défaut attrapé par l'épreuve fonctionnelle du
        #    2026-08-26) : la pose réussissait, mais l'état et l'écart lus
        #    AVANT elle étaient toujours là, et ils redéclenchaient.
        self._etats_a_la_pose = -1
        self._heures_a_la_pose = -1
        # Après une pose RÉUSSIE, on re-demande l'état : ⛔ le verdict de la
        # carte ne dispense pas de RELIRE (AC4.5 « pas par le fait d'avoir
        # écrit »). C'est borné par le plancher, donc ça ne peut pas rafaler.
        self.verifier_apres_pose = False

    # ------------------------------------------------------------------ util
    def _dire(self, msg):
        print("[agent] " + msg, file=sys.stderr)

    def _envoyer(self, commande) -> bool:
        try:
            self.sortie.commande_console(commande)
            return True
        except LiaisonEnAttente:
            # ⚠️ Le port est en backoff : ce n'est PAS une nouvelle panne, c'est
            #    celle déjà signalée qui dure. ⛔ On ne réimprime pas.
            return False
        except Exception as exc:
            self.erreurs_canal += 1
            self._dire("🔴 horloge : commande console en echec (%d) : %s"
                       % (self.erreurs_canal, exc))
            return False

    # ----------------------------------------------------------------- cycle
    def cycle(self, maintenant: float) -> None:
        """Appelé UNE fois par cycle de la boucle (1 Hz). ⛔ Rien d'autre ne le
        déclenche : pas de thread, pas de timer, pas d'attente bloquante."""
        if not self.actif:
            return
        lect = self.sortie.horloge
        self._verdict(maintenant, lect)
        self._interroger(maintenant)
        self._poser(maintenant, lect)

    # --------------------------------------------------------------- verdict
    def _verdict(self, maintenant, lect):
        if self._pose_en_cours is None:
            return
        v = lect.verdict
        if v is None:
            if maintenant - self._pose_en_cours < DN_H_ATTENTE_VERDICT_S:
                return
            # ⛔ « PAS DE RÉPONSE » EST UN TROISIÈME SEAU, ⛔ pas un succès et
            #    ⛔ pas un refus. Les confondre enverrait chercher la panne au
            #    mauvais endroit (la leçon i2c/bcd de dn_rtc).
            self.poses_sans_reponse += 1
            self._pose_en_cours = None
            self._echouer(maintenant, "aucune reponse en %.0f s"
                          % DN_H_ATTENTE_VERDICT_S)
            return
        self._pose_en_cours = None
        if v[0] == "OK":
            self.poses_reussies += 1
            self.echecs_consecutifs = 0
            # ⛔ LE PLANCHER RESTE, MÊME APRÈS UN SUCCÈS : c'est lui qui borne
            #    le pire cas chiffré d'AC4.3. Un succès n'autorise pas une
            #    rafale de succès.
            # 🔴 ET IL NE SUFFIT PAS (correctif de revue 2026-08-26) : le
            #    plancher borne le DEBIT, ⛔ pas la DUREE. Des poses acceptees
            #    qui se REPETENT sont le signe que la carte reperd l'heure —
            #    une panne, ⛔ pas un regime — et elles doivent escalader comme
            #    un refus. Sinon l'agent tourne a ~31 s pour toujours.
            if (self._derniere_pose_ok is not None
                    and maintenant - self._derniere_pose_ok < DN_H_PERIODE_S):
                self.poses_rapprochees += 1
                delai = min(DN_H_BACKOFF_S * (2 ** (self.poses_rapprochees - 1)),
                            DN_H_BACKOFF_MAX_S)
                self.prochaine_pose = maintenant + delai
                self._dire("⚠️  horloge : %d pose(s) REUSSIE(S) RAPPROCHEE(S) — la "
                           "carte REPERD l'heure apres chaque pose. ⛔ Ce n'est "
                           "PAS un refus. Prochaine tentative dans %.0f s"
                           % (self.poses_rapprochees, delai))
            else:
                self.poses_rapprochees = 0
                self.prochaine_pose = maintenant + DN_H_PLANCHER_S
            self._derniere_pose_ok = maintenant
            self.verifier_apres_pose = True
            self._dire("✅ horloge : heure POSEE et VERIFIEE par la carte — %s" % v[1])
        else:
            self.poses_refusees += 1
            self.motifs_refus[v[1]] = self.motifs_refus.get(v[1], 0) + 1
            self._echouer(maintenant, v[1])

    def _echouer(self, maintenant, motif):
        """AC4.3 — L'ANTI-RAFALE, ET IL EST CHIFFRÉ.

        🔴 LE PIRE CAS À FERMER : `rtc set` refusé en boucle à 5 essais/s ⇒
           ~376 o d'écho par essai, soit **plusieurs Ko/s** injectés dans le
           flux console — c'est-à-dire le NOYAGE de `echo_octets`, l'instrument
           d'AC3 de dn2-2, sur le fil qui EST le transport des cinq métriques.
        ⇒ paliers 60 · 120 · 240 … plafonnés à 3 600 s.
        """
        self.echecs_consecutifs += 1
        delai = min(DN_H_BACKOFF_S * (2 ** (self.echecs_consecutifs - 1)),
                    DN_H_BACKOFF_MAX_S)
        self.prochaine_pose = maintenant + delai
        # 🔴 ET ON RE-DEMANDERA L'ÉTAT AVANT DE RETENTER. Sans ça, le palier
        #    ci-dessus serait du CODE MORT : la lecture qui avait déclenché la
        #    pose est CONSOMMÉE, donc plus rien ne redéclencherait avant la
        #    période de 600 s — et l'escalade 60·120·240 ne servirait jamais.
        #    (défaut attrapé par la scène 5 de l'épreuve fonctionnelle)
        self.verifier_apres_pose = True
        self._dire("🔴 horloge : pose REFUSEE (%s) — %d echec(s) consecutif(s), "
                   "prochaine tentative dans %.0f s"
                   % (motif, self.echecs_consecutifs, delai))

    # ----------------------------------------------------------- interroger
    def _interroger(self, maintenant):
        if self._pose_en_cours is not None:
            return               # ⛔ on n'interroge pas pendant qu'on attend un verdict
        lect = self.sortie.horloge
        if lect.etat == "NON_ARMEE" and not self.sortie.reprise_liaison:
            # ✅ AC3.3 — ÉTAT TERMINAL **EN RÉGIME**. Le device I2C n'existe
            #    pas : il n'y a RIEN à poser, et la barre dit déjà « --:-- »,
            #    « et c'est CORRECT ». ⛔ On ne réessaie JAMAIS **en boucle**
            #    là-dessus : ni à la période de 600 s, ni à aucun autre motif.
            # 🔴 MAIS « TERMINAL » N'EST PAS « DEFINITIF » — CORRECTIF DE REVUE
            #    2026-08-26, **decision owner**. `NON ARMEE` n'est ⛔ pas une
            #    propriete de la carte : c'est une CONDITION DE BOOT
            #    (dn_console.c:7419-7421 — bus absent au boot, `Control_1`
            #    illisible, ou `xTaskCreate` echoue), sur un bus dont ce depot a
            #    MESURE qu'il se degrade ~40 s a froid.
            #    En AVALANT `reprise_liaison`, l'agent ne redemandait plus
            #    JAMAIS : la seule sortie devenait le bandeau de boot — canal
            #    mesure a **9/10** (et **0/2** quand c'est l'agent qui
            #    redemarre) et sur lequel AC2.2 ecrit « ⛔ rien ne s'appuie
            #    dessus ». ⇒ une carte redevenue ARMEE laissait la barre a
            #    « --:-- » POUR LA VIE DE L'AGENT.
            # ⇒ ON RE-SONDE **UNE FOIS PAR REPRISE DE LIAISON** (AC4.2), ⛔ pas
            #   en boucle, et le plancher de 30 s ci-dessous borne le cout
            #   exactement comme pour tout autre etat (AC4.3).
            return
        motif = None
        if self.sortie.reprise_liaison:
            motif = "reprise de liaison"
        elif self.verifier_apres_pose and maintenant >= self.prochaine_pose:
            # ⛔ LA RELECTURE EST PACÉE PAR LE MÊME PALIER QUE LA POSE, et ce
            #    n'est pas un détail : une pose refusée en boucle re-demanderait
            #    sinon `rtc` toutes les 30 s — soit **87 o/s**, +32 % du bruit
            #    console mesuré, sur le fil qui EST le transport des cinq
            #    métriques. Le palier gouverne les DEUX.
            motif = "verification apres pose"
        elif (self.derniere_interro is None
              or maintenant - self.derniere_interro >= DN_H_PERIODE_S):
            motif = "periode %.0f s" % DN_H_PERIODE_S
        if motif is None:
            return
        # ⛔ LE PLANCHER EST INCONDITIONNEL : c'est lui qui borne le coût console
        #    quand le port bat (une reprise de liaison toutes les secondes).
        if (self.derniere_interro is not None
                and maintenant - self.derniere_interro < DN_H_PLANCHER_S):
            return
        if not self._envoyer("rtc"):
            return               # port en backoff : on retentera au prochain cycle
        self.sortie.reprise_liaison = False
        self.verifier_apres_pose = False
        self.derniere_interro = maintenant
        self.motif_derniere_interro = motif
        self.interrogations += 1

    # ----------------------------------------------------------------- poser
    def _poser(self, maintenant, lect):
        if self._pose_en_cours is not None:
            return
        motif = self._motif_de_pose(lect)
        if motif is None:
            return
        if maintenant < self.prochaine_pose:
            return               # anti-rafale (voir `_echouer`)
        t = time.time()
        # ⚠️ ARRONDI À LA SECONDE LA PLUS PROCHE, ET C'EST MESURÉ : composer
        #    depuis `localtime(t)` TRONQUE les sous-secondes ⇒ biais
        #    systématiquement dans [−1 s, 0] (−0,4 s et −0,2 s mesurés le
        #    2026-08-26). Avec `t + 0,5` le biais devient [−0,5 s, +0,5 s],
        #    CENTRÉ — et le seuil d'AC1.2 (≤ 2 s) garde toute sa marge.
        lt = time.localtime(t + 0.5)
        # ✅ HEURE LOCALE DÉCOMPOSÉE (A4), ⛔ PAS UN EPOCH UTC. Le jour de
        #    semaine n'est PAS passé : le firmware le CALCULE (Sakamoto) — le
        #    donner ferait deux sources de vérité.
        cmd = "rtc set %04d-%02d-%02d %02d:%02d:%02d" % (
            lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec)
        lect.armer_verdict()
        if not self._envoyer(cmd):
            lect.verdict = None
            return
        self.poses_tentees += 1
        # ⛔ CETTE LECTURE EST CONSOMMÉE : plus rien ne se déclenchera dessus.
        self._etats_a_la_pose = lect.etats_lus
        self._heures_a_la_pose = lect.heures_lues
        self.prochaine_pose = max(self.prochaine_pose,
                                  maintenant + DN_H_PLANCHER_S)
        # ⚠️ CLE NORMALISEE (correctif de revue 2026-08-26) : le motif d'ecart
        #    porte SA VALEUR dans son texte, donc chaque pose creait une CLE
        #    NEUVE. Sur un soak de 7 jours (dn4-5) le dictionnaire — et la ligne
        #    de bilan qui l'imprime — croissaient sans borne. Le detail chiffre
        #    reste visible : il est dans le journal, ligne par ligne.
        cle = "ecart" if motif.startswith("ecart") else motif
        self.motifs_pose[cle] = self.motifs_pose.get(cle, 0) + 1
        self.derniere_pose_texte = cmd
        self._pose_en_cours = maintenant
        self._dire("⏱️  horloge : pose demandee (%s) — « %s »" % (motif, cmd))

    def _motif_de_pose(self, lect):
        # 🔴 AC4.1 — LE DÉCLENCHEUR EST `OS = 1`.
        # ⛔ RIEN NE SE DÉCLENCHE SUR UNE LECTURE DÉJÀ CONSOMMÉE PAR UNE POSE.
        if lect.etats_lus <= self._etats_a_la_pose:
            return None
        if lect.etat == "OS1":
            return "OS=1"
        # 🔴 AC6 — LE TROU ÉTÉ/HIVER, ET LE DÉCLENCHEUR D'AC4.1 NE LE VOIT PAS.
        #    Au passage été/hiver la tour change d'heure, la carte NON : `OS`
        #    reste à 0, la carte se déclare FIABLE, et **la barre affiche une
        #    heure fausse SANS se déclarer fausse, pendant des mois**. C'est
        #    précisément le mode de panne que `dn_rtc.h` dit interdit.
        # ⚠️ On ne compare QUE sur une lecture FRAÎCHE, et ⛔ jamais sur un
        #    état non fiable (comparer l'heure d'une carte qui dit `OS=1` n'a
        #    aucun sens : elle vaut 2000-01-01).
        # ⚠️ ET ⛔ JAMAIS SUR UNE VALEUR QUE LA CARTE DECLARE IRRECEVABLE
        #    (correctif de revue 2026-08-26) : `dn_console.c:7432` accole
        #    « ⛔ NON AFFICHABLE » a l'heure quand `dn_rtc_lire()` a rendu faux.
        #    La prendre quand meme, c'est comparer une valeur GELEE a l'horloge
        #    de la tour — donc un ecart qui derive de 1 s/s et franchit le seuil
        #    tout seul.
        if (lect.etat == "OS0" and lect.lue_ecart_s is not None
                and lect.lue_affichable
                and lect.heures_lues > self._heures_a_la_pose):
            if lect.lue_instant is not None and (
                    lect.etat_instant is None
                    or abs(lect.lue_instant - lect.etat_instant) <= 2.0):
                ecart = abs(lect.lue_ecart_s)
                if self.ecart_max_vu is None or ecart > self.ecart_max_vu:
                    self.ecart_max_vu = ecart
                if ecart > DN_H_SEUIL_ECART_S:
                    return "ecart %+d s > seuil %.0f s" % (
                        lect.lue_ecart_s, DN_H_SEUIL_ECART_S)
        # ⛔ AC4.6 — AUCUNE POSE QUAND LA CARTE DIT `FIABLE` (et dans les
        #    clous). Reposer une heure déjà bonne, c'est du bruit console et un
        #    risque d'écriture pour rien.
        # ⛔ AC3.2 — ET `INCONNU` N'EST NI `OS0` NI `OS1` : on ne pose pas, et
        #    on ne se tait pas non plus (le bilan publie le dernier état LU).
        return None


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
    # 🔴 dn4-17 (2026-08-26) — ET CETTE LIGNE EST PAYÉE PAR UNE MESURE, ⛔ PAS
    #    PAR DU CONFORT. Depuis dn4-17 l'agent tourne DÉTACHÉ sur la tour
    #    (double-clic ou tâche au logon) : il n'a PLUS DE CONSOLE, donc plus
    #    de Ctrl+C. MESURÉ ce jour-là sur le geste `dn-agent.bat stop` :
    #    `taskkill /PID` (poli) NE LE TUE PAS — il était encore vivant après
    #    5 s — et le repli `taskkill /F` (TerminateProcess) ne peut être
    #    intercepté par personne : **0 octet ajouté au journal**.
    #    ⇒ Le bilan de fin — le SEUL instrument qui dise si la liaison va
    #      bien (trames émises, erreurs d'envoi, recalages, bruit d'écho,
    #      refus firmware) — était PERDU À CHAQUE ARRÊT OWNER, alors que
    #      c'est exactement ce que la redirection de stderr existe pour
    #      sauver. Un fichier-drapeau est le seul canal qui traverse les
    #      trois régimes (console, détaché, tâche planifiée sans console).
    # ⚠️ Coût : UN `os.path.exists` par cycle, soit 1/s (PERIODE_S = 1,0 s).
    # 🔴 `type=` REFUSE LA CHAÎNE VIDE À L'ANALYSE (revue du 2026-08-26). Une
    #    option posée avec une valeur vide est une ERREUR DE LANCEUR, ⛔ pas une
    #    demande de désactivation : la taire produit un agent inarrêtable.
    ap.add_argument("--stop-si", metavar="FICHIER", default=None,
                    type=_chemin_non_vide,
                    help="s'arrête PROPREMENT dès que FICHIER apparaît — le "
                         "seul arrêt propre possible sans console")
    # 🔬 dn4-18 (2026-08-26) — INSTRUMENT, ⛔ PAS UN RÉGIME.
    # 🔴 COÛT CORRIGÉ PAR LA REVUE DU 2026-08-26, ET MESURÉ SUR LES CAPTURES
    #    LIVRÉES — ⛔ plus déduit du débit d'écho. Le chiffre annoncé ici était
    #    « ~275 o/s, ~1 Mo/h » : c'était le débit d'écho SEUL, qui oublie
    #    l'en-tête horodaté (~50 o) écrit à CHAQUE drain, donc ~5 fois par
    #    seconde. Mesuré sur `mesures/dn4-18/` :
    #      · AC7-4-temoin-negatif.trace   86 312 o / 193,0 s = 447 o/s (45 % d'en-têtes)
    #      · AC1-1-phaseA-agent-reel.trace 67 853 o / 142,0 s = 478 o/s (37 %)
    #      · AC7-temoin-positif.trace     137 791 o / 260,0 s = 530 o/s (35 %)
    # ⇒ **447 à 530 o/s, soit 1,6 à 1,9 Mo/h** — ~1,7× ce qui était annoncé.
    #   Sur les 7 jours de dn4-5 : **~270 à 320 Mo**, ⛔ sans aucune rotation.
    # ⛔ Ne pas le laisser armé sur un soak.
    # ─── dn4-5 / T4 : LE LISSAGE D'AFFICHAGE ────────────────────────────────
    # 🔴 `on` EST LE REGIME LIVRE. `off` existe pour UNE raison nommee : l'A/B
    #    d'AC4.4 se joue A L'OEIL, ecran contre Gestionnaire des taches, et sans
    #    ce drapeau il faudrait REFLASHER entre les deux jambes — donc casser le
    #    compteur du soak. ⛔ Ce n'est pas un reglage de confort.
    ap.add_argument("--lissage", choices=("on", "off"), default="on",
                    help="dn4-5/T4 — moyenne d'affichage sur 3 echantillons pour "
                         "CPU GHz, RESEAU bas/haut et DISQUE Mo/s (defaut `on`, "
                         "c'est le regime livre). `off` = valeurs BRUTES, pour "
                         "l'A/B a l'oeil d'AC4.4 SANS reflasher.")

    # ─── dn4-5 / AC2.5 : LA BOITE NOIRE DU SOAK ─────────────────────────────
    # ⚠️ ⛔ CE N'EST PAS `--tracer-console`, ET LES DEUX NE SE REMPLACENT PAS.
    #    `--tracer-console` = tout le fil, brut, 447-530 o/s, SANS rotation
    #    (270-320 Mo sur 7 j) : c'est un instrument de DIAGNOSTIC, sur fenetre
    #    courte. `--journal-soak` = le battement, les reboots, les alarmes et
    #    les evenements de port, avec ROTATION : ~18 o/s, soit ~11 Mo sur 7 j.
    # 🔴 CE JOURNAL VIT COTE TOUR (D4/D5) : ⛔ aucune ecriture NVS/flash cote
    #    carte en regime — une semaine H24 est EXACTEMENT le regime ou une
    #    ecriture periodique se paierait (mesure : sous ecriture flash,
    #    « l'image defile », 165 343 o/s).
    ap.add_argument("--journal-soak", metavar="FICHIER", default=None,
                    type=_chemin_non_vide,
                    help="dn4-5/AC2.5 — journal FILTRE et HORODATE du soak "
                         "(battement, reboots, alarmes, evenements de port), "
                         "avec rotation. ⛔ Ne fonctionne QU'AVEC --serie.")
    ap.add_argument("--journal-max-mo", metavar="Mo", type=int, default=32,
                    help="plafond d'un fichier de journal avant rotation "
                         "(defaut 32 Mo ; avec 4 crans la RETENTION est de "
                         "5 x 32 = 160 Mo, et ce qui deborde est DETRUIT — "
                         "chaque rotation l'ecrit dans le journal. Plafond "
                         "2048 Mo. ⚠️ Le debit de regime sur 7 j n'est PAS "
                         "connu : 10,6 Mo est un PLANCHER mesure a 18,3 o/s, "
                         "le plus haut mesure est 163 o/s soit ~98 Mo.)")
    ap.add_argument("--tracer-console", metavar="FICHIER", default=None,
                    type=_chemin_non_vide,
                    help="capture BRUTE et HORODATEE de tout ce que l'agent "
                         "draine sur le fil (diagnostic dn4-18). ⛔ Ne "
                         "fonctionne QUE avec --serie.")
    args = ap.parse_args()

    if args.duree < 0:
        ap.error("--duree doit etre >= 0 (0 = infini)")

    # ⚠️ `if args.serie:` testait la VÉRACITÉ, pas la présence : un `--serie ""`
    # (variable vide développée par un script de lancement) retombait EN SILENCE
    # sur stdout, la carte restait « jamais recue », et rien ne le signalait.
    # 🔬 dn4-18 — ⛔ UNE OPTION QUI NE FAIT RIEN EN SILENCE EST UN DÉFAUT, PAS
    #    UN CONFORT. C'est le motif déjà payé trois fois dans ce fichier
    #    (`--serie ""`, `--stop-si ""`, `--lhm "hote:"`). Il n'y a de FIL que
    #    sur la branche série : sur stdout et sur WebSocket, l'absence de canal
    #    console est un ÉTAT DÉCLARÉ, ⛔ jamais un silence.
    # 🔴 dn4-18, correctif de revue 2026-08-26 — ON ECHOUE **A L'ANALYSE**, ⛔
    #    PAS EN SILENCE PENDANT TOUTE LA SESSION. `_tracer()` avale toute panne
    #    d'ecriture, et c'est VOULU (« un instrument qui casse ce qu'il observe
    #    n'est pas un instrument ») — mais un chemin invalide, un disque plein
    #    ou un droit manquant rendait alors un fichier VIDE sans un mot, et la
    #    fenetre d'observation etait perdue. C'est le motif deja paye trois fois
    #    dans ce fichier (`--serie ""`, `--stop-si ""`, `--lhm "hote:"`).
    if args.tracer_console is not None:
        try:
            with open(args.tracer_console, "ab"):
                pass
        except OSError as exc:
            ap.error("--tracer-console %r n'est PAS inscriptible (%s). ⛔ Une "
                     "capture qui echoue en silence est une fenetre "
                     "d'observation PERDUE." % (args.tracer_console, exc))
    if args.journal_soak is not None:
        # ⚠️ MEME EXIGENCE QUE POUR `--tracer-console`, ET POUR LA MEME RAISON :
        #    un journal qu'on decouvre non inscriptible APRES sept jours est une
        #    fenetre d'observation PERDUE, et elle ne se rejoue pas.
        try:
            with open(args.journal_soak, "a", encoding="utf-8"):
                pass
        except OSError as exc:
            ap.error("--journal-soak %r n'est PAS inscriptible (%s). ⛔ Une "
                     "boite noire qu'on decouvre muette au jour 7 est une "
                     "fenetre d'observation PERDUE." % (args.journal_soak, exc))
    if args.journal_soak is not None and args.serie is None:
        ap.error("--journal-soak n'a de sens QU'AVEC --serie : il journalise ce "
                 "que la CARTE emet sur le fil.")
    if args.journal_max_mo < 1:
        ap.error("--journal-max-mo doit valoir au moins 1.")
    # 🔴 BORNE SUPERIEURE — CORRECTIF DE REVUE 2026-08-28. Seul `< 1` etait
    #    refuse : `--journal-max-mo 100000` DESACTIVAIT la rotation en silence,
    #    sur l'AC qui exige de borner le volume AVANT de lancer. 2 Go est
    #    au-dela de tout debit plausible sur 7 j (le plus haut jamais mesure,
    #    163 o/s, donne ~98 Mo) : franchir ce plafond n'est pas un reglage,
    #    c'est une faute de frappe.
    if args.journal_max_mo > 2048:
        ap.error("--journal-max-mo %d Mo depasse le plafond de 2048 Mo. ⛔ Une "
                 "valeur pareille DESACTIVE la rotation en silence, et AC2.5 "
                 "exige que le volume soit BORNE AVANT de lancer."
                 % args.journal_max_mo)
    if args.tracer_console is not None and args.serie is None:
        ap.error("--tracer-console n'a de sens QU'AVEC --serie : il capture ce "
                 "que l'agent draine sur le FIL de la console, et ni --stdout "
                 "ni --ws n'en ont un. ⛔ Posé ici, il n'ecrirait JAMAIS rien.")

    # dn4-5/T4 — UN SEUL lisseur, quel que soit le transport : il vit entre la
    # PHOTO et la TRAME, ⛔ pas dans la sortie.
    lisseur = Lisseur(actif=(args.lissage == "on"))

    if args.serie is not None:
        if not args.serie.strip():
            ap.error("--serie attend un port (ex. COM3), pas une chaine vide")
        journal = (JournalSoak(args.journal_soak,
                               max_octets=args.journal_max_mo * 1024 * 1024)
                   if args.journal_soak else None)
        sortie = SortieSerie(args.serie, tracer=args.tracer_console,
                             journal=journal)
        if journal is not None:
            journal.evenement("DEPART", "agent demarre — journal du soak arme "
                                        "(fichier plafonne a %d Mo, %d crans "
                                        "=> retention %d Mo ; au-dela, le DEBUT "
                                        "de la fenetre est detruit et chaque "
                                        "rotation le dit)"
                              % (args.journal_max_mo, journal._rot,
                                 args.journal_max_mo * (journal._rot + 1)))
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

    # 🔬 dn4-18 — ⛔ UN TIR INSTRUMENTÉ NE DOIT JAMAIS POUVOIR PASSER POUR UN
    #    TIR DE RÉGIME. Le journal de la tour est cumulatif : sans cette ligne,
    #    un chiffre de coût relevé pendant une capture serait indiscernable
    #    d'un chiffre de régime — et « une mesure porte la date de son binaire »
    #    ne suffirait pas à les séparer, puisque c'est le MÊME binaire.
    if args.tracer_console:
        print("[agent] 🔬 TRACE CONSOLE ARMEE vers %s — ⛔ CE TIR EST "
              "INSTRUMENTE, ce n'est PAS un tir de regime (le fichier grossit "
              "d'environ 275 o/s)." % args.tracer_console, file=sys.stderr)

    moi = psutil.Process()

    # Amorçage deux-temps (le 1er cpu_percent vaut 0.0) + ouverture de la source
    # GPU. ⚠️ NON FATALE : sans GPU, les quatre autres métriques vivent.
    # ⚠️ `--lhm` est un point d'ENTREE d'exercice, ⛔ pas une option de confort :
    #    sans lui, eprouver « lecture lente » ou « service muet » exigerait de
    #    couper le VRAI LHM de la tour, donc un geste owner, pour un chemin de
    #    code. ⛔ Il ne dispense de RIEN : AC8 se joue sur le vrai service.
    # 🔴 VALIDES EN REVUE (2026-08-21). Pour une option dont le motif ecrit est
    #    « EXERCER les chemins d'echec », son PROPRE chemin d'echec etait un
    #    traceback nu : `--lhm hote:abc` levait un `ValueError` non rattrape avant
    #    meme la construction du `Collecteur`. Et `--lhm ::1` se decoupait en hote
    #    `:` port `1` — une adresse IPv6 acceptee EN SILENCE sous une autre.
    lhm_hote, lhm_port = LHM_HOTE, LHM_PORT
    if args.lhm:
        brut = args.lhm.strip()
        if brut.startswith("["):                       # [::1]:8085, forme RFC 3986
            fin_crochet = brut.find("]")
            if fin_crochet < 0:
                ap.error("--lhm : crochet ouvrant sans fermant dans %r" % brut)
            lhm_hote = brut[1:fin_crochet]
            reste = brut[fin_crochet + 1:]
            # 🔴 2e REVUE (2026-08-24) : `reste[1:] if reste.startswith(":") else ""`
            #    JETAIT EN SILENCE tout ce qui suit `]` sans commencer par `:`.
            #    `--lhm "[::1]xyz:9000"` rendait `port_txt = ""` donc le port PAR
            #    DEFAUT, et l'agent imprimait « LHM pointe sur ::1:8085 » pendant que
            #    l'operateur croyait avoir pose 9000. Le meme bloc refuse pourtant le
            #    crochet non ferme, l'IPv6 nu, le port non numerique et l'hote vide :
            #    la queue residuelle etait le SEUL cas sans branche.
            if reste and not reste.startswith(":"):
                ap.error("--lhm : caracteres inattendus apres `]` dans %r "
                         "(%r). Forme attendue : [ADRESSE]:PORT." % (brut, reste))
            port_txt = reste[1:] if reste.startswith(":") else ""
            if reste == ":":
                ap.error("--lhm : `:` sans port dans %r" % brut)
        elif brut.count(":") > 1:
            # ⛔ IPv6 NU : ambigu par construction (`::1` = hote `:` + port `1` ?).
            #    On REFUSE et on dit la forme attendue, ⛔ on ne devine pas.
            ap.error("--lhm : adresse IPv6 nue ambigue (%r). Utiliser [%s]:PORT."
                     % (brut, brut))
        else:
            hote_txt, sep, port_txt = brut.partition(":")
            lhm_hote = hote_txt or LHM_HOTE
            # ⚠️ MEME DEFAUT, AUTRE BRANCHE (2e revue) : `--lhm "hote:"` donnait
            #    `port_txt = ""` donc le port PAR DEFAUT, en silence.
            if sep and not port_txt:
                ap.error("--lhm : `:` sans port dans %r" % brut)
        if port_txt:
            if not port_txt.isdigit():
                ap.error("--lhm : port %r n'est pas un entier" % port_txt)
            lhm_port = int(port_txt)
            if not (1 <= lhm_port <= 65535):
                ap.error("--lhm : port %d hors de 1..65535" % lhm_port)
        if not lhm_hote:
            ap.error("--lhm : hote vide dans %r" % brut)
        print("[agent] ⚠️ LHM pointe sur %s:%d par --lhm — ⛔ ce n'est PAS la "
              "configuration de regime." % (lhm_hote, lhm_port), file=sys.stderr)

    # ⚠️ LE TIMEOUT EST BORNE DES DEUX COTES, ET LES DEUX BORNES ONT UN MOTIF.
    #    0 (ou negatif) rendait `reste <= 0` des la premiere iteration : LHM
    #    devenait definitivement illisible, mais compte comme un ECHEC DE LECTURE —
    #    un diagnostic qui envoie regarder le service au lieu de la ligne de
    #    commande. Et tout ce qui atteint PERIODE_S garantit le depassement de
    #    cadence a CHAQUE cycle, donc le recalage, donc l'echantillon jete.
    # 🔴 2e REVUE (2026-08-24) — `nan` PASSAIT LES DEUX BORNES, MESURE :
    #    `nan <= 0.0` vaut False ET `nan >= 1.0` vaut False. `argparse type=float`
    #    l'accepte. La suite posait `settimeout(nan)` qui leve `ValueError`,
    #    rattrapee par le `except Exception` de `_get` ⇒ LHM en panne PERMANENTE
    #    avec `motif = "ValueError: Invalid value NaN…"` — precisement le
    #    diagnostic « qui envoie regarder le service au lieu de la ligne de
    #    commande » que ces bornes existent pour empecher.
    # ⚠️ `inf`, lui, etait bien rattrape par `>= PERIODE_S`. ⛔ Une comparaison
    #    d'ordre ne borne PAS un NaN : il faut le tester pour lui-meme.
    if not _fini(args.lhm_timeout):
        ap.error("--lhm-timeout doit etre un nombre FINI (recu %r). ⛔ `nan` PASSE "
                 "LES DEUX BORNES ci-dessous (`nan <= 0` et `nan >= PERIODE_S` sont "
                 "FAUX tous les deux) et finit en panne LHM permanente, avec un "
                 "motif qui accuse le service. `inf` est refuse ici aussi, pour que "
                 "le motif dise la LIGNE DE COMMANDE et pas la periode."
                 % args.lhm_timeout)
    if args.lhm_timeout <= 0.0:
        ap.error("--lhm-timeout doit etre > 0 (recu %.3f) : a 0 la source est "
                 "illisible par construction, et ca se lirait comme une panne "
                 "de LHM." % args.lhm_timeout)
    if args.lhm_timeout >= PERIODE_S:
        ap.error("--lhm-timeout = %.3f s >= la periode (%.3f s) : chaque cycle "
                 "depasserait sa fenetre et armerait le recalage de cadence, qui "
                 "JETTE l'echantillon et re-amorce les cinq metriques."
                 % (args.lhm_timeout, PERIODE_S))
    collecteur = Collecteur(lhm_hote=lhm_hote, lhm_port=lhm_port,
                            lhm_timeout_s=args.lhm_timeout)

    # 🔴 dn4-18 — LA REPRISE D'HORLOGE. ⛔ Sur stdout et sur WebSocket il n'y a
    #    pas de canal console : l'absence est un ÉTAT DÉCLARÉ, et elle SE DIT
    #    au lancement comme au bilan. ⛔ Jamais un silence, jamais un
    #    `AttributeError`.
    horloge = ReprisHorloge(sortie)
    if not horloge.actif:
        print("[agent] ⚠️ horloge : AUCUN canal console sur la branche « %s » ⇒ "
              "la reprise d'heure de la carte est DESARMEE. ⛔ Ce n'est pas une "
              "panne : le REPL n'existe que sur --serie." % sortie.nom,
              file=sys.stderr)

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
    # ⚠️ Lu UNE fois : on ne re-teste pas `args.stop_si` a chaque tour pour
    #    rien quand l'option n'est pas posee.
    # 🔴 CORRECTIF DE REVUE DU 2026-08-26 — `args.stop_si or None` testait la
    #    VÉRACITÉ, pas la PRÉSENCE : c'est EXACTEMENT le défaut corrigé vingt
    #    lignes plus haut pour `--serie` (« `--serie ""` retombait EN SILENCE
    #    sur stdout »). Un `--stop-si ""` — que produit une expansion vide de
    #    `%DN_ARGS%` ou un lanceur mal cité — donnait un agent qu'on ne peut
    #    JAMAIS arrêter proprement : `stop` pose le drapeau, attend 8 s,
    #    `taskkill /PID`, puis `/F`, et annonce « LE BILAN EST PERDU » avec la
    #    mauvaise cause. ⇒ La chaîne vide est REFUSÉE À L'ANALYSE (voir
    #    `--stop-si` dans le parseur), et ici on teste la PRÉSENCE.
    drapeau_stop = args.stop_si if args.stop_si is not None else None
    motif_arret = None

    # =====================================================================
    # 🔴 LE BILAN ÉTAIT PERDU À L'EXTINCTION — MESURÉ LE 2026-08-26, ⛔ PAS DÉDUIT
    #    Protocole : agent lancé au logon (PID 3792), `dn-agent.log` à
    #    **74 379 o**, extinction COMPLÈTE de la tour SANS `dn-agent.bat stop`.
    #    Au rallumage, le journal fait 77 342 o — et **l'octet 74 380 est la
    #    PREMIÈRE LIGNE DU NOUVEL AGENT**. Entre les deux : RIEN. **0 octet.**
    #    ⚠️ Or l'extinction est la fin NORMALE de cet agent (décision owner
    #    n°1 : « tour éteinte, la dalle reste allumée »), et `--stop-si` ne
    #    tire QUE depuis `dn-agent.bat stop`. Le défaut que le dossier §25.8
    #    déclare fermé était donc ROUVERT sur le chemin quotidien.
    #    ✅ Contre-épreuve : le chemin PROPRE, lui, écrit toujours son bilan
    #    (1 384 / 853 / 855 o mesurés le même jour). Ce n'est pas l'écriture
    #    qui manquait, c'est le HANDLER à la terminaison de session.
    #
    # ⛔ POURQUOI PAS `signal.SIGTERM` : Windows ne le délivre pas au logoff.
    #    Le seul mécanisme qui l'est est `SetConsoleCtrlHandler`, sur
    #    `CTRL_LOGOFF_EVENT` (2) et `CTRL_SHUTDOWN_EVENT` (6).
    # ⚠️ ET LE HANDLER DOIT **BLOQUER** : rendre la main autorise Windows à
    #    terminer le process. Il pose donc le drapeau, puis ATTEND que la
    #    boucle ait imprimé le bilan — avec un plafond, parce que le système
    #    ne nous accorde que quelques secondes.
    # ⚠️ COÛT SUR LE BUDGET D'AC6 : NUL. Le handler est installé UNE FOIS et
    #    n'est jamais appelé en régime ; la boucle ne gagne qu'un `is_set()`
    #    par cycle (1 Hz).
    # =====================================================================
    arret_systeme = threading.Event()
    bilan_ecrit = threading.Event()
    _handler_ref = _armer_arret_systeme(arret_systeme, bilan_ecrit)

    try:
        while args.duree <= 0 or (time.monotonic() - depart) < args.duree:
            if arret_systeme.is_set():
                motif_arret = "fermeture de session Windows"
                break
            if drapeau_stop is not None and os.path.exists(drapeau_stop):
                motif_arret = drapeau_stop
                break
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
            # 🔴 dn4-5/T4 — LE LISSAGE S'APPLIQUE ICI, ENTRE LA PHOTO ET LA TRAME.
            #    ⇒ le fil porte la valeur LISSÉE pour les quatre grandeurs
            #      verdictées, et la valeur BRUTE pour les douze autres.
            #    ⚠️ La GÉNÉRATION d'ouverture du port lui dit quand VIDER sa
            #      fenêtre (AC4.3) — ⛔ pas le drapeau `reprise_liaison`, qui est
            #      consommé ailleurs.
            # ⛔ ACCES DIRECT, ⛔ PLUS `getattr(..., 0)` : le defaut silencieux
            #    transformait « ce transport n'a pas de garde AC4.3 » en
            #    « generation constante », c'est-a-dire en lissage JAMAIS vide.
            #    `ouvertures` est un contrat de tous les transports ; qu'un
            #    `AttributeError` sorte au premier cycle vaut infiniment mieux
            #    qu'une valeur perimee republiee pendant sept jours.
            photo = lisseur.appliquer(photo, sortie.ouvertures)
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

            # 🔴 dn4-18 — LA REPRISE D'HORLOGE, UNE FOIS PAR CYCLE (1 Hz), ⛔ PAS
            #    UNE FOIS PAR TRAME (ce serait 5 Hz, et le plancher d'AC4.3
            #    deviendrait le SEUL rempart au lieu du second).
            # ⚠️ Elle est appelée MÊME quand l'envoi vient d'échouer : c'est
            #    elle qui doit voir le port revenir (`reprise_liaison`), et
            #    ses envois échouent proprement en `LiaisonEnAttente` tant que
            #    le backoff court.
            horloge.cycle(time.monotonic())

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
        # ⚠️ On DIT pourquoi on s'arrête. Sans ça, dans un journal, un arrêt
        #    demandé et une panne se ressemblent — et le bilan qui suit ne
        #    dirait pas lequel des deux il décrit.
        if motif_arret is not None:
            print("[agent] arrêt demandé (%s)" % motif_arret, file=sys.stderr)
        _bilan(sortie, depart, trames_emises, erreurs_envoi, rattrapages,
               collecteur, horloge)
        collecteur.fermer()
        # ⚠️ DÉBLOQUE LE HANDLER DE FERMETURE DE SESSION : tant qu'il n'a pas
        #    la main, Windows attend. C'est ce qui laisse le bilan sortir.
        try:
            sys.stderr.flush()
        except Exception:
            pass
        bilan_ecrit.set()
        del _handler_ref   # garde la référence vivante jusqu'ici (ctypes)
    return 0


def _chemin_non_vide(v: str) -> str:
    """Refuse une valeur d'option VIDE, à l'analyse. (revue du 2026-08-26)

    🔴 LE MÊME DÉFAUT A ÉTÉ CORRIGÉ DEUX FOIS DANS CE FICHIER, à vingt lignes
       d'écart, et la seconde occurrence a survécu à la première :
         · `--serie ""` retombait EN SILENCE sur stdout (corrigé le 2026-08-19) ;
         · `--stop-si ""` désactivait EN SILENCE l'arrêt propre (mesuré ici).
       Dans les deux cas la cause est la même : `args.X or None` teste la
       VÉRACITÉ là où il fallait tester la PRÉSENCE. ⛔ Une option posée avec
       une valeur vide est une **erreur de lanceur**, jamais une demande de
       désactivation — la taire produit un agent inarrêtable, et `stop` accuse
       alors l'agent d'avoir ignoré un drapeau qu'il n'a jamais eu à lire.
    ⇒ On refuse À L'ANALYSE : c'est le seul endroit qui couvre TOUS les
      appelants (le `.bat`, la tâche, la main de l'owner) d'un seul geste.
    """
    if v is None or v.strip() == "":
        raise argparse.ArgumentTypeError(
            # (!) MESSAGE EN ASCII PUR : il s'affiche dans une console cmd.exe,
            #     dont la page de code rend un "interdit" comme \u26d4. Un
            #     diagnostic illisible la ou il s'affiche n'est pas un diagnostic.
            "valeur VIDE refusee : une option posee doit porter un chemin. "
            "Pour ne pas l'utiliser, ne pas la poser du tout.")
    return v


def _armer_arret_systeme(arret: "threading.Event",
                         bilan_ecrit: "threading.Event"):
    """Fait sortir le bilan quand Windows ferme la session. (revue 2026-08-26)

    🔴 MESURÉ, ⛔ PAS DÉDUIT : extinction complète de la tour sans
       `dn-agent.bat stop`, journal à 74 379 o avant, 77 342 o après — et le
       premier octet écrit après la coupure est la PREMIÈRE LIGNE DU NOUVEL
       AGENT. **0 octet de bilan.** Or l'extinction est la fin NORMALE d'un
       agent permanent.

    ⛔ POURQUOI PAS `signal.SIGTERM` : Windows ne le délivre pas au logoff. Le
       seul mécanisme qui l'est pour un process console est
       `SetConsoleCtrlHandler`.
    ⚠️ ET LE HANDLER DOIT BLOQUER. Rendre la main autorise le système à
       terminer le process : il pose donc le drapeau puis ATTEND que la boucle
       ait imprimé le bilan, avec un plafond — le système ne nous accorde que
       quelques secondes, et un handler qui ne rend jamais la main serait pire
       que le défaut qu'il corrige.
    ⚠️ ON NE TOUCHE PAS À Ctrl+C : les événements 0 et 1 rendent `False`, donc
       le comportement par défaut (KeyboardInterrupt) survit intact — c'est lui
       que le correctif du 2026-08-16 avait mis en place.
    ⇒ Rend l'objet callback, que l'appelant DOIT garder vivant : `ctypes` ne
      détient pas de référence, et un ramasse-miettes le libérerait sous
      Windows, qui appellerait alors une adresse morte.
    """
    if sys.platform != "win32":
        return None
    CTRL_CLOSE, CTRL_LOGOFF, CTRL_SHUTDOWN = 2, 5, 6
    fabrique = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_uint)

    def _sur_evenement(evt):
        if evt in (CTRL_CLOSE, CTRL_LOGOFF, CTRL_SHUTDOWN):
            arret.set()
            bilan_ecrit.wait(4.0)
            return True
        return False   # Ctrl+C / Ctrl+Break : comportement par défaut

    rappel = fabrique(_sur_evenement)
    try:
        if not ctypes.windll.kernel32.SetConsoleCtrlHandler(rappel, True):
            print("[agent] /!\\ SetConsoleCtrlHandler a échoué : le bilan de fin "
                  "sera PERDU si la session se ferme sans `stop`.", file=sys.stderr)
            return None
    except Exception as e:
        print("[agent] /!\\ pas de handler de fermeture de session (%s) : le bilan "
              "sera PERDU a l'extinction." % e, file=sys.stderr)
        return None
    return rappel


def _bilan(sortie, depart: float, seq: int, erreurs_envoi: int, rattrapages: int,
           collecteur=None, horloge=None) -> None:
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
        journal = getattr(sortie, "_journal", None)
        sortie.fermer()  # dernier drain AVANT de publier le chiffre
        # 🔴 LA SANTE DE LA BOITE NOIRE SE PUBLIE ICI — correctif de revue
        #    2026-08-28. Une boite noire cassee se decouvrait en OUVRANT le
        #    fichier au jour 7 : c'est trop tard, la fenetre est perdue.
        if journal is not None:
            etat = journal.sante()
            grave = (journal._echecs_ecriture or journal._echecs_rotation)
            print(f"[agent] {'🔴' if grave else '✅'} boite noire du soak : {etat}",
                  file=sys.stderr)
            if grave:
                print("[agent]    ⛔ LE JOURNAL N'EST PAS COMPLET. Un echec "
                      "d'ecriture ou une rotation refusee signifie que la "
                      "fenetre d'observation a des TROUS — ⛔ ne pas conclure "
                      "sur « 0 reboot » a partir d'un journal troue.",
                      file=sys.stderr)
        print(f"[agent] écho console draîné : {sortie.echo_octets} o, "
              f"{sortie.echo_lignes} lignes en {mur:.1f} s "
              f"= {sortie.echo_octets / mur:.1f} o/s, "
              f"{sortie.echo_lignes / mur:.2f} lignes/s "
              f"(PLAFOND du bruit console : inclut le battement 10 s et tout ESP_LOGx)",
              file=sys.stderr)
        # Le firmware a-t-il ACCEPTÉ ce qu'on lui a envoyé ? « n trames émises » ne
        # l'a jamais dit — seul ce compteur distingue un envoi d'une acceptation.
        # 🔴 dn4-18, CORRECTIF DE REVUE 2026-08-26 — CE COMPTEUR NE DIT PLUS
        #    « TRAMES », ET IL NE LE PEUT PLUS. Le marqueur `non-zero error
        #    code` est rendu par le REPL pour TOUTE commande console qui sort
        #    non nulle. Jusqu'a dn4-18 l'agent n'envoyait que des `pc …`, donc
        #    « n refus = n trames refusees » etait VRAI. Depuis, il envoie aussi
        #    `rtc` et `rtc set`, et `cmd_rtc` sort a 1 sur QUATRE chemins de
        #    refus (dn_console.c:7352-7390). ⇒ le bilan annoncait « N trame(s)
        #    REFUSEE(S) » alors que ZERO trame avait ete refusee.
        # ✅ LA DECOMPOSITION EST EXACTE, ⛔ pas approchee : `rtc` nu rend 0 sur
        #    tous ses chemins, donc seul un `rtc set` REFUSE ajoute un marqueur,
        #    et chacun est deja compte a part par `poses_refusees` — lu, lui, sur
        #    le VERDICT ANCRE de la carte et non sur le marqueur du REPL.
        refus_horloge = horloge.poses_refusees if horloge is not None else 0
        if sortie.refus_firmware:
            reste = sortie.refus_firmware - refus_horloge
            print(f"[agent] 🔴 {sortie.refus_firmware} commande(s) console REFUSÉE(S) "
                  f"par le firmware (marqueur `non-zero error code` sur le fil)",
                  file=sys.stderr)
            print(f"[agent]    ⇒ dont {refus_horloge} pose(s) d'horloge ⇒ "
                  f"{reste} imputable(s) aux trames `pc`. ⛔ « n trames émises » "
                  f"ne prouve que n ÉCRITURES, pas n acceptations.",
                  file=sys.stderr)
            if reste < 0:
                print("[agent]    ⚠️ DÉCOMPTE NÉGATIF : des marqueurs ont été "
                      "perdus (drain manqué pendant un backoff). ⛔ Le total "
                      "ci-dessus est un PLANCHER, pas un compte.", file=sys.stderr)
        else:
            print("[agent] aucun refus de commande console signalé par le firmware "
                  "sur le fil (ni trame `pc`, ni pose d'horloge)", file=sys.stderr)
        # ⚠️ dn4-18 — LA SANTÉ DE L'INSTRUMENT LUI-MÊME. Une troncature de ligne
        #    ne sort JAMAIS en silence : elle voudrait dire que le tampon borné
        #    a jeté du texte, donc qu'un état a PU être manqué.
        if sortie.horloge.lignes_tronquees:
            print(f"[agent] 🔴 {sortie.horloge.lignes_tronquees} ligne(s) console "
                  f"TRONQUEE(S) a {DN_H_LIGNE_MAX} o — un etat d'horloge a PU "
                  f"etre manque. ⚠️ La plus longue ligne mesuree valait 483 o : "
                  f"si ce compteur bouge, la borne est a revoir.", file=sys.stderr)
    else:
        sortie.fermer()
    # =====================================================================
    # 🔴 dn4-18 — L'HORLOGE. TROIS FAITS DISTINCTS, TROIS LIGNES — ⛔ JAMAIS
    #    FONDUS EN UNE (AC5.1). C'est la doctrine déjà écrite pour LHM : « trois
    #    diagnostics qui envoient chercher à trois endroits différents ».
    # ⛔ ET UN COMPTEUR À ZÉRO SE DIT AUSSI (AC5.2) : un paragraphe absent est
    #    indiscernable d'un mécanisme MORT.
    # 🔴 ET LE CAS « JAMAIS DÉCLENCHÉ » DOIT ÊTRE LISIBLE (AC5.3) : une session
    #    entière sans une seule pose est le régime NORMAL (la carte n'a pas été
    #    débranchée) — et c'est EXACTEMENT ce que produirait aussi un mécanisme
    #    cassé. ⇒ le bilan dit ce que l'agent a **LU**, pas seulement ce qu'il
    #    a **FAIT**.
    # =====================================================================
    if horloge is not None:
        if not horloge.actif:
            print("[agent] horloge : reprise DESARMEE (aucun canal console sur "
                  "la branche « %s ») — ⛔ etat declare, pas une panne."
                  % sortie.nom, file=sys.stderr)
        else:
            lect = sortie.horloge
            age = ("il y a %.0f s" % (time.monotonic() - lect.etat_instant)
                   if lect.etat_instant is not None else "jamais")
            # 1/3 — CE QUE L'AGENT A LU.
            print(f"[agent] horloge LUE : dernier etat « {lect.etat} »"
                  f"{' (' + lect.etat_texte + ')' if lect.etat_texte else ''}, "
                  f"{age} — {lect.etats_lus} lecture(s) d'etat sur "
                  f"{horloge.interrogations} interrogation(s) `rtc`",
                  file=sys.stderr)
            if lect.etats_lus == 0:
                print("[agent]    ⚠️ AUCUN etat lu de toute la session : la carte "
                      "n'a jamais rendu de ligne d'horloge reconnue. ⛔ Ce n'est "
                      "PAS « tout va bien » — c'est INCONNU (AC3.2).",
                      file=sys.stderr)
            if lect.lue_texte is not None:
                # ⚠️ `ecart_max_vu` n'est alimenté QUE sur les lectures faites
                #    en `OS0` — comparer l'heure d'une carte qui dit `OS=1`
                #    n'aurait aucun sens (elle vaut 2000-01-01). Il peut donc
                #    être vide alors que `lue` ne l'est pas, et on le DIT au
                #    lieu de planter sur un format.
                maxi = ("%.0f s" % horloge.ecart_max_vu
                        if horloge.ecart_max_vu is not None
                        else "aucun (jamais lue en OS=0)")
                print(f"[agent] horloge VUE : la carte disait « {lect.lue_texte} » "
                      f"(ecart carte-tour {lect.lue_ecart_s:+d} s ; ecart MAX vu "
                      f"{maxi} ; seuil ete/hiver "
                      f"{DN_H_SEUIL_ECART_S:.0f} s)", file=sys.stderr)
            # 2/3 — CE QUE L'AGENT A FAIT.
            if horloge.poses_tentees == 0:
                print("[agent] horloge : AUCUNE pose tentee — c'est le regime "
                      "NORMAL quand la carte n'a pas perdu l'heure. ⚠️ Le lire "
                      "avec la ligne « horloge LUE » ci-dessus : c'est elle qui "
                      "distingue « rien a faire » de « mecanisme mort ».",
                      file=sys.stderr)
            else:
                détail = " · ".join("%s=%d" % (k, v) for k, v in
                                    sorted(horloge.motifs_pose.items()))
                print(f"[agent] horloge POSEE : {horloge.poses_tentees} tentative(s) "
                      f"— {horloge.poses_reussies} reussie(s), "
                      f"{horloge.poses_refusees} refusee(s), "
                      f"{horloge.poses_sans_reponse} sans reponse "
                      f"({détail})", file=sys.stderr)
            # 3/3 — POURQUOI ÇA A ÉCHOUÉ, QUAND ÇA A ÉCHOUÉ.
            if horloge.motifs_refus:
                détail = " · ".join("%s=%d" % (k, v) for k, v in
                                    sorted(horloge.motifs_refus.items()))
                print(f"[agent] 🔴 horloge : motifs de REFUS rendus par la carte : "
                      f"{détail}", file=sys.stderr)
            else:
                print("[agent] horloge : aucun refus de pose signale par la carte",
                      file=sys.stderr)
            # 🔴 CORRECTIF DE REVUE 2026-08-26 — CES DEUX-LA SE TAISAIENT A
            #    ZERO, VINGT LIGNES SOUS LE COMMENTAIRE QUI L'INTERDIT (AC5.2).
            #    « Un paragraphe absent est indiscernable d'un mecanisme MORT »
            #    vaut pour eux comme pour les trois autres lignes du bloc.
            if horloge.erreurs_canal:
                print(f"[agent] 🔴 horloge : {horloge.erreurs_canal} echec(s) du "
                      f"CANAL de commande console (⛔ distinct d'un refus : la "
                      f"carte n'a peut-etre jamais recu la commande)",
                      file=sys.stderr)
            else:
                print("[agent] horloge : aucun echec du CANAL de commande console",
                      file=sys.stderr)
            print(f"[agent] horloge : {sortie.commandes_console} commande(s) "
                  f"console emise(s), {sortie.commandes_echouees} en echec "
                  f"— ⛔ HORS `trames_emises` (le debit publie ci-dessus "
                  f"decrit les trames, et rien d'autre)", file=sys.stderr)
            if horloge.poses_rapprochees:
                print(f"[agent] 🔴 horloge : {horloge.poses_rapprochees} pose(s) "
                      f"REUSSIE(S) RAPPROCHEE(S) — la carte a REPERDU l'heure "
                      f"apres une pose acceptee. ⛔ Ce n'est pas un refus, et "
                      f"l'escalade a ete armee dessus.", file=sys.stderr)
            if lect.ruptures:
                print(f"[agent] horloge : {lect.ruptures} rupture(s) de fil — "
                      f"le fragment de ligne en vol a ete JETE, ⛔ pas recolle "
                      f"au flux suivant", file=sys.stderr)
    if collecteur is not None:
        # ⛔ UN ÉCRÊTAGE NE SORT JAMAIS EN SILENCE. S'il y en a, la valeur
        #    affichée n'est plus la valeur mesurée — c'est une information, pas
        #    un détail d'implémentation.
        if collecteur.non_publiees:
            détail = " · ".join(f"{k}={v}" for k, v in
                                sorted(collecteur.non_publiees.items()))
            print(f"[agent] ⚠️ GRANDEURS LHM LUES MAIS NON PUBLIEES (la position 0 "
                  f"de leur metrique manquait — ⛔ ce n'est PAS une absence LHM, "
                  f"LHM les a rendues) : {détail}", file=sys.stderr)
            print("[agent]    ⇒ les tr/min voyagent dans `disk` : sans `Mo/s`, la "
                  "metrique n'est pas emise et les ventilos disent « -- ». "
                  "⛔ Structurel et ASSUME (regle « aucune grandeur LHM en "
                  "position 0 »), ⛔ pas un defaut.", file=sys.stderr)
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
            print(f"[agent] 🔴 PANNES DE SOURCE (grandeur perdue ⇒ champ VIDE, "
                  f"« -- » sur SA ligne ; metrique non emise SEULEMENT si la "
                  f"position 0 manquait) : {détail}", file=sys.stderr)
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
                # 🔴 CE MESSAGE DISAIT « le plafond a probablement COUPE une
                #    lecture » MEME QUAND `echecs == 0` — c'est-a-dire quand les
                #    donnees PROUVENT le contraire : une lecture coupee ECHOUE,
                #    donc elle serait comptee. Corrige le 2026-08-21, en seance,
                #    apres l'avoir vu imprimer sur un tir a 0 echec.
                # ⛔ C'est la famille « une cause plausible imprimee par le
                #    produit qui tourne » que dn4-7 a deja payee. Un message
                #    d'alerte qui contredit son propre compteur est PIRE que pas
                #    d'alerte : il envoie chercher un defaut qui n'existe pas.
                # 🔴 2e REVUE (2026-08-24) — LA 3e BRANCHE ETAIT UN `elif` DE
                #    `if lhm.echecs:`, DONC MASQUEE DES QU'IL EXISTAIT **UN SEUL**
                #    ECHEC. Or son motif — « le chrono couvre desormais le PARSE,
                #    donc une lecture peut REUSSIR au-dela du plafond » — est
                #    INDEPENDANT du nombre de timeouts reseau. Session a 1 timeout
                #    (0,60 s) + 1 lecture reussie a 1,20 s : la branche 1 imprimait
                #    « le plafond a COUPE au moins une lecture (max 1200 ms pour un
                #    timeout de 600 ms) » — le plafond a coupe a 600, ⛔ pas a 1200,
                #    et le message envoyait revoir le DIMENSIONNEMENT RESEAU alors
                #    que le depassement venait du parse.
                # ⚠️ ET `duree_max` EST UN MAX SUR LES REUSSITES **ET** LES ECHECS
                #    CONFONDUS (`_chrono` est appele dans le `finally` de `lire()`).
                #    Rien ne permettait de savoir de laquelle il venait — donc on ne
                #    l'affirme plus : les deux constats sont DISJOINTS et cumulables.
                if lhm.duree_max >= lhm.timeout_s * 0.9:
                    if lhm.echecs:
                        print(f"[agent] 🔴 le plafond a COUPE au moins une lecture "
                              f"({lhm.echecs} echec(s), timeout "
                              f"{lhm.timeout_s*1000.0:.0f} ms). ⚠️ Le dimensionnement "
                              f"est a revoir. ⛔ `duree_max` "
                              f"({lhm.duree_max*1000.0:.0f} ms) est un MAX sur les "
                              f"reussites ET les echecs : il ne dit PAS a quel "
                              f"instant la coupe a eu lieu.", file=sys.stderr)
                    if lhm.duree_max > lhm.timeout_s:
                        # 🔴 TROISIEME BRANCHE, AJOUTEE EN REVUE (2026-08-21). Les
                        #    deux precedentes supposaient `duree_max > timeout ⇒
                        #    echecs > 0`. C'EST FAUX, et le meme correctif le
                        #    prouve : le chrono couvre desormais le PARSE, qui n'est
                        #    borne par aucun timeout. Une lecture peut donc REUSSIR
                        #    au-dela du plafond.
                        # ⛔ Sans cette branche, le bilan imprimait « atteint 333 %
                        #    du timeout ... La marge est mince, ⛔ pas un incident » —
                        #    arithmetiquement contradictoire, et il DETOURNAIT le
                        #    lecteur du seul depassement reel. Meme famille que le
                        #    message corrige trois lignes plus haut.
                        print(f"[agent] 🔴 UNE LECTURE LHM A DEPASSE LE PLAFOND SANS "
                              f"ECHOUER : {lhm.duree_max*1000.0:.0f} ms pour un timeout "
                              f"de {lhm.timeout_s*1000.0:.0f} ms "
                              f"({lhm.duree_max/lhm.timeout_s*100.0:.0f} %), "
                              f"{lhm.echecs} echec(s). ⚠️ Le budget ne borne que le "
                              f"RESEAU : ce depassement vient d'ailleurs (parse, "
                              f"ordonnancement). ⛔ C'EST un incident — il mange la "
                              f"cadence et arme le recalage.", file=sys.stderr)
                    elif not lhm.echecs:
                        print(f"[agent] ⚠️ la lecture LHM la plus longue "
                              f"({lhm.duree_max*1000.0:.0f} ms) atteint "
                              f"{lhm.duree_max/lhm.timeout_s*100.0:.0f} % du timeout, "
                              f"mais AUCUNE n'a echoue : rien n'a ete coupe. "
                              f"⛔ La marge est mince, et c'est ca l'information — "
                              f"⛔ pas un incident.", file=sys.stderr)
            if lhm.reponses == 0:
                print(f"[agent] ⚠️ LHM est reste INJOIGNABLE toute la session "
                      f"({lhm.motif}) — la °C CPU et les tr/min n'ont JAMAIS ete "
                      f"publies. ⛔ Ce n'est pas « zero », c'est « inconnu » : le "
                      f"fil porte un champ VIDE et la carte affiche « -- ».",
                      file=sys.stderr)
            # 🔴 LE DESACCORD DE FORMAT SE DIT **AVANT** L'ABSENCE, ET IL LA
            #    DISQUALIFIE. Ajoute en revue (2026-08-21) : sans lui, un parseur
            #    en desaccord avec `/metrics` produisait cinq « absences » et
            #    envoyait l'operateur inspecter SES CAPTEURS. ⛔ Deux diagnostics
            #    contraires qui envoient chercher a deux endroits differents.
            if lhm.lignes_illisibles:
                print(f"[agent] 🔴 {lhm.lignes_illisibles} ligne(s) `lhm_` sur "
                      f"{lhm.lignes_lues} n'ont PAS PU ETRE LUES par le parseur. "
                      f"⛔ NE PAS LIRE LES « ABSENCES » CI-DESSOUS COMME DES "
                      f"CAPTEURS MUETS : le format de /metrics et ce parseur ne "
                      f"sont pas d'accord. Regarder /metrics EN PREMIER.",
                      file=sys.stderr)
            # 🔴 2e REVUE (2026-08-24) — TROIS ETATS QUITTENT LE SEAU DES
            #    ABSENCES, PARCE QU'AUCUN N'EST UNE ABSENCE. La doctrine du depot
            #    est « chaque cas sur SON compteur » ; l'en-tete « LHM a REPONDU,
            #    SANS cette valeur » envoie inspecter un capteur, et c'etait faux
            #    pour les trois. Chacun se dit AVANT les absences, et les
            #    DISQUALIFIE — comme le desaccord de format juste au-dessus.
            if lhm.familles:
                détail = " · ".join(f"{k}={v}" for k, v in
                                    sorted(lhm.familles.items()))
                print(f"[agent] 🔴 UNITE CHANGEE COTE LHM (la valeur A ETE RENDUE, "
                      f"sous une AUTRE famille — REFUSEE, ⛔ jamais republiee sous "
                      f"l'ancienne etiquette) : {détail}. ⛔ NE PAS INSPECTER LES "
                      f"CAPTEURS : regarder la configuration d'unites de LHM.",
                      file=sys.stderr)
            if lhm.doublons:
                détail = " · ".join(f"{k}={v}" for k, v in
                                    sorted(lhm.doublons.items()))
                print(f"[agent] 🔴 CONFLIT D'UNITE DANS /metrics (deux familles pour "
                      f"la MEME sonde — valeur REFUSEE, ⛔ pas tranchee au hasard "
                      f"par l'ordre des lignes) : {détail}", file=sys.stderr)
            if lhm.bornages_impossibles:
                print(f"[agent] 🔴 {lhm.bornages_impossibles} lecture(s) LHM N'ONT PAS "
                      f"PU ETRE BORNEES (aucune socket joignable). ⛔ Sur celles-la le "
                      f"budget de {lhm.timeout_s*1000.0:.0f} ms n'a PAS ete applique : "
                      f"un depassement de `duree_max` vient de LA, ⛔ pas du parse.",
                      file=sys.stderr)
            if lhm.absences:
                détail = " · ".join(f"{k}={v}" for k, v in
                                    sorted(lhm.absences.items()))
                print(f"[agent] ⚠️ ABSENCES LHM (LHM a REPONDU, sans cette "
                      f"valeur — champ VIDE sur le fil, ⛔ PAS une panne) : "
                      f"{détail}", file=sys.stderr)
            elif (lhm.reponses and not lhm.lignes_illisibles
                  and not lhm.familles and not lhm.doublons):
                # ⚠️ 2e REVUE : les trois nouveaux seaux DISQUALIFIENT aussi cette
                #    phrase. Sans eux, « aucune absence LHM : les cinq sondes ont
                #    rendu une valeur » pouvait s'imprimer pendant qu'une unite
                #    avait change sous nos pieds.
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

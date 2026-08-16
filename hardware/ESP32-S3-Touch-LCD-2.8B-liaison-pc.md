# §12 — La liaison PC : LA FOURCHE TRANSPORT, tranchée le 2026-08-16 (dn2-2, P5)

Fichier frère du fichier d'autorité `ESP32-S3-Touch-LCD-2.8B-affichage.md`, référencé
depuis lui. Il consigne la décision la plus structurelle de la V1 : **le transport
agent PC → carte est l'USB série (branche A), par la console REPL**. Tout ce que dn3
et dn4-1 construisent en hérite.

---

## 12.1 Les critères d'arbitrage — écrits AVANT la mesure

Posés dans la story dn2-2 (AC5) le 2026-08-16, avant le premier chiffre :

1. **RAM interne consommée** (117 995 o libres au départ, réserve DMA
   `SPIRAM_MALLOC_RESERVE_INTERNAL` = 32 768 o)
2. **Stabilité de l'image à l'œil** (le `fps` est aveugle au défaut §11.4)
3. **Coût CPU** (repos dashboard : 0,9 % en dn1-4)
4. **Coût en dépendances et en binaire** (790 736 o au départ, 81 % libres)
5. **Friction de développement au quotidien** (boucle build/flash/mesure)
6. **Robustesse de la reprise** (liaison morte → vivante sans reboot)
7. **Ce que ça prépare pour la suite** (dn4-1 : 6 métriques, reconnexions, H24)

## 12.2 Branche B (WiFi WebSocket) — ÉLIMINÉE PAR BLOCAGE MESURÉ (verrou 1)

Maquette complète jouée : `esp_wifi` STA + `esp_http_server` en serveur WebSocket
(`/dn`, port 80), agent Windows en client sortant. **Elle a fonctionné de bout en
bout** (35/35 trames, image stable à l'œil) — c'est la RAM qui la tue, pas le bus.

### Le déroulé mesuré de la RAM interne (config WiFi par défaut)

| Étape | RAM interne libre | Delta annoncé par l'instrument | Delta de la colonne |
|---|---:|---:|---:|
| dn1-4, baseline (firmware sans réseau) | 118 575 o | — | — |
| Binaire dn2-2 avec pile LIÉE, avant tout init | 65 095 o | **−53 480 o (au LINK, en `.bss`)** | −53 480 |
| `esp_wifi_init()` + `esp_wifi_start()` | 25 259 o | −39 800 o | −39 836 |
| CONNECTÉE (tampons RX vivants) | 14 463 o | −10 800 o | −10 796 |
| + serveur WebSocket (`httpd_start`) | **6 407 o** | −7 928 o | −8 056 |
| Sous churn de reconnexion (client mort) | **3 795 o** | — | — |

> ⚠️ **LES DEUX COLONNES DE DELTA NE SE RÉCONCILIENT PAS, ET C'EST NORMAL — mais ça
> n'était pas écrit** (correctif de la revue de code du 2026-08-16, qui l'a relevé au
> centime : écarts de 36, 4 et **128** octets). Ce sont **deux instruments distincts**,
> lus à des instants distincts : la colonne « RAM interne libre » vient de la commande
> `mem` de la console, la colonne « Delta annoncé » des `printf` de `imprimer_mem()`
> dans `dn_wifi.c` (`:151-153`, `:267-270`), pris **à l'intérieur** de `dn_wifi_on()` /
> `dn_wifi_ws_on()` — donc avant que les allocations transitoires de la séquence soient
> retombées. Présentées côte à côte sans cette phrase, elles se lisaient comme une chaîne
> d'étapes qui ne peut pas être vraie : une étiquette qui ment au sens du §13.
> **Le verdict, lui, ne dépend d'aucun des deux deltas** : il tient au chiffre ABSOLU de
> 6 407 o (3 795 sous churn) face à la réserve DMA de 32 768 o.

⇒ La réserve DMA de 32 768 o est **violée de fait** dès la connexion. À 6 407 o
libres, le premier `malloc` interne un peu gourmand (un `set bounce`, une trace,
une pile de tâche) tombe. **Injouable pour un produit qui doit encore construire
dn3 et dn4-1.**

- Coût flash : binaire 790 720 → **1 374 384 o** (+583 664 o), 81 % → 67 % libre.
- **La variante « qui sauve la RAM » (`CONFIG_SPIRAM_TRY_ALLOCATE_WIFI_LWIP=y`) est
  RÉFUTÉE PAR PIRE** : `esp_wifi_init` échoue en `ESP_ERR_NO_MEM` — symptôme au
  caractère près : `W wifi:malloc buffer fail` · `E wifi:Expected to init 16 rx
  buffer, actual is 4`. Les tampons RX statiques exigent de la RAM interne DMA que
  ce chemin d'allocation ne fournit plus. **La pile ne démarre pas du tout.**

### Les deux autres verrous, joués quand même (pour l'archive)

- **Verrou 2 (l'image)** : STABLE à l'œil de l'owner sous trafic WebSocket réel
  (témoin positif : 35 messages comptés + case CPU vivante à l'écran pendant le
  constat). ⚠️ **ET C'EST TOUT CE QUE ÇA DIT** (correctif de la revue de code du
  2026-08-16). La phrase d'origine — « *le bounce buffer tient donc aussi contre le
  trafic WiFi* » — était une **généralisation que le stimulus ne porte pas** : 35
  messages de ~30 octets à 1 Hz, c'est **~30 o/s**, quand le BONUS §5.3 de cette
  MÊME story établit que le régime qui fait défiler l'image est **165 343 o/s
  soutenus**, soit ~5 500× plus. Le témoin positif prouve que **les trames
  arrivent**, pas que **le bus est sollicité** : c'est exactement le piège que le
  §13 nomme (« cet instrument PEUT-IL voir le défaut qu'il prétend exclure ? »).
  ⇒ **Ce qui est établi** : sous CE régime, rien vu à l'œil. **Ce qui ne l'est
  pas** : la tenue du bounce sous un trafic WiFi soutenu — non joué. La branche
  étant écartée sur la RAM, la question reste **ouverte** et ne coûte rien
  aujourd'hui ; elle redevient un prérequis si B revient. Même prudence pour la
  phrase jumelle d'AC3 sur le trafic USB 1 Hz (§12.3).
- **Verrou 3 (écriture flash)** : CONSTATÉ au premier `esp_wifi_start()`, dalle
  allumée : `W phy_init: failed to load RF calibration data (0x1102), falling back
  to full calibration` puis `I phy_init: Saving new calibration data due to checksum
  failure or outdated calibration data, mode(2)` — **une écriture NVS pendant
  l'affichage, D4 violé**. Pas de défilement vu sur cette écriture COURTE (ce n'est
  pas le stimulus soutenu de §5.3). Parade en réserve dans `sdkconfig.defaults` :
  `CONFIG_ESP_PHY_CALIBRATION_AND_DATA_STORAGE=n` — OBLIGATOIRE si B revient.
- **Sens de la connexion** : ESP serveur / agent client sortant. Vérifié : le
  sortant Windows traverse le LAN **malgré les trois tunnels** (Surfshark WireGuard,
  OpenVPN DCO, Tailscale) — 40 s de trafic sans une erreur, constaté et pas supposé.
- **Témoin console** : `cfg` a répondu pendant TOUTE la campagne WiFi —
  `CONFIG_ESP_PHY_ENABLE_USB=y` tient sa promesse.
- 🔴 **Défaut de reprise serveur, mesuré** : après un client tué net, les poignées
  de main suivantes tombent en `timed out during handshake` — les sockets mortes ne
  sont pas purgées (correctif identifié : `lru_purge_enable = true`, posé dans la
  maquette avant son écartement).
- ⚠️ Épisode SSID : `loulouland` ⇒ raison 201 (NO_AP_FOUND) en boucle (~2,4 s par
  scan). Le SSID 2,4 GHz réel est `Internet-loulouLand` — la casse compte.
- 🔴 Piège d'implémentation payé cher : un netif orphelin d'un `wifi on` échoué fait
  `assert esp_netif_create_default_wifi_sta (duplicate key)` ⇒ **panique, carte
  haltée, plus de console ni de flash** (récupération : RESET physique + rejeu
  wsl-attach). Les chemins d'erreur de `dn_wifi.c` nettoient désormais tout.

## 12.3 Branche A (USB série CDC) — RETENUE, et ses trois cohabitations mesurées

**Le transport est le REPL lui-même** : l'agent envoie `pc $DN,…` sur COM3 — il
parle le dialecte de la console, la commande `pc` route la trame vers `dn_link`.
Aucun canal séparé, aucun composant, aucune ligne de sdkconfig.

### Cohabitation 1 — avec le REPL : le bruit est chiffré

Régime 1 Hz mesuré sur 45 s : **49,3 o/s, 1,09 lignes/s** ajoutés au flux console
(écho de la commande + invite ; le battement 10 s compte pour ~0,1 ligne/s).
Reproductible : 42,3-49,3 o/s sur 5 sessions. Le log reste lisible — une trame
acceptée n'imprime RIEN (silence = succès, doctrine du REPL).

⚠️ **Ce chiffre est un PLAFOND, pas la contribution propre du régime 1 Hz** (précision
de la revue du 2026-08-16) : le drain de l'agent est aveugle et ramasse aussi le
battement 10 s **et tout `ESP_LOGx` émis par n'importe quel module**.

> 🔴 **LE TROISIÈME COÛT DE LA COHABITATION 1, QUI N'AVAIT PAS ÉTÉ CHIFFRÉ : l'HISTORIQUE
> de la console est noyé en 32 secondes.** Trouvé par la revue de code du 2026-08-16.
> `dn_console.c` démarre le REPL avec `ESP_CONSOLE_REPL_CONFIG_DEFAULT()`, qui pose
> `.max_history_len = 32` (`esp-idf/components/console/esp_console.h:67`), et la boucle
> du REPL appelle `linenoiseHistoryAdd(line)` **pour chaque ligne reçue**
> (`esp_console_common.c:246`). La déduplication de linenoise ne compare qu'à l'entrée
> précédente : le `seq` changeant à chaque trame, **elle ne mord jamais**.
> ⇒ **Deux effets mesurables, tous deux à demeure** : (1) à 1 Hz, les 32 entrées
> d'historique sont **intégralement remplacées par des `pc $DN,…` en 32 s** — la flèche
> haut ne rend plus aucune commande humaine tant qu'un agent tourne, sur une console
> dont c'est le seul confort d'usage ; (2) **un `malloc(~40 o)` + un `free` par seconde,
> en continu**, sur les 113 247 o de RAM interne — le régime H24 que dn4-1 vise.
> ⇒ **Décision owner (2026-08-16) : on l'ÉCRIT, on ne corrige pas.** La boucle qui
> appelle `linenoiseHistoryAdd` est **interne à l'IDF** (on ne la contrôle pas sans
> réécrire le REPL), et `max_history_len = 0` supprimerait aussi l'historique de
> l'opérateur humain — le remède serait pire. **C'est un coût assumé de « le transport
> EST le REPL », légué à dn4-1** (quand l'agent devient permanent, il tourne H24).

### Cohabitation 2 — avec `dn_console.py` : l'exclusion marche, et elle est VOULUE

Mesuré dans les deux sens :
- Sous Windows, une **2ᵉ ouverture de COM3 pendant que l'agent tourne** est refusée :
  `PermissionError(13, 'Accès refusé')` — pas de vol d'octets silencieux côté tour.
- Sous WSL, `dn_console.py` **refuse de démarrer** si un détenteur existe (scan
  `/proc/*/fd` + TIOCEXCL) — reproduit en session.
⇒ **Une campagne de mesure ne peut PAS tourner pendant que l'agent tient le port.**
C'est le coût assumé de la branche A : campagne et agent ALTERNENT, ils ne
coexistent pas. Le geste d'alternance est celui de la cohabitation 3.

### Cohabitation 3 — avec la boucle de flash : le geste exact et son coût

```
# WSL → Windows (l'agent peut démarrer) :
powershell.exe -Command "& 'C:\Program Files\usbipd-win\usbipd.exe' detach --busid 3-1"
#   mesuré : 0,3 s. COM3 apparaît ~2 s après.
# Windows → WSL (reflasher/mesurer) :
cd ~/projects/desknode && ./tools/wsl-attach.sh        # mesuré : ~3,1 s
```

🔴 **LE PIÈGE QUI A COÛTÉ UNE HEURE : les veilleurs `--auto-attach`.** Des processus
`usbipd attach --wsl --auto-attach` (côté Windows) et `usbip-auto-attach` (côté WSL,
lancés par d'anciennes sessions de `wsl-attach.sh`) **re-attachent la carte à WSL
quelques secondes après chaque `detach`** — l'agent Windows trouve alors un COM3
fantôme (`FileNotFoundError`), et l'état usbipd peut se bloquer en « Attached »
orphelin. Avant de rendre le port à l'agent, **tuer les veilleurs des deux côtés** :

```
ps aux | grep usbip-auto-attach          # WSL  → kill <pid>
powershell.exe -Command "Get-CimInstance Win32_Process -Filter \"Name='usbipd.exe'\"
  | ? { $_.CommandLine -match 'auto-attach' } | % { Stop-Process -Id $_.ProcessId -Force }"
```

⚠️ **CROYANCE CORRIGÉE (la §7.3 de la story disait « ouvrir le port ne reset pas la
carte »)** : c'est vrai depuis LINUX. **Sous Windows, pyserial pose DTR/RTS à
l'ouverture et les relâche à la fermeture — et cette séquence RESET la carte**
(même recette que `dn_console.py --reset`). Symptôme : compteurs wipés à chaque
session série, « liaison jamais recue ». Parade DANS L'AGENT : `dtr = False`,
`rts = False` posés AVANT `open()`, plus jamais touchés.

### Le constat à l'œil

Image **STABLE** sous trafic USB 1 Hz (30 s, 60 s, 45 s de sessions constatées par
l'owner), case CPU vivante à ~1 Hz, navigation au doigt intacte pendant la réception.

## 12.4 Le verdict

| Critère (§12.1) | A — USB série (REPL) | B — WiFi WebSocket |
|---|---|---|
| RAM interne | **−5 328 o** (tâche dn_link) | −112 168 o (6 407 restants) ; variante : NE DÉMARRE PAS |
| Image à l'œil | stable | stable (mais sans objet) |
| CPU repos, trafic 1 Hz | **0,8 %** (vs 0,9 % dn1-4) | non mesuré (tué avant) |
| Binaire / dépendances | **+4 768 o / zéro composant** | +583 664 o / composants IDF |
| Friction quotidienne | detach/attach 0,3 s / 3,1 s + veilleurs à tuer | aucune (le port reste à WSL) |
| Reprise | **vivante→morte→vivante prouvée, sans reboot** | handshake mort sans purge LRU |
| Prépare la suite | trame versionnée, transport-agnostique (`dn_link`) | idem, mais la RAM plafonne dn3 |

**⇒ USB série (branche A).** Élimination de B **par blocage mesuré** (verrou 1),
légitime au sens de l'epic (« et/ou ») : les symptômes sont cités au caractère près
en §12.2. La friction detach/attach est le prix payé ; il est borné (3,4 s + les
veilleurs, documentés) et n'affecte que le développement, pas le produit.

**Ce que la décision NE tranche PAS** : l'alimentation « PC éteint » (BIOS/port USB
alimenté, ou alim séparée) est une question DISTINCTE du transport, léguée à dn4-1.
Le brief le disait déjà : même en USB, l'autonomie dépend du port, pas du protocole.

**Ce qui la renverserait (à re-mesurer, pas à re-raisonner)** :
1. Un budget RAM interne redevenu large (ex. draw buffer réduit, tas LVGL rogné) —
   re-jouer le déroulé §12.2 : il faut ≥ 32 768 o libres APRÈS serveur WS connecté.
2. Un besoin produit que l'USB ne peut pas servir (carte loin du PC).
Recette de re-mesure : REQUIRES `esp_wifi esp_netif esp_event esp_http_server` au
CMakeLists + `CONFIG_HTTPD_WS_SUPPORT=y` (et `CONFIG_ESP_PHY_CALIBRATION_AND_DATA_STORAGE=n`
— D4) aux defaults, `rm sdkconfig && idf.py build` : `dn_wifi.c` se recompile seul.

## 12.5 Le protocole de trame (v1) — l'autorité est l'en-tête de `dn_link.h`

```
$DN,<ver>,<seq>,<t_ms>,cpu,<dixiemes>*<CK>      ex. $DN,1,42,123456,cpu,153*47
```

XOR NMEA entre `$` et `*`, hex MAJUSCULES. Entiers seuls (doctrine `parse_entier`,
⛔ jamais `atoi`). **L'horodatage de RÉCEPTION fait foi** (esp_timer, temps absolu) ;
`t_ms` agent est diagnostique. Rejets COMPTÉS par cause : tronquée, checksum,
version, format, bornes (> 1000 dixièmes) ; doublon de seq ignoré ; trous de seq
comptés. Batterie de bruit rejouée sur carte le 2026-08-16 : chaque cause tombe
dans son compteur, aucune trame n'est interprétée à moitié.

**État de liaison (AC7)** : péremption **3 000 ms** (3 périodes nominales) ; au-delà
la case CPU affiche « -- » grisé — jamais un chiffre périmé. Prouvé à l'écran par
l'owner : arrêt propre ET kill brutal ⇒ « -- » ; relance ⇒ la case revit **sans
reboot** en ≤ 2 s (1 s de fenêtre d'échantillonnage agent + ≤ 250 ms de poussée +
premier envoi). 4 reprises comptées en session de clôture.

> ⚠️ **CE QUE LE SECOND TÉMOIN D'AC7 PEUT ÊTRE SUR CE TRANSPORT — et ce qu'il ne peut
> PAS être** (précision de la revue du 2026-08-16). AC7 demande deux témoins : « agent
> arrêté proprement, **et** câble/WiFi coupé brutalement ». Sur la branche retenue, les
> deux ont été joués sous la forme **arrêt propre** (`--duree`) et **kill brutal du
> processus** (l'agent tué net, le port reste ouvert côté carte). 🔴 **Le témoin
> « câble débranché » est, lui, PHYSIQUEMENT INATTEIGNABLE en branche A : le même câble
> USB alimente la carte.** Le débrancher n'éteint pas la liaison, il éteint DeskNode —
> il n'y a plus d'écran pour afficher quoi que ce soit d'honnête. Ce n'est pas un trou de
> preuve, c'est une **propriété de la fourche retenue**, et elle doit être écrite là où
> le verdict l'est. ⇒ **Ce qui reste ouvert pour dn4-1** : l'alimentation « PC éteint »
> (port USB toujours alimenté par réglage BIOS/carte-mère, ou alim séparée) est la
> question qui rend ce témoin jouable — et elle est déjà léguée en §12.4.
> ⚠️ Le compteur `reprises` qui publie « 4 » ci-dessus a par ailleurs été corrigé en
> revue (il sur-comptait quand le verrou LVGL était occupé) : **le chiffre est à
> re-relever** à la prochaine session carte.

## 12.6 Les budgets avec liaison + donnée live (firmware final, 2026-08-16)

| Mesure | dn1-4 | dn2-2 final | Delta |
|---|---:|---:|---|
| RAM interne libre | 118 575 o | **113 247 o** | −5 328 o (tâche dn_link 4096 + TCB + tampons) |
| PSRAM libre | 7 768 608 o | 7 768 536 o | −72 o |
| Tas LVGL (`lv_mem_monitor`) | 15 216 o (25 %) | **15 228 o (25 %)**, frag 1 % | +12 o — ⚠️ **PAS un label ajouté** : dn2-2 n'en crée aucun, le label de valeur de la case existait en dn1-4. C'est son **tampon de texte** qui change de taille (« 42 % » → « 100,0 % » / « -- »). Étiquette corrigée en revue |
| Binaire | 790 736 o | **795 504 o** | +4 768 o (dn_link + pc + stubs) |
| CPU repos, trafic 1 Hz | 0,9 % (sans trafic) | **0,8 %** | le trafic 1 Hz est invisible au 0,1 pt près (la valeur est même SOUS la baseline : c'est du bruit de mesure, pas un gain). ⚠️ **Régime de la mesure, à écrire** : `cpu 30` exige la console, et agent ⇄ campagne **alternent** sur le port (§12.3) — le trafic pendant cette mesure venait donc de `dn_console.py`, pas de l'agent Windows. Côté **firmware** le chemin est identique (même `pc $DN,…`, même `dn_link`, même `dn_ui`), donc le chiffre vaut ; ce qu'il ne mesure pas, c'est le PC |
| `fps` | 37,40 Hz | **37,40 Hz (+0,01 %)** | — ⚠️ le fps reste AVEUGLE au défaut §11.4, le constat est l'œil |
| Flush en régime 1 Hz | (label dn1-3 : 15 892 px, 5,17 %, 1 169 µs) | **4 611 px/cycle (1,50 %), 1,0 flush/cycle, 245 µs** | écart EXPLIQUÉ : le label de la case CPU est ~3,4× plus petit que le label central de dn1-3 |
| Latence acceptation→label | — | **n=107 : min 1 / moy 159 / max 250 ms** | dominée par la période de poussée (250 ms) |

**Latence bout en bout, composantes DÉCLARÉES** : t(mesure PC) → t(affiché) =
fenêtre d'échantillonnage agent (≤ 1 000 ms, non instrumentée) + transport série
(~30 o à 115 200 bauds ≈ 3 ms, non instrumenté) + acceptation→label (**mesuré** :
159 ms moy) + flush LVGL suivant (≤ 1 cycle, ~27 ms, non instrumenté). Ordre de
grandeur total : **~0,7 s moyenne, < 1,3 s pire cas** — largement sous la période.

## 12.7 Ce que dn2-2 change pour dn2-1

- **Le bus I²C n'est PAS touché** : la branche A ne fait ni WiFi ni I²C — dn2-1
  retrouve le bus exactement comme dn1-4 l'a laissé (bounce 4800 en parade).
- **Budgets de départ dn2-1** : RAM interne **113 247 o** (et non 117 995), binaire
  795 504 o. Le reste inchangé.
- **L'ordre du boot gagne une étape** : `dn_link_init()` entre `dn_ui_init()` et
  `dn_console_start()` (étape 8). Rien avant l'affichage n'a bougé.
- **Le patron est posé** : pour brancher une valeur dans une case, appeler une
  fonction publique de `dn_ui` qui prend le verrou elle-même (`dn_ui_cpu_maj` est
  le modèle) — dn2-1 fera pareil pour ses cases capteurs, dn3-1 généralisera.
- ⚠️ Sous Windows, **toute ouverture de port série reset la carte si DTR/RTS ne
  sont pas forcés bas AVANT l'open** — vaut pour tout outil côté tour à venir.

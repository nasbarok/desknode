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

> 🔴 **ET LA PARADE EST WINDOWS-ONLY : SOUS LINUX ELLE PROVOQUE LE RESET QU'ELLE PRÉTEND
> EMPÊCHER.** Mesuré en session de validation le **2026-08-16**, A/B à **une seule
> variable** sur `/dev/ttyACM0` :
>
> | Branche | Octets reçus à l'ouverture | Reboot ? |
> |---|---:|---|
> | **avec** `dtr=False; rts=False` avant `open()` | **6 664 o** | 🔴 **OUI** — `rst:0x15 (USB_UART_CHIP_RESET)` |
> | **sans** y toucher (comme `dn_console.py`) | **38 o** | non |
>
> Témoin négatif béton : `dn_console.py`, qui ne touche **jamais** ces lignes, n'a pas
> reset la carte de **toute une session de vingt invocations** — les compteurs ont survécu.
>
> **Comment ça s'est vu, et ce que ça innocente** : le bruit d'écho d'AC3 remontait à
> **227-247 o/s** au lieu des 42-49 o/s publiés. L'écart n'était pas du bruit de régime :
> c'était **le bandeau de boot (~10 Ko) injecté dans la mesure à chaque ouverture**. Parade
> désactivée sous Linux, trois sessions donnent **47,9 · 48,0 · 49,5 o/s** et **1,09-1,10
> lignes/s** — soit **exactement la fourchette publiée par dn2-2**. ✅ **Le chiffre d'AC3 est
> INNOCENTÉ** ; c'est la parade qui le contaminait, pas la mesure qui était fausse.
>
> **Correctif** : `dn_agent.py` ne pose DTR/RTS que sous `if sys.platform == "win32"`.
> ⚠️ **Le côté Windows n'a PAS été re-vérifié** — impossible depuis WSL, `COM3` n'existe pas
> quand la carte est attachée. La parade y reste posée, là où dn2-2 l'a mesurée nécessaire.
> **Pour trancher côté Windows** : rejouer le même A/B sur `COM3`, carte détachée de WSL.
> ⇒ Leçon de méthode : une parade dont on n'a mesuré QUE la disparition du symptôme, sur UNE
> plateforme, n'est pas une parade établie — c'est une corrélation. Celle-ci était nuisible
> sur l'autre plateforme depuis le premier jour.

### Le constat à l'œil

Image **STABLE** sous trafic USB 1 Hz (30 s, 60 s, 45 s de sessions constatées par
l'owner), case CPU vivante à ~1 Hz, navigation au doigt intacte pendant la réception.

> ✅ **RE-CONSTATÉ SUR LE FIRMWARE REVU — session de validation du 2026-08-16, `058589b`.**
> L'agent réel (`dn_agent.py --serie`) a poussé **60 trames en 60 s**, valeurs cyclant sur
> 11,1 → 99,9 % pour que l'œil puisse suivre. Constats owner, dans l'ordre :
> 1. **État de départ, liaison jamais reçue** : dashboard affiché, case CPU sur **« -- »**,
>    les 5 autres cases sur leur factice, rétroéclairage fixe, image stable.
> 2. **Sous trafic** : « je vois bien le cycle » — la valeur suit à ~1 Hz, sans saut ni gel.
> 3. **À l'arrêt de l'agent** : « -- affiché » — la case retombe, AC7 tenu.
> 4. **Image STABLE pendant tout le régime**, et **les 5 autres cases n'ont pas bougé**.
>
> ⚠️ Le `fps` relevé dans la foulée (**37,34 Hz**) ne participe PAS à ce constat : il est
> aveugle au défaut §11.4 (37,33 avant / 37,45 pendant que l'image défilait, mesuré en
> dn1-4). Les quatre points ci-dessus sont des observations de l'owner, pas des déductions.
>
> 🔎 **Sur la teinte du « -- »** : l'owner le décrit **vert clair**, là où le code pose un gris
> neutre `0x9a9a9a`. Ce n'est pas un défaut et il n'y a rien à corriger : les cases sont du
> noir à `LV_OPA_70` posé sur l'asset **Living PCB**, une image de circuit imprimé donc verte
> — 30 % du fond transparaît, et un gris peu saturé en traits fins antialiasés en prend la
> teinte. Le blanc des valeurs valides, plus lumineux, y résiste. AC7 laisse d'ailleurs le
> rendu libre (« tiret, grisé, mention »). **Écrit ici pour que personne ne re-diagnostique
> ça** : la doc dit « grisé », la dalle montre vert clair, et les deux sont d'accord.

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
| RAM interne libre | 118 575 o | **114 123 o** *(re-relevé après revue, firmware `058589b` ; 113 247 o sur `502f77c`)* | −4 452 o (tâche dn_link 4096 + TCB + tampons) |
| PSRAM libre | 7 768 608 o | 7 768 536 o | −72 o |
| Tas LVGL (`lv_mem_monitor`) | 15 216 o (25 %) | **15 228 o (25 %)**, frag 1 % | +12 o — ⚠️ **PAS un label ajouté** : dn2-2 n'en crée aucun, le label de valeur de la case existait en dn1-4. C'est son **tampon de texte** qui change de taille (« 42 % » → « 100,0 % » / « -- »). Étiquette corrigée en revue |
| Binaire | 790 736 o | **795 504 o** | +4 768 o (dn_link + pc + stubs) |
| CPU sous trafic 1 Hz | 0,9 % (repos, dn1-4) | 🔴 **1,60 %** (0,89 % au repos, même instrument) | **+0,71 pt — le trafic DOUBLE quasiment la charge.** ⚠️ Le « 0,8 % » publié par le dev était FAUX, et la cause est structurelle : voir l'encart ci-dessous |
| `fps` | 37,40 Hz | **37,34 Hz (−0,16 %)** *(`058589b`, 448 trames en 12,0 s)* | dans la bande de bruit déjà constatée du dépôt (37,33-37,45 Hz). ⚠️ **Et ça ne prouve RIEN** : le fps est AVEUGLE au défaut §11.4 — mesuré 37,33 avant / 37,45 pendant que l'image défilait. Le seul constat qui compte est l'œil de l'owner |
| Flush en régime 1 Hz | (label dn1-3 : 15 892 px, 5,17 %, 1 169 µs) | **4 611 px/cycle (1,50 %), 1,0 flush/cycle, 245 µs** | écart EXPLIQUÉ : le label de la case CPU est ~3,4× plus petit que le label central de dn1-3 |
| Latence acceptation→label | — | **n=45 : min 10 / moy 42 / max 248 ms** *(instrument CORRIGÉ, `058589b`)* | bornée par la période de poussée (250 ms), et le max le retrouve. ⚠️ Le « n=107 : 1/159/250 » du dev vient de l'instrument AVANT correctif, qui comptait aussi des poussées n'ayant posé **aucun** label — enveloppe identique, moyenne non comparable (la phase agent/tâche dérive lentement, 1000 ms et 250 ms étant commensurables) |

> 🔴 **`cpu N` NE PEUT PAS VOIR LE TRAFIC — L'INSTRUMENT EST AVEUGLE À CE QU'IL MESURE.**
> Trouvé en session de validation le 2026-08-16. `cmd_cpu` prend un instantané, **dort** la
> fenêtre, puis re-mesure : il **bloque la tâche du REPL**. Or, sur la branche retenue, **le
> REPL EST LE TRANSPORT**. Pendant `cpu 30`, les trames de l'agent restent donc dans le
> tampon USB, `dn_link_ingest_ligne()` n'est jamais appelée, aucune poussée n'a lieu, aucun
> redessin ne se produit. **La mesure décrit le dashboard AU REPOS, quel que soit le trafic
> envoyé.** C'est ce qui explique l'anomalie que le dev avait notée sans l'expliquer : 0,8 %
> « sous trafic » **inférieur** aux 0,9 % au repos.
>
> **L'instrument qui, lui, peut voir** : les compteurs **CUMULÉS** (`cpu brut`), lus de part
> et d'autre d'une vraie session d'agent — la mesure ne s'exécute plus *pendant* le trafic.
> Il se **calibre tout seul** : au repos il retrouve **0,89 %**, soit les 0,9 % de dn1-4.
>
> | Régime (45 s, compteurs cumulés) | Charge globale | `taskLVGL` (cœur 0) | `console_repl` | `dn_link` |
> |---|---:|---:|---:|---:|
> | Silence, aucune trame | **0,89 %** | 1,06 % | 0,03 % | 0,011 % |
> | Trafic 1 Hz réel (45 trames) | **1,60 %** | 2,12 % | 0,42 % | 0,098 % |
> | **Delta** | **+0,71 pt** | +1,06 pt | +0,39 pt | +0,09 pt |
>
> ⇒ **Le coût dominant est le REDESSIN LVGL (+0,53 pt de charge globale), pas la liaison.**
> `dn_link` lui-même est négligeable (+0,04 pt) : ce qui coûte, c'est de repeindre la case à
> chaque seconde. **Ce que ça change pour dn3** : six cases vivantes au lieu d'une ne
> coûteront pas 6 × 0,04 pt mais ~6 × 0,53 pt de redessin — c'est le chiffre à budgéter en
> dn3-2, et il n'était pas sur la table.
> ⚠️ Cette mesure a été prise depuis WSL, l'agent parlant à `/dev/ttyACM0`. Le régime
> **firmware** est identique à celui de l'agent Windows (même `pc $DN,…`, même `dn_link`,
> même `dn_ui`) ; ce que ce chiffre ne mesure pas, c'est le coût **côté PC**.

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

---

# 13. LE PROTOCOLE v2 ET LES CINQ SOURCES PC — mesuré le 2026-08-18 (dn4-1, P9.1)

## 13.1 La grammaire v2 — ⛔ l'autorité reste `main/dn_link.h`

**Ce paragraphe RÉSUME, il ne redéfinit pas.** Le dépôt a déjà publié un checksum **faux** dans
**trois** fichiers d'autorité à la fois (`dn_link.h`, la docstring de l'agent et §12.5), si bien
que l'« exemple valide » du projet était la **seule trame que le firmware refuse**. Une grammaire
recopiée dérive ; celle qui fait foi vit dans `dn_link.h`.

    v1 (dn2-2, TOUJOURS ACCEPTÉE) : $DN,1,<seq>,<t_ms>,cpu,<dixiemes>*<CK>      6 champs EXACTEMENT
    v2 (dn4-1)                    : $DN,2,<seq>,<t_ms>,<metrique>,<v1>[,<v2>]*<CK>   6 OU 7 champs

| métrique | v1 (grandeur 0) | v2 (grandeur 1) | v2 attendue ? |
|---|---|---|---|
| `cpu` | % d'utilisation (0..1000) | GHz (0..1000) | oui |
| `gpu` | % d'utilisation (0..1000) | °C (0..1500) | oui |
| `ram` | % d'occupation (0..1000) | **Go TOTAUX** (0..40000) | oui |
| `net` | Mb/s ↓ (0..1000000) | Mb/s ↑ (0..1000000) | oui |
| `disk` | Mo/s (0..1000000) | — | **non** |

Toutes les valeurs sont en **DIXIÈMES**, entières. ⛔ Aucun flottant sur le fil.

🔴 **`ram` porte le TOTAL, pas l'utilisé, et c'est structurel.** Le firmware compose
« 22,7 / 34,2 Go » en calculant `utilisé = % × total`. Envoyer deux nombres échantillonnés
séparément afficherait tôt ou tard **deux vérités contradictoires dans le même rectangle** —
c'est le motif écrit du mock « 12,1 / 32 Go » de dn3-2, et il vaut plus encore pour du réel.

🔴 **W3 tranché : UNE TRAME PAR MÉTRIQUE.** Trois raisons, dans cet ordre :
1. **Chaque métrique a son horodatage de réception**, donc sa **péremption propre**,
   gratuitement. Une source qui meurt seule meurt seule (W8 fermée du même coup).
2. **La ligne reste courte** : pire cas v2 au gabarit = **51 octets**
   (`$DN,2,4294967295,4294967295,disk,1000000,1000000*FF`). `DN_LINK_LIGNE_MAX` **reste à 63**.
3. **Une 10ᵉ grandeur rentrera encore.** L'option « tout-en-un » faisait ~96 octets.

🔴 **W10 tranché : la 2ᵉ grandeur est OPTIONNELLE, et son absence EST une donnée.** Une trame v2
à 6 champs dit « je connais v1, je ne connais pas v2 ». ⛔ **Pas de jeton « inconnu »** :
`parse_u32_strict` refuse un champ vide (« champ VIDE ≠ zéro », délibéré). Côté écran, la case
reste **RÉELLE** et la seule grandeur manquante s'affiche **« -- » en gris**.
⚠️ **Écart assumé avec `dn_ui_ambiance_maj`**, qui grise ses deux grandeurs ensemble : là, elles
viennent d'**un seul** capteur ; ici, de sources **indépendantes**. Taire le % GPU parce que la
°C manque supprimerait une information vraie et disponible.

**Le seq reste GLOBAL**, jamais par métrique : il numérote les trames de l'**agent**, qui est un
émetteur unique. Le suivre par métrique compterait **4 « pertes » à chaque tour de cinq trames**.

## 13.2 🔴 LA LONGUEUR DE LIGNE, MESURÉE — et l'instrument évident était faux

`max_cmdline_length = 128` est ce que le code **alloue**, pas ce que le fil **délivre**.

| instrument | verdict | valide ? |
|---|---|---|
| l'**écho** du REPL | « intact » jusqu'à **127** caractères | 🔴 **NON** — linenoise renvoie les octets **à mesure qu'ils arrivent**, donc **avant** le plafond du tampon |
| le **firmware lui-même** (`pc $<...>` ré-imprime `argv[1]`) | **124** caractères de trame, **127** pour la ligne entière | ✅ c'est la vue du **consommateur** |

Mesuré par balayage de 115 à 135 caractères : intact jusqu'à 124, plateau à 124 ensuite (9 tirs).
⇒ **La bande « ligne COMPLÈTE mais trop longue » est 64..124**, large de **61 octets**, donc
**atteignable**. C'est la condition pour que `rejets_trop_longue` ne soit pas un compteur
décoratif — *et un compteur décoratif est un instrument qui ment.*

## 13.3 La campagne de bruit — 15 cas, chacun sur SON compteur

`pc reset` avant chaque cas, relevé du delta après. **Critère : le compteur attendu +1, ET LUI
SEUL.**

| cas | compteur | ✓ |
|---|---|---|
| pas de queue `*CK` / queue mutilée (`*4`) | `rejets_tronquee` | ✅ ✅ |
| ligne complète de 64..124 o | `rejets_trop_longue` | ✅ |
| checksum faux | `rejets_checksum` | ✅ |
| version 3 / version 0 | `rejets_version` | ✅ ✅ |
| champ absent (5) / en trop (8) / VIDE | `rejets_format` | ✅ ✅ ✅ |
| métrique inconnue | `rejets_format` | ✅ |
| **v1 avec métrique v2** / **v1 à 7 champs** | `rejets_format` | ✅ ✅ |
| v2 sur métrique sans 2ᵉ grandeur (`disk`) | `rejets_format` | ✅ |
| `cpu` > 1000 / `gpu` °C > 1500 | `rejets_bornes` | ✅ ✅ |

**15 / 15.** Et les trois cas de `seq`, qui demandent deux trames :

| cas | observé |
|---|---|
| doublon de `seq` | `recues` +1, `doublons` +1 — valeur IGNORÉE |
| saut ARRIÈRE (agent redémarré) | `recues` +2, `resynchros` +1 — trame **APPLIQUÉE** |
| trou crédible (+3) | `recues` +2, `pertes_seq` +2 |

⚠️ Mes attentes écrites pour ces trois-là étaient **fausses** (j'avais prédit `resynchros` +2 et
un `resynchros` sur le trou crédible). **C'est le firmware qui a raison** : la première trame
après un `pc reset` est « première », son saut vaut 1 et ne compte rien.

## 13.4 🔴 TÉMOIN DE NON-RÉGRESSION v1 — l'extension EST additive

`agent/dn_agent.py` **de dn2-2, NON MODIFIÉ** (copie figée depuis `git show 395310e:`, vérifiée
identique à l'arbre avant modification), exécuté **sur la tour**, sa sortie `--stdout` capturée
**telle quelle** et injectée. ⛔ **Les trames ne sont pas re-fabriquées par le harnais** : un
harnais qui rejoue au lieu d'extraire fabrique sa propre vérité.

| tir | valides | doublons | pertes | **`rejets_version`** | tous rejets |
|---|---:|---:|---:|---:|---|
| 1 | 7 / 8 | 0 | 1 | **0** | 0 partout |
| 2 | **8 / 8** | 0 | 0 | **0** | 0 partout |
| 3 | **8 / 8** | 0 | 0 | **0** | 0 partout |
| 4 | **8 / 8** | 0 | 0 | **0** | 0 partout |

⇒ **La case CPU vit, `rejets_version` = 0.** L'extension est prouvée additive.
⚠️ **La perte du premier tir est déclarée et NON reproductible** (3 rejeux à 8/8, aucun rejet) :
une trame n'a jamais atteint le parseur — donc ni rejetée ni comptée. C'est un aléa du **harnais
console**, pas du firmware, et il est écrit plutôt que lissé.
✅ **Et le témoin montre W10 en action** : l'agent v1 ne publie pas de fréquence, la case affiche
donc **« 21,3 % » en blanc et « -- » en gris** sur la seconde ligne. Elle ne l'invente pas.

## 13.5 🔴 W1 — LA SOURCE GPU SUR CETTE TOUR : le repli n'a pas servi

**Le constat qui ouvrait la story** : `Win32_VideoController` rend **UN SEUL** contrôleur,
**AMD Radeon RX 6800 XT**, driver 32.0.21045.1000, `PCI\VEN_1002&DEV_73BF`. `pynvml` est
**absent** du Python 3.13 de la tour. ⇒ **NVML, nommée par D10, n'a aucun device ici.**

**Les deux candidats, MÊME protocole (30 tirs à 1 Hz, cumul `Process().cpu_times()`)** :

| source | par tir | % d'un cœur | % machine | rend | verdict |
|---|---:|---:|---:|---|---|
| **`atiadlxx.dll` — `ADL2_New_QueryPMLogData_Get`** | **0,5 ms** | **0,052 %** | **0,0033 %** | **% ET °C en UN appel** | ✅ **RETENUE** |
| WMI `..._GPUEngine` (720 instances) | **342,2 ms** | **30,8 %** | **1,93 %** | % seul | ⛔ **ÉCARTÉE** |

🔴 **657× plus cher** — et le candidat WMI **faisait sauter à lui seul le critère n°4 du brief**
(« l'agent reste imperceptible, < 1 % CPU ») **et ne tenait même pas la cadence 1 Hz** : 33,3 s
de temps mural pour 30 tirs espacés d'une seconde.

⇒ **LE REPLI PRÉ-AUTORISÉ PAR L'OWNER (« % seul, °C absente ») N'A PAS SERVI.** La °C GPU est
là, sans élévation, sans driver, sans .NET — donc **sans franchir la frontière D8**.

⚠️ **LE MAPPING DES CAPTEURS PMLog N'EST PAS DEVINABLE, ET IL SE VÉRIFIE.** Les indices viennent
de l'énumération `ADLSensorType` du SDK ADL ; les prendre pour argent comptant, ce serait risquer
de publier une tension comme une température. **Le témoin est éliminatoire** : les mêmes indices
doivent rendre `BUS_LANES = 16` et `CLK_MEMCLK ≈ 2000 MHz` sur une RX 6800 XT. L'agent **refuse
de servir** sinon. (Relevés : 16 et 1976-1990 MHz selon le tir.)
⚠️ **Cette tour expose SEPT `iAdapterIndex` pour UN SEUL GPU physique** (une entrée par sortie
d'affichage) : l'agent prend **le premier qui RÉPOND à PMLog avec un mapping cohérent**, pas
« le premier présent » — ce serait un pari.

## 13.6 W2 — la grandeur de `DISQUE`, tranchée par la mesure

**Critère écrit AVANT l'échantillonnage** (une case de six doit BOUGER, quantifié), les **deux**
candidats sur la **même** session réelle de **16 min à 1 Hz** (960 échantillons), à la **même**
résolution (le dixième d'unité affichée) :

| candidat | C1 étendue ≥ 5 dixièmes | C2 texte changé ≥ 10 % | C3 σ ≥ 1 dixième | verdict |
|---|---:|---:|---:|---|
| **débit I/O (Mo/s)** | **2 684** (268,4 Mo/s) ✅ | **93,3 %** ✅ | **126,4** ✅ | ✅ **QUALIFIE** |
| taux d'occupation (%) | **0** ❌ | **0,0 %** ❌ | **0,00** ❌ | ❌ |

L'occupation vaut **54,9 %** du premier au dernier échantillon, **étendue nulle au dixième de
point**. ⇒ **le DÉBIT**, et **W12 ne se pose pas** : le candidat retenu bouge.
⛔ **Pas de jauge** : un débit n'a pas de plein, et une jauge dont l'échelle est inventée est un
mensonge d'interface silencieux — **même motif écrit que pour `RÉSEAU`**.

## 13.7 AC11 — ce qui saute, et le legs à `dn4-5`

960 échantillons consécutifs à 1 Hz, côté PC. **Saut = écart entre deux échantillons
consécutifs, à la résolution AFFICHÉE.**

| grandeur | min | max | saut méd. | saut p95 | saut max | % d'échantillons qui changent |
|---|---:|---:|---:|---:|---:|---:|
| **CPU GHz** | 1,2 | 3,2 | **0,8** | **2,0** | **2,0** | 76 % |
| CPU % | 14,2 | 86,9 | 7,3 | 45,7 | 58,4 | 99 % |
| RÉSEAU ↓ Mb/s | 0,1 | 296,1 | 14,0 | 86,1 | 260,8 | 97 % |
| RÉSEAU ↑ Mb/s | 0,2 | 28,1 | 0,6 | 9,3 | 25,2 | 94 % |
| DISQUE Mo/s | 0,0 | 268,4 | 1,0 | 7,6 | 191,1 | 93 % |
| GPU % | 0,0 | 19,0 | 1,0 | 6,0 | 18,0 | 54 % |
| GPU °C | 46,0 | 48,0 | 0,0 | 1,0 | 1,0 | 29 % |
| RAM % | 60,1 | 67,6 | 0,0 | 0,1 | 0,8 | 28 % |

🔴 **LA FRÉQUENCE CPU EST LA PLUS BRUYANTE, ET PAS PAR SON AMPLITUDE — PAR SA NATURE.** Son saut
médian vaut **0,8 GHz sur une plage totale de 2,0** : la moitié des rafraîchissements déplace le
chiffre de **40 % de sa course**, sans rapport lisible avec la charge instantanée (relevé sous
charge constante : 3201 · 1200 · 1300 · 2100 · 1200 MHz).

**Legs à `dn4-5`, écrit** :
- **Lissage NÉCESSAIRE** : `CPU GHz` (le cas d'école), `RÉSEAU ↓`, `DISQUE` — saut p95 ≥ 40 % de
  la plage observée.
- **Lissage INUTILE** : `RAM %` et `GPU °C` — elles changent moins d'un tiers du temps et d'un
  dixième d'unité. Les lisser n'ajouterait qu'un retard.
- **À DISCUTER** : `CPU %` — elle saute beaucoup **mais c'est la vérité de la machine**, et un
  CPU lissé ment sur les pics. *« Le lissage ne se décide pas par principe. »*
- ⚠️ **Contrainte non négociable** : **aucune valeur lissée ne doit survivre à la péremption de
  3 s**, sinon AC7 de dn2-2 tombe.

## 13.8 AC9 — le coût de l'agent, mesuré AU CUMUL

Lancé depuis une session **non élevée**, sans driver, sans .NET.
**Méthode** : cumul `psutil.Process().cpu_times()` rapporté au temps mural. ⛔ **Jamais une
fenêtre glissante** : sa résolution (~0,16 pt sur 10 s, ticks de 15,6 ms) **ne peut pas voir**
un coût de cet ordre.

| | dn2-2 (1 métrique) | **dn4-1 (5 métriques / 7 grandeurs)** |
|---|---:|---:|
| durée | 40 s | **180,0 s** |
| s CPU | 0,141 | **2,750** |
| **% d'un cœur** | 0,35 % | **1,528 %** |
| **% machine (16 cœurs)** | 0,022 % | **0,0955 %** |
| trames émises | 40 | **900** (5,00 /s) |
| écrêtages | — | **0** |
| recalages de cadence | — | **0** |

**L'augmentation est ATTRIBUÉE, source par source** (30 tirs chacune, même méthode) :

| source | ms CPU / tir | part des 15,1 ms/s |
|---|---:|---:|
| `psutil.virtual_memory()` | **7,8** | 52 % |
| `psutil.net_io_counters()` | **6,8** | 45 % |
| **ADL PMLog (GPU % + °C)** | **0,5** | **3 %** |
| `psutil.cpu_percent()` + `cpu_freq()` | ~0,0 | ~0 |
| `psutil.disk_io_counters()` | ~0,0 | ~0 |
| **somme** | **≈ 15,1 ms/s** | **= 1,51 % d'un cœur** |

⇒ **1,51 sur les 1,528 points mesurés sont expliqués.** L'attribution ferme.
🔴 **ET ELLE RENVERSE L'INTUITION DU CADRAGE** : la source GPU était le poste suspect (« mesurer
le coût de l'énumération des 720 instances, c'est le critère n°4 du brief qui est en jeu »).
C'est vrai **du candidat WMI** ; la source **retenue** pèse **3 %** du coût. Les postes
dominants sont `virtual_memory` et `net_io_counters`, deux appels qu'on n'aurait pas soupçonnés.

⚠️ **Quelle lecture de « < 1 % CPU » ?** Le brief ne le dit pas. Les deux sont publiées :
**0,0955 % machine** (ce qu'affiche le Gestionnaire des tâches) ✅ **tenu, avec un facteur 10 de
marge** · **1,528 % d'un cœur** ❌ au-dessus de 1. dn2-2 publiait déjà les deux (0,35 / 0,022).
⚠️ **D8** : ce chiffre porte sur **l'AGENT SEUL** — et c'est légitime **parce qu'il n'y a rien
d'autre**. Sous Ring0 il aurait fallu y ajouter le service LibreHardwareMonitor.

## 13.9 Les dépendances de l'agent, avec leur statut MESURÉ

| dépendance | statut | pourquoi |
|---|---|---|
| `psutil` **7.2.2** | ✅ déjà installée | CPU, RAM, réseau, disque — même chiffre que le noyau |
| `pyserial` | ✅ déjà installée | branche A (COM3) |
| `websockets` | ✅ déjà installée | branche B, **écartée** par la fourche dn2-2 — gardée pour re-mesure |
| **`ctypes` + `atiadlxx.dll`** | ✅ **stdlib + DLL déjà présente** | **aucune dépendance ajoutée** pour le GPU |
| `pywin32` (`win32com`) | ✅ présente, **NON UTILISÉE** en régime | a servi à mesurer le candidat WMI, puis écartée |
| `pynvml` | ❌ absente | **inapplicable** : la tour est AMD |

⇒ **dn4-1 n'ajoute AUCUNE dépendance.** La source GPU passe par `ctypes` (stdlib) et une DLL
installée par le pilote AMD.

## 13.10 Ce qui n'a pas marché, avec son symptôme

- ⛔ **NVML** — écartée **sans être essayée**, et c'est justifié : `Win32_VideoController` rend
  un contrôleur **unique** et **AMD**. Essayer NVML aurait été essayer un pilote NVIDIA sur une
  machine sans NVIDIA.
- ⛔ **WMI `GPUEngine`** — **essayée et mesurée** : fonctionne (720 instances, neutre en langue,
  sans droits) mais **342 ms de CPU par tir**. Écartée par le chiffre, pas par principe.
- ⛔ **`ADL_Overdrive5_Temperature_Get`** → `rc = -5` · **`ADL_Overdrive6_Temperature_Get`** →
  `rc = -5` · **`ADL2_OverdriveN_Temperature_Get`** → `rc = -8`. Les trois API de température
  « classiques » d'ADL sont **mortes sur RDNA2**. Seule `ADL2_New_QueryPMLogData_Get` répond.
- ⛔ **L'écho du REPL comme mesure de longueur de ligne** — rendait « intact » à 127 caractères
  alors que le parseur n'en recevait que 124. **L'instrument ne pouvait pas voir le défaut.**
- ⛔ **`psutil` `errin`/`errout`/`dropin`/`dropout`** — **jamais publiés** : cette tour rend
  `dropin = 113 558 935 299 979`, une valeur impossible. Les compteurs d'octets et de paquets,
  eux, sont cohérents.
- 🔴 **Une session d'échantillonnage a été JETÉE** : un premier lancement en arrière-plan n'était
  pas mort et un second écrivait le même CSV. Symptôme : une ligne à 20 champs au lieu de 21, que
  `csv.DictReader` a avalée **en décalant toutes les colonnes** — l'analyse a publié
  « CPU % max = 1600 » (c'était la fréquence) et « RAM % max = 22 milliards » (des octets).
  ⚠️ **Ce sont des valeurs ABSURDES qui ont sauvé la mesure ; un décalage plausible ne l'aurait
  pas fait.** Le lecteur **compte et rejette** désormais toute ligne malformée, et vérifie que
  les horodatages sont strictement croissants.

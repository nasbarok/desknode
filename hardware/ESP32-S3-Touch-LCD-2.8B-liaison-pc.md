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
doivent rendre une **largeur de lien PCIe légale** et une **horloge mémoire plausible** — ⚠️ **PAS
`BUS_LANES = 16` exactement**, et c'est le CODE qui fait foi (corrigé en revue le 2026-08-18 :
trois textes affirmaient une égalité que le code ne vérifie pas). ⚠️ Le motif avancé alors — une
RX 6000 abaisserait son lien au repos — est une **HYPOTHÈSE NON MESURÉE**, et la séance du même
jour ne la confirme pas : **`BUS_LANES = 16` · `CLK_MEMCLK = 1988 MHz`** relevés sur la tour.
⛔ Ne pas resserrer sur la foi de cette hypothèse ; il faudrait un relevé **au repos prolongé**. L'agent **refuse
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

> ⚠️ **CETTE SECTION MESURE `--stdout`, PAS LE TRANSPORT RETENU — ET PAS L'AGENT LIVRÉ**
> (annotation de revue 2026-08-19 ; elle manquait, et c'est la section que les stories citent).
> Trois chiffres coexistent dans le dépôt, et ils ne se remplacent pas l'un l'autre :
>
> | Mesure | Coût | Où |
> |---|---:|---|
> | `--stdout` (témoin) | **1,528 % d'un cœur · 0,0955 % machine** | ci-dessous |
> | `COM3`, agent de la 1ʳᵉ séance | **2,161 % · 0,135 %** | §13.11.3, README |
> | `COM3`, **agent LIVRÉ** (`d5d3539`) | **2,421 % · 0,1513 %** | `…-affichage.md` §17.9 |
>
> 🔴 **+0,63 pt** entre `--stdout` et `COM3` : le port série a un coût propre, absent de tout
> budget. 🔴 **+0,26 pt** de plus sur l'agent livré, **NON EXPLIQUÉ** — au ledger.
> ⛔ **Ne pas citer le chiffre ci-dessous comme le coût de l'agent.**

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

🔴 **AMENDÉ LE 2026-08-21 (dn4-8 / D13), ⛔ PAS EFFACÉ — ET LA PHRASE S'EST RÉALISÉE.**
*« Sous Ring0 il aurait fallu y ajouter le service LibreHardwareMonitor »* : **c'est exactement
ce qui arrive.** LHM tourne en service permanent, et le *« parce qu'il n'y a rien d'autre »*
**tombe**.
⇒ **D13 tranche la lecture, et elle est obligatoire à écrire** : le critère n°4 du brief
(`< 1 % CPU`) se mesure sur **l'AGENT SEUL** — ⛔ **LHM n'y entre pas** — **mais la charge totale
de la tour, elle, AUGMENTE.**
🔴 **DEUX CHIFFRES, PUBLIÉS SÉPARÉMENT, ⛔ JAMAIS ADDITIONNÉS EN SILENCE, ET ⛔ LE SECOND NE SE
CACHE JAMAIS DERRIÈRE LE PREMIER.** C'est **AC9 de `dn4-8`**, et il n'est **pas** soldé.
⚠️ **Et le chiffre ci-dessus est lui-même à re-lire** : **1,528 %** est un relevé `--stdout`,
⛔ **pas** le transport. Sur `COM3` l'agent livré est à **2,421 % d'un cœur / 0,1513 % machine**
— **+0,63 pt de coût propre au port**, qui n'existait dans aucun budget.
⛔ **AC9 de `dn4-1` reste `PARTIAL`** : le brief ne dit pas laquelle des deux lectures il vise.

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

## 13.11 🔴 SÉANCE CARTE DU 2026-08-18 — le vrai agent sur COM3, et ce que l'œil a trouvé

> Carte **détachée de WSL**, agent réel sur `COM3`, trois lancements successifs.
> ⚠️ Tout ce qui suit est mesuré **sur le transport série**, pas par injection console.

### 13.11.1 AC10 — LE TÉMOIN INDÉPENDANT, ÉCRAN CONTRE GESTIONNAIRE DES TÂCHES

**Le critère a été fixé AVANT de regarder** (sinon on justifie ce qu'on voit) : *quelques points
d'écart = fenêtres d'échantillonnage décalées, **normal** ; un écart de **facteur** = défaut.*

| métrique | écran DeskNode | Gestionnaire des tâches | écart | verdict |
|---|---:|---:|---|---|
| CPU % | 14 | 17 | 3 points | ✅ |
| CPU GHz | 1,3 | 1,5 | 0,2 | ✅ sous le saut médian mesuré (0,8 GHz) |
| GPU % | 5, quasi constant | oscille 3 · 4 · 5 · 8 | dans la plage | ✅ |
| **GPU °C** | **47** | **47** | **0** | 🔴 **exact** |
| RAM % | 63,5 | 64 | 0,5 point | ✅ |
| **RAM totale** | **31,9 Go** | **31,9 Go** | **0** | ✅ **après correctif** — voir 13.11.2 |

⚠️ Constat owner sur le décalage : *« genre moins d'1 s de décalage, tout à fait acceptable »* —
c'est exactement le mécanisme que le critère anticipait.

🔴 **LE `47` CONTRE `47` VAUT PLUS QUE SA PRÉCISION.** Le témoin de mapping PMLog était
**INDIRECT** : une largeur de lien PCIe légale et une horloge mémoire plausible prouvaient qu'on interrogeait la bonne
carte, **pas** que l'indice 8 portait bien la température. Windows vient de le confirmer
**directement**. ⇒ **L'indice n'est plus un pari.**

⚠️ **UNE NUANCE À GARDER POUR `dn4-5`** : le GPU % est « quasi constant » chez nous et oscille
3-8 chez Windows. Ce n'est **pas** un écart de valeur, c'est une **agrégation différente** — ADL
rend l'activité instantanée d'un capteur, Windows moyenne sur ses moteurs. À savoir **avant** de
décider d'un lissage : lisser une source déjà plus lisse que sa référence n'ajouterait qu'un retard.

### 13.11.2 🔴 LE DÉFAUT QUE L'ŒIL A TROUVÉ, ET QUE PERSONNE D'AUTRE N'AURAIT VU

**Constat owner, verbatim** : *« correspond au gestionnaire des tâches, par contre c'est 31.9
(pourquoi 34 ?) »*.

```
34 254 475 264 octets  ÷ 1e9   = 34,3   ← ce que l'écran affichait  (Go DÉCIMAUX)
                       ÷ 2^30  = 31,9   ← ce que Windows affiche    (Gio BINAIRES)
```

**Mêmes octets, deux conventions.** Windows affiche des **Gio** et les étiquette « Go ».

🔴 **CE N'EST PAS UN ARRONDI, C'EST UN MENSONGE D'INTERFACE — ET LE PIRE GENRE : celui qui a
l'air d'un arrondi.** Le module est **posé à côté de la tour** : les deux chiffres se lisent côte
à côte, tous les jours, avec **7,4 % d'écart**.
⚠️ **Aucun instrument du firmware ne pouvait le voir.** `flush` voit les zones sales, `pc` voit
les compteurs, `cpu brut` voit la charge — **aucun ne sait ce que Windows affiche à côté.** C'est
la définition même d'AC10, et c'est la première fois qu'il rapporte.
⚠️ **La spec était du bon côté** : l'addendum §1 écrivait déjà « 12.1 / **32** Go », soit la
convention binaire arrondie. C'est l'implémentation qui avait dérivé.

⇒ **Correctif** : l'agent envoie des **Gio** (2^30). ⛔ **L'étiquette reste « Go », délibérément** :
c'est ce que Windows écrit en français, et mettre « Gio » ferait du module **le seul afficheur de
la machine à le dire autrement**.

### 13.11.3 AC2 / AC9 — CE QUE SEUL L'AGENT RÉEL POUVAIT MESURER

| | 300 s | 600 s | note |
|---|---:|---:|---|
| trames émises | 1 500 | **3 000** | **5,00 /s** dans les deux cas |
| erreurs d'envoi · recalages · écrêtages | 0 · 0 · 0 | **0 · 0 · 0** | |
| **refus signalés par le firmware** | **aucun** | **aucun** | 🔴 *« n trames émises » prouvait n ÉCRITURES ; ceci prouve n **ACCEPTATIONS*** |
| **écho console (AC2)** | 228,7 o/s · **5,11 lignes/s** | 232,0 o/s · **5,11 lignes/s** | **PLAFOND** : inclut le battement 10 s et tout `ESP_LOGx` |
| **coût agent (AC9)** | 1,984 % d'un cœur · 0,124 % machine | **2,161 %** · **0,135 %** | |

🔴 **LE PRIX DE W3 EST CONFIRMÉ PAR LA MESURE.** « Une trame par métrique » avait été tranchée en
annonçant *« ×5 sur l'écho, à mesurer »*. **5,11 lignes/s pour 5 trames/s** : le facteur est bien
là, et il est payé en connaissance de cause.

🔴 **ET LE TRANSPORT A UN COÛT PROPRE, ISOLÉ** : **2,161 %** d'un cœur en `--serie` contre
**1,528 %** en `--stdout`, mêmes sources, même cadence. ⇒ **+0,63 pt** pour l'ouverture, l'écriture
et le drain du port. ⚠️ Ce poste n'existait dans aucun budget : il apparaît parce qu'on a mesuré
l'agent **là où il tourne vraiment**.
⚠️ « < 1 % CPU » (brief n°4) : **0,135 % machine** ✅ · **2,161 % d'un cœur** ❌. Les deux lectures
sont publiées, comme dn2-2 le faisait déjà. ⛔ Le brief ne tranche pas laquelle il vise.

### 13.11.4 Les compteurs après 8 075 trames RÉELLES

| | valeur | lecture |
|---|---:|---|
| trames valides | **8 075** | |
| **rejets, toutes causes** | **0** | aucune trame réelle refusée |
| doublons | **0** | |
| pertes seq | **25** (0,31 %) | ⚠️ **attribué** : l'owner a navigué pendant la session, et `build_scene()` bloque le REPL **307-322 ms**, donc le transport. Ce n'est pas du bruit de liaison |
| **resynchros / reprises** | **2 / 2** | 🔴 **trois lancements d'agent ⇒ DEUX reprises.** Le compteur **ne sur-compte pas** — c'est AC6 prouvé sur le vrai transport, là où dn2-2 pouvait publier une reprise **4 à 9 fois** |
| latence acceptation→label | ~~n=8 075 · 1 / **204** / **480** ms~~ | 🔴 **CE CHIFFRE EST MORT — ⛔ NE PAS LE REPUBLIER** (annotation de revue 2026-08-19). Il a été pris **avant** le correctif d'instrument du 2026-08-18, avec un chronomètre qui partait de `v.age_us`, donc **AVANT la prise du verrou LVGL**. ⚠️ **Son attribution ci-contre est RÉFUTÉE** : ce n'était **pas** l'attente du verrou — l'instrument ne pouvait pas la voir — mais les **re-essais** qu'elle provoquait, chacun ajoutant 250 ms d'âge (`…-affichage.md` §17.9). Remplaçant relevé le 2026-08-18 sur `c1072c0` : **n=896 · 30 / 124 / 169 ms**. ⏳ **Lui-même à re-relever** : le correctif du 2026-08-19 (origine absolue, `dn_link.h`) retire de chaque échantillon un δ non borné |

⚠️ **RAPPEL D'INSTRUMENT** : cette latence **n'est plus celle de dn2-2**. Elle agrège désormais
**les cinq métriques** ; dn2-2 publiait `n=45 : 10 / 42 / 248 ms` pour **une seule**. Les comparer
serait comparer deux grandeurs différentes.

### 13.11.5 🔴 LA PARADE DTR/RTS SOUS WINDOWS — l'incertitude de dn2-2 tombe

dn2-2 écrivait : *« la parade est WINDOWS-ONLY, et sous Linux elle PROVOQUE le reset qu'elle
prétend empêcher (A/B mesuré). ⚠️ Le côté Windows n'a jamais été re-vérifié par A/B. »*

**Témoin POSITIF, et c'est ce qui compte** : le compteur d'uptime du firmware.

| | uptime |
|---|---:|
| avant le détachement de WSL | **1 180 s** |
| après **trois** ouvertures/fermetures de `COM3` par l'agent, et ré-attachement | **3 130 s** |
| **différence** | **+1 950 s** = exactement le temps écoulé |

⇒ **LA CARTE N'A PAS REBOOTÉ.** ⛔ Ce n'est **pas** une absence de symptôme : le compteur
**continue**, il aurait été remis à zéro par un `esp_restart()`.

⚠️ **CE QUE CE TÉMOIN NE PROUVE PAS, ET IL FAUT L'ÉCRIRE** : que la parade soit **NÉCESSAIRE**.
Ce n'est **pas** un A/B — l'agent force `dtr=False, rts=False` avant `open()` dans les trois tirs,
et personne n'a essayé **sans**. ⇒ **Prouvé : avec la parade, Windows n'a pas reset la carte, trois
fois de suite.** Non prouvé : ce qui se passerait sans elle.

### 13.11.6 Les constats owner de la séance, verbatim

| constat | verdict |
|---|---|
| décor plein écran, rétroéclairage fixe | ✅ |
| 💾 icône disquette à 28 px | ✅ acceptée |
| deux grandeurs **empilées** | ✅ *« oui, mieux »* — ⚠️ **préférées** à la ligne unique de l'addendum §1, l'écart n'est plus seulement assumé |
| 5 cases « -- », AMBIANCE seule vivante, agent arrêté | ✅ **le différenciateur du brief, VU** |
| six cases vivantes, **zéro badge ambre** | ✅ |
| 🔴 **aucun clignotement gris** | ✅ **le défaut trouvé par la mesure (408 → 234 flushes) est confirmé réparé À L'ŒIL** |
| image stable sous trafic 1 Hz | ✅ *« nickel »* |
| « est-ce que ça saute désagréablement ? » | ✅ **non** |
| vue détail | ✅ *« données live et pas déconnantes »* |
| **piste de jauge éclaircie** (`0x5A5F6A`) | ✅ *« la barre ressort bien »* |
| **RÉSEAU ↓/↑ empilés** | ✅ *« ok »* |

⚠️ **NON CONFIRMÉ À L'ŒIL, ET DÉCLARÉ TEL** : que le détail affiche bien **« MIN -- · MAX -- »**.
L'owner a jugé le détail « pas déconnant » sans vérifier ce point précis. ⇒ **Vérifié par lecture
du code** : `s_det_minmax` n'a **qu'un seul écrivain** (`dn_ui.c:1946`) et c'est une **constante
littérale**. ⛔ **Une preuve de code n'est pas un constat owner**, et les deux ne se remplacent pas.

### 13.11.7 Le tactile sur la jauge — et il a fallu trois tours

**AC12 exige de viser LA JAUGE**, pas le centre : c'est le seul endroit où `lv_bar` peut voler le
tap sans que rien ne le signale. La bande de la jauge RAM est haute de **10 px** (`y = 340..350`,
formule contrôlée contre le relevé publié de dn3-2 : VENTILOS à `506..516`).

| tour | appuis / taps | dans la bande ? |
|---|---:|---|
| 1 | 10 / 10 | ❌ y = 359 · 363 · 373 · 359 · 362 — **9 à 23 px SOUS la barre** |
| 2 | 21 / 14 | ❌ le plus proche : **337**, à 3 px au-dessus |
| **3** | **16 / 16** | ✅ **y = 349 et y = 350 — DANS la bande, et les deux rendent « TAP sur RAM »** |

🔴 **POURQUOI LES DEUX PREMIERS TOURS ONT ÉCHOUÉ, ET CE QUE ÇA APPREND** : `RAM` était à « -- »,
donc **sa jauge était VIDE** — une fine bande de fond, à peine visible. **On ne peut pas viser ce
qu'on ne voit pas.** Il a fallu **armer le mock** pour que la barre se remplisse et bouge avant
que la cible devienne atteignable.
⇒ **Le stimulus est prouvé** : `lv_bar` ne vole rien, le tap traverse jusqu'à la case.
⚠️ Et un constat non demandé, mais réel : **une bande de 10 px est presque impossible à viser au
doigt**. Les 47 appuis de la séance ne l'ont atteinte **que deux fois**. Le risque pratique que
l'AC redoutait est donc faible — mais c'est le correctif qui le rend nul, pas la difficulté de
visée.

---

## 14. LE PROTOCOLE v3 — mesuré le 2026-08-19 (dn4-6, P9.1b)

> Firmware **`690af25`**, SHA lu au bandeau. Extension **ADDITIVE** : ⛔ v1 et v2
> restent acceptées, et leurs témoins de non-régression restent **VERTS**.

### 14.1 CE QUI CHANGE, ET CE QUI NE CHANGE PAS

| | v2 | **v3** |
|---|---|---|
| `DN_LINK_PROTO_VERSION` | 2 | **3** |
| `..._VERSION_MIN` | 1 | **1** — ⛔ inchangé |
| `NB_CHAMPS_MAX` | 7 | **9** (5 fixes + **1 à 4 valeurs**) |
| `NB_CHAMPS_MIN` | 6 | **6** — inchangé |
| `DN_LINK_LIGNE_MAX` | 63 | **71** |
| `k_metriques[]` | `max1`/`max2`/`unite1`/`unite2`/`v2_attendue` | **`max[4]` · `unite[4]` · `n_grandeurs`** |
| `dn_link_vue_t` | `v1`/`v2`/`v2_connue` | **`v[4]` · `connue[4]` · `n`** |
| `DN_LINK_SAUT_MAX` | `3600 × METRIQUES` | ⛔ **INCHANGÉ** |

🔴 **AUCUNE MÉTRIQUE N'EST AJOUTÉE — DES GRANDEURS LE SONT.** Deux gardes avaient
été posées en revue « parce que `dn4-6` s'apprête à ajouter une métrique »
(`k_metriques[].nom == NULL`, sentinelle décalée de `k_pc[]`). **Ce motif était
faux.** Les gardes sont bonnes et restent ; ⛔ **on n'ajoute pas une métrique pour
leur donner raison**, et `SAUT_MAX` ne bouge donc pas.

⚠️ **`v2_attendue` (booléen) devient `n_grandeurs` (un COMPTE).** Un booléen ne
peut pas distinguer « `gpu` en attend 4 » de « `gpu` en attend 2 » — c'est
pourtant exactement le test qui envoie une trame mal formée en `rejets_format`.

### 14.2 LE PIRE CAS, RECOMPTÉ ET **VÉRIFIÉ PAR L'ÉMETTEUR**

```
$DN,3,4294967295,4294967295,gpu,1000000,1000000,1000000,1000000*FF
```
= **66 octets** — ⛔ pas estimé : `trame()` de l'agent produit la ligne et sa
longueur est **mesurée à 66**. `LIGNE_MAX = 71` laisse **5 octets** de marge.

✅ **L'INVARIANT SE RECALCULE, PAS SEULEMENT LA VALEUR.** Le REPL délivre
**124 caractères** au parseur (mesuré, dn4-1) ⇒ la bande *« ligne COMPLÈTE mais
trop longue »* passe de **64..124 = 61 o** à **72..124 = 53 o** : elle
**rétrécit de 13 % et RESTE ATTEIGNABLE**. Sans quoi `rejets_trop_longue`
deviendrait un compteur décoratif — et un compteur décoratif est un instrument
qui ment. ✅ Budget côté REPL : `66 + "pc " = 69 ≤ 124`.

### 14.3 🔴 W10 À N GRANDEURS — LE CHAMP VIDE

Une source qui rend `(46 %, °C inconnue, 53 W, 604 tr/min)` publie les **trois**
qu'elle connaît et **tait** la deuxième. Sur un fil **positionnel**, ça ne peut
être ni un décalage (la puissance s'afficherait dans la case de la température)
ni une troncature (deux valeurs VRAIES seraient perdues).

⇒ **UN CHAMP VIDE** : `$DN,3,911,1000,gpu,460,,2120,14500*CK`

✅ **Et le parseur savait déjà le voir** : il découpe le corps **à la main** et
non par `strtok`, précisément parce que `strtok` fusionne les séparateurs
consécutifs et que « ,, » lui serait invisible. **La capacité existait depuis
`dn2-2`, elle n'était pas exploitée.**
⚠️ Les `None` de queue sont **tronqués** (« je n'ai que trois grandeurs » et « ma
quatrième est inconnue » sont le même fait, et la forme courte économise des
octets). ⛔ Un champ **0** vide est un `rejets_format` : une trame sans sa valeur
principale ne dit rien, et l'agent ne doit alors **pas émettre** la métrique.

**VÉRIFIÉ SUR LA CARTE** — une valeur après un trou n'est **pas décalée** :
```
gpu -> case 1 GPU VIVANTE  46,0 % · -- (degC ATTENDUE, non publiee par la source) · 212,0 W · 1450,0 tr/min
```

### 14.4 LA CAMPAGNE DE BRUIT — 9 CAS, 9 COMPTEURS, AUCUN CROISEMENT

Chaque cas incrémente **le compteur attendu ET LUI SEUL** (diff avant/après) :

| trame injectée | compteur attendu | **mesuré** |
|---|---|---|
| `ver = 4` | `rejets_version` | ✅ |
| `ver = 1` à 7 champs | `rejets_format` | ✅ |
| `ver = 2` à 9 champs | `rejets_format` (champ EN TROP — **v2 reste v2**) | ✅ |
| `ver = 3` à 10 champs | `rejets_format` | ✅ |
| `ver = 3`, `disk` à 4 valeurs | `rejets_format` | ✅ |
| `ver = 3`, `gpu` v4 hors plafond | `rejets_bornes` | ✅ |
| ligne COMPLÈTE de 72..124 o | `rejets_trop_longue` | ✅ |
| ligne sans `*CK` | `rejets_tronquee` | ✅ |
| checksum FAUX | `rejets_checksum` | ✅ |

**LES TROIS TÉMOINS, TOUS ACCEPTÉS :**

| témoin | origine | **mesuré** |
|---|---|---|
| **v1** (agent `dn2-2` non modifié) | dn2-2 / dn4-1 AC2 | ✅ **VALIDE** |
| **v2** (agent `dn4-1` non modifié) | dn4-1 | ✅ **VALIDE** |
| **v3 à trou interne** | dn4-6 / W10 | ✅ **VALIDE, sans décalage** |

⚠️ **`rejets_bornes` a été prouvé PAR ACCIDENT avant sa campagne** : le premier
jeu « pire cas » de l'injecteur envoyait 9 999 999 dixièmes de Mb/s, au-dessus du
plafond de `k_metriques[]` ⇒ **8 `rejets_bornes` et rien à l'écran**. Le pire cas
d'un injecteur doit rester **dans la grammaire**, sinon on ne mesure pas la
lisibilité, on mesure le parseur.

### 14.5 L'AGENT — SEPT GRANDEURS SANS UN APPEL DE PLUS

| métrique | grandeurs publiées | source |
|---|---|---|
| `cpu` | `%` · `GHz` · **`max(cpu_percent(percpu))`** | `psutil` |
| `gpu` | `%` · `°C` · **`W` (idx 23)** · **`tr/min` (idx 14)** | **UN** `ADL2_New_QueryPMLogData_Get` |
| `ram` | `%` · `Go` totaux | `psutil` |
| `net` | `↓ Mb/s` · `↑ Mb/s` | `psutil` |
| `disk` | `Mo/s` | `psutil` |

✅ **Les deux indices ADL sont GRATUITS** : ils sortent de la **même structure**
que `_brut()` remplit déjà — ⛔ aucun appel supplémentaire.
✅ **Coût mesuré, ordre ALTERNÉ à chaque cycle** (n=958) : `cpu_percent()`
**161 µs** de médiane, `percpu` **287 µs**, les deux **383 µs/cycle** =
**0,0383 % d'un cœur** à 1 Hz — **facteur 26 sous le critère brief n°4**.
⚠️ **Correction d'un chiffre publié** : `percpu` était annoncé à
**0,07..0,10 ms** ; il vaut **0,287 ms** de médiane, **~3× plus cher**.
⚠️ La 1ʳᵉ série **n'était pas anormale** cette fois (158 contre 161 de médiane) :
l'alternance d'ordre est **la garde**, pas la preuve d'un défaut à chaque tir.
✅ **Aucun droit, aucun driver** : lancé depuis une session **NON élevée**.

⚠️ **`BORNES` (agent) est le MIROIR de `k_metriques[]` (firmware), recopié et non
dérivé** — le fil n'a pas de canal de négociation. **Risque assumé et NOMMÉ** :
une dérive se verrait en `rejets_bornes` qui monte, ⛔ pas en silence. ⇒ **les
deux tables bougent dans le MÊME geste.**

### 14.6 🔴 CE QUE CE FICHIER DOIT CORRIGER DANS §13

**`flush/cyc`, `px/cyc` et `duty` du régime (b) dépendent du RYTHME DE
L'ÉMETTEUR.** Même firmware, même jeu de valeurs, seul l'espacement des cinq
trames dans la seconde change :

| espacement | cycles/s | flush/cyc | px/cyc | duty |
|---|---:|---:|---:|---:|
| **40 ms** | 3,154 | 1,63 | **59 630** | 7,96 % |
| **4 ms** | 2,194 | 2,34 | **85 712** | 9,81 % |

⇒ **32 % d'écart sur `px/cyc`, produit par l'instrument.** ⛔ Un relevé de régime
(b) qui ne déclare pas son espacement n'est comparable à rien.
`tools/dn_injecteur.py --espacement` le rend explicite. Voir §18.0 du fichier
d'affichage.


---

# 15. LE PROTOCOLE v3 À QUATRE PARTOUT — les sondes Ring0 arrivent sur le fil (dn4-8, P9.3c)

**2026-08-21.** ⛔ **Séance WSL uniquement** : la carte n'a pas été touchée, `COM3` n'a pas été
ouvert, rien n'a été flashé. Ce qui suit est du **code et de l'arithmétique**, ⛔ pas une mesure
de la carte ni de la tour.

## 15.1 Ce que D13 demandait, et le mur qu'elle a rencontré

D13 (correct-course du 2026-08-21) rouvre le **Ring0 par service tiers** :
`LibreHardwareMonitor` tourne en permanence sur la tour et l'agent **lit** ses valeurs.
⛔ **L'agent ne fait aucun Ring0 lui-même** — c'est ce qui rend la chose acceptable.

🔴 **LE MUR N'EST PAS L'OCTET, C'EST LA QUATRIÈME GRANDEUR.** `DN_LINK_GRANDEURS_MAX = 4`, et la
disposition complète de D13 §4.4 en demandait **SIX** sur `disk` :
`Mo/s` · `tr/min` moyen · **lecture** · **écriture** · ventilo boîtier · ventilo CPU.

**Les quatre voies, pesées avec la disposition COMPLÈTE sur la table :**

| voie | ce qu'elle coûte | verdict |
|---|---|---|
| **(a)** `disk` = `Mo/s` · moyen · boîtier · CPU | ⛔ la séparation **lecture/écriture** de §4.4 tombe | 🎯 **RETENUE**, amendée par la 4ᵉ voie |
| **(b)** `disk` = `Mo/s` · lecture · écriture, ventilos **ailleurs** | ⚠️ **il y a un « ailleurs »** — `ram` et `net` ont **2 places libres chacune** sur les 4. ⛔ **Mais `k_pc[]` mappe métrique → CASE** : un ventilateur publié sous `ram` atterrirait dans la case RAM, que `dn4-9` ne pourrait jamais montrer comme un ventilateur | ⛔ **écartée**, et le motif est l'AFFICHAGE, pas le fil |
| **(c)** monter `GRANDEURS_MAX` à 6 | pire cas au gabarit → **~89 o > 71** ⇒ `LIGNE_MAX` bouge ; `v[]`, `connue[]`, `max[]`, `unite[]` côté fil ; **et `dn_widget` a des tampons INDEXÉS SUR 4** (`txt[4][16]`, `brut[4]`) | ⛔ **écartée** : large, et ⛔ **rien ne l'exige** une fois (a)+(4ᵉ voie) posées |
| **(d)** une 6ᵉ métrique `fan` | +1 trame/s (+20 % d'écho console), `k_pc[]`/`k_source[]`/`k_desc[]`/`k_nom[]`/`k_widget[]`/`cmd_widget` à renseigner, ⛔ **et pas de case libre** (`DN_UI_METRIQUES = 6`, la 6ᵉ est `AMBIANCE`/BME680) | ⛔ **écartée** |

🎯 **LA 4ᵉ VOIE, DÉBLOQUÉE PAR UNE DÉCISION OWNER**, verbatim : *« oui clairement le détail
connaîtra pour chaque case plus d'information »*. Si la **case** et le **détail** ont des
**comptes différents**, ils peuvent avoir des **sélections différentes** :

```
fil    cpu = [ % · GHz · c.max · °C ]   <- ordre INCHANGÉ, témoin v3 INTACT
case   montrera les indices [0, 1, 3]    -> % · GHz · °C   (ce que D13 demande)
détail montrera les 4                    -> + c.max        (décision owner)
```

⇒ Les trois options gelées au cadrage sacrifiaient toujours l'une des trois contraintes.
Celle-ci n'en sacrifie aucune. ⚠️ **Mais le mécanisme n'existe pas** — `detail_reparametrer()`
lit `desc_n(idx)`, le compte de la **case** — ⇒ **legs explicite à `dn4-9`**.

🔴 **CE QUI TOMBE, ET IL FAUT L'ÉCRIRE** : **la séparation lecture/écriture de D13 §4.4**.
⛔ Ce n'est **pas** un arbitrage d'implémentation, c'est une **réduction de périmètre**.
⇒ **portée à l'owner et au ledger**, ⛔ pas rognée en silence.

⚠️ **Et « moyenne entrant/sortant » a été AMENDÉE PAR LA MESURE** : **il n'existe aucun flux
entrant mesurable.** Le 200 mm de façade n'a pas de fil tachymétrique (`0 RPM` **dans le BIOS
aussi**) et le ventilateur du bas est **chaîné** avec un extracteur sur un seul tachy. Une
« moyenne entrante » serait calculée sur **rien**. ⇒ seule la **sortante** existe
(`TOP_OUT` + `REAR_OUT`, deux canaux de même sens).

## 15.2 L'ordre du fil — le piège qui casse un témoin **en silence**

D13 veut que la case CPU montre `[%, GHz, °C]`. L'affichage lit les grandeurs **0..n-1 dans
l'ordre** ⇒ naïvement, la °C devrait être l'**index 2**.

🔴 **ET ALORS UN AGENT v3 NON MODIFIÉ MENT SANS QU'AUCUN COMPTEUR NE BOUGE.** L'agent de `dn4-6`
envoie `…,cpu,52,32,350` ; le `350` (c.max, dixièmes de %) atterrirait en index 2, désormais
`degC`, et `pc` imprimerait **« 35,0 degC »**. Le plafond passant de `1000` à `1500`,
⛔ **`rejets_bornes` ne s'incrémenterait même pas.** **Le témoin de non-régression fabriquerait
lui-même le chiffre faux et plausible qu'il existe pour exclure.**

✅ **TRANCHÉ : la °C est en index 3, `c.max` reste en index 2.** L'ordre du fil **ne bouge pas**
sur 0..2.
⇒ **le témoin v3 est RE-QUALIFIÉ, ⛔ pas retiré** — il continue de porter exactement le même sens.
⇒ **le témoin v1** (agent `dn2-2`, 6 champs, `cpu` seul) est **intact** : `rejets_version = 0`.
⚠️ **À vérifier sur la carte en AC7** — ici c'est une propriété du code, ⛔ pas une mesure.

## 15.3 Le pire cas recompté — la prédiction est **confirmée sur ses nombres et démentie sur sa conclusion**

Instrument : **`tools/recompte_trame_dn48.py`**, qui construit la trame avec
`dn_agent.trame()` — ⛔ pas en additionnant des longueurs à la main.

| convention | cpu | gpu | disk | pire cas |
|---|---:|---:|---:|---|
| **plafonds RÉELS** | 54 o | 57 o | **64 o** | 🔴 **`disk` = 64 o** (marge 7) |
| **gabarit** (4 × 1000000, convention `dn4-6`) | 66 o | 66 o | **67 o** | 🔴 **`disk` = 67 o** (marge 4) |

✅ **L'INVARIANT TIENT** : `DN_LINK_LIGNE_MAX = 71` **ne bouge pas** · la bande *« ligne COMPLÈTE
mais trop longue »* reste **72..124 = 53 octets**, donc **atteignable**, donc
`rejets_trop_longue` reste un compteur qui compte · budget REPL **67 + « pc » + espace = 70 ≤ 124**.

⛔ **CE QUI EST RÉFUTÉ** : la prédiction gelée annonçait *« le pire cas RESTE `gpu` = 66 o »*.
**Faux.** C'est **`disk`**, des deux côtés de la convention. Et **la cause n'est pas celle que la
prédiction nommait** : elle écrivait *« elle tombe si un plafond de ventilateur est posé à
1 000 000 »*. Or les plafonds sont à **100 000** et le gabarit donne **quand même 67** — ce qui
dépasse `gpu`, c'est que **« disk » compte un caractère de plus que « gpu »**. *Le nom de la
métrique est dans la ligne.*

🔴 **ET LA PRÉDICTION COMPARAIT DEUX CHOSES MESURÉES AUTREMENT** : elle chiffrait `disk` à ses
plafonds **réels** (64) et `gpu` au **gabarit** (66), puis les rangeait dans la même colonne.
⛔ C'est la doctrine *« à service rendu égal »* du dépôt, violée par le dépôt, **dans sa propre
prédiction**. ⇒ les deux conventions sont désormais publiées **séparément**, et c'est le
**gabarit** qui dimensionne la constante.

## 15.4 🎯 La garde du miroir — elle se joue AVANT la séance carte, en une seconde

`k_metriques[]` (firmware) et `BORNES` (agent) sont **recopiées**, ⛔ pas dérivées. Le dépôt
l'assume et l'écrit. ⚠️ **Mais le seul témoin de la dérive était `rejets_bornes` qui monte côté
CARTE** — donc **après** un build, un flash et une séance.

⇒ `tools/recompte_trame_dn48.py` **compare les deux tables** (métriques, `n_grandeurs`, plafonds)
et **recompte l'invariant**, en WSL, en une seconde.

✅ **ET IL EST ÉPROUVÉ PAR MUTATION, ⛔ pas supposé** — trois mutants, trois rouges :

| mutant | ce que la garde a dit |
|---|---|
| `BORNES["cpu"][3]` 1500 → **1400** | ✖️ *plafonds firmware ≠ plafonds agent* — `fw=[…,1500] ag=[…,1400]` |
| `k_metriques[disk].n_grandeurs` 4 → **3** | ✖️ *n_grandeurs ≠ nb de plafonds déclarés* |
| `DN_LINK_LIGNE_MAX` 71 → **63** | ✖️ *pire cas atteignable* (64 > 63) **et** *au gabarit* (67 > 63) |

## 15.5 🔴 TROIS DÉFAUTS D'INSTRUMENT DE CETTE SÉANCE — les miens

1. 🔴 **LE TIMEOUT ÉTAIT APPLIQUÉ PAR TENTATIVE, ET `_get()` EN FAIT DEUX.** Pire cas **mesuré :
   802 ms pour un plafond posé à 400 ms**. ⇒ le motif écrit sur la constante (« 0,4 s laisse 0,6 s
   aux cinq autres postes ») était **faux** : il en laissait 0,2.
   ⚠️ **ET LE CONTRÔLE QUI PORTAIT DESSUS NE POUVAIT PAS LE VOIR** : il n'avait qu'une **borne
   inférieure** (« la lecture a bien été coupée »), donc il épinglait **VERT** un dépassement du
   **double**. ⇒ corrigé : budget **global** côté produit, **deux bornes** côté contrôle. Vérifié
   après correctif : **401 ms** pour 400 posées.
2. 🔴 **PYTHON A SERVI UN BYTECODE PÉRIMÉ.** Pendant le test de mutation,
   `agent/__pycache__/dn_agent.cpython-312.pyc` rendait encore `1400` alors que le `.py` disait
   `1500` : **l'outil a vérifié un fichier qui n'existait plus**, et a conclu ROUGE sur un arbre
   SAIN. ⚠️ **Dans l'autre sens il aurait conclu VERT sur un arbre cassé.** ⇒ `dont_write_bytecode`,
   purge du cache, **et surtout : les deux outils publient désormais l'empreinte SHA256 de la
   source qu'ils ont réellement lue.** *Un instrument qui ne nomme pas son sujet ne prouve rien
   sur ce sujet.*
3. ⚠️ **La sonde de démarrage du harnais attendait une RÉPONSE, pas une ÉCOUTE** : en mode
   « lent (2 s) » elle concluait *« le stub n'a pas démarré »* sur un stub parfaitement démarré —
   **l'instrument mesurait la lenteur qu'il était censé mettre en place**. ⇒ `connect()` TCP nu.

## 15.6 Ce qui est exercé, et ⛔ ce qui ne l'est pas

**`tools/verif_source_lhm_dn48.py`** — il **importe et appelle** `agent/dn_agent.py`, ⛔ il ne le
rejoue pas. Six scénarios, **tous verts** :

| # | scénario | ce qu'il établit |
|---|---|---|
| 1 | lecture nominale | 5/5 sondes · `cpu` et `disk` à **4 grandeurs** · °C bien en **index 3** · `Mo/s` en position 0 · **pire trame réelle 56 o ≤ 71** |
| 2 | une sonde **muette** | **champ vide** (`…,disk,18227,9795,,8615*1A`), la suivante **NON décalée**, absence **comptée**, ⛔ **pas** comptée en panne |
| 3 | valeur **négative** | devient un **champ vide**, ⛔ **pas** un `0` écrêté, comptée sur **son** compteur |
| 4 | lecture **lente** | coupée au **timeout** · panne **comptée et nommée** · 🎯 **`ram`/`net` intactes, `cpu` et `disk` survivent avec leurs grandeurs non-LHM** |
| 5 | LHM **absent** puis qui **monte** | 🎯 **reprise sans redémarrer l'agent** · les échecs restent **comptés** |
| 6 | LHM **arrêté en cours** | la °C devient un **champ vide** · ⛔ **aucune valeur figée n'a survécu** |

Boucle complète, `--stdout --duree 4` contre le stub : **16 trames, 4,00 trames/s,
0 erreur d'envoi, 🎯 0 recalage de cadence.**

⛔ **CE QUE RIEN DE TOUT ÇA NE PROUVE, ET IL FAUT LE LIRE** :
- ⛔ **aucune grandeur n'est qualifiée** (AC4) — le serveur en face est un **stub** qui rejoue une
  capture **n = 1** ;
- ⛔ **AC8 n'est pas soldé** : il exige le **VRAI** service coupé pendant que l'agent tourne ;
- ⛔ **la carte n'a rien reçu** (AC7) ;
- ⛔ **aucun coût n'est mesuré** (AC9) : les 1,7 ms / 3,1 ms relevés sont ceux d'un **stub local en
  WSL**, ⛔ pas de LHM sur la tour.

## 15.6bis 🔴 ORDRE DE DÉPLOIEMENT — le firmware D'ABORD, l'agent ENSUITE

⛔ **Ce n'est pas une préférence de confort — l'ordre inverse fait DISPARAÎTRE deux cases.**
Décision owner du **2026-08-21** (revue de code `dn4-8`) : on **documente l'ordre**, ⛔ on ne pose
**pas** de garde de version — ce serait un changement de protocole, donc une story à part.

L'agent vit sur la tour et le firmware se flashe séparément : **rien ne les synchronise**.
Or `dn_link.c` **rejette la trame ENTIÈRE** si elle porte plus de valeurs que la métrique n'en
publie (`nv > k_metriques[].n_grandeurs` ⇒ `rejets_format`) — doctrine **délibérée** : *« plus de
valeurs que la métrique n'en PUBLIE est un défaut de format, ⛔ pas une donnée en trop qu'on
jetterait en silence »*.

⇒ **Agent `dn4-8` + firmware `dn4-6`** = les trames `cpu` (4 valeurs) et `disk` (4 valeurs) sont
rejetées **en entier** : on ne perd pas seulement la °C et les tr/min, **on perd aussi le `%` CPU
et le `Mo/s`**.

🔴 **ET LE SYMPTÔME DÉPEND DE LHM, CE QUI LE REND DÉROUTANT :**

| État de LHM | Ce que l'agent émet | Ce que la carte affiche |
|---|---|---|
| **arrêté** | `cpu` à 3, `disk` à 1 (les `None` de queue sont **tronqués**) | ✅ tout va bien |
| **démarré** | `cpu` à 4, `disk` à 4 | 🔴 **deux cases sur cinq passent à « -- »** |

⚠️ **Donc : « ça marchait, j'ai lancé LHM, deux cases sont mortes » ⇒ le firmware est en retard sur
l'agent.** ⛔ Ne pas chercher du côté de LHM ni du câble : **reflasher**.
⛔ Et rien dans la trame ne déclare « je porte plus que tu ne sais » — c'est précisément pourquoi
l'ordre doit être **écrit**.


---

## 15.7 🔴 La lecture LHM est la PREMIÈRE du cycle, et **avant** `t = monotonic()`

⛔ **Ce n'est pas cosmétique — c'est ce qui empêche un débit faux.** `net` et `disk` sont des
**deltas de compteurs cumulés** divisés par `t_now − t_prev`. Placée **entre** `t` et les lectures
`psutil`, la latence LHM entrerait dans la fenêtre **à une seule extrémité** : un tir à **600 ms**
(`LHM_TIMEOUT_S`) sur un cycle nominal à 16 ms rendrait un Δt **sous-estimé de 0,58 s**, donc un
**débit disque surestimé de ~58 %** — un chiffre **frais et faux**, la famille exacte que la
resynchronisation de `dn2-2` existe pour empêcher.
> ⚠️ **Corrigé en revue de code le 2026-08-21.** Ce paragraphe disait « un tir à 400 ms (le timeout)
> ⇒ 0,38 s ⇒ ~38 % » : un calcul **dérivé d'un plafond mort**, alors que §16.5 — plus bas dans ce
> même document — porte le timeout à **600 ms par la mesure**. ⛔ C'est exactement la classe de
> défaut qu'AC10 existe pour fermer, et elle s'était refermée à l'intérieur de la story elle-même.
> 🎯 Le chiffre corrigé est **pire** que l'ancien : l'argument en sort renforcé, pas affaibli.
✅ **Placée AVANT `t`, sa latence est hors fenêtre des deux côtés** (elle décale `t` et les
compteurs du même montant) et **s'annule**.

## 15.8 Les dépendances de l'agent, RE-PUBLIÉES avec leur statut (dn4-8)

| dépendance | statut | pourquoi |
|---|---|---|
| `psutil` **7.2.2** | ✅ déjà installée | CPU, RAM, réseau, disque |
| `pyserial` | ✅ déjà installée | branche A (COM3) |
| `websockets` | ✅ déjà installée | branche B, **écartée** par la fourche `dn2-2` |
| `ctypes` + `atiadlxx.dll` | ✅ **stdlib + DLL du pilote** | GPU (% · °C · W · tr/min) |
| 🆕 **`http.client`** | ✅ **STDLIB** | la lecture LHM. ⛔ **pas `requests`** : il fallait la **connexion** (keep-alive) |
| 🆕 **`re`** | ✅ **STDLIB** | le parseur d'une ligne `/metrics` |
| `pywin32` | ✅ présente, **NON UTILISÉE** en régime | — |
| `pynvml` | ❌ absente | **inapplicable** : la tour est AMD |
| **`dotnet`** | ✅ **PRÉSENT** (runtimes 6 et 7) | 🔴 **`dn2-2` disait le contraire — RÉFUTÉ le 2026-08-21.** ⚠️ La **conclusion** tient pour une autre raison : **pas de .NET 10**, donc le build `.NET Framework` de LHM reste le bon |

⇒ ✅ **LA LIGNE « `dn4-1` N'AJOUTE AUCUNE DÉPENDANCE » EST CONFIRMÉE ET ÉTENDUE : `dn4-8` NON
PLUS.** Les deux modules ajoutés sont la **stdlib**.
⚠️ **MAIS UNE DÉPENDANCE D'UN AUTRE ORDRE APPARAÎT, ET ELLE N'EST PAS PYTHON** : ces grandeurs
exigent **LibreHardwareMonitor installé, élevé et permanent sur la machine**. ⛔ Le critère owner
de D8 (*« générique et libre de droits, réutilisable sur toutes les configs »*) **ne tient plus
pour elles** — les onze autres grandeurs, si. **C'est un coût assumé, ⛔ pas un oubli.**

## 15.9 La table des sondes — une **configuration**, avec sa **provenance**

Décision owner : *« on code comme ça de façon à plus tard ajouter des menus de personnalisation
et aussi changer les liens si mauvais »*. ⇒ `LHM_SONDES` vit **côté agent**, ⛔ jamais dans le
firmware : c'est une propriété de **cette** tour.

| clé | `SensorId` | provenance |
|---|---|---|
| `cpu.degc` | `/intelcpu/0/temperature/10` | **MESURÉ** (LHM 0.9.6, 2026-08-21) — « CPU Package », recoupé par le Super I/O `/lpc/nct6792d/0/temperature/0` (40,5 contre 41,0 : **1,2 %**). ⚠️ **instantané n = 1** |
| `fan.top_out` | `/lpc/nct6792d/0/fan/0` | **MESURÉ** (jointure BIOS↔LHM par RPM, 2026-08-21) — `CPU_FAN2` |
| `fan.cpu_noctua` | `/lpc/nct6792d/0/fan/1` | **MESURÉ** (idem) — `CPU_FAN1`, le ventirad |
| `fan.case_group` | `/lpc/nct6792d/0/fan/2` | **MESURÉ** (idem) — ⚠️ **DEUX ventilateurs chaînés sur UN tachy** |
| `fan.rear_out` | `/lpc/nct6792d/0/fan/4` | **MESURÉ** (idem) — 140 mm arrière |

⛔ **`FRONT_IN` N'EST PAS DANS CETTE TABLE ET N'Y SERA JAMAIS** : pas de fil tachymétrique,
`0 RPM` **dans le BIOS aussi**. ⚠️ Il tourne — **il ne le dit pas**. ⇒ `dn4-9`, qui doit *« nommer
chaque ventilateur »*, a un ventilateur qu'elle **ne pourra jamais nommer**.

## 15.10 Entrées au ledger, portées par `dn4-8` — ⛔ par AJOUT, jamais par effacement

| # | Entrée | État | Condition de réouverture / de clôture |
|---|---|---|---|
| L1 | **Le démarrage automatique de l'AGENT** — 1ʳᵉ moitié du critère n°4 du brief (*« démarre avec la session »*) | 🔴 **NON TENUE** : l'agent est lancé à la main | ⛔ Hors périmètre `dn4-8`. ⚠️ **Ironie à écrire** : **LHM, lui, démarre tout seul depuis le 2026-08-21** — le service tiers tient le critère que le produit ne tient pas |
| L2 | **L'unité du « < 1 % CPU »** | 🔴 **TOUJOURS NON TRANCHÉE** (AC9 de `dn4-1` = `PARTIAL`) | Le brief ne dit pas s'il vise **% d'un cœur** (❌ 2,421) ou **% machine** (✅ 0,1513). ⛔ Ne pas cocher le critère tant que l'unité n'est pas dite |
| L3 | **Le `+0,26 pt` NON EXPLIQUÉ** de l'agent livré (`d5d3539`) | 🟠 ouvert | ⛔ Un delta non expliqué **se déclare**, il ne se lisse pas. AC9 de `dn4-8` doit l'attribuer poste par poste |
| L4 | 🆕 **La règle « valeur négative ⇒ champ vide » ne vaut QUE pour les grandeurs LHM** | 🟠 **asymétrie ASSUMÉE et NOMMÉE** | Motif : « 0 tr/min » est une **vraie** valeur (fan-stop), donc un `-1` écrêté à 0 fabriquerait un mensonge **indistinguable**. Les autres grandeurs gardent l'écrêtage compté de `_dx()`. ⛔ **La question générale n'est pas tranchée** |
| L5 | 🆕 **La séparation LECTURE / ÉCRITURE du disque** | 🔴 **HORS PÉRIMÈTRE V1** (`sprint-change-proposal-2026-08-21b.md`) | ⚠️ **Dette de PLACE, ⛔ pas de source** : `psutil.disk_io_counters()` la rend déjà, gratuitement. Rouvrir le jour où une place existe sur le fil — **précédent exact : le `tr/min` du GPU** |
| L6 | 🆕 **`TOP_OUT` et `REAR_OUT` ne sont pas distinguables sur le fil** | 🔴 **fondus** dans la moyenne d'extraction | Rouvrir si `DN_LINK_GRANDEURS_MAX` bouge un jour. ⚠️ Les deux **canaux existent** et sont mesurés séparément **côté agent** — c'est la publication qui fusionne |
| L7 | 🆕 **`FRONT_IN` (200 mm façade) ne sera JAMAIS publiable** | ⛔ **CLOS — matériel** | **Pas de fil tachymétrique**, `0 RPM` **dans le BIOS aussi**. ⛔ **Aucune condition de réouverture logicielle** : il faudrait changer le ventilateur. ⚠️ **Il tourne, il ne le dit pas** |
| L8 | 🆕 **`CASE_GROUP` = UN tachy pour DEUX ventilateurs chaînés** | 🟠 **limite CONNUE et NOMMÉE** | **Si celui du bas s'arrête, rien ne le dira.** ⛔ Ne pas le rebaptiser d'un nom qui prétendrait le contraire |
| L9 | 🆕 **Toute grandeur qui ne qualifiera pas au critère W2 (AC4)** mais dont la source est prouvée | ⏳ **en attente d'AC4** | ✅ **Repli PRÉ-AUTORISÉ** : elle est publiée quand même, et le fait est **transmis à `dn4-9` comme une réserve d'affichage**. ⛔ Une case qui ne bouge jamais est une case morte |

⚠️ **`FAN_PCT` (« idx 15, 18 % »), cité par D13, N'EXISTE NULLE PART DANS LE CODE** — seul
`_PM_FAN_RPM = 14` est implémenté, et le « 18 % » est un **instantané n = 1 jamais échantillonné**.
⛔ **Ne pas le citer comme un acquis.**


---

# 16. SÉANCE CARTE DU 2026-08-21 — AC7, AC8 et AC9 (dn4-8, P9.3c)

**SHA lu au bandeau : `App version: 4c3a3f7`** — ⛔ pas déduit du dépôt, **sans `-dirty`**,
arbre `porcelain` **vide** au moment du flash. `SPI Flash Size : 16MB`.

## 16.1 Baseline T0 — les gardes des marches du dessous

| Instrument | Relevé | Verdict |
|---|---|---|
| `cfg` | `num_fbs=1 bounce_px=7680 draw_lines=128 draw_psram=0` | ✅ configuration de la mesure, écrite |
| `pc` à froid | 0 valides · **les six compteurs de rejet à 0** | ✅ |
| `touch` | 1290 lectures · **0 erreur I²C** | ✅ |
| BME680 | 23,4 °C / 53,6 %, âge 497 ms · `config relue : 0x72=04 0x74=84 0x75=08` | ✅ |
| `fps 15` | **37,40 Hz** mesuré = **37,40 Hz** théorique, écart **+0,00 %** | ✅ |
| bandeau | ⚠️ `E gpio_install_isr_service` — **antérieure et attendue**, ⛔ pas nouvelle | ✅ |

🎯 **ET L'AUDIT DE BOOT CONFIRME AC5 TOUT SEUL**, sans qu'on ait rien à lui demander :

```
k_desc[CPU]    : 3 grandeur(s) affichee(s), 4 PEUPLEE(S) — `widget grandeurs 0 4` est jouable
k_desc[DISQUE] : 1 grandeur(s) affichee(s), 4 PEUPLEE(S) — `widget grandeurs 4 4` est jouable
precision d'affichage : 6 cases auditees, 0 trou (AC9)
```

## 16.2 AC7 — les quatre grandeurs arrivent, et le trou ne décale rien

**Par injection** (`tools/dn_injecteur.py`, jeux étendus) :

| jeu | ce que `pc` a rendu |
|---|---|
| `reel` | `cpu 5,2 % · 3,2 GHz · 35,0 % · 41,0 degC` · `disk 0,2 Mo/s · 979,5 · 283,9 · 861,5 tr/min` |
| `trou` | `cpu 54,0 % · -- (GHz) · 88,0 % · -- (degC)` · `disk 480,0 Mo/s · 1200,0 · -- (tr/min) · 1400,0` |

🎯 **LE CONTRÔLE DISCRIMINANT** : dans le jeu `trou`, le champ vide est en position **interne** et
**`1400,0` est resté en position 3**. ⛔ Un `strtok` aurait fusionné les `,,` et fait glisser la
valeur d'un cran, **en silence**. Le parseur découpe le corps à la main, précisément pour ça.
⚠️ Et `pc` boucle jusqu'au compte **DÉCLARÉ** par `k_metriques[]`, ⛔ pas jusqu'à ce que la trame a
porté : c'est ce qui lui permet de dire *« attendue mais absente »* — un silence **très différent**
de *« pas de grandeur là »*.

**Campagne de bruit — 10 cas, chacun dans SON compteur ET LUI SEUL** (`tools/campagne_bruit_dn48.py`,
diff avant/après sur les six compteurs) :

| trame injectée | o | compteur touché |
|---|---:|---|
| version hors `[1..3]` | 27 | `rejets_version` |
| `ver=1` à 7 champs | 31 | `rejets_format` |
| `ver=2` à 9 champs | 39 | `rejets_format` |
| plus de valeurs que `ram` n'en publie | 39 | `rejets_format` |
| 🆕 **`cpu` degC 1600 > 1500** | 40 | **`rejets_bornes`** |
| 🆕 **`disk` tr/min 999999 > 100000** | 47 | **`rejets_bornes`** |
| ligne COMPLÈTE **dans la bande 72..124** | **78** | **`rejets_trop_longue`** |
| ligne sans `*CK` | 24 | `rejets_tronquee` |
| checksum faux | 27 | `rejets_checksum` |
| 🆕 **champ vide en position 0** | 36 | `rejets_format` |

✅ **TÉMOIN v1** (agent `dn2-2` **non modifié**, `$DN,1,42,123456,cpu,153*47`) : `rejets_version = 0`
et la case CPU **VIVANTE**. ⇒ **l'extension reste additive.**
🎯 **ET LA BANDE 72..124 EST CONFIRMÉE ATTEIGNABLE SUR LA CARTE** — mon recomptage n'était
qu'arithmétique ; une ligne de 78 o l'a prouvée sur le silicium.

**Régime réel, agent sur `COM3`** (⛔ pas seulement par injection) :

```
cpu  -> 50,7 % · 3,2 GHz · 58,6 % · 41,0 degC        · seq 96
disk -> 0,0 Mo/s · 994,4 tr/min · 294,9 tr/min · 872,1 tr/min
100 trames / 20 s = 4,97 trames/s · 0 erreur d'envoi · 0 recalage de cadence
echo console : 246,5 o/s · 5,07 lignes/s
latence acceptation->label : n=728 · min 4 ms · moy 167 ms · max 316 ms
```

### 🎯 CONSTAT OWNER, À L'ŒIL — la preuve qu'aucune console ne pouvait donner

**Agent réel sur `COM3`, données réelles qui bougent, dalle regardée pendant le tir.**
Question posée en trois points, réponse verbatim : *« 1 oui c'est ca pas la température · 2 oui 1
seul ligne · 3 oui vivantes »*.

| Contrôle | Attendu | Constaté |
|---|---|---|
| Case **CPU** | **TROIS** lignes (`%` · `GHz` · `c.max`), ⛔ **pas** la °C | ✅ *« pas la température »* |
| Case **DISQUE** | **UNE** ligne (`Mo/s`), ⛔ pas les `tr/min` | ✅ *« 1 seule ligne »* |
| Les six cases | **vivantes**, des chiffres qui bougent | ✅ *« vivantes »* |

🔴 **C'EST LA CLÔTURE D'AC5, ET ELLE NE POUVAIT VENIR QUE DE L'ŒIL.** La console prouve ce
qui circule **sur le fil** ; elle ne peut pas dire ce que la **dalle dessine**. Le fil porte
QUATRE grandeurs sur `cpu` et sur `disk`, l'écran en montre **trois** et **une** — patron `gpu`
exactement (`desc_peuplees = 4` pour `n_grandeurs = 3`).
⛔ **`dn4-8` a le droit de mettre les grandeurs sur le fil, ⛔ pas à l'écran** : c'est `dn4-9`, et
D13 impose l'ordre. Une 4ᵉ ligne sur CPU aurait été une **régression**, ⛔ pas une avance.
⚠️ **Et c'est un constat SENSORIEL, donc il est de l'OWNER, ⛔ jamais de l'agent** — la règle du
dépôt, et elle vaut ici plus qu'ailleurs : un compteur vsync tourne aussi écran noir.

## 16.3 🔴 AC8 — les TROIS scénarios, sur le VRAI service

⛔ **Aucun n'est simulé.** LHM a été réellement arrêté et relancé pendant que l'agent tournait.

| # | scénario | ce que `pc` a rendu | pannes |
|---|---|---|---|
| **1** | LHM **jamais démarré** | `cpu … -- (degC ATTENDUE)` · `disk 0,6 Mo/s · -- · -- · --` | `lhm:TimeoutError=12` |
| **2** | LHM **arrêté EN COURS** | `cpu 8,7 % · 1,2 GHz · 25,4 % · -- (degC ATTENDUE)` · `disk 0,2 Mo/s · -- · -- · --` | `lhm:TimeoutError=16` |
| **3** | LHM **redémarré** | `cpu 14,3 % · 3,2 GHz · 28,8 % · 40,5 degC` · `disk 0,3 Mo/s · 984,2 · 288,7 · 862,9` | ✅ **REPRIS après 21 échecs** |

🎯 **⛔ AUCUN COMPTEUR DE REJET N'A MONTÉ DANS LES TROIS.** C'est le contrôle le plus discriminant
d'AC8, et il tient : **une absence de donnée n'est pas une erreur de protocole.**
✅ Le message de panne est imprimé **UNE SEULE FOIS** par type, comme promis.
✅ **La reprise se fait SANS redémarrer l'agent** — verbatim du bilan : *« source `lhm` a REPRIS
après 21 échec(s) consécutif(s) — la connexion persistante s'est rétablie SANS redémarrer l'agent »*.
✅ **Le `Mo/s` survit à chaque fois** : aucune case ne s'est éteinte. ⚠️ **La péremption de 3 s ne
s'applique à AUCUNE case, et c'est DÉLIBÉRÉ** — aucune grandeur LHM n'est en position 0. C'était la
décision d'AC5, et c'est elle qui empêche l'arrêt de LHM d'emporter le débit disque.

### 🎯 LE CYCLE DE TRANSITION, CAPTURÉ — et il valide une décision de conception

Au scénario 2, le bilan a rendu :

```
⚠️ ABSENCES LHM (LHM a REPONDU, sans cette valeur — champ VIDE sur le fil, ⛔ PAS une panne) :
   cpu.degc=1 · fan.case_group=1 · fan.cpu_noctua=1 · fan.rear_out=1 · fan.top_out=1
🔴 PANNES DE SOURCE : lhm:TimeoutError=16
```

⇒ **EXACTEMENT UN cycle** où LHM **a répondu** alors que son arbre de capteurs était **déjà
démonté** : le serveur HTTP servait encore, les sondes non.
🔴 **Sans la séparation `pannes` / `absences`, ce cycle-là aurait été INDISCERNABLE des 16
timeouts.** La décision *« une absence n'est pas une panne — deux diagnostics contraires, deux
compteurs »* avait été prise **sur un raisonnement** (le patron `tronquee`/`trop_longue`) ; elle a
**payé au premier test réel**.

## 16.4 🔴 SUR CETTE TOUR, UN PORT FERMÉ NE REFUSE PAS — IL PEND

Mesuré pendant que LHM était coupé, `socket.create_connection` sur le Python de la tour :

| cible | timeout posé | résultat, n=5 |
|---|---|---|
| `127.0.0.1:8085` | 2,0 s | **2016 / 2015 / 2009 / 2016 / 2013 ms** → `TimeoutError` |
| `localhost:8085` | 4,0 s | **4019 / 4029 / 4024 ms** (deux adresses × 2 s) |

⛔ **Aucun `ECONNREFUSED` rapide, jamais.** C'est l'inverse exact de WSL, où l'absence de LHM rend
`ConnectionRefusedError` **instantanément** (mesuré au harnais d'exercice).
⚠️ **La signature (drop plutôt que reject) évoque un pare-feu — ⛔ MAIS JE NE L'AI PAS TESTÉ, donc
je ne le nomme pas comme cause.** Entrée au ledger.

**Trois conséquences, toutes mesurées :**
1. 🎯 **Le timeout EST le détecteur.** « LHM absent » ne peut pas se détecter plus vite que lui.
2. L'agent brûle **~611 ms de chaque cycle** en attente quand LHM est coupé — ⚠️ mais c'est de
   l'**attente d'E/S**, ⛔ pas du CPU : **`0 recalage de cadence`** mesuré, et le critère n°4 n'est
   pas touché.
3. ⚠️ **La prémisse écrite dans `_get()` est à demi fausse** : *« la seconde tentative existe pour
   la connexion PÉRIMÉE, qui échoue IMMÉDIATEMENT »* vaut pour une connexion **réinitialisée par le
   pair**, ⛔ **pas** pour un port fermé. Dans ce cas-là, la première tentative consomme tout le
   budget et il n'y a pas de retry — ce qui **reste le comportement correct**.

## 16.5 🔴 LE TIMEOUT DE 400 ms ÉTAIT TROP COURT — porté à 600 ms PAR LA MESURE

| tir | LHM | moyenne | MAX | échecs |
|---|---|---:|---:|---:|
| régime réel (20 s) | debout | 43,8 ms | **377,5 ms** | 0 |
| régime réel (12 s) | debout | 8,8 ms | 20,6 ms | 0 |
| AC9 (60 s) | debout | 26,7 ms | 🔴 **454,7 ms** | 🔴 **1** |
| **après correctif** (45 s) | debout | 20,4 ms | 434,6 ms | ✅ **0** |
| **après correctif** (20 s) | **coupé** | 611,2 ms | 676,0 ms | 21 — ✅ **0 recalage** |

🔴 **LA LEÇON N'EST PAS « J'AVAIS MIS TROP BAS », C'EST PLUS INSTRUCTIF** : le critère gelé d'AC2
avait mesuré `/metrics` à **16,5 ms de mural p95**, avec un instrument **DÉDIÉ** qui ne faisait que
ça. L'agent, lui, lit LHM **au milieu de cinq sources et de cinq écritures série**.
⇒ **Le p95 d'un instrument dédié ne prédit pas la QUEUE d'un régime chargé.** ⛔ Ce n'est pas un
ajustement de confort : c'est une classe d'erreur de dimensionnement.
⚠️ **Et le budget n'est pas une garantie dure** : 676 ms observés pour 600 posées (**+13 %**) —
granularité du timeout socket plus le test de budget restant. À savoir avant de le resserrer.

## 16.6 AC9 — DEUX CHIFFRES, PUBLIÉS SÉPARÉMENT, ⛔ JAMAIS ADDITIONNÉS EN SILENCE

**Méthode** : cumul `cpu_times()` rapporté au temps mural, ⛔ pas une fenêtre glissante.
**16 cœurs logiques.** Agent sur **`COM3`** (⛔ pas `--stdout`).

| # | quoi | % d'un cœur | % machine |
|---|---|---:|---:|
| **1** | **AGENT SEUL**, 60 s | **2,523** | **0,1577** |
| **2** | 🔴 **LHM SEUL**, 60 s, aucun agent | **7,990** | **0,4994** |
| — | LHM **pendant** l'agent | 7,839 | 0,4899 |

✅ **LA PRÉDICTION D'AC2 TIENT** : elle annonçait **`[2,42 ; 2,66]` % d'un cœur**, la mesure donne
**2,523**. Le delta contre l'agent livré (2,421) est de **+0,102 pt**, contre **+0,24** prédits —
⚠️ **moins cher que prévu**, et il faut le dire dans ce sens-là.
⚠️ **AVEC SA RÉSERVE** : le témoin cumulé **descendait encore** à 60 s (5,141 → 3,586 → 3,167 →
2,810 → 2,686 → **2,523**). ⛔ Comparer un cumul de 60 s non convergé à une base d'une autre durée
n'est pas « à service rendu égal ».

🔴 **LE DELTA ATTRIBUABLE À LA LECTURE 1 Hz EST DE −0,151 pt, C'EST-À-DIRE NÉGATIF.** ⛔ Ça ne veut
pas dire que l'agent rend LHM moins cher : **c'est sous la résolution de la mesure**.
⇒ 🎯 **LA LECTURE DE L'AGENT N'AJOUTE RIEN DE MESURABLE À LHM.** Le coût de LHM est celui de **son
propre échantillonnage**, qui tourne que quelqu'un lise ou non.

🔴 **ET LHM COÛTE TROIS FOIS L'AGENT.** C'est exactement ce que D13 exigeait d'écrire :
> *« Le critère n°4 se mesure sur l'AGENT SEUL — ⛔ LHM n'y entre pas, et il faut l'écrire : la
> charge totale de la tour, elle, AUGMENTE. »*

**Charge totale de la tour : ~10,5 % d'un cœur · ~0,65 % machine.** ⛔ Écrite ici **une fois**, en
toutes lettres, ⛔ et jamais substituée au chiffre n°1.

⛔ **LE CRITÈRE N°4 N'EST TOUJOURS PAS COCHÉ** : son **unité** n'est pas tranchée (AC9 de `dn4-1`
= `PARTIAL`). En **% machine** l'agent tient (0,158 ✅) et même la tour entière (0,65 ✅) ; en
**% d'un cœur** ni l'un (2,52 ❌) ni l'autre (10,5 ❌). ⚠️ Et *« démarre avec la session »* n'est
toujours pas tenu pour l'agent. **Les deux restent au ledger.**

## 16.7 🔴 QUATRE DÉFAUTS D'INSTRUMENT DE CETTE SÉANCE — LES MIENS

1. 🔴 **UN TEST VERT SUR UN TEST QUI N'A JAMAIS EU LIEU.** J'avais mis
   `-ErrorAction SilentlyContinue` sur `Stop-Process` — **la seule action dont dépendait tout
   AC8 scénario 2**. LHM tourne **élevé**, mon PowerShell ne l'est pas ⇒ *« Accès refusé »*,
   **avalé**. Le harnais a conclu *« aucun compteur de rejet n'a monté »* sur une coupure qui
   n'avait pas eu lieu. ⇒ ⛔ **jamais de `SilentlyContinue` sur l'action mesurée**, et **la
   coupure se VÉRIFIE FONCTIONNELLEMENT** (`/metrics` injoignable), ⛔ pas par le retour du kill.
   ✅ Voie correcte trouvée : **`Stop-ScheduledTask`** (marche non élevé) / **`Start-ScheduledTask`**
   (relance **élevé, sans invite UAC** — vérifié par la présence des 31 capteurs `/lpc/…`).
2. 🔴 **UNE ABSENCE FABRIQUÉE PAR LA CAPTURE.** Un relevé a rendu **4 métriques sur 5** (`disk`
   manquait), puis un autre **3 sur 5** (`cpu` et `gpu`). ⛔ **Ce n'était pas le firmware** :
   `dn_link_vue()` ne peut PAS rendre `false` pour une métrique valide (`dn_link.c:539`) — et
   ⛔ **ce n'était pas mon filtre non plus, testé à une variable**. C'est **la capture hôte qui perd
   des lignes**, défaut **déjà mesuré** le 2026-08-20. ⚠️ Fait nouveau : elle perd **les PREMIÈRES**
   lignes du bloc. ⛔ **Le mécanisme n'est pas établi, et je ne le nomme pas.**
   ⇒ **L'instrument COMPTE désormais ce qu'il a capturé et REFUSE de conclure** en dessous de 5,
   puis **relit** (jusqu'à 3 tirs, dans la fenêtre de péremption, le nombre de tirs **publié**).
   🎯 **Et cette garde a mordu au tir suivant** — elle m'a empêché d'écrire « `cpu` absent ».
3. 🔴 **UN MESSAGE DU PRODUIT QUI CONTREDISAIT SON PROPRE COMPTEUR.** Le bilan imprimait *« le
   plafond a probablement COUPÉ une lecture »* **même avec `echecs == 0`** — c'est-à-dire quand les
   données prouvent le contraire. ⛔ Famille *« une cause plausible imprimée par le produit qui
   tourne »*, déjà payée en `dn4-7`. ⇒ corrigé : deux branches, selon `echecs`.
4. ⚠️ **UN REGEX QUI COMPTAIT ZÉRO.** `'hardwareId..=../lpc/'` — `..` fait deux caractères là où
   `"="` en fait trois ⇒ *« capteurs Super I/O : 0 »* sur une tour parfaitement saine. J'ai failli
   en conclure que LHM était remonté **non élevé**. ⇒ ⛔ **ne jamais conclure d'un compteur à zéro
   sans avoir prouvé que l'instrument sait compter autre chose que zéro.**

## 16.8 Ce que la séance n'a PAS mesuré

- ⛔ **AC4 — la qualification W2** : aucune des quatre grandeurs n'a prouvé qu'elle **BOUGE**.
  ⚠️ Les valeurs vues ici sont des **instantanés**, ⛔ pas une session échantillonnée.
- ⛔ **Le mécanisme du « port fermé qui pend »** : hypothèse pare-feu **non testée**.
- ⛔ **Le mécanisme de la perte de lignes à la capture** : non établi.
- ⚠️ **`pertes_seq`** relevées et non expliquées : 1 · 0 · 0 · 0 · 3 · 6 selon les tirs. Sporadiques,
  toujours faibles. ⛔ Aucune n'est un rejet de protocole.


---

# 17. AC4 — LA QUALIFICATION W2 DES QUATRE GRANDEURS LHM (dn4-8, 2026-08-21)

**Critère GELÉ et HORODATÉ le `2026-08-21T18:09:35Z`, committé en `c377d2c`, ⛔ AVANT que
l'instrument n'existe.** Amendé le `18:25:17Z` (`5773e85`), ⛔ **avant le tir** lui aussi.

## 17.1 🔴 LA CADENCE DE LHM EST DE 4,00 s — et elle a démoli mon critère

Le critère gelé exigeait lui-même de la relever (*« ⛔ ne pas la supposer égale à 1 Hz »*) :

| grandeur | changements | médiane | min | max | fréquence |
|---|---:|---:|---:|---:|---:|
| `cpu.degc` | 21 | **4,01 s** | 3,64 | 8,28 | 0,250 Hz |
| `disk.extraction_moy` | 20 | **4,01 s** | 3,86 | 8,03 | 0,249 Hz |
| `disk.cpu_noctua` | 22 | **4,00 s** | 3,86 | 4,20 | 0,250 Hz |
| `disk.case_group` | 22 | **4,00 s** | 3,86 | 4,20 | 0,250 Hz |

*(785 lectures à 10 Hz sur 90 s.)* 🔴 **Constante de la source, ⛔ pas du bruit** : quatre grandeurs
indépendantes, même médiane à **0,01 s** près, et les `max` sont des **multiples** de la période.

⇒ **CONSÉQUENCE ARITHMÉTIQUE** : à **1 Hz** d'échantillonnage, le taux de changement du texte est
**plafonné à 1/4 = 25,0 %**. 🔴 **Or C2 était gelé à 25 % pour la °C — LE PLAFOND LUI-MÊME.**
⛔ **Et mon motif était faux mot pour mot** : *« la résolution est 10× plus fine, le texte change
bien plus souvent »*. **La résolution ne peut pas faire changer le texte plus souvent que la source
ne se rafraîchit.** J'avais raisonné sur la résolution d'affichage **en ignorant la cadence** —
alors que **mon propre §4 me disait de la relever.**
✅ **C2 est devenu RELATIF au plafond mesuré** (≥ **60 % des OCCASIONS**), donc **indépendant de la
cadence d'échantillonnage**. ⛔ **C1 et C3 n'ont pas bougé** : seul C2 était fautif.

## 17.2 🎯 LE VERDICT — LES QUATRE QUALIFIENT

**`n = 960` · 16 min à 1 Hz · 0 lecture en échec · TOUR AU REPOS.**
CSV relu en lecture **stricte** : **7 colonnes vérifiées** sur les 960 lignes.

| grandeur | plage | C1 étendue | C2 (% des occasions) | C3 σ | verdict |
|---|---|---:|---:|---:|---|
| `cpu.degc` | 39,0..44,0 °C | **5,00** ≥ 3,0 | **89,3 %** ≥ 60 | **0,86** ≥ 0,5 | ✅ |
| `disk.extraction_moy` | 952..1034 tr/min | **82** ≥ 5 | **93,0 %** | **12,86** ≥ 1,0 | ✅ |
| `disk.cpu_noctua` | 256..334 tr/min | **78** | **94,7 %** | **12,67** | ✅ |
| `disk.case_group` | 835..890 tr/min | **55** | **92,2 %** | **10,06** | ✅ |

⚠️ **Les quatre changent à 89-95 % des occasions où elles POUVAIENT changer** — c'est-à-dire
quasiment à **chaque rafraîchissement de LHM**. ⛔ Ce ne sont pas des cases molles.

## 17.3 🔴 UNE RÉSERVE ÉCRITE D'AVANCE QUI NE S'EST PAS RÉALISÉE — et la mesure dit pourquoi

J'avais écrit, **avant le tir** : *« `disk.extraction_moy` est une grandeur DÉRIVÉE (moyenne de deux
canaux). Une moyenne LISSE, donc son σ est structurellement plus bas que celui de ses composantes.
Si elle échoue C3 en passant C1 et C2, ce n'est PAS une sonde morte. »*

⛔ **ELLE N'A PAS ÉCHOUÉ, ET LA PRÉMISSE ÉTAIT FAUSSE ICI** :

| | étendue | σ |
|---|---:|---:|
| `TOP_OUT` (`fan/0`) | 114 | **16,94** |
| `REAR_OUT` (`fan/4`) | 55 | **9,07** |
| **moyenne des deux** | 82 | **12,86** |

**σ de la moyenne = 12,86** contre **moyenne des σ = 13,00** ⇒ ⛔ **elle ne lisse pas** (1 % d'écart).

🎯 **ET LA CAUSE EST MESURÉE : `corrélation TOP_OUT ↔ REAR_OUT = 0,955`.** Moyenner ne réduit la
variance que sur des signaux **INDÉPENDANTS** (facteur √2). Ces deux extracteurs sont pilotés par
**la même source thermique** : ils bougent **ensemble**, donc la moyenne **préserve** le signal.
✅ **ET ÇA VALIDE LA DISPOSITION D'AC5 par la mesure, ⛔ pas par le raisonnement** : moyenner ces
deux-là **ne perd rien**, alors que l'alternative (publier deux canaux et abandonner `CASE_GROUP`)
aurait rendu **deux ventilateurs physiques invisibles**.

## 17.4 🔴 UN DÉFAUT D'INSTRUMENT, LE MIEN — une garde fausse D'UN CRAN

`cadence_lhm()` refusait de conclure sous **2** changements. ⇒ avec **exactement 2**, elle calculait
une « médiane » sur **UN SEUL intervalle** et la **publiait**. Vue passer en séance :
*« intervalle median 4,17 s »* sur 2 changements, là où 785 lectures donnaient **4,00 s**.
⛔ **Fausse d'un cran, et dans le sens dangereux : elle rendait un chiffre AU LIEU DE REFUSER.**
⇒ corrigée à **≥ 5 changements** (4 intervalles). ✅ Le verdict a été **re-jugé avec la cadence
robuste** (`--rejuger --periode-lhm 4.00`) : les pourcentages passent de 92-99 % à **89-95 %**, et
⛔ **aucun verdict ne change** — mais **le chiffre publié repose désormais sur la mesure solide.**

## 17.5 ⛔ CE QUE CE TIR NE PROUVE PAS

- 🔴 **LA PHASE DE CHARGE N'EST PAS COUVERTE.** Décision owner : *« au repos oui on fera les autres
  étalonnages plus tard que ça ne soit pas bloquant »*.
  ⚠️ **L'asymétrie est ce qui rend ce tir acceptable** : une **qualification** au repos reste
  **VALIDE** (ce qui bouge assez au repos bouge *a fortiori* sous charge) ; une **non-qualification**
  aurait été **NON CONCLUANTE**. ⇒ **les quatre ayant qualifié, la réserve ne mord sur rien.**
  ⛔ **L'étalonnage sous charge reste DÛ** — au ledger.
- ⛔ **Le choix de la sonde de °C n'est pas rouvert** : `CPU Package` qualifie. `Core Max` existe et
  dit autre chose ; le tester serait **un tir NEUF**, avec son critère à geler.
- ⛔ **`FRONT_IN` n'est pas dans ce tableau, et il n'y sera jamais** : pas de fil tachymétrique.

---

# 18. 🔴 SÉANCE CARTE DU 2026-08-21 (soir) — APRÈS LA REVUE DE CODE : le témoin v3 est TIRÉ, AC7 et AC8 sont RE-MESURÉS

⚠️ **Pourquoi cette séance existe, et c'est une règle de méthode, ⛔ pas un caprice.**
La revue de code du 2026-08-21 a modifié **onze instruments**. Le skill de séance carte l'impose :
*« quand une revue a changé un INSTRUMENT, les chiffres publiés sont MORTS — les re-relever EN
PREMIER »*. AC7 et AC8 reposaient sur `campagne_bruit_dn48.py` et `regime_reel_dn48.py`, tous deux
corrigés. ⇒ leurs verdicts de §16 sont **remplacés par ceux-ci**.

## 18.0 Le firmware sous test — LU, ⛔ pas supposé

| Fait | Valeur | D'où |
|---|---|---|
| `App version` | **`4c3a3f7`** | bandeau de boot, `dn_console.py --reset` |
| `SPI Flash Size` | `16MB` | bootloader, avant `app_main` |
| `cfg` (NVS = ACTIVE) | `num_fbs=1 bounce_px=7680 draw_lines=128 draw_psram=0 lvgl_core=0` | `cfg`, relevé avant campagne |

~~🎯 **ET C'EST BIEN LE FIRMWARE DE `HEAD`**~~ — 🔴 **AMENDÉ LE 2026-08-24 (2ᵉ revue de code),
⛔ PAS EFFACÉ. LA CONCLUSION ÉTAIT FAUSSE AU MOMENT OÙ ELLE A ÉTÉ ÉCRITE.**
`git diff 4c3a3f7..8f4cebc -- firmware/` est bien **VIDE** (re-vérifié) — mais `8f4cebc` est la base
**D'AVANT** la revue, ⛔ pas `HEAD`. À l'heure de cette séance, le commit `75f8afc` (« D3 — la garde
refusait des lignes NON PEUPLÉES », **+85 lignes dans `dn_ui.c`**) était **déjà dans l'intervalle** :
l'arbre différait donc du firmware que la carte portait.
✅ **CE QUI TIENT, ET C'EST ÉCRIT DEUX LIGNES PLUS BAS** : les trois tirs exercent `dn_link.c` et
`dn_console.c`, qu'aucun patch de revue ne touche. **Le raisonnement était bon ; c'est la phrase de
conclusion qui était fausse** — et c'est elle qu'un lecteur reprend.
⛔ **Aucun flash n'a eu lieu**, et il n'en fallait pas : les trois tirs exercent `dn_link.c` (parse
+ compteurs) et `dn_console.c` (`pc`), qu'aucun patch de revue ne touche. Le seul patch firmware de
la revue est la garde `dn_ui.c` (`widget grandeurs`), **qui reste À VALIDER SUR CARTE** — elle
demande un flash, donc un arbre propre, donc les commits.

## 18.1 🎯 AC5 — LE TÉMOIN v3 EST TIRÉ. Il n'avait JAMAIS été exercé.

AC5 exigeait que le témoin v3 soit *« soit **re-qualifié**, soit retiré explicitement … ⛔ jamais
laissé vert par inadvertance sur une sémantique qui a changé »*. La campagne ne portait qu'un
témoin **v1**, et la story écrivait elle-même, à deux endroits, *« re-qualifié PAR CONSTRUCTION,
⛔ pas encore par la mesure »*. La séance carte du matin ne l'a pas ajouté, et **AC5 comme AC7 ont
été marqués SOLDÉS**. La revue l'a relevé ; l'owner a rouvert AC5 ; le voici mesuré.

**Ce qu'il prouve** : un agent v3 **NON MODIFIÉ** (ère `dn4-6`) émet `cpu` à TROIS valeurs et
`disk` à UNE. Contre le firmware `dn4-8`, sa dernière valeur ne doit **pas glisser** dans la case
qu'elle ne connaît pas.

| Témoin | Trame injectée | `pc` LU sur la carte | Compteurs |
|---|---|---|---|
| **v3 `cpu` à TROIS** | `$DN,3,1012,10120,cpu,520,32,880*45` | `52,0 %` · `3,2 GHz` · **`88,0 %`** · `-- (degC ATTENDUE…)` | **0 delta** |
| **v3 `disk` à UNE** | `$DN,3,1013,10130,disk,7085*3A` | `708,5 Mo/s` · `--` · `--` · `--` | **0 delta** |

🔴 **LE `c.max` EST EN INDEX 2, ET LA CASE °C DIT `--`.** C'est exactement ce que la **4ᵉ voie** a
acheté : avec l'ordre naïf (`°C` en index 2), le `88,0` d'un agent v3 non modifié serait tombé
**dans la case température**, affiché `88,0 degC`, et **aucun compteur n'aurait bronché**.
✅ **AC5 est re-qualifié PAR LA MESURE**, ⛔ plus par construction.

⚠️ **Le témoin discrimine — vérifié par témoin positif avant le tir.** Le contrôle porte sur la
**position ET l'unité** : l'ordre naïf (`88,0 degC` en position 2) est **REFUSÉ**, un décalage d'un
cran est **REFUSÉ**, une ligne illisible est **REFUSÉE**. ⛔ Une première rédaction ne comparait que
le **nombre** (`"88,0"`) : elle aurait épinglé VERT l'échange d'unité, c'est-à-dire exactement la
garde décorative que la revue venait de retirer d'ailleurs.

## 18.2 AC7 — la campagne repasse à **ONZE** cas, et la bande est ASSERTÉE

`campagne_bruit_dn48.py` corrigé : **exit 0**, chaque cas dans **son** compteur et **lui seul**.

| Ce qui a changé depuis §16.2 | Pourquoi |
|---|---|
| **+1 cas** : « champ VIDE en position **INTERNE** » | C'était une **ligne du tableau d'AC7** que la campagne ne testait pas — fermée seulement par une lecture humaine d'un dump. Elle a une forme de verdict **différente** (aucun compteur ne bouge **et** la suivante n'est pas décalée), que `ok = bouges == {attendu: 1}` ne pouvait pas exprimer. **Résultat : `480,0 Mo/s` · `--` · `800,0 tr/min` · `1400,0 tr/min`, 0 delta.** |
| **bande 72..124 ASSERTÉE** | Elle était calculée **après** le tir et n'entrait jamais dans le verdict, alors que l'en-tête promettait « vérifiée AVANT le tir ». **Mesure : 78 o, dans la bande.** |
| **anti-collision checksum** | Le faux CK était forcé à `"00"` : quand le CK réel vaut `00`, la trame est **valide** et le cas échouait à tort. Le jumeau `dn_injecteur.py` gardait déjà cette collision. |

## 18.3 AC8 — le régime réel RE-TIRÉ, et cette fois l'instrument GATE

`regime_reel_dn48.py` corrigé : il lit `pr.returncode`, borne le `subprocess`, **publie la durée
murale** et **arrête** sur un relevé périmé. Le tir précédent n'était gaté par **rien** : un agent
mort au démarrage aurait imprimé le même `✅`.

| Contrôle | Relevé |
|---|---|
| durée murale de l'agent | **20,9 s** pour 20 s demandées (⇒ l'agent a bien vécu) |
| `pc` relu après l'arrêt | **0,63 s** — **FRAIS** (péremption 3,00 s) |
| capture | **COMPLÈTE, 5/5 métriques** |
| **delta des six compteurs de rejet** | 🎯 **TOUS À ZÉRO** |
| trames émises | 100 en 20,0 s (**4,99 trames/s**), 0 erreur d'envoi, **0 recalage de cadence** |
| bruit console | 4 882 o / 103 lignes en 20,0 s = **243,7 o/s · 5,14 lignes/s** |
| latence acceptation→label | n=102 · min 13 ms · **moy 192 ms** · max 276 ms |

**Ce que `pc` montrait, avec des valeurs RÉELLES :**

```
cpu  -> 43,1 % · 3,2 GHz · 71,2 % · 41,8 degC
disk -> 12,3 Mo/s · 971,0 tr/min · 273,9 tr/min · 845,0 tr/min
```

## 18.4 🎯 CE QUE CETTE SÉANCE VALIDE DES PATCHES DE REVUE, SUR LE MATÉRIEL RÉEL

- **Vérification de famille `/metrics`** (le contrôle qui manquait, et qui justifiait d'avoir
  éliminé `/data.json`) : **aucune ligne « famille inattendue », aucune ligne illisible**. Les
  familles réelles de LHM 0.9.6 sur cette tour sont bien `lhm_cpu_temperature_celsius` et
  `lhm_motherboard_fan_rpm`. ⛔ Testé contre le **vrai service**, plus seulement contre la fixture.
- **Durée LHM incluant le parse** (`_chrono` déplacé) : **moyenne 24,1 ms, MAX 181,9 ms** pour un
  timeout posé à **600 ms**, **0 échec**. ⚠️ ⛔ **NE PAS COMPARER** aux 26,7 / 454,7 ms de §16.5 :
  ce n'est ni la même session ni le même instrument — celui-ci mesure **en plus** le parse.
- **`dn_lhm_tour.ps1` durci** : le verdict exige désormais `/metrics` **et** zéro anomalie, et les
  deux passent — `GET /metrics : HTTP 200 | 76 901 o | 38 ms` contre `/data.json` **495 ms**.
- **Seau `non_publiees`** (grandeurs LHM lues mais non publiées) : **jamais déclenché**, la source
  disque n'a pas failli de la session.

## 18.5 🔴 UN DÉFAUT D'INSTRUMENT DE CETTE SÉANCE — LE MIEN, ET IL A ACCUSÉ UNE CARTE SAINE

**Premier tir : TROIS cas déclarés EN ÉCHEC. La carte affichait EXACTEMENT l'attendu.**

Le découpage de la ligne `pc` faisait `ligne.split("->")[-1].split("·")`, en supposant que les
grandeurs suivent la flèche. **Elles ne la suivent pas** : le format réel est
`"  %-5s -> case %d %-9s %-12s"` (`dn_console.c:2664`), donc `case 0 CPU  VIVANTE` s'intercale —
et une **queue `· age … · seq …`** ferme la ligne sans être une grandeur.

⛔ **Un instrument faux accuse le sujet sain.** C'est la même famille que les défauts que la revue
venait de retirer, commise en écrivant le correctif.
⇒ Le découpage est maintenant **un miroir explicite du format C**, il **jette** la queue de
diagnostic, il **valide** que la première case ressemble à une grandeur, et il rend **`None`**
plutôt qu'un découpage douteux — un échec de parsing se dit **comme un échec d'instrument**,
⛔ jamais comme un échec de la carte. Éprouvé sur les **quatre** formes réelles, `jamais recue`
comprise.

## 18.6 ⛔ CE QUE CETTE SÉANCE NE PROUVE PAS

- ⛔ **AC2 et AC4 restent MORTS.** `mesure_lhm_dn48.py` (biais `_cpu_ms`, `murs` filtré) et
  `mesure_w2_dn48.py` (**`affichee()` : arrondi banquier → demi-haut**) ont été corrigés et **n'ont
  pas été re-tirés**. ⚠️ Et `--rejuger` ne sauvera pas AC4 : le CSV stocke des valeurs **déjà
  quantifiées par l'ancienne règle**. ⇒ **un tir NEUF de 16 min sur la tour est DÛ.**
- ⛔ **La garde `dn_ui.c` (`widget grandeurs disk 4` doit être REFUSÉE) n'est PAS validée sur
  carte** : elle exige un flash, donc un arbre propre, donc les commits.
- ⛔ **Aucune observation à l'œil** n'a été demandée : les trois tirs sont intégralement
  instrumentés par compteurs et par `pc`. ⚠️ Le constat *« le fil porte 4, la dalle montre 3 et 1 »*
  reste celui de §16, ⛔ il n'a pas été refait.
- ⛔ **La permanence de LHM n'est pas re-prouvée** : elle se prouve en **redémarrant la tour**.

---

# 19. 🎯 AC4 RE-TIRÉ APRÈS LA REVUE — LES QUATRE QUALIFIENT, ET CETTE FOIS C'EST DÉFENDABLE

⚠️ **Ce tir REMPLACE celui de §17.** Pas parce que l'ancien avait tort sur le fond, mais parce
que son instrument a changé : `affichee()` est passée de l'arrondi **banquier** au **demi-haut**
pour appeler la quantification réelle du produit. La grille native du capteur Intel étant de
**0,25 °C**, un échantillon sur deux tombait sur une égalité — et C2 est un taux de changement de
**TEXTE**, la statistique la plus sensible qui soit à ces égalités.
⛔ **Et `--rejuger` ne pouvait pas sauver §17** : `affichee()` s'applique à l'échantillonnage, donc
le CSV portait des valeurs **déjà quantifiées par l'ancienne règle**.

## 19.1 Le verdict

| Grandeur | C1 étendue | **C2 % des occasions** | C3 σ | Verdict |
|---|---|---|---|---|
| `cpu.degc` | 4,00 ≥ 3,0 | **90,6 %** (238 occ., 216 chgt) | 0,82 ≥ 0,5 | ✅ **QUALIFIE** |
| `disk.extraction_moy` | 54,0 ≥ 5,0 | **93,1 %** (238 occ., 222 chgt) | 9,50 ≥ 1,0 | ✅ **QUALIFIE** |
| `disk.cpu_noctua` | 60,0 ≥ 5,0 | **96,0 %** (238 occ., 229 chgt) | 11,84 ≥ 1,0 | ✅ **QUALIFIE** |
| `disk.case_group` | 41,0 ≥ 5,0 | **87,2 %** (238 occ., 208 chgt) | 6,29 ≥ 1,0 | ✅ **QUALIFIE** |

Plancher C2 = **60,0 % des OCCASIONS** (amendement owner daté du 2026-08-21, `5773e85`).

**Écart avec §17 — il n'est pas nul, et c'est l'information :**

| | `cpu.degc` | `extraction_moy` | `cpu_noctua` | `case_group` |
|---|---|---|---|---|
| §17 (ancien arrondi) | 89,3 | 93,0 | 94,7 | 92,2 |
| **§19 (arrondi du produit)** | **90,6** | **93,1** | **96,0** | **87,2** |
| Δ | +1,3 | +0,1 | +1,3 | **−5,0** |

🔴 **`case_group` bouge de 5 points.** Le changement d'arrondi n'était donc **pas cosmétique** —
mais on reste très loin du plancher, dans les deux sens. ⚠️ **Ces deux séries ne sont pas
strictement comparables** (sessions différentes, machine dans un autre état) : le Δ mesure
l'arrondi **et** la session. ⛔ Ne pas l'attribuer entièrement à l'un ou à l'autre.

## 19.2 Ce qui rend CE tir défendable, et que §17 n'avait pas

| Propriété | §17 | **§19** |
|---|---|---|
| Cadence LHM | **tapée à la main** (`--rejuger --periode-lhm 4.00`) : `cadence_lhm()` rendait `None` à tous les coups, sa fenêtre de 12 s ne pouvant pas voir les 5 changements exigés à 4,00 s | 🎯 **MESURÉE par le tir qui juge** : **4,01 s** sur **4/4 sondes** (médiane des médianes, fenêtre 40 s) |
| Espacement des échantillons | `periode_ech = 1.0` **codé en dur**, la colonne `t_s` jamais relue | 🎯 **MESURÉ dans `t_s` : 1,000 s** |
| Dérive de cadence | aucun rattrapage : une lecture qui déborde enchaînait les itérations dos à dos **en silence** | **1 recalage COMPTÉ et PUBLIÉ** (retard 3,17 s) — ⚠️ le défaut s'est **réellement produit** |
| Quantification | `round()` **banquier**, réimplémenté | 🎯 `dn_agent._dx` + l'arrondi firmware, **appelés** |
| Seuils au bandeau | annonçait `C2>=25 %` / `C2>=10 %` — des seuils **périmés** | LIT les constantes : `C2 >= 60,0 % des OCCASIONS` |
| σ par canal / corrélation | publiés en §17.3, produits par **aucun instrument commité** | 🎯 produits par `analyser()`, **les SIX canaux** |

## 19.3 σ sur les SIX canaux, et les corrélations

```
cpu.degc            σ  0,819 | étendue  4,00  (38,00..42,00)
disk.extraction_moy σ  9,503 | étendue 54,00  (927,00..981,00)
disk.cpu_noctua     σ 11,841 | étendue 60,00  (226,00..286,00)
disk.case_group     σ  6,286 | étendue 41,00  (816,00..857,00)
fan.top_out         σ 14,226 | étendue 77,00  (603,00..680,00)   ← absent de §17.3
fan.rear_out        σ  5,162 | étendue 32,00  (1250,00..1282,00) ← absent de §17.3

extraction_moy ~ fan.top_out      r = 0,992
extraction_moy ~ fan.rear_out     r = 0,943
extraction_moy ~ cpu.degc         r = 0,449
extraction_moy ~ disk.cpu_noctua  r = 0,974
```

⚠️ **Un `r` élevé entre `extraction_moy` et SES PROPRES canaux est ATTENDU — c'est leur moyenne.**
⛔ Ce n'est pas une découverte, c'est un **contrôle de cohérence de l'instrument**, et il passe.
⚠️ §17.3 citait `r = 0,955` : autre session, autre nombre, même forme. ⛔ Ne pas les confronter.

## 19.4 ⛔ CE QUE CE TIR NE PROUVE PAS

- ⛔ **TIR AU REPOS**, décision owner, comme §17. **La phase de CHARGE n'est pas couverte.**
  L'asymétrie est ce qui le rend acceptable : une **qualification** au repos reste **valide** (ce
  qui bouge assez au repos bouge a fortiori sous charge) ; c'est une **non**-qualification qui
  aurait été non concluante. ⇒ **l'étalonnage sous charge reste DÛ, au ledger.**
- ⛔ **AC2 reste MORT** : `mesure_lhm_dn48.py` a été corrigé (biais `_cpu_ms`, `murs` filtré) et
  **n'a pas été re-tiré**. La *décision* keep-alive survivra très probablement ; **les nombres,
  non**.
- ✅ **Le CSV et le log sont ARCHIVÉS** — `mesures/dn4-8/`, avec leur provenance. C'est la leçon
  directe de ce re-tir : celui de §17 n'était nulle part. ⚠️ Et sa provenance dit aussi ce qu'un
  CSV **ne** sauve pas.

---

# 20. `dn4-9` (P9.3d) — CE QUE L'ÉCRAN EN MONTRE

**Story** : `dn4-9-cpu-prend-la-temperature-disque-prend-les-ventilos`.
**Périmètre : AFFICHAGE PUR.** ⛔ **Aucune ligne d'agent, aucune de `dn_link`, aucune du
protocole `$DN`.** Le fil est **servi** depuis `dn4-8` : `cpu = [% · GHz · c.max · °C]` et
`disk = [Mo/s · extraction_moy · CPU_NOCTUA · CASE_GROUP]`.
✅ **La preuve que le fil n'a pas bougé est `tools/recompte_trame_dn48.py`, qui reste VERT SANS
AVOIR ÉTÉ MODIFIÉ** (exit 0, `agent/dn_agent.py sha256:95a4481904e2a530`).

## 20.1 🔴 LE MAPPING BIOS ↔ LHM ↔ RPM — REMONTÉ ICI, IL N'EXISTAIT QUE DANS LA STORY

⚠️ **C'est la SOURCE ÉCRITE des trois libellés de `DISQUE`.** Il vivait dans le fichier de story
de `dn4-8` et nulle part ailleurs : un mapping qu'on ne retrouve que dans un artefact de sprint est
un mapping qu'on re-déduira faux.

**Quatre captures owner du 2026-08-21.** Le BIOS **nomme** les en-têtes **et** affiche leur RPM :
le RPM est la **clé de jointure** avec les `fan/N` de LHM.

| BIOS | RPM BIOS | LHM | RPM Windows | nom retenu | nommable à l'écran ? |
|---|---|---|---|---|---|
| `CPU 1` | ~305 | **`fan/1`** | 364 | **`CPU_NOCTUA`** | ✅ **oui, sans réserve** — libellé `ventirad` |
| `CPU 2` | ~700 | **`fan/0`** | 784 | **`TOP_OUT`** | 🔴 **FONDU** dans `extraction_moy` ⇒ ⛔ pas seul |
| `System 1` | 877 | **`fan/2`** | 930 | **`CASE_GROUP`** | ⚠️ **avec réserve** — libellé `boitier`, ⛔ jamais « TOP »/« BOTTOM » |
| `System 2` | **0** | `fan/3` ou `fan/5` | **0** | **`FRONT_IN`** | ⛔ **JAMAIS, PAR AUCUN LOGICIEL** (L7, CLOS) |
| `System 3` | 1305 | **`fan/4`** | 1358 | **`REAR_OUT`** | 🔴 **FONDU** ⇒ ⛔ pas seul |

✅ **Jointure SANS AMBIGUÏTÉ** : quatre valeurs strictement croissantes de chaque côté, aucune
paire proche (la plus serrée est à 1,25×).
🔴 **L'ORDRE NAÏF ÉTAIT FAUX SUR LES DEUX PREMIERS** : `fan/0` est **`CPU_FAN2`**, ⛔ pas
`CPU_FAN1`. Le coder naïvement aurait affiché **« CPU » sur l'extraction haute**. C'est **la
capture BIOS de l'owner** qui l'a attrapé, ⛔ pas le raisonnement.

## 20.2 Ce que la story change — les DEUX comptes et la sélection d'indices

🔴 **LE MÉCANISME QUI MANQUAIT** : jusqu'à `dn4-9`, une case n'avait **qu'un nombre**
(`n_grandeurs`) et l'affichage lisait les grandeurs `0..n-1` **dans l'ordre** — il n'y avait
**aucune sélection**. Or D13 demande `[%, GHz, °C]` pour `CPU`, c'est-à-dire les grandeurs
**0, 1 et 3**, et la place n'en autorise que **trois** (`48 + 3×40 + 35 = 203 > 163`, mesuré).

| case | CASE dessine | DÉTAIL montre | changement |
|---|---|---|---|
| **CPU** | **3** — `[0, 1, 3]` = `%` · `GHz` · **`°C`** | **4** — `[0, 1, 2, 3]` | 🔴 `c.max` **descend au détail**, ⛔ n'est pas supprimé |
| **GPU** | 3 — `[0, 1, 2]` | **4** — `[0, 1, 2, 3]` | ✅ le `tr/min` du GPU devient **visible pour la première fois depuis `dn4-6`** |
| **RAM** | 1 — `[0]` | 1 | inchangée. ⚠️ **⛔ NE PAS lui donner sa grandeur 1 au détail** : elle part déjà en ligne secondaire, elle s'y afficherait DEUX FOIS |
| **RÉSEAU** | 2 — `[0, 1]` | 2 | inchangée |
| **DISQUE** | **2** — `[0, 1]` = `Mo/s` · **`extr.moy tr/min`** | **4** — `[0, 1, 2, 3]` | 🔴 de UNE à DEUX ; les trois **préfixes** posés |
| **AMBIANCE** | 2 — `[0, 1]` | 2 | inchangée |

**La forme retenue** : `sel_p1[]` (index **décalé de 1**, `0` = non déclaré ⇒ **identité**) +
`n_detail` (`0` = « comme la case »). ⚠️ **Le décalage est la convention du dépôt**
(`DN_VAL_ABSENTE`, `DN_PREC_NON_RENSEIGNEE`, `k_pc[].idx_p1`) : un descripteur qui ne déclare rien
naît **ignorant**, et l'ignorance se lit « identité », c'est-à-dire le comportement d'avant
`dn4-9` à l'octet près pour les CINQ cases sans sélection.
⛔ **Il n'y a PAS de `sel_detail_p1[]`** : le détail montre `0..n_detail-1` **dans l'ordre du fil**
— il n'a aucune raison de réordonner ce que la source publie, et un champ que personne n'utilise
est un champ mort.

## 20.3 🔴 LES TROIS VERROUS ÉTAIENT **EN SÉRIE** — en lever un seul ne donnait rien

| # | Où | Ce qu'il faisait | Levé par |
|---|---|---|---|
| 1 | `detail_reparametrer()` | lisait `desc_n(idx)`, le compte de la **CASE** | `desc_n_detail(idx)` |
| **2** | 🔴 **`dn_ui_pc_maj()`** | **bornait le FORMATAGE** par le compte de la case ⇒ **`s_wetat[CPU].txt[3]` n'était JAMAIS ÉCRIT** | borne = `desc_peuplees(idx)` |
| 3 | `desc_n()` | **un seul** nombre par case | `case_grandeurs()` + `desc_n_detail()` |

🎯 **LE N°2 EST CELUI QU'ON RATE.** Lever les n°1 et n°3 seuls aurait donné un détail affichant
**`--` gris** à la place de la °C : **un défaut MUET à la place d'un défaut VISIBLE**, et le dev
aurait conclu que le mécanisme marche.

⚠️ **Et un QUATRIÈME point, qui n'était dans aucun artefact** : `build_dashboard()` passait à
`dn_widget` une **copie** du descripteur pendant que `case_poser()` passait `&k_desc[idx]`, le
descripteur **brut**. Tant que le rang valait l'index, les deux composaient la même chose. Avec une
sélection, la case aurait affiché `[%, GHz, °C]` à la construction puis `[%, GHz, c.max]` **dès la
première mise à jour** — ~~5 fois par seconde~~, **sans un log**, parce que le garde-fou de
`dn_widget_maj()` est le **POINTEUR** `valeur[i]` et pas le compte.

> 🔴 **CHIFFRE ANNOTÉ LE 2026-08-24 (`dn4-4` / AC3, 2ᵉ passe — revue de code), SUR MESURE,
> ⛔ PAS EFFACÉ** : la cadence de poussée a été mesurée (100 trames acceptées ⇒ 100 poussées
> en 20,5 s) = **5,0 poussées/s TOUTES MÉTRIQUES CONFONDUES**, donc **1,0/s PAR MÉTRIQUE**.
> Le « 5 fois par seconde » ci-dessus vaut donc pour le chemin `case_poser()` **vu de tout
> le tableau de bord** ; pour **UNE** case, **c'est ~1 Hz**. ⚠️ Le premier balayage d'AC3
> n'avait couvert que `firmware/` — ce site vivait dans `hardware/`, que le `grep` de l'AC
> nomme pourtant explicitement. [Source : `liaison-pc.md` §21.6] ⇒ **`desc_effectif()`** : une
seule fabrique, les deux chemins la prennent.

## 20.4 Les gardes — elles jugent **l'UNION**, ⛔ plus « les `n` premières »

*Ce qui est affiché quelque part est jugé.* Le cas est **réel** : la case `CPU` = `[0, 1, 3]` ne
contient **plus** le couple `%`/`%`, alors que le détail `[0, 1, 2, 3]` le contient.

- **Invariant A** (audité au boot) : `sel_case ⊆ [0, n_detail)` ⇒ *la case montre un
  sous-ensemble de ce que le détail montre*. C'est lui qui rend **l'union égale à la plage du
  détail**, et donc les gardes exactes sans jamais fusionner deux listes.
- **Invariant B** : les indices d'une case sont deux à deux **distincts**.
- **Invariant C** : `sel_p1` est déclarée **entièrement ou pas du tout**.
- `desc_ligne_indistincte()` juge `0..n_detail-1` — ⛔ plus le compte de la case.
- `desc_peuplees()` **n'est plus la garde** : elle rend « la dernière peuplée **+ 1** », donc
  comparer un COMPTE laissait passer une sélection **contenant un trou**. ⇒ `desc_indice_vide()`
  juge **chaque indice**.
- `dn_ui_set_case_grandeurs()` refuse aussi `n > n_detail` : la case dessinerait une grandeur que
  la page censée l'**expliquer** ne montre pas.

🔴 **ET L'AUDIT DE BOOT CESSE DE MENTIR.** Il annonçait *« `widget grandeurs 4 4` est jouable »*
pour `DISQUE` alors que la garde de `dn4-8` la **REFUSAIT** (trois `tr/min` sans préfixe). ⚠️ Ce
n'était pas une faute de `dn4-8` : la garde et l'audit ont été écrits à **deux moments
différents**. C'était un défaut **LIVRÉ**. La ligne publie désormais les deux comptes, les deux
listes, et **interroge les mêmes gardes** que le setter — ⛔ pas une copie de leur raisonnement.

## 20.5 🔴 DEUX DÉFAUTS D'INSTRUMENT TROUVÉS AU CADRAGE — ⛔ pas à l'exécution

1. **`widget detail` était PLUS PETIT que ce qu'il devait relire** : `128 o`
   (`DN_WIDGET_TXT_MAX * 4 + 64`) contre **168 o** produits
   (`4 * (DN_WIDGET_TXT_MAX + 24) + 8`), et `dn_ui_detail_label()` faisait
   `snprintf(txt, txt_n, "%s", src)` **sans tester le retour**. À quatre grandeurs **avec
   préfixes**, le pire cas dépasse : **le seul instrument capable de prouver qu'une ligne tient
   aurait tronqué le texte qu'il prétend relire**, pendant que le produit, lui, va bien.
   🎯 *« Un instrument faux accuse le sujet sain. »*
   ⇒ **UNE constante** (`DN_UI_DETAIL_TXT_MAX`, `dn_ui.h`), les deux côtés la prennent, et la
   troncature rend **`false`** avec un `ESP_LOGE` qui nomme les deux tailles.
2. **`s_gr_force[]` avait CINQ lecteurs pour QUATRE annoncés** — `pousser_nolock()`, ajouté par la
   revue du 2026-08-19 **dans le geste même** où l'énumération était présentée comme « faisant
   partie de la garde ». C'est mot pour mot la dérive payée sur `s_nue_force[]`
   (*« 1/6, 2/5, 3/5, 4/6, 5/5 : cinq numérotations pour une liste »*).
   ⇒ `dn4-9` **ne renumérote pas, elle supprime le besoin de numéroter** : `s_gr_force[]` n'a plus
   qu'**UN lecteur** (`case_grandeurs()`) et **UN écrivain** (`dn_ui_set_case_grandeurs()`), et
   c'est un `grep -n s_gr_force dn_ui.c` qui le dit — **TROIS lignes de code**, ⛔ pas un compte
   tenu à la main.

## 20.6 La gate WSL — `tools/verif_selection_dn49.py`

**Jouable sans carte, sans tour, sans LHM.** Elle fait ce que **ni le firmware ni l'œil** ne
peuvent faire :

- **M1 — LE MIROIR ÉCRAN ↔ FIL.** Le firmware n'a **aucun** accès à ce que l'agent publie : il ne
  peut pas savoir qu'une case SÉLECTIONNE une grandeur que `k_metriques[]` ne porte pas. Cette
  grandeur s'afficherait « -- » gris **À VIE**, et rien ne le dirait.
- **M2 — LE MIROIR DES TAMPONS.** Producteur et instrument prennent-ils la même taille ? C'est une
  propriété de **SOURCE** ; à l'exécution, le second tronque simplement en silence.
- **M3 — LE PRÉ-VOL** des invariants A/B/C, de l'union distincte et des indices peuplés.
  ⚠️ **DOUBLON ASSUMÉ** de `selections_auditer()` : deux lectures **indépendantes** de la même
  table, l'une en Python sur le source, l'autre en C sur la structure compilée. ⛔ **Elle ne le
  remplace pas** — il lit l'ÉTAT à l'exécution, elle lit la TABLE.

⛔ **Elle ne calcule AUCUNE largeur.** Une largeur dépend des **glyphes** et du crénage, ⛔ pas
d'un nombre de caractères. Elle **ÉMET** les commandes `widget largeur` à jouer sur la carte,
construites depuis les descripteurs **et les plafonds RÉELS de `k_metriques[]`** — pour que la
liste des lignes à mesurer ne puisse pas diverger de ce que le firmware dessine.
⚠️ **Elle a attrapé son propre défaut au premier tir** : `k_desc[]` initialise par **champs
désignés** et `k_metriques[]` **positionnellement**. Un parseur unique lisait **zéro** grandeur sur
le fil et concluait que TOUTES les cases affichent du vide.

## 20.7 ⛔ CE QUE CE FICHIER NE PROUVE PAS ENCORE

- ⛔ **AUCUNE LARGEUR N'EST MESURÉE.** Elles exigent la carte (`widget largeur`, `widget detail`).
  ⚠️ **Réserve écrite d'avance** : la ligne 1 du détail `DISQUE`
  (`100000,0 Mo/s   ·   extr.moy 10000 tr/min`) devient **le pire cas de tout l'écran**, et il
  n'est budgété **nulle part**. Les pires cas publiés culminent à **265 px** — sans préfixe et sans
  un `Mo/s` à six chiffres. **Repli PRÉ-AUTORISÉ : raccourcir le libellé**, en gardant les
  interdits de nommage.
- ⛔ **AUCUN CONSTAT OWNER.** Les constats sensoriels sont l'**OWNER**, jamais l'agent.
- ⛔ **AUCUNE MESURE DE COÛT** (`mem`, `cpu brut`, `fps`, `nav ab`) : elles exigent la carte.
- ⛔ **La garde `dn_ui.c` de `dn4-8` n'est TOUJOURS pas validée sur la carte** — elle exige un
  flash.

## 20.8 Entrées au ledger portées par `dn4-9` — ⛔ par AJOUT

| # | Entrée | État | Condition de réouverture / de clôture |
|---|---|---|---|
| L10 | 🆕 **L'échelle haute de `DISQUE` (`Mo/s → Go/s`) est PRÊTE mais NON ARMÉE** | 🟠 ouvert, **legs explicite** | Mécanisme livré en `dn4-6` ; *« l'owner a nommé RÉSEAU »*. ⚠️ **Le chiffre qui la rendra nécessaire** : `« 100000,0 Mo/s »` a la même forme que le `« ↓ 99999,9 Mb/s »` **mesuré à 202 px pour 201 utiles** |
| L11 | 🆕 **`s_trop_larges` ne mesure QU'À LA CONSTRUCTION** | 🟠 **limite CONNUE** | Une valeur qui devient trop large **entre deux reconstructions** n'est vue par personne. ⛔ Hors périmètre `dn4-9`. Forcer le pire cas par `dn_injecteur.py --jeu pire`, qui reconstruit avec les plafonds |
| L12 | 🆕 **L'`_Static_assert` manquant entre `DN_LINK_GRANDEURS_MAX` et `DN_WIDGET_GRANDEURS_MAX`** | 🟠 ouvert | Les deux valent 4, le découplage est **documenté et voulu**, mais `cpu` et `disk` sont **EXACTEMENT au plafond des deux côtés**. ⇒ **soit l'assertion, soit le motif écrit**. Le dépôt utilise `_Static_assert` ailleurs (`dn_env.c:29`) |
| L13 | 🆕 **`brut[1..3]` n'est JAMAIS alimenté, et la jauge lit `brut[0]`** | 🟠 **nommé dans le code** | `brut[0]` = **grandeur 0 DU DESCRIPTEUR**, ⛔ pas « la première ligne affichée ». ⚠️ Aucune case livrée ne montrerait le défaut : `RAM` est la seule à `indicateur = true`, mono-grandeur, sélection identité — **exactement la configuration qui l'a laissé passer deux fois**. Rouvrir le jour où une case **à jauge** reçoit une sélection |
| L14 | 🆕 **Le résiduel *« `pc` ne peut plus nommer QUEL ventilateur est muet »*** | ✅ **SOLDÉ le 2026-08-22** | Par `dn_ui_case_prefixe()`, consommé par `cmd_pc`. ⛔ **JAMAIS** en modifiant `k_metriques[].unite`, qui casserait les témoins v1 et v3 |
| L15 | 🆕 **`widget grandeurs <c> <n>` sur une case À SÉLECTION ne reproduit PAS la case livrée** | 🟠 **comportement ÉCRIT, à connaître devant la carte** | Sur `CPU`, `widget grandeurs 0 3` montre `[%, GHz, c.max]`, ⛔ pas `[%, GHz, °C]` : l'override force **l'identité** (les `n` premières du DÉTAIL). C'est `widget grandeurs 0 0` qui rend la case à son descripteur. ⚠️ **Le compte du DÉTAIL n'a aucun override** : si l'arbitrage en demande un, c'est une sous-commande **à écrire et à nommer** |


## 20.9 🎯 CE QUE LA SÉANCE DU 2026-08-22 A SOLDÉ SUR LE FIL — firmware `38c3b99`

### L14 EST SOLDÉ, ET PROUVÉ SUR LA CARTE

Le résiduel de revue *« `pc` ne peut plus nommer QUEL ventilateur est muet »* est fermé. Relevé
**sur la carte**, LHM absent (⛔ aucun agent ne tournait, trame injectée par `pc $DN,…`) :

```
disk -> case 4 DISQUE   100000,0 Mo/s · extr.moy 10000,0 tr/min ·
                        ventirad 10000,0 tr/min · boitier 10000,0 tr/min
```

⚠️ **AVANT**, cette ligne rendait **trois entrées byte-identiques**
`-- (tr/min ATTENDUE, non publiee par la source)`, parce que `cmd_pc` imprime
`dn_link_metrique_unite()` — l'unité **DU FIL** — et que `disk` y porte trois `"tr/min"`.
✅ Le préfixe est un **nom d'ÉCRAN affiché EN PLUS**, via `dn_ui_case_prefixe()`. ⛔ **JAMAIS** en
touchant `k_metriques[].unite`, qui casserait les témoins v1 et v3.
🎯 **Et c'est cette console que `regime_reel_dn48.py` et `campagne_bruit_dn48.py` LISENT.**

⚠️ **`pc` imprime en DIXIÈMES** (`10000,0 tr/min`), l'écran en **ENTIER** (`10000 tr/min`) : la
console montre le **FIL**, l'écran applique la **précision du descripteur**. ⛔ Ne pas lire la
décimale de `pc` comme un défaut d'affichage.

### ⚠️ DEUX PIÈGES D'INSTRUMENT DE CETTE SÉANCE, TOUS DEUX LES MIENS

1. 🔴 **LA PÉREMPTION EST À 3 s, ET ELLE FABRIQUE DES FAUX `--`.** Une trame injectée puis relue
   dans une **invocation suivante** de `dn_console.py` rend `ABSENTE` : la valeur a péri entre les
   deux. ⛔ Un « `--` » n'est **pas** une preuve que l'affichage est cassé tant qu'on n'a pas montré
   que la valeur était **encore vivante** au moment de la lecture. ⇒ trame et lecture **dans la
   MÊME invocation**, et le dump long (`widget`) rate encore la fenêtre une fois sur deux.
   ✅ Pour un état **soutenu**, `dn_injecteur.py --secondes N` puis lecture **immédiate** — mais
   ⛔ pas en parallèle : le port est exclusif, et *« deux processus lisent `/dev/ttyACM0` sans
   erreur et SE VOLENT LES OCTETS »*.
2. 🔴 **PIÈGE N°10, PRIS EN FLAGRANT DÉLIT** : j'ai **recopié** un checksum au lieu d'utiliser celui
   que je venais de calculer, et la trame est tombée en rejet. *« Une trame de test copiée d'une doc
   peut être FAUSSE. »* ⇒ La commande qui calcule et la commande qui envoie doivent être **le même
   geste** (`CK=$(python3 -c …)` puis `…*$CK`), ⛔ jamais deux étapes séparées par un copier-coller.

### ⚠️ CE QUE `--jeu pire` N'EST PAS

Il sert des valeurs **plausibles hautes**, ⛔ **pas les plafonds du protocole** : `3000 tr/min` là
où `k_metriques[]` autorise **10000**, `5,7 GHz` là où le plafond est `100,0`. ⇒ **Il ne produit
pas le pire cas de largeur.** Celui-là se mesure **séparément**, par `widget largeur` sur la chaîne
construite depuis les plafonds — ce que `tools/verif_selection_dn49.py` **émet**.
⛔ Conclure « ça tient » du seul injecteur serait valider un cas qu'on n'a pas joué.

### 20.10 Entrées au ledger portées par la SÉANCE du 2026-08-22 — ⛔ par AJOUT

| # | Entrée | État | Condition de réouverture / de clôture |
|---|---|---|---|
| L10 | **L'échelle haute de `DISQUE` (`Mo/s → Go/s`)** | ✅ **SOLDÉE le 2026-08-22** | **ARMÉE** sur décision owner (règle des 3000). 🎯 **Et elle réparait un défaut LIVRÉ que personne n'avait vu** : `« 100000,0 Mo/s »` = **206 px pour 201 utiles**, la grandeur 0 débordait déjà |
| L14 | **`pc` ne nomme pas quel ventilateur est muet** | ✅ **SOLDÉ le 2026-08-22, PROUVÉ SUR CARTE** | `dn_ui_case_prefixe()` + `cmd_pc` |
| L16 | 🆕 **La marge de hauteur du détail `DISQUE` est de ZÉRO pixel** | 🟠 **choix ASSUMÉ** | `14 + 4×35 = 154` dans un panneau de **154**. C'est le minimum EXACT, pris pour ne pas coûter un pixel de plus à `dn4-4`. ⛔ Une grandeur de plus, ou une police plus haute, et ça déborde — **la garde de hauteur le dira**, elle existe depuis cette séance |
| L17 | 🆕 **`dn4-4` hérite d'un placeholder de courbe à 108 px, ⛔ pas 165** | 🔴 **facture DITE** | **57 px** repris, ⛔ pas 43 : mon arithmétique avait oublié le `y = 14` du label, et **c'est la carte qui l'a corrigée** une fois l'instrument capable de voir la hauteur. Le bas reste à **370** |
| L18 | 🆕 **Deux prédictions d'AC9 sont INDÉCIDABLES faute de T0** | 🔴 **défaut de protocole, le mien** | Δ tas LVGL (`ui`) et Δ `cpu brut` : les deux instruments sont nommés dans la prédiction et **aucun n'a été relevé au T0**. ⇒ **Règle** : toute prédiction NOMME son instrument, et **le T0 de CET instrument se relève AVANT le premier tir**. ⛔ Une prédiction qu'on ne peut pas confronter ne coûte rien à celui qui l'écrit |
| L19 | 🆕 **La colonne « AVANT » du tableau d'AC6 n'était pas observable** | ✅ **CLOS par la mesure** | `desc_ligne_indistincte` **n'existe pas** dans `4c3a3f7` (grep : 0, contre 3 à `cdfe88c`) : la garde est arrivée **après** le flash. ⛔ Ce n'était pas une régression, et ⛔ ce n'était pas non plus un état observable |
| L20 | 🆕 **`--jeu pire` n'atteint PAS les plafonds du protocole** | 🟠 **limite NOMMÉE de l'instrument** | `3000 tr/min` pour un plafond à `10000`. ⛔ Il ne produit donc pas le pire cas de LARGEUR. Rouvrir si une story a besoin du plafond en régime soutenu ; jusque-là, `widget largeur` sur la chaîne des plafonds fait foi |

---

## 21. 🎯 SÉANCE CARTE DU 2026-08-24 — les décisions D3 et D4 de la 2ᵉ revue, VALIDÉES SUR LE MATÉRIEL

**Firmware `e85107e`**, SHA **LU AU BANDEAU** (`App version: e85107e`), ⛔ pas déduit du dépôt.
`git status --porcelain` **vérifié VIDE avant le flash** — 12 commits posés d'abord, un par sujet.
Build : **0 avertissement, 0 erreur**, `desknode.bin` 0xf6fa0 o (76 % libre).

### 21.1 Ce que la séance valide

| Tir | Instrument | Résultat |
|---|---|---|
| **D3** — icônes en vue DÉTAIL | **constat owner à l'œil** | ✅ *« oui les flèches ok »* · *« pas de débordement »* |
| **D3 bis** — pire cas du tampon (`DISQUE` à 4 grandeurs, aux plafonds) | **constat owner à l'œil** | ✅ *« boitier 10000 tr/min est sur la limite mais ça rentre, pas de débordement sur les côtés, bien centré »* |
| **D4** — la garde refuse l'override 4-4 | console, avec **témoin positif** | ✅ `widget grandeurs 4 2` **ACCEPTÉ** · `widget grandeurs 4 4` **REFUSÉ (`ESP_ERR_INVALID_ARG`), « RIEN n'a changé »** |

🎯 **Le motif rendu par la carte est EXACTEMENT celui prédit** :
> *« dans la vue CASE, la grandeur 2 porterait l'unité "tr/min" DÉJÀ présente sans préfixe ni icône
> QUI Y SOIT AFFICHÉ — deux lignes identiques à l'œil, dont une ment par omission. ⚠️ Un préfixe
> marqué `prefixe_detail_seul` ne compte PAS dans la CASE : il n'y est pas dessiné. »*

⇒ **RÉFUTATION MESURÉE** : l'Acceptance Auditor de la 2ᵉ revue concluait que *« l'override 4-4 est
DÉBLOQUÉ »*. **FAUX**, et la carte le dit. Le constat avait déjà été réfuté par lecture le matin ;
il l'est désormais **par le matériel**.

### 21.2 Le texte composé, relu des objets LVGL — ⛔ pas déduit du code

`RÉSEAU`, deux grandeurs, **les icônes sont dans la chaîne**, chacune devant SA valeur :

```
« EF 81 B8  985,0 Mb/s   ·   EF 81 B7  48,0 Mb/s »
   LV_SYMBOL_DOWN            LV_SYMBOL_UP
```
largeur **416 px** pour 446 utiles ⇒ tient.

`DISQUE`, quatre grandeurs **aux plafonds du protocole** (`1000000,100000,100000,100000`) :

```
100,0 Go/s
extr.moy 10000 tr/min
ventirad 10000 tr/min
boitier 10000 tr/min
```
largeur **315 px** pour 432 utiles · hauteur **`14 + 140 = 154 ≤ 154`, MARGE ZÉRO** ·
**0 log `TAMPON TROP COURT`** (le texte pèse ~75 o pour 184 disponibles) ·
**0 `rejets_bornes`** alors que l'injection était AUX plafonds — ils sont donc bien **atteignables**.

### 21.3 🔴 DEUX DÉFAUTS D'INSTRUMENT DE CETTE SÉANCE — les miens, et ils ont coûté une observation owner

1. 🔴 **UNE OBSERVATION OWNER GÂCHÉE : j'ai fait regarder un état PÉRIMÉ.** `detail_reparametrer()`
   porte un court-circuit — `if (e->regime == DN_VAL_ABSENTE || e->txt[0][0] == '\0') → buf = "--"` —
   et ma boucle patchée est dans le `else`. Entre l'injection et la lecture de l'owner, la
   péremption (3 s) était passée : l'écran montrait **un seul `--`**, sans icône ni découpage.
   Le constat *« pas de flèche »* était **JUSTE**, et il **ne testait pas le correctif**.
   ⇒ **Une vue qui périme en 3 s exige une injection CONTINUE pendant l'observation.** La fenêtre
   se prépare AVANT de demander les yeux.
2. 🔴 **UNE TRAME MODIFIÉE SANS RECALCULER LE CHECKSUM.** J'ai passé `seq 1 → 5` en gardant `*4A` ;
   le vrai était `*4E`. Elle est tombée en `rejets_checksum`, et j'ai conclu deux fois sur un tir
   qui n'avait rien mesuré. ⚠️ **C'est le piège n°10 du skill, à la lettre.** ⇒ le checksum se
   GÉNÈRE, ⛔ il ne se tape pas.

### 21.4 ⛔ CE QUE CETTE SÉANCE NE PROUVE PAS

- **`890 pertes seq` et `1 rejets_checksum` sont des ARTEFACTS DU HARNAIS**, ⛔ pas des mesures de la
  liaison : l'injection tournait à **~100× la cadence nominale** (le REPL en série, pas 1 Hz), et
  `dn_console.py` est documenté comme perdant des lignes à ce régime. **Aucun taux de perte ne peut
  être publié depuis cette séance.**
- Le **parse PowerShell** de `dn_lhm_tour.ps1` et `deployer_tour.sh --verifier` exigent la TOUR :
  ⛔ non joués ici.
- **`campagne_bruit_dn48.py` et `regime_reel_dn48.py` n'ont PAS été rejoués** — leurs instruments ont
  changé en 2ᵉ revue, donc **§18.2 et §18.3 restent MORTES**. C'est le reste de `dn4-8`.

### 21.5 🔴 DEUX CONSTATS QUI SORTENT DU PÉRIMÈTRE `dn4-8` — ils appellent un `[CC]`

Les deux portent sur la **vue DÉTAIL**, livrée par **`dn4-9`, qui est `done`**. ⛔ Son dossier n'est
pas réécrit en silence.

1. ~~🔴 **LE DÉTAIL NE PROPAGE PAS LES CHANGEMENTS DE VALEUR TANT QU'IL EST OUVERT.** MESURÉ : le fil
   portait `111,0 / 222,0 Mb/s` (**accepté**, `seq 84`, `age 102 ms`) pendant que le détail affichait
   toujours **`985,0 / 48,0`** — les valeurs de l'**OUVERTURE**. Tenu sur 15 injections / ~1,5 s,
   donc bien au-delà du tick à 5 Hz.~~ ✅ **La PÉREMPTION, elle, passe** (retour à `--`) : AC7 de
   `dn2-2` tient.

   🔴 **AMENDÉ LE 2026-08-24 PAR `dn4-4` (AC1) — ⛔ PAS EFFACÉ. LE CONSTAT EST RÉFUTÉ, ET LA CAUSE
   PUBLIÉE L'EST DEUX FOIS.** Voir **§21.6**. En un mot : le SYMPTÔME était réel, mais il vient de
   ce harnais-ci, ⛔ pas du firmware — et l'explication qui en a été tirée (« `detail_reparametrer()`
   n'a qu'un seul appelant ») était fausse **par simple `grep`**.
2. ⚠️ **MARGE ZÉRO EN HAUTEUR sur le pire cas `DISQUE`** : `14 + 140 = 154 ≤ 154`. L'arithmétique et
   l'œil **CONCORDENT** (*« sur la limite mais ça rentre »*). ⛔ Ce n'est **pas** une régression de
   `dn4-8` : les icônes s'insèrent DANS la ligne, elles n'en ajoutent aucune.

### 21.6 🔴 `dn4-4` / AC1 — LE CONSTAT n°1 DE §21.5 EST RÉFUTÉ **PAR LA MESURE**, ET SA CAUSE PUBLIÉE L'EST **PAR LECTURE**

**Firmware sous test : `d379c0d`, SHA LU AU BANDEAU** (`App version: d379c0d`).
⚠️ **ET C'EST FONCTIONNELLEMENT LE BINAIRE DE §21.5** : entre `e85107e` (la séance) et `d379c0d`,
`git diff -- firmware/` ne rend **qu'un commentaire** dans `dn_ui.c` — **zéro ligne de code**.
⛔ Le firmware n'est donc pas une variable entre les deux observations.

#### a. La cause publiée est fausse, et ça se vérifie en une commande

Le `[CC]` du 2026-08-24 écrit que `detail_reparametrer()` *« n'a **qu'UN SEUL appelant** —
`build_detail()` … **aucun chemin de mise à jour de données ne l'appelle** »*.
`grep -n detail_reparametrer firmware/desknode/main/dn_ui.c` rend **TROIS** sites d'appel :

| # | Fonction | Nature | Posé par |
|---|---|---|---|
| 1 | `build_detail()` | construction de la vue | — |
| 2 | `nav_appliquer()`, branche `DN_NAV_SCREENS` | transition | — |
| 3 | 🔴 **`case_poser()`** | 🔴 **MISE À JOUR DE DONNÉES** | 🔴 **`030f0566`, 2026-08-17 18:45** |

#### b. La propagation MARCHE — témoin POSITIF, six trames, dans l'ordre

Protocole (`tools/diag_p1_dn44.py`), **écrit avant d'être exécuté**, et construit pour **ne pas
pouvoir fabriquer le faux positif de l'injecteur** (dont les jeux portent des valeurs FIXES) :
valeurs qui **changent** à chaque trame · `seq` **incrémenté** · checksum **recalculé** · injection
**continue** (péremption 3 s) · lecture par **`widget detail`** (relecture des objets LVGL).

| `seq` | ce que le fil portait | ce que la DALLE portait |
|---|---|---|
| 300 | `111,0 / 222,0` | `111,0 Mb/s · 222,0 Mb/s` |
| 301 | `333,0 / 333,0` | `333,0 Mb/s · 333,0 Mb/s` |
| 302 | `555,0 / 444,0` | `555,0 Mb/s · 444,0 Mb/s` |
| 303 | `777,0 / 555,0` | `777,0 Mb/s · 555,0 Mb/s` |
| 304 | `999,0 / 666,0` | `999,0 Mb/s · 666,0 Mb/s` |
| 305 | `1221,0 / 777,0` | `1221,0 Mb/s · 777,0 Mb/s` |

⇒ **6 sur 6, dans l'ordre, la page restant OUVERTE.** ⛔ Aucune reconstruction de vue.

#### c. 🔴 LE SYMPTÔME EST REPRODUIT À VOLONTÉ — PAR LE HARNAIS, ET LE COMPTEUR LE DIT

Témoin **négatif** : cinq trames à **`seq` FIGÉ (316)**, dont les **valeurs changent à chaque tour**.

```
tour 1/5 · seq FIGÉ 316 · fil « 999,0 / 111,0 »   dalle « 999,0 Mb/s · 111,0 Mb/s »
tour 2/5 · seq FIGÉ 316 · fil « 888,0 / 210,9 »   dalle « 999,0 Mb/s · 111,0 Mb/s »
tour 3/5 · seq FIGÉ 316 · fil « 777,0 / 310,8 »   dalle « 999,0 Mb/s · 111,0 Mb/s »
tour 4/5 · seq FIGÉ 316 · fil « 666,0 / 410,7 »   dalle « 999,0 Mb/s · 111,0 Mb/s »
tour 5/5 · seq FIGÉ 316 · fil « 555,0 / 510,6 »   dalle « 999,0 Mb/s · 111,0 Mb/s »
doublons : 1 -> 5 (+4) · textes DISTINCTS sur la dalle : 1
```

C'est `dn_link.c` (*« rejouer un seq n'est pas une donnée »*) : la trame est comptée en **`doublons`**
et **la valeur n'entre pas**. Une propagation qui MARCHE rend alors **exactement** l'écran de §21.5.
⚠️ **Et §21.4 dit déjà que ce harnais-là perdait des lignes** : l'injection de §21 tournait à
**~100× la cadence nominale** avec **890 `pertes seq`**.

⛔ **CE QUE §21.6 NE PROUVE PAS** : que le `seq` était figé *ce jour-là*. La fenêtre brute de §21.5
n'a pas été capturée — seul le récit subsiste. Ce qui est prouvé, c'est que **le firmware propage**
et qu'**un harnais suffit à produire le symptôme**. La cause exacte de ce tir-là reste **indécidable**,
et c'est dit plutôt que comblé.

#### d. Les trois autres témoins d'AC2 (`tools/temoins_ac2_dn44.py`)

| Témoin | Résultat |
|---|---|
| **PÉREMPTION** — injection coupée 4,0 s | ✅ retour à `--` (**AC7 de `dn2-2` NE RÉGRESSE PAS**) |
| **MOCK** — `widget mock on` | ✅ régime **`SIMULÉE`** relu dans la table de `widget`, valeur qui **VARIE** (`845` → `705`) |
| **CROISÉ** — détail sur `CPU`, `net` qui bouge 3 fois | ✅ le détail de `CPU` **NE BOUGE PAS** (`50,0 % · 3,0 GHz | c.max 50,0 % · 40,0 °C`, identique) |

#### e. 🔴 LA CADENCE, MESURÉE — ⛔ « 5 FOIS PAR SECONDE » ÉTAIT FAUX POUR LE DÉTAIL

| Grandeur | Relevé |
|---|---|
| trames acceptées sur la fenêtre | **100** |
| poussées avec label posé (`latence acceptation->label`, `n`) | **100** |
| durée de la fenêtre | **20,5 s** |
| ⇒ **cadence, TOUTES métriques** | **5,0 poussées/s** |
| ⇒ **cadence PAR métrique** | **1,0 poussée/s** |
| plafond structurel (`tache_lien`, `vTaskDelayUntil` 250 ms) | **4 poussées/s** |

⇒ `detail_reparametrer()` ne sert **que la métrique affichée** (`s_metrique == idx`) : elle tourne
**~1 fois par seconde en régime**, **jamais 5**. Les « 5 fois par seconde » du reste du firmware
décrivent le chemin `case_poser`/`dn_widget_maj`, parcouru pour les **CINQ** métriques : **ils sont
justes**, et ils sont désormais **datés de cette mesure**.

> 🔴 **AMENDÉ LE 2026-08-24 (2ᵉ passe, revue de code) — CETTE PHRASE DISAIT « DU RESTE DU
> FIRMWARE », ET C'EST PRÉCISÉMENT L'ANGLE MORT QU'ELLE A LAISSÉ OUVERT.** Le premier balayage
> d'AC3 n'a couvert que `firmware/` ; le `grep` que l'AC prescrit porte sur **`firmware/ hardware/`**.
> Trois occurrences vivaient dans le **dossier de mesure** et n'ont été annotées qu'à la revue :
> `affichage.md:4210`, `affichage.md:4578`, `liaison-pc.md:1842`. ⇒ **Le balayage couvre désormais
> `firmware/` ET `hardware/`**, et le `grep` de l'AC rend **zéro occurrence non annotée**.
> ⚠️ Leçon : *un critère mécanique ne vaut que si on le joue sur le périmètre qu'il nomme, pas sur
> celui qu'on a sous la main.*

✅ **CONSÉQUENCE** : la garde de largeur/hauteur de `detail_reparametrer()` **EST rejouée** sur la vue
ouverte — ⛔ elle n'est **pas** décorative, contrairement à ce que le `[CC]` a conclu. Le seul
reproche qui tienne est qu'**aucun témoin négatif ne l'a jamais fait crier** : c'est le travail
d'AC4.

#### f. 🔴 DEUX DÉFAUTS DE CADRAGE DE `dn4-4`, TROUVÉS EN L'EXÉCUTANT

1. **`nav ab 40` ne rend pas `n = 40`, il rend `n = 80`.** `nav ab <n>` fait `n` **allers-retours**
   et chronomètre les **deux** sens. Le protocole des trois points publiés est **`nav ab 20`** —
   **le firmware l'imprime lui-même** (`nav model` : *« comparer proprement : `touch reset` puis
   `nav ab 20` »*). ⇒ les deux ont été tirés, et ils **concordent à 0,8 ms**.
2. **`widget mock` n'est pas l'instrument de G3.** Sans `on|off` cette sous-commande imprime son
   usage et rend `0x1`. L'état du mock est publié par **`widget` nu** (ligne `mock : ARME|COUPE`,
   plus la colonne `regime` par case).

---

---

## 22. 🎯 SÉANCE DU 2026-08-24 (suite) — §18.2 ET §18.3 SONT RÉGÉNÉRÉES

Les deux campagnes de séance avaient été **déclarées MORTES** par la 2ᵉ revue : leurs instruments
avaient changé. ⛔ On ne republie pas un chiffre produit par un instrument qui n'existe plus.
**Firmware `d379c0d`**, SHA **lu au bandeau**, `porcelain` vérifié vide avant le flash.

### 22.1 AC7 — la campagne de bruit, REJOUÉE : **14 contrôles, exit 0**

🎯 **CE QUE CE TIR PROUVE, ET QUI N'AVAIT JAMAIS PU L'ÊTRE** : les **DEUX TÉMOINS v3** — ceux qui
soldent AC5 — **passent**. Avant les correctifs de la 2ᵉ revue ils sortaient ✖️ **sur une carte
saine**, parce que `dn4-9` avait posé les préfixes d'écran et qu'aucun instrument de `dn4-8` ne
savait les lire.

| Contrôle | Compteur touché |
|---|---|
| version hors `[1..3]` | `version` (27 o) |
| `ver=1` à 7 champs · `ver=2` à 9 champs · plus de valeurs que la métrique | `format` (31 / 39 / 39 o) |
| °C hors plafond (1600 > 1500) · `tr/min` hors plafond (999999 > 100000) | `bornes` (40 / 47 o) |
| ligne complète dans la bande **72..124** | `trop longue` (**78 o**, bande confirmée ATTEIGNABLE) |
| ligne sans `*CK` · checksum faux · champ vide en position 0 | `tronquee` / `checksum` / `format` |
| **champ vide en position INTERNE** | ✅ **ACCEPTÉE**, valeur suivante NON décalée |
| **TÉMOIN v1** · **TÉMOIN v3 `cpu`** · **TÉMOIN v3 `disk`** | ✅ **les trois VERTS** |

⇒ **11 cas de bruit** + témoin v1 + 2 témoins v3 = **14**. ⚠️ Le « 10 cas » publié en trois endroits
du dossier était **faux** ; corrigé par la 2ᵉ revue, **confirmé par le recompte de ce tir**.

### 22.2 AC8 — le régime réel, REJOUÉ : le ✅ est désormais MÉRITÉ

Agent **RÉEL** sur `COM3`, 20 s, puis `pc` relu **dans la péremption**.

```
compteurs de RECEPTION (delta) : {'valides': 100, 'doublons': 0, 'pertes seq': 0, 'resynchros': 1}
✅ AUCUN COMPTEUR DE REJET N'A MONTE (les six a zero de delta), ET LA CARTE A ACCEPTE 100 TRAME(S).
```

🔴 **C'EST LA DIFFÉRENCE AVEC §18.3** : l'ancien instrument concluait ✅ **sans jamais vérifier que la
carte avait reçu quoi que ce soit** — un critère satisfait par l'état MORT. Il lit désormais la ligne
`trames : … valides`, publiée **une ligne au-dessus** de celle qu'il lisait, et **ÉCHOUE** si le delta
est nul.

**Les quatre grandeurs LHM sont VIVANTES sur le fil, avec leurs préfixes d'écran :**

| Métrique | Ce que la dalle porte |
|---|---|
| `cpu` | `40,9 %` · `3,2 GHz` · **`c.max 48,6 %`** · **`45,0 degC`** |
| `disk` | `0,1 Mo/s` · **`extr.moy 1098,5`** · **`ventirad 393,7`** · **`boitier 946,9 tr/min`** |

Latence acceptation→label : **n=104 · min 54 ms · moy 199 ms · max 265 ms**.

### 22.3 🔴 UNE RÉGRESSION QUE J'AI INTRODUITE EN 2ᵉ REVUE, ET QUE SEULE LA CARTE A TROUVÉE

Le premier tir de `regime_reel_dn48.py` est sorti en **traceback**, sur une carte qui répondait
parfaitement.

**Cause** : le correctif de revue convertissait `time.time()` → `time.monotonic()`. Il avait converti
`fin = time.monotonic() + timeout` et **PAS** la comparaison `while time.time() < fin`.
`monotonic()` rend l'uptime (~2·10⁵), `time()` rend l'epoch (~1,7·10⁹) : la condition était **fausse
immédiatement**, la boucle de lecture **ne tournait jamais**, `buf` restait vide.
⇒ **`cmd()` était cassée sur toute la ligne**, et l'instrument accusait le sujet sain — la faute même
que le patch prétendait corriger.

⚠️ **CAUSE DE LA FAUTE, ET ELLE EST INSTRUCTIVE** : la conversion a été faite sur une liste `grep`
**TRONQUÉE** — elle annonçait **6 occurrences et n'en listait que 5**. ⛔ **Compter les occurrences
sans intermédiaire qui résume.**

**Second défaut trouvé du même coup** : le correctif de revue protégeait l'extraction d'**APRÈS** et
avait oublié celle d'**AVANT**. Un traceback nu sortait encore sur la baseline. ⇒ **un défaut qu'on
prétend fermer se ferme des DEUX côtés, ou il n'est pas fermé.**

### 22.4 ⛔ CE QUE CETTE SÉANCE NE PROUVE TOUJOURS PAS

- **`969 pertes seq` en CUMULÉ** est un artefact des injections manuelles de §21 (~100× la cadence
  nominale). 🎯 **Le DELTA du tir, lui, est `0`** — et c'est le seul chiffre opposable.
- **AC9 reste ROUVERT** : aucun re-tir de coût n'a eu lieu.
- **AC2 reste MORT**, et l'**étalonnage sous charge d'AC4** reste dû.

---

## 23. 🔴 AC9 RE-TIRÉ — LA PRÉDICTION, ÉCRITE ET COMMITTÉE **AVANT** LA MESURE

⛔ **Ce bloc est committé AVANT que l'agent ne tourne.** AC9 : *« La prédiction s'écrit ET SE
COMMITTE AVANT la mesure. »* Si le commit suivant portait déjà le résultat, il n'y aurait pas de
prédiction, il y aurait une justification.

### 23.1 Pourquoi un re-tir

Le chiffre n°1 de §16.6 (**2,523 % d'un cœur / 0,1577 % machine**) a été mesuré au SHA `4c3a3f7`.
Depuis, `agent/dn_agent.py` a changé de **+474/−42**, et le delta tombe **dans le chemin par cycle**.
La 2ᵉ revue l'a déclaré **MORT** (décision owner D1 du 2026-08-24).
✅ **Le chiffre n°2 (LHM seul, 7,990 % / 0,4994 %) n'est PAS re-tiré** : ce delta ne touche pas LHM.

### 23.2 Ce qui s'est ajouté au chemin par cycle, et ce que ça devrait coûter

| Ajout | Fréquence | Coût unitaire attendu |
|---|---|---|
| `read1()` + `_borner_socket()` **par morceau** (`perf_counter` + `settimeout`) | ~2/cycle (75 Ko / 64 Ko) | µs |
| `_borner_socket()` **avant `request()`** (2ᵉ revue) | 1/cycle | µs |
| `_chrono` couvre le parse | comptabilité seule | ~0 |
| regex à **4 groupes** | **253 lignes/s** | ns/ligne |
| 2 compteurs (`lues`, `illisibles`) | **253/s** | ns |
| **`dict.get` de détection de doublon** (2ᵉ revue) | **253/s** | ~50 ns ⇒ **~13 µs/s ≈ 0,0013 %** |
| garde `lues == 0` · `_lhm_rendu` | 1 et 4/cycle | ns |
| vérification de famille | 5/s | ns |

⇒ **Le poste le plus lourd de tous est estimé à 0,0013 % d'un cœur.** L'ensemble reste **deux ordres
de grandeur sous la résolution** de la mesure.

### 23.3 🎯 LA PRÉDICTION

> **À 60 s de cumul, sur `COM3`, 16 cœurs logiques :**
> **`[2,35 ; 2,75] % d'un cœur`** et **`[0,147 ; 0,172] % machine`**
> — c'est-à-dire **INDISCERNABLE de 2,523**.

**Ce qui la démentirait, et il faudrait alors CHERCHER, ⛔ pas accepter** : une valeur **> 2,75**
signalerait un coût que le tableau ci-dessus n'a pas vu.

### 23.4 ⛔ LES DEUX PIÈGES DE COMPARAISON, NOMMÉS AVANT LE TIR

1. 🔴 **LE TÉMOIN N'AVAIT PAS CONVERGÉ À 60 s.** §16.6 le dit : `5,141 → 3,586 → 3,167 → 2,810 →
   2,686 → 2,523`. ⇒ **la comparaison se fait au MÊME rang de la série**, ⛔ pas entre un 60 s et un
   180 s. La série complète est publiée, pas seulement son dernier point.
2. ⛔ **JAMAIS un chiffre `--stdout` contre un chiffre `COM3`** : le port coûte **+0,63 pt** en
   propre. Le tir se fait sur `COM3`, comme §16.6.

⚠️ **ET CE QUE CE TIR NE MESURERA PAS** : la tour n'est pas au repos contrôlé. Une charge de fond
différente de celle du 2026-08-21 déplace le mural, donc le rapport. C'est une **réserve**, ⛔ pas une
excuse — elle est écrite avant, pas après.

### 23.5 🎯 LE RÉSULTAT — prédiction TENUE, **par la borne basse**

Agent **RÉEL** sur `COM3`, `--temoin`, 180 s, firmware `d379c0d`, 16 cœurs logiques.

| | Prédit (committé `9297fd4`, **avant** le tir) | Mesuré à 60 s | Verdict |
|---|---|---:|---|
| % d'un cœur | `[2,35 ; 2,75]` | **2,367** | ✅ dedans — **marge 0,017 pt** |
| % machine | `[0,147 ; 0,172]` | **0,1480** | ✅ dedans — **marge 0,001 pt** |

⚠️ **DANS LE BON SENS** : la prédiction annonçait *« indiscernable de 2,523 »*. La mesure est **plus
BASSE**, et elle frôle la borne posée par prudence. **Le raisonnement a vu juste sur l'ordre de
grandeur, ⛔ pas sur le signe.**

### 23.6 🔴 LA BAISSE EST À **TOUS LES RANGS**, ⛔ pas sur un point

| rang | 10 s | 20 s | 30 s | 40 s | 50 s | **60 s** |
|---|---:|---:|---:|---:|---:|---:|
| §16.6 (`4c3a3f7`) | 5,141 | 3,586 | 3,167 | 2,810 | 2,686 | **2,523** |
| **ce tir (`9297fd4`)** | 4,348 | 3,431 | 2,859 | 2,692 | 2,497 | **2,367** |
| Δ | −0,793 | −0,155 | −0,308 | −0,118 | −0,189 | **−0,156** |

⇒ 🎯 **L'HYPOTHÈSE « LES +474/−42 ONT ALOURDI L'AGENT » EST RÉFUTÉE** : il est moins cher aux six
rangs. C'est la comparaison **au même rang** qu'AC9 exige, et elle est faite.

⛔ **CE QUE CE TIR NE TRANCHE PAS** : un décalage **uniforme** s'explique aussi bien par un agent
réellement plus léger que par une **charge de fond différente**. ⛔ Pas de témoin de contrôle. La
réserve était écrite AVANT le tir (§23.4), elle tient — **c'est une réserve, pas une excuse**.

⚠️ **LA SÉRIE N'A TOUJOURS PAS CONVERGÉ** : 180 s ⇒ **2,065 %** (`0,1291 %` machine), et elle
descend encore. ⛔ Ne comparer que des rangs identiques.

### 23.7 ⚠️ UN FAIT QUE CE TIR NE S'EXPLIQUE PAS — et qu'il ne faut pas expliquer au jugé

```
LHM : 181 lecture(s) reussie(s), 0 en echec — duree moyenne 53,0 ms, MAX 424,3 ms
```

§18.4 donnait **24,1 ms de moyenne / 181,9 ms max**. C'est **2,2× plus lent en MURAL**, pendant que
le **CPU BAISSE**. Les deux ensemble pointent vers de l'**ATTENTE** (I/O), ⛔ pas du calcul — attendre
ne consomme pas de CPU.
⛔ **MAIS CE N'EST PAS AFFIRMÉ** : deux sessions, deux jours, charge de tour non contrôlée, et §18.4
écrit elle-même *« ⛔ NE PAS COMPARER … ce n'est ni la même session ni le même instrument »*.
🎯 **Le max reste sous le plafond** (424,3 ms pour 600 posées) et **0 lecture en échec** : le
dimensionnement de `LHM_TIMEOUT_S` tient. **⇒ AU LEDGER, pas conclu ici.**

### 23.8 Le reste du bilan, propre

**900 trames** émises (5,00/s), **0 erreur d'envoi**, **0 recalage de cadence**, **0 écrêtage**,
**5/5 sondes LHM** avec valeur, **0 lecture en échec**, **aucune absence LHM**.
✅ **Le chiffre n°2 (LHM seul, 7,990 % / 0,4994 %) reste celui de §16.6** — ce delta ne touche pas
LHM, il n'est pas re-tiré, et c'est écrit.
🎯 **LHM coûte donc toujours ~3,4× l'agent**, et D13 exigeait que ce soit dit.

⛔ **CE QUI RESTE OUVERT SUR AC9** : le **critère n°4 du brief** (« < 1 % ») n'est toujours pas coché
— **son unité n'est pas tranchée**. À `0,1480 % machine` il passe largement ; à `2,367 % d'un cœur`,
non. ⚠️ **C'est une décision owner, ⛔ pas une lecture.**

### 23.9 🎯 L'UNITÉ EST TRANCHÉE — DÉCISION OWNER DU 2026-08-24 : **% DE LA MACHINE**

Ce fichier écrivait lui-même *« le brief ne tranche pas laquelle il vise »*. **C'est tranché**, et
c'est énoncé **dans le brief** (critère n°4), là où l'entrée de ledger l'exigeait.

| lecture | mesuré (`COM3`, agent réel, 180 s, 2026-08-24) | verdict au critère « < 1 % » |
|---|---:|---|
| 🎯 **% de la MACHINE** *(retenu)* | **0,1480 %** | ✅ **PASSE**, avec **6,8× de marge** |
| % d'UN cœur | 2,367 % | ❌ (⛔ n'est plus le critère) |

✅ **LE CRITÈRE N°4 DU BRIEF EST COCHÉ.** Le titre d'AC9 (« SOUS 1 % ») cesse d'être une annonce non
démontrée. ⇒ **AC9 est SOLDÉ dans ses deux chiffres et dans son critère.**

⚠️ **LA CONSÉQUENCE, ÉCRITE AVANT QU'ON LA DÉCOUVRE** : le % machine **dépend du nombre de cœurs**.
À `2,367 % d'un cœur`, le critère tient **dès 3 cœurs logiques** (2,367 / 3 = 0,79 %) et
**ÉCHOUERAIT À 2** (1,18 %). **La tour en a 16.** ⛔ Ce n'est pas une objection à la décision —
c'est ce qu'il faut savoir avant de promettre le critère **sur une autre machine**.

⚠️ **ET ÇA SOLDE UNE SECONDE ENTRÉE DE LEDGER** : celle du « +0,26 pt d'isolation des sources »
disait *« si le critère vise le cœur, ce +0,26 pt compte ; s'il vise la machine, il est dans le
bruit »*. ⇒ **Il est dans le bruit.** Son A/B sur tour au repos n'est plus requis **pour ce
critère-là** — il reste dû si on veut **attribuer** le coût, ce qui est une autre question.

---

## 24. 🎯 AC2 RE-TIRÉ — LE CLASSEMENT EST RENVERSÉ, ET LA DÉCISION EST RECONDUITE **AVEC** LE CHIFFRE

Campagne du 2026-08-24 sur la tour : `n = 1000` par combinaison, **12 combinaisons**, **ordre
alterné** (`combos[r:] + combos[:r]`), 5 tirs jetés. Critère gelé `831f619` **vérifié non dérivé**.
Log et provenance : `mesures/dn4-8/ac2-retir-2026-08-24.log`.

| candidat / transport | CPU/tir | mur md | mur p95 | s.val | échecs |
|---|---:|---:|---:|---:|---:|
| `data.json` / keep-alive | 2,047 | 5,9 | 12,4 | 0 | 0 |
| 🎯 **`metrics` / keep-alive** *(retenu)* | **2,562** | **24,5** | **53,2** | **0** | 0 |
| `sensor_xN` / keep-alive | **1,141** | **1,7** | **2,7** | 0 | 0 |
| `data.json` / neuf | 2,984 | 27,7 | 35,5 | 0 | 0 |
| `metrics` / neuf | 3,703 | 40,9 | 75,1 | 0 | 🔴 **3 — DISQUALIFIÉ** |
| `sensor_xN` / neuf | 4,781 | 40,1 | 57,0 | 0 | C1 **et** C2 **DÉPASSÉS** |

🔴 **`/metrics` EN KEEP-ALIVE EST LE PLUS CHER DES TROIS KEEP-ALIVE, SUR LES QUATRE COLONNES.**
`sensor_xN` le bat **2,2× en CPU**, **14,7× en mural médian**, **19,9× en p95**.
⛔ **Ce chiffre n'est pas lissé, et il n'est pas effacé.**

### 24.1 🎯 DÉCISION OWNER DU 2026-08-24 : **ON GARDE `/metrics`**

**Motif, et il n'est disponible que depuis aujourd'hui** : l'unité du critère venait d'être tranchée
en **% MACHINE** (§23.9). À cette échelle, le gain d'un basculement vaut **1,42 ms/s ≈ 0,14 % d'un
cœur ≈ 0,0089 % machine** — l'agent passerait de `0,148` à `~0,139 %`. **Invisible sur un budget de
1 %.**

**Et trois motifs du choix d'origine ne sont PAS mesurés par cette campagne** :

1. **`s.val = 0` sur les DEUX jeux** — `/metrics` est le **seul candidat** à avoir rendu une valeur
   **à chaque tir** (`data.json` et `sensor_xN` en ont manqué 4 chacun sur le jeu B) ;
2. **unités de base, `InvariantCulture`** — ⚠️ `/data.json` rend `Value` **formaté selon la
   culture**, et la tour est **en français** : le dépôt a déjà éliminé `Get-Counter` pour cette
   raison exacte ;
3. **UNE seule requête quel que soit `N`** — `sensor_xN` est un **POST par sonde**, et il monte de
   `1,141` à `2,562` ms de 3 à 8 sondes.

⇒ **Les comparer sur le seul coût serait comparer à service INÉGAL.**

### 24.2 ⛔ CE QUI RESTE VRAI, ET QUI N'EST PAS EFFACÉ PAR LA DÉCISION

🔴 **Sur la QUEUE, l'écart est de 20×** (p95 `53,2` contre `2,7` ms). Or c'est **exactement la
queue** qui a forcé `LHM_TIMEOUT_S` de 0,40 à 0,60 s — §16.5 : *« LA QUEUE DE DISTRIBUTION EST BIEN
AU-DELÀ DU p95 D'AC2 »* — et **§23.7 relève une durée LHM moyenne à 53,0 ms dans l'agent, non
expliquée**.
⇒ 🎯 **Si la queue redevient un sujet, le chiffre est DÉJÀ MESURÉ, et il pointe vers `/Sensor`.**

⚠️ **Signal conservé** : `metrics/neuf` est **DISQUALIFIÉ** sur 3 `TimeoutError`. C'est l'autre
transport, ⛔ pas celui retenu — **mais c'est la même source.**

### 24.3 ⛔ CE QUE CETTE CAMPAGNE NE MESURE PAS

- **La tour n'est pas au repos contrôlé** : LHM tourne, l'agent non, et il n'y a **aucun témoin de
  charge de fond**. Un écart de 20× est trop gros pour être du bruit, ⛔ mais il n'est pas
  proprement **attribué**.
- **Ni la culture, ni la montée en `N` au-delà de 8** — c'est-à-dire précisément les deux motifs qui
  ont fait choisir `/metrics`.

### 24.4 AC4 — L'ÉTALONNAGE SOUS CHARGE EST **REPORTÉ PAR L'OWNER**

Verbatim du 2026-08-24 : *« je ferai des tests de charges plus tard »*.
⇒ ⛔ **Ce n'est ni un oubli ni un blocage : c'est un ÉCART DÉCLARÉ.** `dn4-8` se ferme avec lui.
✅ **Une qualification au repos reste VALIDE** — c'est une **NON**-qualification qui aurait été non
concluante, et les quatre grandeurs qualifient.
⚠️ **Et il pèse un refus owner antérieur** : *« non pas de tests comme ça sur le pc »*. ⛔ **Ce tir
ne se lance pas sans demande explicite.**

---

## 25. 🔴 `dn4-17` — L'AGENT VIT SUR LA TOUR : LE RÉGIME CHANGE, DONC LE CHIFFRE SE RE-MESURE

> ⛔ **CE BLOC EST COMMITTÉ AVANT QUE L'AGENT NE TOURNE SOUS LE NOUVEAU RÉGIME.**
> C'est la doctrine d'AC9 (`dn4-1`), appliquée en §23 : *« Si le commit suivant portait déjà le
> résultat, il n'y aurait pas de prédiction, il y aurait une justification. »*

### 25.1 Ce qui change dans le régime — ⛔ pas dans le code de mesure

Le chiffre de **§23.9** (`0,1480 % machine` / `2,367 % d'un cœur` au rang 60 s) décrit **un agent
lancé À LA MAIN DEPUIS WSL**. `dn4-17` livre autre chose :

| | §23 (2026-08-24) | 🆕 régime `dn4-17` |
|---|---|---|
| d'où l'agent est lu | dépôt WSL | **copie locale sur `H:\dev\projets\desknode`** |
| qui le lance | l'opérateur, à la main | **une tâche planifiée AU LOGON**, `-RunLevel Limited` |
| père du process | le shell | **`cmd.exe` du `.bat`**, vivant tout le run |
| console | oui | ⛔ **aucune** — `stderr` est **redirigé vers un fichier** |
| WSL | allumé | **peut être éteint** |
| dans le chemin par cycle | — | 🆕 **un `os.path.exists()`** (`--stop-si`), **1/s** |
| `--temoin` | posé pour le tir | **posé EN PERMANENCE** (il fait partie du régime livré) |

### 25.2 Ce que le nouveau chemin par cycle devrait coûter

| Ajout | Fréquence | Coût unitaire attendu |
|---|---|---|
| `os.path.exists(drapeau)` sur un NTFS **local** | **1/s** (PERIODE_S = 1,0 s) | ~10–50 µs ⇒ **~0,005 % d'un cœur** |
| `stderr` vers un **fichier** au lieu d'une console | 1 ligne / 10 s | ⚠️ **moins cher** qu'une console |
| chargement du `.py` depuis `H:` au lieu de `\\wsl.localhost` | **1 fois**, au démarrage | hors régime établi |

⇒ **Le seul poste récurrent nouveau est estimé à 0,005 % d'un cœur** — un ordre de grandeur sous la
dispersion observée entre deux tirs (§23.6 : Δ de 0,118 à 0,793 pt selon le rang).

### 25.3 🎯 LA PRÉDICTION

> **Agent RÉEL, `COM3`, `--temoin`, 16 cœurs logiques, lancé PAR LA TÂCHE, WSL éteint :**
>
> | rang | % d'un cœur | % machine |
> |---|---|---|
> | **60 s** | **`[2,20 ; 2,70]`** | **`[0,1375 ; 0,1688]`** |
> | **180 s** | **`[1,90 ; 2,30]`** | **`[0,1188 ; 0,1438]`** |
>
> — c'est-à-dire **INDISCERNABLE de 2,367 / 2,065**.

🔴 **CE QUI LA DÉMENTIRAIT, ET IL FAUDRAIT ALORS CHERCHER, ⛔ PAS ACCEPTER** : une valeur **> 2,70**
au rang 60 s signalerait un coût que le tableau de §25.2 n'a pas vu. La cause à suspecter en
premier serait **le drainage d'écho**, ⛔ pas le drapeau.

### 25.4 ⛔ LES RÉSERVES, ÉCRITES AVANT LE TIR — ET IL Y EN A **TROIS**, PAS DEUX

1. 🔴 **LES DEUX PIÈGES DE §23.4 TIENNENT ET SE RÉÉCRIVENT.**
   (a) **Comparer au MÊME RANG** : la série n'avait pas convergé à 60 s
   (`4,348 → 3,431 → 2,859 → 2,692 → 2,497 → 2,367`, puis **2,065** à 180 s). ⛔ Jamais un 60 s
   contre un 180 s. (b) ⛔ **JAMAIS un chiffre `--stdout` contre un chiffre `COM3`** : le port coûte
   **+0,63 pt** en propre. Le tir est sur `COM3`.
2. 🔴 **LHM DOIT ÊTRE VIVANT, SINON LE CHIFFRE N'EST PAS COMPARABLE À §23 — ET C'EST MESURÉ.**
   Le tir de §23 avait *« LHM : 181 lectures réussies, **0 en échec**, 53,0 ms de moyenne »*.
   Le 2026-08-26, la tour rend l'inverse : **0 réussie, 24 en échec**, chacune coupée au **timeout
   de 600 ms**. La tâche `LibreHardwareMonitor` est pourtant **PRÉSENTE** (`RunLevel=Highest`,
   `état=Ready`) — **LHM n'est simplement pas lancé** (0 processus). ⚠️ Une source qui échoue au
   timeout à chaque cycle change le **mural**, donc le **rapport** : *attendre ne consomme pas de
   CPU* (§23.7). ⇒ **Si LHM n'est pas vivant au moment du tir, le chiffre est publié AVEC cette
   mention et ⛔ N'EST PAS opposé à 2,367.**
3. ⚠️ **LE FIRMWARE N'EST PAS LE MÊME, ET IL PARLE.** §23 tirait sur `d379c0d`. La carte porte
   aujourd'hui le firmware de `dn3-3`. Le bruit de console mesuré le 2026-08-26 est de
   **226,1 o/s · 5,04 lignes/s** — c'est de l'écho que l'agent **draine**, donc du coût. ⛔ Un écart
   de bruit console est une cause de premier rang, et elle n'est pas contrôlée.
4. ⚠️ **La tour n'est pas au repos contrôlé** (réserve de §23.4, inchangée). C'est une **réserve**,
   ⛔ pas une excuse — elle est écrite **avant**.

### 25.5 ⛔ CE TIR NE SOLDE **PAS** L'ENTRÉE « +0,26 pt » DU LEDGER

[`deferred-work.md:1879`] Elle a **deux candidats non départagés** (isolation par source ·
découplage des fenêtres de débit) et exige un **A/B sur tour au repos**. 🔴 **Le changement de
régime de `dn4-17` en ajoute un TROISIÈME.** Mesurer après lui, sans point de comparaison,
**mélangerait trois causes dans un même chiffre**. ⛔ **PAS D'A/B ⇒ PAS D'ATTRIBUTION.**
⇒ **L'entrée RESTE OUVERTE**, avec ce motif.

---

### 25.6 Le geste de reprise de main — **MESURÉ**, ⛔ pas « plus simple »

`tools/rendre-port.sh` (nouveau) fait **les deux sens** en **une** commande. Le busid est **relu à
chaque appel** (⛔ jamais en dur : `usbipd list` rend **`3-1`** le 2026-08-26 là où `dn4-15` a
compté **`3-7`** — *il suit le port physique*, les deux ont été vrais).

| | AVANT (README § « le port est EXCLUSIF ») | 🆕 APRÈS (`rendre-port.sh`) |
|---|---|---|
| commandes owner | **4**, plus une **étape 0** | **1** |
| durée | réattachement seul : **2,7–3,1 s** (dn4-3) | **vers-agent 7,26 s** · **vers-flash 6,58 s** |
| n | — | **4 par sens**, 2026-08-26 |
| échecs | 🔴 **non nul** : veilleur ressuscité, `COM3` fantôme, « Attached » orphelin, RESET physique | **0 / 8** |
| detach re-vérifié | ⛔ non (`echo OK`) | ✅ **relu après 4 s** — et il **échoue bruyamment** si la ligne repasse à `Attached` |

⚠️ **LE GESTE EST PLUS LONG QUE LE `detach` NU, ET C'EST VOULU** : ~4 des 7,26 s de `--vers-agent`
sont **le délai de re-vérification**. On paie 4 s pour ne plus payer une heure — *« les veilleurs
ressuscitent en ~2 s »*, et c'est ce qui faisait échouer le rituel.
🔴 **ET LE COMPTE NE TRANCHE PAS, LE PORT TRANCHE** : à chaque passage, l'outil signale
**1 `usbipd.exe` à `CommandLine` ILLISIBLE** — *« ni tué, ni innocenté »*. Le faux négatif de
`wsl-attach.sh:75-81` est donc **VISIBLE** au lieu d'être silencieux, et le verdict reste
`STATE` + présence de `COM3` / `/dev/ttyACM*`.

### 25.7 🎯 LA FOURCHE « WSL vs WINDOWS-ONLY » — les DEUX colonnes, mesurées

| | branche **WSL** (`usbipd`) | branche **WINDOWS-ONLY** |
|---|---|---|
| rendre la carte au flash | `rendre-port.sh --vers-flash` — **6,58 s** | `dn-agent.bat stop` — **2,76 s** |
| rendre la carte à l'agent | `rendre-port.sh --vers-agent` — **7,26 s** | `dn-agent.bat start` — **5,39 s** |
| **aller-retour** | **13,84 s** | **8,15 s** |
| commandes owner | 2 | 2 |
| échecs mesurés | **0 / 8** | **0 / 1** |
| outil de flash | ESP-IDF **dans WSL** ✅ | 🎯 **`esptool 5.3.1` EST présent** sur le Python de la tour, et **il parle à la puce** : `MAC a0:f2:62:e3:d7:f4`, entrée **et sortie** de download mode (`--after watchdog_reset`) en **1,62 s** |
| **construire** le firmware | ✅ | 🔴 **NON** — `IDF_PATH` absent, **aucun** répertoire ESP-IDF côté Windows |
| dépendance `usbipd` | oui (veilleurs, busid, délai) | ⛔ **aucune** |

🎯 **VERDICT, AVEC SES CHIFFRES.** La branche Windows-only **existe déjà à moitié** : elle **flashe**
(1,62 s pour parler à la puce, `usbipd` entièrement dissous) mais elle **ne construit pas**.
⇒ **La bascule complète n'est PAS jouable aujourd'hui**, et le manque est **nommé** : ESP-IDF
côté Windows. ⛔ **On ne conclut donc pas sur la branche survivante** — la branche WSL reste le
régime, et le cap owner *« Windows-only à terme »* a désormais **son chiffre et son bloquant**.
⚠️ **Ce que ce relevé NE dit PAS** : le coût d'un `write_flash` réel côté Windows (seul un
`chip-id` a été joué), ni comment l'artefact construit dans WSL atteindrait `esptool` côté tour.

### 25.8 L'arrêt de l'agent — **le bilan était perdu à CHAQUE FOIS**, et c'est mesuré

| geste | l'agent meurt ? | bilan de fin écrit |
|---|---|---:|
| `taskkill /PID` (poli) | ⛔ **NON** — encore vivant après **5 s** | — |
| `taskkill /F` (repli) | ✅ | 🔴 **0 o** |
| 🆕 **drapeau `--stop-si`** | ✅ **en 1 s** | ✅ **1 560 o** |

🔴 **Pourquoi ça compte** : détaché ou en tâche planifiée, **l'agent n'a pas de console**, donc pas
de `Ctrl+C`. Le bilan est *« le seul instrument qui dit si la liaison va bien »* (trames émises,
erreurs d'envoi, recalages, bruit d'écho, refus firmware). Sans le drapeau, la redirection de
`stderr` d'AC3.6 sauvait le journal **de fonctionnement** et perdait **le bilan**.
⚠️ **Le repli `taskkill /F` reste**, et il **DÉCLARE** la perte au lieu de la taire.

### 25.9 La rotation du journal — **décision ÉCRITE, et elle est dimensionnée sur un débit MESURÉ**

| | mesuré le 2026-08-26 |
|---|---|
| `stderr` en **régime établi**, sans `--temoin` | **0 o/s** — les 1 162 o d'une session sont **tous écrits dans les 4 premières secondes**, puis plus rien pendant **178 s** |
| avec `--temoin` (le régime livré) | 1 ligne / 10 s ≈ **~1,2 Mo/jour** |

⇒ **Politique** : bascule en `.1` (**une seule génération**) dès que le journal atteint **5 Mo**,
**au pré-vol** de chaque lancement. Plafond disque **10 Mo**.
⚠️ **CE QUE CETTE POLITIQUE NE COUVRE PAS, ET ON LE DIT** : la rotation a lieu **au lancement**.
Un agent permanent qui tourne **des semaines sans redémarrer** peut dépasser le plafond — à
~1,2 Mo/jour, il atteint 5 Mo en **~4 jours**. ⛔ C'est **assumé**, ⛔ pas ignoré : l'agent redémarre
à chaque logon, et le débit mesuré dit de combien on dépasse si ce n'est pas le cas.

---

### 25.10 🔴 LE RÉSULTAT — **LA PRÉDICTION EST RATÉE, PAR LE BAS, AUX DEUX RANGS**

Tir du **2026-08-26**, agent **RÉEL** sur `COM3`, `--temoin`, **lancé par la tâche au logon**,
**WSL éteint**, 16 cœurs, SHA déposé **`f614b8f`**.
Capture brute : `mesures/dn4-17/AC5-AC6-constat-apres-logon.txt`.

| | prédit (committé `74c63db`, **avant** le tir) | **mesuré** | verdict |
|---|---|---:|---|
| % d'un cœur à **60 s** | `[2,20 ; 2,70]` | **2,057** | ❌ **HORS BANDE**, −0,143 pt sous la borne basse |
| % machine à **60 s** | `[0,1375 ; 0,1688]` | **0,1285** | ❌ hors bande |
| % d'un cœur à **180 s** | `[1,90 ; 2,30]` | **1,805** | ❌ **HORS BANDE**, −0,095 pt |
| % machine à **180 s** | `[0,1188 ; 0,1438]` | **0,1128** | ❌ hors bande |

🔴 **ET UN DÉFAUT DE LA PRÉDICTION ELLE-MÊME, QU'IL FAUT ÉCRIRE.** §25.3 ne nommait qu'**UNE**
réfutation : *« une valeur **> 2,70** signalerait un coût que le tableau n'a pas vu »*. **Le critère
de réfutation était UNILATÉRAL** — il ne disait rien d'un dépassement par le bas, et c'est
précisément ce qui est arrivé. ⛔ Une prédiction qui ne peut être démentie que d'un côté est une
demi-prédiction. *(Et §23.5 avait déjà noté le même biais de signe : « le raisonnement a vu juste
sur l'ordre de grandeur, ⛔ pas sur le signe ».)*

### 25.11 🔴 LA BAISSE EST À **TOUS LES RANGS** — troisième tir consécutif qui descend

> 🔴 **AMENDÉ PAR §25.17, LE MÊME JOUR.** Un tir de CONTRÔLE a été joué quelques heures plus
> tard, **même binaire, même méthode**, et il rend **+0,390 pt** au rang 60 s. ⇒ **La dispersion de
> l'instrument entre deux tirs du même jour est PLUS GRANDE que l'écart contre §23.** Le tableau
> ci-dessous reste exact ; ⛔ **sa lecture « l'agent descend » n'est PAS soutenue.**

| rang | §16.6 (`4c3a3f7`) | §23 (`9297fd4`) | 🆕 **`dn4-17` (`f614b8f`)** | Δ vs §23 |
|---|---:|---:|---:|---:|
| 10 s | 5,141 | 4,348 | **3,119** | −1,229 |
| 20 s | 3,586 | 3,431 | **2,263** | −1,168 |
| 30 s | 3,167 | 2,859 | **2,173** | −0,686 |
| 40 s | 2,810 | 2,692 | **2,147** | −0,545 |
| 50 s | 2,686 | 2,497 | **2,030** | −0,467 |
| **60 s** | 2,523 | 2,367 | **2,057** | **−0,310** |
| **180 s** | — | 2,065 | **1,805** | **−0,260** |

Série complète du tir : `3,119 · 2,263 · 2,173 · 2,147 · 2,030 · 2,057 · 1,964 · 1,894 · 1,874 ·
1,859 · 1,832 · 1,797 · 1,803 · 1,785 · 1,791 · 1,787 · 1,801 · 1,805 · 1,817` (rangs 10→190 s).
⚠️ **Elle a CONVERGÉ cette fois** : au-delà de 120 s elle oscille dans `[1,785 ; 1,817]`, soit une
bande de **0,032 pt**. §23 disait *« elle descend encore »* à 180 s.

⛔ **CE QUE CE TIR NE TRANCHE PAS, ET C'EST LE MÊME AVEU QU'EN §23.6** : un décalage à tous les
rangs s'explique aussi bien par un agent réellement moins cher que par une **charge de fond
différente**. ⛔ **Pas de témoin de contrôle.** La réserve « la tour n'est pas au repos contrôlé »
(§25.4-4) était écrite avant le tir ; elle tient, et elle suffit à expliquer l'écart.
⚠️ **Une piste NOMMÉE mais NON mesurée** : `LHM` a répondu en **8,1 ms de moyenne** ce jour-là,
contre **53,0 ms** en §23 et **24,1 ms** en §18.4. Le service est **6,5× plus rapide** qu'au tir de
référence. ⛔ **Ce n'est pas une explication** — la cadence est absolue (`prochain += PERIODE_S`),
donc une lecture plus rapide ne raccourcit pas le mural. C'est **un fait à côté du chiffre**, versé
tel quel.

### 25.12 ✅ LE RÉGIME EST **PROUVÉ**, ET IL EST **COMPARABLE** — les deux réserves qui comptaient sont levées

**AC6.6 — le process mesuré EST celui que la tâche a lancé, prouvé par la chaîne de PID :**

```
[0] PID=16344  python.exe   <- père 9492
      "…\Python313\python.exe" "H:\dev\projets\desknode\dn_agent.py" --serie COM3 --stop-si … --temoin
[1] PID=9492   cmd.exe      <- père 1516      ^^^ C'EST L'ENGINE DE LA TÂCHE
[2] PID=1516   svchost.exe  <- père 1144
EnginePID de la tâche = 9492
```

⇒ ⛔ **Ce n'est pas un agent lancé à la main depuis `H:` qu'on appellerait « le régime livré »** :
le `cmd.exe` père de `python.exe` **EST** le moteur de la tâche planifiée, `état=Running`,
`RunLevel=Limited`, `LastRunTime=2026-08-26 09:54:54`.

| réserve écrite **avant** le tir (§25.4) | ce que le tir en dit |
|---|---|
| **WSL doit être éteint** | ✅ `wsl -l --running` ⇒ *« Aucune distribution en cours d'exécution »* |
| 🔴 **LHM doit être vivant, sinon ⛔ non opposable à 2,367** | ✅ **LEVÉE** — `LHM : 1 processus`, `HTTP 200 (75 841 o)`, et le bilan dit **988 lectures réussies / 1 en échec**, moyenne **8,1 ms**. §23 avait 181 / 0. **Le chiffre EST opposable.** |
| ⚠️ **le firmware n'est pas le même et il PARLE** | ⚠️ **TIENT** — écho drainé **275,6 o/s · 5,21 lignes/s** sur 989 s. ⛔ §23 ne publie pas son propre débit d'écho : **la comparaison de ce poste-là est impossible**, et c'est une limite de la référence, pas de ce tir |
| ⚠️ la tour n'est pas au repos contrôlé | ⚠️ **TIENT** — et c'est l'explication la plus économique de la baisse à tous les rangs |

**Le bilan de fin du run mesuré** (989,0 s, arrêt propre par drapeau) :
`4 945 trames émises (5,00 trames/s) · 0 erreur d'envoi · 0 recalage de cadence · aucun refus
firmware · aucun écrêtage`. ⚠️ `1` lecture LHM à **606,4 ms** pour un plafond de 600 ms (101 %) —
incident déjà nommé en §18. Absences LHM : `cpu.degc=2 · fan.case_group=3 · fan.cpu_noctua=3 ·
fan.rear_out=3 · fan.top_out=3` sur 989 cycles.

### 25.13 🎯 LE VERDICT DU CRITÈRE N°4 — **LES DEUX MOITIÉS SONT COCHÉES**

| moitié du critère n°4 | verdict |
|---|---|
| *« l'agent démarre avec la session »* | ✅ **TENUE** — témoin par un **logoff/logon RÉEL**, ⛔ pas par `Start-ScheduledTask`. La case CPU est revenue **seule**, WSL éteint |
| *« < 1 % CPU »* (unité **% machine**, décision owner 2026-08-24) | ✅ **TENUE** — **0,1285 %** au rang 60 s (**7,8× de marge**), **0,1128 %** à 180 s (**8,9×**) |

⚠️ **La conséquence de §23.9 se réécrit avec le nouveau chiffre** : à `2,057 % d'un cœur`, le critère
tient **dès 3 cœurs logiques** (0,686 %) et **échouerait à 2** (1,03 %). **La tour en a 16.**

### 25.14 ⛔ CE TIR NE SOLDE **TOUJOURS PAS** L'ENTRÉE « +0,26 pt »

Rien n'a changé au raisonnement de §25.5 : **aucun A/B**, tour non au repos, et le régime a bougé
sur **quatre** axes à la fois. ⛔ **PAS D'A/B ⇒ PAS D'ATTRIBUTION.** L'entrée reste ouverte.
⚠️ **Et ce tir en RAJOUTE** : il montre une baisse de **−0,310 pt** au rang 60 s sans plus
d'explication que le +0,26 pt n'en avait. **Deux écarts non attribués, même méthode manquante.**

### 25.15 🔴 UN DÉFAUT TROUVÉ PAR **L'ŒIL DE L'OWNER**, qu'aucune gate ne voyait

Au logon, la tâche a ouvert **une fenêtre console visible**, et elle **y est restée** : relevé
`MainWindowHandle=65826` sur le `cmd.exe` de la tâche, **812 s après le logon**. L'action était
`cmd.exe /c "…dn-agent.bat" run …`, et Task Scheduler en `LogonType Interactive` **montre** cette
console. ⛔ Un agent **permanent** qui laisse une fenêtre ouverte 24 h/24 est un défaut du produit.
⚠️ **Aucun instrument de cette story ne pouvait le voir** : le compte de process, l'état du port et
la chaîne de PID sont tous **vrais** avec la fenêtre ouverte. C'est l'œil qui l'a trouvé.

✅ **CORRIGÉ ET PROUVÉ** : l'action passe par `powershell.exe -WindowStyle Hidden -File … tache`,
qui appelle le `.bat` — le quoting délicat reste **dans PowerShell**, et la console est cachée pour
**tout l'arbre**. Vérifié mécaniquement après re-pose :

```
[0] PID=20132  python.exe      MainWindowHandle=0
[1] PID=19324  cmd.exe         MainWindowHandle=0
[2] PID=24608  powershell.exe  MainWindowHandle=0
--- fenêtres console visibles dans la session : AUCUNE ---
```

⚠️ **CE QUE ÇA LAISSE OUVERT, ET ON LE DIT** : le chiffre de §25.10 a été pris avec **l'ancienne
action** (fenêtre visible). La chaîne gagne un maillon `powershell.exe` **inactif**, qui ⛔ **ne peut
pas** entrer dans un `psutil.Process()` mesurant l'agent **sur lui-même** — mais *« un chiffre ne se
transporte pas d'un régime à l'autre »*. ✅ **La vérification est GRATUITE et AUTOMATIQUE** :
`--temoin` est **permanent** dans le régime livré, donc **le prochain logon réécrit la série
entière** dans `dn-agent.log`. Il suffira de comparer **aux mêmes rangs**.

### 25.16 ✅ AC5.1 — **UN FLASH RÉEL, APRÈS LA POSE DE LA TÂCHE**

C'est le seul risque de régression que la story portait : *un agent qui redémarre seul tient `COM3`
et bloque le flash de `dn3-3`/`dn4-10`.* Joué **tâche posée ET agent vivant** :

| étape | mesure |
|---|---|
| `rendre-port.sh --vers-flash` | **8,5 s** — l'agent est arrêté **proprement** (bilan de 989 s écrit) et la carte passe à WSL |
| `esptool chip_id` depuis WSL | **1,03 s** — `MAC a0:f2:62:e3:d7:f4` |
| `verify_flash 0x10000` | 🎯 **`verify OK (digest matched)`** — la carte portait **exactement** `build/desknode.bin` |
| `write_flash 0x10000` | ✅ **1 144 160 o écrits**, 604 614 compressés, **5,8 s à 1 573,5 kbit/s**, *« Hash of data verified »* |
| `rendre-port.sh --vers-agent` | **7,1 s** — le port revient à l'agent |

🔴 **POURQUOI `esptool` ET ⛔ PAS `idf.py flash`** : `idf.py` **reconstruit** d'abord, et un rebuild
ré-embarque le SHA courant dans `App version` — ce qui **changerait le firmware de `dn3-3`** (dont
les mesures nomment `6144064`). Le `verify_flash` **préalable** prouve que les octets écrits sont
**ceux déjà en place** : le flash est réel et son effet sur la carte est **nul**.

⚠️ **UNE FRICTION MESURÉE, QUI PÈSE SUR LA FOURCHE DE §25.7** : `--after watchdog_reset` **fait
tomber l'attachement WSL** (la puce ré-énumère l'USB — `wsl-attach.sh` le documente). Il faut donc
**re-jouer `wsl-attach.sh` après chaque esptool**. ⛔ **La branche Windows-only n'a pas ce coût** :
le même reset côté Windows a rendu `COM3` tout seul. ⚠️ Et les deux `esptool` **ne sont pas la même
version** : **v4.12.0** dans WSL (ESP-IDF 5.5) contre **v5.3.1** côté Windows.


---

### 25.17 🔴 LE TIR DE CONTRÔLE RENVERSE LA LECTURE — **l'écart contre §23 est DANS LE BRUIT DE L'INSTRUMENT**

§25.11 disait, comme §23.6 avant lui : *« ⛔ pas de témoin de contrôle »*. **Il y en a un
maintenant**, et il a été joué **le même jour**, sur **le même binaire déposé** (`f614b8f`), avec la
**même méthode** (agent réel, `COM3`, `--temoin`, tâche planifiée, cumul rapporté au mural).
La seule chose qui change entre les deux, c'est **l'état de la tour** : le tir de régime a eu lieu
**juste après le logon, WSL éteint, rien d'autre en marche** ; le contrôle pendant une **session de
travail active** (WSL, éditeur, agent de dev).

| rang | tir de RÉGIME (logon, tour au calme) | tir de CONTRÔLE (même jour, tour occupée) | **Δ** |
|---|---:|---:|---:|
| 60 s | **2,057** | **2,447** | **+0,390** |
| 180 s | **1,805** | **2,144** | **+0,339** |

**Mis en regard des écarts qu'on interprétait :**

| écart | valeur | ce qu'on en disait |
|---|---:|---|
| `dn4-17` − §23, rang 60 s | **−0,310** | « la baisse est à tous les rangs » |
| `dn4-17` − §23, rang 180 s | **−0,260** | idem |
| 🔴 **dispersion du MÊME jour, rang 60 s** | **+0,390** | — |
| 🔴 **dispersion du MÊME jour, rang 180 s** | **+0,339** | — |

🎯 **CONCLUSION, ET ELLE PORTE SUR TROIS TIRS EN ARRIÈRE** : **la dispersion de l'instrument est
PLUS GRANDE que tous les Δ inter-sessions que ce dossier a publiés.** ⇒ ⛔ **Aucun des trois écarts
(§16.6 → §23 → `dn4-17`) ne peut être lu comme « l'agent a changé de coût ».** Ils sont compatibles
avec **un seul et même agent** mesuré sur **une tour dont la charge n'est pas contrôlée** — ce que
les deux dossiers écrivaient déjà en réserve, **sans jamais pouvoir le chiffrer**.
✅ **§23.6 avait posé la bonne question** (*« un décalage uniforme s'explique aussi bien par une
charge de fond différente »*) et concluait quand même à *« l'hypothèse est RÉFUTÉE »*. **Avec ce
chiffre, ⛔ cette réfutation-là ne tient plus non plus** : elle reposait sur un Δ plus petit que le
bruit.

⚠️ **ET ÇA CHANGE LA LECTURE DE MA PROPRE PRÉDICTION.** Le tir de contrôle, à **2,447**, tombe
**DANS** la bande `[2,20 ; 2,70]` de §25.3. ⇒ **La prédiction n'était pas fausse sur l'agent : elle
était fausse sur la TOUR.** ⛔ Ça ne la sauve pas — une prédiction qui ne dit pas dans quel état de
charge elle vaut n'est pas tranchable — mais ça nomme **ce qu'il faut réparer dans la méthode**, et
ce n'est pas le code de l'agent.

🔴 **CE QUE ÇA IMPOSE AU PROCHAIN QUI PUBLIERA UN COÛT D'AGENT** :
1. ⛔ **Ne plus publier un Δ inter-session sous ~0,4 pt** au rang 60 s comme s'il signifiait quelque
   chose. **La résolution de la méthode est de cet ordre**, elle est maintenant **mesurée**.
2. ✅ **Un tir SE DOUBLE d'un contrôle** joué dans un état de charge différent, ⛔ pas d'une réserve
   écrite en prose. Le coût est de trois minutes.
3. ✅ **Le tir de régime se prend juste après le logon**, tour au calme : c'est le seul état
   **reproductible** de cette machine, et c'est aussi **le régime réel** de l'agent permanent.
4. ⛔ **L'entrée « +0,26 pt » du ledger est, elle aussi, sous ce bruit.** ⚠️ Ça ne la solde toujours
   pas — *« pas d'A/B ⇒ pas d'attribution »* — mais ça **change ce qu'il faut faire** : ⛔ ce n'est
   pas un A/B avant/après commit qu'il faut, c'est un A/B **à charge de tour contrôlée**, et il faut
   **n > 1 par branche**.

⚠️ **CE QUE CE CONTRÔLE NE DIT PAS** : il **ne mesure pas** l'effet du correctif de fenêtre de
§25.15 (le contrôle porte la nouvelle action, le tir de régime l'ancienne). **Deux variables ont
bougé ensemble** — la fenêtre ET la charge. ⛔ Il ne prouve donc **rien** sur la fenêtre ; il prouve
que **la charge domine**. La vérification du correctif reste **gratuite et automatique** au prochain
logon (§25.15).

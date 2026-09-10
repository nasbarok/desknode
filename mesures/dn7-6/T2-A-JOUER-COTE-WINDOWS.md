> 🔴 **CE RELEVÉ N'A PAS ÉTÉ JOUÉ, ET C'EST ÉCRIT EN PREMIÈRE LIGNE PLUTÔT QUE DÉCOUVERT
> PLUS BAS.** Ce fichier est un **protocole**, ⛔ pas une mesure. Il est resté vide parce que
> **WSL ne peut pas le jouer** : le WSL de la tour est en NAT, `localhost` ne traverse pas,
> donc la page n'est pas servie en **contexte sécurisé** et l'accès série du navigateur est
> **bloqué**. ⇒ tout ce qui suit se joue **CÔTÉ WINDOWS**, à la main, et son porteur est
> **nommé au ledger**.

# `dn7-6` / T2 — le protocole côté Windows

**Ce que la mesure mécanique ⛔ NE FERME PAS.** `tools/verif_preconditions_dn76.py` est
**structurelle** : elle ⛔ n'ouvre aucun navigateur, ⛔ n'installe rien, ⛔ ne pose aucune
tâche planifiée et ⛔ ne regarde aucune pastille. Elle prouve que **le mécanisme est branché**.
Trois choses restent, et elles vivent ici.

---

## 1. Tout est là — la ligne de référence

**Geste** : double-cliquer `installeur/DeskNode-installeur.bat`, sur une tour où les deux
modules Python **et** LibreHardwareMonitor sont présents.

**Attendu** :

- les **quatre** étapes du workflow portent le témoin **« prête »** ;
- ⛔ **aucun** bouton n'est grisé par une précondition ;
- *« Activer l'agent »*, en section 4, est **armé** ;
- les deux bandeaux de précondition (dépendances, LibreHardwareMonitor) sont **absents**.

**À relever** : une capture de la page entière, et la réponse de l'owner à la question 4.

---

## 2. Une dépendance retirée — et le flash qui ⛔ **reste** utilisable

**Geste** : `pip uninstall psutil` dans l'interpréteur que la page utilise, puis relancer le
`.bat`.

**Attendu** :

- l'étape de l'agent est **grisée**, et **la raison est écrite SOUS le bouton** — elle nomme
  le module manquant **et** le geste de réparation ;
- le bouton *« Installer les dépendances de l'agent »* est **armé**, en tête de page ;
- 🔴 **le bouton de flash ⛔ RESTE UTILISABLE** — c'est la ligne de partage, et elle n'est
  ⛔ pas intuitive. Poser le firmware ⛔ n'a rien à voir avec l'agent.

**Puis cliquer** *« Installer les dépendances de l'agent »*.

**Attendu** :

- le bouton se **désarme pendant le geste** ;
- la sortie s'affiche **SOUS LUI** (place mobile de `dn7-4`), ⛔ pas quatre gestes plus bas ;
- **`rc` et sortie rendus tels quels** ;
- puis les témoins bougent **SANS RECHARGEMENT**, et *« Activer l'agent »* s'arme.

⚠️ **À relever aussi** : le **temps** que le geste a pris. Le plafond est de 900 s, il est
**explicite** dans le serveur, et ⛔ il n'a **jamais été confronté à une mesure**.

---

## 3. `pip` indisponible — le verdict explicite

**Geste** : servir la page avec un interpréteur **sans `pip`**, puis cliquer le même bouton.

**Attendu** : un verdict qui **dit** que `pip` n'est pas disponible, que le geste **n'a pas eu
lieu**, et qu'il **redevient un geste à recopier**. ⛔ Jamais un succès annoncé, ⛔ jamais une
trace nue.

---

## 4. LibreHardwareMonitor arrêté

**Geste** : arrêter le service LibreHardwareMonitor, puis relancer le `.bat`.

**Attendu** :

- l'activation de l'agent est **grisée**, et le motif dit que **le pré-vol refuserait**, avec
  son propre code de sortie ;
- la commande de LibreHardwareMonitor est **à recopier**, et ⛔ **aucun bouton ne l'exécute** ;
- **le motif de cette absence est écrit à côté** — le geste exige des droits que cet
  installeur ⛔ ne demande jamais ;
- ⛔ le bouton de flash **reste utilisable**.

---

## 5. Activer / désactiver, dans les deux sens — 🔴 **c'est l'instrument qui ferme `AC7.6.4`**

**Geste** : cliquer *« Activer l'agent »*.

**Attendu**, et ⛔ **pas déduit du message** :

```powershell
Get-ScheduledTask -TaskName 'DeskNode agent' | Format-List TaskName, State
(Get-ScheduledTask -TaskName 'DeskNode agent').Principal.RunLevel   # attendu : Limited
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'dn_agent\.py' } |
  Select-Object ProcessId, CommandLine
```

- la tâche est **redemandée au système** et elle existe ;
- son niveau d'exécution est **`Limited`** — c'est ce qui tient *« rien de `dn7` n'exige de
  droits administrateur »* ;
- le processus de l'agent est **constaté vivant**, par requête ;
- le code de retour rendu par la page est **`0`**.

**Puis cliquer** *« Retirer l'agent »*, et **vérifier la disparition par requête** (la même
première commande, qui ne doit plus rien rendre).

⚠️ **Et le demi-succès, si l'occasion se présente** : tâche posée **et vérifiée**, aucun agent
vivant 10 s après ⇒ la page doit relayer **`13`**, et le message doit dire **la moitié qui a
réussi**. ⛔ Ni un succès, ni un échec total : les deux seraient faux.

---

## 6. 🔴 À L'ŒIL DE L'OWNER — **la seule question que la mesure ne tranche pas**

> **Les quatre témoins sont-ils lisibles, dans leurs trois positions, SANS LE VERT ?**

L'owner a demandé des *« pastilles vertes »*. Le témoin est ⛔ **délibérément pas vert**, et
l'écart est **écrit, daté et porté** : `installeur/IDENTITE.md` (annotation du 2026-09-10),
`installeur/index.html` (bloc de style), et `AC7.6.1` de la story. Trois mesures le
commandent — l'identité est une **liste fermée de sept rôles relevés dans le firmware** et
aucun n'est vert ; le vert `0x4ade80` **a été essayé sur le produit et abandonné** sur constat
owner à l'œil ; et `dn7-4` a déjà tranché **sur cette page** que l'aplat est une différence de
**forme**, ⛔ pas de teinte.

⇒ **C'est cette observation-ci qui décide du porteur d'`AC7.6.1`** :

- si la forme suffit à l'œil ⇒ l'écart se **ferme** tel quel ;
- si elle ne suffit pas ⇒ le porteur est **un arbitrage owner qui amende `IDENTITE.md` avec
  une source firmware VIVANTE**. ⛔ Pas une couleur inventée dans la page : ce serait casser
  la règle que ce fichier existe pour tenir.

---

## Ce que ce protocole ⛔ **ne demande pas**

⛔ De jouer quoi que ce soit **depuis WSL**. Le NAT rend `localhost` inatteignable, le
navigateur refuse l'accès série **sans le dire**, et un relevé pris là serait faux **sans que
rien ne rougisse**.

# dn7-5 / `T2-b` — ⛔ **CE FICHIER N'EST PAS UNE MESURE. C'EST LE PROTOCOLE.**

🔴 **RIEN CI-DESSOUS N'A ÉTÉ JOUÉ.** Ce fichier existe pour que l'instrument qui ferme
`AC7.5.3` soit **écrit** plutôt que promis — ⛔ pas pour laisser croire qu'il a tourné.
Tant qu'aucun relevé ne le remplace, `AC7.5.3` est **OUVERTE**, et le report du ledger
(`[dn7-5 2026-09-10] PORTÉE`) est **vivant**.

⚠️ **POURQUOI ÇA NE PEUT PAS SE JOUER D'ICI.** Le WSL de la tour est en **NAT** : `localhost`
⛔ **ne traverse pas**. Une page servie sur la boucle locale de WSL n'est pas la page que le
navigateur Windows ouvrirait, et une tâche planifiée Windows n'existe pas dans WSL.
⇒ **tout ce qui suit se tape CÔTÉ WINDOWS**, dans une invite `cmd` ou PowerShell **non
élevée**, depuis la copie déployée du dépôt.

⚠️ **CE QUI EST DÉJÀ MESURÉ, ET QU'IL EST INUTILE DE REJOUER** : la sonde à trois positions et
le fait que le chemin de mesures tranche — voir `T2-a-wsl-prevol-et-trois-positions.txt`. Ce
qui manque est **la tour**, ⛔ pas le mécanisme.

---

## `T2-b-1` — LHM **DEBOUT** : la page le dit, et rien d'autre ne change

```
.\tools\dn_lhm_tour.ps1
```
⇒ relever son code de sortie (**`0`** = prêt, **`1`** sinon). ⛔ Ne pas continuer sur `1` :
la suite mesurerait un LHM absent en croyant mesurer un LHM debout.

```
installeur\DeskNode-installeur.bat
```

**À relever, ⛔ pas à déduire :**
- la ligne `LibreHardwareMonitor` du pré-vol dans la console ⇒ attendu **`present`** ;
- le **code de sortie** du pré-vol ⇒ 🔴 **attendu : `0`.** C'est **la valeur de référence de
  tout ce protocole**, et elle est écrite plutôt que laissée à « inchangé » : sur une tour où
  `psutil` **et** `pyserial` sont installés et où la charge est complète, `prevol()` ⛔ n'a
  aucune raison de rendre autre chose. ⚠️ Le seul chiffre déjà capturé — `rc=6` dans
  `T2-a` — est un **artefact WSL** (`psutil` manque sur ce Python-là) et ⛔ **ne sert pas** de
  référence ici. Si la tour rend `6`, c'est qu'il manque un module Python, ⛔ **pas** LHM :
  relever lequel avant d'aller plus loin ;
- **sur la page servie**, la ligne `LibreHardwareMonitor` de la section *« Ce que vous devez
  installer vous-même »* ⇒ attendu **`présente`** ;
- une **capture d'écran** de cette ligne. 🔴 C'est **l'œil de l'owner** qui ferme la lisibilité,
  ⛔ aucune vérification de ce dépôt.

## `T2-b-2` — LHM **ARRÊTÉ** : la page le dit avec **son** geste, et elle s'ouvre quand même

Arrêter LibreHardwareMonitor (le fermer depuis sa zone de notification suffit ; ⛔ inutile de le
désinstaller), puis :

```
installeur\DeskNode-installeur.bat
```

**À relever :**
- la ligne du pré-vol ⇒ attendu **`ABSENT`**, suivie du bloc `ECART DECLARE (2)` qui nomme
  **`tools\dn_lhm_tour.ps1 -Poser`** — ⛔ **pas** `pip` ;
- le **code de sortie** du pré-vol ⇒ attendu **`0`**, c'est-à-dire **le même** qu'en `T2-b-1`.
  🔴 **Si ce code a bougé, c'est un défaut** : LHM ⛔ ne doit **pas** entrer dans la liste des
  modules manquants — c'est cette liste qui commande **à la fois** le `6` **et** le bloc qui
  publie la commande `pip` ;
- **la page s'ouvre quand même** ⇒ attendu **oui** ;
- **le bouton de flash reste utilisable** ⇒ attendu **oui**. ⛔ Ne pas déduire ça de l'apparence :
  le vérifier en survolant/cliquant, carte branchée.
- la ligne LHM de la page ⇒ attendu **`ABSENT — voir le geste ci-dessous`**.

### La **troisième** position, si elle est atteignable

Servir la page depuis une copie du dossier `installeur/` **sortie de son dépôt** (l'arbre parent
absent ⇒ `agent/dn_agent.py` illisible) ⇒ attendu **`non testable ici — ⛔ ce n'est PAS
« absent »`**. ⚠️ Si cette copie n'est pas faite, l'écrire **ici**, plutôt que laisser croire que
la position a été vue.

## `T2-b-3` — 🔴 **LE REFUS, DANS LES DEUX SENS — C'EST LUI QUI FERME `AC7.5.3`**

**(a) avec LHM debout** — le relancer, vérifier `.\tools\dn_lhm_tour.ps1` ⇒ `0`, puis :

```
tools\dn-agent.bat run
tools\dn-agent.bat etat
```
⇒ attendu : **l'agent démarre**, et `etat` **nomme son PID**. Relever le PID.

**(b) sans LHM** — arrêter LibreHardwareMonitor, arrêter l'agent (`tools\dn-agent.bat stop`),
puis :

```
tools\dn-agent.bat run
echo %ERRORLEVEL%
tools\dn-agent.bat etat
```

**À relever, et ⛔ dans cet ordre :**
1. le message ⇒ attendu : il **nomme** LibreHardwareMonitor, **son geste**, et **ce qui tombe
   sans lui** ;
2. `%ERRORLEVEL%` ⇒ attendu **`12`**. ⛔ **Pas `4`** : `4` porte deux sens selon le verbe et
   `lancer` le neutralise en `0` — s'il sort `4`, l'agent aurait démarré ;
3. 🔴 **`tools\dn-agent.bat etat` ⇒ attendu : AUCUN agent vivant.**
   ⛔ **C'est cette troisième ligne qui ferme l'AC, ⛔ pas le message.** Un message de refus
   ⛔ ne prouve **pas** qu'aucun processus n'a été créé — ce dépôt a déjà payé ce raccourci
   (*« un process qu'on croit mort peut tenir COM3 »*, en tête de `dn_agent_tour.ps1`).

**(c) la reprise, si elle est observable** — reposer la permanence, redémarrer la session avec
LHM en démarrage automatique, et relever si l'agent est là après le logon. ⚠️ **La borne écrite
est de 3 reprises à 1 minute** : au-delà d'environ **trois minutes**, l'agent est **absent toute
la session**. Si ce cas n'est pas joué, l'écrire ici — c'est un **risque connu**, ⛔ pas un fait
mesuré.

---

## Comment ce fichier cesse d'être un protocole

Le remplacer par le **relevé brut** (sorties collées, codes de retour, captures), en gardant
**ce qui a été joué** et **ce qui ne l'a pas été** — ⛔ pas seulement ce qui a réussi. Puis
solder le report du ledger et porter `dn7-5` à son état.

──────────────────────────────────────────────────────────────────────────────
🔴 ANNOTE LE 2026-09-12 PAR `dn8-3` — ⛔ AUCUNE LIGNE CI-DESSUS N'EST EFFACEE,
   ET CE PROTOCOLE N'A **TOUJOURS PAS** ETE JOUE.
──────────────────────────────────────────────────────────────────────────────
⛔ CE QUI N'A PAS CHANGE : l'instrument reste **L'ŒIL DE L'OWNER**, sur la page
   SERVIE, cote Windows. ⛔ Aucune gate de ce depot ne rend ce verdict-la, et
   une gate qui pretendrait le faire serait pire qu'aucune gate.

🔴 CE QUI A CHANGE, ET QUI RACCOURCIT LA SEANCE — TROIS FAITS MESURES :

  (1) ⚠️ **LA PREMISSE DE NAT EST REFUTEE** (M6, 2026-09-12). *« le WSL de la
      tour est en NAT ⇒ localhost ne traverse pas »* est **FAUX comme enonce
      de JOIGNABILITE** : un serveur lie DANS WSL repond **200** a un
      `Invoke-WebRequest` venu de Windows, sur `127.0.0.1` ET sur `0.0.0.0`.
      ⛔ **ET CA NE FERME RIEN ICI** : ce qui est mesure est un CLIENT HTTP,
      ⛔ pas un NAVIGATEUR, et ⛔ surtout pas un ŒIL. Le contexte securise, Web
      Serial et la LISIBILITE restent **entiers et non mesures**.

  (2) 🔴 **LE DEPLOIEMENT DE LA TOUR EST PERIME — A CORRIGER *AVANT* LA SEANCE.**
      `/mnt/h/dev/projets/desknode/PROVENANCE.txt` ⇒ `HEAD = e3064f0`, depose le
      **2026-08-28** ; le depot est a `0fa214d`. `exit 12` et `PREREQUIS DUR`
      comptent **ZERO occurrence** dans le `dn_agent_tour.ps1` DEPLOYE.
      ⇒ jouer ce protocole sur la tour TELLE QUELLE mesurerait un produit
        **d'il y a deux semaines**, et le refus ⛔ **n'y serait pas** : un
        ⛔ **FAUX NEGATIF que ⛔ RIEN ne signalerait**.
      ⇒ **LE GESTE, EN PREMIER** :  ~/projects/desknode/tools/deployer_tour.sh
         puis RELIRE `PROVENANCE.txt` et verifier qu'il annonce le HEAD du jour.

  (3) ✅ **CE QUI EST DESORMAIS MECANISE, ET QU'IL EST INUTILE DE REJOUER A LA
      MAIN** : la **POLARITE** de la sonde LHM est rejouee dans un **vrai
      `powershell.exe`**, dans les DEUX sens, par
      `tools/verif_lhm_ps_dn83.py` — mesure du 2026-09-12 : LHM qui repond
      **sans une seule ligne `lhm_`** ⇒ **exit 12** ; LHM debout ⇒ ⛔ **pas 12**.
      ⛔ CE QUE CA ⛔ NE REMPLACE PAS : la TOUR REELLE, sa TACHE PLANIFIEE et la
      COURSE AU LOGON. Le banc ⛔ n'installe pas LHM, ⛔ ne pose aucune tache,
      ⛔ n'ouvre aucun navigateur.

⚠️ **CE QUI EST ALLEGE DANS CE PROTOCOLE** : `T2-b-3`, *« le refus, dans les
   deux sens »*, est **MECANISE** pour sa moitie POLARITE. Ce qu'il reste a
   constater sur la tour est ce qu'⛔ aucun banc ne peut produire :
     · que `dn-agent.bat etat` ne trouve **AUCUN agent vivant** apres le refus
       — ⛔ c'est cette ligne-la qui ferme l'AC, ⛔ pas le message ;
     · la **reprise au logon** (`(c)`), sa borne de ~3 minutes, jamais observee.

🆕 **ET LE PORT DE LHM SE PASSE MAINTENANT** (`dn8-3`) : si LHM ecoute ailleurs,
   ⛔ **ne plus aligner la constante du produit** —
       tools\dn-agent.bat run COM3 0 "" 127.0.0.1:<port>
   L'adresse traverse jusqu'a l'agent. ⚠️ La 4e place (le temoin) doit etre
   OCCUPEE : `""` si pas de temoin, sinon `cmd.exe` lit l'adresse en `%4`.

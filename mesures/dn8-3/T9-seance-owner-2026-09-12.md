# `dn8-3` / T9 — LA SEANCE OWNER DU 2026-09-12, SUR LA PAGE **SERVIE**

> 🔴 **CE FICHIER EST UNE MESURE, ⛔ PAS UN PROTOCOLE.** L'instrument est **l'ŒIL DE
> L'OWNER**, et c'est declare. Les observations sont rapportees **telles qu'elles ont ete
> faites**, ⛔ pas resumees.
> **Date** : 2026-09-12 · **Produit mesure** : la tour REDEPLOYEE a `d33166d` le meme jour
> a 14:40:44 — ⛔ pas la copie perimee du 2026-08-28.

## Ce qui rendait cette seance possible, et qui ne l'etait pas ce matin

`mesures/dn8-3/T4-refus-cote-tour.txt` avait mesure que la tour portait `e3064f0`
(2026-08-28) avec **ZERO** occurrence de `exit 12`. ⇒ une seance jouee avant redeploiement
aurait mesure un produit d'il y a deux semaines. **Le redeploiement a eu lieu d'abord** :
les 5 fichiers identiques, `PROVENANCE.txt` a jour, `exit 12` x3 et `-Lhm` x2 presents.
Pre-vol depuis le partage WSL : **`ERRORLEVEL=0`**, charge **intacte (CRC32 verifie)**,
`psutil` / `pyserial` / **LibreHardwareMonitor presents**. `dn_lhm_tour.ps1` : **rc=0**.

---

## Geste C — 🔴 **POSITION ACTIVE : RELEVEE**   (ferme `AC7.4.3`)

**Question posee** : les **deux** selecteurs de langue — celui de la page en tete, celui de
la dalle a l'etape 3 — montrent-ils leur position active **REMPLIE**, lisible **sans
survoler et sans comparer** ?

**REPONSE DE L'OWNER, VERBATIM** : *« position active oik »* ⇒ **OUI**.

⇒ **C'EST L'INSTRUMENT QUI FERMAIT `AC7.4.3`, ET IL A RENDU SON VERDICT.** Le defaut que
`dn7-4` avait mesure — les deux regles d'etat portant **rigoureusement** les declarations de
`button:hover:enabled`, donc « selectionne » et « survole » **indiscernables** — est
**resolu a l'œil sur la page servie**, et ⛔ pas seulement garde par `verif_placement_dn74.py`.

## Geste A — le verdict d'un verbe s'ecrit **SOUS LE BOUTON**   (ferme la moitie a l'ŒIL d'`AC7.4.1`)

**REPONSE DE L'OWNER** : *« arreter l'agent ok ! »* puis *« retirer l'agent ok ! »*, avec le
bloc de verdict de la page colle. ⚠️ La page **affiche la commande qu'elle lance**
(`installeur/index.html:2068`, `"$ " + d.commande`) : le collage est donc bien **la sortie de
la page**, ⛔ pas un tir en terminal.

Verdict rendu sous « Arreter l'agent et rendre le port » :

    === STOP ===
      aucun agent reconnu.
    === PREUVE : ON RE-OUVRE LE PORT ===
      python.exe vivants : 2  (portant dn_agent.py : 0 | CommandLine ILLISIBLE : 0)
      port COM3 : libre
      usbipd : 3-5 303a:1001 Peripherique serie USB (COM3) ... Shared
      marqueur : absent
      OK - COM3 se REOUVRE : le port est rendu.
    code de retour : 0  - rendu par l'outil
    le port a ete REOUVERT apres l'arret : il est rendu. C'est l'ouverture qui fait foi,
    PAS le code de retour.

⚠️ **CE QUE CE TIR N'EXERCE PAS, ET C'EST DIT** : « aucun agent reconnu » parce que l'agent
avait deja ete arrete ~20 min plus tot, au redeploiement. ⇒ ce geste exerce **LA PLACE DU
VERDICT**, ⛔ pas un arret reel. La preuve du port, elle, est jouee : COM3 se rouvre.

Verdict rendu sous « Retirer l'agent », en section 4 :

    $ powershell -NoProfile -ExecutionPolicy Bypass -File H:\dev\projets\desknode\dn_agent_tour.ps1 retirer -Serie COM3
    === RETRAIT DE LA TACHE ===
      tache 'DeskNode agent' ABSENTE - retrait verifie.
      /!\ L'AGENT N'EST PLUS LA APRES LE RETRAIT.
      /!\   Le Planificateur a termine l'arbre d'action de la tache : le bilan
      /!\   de fin est PERDU (TerminateProcess, aucun --stop-si lu).
      /!\   => la prochaine fois, jouer 'dn-agent.bat stop' AVANT 'retirer'.
    code de retour : 0  - rendu par l'outil
    la tache << DeskNode agent >> est ABSENTE - re-interrogee apres coup.

🔴 **LA COMMANDE CITEE NOMME `H:\dev\projets\desknode\dn_agent_tour.ps1`** — la copie
**REDEPLOYEE**. La seance a donc tourne contre le produit neuf, ⛔ pas le perime.
✅ Et la tache est **RE-INTERROGEE APRES COUP**, ⛔ pas deduite du message : c'est la
propriete que `dn7-5` avait posee.

## Geste B — le selecteur **ANNULE** dit le fait exact   (ferme le residu d'`AC7.4.2`)

**REPONSE DE L'OWNER** : *« 3 oui »*, avec le texte rendu par la page :

    Aucun port n'a ete choisi.
    Le selecteur a ete ferme sans selectionner la ligne. Rien n'est ouvert, et rien n'a ete
    lu. Recliquez le bouton, puis cliquez la ligne avant de valider.
    (NotFoundError: Failed to execute 'requestPort' on 'Serial': No port selected by the user.)
    Cette page ne tient PAS le port serie - rien de notre fait ne le retient.

⇒ **C'EST LE MESSAGE NEUF, MOT POUR MOT**, et ⛔ **PAS** l'ancienne supposition *« le plus
souvent, un selecteur est deja ouvert »*. Le domaine de `langue.port-indisponible` a bien
**RETRECI** au seul cas ou sa phrase est vraie, comme `AC7.4.2` le demandait.

---

## ⛔ CE QUE CETTE SEANCE NE FERME PAS

- **`AC8.3.3`** reste **BLOQUEE** : le bouton reellement grise, « Activer l'agent » constate
  **vivant par requete**, le geste `pip` **et son temps** (plafond **900 s**, toujours
  ⛔ jamais confronte a une mesure), le verdict de `pip` indisponible, et **la course au
  logon**. Protocole : `mesures/dn7-6/T2-A-JOUER-COTE-WINDOWS.md`.
- **`AC7.5.3`** — le refus cote tour dans les deux sens (`mesures/dn7-5/T2-b-3`) ⛔ n'a pas
  ete joue. Il est desormais **jouable** : le refus est deploye.

## ⚠️ DEUX FAITS D'ETAT LAISSES SUR LA MACHINE

1. 🔴 **LA TACHE AU LOGON EST RETIREE.** Le geste « Retirer l'agent » l'a supprimee, et le
   retrait est **verifie**. ⇒ **l'agent ⛔ ne redemarrera PAS au prochain logon** tant que la
   permanence n'est pas reposee : `dn-agent.bat permanence`, ou le bouton de la page.
2. L'agent **ne tourne pas**. Pour le relancer : `H:\dev\projets\desknode\dn-agent.bat start`.

---

## ✅ SUITE DE SEANCE — « ACTIVER L'AGENT »   (releve `AC8.3.3` **(b)**, ⛔ pas le reste)

**REPONSE DE L'OWNER, VERBATIM** : *« ok activé l'agent nickel ca met bien les info sur la
dalle en 2-3 sec »*.

⚠️ **CE QUE CETTE PHRASE PROUVE, ET CE QU'ELLE NE PROUVE PAS.** La dalle qui se remplit en
2-3 s etablit que l'agent **tourne et publie de bout en bout** — c'est fort, et ⛔ ce n'est
PAS ce que l'AC demande. `AC8.3.3` (b) exige la tache **et** un agent **CONSTATE VIVANT PAR
REQUETE**, en `-RunLevel Limited` : *« attendu, et ⛔ pas deduit du message »*. Les trois
requetes du protocole `dn7-6` §5 ont donc ete jouees.

**(1) LA TACHE, RE-DEMANDEE AU SYSTEME**

    tache     : PRESENTE
    State     : Ready
    RunLevel  : Limited          <= ATTENDU
    action    : powershell.exe
    arguments : -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden
                -File "H:\dev\projets\desknode\dn_agent_tour.ps1" tache -Serie COM3 -Duree 0

🔴 **`RunLevel = Limited` EST LE POINT** : c'est lui qui tient *« rien de `dn7` n'exige de
droits administrateur »*, et l'outil traite un autre niveau comme un DEFAUT.
✅ **L'ACTION NOMME LA COPIE REDEPLOYEE** (`H:\dev\projets\desknode\dn_agent_tour.ps1`).
✅ **ET ELLE DIT CE QUI A ETE CLIQUE** : la tache EXISTE, donc c'est le verbe **de la page**
   (« Activer l'agent », qui COMPOSE permanence + demarrage), ⛔ pas `dn-agent.bat start`,
   qui ⛔ n'en pose aucune.

**(2) L'AGENT, CONSTATE VIVANT PAR REQUETE**

    agents vivants : 1   (requete OK : True)
      PID=24956   C:\Users\naoua\AppData\Local\Programs\Python\...

⚠️ **LE `(requete OK : True)` N'EST PAS DECORATIF** : cette marche a deja publie un
« agents vivants : 0 » qui etait un **FAUX ZERO** rendu par une commande EN ERREUR. Un
compte se relit **A COTE DU CODE DE RETOUR**, ⛔ jamais seul. Ici la requete reussit.

**(3) LE PORT SERIE**

    COM3 : TENU   (⇒ coherent avec un agent qui publie)

⚠️ **UN CONSTAT AU PASSAGE, ⛔ PAS UN DEFAUT** : la tache est posee **SANS `-Temoin`** (et
sans `-Lhm`). Le verbe `etat` de l'outil AVERTIT sur ce cas : l'agent lance par la tache
⛔ n'aura PAS l'instrument de cout, donc la re-verification « gratuite au prochain logon »
⛔ n'aura pas lieu. C'est le comportement du verbe de la page, ⛔ pas une regression.

## ⛔ CE QUE CETTE SUITE NE FERME **TOUJOURS** PAS — `AC8.3.3` RESTE BLOQUEE

Sur les cinq points de l'AC, **UN** est releve. Restent :

- *(a)* qu'un bouton soit **REELLEMENT GRISE** sous les yeux de quelqu'un — il faut RETIRER
  une dependance (`pip uninstall psutil`) pour le voir se griser, avec sa raison **sous le
  bouton** ; et le bouton de **flash doit RESTER utilisable** (c'est la ligne de partage, et
  elle ⛔ n'est pas intuitive) ;
- *(c)* que le geste `pip` aboutisse, **ET EN COMBIEN DE TEMPS** — le plafond de **900 s** est
  explicite dans le serveur et ⛔ **n'a jamais ete confronte a une mesure** ;
- *(d)* que le verdict de **`pip` indisponible** sorte (⛔ ni succes annonce, ⛔ ni trace nue) ;
- *(e)* **LA COURSE AU LOGON** : tache LHM `AtLogOn` **elevee**, tache agent `AtLogOn` **non
  elevee**, meme evenement. Parade : **3 reprises a 1 minute**, borne **~3 min**, et ⛔ personne
  ne l'a observee sur une **vraie ouverture de session**. ⚠️ RISQUE CONNU, ⛔ pas un fait mesure.
  ⇒ C'est le seul point que la tache **qui vient d'etre posee** rend enfin observable : il
    suffit d'un redemarrage, puis de rejouer ces trois requetes **sans rien lancer a la main**.

---

## 🔴 LA COURSE AU LOGON EST **MESUREE** — ET LA PARADE **N'A PAS TIRE**

> **PARADE NON TIREE** · redemarrage owner du 2026-09-12 · c'est la **PREMIERE**
> observation de cette course sur une **vraie ouverture de session**. Elle etait
> jusqu'ici un **RISQUE ECRIT**, ⛔ pas un fait.

**CONSTAT OWNER, VERBATIM** : *« tour redemmarré la dalle ne se rempli pas »*.

### Ce qui est mesure, horodate

    demarrage de la tour        18:12:58
    tache 'DeskNode agent' tire 18:13:13   (15 s apres le boot)
      -> LastTaskResult         = 12       <= LE REFUS LHM, exit 12
    process LHM demarre         18:13:34   (21 s APRES le tir de la tache agent)
    agents vivants              0
    COM3                        LIBRE
    /metrics (au constat)       HTTP 200, corps porteur de lignes lhm_

⇒ **LE PRE-VOL A SONDE LHM AVANT QU'IL NE SOIT DEBOUT, ET IL A REFUSE.** Le refus
est **juste** — c'est le prerequis dur voulu par l'arbitrage owner du 2026-09-10.
La machine, elle, etait **SAINE** : LHM est monte 21 s plus tard.

### 🔴 CE QUI COMPTE DAVANTAGE : LA PARADE EXISTE, ET ELLE N'A RIEN RATTRAPE

La tache porte bien ce que `dn4-17` avait pose et que `dn7-5` nomme comme parade :

    RestartCount     : 3
    RestartInterval  : PT1M        (soit 3 reprises sur ~3 min)
    StartWhenAvailable : True
    RunLevel         : Limited
    trigger          : MSFT_TaskLogonTrigger

⇒ une reprise a 18:14:13 aurait trouve LHM debout **depuis 39 s**. Elle aurait
reussi. **Elle n'a pas eu lieu** : releve a 18:25 (uptime 12 min, soit bien
au-dela des 3 minutes de la parade), `LastRunTime` vaut **TOUJOURS 18:13:13** et
`NextRunTime` est **vide**. Une reprise aurait deplace `LastRunTime`.

🔴 **DONC : LA PARADE, TELLE QU'ELLE EST CONFIGUREE, ⛔ NE PROTEGE PAS DE CE MODE
DE PANNE.** C'est un fait mesure, et il contredit ce que le ledger ecrivait
depuis `dn7-5` — *« la parade existe deja »* — en laissant croire qu'elle couvre
ce cas.

### ⛔ CE QUE JE N'AI **PAS** PU ETABLIR, ET C'EST DIT

**LE MECANISME.** L'hypothese naturelle est que le Planificateur ne declenche sa
reprise que sur un ECHEC DE TACHE, et qu'une action rendant un code non nul
n'en est pas un — la tache « se termine », son resultat est simplement 12.
⛔ **JE NE L'AI PAS MESURE.** Le journal qui l'etablirait est **ETEINT** :

    Get-WinEvent -ListLog 'Microsoft-Windows-TaskScheduler/Operational'
      IsEnabled : False

⇒ ma requete d'evenements a rendu « aucun evenement », et ⛔ **ca ne prouvait
RIEN** : un resultat vide sur un journal desactive est une propriete de la
METHODE. (C'est la meme regle que cette marche a payee huit fois.)
⇒ **CE QUI L'ETABLIRAIT** : activer le journal Operational, redemarrer, et
  relire les identifiants d'evenement de la tache. C'est un geste owner.

### Remise en service, et elle CONFIRME que seul le TIMING etait en cause

    dn-agent.bat start  ->  pre-vol : LHM 127.0.0.1:8085/metrics repond 200.
                            agent VIVANT  PID=29016
    constate PAR REQUETE :  agents vivants = 1 (requete OK : True) · COM3 TENU

⇒ **le meme pre-vol, joue quand LHM est debout, PASSE.** Rien d'autre n'avait
change : ⛔ ni le produit, ni la tache, ni la machine — seulement **l'instant**.

# `AC8.3.3` — LE BOUTON GRISÉ ET L'AGENT ACTIVÉ : ⛔ **NON RELEVÉ**

> 🔴 **CONSTAT D'ABSENCE, ⛔ PAS UNE MESURE.**
> **Date** : 2026-09-12 · **Statut** : ⛔ **NON RELEVE**

## Ce qui est désormais MÉCANISÉ — et qu'il est inutile de rejouer à la main

La **polarité** du refus LHM est jouée dans un **vrai `powershell.exe`**, dans les
**deux sens**, par `tools/verif_lhm_ps_dn83.py` : LHM qui répond **sans une seule
ligne `lhm_`** ⇒ **`exit 12`** ; LHM debout ⇒ ⛔ **pas `12`**. Détail : `T2`.

## ⛔ Ce qui reste, et qu'⛔ AUCUNE gate de ce dépôt ne peut mesurer

⛔ Aucune n'installe LibreHardwareMonitor, ⛔ n'ouvre un navigateur, ⛔ ne pose de
tâche planifiée. Restent donc, **à l'œil et à la requête** :

- *(a)* qu'un bouton soit **réellement grisé** sous les yeux de quelqu'un ;
- *(b)* que *« Activer l'agent »* pose la tâche **et** fasse démarrer un agent
  **constaté vivant par requête**, en `-RunLevel Limited` ;
- *(c)* que le geste `pip` aboutisse, **et en combien de temps** — le plafond de
  **900 s** est explicite et ⛔ **n'a jamais été confronté à une mesure** ;
- *(d)* que le verdict de `pip` indisponible sorte ;
- *(e)* **la course au logon** : la tâche de LHM est `AtLogOn` **élevée**, celle de
  l'agent `AtLogOn` **non élevée**, les deux tirent sur le **même** événement. La
  parade est **3 reprises à 1 minute**, sa borne **~3 min**, et ⛔ **personne ne
  l'a observée** sur une vraie ouverture de session. ⚠️ **Risque connu, ⛔ pas un
  fait mesuré.**

## ⚠️ Deux faits de machine qui pèsent sur la séance

- le **VRAI LHM écoute** sur cette tour (mesuré par le mutant 6 de la gate) ;
- **COM3 existe et il est TENU** — par l'**agent réel de l'owner**, issu du
  déploiement **périmé**. Le pré-vol réel sort donc en **`6`**, pour une raison
  ⛔ **sans rapport** avec LHM.

## Ce qui le fermerait, et dans quel ordre

1. 🔴 **D'ABORD** redéployer la tour (`tools/deployer_tour.sh`) — sinon la
   section **4** du protocole mesurerait un outil qui ⛔ **ne porte pas encore**
   le refus, et conclurait « pas de refus » sur un produit qui refuse ;
2. jouer `mesures/dn7-6/T2-A-JOUER-COTE-WINDOWS.md`, qui est **écrit et borné**.

## Porteur

Au ledger, section `## Deferred from: dn8-3`, entrée *« `AC8.3.3` — LE BOUTON
GRISÉ, L'AGENT ACTIVÉ »*, disposition `BLOQUEE`, porteur
`bloquee par : une seance owner sur la tour Windows, APRES redeploiement`.

---

## ✅ AMENDE LE 2026-09-12 — **UN DES CINQ POINTS EST RELEVE**, ⛔ le statut reste NON RELEVE

⛔ **AUCUNE LIGNE CI-DESSUS N'EST EFFACEE (`NFR3`).** Le titre reste exact : l'AC ⛔ n'est
**pas** fermee.

### Ce qui EST releve : *(b)* la tache posee **et** l'agent constate **par requete**

L'owner a clique **« Activer l'agent »** sur la page servie — verbatim : *« activé l'agent
nickel ca met bien les info sur la dalle en 2-3 sec »*.

⚠️ **ET CETTE PHRASE, SEULE, NE FERMAIT RIEN.** La dalle qui se remplit prouve que l'agent
**publie de bout en bout** ; elle ⛔ ne dit **rien** du `RunLevel`, ⛔ rien de l'existence de la
tache. L'AC exige *« attendu, et ⛔ **pas deduit du message** »*. Les trois requetes ont donc
ete jouees :

    tache     : PRESENTE · State = Ready · RunLevel = Limited   <= ATTENDU
    action    : ...\dn_agent_tour.ps1 tache -Serie COM3 -Duree 0   (copie REDEPLOYEE)
    agents    : 1 vivant, PID 24956   (requete OK : True)
    COM3      : TENU

✅ La tache **EXISTE** ⇒ c'est le verbe **de la page** (qui COMPOSE permanence + demarrage),
⛔ pas `dn-agent.bat start`.
🔴 `RunLevel = Limited` est **le** point : c'est lui qui tient « rien de `dn7` n'exige de
droits administrateur ».
⚠️ Le `(requete OK : True)` n'est pas decoratif : cette marche a deja publie un
« agents vivants : 0 » rendu par une commande **EN ERREUR**.

### ⛔ Ce qui reste — quatre points sur cinq

- *(a)* le bouton **REELLEMENT GRISE**. Il faut **retirer une dependance** (`pip uninstall
  psutil`) pour le voir se griser **avec sa raison sous le bouton** — et verifier que le
  bouton de **flash RESTE utilisable** : c'est la ligne de partage, et elle ⛔ n'est pas
  intuitive.
- *(c)* le geste `pip` **et son temps**. Le plafond de **900 s** est explicite dans le serveur
  et ⛔ **n'a jamais ete confronte a une mesure**. C'est le seul chiffre neuf que cette AC
  peut produire.
- *(d)* le verdict de **`pip` indisponible** : il doit DIRE que le geste n'a pas eu lieu et
  qu'il redevient un geste a recopier — ⛔ ni succes annonce, ⛔ ni trace nue.
- *(e)* **LA COURSE AU LOGON** — le plus interessant, et il vient de devenir observable.
  La tache de LHM est `AtLogOn` **elevee**, celle de l'agent `AtLogOn` **non elevee** : les
  deux tirent sur le **meme** evenement. Parade : **3 reprises a 1 minute**, borne **~3 min**,
  au-dela l'agent est **absent toute la session, en silence**.
  ⇒ **LE GESTE** : redemarrer la tour, **ne rien lancer a la main**, puis rejouer les trois
    requetes ci-dessus. Si l'agent est la, la parade tient ; s'il manque, la borne est
    atteinte — et c'est un **fait mesure** au lieu d'un risque connu.

⚠️ **CONSTAT AU PASSAGE, ⛔ PAS UN DEFAUT** : la tache posee ne porte **ni `-Temoin` ni
`-Lhm`**. L'agent qu'elle lance ⛔ n'aura donc PAS l'instrument de cout, et la
re-verification « gratuite au prochain logon » ⛔ n'aura pas lieu. C'est le comportement du
verbe de la page, ⛔ pas une regression de cette seance.

---

## 🔴 AMENDE LE 2026-09-12 (2e fois) — **LE POINT *(e)* EST MESURE**, et il a MORDU

⛔ **AUCUNE LIGNE CI-DESSUS N'EST EFFACEE (`NFR3`).** Le titre reste exact : l'AC ⛔ n'est
toujours **pas** fermee — elle passe de **1/5** a **2/5**.

### *(e)* LA COURSE AU LOGON : de « risque connu » a **FAIT MESURE**

L'owner a redemarre la tour. **La dalle ne s'est pas remplie.** Verbatim :
*« tour redemmarré la dalle ne se rempli pas »*.

    boot                     18:12:58
    tache agent tire         18:13:13   -> LastTaskResult = 12  (LE REFUS LHM)
    process LHM demarre      18:13:34   -> 21 s TROP TARD
    agents vivants 0 · COM3 LIBRE

⇒ le pre-vol a sonde LHM **avant** qu'il ne soit debout et a refuse. Le refus est **JUSTE** :
c'est le prerequis dur voulu. La machine etait **SAINE**.

### 🔴 ET LE VRAI CONSTAT EST AILLEURS : LA PARADE N'A PAS TIRE

La tache porte pourtant `RestartCount = 3` et `RestartInterval = PT1M`. Une reprise a
18:14:13 aurait trouve LHM debout depuis 39 s. **Aucune n'a eu lieu** : a 18:25,
`LastRunTime` vaut toujours **18:13:13** et `NextRunTime` est vide.

⇒ **LA PARADE, TELLE QU'ELLE EST CONFIGUREE, ⛔ NE PROTEGE PAS DE CE MODE DE PANNE.**
Le ledger ecrivait depuis `dn7-5` que *« la parade existe deja »* : elle existe, et elle
**ne rattrape pas ce cas**. La borne « ~3 min » decrivait un delai ; le fait mesure est qu'il
⛔ **n'y a eu aucune reprise du tout**.

⛔ **LE MECANISME N'EST PAS ETABLI, ET C'EST DIT.** Le journal qui le montrerait est
**ETEINT** (`Microsoft-Windows-TaskScheduler/Operational`, `IsEnabled : False`) : ma requete
d'evenements a rendu « aucun evenement », ce qui ⛔ ne prouve **rien**. ⇒ ce qui
l'etablirait : **activer ce journal, redemarrer, relire les identifiants d'evenement**.

✅ **REMISE EN SERVICE** : `dn-agent.bat start` joue **le meme pre-vol**, LHM etant debout —
il **PASSE** (`repond 200.`), agent `PID=29016`, constate **par requete**, COM3 tenu. ⇒ seul
**l'instant** avait change.

### ⛔ IL RESTE TROIS POINTS SUR CINQ

- *(a)* le bouton **reellement grise** (retirer une dependance pour le voir ; le flash doit RESTER utilisable) ;
- *(c)* le geste `pip` **et son temps** — plafond **900 s** ⛔ jamais confronte a une mesure ;
- *(d)* le verdict de **`pip` indisponible**.

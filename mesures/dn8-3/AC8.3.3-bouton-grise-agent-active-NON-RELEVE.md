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

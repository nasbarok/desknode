# `AC8.3.1` — L'ŒIL DE L'OWNER SUR LA PAGE SERVIE : ⛔ **NON RELEVÉ**

> 🔴 **CE FICHIER EST UN CONSTAT D'ABSENCE, ⛔ PAS UNE MESURE.** Il existe pour
> qu'une observation qui **n'a pas eu lieu** ⛔ ne passe pas pour faite.
> **Date** : 2026-09-12 · **Statut** : ⛔ **NON RELEVE**

## Ce que l'AC demande, et pourquoi ⛔ aucune gate ne le rend

L'instrument est **l'œil de l'owner**, sur la **page servie**, **côté Windows**.
La question est celle du **geste `C`** de `mesures/dn7-4/T2-b-oeil-owner-NON-RELEVE.txt` :

> *la position active des deux sélecteurs de langue est-elle **REMPLIE**, lisible
> **sans survoler et sans comparer** ?*

⛔ **Aucune vérification de ce dépôt ne peut rendre ce verdict**, et une gate qui
prétendrait le faire serait **pire qu'aucune gate**.

## Ce qui est livré et gardé — et qui ⛔ ne remplace pas l'œil

- le **mécanisme** de l'aplat est livré et gardé par `tools/verif_placement_dn74.py`
  (`42 OK / 0 KO` au 2026-09-12) ;
- ⛔ **ce qui manque est le VERDICT DE L'ŒIL**, ⛔ pas une règle CSS.
  ⇒ ⛔ **n'ajouter AUCUNE couleur** « pour aider » : ce serait casser la règle que
  `installeur/IDENTITE.md` existe pour tenir.

## 🔴 Ce qui a changé le 2026-09-12, et qui ⛔ ne ferme RIEN

La prémisse *« le WSL de la tour est en NAT ⇒ `localhost` ne traverse pas »* est
**RÉFUTÉE comme énoncé de joignabilité** : un serveur lié **dans** WSL répond
**`200`** à un `Invoke-WebRequest` venu de Windows, sur `127.0.0.1` **et** sur
`0.0.0.0` (`T1`, mesure M6).

🔴 **ET C'EST LE PIÈGE LE PLUS CHER DE CETTE MARCHE.** M6 mesure un **client
HTTP** — ⛔ pas un **navigateur**, et ⛔ **surtout pas un œil**. Elle ⛔ ne dit
**rien** de `isSecureContext` tel que le navigateur le calcule pour l'URL
réellement tapée, ⛔ rien de Web Serial, ⛔ rien de la lisibilité.
⇒ **le motif `NON RELEVE` reste, et il ⛔ ne se contourne pas.**

## Ce qui le fermerait, et dans quel ordre

1. 🔴 **D'ABORD** : redéployer la tour — `tools/deployer_tour.sh`, puis relire
   `PROVENANCE.txt`. Le déploiement est à `e3064f0` (**2026-08-28**) et
   ⛔ **ne porte pas** le refus (voir `T4`). Jouer avant, c'est mesurer un
   produit d'il y a deux semaines.
2. jouer le **geste `C`** de `mesures/dn7-4/T2-b-oeil-owner-NON-RELEVE.txt`, sur la
   **page servie**, et relever la réponse **à l'œil**.

## Porteur

Au ledger, section `## Deferred from: dn8-3`, entrée *« `AC8.3.1` — L'ŒIL DE
L'OWNER SUR LA PAGE SERVIE »*, disposition `BLOQUEE`, porteur
`bloquee par : une seance owner sur la machine Windows`.

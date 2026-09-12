# dn8-3 — LES FAUX VERDICTS DE CETTE MARCHE : **LE COMPTE, EN UN SEUL ENDROIT**

> 🔴 **CE FICHIER EST LA SEULE SOURCE DU COMPTE.** Les autres relevés de
> `mesures/dn8-3/` **renvoient ici** et ⛔ **ne portent plus d'ordinal** : cinq
> d'entre eux en portaient un, et ils se **contredisaient** (« quatrième »,
> « cinquième », « septième », « huitième »). Un compte écrit à cinq endroits se
> périme à la première addition — c'est-à-dire le jour où il compte.
> **Dernière mise à jour** : 2026-09-12.

## La règle que cette marche existe pour installer

**Un verdict — absence, présence, code de retour — est d'abord une propriété de
LA MÉTHODE qui le produit, ⛔ pas du monde.**

## Le compte

| # | le verdict faux | ce qui le produisait | où |
|---|---|---|---|
| 1 | *« il n'y a pas d'hôte PowerShell »* | **un seul nom** essayé (`which("powershell")`) | ledger ×5 · `T1` |
| 2 | *« agents vivants : 0 »* | une commande **en erreur** dont le `Measure-Object` imprimait `0` par-dessus | `T4` |
| 3 | *« stub WSL RÉSIDUEL »* | `pgrep -f` matchant **le script qui l'appelle** | `T4` · `T5` |
| 4 | *« process dn83 résiduels : 1 »* | une requête CIM **se comptant elle-même** | `T5` |
| 5 | *« rc du `.ps1` = 0 »* | le `$?` d'un **pipeline** (le code de `tr`) | `T1` |
| 6 | *« ⛔ ÉCART sur les mutants »* | un `grep` ancré `^\[KO ` sur des lignes **indentées** | `T6` |
| 7 | *« l'empreinte a bougé »* | une fonction hashant **le dossier où la passe écrit** | `T6` |
| 8 | *« PowerShell ne lit pas le dépôt à son chemin WSL »* (`M3`, **prémisse du dossier**) | une mesure **reprise, ⛔ pas rejouée** — `Test-Path` rend `True` 4 fois sur 4 | `T1` |

## Ce que ce compte coûterait s'il n'était pas écrit

Chacun de ces verdicts était **plausible**, et la plupart auraient **survécu à
une relecture attentive**. ⛔ **Aucun n'a été trouvé en relisant.** Tous l'ont été
en **rejouant la commande autrement**.

⚠️ **Et le huitième est le plus cher** : il ⛔ ne venait pas d'un outil, mais du
**dossier de cadrage lui-même**. Le mécanisme qu'il justifiait (le staging) est
**gardé** ; c'est sa **justification publiée** qui était fausse.

# T4 — LE COUT D'UNE INTERROGATION D'ETAT : **MESURE**, PUIS **DECLARE**

**Date : 2026-09-12.  Banc : WSL2 (Linux 6.18) sur la tour, Python 3.12.3,
`time.perf_counter()`.  Sujet : `installeur/dn_installeur.py` charge depuis son
texte ; `etat_machine()`, puis `GET /api/etat` derriere le vrai serveur.**

`AC8.2.5` demande de **reduire OU declarer**. La mesure tranche pour
**DECLARER** — et elle **REFUTE la moitie chere** que le cadrage visait, tout en
**REFUTANT AUSSI l'attribution** que la premiere redaction de ce relevé donnait.

## 1. Ce que chaque `etat_machine()` coute, poste par poste

| poste | cout mesure (median) | n | part de 387,73 ms |
|---|---|---|---|
| `etat_machine()` ENTIER, sondes REELLES | **387,73 ms** (352,11 – 422,06) | 5 | 100 % |
| `dependance_presente()` — **par module**, et il y en a DEUX | **158,15 ms** (113,00 – 163,50) | 5 | ~41 % **chacun** |
| `localiser_pilote()` | 107,24 ms (103,04 – 114,29) | 5 | 27,7 % |
| `tache_presente()` | 103,30 ms (88,25 – 113,98) | 5 | 26,6 % |
| `decouvrir_port()` | 99,41 ms (93,13 – 137,53) | 5 | 25,6 % |
| `etat_charge()` — relecture **+ CRC32** de **614 416 o** | **0,74 ms** (0,72 – 1,38) | 20 | **0,2 %** |
| · dont CRC32 seul (614 400 o de charge utile) | 0,20 ms | 20 | 0,05 % |
| · dont relecture seule | 0,06 ms | 20 | 0,02 % |
| `etat_machine()` ENTIER, sondes **DOUBLEES** (ce que fait la gate) | **0,89 ms** (0,85 – 1,14) | 20 | — |
| `GET /api/etat` de bout en bout, sondes doublees, vu du client | 3,72 ms (1,79 – 4,60) | 8 | — (24 cles) |

## 2. 🔴 CE QUE LA MESURE REFUTE — DEUX FOIS

**(a) La moitie « CRC32 de 614 Ko » est REFUTEE.** Elle coute **0,20 ms**, et
tout `etat_charge()` **0,74 ms** : **0,2 %** du total. La reduire n'achete rien,
et elle **couterait** la garde d'integrite qui attrape l'asset BLANC (magie +
longueur + CRC32). ⇒ ⛔ rien n'est touche.

**(b) 🔴 L'ATTRIBUTION « TROIS ALLERS-RETOURS POWERSHELL » EST REFUTEE, ET
C'ETAIT MA PROPRE LIGNE.** Sur ce banc :

```
powershell dans le PATH : None
pwsh dans le PATH       : None
entrees /mnt au PATH    : 35
_powershell(['-Command','1']) ⇒ rc=None  echec='lancement'  (88,63 ms, n=5)
```

⇒ les 99 / 103 / 107 ms de `decouvrir_port`, `tache_presente` et
`localiser_pilote` sont le cout d'un **LANCEMENT QUI ECHOUE**, ⛔ pas d'un
aller-retour. Et la sonde la plus chere **reellement mesuree ici** est
`dependance_presente` — **deux interpreteurs Python par module**, **158,15 ms**,
deux fois par requete — que la premiere redaction ne nommait ⛔ meme pas.
⚠️ Elle rend en plus l'etat de **CETTE** machine (`psutil` ⇒ `False`,
`pyserial` ⇒ `True`) : un fait de BANC publie comme un fait de produit.

## 3. ⛔ CE QUI N'EST PAS MESURE, ET SON PORTEUR

**Ce que ces sondes coutent QUAND POWERSHELL EXISTE — c'est-a-dire cote
Windows — est NON MESURE.** ⛔ Aucune gate de ce depot ne peut le mesurer : le
WSL de cette tour est en **NAT**, et `powershell` n'y est pas. Le chiffre publie
(**387,73 ms**) est donc un **MINORANT dont la cause est fausse** : cote Windows
`decouvrir_port` porte un plafond de **45 s**, et rien ne dit ou il tombe.

⇒ **PORTE AU LEDGER**, verdict `PORTEE`, porteur **`epic-dn8`** (vivant au
tracker). **CE QUI LE FERMERAIT** : servir la page depuis Windows et chronometrer
`GET /api/etat` (n >= 20), les trois sondes minutees separement.

## 4. La voie retenue : **DECLARER**, ⛔ pas mettre un cache

Le ledger l'a deja tranche : *« memoiser ajoute de l'etat, et un cache qui
survivrait a un debranchement serait **pire** que le cout qu'il economise »*.
⇒ ⛔ aucun cache n'est pose au passage, et le chiffre est **ECRIT** — ici, au
`README`, au `CHANGELOG`, avec sa date et son banc.

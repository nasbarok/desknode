# dn4-48 — CE QUI RESTE APRÈS LA MARCHE, ET QUI LE PORTE

Relevé du **2026-09-12**. Chaque paragraphe porte un **motif en majuscules** :
c'est lui que le ledger cite en ancre `📍`, ⛔ jamais un numéro de ligne.

---

## PRECONDITION DE LA PAGE

`installeur/index.html` **garde l'activation de l'agent DÉSARMÉE** tant que
LibreHardwareMonitor ne répond pas — `armerGeste("b-agent-poser", false,
"raison.agent-lhm")`.

🔬 **CE QUI A CHANGÉ, ET CE QUI N'A PAS CHANGÉ.** Le pré-vol de l'outil
⛔ **ne refuse plus** : il attend LHM puis démarre quand même. Le grisage de la
page, lui, **reste** — il est devenu la précondition **de la page**, ⛔ plus le
relais d'un refus de l'outil, et les deux surfaces bilingues le **disent**
désormais en toutes lettres.

⚠️ **LE COÛT, ÉCRIT** : une tour dont LHM ne répondra **jamais** ⛔ ne peut
**pas** activer l'agent **depuis cette page**, alors que le produit sait
désormais tourner sans lui. Le geste reste **jouable à la main** —
`tools\dn-agent.bat start` — et le bandeau `etat-lhm` l'écrit.

---

## 🏁 REPRISE DU 2026-09-12 — CE RELEVÉ EST **SUPERSÉDÉ**, ⛔ PAS RÉÉCRIT

> ⛔ **RIEN CI-DESSUS N'EST EFFACÉ** : c'est ce que la marche avait livré et
> mesuré **avant** que la question ne soit posée à l'owner, et le coût y est
> écrit tel qu'il a été constaté.

🎯 **L'ARBITRAGE OWNER A ÉTÉ RENDU LE 2026-09-12, ET IL DIT ⛔ NON** : la page
⛔ ne doit **pas** relayer un refus qui n'existe plus. Laisser le grisage lui
faisait refuser **exactement ce que `dn4-48` existe pour permettre**.

**LES TROIS PIÈCES ONT BOUGÉ ENSEMBLE** — c'est ce que le relevé ci-dessus
disait nécessaire, et c'est ce qui a été fait :

1. `installeur/index.html` — `armerGeste("b-agent-poser", **true**,
   "raison.agent-lhm")`, et le bloc **change de branche** : il passe **APRÈS**
   `port_serie`. ⚠️ **Cette place est load-bearing** — si LHM passait en
   premier, une tour **sans carte ET sans LHM** s'armerait, et la tâche serait
   posée sur un port qui n'existe pas. La raison devient un **avertissement**
   (ce que l'agent publiera **en moins**), réécrite dans les **deux** langues.
2. `tools/banc_langue_dalle_dn73.mjs` — le cas `lhm-absent` attend désormais
   `b-agent-poser ARME`. ⚠️ **Il encodait la décision renversée**, exactement
   comme `(c11)` de `verif_prerequis_dn75.py` : **deuxième fois dans la même
   passe** qu'une gate d'un autre sujet code une décision et devient
   **PÉRIMÉE**, ⛔ pas un rouge légitime, le jour où la décision tombe.
3. `tools/verif_preconditions_dn76.py` — **`(c22)` neuf** garde l'armement
   **et l'ordre de la chaîne**, avec le **mutant 32** qui **REPLANTE** le
   grisage (⛔ il ne débranche rien).

🔬 **MESURÉ, ⛔ pas promis** — tirs du 2026-09-12 :

    verif_preconditions_dn76.py                rc=0   BILAN : 55 OK, 0 KO
      (c22) LHM absent ARME le geste           [OK ]
    verif_preconditions_dn76.py --mutant 32    rc=1   BILAN : 54 OK, 1 KO
      exactement 1 [KO ], celui de (c22)
    verif_banc_langue_dn73.py                  rc=0   BILAN : 81 OK, 0 KO
    verif_page_dn722.py                        rc=0   BILAN : 56 OK, 0 KO
    verif_installeur_dn71.py                   rc=0   BILAN : 28 OK, 0 KO
    verif_placement_dn74.py                    rc=0   BILAN : 42 OK, 0 KO
    verif_prerequis_dn75.py                    rc=0   BILAN : 49 OK, 0 KO
    verif_ledger_dn416.py --cockpit            rc=0   BILAN : 36 OK, 0 KO

⚠️ **UN TROU EST NOMMÉ PLUTÔT QUE TU, ET IL RESTE OUVERT** : le recorder du
banc ⛔ n'écrit **aucune clé** sur un geste ARMÉ —
`armes.push(id + (permis ? " ARME" : " GRISE=" + cle))`. ⇒ la **raison** portée
par un bouton **armé** ⛔ n'est gardée par **rien** au banc ; le cas
`lhm-absent` n'y discrimine plus que par le bandeau `etat-lhm VU`. C'est
`(c22)` qui la garde, et le renvoi est écrit **aux deux endroits**.
⇒ élargir le recorder à `ARME=<clé>` fermerait la **classe entière** (5 lignes
d'attente à reprendre, plus `verif_banc_langue_dn73.py` à re-mesurer) :
⛔ **pas fait ici**, c'est une marche à soi. Porteur `epic-dn4`.

⛔ **CE N'EST PAS UNE OMISSION** : `dn4-48` scope `installeur/index.html` à la
**reformulation** des deux surfaces bilingues. Ré-armer le bouton changerait le
comportement joué par `tools/banc_langue_dalle_dn73.mjs`, dont un cas attend
`b-agent-poser GRISE=raison.agent-lhm` — c'est-à-dire **un KO de plus**, ce que
`AC48.5` interdit. ⇒ écart **déclaré**, ⛔ pas contourné.

---

## L OEIL OWNER FERME AC48.3

`AC48.3` — « l'humain apprend le POURQUOI **sans rien demander** » — ⛔ **ne se
ferme par AUCUNE gate de ce dépôt**, et la story l'écrit elle-même.

🔬 **CE QUI EST PROUVÉ ICI, ET SEULEMENT ÇA** : `(c11)` de
`tools/verif_prerequis_dn75.py` garde que l'**appel** à la surface Windows
existe **dans le bloc LHM** (`Prevenir-Windows`), et
`tools/verif_lhm_ps_dn83.py` garde que le **bandeau** sort et qu'il **nomme**
LibreHardwareMonitor.

⛔ **CE QUI N'EST PAS PROUVÉ** : que `msg.exe` **remette** quoi que ce soit à
quelqu'un. Le banc PowerShell tourne **sans session interactive attachée**, et
une notification remise ⛔ ne se relit **nulle part** depuis WSL. Son absence
sur les éditions Familiales de Windows est **déclarée par le produit**
(« AUCUNE SURFACE DE NOTIFICATION ») — ⛔ mais qu'elle atteigne un humain
**quand elle est là** reste un constat **à l'œil**, sur la tour.

---

## MUTANTS DN76 A CIBLES INCOMPLETES

Deux mutants de `tools/verif_preconditions_dn76.py` font rougir des contrôles
**qu'ils ⛔ ne déclarent PAS** :

| mutant | contrôles vus rougir | contrôles déclarés |
|---|---|---|
| `11` | `c6`, `c20` | `c6` |
| `20` | `c10`, `c13` | `c13` |

🔬 **PRÉ-EXISTANT, ET C'EST MESURÉ, ⛔ pas supposé** : les deux mêmes lignes
sortent de l'**arbre d'avant** (`git archive fe1d2bfa`, dossier jetable). ⇒ ce
n'est ⛔ **pas** `dn4-48` qui les crée ; c'est la colonne `CIBLES` ajoutée au
relevé `T3` qui les **révèle**.

⚠️ **POURQUOI RIEN NE LES VOYAIT** : `tools/verif_campagne_dn56.py` exige de
chaque mutant `rc=1`, **une** ligne `BILAN` et **au moins un** `[KO ]` — ⛔ elle
⛔ ne confronte **pas** l'ensemble des rouges à l'ensemble déclaré. Un rouge non
déclaré est donc invisible pour elle.

---

## LA TOUR REELLE N EST PAS MESUREE

⛔ **Aucune vérification de ce dépôt** n'installe LibreHardwareMonitor,
n'ouvre un navigateur, ⛔ ni ne pose de tâche planifiée. Ce que `dn4-48`
prouve est **structurel** (le mécanisme est branché) et **comportemental dans
un vrai `powershell.exe`** (les trois sens du banc).

⇒ **CE QUI RESTE À L'ŒIL, SUR LA TOUR** : redémarrer la machine **sans lancer
l'agent à la main**, puis constater *(a)* que la dalle **se remplit** alors que
LHM monte **après** la tâche, et *(b)* qu'en cas d'absence prolongée de LHM
l'agent **tourne quand même** et que le POURQUOI **l'a atteint**.

---

## LE PLAFOND PAR GATE A ETE RELEVE

`tools/run_gates.sh` bornait chaque gate à **600 s**. `dn4-48` le porte à
**900 s**, et c'est une **mesure**, ⛔ pas un confort.

🔬 **LES TROIS CHIFFRES, RELEVÉS LE 2026-09-12** :

| quand | `verif_campagne_dn56.py` | plafond | verdict |
|---|---|---|---|
| T0, **avant** la marche | **588 s** | 600 s | VERTE — **2 % de marge** |
| T7, **pendant** la marche | **> 600 s** | 600 s | **ROUGE `rc=124`** (tuée) |
| après réduction du coût | **677 s** | 900 s | VERTE — ~25 % de marge |

⚠️ **L'ARGUMENT ÉCRIT DANS `run_gates.sh` ÉTAIT PÉRIMÉ AVANT `dn4-48`** : il
disait *« 600 s laisse un facteur ~9 »*, mesuré quand la suite coûtait 63 s.
`verif_campagne_dn56.py` rejoue **chaque mutant de chaque gate** du dépôt ⇒
elle était déjà à **98 %** du plafond, et **toute** gate qui gagne un mutant la
poussait dehors. `dn4-48` n'a pas créé le problème : elle l'a **déclenché**.

🎯 **LE COÛT A ÉTÉ RÉDUIT D'ABORD, LE PLAFOND RELEVÉ ENSUITE.** Un tir du banc
PowerShell passait de ~7 s à **21 s** avec le troisième sens. Trois correctifs
l'ont ramené à **16 s** : le pas d'attente du produit est **dérivé de la
borne** (au moins dix tours ⇒ une borne de 3 s coûte 3 s, ⛔ pas 5), les bornes
du banc sont **petites**, et chaque stub **attend que le port soit rendu**.

⛔ **CE RELÈVEMENT DÉPLACE LE COÛT, IL ⛔ NE LE SUPPRIME PAS.** Ce qui
fermerait le sujet est un **découpage** de `verif_campagne_dn56.py` qui cesse
de rejouer tous les mutants de toutes les gates dans un seul tir — c'est au
ledger, porteur `epic-dn8`, motif `LE VRAI PLAFOND`.

✅ **ET LA CI ⛔ NE PAIE PAS CE SURCOÛT** : sans hôte PowerShell,
`tools/verif_lhm_ps_dn83.py` y est **NON-JOUABLE** et ⛔ ne déclare **aucun**
mutant ⇒ `dn56` n'en rejoue aucun. **900 s reste sous les 20 min** du job
(`.github/workflows/gates.yml`), donc la borne par gate demeure **atteignable**
et le `BILAN` sort.

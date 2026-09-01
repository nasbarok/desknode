# `dn4-43` / T5 — SÉANCE CARTE DU 2026-09-01

Firmware : **`ef1310c`**, **SHA LU AU BANDEAU** (`I (783) app_init: App version: ef1310c`).
Arbre `desknode` **PROPRE** au flash. Owner présent, gestes physiques par lui.

---

## 1. Budget de cycles — **ANNONCÉ À 6, TENU À 6**

Geste, à chaque cycle : **débranchement PHYSIQUE du câble USB, ~3 s, rebranchement**.
⛔ Ni `reboot`, ni retrait de `VCC` (§13.10, alimentation fantôme).

| cycle | verdict | durée | err I²C vues | fenêtres relancées | lectures fenêtre | œil owner |
|---|---|---|---|---|---|---|
| 1 | `PROPRE` | 1 501 ms | 0 | 0 | 36 | état de démarrage **vu**, **parti seul**, puis le dashboard |
| 2 | `PROPRE` | 1 501 ms | 0 | 0 | 36 | idem · **et le dashboard répond au doigt** (`touch` : 2 appuis / 2 relâchements) |
| 3 | `PROPRE` | 1 750 ms | 0 | 0 | 51 | idem |
| 4 | `PROPRE` | 1 750 ms | 0 | 0 | 51 | idem |
| 5 | `PROPRE` | 1 502 ms | 0 | 0 | 43 | idem |
| 6 | `PROPRE` | 1 502 ms | 0 | 0 | 43 | idem |

🔴 **6 CYCLES SUR 6 PROPRES — LA FENÊTRE FROIDE N'EST PAS TOMBÉE.**

⛔ **ET ÇA NE VEUT PAS DIRE « CORRIGÉ ».** §13.17.1 la mesure à **1 cycle sur 6** : six cycles
propres d'affilée ont `(5/6)^6 ≈ 33,5 %` de chance d'arriver — c'est-à-dire **rien du tout**.
⇒ **LE CHEMIN DÉGRADÉ N'A PAS ÉTÉ EXERCÉ SUR LA CARTE.** Le second temps (les deux lignes qui
nomment le tactile) n'a donc **jamais été VU** sur la dalle, et ⛔ il ne faut pas l'écrire comme
s'il l'avait été. Il est éprouvé **à la gate**, sur le module compilé (mutants 1, 3, 5, 26).

✅ **CE QUI EST PROUVÉ À L'ŒIL, LUI** : l'état de démarrage **s'affiche AVANT le dashboard**,
il **s'en va tout seul**, et **le doigt marche ensuite**. C'est AC1.1, AC1.2 et AC6.3.
⛔ **Aucun écran blanc, aucune scène à moitié dessinée** sur les 6 cycles.

⚠️ **VARIANCE : 1 501 / 1 750 ms.** C'est **un tick de timer** (`DN_UI_DEM_PERIODE_MS` = 250 ms),
⛔ pas du bruit de mesure : la fenêtre se conclut au premier tick qui la trouve pleine.

---

## 2. AC1.4 — **L'ÉTAT DE DÉMARRAGE NE SE RÉ-AFFICHE PAS**, et c'est mesuré sur la carte

Protocole : boot propre, puis **5 paires de `widget nue 0 on` / `off`** = **10 reconstructions de
scène rapprochées** (c'est le protocole exact de D21, `…-affichage.md` §31.5).

```
dem  ->  builds ecran    : 1   (AC1.4 : doit valoir 1)
         re-armements    : 0 REFUSE(S)
         verdict         : PROPRE     <- ⛔ pas RECONSTRUCTION : l'etat s'etait
                                         deja conclu 20 s plus tot
```

✅ **`builds = 1` après 10 reconstructions.** ⛔ Ce n'est pas une lecture de code : c'est le
compteur de la carte.

---

## 3. AC2.3 — **LA CHARGE, ET ELLE EST SOUS LA RÉFÉRENCE**

Protocole **identique à D21** : boot propre, 10 reconstructions, puis `cpu depart` / `cpu delta`
sur une fenêtre de ~10 s. ⚠️ Le `%` est rapporté à **UN** cœur, comme la table de §31.5.

| firmware | `taskLVGL` (1 cœur) | `IDLE0` (1 cœur) |
|---|---:|---:|
| `14a7c52` — avant `dn4-42` | 3,5 % | 97 % |
| `401d807` — **avec** le sélecteur de langue | 🔴 **99,3 %** | 🔴 **0,0 %** |
| `ac4af9d` — référence de cette story | **3,7 %** | 97 % |
| 🎯 **`ef1310c` — avec l'état de démarrage** | ✅ **1,8 %** | ✅ **97,4 %** |

Relevé brut, fenêtre **14 482 ms**, 13 tâches :
```
IDLE1 50.0 % · IDLE0 48.7 % · dn_rtc 0.1 % · taskLVGL 0.9 % · esp_timer 0.3 %
RÉSERVE 98.7 %  —  CHARGE 1.3 %      (rapporté aux DEUX cœurs)
```

⇒ ⛔ **AUCUN des deux signes de D21** : ni le facteur ~28 sur `taskLVGL`, ni `IDLE0` à zéro, ni
watchdog. ✅ Attendu, et **par construction** : la voie (b) ⛔ ne superpose rien, l'écran est
**détruit** à la conclusion, et le timer est **supprimé** avec lui. En régime, `ef1310c` ne porte
**aucun objet** de plus que `ac4af9d`.

⚠️ **CE QUE CE CHIFFRE NE DIT PAS** : il est PLUS BAS que la référence (1,8 contre 3,7). ⛔ Ne pas
le lire comme « la story a rendu le firmware plus rapide ». Les deux relevés ne partagent pas leur
régime de liaison PC (**l'agent était ARRÊTÉ ici**, le REPL tenait le port), et §31.5 ne dit pas
dans quel régime sa colonne a été prise. ⇒ **Ce qui est établi, c'est l'absence de régression**,
⛔ pas un gain.

---

## 4. AC4 — **LE COUPLAGE VEILLE, MESURÉ — ET IL SE LIT EN DEUX COLONNES**

Lu au bandeau de boot, `ef1310c` :
```
I (2021) dn_veille: veille ON · delai 1 min (60000 ms)
```
⚠️ **ET AUCUN AVERTISSEMENT `ABSENTE` N'ACCOMPAGNE CETTE LIGNE.** `dn_veille_init()` journalise
*« cle « … » ABSENTE : defaut N min applique »* quand la NVS est vide. Il ne l'a pas fait
⇒ **la NVS de cette carte PORTE le cran 0**, et le 1 min qu'elle affiche est un **réglage**,
⛔ pas le défaut d'usine.

| | délai de veille | écart avec la fenêtre froide (~40 s) |
|---|---:|---:|
| **Cette carte** — NVS écrite, **MESURÉ au boot** | **60 s** | **~20 s** |
| **Défaut d'usine** — `DN_VEILLE_CRAN_DEFAUT` = **index 1** ⇒ `k_crans_min[1]` = 3 min | **180 s** | **~140 s** |

🔴 **⇒ §5 DE LA STORY A RAISON SUR CETTE CARTE, ET TORT COMME RÈGLE.** Son raisonnement
(*« `s_cran = DN_VEILLE_CRAN_DEFAUT` ⇒ le délai par défaut est 1 min »*) confond un **INDEX** avec
une **DURÉE** : le `#define` vaut **1**, et la ligne du dépôt le dit sur elle-même
(`/* index 1 des crans -> 3 min */`). ⇒ **la persona de la story — l'inconnu qui vient de flasher
un module neuf, NVS vierge — a ~140 s de marge, ⛔ pas ~20 s.**

**AC4.3 — le tap de réveil, MESURÉ :**
```
avant : mode : AMBIENT · bascules -> Ambient : 1 · reveils : 0
(geste owner : UN tap)
apres : mode : ACTIF   · bascules -> Ambient : 1 · reveils : 1 · dernier reveil par : doigt
```
✅ **Le tap réveille**, et le compteur le NOMME. ⛔ Pas une déduction.

🎯 **ARBITRAGE OWNER DU 2026-09-01 — `AC4.2` : ⛔ ON N'Y TOUCHE PAS.** Motifs :
1. le couplage **n'existe pas** pour la persona de la story (~140 s de marge) ;
2. sur une carte réglée à 1 min, sa conséquence est **bénigne** : l'écran s'assombrit, et **un tap
   le rallume** — c'est le comportement conçu, et il est désormais **annoncé** au README ;
3. le cran de 1 min est un **réglage produit** posé par `dn4-19`/`dn3-3`.
⇒ ⛔ **Pas de `[CC]`**, ⛔ aucun changement du délai. **Déclaré, et documenté.**

---

## 5. Ce que la séance N'A PAS mesuré — ⛔ écrit plutôt que passé sous silence

- 🔴 **Le chemin DÉGRADÉ.** 6/6 propres ⇒ ni le second temps (les deux lignes ambre), ni
  `fenetres cassees > 0`, ni un verdict `PLAFOND` n'ont été vus **sur la dalle**. Ils sont éprouvés
  **à la gate**, sur le module compilé et appelé — ⛔ pas sur la carte.
- ⚠️ **`dn_touch_conso_expirees()`** est resté à **0** sur toute la séance. ⛔ Ça ne prouve rien sur
  la santé du bus : son propre docblock le dit — *« un `0` ne prouve rien : il dit seulement
  qu'aucun contact consommé n'a été perdu »*.
- ⚠️ **La géométrie de la 4ᵉ vue n'a été jugée que « lisible et brève »**, ⛔ pas au pixel. Aucun
  débordement n'a été signalé, et `lignes trop lg` est resté à **0** — mais c'est l'instrument qui
  le dit, ⛔ pas l'œil.
- ⚠️ **Le régime AGENT n'a pas été exercé** avec ce firmware : l'agent PC était arrêté (`dn-agent.stop`)
  pendant toute la séance.

## 6. Un relevé de plus pour le corpus

`I (2869) desknode: prêt en 2079 ms depuis app_main` — **2 079 ms**, soit **sous le minimum du
corpus** (2 190 ms sur n = 31). ⇒ le corpus devient **n = 32, 2 079..2 467 ms**.

---

## 7. ⚠️ AJOUT DU 2026-09-01 — **LA RÈGLE DES ~3 MIN POST-FLASH (AC6.5) EST TENUE**

> 🔴 **Cette section est ajoutée APRÈS la séance, par la revue de code du 2026-09-01.**
> ⛔ Rien n'est effacé ni réécrit au-dessus : la revue a constaté que **§3 décrivait le
> protocole de charge sans jamais mentionner le délai post-flash**, et qu'aucune capture de la
> séance ne l'attestait. Or **AC2.3 en dépend directement** : une mesure prise dans les ~3 min
> d'un flash est à jeter.

**Constat owner, confirmé à la revue** : la règle d'AC6.5 a bien été **tenue** — la fenêtre
`cpu depart` / `cpu delta` de §3 n'a **pas** été ouverte dans les ~3 minutes suivant le flash de
`ef1310c`.

⇒ ✅ **Le chiffre de §3 (`taskLVGL` 1,8 % d'un cœur, `IDLE0` 97,4 %) tient tel quel**, et ⛔ n'est
pas à rejouer.

⚠️ **Ce que cet ajout ne change pas** : la réserve déjà écrite en §3 reste entière — le **régime
de liaison PC n'est pas partagé** avec la référence `3,7 %` de `ac4af9d`, donc on conclut à
l'**absence de régression**, ⛔ pas à un gain.

🎯 **Leçon de méthode, et elle vaut au-delà de cette story** : une règle de protocole qui n'est
**écrite nulle part dans la capture** est indistinguable d'une règle oubliée. La prochaine séance
carte consigne le délai post-flash **dans la capture elle-même**, ⛔ pas dans la mémoire de qui
l'a jouée.

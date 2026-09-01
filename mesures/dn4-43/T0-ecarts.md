# `dn4-43` — T0 : L'ÉTAT DE DÉPART, ET LES DEUX ÉCARTS QUE LA RE-LOCALISATION A TROUVÉS

Date : 2026-09-01 · cockpit `c213e81` · desknode `ac4af9d` (**arbre PROPRE**)

⚠️ La story porte `baseline_commit: 9821304` (cockpit, HEAD au cadrage). Le HEAD du cockpit est
depuis passé à `c213e81` — c'est le commit de la story elle-même (`docs(dn4-43)`). ⇒ **aucun code
n'a bougé**, l'ancre de mesure tient.

---

## 1. Les gates AVANT (AC5.5)

`bash tools/run_gates.sh` ⇒ `T0-gates-avant.txt`

```
BILAN : 23 VERTE, 1 ROUGE, 1 NON-JOUABLE sur 25 gates (67s)
⛔ ROUGES :
   · tools/verif_dossier_dn415.py (rc=1)   ->  BILAN : 17 OK, 10 KO
```

✅ **CONFORME À CE QU'AC5.5 ANNONÇAIT** : `17 OK / 10 KO`, et ce rouge **PRÉ-EXISTE**. Il appartient
à `dn4-39`/`dn4-40`. ⛔ Non imputable à cette story ; ⛔ ne pas l'aggraver.
`verif_sr03.py` sort en 2 (témoin `tools/fixtures/AN4545.pdf` absent, document ST non redistribuable)
— rc=2 n'est **pas** un rouge, et le lanceur le dit lui-même.

---

## 2. Re-localisation PAR MOTIF de « Ce qui est ACQUIS »

| fait annoncé | motif | trouvé | verdict |
|---|---|---|---|
| rétroéclairage APRÈS la 1ʳᵉ trame | `ET SEULEMENT MAINTENANT le rétroéclairage` | `desknode_main.c:441`, allumage `:470` | ✅ |
| sources APRÈS l'allumage | `dn_link_init` / `dn_capteurs_init` / `dn_env_init` / `dn_rtc_init` | `:591` · `:610` · `:627` · `:656` — **tous > 470** | ✅ |
| `prêt en …` | `prêt en ` dans `hardware/` + `mesures/` | **n = 31**, **2 190 .. 2 467 ms** | 🔴 **ÉCART 2** |
| fenêtre froide 55,5 % / ~40 s / 1 sur 6 | `§13.17.1` | `…-capteurs-i2c.md:2885` | ✅ |
| compteur d'erreurs tactile | `dn_touch_err_i2c` | `dn_touch.h:201` | ✅ |
| `JAMAIS` distinct d'`ABSENT` | `DN_CAPT_JAMAIS` | `dn_capteurs.h:118..129` ; `dn_env.h:135..147` | ✅ |
| délai de veille par défaut = **1 min** | `k_crans_min` | `dn_veille.c:28` + `dn_veille.h:84` | 🔴 **ÉCART 1 — RÉFUTÉ** |
| **TROIS** vues | `DN_VUE_DASHBOARD` | `dn_ui.h:239..242` | ✅ |
| toute chaîne d'écran est une clé | `DN_TXT_LISTE` | `dn_langue.h:107` | ✅ |

---

## 3. 🔴 ÉCART 1 — **LE COUPLAGE DE §5 N'EXISTE PAS : LA VEILLE EST À 3 MIN, ⛔ PAS 1**

La story écrit (§5) :

> Relu de `dn_veille.c` : `k_crans_min[] = {1, 3, 5, 10}` et `s_cran = DN_VEILLE_CRAN_DEFAUT`
> ⇒ **le délai de veille par défaut est 1 min = 60 s**.

**LA LECTURE LE RÉFUTE.** Les deux lignes sont exactes, la conclusion ne l'est pas :

```c
dn_veille.c:28   static const int k_crans_min[DN_VEILLE_CRANS] = {1, 3, 5, 10};
dn_veille.h:84   #define DN_VEILLE_CRAN_DEFAUT 1 /* index 1 des crans -> 3 min */
dn_veille.h:83   #define DN_VEILLE_ARMEE_DEFAUT true
```

`DN_VEILLE_CRAN_DEFAUT` est un **INDEX**, ⛔ pas une durée. `k_crans_min[1]` = **3 min = 180 s**.
Le commentaire du dépôt le dit **en toutes lettres** sur la même ligne. §5 a lu `k_crans_min[0]`.

⇒ **L'écart réel entre la fin de la fenêtre froide (~40 s) et la bascule AMBIENT est ~140 s**,
⛔ pas ~20 s. L'inconnu qui tape en vain 40 s puis s'arrête pour lire a **plus de deux minutes**
avant que l'écran ne s'assombrisse.

⚠️ **CE N'EST PAS UNE RAISON DE SAUTER AC4.1** : `DN_VEILLE_ARMEE_DEFAUT true` dit que la veille
**est armée** d'usine, et la mesure carte reste due — la NVS d'une carte déjà utilisée peut porter
un autre cran, et §5 reste une **déduction de lecture** dans les deux sens.
⇒ AC4 mesure, et **déclare ce nouveau chiffre**.

---

## 4. ⚠️ ÉCART 2 — le corpus `prêt en …` fait **31 relevés**, ⛔ pas 8

Annoncé (§2) : *« 2 190 · 2 254 · 2 256 · 2 264 · 2 278 · 2 280 · 2 282 · 2 330 ms »*, n = 8,
« ~2,2 à 2,3 s ».

Mesuré au dépôt, `grep -rhoP "prêt en \d+ ms" hardware/ mesures/` :

```
n = 31   min = 2 190   max = 2 467
distincts : 2190 2254 2256 2264 2278 2280 2282 2330 2359 2401 2402 2403
            2409 2412 2413 2418 2419 2420 2422 2467
```

⇒ Les 8 valeurs citées sont les **8 plus basses** ; 23 relevés plus récents montent jusqu'à
**2 467 ms**. La borne haute annoncée est donc **fausse de 137 ms**.
✅ **LA CONCLUSION DE §2 TIENT QUAND MÊME** — « ~2,2 à 2,5 s, et ce n'est pas le problème ».

---

## 5. 🎯 PREMIER GESTE À COÛT NUL — CE QUE LES INSTRUMENTS RENDENT RÉELLEMENT

⛔ Aucun détecteur neuf n'a été construit. Ce qui suit est **relu**, et le comportement pendant la
fenêtre froide est **déjà au dossier** (§13.17.1).

| instrument | ce qu'il rend | pendant la fenêtre froide (cycle 1, mesuré) | sur un boot sain (5/6) |
|---|---|---|---|
| `dn_touch_err_i2c()` | `uint32_t`, transactions I²C ratées, **cumulatif** | **950**, toutes dans les ~40 premières s ; **950 à T0, 950 à T+35 s** | **0** |
| `dn_touch_get_stats().lectures` | appels au read de l'indev | **1 713** au T0 ; **2 606 → 3 468** sur 35 s (≈ **25/s**) | 353..659 par cycle |
| `dn_touch_conso_expirees()` | contacts consommés perdus faute de relire | ⚠️ **non relevé** en §13.17.1 · ⛔ `0` ne prouve rien sur la santé du bus (docblock) | 0 |
| `dn_capt_etat()` | `JAMAIS` / `VIVANT` / `MUET` / `ABSENT` | **`JAMAIS`** (identité BME680 ⛔ NON LUE) → `VIVANT` à **T+~60/90 s** | `JAMAIS` jusqu'à la 1ʳᵉ lecture, période **5 000 ms** |
| `dn_touch_ready()` | le GT911 a répondu et l'indev est branché | vrai (le contrôleur répond, ce sont les **transactions de donnée** qui ratent) | vrai |

### 🎯 CE QUE ÇA DÉCIDE POUR AC1.2

🔴 **LE CRITÈRE DE FIN EST `err_i2c` STABLE, ⛔ PAS L'ÉTAT CAPTEUR.**

- **`dn_capt_etat()` est DISQUALIFIÉ comme critère** : il vaut `JAMAIS` **à tout boot**, sain
  compris, pendant **jusqu'à 5 000 ms** (`DN_CAPT_PERIODE_MS`). L'attendre ajouterait **5 s
  d'attente à une carte qui va bien** ⇒ ⛔ **viole AC1.3** frontalement.
- **`err_i2c` stable est DISCRIMINANT, et c'est de l'arithmétique** : à **55,5 %** d'échec et
  **≈ 25 lectures/s**, une fenêtre propre de 1,5 s (≈ 37 lectures) a une probabilité
  `0,445 ^ 37 ≈ 6·10⁻¹⁴` d'arriver par hasard. ⇒ ⛔ ce n'est pas un minuteur déguisé.
- **Et il est déjà prouvé qu'il se FIGE à la reprise** : 950 → 950 pendant **+862 lectures**.
  C'est exactement le signal de fin, et il est **mesuré**, ⛔ pas supposé.

⚠️ **LE PIÈGE DU VIDE, ET IL EST DÉJÀ AU DOSSIER DU DÉPÔT** : une fenêtre d'observation sans
lectures ne mesure **rien**. ⇒ le critère exige **AUSSI** que `lectures` ait progressé d'au moins
N pendant la fenêtre. Sans ça, un tactile mort (`dn_touch_ready()` faux, `lectures` figé à 0,
`err_i2c` figé à 0) sortirait de l'état de démarrage **par un compteur immobile**, c'est-à-dire
en mesurant du vide.
⇒ le cas « tactile INDISPONIBLE » est traité **explicitement**, ⛔ pas par accident.

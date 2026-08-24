# AC2 — RE-TIR DU 2026-08-24

**Fichier** : `ac2-retir-2026-08-24.log`

## Comment il a été produit

```
tools/mesure_lhm_dn48.py --n 1000 --lot 50 --periode 1.0 --jeter 5
```
Lancé **depuis la tour** (`%LOCALAPPDATA%\Programs\Python\Python313\python.exe`), par UNC sur le
dépôt WSL. ⛔ **La carte n'est pas dans la boucle** : cette campagne mesure LHM et les interfaces,
pas la liaison.

- **Critère GELÉ AVANT** : cockpit `831f619` (2026-08-21T13:30:23Z). ✅ **Vérifié : aucun seuil n'a
  bougé depuis** (`git diff 831f619..HEAD` sur la story ne touche aucun des quatre).
- **`n` annoncé d'avance** : 1000 tirs par combinaison, 12 combinaisons, période 1,0 s.
- **Ordre ALTERNÉ** : `combos[r:] + combos[:r]`, rotation à chaque tour — AC2 l'exige.
- **Amorçage jeté** : 5 premiers tirs.
- **Sonde préalable** : 12/12 combinaisons OK, tour complet **636 ms** (< période).

## Pourquoi ce re-tir

Les six nombres de la campagne 3 étaient **MORTS** : leur instrument a été corrigé **deux fois**.
1ʳᵉ revue — `_cpu_ms` hissé hors des fenêtres mesurées, `murs` filtré sur les succès.
2ᵉ revue (2026-08-24) — **`bloc_cpu` filtré aussi** (il ne l'était pas, alors que le motif écrit
valait à l'identique pour le CPU, qui porte C1 et C2), et **garde de finitude sur `lire_sensor`**
(`json.loads` accepte `NaN` non quoté).

⚠️ **Ces deux correctifs poussent dans des SENS OPPOSÉS** sur le verdict : filtrer `bloc_cpu`
**augmente** le CPU par tir ; la garde `_fini` peut **disqualifier** `lire_sensor`. ⛔ Aucune
prédiction n'a été faite sur le classement — c'est écrit avant le tir.

## ⛔ Ce que ce tir NE mesure PAS

- **La tour n'est pas au repos contrôlé.** LHM tourne, l'agent non. Pas de témoin de charge de fond.
- **Ni la culture ni les unités** : `/data.json` rend `Value` formaté selon la culture (la tour est
  en français) — c'est un motif d'élimination **qui ne se lit pas dans ces colonnes**.
- **Ni la montée en N au-delà de 8** : `sensor_xN` est un POST **par sonde**.

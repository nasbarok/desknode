# `mesures/dn4-8/` — les relevés BRUTS d'AC4, gardés pour pouvoir RE-JUGER

## Pourquoi ce dossier existe

🔴 **Parce que le CSV du PREMIER tir d'AC4 n'était nulle part.** La revue de code du
2026-08-21 a corrigé `affichee()` (arrondi banquier → demi-haut, pour appeler la
quantification réelle du produit) — ce qui a rendu **caducs** les quatre pourcentages
publiés. Pour savoir de combien ils bougeaient, il aurait suffi de re-juger le CSV
d'origine. ⛔ **Il n'était pas dans le dépôt**, et il a fallu refaire un tir de 16 minutes.

⚠️ **Et re-juger n'aurait de toute façon PAS suffi**, ce qui est la deuxième leçon :
`affichee()` s'applique **à l'échantillonnage**, donc le CSV stocke des valeurs **déjà
quantifiées**. Un `--rejuger` aurait rejugé l'ancienne quantification.
⇒ **Un CSV ne sauve que ce qui se recalcule EN AVAL de lui.** C'est écrit ici pour que
personne ne croie qu'archiver le CSV rend tout tir rejouable.

## Ce qu'on peut faire avec

```bash
python3 tools/mesure_w2_dn48.py --rejuger mesures/dn4-8/w2-ac4-2026-08-21-retir.csv \
                                --periode-lhm 4.01
```

✅ **Re-jugeable** : les seuils C1/C2/C3, le dénominateur d'occasions, les σ, les
corrélations — tout ce que `juger()` et `analyser()` calculent **à partir** des colonnes.
⛔ **PAS re-jugeable** : la quantification elle-même, la cadence de LHM, l'espacement réel.

## Le tir

| Fait | Valeur |
|---|---|
| Date | **2026-08-21**, ~23:08 → ~23:25 (heure de la tour) |
| Motif | **re-tir** après la revue de code — l'instrument avait changé, donc les chiffres étaient morts |
| Instrument | `tools/mesure_w2_dn48.py`, commit **`d2a8d09`** |
| n | **957** échantillons · **0** lecture en échec · **1** recalage de cadence |
| Espacement **mesuré** dans `t_s` | **1,000 s** (⛔ pas supposé) |
| Cadence LHM **mesurée** | **4,01 s**, sur **4/4** sondes (médiane des médianes) |
| Régime | **AU REPOS** — décision owner. ⛔ La phase de charge n'est **pas** couverte |

⚠️ **`fan.top_out` et `fan.rear_out` sont dans le CSV mais ne sont PAS jugés** : ce sont les
deux canaux dont `disk.extraction_moy` est la moyenne. Ils sont là pour que les σ par canal
et les corrélations soient calculables — c'est précisément ce qui manquait quand §17.3 a
publié un σ et un `r` qu'aucun instrument commité ne produisait.

# `tests/` — POURQUOI IL EST VIDE, ET OÙ EST LA VÉRIFICATION

> Tranché par `dn4-24` le **2026-08-30**, voie **(b)** d'AC5.1.
> ⚠️ L'owner peut retenir la voie **(a)** à la revue — ce fichier dit alors ce qu'il
> faudrait poser, et ce que ça coûte.

## Le fait

`tests/` a été créé par `dn1-1` le **2026-08-14** et n'a jamais contenu qu'un
`.gitkeep` de **0 octet**. L'entrée de ledger qui le signale y dort depuis — non pas
parce que personne ne l'a lue, mais parce que **personne n'avait tranché**. Un
répertoire vide sans explication est indiscernable d'un oubli : on ne sait pas s'il
attend quelque chose ou s'il n'attend rien.

## La décision

**La vérification rejouable de ce dépôt, ce sont les gates de `tools/`.** Elles sont
**découvertes par glob** (`tools/verif_*.py`) et se passent toutes en une commande —
⛔ leur nombre n'est **pas** écrit ici, le runner l'imprime. *(Revue du 2026-09-02 :
cette ligne annonçait « 22 » depuis `dn4-24` alors que le glob en trouvait **27** —
un compte écrit se périme le jour où on ajoute une gate, c'est-à-dire le jour où il
compte. Depuis le 2026-09-02, `.github/workflows/gates.yml` les invoque à chaque
poussée : la phrase « rien ne les invoque » qui vivait ailleurs est morte.)*

```bash
bash tools/run_gates.sh
```

⛔ **Ce ne sont pas des tests unitaires déguisés.** Chacune relit une propriété du code
ou du dossier et la confronte à la source — et, pour la plupart, **se prouve par
MUTATION** : elle casse ce qu'elle garde et exige de se voir ROUGIR. Une gate qu'on n'a
jamais vue échouer ne prouve rien, et le dépôt a payé ce motif plusieurs fois
(`dn4-14` a épinglé du code **faux** avec une gate **verte**).

## Pourquoi la chaîne `build → flash → log` n'est PAS ici

Elle a besoin de **la carte**, et la carte n'est pas automatisable depuis ce poste :

- **le flash passe par Windows** — WSL sait *construire*, la branche Windows-only sait
  *flasher*, et `IDF_PATH` n'existe pas côté Windows ;
- **rendre le port à l'agent REBOOTE la carte**, ce qui change l'état mesuré ;
- **un `log` utile suppose une carte alimentée, réveillée et non occupée** par un soak
  en cours — `dn4-5` en tient un sur plusieurs jours.

⇒ Poser ici un « test » qui *suppose* la carte produirait un **rouge permanent** que
tout le monde apprendrait à ignorer. C'est pire que rien : une garde qu'on contourne
par habitude est une garde morte qui a l'air vivante.

## Ce qui remplirait `tests/` le jour où ça change

Deux conditions, et **elles sont mesurables** :

1. **un flash pilotable sans geste humain** depuis un runner (aujourd'hui : non — voir
   `README.md` § *Toolchain / build & flash*, voies A et C) ;
2. **une carte dédiée à la vérification**, distincte de celle qui porte les soaks.

Alors — et alors seulement — `tests/` accueillerait la chaîne `build → flash → log`
bout en bout : le binaire construit, flashé, et le premier bloc de console confronté à
ce que le firmware promet d'imprimer au boot.

## Ce que ce fichier remplace

`tests/.gitkeep`, 0 octet, sans un mot. ⛔ Il n'est pas revenu : un répertoire dont on
ne sait pas s'il attend quelque chose est un défaut de dossier, pas un détail de dépôt.

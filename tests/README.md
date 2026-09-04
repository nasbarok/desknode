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

> ⚠️ **ANNOTÉ LE 2026-09-04 (`dn5-4`) — DEUX DES TROIS PUCES CI-DESSUS SONT À CORRIGER,
> ET ELLES SONT DATÉES PLUTÔT QUE RÉÉCRITES.** Les deux visées sont la **1ʳᵉ** (« le flash
> passe par Windows ») et la **3ᵉ** (le soak) ; la **2ᵉ** — rendre le port à l'agent
> reboote la carte — n'a pas bougé.
> *(⚠️ Carte de lecture corrigée à la revue de code du 2026-09-04 : cet en-tête désignait
> « la troisième » pour la puce du port, qui est la deuxième, et l'item « 2. » ci-dessous
> porte bien sur la troisième puce. Dans un bloc dont l'unique fonction est de désigner
> des puces précises, s'en remettre à un renvoi faux revenait à ne rien désigner.)*
>
> **1. « le flash passe par Windows » — la moitié qui compte pour cette page tient, la
> moitié sur le flash, non.** ⛔ *Faux tel quel* : la boucle de travail **retenue** du
> `README.md` § *Toolchain / build & flash* flashe **depuis WSL**
> (`idf.py -p /dev/ttyACM0 flash monitor`) ; la voie qui flashe depuis Windows y est
> nommée **« secours, et cap à terme »**. ✅ *Vrai, et c'est ce qui fonde ce paragraphe* :
> **le BUILD, lui, est bien Linux/WSL sur les deux voies**, et `IDF_PATH` n'existe
> toujours pas côté Windows — ⚠️ **par ABSENCE d'installation, ⛔ pas par un essai qui
> aurait échoué**. La plateforme de build supportée est désormais **déclarée** dans
> [`CONTRIBUTING.md`](../CONTRIBUTING.md) § *Building the firmware* ; c'est là qu'elle
> fait foi, et cette page ⛔ ne la redouble pas.
>
> **2. « `dn4-5` en tient un sur plusieurs jours » — ⛔ IL N'Y A PLUS DE SOAK.** Mesuré
> par `dn5-1` le 2026-09-02, **sans ouvrir le port** : le dernier soak est **mort depuis
> le 2026-08-26 à 23:28:39**, et il n'avait vécu que **60 s**. Aggravant, mesuré aussi :
> il **n'est pas armable** par le lanceur livré — **0 occurrence** de `journal-soak` dans
> `tools/dn_agent_tour.ps1`. ⇒ l'argument « la carte est occupée par un soak » **n'a plus
> d'objet**. ⚠️ **Ce qui rend la carte indisponible reste vrai, mais pour un AUTRE
> motif** : un agent tient le port **en exclusif** depuis le 2026-09-02, et la carte est
> le module en service de l'auteur. La conclusion du paragraphe ne change pas ; **sa
> prémisse, si.**

⇒ Poser ici un « test » qui *suppose* la carte produirait un **rouge permanent** que
tout le monde apprendrait à ignorer. C'est pire que rien : une garde qu'on contourne
par habitude est une garde morte qui a l'air vivante.

## Ce qui remplirait `tests/` le jour où ça change

Deux conditions, et **elles sont mesurables** :

1. **un flash pilotable sans geste humain** depuis un runner (aujourd'hui : non — voir
   `README.md` § *Toolchain / build & flash*, voies A et C) ;
2. **une carte dédiée à la vérification**, distincte de celle qui porte l'usage réel.
   ⚠️ *(Reformulé le 2026-09-04 : cette ligne disait « celle qui porte **les soaks** », au
   présent, douze lignes sous l'annotation qui vient d'établir qu'il n'y en a plus. Ce qui
   monopolise la carte aujourd'hui, c'est l'agent qui tient le port et le fait qu'elle soit
   le module en service — ⛔ pas un soak. L'ancienne formule est nommée ici, ⛔ pas effacée.)*

Alors — et alors seulement — `tests/` accueillerait la chaîne `build → flash → log`
bout en bout : le binaire construit, flashé, et le premier bloc de console confronté à
ce que le firmware promet d'imprimer au boot.

## Ce que ce fichier remplace

`tests/.gitkeep`, 0 octet, sans un mot. ⛔ Il n'est pas revenu : un répertoire dont on
ne sait pas s'il attend quelque chose est un défaut de dossier, pas un détail de dépôt.

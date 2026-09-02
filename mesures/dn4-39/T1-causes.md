# dn4-39 / T1 — LES 6 ROUGES DE CI, RANGES PAR CAUSE

Mesure du 2026-09-02. Deux instruments, et ils ne voient PAS la meme chose :

- **clone neuf + `HOME` etranger** — `git clone --depth 1 file://~/projects/desknode dn`
  puis `HOME=/tmp/fakehome bash tools/run_gates.sh`. C'est la seule configuration
  disponible ici qui reproduit un runner. ⛔ SANS le `HOME` etranger la mesure est
  FAUSSE DANS LE SENS RASSURANT : trois de ces outils sortent du clone et
  atteignent `/home/nasbarok/projects/...`, qui existe sur cette machine
  (`docs/dn5-1-ecart-promesses.md` §5).
- **la LECTURE DU CODE** — et elle voit ce que le clone ne peut pas voir.

## Le tableau

| gate | cause | vue dans le clone ? | rc SANS son prerequis (avant `dn4-39`) |
|---|---|---|---|
| `verif_dossier_dn415.py`   | **A** — le cockpit n'est pas dans le clone     | oui | **1** — `BILAN : 1 OK, 1 KO` |
| `verif_ledger_dn416.py`    | **A**                                          | oui | **1** — `BILAN : 1 OK, 3 KO` + `ARRET` |
| `verif_veille_dn33.py`     | **B** — `managed_components/` est gitignore    | oui | **1** — `ECHEC : generateur amont introuvable` |
| `verif_harnais_dn413.py`   | **B**                                          | oui | **1** — `6 ECHEC(S) sur 27`, dont **5 FAUX** |
| `verif_hist_dn413.py`      | **B**                                          | oui | **1** — `Traceback` NU (`FileNotFoundError`) |
| `verif_dossier_d5_dn45.py` | **C** — chemins **ABSOLUS** de la machine      | **NON, elle y est VERTE** | **1** — `BILAN : 1 OK, 7 KO` |

**LES SIX RENDAIENT `1`. C'EST LE CONSTAT QUI DECIDE DE TOUT LE RESTE** : `1` est
aussi la valeur de leur ROUGE. Declarer `rc attendu = 1` dans la table
`NON_JOUABLES` de `run_gates.sh` aurait produit une declaration satisfaite AUSSI
BIEN par « le terrain manque » que par « j'ai trouve un defaut ». La regle (3)
du runner — la declaration est falsifiable — tombait A VIDE.

## Les trois causes, et aucune ne parle du code

**A — le cockpit de planification n'est pas clone.** C'est un depot PRIVE
(`~/projects/compagnon_project`). Deux gates le lisent par
`COCKPIT_DEFAUT = os.path.expanduser(...)` : `verif_dossier_dn415.py:168` et
`verif_ledger_dn416.py:148`. Un `HOME` etranger suffit a les faire rougir —
c'est pour ca qu'on les voit.

**B — `managed_components/` est gitignore** (`.gitignore:9`), pese 186 Mo
localement, et est repeuple par `idf.py reconfigure` (ESP-IDF `~5.5.0`).
Trois gates en dependent.

**C — LA PLUS DANGEREUSE, PARCE QU'ELLE EST INVISIBLE A LA MESURE.**
`verif_dossier_d5_dn45.py:47-48` code deux chemins **ABSOLUS** :
`/home/nasbarok/projects/desknode` et `/home/nasbarok/projects/compagnon_project`.
⛔ `HOME` n'y peut rien. Sur cette machine ils existent ⇒ **la gate est VERTE
dans le clone**. Sur un runner ils n'existent pas.

🔬 REPRODUIT au cadrage en pointant les deux constantes sur un chemin inexistant
(`mesures/dn4-39/T1-cause-C.txt`) :

    [KO ] .../sprint-status-desknode.yaml    ⛔ FICHIER INTROUVABLE
    [KO ] le balayage a bien trouve des occurrences   0 occurrence(s) ...
    BILAN : 1 OK, 7 KO                        (rc 1)

## La chasse a une AUTRE cause C — elle se LIT, elle ne s'attend pas

⛔ Un chemin absolu n'apparait dans AUCUNE mesure prise depuis ce poste. Balayage
des **27** gates :

    grep -nE '"/home/|/home/nasbarok'  tools/verif_*.py
      -> tools/verif_dossier_d5_dn45.py:47  DESKNODE = "/home/nasbarok/projects/desknode"
      -> tools/verif_dossier_d5_dn45.py:48  COCKPIT  = "/home/nasbarok/projects/compagnon_project"

    grep -n 'expanduser|Path.home\(\)|environ\[.HOME.\]'  tools/verif_*.py
      -> tools/verif_dossier_dn415.py:168   COCKPIT_DEFAUT = expanduser("~/projects/compagnon_project")
      -> tools/verif_ledger_dn416.py:148    COCKPIT_DEFAUT = expanduser("~/projects/compagnon_project")

    autres racines absolues / lettres de lecteur Windows : AUCUNE
      (seul bruit : `verif_source_lhm_dn48.py:299,325` — `/lpc/nct6792d/0/fan/1`
       est un IDENTIFIANT DE SONDE passe a un stub, ⛔ pas un chemin de fichier ;
       la gate est VERTE dans le clone.)

⇒ **UNE SEULE cause C dans les 27 gates**, et c'est celle qui etait deja nommee.
⚠️ Ce verdict vaut pour l'etat lu le 2026-09-02 : toute cause C future echappera
de la meme facon a la mesure du clone. Elle se **LIT DANS LE CODE**.

## Ce que la CI ne verra JAMAIS — et elle ne pretend pas le contraire (AC39.2.b)

Le rouge PRE-EXISTANT n'est **pas le meme rouge des deux cotes** :

| ou | ce que `verif_dossier_dn415.py` rend |
|---|---|
| poste de l'auteur (le cockpit est la) | **17 OK / 10 KO** — sur le **CONTENU** du cockpit |
| clone / runner (le cockpit est absent) | **1 OK / 1 KO**, et elle **s'arrete la** |

⇒ Ces **10 KO sont HORS de portee d'un runner**. La gate le DIT desormais dans sa
sortie de prerequis absent. ⛔ Elle ne pretend pas garder ce qu'elle ne peut pas
voir. Leur remede d'ancrage **par motif** appartient a `dn4-40`, inchange.

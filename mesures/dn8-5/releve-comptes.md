# dn8-5 — LE RELEVÉ **AU COMPTE**, gate par gate, AVANT / APRÈS

🔴 **LE COMPTE, ⛔ PAS LA COULEUR.** La seule gate rouge de ce dépôt est à `23 OK / 10 KO` :
une gate déjà rouge absorbe un KO de plus sans changer de couleur.

**Bornes** : `T0-borne-entree.txt` (passe du 2026-09-13, 11:37 → 11:55, `HEAD = d2e6330`, arbre
propre) · **`T5`** (passe d'arrivée, 2026-09-13, 12:39 → 13:14, même `HEAD`, les fichiers de la marche **indexés**, ⛔ aucun
commit). Les sorties brutes des deux passes (une par gate) sont restées sous le scratchpad de
session ; ce fichier en porte les comptes. Script : `T0-borne-entree.txt` § 4, plus un dernier bloc
qui joue `bash tools/run_gates.sh --cockpit` **après** les tirs isolés, ⛔ en parallèle.

⚠️ **ORDRE D'ÉCRITURE, DÉCLARÉ** : ce fichier est écrit **après** `T5` — c'est une mutation de ce
seul fichier, et les gates qui lisent les Markdown et les captures suivis (`dn52`, `dn63`, `dn415`,
`dn45`, `dn81`, `dn416`, la vitrine, la gate neuve) sont **re-jouées après son écriture** ; leurs
comptes sont rapportés avec la livraison, ⛔ pas réécrits ici (un compte écrit après sa mesure
serait une mesure qui n'a pas eu lieu).
⚠️ **UNE PREMIÈRE PASSE D'ARRIVÉE A ÉTÉ ARRÊTÉE** (lancée à 12:14, arrêtée à 12:15, pendant
`verif_campagne_dn440.py`) pour écrire la section « What belongs here » de `SECURITY.md` ⇒ ⛔
aucune mesure n'a chevauché cette écriture ; `T2` et `T3` ont été **rejoués** sur le texte livré, et
`T5` est la passe relancée ensuite. Contrôle : aucun processus `verif_*` ne survivait à l'arrêt, et
`git status --porcelain` ne portait **aucun** fichier hors index.

## ⛔ CE QUE CE RELEVÉ NE DIT PAS

- ⛔ **Que GitHub ACCEPTE les formulaires.** La gate neuve confronte les trois YAML aux règles que la
  documentation **écrit** (`T1` § 1). Elle ne voit ni la validation réelle — des mots interdits
  dans un label **que la documentation ne liste pas**, des labels « trop proches » décrits par
  l'exemple —, ni le **rendu du sélecteur** d'issues. Le dépôt est privé et rien n'est poussé.
- ⛔ **Que `validations.required` agit.** La documentation le réserve aux **dépôts publics** : la
  gate vérifie la **déclaration** sur 5 champs, ⛔ l'effet.
- ⛔ **Que le formulaire privé de failles est ATTEIGNABLE par un inconnu.** Le réglage n'existe que
  sur un dépôt public (API : **404** sur `desknode` privé, `T1` § 4) ; `SECURITY.md` le dit, daté.
  Ce qui est prouvé : l'emplacement reconnu, le lien de **ce** dépôt, l'interdiction du ticket
  public, et l'atteignabilité **depuis le dépôt** (vitrine, `CONTRIBUTING.md`, `config.yml`).
- ⛔ **Que PyYAML est sur le Python système du runner.** Étayé par la liste de paquets de l'image
  (`python3-yaml`), ⛔ mesuré sur aucun run. Sans lui la gate **échoue fermée** (`T2` § 3).
- ⛔ **Que le profil communautaire devient non nul.** Il rendait `null` à `T0` pour
  `code_of_conduct`, `issue_template`, `pull_request_template` ; il ne verra les fichiers qu'une
  fois poussés.
- ⛔ **Que la CI réelle, SANS cockpit, rend ces comptes.** Le « chemin CI » du § 6 est un clone
  `--depth 1` joué **sur ce poste**, où le chemin par défaut du cockpit **existe** : les gates qui le
  lisent l'ont trouvé (sur un runner elles rendent leur `rc=4` déclaré).
- ⛔ **Que la conduite reçoit un canal privé.** Elle n'en a **aucun**, par arbitrage owner (A1), et
  le code de conduite le dit : ce relevé ne mesure pas une absence qu'il a lui-même écrite.

## 1. LE COMPTE DE CHAQUE GATE — tir isolé, `T0` ⇄ `T5`

Instrument : chaque `tools/verif_*.py` du glob, joué seul (`--cockpit` quand la gate le déclare),
`timeout 900`. ⚠️ **Dix gates n'impriment aucune ligne `BILAN`** : leur compte est lu dans leur
propre forme de fin, et la forme est écrite dans la cellule (script `compte.py`, § 9).

| gate | `T0` (avant) | `T5` (après) | rc avant → après | durée avant → après |
|---|---|---|---|---|
| `verif_affiliation_dn65.py` | 23 OK, 0 KO | **23 OK, 0 KO** | 0 → 0 | 1.74 → 2.11 s |
| `verif_banc_langue_dn73.py` | 81 OK, 0 KO | **81 OK, 0 KO** | 0 → 0 | 2.49 → 2.42 s |
| `verif_bme680_retard_dn45.py` | 15 OK, 0 KO | **15 OK, 0 KO** | 0 → 0 | 0.04 → 0.05 s |
| `verif_boitier_dn64.py` | 29 OK, 0 KO | **29 OK, 0 KO** | 0 → 0 | 0.91 → 0.37 s |
| `verif_bom_dn61.py` | 24 OK, 0 KO | **24 OK, 0 KO** | 0 → 0 | 0.08 → 0.04 s |
| `verif_cablage_dn62.py` | 37 OK, 0 KO | **37 OK, 0 KO** | 0 → 0 | 0.08 → 0.11 s |
| `verif_campagne_dn440.py` | 62 OK, 0 KO | **62 OK, 0 KO** | 0 → 0 | 142.66 → 145.35 s |
| `verif_campagne_dn56.py` | 8 OK, 0 KO | **8 OK, 0 KO** | 0 → 0 | 763.75 → 776.70 s |
| `verif_courbe_dn413.py` | 58 OK, 0 KO *(« contrôles passent »)* | **58 OK, 0 KO *(« contrôles passent »)*** | 0 → 0 | 11.10 → 10.65 s |
| `verif_cumul_ambient_dn45.py` | 23 OK, 0 KO | **23 OK, 0 KO** | 0 → 0 | 1.35 → 1.07 s |
| `verif_d4_nvs_dn45.py` | 6 OK, 0 KO | **6 OK, 0 KO** | 0 → 0 | 0.38 → 0.33 s |
| `verif_decoupe_horloge_dn418.py` | 7 ✅ / 0 ❌ *(lignes, aucun BILAN)* | **7 ✅ / 0 ❌ *(lignes, aucun BILAN)*** | 0 → 0 | 6.78 → 6.47 s |
| `verif_demarrage_dn443.py` | 58 OK, 0 KO | **58 OK, 0 KO** | 0 → 0 | 0.84 → 0.64 s |
| `verif_dossier_d5_dn45.py` | 12 OK, 0 KO | **12 OK, 0 KO** | 0 → 0 | 1.21 → 1.17 s |
| `verif_dossier_dn415.py` | 23 OK, 10 KO | **23 OK, 10 KO** | 1 → 1 | 8.74 → 8.63 s |
| `verif_entree_dn82.py` | 45 OK, 0 KO | **45 OK, 0 KO** | 0 → 0 | 0.26 → 0.20 s |
| `verif_flash_dn72.py` | 30 OK, 0 KO | **30 OK, 0 KO** | 0 → 0 | 0.30 → 0.29 s |
| `verif_harnais_dn413.py` | 22 OK, 0 KO *(« contrôles passent »)* | **22 OK, 0 KO *(« contrôles passent »)*** | 0 → 0 | 9.65 → 8.19 s |
| `verif_harnais_dn81.py` | 28 OK, 0 KO | **28 OK, 0 KO** | 0 → 0 | 5.03 → 4.56 s |
| `verif_hist_dn413.py` | 56 OK, 0 KO *(« contrôles passent »)* | **56 OK, 0 KO *(« contrôles passent »)*** | 0 → 0 | 3.98 → 3.50 s |
| `verif_installeur_dn71.py` | 28 OK, 0 KO | **28 OK, 0 KO** | 0 → 0 | 0.27 → 0.21 s |
| `verif_instruments_dn423.py` | 163 OK, 0 KO | **163 OK, 0 KO** | 0 → 0 | 0.66 → 0.60 s |
| `verif_journal_soak_dn45.py` | 26 OK, 0 KO | **26 OK, 0 KO** | 0 → 0 | 0.10 → 0.09 s |
| `verif_langue_dalle_dn73.py` | 61 OK, 0 KO | **61 OK, 0 KO** | 0 → 0 | 0.14 → 0.14 s |
| `verif_langues_dn442.py` | 31 OK, 0 KO | **31 OK, 0 KO** | 0 → 0 | 0.89 → 0.65 s |
| `verif_ledger_dn416.py` | 36 OK, 0 KO | **36 OK, 0 KO** | 0 → 0 | 0.98 → 0.79 s |
| `verif_lhm_ps_dn83.py` | 26 OK, 0 KO | **26 OK, 0 KO** | 0 → 0 | 17.94 → 18.41 s |
| `verif_licences_dn52.py` | 34 OK, 0 KO | **34 OK, 0 KO** | 0 → 0 | 0.92 → 0.85 s |
| `verif_lissage_dn45.py` | 21 OK, 0 KO | **21 OK, 0 KO** | 0 → 0 | 0.22 → 0.15 s |
| `verif_miroir_horloge_dn418.py` | 18 ✅ / 0 ❌ *(lignes, aucun BILAN)* | **18 ✅ / 0 ❌ *(lignes, aucun BILAN)*** | 0 → 0 | 0.07 → 0.08 s |
| `verif_page_dn722.py` | 56 OK, 0 KO | **56 OK, 0 KO** | 0 → 0 | 0.13 → 0.17 s |
| `verif_paliers_dn441.py` | 42 OK, 0 KO | **42 OK, 0 KO** | 0 → 0 | 0.19 → 0.23 s |
| `verif_photos_dn63.py` | 28 OK, 0 KO | **28 OK, 0 KO** | 0 → 0 | 0.35 → 0.49 s |
| `verif_placement_dn74.py` | 42 OK, 0 KO | **42 OK, 0 KO** | 0 → 0 | 0.08 → 0.09 s |
| `verif_polices_dn440.py` | 11 OK, 0 KO | **11 OK, 0 KO** | 0 → 0 | 0.03 → 0.05 s |
| `verif_preconditions_dn76.py` | 55 OK, 0 KO | **55 OK, 0 KO** | 0 → 0 | 0.21 → 0.18 s |
| `verif_prerequis_dn75.py` | 51 OK, 0 KO | **51 OK, 0 KO** | 0 → 0 | 0.23 → 0.26 s |
| `verif_rebouclage_dn45.py` | 30 OK, 0 KO | **30 OK, 0 KO** | 0 → 0 | 2.62 → 3.07 s |
| `verif_reception_dn85.py` | *(absente)* | **16 OK, 0 KO** | — → 0 | — → 0.24 s |
| `verif_reprise_horloge_dn418.py` | 50 ✅ / 0 ❌ *(lignes, aucun BILAN)* | **50 ✅ / 0 ❌ *(lignes, aucun BILAN)*** | 0 → 0 | 0.10 → 0.13 s |
| `verif_selection_dn49.py` | 70 OK, 0 KO *(« contrôles passent »)* | **70 OK, 0 KO *(« contrôles passent »)*** | 0 → 0 | 0.06 → 0.10 s |
| `verif_serie_dn412.py` | 50 OK, 0 KO | **50 OK, 0 KO** | 0 → 0 | 1.53 → 1.62 s |
| `verif_source_lhm_dn48.py` | 46 [OK ], 0 [KO] *(« tous les controles passent »)* | **46 [OK ], 0 [KO] *(« tous les controles passent »)*** | 0 → 0 | 4.00 → 4.05 s |
| `verif_sr03.py` | NON-JOUABLE *(témoin absent)* | **NON-JOUABLE *(témoin absent)*** | 2 → 2 | 0.04 → 0.07 s |
| `verif_temoin_filtre_dn447.py` | 5 OK, 0 KO | **5 OK, 0 KO** | 0 → 0 | 1.81 → 1.77 s |
| `verif_veille_dn33.py` | 267 OK, 0 KO | **267 OK, 0 KO** | 0 → 0 | 6.87 → 7.71 s |
| `verif_verrou_lvgl_dn413.py` | 60 OK, 0 KO *(« contrôles passent »)* | **60 OK, 0 KO *(« contrôles passent »)*** | 0 → 0 | 16.37 → 16.84 s |
| `verif_vitrine_dn84.py` | 16 OK, 0 KO | **16 OK, 0 KO** | 0 → 0 | 0.08 → 0.08 s |
| `verif_xip_dn422.py` | 10 OK, 0 KO | **10 OK, 0 KO** | 0 → 0 | 0.04 → 0.03 s |

ECARTS DE COMPTE T0 ⇄ T5 : 1
  verif_reception_dn85.py : *(absente)* ⇒ 16 OK, 0 KO

⇒ **0 KO DE PLUS, GATE PAR GATE** : les **48** gates de `T0` rendent **exactement** leur compte de
`T0` à `T5` ; la seule différence de la table est la **49ᵉ**, `verif_reception_dn85.py`, neuve et
**verte** (`16 OK, 0 KO`). `verif_dossier_dn415.py` reste à **`23 OK / 10 KO`**, et ses lignes
`[KO ]` sont **identiques au caractère** à `T0` (diff des sorties capturées : vide).
⚠️ **Au compte, ⛔ au détail** : quatre gates ont des **détails** qui bougent, et c'est la marche —
`verif_licences_dn52.py` lit **224 liens / 19 fichiers** de prose (208 / 17 à `T0`), **8**
citations de section (6) et **23** marqueurs cités (20) ; `verif_harnais_dn81.py` a **7** fichiers
à son périmètre (6), **127** cibles d'ancre (122) et **4** couples (bloc, structure) jugés (3) —
le 4ᵉ est `tools/verif_reception_dn85.py→yaml`, **avec** son parseur. Mêmes libellés, mêmes
verdicts.

## 2. LES OUTILS QUI NE SONT PAS DES GATES

| outil | `T0` | `T5` |
|---|---|---|
| `node tools/banc_langue_dalle_dn73.mjs` | rc=0 · `BANC : 39 OK, 0 KO` | **rc=0 · `BANC : 39 OK, 0 KO`** |
| `node tools/banc_couverture_dn82.mjs` | rc=0 · 96/100 fonctions, 131/190 blocs | **rc=0 · 96/100 fonctions, 131/190 blocs** |
| `python3 tools/campagne_ctrl_dn440.py --cockpit …` | rc=0 · 15 cas, 11 sites vivants, 4 fiches, 0 échec | **rc=0 · identique** |
| `python3 tools/verif_ledger_dn416.py --cockpit … --manifeste` | rc=0 | **rc=0** (manifeste régénéré avant la passe : 395 lignes, « DEJA d'accord ») |
| `python3 tools/scission_readme_dn84.py --verifier --avant baf4265 --apres WORKTREE` | rc=0 · `IDENTIQUE` | **rc=0 · `IDENTIQUE`** |
| `python3 tools/stub_lhm_dn48.py --port 8085` | rc=1 (refus du port, par construction) | **rc=1** |
| `python3 -m py_compile …` · `bash -n tools/rendre-port.sh` | rc=0 · rc=0 | **rc=0 · rc=0** |
| `gh api repos/nasbarok/desknode/community/profile` | `code_of_conduct`, `issue_template`, `pull_request_template` = `null` | **identique** — ⛔ rien n'est poussé |
| **`python3 tools/inventaire_motif_dn53.py`** | classe 1 **0/0** · 2 **23 / 58** · 3 **5 / 5** · 4 **224 / 1 982** · 5 **4 / 20** · total **256 / 2 065** | classe 1 **0/0** · 2 **30 / 77** · 3 **5 / 5** · 4 **228 / 2 018** · 5 **4 / 21** · total **267 / 2 121** |

🔴 **`inventaire_motif_dn53.py` BOUGE, ET C'EST ÉCRIT PLUTÔT QUE TU.** Son motif
(`nasbarok|naoua|~/projects|wsl\.localhost`) mord sur **l'URL du dépôt**, que les fichiers neufs
écrivent en **absolu** (le dossier interdit les liens GitHub relatifs) :
- **classe 2, +7 fichiers / +19 sites** : `bug_report.yml`, `feature_request.yml`, `config.yml`, le
  modèle de PR, `SECURITY.md`, la vitrine et la gate neuve — un **login dans une URL**, ⛔ une
  machine nommée ; **classe 1 reste à 0** (« l'arbre du jour est SOLDE », `[OK ]`) ;
- **classe 4, +4 fichiers / +36 sites** : `T0`→`T3` de `mesures/dn8-5/` (captures et citations
  d'URL) ;
- **classe 5, +1 site** : `CONTRIBUTING.md` 8 ⇒ 9, le lien du formulaire de bug.
⚠️ **Les comptes que `CONTRIBUTING.md` publie de cet outil sont DATÉS** (2026-09-04 et 2026-09-05,
§ *Conventions in this repository*) : ils restent vrais **à leur date**, et ils ne sont ⛔ pas
réécrits. ⚠️ Une phrase de ce bloc dit, à propos des captures de `dn5-4`, *« hand-written text
never re-introduces the pattern »* ; `T1` (écrit à la main) porte des URL du dépôt, et les fichiers
publics neufs aussi. ⛔ Ce n'est **pas** une machine nommée — c'est l'identité du dépôt, que le
clone publié porte déjà —, mais la phrase **générale** ne dit plus tout ; elle n'est ⛔ pas
annotée dans cette marche (hors de ce que le dossier touche dans `CONTRIBUTING.md`), elle est
**nommée ici**.

## 3. `verif_campagne_dn56.py` — LA DURÉE, SOUS 900 s

| tir | `T0` | `T5` |
|---|---|---|
| isolé | **763,75 s** · 669 mutants / 22 cibles · `8 OK, 0 KO` | **776,70 s** · **690 mutants / 23 cibles** · `8 OK, 0 KO` |
| dans `run_gates.sh` | *(runner non joué à `T0`)* | **752 s** |
| clone `--depth 1` (chemin CI, § 6) | — | **767,30 s** · `8 OK, 0 KO` |

⇒ **+21 mutants** (ceux de la gate neuve), **< 900 s** sur les trois tirs, marge **≥ 123 s**.
⚠️ La durée isolée de `T0` a été prise **sous une charge légère** (lectures réseau de l'agent pendant
la passe, déclaré dans `T0`) : l'écart `T0`⇄`T5` (+13 s) ⛔ ne s'attribue pas aux seuls 21 mutants.
⚠️ *Annoté le 2026-09-13 après revue, la ligne ci-dessus ⛔ non effacée* : la gate neuve porte
désormais **38** mutants (+17). Leur coût dans `dn56` ⛔ **n'est pas remesuré ici** (consigne :
seuls les tests des fichiers édités) — le tir de `T2` joue les 38 un par un, et la vérification
complète est faite côté coordinateur.

## 4. LA PASSE ENTIÈRE — `bash tools/run_gates.sh --cockpit`

```
BILAN : 47 VERTE, 1 ROUGE, 1 NON-JOUABLE sur 49 gates (1012s)
RC_RUN_GATES=1  duree mur 1013 s
  [ROUGE      ] tools/verif_dossier_dn415.py           rc=1      9s   (23 OK / 10 KO, pré-existant)
  [NON-JOUABLE] tools/verif_sr03.py                    rc=2   (attendu) temoin absent : tools/fixtures/AN4545.pdf
  [VERTE      ] tools/verif_reception_dn85.py          rc=0      0s
```

⇒ la passe **est allée au bout** (le runner de `dn8-4` avait été tué par le harnais de session).
⚠️ **Il n'a PAS été joué à `T0`** : la comparaison au compte est celle du § 1 (tir isolé), et la
couleur de la passe est **cohérente** avec elle — 48 gates de `T0` : 46 V / 1 R / 1 NJ (même
répartition qu'au `T6` de `dn8-4`) ⇒ `T5` : **47 V / 1 R / 1 NJ sur 49**.

## 5. `AC8.5.6` — LES TROIS FICHIERS VOISINS, ET LES EMPREINTES

```
                                                                    T0    T5
a32e2944977d8009c98f98a8ffd6c73f474313569af3f9b133944ae7ab73e581  .github/workflows/cla.yml       ==    ==
00f194c9d459caca3205f53c294dc8863aef4b4e587d6ba0fd32c4156bd9566e  .github/workflows/gates.yml     ==    ==
a0d5bfe53d7bda13a42cb8e585ce1c445962fde059eca76f2369809842f0d5b7  .github/cla-signatures.json     ==    ==
```

⇒ **`sha256` IDENTIQUES** à `T0` (relus avant **et** après la passe `T5`).

| empreinte | `T0` avant ⇄ après | `T5` avant ⇄ après tirs isolés ⇄ après `run_gates` |
|---|---|---|
| desknode, contenu suivi | `fe8f410124f4b678` ⇄ idem | `1270b57ba31fb5bc` ⇄ idem ⇄ idem |
| desknode, index (`git ls-files -s`) | `0a21f91955ff42c6` ⇄ idem | `c7de5ec62b20445f` ⇄ idem ⇄ idem |
| cockpit, `implementation-artifacts` suivis | `87373bdb64bb5f4c` ⇄ idem | `1e05306ada8151a1` ⇄ idem ⇄ idem |

⇒ **⛔ aucune passe n'a chevauché une mutation** (empreintes stables sur chacune).
⇒ **L'empreinte HORS fichiers de la marche est IDENTIQUE** — blobs de `git ls-tree -r d2e6330` ⇄
blobs de l'index, en excluant les 13 fichiers publics et la gate de la marche et `mesures/dn8-5/` :
**`7996d7ffa9a8a924` ⇄ `7996d7ffa9a8a924`, 820 fichiers**. ⛔ Ni `firmware/`, ni `agent/`, ni
`installeur/`, ni le texte de `CLA.md`.
⚠️ *Annoté le 2026-09-13 après revue, la phrase ci-dessus ⛔ non effacée* : « 13 fichiers publics
**et** la gate » est **faux au compte**. L'ensemble exclu par le script comptait **13 fichiers au
total** : **12 fichiers publics** (6 neufs : 3 YAML, le modèle de PR, `SECURITY.md`,
`CODE_OF_CONDUCT.md` ; 6 modifiés : `CONTRIBUTING.md`, `README.md`, `LICENSING.md`,
`THIRD-PARTY.md`, `CHANGELOG.md`, `docs/roadmap.md`) **+ la gate**. L'empreinte, elle, est juste :
elle a été calculée sur cet ensemble-là.

## 6. LE CHEMIN DE LA CI — clone `--depth 1`, gate par gate, BASE ⇄ MARCHE

Deux copies jetables **construites de la même façon** (`git archive d2e6330` ⇄ les fichiers de
l'index), chacune **commitée**, puis `git clone --depth 1 file://…` et `origin` posé sur
`https://github.com/nasbarok/desknode.git`. Toutes les gates jouées **sans** `--cockpit`, hors
`dn56`/`dn440` (durée ; `dn56` jouée à part sur la marche, § 3).

- **47 gates IDENTIQUES** BASE ⇄ MARCHE (rc et `BILAN`), dont `verif_licences_dn52.py` **`33 OK,
  0 KO`** des deux côtés, `verif_vitrine_dn84.py` **`16 OK, 0 KO`**, `verif_dossier_dn415.py`
  **`23 OK, 10 KO`** ;
  ⚠️ *Annoté le 2026-09-13 après revue, la puce ci-dessus ⛔ non effacée* : **faux au compte**. Le
  script a joué **47 gates** (les 49 du glob moins `dn56` et `dn440`), et `ci.txt` rend **45**
  `IDENTIQUE`, **1** `NEUVE`, **1** `⛔ ECART` (recompté par `grep -c` sur la sortie) ⇒ **45 gates
  identiques**, ⛔ 47 ;
- **1 NEUVE** : `verif_reception_dn85.py` **`16 OK, 0 KO`** sur le clone — ⛔ elle ne lit aucun
  historique ;
- **1 ÉCART, ET C'EST UN ARTEFACT DU BANC, NOMMÉ** : `verif_harnais_dn81.py` rend **`27 OK, 1 KO`**
  sur la BASE et **`28 OK, 0 KO`** sur la MARCHE. Le KO est `(c2a) chaque cible d'ancre 📍 est
  ATTEIGNABLE` — **5 ancres mortes, les 5 de la section `dn8-5` du ledger** (`SECURITY.md`,
  `verif_reception_dn85.py`, `CODE_OF_CONDUCT.md`, `T3`) : le cockpit **vivant** porte déjà ces
  ancres, et la BASE n'a pas leurs fichiers. ⛔ Ce n'est pas une régression : la MARCHE est au compte
  de `T0`.
⚠️ **CE QUE CE CHEMIN NE SIMULE PAS** : un runner **sans** cockpit. Sur ce poste, le chemin par défaut
du cockpit existe, et les gates qui le lisent l'ont trouvé ; sur `ubuntu-latest` elles rendent leur
`rc=4` déclaré (`NON_JOUABLES`). Ni la présence de PyYAML sur le runner (ledger, `dn8-8`).

## 7. AUCUN MUTANT EXISTANT RENDU INAPPLICABLE — ET LA GATE NEUVE

- **`verif_campagne_dn56.py`** : `8 OK, 0 KO` à `T5` — **690 mutants** confrontés, *« aucun mutant
  devenu MUET »*, *« tout mutant rouge a bien imprimé un BILAN »*, *« chaque mutant vise un
  contrôle »*.
- ⚠️ **`dn56` ⛔ NE COMPARE PAS la cible vue à la cible déclarée** ⇒ les gates **d'autres sujets** qui
  lisent un fichier que la marche **modifie** ont été rejouées **BASE ⇄ MARCHE**, sur deux copies
  jetables construites à l'identique (`origin` GitHub), nominal **et** chaque mutant : même rc, même
  `BILAN`, **mêmes libellés `[KO ]` à colonne fixe** `[7:65]` :

```
  verif_licences_dn52         41 tir(s) (nominal + mutants) · 0 ecart(s) BASE ⇄ MARCHE
  verif_photos_dn63           33 tir(s) (nominal + mutants) · 0 ecart(s) BASE ⇄ MARCHE
  verif_boitier_dn64          36 tir(s) (nominal + mutants) · 0 ecart(s) BASE ⇄ MARCHE
  verif_affiliation_dn65      39 tir(s) (nominal + mutants) · 0 ecart(s) BASE ⇄ MARCHE
  verif_installeur_dn71       41 tir(s) (nominal + mutants) · 0 ecart(s) BASE ⇄ MARCHE
  verif_prerequis_dn75        32 tir(s) (nominal + mutants) · 0 ecart(s) BASE ⇄ MARCHE
  verif_vitrine_dn84          17 tir(s) (nominal + mutants) · 0 ecart(s) BASE ⇄ MARCHE
BILAN BASE ⇄ MARCHE : 239 tir(s), 0 ecart(s)
```

  ⇒ en particulier les mutants ancrés dans `CONTRIBUTING.md` (`dn52` 9·10·11·12·13·14·27·35·37·39·40,
  `dn63` 32) et dans `CHANGELOG.md`/`docs/roadmap.md` rougissent **sur le même contrôle** qu'avant.
  Et `verif_vitrine_dn84.py` : **16 mutants, cible vue == cible déclarée** (même banc que `T2`).
- **La gate neuve** : `16 OK, 0 KO` ; **21 mutants, cible vue == cible déclarée sur les 21** ;
  ⚠️ *annoté le 2026-09-13 après revue : 38 mutants depuis, cible vue == déclarée sur les 38 (§ 10)* ;
  PyYAML masqué ⇒ `11 OK, 5 KO` rc=1 (nominal) et `10 OK, 6 KO` rc=1 (`--mutant 9`) ; `--help` et
  `--liste-mutants` sans PyYAML rc=0 ; mutant 999 rc=2 ; ancre absente **et** état inchangé ⇒ rc=3
  **avec** `BILAN` — tout dans `T2`. Au périmètre de `verif_harnais_dn81.py` : `(c1d)` 7 fichiers,
  `(c3b)` le couple `→yaml` **avec** parseur.

## 8. LE COCKPIT, ET AUCUNE LIGNE DE PROSE EFFACÉE

- **Tracker** : `dn8-5` `backlog` ⇒ **`review`**, état précédent **nommé en tête**, ligne d'origine
  gardée en queue du commentaire ; `yaml.safe_load` ⇒ **102 clés**, `dn8-5 = review`.
- **Ledger** : section **neuve en queue** `## Deferred from: dn8-5 — …` — **5 entrées** (3 `PORTÉE`
  porteur `dn8-8-la-bascule-et-ce-qu-elle-rend-possible`, 2 `CONNAISSANCE`) ;
  `git diff --numstat` du ledger : **+89 lignes, 0 supprimée**. Manifeste `--en-place` ⇒ **395 lignes**, puis
  `verif_ledger_dn416.py --cockpit` **`36 OK, 0 KO`**.
- **Prose** — chaque ligne des fichiers modifiés à `d2e6330` est **présente** dans le fichier livré
  (multiensemble) :

| fichier | lignes base ⇒ livré | lignes de base absentes |
|---|---|---|
| `CONTRIBUTING.md` | 879 ⇒ 904 | **0** |
| `README.md` | 72 ⇒ 79 | **0** |
| `LICENSING.md` | 126 ⇒ 135 | **0** |
| `THIRD-PARTY.md` | 102 ⇒ 130 | **0** |
| `CHANGELOG.md` | 831 ⇒ 870 | **0** |
| `docs/roadmap.md` | 158 ⇒ 159 | **1 — la ligne `dn8`, AMENDÉE** : son ancien état est gardé **barré**, mot pour mot (`~~**eight stories; `dn8-1` to `dn8-4` shipped …**~~`), suivi du neuf daté |
| `.github/workflows/cla.yml` · `gates.yml` · `cla-signatures.json` | inchangés | **0** |

## 9. LES SCRIPTS DE BANC (sous le scratchpad de session, ⛔ versés comme fichiers)

- `passe.sh` (verse dans `T0-borne-entree.txt` § 4) ; `passe-apres.sh` = `passe.sh` + le bloc
  `run_gates.sh` du § 4 ;
- `compte.py T0 T5` — la table du § 1, lue dans les sorties capturées ;
- `base_marche.sh` — le § 7 ; `ci.sh` — le § 6 ;
- `temoins.py`, `t2.sh`, `t3.py` — versés **en annexe** de `T2` et `T3`.

## 10. ⚠️ AJOUTÉ LE 2026-09-13 APRÈS LA REVUE DU COORDINATEUR — CE QUI A CHANGÉ APRÈS `T5`

⛔ **Les §§ 1-9 mesurent l'arbre AVANT les correctifs de revue** : leurs empreintes, leurs durées et
leur passe entière ⛔ ne sont pas rejouées ici (consigne : seuls les tests des fichiers édités ; la
vérification complète est faite côté coordinateur).

- **La gate neuve** : **16 contrôles, 38 mutants** (21 ⇒ 38). Six règles de `(c2)(c3)(c4)(c5)` et trois
  propriétés de `(c8)` n'étaient épinglées par **aucun** mutant (démontré par la revue) ; `(c9)(c10)`
  ne voyaient pas « within a week », « within 72h », « We'll respond within two business days » ;
  `(c3)` n'exigeait pas le renvoi du bug report vers `SECURITY.md` ; `(c8)` lisait l'attribution
  jusqu'à la fin du fichier ; `(c1)(c2)` codaient en dur leurs deux formulaires ; `(c12)` sautait tout
  lien sans `#` ; `(c4)` lisait « no sla » dans « no slack ». ⇒ 17 mutants neufs, chacun **replante**
  sa faute. 🔴 **Et un mutant existant est devenu VERT** : le 19 videait `CIBLES[1]` (`c3`), que les
  mutants 25 et 33 visent désormais aussi ⇒ il est **réécrit** (retirer `c13` de toutes les cibles).
  Cible vue == cible déclarée sur les 38 : `T2` § 2.
- **`config.yml`** : `blank_issues_enabled: true` (défaut de GitHub) ; `(c5)` exige un booléen
  explicite.
- **Fichiers publics touchés par les correctifs** : `.github/ISSUE_TEMPLATE/bug_report.yml`,
  `config.yml`, `.github/pull_request_template.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`,
  `THIRD-PARTY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `docs/roadmap.md` ; records : `T1`, `T2`, `T3`,
  ce fichier ; cockpit : ledger (entrées *(i)(ii)(iii)*), manifeste, tracker.
- **Gates rejouées après les correctifs** (celles qui lisent les fichiers édités) : voir le rapport de
  livraison ; ⛔ pas réécrites ici, pour la même raison qu'au § 9 de `dn8-4`.

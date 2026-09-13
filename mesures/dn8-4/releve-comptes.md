# dn8-4 — LE RELEVÉ **AU COMPTE**, gate par gate, AVANT / APRÈS

🔴 **LE COMPTE, ⛔ PAS LA COULEUR.** La seule gate rouge de ce dépôt est à `23 OK / 10 KO` :
une gate déjà rouge absorbe un KO de plus sans changer de couleur.

**Bornes** : `T0-borne-entree.txt` (passe du 2026-09-13, 01:12 → 01:46, `HEAD = baf4265`,
arbre propre) · **`T5`** (passe d'arrivée, 02:06 → 02:40, même `HEAD`, les 30 fichiers de la marche
**indexés**). Les sorties brutes des deux passes (une par gate) sont restées sous le scratchpad de
session ; ce fichier en porte les comptes.

⚠️ **ORDRE D'ÉCRITURE, DÉCLARÉ** : ce fichier est posé **avant** la passe d'arrivée `T5` (une
ancre du ledger le vise), et ses tableaux sont versés **après** elle. ⇒ les gates qui lisent les
Markdown suivis sont **re-jouées après l'écriture** (§ 7).

## ⛔ CE QUE CE RELEVE NE DIT PAS

- ⛔ **Qu'un inconnu comprend DeskNode en moins de quinze secondes** (`AC8.4.3`). Ce qui est
  prouvé est l'**ordre** de lecture statué, relevé dans le HTML que GitHub rend (`T4`) et gardé
  par `tools/verif_vitrine_dn84.py` ; le verdict *compris* est **l'œil d'un inconnu**, et un
  inconnu n'existe qu'après la bascule. **NON COCHÉ**, déclaré au ledger (porteur `dn8-8`).
- ⛔ **Que les pointeurs datés de `hardware/*.md` sont justes** : ils citent le `README.md` à des
  dates où il était le journal, et ils sont **laissés en place**. Ce sont des citations datées —
  de l'historique —, ⛔ pas des renvois à suivre aujourd'hui.
- ⛔ **Que les photos s'affichent sur github.com** : le dépôt est privé, et le remote a
  **50 commits** de retard (`T1` (d)).
- ⛔ **Que le transport SSH marche ou non** : il n'a pas été atteint depuis ce poste (`T1` (d)).
- ⛔ **Que la vitrine est juste au-delà de ce qu'elle garde** : « 12 mutants, 12 vus rougir »
  prouve `mutant ⇒ rouge`, ⛔ pas `contrôle ⇒ couvert`. Un contrôle qui rougit sur **plusieurs**
  fautes n'est vu rougir que sur **une**.
- ⚠️ *Ajouté le 2026-09-13 après revue* — ⛔ **les affirmations de la vitrine qu'AUCUNE gate ne
  garde**, nommées plutôt que tues : *la page d'installation s'ouvre en anglais, le français à un
  clic* · *LibreHardwareMonitor est optionnel, l'agent l'attend 5 minutes par défaut, et
  l'installer exige des droits administrateur (driver noyau signé, tâche planifiée élevée)* ·
  *l'installeur ne demande aucun droit administrateur* · *toute la pile n'a été éprouvée que sur
  une carte*. Elles sont **tirées du journal**, où d'autres gates gardent parfois leur source
  (`verif_prerequis_dn75.py`, `verif_banc_langue_dn73.py`) — ⛔ mais aucune ne relit **leur
  phrase anglaise**, et une réécriture qui les contredirait laisserait toutes les gates vertes.

## 1. LE COMPTE DE CHAQUE GATE — tir isolé, `T0` ⇄ `T5`

Instrument : chaque `tools/verif_*.py` du glob, joué seul (`--cockpit` quand la gate le déclare),
`timeout 900`. ⚠️ **Dix gates n'impriment aucune ligne `BILAN`** : leur compte est lu dans leur
propre forme de fin, et la forme est écrite dans la cellule.

| gate | `T0` (avant) | `T5` (après) | rc avant → après | durée avant → après |
|---|---|---|---|---|
| `verif_affiliation_dn65.py` | 23 OK, 0 KO | **22 OK, 1 KO** ⚠️ → **23 OK, 0 KO** après correctif (§ 3) | 0 → 1 | 1.92 → 2.07 s |
| `verif_banc_langue_dn73.py` | 81 OK, 0 KO | **81 OK, 0 KO** | 0 → 0 | 2.50 → 2.46 s |
| `verif_bme680_retard_dn45.py` | 15 OK, 0 KO | **15 OK, 0 KO** | 0 → 0 | 0.04 → 0.06 s |
| `verif_boitier_dn64.py` | 29 OK, 0 KO | **29 OK, 0 KO** | 0 → 0 | 0.80 → 0.40 s |
| `verif_bom_dn61.py` | 24 OK, 0 KO | **24 OK, 0 KO** | 0 → 0 | 0.05 → 0.08 s |
| `verif_cablage_dn62.py` | 37 OK, 0 KO | **37 OK, 0 KO** | 0 → 0 | 0.16 → 0.08 s |
| `verif_campagne_dn440.py` | 62 OK, 0 KO | **62 OK, 0 KO** | 0 → 0 | 142.24 → 143.51 s |
| `verif_campagne_dn56.py` | 8 OK, 0 KO | **8 OK, 0 KO** | 0 → 0 | 733.79 → 746.76 s |
| `verif_courbe_dn413.py` | 58 OK, 0 KO *(« contrôles passent »)* | **58 OK, 0 KO *(« contrôles passent »)*** | 0 → 0 | 11.62 → 11.19 s |
| `verif_cumul_ambient_dn45.py` | 23 OK, 0 KO | **23 OK, 0 KO** | 0 → 0 | 1.26 → 1.32 s |
| `verif_d4_nvs_dn45.py` | 6 OK, 0 KO | **6 OK, 0 KO** | 0 → 0 | 0.43 → 0.32 s |
| `verif_decoupe_horloge_dn418.py` | 7 ✅ / 0 ❌ *(lignes, aucun BILAN)* | **7 ✅ / 0 ❌ *(lignes, aucun BILAN)*** | 0 → 0 | 7.21 → 7.31 s |
| `verif_demarrage_dn443.py` | 58 OK, 0 KO | **58 OK, 0 KO** | 0 → 0 | 0.69 → 0.66 s |
| `verif_dossier_d5_dn45.py` | 12 OK, 0 KO | **12 OK, 0 KO** | 0 → 0 | 1.16 → 1.17 s |
| `verif_dossier_dn415.py` | 23 OK, 10 KO | **23 OK, 10 KO** | 1 → 1 | 8.23 → 8.69 s |
| `verif_entree_dn82.py` | 45 OK, 0 KO | **45 OK, 0 KO** | 0 → 0 | 0.17 → 0.19 s |
| `verif_flash_dn72.py` | 30 OK, 0 KO | **30 OK, 0 KO** | 0 → 0 | 0.21 → 0.26 s |
| `verif_harnais_dn413.py` | 22 OK, 0 KO *(« contrôles passent »)* | **22 OK, 0 KO *(« contrôles passent »)*** | 0 → 0 | 9.66 → 8.64 s |
| `verif_harnais_dn81.py` | 28 OK, 0 KO | **28 OK, 0 KO** | 0 → 0 | 4.85 → 4.94 s |
| `verif_hist_dn413.py` | 56 OK, 0 KO *(« contrôles passent »)* | **56 OK, 0 KO *(« contrôles passent »)*** | 0 → 0 | 3.85 → 4.13 s |
| `verif_installeur_dn71.py` | 28 OK, 0 KO | **28 OK, 0 KO** | 0 → 0 | 0.24 → 0.28 s |
| `verif_instruments_dn423.py` | 163 OK, 0 KO | **163 OK, 0 KO** | 0 → 0 | 0.70 → 0.67 s |
| `verif_journal_soak_dn45.py` | 26 OK, 0 KO | **26 OK, 0 KO** | 0 → 0 | 0.12 → 0.08 s |
| `verif_langue_dalle_dn73.py` | 61 OK, 0 KO | **61 OK, 0 KO** | 0 → 0 | 0.13 → 0.14 s |
| `verif_langues_dn442.py` | 31 OK, 0 KO | **31 OK, 0 KO** | 0 → 0 | 0.80 → 0.69 s |
| `verif_ledger_dn416.py` | 36 OK, 0 KO | **36 OK, 0 KO** | 0 → 0 | 0.92 → 0.94 s |
| `verif_lhm_ps_dn83.py` | 26 OK, 0 KO | **26 OK, 0 KO** | 0 → 0 | 17.71 → 18.61 s |
| `verif_licences_dn52.py` | 34 OK, 0 KO | **34 OK, 0 KO** | 0 → 0 | 1.04 → 0.97 s |
| `verif_lissage_dn45.py` | 21 OK, 0 KO | **21 OK, 0 KO** | 0 → 0 | 0.18 → 0.25 s |
| `verif_miroir_horloge_dn418.py` | 18 ✅ / 0 ❌ *(lignes, aucun BILAN)* | **18 ✅ / 0 ❌ *(lignes, aucun BILAN)*** | 0 → 0 | 0.13 → 0.09 s |
| `verif_page_dn722.py` | 56 OK, 0 KO | **56 OK, 0 KO** | 0 → 0 | 0.18 → 0.16 s |
| `verif_paliers_dn441.py` | 42 OK, 0 KO | **42 OK, 0 KO** | 0 → 0 | 0.18 → 0.19 s |
| `verif_photos_dn63.py` | 28 OK, 0 KO | **28 OK, 0 KO** | 0 → 0 | 0.45 → 0.38 s |
| `verif_placement_dn74.py` | 42 OK, 0 KO | **42 OK, 0 KO** | 0 → 0 | 0.08 → 0.11 s |
| `verif_polices_dn440.py` | 11 OK, 0 KO | **11 OK, 0 KO** | 0 → 0 | 0.03 → 0.03 s |
| `verif_preconditions_dn76.py` | 55 OK, 0 KO | **55 OK, 0 KO** | 0 → 0 | 0.23 → 0.18 s |
| `verif_prerequis_dn75.py` | 51 OK, 0 KO | **51 OK, 0 KO** | 0 → 0 | 0.23 → 0.29 s |
| `verif_rebouclage_dn45.py` | 30 OK, 0 KO | **30 OK, 0 KO** | 0 → 0 | 2.91 → 3.16 s |
| `verif_reprise_horloge_dn418.py` | 44 ✅ / 0 ❌ *(lignes, aucun BILAN)* | **44 ✅ / 0 ❌ *(lignes, aucun BILAN)*** | 0 → 0 | 0.10 → 0.15 s |
| `verif_selection_dn49.py` | 70 OK, 0 KO *(« contrôles passent »)* | **70 OK, 0 KO *(« contrôles passent »)*** | 0 → 0 | 0.08 → 0.08 s |
| `verif_serie_dn412.py` | 50 OK, 0 KO | **50 OK, 0 KO** | 0 → 0 | 1.65 → 1.77 s |
| `verif_source_lhm_dn48.py` | 46 OK, 0 KO *(lignes `[OK]`, aucun BILAN)* | **46 OK, 0 KO *(lignes `[OK]`, aucun BILAN)*** | 0 → 0 | 4.03 → 4.03 s |
| `verif_sr03.py` | *(aucun compte imprime)* | ***(aucun compte imprime)*** | 2 → 2 | 0.07 → 0.08 s |
| `verif_temoin_filtre_dn447.py` | 5 OK, 0 KO | **5 OK, 0 KO** | 0 → 0 | 1.69 → 1.71 s |
| `verif_veille_dn33.py` | 267 OK, 0 KO | **267 OK, 0 KO** | 0 → 0 | 7.23 → 7.88 s |
| `verif_verrou_lvgl_dn413.py` | 60 OK, 0 KO *(« contrôles passent »)* | **60 OK, 0 KO *(« contrôles passent »)*** | 0 → 0 | 16.78 → 17.24 s |
| `verif_vitrine_dn84.py` | ⛔ n'existait pas | **12 OK, 0 KO** 🆕 | — → 0 | — → 0.06 s |
| `verif_xip_dn422.py` | 10 OK, 0 KO | **10 OK, 0 KO** | 0 → 0 | 0.04 → 0.06 s |

⇒ **0 KO de plus, gate par gate, sur 47 gates** — hors `verif_affiliation_dn65.py`, dont le KO de
`T5` est **causé par cette marche** et **soldé** (§ 3). `verif_dossier_dn415.py` reste à
**`23 OK / 10 KO`**, et ses **23 lignes `[OK]`/`[KO]` sont identiques au caractère** entre `T0` et
`T5` (`diff` vide) : ⛔ aucun KO absorbé en silence, ⛔ aucun fantôme neuf.

## 2. LA PASSE ENTIÈRE — `bash tools/run_gates.sh --cockpit`

| | `T0` | `T5` |
|---|---|---|
| bilan | **45 VERTE, 1 ROUGE, 1 NON-JOUABLE sur 47** · 996 s | **45 VERTE, 2 ROUGE, 1 NON-JOUABLE sur 48** · 1 009 s |
| les ROUGES | `verif_dossier_dn415.py` | `verif_affiliation_dn65.py` (§ 3) · `verif_dossier_dn415.py` |
| la NON-JOUABLE | `verif_sr03.py` (témoin absent, `rc=2` attendu) | idem |
| `verif_vitrine_dn84.py` | ⛔ n'existait pas | **VERTE**, jouée — ⛔ **pas** déclarée NON-JOUABLE (stdlib seule, aucun cockpit) |
| `verif_campagne_dn56.py` dans la passe | **740 s** | **747 s** |
| empreinte suivie avant ⇄ après | `50e51d072d8a5b32` ⇄ `50e51d072d8a5b32` | `c93db9b2a2faf1c2` ⇄ `c93db9b2a2faf1c2` |
| empreinte cockpit avant ⇄ après | `0308cdd5cf402fe9` ⇄ `0308cdd5cf402fe9` | `1343ec27f5601007` ⇄ `1343ec27f5601007` |

⇒ ⛔ **aucune passe n'a chevauché une mutation** : les deux empreintes sont identiques avant et après
chacune, et la quiescence était relevée avant de lancer.

> ⚠️ **ANNOTÉ LE 2026-09-13 APRÈS REVUE — LA PHRASE CI-DESSUS EST TROP LARGE, ET ELLE N'EST ⛔ PAS
> EFFACÉE.** La production des deux photos (`T2`, horodatée **01:34:57**) a tourné **pendant** la
> passe `T0` (01:12:24 → 01:46:44). Elle écrivait **sous le scratchpad**, ⛔ pas dans l'arbre —
> d'où des empreintes identiques —, et le brouillon de la vitrine et de la gate a de même été joué
> dans un clone jetable pendant cette passe. ⛔ **Ce que ce chevauchement a pu affecter** : les
> **durées** de `T0`, et d'abord celle de `verif_campagne_dn56.py` (**733,79 s** isolé, **740 s**
> dans la passe), mesurées sous une **charge concurrente** — deux réductions de JPEG de
> 10-11 Mo et quelques gates d'une seconde, sur une machine de 16 cœurs. ⇒ la marge budgétaire
> de `T0` est un chiffre **sous charge**, ⛔ pas au repos ; les **comptes** (`N OK / M KO`),
> eux, ne dépendent pas du temps.

## 3. 🔴 LE ROUGE DE `T5` — ⛔ LES GATES D'UN AUTRE SUJET ROUGISSENT SUR CE QUE CETTE MARCHE ÉCRIT

`verif_affiliation_dn65.py (c15)` — *« ⛔ aucun jalon CHIFFRÉ dans tout le dépôt »* — a rougi sur
`mesures/dn8-4/T1-conditions-build.txt` : le script de `T1`, recopié tel que joué, portait une
commande `sed` dont l'ancre de fin de ligne suit un `1000`, et le chiffre suivi du signe dollar est
un **jalon chiffré** pour cette gate. ⛔ Le contenu n'était **pas** un jalon ; la gate lit un
**motif**, et elle a raison de le lire partout. ⇒ **correctif, après la passe** : l'ancre est écrite
`<FIN-DE-LIGNE>` dans la recopie, avec une annotation qui dit pourquoi ; re-joué :
**`23 OK, 0 KO`**. ⚠️ C'est **exactement** le défaut que ce dépôt a déjà nommé trois fois
(*« les gates d'autrui rougissent sur votre prose »*) : ⛔ « les gates de mon sujet » était aveugle,
la borne est la **passe entière** — et c'est elle qui l'a vu.
⇒ `T5` ⛔ **ne mesure plus l'arbre livré** : la passe de **confirmation** est au § 9.

## 4. LE BUDGET — `verif_campagne_dn56.py` (plafond **900 s**)

| | `T0` | `T5` |
|---|---|---|
| tir **isolé** | `8 OK, 0 KO` · **733,79 s** · 21 cibles / 653 mutants | `8 OK, 0 KO` · **746,76 s** · **22 cibles / 665 mutants** |
| dans la passe | 740 s | 747 s |

⇒ les **12** mutants de la gate neuve coûtent **≈ +13 s**. Marge sous le plafond : **≈ 153 s**.
⚠️ **Ce que ce chiffre ne dit pas** : `verif_paliers_dn441.py` ⛔ **ne déclare pas**
`--liste-mutants`, donc `dn56` ⛔ **ne rejoue pas** ses mutants 14 et 15, ancrés sur le journal —
ils sont rejoués **à la main** au § 6.

## 5. ⚠️ LES OUTILS QUI NE SONT **PAS** DES GATES

| outil | `T0` | `T5` |
|---|---|---|
| `node tools/banc_langue_dalle_dn73.mjs` | `BANC : 39 OK, 0 KO` | **`BANC : 39 OK, 0 KO`** |
| `node tools/banc_couverture_dn82.mjs` | `96/100 fonctions, 131/190 blocs` | **identique**, seuils tenus |
| `python3 tools/inventaire_motif_dn53.py` | classe 1 : **0** fichier · TOTAL 251 fichiers / 2 035 sites | classe 1 : **0** fichier · TOTAL **255 / 2 062** |
| `python3 tools/campagne_ctrl_dn440.py --cockpit` | `rc=0`, BILAN TRI 15 cas, 0 échec | **sortie identique au caractère** (`diff` vide) |
| `verif_ledger_dn416.py --manifeste` | 383 lignes de tableau | **389** (+6 : la section `dn8-4`), régénéré `--en-place` **après** la dernière édition du ledger |
| `stub_lhm_dn48.py --port 8085` | refus, `rc=1` | **refus, `rc=1`** |
| `py_compile` `dn_console.py` `gen_font_dn.py` `dn_gates.py` | `rc=0` | **`rc=0`** (les deux outils re-ciblés compilent) |
| `bash -n tools/rendre-port.sh` | `rc=0` | **`rc=0`** |

⚠️ `inventaire_motif_dn53.py` : **seule la POPULATION bouge** — la classe 4 (*registre de
preuves, `mesures/` INTACT*) gagne les 4 captures de `mesures/dn8-4/` qui citent des chemins de la
machine de mesure (+27 sites). ⛔ La classe 1, la seule qui soit un défaut, reste à **0**.

## 6. LES MUTANTS — ceux de la gate neuve, et ⛔ AUCUN MUTANT EXISTANT RENDU INAPPLICABLE

### 6.1 `verif_vitrine_dn84.py` — cible **VUE ⇄ DÉCLARÉE**, à la main (`dn56` ne compare pas)

```
── verif_vitrine_dn84.py : chaque mutant, cible VUE ⇄ DECLAREE ──
  mutant  1  rc=1  BILAN=1  KO vus=[c1]  declares=[c1]  VU == DECLARE
  mutant  2  rc=1  BILAN=1  KO vus=[c2]  declares=[c2]  VU == DECLARE
  mutant  3  rc=1  BILAN=1  KO vus=[c3]  declares=[c3]  VU == DECLARE
  mutant  4  rc=1  BILAN=1  KO vus=[c4]  declares=[c4]  VU == DECLARE
  mutant  5  rc=1  BILAN=1  KO vus=[c5]  declares=[c5]  VU == DECLARE
  mutant  6  rc=1  BILAN=1  KO vus=[c6]  declares=[c6]  VU == DECLARE
  mutant  7  rc=1  BILAN=1  KO vus=[c7]  declares=[c7]  VU == DECLARE
  mutant  8  rc=1  BILAN=1  KO vus=[c8]  declares=[c8]  VU == DECLARE
  mutant  9  rc=1  BILAN=1  KO vus=[c9]  declares=[c9]  VU == DECLARE
  mutant 10  rc=1  BILAN=1  KO vus=[c10]  declares=[c10]  VU == DECLARE
  mutant 11  rc=1  BILAN=1  KO vus=[c11]  declares=[c11]  VU == DECLARE
  mutant 12  rc=1  BILAN=1  KO vus=[c12]  declares=[c12]  VU == DECLARE
  mutant 13 (inconnu) rc=2
  --liste-mutants rc=0  (12)
```

### 6.2 La matrice I/O du dossier, jouée sur une copie jetable

```
── temoins de la matrice I/O, joues sur une copie jetable (tools/ + docs/ + README variant) ──
  nominal (copie conforme)                                   rc=0  BILAN : 12 OK, 0 KO|
  titre SETEXT ajoute                                        rc=1   [KO ] (c3) ⛔ HTML brut, setext, lien de reference ⛔ l.74 titre setext '====='|BILAN : 11 OK, 1 KO|
  lien de REFERENCE ajoute                                   rc=1   [KO ] (c3) ⛔ HTML brut, setext, lien de reference ⛔ l.73 lien de reference '[journal]: docs/journal-de-bord.md'|BILAN : 11 OK, 1 KO|
  « not perceptible » ajoute aux known issues              rc=1   [KO ] (c9) ~40 s · 335.8/300 ms · AMD · Intel Arc ⛔ l.57 promet « not perceptible »|BILAN : 11 OK, 1 KO|
  vitrine ABSENTE                                            rc=1   [KO ] (c1) la vitrine se LIT ⛔ README.md : [Errno 2] No such file or directory: '/tmp/claude-1000/-home-nasbarok-projects-compagnon-project/fa43b17|BILAN : 0 OK, 1 KO|
  mutant 12 sur une vitrine SANS son ancre                   rc=3  ⛔ MUTANT 12 NON EXERCE : l'ancre 'sits next to your PC' est ABSENTE de la vitrine|
  mutant 5 sur une photo sans SOI                            rc=3  ⛔ MUTANT 5 NON EXERCE : la photo n'a pas de SOI|
```

### 6.3 Chaque mutant EXISTANT, BASE vierge ⇄ arbre de la marche

Instrument : un clone de `baf4265` sous le scratchpad (`managed_components/` relié), et l'arbre de
la marche ; pour chaque mutant, `rc`, présence d'un `BILAN`, et l'**ensemble des libellés `[KO ]`**
lus à colonne fixe. Un écart = un mutant dont la cible ou le verdict a bougé.

```
  verif_installeur_dn71       40 mutant(s) · 0 ecart(s) BASE ⇄ MARCHE — rc, BILAN et libelles [KO ] IDENTIQUES
  verif_prerequis_dn75        31 mutant(s) · 0 ecart(s) BASE ⇄ MARCHE — rc, BILAN et libelles [KO ] IDENTIQUES
  verif_paliers_dn441          0 mutant(s) · 0 ecart(s) BASE ⇄ MARCHE — rc, BILAN et libelles [KO ] IDENTIQUES
  verif_demarrage_dn443       48 mutant(s) · 0 ecart(s) BASE ⇄ MARCHE — rc, BILAN et libelles [KO ] IDENTIQUES
  verif_langues_dn442         25 mutant(s) · 0 ecart(s) BASE ⇄ MARCHE — rc, BILAN et libelles [KO ] IDENTIQUES
  verif_flash_dn72            41 mutant(s) · 0 ecart(s) BASE ⇄ MARCHE — rc, BILAN et libelles [KO ] IDENTIQUES
  verif_cablage_dn62          40 mutant(s) · 0 ecart(s) BASE ⇄ MARCHE — rc, BILAN et libelles [KO ] IDENTIQUES
  verif_licences_dn52         40 mutant(s) · 38 ecart(s) BASE ⇄ MARCHE
  verif_photos_dn63           32 mutant(s) · 0 ecart(s) BASE ⇄ MARCHE — rc, BILAN et libelles [KO ] IDENTIQUES
  verif_veille_dn33            0 mutant(s) · 0 ecart(s) BASE ⇄ MARCHE — rc, BILAN et libelles [KO ] IDENTIQUES
TOTAL : 297 mutant(s) confronte(s), 38 ecart(s)
  verif_licences_dn52         40 mutant(s) · 0 ecart(s) BASE ⇄ MARCHE — rc, BILAN et libelles [KO ] IDENTIQUES
TOTAL : 40 mutant(s) confronte(s), 0 ecart(s)
  ⛔ verif_dossier_d5_dn45 #1  BASE rc=1 bilan=True KO=['README.md', 'README.md date le constat', 'au moins un fichier ATTEIGNABLE a rendu un verdict', 'hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md', 'hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md date le con', 'hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md', 'hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md', 'hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md date le co', 'implementation-artifacts/sprint-status-desknode.yaml', 'le balayage a bien trouve des occurrences', 'mad-output/implementation-artifacts/deferred-work.md', 'rdware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md date le co']  ⇄  MARCHE rc=1 bilan=True KO=['README.md', 'README.md date le constat', 'au moins un fichier ATTEIGNABLE a rendu un verdict', 'docs/journal-de-bord.md', 'docs/journal-de-bord.md date le constat', 'hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md', 'hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md date le con', 'hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md', 'hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md', 'hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md date le co', 'implementation-artifacts/sprint-status-desknode.yaml', 'le balayage a bien trouve des occurrences', 'mad-output/implementation-artifacts/deferred-work.md', 'rdware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md date le co']
  verif_dossier_d5_dn45        3 mutant(s) · 1 ecart(s) BASE ⇄ MARCHE
  verif_boitier_dn64          35 mutant(s) · 0 ecart(s) BASE ⇄ MARCHE — rc, BILAN et libelles [KO ] IDENTIQUES
TOTAL : 38 mutant(s) confronte(s), 1 ecart(s)
  verif_paliers_dn441 #14 (ancre README) : rc=1 BILAN=True KO=['le README nomme le palier « DeskNode + Ambiance »'] — identique
  verif_paliers_dn441 #15 (ancre README) : rc=1 BILAN=True KO=["⛔ le README ne PROMET PAS NVIDIA (l'agent n'a aucun NVML)"] — identique
  verif_paliers_dn441         16 mutant(s) (joues par NUMERO : la gate ne declare PAS --liste-mutants) · 0 ecart(s)
```

⚠️ **Trois lectures à faire, et elles sont faites** :
- la **première** confrontation de `verif_licences_dn52.py` rendait **38 écarts** : **tous** portaient
  le seul libellé *« `path-to-document` désigne CE dépôt »*, KO dans le clone vierge parce que son
  `origin` était un chemin disque. Rejouée après `git remote set-url origin` (l'URL GitHub, celle
  de la CI) : **0 écart sur 40**. ⇒ un artefact **de la méthode**, ⛔ pas de la marche.
- `verif_dossier_d5_dn45.py #1` voit **un fichier de plus** illisible : le journal, **ajouté** à
  `AUTORITE` par cette marche. ⛔ Pas une dérive : c'est l'ajout, vu par le mutant fait pour ça.
- `verif_veille_dn33.py` ⛔ **ne déclare pas** de campagne (`0 mutant`) ; `verif_paliers_dn441.py`
  non plus — ses **16** mutants sont joués **par numéro**, dont **14** et **15**, ancrés sur le
  journal : **identiques**.

## 7. CE QUE LA MARCHE A TOUCHÉ, ET CE QU'ELLE N'A PAS TOUCHÉ

```
fichiers de la marche (index ⇄ BASE differents) : 30
   M CHANGELOG.md
   M CONTRIBUTING.md
   M README.md
   M docs/dn4-15-arbitrage.md
   M docs/dn5-1-ecart-promesses.md
   A docs/journal-de-bord.md
   A docs/photos/2026-08-30-1804-desknode-etat-actif-gros-plan.jpg
   A docs/photos/2026-08-30-1818-desknode-ambient-sur-la-tour.jpg
   M docs/roadmap.md
   A mesures/dn8-4/T0-borne-entree.txt
   A mesures/dn8-4/T1-conditions-build.txt
   A mesures/dn8-4/T2-photos.txt
   A mesures/dn8-4/T3-preuve-scission.txt
   A mesures/dn8-4/T4-rendu-github.txt
   A mesures/dn8-4/releve-comptes.md
   M tests/README.md
   M tools/dn_console.py
   M tools/gen_font_dn.py
   M tools/rendre-port.sh
   M tools/run_gates.sh
   A tools/scission_readme_dn84.py
   M tools/verif_demarrage_dn443.py
   M tools/verif_dossier_d5_dn45.py
   M tools/verif_flash_dn72.py
   M tools/verif_installeur_dn71.py
   M tools/verif_langues_dn442.py
   M tools/verif_paliers_dn441.py
   M tools/verif_prerequis_dn75.py
   M tools/verif_veille_dn33.py
   A tools/verif_vitrine_dn84.py
fichiers de l'arbre de travail NON indexes : 0 []
hors marche : 795 fichiers · empreinte BASE 4527a3d5730086c8 · empreinte INDEX 4527a3d5730086c8
```

⇒ l'**empreinte hors fichiers de la marche** est **identique** (`4527a3d5730086c8`, 795 fichiers) :
⛔ ni `firmware/`, ni `agent/`, ni `installeur/`, ni `tools/dn_agent_tour.ps1`, ni `hardware/`.

**⛔ Aucune ligne de prose effacée** : les lignes « retirées » du diff sont des **re-ciblages**
(`README.md` → `docs/journal-de-bord.md`), chacune accompagnée d'une mention datée qui **nomme
l'ancienne cible** — CONTRIBUTING 6 · manifeste `dn4-15` 6 · `dn5-1` 1 · `tests/README.md` 2 · un
chemin ou un message par outil re-ciblé. Et le journal : les **2 551** lignes (`split`) de
`README.md@baf4265` sont **toutes** dans `docs/journal-de-bord.md`, **sauf les 12 lignes rebasées**
(comptage en multiensemble).

## 8. `AC8.4.4` · `AC8.4.7` · LE CHEMIN DE LA CI

- **NVIDIA** — balayage : git ls-files (825 fichiers suivis, texte UTF-8), motif /nvidia|nvml/i, refutations = REFUTATIONS de verif_licences_dn52.py (14 marqueurs) ; lignes qui nomment NVIDIA/NVML : 125 · SANS refutation sur la meme ligne : 83.
  Par dossier : `docs/` **1** (`journal-de-bord.md` : *« `pynvml` n'est pas installé »* — une
  réfutation écrite autrement, en minuscules, hors du motif sensible à la casse de
  `verif_licences_dn52.py (c7)`) · `hardware/` **5** (le dossier de mesure : NVML **écartée**, **absente**)
  · `mesures/` **41** (captures et citations datées) · `tools/` **36** (le code et les fixtures des
  gates qui gardent la propriété). ⇒ **0 promesse publique NVIDIA non réfutée** ; la vitrine porte
  *NVIDIA … **not implemented*** sur **la même ligne**, et `(c7)` reste vert.
- **`verif_licences_dn52.py`** : **`34 OK, 0 KO`** à `T0` et à `T5`, journal compris dans son corpus
  (*« 209 lien(s) local(aux), 17 fichier(s) »*, contre 187 / 16 à `T0`).
- **Le chemin de la CI** — clone `--depth 1` d'une copie jetable où la marche est commitée,
  `origin` posé sur l'URL GitHub : `verif_licences_dn52.py` **`33 OK, 0 KO`** (*33 émis + 1
  déclaré = 34 prévus*), **identique** au même tir sur un clone `--depth 1` de `baf4265` ;
  `verif_vitrine_dn84.py` **`12 OK, 0 KO`** ; `scission_readme_dn84.py --verifier` **`rc=4`**
  (*« révision de base absente »*) — c'est pour ça que la preuve ⛔ n'est pas une gate.

## 9. `T6` — LA PASSE DE CONFIRMATION, SUR L'ARBRE LIVRÉ

Jouée **après** le correctif du § 3 et l'écriture des §§ 1-8 (2026-09-13, 02:44 → 03:19), avec le
même script que `T0` et `T5`.

| | `T5` | **`T6` (état livré)** |
|---|---|---|
| `bash tools/run_gates.sh --cockpit` | 45 VERTE, 2 ROUGE, 1 NON-JOUABLE sur 48 · 1 009 s | **46 VERTE, 1 ROUGE, 1 NON-JOUABLE sur 48** · 1 011 s |
| la seule ROUGE, **au compte** | `23 OK / 10 KO` | **`23 OK / 10 KO`** — ses lignes `[OK]`/`[KO]` **identiques au caractère à `T0`** |
| `verif_affiliation_dn65.py` | `22 OK, 1 KO` | **`23 OK, 0 KO`** (= `T0`) |
| les 46 autres gates, tir isolé | voir § 1 | **au compte de `T5`, une par une** (`compte.py T6 T5` : seul `dn65` diffère) |
| `verif_campagne_dn56.py` | 746,76 s isolé · 747 s passe | **749,90 s isolé · 749 s passe** · 22 cibles / 665 mutants · plafond 900 s |
| non-gates | § 5 | **identiques**, sauf la population de `inventaire_motif_dn53.py` : 256 fichiers / 2 063 sites (+1 / +1 : ce relevé) |
| empreinte suivie avant ⇄ après | `c93db9b2a2faf1c2` ⇄ idem | **`67fbc894f340d24c` ⇄ `67fbc894f340d24c`** |
| empreinte cockpit avant ⇄ après | `1343ec27f5601007` ⇄ idem | **`1343ec27f5601007` ⇄ `1343ec27f5601007`** |

⇒ **0 KO DE PLUS QU'À `T0`, GATE PAR GATE, SUR L'ARBRE LIVRÉ** : `T0` 45 V / 1 R / 1 NJ sur 47 ⇒
`T6` 46 V / 1 R / 1 NJ sur **48** (la 48ᵉ est `verif_vitrine_dn84.py`, verte).
⚠️ **Ce § 9 est écrit APRÈS `T6`** : c'est une mutation de ce seul fichier, et les gates qui lisent
les Markdown et les captures suivis (`dn52`, `dn63`, `dn65`, `dn415`, `dn45`, `dn81`, `dn416`, la
vitrine) sont re-jouées après son écriture — leurs comptes sont rapportés à l'owner avec la
livraison, ⛔ pas réécrits ici (un compte écrit après sa mesure serait une mesure qui n'a pas eu lieu).

## 10. ⚠️ AJOUTÉ LE 2026-09-13 APRÈS REVUE — LA GATE NEUVE A CHANGÉ APRÈS `T6`

⛔ **Les §§ 1-9 mesurent la gate à 12 contrôles.** La revue a imposé : `(c2)` et l'interdit
*not perceptible* lus aussi sur le texte **aplati** ; `(c3)` qui détecte l'**ouvrant** HTML ;
`(c5)`/`(c6)` étendus à **toute image locale citée**, avec refus de tout `APPn` hors `APP0 JFIF`,
de tout `COM`, et un grand côté ≤ 1 600 px ; `(c8)` qui exige le point d'entrée **sur le disque** ;
`(c13)` neuf (la commande `GESTE_DEPENDANCES`, lue à l'AST, et « V0.2 » dans `## Install`) ;
`(c14)(c15)(c16)`, la réciproque portée de `verif_prerequis_dn75.py`. ⇒ **16 contrôles,
16 mutants** — ⚠️ **au-delà du plafond de 12 mutants que le dossier fixait**, sur consigne de la
revue ; les mutants 2 et 3 ont été **réécrits** pour replanter la forme que l'ancienne lecture ne
voyait pas (`**CPU** monitor`, une balise `<img` coupée sur deux lignes).
⛔ **La passe entière ⛔ n'a PAS été rejouée après ces changements** (consigne : seuls les tests
des fichiers édités) ; la vérification complète est faite côté coordinateur.

```
── verif_vitrine_dn84.py apres la revue du 2026-09-13 : chaque mutant, cible VUE ⇄ DECLAREE ──
  mutant  1  rc=1  BILAN=1  KO vus=[c1]  declares=[c1]  VU == DECLARE
  mutant  2  rc=1  BILAN=1  KO vus=[c2]  declares=[c2]  VU == DECLARE
  mutant  3  rc=1  BILAN=1  KO vus=[c3]  declares=[c3]  VU == DECLARE
  mutant  4  rc=1  BILAN=1  KO vus=[c4]  declares=[c4]  VU == DECLARE
  mutant  5  rc=1  BILAN=1  KO vus=[c5]  declares=[c5]  VU == DECLARE
  mutant  6  rc=1  BILAN=1  KO vus=[c6]  declares=[c6]  VU == DECLARE
  mutant  7  rc=1  BILAN=1  KO vus=[c7]  declares=[c7]  VU == DECLARE
  mutant  8  rc=1  BILAN=1  KO vus=[c8]  declares=[c8]  VU == DECLARE
  mutant  9  rc=1  BILAN=1  KO vus=[c9]  declares=[c9]  VU == DECLARE
  mutant 10  rc=1  BILAN=1  KO vus=[c10]  declares=[c10]  VU == DECLARE
  mutant 11  rc=1  BILAN=1  KO vus=[c11]  declares=[c11]  VU == DECLARE
  mutant 12  rc=1  BILAN=1  KO vus=[c12]  declares=[c12]  VU == DECLARE
  mutant 13  rc=1  BILAN=1  KO vus=[c13]  declares=[c13]  VU == DECLARE
  mutant 14  rc=1  BILAN=1  KO vus=[c14]  declares=[c14]  VU == DECLARE
  mutant 15  rc=1  BILAN=1  KO vus=[c15]  declares=[c15]  VU == DECLARE
  mutant 16  rc=1  BILAN=1  KO vus=[c16]  declares=[c16]  VU == DECLARE
  mutant 17 (inconnu) rc=2
```

```
── temoins de la revue du 2026-09-13, sur une copie jetable (tools/ + docs/ + installeur/ + variantes) — 2026-09-13T04:17:18+02:00
  nominal                                                        rc=0  BILAN : 16 OK, 0 KO|
  balise <img coupee sur deux lignes (sans mutant)               rc=1   [KO ] (c3) ⛔ HTML brut, setext, lien de reference ⛔ l.73 HTML brut '<img'|BILAN : 15 OK, 1 KO|
  autolien <https://example.org> (admis)                         rc=0  BILAN : 16 OK, 0 KO|
  « **CPU** monitor » dans le texte                            rc=1   [KO ] (c2) ⛔ « CPU monitor » — le message n'est pas celui-la ⛔ present dans le texte APLATI (emphase ou saut de ligne)|BILAN : 15 OK, 1 KO|
  « not » / « perceptible » coupes par un saut de ligne      rc=1   [KO ] (c9) ~40 s · 335.8/300 ms · AMD · Intel Arc ⛔ « not perceptible » dans le texte APLATI|BILAN : 15 OK, 1 KO|
  3e image citee, JPEG avec segment COM                          rc=1   [KO ] (c5) JPEG lisibles, APP0 JFIF seul, <= 1600 px ⛔ docs/photos/extra.jpg ⛔ porte COM|BILAN : 15 OK, 1 KO|
  3e image citee, JPEG avec APP13                                rc=1   [KO ] (c5) JPEG lisibles, APP0 JFIF seul, <= 1600 px ⛔ docs/photos/extra.jpg ⛔ porte APP13|BILAN : 15 OK, 1 KO|
  ⚠️ 1er tir de ce temoin INVALIDE (mon generateur a planté, ⛔ aucune image produite, rc=0 NON SIGNIFICATIF) — rejoue :
  3e image citee, 1700 x 900 px                                  rc=1   [KO ] (c5) JPEG lisibles, APP0 JFIF seul, <= 1600 px ⛔ docs/photos/extra.jpg ⛔ 1700x900, grand cote > 1600|BILAN : 15 OK, 1 KO|
  3e image citee, ABSENTE du disque                              rc=1   [KO ] (c5) JPEG lisibles, APP0 JFIF seul, <= 1600 px ⛔ docs/photos/absente.jpg ABSENTE| [KO ] (c6) toute image citee existe, < 600000 o ⛔ docs/photos/absente.jpg ABSENTE|BILAN : 14 OK, 2 KO|
  le point d'entree ABSENT du disque                             rc=1   [KO ] (c8) deux paliers, point d'entree, anglais par defaut ⛔ absent(s) : ['installeur/DeskNode-installeur.bat SUR LE DISQUE']|BILAN : 15 OK, 1 KO|
  commande tronquee (la demonstration de la revue)               rc=1   [KO ] (c13) `## Install` porte GESTE_DEPENDANCES et V0.2 ⛔ `pip install --user psutil pyserial` absent de `## Install`|BILAN : 15 OK, 1 KO|
  CIBLES[7] = ("c8",) dans la source                             rc=1   [KO ] (c14) chaque controle est vise par >= 1 mutant ⛔ 1 CONTROLE(S) GARDE(S) PAR RIEN : c7|BILAN : 15 OK, 1 KO|
  un 17e controle SANS mutant dans la source                     rc=1   [KO ] (c14) chaque controle est vise par >= 1 mutant ⛔ 1 CONTROLE(S) GARDE(S) PAR RIEN : c17| [KO ] (z) tout controle prevu est EMIS ⛔ 17 emis pour 16 prevus — une gate qui joue MOINS de controles qu'annonce sort VERTE sur une population RETRECIE, ⛔ sans le|BILAN : 16 OK, 2 KO|
  mutant 13 sur une vitrine SANS la commande                     rc=3  ⛔ MUTANT 13 NON EXERCE : l'ancre '`pip install --user psutil pyserial`' est ABSENTE de la vitrine|
  mutant 16 quand CIBLES[999] existe deja                        rc=3  ⛔ MUTANT 16 NON EXERCE : `CIBLES[999]` existe deja|
```

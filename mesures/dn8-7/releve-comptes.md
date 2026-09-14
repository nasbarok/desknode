# `dn8-7` — le relevé des comptes, avant et après

> Passe d'**implémentation** seulement : ⛔ aucun commit, aucun tag, aucune poussée, aucune release.
> Borne d'entrée `T0` : `mesures/dn8-7/T0-borne-entree.txt` (2026-09-14, 00:48 ⇒ 01:26).
> Borne d'arrivée `T4` : même script (`passe.sh`, versé dans `T0` § 5), mêmes étapes, sur l'arbre
> **final** de la passe, jouée le 2026-09-14 de 01:37 à la fin relevée au § 3 — sorties sous le
> scratchpad de session, versées ici **après** la passe. Ce fichier-ci est écrit **après** `T4` :
> ⛔ il n'est pas dans l'arbre qu'elle a mesuré.

## 1. Le compte, gate par gate (`comparer.py T0 T4`, rc=0)

`comparer.py` est celui de `mesures/dn8-6/T2-passe-arretee.txt` § 5, avec les **deux défauts** que la
revue de `dn8-6` lui a trouvés **corrigés** : une gate absente d'une passe, et un `rc` qui se dégrade
à compte égal, font désormais sortir en 1. **Vu rougir avant usage** sur une copie altérée de `T0`
(une gate retirée, `langues` 31 ⇒ 30 OK, `dossier_dn415` 10 ⇒ 11 KO, un `[OK` de `courbe_dn413`
changé en `[KO`, `xip` rc 0 ⇒ 2) : **5 écarts sur 5** sortis « ⛔ », rc=1.

```
gate                               T0 rc OK/KO            T4 rc OK/KO            verdict
verif_affiliation_dn65.py          rc=0     23/0            rc=0     23/0            =
verif_banc_langue_dn73.py          rc=0     81/0            rc=0     81/0            =
verif_bme680_retard_dn45.py        rc=0     15/0            rc=0     15/0            =
verif_boitier_dn64.py              rc=0     29/0            rc=0     29/0            =
verif_bom_dn61.py                  rc=0     24/0            rc=0     24/0            =
verif_cablage_dn62.py              rc=0     37/0            rc=0     37/0            =
verif_campagne_dn440.py            rc=0     62/0            rc=0     62/0            =
verif_campagne_dn56.py             rc=0      8/0            rc=0      8/0            =
verif_courbe_dn413.py              rc=0     58/0            rc=0     58/0            =  (forme [OK]/[KO])
verif_cumul_ambient_dn45.py        rc=0     23/0            rc=0     23/0            =
verif_d4_nvs_dn45.py               rc=0      6/0            rc=0      6/0            =
verif_decoupe_horloge_dn418.py     rc=0      7/0            rc=0      7/0            =  (forme ✅/❌)
verif_demarrage_dn443.py           rc=0     58/0            rc=0     58/0            =
verif_dossier_d5_dn45.py           rc=0     12/0            rc=0     12/0            =
verif_dossier_dn415.py             rc=1     23/10           rc=1     23/10           =
verif_entree_dn82.py               rc=0     45/0            rc=0     45/0            =
verif_flash_dn72.py                rc=0     30/0            rc=0     30/0            =
verif_harnais_dn413.py             rc=0     22/0            rc=0     22/0            =  (forme [OK]/[KO])
verif_harnais_dn81.py              rc=0     28/0            rc=0     28/0            =
verif_hist_dn413.py                rc=0     56/0            rc=0     56/0            =  (forme [OK]/[KO])
verif_installeur_dn71.py           rc=0     28/0            rc=0     28/0            =
verif_instruments_dn423.py         rc=0    163/0            rc=0    163/0            =
verif_journal_soak_dn45.py         rc=0     26/0            rc=0     26/0            =
verif_langue_dalle_dn73.py         rc=0     61/0            rc=0     61/0            =
verif_langues_dn442.py             rc=0     31/0            rc=0     31/0            =
verif_ledger_dn416.py              rc=0     36/0            rc=0     36/0            =
verif_lhm_ps_dn83.py               rc=0     26/0            rc=0     26/0            =
verif_licences_dn52.py             rc=0     34/0            rc=0     34/0            =
verif_lissage_dn45.py              rc=0     21/0            rc=0     21/0            =
verif_miroir_horloge_dn418.py      rc=0     18/0            rc=0     18/0            =  (forme ✅/❌)
verif_page_dn722.py                rc=0     56/0            rc=0     56/0            =
verif_paliers_dn441.py             rc=0     42/0            rc=0     42/0            =
verif_photos_dn63.py               rc=0     28/0            rc=0     28/0            =
verif_placement_dn74.py            rc=0     42/0            rc=0     42/0            =
verif_polices_dn440.py             rc=0     11/0            rc=0     11/0            =
verif_preconditions_dn76.py        rc=0     55/0            rc=0     55/0            =
verif_prerequis_dn75.py            rc=0     51/0            rc=0     51/0            =
verif_rebouclage_dn45.py           rc=0     30/0            rc=0     30/0            =
verif_reception_dn85.py            rc=0     16/0            rc=0     16/0            =
verif_reprise_horloge_dn418.py     rc=0     50/0            rc=0     50/0            =  (forme ✅/❌)
verif_selection_dn49.py            rc=0     70/0            rc=0     70/0            =  (forme [OK]/[KO])
verif_serie_dn412.py               rc=0     50/0            rc=0     50/0            =
verif_source_lhm_dn48.py           rc=0     46/0            rc=0     46/0            =  (forme [OK]/[KO])
verif_sr03.py                      rc=2      0/0            rc=2      0/0            =  (forme ✅/❌)
verif_temoin_filtre_dn447.py       rc=0      5/0            rc=0      5/0            =
verif_veille_dn33.py               rc=0    267/0            rc=0    267/0            =
verif_verrou_lvgl_dn413.py         rc=0     60/0            rc=0     60/0            =  (forme [OK]/[KO])
verif_vitrine_dn84.py              rc=0     16/0            rc=0     16/0            =
verif_xip_dn422.py                 rc=0     10/0            rc=0     10/0            =

gates comparees : 49 (T0 49 · T4 49) · identiques au compte : 49 · differentes : 0 · OK perdu, KO gagne, rc degrade ou gate absente : 0
verif_dossier_dn415.py a T4 : 23 OK / 10 KO  (exige : 23 OK / 10 KO)
```

Formes de fin des gates **sans ligne `BILAN`**, relues dans leur sortie capturée à `T4` :

```
     verif_courbe_dn413                 ✅ lignes 1 · ❌ lignes 0 · [OK 58 · [KO 0 · derniere : ✅ 58 contrôles passent, 0 échec.
     verif_decoupe_horloge_dn418        ✅ lignes 7 · ❌ lignes 0 · [OK 0 · [KO 0 · derniere : ✅ TOUT TIENT.
     verif_harnais_dn413                ✅ lignes 1 · ❌ lignes 0 · [OK 22 · [KO 0 · derniere : ✅ 22 contrôles passent, 0 échec.
     verif_hist_dn413                   ✅ lignes 1 · ❌ lignes 0 · [OK 56 · [KO 0 · derniere : ✅ 56 contrôles passent, 0 échec.
     verif_miroir_horloge_dn418         ✅ lignes 18 · ❌ lignes 0 · [OK 0 · [KO 0 · derniere : ✅ LE MIROIR TIENT.
     verif_reprise_horloge_dn418        ✅ lignes 50 · ❌ lignes 0 · [OK 0 · [KO 0 · derniere : ✅ LES 12 SCENES TIENNENT.
     verif_selection_dn49               ✅ lignes 1 · ❌ lignes 0 · [OK 70 · [KO 0 · derniere :    MESURENT sur la carte, et les constats sensoriels sont l'OWNER.
     verif_source_lhm_dn48              ✅ lignes 3 · ❌ lignes 0 · [OK 46 · [KO 0 · derniere :    service coupe pendant que l'agent tourne, sur la tour.
     verif_sr03                         ✅ lignes 0 · ❌ lignes 0 · [OK 0 · [KO 0 · derniere :       TLS aboutit puis le flux HTTP/2 casse (INTERNAL_ERROR).
     verif_verrou_lvgl_dn413            ✅ lignes 1 · ❌ lignes 0 · [OK 60 · [KO 0 · derniere : ✅ 60 contrôles passent, 0 échec.
```

## 2. `run_gates.sh --silencieux --cockpit ~/projects/compagnon_project`

⚠️ **Écart au dossier, déclaré** : le dossier demande ce runner « par lots < 600 s ». Il n'a
**aucune** option de sous-ensemble (les gates sont découvertes par glob, règle (1) de son en-tête),
et il dure 942 à 1 041 s. ⇒ il est joué **entier**, **détaché** (`setsid nohup`), **après** les tirs
isolés et ⛔ jamais en parallèle, attendu par des tirs de scrutation < 600 s (`T0` § 2).

**`T0`**

```
=== bash tools/run_gates.sh --silencieux --cockpit (APRES les tirs isoles) ===
run_gates.sh --silencieux --cockpit /home/nasbarok/projects/compagnon_project : rc=1  1040.92 s
      [VERTE      ] tools/verif_page_dn722.py              rc=0      0s
      [VERTE      ] tools/verif_paliers_dn441.py           rc=0      0s
      [VERTE      ] tools/verif_photos_dn63.py             rc=0      1s
      [VERTE      ] tools/verif_placement_dn74.py          rc=0      0s
      [VERTE      ] tools/verif_polices_dn440.py           rc=0      0s
      [VERTE      ] tools/verif_preconditions_dn76.py      rc=0      0s
      [VERTE      ] tools/verif_prerequis_dn75.py          rc=0      1s
      [VERTE      ] tools/verif_rebouclage_dn45.py         rc=0      3s
      [VERTE      ] tools/verif_reception_dn85.py          rc=0      0s
      [VERTE      ] tools/verif_reprise_horloge_dn418.py   rc=0      0s
      [VERTE      ] tools/verif_selection_dn49.py          rc=0      0s
      [VERTE      ] tools/verif_serie_dn412.py             rc=0      2s
      [VERTE      ] tools/verif_source_lhm_dn48.py         rc=0      5s
      [NON-JOUABLE] tools/verif_sr03.py                    rc=2   (attendu) temoin absent : tools/fixtures/AN4545.pdf
      [VERTE      ] tools/verif_temoin_filtre_dn447.py     rc=0      2s
      [  temoin  ] tools/verif_veille_dn33.py             firmware/desknode/managed_components/lvgl__lvgl/scripts/built_in_font/built_in_font_gen.py est present ⇒ la gate est JOUEE
      [VERTE      ] tools/verif_veille_dn33.py             rc=0      8s
      [VERTE      ] tools/verif_verrou_lvgl_dn413.py       rc=0     17s
      [VERTE      ] tools/verif_vitrine_dn84.py            rc=0      1s
      [VERTE      ] tools/verif_xip_dn422.py               rc=0      0s
      
      BILAN : 47 VERTE, 1 ROUGE, 1 NON-JOUABLE sur 49 gates (1041s)
      appariement --cockpit : 0 divergence(s) entre la detection LARGE (quotes simples/doubles, declaration coupee) et la detection ETROITE d'origine
      ⛔ ROUGES :
         · tools/verif_dossier_dn415.py (rc=1)
```

**`T4`**

```
=== bash tools/run_gates.sh --silencieux --cockpit (APRES les tirs isoles) ===
run_gates.sh --silencieux --cockpit /home/nasbarok/projects/compagnon_project : rc=1  1041.78 s
      [VERTE      ] tools/verif_page_dn722.py              rc=0      0s
      [VERTE      ] tools/verif_paliers_dn441.py           rc=0      0s
      [VERTE      ] tools/verif_photos_dn63.py             rc=0      1s
      [VERTE      ] tools/verif_placement_dn74.py          rc=0      0s
      [VERTE      ] tools/verif_polices_dn440.py           rc=0      0s
      [VERTE      ] tools/verif_preconditions_dn76.py      rc=0      0s
      [VERTE      ] tools/verif_prerequis_dn75.py          rc=0      0s
      [VERTE      ] tools/verif_rebouclage_dn45.py         rc=0      4s
      [VERTE      ] tools/verif_reception_dn85.py          rc=0      0s
      [VERTE      ] tools/verif_reprise_horloge_dn418.py   rc=0      0s
      [VERTE      ] tools/verif_selection_dn49.py          rc=0      0s
      [VERTE      ] tools/verif_serie_dn412.py             rc=0      1s
      [VERTE      ] tools/verif_source_lhm_dn48.py         rc=0      4s
      [NON-JOUABLE] tools/verif_sr03.py                    rc=2   (attendu) temoin absent : tools/fixtures/AN4545.pdf
      [VERTE      ] tools/verif_temoin_filtre_dn447.py     rc=0      1s
      [  temoin  ] tools/verif_veille_dn33.py             firmware/desknode/managed_components/lvgl__lvgl/scripts/built_in_font/built_in_font_gen.py est present ⇒ la gate est JOUEE
      [VERTE      ] tools/verif_veille_dn33.py             rc=0      9s
      [VERTE      ] tools/verif_verrou_lvgl_dn413.py       rc=0     17s
      [VERTE      ] tools/verif_vitrine_dn84.py            rc=0      0s
      [VERTE      ] tools/verif_xip_dn422.py               rc=0      0s
      
      BILAN : 47 VERTE, 1 ROUGE, 1 NON-JOUABLE sur 49 gates (1041s)
      appariement --cockpit : 0 divergence(s) entre la detection LARGE (quotes simples/doubles, declaration coupee) et la detection ETROITE d'origine
      ⛔ ROUGES :
         · tools/verif_dossier_dn415.py (rc=1)
```

## 3. Les empreintes, les trois fichiers de `.github/`, les non-gates

**`T0` — début et fin**

```
EMPREINTE desknode AVANT (contenu, git ls-files | sha256sum) : 47699828aa5301eb
EMPREINTE desknode AVANT (index, git ls-files -s | sha256sum) : bd4a8c5914a0661a
EMPREINTE cockpit  AVANT : e04aae6c4d9cdebb
sha256 .github/ :
  a32e2944977d8009c98f98a8ffd6c73f474313569af3f9b133944ae7ab73e581  .github/workflows/cla.yml
  00f194c9d459caca3205f53c294dc8863aef4b4e587d6ba0fd32c4156bd9566e  .github/workflows/gates.yml
  a0d5bfe53d7bda13a42cb8e585ce1c445962fde059eca76f2369809842f0d5b7  .github/cla-signatures.json
EMPREINTE desknode APRES (contenu) : 47699828aa5301eb
EMPREINTE desknode APRES (index)   : bd4a8c5914a0661a
EMPREINTE cockpit  APRES : e04aae6c4d9cdebb
sha256 .github/ (apres) :
  a32e2944977d8009c98f98a8ffd6c73f474313569af3f9b133944ae7ab73e581  .github/workflows/cla.yml
  00f194c9d459caca3205f53c294dc8863aef4b4e587d6ba0fd32c4156bd9566e  .github/workflows/gates.yml
  a0d5bfe53d7bda13a42cb8e585ce1c445962fde059eca76f2369809842f0d5b7  .github/cla-signatures.json
git status --porcelain desknode (apres) :
=== fin 2026-09-14T01:26:36+02:00 ===
```

**`T4` — début et fin**

```
=== dn8-7 / passe T4 — debut 2026-09-14T01:37:07+02:00 ===
HEAD desknode : 0086ea6579ddf012ffb2752ddf72306a5939779f
HEAD cockpit  : f53f468a3f5476052075c2510896663bc54c42c7
git status --porcelain desknode :
   M CHANGELOG.md
   M CONTRIBUTING.md
   M README.md
   M SECURITY.md
   M docs/dn5-1-ecart-promesses.md
   A docs/releases/v0.1.0-beta.md
   M docs/roadmap.md
   M installeur/charge/PROVENANCE.md
   M installeur/charge/desknode.bin
   M installeur/charge/manifest.json
   M installeur/index.html
   A mesures/dn8-7/T0-borne-entree.txt
   A mesures/dn8-7/T1-la-charge-de-la-seance.txt
   A mesures/dn8-7/T2-ecriture-et-temoins.txt
   A mesures/dn8-7/T3-temoins-de-la-matrice.txt
git status --porcelain cockpit (implementation-artifacts) :
   M _bmad-output/implementation-artifacts/epic-dn8-context.md
  ?? _bmad-output/implementation-artifacts/dn8-7-la-release-existe-et-ce-qu-elle-distribue-a-une-source.md
EMPREINTE desknode AVANT (contenu, git ls-files | sha256sum) : a1114521acc3e0bf
EMPREINTE desknode AVANT (index, git ls-files -s | sha256sum) : 08dd444bc7eb8e0d
EMPREINTE cockpit  AVANT : e04aae6c4d9cdebb
sha256 .github/ :
  a32e2944977d8009c98f98a8ffd6c73f474313569af3f9b133944ae7ab73e581  .github/workflows/cla.yml
  00f194c9d459caca3205f53c294dc8863aef4b4e587d6ba0fd32c4156bd9566e  .github/workflows/gates.yml
  a0d5bfe53d7bda13a42cb8e585ce1c445962fde059eca76f2369809842f0d5b7  .github/cla-signatures.json
EMPREINTE desknode APRES (contenu) : a1114521acc3e0bf
EMPREINTE desknode APRES (index)   : 08dd444bc7eb8e0d
EMPREINTE cockpit  APRES : e04aae6c4d9cdebb
sha256 .github/ (apres) :
  a32e2944977d8009c98f98a8ffd6c73f474313569af3f9b133944ae7ab73e581  .github/workflows/cla.yml
  00f194c9d459caca3205f53c294dc8863aef4b4e587d6ba0fd32c4156bd9566e  .github/workflows/gates.yml
  a0d5bfe53d7bda13a42cb8e585ce1c445962fde059eca76f2369809842f0d5b7  .github/cla-signatures.json
git status --porcelain desknode (apres) :
   M CHANGELOG.md
   M CONTRIBUTING.md
   M README.md
   M SECURITY.md
   M docs/dn5-1-ecart-promesses.md
   A docs/releases/v0.1.0-beta.md
   M docs/roadmap.md
   M installeur/charge/PROVENANCE.md
   M installeur/charge/desknode.bin
   M installeur/charge/manifest.json
   M installeur/index.html
   A mesures/dn8-7/T0-borne-entree.txt
   A mesures/dn8-7/T1-la-charge-de-la-seance.txt
   A mesures/dn8-7/T2-ecriture-et-temoins.txt
   A mesures/dn8-7/T3-temoins-de-la-matrice.txt
=== fin 2026-09-14T02:13:36+02:00 ===
```

⇒ à `T0` comme à `T4`, **AVANT = APRÈS** (contenu, index, cockpit) : ⛔ aucune écriture n'a
chevauché une passe. Les **sha256 de `cla.yml`, `gates.yml` et `cla-signatures.json` sont identiques**
entre `T0` et `T4`.

**Les outils qui ne sont pas des gates, `T4`**

```
=== LES OUTILS QUI NE SONT PAS DES GATES ===
--- node tools/banc_langue_dalle_dn73.mjs : rc=0  0.75 s
      BANC : 39 OK, 0 KO
--- node tools/banc_couverture_dn82.mjs : rc=0  0.98 s
      COUVERTURE dn8-2 — LE SCRIPT DE LA PAGE, MESURE PENDANT QU'IL S'EXECUTE
      COUVERTURE : 96/100 fonctions, 131/190 blocs — les deux seuils sont tenus.
--- python3 tools/inventaire_motif_dn53.py : rc=0  0.30 s
      18:  [OK ] classe 1 : le defaut de `--csv` est LOCALISE par AST     ancre semantique, ⛔ pas verbatim
      19:  [OK ] classe 1 : l'arbre du jour est SOLDE                     0 fait
      20:  [OK ] classe 1 : faute REPLANTEE ⇒ elle REMONTE                ≥1 fait
      23:  1. dependance FONCTIONNELLE  (le seul defaut)      0 fichiers      0 sites
      24:  2. exemple d'usage          (declare au site)     32 fichiers     87 sites
      25:  3. trace de generation      (polices — INTACTES)    5 fichiers      5 sites
      26:  4. registre de preuves      (mesures/ — INTACT)  238 fichiers   2099 sites
      27:  5. le motif est le SUJET    (EXCLUSION DECLAREE)    4 fichiers     21 sites
      28:       TOTAL                                       279 fichiers   2212 sites
      55:     STABLE, c'est la classe 1 : plus aucun outil ne depend d'une
--- python3 tools/campagne_ctrl_dn440.py --cockpit /home/nasbarok/projects/compagnon_project : rc=0  66.74 s
      BILAN TRI : 15 cas au tableau — dont 11 SITE(S) VIVANT(S) et 4 FICHE(S) de remede — 6 LEGITIME(S), 3 TROU(S), 1 INERTE(S), 5 BRANCHE(S), 0 echec(s)
--- python3 tools/verif_ledger_dn416.py --cockpit /home/nasbarok/projects/compagnon_project --manifeste : rc=0  0.78 s
--- python3 tools/scission_readme_dn84.py --verifier --avant baf4265a292a7db1ae9f6bc8673779f2e743d45b --apres WORKTREE : rc=0  0.09 s
         couverture : 13 lien(s) local(aux) dans la base, 13 rebasage(s)
      IDENTIQUE — le corps du journal est T(README@baf4265a292a), octet pour octet.
--- python3 -m py_compile tools/dn_console.py tools/gen_font_dn.py tools/dn_gates.py : rc=0  0.06 s
--- bash -n tools/rendre-port.sh : rc=0  0.00 s
```

⚠️ **`inventaire_motif_dn53.py` bouge, et c'est écrit** : classe 2 *exemple d'usage* **30 ⇒ 32
fichiers, 77 ⇒ 87 sites** — les liens absolus `github.com/nasbarok/desknode/…` des notes de release
(8 lignes) et les deux définitions de liens du `CHANGELOG` ; classe 4 *registre de preuves*
**234 ⇒ 238 fichiers** — `T0`→`T3` de cette marche. La classe 1 (le seul défaut) reste **0 / 0**.
`README.md` et `SECURITY.md` portaient déjà l'URL du dépôt (`dn8-5`).

## 4. Ce que la marche ⛔ ne devait pas toucher

- `git diff --quiet 0086ea6 -- firmware/ agent/ tools/` : **rc=0** (`--stat` : « vide »).
- `git diff --quiet 0086ea6 -- .github/workflows/cla.yml .github/workflows/gates.yml .github/cla-signatures.json tools/dn_agent_tour.ps1 installeur/dn_installeur.py` : **rc=0**.
- `installeur/index.html` : **3229 lignes** avant et après, **4 / 4** au `numstat` (`T2` § 1 (3)).
- ⛔ aucun `idf.py`, ⛔ aucun exécutable, ⛔ aucun `--onefile` : `FR23` reste un **écart déclaré V0.2**.

L'arbre à la fin de la passe (`git diff --stat HEAD`, fichiers neufs en intention d'ajout) :

```
 CHANGELOG.md                                |  65 ++
 CONTRIBUTING.md                             |   8 +
 README.md                                   |   1 +
 SECURITY.md                                 |   3 +
 docs/dn5-1-ecart-promesses.md               |   4 +-
 docs/releases/v0.1.0-beta.md                |  41 ++
 docs/roadmap.md                             |  13 +-
 installeur/charge/PROVENANCE.md             |  67 ++-
 installeur/charge/desknode.bin              | Bin 1266752 -> 1266928 bytes
 installeur/charge/manifest.json             |   2 +-
 installeur/index.html                       |   8 +-
 mesures/dn8-7/T0-borne-entree.txt           | 362 ++++++++++++
 mesures/dn8-7/T1-la-charge-de-la-seance.txt | 154 +++++
 mesures/dn8-7/T2-ecriture-et-temoins.txt    | 394 +++++++++++++
 mesures/dn8-7/T3-temoins-de-la-matrice.txt  | 878 ++++++++++++++++++++++++++++
 15 files changed, 1987 insertions(+), 13 deletions(-)
```

## 5. ⚠️ Deux retouches de prose APRÈS `T2`/`T3`, ⛔ avant `T4`

Faites entre 01:33 et 01:36, **après** les témoins et **avant** la borne d'arrivée :

1. `installeur/charge/PROVENANCE.md` — la phrase disait que le binaire avait été copié « par la seule
   ligne `cp build/desknode.bin` ci-dessus » : **faux**, la copie est passée par la garde (a) du script
   (`T1` § 4). Rectifiée en « une copie **gardée**, SHA-256 relu avant et après ». Nombre de lignes égal.
2. `docs/roadmap.md` — l'annotation du 2026-09-14 comptait « deux » items de la ligne `dn8` faits ; ils
   sont **trois** (les gabarits de `dn8-5` étaient faits aussi). Réécrite avant tout commit.

⇒ **ce que `T2` et `T3` ont lu diffère de l'arbre final sur ces deux passages de prose, et sur rien
d'autre**. `verif_flash_dn72.py` rejoué après la retouche : **30 OK / 0 KO**. `T4` porte l'arbre final.

> 🔴 **CORRIGÉ LE 2026-09-14, À LA REVUE DE LA PASSE — le paragraphe ci-dessus est ⛔ non effacé, et il
> est faux deux fois. `T2` n'est ⛔ pas retouché.**
> *(i)* « **et sur rien d'autre** » est faux : la retouche de la roadmap n'a pas seulement changé
> « deux » en « trois », elle a aussi **retiré une phrase** — *« The sentence "when `CONTRIBUTING.md`
> says a version displayed on the device is 'still to come'" no longer has a sentence to point at »*,
> visible dans le balayage de `T2` § 6 (`docs/roadmap.md:156`) et absente de `docs/roadmap.md` final,
> où elle est remplacée par *« so the example the first paragraph gives, a displayed version "still to
> come", has stopped being true »*.
> *(ii)* `T2` § 1 (1) dit que le mutant 17 « vise la révision ». Il ne réécrit que le **pointeur** de la
> page vers `PROVENANCE.md` (la moitié `pointe` de `(c16)`) ; la moitié « la révision du binaire est
> écrite dans `PROVENANCE.md` » est une **simple sous-chaîne**, que les annotations de cette marche
> satisfont à elles seules : la cellule « révision du dépôt » remise à `40be2c8` laisse la gate à
> **30 OK / 0 KO**. ⇒ cette cellule est désormais gardée par l'étape `garde` du script de publication,
> et la faute est **replantée et vue rougir** dans `T5-temoins-des-correctifs-de-revue.txt` (R1).
> ⚠️ **Et « `T4` porte l'arbre final » a cessé d'être vrai le même jour** : les correctifs de revue ont
> modifié, **après** `T4`, `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`,
> `.github/ISSUE_TEMPLATE/bug_report.yml`, `installeur/index.html` (3229 lignes, inchangé),
> `installeur/charge/PROVENANCE.md`, `docs/dn5-1-ecart-promesses.md`, `docs/releases/v0.1.0-beta.md`,
> et ajouté ce paragraphe et `T5`. Seules les gates qui couvrent ces fichiers ont été rejouées à ce
> stade ; la passe complète n'est ⛔ pas rejouée ici.

## 6. Ce que ce relevé ⛔ NE DIT PAS

- ⛔ **Que la release existe.** Rien n'a été tagué, poussé ni publié : `git tag` est vide,
  `git ls-remote --tags origin` est vide, `gh api …/releases` rend `[]` (`T3`, avant et après).
  AC8.7.1 → AC8.7.3, AC8.7.4 (corps relu à l'API), le run CI du tag et la relecture sur le remote
  **appartiennent à la passe de publication**, qui suit la revue et le commit `C1`.
- ⛔ **Que les fichiers de `C1` seront ceux-ci.** La revue peut les changer ; toute retouche impose de
  rejouer `verif_flash_dn72.py` et la borne.
- ⛔ **Que les dates tiennent.** Les notes, le `CHANGELOG` (`## [0.1.0-beta] - 2026-09-14`), la
  roadmap et les annotations datent la release du **2026-09-14**. Une publication un autre jour les
  rend **fausses** : elles devraient être re-datées **avant** `C1`.
- ⛔ **Que les ancres du tag existent** : `POST /markdown` n'émet aucune ancre (`T2` § 1 (4)) ; la
  preuve est l'étape `liens` de la publication.
- ⛔ **Que la garde « tag déjà présent » protège quoi que ce soit contre un tiers** : aucune protection
  de tag n'est possible sur ce dépôt privé (`rulesets` 403, `tags/protection` 404, mesure du dossier) ;
  la garde n'arrête que **ce script**.
- ⛔ **Le coût du pack** : « ~+204 Ko de delta » est le chiffre du dossier, ⛔ re-mesuré ici.
- ⛔ **La lisibilité de la prose anglaise**, ni l'œil d'un lecteur sur la page de release.
- Le tracker est écrit **après** `T4` ; les gates qui lisent le cockpit sont re-tirées après son
  écriture, et leurs comptes sont rapportés avec la livraison, ⛔ réécrits ici.

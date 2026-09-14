# `dn8-9` — le relevé de clôture, sur `C1`

> **`C1`** = `cc074298a253cfbd63f4a7508f4084d57ce47219` (`feat(dn8-9)`, parent `d8da714`), arbre propre au départ de la passe.
> Passe complète jouée sur `C1` le 2026-09-14, de 13:14:38 à 13:51:06 (+02:00) : même script que `T0`/`T4`
> (`passe.sh`, versé dans `T0` § 5), mêmes étapes — chaque gate isolée, puis `verif_campagne_dn56.py`
> **détachée**, les outils qui ne sont pas des gates, puis `run_gates.sh --silencieux --cockpit`
> **détaché**, l'un après l'autre, ⛔ jamais en parallèle. Sorties sous le scratchpad, versées ici
> **après** la passe : ce fichier est dans `C2`, ⛔ pas dans l'arbre mesuré. ⛔ Rien n'est poussé.

## 1. Les vidéos, les ajouts, les GIF, `firmware/` (`AC8.9.6`)

Relevé git brut, joué à 13:34:23 pendant l'attente de `run_gates.sh` — **lecture seule**, empreintes de
fin de passe égales à celles du début (§ 4). Chaque commande passée par `rtk proxy` : le filtre du
proxy tronquait le sujet du commit dans un premier relevé (13:33:50), rejoué.

```
date : 2026-09-14T13:34:23+02:00  (chaque commande git passee par `rtk proxy`, sortie BRUTE)
$ git rev-parse HEAD
cc074298a253cfbd63f4a7508f4084d57ce47219
$ git status --porcelain --untracked-files=all | wc -l
0
$ git ls-files | grep -icE '\.(mp4|webm|mov|mkv)$'
0
$ git ls-files | grep -iE '\.gif$'
docs/demo/2026-08-30-1853-desknode-toucher.gif
docs/demo/2026-08-30-1910-desknode-reseau-en-direct.gif
docs/demo/2026-08-30-1911-desknode-courbe-reseau.gif
$ git log --diff-filter=A --name-only --format='commit %H %s' d8da714..cc074298a253cfbd63f4a7508f4084d57ce47219
commit cc074298a253cfbd63f4a7508f4084d57ce47219 feat(dn8-9): LA DEMO SE VOIT -- UN LIEN VERS LA VIDEO, TROIS GIF DANS LA VITRINE, ET (c5) LIT LE GIF PAR SES BLOCS

docs/demo/2026-08-30-1853-desknode-toucher.gif
docs/demo/2026-08-30-1910-desknode-reseau-en-direct.gif
docs/demo/2026-08-30-1911-desknode-courbe-reseau.gif
mesures/dn8-9/T0-borne-entree.txt
mesures/dn8-9/T1-recette-des-gif.txt
mesures/dn8-9/T2-lien-oembed.txt
mesures/dn8-9/T3-gate-et-temoins.txt
mesures/dn8-9/T4-passe-apres-ecriture.txt
mesures/dn8-9/T5-correctifs-de-revue.txt
$ git log --diff-filter=A --name-only --format= d8da714..cc074298a253cfbd63f4a7508f4084d57ce47219 | grep -icE '\.(mp4|webm|mov|mkv)$'
0
$ git ls-tree -l cc074298a253cfbd63f4a7508f4084d57ce47219 docs/demo/
100644 blob febe0a04815ca5af6fead2c922c6e7975f31d353  551967	docs/demo/2026-08-30-1853-desknode-toucher.gif
100644 blob 197f5df6cdaa66bcba29c50746a47dc95c16cca6  542301	docs/demo/2026-08-30-1910-desknode-reseau-en-direct.gif
100644 blob 3b037a2da0a01421f5b7fb8459303db0ed4b0de1  520906	docs/demo/2026-08-30-1911-desknode-courbe-reseau.gif
$ git diff --stat d8da714 cc074298a253cfbd63f4a7508f4084d57ce47219 -- firmware/  (sortie entre crochets)
[]
git diff --quiet … -- firmware/ : rc=0
git diff --quiet … -- agent/ installeur/ .github/ tools/dn_gates.py : rc=0
$ git diff --numstat d8da714 cc074298a253cfbd63f4a7508f4084d57ce47219
25	0	CHANGELOG.md
12	0	README.md
-	-	docs/demo/2026-08-30-1853-desknode-toucher.gif
-	-	docs/demo/2026-08-30-1910-desknode-reseau-en-direct.gif
-	-	docs/demo/2026-08-30-1911-desknode-courbe-reseau.gif
8	1	docs/roadmap.md
521	0	mesures/dn8-9/T0-borne-entree.txt
424	0	mesures/dn8-9/T1-recette-des-gif.txt
141	0	mesures/dn8-9/T2-lien-oembed.txt
458	0	mesures/dn8-9/T3-gate-et-temoins.txt
351	0	mesures/dn8-9/T4-passe-apres-ecriture.txt
489	0	mesures/dn8-9/T5-correctifs-de-revue.txt
287	6	tools/verif_vitrine_dn84.py
$ git rev-parse 'v0.1.0-beta^{}'
fb6d64601f5b17ce54927a7e2aae599bd517a4e0
$ git ls-remote --tags origin
f382819016ea4a2431350a2127e29258dbb027e1	refs/tags/v0.1.0-beta
fb6d64601f5b17ce54927a7e2aae599bd517a4e0	refs/tags/v0.1.0-beta^{}
$ git rev-list --left-right --count origin/main...main
0	58
$ sha256sum .github/workflows/cla.yml .github/workflows/gates.yml .github/cla-signatures.json
a32e2944977d8009c98f98a8ffd6c73f474313569af3f9b133944ae7ab73e581  .github/workflows/cla.yml
00f194c9d459caca3205f53c294dc8863aef4b4e587d6ba0fd32c4156bd9566e  .github/workflows/gates.yml
a0d5bfe53d7bda13a42cb8e585ce1c445962fde059eca76f2369809842f0d5b7  .github/cla-signatures.json
```

- **0** fichier vidéo suivi (`mp4`, `webm`, `mov`, `mkv`) ; **0** vidéo ajoutée par `C1`.
- Les **3** GIF de `C1` : 551 967 + 542 301 + 520 906 = **1 615 174 o**, chacun sous 600 000 o.
- `git diff d8da714 C1 -- firmware/` : **vide** (rc=0) ; `agent/`, `installeur/`, `.github/`,
  `tools/dn_gates.py` : intacts (rc=0).
- `v0.1.0-beta^{}` = `fb6d64601f5b17ce54927a7e2aae599bd517a4e0`, le même en local et sur le remote,
  comme à `T0` ; `origin/main...main` = `0 58` ⇒ ⛔ rien de poussé.
- sha256 de `cla.yml`, `gates.yml`, `cla-signatures.json` : **identiques** à `T0`.
- `verif_licences_dn52.py` sur `C1` : `BILAN : 34 OK, 0 KO` ⇒ **≥ 34 OK**.

## 2. Le compte, `T0` ⇒ `C1`, gate par gate (`python3 comparer.py T0 C1` : rc=0)

```
gate                               T0 rc OK/KO            C1 rc OK/KO            verdict
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

gates comparees : 49 (T0 49 · C1 49) · identiques au compte : 49 · differentes : 0 · OK perdu, KO gagne, rc degrade ou gate absente : 0
verif_dossier_dn415.py a C1 : 23 OK / 10 KO  (exige : 23 OK / 10 KO)
```

## 3. `run_gates.sh --silencieux --cockpit`, sur `C1`

```
run_gates.sh --silencieux --cockpit /home/nasbarok/projects/compagnon_project : rc=1  1040.77 s
[VERTE      ] tools/verif_page_dn722.py              rc=0      0s
[VERTE      ] tools/verif_paliers_dn441.py           rc=0      1s
[VERTE      ] tools/verif_photos_dn63.py             rc=0      0s
[VERTE      ] tools/verif_placement_dn74.py          rc=0      0s
[VERTE      ] tools/verif_polices_dn440.py           rc=0      0s
[VERTE      ] tools/verif_preconditions_dn76.py      rc=0      1s
[VERTE      ] tools/verif_prerequis_dn75.py          rc=0      0s
[VERTE      ] tools/verif_rebouclage_dn45.py         rc=0      3s
[VERTE      ] tools/verif_reception_dn85.py          rc=0      0s
[VERTE      ] tools/verif_reprise_horloge_dn418.py   rc=0      1s
[VERTE      ] tools/verif_selection_dn49.py          rc=0      0s
[VERTE      ] tools/verif_serie_dn412.py             rc=0      1s
[VERTE      ] tools/verif_source_lhm_dn48.py         rc=0      4s
[NON-JOUABLE] tools/verif_sr03.py                    rc=2   (attendu) temoin absent : tools/fixtures/AN4545.pdf
[VERTE      ] tools/verif_temoin_filtre_dn447.py     rc=0      1s
[  temoin  ] tools/verif_veille_dn33.py             firmware/desknode/managed_components/lvgl__lvgl/scripts/built_in_font/built_in_font_gen.py est present ⇒ la gate est JOUEE
[VERTE      ] tools/verif_veille_dn33.py             rc=0      9s
[VERTE      ] tools/verif_verrou_lvgl_dn413.py       rc=0     16s
[VERTE      ] tools/verif_vitrine_dn84.py            rc=0      0s
[VERTE      ] tools/verif_xip_dn422.py               rc=0      0s

BILAN : 47 VERTE, 1 ROUGE, 1 NON-JOUABLE sur 49 gates (1040s)
appariement --cockpit : 0 divergence(s) entre la detection LARGE (quotes simples/doubles, declaration coupee) et la detection ETROITE d'origine
⛔ ROUGES :
   · tools/verif_dossier_dn415.py (rc=1)
```

À `T0` : `rc=1`, **47 VERTE · 1 ROUGE (`verif_dossier_dn415`) · 1 NON-JOUABLE (`verif_sr03`)** — identique.

## 4. Le relevé brut de la passe (empreintes avant / après)

```
=== dn8-9 / passe C1 — debut 2026-09-14T13:14:38+02:00 ===
HEAD desknode : cc074298a253cfbd63f4a7508f4084d57ce47219
HEAD cockpit  : 7e880800fa79ff448c87c42b391f3b3de54854b3
git status --porcelain desknode :
git status --porcelain cockpit (implementation-artifacts) :
   M _bmad-output/implementation-artifacts/sprint-status-desknode.yaml
  ?? _bmad-output/implementation-artifacts/dn8-9-la-demo-se-voit-la-video-par-un-lien-trois-gif-dans-la-vitrine.md
EMPREINTE desknode AVANT (contenu, git ls-files | sha256sum) : eb4bacf2fdacc70d
EMPREINTE desknode AVANT (index, git ls-files -s | sha256sum) : a9d19c911ba5e574
EMPREINTE cockpit  AVANT : a50942e99e96a23d
sha256 .github/ :
  a32e2944977d8009c98f98a8ffd6c73f474313569af3f9b133944ae7ab73e581  .github/workflows/cla.yml
  00f194c9d459caca3205f53c294dc8863aef4b4e587d6ba0fd32c4156bd9566e  .github/workflows/gates.yml
  a0d5bfe53d7bda13a42cb8e585ce1c445962fde059eca76f2369809842f0d5b7  .github/cla-signatures.json
sha256 installeur/charge/ :
  4b36efb1816fbb173ec9acd4dc686e2327689040590f9f765ce23368e0b55fb8  installeur/charge/PROVENANCE.md
  d1bf1fd347b3494bcb3d38c7cee0d4698fd45617505529cf5c5dc1653ae0a478  installeur/charge/bootloader.bin
  2b845a161079de8bb90ee2b23208a2531d04b157f76fea1c61933a6f8d474e3b  installeur/charge/desknode.bin
  fae162a0a422c3c134db7ba015d8ddcf0adb20502be4f1617c17dba9fb3500ed  installeur/charge/living_pcb_v0.bin
  8835022afbf87d828403dea65ffe9d0ef7d364b6c9c1d7d7eb4c0620afbc45cd  installeur/charge/manifest.json
  0934eb422b7c7f52193373a9ce81818e7344d9f0061e073b60fb8ebe209e46eb  installeur/charge/partition-table.bin
sha256 build/ :
  2b845a161079de8bb90ee2b23208a2531d04b157f76fea1c61933a6f8d474e3b  firmware/desknode/build/desknode.bin
  d1bf1fd347b3494bcb3d38c7cee0d4698fd45617505529cf5c5dc1653ae0a478  firmware/desknode/build/bootloader/bootloader.bin
  0934eb422b7c7f52193373a9ce81818e7344d9f0061e073b60fb8ebe209e46eb  firmware/desknode/build/partition_table/partition-table.bin
build/ : -rw-r--r-- 1 nasbarok nasbarok 1266928 2026-09-13 19:48:42.326192241 +0200 firmware/desknode/build/desknode.bin
git describe --tags --always --dirty : v0.1.0-beta-2-gcc07429
git tag (brut, entre crochets) : [v0.1.0-beta]
git ls-remote origin (toutes refs) :
  7246f5248d1625a2a351bbb374c03f0585a008c3	HEAD
  3db180cbd6789cde32bb093dd565d1ab3c4f298f	refs/heads/dn4-5-le-module-vit-tout-seul
  7246f5248d1625a2a351bbb374c03f0585a008c3	refs/heads/main
  d11977f8d80eee890f37bf79843cfe782b612338	refs/pull/1/head
  6a80de8ccab4fb3715ebfdeae830ecbe801a5069	refs/pull/2/head
  f382819016ea4a2431350a2127e29258dbb027e1	refs/tags/v0.1.0-beta
  fb6d64601f5b17ce54927a7e2aae599bd517a4e0	refs/tags/v0.1.0-beta^{}
git ls-remote --tags origin (brut, entre crochets) : [f382819016ea4a2431350a2127e29258dbb027e1	refs/tags/v0.1.0-beta
fb6d64601f5b17ce54927a7e2aae599bd517a4e0	refs/tags/v0.1.0-beta^{}]
git rev-list --left-right --count origin/main...main : 0	58
gh api repos/nasbarok/desknode/releases (RESUME) : 1 objet(s) : v0.1.0-beta prerelease=True 6 assets
gh api repos/nasbarok/desknode/tags (RESUME) : 1 objet(s) : v0.1.0-beta ⇒ fb6d64601f5b17ce54927a7e2aae599bd517a4e0
git rev-parse v0.1.0-beta^{} : fb6d64601f5b17ce54927a7e2aae599bd517a4e0
git ls-files | grep -icE '\.(mp4|webm|mov|mkv|gif)$' : 3
git ls-files | grep -icE '\.(mp4|webm|mov|mkv)$' (videos seules) : 0
taille de la vitrine : 7915 o  README.md

=== LE COMPTE DE CHAQUE GATE (tir isole, timeout 900 s, ordre du glob) ===
verif_affiliation_dn65.py          rc=0       1.81 s  BILAN : 23 OK, 0 KO 
verif_banc_langue_dn73.py          rc=0       2.39 s  BILAN : 81 OK, 0 KO 
verif_bme680_retard_dn45.py        rc=0       0.05 s  BILAN : 15 OK, 0 KO 
verif_boitier_dn64.py --cockpit    rc=0       0.35 s  BILAN : 29 OK, 0 KO 
verif_bom_dn61.py                  rc=0       0.04 s  BILAN : 24 OK, 0 KO 
verif_cablage_dn62.py              rc=0       0.11 s  BILAN : 37 OK, 0 KO 
verif_campagne_dn440.py --cockpit  rc=0     139.47 s  BILAN CAMPAGNE : 39 mutant(s) JOUE(S), 0 echec(s), 0 controle(s) gardes par rien BILAN : 62 OK, 0 KO 
verif_campagne_dn56.py             rc=0     784.61 s  BILAN : 8 OK, 0 KO 
verif_courbe_dn413.py              rc=0      10.44 s  ⛔ aucune ligne BILAN
verif_cumul_ambient_dn45.py        rc=0       1.49 s  BILAN : 23 OK, 0 KO 
verif_d4_nvs_dn45.py               rc=0       0.71 s  BILAN : 6 OK, 0 KO 
verif_decoupe_horloge_dn418.py     rc=0       6.33 s  ⛔ aucune ligne BILAN
verif_demarrage_dn443.py           rc=0       0.67 s  BILAN : 58 OK, 0 KO 
verif_dossier_d5_dn45.py --cockpit rc=0       1.39 s  BILAN : 12 OK, 0 KO 
verif_dossier_dn415.py --cockpit   rc=1       7.92 s  BILAN : 23 OK, 10 KO 
verif_entree_dn82.py               rc=0       0.25 s  BILAN : 45 OK, 0 KO 
verif_flash_dn72.py                rc=0       0.39 s  BILAN : 30 OK, 0 KO 
verif_harnais_dn413.py             rc=0       8.65 s  ⛔ aucune ligne BILAN
verif_harnais_dn81.py --cockpit    rc=0       5.25 s  BILAN : 28 OK, 0 KO 
verif_hist_dn413.py                rc=0       4.22 s  ⛔ aucune ligne BILAN
verif_installeur_dn71.py           rc=0       0.25 s  BILAN : 28 OK, 0 KO 
verif_instruments_dn423.py         rc=0       0.60 s  BILAN : 163 OK, 0 KO 
verif_journal_soak_dn45.py         rc=0       0.12 s  BILAN : 26 OK, 0 KO 
verif_langue_dalle_dn73.py         rc=0       0.11 s  BILAN : 61 OK, 0 KO 
verif_langues_dn442.py             rc=0       0.66 s  BILAN : 31 OK, 0 KO 
verif_ledger_dn416.py --cockpit    rc=0       1.24 s  BILAN : 36 OK, 0 KO 
verif_lhm_ps_dn83.py               rc=0      18.30 s  BILAN : 26 OK, 0 KO 
verif_licences_dn52.py             rc=0       0.93 s  BILAN : 34 OK, 0 KO 
verif_lissage_dn45.py              rc=0       0.16 s  BILAN : 21 OK, 0 KO 
verif_miroir_horloge_dn418.py      rc=0       0.07 s  ⛔ aucune ligne BILAN
verif_page_dn722.py                rc=0       0.15 s  BILAN : 56 OK, 0 KO 
verif_paliers_dn441.py             rc=0       0.16 s  BILAN : 42 OK, 0 KO 
verif_photos_dn63.py               rc=0       0.68 s  BILAN : 28 OK, 0 KO 
verif_placement_dn74.py            rc=0       0.09 s  BILAN : 42 OK, 0 KO 
verif_polices_dn440.py             rc=0       0.05 s  BILAN : 11 OK, 0 KO 
verif_preconditions_dn76.py        rc=0       0.17 s  BILAN : 55 OK, 0 KO 
verif_prerequis_dn75.py            rc=0       0.23 s  BILAN : 51 OK, 0 KO 
verif_rebouclage_dn45.py           rc=0       3.04 s  BILAN : 30 OK, 0 KO 
verif_reception_dn85.py            rc=0       0.16 s  BILAN : 16 OK, 0 KO 
verif_reprise_horloge_dn418.py     rc=0       0.11 s  ⛔ aucune ligne BILAN
verif_selection_dn49.py            rc=0       0.07 s  ⛔ aucune ligne BILAN
verif_serie_dn412.py               rc=0       2.05 s  BILAN : 50 OK / 0 KO 
verif_source_lhm_dn48.py           rc=0       4.02 s  ⛔ aucune ligne BILAN
verif_sr03.py                      rc=2       0.05 s  ⛔ aucune ligne BILAN
verif_temoin_filtre_dn447.py       rc=0       1.77 s  BILAN : 5 OK, 0 KO 
verif_veille_dn33.py               rc=0       8.35 s  BILAN : 267 OK · 0 KO 
verif_verrou_lvgl_dn413.py         rc=0      16.36 s  ⛔ aucune ligne BILAN
verif_vitrine_dn84.py              rc=0       0.12 s  BILAN : 16 OK, 0 KO 
verif_xip_dn422.py                 rc=0       0.04 s  BILAN : 10 OK / 0 KO 

=== LES OUTILS QUI NE SONT PAS DES GATES ===
--- node tools/banc_langue_dalle_dn73.mjs : rc=0  0.74 s
      BANC : 39 OK, 0 KO
--- node tools/banc_couverture_dn82.mjs : rc=0  0.98 s
      COUVERTURE dn8-2 — LE SCRIPT DE LA PAGE, MESURE PENDANT QU'IL S'EXECUTE
      COUVERTURE : 96/100 fonctions, 131/190 blocs — les deux seuils sont tenus.
--- python3 tools/inventaire_motif_dn53.py : rc=0  0.33 s
      18:  [OK ] classe 1 : le defaut de `--csv` est LOCALISE par AST     ancre semantique, ⛔ pas verbatim
      19:  [OK ] classe 1 : l'arbre du jour est SOLDE                     0 fait
      20:  [OK ] classe 1 : faute REPLANTEE ⇒ elle REMONTE                ≥1 fait
      23:  1. dependance FONCTIONNELLE  (le seul defaut)      0 fichiers      0 sites
      24:  2. exemple d'usage          (declare au site)     32 fichiers     88 sites
      25:  3. trace de generation      (polices — INTACTES)    5 fichiers      5 sites
      26:  4. registre de preuves      (mesures/ — INTACT)  247 fichiers   2166 sites
      27:  5. le motif est le SUJET    (EXCLUSION DECLAREE)    4 fichiers     21 sites
      28:       TOTAL                                       288 fichiers   2280 sites
      55:     STABLE, c'est la classe 1 : plus aucun outil ne depend d'une
--- python3 tools/campagne_ctrl_dn440.py --cockpit /home/nasbarok/projects/compagnon_project : rc=0  66.91 s
      BILAN TRI : 15 cas au tableau — dont 11 SITE(S) VIVANT(S) et 4 FICHE(S) de remede — 6 LEGITIME(S), 3 TROU(S), 1 INERTE(S), 5 BRANCHE(S), 0 echec(s)
--- python3 tools/verif_ledger_dn416.py --cockpit /home/nasbarok/projects/compagnon_project --manifeste : rc=0  0.68 s
--- python3 tools/scission_readme_dn84.py --verifier --avant baf4265a292a7db1ae9f6bc8673779f2e743d45b --apres WORKTREE : rc=0  0.10 s
         couverture : 13 lien(s) local(aux) dans la base, 13 rebasage(s)
      IDENTIQUE — le corps du journal est T(README@baf4265a292a), octet pour octet.
--- python3 -m py_compile tools/dn_console.py tools/gen_font_dn.py tools/dn_gates.py : rc=0  0.06 s
--- bash -n tools/rendre-port.sh : rc=0  0.01 s

=== bash tools/run_gates.sh --silencieux --cockpit (APRES les tirs isoles) ===
run_gates.sh --silencieux --cockpit /home/nasbarok/projects/compagnon_project : rc=1  1040.77 s
      [VERTE      ] tools/verif_page_dn722.py              rc=0      0s
      [VERTE      ] tools/verif_paliers_dn441.py           rc=0      1s
      [VERTE      ] tools/verif_photos_dn63.py             rc=0      0s
      [VERTE      ] tools/verif_placement_dn74.py          rc=0      0s
      [VERTE      ] tools/verif_polices_dn440.py           rc=0      0s
      [VERTE      ] tools/verif_preconditions_dn76.py      rc=0      1s
      [VERTE      ] tools/verif_prerequis_dn75.py          rc=0      0s
      [VERTE      ] tools/verif_rebouclage_dn45.py         rc=0      3s
      [VERTE      ] tools/verif_reception_dn85.py          rc=0      0s
      [VERTE      ] tools/verif_reprise_horloge_dn418.py   rc=0      1s
      [VERTE      ] tools/verif_selection_dn49.py          rc=0      0s
      [VERTE      ] tools/verif_serie_dn412.py             rc=0      1s
      [VERTE      ] tools/verif_source_lhm_dn48.py         rc=0      4s
      [NON-JOUABLE] tools/verif_sr03.py                    rc=2   (attendu) temoin absent : tools/fixtures/AN4545.pdf
      [VERTE      ] tools/verif_temoin_filtre_dn447.py     rc=0      1s
      [  temoin  ] tools/verif_veille_dn33.py             firmware/desknode/managed_components/lvgl__lvgl/scripts/built_in_font/built_in_font_gen.py est present ⇒ la gate est JOUEE
      [VERTE      ] tools/verif_veille_dn33.py             rc=0      9s
      [VERTE      ] tools/verif_verrou_lvgl_dn413.py       rc=0     16s
      [VERTE      ] tools/verif_vitrine_dn84.py            rc=0      0s
      [VERTE      ] tools/verif_xip_dn422.py               rc=0      0s
      
      BILAN : 47 VERTE, 1 ROUGE, 1 NON-JOUABLE sur 49 gates (1040s)
      appariement --cockpit : 0 divergence(s) entre la detection LARGE (quotes simples/doubles, declaration coupee) et la detection ETROITE d'origine
      ⛔ ROUGES :
         · tools/verif_dossier_dn415.py (rc=1)

EMPREINTE desknode APRES (contenu) : eb4bacf2fdacc70d
EMPREINTE desknode APRES (index)   : a9d19c911ba5e574
EMPREINTE cockpit  APRES : a50942e99e96a23d
sha256 .github/ (apres) :
  a32e2944977d8009c98f98a8ffd6c73f474313569af3f9b133944ae7ab73e581  .github/workflows/cla.yml
  00f194c9d459caca3205f53c294dc8863aef4b4e587d6ba0fd32c4156bd9566e  .github/workflows/gates.yml
  a0d5bfe53d7bda13a42cb8e585ce1c445962fde059eca76f2369809842f0d5b7  .github/cla-signatures.json
git rev-parse v0.1.0-beta^{} (apres) : fb6d64601f5b17ce54927a7e2aae599bd517a4e0
git status --porcelain desknode (apres) :
=== fin 2026-09-14T13:51:06+02:00 ===
```

Les outils qui ne sont pas des gates :

```
--- node tools/banc_langue_dalle_dn73.mjs : rc=0  0.74 s
      BANC : 39 OK, 0 KO
--- node tools/banc_couverture_dn82.mjs : rc=0  0.98 s
      COUVERTURE dn8-2 — LE SCRIPT DE LA PAGE, MESURE PENDANT QU'IL S'EXECUTE
      COUVERTURE : 96/100 fonctions, 131/190 blocs — les deux seuils sont tenus.
--- python3 tools/inventaire_motif_dn53.py : rc=0  0.33 s
      18:  [OK ] classe 1 : le defaut de `--csv` est LOCALISE par AST     ancre semantique, ⛔ pas verbatim
      19:  [OK ] classe 1 : l'arbre du jour est SOLDE                     0 fait
      20:  [OK ] classe 1 : faute REPLANTEE ⇒ elle REMONTE                ≥1 fait
      23:  1. dependance FONCTIONNELLE  (le seul defaut)      0 fichiers      0 sites
      24:  2. exemple d'usage          (declare au site)     32 fichiers     88 sites
      25:  3. trace de generation      (polices — INTACTES)    5 fichiers      5 sites
      26:  4. registre de preuves      (mesures/ — INTACT)  247 fichiers   2166 sites
      27:  5. le motif est le SUJET    (EXCLUSION DECLAREE)    4 fichiers     21 sites
      28:       TOTAL                                       288 fichiers   2280 sites
      55:     STABLE, c'est la classe 1 : plus aucun outil ne depend d'une
--- python3 tools/campagne_ctrl_dn440.py --cockpit /home/nasbarok/projects/compagnon_project : rc=0  66.91 s
      BILAN TRI : 15 cas au tableau — dont 11 SITE(S) VIVANT(S) et 4 FICHE(S) de remede — 6 LEGITIME(S), 3 TROU(S), 1 INERTE(S), 5 BRANCHE(S), 0 echec(s)
--- python3 tools/verif_ledger_dn416.py --cockpit /home/nasbarok/projects/compagnon_project --manifeste : rc=0  0.68 s
--- python3 tools/scission_readme_dn84.py --verifier --avant baf4265a292a7db1ae9f6bc8673779f2e743d45b --apres WORKTREE : rc=0  0.10 s
         couverture : 13 lien(s) local(aux) dans la base, 13 rebasage(s)
      IDENTIQUE — le corps du journal est T(README@baf4265a292a), octet pour octet.
--- python3 -m py_compile tools/dn_console.py tools/gen_font_dn.py tools/dn_gates.py : rc=0  0.06 s
--- bash -n tools/rendre-port.sh : rc=0  0.01 s
```

⚠️ `inventaire_motif_dn53.py` : le registre de preuves passe de **241 fichiers / 2 120 sites** (`T0`)
à **247 / 2 166** — ce sont `T0`→`T5` de cette marche. La classe 1 reste 0.

## 5. Ce que ce relevé ⛔ NE DIT PAS

- ⛔ **Que `C2` ne porte aucune vidéo** : c'est `git show --name-status C2`, relevé après son commit
  et rapporté avec la livraison, ⛔ ici (ce fichier est DANS `C2`).
- ⛔ **Que la vidéo en ligne est le montage mesuré** : seule la durée concorde (78 s contre 77,845 s) ;
  la relecture du sha256 **avant l'envoi** est un geste owner relevé par personne — écart déclaré
  d'`AC8.9.1`, ⛔ coché.
- ⛔ **Que `## Demo` est gardée** : la gate rend 16/0 sur une vitrine sans cette section (`T3` (5b)) ;
  ni le lien, ni le nombre de GIF, ni la légende, ni l'animation ne sont gardés.
- ⛔ **Que le tracker, le ledger et le manifeste du cockpit tiennent** : ils s'écrivent après ce
  relevé, et leurs six gates sont rejouées après la dernière écriture, hors de ce fichier.
- ⛔ **Que les petits textes de la dalle se lisent dans les GIF** à leur taille affichée (`T5` § 4).
- ⛔ **Que la passe dit quelque chose du remote au-delà de ses refs** : ni la CI de `main`, ni l'état
  du dépôt public (il ne l'est pas).

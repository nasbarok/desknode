# `dn4-15` — MANIFESTE D'ARBITRAGE

> **Un verdict par occurrence, et le verdict est LISIBLE HORS DU CODE.**
> Produit le **2026-08-30** par la story `dn4-15`, sur `desknode@6f92e9a` et
> `compagnon_project@303c6bf+`. ⛔ **Ce n'est pas une liste de corrections** : c'est la
> trace de ce qui a été LU, et de ce qui a été décidé pour chaque occurrence.

## Pourquoi ce fichier existe

L'epic `dn4` du 2026-08-25 annonçait *« 17 occurrences `VL53L0X` »* à corriger. Elles ont été
**lues une par une** le 2026-08-30 : **28 sur 29 étaient LÉGITIMES** — des réfutations, un témoin
négatif, un piège de source. **Les supprimer aurait détruit la connaissance** qui empêche de
re-tenter une piste déjà éliminée par la mesure. **Le seul vrai défaut vivait dans un fichier
que le périmètre annoncé ne couvrait pas** (`sdkconfig.defaults`).

🔴 **UN COMPTE DE `grep` MESURE *LE MOT*, ⛔ PAS *LE DÉFAUT*.** Ce manifeste est ce qui
transforme un compte en verdict, et ce qui **protège la prochaine passe d'un `sed` global** :
une occurrence non listée est **indiscernable d'une occurrence oubliée**.

## Les quatre verdicts, et rien d'autre

| verdict | ce qu'il veut dire | ce qu'on en fait |
|---|---|---|
| **`FAUX`** | l'énoncé est faux **aujourd'hui** | corrigé |
| **`VRAI`** | l'énoncé est exact aujourd'hui | ⛔ **ne pas toucher** |
| **`HISTORIQUE`** | vrai **à sa date**, trompeur hors contexte | un **renvoi** suffit ; ⛔ la narration n'est pas réécrite |
| **`SANS-RAPPORT`** | **homonyme** — le mot, pas le sujet | ⛔ **ne pas toucher**, et surtout pas au `sed` |

| cockpit | _bmad-output/implementation-artifacts/code-reviews/cr-dn4-17-desknode.patch | 1 | busid-en-dur | 1 | -powershell.exe -Command "& 'C:\Program Files\usbipd-win\usbipd.exe' detach --busid 3-1" | HISTORIQUE | mention DATEE d'un busid, ⛔ pas une recette nue : elle se LIT, elle ne s'execute pas. Rendue visible par le motif elargi |
| cockpit | _bmad-output/implementation-artifacts/code-reviews/cr-dn4-2-delta-diff.patch | 1 | busid-en-dur | 1 | +> ⚠️ **Busid `3-7`, pas `3-1`.** Le skill `/desknode-board`, le `README.md` et six stories écrivent | HISTORIQUE | mention DATEE d'un busid, ⛔ pas une recette nue : elle se LIT, elle ne s'execute pas. Rendue visible par le motif elargi |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | 506..516 | 1 | **contrôler la formule contre un relevé déjà publié** (ici : VENTILOS à `506..516` en dn3-2) | HISTORIQUE | coordonnee morte CITEE dans un recit date — la narration reste, le renvoi a `widget jauge` fait foi (AC5.3) |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | 506..516 | 1 | rectangle réel posé par LVGL** (`dn_ui_widget_jauge_rect()`, `dn4-4`/AC9). `VENTILOS 506..516` | HISTORIQUE | coordonnee morte CITEE dans un recit date — la narration reste, le renvoi a `widget jauge` fait foi (AC5.3) |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | busid-en-dur | 1 | PAREIL.** Le cadrage comptait **17** « busid `3-1` ». Le balayage distingue **9 recettes** | HISTORIQUE | mention DATEE d'un busid, ⛔ pas une recette nue : elle se LIT, elle ne s'execute pas. Rendue visible par le motif elargi |
| cockpit | _bmad-output/implementation-artifacts/dn1-1-toolchain-build-flash-log-serie-wsl.md | 1 | busid-en-dur | 1 | → **BUSID = `3-1`** (`303a:1001`). `bind` OK, état passé de `Not shared` à **`Shared`**. | HISTORIQUE | mention DATEE d'un busid, ⛔ pas une recette nue : elle se LIT, elle ne s'execute pas. Rendue visible par le motif elargi |
| cockpit | _bmad-output/implementation-artifacts/dn1-1-toolchain-build-flash-log-serie-wsl.md | 1 | busid-en-dur | 1 | → écrite. **Aucun placeholder orphelin** : `COM3` et le BUSID `3-1` sont les valeurs réelles, | HISTORIQUE | mention DATEE d'un busid, ⛔ pas une recette nue : elle se LIT, elle ne s'execute pas. Rendue visible par le motif elargi |
| cockpit | _bmad-output/implementation-artifacts/dn1-1-toolchain-build-flash-log-serie-wsl.md | 1 | busid-en-dur | 1 | - [x] [Review][Patch] 🔴 **L'étape indispensable de la voie A n'est pas exécutable** — le `detach` (sans lui `COM3` n'exi | HISTORIQUE | mention DATEE d'un busid, ⛔ pas une recette nue : elle se LIT, elle ne s'execute pas. Rendue visible par le motif elargi |
| cockpit | _bmad-output/implementation-artifacts/dn1-2-living-pcb-statique-plein-ecran.md | 1 | busid-en-dur | 1 | \| USB \| natif `303A:1001` (Serial/JTAG), **pas** de CH343P ; BUSID `3-1` ; COM3 côté Windows \| | HISTORIQUE | mention DATEE d'un busid, ⛔ pas une recette nue : elle se LIT, elle ne s'execute pas. Rendue visible par le motif elargi |
| cockpit | _bmad-output/implementation-artifacts/dn4-10-l-image-glisse-encore-et-aucun-compteur-ne-le-dit.md | 1 | busid-en-dur | 1 | 4. 🔴 **LE BUSID `3-1` DU SKILL `desknode-board` EST FAUX SUR CETTE MACHINE** — la carte est sur | HISTORIQUE | mention DATEE d'un busid, ⛔ pas une recette nue : elle se LIT, elle ne s'execute pas. Rendue visible par le motif elargi |
| cockpit | _bmad-output/implementation-artifacts/dn4-14-les-icones-disent-ce-qu-elles-montrent.md | 1 | busid-en-dur | 1 | - ⛔ **Les quatre écarts de dossier** (`façade de la tour`, busid `3-1`, `VL53L0X`, `y = 340..350`) | HISTORIQUE | mention DATEE d'un busid, ⛔ pas une recette nue : elle se LIT, elle ne s'execute pas. Rendue visible par le motif elargi |
| cockpit | _bmad-output/implementation-artifacts/dn4-17-l-agent-vit-sur-la-tour-et-on-reprend-la-main.md | 1 | busid-en-dur | 1 | \| `README.md` \| **129 K** ; § « port EXCLUSIF » ligne **989** ; busid `3-1` en dur \| AC7.1, AC7.2 \| | HISTORIQUE | mention DATEE d'un busid, ⛔ pas une recette nue : elle se LIT, elle ne s'execute pas. Rendue visible par le motif elargi |
| cockpit | _bmad-output/implementation-artifacts/dn4-2-brancher-les-trois-capteurs.md | 1 | busid-en-dur | 1 | vérifié **VIDE AVANT** le flash. Port `/dev/ttyACM0`, **busid `3-7`** (⛔ **pas `3-1`** — six | HISTORIQUE | mention DATEE d'un busid, ⛔ pas une recette nue : elle se LIT, elle ne s'execute pas. Rendue visible par le motif elargi |
| cockpit | _bmad-output/implementation-artifacts/sprint-status-desknode.yaml | 1 | 506..516 | 1 | #          1re ligne se déplace (VENTILOS 506..516 de dn3-2, bande de jauge | HISTORIQUE | coordonnee morte CITEE dans un recit date — la narration reste, le renvoi a `widget jauge` fait foi (AC5.3) |
| cockpit | _bmad-output/implementation-artifacts/sprint-status-desknode.yaml | 1 | busid-en-dur | 1 | dn4-10-l-image-glisse-encore-et-aucun-compteur-ne-le-dit: in-progress  # 📌 RENVOI dn4-22 (2026-08-28, [CC] 28b §4.6) — ⛔ | HISTORIQUE | mention DATEE d'un busid, ⛔ pas une recette nue : elle se LIT, elle ne s'execute pas. Rendue visible par le motif elargi |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | 506..516 | 1 | pas mais `CASE_H` oui — `VENTILOS 506..516` de `dn3-2`, bande de jauge `y = 340..350` de `dn4-1`) | HISTORIQUE | coordonnee morte CITEE dans un recit date — la narration reste, le renvoi a `widget jauge` fait foi (AC5.3) |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | busid-en-dur | 1 | > \| busid `3-7` vs `3-1` \| **3** occ., « le busid est `3-7` » \| **9 RECETTES** (+ des mentions datées) \| 🔴 **la QUESTION | HISTORIQUE | mention DATEE d'un busid, ⛔ pas une recette nue : elle se LIT, elle ne s'execute pas. Rendue visible par le motif elargi |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-18.md | 1 | vl53l0x | 1 | \| `dn4-2` \| **Les trois capteurs sur le bus, soudés** \| 🥈 2a \| BH1750 · VL53L0X · INA219 soudés, inventaire + photos \| * | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-18b.md | 1 | 340..350 | 1 | `VENTILOS 506..516` (dn3-2) et la bande de jauge `y = 340..350` (dn4-1) **ne décrivent plus | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-18b.md | 1 | 506..516 | 1 | `VENTILOS 506..516` (dn3-2) et la bande de jauge `y = 340..350` (dn4-1) **ne décrivent plus | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-18b.md | 1 | 340..350 | 1 | #          (VENTILOS 506..516 de dn3-2, jauge y=340..350 de dn4-1) ⇒ recalculer | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-18b.md | 1 | 506..516 | 1 | #          (VENTILOS 506..516 de dn3-2, jauge y=340..350 de dn4-1) ⇒ recalculer | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-20.md | 1 | vl53l0x | 1 | \| 1 \| Le brief et l'epic disent **« VL53L0X »** \| ✅ **CONFIRMÉ** \| Étiquette héritée d'un dump, jamais confrontée à la s | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-20.md | 1 | facade | 1 | \| 3 \| *« monté sur la façade de la tour »*, périmé \| 🔴 **RÉFUTÉ** — ⚠️ **RÉFUTATION LEVÉE le 2026-08-30, voir la note so | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-20.md | 1 | facade | 1 | La story `dn4-2` écrit que la ligne du brief *« monté verticalement sur la façade de la tour PC »* | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-20.md | 1 | facade | 1 | - **D4** : *« OTA … flash USB-C suffit tant que le module **n'est pas vissé dans la façade** »* — | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-20.md | 1 | facade | 1 | - 🔴 **le brief lui-même**, à la ligne suivante : *« Installation : portrait sur façade Phantom 630 ; | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-20.md | 1 | facade | 1 | >   *« docs(dn2-1): AC11 — la doc rattrape la realite, et le montage en facade est PERIME »* ; | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-20.md | 1 | facade | 1 | > **ventilateur 200 mm de façade**, qui est un fait mesuré — sont **laissés INTACTS**, et le | VRAI | le ventilateur 200 mm DE FACADE — fait MESURE (`0 RPM` dans le BIOS aussi, pas de fil tachymetrique) ⛔ NE PAS TOUCHER |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-20.md | 1 | vl53l0x | 1 | \| `epics-desknode-v1.md` \| 4× « VL53L0X », dont 2 **prospectifs** \| **Édition 3** \| | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-20.md | 1 | vl53l0x | 1 | ⇒ **Trois voies écrites au brief, aucune tranchée** : ajouter un VL53L0X · dériver la présence d'une | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-20.md | 1 | vl53l0x | 1 | **(b) 🔴 ET LA VOIE « AJOUTER UN VL53L0X » COÛTE UNE MODIFICATION MATÉRIELLE, PAS UN ACHAT.** | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-20.md | 1 | vl53l0x | 1 | Le VL53L0X a pour adresse par défaut **`0x29`** — **exactement celle du VL6180X déjà soudé**. Deux | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-20.md | 1 | vl53l0x | 1 | le VL53L0X n'a pas et qui recouvre partiellement le BH1750. ⛔ **Pas une redondance à supprimer** : | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-20.md | 1 | vl53l0x | 1 | \| **1** \| `brief.md:48` (*Figé*) \| `VL53L0X` → **`TOF050C-VL6180X`** · `0x76/0x77` → **`0x77`** · les 3 écarts de protoc | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-20.md | 1 | vl53l0x | 1 | \| **Owner** \| ⏳ **Décider l'étage *présence*** du réveil (3 voies écrites, ⚠️ la voie « VL53L0X » coûte une modif matéri | HISTORIQUE | correct-course DATE : il porte une decision a SA date. Surface entree au perimetre a la revue du 2026-08-30 (14 lignes a motif y vivaient hors filet, dont le §1.1 du 2026-08-20) |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-21.md | 1 | facade | 1 | **fondus** dans une moyenne, et le **200 mm de façade n'a PAS de fil tachymétrique** (`0 RPM` **dans | VRAI | le ventilateur 200 mm DE FACADE — fait MESURE (`0 RPM` dans le BIOS aussi, pas de fil tachymetrique) ⛔ NE PAS TOUCHER |
| cockpit | _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-21b.md | 1 | facade | 1 | \| `SYS_FAN2` — 200 mm façade \| — \| ⛔ **JAMAIS nommable, par aucun logiciel** : **pas de fil tachymétrique**, `0 RPM` **d | VRAI | le ventilateur 200 mm DE FACADE — fait MESURE (`0 RPM` dans le BIOS aussi, pas de fil tachymetrique) ⛔ NE PAS TOUCHER |
| desknode | README.md | 1 | busid-en-dur | 1 | > ⛔ pas une perte. **12 passages, 0 échec**, busid `3-5`, SHA au dossier §25.18. | HISTORIQUE | mention DATEE d'un busid, ⛔ pas une recette nue : elle se LIT, elle ne s'execute pas. Rendue visible par le motif elargi |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md | 1 | 506..516 | 1 | APPUI 1 · (133, 513)  -> TAP sur VENTILOS      <- LA JAUGE (barre y = 506..516) | HISTORIQUE | coordonnee morte CITEE dans un recit date — la narration reste, le renvoi a `widget jauge` fait foi (AC5.3) |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md | 1 | busid-en-dur | 1 | - 🔴 **LE BUSID `3-1` DU SKILL `desknode-board` EST FAUX SUR CETTE MACHINE.** La carte est sur | VRAI | la PIECE QUI REFUTE le busid du skill : `3-1` n'est pas seulement perime, il est OCCUPE (`V31GT 0e8d:201c`) |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md | 1 | 506..516 | 1 | (`VENTILOS 506..516`, jauge `y = 340..350`) pendant que `dn4-5` et `dn4-10` sont ouverts. | HISTORIQUE | coordonnee morte CITEE dans un recit date — la narration reste, le renvoi a `widget jauge` fait foi (AC5.3) |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | busid-en-dur | 1 | > ⚠️ **Busid `3-7`, pas `3-1`.** Le skill `/desknode-board`, le `README.md` et six stories écrivent | HISTORIQUE | mention DATEE d'un busid, ⛔ pas une recette nue : elle se LIT, elle ne s'execute pas. Rendue visible par le motif elargi |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md | 1 | 506..516 | 1 | formule contrôlée contre le relevé publié de dn3-2 : VENTILOS à `506..516`). | HISTORIQUE | coordonnee morte CITEE dans un recit date — la narration reste, le renvoi a `widget jauge` fait foi (AC5.3) |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md | 1 | 340..350 | 1 | > `y = 340..350` (jauge RAM, `dn4-1`) **ET `VENTILOS 506..516`** (`dn3-2`), sont | HISTORIQUE | coordonnee morte CITEE dans un recit date — la narration reste, le renvoi a `widget jauge` fait foi (AC5.3) |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md | 1 | 506..516 | 1 | > `y = 340..350` (jauge RAM, `dn4-1`) **ET `VENTILOS 506..516`** (`dn3-2`), sont | HISTORIQUE | coordonnee morte CITEE dans un recit date — la narration reste, le renvoi a `widget jauge` fait foi (AC5.3) |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md | 1 | 340..350 | 1 | > 🔴 **Corrigé par la revue du 2026-08-30** : ce renvoi ne nommait que `340..350` | HISTORIQUE | coordonnee morte CITEE dans un recit date — la narration reste, le renvoi a `widget jauge` fait foi (AC5.3) |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md | 1 | 506..516 | 1 | > et la gate ne surveillait pas du tout `506..516` (AC5.3 les met pourtant au | HISTORIQUE | coordonnee morte CITEE dans un recit date — la narration reste, le renvoi a `widget jauge` fait foi (AC5.3) |

| cockpit | .claude/skills/desknode-board/SKILL.md | 1 | 340..350 | 1 | périmés (`façade`, `VL53L0X`, `340..350`, `506..516`, busid en dur) sur **les deux | HISTORIQUE | coordonnee morte CITEE dans un recit date — la narration reste, le renvoi a `widget jauge` fait foi (AC5.3) |
| cockpit | .claude/skills/desknode-board/SKILL.md | 1 | 506..516 | 1 | périmés (`façade`, `VL53L0X`, `340..350`, `506..516`, busid en dur) sur **les deux | HISTORIQUE | coordonnee morte CITEE dans un recit date — la narration reste, le renvoi a `widget jauge` fait foi (AC5.3) |
| cockpit | .claude/skills/desknode-board/SKILL.md | 1 | facade | 1 | périmés (`façade`, `VL53L0X`, `340..350`, `506..516`, busid en dur) sur **les deux | HISTORIQUE | archive datee : dit ce qui etait vrai ALORS. Rendue visible par l'elargissement du perimetre a la revue du 2026-08-30 |
| cockpit | .claude/skills/desknode-board/SKILL.md | 1 | vl53l0x | 1 | périmés (`façade`, `VL53L0X`, `340..350`, `506..516`, busid en dur) sur **les deux | HISTORIQUE | archive datee : dit ce qui etait vrai ALORS. Rendue visible par l'elargissement du perimetre a la revue du 2026-08-30 |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | facade | 3 | >    **5** occurrences échappent à un motif sensible à la casse — ⚠️ **⛔ PAS « sur 29 »** : `29` est le compte des `VL53 | HISTORIQUE | archive datee : dit ce qui etait vrai ALORS. Rendue visible par l'elargissement du perimetre a la revue du 2026-08-30 |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | vl53l0x | 3 | >    **5** occurrences échappent à un motif sensible à la casse — ⚠️ **⛔ PAS « sur 29 »** : `29` est le compte des `VL53 | HISTORIQUE | archive datee : dit ce qui etait vrai ALORS. Rendue visible par l'elargissement du perimetre a la revue du 2026-08-30 |

## Ce que ce manifeste NE dit pas

- ⛔ **Il ne remplace pas la lecture.** Il enregistre un acte de lecture daté ; si le texte change,
  **le verdict est à refaire** — c'est pour ça que la gate sort en ROUGE sur toute occurrence
  nouvelle **ou déplacée**.
- ⚠️ **Une ligne source peut porter plusieurs occurrences du même motif.** Le manifeste porte
  alors **une ligne avec une colonne `n`** : c'est **un seul acte d'arbitrage** (même phrase,
  même verdict). La gate vérifie que **la somme des `n`** égale le compte de l'arbre.
- ⛔ **Les ARCHIVES du cockpit** (stories `dn*.md` livrées, investigations) sont **comptées et
  listées par la gate**, ⛔ pas arbitrées ici : elles disent ce qui était vrai ALORS. **Une seule
  exception, et elle est mesurée** : le motif `busid-en-dur` est arbitré **partout, archives
  comprises** — une recette se copie-colle même depuis une story fermée, et `3-1` n'est pas
  seulement périmé, **il est OCCUPÉ** (`V31GT`, `0e8d:201c`) : la suivre **détache le mauvais
  périphérique**.
- ⛔ **Auto-références exclues, et déclarées** : ce fichier, `tools/verif_dossier_dn415.py`, la
  story `dn4-15-*.md`, la ligne `dn4-15-*` du tracker, `mesures/`, `sprint-board-desknode.html`.

## Le compte

> 🔴 **RECOMPTE PAR LA REVUE DU 2026-08-30.** Ces chiffres ne sont plus de la
> prose : **la gate les CONFRONTE au detail** a chaque tir (ils ne l'etaient par
> RIEN, et derivaient donc en silence — dans le fichier meme dont la raison
> d'etre est que le dossier ne mente plus sur ses chiffres).

| verdict | occurrences |
|---|---:|
| `FAUX` | 0 |
| `VRAI` | 120 |
| `HISTORIQUE` | 82 |
| `SANS-RAPPORT` | 2 |
| **TOTAL** | **204** |

> 🆕 **RATTRAPÉ PAR `dn4-16` LE 2026-08-30 — +5 `HISTORIQUE`, +5 `vl53l0x`, total 199 → 204.**
> `dn4-16` a écrit **cinq citations `VL53L0X`** dans le ledger (le bandeau de collision
> `bmad-loop-sweep`, et deux lignes de disposition). Elles sont **légitimes** — ce sont des faits
> datés et une mesure, ⛔ pas des assertions sur le bus — et elles sont **arbitrées ci-dessous**,
> comme la gate l'exige. ⚠️ **28 adresses** de ce manifeste ont dû être **RE-ANCRÉES** — **27** dans
> `deferred-work.md` et **1** dans `epics-desknode-v1.md` : les 248 lignes de disposition insérées par
> `dn4-16` les avaient décalées. **Aucun verdict n'a changé, seule la colonne `ligne` a bougé.**
> ⛔ **Correctif de sa REVUE DE CODE (2026-08-30)** : il était écrit ici **« 50 adresses — 27 + 23 »**.
> Mesure sur le diff livré : **28** lignes de données réécrites (27 + 1) et **5** neuves. Les 23 autres
> lignes `epics-…` sont **au-dessus** du point d'insertion dans l'epic — elles n'ont pas pu bouger.
> ⚠️ **Ré-ancré une SECONDE fois le 2026-08-30**, par la revue elle-même : ses corrections de chiffres
> ont redécalé le ledger et refait rougir cette gate à **62 KO**. **30** adresses re-mappées, par
> correspondance de lignes CALCULÉE (`difflib` sur l'avant/après), ⛔ pas à la main. Le mécanisme se
> repaiera à chaque écriture tant que l'ancrage est un NUMÉRO — porté par `dn4-24`.
> 🔴 **Et c'est la démonstration en direct de ce que `dn4-16` a mesuré** : ce manifeste ancre par
> **NUMÉRO DE LIGNE**, donc il se périme à chaque écriture dans le fichier qu'il décrit — 62
> contrôles ont rougi d'un coup, sans qu'une seule occurrence change de sens. Voir l'entrée
> `⇒ [dn4-16 …] CONNAISSANCE` du ledger : *« une adresse se vérifie par MOTIF, jamais par numéro »*.

| motif | occurrences |
|---|---:|
| `facade` | 66 |
| `vl53l0x` | 85 |
| `340..350` | 20 |
| `506..516` | 12 |
| `busid-en-dur` | 21 |

## Le manifeste

### 🔴 LA 3ᵉ COLONNE N'EST PLUS UN NUMÉRO DE LIGNE — `dn4-24`, 2026-08-30

**Ce qui se payait.** Chaque occurrence était ancrée par son **numéro de ligne**.
Un numéro ne dit rien du CONTENU : il dit où la ligne se trouvait *le jour où on l'a lue*.
Or ces fichiers s'écrivent tous les jours — `deferred-work.md` reçoit une entrée,
`epics-desknode-v1.md` une correction — et **tout ce qui est en dessous se décale**.
⇒ Insérer **une seule ligne ordinaire** en tête de `deferred-work.md` faisait passer
`verif_dossier_dn415.py` à **69 KO** *sans qu'une seule occurrence change de sens*.

⚠️ **Et ce n'est pas une inquiétude théorique.** Au moment du ré-ancrage, **trois adresses
étaient DÉJÀ périmées** — `dn_console.c` `7018`/`7817`/`8160` → `7029`/`7828`/`8171`,
décalées **le jour même** par un correctif de `dn4-24`. Le cadrage de la story avait déjà
mesuré la même dérive ailleurs (`verif_veille_dn33.py:2034` écrit au ledger, `:2072` mesuré
le lendemain).

**Ce qui ancre maintenant : le TEXTE.** La clé d'arbitrage est

> `(dépôt, fichier, motif, les 48 premiers caractères normalisés de la citation, RANG)`

La colonne s'appelle donc **`occ`** — le **rang** de l'occurrence parmi celles que *rien
d'autre ne distingue*. ⛔ **Ce n'est pas une adresse** : elle ne bouge pas quand le fichier
grossit. Elle vaut **`1` pour 194 des 195 occurrences**.

⚠️ **AC4.4 — LA SEULE OCCURRENCE QUI NE SE DISTINGUE PAS PAR SON TEXTE, DÉCLARÉE :**
`hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md`, motif `340..350`, deux lignes **au texte
identique** (« *renvoi (`dn4-15`, 2026-08-30) — la coordonnée…* »). Elles portent `occ = 1`
et `occ = 2`, dans l'ordre du fichier. ⛔ Elles ne sont pas laissées en numéro : le rang
**est** leur motif de distinction, et il est dit ici.

⚠️ **Ce que le rang NE protège PAS, et c'est déclaré :** si ces deux lignes-là étaient
permutées, le manifeste ne le verrait pas — elles sont indiscernables. Leur verdict est
le même (`VRAI`), donc l'échange est sans effet sur l'arbitrage.

---

### ⚠️ CE QUE LE RÉ-ANCRAGE COÛTE — revue de code du 2026-08-31, **arbitré par l'owner**

Le ré-ancrage par le contenu rend **le déplacement pur invisible**, et c'est sa **raison
d'être** : c'est exactement ce qui fait passer le témoin d'AC4.2 de **69 KO à 0 KO**. Mais un
gain n'est pas gratuit, et ce qu'il coûte s'écrit ici plutôt que de se découvrir un jour.

🔴 **CE QUI N'EST PLUS VU.** Une occurrence portant le verdict **`HISTORIQUE`** — dont la
définition est « *vrai à sa date* » — peut être **déplacée dans un bloc de prescription
vivante** et y garder son verdict, **gate verte**. Mesuré le 2026-08-31 : une ligne arbitrée
remontée en tête de son fichier ⇒ `BILAN : 21 OK, 0 KO`. Le manifeste ne connaît plus la
**place** d'un énoncé, seulement son **texte** — or `HISTORIQUE` est un verdict dont le sens
dépend du voisinage : un fait périmé cité dans une rétrospective est juste ; le même fait
déplacé dans une consigne devient une **instruction fausse**.

⚖️ **ARBITRÉ LE 2026-08-31 — LE COÛT S'ÉCRIT, LA CLÉ NE SE RESSERRE PAS.** Ajouter la section
porteuse à la clé rougirait sur un déplacement **entre** sections — mais reprendrait d'une
main ce qu'AC4.2 vient de gagner, puisque toute réorganisation d'un dossier redeviendrait un
rouge de masse **sans qu'un sens change**. ⇒ Le coût est **déclaré**, ⛔ pas refermé.

🎯 **CE QUI EST VU, EN REVANCHE, ET C'EST NEUF DEPUIS LE 2026-08-31** : **raccourcir** une
ligne arbitrée ne passe plus. Le contrôle comparait un **préfixe commun**
(`n = min(len(a), len(b))`), ce qui rendait toute troncature structurellement invisible —
35 caractères retirés d'un énoncé arbitré rendaient `20 OK / 0 KO`. Une **garde de longueur**
a été ajoutée, et elle est fondée sur une mesure : sur les 195 lignes, la citation de l'arbre
n'est **jamais** plus courte que celle du manifeste (181 égales, 14 plus longues à cause de
l'échappement des `|`, **0 plus courte**). Donc « arbre plus court » ne peut signifier qu'une
chose : **la ligne source a perdu du texte**.

⚠️ **COÛT RÉSIDUEL, NOMMÉ** : un **ajout** au-delà du 120ᵉ caractère reste invisible — le
manifeste ne stocke que 120 caractères, il ne peut pas garder ce qu'il n'a jamais lu.

| depot | fichier | occ | motif | n | citation (≤ 120 car.) | verdict | motif du verdict |
|---|---|---:|---|---:|---|---|---|
| desknode | README.md | 1 | facade | 1 | côté de la tour PC** (décision owner du 2026-08-17 — le brief dit encore « monté sur la façade du | VRAI | la NOTICE de correction : le README dit « posé à côté », décision owner du 2026-08-17, et signale que le brief était périmé |
| desknode | README.md | 1 | vl53l0x | 1 | \| **`tof`** (dn4-7) \| le **VL6180X** `0x29` instruit **pour de bon** — `etat` (registres, **lecture seule**), `sr03`,  | VRAI | le PIÈGE DE SOURCE : deux URL nommées « VL6180X » rendaient en HTTP 200 un vrai PDF ST… du VL53L0X |
| desknode | README.md | 1 | vl53l0x | 1 | \| **`i2c`** (dn2-1/**dn4-2**) \| le **bus vu de ses adresses** : `i2c` scanne 0x08..0x77, `i2c lire <addr> <reg> [n]` l | VRAI | le TÉMOIN NÉGATIF de l'identification (`i2c lire 29 C0` ne doit PAS rendre `EE` de façon reproductible) |
| desknode | README.md | 1 | facade | 1 | ⛔ **ET UN VENTILATEUR NE SERA JAMAIS PUBLIABLE** : le **200 mm de façade** n'a **pas de fil | VRAI | le VENTILATEUR 200 mm DE FAÇADE de la tour — fait MESURÉ (pas de fil tachymétrique, `0 RPM` dans le BIOS aussi). ⛔ NE PAS TOUCHER |
| desknode | README.md | 1 | vl53l0x | 1 | \| 🔴 **TOF050C-VL6180X** (⛔ **PAS** un VL53L0X) \| proximité / présence \| **`0x29` MESURÉ** ✅ **QUALIFIÉ PAR LECTURE**  | VRAI | la CORRECTION elle-même : « TOF050C-VL6180X (⛔ PAS un VL53L0X) », qualifié par lecture |
| desknode | tools/verif_sr03.py | 1 | vl53l0x | 1 | HTTP 200 un PDF ST authentique... du VL53L0X. Le code de retour et le nom de | VRAI | le piège de source, écrit dans le harnais même qui l'a attrapé |
| desknode | tools/fixtures/PROVENANCE.md | 1 | facade | 1 | facade n'a pas de fil tachymetrique, 0 RPM DANS LE BIOS AUSSI). | VRAI | le ventilateur 200 mm de façade — provenance d'une fixture, fait mesuré |
| desknode | firmware/desknode/sdkconfig.defaults | 1 | facade | 1 | #    monté sur la façade ; corrigé par dn4-15 le 2026-08-30). Ce n'est pas une | VRAI | corrigé par dn4-15 : le LIEU est « posé à côté », l'argument PSRAM est CONSERVÉ, et l'amplitude thermique réelle est déclarée NON MESURÉE |
| desknode | firmware/desknode/sdkconfig.defaults | 1 | vl53l0x | 1 | #    🔴 dn4-15, 2026-08-30 : cette ligne écrivait « VL53L0X ». C'était le SEUL | VRAI | la correction elle-même : l'inventaire de bus nommait `VL53L0X`, il nomme désormais `VL6180X` (c'était LE seul vrai défaut des 29) |
| desknode | firmware/desknode/main/desknode_main.c | 1 | facade | 1 | * observation de façade. Le seul instrument qui peut réellement CONTREDIRE | SANS-RAPPORT | l'IDIOME FRANÇAIS « observation de façade » (= superficielle). ⛔ Aucun rapport avec le lieu ni avec le ventilateur : un `sed` global le corromprait |
| desknode | firmware/desknode/main/dn_capteurs.h | 1 | vl53l0x | 1 | * (⚠️ « dn4-1 » et « VL53L0X » étaient DEUX étiquettes fausses — cf. dn_pins.h). ⚠️ Il n'est pour | VRAI | le récit des DEUX étiquettes fausses (« dn4-1 » et « VL53L0X »), avec renvoi à dn_pins.h |
| desknode | firmware/desknode/main/dn_console.c | 1 | vl53l0x | 1 | *  (b) 🔴 « VL53L0X » : REFUTE PAR L'INVENTAIRE PHYSIQUE. Le module est un | VRAI | « VL53L0X : RÉFUTÉ PAR L'INVENTAIRE PHYSIQUE » — la réfutation, imprimée à l'aide |
| desknode | firmware/desknode/main/dn_console.c | 1 | vl53l0x | 1 | "REPRODUCTIBLE, c'est un VL53L0X et le sachet ment " | VRAI | le témoin négatif, dans le texte d'aide de la commande `tof` |
| desknode | firmware/desknode/main/dn_console.c | 1 | vl53l0x | 1 | *    URL Pololu rendaient un PDF ST authentique en HTTP 200… du VL53L0X. Le | VRAI | le piège de source Pololu, imprimé à l'aide |
| desknode | firmware/desknode/main/dn_display.h | 1 | facade | 1 | /* Façade booléenne héritée de dn1-2 : `false` -> 0 %, `true` -> 100 %. | SANS-RAPPORT | le PATRON DE CONCEPTION (« Façade booléenne héritée de dn1-2 » = *facade pattern*). ⛔ Aucun rapport |
| desknode | firmware/desknode/main/dn_env.c | 1 | vl53l0x | 1 | * ⚠️ C'est exactement ce qui distingue cette puce d'un VL53L0X, et ce qui a | VRAI | ce qui DISTINGUE le VL6180X d'un VL53L0X — connaissance opérationnelle |
| desknode | firmware/desknode/main/dn_env.c | 1 | vl53l0x | 1 | *    permis de REFUTER l'étiquette « VL53L0X » (§13.16.7). */ | VRAI | « ce qui a permis de RÉFUTER l'étiquette » |
| desknode | firmware/desknode/main/dn_link.c | 1 | facade | 1 | *    **il n'existe AUCUN flux entrant mesurable.** Le 200 mm de façade n'a pas | VRAI | le ventilateur 200 mm de façade, sans fil tachymétrique — fait MESURÉ |
| desknode | firmware/desknode/main/dn_pins.h | 1 | vl53l0x | 1 | *    est rapporté sur le VL53L0X — la puce sœur. | VRAI | « la puce sœur » : le mode de panne rapporté sur le VL53L0X, connaissance opérationnelle |
| desknode | firmware/desknode/main/dn_pins.h | 1 | vl53l0x | 1 | * 🔴 LE 3ᵉ N'EST PAS UN VL53L0X : C'EST UN **TOF050C-VL6180X**. Ce fichier, le | VRAI | 🎯 LE BLOC QUI TRANCHE — « LE 3ᵉ N'EST PAS UN VL53L0X : C'EST UN TOF050C-VL6180X ». C'est la CIBLE de tous les renvois de cette story |
| desknode | firmware/desknode/main/dn_pins.h | 1 | vl53l0x | 1 | *    « VL53L0X » du 2026-08-14 au 2026-08-19. L'addendum §3 du brief avait POSÉ | VRAI | le récit DATÉ de l'étiquette fausse (portée du 2026-08-14 au 2026-08-19) |
| desknode | firmware/desknode/main/dn_ui.c | 1 | facade | 1 | * 🔴 `FRONT_IN` (200 mm façade) N'EST **JAMAIS** PUBLIABLE : il n'a pas de | VRAI | le ventilateur `FRONT_IN` 200 mm de façade — JAMAIS publiable, fait mesuré |
| desknode | firmware/desknode/main/dn_ui.c | 1 | facade | 1 | *    ⛔ `FRONT_IN` (200 mm façade) n'apparaît NULLE PART : pas de fil | VRAI | le même ventilateur, dans la table des sources |
| desknode | agent/dn_agent.py | 1 | facade | 1 | # ⛔ `FRONT_IN` (200 mm facade, `fan/3` ou `fan/5`) N'EST PAS DANS CETTE TABLE ET | VRAI | le ventilateur `FRONT_IN` 200 mm de façade, côté agent Windows |
| desknode | agent/dn_agent.py | 1 | facade | 1 | facade n'a pas de tachy (0 RPM dans le BIOS aussi) et le ventilateur du | VRAI | « pas de tachy, 0 RPM dans le BIOS aussi » — le fait mesuré, côté agent |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md | 1 | facade | 1 | > monté sur la façade** ; la phrase disait le contraire jusqu'au **2026-08-30** | VRAI | la notice de correction posée par dn4-15 : lieu corrigé, argument PSRAM conservé, amplitude thermique déclarée NON mesurée |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md | 1 | vl53l0x | 1 | VL53L0X, INA219 sur ce même bus) aurait fait défiler l'écran en permanence, et | HISTORIQUE | narration d'un arbitrage ANTÉRIEUR au 2026-08-19 — vraie à sa date. ⇒ RENVOI ajouté (AC3.4), narration ⛔ PAS réécrite |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md | 1 | vl53l0x | 1 | > ⚠️ **RENVOI (`dn4-15`, 2026-08-30) — « VL53L0X » ci-dessus est la narration d'un | VRAI | le RENVOI lui-même, posé par dn4-15/AC3.4 |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md | 1 | 340..350 | 1 | de faire viser quoi que ce soit** : elle reproduit `y = 340..350` (dn4-1) sur | HISTORIQUE | relevé de séance du 2026-08-20, explicitement « sur l'ANCIENNE géométrie » ⇒ vrai à sa date. RENVOI ajouté |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md | 1 | 340..350 | 1 | > ⚠️ **RENVOI (`dn4-15`, 2026-08-30)** — la coordonnée `y = 340..350` citée ci-dessus | VRAI | le RENVOI lui-même |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md | 1 | 340..350 | 1 | \| `dn4-1` \| — \| `340..350` \| calculé, **déjà déclaré périmé** (`CASE_H` 156 → 163) \| | VRAI | §22.3 — le tableau du DÉSACCORD PUBLIÉ, qui déclare lui-même `340..350` « déjà périmé » et que `widget jauge` tranche |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md | 1 | 340..350 | 1 | (`VENTILOS 506..516`, jauge `y = 340..350`) pendant que `dn4-5` et `dn4-10` sont ouverts. | HISTORIQUE | compte rendu daté de la séance dn4-14-2 : énumère l'état publié À SA DATE. RENVOI ajouté, narration ⛔ intacte |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md | 2 | 340..350 | 1 | > ⚠️ **RENVOI (`dn4-15`, 2026-08-30)** — la coordonnée `y = 340..350` citée ci-dessus | VRAI | le RENVOI lui-même |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | vl53l0x | 1 | c'est l'une d'elles qui **réfute l'étiquette « VL53L0X »** portée depuis le 2026-08-14 par le brief, | VRAI | « réfute l'étiquette VL53L0X » — la réfutation |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | vl53l0x | 1 | \| `2026-08-19_1718-tof050c-vl6180x-face-capteur-et-sachet.jpg` \| 17:18:48 \| 🔴 **LA PIÈCE QUI RÉFUTE « VL53L0X ».** Ét | VRAI | 🎯 LA PIÈCE QUI RÉFUTE : la photo du sachet, `TOF050C-VL6180X` lisible |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | vl53l0x | 1 | > 🔴 **LE 3ᵉ CAPTEUR N'EST PAS UN VL53L0X. C'EST UN VL6180X — et *« même famille ToF »* est faux | VRAI | « LE 3ᵉ CAPTEUR N'EST PAS UN VL53L0X » — la réfutation, en tête de § |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | vl53l0x | 1 | > le 2026-08-14 — *« La roadmap historique nomme "TOF050C" là où le dump dit VL53L0X — même famille | VRAI | citation DATÉE de l'addendum du 2026-08-14, à l'intérieur du bloc qui la réfute |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | vl53l0x | 1 | > \| \| **VL6180X** (ce qu'on a) \| **VL53L0X** (ce que six documents annoncent) \| | VRAI | la TABLE COMPARATIVE VL6180X (ce qu'on a) vs VL53L0X (ce que six documents annonçaient) |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | vl53l0x | 1 | « dn4-1 » et « VL53L0X » — deux étiquettes fausses, corrigées par la revue de code du 2026-08-20 : | VRAI | le récit de la correction du 2026-08-20 (« deux étiquettes fausses ») |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | facade | 1 | > Le module sera **POSÉ À CÔTÉ de la tour**, pas monté dans la façade du Phantom 630 — verbatim : | VRAI | 🎯 LA DÉCISION OWNER DU 2026-08-17, avec son verbatim — la source de première main |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | facade | 1 | > ⚠️ **Le BRIEF disait encore « monté sur la façade »** — le README, lui, est corrigé | VRAI | la notice, CORRIGÉE par dn4-15/AC3.3 : elle ne vise plus que le brief (le README est corrigé depuis le 2026-08-17) |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | facade | 1 | > littéralement *« le montage en facade est PERIME »*). ⇒ **une réfutation vaut ce | VRAI | citation du TITRE du commit `b554a4e` — la preuve que la décision existait |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | vl53l0x | 1 | 1. ~~**dn4-1** — les 3 autres breakouts (BH1750 `0x23`, VL53L0X `0x29`, INA219 `0x40`) : **ni | VRAI | ligne BARRÉE (`~~…~~`) : le texte d'origine de dn4-1, conservé lisible |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | vl53l0x | 1 | `VL53L0X` mais un **`TOF050C-VL6180X`**, tranché **par la lecture** (`i2c lire16 29 0000` → `B4`, | VRAI | la réfutation PAR LA LECTURE (`i2c lire16 29 0000` → `B4`, 5/5) |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | vl53l0x | 1 | \| **VL53L0X** (témoin négatif) \| `i2c lire 29 C0` · `C1` · `C2` — index **8 bits** \| **`01` · `00` · `00`** \| ⛔ **RÉ | VRAI | 🎯 LE TÉMOIN NÉGATIF — `01/00/00` au lieu de `EE/AA/10`. C'est LA MESURE qui tranche |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | vl53l0x | 1 | > BH1750/**VL53L0X**/INA219 se ré-arbitrent chacun sur le même critère 1. »* | HISTORIQUE | citation d'un arbitrage antérieur, dans un blockquote — vraie comme citation, il lui manquait un renvoi. ⇒ RENVOI ajouté (AC3.4) |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | vl53l0x | 1 | > **`TOF050C-VL6180X`**, ⛔ **pas** un `VL53L0X` : cf. **§13.16.7** et | VRAI | le RENVOI lui-même, posé par dn4-15/AC3.4 |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | vl53l0x | 1 | \| `q=vl53` \| 200 \| `espp/vl53l` 1.1.8 · `rjrp44/vl53l5cx` 4.0.1 · `rjrp44/vl53l8cx` 4.0.1 · `grrtzm/v53l7cx-library`  | HISTORIQUE | 🔴 `vl53l0x` EN CASSE BASSE — relevé de recherche du registre de composants (`q=vl53`). Invisible à un grep sensible à la casse ; la ligne dit elle-même « tous des VL53Lxx, puce DIFFÉRENTE » |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | vl53l0x | 1 | \| `pololu.com/file/0J1187/VL6180X.pdf` \| ⛔ un **vrai PDF ST**… du **VL53L0X** (titre : *« World's smallest Time-of-Fli | VRAI | le PIÈGE DE SOURCE : `pololu.com/…/VL6180X.pdf` rend un vrai PDF ST du VL53L0X |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | vl53l0x | 1 | **VL53L0X**, l'autre un schéma **Pololu**. Je les avais déjà rangés comme sources avant de lire | VRAI | le récit du piège de source (deux documents rangés avant d'être lus) |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md | 1 | vl53l0x | 1 | VL53L0X, la puce sœur. | VRAI | « la puce sœur » — le mode de panne rapporté sur le VL53L0X |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md | 1 | 340..350 | 1 | tap sans que rien ne le signale. La bande de la jauge RAM est haute de **10 px** (`y = 340..350`, | HISTORIQUE | relevé de la séance tactile du 2026-08-20 (§13.11.7) — vrai à sa date, RENVERSÉ depuis par §22.3. RENVOI ajouté, narration ⛔ intacte |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md | 1 | facade | 1 | entrant mesurable.** Le 200 mm de façade n'a pas de fil tachymétrique (`0 RPM` **dans le BIOS | VRAI | le ventilateur 200 mm de façade, `0 RPM` dans le BIOS aussi — fait MESURÉ |
| desknode | hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md | 1 | facade | 1 | \| L7 \| 🆕 **`FRONT_IN` (200 mm façade) ne sera JAMAIS publiable** \| ⛔ **CLOS — matériel** \| **Pas de fil tachymétriqu | VRAI | L7 — le même ventilateur, entrée CLOSE pour cause matérielle |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/.memlog.md | 1 | facade | 2 | - (decision) 🔴 **2026-08-17 — PAS DE MONTAGE EN FAÇADE.** Verbatim owner : *« y aura pas de montage définitif dans le ph | VRAI | l'entrée de journal posée par dn4-15/AC4 : elle porte la décision ET conserve le `topic:` d'origine en toutes lettres (un champ YAML ne se barre pas) |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/addendum.md | 1 | facade | 1 | tachymètre. ⛔ **Le 200 mm de façade n'a PAS de fil tachymétrique** — `0 RPM` **DANS LE BIOS AUSSI** | VRAI | le ventilateur 200 mm de façade — ⛔ LAISSÉ INTACT par AC4.3, et le bloc de décision le dit |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/addendum.md | 1 | facade | 1 | - OTA : hors V1 sauf objection ; ~~redevient important une fois le module vissé dans la façade~~ ⚠️ *[périmé — voir la D | VRAI | phrase BARRÉE par AC4 + son motif : le module ne sera pas vissé, donc le motif de réouverture de l'OTA tombe (⛔ pas sa conclusion) |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/addendum.md | 1 | vl53l0x | 1 | - La roadmap historique nomme « TOF050C » là où le dump dit VL53L0X — même famille ToF, noter la réf réelle du breakout  | HISTORIQUE | note de cadrage du 2026-08-14 — c'est LA SOURCE de l'étiquette fausse, et « même famille ToF » est faux. ⇒ RENVOI ajouté, note ⛔ conservée telle quelle |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/addendum.md | 1 | facade | 1 | - ~~Support/cadre imprimé 3D pour la façade Phantom 630, passage du câble USB à l'intérieur du boîtier.~~ ⚠️ *[périmé —  | VRAI | support 3D + passage de câble : BARRÉS et déclarés ANNULÉS (⛔ pas reportés) par AC4 |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | facade | 1 | > ## 🔴 DÉCISION OWNER DU **2026-08-17** — ⛔ **PAS DE MONTAGE EN FAÇADE.** AMENDEMENT DATÉ, ⛔ RIEN N'EST EFFACÉ | VRAI | le BLOC DE DÉCISION DATÉ posé par AC4 (titre) |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | facade | 1 | > dont le titre dit littéralement *« le montage en facade est PERIME »*. | VRAI | le bloc de décision : citation du titre du commit `b554a4e`, la preuve datée |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | facade | 1 | > 1. le **support / cadre imprimé 3D** pour la façade du Phantom 630 (addendum §5) ; | VRAI | le bloc de décision : ce qui TOMBE (support 3D pour la façade) |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | facade | 1 | > - 🟢 **`Résumé › Périmètre V1 › Dehors` — « le 200 mm de façade n'a pas de fil | VRAI | le bloc de décision : ce qui NE tombe PAS (le ventilateur), pour qu'on n'y voie pas un oubli |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | facade | 1 | >   tachymétrique »** (brief l. 46) et **addendum §2 « Le 200 mm de façade n'a PAS de | VRAI | le bloc de décision : idem, côté addendum §2 |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | facade | 1 | >   **LAISSÉS INTACTS**. Ils parlent du **VENTILATEUR 200 mm DE FAÇADE de la tour**, | VRAI | le bloc de décision : l'avertissement d'homonymie (le VENTILATEUR, ⛔ pas le module) |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | facade | 1 | >   remplacement en masse du mot « façade » le casserait. | VRAI | le bloc de décision : « un remplacement en masse du mot façade le casserait » |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | facade | 1 | DeskNode est un mini-display tactile de 2,8" ~~monté verticalement sur la façade de la tour PC (NZXT Phantom 630)~~ ⚠️ * | VRAI | §Résumé exécutif — phrase d'origine BARRÉE, correction posée à côté (AC4.2) |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | facade | 1 | Un module autonome ~~sur la façade de la tour~~ ⚠️ *[périmé — voir la DÉCISION OWNER DU 2026-08-17 en tête de brief]* ** | VRAI | §La solution — phrase d'origine BARRÉE, correction posée à côté |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | facade | 1 | ⛔ **Un ventilateur ne sera JAMAIS publiable** : le 200 mm de façade n'a **pas de fil | VRAI | le ventilateur 200 mm de façade — ⛔ LAISSÉ INTACT par AC4.3 |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | vl53l0x | 1 | 🔴 **Ce n'est PAS un VL53L0X** — corrigé le 2026-08-20 (`dn4-2`, correct-course du même jour). L'étiquette venait d'un du | VRAI | la CORRECTION du 2026-08-20 : « Ce n'est PAS un VL53L0X », avec sa mesure |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | facade | 1 | - Installation : portrait, ~~sur façade Phantom 630~~ ⚠️ *[périmé — voir la DÉCISION OWNER DU 2026-08-17 en tête de brie | VRAI | §Installation — phrase d'origine BARRÉE ; le « POC sur bureau » EST l'installation |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | facade | 1 | - OTA : dans V1 ou reporté (le flash USB-C suffit ~~tant que le module n'est pas vissé dans la façade~~ ⚠️ *[périmé — vo | VRAI | §OTA — phrase d'origine BARRÉE ; l'USB-C reste accessible, ce qui RENFORCE le report |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | vl53l0x | 1 | Le module est un **TOF050C-VL6180X**, pas un VL53L0X. ST garantit le VL6180X **jusqu'à 100 mm** | VRAI | l'arbitrage de portée : VL6180X garanti 100 mm vs VL53L0X 2 m |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | vl53l0x | 1 | revendeur**, ⛔ pas une spec — là où le VL53L0X qu'annonçaient six documents portait, lui, à **2 m**. | VRAI | idem — la portée annoncée par six documents |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | vl53l0x | 1 | 1. **Ajouter un VL53L0X** (2 m) à côté, pour l'étage présence ; | VRAI | une VOIE OUVERTE (ajouter un VL53L0X pour l'étage présence) — ⛔ pas une description du matériel actuel |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | vl53l0x | 1 | 🔴 **PIÈGE À NOMMER AVANT DE CHOISIR LA VOIE 1 — LES DEUX ToF SE COLLISIONNENT.** Le VL53L0X a | VRAI | le PIÈGE de collision à `0x29` entre les deux ToF — connaissance opérationnelle |
| cockpit | _bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/brief.md | 1 | vl53l0x | 1 | VL6180X embarque un **capteur de lumière ambiante** que le VL53L0X n'a pas, et qui **recouvre | VRAI | la différence d'ALS entre les deux puces — connaissance opérationnelle |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | vl53l0x | 1 | pas un VL53L0X, et le BME680 est à `0x77` (`SDO` haut), pas « 0x76/0x77 ».* | VRAI | notice de correction en tête d'epic (« pas un VL53L0X ») |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | facade | 1 | que le module n'est pas vissé dans la façade). | HISTORIQUE | citation du brief au 2026-08-14 (« tant que le module n'est pas vissé »), périmée par la décision du 2026-08-17 — traitée dans le brief par AC4. ⛔ l'epic n'est pas édité hors du bloc dn4-15 (périmètre) |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | 340..350 | 1 | pas mais `CASE_H` oui — `VENTILOS 506..516` de `dn3-2`, bande de jauge `y = 340..350` de `dn4-1`) | HISTORIQUE | citation de l'état publié au 2026-08-25 dans le bloc d'epic dn4-4. ⛔ hors périmètre d'édition de cette story |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | vl53l0x | 1 | consiste à ajouter un VL53L0X **collisionne à `0x29`** avec le module déjà soudé, dont l'`XSHUT` | VRAI | le piège de collision à `0x29` (voie « ajouter un VL53L0X ») |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | vl53l0x | 1 | 2. **Le VL6180X porte un ALS** que le VL53L0X n'a pas, et qui **recouvre partiellement le BH1750**. | VRAI | la différence d'ALS entre les deux puces |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | facade | 1 | > \| *« monté sur la façade »* \| **2** occ. \| **34** occ. hors archives sur 2 dépôts (**57** au balayage total) \| 🔴 **sou | VRAI | bloc de CORRECTION AC7.3 : la ligne re-comptée du tableau |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | vl53l0x | 1 | > \| citation `VL53L0X` \| **17** occ. sur 3 `.md`, à corriger \| **29** occ. dans `desknode` seul, **11 dans le CODE**  | VRAI | bloc de correction AC7.3 : la ligne re-comptée du tableau |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | 340..350 | 1 | > \| `y = 340..350` \| **5** occ., console en `:3247`/`:3953` \| **8** occ., console en **`:4366`/`:5395`** \| 🔴 **compt | VRAI | bloc de correction AC7.3 : la ligne re-comptée du tableau |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | facade | 1 | > 1. 🔴 **`façade` a TROIS HOMONYMES, et un remplacement en masse casse un fait mesuré.** Le mot | VRAI | bloc de correction AC7.3 : les TROIS homonymes de `façade` |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | facade | 1 | >    désigne aussi le **ventilateur 200 mm DE FAÇADE de la tour** (13 occ., **VRAI et MESURÉ** : | VRAI | bloc de correction AC7.3 : le ventilateur 200 mm, 13 occ. VRAIES |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | facade | 2 | >    de façade »* (`desknode_main.c:125`) et le **patron de conception** *« Façade booléenne »* | VRAI | bloc de correction AC7.3 : l'idiome et le patron de conception |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | vl53l0x | 1 | > 3. 🔴 **Le compte de `VL53L0X` est presque exact, et son VERDICT est INVERSÉ.** Les 29 | VRAI | bloc de correction AC7.3 : le verdict INVERSÉ, 28/29 légitimes |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | vl53l0x | 1 | >    occurrences ont été **lues une par une** : **28 sont légitimes** — elles nomment le VL53L0X | VRAI | bloc de correction AC7.3 : les réfutations qu'il ne fallait pas supprimer |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | facade | 1 | >    `Façade` ×1) — et **4 vivent dans des dossiers que ce bloc ne nomme pas** (`agent/`, | VRAI | bloc de correction AC7.3 : `Façade` et les dossiers jamais nommés |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | facade | 1 | \| Le brief dit encore *« monté sur la façade de la tour »* \| **2 occurrences** (`brief.md:12`, `:24`) \| | HISTORIQUE | LIGNE DU TABLEAU D'ORIGINE (2026-08-25), ⛔ CONSERVÉE, pas effacée — son compte est faux et la correction est juste au-dessus |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | vl53l0x | 1 | \| Une citation **`VL53L0X`** subsiste (le module est un **VL6180X**) \| **17 occurrences** : `capteurs-i2c.md` (13), `R | HISTORIQUE | LIGNE DU TABLEAU D'ORIGINE, ⛔ conservée — « 17 occurrences » : compte quasi exact, verdict inversé |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | 340..350 | 1 | \| Les coordonnées **`y = 340..350`** survivent dans les textes de péremption \| **5 occurrences**, dont 🔴 **DEUX dans l | HISTORIQUE | LIGNE DU TABLEAU D'ORIGINE, ⛔ conservée — compte faux ET adresses qui ne pointent rien |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | vl53l0x | 1 | ⚠️ **`VL53L0X` vs `VL6180X` porte un risque particulier** : ce sont deux capteurs ToF réels et | VRAI | le motif de la story : nommer le mauvais composant peut faire re-tenter une piste éliminée |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | facade | 1 | \| `SYS_FAN2` — 200 mm façade \| — \| ⛔ **JAMAIS nommable, PAR AUCUN LOGICIEL** \| | VRAI | `SYS_FAN2` — le ventilateur 200 mm de façade, JAMAIS nommable. ⚠️ HORS des 11 `VRAI` listés par la story |
| cockpit | _bmad-output/planning-artifacts/epics-desknode-v1.md | 1 | vl53l0x | 1 | > `VL53L0X` légitimes. ⇒ un 5ᵉ verdict, **`CONNAISSANCE`**, a été ajouté. **Écart de cadrage | HISTORIQUE | 🆕 AJOUT `dn4-16` (2026-08-30) — la CORRECTION EN PLACE du bloc `dn4-16` cite la mesure de `dn4-15` (28 legitimes sur 29) pour justifier le 5e verdict `CONNAISSANCE`. Fait DATE, ⛔ pas une assertion sur le bus. |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | 340..350 | 1 | contre un relevé déjà publié** (elle reproduit `y = 340..350` de `dn4-1` sur | HISTORIQUE | récit de la séance du 2026-08-20 (formule contrôlée sur l'ANCIENNE géométrie) — vrai à sa date |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | 340..350 | 1 | atteint la bande `y = 340..350`, parce que `RAM` était à « -- » ⇒ **jauge vide, donc quasi | HISTORIQUE | récit de séance : pourquoi le tap n'atteignait pas la bande — vrai à sa date |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | facade | 1 | - ⚪ **[Doc][À corriger en correct-course] Le brief dit encore « monté sur la façade de la tour ».** [`_bmad-output/plann | VRAI | l'ENTRÉE DE LEDGER qui signale l'écart du brief — soldée le 2026-08-30 par AC4/AC7.1 |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | facade | 1 | Décision owner du 2026-08-17 : le module sera **posé à côté** de la tour, pas monté dans la façade du Phantom 630. ⇒ Tom | VRAI | la décision owner du 2026-08-17, recopiée dans l'entrée |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | facade | 1 | `addendum.md:143` — le **ventilateur 200 mm de façade**, fait MESURÉ — sont **laissés INTACTS**, | VRAI | le SOLDE posé par AC7.1 : il dit que le ventilateur reste INTACT |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | facade | 1 | **2026-08-17 13:13:42**, dont le titre dit *« le montage en facade est PERIME »*. Et `D4`/`D9`, | VRAI | le solde : citation du titre du commit `b554a4e`, la preuve |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | vl53l0x | 1 | L'entrée de la session dn1-4 annonçait : *« à traiter quand quelqu'un touchera à l'ordre d'installation de l'ISR (dn2-1  | HISTORIQUE | texte d'ORIGINE de l'entrée `dn1-4` (« VL53L0X et BH1750 peuvent exposer une broche »), conservé selon la convention du ledger — le solde du 2026-08-19 juste dessous le réfute |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | 340..350 | 1 | - ⚪ **[DeskNode][Instrument][→ prochain passage sur `dn_ui`/`dn_console`] LES COORDONNÉES `y = 340..350` SURVIVENT DANS  | VRAI | l'ENTRÉE DE LEDGER : son CONSTAT était juste (l'avertissement enseignait un chiffre mort) |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | 340..350 | 1 | *« TOUTE COORDONNÉE TACTILE PUBLIÉE EST DÉSORMAIS PÉRIMÉE : … bande de jauge y=340..350 (dn4-1) »*, | HISTORIQUE | citation du texte de console — la console ne dit plus cela depuis AC5, mais la citation reste vraie comme trace |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | vl53l0x | 1 | - ⚪ **[DeskNode][Doc][→ prochain passage sur `affichage.md`] UNE CITATION « VL53L0X » SUBSISTE DANS UNE ANALYSE RÉTROSPE | VRAI | l'ENTRÉE DE LEDGER qui signale la citation d'`affichage.md` — soldée par AC3.4 |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | vl53l0x | 1 | *« VL53L0X, INA219 sur ce même bus »* — narration d'un arbitrage **antérieur au 2026-08-19**, | VRAI | la citation d'`affichage.md` reprise dans l'entrée |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | vl53l0x | 1 | `dn4-15` a lu les **29** occurrences de `VL53L0X` une par une. **28 sont LÉGITIMES** | VRAI | le SOLDE posé par AC7.1 : 28/29 légitimes, 1 seul défaut |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | busid-en-dur | 1 | d'alternance WSL↔COM3), le `README.md` et plusieurs stories écrivent `--busid 3-1`. | VRAI | l'ENTRÉE DE LEDGER qui CONSTATE les recettes en dur — soldée par AC3/T3. ⛔ ce n'est pas une recette, c'est son signalement |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | vl53l0x | 1 | bloqué bas après une période de fonctionnement sur **VL53L0X**, la puce sœur. | VRAI | « la puce sœur » — le mode de panne rapporté sur le VL53L0X |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | facade | 1 | **0 occurrence ajoutée** de `VL53L0X`, de `3-1` en dur, de *« façade de la tour »*. Les compteurs | VRAI | le constat de `dn4-18` : 0 occurrence ajoutée — vérifié et confirmé par le re-compte |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | vl53l0x | 1 | **0 occurrence ajoutée** de `VL53L0X`, de `3-1` en dur, de *« façade de la tour »*. Les compteurs | VRAI | idem, même ligne |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | vl53l0x | 1 | globaux sur `README.md` + `hardware/` sont **inchangés** (`VL53L0X` toujours à **17**). | HISTORIQUE | « VL53L0X toujours à 17 » — exact EN CASSE SENSIBLE au 2026-08-26 ; 18 en insensible. Corrigé juste dessous, ⛔ pas réécrit |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | vl53l0x | 1 | ⚠️ **UNE SEULE CORRECTION À CETTE ENTRÉE, ET ELLE VIENT DE LA CASSE** : *« `VL53L0X` toujours à | VRAI | la correction posée par AC7.1 : 17 en casse sensible, 18 en insensible |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | vl53l0x | 1 | `hardware/` en portent **18** — `capteurs-i2c.md:3477` écrit **`vl53l0x` en minuscules**, dans un | VRAI | la correction : `capteurs-i2c.md:3459` écrit `vl53l0x` en minuscules |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | vl53l0x | 1 | **La preuve, chiffrée** : l'epic annonçait *« 17 occurrences `VL53L0X` »* comme autant d'écarts à | VRAI | le FAIT NEUF (AC7.4) : le `grep` mesure le mot, pas le défaut |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | vl53l0x | 1 | LÉGITIMES** — des **réfutations** (*« LE 3ᵉ N'EST PAS UN VL53L0X »*), le **témoin négatif** qui a | VRAI | le fait neuf : les réfutations qu'il ne fallait pas supprimer |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | vl53l0x | 1 | (une URL nommée « VL6180X » qui rend en HTTP 200 un vrai PDF ST… du VL53L0X). **Les supprimer | VRAI | le fait neuf : le piège de source |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | facade | 1 | 13:13:42** (`b554a4e`, titre : *« le montage en facade est PERIME »*). Et les deux arguments | VRAI | le 2ᵉ fait neuf : citation du titre du commit `b554a4e` |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | busid-en-dur | 1 | (`--busid 3-1`, forme NUE, exécutable) du reste, qui sont des **faits datés** (« `usbipd list` | VRAI | le 3ᵉ fait neuf : une mention datée n'est pas une recette. ⛔ la forme est citée, pas prescrite |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | vl53l0x | 1 | > les 29 occurrences de `VL53L0X` une par une — **28 étaient légitimes** (réfutations, témoin | HISTORIQUE | 🆕 AJOUT `dn4-16` (2026-08-30) — bandeau de collision `bmad-loop-sweep` pose par `dn4-16` : il CITE la mesure de `dn4-15` (28 legitimes sur 29) pour prouver que la prose du ledger EST la connaissance. ⛔ Le supprimer detruirait l'argument qui protege le fichier de `--migrate`. |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | vl53l0x | 1 | ⇒ [dn4-16 2026-08-30] CLOSE · porteur : clos par : `dn4-15` (2026-08-30) — confirmée par le re-compte · preuve | HISTORIQUE | 🆕 AJOUT `dn4-16` (2026-08-30) — ligne de disposition `dn4-16` sur l'entree `dn4-18` : elle rappelle la correction de CASSE versee par `dn4-15` (`vl53l0x` en minuscules dans `capteurs-i2c.md`). C'est un fait DATE sur un compte, ⛔ pas une assertion sur le bus. |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | vl53l0x | 1 | ⇒ [dn4-16 2026-08-30] CONNAISSANCE · porteur : — · preuve : règle : un compte de `grep` sur un motif de dossie | HISTORIQUE | 🆕 AJOUT `dn4-16` (2026-08-30) — ligne de disposition `dn4-16` sur l'entree de METHODE de `dn4-15` : « 1 defaut sur 29 `VL53L0X` ». Le nombre est le RESULTAT de la lecture une-par-une, ⛔ pas une citation du composant. |
| cockpit | _bmad-output/implementation-artifacts/deferred-work.md | 1 | vl53l0x | 1 | inchangés), ⛔ **aucun verdict touché** ; les **5 citations `VL53L0X`** que `dn4-16` a réellement | HISTORIQUE | 🆕 AJOUT `dn4-16` (2026-08-30) — l'entree qui RACONTE l'arbitrage des trois citations precedentes en cite le motif a son tour. ⇒ la boucle se demontre elle-meme : le motif se propage par le RECIT, ⛔ pas par le defaut. |
| cockpit | _bmad-output/implementation-artifacts/sprint-status-desknode.yaml | 1 | 340..350 | 1 | #          y = 340..350 de dn4-1) ⇒ recalculer ET contrôler la formule contre un | HISTORIQUE | journal daté du tracker (décisions dn4-2/dn4-4) — vrai à sa date |
| cockpit | _bmad-output/implementation-artifacts/sprint-status-desknode.yaml | 1 | vl53l0x | 1 | #     Quatre etiquettes corrigees (« VL53L0X » -> TOF050C-VL6180X dans le brief, | VRAI | le récit des quatre étiquettes corrigées |
| cockpit | _bmad-output/implementation-artifacts/sprint-status-desknode.yaml | 1 | facade | 1 | #     sur la facade de la tour » du brief n'est PAS perimee — D4 et D9 la | HISTORIQUE | 🔴 LA RÉFUTATION DU 2026-08-20, ⛔ CONSERVÉE — elle est LEVÉE par la note du 2026-08-30 juste dessous, avec sa preuve |
| cockpit | _bmad-output/implementation-artifacts/sprint-status-desknode.yaml | 1 | facade | 1 | #     en facade est PERIME », avec verbatim owner « y aura pas de montage | VRAI | la NOTE du 2026-08-30 qui lève la réfutation : citation du titre du commit `b554a4e` |
| cockpit | _bmad-output/implementation-artifacts/sprint-status-desknode.yaml | 1 | facade | 1 | #     (le VENTILATEUR 200 mm de facade, fait mesure) restent INTACTS. | VRAI | la note : le ventilateur 200 mm reste INTACT |
| cockpit | _bmad-output/implementation-artifacts/sprint-status-desknode.yaml | 1 | vl53l0x | 1 | #     a ZERO materiel — et ⚠️ celle qui ajoute un VL53L0X COLLISIONNE a 0x29 avec | VRAI | la voie « ajouter un VL53L0X » et sa collision à `0x29` |
| cockpit | _bmad-output/implementation-artifacts/sprint-status-desknode.yaml | 1 | facade | 1 | dn2-1-bme680-bus-i2c-externe: done  # P4 — ✅ CLOSE le 2026-08-17 sur décision owner, AVEC DEUX ÉCARTS DÉCLARÉS (jamais m | VRAI | la décision owner du 2026-08-17, citée au tracker de `dn2-1` |
| cockpit | _bmad-output/implementation-artifacts/sprint-status-desknode.yaml | 1 | vl53l0x | 1 | dn2-1-bme680-bus-i2c-externe: done  # P4 — ✅ CLOSE le 2026-08-17 sur décision owner, AVEC DEUX ÉCARTS DÉCLARÉS (jamais m | VRAI | l'inventaire des 4 capteurs au 2026-08-16, avant la réfutation |
| cockpit | _bmad-output/implementation-artifacts/sprint-status-desknode.yaml | 1 | vl53l0x | 3 | dn4-2-brancher-les-trois-capteurs: done  # ✅ CLOSE EN `done` LE 2026-08-24 PAR DECISION OWNER, AVEC TROIS ECARTS DECLARE | VRAI | le récit de la réfutation par les photos du 2026-08-19 (bilan de `dn4-2`) |
| cockpit | _bmad-output/implementation-artifacts/sprint-status-desknode.yaml | 1 | 340..350 | 1 | dn4-2-brancher-les-trois-capteurs: done  # ✅ CLOSE EN `done` LE 2026-08-24 PAR DECISION OWNER, AVEC TROIS ECARTS DECLARE | HISTORIQUE | bilan daté de `dn4-2` : le motif du report `y=340..350` — vrai à sa date |
| cockpit | _bmad-output/implementation-artifacts/sprint-status-desknode.yaml | 1 | vl53l0x | 2 | dn4-3-exploiter-les-capteurs: done  # ✅ DONE le 2026-08-20 AVEC UN ECART DECLARE — AC3 est PARTIEL et la story passe don | VRAI | le relevé du registre de composants (aucun composant VL6180X, les « ToF » sont des VL53L0X) |
| cockpit | _bmad-output/implementation-artifacts/sprint-status-desknode.yaml | 1 | vl53l0x | 1 | dn4-7-le-tof-porte-t-il-vraiment: blocked  # 🔴 BLOQUÉE LE 2026-08-21 (correct-course, D14). CE QUI LA DÉBLOQUE : UN MODU | VRAI | `dn4-7` est BLOQUÉE : acheter un VL53L0X est bloqué par la collision `0x29` |
| cockpit | _bmad-output/implementation-artifacts/sprint-status-desknode.yaml | 1 | facade | 1 | dn4-8-la-tour-expose-ses-sondes-ring0: done  # ✅ CLOSE EN `done` LE 2026-08-24 AVEC TROIS ECARTS DECLARES — decision own | VRAI | `FRONT_IN` 200 mm de façade, pas de fil tachy — fait MESURÉ. ⚠️ HORS des 11 `VRAI` listés par la story |
| cockpit | _bmad-output/implementation-artifacts/sprint-status-desknode.yaml | 1 | busid-en-dur | 1 | dn4-17-l-agent-vit-sur-la-tour-et-on-reprend-la-main: done  # 2026-08-26 CLOS apres REVUE DE CODE 3 COUCHES : 4 decision | HISTORIQUE | `busid 3-5` — un FAIT MESURÉ et daté du 2026-08-26 (12 passages, 0 échec), ⛔ pas une recette à exécuter |
| cockpit | _bmad-output/implementation-artifacts/dn2-2-cpu-live-fourche-transport.md | 1 | busid-en-dur | 1 | inversement. ~~`usbipd detach --busid 3-1`~~ obligatoire pour rendre le port à l'agent Windows, et | HISTORIQUE | recette d'origine BARRÉE par T3, ⛔ pas effacée, avec son renvoi à `rendre-port.sh` et le motif (`3-1` est OCCUPÉ par un `V31GT`) |
| cockpit | _bmad-output/implementation-artifacts/dn4-6-cpu-et-gpu-a-trois-et-quatre-grandeurs.md | 1 | busid-en-dur | 1 | - **Attachement WSL↔carte** : ~~`usbipd bind/attach --busid 3-1`~~ depuis Windows. | HISTORIQUE | recette d'origine BARRÉE par T3, ⛔ pas effacée, avec son renvoi à `wsl-attach.sh`/`rendre-port.sh` |

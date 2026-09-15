#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn6-1 — LA BOM NE PEUT PAS POURRIR EN SILENCE.

======================= CE QUE CETTE GATE FAIT, ET POURQUOI =================

`docs/bom.md` publie des prix. Un prix est ce qui se perime le plus vite dans
un depot, et il se perime SANS RIEN DIRE. La page a donc une regle : ⛔ AUCUN
PRIX SANS SA DATE ET SA SOURCE. Cette gate garde cette regle, et rien d'autre.

🔴 ELLE EXISTE PARCE QUE LE PRECEDENT DU DEPOT NE SUFFISAIT PAS. `dn5-1`
   verifiait une propriete de prose par une CAPTURE UNIQUE sous `mesures/`
   (`mesures/dn5-1/T4-comptage-clone-neuf.txt`). Une capture dit ce qui etait
   vrai LE JOUR OU ON A REGARDE ; elle ne dit rien du jour ou quelqu'un ajoute
   une ligne sans date. C'est exactement ce que `dn5-6` puis `dn4-47` ont paye
   deux fois — *« les campagnes de mutants cessent d'etre des captures
   uniques »*. ⇒ ici, la propriete est REJOUEE a chaque passe.

── ⛔ CE QU'ELLE NE FAIT PAS, ET C'EST LA MOITIE DU SUJET ──────────────────

⛔ **ELLE NE JUGE AUCUN PRIX.** Elle ne sait pas si 26,77 € est vrai, ni s'il
   l'est encore. Elle ne va sur AUCUN reseau. Un prix faux mais date et source
   la laisse VERTE — et c'est voulu : la verite d'un prix se verifie en
   rouvrant la source, ⛔ pas en relisant le fichier.
⛔ Elle ne dit rien du cablage, rien du firmware, et n'ouvre aucun port.
⛔ Elle ne lit AUCUN fichier hors de `docs/bom.md`.

── CE QU'ELLE GARDE, CONTROLE PAR CONTROLE ─────────────────────────────────

  (c1) le document EXISTE, n'est pas vide, et porte au moins une TABLE DE BOM
       — une table est « de BOM » quand son en-tete nomme lui-meme
       `Date du releve` ET `Source`. ⛔ Aucune table n'est reconnue par sa
       position : une table qui ne declare pas ses colonnes n'est pas gardee,
       et c'est ECRIT plutot que tu ;
  (c2) les DEUX paliers sont nommes LITTERALEMENT, aux noms de `D19` ;
  (c3) toute ligne de BOM portant un PRIX porte une DATE de releve ;
  (c4) ... et une URL SOURCE ;
  (c5) toute ligne SANS prix porte une DECLARATION dans sa colonne Prix —
       ⛔ le silence n'est pas une declaration, et `—` non plus ;
  (c6) `VL6180X` et `INA219` sont NOMMES, et ils le sont HORS des sections de
       palier — le controle joue DANS LES DEUX SENS : absents = defaut,
       ranges dans un palier = defaut ;
  (c7) chacun porte un MOTIF d'exclusion substantiel ;
  (c8) `dn4-41` est CITEE avec son STATUT et une DATE ⛔ au lieu d'etre
       affirmee acquise ;
  (c9) la page DECLARE si elle porte des liens affilies ;
  (c10) ⛔ AUCUN JALON CHIFFRE — decision owner du 2026-09-06. Ils sont sortis
       du perimetre ; le sujet est porte par `dn6-5`.

── 🆕 2026-09-15 (`dn6-6`) — LA PAGE EST PASSEE EN ANGLAIS, SES LITTERAUX AUSSI ──

⚠️ ANNOTATION, ⛔ PAS UNE REECRITURE (NFR3). Tout ce qui precede — et les
   commentaires plus bas — nomme les litteraux de la page FRANCAISE : c'est
   ce que `docs/bom.md` ecrivait JUSQU'AU 2026-09-15 (page francaise jusqu'a
   cette date, texte d'origine dans l'historique git). Decision owner du
   2026-09-15 : la page passe en anglais, ⛔ UNE SEULE page (pas de
   `bom.en.md`). Les controles gardent le MEME invariant, sur les litteraux
   anglais, et ⛔ aucun controle n'est ajoute ni retire (24 + (z) ; 31 mutants,
   33 apres la revue du meme jour) :
     `Date du relevé` ⇒ `Survey date` · `Prix` ⇒ `Price` · `Qté` ⇒ `Qty` ·
     `Désignation` ⇒ `Item` · `Référence exacte` ⇒ `Exact reference` ·
     `Fournisseur` ⇒ `Supplier` · `Pourquoi il n'est pas…` ⇒ `Why it is not…`
     · `Adresse tentée` ⇒ `Address tried` · `Résultat` ⇒ `Result` ·
     « non relevé » ⇒ « not surveyed » · `⛔ PAS UNE TABLE DE BOM` ⇒
     `⛔ NOT A BOM TABLE` · `## Palier « X »` ⇒ `## Tier "X"` ·
     « ne porte aucun lien affilié » / « porte des liens affiliés » ⇒
     « carries no affiliate link » / « carries affiliate links ».
🔴 (c1) SE DECLARE DESORMAIS PAR `Survey date` ET `Source`, ⛔ plus par la
   seule sous-chaine `date`. `Date du relevé` CONTIENT `date` ⇒ une table de
   palier retraduite en francais continuait de se declarer table de BOM, et
   ⛔ n'etait vue que par RICOCHET (colonnes `item · price · …` introuvables).
   Avec `Survey date`, elle CESSE de se declarer et (c1c) la NOMME (`23 OK,
   1 KO`, « table a prix ni declaree ni exemptee ») ; et la page francaise
   d'origine ENTIERE sort a `1 OK, 1 KO` — AUCUNE table ne se declare. Ces deux
   derniers comptes sont PUBLIES : `mesures/dn6-6/T3`, temoins W9bis et W9.
   ⚠️ CORRIGE PAR LA REVUE 4 COUCHES DU 2026-09-15 : cette phrase citait aussi
      un `22 OK, 2 KO` de l'ANCIENNE regle comme « mesure publiee dans T3 » —
      ⛔ il n'y est pas (les trois `22 OK, 2 KO` de T3 sont des mutants de la
      gate d'affiliation). Ce compte a ete OBSERVE pendant le dev, ⛔ pas publie.
   🆕 Et le mutant 32 garde desormais cette branche : il remet `Date du relevé`
      dans une table de palier, ce que l'ancienne regle laissait VERT.
⚠️ LES PAGES QUI RESTENT EN FRANCAIS NE SONT PAS LUES ICI : cette gate ⛔ ne
   lit que `docs/bom.md`. `docs/affiliation.md` reste francaise, et c'est
   `verif_affiliation_dn65.py` qui lit ses deux langues.

Sortie : `BILAN : n OK, m KO`, rc 0 si tout passe, 1 sinon, 3 si le mutant
         demande n'a plus d'effet (🆕 2026-09-15, revue de `dn6-6` : il rendait 1,
         que `verif_campagne_dn56.py` compte « sain » — c'est le rc de dn65/dn62).
Usage  : python3 tools/verif_bom_dn61.py [--mutant <n>] [--liste-mutants]
         `--mutant` REPLANTE UNE FAUTE EN MEMOIRE et doit faire ROUGIR.
         ⛔ Aucun fichier du depot n'est modifie — la substitution vit dans
         une chaine, et le fichier n'est ouvert qu'en LECTURE.

⚠️ **UN MUTANT QUI DEBRANCHE LA GARDE NE PROUVE QUE SON EXISTENCE.** Les
   mutants d'ici replantent la faute REELLE — une date qui disparait, une URL
   qui disparait, un palier renomme, un composant hors palier range DANS un
   palier, une citation d'etat remplacee par une affirmation, un jalon qui
   revient — et la gate doit la VOIR.
"""

import argparse
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F_BOM = os.path.join(RACINE, "docs", "bom.md")
BOM_REL = "docs/bom.md"

# Les deux paliers de D19. ⛔ Ce sont des NOMS, pas des descriptions : les
# ecrire ici en dur est le sujet du controle, ⛔ pas un raccourci.
PALIERS = ("DeskNode", "DeskNode + Ambiance")

# 🔴 REVUE DU 2026-09-07 — LE REGIME ENTIER S'ARRETAIT A L'EURO A DEUX
#    DECIMALES. Une table libellee en GBP, en USD ou en euros RONDS ne portait
#    aucun « prix » aux yeux de la gate : (c1c) la sautait, et elle publiait
#    donc ses prix SANS date et SANS source, en vert. Ce n'est pas theorique —
#    `docs/bom.md` publie deja un prix en GBP (Pimoroni).
#    ⛔ La devise ne change RIEN a l'invariant : un prix se date et se source.
RE_PRIX = re.compile(r"\d+(?:[,.]\d{1,2})?\s*(?:€|EUR|£|GBP|\$|USD|CHF)")
RE_DATE = re.compile(r"20\d{2}-\d{2}-\d{2}")
RE_URL = re.compile(r"https?://\S+")
# ⚠️ « non releve » est la SEULE formule qui vaut declaration. Une gate qui
#    accepterait « ⛔ » ou « ? » laisserait passer un trou decore.
# 🆕 2026-09-15 (`dn6-6`) : la formule est desormais « not surveyed » — la
#    page est anglaise. ⛔ La forme francaise ⛔ n'est PAS gardee en
#    alternative : une ligne retraduite ne doit pas passer en silence.
RE_NON_RELEVE = re.compile(r"not\s+surveyed", re.I)
# 🔴 REVUE DU 2026-09-07 — DEUX MOTS NE SONT PAS UNE DECLARATION. Le seuil
#    est ecrit ici plutot que devine : `⛔ **non relevé**` fait 16 caracteres,
#    et c'est exactement la forme qui passait pour une declaration.
MIN_RAISON = 30
# 🆕 2026-09-15 (`dn6-6`) — LES DEUX FORMES DE LA DECLARATION, EN ANGLAIS. Elles
#    etaient « ne porte aucun lien affilié » / « porte des liens affiliés »
#    jusqu'au 2026-09-15 ; `verif_affiliation_dn65.py` ecrit les MEMES deux
#    litteraux pour la page d'achat (`NEG_BOM`/`POS_BOM`) — ⛔ les faire
#    diverger ferait lire aux deux gates deux declarations differentes.
DECL_NEG = "carries no affiliate link"
DECL_POS = "carries affiliate links"
# ⚠️ LE COMPTE DU CHEMIN NORMAL, hors le controle final qui le confronte.
#    Il se PERIME si on ajoute un controle sans le mettre a jour — et
#    c'est voulu : c'est ce qui rend le controle final FALSIFIABLE.
CONTROLES_PREVUS = 24

ok_total = [0]
ko_total = [0]

MUTANTS = {}                      # ⛔ AU NIVEAU MODULE — sinon `--liste-mutants`
# 🆕 2026-09-15 (`dn6-6`) — LES MUTANTS ANCRES SUR DU TEXTE SONT RE-ANCRES SUR
#    LA PAGE ANGLAISE : 4, 7, 8, 9, 12, 13, 19, 20, 21, 22, 23, 24, 28, 29,
#    30, 31. Chacun replante la MEME faute qu'avant ; seul son litteral change,
#    et les descriptions ci-dessous nomment le litteral anglais. ⚠️ Le mutant 8
#    retire desormais les DEUX formes de la declaration : la page porte la
#    phrase perimee ET la neuve (NFR3), en retirer une seule laissait (c9) VERT.
MUTANTS[1] = ("retire la DATE de la 1re ligne de BOM qui porte un prix "
              "(un prix nu se perime sans le dire)")
MUTANTS[2] = ("retire l'URL SOURCE de la 1re ligne de BOM qui porte un prix")
MUTANTS[3] = ("vide la colonne Prix d'une ligne qui n'en a pas "
              "(le trou MUET, ⛔ plus la declaration)")
MUTANTS[4] = ("renomme le palier « DeskNode + Ambiance » en « DeskNode Pro »")
MUTANTS[5] = ("supprime la ligne INA219 "
              "(un composant du prototype absent SANS motif)")
MUTANTS[6] = ("vide le motif d'exclusion du VL6180X "
              "(present, mais sans le POURQUOI)")
MUTANTS[7] = ("remplace la citation d'etat de `dn4-41` par une affirmation "
              "acquise (statut et date retires)")
MUTANTS[8] = ("supprime la declaration de liens affilies")
MUTANTS[9] = ("reintroduit un JALON CHIFFRE, sorti du perimetre le 2026-09-06")
MUTANTS[10] = ("deplace l'INA219 DANS une table de palier "
               "(le mensonge dans l'autre sens)")
MUTANTS[11] = ("rend le document VIDE "
               "(une gate qui ne trouve rien ⛔ ne sort pas verte)")
# 🔴 LES SIX SUIVANTS SONT NES D'UNE MESURE, ⛔ PAS D'UNE INTUITION. La 1re
#    campagne a rendu **11 mutants sur 11 vus rougir** — et le controle de la
#    RECIPROQUE a montre que **cinq controles n'etaient gardes par RIEN** :
#    la table qui se declare, le palier 1, les DEUX sens du VL6180X, et la
#    presence meme de la citation `dn4-41`. « N vus rougir » prouve
#    `mutant ⇒ rouge`, ⛔ jamais `controle ⇒ couvert`.
MUTANTS[12] = ("retire `Survey date` de l'en-tete d'une table "
               "(elle cesse de SE DECLARER table de BOM, et sort du controle)")
MUTANTS[13] = ("renomme le palier 1 \"DeskNode\" en \"DeskNode Solo\" "
               "⛔ sans toucher au palier 2")
MUTANTS[14] = ("supprime la ligne VL6180X (l'autre composant hors palier)")
MUTANTS[15] = ("deplace le VL6180X DANS une table de palier")
MUTANTS[16] = ("efface toute mention de `dn4-41` "
               "(le palier 1 redevient affirme sans source)")
MUTANTS[17] = ("retire la date de la SEULE fenetre de citation de `dn4-41` "
               "⛔ sans toucher aux autres dates du document")
# 🔴 LE JETON D'EXEMPTION EST UNE ECHAPPATOIRE — donc il se teste LUI AUSSI.
#    Sans ce mutant, n'importe qui refermerait (c1c) en posant un jeton VIDE
#    au-dessus d'une table a prix : l'exception doit rester FALSIFIABLE.
MUTANTS[18] = ("vide le MOTIF du jeton d'exemption "
               "(une exception sans motif ⛔ n'exempte RIEN)")
# ⚠️ Le mutant 12 n'en retire qu'UNE : deux tables restaient declarees, donc
#    (c1b) — « au moins une table se declare » — n'etait garde par RIEN. Il
#    faut les retirer TOUTES pour l'atteindre. Ecrit parce que la difference
#    entre « une » et « toutes » est exactement ce qui rendait le controle nu.
MUTANTS[19] = ("retire `Survey date` de TOUTES les tables "
               "(⛔ plus AUCUNE table de BOM — la gate ne trouve plus sa cible)")
# 🔴 LES SIX SUIVANTS SONT NES DE LA REVUE DU 2026-09-07. Chacun REPLANTE la
#    faute que son controle venait de rater — ⛔ aucun ne DEBRANCHE une garde.
MUTANTS[20] = ("retire le nom d'un palier de son TITRE en le laissant dans la "
               "PROSE (une mention n'est pas une section : la population de "
               "(c6) se vidait, et rien ne rougissait)")
MUTANTS[21] = ("renomme l'en-tete `Price` d'une table de BOM "
               "(la colonne ne se resout plus, la table sortait du controle)")
MUTANTS[22] = ("reduit une declaration a la SEULE formule « not surveyed » "
               "(le TROU MUET du tableau d'E/S, qui sortait VERT)")
MUTANTS[23] = ("renomme la colonne `Why` de la table hors-palier "
               "(le motif se lisait alors dans la mauvaise cellule)")
MUTANTS[24] = ("passe un composant hors-palier en MINUSCULES dans une section "
               "de palier (la casse sauvait (c6) par accident)")
MUTANTS[25] = ("fait pointer la cible sur un fichier INEXISTANT "
               "(le seul controle qu'aucun mutant n'atteignait)")
MUTANTS[26] = ("fait sortir la gate APRES (c2) sans rien declarer "
               "(le bilan retrecit, et il sortirait VERT)")
MUTANTS[27] = ("vide la QUANTITE d'une ligne a prix "
               "(une ligne incomplete ⛔ n'est pas commandable)")
MUTANTS[28] = ("retire la colonne `Qty` d'une table de palier "
               "(⛔ retirer la colonne echappait au controle du champ)")
MUTANTS[29] = ("remplace une URL tentee par un NOM D'HOTE nu "
               "(un nom de boutique ⛔ ne se re-tente pas)")
MUTANTS[30] = ("retire la DATE d'une tentative de source "
               "(une tentative sans date ⛔ ne se rejoue pas)")
MUTANTS[31] = ("renomme l'en-tete de la table des sources non atteintes "
               "(elle cesse d'etre reconnue, et le SILENCE ne vaut pas "
               "« toutes les sources ont repondu »)")
# 🆕 2026-09-15 (`dn6-6`, REVUE 4 COUCHES) — DEUX BRANCHES NEUVES QU'AUCUN MUTANT
#    NE GARDAIT (revenir a l'ancienne forme laissait le tir nu et les 31 mutants
#    identiques, mesure de la revue).
MUTANTS[32] = ("remet l'en-tete FRANCAIS `Date du relevé` dans une table de "
               "palier (l'ancienne regle `date` la laissait se declarer)")
MUTANTS[33] = ("replante « Milestone: 12.50 € » (une decimale ANGLAISE coupait "
               "la fenetre de (c10))")
_MUTANT = 0


def ctrl(ok, libelle, detail=""):
    """UNE assertion, UNE ligne. ⛔ Aucun controle muet."""
    if ok:
        ok_total[0] += 1
    else:
        ko_total[0] += 1
    print("  [%s] %-58s %s" % ("OK " if ok else "KO ", libelle, detail))
    return ok


def bilan(rc, anticipee=""):
    """TOUT CHEMIN QUI RENDRA UN VERDICT passe ici. Une gate qui sort sans
    `BILAN` est indiscernable d'une gate MORTE — et c'est precisement le
    discriminant que `verif_campagne_dn56.py` exige de chaque mutant.

    ⚠️ DEUX SORTIES NE PASSENT PAS ICI, ET C'EST ECRIT PLUTOT QUE PROMIS
       (revue du 2026-09-07 — la phrase « ⛔ TOUS LES CHEMINS DE SORTIE
       PASSENT ICI » etait FAUSSE deux fois) :
         · `--liste-mutants`, qui n'emet AUCUN controle et ne rend AUCUN
           verdict — `verif_campagne_dn56.py` ne s'en sert que pour enumerer ;
         · `sys.exit("MUTANT %d INCONNU")`, qui est une ERREUR D'APPEL.
       Aucune des deux ne peut etre prise pour un verdict vert.

    🔴 ET LE BILAN DECLARE DESORMAIS CE QU'IL N'A PAS JOUE. Mesure du
       2026-09-07 : `--mutant 11` sortait `BILAN : 0 OK, 1 KO` — UN controle
       emis sur 20 — et le contrat de la campagne (rc=1 + BILAN + un [KO ])
       le comptait « conforme ». Les 19 controles evapores n'etaient declares
       NULLE PART. ⛔ Un bilan qui retrecit sans le dire est le meme defaut
       que celui que (c1c) garde un etage plus bas."""
    # 🔴 (z) VIT ICI, ⛔ PAS EN FIN DE `main()` — 1re redaction du 2026-09-07 :
    #    posee a la fin, elle etait SAUTEE par exactement le defaut qu'elle
    #    garde (une sortie anticipee la court-circuite avec le reste). Tout
    #    verdict passe par `bilan()` : c'est le seul point qui les voit tous.
    emis = ok_total[0] + ko_total[0]
    if not anticipee and emis != CONTROLES_PREVUS:
        ctrl(False, "tout controle prevu est EMIS",
             "⛔ %d emis pour %d prevus — une gate qui joue MOINS de controles "
             "qu'annonce sort VERTE sur une population RETRECIE, et ⛔ sans le "
             "declarer" % (emis, CONTROLES_PREVUS))
        rc = 1
    print("\n" + "=" * 78)
    if anticipee:
        print("⛔ SORTIE ANTICIPEE — %d controle(s) emis sur %d prevus : %s"
              % (ok_total[0] + ko_total[0], CONTROLES_PREVUS, anticipee))
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return rc


def cellules(ligne):
    """Les cellules d'une ligne de tableau markdown, bords retires."""
    return [c.strip() for c in ligne.strip().strip("|").split("|")]


def est_separateur(ligne):
    return bool(re.fullmatch(r"\|[\s:|-]+\|", ligne.strip()))


# 🔴 CE JETON EST L'EXCEPTION **FALSIFIABLE** — voir `toutes_les_tables()`.
#    Il porte un MOTIF, et un motif vide ne vaut pas exemption.
# 🆕 2026-09-15 (`dn6-6`) : le jeton est `⛔ NOT A BOM TABLE` (page anglaise).
RE_EXEMPT = re.compile(r"<!--\s*⛔ NOT A BOM TABLE\s*:\s*(.+?)-->", re.S)


def toutes_les_tables(texte):
    """TOUTES les tables markdown du document, ⛔ pas seulement celles de BOM.

    Rend `[(entetes, [lignes], amont)]` ou `amont` est le texte des 3 lignes
    qui precedent la table — c'est la ou vit le jeton d'exemption.

    🔴 ELLE EXISTE PARCE QUE LA 1re REDACTION NE VOYAIT QUE LES TABLES DE BOM,
       ET C'ETAIT LE DEFAUT (mesure du 2026-09-06, mutant 12). Une table est
       « de BOM » quand son en-tete nomme `Date` ET `Source` — donc **retirer
       cet en-tete faisait SORTIR la table du controle**, avec ses lignes, et
       la gate restait **VERTE** : elle retrecissait sa propre population EN
       SILENCE. Le mutant 12 sortait `rc=0`, `18 OK, 0 KO`.
       ⇒ on regarde maintenant TOUTE table qui porte un PRIX, et on exige
         qu'elle soit **declaree** BOM **ou exemptee AVEC MOTIF**."""
    out = []
    lignes = texte.split("\n")
    i = 0
    while i < len(lignes) - 1:
        if (lignes[i].strip().startswith("|")
                and est_separateur(lignes[i + 1])):
            ent = cellules(lignes[i])
            corps = []
            j = i + 2
            while j < len(lignes) and lignes[j].strip().startswith("|"):
                corps.append(lignes[j])
                j += 1
            # ⚠️ SIX lignes, ⛔ pas trois : MESURE du 2026-09-06 — le jeton
            #    d'exemption tient sur 3 lignes PLUS la ligne vide qui le
            #    separe de la table, soit 4 au minimum. Une fenetre de 3 le
            #    ratait, et la gate rougissait sur une table LEGITIMEMENT
            #    exemptee. La fenetre est ECRITE ici plutot que devinee.
            out.append((ent, corps, "\n".join(lignes[max(0, i - 6):i])))
            i = j
            continue
        i += 1
    return out


def est_table_de_bom(entetes):
    """Une table SE DECLARE de BOM quand son en-tete nomme `Date` ET `Source`.
    ⛔ Aucune reconnaissance par position : la position se perime au premier
    paragraphe insere.

    🆕 2026-09-15 (`dn6-6`) : `Survey date`, ⛔ plus la sous-chaine `date`.
       `Date du relevé` et `Date of the attempt` CONTIENNENT `date` : une
       table de BOM retraduite en francais continuait de SE DECLARER. Le
       litteral est celui de la page anglaise, et une table qui ne l'ecrit
       pas sort de la declaration — (c1c) la nomme si elle porte un prix."""
    bas = [c.lower() for c in entetes]
    return (any("survey date" in c for c in bas)
            and any("source" in c for c in bas))


def tables_de_bom(texte):
    """Les tables de BOM seules — `(entetes, [lignes])`."""
    return [(e, c) for e, c, _a in toutes_les_tables(texte)
            if est_table_de_bom(e)]


def nom_nu(s):
    """Un nom DEBARRASSE de sa decoration markdown, pour comparer des NOMS.

    🔴 MESURE DU 2026-09-07 — `(c2)` MESURAIT LA DECORATION, ⛔ PAS LE NOM.
       Elle exigeait la forme A GUILLEMETS (« DeskNode »), alors que le README
       — la source de verite que `Always` designe, « exactement les noms du
       README » — les ecrit EN GRAS (`**DeskNode**`). Rendre la page comme le
       README la rend sortait `17 OK, 2 KO`, avec le message « ⛔ un synonyme
       n'est pas un nom » sur des chaines qui ⛔ ne sont PAS des synonymes.
       ⚠️ C'est le MEME defaut que `mesures/dn6-1/T3` avait deja nomme et
       corrige DANS L'INSTRUMENT DE COMPTAGE — et laisse ici, la ou il porte.
    """
    return re.sub(r"\s+", " ", re.sub(r"[*`«»\"'']", " ", s)).strip().lower()


def declaration_valable(cel_prix, cel_date, cel_src):
    """Ce qui vaut DECLARATION pour une ligne SANS prix.

    🔴 MESURE DU 2026-09-07 — `(c5)` INVERSAIT LES DEUX LIGNES DU MILIEU DU
       TABLEAU D'E/S DE LA STORY. Elle cherchait la formule « non relev » dans
       la SEULE cellule de prix, si bien que :
         · une ligne « source non atteinte » COMPLETE (URL tentee + date +
           motif d'echec) — que le tableau d'E/S declare CONFORME — sortait
           `[KO ] MUETTE(S)`, `18 OK, 1 KO`. Le message etait FAUX : cette
           ligne etait la plus bavarde de la page.
         · un TROU MUET — ni URL tentee, ni date, ni motif — portant les deux
           mots et RIEN d'autre sortait `19 OK, 0 KO`. Le tableau d'E/S en
           fait un `[KO ]`, rc=1.
       ⇒ ce qui vaut declaration, c'est le CONTENU qu'`Always` enumere :
         l'URL tentee, la date de la tentative et l'echec observe — ou, quand
         AUCUNE source n'a ete tentee, une RAISON ECRITE. ⛔ Pas une formule.
    """
    raison = cel_prix.strip()
    if len(raison) < MIN_RAISON:
        return False
    # (a) la source a ete tentee, et la tentative est TRACABLE ET DATEE
    if RE_URL.search(cel_src) and RE_DATE.search(cel_date):
        return True
    if RE_URL.search(raison) and RE_DATE.search(raison):
        return True
    # (b) aucune source n'etait tentable — la raison est ECRITE, ⛔ pas decoree
    return bool(RE_NON_RELEVE.search(raison))


def colonne(entetes, motif):
    """L'index de la colonne dont l'en-tete contient `motif`, ou None."""
    for k, c in enumerate(entetes):
        if motif in c.lower():
            return k
    return None


def sections(texte):
    """Le document decoupe par titres `## `. Rend [(titre, corps)]."""
    out = []
    titre, corps = "(preambule)", []
    for l in texte.split("\n"):
        if l.startswith("## "):
            out.append((titre, "\n".join(corps)))
            titre, corps = l[3:].strip(), []
        else:
            corps.append(l)
    out.append((titre, "\n".join(corps)))
    return out


# ═══════════════════════════ LES MUTANTS ═══════════════════════════════════
# ⛔ Chacun REPLANTE une faute dans le TEXTE. Aucun ne debranche un controle,
#    aucun ne touche le disque : la substitution vit dans une chaine.

def _ligne_avec_prix(texte):
    """La 1re ligne de BOM portant un prix — la cible des mutants 1 et 2."""
    for _ent, corps in tables_de_bom(texte):
        for l in corps:
            if RE_PRIX.search(l):
                return l
    return None


def _ligne_sans_prix(texte):
    for _ent, corps in tables_de_bom(texte):
        for l in corps:
            if not RE_PRIX.search(l) and RE_NON_RELEVE.search(l):
                return l
    return None


def muter(texte):
    if not _MUTANT:
        return texte
    if _MUTANT == 1:
        l = _ligne_avec_prix(texte)
        return texte.replace(l, RE_DATE.sub("le jour du releve", l), 1)
    if _MUTANT == 2:
        l = _ligne_avec_prix(texte)
        return texte.replace(l, RE_URL.sub("(la source habituelle)", l), 1)
    if _MUTANT == 3:
        l = _ligne_sans_prix(texte)
        return texte.replace(l, RE_NON_RELEVE.sub("", l), 1)
    if _MUTANT == 4:
        return texte.replace("DeskNode + Ambiance", "DeskNode Pro")
    if _MUTANT == 5:
        return "\n".join(l for l in texte.split("\n") if "INA219" not in l)
    if _MUTANT == 6:
        out = []
        for l in texte.split("\n"):
            if "VL6180X" in l and l.strip().startswith("|"):
                c = cellules(l)
                c[-1] = "—"
                l = "| " + " | ".join(c) + " |"
            out.append(l)
        return "\n".join(out)
    if _MUTANT == 7:
        # ⚠️ CHIRURGICAL, ⛔ PAS UN SED GLOBAL. La 1re redaction faisait
        #    `RE_DATE.sub(...)` sur TOUT le document : elle rougissait AUSSI
        #    (c3) et (c8c), c'est-a-dire qu'elle synchronisait la faute et sa
        #    fixture. Un mutant qui casse trois choses n'en prouve aucune.
        # 🆕 2026-09-15 (`dn6-6`) : ancre anglaise (« statut » ⇒ « status »).
        return texte.replace("status `in-progress`", "and it is acquired")
    if _MUTANT == 12:
        return texte.replace("Survey date", "When", 1)
    if _MUTANT == 13:
        # 🆕 2026-09-15 (`dn6-6`) : la page anglaise ecrit le nom entre
        #    guillemets DROITS (`## Tier "DeskNode"`), que `nom_nu()` retire.
        return texte.replace('"DeskNode"', '"DeskNode Solo"')
    if _MUTANT == 14:
        return "\n".join(l for l in texte.split("\n") if "VL6180X" not in l)
    if _MUTANT == 15:
        lignes = texte.split("\n")
        vl = next(l for l in lignes
                  if "VL6180X" in l and l.strip().startswith("|"))
        lignes.remove(vl)
        t = "\n".join(lignes)
        _e, corps = tables_de_bom(t)[0]
        return t.replace(corps[-1], corps[-1] + "\n" + vl, 1)
    if _MUTANT == 16:
        return texte.replace("dn4-41", "cette marche")
    if _MUTANT == 19:
        return texte.replace("Survey date", "When")
    if _MUTANT == 18:
        return RE_EXEMPT.sub("<!-- ⛔ NOT A BOM TABLE : -->", texte)
    if _MUTANT == 17:
        # La date DISPARAIT DE LA SEULE FENETRE que (c8) regarde — le reste du
        # document garde les siennes, sinon (c3) tomberait avec.
        m = re.search(r"`?dn4-41`?", texte)
        a, b = max(0, m.start() - 200), m.start() + 600
        return texte[:a] + RE_DATE.sub("recemment", texte[a:b]) + texte[b:]
    if _MUTANT == 8:
        # 🆕 2026-09-15 (`dn6-6`) : les DEUX formes — la page porte la phrase
        #    perimee (annotee, NFR3) ET la declaration neuve en dessous.
        #    N'en retirer qu'une laissait l'autre satisfaire (c9).
        return texte.replace(DECL_NEG, "is what it is") \
                    .replace(DECL_POS, "is what it is")
    if _MUTANT == 9:
        # 🔴 REVUE DU 2026-09-07 — CE MUTANT REPUBLIAIT, MOT POUR MOT, LES
        #    QUATRE CHIFFRES QUE LA DECISION OWNER DU 2026-09-06 A SORTIS DU
        #    PERIMETRE. `AC6.1.5` amendee ecrit « ⛔ aucun chiffre de jalon
        #    n'est ecrit dans la BOM NI AILLEURS PAR CETTE MARCHE » — or ce
        #    fichier EST livre par cette marche, il est joue par la CI, et
        #    (c10) ne lit que `docs/bom.md` : elle ⛔ ne pouvait pas se voir.
        #    ⇒ le mutant garde sa FORME et abandonne les chiffres de l'owner.
        # 🆕 2026-09-15 (`dn6-6`) : la charge est ecrite dans la langue de la
        #    page ; (c10) lit les mots de jalon anglais ET francais.
        return texte + "\n\n⚠️ Re-evaluation thresholds: 12 € and 34 €.\n"
    if _MUTANT == 10:
        # La ligne INA219 est DEPLACEE : retiree de sa table, reinjectee dans
        # la 1re table de BOM d'une section de palier.
        lignes = texte.split("\n")
        ina = next(l for l in lignes if "INA219" in l and l.strip().startswith("|"))
        lignes.remove(ina)
        t = "\n".join(lignes)
        _e, corps = tables_de_bom(t)[0]
        return t.replace(corps[-1], corps[-1] + "\n" + ina, 1)
    if _MUTANT == 11:
        return ""
    if _MUTANT == 20:
        # ⚠️ REECRIT LE 2026-09-07 : sa 1re version reformulait les titres SANS
        #    retirer les noms — or c'est precisement ce que le correctif rend
        #    LEGITIME (la population ne depend plus de la FORME du titre). Un
        #    mutant qui ne replante plus rien ⛔ n'est pas un mutant. Il vise
        #    donc la faute REELLE : le nom vit dans la prose, ⛔ pas en titre.
        q = PALIERS[1]
        # 🆕 2026-09-15 (`dn6-6`) : titre anglais `## Tier "…"`.
        return texte.replace('## Tier "%s"' % q, "## The sensor option", 1) \
                    .replace("---\n", '---\n\nThis is about the "%s" tier.\n' % q, 1)
    if _MUTANT == 21:
        return texte.replace("| Price |", "| Cost |", 1)
    if _MUTANT == 22:
        l = _ligne_sans_prix(texte)
        c = cellules(l)
        for k, cel in enumerate(c):
            if RE_NON_RELEVE.search(cel):
                c[k] = "not surveyed"
                break
        return texte.replace(l, "| " + " | ".join(c) + " |", 1)
    if _MUTANT == 23:
        return texte.replace("| Why it is **not** in the catalogue |",
                             "| Free comment |", 1)
    if _MUTANT == 24:
        return texte.replace("**BH1750**", "**BH1750** (see also ina219)", 1)
    if _MUTANT == 32:
        return texte.replace("| Survey date | Source |",
                             "| Date du relevé | Source |", 1)
    if _MUTANT == 33:
        return texte + "\n\nMilestone: 12.50 €\n"
    if _MUTANT == 31:
        return texte.replace("| Address tried | Date of the attempt |",
                             "| Shop | When |", 1)
    if _MUTANT == 27:
        for _e, corps in tables_de_bom(texte):
            for l in corps:
                c = cellules(l)
                k = colonne(_e, "qty")
                if RE_PRIX.search(l) and k is not None and k < len(c) \
                        and c[k].strip(" —-–*`"):
                    c[k] = " "
                    return texte.replace(l, "| " + " | ".join(c) + " |", 1)
        return texte
    if _MUTANT == 28:
        return texte.replace("| Item | Exact reference | Qty | "
                             "Supplier | Price | Survey date | Source |",
                             "| Item | Exact reference | "
                             "Supplier | Price | Survey date | Source |", 1)
    if _MUTANT == 29:
        # ⚠️ CHIRURGICAL : la MEME URL vit aussi dans la PROSE, plus haut. Une
        #    substitution « la 1re occurrence » frappait la prose et laissait
        #    la table intacte — le mutant sortait VERT sans rien prouver
        #    (mesure du 2026-09-07). On vise LA LIGNE DE TABLE.
        # 🆕 2026-09-15 (`dn6-7`) : la ligne de la CARTE porte desormais une adresse
        #    `waveshare.com` datee (le lien de la boutique Waveshare) — et elle est la
        #    1re de la page. Le mutant la frappait, ⛔ plus la table des tentatives, et
        #    sortait VERT (mesure). ⇒ la ligne visee COMMENCE par l'URL tentee.
        for l in texte.split("\n"):
            if l.strip().startswith("| `https://") and "waveshare.com" in l \
                    and RE_DATE.search(l):
                c = cellules(l)
                c[0] = "`waveshare.com` (product page)"
                return texte.replace(l, "| " + " | ".join(c) + " |", 1)
        return texte
    if _MUTANT == 30:
        return texte.replace("| `https://www.mouser.fr/c/?q=ESP32-S3-Touch-LCD-2.8B` | 2026-09-06 |",
                             "| `https://www.mouser.fr/c/?q=ESP32-S3-Touch-LCD-2.8B` | recently |", 1)
    if _MUTANT in (25, 26):
        # ⚠️ Ces deux-la ⛔ ne mutent PAS le texte : 25 deplace la CIBLE, 26
        #    replante une sortie anticipee. Le texte revient intact, et la
        #    garde du no-op les excepte NOMMEMENT.
        return texte
    raise AssertionError("mutant %d declare mais SANS CORPS" % _MUTANT)


# ═══════════════════════════ LES CONTROLES ═════════════════════════════════

def main():
    global _MUTANT
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--mutant", type=int, default=None,
                    help="REPLANTE une faute EN MEMOIRE pour prouver que le "
                         "controle correspondant sait ROUGIR")
    ap.add_argument("--liste-mutants", action="store_true",
                    help="dit ce que chaque mutant replante, et sort")
    args = ap.parse_args()
    # ⛔ Un mutant qui n'existe pas ne prouve RIEN : il doit sortir en ERREUR,
    #    ⛔ jamais en vert. Une campagne pilotee sur une liste perimee compterait
    #    sinon un mutant INEXISTANT comme « vu rougir ».
    if args.mutant is not None and args.mutant not in MUTANTS:
        sys.exit("MUTANT %d INCONNU : il n'est pas declare. ⛔ Un mutant qui "
                 "n'existe pas ne prouve RIEN — ⛔ ne pas conclure que le "
                 "controle est vert." % args.mutant)
    _MUTANT = args.mutant

    if args.liste_mutants:
        for n in sorted(MUTANTS):
            print("  %2d  %s" % (n, MUTANTS[n]))
        return 0

    print("=" * 78)
    print("dn6-1 — LA BOM NE PEUT PAS POURRIR EN SILENCE"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)
    print("cible      : %s" % BOM_REL)
    print("⛔ CETTE GATE NE JUGE AUCUN PRIX — elle garde qu'un prix porte sa "
          "date et sa source.")

    # ── (c1) le document existe, n'est pas vide, et se declare ─────────────
    print("\n── (c1) LE DOCUMENT EXISTE ET PORTE UNE TABLE DE BOM ─────────────")
    # 🔴 LE MUTANT 25 EST LE SEUL QUI DEPLACE LA CIBLE, ⛔ et il ne touche
    #    toujours PAS le disque : il ne fait que viser un chemin qui n'existe
    #    pas. Sans lui, le controle « le document existe » etait le SEUL du
    #    fichier qu'AUCUN mutant n'atteignait — et la reciproque « 19 gardes,
    #    0 NU » le comptait quand meme, parce qu'elle ne compte que les
    #    controles du chemin NORMAL.
    cible = "docs/⛔-ce-fichier-n-existe-pas.md" if _MUTANT == 25 else BOM_REL
    chemin = os.path.join(RACINE, cible)
    if not os.path.isfile(chemin):
        ctrl(False, "le document d'achat existe",
             "⛔ %s est ABSENT — ⛔ pas de trace nue, un KO nomme" % cible)
        return bilan(1, "le document d'achat est ABSENT")
    try:
        with open(chemin, encoding="utf-8") as fh:
            brut = fh.read()
    except (OSError, UnicodeDecodeError) as e:
        ctrl(False, "le document d'achat est LISIBLE",
             "⛔ %s: %s" % (type(e).__name__, str(e)[:90]))
        return bilan(1, "le document d'achat est illisible")
    # 🔴 REVUE DU 2026-09-07 — UN MUTANT QUI MEURT SORTAIT EN TRACEBACK, SANS
    #    `BILAN`. Or « pas de BILAN » est precisement le discriminant d'une
    #    gate MORTE que `verif_campagne_dn56.py` cherche : la campagne aurait
    #    donc accuse la GATE la ou la faute est dans le MUTANT (sa cible
    #    litterale a bouge, ou son corps manque). ⇒ il se rend en KO nomme.
    try:
        texte = muter(brut)
    except Exception as e:
        ctrl(False, "le mutant %d a une CIBLE et un CORPS" % _MUTANT,
             "⛔ %s: %s — ⛔ la faute est dans le MUTANT, ⛔ pas dans la gate"
             % (type(e).__name__, str(e)[:90]))
        return bilan(1, "le mutant %d n'a pas pu s'appliquer" % _MUTANT)
    # 🔴 UN MUTANT QUI NE CHANGE RIEN NE PROUVE RIEN, ET IL EST INVISIBLE AU
    #    CONTRAT DE `verif_campagne_dn56.py` (rc=1 + BILAN + un [KO ]) : le
    #    jour ou la formulation visee bouge dans `docs/bom.md`, la substitution
    #    devient un no-op et la gate sort VERTE — la campagne accuse alors la
    #    GATE, la ou la faute est dans le MUTANT. ⇒ il se declare lui-meme.
    if _MUTANT and _MUTANT not in (25, 26) and texte == brut:
        ctrl(False, "le mutant %d a bien un EFFET" % _MUTANT,
             "⛔ SANS EFFET — sa cible litterale a disparu de %s. ⛔ Ce n'est "
             "PAS un controle vert." % BOM_REL)
        # 🆕 2026-09-15 (revue de `dn6-6`) : rc=3, ⛔ plus rc=1 — rc=1 + BILAN +
        #    [KO ] est EXACTEMENT le contrat « sain » de `verif_campagne_dn56.py`,
        #    et 16 mutants venaient d'etre re-ancres : un perime passait pour sain.
        return bilan(3, "le mutant %d n'a eu aucun effet" % _MUTANT)

    if not ctrl(bool(texte.strip()), "le document n'est pas vide",
                "%d caractere(s)" % len(texte.strip())):
        return bilan(1, "le document est VIDE")
    tables = tables_de_bom(texte)
    if not ctrl(bool(tables),
                "au moins une table SE DECLARE table de BOM",
                "%d table(s) portant `Survey date` ET `Source` en en-tete" % len(tables)
                if tables else
                "⛔ AUCUNE — une table non declaree n'est gardee par RIEN"):
        return bilan(1, "AUCUNE table ne se declare table de BOM")

    # ── (c1c) 🔴 AUCUNE TABLE A PRIX NE SORT DU CONTROLE EN SILENCE ────────
    #     Ne pas ecrire ce controle laissait la gate RETRECIR sa population :
    #     une table qui perd son en-tete `Date`/`Source` cessait d'etre lue,
    #     avec toutes ses lignes, et la gate restait VERTE (mutant 12).
    print("\n── (c1c) TOUTE TABLE A PRIX EST DECLAREE, OU EXEMPTEE AVEC MOTIF ──")
    orphelines = []
    for ent, corps, amont in toutes_les_tables(texte):
        if not any(RE_PRIX.search(l) for l in corps):
            continue
        if est_table_de_bom(ent):
            continue
        ex = RE_EXEMPT.search(amont)
        if not (ex and len(ex.group(1).strip()) >= 20):
            orphelines.append(" / ".join(ent)[:52])
    ctrl(not orphelines,
         "aucune table a prix hors du controle",
         "toutes declarees ou exemptees avec motif" if not orphelines
         else "⛔ %d TABLE(S) A PRIX NI DECLAREE(S) NI EXEMPTEE(S) : %s"
              % (len(orphelines), " · ".join(orphelines)))

    # ── (c2) les deux paliers, aux noms de D19 ─────────────────────────────
    # ── (c2) les deux paliers TITRENT chacun une section ───────────────────
    # 🔴 LE CONTROLE PORTE SUR LES TITRES, ⛔ PLUS SUR LE TEXTE ENTIER, et il
    #    compare des NOMS, ⛔ pas leur decoration (voir `nom_nu`). Deux defauts
    #    en un seul geste :
    #      · `« DeskNode »` cite n'importe ou dans la prose suffisait ;
    #      · et (c6) plus bas SELECTIONNAIT SA POPULATION sur la forme du
    #        titre (`startswith("Palier «")`). Mesure du 2026-09-07 : reformuler
    #        les deux titres en `## La carte seule (palier « DeskNode »)` faisait
    #        tomber `corps_paliers` de 6 220 caracteres a **0**, et une ligne
    #        INA219 ACHETABLE posee dans la table du palier 1 sortait
    #        `19 OK, 0 KO`. La population est desormais celle de (c2) : elle ne
    #        peut plus se vider sans que (c2) rougisse D'ABORD.
    # ⚠️ LE PIEGE DE SOUS-CHAINE EST TRAITE : « DeskNode » est CONTENU dans
    #    « DeskNode + Ambiance ». Chaque titre est attribue au palier le PLUS
    #    LONG qu'il nomme, ⛔ jamais au premier trouve.
    print("\n── (c2) LES DEUX PALIERS TITRENT CHACUN UNE SECTION ──────────────")
    secs = sections(texte)
    par_palier = {}
    for t, b in secs:
        tn = nom_nu(t)
        # 🔴 LE PIEGE DE SOUS-CHAINE, MESURE SUR MOI-MEME LE 2026-09-07 : la
        #    1re redaction testait `nom_nu(q) in tn`, et le mutant 13 est
        #    sorti VERT — « DeskNode Solo » CONTIENT « DeskNode ». C'est la
        #    meme classe que `NFR6.3` qui contient `FR6.3`. ⇒ le nom doit etre
        #    DELIMITE : ⛔ ni suivi d'un mot, ⛔ ni d'un `+` qui le prolonge en
        #    un palier PLUS LONG.
        cands = [q for q in PALIERS
                 if re.search(re.escape(nom_nu(q)) + r"(?!\s*[\w+])", tn)]
        if cands:
            par_palier.setdefault(max(cands, key=len), []).append((t, b))
    for q in PALIERS:
        vus = par_palier.get(q, [])
        ctrl(len(vus) == 1, "le palier « %s » titre UNE section" % q,
             "« %s »" % vus[0][0][:44] if len(vus) == 1
             else "⛔ %d section(s) — ⛔ un synonyme n'est pas un nom, et une "
                  "population VIDE n'est pas une absence de defaut" % len(vus))
    corps_paliers = "\n".join(b for v in par_palier.values() for _t, b in v)

    # ⚠️ LE MUTANT 26 NE TOUCHE PAS AU DOCUMENT : il replante une SORTIE
    #    ANTICIPEE NON DECLAREE — la seule forme que prend, dans le code, le
    #    defaut que (z) garde. ⛔ Il ne debranche aucune garde : il fait
    #    exactement ce qu'une future refonte maladroite ferait.
    if _MUTANT == 26:
        return bilan(0)

    # ── (c3)/(c4)/(c5) chaque ligne de BOM ─────────────────────────────────
    print("\n── (c3)(c4)(c5) CHAQUE LIGNE DE BOM REND SES COMPTES ─────────────")
    # 🔴 REVUE DU 2026-09-07 — LA STORY ANNONCE QUE LA GATE « VERIFIE QUE
    #    CHAQUE LIGNE PORTE SES 7 CHAMPS ». Elle en connaissait TROIS (prix,
    #    date, source) : les mots `quantité`, `fournisseur` et `référence`
    #    n'apparaissaient nulle part dans sa logique. Mesure : une ligne
    #    `|  |  |  |  | 99,99 € | 2026-09-06 | https://… |` — ⛔ pas
    #    commandable par qui que ce soit — etait comptee « a prix, datee,
    #    sourcee », `19 OK, 0 KO`.
    # ⚠️ MOTIFS SANS LEUR PREMIERE SYLLABE ACCENTUEE : `"design" in
    #    "désignation"` est FAUX (`dé` ≠ `de`) — mesure du 2026-09-07, le
    #    controle accusait les 4 lignes de la page d'etre sans designation.
    # 🆕 2026-09-15 (`dn6-6`) : en-tetes anglais `Item | Exact reference |
    #    Qty | Supplier` — ⛔ plus de piege d'accent, mais `item` et `qty`
    #    sont COURTS : ils ne se resolvent que dans une table de BOM, dont
    #    aucun autre en-tete ne les contient (mesure du 2026-09-15).
    CHAMPS = (("item", "item"), ("reference", "reference"),
              ("qty", "quantity"), ("supplier", "supplier"))
    sans_date, sans_url, muettes, sans_colonne, creux = [], [], [], [], []
    avec_prix = sans_prix = 0
    for ent, corps in tables:
        i_prix = colonne(ent, "price")
        i_date = colonne(ent, "date")
        i_src = colonne(ent, "source")
        # 🔴 UNE COLONNE QUI NE SE RESOUT PAS SORTAIT LA TABLE DU CONTROLE EN
        #    SILENCE : `cel` retombait sur la LIGNE ENTIERE. Renommer l'en-tete
        #    `Prix` suffisait a faire retrecir la population un cran SOUS (c1c).
        if i_prix is None or i_date is None or i_src is None:
            sans_colonne.append(" / ".join(ent)[:52])
            continue
        for l in corps:
            c = cellules(l)
            cel = c[i_prix] if i_prix < len(c) else ""
            cdate = c[i_date] if i_date < len(c) else ""
            csrc = c[i_src] if i_src < len(c) else ""
            nom = c[0][:34] if c else "?"
            if RE_PRIX.search(cel):
                avec_prix += 1
                # ⛔ UNE COLONNE DECLAREE SE REMPLIT. La table hors-palier ne
                #    declare ⛔ ni `Qté` ni `Fournisseur` — et c'est JUSTE :
                #    elle ne vend rien. Ce sont les tables DE PALIER qui
                #    doivent porter les 7 colonnes, et c'est le controle
                #    separe juste en dessous qui l'exige.
                for motif_col, lib in CHAMPS:
                    k = colonne(ent, motif_col)
                    if k is None:
                        continue
                    v = c[k].strip(" —-–*`") if k < len(c) else ""
                    if not v:
                        creux.append("%s (%s)" % (nom, lib))
                # ⛔ DANS LEUR CELLULE, ⛔ plus « quelque part dans la ligne ».
                #    Mesure du 2026-09-07 : colonnes `Date du relevé` et
                #    `Source` VIDES, une date dans la designation et une URL
                #    dans la reference ⇒ `19 OK, 0 KO`, la ligne comptee
                #    « datee » et « sourcee ».
                if not RE_DATE.search(cdate):
                    sans_date.append(nom)
                if not RE_URL.search(csrc):
                    sans_url.append(nom)
            else:
                sans_prix += 1
                if not declaration_valable(cel, cdate, csrc):
                    muettes.append(nom)

    # ⛔ ET LES TABLES DE PALIER PORTENT LES 7 COLONNES : sans ce controle, en
    #    RETIRER une suffirait a echapper au controle ci-dessus.
    manquantes = []
    for ent, _co in tables_de_bom(corps_paliers):
        for motif_col, lib in CHAMPS + (("price", "price"), ("date", "date"),
                                        ("source", "source")):
            if colonne(ent, motif_col) is None:
                manquantes.append(lib)
    ctrl(not manquantes, "toute table de PALIER declare ses 7 colonnes",
         "%d table(s) de palier, 7 colonnes chacune"
         % len(tables_de_bom(corps_paliers)) if not manquantes
         else "⛔ COLONNE(S) ABSENTE(S) : %s" % " · ".join(sorted(set(manquantes))))
    ctrl(not creux, "toute ligne a prix porte ses AUTRES champs",
         "%d ligne(s) a prix, designation/reference/qte/fournisseur remplis"
         % avec_prix if not creux
         else "⛔ CHAMP(S) VIDE(S) : %s — une ligne n'est ACHETABLE que "
              "complete" % " · ".join(creux))
    ctrl(not sans_colonne, "toute table de BOM RESOUT ses 3 colonnes",
         "%d table(s), colonnes prix/date/source resolues" % len(tables)
         if not sans_colonne
         else "⛔ %d TABLE(S) SORTIE(S) DU CONTROLE : %s"
              % (len(sans_colonne), " · ".join(sans_colonne)))
    ctrl(not sans_date, "toute ligne a prix porte sa DATE de releve",
         "%d ligne(s) a prix, toutes datees" % avec_prix if not sans_date
         else "⛔ SANS DATE dans sa colonne : %s" % " · ".join(sans_date))
    ctrl(not sans_url, "toute ligne a prix porte son URL SOURCE",
         "%d ligne(s) a prix, toutes sourcees" % avec_prix if not sans_url
         else "⛔ SANS SOURCE dans sa colonne : %s" % " · ".join(sans_url))
    ctrl(not muettes, "toute ligne SANS prix se DECLARE",
         "%d ligne(s) sans prix, toutes declarees" % sans_prix if not muettes
         else "⛔ SANS DECLARATION : %s — il faut l'URL tentee, sa date et le "
              "motif, ⛔ ou une raison ecrite" % " · ".join(muettes))

    # ── (c6)/(c7) le hors-palier, dans les DEUX sens ───────────────────────
    print("\n── (c6)(c7) LE HORS-PALIER EST NOMME, ET IL EST DEHORS ───────────")
    # ⛔ INSENSIBLE A LA CASSE : `docs/bom.md` portait deja un `ina219`
    #    MINUSCULE — un nom de fichier photo — DANS la section du palier 2, et
    #    SEULE la casse sauvait ce controle. Mesure du 2026-09-07 : passer
    #    cette unique occurrence en majuscules rendait `18 OK, 1 KO`.
    haut, haut_paliers = texte.upper(), corps_paliers.upper()
    for comp in ("VL6180X", "INA219"):
        ctrl(comp in haut, "%s est NOMME dans le document" % comp,
             "present" if comp in haut
             else "⛔ ABSENT — un composant du prototype absent SANS motif "
                  "ecrit est un defaut")
        ctrl(comp not in haut_paliers,
             "%s est HORS des sections de palier" % comp,
             "dehors" if comp not in haut_paliers
             else "⛔ RANGE DANS UN PALIER — il n'entre dans aucun palier V1")
        # 🔴 LE MOTIF SE LIT PAR SON EN-TETE, ⛔ PLUS PAR `[-1]`. Mesure du
        #    2026-09-07 : la ligne INA219 realignee sur les 7 colonnes d'une
        #    table de palier rendait « 58 caractere(s) de motif » — ces 58
        #    caracteres etant son URL **Source**, sur une ligne SANS aucun
        #    motif. Le controle certifiait un motif qui n'existait pas.
        motif = ""
        for ent, corps, _a in toutes_les_tables(texte):
            # 🆕 2026-09-15 (`dn6-6`) : `Why it is **not** in the catalogue`.
            i_m = colonne(ent, "why")
            trouvee = next((l for l in corps if comp in l.upper()), None)
            if trouvee is None:
                continue
            c = cellules(trouvee)
            motif = c[i_m] if (i_m is not None and i_m < len(c)) else ""
            break
        ctrl(len(motif) >= 40, "%s porte un MOTIF d'exclusion" % comp,
             "%d caractere(s) de motif" % len(motif) if len(motif) >= 40
             else "⛔ motif VIDE OU CREUX (%d caractere(s)) — ⛔ une colonne "
                  "`Why` absente n'est pas un motif" % len(motif))

    # ── (c11) LES SOURCES NON ATTEINTES SE DECLARENT, UNE PAR UNE ──────────
    # 🔴 `AC6.1.1` exige que toute source non atteinte soit declaree AVEC SON
    #    URL, SA DATE DE TENTATIVE ET SON MOTIF. La page le faisait — avec des
    #    NOMS D'HOTE nus et une date COLLECTIVE — et ⛔ AUCUN controle ne le
    #    gardait : cette table ne porte pas de prix, donc (c1c) la saute, et
    #    elle ne se declare pas table de BOM, donc (c3)(c4)(c5) ne la voient
    #    pas. ⛔ Un nom de boutique ne se re-tente pas ; une URL, si.
    print("\n── (c11) CHAQUE SOURCE NON ATTEINTE PORTE URL + DATE + MOTIF ─────")
    t_src = [(e, co) for e, co, _a in toutes_les_tables(texte)
             if colonne(e, "tried") is not None]
    ctrl(len(t_src) == 1, "la table des sources non atteintes est LA",
         "1 table" if len(t_src) == 1
         else "⛔ %d — ⛔ le silence n'est pas « toutes les sources ont "
              "repondu »" % len(t_src))
    incompletes = []
    for ent, corps in t_src:
        # 🆕 2026-09-15 (`dn6-6`) : `Address tried | Date of the attempt |
        #    Result`. ⚠️ `tried` et ⛔ pas `attempt` : c'est la colonne
        #    ADRESSE qu'il faut resoudre, et `Date of the attempt` porterait
        #    `attempt` sans porter d'URL.
        i_a, i_d, i_r = (colonne(ent, "tried"), colonne(ent, "date"),
                         colonne(ent, "result"))
        for l in corps:
            c = cellules(l)
            def _c(i):
                return c[i] if (i is not None and i < len(c)) else ""
            if not (RE_URL.search(_c(i_a)) and RE_DATE.search(_c(i_d))
                    and len(_c(i_r).strip(" —-–*`")) >= 3):
                incompletes.append(_c(i_a)[:40] or "?")
    ctrl(not incompletes, "chaque source tentee porte URL, DATE et MOTIF",
         "%d source(s) declaree(s)" % sum(len(c) for _e, c in t_src)
         if not incompletes
         else "⛔ INCOMPLETE(S) : %s" % " · ".join(incompletes))

    # ── (c8) dn4-41 est CITEE, ⛔ pas affirmee acquise ──────────────────────
    print("\n── (c8) `dn4-41` EST CITEE AVEC SON ETAT ─────────────────────────")
    m = re.search(r"`?dn4-41`?", texte)
    fen = texte[max(0, m.start() - 200):m.start() + 600] if m else ""
    ctrl(m is not None, "la BOM cite la marche `dn4-41`",
         "citee" if m else "⛔ ABSENTE — le palier 1 serait affirme acquis")
    ctrl("in-progress" in fen, "elle cite son STATUT",
         "`in-progress`" if "in-progress" in fen
         else "⛔ le statut n'est pas cite dans la fenetre de la citation")
    d = RE_DATE.search(fen)
    ctrl(d is not None, "elle cite une DATE de relecture",
         d.group(0) if d else "⛔ aucune date — un statut sans date se perime")

    # ── (c9) la declaration d'affiliation ──────────────────────────────────
    print("\n── (c9) LA PAGE DECLARE SES LIENS AFFILIES ───────────────────────")
    # 🆕 2026-09-15 (`dn6-6`) : les deux formes ANGLAISES. ⚠️ `docs/affiliation.md`
    #    reste francaise et garde ses litteraux : c'est `verif_affiliation_dn65.py`
    #    qui confronte les deux langues, fichier par fichier.
    decl = re.search(r"(%s|%s)" % (DECL_NEG, DECL_POS), texte)
    ctrl(decl is not None, "la page DECLARE si elle porte des liens affilies",
         "« %s »" % decl.group(0) if decl
         else "⛔ AUCUNE declaration — ⛔ le silence ne vaut pas « non »")

    # ── (c10) ⛔ aucun jalon chiffre ────────────────────────────────────────
    print("\n── (c10) ⛔ AUCUN JALON CHIFFRE (decision owner 2026-09-06) ───────")
    # 🔴 REVUE DU 2026-09-07 — LE CONTROLE ETAIT ANCRE SUR UN MOT, ⛔ PAS SUR
    #    LA DECISION QU'IL GARDE. Mesure : « Seuils de réévaluation du projet :
    #    …€ » sortait VERT, et le mutant 9 etait taille sur la regex plutot que
    #    sur la decision owner du 2026-09-06. ⛔ Aucun de ces mots n'apparait
    #    dans la page (mesure du 2026-09-07), donc elargir ⛔ ne cree pas de
    #    faux positif : il ferme une porte, il n'en ouvre aucune.
    # 🆕 2026-09-15 (`dn6-6`) : la page est anglaise ⇒ les mots de jalon
    #    anglais sont AJOUTES aux francais, ⛔ ils ne les remplacent pas.
    # 🆕 2026-09-15 (revue 4 couches) — TROIS TROUS DE L'AJOUT ANGLAIS, MESURES :
    #    les mots anglais n'avaient ⛔ aucune borne (`targets?` mordait sur
    #    « targeted ») ; la fenetre `[^.\n]` s'arretait sur la DECIMALE anglaise
    #    (« Milestone: 12.50 € » sortait VERT) ; un montant en euros ecrit EN
    #    PREFIXE (`€300`) n'etait pas vu. ⇒ bornes `\b`, point admis ENTRE deux
    #    chiffres, `€`/`EUR` admis devant. Le mutant 33 replante la decimale.
    RE_JALON = (r"(?:jalons?|seuils?|objectifs?|d[ée]clencheurs?|paliers? de dons?"
                r"|\b(?:milestones?|thresholds?|targets?|goals?|triggers?"
                r"|donation tiers?)\b)")
    jalons = [w.group(0) for w in re.finditer(
                  RE_JALON + r"(?:[^.\n]|(?<=\d)\.(?=\d)){0,200}", texte, re.I)
              if re.search(r"\d[\d\s  ]*(?:€|EUR)|(?:€|EUR)\s?\d",
                           w.group(0))]
    ctrl(not jalons, "⛔ aucun jalon CHIFFRE n'est publie",
         "aucun" if not jalons
         else "⛔ %d — ils sont SORTIS du perimetre, le sujet est `dn6-5` : %s"
              % (len(jalons), jalons[0][:60]))

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : elle ne dit RIEN de la")
    print("   VERITE d'un prix ni de sa fraicheur. Un prix faux mais date et")
    print("   source la laisse VERTE. Rouvrir la source est le seul chemin.")
    return bilan(1 if ko_total[0] else 0)


if __name__ == "__main__":
    sys.exit(main())

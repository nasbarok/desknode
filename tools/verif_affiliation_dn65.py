#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn6-5 — LA DECLARATION D'AFFILIATION EST GARDEE **DANS LES DEUX SENS**.

======================= CE QUE CETTE GATE FAIT, ET POURQUOI =================

`docs/bom.md` affirme depuis `dn6-1` que la page **ne porte aucun lien
affilie**, et `docs/affiliation.md` affirme la meme chose du depot entier.
Ces deux phrases ne valent que si QUELQUE CHOSE les confronte a l'etat REEL
des adresses publiees. Cette gate est ce quelque chose.

🔴 ELLE EXISTE PARCE QUE `(c9)` DE `verif_bom_dn61.py` NE GARDE QUE LA FORME.
   Mesure : `(c9)` cherche l'une des deux phrases LITTERALES et sort verte des
   qu'elle en trouve une — elle ⛔ ne regarde AUCUNE adresse. ⇒ on pouvait
   poser un lien marque `aff_trace_key=…` dans la table de BOM et la page
   continuait de jurer qu'il n'y en avait aucun, avec `24 OK, 0 KO`.

── LES DEUX SENS, ET POURQUOI ILS SONT **DEUX** CONTROLES ─────────────────

  (c5) ⛔ AUCUNE adresse publiee ne porte de marqueur d'affiliation.
       C'est l'ETAT. Le jour ou une adresse en porte un, ce controle rougit
       EN LA NOMMANT — meme si les deux pages ont ete mises a jour, parce que
       l'affirmation « aucun » est alors devenue fausse.
  (c6) L'AFFIRMATION DES DEUX PAGES CONCORDE AVEC L'ETAT MESURE.
       C'est la CONTRADICTION. Poser un lien marque SANS toucher aux pages
       fait rougir (c5) ET (c6) ; le corriger dans les pages eteint (c6) et
       laisse (c5) rouge. ⇒ les deux fautes sont DISTINCTES et se lisent
       separement, ⛔ pas confondues dans un seul verdict.

── (c5) EST UN **ENGAGEMENT**, ⛔ PAS UNE OBSERVATION — ET C'EST VOULU ─────

Le jour ou l'owner pose un vrai lien affilie, (c5) reste ROUGE meme apres que
les deux pages ont ete correctement annotees. ⛔ CE N'EST PAS UN BUG : c'est
la ligne 2 de la matrice de `dn6-5`. Le depot s'est engage a n'en porter
aucun ; changer cet engagement est un GESTE ECRIT, ⛔ pas une derive. Le
remede est donc explicite, et il se fait DANS LE MEME COMMIT que le lien :
rouvrir cette gate, remplacer (c5) par le controle du NOUVEL engagement (par
exemple « toute adresse marquee est declaree ligne a ligne »), et l'ecrire.
⇒ (c6) et (c7), eux, restent VERTS si l'annotation est faite dans les regles —
  c'est mesure, et le temoin est dans `mesures/dn6-5/T3`.

── 🔴 LA POPULATION SE **DERIVE** DE `docs/bom.md`, ⛔ ELLE NE S'ENUMERE PAS ─

Mesure du 2026-09-07 : les cellules `Source` des tables de BOM ne citent
qu'**UN** fournisseur de record (`aliexpress.com`, 5 cellules), plus **UN**
fabricant nomme en PROSE (`waveshare.com`). Les **10** autres domaines vivent
dans la table des adresses TENTEES : ce sont des echecs, ⛔ pas des
fournisseurs.
⇒ (c3) exige une ligne de releve pour chaque domaine de la 1re population, et
  (c4) exige que la 2e soit publiee EXACTEMENT, dans les deux sens. Le jour ou
  la BOM change de fournisseur, le releve ROUGIT au lieu de pourrir en
  silence — le defaut exact que `dn5-6` puis `dn4-47` ont paye deux fois.
⚠️ **CE QUI EST TOUT DE MEME ECRIT EN DUR ICI, ET QUI DECIDE DES VERDICTS.**
   🔴 **CET INVENTAIRE EN NOMMAIT DEUX JUSQU'AU 2026-09-08. IL Y EN A NEUF** —
   et l'omission n'etait pas cosmetique : un mainteneur qui croyait deux
   vocabulaires a tenir a la main en laissait sept pourrir. La liste, dans
   l'ordre du fichier :
     1. `RE_MARQUEUR_FRANC` — les parametres d'affiliation reconnus (c5) ;
     2. `RE_MARQUEUR_AMBIGU` — ceux qui ⛔ ne mordent que sur une boutique ;
     3. `REDIRECTIONS` (**11** hotes) — une adresse posee sur un redirecteur
        ABSENT de la liste **PASSE** ;
     4. `RE_MOTIF` — les motifs d'echec acceptes (c11) ;
     5. `OFFICIELS` (**5** domaines d'autorite) — les sources de loi (c12) ;
     6. `_DEVISE` / `_JALONS` — les devises et les quatre valeurs (c15) ;
     7. `RE_PROJECTION` / `RE_EXEMPT_CONDITION` — ce qui fait une prevision,
        et ce qui l'excuse (c16) ;
     8. `REFUS_PORTEUR` — les bouchons refuses comme porteur (c14) ;
     9. `RE_DOMAINE` — les **TLD** admis, et c'est le plus tranchant : un
        domaine sur un TLD absent rend (c4) **INSOLUBLE**, ⛔ pas seulement
        aveugle. `RE_FOURNISSEUR` et `METHODES` completent la serie.
   ⛔ Ce ne sont ⛔ PAS des fournisseurs : la population des fournisseurs, elle,
   est integralement DERIVEE. Ce sont des VOCABULAIRES, ils se completent A LA
   MAIN — c'est ecrit plutot que tu.

── ⛔ CE QU'ELLE NE FAIT PAS, ET C'EST LA MOITIE DU SUJET ──────────────────

⛔ **ELLE NE JUGE AUCUN TAUX ET AUCUNE CONDITION.** Un taux faux mais date et
   source la laisse VERTE. Elle ne va sur AUCUN reseau : elle relit ce que le
   depot PUBLIE, ⛔ elle ne re-verifie pas la page du programme. Rouvrir la
   source est le seul chemin, et c'est ECRIT dans la page.
⛔ Elle ne dit RIEN de l'opportunite de s'inscrire : c'est un arbitrage
   d'owner, et la page le lui POSE au lieu de le supposer acquis.
⛔ Elle ne MODIFIE aucun fichier : tout est ouvert en LECTURE SEULE et les
   mutants vivent EN MEMOIRE.
⛔ Elle ne lit **que le clone** — ⛔ ni cockpit, ⛔ ni reseau. C'est ce qui la
   fait entrer TOUTE SEULE par le glob `tools/verif_*.py` de `run_gates.sh`,
   et c'est pour ca que `run_gates.sh` n'est ⛔ PAS touche (`NFR6.5` :
   l'hygiene du harnais est territoire `dn4`).
⛔ Elle ne touche ⛔ ni `hardware/`, ⛔ ni `firmware/`, ⛔ ni `agent/`.

── LE PIEGE DE LA DECLARATION, TRAITE : **EN GRAS**, ET LA DERNIERE ──────

Deux bornes, et chacune ferme un faux KO MESURE :

  1. La phrase d'etat existe sous ses DEUX formes dans la prose : une page qui
     EXPLIQUE la regle ecrit forcement « … porte des liens affiliés » quelque
     part. ⇒ la DECLARATION est celle qui vit **dans un passage en gras** ; le
     reste est de l'explication. Sans cette borne, expliquer la regle rendait
     la gate incoherente avec elle-meme.
  2. 🔴 CELLE QUI FAIT FOI EST LA **DERNIERE**, ⛔ pas « toutes ». Mesure du
     2026-09-07, sur le geste REEL du jour ou l'etat bascule : `NFR3` dit
     d'ANNOTER, ⛔ pas d'effacer ⇒ la phrase perimee RESTE, et la neuve
     s'ecrit EN DESSOUS. Une regle « toutes les declarations concordent »
     rendrait donc la bascule IMPOSSIBLE a ecrire correctement : elle
     exigerait d'effacer, c'est-a-dire exactement ce que `NFR3` interdit.
     ⚠️ Et (c7) reste entier : la phrase d'origine, elle, doit rester MOT
        POUR MOT — l'annoter est permis, la reecrire ⛔ pas.

── LE PORTEUR SE LIT SUR SA VALEUR, ⛔ PAS SUR LA PRESENCE DU MOT ──────────

🔴 MESURE PAYEE A `dn6-4` : chercher la sous-chaine « orteur » laissait passer
   « Porteur : à nommer ». (c14) refuse donc explicitement « a nommer »,
   « TBD », « a definir », un tiret et une case vide : un porteur A NOMMER
   n'est ⛔ PAS un porteur.

── LA GARDE DU NO-OP EST UNIVERSELLE, ⛔ PAS UNE LISTE D'EXCEPTIONS ────────

🔴 TOUTE mutation passe par un SEUL etat (`prose`, `cibles`, `regles`),
   compare AVANT/APRES. Un mutant devenu sans effet — parce que son ancre
   litterale a bouge — se declare lui-meme en `rc=3` (mutant PERIME), ⛔ pas
   en `rc=1` : `rc=1` + `BILAN` + un `[KO ]` est EXACTEMENT le contrat que
   `verif_campagne_dn56.py` appelle « sain », donc un no-op le remplirait mot
   pour mot pendant que le controle qu'il garde perdrait son seul gardien.

Sortie : `BILAN : n OK, m KO`, rc 0 si tout passe, 1 sinon, 3 si le mutant
         demande n'a plus d'effet.
Usage  : python3 tools/verif_affiliation_dn65.py [--mutant <n>] [--liste-mutants]

⚠️ **UN MUTANT QUI DEBRANCHE LA GARDE NE PROUVE QUE SON EXISTENCE** (NFR7).
   Ceux d'ici REPLANTENT la faute REELLE — un lien marque pose dans la table
   de BOM, une phrase d'etat retournee, un fournisseur neuf sans ligne de
   releve, une date effacee, un motif efface, un porteur « a nommer », un
   jalon chiffre qui revient, un revenu projete.
"""

import argparse
import ast
import copy
import os
import re
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOM = "docs/bom.md"
PAGE = "docs/affiliation.md"

# ── LES ANCRES LITTERALES ─────────────────────────────────────────────────
# Une ancre qui bouge rend son mutant PERIME (rc=3) ⇒ elle se remarque,
# ⛔ elle ne pourrit pas en silence.
A_TITRE_RELEVE = "## 3. Le relevé, fournisseur par fournisseur"
A_TITRE_TENTEES = "## 4. Les dix adresses tentées ne sont ⛔ pas des fournisseurs"
A_TITRE_LOI = "## 5. L'obligation de déclaration en France et dans l'Union"
A_TITRE_OWNER = "## 6. Ce que l'owner doit faire lui-même"
A_TITRE_BASCULE = "## 7. Le point de bascule"
A_TITRE_REMESURE = "## 8. Comment ces nombres se re-mesurent"
A_PAS_CONSEIL = "Ce n'est pas un conseil juridique"
A_SECTION_BOM = "## Liens affiliés"
A_DECL_BOM = ("**Cette page ne porte aucun lien affilié.** Les URL ci-dessus "
              "sont des adresses de recherche nues.")
A_BASCULE_BOM = "point de bascule"

# ── CE QUI SIGNE UN LIEN AFFILIE ──────────────────────────────────────────
# ⚠️ LE MARQUEUR EST CHERCHE **DANS L'ADRESSE**, ⛔ pas dans la prose : la page
#    NOMME ces parametres pour expliquer ce qu'est un lien affilie. Un
#    controle ancre sur le mot ferait rougir la page qui l'explique — un faux
#    KO sur du contenu JUSTE, et la classe de defaut la plus chere de ce depot.
RE_URL = re.compile(r"https?://[^\s`)>\"'\]]+")
# 🔴 DEUX FAMILLES DE MARQUEURS, ET LA DIFFERENCE FERME UN FAUX KO MESURE.
#
#  · FRANCS — `aff…`, `affid`, `ascsubtag`, `irclickid`, `partner_id`,
#    `linkId`, et la forme CHEMIN `/aff/1234/`. Aucun de ceux-la n'a d'usage
#    innocent : ils rougissent sur N'IMPORTE QUEL hote.
#    ⚠️ `aff[a-z_]*` et ⛔ pas `aff_[a-z_]+` : un `?aff=4231` NU est un vrai
#       lien affilie, et l'ancienne forme exigeait le `_` — elle le ratait.
#    ⚠️ `[?&#]` et ⛔ pas `[?&]` : un marqueur peut vivre dans le FRAGMENT.
#  · AMBIGUS — `tag`, `ref`, `utm_source`… Ils SIGNENT une affiliation sur une
#    boutique et ne signent RIEN ailleurs : `?ref=` sur une page de
#    documentation est une reference ordinaire.
#    🔴 SANS CETTE DISTINCTION, LE FAUX KO EST PIRE QUE LE TROU : (c5) rougit
#       sur un lien innocent, PUIS (c6) exige des deux pages qu'elles
#       affirment que le depot PORTE des liens affilies. ⇒ la gate ferait
#       PUBLIER UNE AFFIRMATION FAUSSE. Un faux KO qui se propage en mensonge
#       publie n'est pas un desagrement, c'est une faute.
#  ⇒ les AMBIGUS ne sont testes que sur un hote de BOUTIQUE, et « boutique »
#    est **DERIVE** de `docs/bom.md` (populations 1 et 2), ⛔ pas enumere.
#  ⛔ CE QUE CETTE EXCEPTION LAISSE PASSER, ECRIT PLUTOT QUE TU : un `?tag=`
#    pose sur une boutique que la BOM ne nomme PAS. Seule la famille FRANCHE
#    ou la liste des redirecteurs l'attrape alors. La contrepartie est
#    assumee : ⛔ mieux vaut ce trou NOMME qu'une gate qui fait publier faux.
# 🔴 RESSERRE LE 2026-09-08 — LE MOTIF FRANC MORDAIT SUR DU LEGITIME, ET
#    C'EST MESURE : `aff[a-z_]*=` attrapait `?affichage=`, `?affaire=`,
#    `?affluence=` ; et la forme CHEMIN `/aff…/` mordait sur N'IMPORTE QUEL
#    hote — `eur-lex.europa.eu/affiliate/guide` et
#    `legifrance.gouv.fr/aff/1234/texte` sortaient « marqueur franc ». Or un
#    faux (c5) CASCADE sur (c6), qui exigerait alors des deux pages qu'elles
#    declarent PORTER des liens affilies : une gate qui fait publier FAUX.
#    ⇒ le parametre est un vocabulaire FERME (`aff=`, `affid=`, `affiliate=`,
#      `aff_<quelque chose>=`), ⛔ plus un prefixe ouvert ;
#    ⇒ la forme CHEMIN descend chez les AMBIGUS : un segment `/aff/` est un
#      indice, ⛔ pas une preuve, et il ne mord donc plus que sur un hote de
#      boutique DERIVE de la BOM. ⛔ Contrepartie ECRITE : un chemin affilie
#      pose sur une boutique que la BOM ne nomme pas passe — c'est le trou
#      deja nomme plus bas, ⛔ pas un trou neuf.
RE_MARQUEUR_FRANC = re.compile(
    r"[?&#](?:aff|affid|affiliate|aff_[a-z0-9_]+"
    r"|ascsubtag|irclickid|partner_id|linkid)=", re.I)
RE_MARQUEUR_AMBIGU = re.compile(
    r"[?&#](?:tag|ref|referral|utm_source|utm_campaign|utm_medium"
    r"|pid|sid|clickid)="
    r"|/aff(?:iliate|iliation)?/[A-Za-z0-9_.~-]{2,}", re.I)
RE_HOTE = re.compile(r"https?://([A-Za-z0-9.-]+)")
# ⛔ `portals.` et `partner.aliexpress.com` N'Y SONT PAS, ET C'EST DELIBERE :
#    ce sont les pages PUBLIQUES du programme, que le releve CITE comme
#    sources. Les ranger en redirecteurs ferait rougir la page qui declare
#    n'avoir rien signe. Les redirecteurs reels d'AliExpress sont `s.click.`
#    et le raccourcisseur `a.aliexpress.com`.
# ⚠️ CETTE LISTE EST UN VOCABULAIRE ECRIT A LA MAIN : un redirecteur qui n'y
#    est pas PASSE. Elle se complete, ⛔ elle ne se derive pas.
REDIRECTIONS = ("s.click.aliexpress.com", "a.aliexpress.com",
                "shareasale.com", "awin1.com",
                "go.skimresources.com", "amzn.to", "shrsl.com", "tidd.ly",
                "alitems.com", "click.linksynergy.com", "go.redirectingat.com")

# ── LES DEUX FORMES DE LA DECLARATION, ACCENTS COMPRIS ────────────────────
# 🔴 CES DEUX LITTERAUX SONT CEUX DE `(c9)` DE `verif_bom_dn61.py`. Les
#    reecrire desarmerait le mutant 8 de cette gate-la — une preuve MORTE,
#    ⛔ pas un rouge. ⇒ on les REUTILISE, on ne les redefinit pas.
NEG = "ne porte aucun lien affilié"
POS = "porte des liens affiliés"
RE_DECL_GRAS = re.compile(
    r"\*\*[^*]{0,300}?(" + NEG + r"|" + POS + r")[^*]{0,300}?\*\*")

RE_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
RE_MOTIF = re.compile(r"HTTP\s*\d{3}|authentification|d[ée]lai d[ée]pass"
                      r"|sans fiche", re.I)
A_NON_ATTEINT = "NON ATTEINT"
OFFICIELS = ("legifrance.gouv.fr", "eur-lex.europa.eu", "impots.gouv.fr",
             "economie.gouv.fr", "service-public.fr")

# ⛔ LES CHIFFRES SORTIS DU PERIMETRE PAR L'OWNER LE 2026-09-06.
_E = r"[\s  ]?"
# ⚠️ `(?<![0-9])` N'EST ⛔ PAS DU CONFORT : sans lui, un prix ORDINAIRE de
#    `175 €` CONTIENT `75 €` et (c15) rougit sur du contenu JUSTE.
# 🔴 ET IL NE SUFFISAIT ⛔ PAS — MESURE PAR LA REVUE DE SUIVI DU 2026-09-08 :
#    un chiffre n'est pas colle a son SEPARATEUR. `1 250 €` rendait `250 €`,
#    `3 250 €` rendait `250 €`, `4,75 €` rendait `75 €` et `12.75 EUR`
#    rendait `75 EUR` — quatre FAUX KO sur des prix ORDINAIRES, et (c15)
#    ⛔ n'a PAS l'exemption de prix dont (c16) dispose. Le rayon venait
#    d'etre elargi de deux fichiers a TOUT le corpus : le faux KO avec.
#    ⇒ la 2e borne refuse un chiffre precede d'un separateur decimal ou de
#      milliers, lui-meme precede d'un chiffre.
_JALONS = (r"(?<![0-9])(?<![0-9][.,\s])"
           r"(?:75|250|1" + _E + r"000|5" + _E + r"000)")
# ⚠️ LES DEVISES SONT UN VOCABULAIRE, ET IL ETAIT REDUIT A L'EURO — or la
#    page publie elle-meme des montants en `US$`. Un jalon ou un revenu
#    projete ecrit en dollars passait VERT des deux cotes.
_DEVISE = r"(?:€|EUR|USD|GBP|US\$|\$|£)"
RE_JALON = re.compile(_JALONS + r"\s*" + _DEVISE
                      + r"|" + _DEVISE + r"\s*" + _JALONS)
RE_MONTANT = re.compile(r"\d+(?:[.,]\d+)?\s*(?:€|EUR|USD|GBP)"
                        r"|(?:US\$|\$|£)\s?\d+(?:[.,]\d+)?")
# 🔴 `paliers?|seuils?` SONT DANS LA LISTE, ET C'EST UNE MESURE : un jalon
#    ecrit avec un montant HORS des quatre valeurs nommees — « palier posé à
#    300 € » — passait (c15) ET (c16). Le MOT compte, ⛔ pas que le chiffre.
RE_PROJECTION = re.compile(
    r"par carte|par mois|revenus?|jalons?|objectifs?|rapporter"
    r"|paliers?|seuils?", re.I)
# ⚠️ L'EXCEPTION EST FALSIFIABLE, ET ELLE FERME UN FAUX KO MESURE :
#    `docs/bom.md` ecrit « Coût du palier, au 2026-09-06 : environ … ≈ 41 € ».
#    C'est un PRIX, ⛔ pas un jalon de revenus — et un prix est le territoire
#    de `dn6-1`, deja garde par `verif_bom_dn61.py`. ⇒ un montant introduit
#    par `coût`/`prix`/`tarif`/`versement` dans la meme clause sort de la
#    population.
#    ⛔ CE N'EST PAS UNE LISTE D'EXCLUSION : le mutant 34 replante
#    « palier posé à 300 € » SANS ce mot, et il DOIT rougir.
# 🔴 L'EXCEPTION SE LIT **DEVANT LE MONTANT**, ⛔ PAS N'IMPORTE OU DANS LA
#    FENETRE — MESURE LE 2026-09-08 : « Revenus attendus : 300 € par mois, au
#    prix actuel de la carte. » sortait VERT parce que le mot `prix` vivait
#    APRES le montant, dans une clause qui ne le qualifiait pas. Un mot qui
#    SUIT un montant ⛔ ne dit rien de ce qu'il est. ⇒ seul un mot de prix
#    ECRIT AVANT le montant, dans la meme clause, le sort de la population.
#    ⚠️ Le nom `RE_EXEMPT_PRIX` a ete abandonne le meme jour : il ne disait
#      plus ce que la regle FAIT.
# 🔴 ELARGI LE 2026-09-08, ET C'EST UN FAUX KO MESURE QUI L'A EXIGE : des
#    que les devises sont entrees dans `RE_MONTANT`, la ligne
#    « seuil de versement PayPal — US$5 » de `mesures/dn6-5/T7` a fait rougir
#    (c16). C'est une CONDITION PUBLIEE PAR LE PROGRAMME, ⛔ pas une
#    prevision — exactement ce que la page a le droit d'ecrire. ⇒ un montant
#    introduit par un mot de PRIX **ou de CONDITION DE VERSEMENT** sort de la
#    population. ⛔ `commission` n'y est PAS : un montant de commission est un
#    gain, et les quatre valeurs de jalon restent gardees par (c15), qui ⛔ n'a
#    aucune exemption.
RE_EXEMPT_CONDITION = re.compile(
    r"co[uû]ts?|prix|tarifs?|versements?|paiements?|frais", re.I)
PORTEE_PROJECTION = 200
# ⚠️ LA CLAUSE SE COUPE SUR UN POINT DE PHRASE, ⛔ PAS SUR UNE DECIMALE :
#    `re.split(r"[.\n]", …)` coupait « rapporterait environ 0.44 € par carte »
#    juste apres le `0`, et le revenu projete sortait VERT — la meme phrase
#    ecrite `0,44 €` rougissait. Le verdict ⛔ ne peut pas dependre de la
#    notation decimale.
RE_COUPE_CLAUSE = re.compile(r"(?<![0-9])\.(?![0-9])|\n")

# Un porteur A NOMMER n'est ⛔ PAS un porteur — mesure `dn6-4`.
REFUS_PORTEUR = ("a nommer", "à nommer", "tbd", "a definir", "à définir",
                 "a preciser", "à préciser", "inconnu", "?", "-", "—", "")

# Ce qui fait d'un paragraphe de prose un paragraphe de FOURNISSEUR.
RE_FOURNISSEUR = re.compile(
    r"fabricant|fournisseur|boutique|vendeur|revendeur|distributeur"
    r"|constructeur|place de march[ée]", re.I)

# 🔴 LA LECON DE CETTE MARCHE, INSTALLEE EN CONTROLE (c23) : « non atteint »
#    est une propriete de la METHODE de recuperation, ⛔ pas de l'adresse. Un
#    HTTP 403 rendu a un outil et un HTTP 200 rendu a un navigateur sont le
#    MEME jour, la MEME adresse, et deux verdicts opposes. ⇒ tout verdict dit
#    AVEC QUOI l'adresse a ete tentee, sinon il publie comme une propriete du
#    monde ce qui n'est qu'une propriete de l'outil.
METHODES = ("outil de récupération", "récupération automatisée",
            "en-tête de navigateur", "User-Agent", "navigateur")
RE_METHODE = re.compile("|".join(m.replace("-", "[- ]") for m in METHODES),
                        re.I)
A_MARQUEUR_METHODE = "méthode"
PORTEE_METHODE = 90


def methode_dite(txt):
    """La methode est-elle DITE — ⛔ pas seulement un de ses mots present ?

    🔴 CORRIGE PAR LA REVUE DE SUIVI DU 2026-09-08. (c23) cherchait ses mots
       dans la LIGNE ENTIERE pour les puces — exactement le defaut que son
       propre commentaire dit avoir mesure et ferme pour les tables. Les deux
       puces `NON ATTEINT` de la page se terminent par *« ⛔ pas re-tentée
       avec un en-tête de navigateur »* : le mot `navigateur` y parle de ce
       qui N'A PAS ete fait. Une puce SANS methode mais portant ce mot dans
       une autre clause sortait donc VERTE.
    ⇒ la methode doit etre INTRODUITE par le marqueur `méthode`, et lue dans
      la fenetre qui le suit. ⛔ Un mot qui traine ne vaut pas une methode."""
    i = txt.lower().find(A_MARQUEUR_METHODE)
    if i < 0:
        return False
    return bool(RE_METHODE.search(txt[i:i + PORTEE_METHODE]))

# ⚠️ VOCABULAIRE ECRIT A LA MAIN, ET IL DECIDE DE (c4) — nomme ici depuis
#    le 2026-09-08. Un domaine publie sur un TLD ABSENT de cette liste ⛔ ne
#    peut PAS entrer dans `nommes` : (c4) le compte alors « absent » et
#    ⛔ AUCUNE redaction correcte ne peut l'eteindre — un rouge INSOLUBLE, la
#    classe exacte que `hote()` a du fermer pour (c3). ⇒ le jour ou la BOM
#    cite une boutique sur un TLD neuf, C'EST CETTE LIGNE qu'on complete.
#    ⛔ Elle ⛔ ne se generalise PAS en `[a-z]{2,24}` : `bom.md`, `roadmap.md`
#    et tout nom de fichier en accents graves deviendraient des « domaines ».
# 🔴 ET LA CASSE : `match()` sur `AliExpress.com` rendait None. Le site
#    d'appel abaisse desormais la casse avant de confronter.
RE_DOMAINE = re.compile(
    r"^[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)*\."
    r"(?:com|fr|de|nl|eu|org|net|io|be|es|it|uk|ch|cn|co"
    r"|se|dk|at|pl|pt|cz|fi|no|ie|jp|us|ca|au"
    r"|cc|shop|store|tech|dev)$")

LARGEUR_LIBELLE = 58
MIN_CORPS = 200

ok_total = [0]
ko_total = [0]
ids_emis = []

MUTANTS = {}                      # ⛔ AU NIVEAU MODULE — sinon `--liste-mutants`
CIBLES = {}                       # ⛔ AU NIVEAU MODULE — matiere de (c20)

MUTANTS[1] = ("efface du RELEVE toutes les lignes d'un fournisseur de "
              "record ⇒ un domaine cite par la BOM sans aucun releve")
CIBLES[1] = ("c3",)
MUTANTS[2] = ("fait citer a `docs/bom.md` un fournisseur NEUF en cellule "
              "`Source` ⇒ la BOM change de fournisseur, le releve ne suit pas")
CIBLES[2] = ("c3",)
MUTANTS[3] = ("retire de la page un domaine de la table des adresses "
              "tentees ⇒ la 2e population cesse d'etre publiee en entier")
CIBLES[3] = ("c4",)
MUTANTS[4] = ("POSE UN LIEN AFFILIE dans `docs/bom.md` sans toucher aux "
              "declarations ⇒ l'etat et l'affirmation se contredisent")
# ⚠️ CIBLE DOUBLE, MESUREE : l'adresse marquee existe (c5) ET les deux pages
#    jurent encore qu'il n'y en a aucune (c6). C'est la ligne 3 de la matrice.
CIBLES[4] = ("c5", "c6")
MUTANTS[5] = ("retourne la phrase d'etat de `docs/affiliation.md` : elle "
              "affirme porter des liens la ou l'etat mesure est ZERO")
CIBLES[5] = ("c6",)
MUTANTS[6] = ("reecrit la phrase d'etat de `docs/bom.md` — la faute que "
              "`NFR3` interdit : annoter, ⛔ ne pas effacer")
# ⚠️ CIBLE DOUBLE, MESUREE : la phrase reecrite n'est plus la phrase d'origine
#    (c7) et elle cesse d'etre une declaration lisible en gras (c6).
CIBLES[6] = ("c7", "c6")
MUTANTS[7] = ("retire de `docs/bom.md` le renvoi vers la page d'affiliation")
CIBLES[7] = ("c8",)
MUTANTS[8] = ("fait pointer ce renvoi sur un fichier INEXISTANT")
CIBLES[8] = ("c8",)
MUTANTS[9] = ("efface les conditions du POINT DE BASCULE de `docs/bom.md` "
              "⇒ un titre qui l'annonce, et rien derriere")
CIBLES[9] = ("c9",)
MUTANTS[10] = ("efface la DATE d'une ligne de releve ⇒ un fait sans date, "
               "ce que `NFR4` interdit")
# ⚠️ CIBLE DOUBLE, MESUREE : la ligne visee est AUSSI une source NON ATTEINTE
#    ⇒ elle perd sa date des DEUX cotes. La cible declaree dit ce que le
#    mutant FAIT, ⛔ pas ce qu'on aimerait qu'il isole.
CIBLES[10] = ("c10", "c11")
MUTANTS[11] = ("efface l'ADRESSE d'une ligne de releve ⇒ un fait sans "
               "source re-ouvrable")
# ⚠️ CIBLE **SIMPLE**, ET C'EST UNE CORRECTION MESUREE LE 2026-09-07 : elle
#    disait `("c10", "c11")` en s'appuyant sur le fait que la ligne visee
#    etait « aussi un echec declare ». Elle ne l'est PLUS — la correction des
#    deux verdicts faux a fait passer cette ligne de l'echec a
#    `✅ **ATTEINTE**`, donc (c11) ne la regarde plus. ⛔ Une cible qui decrit
#    un etat PERIME du document est une reciproque qui ment.
CIBLES[11] = ("c10",)
MUTANTS[12] = ("efface le MOTIF d'une source NON ATTEINTE ⇒ le blanc muet "
               "que `NFR4` interdit")
CIBLES[12] = ("c11",)
MUTANTS[13] = ("efface la SOURCE OFFICIELLE d'un texte de loi cite ⇒ une "
               "obligation affirmee sans son texte")
CIBLES[13] = ("c12",)
MUTANTS[14] = ("retire la phrase « ⛔ pas un conseil juridique » ⇒ la page "
               "se met a parler comme un avocat")
CIBLES[14] = ("c13",)
MUTANTS[15] = ("remplace un porteur par « a nommer » — la faute EXACTE que "
               "`dn6-4` a payee : la sous-chaine « orteur » la laissait passer")
CIBLES[15] = ("c14",)
MUTANTS[16] = ("replante un JALON CHIFFRE dans `docs/affiliation.md`")
# ⚠️ CIBLE DOUBLE, MESUREE : la phrase replantee porte un montant ET le mot
#    `jalon` — elle est donc AUSSI une projection de revenu.
CIBLES[16] = ("c15", "c16")
MUTANTS[17] = ("replante un JALON CHIFFRE dans `docs/bom.md`")
# ⚠️ CIBLE DOUBLE **DEPUIS LA REVUE**, ET C'EST MESURE : la charge porte le mot
#    `palier`, entre depuis dans les mots de projection ⇒ elle est AUSSI un
#    revenu projete. La cible dit ce que le mutant FAIT.
CIBLES[17] = ("c15", "c16")
MUTANTS[18] = ("replante un REVENU PROJETE (« … € par carte ») — un taux "
               "affiche est une condition, une projection est une prevision")
CIBLES[18] = ("c16",)
MUTANTS[19] = ("supprime la section du POINT DE BASCULE de la page")
# ⚠️ CIBLE DOUBLE, MESUREE : ce titre est aussi la BORNE DE FIN du bloc des
#    gestes owner. Le supprimer prive (c14) de sa matiere, et il le DIT — un
#    decoupage par titres se paie ainsi, et c'est ecrit plutot que tu.
CIBLES[19] = ("c17", "c14")
MUTANTS[20] = ("retire de la prose TOUS les liens entrants vers la page "
               "⇒ la page ORPHELINE que `AC-G4` de `dn6-2` a interdite")
# ⚠️ CIBLE DOUBLE, MESUREE : le renvoi de `docs/bom.md` fait partie du lot.
CIBLES[20] = ("c18", "c8")
MUTANTS[21] = ("supprime la section « comment ces nombres se re-mesurent » "
               "⇒ des chiffres publies que personne ne sait re-tirer")
# ⚠️ CIBLE DOUBLE, MESUREE : ce titre est la BORNE DE FIN du bloc du point de
#    bascule — meme mecanique qu'au mutant 19.
CIBLES[21] = ("c19", "c17")
MUTANTS[22] = ("rend `docs/affiliation.md` VIDE (⛔ un vide n'est pas une "
               "absence de defaut)")
CIBLES[22] = ("c1",)
MUTANTS[23] = ("casse toutes les adresses de `docs/bom.md` ⇒ la population "
               "DERIVEE se vide, et une gate ⛔ ne sort pas verte sur du vide")
# ⚠️ CIBLE **TRIPLE**, MESUREE : les deux populations se derivent de la meme
#    page, donc la table des adresses tentees ne correspond plus a rien (c4) —
#    et depuis que (c3) regarde les DEUX sens, ses lignes de releve deviennent
#    toutes ORPHELINES (c3). La cible dit ce que le mutant FAIT.
CIBLES[23] = ("c2", "c4", "c3")
MUTANTS[24] = ("retire une cible de `CIBLES` ⇒ un controle garde par ZERO "
               "mutant, le risque que `dn6-1` avait paye")
CIBLES[24] = ("c20",)
MUTANTS[25] = ("declare dans `CIBLES` un controle INEXISTANT (`c99`) ⇒ une "
               "cible PERIMEE, que « N mutants, N rouges » ne verrait pas")
CIBLES[25] = ("c21",)
MUTANTS[26] = ("declare une cible pour un mutant qui N'EXISTE PAS "
               "(`CIBLES` et `MUTANTS` cessent de se correspondre)")
CIBLES[26] = ("c22",)
MUTANTS[27] = ("replante une SORTIE ANTICIPEE NON DECLAREE : le bilan "
               "retrecit, et il sortirait VERT")
CIBLES[27] = ("z",)
MUTANTS[28] = ("declare un mutant dont le CORPS LEVE ⇒ un mutant MORT, qui "
               "sortirait en Traceback SANS `BILAN` s'il n'etait pas rattrape")
CIBLES[28] = ("c0",)
MUTANTS[29] = ("fait nommer a la page un domaine tente qui n'existe PAS "
               "dans la BOM ⇒ le SENS INVERSE de (c4)")
CIBLES[29] = ("c4",)
# 🔴 LES SIX SUIVANTS SONT NES D'UNE REVUE, ET CHACUN REPLANTE UNE FAUTE QUI
#    AVAIT ETE **DEMONTREE VERTE** — ⛔ pas une faute imaginee.
MUTANTS[30] = ("verse au corpus une page suivie au NOM ACCENTUE portant une "
               "adresse marquee — celle que `git ls-files` echappait")
# ⚠️ CIBLE DOUBLE, MESUREE : l'adresse marquee existe (c5) et les deux pages
#    jurent encore qu'il n'y en a aucune (c6).
# ⚠️ CORRIGEE LE 2026-09-08 : le mutant 30 pose sa page HORS des deux pages
#    qui portent la declaration ⇒ il ne vise plus (c6) depuis que celui-ci ne
#    lit que `docs/bom.md` et `docs/affiliation.md`. La cible declaree suit
#    la MESURE, ⛔ pas l'inverse.
CIBLES[30] = ("c5",)
MUTANTS[31] = ("pose dans `docs/bom.md` une adresse de REDIRECTEUR "
               "(`s.click.`) — la branche que ⛔ AUCUN mutant ne gardait")
# ⚠️ CIBLE DOUBLE, MESUREE : l'adresse existe (c5) et les deux pages jurent
#    encore qu'il n'y en a aucune (c6).
CIBLES[31] = ("c5", "c6")
MUTANTS[32] = ("garde au releve la ligne d'un fournisseur que la BOM ne "
               "nomme PLUS ⇒ le SENS INVERSE de (c3)")
CIBLES[32] = ("c3",)
MUTANTS[33] = ("replante un JALON CHIFFRE dans un TROISIEME fichier suivi "
               "(`CHANGELOG.md`) — hors des deux pages")
CIBLES[33] = ("c15",)
MUTANTS[34] = ("replante un palier chiffre HORS des quatre valeurs nommees "
               "(« posé à 300 € »), dans `docs/roadmap.md`")
CIBLES[34] = ("c16",)
MUTANTS[35] = ("efface d'une ligne de releve la METHODE de recuperation ⇒ "
               "un verdict qui ne dit pas AVEC QUOI l'adresse a ete tentee")
CIBLES[35] = ("c23",)
# 🔴 AJOUTES PAR LA REVUE DE SUIVI DU 2026-09-08 — LA BRANCHE « MARQUEUR
#    AMBIGU SUR UNE BOUTIQUE » DE (c5) N'ETAIT VISEE PAR ⛔ AUCUN MUTANT, et
#    c'est elle qui porte TOUT l'arbitrage FRANC/AMBIGU du fichier. Demontre
#    deux fois : branche remplacee par `elif False:` ⇒ 23 OK, 0 KO et 35/35
#    mutants « sains » ; clause sous-domaine de `est_boutique()` retiree ⇒
#    idem. (c20) ⛔ ne pouvait pas le voir : il raisonne a la maille du
#    CONTROLE (`c5` restait vise par 4/30/31), ⛔ pas de la BRANCHE.
MUTANTS[36] = ("replante un marqueur AMBIGU (`?tag=`) sur un hote de "
               "boutique DERIVE de la BOM ⇒ la 3e branche de (c5)")
CIBLES[36] = ("c5", "c6")
MUTANTS[37] = ("replante un marqueur AMBIGU sur un SOUS-DOMAINE de boutique "
               "⇒ la clause `h.endswith('.' + b)` de est_boutique()")
CIBLES[37] = ("c5", "c6")

# ⚠️ LE COMPTE DU CHEMIN NORMAL, hors le controle final qui le confronte.
#    Il se PERIME si on ajoute un controle sans le mettre a jour — et c'est
#    voulu : c'est ce qui rend (z) FALSIFIABLE.
CONTROLES_PREVUS = 23

_MUTANT = 0

RE_ID_CTRL = re.compile(r"\((\w+)\)")


def ctrl(ok, libelle, detail=""):
    """UNE assertion, UNE ligne, UN identifiant. ⛔ Aucun controle muet.

    ⚠️ L'IDENTIFIANT VIT DANS LE LIBELLE, ⛔ pas dans un argument a part :
       `verif_campagne_dn56.py` lit les libelles A L'AST en prenant `args[1]`
       de chaque `ctrl(...)`. Une signature `ctrl(cid, ok, libelle)` mettrait
       le booleen en `args[1]` et retrecirait SILENCIEUSEMENT la population
       de cette gate-la. ⛔ Une gate ne retrecit pas l'instrument d'une autre.
    ⚠️ Le libelle est imprime a COLONNE FIXE (58) : c'est la cle que la
       campagne de `mesures/dn6-5/T3` relit pour attribuer chaque signalement
       a son controle."""
    assert len(libelle) <= LARGEUR_LIBELLE, (
        "libelle de %d colonnes (max %d) : %r — il deborderait la cle a "
        "colonne fixe" % (len(libelle), LARGEUR_LIBELLE, libelle))
    m = RE_ID_CTRL.match(libelle)
    ids_emis.append(m.group(1) if m else "?")
    if ok:
        ok_total[0] += 1
    else:
        ko_total[0] += 1
    print("  [%s] %-58s %s" % ("OK " if ok else "KO ", libelle, detail))
    return ok


def bilan(rc, anticipee=""):
    """TOUT CHEMIN QUI REND UN VERDICT passe ici. Une gate qui sort sans
    `BILAN` est indiscernable d'une gate MORTE — et c'est precisement le
    discriminant que `verif_campagne_dn56.py` exige de chaque mutant.

    ⚠️ DEUX SORTIES NE PASSENT PAS ICI, ET C'EST ECRIT PLUTOT QUE PROMIS :
       · `--liste-mutants`, qui n'emet AUCUN controle et ne rend AUCUN
         verdict — la campagne ne s'en sert que pour enumerer ;
       · `sys.exit("MUTANT %d INCONNU")`, qui est une ERREUR D'APPEL."""
    emis = ok_total[0] + ko_total[0]
    if not anticipee and emis != CONTROLES_PREVUS:
        ctrl(False, "(z) tout controle prevu est EMIS",
             "⛔ %d emis pour %d prevus — une gate qui joue MOINS de controles "
             "qu'annonce sort VERTE sur une population RETRECIE, ⛔ sans le "
             "declarer" % (emis, CONTROLES_PREVUS))
        rc = 1
    print("\n" + "=" * 78)
    if anticipee:
        print("⛔ SORTIE ANTICIPEE — %d controle(s) emis sur %d prevus : %s"
              % (ok_total[0] + ko_total[0], CONTROLES_PREVUS, anticipee))
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return rc


# ═══════════════════════ LIRE LE DEPOT ═════════════════════════════════════

def suivis():
    """Les fichiers TRACES, par `git ls-files`. ⛔ Pas un parcours du disque :
    un repertoire ignore n'est pas du depot. Rend `None` si git refuse.

    🔴 `core.quotePath=false` ET `-z` NE SONT ⛔ PAS DU CONFORT — ET LE DEPOT
       EST FRANCOPHONE. Par defaut `git ls-files` ECHAPPE tout chemin non
       ASCII et l'entoure de guillemets (`"docs/note-accentu\\303\\251e.md"`).
       Ce jeton ⛔ ne finit PAS par `.md` ⇒ la page quitte le corpus EN
       SILENCE, et (c5) continue de jurer que **toutes** les pages suivies ont
       ete relues alors qu'il en manque une — celle qui, justement, pourrait
       porter l'adresse marquee. C'est le defaut EXACT que la revue de `dn6-4`
       a corrige dans `verif_boitier_dn64.py`, et il se reproduisait ici mot
       pour mot.
       ⇒ `-z` separe au NUL, ce qui rend aussi un nom contenant un retour a la
         ligne — que `splitlines()` aurait coupe en deux."""
    # ⚠️ `encoding="utf-8"` EST OBLIGATOIRE : sans lui, `text=True` decode
    #    avec la locale, et sous `LC_ALL=C` un chemin accentue leve
    #    `UnicodeDecodeError` — un Traceback SANS `BILAN`, c'est-a-dire la
    #    signature d'une gate MORTE. Le depot est francophone.
    try:
        r = subprocess.run(["git", "-c", "core.quotePath=false",
                            "ls-files", "-z"], cwd=RACINE,
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return None
    if r.returncode != 0:
        return None
    return sorted(x for x in r.stdout.split("\0") if x.strip())


def cellules(ligne):
    """Les cases d'une ligne de table markdown."""
    t = ligne.strip()
    if not t.startswith("|"):
        return None
    return [c.strip() for c in t.strip("|").split("|")]


def tables(texte):
    """`[(entete, corps)]` — les tables markdown, reconnues par leur
    SEPARATEUR et par l'EGALITE des largeurs. ⛔ Aucun numero de ligne."""
    lignes = texte.split("\n")
    out, i = [], 0
    while i < len(lignes) - 1:
        h, s = cellules(lignes[i]), cellules(lignes[i + 1])
        if (h and s and len(h) == len(s)
                and all(re.fullmatch(r":?-{3,}:?", c) for c in s)):
            corps, j = [], i + 2
            while j < len(lignes):
                c = cellules(lignes[j])
                if not c or len(c) != len(h):
                    break
                corps.append(c)
                j += 1
            out.append((h, corps))
            i = j
        else:
            i += 1
    return out


def sections(texte, niveau="## "):
    """`[(titre, corps)]` — decoupe par titre, ⛔ pas par numero de ligne."""
    out, titre, corps = [], None, []
    for l in texte.split("\n"):
        if l.startswith(niveau) and not l.startswith(niveau + "#"):
            if titre is not None:
                out.append((titre, "\n".join(corps)))
            titre, corps = l.rstrip(), []
        elif titre is not None:
            corps.append(l)
    if titre is not None:
        out.append((titre, "\n".join(corps)))
    return out


def corps_de(texte, titre):
    """Le corps de la section dont le titre COMMENCE par `titre`."""
    for t, b in sections(texte):
        if t.startswith(titre):
            return b
    return None


def hote(url):
    """L'hote d'une adresse, NORMALISE.

    ⚠️ `.lower()` et `.rstrip(".")` ferment deux (c3) ROUGES PERMANENTS : un
       hote ecrit `AliExpress.com` et une adresse nue qui termine une phrase
       (`… sur https://www.aliexpress.com.`) ne s'apparient a AUCUNE ligne de
       releve, et le KO serait INSOLUBLE — le domaine DERIVE et le domaine
       PUBLIE ne pourraient jamais coincider."""
    m = RE_HOTE.search(url)
    if not m:
        return ""
    d = m.group(1).lower().rstrip(".")
    return d[4:] if d.startswith("www.") else d


def dom_nu(s):
    """Un domaine ECRIT dans la page, normalise comme `hote()`."""
    d = re.sub(r"[`*_]", "", s or "").strip().lower().rstrip(".")
    return d[4:] if d.startswith("www.") else d


def est_boutique(h, boutiques):
    """Un hote de BOUTIQUE — **derive** de `docs/bom.md`, ⛔ pas enumere.
    Un sous-domaine d'un domaine derive en fait partie."""
    return any(h == b or h.endswith("." + b) for b in boutiques)


def cible_lien(depuis, href):
    """La cible d'un lien markdown, NORMALISEE en chemin du depot.

    ⚠️ ⛔ PAS une comparaison a deux litteraux : `](affiliation.md)`,
       `](../docs/affiliation.md)` et `](affiliation.md#le-point-de-bascule)`
       designent LA MEME page. Comparer des chaines faisait declarer
       « aucun renvoi » / « page orpheline » sur un lien qui MARCHE."""
    chemin = href.split("#")[0].split("?")[0].strip()
    if not chemin or chemin.startswith(("http://", "https://", "mailto:")):
        return None
    return os.path.normpath(os.path.join(os.path.dirname(depuis), chemin))


def unites(texte):
    """Les UNITES DE DECLARATION : une ligne structurelle + ses continuations.

    🔴 UN VERDICT REPLIE SUR DEUX LIGNES PHYSIQUES RESTE UN SEUL VERDICT.
       Lu ligne a ligne, un verdict d'echec sur la 1re et son motif sur la 2e
       sortait « ECHEC MUET » — un KO sur une declaration PARFAITEMENT
       complete, que la seule largeur de la fenetre d'edition decidait."""
    out = []
    for brut in texte.split("\n"):
        s = re.sub(r"^\s*>\s?", "", brut).strip()
        if not s:
            out.append(None)
            continue
        debut = (s.startswith(("|", "- ", "* ", "#", "```"))
                 or re.match(r"^\d+\. ", s) is not None)
        if debut or not out or out[-1] is None:
            out.append(s)
        else:
            out[-1] += " " + s
    return [u for u in out if u]


def populations(bom):
    """LES DEUX POPULATIONS, DERIVEES DE `docs/bom.md`.

    🔴 ⛔ AUCUNE ENUMERATION : la 1re sort des cellules de la colonne dont
       l'entete commence par `Source`, PLUS les domaines nommes en PROSE hors
       de toute table (c'est la que vit le fabricant non relevable) ; la 2e
       sort de la colonne dont l'entete contient `Adresse`."""
    pop1, pop2 = set(), set()
    lignes = bom.split("\n")
    en_table = set()
    for h, corps in tables(bom):
        i_src = next((k for k, n in enumerate(h)
                      if n.lower().startswith("source")), None)
        i_ten = next((k for k, n in enumerate(h)
                      if "adresse" in n.lower()), None)
        for c in corps:
            if i_src is not None:
                pop1.update(hote(u) for u in RE_URL.findall(c[i_src]))
            if i_ten is not None:
                pop2.update(hote(u) for u in RE_URL.findall(c[i_ten]))
    for h, corps in tables(bom):
        en_table.add(" | ".join(h))
        for c in corps:
            en_table.add(" | ".join(c))
    # 🔴 LE BALAYAGE DE PROSE EST **CONTEXTUEL**, ⛔ PAS AVEUGLE — ET C'EST UN
    #    FAUX KO MESURE. Pris a toute la prose, il rangeait en « fournisseur »
    #    la moindre adresse citee dans la page : ajouter un lien vers une fiche
    #    technique ou une norme forcait (c3) au ROUGE et exigeait une ligne de
    #    releve d'affiliation pour un editeur de datasheet. ⇒ seul un
    #    PARAGRAPHE qui parle de fournisseur livre ses adresses. C'est la
    #    forme exacte du seul cas reel : le fabricant non relevable, nomme en
    #    prose a cote du mot `fabricant`.
    #    ⛔ CE QUE CA LAISSE PASSER, ECRIT : un fournisseur nomme en prose SANS
    #    aucun de ces mots sort de la population. Il rentre des qu'une cellule
    #    `Source` le cite — et c'est la colonne qui fait foi.
    hors_table = []
    for l in lignes:
        cl = cellules(l)
        if cl is not None and " | ".join(cl) in en_table:
            hors_table.append("")
        else:
            hors_table.append(l)
    for para in re.split(r"\n\s*\n", "\n".join(hors_table)):
        if RE_FOURNISSEUR.search(para):
            pop1.update(hote(u) for u in RE_URL.findall(para))
    return {d for d in pop1 if d}, {d for d in pop2 if d}


def declarations(texte):
    """Les phrases d'etat, LUES EN GRAS — ⛔ pas dans la prose explicative."""
    return [m.group(1) for m in RE_DECL_GRAS.finditer(texte)]


def declaration_en_vigueur(texte):
    """LA DERNIERE declaration en gras — celle qui fait foi.

    🔴 ⛔ PAS « toutes » : `NFR3` fait ANNOTER plutot qu'effacer, donc le jour
       ou l'etat bascule la phrase perimee RESTE au-dessus de la neuve. Exiger
       que TOUTES concordent rendrait la bascule inecrivable autrement qu'en
       effacant — le contraire de la regle qu'on pretend garder."""
    d = declarations(texte)
    return d[-1] if d else None


def nu(cellule):
    """Une case de table, debarrassee de sa decoration markdown."""
    return re.sub(r"[`*_]", "", cellule).strip()


# ═══════════════════════ LES MUTANTS ═══════════════════════════════════════

def muter(etat):
    """REPLANTE une faute DANS L'ETAT — ⛔ jamais dans un fichier du depot.

    🔴 TOUTE mutation passe par cet unique etat, et `main()` compare l'etat
       AVANT/APRES : la garde du no-op est donc UNIVERSELLE, ⛔ pas une liste
       d'exceptions a tenir a jour.
    ⚠️ **CETTE PHRASE A ETE FAUSSE JUSQU'AU 2026-09-08, ET C'EST MESURE** : la
       comparaison AVANT/APRES ⛔ n'est atteinte que si le corps du mutant
       REND. Cinq corps LEVAIENT quand leur ancre avait disparu, et le `try`
       de `main()` les rendait en `rc=1` + `[KO ]` — le contrat « sain » de la
       campagne. ⇒ tout corps qui depaquete un `split`, lit un corps de
       section ou indexe un fichier VERIFIE son ancre d'abord et rend `e`
       INCHANGE. ⛔ La garde ne se decrete pas, elle s'atteint."""
    e = copy.deepcopy(etat)
    p, r = e["prose"], e["regles"]

    # 🔴 CORRIGE PAR LA REVUE DE SUIVI DU 2026-09-08 — LA GARDE DU NO-OP
    #    N'ETAIT ⛔ PAS UNIVERSELLE, ET C'EST MESURE : cinq mutants (1, 3, 9,
    #    33, 34) ⛔ ne rendaient PAS `rc=3` quand leur ancre avait bouge — ils
    #    LEVAIENT (`ValueError` sur un `split` depaquete, `TypeError` sur un
    #    corps de section absent, `KeyError` sur un fichier sorti du corpus).
    #    Le `try` de `main()` les rattrapait et les rendait en `rc=1` +
    #    `BILAN` + `[KO ]` — c'est-a-dire, MOT POUR MOT, le contrat que
    #    `verif_campagne_dn56.py:319` appelle « sain ». Un mutant PERIME
    #    passait donc pour un gardien vivant. ⇒ chacun de ces cinq VERIFIE son
    #    ancre et rend l'etat INCHANGE si elle a disparu, ce qui le fait
    #    tomber dans la garde du no-op. ⛔ Le mutant 28 continue de lever
    #    EXPRES : lui est le temoin du « mutant declare qui MEURT ».
    if _MUTANT == 1:
        if A_TITRE_RELEVE not in p[PAGE] or A_TITRE_TENTEES not in p[PAGE]:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        avant, apres = p[PAGE].split(A_TITRE_RELEVE, 1)
        bloc, suite = apres.split(A_TITRE_TENTEES, 1)
        p[PAGE] = (avant + A_TITRE_RELEVE
                   + bloc.replace("`waveshare.com`", "`ce fabricant`")
                   + A_TITRE_TENTEES + suite)
    elif _MUTANT == 2:
        p[BOM] = p[BOM].replace(
            "https://www.aliexpress.com/w/wholesale-INA219-CJMCU.html",
            "https://www.reichelt.de/w/ina219-cjmcu")
    elif _MUTANT == 3:
        if A_TITRE_TENTEES not in p[PAGE] or A_TITRE_LOI not in p[PAGE]:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        avant, apres = p[PAGE].split(A_TITRE_TENTEES, 1)
        bloc, suite = apres.split(A_TITRE_LOI, 1)
        p[PAGE] = (avant + A_TITRE_TENTEES
                   + bloc.replace("`thepihut.com`", "une dixième boutique")
                   + A_TITRE_LOI + suite)
    elif _MUTANT == 4:
        # 🔴 LA FAUTE REELLE : une adresse de la table de BOM devient un lien
        #    marque, et ⛔ PERSONNE ne revient corriger les deux phrases.
        p[BOM] = p[BOM].replace(
            "https://www.aliexpress.com/w/wholesale-BH1750-GY-302.html",
            "https://www.aliexpress.com/w/wholesale-BH1750-GY-302.html"
            "?aff_trace_key=dn65", 1)
    elif _MUTANT == 5:
        p[PAGE] = p[PAGE].replace("**Ce dépôt " + NEG + ".**",
                                  "**Ce dépôt " + POS + ".**")
    elif _MUTANT == 6:
        p[BOM] = p[BOM].replace(A_DECL_BOM, "Rien à signaler de ce côté.")
    elif _MUTANT == 7:
        p[BOM] = p[BOM].replace("](affiliation.md)", "](le sujet)")
    elif _MUTANT == 8:
        p[BOM] = p[BOM].replace("](affiliation.md)",
                                "](affiliation-inexistante.md)")
    elif _MUTANT == 9:
        bloc = corps_de(p[BOM], A_SECTION_BOM)
        if not bloc:
            return e                      # section disparue ⇒ NO-OP ⇒ rc=3
        garde = re.sub(r"(?m)^\d+\. .*(?:\n   .*)*\n", "", bloc)
        p[BOM] = p[BOM].replace(bloc, garde)
    elif _MUTANT == 10:
        p[PAGE] = p[PAGE].replace(
            "`https://sale.aliexpress.com/__pc/uTHnW6wRZg.htm` | 2026-09-07 |",
            "`https://sale.aliexpress.com/__pc/uTHnW6wRZg.htm` | bientôt |")
    elif _MUTANT == 11:
        p[PAGE] = p[PAGE].replace(
            "| `https://www.waveshare.com/` | 2026-09-07 |",
            "| leur boutique | 2026-09-07 |")
    elif _MUTANT == 12:
        p[PAGE] = p[PAGE].replace(
            "— HTTP 404 : l'accord n'est pas à cette adresse.", "—")
    elif _MUTANT == 13:
        p[PAGE] = p[PAGE].replace(
            "`https://www.legifrance.gouv.fr/codes/article_lc/"
            "LEGIARTI000044563107` | 2026-09-07 |", "— | 2026-09-07 |")
    elif _MUTANT == 14:
        p[PAGE] = p[PAGE].replace(A_PAS_CONSEIL, "Voici ce qu'il faut faire")
    elif _MUTANT == 15:
        # 🔴 LA FAUTE EXACTE DE `dn6-4` : le mot « Porteur » est TOUJOURS la.
        p[PAGE] = p[PAGE].replace("| **owner** |", "| à nommer |", 1)
    elif _MUTANT == 16:
        p[PAGE] += ("\n⚠️ Le premier jalon est atteint à 5 000 € de "
                    "commissions cumulées.\n")
    elif _MUTANT == 17:
        p[BOM] += ("\n⚠️ Le premier palier chiffré est posé à 1 000 € de "
                   "commissions.\n")
    elif _MUTANT == 18:
        p[PAGE] += ("\n⇒ à ce taux, ça rapporterait environ 0,44 € par carte "
                    "vendue par ce dépôt\n")
    elif _MUTANT == 19:
        p[PAGE] = p[PAGE].replace(A_TITRE_BASCULE, "## 7. Quelques remarques")
    elif _MUTANT == 20:
        for f in list(p):
            if f != PAGE:
                p[f] = p[f].replace("](affiliation.md)", "](le sujet)")
                p[f] = p[f].replace("](docs/affiliation.md)", "](le sujet)")
    elif _MUTANT == 21:
        p[PAGE] = p[PAGE].replace(A_TITRE_REMESURE, "## 8. Pour finir")
    elif _MUTANT == 22:
        p[PAGE] = ""
    elif _MUTANT == 23:
        p[BOM] = p[BOM].replace("https://", "hxxps://")
    elif _MUTANT == 24:
        # ⚠️ LA VICTIME EST **DERIVEE**, ⛔ pas codee en dur : viser un mutant
        #    par son numero cesse de marcher le jour ou son controle gagne un
        #    SECOND gardien.
        compte = {}
        for _n, _v in e["cibles"].items():
            for _c in _v:
                compte[_c] = compte.get(_c, 0) + 1
        for _n, _v in sorted(e["cibles"].items()):
            if any(compte[_c] == 1 for _c in _v):
                e["cibles"][_n] = ()
                break
    elif _MUTANT == 25:
        e["cibles"][25] = tuple(e["cibles"][25]) + ("c99",)
    elif _MUTANT == 26:
        e["cibles"][99] = ("c9",)      # une cible pour un mutant INEXISTANT
    elif _MUTANT == 27:
        r["sortie_anticipee"] = True
    elif _MUTANT == 28:
        # 🔴 IL LEVE EXPRES : c'est la faute « un mutant declare qui MEURT ».
        raise AssertionError("mutant 28 : corps volontairement LEVANT")
    elif _MUTANT == 29:
        p[PAGE] = p[PAGE].replace("et `thepihut.com`.",
                                  "`thepihut.com` et `reichelt.de`.")
    elif _MUTANT == 30:
        # 🔴 LE NOM EST ACCENTUE EXPRES : sans `core.quotePath=false` + `-z`,
        #    une page comme celle-ci ⛔ n'entrait JAMAIS dans le corpus.
        # ⚠️ CE QU'IL PROUVE, ET CE QU'IL NE PROUVE ⛔ PAS — ECRIT LE
        #    2026-09-08 : il ecrit DANS `prose`, c'est-a-dire EN AVAL de
        #    `suivis()`. Il prouve que (c5) relit tout le corpus ; il ⛔ ne
        #    prouve PAS que `git ls-files` le RENDE. Mesure : retirer `-z` et
        #    `core.quotePath=false` de `suivis()` laisse la gate a 23 OK et
        #    les 37 mutants « sains ». La garde est donc REELLE mais
        #    ⛔ NON EXERCEE — et elle le restera tant que le depot ne suivra
        #    AUCUN chemin non-ASCII (mesure du 2026-09-08 : **0** sur 685).
        #    ⇒ ce qui l'exercerait est un FICHIER SUIVI au nom accentue,
        #      ⛔ pas un mutant : au ledger, ⛔ pas rapiece ici.
        p["docs/relevé-fournisseurs-accentué.md"] = (
            "# Relevé accentué\n\nVoir "
            "https://www.aliexpress.com/item/1005.html?aff_trace_key=REPLANTE\n")
    elif _MUTANT == 31:
        # ⚠️ POSEE EN PROSE, HORS d'un paragraphe de fournisseur : le mutant
        #    vise la branche REDIRECTEUR de (c5), ⛔ pas la derivation.
        # ⚠️ LE CODE EST FABRIQUE, ET C'EST ECRIT : `AC-A3` promet qu'AUCUN
        #    identifiant de suivi n'a ete ecrit, « verifiable a la lecture du
        #    diff ». Un code qui a l'AIR vrai rend cette promesse invérifiable
        #    a l'oeil. Seul l'HOTE compte pour la branche REDIRECTEUR.
        p[BOM] += "\n\nhttps://s.click.aliexpress.com/e/_TEMOIN31FABRIQUE\n"
    elif _MUTANT == 32:
        p[PAGE] = p[PAGE].replace(
            "\n| `waveshare.com` | *la boutique elle-même* |",
            "\n| `reichelt.de` | *une boutique que la BOM ne nomme pas* | — | "
            "`https://www.reichelt.de/` | 2026-09-07 | ✅ **ATTEINTE** "
            "(méthode : outil de récupération automatisée). |"
            "\n| `waveshare.com` | *la boutique elle-même* |", 1)
    elif _MUTANT == 33:
        if "CHANGELOG.md" not in p:
            return e                      # fichier hors corpus ⇒ NO-OP ⇒ rc=3
        p["CHANGELOG.md"] += "\n- Replante : 5 000 € cumules.\n"
    elif _MUTANT == 34:
        if "docs/roadmap.md" not in p:
            return e                      # fichier hors corpus ⇒ NO-OP ⇒ rc=3
        p["docs/roadmap.md"] += ("\n\nJALON REPLANTE : le palier suivant est "
                                 "posé à 300 €.\n")
    elif _MUTANT == 35:
        p[PAGE] = p[PAGE].replace("(méthode : en-tête de navigateur)",
                                  "(sans plus de précision)", 1)
    elif _MUTANT == 36:
        # ⚠️ POSE EN PROSE, comme le 31 : le `?tag=` n'est ⛔ PAS un marqueur
        #    FRANC — seule la 3e branche, celle qui exige un hote de boutique
        #    DERIVE, peut l'attraper.
        p[BOM] += "\n\nhttps://www.aliexpress.com/item/1005.html?tag=dn65\n"
    elif _MUTANT == 37:
        p[BOM] += ("\n\nhttps://sale.aliexpress.com/__pc/x.htm?ref=dn65\n")
    else:
        raise AssertionError("mutant %d declare mais SANS CORPS" % _MUTANT)
    return e


# ═══════════════════════════ LES CONTROLES ═════════════════════════════════

def _texte_litteral(n):
    """La partie LITTERALE d'un libelle, meme construit par formatage."""
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Mod, ast.Add)):
        return _texte_litteral(n.left)
    if isinstance(n, ast.JoinedStr) and n.values:
        return _texte_litteral(n.values[0])
    return None


def ids_par_ast():
    """Les identifiants de TOUS les `ctrl(...)` de CE fichier, lus A L'AST.

    🔴 POURQUOI PAS `set(ids_emis)` : ce set est fige AU MOMENT DE L'APPEL de
       (c20). Tout controle ajoute APRES ce bloc en sortirait INVISIBLE a la
       reciproque."""
    try:
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            arbre = ast.parse(fh.read())
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    out = set()
    for n in ast.walk(arbre):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "ctrl" and len(n.args) >= 2):
            m = RE_ID_CTRL.match(_texte_litteral(n.args[1]) or "")
            if m:
                out.add(m.group(1))
    return out or None


def main():
    global _MUTANT
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--mutant", type=int, default=None,
                    help="REPLANTE une faute EN MEMOIRE pour prouver que le "
                         "controle correspondant sait ROUGIR")
    ap.add_argument("--liste-mutants", action="store_true",
                    help="dit ce que chaque mutant replante, et sort")
    args = ap.parse_args()
    if args.mutant is not None and args.mutant not in MUTANTS:
        sys.exit("MUTANT %d INCONNU : il n'est pas declare. ⛔ Un mutant qui "
                 "n'existe pas ne prouve RIEN — ⛔ ne pas conclure que le "
                 "controle est vert." % args.mutant)
    _MUTANT = args.mutant or 0

    if args.liste_mutants:
        # ⚠️ LES CIBLES SONT IMPRIMEES, ⛔ pas seulement le texte du mutant :
        #    `docs/affiliation.md` publie cette commande comme montrant « ce
        #    que chaque controle garde ». Sans la colonne des cibles, aucun
        #    identifiant de controle n'apparaissait — la page promettait ce
        #    que la sortie ne rendait pas.
        for n in sorted(MUTANTS):
            print("  %2d  [%s]  %s"
                  % (n, ",".join(CIBLES.get(n, ())) or "—", MUTANTS[n]))
        return 0

    print("=" * 78)
    print("dn6-5 — LA DECLARATION D'AFFILIATION EST GARDEE DANS LES DEUX SENS"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)
    print("cibles     : %s  +  %s  +  toute page `.md` suivie" % (PAGE, BOM))
    print("⛔ CETTE GATE NE JUGE AUCUN TAUX ET N'OUVRE AUCUNE CONNEXION — elle "
          "relit ce\n   que le depot PUBLIE, ⛔ pas la page du programme.")

    traces = suivis()
    if traces is None:
        ctrl(False, "(c0) l'arbre trace est LISIBLE",
             "⛔ `git ls-files` a refuse — ⛔ pas de parcours de disque en "
             "remplacement : un repertoire ignore n'est pas du depot")
        return bilan(1, "l'arbre trace est illisible")
    # 🔴 LE CORPUS EST `.md` **ET** `.txt`, ET C'EST CE QUI REND VRAIE LA
    #    PHRASE PUBLIEE. La page affirme relire « tous les fichiers de texte
    #    publies et suivis » : borne aux `.md`, la gate laissait hors scan des
    #    fichiers SUIVIS ET PUBLIES qui portent des adresses de boutique (les
    #    releves de prix de `mesures/`). ⇒ soit on elargit, soit la phrase
    #    ment ; on elargit. Mesure du 2026-09-07 : 0 marqueur sur les 408
    #    `.txt` suivis, l'elargissement ⛔ n'invente aucun rouge.
    prose, illisibles = {}, []
    for f in traces:
        if not f.endswith((".md", ".txt")):
            continue
        try:
            with open(os.path.join(RACINE, f), encoding="utf-8",
                      errors="replace") as fh:
                prose[f] = fh.read()
        except OSError as exc:
            # 🔴 ⛔ PAS UN `continue` SILENCIEUX : un fichier illisible
            #    RETRECIT le corpus de (c5) sans qu'aucun controle le dise —
            #    la population devient INCONNUE, ⛔ pas vide.
            illisibles.append("%s (%s)" % (f, type(exc).__name__))
    if illisibles:
        ctrl(False, "(c0) tout fichier de texte suivi est LISIBLE",
             "⛔ %d ILLISIBLE(S) : %s — le corpus de (c5) serait RETRECI en "
             "silence" % (len(illisibles), " · ".join(illisibles[:2])))
        return bilan(1, "%d fichier(s) suivi(s) illisible(s)" % len(illisibles))
    if BOM not in prose:
        ctrl(False, "(c0) `docs/bom.md` est au depot",
             "⛔ ABSENTE — la population se DERIVE d'elle, ⛔ il n'y a pas de "
             "repli")
        return bilan(1, "`docs/bom.md` est absente")

    etat = {"prose": prose,
            "cibles": {n: tuple(v) for n, v in CIBLES.items()},
            "regles": {"sortie_anticipee": False}}

    # 🔴 UN MUTANT QUI MEURT SORTIRAIT EN TRACEBACK, SANS `BILAN` — or « pas
    #    de BILAN » est le discriminant d'une gate MORTE. ⇒ il se rend en KO.
    try:
        neuf = muter(etat) if _MUTANT else etat
    except Exception as exc:                              # noqa: BLE001
        ctrl(False, "(c0) le mutant %d a une CIBLE et un CORPS" % _MUTANT,
             "⛔ %s: %s — la faute est dans le MUTANT, ⛔ pas dans la gate"
             % (type(exc).__name__, str(exc)[:80]))
        return bilan(1, "le mutant %d n'a pas pu s'appliquer" % _MUTANT)
    # 🔴 UN MUTANT SANS EFFET EST INVISIBLE AU CONTRAT DE LA CAMPAGNE.
    if _MUTANT and neuf == etat:
        ctrl(False, "(c0) le mutant %d a bien un EFFET" % _MUTANT,
             "⛔ SANS EFFET — son ancre litterale a disparu de la cible. "
             "⛔ Ce n'est PAS un controle vert : rc=3, mutant PERIME.")
        return bilan(3, "le mutant %d n'a eu aucun effet" % _MUTANT)

    prose = neuf["prose"]
    cibles, regles = neuf["cibles"], neuf["regles"]
    bom = prose[BOM]
    page = prose.get(PAGE, "")

    # ── (c1) LA PAGE EXISTE ET PORTE DU TEXTE ──────────────────────────────
    print("\n── (c1) LA PAGE D'AFFILIATION EXISTE ─────────────────────────────")
    if not ctrl(len(page.strip()) > MIN_CORPS,
                "(c1) `docs/affiliation.md` existe et porte du texte",
                "%d caracteres" % len(page) if len(page.strip()) > MIN_CORPS
                else "⛔ ABSENTE OU VIDE — ⛔ un vide n'est pas une absence de "
                     "defaut"):
        return bilan(1, "la page d'affiliation est absente ou vide")

    # ── (c2)(c3)(c4) LA POPULATION EST DERIVEE, PUIS CONFRONTEE ────────────
    print("\n── (c2)(c3)(c4) LA POPULATION SE DERIVE DE LA BOM ────────────────")
    pop1, pop2 = populations(bom)
    ctrl(bool(pop1), "(c2) la population des fournisseurs se DERIVE",
         "%d domaine(s) : %s" % (len(pop1), " · ".join(sorted(pop1)))
         if pop1 else
         "⛔ AUCUN domaine derive de `docs/bom.md` — ⛔ une gate ne sort pas "
         "verte sur une population VIDE")

    bloc_releve = ""
    if A_TITRE_RELEVE in page and A_TITRE_TENTEES in page:
        bloc_releve = page.split(A_TITRE_RELEVE, 1)[1].split(
            A_TITRE_TENTEES, 1)[0]
    t_rel = [(h, c) for h, c in tables(bloc_releve)
             if h and h[0].lower().startswith("domaine")]
    domaines_releves = set()
    for _h, corps in t_rel:
        for c in corps:
            domaines_releves.add(dom_nu(c[0]))
    # 🔴 LES **DEUX** SENS, comme (c4) — et c'etait un trou : un releve pouvait
    #    garder la ligne d'un fournisseur que la BOM ne nomme PLUS, et rien ne
    #    le disait. Un releve qui parle d'une boutique disparue est aussi faux
    #    qu'un releve qui oublie une boutique presente.
    manquants = sorted(d for d in pop1 if d not in domaines_releves)
    orphelines = sorted(d for d in domaines_releves if d and d not in pop1)
    ctrl(bool(t_rel) and not manquants and not orphelines,
         "(c3) le releve couvre la BOM, DANS LES DEUX SENS",
         "%d domaine(s) confronte(s), %d ligne(s) de releve"
         % (len(pop1), sum(len(c) for _h, c in t_rel))
         if t_rel and not manquants and not orphelines
         else ("⛔ cites par la BOM SANS releve : %s · releves SANS ligne de "
               "BOM : %s" % (" · ".join(manquants) or "—",
                             " · ".join(orphelines) or "—")
               if (manquants or orphelines) else
               "⛔ AUCUNE table de releve trouvee — ⛔ pas vert sur du vide"))

    bloc_tentees = ""
    if A_TITRE_TENTEES in page and A_TITRE_LOI in page:
        bloc_tentees = page.split(A_TITRE_TENTEES, 1)[1].split(
            A_TITRE_LOI, 1)[0]
    nommes = {t.lower().rstrip(".") for t in
              re.findall(r"`([^`]+)`", bloc_tentees)
              if RE_DOMAINE.match(t.lower().rstrip("."))}
    absents = sorted(pop2 - nommes)
    intrus = sorted(nommes - pop2)
    ctrl(bool(pop2) and not absents and not intrus,
         "(c4) la 2e population est publiee, DANS LES DEUX SENS",
         "%d adresse(s) tentee(s), toutes nommees" % len(pop2)
         if pop2 and not absents and not intrus
         else "⛔ derives SANS ligne : %s · nommes HORS de la BOM : %s"
              % (" · ".join(absents) or "—", " · ".join(intrus) or "—"))

    # ── (c5)(c6) LES DEUX SENS DE LA DECLARATION ───────────────────────────
    print("\n── (c5)(c6) L'ETAT MESURE, PUIS LA CONCORDANCE ───────────────────")
    # ⚠️ PIEGE NE DE L'ELARGISSEMENT AUX `.txt`, ECRIT PLUTOT QUE DECOUVERT :
    #    les fichiers de `mesures/` sont SUIVIS, donc RELUS. Un temoin qui
    #    recopierait dans son compte rendu une adresse marquee EN ENTIER ferait
    #    rougir (c5) sur le compte rendu lui-meme. ⇒ un releve de mesure cite
    #    une adresse marquee TRONQUEE, ou nomme le parametre sans l'adresse.
    #    Mesure du 2026-09-07 : les sorties de `mesures/dn6-5/T3` tronquent a
    #    56 caracteres et passent — mais c'est une PROPRIETE DE LA TRONCATURE,
    #    ⛔ pas une garantie.
    # 🔴 CE QUE LA REVUE DE SUIVI DU 2026-09-08 A CHANGE, ET POURQUOI : cette
    #    dependance a la troncature ⛔ n'etait pas seulement fragile, elle
    #    CASCADAIT. `attendue` se derivait de TOUT `marques` ⇒ le jour ou un
    #    relevé cite une adresse marquee en entier, (c6) exigeait des deux
    #    pages qu'elles declarent PORTER des liens affilies. Une citation
    #    aurait fait publier une affirmation FAUSSE. ⇒ (c5) continue de
    #    signaler un marqueur PARTOUT dans le corpus — c'est sa promesse —
    #    mais (c6) ne derive son attente que des DEUX PAGES QUI PORTENT LA
    #    DECLARATION. Ce que le depot AFFIRME de lui-meme se lit sur ce qu'il
    #    PUBLIE comme ses adresses, ⛔ pas sur ce qu'il cite.
    boutiques = tuple(sorted(pop1 | pop2))
    marques, n_url = [], 0
    for f in sorted(prose):
        for m in RE_URL.finditer(prose[f]):
            n_url += 1
            u = m.group(0)
            h = hote(u)
            if any(h == x or h.endswith("." + x) for x in REDIRECTIONS):
                marques.append("%s : %s (REDIRECTEUR)" % (f, u[:56]))
            elif RE_MARQUEUR_FRANC.search(u):
                marques.append("%s : %s (marqueur franc)" % (f, u[:56]))
            elif (RE_MARQUEUR_AMBIGU.search(u)
                  and est_boutique(h, boutiques)):
                marques.append("%s : %s (marqueur sur BOUTIQUE)" % (f, u[:56]))
    ctrl(not marques, "(c5) ⛔ aucune adresse publiee n'est MARQUEE",
         "%d adresse(s) relue(s) dans %d fichier(s) de texte suivis "
         "(`.md` + `.txt`), 0 marqueur, 0 redirecteur" % (n_url, len(prose))
         if not marques
         else "⛔ %d ADRESSE(S) MARQUEE(S) : %s — l'affirmation « aucun lien "
              "affilie » est DEVENUE FAUSSE"
              % (len(marques), " · ".join(marques[:2])))

    vig = {BOM: declaration_en_vigueur(bom),
           PAGE: declaration_en_vigueur(page)}
    publiees = [x for x in marques
                if x.startswith(BOM + " :") or x.startswith(PAGE + " :")]
    attendue = NEG if not publiees else POS
    absentes = sorted(f for f, d in vig.items() if d is None)
    fautives = sorted(f for f, d in vig.items()
                      if d is not None and d != attendue)
    ctrl(not absentes and not fautives,
         "(c6) l'affirmation CONCORDE avec l'etat mesure",
         "2 declarations EN VIGUEUR, « %s » des deux cotes" % attendue
         if not absentes and not fautives
         else ("⛔ %d CONTRADICTION(S) — l'etat mesure dit « %s », la "
               "declaration EN VIGUEUR dit l'inverse : %s"
               % (len(fautives), attendue, " · ".join(fautives))
               if fautives else
               "⛔ DECLARATION ABSENTE de %s — ⛔ le silence ne vaut pas "
               "« non »" % " · ".join(absentes)))

    # ── (c7)(c8)(c9) CE QUE `docs/bom.md` DOIT PORTER ──────────────────────
    print("\n── (c7)(c8)(c9) LA PAGE D'ACHAT : PHRASE, RENVOI, BASCULE ────────")
    ctrl(A_DECL_BOM in bom, "(c7) la phrase d'etat d'origine est INTACTE",
         "mot pour mot" if A_DECL_BOM in bom
         else "⛔ REECRITE OU EFFACEE — `NFR3` dit d'ANNOTER, ⛔ pas d'effacer")

    # ⚠️ LA CIBLE EST NORMALISEE, ⛔ pas comparee a un litteral : une ancre
    #    (`#…`) ou une autre profondeur de repertoire faisait declarer
    #    « AUCUN RENVOI » sur un lien qui MARCHE. Et la resolution se fait
    #    dans le CORPUS SUIVI, ⛔ plus sur le disque : un fichier non suivi
    #    satisfaisait le controle sans etre au depot.
    renvois = [x for x in re.findall(r"\]\(([^)\s]+)\)", bom)
               if (cible_lien(BOM, x) or "").endswith("affiliation.md")]
    resolus = [x for x in renvois if cible_lien(BOM, x) in prose]
    ctrl(bool(renvois) and len(resolus) == len(renvois),
         "(c8) la page d'achat RENVOIE vers la page, et ca resout",
         "%d renvoi(s), tous resolus" % len(renvois)
         if renvois and len(resolus) == len(renvois)
         else ("⛔ RENVOI MORT : %s" % " · ".join(set(renvois) - set(resolus))
               if renvois else
               "⛔ AUCUN RENVOI — le lecteur de la page d'achat ⛔ ne peut pas "
               "trouver le sujet"))

    sec_bom = corps_de(bom, A_SECTION_BOM) or ""
    conditions = re.findall(r"(?m)^\d+\. ", sec_bom)
    ctrl(A_BASCULE_BOM in sec_bom and len(conditions) >= 3,
         "(c9) le POINT DE BASCULE est ecrit, avec ses conditions",
         "%d condition(s) nommee(s)" % len(conditions)
         if A_BASCULE_BOM in sec_bom and len(conditions) >= 3
         else "⛔ %s — un titre qui l'annonce et rien derriere ⛔ n'est pas un "
              "point de bascule"
              % ("le libelle est absent" if A_BASCULE_BOM not in sec_bom
                 else "%d condition(s) seulement" % len(conditions)))

    # ── (c10)(c11) CHAQUE FAIT PORTE SA SOURCE, CHAQUE ECHEC SON MOTIF ─────
    print("\n── (c10)(c11) URL + DATE PARTOUT, MOTIF SUR CHAQUE ECHEC ─────────")
    muettes, n_lignes = [], 0
    for _h, corps in t_rel:
        for c in corps:
            n_lignes += 1
            ligne = " | ".join(c)
            if not RE_URL.search(ligne) or not RE_DATE.search(ligne):
                # ⚠️ `c[1]` EST GARDE : une table a UNE colonne sous un entete
                #    `Domaine` levait `IndexError` SANS `BILAN` — soit la
                #    signature d'une gate MORTE, ce que ce depot interdit.
                muettes.append(nu(c[0]) + " / "
                               + (nu(c[1])[:24] if len(c) > 1 else "?"))
    ctrl(n_lignes > 0 and not muettes,
         "(c10) chaque ligne de releve porte URL + DATE",
         "%d ligne(s) confrontee(s)" % n_lignes if n_lignes and not muettes
         else ("⛔ %d LIGNE(S) SANS URL OU SANS DATE : %s"
               % (len(muettes), " · ".join(muettes[:2])) if muettes
               else "⛔ AUCUNE ligne de releve — ⛔ pas vert sur du vide"))

    sans_motif, n_echecs = [], 0
    unites_page = unites(page)
    for l in unites_page:
        if A_NON_ATTEINT not in l:
            continue
        n_echecs += 1
        if not (RE_MOTIF.search(l) and RE_URL.search(l) and RE_DATE.search(l)):
            sans_motif.append(l.strip()[:48])
    ctrl(n_echecs > 0 and not sans_motif,
         "(c11) chaque source NON ATTEINTE porte son MOTIF",
         "%d echec(s) declare(s), tous motives" % n_echecs
         if n_echecs and not sans_motif
         else ("⛔ %d ECHEC(S) MUET(S) : %s — un blanc muet est le defaut que "
               "`NFR4` interdit" % (len(sans_motif), sans_motif[0])
               if sans_motif else
               "⛔ AUCUN echec declare — ⛔ le silence n'est pas « tout a "
               "repondu »"))

    # ── (c23) UN VERDICT DIT **AVEC QUOI** L'ADRESSE A ETE TENTEE ──────────
    print("\n── (c23) CHAQUE VERDICT NOMME SA METHODE DE RECUPERATION ─────────")
    # 🔴 C'EST LA LECON DE CETTE MARCHE, ET ELLE A ETE PAYEE ICI MEME : deux
    #    adresses avaient ete publiees « non atteintes, HTTP 403 » ; re-tentees
    #    le MEME JOUR avec un simple en-tete de navigateur, elles rendent
    #    HTTP 200 et 105 660 octets de conditions lisibles. Le 403 etait REEL —
    #    pour un OUTIL. ⇒ un verdict muet sur sa methode publie comme une
    #    propriete du monde ce qui n'est qu'une propriete de l'outil.
    #    ⛔ Ce controle ne juge ⛔ AUCUNE methode : il exige qu'elle soit DITE.
    # ⚠️ IL LIT LA CELLULE **VERDICT**, ⛔ PAS LA LIGNE ENTIERE — ET C'EST UNE
    #    MESURE : la cellule « ce que sa page affiche » d'une ligne parle de
    #    la « session du **navigateur** ». Lu sur la ligne entiere, le mot y
    #    suffisait, et le mutant 35 — qui EFFACE la methode du verdict —
    #    sortait **VERT**. Un controle satisfait par un mot qui parle d'autre
    #    chose ne garde rien.
    sans_methode, n_verdicts = [], 0
    for h, corps in t_rel:
        iv = next((k for k, n in enumerate(h)
                   if n.strip().lower().startswith("verdict")), len(h) - 1)
        for c in corps:
            n_verdicts += 1
            if iv >= len(c) or not methode_dite(c[iv]):
                sans_methode.append(nu(c[0])[:24])
    for l in unites_page:
        if A_NON_ATTEINT not in l:
            continue
        n_verdicts += 1
        if not methode_dite(l):
            sans_methode.append(l.strip()[:24])
    ctrl(n_verdicts > 0 and not sans_methode,
         "(c23) chaque verdict NOMME sa methode de releve",
         "%d verdict(s), tous methodes" % n_verdicts
         if n_verdicts and not sans_methode
         else ("⛔ %d VERDICT(S) MUET(S) SUR LEUR METHODE : %s — « non "
               "atteint » est une propriete de l'OUTIL, ⛔ pas de l'adresse"
               % (len(sans_methode), " · ".join(sans_methode[:2]))
               if sans_methode else
               "⛔ AUCUN verdict trouve — ⛔ pas vert sur du vide"))

    # ── (c12)(c13) LA LOI EST CITEE A SA SOURCE, ET SANS SE DEGUISER ───────
    print("\n── (c12)(c13) LES TEXTES CITES, ET LA MISE EN GARDE ──────────────")
    bloc_loi = ""
    if A_TITRE_LOI in page and A_TITRE_OWNER in page:
        bloc_loi = page.split(A_TITRE_LOI, 1)[1].split(A_TITRE_OWNER, 1)[0]
    t_loi = [(h, c) for h, c in tables(bloc_loi)
             if h and h[0].lower().startswith("texte")]
    sans_source = []
    n_textes = 0
    for _h, corps in t_loi:
        for c in corps:
            n_textes += 1
            ligne = " | ".join(c)
            urls = RE_URL.findall(ligne)
            if not (RE_DATE.search(ligne)
                    and any(any(o in hote(u) for o in OFFICIELS)
                            for u in urls)):
                sans_source.append(nu(c[0])[:40])
    ctrl(n_textes >= 4 and not sans_source,
         "(c12) chaque texte cite porte sa SOURCE OFFICIELLE",
         "%d texte(s), tous sources et dates" % n_textes
         if n_textes >= 4 and not sans_source
         else ("⛔ %d TEXTE(S) SANS SOURCE OFFICIELLE OU SANS DATE : %s"
               % (len(sans_source), " · ".join(sans_source[:2]))
               if sans_source else
               "⛔ %d texte(s) seulement — ⛔ nommer une obligation sans son "
               "texte n'est pas la nommer" % n_textes))

    ctrl(A_PAS_CONSEIL in page,
         "(c13) la page dit que ⛔ ce n'est PAS un conseil",
         "la mise en garde est ecrite" if A_PAS_CONSEIL in page
         else "⛔ ABSENTE — citer des textes sans cette phrase, c'est se faire "
              "passer pour un avocat")

    # ── (c14) CHAQUE GESTE OWNER PORTE UN PORTEUR **NOMME** ────────────────
    print("\n── (c14) L'ACCOMPAGNEMENT NOMME SES PORTEURS ─────────────────────")
    bloc_owner = ""
    if A_TITRE_OWNER in page and A_TITRE_BASCULE in page:
        bloc_owner = page.split(A_TITRE_OWNER, 1)[1].split(
            A_TITRE_BASCULE, 1)[0]
    t_own = [(h, c) for h, c in tables(bloc_owner)
             if h and h[-1].lower().startswith("porteur")]
    orphelins, n_gestes = [], 0
    for _h, corps in t_own:
        for c in corps:
            n_gestes += 1
            v = nu(c[-1])
            if v.lower() in REFUS_PORTEUR or len(v) < 3:
                orphelins.append("%s ⇒ « %s »" % (nu(c[0])[:28], v or "vide"))
    ctrl(n_gestes > 0 and not orphelins,
         "(c14) chaque geste owner porte un porteur NOMME",
         "%d geste(s), tous portes" % n_gestes if n_gestes and not orphelins
         else ("⛔ %d GESTE(S) SANS PORTEUR : %s — « a nommer » n'est ⛔ PAS un "
               "porteur (mesure `dn6-4`)"
               % (len(orphelins), " · ".join(orphelins[:2])) if orphelins
               else "⛔ AUCUN geste liste — ⛔ pas vert sur du vide"))

    # ── (c15)(c16) CE QUE LA DECISION OWNER A SORTI DU PERIMETRE ───────────
    print("\n── (c15)(c16) ⛔ NI JALON CHIFFRE, ⛔ NI REVENU PROJETE ──────────")
    # 🔴 LA POPULATION EST **TOUT LE CORPUS SUIVI**, ⛔ plus les deux pages —
    #    ET C'EST CE QUE LES PAGES PROMETTENT. `docs/affiliation.md`,
    #    `CHANGELOG.md` et `docs/roadmap.md` ecrivent tous les trois que ⛔
    #    AUCUN jalon n'apparait **nulle part** dans ce depot. Borne aux deux
    #    pages, la gate laissait poser un jalon dans `docs/roadmap.md` ou dans
    #    `CHANGELOG.md` sans qu'une seule gate du depot ne rougisse.
    jalons = []
    for f in sorted(prose):
        for m in RE_JALON.finditer(prose[f]):
            jalons.append("%s : « %s »" % (f, m.group(0)))
    ctrl(not jalons, "(c15) ⛔ aucun jalon CHIFFRE dans tout le depot",
         "aucun" if not jalons
         else "⛔ %d — ils sont SORTIS du perimetre par decision owner du "
              "2026-09-06 : %s" % (len(jalons), " · ".join(jalons[:2])))

    projections = []
    for f in sorted(prose):
        txt = prose[f]
        for m in RE_PROJECTION.finditer(txt):
            # 🔴 LA FENETRE EST BILATERALE — MESURE LE 2026-09-08 :
            #    « 300 € de commissions par mois » sortait VERT parce que le
            #    montant precedait le mot. Une projection ⛔ ne s'ecrit pas
            #    dans un seul ordre.
            deb = max(0, m.start() - PORTEE_PROJECTION)
            brut = txt[deb:m.start() + PORTEE_PROJECTION]
            rel = m.start() - deb
            g0 = 0
            for c in RE_COUPE_CLAUSE.finditer(brut[:rel]):
                g0 = c.end()
            fin = RE_COUPE_CLAUSE.search(brut, rel)
            fen = brut[g0:fin.start() if fin else len(brut)]
            mm = RE_MONTANT.search(fen)
            if not mm:
                continue
            if RE_EXEMPT_CONDITION.search(fen[:mm.start()]):
                continue          # un PRIX, ⛔ pas un jalon — voir RE_EXEMPT_PRIX
            projections.append("%s : « %s »" % (f, fen.strip()[:44]))
    ctrl(not projections, "(c16) ⛔ aucun REVENU PROJETE dans tout le depot",
         "aucun" if not projections
         else "⛔ %d — un taux AFFICHE est une condition, un revenu projete "
              "est une prevision : %s"
              % (len(projections), projections[0]))

    # ── (c17)(c18)(c19) LA BASCULE, L'ACCES, LA RE-MESURE ──────────────────
    print("\n── (c17)(c18)(c19) BASCULE · ACCES · RE-MESURE ───────────────────")
    bloc_bascule = ""
    if A_TITRE_BASCULE in page and A_TITRE_REMESURE in page:
        bloc_bascule = page.split(A_TITRE_BASCULE, 1)[1].split(
            A_TITRE_REMESURE, 1)[0]
    ctrl(len(bloc_bascule) >= MIN_CORPS and "prérequis" in bloc_bascule,
         "(c17) le point de bascule NOMME son prerequis",
         "%d caracteres" % len(bloc_bascule)
         if len(bloc_bascule) >= MIN_CORPS and "prérequis" in bloc_bascule
         else "⛔ %s — « ca changera un jour » n'est ⛔ pas un point de bascule"
              % ("section ABSENTE ou trop courte" if len(bloc_bascule)
                 < MIN_CORPS else "aucun prerequis nomme"))

    # ⚠️ MEME NORMALISATION QU'EN (c8) : un lien entrant ecrit avec une ancre
    #    ou depuis une autre profondeur faisait declarer la page ORPHELINE
    #    alors qu'elle est atteignable.
    entrants = sorted(
        f for f in prose if f != PAGE and f.endswith(".md")
        and any(cible_lien(f, h) == PAGE
                for h in re.findall(r"\]\(([^)\s]+)\)", prose[f])))
    ctrl(bool(entrants), "(c18) la page est ATTEIGNABLE depuis la prose",
         "%d lien(s) entrant(s) : %s" % (len(entrants), " · ".join(entrants))
         if entrants
         else "⛔ AUCUN LIEN ENTRANT — la page ORPHELINE que `AC-G4` de "
              "`dn6-2` a interdite")

    bloc_rem = ""
    if A_TITRE_REMESURE in page:
        bloc_rem = page.split(A_TITRE_REMESURE, 1)[1]
    cmds = {c for c in re.findall(r"`([^`]+)`", bloc_rem)
            if re.match(r"(?:python3|git|bash)\s", c)}
    ctrl(len(cmds) >= 3, "(c19) la page dit comment ses nombres se re-tirent",
         "%d commande(s) publiee(s)" % len(cmds) if len(cmds) >= 3
         else "⛔ %d commande(s) — un chiffre qu'on ne sait pas re-tirer est "
              "un chiffre a croire sur parole" % len(cmds))

    if regles["sortie_anticipee"]:
        return bilan(0)

    # ── (c20)(c21)(c22) LA RECIPROQUE, MECANIQUE ───────────────────────────
    print("\n── (c20)(c21)(c22) AUCUN CONTROLE GARDE PAR ZERO MUTANT ──────────")
    # 🔴 « N mutants, N vus rougir » prouve `mutant ⇒ rouge`, ⛔ JAMAIS
    #    `controle ⇒ couvert`. Les deux sens sont mesures, SEPAREMENT.
    lus_ast = ids_par_ast()
    reels = set(ids_emis) | (lus_ast or set())
    vises = set()
    for v in cibles.values():
        vises.update(v)
    nus = sorted(reels - vises, key=lambda s: (len(s), s))
    ctrl(not nus and lus_ast is not None,
         "(c20) chaque controle est vise par >= 1 mutant",
         "%d controle(s) lu(s) a l'AST, %d cible(s) declaree(s)"
         % (len(reels), len(vises)) if not nus and lus_ast is not None
         else ("⛔ %d CONTROLE(S) GARDE(S) PAR RIEN : %s"
               % (len(nus), " · ".join(nus)) if nus
               else "⛔ LA SOURCE NE S'ANALYSE PAS A L'AST — la population de "
                    "ce controle est INCONNUE, ⛔ pas vide"))
    perimees = sorted(vises - reels, key=lambda s: (len(s), s))
    ctrl(not perimees, "(c21) chaque cible de mutant est un controle REEL",
         "%d cible(s) confrontee(s)" % len(vises) if not perimees
         else "⛔ %d CIBLE(S) PERIMEE(S) : %s — un mutant qui vise un "
              "controle inexistant ⛔ ne garde rien"
              % (len(perimees), " · ".join(perimees)))
    orph = sorted(set(cibles) - set(MUTANTS))
    sans_cible = sorted(set(MUTANTS) - set(cibles))
    ctrl(not orph and not sans_cible,
         "(c22) `CIBLES` et `MUTANTS` se correspondent",
         "%d mutant(s), %d cible(s), cle a cle" % (len(MUTANTS), len(cibles))
         if not orph and not sans_cible
         else "⛔ cible(s) SANS mutant : %s · mutant(s) SANS cible : %s"
              % (orph or "—", sans_cible or "—"))

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : que le taux publie soit VRAI")
    print("   ni FRAIS. Un taux faux mais date et source la laisse VERTE —")
    print("   rouvrir la source est le seul chemin. Elle ne prouve pas non")
    print("   plus que le mutant rougisse BIEN le controle qu'il declare :")
    print("   ca, c'est `mesures/dn6-5/T3`, qui relit A COLONNE FIXE.")
    return bilan(1 if ko_total[0] else 0)


if __name__ == "__main__":
    sys.exit(main())

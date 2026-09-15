# Les liens affiliés — l'état mesuré, ce qui existe, et ce que l'owner doit signer lui-même

Cette page dit **si quelqu'un est payé quand vous cliquez**, **quels programmes existent réellement
pour les fournisseurs que ce dépôt cite**, **à quelles conditions**, **ce que la loi française et
européenne oblige à déclarer**, et **ce qui doit être vrai pour que l'état change**. Elle est écrite pour
quelqu'un qui n'a jamais vu ce projet et qui veut savoir **si on gagne de l'argent quand il clique**.

🔴 **Ce que cette page ⛔ n'est pas.** Ce n'est **ni une inscription, ni une intention d'inscription
datée, ni un objectif chiffré**. Aucun compte n'a été créé, aucune condition générale n'a été
acceptée, aucun identifiant de suivi n'a été écrit nulle part dans ce dépôt — et c'est **vérifiable
sur le diff** de la marche qui a produit cette page. S'inscrire est un **geste de l'owner** ; ce qui
est livré ici, c'est **ce qu'il faut savoir avant de le faire**, et **ce qu'il faudra écrire après**.

⚠️ **Annoté le 2026-09-15 (`dn6-6`) — le paragraphe ci-dessus est PÉRIMÉ, ⛔ pas effacé.** Ce jour-là,
l'owner a ouvert **lui-même** son compte au programme d'affiliation d'AliExpress (AliExpress Portals),
en a accepté les règles, et a généré les liens suivis : cinq identifiants de suivi sont désormais
écrits dans ce dépôt, **tous** dans [ce qu'il faut acheter](bom.md), chacun à côté de la mention
`affiliate link`. ⛔ Aucun agent n'a créé de compte, accepté de conditions ni généré de lien. Ce que
cette page livre depuis ce jour, c'est **ce qu'il fallait écrire après** : §2, §3, §5, §6 et §7 sont
annotés, datés, chaque fait neuf avec son adresse, sa date et sa méthode.

⛔ **Et il n'y a aucun chiffre de palier de revenus dans ce dépôt.** Des seuils chiffrés avaient été
esquissés pendant la rédaction de la nomenclature ; ils ont été **sortis du périmètre par décision de
l'owner le 2026-09-06**, et ils ne sont réintroduits **ni ici, ni dans
[ce qu'il faut acheter](bom.md)**.

---

## 1. Ce qu'est un lien affilié, en une phrase

Un lien affilié est une adresse **marquée** : elle contient un identifiant qui dit à la boutique
« ce visiteur vient de chez moi », de sorte qu'un achat déclenche une commission. La marque est
visible dans l'adresse elle-même — c'est un paramètre du type `aff_trace_key`, `aff_platform`,
`tag`, `ref` ou `utm_source`, ou bien un **domaine de redirection** qui compte les clics avant de
renvoyer vers la boutique.

⇒ **c'est mécaniquement détectable**, et c'est exactement ce que fait la vérification décrite au §8 :
elle relit toutes les adresses publiées par ce dépôt et compte celles qui portent une marque.
⚠️ *Annoté le 2026-09-15 (`dn6-6`)* : elle vérifie désormais aussi leur **place** — une adresse marquée
⛔ n'a le droit de vivre que dans la page d'achat, dans une cellule qui porte la mention `affiliate link`,
et cette mention ⛔ ne décore jamais une adresse nue.

---

## 2. L'état mesuré, et comment il se vérifie

🔵 **Ce dépôt ne porte aucun lien affilié.**

⚠️ **Annoté le 2026-09-15 (`dn6-6`) — la phrase d'état ci-dessus est PÉRIMÉE, ⛔ pas effacée** : elle
était vraie jusqu'à ce jour. Celle qui fait foi est écrite en dessous, comme le §7 l'annonçait.

🔵 **Ce dépôt porte des liens affiliés.** Cinq, et **seulement** dans [ce qu'il faut acheter](bom.md) :
un lien suivi du programme d'affiliation d'AliExpress dans la cellule `Source` de chacune des cinq
lignes AliExpress — la carte, les deux capteurs du palier « DeskNode + Ambiance », et les deux modules
hors palier — chacun avec la mention `affiliate link` dans la même cellule. ⛔ **Aucun lien Waveshare** :
la candidature attend son approbation, et elle est **hors de la marche qui a posé ces liens** (§6).

⚠️ **Annoté le 2026-09-15 (`dn6-7`), plus tard le même jour — le paragraphe ci-dessus est PÉRIMÉ pour
Waveshare, ⛔ pas effacé.** La candidature Waveshare est **approuvée** : l'owner a trouvé l'espace affilié
ouvert, sans e-mail. Sur décision owner du même jour, la **ligne de la carte** de la page d'achat pointe
désormais vers la **boutique Waveshare** avec un lien affilié Waveshare, et son lien suivi AliExpress est
**retiré** — la règle Waveshare interdit de diriger vers des vendeurs tiers de ses produits (§3). Les quatre
autres lignes gardent leur lien AliExpress : toujours **cinq** liens, tous dans la page d'achat, de **deux**
programmes.

🔵 **Ce dépôt porte des liens affiliés** — de deux programmes : Waveshare pour la carte, AliExpress pour les
quatre autres lignes.

Relevé le 2026-09-07 sur **tous les fichiers de texte suivis par git** — les pages `.md` **et** les
relevés `.txt`, ⛔ pas un échantillon : **0** adresse portant un marqueur d'affiliation, **0** sur un
domaine de redirection.
⚠️ **Ce que ce corpus ⛔ ne couvre pas, écrit plutôt que tu — et la première rédaction de cette
borne était trop large, corrigée le 2026-09-08 sans être effacée.** Elle ne nommait que les
fichiers **binaires** et les sources de code. Le corpus est celui des `.md` et des `.txt` suivis :
**436 fichiers sur les 685** que git suit. Les **249** autres sont, pour l'essentiel, du code et des
binaires — mais **97** d'entre eux sont du texte qui n'est ⛔ ni l'un ni l'autre (`.log`, `.yml`,
`.json`, `.csv`, `LICENSE`, `.gitignore`…), et **cinq** portent une adresse.
🔬 Ces cinq ont été relus à la main le 2026-09-08 avec les mêmes motifs : **0 marqueur**. Le zéro
ci-dessus tient donc au-delà de sa propre borne — mais c'est une **mesure datée**, ⛔ pas une
propriété de la gate, et un `.log` neuf ⛔ n'est vu par personne.
Les adresses de [ce qu'il faut acheter](bom.md) sont des **adresses de recherche nues** — elles
mènent à une page de résultats, et personne n'est payé si vous cliquez.

⚠️ *Annoté le 2026-09-15 (`dn6-6`)* : les deux zéros et les « adresses de recherche nues » ci-dessus sont
**périmés pour cinq adresses**. Re-mesuré ce jour par la vérification du §8 : **5** adresses marquées,
toutes sur le redirecteur de suivi d'AliExpress, toutes dans la page d'achat, chacune avec sa mention.
Un achat passé par l'un de ces liens peut rémunérer l'owner — ou non : les conditions relevées sont au
§3. Les **dix** adresses tentées de la page d'achat, elles, restent nues. La correspondance entre
chaque lien suivi (désigné par son seul code, ⛔ jamais par son adresse entière) et l'adresse de
recherche nue d'où l'owner l'a généré est dans
[le relevé du 2026-09-15](../mesures/dn6-6/T1-releves-du-2026-09-15.txt).
⚠️ *Annoté le 2026-09-15 (`dn6-7`), plus tard le même jour* : toujours **5** adresses marquées, mais
**quatre** seulement sur le redirecteur d'AliExpress ; la cinquième, sur la ligne de la carte, est la
**fiche produit Waveshare** portant l'identifiant d'affiliation de l'owner — ⛔ pas générée depuis une
recherche. Le relevé est [celui de `dn6-7`](../mesures/dn6-7/T1-releve-waveshare-du-2026-09-15.txt).

⚠️ **Ces deux zéros ⛔ ne sont pas un instantané** : ils sont **re-dérivés à chaque tir** de la
vérification du §8, sur la population que `git ls-files` rend. Un chiffre publié que rien ne
confronte est un défaut ; ceux-ci sont confrontés.

⚠️ **Ce n'est pas une promesse, c'est un état.** Il est **gardé dans les deux sens** : tant qu'aucune
adresse n'est marquée, les deux pages **doivent le dire** ; le jour où l'une l'est, la phrase
ci-dessus devient fausse et la vérification **rougit** — même si personne n'a pensé à mettre la
déclaration à jour. Le point de bascule est écrit au §7.
⚠️ *Annoté le 2026-09-15 (`dn6-6`)* : ce jour est venu, et la vérification a été **rouverte le même jour**
pour garder le **nouvel** engagement — toute adresse marquée est déclarée, à sa place, et toute mention
porte une adresse marquée. Retirer les liens sans remettre la phrase d'état à jour la fait rougir tout
autant.

---

## 3. Le relevé, fournisseur par fournisseur

La population de ce relevé **se dérive de [ce qu'il faut acheter](bom.md)**, ⛔ elle ne s'énumère
pas : ce sont les domaines des cellules `Source` de ses tables, plus le fabricant nommé en prose.
Mesuré le 2026-09-07, ça fait **deux** domaines — ⛔ pas onze. Le détail de la dérivation est dans
[T1](../mesures/dn6-5/T1-population-bom.txt), le relevé brut dans
[T2](../mesures/dn6-5/T2-releve-programmes.txt).
⚠️ *Annoté le 2026-09-15 (`dn6-6`)* : **toujours deux**. Les cinq cellules AliExpress pointent désormais sur
le redirecteur de suivi `s.click.aliexpress.com`, que la vérification attribue à son domaine parent,
`aliexpress.com` — ⛔ un redirecteur n'est pas un fournisseur.
⚠️ *Annoté le 2026-09-15 (`dn6-7`)* : **toujours deux**, mais les cellules AliExpress sont **quatre** ; celle
de la carte cite désormais `waveshare.com` directement.

| Domaine | Programme, tel que sa page le nomme | Ce que sa propre page affiche | Adresse relevée | Date | Verdict |
|---|---|---|---|---|---|
| `aliexpress.com` | **AliExpress Partner Program** | taux de commission **« range from 4% to 8% »**, l'électronique étant citée parmi les catégories les mieux payées ; inscription **« at no cost »**, puis **« once approved »** | `https://www.aliexpress.com/s/wiki-ssr/article/aliexpress-affiliate-commission-rate` | 2026-09-07 | ✅ **LU** (méthode : outil de récupération automatisée) — page publiée par le fournisseur lui-même. ⚠️ Elle date son chiffre de « 2024 » dans la phrase suivante : le taux est donc daté par sa source, pas par nous. |
| `aliexpress.com` | *le même programme — ses conditions d'admission détaillées* | — | `https://portals.aliexpress.com/help.htm` | 2026-09-07 | ⛔ **NON ATTEINT** (méthode : outil de récupération automatisée ; ⛔ pas re-tenté avec un en-tête de navigateur) — HTTP 302 vers une page de connexion : les conditions sont derrière une **authentification**. Les lire exige un compte, et créer un compte est le geste de l'owner. |
| `aliexpress.com` | *le même programme — son accord de service* | — | `https://sale.aliexpress.com/__pc/uTHnW6wRZg.htm` | 2026-09-07 | ⛔ **NON ATTEINT** (méthode : outil de récupération automatisée ; ⛔ pas re-tenté avec un en-tête de navigateur) — HTTP 404 : l'accord n'est pas à cette adresse. |
| `aliexpress.com` | *le portail du programme* | — | `https://portals.aliexpress.com/` | 2026-09-07 | ⛔ **NON ATTEINT** (méthode : outil de récupération automatisée ; ⛔ pas re-tenté avec un en-tête de navigateur) — HTTP 302 vers le portail, puis une page réduite à son titre : c'est une application, ⛔ pas une page de conditions. Aucun taux, aucune condition lisible. |
| `waveshare.com` | **Waveshare® Affiliate Program** | commission de base **2 %** par commande passée via le lien ; suivi valable **au moins 72 h** (et tant que dure la session du navigateur) ; versement **PayPal uniquement**, à partir de **US$5** cumulés, traité **avant le 15 du mois** ; frais PayPal annoncés **4,4 % + US$0,30** ; taux **renégociable** sur demande motivée ; une liste de promotions **interdites** est publiée | `https://www.waveshare.com/join_affiliate.html` | 2026-09-07 | ✅ **LU** (méthode : en-tête de navigateur) — page publiée par le fournisseur lui-même, section *Frequently Asked Questions*. |
| `waveshare.com` | *la boutique elle-même* | — | `https://www.waveshare.com/` | 2026-09-07 | ✅ **ATTEINTE** (méthode : en-tête de navigateur) — répond normalement. |
| `aliexpress.com` | **AliExpress Portals — « Affiliate Program Rules »**, version du 2025-08-01 | Commission : **7 %** pour « Other Categories » si le vendeur est affilié, **0** sinon (§5.1.5.5 des règles) ; la grille des taux ⛔ n'a **aucune ligne pour les composants électroniques** (lecture owner), d'où « Other Categories ». Plafond : **50 USD** de commission par commande. Retrait par virement : seuil de paiement **16 USD**, frais de **15 USD** par retrait. Durée de suivi : ⛔ **écrite nulle part** dans les règles. | `https://portals.aliexpress.com/` — ⚠️ l'adresse exacte du document de règles n'a **pas** été relevée | 2026-09-15 | ✅ **LU PAR L'OWNER** (méthode : lecture par l'owner dans un navigateur connecté au portail) — relevé owner, ⛔ pas relu par l'agent : le portail exige le compte de l'owner. |
| `waveshare.com` | **Waveshare® Affiliate Program** — relu le jour de la bascule | à *« What is the validity period of URL tracking? »*, la page affiche **toujours** *« At least 72 hours. »* puis *« Flexible Tracking: Your link remains active until the customer's browser session expires. »* ; *Who can Join* invite toujours *« primarily »* les présences sur **GitHub** ; la liste des promotions interdites nomme *« directing traffic to specific third-party sellers of Waveshare® products instead of the official Waveshare® store »* | `https://www.waveshare.com/join_affiliate.html` | 2026-09-15 | ✅ **LU** (méthode : en-tête de navigateur, `curl -A "Mozilla/5.0 …"`) — HTTP 200, 105 653 octets. |
| `waveshare.com` | **Waveshare® Affiliate Program** — candidature approuvée | candidature **approuvée** : l'espace affilié s'ouvre, ⛔ aucun e-mail reçu ; la durée de suivi ⛔ **n'y est affichée nulle part** ; prix de la carte en version *With Touch Function* : **29.99 USD** (la fiche affiche 22.99 – 29.99 USD selon les options) | `https://www.waveshare.com/esp32-s3-touch-lcd-2.8b.htm` | 2026-09-15 | ✅ **LU PAR L'OWNER** (méthode : lecture par l'owner dans un navigateur connecté à l'espace affilié) — ⚠️ l'adresse de l'espace affilié n'a pas été relevée ; la fourchette de prix est relue par l'agent (méthode : en-tête de navigateur, HTTP 200, fiche **sans** identifiant d'affiliation). |

⚠️ **Annoté le 2026-09-15 (`dn6-6`) — DEUX RELEVÉS WAVESHARE DIVERGENT, ET LES DEUX SONT ÉCRITS, ⛔ PAS
TRANCHÉS.** La ligne du 2026-09-07 ci-dessus écrit un suivi valable *« au moins 72 h »*. Le 2026-09-15,
l'owner a relevé un suivi *« désormais limité à la session du navigateur »* (méthode : lecture par
l'owner ; ⚠️ l'adresse où il l'a lu n'a pas été relevée). Le **même jour**, la page publique du
programme, relue par l'agent avec un en-tête de navigateur (dernière ligne du tableau — ⚠️ *annoté le
2026-09-15, `dn6-7` : la ligne « relu le jour de la bascule », qui n'est plus la dernière*), affiche
**toujours** *« At least 72 hours »*. ⇒ ⛔ cette page ne publie pas que les 72 h ont disparu, et ⛔ elle
ne publie pas non plus que le relevé de l'owner est faux : ce qui les départagerait est l'espace
affilié Waveshare, que la candidature en attente ne donne pas encore.
⚠️ *Annoté le 2026-09-15 (`dn6-7`)* : la candidature est approuvée et l'espace affilié s'ouvre — mais il
**n'affiche la durée de suivi nulle part** (relevé owner, ligne « candidature approuvée » du tableau). ⛔ L'écart reste non
tranché, et le lien Waveshare est posé quand même, sur décision owner.
⚠️ *Et la règle Waveshare citée ci-dessus* — ne pas diriger vers des vendeurs tiers — ⛔ est
**assumée par l'owner**, ⛔ pas ignorée : la carte de la page d'achat pointe vers AliExpress. C'est une
décision owner du 2026-09-15, écrite ici pour qu'elle ne se redécouvre pas.
⚠️ *Annoté le 2026-09-15 (`dn6-7`), plus tard le même jour* : ⛔ **plus vrai** — la candidature approuvée,
l'owner a décidé que la carte **s'achète chez Waveshare** ; son lien AliExpress est retiré de la page
d'achat, et le conflit avec cette règle est **levé** (§6).
⚠️ *Ce que la ligne AliExpress du 2026-09-15 ⛔ ne dit pas* : l'adresse exacte du document de règles
n'a pas été relevée, et la durée de suivi n'y est écrite nulle part — ⛔ ni l'une ni l'autre n'est
comblée ici. L'owner a aussi reçu l'e-mail *« Your affiliate account is ready »* ; il est consigné dans
[le relevé du 2026-09-15](../mesures/dn6-6/T1-releves-du-2026-09-15.txt), ⛔ pas recopié.

⚠️ *Annoté le 2026-09-15 (`dn6-6`, revue)* : dans la citation qui suit, « ces deux lignes » désigne les
deux lignes `waveshare.com` **du 2026-09-07** du tableau — le programme et la boutique —, ⛔ pas les deux
lignes du 2026-09-15 ajoutées depuis sous le tableau *(trois depuis `dn6-7`)*.

> ⏪ **CE QUE CES DEUX LIGNES DISAIENT LE MÊME JOUR, ET QUI EST RÉFUTÉ — ⛔ pas effacé (`NFR3`) :**
> les deux portaient un verdict d'échec, motivé par un **HTTP 403** — la première en le
> généralisant *« à toute récupération automatisée »*, la seconde en le rattachant au 403 que la
> fiche produit avait rendu le 2026-09-06.
> ⚠️ **Le verdict lui-même n'est ⛔ pas recopié ici, et c'est délibéré** : le recopier ajouterait
> **une occurrence de plus** au corpus que la vérification relit, et l'incident se reproduirait
> dans le texte qui le décrit. C'est une faute déjà payée dans ce dépôt — mesurée à `dn6-1`.
>
> 🔴 **LA LEÇON EST PLUS UTILE QUE LA CORRECTION, ET ELLE SE GÉNÉRALISE : « non atteint » est une
> propriété de la MÉTHODE de récupération, ⛔ pas de l'adresse.** Le 403 était **réel** — pour un
> outil. Re-tentées le 2026-09-07 avec un simple en-tête de navigateur, les **deux** adresses
> rendent **HTTP 200**, et la première rend **105 660 octets** de conditions lisibles.
> ⇒ **un verdict d'échec doit dire AVEC QUOI l'adresse a été tentée**, sinon il publie comme une
> propriété du monde ce qui n'est qu'une propriété de l'outil.
>
> ⚠️ **ET ÇA NE S'ARRÊTE PAS À CETTE PAGE.** [Ce qu'il faut acheter](bom.md) publie *« Prix
> fabricant non relevable — `waveshare.com/esp32-s3-touch-lcd-2.8b.htm` rend **HTTP 403** à toute
> récupération automatisée »*. Cette fiche produit rend elle aussi **HTTP 200** le 2026-09-07.
> ⛔ **Cette page ne la corrige pas** : le relevé de prix n'est pas son territoire, et une table de
> prix se re-relève, ⛔ elle ne se rafistole pas. Le constat est **écrit au ledger de planification
> avec son porteur**.
> ⚠️ *Annoté le 2026-09-15 (`dn6-6`)* : la page d'achat est désormais en anglais. La phrase citée y vit
> **traduite** (*Manufacturer price not surveyable*), et elle y est **annotée comme réfutée**, datée,
> juste en dessous — ⛔ toujours pas corrigée : le re-relevé du prix reste porté au ledger.

### 🔴 Ce qui est LU, ce qui reste inconnu, et pourquoi la différence compte

**Ce qui est lu tient sur une ligne** : le taux de base de Waveshare est de **2 %**, il est écrit
sur **la page du programme lui-même**, à la question *« What is our base commission? »*, et il est
daté ici du 2026-09-07. Un taux lu sur sa propre page est une **condition vérifiable** ; le même
chiffre repris d'une note interne n'aurait été qu'un souvenir. La différence n'est pas de forme :
elle décide si quelqu'un peut aller **rouvrir la source** et constater que ça a changé.

> ⏪ **CE QUE CE PARAGRAPHE DISAIT, ET QUI EST RÉFUTÉ — ⛔ pas effacé (`NFR3`) :** *« Un taux de
> **2 %** pour Waveshare circule dans les notes internes du projet. Il n'est ⛔ pas lu sur la page
> du programme, ⛔ pas daté, ⛔ pas sourcé — et il n'est donc republié nulle part ici. »*
> 🔴 **Il l'est.** Le raisonnement était juste, sa **prémisse** était fausse — et elle l'était pour
> une seule raison : la page avait été déclarée inatteignable sans dire **avec quoi** on l'avait
> tentée. ⇒ *« on ne l'a pas lu »* et *« on n'a pas su l'ouvrir »* sont deux affirmations
> différentes, et seule la seconde était vraie.

⚠️ **Quatre conditions restent inconnues — pour AliExpress seulement** : la durée du cookie, le
seuil de paiement, le plafond éventuel par commande, et le critère d'approbation. Aucune des pages
atteintes ne les affiche. Elles ⛔ ne se devinent pas ; elles se liront **depuis le portail**, une
fois un compte ouvert — et c'est un geste de l'owner (§6).
✅ **Pour Waveshare, ces quatre-là sont désormais LUES** (2 %, 72 h, US$5, approbation après
confirmation de réception) — voir la ligne du tableau ci-dessus.
⚠️ **Annoté le 2026-09-15 (`dn6-6`)** — pour AliExpress, **trois** des quatre sont fermées par le relevé
de l'owner (ligne du 2026-09-15 du tableau) : le seuil de paiement et le plafond par commande sont
**lus**, et l'approbation est **acquise** — le compte de l'owner est actif, même si le critère lui-même
n'a pas été lu. ⛔ **La durée de suivi reste inconnue** : elle n'est écrite nulle part dans les règles
relevées, et elle ⛔ ne se devine pas. ⚠️ Et pour Waveshare, le « 72 h » est **contesté** par le relevé de
l'owner du même jour — les deux relevés sont écrits sous le tableau.

---

## 4. Les dix adresses tentées ne sont ⛔ pas des fournisseurs

[Ce qu'il faut acheter](bom.md) porte une seconde liste : dix adresses **tentées sans succès** le
2026-09-06 — 403, 404, délai dépassé, page sans fiche produit. Ce sont
`waveshare.com`, `mouser.fr`, `tinytronics.nl`, `eckstein-shop.de`, `octopart.com`, `adafruit.com`,
`gotronic.fr`, `welectron.com`, `berrybase.de` et `thepihut.com`.

⛔ **Leurs programmes n'ont pas été recherchés, et le motif est écrit** : le dépôt ne sait même pas
si ces boutiques vendent la carte. Publier dix lignes de conditions sur des boutiques dont on ignore
le catalogue donnerait une page longue et sans prise, ⛔ pas une information.

⇒ **ce qui les ferait entrer dans le relevé du §3** : qu'une cellule `Source` de la nomenclature les
cite. La vérification **dérive cette colonne à chaque tir** — ce jour-là, elle rougit tant que le
relevé ne les a pas. ⛔ Cette liste ne peut donc pas pourrir en silence.

⚠️ `waveshare.com` est le seul des dix qui est **aussi** un fournisseur du §3, par la prose : c'est
le fabricant de la carte. Ses deux lignes de relevé sont ci-dessus.
⚠️ *Annoté le 2026-09-15 (`dn6-7`)* : `waveshare.com` est désormais **aussi** cité par une cellule `Source`
(la ligne de la carte), ⛔ plus seulement par la prose ; il a **quatre** lignes de relevé au §3.

---

## 5. L'obligation de déclaration en France et dans l'Union

⛔ **Ce n'est pas un conseil juridique.** Ce sont des textes cités **avec leur source officielle et
la date à laquelle ils ont été lus**. Ils disent ce qu'ils disent ; ils ⛔ ne disent pas ce que
l'owner doit faire dans sa situation, et lui seul peut aller chercher cette réponse-là.

| Texte | Ce qu'il impose, en une ligne | Source officielle | Lue le |
|---|---|---|---|
| Directive 2005/29/CE, annexe I, point 11 | interdit d'utiliser « un contenu rédactionnel dans les médias pour faire la promotion d'un produit, alors que le professionnel a financé celle-ci lui-même, sans l'indiquer clairement » | `https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:32005L0029` | 2026-09-07 |
| Code de la consommation, article L121-4, 11° | la même interdiction, en droit français : « sans l'indiquer clairement » est le point qui mord | `https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000044563107` | 2026-09-07 |
| LOI n° 2023-451 du 9 juin 2023, article 1er | définit qui exerce l'« influence commerciale par voie électronique » : mobiliser **à titre onéreux** sa notoriété auprès de son audience | `https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000047663185` | 2026-09-07 |
| LOI n° 2023-451 du 9 juin 2023, article 5, I | impose alors la mention explicite « Publicité » **ou** « Collaboration commerciale » | `https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000047663211` | 2026-09-07 |
| impots.gouv.fr — économie collaborative et plateformes numériques | « Les sommes perçues [...] sont susceptibles de constituer des revenus qui doivent [...] figurer dans la déclaration de revenus du bénéficiaire », et une activité imposable **doit être immatriculée** | `https://www.impots.gouv.fr/economie-collaborative-et-plateformes-numeriques` | 2026-09-07 |

### Les sources officielles qu'on n'a ⛔ pas pu atteindre

⚠️ La doctrine administrative qui **explique** ces textes n'a pas été lue, et c'est écrit plutôt que
comblé par une reformulation :

- `https://www.economie.gouv.fr/dgccrf/influenceurs-et-influence-commerciale` — relevée le 2026-09-07, méthode : **outil de récupération automatisée** — ⛔ **NON ATTEINT**, HTTP 403 ; ⛔ pas re-tentée avec un en-tête de navigateur.
- `https://www.economie.gouv.fr/influenceurs-quels-sont-mes-devoirs` — relevée le 2026-09-07, méthode : **outil de récupération automatisée** — ⛔ **NON ATTEINT**, HTTP 403 ; ⛔ pas re-tentée avec un en-tête de navigateur.

⚠️ **Et ces deux-là portent exactement le doute que le §3 vient de payer** : un 403 rendu à un outil
n'est ⛔ pas un 403 rendu à un navigateur. Elles sont donc publiées **avec leur méthode**, et le fait
qu'elles n'aient ⛔ pas été re-tentées est écrit — ⛔ ce n'est pas une propriété de ces adresses.

### Ce que ça donne concrètement pour ce dépôt

Deux choses, et elles ⛔ ne se confondent pas :

1. **La transparence** est due **dès le premier lien marqué**, indépendamment de tout revenu : c'est
   le point 11 ci-dessus. Une page d'achat qui rapporte sans le dire est exactement le cas visé.
2. **La déclaration fiscale et l'immatriculation** ne se déclenchent pas à la publication du lien
   mais à la **perception** de sommes. C'est un sujet distinct, et c'est celui sur lequel un dépôt
   ⛔ ne peut rien faire à la place de son auteur.

⚠️ Le régime de l'« influence commerciale » (articles 1er et 5) suppose de **mobiliser une audience
à titre onéreux**. Un dépôt de code **privé** n'a pas d'audience publique aujourd'hui — mais
⛔ **ce n'est pas une exemption** : le jour où le dépôt est public et où un lien est marqué, la
question se pose entière, et la mention explicite est le comportement sûr.

⚠️ **Annoté le 2026-09-15 (`dn8-8`)** : le dépôt est **public** depuis ce jour, et la phrase sur le
dépôt de code privé sans audience publique a cessé d'être vraie. L'autre moitié de la condition —
un lien marqué — ⛔ n'est pas remplie : l'état du §2 n'a pas changé.

⚠️ **Annoté le 2026-09-15 (`dn6-6`) — l'autre moitié est remplie depuis ce jour** : cinq liens marqués
sont publiés dans la page d'achat, et l'état du §2 a changé. La transparence du point 1 ci-dessus est
donc **due**. La mention posée à côté de chaque lien est **`affiliate link`**, en anglais comme la page,
dans la même cellule que le lien.
⚠️ **Juxtaposé, ⛔ pas tranché** : l'article 5, I de la loi n° 2023-451 cité dans le tableau ci-dessus
impose la mention « Publicité » **ou** « Collaboration commerciale » à l'influence commerciale ; la
mention retenue par l'owner est `affiliate link`. Cette page ⛔ ne dit pas si l'une vaut l'autre, ni si
le régime de l'influence commerciale s'applique à ce dépôt — ⛔ elle n'est pas un conseil, et seul
l'owner peut aller chercher cette réponse-là.

---

## 6. Ce que l'owner doit faire lui-même

Chaque geste ci-dessous est **hors de portée d'un agent** — non par prudence, mais parce qu'il
engage une personne : un compte, un contrat, une identité fiscale.

| Geste | Pourquoi ⛔ un agent ne peut pas le faire à sa place | Porteur |
|---|---|---|
| Ouvrir un compte sur le portail d'un programme et **accepter ses conditions générales** | accepter un contrat engage une personne ; ⛔ un agent n'a ni identité, ni consentement à donner | **owner** |
| **Lire les quatre conditions inconnues d'AliExpress** du §3 (cookie, seuil de paiement, plafond, critère d'approbation) | elles sont derrière l'authentification du portail — mesuré le 2026-09-07, redirection vers une page de connexion. ⚠️ Celles de Waveshare, elles, sont **publiques et lues** | **owner** |
| Décider si le dépôt **doit** porter des liens affiliés | c'est un arbitrage de projet, ⛔ pas une conséquence technique ; rien dans ce dépôt ne l'impose | **owner** |
| Déclarer les sommes perçues et **immatriculer** l'activité si elle devient imposable | acte fiscal personnel ; ⛔ hors de tout dépôt de code | **owner** |
| **Annoter les deux phrases d'état** le jour où un lien est posé — la périmée **reste**, la neuve s'écrit en dessous | c'est le geste qui rend la promesse vraie ; la vérification l'**exige**, elle ne peut pas l'écrire à sa place | **owner** |
| 🆕 *(2026-09-15)* **Cliquer une fois chacun des cinq liens suivis** de la page d'achat, ⛔ sans acheter, et confirmer qu'il ouvre la recherche du bon module | un clic est **compté** par le programme sur le compte de l'owner, et ses règles sanctionnent le trafic artificiel — annexe des pénalités, au titre du spam de trafic (lecture owner) : ⛔ un agent n'envoie aucune requête vers un lien suivi | **owner** |
| 🆕 *(2026-09-15)* **Suivre la candidature Waveshare** — « Waiting for approval » — et, si elle est approuvée, relever la durée de suivi dans l'espace affilié avant tout lien Waveshare. ⚠️ Une approbation mettrait le lien AliExpress de la carte en **conflit** avec la règle Waveshare sur les vendeurs tiers : elle exige une **nouvelle décision owner** avant tout lien Waveshare | la candidature et son espace affilié sont au nom de l'owner ; ⛔ elle est hors de la marche qui a posé les liens AliExpress | **owner** |
| 🆕 *(2026-09-15, revue)* **Décider si la mention `affiliate link` suffit**, ou s'il faut « Publicité » / « Collaboration commerciale » (§5) | c'est l'appréciation juridique de sa propre situation ; ⛔ une page de dépôt ne la tranche pas, et un agent ne donne pas de conseil juridique | **owner** |

⚠️ **Le dernier n'est pas facultatif** : tant qu'il n'est pas fait, la vérification reste rouge. Elle
est écrite pour ça — un lien marqué posé sans mise à jour de la déclaration est **exactement** le cas
qu'elle attrape.

⚠️ **Annoté le 2026-09-15 (`dn6-6`) — l'état des gestes ci-dessus, ce jour-là** :
- *ouvrir un compte et accepter ses conditions* — **fait par l'owner** pour AliExpress ; pour Waveshare,
  la candidature est déposée et **attend son approbation** ;
- *lire les quatre conditions inconnues d'AliExpress* — **trois** lues par l'owner, ⛔ la durée de suivi
  est écrite nulle part (§3) ;
- *décider si le dépôt doit porter des liens affiliés* — **décidé par l'owner** : oui, sur la page d'achat ;
- *déclarer les sommes perçues* — ⛔ rien à dire tant que rien n'est perçu, et ⛔ ce n'est pas le
  territoire d'un dépôt ;
- *annoter les deux phrases d'état* — **fait**, le même jour, dans les deux pages : la vérification ⛔ n'est
  pas restée rouge.

⚠️ **Annoté le 2026-09-15 (`dn6-7`), plus tard le même jour** : *suivre la candidature Waveshare* — elle est
**approuvée** (espace affilié ouvert, ⛔ sans e-mail) ; la durée de suivi n'y est **pas affichée** (§3) ; et la
**nouvelle décision owner** qu'exigeait le conflit avec la règle sur les vendeurs tiers est **prise** : la
carte s'achète chez Waveshare, son lien AliExpress est retiré de la page d'achat. Les **conditions** du
programme ont été acceptées par l'owner en déposant sa candidature (case des conditions du formulaire —
relevé owner du 2026-09-15). ⚠️ Le geste *cliquer une fois chacun des cinq liens suivis* porte désormais
sur **quatre** recherches AliExpress **et** la fiche Waveshare de la carte, ⛔ plus sur cinq recherches.
✅ **Annoté le 2026-09-15 (`dn6-7`) — TROIS des cinq sont FAITS** : l'owner a cliqué, ⛔ sans acheter, les
trois liens du palier « DeskNode + Ambiance » — la **carte** (fiche Waveshare), le **BME680** et le
**BH1750** — et chacun ouvre la bonne page. ⛔ **Les deux liens des modules hors palier** (`VL6180X`,
`INA219`) ⛔ **n'ont pas été cliqués** : leur destination reste une **déclaration de l'owner**, ⛔ pas une
observation, et c'est au ledger de planification avec son porteur.

---

## 7. Le point de bascule

**Ce qui doit être vrai pour que l'état du §2 change** — les trois conditions, dans l'ordre :

1. **Un prérequis qui ne dépend pas de nous** : le programme doit être **ouvert** à ce dépôt. C'est aujourd'hui
   **inconnu, ⛔ pas acquis** — mais l'inconnue est **partielle**, ⛔ plus totale : les conditions
   d'admission d'AliExpress sont derrière une authentification, tandis que **celles de Waveshare
   sont publiques et lues** (§3).
   🔴 **Et c'est là que la mesure devient tranchante.** La rubrique **Who can Join** de Waveshare
   dit accueillir *« a college student, an individual electronics maker, a DIY electronics
   hobbyist, a tech enthusiast »* — ⛔ aucun seuil d'audience — **puis** ajoute : *« At this time,
   we are primarily inviting individuals with a presence or influence on platforms like YouTube,
   **GitHub**, Reddit, Discord, or similar channels »* (lu le 2026-09-07). ⇒ la plateforme nommée
   **est celle de ce dépôt**, et ce dépôt y est **privé** aujourd'hui : une présence privée n'est
   pas une présence. ⚠️ *« primarily inviting »* ⛔ n'est pas *« exclusively »* — c'est un critère
   **mou**, ⛔ pas une porte fermée, et seul le dépôt d'une candidature tranchera.
   ⚠️ Un second indice, ⛔ pas une preuve : une page publiée par AliExpress elle-même tient une plateforme
   numérique publique (blog, chaîne, réseau social, site) pour **« essential »** à l'affiliation. Ce
   dépôt est **privé** aujourd'hui. Si l'indice se confirme, la bascule publique est un **prérequis**
   de l'inscription ; s'il est démenti, l'écart s'écrira ici.
   ⚠️ **Annoté le 2026-09-15 (`dn8-8`)** : le dépôt est **public** sur GitHub depuis ce jour — les
   deux « privé aujourd'hui » de ce point ont cessé d'être vrais. Le critère de Waveshare reste
   **mou** et l'indice d'AliExpress reste un indice : seule une candidature, geste de l'owner
   (§6), tranchera.
   ⚠️ **Annoté le 2026-09-15 (`dn6-6`)** : pour **AliExpress**, la condition est **réunie** — le compte de
   l'owner est actif (relevé owner, §3). Pour **Waveshare**, ⛔ pas encore : la candidature attend son
   approbation, et ⛔ aucun lien Waveshare n'est publié.
   ⚠️ **Annoté le 2026-09-15 (`dn6-7`)** : pour **Waveshare** aussi, la condition est **réunie** — la
   candidature est approuvée le même jour, et un lien Waveshare est publié, sur la seule ligne de la carte.
2. **Un geste de l'owner** : ouvrir le compte, accepter les conditions générales, relever les quatre
   conditions inconnues (§6).
   ⚠️ **Annoté le 2026-09-15 (`dn6-6`)** : **fait par l'owner** pour AliExpress — trois conditions sur
   quatre relevées, la durée de suivi introuvable dans les règles.
   ⚠️ **Annoté le 2026-09-15 (`dn6-7`)** : **fait par l'owner** pour Waveshare aussi — candidature déposée
   avec la case des conditions cochée (relevé owner), approuvée le même jour ; la durée de suivi ⛔ n'est
   affichée nulle part dans l'espace affilié.
3. **Une annotation des deux phrases d'état** : celle du §2 de cette page, et celle de la section
   correspondante de [ce qu'il faut acheter](bom.md). ⛔ **Elles ne s'effacent pas** : la phrase
   périmée **reste**, et la nouvelle s'écrit **en dessous** — c'est la règle « annoter, ⛔ pas
   effacer » du dépôt, et la vérification est écrite pour que ce geste-là soit **le seul** qui
   passe. ⚠️ **Et elle restera rouge ensuite**, jusqu'à ce que quelqu'un rouvre la vérification pour
   y écrire le **nouvel** engagement. C'est délibéré : changer une promesse publiée doit être un
   geste écrit, ⛔ pas une dérive silencieuse.
   ⚠️ **Annoté le 2026-09-15 (`dn6-6`)** : **fait**, dans les deux pages, la périmée gardée au-dessus de
   la neuve. ⛔ Et la vérification **n'est pas restée rouge** : elle a été rouverte **le même jour** pour y
   écrire le nouvel engagement — toute adresse marquée est déclarée, à sa place, avec sa mention, et toute
   mention porte une adresse marquée (`tools/verif_affiliation_dn65.py`, contrôles `(c5)` et `(c24)`).

**Où ça se dira** : **ici**, au §2 et au §3 (le programme, ses conditions, son taux, sa date), **et**
dans la section « Liens affiliés » de la page d'achat, à la place exacte où vit déjà la phrase d'état
— parce que c'est là que se trouve le lecteur que ça concerne, au moment où il achète.
⚠️ *Annoté le 2026-09-15 (`dn6-6`)* : la page d'achat est passée **en anglais** le même jour, en une seule
page ; cette section s'y appelle désormais `Affiliate links`, et la déclaration neuve y est écrite sous
la phrase d'origine traduite.

⛔ **Ce qui ⛔ ne fait PAS partie du point de bascule** : un montant, un palier de revenus, une date
cible. Ils ont été sortis du périmètre par l'owner, et les réintroduire par la porte du « point de
bascule » serait remettre exactement ce qui a été retiré.

---

## 8. Comment ces nombres se re-mesurent

Rien ici n'est à croire sur parole. Depuis la racine du dépôt :

| Ce qu'on veut re-mesurer | La commande |
|---|---|
| l'état d'affiliation, les deux populations, la concordance des deux pages | `python3 tools/verif_affiliation_dn65.py` |
| ce que chaque contrôle garde, et la faute que son mutant replante | `python3 tools/verif_affiliation_dn65.py --liste-mutants` |
| la population relue (⛔ l'arbre suivi, pas le disque) | `git ls-files '*.md' '*.txt'` |
| la forme de la page d'achat, inchangée par cette page | `python3 tools/verif_bom_dn61.py` |

Les bornes de départ et d'arrivée sont dans [T0](../mesures/dn6-5/T0-bornes-depart.txt) et
[T7](../mesures/dn6-5/T7-bornes-arrivee.txt) ; la campagne de mutants et sa réciproque dans
[T3](../mesures/dn6-5/T3-campagne-mutants.txt).
⚠️ *Annoté le 2026-09-15 (`dn6-6`)* : celles de la bascule sont dans
[T0](../mesures/dn6-6/T0-bornes-depart.txt), [T1](../mesures/dn6-6/T1-releves-du-2026-09-15.txt),
[T3](../mesures/dn6-6/T3-campagne-mutants.txt) et [T7](../mesures/dn6-6/T7-bornes-arrivee.txt).

⛔ **Ce que la vérification ne prouve pas** : elle ne dit **rien** de la vérité d'un taux ni de sa
fraîcheur. Un taux faux mais daté et sourcé la laisse verte. Rouvrir la source est le seul chemin —
et c'est pour ça que chaque ligne du §3 porte son adresse.

---

## Licence

Cette page est de la documentation : **CC-BY-SA-4.0**, comme le reste de ce répertoire. Voir
[LICENSING.md](../LICENSING.md).

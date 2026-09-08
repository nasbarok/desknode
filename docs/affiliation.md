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

---

## 2. L'état mesuré, et comment il se vérifie

🔵 **Ce dépôt ne porte aucun lien affilié.**

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

⚠️ **Ces deux zéros ⛔ ne sont pas un instantané** : ils sont **re-dérivés à chaque tir** de la
vérification du §8, sur la population que `git ls-files` rend. Un chiffre publié que rien ne
confronte est un défaut ; ceux-ci sont confrontés.

⚠️ **Ce n'est pas une promesse, c'est un état.** Il est **gardé dans les deux sens** : tant qu'aucune
adresse n'est marquée, les deux pages **doivent le dire** ; le jour où l'une l'est, la phrase
ci-dessus devient fausse et la vérification **rougit** — même si personne n'a pensé à mettre la
déclaration à jour. Le point de bascule est écrit au §7.

---

## 3. Le relevé, fournisseur par fournisseur

La population de ce relevé **se dérive de [ce qu'il faut acheter](bom.md)**, ⛔ elle ne s'énumère
pas : ce sont les domaines des cellules `Source` de ses tables, plus le fabricant nommé en prose.
Mesuré le 2026-09-07, ça fait **deux** domaines — ⛔ pas onze. Le détail de la dérivation est dans
[T1](../mesures/dn6-5/T1-population-bom.txt), le relevé brut dans
[T2](../mesures/dn6-5/T2-releve-programmes.txt).

| Domaine | Programme, tel que sa page le nomme | Ce que sa propre page affiche | Adresse relevée | Date | Verdict |
|---|---|---|---|---|---|
| `aliexpress.com` | **AliExpress Partner Program** | taux de commission **« range from 4% to 8% »**, l'électronique étant citée parmi les catégories les mieux payées ; inscription **« at no cost »**, puis **« once approved »** | `https://www.aliexpress.com/s/wiki-ssr/article/aliexpress-affiliate-commission-rate` | 2026-09-07 | ✅ **LU** (méthode : outil de récupération automatisée) — page publiée par le fournisseur lui-même. ⚠️ Elle date son chiffre de « 2024 » dans la phrase suivante : le taux est donc daté par sa source, pas par nous. |
| `aliexpress.com` | *le même programme — ses conditions d'admission détaillées* | — | `https://portals.aliexpress.com/help.htm` | 2026-09-07 | ⛔ **NON ATTEINT** (méthode : outil de récupération automatisée ; ⛔ pas re-tenté avec un en-tête de navigateur) — HTTP 302 vers une page de connexion : les conditions sont derrière une **authentification**. Les lire exige un compte, et créer un compte est le geste de l'owner. |
| `aliexpress.com` | *le même programme — son accord de service* | — | `https://sale.aliexpress.com/__pc/uTHnW6wRZg.htm` | 2026-09-07 | ⛔ **NON ATTEINT** (méthode : outil de récupération automatisée ; ⛔ pas re-tenté avec un en-tête de navigateur) — HTTP 404 : l'accord n'est pas à cette adresse. |
| `aliexpress.com` | *le portail du programme* | — | `https://portals.aliexpress.com/` | 2026-09-07 | ⛔ **NON ATTEINT** (méthode : outil de récupération automatisée ; ⛔ pas re-tenté avec un en-tête de navigateur) — HTTP 302 vers le portail, puis une page réduite à son titre : c'est une application, ⛔ pas une page de conditions. Aucun taux, aucune condition lisible. |
| `waveshare.com` | **Waveshare® Affiliate Program** | commission de base **2 %** par commande passée via le lien ; suivi valable **au moins 72 h** (et tant que dure la session du navigateur) ; versement **PayPal uniquement**, à partir de **US$5** cumulés, traité **avant le 15 du mois** ; frais PayPal annoncés **4,4 % + US$0,30** ; taux **renégociable** sur demande motivée ; une liste de promotions **interdites** est publiée | `https://www.waveshare.com/join_affiliate.html` | 2026-09-07 | ✅ **LU** (méthode : en-tête de navigateur) — page publiée par le fournisseur lui-même, section *Frequently Asked Questions*. |
| `waveshare.com` | *la boutique elle-même* | — | `https://www.waveshare.com/` | 2026-09-07 | ✅ **ATTEINTE** (méthode : en-tête de navigateur) — répond normalement. |

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

⚠️ **Le dernier n'est pas facultatif** : tant qu'il n'est pas fait, la vérification reste rouge. Elle
est écrite pour ça — un lien marqué posé sans mise à jour de la déclaration est **exactement** le cas
qu'elle attrape.

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
2. **Un geste de l'owner** : ouvrir le compte, accepter les conditions générales, relever les quatre
   conditions inconnues (§6).
3. **Une annotation des deux phrases d'état** : celle du §2 de cette page, et celle de la section
   correspondante de [ce qu'il faut acheter](bom.md). ⛔ **Elles ne s'effacent pas** : la phrase
   périmée **reste**, et la nouvelle s'écrit **en dessous** — c'est la règle « annoter, ⛔ pas
   effacer » du dépôt, et la vérification est écrite pour que ce geste-là soit **le seul** qui
   passe. ⚠️ **Et elle restera rouge ensuite**, jusqu'à ce que quelqu'un rouvre la vérification pour
   y écrire le **nouvel** engagement. C'est délibéré : changer une promesse publiée doit être un
   geste écrit, ⛔ pas une dérive silencieuse.

**Où ça se dira** : **ici**, au §2 et au §3 (le programme, ses conditions, son taux, sa date), **et**
dans la section « Liens affiliés » de la page d'achat, à la place exacte où vit déjà la phrase d'état
— parce que c'est là que se trouve le lecteur que ça concerne, au moment où il achète.

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

⛔ **Ce que la vérification ne prouve pas** : elle ne dit **rien** de la vérité d'un taux ni de sa
fraîcheur. Un taux faux mais daté et sourcé la laisse verte. Rouvrir la source est le seul chemin —
et c'est pour ça que chaque ligne du §3 porte son adresse.

---

## Licence

Cette page est de la documentation : **CC-BY-SA-4.0**, comme le reste de ce répertoire. Voir
[LICENSING.md](../LICENSING.md).

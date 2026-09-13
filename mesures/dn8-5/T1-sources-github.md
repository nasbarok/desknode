# dn8-5 / T1 — CHAQUE CAPACITÉ GITHUB NOMMÉE PAR UN FICHIER PUBLIC, ET SA SOURCE

🔴 **POURQUOI CE FICHIER EXISTE, ET C'EST UNE FAUTE PAYÉE, ⛔ PAS UNE PRÉCAUTION.** La passe 1 du
cadrage de cette marche a présenté le *reported content* de GitHub comme une voie disponible pour
ce dépôt, « à relever à la bascule ». La documentation dit l'inverse : la fonction est **réservée
aux dépôts d'organisation**. L'owner avait tranché sur cette prémisse fausse, et l'arbitrage a dû
être rouvert. ⇒ **aucune capacité GitHub n'est écrite dans un fichier public sans sa ligne ici** :
l'URL, la phrase **exacte**, la date de lecture.

**Méthode de lecture** : `curl -sS -L 'https://docs.github.com/api/article/body?pathname=/en/<chemin>'`
(le corps Markdown **rendu** de la page, variables de gabarit résolues — ⛔ pas la source brute du
dépôt `github/docs`, dont les `{% data reusables %}` ne sont pas résolus). Pages relues le
**2026-09-13 entre 11:39 et 11:44 (+02:00)**, copies sous le scratchpad de session (éphémères) ;
la phrase est recopiée **telle que rendue**, numéro de ligne de la copie entre crochets. Les
mesures d'API ont été jouées le même jour, jeton `gh` de l'owner (portées `repo`, `workflow`,
`user`, `read:org`, `gist`), ⛔ aucune écriture.

Préfixe des URL : `https://docs.github.com/en/`.

---

## 1. Formulaires d'issues — lus par `.github/ISSUE_TEMPLATE/*.yml` et par `tools/verif_reception_dn85.py` (c2)

| capacité / règle | URL (préfixe omis) | phrase exacte |
|---|---|---|
| emplacement des formulaires | `communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository` | [50] « To use an issue form in your repository, you must create a new file and add it to the `.github/ISSUE_TEMPLATE` folder in your repository. » |
| clés de tête obligatoires | `…/syntax-for-issue-forms` | [95] « All issue form configuration files must begin with `name`, `description`, and `body` key-value pairs. » |
| `name` unique | `…/syntax-for-issue-forms` | [107] « A name for the issue form template. Must be unique from all other templates, including Markdown templates. » |
| `name` > 3 caractères | `…/configuring-issue-templates-for-your-repository` | [130] « The `name` field must be more than 3 characters. If it's not, the template won't be shown when creating an issue. » |
| clés de tête permises | `…/syntax-for-issue-forms` | [107-116] table : `name`, `description`, `body` (Required) · `assignees`, `labels`, `title`, `type`, `projects` (Optional) |
| `labels` | `…/syntax-for-issue-forms` | [111] « Labels that will automatically be added to issues created with this template. If a label does not already exist in the repository, it will not be automatically added to the issue. » |
| types d'éléments | `…/syntax-for-githubs-form-schema` | [55] « `type` — The type of element that you want to define. » Valeurs : `checkboxes`, `dropdown`, `input`, `markdown`, `textarea`, `upload` |
| clés d'élément | `…/syntax-for-githubs-form-schema` | [55-58] `type`, `id`, `attributes`, `validations` |
| `id` | `…/syntax-for-githubs-form-schema` | [56] « The identifier for the element, except when `type` is set to `markdown`. Can only use alpha-numeric characters, `-`, and `_`. Must be unique in the form definition. » |
| `markdown` ⇒ `value` | `…/common-validation-errors-when-creating-issue-forms` | [346] « One of the required `value` attributes has not been provided. The error occurs when a block does not have an `attributes` key or does not have a `value` key under the `attributes` key. » |
| `label` des champs de saisie | `…/common-validation-errors-when-creating-issue-forms` | [411] « If the attribute is required, the value must be a non-empty string. » (section *label must be a string*, [372]) |
| type inconnu | `…/common-validation-errors-when-creating-issue-forms` | [322] « One of the body blocks contains a type value that is not one of the permitted types. » |
| ≥ 1 élément non-markdown | `…/common-validation-errors-when-creating-issue-forms` | [97] « A `markdown` element is static text, so a `body` array cannot contain only `markdown` elements. » |
| `id` uniques | `…/common-validation-errors-when-creating-issue-forms` | [124] « If using `id` attributes to distinguish multiple elements, each `id` attribute must be unique. » |
| labels uniques | `…/common-validation-errors-when-creating-issue-forms` | [158] « When there are multiple `body` elements that accept user input, the `label` attribute for each user input field must be unique. » |
| `options` non vides et distinctes | `…/syntax-for-githubs-form-schema` | [196] « An array of options the user can choose from. Cannot be empty and all choices must be distinct. » |
| « None » réservé | `…/common-validation-errors-when-creating-issue-forms` | [561] « "None" is a reserved word in an `options` set because it is used to indicate non-choice when a `dropdown` is not required. » |
| booléens YAML | `…/common-validation-errors-when-creating-issue-forms` | [596] « There are a number of English words that become processed into Boolean values by the YAML parser unless they are wrapped in quotes. For dropdown `options`, all items must be strings rather than Booleans. » · [89-91] clés interdites `y`, `yes`, `on`, `true`, `false`… |
| `render` | `…/syntax-for-githubs-form-schema` | [117] « If a value is provided, submitted text will be formatted into a codeblock. » |
| **`validations.required` — PUBLIC SEULEMENT** | `…/syntax-for-githubs-form-schema` | [125] « Prevents form submission until element is completed. **Only for public repositories.** » |
| mots interdits dans un label (⛔ liste non publiée) | `…/common-validation-errors-when-creating-issue-forms` | [475] « some words commonly used by attackers are not permitted in the `label` of input or textarea elements. » ⇒ **aveuglement de la gate**, la liste n'est pas écrite |
| `config.yml` | `…/configuring-issue-templates-for-your-repository` | [143] « You can customize the issue template chooser that people see when creating a new issue in your repository by adding a `config.yml` file to the `.github/ISSUE_TEMPLATE` folder. » |
| `blank_issues_enabled` | idem | [145] « When `blank_issues_enabled` is set to `false`, users with write access or above (Write, Maintain, or Admin roles) will still see the **Blank issue** option » |
| `contact_links` | idem | [147] « If you prefer to receive certain reports outside of GitHub, you can direct people to external sites with `contact_links`. » [152-159] exemple : `name`, `url`, `about` |
| le lien `?template=` | `issues/tracking-your-work-with-issues/using-issues/creating-an-issue` | [152] « The `template` query parameter works with templates stored in an `ISSUE_TEMPLATE` subdirectory within the root, `docs/` or `.github/` directory in a repository. » |

**Mesuré** : `gh api repos/nasbarok/desknode/labels --jq '.[].name'` ⇒ `accessibility`, `bug`,
`documentation`, `duplicate`, `enhancement`, `good first issue`, `help wanted`, `invalid`,
`question`, `wontfix` ⇒ les labels `bug` et `enhancement` que posent les deux formulaires
**existent** (sinon [111] : ils ne seraient pas ajoutés, en silence).

## 2. Modèle de pull request

| capacité | URL | phrase exacte |
|---|---|---|
| `.github/pull_request_template.md` | `communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository` | [24] « To store your file in a hidden directory, name the pull request template `.github/pull_request_template.md`. » |

## 3. `SECURITY.md` et `CODE_OF_CONDUCT.md` — emplacements reconnus

| capacité | URL | phrase exacte |
|---|---|---|
| ordre de recherche d'un code de conduite | `communities/setting-up-your-project-for-healthy-contributions/adding-a-code-of-conduct-to-your-project` | [63] « GitHub looks for a code of conduct in the `.github` directory, then the root of the repository, then the `docs` directory, and uses the first file it finds. » |
| fichiers de santé communautaire, dont `SECURITY.md` | `communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file` | [44] « A SECURITY file gives instructions on how to report a security vulnerability in your project » · [11-15] ordre de précédence : « The `.github` folder », la racine, « The `docs` folder » |
| contenu d'une politique de sécurité | `code-security/getting-started/adding-a-security-policy-to-your-repository` | [13] « In the new `SECURITY.md` file, add information about supported versions of your project and how to report a vulnerability. » |

⚠️ La ligne [11-15] du fichier de santé communautaire décrit l'ordre des **fichiers par défaut**
d'un compte ; pour `CODE_OF_CONDUCT.md`, la phrase [63] le dit **du dépôt lui-même**. Pour
`SECURITY.md`, aucune page lue ne dit « GitHub cherche `SECURITY.md` à la racine » en toutes
lettres pour un dépôt : l'emplacement racine est **étayé** par [44] + [11-15], ⛔ pas cité mot pour
mot — et le profil communautaire, qui le dirait, ⛔ ne se relève qu'après une poussée (ledger, `dn8-8`).

## 4. Signalement privé de failles (*private vulnerability reporting*) — lu par `SECURITY.md`, `config.yml`

| capacité | URL | phrase exacte |
|---|---|---|
| **public seulement** | `code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository` | [3] « Owners and administrators of **public repositories** can allow security researchers to report vulnerabilities securely in the repository by enabling private vulnerability reporting. » |
| le bouton | idem | [19] « When private vulnerability reporting is enabled, security researchers see a **Report a vulnerability** button on the repository’s "Advisories" page, which allows them to submit a private report. » |
| privé, vers les mainteneurs | `code-security/how-tos/report-and-fix-vulnerabilities/report-privately` | [3] « Some public repositories configure security advisories so that anyone can report security vulnerabilities directly and privately to the maintainers. » |
| distinct de `SECURITY.md` | idem | [10] « Private vulnerability reporting is separate from a repository’s `SECURITY.md` file. You can only report vulnerabilities privately for repositories where this feature is enabled » |
| le geste du rapporteur | idem | [20] « Click **Report a vulnerability** to open the advisory form. » |

**Mesures du 2026-09-13 (11:41)** :

```
$ curl -sS -o /dev/null -w '%{http_code} -> %{redirect_url}\n' https://github.com/sindresorhus/got/security/advisories/new
302 -> https://github.com/login?return_to=https%3A%2F%2Fgithub.com%2Fsindresorhus%2Fgot%2Fsecurity%2Fadvisories%2Fnew
$ gh api repos/sindresorhus/got/private-vulnerability-reporting
{"enabled":true}
$ gh api repos/nasbarok/desknode/private-vulnerability-reporting
{"message":"Not Found","documentation_url":"https://docs.github.com/rest","status":"404"}gh: Not Found (HTTP 404)
$ gh api repos/nasbarok/desknode --jq '.owner.type, .visibility'
User
private
```

⇒ **le rapporteur doit être CONNECTÉ** : sans session, l'URL du formulaire rend **302 vers la
page de connexion** sur un dépôt **d'utilisateur** public où la fonction est active (`got`,
`{"enabled":true}`). ⚠️ C'est une **mesure sur un tiers**, ⛔ pas une phrase de la documentation :
elle se rejoue sur `nasbarok/desknode` à la bascule (ledger, `dn8-8`). ⇒ sur `desknode`, **privé**,
la lecture du réglage rend **404** — cohérent avec [3] « public repositories », ⚠️ sans que l'API
nomme la cause.

## 5. Conduite — ce que GitHub offre à un dépôt **d'utilisateur**, et ce qu'il ⛔ n'offre pas

| capacité | URL | phrase exacte |
|---|---|---|
| 🔴 **reported content : ORGANISATIONS SEULEMENT** | `communities/moderating-comments-and-conversations/managing-how-contributors-report-abuse-in-your-organizations-repository` | [5] « You can enable or disable reported content for public repositories **owned by an organization**. » |
| idem, côté API | `rest/metrics/community` | [21] « content_reports_enabled is only returned for organization-owned repositories. » |
| *Report abuse to GitHub Support* | `communities/maintaining-your-safety-on-github/reporting-abuse-or-spam` | [39] « In the upper-right corner of the issue or pull request, click …, then click **Report content**. » [42-43] « You may see options to **Report to repository admins** or **Report abuse to GitHub Support**. If not, skip to the next step. · To report the content to GitHub Support, click **Report abuse to GitHub Support**. » [60] même geste sur un commentaire |
| signaler un utilisateur | idem | [18] « In the left sidebar, below the user's profile information, click **Block or Report**. » [21-22] « Click **Report abuse**. · Complete the contact form to tell GitHub Support about the user's behavior » |
| conditionnel du signalement aux mainteneurs | idem | [11] « If reported content is enabled for a public repository, you can also report content directly to repository maintainers. » |
| masquer un commentaire | `communities/moderating-comments-and-conversations/managing-disruptive-comments` | [7] « Organization moderators and anyone with write access to a repository, can hide comments on issues, discussions, pull requests, and commits. » [9] « Hidden comments are minimized but people with read access to the repository can expand them. » |
| éditer un commentaire | idem | [33] « Anyone with write access to a repository can edit comments on issues, discussions, pull requests, and commits. » [39] « anyone with read access to a repository can view a comment's edit history. » |
| supprimer un commentaire | idem | [61] « Anyone with write access to a repository can delete comments on issues, discussions, pull requests, and commits. » |
| verrouiller une conversation | `communities/moderating-comments-and-conversations/locking-conversations` | [3] « Repository owners and collaborators, and people with write access to a repository, can lock conversations on issues, pull requests, and commits permanently or temporarily to defuse a heated interaction. » |
| bloquer un utilisateur | `communities/maintaining-your-safety-on-github/blocking-a-user-from-your-personal-account` | [3] « You can block a user to deny them access to your activity and repositories, and to prevent them from sending you notifications. » [45-49] « In repositories you own, blocked users also cannot: Open issues · Send, close, or merge pull requests · Comment on issues, pull requests, discussions, or commits » |
| se protéger soi-même | idem | [30-33] « After you've blocked a user, they cannot: Send you any notifications, including by @mentioning your username · Comment on or edit issues or pull requests that you've created » |
| **limites d'interaction — public seulement, par CATÉGORIE d'utilisateurs** | `communities/moderating-comments-and-conversations/limiting-interactions-in-your-repository` | [3] « You can temporarily enforce a period of limited activity for certain users on a public repository. » [9] « you can choose a duration for the limit: 24 hours, 3 days, 1 week, 1 month, or 6 months. » [13-15] trois types : *existing users* · *prior contributors* · *repository collaborators* |

**Mesures du 2026-09-13 (11:41)** :

```
$ gh api repos/nasbarok/desknode/interaction-limits
{"message":"Server Error","errors":"Interaction limits are not available for private repositories.", … "status":"405"}
$ gh api repos/github/docs/community/profile --jq '.content_reports_enabled'
true
$ gh api repos/sindresorhus/got/community/profile --jq 'has("content_reports_enabled")'
false
```

⇒ **aucun des outils de la table n'est un canal privé vers le mainteneur** : *Report abuse* va à
**GitHub Support** ; masquer, éditer, supprimer, verrouiller, bloquer et limiter sont des gestes
**du mainteneur**, ⛔ des moyens de le joindre. ⚠️ Les limites d'interaction s'appliquent à une
**catégorie** d'utilisateurs, ⛔ à une personne : il n'existe **aucun** « bannissement temporaire
d'une personne » pour un dépôt d'utilisateur — `CODE_OF_CONDUCT.md` le dit.

## 6. La licence du Contributor Covenant 2.1 — lue dans l'historique de sa source

⛔ **Le texte 2.1 ne porte AUCUNE mention de licence** : le fichier officiel re-téléchargé le
2026-09-13 (`https://www.contributor-covenant.org/version/2/1/code_of_conduct/code_of_conduct.md`,
HTTP 200) est **identique octet pour octet** à la copie de la passe 2 du cadrage (`cmp` sans
sortie), et sa section *Attribution* ne nomme aucune licence. ⇒ la licence se lit **dans le dépôt
source**.

> ⚠️ **ANNOTÉ LE 2026-09-13 APRÈS REVUE — LA PREUVE CI-DESSUS NE PROUVAIT PAS CE QU'ELLE SEMBLAIT
> PROUVER, ET ELLE EST ⛔ NON EFFACÉE.** « Identique octet pour octet » comparait **deux copies
> téléchargées du site en 2026** : elle dit que le site n'a pas bougé entre la passe 2 et cette
> passe, ⛔ que le texte adapté est celui **publié pendant la période CC BY**. ⇒ comparaison
> rejouée contre le fichier **au tag `2.1`** du dépôt source (commit `8a3be13`, 2021-07-30), où
> le `LICENSE.md` du même tag est bien **CC BY 4.0** :
>
> ```
> $ gh api 'repos/EthicalSource/contributor_covenant/git/trees/2.1?recursive=1' --jq '.tree[].path' | grep version/2/1
> content/version/2/1
> content/version/2/1/code_of_conduct.md
> $ gh api 'repos/EthicalSource/contributor_covenant/commits/2.1' --jq '[.sha, .commit.committer.date] | @tsv'
> 8a3be1350b07f38b53bbc7073f765a48c4c53ce1	2021-07-30T18:09:11Z
> $ gh api 'repos/EthicalSource/contributor_covenant/contents/LICENSE.md?ref=2.1' --jq .content | base64 -d | head -1
> ### Creative Commons Attribution 4.0 International Public License
> $ gh api 'repos/EthicalSource/contributor_covenant/contents/content/version/2/1/code_of_conduct.md?ref=2.1' --jq .content | base64 -d > cc21-tag21.md
> tag 2.1 : 5 541 o (en-tête TOML `version = "2.1"` + texte coupé à ~80 colonnes)
> site    : 5 480 o (texte en lignes longues, sans en-tête)
> normalisation : en-tête TOML `+++…+++` retiré, blancs repliés en un espace
> tag 2.1 normalisé : 5442 car. sha256[:16] 72edb718cd7c7efe
> site    normalisé : 5442 car. sha256[:16] 72edb718cd7c7efe
> IDENTIQUES apres normalisation — diff mot a mot : 0 operation
> ```
>
> ⇒ **le texte dont part `CODE_OF_CONDUCT.md` est, mot pour mot, celui du tag `2.1`, publié sous
> CC BY 4.0** ; seuls diffèrent la coupe des lignes et l'en-tête du générateur de site. Joué le
> 2026-09-13 à 14:21 (+02:00).
> ⚠️ **Et l'URI de la licence manquait** : CC BY 4.0 § 3(a)(1)(C) demande l'URI ou le texte.
> `CODE_OF_CONDUCT.md` et `THIRD-PARTY.md` portent désormais
> `https://creativecommons.org/licenses/by/4.0/`.

```
$ gh api 'repos/EthicalSource/contributor_covenant/commits?path=LICENSE.md&per_page=100' \
    --jq '.[] | [.sha[0:7], .commit.author.date, .commit.message[0:100]] | @tsv'
e0324b3	2025-07-21T18:21:23Z	Site redesign, update to v3
91532d8	2022-01-10T16:28:25Z	Update LICENSE.md
519ee05	2016-10-28T22:27:08Z	Update and rename LICENSE to LICENSE.md

$ for s in 519ee05 91532d8 e0324b3; do gh api "repos/EthicalSource/contributor_covenant/contents/LICENSE.md?ref=$s" --jq .content | base64 -d | head -1; done
### Creative Commons Attribution 4.0 International Public License      # @ 519ee05
### Creative Commons Attribution 4.0 International Public License      # @ 91532d8
HIPPOCRATIC LICENSE                                                    # @ e0324b3

$ gh api 'repos/EthicalSource/contributor_covenant/releases?per_page=30' --jq '.[] | [.tag_name, .published_at] | @tsv'
2.1	2021-08-04T13:57:54Z
2.0	2020-06-25T00:22:58Z
1.4	2016-01-30T22:06:18Z
```

⇒ la **version 2.1 est publiée le 2021-08-04**, dans la fenêtre où le `LICENSE.md` du dépôt source
est **CC BY 4.0** (2016-10-28 → 2025-07-21, relu à `91532d8` du 2022-01-10). ⇒ l'adaptation
`CODE_OF_CONDUCT.md` part d'un texte **CC BY 4.0**, et se publie sous **CC-BY-SA-4.0**, la licence
que `LICENSING.md` donne déjà au Markdown racine. ⚠️ **Limite écrite** : la licence d'un dépôt
s'applique au contenu de ce dépôt ; le texte de la version 2.1 **servi par le site** en est tiré,
⛔ mais aucun des deux ne l'écrit dans le fichier lui-même.

## 6 bis. Les espaces que CE dépôt a — lus par `CODE_OF_CONDUCT.md` (*Scope*) et `SECURITY.md`

*Ajouté le 2026-09-13 après revue : le code de conduite nommait des « discussions » et des
« wiki edits », et `SECURITY.md` interdisait une « discussion », dans un dépôt qui n'a ni l'un ni
l'autre.*

```
$ gh api repos/nasbarok/desknode --jq '{has_discussions, has_wiki, has_issues, has_projects}'
{"has_discussions":false,"has_issues":true,"has_projects":true,"has_wiki":false}
```

Mesuré le 2026-09-13 à 14:14 (+02:00). ⇒ les deux fichiers ne nomment plus que les issues, les
pull requests, les commits, les commentaires et les avis de sécurité.

## 7. Ce que CE fichier ⛔ ne couvre pas

- ⛔ **La validation réelle de GitHub** : [475] parle de mots interdits **non listés**, et le
  rapprochement des labels « trop proches » n'est décrit que par l'exemple. La gate garde les
  **règles écrites** ; le reste attend une poussée (ledger, `dn8-8`).
- ⛔ **Le rendu du sélecteur d'issues, l'effet de `required`, le profil communautaire non nul** :
  tous exigent un dépôt **public** et poussé.
- ⛔ **L'activation du signalement privé** : réglage d'un dépôt public, geste de la bascule.

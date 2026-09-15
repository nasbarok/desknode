# DeskNode Contributor License Agreement

*Version 1, 2026-09-02.*

*Version 2, 2026-09-14. **Version 1 was never signed**: on 2026-09-14 the signature record,
`.github/cla-signatures.json`, was read and held no signature at all
(`{"signedContributors": []}`), so this revision changes nobody's consent. Version 2 keeps
every word of version 1 and adds five things: who "the project owner" is, a term saying that
no governing law and no jurisdiction are chosen, what the signature record keeps and that it
is public, the fact that a recorded signature stays in the history of this repository, and
the fact that the bot links a fixed revision of this text, unlike the pull request template.*

Thank you for wanting to contribute. This page is the agreement a bot asks you to
accept the first time you open a pull request. It is short on purpose, and this first
section says plainly what it is for before the terms start.

## Why this exists, in one paragraph

DeskNode is GPL-3.0-or-later for the firmware, MIT for the agent, CC-BY-SA-4.0 for the
documentation — see [`LICENSING.md`](LICENSING.md). If every contributor keeps sole
copyright on their own patch, then **the licensing of this project is frozen the moment
the first outside contribution is merged**: changing it later would require finding and
convincing every past contributor. That would rule out, in particular, a commercial
arrangement with a manufacturer, which is a door this project deliberately keeps open.
This agreement keeps that door open. **It does not take your copyright away** — you
keep it, and you keep the right to use your own work however you like, anywhere else.

## Terms

By submitting a contribution to this repository, you agree to the following.

*Added in version 2:* in these terms, **"the project owner" means Nasbarok** — the author
and maintainer of DeskNode, and the copyright holder named in [`LICENSING.md`](LICENSING.md).
Wherever the terms below grant a license to the project owner, it is granted to that
person, and it is a license: nothing in these terms is an assignment.

1. **You keep your copyright.** Nothing here assigns or transfers it.

2. **Copyright license.** You grant the project owner a perpetual, worldwide,
   non-exclusive, royalty-free, irrevocable license to reproduce, modify, publicly
   display, sublicense and distribute your contribution and works derived from it,
   **including under a different license than the one that applies today**. This is the
   clause that keeps relicensing possible.

3. **Patent license.** You grant the project owner and the recipients of the software a
   perpetual, worldwide, non-exclusive, royalty-free, irrevocable patent license to
   make, use, sell, offer for sale, import and otherwise transfer your contribution,
   covering only the patent claims you own or control that are necessarily infringed by
   your contribution alone or by its combination with this project.

4. **You have the right to grant this.** Your contribution is your original work, or you
   have the right to submit it under these terms. If your employer has rights to work
   you produce, you have permission to make this contribution on your own behalf, or
   your employer has waived those rights for it.

5. **Third-party material is declared.** If your contribution includes anything you did
   not write, you say so and you name its license, so it can be recorded in
   [`THIRD-PARTY.md`](THIRD-PARTY.md).

6. **No warranty.** You provide your contribution "as is", without warranty of any kind,
   express or implied.

7. **No governing law and no jurisdiction are chosen.** *(Added in version 2.)* This
   agreement names neither a law that governs it nor a court that would hear a dispute
   about it. That absence is deliberate, and it is written here so that it is not read as
   an oversight.

## How you accept it

A bot comments on your first pull request with a link to this page. Replying to that
comment with the sentence it gives you records your signature — there is nothing to
print, sign or e-mail. The record is kept in this repository, in
`.github/cla-signatures.json`, and one signature covers all your future pull requests.

*Added in version 2:* **that record is public**, like everything else in this repository,
and the bot writes it by a commit on the `main` branch. For each signature it keeps
**six fields**, and nothing else:

- `name` — your GitHub login;
- `id` — the numeric id of your GitHub account;
- `comment_id` — the id of the comment you signed with;
- `created_at` — when that comment was posted;
- `repoId` — the numeric id of this repository;
- `pullRequestNo` — the number of the pull request you signed on.

It keeps no e-mail address, and it does not record which version of this text you
accepted. This repository does not rewrite its history, so once a signature has been recorded
it stays there, in the history, even if the record file changes later. **The link the bot posts names a fixed revision of this text** — a commit, not
the tip of a branch — so the text behind that link stays the one you read when you signed.
The link in the pull request template is different: it shows the current text on `main`, which
is where a later version would appear; the text you sign is the one behind the bot's link,
which names a commit.

If you would rather not agree to this, say so on the pull request. Reporting a bug,
opening an issue and discussing a design need no agreement at all — this applies only to
code and content you ask to have merged.

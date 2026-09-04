# What the markers mean

Files in this repository sometimes say that something is *"tracked as `dn8`"* or
*"tracked separately (`dn4-39`)"*. This page says what those markers are, so that a
marker you are pointed at is one you can look up.

It exists because of a rule this repository broke once and now states out loud, in
[`CONTRIBUTING.md`](../CONTRIBUTING.md) § *Conventions in this repository*:
**nothing that is pushed lies**, and anything that cannot be fixed before a push is
written down *with the marker that will fix it*. A marker the reader cannot resolve
is only half of that promise.

## Where the markers come from — and what you cannot see

DeskNode is planned in a separate, **unpublished** working repository. Each marker is
a key in that plan: `dnE-N` is story *N* of epic *E*, and `dnE` on its own is a whole
epic. **The plan itself is not part of this clone and there is no schedule in it that
would be worth publishing** — what follows is the meaning of each marker and its
state, not a commitment to a date.

⚠️ **This page is not the changelog and not the history.** It lists only the markers
that name work **still to come**. Markers that name *past* work — most of `dn1-*`,
`dn2-*`, `dn3-*` and `dn4-*`, which appear throughout [`README.md`](../README.md) and
[`dn4-15-arbitrage.md`](dn4-15-arbitrage.md) — are described where they are cited;
they are the engineering log, and this page does not duplicate it.

⚠️ **Amended on 2026-09-04, and the sentence above is kept rather than replaced.** A
marker that is *cited in this tree* stays listed here **after it closes**, with the state
`done`, instead of vanishing: a marker you are pointed at must remain one you can look
up, and that promise does not expire the day the work does. What the paragraph above
still rules out is unchanged — a marker nobody cites here does not get a row just because
it exists. ⇒ the admission rule is **"cited in this tree"**, ⛔ not "not finished yet".

🔴 **How to read the `state` column — this is a rule, ⛔ not a promise of freshness.** The
authority on any state is the unpublished plan, ⛔ never this page: this column is a
**snapshot, refreshed when the work that changes a marker also passes through here**. It
was wrong three times at once on 2026-09-04 (see the rows below), which is why the rule is
now written instead of assumed. ⛔ If a row disagrees with something else in this tree,
the row is the one to doubt.

## The markers cited in this tree

| marker | what it covers | state |
|---|---|---|
| `dn4-5` | Long-running soak of the agent module on its own. | in progress |
| `dn4-39` | Making the repository's gates run **without anyone having to think about it**. ✅ Done on 2026-09-02: `.github/workflows/gates.yml` runs `bash tools/run_gates.sh` on every push and every pull request, and the six gates that cannot be exercised on a runner are **declared** with their reason, a witness path and an exact expected exit code — ⛔ not silenced. ⚠️ One piece of it is **not** covered and it is not a CI matter: the generated table in the private planning repository is regenerated **at the workstation**, because that repository is never cloned — that part is carried by `dn5-5`, ⛔ it does not keep this marker open. *(Reworded on 2026-09-04 at the code review: it read "⚠️ **Still open**, …", which left the cell saying `done` and "still open" at the same time — the very contradiction the correction beside it had just claimed to remove. The earlier wording is named here rather than erased.)* ⚠️ **State corrected on 2026-09-04 (`dn5-4`): this row read `in review`, and the marker had been closed on 2026-09-02.** The sentence above already said "Done on 2026-09-02", so this page contradicted itself in a single cell. ⛔ Note the earlier wording was *"`tools/run_gates.sh` exists and works; nothing invokes it automatically."* — the **first half stays true** (the script exists and works, and it is still the manual command); it is the **second half** that changed. *(Restored at the code review of 2026-09-02: the first clause had been dropped rather than annotated, which §14 of the story forbids.)* | done |
| `dn4-40` | Stopping gates from passing on nothing, and anchoring their manifests **by pattern instead of by line number**. ⚠️ **State corrected on 2026-09-04 (`dn5-4`): this row read `not started`, and the marker had in fact been closed.** ⛔ The earlier wording is kept above rather than replaced. One acceptance criterion did not close with it and was handed on rather than dropped — it is carried by `dn4-44`, whose own work armed it. | done |
| `dn4-41` | The board on its own is enough — the two hardware tiers behave correctly without the ambient sensors. | in progress |
| `dn4-42` | The display speaks two languages. | in review |
| `dn7` | The install side: the browser flasher, a packaged agent you do not have to run from source, and **the language chosen at install time** rather than on the panel. | not started |
| `dn5-4` | The firmware builds in a **fresh directory**, from a clean clone. ⚠️ **State corrected on 2026-09-04, by that work itself: this row read `not started` while the marker was under way** — the commit carrying this correction is the same one that adds the cold-build measurements and the *Building the firmware* section of [`CONTRIBUTING.md`](../CONTRIBUTING.md). ⚠️ **Corrected again on 2026-09-04 at the code review, and the reason is worth more than the value:** the correction above wrote `in progress` while the plan already read `review`, and this page **distinguishes the two** (see `dn4-42`). A state written for the moment of writing is stale by the time it is pushed; what is written now is the state the marker has **in the commit that publishes this line** — and the review that produced this correction closed the marker in the same gesture, so it lands here as `done`. | done |
| `dn4-44` | **No new check ships without a mutant that replants the fault it guards against** — a rule about the repository's own gates, not about the firmware. It armed the acceptance criterion that `dn4-40` handed on. | done |
| `dn4-45` | **Building the firmware in CI.** Deliberately out of scope for `dn5-4`, which measured what it would cost: a runner would install ESP-IDF v5.5.5 (**3.84 GiB**, 23 submodules) and its toolchains (**4.30 GiB**), then pull **172.5 MiB** of components — against a workflow that today runs on `ubuntu-latest` with a 20-minute timeout and no `pip install` at all. 🔴 And one measured fact decides more than the sizes: **a cold build needs the network, and no local archive cache replaces it** (`dependencies.lock` is gitignored, so a fresh clone must *solve*, and solving queries the registry). | not started |
| `dn5-5` | The clone states its own size, and everything still missing before a public release has a named owner. | not started |
| `dn8` | The public face: splitting the long French `README.md` into a short front page plus an engineering log, a version **shown on the device**, a release tag, the templates needed to receive issues and pull requests, and **proving the CLA bot against a real outside contributor** — which cannot happen while the repository is private and has no fork. | epic opened, **no stories written yet** |

⚠️ **`dn8` is the least defined entry here, and that is stated rather than dressed
up.** It is an open epic with no stories behind it: when `CONTRIBUTING.md` says a
version displayed on the device is "still to come", `dn8` names *where that work will
live*, not work that is under way.

## What is already known to be wrong, and where it is written

The gap between what this repository **asks of you** and what it **can currently
do** was measured and written down before the code was published. It is in
[`dn5-1-ecart-promesses.md`](dn5-1-ecart-promesses.md) — six entries, each with the
marker that carries it. That page is in French; it is part of the engineering log,
and splitting the two is itself part of `dn8`.

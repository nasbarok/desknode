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

## The markers cited in this tree

| marker | what it covers | state |
|---|---|---|
| `dn4-5` | Long-running soak of the agent module on its own. | in progress |
| `dn4-39` | Making the repository's gates run **without anyone having to think about it**. `tools/run_gates.sh` exists and works; nothing invokes it automatically. | not started |
| `dn4-40` | Stopping gates from passing on nothing, and anchoring their manifests **by pattern instead of by line number**. | not started |
| `dn4-41` | The board on its own is enough — the two hardware tiers behave correctly without the ambient sensors. | in progress |
| `dn4-42` | The display speaks two languages. | in review |
| `dn5-2` | Making the repository keep the promises it **already published**: licensing, `THIRD-PARTY.md`, the CLA bot that `CONTRIBUTING.md` mentions but that does not exist, and the `CHANGELOG.md` claim about NVIDIA GPUs that the agent code refutes. | not started |
| `dn5-3` | Removing every remaining dependency on the author's own machine, and declaring the ones that only *name* it. Four tools under `tools/` reach **outside the clone**, to absolute paths that exist only on the author's machine — so they cannot work from a clone anywhere else. One of them, `tools/bench_lisseur_dn45.py`, already fails outright: `ModuleNotFoundError: No module named 'dn_agent'`. | not started |
| `dn5-4` | The firmware builds in a **fresh directory**, from a clean clone. | not started |
| `dn5-5` | The clone states its own size, and everything still missing before a public release has a named owner. | not started |
| `dn8` | The public face: splitting the long French `README.md` into a short front page plus an engineering log, a version **shown on the device**, a release tag, and the templates needed to receive issues and pull requests. | epic opened, **no stories written yet** |

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

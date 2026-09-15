# Changelog

All notable changes to DeskNode are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- 🆕 **The purchase list speaks English, and it carries its affiliate links** (`dn6-6`, 2026-09-15).
  Measured that day: the front page sends "What to buy" to `docs/bom.md`, which was written entirely
  in French, and its five AliExpress addresses were bare search pages. What changed, on owner
  decisions of the same day. (1) `docs/bom.md` is translated into English, **as a single page** —
  every section, table and dated annotation, with the same prices, dates, the ten addresses tried
  and the six photo links; the French text now lives in the history only. (2) The five AliExpress
  rows carry, in their `Source` cell, a tracked link of the AliExpress affiliate programme generated
  by the owner from the very search page where the price was read, with the words
  `affiliate link` right beside it. (3) The original status sentence of the page is kept,
  translated, and the declaration in force is written below it; `docs/affiliation.md` stays in
  French and annotates every sentence that went stale, with the programme terms the owner read on
  its portal — the tracking window is written nowhere in them — and **two** Waveshare readings of
  the same day that disagree, both written and neither settled. The manufacturer price sentence
  that was refuted on 2026-09-07 is annotated as refuted, ⛔ not re-surveyed.
  ⚠️ **What did ⛔ not happen, written**: no Waveshare link is published (the application is waiting
  for approval), no sponsor button exists, and the destination of each tracked link was ⛔ not
  opened by the agent that wrote it — a click is counted by the programme, so checking them once is
  the owner's gesture.
- 🆕 **The affiliation check guards the new commitment instead of the old one** (`dn6-6`, 2026-09-15).
  `tools/verif_affiliation_dn65.py` had written its control `(c5)` — *no published address is
  marked* — as a commitment, and named its own remedy. It is applied in the same change as the
  links: `(c5)` now requires every marked address of the tracked text files to live in
  `docs/bom.md`, in a cell that carries the mention; the new `(c24)` requires every mention in a
  table of that page to sit on a marked address; `(c6)` reads the purchase page in English and the
  affiliation page in French. A redirector host such as the programme's click tracker counts for
  its parent domain, so the survey still covers **two** domains. `tools/verif_bom_dn61.py` and
  `tools/verif_cablage_dn62.py` read the English page; a table retranslated into French stops
  declaring itself and is named. Twelve new mutants in the affiliation check replant a marked link
  outside the purchase page, a link without its mention, a mention on a bare address, links removed
  while both pages still declare them, a survey row given to the redirector itself, an unqualified
  threshold, an English tier amount, a mention turned into "no affiliate link", a mention moved to
  another cell of the row, a tracked link beside a link to the affiliate links page, a euro amount
  written before the number, and a thousands separator written with a comma; two new mutants in the
  purchase-list check replant a French date header and a milestone with an English decimal. Each
  one is seen red on the control it names.
  🔍 *Reviewed on 2026-09-15 (four layers)*: the review found that six of those branches, one
  exception and two vocabulary gaps were guarded by nothing, that a stale mutant of the
  purchase-list check still counted as healthy, and that the translation had changed the meaning of
  a few sentences; all of it is fixed in the same step, and what the review raised without fixing
  is written in the planning ledger.
- 🆕 **The repository is public, and what that makes possible** (`dn8-8`, 2026-09-15).
  Measured on 2026-09-14, before anything was pushed: the repository was private, with 0 forks and 0
  stars, `main` on GitHub was 59 commits behind, and what the release promises a stranger — the
  GPL source of the published binary, a private route for security reports, an archive to
  download — could be checked by nobody. What changed, in order. (1) What would become public was
  **inventoried first**, and the inventory is versioned under `mesures/dn8-8/` with its sensitive
  values masked: the whole history goes public **as it is**, by an owner decision of 2026-09-14,
  and ⛔ nothing was rewritten. (2) `CLA.md` is at **version 2**: it names the project owner, keeps
  the license without assignment and the right to relicense, says that no governing law and no
  jurisdiction are chosen, lists the six fields the signature record keeps and says that record
  is public. Version 1 was never signed. The bot now links that text **at a fixed commit**
  instead of the tip of `main`. (3) `main` was pushed and the repository was made public.
  (4) What is still missing for someone arriving from outside is written in `docs/roadmap.md`, as a
  curated copy of the planning list, with the rule that keeps it. The `dn8-8` row of that page
  reads `done` and describes the repository as public: like the `dn8-7` row, it is written as the
  state **once the switch is played**, a rule of reading rather than a snapshot, because the
  commit that carries it is pushed before the repository is made public.
  🔴 **`main` is deliberately not protected**: the bot records each signature with a commit on
  `main`, and on a repository owned by a personal account a branch protection rule cannot exempt
  it — the reason, and what was ⛔ not tried, are in `CONTRIBUTING.md`.
  ⚠️ **What this entry does ⛔ not assert**: the gestures played **after** this text was published —
  protecting the tag `v0.1.0-beta`, turning on private vulnerability reporting, what was actually
  read without an account, and the continuous integration run of the pushed `main`. Each
  one is written here by a dated annotation only once it has been measured, and not before.
  ✅ *Measured on 2026-09-15, once played (`mesures/dn8-8/P1-bascule.txt`):* the tag `v0.1.0-beta` is
  protected by a ruleset that blocks its deletion, its update and any non-fast-forward change, with
  nobody allowed to bypass it; private vulnerability reporting is on, read back as enabled; 15 pages,
  the 6 release assets and a clone were read **without an account** — every page answered 200, every
  asset matched its digest, the four `.bin` matched `PROVENANCE.md` and `manifest.json` its copy at
  the tag, and the clone carries `55006c1`; the archive downloaded without an account started its
  installer, which answered over HTTP, on the maintainer's machine, which already has Python; and
  the continuous integration run of the pushed `main` concluded `success`.
  ⚠️ **What this does ⛔ not provide, written**: proof that the bot records the signature of a
  real outside contributor — that waits for the first such pull request, and nobody opens one on
  purpose —; activating the agent from a downloaded copy, which stays a known issue until the
  standalone agent of V0.2; whether a stranger understands DeskNode in fifteen seconds, which only
  a stranger can say; and a release body that says the repository became public: the notes of
  `v0.1.0-beta` are annotated on `main` only, and the release does not move. The `dn8-8` row of
  `docs/roadmap.md` names the same four.
- 🆕 **The demo can be seen: a link to the video, and three animations on the front page** (`dn8-9`, 2026-09-14).
  Measured that day: the front page cited two images, no animation and no video link, and the
  repository tracked no GIF and no video file — a stranger never saw DeskNode move. What changed.
  (1) A `## Demo` section, placed right after the caption of the photos, links the 78-second demo
  video, which is hosted on YouTube, **outside this repository**. (2) Three silent GIF excerpts of
  that video live in `docs/demo/` — a touch that wakes the full view and opens the CPU detail, the
  network cell jumping past 2,000 Mb/s, and the network curve — each lighter than the ceiling the
  front-page check already set for images, and each named after the time read on the screen; the
  network detail view shows no clock, so the curve takes the time read on a neighbouring frame of
  the same shot. Their
  caption assumes what the photo caption assumes: a bare-wired prototype with no enclosure, and a
  screen in French. (3) `tools/verif_vitrine_dn84.py` read every image the front page cites as a
  JPEG, so a GIF would have turned it red: its image control now tells the two formats apart by
  their first bytes, reads a GIF block by block up to its trailer, accepts only the graphic control
  extension and the `NETSCAPE2.0` loop, each in its exact shape, and names anything else it finds.
  Eleven new mutants plant a comment extension, a foreign application extension, an oversized
  logical screen, a truncated file, a payload added to the loop, a payload added to a graphic
  control block, an oversized image, an unknown extension, a GIF with no image, a stray byte
  between blocks, and PNG magic bytes in place of GIF ones, and each one is seen red.
  ⚠️ **These animations are ⛔ not part of the `v0.1.0-beta` release**: that tag was pushed before
  them, and it does not move. ⚠️ **The video file is ⛔ not in the repository**, so the recipe that
  cut the GIFs, written under `mesures/dn8-9/`, can be replayed by the owner only.

## [0.1.0-beta] - 2026-09-14

Work towards the first public release, `v0.1.0-beta`.

> ⚠️ **Annotated on 2026-09-14 (`dn8-7`) — the line above is ⛔ not rewritten.** This section was
> `[Unreleased]` until that day, and it is now `0.1.0-beta`: a **pre-release** of a repository that
> is **still private**. ⇒ it is the first release, and ⛔ not yet a public one. Nothing below was
> back-filled: work items closed before the release keep the entries they had, and none gained one.

> ⚠️ **Annotated on 2026-09-15 (`dn8-8`) — the annotation above is ⛔ not rewritten.** "Still
> private" stopped being true after this release was published: the repository became
> public. The release itself did not move — neither its tag, nor its assets, nor its body.

### Added

- 🆕 **The first release exists, and what it distributes has a source** (`dn8-7`, 2026-09-14).
  Measured that day: `git tag` and `git ls-remote --tags origin` were both empty and the GitHub API
  listed no release — while the install page's payload was a build of 2026-09-08, made **before**
  the version appeared on the display: shipped as-is, it would have distributed a firmware that does
  not show its version. What changed. (1) The payload's `desknode.bin` is now **the build that was
  flashed and read on the development board on 2026-09-13** (`version 55006c1` under the menu
  title) — copied, ⛔ not rebuilt: three builds of the same size made that day have three different
  SHA-256. `installeur/charge/PROVENANCE.md` and `manifest.json` name revision `55006c1`, and the
  earlier values stay there as a dated quotation. (2) `v0.1.0-beta` is an **annotated tag** on the
  commit that carries this entry, pushed on its own, and a GitHub **pre-release** attaches the four
  images, `manifest.json` and `desknode-v0.1.0-beta.zip` — the **whole tree** of the tag, made by
  `git archive`, because the installer needs the rest of the repository next to it. The release
  notes are versioned in `docs/releases/v0.1.0-beta.md` and **link** to the status, the
  instructions, the known issues, this file, the licenses and the provenance instead of copying
  them. (3) The known issues are reconciled: the front page, this file and `CONTRIBUTING.md` now
  say the same thing of the cold-start window — characterised, cause **not established** — and
  *"Not perceptible in use"* and the LibreHardwareMonitor refusal carry dated annotations that cite
  their sources, below.
  ⚠️ **What this release does ⛔ not provide, written rather than implied**: a **publicly reachable
  source** — the repository is still private, so the source it names can be reached by its owner
  only; a **mechanised provenance** — the binaries are built by hand and no CI builds this firmware
  (`dn4-45`); and a **standalone executable** for the agent, planned for V0.2. ⚠️ **And one thing is
  not replayed**: flashing this exact binary **from the install page** — the page was proven end to
  end on the previous payload, and the 2026-09-13 session flashed this one with `idf.py`.

  > ⚠️ **Annotated on 2026-09-15 (`dn8-8`) — this entry is ⛔ not rewritten.** Its first gap has
  > closed since: the repository became public, so the source this release names — the tag, and
  > revision `55006c1` — now sits in a public repository. The other two gaps are unchanged.
- 🆕 **The repository can now receive what comes back: issue forms, a security policy, a code of
  conduct, and a status line that promises nothing** (`dn8-5`, 2026-09-13). Measured that morning:
  `.github/` held only the CLA signature store and two workflows, and GitHub's community profile
  returned `null` for the code of conduct, the issue template and the pull request template — a
  stranger had to guess how to report a bug, and a security researcher had **nowhere** to send a
  vulnerability except a public issue, which publishes it.
  What exists now. (1) `.github/ISSUE_TEMPLATE/bug_report.yml` asks for the hardware tier, the GPU,
  LibreHardwareMonitor, the firmware SHA from the boot banner, the Windows version, what happened,
  the steps and the logs; `feature_request.yml` links the status instead of repeating it; and
  `config.yml` keeps **blank issues available** (GitHub's default, and the only generic route left
  for a question: Discussions are off and there is no question form), sends security reports **out
  of the issues**, and links the code of conduct from the template chooser. (2) `.github/pull_request_template.md` points at the CLA, the license of the area
  touched, and what was run to check the change. (3) `SECURITY.md` sends vulnerabilities to
  GitHub's **private vulnerability reporting** — ⛔ no e-mail address, by owner decision. (4)
  `CODE_OF_CONDUCT.md` adapts the **Contributor Covenant 2.1** (CC BY 4.0), published under
  CC-BY-SA-4.0 with its changes listed, and credited in `THIRD-PARTY.md`. (5) The status is written
  **once**, in `CONTRIBUTING.md` § *What this project is, honestly*, completed in place: every other
  page links to it.
  🔴 **The route chosen for conduct reports, and its cost, written rather than smoothed over.**
  The original Covenant assumes a private channel to the people who enforce it. GitHub offers one —
  *reported content* — **only to repositories owned by an organization**, and this one belongs to a
  personal account. Among four options (no private channel and say so; misuse the security form;
  a dedicated address; moving the repository under an organization), the owner chose the first on
  2026-09-13. ⇒ the code of conduct **says there is no private channel to the maintainer**, sends
  anything serious to *Report abuse* (read by GitHub Support, not by the maintainer), names only the
  moderation tools a personal repository really has, and drops the three promises the original
  makes that nothing here could keep: a contact address, a quick review of every complaint, and a
  warning sent privately. ⚠️ **The cost**: someone harassed here **cannot alert the maintainer
  privately**. The text is weaker than the original, and it says so.
  A new check, `tools/verif_reception_dn85.py` (run by `tools/run_gates.sh`), **parses** the three
  YAML files with a real YAML parser, confronts the forms with the rules GitHub's documentation
  writes down, keeps delay promises and addresses out of the new files, and fails if the two-word
  status label that `CONTRIBUTING.md` carries (case and emphasis ignored) appears in any other file
  among
  the Markdown files at the root, everything under `.github/` and the top-level Markdown files of
  `docs/` (the French engineering log excepted), or if a link points at a file or a heading that
  does not exist: **16 controls, 38 mutants**, each seen red on the control it declares. ⚠️ Without PyYAML it
  fails closed rather than passing on files it did not read; PyYAML on the CI runner is supported by
  the runner image's package list, ⛔ not yet measured on a run.
  ⛔ **What waits for the switch to public** (`dn8`): whether GitHub accepts and renders the forms,
  whether `required` takes effect (it only does on public repositories), and whether the private
  reporting form reaches a stranger — that setting only exists once the repository is public, and
  turning it on belongs to the switch.

  > ⚠️ **Annotated on 2026-09-15 (`dn8-8`) — ⛔ not rewritten.** The switch happened that day: the
  > repository is public, so the first two can now be observed. The third needs the reporting
  > setting, which is turned on **after** this text is published; this annotation does ⛔ not say it
  > is on, and none of the three is recorded here as observed. Filling a form in from a second
  > account was ⛔ not done.
- 🆕 **The LHM probe's polarity is now replayed inside a real PowerShell, and the LHM port
  travels end to end** (`dn8-3`, 2026-09-12). 🔬 **The blocker was refuted by measurement, ⛔ not
  argued away.** Five ledger entries carried the same cause, word for word — *"there is ⛔ no
  PowerShell host, which the tower's WSL does not have"* — and it is **false**: `powershell.exe`
  **5.1.19041.6456** answers `rc=0` from that very WSL, execution policy is `Undefined`
  everywhere, and an **unsigned** `.ps1` runs there with its exit code honoured. 🔴 **The exact
  mechanism of the false negative**: `shutil.which("powershell")` returns **`None`** while
  `shutil.which("powershell.exe")` returns **the path**. **It was a NAME, ⛔ not an absence** —
  the same rule this repository has already paid for twice (*"NOT REACHED" is a property of the
  **method** of retrieval, ⛔ not of the address*). ⇒ the fix is **mechanised, ⛔ not a
  reminder**: the new check and its witness in `tools/run_gates.sh` try **four** names, and the
  trap is written **inside the file**.
  What changed. (1) A new check, `tools/verif_lhm_ps_dn83.py`, stages a throwaway directory
  **visible to Windows**, puts the **real** `tools/dn_agent_tour.ps1` in it next to a bench
  `dn_agent.py` whose **only** difference is the port, starts the repository's own
  `tools/stub_lhm_dn48.py`, and runs the pre-flight **in a real `powershell.exe`, both ways**:
  a monitor answering **200 with not a single `lhm_` line** ⇒ the pre-flight **refuses**; the
  real capture ⇒ it does ⛔ **not**. ⚠️ **The discriminant is *refuses* vs ⛔ *does not refuse*,
  ⛔ never *refuses* vs *succeeds*** — measured: past the LHM block the pre-flight **carries on**
  and exits on the serial port, so a bench expecting success would go red on a **healthy**
  machine. Each control is seen red under a mutant that **replants** the fault, the stub and the
  staging are closed in a `finally`, and a missing PowerShell host yields a **declared** `4`,
  ⛔ never a green. (2) The LHM port is now **passable end to end**: `-Lhm HOTE:PORT` on
  `tools/dn-agent.bat` (5th argument) and on `tools/dn_agent_tour.ps1`, reaching the agent as
  `--lhm`, carried by the logon task and **verified after it is registered**. Both tools
  previously had **zero** occurrences of the flag, while `tools/dn_lhm_tour.ps1` called a
  different port a *supported configuration* — so on a **healthy** tower whose monitor listened
  elsewhere, the pre-flight refused. A malformed value is **refused explicitly**, ⛔ never folded
  back onto the default.
  🔴 **What is still ⛔ NOT measured, written rather than left quiet.** The **real tower** is
  ⛔ untouched: ⛔ no check here installs LibreHardwareMonitor, opens a browser, or registers a
  scheduled task. A greyed-out button actually **seen**, an agent **observed alive by query**,
  the `pip` gesture's **900 s** ceiling (still ⛔ never confronted with a measurement) and the
  logon race all remain **owner-session** work, carried in the ledger with their owner.
  ⚠️ **And one measured fact shortens that session**: the tower's deployed copy sits at
  `e3064f0` (**2026-08-28**) and contains **zero** occurrences of the refusal — running the
  written protocol there as-is would measure a two-week-old product and yield a **false
  negative that nothing would flag**. The three protocols are annotated with that, ⛔ none of
  them rewritten, and their `NOT RECORDED` marker **stays**.
  ⚠️ **A premise was also refuted, and it closes nothing**: *"the tower's WSL is NATed ⇒
  localhost does not traverse"* is **false as a statement of reachability** (a server bound
  inside WSL answers **200** to a request from Windows). ⛔ That measures an **HTTP client**,
  ⛔ not a **browser**, and ⛔ above all not an **eye** — secure context, Web Serial and
  legibility remain **untouched and unmeasured**.

- 🆕 **The page's JavaScript is now executed against a real server, and five of the entry
  point's six exit codes are provoked** (`dn8-2`, 2026-09-12). 🔬 **Measured first, under
  `NODE_V8_COVERAGE`:** of the **93 functions** in the `<script>` of `installeur/index.html`,
  **21 had never been entered**, and **54 of the 141 internal blocks** of the living ones were
  never reached — while the bench reported `27 OK, 0 KO`. **The existence of a bench ⛔ is not
  coverage.** What changed. (1) `tools/banc_langue_dalle_dn73.mjs` now **asserts its DOM is not
  degenerate**, judging **values** — a mounted element's parent **is** its container, its next
  sibling **is** the container's — and it does so **before** `runInContext`, because a page reads
  those at load; the witness `--temoin-dom` replants the exact fault measured on 2026-09-10,
  when two branches of `montrerSortie()` were dead and the bench stayed green over them. (2) The
  check `tools/verif_banc_langue_dn73.py` binds the product's **real** `ThreadingHTTPServer` on
  `127.0.0.1:0`, hands the bench its address, and closes it in a `finally`; the bridge
  **imitates the browser** by sending an `Origin` on POSTs — without which the product's
  `Origin` refusal was **never** played the way the page triggers it, since node's `fetch` sends
  **none** — and each case **names the route it reached**, read from what the response carries
  rather than from the path it asked for. ⛔ No real gesture reaches the machine:
  `_powershell`, `lhm_present`, `dependance_presente` (two interpreters per call) and
  `_jouer_dependances` (which runs a real `pip install`) are replaced by paper doubles. (3) A new
  check, `tools/verif_entree_dn82.py`, **provokes** `0`, `3`, `4`, `5` and `6` by calling the
  product's own **`main()`** in a throwaway copy of `installeur/`, and reads each **by name**,
  `5` **before** `6`. ⚠️ `main()` takes ⛔ **no argument**: `sys.argv` is **set** —
  `--verifier` for `0`, `3`, `5` and `6`, and **`--sans-navigateur`** for the `4`, because
  under `--verifier` `main()` returns **before** the bind and ⛔ cannot produce it. Before this work only **four** issues of `prevol()` were played, by
  import: **`2`, `4` and `5` were played by nothing.**
  🔬 **Coverage after, measured without a server — the figure CI replays: 96/100 functions
  exercised** (4 still dead) and **131/190 blocks**. ⚠️ A figure taken *with* the real server
  is ⛔ **not published**: no **committed** caller in this repository passes `--base` to the
  relevé, so ⛔ nobody replays it.
  ⚠️ Dead blocks go from **54 of 141** to **59 of 190**, and those two counts ⛔ **do not
  subtract**: V8 only emits a function's inner blocks once it has been compiled, so the
  denominator **rises with coverage**. That is why the declared threshold (**92 functions ·
  120 blocks**) is on the **numerator**, never a ratio.
  🔴 **And the point that matters: rising coverage ⛔ does not prove a fault would be seen.** It
  is **measured**, not feared: a first attempt went from 21 dead functions to 5 **and stayed
  green over eleven real inversions** of this page. ⇒ what **judges** is elsewhere — every
  conditional display block is now observed in **both** states by a vector compared whole, and
  each of those inversions is replanted by a mutant **seen red**.
  ⚠️ **Three limits are declared rather than left quiet.** The check ⛔ does **not** run
  `cmd.exe` — the CI is Linux — so the `2` is **read in the modelled flow** of the `.bat`, not
  provoked: every label carrying a code is reached **from the head of the file**, posts **the**
  code the table declares, ⛔ no out-of-table label posts one, both `%PY%` calls relay
  `%ERRORLEVEL%`, and `:FIN` exits by `exit /b %RC%`. The real `cmd.exe` shot is **not played**,
  and its owner is **the ledger** (`epic-dn8`). And whether the language choice is **legible** on
  the served page ⛔ is not settled here: that verdict is taken by eye, on Windows, owner
  `dn8-3` (its `AC8.3.1` re-hosts `AC7.4.3`).
- 📏 **The cost of one state query is measured, and declared rather than reduced** (`dn8-2`,
  2026-09-12, WSL). `etat_machine()` costs **387,73 ms** (median, n=5); `GET /api/etat` under
  the check's doubles, **3,72 ms**. The half the planning notes expected to be expensive —
  re-reading and CRC32-ing the **614 416-byte** asset — is **refuted by the measurement:
  0,74 ms, that is 0,2 %** (CRC32 alone: 0,20 ms), and removing it would cost the integrity
  guard that catches a blank asset. 🔴 **And the attribution of what does cost was wrong in this
  very file:** these are ⛔ **not** "PowerShell round-trips". On this bench `powershell` and
  `pwsh` are **not found** (35 `/mnt` entries on `PATH`), `_powershell()` returns `rc=None` with
  `echec='lancement'`, and the **99 / 103 / 107 ms** of `decouvrir_port`, `tache_presente` and
  `localiser_pilote` are the cost of a **failed launch**. The genuinely expensive probe
  **measured here** is `dependance_presente`: **158,15 ms**, two Python interpreters per module,
  two modules per request. ⚠️ The figure **on Windows** — where PowerShell exists and
  `decouvrir_port` carries a **45 s** ceiling — is ⛔ **not measured**, and cannot be from here:
  this tower's WSL is behind **NAT**. ⇒ 387,73 ms is a **lower bound whose cause is wrong**, it
  is written as such, and the Windows reading is **carried in the ledger** (`epic-dn8`). ⛔ No
  cache is dropped in passing: one surviving an unplug would be **worse** than the cost it saves.

- 🆕 **The checks now parse what they judge, and their shared helpers live in one place**
  (`dn8-1`, 2026-09-11). A new module, `tools/dn_gates.py`, holds the eight helper names the
  checks had been copying — measured that day across the 44 checks: **101 copies for 8 names,
  in 57 distinct implementations**, `ctrl` alone in **19**. ⚠️ **The figure in the planning
  notes was 51 copies and 5 implementations for one of them; both numbers are written down
  and neither is erased** — the first was a textual count, this one reads the syntax tree,
  and that difference is precisely what this work exists to install. A new check,
  `tools/verif_harnais_dn81.py`, fails on a helper re-defined inside the perimeter this epic
  writes — **whether the body differs or is identical**, because an identical copy is still a
  copy — on a `📍` anchor of the planning ledger whose target cannot be reached or whose
  pattern is no longer in it, and on a control written by this epic that judges YAML, HTML,
  CSS or PowerShell **without a parser and without naming what it cannot see**.
- 🆕 **One control added to the ledger check: the planning tracker is now parsed.** Measured
  on a throwaway copy on 2026-09-11 — ⛔ never on the live tracker: a single key re-indented
  from two spaces to four makes the file **unreadable to any YAML parser**, and the check
  returned **`BILAN : 35 OK, 0 KO`, exit code 0** all the same, because it matched
  `^  key:` line by line and the re-indented line simply left the population. 🔴 **And the
  witness the notes prescribed hid this**: re-indenting `epic-dn8` *did* turn the check red —
  but for the wrong reason, three failures all saying *"13 phantom keys"*, because that key
  happens to be cited thirteen times as an owner. A key **nobody cites** broke the file in
  complete silence. Both witnesses are replayed by `tools/verif_campagne_dn440.py`, and it is
  the second one that proves the new control carries anything.

- 🆕 **The install page now installs what it can, and it blocks on what it cannot.** Five
  requests from the owner in session on 2026-09-10 — ⛔ raised by no check in this repository.
  Each of the workflow's four steps carries a **three-position** state witness, in the
  vocabulary the panel itself uses (*real* / *simulated* / *absent*), and every one of those
  identifiers sits in the list the page resets when its local server goes quiet — an
  identifier left out of it would stay on its ellipsis **forever**, which reads as *in
  progress* when it is finished. A **single named factory** greys a gesture **and writes the
  reason and the repair under the button**: before this, the page had **one** disarmed gesture
  on **one** condition, fifteen scattered `disabled` assignments and ⛔ no common factory.
  ⚠️ **Corrected on 2026-09-10 — the earlier figure is named rather than erased.** This
  line, the page and the check all read *seventeen*; re-measured on the page as it stood
  before this marker, `.disabled` is **assigned** at 15 sites and **referenced** 18 times,
  three of them reads. *Seventeen* was references minus one — a count of the wrong thing,
  published on four surfaces, which is the class this repository has already paid for.
  ⚠️ **The line of division is written because it is not intuitive**: the flash is ⛔ **not**
  blocked by the agent's dependencies nor by LibreHardwareMonitor — putting the firmware on
  the board has nothing to do with either, and taking the **main** gesture away from a
  newcomer over a dependency of the **agent** is the very mistake `dn7-5` refused to make.
  ⚠️ And the **third position does not block**: *not testable here* is ⛔ not *absent*; an
  ignorance is ⛔ not a verdict.
- 🆕 **A button that runs the dependency gesture**, non-elevated, with the interpreter that
  serves the page — so the one the agent will use, ⛔ not the first `pip` on the `PATH`. The
  command run is **derived** from the published string rather than written a second time, its
  output and exit code are handed over **as they are**, and three outcomes are told apart:
  success, `pip` **unavailable**, and **timed out**. Afterwards the state is **measured
  again** and the witnesses move **without a reload** — ⚠️ it is that measurement which
  decides, ⛔ not `pip`'s exit code.
- 🆕 **A new verb that activates the agent**, and it is a **composition**, ⛔ not a new
  mechanism. Measured: of the tool's seven verbs, **none** activated. One installs the
  scheduled task but its trigger is the logon **alone**, so nothing starts today; the other
  starts the agent but never touches the scheduler, so nothing survives the session. The new
  verb plays both, relays their exit codes untouched, and reserves **one code of its own** for
  the outcome none of them says: the task installed **and verified**, and no agent alive ten
  seconds later — ⛔ neither a success nor a total failure, since both would be false.
  ⛔ It **redeclares no task setting**: the limited run level, the logon trigger and the
  **3 restarts, 1 minute apart** come **with** the block it reuses, ⛔ not from a rule someone
  could forget. That is what keeps *nothing in `dn7` needs administrator rights* true **by
  construction** rather than by discipline.
- 🆕 **A check over all of that** (`tools/verif_preconditions_dn76.py`, run by
  `tools/run_gates.sh` and replayed mutant by mutant by `tools/verif_campagne_dn56.py`): each
  step carries a witness and its identifier is in the reset list; the witness is painted only
  in the seven stated tokens, each declared in `:root`; the **rejected** green of the firmware
  stays out of the page — and the check **re-measures** that it is indeed rejected there
  rather than taking it on trust; disarming goes through **one** factory; the reason is
  written by a factory under its button; the new verb moves on its **three** surfaces at once;
  its half-success code is checked **as a property**, ⛔ not as a literal; ⛔ no elevation in
  its block — a reciprocal carried where the two existing elevation checks ⛔ do not reach;
  the `pip` gesture is runnable and the LibreHardwareMonitor one is ⛔ not, with the reason
  written; and the **new route** refuses foreign `Origin` and `Host` headers with a **403**,
  which the existing check ⛔ could not see because it knows only the two older routes.
  ⛔ **What it does not prove, and its own header says so**: it opens no browser, installs
  nothing and schedules no task. It proves the mechanism is **wired**.
- **A purchasing page** ([`docs/bom.md`](docs/bom.md)) — what to buy for each of the two
  named tiers, every line carrying a reference, a supplier, a price, **the date the price
  was read** and **the source URL**. Sources that could not be reached are listed one by
  one with the exact address tried, the date and the failure; ⛔ no price is reconstructed.
- **A gate over that page's shape** (`tools/verif_bom_dn61.py`, run by `tools/run_gates.sh`
  and replayed mutant by mutant by `tools/verif_campagne_dn56.py`): the seven fields per
  line, the two tier names, the out-of-tier components and their written reasons, the
  citation of `dn4-41`'s state, and the affiliate-link declaration. It deliberately judges
  **no price** — only that a price carries its date and its source.

- **A place for the 3D-printed case, and a printing notice that says what is not known**
  ([`docs/boitier.md`](docs/boitier.md) and [`docs/boitier/PLANS.md`](docs/boitier/PLANS.md)) —
  the folder `docs/boitier/`, the six accepted file formats and the rule that a mesh alone is not
  enough, the licence (already granted by the `docs/` row of `LICENSING.md`, which was **not**
  touched), and a notice whose **four** parameters — material, layer height, infill, supports —
  are each written **not measured**, with the reason and the owner beside them. 🔴 **No plan is
  deposited**: nothing has been printed and there is nothing to print yet. The page says so
  instead of leaving a reader to find out.
- **A gate over that place and that notice** (`tools/verif_boitier_dn64.py`, run by
  `tools/run_gates.sh` and replayed mutant by mutant by `tools/verif_campagne_dn56.py`): it keeps
  the statement true **in both directions** — while no plan is tracked the page must say so, and
  the day a plan lands under `docs/boitier/` the sentence becomes false and the check goes red,
  every deposited plan having to be cited by the page. It also keeps the plans folder **under
  `docs/`** rather than at the repository root, refuses a plan filed anywhere else, and refuses a
  printing parameter that carries a figure without citing the measurement it comes from. It
  deliberately judges **no drawing** — no dimension, no printability.

- **An affiliate-link page** ([`docs/affiliation.md`](docs/affiliation.md)) — whether this
  repository carries affiliate links, which programmes actually exist for the suppliers it names,
  on what terms, and what French and EU law requires to be disclosed. The state is **measured, not
  promised**: across every tracked text file — the `.md` pages **and** the `.txt` measurement
  records, 436 files on the day it shipped — **no** published address carries an affiliate marker.
  Binary files and source code are outside that sweep; so are 97 tracked text files that are neither — logs, workflow and licence files — five of which carry an address and were re-read by hand on 2026-09-08, also at zero. The page states that boundary rather than implying it. The survey **derives**
  its population from the purchasing page instead of listing it, which comes out at **two**
  suppliers of record rather than the eleven domains the page names. The other ten are the
  addresses `dn6-1` tried and failed to reach, filed as exactly that with the reason they were not
  researched written down — and `waveshare.com` belongs to **both** lists, because it is the board's
  manufacturer as well as one of the addresses that had failed; the page states that overlap
  instead of presenting a clean split. 🔴 **Nothing was signed**: no account opened, no terms accepted, no tracking identifier
  written; every gesture that only the owner can perform is listed with its owner. ⚠️ What that
  costs is written too — AliExpress's admission terms sit behind a login, so four conditions
  (cookie window, payout threshold, per-order cap, approval criterion) come out **not read** rather
  than reconstructed. 🔴 **And the survey corrected itself before publication, on the finding that
  matters most here**: two rows first said Waveshare answered HTTP 403 "to any automated
  retrieval". It does not — with an ordinary browser header the same two addresses answer **200**,
  and the programme page states its terms outright (2% base, 72-hour tracking, US$5 PayPal
  threshold, and a *Who can Join* section that names **GitHub**). ⇒ *"not reached"* is a property
  of the **retrieval method**, ⛔ not of the address, and a failure verdict has to say what it was
  tried with. Both refuted sentences are **described** beside their correction rather than erased — described
  and ⛔ not quoted, deliberately: the gate counts failure verdicts in that page, so quoting the
  old one verbatim would add a fresh occurrence of the very defect the correction removes.
  Every legal text is quoted with its official source and the date it was read, and the page says
  in as many words that it is **not legal advice**. ⛔ No revenue milestone appears anywhere: those
  were taken out of scope on 2026-09-06.
- **A gate over that declaration** (`tools/verif_affiliation_dn65.py`, run by `tools/run_gates.sh`
  and replayed mutant by mutant by `tools/verif_campagne_dn56.py`): it keeps the statement true
  **in both directions**, and it splits the two failures rather than merging them — one check says
  no published address is marked, a separate one says the declaration in force agrees with the
  measured state. Posting a marked link without updating the pages turns both red; annotating the
  pages correctly turns the second one green again and leaves the first red, because the published
  promise itself has changed and that must be a written act. It also keeps the original sentence of
  the purchasing page **word for word** (annotate, ⛔ do not erase), keeps the survey covering every
  supplier the bill of materials names — so the day a new `Source` domain appears the survey goes
  red instead of quietly rotting — and refuses a survey line without its address and date, a failed
  source without its reason, a legal text without its official source, an owner gesture whose owner
  reads "to be named", a milestone figure, and a projected revenue. It deliberately judges **no
  rate** and opens **no connection**: a wrong but dated and sourced rate leaves it green.

- **A local installer, and one file to double-click** (`installeur/`) — `DeskNode-installeur.bat`
  starts a small server **on your own machine** and opens a page on
  `http://127.0.0.1:<port drawn at launch>`. ⛔ Nothing is hosted, ⛔ nothing is opened from disk,
  and ⛔ the port is never a constant: a fixed port can already be taken on somebody else's
  machine, and since *updating DeskNode means reinstalling it*, the second launch is everybody's
  normal case rather than an edge one. The page **exposes** two verbs the repository already had —
  `stop` and `retirer` of `tools/dn_agent_tour.ps1` — and ⛔ reimplements neither; the tool's output
  and exit code are relayed as they are (and the page says **who set** that code, since a few of
  them are its own), and after `retirer` the scheduled task is **asked for again**, because a
  message that says "removed" is not a measurement. 🔴 **The server answers its own page and
  nothing else**: it refuses any request whose `Host` is not the loopback it actually bound, and
  any `Origin` that is not itself — a drawn port is ⛔ not a secret, and a plain cross-origin
  `POST` has no CORS preflight to clear. 🔴 **Nothing here asks for
  administrator rights.** That is not a promise but the state of the code: the task is registered at
  `-RunLevel Limited`, and the tool stops on anything else as a defect — so an elevated installer
  would break the tool that already exists. ⚠️ **What you still have to install yourself is written
  down with the owner who will remove it**: without a standalone executable you need Python 3 plus
  `psutil` and `pyserial`, and the return to a single download is carried by the standalone agent
  planned for V0.2. It is a **declared gap**, ⛔ not a tick and ⛔ not a fault. It ⛔ does not flash
  the board, ⛔ does not offer a language choice, and ⛔ shows no preview of the panel — the last of
  those being a **declared exclusion** of the first version.
  > ⚠️ **Annotated on 2026-09-08 — the first of those three ceased to be true the same day, and the
  > sentence is kept rather than rewritten:** the page **does** flash the board now (see the entry
  > above). The other two hold: no language choice, and no panel preview.
- **A written visual identity for that page** (`installeur/IDENTITE.md`) — seven colour tokens,
  each citing **the firmware file and line it is taken from**, replacing the palette the throwaway
  prototype had borrowed from GitHub. The page and the panel are the same product seen at two
  moments; if they do not look alike, the page is a brochure for something else.
- **A gate over the installer** (`tools/verif_installeur_dn71.py`, run by `tools/run_gates.sh` and
  replayed mutant by mutant by `tools/verif_campagne_dn56.py`): the folder is filed in
  `LICENSING.md`, ⛔ no elevation verb appears in the installer's code, the port is drawn rather
  than written, the announced address is built from the port actually bound, the two exposed verbs
  are **re-read from the tool's own `[ValidateSet]`** instead of copied, the removal is verified by
  a second query, the declared gap carries its owner — ⛔ never "to be named" — and the page's
  colours equal the declared ones **in both directions**, each declared colour being checked
  against the firmware line it cites.
- 🆕 **The install page now flashes the board** (`installeur/charge/` and the flash section of
  `installeur/index.html`). Four **versioned** images and their manifest ship with the repository —
  bootloader, partition table, application and the display asset — written at `0` / `32768` /
  `65536` / `4259840`, `chipFamily` **ESP32-S3**, ⛔ with **no merged binary**, by ESP Web Tools
  **pinned to `10.4.0`**. The pin is a measurement, ⛔ not a habit: on 2026-09-08 the range form
  `esp-web-tools@10` answered **HTTP 302** and redirected — a version that moves on its own would
  change the code that **writes to somebody's board**, silently. 🔴 **The announced version is READ
  out of the binary, ⛔ never copied beside it**: it is the `version` field of `esp_app_desc_t`, and
  a gate refuses any difference between it and the manifest.
- 🆕 **The page frees the serial port by itself, on the port it discovered.** Updating DeskNode
  means reinstalling it, so the second launch is everybody's normal case, and the port is already
  held: the browser would fail on `Failed to execute 'open' on 'SerialPort'`, which explains
  nothing. The page plays the existing `stop` verb — ⛔ it reimplements none — and passes it the
  `COM<n>` it found by asking Windows for `VID_303A&PID_1001`, interface `MI_00`, instead of
  letting the tool fall back to its hard-coded `COM3`. ⚠️ **That verb's exit codes are read as
  facts, ⛔ not as a boolean**: `0` the port was handed back · `4` the stop flag could not be
  written · `7` the agent stopped but the port is **gone** · `8` it is still held. Reading `7` as a
  failure would make somebody give up on a gesture that worked; reading it as a success would
  announce "port handed back" about a port that no longer exists.
- 🆕 **Four obstacles get the page's own words, at the moment they happen.** The flashing tool's
  fallback dialog offers **CP2102 / CH340 / CH342** drivers that this native-USB board
  (`303A:1001`) does not need — the page says so over it. ~~The port's **real name** is given in
  both forms, the one Windows shows (translated: `Périphérique série USB (COM3)` on the reference
  machine) and the one the chip announces (`USB JTAG/serial debug unit`)~~ — ⛔ it is not called
  "DeskNode". ~~The port picker needs **two gestures**, and the page says which.~~ And the
  **recovery procedure** is reachable from the page rather than buried in a 200 KB README.

  > 🔴 **ANNOTATED ON 2026-09-09 (`dn7-2-2`), AND THE TWO STRUCK-THROUGH HALVES ABOVE ARE ⛔ NOT
  > ERASED — THEY ARE DATED.** The browser's port picker was finally **opened**, and it refutes
  > both. It shows **ONE line**, `USB JTAG/serial debug unit (COM3)`, and its button reads
  > **« Connexion »**. ⇒ *"both forms"* presented the localised Windows name as a second form
  > **of the picker**; it is what the **Device Manager** shows, ⛔ not the browser — the page now
  > **attributes** it instead of offering it. And the second gesture was named
  > *"Se connecter"*, which is ⛔ not what the button says. ⚠️ What stays true: the port is ⛔ not
  > called "DeskNode", the selection really does take **two gestures**, and closing the window
  > without picking exits on *"No port selected"*. 🎯 **Mechanism**: Edge names the port by the
  > chip's **USB product string**, ⛔ not by the localised Windows `FriendlyName` — `dn7-2`
  > measured `Get-PnpDevice`, the Device Manager's view, and **generalised** it to a picker
  > nobody had opened. ⚠️ The server-side discovery stays **correct**: it targets interface
  > `MI_00` and returns the right `COM<n>`. It was the **display** that lied. ⚠️ The recovery
  wording is **what was measured**: this repository only ever documented **BOOT held + RESET**;
  "BOOT held while plugging in" appears nowhere, and the page writes the true one.
- 🆕 **Opened anywhere but Windows, the page says so BEFORE the flash.** Web Serial also runs on
  macOS, Linux and ChromeOS while the agent is Windows only, so the flash would **succeed** and
  leave somebody with a correctly flashed board and nothing to display on it. ⛔ This does not widen
  the scope — it ends a silence.
- 🆕 **Where the installed firmware comes from** (`installeur/charge/PROVENANCE.md`) — the exact
  revision, the command that produced it, and the size and SHA-256 of each of the four images.
  ⚠️ **And what nothing checks is written down too**: no CI builds this firmware (`dn4-45`,
  `not started`), the images were produced **by hand**, one of them comes out of a script, and
  there is **no tag and no release** — measured on 2026-09-08, `git tag -l` and `gh release list`
  are both empty and this repository is private. The GPL obligation to point at the source of *this
  exact revision* is therefore met by the revision read out of the binary; a **publicly reachable**
  source is a declared gap carried by `dn8`. Each gap names its owner.
- 🆕 **A gate over the payload** (`tools/verif_flash_dn72.py`, run by `tools/run_gates.sh` and
  replayed mutant by mutant by `tools/verif_campagne_dn56.py`): the five payload files are tracked,
  the four offsets **equal** the ones the build wrote in `flasher_args.json` — or, in a fresh clone
  where `build/` is git-ignored, the partition table, and the check **says which source it used** —
  `chipFamily` is `ESP32-S3`, ⛔ nothing merges the images, the manifest's version **equals** the
  descriptor inside the `desknode.bin` served beside it and is ⛔ never `0.1.0-beta-essai`, each
  image exists at the size and hash `PROVENANCE.md` publishes, the display asset's integrity
  trailer (magic, length, **CRC32**) still validates, the pinned ESP Web Tools version is the same
  in the page and in `THIRD-PARTY.md`, and the page carries every sentence above.
- 🆕 **The panel's language is chosen on the install page, before the flash — and a separate
  gesture writes it into the board.** Two positions above the install button, **English by
  default**, visible without unfolding anything, plus a **separate, explicit gesture** that writes
  the choice into the board after the flash. 🔴 **⛔ THIS ENTRY DOES NOT CLAIM THE BOARD HAS THE
  LANGUAGE ON ITS FIRST BOOT, AND THE REASON IS MEASURED**: flashing **wipes the board's stored
  settings** — after a flash from this page the board's `cfg` command answers *no config in NVS,
  defaults applied* (2026-09-09) — and the board **restarts on its own before** the gesture is
  played. ⇒ **the first boot after an install is ENGLISH whatever was chosen**; the panel switches
  when the gesture is played, and the gesture is **to be replayed after every install**, because
  updating DeskNode means reflashing it. The page says so at the step that sets the language.
  🔴 **Choosing English writes nothing at all**, and that is the property rather than a shortcut:
  the board starts in English when its NVS carries **no** language, so writing a value meaning
  "English" would replace a **default** with a **choice**. Measured: the gesture played with
  English selected sends **zero bytes** on the port. ⚠️ And the page ⛔ promises no more than it
  knows: it has **not read** what the board carries, so it ⛔ does not claim an English start on a
  board whose settings already hold French. 🔴 **The gesture is explicit, ⛔ not chained to the end
  of the flash**, and two measurements decide that: the page holds **no listener** on the flashing
  module, and **the delay between the end of the flash and the moment the REPL answers is not
  measured** — sending too early loses the line, and a lost line would produce *a success announced
  on a language that was never set*. The gesture therefore **wakes the console up and waits for its
  prompt** before sending anything. 🔴 **The acceptance is read, then the state is read back —
  ⛔ never the order that was sent**: *set* is only reachable from a re-read that carries the chosen
  code. There are **five distinct outcomes**, each recognised by the literal the `langue` command
  prints **for it** — *set* · *refused* · *applied but ⛔ NOT stored* · *no answer* · *no prompt* —
  with the board's own words relayed verbatim. ⚠️ The fifth one exists because it was **measured**:
  when the board fails to store the setting it prints its warning, **then rebuilds the scene, then
  prints the success line**, and returns non-zero — so it gets **one key that says both facts**, the
  panel **has** switched and it will ⛔ **not** keep it. ⚠️ And *set* ⛔ **does not promise that a
  reboot survives it**: the board applies the setting **before** storing it, so the re-read answers
  the same either way — the only proof is the panel's own top bar after a power cycle.
  ⛔ **Nothing was added to the firmware**: the console command, the NVS key and the
  one-definition-per-string table were already shipped; this page adds **the choice**.
- 🆕 **A gate over that choice and that gesture** (`tools/verif_langue_dalle_dn73.py`, 61 checks,
  34 mutants, run by `tools/run_gates.sh` and replayed mutant by mutant by
  `tools/verif_campagne_dn56.py`): the choice exists at two positions and **precedes** the flash
  element, the English default is written **in the document** rather than posted by a script, the
  panel's choice stays **distinct** from the page's own language and the page **says so in both
  languages**, the order sent is a literal plus a code the binary really carries, the guard that
  writes nothing for English **precedes** every write, the write lock is released **on both
  paths**, the prompt is awaited **before** the order, the outcomes are anchored **each in its own
  branch**, success is reachable **only from the re-read**, every outcome **says what became of the
  port**, and the gesture ⛔ **is not offered** while the install block is hidden. It also
  **re-reads inside `firmware/`** the six answer literals it anchors and pairs them **both ways**
  with the patterns the page matches — a literal nobody pairs guards nothing, and a pattern nothing
  re-reads rots silently. 🔴 One check exists for a trap that was **measured**: the board's console
  carries the word *REFUS* for the I²C bus and for the clock too, on the **same** stream, in the
  cold-start window where this gesture is played — so no classification pattern is allowed to match
  an **unrelated** log line, and the witnesses for that are read out of `firmware/` rather than
  invented. The page itself cites ⛔ **no line number**.
- 🆕 **A bench that RUNS the install page's JavaScript — the first thing in this repository
  that does.** Until now no tool here executed `installeur/index.html`: the gates read its
  structure, and the only DOM shot ever fired was a headless browser started by hand, outside
  `tools/run_gates.sh`. `dn7-3` added matter of a new kind to that hole — the page had only ever
  **read** the port, and it now **writes** — so the hole is closed for that path.
  `tools/banc_langue_dalle_dn73.mjs` **extracts the page's `<script>` and evaluates it** against
  a stub DOM and a stub port, then plays the **nine** rows of the story's input/output matrix,
  including the three nothing covered before — *the port is held by the agent*, *double click*,
  *no serial access* — plus **nine** paths two reviews named: the port obtained **through the
  browser's picker** followed by a complete set, the *applied but not stored* answer, a re-read
  that does **not** carry the code, a picker **already open**, a picker **cancelled**, a **real
  click** on the French button (the button ⇄ code binding, which nothing asserted), the install
  block **revealed** and then **hidden** (the arming polarity, in both directions), and a
  `write()` that **rejects in flight** (the safety net, which must hand the gesture back). ⛔ It copies no logic: a harness
  replaying its own copy measures only itself, and a check enforces that. 🔴 It also records the
  **bytes** written rather than the number of `write()` calls — *zero bytes* is what three
  surfaces here publish — and the **sequence** of announced outcomes rather than the final state — a success announced too early
  and then **overwritten** leaves the final screen correct and the defect invisible, which is
  measured, ⛔ not supposed. 🔴 And it **exits non-zero when its chain does not resolve**: a bench
  that returns 0 on a truncated list announces a success it never measured, and a flag replays
  exactly that case. `tools/verif_banc_langue_dn73.py` (40 checks, 28 mutants) **launches** it on
  every pass. ⚠️ **`node` is a declared prerequisite**: without it that gate returns **4** with its
  reason and is declared non-playable — ⛔ it never comes out green on a bench that did not run,
  and the CI **records** whether the engine is there rather than assuming it.
  ⛔ **What the bench does not prove**: it plays a **stub** board. That the language is really
  on the device, and survives a power cycle, is read **on the panel's own top bar, by eye**.
- **Licensing.** GPL-3.0-or-later for `firmware/`, MIT for `agent/`, CC-BY-SA-4.0 for
  `docs/`, and GPL-3.0-or-later for `installeur/` — code that serves a GPL binary, ⛔ not prose.
  See [`LICENSING.md`](LICENSING.md).
- **Third-party inventory** (`THIRD-PARTY.md`) — necessary because
  `managed_components/` is git-ignored, so the licenses DeskNode links against were
  recorded nowhere.
- **Contribution guide** (`CONTRIBUTING.md`), including the CLA requirement.
- **The CLA itself** (`CLA.md`) and the workflow that asks for it
  (`.github/workflows/cla.yml`). Until 2026-09-02 `CONTRIBUTING.md` promised that "a
  bot handles it in one click" while there was no file under `.github/` at all.
- **A gate over the promises this repository publishes**
  (`tools/verif_licences_dn52.py`, run by `tools/run_gates.sh`): licensing coverage in
  both directions, `idf_component.yml` against `THIRD-PARTY.md` in both directions, and,
  in the reader-facing files, outbound links, quoted section titles, cited tool flags,
  roadmap markers, announced counts, the CLA artifact — the workflow, its pinned
  version, the document it makes you sign, and the named owner of the gap it leaves —
  and the rule that a NVIDIA claim is **not implemented** unless the agent says so.
  It does **not** check every promise in prose; the list above is what it checks, and
  the tool's own header says what it deliberately does not.

### Changed

- 🆕 **The root `README.md` is split: a short front page in English says what DeskNode is, and
  the French engineering log moves to `docs/journal-de-bord.md`** (`dn8-4`, 2026-09-13).
  🔬 **Measured the same day, ⛔ not taken from planning**: the root `README.md` had become a
  French engineering log of **257 192 bytes / 2 550 lines** at `baf4265` — its own opening line
  still announced *"168 Ko"*. **It is moved, ⛔ not rewritten**: the body of
  `docs/journal-de-bord.md` is that file **byte for byte**, except **13 relative links** rebased
  so they still resolve from `docs/`. That transformation is a piece of data, it **fails
  closed** (each rebase must apply exactly once, and every local link of the base must be
  covered), and it is proven three ways: a comparison tool kept in the tree and replayable at
  any time, `tools/scission_readme_dn84.py` (⛔ not a check: CI clones without history, and the
  log will keep being annotated), which reports `IDENTIQUE` and goes red on a one-byte change,
  on one link left un-rebased, and — seen on mutated copies of the tool — on a rebase that does
  not apply or a base link the table does not cover; a raw `diff` between the base and the log's
  body that shows **the 12 lines carrying those 13 links, and nothing else**; and
  `tools/verif_licences_dn52.py` resolving every link from `docs/`. ⚠️ **The licence check is ⛔
  not fully independent of the tool**: both read links with the same expression. What that
  expression cannot see was measured in the base — **0** reference-style link definitions and
  **0** HTML links outside code blocks, plus one external `https://` autolink that rebasing does
  not concern. A dated header in front of the body says where the file came from, and that the
  paths written in `code` still read from the repository root. ⛔ **Not split into several
  files**: each extra file is one more place where a check that reads **text** can be green on
  something false.
  **The front page** follows the reading order the epic set — the name, **a photo**, **one
  sentence** (*a physical desktop dashboard*), **the licences**, then the hardware — and carries
  the known issues **as measured** (below). ⛔ No logo exists in the repository, and none was
  invented. 📷 **The media is an owner decision of 2026-09-13, written rather than left open**:
  two photos of the **bare-wired prototype** taken on 2026-08-30 (`DSC04915` in the Active
  state, `DSC04919` in context on the tower) are **assumed** for this first version rather than
  reshot, **and so is the French interface they show** — a freshly flashed board starts in
  English, and the caption says so. The two JPEGs were reduced to 1 600 px, orientation applied
  **before** stripping every EXIF segment, **171 807** and **206 956 bytes** (the camera files
  weighed 10.4 and 11.3 MB); they live under `docs/photos/`, so `docs/`'s **CC-BY-SA-4.0**
  applies. ⚠️ **Their names are not the ones first planned, and the reason is measured**:
  `2026-08-30_1804-…jpg` matches the naming convention of `tools/verif_photos_dn63.py`, which
  treats any such name cited in any tracked Markdown file as a wiring photo — the first draft
  turned that check red (`27 OK, 1 KO`). The date and time are kept, separated by a hyphen.
  **What guards what, and the price is written.** The seven checks that read the log at the
  root (`verif_installeur_dn71`, `verif_prerequis_dn75`, `verif_paliers_dn441`,
  `verif_demarrage_dn443`, `verif_langues_dn442`, `verif_veille_dn33`, `verif_flash_dn72`) are
  **re-pointed** at `docs/journal-de-bord.md`, each with a dated comment, ⛔ not rewritten: they
  guard exact French sentences, with mutants anchored on them, and every count is unchanged.
  ⇒ **they no longer guard what a newcomer reads first.** A new check,
  `tools/verif_vitrine_dn84.py`, does: the reading order, the absence of *"CPU monitor"*, the
  size, every local image the page cites read **marker by marker** (⛔ no Pillow on the runner)
  for its pixels (long edge ≤ 1 600) and for any segment other than `APP0 JFIF`, the caption that
  assumes the prototype, the tiers, the entry point (named **and** present), English by default,
  the install command read from the local server's own `GESTE_DEPENDANCES`, and the known issues — `~40 s`, `335.8 ms` against `300 ms`, AMD only, and
  **NVIDIA with *not implemented* on the same line**. It reads headings and images outside code
  blocks, **states in its own output that it does not read raw HTML, setext headings or
  reference links**, and goes red if the page contains any. **16 controls, 16 mutants**, each
  mutant seen red on the control it targets, and a mutant that changes nothing exits `3`; three
  of the controls check that every control is targeted by a mutant and every target is real.
  ⚠️ Several controls bundle several properties, and a mutant proves **one** of them, ⛔ not
  all.
  `tools/verif_dossier_d5_dn45.py` gains the log **next to** the README, so its coverage does not
  shrink in silence, and the six manifest rows of `docs/dn4-15-arbitrage.md` that were keyed on
  `README.md` are re-targeted with a dated note — `23 OK, 10 KO`, exactly as before.
  ⛔ **What is not measured, and cannot be here**: whether a stranger understands DeskNode in
  fifteen seconds. That verdict needs a stranger, and there is none while the repository is
  private. *(Annotated on 2026-09-15, `dn8-8`: the repository is public since that day, so a
  stranger can now exist; that verdict is still ⛔ not measured.)*
  **The build's starting conditions now have their failure written down**, measured on
  2026-09-13 outside any working tree and published in `CONTRIBUTING.md` under *When a
  starting condition is not met*: an ESP-IDF outside `~5.5.0` is refused with exit code **2**
  by a message that never names the version it found (provoked through
  `CI_TESTING_IDF_VERSION`, which plays **only** the component manager's check); an inherited
  `sdkconfig` wins **silently** even while the tool announces it is loading
  `sdkconfig.defaults`; the disk budget is **summed** for the first time — **8.16 GiB**
  allocated for ESP-IDF, toolchains, one build and its components, **8.34 GiB** with the
  component cache — and the **4.30 GiB** published for `~/.espressif` turns out to count 81
  hard-linked toolchain files more than once (**3.80 GiB** on disk); an HTTPS clone was
  measured, and SSH was not.

- ⚠️ **Five `📍` anchors of the planning ledger pointed at nothing, and they were re-routed
  in place** (`dn8-1`, 2026-09-11). Measured over the **94** targets carried by **86** anchor
  lines: one named a capture file that never existed, two named patterns that had been
  removed from the tools they point at, and two named sentences no longer on the install
  page. ⚠️ **Seven more are reachable only after normalisation** — accents, mixed case, dash
  runs, the ⛔/⚠️ markers this repository scatters through its prose — and that population is
  itself a control: if it ever empties, the normalisation is proven by nothing and the check
  says so.

- 🆕 **`dn7` stops only exposing, and that is an owner decision, ⛔ not a drift.** The thread
  of this epic was *« `dn7` exposes, it builds nothing »* — true from `dn7-1` to `dn7-3`, and
  **false from 2026-09-10 on**, by the arbitration *« it installs as far as possible,
  otherwise it exposes »*. ⛔ The earlier sentence is **named rather than erased**: it
  described exactly what the page did over those three markers. What it exposes now, it
  exposes **with its reason**: LibreHardwareMonitor, whose gesture needs administrator rights
  this installer never asks for, and Python itself, which ⛔ cannot be a precondition of a
  page that **does not exist without it** — the file you double-click stops before serving a
  single byte, so the link lives in **both** places rather than only in the one nobody in need
  can reach.
- ⚠️ **A declared gap, and it is the heart of this change rather than a footnote: the state
  witness is ⛔ NOT green**, although the owner asked for green dots. Three measurements
  decide it, ⛔ no argument. The install page's identity is a **closed list of seven roles**,
  each one **read out of the firmware**, and the file that states it writes its own rule —
  *colours are not invented here, they are read over there*; none of the seven is green.
  Green was **tried on the product and abandoned**: `0x4ade80` was the first pass, and the
  owner's own **eye** replaced it on 2026-08-25 because it did not read well on a green PCB —
  its three occurrences in `firmware/` are **all** annotations of that rejection. And `dn7-4`
  already settled, **on this very page**, that the filled state is a difference of **shape**,
  ⛔ not of hue, after two neighbouring hues made one position be read for the other **in
  session**. ⇒ what the request wanted — *seeing at a glance* — is carried by the **shape**
  and by the product's own vocabulary. 🔴 **And the mechanical back door is closed on
  purpose**: citing the firmware line where the abandoned green still sits would **pass** the
  existing identity check while publishing a dead value as a live identity, so the new check
  refuses the rejected values **by name**. The carrier is written: an owner arbitration that
  amends the identity file with a **live** firmware source.
- 🆕 **LibreHardwareMonitor is now a HARD prerequisite of the agent, and the declared
  gap names it.** Owner decision of 2026-09-10, raised **by a question in session** —
  ⛔ by no check in this repository. Measured the same day: the install page, its local
  server and the roadmap carried **zero** mention of it, while `agent/dn_agent.py`
  carried 142 on 129 lines and its own header says *« it is LHM that does it, and it
  alone »*. Someone following the page to the letter therefore ended up with a running
  agent whose **CPU temperature** and **three fan speeds** would never fill in, and the
  only complete sentence about that in the product was a `stderr` line printed **when a
  scheduled task shuts down**.
  - **What changed, exactly.** The declared gap names LibreHardwareMonitor on the three
    surfaces a newcomer crosses — the page, this file's sibling `README.md`, and the
    installer's pre-flight, which now **prints** its state in **three positions**
    (*present* / *ABSENT* / *not testable here*). Its gesture is **its own**
    (`tools\dn_lhm_tour.ps1 -Poser`), ⛔ not `pip`: it is ⛔ **not** a Python module.
    The published gap is now **re-derived** from the agent's real imports **through the
    AST**, in **both directions**, so a dependency that appears, disappears or loses its
    guard makes a check go red instead of staying quiet. That derivation found a second
    fault on its first run: `pyserial` is imported **without a guard** too, in the
    normal-regime branch, and the page said that of `websockets` alone.
  - **The pre-flight that really refuses is the agent's, ⛔ not the installer's.** It
    stops on its **own** exit code, **`12`**, with a message naming LibreHardwareMonitor,
    its gesture and what falls without it. ⛔ The install page does **not** refuse and its
    exit code `6` is **unchanged**: flashing the board has nothing to do with
    LibreHardwareMonitor, and blocking the page would take the **main** gesture away from
    a newcomer over a dependency of the **agent**.
  - 🔴 **And the price is written, ⛔ not hidden.** A machine without it kept everything
    **except the four quantities LibreHardwareMonitor publishes** — the CPU
    temperature and the three fan speeds — and now loses the **agent entirely** — the README table
    that measures the opposite is **annotated at its date**, ⛔ not erased, because it is
    what makes the cost readable. And because the LibreHardwareMonitor task starts
    **elevated** at logon while the agent's does not, the two **race**: the existing
    recovery is **3 restarts, 1 minute apart**, so **beyond about three minutes the
    agent is absent for the whole session**. ⛔ No elevation was added to anything this
    repository ships — probing is a `GET` on the loopback, and the agent's scheduled task
    stays a limited one.
  - ⚠️ **What is ⛔ not closed by any check here**: that a real tower without
    LibreHardwareMonitor refuses. No check in this repository installs it, opens a
    browser or starts a scheduled task. That fact is measured on Windows and filed under
    `mesures/dn7-5/`, where the agent's absence is **verified** rather than deduced from
    the message.

  > ⚠️ **Annotated on 2026-09-14 (`dn8-7`) — this entry is ⛔ not rewritten, and the refusal it
  > describes no longer ships.** It held from 2026-09-10 to 2026-09-12. Since 2026-09-12 the agent's
  > pre-flight **waits** for LibreHardwareMonitor — 5 minutes by default, `-AttenteLhm` in
  > `tools/dn_agent_tour.ps1` — and then **starts anyway**, the CPU temperature and the fan speeds at
  > `--`. Source: the re-annotation of 2026-09-12 in `docs/journal-de-bord.md`, and the front page's
  > *Install* section, which says the same. No entry was added for that change, and none is back-filled.
- **`mesures/` and the Markdown files at the repository root are now CC-BY-SA-4.0**
  too — added on 2026-09-04, at the code review of the entry below, which had applied
  its own reason to only half the tree. `mesures/` is 330 measurement captures and the
  root prose is the README, the contribution guide, the changelog, this file's siblings
  and the CLA: filing either under a software copyleft says the same unsupported thing.
  `LICENSE` itself and `.gitignore` deliberately stay under the fallback.
- **`hardware/` and `assets/` are now CC-BY-SA-4.0**, not GPL-3.0. `hardware/` is the
  measurement log of the board — documentation, the same nature as `docs/` — and
  `assets/` was covered by neither list in `LICENSING.md`, which is not the same thing
  as being covered by the fallback. See `LICENSING.md` for the reasoning and for why
  this is a correction rather than a relicensing.

### Fixed

- 🆕 **Three things the install page placed badly, ⛔ none of them a false statement.** All
  three were seen **by eye, by the owner**, on 2026-09-10, and ⛔ by no check in this
  repository.
  🔴 **A verb's verdict was written four gestures below the button that ran it.** The
  transcript had **one** place — after the fourth step — while *"Stop the agent"* lives at
  the **first**: clicking moved the view onto step 2 and nothing changed under the reader's
  eyes. ⚠️ This is **the defect `dn7-2-2` fixed for "Remove the agent"**, surviving **the
  other way round**: a **fixed** place cannot serve two buttons four gestures apart. ⇒ the
  transcript is now **moved under the button that was just clicked**, and returns to its
  place in the document when nobody asked — a **page-level** fact (*no server*, written with
  **no click**) is ⛔ never attributed to the last button pressed, which would publish a
  **false cause**. The place it returns to is **read from the document**, ⛔ not written a
  second time in script: a number written beside a computed number ends up diverging.
  🔴 **The language gesture now relays the console's exact refusal.** The page **knew** the
  cause — *"the picker was closed without selecting the line"* — and wrote it in the block of
  **step 4**, while step 3 showed a **guess**: *"most often a port picker is already open"*.
  ⇒ the named fact now surfaces **where the eye is**. ⛔ **No message was written and ⛔ no
  key was added**: the guess **stays**, for the **one** case where it is **true** — an
  opening genuinely **already in flight**. A refusal is forgotten at the **start** of every
  attempt, so ⛔ no refusal from an earlier attempt is ever relayed as a fact of this one.
  ⚠️ **The dynamic bench is what measured this change**: `tools/verif_banc_langue_dn73.py`
  **executes** the page's own script against a dummy port, and **three of its cases went red
  the moment the fix landed** — port refused, no serial access, picker cancelled — because
  their expected text still spelled out the defect. Those three expectations were rewritten
  to the fact, **with the earlier value named rather than erased**.
  🔴 **The active position of a language picker is now a filled block**, ⛔ no longer an
  outline. Both state rules carried **exactly** the declarations of `button:hover:enabled`,
  so hovering an inactive position made it **look active**, and the gap at rest was **two
  neighbouring shades**. ⛔ **No colour was added**: the fill uses tokens already declared in
  `installeur/IDENTITE.md`, and the **active-and-disabled** case is written out explicitly,
  because the state rule outweighs `button:disabled` and a greyed button would otherwise
  read as clickable.
  ⚠️ **What is measured, and what is not.** A new check,
  `tools/verif_placement_dn74.py` (**42 checks, 25 mutants**, run by `tools/run_gates.sh` and
  replayed mutant by mutant by `tools/verif_campagne_dn56.py`), keeps the **mechanism**: the
  transcript's home is read rather than rewritten, it is moved **before** being revealed,
  every write inside the verb carries its button, the page-level fact carries none, the
  console's refusal is recorded and relayed, and the two state rules carry a fill that
  **differs** from the hover rule. Its thirteen new checks were played against the
  **original** page first, and **all thirteen came back red**. The bench gained **two cases**
  of its own — where the transcript ends up after a click, and where it returns with no click —
  and the click case is **red against the original page** too. 🔴 **It ⛔ does not run the
  page's JavaScript and ⛔ draws nothing** — so ⛔ **it cannot say the reader sees any of
  this**. Whether the filled position reads as selected at a glance closes **at the owner's
  eye**, on the served page, and that observation had ⛔ **not** been recorded when this
  entry was written.
- 🆕 **The install page said one thing and the port picker showed another.** The picker was
  finally **opened** on 2026-09-09, and it shows **ONE line** — `USB JTAG/serial debug unit
  (COM3)` — with a button reading **« Connexion »**, while the page announced *"the two forms"*
  and *"Se connecter"*. The page now names **the form the picker shows**, and **attributes** the
  localised Windows name to the **Device Manager**, where it really appears. ⚠️ The earlier
  wording is **struck through and dated**, ⛔ not erased, in this file and in `README.md`.
  ⚠️ The **server-side discovery was never wrong**: it targets interface `MI_00` and returns the
  right `COM<n>`. It was the **display** that lied, and ⛔ nothing was "fixed" in the discovery.
  🔴 **And the check that guarded the old wording was made to go RED before it went green
  again**: the two reversed controls of `tools/verif_flash_dn72.py` were rewritten first and
  played against the **original page** — both `[KO ]`. A check that goes green without ever
  having gone red guarded nothing.
- 🆕 **Two buttons posted the same verb, and the code said so.** *"Free the port"* and *"Stop the
  agent"* both posted `stop`, on the same port, and returned the same output — so naming them by
  what set them apart was impossible: nothing did. They are **merged** into one button named by
  its whole effect, **"Stop the agent and hand the port back"**.
- 🆕 **Reading the board no longer goes through the button that reflashes it.** Until 2026-09-09
  the only path to the board's logs was the install button. The page now carries a **separate**
  entry that opens its **own** serial port at **115200** baud — a rate given by three concordant
  sources in this repository — plus an explicit **"Close and hand the port back"**. ⚠️ Its three
  refusals are named **separately**: no serial access · no port chosen · **port refused** (the
  port exists, it was chosen, and the agent holds it). ⛔ Never "no board" for a refused port.
  ⚠️ **Written rather than left implicit**: this is ⛔ not a limitation of ESP Web Tools. Its
  console lives in a **second chunk whose name carries a build hash**, imported only from the
  install button's own click handler — measured: the pinned module (`install-button.js`, 2 829 B)
  contains `getWriter` ×0, `onData` ×0, `writable` ×0. Hard-coding that hashed name would work
  today and return **404 in silence** at the first upstream release, with ⛔ no gate in this
  repository able to see it.
- 🆕 **The install page speaks two languages, English by default.** Both languages live in the
  **same document**, as sibling elements, and a stylesheet rule hides one: the page is therefore
  English **before any script runs** — the default is **structural**, ⛔ not promised.
  ⚠️ **⛔ No memory is promised, and that is measured**: the server draws a **different port at
  every launch**, so a new origin every time, so **no browser storage survives**. The page comes
  back in English at each launch and ⛔ does not claim otherwise. ⚠️ ⛔ **Not to be confused with
  the language of the panel**, which is a different question and a different language.
  🔴 A new gate, `tools/verif_page_dn722.py` (**56 checks, 32 mutants**), keeps all of the above:
  it also refuses a key of the message table that has **no twin**, and any visible text that sits
  outside the two-language mechanism.
- 🆕 **The gesture table in `README.md` contradicted itself in one paragraph** — it listed
  **four** rows while the sentence under it said "these **two** gestures", and two of its four
  rows were the same gesture. Corrected, with the earlier value **named rather than erased**.
- **The false claim that NVIDIA GPUs are covered.** NVIDIA is **not implemented**:
  there is no NVML in the agent. The claim appeared in this file and in
  `THIRD-PARTY.md`, while `agent/dn_agent.py` refuted it in writing the whole time.
  Both files now say so.
- **Numbers that were rounded now carry their measurement.** The detail-page timing is
  335.8 ms over n = 80, not "about 335 ms".
- **Tools no longer reach outside the clone.** Three tools under `tools/` depended on
  a path that only exists on one machine: two absolute paths in
  `tools/verif_dossier_d5_dn45.py`, a UNC path in `tools/bench_lisseur_dn45.py`, and
  the default of `--csv` in `tools/thermique_ventilos_dn48.py`, which pointed at a
  Windows user profile and was **opened for writing**. ⚠️ *Corrected at the code review
  of 2026-09-04: this sentence said that one "started, printed its header, and only then
  failed". It does not. `enregistrer()` writes a `<csv>.pid` file first, before any
  output, so on another machine it died* **silently, with nothing printed at all** *—
  measured: exit 1, empty stdout, `FileNotFoundError` on the `.pid`. The original wording
  is named here rather than quietly swapped.* Each now derives its root from its own file
  location, or from `tempfile.gettempdir()`. The gate that also reads the private
  planning repository now takes it as an argument and, when it is absent, checks the
  four authoritative files that *are* in the clone and **prints the two it could not
  reach** — instead of silently certifying a tree that was not the one under test.

### Verified

- **Browser flashing works end to end** on the Waveshare ESP32-S3-Touch-LCD-2.8B
  (2026-08-31). Web Serial in Edge over a secure context, the four images written at
  their offsets with no merged binary, a clean reset, the USB device re-enumerating
  unchanged, and the dashboard coming back live. **No driver and no toolchain
  required.**

  > 🔴 **CONFRONTED ON 2026-09-08, AND THE CLAIM ABOVE IS ⛔ NOT ERASED — IT IS DATED.** What was
  > measured on 2026-08-31 was measured on a **throwaway prototype that lives outside this
  > repository**, whose manifest announced `0.1.0-beta-essai` — its own test-bench value — over
  > images that are now **stale** (they predate the language work). ⇒ the sentence is true **of that
  > run, on that day, with that payload**; it was ⛔ never true of anything this repository shipped,
  > because until 2026-09-08 this repository shipped **no flasher at all**. What ships now is the
  > page of `installeur/`, with a **versioned** payload whose announced version is read out of the
  > binary — and inheriting the claim above in silence would have been exactly the defect that
  > version check exists to prevent. ⚠️ **What is still not re-measured is the second half**: that
  > the port dialog goes all the way through *from this page*, on a board. That is a native browser
  > dialog no command-line flag drives; it needs a human hand, and it is recorded under
  > `mesures/dn7-2/` rather than assumed here.

### Known issues

- **Activating the agent from a downloaded copy is expected to fail** (added on 2026-09-14,
  `dn8-7`). On a clone or a downloaded archive of the repository, the install page's *Activate the
  agent* step should be refused with exit code `3`: the launcher expects the agent **next to
  itself** (`tools/dn_agent.py`), a layout that only the author's own deployment script produces.
  This was established on 2026-09-14 by reading `tools/dn_agent_tour.ps1` (and by an earlier run
  of that launcher from a copy of the repository); it has ⛔ not yet been observed on a downloaded
  copy. The standalone executable planned for V0.2 is what removes that step.
- Touch input can be unreliable for roughly **40 s after a cold start** — the whole
  I²C bus degrades during that window. Cause not yet investigated.
  > ⚠️ **Annotated on 2026-09-14 (`dn8-7`) — *"Cause not yet investigated"* is ⛔ not rewritten,
  > and it had stopped being true on 2026-08-20.** The window was **characterised** that day, over
  > six physical cold starts (`hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md`, § 13.17.1): on
  > about **1 cold start in 6**, multi-byte transactions fail across the **whole** bus — the touch
  > controller's reads failed **55.5 %** of the time — for about the first 40 s, then recover on
  > their own. What is still missing is the **cause**: it is **not established**. The front page's
  > *Known issues* carries that wording.
- Opening a detail page takes **335.8 ms** on average against a 300 ms target — n = 80,
  spread 281.2 to 400.9. Not perceptible in use, but the number does not meet the
  stated goal.
  > ⚠️ **Annotated on 2026-09-14 (`dn8-7`) — *"Not perceptible in use"* is ⛔ not rewritten, and it
  > is a verdict, ⛔ not a measurement.** It is the owner's verdict **by finger**, in the session of
  > 2026-08-24 (*« franchement ca repond tres bien »*), and the same pass timed **361.8 ms** on
  > average from tap to flushed screen (n = 26) — more than the 335.8 ms above, which is measured
  > without the touch chain (`hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md`, § 22.10). The front
  > page does not repeat it.
- The agent runs on **Windows only**, and its GPU readings come from **AMD only**.
  **NVIDIA is not implemented** — there is no NVML in the agent, and `pynvml` is not a
  dependency. **Intel Arc and integrated GPUs are untested** — no hardware available to
  check.
- **The display has no language selector, and that is deliberate.** One was built,
  flashed, seen working and validated, then removed: the choice belongs on the browser
  flasher, not on the panel. What ships is an interface that speaks **English by
  default**; the language can be changed from the serial console (`langue fr`) and is
  then persisted on the device. Offering the choice at
  install time is still to come (`dn7` — see [`docs/roadmap.md`](docs/roadmap.md)).
  > ⚠️ **Annotated on 2026-09-09 (`dn7-2-2`) — the entry above is ⛔ not erased, and it stays
  > OPEN, but half of what a reader would take from it has changed.** The install **page** now
  > offers **FR/EN with English by default**, chosen at the top of the page. ⛔ That is
  > **not** the sentence above: the **panel** still has no selector, and the choice made on the
  > page is ⛔ **not** carried to the board. **Two different languages are in play** — the one
  > the reader reads, and the one written into the device — and posting the second at install
  > time is still to come. ⇒ this entry stays under *Known issues* for the **panel**, and the
  > page's own language is recorded under *Fixed*.
  > 🎯 **Re-annotated on 2026-09-09 (`dn7-3`) — ⛔ nothing above is erased, and the last
  > sentence has just stopped being true.** *Offering the choice at install time* is no longer
  > "still to come": the install page carries the choice, **above the flash button**, English by
  > default, and a separate gesture writes it into the board over the serial console. ⇒ what is
  > **left** of the entry above, and it is smaller: the **panel itself** still has no on-screen
  > selector — the choice is made on the page, ⛔ not on the device, and that was a decision
  > rather than an omission (the two on-screen targets were built, measured, and removed for a
  > measured load regression). ⛔ This entry is **not** deleted: it stays as the record of what
  > the panel does not offer.
- **The CLA bot has never been exercised by an outside contributor.** It was watched
  running on an **internal** pull request on 2026-09-02 — it commented, linked to
  `CLA.md` and created the signature store — and again on 2026-09-04, on the workflow
  as it now ships: it commented, an unrelated comment allocated **no runner at all**,
  and a `recheck` comment did. But this repository has no fork and a single
  collaborator, so no *external* pull request can exist yet. Proving it against
  a real outside contributor is carried by `dn8` — see
  [`docs/roadmap.md`](docs/roadmap.md).

  > ⚠️ **Annotated on 2026-09-15 (`dn8-8`) — ⛔ not rewritten.** The repository became public that
  > day and can be forked, so a pull request from outside can now exist. None has been opened
  > yet: the recording of a real signature is still unobserved.
- **One of the repository's own gates is red in the published tree**:
  `tools/verif_dossier_dn415.py`, 17 checks passing and 10 failing. All ten concern
  files of the private planning repository, which are not part of this clone. It is
  published as-is rather than hidden, and making the gates run automatically is
  `dn4-39` — see [`docs/roadmap.md`](docs/roadmap.md).
  > ⚠️ **Annotated on 2026-09-02.** The gates now run automatically
  > (`.github/workflows/gates.yml`). ⛔ That does **not** make those ten failures go
  > away, and CI will never see them: they concern the private planning repository,
  > which is not in the clone. Where that repository is absent the gate now reports a
  > **missing prerequisite** with its reason and a dedicated exit code, ⛔ not a
  > verdict on the code — and it says so in its own output. Anchoring those manifests
  > by pattern instead of by line number is still `dn4-40`.
- ~~**Four tools under `tools/` reach outside the clone**, to absolute paths that
  exist only on the author's machine, so they cannot run from a clone anywhere else.~~

  ✅ **Resolved on 2026-09-04.** ⛔ The sentence above is struck through rather than
  deleted: it was true when it was published. Two of those four were repaired in
  passing by unrelated work before this was picked up, and a **fifth** — which no
  earlier list had ever named — was found the day it was fixed, in the default value
  of a `--csv` option pointing at the author's **Windows** profile. All of the
  remaining ones now derive their root from their own location, or from the system
  temporary directory. See **Fixed**, above.
- CPU temperature and fan RPM require **LibreHardwareMonitor**, installed separately
  with administrator rights. Without it those two values show `--` and everything else
  keeps working.
  🔴 **Annotated on 2026-09-10, ⛔ not rewritten — the last sentence stopped being the
  whole truth that day.** *« Everything else keeps working »* is still exactly right of
  the **firmware and the agent's own measurements**: the CPU percentage, the GHz, the
  MB/s and the AMBIENT box never depended on LibreHardwareMonitor. What changed is **the
  supported path**: the owner ruled that it is a **hard** prerequisite, so the agent's
  pre-flight now **refuses** to start it without one — see **Changed**, above. ⇒ on a
  machine without LibreHardwareMonitor there is **no agent left to keep anything
  working**, and *« installed separately »* now understates what that costs. ⛔ The
  earlier wording is named here rather than swapped out: it was true when it was
  published, and it still describes the hardware.
  ⚠️ **Re-annotated on 2026-09-14 (`dn8-7`), ⛔ nothing above erased — the refusal has itself
  fallen, on 2026-09-12.** The pre-flight no longer refuses: it **waits** for
  LibreHardwareMonitor (5 minutes by default) and then **starts the agent anyway**. ⇒ the first
  sentence of this entry is the whole truth again — without it, those two values show `--` and
  everything else keeps working. Source: `-AttenteLhm` in `tools/dn_agent_tour.ps1`, and the
  re-annotation of 2026-09-12 in `docs/journal-de-bord.md`.
  ⚠️ **The refusal itself is asserted only where it has been measured**: what has been
  checked here is that the mechanism is wired — the probe exists, it targets what the
  agent targets, and the refusal carries its own exit code. That a real tower without
  LibreHardwareMonitor refuses is closed by a Windows-side record under
  `mesures/dn7-5/`, ⛔ not by any check in this repository.

[Unreleased]: https://github.com/nasbarok/desknode/compare/v0.1.0-beta...HEAD
[0.1.0-beta]: https://github.com/nasbarok/desknode/releases/tag/v0.1.0-beta

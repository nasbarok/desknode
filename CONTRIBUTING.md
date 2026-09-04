# Contributing to DeskNode

Thanks for looking. A few things worth knowing before you spend time.

## What this project is, honestly

DeskNode is a **personal project**, published because it is clean and because someone
else might want to build one. It is maintained **best effort**:

- No SLA, no promised response time, no guaranteed individual support.
- Important bugs get fixed. Good pull requests get merged.
- Feature requests go to a backlog, and the backlog is not a promise.
- **Forking is entirely legitimate.** That is what the open license is for.

This is stated up front, before you buy anything or build anything, so nobody is
disappointed later.

**The door is not closed.** If the project ever finds funding — a manufacturer
sponsorship, a fabrication sponsorship, a specific funded request — the pace picks
back up.

## Reporting a bug

Please include:

- Which **tier** you built: board only — called **“DeskNode”** — or board + ambient
  sensors — called **“DeskNode + Ambiance”**. Both are defined in
  [`README.md`](README.md), section *« Les deux paliers matériels »* (`palier` is the
  French word this repository uses for *tier*; the README is in French, splitting it
  into a short front page and an engineering log is tracked as `dn8` — see
  [`docs/roadmap.md`](docs/roadmap.md)).
- Whether **LibreHardwareMonitor** is installed (it changes what the CPU and disk
  cells can show).
- Your **DeskNode version**. ⚠️ There is **no version shown on the display** yet. The
  device identifies its firmware by a git SHA printed on the **serial console at boot**:

  ```
  I (783) app_init: Project name:     desknode
  I (783) app_init: App version:      6a91fa3
  ```

  The banner is printed **only at boot**, so reading it means restarting the board
  while a serial terminal is attached at **115200 baud**. The port is `COM<n>` on
  Windows (usually `COM3`) and `/dev/ttyACM0` on Linux/WSL.

  The tool shipped in this repository does both steps in one command — it pulses
  RTS to restart the board, then captures the banner:

  ```
  python3 tools/dn_console.py --reset --port COM3        # Windows
  python3 tools/dn_console.py --reset                    # Linux/WSL (default port)
  ```

  ⚠️ Without `--reset` it attaches to an already-running board, and **the banner
  will never appear** — it was printed before you connected. Pressing the physical
  RESET button also works, but it re-enumerates USB and drops the terminal.

  Two other terminals can read the same line, with caveats worth knowing before you
  reach for them: `idf.py monitor` needs a full ESP-IDF install *and* a configured
  build (`sdkconfig`, `build/` and `managed_components/` are not in the clone), and
  `python3 -m serial.tools.miniterm <port> 115200` needs `pyserial`
  (`python3 -m pip install --user pyserial`) — note `python3`, since plain `python`
  is unbound on Debian, Ubuntu and WSL.

  ⚠️ **The SHA is only a SHA when the firmware was built from a git checkout.**
  Nothing in `firmware/desknode/sdkconfig.defaults` pins a project version, so
  ESP-IDF derives it from git: a build made from a downloaded ZIP (no `.git`) prints
  `App version: 1`, and a build made from a modified tree prints `<sha>-dirty`. All
  three are useful — just say which one you saw.

  A version displayed on the device itself, and a release tag, are still to come
  (`dn8` — see [`docs/roadmap.md`](docs/roadmap.md)).
- Your **Windows version**, and the make of your GPU. ⚠️ GPU metrics come from
  **AMD only** today: NVIDIA is **not implemented** — there is no NVML in the agent
  — and Intel Arc and integrated GPUs are untested. If yours shows `--`, that is
  expected rather than a bug, but the make is still worth telling us.
- Serial console output if you have it, and the steps to reproduce.

Two things are already known, so no need to report them:

- For roughly **40 seconds after a cold start**, touch input can be unreliable.
  The cause is not yet understood.
- Opening a detail page takes **335.8 ms** on average — n = 80, spread 281.2 to
  400.9 — where the target was 300 ms.

## Pull requests

Contributions are welcome. Two practical points:

1. **A CLA is required** on your first pull request, and **a bot handles it**: it
   comments on the pull request with a link, you reply once with the sentence it gives
   you, and the signature is recorded in `.github/cla-signatures.json`. The document
   you are agreeing to is [`CLA.md`](CLA.md), and one signature covers every pull
   request you open afterwards. It exists so the project keeps the ability to relicense
   later — without it, the license is frozen the moment the first contribution is
   merged, and a commercial arrangement with a manufacturer would become impossible.
   You keep the copyright on your work.

   ⚠️ **Two things about that bot are written down rather than glossed over.** The
   workflow is [`.github/workflows/cla.yml`](.github/workflows/cla.yml) and it pins
   `contributor-assistant/github-action@v2.6.1`. That action's repository is
   **archived** — last push 2026-03-23, last release `v2.6.1` of 2024-09-26, measured
   against the GitHub API on 2026-09-02. It still runs; it is simply no longer
   maintained, and the version is pinned rather than floating so that what runs is what
   is written here. It was watched running on an internal pull request on
   2026-09-02: it commented, it linked to `CLA.md`, and it created the signature
   store. And it has never been exercised by an **outside** contributor, because this
   repository has no fork and a single collaborator, so no such pull request can exist
   yet: proving it against a real external contributor is carried by `dn8` — see
   [`docs/roadmap.md`](docs/roadmap.md).

   ⚠️ **The check will be red on your pull request until you sign, and that is the
   point** — a CLA gate that stayed green would gate nothing. Post the sentence the
   bot gives you and it turns green; comment `recheck` if it does not pick it up.
2. **Match the license of the area you are touching.** Firmware is GPL-3.0-or-later,
   the agent is MIT, documentation is CC-BY-SA-4.0. See
   [`LICENSING.md`](LICENSING.md).

## Conventions in this repository

- **Measure, never assume.** Claims in this repository are backed by a number or
  explicitly marked as unmeasured. Please keep it that way.
- **Annotate, do not erase.** When something turns out to be wrong, the correction is
  written next to the original rather than replacing it. The history of what was
  believed is part of the documentation.
- `mesures/` holds the raw measurement record. It is deliberately kept — it is the
  evidence behind the numbers.

  ⚠️ **Extended on 2026-09-04 (`dn5-3`): the author's machine is still named in this
  tree, in places that are kept on purpose. Here is the whole picture, measured.**

  Nothing in this repository still *depends* on one particular machine. What remains
  are names, and each kind is kept for a different reason.

  **The instrument, stated — a count without its pattern means nothing.** Every number
  below comes from, on the tree as it stood on **2026-09-04**:

  ```
  git grep -n -I -E 'nasbarok|naoua|~/projects|wsl\.localhost' HEAD --
  ```

  🔴 **Two counts, because the work changed one of them — and running the command
  today gives you the second, not the first.** Saying only the "before" number would
  publish a figure this tree refutes.

  | class | before → after (files) | before → after (sites) | what it is | why it is what it is |
  |---|---:|---:|---|---|
  | 1. functional dependency | **3 → 0** | **4 → 0** | tools that could not run from a clone | 🔴 **the only class that was a defect — and it is now empty** |
  | 2. usage example | 18 → 19 | 39 → 50 | Windows recipes, docstrings, comments | ✅ each one that *names* the machine now **declares itself as an example** at the point where it is read, with the command that gives you your own path. ⚠️ **It grew, and that is the fix working, not regressing:** every declaration written next to a path is itself a line carrying the pattern |
  | 3. generation trace | 5 → 5 | 5 → 5 | the `* Opts:` line in `firmware/…/fonts/dn_font_*.c` | 🔴 **kept, untouched** — see below |
  | 4. evidence record | 111 → 121 | 1 264 → 1 350 | `mesures/` — captured console output | 🔴 **kept, untouched** — rewriting it would falsify the record. ⚠️ **It grew too**, for the same reason as class 2: the measurements proving this very change are themselves captures, and they are kept like every other one |
  | 5. the name *is* the subject | 2 → 4 | 11 → 17 | see the declared exclusions below | ⚠️ **excluded, and the exclusion is written**. 🔴 **Corrected at the code review of 2026-09-04 — this row read `2 → 2` / `11 → 11`, and the original figures are kept above rather than replaced.** Two files were booked as *usage examples* while being, by this table's own definition, pages whose subject **is** the pattern: this file, and the instrument that produces these counts. An exclusion that is not written is the thing this row exists to prevent |
  | **total** | **139 → 149** | **1 323 → 1 422** | | |

  ⚠️ **Do not treat any of these as a fixed number.** They move whenever a declaration
  is added, and a declaration is exactly what this repository asks for. What is stable
  is the **first row**: no tool depends on one particular machine. ⚠️ A different
  pattern also returns different numbers — `nasbarok` alone, the one earlier notes
  used, returns **120 files**. Neither pattern is wrong; they measure different things,
  and that is why the pattern is always written next to the count.

  🔴 **Corrected at the code review of 2026-09-04, and the mechanism is worth more than
  the number.** This line published **110**, and the line above it published `395 files`:
  both were true — of the tree **before this work committed its own captures** — while the
  command printed next to them says `HEAD`. A figure taken at one commit and handed to the
  reader with a command that resolves at another **is refuted by the tree that ships it**,
  which is exactly the bar stated further down this file. ⛔ The old figures are not erased;
  they are named here as what they were.

  **What `mesures/` actually costs, since it is kept on purpose.** As of **2026-09-04**,
  after the code review of that day, it holds **406 files** and **10 016 839 bytes** — that is
  **10.02 MB** in decimal units, or **9.55 MiB** in binary ones. *(Before the review's own
  captures were added it held 395 files / 9 900 692 bytes; that figure is kept rather than
  replaced, and it is why the sentence now says which tree it counts.)* ⚠️ Those are the **same number of bytes** written in two
  different units, ⛔ not two different measurements; earlier notes in the planning
  repository quoted *320 files / 9.6 MB*, which is simply older. Reproduce it with
  `git ls-tree -r -l HEAD mesures/`.

  **Why the five font files are never rewritten.** `firmware/desknode/main/fonts/`
  holds five generated C files, and each carries a line beginning `* Opts:` that
  records **the exact `lv_font_conv` command that actually produced the file** —
  including the absolute output path it was written to. That line is *provenance*: it
  is how anyone can regenerate the same font and get the same bytes. Rewriting it to
  hide a directory name would leave a command that was never run. Same reasoning as
  `mesures/`, different artefact: `mesures/` is **the evidence behind a number**, a
  font header is **the command behind a file**. Neither is decoration, and neither is
  edited.

  **The declared exclusions**, because an exclusion that is not written is a lie
  of omission. ⚠️ **This list said "the two declared exclusions" until the code review of
  2026-09-04 — the wording is corrected rather than the count quietly grown, because two
  more files belong here and were being counted as usage examples:**

  - `.github/workflows/cla.yml` names `nasbarok` **once**, inside the URL of the CLA
    document the bot asks contributors to sign. That is a **GitHub login in a URL**,
    ⛔ not a filesystem path. Removing it breaks the bot.
  - `docs/dn5-1-ecart-promesses.md` carries **ten** occurrences because it is *the
    page that documents this very gap*. Censoring it would make the record
    unreadable.
  - **this file**, because the paragraph you are reading states the pattern, quotes it,
    and names the other exclusions. Counting those as defects would be measuring this
    page's own prose.
  - `tools/inventaire_motif_dn53.py`, the instrument that produces every number above.
    It writes the pattern in order to search for it. ⚠️ **It is deliberately outside the
    `tools/verif_*.py` glob**: `tools/run_gates.sh` discovers gates by that glob and runs
    them all, and this is not a gate — it renders no verdict on the repository, it counts.
    Run it yourself: `python3 tools/inventaire_motif_dn53.py`. It checks its own
    instrument first, against faults it re-plants on purpose, and if that check fails it
    says so **before** printing a single figure.

  **On `~/projects/desknode`.** It appears throughout the documentation and it
  **names no one** — there is no user name in it. It is this repository's
  conventional clone location, nothing more: **any path works**, and the tools no
  longer care, since each one now derives its root from its own location. Where a
  Windows recipe needs the UNC form of *your* clone, run `wslpath -w ~/projects/desknode`.
- **Nothing that is pushed lies.** The bar for publishing is *not* "every story is
  finished" — at that bar nothing would ever ship. The bar is that no file in the
  published tree makes a claim the tree itself refutes. Unfinished work may be
  pushed; an unbacked claim may not. Anything that cannot be fixed before a push is
  written down **with the marker that will fix it**, never left silent.

  ⚠️ **This rule exists because the repository broke it, and the date is on record.**
  On **2026-08-31**, commit `b524e98` published a `CONTRIBUTING.md` asking every bug
  reporter which **tier** they had built — while the `README.md` of that same commit
  contained **0** occurrences of *tier*, or of its French equivalent *palier*, across
  **173 361 bytes** — counted **as whole words**, which is the only count that means
  anything here: a naive substring `grep` returns 9, and every one of them is inside
  an unrelated French word (`entier` ×5, `boîtier` ×2, `entiers` ×1) or is `tiers`
  ×1, French for *third party*. The repository asked a question its own contents defined nowhere.

  **Three more instances of that same class** were found the day it was fixed — an
  unimplemented CLA bot, a "version displayed on the device" that does not exist, and
  a `CHANGELOG.md` claiming NVIDIA support the code refutes. The full list is in
  [`docs/dn5-1-ecart-promesses.md`](docs/dn5-1-ecart-promesses.md), which numbers
  **six** entries: those four, plus two of a different kind — a gate that is red in
  the published tree, and ~~tooling that still depends on the author's own machine~~.
  Each one names the marker that carries it.

  ⚠️ **Struck through, not deleted, on 2026-09-04.** The last clause was true when it was
  written and is not any more: no tool depends on one particular machine, as the class
  table above states and as `tools/inventaire_motif_dn53.py` re-checks on demand. ⛔ The
  count **six** is unchanged — the entry still exists, it is its *disposition* that moved
  from open to settled.

  ⛔ **This is deliberately not a git hook and not a CI job.** A hook lives in
  `.git/hooks/` and **is not cloned**, so it would guard this checkout and no one
  else's — the appearance of a guard with none of the reach. Making the repository's
  gates run without anyone thinking about it is tracked separately (`dn4-39` — see
  [`docs/roadmap.md`](docs/roadmap.md)); until then this is a convention a human
  applies, and it says so rather than pretending otherwise.

  > ⚠️ **Annotated on 2026-09-02 — half of the sentence above is now out of date, and
  > the other half is not.**
  >
  > **Still true, and it stays published: this is not a git hook.** The reason has not
  > moved — `.git/hooks/` is not cloned, so a hook would guard this checkout and no
  > one else's. Nothing in this repository writes one, and `.git/hooks/` holds nothing
  > but the samples git ships.
  >
  > **No longer true: "not a CI job".** `.github/workflows/gates.yml` now runs
  > `bash tools/run_gates.sh` on every push and every pull request. What made the
  > older sentence possible was that this repository had no remote at all; it has had
  > one since `dn5-1`, and Actions have really run on it since `dn5-2`.
  >
  > ⚠️ **What CI can and cannot see, measured rather than assumed.** **Seven** of the
  > twenty-seven gates cannot be exercised where CI runs — two read the private
  > planning repository, three need `managed_components/`, which is gitignored, one
  > reads absolute paths that exist only on the author's machine, and one needs a
  > vendor PDF that is not redistributable.
  >
  > ⚠️ **Annotated on 2026-09-04 — one clause above is no longer true, and it is
  > dated rather than rewritten.** *"one reads absolute paths that exist only on the
  > author's machine"* described `tools/verif_dossier_d5_dn45.py`. It no longer reads
  > any absolute path: it derives its root from its own location and takes
  > `--cockpit`. It is still declared, and still returns the same exit code where CI
  > runs — but now for the **same reason as the two others**: the planning repository
  > is private and is never cloned. Without it, the gate now checks the four
  > authoritative files that *are* in the clone and **prints the two it could not
  > reach**, instead of having nothing to scan.
  >
  > ⚠️ **The two counts in this paragraph — "seven" and "twenty-seven" — are known to
  > be out of date and are ⛔ deliberately not corrected here.** They belong to
  > `dn4-39`, whose table and CI they describe; they are recorded against it rather
  > than fixed in passing by an unrelated change.
  >
  > *(Corrected at the code review of
  > 2026-09-02: this said "six", omitting the PDF one — while `README.md` said
  > "seven", the declaration table holds seven entries, and the first real run
  > reported `7 NON-JOUABLE`.)* They are
  > **declared** in the runner's `NON_JOUABLES` table, each with its reason, a witness
  > path and an exact expected exit code — ⛔ not silenced, ⛔ not excluded, ⛔ no
  > `continue-on-error`. The day the witness appears, the gate is played again.

## Commercial use

The firmware is GPL-3.0-or-later: distributing a modified version means publishing its
source. If that does not work for your situation, open an issue or get in touch — a
different arrangement can be discussed.

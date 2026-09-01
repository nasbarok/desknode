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
  French word this repository uses for *tier*; the README is in French, the split is
  tracked as `dn8`).
- Whether **LibreHardwareMonitor** is installed (it changes what the CPU and disk
  cells can show).
- Your **DeskNode version**. ⚠️ There is **no version shown on the display** yet. The
  device identifies its firmware by a git SHA printed on the **serial console at boot**:

  ```
  I (783) app_init: Project name:     desknode
  I (783) app_init: App version:      6a91fa3
  ```

  To read it, attach a serial terminal at **115200 baud** and restart the board — the
  banner is printed **only at boot**. Any of these work:
  `python3 tools/dn_console.py`, `idf.py monitor`, or
  `python -m serial.tools.miniterm <port> 115200`.
  A version displayed on the device itself, and a release tag, are still to come.
- Your **Windows version**, and your GPU (NVIDIA / AMD / Intel).
- Serial console output if you have it, and the steps to reproduce.

Two things are already known, so no need to report them:

- For roughly **40 seconds after a cold start**, touch input can be unreliable.
  The cause is not yet understood.
- Opening a detail page takes about **335 ms**, where the target was 300 ms.

## Pull requests

Contributions are welcome. Two practical points:

1. **A CLA is required** on your first pull request. A bot handles it in one click.
   It exists so the project keeps the ability to relicense later — without it, the
   license is frozen the moment the first contribution is merged, and a commercial
   arrangement with a manufacturer would become impossible. You keep the copyright on
   your work.
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
- **Nothing that is pushed lies.** The bar for publishing is *not* "every story is
  finished" — at that bar nothing would ever ship. The bar is that no file in the
  published tree makes a claim the tree itself refutes. Unfinished work may be
  pushed; an unbacked claim may not. Anything that cannot be fixed before a push is
  written down **with the marker that will fix it**, never left silent.

  ⚠️ **This rule exists because the repository broke it, and the date is on record.**
  On **2026-08-31**, commit `b524e98` published a `CONTRIBUTING.md` asking every bug
  reporter which **tier** they had built — while the `README.md` of that same commit
  contained **0** occurrences of *tier* or its French equivalent *palier*, across
  **173 361 bytes**. The repository asked a question its own contents defined nowhere.
  Three more instances of the same defect were found the day it was fixed; the full
  list, each with the marker that carries it, is in
  [`docs/dn5-1-ecart-promesses.md`](docs/dn5-1-ecart-promesses.md).

  ⛔ **This is deliberately not a git hook and not a CI job.** A hook lives in
  `.git/hooks/` and **is not cloned**, so it would guard this checkout and no one
  else's — the appearance of a guard with none of the reach. Making the repository's
  gates run without anyone thinking about it is tracked separately (`dn4-39`); until
  then this is a convention a human applies, and it says so rather than pretending
  otherwise.

## Commercial use

The firmware is GPL-3.0-or-later: distributing a modified version means publishing its
source. If that does not work for your situation, open an issue or get in touch — a
different arrangement can be discussed.

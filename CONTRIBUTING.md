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
  the published tree, and tooling that still depends on the author's own machine.
  Each one names the marker that carries it.

  ⛔ **This is deliberately not a git hook and not a CI job.** A hook lives in
  `.git/hooks/` and **is not cloned**, so it would guard this checkout and no one
  else's — the appearance of a guard with none of the reach. Making the repository's
  gates run without anyone thinking about it is tracked separately (`dn4-39` — see
  [`docs/roadmap.md`](docs/roadmap.md)); until then this is a convention a human
  applies, and it says so rather than pretending otherwise.

## Commercial use

The firmware is GPL-3.0-or-later: distributing a modified version means publishing its
source. If that does not work for your situation, open an issue or get in touch — a
different arrangement can be discussed.

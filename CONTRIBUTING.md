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

- Which **tier** you built: board only, or board + ambient sensors.
- Whether **LibreHardwareMonitor** is installed (it changes what the CPU and disk
  cells can show).
- Your **DeskNode version** — it is displayed on the device.
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

## Commercial use

The firmware is GPL-3.0-or-later: distributing a modified version means publishing its
source. If that does not work for your situation, open an issue or get in touch — a
different arrangement can be discussed.

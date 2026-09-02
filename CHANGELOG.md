# Changelog

All notable changes to DeskNode are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Work towards the first public release, `v0.1.0-beta`.

### Added

- **Licensing.** GPL-3.0-or-later for `firmware/`, MIT for `agent/`, CC-BY-SA-4.0 for
  `docs/`. See [`LICENSING.md`](LICENSING.md).
- **Third-party inventory** (`THIRD-PARTY.md`) — necessary because
  `managed_components/` is git-ignored, so the licenses DeskNode links against were
  recorded nowhere.
- **Contribution guide** (`CONTRIBUTING.md`), including the CLA requirement.
- **The CLA itself** (`CLA.md`) and the workflow that asks for it
  (`.github/workflows/cla.yml`). Until 2026-09-02 `CONTRIBUTING.md` promised that "a
  bot handles it in one click" while there was no file under `.github/` at all.
- **A gate over the promises this repository publishes**
  (`tools/verif_licences_dn52.py`, run by `tools/run_gates.sh`): licensing coverage in
  both directions, `idf_component.yml` against `THIRD-PARTY.md` in both directions, and
  every promise in the reader-facing files matched to an artifact or to a declared gap
  with a named owner.

### Changed

- **`hardware/` and `assets/` are now CC-BY-SA-4.0**, not GPL-3.0. `hardware/` is the
  measurement log of the board — documentation, the same nature as `docs/` — and
  `assets/` was covered by neither list in `LICENSING.md`, which is not the same thing
  as being covered by the fallback. See `LICENSING.md` for the reasoning and for why
  this is a correction rather than a relicensing.

### Fixed

- **The false claim that NVIDIA GPUs are covered.** NVIDIA is **not implemented**:
  there is no NVML in the agent. The claim appeared in this file and in
  `THIRD-PARTY.md`, while `agent/dn_agent.py` refuted it in writing the whole time.
  Both files now say so.
- **Numbers that were rounded now carry their measurement.** The detail-page timing is
  335.8 ms over n = 80, not "about 335 ms".

### Verified

- **Browser flashing works end to end** on the Waveshare ESP32-S3-Touch-LCD-2.8B
  (2026-08-31). Web Serial in Edge over a secure context, the four images written at
  their offsets with no merged binary, a clean reset, the USB device re-enumerating
  unchanged, and the dashboard coming back live. **No driver and no toolchain
  required.**

### Known issues

- Touch input can be unreliable for roughly **40 s after a cold start** — the whole
  I²C bus degrades during that window. Cause not yet investigated.
- Opening a detail page takes **335.8 ms** on average against a 300 ms target — n = 80,
  spread 281.2 to 400.9. Not perceptible in use, but the number does not meet the
  stated goal.
- The agent runs on **Windows only**, and its GPU readings come from **AMD only**.
  **NVIDIA is not implemented** — there is no NVML in the agent, and `pynvml` is not a
  dependency. **Intel Arc and integrated GPUs are untested** — no hardware available to
  check.
- **The display has no language selector, and that is deliberate.** One was built,
  flashed, seen working and validated, then removed: the choice belongs on the browser
  flasher, not on the panel. What ships is an interface that speaks **English by
  default**, with the language persisted per device once set. Offering the choice at
  install time is still to come (`dn7` — see [`docs/roadmap.md`](docs/roadmap.md)).
- **The CLA bot has never been exercised by an outside contributor.** This repository
  has no fork and a single collaborator, so no such pull request can exist yet. What is
  in place is the workflow and the document it points at; proving it against a real
  external contributor is carried by `dn8` — see [`docs/roadmap.md`](docs/roadmap.md).
- **One of the repository's own gates is red in the published tree**:
  `tools/verif_dossier_dn415.py`, 17 checks passing and 10 failing. All ten concern
  files of the private planning repository, which are not part of this clone. It is
  published as-is rather than hidden, and making the gates run automatically is
  `dn4-39` — see [`docs/roadmap.md`](docs/roadmap.md).
- **Four tools under `tools/` reach outside the clone**, to absolute paths that exist
  only on the author's machine, so they cannot run from a clone anywhere else.
  Removing that dependency is `dn5-3` — see [`docs/roadmap.md`](docs/roadmap.md).
- CPU temperature and fan RPM require **LibreHardwareMonitor**, installed separately
  with administrator rights. Without it those two values show `--` and everything else
  keeps working.

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

### Verified

- **Browser flashing works end to end** on the Waveshare ESP32-S3-Touch-LCD-2.8B
  (2026-08-31). Web Serial in Edge over a secure context, the four images written at
  their offsets with no merged binary, a clean reset, the USB device re-enumerating
  unchanged, and the dashboard coming back live. **No driver and no toolchain
  required.**

### Known issues

- Touch input can be unreliable for roughly **40 s after a cold start** — the whole
  I²C bus degrades during that window. Cause not yet investigated.
- Opening a detail page takes about **335 ms** against a 300 ms target. Not perceptible
  in use, but the number does not meet the stated goal.
- The agent runs on **Windows only**. NVIDIA and AMD GPUs are covered; **Intel Arc and
  integrated GPUs are untested** — no hardware available to check.
- CPU temperature and fan RPM require **LibreHardwareMonitor**, installed separately
  with administrator rights. Without it those two values show `--` and everything else
  keeps working.

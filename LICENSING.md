# Licensing

DeskNode is licensed **per file type**, which is common practice for open hardware
projects. Three licenses apply, and each one covers a clearly delimited part of the
repository.

| Path | License | File |
|---|---|---|
| `firmware/` — the ESP32-S3 firmware (C/C++) | **GPL-3.0-or-later** | [`LICENSE`](LICENSE) |
| `agent/` — the Windows telemetry agent (Python) | **MIT** | [`agent/LICENSE`](agent/LICENSE) |
| `docs/` — documentation, wiring photos, schematics, enclosure plans | **CC-BY-SA-4.0** | [`docs/LICENSE`](docs/LICENSE) |

Anything not covered above (`tools/`, `tests/`, `mesures/`, `hardware/`, and the
repository root) follows the **GPL-3.0-or-later** of the root `LICENSE`.

Copyright © 2026 Nasbarok.

## What this means for you

- **You want to build DeskNode and change it for yourself.** Do whatever you like.
  Nothing here asks you to publish anything.
- **You want to publish a modified firmware.** GPL-3.0 asks you to publish its source
  too. That is the whole point: the next person gets what you got.
- **You want to reuse the Python agent elsewhere.** It is MIT. Take it, no strings.
  That part is deliberately permissive so it can be plugged into anything.
- **You want to reuse the photos, wiring diagrams or enclosure plans.** CC-BY-SA-4.0:
  credit the source and share your version under the same terms.
- **You are a company and none of this works for you.** Get in touch — a different
  arrangement is possible. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Binary releases

Released firmware binaries — including the ones installed by the web flasher — are
built from this repository and are covered by **GPL-3.0-or-later**. Every release
links the exact source revision it was built from.

## Third-party components

DeskNode builds on ESP-IDF, LVGL and several managed components, all under permissive
licenses. The inventory is in [`THIRD-PARTY.md`](THIRD-PARTY.md).

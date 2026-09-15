# Licensing

DeskNode is licensed **per file type**, which is common practice for open hardware
projects. Three licenses apply, and each one covers a clearly delimited part of the
repository.

| Path | License | File |
|---|---|---|
| `firmware/` — the ESP32-S3 firmware (C/C++) | **GPL-3.0-or-later** | [`LICENSE`](LICENSE) |
| `agent/` — the Windows telemetry agent (Python) | **MIT** | [`agent/LICENSE`](agent/LICENSE) |
| `docs/` — documentation, wiring photos, schematics, enclosure plans | **CC-BY-SA-4.0** | [`docs/LICENSE`](docs/LICENSE) |
| `hardware/` — the measurement log of the board: display, I²C sensors, PC link | **CC-BY-SA-4.0** | [`docs/LICENSE`](docs/LICENSE) |
| `assets/` — mockups and other visuals | **CC-BY-SA-4.0** | [`docs/LICENSE`](docs/LICENSE) |
| `mesures/` — the measurement register: console captures, gate runs, benchmarks | **CC-BY-SA-4.0** | [`docs/LICENSE`](docs/LICENSE) |
| `installeur/` — the local install page and the script that serves it | **GPL-3.0-or-later** | [`LICENSE`](LICENSE) |

Anything not covered above (`tools/`, `tests/`, `.github/`, and the repository
root) follows the **GPL-3.0-or-later** of the root `LICENSE`.

**The Markdown files at the repository root** — `README.md`, `CONTRIBUTING.md`,
`CHANGELOG.md`, `LICENSING.md`, `THIRD-PARTY.md` and `CLA.md` — are documentation
and follow **CC-BY-SA-4.0**, like `docs/`. `LICENSE` itself and `.gitignore` are
not documentation and stay under the fallback above.

⚠️ *Extended on 2026-09-13 (`dn8-5`), and the list above is kept as it was written:
`SECURITY.md` and `CODE_OF_CONDUCT.md` joined the repository root that day, and they are
Markdown prose like the six files named above, so they follow **CC-BY-SA-4.0** too.
`CODE_OF_CONDUCT.md` is an adaptation of a text published under CC BY 4.0: where it comes
from and what was changed is written in the file itself and in
[`THIRD-PARTY.md`](THIRD-PARTY.md). The issue forms and the pull request template added
under `.github/` on the same day follow the fallback above, like the rest of that
directory.*

**Every tracked top-level directory is named by one of those two lists**, and that is
checked mechanically by `tools/verif_licences_dn52.py` — in both directions. A path
announced here that does not exist fails; a directory that exists in the tree without
being named here fails too. The second direction is the one that was broken: `assets/`
was in neither list until 2026-09-02.

Copyright © 2026 Nasbarok.

## Why `hardware/`, `assets/`, `mesures/` and the root prose are CC-BY-SA-4.0

Until 2026-09-02 this file put `hardware/` under the GPL fallback and did not mention
`assets/` at all. Both were wrong, in the same direction and for the same reason.

- `hardware/` holds three markdown files, 1.4 MB together: the measurement log of the
  display, of the I²C sensors and of the PC link. That is documentation — the same
  nature as `docs/`, which this table already puts under CC-BY-SA-4.0. Filing it under
  a software copyleft claimed something its content does not support.
- `assets/` holds one file, a mockup image. It was covered by **neither** list, and
  silence is not coverage. Filing an image under the GPL would have repeated, on a new
  path, the very mistake being corrected on `hardware/`.

### Extended on 2026-09-04, at the code review of `dn5-2` — the reason above was applied to only half the tree

⚠️ **The two paragraphs above are kept as they were written on 2026-09-02, and the
sentence they turn on is the one that forced this extension**: filing documentation
under a software copyleft *"claimed something its content does not support"*. That
reason does not stop at `hardware/`.

- `mesures/` holds **330 files**: console captures, gate runs and benchmark logs. It is
  the measurement register of the project — the same nature as `hardware/`, which the
  table above already moved for exactly that reason. It was left under the GPL fallback
  on 2026-09-02, and that was an oversight rather than a decision.
- **The Markdown files at the repository root** are prose a reader reads: the README, the
  contribution guide, the changelog, this file, the third-party inventory and the CLA.
  Filing them under a software copyleft says the same unsupported thing. `LICENSE` and
  `.gitignore` are not prose and are deliberately left where they were.

**This is a correction, not a relicensing — and the difference is a matter of fact and
of date.** Measured on 2026-09-02: this repository is `private`, it has **0 forks**,
`network_count` **0**, **one** collaborator (its author) and **no tag**. Nobody has
ever received this file under its previous terms, so no third party's rights are
touched by the change. Once the repository is public and tagged (`dn8` — see
[`docs/roadmap.md`](docs/roadmap.md)), the same edit would be a relicensing, and it
would need the agreement of everyone who had contributed in between. **That is exactly
what the CLA in [`CONTRIBUTING.md`](CONTRIBUTING.md) exists to keep possible.**

*Annotated on 2026-09-15 (`dn8-8`): that condition is now met. This repository is tagged since
`v0.1.0-beta` and public since 2026-09-15, so from that date an edit like the one described
above is a relicensing, ⛔ not a correction. On that date no outside contribution had been
merged, and the signature record of the CLA held no signature.*

## Why `installeur/` is GPL-3.0-or-later, and ⛔ not CC-BY-SA-4.0

Added on 2026-09-08, with the **first** file of the installer and ⛔ not after it. The
folder was new, and this repository checks its licence coverage **in both directions**
(`tools/verif_licences_dn52.py`): a new tracked top-level directory that nobody files here
turns a green check red. So the decision came before the writing, not after.

⚠️ **The easy answer would have been wrong.** `installeur/` holds a web page, and pages
look like the prose this file has twice moved under CC-BY-SA-4.0. It is not prose:

- **It is code.** A `.bat` that starts a local HTTP server, the Python server itself, and
  a page whose scripts probe the browser and drive the agent. The reason given above for
  moving `hardware/`, `assets/`, `mesures/` and the root Markdown — *filing documentation
  under a software copyleft claims something its content does not support* — runs the
  **other way** here: filing a program under a documentation licence would claim exactly
  as little.
- **It serves a GPL binary.** The page installs the firmware of `firmware/`, which is
  GPL-3.0-or-later, and the *Binary releases* section below already says released firmware
  binaries — *including the ones installed by the web flasher* — carry that licence. The
  installer is the thing that hands it over; putting the deliverer under a licence weaker
  than the delivery would be an odd place to draw the line.
- **It is ⛔ not `agent/`.** `agent/` is deliberately MIT so it can be plugged into
  anything. The installer is not a component anybody would embed elsewhere — it exists to
  install *this* firmware — so the argument that earned `agent/` its permissive licence
  does not reach it.

⇒ It follows the root `LICENSE`, like `tools/`, and it is named in the **table** rather
than left to the fallback sentence: a folder a reader will actually open deserves a row
they can find, ⛔ not a silence that happens to be covered.

## What this means for you

- **You want to build DeskNode and change it for yourself.** Do whatever you like.
  Nothing here asks you to publish anything.
- **You want to publish a modified firmware.** GPL-3.0 asks you to publish its source
  too. That is the whole point: the next person gets what you got.
- **You want to reuse the Python agent elsewhere.** It is MIT. Take it, no strings.
  That part is deliberately permissive so it can be plugged into anything.
- **You want to reuse the documentation, the measurement log, the photos, the wiring
  diagrams, the enclosure plans, the mockups or the measurement register** — `docs/`,
  `hardware/`, `assets/`, `mesures/`, and the Markdown at the root.
  CC-BY-SA-4.0: credit the source and share your version under the same terms.
- **You are a company and none of this works for you.** Get in touch — a different
  arrangement is possible. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Binary releases

Released firmware binaries — including the ones installed by the web flasher — are
built from this repository and are covered by **GPL-3.0-or-later**. Every release
links the exact source revision it was built from.

## Third-party components

DeskNode builds on ESP-IDF, LVGL and several managed components, all under permissive
licenses. The inventory is in [`THIRD-PARTY.md`](THIRD-PARTY.md).

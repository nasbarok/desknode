# Changelog

All notable changes to DeskNode are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Work towards the first public release, `v0.1.0-beta`.

### Added

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
  both directions, `idf_component.yml` against `THIRD-PARTY.md` in both directions, and,
  in the reader-facing files, outbound links, quoted section titles, cited tool flags,
  roadmap markers, announced counts, the CLA artifact — the workflow, its pinned
  version, the document it makes you sign, and the named owner of the gap it leaves —
  and the rule that a NVIDIA claim is **not implemented** unless the agent says so.
  It does **not** check every promise in prose; the list above is what it checks, and
  the tool's own header says what it deliberately does not.

### Changed

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
  default**; the language can be changed from the serial console (`langue fr`) and is
  then persisted on the device. Offering the choice at
  install time is still to come (`dn7` — see [`docs/roadmap.md`](docs/roadmap.md)).
- **The CLA bot has never been exercised by an outside contributor.** It was watched
  running on an **internal** pull request on 2026-09-02 — it commented, linked to
  `CLA.md` and created the signature store — and again on 2026-09-04, on the workflow
  as it now ships: it commented, an unrelated comment allocated **no runner at all**,
  and a `recheck` comment did. But this repository has no fork and a single
  collaborator, so no *external* pull request can exist yet. Proving it against
  a real outside contributor is carried by `dn8` — see
  [`docs/roadmap.md`](docs/roadmap.md).
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

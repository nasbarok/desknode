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

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

## What cloning this costs

Two figures, because they do not answer the same person's question. Both are what
`git clone` prints **about itself**, ⛔ not what a directory listing says afterwards.
Measured on **2026-09-05**, against `origin/main` at `7246f52`.

| you run | objects received | **received over the wire** | on disk afterwards (`.git` + working tree) | who this figure is for |
|---|---:|---:|---:|---|
| `git clone <url>` | 3 875 | **31.94 MiB** ≈ 33.5 MB | 79 848 261 B ≈ **79.8 MB** | **anyone who intends to contribute.** You get all **451** commits and both published branches, so `git log`, `git blame` and a pull request all work. |
| `git clone --depth 1 --branch main <url>` | 637 | **30.22 MiB** ≈ 31.7 MB | 77 938 430 B ≈ **77.9 MB** | **anyone who just wants to build it once.** One commit, no history — enough to compile the firmware, ⛔ not enough to open a pull request. ⚠️ "Enough to compile" is not "enough to compile offline": a cold build **needs the network**, and no local cache replaces it — see *Building the firmware* below. |

**Every column above comes from a command.** The first two are the line `git clone` prints
for itself; the last two are separate readings, because `clone` does not print them:

```
# what crosses the wire, and how many objects
git clone --progress https://github.com/nasbarok/desknode.git dn-full 2>&1 \
  | grep 'Receiving objects' | tail -1
git clone --progress --depth 1 --branch main https://github.com/nasbarok/desknode.git dn-shallow 2>&1 \
  | grep 'Receiving objects' | tail -1
# what landed on disk
du -sb dn-full dn-shallow
# how many commits you actually got
git -C dn-full rev-list --count HEAD ; git -C dn-shallow rev-list --count HEAD
```

⚠️ **Three things that will bite you, said rather than left to discover.**
**(1) This repository is still private.** `gh repo view` returned `visibility: PRIVATE`,
**0** forks, on 2026-09-05 — so those commands need an authenticated account with access
until the switch to public happens (`dn8` — see [`docs/roadmap.md`](docs/roadmap.md)).
**(2)** Without `| tail -1`, `grep` prints about a hundred progress lines and it is easy to
read a mid-transfer figure as the total. **(3)** `git clone` refuses a destination that
already exists, so `dn-full` and `dn-shallow` must not be there yet.

🔴 **`--depth 1` saves 1.72 MiB — 5.4 % — and that is much less than it sounds.** Comparing
like with like, both being what crosses the wire: the current version alone costs
**30.22 MiB**, and **450 further commits of history add 1.72 MiB on top**. The weight of
this repository is not in its history. A shallow clone throws away the cheap half — still
the right choice if you only want to build once, just not for the reason people expect.

⚠️ **That comparison needed a third clone, and the first attempt did not establish it.**
The full clone and the shallow one differ on **two** variables at once — depth *and* branch
scope — so their difference could not be attributed to either. A third clone,
`--single-branch --branch main` at full depth, separates them: it receives **exactly the
same 3 875 objects and 31.94 MiB** as the full clone, so the second published branch costs
**nothing** on the wire and the whole 1.72 MiB is depth. Raw output:
[`mesures/dn5-5/T9-profondeur-vs-perimetre.txt`](mesures/dn5-5/T9-profondeur-vs-perimetre.txt).

**Where the weight actually sits** — a *different* instrument, named as such: the apparent
size of the tracked files, measured on **`76b031a`**, is **46 254 844 bytes** across **603**
files, of which `docs/` is **27 992 816** (almost all wiring photographs) and `mesures/`
**10 234 634**. ⛔ Do not subtract that from the wire figures: compressed transfer and
apparent size are not the same measurement, and mixing them is the mistake this file warns
about two paragraphs down. Making the photographs lighter is tracked separately (`dn6` —
see [`docs/roadmap.md`](docs/roadmap.md)).

⚠️ **`du -sh .git` is not this number, and it is the figure that used to circulate here.**
Measured on **2026-09-05**, with the local repository at **`76b031a`**, `du -sb .git`
returns **134 406 999 bytes** — about **four times** what a clone transfers. Where the
difference goes, measured object by object:

| what the gap is made of | bytes | share |
|---|---:|---:|
| **the same content, stored differently.** The 3 875 objects a clone receives occupy **75 146 810 B** locally — **1 994** of them sitting *loose* (zlib only, no delta) and 1 881 packed — against **33 490 599 B** in the clone's freshly built pack. | 41 656 211 | 41.4 % |
| **content no clone ever receives.** **6 084** objects: **22** reachable only from local branches, and **6 062** reachable from **no ref at all** — dead history a `git gc` would drop. | 58 406 648 | 58.0 % |
| pack index and headers, `objects/info`, and the rest of `.git` (index, `logs/`, `refs/`, sample hooks, config) | 638 801 | 0.6 % |
| **total** = 134 406 999 − 33 705 339 | **100 701 660** | **100 %** |

🔴 **An earlier version of this section published two *different* causes, and both were
wrong. They are named rather than quietly swapped**, because how they were wrong is the
useful part. It said loose objects are *"never transferred"* — but **1 994 of the 2 077**
loose objects here are reachable from the published refs, so a clone does receive that
content, packed; what differs is **storage form**, not transfer. And it said the local pack
*"covers four local branches"* — but
`git rev-list --objects --all --not origin/main origin/dn4-5-le-module-vit-tout-seul`
returns **22** objects, not ~4 000; the pack's 6 001 extra objects are reachable from no ref
at all. Every set membership above is decided by a printed command, in
[`mesures/dn5-5/T8-decomposition-ecart-REFUTE-T3.txt`](mesures/dn5-5/T8-decomposition-ecart-REFUTE-T3.txt).

🔴 **And why the wrong version looked convincing is worth more than the correction.** It
closed to the byte, and read that as proof. It is not. `pack + loose + the rest = .git` is a
**partition identity**: every byte falls in exactly one bucket, so the sum equals the total
*whatever label you put on the buckets*. **A closure to the byte can falsify no attribution
at all.** What is falsifiable is which object belongs to which set — which is what the table
above is built from, one command per row.

⚠️ **This split describes one machine at one commit, ⛔ not a property of the project.**
A `git gc` here would move most of it.

⚠️ **`git count-objects -v` and `du -sb` do not measure the same thing**, and mixing them
invents about **5.3 MiB** out of nothing — an early draft of the table above did exactly
that and came out with a *negative* remainder. `du -sb` reports **apparent size**;
`count-objects` reports **disk space consumed**, in **KiB**, with each loose object rounded
up to a 4 KiB block. The table is measured end to end with `du -sb`. The two original clone
runs are in
[`mesures/dn5-5/T1-clone-complet.txt`](mesures/dn5-5/T1-clone-complet.txt) and
[`mesures/dn5-5/T2-clone-depth1.txt`](mesures/dn5-5/T2-clone-depth1.txt), and the first,
refuted decomposition is kept unedited in
[`mesures/dn5-5/T3-ecart-du-vs-clone.txt`](mesures/dn5-5/T3-ecart-du-vs-clone.txt).

⚠️ `size-pack` (**82.74 MiB**, from `git count-objects -vH`) is a third answer to a third
question — *what does the local pack weigh* — and it is not the price of a clone either.
Three instruments, three numbers, one of which is the one you pay.

⚠️ **Every figure in this section names the commit it was taken on** — `7246f52` for what
the clones received, `76b031a` for what the tree and the local `.git` hold. That is
deliberate, and it replaces a rule this file tried first and could not keep: *"publish the
figure the tree carrying it returns"* is a **fixed point**, not a rule, because the size of
the tree includes this very file, whose size depends on the figure written in it. An anchor
can be re-run exactly; a promise of freshness cannot. ⇒ the tree carrying this sentence is
one commit further along, and slightly larger than the figures above say.

⚠️ **None of these is a fixed number**, for the same reason as every other figure in this
file: they move with the next commit. What is stable is which instrument answers which
question, and each command is printed above so you can take your own reading.

## Reporting a bug

Please include:

- Which **tier** you built: board only — called **“DeskNode”** — or board + ambient
  sensors — called **“DeskNode + Ambiance”**. Both are defined in
  [`docs/journal-de-bord.md`](docs/journal-de-bord.md), section *« Les deux paliers matériels »* (`palier` is the
  French word this repository uses for *tier*; the README is in French, splitting it
  into a short front page and an engineering log is tracked as `dn8` — see
  [`docs/roadmap.md`](docs/roadmap.md)).
  ⚠️ *Annotated on 2026-09-13: this pointer named the root `README.md`, which was the
  engineering log until that day. The log moved to `docs/journal-de-bord.md` **byte for
  byte** (13 links rebased, nothing else), so the section is there, unchanged. The sentence
  above about splitting it is kept as written — the split is now done: the root `README.md`
  is a short front page in English, which names both tiers as well.*
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

## Building the firmware

**Where the firmware is built, stated — because until 2026-09-04 nothing in this
repository said it.** The ESP-IDF version was published, and so were the Ubuntu
prerequisites; the *platform* was not, in any file. This section is that statement.

**Supported: Linux, including Ubuntu under WSL2.** It is the only platform this project
has ever built the firmware on, and the build itself is measured rather than assumed —
see the figures below.

⚠️ **Corrected at the code review of 2026-09-04, and the original wording is kept rather
than replaced.** It read *"That is the only platform the firmware has ever been built on,
and it is **measured** rather than assumed"*. The **build** is measured; the claim about
the **history** of every build ever made is not the kind of thing a measurement returns.
What the tree actually holds for the other platforms are *observations of absence* — the
tooling is not installed — ⛔ not attempts that failed. The distinction is the whole point
of the paragraph below, so the sentence above should not have blurred it.

**Not instructed, and each for its own reason:**

- **ESP-IDF natively on Windows: never tried.** Not "does not work" — *never tried*.
  What the tree records are observations that the tooling is **absent** on the Windows
  side (`hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md`), never the result of an
  attempt. The attempt needs someone to run the official Windows installer, and it is
  deferred rather than concluded. ⛔ Do not read the silence as a verdict either way.
- **macOS: never tried.** ESP-IDF supports it upstream; this project has no measurement.

⚠️ **Two lines elsewhere in this tree describe the Windows side and are worth reading
together rather than one at a time.** `docs/journal-de-bord.md` documents *"Voie A — build WSL, flash
depuis Windows"* as a fallback, and `tests/README.md` says the flash goes through
Windows. The **retained** working loop in `docs/journal-de-bord.md` flashes from WSL. Both paths have
been used; the difference is which one a given session had set up, ⛔ not a
contradiction about what is possible. What has never varied is the half this section is
about: **the build is done on Linux/WSL, on every path.**

**The commands live in `docs/journal-de-bord.md`, and this section deliberately does not repeat them.**
Install ESP-IDF once with *Installation — une seule fois*, then use *Toolchain / build &
flash* for the per-shell sequence. ⚠️ `docs/journal-de-bord.md` is in French; these three lines are what
you need from it, and they are the part that is easy to get wrong:

```bash
. $HOME/esp/esp-idf/export.sh   # once per shell — IDF_PATH does not persist
cd firmware/desknode            # ⛔ NOT the repository root: the ESP-IDF project lives here
idf.py set-target esp32s3 && idf.py build
```

⚠️ *Annotated on 2026-09-13: the four pointers in this section, and the one under
**What you need that the clone does not contain** below, named the root `README.md`. That
file was the engineering log until that day; it moved **byte for byte** to
`docs/journal-de-bord.md`, where the sections cited here are unchanged. The root `README.md`
is now a short front page, and it does not carry these commands.*

⚠️ **The tree holds two ESP-IDF projects**, and the second one matters when something
fails: `firmware/desknode` is the firmware, and `firmware/hello-desknode` is a minimal
project with **no** `idf_component.yml` — it is the control that tells a missing toolchain
apart from a missing network (see the offline section below). ⛔ Building from the
repository root builds neither.

*(This pointer was added at the code review of 2026-09-04: the section stated the platform
and its costs but gave no command and never named the working directory, so following it
literally did not produce a build.)*

**What a cold build actually costs, measured on 2026-09-04** — a fresh `git clone` into
a new directory outside any existing checkout, with no inherited `sdkconfig`:

| | |
|---|---|
| `idf.py set-target esp32s3` | **118.7 s** ⚠️ *(the duration is measured; the split between network and CMake was **not** captured — see the note under the table)* |
| `idf.py build` | **173.7 s** |
| total | **292.4 s**, exit code **0** |
| `build/desknode.bin` | **1 266 752 bytes** |
| pulled from the network | **172.5 MiB** into the project's `managed_components/` (**5 079** files) |
| written under `build/` | **201.4 MiB** (2 316 files) |
| `sdkconfig` rebuilt from `sdkconfig.defaults` | **2 010 keys** |

The clone ships **none** of that: `sdkconfig`, `managed_components/`,
`dependencies.lock` and `build/` are all gitignored, and were verified absent from the
fresh clone before the build.

⚠️ **Two clarifications added at the code review of 2026-09-04.** *(a)* The first row
originally read *"118.7 s — **most of it fetching components**"*. Only the **total** was
captured; no network/CMake split was taken, so the cause was inferred and the wording is
corrected rather than kept. *(b)* Two different directories hold **172.5 MiB** of
components and they are easy to confuse, so both are named wherever the figure appears:
the project's own `managed_components/` (**5 079** files, written by this build) and the
machine-wide component cache under `~/.cache/Espressif/ComponentManager` (**5 068**
files, shared across projects). Same byte total, two directories, ⛔ not two measurements
of one thing.

**What you need that the clone does not contain:**

1. **ESP-IDF v5.5.5** and its toolchains — roughly **3.84 GiB** for the IDF checkout
   with its 23 submodules, plus **4.30 GiB** under `~/.espressif` after
   `install.sh esp32s3`. 🔴 **Corrected at the code review of 2026-09-04; the earlier
   figure is kept rather than replaced.** This line read *"**3.73 GiB** of toolchains
   under `~/.espressif`"*, which attached the right number to the wrong directory:
   `~/.espressif/tools` is **3.73 GiB** (8 933 files), while `~/.espressif` **as a whole**
   — the toolchains plus the Python environment the installer creates beside them — is
   **4.30 GiB** (14 188 files). ⚠️ **4.30 GiB is the figure to provision a disk with**,
   because it is what actually gets written. Budget roughly **8.2 GiB** for the IDF and
   its toolchains together, before this project's own `build/` and components.
   ⚠️ **Annotated on 2026-09-13 — the two figures above are kept, and one of them is
   not what the disk holds.** Re-measured with two `du` methods and a per-entry sum
   ([`mesures/dn8-4/T1-conditions-build.txt`](mesures/dn8-4/T1-conditions-build.txt)):
   **3.84 GiB** for the IDF checkout is exact for its **apparent** size (`du -sb`, and the
   same per-entry sum); allocated on disk it is **3.94 GiB**. **4.30 GiB** for
   `~/.espressif` (and **3.73 GiB** for its `tools/`) is the sum of every file entry's
   size, which counts **81** hard-linked toolchain files more than once; what is actually
   written is **3.80 GiB** (`du -sb`, apparent) or **3.83 GiB** (`du -s --block-size=1`,
   allocated). Same file counts as on 2026-09-04 (14 188 and 8 933): nothing was cleaned
   up, the **method** differs. The full sum, with `build/` and the components, is under
   *When a starting condition is not met*, below.
2. **`IDF_PATH`, set by `export.sh` in every new shell.** Measured: it is unset in a
   fresh shell, and `firmware/desknode/CMakeLists.txt` reads it. Sourcing `export.sh`
   is not optional and is not once-per-machine — it is once per shell.
3. The Ubuntu packages listed under *Installation* in `docs/journal-de-bord.md` (the root `README.md` until 2026-09-13). All sixteen were
   verified present on the build machine on 2026-09-04.
4. **`python3`, and the `tools/` directory intact.** This one is easy to miss:
   `firmware/desknode/CMakeLists.txt` puts `tools/gen_living_pcb.py` in an
   `add_custom_target(... ALL)`, so it is part of the default target and **a cold build
   always runs it**, producing `living_pcb_v0.bin` (**614 416 bytes**). A clone with
   `tools/` removed does not build. The script itself is standard-library only — no
   network, no `subprocess`. ⚠️ *Corrected at the code review of 2026-09-04: this read
   "**every** build runs it". Being in `ALL` puts the target in every build, but the
   command attached to it only re-runs when its output is missing or the script changed —
   so an incremental build usually skips it. The practical consequence is unchanged: from
   a fresh clone, `tools/` must be there.*
5. **Network access to the Espressif component registry.** See below; this is the one
   that surprises people.

🔴 **An offline build fails, and a local component cache does not save it.** Measured on
2026-09-04 inside a network namespace with no connectivity: even with the machine's
component cache fully populated (**172.5 MiB**, **5 068** files under
`~/.cache/Espressif/ComponentManager`), `idf.py set-target` exits
**2** with:

```
NOTICE: Dependencies lock doesn't exist, solving dependencies.
ERROR: Cannot establish a connection to the component registry. Are you connected
to the internet?
URL: https://components-file.espressif.com/components/espressif/esp_io_expander_tca9554.json
```

The reason is structural rather than accidental: **`dependencies.lock` is gitignored**,
so a fresh clone has no solved dependency set and the component manager must *solve*
before it can install. Solving queries the registry for metadata, and a cache of
downloaded archives does not answer that. ⛔ So "I have the components on disk" is not
enough — the first build of a fresh clone needs to reach the network.

⚠️ **Scope of that claim, narrowed at the code review of 2026-09-04; the original wording
is kept rather than replaced.** It ended *"needs to reach the network, **whatever is
cached**"*, which is broader than what was measured. What was measured is that a cache of
downloaded **archives** does not help, however complete. ESP-IDF also supports pointing
the component manager at a **different registry** — `IDF_COMPONENT_STORAGE_URL`,
`IDF_COMPONENT_LOCAL_STORAGE_URL`, `--local-storage-url`, and a bundled component-mirror
module — and **that path has never been tried here**. So: an offline build against a
local *registry mirror* is neither confirmed nor refuted by this measurement, and anyone
who needs one should expect to be the first to walk it.

⚠️ **The toolchain is not what fails there, and that is separated rather than assumed.**
`firmware/hello-desknode` has no `idf_component.yml` and therefore no remote
dependencies; building **it** offline is the control that tells the two failures apart.

**Does the same commit give the same binary? Almost — and the exception is measured
rather than guessed.** Two independent clones of the same commit, built in different
directories on 2026-09-04, produced `desknode.bin` files of **identical size** whose
contents differ in **70 bytes out of 1 266 752** — 0.0055 %. Those 70 bytes fall in
exactly three places, and all three come from one root cause:

| offset | span | bytes that differ | what it is |
|---:|---:|---:|---|
| 113 | 7 | **5** | `esp_app_desc_t.time` — **the wall-clock time of the build** (`13:47:30` vs `14:04:28`; the two `:` coincide, which is why 5 of the 7 positions differ. The `date` field matched — see the warning below) |
| 176 | 32 | **32** | `esp_app_desc_t.app_elf_sha256` — the ELF's hash, which moves because the ELF carries that same timestamp |
| 1 266 719 | 33 | **33** | the 32-byte image SHA-256 that `esptool` appends, plus the image checksum byte immediately before it, which moves with the image |

⚠️ *Two columns, added at the code review of 2026-09-04: the table previously carried a
single `bytes` column holding the **spans** (7 / 32 / 33), which sum to 72 next to a
stated total of 70. The spans are correct; what differs inside the first one is 5 bytes,
and **5 + 32 + 33 = 70**.*

**Everything else — all the code and all the data, 99.98 % of the image — is identical
byte for byte.** That result also refutes a common suspicion worth naming: the two
clones live at *different absolute paths*, and no path appears in the diff. Build paths
are **not** baked into the flashed payload. (They are in the debug ELF, which is normal
and is not flashed.)

So if you are checking that a binary really came from this source — the thing
GPL-3.0-or-later actually asks of us — rebuild the commit and compare. ⛔ This is one
measurement, on one machine, with one IDF version; it is not a reproducible-builds
guarantee.

🔴 **What to expect to differ, corrected and widened at the code review of 2026-09-04 —
and the original sentence is kept rather than replaced.** It read *"everything must match
except those three fields"*, which is only true of a rebuild done **the same day, from a
git clone of the same commit, on the same IDF version**. That is exactly the shape of the
measurement above: the two clones were built **17 minutes apart**, so the `date` field
could not move and the rule was generalised from a case that could not exercise it.
`esp_app_desc_t` carries three more fields that move under conditions this very page
declares supported:

| offset | field | moves when |
|---:|---|---|
| 48 | `version` | you build from a **ZIP** instead of a clone (it becomes `1`) or from a **modified tree** (`<sha>-dirty`) — see the note on `project_version` earlier in this file |
| 128 | `date` | you rebuild on **any other day** |
| 144 | `idf_ver` | you build on any **other 5.5.x**, which the manifest allows |

⇒ the check that actually holds is: **rebuild from a git clone of the exact commit, on
v5.5.5, and everything must match except `esp_app_desc_t`'s build-identity fields
(`version`, `time`, `date`, `idf_ver`), the ELF hash that follows them, and the trailing
image checksum + SHA-256.** All the code and all the data must be identical. ⛔ A
difference **outside** those fields is the one that means something.

**Which ESP-IDF version is authoritative — the manifest, not the measurement.**
`firmware/desknode/main/idf_component.yml` declares `idf: "~5.5.0"`, which accepts
**5.5.0 through 5.5.x**. That constraint is the contract, and it is what the tooling
enforces. Everything published in this repository was nonetheless measured on
**v5.5.5**, and **5.5.0 to 5.5.4 have never been built here**. Both facts are true and
they answer different questions: the manifest says what is *allowed*, v5.5.5 says what
is *known to work*. If you build on anything other than v5.5.5 you are on ground this
repository has not walked — which is fine, and worth saying if you report a bug.

### When a starting condition is not met — what the failure looks like

Measured on **2026-09-13**, in throwaway copies of the repository taken **outside** any
working tree, on ESP-IDF v5.5.5. Raw output, commands and exit codes:
[`mesures/dn8-4/T1-conditions-build.txt`](mesures/dn8-4/T1-conditions-build.txt).

**(a) An ESP-IDF outside `~5.5.0` — refused, with exit code 2, by a message that never
names your version.** Provoked rather than installed: the ESP-IDF component manager
(2.5.0) takes the IDF version from `CI_TESTING_IDF_VERSION` **before** asking
`idf.py --version`, so `CI_TESTING_IDF_VERSION=5.4.0 idf.py reconfigure` on a fresh copy
plays its version check without a second ESP-IDF on disk. On a fresh copy (*copy A*), it
exits **2**, after:

```
ERROR: Version solving failed:
    - no versions of idf match ~5.5.0
    - project depends on idf (~5.5.0)
```

`CI_TESTING_IDF_VERSION=6.0.0`, run next **in the same copy A** (after that failed
reconfigure), gives the same block and the same exit code; a **second** fresh copy (*copy B*),
**without** the variable, exits **0**. ⚠️ The message names the constraint and ⛔ **never the version it
found** — read *"no versions of idf match"* as *"your ESP-IDF is not 5.5.x"*.
⚠️ **Limit, written with the measurement**: this exercises the component manager's
version check and nothing else. What a real 5.4 or 6.0 would break beyond it (APIs,
Kconfig, toolchain) is ⛔ **not** measured.

**(b) An inherited `sdkconfig` wins — silently, for the key that was measured.** In copy B,
once configured, `CONFIG_FREERTOS_HZ` was set by hand to `100` in `sdkconfig` while
`sdkconfig.defaults` says `1000`. `idf.py reconfigure` then exited **0**, printed *"Loading
defaults file …/sdkconfig.defaults..."*, emitted **no** warning — and the key was **still
`100`**. The one remedy tried — deleting `sdkconfig`, then `idf.py reconfigure` — brought it
back to `1000`. ⚠️ **Scope**: one key, one sequence; other keys and other ESP-IDF commands
were not measured. ⇒ if a change to `sdkconfig.defaults` does not seem to take effect, an
existing `sdkconfig` is the first suspect, and in that run nothing on screen said so.
⚠️ **Deleting `sdkconfig` also discards every local `menuconfig` change** you made on top
of the defaults — save what you need first.

**(c) Disk space — the sum, and the method that gives it.** After a complete build of copy
B (exit code 0, `desknode.bin` 1 266 752 bytes) — a copy that had first been reconfigured
for (a), had its `sdkconfig` edited by hand for (b), then deleted and regenerated from
`sdkconfig.defaults` before the build:

| | `du -sb` (apparent) | `du -s --block-size=1` (allocated) |
|---|---:|---:|
| `~/esp/esp-idf` | 3.84 GiB | 3.94 GiB |
| `~/.espressif` | 3.80 GiB | 3.83 GiB |
| the project's `build/` | 201.4 MiB | 209.8 MiB |
| the project's `managed_components/` | 172.5 MiB | 185.6 MiB |
| **total** | **8.01 GiB** | **8.16 GiB** |
| plus the machine-wide component cache `~/.cache/Espressif/ComponentManager` | 172.5 MiB | 185.6 MiB |
| **total with the cache** | **8.18 GiB** | **8.34 GiB** |

⇒ provision **about 8.4 GiB** for one ESP-IDF, its toolchains, and one build of this
project. **Scope of that figure**: it includes the toolchains installed by
`install.sh esp32s3` and the download archives they came from under `~/.espressif/dist`
(**0.49 GiB**), and the component cache; it excludes the clone itself (about **80 MB** — see
*What cloning this costs*). ⚠️ The per-directory figures published earlier on this page were never summed,
and one of them was not a disk measurement — see the annotation under *What you need that
the clone does not contain*.

**(d) Getting the clone — HTTPS measured, SSH not.** A full `git clone` over **HTTPS**
exited **0** in **3.2 s**, on the same `origin/main` (`7246f52`) that *What cloning this
costs* measured on 2026-09-05, with the same **3 875** objects and the same **79 848 261
bytes** on disk. ⚠️ **Two instruments, two figures, ⛔ not reconciled here**: that section
reports what `git clone` printed as **received over the wire** (**31.94 MiB**); this
measurement read the pack's size afterwards with `git count-objects -vH` (`size-pack`
**32.04 MiB**). **SSH was not measured.**

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
   store. It was watched again on 2026-09-04, on the workflow **as it now ships**,
   because the 2026-09-02 runs had been produced by an earlier version of the
   trigger: it commented again, and the two things the current version claims were
   measured rather than read — an unrelated comment allocates **no runner**, and a
   `recheck` comment does. What still has **not** been exercised is the signature
   itself: signing your own CLA proves nothing, so that step waits for a real
   outside contributor. And it has never been exercised by an **outside** contributor, because this
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
- **The published history is never rewritten.** No `git filter-repo`, no BFG, no rebase
  onto anything already pushed. Two reasons, and the second one is measured.

  **It would break every clone and every fork.** Rewriting history rewrites **every SHA**
  from the point it touches onwards. Anyone who had already cloned would find their `main`
  unrelated to this one; every SHA quoted in an issue, a commit message or a page under
  `docs/` would point at nothing; and the serial banner — which prints the build's git SHA
  and is, until `dn8`, the **only** version this device has — would name a commit that no
  longer exists. That is a cost paid by other people, for a benefit measured below at zero.

  **And the usual motive does not apply here.** People reach for a rewrite when a single
  file is too large for the host. GitHub refuses any **single file** over **100 MB**.
  Measured on **2026-09-05** on `main` at `7246f52`, the largest file in this repository is
  **5 071 848 bytes** — **5.07 MB** decimal, **4.84 MiB** binary — and it is
  `docs/cablage/2026-08-17_0012-breakout-ecarte-barrette-inseree.jpg`. That leaves **19.7×**
  of margin against the 100 MB limit (**20.7×** if you read the limit as 100 MiB). Nothing
  in this tree is anywhere near the ceiling, so a purge would buy nothing at all. Take your
  own reading with:

  ```
  # the largest file in the CURRENT version
  git ls-tree -r -l HEAD | sort -k4 -n -r | head -5
  # the largest blob ANYWHERE IN HISTORY — this is the one the argument needs, since a
  # huge file deleted long ago would still be in every clone
  git rev-list --objects --all \
    | git cat-file --batch-check='%(objecttype) %(objectsize) %(rest)' \
    | awk '$1=="blob"' | sort -k2 -n -r | head -5
  ```

  ⚠️ **The first command only inspects `HEAD`, and on its own it would not settle the
  question** — the argument is about the *history*, and a blob over 100 MB removed in an old
  commit would stay invisible to it while still being downloaded by everyone. The second one
  sweeps every object reachable from every ref. Both are printed because they answer
  different questions, and only the second one carries the claim.

  ⚠️ **Annotated on 2026-09-07 — the paragraph above stays TRUE OF THE COMMIT IT NAMES, and is
  no longer true of the working tree.** The eleven heaviest photographs were recompressed in place
  (JPEG quality 88, **no resizing**, EXIF preserved). `docs/cablage/` went from **27 860 048 bytes**
  to **15 762 150**, and the largest file in the current tree is now that same photograph at
  **2 708 418 bytes** — a **36.9×** margin against the 100 MB limit instead of 19.7×. ⛔ The
  original sentence is **not** corrected: at `7246f52` it said something true, and it is the
  measurement of that commit. Raw output:
  [`mesures/dn6-3/T7-etat-arrivee.txt`](mesures/dn6-3/T7-etat-arrivee.txt).

  ✅ **Run on 2026-09-05, the second command returns the same file**: across the whole
  history, the largest blob this repository has ever held is still those **5 071 848 bytes**.
  Nothing bigger was ever committed and later deleted, so the 19.7× margin holds for the
  *history*, not just for the current version — which is exactly what makes a purge
  pointless. Raw output:
  [`mesures/dn5-5/T10-volumetries-arbre-porteur.txt`](mesures/dn5-5/T10-volumetries-arbre-porteur.txt).

  ⚠️ **The margin quoted in this project's planning notes was `54×`, and it is corrected
  here rather than carried over.** It does not follow from either of the two numbers it was
  written next to: 100 / 4.9 = 20.4, 100 / 4.84 = 20.7, 104.86 / 4.84 = 21.7, 104.86 / 4.9
  = 21.4. None of them is 54. The **conclusion** survives with room to spare — a twentyfold
  margin makes a purge pointless either way — but the figure that ships is the measured one.
  ⛔ The original line is dated where it was written, not erased. Raw output:
  [`mesures/dn5-5/T4-volumetries.txt`](mesures/dn5-5/T4-volumetries.txt).

  ⚠️ **This is not a claim that the repository is small**, and it is a different question
  from what a clone costs — for that, see *What cloning this costs* near the top of this
  file. Making the wiring photographs lighter is real work with a real owner (`dn6` — see
  [`docs/roadmap.md`](docs/roadmap.md)); ⛔ it is not done by rewriting history.

  ⚠️ **Annotated on 2026-09-07: that work HAS NOW HAPPENED, and it made this repository BIGGER
  to clone.** The photographs were recompressed in place — the working tree dropped by
  **12 097 898 bytes**, i.e. **43.4 % of `docs/cablage/`** (⛔ not of the tree, which is a much
  larger denominator) — but the history was **not** rewritten, so the original blobs are all still
  there and eleven new ones sit on top of them. Measured with `pack.threads=1`, which is the only
  reproducible setting: the bundle of the isolated curation went from **33 548 491 bytes** to
  **43 713 244**, i.e. **+10 164 753 bytes, +30.3 %**. ⚠️ That second figure is **not** a weight
  `main` ever had: it is the bundle of a throwaway measurement commit carrying **only the eleven
  recompressed photographs**, so the number attributes the cost to the curation and to nothing
  else — and it is reproducible only with the commit **identity, dates, message and ref name** all
  pinned, as the recipe in [`mesures/dn6-3/T7-etat-arrivee.txt`](mesures/dn6-3/T7-etat-arrivee.txt)
  §2 does; a differently named ref alone moves it by 7 bytes. ⛔ Not a guarantee to the byte — a
  falsifiable one. The **conclusion** survives every one of those variations: the magnitude is 10⁷
  and the sensitivity is 10¹. ⇒ making the photographs lighter is a gain for *readers of the tree*, and a **cost** for
  *everyone who clones*. That is the price of never rewriting history, written down once with its
  number rather than left to be rediscovered. ⚠️ These four figures are **re-derived from the tree
  by `tools/verif_photos_dn63.py` (c28)**: republishing a number here ⛔ does not re-measure it, so
  it is confronted. Index and full accounting:
  [`docs/cablage/PHOTOS.md`](docs/cablage/PHOTOS.md).

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

  🔴 **Three counts now, because two separate pieces of work each moved them — and
  running the command today gives you the third.** Saying only the "before" number
  would publish a figure this tree refutes.

  ⚠️ **The third column was added on 2026-09-04 by `dn5-4`, and ⛔ the earlier two are
  kept rather than replaced.** That work measured the cold build and wrote **ten**
  capture files into `mesures/dn5-4/`. Exactly **three** of them carry the pattern, and
  all three are **raw tool output kept verbatim** — two gate run summaries and one run
  of the inventory itself. ⛔ None of the prose written by hand carries it, which is
  deliberate: a capture is never doctored, and hand-written text never re-introduces
  the pattern. That is why only row 4 moves.

  | class | files: before → after → 09-04b | sites: before → after → 09-04b | what it is | why it is what it is |
  |---|---:|---:|---|---|
  | 1. functional dependency | **3 → 0 → 0** | **4 → 0 → 0** | tools that could not run from a clone | 🔴 **the only class that was a defect — and it is now empty** |
  | 2. usage example | 18 → 19 → 19 | 39 → 50 → 50 | Windows recipes, docstrings, comments | ✅ each one that *names* the machine now **declares itself as an example** at the point where it is read, with the command that gives you your own path. ⚠️ **It grew, and that is the fix working, not regressing:** every declaration written next to a path is itself a line carrying the pattern |
  | 3. generation trace | 5 → 5 → 5 | 5 → 5 → 5 | the `* Opts:` line in `firmware/…/fonts/dn_font_*.c` | 🔴 **kept, untouched** — see below |
  | 4. evidence record | 111 → 121 → **124** | 1 264 → 1 350 → **1 446** | `mesures/` — captured console output | 🔴 **kept, untouched** — rewriting it would falsify the record. ⚠️ **It grew too**, for the same reason as class 2: the measurements proving this very change are themselves captures, and they are kept like every other one |
  | 5. the name *is* the subject | 2 → 4 → 4 | 11 → 17 → 17 | see the declared exclusions below | ⚠️ **excluded, and the exclusion is written**. 🔴 **Corrected at the code review of 2026-09-04 — this row read `2 → 2` / `11 → 11`, and the original figures are kept above rather than replaced.** Two files were booked as *usage examples* while being, by this table's own definition, pages whose subject **is** the pattern: this file, and the instrument that produces these counts. An exclusion that is not written is the thing this row exists to prevent |
  | **total** | **139 → 149 → 152** | **1 323 → 1 422 → 1 518** | | |

  ⚠️ **Re-measured on 2026-09-05 by `dn5-5`, and ⛔ no earlier column is erased — a fourth
  reading, not a replacement.** The instrument is the same
  (`python3 tools/inventaire_motif_dn53.py`), and it returned: class 1 **0 / 0** · class 2
  **20 files / 52 sites** · class 3 **5 / 5** · class 4 **133 / 1 477** · class 5
  **4 / 19** · total **162 / 1 553**.

  🔴 **Two of those sites are new, and they are this work's own:** the **clone URLs** printed
  in *What cloning this costs* above. Measured directly, and this one *is* commit-anchored:
  `git grep -c -E 'nasbarok|naoua|~/projects|wsl\.localhost' <rev> -- CONTRIBUTING.md`
  returns **5** at `7246f52` and **7** at `76b031a`. They land in **class 5**, since this
  file is a declared exclusion — and a clone URL a reader cannot copy is not a command.

  ⚠️ **That fourth reading is ⛔ NOT anchored to a commit, and saying so matters.** Unlike
  every other figure `dn5-5` published, this instrument reads
  `git ls-files --cached --others` — the **working tree** — so it counted this work's own
  captures while they were still uncommitted. ⛔ The movements in classes 2 and 4 are
  therefore **not attributed here**: the previous column was taken on a different tree, and
  explaining a delta between two trees measured at different moments would be a guess, which
  is the thing this table exists to refuse.

  ⚠️ **One site in `mesures/dn5-5/` is there by a defect, and it is named rather than
  quietly cleaned.** `mesures/dn5-5/T0-temoin-port.txt` prints a real Windows user profile
  under a caption announcing it redacted, while `T7-temoin-port.txt` prints the redacted form
  at the same place — so the witness contradicts itself when the two are read side by side.
  The cause is measured: the redaction pattern was wrong when T0 was taken and was fixed
  before T7. ⛔ **The capture is not edited** — a tool's output is never doctored — and what
  the witness actually proves is untouched, since that is `--serie COM3` and the monotonic
  counter, not a Python path. Full account:
  [`mesures/dn5-5/T10-volumetries-arbre-porteur.txt`](mesures/dn5-5/T10-volumetries-arbre-porteur.txt), § 4.

  ⚠️ **Do not treat any of these as a fixed number.** They move whenever a declaration
  is added, and a declaration is exactly what this repository asks for. What is stable
  is the **first row**: no tool depends on one particular machine. ⚠️ A different
  pattern also returns different numbers — `nasbarok` alone, the one earlier notes
  used, returns **123 files** *(it returned **120** before `dn5-4` added its
  captures on 2026-09-04; the earlier figure is kept rather than replaced).* Neither pattern is wrong; they measure different things,
  and that is why the pattern is always written next to the count.

  🔴 **Corrected at the code review of 2026-09-04, and the mechanism is worth more than
  the number.** This line published **110**, and the line above it published `395 files`:
  both were true — of the tree **before this work committed its own captures** — while the
  command printed next to them says `HEAD`. A figure taken at one commit and handed to the
  reader with a command that resolves at another **is refuted by the tree that ships it**,
  which is exactly the bar stated further down this file. ⛔ The old figures are not erased;
  they are named here as what they were.

  **What `mesures/` actually costs, since it is kept on purpose.** Measured on
  **`76b031a`** — the commit is named so the figure can be re-run rather than trusted — it
  holds **428 files** and **10 234 634 bytes**: **10.23 MB** in decimal units, or
  **9.76 MiB** in binary ones. It is the same pair the section *What cloning this costs*
  publishes, with the same anchor; ⛔ this file does not carry two values for `mesures/`. *(Five earlier figures are kept rather than replaced, because
  each was true of the tree that carried it: **395 files / 9 900 692 bytes** before the code
  review of 2026-09-04 added its own captures, then **406 files / 10 016 839 bytes** after it
  and before `dn5-4`, then **416 files / 10 116 415 bytes** after `dn5-4`'s ten cold-build
  captures and before its review added the port-possession one, then **417 files /
  10 120 981 bytes** after that review — and then **419 files / 10 133 104 bytes**, which is
  what the tree already held before the present work wrote a single line.)*

  🔴 **That last pair is the one worth reading, because it is the same defect a third time.**
  The figure published on this page was **417** while `git ls-tree -r -l HEAD mesures/` — the
  command printed a few lines below — returned **419** on the very tree that shipped the
  sentence. Two more captures had landed in between. A number is only true of one commit; the
  command beside it resolves at whichever commit you run it on, and the two drift apart the
  moment anything else is committed.

  ⇒ **The rule this file applies is an ANCHOR, and the first attempt at a rule was wrong.**
  That attempt read *"the figure published here is the one the tree carrying it returns"*.
  It cannot be kept: the size of the tree includes this very file, whose size depends on the
  figure written in it — a **fixed point**, not a rule. What works instead is to **name the
  commit each figure describes**, so a reader can re-run it exactly. ⚠️ The consequence is
  stated rather than hidden: the tree carrying this sentence is one commit further along
  than `76b031a`, and holds a few more captures. ⛔ Do not read a figure here as current;
  run the command.

  ⚠️ **This number moves every time a
  measurement is committed, which is most of them** — that is the point of the directory,
  and it is why the command that reproduces it is printed right below rather than being
  left to trust.

  ⚠️ **One of those files is bloated by a capture-harness bug, and it is named here rather
  than quietly fixed.** `mesures/dn5-4/T0-gates-avant.txt` repeats its own header **78
  times** — about **27.7 KB** of duplicate — before the real tool output starts. The
  measurement it records is intact, and no other capture is affected (the harness was
  already correct when the "after" run was taken). 🔴 **It is not being edited**, for the
  reason this directory exists at all: *a tool's output is never doctored*. It also cannot
  be re-taken — it records the state **before any writing**, and the tree has been written
  to since. ⚠️ Two consequences worth knowing when reading these numbers: the duplicate is
  counted in the byte total above, and it accounts for most of that file's hits in the
  pattern table further down — those hits are a formatting artefact, ⛔ not evidence.

  ⚠️ Those are the **same number of bytes** written in two
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

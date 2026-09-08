# Third-party components

DeskNode depends on the components below. **None of them is vendored in this
repository** — `managed_components/` is git-ignored and repopulated by
`idf.py reconfigure` from the versions pinned in
`firmware/desknode/main/idf_component.yml`, which is the single source of truth.

This file exists because that directory is ignored: without it, the licenses of what
DeskNode actually links against would be recorded nowhere.

*Inventory measured on 2026-08-31 against the resolved components.*

## Firmware

| Component | Pinned version | License |
|---|---|---|
| ESP-IDF | `~5.5.0` | Apache-2.0 |
| `espressif/esp_lcd_st7701` | `2.0.2` | Apache-2.0 |
| `espressif/esp_lcd_panel_io_additions` | `1.0.1` | Apache-2.0 |
| `espressif/esp_io_expander_tca9554` | `2.0.3` | Apache-2.0 |
| `espressif/esp_io_expander` | *(transitive)* | Apache-2.0 |
| `espressif/esp_lvgl_port` | `2.9.0` | Apache-2.0 |
| `espressif/esp_lcd_touch` | `1.2.1` | Apache-2.0 |
| `espressif/esp_lcd_touch_gt911` | `1.2.1` | Apache-2.0 |
| `espressif/cmake_utilities` | *(transitive)* | Apache-2.0 |
| `lvgl/lvgl` | `9.5.0` | MIT |
| `k0i05/esp_bme680` | `1.2.7` | MIT |
| `k0i05/esp_type_utils` | `1.2.7` | MIT |

**Apache-2.0 and MIT are both compatible with GPL-3.0-or-later**, which is why the
firmware can be distributed under the GPL. (Apache-2.0 is compatible with GPLv3 in one
direction only: Apache-2.0 code may be combined into a GPLv3 work, not the reverse.)

## Windows agent

The agent (MIT) reads system metrics through `psutil` and AMD `atiadlxx.dll`.
**NVIDIA NVML is not implemented** — the agent never links against it and `pynvml`
is not a dependency. This line said the opposite until 2026-09-02; it was wrong, and
`agent/dn_agent.py` refuted it in writing at the time it was published.

**LibreHardwareMonitor is optional and is not redistributed here.** When present, the
agent reads values it exposes; without it, CPU temperature and fan RPM simply show
`--` and everything else keeps working. LibreHardwareMonitor is published under
**MPL-2.0** — if a future release ever bundles it, the MPL conditions apply and must be
honoured. It is installed by the user, separately, today.

## Web flasher

The install page uses [ESP Web Tools](https://github.com/esphome/esp-web-tools)
(Apache-2.0), loaded from a CDN. It is not vendored either.

**Version pinned: `10.4.0`.** `installeur/index.html` loads exactly
`https://unpkg.com/esp-web-tools@10.4.0/dist/web/install-button.js?module`, and
`tools/verif_flash_dn72.py` checks that the number written here and the number
written in the page are **the same**, in both directions.

🔴 **The pin is a measurement, not a habit.** On 2026-09-08 the range form
`esp-web-tools@10` answered **HTTP 302** and redirected to `10.4.0`: writing
`@10` would silently change the code that **writes to somebody's board** the day
upstream publishes again. A version that moves on its own is not a declared
dependency.

⚠️ **This is the only remote load in `installeur/`, and it is the one place the
page contradicts its own comment** — `installeur/index.html` still says "no
library and no remote load" about its *state-probing* script, which remains
true of that script. The sentence is annotated there rather than erased, with
the exact scope of what stays true.

⚠️ **Not vendoring it is a dated choice, not an oversight.** Working offline was
downgraded from a promise to a convenience by the owner on 2026-09-08, and the
vendoring that had been *deduced* from that promise fell with it. A CDN is
therefore acceptable; what the page still owes the reader is to **say so when it
does not load**, which `#etat-cdn` does.

## Keeping this file honest

This table is checked by `tools/verif_licences_dn52.py`, run by
`tools/run_gates.sh`. The check goes **both ways**: every entry pinned in
`firmware/desknode/main/idf_component.yml` must appear here with the same version
(the manifest's `==` is stripped before comparing), and every row here must be either
pinned in the manifest, the declared alias for it (`idf` ⇄ `ESP-IDF`), or marked
*(transitive)* **and absent from the manifest**. A row marked transitive that turns up
in the manifest fails too — it would be pinned, so it would no longer be transitive.

⛔ **What the check cannot do, said here rather than left silent: it does not verify
the License column.** The only source for those is `managed_components/`, which is
git-ignored and therefore **absent from any clone**. The gate deliberately does not
read it even when it happens to be present, because a check that passes on the
author's machine and nowhere else is worse than no check at all.

**So re-check that column by hand whenever `idf_component.yml` changes**, and here is
how, because "by hand" with no procedure is a promise too. Run `idf.py reconfigure`
in `firmware/desknode/`, then read `managed_components/<owner>__<name>/LICENSE` for
each row — that directory is what the build actually links against. The registry page
for a component is a second source, not a substitute: it states the license of the
*latest* version, and this manifest pins older ones.

⛔ **No marker will automate this, and that is a conclusion rather than an omission.**
The only source is git-ignored, so a gate that read it would pass on the machine that
has it and nowhere else. The person changing `idf_component.yml` carries the re-check;
the gate above tells them the row exists, not that its license is right.

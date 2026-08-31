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

The agent (MIT) reads system metrics through `psutil`, NVIDIA NVML and AMD
`atiadlxx.dll`.

**LibreHardwareMonitor is optional and is not redistributed here.** When present, the
agent reads values it exposes; without it, CPU temperature and fan RPM simply show
`--` and everything else keeps working. LibreHardwareMonitor is published under
**MPL-2.0** — if a future release ever bundles it, the MPL conditions apply and must be
honoured. It is installed by the user, separately, today.

## Web flasher

The install page uses [ESP Web Tools](https://github.com/esphome/esp-web-tools)
(Apache-2.0), loaded from a CDN. It is not vendored either.

## Keeping this file honest

`managed_components/` is ignored, so nothing enforces this table automatically.
**Re-check it whenever `idf_component.yml` changes.**

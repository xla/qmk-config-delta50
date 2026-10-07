# Hardware profile

`delta50.json` records unknowns explicitly. Copy it to the ignored `local.json`, fill in measured values and evidence, and set `status` to `verified`. The status records your review; the tool cannot measure or authenticate the PCB.

| Field | Required evidence |
| --- | --- |
| `qmk.processor` | MCU marking or vendor schematic; exact QMK processor name |
| `qmk.bootloader` | Bootloader identification and available entry method |
| `qmk.matrix_pins.rows` | Four GPIOs in electrical row order 0–3 |
| `qmk.matrix_pins.cols` | Fourteen GPIOs in electrical column order 0–13 |
| `qmk.diode_direction` | Measured `COL2ROW` or `ROW2COL` direction |
| `qmk.eeprom` | Persistent storage driver, flash allocation where applicable |
| `qmk.features.rgblight` | Explicit `true` to configure lighting or `false` to omit it |
| `qmk.rgblight` | For lighting: `driver: "ws2812"` and measured `led_count` |
| `qmk.ws2812` | For lighting: verified `pin` and QMK `driver` |

Matrix coordinates are not GPIO names. USB identity does not identify a processor. The last physical keys in rows 0–2 map to electrical `1,13`, `2,13`, `3,13`; bottom-row gaps are intentional. Preserve the recovered coordinate ordering when measuring traces.

Each entry in `evidence` must name its source or measurement. Retain photographs, schematics, and measurement tables with the profile when available. The original VIA JSON contains none of the pin or processor information.

The current builder supports a conventional diode matrix, QMK `vendor` or `wear_leveling` EEPROM, and WS2812 RGBLight. Wear-leveling configurations must supply `driver`, `logical_size` (at least 1024 bytes), and `backing_size` (at least twice the logical size), matched to the processor's flash geometry. `vendor` uses the processor's QMK implementation; inspect the pinned platform source to establish its storage layout. Custom matrix scanners, external EEPROM devices, APA102 lighting, and custom WS2812 drivers require additional board support, not invented values in this profile.

Set `features.rgblight` to `false` and remove `rgblight` and `ws2812` entirely for a deliberately unlit build. Record that choice in `evidence.lighting`. The build emits a matching VIA definition without RGB menus; RGB keycodes in the authored FN layer have no effect in that variant.

Lighting defaults are software choices: suspend with USB, maximum brightness 120, initial brightness 60, and breathing/rainbow effects. They are not recovered vendor values. Other authored choices include 5 ms debounce, 200 ms tap-hold timing, permissive hold, and Bootmagic at matrix `0,1`.

`tests/fixtures/hardware-atmega32u4.json` is arbitrary compile-test wiring. Its processor, diode direction, and LED count are not hardware evidence for the Delta50. It is accepted only with `--compile-test`, which changes the USB identity and labels generated artifacts accordingly.

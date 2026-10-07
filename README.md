# Delta50 QMK configuration

An isolated QMK source overlay for the BeatLab Delta50: its 50-key layout, static and VIA keymaps, four layers, RGBLight controls, raw-keymap import, pinned build tooling, and validation. QMK itself is downloaded into `.build/` and is not vendored into this repository.

**The software compiles with the synthetic test profile. A firmware build for the physical Delta50 still requires its MCU, bootloader, GPIO wiring, diode direction, EEPROM configuration, and lighting hardware. These are absent from the recovered VIA definition.** The real hardware profile deliberately contains nulls; the build command rejects it until those facts are supplied. Synthetic binaries have a different USB identity and are not Delta50 firmware.

## Included code

| Path | Purpose |
| --- | --- |
| [`qmk/keyboards/beatlab/delta50/`](qmk/keyboards/beatlab/delta50/) | QMK layout template, configuration, and keymaps |
| [`hardware/delta50.json`](hardware/delta50.json) | Outstanding board-specific hardware values and evidence |
| [`via/delta50.json`](via/delta50.json) | Recovered VIA v3 definition for the existing firmware |
| [`tools/build_firmware.py`](tools/build_firmware.py) | Validate hardware, stage the keyboard, compile, and record artifacts |
| [`tools/dump_keymap.py`](tools/dump_keymap.py) | Read all 224 dynamic keycodes from the existing board |
| [`qmk-version.json`](qmk-version.json) | QMK 0.32.0 source commit and CLI version |

No custom matrix scanner is needed for a conventional GPIO diode matrix: the port uses QMK's matrix, debounce, USB, EEPROM, VIA, and RGBLight implementations. If hardware recovery identifies a different matrix or lighting controller, its driver must be implemented before this port applies.

## Keymaps

`default` is a static four-layer keymap. `via` adds persistent VIA remapping to the same initial layout. These are newly authored defaults, not a factory firmware recovery. Their base layer follows the recorded labels; layers 1–3 are new designs.

| Layer | Access | Contents |
| --- | --- | --- |
| 0 BASE | Normal operation | QWERTY; Tab on tap / left Ctrl on hold; two spacebars; Alt and GUI |
| 1 NAV | Hold either `MO(1)` key | Digits on Q–P, grave, minus, equals, backslash, Delete; navigation on A–F and H–L |
| 2 NUM | Toggle the top-left detached key | Digits on Q–P, minus, equals, backslash; the same key exits the layer |
| 3 FN | Hold bottom-right `MO(3)` | F1–F12, playback/volume, RGB toggle/mode/hue/saturation/brightness |

The remaining three detached keys retain `KC_NO`, matching the observations. The six unused electrical cells are `KC_NO` on every authored layer. See the [keymap reference](qmk/keyboards/beatlab/delta50/keymaps/default/readme.md) for control positions.

`recovered` is generated only from a full raw capture after keycode compatibility has been reviewed. It preserves all 224 values, including unused cells. It does not infer missing layers from screenshots.

## Build for the physical keyboard

Install the [QMK toolchain](https://docs.qmk.fm/newbs_getting_started) for the actual MCU. Python 3.10+ and Git are required for the build tooling; repository-only checks also work with Python 3.9.

```sh
python3 tools/setup_qmk.py
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-build.txt -r .build/qmk_firmware/requirements.txt
cp hardware/delta50.json hardware/local.json
```

Populate `hardware/local.json` from vendor source, a schematic, PCB inspection, or electrical measurements. Document the evidence and mark the profile `verified` only after completing it. The exact fields and supported drivers are in [hardware/README.md](hardware/README.md).

```sh
python tools/build_firmware.py --hardware hardware/local.json --keymap via
# Static keymap:
python tools/build_firmware.py --hardware hardware/local.json --keymap default
```

The helper checks the pinned QMK commit, rejects tracked upstream modifications, and materializes `keyboard.json` under `.build/qmk_firmware/keyboards/beatlab/delta50/`. It only replaces a generated target owned by this repository. Edit the source overlay here; staged copies are replaced on the next build. `--qmk-home PATH` selects another checkout at the pinned revision. `--prepare-only` stages the target for QMK inspection without compiling.

Successful builds place the firmware, `build.json` manifest, and matching `via.json` under `.build/firmware/hardware-profile/<keymap>/`. The manifest records the profile, QMK revision, source hashes, and artifact hashes. The generated VIA definition omits RGB menus if lighting was explicitly disabled. For existing vendor firmware, continue using the recovered `via/delta50.json`.

Build commands do not flash or communicate with the keyboard. The correct flashing transport and reset method depend on the unrecovered bootloader. Once this firmware is installed, holding physical Esc (matrix `0,1`) during connection invokes QMK Bootmagic; **Bootmagic clears EEPROM settings and enters the bootloader**. Compiled defaults do not automatically replace a valid stored VIA keymap.

## Capture and import the current keymap

The committed layer-0 observations are labels, not a complete raw backup. With the board connected, close VIA to release Raw HID, then capture its current state:

```sh
python3 -m venv .venv-hid
.venv-hid/bin/python -m pip install hidapi
.venv-hid/bin/python tools/dump_keymap.py --out data/keymap-baseline.json
python3 tools/validate.py
```

A separate HID environment avoids conflicts between the `hid` module used by QMK's CLI and the `hidapi` module used by the capture tools. The capture tool reads only VID/PID `4242:4441`, Raw HID interface `FF60:61`, VIA protocol `0x000c`, and four 4×14 layers. It refuses to overwrite an existing capture. It does not capture macros, RGB settings, or a complete EEPROM image.

Review every raw keycode against the pinned QMK revision. VIA protocol `0x000c` alone does not establish the vendor's QMK keycode version or the behavior of vendor custom keycodes. After resolving compatibility:

```sh
. .venv/bin/activate
python tools/build_firmware.py --hardware hardware/local.json --keymap recovered \
  --baseline data/keymap-baseline.json --keycodes-reviewed
```

This declares the compatibility review; the tool does not perform it or silently translate keycodes. Any vendor custom behavior needs corresponding source implementation. The generated `recovered` keymap enables VIA and replaces only the compiled initial keymap.

Read-only matrix observation remains available:

```sh
.venv-hid/bin/python tools/matrix_monitor.py
```

Firmware may restrict matrix telemetry; zero responses alone do not identify a wiring fault.

## Validation

```sh
make check
```

Checks cover VIA/QMK geometry, raw-capture structure, read-only HID behavior, incomplete hardware rejection, conflicting GPIOs, storage, RGB configuration, and generated-target ownership.

To run compile tests, install an AVR QMK toolchain and the Python build requirements, then run:

```sh
python3 tools/setup_qmk.py --avr-only
python3 tools/test_compile.py
```

These compile `default`, `via`, and `recovered` with synthetic ATmega32U4 wiring, plus a no-RGB `ROW2COL` build. The test reads the linked ELF data to verify physical key positions, layer access, unused cells, and exact raw-keycode preservation. Test outputs stay under `.build/compile-checks/`, use `FEED:5050`, and are prefixed `DO-NOT-FLASH_`. CI runs the same checks without publishing firmware artifacts. Compilation does not verify the physical Delta50.

## Recovered facts and provenance

| Property | Evidence available here |
| --- | --- |
| BeatLab / Delta; USB `4242:4441` | USB interrogation reported in the recovery conversation |
| Matrix 4×14, 50 physical keys | Recovered VIA definition and [`data/matrix.json`](data/matrix.json) |
| VIA protocol `0x000c`, four layers | Interrogation and VIA UI reported in that conversation |
| QMK RGBLight controls | VIA UI; driver, GPIO and LED count still unknown |

The VIA v3 definition was reconstructed and successfully loaded against the owner's keyboard on 2026-10-07 in the referenced ChatGPT conversation, `Find Delta50 VIA QMK Files` (`6ac46015-0498-83ec-9342-49f159cde2c4`). Its source was `/Users/xla/Downloads/delta50.json`. The layer-0 observations transcribe a screenshot from that conversation; the screenshot and complete raw keymap are not committed. Device behavior has not been reverified by these builds.

Implementation references: [QMK keyboard porting](https://docs.qmk.fm/porting_your_keyboard_to_qmk), [VIA QMK configuration](https://caniusevia.com/docs/configuring_qmk/), and the [pinned QMK source](https://github.com/qmk/qmk_firmware/tree/d55d65b77fc7d8c3ea535348f949a3a70bdb3279).

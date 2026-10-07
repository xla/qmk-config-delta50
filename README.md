# Delta50 recovered configuration

Source-controlled records for the BeatLab Delta50. The [VIA v3 definition](via/delta50.json) was reconstructed and loaded successfully in VIA against the owner's keyboard on 2026-10-07. It can be loaded through VIA's Design tab to expose the existing dynamic keymap.

This repository does **not** contain flashable firmware. The controller and PCB wiring have not been recovered. The current four-layer raw keymap was discussed in the source conversation but its dump is not available in the accessible conversation history or local files used to create this repository. Do not treat the layer-0 observations as a complete factory keymap.

## Recovered facts

| Property | Value | Evidence |
| --- | --- | --- |
| USB VID / PID | `0x4242` / `0x4441` | Device interrogation in the referenced recovery conversation |
| Manufacturer / product | BeatLab / Delta | USB identity reported in that conversation |
| VIA protocol | `0x000c` | Raw HID interrogation reported in that conversation |
| Matrix | 4 rows × 14 columns | VIA definition and matrix recovery |
| Physical keys | 50 | [Matrix record](data/matrix.json) and loaded VIA definition |
| Dynamic layers | 4 | VIA UI and prior interrogation |
| RGB | QMK RGBLight controls exposed | VIA UI; pin and LED count unknown |

The [matrix record](data/matrix.json) stores every physical position in keyboard row order. Its coordinate strings are matrix `row,col`, not physical x/y positions. The [layer-0 observations](data/layer0-observations.json) transcribe the displayed key labels from the VIA screenshot. They are not raw 16-bit keycodes. Layers 1–3 and the keycodes of unused matrix cells remain unrecorded here.

## Capture the exact current keymap

With the Delta50 connected, close VIA so it releases the Raw HID interface. Install the `hidapi` Python package in a local environment, then run:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install hidapi
.venv/bin/python tools/dump_keymap.py --out data/keymap-baseline.json
python3 tools/validate.py
```

The dump tool reads the VIA protocol, verifies four layers, and records all 224 matrix cells as raw 16-bit keycodes. It accepts only VID/PID `4242:4441` on the VIA Raw HID interface (`FF60:61`) and refuses to replace an existing file. Commit that capture as the **current recovered baseline** before changing mappings in VIA. A later VIA edit changes device storage, not this repository; repeat the capture under a new filename for each intended revision.

The tool sends only VIA read commands. It has no reset, remap, restore, bootloader, or flash path. It was tested with a simulated HID device; no live capture was possible while preparing this repository because the keyboard was not connected.

To observe matrix coordinates without changing settings:

```sh
.venv/bin/python tools/matrix_monitor.py
```

The matrix-state read may return zeros on firmware that restricts matrix telemetry. A zero response alone does not prove that keys or wiring are faulty.

## QMK target status

[`qmk/keyboards/beatlab/delta50/`](qmk/keyboards/beatlab/delta50/) contains an intentionally non-buildable `keyboard.json.incomplete` with the recovered USB identity and 50-key layout. It is **not** a QMK `keyboard.json`, and there is no `keymap.c` to compile or flash. See its readme for the remaining hardware investigation.

## Validation

```sh
python3 tools/validate.py
python3 -m unittest discover -s tests -v
```

CI checks the VIA geometry and read-only tool behavior. If a full dump is committed at `data/keymap-baseline.json`, validation checks its identity and all four 4×14 layers.

## Provenance

- Referenced ChatGPT conversation: `Find Delta50 VIA QMK Files` (`6ac46015-0498-83ec-9342-49f159cde2c4`), 2026-10-07.
- VIA JSON source: `/Users/xla/Downloads/delta50.json`, recovered and confirmed working in that conversation.
- Layer-0 labels: screenshot attached to that conversation and its interpretation. The screenshot is not committed; the JSON observations are a transcription.

The words “factory” and “default” should not be applied to the observed dynamic state without a vendor firmware or factory EEPROM image. A raw capture records what is on the device at capture time.

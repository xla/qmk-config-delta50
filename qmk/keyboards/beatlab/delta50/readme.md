# BeatLab Delta50

50 physical keys in a 4×14 electrical matrix. `keyboard.json.in` contains the recovered physical layout and identity plus authored software settings. `config.h`, `rules.mk`, and the keymaps form the source overlay. QMK generates the `LAYOUT` macro from the staged JSON; no handwritten layout header or custom scanner is needed for the supported GPIO diode matrix.

Use `tools/build_firmware.py` from the repository root to combine this overlay with an explicit hardware profile. It produces `keyboard.json` and `hardware_verified.h` in a pinned QMK checkout. This source directory is not directly buildable: processor, pins, bootloader and storage remain external inputs.

Available keymaps:

- `default`: authored QWERTY, navigation/numbers, number toggle, and function/media/RGB layers.
- `via`: the same defaults with four persistent dynamic layers and Raw HID.
- `recovered`: generated from a complete raw baseline using the build helper.

The staged keyboard builds as `beatlab/delta50:<keymap>`. Build output is not evidence that the hardware profile matches the physical keyboard. See the repository root README for setup, profiles, capture, and verification.

Once installed on matching hardware, hold physical Esc while connecting to invoke Bootmagic, clear EEPROM, and enter the configured bootloader. No software-reset keycode is assigned in the authored layers.

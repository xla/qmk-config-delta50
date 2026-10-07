# Recovered keymap

The build helper generates `keymap.c` and `rules.mk` in the staged QMK tree when invoked with `--keymap recovered --baseline PATH --keycodes-reviewed`.

The baseline must be a `delta50-via-keymap-v1` raw capture with identity `4242:4441`, VIA protocol `0x000c`, and all four 4×14 layers. Every 16-bit value is preserved, including the six unused matrix cells in each layer. VIA is enabled for this variant.

`--keycodes-reviewed` declares that the capture's keycode meanings have been checked against the pinned QMK revision. The protocol version does not prove compatibility with vendor keycode ranges or custom behavior. The generator does not translate values or implement vendor custom handlers.

No baseline is committed yet. The authored `default`/`via` keymaps are usable starting layouts once hardware is configured; they do not recover the missing layers from the device. Captures contain keycodes only, not dynamic macros, lighting settings, or the complete EEPROM state.

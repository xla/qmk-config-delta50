# BeatLab Delta50 QMK target: incomplete

`keyboard.json.incomplete` is a structured reference. It contains the recovered USB identity, matrix size, and all 50 physical-to-matrix positions. Its null hardware fields are intentional. QMK will not discover it as a buildable keyboard target.

Hardware facts still required:

1. Exact MCU/processor and compatible bootloader.
2. Four row GPIO pins and fourteen column GPIO pins, or the actual matrix driver if it is not direct GPIO.
3. Diode direction.
4. RGBLight data pin and LED count, plus any hardware-specific driver configuration.
5. EEPROM or flash layout and any non-default VIA dynamic-keymap storage settings.

After recovering these from board inspection, vendor source, or measured firmware evidence, replace the nulls with verified values in a real `keyboard.json`. Recover the complete raw keymap before creating a default `keymap.c`, then confirm each raw keycode against the QMK version used by the board. Compile and inspect the result before considering a flash. The observed VIA state may differ from the firmware's compiled defaults.

No flashing workflow is present in this repository.

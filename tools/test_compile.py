#!/usr/bin/env python3
"""Compile synthetic AVR targets and inspect their actual ELF keymap data. Never flashes."""

import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile

from build_firmware import ROOT, read_json, require


def compiled_keymap(home: Path, keymap: str, temp: Path) -> tuple:
    elf = home / f".build/beatlab_delta50_{keymap}.elf"
    symbols = subprocess.check_output(["avr-nm", "-S", "--defined-only", str(elf)], text=True)
    match = re.search(r"^([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+\w\s+keymaps$", symbols, re.MULTILINE)
    require(match is not None, "Compiled ELF has no keymaps symbol")
    address, size = (int(value, 16) for value in match.groups())
    require(size == 4 * 4 * 14 * 2, f"Expected 224 uint16_t keycodes in ELF, got {size} bytes")
    binary = temp / "text.bin"
    subprocess.run(["avr-objcopy", "-O", "binary", "--only-section=.text", str(elf), str(binary)], check=True)
    return struct.unpack("<224H", binary.read_bytes()[address:address + size])


def check_authored_keymap(home: Path, values: tuple) -> None:
    # Resolve observations using the pinned QMK constants, not a duplicate keycode table.
    constants = dict(re.findall(r"^\s*(\w+)\s*=\s*(0x[0-9A-Fa-f]+|\w+)\s*,", (home / "quantum/keycodes.h").read_text(), re.MULTILINE))

    def code(name):
        value = constants[name]
        return int(value, 16) if value.startswith("0x") else code(value)

    def observed_code(label):
        if label.startswith("TG("):
            return code("QK_TOGGLE_LAYER") | int(label[3:-1])
        if label.startswith("MO("):
            return code("QK_MOMENTARY") | int(label[3:-1])
        if label == "LCTL_T(KC_TAB)":
            return code("QK_MOD_TAP") | 0x0100 | code("KC_TAB")
        return code(label)

    observations = read_json(ROOT / "data/layer0-observations.json")["observed_layer_0"]
    physical = {tuple(map(int, pos.split(','))) for pos in observations}
    for pos, label in observations.items():
        row, col = map(int, pos.split(','))
        require(values[row * 14 + col] == observed_code(label), f"Compiled base mapping differs at {pos}: {label}")
    for layer in range(4):
        for row in range(4):
            for col in range(14):
                if (row, col) not in physical:
                    require(values[layer * 56 + row * 14 + col] == 0, f"Unused matrix cell is active: {layer}/{row}/{col}")
    require(values[2 * 56] == observed_code("TG(2)"), "Number toggle must also exit layer 2")
    for layer in (1, 2, 3):
        for row, col in ((3, 10), (3, 11), (3, 13)):
            require(values[layer * 56 + row * 14 + col] == code("KC_TRNS"), "Upper layers must preserve access to the momentary layer keys")
    require(values[56 + 2] == code("KC_1"), "NAV number row missing")
    require(values[56 + 1 * 14 + 12] == code("KC_BSLS"), "NAV backslash missing")
    require(values[3 * 56 + 2] == code("KC_F1"), "FN function row missing")


def main() -> None:
    home = Path(os.environ.get("QMK_HOME", ROOT / ".build/qmk_firmware")).resolve()
    profile = read_json(ROOT / "tests/fixtures/hardware-atmega32u4.json")
    (ROOT / ".build").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="compile-test-", dir=ROOT / ".build") as directory:
        temp = Path(directory)
        profile_path = temp / "hardware.json"
        baseline_path = temp / "baseline.json"
        raw_values = list(range(224))
        baseline = {"format": "delta50-via-keymap-v1", "vendor_id": "0x4242", "product_id": "0x4441",
                    "via_protocol": "0x000c", "matrix": {"rows": 4, "cols": 14},
                    "layers": [[[f"0x{layer * 56 + row * 14 + col:04X}" for col in range(14)] for row in range(4)] for layer in range(4)]}
        baseline_path.write_text(json.dumps(baseline))
        for keymap, rgb in (("default", True), ("via", True), ("recovered", True), ("via", False)):
            if not rgb:
                profile["qmk"]["features"]["rgblight"] = False
                profile["qmk"]["diode_direction"] = "ROW2COL"
                del profile["qmk"]["rgblight"], profile["qmk"]["ws2812"]
                profile["evidence"]["lighting"] = "Synthetic fixture with lighting disabled"
                profile["evidence"]["diode_direction"] = "Synthetic ROW2COL fixture"
            profile_path.write_text(json.dumps(profile))
            command = [sys.executable, str(ROOT / "tools/build_firmware.py"), "--hardware", str(profile_path),
                       "--qmk-home", str(home), "--keymap", keymap, "--compile-test",
                       "--output", str(ROOT / ".build/compile-checks" / ("rgb" if rgb else "no-rgb"))]
            if keymap == "recovered":
                command.extend(["--baseline", str(baseline_path), "--keycodes-reviewed"])
            subprocess.run(command, check=True)
            values = compiled_keymap(home, keymap, temp)
            if keymap == "recovered":
                require(list(values) == raw_values, "Raw keycodes changed during compilation")
            else:
                check_authored_keymap(home, values)
            print(f"ELF verified: {keymap}, RGB={rgb}, 224 keycodes", flush=True)


if __name__ == "__main__":
    main()

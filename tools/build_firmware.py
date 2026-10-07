#!/usr/bin/env python3
"""Stage and compile Delta50 QMK firmware from an explicit hardware profile."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "qmk/keyboards/beatlab/delta50"
KEYBOARD = "beatlab/delta50"
EVIDENCE_FIELDS = ("processor", "bootloader", "matrix_pins", "diode_direction", "eeprom", "lighting")


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return data


def require(condition, message: str) -> None:
    if not condition:
        raise ValueError(message)


def nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_hardware(profile: dict, compile_test: bool = False) -> dict:
    require(profile.get("format") == "delta50-hardware-v1", "Unsupported hardware profile format")
    expected = "compile-test-only" if compile_test else "verified"
    require(profile.get("status") == expected,
            f"Hardware profile must have status '{expected}'; MCU, wiring and storage remain required inputs")
    evidence = profile.get("evidence", {})
    require(isinstance(evidence, dict), "evidence must be an object")
    for field in EVIDENCE_FIELDS:
        require(nonempty(evidence.get(field)), f"Missing hardware evidence: {field}")
    hw = deepcopy(profile.get("qmk"))
    require(isinstance(hw, dict), "Missing qmk hardware object")
    required = {"processor", "bootloader", "matrix_pins", "diode_direction", "eeprom", "features"}
    allowed = required | {"rgblight", "ws2812", "board", "bootloader_defs"}
    require(required <= hw.keys() <= allowed, "Missing or unsupported qmk hardware fields")
    for field in ("processor", "bootloader"):
        require(nonempty(hw[field]), f"Missing {field}")
    require(hw["bootloader"] not in {"unknown", "none"}, "A known bootloader is required")
    require(hw["diode_direction"] in ("COL2ROW", "ROW2COL"), "Expected COL2ROW or ROW2COL")
    matrix = hw["matrix_pins"]
    require(isinstance(matrix, dict) and set(matrix) == {"rows", "cols"}, "Only direct GPIO diode matrices are supported")
    pins = []
    for axis, count in (("rows", 4), ("cols", 14)):
        values = matrix[axis]
        require(isinstance(values, list) and len(values) == count, f"Expected {count} {axis} pins in recovered matrix order")
        require(all(isinstance(p, str) and re.fullmatch(r"[A-Z][A-Z0-9]*", p) and p not in {"NO_PIN", "NONE"} for p in values),
                f"Invalid or missing {axis} GPIO pins")
        pins.extend(values)
    require(len(set(pins)) == 18, "Row and column GPIO pins must be distinct")
    eeprom = hw["eeprom"]
    require(isinstance(eeprom, dict) and eeprom.get("driver") in ("vendor", "wear_leveling"),
            "Specify persistent EEPROM: vendor or wear_leveling; other drivers need board-specific source")
    if eeprom["driver"] == "wear_leveling":
        wear = eeprom.get("wear_leveling", {})
        require(isinstance(wear, dict) and nonempty(wear.get("driver")), "Specify the wear-leveling backing driver")
        require(wear["driver"] in {"embedded_flash", "rp2040_flash", "spi_flash", "legacy"}, "Unsupported wear-leveling driver")
        for field in ("logical_size", "backing_size"):
            require(type(wear.get(field)) is int and wear[field] >= 1024, f"Specify EEPROM {field} (at least 1024 bytes)")
        require(wear["backing_size"] >= 2 * wear["logical_size"], "EEPROM backing_size must be at least twice logical_size")
    features = hw["features"]
    require(isinstance(features, dict) and set(features) == {"rgblight"} and type(features["rgblight"]) is bool,
            "Set features.rgblight explicitly to true or false")
    if features["rgblight"]:
        rgb, ws = hw.get("rgblight", {}), hw.get("ws2812", {})
        require(isinstance(rgb, dict) and rgb.get("driver") == "ws2812", "This port supports WS2812 RGBLight; other LEDs need a board driver")
        require(type(rgb.get("led_count")) is int and 1 <= rgb["led_count"] <= 255, "Specify RGBLight LED count (1..255)")
        require(isinstance(ws, dict) and ws.get("driver") in ("bitbang", "pwm", "spi", "vendor"), "Specify the WS2812 driver")
        pin = ws.get("pin")
        require(isinstance(pin, str) and re.fullmatch(r"[A-Z][A-Z0-9]*", pin) and pin not in pins,
                "WS2812 needs a valid GPIO distinct from the matrix")
    else:
        require("rgblight" not in hw and "ws2812" not in hw, "Remove rgblight and ws2812 fields when lighting is disabled")
    # Prevent an unresolved nested setting from reaching QMK's generators.
    def check_values(value):
        require(value is not None, "Hardware profile contains an unresolved null")
        if isinstance(value, dict):
            for child in value.values():
                check_values(child)
        elif isinstance(value, list):
            for child in value:
                check_values(child)
    check_values(hw)
    return hw


def keyboard_definition(hw: dict, compile_test: bool = False) -> dict:
    info = read_json(SOURCE / "keyboard.json.in")
    features = info["features"] | hw["features"]
    info.update(deepcopy(hw))
    info["features"] = features
    if features["rgblight"]:
        info["rgblight"].update({"sleep": True, "max_brightness": 120,
                               "default": {"val": 60},
                               "animations": {"breathing": True, "rainbow_mood": True, "rainbow_swirl": True}})
    if compile_test:
        info["keyboard_name"] = "Delta50 COMPILE TEST"
        info["usb"].update({"vid": "0xFEED", "pid": "0x5050"})
    return info


def via_definition(info: dict) -> dict:
    via = read_json(ROOT / "via/delta50.json")
    via.update({"vendorId": info["usb"]["vid"], "productId": info["usb"]["pid"], "name": info["keyboard_name"]})
    if not info["features"]["rgblight"]:
        via.pop("menus", None)
        via.pop("keycodes", None)
    return via


def validate_baseline(dump: dict) -> list:
    require(dump.get("format") == "delta50-via-keymap-v1", "Unsupported baseline format")
    for field, expected in (("vendor_id", "0x4242"), ("product_id", "0x4441"), ("via_protocol", "0x000c")):
        value = dump.get(field)
        require(isinstance(value, str) and value.lower() == expected, f"Baseline {field} mismatch")
    require(dump.get("matrix") == {"rows": 4, "cols": 14}, "Baseline matrix mismatch")
    layers = dump.get("layers")
    require(isinstance(layers, list) and len(layers) == 4, "Baseline must contain four layers")
    for layer in layers:
        require(isinstance(layer, list) and len(layer) == 4, "Each baseline layer must have four rows")
        for row in layer:
            require(isinstance(row, list) and len(row) == 14, "Each baseline row must have fourteen columns")
            require(all(isinstance(code, str) and re.fullmatch(r"0x[0-9a-fA-F]{4}", code) for code in row), "Baseline keycodes must be 16-bit hexadecimal strings")
    return layers


def recovered_keymap(dump: dict) -> str:
    layers = validate_baseline(dump)
    lines = ['// SPDX-License-Identifier: GPL-2.0-or-later',
             '// Raw values preserved, including the six non-physical cells per layer.',
             '// Keycode semantics must be reviewed against the pinned QMK revision.',
             '#include QMK_KEYBOARD_H', '',
             'const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {']
    for index, layer in enumerate(layers):
        lines.append(f'    [{index}] = {{')
        lines.extend('        {' + ', '.join(row) + '},' for row in layer)
        lines.append('    },')
    lines.append('};\n')
    return '\n'.join(lines)


def stage_keyboard(home: Path, info: dict, recovered: str | None = None) -> Path:
    target = home / "keyboards" / KEYBOARD
    marker = target / ".delta50-generated"
    # Only replace copies produced by this repository, never a vendor/user port.
    if target.exists() or target.is_symlink():
        require(not target.is_symlink() and marker.is_file() and marker.read_text() == str(ROOT),
                f"Refusing to replace an unmanaged keyboard directory: {target}")
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE, target)
    (target / "keyboard.json.in").unlink()
    (target / "keyboard.json").write_text(json.dumps(info, indent=2) + '\n', encoding="utf-8")
    (target / "hardware_verified.h").write_text('// Generated from an explicit hardware profile.\n#pragma once\n', encoding="utf-8")
    if recovered is not None:
        (target / "keymaps/recovered/keymap.c").write_text(recovered, encoding="utf-8")
        (target / "keymaps/recovered/rules.mk").write_text('VIA_ENABLE = yes\n', encoding="utf-8")
    marker.write_text(str(ROOT), encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hardware", type=Path, default=ROOT / "hardware/delta50.json")
    parser.add_argument("--qmk-home", type=Path, default=ROOT / ".build/qmk_firmware")
    parser.add_argument("--keymap", choices=("default", "via", "recovered"), default="via")
    parser.add_argument("--output", type=Path, default=ROOT / ".build/firmware")
    parser.add_argument("--compile-test", action="store_true", help="Accept only a synthetic test profile; use a different USB identity")
    parser.add_argument("--prepare-only", action="store_true", help="Stage the QMK target without compiling")
    parser.add_argument("--baseline", type=Path, help="Full raw capture for the recovered keymap")
    parser.add_argument("--keycodes-reviewed", action="store_true", help="Declare all captured keycodes reviewed for this QMK revision")
    args = parser.parse_args()
    try:
        profile = read_json(args.hardware)
        info = keyboard_definition(validate_hardware(profile, args.compile_test), args.compile_test)
        recovered = None
        if args.keymap == "recovered":
            require(args.baseline is not None and args.keycodes_reviewed,
                    "recovered requires --baseline and --keycodes-reviewed; protocol 0x000c does not identify keycode semantics")
            recovered = recovered_keymap(read_json(args.baseline))
        else:
            require(args.baseline is None and not args.keycodes_reviewed, "Baseline options apply only to the recovered keymap")
        home = args.qmk_home.resolve()
        require((home / "quantum/quantum.h").is_file(), "QMK source missing; run tools/setup_qmk.py first")
        version = read_json(ROOT / "qmk-version.json")
        commit = subprocess.check_output(["git", "-C", str(home), "rev-parse", "HEAD"], text=True).strip()
        require(commit == version["commit"], f"QMK revision mismatch; expected {version['commit']}, got {commit}")
        require(subprocess.run(["git", "-C", str(home), "diff", "--quiet", "HEAD", "--"]).returncode == 0,
                "QMK has tracked source or submodule changes; use an unmodified pinned checkout")
        target = stage_keyboard(home, info, recovered)
        print(f"Staged {target} ({profile['status']})", flush=True)
        if args.prepare_only:
            return 0
        qmk = shutil.which("qmk")
        require(qmk is not None, "QMK CLI missing from PATH; activate .venv first")
        cli_version = subprocess.check_output([qmk, "--version"], text=True).strip()
        require(cli_version == version["cli_version"], f"QMK CLI version mismatch; install requirements-build.txt (found {cli_version})")
        stem = f"beatlab_delta50_{args.keymap}"
        # Remove previous outputs so a failed build cannot be mistaken for a new binary.
        for ext in ("hex", "bin", "uf2"):
            (home / f"{stem}.{ext}").unlink(missing_ok=True)
        env = dict(os.environ, QMK_HOME=str(home), QMK_USERSPACE="")
        subprocess.run([qmk, "compile", "-kb", KEYBOARD, "-km", args.keymap], cwd=home, env=env, check=True)
        artifacts = [home / f"{stem}.{ext}" for ext in ("hex", "bin", "uf2") if (home / f"{stem}.{ext}").is_file()]
        require(bool(artifacts), "QMK reported success but produced no firmware artifact")
        output = args.output.resolve() / ("compile-test-only" if args.compile_test else "hardware-profile") / args.keymap
        output.mkdir(parents=True, exist_ok=True)
        hashes = {}
        for artifact in artifacts:
            name = ("DO-NOT-FLASH_" if args.compile_test else "") + artifact.name
            shutil.copy2(artifact, output / name)
            hashes[name] = hashlib.sha256(artifact.read_bytes()).hexdigest()
        manifest = {"qmk": version, "keymap": args.keymap, "hardware_profile": profile,
                    "keyboard": info, "artifacts_sha256": hashes,
                    "physical_hardware_tested": False,
                    "sources_sha256": {str(path.relative_to(target)): hashlib.sha256(path.read_bytes()).hexdigest()
                                       for path in sorted(target.rglob("*"))
                                       if path.is_file() and path.suffix in {".c", ".h", ".mk", ".json"}}}
        if args.baseline:
            manifest["baseline_sha256"] = hashlib.sha256(args.baseline.read_bytes()).hexdigest()
        (output / "build.json").write_text(json.dumps(manifest, indent=2) + '\n', encoding="utf-8")
        (output / "via.json").write_text(json.dumps(via_definition(info), indent=2) + '\n', encoding="utf-8")
        print(f"Firmware and build manifest: {output}")
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"Build stopped: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_firmware import (keyboard_definition, recovered_keymap, stage_keyboard,
                            validate_baseline, validate_hardware, via_definition)
from dump_keymap import capture
from test_read_only import FakeDevice


class FirmwareTests(unittest.TestCase):
    def setUp(self):
        self.profile = json.loads((ROOT / "tests/fixtures/hardware-atmega32u4.json").read_text())

    def test_actual_profile_cannot_build(self):
        profile = json.loads((ROOT / "hardware/delta50.json").read_text())
        with self.assertRaisesRegex(ValueError, "verified"):
            validate_hardware(profile)
        profile["status"] = "verified"
        with self.assertRaisesRegex(ValueError, "evidence"):
            validate_hardware(profile)

    def test_fixture_requires_explicit_mode(self):
        with self.assertRaisesRegex(ValueError, "verified"):
            validate_hardware(self.profile)
        hw = validate_hardware(self.profile, compile_test=True)
        info = keyboard_definition(hw, compile_test=True)
        self.assertEqual(info["usb"]["vid"], "0xFEED")
        self.assertEqual(info["usb"]["pid"], "0x5050")
        self.assertNotEqual(via_definition(info)["vendorId"], "0x4242")

    def test_missing_and_conflicting_pins_rejected(self):
        for mutation in (lambda p: p["qmk"]["matrix_pins"]["rows"].pop(),
                         lambda p: p["qmk"]["matrix_pins"]["cols"].__setitem__(0, "D0"),
                         lambda p: p["qmk"]["matrix_pins"]["cols"].__setitem__(0, None),
                         lambda p: p["qmk"]["ws2812"].__setitem__("pin", "D0")):
            with self.subTest(mutation=mutation):
                profile = deepcopy(self.profile)
                mutation(profile)
                with self.assertRaises(ValueError):
                    validate_hardware(profile, True)

    def test_identity_and_layers_cannot_be_overridden(self):
        for field, value in (("usb", {"vid": "0x1234"}), ("dynamic_keymap", {"layer_count": 1}), ("layouts", {})):
            profile = deepcopy(self.profile)
            profile["qmk"][field] = value
            with self.assertRaises(ValueError):
                validate_hardware(profile, True)

    def test_storage_must_be_persistent(self):
        self.profile["qmk"]["eeprom"]["driver"] = "transient"
        with self.assertRaisesRegex(ValueError, "persistent"):
            validate_hardware(self.profile, True)

    def test_disabled_rgb_has_no_via_lighting_menu(self):
        self.profile["qmk"]["features"]["rgblight"] = False
        with self.assertRaisesRegex(ValueError, "Remove"):
            validate_hardware(self.profile, True)
        del self.profile["qmk"]["rgblight"], self.profile["qmk"]["ws2812"]
        info = keyboard_definition(validate_hardware(self.profile, True))
        self.assertNotIn("menus", via_definition(info))
        self.assertNotIn("keycodes", via_definition(info))
        self.assertTrue(info["features"]["bootmagic"])
        self.assertEqual(info["dynamic_keymap"], {"layer_count": 4})

    def test_raw_capture_round_trip_including_unused_cells(self):
        dump = capture(FakeDevice())
        values = [f"0x{v:04X}" for v in range(224)]
        dump["layers"] = [[values[layer * 56 + row * 14:layer * 56 + (row + 1) * 14] for row in range(4)] for layer in range(4)]
        code = recovered_keymap(dump)
        self.assertEqual(re.findall(r"0x[0-9A-F]{4}", code), values)

    def test_malformed_and_wrong_device_baselines_rejected(self):
        for mutation in (lambda d: d.__setitem__("vendor_id", "0x1234"),
                         lambda d: d.__setitem__("via_protocol", "0x000b"),
                         lambda d: d["layers"].pop(),
                         lambda d: d["layers"][0][0].pop(),
                         lambda d: d["layers"][0][0].__setitem__(0, "0x10000"),
                         lambda d: d["layers"][0][0].__setitem__(0, "KC_A")):
            dump = capture(FakeDevice())
            mutation(dump)
            with self.assertRaises(ValueError):
                validate_baseline(dump)

    def test_stage_refuses_unmanaged_target_and_replaces_own_output(self):
        info = keyboard_definition(validate_hardware(self.profile, True), True)
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            target = stage_keyboard(home, info, recovered_keymap(capture(FakeDevice())))
            self.assertTrue((target / "keymaps/recovered/keymap.c").exists())
            stage_keyboard(home, info)
            self.assertFalse((target / "keymaps/recovered/keymap.c").exists())
            (target / ".delta50-generated").unlink()
            with self.assertRaisesRegex(ValueError, "unmanaged"):
                stage_keyboard(home, info)
            self.assertTrue((target / "keyboard.json").exists())

    def test_build_rejects_unknown_hardware_before_creating_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "qmk"
            result = subprocess.run([sys.executable, str(ROOT / "tools/build_firmware.py"),
                                     "--qmk-home", str(home), "--prepare-only"], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("verified", result.stderr)
            self.assertFalse(home.exists())


if __name__ == "__main__":
    unittest.main()

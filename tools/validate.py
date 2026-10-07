#!/usr/bin/env python3
"""Check recovered geometry and any captured baseline without third-party packages."""

from __future__ import annotations

import json
from pathlib import Path

from build_firmware import validate_baseline

ROOT = Path(__file__).resolve().parents[1]


def read(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def validate() -> None:
    via = read("via/delta50.json")
    matrix = read("data/matrix.json")
    observed = read("data/layer0-observations.json")
    assert via["vendorId"] == "0x4242"
    assert via["productId"] == "0x4441"
    assert via["matrix"] == {"rows": 4, "cols": 14}
    assert via["keycodes"] == ["qmk_rgblight_keycodes"]
    assert via["menus"] == ["qmk_rgblight"]
    physical = [[item for item in row if isinstance(item, str)] for row in via["layouts"]["keymap"]]
    assert physical == matrix["physical_rows"]
    assert len(physical) == 4
    coords = [item for row in physical for item in row]
    assert len(coords) == matrix["physical_key_count"] == 50
    assert len(set(coords)) == 50
    for coord in coords:
        row, col = map(int, coord.split(","))
        assert 0 <= row < 4 and 0 <= col < 14
    assert observed["status"] == "partial_observation_not_raw_dump"
    assert set(observed["observed_layer_0"]) == set(coords)
    assert observed["unobserved_layers"] == [1, 2, 3]

    # Independently reconstruct KLE geometry, including the offset macro column.
    expected_layout = []
    for y, row in enumerate(via["layouts"]["keymap"]):
        x, width = 0, 1
        for item in row:
            if isinstance(item, dict):
                x += item.get("x", 0)
                width = item.get("w", 1)
            else:
                expected_layout.append({"matrix": list(map(int, item.split(","))), "x": x, "y": y, "w": width})
                x += width
                width = 1
    qmk = read("qmk/keyboards/beatlab/delta50/keyboard.json.in")
    assert qmk["layouts"]["LAYOUT"]["layout"] == expected_layout
    assert qmk["usb"]["vid"] == via["vendorId"] and qmk["usb"]["pid"] == via["productId"]
    assert qmk["dynamic_keymap"]["layer_count"] == 4
    assert qmk["bootmagic"]["matrix"] == [0, 1]
    assert "processor" not in qmk and "matrix_pins" not in qmk

    baseline = ROOT / "data/keymap-baseline.json"
    if baseline.exists():
        dump = json.loads(baseline.read_text(encoding="utf-8"))
        validate_baseline(dump)
        print("Full four-layer raw baseline: valid")
    else:
        print("Full four-layer raw baseline: unavailable; connect board and capture")
    print("VIA definition, QMK geometry and 50-key matrix: valid")


if __name__ == "__main__":
    validate()

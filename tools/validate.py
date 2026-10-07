#!/usr/bin/env python3
"""Check recovered geometry and any captured baseline without third-party packages."""

from __future__ import annotations

import json
from pathlib import Path

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

    baseline = ROOT / "data/keymap-baseline.json"
    if baseline.exists():
        dump = json.loads(baseline.read_text(encoding="utf-8"))
        assert dump["format"] == "delta50-via-keymap-v1"
        assert dump["vendor_id"] == "0x4242"
        assert dump["product_id"] == "0x4441"
        assert dump["via_protocol"].lower() == "0x000c"
        assert dump["matrix"] == {"rows": 4, "cols": 14}
        assert len(dump["layers"]) == 4
        for layer in dump["layers"]:
            assert len(layer) == 4
            for row in layer:
                assert len(row) == 14
                assert all(isinstance(code, str) and len(code) == 6 and code.startswith("0x") and all(c in "0123456789ABCDEFabcdef" for c in code[2:]) for code in row)
        print("Full four-layer raw baseline: valid")
    else:
        print("Full four-layer raw baseline: unavailable; connect board and capture")
    print("VIA definition and 50-key matrix: valid")


if __name__ == "__main__":
    validate()

#!/usr/bin/env python3
"""Capture all Delta50 dynamic keycodes without changing keyboard state."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from via_hid import open_delta50, read_command, require_recovered_protocol

ROWS = 4
COLS = 14
LAYERS = 4


def capture(device) -> dict:
    protocol = require_recovered_protocol(device)
    count = read_command(device, 0x11)[1]
    if count != LAYERS:
        raise RuntimeError(f"Expected {LAYERS} layers; device reported {count}")
    layers = []
    for layer in range(count):
        rows = []
        for row in range(ROWS):
            keycodes = []
            for col in range(COLS):
                response = read_command(device, 0x04, layer, row, col)
                keycodes.append(f"0x{int.from_bytes(response[4:6], 'big'):04X}")
            rows.append(keycodes)
        layers.append(rows)
    return {
        "format": "delta50-via-keymap-v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "live Delta50 VIA read-only Raw HID capture",
        "vendor_id": "0x4242",
        "product_id": "0x4441",
        "via_protocol": f"0x{protocol:04X}",
        "matrix": {"rows": ROWS, "cols": COLS},
        "layers": layers,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="New JSON file; never overwritten")
    args = parser.parse_args()
    with open_delta50() as device:
        data = capture(device)
    # Exclusive creation protects an existing baseline from accidental replacement.
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")
    print(f"Captured {LAYERS} layers × {ROWS} rows × {COLS} columns to {args.out}")


if __name__ == "__main__":
    main()

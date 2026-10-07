#!/usr/bin/env python3
"""Poll the VIA matrix-state read command; never write keyboard settings."""

from __future__ import annotations

import argparse
import time

from via_hid import open_delta50, read_command, require_recovered_protocol


def pressed_positions(device) -> set[str]:
    # VIA keyboard value 0x03, offset 0. Four 14-column rows occupy 8 bytes.
    response = read_command(device, 0x02, 0x03, 0x00)
    pressed = set()
    for row in range(4):
        bits = int.from_bytes(response[3 + row * 2 : 5 + row * 2], "big")
        for col in range(14):
            if bits & (1 << col):
                pressed.add(f"{row},{col}")
    return pressed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=float, default=0.1, help="Polling interval in seconds")
    args = parser.parse_args()
    if args.interval < 0.05:
        parser.error("--interval must be at least 0.05 seconds")
    with open_delta50() as device:
        require_recovered_protocol(device)
        previous = set()
        print("Polling read-only matrix state. Press keys; Ctrl-C stops.", flush=True)
        try:
            while True:
                current = pressed_positions(device)
                for key in sorted(current - previous):
                    print(f"down {key}", flush=True)
                for key in sorted(previous - current):
                    print(f"up   {key}", flush=True)
                previous = current
                time.sleep(args.interval)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()

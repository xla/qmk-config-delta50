#!/usr/bin/env python3
"""Fetch the pinned QMK tree into .build without changing global QMK settings."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qmk-home", type=Path, default=ROOT / ".build/qmk_firmware")
    parser.add_argument("--avr-only", action="store_true", help="Fetch only LUFA/printf for the synthetic AVR compile test")
    args = parser.parse_args()
    home = args.qmk_home.resolve()
    version = json.loads((ROOT / "qmk-version.json").read_text())
    try:
        if not home.exists():
            home.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "clone", "--depth", "1", "--branch", version["tag"], version["repository"], str(home)], check=True)
        commit = subprocess.check_output(["git", "-C", str(home), "rev-parse", "HEAD"], text=True).strip()
        if commit != version["commit"]:
            raise ValueError(f"Existing QMK checkout is {commit}; expected {version['commit']}. No checkout changes made.")
        command = ["git", "-C", str(home), "submodule", "update", "--init", "--recursive", "--depth", "1"]
        if args.avr_only:
            command.extend(["lib/lufa", "lib/printf"])
        subprocess.run(command, check=True)
        print(f"Pinned QMK {version['tag']} ready at {home}")
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Setup stopped: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

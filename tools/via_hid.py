"""Small, read-only VIA Raw HID client for the recovered Delta50 identity."""

from __future__ import annotations

from contextlib import contextmanager

VID = 0x4242
PID = 0x4441
USAGE_PAGE = 0xFF60
USAGE = 0x61
REPORT_SIZE = 32

# Only VIA commands whose defined behavior reads device state are exposed.
READ_COMMANDS = {0x01, 0x02, 0x04, 0x11}


def _hid_module():
    try:
        import hid  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("Install hidapi first: python3 -m pip install hidapi") from exc
    return hid


@contextmanager
def open_delta50():
    hid = _hid_module()
    matches = [
        device
        for device in hid.enumerate(VID, PID)
        if device.get("usage_page") == USAGE_PAGE and device.get("usage") == USAGE
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one Delta50 VIA Raw HID interface; found {len(matches)}. "
            "Connect the board and close VIA before retrying."
        )
    device = hid.device()
    device.open_path(matches[0]["path"])
    try:
        yield device
    finally:
        device.close()


def read_command(device, command: int, *parameters: int) -> bytes:
    if command not in READ_COMMANDS:
        raise ValueError(f"Command 0x{command:02x} is not in the read-only allowlist")
    if any(not 0 <= value <= 255 for value in parameters):
        raise ValueError("Parameters must be bytes")
    payload = bytes([command, *parameters]).ljust(REPORT_SIZE, b"\0")
    # HID report ID 0 is the transport prefix; the VIA command is the next byte.
    written = device.write(b"\0" + payload)
    if written != REPORT_SIZE + 1:
        raise RuntimeError(f"Short HID write: {written} bytes")
    response = bytes(device.read(REPORT_SIZE, 1000))
    if len(response) != REPORT_SIZE:
        raise RuntimeError(f"Short or timed-out HID response: {len(response)} bytes")
    expected = bytes([command, *parameters])
    if not response.startswith(expected):
        raise RuntimeError(
            f"Unexpected VIA response header: {response[:len(expected)].hex()} "
            f"(expected {expected.hex()})"
        )
    return response


def protocol_version(device) -> int:
    response = read_command(device, 0x01)
    return int.from_bytes(response[1:3], "big")


def require_recovered_protocol(device) -> int:
    version = protocol_version(device)
    if version != 0x000C:
        raise RuntimeError(
            f"Expected recovered VIA protocol 0x000c; device returned 0x{version:04x}"
        )
    return version

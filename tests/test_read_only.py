import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from via_hid import read_command  # noqa: E402
from dump_keymap import capture  # noqa: E402


class FakeDevice:
    def __init__(self):
        self.commands = []
        self.pending = b""

    def write(self, packet):
        assert len(packet) == 33 and packet[0] == 0
        command = packet[1]
        self.commands.append(command)
        if command == 0x01:
            response = bytes([0x01, 0x00, 0x0C])
        elif command == 0x11:
            response = bytes([0x11, 4])
        elif command == 0x04:
            response = bytes(packet[1:5]) + bytes([0x00, 0x04])
        else:
            response = bytes(packet[1:4])
        self.pending = response.ljust(32, b"\0")
        return len(packet)

    def read(self, size, timeout):
        assert size == 32 and timeout == 1000
        return self.pending


class ReadOnlyTests(unittest.TestCase):
    def test_rejects_mutating_via_commands(self):
        device = FakeDevice()
        for command in (0x03, 0x05, 0x06, 0x0A, 0x0B, 0x13):
            with self.assertRaises(ValueError):
                read_command(device, command)
        self.assertEqual(device.commands, [])

    def test_full_matrix_capture_shape(self):
        device = FakeDevice()
        result = capture(device)
        self.assertEqual(len(result["layers"]), 4)
        self.assertEqual(result["layers"][0][0][0], "0x0004")
        self.assertEqual(device.commands.count(0x04), 4 * 4 * 14)
        self.assertEqual(set(device.commands), {0x01, 0x04, 0x11})


if __name__ == "__main__":
    unittest.main()

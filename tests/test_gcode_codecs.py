"""The bgcode G-code decoders (heatshrink, MeatPack) and the toolpath summary, on hand-made streams and on the
sliced cube fixture."""

import math
import unittest

from schlieren import bgcode
from schlieren.gcode_codecs import heatshrink_decode, meatpack_decode
from schlieren.gcode_toolpath import summarize
from tests.print_helpers import cube_bgcode

PACK = {c: i for i, c in enumerate("0123456789. \nGX")}


class Bits:
    """Writes the bit stream heatshrink reads: most significant bit first, zero padded."""

    def __init__(self):
        self.bits: list[int] = []

    def put(self, value: int, count: int) -> "Bits":
        self.bits += [(value >> (count - 1 - i)) & 1 for i in range(count)]
        return self

    def literal(self, byte: int) -> "Bits":
        return self.put(1, 1).put(byte, 8)

    def reference(self, offset: int, length: int, window=12, lookahead=4) -> "Bits":
        return self.put(0, 1).put(offset - 1, window).put(length - 1, lookahead)

    def bytes(self) -> bytes:
        padded = self.bits + [0] * (-len(self.bits) % 8)
        return bytes(int("".join(map(str, padded[i : i + 8])), 2) for i in range(0, len(padded), 8))


def meatpack(text: str) -> bytes:
    """Pack text in packing mode: two characters a byte, low nibble first, full bytes after a 15 nibble."""
    out = bytearray([0xFF, 0xFF, 251])
    chars = list(text) + ([] if len(text) % 2 == 0 else ["\n"])
    for first, second in zip(chars[::2], chars[1::2], strict=True):
        nibbles, extra = [], []
        for c in (first, second):
            if c in PACK:
                nibbles.append(PACK[c])
            else:
                nibbles.append(15)
                extra.append(ord(c))
        out.append(nibbles[0] | (nibbles[1] << 4))
        out += bytes(extra)
    return bytes(out)


class HeatshrinkTests(unittest.TestCase):
    def test_literals(self):
        bits = Bits()
        for byte in b"G1 X10":
            bits.literal(byte)
        self.assertEqual(heatshrink_decode(bits.bytes(), 6), b"G1 X10")

    def test_back_reference_copies_earlier_output(self):
        bits = Bits().literal(ord("a")).literal(ord("b")).reference(offset=2, length=6)
        self.assertEqual(heatshrink_decode(bits.bytes(), 8), b"abababab")

    def test_reference_before_the_start_reads_zeros(self):
        bits = Bits().reference(offset=4, length=3).literal(ord("z"))
        self.assertEqual(heatshrink_decode(bits.bytes(), 4), b"\0\0\0z")

    def test_window_and_lookahead_are_parameters(self):
        bits = Bits().literal(ord("a")).reference(1, 3, window=11, lookahead=4)
        self.assertEqual(heatshrink_decode(bits.bytes(), 4, 11, 4), b"aaaa")

    def test_output_is_cut_at_the_stated_size(self):
        bits = Bits().literal(ord("a")).reference(1, 10)
        self.assertEqual(heatshrink_decode(bits.bytes(), 5), b"aaaaa")

    def test_short_stream_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "ended after 2 of 9"):
            heatshrink_decode(Bits().literal(1).literal(2).bytes(), 9)


class MeatPackTests(unittest.TestCase):
    def test_packed_text(self):
        self.assertEqual(meatpack_decode(meatpack("G1 X10.50\n")), "G1 X10.50\n")

    def test_odd_length_gets_a_trailing_newline(self):
        self.assertEqual(meatpack_decode(meatpack("G1 X1")), "G1 X1\n")

    def test_characters_outside_the_alphabet_follow_as_full_bytes(self):
        self.assertEqual(meatpack_decode(meatpack("G1Y2E3F9X\n")), "G1Y2E3F9X\n")

    def test_no_spaces_turns_nibble_11_into_e(self):
        self.assertEqual(meatpack_decode(bytes([0xFF, 0xFF, 251, 0xFF, 0xFF, 247, 0xB1, 0xC2])), "1E2\n")

    def test_disabled_packing_passes_text_through(self):
        data = bytes([0xFF, 0xFF, 250]) + b"; comment\n" + bytes([0xFF, 0xFF, 251, 0x21])
        self.assertEqual(meatpack_decode(data), "; comment\n12")

    def test_reset_command(self):
        data = bytes([0xFF, 0xFF, 251, 0xFF, 0xFF, 249]) + b"ok"
        self.assertEqual(meatpack_decode(data), "ok")

    def test_unknown_command_is_an_error(self):
        with self.assertRaises(ValueError):
            meatpack_decode(bytes([0xFF, 0xFF, 77]))

    def test_truncated_full_byte_is_an_error(self):
        with self.assertRaises(ValueError):
            meatpack_decode(bytes([0xFF, 0xFF, 251, 0xF1]))


class FixtureDecodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.file = bgcode.parse(cube_bgcode().read_bytes())

    def test_gcode_blocks_decode_to_gcode(self):
        text = self.file.gcode()
        self.assertIn("M73 P0", text)
        self.assertIn(";LAYER_CHANGE", text)
        self.assertIn("G1X", text.replace(" ", ""))

    def test_every_gcode_block_decodes_to_its_stated_size(self):
        for block in self.file.blocks:
            if block.type == bgcode.BlockType.GCODE:
                self.assertEqual(len(block.payload()), block.uncompressed_size)

    def test_metadata_blocks_are_read(self):
        self.assertEqual(self.file.metadata(bgcode.BlockType.PRINTER_METADATA)["printer_model"], "MINIIS")
        self.assertEqual(self.file.metadata(bgcode.BlockType.SLICER_METADATA)["layer_height"], "0.15")
        self.assertIn("filament used [cm3]", self.file.metadata(bgcode.BlockType.PRINT_METADATA))

    def test_a_gcode_block_is_not_metadata(self):
        with self.assertRaises(ValueError):
            self.file.metadata(bgcode.BlockType.GCODE)


class ToolpathTests(unittest.TestCase):
    AREA = math.pi * 0.875**2

    def test_extrusion_volume_by_type_and_layers(self):
        path = summarize(
            ";LAYER_CHANGE\n;Z:0.2\n;TYPE:Perimeter\nM83\nG1 X10 Y0 E2\nG1 X10 Y5 E1\n"
            ";LAYER_CHANGE\n;Z:0.35\n;TYPE:Skirt/Brim\nG1 X0 Y5 E4\n"
        )
        self.assertEqual(path.layers, [0.2, 0.35])
        self.assertAlmostEqual(path.volume["Perimeter"], 3 * self.AREA)
        self.assertAlmostEqual(path.volume["Skirt/Brim"], 4 * self.AREA)
        self.assertAlmostEqual(path.part_volume(), 3 * self.AREA)

    def test_travel_and_retraction_do_not_count_as_extrusion(self):
        path = summarize(";TYPE:Perimeter\nM83\nG1 E-2\nG1 X50 Y50\nG1 E2\nG1 X51 Y50 E1\n")
        self.assertAlmostEqual(path.volume["Perimeter"], self.AREA)
        self.assertAlmostEqual(path.net_extrusion, 1.0)
        self.assertEqual(
            (path.extrusion_box["Perimeter"].x_min, path.extrusion_box["Perimeter"].x_max), (51, 51)
        )
        self.assertEqual((path.move_box.x_min, path.move_box.x_max), (0, 51))

    def test_absolute_extrusion_and_g92(self):
        path = summarize(";TYPE:Perimeter\nM82\nG92 E0\nG1 X1 E1\nG1 X2 E2.5\nG92 E0\nG1 X3 E1\n")
        self.assertAlmostEqual(path.volume["Perimeter"], 3.5 * self.AREA)

    def test_relative_xyz(self):
        path = summarize("G90\nG1 X10 Y10\nG91\nG1 X5 Y-2 Z1\n")
        self.assertEqual((path.move_box.x_max, path.move_box.y_min), (15, 8))
        self.assertEqual(path.move_z, (0, 1))

    def test_arc_bounds_include_its_extremes(self):
        # Counter-clockwise from (10, 0) to (-10, 0) about the origin passes (0, 10).
        path = summarize(";TYPE:Perimeter\nG1 X10 Y0\nG3 X-10 Y0 I-10 J0 E1\n")
        box = path.extrusion_box["Perimeter"]
        self.assertAlmostEqual(box.y_max, 10)
        self.assertAlmostEqual(box.y_min, 0)
        self.assertAlmostEqual(box.x_min, -10)

    def test_clockwise_arc_takes_the_other_way_round(self):
        path = summarize(";TYPE:Perimeter\nG1 X10 Y0\nG2 X-10 Y0 I-10 J0 E1\n")
        box = path.extrusion_box["Perimeter"]
        self.assertAlmostEqual(box.y_min, -10)
        self.assertAlmostEqual(box.y_max, 0)

    def test_temperatures_support_and_comments(self):
        path = summarize(
            "M104 S170\nM109 R170\nM140 S60\nM190 S60\nM104 S220 ; later\n;TYPE:Support material\nM83\nG1 X1 E1\n"
        )
        self.assertEqual(path.hotend_temperatures, [170, 170, 220])
        self.assertEqual(path.bed_temperatures, [60, 60])
        self.assertTrue(path.has_support())
        self.assertEqual(path.part_volume(), 0)


if __name__ == "__main__":
    unittest.main()

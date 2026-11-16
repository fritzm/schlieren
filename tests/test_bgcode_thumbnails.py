"""bgcode thumbnail embedding: the container, the image encoders, and the rendered thumbnails.

The bgcode here is synthetic (the block layout PrusaSlicer writes, with stand-in payloads), so the tests need no
slicer output; the layout itself was checked against PrusaSlicer-sliced files.
"""

import struct
import unittest
import zipfile
import zlib
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from schlieren import bgcode
from schlieren.cli.make_bgcode import embed_thumbnails, model_for
from schlieren.image_codecs import decode_qoi, encode_png, encode_qoi
from schlieren.print_3mf import bed_size, read_placed_mesh
from schlieren.thumbnail import (
    MODEL_COLOR,
    ThumbnailSpec,
    render_thumbnail_pixels,
    render_thumbnails,
    thumbnail_specs,
)

CONFIG = "; bed_shape = 0x0,180x0,180x180,0x180\n; thumbnails = 16x16/QOI, 40x30/PNG\n; other = 1\n"
CUBE_MODEL = """<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
 <resources>
  <object id="1" type="model"><mesh>
   <vertices>
    <vertex x="0" y="0" z="0"/><vertex x="10" y="0" z="0"/><vertex x="10" y="10" z="0"/><vertex x="0" y="10" z="0"/>
    <vertex x="0" y="0" z="10"/><vertex x="10" y="0" z="10"/><vertex x="10" y="10" z="10"/><vertex x="0" y="10" z="10"/>
   </vertices>
   <triangles>
    <triangle v1="0" v2="2" v3="1"/><triangle v1="0" v2="3" v3="2"/>
    <triangle v1="4" v2="5" v3="6"/><triangle v1="4" v2="6" v3="7"/>
    <triangle v1="0" v2="1" v3="5"/><triangle v1="0" v2="5" v3="4"/>
    <triangle v1="1" v2="2" v3="6"/><triangle v1="1" v2="6" v3="5"/>
    <triangle v1="2" v2="3" v3="7"/><triangle v1="2" v2="7" v3="6"/>
    <triangle v1="3" v2="0" v3="4"/><triangle v1="3" v2="4" v3="7"/>
   </triangles>
  </mesh></object>
 </resources>
 <build>
  <item objectid="1" transform="1 0 0 0 1 0 0 0 1 70 90 0"/>
  <item objectid="1" transform="0 1 0 -1 0 0 0 0 1 110 90 0"/>
 </build>
</model>
"""


def block(kind: int, parameters: bytes, data: bytes, compression: int = 0) -> bytes:
    header = struct.pack("<HHI", kind, compression, len(data) * (2 if compression else 1))
    if compression:
        header += struct.pack("<I", len(data))  # The payload is opaque, so it only has to match this size.
    body = header + parameters + data
    return body + struct.pack("<I", zlib.crc32(body))


def synthetic_bgcode(thumbnails: bool) -> bytes:
    blocks = [
        block(bgcode.BlockType.FILE_METADATA, b"\0\0", b"Producer=test\n"),
        block(bgcode.BlockType.PRINTER_METADATA, b"\0\0", b"printer_model=MINIIS\n"),
    ]
    if thumbnails:
        blocks.append(block(bgcode.BlockType.THUMBNAIL, struct.pack("<HHH", 2, 1, 1), b"old"))
    blocks += [
        block(bgcode.BlockType.PRINT_METADATA, b"\0\0", b"time=1\n"),
        block(bgcode.BlockType.SLICER_METADATA, b"\0\0", b"layer=0.15\n"),
        block(bgcode.BlockType.GCODE, b"\0\0", b"G1 X1\n"),
        block(bgcode.BlockType.GCODE, b"\0\0", b"G1 X2\n"),
    ]
    return struct.pack("<4sIH", b"GCDE", 1, 1) + b"".join(blocks)


def kinds(data: bytes) -> list[int]:
    return [b.type for b in bgcode.parse(data).blocks]


class ContainerTests(unittest.TestCase):
    def test_parse_round_trips_byte_for_byte(self):
        data = synthetic_bgcode(thumbnails=True)
        self.assertEqual(bgcode.parse(data).to_bytes(), data)

    def test_corrupt_block_is_rejected(self):
        data = bytearray(synthetic_bgcode(thumbnails=False))
        data[-3] ^= 0xFF
        with self.assertRaisesRegex(bgcode.BgcodeError, "checksum"):
            bgcode.parse(bytes(data))

    def test_truncated_file_is_rejected(self):
        with self.assertRaises(bgcode.BgcodeError):
            bgcode.parse(synthetic_bgcode(thumbnails=False)[:-5])

    def test_not_a_bgcode_is_rejected(self):
        with self.assertRaises(bgcode.BgcodeError):
            bgcode.parse(b"; gcode\n" * 4)

    def test_compressed_block_header_is_read(self):
        data = struct.pack("<4sIH", b"GCDE", 1, 1) + block(
            bgcode.BlockType.GCODE, b"\0\0", b"abcdef", compression=3
        )
        self.assertEqual(kinds(data), [bgcode.BlockType.GCODE])


class EmbedThumbnailsTests(unittest.TestCase):
    images = (
        (bgcode.ImageFormat.QOI, 16, 16, b"qoi-bytes"),
        (bgcode.ImageFormat.PNG, 40, 30, b"png-bytes"),
    )

    def test_thumbnails_go_between_printer_and_print_metadata(self):
        block_type = bgcode.BlockType
        result = embed_thumbnails(synthetic_bgcode(thumbnails=False), self.images)
        self.assertEqual(
            kinds(result),
            [
                block_type.FILE_METADATA,
                block_type.PRINTER_METADATA,
                block_type.THUMBNAIL,
                block_type.THUMBNAIL,
                block_type.PRINT_METADATA,
                block_type.SLICER_METADATA,
                block_type.GCODE,
                block_type.GCODE,
            ],
        )

    def test_thumbnail_parameters_and_data(self):
        result = bgcode.parse(embed_thumbnails(synthetic_bgcode(thumbnails=False), self.images))
        found = [(b.thumbnail, b.data) for b in result.blocks if b.thumbnail]
        self.assertEqual(
            found,
            [
                ((bgcode.ImageFormat.QOI, 16, 16), b"qoi-bytes"),
                ((bgcode.ImageFormat.PNG, 40, 30), b"png-bytes"),
            ],
        )

    def test_existing_thumbnails_are_replaced(self):
        result = embed_thumbnails(synthetic_bgcode(thumbnails=True), self.images)
        self.assertEqual(kinds(result).count(bgcode.BlockType.THUMBNAIL), 2)
        self.assertNotIn(b"old", result)

    def test_gcode_blocks_are_untouched(self):
        before = bgcode.parse(synthetic_bgcode(thumbnails=False))
        after = bgcode.parse(embed_thumbnails(synthetic_bgcode(thumbnails=False), self.images))
        gcode = [b.raw for b in before.blocks if b.type == bgcode.BlockType.GCODE]
        self.assertEqual(gcode, [b.raw for b in after.blocks if b.type == bgcode.BlockType.GCODE])

    def test_idempotent(self):
        once = embed_thumbnails(synthetic_bgcode(thumbnails=False), self.images)
        self.assertEqual(embed_thumbnails(once, self.images), once)

    def test_no_printer_metadata_is_an_error(self):
        data = struct.pack("<4sIH", b"GCDE", 1, 1) + block(bgcode.BlockType.GCODE, b"\0\0", b"G1\n")
        with self.assertRaises(bgcode.BgcodeError):
            embed_thumbnails(data, self.images)

    def test_without_checksums_none_are_written(self):
        header = struct.pack("<4sIH", b"GCDE", 1, 0)
        body = struct.pack("<HHI", bgcode.BlockType.PRINTER_METADATA, 0, 3) + b"\0\0" + b"abc"
        result = embed_thumbnails(header + body, self.images)
        self.assertEqual(
            kinds(result), [bgcode.BlockType.PRINTER_METADATA] + [bgcode.BlockType.THUMBNAIL] * 2
        )
        self.assertEqual(len(result), len(header + body) + 2 * (8 + 6) + len(b"qoi-bytes" + b"png-bytes"))


class ModelLookupTests(unittest.TestCase):
    def test_model_is_found_beside_the_slicer_named_bgcode(self):
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "slit_stage_plate.3mf").write_bytes(b"")
            sliced = folder / "slit_stage_plate_0.4n_0.15mm_PLA_MINIIS_1h49m.bgcode"
            self.assertEqual(model_for(sliced), folder / "slit_stage_plate.3mf")

    def test_missing_model_is_an_error(self):
        with TemporaryDirectory() as directory, self.assertRaises(FileNotFoundError):
            model_for(Path(directory) / "x_0.4n_0.2mm_PLA_MINIIS_1m.bgcode")


class CodecTests(unittest.TestCase):
    @staticmethod
    def image() -> np.ndarray:
        rng = np.random.default_rng(1)
        pixels = rng.integers(0, 256, (24, 31, 4), dtype=np.uint8)
        pixels[3:9] = (20, 20, 20, 255)  # Runs.
        pixels[10:14, 5:20, :3] = np.arange(15, dtype=np.uint8)[None, :, None] * 3  # Small differences.
        pixels[..., 3] = np.where(np.arange(24)[:, None] < 16, 255, pixels[..., 3])
        return pixels

    def test_qoi_round_trips(self):
        pixels = self.image()
        np.testing.assert_array_equal(decode_qoi(encode_qoi(pixels)), pixels)

    def test_qoi_header_and_end_marker(self):
        data = encode_qoi(self.image())
        self.assertEqual(data[:14], b"qoif" + struct.pack(">IIBB", 31, 24, 4, 0))
        self.assertTrue(data.endswith(b"\x00" * 7 + b"\x01"))

    def test_png_header_and_pixels(self):
        pixels = self.image()
        data = encode_png(pixels)
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", data[16:24]), (31, 24))
        self.assertEqual(data[24:26], bytes([8, 6]))  # 8-bit RGBA
        idat = data.index(b"IDAT")
        (length,) = struct.unpack(">I", data[idat - 4 : idat])
        rows = np.frombuffer(zlib.decompress(data[idat + 4 : idat + 4 + length]), np.uint8).reshape(24, -1)
        self.assertTrue((rows[:, 0] == 0).all())
        np.testing.assert_array_equal(rows[:, 1:].reshape(24, 31, 4), pixels)

    def test_wrong_array_is_rejected(self):
        with self.assertRaises(ValueError):
            encode_qoi(np.zeros((4, 4, 3), np.uint8))


class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = TemporaryDirectory()
        cls.model = Path(cls.directory.name) / "cube.3mf"
        with zipfile.ZipFile(cls.model, "w") as archive:
            archive.writestr("3D/3dmodel.model", CUBE_MODEL)
            archive.writestr("Metadata/Slic3r_PE.config", CONFIG)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_specs_come_from_the_profile(self):
        self.assertEqual(
            thumbnail_specs(CONFIG),
            [ThumbnailSpec(16, 16, bgcode.ImageFormat.QOI), ThumbnailSpec(40, 30, bgcode.ImageFormat.PNG)],
        )

    def test_jpg_is_unsupported(self):
        with self.assertRaises(ValueError):
            thumbnail_specs("; thumbnails = 16x16/JPG\n")

    def test_bed_size(self):
        self.assertEqual(bed_size(CONFIG), (180.0, 180.0))

    def test_items_are_placed_by_their_transforms(self):
        vertices, triangles = read_placed_mesh(self.model)
        self.assertEqual(vertices.shape, (16, 3))
        self.assertEqual(triangles.shape, (24, 3))
        self.assertEqual(triangles.max(), 15)
        np.testing.assert_allclose(
            vertices.min(axis=0), (70, 90, 0)
        )  # The second cube is turned 90 deg about z.
        np.testing.assert_allclose(vertices.max(axis=0), (110, 100, 10))

    def test_render_is_opaque_with_the_model_in_view(self):
        vertices, triangles = read_placed_mesh(self.model)
        pixels = render_thumbnail_pixels(vertices, triangles, (180, 180), 80, 60)
        self.assertEqual(pixels.shape, (60, 80, 4))
        self.assertTrue((pixels[..., 3] == 255).all())
        orange = np.abs(pixels[..., :3].astype(float) / 255 - MODEL_COLOR).max(axis=2) < 0.35
        self.assertGreater(orange.mean(), 0.1)  # The model fills a good part of the frame...
        self.assertTrue(orange[:, :4].sum() + orange[:, -4:].sum() == 0)  # ...inside the margin.
        self.assertTrue(orange[:3].sum() + orange[-3:].sum() == 0)

    def test_render_thumbnails_returns_each_spec_encoded(self):
        rendered = render_thumbnails(self.model)
        self.assertEqual([spec for spec, _ in rendered], thumbnail_specs(CONFIG))
        self.assertEqual(decode_qoi(rendered[0][1]).shape, (16, 16, 4))
        self.assertEqual(rendered[1][1][:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()

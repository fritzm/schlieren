"""Print checks on a sliced bgcode, the slicer wrapper, and the make-bgcode commands, on the sliced cube fixture."""

import re
import shutil
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from schlieren import bgcode, print_checks, prusaslicer
from schlieren.cli import make_bgcode
from schlieren.gcode_toolpath import summarize
from schlieren.print_3mf import build_3mf
from tests.print_helpers import CUBE_3MF, cube_bgcode, write_box_stl

Status = print_checks.Status


def by_name(checks):
    return {check.name: check for check in checks}


class CheckTests(unittest.TestCase):
    def test_a_good_slice_passes_everything(self):
        checks = print_checks.check_bgcode(cube_bgcode(), CUBE_3MF)
        self.assertEqual(
            [c.name for c in checks],
            [
                "structure",
                "decode",
                "layers",
                "temperatures",
                "supports",
                "volume accounting",
                "bed",
                "footprint",
                "height",
                "part volume",
            ],
        )
        self.assertEqual([c for c in checks if c.status != Status.OK], [])

    def test_without_a_model_the_comparison_is_skipped(self):
        checks = by_name(print_checks.check_bgcode(cube_bgcode(), None))
        self.assertEqual(checks["model comparison"].status, Status.NOTE)
        self.assertNotIn("footprint", checks)

    def test_corrupt_file_fails_structure(self):
        with tempfile.TemporaryDirectory() as directory:
            data = bytearray(cube_bgcode().read_bytes())
            data[len(data) // 2] ^= 0xFF
            broken = Path(directory) / "broken.bgcode"
            broken.write_bytes(data)
            checks = print_checks.check_bgcode(broken, CUBE_3MF)
        self.assertEqual([(c.name, c.status) for c in checks], [("structure", Status.FAIL)])

    def test_unexpected_support_fails_and_expected_support_is_required(self):
        self.assertEqual(
            by_name(print_checks.check_bgcode(cube_bgcode(), CUBE_3MF, expect_support=True))[
                "supports"
            ].status,
            Status.FAIL,
        )

    def test_hotend_limit(self):
        checks = by_name(print_checks.check_bgcode(cube_bgcode(), CUBE_3MF, max_hotend=200))
        self.assertEqual(checks["temperatures"].status, Status.FAIL)

    def test_a_model_that_does_not_match_fails_footprint_and_height(self):
        with tempfile.TemporaryDirectory() as directory:
            big = Path(directory) / "big.3mf"
            build_3mf(write_box_stl(Path(directory) / "big.stl", (40, 10, 25)), CUBE_3MF, big)
            checks = by_name(print_checks.check_bgcode(cube_bgcode(), big))
        self.assertEqual(checks["footprint"].status, Status.FAIL)
        self.assertEqual(checks["height"].status, Status.FAIL)

    def test_a_model_off_the_bed_is_seen_in_the_bed_check(self):
        with tempfile.TemporaryDirectory() as directory:
            narrow = Path(directory) / "narrow.3mf"
            shutil.copy(CUBE_3MF, narrow)
            with zipfile.ZipFile(CUBE_3MF) as source, zipfile.ZipFile(narrow, "w") as target:
                for name in source.namelist():
                    data = source.read(name)
                    if name == "Metadata/Slic3r_PE.config":
                        data = re.sub(rb"; bed_shape = .*", b"; bed_shape = 0x0,80x0,80x80,0x80", data)
                    target.writestr(name, data)
            checks = by_name(print_checks.check_bgcode(cube_bgcode(), narrow))
        self.assertEqual(checks["bed"].status, Status.FAIL)

    def test_report_and_failed(self):
        checks = print_checks.check_bgcode(cube_bgcode(), CUBE_3MF, max_hotend=200)
        self.assertEqual([c.name for c in print_checks.failed(checks)], ["temperatures"])
        self.assertIn("[FAIL] temperatures", print_checks.report(checks))
        self.assertIn("[  ok] structure", print_checks.report(checks))


FAKE_OK = """#!/bin/sh
out="$5"
echo "10 => Processing triangulated mesh"
echo "90 => Exporting G-code to $out/part_{printing_filament_types}.bgcode"
cp "{source}" "$out/part_0.4n_0.15mm_PLA_MINIIS_1m.bgcode"
echo "Slicing result exported to $out/part_0.4n_0.15mm_PLA_MINIIS_1m.bgcode"
"""


class SlicerTests(unittest.TestCase):
    def fake(self, directory: Path, body: str) -> Path:
        script = directory / "fake-slicer"
        script.write_text(body.replace("{source}", str(cube_bgcode())))
        script.chmod(script.stat().st_mode | stat.S_IEXEC)
        return script

    def test_clean_slice_returns_the_file_the_slicer_named(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = prusaslicer.slice_3mf(CUBE_3MF, root / "out", self.fake(root, FAKE_OK))
            self.assertEqual(result.output, root / "out" / "part_0.4n_0.15mm_PLA_MINIIS_1m.bgcode")
            self.assertTrue(result.output.exists())
            self.assertEqual(result.problems, ())

    def test_warning_lines_are_returned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            body = FAKE_OK.replace('echo "10', 'echo "Warning: object floats above the bed" >&2\necho "10')
            result = prusaslicer.slice_3mf(CUBE_3MF, root / "out", self.fake(root, body))
            self.assertEqual(result.problems, ("Warning: object floats above the bed",))

    def test_failure_raises_with_the_log(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = self.fake(root, '#!/bin/sh\necho "Error: no objects" >&2\nexit 3\n')
            with self.assertRaisesRegex(prusaslicer.SliceError, "Error: no objects"):
                prusaslicer.slice_3mf(CUBE_3MF, root / "out", script)

    def test_missing_slicer_is_an_error(self):
        with self.assertRaisesRegex(prusaslicer.SliceError, "not found"):
            prusaslicer.find_slicer(Path("/no/such/slicer"))

    def test_slicer_comes_from_the_environment(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            mock.patch.dict("os.environ", {prusaslicer.SLICER_ENV: directory}),
        ):
            self.assertEqual(prusaslicer.find_slicer(), Path(directory))

    @unittest.skipUnless(prusaslicer.DEFAULT_SLICER.exists(), "PrusaSlicer is not installed")
    def test_real_slicer_makes_a_bgcode_that_passes_the_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            result = prusaslicer.slice_3mf(CUBE_3MF, Path(directory))
            self.assertEqual(result.problems, ())
            checks = print_checks.check_bgcode(result.output, CUBE_3MF)
            self.assertEqual([c for c in checks if c.status != Status.OK], [])


class AddedPartSliceTests(unittest.TestCase):
    @unittest.skipUnless(prusaslicer.DEFAULT_SLICER.exists(), "PrusaSlicer is not installed")
    def test_slicer_merges_an_added_box_into_the_part(self):
        # A 10 mm cube with a 2 x 2 x 0.3 mm tab on its side: the tab is sliced, and nothing else changes.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stl = write_box_stl(root / "cube.stl", (10, 10, 10))
            build_3mf(stl, CUBE_3MF, root / "tab.3mf", boxes=[(9, 4, 0, 12, 6, 0.3)])
            result = prusaslicer.slice_3mf(root / "tab.3mf", root / "out")
            self.assertEqual(result.problems, ())
            path = summarize(bgcode.parse(result.output.read_bytes()).gcode())
            self.assertGreater(path.part_box().x_max, 95.5)  # The cube ends at 95; the tab reaches 97.
            self.assertLess(path.extrusion_z["External perimeter"][0], 0.25)
            self.assertEqual(
                print_checks.failed(print_checks.check_bgcode(result.output, root / "tab.3mf")), []
            )


class CommandTests(unittest.TestCase):
    def run_main(self, *argv: str):
        with mock.patch.object(sys, "argv", ["make-bgcode", *argv]):
            make_bgcode.main()

    def test_validate_exits_nonzero_on_a_failed_check(self):
        self.run_main("validate", str(cube_bgcode()), "--model", str(CUBE_3MF))
        with self.assertRaises(SystemExit) as raised:
            self.run_main(
                "validate", str(cube_bgcode()), "--model", str(CUBE_3MF), "--max-temperature", "200"
            )
        self.assertIn("temperatures", str(raised.exception))

    def test_thumbnails_replace_in_place_and_leave_no_other_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy = root / cube_bgcode().name
            shutil.copy(cube_bgcode(), copy)
            shutil.copy(CUBE_3MF, root / "cube.3mf")
            self.run_main("thumbnails", str(copy))
            self.assertEqual(sorted(p.name for p in root.iterdir()), sorted([copy.name, "cube.3mf"]))
            thumbs = [b.thumbnail for b in bgcode.parse(copy.read_bytes()).blocks if b.thumbnail]
            self.assertEqual([(w, h) for _, w, h in thumbs], [(16, 16), (220, 124), (200, 240), (380, 285)])
            self.assertEqual(print_checks.failed(print_checks.check_bgcode(copy, root / "cube.3mf")), [])

    def test_keep_original_is_opt_in(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy = root / cube_bgcode().name
            shutil.copy(cube_bgcode(), copy)
            shutil.copy(CUBE_3MF, root / "cube.3mf")
            self.run_main("thumbnails", str(copy), "--keep-original")
            original = copy.with_suffix(".bgcode.orig")
            self.assertEqual(original.read_bytes(), cube_bgcode().read_bytes())

    def test_prepare_refuses_to_replace_a_3mf(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stl = write_box_stl(root / "cube.stl", (10, 10, 10))
            shutil.copy(CUBE_3MF, root / "cube.3mf")
            with self.assertRaisesRegex(SystemExit, "exists"):
                self.run_main("prepare", str(stl), "--template", str(CUBE_3MF), "--output-dir", str(root))

    @unittest.skipUnless(prusaslicer.DEFAULT_SLICER.exists(), "PrusaSlicer is not installed")
    def test_prepare_runs_every_step(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stl = write_box_stl(root / "block.stl", (10, 12, 14))
            self.run_main("prepare", str(stl), "--template", str(CUBE_3MF), "--output-dir", str(root / "out"))
            sliced = list((root / "out").glob("block_*.bgcode"))
            self.assertEqual(len(sliced), 1)
            self.assertEqual(
                [b.thumbnail[1:] for b in bgcode.parse(sliced[0].read_bytes()).blocks if b.thumbnail],
                [(16, 16), (220, 124), (200, 240), (380, 285)],
            )
            self.assertEqual(sorted(p.suffix for p in (root / "out").iterdir()), [".3mf", ".bgcode"])


if __name__ == "__main__":
    unittest.main()

"""Building a PrusaSlicer 3MF from an STL: orientation, placement, mesh welding, and the carried-over profile."""

import re
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np

from schlieren.print_3mf import (
    CONFIG_PATH,
    build_3mf,
    mesh_volume,
    read_config,
    read_placed_mesh,
    read_stl,
    rotation_to_up,
)
from tests.print_helpers import CUBE_3MF, box_triangles, write_box_stl

AXES = {
    "+x": (1, 0, 0),
    "-x": (-1, 0, 0),
    "+y": (0, 1, 0),
    "-y": (0, -1, 0),
    "+z": (0, 0, 1),
    "-z": (0, 0, -1),
}


class RotationTests(unittest.TestCase):
    def test_each_up_axis_goes_to_plus_z_by_a_proper_rotation(self):
        for name, axis in AXES.items():
            with self.subTest(up=name):
                rotation = rotation_to_up(name)
                np.testing.assert_allclose(rotation @ axis, (0, 0, 1), atol=1e-12)
                np.testing.assert_allclose(rotation @ rotation.T, np.eye(3), atol=1e-12)
                self.assertAlmostEqual(float(np.linalg.det(rotation)), 1.0)

    def test_sign_is_optional_and_case_is_ignored(self):
        np.testing.assert_allclose(rotation_to_up("Y"), rotation_to_up("+y"))

    def test_bad_axis_is_an_error(self):
        for bad in ("w", "", "+xy", "up"):
            with self.subTest(bad), self.assertRaises(ValueError):
                rotation_to_up(bad)


class StlTests(unittest.TestCase):
    def test_binary_and_ascii_agree(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = write_box_stl(Path(directory) / "b.stl", (1, 2, 3))
            lines = ["solid box"]
            for triangle in box_triangles((1, 2, 3)):
                lines.append("facet normal 0 0 0\nouter loop")
                lines += [f"vertex {x} {y} {z}" for x, y, z in triangle]
                lines.append("endloop\nendfacet")
            ascii_path = Path(directory) / "a.stl"
            ascii_path.write_text("\n".join(lines) + "\nendsolid box\n")
            np.testing.assert_allclose(read_stl(ascii_path), read_stl(binary))

    def test_garbage_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            junk = Path(directory) / "x.stl"
            junk.write_bytes(b"not an stl")
            with self.assertRaises(ValueError):
                read_stl(junk)

    def test_box_volume(self):
        triangles = box_triangles((2, 3, 4))
        vertices = triangles.reshape(-1, 3)
        self.assertAlmostEqual(mesh_volume(vertices, np.arange(len(vertices)).reshape(-1, 3)), 24.0)


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.directory.name)
        cls.stl = write_box_stl(cls.dir / "box.stl", (20, 10, 30))

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def build(self, up: str, **kwargs):
        output = self.dir / f"box_{up.replace('+', 'p').replace('-', 'm')}.3mf"
        return output, build_3mf(self.stl, CUBE_3MF, output, up=up, **kwargs)

    def test_up_axis_stands_the_part_on_that_end(self):
        # The box is 20 x 10 x 30 in x, y, z; standing it on its x end makes x the height.
        output, built = self.build("+x")
        self.assertEqual(sorted(round(v, 6) for v in built.size), [10, 20, 30])
        self.assertAlmostEqual(built.size[2], 20)
        vertices, _ = read_placed_mesh(output)
        self.assertAlmostEqual(vertices[:, 2].min(), 0)
        self.assertAlmostEqual(vertices[:, 2].max(), 20)

    def test_minus_up_flips_the_part(self):
        _, built = self.build("-z")
        self.assertAlmostEqual(built.size[2], 30)
        self.assertAlmostEqual(built.volume, 6000)  # Still outward-facing: a reflection would flip the sign.

    def test_part_is_centered_on_the_templates_bed_position(self):
        output, _ = self.build("+z")
        vertices, _ = read_placed_mesh(output)
        np.testing.assert_allclose((vertices.min(axis=0) + vertices.max(axis=0))[:2] / 2, (90, 90), atol=1e-4)

    def test_mesh_is_welded_and_closed(self):
        _, built = self.build("+z")
        self.assertEqual((built.vertices, built.triangles, built.open_edges), (8, 12, 0))

    def test_open_mesh_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            holed = write_box_stl(Path(directory) / "holed.stl", (5, 5, 5), drop=3)
            built = build_3mf(holed, CUBE_3MF, Path(directory) / "holed.3mf")
        self.assertEqual(built.open_edges, 3)

    def test_profile_is_carried_over_unchanged(self):
        output, _ = self.build("+z")
        self.assertEqual(read_config(output), read_config(CUBE_3MF))
        with zipfile.ZipFile(output) as built, zipfile.ZipFile(CUBE_3MF) as template:
            self.assertEqual(built.namelist(), template.namelist())
            self.assertEqual(built.read(CONFIG_PATH), template.read(CONFIG_PATH))

    def test_object_config_matches_the_mesh(self):
        output, built = self.build("+z", name="my part")
        with zipfile.ZipFile(output) as archive:
            config = archive.read("Metadata/Slic3r_PE_model.config").decode()
            model = archive.read("3D/3dmodel.model").decode()
        self.assertIn(f'lastid="{built.triangles - 1}"', config)
        self.assertIn('value="my part.stl"', config)
        self.assertIn('name="Title">my part<', model)
        self.assertEqual(len(re.findall("<triangle ", model)), built.triangles)

    def test_added_box_is_a_separate_part_in_the_rotated_frame(self):
        # The box (STL frame) is turned and shifted with the part: up=-z flips y and z, the part's own x-y
        # center goes to the bed position, and its lowest point to the bed.
        output = self.dir / "web.3mf"
        built = build_3mf(self.stl, CUBE_3MF, output, up="-z", boxes=[(1, 1, 1, 3, 2, 4)])
        self.assertEqual((built.vertices, built.triangles, built.open_edges), (8, 12, 0))  # The part alone.
        vertices, triangles = read_placed_mesh(output)
        self.assertEqual((len(vertices), len(triangles)), (16, 24))
        np.testing.assert_allclose(vertices[8:].min(axis=0), (81, 93, 26), atol=1e-6)
        np.testing.assert_allclose(vertices[8:].max(axis=0), (83, 94, 29), atol=1e-6)
        self.assertAlmostEqual(mesh_volume(vertices, triangles), 6000 + 2 * 1 * 3, places=4)

    def test_added_box_is_declared_as_its_own_volume(self):
        output = self.dir / "web2.3mf"
        built = build_3mf(self.stl, CUBE_3MF, output, boxes=[(0, 0, 0, 1, 1, 1), (2, 2, 2, 3, 3, 3)])
        with zipfile.ZipFile(output) as archive:
            config = archive.read("Metadata/Slic3r_PE_model.config").decode()
        ranges = [(int(a), int(b)) for a, b in re.findall(r'<volume firstid="(\d+)" lastid="(\d+)"', config)]
        self.assertEqual(ranges, [(0, built.triangles - 1), (12, 23), (24, 35)])
        self.assertEqual(config.count('key="volume_type" value="ModelPart"'), 3)

    def test_degenerate_box_is_an_error(self):
        with self.assertRaises(ValueError):
            build_3mf(self.stl, CUBE_3MF, self.dir / "bad.3mf", boxes=[(0, 0, 0, 1, 0, 1)])

    def test_parts_cannot_be_added_to_a_template_that_already_has_them(self):
        two = self.dir / "two.3mf"
        build_3mf(self.stl, CUBE_3MF, two, boxes=[(0, 0, 0, 1, 1, 1)])
        with self.assertRaisesRegex(ValueError, "single volume"):
            build_3mf(self.stl, two, self.dir / "three.3mf", boxes=[(0, 0, 0, 1, 1, 1)])

    def test_template_without_a_build_item_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            bare = Path(directory) / "bare.3mf"
            with zipfile.ZipFile(CUBE_3MF) as source, zipfile.ZipFile(bare, "w") as target:
                for name in source.namelist():
                    data = source.read(name)
                    if name == "3D/3dmodel.model":
                        data = re.sub(rb"<item [^>]*/>", b"", data)
                    target.writestr(name, data)
            with self.assertRaises(ValueError):
                build_3mf(self.stl, bare, Path(directory) / "out.3mf")


if __name__ == "__main__":
    unittest.main()

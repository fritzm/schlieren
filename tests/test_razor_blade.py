"""Stanley razor blade: measured envelope, bevel, fold, and the approximated notches and slot."""

import unittest
from dataclasses import replace

from build123d import Vector

from schlieren.parts.razor_blade import RazorBladeParameters, build_razor_blade, build_razor_blade_assembly
from schlieren.standards import INCH


class RazorBladeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = RazorBladeParameters()
        cls.p.validate()
        cls.blade = build_razor_blade(cls.p)

    def inside(self, x, y, z):
        return self.blade.is_inside(Vector(x, y, z))

    def test_single_valid_solid(self):
        self.assertEqual(len(self.blade.solids()), 1)
        self.assertTrue(self.blade.is_valid)

    def test_measured_envelope(self):
        box = self.blade.bounding_box()
        self.assertAlmostEqual(box.size.X, 1.537 * INCH, places=6)
        self.assertAlmostEqual(box.size.Z, 0.773 * INCH, places=6)
        self.assertAlmostEqual(box.size.Y, 0.040 * INCH, places=6)
        self.assertAlmostEqual(box.min.Z, 0, places=9)  # The cutting edge is the origin line.

    def test_plate_is_symmetric_about_its_mid_plane(self):
        box = self.blade.bounding_box()
        self.assertAlmostEqual(box.min.Y, -box.max.Y, places=9)
        self.assertAlmostEqual(box.min.X, -box.max.X, places=9)

    def test_plate_thickness_between_bevel_and_fold(self):
        p, half = self.p, self.p.thickness / 2
        z = (p.bevel_break + p.fold_front_z) / 2
        self.assertTrue(self.inside(14, half - 0.01, z))
        self.assertFalse(self.inside(14, half + 0.01, z))
        self.assertTrue(self.inside(14, -half + 0.01, z))
        self.assertFalse(self.inside(14, -half - 0.01, z))

    def test_bevel_on_both_faces_breaks_at_the_measured_distance(self):
        p = self.p
        # Past the break the plate is full thickness; short of it the section narrows toward the tip.
        past = p.bevel_break + 0.05
        self.assertTrue(self.inside(14, p.thickness / 2 - 0.01, past))
        self.assertFalse(self.inside(14, p.thickness / 2 - 0.01, p.bevel_break / 2))
        self.assertFalse(self.inside(14, -(p.thickness / 2 - 0.01), p.bevel_break / 2))
        self.assertTrue(self.inside(14, 0, 0.02))

    def test_fold_covers_both_faces_for_the_measured_extent(self):
        p = self.p
        for sign in (1, -1):
            top = sign * (p.fold_thickness / 2 - 0.01)
            self.assertTrue(self.inside(0, top, p.width - 0.01))
            self.assertTrue(self.inside(0, top, p.width - p.fold_extent + 0.01))
            self.assertFalse(self.inside(0, top, p.width - p.fold_extent - 0.01))

    def test_fold_corners_toward_the_edge_are_rounded(self):
        p = self.p
        self.assertFalse(self.inside(p.length / 2 - 0.1, p.fold_thickness / 2 - 0.01, p.fold_front_z + 0.1))
        self.assertTrue(self.inside(p.length / 2 - 0.1, p.fold_thickness / 2 - 0.01, p.width - 0.5))

    def test_notches_are_open_to_each_end_and_mirror_each_other(self):
        p = self.p
        for sign in (1, -1):
            self.assertFalse(self.inside(sign * (p.length / 2 - 0.5), 0, p.notch_z))
            self.assertFalse(self.inside(sign * (p.length / 2 - p.notch_depth + 0.2), 0, p.notch_z))
            self.assertTrue(self.inside(sign * (p.length / 2 - p.notch_depth - 0.2), 0, p.notch_z))
            # Wider than the notch, the end edge is intact.
            self.assertTrue(self.inside(sign * (p.length / 2 - 0.5), 0, p.notch_z + p.notch_width))

    def test_central_slot_is_a_through_stadium_along_the_width(self):
        p = self.p
        self.assertFalse(self.inside(0, 0, p.slot_z))
        self.assertFalse(self.inside(0, 0, p.slot_z + p.slot_length / 2 - 0.1))
        self.assertTrue(self.inside(0, 0, p.slot_z + p.slot_length / 2 + 0.1))
        self.assertFalse(self.inside(p.slot_width / 2 - 0.1, 0, p.slot_z))
        self.assertTrue(self.inside(p.slot_width / 2 + 0.1, 0, p.slot_z))
        # The round ends: the stadium's corner is not cut.
        self.assertTrue(self.inside(p.slot_width / 2 - 0.1, 0, p.slot_z + p.slot_length / 2 - 0.1))

    def test_features_leave_the_bevel_and_the_fold_intact(self):
        p = self.p
        for z in (p.notch_z, p.slot_z):
            self.assertGreater(z - p.slot_length / 2, p.bevel_break)
            self.assertLess(z + p.slot_length / 2, p.fold_front_z)

    def test_viewer_child_is_labeled(self):
        child = build_razor_blade_assembly(self.p)
        self.assertEqual(child.label, "Razor blade")
        self.assertAlmostEqual(child.volume, self.blade.volume, places=6)

    def test_rejects_inconsistent_parameters(self):
        for change in (
            {"edge_tip_thickness": 0.3},
            {"fold_thickness": 0.2},
            {"fold_extent": 19.0},
            {"notch_z": 14.0},
            {"slot_length": 2.0},
            {"notch_depth": 19.0},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(self.p, **change).validate()


if __name__ == "__main__":
    unittest.main()

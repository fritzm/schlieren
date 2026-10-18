"""Engineering invariants for the cased iPhone 17 model (design §9.1)."""

import unittest

from schlieren.cad import box_between, intersect, y_cylinder
from schlieren.parts.phone import (
    BUTTONS,
    PhoneParameters,
    build_bare_phone,
    build_camera_glass,
    build_case,
)

TOL = 1e-3  # mm


class PhoneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = PhoneParameters()
        cls.bare = build_bare_phone(cls.p)
        cls.glass = build_camera_glass(cls.p)
        cls.case = build_case(cls.p)

    def test_each_part_is_one_valid_solid(self):
        for name, part in (("bare", self.bare), ("glass", self.glass), ("case", self.case)):
            with self.subTest(part=name):
                self.assertTrue(part.is_valid)
                self.assertEqual(len(part.solids()), 2 if name == "glass" else 1)

    def test_bare_phone_is_apples_body_with_protruding_buttons(self):
        p, box = self.p, self.bare.bounding_box()
        pushed = max(b.protrusion for b in BUTTONS)
        self.assertAlmostEqual(box.size.X, 149.61, places=3)
        self.assertAlmostEqual(box.size.Z, 71.45 + 2 * pushed, places=3)
        self.assertAlmostEqual(box.min.Y, p.front_glass_y, places=3)
        self.assertAlmostEqual(box.max.Y, p.back_glass_y + p.plateau_height, places=3)

    def test_case_outside_is_the_measured_cased_phone(self):
        p, box = self.p, self.case.bounding_box()
        self.assertAlmostEqual(-box.min.X, 34.3, places=3)  # Main camera from the near edge, §9.1.
        self.assertAlmostEqual(-box.min.Z, 60.6, places=3)  # Main camera above the lower edge, §9.1.
        self.assertAlmostEqual(box.size.Y, 0.510 * 25.4, places=3)  # Measured thickness over the case.
        self.assertAlmostEqual(box.max.Y, 0.0, places=3)  # The back plane, where the lens seats.
        self.assertAlmostEqual(box.size.X, p.cased_length, places=3)
        self.assertAlmostEqual(box.size.Z, p.cased_width, places=3)

    def test_main_camera_is_on_the_axis_and_ultra_wide_17_72_mm_toward_the_near_edge(self):
        ring = self.glass.bounding_box()
        self.assertAlmostEqual(ring.max.X, self.p.camera_ring_diameter / 2, places=3)
        self.assertAlmostEqual(ring.min.X, -17.72 - self.p.camera_ring_diameter / 2, places=3)
        self.assertAlmostEqual((ring.min.Z + ring.max.Z) / 2, 0.0, places=3)

    def test_plateau_top_and_fillet_foot_are_at_apples_extents(self):
        p, y = self.p, self.p.back_glass_y
        x_lo, x_hi = p.x_of(p.plateau_foot_v[0]), p.x_of(p.plateau_foot_v[1])
        z_lo, z_hi = p.z_of(p.plateau_foot_u[1]), p.z_of(p.plateau_foot_u[0])
        window = box_between(x_lo - 5, x_hi + 5, y, y + p.plateau_height + 1, z_lo - 5, z_hi + 5)
        top = intersect(
            intersect(self.bare, window),
            box_between(x_lo - 5, x_hi + 5, y + 1.77, y + 2.0, z_lo - 5, z_hi + 5),
        )
        box = top.bounding_box()
        self.assertAlmostEqual(box.min.X, p.x_of(3.97), delta=0.02)
        self.assertAlmostEqual(box.max.X, p.x_of(40.99), delta=0.02)
        self.assertAlmostEqual(box.min.Z, p.z_of(23.45), delta=0.02)
        self.assertAlmostEqual(box.max.Z, p.z_of(3.79), delta=0.02)
        foot = intersect(self.bare, box_between(x_lo - 5, x_hi + 5, y + 0.0, y + 0.02, z_lo - 5, z_hi + 5))
        box = foot.bounding_box()
        self.assertAlmostEqual(box.min.X, p.x_of(1.34), delta=0.02)
        self.assertAlmostEqual(box.max.X, p.x_of(43.62), delta=0.02)
        self.assertAlmostEqual(box.min.Z, p.z_of(26.06), delta=0.02)

    def test_camera_opening_is_the_measured_size_and_placed_from_the_case_edge(self):
        p = self.p
        xc = (p.x_of(p.plateau_v[0]) + p.x_of(p.plateau_v[1])) / 2
        z_hi = p.z_upper + p.case_side_wall - 0.180 * 25.4
        half = 1.585 * 25.4 / 2
        z_lo = z_hi - 1.35 * 25.4
        zm = (z_hi + z_lo) / 2

        def case_in(x0, x1, z0, z1):
            return intersect(box_between(x0, x1, p.back_glass_y + 1.0, 0.0, z0, z1), self.case).volume

        inside = 0.05
        self.assertLess(case_in(xc - half + inside, xc + half - inside, zm - 1, zm + 1), TOL)
        self.assertLess(case_in(xc - 1, xc + 1, z_lo + inside, z_hi - inside), TOL)
        self.assertGreater(case_in(xc - 1, xc + 1, z_hi + 0.05, z_hi + 1.0), 0.1)
        self.assertGreater(case_in(xc - 1, xc + 1, z_lo - 1.0, z_lo - 0.05), 0.1)
        self.assertGreater(case_in(xc + half + 0.05, xc + half + 1.0, zm - 1, zm + 1), 0.1)

    def test_camera_glass_rings_are_separate_16_mm_windows(self):
        self.assertAlmostEqual(self.p.camera_ring_diameter, 16.0, places=3)  # Apple: 2X Ø16.00.
        self.assertGreater(17.72 - self.p.camera_ring_diameter, 1.0)  # The rings do not touch.

    def test_camera_glass_stands_under_the_case_lip(self):
        p = self.p
        ring = self.glass.bounding_box()
        self.assertAlmostEqual(ring.max.Y - p.back_glass_y, 3.45, places=3)  # Apple: back glass to glass.
        self.assertAlmostEqual(ring.max.Y, -p.camera_glass_recess, places=3)
        self.assertGreater(p.camera_glass_recess, 0.0)

    def test_screen_is_0_050_in_under_the_case_front_rim(self):
        self.assertAlmostEqual(
            self.bare.bounding_box().min.Y - self.case.bounding_box().min.Y, 1.27, places=3
        )

    def test_bare_phone_sits_in_the_case_without_interference(self):
        self.assertLess(intersect(self.bare, self.case).volume, TOL)
        self.assertLess(intersect(self.glass, self.case).volume, TOL)
        self.assertLess(intersect(self.glass, self.bare).volume, TOL)

    def test_case_back_is_open_over_the_camera_plateau_and_flash(self):
        p = self.p
        x0, x1 = p.x_of(p.plateau_v[0]), p.x_of(p.plateau_v[1])
        z0, z1 = p.z_of(p.plateau_u[1]), p.z_of(p.plateau_u[0])
        end = (z1 - z0) / 2  # The plateau's round ends.
        over_plateau = box_between(x0 + end, x1 - end, p.back_glass_y, 0.0, z0, z1)
        self.assertLess(intersect(over_plateau, self.case).volume, TOL)
        flash = y_cylinder(p.flash_diameter, p.x_of(p.flash_v), p.z_of(p.flash_u), p.back_glass_y, 0.0)
        self.assertLess(intersect(flash, self.case).volume, TOL)
        # The camera lip stands round the plateau, and the back plate is there beyond the opening.
        lip = box_between(x0 - 3, x1 + 3, p.back_glass_y, 0.0, z0 - 3, z1 + 3)
        self.assertGreater(intersect(lip, self.case).volume, 100.0)


if __name__ == "__main__":
    unittest.main()

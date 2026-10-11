"""Engineering invariants for the cased iPhone 17 model (design §9.1)."""

import unittest

from schlieren.cad import box_between, y_cylinder
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
                self.assertEqual(len(part.solids()), 1)

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

    def test_camera_glass_stands_under_the_case_lip(self):
        p = self.p
        ring = self.glass.bounding_box()
        self.assertAlmostEqual(ring.max.Y - p.back_glass_y, 3.45, places=3)  # Apple: back glass to glass.
        self.assertAlmostEqual(ring.max.Y, -p.camera_glass_recess, places=3)
        self.assertGreater(p.front_lip_height, 0.0)

    def test_bare_phone_sits_in_the_case_without_interference(self):
        self.assertLess((self.bare & self.case).volume, TOL)
        self.assertLess((self.glass & self.case).volume, TOL)
        self.assertLess((self.glass & self.bare).volume, TOL)

    def test_case_back_is_open_over_the_camera_plateau_and_flash(self):
        p = self.p
        x0, x1 = p.x_of(p.plateau_v[0]), p.x_of(p.plateau_v[1])
        z0, z1 = p.z_of(p.plateau_u[1]), p.z_of(p.plateau_u[0])
        end = (z1 - z0) / 2  # The plateau's round ends.
        over_plateau = box_between(x0 + end, x1 - end, p.back_glass_y, 0.0, z0, z1)
        self.assertLess((over_plateau & self.case).volume, TOL)
        flash = y_cylinder(p.flash_diameter, p.x_of(p.flash_v), p.z_of(p.flash_u), p.back_glass_y, 0.0)
        self.assertLess((flash & self.case).volume, TOL)
        # The camera lip stands round the plateau, and the back plate is there beyond the opening.
        lip = box_between(x0 - 3, x1 + 3, p.back_glass_y, 0.0, z0 - 3, z1 + 3)
        self.assertGreater((lip & self.case).volume, 100.0)


if __name__ == "__main__":
    unittest.main()

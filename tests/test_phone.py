"""Engineering invariants for the cased iPhone 17 model (design §9.1)."""

import unittest

from schlieren.cad import box_between, intersect, y_cylinder
from schlieren.parts.phone import (
    BUTTONS,
    PhoneParameters,
    build_bare_phone,
    build_camera_cover,
    build_case,
    build_phone,
)

TOL = 1e-3  # mm


class PhoneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = PhoneParameters()
        cls.bare = build_bare_phone(cls.p)
        cls.case = build_case(cls.p)
        cls.cover = build_camera_cover(cls.p)
        # The camera glass rings: the part of the phone standing above the plateau top.
        above_plateau = box_between(
            -1000, 1000, cls.p.back_glass_y + cls.p.plateau_height + 0.01, 1000, -1000, 1000
        )
        cls.glass = intersect(cls.bare, above_plateau)

    def test_each_part_is_one_valid_solid(self):
        for name, part in (("bare", self.bare), ("case", self.case)):
            with self.subTest(part=name):
                self.assertTrue(part.is_valid)
                self.assertEqual(len(part.solids()), 1)
        self.assertEqual(len(self.glass.solids()), 2)  # The two camera glass rings.

    def test_bare_phone_is_apples_body_with_protruding_buttons(self):
        p, box = self.p, self.bare.bounding_box()
        pushed = max(b.protrusion for b in BUTTONS)
        self.assertAlmostEqual(box.size.X, 149.61, places=3)
        self.assertAlmostEqual(box.size.Z, 71.45 + 2 * pushed, places=3)
        self.assertAlmostEqual(box.min.Y, p.front_glass_y, places=3)
        self.assertAlmostEqual(box.max.Y, p.back_glass_y + p.camera_glass_height, places=3)  # The glass.

    def test_case_outside_is_the_measured_cased_phone(self):
        p, box = self.p, self.case.bounding_box()
        self.assertAlmostEqual(-box.min.X, 34.3, places=3)  # Main camera from the near edge, §9.1.
        self.assertAlmostEqual(-box.min.Z, 60.6, places=3)  # Main camera above the lower edge, §9.1.
        # The back plane is the cover top: 0.080 in over the 1.78 mm plateau, over the back glass.
        flat_back = -(1.78 + 0.080 * 25.4 - 0.125 * 25.4)
        self.assertAlmostEqual(box.min.Y, flat_back - 0.540 * 25.4, places=3)  # Measured depth to the front.
        self.assertAlmostEqual(box.max.Y, flat_back + 0.050 * 25.4, places=3)  # The ridge top.
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

    def test_camera_opening_is_the_measured_size_centered_on_the_plateau_and_hugging_the_fillet_foot(self):
        p = self.p
        xc = (p.x_of(p.plateau_v[0]) + p.x_of(p.plateau_v[1])) / 2
        z_hi = p.z_of(p.plateau_foot_u[0])  # The camera-side edge, at the fillet foot.
        half = 1.590 * 25.4 / 2
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

    def test_flash_is_a_6_28_mm_disc_flush_with_the_back_glass_centered_on_the_plateau_lengthwise(self):
        p = self.p
        flash = {c.label: c for c in build_phone(p).children}["Flash"].bounding_box()
        self.assertAlmostEqual(flash.size.X, 6.28, places=3)  # Apple, Detail D.
        self.assertAlmostEqual(flash.size.Z, 6.28, places=3)
        self.assertAlmostEqual(flash.max.Y, p.back_glass_y, places=3)  # Flush with the back glass.
        self.assertAlmostEqual((flash.min.X + flash.max.X) / 2, p.x_of(22.48), places=3)
        self.assertAlmostEqual((flash.min.Z + flash.max.Z) / 2, p.z_of(30.41), places=3)
        plateau_middle = (p.x_of(p.plateau_v[0]) + p.x_of(p.plateau_v[1])) / 2
        self.assertAlmostEqual((flash.min.X + flash.max.X) / 2, plateau_middle, places=3)
        # Beside the plateau: its foot is clear of the flash.
        self.assertGreater(p.z_of(p.plateau_foot_u[1]) - flash.max.Z, 1.0)

    def test_camera_glass_rings_are_separate_16_mm_windows(self):
        self.assertAlmostEqual(self.p.camera_ring_diameter, 16.0, places=3)  # Apple: 2X Ø16.00.
        self.assertGreater(17.72 - self.p.camera_ring_diameter, 1.0)  # The rings do not touch.

    def test_camera_glass_stands_3_45_mm_above_the_back_glass_under_the_cover_top(self):
        p = self.p
        ring = self.glass.bounding_box()
        self.assertAlmostEqual(ring.max.Y - p.back_glass_y, 3.45, places=3)  # Apple: back glass to glass.
        self.assertLess(ring.max.Y, self.cover.bounding_box().max.Y)

    def test_camera_cover_top_is_the_back_plane_and_stands_under_the_ridge_top(self):
        p, box = self.p, self.cover.bounding_box()
        self.assertAlmostEqual(box.max.Y, 0.0, places=3)  # The back plane, where the lens seats.
        self.assertAlmostEqual(box.min.Y, p.back_glass_y + p.plateau_height, places=3)  # On the plateau top.
        self.assertAlmostEqual(box.size.Y, 0.080 * 25.4, places=3)
        self.assertAlmostEqual(p.camera_cover_recess, 0.050 * 25.4 - (1.78 + 0.080 * 25.4 - 0.125 * 25.4), 3)
        self.assertGreater(p.camera_cover_recess, 0.0)

    def test_camera_cover_is_the_plateau_stadium_counterbored_for_the_glass_rings(self):
        p, box = self.p, self.cover.bounding_box()
        self.assertTrue(self.cover.is_valid)
        self.assertEqual(len(self.cover.solids()), 1)
        self.assertAlmostEqual(
            box.size.X, p.plateau_v[1] - p.plateau_v[0], places=3
        )  # Plateau top, full size.
        self.assertAlmostEqual(box.size.Z, p.plateau_u[1] - p.plateau_u[0], places=3)
        self.assertLess(intersect(self.cover, self.bare).volume, TOL)  # Rings sit in the bores.
        for x, z in ((p.x_of(p.main_camera_from_end), p.z_of(p.camera_from_long_edge)),):
            under = intersect(self.cover, y_cylinder(p.camera_ring_diameter, x, z, -10.0, 10.0))
            self.assertGreater(under.volume, 0.0)  # The web over the glass.
            lower = intersect(self.cover, y_cylinder(p.camera_ring_diameter, x, z, -10.0, -0.5))
            self.assertLess(lower.volume, TOL)  # The bore is open below the web.

    def test_back_plate_is_0_125_in_and_front_rim_is_what_the_depth_leaves(self):
        p = self.p
        x0 = p.x_near + p.length - 20  # Well clear of the camera opening and ridge.
        plate = 0.125 * 25.4

        def case_in(y0, y1):
            return intersect(box_between(x0, x0 + 5, y0, y1, -5, 5), self.case).volume

        self.assertAlmostEqual(case_in(p.back_glass_y, p.back_glass_y + plate), 5 * 10 * plate, places=2)
        self.assertLess(case_in(p.back_glass_y + plate + 0.05, p.back_glass_y + plate + 1.0), TOL)
        self.assertAlmostEqual(
            self.bare.bounding_box().min.Y - self.case.bounding_box().min.Y, 2.591, places=3
        )

    def test_camera_opening_flares_from_the_back_glass_to_the_ridge_top(self):
        p = self.p
        length, width, _ = p.camera_opening_at(p.back_glass_y)
        self.assertAlmostEqual(length, 1.590 * 25.4, places=3)  # Measured at the back glass.
        self.assertAlmostEqual(width, 1.350 * 25.4, places=3)
        length, width, _ = p.camera_opening_at(p.camera_ridge_top_y)
        self.assertAlmostEqual(length, 1.750 * 25.4, places=3)  # Measured at the ridge top.
        self.assertAlmostEqual(width, 1.475 * 25.4, places=3)
        xc, zc = p.camera_opening_center
        eps = 0.05

        def case_at(x, z, y):
            return intersect(
                box_between(x - eps, x + eps, y - eps, y + eps, z - eps, z + eps), self.case
            ).volume

        for y in (p.back_glass_y + 0.5, p.flat_back_y - 0.5, p.camera_ridge_top_y - 0.5):
            length, width, _ = p.camera_opening_at(y)
            with self.subTest(y=y):
                self.assertLess(case_at(xc + length / 2 - 0.1, zc, y), TOL)  # Just inside the end wall.
                self.assertGreater(case_at(xc + length / 2 + 0.1, zc, y), 1e-4)  # Just outside it.
                self.assertLess(case_at(xc, zc + width / 2 - 0.1, y), TOL)
                self.assertGreater(case_at(xc, zc + width / 2 + 0.1, y), 1e-4)

    def test_camera_opening_corners_follow_the_fillet_foot_radius(self):
        p = self.p
        self.assertAlmostEqual(p.camera_opening_corner_radius, (26.06 - 1.18) / 2, places=3)  # Foot's ends.
        xc, zc = p.camera_opening_center
        y = p.flat_back_y - 0.5
        length, width, r = p.camera_opening_at(y)
        c = (xc + length / 2 - r, zc + width / 2 - r)  # Center of one corner's arc.
        eps = 0.05

        def case_at(x, z):
            return intersect(
                box_between(x - eps, x + eps, y - eps, y + eps, z - eps, z + eps), self.case
            ).volume

        diagonal = r * 2**-0.5
        self.assertLess(case_at(c[0] + diagonal * 0.98, c[1] + diagonal * 0.98), TOL)  # Just inside the arc.
        self.assertGreater(case_at(c[0] + diagonal * 1.03, c[1] + diagonal * 1.03), 1e-4)  # Just outside it.

    def test_camera_ridge_has_the_measured_height_foot_and_flat_top_width(self):
        p = self.p
        xc, zc = p.camera_opening_center
        flat, top = p.flat_back_y, p.camera_ridge_top_y
        self.assertAlmostEqual(top - flat, 0.050 * 25.4, places=3)
        eps = 0.04

        def case_in(x0, x1, y0, y1):
            return intersect(box_between(x0, x1, y0, y1, zc - 1, zc + 1), self.case).volume

        def inner_end(y):
            return xc + p.camera_opening_at(y)[0] / 2

        # At the foot, 0.085 in wide beyond the opening's wall at that height.
        end, foot = inner_end(flat + eps), 0.085 * 25.4 - 0.1
        self.assertGreater(case_in(end + 0.1, end + foot, flat + eps, flat + 2 * eps), 1e-3)
        self.assertLess(
            case_in(end + 0.085 * 25.4 + 0.2, end + 0.085 * 25.4 + 1.2, flat + eps, flat + 2 * eps), TOL
        )
        # The flat top, 0.040 in wide.
        end, flat_top = inner_end(top - eps), 0.040 * 25.4
        self.assertGreater(case_in(end + 0.1, end + flat_top - 0.1, top - 2 * eps, top - eps), 1e-3)
        self.assertLess(case_in(end + flat_top + 0.2, end + flat_top + 1.2, top - 2 * eps, top - eps), TOL)
        self.assertGreater(p.camera_ridge_height, p.camera_cover_height - p.case_back_thickness)

    def test_ridge_outer_wall_runs_down_over_the_case_back_edge_round_on_the_camera_side(self):
        p = self.p
        xc, zc = p.camera_opening_center
        flat = p.flat_back_y
        # At the camera-side edge the ridge's outer wall comes within the case edge round (2.0 mm) of the side.
        outer_z = zc + p.camera_opening_at(flat)[1] / 2 + 0.085 * 25.4
        self.assertLess(p.z_upper + p.case_side_wall - outer_z, p.case_edge_fillet)
        eps = 0.04
        # The wall continues straight down: material at the wall's foot, in the round that would be bare.
        z = outer_z - 0.1
        probe = intersect(box_between(xc - 1, xc + 1, flat - 1.5, flat - 1.5 + eps, z, z + eps), self.case)
        self.assertGreater(probe.volume, 1e-5)

    def test_bare_phone_sits_in_the_case_without_interference(self):
        self.assertLess(intersect(self.bare, self.case).volume, TOL)

    def test_case_back_is_open_over_the_camera_plateau_and_flash(self):
        p = self.p
        x0, x1 = p.x_of(p.plateau_v[0]), p.x_of(p.plateau_v[1])
        z0, z1 = p.z_of(p.plateau_u[1]), p.z_of(p.plateau_u[0])
        end = (z1 - z0) / 2  # The plateau's round ends.
        over_plateau = box_between(x0 + end, x1 - end, p.back_glass_y, 0.0, z0, z1)
        self.assertLess(intersect(over_plateau, self.case).volume, TOL)
        flash = y_cylinder(p.flash_diameter, p.x_of(p.flash_v), p.z_of(p.flash_u), p.back_glass_y, 0.0)
        self.assertLess(intersect(flash, self.case).volume, TOL)
        # The back plate is there beyond the opening.
        lip = box_between(x0 - 3, x1 + 3, p.back_glass_y, 0.0, z0 - 3, z1 + 3)
        self.assertGreater(intersect(lip, self.case).volume, 100.0)


if __name__ == "__main__":
    unittest.main()

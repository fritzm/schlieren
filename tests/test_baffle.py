"""Slit baffle (§7.8): clamp, relief, collars, net windows, foil, and parameter invariants."""

import unittest
from dataclasses import replace
from math import cos, radians, sin

from build123d import Vector

from schlieren.cad import y_cylinder
from schlieren.parts.baffle import BaffleParameters, build_baffle, build_baffle_foil, clamp_hardware
from schlieren.testing import overlap_volume
from schlieren.vendor_cad import MCMASTER_91292A114_LENGTH


class BaffleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = BaffleParameters()
        cls.p.validate()
        cls.body = build_baffle(cls.p)
        cls.foil = build_baffle_foil(cls.p)

    def inside(self, x, y, z):
        return self.body.is_inside(Vector(x, y, z))

    def on_net(self, azimuth_degrees, y, radius):
        """A point on the net at an azimuth measured from +z toward +x."""
        a = radians(azimuth_degrees)
        return self.inside(radius * sin(a), y, radius * cos(a))

    def test_one_valid_solid_with_the_envelope(self):
        p = self.p
        self.assertEqual(len(self.body.solids()), 1)
        self.assertTrue(self.body.is_valid)
        box = self.body.bounding_box()
        self.assertAlmostEqual(box.max.Y, 0, places=6)  # The clamp's front face butts the ring.
        self.assertAlmostEqual(box.min.Y, -p.length, places=6)
        self.assertAlmostEqual(box.min.Z, -p.clamp_diameter / 2, places=6)
        self.assertAlmostEqual(box.max.Z, p.ear_top_z, places=6)  # Ears up.
        self.assertAlmostEqual(box.max.X - box.min.X, p.clamp_diameter, places=6)

    def test_clamp_bore_slips_over_the_spigot_and_stops_short_of_its_end(self):
        p = self.p
        spigot = y_cylinder(p.spigot_diameter, 0, 0, p.spigot_end_y, 1.0)
        self.assertAlmostEqual(overlap_volume(spigot, self.body), 0, places=6)
        radius = p.clamp_bore / 2
        self.assertFalse(self.inside(0, -3.0, -(radius - 0.05)))  # Bore.
        self.assertTrue(self.inside(0, -3.0, -(radius + 0.05)))  # Wall.
        # The shoulder (the collar's face) is the bore's end, spigot_end_gap short of the spigot's.
        below = -(p.net_bore / 2 + 0.5)
        self.assertFalse(self.inside(0, p.shoulder_y + 0.1, below))
        self.assertTrue(self.inside(0, p.shoulder_y - 0.1, below))
        self.assertAlmostEqual(p.spigot_end_y - p.shoulder_y, p.spigot_end_gap)

    def test_slit_runs_the_clamp_and_ends_in_the_relief_hole(self):
        p = self.p
        top = p.clamp_diameter / 2 - 0.5  # In the top wall.
        self.assertFalse(self.inside(0, -3.0, top))  # The slit,
        self.assertFalse(self.inside(0, p.relief_y, top))  # the relief hole's center,
        self.assertTrue(self.inside(0, p.relief_y - p.relief_diameter / 2 - 0.1, top))  # Solid beyond it.
        self.assertTrue(self.inside(0, p.relief_y, -top))  # Below: intact.
        # The slit is split_gap wide: both faces are ear material.
        self.assertTrue(self.inside(p.split_gap / 2 + 0.1, -3.0, p.ear_top_z - 0.5))
        self.assertTrue(self.inside(-p.split_gap / 2 - 0.1, -3.0, p.ear_top_z - 0.5))
        self.assertFalse(self.inside(0, -3.0, p.ear_top_z - 0.5))

    def test_screw_hole_and_nut_pocket_cross_the_ears(self):
        p = self.p
        y, z = p.screw_y, p.screw_z
        for x in (p.screw_ear_outer_x + 0.3, -p.split_gap / 2 - 0.3, p.split_gap / 2 + 0.3):
            self.assertFalse(self.inside(x, y, z), msg=f"hole at x={x}")
        # The nut pocket opens on the 4.5 mm ear's outer face and leaves an inner wall.
        self.assertFalse(self.inside(p.nut_ear_outer_x - 0.5, y, z + 2.5))
        self.assertTrue(self.inside(p.nut_ear_outer_x - p.nut_pocket_depth - 0.3, y, z + 2.5))
        self.assertTrue(
            self.inside(p.screw_ear_outer_x + 0.3, y, z + 2.5)
        )  # The screw ear is solid round the hole.
        # The 12 mm screw reaches through both ears to the nut.
        reach = p.nut_ear_outer_x - p.screw_ear_outer_x
        self.assertGreater(MCMASTER_91292A114_LENGTH + 3.0, reach)  # Head height included.
        self.assertGreater(MCMASTER_91292A114_LENGTH, reach - p.nut_pocket_depth + p.nut_thickness)

    def test_collars_are_solid_and_the_net_has_windows_and_triangles(self):
        p = self.p
        r_mean = (p.net_diameter - p.vane_depth) / 2
        far_row = p.row_count - 1
        # Window centers: row r at azimuth (k + (r mod 2) / 2) * pitch; row 0 and the last row sit on the
        # collar faces, clipped to triangles. Collar faces are intact beyond them.
        row_y = lambda row: p.collar_back_y - row * p.row_pitch  # noqa: E731
        azimuth = p.window_pitch_degrees  # A window azimuth in even rows, clear of the slit at the top.
        self.assertFalse(self.on_net(azimuth, row_y(0) - 0.5, r_mean))  # Triangle at the near collar.
        self.assertTrue(self.on_net(azimuth, row_y(0) + 0.5, r_mean))  # Collar.
        last = azimuth + ((far_row % 2) / 2) * p.window_pitch_degrees
        self.assertFalse(self.on_net(last, row_y(far_row) + 0.5, r_mean))  # Triangle at the far collar.
        self.assertTrue(self.on_net(last, row_y(far_row) - 0.5, r_mean))  # Far collar.
        # Interior: a window at its row, and a ligament halfway between neighbors.
        self.assertFalse(self.on_net(0.5 * p.window_pitch_degrees, row_y(1), r_mean))
        self.assertTrue(self.on_net(0.25 * p.window_pitch_degrees, (row_y(1) + row_y(2)) / 2, r_mean))
        # The ligaments are vanes: solid from the bore to the outside, across the vane depth.
        for radius in (p.net_bore / 2 + 0.1, r_mean, p.net_diameter / 2 - 0.1):
            self.assertTrue(
                self.on_net(0.25 * p.window_pitch_degrees, (row_y(1) + row_y(2)) / 2, radius), msg=radius
            )

    def test_the_bore_is_clear_of_vanes_and_wider_than_the_spigot_bore(self):
        p = self.p
        bore = y_cylinder(p.net_bore - 0.01, 0, 0, p.far_y, p.shoulder_y)
        self.assertAlmostEqual(overlap_volume(bore, self.body), 0, places=6)
        self.assertGreaterEqual(p.net_bore, p.spigot_bore)

    def test_foil_wraps_the_net_between_the_collars(self):
        p = self.p
        box = self.foil.bounding_box()
        self.assertAlmostEqual(box.min.Y, p.net_end_y, places=6)
        self.assertAlmostEqual(box.max.Y, p.collar_back_y, places=6)
        self.assertAlmostEqual(overlap_volume(self.foil, self.body), 0, places=6)
        self.assertLess(p.foil_diameter, p.clamp_diameter)  # The collars stand proud of the wrap.

    def test_hardware_sits_on_the_screw_axis(self):
        p = self.p
        screw, nut = clamp_hardware(p)
        for part in (screw, nut):
            center = part.bounding_box().center()
            self.assertAlmostEqual(center.Y, p.screw_y, delta=0.01)
            self.assertAlmostEqual(center.Z, p.screw_z, delta=0.01)
        self.assertAlmostEqual(screw.bounding_box().min.X, p.screw_ear_outer_x - 3.0, delta=0.05)  # Head.

    def test_rows_span_the_net_exactly(self):
        p = self.p
        self.assertAlmostEqual((p.row_count - 1) * p.row_pitch, p.net_length, places=9)
        self.assertGreater(
            p.window_half_diagonal, p.row_pitch / 2
        )  # Windows overlap their row neighbors' span.

    def test_validation_rejects_bad_layouts(self):
        for change in (
            {"clamp_bore_diametral_clearance": -0.1},  # Not a clearance.
            {"vane_depth": 9.0},  # Bore narrower than the spigot's.
            {"net_diameter": 35.0},  # The net as wide as the collars: no shoulder.
            {"relief_center_past_bore": 0.5},  # The relief breaks into the shoulder plane.
            {"relief_diameter": 1.0},  # Narrower than the split.
            {"nut_axial_clearance": 3.0},  # Pocket through the ear.
            {"window_ligament": 11.0},  # No window left.
            {"length": 30.0},  # Too short for a net.
        ):
            with self.assertRaises(ValueError, msg=str(change)):
                replace(self.p, **change).validate()


if __name__ == "__main__":
    unittest.main()

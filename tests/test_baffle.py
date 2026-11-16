"""Slit baffle: clamp, slit, ribs, helical net vanes, foil, and parameter invariants."""

import unittest
from dataclasses import replace
from math import cos, degrees, pi, radians, sin

from build123d import Vector

from schlieren.cad import y_cylinder
from schlieren.parts.baffle import BaffleParameters, build_baffle, build_baffle_foil, clamp_hardware
from schlieren.testing import overlap_volume, slow
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
        self.assertAlmostEqual(box.min.Z, -p.rib_diameter / 2, places=6)
        self.assertAlmostEqual(box.max.Z, p.ear_top_z, places=6)  # Ears up.
        self.assertAlmostEqual(box.max.X - box.min.X, p.rib_diameter, places=6)

    def test_clamp_bore_slips_over_the_spigot_and_stops_short_of_its_end(self):
        p = self.p
        spigot = y_cylinder(p.spigot_diameter, 0, 0, p.spigot_end_y, 1.0)
        self.assertAlmostEqual(overlap_volume(spigot, self.body), 0, places=6)
        radius = p.clamp_bore / 2
        self.assertFalse(self.inside(0, -3.0, -(radius - 0.05)))  # Bore.
        self.assertTrue(self.inside(0, -3.0, -(radius + 0.05)))  # Wall.
        # One bore runs the whole length: no shoulder, no step (the net's inside is the clamp's).
        self.assertFalse(self.inside(0, p.rib_back_y - 5.0, -(radius - 0.05)))
        self.assertFalse(self.inside(0, p.far_y + p.far_rib_length + 5.0, -(radius - 0.05)))
        self.assertAlmostEqual(p.net_bore, p.clamp_bore)
        self.assertAlmostEqual(p.net_diameter, p.clamp_diameter)

    def test_slit_runs_the_clamp_and_rib_into_the_first_cell(self):
        p = self.p
        top = p.clamp_diameter / 2 - 0.5  # In the top wall.
        self.assertFalse(self.inside(0, -3.0, top))  # The slit,
        self.assertFalse(self.inside(0, p.rib_back_y + 0.1, top))  # through the rib's back face,
        self.assertFalse(self.inside(0, p.rib_back_y - 1.0, top))  # into the net's first cell.
        self.assertTrue(self.inside(0, p.rib_back_y + 0.1, -top))  # Below: intact.
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

    def vane_azimuth(self, start_azimuth, hand, depth):
        """A vane's centerline azimuth (degrees) `depth` mm behind the near rib's rear face."""
        return start_azimuth + hand * degrees(depth / self.p.mean_radius)

    def radii(self):
        p = self.p
        return (p.net_bore / 2 + 0.1, p.mean_radius, p.net_diameter / 2 - 0.1)

    def test_vanes_of_both_hands_run_helically_from_rib_to_rib(self):
        p = self.p
        start = p.vane_phase_degrees  # Both hands start at the same azimuths, 30° off the slit.
        for hand in (1, -1):
            for depth in (0.5, 10.0, 25.0, p.net_length - 0.5):
                azimuth = self.vane_azimuth(start, hand, depth)
                for radius in self.radii():  # Solid from the bore to the outside, at every depth.
                    self.assertTrue(
                        self.on_net(azimuth, p.rib_back_y - depth, radius), msg=(hand, depth, radius)
                    )

    def test_vanes_are_triangles_with_the_apex_on_the_bore(self):
        p = self.p
        depth = 10.0
        for hand in (1, -1):
            azimuth = self.vane_azimuth(p.vane_phase_degrees, hand, depth)
            y = p.rib_back_y - depth
            self.assertFalse(self.on_net(azimuth, y, p.net_bore / 2 - 0.05))  # Bore side of the apex.
            self.assertTrue(self.on_net(azimuth, y, p.net_bore / 2 + 0.05))
            # Width on the outside is the vane width; at mid depth about half of it.
            for radius, width in (
                (p.net_diameter / 2 - 0.05, p.vane_width),
                (p.mean_radius, p.vane_width / 2),
            ):
                inside = width / 2 * 0.9 / radius
                outside = width / 2 * 1.1 / radius
                self.assertTrue(self.on_net(azimuth + degrees(inside), y, radius))
                self.assertFalse(self.on_net(azimuth + degrees(outside), y, radius))

    def test_cells_are_open_and_crossings_are_solid_at_every_azimuth(self):
        p = self.p
        r_mean = p.mean_radius
        node_depth = r_mean * radians(
            p.vane_pitch_degrees / 2
        )  # Where a hand's vane has turned half a pitch.
        for k in range(p.vanes_per_hand):
            cell = k * p.vane_pitch_degrees  # Cell centers at the rib face and again 2 node-depths behind.
            for radius in self.radii():
                self.assertTrue(
                    self.on_net(cell, p.rib_back_y - node_depth, radius), msg=(k, radius)
                )  # A crossing.
            self.assertFalse(self.on_net(cell, p.rib_back_y - 2 * node_depth, r_mean), msg=k)
            self.assertFalse(self.on_net(cell, p.rib_back_y - 0.5, r_mean), msg=k)  # First cell, at the rib.

    def test_crossings_are_the_exact_union_of_the_two_vanes(self):
        """At a crossing the top is the patch of the outside cylinder bounded by the four edge helices: a diamond
        reaching half a vane width either side around the tube and to the crotch (a half width scaled to the mean
        radius) along it. Below the top nothing is added: under a side corner the flanks leave the wall open, as
        a lone vane would. The full crossing unit's crossings and the first row's (on the rib) are checked."""
        p = self.p
        r_out = p.net_diameter / 2
        half_angle = degrees(p.vane_width / 2 / r_out)
        crotch = p.vane_width / 2 / r_out * p.mean_radius
        on_top = r_out - 0.02
        for m in (1, 2, 5):
            node = p.vane_phase_degrees + m * p.vane_pitch_degrees / 2
            y = p.rib_back_y - m * p.node_pitch
            self.assertTrue(self.on_net(node + 0.9 * half_angle, y, on_top), msg=m)  # Side corners.
            self.assertTrue(self.on_net(node - 0.9 * half_angle, y, on_top), msg=m)
            self.assertFalse(self.on_net(node + 1.1 * half_angle, y, on_top), msg=m)
            self.assertTrue(self.on_net(node, y - 0.9 * crotch, on_top), msg=m)  # Crotch corners.
            self.assertTrue(self.on_net(node, y + 0.9 * crotch, on_top), msg=m)
            self.assertFalse(self.on_net(node, y - 1.1 * crotch, on_top), msg=m)
            self.assertFalse(self.on_net(node + 0.9 * half_angle, y, p.mean_radius), msg=m)  # No fill below.
            self.assertFalse(self.on_net(node, y - crotch, p.mean_radius), msg=m)

    @slow
    def test_net_builds_for_nearby_dimensions(self):
        """The net's construction holds as dimensions change: each build is one valid solid whose volume is the
        sum of its parts (build_baffle raises otherwise)."""
        for change in ({"vane_width": 1.8}, {"length": 83.0}, {"clamp_wall": 2.5}):
            body = build_baffle(replace(self.p, **change))
            self.assertEqual(len(body.solids()), 1, msg=str(change))

    def test_ribs_close_the_net_at_both_ends(self):
        p = self.p
        for y in (p.rib_back_y + 0.5, p.far_y + 0.5):
            self.assertTrue(self.on_net(45, y, p.mean_radius))
        self.assertAlmostEqual(self.body.bounding_box().min.Y, -p.length, places=6)

    def test_the_bore_is_clear_and_wider_than_the_spigot_bore(self):
        p = self.p
        bore = y_cylinder(p.net_bore - 0.01, 0, 0, p.far_y, p.rib_back_y)
        self.assertAlmostEqual(overlap_volume(bore, self.body), 0, places=6)
        self.assertGreaterEqual(p.net_bore, p.spigot_bore)

    def test_foil_wraps_the_net_between_the_ribs(self):
        p = self.p
        box = self.foil.bounding_box()
        self.assertAlmostEqual(box.min.Y, p.net_end_y, places=6)
        self.assertAlmostEqual(box.max.Y, p.rib_back_y, places=6)
        self.assertAlmostEqual(overlap_volume(self.foil, self.body), 0, places=6)
        self.assertLess(p.foil_diameter, p.rib_diameter)  # The ribs stand proud of the wrap.
        self.assertAlmostEqual(p.net_diameter, p.clamp_diameter)  # No step from the clamp to the net.

    def test_hardware_sits_on_the_screw_axis(self):
        p = self.p
        screw, nut = clamp_hardware(p)
        for part in (screw, nut):
            center = part.bounding_box().center()
            self.assertAlmostEqual(center.Y, p.screw_y, delta=0.01)
            self.assertAlmostEqual(center.Z, p.screw_z, delta=0.01)
        self.assertAlmostEqual(screw.bounding_box().min.X, p.screw_ear_outer_x - 3.0, delta=0.05)  # Head.

    def test_vane_pitch_is_45_degrees_at_the_mean_radius(self):
        p = self.p
        self.assertAlmostEqual(p.vane_lead, 2 * pi * p.mean_radius)
        self.assertEqual(p.vanes_per_hand, 6)

    def test_validation_rejects_bad_layouts(self):
        for change in (
            {"clamp_bore_diametral_clearance": -0.1},  # Not a clearance.
            {"rib_height": 0.2},  # Rib no higher than the foil.
            {"split_gap": 16.0},  # Wider than the cell it opens into.
            {"nut_axial_clearance": 3.0},  # Pocket through the ear.
            {"vane_width": 9.0},  # No cell left.
            {"length": 30.0},  # Too short for a net.
        ):
            with self.assertRaises(ValueError, msg=str(change)):
                replace(self.p, **change).validate()


if __name__ == "__main__":
    unittest.main()

"""Cassette envelope, datum preservation, and mating-carriage checks."""

import unittest
from dataclasses import replace
from math import radians, tan

from build123d import Circle, Compound, Cylinder, Pos, Rot, extrude

from schlieren.cad import ON_FLOOR, children_by_label, leaves
from schlieren.parts.carriage import CarriageParameters, build_carriage
from schlieren.parts.cassette import (
    CassetteParameters,
    ClampBarParameters,
    build_cassette,
    build_cassette_assembly,
    build_clamp_bar,
)


class CassetteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blank = build_cassette()

    def test_envelope_and_aperture(self):
        s = self.blank
        self.assertTrue(s.is_valid)
        self.assertEqual(len(s.solids()), 1)
        b = s.bounding_box()
        for actual, expected in ((b.size.X, 64), (b.size.Y, 64), (b.size.Z, 8), (b.min.Z, 0)):
            self.assertAlmostEqual(actual, expected)
        for z in (0.01, 2.5, 4.99):
            self.assertFalse(s.is_inside((11.99, 0, z)))
            self.assertTrue(s.is_inside((12.01, 0, z)))

    def test_four_bevels(self):
        p = CassetteParameters()
        z = p.thickness - p.bevel_depth / 2
        edge = p.size / 2 - (p.bevel_depth / 2) / tan(radians(p.bevel_angle))
        for rotation in (0, 90, 180, 270):
            s = Rot(Z=rotation) * self.blank
            self.assertTrue(s.is_inside((edge - 0.01, 0, z)))
            self.assertFalse(s.is_inside((edge + 0.01, 0, z)))

    def test_carriage_fit_and_swept_datum_tracks(self):
        p = CarriageParameters()
        c = CassetteParameters()
        for a, b in (
            (c.size, p.cassette_size),
            (c.thickness, p.cassette_thickness),
            (c.aperture_diameter, p.aperture_diameter),
            (c.bevel_depth, p.bevel_depth),
            (c.bevel_angle, p.bevel_angle),
        ):
            self.assertEqual(a, b)
        parts = children_by_label(build_carriage(p))
        for rotation in (0, 90, 180, 270):
            blank = Rot(Z=rotation) * self.blank
            for travel in (-5, 0, 5):
                moved = Pos(0, travel, p.plate_thickness + p.datum_projection) * blank
                for name, part in parts.items():
                    if "plunger" in name:
                        part = Pos(0, travel, 0) * part
                    self.assertLess((moved & part).volume, 1e-6, (rotation, travel, name))
                for x, y in p.datum_points:
                    self.assertTrue(blank.is_inside((x, y - travel, 0.01)))
                    # Entire nominal pin-head footprint stays on uninterrupted land.
                    track = Pos(x, y - travel, 0) * Cylinder(3.18 / 2, 0.02, align=ON_FLOOR)
                    self.assertAlmostEqual((track & blank).volume, track.volume, places=6)

    def test_countersinks_and_cleats(self):
        p = CassetteParameters()
        for x, y in p.clamp_holes:
            self.assertFalse(self.blank.is_inside((x, y, 2.5)))
            self.assertFalse(self.blank.is_inside((x + 3, y, 0.01)))
            self.assertTrue(self.blank.is_inside((x + 3, y, 0.2)))
            self.assertFalse(self.blank.is_inside((x + 1.69, y, 4.9)))
            self.assertTrue(self.blank.is_inside((x + 1.71, y, 4.9)))
            # Fastener shanks lie outside measured blade ends.
            self.assertGreater(abs(x) - p.bore_diameter / 2, 38.99 / 2)
        for x in (-p.cleat_x, p.cleat_x):
            self.assertTrue(self.blank.is_inside((x, 0, 7.99)))
            # No rounded foot may lift a wrapped filament off the front datum.
            self.assertFalse(self.blank.is_inside((x, p.cleat_base_diameter / 2 + 0.02, 5.01)))
            self.assertFalse(self.blank.is_inside((x, 2.1, 5.7)))
            self.assertTrue(self.blank.is_inside((x, 2.1, 7)))
            self.assertGreater(abs(x) - p.cleat_top_diameter / 2, 38.99 / 2)
        beam = Cylinder(12, 8, align=ON_FLOOR)
        self.assertLess((self.blank & beam).volume, 1e-6)

    def test_clamp_bars_and_hardware_clearance(self):
        p, b, c = CassetteParameters(), ClampBarParameters(), CarriageParameters()
        bar = build_clamp_bar(p, b)
        self.assertTrue(bar.is_valid)
        self.assertEqual(len(bar.solids()), 1)
        self.assertAlmostEqual(bar.bounding_box().size.Z, 4)
        self.assertAlmostEqual(c.keeper_opening_width / 2 - bar.bounding_box().max.X, 2)
        self.assertAlmostEqual(c.keeper_opening_width / 2 - p.clamp_hole_x - b.washer_od / 2, 2.5)
        # Full 7.2 mm washer-bearing lands on the bar top, excluding screw bore.
        for x in (-p.clamp_hole_x, p.clamp_hole_x):
            land = extrude(
                Pos(x, p.clamp_hole_y, b.thickness - 0.02) * (Circle(3.6) - Circle(p.bore_diameter / 2)),
                amount=0.01,
            )
            self.assertAlmostEqual((bar & land).volume, land.volume, places=6)
        nut_top = b.bar_bottom(p) + b.thickness + b.washer_thickness + b.nut_height
        self.assertGreater(b.screw_length + b.head_recess - nut_top, 0.5)
        beam = Cylinder(12, 20, align=ON_FLOOR)
        assembly = Compound([s for leaf in leaves(build_cassette_assembly(p, b)) for s in leaf.solids()])
        self.assertLess((assembly & beam).volume, 1e-6)
        # Include all screws, nuts, washers and pads in the carriage interference test.
        parts = children_by_label(build_carriage(c))
        for rotation in (0, 90, 180, 270):
            for travel in (-5, 0, 5):
                moved = Pos(0, travel, c.plate_thickness + c.datum_projection) * (Rot(Z=rotation) * assembly)
                for name, part in parts.items():
                    if "plunger" in name:
                        part = Pos(0, travel, 0) * part
                    self.assertLess((moved & part).volume, 1e-6, (rotation, travel, name))
        # Thin media at zero lift still clears the 12 mm plunger top with relief.
        self.assertGreater(
            c.plate_thickness + c.datum_projection + p.thickness + b.epdm_thickness + b.end_relief_depth,
            c.body_top,
        )

    def test_invalid_parameters(self):
        for changes in (
            {"bevel_angle": 90},
            {"bevel_angle": 0},
            {"bevel_depth": 5},
            {"aperture_diameter": 64},
            {"size": float("nan")},
        ):
            with self.assertRaises(ValueError):
                build_cassette(replace(CassetteParameters(), **changes))


if __name__ == "__main__":
    unittest.main()

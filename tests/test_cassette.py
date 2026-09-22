"""Cassette envelope, datum preservation, and mating-carriage checks."""
import unittest
from dataclasses import replace
from math import radians, tan

import cadquery as cq

from schlieren.parts.cassette import (CassetteParameters, ClampBarParameters, build_cassette,
                                      build_clamp_bar, build_cassette_assembly)
from schlieren.parts.carriage import CarriageParameters, build_carriage


class CassetteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blank = build_cassette().val()

    def test_envelope_and_aperture(self):
        s = self.blank
        self.assertTrue(s.isValid())
        self.assertEqual(len(s.Solids()), 1)
        b = s.BoundingBox()
        for actual, expected in ((b.xlen, 64), (b.ylen, 64), (b.zlen, 8), (b.zmin, 0)):
            self.assertAlmostEqual(actual, expected)
        for z in (0.01, 2.5, 4.99):
            self.assertFalse(s.isInside((11.99, 0, z)))
            self.assertTrue(s.isInside((12.01, 0, z)))

    def test_four_bevels(self):
        p = CassetteParameters()
        z = p.thickness - p.bevel_depth / 2
        edge = p.size / 2 - (p.bevel_depth / 2) / tan(radians(p.bevel_angle))
        for rotation in (0, 90, 180, 270):
            s = self.blank.rotate((0, 0, 0), (0, 0, 1), rotation)
            self.assertTrue(s.isInside((edge - 0.01, 0, z)))
            self.assertFalse(s.isInside((edge + 0.01, 0, z)))

    def test_carriage_fit_and_swept_datum_tracks(self):
        p = CarriageParameters()
        c = CassetteParameters()
        for a, b in ((c.size, p.cassette_size), (c.thickness, p.cassette_thickness),
                     (c.aperture_diameter, p.aperture_diameter),
                     (c.bevel_depth, p.bevel_depth), (c.bevel_angle, p.bevel_angle)):
            self.assertEqual(a, b)
        parts = {n: o.obj.val() for n, o in build_carriage(p).objects.items() if o.obj is not None}
        for rotation in (0, 90, 180, 270):
            blank = self.blank.rotate((0, 0, 0), (0, 0, 1), rotation)
            for travel in (-5, 0, 5):
                moved = blank.translate((0, travel, p.plate_thickness + p.datum_projection))
                for name, part in parts.items():
                    if "plunger" in name:
                        part = part.translate((0, travel, 0))
                    self.assertLess(moved.intersect(part).Volume(), 1e-6, (rotation, travel, name))
                for x, y in p.datum_points:
                    self.assertTrue(blank.isInside((x, y - travel, 0.01)))
                    # Entire nominal pin-head footprint stays on uninterrupted land.
                    track = cq.Workplane("XY", origin=(x, y - travel, 0)).circle(3.18 / 2).extrude(0.02).val()
                    self.assertAlmostEqual(track.intersect(blank).Volume(), track.Volume(), places=6)

    def test_countersinks_and_cleats(self):
        p = CassetteParameters()
        for x, y in p.clamp_holes:
            self.assertFalse(self.blank.isInside((x, y, 2.5)))
            self.assertFalse(self.blank.isInside((x + 3, y, 0.01)))
            self.assertTrue(self.blank.isInside((x + 3, y, 0.2)))
            self.assertFalse(self.blank.isInside((x + 1.69, y, 4.9)))
            self.assertTrue(self.blank.isInside((x + 1.71, y, 4.9)))
            # Fastener shanks lie outside measured blade ends.
            self.assertGreater(abs(x) - p.bore_diameter / 2, 38.99 / 2)
        for x in (-p.cleat_x, p.cleat_x):
            self.assertTrue(self.blank.isInside((x, 0, 7.99)))
            # No rounded foot may lift a wrapped filament off the front datum.
            self.assertFalse(self.blank.isInside((x, p.cleat_base_diameter / 2 + 0.02, 5.01)))
            self.assertFalse(self.blank.isInside((x, 2.1, 5.7)))
            self.assertTrue(self.blank.isInside((x, 2.1, 7)))
            self.assertGreater(abs(x) - p.cleat_top_diameter / 2, 38.99 / 2)
        beam = cq.Workplane("XY").circle(12).extrude(8).val()
        self.assertLess(self.blank.intersect(beam).Volume(), 1e-6)

    def test_clamp_bars_and_hardware_clearance(self):
        p, b, c = CassetteParameters(), ClampBarParameters(), CarriageParameters()
        bar = build_clamp_bar(p, b).val()
        self.assertTrue(bar.isValid())
        self.assertEqual(len(bar.Solids()), 1)
        self.assertAlmostEqual(bar.BoundingBox().zlen, 4)
        self.assertAlmostEqual(c.keeper_opening_width / 2 - bar.BoundingBox().xmax, 2)
        self.assertAlmostEqual(c.keeper_opening_width / 2 - p.clamp_hole_x - b.washer_od / 2, 2.5)
        # Full 7.2 mm washer-bearing lands on the bar top, excluding screw bore.
        for x in (-p.clamp_hole_x, p.clamp_hole_x):
            land = cq.Workplane("XY", origin=(x, p.clamp_hole_y, b.thickness - 0.02)).circle(
                3.6).circle(p.bore_diameter / 2).extrude(0.01).val()
            self.assertAlmostEqual(bar.intersect(land).Volume(), land.Volume(), places=6)
        nut_top = b.bar_bottom(p) + b.thickness + b.washer_thickness + b.nut_height
        self.assertGreater(b.screw_length + b.head_recess - nut_top, 0.5)
        beam = cq.Workplane("XY").circle(12).extrude(20).val()
        assembly = build_cassette_assembly(p, b).toCompound()
        self.assertLess(assembly.intersect(beam).Volume(), 1e-6)
        # Include all screws, nuts, washers and pads in the carriage interference test.
        parts = {n: o.obj.val() for n, o in build_carriage(c).objects.items() if o.obj is not None}
        for rotation in (0, 90, 180, 270):
            for travel in (-5, 0, 5):
                moved = assembly.rotate((0, 0, 0), (0, 0, 1), rotation).translate(
                    (0, travel, c.plate_thickness + c.datum_projection))
                for name, part in parts.items():
                    if "plunger" in name:
                        part = part.translate((0, travel, 0))
                    self.assertLess(moved.intersect(part).Volume(), 1e-6, (rotation, travel, name))
        # Thin media at zero lift still clears the 12 mm plunger top with relief.
        self.assertGreater(c.plate_thickness + c.datum_projection + p.thickness
                           + b.epdm_thickness + b.end_relief_depth, c.body_top)

    def test_invalid_parameters(self):
        for changes in ({"bevel_angle": 90}, {"bevel_angle": 0}, {"bevel_depth": 5},
                        {"aperture_diameter": 64}, {"size": float("nan")}):
            with self.assertRaises(ValueError):
                build_cassette(replace(CassetteParameters(), **changes))


if __name__ == "__main__":
    unittest.main()

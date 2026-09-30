"""LED datum, calibration, assembly path, and hardware envelope invariants."""
import unittest
from dataclasses import replace

import cadquery as cq

from schlieren.parts.led_module import (LEDModuleParameters, build_led_bracket,
                                       build_heatsink_envelope, build_led_module_assembly)


class LEDModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = LEDModuleParameters()
        cls.bracket = build_led_bracket(cls.p).val()

    def test_solid_and_post_top_datum(self):
        p, s = self.p, self.bracket
        self.assertTrue(s.isValid())
        self.assertEqual(len(s.Solids()), 1)
        self.assertAlmostEqual(s.BoundingBox().zmin, 0)
        self.assertAlmostEqual(p.post_top + p.axis_z, 72.35)
        annulus = cq.Workplane("XY").circle(p.post_diameter / 2).circle(
            (p.m4_diameter + p.m4_diametral_clearance) / 2).extrude(0.01).val()
        self.assertAlmostEqual(s.intersect(annulus).Volume(), annulus.Volume(), places=6)
        tool = cq.Workplane("XY", origin=(0,0,p.tab_thickness)).circle(4).extrude(50).val()
        self.assertLess(s.intersect(tool).Volume(), 1e-7)
        self.assertFalse(s.isInside((0,0,p.tab_thickness / 2)))

    def test_calibration_clearance_and_vertical_assembly_path(self):
        p, s = self.p, self.bracket
        # Full continuous swept volume for ±3 mm, rather than only endpoints.
        sink = build_heatsink_envelope(p).val()
        # Explicit extruded convex hull of the octagon's vertical sweep.
        from math import pi, tan
        a, b, t = p.half_flat, p.half_flat * tan(pi / 8), p.calibration_half_travel
        plane = cq.Plane(origin=(0,p.front_y,p.axis_z), xDir=(1,0,0), normal=(0,-1,0))
        sweep = cq.Workplane(plane).polyline([(a,b+t),(b,a+t),(-b,a+t),(-a,b+t),
                                             (-a,-b-t),(-b,-a-t),(b,-a-t),(a,-b-t)]).close().extrude(
                                                 p.heatsink_depth).val()
        self.assertLess(s.intersect(sweep).Volume(), 1e-7)
        for travel in (-3,0,3):
            heatsink = build_heatsink_envelope(p, travel).val()
            self.assertTrue(heatsink.isValid())
            self.assertAlmostEqual(heatsink.BoundingBox().xlen, 55)
            self.assertAlmostEqual(heatsink.BoundingBox().ylen, 20)
            # Both rear lips overlap the rear-face footprint at all settings.
            for sign in (-1,1):
                x = sign * (p.inner_x - p.retaining_lip / 2)
                for z in (p.axis_z - 6, p.axis_z + 6):
                    self.assertTrue(s.isInside((x,p.heatsink_rear_y-0.01,z)))
                    self.assertTrue(heatsink.isInside((x,p.heatsink_rear_y+0.01,z)))
        # With pressure screws retracted, drop the envelope in from above.
        for lift in (5,10,20,30,50,70):
            self.assertLess(s.intersect(sink.translate((0,0,lift))).Volume(), 1e-7)

    def test_hardware_and_station_clearances(self):
        p, s = self.p, self.bracket
        assembly = build_led_module_assembly(p, with_shoe=True)
        parts = {name: obj.obj.val() for name, obj in assembly.objects.items()
                 if obj.obj is not None}
        for name, part in parts.items():
            if "screw reference" in name or "nut reference" in name:
                self.assertLess(s.intersect(part).Volume(), 1e-7, name)
                self.assertLess(build_heatsink_envelope(p).val().intersect(part).Volume(), 1e-7, name)
        sink = build_heatsink_envelope(p, -3).val().translate((0,0,p.post_top))
        station_bracket = s.translate((0,0,p.post_top))
        for name, part in parts.items():
            if any(label in name for label in ("TR50", "Rail shoe", "rail envelope", "datum disc")):
                self.assertLess(sink.intersect(part).Volume(), 1e-7, name)
                self.assertLess(station_bracket.intersect(part).Volume(), 1e-7, name)
        # Nut can enter from above; its top-loading pocket remains unobstructed.
        nut = next(part for name, part in parts.items() if "Right nut reference" in name)
        for lift in (0,1,3,6,12):
            self.assertLess(s.intersect(nut.translate((0,0,lift))).Volume(), 1e-7)

    def test_reject_unsupported_geometry(self):
        for changes in ({"heatsink_across_flats":45}, {"calibration_half_travel":5},
                        {"heatsink_depth":8}, {"pressure_screw_length":8},
                        {"optical_height":float("nan")}, {"heatsink_rear_y":6}):
            with self.assertRaises(ValueError):
                build_led_bracket(replace(self.p, **changes))
        for travel in (-3.01,3.01,float("nan")):
            with self.assertRaises(ValueError):
                build_heatsink_envelope(self.p, travel)


if __name__ == "__main__":
    unittest.main()

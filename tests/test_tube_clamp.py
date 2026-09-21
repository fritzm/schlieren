"""Fit and geometry invariants for the SM1 retaining clamp."""
from dataclasses import replace
from math import cos, pi
import unittest
import cadquery as cq
from schlieren.parts.tube_clamp import TubeClampParameters, build_tube_clamp


class TubeClampTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = TubeClampParameters()
        cls.s = build_tube_clamp(cls.p).val()

    def test_valid_solid_and_axial_width(self):
        self.assertTrue(self.s.isValid())
        self.assertEqual(len(self.s.Solids()), 1)
        self.assertAlmostEqual(self.s.BoundingBox().zlen, 8.0, places=5)

    def test_bore_and_single_full_depth_split(self):
        p = self.p
        bore = cq.Workplane('XY').circle(p.bore_diameter / 2).extrude(p.axial_width).val()
        self.assertLess(self.s.intersect(bore).Volume(), 1e-7)
        x = p.bore_diameter / 2 + p.radial_wall / 2
        for z in (0.1, p.axial_width / 2, p.axial_width - 0.1):
            self.assertFalse(self.s.isInside((x, 0, z)))
            self.assertTrue(self.s.isInside((-x, 0, z)))
        self.assertAlmostEqual(p.bore_diameter, 30.73)

    def test_hardware_fit_and_bearing_wall(self):
        p = self.p
        y0 = -p.split_gap / 2 - p.screw_ear_thickness
        yn = p.split_gap / 2 + p.nut_ear_thickness
        screw = cq.Solid.makeCylinder(1.5, p.screw_length,
            cq.Vector(p.screw_x, y0, p.axial_width / 2), cq.Vector(0, 1, 0))
        head = cq.Solid.makeCylinder(2.75, 3,
            cq.Vector(p.screw_x, y0, p.axial_width / 2), cq.Vector(0, -1, 0))
        nut = cq.Workplane(cq.Plane(origin=(p.screw_x, yn-p.nut_pocket_depth, p.axial_width/2),
            xDir=(1,0,0), normal=(0,1,0))).polygon(6, p.nut_across_flats/cos(pi/6)).extrude(p.nut_thickness).val()
        for solid in (screw, head, nut):
            self.assertLess(self.s.intersect(solid).Volume(), 1e-7)
        self.assertTrue(self.s.isInside((p.screw_x, yn-p.nut_pocket_depth-0.1, p.axial_width/2+2.2)))
        self.assertFalse(self.s.isInside((p.screw_x, yn-p.nut_pocket_depth+0.1, p.axial_width/2+2.2)))

    def test_outer_rims_are_filleted(self):
        rims = [f for f in self.s.Faces() if f.geomType() == 'TORUS'
                and abs(f._geomAdaptor().Torus().MinorRadius()-self.p.outer_rim_fillet)<1e-6]
        self.assertGreaterEqual(len(rims), 2)
        self.assertTrue(any(f.Center().z < 1 for f in rims))
        self.assertTrue(any(f.Center().z > 7 for f in rims))

    def test_clearance_variant_and_undersized_tab_rejection(self):
        self.assertTrue(build_tube_clamp(replace(self.p, tube_diametral_clearance=0.1)).val().isValid())
        with self.assertRaises(ValueError):
            build_tube_clamp(replace(self.p, axial_width=5))


if __name__ == '__main__':
    unittest.main()

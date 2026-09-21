"""Engineering invariants for the exploratory shoe (no external test runner)."""

from dataclasses import replace
import unittest

import cadquery as cq

from schlieren.parts.rail_shoe import RailShoeParameters, build_rail_shoe, reference_parts, viewer_assembly


class RailShoeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = RailShoeParameters()
        cls.shoe = build_rail_shoe(cls.p)
        cls.solid = cls.shoe.val()

    def test_single_valid_solid_and_envelope(self):
        self.assertTrue(self.solid.isValid())
        self.assertEqual(len(self.shoe.solids().vals()), 1)
        box = self.solid.BoundingBox()
        # Ears retain their original hardware clearances and overhang the bridge.
        for actual, expected in ((box.xlen, self.p.width),
                                 (box.ymin, -15.0), (box.ymax, self.p.ear_y_end),
                                 (box.zmin, -self.p.skirt_depth), (box.zmax, self.p.collar_top)):
            self.assertAlmostEqual(actual, expected, places=5)

    def test_post_disc_and_rail_do_not_intersect_abs(self):
        for name, reference in reference_parts(self.p).items():
            with self.subTest(name=name):
                self.assertLess(self.solid.intersect(reference.val()).Volume(), 1e-7)

    def test_post_bore_diameter(self):
        radii = [f._geomAdaptor().Cylinder().Radius() for f in self.solid.Faces()
                 if f.geomType() == "CYLINDER"]
        self.assertTrue(any(abs(r - self.p.post_bore / 2) < 1e-7 for r in radii))

    def test_m5_side_channel_holes(self):
        for x in (-self.p.width / 2 + 1, self.p.width / 2 - 1):
            self.assertFalse(self.solid.isInside((x, 0, -10)))
            self.assertTrue(self.solid.isInside((x, 4, -10)))

    def test_split_is_open_above_rounded_termination(self):
        self.assertFalse(self.solid.isInside((0, 9, 18)))
        self.assertFalse(self.solid.isInside((0, 9, self.p.split_relief_z)))
        self.assertTrue(self.solid.isInside((0, 9, self.p.bridge_top + 1)))

    def test_clamp_screw_and_nut_fit(self):
        p = self.p
        screw = cq.Solid.makeCylinder(1.5, p.clamp_screw_length,
            cq.Vector(-p.ear_outer_x, p.clamp_screw_y, p.clamp_screw_z), cq.Vector(1, 0, 0))
        self.assertLess(self.solid.intersect(screw).Volume(), 1e-7)
        from math import cos, pi
        nut = cq.Workplane("YZ", origin=(p.ear_outer_x - p.nut_pocket_depth,
            p.clamp_screw_y, p.clamp_screw_z)).polygon(6, p.clamp_nut_across_flats / cos(pi / 6)).extrude(p.clamp_nut_thickness)
        self.assertLess(self.solid.intersect(nut.val()).Volume(), 1e-7)

    def test_fabrication_clearance_can_be_changed(self):
        variant = build_rail_shoe(replace(self.p, post_diametral_clearance=0.10,
                                         rail_lateral_clearance_per_side=0.10))
        self.assertTrue(variant.val().isValid())

    def test_rejects_shim_interference(self):
        with self.assertRaises(ValueError):
            build_rail_shoe(replace(self.p, datum_counterbore_depth=0.1))

    def test_bridge_length_and_rail_top_seating(self):
        section = self.shoe.section(2).val().BoundingBox()
        self.assertAlmostEqual(section.ylen, 30.0, places=5)
        for y in (-13, 13):
            for x in (-7, 7):
                self.assertFalse(self.solid.isInside((x, y, -0.01)))
                self.assertTrue(self.solid.isInside((x, y, 0.01)))

    def test_counterbore_clearance_and_roof(self):
        p = self.p
        cavity = cq.Workplane("XY").circle(p.datum_counterbore_diameter / 2).extrude(p.datum_counterbore_depth)
        self.assertLess(self.solid.intersect(cavity.val()).Volume(), 1e-7)
        self.assertTrue(self.solid.isInside((0, 9, p.datum_counterbore_depth + 0.01)))
        self.assertAlmostEqual(p.datum_counterbore_diameter, 22.05)
        self.assertAlmostEqual(p.datum_counterbore_depth, 1.0)

    def test_post_has_separate_viewer_group(self):
        assembly = viewer_assembly(self.shoe, self.p)
        groups = {child.name: child for child in assembly.children}
        self.assertEqual(set(groups), {"Shoe", "Rail and datum", "Post"})
        self.assertEqual([child.name for child in groups["Post"].children], ["TR50_M"])


if __name__ == "__main__":
    unittest.main()

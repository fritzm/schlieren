"""Experimental ground-glass focus screen: datum plane, glass seating, gasket loading, and aperture."""

import unittest
from dataclasses import replace

from build123d import Vector

from schlieren.cad import children_by_label
from schlieren.parts.slit_focus_screen import (
    FocusScreenParameters,
    build_focus_screen_assembly,
    build_focus_screen_fixture,
    build_gasket,
    build_glass,
)
from schlieren.parts.slit_focus_target import build_focus_target
from schlieren.testing import overlap_volume, shared


class FocusScreenTests(unittest.TestCase):
    @shared
    def assembly(cls):
        return build_focus_screen_assembly(cls.p, include_support=False)

    @classmethod
    def setUpClass(cls):
        cls.p = FocusScreenParameters()
        cls.p.validate()
        cls.fixture = build_focus_screen_fixture(cls.p)
        cls.glass = build_glass(cls.p)
        cls.gasket = build_gasket(cls.p)

    def test_solids_are_single_and_valid(self):
        for part in (self.fixture, self.glass, self.gasket):
            self.assertEqual(len(part.solids()), 1)
            self.assertTrue(part.is_valid)

    def test_ground_face_is_the_same_datum_as_the_paper_target(self):
        # The ring seats on the rim at y = 0, so the glass's ground face is the target's paper/blade plane.
        self.assertAlmostEqual(self.glass.bounding_box().max.Y, 0, places=9)
        self.assertAlmostEqual(build_focus_target(self.p.target).bounding_box().max.Y, 0, places=9)
        self.assertAlmostEqual(self.fixture.bounding_box().max.Y, 0, places=9)

    def test_counterbore_clears_the_glass_and_floor_lip_overlaps_it(self):
        p = self.p
        y = -p.glass_thickness_nominal
        self.assertFalse(self.fixture.is_inside(Vector(p.glass_diameter / 2 + 0.05, y, 0)))
        self.assertTrue(self.fixture.is_inside(Vector(p.counterbore_diameter / 2 + 0.2, y, 0)))
        floor = -p.counterbore_depth
        self.assertTrue(self.fixture.is_inside(Vector(p.aperture_diameter / 2 + 0.3, floor - 0.5, 0)))
        self.assertFalse(self.fixture.is_inside(Vector(p.aperture_diameter / 2 - 0.3, floor - 0.5, 0)))

    def test_gasket_is_lightly_loaded_across_the_glass_tolerance(self):
        p = self.p
        for thickness in (p.glass_thickness_min, p.glass_thickness_nominal, p.glass_thickness_max):
            self.assertTrue(0.05 <= p.gasket_compression(thickness) <= 0.45)

    def test_glass_stack_does_not_interfere(self):
        children = children_by_label(self.assembly)
        fixture, ring = children["Focus screen fixture"], children["Retaining ring"]
        for name in ("Ground glass", "Gasket"):
            self.assertAlmostEqual(overlap_volume(children[name], fixture), 0, places=6)
            self.assertAlmostEqual(overlap_volume(children[name], ring), 0, places=6)
        self.assertAlmostEqual(overlap_volume(children["Ground glass"], children["Gasket"]), 0, places=6)

    def test_validate_rejects_paper_a_thin_wall_and_a_deep_counterbore(self):
        p = self.p
        with self.assertRaises(ValueError):
            replace(p, target=replace(p.target, paper_thickness=0.15)).validate()
        with self.assertRaises(ValueError):
            replace(p, counterbore_diametral_clearance=3.0).validate()
        with self.assertRaises(ValueError):
            replace(p, gasket_min_gap=6.0).validate()


if __name__ == "__main__":
    unittest.main()

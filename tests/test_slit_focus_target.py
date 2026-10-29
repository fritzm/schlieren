"""Experimental slit focus target: paper plane, ring interface, insert, and window invariants."""

import unittest
from dataclasses import replace

from build123d import Vector

from schlieren.cad import children_by_label
from schlieren.parts.slit_focus_target import (
    FocusTargetParameters,
    build_focus_target,
    build_focus_target_assembly,
    build_paper,
    build_retaining_ring,
)
from schlieren.parts.slit_stage import SlitStageParameters, head_location
from schlieren.testing import overlap_volume, shared
from schlieren.vendor_cad import SM1RC_M_THICKNESS


class FocusTargetTests(unittest.TestCase):
    @shared
    def assembly(cls):
        return build_focus_target_assembly(cls.p, include_support=False)

    @classmethod
    def setUpClass(cls):
        cls.p = FocusTargetParameters()
        cls.p.validate()
        cls.target = build_focus_target(cls.p)
        cls.ring = build_retaining_ring(cls.p)
        cls.paper = build_paper(cls.p)

    def test_printed_parts_are_single_valid_solids(self):
        for part in (self.target, self.ring, self.paper):
            self.assertEqual(len(part.solids()), 1)
            self.assertTrue(part.is_valid)

    def test_rim_face_is_the_blade_seat_plane_the_stage_head_puts_ahead_of_the_post(self):
        p = self.p
        self.assertAlmostEqual(self.target.bounding_box().max.Y, 0, places=9)
        self.assertAlmostEqual(self.paper.bounding_box().min.Y, 0, places=9)
        # The rim stands off the post axis exactly as the stage head's blades do.
        rim_from_post = SM1RC_M_THICKNESS / 2 + p.stage.ring_gap + p.barrel_length
        self.assertAlmostEqual(head_location(p.stage).position.Y, rim_from_post, places=9)

    def test_paper_plane_is_the_stage_blades_edge_plane_not_the_flexure_heads(self):
        p = self.p
        self.assertIsInstance(p.stage, SlitStageParameters)  # 2.9 mm overhang, not the flexure head's 1.5 mm.
        # The paper's rear face is the seat plane; the stage's inclined blades put their edges' mid-plane
        # within 0.02 mm of it, where the flexure head's 1.5 mm overhang would put them 0.076 mm off.
        edge_plane = p.stage.seated_blade_y(0, 0)
        self.assertAlmostEqual(self.paper.bounding_box().min.Y, edge_plane, delta=0.02)
        self.assertAlmostEqual(self.paper.bounding_box().min.Y, 0, places=9)

    def test_ring_interface_matches_the_stage_plate(self):
        s = self.p.stage
        box = self.target.bounding_box()
        self.assertAlmostEqual(box.min.Y, s.plate_back - s.spigot_length, places=9)
        # Spigot and shoulder diameters are the plate's, so the SM1RC/M and baffle tube seat the same way.
        self.assertTrue(self.target.is_inside(Vector(s.spigot_diameter / 2 - 0.2, s.plate_back - 6.0, 0)))
        self.assertFalse(self.target.is_inside(Vector(s.spigot_diameter / 2 + 0.2, s.plate_back - 6.0, 0)))
        self.assertTrue(
            self.target.is_inside(Vector(s.spigot_shoulder_diameter / 2 - 0.2, s.plate_back - 1.0, 0))
        )
        self.assertFalse(
            self.target.is_inside(Vector(s.spigot_shoulder_diameter / 2 + 0.2, s.plate_back - 1.0, 0))
        )

    def test_barrel_steps_out_to_the_rim_only_where_the_inserts_are(self):
        p = self.p
        y_barrel = -p.rim_length - 1.0
        for y, r, inside in (
            (y_barrel, p.barrel_diameter / 2 - 0.2, True),
            (y_barrel, p.barrel_diameter / 2 + 0.2, False),
            (-p.rim_length + 1.0, p.rim_diameter / 2 - 0.2, True),
            (-0.5, p.rim_diameter / 2 + 0.2, False),
        ):
            self.assertEqual(self.target.is_inside(Vector(r, y, 0)), inside)

    def test_bore_is_clear_end_to_end(self):
        p = self.p
        for y in (p.stage.plate_back - 5.0, p.stage.plate_back + 5.0, -0.5):
            self.assertFalse(self.target.is_inside(Vector(p.bore / 2 - 0.2, y, 0)))
            self.assertTrue(self.target.is_inside(Vector(p.bore / 2 + 0.2, y, 0)))

    def test_ring_window_passes_the_beam_and_ring_grips_the_rim(self):
        p = self.p
        self.assertLessEqual(p.ring_window_diameter, p.stage.tube_clear_diameter)
        self.assertGreater(p.ring_window_diameter, 2 * p.stage.lit_half_length)
        self.assertLess(p.ring_window_diameter, p.bore)
        self.assertFalse(
            self.ring.is_inside(Vector(p.ring_window_diameter / 2 - 0.2, p.ring_thickness / 2, 0))
        )
        self.assertTrue(
            self.ring.is_inside(Vector(p.ring_window_diameter / 2 + 0.2, p.ring_thickness / 2, 0))
        )

    def test_four_insert_holes_match_ring_screw_holes(self):
        p = self.p
        s = p.stage
        self.assertEqual(len(p.screw_xz()), 4)
        depth = s.insert_flange_recess_depth + s.insert_hole_depth
        for x, z in p.screw_xz():
            self.assertFalse(self.target.is_inside(Vector(x, -depth + 0.2, z)))
            self.assertTrue(self.target.is_inside(Vector(x, -depth - 0.3, z)))
            self.assertFalse(self.ring.is_inside(Vector(x, p.ring_thickness / 2, z)))
            self.assertTrue(
                self.ring.is_inside(Vector(x + s.screw_clearance / 2 + 0.3, p.ring_thickness / 2, z))
            )
            self.assertFalse(self.paper.is_inside(Vector(x, p.paper_thickness / 2, z)))

    def test_screws_run_through_the_inserts_without_bottoming(self):
        p = self.p
        s = p.stage
        self.assertGreaterEqual(p.screw_engagement, s.insert_installed_length - p.insert_engagement_margin)
        self.assertLessEqual(p.screw_engagement, s.insert_hole_depth)

    def test_insert_recesses_leave_walls(self):
        p = self.p
        r = p.screw_radius
        recess = p.stage.insert_flange_recess_diameter
        self.assertGreater(r - recess / 2 - p.bore / 2, 1.0)
        self.assertGreater(p.rim_diameter / 2 - (r + recess / 2), 1.0)

    def test_assembly_parts_do_not_interfere(self):
        children = children_by_label(self.assembly)
        self.assertAlmostEqual(
            overlap_volume(children["Retaining ring"], children["Focus target"]), 0, places=6
        )
        self.assertAlmostEqual(overlap_volume(children["Paper"], children["Retaining ring"]), 0, places=6)

    def test_validate_rejects_a_window_the_baffle_tube_cannot_pass(self):
        with self.assertRaises(ValueError):
            replace(self.p, ring_window_diameter=self.p.stage.tube_clear_diameter + 1.0).validate()


if __name__ == "__main__":
    unittest.main()

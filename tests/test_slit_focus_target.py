"""Experimental slit focus targets: the shared fixture (paper plane, ring interface, insert, seat bore) and the
paper and ground-glass variants with their retaining rings."""

import unittest
from dataclasses import replace

from build123d import Vector

from schlieren.cad import children_by_label
from schlieren.parts.slit_focus_target import (
    FocusScreenParameters,
    FocusTargetParameters,
    build_focus_screen_assembly,
    build_focus_target,
    build_focus_target_assembly,
    build_gasket,
    build_glass,
    build_glass_retaining_ring,
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

    def test_assembly_has_no_baffle_tube(self):
        self.assertNotIn("SM1 baffle tube", children_by_label(self.assembly))

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
        taper = p.seat_taper_length
        for y in (p.stage.plate_back - 5.0, p.stage.plate_back + 5.0, -taper - 0.5):
            self.assertFalse(self.target.is_inside(Vector(p.bore / 2 - 0.2, y, 0)))
            self.assertTrue(self.target.is_inside(Vector(p.bore / 2 + 0.2, y, 0)))

    def test_bore_tapers_to_a_wide_seat_at_the_rim_face(self):
        p = self.p
        r_seat, taper = p.seat_bore_diameter / 2, p.seat_taper_length
        self.assertGreaterEqual(p.seat_bore_diameter, 2 * p.stage.lit_half_length + 4.0)  # Beam, with margin.
        # Open inside the seat bore at the face, solid just outside it, and 45 degrees in between.
        self.assertFalse(self.target.is_inside(Vector(r_seat - 0.2, -0.05, 0)))
        self.assertTrue(self.target.is_inside(Vector(r_seat + 0.2, -0.05, 0)))
        self.assertFalse(self.target.is_inside(Vector(r_seat + taper / 2 - 0.2, -taper / 2, 0)))
        self.assertTrue(self.target.is_inside(Vector(r_seat + taper / 2 + 0.2, -taper / 2, 0)))
        # A 25 mm glass with 0.2 mm bevels (Ø25.0 flat) seats on at least 2 mm of the rim face.
        self.assertGreaterEqual(25.0 / 2 - r_seat, 2.0)

    def test_validate_rejects_a_seat_bore_that_clips_the_beam(self):
        with self.assertRaises(ValueError):
            replace(self.p, seat_bore_diameter=12.0).validate()
        with self.assertRaises(ValueError):
            replace(self.p, seat_bore_diameter=self.p.bore + 1.0).validate()

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

    def test_window_is_beveled_on_the_mirror_side_only(self):
        p = self.p
        c = p.ring_window_chamfer
        r = p.ring_window_diameter / 2
        top = p.ring_thickness
        # The paper-side land stays a cylinder; the bevel opens 45 degrees to the front face.
        self.assertTrue(self.ring.is_inside(Vector(r + 0.2, top - c - 0.3, 0)))
        self.assertFalse(self.ring.is_inside(Vector(r + c - 0.2, top - 0.1, 0)))
        self.assertTrue(self.ring.is_inside(Vector(r + c + 0.2, top - 0.1, 0)))
        self.assertFalse(self.ring.is_inside(Vector(r + c / 2 - 0.2, top - c / 2, 0)))
        self.assertTrue(self.ring.is_inside(Vector(r + c / 2 + 0.2, top - c / 2, 0)))
        # The screw heads keep a bearing face outside the bevel.
        head_edge = p.screw_radius - p.stage.screw_head_diameter / 2
        self.assertGreater(head_edge, r + c)

    def test_validate_rejects_a_chamfer_that_eats_the_screw_heads(self):
        with self.assertRaises(ValueError):
            replace(self.p, ring_window_chamfer=3.0).validate()
        with self.assertRaises(ValueError):
            replace(self.p, ring_window_chamfer=self.p.ring_thickness).validate()

    def test_outer_edges_are_broken_except_where_the_fixture_and_ring_mate(self):
        p = self.p
        c, r = p.edge_chamfer, p.rim_diameter / 2
        glass_ring = build_glass_retaining_ring(FocusScreenParameters(target=p))
        for part, y_broken, y_mating, direction in (
            (self.target, -p.rim_length, 0.0, 1),
            (self.ring, p.ring_thickness, 0.0, -1),
            (glass_ring, glass_ring.bounding_box().max.Y, 0.0, -1),
        ):
            inside = y_broken + direction * 0.05  # A hair inside the broken face, at its outer edge.
            self.assertFalse(part.is_inside(Vector(r - 0.05, inside, 0)))  # Chamfer removes the corner.
            self.assertTrue(part.is_inside(Vector(r - c - 0.05, inside, 0)))
            self.assertTrue(
                part.is_inside(Vector(r - 0.05, y_mating - direction * 0.05, 0))
            )  # Mating edge sharp.

    def test_validate_rejects_an_edge_chamfer_that_reaches_the_screw_heads(self):
        with self.assertRaises(ValueError):
            replace(self.p, edge_chamfer=1.5).validate()

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

    def test_ring_window_is_the_seat_bore(self):
        p = self.p
        self.assertEqual(p.ring_window_diameter, p.seat_bore_diameter)
        # Ring and rim annuli meet: the ring clamps out to the edge of the opening in the rim face.
        self.assertFalse(
            self.ring.is_inside(Vector(p.seat_bore_diameter / 2 - 0.05, p.ring_thickness / 2, 0))
        )
        self.assertTrue(self.ring.is_inside(Vector(p.seat_bore_diameter / 2 + 0.05, p.ring_thickness / 2, 0)))
        self.assertTrue(self.target.is_inside(Vector(p.seat_bore_diameter / 2 + 0.05, -0.05, 0)))

    def test_validate_rejects_a_window_the_baffle_tube_cannot_pass(self):
        with self.assertRaises(ValueError):
            replace(self.p, seat_bore_diameter=self.p.stage.tube_clear_diameter + 0.6).validate()


class FocusScreenTests(unittest.TestCase):
    @shared
    def assembly(cls):
        return build_focus_screen_assembly(cls.p, include_support=False)

    @classmethod
    def setUpClass(cls):
        cls.p = FocusScreenParameters()
        cls.p.validate()
        cls.ring = build_glass_retaining_ring(cls.p)
        cls.glass = build_glass(cls.p)
        cls.gasket = build_gasket(cls.p)

    def test_solids_are_single_and_valid(self):
        for part in (self.ring, self.glass, self.gasket):
            self.assertEqual(len(part.solids()), 1)
            self.assertTrue(part.is_valid)

    def test_fixture_is_the_paper_targets(self):
        children = children_by_label(self.assembly)
        self.assertAlmostEqual(
            children["Focus target"].volume, build_focus_target(self.p.target).volume, places=6
        )
        self.assertNotIn("Focus screen fixture", children)

    def test_ground_face_is_the_stage_blades_edge_plane_on_the_rim_face(self):
        # The glass lies on the rim face like the paper: its source-facing ground face is the y = 0 seat
        # plane, within 0.02 mm of the stage's inclined blade edges' mid-plane, at any glass thickness.
        edge_plane = self.p.target.stage.seated_blade_y(0, 0)
        for thickness in (self.p.glass_thickness_min, self.p.glass_thickness_max):
            glass = build_glass(self.p, thickness)
            self.assertAlmostEqual(glass.bounding_box().min.Y, 0, places=9)
            self.assertAlmostEqual(glass.bounding_box().min.Y, edge_plane, delta=0.02)
        self.assertAlmostEqual(self.glass.bounding_box().min.Y, 0, places=9)  # The vendor model, nominal.
        self.assertAlmostEqual(build_focus_target(self.p.target).bounding_box().max.Y, 0, places=9)
        self.assertAlmostEqual(self.ring.bounding_box().min.Y, 0, places=9)

    def test_glass_is_the_vendor_model_and_the_parametric_disc_matches_it(self):
        p = self.p
        box = self.glass.bounding_box()
        self.assertAlmostEqual(box.max.Y - box.min.Y, p.glass_thickness_nominal, delta=1e-6)
        self.assertAlmostEqual(box.max.X - box.min.X, p.glass_diameter, delta=1e-6)
        disc = build_glass(p, p.glass_thickness_nominal)  # Same thickness, built here with the bevels.
        self.assertAlmostEqual(disc.volume, self.glass.volume, delta=0.5)
        # The bevel: the flat face is Ø25.0 inside the Ø25.4 edge, at both faces.
        for y in (0.05, p.glass_thickness_nominal - 0.05):
            self.assertFalse(self.glass.is_inside(Vector(p.glass_diameter / 2 - 0.01, y, 0)))
            self.assertTrue(self.glass.is_inside(Vector(p.glass_flat_diameter / 2 - 0.1, y, 0)))

    def test_glass_seats_on_the_rim_outside_the_seat_bore_and_gasket_on_its_flat(self):
        p = self.p
        self.assertGreaterEqual(p.rim_seating_width, p.seating_min)
        gasket = self.gasket.bounding_box()
        self.assertAlmostEqual(gasket.max.X, p.glass_flat_diameter / 2, delta=1e-6)

    def test_assembly_has_no_baffle_tube(self):
        self.assertNotIn("SM1 baffle tube", children_by_label(self.assembly))

    def test_pocket_clears_the_glass_and_lip_overlaps_it(self):
        p = self.p
        mid = p.glass_thickness_nominal
        self.assertFalse(self.ring.is_inside(Vector(p.glass_diameter / 2 + 0.05, mid, 0)))
        self.assertTrue(self.ring.is_inside(Vector(p.pocket_diameter / 2 + 0.2, mid, 0)))
        lip = p.pocket_depth + 0.3
        self.assertTrue(self.ring.is_inside(Vector(p.aperture_diameter / 2 + 0.3, lip, 0)))
        self.assertFalse(self.ring.is_inside(Vector(p.aperture_diameter / 2 - 0.3, lip, 0)))

    def test_window_is_beveled_with_a_land_under_the_bevel(self):
        p = self.p
        r, c, top = p.aperture_diameter / 2, p.window_chamfer, p.ring_thickness
        self.assertTrue(self.ring.is_inside(Vector(r + 0.2, top - c - 0.2, 0)))
        self.assertFalse(self.ring.is_inside(Vector(r + c - 0.2, top - 0.1, 0)))

    def test_ring_screws_reach_the_inserts_with_the_thicker_ring(self):
        p = self.p
        t, s = p.target, p.target.stage
        engagement = p.ring_target.screw_engagement
        self.assertGreaterEqual(engagement, s.insert_installed_length - t.insert_engagement_margin)
        self.assertLessEqual(engagement, s.insert_hole_depth)

    def test_gasket_is_lightly_loaded_across_the_glass_tolerance(self):
        p = self.p
        for thickness in (p.glass_thickness_min, p.glass_thickness_nominal, p.glass_thickness_max):
            self.assertTrue(0.05 <= p.gasket_compression(thickness) <= 0.45)

    def test_glass_stack_does_not_interfere(self):
        children = children_by_label(self.assembly)
        fixture, ring = children["Focus target"], children["Retaining ring"]
        for name in ("Ground glass", "Gasket"):
            self.assertAlmostEqual(overlap_volume(children[name], fixture), 0, places=6)
            self.assertAlmostEqual(overlap_volume(children[name], ring), 0, places=6)
        self.assertAlmostEqual(overlap_volume(children["Ground glass"], children["Gasket"]), 0, places=6)

    def test_validate_rejects_a_thin_wall_a_deep_pocket_and_a_knife_edge(self):
        p = self.p
        with self.assertRaises(ValueError):
            replace(p, pocket_diametral_clearance=3.0).validate()
        with self.assertRaises(ValueError):
            replace(p, gasket_min_gap=6.0).validate()
        with self.assertRaises(ValueError):
            replace(p, window_chamfer=1.4).validate()
        with self.assertRaises(ValueError):
            replace(p, target=replace(p.target, seat_bore_diameter=22.0)).validate()  # No seat for the glass.


if __name__ == "__main__":
    unittest.main()

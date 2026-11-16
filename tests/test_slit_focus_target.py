"""Slit focus target: the fixture (rim plane, ring interface, inserts, seat bore) and the ground-glass screen with
its pocketed retaining ring and gasket."""

import unittest
from dataclasses import replace

from build123d import Vector

from schlieren.cad import children_by_label
from schlieren.parts.slit_focus_target import (
    FocusTargetParameters,
    build_focus_target,
    build_focus_target_assembly,
    build_gasket,
    build_glass,
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
        cls.glass = build_glass(cls.p)
        cls.gasket = build_gasket(cls.p)

    def test_printed_parts_are_single_valid_solids(self):
        for part in (self.target, self.ring, self.glass, self.gasket):
            self.assertEqual(len(part.solids()), 1)
            self.assertTrue(part.is_valid)

    def test_rim_face_is_the_blades_edge_plane_the_stage_head_puts_ahead_of_the_post(self):
        p = self.p
        self.assertAlmostEqual(self.target.bounding_box().max.Y, 0, places=9)
        self.assertAlmostEqual(self.glass.bounding_box().min.Y, 0, places=9)
        # The rim stands off the post axis as the stage head's blade edges do: the blade-seat plane's distance,
        # plus the edges' height above it.
        rim_from_post = SM1RC_M_THICKNESS / 2 + p.stage.ring_gap + p.barrel_length
        self.assertAlmostEqual(
            head_location(p.stage).position.Y + p.stage.seated_blade_y(0, 0), rim_from_post, places=9
        )

    def test_ground_face_is_the_stage_blades_edge_plane(self):
        p = self.p
        self.assertIsInstance(p.stage, SlitStageParameters)  # 2.9 mm blade overhang.
        # The stage's blades lie flat on their folds, so their cutting edges' mid-plane is half the fold's
        # thickness above the seat plane. The glass's ground face is that plane.
        edge_plane = p.stage.seated_blade_y(0, 0)
        self.assertAlmostEqual(edge_plane, p.stage.blade.fold_thickness / 2, places=9)
        self.assertAlmostEqual(p.rim_y, edge_plane, places=9)
        glass = children_by_label(self.assembly)["Ground glass"].bounding_box()
        self.assertAlmostEqual(glass.min.Y - head_location(p.stage).position.Y, edge_plane, places=9)

    def test_assembly_has_no_baffle(self):
        self.assertNotIn("Baffle", children_by_label(self.assembly))

    def test_ring_interface_matches_the_stage_plate(self):
        p = self.p
        s = p.stage
        box = self.target.bounding_box()
        self.assertAlmostEqual(box.min.Y, p.plate_back - s.spigot_length, places=9)
        # Spigot and shoulder diameters are the plate's, so the SM1RC/M seats the same way.
        self.assertTrue(self.target.is_inside(Vector(s.spigot_diameter / 2 - 0.2, p.plate_back - 6.0, 0)))
        self.assertFalse(self.target.is_inside(Vector(s.spigot_diameter / 2 + 0.2, p.plate_back - 6.0, 0)))
        self.assertTrue(
            self.target.is_inside(Vector(s.spigot_shoulder_diameter / 2 - 0.2, p.plate_back - 1.0, 0))
        )
        self.assertFalse(
            self.target.is_inside(Vector(s.spigot_shoulder_diameter / 2 + 0.2, p.plate_back - 1.0, 0))
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
        for y in (p.plate_back - 5.0, p.plate_back + 5.0, -taper - 0.5):
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
        self.assertLessEqual(p.window_diameter, p.stage.spigot_bore)
        self.assertGreater(p.window_diameter, 2 * p.stage.lit_half_length)
        self.assertLess(p.window_diameter, p.bore)
        self.assertFalse(
            self.ring.is_inside(Vector(p.window_diameter / 2 - 0.2, p.pocket_depth + p.land_min / 2, 0))
        )
        self.assertTrue(
            self.ring.is_inside(Vector(p.window_diameter / 2 + 0.2, p.pocket_depth + p.land_min / 2, 0))
        )

    def test_window_is_beveled_on_the_mirror_side_only(self):
        p = self.p
        c = p.window_chamfer
        r = p.window_diameter / 2
        top = p.ring_thickness
        # The land behind the bevel stays a cylinder; the bevel opens 45 degrees to the front face.
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
            replace(self.p, window_chamfer=3.0).validate()
        with self.assertRaises(ValueError):
            replace(self.p, window_chamfer=self.p.ring_thickness).validate()

    def test_outer_edges_are_broken_except_where_the_fixture_and_ring_mate(self):
        p = self.p
        c, r = p.edge_chamfer, p.rim_diameter / 2
        for part, y_broken, y_mating, direction in (
            (self.target, -p.rim_length, 0.0, 1),
            (self.ring, p.ring_thickness, 0.0, -1),
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

    def test_ring_window_is_the_seat_bore(self):
        p = self.p
        self.assertEqual(p.window_diameter, p.seat_bore_diameter)
        # Ring and rim annuli meet: the ring clamps out to the edge of the opening in the rim face.
        self.assertFalse(
            self.ring.is_inside(Vector(p.seat_bore_diameter / 2 - 0.05, p.pocket_depth + p.land_min / 2, 0))
        )
        self.assertTrue(
            self.ring.is_inside(Vector(p.seat_bore_diameter / 2 + 0.05, p.pocket_depth + p.land_min / 2, 0))
        )
        self.assertTrue(self.target.is_inside(Vector(p.seat_bore_diameter / 2 + 0.05, -0.05, 0)))

    def test_fixture_has_no_paper_or_baffle_parts(self):
        children = children_by_label(self.assembly)
        self.assertNotIn("Paper", children)
        self.assertNotIn("Baffle", children)

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

    def test_ground_face_is_the_rim_face_at_any_glass_thickness(self):
        p = self.p
        for thickness in (p.glass_thickness_min, p.glass_thickness_max):
            self.assertAlmostEqual(build_glass(p, thickness).bounding_box().min.Y, 0, places=9)
        self.assertAlmostEqual(self.ring.bounding_box().min.Y, 0, places=9)

    def test_glass_seats_on_the_rim_outside_the_seat_bore_and_gasket_on_its_flat(self):
        p = self.p
        self.assertGreaterEqual(p.rim_seating_width, p.seating_min)
        self.assertAlmostEqual(self.gasket.bounding_box().max.X, p.glass_flat_diameter / 2, delta=1e-6)
        self.assertAlmostEqual(self.gasket.bounding_box().max.Y, p.pocket_depth, delta=1e-6)

    def test_pocket_clears_the_glass_and_lip_overlaps_it(self):
        p = self.p
        mid = p.glass_thickness_nominal
        self.assertFalse(self.ring.is_inside(Vector(p.glass_diameter / 2 + 0.05, mid, 0)))
        self.assertTrue(self.ring.is_inside(Vector(p.pocket_diameter / 2 + 0.2, mid, 0)))
        lip = p.pocket_depth + 0.3
        self.assertTrue(self.ring.is_inside(Vector(p.window_diameter / 2 + 0.3, lip, 0)))
        self.assertFalse(self.ring.is_inside(Vector(p.window_diameter / 2 - 0.3, lip, 0)))

    def test_ring_screws_reach_the_inserts(self):
        p = self.p
        s = p.stage
        self.assertGreaterEqual(p.screw_engagement, s.insert_installed_length - p.insert_engagement_margin)
        self.assertLessEqual(p.screw_engagement, s.insert_hole_depth)

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
            replace(p, seat_bore_diameter=22.0).validate()  # No seat for the glass.


if __name__ == "__main__":
    unittest.main()

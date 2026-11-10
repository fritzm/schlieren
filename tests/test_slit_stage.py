"""Experimental stage-mounted slit head: slit, seat-plane, stage-hole, beam, and ring invariants."""

import unittest
from dataclasses import replace

from build123d import Compound, Pos, Rot, Vector

from schlieren.cad import children_by_label, intersect, leaves, moved, y_cylinder, z_cylinder
from schlieren.parts.baffle import BODY_LABEL, BaffleParameters, build_baffle
from schlieren.parts.rail_shoe import build_rail_shoe
from schlieren.parts.slit_stage import (
    STAGE_BASE_FLANGE,
    STAGE_BASE_HOLE_PITCH,
    STAGE_END_BUMP,
    STAGE_SIZE,
    STAGE_TABLE_HOLE_PITCH,
    STAGE_THICKNESS,
    SlitStageParameters,
    _toe_pad,
    beam_envelope,
    blade,
    build_pedestal,
    build_slit_stage_assembly,
    build_stage,
    build_stage_plate,
    build_toe_bar,
    head_location,
    stage_location,
)
from schlieren.testing import bounded_distance, overlap_volume, shared, slow
from schlieren.vendor_cad import (
    SM1L10_OUTER_DIAMETER,
    SM1RC_M_THICKNESS,
    thorlabs_sm1rc_m,
)

ROTATION_SWEEP = range(-130, 131, 10)
TR50_STUD_MAX = 5.2  # TR50/M drawing: setscrew stud 4.6-5.2 mm above the post top.


class SlitStageTests(unittest.TestCase):
    @shared
    def shoe(cls):
        return build_rail_shoe()

    @shared
    def baffle_body(cls):
        return children_by_label(children_by_label(cls.assembly)["Baffle"])[BODY_LABEL]

    @shared
    def assembly(cls):
        return build_slit_stage_assembly(cls.p, include_support=False)

    @classmethod
    def setUpClass(cls):
        cls.p = SlitStageParameters()
        cls.p.validate()
        cls.plate = build_stage_plate(cls.p)
        cls.pedestal = build_pedestal(cls.p)
        cls.bar = build_toe_bar(cls.p)
        cls.stage = moved(Compound(list(build_stage())), stage_location(cls.p))

    def test_printed_parts_are_single_valid_solids(self):
        for part in (self.plate, self.pedestal, self.bar):
            self.assertEqual(len(part.solids()), 1)
            self.assertTrue(part.is_valid)

    def test_blades_set_the_slit_and_share_the_seat_plane(self):
        p = self.p
        upper, lower = blade(p, 1).bounding_box(), blade(p, -1).bounding_box()
        self.assertAlmostEqual(upper.min.Z - lower.max.Z, p.slit_width, delta=0.001)  # Edge tips.
        self.assertAlmostEqual(upper.min.Z, p.slit_width / 2, delta=0.001)
        # Each blade lies on its fold, the fold's outer layer in the seat plane, and both alike: the cutting
        # edges are parallel and at one height, collinear were the slit closed.
        self.assertAlmostEqual(upper.min.Y, lower.min.Y, places=9)
        self.assertAlmostEqual(upper.min.Y, 0, places=9)
        self.assertAlmostEqual(upper.max.Y, p.blade.fold_thickness, places=9)
        # The edge's mid-plane stands half the fold's thickness above the seat plane.
        self.assertAlmostEqual(p.seated_blade_y(0, 0), p.blade.fold_thickness / 2, places=9)
        # The stage's table top and the pedestal top are both the seat plane.
        self.assertAlmostEqual(stage_location(p).position.Y + STAGE_THICKNESS, 0, places=9)
        self.assertAlmostEqual(self.pedestal.bounding_box().max.Y, 0, places=9)
        self.assertAlmostEqual(self.pedestal.bounding_box().min.Y, p.plate_front, places=9)

    def test_table_and_pedestal_edges_set_the_blade_overhang(self):
        p = self.p
        self.assertAlmostEqual(self.stage.bounding_box().min.Z, p.table_edge - STAGE_END_BUMP, places=6)
        self.assertAlmostEqual(self.pedestal.bounding_box().max.Z, -p.table_edge, places=6)
        self.assertAlmostEqual(p.table_edge - p.slit_width / 2, p.blade_overhang, places=9)
        self.assertGreater(p.blade_length / 2, p.spigot_bore / 2 + 3)

    def test_micrometer_is_up_at_rotation_zero(self):
        p = self.p
        box = self.stage.bounding_box()
        self.assertAlmostEqual(box.max.Z, p.micrometer_reach, places=6)
        self.assertGreater(box.max.Z, 2 * p.table_edge + STAGE_SIZE)

    def test_toe_screws_sit_in_the_stage_hole_grid(self):
        """The toe bars' screw axes land in the table's second row of tapped holes."""
        p = self.p
        holes = {
            (round(c.X, 6), round(c.Z, 6))
            for c in (
                moved(Pos(hx, 0, hz) * y_cylinder(1.0, 0, 0, 0, 1), stage_location(p)).center()
                for hx in (-STAGE_TABLE_HOLE_PITCH, 0, STAGE_TABLE_HOLE_PITCH)
                for hz in (-STAGE_TABLE_HOLE_PITCH, 0, STAGE_TABLE_HOLE_PITCH)
            )
        }
        for x in p.toe_x:
            self.assertIn((round(x, 6), round(p.toe_z, 6)), holes)
            self.assertFalse(self.stage.is_inside(Vector(x, -3.0, p.toe_z)))  # In the hole.
            self.assertTrue(self.stage.is_inside(Vector(x + 2.0, -3.0, p.toe_z)))  # In the table.
        # The second row, as seen from the slit: one hole row (the table's mid-row) behind the blade's rear edge.
        self.assertAlmostEqual(p.toe_z - p.table_edge, STAGE_SIZE / 2, places=6)
        self.assertGreater(p.toe_row_distance, p.blade_width - p.blade_overhang)

    def test_blades_lie_flat_on_their_folds(self):
        p = self.p
        standoff = p.blade.fold_standoff
        z_fold = p.fold_front_z
        for sign, support in ((1, self.stage), (-1, self.pedestal)):
            b = blade(p, sign)
            self.assertAlmostEqual(overlap_volume(b, support), 0, places=6)
            self.assertLess(bounded_distance(b, support, 0.05), 1e-3)  # The fold touches the seat.
            # The fold's outer layer is on the seat plane, over its whole width and no lower.
            self.assertTrue(b.is_inside(Vector(0, 0.01, sign * (z_fold + 3.0))))
            self.assertFalse(b.is_inside(Vector(0, -0.001, sign * (z_fold + 3.0))))
            # The plate in front of the fold is parallel to the seat, standoff above it, clear of the seat edge.
            for z in (p.slit_width / 2 + 3.0, p.slit_width / 2 + 8.0):
                self.assertFalse(b.is_inside(Vector(8.0, standoff - 0.05, sign * z)))  # Off the central slot.
                self.assertTrue(b.is_inside(Vector(8.0, standoff + 0.05, sign * z)))
        # The seat reaches under the whole fold.
        self.assertLess(p.table_edge, z_fold)

    def test_toe_presses_the_fold_between_the_slit_and_the_field_lens_tube(self):
        p = self.p
        near, far = p.toe_pad_z
        self.assertGreater(near, p.fold_front_z)  # On the fold,
        self.assertLess(far, p.blade_rear_z)  # not past its rear edge.
        # The finger's face stands clear of the field-lens tube's Ø30.5 mm body, concentric with the axis.
        self.assertGreaterEqual(p.toe_finger_face_z, SM1L10_OUTER_DIAMETER / 2 + 0.5)
        for sign, turn in ((1, 0), (-1, 180)):
            placed = Pos(0, 0, sign * p.toe_z) * Rot(Y=turn)
            bar = moved(self.bar, placed)
            pad = moved(_toe_pad(p), placed)
            b = blade(p, sign)
            box = bar.bounding_box()
            # The bar spans the blade; its body stops behind the blade's rear edge.
            self.assertLessEqual(box.min.X, -p.blade_length / 2 + 0.1)
            self.assertGreaterEqual(box.max.X, p.blade_length / 2 - 0.1)
            self.assertGreater(p.toe_z - p.toe_body_setback, p.blade_rear_z)
            # The finger clears the blade by the pad's compressed thickness; only the EPDM pad touches it.
            self.assertAlmostEqual(overlap_volume(bar, b), 0, places=6)
            self.assertAlmostEqual(
                bounded_distance(bar, b, 1.0), p.epdm_thickness - p.toe_pad_squeeze, delta=1e-6
            )
            self.assertGreater(overlap_volume(pad, b), 0)  # The pad's compression.
            self.assertAlmostEqual(
                overlap_volume(pad, b) / (pad.bounding_box().size.X * p.toe_pad_width),
                p.toe_pad_squeeze,
                delta=0.05,  # The fold's top is flat under the pad: no slot or notch crosses it.
            )
            # The pad's footprint is wholly on the fold's top face.
            pad_box = pad.bounding_box()
            lo, hi = sorted((abs(pad_box.min.Z), abs(pad_box.max.Z)))
            self.assertGreater(lo, p.fold_front_z)
            self.assertLess(hi, p.blade_rear_z)
            for x in p.toe_x:  # Screw holes at the stage's hole grid.
                self.assertFalse(bar.is_inside(Vector(x, p.toe_thickness / 2, sign * p.toe_z)))
                self.assertTrue(bar.is_inside(Vector(x + 2.5, p.toe_thickness / 2, sign * p.toe_z)))

    def test_pedestal_takes_heat_set_inserts_for_toe_and_mounting_screws(self):
        p = self.p
        depth = p.insert_flange_recess_depth + p.insert_hole_depth
        for x in p.toe_x:  # Toe screws, from the seat plane.
            z = -p.toe_z
            self.assertFalse(self.pedestal.is_inside(Vector(x, -depth + 0.2, z)))
            self.assertFalse(self.pedestal.is_inside(Vector(x + p.insert_hole_diameter / 2 - 0.2, -3.0, z)))
            self.assertTrue(self.pedestal.is_inside(Vector(x + p.insert_hole_diameter / 2 + 0.3, -3.0, z)))
            self.assertTrue(self.pedestal.is_inside(Vector(x, -depth - 0.3, z)))  # Solid under the hole.
        for x, z in p.pedestal_screw_xz():  # Mounting screws, from the plate-side face.
            bottom = p.plate_front
            self.assertFalse(self.pedestal.is_inside(Vector(x, bottom + depth - 0.2, z)))
            self.assertFalse(self.pedestal.is_inside(Vector(x, bottom + depth + 1.0, z)))  # Clearance hole.
            self.assertTrue(self.pedestal.is_inside(Vector(x + 2.5, bottom + depth - 0.2, z)))
        # The toe screws run through their inserts without bottoming.
        self.assertLessEqual(p.screw_length - p.toe_thickness, p.insert_hole_depth)

    def test_plate_holes_match_stage_and_pedestal(self):
        p = self.p
        stage_holes = p.stage_screw_xz()
        xs = sorted({x for x, _ in stage_holes})
        zs = sorted({z for _, z in stage_holes})
        self.assertEqual(len(stage_holes), 4)
        self.assertAlmostEqual(xs[1] - xs[0], STAGE_BASE_HOLE_PITCH)
        self.assertAlmostEqual(zs[1] - zs[0], STAGE_BASE_HOLE_PITCH)
        self.assertAlmostEqual(sum(xs) / 2, 0)
        self.assertAlmostEqual(sum(zs) / 2, p.stage_center_z)
        for x, z in stage_holes + p.pedestal_screw_xz():
            hole = y_cylinder(p.screw_clearance - 0.1, x, z, p.plate_back, p.plate_front)
            self.assertAlmostEqual(overlap_volume(self.plate, hole), 0, places=6, msg=f"({x}, {z})")
        # Pedestal screws stay under the pedestal; the stage screws stay under the stage.
        for _, z in p.pedestal_screw_xz():
            self.assertLess(z, -p.table_edge)
        for _, z in stage_holes:
            self.assertGreater(z, p.table_edge)

    def test_spigot_grips_the_whole_ring(self):
        p = self.p
        plate = moved(self.plate, head_location(p))
        ring_face = SM1RC_M_THICKNESS / 2
        # The spigot protrudes past the ring's far face by the baffle's extension.
        self.assertAlmostEqual(plate.bounding_box().min.Y, -ring_face - p.baffle.spigot_extension, places=6)
        ring = moved(thorlabs_sm1rc_m(), Pos(0, -SM1RC_M_THICKNESS / 2, p.optical_height))
        self.assertAlmostEqual(plate.distance_to(ring), 0, places=3)  # Seated on the shoulder.
        self.assertAlmostEqual(overlap_volume(plate, ring), 0, places=3)

    def test_baffle_butts_the_ring_and_clamps_the_extended_spigot(self):
        """The baffle's clamp front face is the ring's source face; its bore wraps the protruding spigot."""
        p = self.p
        ring_face = SM1RC_M_THICKNESS / 2
        baffle = children_by_label(children_by_label(self.assembly)["Baffle"])[BODY_LABEL]  # Already placed.
        box = baffle.bounding_box()
        self.assertAlmostEqual(box.max.Y, -ring_face, places=6)
        self.assertAlmostEqual(box.min.Y, -ring_face - p.baffle.length, places=6)
        self.assertAlmostEqual(box.min.Z, p.optical_height - p.baffle.clamp_diameter / 2, places=6)
        self.assertAlmostEqual(box.max.Z, p.optical_height + p.baffle.ear_top_z, places=6)  # Ears up.
        plate = moved(self.plate, head_location(p))
        self.assertAlmostEqual(overlap_volume(plate, baffle), 0, places=6)
        # The bore clears the spigot by half the diametral clearance, radially; nothing is closer.
        self.assertAlmostEqual(
            bounded_distance(plate, baffle, 1.0), p.baffle.clamp_bore_diametral_clearance / 2, delta=1e-3
        )
        self.assertAlmostEqual(plate.bounding_box().min.Y, -ring_face - p.baffle.spigot_extension, places=6)
        self.assertAlmostEqual(
            plate.bounding_box().min.Y - baffle.bounding_box().max.Y, -p.baffle.spigot_extension, places=6
        )

    def test_baffle_turns_with_the_head_and_needs_no_post_of_its_own(self):
        full = build_slit_stage_assembly(self.p)
        posts = [leaf for leaf in leaves(full) if leaf.label == "TR50 M post"]
        self.assertEqual(len(posts), 1)  # The head's only.
        rotated = build_slit_stage_assembly(self.p, rotation=90.0, include_support=False)
        spun = children_by_label(children_by_label(rotated)["Baffle"])[BODY_LABEL].bounding_box()
        straight = children_by_label(children_by_label(self.assembly)["Baffle"])[BODY_LABEL].bounding_box()
        self.assertAlmostEqual(spun.size.Y, straight.size.Y, places=6)
        self.assertAlmostEqual(spun.min.Y, straight.min.Y, places=6)
        self.assertGreater(spun.size.X, straight.size.X)  # The ears went sideways.

    def test_spigot_bearing_surface_is_a_full_tube(self):
        # The stage-screw nut pockets reach inside the spigot's radius; the spigot, restored past the
        # shoulder's back face, roofs them rather than being notched, so the ring grips a complete cylinder.
        p = self.p
        shoulder_back = p.plate_back - p.ring_gap
        spigot_end = p.spigot_end_y
        tube = y_cylinder(p.spigot_diameter, 0, 0, spigot_end, shoulder_back) - y_cylinder(
            p.spigot_bore, 0, 0, spigot_end - 1, shoulder_back + 1
        )
        self.assertAlmostEqual(intersect(self.plate, tube).volume, tube.volume, places=3)

    def test_baffle_bore_passes_the_beam_and_the_spigot_bore(self):
        p = self.p
        self.assertGreaterEqual(p.baffle.net_bore, p.spigot_bore)
        self.assertGreaterEqual(p.baffle.net_bore, 2 * p.lit_half_length + 4.0)
        ring_face = SM1RC_M_THICKNESS / 2
        beam = y_cylinder(
            2 * (p.lit_half_length + 1.0), 0, p.optical_height, -ring_face - p.baffle.length, -ring_face
        )
        self.assertAlmostEqual(overlap_volume(beam, self.baffle_body), 0, places=6)

    def test_beam_clears_stage_pedestal_and_plate(self):
        p = self.p
        beam = beam_envelope(p)
        for name, part in (("stage", self.stage), ("pedestal", self.pedestal), ("plate", self.plate)):
            self.assertAlmostEqual(overlap_volume(beam, part), 0, places=6, msg=name)
        for part in (self.stage, self.pedestal):
            self.assertGreaterEqual(bounded_distance(beam, part, p.beam_margin), p.beam_margin - 1e-6)
        self.assertGreater(p.beam_clearance, p.beam_margin)

    def test_toe_and_mounting_screws_engage_without_bottoming(self):
        p = self.p
        self.assertGreater(p.screw_length - p.toe_thickness, 4.0)  # At least ~8 threads in the table.

    def test_stage_screws_are_the_shorter_m3_and_reach_the_nuts(self):
        p = self.p
        self.assertEqual(p.stage_screw_length, 10.0)
        tip = p.plate_front + STAGE_BASE_FLANGE - p.stage_screw_length
        self.assertLessEqual(tip, p.plate_back)  # Through the plate to the nuts.
        self.assertLess(p.plate_back - tip, p.ring_gap)  # Short of the ring face.
        screws = [
            c for label, c in children_by_label(self.assembly).items() if label.startswith("Stage screw")
        ]
        self.assertEqual(len(screws), 4)
        for screw in screws:
            self.assertAlmostEqual(screw.bounding_box().min.Y, head_location(p).position.Y + tip, delta=0.05)

    def test_validation_rejects_bad_layouts(self):
        for change in (
            {"cone_half_angle": 10.0},  # Cone reaches the stage edge.
            {"baffle": replace(BaffleParameters(), spigot_bore=20.0)},  # Baffle for a different spigot.
            {"baffle": replace(BaffleParameters(), vane_depth=9.0)},  # Vanes narrow the bore past the beam.
            {"toe_thickness": 4.0},  # Screw would bottom in the tapped hole.
            {"toe_pad_width": 9.0},  # Pad runs off the fold's rear edge.
            {"toe_finger_tube_clearance": 0.0},  # Fingers touch the field-lens tube.
            {"toe_finger_tube_clearance": 4.0},  # Pad would run off the fold.
            {"toe_end_margin": 1.0},  # Bar shorter than the blade.
            {"toe_pad_squeeze": 0.0},  # No clamping.
            {"stage_screw_length": 5.0},  # Stage screws would not reach the nuts.
            {"screw_length": 14.0},  # Toe screws would bottom in the inserts.
            {"toe_body_setback": 4.0},  # Body rides on the blade.
        ):
            with self.assertRaises(ValueError, msg=str(change)):
                replace(self.p, **change).validate()

    @slow
    def test_rotation_sweep_clears_post_ring_and_shoe(self):
        """Plate, stage (with its micrometer), pedestal, and baffle clear the post and shoe through the working range."""
        p = self.p
        post_top = p.datum_thickness + p.post_length
        body = z_cylinder(p.post_diameter, 0, 0, p.datum_thickness, post_top)
        stud = z_cylinder(4.0, 0, 0, post_top, post_top + TR50_STUD_MAX)
        for rotation in ROTATION_SWEEP:
            loc = head_location(p, rotation)
            moving = [
                moved(self.plate, loc),
                moved(self.stage, loc),
                moved(self.pedestal, loc),
                moved(build_baffle(p.baffle), loc * Pos(0, p.ring_face_y, 0)),  # With its ears.
            ]
            for name, fixed in (("post", body), ("shoe", self.shoe)):
                clearance = min(bounded_distance(part, fixed, p.post_clearance) for part in moving)
                self.assertGreaterEqual(clearance, p.post_clearance, msg=f"{name} at rotation {rotation}")
            self.assertGreater(min(bounded_distance(part, stud, 1.0) for part in moving), 1.0)


if __name__ == "__main__":
    unittest.main()

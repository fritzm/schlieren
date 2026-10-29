"""Experimental stage-mounted slit head: slit, seat-plane, stage-hole, beam, and ring invariants."""

import unittest
from dataclasses import replace

from build123d import Compound, Pos, Rot, Vector

from schlieren.cad import children_by_label, moved, y_cylinder, z_cylinder
from schlieren.parts.rail_shoe import build_rail_shoe
from schlieren.parts.slit_stage import (
    STAGE_BASE_HOLE_PITCH,
    STAGE_END_BUMP,
    STAGE_SIZE,
    STAGE_TABLE_HOLE_PITCH,
    STAGE_THICKNESS,
    SlitStageParameters,
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
    SM1L15_SHOULDER_TO_OPEN_END,
    SM1L15_THREAD_LENGTH,
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
        self.assertAlmostEqual(upper.min.Z - lower.max.Z, p.slit_width, places=9)
        self.assertAlmostEqual(upper.min.Z, p.slit_width / 2, places=9)
        for box in (upper, lower):
            self.assertAlmostEqual(box.min.Y, 0, places=9)
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

    def test_toe_bars_clamp_the_spine_clear_of_the_blade(self):
        p = self.p
        spine_far = p.slit_width / 2 + p.blade_width  # Distance from the slit center; the blade's rear edge.
        for sign, turn in ((1, 0), (-1, 180)):
            bar = moved(self.bar, Pos(0, 0, sign * p.toe_z) * Rot(Y=turn))
            box = bar.bounding_box()
            finger_tip = min(abs(box.min.Z), abs(box.max.Z))  # Nearest the slit.
            # The bar spans the blade; its finger reaches over the whole spine and its body edge stops behind
            # the blade's rear edge.
            self.assertLessEqual(box.min.X, -p.blade_length / 2 + 0.1)
            self.assertGreaterEqual(box.max.X, p.blade_length / 2 - 0.1)
            self.assertLess(finger_tip, spine_far - p.spine_width)
            self.assertGreater(p.toe_z - p.toe_body_setback, spine_far)
            self.assertAlmostEqual(overlap_volume(bar, blade(p, sign)), 0, places=6)
            self.assertGreater(bounded_distance(bar, blade(p, sign), 1.0), 0.4)
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

    def test_spigot_shares_the_ring_with_the_baffle_tube(self):
        p = self.p
        plate = moved(self.plate, head_location(p))
        ring_face = SM1RC_M_THICKNESS / 2
        self.assertAlmostEqual(plate.bounding_box().min.Y, ring_face - p.ring_grip, places=6)
        ring = moved(thorlabs_sm1rc_m(), Pos(0, -SM1RC_M_THICKNESS / 2, p.optical_height))
        self.assertAlmostEqual(plate.distance_to(ring), 0, places=3)  # Seated on the shoulder.
        self.assertAlmostEqual(overlap_volume(plate, ring), 0, places=3)
        tube = children_by_label(self.assembly)["SM1 baffle tube"]  # Already placed.
        # The tube enters from the other side by the same grip, leaving the gap between it and the spigot.
        self.assertAlmostEqual(tube.bounding_box().max.Y, -ring_face + p.ring_grip, places=3)
        self.assertAlmostEqual(plate.bounding_box().min.Y - tube.bounding_box().max.Y, p.tube_gap, places=3)
        self.assertAlmostEqual(p.tube_diameter, p.spigot_diameter)
        self.assertAlmostEqual(overlap_volume(tube, plate), 0, places=6)

    def test_baffle_tubes_are_threaded_together(self):
        """The source-side tube's thread runs into the ring-side tube's open end, shoulder to open end."""
        tube = children_by_label(self.assembly)["SM1 baffle tube"]
        near, far = (
            children_by_label(tube)[label] for label in ("SM1L15 (ring side)", "SM1L15 (source side)")
        )
        length = SM1L15_SHOULDER_TO_OPEN_END + SM1L15_THREAD_LENGTH
        self.assertAlmostEqual(tube.bounding_box().size.Y, 2 * length - SM1L15_THREAD_LENGTH, places=3)
        # The far tube's open end is at the near tube's shoulder; its thread is inside the near tube.
        self.assertAlmostEqual(
            far.bounding_box().max.Y, near.bounding_box().min.Y + SM1L15_THREAD_LENGTH, places=3
        )

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

    def test_validation_rejects_bad_layouts(self):
        for change in (
            {"cone_half_angle": 10.0},  # Cone reaches the stage edge.
            {"ring_grip": 5.0},  # Spigot and tube meet inside the ring.
            {"toe_thickness": 4.0},  # Screw would bottom in the tapped hole.
            {"toe_finger_length": 1.0},  # Finger misses the spine.
            {"toe_end_margin": 1.0},  # Bar shorter than the blade.
            {"toe_pad_squeeze": 0.0},  # No clamping.
            {"screw_length": 14.0},  # Toe screws would bottom in the inserts.
            {"toe_body_setback": 4.0},  # Body rides on the blade.
        ):
            with self.assertRaises(ValueError, msg=str(change)):
                replace(self.p, **change).validate()

    @slow
    def test_rotation_sweep_clears_post_ring_and_shoe(self):
        """Plate, stage (with its micrometer), and pedestal clear the post and shoe through the working range."""
        p = self.p
        post_top = p.datum_thickness + p.post_length
        body = z_cylinder(p.post_diameter, 0, 0, p.datum_thickness, post_top)
        stud = z_cylinder(4.0, 0, 0, post_top, post_top + TR50_STUD_MAX)
        for rotation in ROTATION_SWEEP:
            loc = head_location(p, rotation)
            moving = [moved(self.plate, loc), moved(self.stage, loc), moved(self.pedestal, loc)]
            for name, fixed in (("post", body), ("shoe", self.shoe)):
                clearance = min(bounded_distance(part, fixed, p.post_clearance) for part in moving)
                self.assertGreaterEqual(clearance, p.post_clearance, msg=f"{name} at rotation {rotation}")
            self.assertGreater(min(bounded_distance(part, stud, 1.0) for part in moving), 1.0)


if __name__ == "__main__":
    unittest.main()

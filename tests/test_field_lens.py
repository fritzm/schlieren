"""Field lens station: lens seating and placement, clearances to the slit head, the beam through the tube, and
the optics that set the lens (design §§6.3, 7.9)."""

import unittest
from dataclasses import replace

from build123d import GeomType, Pos, Rot

from schlieren.cad import children_by_label, fused, leaves, moved, y_cylinder, z_cylinder
from schlieren.parts.field_lens import (
    FIELD_LENS_HARDWARE_LABEL,
    LA1433_A_EDGE_THICKNESS,
    SM1D12_MAX_DIAMETER,
    FieldLensParameters,
    build_field_lens_head_assembly,
    build_field_lens_station,
)
from schlieren.parts.light_source import LightSourceParameters
from schlieren.parts.rail_shoe import build_rail_shoe
from schlieren.parts.slit_stage import blade, build_toe_bar, head_location
from schlieren.standards import POST_DIAMETER
from schlieren.testing import bounded_distance, shared, slow
from schlieren.vendor_cad import (
    SM1L10_LENGTH,
    SM1L10_LIP_DIAMETER,
    SM1L10_OUTER_DIAMETER,
    SM1L10_THREAD_DEPTH,
    SM1L10_THREAD_DIAMETER,
    SM1L10_THREAD_LENGTH,
    SM1RC_M_THICKNESS,
    SM1RR_CLEAR_DIAMETER,
    thorlabs_sm1rc_m,
)

ROTATION_SWEEP = range(-130, 131, 10)
N_BK7_INDEX = 1.5168  # At 587.6 nm.


class FieldLensTests(unittest.TestCase):
    @shared
    def station(cls):
        return build_field_lens_station(cls.p)

    @classmethod
    def setUpClass(cls):
        cls.p = FieldLensParameters()
        cls.p.validate()

    def child(self, label):
        return children_by_label(self.station)[label]

    def test_lens_matches_the_catalog(self):
        p = self.p
        self.assertAlmostEqual(p.lens_edge_thickness, LA1433_A_EDGE_THICKNESS, delta=0.1)
        # Lensmaker's: f = R / (n - 1) for a plano-convex lens, the catalog's +-1 %.
        self.assertAlmostEqual(p.lens_radius / (N_BK7_INDEX - 1), p.lens_focal_length, delta=0.01 * 149.5)
        # The object-side principal plane lies CT / n inside the plano face, the catalog's f - back focal length.
        h_object, h_image = p.principal_planes
        self.assertAlmostEqual(h_object, p.lens_center_thickness / N_BK7_INDEX, delta=0.1)
        self.assertAlmostEqual(h_image, p.lens_center_thickness)

    def test_lens_stands_on_the_tube_lip_with_its_convex_face_toward_the_mirror(self):
        p = self.p
        box = self.child("Field lens LA1433-A").bounding_box()
        self.assertAlmostEqual(box.min.Y, p.lens_plano_y, places=6)  # Plano face on the lip.
        self.assertAlmostEqual(box.max.Y, p.lens_plano_y + p.lens_center_thickness, places=6)
        self.assertAlmostEqual(box.center().X, 0, places=6)
        self.assertAlmostEqual(box.center().Z, p.stage.optical_height, places=6)
        # The tube's lip is the vendor model's internal shoulder, SM1L10_THREAD_DEPTH from the open end.
        tube = self.child("Field lens tube SM1L10")
        lips = {
            round(face.center().Y, 2)
            for face in tube.faces().filter_by(GeomType.PLANE)
            if abs(face.normal_at().Y) > 0.99 and face.area > 50
        }
        self.assertIn(round(p.lens_plano_y, 2), lips)
        self.assertAlmostEqual(tube.bounding_box().max.Y - p.lens_plano_y, SM1L10_THREAD_DEPTH, delta=0.03)

    def test_retaining_ring_holds_the_convex_face_inside_the_thread(self):
        p = self.p
        ring = self.child("Field lens retaining ring SM1RR").bounding_box()
        self.assertAlmostEqual(ring.min.Y, p.retaining_ring_y, delta=0.01)
        self.assertGreater(p.retaining_ring_y, p.lens_plano_y)  # On the convex side.
        self.assertLess(p.retaining_ring_y, p.lens_plano_y + p.lens_center_thickness)  # Bearing on the face.
        self.assertLessEqual(ring.max.Y, p.tube_open_end_y)

    def test_tube_stands_between_the_toe_fingers_just_over_the_folds(self):
        p, s = self.p, self.p.stage
        tube = self.child("Field lens tube SM1L10").bounding_box()
        self.assertAlmostEqual(tube.min.Y, p.tube_end_y, delta=0.01)
        self.assertAlmostEqual(tube.size.Y, SM1L10_LENGTH, delta=0.03)
        # The thread end is over the tops of the blades' folds, the highest part of the blades.
        self.assertAlmostEqual(p.tube_end_y - s.blade.fold_thickness, p.fold_clearance)
        self.assertAlmostEqual(p.tube_shoulder_y - p.tube_end_y, SM1L10_THREAD_LENGTH)
        # The toe fingers stop short of the tube's body, which is concentric with the head's axis.
        self.assertGreaterEqual(
            s.toe_finger_face_z - SM1L10_OUTER_DIAMETER / 2, p.finger_wall_clearance - 1e-9
        )
        # The clamp ring and post stand clear of the toe bars and their screw heads.
        self.assertGreaterEqual(p.clamp_ring_y, s.toe_thickness + s.screw_head_height + s.post_clearance)
        self.assertGreaterEqual(
            p.post_y - POST_DIAMETER / 2, s.toe_thickness + s.screw_head_height + s.post_clearance
        )

    def test_clamp_ring_stands_on_the_tubes_full_diameter_section(self):
        p = self.p
        stack = children_by_label(self.child(FIELD_LENS_HARDWARE_LABEL))
        placed = stack["SM1RC M ring"].bounding_box()
        seat = moved(thorlabs_sm1rc_m(), Pos(0, p.clamp_ring_y, p.stage.optical_height)).bounding_box()
        self.assertAlmostEqual(placed.min.Y, seat.min.Y, delta=0.01)
        self.assertAlmostEqual(placed.size.Y, SM1RC_M_THICKNESS, delta=0.01)
        # Past the thread's shoulder and short of the open end: wholly on the Ø30.5 section.
        self.assertGreaterEqual(placed.min.Y, p.tube_shoulder_y)
        self.assertLessEqual(placed.max.Y, p.tube_open_end_y)
        # The post's axis is the clamp ring's center.
        self.assertAlmostEqual(p.post_y, p.clamp_ring_y + SM1RC_M_THICKNESS / 2)

    def test_post_stack_is_the_common_one(self):
        labels = set(children_by_label(self.child(FIELD_LENS_HARDWARE_LABEL)))
        self.assertTrue({"SM1RC M ring", "TR50 M post", "Rail shoe"} <= labels)

    def test_beam_passes_the_lip_bore_and_the_retaining_ring(self):
        p = self.p
        self.assertGreater(SM1L10_LIP_DIAMETER / 2, p.beam_half_length(p.lens_plano_y) + p.beam_margin)
        self.assertGreater(SM1RR_CLEAR_DIAMETER / 2, p.beam_half_length(p.tube_open_end_y) + p.beam_margin)

    def test_optics_rest_on_the_light_source_geometry(self):
        p = self.p
        # The iris sits about 150 mm behind the slit (§6.3); the condenser model puts the lens's convex vertex
        # a few millimeters farther.
        self.assertAlmostEqual(p.iris_to_slit, LightSourceParameters().lens_to_slit, delta=5.0)

    def test_lens_centers_every_cone_on_the_mirror(self):
        p = self.p
        # Without it the lit end's cone lands more than the mirror's radius off center; with it, a few millimeters.
        self.assertGreater(p.unlensed_shift, p.mirror_half_aperture)
        self.assertLess(abs(p.chief_ray_shift()), 3.0)
        self.assertLess(abs(p.chief_ray_shift(3.0)), abs(p.chief_ray_shift()))
        # The stock focal length is within a few percent of the one that images the iris onto the mirror.
        self.assertAlmostEqual(p.lens_focal_length, p.ideal_focal_length, delta=0.03 * p.ideal_focal_length)

    def test_lens_narrows_each_cone_slightly_and_the_iris_makes_up_for_it(self):
        p = self.p
        h_object, _ = p.principal_planes
        # The cone's footprint shrinks by about the lens's distance from the slit over its focal length.
        self.assertAlmostEqual(
            1 - p.cone_scale, (p.lens_plano_y + h_object) / p.lens_focal_length, delta=0.01
        )
        self.assertLess(p.fill_iris_diameter, SM1D12_MAX_DIAMETER)  # The iris opens far enough.
        self.assertLess(p.fill_iris_diameter, 10.5)  # Within the iris setting the condenser was sized for.

    def test_axial_position_is_not_critical(self):
        """The tube slides in its ring: a couple of millimeters either way moves the lit end's cone little."""
        p = self.p
        for shift in (-2.0, 2.0):
            moved_lens = replace(p, fold_clearance=p.fold_clearance + shift)
            self.assertAlmostEqual(moved_lens.chief_ray_shift(), p.chief_ray_shift(), delta=2.0)

    def test_validation_rejects_bad_layouts(self):
        for change in (
            {"lens_radius": 70.0},  # Edge thickness off the catalog.
            {"fold_clearance": 0.0},  # Tube on the blades' folds.
            {"ring_shoulder_margin": 30.0},  # Clamp ring over the open end.
            {"ring_shoulder_margin": 4.5},  # Post within the post clearance of the toe screw heads.
            {"ring_shoulder_margin": -0.5},  # Clamp ring on the thread.
            {"finger_wall_clearance": 3.0},  # The toe fingers do not clear the tube's body by that much.
            {"beam_margin": 8.0},  # The beam cannot pass the bores.
        ):
            with self.assertRaises(ValueError, msg=str(change)):
                replace(self.p, **change).validate()

    def test_station_is_one_labeled_group(self):
        labels = set(children_by_label(self.station))
        self.assertEqual(
            labels,
            {
                "Field lens LA1433-A",
                "Field lens tube SM1L10",
                "Field lens retaining ring SM1RR",
                FIELD_LENS_HARDWARE_LABEL,
            },
        )

    def test_head_assembly_adds_the_station_to_the_slit_head(self):
        head = build_field_lens_head_assembly(self.p)
        labels = set(children_by_label(head))
        self.assertIn("Field lens station", labels)
        self.assertIn("Baffle", labels)
        # The station is placed with the slit head's blade-seat plane at its origin.
        glass = [leaf for leaf in leaves(head) if leaf.label == "Field lens LA1433-A"]
        self.assertEqual(len(glass), 1)
        self.assertAlmostEqual(
            glass[0].bounding_box().min.Y - head_location(self.p.stage).position.Y,
            self.p.lens_plano_y,
            delta=0.01,
        )

    @slow
    def test_slit_head_turns_clear_of_the_lens_post_and_tube(self):
        """The toe bars, their screw heads, and the blades, the parts of the head ahead of the blade-seat plane,
        clear the post, ring, shoe, and tube through the head's rotation range."""
        p, s = self.p, self.p.stage
        bar = build_toe_bar(s)
        top = s.toe_thickness + s.screw_head_height
        heads = [
            y_cylinder(s.screw_head_diameter, x, side * s.toe_z, s.toe_thickness, top)
            for x in s.toe_x
            for side in (1, -1)
        ]
        post = z_cylinder(POST_DIAMETER, 0, p.post_y, s.datum_thickness, s.datum_thickness + s.post_length)
        # The tube as the step it is: the narrow threaded end, then the full diameter.
        tube = fused(
            y_cylinder(SM1L10_THREAD_DIAMETER, 0, s.optical_height, p.tube_end_y, p.tube_shoulder_y),
            y_cylinder(SM1L10_OUTER_DIAMETER, 0, s.optical_height, p.tube_shoulder_y, p.tube_open_end_y),
        )
        ring = moved(thorlabs_sm1rc_m(), Pos(0, p.clamp_ring_y, s.optical_height))
        shoe = moved(build_rail_shoe(), Pos(0, p.post_y, 0))
        # The project's clearance from rotating parts to a post and shoe (§7.5); the tube's own clearances over
        # the folds and from the fingers are the design clearances its position is set by.
        fixed = {
            "post": (post, s.post_clearance),
            "ring": (ring, s.post_clearance),
            "shoe": (shoe, s.post_clearance),
            "tube": (tube, min(p.fold_clearance, p.finger_wall_clearance)),
        }
        for rotation in ROTATION_SWEEP:
            loc = Pos(0, 0, s.optical_height) * Rot(Y=rotation)
            moving = [
                moved(bar, loc * Pos(0, 0, side * s.toe_z) * Rot(Y=turn))
                for side, turn in ((1, 0), (-1, 180))
            ]
            moving += [moved(head, loc) for head in heads]
            moving += [moved(blade(s, side), loc) for side in (1, -1)]
            for name, (part, required) in fixed.items():
                clearance = min(bounded_distance(m, part, required) for m in moving)
                self.assertGreaterEqual(clearance, required - 1e-6, msg=f"{name} at rotation {rotation}")


if __name__ == "__main__":
    unittest.main()

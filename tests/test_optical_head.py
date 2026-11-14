"""Engineering invariants for the assembled tabletop optical head (design §§2, 3)."""

import unittest
from math import pi

from schlieren.cad import box_between, children_by_label, intersect, leaves, moved
from schlieren.parts.optical_head import (
    OpticalHeadParameters,
    assemble_optical_head,
    build_imaging_fixtures,
    build_optical_head,
    build_source_fixtures,
)
from schlieren.standards import DATUM_SHIM_THICKNESS, IMAGING_SIDE, POST_LENGTH, SOURCE_SIDE
from schlieren.testing import loose_box, near_pairs, slow

POST_TOP = DATUM_SHIM_THICKNESS + POST_LENGTH  # Datum shim plus TR50/M, above the rail top (§3.4).
TR50_MODEL_ROUNDING = 0.03  # The TR50/M STEP model is rounded to inches.
INTERFERENCE_TOLERANCE = 1e-3  # mm^3.
MIN_CLEARANCE = 1.0  # mm, between any source-side and imaging-side part.
# Vendor fasteners whose exact distance queries are slow (about a second each); their clearance is checked
# against a nominal envelope instead (see `nominal_envelope`).
ENVELOPED_FASTENERS = ("Keeper nut", "Keeper screw")
# (left rail yaw, right rail yaw, slit rotation, cutoff stagger): degrees outward from nominal, degrees, mm.
# The frame's yaw range is +-3 degrees (§4.2), the slit turns through its working range, and the stagger
# starting point is 30-40 mm (§3.3).
EXTREME_POSES = (
    (-3.0, -3.0, 0.0, 0.0),  # Rails converged, slit and cutoff in the same plane: the closest approach.
    (-3.0, -3.0, 45.0, 35.0),
    (3.0, 3.0, 0.0, -35.0),
    (-3.0, 3.0, -90.0, 0.0),  # Vertical slit, micrometer outboard: clear with no stagger.
    (-3.0, 3.0, 90.0, 17.5),  # Micrometer toward the cutoff carriage: needs about 16 mm of stagger.
    (3.0, -3.0, 90.0, 35.0),
)


def nominal_envelope(leaf, rail_loc):
    """A box in the rail frame (the rail's Location in the pivot frame) enclosing the vendor fastener leaf.

    It stands in for the fastener in distance queries, which are slow on the vendor B-rep. The box contains
    the fastener, so a clearance that holds to the box holds to the fastener.
    """
    box = loose_box(moved(leaf, rail_loc.inverse()))
    return moved(box_between(box.min.X, box.max.X, box.min.Y, box.max.Y, box.min.Z, box.max.Z), rail_loc)


def by_label(node, label):
    return [leaf for leaf in leaves(node) if leaf.label == label]


class OpticalHeadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h = OpticalHeadParameters()
        # The fixture groups in the rail frames, where stations are measured; the head places copies of them
        # in the pivot frame, so each is built once.
        cls.source = build_source_fixtures(cls.h)
        cls.imaging = build_imaging_fixtures(cls.h)
        cls.head = assemble_optical_head(cls.h, cls.source, cls.imaging)
        cls.groups = children_by_label(cls.head)

    def test_shoe_ears_and_ring_screws_face_outboard_on_both_rails(self):
        """Ears and locking-screw heads point away from the other rail, for reaching them: -x on the source
        rail (the three shoes and the two split rings), +x on the imaging rail (the cutoff's)."""
        for group, side, shoes, rings in (
            (self.source, SOURCE_SIDE, 3, 2),
            (self.imaging, IMAGING_SIDE, 1, 1),
        ):
            with self.subTest(side=side):
                shoe_boxes = [leaf.bounding_box() for leaf in by_label(group, "Rail shoe")]
                self.assertEqual(len(shoe_boxes), shoes)
                for box in shoe_boxes:
                    self.assertGreater((box.max.X + box.min.X) * side, 0.0)
                ring_screws = [
                    min(leaf.solids(), key=lambda s: s.volume).bounding_box()
                    for leaf in by_label(group, "SM1RC M ring")
                ]
                self.assertEqual(len(ring_screws), rings)
                for box in ring_screws:
                    self.assertGreater(box.center().X * side, 0.0)

    def test_stations_stand_on_the_rails(self):
        self.h.validate()
        for station in (
            self.h.slit_post_station,
            self.h.field_lens_post_station,
            self.h.light_source_post_station,
            self.h.cutoff_post_station,
        ):
            self.assertLess(-self.h.frame.rail_front_setback - self.h.frame.rail_length, station)
            self.assertLess(station, -self.h.frame.rail_front_setback)

    def test_posts_stand_at_the_common_height(self):
        for group in (self.source, self.imaging):
            posts = by_label(group, "TR50 M post")
            self.assertTrue(posts)
            for post in posts:
                body = max(post.solids(), key=lambda s: s.volume)  # Not the setscrew stud above the top.
                self.assertAlmostEqual(body.bounding_box().max.Z, POST_TOP, delta=TR50_MODEL_ROUNDING)
        # Light source, slit, and field lens.
        self.assertEqual(len(by_label(self.source, "TR50 M post")), 3)
        self.assertEqual(len(by_label(self.imaging, "TR50 M post")), 1)  # Cutoff.

    def test_slit_blades_lie_on_the_slit_station(self):
        blades = [*by_label(self.source, "Stationary blade"), *by_label(self.source, "Movable blade")]
        self.assertEqual(len(blades), 2)
        for blade in blades:
            box = blade.bounding_box()
            # The blade rests on the blade-seat plane and extends toward the head's front, rail +y (toward
            # the mirror); its edge, inclined to the plane by the fold, dips about 0.1 mm behind it over the
            # 2.9 mm overhang.
            self.assertAlmostEqual(box.min.Y, self.h.slit_station, delta=0.1)

    def test_condenser_is_the_design_distance_from_the_slit(self):
        (lens,) = by_label(self.source, "ACL2520U-A condenser")
        ls = self.h.light_source
        vertex = lens.bounding_box().max.Y  # Plano face toward the LED, convex vertex toward the slit (§6).
        self.assertAlmostEqual(self.h.slit_station - vertex, ls.lens_to_slit, delta=0.05)

    def test_field_lens_stands_ahead_of_the_slit_on_its_own_post(self):
        lens = self.h.field_lens_parameters
        (glass,) = by_label(self.source, "Field lens LA1433-A")
        # The plano face is the lens's rear: the design distance ahead of the blade plane, on the axis.
        box = glass.bounding_box()
        self.assertAlmostEqual(box.min.Y - self.h.slit_station, lens.lens_plano_y, delta=0.01)
        self.assertAlmostEqual(box.center().Z, self.h.slit.optical_height, delta=0.01)
        # Its post stands ahead of the slit's by the design spacing, with the shoes clear of each other.
        self.assertAlmostEqual(
            self.h.field_lens_post_station - self.h.slit_post_station, lens.post_spacing, delta=0.01
        )

    def test_field_lens_can_be_left_out(self):
        bare = OpticalHeadParameters(field_lens=False)
        bare.validate()
        source = build_source_fixtures(bare)
        self.assertEqual(by_label(source, "Field lens LA1433-A"), [])
        self.assertEqual(len(by_label(source, "TR50 M post")), 2)  # Light source and slit.

    def test_cutoff_plane_follows_the_stagger(self):
        base = OpticalHeadParameters()
        moved = OpticalHeadParameters(cutoff_stagger=17.5)
        self.assertAlmostEqual(moved.cutoff_post_station - base.cutoff_post_station, 17.5)
        self.assertAlmostEqual(moved.phone_back_station - base.phone_back_station, 17.5)
        self.assertAlmostEqual(moved.slit_post_station, base.slit_post_station)

    def test_lens_front_keeps_the_assumed_gap_to_the_split_ring(self):
        (lens,) = by_label(self.imaging, "Lens body")
        (ring,) = by_label(self.imaging, "SM1RC M ring")
        gap = ring.bounding_box().min.Y - lens.bounding_box().max.Y
        self.assertAlmostEqual(gap, 10.0, delta=0.05)

    def test_imaging_fixtures_do_not_carry_their_own_rail(self):
        self.assertEqual(by_label(self.imaging, "Rail"), [])
        self.assertEqual(by_label(self.imaging, "Optical axis"), [])

    def test_head_has_frame_and_both_fixture_groups(self):
        self.assertEqual(
            set(self.groups),
            {"Tabletop frame", "Source rail fixtures", "Imaging rail fixtures"},
        )
        self.assertEqual(
            set(children_by_label(self.groups["Tabletop frame"])),
            {"Pivot plate assembly", "Left rail assembly", "Right rail assembly"},
        )

    @slow
    def test_source_and_imaging_fixtures_clear_each_other(self):
        self.assert_fixtures_clear_each_other(self.groups)

    @slow
    def test_fixtures_clear_the_frame(self):
        self.assert_fixtures_clear_the_frame(self.groups)

    @slow
    def test_clearances_hold_at_the_adjustment_extremes(self):
        """The head is clear in the poses that bring its parts closest, not only at nominal.

        With both rails yawed inward and the slit and cutoff un-staggered, the slit head passes the
        cutoff carriage's keeper frame at only about 1.4 mm (the stagger of §3.3 is what gives margin); the
        assertions keep that above MIN_CLEARANCE. The other poses cover opposite yaws, slit rotations, and the
        stagger at both signs.
        """
        for yaw_left, yaw_right, slit_rotation, stagger in EXTREME_POSES:
            with self.subTest(yaw=(yaw_left, yaw_right), slit_rotation=slit_rotation, stagger=stagger):
                head = build_optical_head(
                    OpticalHeadParameters(cutoff_stagger=stagger), yaw_left, yaw_right, slit_rotation
                )
                groups = children_by_label(head)
                self.assert_fixtures_clear_each_other(groups, yaw_right)
                self.assert_fixtures_clear_the_frame(groups)

    def assert_fixtures_clear_each_other(self, groups, yaw_right=0.0):
        source = leaves(groups["Source rail fixtures"])
        imaging = leaves(groups["Imaging rail fixtures"])
        imaging_loc = self.h.frame.rail_location(IMAGING_SIDE, yaw_right * pi / 180)
        for s, i in near_pairs(source, imaging, MIN_CLEARANCE):
            other = nominal_envelope(i, imaging_loc) if i.label.startswith(ENVELOPED_FASTENERS) else i
            self.assertGreaterEqual(
                s.distance_to(other),
                MIN_CLEARANCE,
                f"{s.label} and {i.label} are closer than {MIN_CLEARANCE} mm",
            )

    def assert_fixtures_clear_the_frame(self, groups):
        """No part of a fixture touches the frame hardware; the shoes straddle the rails, so only an overlap
        with a rail counts there."""
        frame = leaves(groups["Tabletop frame"])
        for group in ("Source rail fixtures", "Imaging rail fixtures"):
            for s, f in near_pairs(leaves(groups[group]), frame, MIN_CLEARANCE):
                if f.label == "Rail":
                    volume = intersect(s, f).volume
                    self.assertLess(volume, INTERFERENCE_TOLERANCE, f"{s.label} and the rail interfere")
                else:
                    self.assertGreaterEqual(
                        s.distance_to(f),
                        MIN_CLEARANCE,
                        f"{s.label} is within {MIN_CLEARANCE} mm of {f.label}",
                    )


if __name__ == "__main__":
    unittest.main()

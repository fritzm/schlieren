"""Engineering invariants for the assembled tabletop optical head (design §§2, 3)."""

import unittest
from math import pi

from schlieren.cad import box_between, children_by_label, intersect, leaves, moved
from schlieren.parts.optical_head import (
    IMAGING_SIDE,
    OpticalHeadParameters,
    build_imaging_fixtures,
    build_optical_head,
    build_source_fixtures,
)
from schlieren.standards import DATUM_DISC_THICKNESS, POST_LENGTH
from schlieren.testing import loose_box, near_pairs, slow

POST_TOP = DATUM_DISC_THICKNESS + POST_LENGTH  # Datum disc plus TR50/M, above the rail top (§3.4).
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
    (-3.0, 3.0, 90.0, 0.0),
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
        cls.head = build_optical_head(cls.h)
        cls.groups = children_by_label(cls.head)
        # The fixture groups are in the pivot frame, so measure stations in rail frames from the models.
        cls.source = build_source_fixtures(cls.h)
        cls.imaging = build_imaging_fixtures(cls.h)

    def test_stations_stand_on_the_rails(self):
        self.h.validate()
        for station in (
            self.h.slit_post_station,
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
        self.assertEqual(len(by_label(self.source, "TR50 M post")), 2)  # Light source and slit.
        self.assertEqual(len(by_label(self.imaging, "TR50 M post")), 1)  # Cutoff.

    def test_slit_blades_lie_on_the_slit_station(self):
        blades = [*by_label(self.source, "Datum blade"), *by_label(self.source, "Width blade")]
        self.assertEqual(len(blades), 2)
        for blade in blades:
            box = blade.bounding_box()
            # The blade seats on the blade-seat plane and extends toward the head's front, rail -y.
            self.assertAlmostEqual(box.max.Y, self.h.slit_station, delta=0.01)

    def test_condenser_is_the_design_distance_from_the_slit(self):
        (lens,) = by_label(self.source, "ACL2520U-A condenser")
        ls = self.h.light_source
        vertex = lens.bounding_box().max.Y  # Plano face toward the LED, convex vertex toward the slit (§6).
        self.assertAlmostEqual(self.h.slit_station - vertex, ls.lens_to_slit, delta=0.05)

    def test_cutoff_plane_follows_the_stagger(self):
        base = OpticalHeadParameters()
        moved = OpticalHeadParameters(cutoff_stagger=17.5)
        self.assertAlmostEqual(moved.cutoff_post_station - base.cutoff_post_station, 17.5)
        self.assertAlmostEqual(moved.phone_back_station - base.phone_back_station, 17.5)
        self.assertAlmostEqual(moved.slit_post_station, base.slit_post_station)

    def test_lens_front_keeps_the_assumed_gap_to_the_slip_ring(self):
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

        With both rails yawed inward and the slit and cutoff un-staggered, the slit's flexure head passes the
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

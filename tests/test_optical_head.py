"""Engineering invariants for the assembled tabletop optical head (design §§2, 3)."""

import unittest

from schlieren.cad import children_by_label, leaves
from schlieren.parts.optical_head import (
    OpticalHeadParameters,
    build_imaging_fixtures,
    build_optical_head,
    build_source_fixtures,
)
from schlieren.standards import DATUM_DISC_THICKNESS, POST_LENGTH
from schlieren.testing import near_pairs, slow

POST_TOP = DATUM_DISC_THICKNESS + POST_LENGTH  # Datum disc plus TR50/M, above the rail top (§3.4).
TR50_MODEL_ROUNDING = 0.03  # The TR50/M STEP model is rounded to inches.
INTERFERENCE_TOLERANCE = 1e-3  # mm^3.
MIN_CLEARANCE = 1.0  # mm, between any source-side and imaging-side part.


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
        (lens,) = by_label(self.imaging, "Telephoto envelope")
        (ring,) = by_label(self.imaging, "SM1RC M ring")
        gap = ring.bounding_box().min.Y - lens.bounding_box().max.Y
        self.assertAlmostEqual(gap, 10.0, delta=0.05)

    def test_imaging_fixtures_do_not_carry_their_own_rail(self):
        self.assertEqual(by_label(self.imaging, "Rail"), [])
        self.assertEqual(by_label(self.imaging, "Optical axis"), [])

    def test_head_has_frame_and_both_fixture_groups(self):
        self.assertEqual(
            set(self.groups),
            {
                "Pivot plate assembly",
                "Left rail assembly",
                "Right rail assembly",
                "Source rail fixtures",
                "Imaging rail fixtures",
            },
        )

    @slow
    def test_source_and_imaging_fixtures_clear_each_other(self):
        source = leaves(self.groups["Source rail fixtures"])
        imaging = leaves(self.groups["Imaging rail fixtures"])
        for s, i in near_pairs(source, imaging, MIN_CLEARANCE):
            self.assertGreaterEqual(
                s.distance_to(i),
                MIN_CLEARANCE,
                f"{s.label} and {i.label} are closer than {MIN_CLEARANCE} mm",
            )

    @slow
    def test_fixtures_clear_the_frame(self):
        """No part of a fixture touches the frame hardware; the shoes straddle the rails, so only an overlap
        with a rail counts there."""
        frame = [
            leaf
            for name in ("Pivot plate assembly", "Left rail assembly", "Right rail assembly")
            for leaf in leaves(self.groups[name])
        ]
        for group in ("Source rail fixtures", "Imaging rail fixtures"):
            for s, f in near_pairs(leaves(self.groups[group]), frame, MIN_CLEARANCE):
                if f.label == "Rail":
                    common = s.intersect(f)
                    volume = common.volume if common is not None else 0.0
                    self.assertLess(volume, INTERFERENCE_TOLERANCE, f"{s.label} and the rail interfere")
                else:
                    self.assertGreaterEqual(
                        s.distance_to(f),
                        MIN_CLEARANCE,
                        f"{s.label} is within {MIN_CLEARANCE} mm of {f.label}",
                    )


if __name__ == "__main__":
    unittest.main()

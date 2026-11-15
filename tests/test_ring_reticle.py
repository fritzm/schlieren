"""Ring reticle: two identical snap-together halves forming a sighting tube for the cutoff post's ring."""

import math
import unittest
from dataclasses import replace

from build123d import Vector

from schlieren.cad import children_by_label, intersect
from schlieren.parts.camera_support import LENS_TO_SPLIT_RING
from schlieren.parts.ring_reticle import (
    HALF_LABEL,
    PRINT_FIRST_LAYER,
    PRINT_LAYER_HEIGHT,
    RingReticleParameters,
    build_reticle_half,
    build_ring_reticle,
    build_ring_reticle_assembly,
    lens_clearance,
    snapped_locations,
)
from schlieren.standards import DATUM_SHIM_THICKNESS, INCH, OPTICAL_HEIGHT, SM1_TUBE_DIAMETER, SM1RC_M_BORE
from schlieren.testing import shared
from schlieren.vendor_cad import SM1RC_M_THICKNESS

MEASURED_FRONT_CLEAR_APERTURE = 0.845 * INCH  # §9.2.


def arm_point(angle_deg, radius, y, across=0.0):
    """A point along the arm of the cross at angle_deg (from +x toward +z), radius out, offset across the arm."""
    a = math.radians(angle_deg)
    return Vector(radius * math.cos(a) - across * math.sin(a), y, radius * math.sin(a) + across * math.cos(a))


def radial_point(radius, y, angle_deg):
    a = math.radians(angle_deg)
    return Vector(radius * math.cos(a), y, radius * math.sin(a))


class RingReticleTests(unittest.TestCase):
    @shared
    def unit(cls):
        return build_ring_reticle(cls.p)

    @shared
    def head(cls):
        return build_ring_reticle_assembly(cls.p)

    @classmethod
    def setUpClass(cls):
        cls.p = RingReticleParameters()
        cls.p.validate()
        cls.half = build_reticle_half(cls.p)

    def test_half_is_one_valid_solid_standing_on_its_crosshair_end(self):
        self.assertEqual(len(self.half.solids()), 1)
        self.assertTrue(self.half.is_valid)
        box = self.half.bounding_box()
        self.assertAlmostEqual(box.min.Y, 0, places=6)
        self.assertAlmostEqual(box.max.Y, self.p.body_length + self.p.arm_length, places=9)

    def test_tube_is_the_carriage_spigots_diameter(self):
        p = self.p
        self.assertEqual(p.tube_diameter, SM1_TUBE_DIAMETER)
        box = self.half.bounding_box()
        for extent in (box.max.X, -box.min.X, box.max.Z, -box.min.Z):
            self.assertAlmostEqual(extent, p.tube_diameter / 2, places=6)

    def test_crosshair_marks_the_axis_across_an_open_bore(self):
        p = self.p
        mid_hair = p.hair_thickness / 2
        self.assertTrue(self.half.is_inside(Vector(0, mid_hair, 0)))
        for x, z in ((p.bore / 4, 0), (0, -p.bore / 4)):  # Along each arm of the cross.
            self.assertTrue(self.half.is_inside(Vector(x, mid_hair, z)))
        # Between the arms the bore is clear; above the hair's two layers, so is the axis.
        self.assertFalse(self.half.is_inside(Vector(p.bore / 4, mid_hair, p.bore / 4)))
        self.assertFalse(self.half.is_inside(Vector(0, p.hair_thickness + 1.0, 0)))

    def test_hairs_are_several_layers_thick_and_axial_planes_sit_on_the_layer_grid(self):
        p = self.p
        self.assertGreaterEqual(p.hair_layers, 4)  # Two layers broke off the first print.
        for plane in (p.hair_thickness, p.body_length, p.body_length + p.arm_length):
            layers = (plane - PRINT_FIRST_LAYER) / PRINT_LAYER_HEIGHT
            self.assertAlmostEqual(layers, round(layers), places=6, msg=f"{plane} is between layers")

    def test_each_hair_has_a_one_sided_fin_along_the_wall(self):
        p = self.p
        h, rb, r, hw = p.hair_thickness, p.bore_radius, p.hair_top_fillet_radius, p.hair_width / 2
        for angle in (0, 90, 180, 270):
            # The corner between the hair's open face and the wall is filled, across the hair's width only.
            for across in (0.0, hw - 0.05, -(hw - 0.05)):
                self.assertTrue(
                    self.half.is_inside(arm_point(angle, rb - 0.2, h + 0.2, across)), (angle, across)
                )
            for across in (hw + 0.1, -(hw + 0.1)):
                self.assertFalse(
                    self.half.is_inside(arm_point(angle, rb - 0.2, h + 0.2, across)), (angle, across)
                )
            # Nothing flares the hair in the plane of the bed: beside it, at the wall, the bore is open.
            for across in (hw + 0.2, -(hw + 0.2)):
                self.assertFalse(
                    self.half.is_inside(arm_point(angle, rb - 0.2, h / 2, across)), (angle, across)
                )
            # The fin's round is concave: its center is open, and it is no taller than its radius.
            self.assertFalse(self.half.is_inside(arm_point(angle, rb - r, h + r)))
            self.assertFalse(self.half.is_inside(arm_point(angle, rb - r - 0.3, h + 0.1)))
            self.assertFalse(self.half.is_inside(arm_point(angle, rb - 0.2, h + r + 0.2)))
        self.assertLess(r, rb - p.circle_diameter / 2 - p.hair_width)  # It ends short of the circle aid.
        # The hair's other face is the tube's end: nothing is added below it.
        self.assertAlmostEqual(self.half.bounding_box().min.Y, 0, places=6)

    def test_circle_aid_is_the_front_glass_and_the_bore_passes_it(self):
        p = self.p
        # The measured clear aperture of the front glass, §9.2 (the lens model's 0.82 in is the glass at the
        # bottom of the recess, a little smaller).
        self.assertAlmostEqual(p.circle_diameter, MEASURED_FRONT_CLEAR_APERTURE, delta=0.05)
        self.assertGreater(p.bore, p.circle_diameter)
        y = p.hair_thickness / 2
        self.assertTrue(self.half.is_inside(radial_point(p.circle_diameter / 2 + p.hair_width / 2, y, 20)))
        self.assertFalse(self.half.is_inside(radial_point(p.circle_diameter / 2 - p.hair_width, y, 20)))

    def test_halves_snap_into_one_tube_without_touching_where_they_should_not(self):
        p = self.p
        aft, fore = (c.bounding_box() for c in self.unit.children)
        self.assertAlmostEqual(min(aft.min.Y, fore.min.Y), 0, places=6)
        self.assertAlmostEqual(max(aft.max.Y, fore.max.Y), p.unit_length, places=6)
        a, b = self.unit.children
        self.assertAlmostEqual(intersect(a, b).volume, 0, places=6)
        # The arms' clearances are small but real: the halves stay apart.
        self.assertGreater(a.distance_to(b), p.arm_slack / 2)
        self.assertLess(a.distance_to(b), 0.1)

    def test_fit_stays_as_tight_as_the_second_print_made_it(self):
        # The first print was loose axially and circumferentially; these are the tightened clearances.
        p = self.p
        self.assertLessEqual(p.arm_slack, 0.05)  # Axial play between the halves.
        self.assertLessEqual(p.groove_axial_clearance, 0.10)  # Per side, ridge in groove.
        self.assertLessEqual(p.arm_side_clearance, 0.10)  # Per side, circumferential play of the arms.

    def test_snapped_tube_is_flush_all_round(self):
        p = self.p
        mid = p.unit_length / 2
        for angle in (10, 80, 100, 170, 190, 260, 280, 350):
            self.assertTrue(
                any(c.is_inside(radial_point(p.outer_radius - 0.2, mid, angle)) for c in self.unit.children),
                angle,
            )
            self.assertFalse(
                any(c.is_inside(radial_point(p.outer_radius + 0.2, mid, angle)) for c in self.unit.children)
            )

    def test_wall_is_whole_at_the_lap(self):
        # In every quadrant, both the outer and inner shells are present at mid-lap, one from each half.
        p = self.p
        mid = p.unit_length / 2
        for angle in (45, 135, 225, 315):
            inner = radial_point(p.bore_radius + p.shell_thickness / 2, mid, angle)
            outer = radial_point(p.outer_radius - p.shell_thickness / 2, mid, angle)
            a, b = self.unit.children
            self.assertNotEqual(a.is_inside(inner), b.is_inside(inner), angle)
            self.assertNotEqual(a.is_inside(outer), b.is_inside(outer), angle)
            self.assertNotEqual(a.is_inside(inner), a.is_inside(outer), angle)

    def test_each_ridge_sits_in_the_groove_that_covers_it(self):
        p = self.p
        a, b = self.unit.children
        ridge_mid = p.body_length + p.ridge_from_root + p.ridge_return + p.ridge_flat / 2
        # The fore half is turned end for end: its arm position s sits at unit_length - (body + s) from y = 0.
        y = p.unit_length - ridge_mid
        r = p.interface_radius - p.lap_radial_clearance + 0.9 * p.ridge_height
        for angle in (45, 135, 225, 315):
            point = radial_point(r, y, angle)
            self.assertTrue(b.is_inside(point), angle)  # The ridge is on the fore half's inner arm.
            self.assertFalse(a.is_inside(point), angle)  # And the aft half's groove is cut there.

    def test_ridge_is_proud_of_the_facing_arm_and_the_groove_floor_is_above_it(self):
        p = self.p
        self.assertGreater(p.interference, 0)
        self.assertGreater(p.groove_depth, p.interference)
        self.assertGreaterEqual(p.wall_under_groove, p.min_wall_under_groove)
        self.assertLess(p.arm_strain_bound, 0.03)  # Beyond a few percent PLA does not recover.
        self.assertLessEqual(p.ridge_return, p.ridge_height)  # 45 degrees or steeper: prints unsupported.

    def test_identical_halves_assemble_either_way_round(self):
        # The halves are one part: both children are the same solid, only placed differently.
        a, b = self.unit.children
        self.assertAlmostEqual(a.volume, b.volume, places=6)
        self.assertEqual(self.unit.children[0].label, f"{HALF_LABEL}, aft")
        aft, fore = snapped_locations(self.p, 0.0)
        self.assertAlmostEqual(fore.position.Y - aft.position.Y, self.p.unit_length, places=9)

    def test_tube_clears_the_lens_with_room_to_slide(self):
        p = self.p
        centered = lens_clearance(p)
        self.assertGreater(centered, 3.0)
        # The lens front is the assumed gap behind the ring's rear face; the ring is centered on the origin.
        lens_front = -(SM1RC_M_THICKNESS / 2 + LENS_TO_SPLIT_RING)
        aft = children_by_label(self.head)[f"{HALF_LABEL}, aft"].bounding_box().min.Y
        self.assertAlmostEqual(aft - lens_front, centered, places=6)
        # The forward crosshair stands off the ring's front face by the same.
        fore = children_by_label(self.head)[f"{HALF_LABEL}, fore"].bounding_box().max.Y
        self.assertAlmostEqual(fore, aft + p.unit_length, places=6)

    def test_model_is_just_the_reticle_the_ring_the_post_and_the_shoe(self):
        self.assertEqual(
            sorted(c.label for c in self.head.children),
            sorted([f"{HALF_LABEL}, aft", f"{HALF_LABEL}, fore", "SM1RC M ring", "TR50 M post", "Rail shoe"]),
        )

    def test_origin_is_where_the_post_axis_meets_the_optical_axis(self):
        parts = children_by_label(self.head)
        center = lambda label: [  # noqa: E731
            (getattr(parts[label].bounding_box().min, a) + getattr(parts[label].bounding_box().max, a)) / 2
            for a in "XYZ"
        ]
        # The post stands on the origin's vertical, on its datum shim, OPTICAL_HEIGHT below the optical axis.
        post = parts["TR50 M post"].bounding_box()
        self.assertAlmostEqual((post.min.X + post.max.X) / 2, 0, places=3)
        self.assertAlmostEqual((post.min.Y + post.max.Y) / 2, 0, places=3)
        self.assertAlmostEqual(post.min.Z, DATUM_SHIM_THICKNESS - OPTICAL_HEIGHT, places=3)
        # The reticle is centered on the optical axis, which runs along y through the origin.
        for label in (f"{HALF_LABEL}, aft", f"{HALF_LABEL}, fore"):
            x, _, z = center(label)
            self.assertAlmostEqual(x, 0, places=3, msg=label)
            self.assertAlmostEqual(z, 0, places=3, msg=label)
        # So is the ring: it straddles the post and its bore is centered on the origin. Its post seat below and
        # its locking screw above make its box lopsided, so probe the bore along the diagonals, away from its
        # split and seat: open just inside its wall, ring material just outside.
        ring = parts["SM1RC M ring"]
        bore = SM1RC_M_BORE / 2
        self.assertFalse(ring.is_inside(Vector(0, 0, 0)))
        for angle in (45, 135, 225, 315):
            self.assertFalse(ring.is_inside(arm_point(angle, bore - 0.3, 0)), angle)
            self.assertTrue(ring.is_inside(arm_point(angle, bore + 0.5, 0)), angle)
        box = ring.bounding_box()
        self.assertAlmostEqual((box.min.Y + box.max.Y) / 2, 0, places=3)

    def test_validate_rejects_a_snap_that_cannot_work(self):
        for change in (
            {"ridge_height": 0.15},  # Would not stand proud of the facing arm.
            {"ridge_return": 0.6},  # Shallower than 45 degrees.
            {"groove_depth": 0.2},  # Shallower than the interference.
            {"groove_depth": 0.9},  # Leaves no wall.
            {"bore": 31.0},
            {"circle_diameter": 26.0},
            {"hair_top_fillet_radius": 2.0},
        ):
            with self.assertRaises(ValueError, msg=str(change)):
                replace(self.p, **change).validate()


if __name__ == "__main__":
    unittest.main()

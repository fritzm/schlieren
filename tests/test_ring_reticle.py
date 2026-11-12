"""Ring reticle: two identical snap-together halves forming a sighting tube for the cutoff post's ring."""

import math
import unittest
from dataclasses import replace

from build123d import Vector

from schlieren.cad import children_by_label, intersect
from schlieren.parts.camera_support import CameraSupportParameters
from schlieren.parts.ring_reticle import (
    HALF_LABEL,
    RingReticleParameters,
    build_reticle_half,
    build_ring_reticle,
    build_ring_reticle_assembly,
    lens_clearance,
    snapped_locations,
)
from schlieren.standards import INCH, SM1_TUBE_DIAMETER
from schlieren.testing import shared

MEASURED_FRONT_CLEAR_APERTURE = 0.845 * INCH  # §9.2.


def radial_point(radius, y, angle_deg):
    a = math.radians(angle_deg)
    return Vector(radius * math.cos(a), y, radius * math.sin(a))


class RingReticleTests(unittest.TestCase):
    @shared
    def unit(cls):
        return build_ring_reticle(cls.p)

    @shared
    def head(cls):
        return build_ring_reticle_assembly(cls.p, include_support=False)

    @classmethod
    def setUpClass(cls):
        cls.p = RingReticleParameters()
        cls.p.validate()
        cls.half = build_reticle_half(cls.p)

    def test_half_is_one_valid_solid_standing_on_its_crosshair_end(self):
        self.assertEqual(len(self.half.solids()), 1)
        self.assertTrue(self.half.is_valid)
        box = self.half.bounding_box()
        self.assertAlmostEqual(box.min.Y, 0, places=9)
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
        self.assertLess(a.distance_to(b), p.lap_radial_clearance * 3)

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
        camera = CameraSupportParameters()
        centered = lens_clearance(p)
        self.assertGreater(centered, 3.0)
        # Where the aft crosshair actually is in the assembly agrees with the clearance.
        aft = children_by_label(self.head)[f"{HALF_LABEL}, aft"].bounding_box().min.Y
        self.assertAlmostEqual(aft - camera.lens_length, centered, places=6)
        # The forward crosshair stands off the ring's front face by the same.
        fore = children_by_label(self.head)[f"{HALF_LABEL}, fore"].bounding_box().max.Y
        self.assertAlmostEqual(fore, aft + p.unit_length, places=6)

    def test_assembly_axis_is_the_optical_height(self):
        camera = CameraSupportParameters()
        for child in self.head.children:
            box = child.bounding_box()
            self.assertAlmostEqual((box.min.X + box.max.X) / 2, 0, places=6)
            self.assertAlmostEqual((box.min.Z + box.max.Z) / 2, camera.optical_height, places=6)

    def test_validate_rejects_a_snap_that_cannot_work(self):
        for change in (
            {"ridge_height": 0.15},  # Would not stand proud of the facing arm.
            {"ridge_return": 0.6},  # Shallower than 45 degrees.
            {"groove_depth": 0.2},  # Shallower than the interference.
            {"groove_depth": 0.9},  # Leaves no wall.
            {"bore": 31.0},
            {"circle_diameter": 26.0},
        ):
            with self.assertRaises(ValueError, msg=str(change)):
                replace(self.p, **change).validate()


if __name__ == "__main__":
    unittest.main()

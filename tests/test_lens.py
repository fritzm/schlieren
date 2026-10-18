"""Engineering invariants for the telephoto lens model (design §9.2)."""

import unittest
from itertools import pairwise
from math import pi

from schlieren.cad import box_between, intersect, y_cylinder
from schlieren.parts.lens import (
    LensParameters,
    build_focus_ring,
    build_front_glass,
    build_glass,
    build_lens,
    build_lens_body,
)
from schlieren.standards import INCH
from schlieren.testing import shared

TOL = 1e-3  # mm


class LensTests(unittest.TestCase):
    @shared
    def front_glass(cls):
        return build_front_glass(cls.p)

    @shared
    def lens(cls):
        return build_lens(cls.p)

    @shared
    def glass(cls):
        return build_glass(cls.p)

    @classmethod
    def setUpClass(cls):
        cls.p = LensParameters()
        cls.body = build_lens_body(cls.p)
        cls.ring = build_focus_ring(cls.p)

    def test_body_is_one_valid_solid_on_the_y_axis(self):
        box = self.body.bounding_box()
        self.assertTrue(self.body.is_valid)
        self.assertEqual(len(self.body.solids()), 1)
        self.assertAlmostEqual(box.min.Y, 0.0, delta=TOL)
        self.assertAlmostEqual((box.min.X + box.max.X) / 2, 0.0, delta=TOL)
        self.assertAlmostEqual((box.min.Z + box.max.Z) / 2, 0.0, delta=TOL)

    def test_sections_are_the_measured_values(self):
        p = self.p
        self.assertAlmostEqual(p.boss_length, 0.10 * INCH, delta=TOL)
        self.assertAlmostEqual(p.shoulder_length, 0.40 * INCH, delta=TOL)
        self.assertAlmostEqual(p.shoulder_diameter, 1.26 * INCH, delta=TOL)
        self.assertAlmostEqual(p.barrel_length, 4.285 * INCH, delta=TOL)
        self.assertAlmostEqual(self.body.bounding_box().max.Y, 4.785 * INCH, delta=TOL)

    def test_diameters_step_up_from_the_thread_to_the_barrel(self):
        p, box = self.p, self.body.bounding_box()
        self.assertAlmostEqual(box.size.X, p.barrel_diameter, delta=TOL)
        self.assertLess(p.thread_diameter, p.shoulder_diameter)
        self.assertLess(p.shoulder_diameter, p.barrel_diameter)
        # A slice through the boss is the thread's diameter, through the shoulder the shoulder's.
        for y, diameter in ((p.boss_length / 2, p.thread_diameter), (p.boss_length + 1, p.shoulder_diameter)):
            probe = box_between(-50, 50, y - 0.1, y + 0.1, -50, 50)
            section = (self.body & probe).bounding_box()
            self.assertAlmostEqual(section.size.X, diameter, delta=TOL)

    def test_barrel_root_is_filleted_into_the_shoulder(self):
        p = self.p
        r = p.barrel_root_fillet

        def width_at(y):
            return (self.body & box_between(-50, 50, y - 0.01, y + 0.01, -50, 50)).bounding_box().size.X

        self.assertAlmostEqual(width_at(p.barrel_start - r - 0.5), p.shoulder_diameter, delta=TOL)
        self.assertGreater(width_at(p.barrel_start - 0.2), p.shoulder_diameter + 1.0)
        self.assertLess(width_at(p.barrel_start - 0.2), p.barrel_diameter)
        # A circular fillet of radius r is r - sqrt(r^2 - (r - d)^2) high at distance d from the face.
        d = r / 2
        expected = p.shoulder_diameter + 2 * (r - (r**2 - (r - d) ** 2) ** 0.5)
        self.assertAlmostEqual(width_at(p.barrel_start - d), expected, delta=0.05)

    def test_shoulder_rear_edge_is_chamfered(self):
        p = self.p
        c = p.shoulder_rear_chamfer

        def width_at(y):
            return (self.body & box_between(-50, 50, y - 0.01, y + 0.01, -50, 50)).bounding_box().size.X

        self.assertAlmostEqual(width_at(p.boss_length + c + 0.5), p.shoulder_diameter, delta=TOL)
        self.assertAlmostEqual(width_at(p.boss_length + c / 2), p.shoulder_diameter - c, delta=0.05)
        self.assertGreater(width_at(p.boss_length + 0.01), p.shoulder_diameter - 2 * c)

    def test_focus_ring_is_flush_with_the_barrel_with_raised_axial_ridges(self):
        p, ring = self.p, self.ring.bounding_box()
        self.assertTrue(self.ring.is_valid)
        self.assertEqual(len(self.ring.solids()), 1)
        self.assertAlmostEqual(self.body.bounding_box().max.Y - ring.max.Y, p.front_lip_length, delta=TOL)
        self.assertAlmostEqual(ring.size.Y, p.focus_ring_length, delta=TOL)
        self.assertGreater(ring.min.Y, p.barrel_start)
        # Ridge crests stand above the barrel; between them the ring is flush with it.
        self.assertAlmostEqual(ring.size.X, p.focus_ring_crest_diameter, delta=TOL)
        r, h, y0 = p.barrel_diameter / 2, p.focus_ridge_height, p.focus_ring_start
        above = y_cylinder(2 * (r + h), 0, 0, y0 - 1, y0 + p.focus_ring_length + 1) - y_cylinder(
            2 * (r + 0.05), 0, 0, y0 - 1, y0 + p.focus_ring_length + 1
        )
        ridges = intersect(self.ring, above)
        self.assertEqual(len(ridges.solids()), p.focus_ridge_count)
        # Rectangular ridges: width x (height above the cut) x length, less the round of the cut annulus.
        expected = p.focus_ridge_count * p.focus_ridge_width * (h - 0.05) * p.focus_ring_length
        self.assertAlmostEqual(ridges.volume / expected, 1.0, delta=0.03)
        # Ridges are axial: every cross-section through the ring is the same.
        mid = y0 + p.focus_ring_length / 2
        cut = lambda y: intersect(self.ring, box_between(-50, 50, y, y + 0.01, -50, 50)).volume  # noqa: E731
        self.assertAlmostEqual(cut(mid - 2), cut(mid + 2), delta=1e-6)

    def test_barrel_has_a_channel_that_holds_the_focus_ring_without_overlap(self):
        p = self.p
        mid = p.focus_ring_start + p.focus_ring_length / 2

        def body_width_at(y):
            return (self.body & box_between(-50, 50, y - 0.01, y + 0.01, -50, 50)).bounding_box().size.X

        self.assertAlmostEqual(body_width_at(mid), p.focus_ring_bore_diameter, delta=TOL)
        self.assertAlmostEqual(body_width_at(p.focus_ring_start - 0.5), p.barrel_diameter, delta=TOL)
        # The barrel runs on at the same diameter ahead of the ring.
        self.assertAlmostEqual(
            body_width_at(p.focus_ring_start + p.focus_ring_length + 0.5), p.barrel_diameter, delta=TOL
        )
        self.assertLess(intersect(self.body, self.ring).volume, 1e-6)
        self.assertEqual(len((self.body + self.ring).solids()), 1)  # Bearing on the channel floor.

    def test_barrel_ahead_of_the_focus_ring_keeps_its_diameter_with_a_rounded_front_edge(self):
        p = self.p

        def width_at(y):
            return (self.body & box_between(-50, 50, y - 0.01, y + 0.01, -50, 50)).bounding_box().size.X

        front = p.length
        self.assertAlmostEqual(width_at(front - p.front_lip_length / 2), p.barrel_diameter, delta=TOL)
        self.assertLess(width_at(front - 0.05), p.barrel_diameter - 1.0)  # Rounded.

    def test_front_face_steps_down_in_six_concentric_steps_to_the_glass(self):
        p = self.p
        front = p.length
        self.assertEqual(p.front_step_count, 6)
        self.assertAlmostEqual(p.front_glass_diameter, 0.82 * INCH, delta=TOL)  # Measured.
        self.assertAlmostEqual(p.front_glass_depth, 0.335 * INCH, delta=TOL)  # Measured.

        def solid_in(diameter, y0, y1):
            return intersect(self.body, y_cylinder(diameter, 0, 0, y0, y1)).volume

        diameters = [p.front_step_diameter(k) for k in range(p.front_step_count)]
        self.assertAlmostEqual(diameters[0], p.front_aperture_diameter)
        self.assertAlmostEqual(diameters[-1], p.front_glass_diameter)
        self.assertTrue(all(a > b for a, b in pairwise(diameters)))
        for k, diameter in enumerate(diameters):
            floor = front - (k + 1) * p.front_step_depth
            with self.subTest(step=k):
                # Open down to this step's floor at its diameter, with a shelf of material at the next.
                self.assertLess(solid_in(diameter - 0.02, floor + 0.01, front), 1e-6)
                if k:
                    outer = diameters[k - 1]
                    top = floor + p.front_step_depth
                    shelf = solid_in(outer - 0.02, top - 0.5, top) - solid_in(diameter + 0.02, top - 0.5, top)
                    self.assertGreater(shelf, 0.5)
        glass = self.front_glass
        box = glass.bounding_box()
        self.assertAlmostEqual(box.size.X, p.front_glass_diameter, delta=TOL)
        # Below the bottom step: the glass's front face is the step's floor, and it lies behind it.
        self.assertAlmostEqual(box.max.Y, front - p.front_glass_depth, delta=TOL)
        self.assertAlmostEqual(box.size.Y, p.front_glass_thickness, delta=TOL)
        self.assertLess(
            solid_in(p.front_glass_diameter - 0.02, front - p.front_glass_depth + 0.01, front), 1e-6
        )  # Nothing stands in the staircase.
        self.assertLess(intersect(self.body, glass).volume, 1e-6)
        self.assertLess(box.size.X, p.focus_ring_bore_diameter)  # Inside the ring's channel.

    def test_thin_groove_runs_round_the_barrel_1_3_in_from_the_shoulder(self):
        p = self.p
        y = p.barrel_start + 1.3 * INCH

        def width_at(y):
            return (self.body & box_between(-50, 50, y - 0.01, y + 0.01, -50, 50)).bounding_box().size.X

        self.assertAlmostEqual(width_at(y), p.barrel_diameter - 2 * p.barrel_groove_depth, delta=TOL)
        for side in (-1, 1):
            beyond = y + side * (p.barrel_groove_width / 2 + 0.2)
            self.assertAlmostEqual(width_at(beyond), p.barrel_diameter, delta=TOL)
        self.assertLess(p.barrel_groove_width, 0.5)  # Thin.

    def test_ridges_are_narrower_than_the_gaps_between_them(self):
        p = self.p
        pitch = pi * p.barrel_diameter / p.focus_ridge_count
        self.assertLess(p.focus_ridge_width, pitch - p.focus_ridge_width)

    def test_assembly_has_body_and_focus_ring(self):
        labels = sorted(child.label for child in self.lens.children)
        self.assertEqual(labels, ["Focus ring", "Front glass", "Lens body", "Lens glass"])

    def test_boss_is_a_ring_with_the_glass_inset_from_its_end(self):
        p, glass = self.p, self.glass.bounding_box()
        self.assertAlmostEqual(glass.min.Y, 0.05 * INCH, delta=TOL)  # Measured, §9.2.
        self.assertAlmostEqual(glass.size.X, p.thread_diameter - 2 * 0.10 * INCH, delta=TOL)  # Ring width.
        self.assertAlmostEqual(glass.size.X, p.boss_bore_diameter, delta=TOL)

        def width_at(y):
            return (self.body & box_between(-50, 50, y - 0.01, y + 0.01, -50, 50)).bounding_box().size.X

        self.assertAlmostEqual(width_at(0.01), p.thread_diameter, delta=TOL)
        hollow = box_between(
            -p.boss_bore_diameter / 2 + 0.1, p.boss_bore_diameter / 2 - 0.1, 0.0, p.glass_inset, -1, 1
        )
        self.assertLess(intersect(self.body, hollow).volume, 1e-6)  # Open in front of the glass.
        self.assertLess(intersect(self.body, self.glass).volume, 1e-6)  # The glass sits in the bore.


if __name__ == "__main__":
    unittest.main()

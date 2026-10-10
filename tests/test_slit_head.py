"""Flexure slit head (§7): datum, flexure, adjuster, fit, and clearance invariants."""

import unittest
from dataclasses import replace

from build123d import Pos

from schlieren.cad import box_between, z_cylinder
from schlieren.parts.rail_shoe import build_rail_shoe
from schlieren.parts.slit_head import (
    SlitHeadParameters,
    _blade,
    build_clamp_bar,
    build_slit_head,
    build_spigot_adapter,
    head_location,
)
from schlieren.testing import slow
from schlieren.vendor_cad import SM1RC_M_THICKNESS, thorlabs_fas100, thorlabs_sm1rc_m, thorlabs_tr50_m

MODEL_MATCH = 0.001
WORKING_ROTATIONS = (0, 5, -5, 90, -90)  # Horizontal, vertical, and parallelism trim.
ROTATION_SWEEP = range(-110, 111, 10)
TR50_STUD_MAX = 5.2  # TR50/M drawing: setscrew stud 4.6-5.2 mm above the post top.  # Working range with margin past vertical; ±90 included.


def _overlap(a, b):
    return (a & b).volume


class SlitHeadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = SlitHeadParameters()
        cls.p.validate()
        cls.head = build_slit_head(cls.p)
        cls.adapter = build_spigot_adapter(cls.p)
        cls.fas = [
            (Pos(x, cls.p.axis_y, z) * thorlabs_fas100())
            for x, z in (
                (cls.p.centering_screw_x, cls.p.centering_tip_z),
                (cls.p.width_screw_x, cls.p.width_tip_z),
            )
        ]

    def test_printed_parts_are_single_valid_solids(self):
        for part in (self.head, self.adapter, build_clamp_bar(self.p)):
            self.assertEqual(len(part.solids()), 1)
            self.assertTrue(part.is_valid)

    def test_flexures_are_the_only_links(self):
        """Severing the four flexure blades leaves frame, platform, and width stage as separate bodies."""
        p = self.p
        cut = self.head
        for span, blades in (
            (p.width_blade_span, p.width_blades),
            (p.centering_blade_span, p.centering_blades),
        ):
            mid = sum(span) / 2
            for z0, z1 in blades:
                cut -= box_between(mid - 1, mid + 1, -p.body_thickness - 1, 1, z0 - 0.1, z1 + 0.1)
        self.assertEqual(len(cut.solids()), 3)

    def test_adjustment_keeps_slit_parallel_and_square(self):
        """In-plane stage rotation from adjusting, over a 10 mm illuminated slit length (first-order model)."""
        p = self.p
        lit_length = 10.0
        # Width: a 0.1 mm change tapers the slit by under 1 um; full travel by under 10 um.
        self.assertLess(p.stage_rotation("width") * 0.1 * lit_length, 0.001)
        self.assertLess(p.stage_rotation("width") * p.width_travel * lit_length, 0.010)
        # Centering: full travel skews the slit against the knife edge by under 1 um.
        self.assertLess(p.stage_rotation("centering") * 2 * p.centering_half_travel * lit_length, 0.001)

    def test_optical_height_datum(self):
        p = self.p
        ring_axis = -thorlabs_sm1rc_m().bounding_box().min.Z  # Post seat to axis.
        self.assertAlmostEqual(p.datum_thickness + p.post_length + ring_axis, p.optical_height, delta=0.01)

    def test_slit_centered_on_axis_with_blades_on_seat_plane(self):
        p = self.p
        upper, lower = _blade(p, 1).bounding_box(), _blade(p, -1).bounding_box()
        self.assertAlmostEqual(upper.min.Z, p.slit_width / 2, places=9)
        self.assertAlmostEqual(lower.max.Z, -p.slit_width / 2, places=9)
        self.assertAlmostEqual(upper.min.Y, 0, places=9)
        self.assertEqual(self.head.bounding_box().max.Y, 0)
        # The blades, not the head, bound the illuminated aperture.
        self.assertGreater(p.blade_length / 2, p.spigot_bore / 2 + 3)

    def test_flexure_strain_and_preload(self):
        p = self.p
        self.assertLess(p.centering_strain, 0.005)
        self.assertLess(p.width_strain, 0.005)
        # Width-stage flexure preload holds the stage (~12 g with blade and clamp) on FAS100 #2 in any pose.
        self.assertGreater(min(p.width_preload_range), 0.5)
        self.assertGreater(min(p.spring_force_range), 3.0)

    def test_adjustment_ranges(self):
        p = self.p
        self.assertGreaterEqual(p.centering_half_travel, 1.5)  # ~±30 mm of beam steering at the mirror.
        self.assertGreaterEqual(p.width_travel, 0.5)  # Covers the 0.10-0.30 mm working widths with margin.

    def test_spigot_fits_sm1rc_m(self):
        p = self.p
        clearance = p.ring_bore - p.spigot_diameter
        self.assertGreater(clearance, 0)
        self.assertLess(clearance, 0.3)
        self.assertGreaterEqual(p.spigot_length, p.ring_thickness)

    def test_insert_and_nut_material(self):
        p = self.p
        self.assertGreaterEqual(p.bar_thickness, p.insert_min_material)
        self.assertLess(p.clamp_nut_floor, -2.0)

    def test_hardware_clears_printed_parts(self):
        p, head = self.p, self.head
        for fas in self.fas:
            self.assertAlmostEqual(_overlap(fas, head), 0, places=3)
        self.assertAlmostEqual(_overlap(self.fas[0], self.fas[1]), 0, places=3)
        for sign in (1, -1):
            self.assertAlmostEqual(_overlap(_blade(p, sign), head), 0, places=3)
        self.assertAlmostEqual(_overlap(self.adapter, head), 0, places=3)

    @slow
    def test_working_rotations_clear_post_ring_and_shoe(self):
        p = self.p
        support = [
            (Pos(0, 0, p.datum_thickness) * thorlabs_tr50_m()),
            (Pos(0, -SM1RC_M_THICKNESS / 2, p.optical_height) * thorlabs_sm1rc_m()),
            build_rail_shoe(),
        ]
        for rotation in WORKING_ROTATIONS:
            loc = head_location(p, rotation)
            moving = [(loc * self.head), (loc * self.adapter)] + [(loc * f) for f in self.fas]
            for part in moving:
                for other in support:
                    self.assertAlmostEqual(_overlap(part, other), 0, places=3, msg=f"rotation {rotation}")

    @slow
    def test_rotation_sweep_keeps_clearance(self):
        """Corners, knobs, and the adapter clear the post and shoe all the way through the working range.

        The post's M4 stud is checked separately: it reaches up into the SM1RC/M's tapped hole and stops just
        short of the ring bore, so its gap to anything in the bore is set by Thorlabs, not by this design.
        """
        p = self.p
        # Nominal envelopes (the vendor solids make distance queries very slow): the metric post, and the M4
        # stud at its drawing maximum of 5.2 mm above the post top.
        post_top = p.datum_thickness + p.post_length
        body = z_cylinder(p.post_diameter, 0, 0, p.datum_thickness, post_top)
        stud = z_cylinder(4.0, 0, 0, post_top, post_top + TR50_STUD_MAX)
        shoe = build_rail_shoe()
        for rotation in ROTATION_SWEEP:
            loc = head_location(p, rotation)
            moving = [(loc * self.head), (loc * self.adapter)] + [(loc * f) for f in self.fas]
            for name, fixed in (("post", body), ("shoe", shoe)):
                clearance = min(part.distance_to(fixed) for part in moving)
                self.assertGreaterEqual(clearance, p.post_clearance, msg=f"{name} at rotation {rotation}")
            self.assertGreater(
                min(part.distance_to(stud) for part in moving), 1.0, msg=f"stud at rotation {rotation}"
            )

    def test_adapter_prints_flat_on_washer_spacers(self):
        p = self.p
        self.assertAlmostEqual(self.adapter.bounding_box().max.Y, p.adapter_front, places=6)
        self.assertGreaterEqual(p.spacer_washers * p.washer_thickness_min, p.stage_back_clearance)

    def test_spigot_shoulder_locates_ring(self):
        p = self.p
        bb = self.adapter.bounding_box()
        self.assertAlmostEqual(bb.min.Y, p.adapter_back - p.ring_gap - p.ring_thickness, places=6)
        ring = (
            head_location(p).inverse() * Pos(0, -SM1RC_M_THICKNESS / 2, p.optical_height) * thorlabs_sm1rc_m()
        )
        self.assertAlmostEqual(ring.bounding_box().max.Y, p.adapter_back - p.ring_gap, places=6)
        self.assertAlmostEqual(self.adapter.distance_to(ring), 0, places=3)  # Seated on the shoulder.
        self.assertAlmostEqual(_overlap(self.adapter, ring), 0, places=3)

    def test_vendor_models_match_parameters(self):
        p = self.p
        ring = thorlabs_sm1rc_m().bounding_box()
        self.assertAlmostEqual(ring.max.Y - ring.min.Y, p.ring_thickness, delta=MODEL_MATCH)
        fas = thorlabs_fas100()
        knob = max(fas.solids(), key=lambda s: s.volume if s.bounding_box().min.Z > 10 else 0).bounding_box()
        self.assertAlmostEqual(knob.min.Z, p.adjuster_thread_length, delta=MODEL_MATCH)
        self.assertAlmostEqual(knob.max.X - knob.min.X, p.adjuster_knob_diameter, delta=0.05)

    def test_validation_rejects_bad_layouts(self):
        for change in (
            {"centering_half_travel": 3.0},  # Exceeds the running clearance.
            {"spigot_diameter": 31.0},  # Does not enter the SM1RC/M.
            {"width_blade_thickness": 3.0},  # Overstrained flexure.
            {"spring_outer_diameter": 11.0},  # Does not fit the lower platform connector.
            {"width_screw_x": -15.0},  # FAS100 #2 knob hits the frame top bar.
            {"ring_gap": 2.0},  # Adapter plate within 2 mm of the post.
            {"spigot_shoulder_diameter": 31.0},  # No land on the ring face.
        ):
            with self.assertRaises(ValueError, msg=str(change)):
                replace(self.p, **change).validate()


if __name__ == "__main__":
    unittest.main()

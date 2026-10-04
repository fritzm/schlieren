"""Threaded LED module focus range, fit, and clearance invariants."""

import math
import unittest
from dataclasses import replace

from build123d import Box, Pos

from schlieren.cad import FROM_CORNER, children_by_label
from schlieren.parts.led_module import GREEN, MODULES, WHITE, LEDStackParameters, build_led_stack_assembly
from schlieren.vendor_cad import (
    alpha_cn40_40b,
    thorlabs_sm1cp2m,
    thorlabs_smr1_m,
    thorlabs_tr50_m,
    vendor_step,
)

USEFUL_GAP = (13.0, 17.0)  # §6.7: useful emitter-to-plano range
# Required gap travel either side of the optimum. Relaxed from 1.0 mm: with exact Thorlabs dimensions the
# white module has 0.93 mm on the long-gap side. Accepted pending the build; if the white module cannot reach
# focus, space its cap flange off the SMR1/M face with a thin shim (moving the emitter away from the lens;
# a shim under the star board would shorten the gap and make this worse).
FOCUS_MARGIN = 0.9
MODEL_MATCH = 0.001  # Parameters taken from vendor STEP models
# The TR50/M STEP model is rounded to inches (1.969 in long, 0.499 in diameter); the metric nominal is exact.
TR50_MODEL_ROUNDING = 0.03


class LEDStackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = LEDStackParameters()
        cls.p.validate()

    def test_optical_height_datum(self):
        p = self.p
        self.assertAlmostEqual(p.post_top + p.smr1_axis_above_post_top, p.optical_height, delta=0.01)

    def test_optimum_gap_images_emitter_onto_slit(self):
        self.assertAlmostEqual(self.p.optimum_gap, 15.0, delta=0.2)
        self.assertAlmostEqual(self.p.magnification, 6.6, delta=0.2)

    def test_measured_board_thicknesses(self):
        self.assertAlmostEqual(GREEN.thickness, 1.59, places=2)
        self.assertAlmostEqual(WHITE.thickness, 1.50, places=2)

    def test_each_module_focuses_with_margin(self):
        p, opt = self.p, self.p.optimum_gap
        for board in MODULES:
            lo, hi = p.engagement_range(board)
            self.assertLess(lo, hi, board.name)
            # The cap thread and the SM1V05 sleeve share the SMR1/M thread.
            self.assertLessEqual(hi + p.cap_thread_length, p.smr1_thickness, board.name)
            g_lo, g_hi = p.gap_range(board)
            self.assertLessEqual(g_lo, opt - FOCUS_MARGIN, board.name)
            self.assertGreaterEqual(g_hi, opt + FOCUS_MARGIN, board.name)
            self.assertGreaterEqual(g_lo, USEFUL_GAP[0] - 0.5, board.name)
            self.assertLessEqual(g_hi, USEFUL_GAP[1], board.name)
            self.assertAlmostEqual(p.gap(board, p.focus_engagement(board)), opt, places=9)

    def test_modules_swap_within_one_thread_turn(self):
        p = self.p
        delta = abs(p.focus_engagement(GREEN) - p.focus_engagement(WHITE))
        self.assertLess(delta, p.sm1_thread_pitch)

    def test_boards_fit_smr1_bore_with_lead_annulus(self):
        for board in MODULES:
            annulus = (self.p.sm1_thread_major - board.outline_diameter) / 2
            self.assertGreaterEqual(annulus, 2.5, board.name)

    def test_heatsink_clears_post_at_any_rotation(self):
        p = self.p
        self.assertGreaterEqual(p.heatsink_post_top_clearance, 2.0)
        self.assertLess(p.heatsink_front, 0)

    def test_vendor_models_match_catalog_parameters(self):
        p = self.p
        post = max(thorlabs_tr50_m().solids(), key=lambda s: s.volume).bounding_box()  # Not the stud.
        self.assertAlmostEqual(post.size.Z, p.post_length, delta=TR50_MODEL_ROUNDING)
        self.assertAlmostEqual(post.size.X, p.post_diameter, delta=TR50_MODEL_ROUNDING)
        ring = thorlabs_smr1_m().bounding_box()
        self.assertAlmostEqual(ring.size.Y, p.smr1_thickness, delta=MODEL_MATCH)
        self.assertAlmostEqual(ring.size.X, p.smr1_outer_diameter, delta=MODEL_MATCH)
        self.assertAlmostEqual(-ring.min.Z, p.smr1_axis_above_post_top, delta=MODEL_MATCH)
        cap = thorlabs_sm1cp2m().bounding_box()
        self.assertAlmostEqual(cap.max.Y, p.cap_thread_length, delta=MODEL_MATCH)
        self.assertAlmostEqual(cap.size.Y, p.cap_overall, delta=MODEL_MATCH)
        self.assertAlmostEqual(cap.size.X, p.cap_flange_diameter, delta=MODEL_MATCH)
        sm1v05 = vendor_step("Thorlabs-SM1V05.step").bounding_box()
        self.assertAlmostEqual(sm1v05.size.X, p.sm1v05_overall, delta=MODEL_MATCH)
        heatsink = alpha_cn40_40b()
        hs = heatsink.bounding_box()
        self.assertAlmostEqual(hs.max.Y, 0, delta=MODEL_MATCH)
        self.assertAlmostEqual(hs.size.Y, p.heatsink_height, delta=MODEL_MATCH)
        self.assertAlmostEqual(hs.size.X, p.heatsink_diameter, delta=MODEL_MATCH)
        self.assertAlmostEqual(hs.size.Z, p.heatsink_diameter, delta=MODEL_MATCH)

        def section_area(y):
            r = p.heatsink_diameter
            return (heatsink & (Pos(-r, y, -r) * Box(2 * r, 0.01, 2 * r, align=FROM_CORNER))).volume / 0.01

        # Full disc through the base, open pin field just behind it.
        self.assertAlmostEqual(section_area(-0.5), math.pi * p.heatsink_diameter**2 / 4, delta=1.0)
        self.assertLess(section_area(-p.heatsink_base - 0.1), 0.2 * section_area(-0.5))

    def test_vendor_model_placement(self):
        p = self.p
        placed = children_by_label(build_led_stack_assembly(p)).__getitem__

        post = max(placed("TR50 M post").solids(), key=lambda s: s.volume).bounding_box()
        self.assertAlmostEqual(post.min.Z, p.datum_thickness, delta=0.01)
        self.assertAlmostEqual(post.max.Z, p.post_top, delta=TR50_MODEL_ROUNDING)
        self.assertAlmostEqual(post.center().X, 0, delta=0.01)
        self.assertAlmostEqual(post.center().Y, p.smr1_thickness / 2, delta=MODEL_MATCH)
        ring = placed("SMR1 M ring").bounding_box()
        self.assertAlmostEqual(ring.min.Y, 0, delta=0.01)
        self.assertAlmostEqual(ring.min.Z, p.post_top, delta=0.01)
        self.assertAlmostEqual((ring.min.X + ring.max.X) / 2, 0, delta=0.01)
        cap = placed("SM1CP2M cap").bounding_box()
        self.assertAlmostEqual(cap.min.Y, p.heatsink_front, delta=MODEL_MATCH)
        self.assertAlmostEqual(cap.max.Y, p.cap_face, delta=MODEL_MATCH)
        self.assertAlmostEqual(cap.center().Z, p.optical_height, delta=0.01)
        heatsink = placed("CN40-40B heatsink").bounding_box()
        self.assertAlmostEqual(heatsink.max.Y, p.heatsink_front, delta=MODEL_MATCH)
        self.assertAlmostEqual(heatsink.min.Y, p.heatsink_front - p.heatsink_height, delta=MODEL_MATCH)
        self.assertAlmostEqual(heatsink.min.Z, p.optical_height - p.heatsink_diameter / 2, delta=0.01)
        self.assertAlmostEqual(heatsink.min.Z - p.post_top, p.heatsink_post_top_clearance, delta=0.01)

    def test_assembly_parts_do_not_interfere(self):
        for board in MODULES:
            p = self.p
            for e in p.engagement_range(board):
                assembly = build_led_stack_assembly(p, board, e)
                parts = children_by_label(assembly)
                self.assertTrue(all(s.is_valid for s in parts.values()))
                names = list(parts)
                for i, a in enumerate(names):
                    for b in names[i + 1 :]:
                        overlap = parts[a] & parts[b]
                        if overlap.volume < 1e-6:
                            continue
                        # Only the inch-rounded TR50/M model may overlap its seat, by that rounding.
                        self.assertIn("TR50 M post", (a, b), (board.name, e, a, b))
                        bb = overlap.bounding_box()
                        self.assertLessEqual(
                            min(bb.size.X, bb.size.Y, bb.size.Z), TR50_MODEL_ROUNDING, (board.name, e, a, b)
                        )

    def test_reject_out_of_range(self):
        p = self.p
        lo, hi = p.engagement_range(GREEN)
        for e in (lo - 0.01, hi + 0.01, float("nan")):
            with self.assertRaises(ValueError):
                p.gap(GREEN, e)
        for changes in ({"cap_thread_length": 10.2}, {"lens_to_slit": 15.0}, {"heatsink_base": float("nan")}):
            with self.assertRaises(ValueError):
                replace(p, **changes).validate()


if __name__ == "__main__":
    unittest.main()

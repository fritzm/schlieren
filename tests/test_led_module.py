"""Threaded LED module focus range, fit, and clearance invariants."""

import unittest
from dataclasses import replace

from schlieren.parts.led_module import GREEN, MODULES, WHITE, LEDStackParameters, build_led_stack_assembly

USEFUL_GAP = (13.0, 17.0)  # §7: useful emitter-to-plano range
FOCUS_MARGIN = 1.0  # Required gap travel either side of the optimum


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

    def test_assembly_envelopes_do_not_interfere(self):
        for board in MODULES:
            p = self.p
            for e in p.engagement_range(board):
                assembly = build_led_stack_assembly(p, board, e)
                parts = {n: o.obj.val() for n, o in assembly.objects.items() if o.obj is not None}
                self.assertTrue(all(s.isValid() for s in parts.values()))
                names = list(parts)
                for i, a in enumerate(names):
                    for b in names[i + 1 :]:
                        self.assertLess(parts[a].intersect(parts[b]).Volume(), 1e-6, (board.name, e, a, b))

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

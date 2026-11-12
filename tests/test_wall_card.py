"""Wall fiducial cards: sheet and mark geometry, and that the SVG and PDF outputs are true scale."""

import re
import unittest
import xml.etree.ElementTree as ET

from schlieren.parts.wall_card import (
    CARDS,
    LETTER,
    PT_PER_MM,
    SQUARE_250,
    Circle,
    marks,
    to_annotated_svg,
    to_pdf,
    to_svg,
)
from schlieren.testing import svg_attr


class WallCardTests(unittest.TestCase):
    def test_letter_sheet_and_marks(self):
        self.assertAlmostEqual(LETTER.width, 279.4)
        self.assertAlmostEqual(LETTER.height, 215.9)
        self.assertEqual(len(LETTER.mark_centres()), 8)
        self.assertNotIn((LETTER.width / 2, LETTER.height / 2), LETTER.mark_centres())
        xs, ys = LETTER.mark_xs(), LETTER.mark_ys()
        self.assertAlmostEqual(xs[2] - xs[0], 239.4)
        self.assertAlmostEqual(ys[2] - ys[0], 175.9)

    def test_square_card_marks_are_symmetric(self):
        xs = SQUARE_250.mark_xs()
        self.assertEqual(xs, SQUARE_250.mark_ys())
        self.assertEqual((xs[0], xs[2] - xs[0]), (15, 220))

    def test_one_ring_on_top_left_mark(self):
        for p in CARDS.values():
            rings = [m for m in marks(p) if isinstance(m, Circle)]
            self.assertEqual([(r.cx, r.cy) for r in rings], [(p.inset, p.inset)])

    def test_svg_is_true_scale(self):
        for p in CARDS.values():
            root = ET.fromstring(to_svg(p))
            self.assertEqual(svg_attr(root, "width"), f"{p.width:g}mm")
            self.assertEqual(svg_attr(root, "viewBox").split()[2:], [f"{p.width:g}", f"{p.height:g}"])
            ET.fromstring(to_annotated_svg(p))

    def test_pdf_page_is_the_sheet(self):
        for p in CARDS.values():
            pdf = to_pdf(p)
            self.assertTrue(pdf.startswith(b"%PDF-") and pdf.rstrip().endswith(b"%%EOF"))
            box = re.search(rb"/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]", pdf)
            assert box
            self.assertAlmostEqual(float(box[1]), p.width * PT_PER_MM, delta=0.01)
            self.assertAlmostEqual(float(box[2]), p.height * PT_PER_MM, delta=0.01)
            start = int(re.search(rb"startxref\n(\d+)", pdf)[1])  # ty: ignore[not-subscriptable]
            self.assertTrue(pdf[start:].startswith(b"xref"))


if __name__ == "__main__":
    unittest.main()

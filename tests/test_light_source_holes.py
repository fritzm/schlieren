"""LED module cap and heatsink hole layout: pin clearance, through-hole geometry, and the drawings."""

import math
import unittest
import xml.etree.ElementTree as ET
from dataclasses import replace
from itertools import combinations

from build123d import GeomType

from schlieren.cad import intersect, z_cylinder
from schlieren.parts.light_source import MODULES, LightSourceParameters, build_star_board
from schlieren.parts.light_source_drawing import layout_drawing_svg
from schlieren.parts.light_source_holes import HoleLayoutParameters
from schlieren.testing import svg_attr
from schlieren.vendor_cad import MCMASTER_92095A453_HEAD_DIAMETER, alpha_cn40_40b

NS = "{http://www.w3.org/2000/svg}"
M2_SCREW_LENGTH = 6.0  # McMaster 92095A453, under the head.
M2_WASHER_THICKNESS = 0.4  # McMaster 91545A410, under each screw head.
M2_MIN_CENTERING_PLAY = (
    0.3  # Shank to the notch's closed end: a 0.3 mm emitter offset moves the slit image 2 mm.
)
M2_MIN_HEAD_BEARING = 1.5  # mm², star board under the screw head.
M2_MIN_WASHER_BEARING = 8.0  # mm², star board under the washer.
M3_SCREW_LENGTH = 6.0  # §6.2, provisional.
HEATSINK_BASE = 3.0  # CN40 flat base; the M3 screws pass through it first.


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class HoleLayoutTest(unittest.TestCase):
    def setUp(self):
        self.p = HoleLayoutParameters()
        self.holes = {h.name: h for h in self.p.holes()}

    def test_layout_validates(self):
        self.p.validate()

    def test_pin_lattice_matches_the_vendor_model(self):
        """The 24 pin centers are those of the CN40-40B STEP model (pin faces split in two along its z)."""
        faces = [f for f in alpha_cn40_40b().faces() if f.geom_type == GeomType.CYLINDER]
        faces = [f for f in faces if abs((f.radius or 0.0) - self.p.pin_radius) < 0.01]
        columns: dict[float, list[float]] = {}
        for f in faces:
            c = f.center()
            columns.setdefault(round(c.X, 2), []).append(round(c.Z, 2))
        model = set()
        for x, zs in columns.items():
            zs.sort()
            for lo, hi in zip(zs[0::2], zs[1::2], strict=True):
                model.add((x, round((lo + hi) / 2, 2)))
        self.assertEqual(len(model), 24)
        self.assertEqual(model, {(round(x, 2), round(y, 2)) for x, y in self.p.pin_positions()})

    def test_hole_counts_and_symmetry(self):
        kinds = [h.kind for h in self.p.holes()]
        self.assertEqual((kinds.count("m3"), kinds.count("m2"), kinds.count("lead")), (3, 2, 2))
        m2 = [self.holes["m2-1"], self.holes["m2-2"]]
        self.assertAlmostEqual(m2[0].x, -m2[1].x)
        self.assertAlmostEqual(m2[0].y, m2[1].y)
        leads = [self.holes["lead-1"], self.holes["lead-2"]]
        self.assertAlmostEqual(leads[0].y, -leads[1].y)
        self.assertAlmostEqual(leads[0].x, 0.0)

    def test_m3_heads_sit_between_four_pins(self):
        """Each M3 hole is the center of a lattice cell: four pins at 3.45·√2, and no other pin under the
        head."""
        cell_diagonal = self.p.lattice_pitch / math.sqrt(2)
        for hole in (h for h in self.p.holes() if h.kind == "m3"):
            distances = sorted(distance(hole.position, pin) for pin in self.p.pin_positions())
            for d in distances[:4]:
                self.assertAlmostEqual(d, cell_diagonal)
            self.assertGreater(distances[4], distances[3] + 1.0)
            self.assertGreater(distances[0] - self.p.pin_radius, self.p.m3_head_diameter / 2)

    def test_lead_holes_pass_between_pin_columns(self):
        for hole in (h for h in self.p.holes() if h.kind == "lead"):
            nearest = min(distance(hole.position, pin) - self.p.pin_radius for pin in self.p.pin_positions())
            self.assertGreaterEqual(nearest - self.p.lead_hole_diameter / 2, self.p.min_pin_gap)

    def test_clearances_meet_minimums(self):
        gaps = self.p.clearances()
        self.assertGreaterEqual(gaps["cap_wall"], self.p.min_wall)
        self.assertGreaterEqual(gaps["lead_to_pin"], self.p.min_pin_gap)
        self.assertGreaterEqual(gaps["head_to_pin"], self.p.min_head_gap)
        self.assertGreaterEqual(gaps["lead_to_relief"], self.p.min_relief_wall)
        self.assertGreaterEqual(gaps["lead_to_star_edge"], -1e-9)

    def test_holes_do_not_overlap_in_the_cap(self):
        for a, b in combinations(self.p.holes(), 2):
            wall = (
                distance(a.position, b.position)
                - self.p.keep_out_radius(a.kind)
                - self.p.keep_out_radius(b.kind)
            )
            self.assertGreater(wall, 0, (a.name, b.name))

    def test_m2_screws_sit_inboard_of_the_notch_centers(self):
        """The screws are on a corner's axis, closer in than the notch arcs' centers."""
        for name in ("m2-1", "m2-2"):
            self.assertAlmostEqual(math.hypot(*self.holes[name].position), self.p.m2_radius)
            self.assertAlmostEqual(self.holes[name].y, 0.0)
        self.assertLess(self.p.m2_radius, self.p.notch_center_radius)

    def test_m2_shank_keeps_centering_play_in_the_notch(self):
        for board in MODULES:
            play = self.p.m2_radius - self.p.m2_thread_major / 2 - board.notch_end_radius
            self.assertGreaterEqual(play, M2_MIN_CENTERING_PLAY, board.name)

    def test_m2_head_and_washer_bear_on_the_board(self):
        for board in MODULES:
            star = build_star_board(board)
            for diameter, minimum in (
                (MCMASTER_92095A453_HEAD_DIAMETER, M2_MIN_HEAD_BEARING),
                (self.p.m2_washer_diameter, M2_MIN_WASHER_BEARING),
            ):
                disc = z_cylinder(diameter, self.p.m2_radius, 0, -1, board.thickness + 1)
                self.assertGreaterEqual(intersect(star, disc).volume / board.thickness, minimum, board.name)

    def test_leads_sit_just_outside_the_star_flats(self):
        for name in ("lead-1", "lead-2"):
            inner_edge = abs(self.holes[name].y) - self.p.lead_hole_diameter / 2
            self.assertAlmostEqual(inner_edge, self.p.star_across_flats / 2)

    def test_screws_stay_inside_the_cap(self):
        """All holes are through holes, and no screw is long enough to reach the far face."""
        cap = LightSourceParameters().cap_overall
        for board in MODULES:
            self.assertLess(M2_SCREW_LENGTH - M2_WASHER_THICKNESS - board.thickness, cap, board.name)
        self.assertLess(M3_SCREW_LENGTH - HEATSINK_BASE, cap)

    def test_every_hole_stays_inside_the_cap_thread_relief(self):
        for hole in self.p.holes():
            self.assertLess(
                math.hypot(*hole.position) + self.p.keep_out_radius(hole.kind), self.p.cap_relief_radius
            )

    def test_tightened_lead_radius_is_rejected(self):
        with self.assertRaises(ValueError):
            replace(self.p, lead_radius=11.6).validate()

    def test_too_large_lead_hole_is_rejected(self):
        with self.assertRaises(ValueError):
            replace(self.p, lead_hole_diameter=3.0).validate()


class HoleDrawingTest(unittest.TestCase):
    def setUp(self):
        self.p = HoleLayoutParameters()

    @staticmethod
    def holes_in(svg_text):
        svg = ET.fromstring(svg_text)
        return svg, {e.get("data-hole"): e for e in svg.iter(f"{NS}circle") if e.get("data-hole")}

    def holes_by_name(self):
        return {h.name: h for h in self.p.holes()}

    def test_layout_figure_shows_every_hole_as_drilled_in_the_cap(self):
        _, holes = self.holes_in(layout_drawing_svg(self.p))
        self.assertEqual(set(holes), set(self.holes_by_name()))
        for name, hole in self.holes_by_name().items():
            self.assertAlmostEqual(float(svg_attr(holes[name], "r")) * 2, self.p.cap_hole_diameter(hole.kind))


if __name__ == "__main__":
    unittest.main()

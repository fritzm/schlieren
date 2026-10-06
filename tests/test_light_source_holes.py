"""LED module cap and heatsink hole layout: pin clearance, through-hole geometry, and the drawings."""

import math
import unittest
from dataclasses import replace
from itertools import combinations
from xml.etree import ElementTree

from build123d import GeomType

from schlieren.parts.light_source import LightSourceParameters
from schlieren.parts.light_source_drawing import drilling_templates_svg, layout_drawing_svg
from schlieren.parts.light_source_holes import HoleLayoutParameters
from schlieren.vendor_cad import alpha_cn40_40b

NS = "{http://www.w3.org/2000/svg}"
M2_SCREW_LENGTH = 5.0  # McMaster 92095A452, under the head.
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
        faces = [f for f in faces if abs(f.radius - self.p.pin_radius) < 0.01]
        columns: dict[float, list[float]] = {}
        for f in faces:
            c = f.center()
            columns.setdefault(round(c.X, 2), []).append(round(c.Z, 2))
        model = set()
        for x, zs in columns.items():
            zs.sort()
            for lo, hi in zip(zs[0::2], zs[1::2]):
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
        """Each M3 hole is the center of a lattice cell: four pins at 3.45·√2, and no other pin under the head."""
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
        self.assertGreaterEqual(gaps["lead_to_root"], self.p.min_root_wall)
        self.assertGreaterEqual(gaps["lead_to_star_edge"], -1e-9)

    def test_holes_do_not_overlap_in_the_cap(self):
        for a, b in combinations(self.p.holes(), 2):
            wall = (
                distance(a.position, b.position)
                - self.p.keep_out_radius(a.kind)
                - self.p.keep_out_radius(b.kind)
            )
            self.assertGreater(wall, 0, (a.name, b.name))

    def test_m2_screws_sit_in_star_notches(self):
        """The M2 screw center is the notch center, on a corner of the star."""
        for name in ("m2-1", "m2-2"):
            self.assertAlmostEqual(math.hypot(*self.holes[name].position), self.p.notch_center_radius)
            self.assertAlmostEqual(self.holes[name].y, 0.0)

    def test_leads_sit_just_outside_the_star_flats(self):
        for name in ("lead-1", "lead-2"):
            inner_edge = abs(self.holes[name].y) - self.p.lead_hole_diameter / 2
            self.assertAlmostEqual(inner_edge, self.p.star_across_flats / 2)

    def test_screws_stay_inside_the_cap(self):
        """All holes are through holes, and no screw is long enough to reach the far face."""
        cap = LightSourceParameters().cap_overall
        self.assertLess(M2_SCREW_LENGTH, cap)
        self.assertLess(M3_SCREW_LENGTH - HEATSINK_BASE, cap)

    def test_every_hole_stays_inside_the_cap_thread_root(self):
        for hole in self.p.holes():
            self.assertLess(
                math.hypot(*hole.position) + self.p.keep_out_radius(hole.kind), self.p.cap_thread_root_radius
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
        svg = ElementTree.fromstring(svg_text)
        return svg, {e.get("data-hole"): e for e in svg.iter(f"{NS}circle") if e.get("data-hole")}

    def test_templates_are_full_scale_letter(self):
        svg, _ = self.holes_in(drilling_templates_svg(self.p))
        _, _, width, height = (float(v) for v in svg.get("viewBox").split())
        self.assertEqual(svg.get("width"), f"{width}mm")  # One user unit is 1 mm.
        self.assertEqual(svg.get("height"), f"{height}mm")
        self.assertAlmostEqual(width, 215.9)
        self.assertAlmostEqual(height, 279.4)

    def test_template_holes_are_those_of_the_layout_in_both_templates(self):
        """Cap holes (all seven) and heatsink holes (no M2) sit at the layout positions, relative to each center."""
        svg, _ = self.holes_in(drilling_templates_svg(self.p))
        by_name: dict[str, list[ElementTree.Element]] = {}
        for e in svg.iter(f"{NS}circle"):
            if e.get("data-hole"):
                by_name.setdefault(e.get("data-hole"), []).append(e)
        for hole in self.p.holes():
            circles = by_name[hole.name]
            self.assertEqual(len(circles), 2 if hole.kind != "m2" else 1, hole.name)
            circles.sort(key=lambda e: float(e.get("cx")))  # cap template is the left one
            for e, diameter in zip(
                circles,
                [self.p.cap_hole_diameter(hole.kind), self.p.heatsink_hole_diameter(hole.kind)],
            ):
                self.assertAlmostEqual(float(e.get("r")) * 2, diameter)
        cap = {n: c[0] for n, c in by_name.items()}
        centers = {n: (float(c.get("cx")), float(c.get("cy"))) for n, c in cap.items()}
        origin_x = centers["m3-1"][0] - self.holes_by_name()["m3-1"].x
        origin_y = centers["m3-1"][1] + self.holes_by_name()["m3-1"].y
        for name, (cx, cy) in centers.items():
            hole = self.holes_by_name()[name]
            self.assertAlmostEqual(cx - origin_x, hole.x, places=2)
            self.assertAlmostEqual(origin_y - cy, hole.y, places=2)

    def holes_by_name(self):
        return {h.name: h for h in self.p.holes()}

    def test_templates_state_through_holes_and_plug_taps(self):
        text = " ".join(
            e.text or "" for e in ElementTree.fromstring(drilling_templates_svg(self.p)).iter(f"{NS}text")
        )
        self.assertIn("THROUGH", text)
        self.assertIn("plug taps", text)

    def test_layout_figure_shows_every_hole_as_drilled_in_the_cap(self):
        _, holes = self.holes_in(layout_drawing_svg(self.p))
        self.assertEqual(set(holes), set(self.holes_by_name()))
        for name, hole in self.holes_by_name().items():
            self.assertAlmostEqual(float(holes[name].get("r")) * 2, self.p.cap_hole_diameter(hole.kind))


if __name__ == "__main__":
    unittest.main()

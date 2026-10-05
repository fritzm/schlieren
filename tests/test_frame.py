"""Engineering invariants for the tabletop frame (design §4)."""

import unittest
from dataclasses import replace
from itertools import combinations
from math import degrees, pi
from xml.etree import ElementTree

from schlieren.cad import children_by_label, leaves
from schlieren.parts.frame import (
    SIDES,
    FrameParameters,
    build_foot_block,
    build_frame_assembly,
    build_pivot_plate,
)
from schlieren.parts.frame_drawing import pivot_plate_drawing_svg
from schlieren.vendor_cad import (
    MCMASTER_8215K2_DIAMETER,
    MCMASTER_8215K2_HEIGHT,
    MCMASTER_92815A202_DIAMETER,
    MCMASTER_92815A202_HEIGHT,
    vendor_step,
)

MAX_YAW = 3.0  # deg from nominal; the adjustment range §4.2 sizes the fixed yaw holes for.
# mm^3. The foot-screw tips graze the slot-floor taper of the rail model, whose taper is nominal, not measured.
INTERFERENCE_TOLERANCE = 1e-3


def boxes_overlap(a, b):
    return all(
        getattr(a.min, axis) < getattr(b.max, axis) and getattr(b.min, axis) < getattr(a.max, axis)
        for axis in "XYZ"
    )


class FrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = FrameParameters()
        cls.frame = build_frame_assembly(cls.p)
        cls.groups = children_by_label(cls.frame)
        cls.fixed = children_by_label(cls.groups["Pivot plate assembly"])

    def rail_parts(self, frame, name):
        return children_by_label(children_by_label(frame)[f"{name} rail assembly"])

    def assert_point(self, actual, expected):
        for a, e in zip(actual, expected):
            self.assertAlmostEqual(a, e, delta=0.005)

    def test_half_angle_and_hole_layout_match_design(self):
        p = self.p
        self.assertAlmostEqual(degrees(p.half_angle), 0.850, places=3)
        # Pivot frame: +y toward the mirror from the aft edge, so the pivots are forward of the straps.
        self.assert_point(p.strap_center(-1), (-48.84, 35.01))
        self.assert_point(p.strap_center(1), (48.84, 35.01))
        expected = {
            "Left pivot": (-47.50, 125.00),
            "Right pivot": (47.50, 125.00),
            "Left outer yaw": (-68.83, 35.31),
            "Left inner yaw": (-28.84, 34.71),
            "Right inner yaw": (28.84, 34.71),
            "Right outer yaw": (68.83, 35.31),
        }
        holes = p.plate_holes()
        self.assertEqual(set(holes), set(expected))
        for name, center in expected.items():
            with self.subTest(hole=name):
                self.assert_point(holes[name], center)

    def test_pivot_plate_envelope_and_six_holes(self):
        p = self.p
        plate = build_pivot_plate(p)
        self.assertEqual(len(plate.solids()), 1)
        box = plate.bounding_box()
        for actual, expected in (
            (box.min.X, -90.0),
            (box.max.X, 90.0),
            (box.min.Y, 0.0),
            (box.max.Y, 150.0),
            (box.min.Z, -32.7),
            (box.max.Z, -20.0),
        ):
            self.assertAlmostEqual(actual, expected, places=5)
        mid = (p.plate_top + p.plate_bottom) / 2
        for name, (x, y) in p.plate_holes().items():
            with self.subTest(hole=name):
                self.assertFalse(plate.is_inside((x + p.m5_clearance_diameter / 2 - 0.05, y, mid)))
                self.assertTrue(plate.is_inside((x + p.m5_clearance_diameter / 2 + 0.05, y, mid)))
        solid = p.plate_width * p.plate_depth * p.plywood_thickness
        hole = pi * (p.m5_clearance_diameter / 2) ** 2 * p.plywood_thickness
        self.assertAlmostEqual(plate.volume, solid - 6 * hole, delta=0.01)

    def test_foot_block_envelope_and_screw_holes(self):
        p = self.p
        block = build_foot_block(p)
        box = block.bounding_box()
        self.assertAlmostEqual(box.size.X, 50.0, places=5)
        self.assertAlmostEqual(box.size.Y, 75.0, places=5)
        self.assertAlmostEqual(box.size.Z, 12.7, places=5)
        for y in (-25.0, 25.0):
            self.assertFalse(block.is_inside((0, y, -p.plywood_thickness / 2)))
        self.assertTrue(block.is_inside((0, 0, -p.plywood_thickness / 2)))
        # Each screw center is 12.5 mm from its nearest block end.
        self.assertAlmostEqual(p.foot_block_length / 2 - p.foot_screw_spacing / 2, 12.5)

    def test_rails_are_400_mm_with_tops_on_the_datum(self):
        for name in SIDES:
            with self.subTest(rail=name):
                rail = self.rail_parts(self.frame, name)["Rail"]
                self.assertAlmostEqual(rail.bounding_box().max.Z, 0.0, places=5)
                self.assertAlmostEqual(rail.bounding_box().min.Z, -20.0, places=5)
                section = self.p.rail_profile()
                self.assertGreater(rail.volume, 0.3 * section.size**2 * self.p.rail_length)
                self.assertGreater(rail.bounding_box().size.Y, 399.9)

    def test_rails_diverge_aft_and_frame_is_mirror_symmetric(self):
        left = self.rail_parts(self.frame, "Left")
        right = self.rail_parts(self.frame, "Right")
        for label in ("Rail", "Pivot lug", "Foot block", "Foot"):
            with self.subTest(part=label):
                a, b = left[label].center(), right[label].center()
                self.assertAlmostEqual(a.X, -b.X, places=4)
                self.assertAlmostEqual(a.Y, b.Y, places=4)
                self.assertAlmostEqual(a.Z, b.Z, places=4)
        foot_x = right["Foot"].center().X
        self.assertGreater(foot_x, self.p.pivot_separation / 2)
        # The foot follows the chief ray aft from the pivot, against the rail's +y.
        dx, dy = self.p.rail_direction(1)
        self.assertGreater(dy, 0.0)
        self.assertAlmostEqual(foot_x, 47.5 - self.p.foot_block_center * dx, places=4)
        self.assertLess(right["Foot"].center().Y, 0.0)  # Aft of the plate.

    def test_three_feet_stand_on_one_plane_below_everything(self):
        p = self.p
        feet = [self.fixed["Front foot"]] + [self.rail_parts(self.frame, name)["Foot"] for name in SIDES]
        for foot in feet:
            self.assertAlmostEqual(foot.bounding_box().min.Z, p.table, places=5)
        front = feet[0].center()
        self.assertAlmostEqual(front.X, 0.0, places=5)
        self.assertAlmostEqual(front.Y, p.plate_depth - p.pivot_setback, places=5)
        lowest_other = min(
            part.bounding_box().min.Z for part in leaves(self.frame) if not part.label.endswith("oot")
        )
        self.assertGreater(lowest_other - p.table, 5.0)

    def test_rear_foot_sits_between_its_screws_under_the_rail(self):
        for name in SIDES:
            parts = self.rail_parts(self.frame, name)
            foot, block = parts["Foot"], parts["Foot block"]
            self.assertAlmostEqual(foot.center().X, block.center().X, places=4)
            self.assertAlmostEqual(foot.center().Y, block.center().Y, places=4)
            self.assertAlmostEqual(foot.center().X, parts["Rail"].center().X, delta=3.0)
            washers = [part for label, part in parts.items() if "washer" in label]
            self.assertEqual(len(washers), 4)  # Two under each of the two screw heads.
            for washer in washers:
                self.assertGreater(foot.distance_to(washer), 1.0)

    def test_screw_stacks_have_thread_to_spare(self):
        p = self.p
        self.assertGreater(p.pivot_screw_protrusion, 0)
        self.assertGreater(p.yaw_screw_length_above_strap_washer, MCMASTER_92815A202_HEIGHT)
        self.assertGreater(p.foot_screw_slot_entry, p.rail_slot_lip_thickness)
        self.assertAlmostEqual(p.foot_screw_slot_entry, 5.3)
        self.assertAlmostEqual(p.foot_screw_slot_margin, 1.15)
        with self.assertRaises(ValueError):
            replace(p, foot_washers_per_screw=0).validate()
        with self.assertRaises(ValueError):
            replace(p, foot_screw_length=25.0).validate()

    def test_pivot_lug_end_hole_is_on_the_pivot_axis_at_any_yaw(self):
        p = self.p
        for yaw in (-MAX_YAW, 0.0, MAX_YAW):
            frame = build_frame_assembly(p, left_yaw=yaw, right_yaw=yaw)
            for name, side in SIDES.items():
                with self.subTest(yaw=yaw, rail=name):
                    lug = self.rail_parts(frame, name)["Pivot lug"]
                    x, y = p.pivot_center(side)
                    z = p.joining_plate_thickness / 2
                    self.assertFalse(lug.is_inside((x, y, z)))
                    self.assertTrue(lug.is_inside((x + p.m5_clearance_diameter / 2 + 0.5, y, z)))
                    self.assertAlmostEqual(lug.bounding_box().min.Z, 0.0, places=5)

    def test_yaw_bolt_clearance_to_rail(self):
        p = self.p
        nominal = min(
            self.rail_parts(self.frame, name)["Rail"].distance_to(self.fixed[f"{name} {where} yaw screw"])
            for name in SIDES
            for where in ("inner", "outer")
        )
        self.assertAlmostEqual(nominal, 7.5, delta=0.01)
        for yaw in (-MAX_YAW, MAX_YAW):
            frame = build_frame_assembly(p, left_yaw=yaw, right_yaw=yaw)
            closest = min(
                self.rail_parts(frame, name)["Rail"].distance_to(self.fixed[f"{name} {where} yaw screw"])
                for name in SIDES
                for where in ("inner", "outer")
            )
            with self.subTest(yaw=yaw):
                self.assertAlmostEqual(closest, 2.8, delta=0.1)

    def test_no_part_interference_across_the_yaw_range(self):
        for yaw in (-MAX_YAW, 0.0, MAX_YAW):
            parts = leaves(build_frame_assembly(self.p, left_yaw=yaw, right_yaw=yaw))
            boxes = [part.bounding_box() for part in parts]
            for (a, box_a), (b, box_b) in combinations(zip(parts, boxes), 2):
                if boxes_overlap(box_a, box_b):
                    with self.subTest(yaw=yaw, pair=(a.label, b.label)):
                        self.assertLess((a & b).volume, INTERFERENCE_TOLERANCE)

    def test_thumb_nuts_are_vendor_models_seated_on_the_strap_washers(self):
        p = self.p
        model = vendor_step("McMaster-92815A202.step").bounding_box()
        self.assertAlmostEqual(model.size.Z, MCMASTER_92815A202_HEIGHT, places=3)
        self.assertAlmostEqual(model.size.X, MCMASTER_92815A202_DIAMETER, places=3)
        for label, (x, y) in p.plate_holes().items():
            if not label.endswith("yaw"):
                continue
            with self.subTest(nut=label):
                box = self.fixed[f"{label} nut"].bounding_box()
                self.assertAlmostEqual(box.min.Z, p.strap_top + p.oversize_washer_thickness, places=4)
                self.assertAlmostEqual(box.size.Z, MCMASTER_92815A202_HEIGHT, places=3)
                self.assertAlmostEqual(box.center().X, x, delta=0.01)
                self.assertAlmostEqual(box.center().Y, y, delta=0.01)
                # The screw reaches through the nut.
                self.assertGreater(self.fixed[f"{label} screw"].bounding_box().max.Z, box.max.Z)

    def test_feet_are_vendor_models_stuck_to_the_plywood(self):
        p = self.p
        model = vendor_step("McMaster-8215K2.step").bounding_box()
        self.assertAlmostEqual(model.size.Y, MCMASTER_8215K2_HEIGHT, places=3)
        self.assertAlmostEqual(model.size.X, MCMASTER_8215K2_DIAMETER, places=3)
        feet = [self.fixed["Front foot"]] + [self.rail_parts(self.frame, name)["Foot"] for name in SIDES]
        for foot in feet:
            box = foot.bounding_box()
            self.assertAlmostEqual(box.max.Z, p.plate_bottom, places=4)  # Adhesive face on the plywood.
            self.assertAlmostEqual(box.size.Z, MCMASTER_8215K2_HEIGHT, places=3)
            self.assertAlmostEqual(box.size.X, MCMASTER_8215K2_DIAMETER, delta=0.05)

    def test_drilling_drawing_is_full_scale_with_holes_dimensioned_from_the_edges(self):
        p = self.p
        svg = ElementTree.fromstring(pivot_plate_drawing_svg(p))
        ns = "{http://www.w3.org/2000/svg}"
        _, _, width, height = (float(v) for v in svg.get("viewBox").split())
        self.assertEqual(svg.get("width"), f"{width}mm")  # One user unit is 1 mm.
        self.assertEqual(svg.get("height"), f"{height}mm")
        outline = next(e for e in svg.iter(f"{ns}rect") if e.get("class") == "outline")
        self.assertEqual((float(outline.get("width")), float(outline.get("height"))), (180.0, 150.0))
        left, top = float(outline.get("x")), float(outline.get("y"))
        circles = {e.get("data-hole"): e for e in svg.iter(f"{ns}circle") if e.get("data-hole")}
        self.assertEqual(set(circles), set(p.plate_holes()))
        for name, (x, y) in p.plate_holes().items():
            with self.subTest(hole=name):
                circle = circles[name]
                # Seen from above with the mirror ahead: +x to the right, +y up the sheet.
                self.assertAlmostEqual(float(circle.get("cx")) - left, x + 90.0, places=3)
                self.assertAlmostEqual(top + 150.0 - float(circle.get("cy")), y, places=3)
                self.assertAlmostEqual(float(circle.get("r")), 2.75, places=3)
        figures = [e.text for e in svg.iter(f"{ns}text")]
        # x from the plate centerline, y from the aft edge, as in §4.2.
        x_figures = ("-90.0", "-68.8", "-47.5", "-28.8", "0 CL", "+28.8", "+47.5", "+68.8", "+90.0")
        for expected in (*x_figures, "0.0", "35.3", "125.0", "150.0"):
            self.assertIn(expected, figures)
        self.assertTrue(any("34.7" in figure for figure in figures))

    def test_assembly_groups(self):
        self.assertEqual(
            list(self.groups), ["Pivot plate assembly", "Left rail assembly", "Right rail assembly"]
        )
        straps = [label for label in self.fixed if label.endswith("yaw strap")]
        self.assertEqual(straps, ["Left yaw strap", "Right yaw strap"])
        self.assertEqual(sum(label.endswith("yaw screw") for label in self.fixed), 4)
        self.assertEqual(sum(label.endswith("pivot screw") for label in self.fixed), 2)


if __name__ == "__main__":
    unittest.main()

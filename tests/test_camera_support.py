"""Engineering invariants for the lens pointer and phone rest concept mock-up (design §§9.4-9.7)."""

import unittest
from itertools import combinations

from build123d import Vector

from schlieren.cad import leaves
from schlieren.parts.camera_support import (
    CameraSupportParameters,
    build_camera_support_assembly,
    build_lens_pointer,
    build_phone_rest,
)
from schlieren.vendor_cad import MCMASTER_94459A797_FLANGE_DIAMETER, MCMASTER_94459A797_LENGTH, vendor_step

CONTACT = 1e-3  # mm
ADJUSTERS = tuple(f"{where} {side}" for where in ("Aft", "Fore") for side in ("left", "right"))
MAGNET_PADS = ("Fore left", "Fore right", "Aft right")  # The aft left screw sits in the rod groove.


class LensPointerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = CameraSupportParameters()
        cls.assembly = build_camera_support_assembly(cls.p)
        cls.parts = {part.label: part for part in leaves(cls.assembly)}

    def test_lens_sections_are_the_measured_values(self):
        p = self.p
        self.assertAlmostEqual(p.aft_stub_length, 14.351, places=3)
        self.assertAlmostEqual(p.rear_section_length, 33.02, places=3)
        self.assertAlmostEqual(p.long_section_length, 57.15, places=3)
        self.assertAlmostEqual(p.lens_length, 120.523, places=3)

    def test_collars_sit_on_the_clampable_barrel_clear_of_the_focus_ring(self):
        p = self.p
        rear_end = p.aft_stub_length + p.rear_section_length
        aft = self.parts["Aft collar"].bounding_box()
        fore = self.parts["Fore collar"].bounding_box()
        self.assertGreaterEqual(aft.min.Y, p.aft_stub_length)
        self.assertLessEqual(aft.max.Y, rear_end)
        self.assertGreaterEqual(fore.min.Y, rear_end)
        self.assertGreaterEqual(p.focus_ring_start - fore.max.Y, 1.5)
        self.assertGreater(p.fore_station - p.aft_station, 70.0)

    def test_lens_and_main_camera_are_on_the_optical_axis(self):
        p = self.p
        lens = self.parts["Telephoto envelope"].bounding_box()
        self.assertAlmostEqual((lens.min.Z + lens.max.Z) / 2, 72.35, places=4)
        self.assertAlmostEqual((lens.min.X + lens.max.X) / 2, 0.0, places=4)
        phone = self.parts["Phone envelope"].bounding_box()
        self.assertAlmostEqual(72.35 - phone.min.Z, 60.6, places=4)  # Measured, §9.1.
        self.assertAlmostEqual(-phone.min.X, 34.3, places=4)  # Measured, §9.1.
        self.assertGreater(phone.max.X, -phone.min.X)  # The body hangs outboard, toward +x.
        self.assertLessEqual(phone.max.Y, lens.min.Y + CONTACT)  # Lens ahead of the phone back.
        self.assertAlmostEqual(p.phone_length, 155.15, places=2)

    def test_each_screw_tip_bears_on_its_pad_or_the_groove(self):
        for station in MAGNET_PADS:
            screw, pad = self.parts[f"{station} screw"], self.parts[f"{station} magnet"]
            with self.subTest(pad=station):
                self.assertLess(screw.distance_to(pad), CONTACT)
                self.assertLess((screw & pad).volume, CONTACT)
        self.assertNotIn("Aft left magnet", self.parts)
        screw = self.parts["Aft left screw"]
        for rod in ("Groove rod -1", "Groove rod +1"):
            with self.subTest(rod=rod):
                self.assertLess(screw.distance_to(self.parts[rod]), CONTACT)
                self.assertLess((screw & self.parts[rod]).volume, CONTACT)

    def test_screws_are_at_right_angles_through_the_lens_axis(self):
        p = self.p
        self.assertEqual(p.screw_angle, 45.0)
        for station in MAGNET_PADS:
            center = self.parts[f"{station} magnet"].center()
            # Pads are tangent to a circle about the axis: equal offsets across and below it.
            with self.subTest(pad=station):
                self.assertAlmostEqual(abs(center.X), 72.35 - center.Z, places=3)
        # Pads lie with their long side across the rail, the direction they slide most.
        self.assertAlmostEqual(self.parts["Fore left magnet"].bounding_box().size.Y, p.magnet_width, places=4)

    def test_four_adjusters_with_inserts_inside_the_yoke_bosses(self):
        p = self.p
        model = vendor_step("McMaster-94459A797.step").bounding_box()
        self.assertAlmostEqual(model.size.Y, MCMASTER_94459A797_LENGTH, places=3)
        self.assertAlmostEqual(model.size.X, MCMASTER_94459A797_FLANGE_DIAMETER, places=3)
        self.assertGreaterEqual(p.yoke_boss_length, MCMASTER_94459A797_LENGTH)
        pointer = self.parts["Lens pointer"]
        # The thumb nut stays clear above the insert flange over the screw's travel.
        self.assertGreaterEqual(p.boss_top_below_tip - p.nut_below_tip - 5.0, 4.0)
        for name in ADJUSTERS:
            insert, nut = self.parts[f"{name} insert"], self.parts[f"{name} thumb nut"]
            side = -1 if name.endswith("left") else 1
            toward_axis = Vector(-side, 0, 1).normalized()
            center = insert.center()
            with self.subTest(adjuster=name):
                # The insert lies along the screw axis, buried in its boss from the lens-side face.
                box = insert.bounding_box()
                along = max(box.size.X, box.size.Z)
                self.assertGreater(along, MCMASTER_94459A797_FLANGE_DIAMETER)  # Inclined, not axis-aligned.
                for offset in (-0.4, 0.0, 0.4):
                    point = center + toward_axis * (offset * MCMASTER_94459A797_LENGTH)
                    self.assertTrue(pointer.is_inside(point))
                self.assertFalse(pointer.is_inside(center + toward_axis * MCMASTER_94459A797_LENGTH))
                self.assertGreater(nut.distance_to(pointer), 4.0)
        for kind in ("insert", "thumb nut", "screw"):
            self.assertEqual(sum(label == f"{name} {kind}" for name in ADJUSTERS for label in self.parts), 4)

    def test_phone_lower_edge_rests_on_the_rod(self):
        p = self.p
        rod = self.parts["Rest rod"].bounding_box()
        phone = self.parts["Phone envelope"].bounding_box()
        self.assertAlmostEqual(rod.max.Z, phone.min.Z, places=4)
        self.assertGreater(rod.min.X, 60.0)  # Well outboard of the lens axis.
        self.assertLess(rod.max.X, phone.max.X)
        self.assertLess(rod.min.Y, phone.min.Y)  # The rod spans the phone's thickness, along the rail.
        self.assertGreater(rod.max.Y, phone.max.Y)
        self.assertAlmostEqual(phone.min.Z, 11.75, places=4)
        self.assertAlmostEqual(p.rest_x, 100.0)

    def test_pointer_and_rest_are_separate_single_parts(self):
        pointer, rest = build_lens_pointer(self.p), build_phone_rest(self.p)
        self.assertEqual(len(pointer.solids()), 1)
        self.assertEqual(len(rest.solids()), 1)
        self.assertGreater(pointer.distance_to(rest), 1.0)
        # Each straddles the rail: nothing of either lies inside the rail section.
        for part in (pointer, rest):
            self.assertFalse(part.is_inside((0, part.center().Y, -10)))

    def test_parts_clear_each_other_and_the_cutoff_station(self):
        own = {part.label for part in leaves(build_camera_support_assembly(self.p, include_cutoff=False))}
        printed = ("Lens pointer", "Phone rest", "Aft collar", "Fore collar")
        let_in = (" screw", " magnet", " rod")  # Threaded into, or let into, a printed part.
        optics = {"Telephoto envelope", "Focus ring"}
        for a, b in combinations(self.parts.values(), 2):
            labels = (a.label, b.label)
            if not own.intersection(labels) or "Optical axis" in labels or set(labels) == optics:
                continue  # The cutoff station's own fits are covered by its tests.
            if any(label.endswith(" insert") for label in labels):
                continue  # Inserts are checked in their bosses above; their knurled model is slow to intersect.
            fitted = any(word in label for label in labels for word in let_in)
            if fitted and any(label in printed for label in labels):
                continue
            box_a, box_b = a.bounding_box(), b.bounding_box()
            if any(
                getattr(box_a.min, k) >= getattr(box_b.max, k)
                or getattr(box_b.min, k) >= getattr(box_a.max, k)
                for k in "XYZ"
            ):
                continue
            with self.subTest(pair=labels):
                self.assertLess((a & b).volume, 0.01)
        gap = self.parts["Rail shoe"].bounding_box().min.Y - self.parts["Lens pointer"].bounding_box().max.Y
        self.assertGreater(gap, 5.0)

    def test_rejects_collars_off_the_clampable_barrel(self):
        from dataclasses import replace

        for bad in (
            {"aft_station": 10.0},
            {"aft_station": 45.0},
            {"fore_station": 100.0},
            {"yoke_boss_length": 6.0},
        ):
            with self.subTest(parameters=bad), self.assertRaises(ValueError):
                replace(self.p, **bad).validate()


if __name__ == "__main__":
    unittest.main()

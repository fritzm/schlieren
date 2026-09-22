"""Engineering invariants for the preliminary carriage, not print qualification."""
import unittest
from itertools import combinations
from math import cos, sin, pi, radians, tan

import cadquery as cq

from schlieren.parts.carriage import CarriageParameters, build_carriage


class CarriageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = CarriageParameters()
        cls.parts = {n: o.obj.val() for n, o in build_carriage().objects.items() if o.obj is not None}

    def test_four_valid_single_solids(self):
        self.assertEqual(len(self.parts), 4)
        for s in self.parts.values():
            self.assertTrue(s.isValid())
            self.assertEqual(len(s.Solids()), 1)
        self.assertAlmostEqual(self.parts['Base plate'].BoundingBox().xlen, 86)
        self.assertAlmostEqual(self.parts['Keeper plate'].BoundingBox().zmax, 15)

    def test_travel_and_loading_clearance(self):
        for travel, retract in ((-5, 0), (0, 0), (5, 0), (0, 6)):
            parts = dict(self.parts)
            parts['Driven plunger'] = parts['Driven plunger'].translate((0, travel, 0))
            parts['Spring plunger'] = parts['Spring plunger'].translate((0, travel - retract, 0))
            for (na, a), (nb, b) in combinations(parts.items(), 2):
                self.assertLess(a.intersect(b).Volume(), 1e-6, (travel, retract, na, nb))
            # Keeper has actual bearing overlap above both swept guide ears.
            for name in ('Driven plunger', 'Spring plunger'):
                raised = parts[name].translate((0, 0, 0.5))
                self.assertGreater(raised.intersect(parts['Keeper plate']).Volume(), 1)

    def test_optical_aperture_and_datum_tracks(self):
        p = self.p
        base = self.parts['Base plate']
        # Material just beyond the circular opening remains on both travel-axis sides.
        for y in (-p.aperture_diameter / 2 - 0.1, p.aperture_diameter / 2 + 0.1):
            self.assertTrue(base.isInside((0, y, p.plate_thickness / 2)))
        for travel in (-5, 0, 5):
            beam = cq.Workplane('XY').circle(p.aperture_diameter / 2).extrude(15).val()
            for name, part in self.parts.items():
                if 'plunger' in name:
                    part = part.translate((0, travel, 0))
                self.assertLess(part.intersect(beam).Volume(), 1e-6)
            for x, y in p.datum_points:
                self.assertLess(abs(x) + 3.18 / 2, 32)
                self.assertLess(abs(y - travel) + 3.18 / 2, 32)
                self.assertGreater((x*x + (y-travel)**2)**0.5 - 3.18 / 2, 12)
                self.assertFalse(base.isInside((x, y, 2)))

    def test_beveled_cassette_clears_printed_parts(self):
        p = self.p
        rear = p.plate_thickness + p.datum_projection
        front = rear + p.cassette_thickness
        inset = p.bevel_depth / tan(radians(p.bevel_angle))
        profile = [(-32, rear), (32, rear), (32, front - p.bevel_depth),
                   (32 - inset, front), (-32 + inset, front), (-32, front - p.bevel_depth)]
        blank = cq.Workplane('YZ', origin=(-32, 0, 0)).polyline(profile).close().extrude(64).val()
        cassette = blank.intersect(blank.rotate((0, 0, 0), (0, 0, 1), 90))
        for travel in (-5, 0, 5):
            moved = cassette.translate((0, travel, 0))
            for name, part in self.parts.items():
                if 'plunger' in name:
                    part = part.translate((0, travel, 0))
                self.assertLess(part.intersect(moved).Volume(), 1e-6, (travel, name))

    def test_hardware_stack(self):
        p = self.p
        top = p.keeper_z + p.keeper_thickness - p.screw_head_recess
        # M3 x 12 reaches the rear-opening nut with only slight projection.
        self.assertAlmostEqual(top - 12, -0.1)
        for x, y in p.fasteners:
            screw = cq.Solid.makeCylinder(1.5, 12, cq.Vector(x, y, top), cq.Vector(0, 0, -1))
            nut = cq.Workplane('XY', origin=(x, y, p.nut_pocket_depth - 2.4)).polygon(
                6, 5.5 / cos(pi / 6)).extrude(2.4).val()
            for name in ('Base plate', 'Keeper plate'):
                for hardware in (screw, nut):
                    self.assertLess(self.parts[name].intersect(hardware).Volume(), 1e-6)
        for travel in (-5, 0, 5):
            length = p.spring_fiducial_length + travel
            self.assertIn(length, (11.5, 16.5, 21.5))
            self.assertGreaterEqual(p.shoulder_length - length - p.rear_wall_thickness, 15)
        self.assertAlmostEqual(p.rear_wall_thickness, p.keeper_end_member_width)
        self.assertAlmostEqual(p.spring_seat_y, p.keeper_opening_y - p.keeper_opening_length / 2)
        self.assertAlmostEqual(p.plate_length, 127)
        self.assertAlmostEqual(self.parts['Base plate'].BoundingBox().ylen, 127)
        for start, end, diameter in p.support_spans:
            expected = p.adjuster_support_length if start > 0 else p.rear_wall_thickness
            self.assertAlmostEqual(end - start, expected)

    def test_plungers_drop_into_open_tracks(self):
        base = self.parts['Base plate']
        for name in ('Driven plunger', 'Spring plunger'):
            for lift in (0, 2, 6, 15):
                self.assertLess(base.intersect(self.parts[name].translate((0, 0, lift))).Volume(), 1e-6)

    def test_supports_reach_plate_edges_and_keeper_lifts_off(self):
        p = self.p
        base = self.parts['Base plate']
        for y in (-p.plate_length / 2 + 0.1, p.plate_length / 2 - 0.1):
            for x in (-p.plate_width / 2 + 0.1, -20, 20, p.plate_width / 2 - 0.1):
                self.assertTrue(base.isInside((x, y, p.floor_z + 1)))
        for lift in (0, 1, 3, 6):
            self.assertLess(base.intersect(self.parts['Keeper plate'].translate((0, 0, lift))).Volume(), 1e-6)
        for start, end, diameter in p.support_spans:
            bore = cq.Solid.makeCylinder(diameter / 2, end-start,
                                        cq.Vector(0, start, p.adjuster_axis_z if start > 0 else p.spring_axis_z), cq.Vector(0, 1, 0))
            for name in ('Base plate', 'Keeper plate'):
                self.assertLess(self.parts[name].intersect(bore).Volume(), 1e-6)

    def test_adjuster_block_is_integrated_with_end_member(self):
        p = self.p
        base = self.parts['Base plate']
        keeper = self.parts['Keeper plate']
        start, end, _ = p.support_spans[0]
        for y in (start + 0.1, (start + end) / 2, end - 0.1):
            self.assertTrue(base.isInside((10, y, p.keeper_z - 0.1)))
            self.assertFalse(base.isInside((10, y, p.keeper_z + 0.1)))
            self.assertTrue(keeper.isInside((10, y, p.keeper_z + 0.1)))
            # Lowering the axis now leaves a continuous roof over the insert bore.
            self.assertTrue(keeper.isInside((0, y, p.keeper_z + p.keeper_thickness - 0.1)))
        self.assertAlmostEqual(base.BoundingBox().zmax, p.keeper_z)

    def test_lowered_bodies_and_rod_axes(self):
        p = self.p
        for name, sign in (('Driven plunger', 1), ('Spring plunger', -1)):
            part = self.parts[name]
            y = sign * (p.cassette_size / 2 + p.body_length / 2)
            self.assertAlmostEqual(part.BoundingBox().zmin - p.plate_thickness, 0.3)
            self.assertTrue(part.isInside((0, y, p.plate_thickness + 0.4)))
            # Body extension must not lower the ears into their guide floors.
            self.assertFalse(part.isInside((35, y, p.floor_z)))
            self.assertTrue(part.isInside((35, y, p.floor_z + p.ear_lower_clearance + 0.1)))
        pocket_bottom = p.adjuster_axis_z - (p.magnet_width + p.magnet_fit_clearance) / 2
        self.assertGreaterEqual(pocket_bottom - (p.plate_thickness + p.body_deck_clearance), 0.6)
        roof = self.parts['Keeper plate'].BoundingBox().zmax - (p.adjuster_axis_z + p.insert_bore_diameter / 2)
        self.assertAlmostEqual(roof, p.keeper_thickness)
        self.assertAlmostEqual(p.adjuster_axis_z - p.insert_bore_diameter / 2, p.plate_thickness)
        self.assertAlmostEqual(p.spring_axis_z, 7.5)
        start, end, _ = p.support_spans[0]
        self.assertTrue(self.parts['Base plate'].isInside((0, (start + end) / 2, p.plate_thickness - 0.1)))

    def test_adjuster_crown_radial_wall(self):
        p = self.p
        keeper = self.parts['Keeper plate']
        start, end, _ = p.support_spans[0]
        inner = p.insert_bore_diameter / 2
        outer = inner + p.keeper_thickness
        for y in (start + 0.1, (start + end) / 2, end - 0.1):
            for angle in (30, 45, 60, 90, 120, 135, 150):
                a = radians(angle)
                for r in (inner + 0.05, outer - 0.05):
                    self.assertTrue(keeper.isInside((r * cos(a), y, p.adjuster_axis_z + r * sin(a))))
            self.assertFalse(keeper.isInside((0, y, p.adjuster_axis_z + outer + 0.05)))
        # Flat regions retain their original 3 mm section.
        self.assertFalse(keeper.isInside((20, (start + end) / 2,
                                         p.keeper_z + p.keeper_thickness + 0.05)))

    def test_spring_rod_pilot_relief_and_chamfer(self):
        p = self.p
        part = self.parts['Spring plunger']
        mouth_y = -p.cassette_size / 2 - p.body_length
        depth = p.shoulder_thread_depth + p.shoulder_tap_relief
        self.assertAlmostEqual(depth, 9)
        self.assertFalse(part.isInside((0, mouth_y + depth - 0.1, p.spring_axis_z)))
        self.assertTrue(part.isInside((0, mouth_y + depth + 0.1, p.spring_axis_z)))
        self.assertAlmostEqual(p.body_length - depth, 1)
        r = p.shoulder_thread_pilot / 2
        self.assertFalse(part.isInside((r - 0.05, mouth_y + 2, p.spring_axis_z)))
        self.assertTrue(part.isInside((r + 0.05, mouth_y + 2, p.spring_axis_z)))
        self.assertFalse(part.isInside((r + 0.25, mouth_y + 0.1, p.spring_axis_z)))
        self.assertTrue(part.isInside((r + 0.25, mouth_y + 0.4, p.spring_axis_z)))

    def test_unsupported_poses_rejected(self):
        for args in ({'travel': 5.1}, {'retract': 6.1}, {'travel': 1, 'retract': 1}):
            with self.assertRaises(ValueError):
                build_carriage(**args)


if __name__ == '__main__':
    unittest.main()

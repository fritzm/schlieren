"""Shape checks for the generic 2020 rail used in viewer assemblies and figures."""

import unittest

from schlieren.parts.rail import RailProfile, build_rail

LENGTH = 60.0


class RailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = RailProfile()
        cls.rail = build_rail(LENGTH, cls.f)

    def test_single_valid_solid_in_rail_assembly_frame(self):
        self.assertTrue(self.rail.is_valid)
        self.assertEqual(len(self.rail.solids()), 1)
        box = self.rail.bounding_box()
        for actual, expected in (
            (box.min.X, -self.f.size / 2),
            (box.max.X, self.f.size / 2),
            (box.min.Y, -LENGTH / 2),
            (box.max.Y, LENGTH / 2),
            (box.min.Z, -self.f.size),
            (box.max.Z, 0.0),
        ):
            self.assertAlmostEqual(actual, expected, places=5)

    def test_t_slot_on_every_face_and_center_bore(self):
        f = self.f
        center_z = -f.size / 2
        reach = f.size / 2
        just_under_lip = reach - f.lip_thickness - 0.1
        beside_mouth = (f.slot_mouth_width + f.cavity_width) / 4
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            with self.subTest(face=(dx, dz)):
                # Outward along the face normal (dx, dz); sideways along the face (dz, dx).
                def point(out, side=0.0, dx=dx, dz=dz):
                    return (dx * out + dz * side, 0, center_z + dz * out + dx * side)

                self.assertFalse(self.rail.is_inside(point(reach - 0.1)))  # Slot mouth.
                self.assertTrue(self.rail.is_inside(point(reach - 0.1, beside_mouth)))  # Lip.
                self.assertFalse(
                    self.rail.is_inside(point(just_under_lip, beside_mouth))
                )  # Cavity under lip.
                self.assertTrue(self.rail.is_inside(point(reach - f.slot_depth - 0.1)))  # Web below the slot.
        self.assertFalse(self.rail.is_inside((0, 0, center_z)))


if __name__ == "__main__":
    unittest.main()

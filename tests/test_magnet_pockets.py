"""One convention for the 10 x 5 x 2 mm magnet pockets: the same total allowance in every model."""

import unittest

from schlieren.hardware import MAGNET_LENGTH, MAGNET_WIDTH
from schlieren.parts.camera_support import CameraSupportParameters, _pad_pocket
from schlieren.parts.carriage import CarriageParameters, build_plunger
from schlieren.parts.slit_head import SlitHeadParameters, _magnet_pocket
from schlieren.standards import MAGNET_POCKET_CLEARANCE

TOLERANCE = 1e-6


class MagnetPocketTests(unittest.TestCase):
    def test_every_model_takes_the_shared_total_allowance(self):
        self.assertAlmostEqual(MAGNET_POCKET_CLEARANCE, 0.20)
        self.assertEqual(CameraSupportParameters().pad_pocket_clearance, MAGNET_POCKET_CLEARANCE)
        self.assertEqual(CarriageParameters().magnet_pocket_clearance, MAGNET_POCKET_CLEARANCE)
        self.assertEqual(SlitHeadParameters().magnet_pocket_clearance, MAGNET_POCKET_CLEARANCE)

    def test_pocket_is_the_magnet_plus_the_allowance_across_length_and_width(self):
        across, along = MAGNET_LENGTH + MAGNET_POCKET_CLEARANCE, MAGNET_WIDTH + MAGNET_POCKET_CLEARANCE
        self.assertAlmostEqual(_pad_pocket(CameraSupportParameters(), False)[0], across)
        self.assertAlmostEqual(_pad_pocket(CameraSupportParameters(), False)[1], along)
        box = _magnet_pocket(SlitHeadParameters(), 0.0, 0.0).bounding_box()
        self.assertAlmostEqual(box.size.X, across, delta=TOLERANCE)
        self.assertAlmostEqual(box.size.Y, along, delta=TOLERANCE)

    def test_carriage_pocket_walls_and_recess(self):
        p = CarriageParameters()
        plunger = build_plunger(p)
        outer_y = p.cassette_size / 2 + p.body_length
        z = p.adjuster_axis_z
        half_length = (MAGNET_LENGTH + MAGNET_POCKET_CLEARANCE) / 2
        depth_mid = outer_y - 0.5  # Inside the pocket's depth, near its mouth.
        # Across the length: the pocket wall is half the allowance beyond the magnet's end.
        self.assertFalse(plunger.is_inside((half_length - 0.01, depth_mid, z)))
        self.assertTrue(plunger.is_inside((half_length + 0.01, depth_mid, z)))
        # Down the pocket, the magnet's face sits magnet_face_recess below the outer face.
        floor_y = outer_y - (p.magnet_thickness + p.magnet_face_recess)
        self.assertFalse(plunger.is_inside((0, floor_y + 0.01, z)))
        self.assertTrue(plunger.is_inside((0, floor_y - 0.01, z)))
        self.assertAlmostEqual(p.magnet_contact_y, outer_y - p.magnet_face_recess)


if __name__ == "__main__":
    unittest.main()

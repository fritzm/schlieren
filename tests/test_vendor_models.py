"""The vendor STEP models match the catalog dimensions recorded for them in vendor_cad.

Each model's bounding-box extents are compared, sorted so that the model's own axis does not matter, with the
dimensions the part modules and placements rely on. A re-exported or substituted model file, or a mistyped
catalog constant, fails here rather than as a mysterious offset in an assembly. Some models are rounded to
thousandths of an inch, hence the tolerance.
"""

import unittest

from build123d import Box, Pos

from schlieren import vendor_cad as v
from schlieren.vendor_cad import (
    kozak_tb250_80_625,
    mcmaster_91131a028,
    vendor_step,
)

MODEL_ROUNDING = 0.03  # mm

# (STEP file, extents of the model: diameter or width, diameter or width, length or thickness).
MODELS = {
    "Kozak TS250-80-2500 screw": (
        "Kozak-TS250-80-2500.step",
        (v.KOZAK_TS250_DIAMETER, v.KOZAK_TS250_DIAMETER, v.KOZAK_TS250_LENGTH),
    ),
    "Kozak KB250-80 knob": (
        "Kozak-KB250-80.step",
        (v.KOZAK_KB250_DIAMETER, v.KOZAK_KB250_DIAMETER, v.KOZAK_KB250_LENGTH),
    ),
    "Kozak TB250-80-625 bushing": (
        "Kozak-TB250-80-625.step",
        (v.KOZAK_TB250_FLANGE_DIAMETER, v.KOZAK_TB250_FLANGE_DIAMETER, v.KOZAK_TB250_LENGTH),
    ),
    "McMaster 93339A252 ball-tip set screw": (
        "McMaster-93339A252.step",
        (v.MCMASTER_93339A252_DIAMETER, v.MCMASTER_93339A252_DIAMETER, v.MCMASTER_93339A252_LENGTH),
    ),
    "McMaster 98164A527 button-head screw": (
        "McMaster-98164A527.step",
        (
            v.MCMASTER_98164A527_HEAD_DIAMETER,
            v.MCMASTER_98164A527_HEAD_DIAMETER,
            v.MCMASTER_98164A527_LENGTH + v.MCMASTER_98164A527_HEAD_HEIGHT,
        ),
    ),
    "McMaster 96659A134 washer": (
        "McMaster-96659A134.step",
        (v.MCMASTER_96659A134_DIAMETER, v.MCMASTER_96659A134_DIAMETER, v.MCMASTER_96659A134_THICKNESS),
    ),
    "McMaster 91116A350 washer": (
        "McMaster-91116A350.step",
        (v.MCMASTER_91116A350_DIAMETER, v.MCMASTER_91116A350_DIAMETER, v.MCMASTER_91116A350_THICKNESS),
    ),
    "McMaster 93475A240 washer": (
        "McMaster-93475A240.step",
        (v.MCMASTER_93475A240_DIAMETER, v.MCMASTER_93475A240_DIAMETER, v.MCMASTER_93475A240_THICKNESS),
    ),
    "McMaster 91585A351 dowel pin": (
        "McMaster-91585A351.step",
        (v.MCMASTER_91585A351_DIAMETER, v.MCMASTER_91585A351_DIAMETER, v.MCMASTER_91585A351_LENGTH),
    ),
    "McMaster 91585A457 dowel pin": (
        "McMaster-91585A457.step",
        (v.MCMASTER_91585A457_DIAMETER, v.MCMASTER_91585A457_DIAMETER, v.MCMASTER_91585A457_LENGTH),
    ),
    "McMaster 91131A028 spherical washer pair": (
        "McMaster-91131A028.step",
        (
            v.MCMASTER_91131A028_FEMALE_DIAMETER,
            v.MCMASTER_91131A028_FEMALE_DIAMETER,
            v.MCMASTER_91131A028_HEIGHT,
        ),
    ),
    "McMaster 92815A202 thumb nut": (
        "McMaster-92815A202.step",
        (v.MCMASTER_92815A202_DIAMETER, v.MCMASTER_92815A202_DIAMETER, v.MCMASTER_92815A202_HEIGHT),
    ),
    "McMaster 8215K2 bumper": (
        "McMaster-8215K2.step",
        (v.MCMASTER_8215K2_DIAMETER, v.MCMASTER_8215K2_DIAMETER, v.MCMASTER_8215K2_HEIGHT),
    ),
    "McMaster 94459A797 heat-set insert": (
        "McMaster-94459A797.step",
        (
            v.MCMASTER_94459A797_FLANGE_DIAMETER,
            v.MCMASTER_94459A797_FLANGE_DIAMETER,
            v.MCMASTER_94459A797_LENGTH,
        ),
    ),
    "McMaster 8681N11 corner bracket": (
        "McMaster-8681N11.step",
        (v.MCMASTER_8681N11_WIDTH, v.MCMASTER_8681N11_LEG, v.MCMASTER_8681N11_LEG),
    ),
    "McMaster 92290A228 M5 x 12 screw": (
        "McMaster-92290A228.step",
        (
            v.MCMASTER_92290A_HEAD_DIAMETER,
            v.MCMASTER_92290A_HEAD_DIAMETER,
            v.MCMASTER_92290A228_LENGTH + v.MCMASTER_92290A_HEAD_HEIGHT,
        ),
    ),
    "McMaster 92290A242 M5 x 20 screw": (
        "McMaster-92290A242.step",
        (
            v.MCMASTER_92290A_HEAD_DIAMETER,
            v.MCMASTER_92290A_HEAD_DIAMETER,
            v.MCMASTER_92290A242_LENGTH + v.MCMASTER_92290A_HEAD_HEIGHT,
        ),
    ),
    "McMaster 92290A265 M5 x 50 screw": (
        "McMaster-92290A265.step",
        (
            v.MCMASTER_92290A_HEAD_DIAMETER,
            v.MCMASTER_92290A_HEAD_DIAMETER,
            v.MCMASTER_92290A265_LENGTH + v.MCMASTER_92290A_HEAD_HEIGHT,
        ),
    ),
}


def extents(shape):
    size = shape.bounding_box().size
    return sorted((size.X, size.Y, size.Z))


class VendorModelTests(unittest.TestCase):
    def test_models_match_their_catalog_extents(self):
        for name, (filename, expected) in MODELS.items():
            with self.subTest(model=name):
                for found, wanted in zip(extents(vendor_step(filename)), sorted(expected)):
                    self.assertAlmostEqual(found, wanted, delta=MODEL_ROUNDING)

    def test_spherical_washer_halves(self):
        female, male = mcmaster_91131a028()
        # The male half is the smaller of the nested pair, and the pair stands MCMASTER_91131A028_HEIGHT tall.
        self.assertAlmostEqual(extents(male)[-1], v.MCMASTER_91131A028_MALE_DIAMETER, delta=MODEL_ROUNDING)
        self.assertAlmostEqual(
            extents(female)[-1], v.MCMASTER_91131A028_FEMALE_DIAMETER, delta=MODEL_ROUNDING
        )
        self.assertAlmostEqual(female.bounding_box().min.Y, 0.0, delta=MODEL_ROUNDING)

    def test_bushing_flange_and_barrel(self):
        bushing = kozak_tb250_80_625()  # Axis +Y, flange face at y=0, barrel toward +Y.

        def width_of(y0, y1):
            slab = Pos(0, (y0 + y1) / 2, 0) * Box(100, y1 - y0, 100)
            piece = bushing & slab
            box = piece.bounding_box()
            return max(box.size.X, box.size.Z)

        self.assertAlmostEqual(width_of(0.0, 0.2), v.KOZAK_TB250_FLANGE_DIAMETER, delta=MODEL_ROUNDING)
        self.assertAlmostEqual(
            width_of(v.KOZAK_TB250_FLANGE_THICKNESS + 0.1, v.KOZAK_TB250_LENGTH - 0.1),
            v.KOZAK_TB250_BARREL_DIAMETER,
            delta=MODEL_ROUNDING,
        )


if __name__ == "__main__":
    unittest.main()

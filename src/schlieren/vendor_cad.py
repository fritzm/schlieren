"""Vendor-supplied CAD models of purchased parts, stored in cad/vendor/ (see the README there).

Models are manufacturer geometry for viewing and clearance checks; committed or measured dimensions in
docs/design/ and the part parameter classes remain authoritative. Each part helper returns the model moved
from the vendor's frame into a documented mounting frame, so callers place it with a translation.
"""

from functools import cache
from pathlib import Path

from build123d import Compound, Location, Pos, Rot, import_step

VENDOR_CAD_DIR = Path(__file__).resolve().parents[2] / "cad" / "vendor"
INCH = 25.4

# Vendor-frame features used for placement (Thorlabs drawings are inch-primary).
SM1CP2M_SEAT_Y = 0.110 * INCH  # Flange seat face (thread shoulder) above the knurled back face.
SM1RC_M_THICKNESS = 0.400 * INCH
# FAS100 model: axis along +X through (y, z) = FAS100_AXIS_YZ, knob at -X, ball-tip apex at x=FAS100_TIP_X.
FAS100_AXIS_YZ = (1.583, -2.103)
FAS100_TIP_X = 22.013


@cache
def vendor_step(filename: str) -> Compound:
    """Import a single-part vendor STEP file (millimeters), in the vendor's own coordinate frame.

    Callers place the result with a Location (`loc * model`, which returns a moved copy); the cached object
    must not be modified.
    """
    return import_step(VENDOR_CAD_DIR / filename)


def _moved(filename: str, loc: Location) -> Compound:
    return loc * vendor_step(filename)


@cache
def thorlabs_tr50_m() -> Compound:
    """Thorlabs TR50/M post with its M4 setscrew stud; axis +Z, post base at the origin."""
    return _moved("Thorlabs-TR50-M.step", Rot(X=90))


@cache
def thorlabs_smr1_m() -> Compound:
    """Thorlabs SMR1/M ring; optical axis +Y through the origin, faces at y=0 and y=thickness, post seat -Z."""
    return _moved("Thorlabs-SMR1-M.step", Rot(X=90))


@cache
def thorlabs_sm1cp2m() -> Compound:
    """Thorlabs SM1CP2M end cap; axis +Y through the origin, flange seat face at y=0, thread toward +Y."""
    return _moved("Thorlabs-SM1CP2M.step", Pos(0, -SM1CP2M_SEAT_Y, 0))


@cache
def thorlabs_sm1rc_m() -> Compound:
    """Thorlabs SM1RC/M slip ring; axis +Y through the origin, faces at y=0 and y=thickness, post seat -Z.

    The M4 locking screw across the clamp split is at +Z.
    """
    return _moved("Thorlabs-SM1RC-M.step", Pos(0, SM1RC_M_THICKNESS, 0) * Rot(X=90))


@cache
def thorlabs_fas100() -> Compound:
    """Thorlabs FAS100 1/4"-80 adjuster; ball-tip apex at the origin, axis +Z toward the knob."""
    y, z = FAS100_AXIS_YZ
    to_tip = Pos(-FAS100_TIP_X, -y, -z)
    return _moved("Thorlabs-FAS100.step", Rot(Y=90) * to_tip)


@cache
def alpha_cn40_40b() -> Compound:
    """Alpha CN40-40B pin-fin heatsink; axis +Y through the origin, base mounting face at y=0, pins toward -Y."""
    return _moved("Alpha-CN40-40B.step", Rot(Z=180))

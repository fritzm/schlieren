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
# SM1V05 model: axis +X through (y, z) = SM1V05_AXIS_YZ, sleeve end at x=0; the SM1NT lock ring and the lens
# retaining ring are separate solids, each with its sleeve-end-side face at the x given here.
SM1V05_AXIS_YZ = (0.600 * INCH, 0.600 * INCH)
SM1V05_LOCK_RING_X = 0.195 * INCH
SM1V05_RETAINING_RING_X = 0.950 * INCH
SM1L03_SHOULDER_X = -0.330 * INCH  # External-thread shoulder; thread end at x=-0.450 in, open end at x=0.
SM1D12_SHOULDER_Z = 0.080 * INCH  # External-thread shoulder above the thread end at z=0.
ACL2520U_A_PLANO_Y = 6.0  # Plano face; convex vertex at y=-6.0.
# FAS100 model: axis along +X through (y, z) = FAS100_AXIS_YZ, knob at -X, ball-tip apex at x=FAS100_TIP_X.
FAS100_AXIS_YZ = (1.583, -2.103)
FAS100_TIP_X = 22.013
# McMaster 92815A202 model: axis +Z through the origin, centered on its height, collar at +Z.
MCMASTER_92815A202_DIAMETER = 20.0
MCMASTER_92815A202_HEIGHT = 5.0
# McMaster 8215K2 model: hemisphere on axis +Y through the origin, adhesive face at y=-height/2, apex toward +Y.
MCMASTER_8215K2_DIAMETER = 1.25 * INCH
# McMaster 93339A252 model: axis +Z through the origin, hex-socket end at z=11.99 mm, ball apex at z=-13.01 mm;
# the Ø3 mm ball is a separate solid centered 1.5 mm inside its apex.
MCMASTER_93339A252_LENGTH = 25.0  # Overall, socket end to ball apex.
MCMASTER_93339A252_DIAMETER = 5.0
MCMASTER_93339A252_BALL_DIAMETER = 3.0
MCMASTER_93339A252_APEX_Z = -13.01
# McMaster 94459A797 model (inch-dimensioned): axis +Y through the origin, flange face at y=0.1525 in, tapered
# pilot end at y=-0.1125 in; Ø5 mm plain bore.
MCMASTER_94459A797_LENGTH = 0.265 * INCH
MCMASTER_94459A797_FLANGE_DIAMETER = 0.312 * INCH
MCMASTER_94459A797_FLANGE_Y = 0.1525 * INCH
MCMASTER_8215K2_HEIGHT = 0.625 * INCH


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
def thorlabs_sm1v05() -> tuple[Compound, Compound, Compound]:
    """Thorlabs SM1V05 as (body, SM1NT lock ring, lens retaining ring), each on axis +Y through the origin.

    The body has its sleeve (externally threaded) end at y=0 and its open end toward +Y. The two rings are
    positioned along the body in use, so each is returned with its sleeve-side face at y=0.
    """
    y, z = SM1V05_AXIS_YZ
    retaining_ring, lock_ring, body = sorted(
        vendor_step("Thorlabs-SM1V05.step").solids(), key=lambda s: s.volume
    )
    to_axis = Rot(Z=90) * Pos(0, -y, -z)
    return (
        Compound([to_axis * body]),
        Compound([to_axis * Pos(-SM1V05_LOCK_RING_X, 0, 0) * lock_ring]),
        Compound([to_axis * Pos(-SM1V05_RETAINING_RING_X, 0, 0) * retaining_ring]),
    )


@cache
def thorlabs_acl2520u_a() -> Compound:
    """Thorlabs ACL2520U-A condenser; axis +Y through the origin, plano face at y=0, convex vertex toward +Y."""
    return _moved("Thorlabs-ACL2520U-A.step", Pos(0, ACL2520U_A_PLANO_Y, 0) * Rot(Z=180))


@cache
def thorlabs_sm1l03() -> Compound:
    """Thorlabs SM1L03 tube, without its retaining ring; axis +Y through the origin.

    The external-thread shoulder is at y=0, with the thread toward -Y and the open end toward +Y.
    """
    tube = max(vendor_step("Thorlabs-SM1L03.step").solids(), key=lambda s: s.volume)
    return Compound([Rot(Z=90) * Pos(-SM1L03_SHOULDER_X, 0, 0) * tube])


@cache
def thorlabs_sm1d12() -> tuple[Compound, Compound]:
    """Thorlabs SM1D12 iris as (housing with leaves, actuating lever), sharing one frame.

    Axis +Y through the origin, external-thread shoulder at y=0, thread toward -Y, lever at +Z.
    """
    iris = _moved("Thorlabs-SM1D12.step", Rot(Y=180) * Rot(X=-90) * Pos(0, 0, -SM1D12_SHOULDER_Z))
    *rest, lever = sorted(iris.solids(), key=lambda s: s.bounding_box().max.Z)
    return Compound(rest), Compound([lever])


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


@cache
def mcmaster_92815a202() -> Compound:
    """McMaster 92815A202 M5 low-profile knurled thumb nut (unthreaded model); axis +Z through the origin.

    The collar face is at z=0, bearing downward, with the knurled head toward +Z.
    """
    return _moved("McMaster-92815A202.step", Pos(0, 0, MCMASTER_92815A202_HEIGHT / 2) * Rot(X=180))


@cache
def mcmaster_8215k2() -> Compound:
    """McMaster 8215K2 Sorbothane bumper, a hemisphere; axis +Z through the origin.

    The adhesive face is at z=0, with the dome hanging toward -Z.
    """
    return _moved("McMaster-8215K2.step", Pos(0, 0, -MCMASTER_8215K2_HEIGHT / 2) * Rot(X=-90))


@cache
def mcmaster_93339a252() -> Compound:
    """McMaster 93339A252 M5 × 25 ball-tip set screw (unthreaded model); axis +Z through the origin.

    The ball apex is at the origin, pointing +Z, with the screw body and its hex socket toward -Z.
    """
    return _moved("McMaster-93339A252.step", Pos(0, 0, MCMASTER_93339A252_APEX_Z) * Rot(X=180))


@cache
def mcmaster_94459a797() -> Compound:
    """McMaster 94459A797 M5 flanged heat-set insert (unthreaded model); axis +Z through the origin.

    The flange face is at z=0, with the knurled body and its tapered pilot end toward -Z.
    """
    return _moved("McMaster-94459A797.step", Pos(0, 0, -MCMASTER_94459A797_FLANGE_Y) * Rot(X=90))

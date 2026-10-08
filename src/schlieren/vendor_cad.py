"""Vendor-supplied CAD models of purchased parts, stored in cad/vendor/ (see the README there).

Models are manufacturer geometry for viewing and clearance checks; committed or measured dimensions in
docs/design/ and the part parameter classes remain authoritative. Each part helper returns the model moved
from the vendor's frame into a documented mounting frame, so callers place it with a translation.
"""

from functools import cache
from pathlib import Path

from build123d import Box, Compound, Location, Pos, Rot, import_step

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
# Kozak TS250-80-2500 model: axis +X through the origin, ball center at x=0 (Ø3.969 mm ball, so the tip is at
# x=-KOZAK_TS250_BALL_RADIUS), plain Ø6.35 mm body to the end at x=61.516 mm, which has a hex-drive socket 2.286 mm deep.
KOZAK_TS250_BALL_RADIUS = 1.984
KOZAK_TS250_LENGTH = 2.5 * INCH
KOZAK_TS250_DIAMETER = 0.25 * INCH
KOZAK_TS250_END_X = 61.516
# Kozak KB250-80 model: axis +X through the origin, knurled Ø12.7 mm body from x=-1.538 to 9.892 mm. The open end
# (x=9.892) takes the screw end: a Ø6.35 bore to x=4.304, then a Ø3.94 pocket (over the hex socket) to x=-1.03.
KOZAK_KB250_OPEN_X = 9.892
KOZAK_KB250_BORE_BOTTOM_X = 4.304
KOZAK_KB250_LENGTH = 11.43
KOZAK_KB250_DIAMETER = 0.5 * INCH
# Kozak TB250-80-625 model: axis +X through (y, z) = (94.65, 0) mm, off origin; flange face at x=-60.966 mm.
KOZAK_TB250_AXIS_Y = 94.65
KOZAK_TB250_FLANGE_X = -60.966
KOZAK_TB250_LENGTH = 0.625 * INCH
KOZAK_TB250_FLANGE_DIAMETER = 8.941
KOZAK_TB250_BARREL_DIAMETER = 7.938
KOZAK_TB250_FLANGE_THICKNESS = 0.254
# McMaster 8681N11 model: extrusion axis +X centered on the origin, outer corner at y=z=-3 in / 2, legs toward +y and +z.
MCMASTER_8681N11_LEG = 3.0 * INCH
MCMASTER_8681N11_THICKNESS = 0.25 * INCH
MCMASTER_8681N11_WIDTH = 33.274
# McMaster 8681N11 holes: Ø8.332 mm, centered across the leg, 0.75 and 2.25 in from the outer corner on each leg.
MCMASTER_8681N11_HOLE_DIAMETER = 8.332
MCMASTER_8681N11_HOLE_OFFSETS = (0.75 * INCH, 2.25 * INCH)
# McMaster 98164A527 model: axis +Z through the origin, bearing face at z=17.463 mm, tip at z=-17.463 mm.
MCMASTER_98164A527_LENGTH = 1.375 * INCH
MCMASTER_98164A527_HEAD_HEIGHT = 4.216
MCMASTER_98164A527_HEAD_DIAMETER = 13.87
MCMASTER_98164A527_HEAD_BASE_Z = 17.463
# McMaster 90099A030 model: axis +Y through the origin, y=-5.556 mm at the seating face, nylon insert at +Y.
MCMASTER_90099A030_HEIGHT = 7 / 16 * INCH
# McMaster 96659A134 model: axis +Z through the origin, centered on its 1.664 mm thickness.
MCMASTER_96659A134_THICKNESS = 1.664
MCMASTER_96659A134_DIAMETER = 17.476
# McMaster 92290A228 (M5 × 12) and 92290A242 (M5 × 20) models, no threads: axis +Z through the origin, centered on the
# overall length (the nominal length plus the head), Ø8.5 mm head of 5 mm at +Z, Ø5 mm plain shank to -Z.
MCMASTER_92290A_HEAD_HEIGHT = 5.0
MCMASTER_92290A_HEAD_DIAMETER = 8.5
MCMASTER_92290A228_LENGTH = 12.0  # Nominal: under the head.
MCMASTER_92290A242_LENGTH = 20.0
MCMASTER_92290A265_LENGTH = 50.0  # The 92290A265 (M5 × 50) model has the same layout.
# McMaster 91116A350 model: axis +Z through the origin, centered on its 1.2 mm thickness; Ø15 mm OD.
MCMASTER_91116A350_THICKNESS = 1.2
MCMASTER_91116A350_DIAMETER = 15.0
# McMaster 93625A225 model (M5 nyloc nut, no threads): axis +Y through the origin, y from -2.5 to 2.5 mm, nylon insert
# at +Y; 8 mm across flats (along x), 9.11 mm across corners (along z); two solids (nut, insert).
MCMASTER_93625A225_HEIGHT = 5.0
# McMaster 93475A240 model: axis +Z through the origin, centered on its 1 mm thickness; Ø10 mm OD, Ø5.3 mm ID.
MCMASTER_93475A240_THICKNESS = 1.0
MCMASTER_93475A240_DIAMETER = 10.0
# McMaster 91292A114 model (M3 × 12, no threads): axis +Z through the origin, centered on its 15 mm overall length
# (12 mm under the head plus the head), Ø5.5 mm head of 3 mm at +Z, Ø3 mm plain shank to -Z.
MCMASTER_91292A114_LENGTH = 12.0  # Nominal: under the head.
MCMASTER_91292A114_HEAD_HEIGHT = 3.0
# McMaster 91585A351 (Ø3 × 10 mm) and 91585A457 (Ø4 × 20 mm) dowel pins: axis +X through the origin, centered on
# the length; chamfered ends.
MCMASTER_91585A351_DIAMETER = 3.0
MCMASTER_91585A351_LENGTH = 10.0
MCMASTER_91585A457_DIAMETER = 4.0
MCMASTER_91585A457_LENGTH = 20.0
# McMaster 91828A211 model (M3 nut, no threads): axis +Z through the origin, centered on its 2.4 mm height; 5.5 mm
# across flats (along x), 6.326 mm across corners (along y).
MCMASTER_91828A211_HEIGHT = 2.4
# McMaster 91131A028 model: axis +Y through the origin; the female half's flat back is at y=-3.378 mm.
MCMASTER_91131A028_BACK_Y = -3.378
MCMASTER_91131A028_HEIGHT = 6.756
MCMASTER_91131A028_FEMALE_DIAMETER = 0.5 * INCH
MCMASTER_91131A028_MALE_DIAMETER = 0.438 * INCH


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
def thorlabs_fas100_parts() -> tuple[Compound, Compound, Compound]:
    """The thorlabs_fas100 frame split as (screw with ball tip, knob, index dimple), for coloring."""
    dimple, tip, screw, knob = sorted(thorlabs_fas100().solids(), key=lambda s: s.volume)
    return Compound([screw, tip]), Compound([knob]), Compound([dimple])


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


@cache
def kozak_ts250_80_2500() -> tuple[Compound, Compound]:
    """Kozak TS250-80-2500 adjuster as (screw, ball tip); axis +Y through the origin, ball tip at y=0.

    The hex-drive end is at y=KOZAK_TS250_LENGTH.
    """
    to_tip = Pos(0, KOZAK_TS250_BALL_RADIUS, 0) * Rot(Z=90)
    ball, screw = sorted(vendor_step("Kozak-TS250-80-2500.step").solids(), key=lambda s: s.volume)
    return Compound([to_tip * screw]), Compound([to_tip * ball])


@cache
def kozak_tb250_80_625() -> Compound:
    """Kozak TB250-80-625 bushing; axis +Y through the origin, flange face at y=0, barrel toward +Y."""
    to_axis = Pos(KOZAK_TB250_AXIS_Y, -KOZAK_TB250_FLANGE_X, 0) * Rot(Z=90)
    return _moved("Kozak-TB250-80-625.step", to_axis)


@cache
def kozak_kb250_80() -> Compound:
    """Kozak KB250-80 knob; axis +Y through the origin, open (screw) end at y=0, outer end at y=11.43 mm."""
    return _moved("Kozak-KB250-80.step", Pos(0, KOZAK_KB250_OPEN_X, 0) * Rot(Z=-90))


@cache
def mcmaster_91131a028() -> tuple[Compound, Compound]:
    """McMaster 91131A028 spherical washer pair as (female half, male half); axis +Y through the origin.

    Nested as supplied, with the female half's flat back at y=0 and the male half's flat face at
    y=MCMASTER_91131A028_HEIGHT.
    """
    female, male = sorted(
        vendor_step("McMaster-91131A028.step").solids(), key=lambda s: s.bounding_box().min.Y
    )
    to_back = Pos(0, -MCMASTER_91131A028_BACK_Y, 0)
    return Compound([to_back * female]), Compound([to_back * male])


@cache
def mcmaster_8681n11() -> Compound:
    """McMaster 8681N11 3 in corner bracket; width along x centered on the origin, outer corner on the y and z axes.

    One leg lies along +y and the other along +z, both starting at the outer corner (y=z=0).
    """
    half = MCMASTER_8681N11_LEG / 2
    return _moved("McMaster-8681N11.step", Pos(0, half, half))


@cache
def mcmaster_98164a527() -> Compound:
    """McMaster 98164A527 5/16"-18 × 1-3/8" 316 stainless button-head screw (unthreaded model); axis +Z through the origin.

    The head's bearing face is at z=0, with the head toward +Z and the shank toward -Z.
    """
    return _moved("McMaster-98164A527.step", Pos(0, 0, -MCMASTER_98164A527_HEAD_BASE_Z))


@cache
def mcmaster_90099a030() -> tuple[Compound, Compound]:
    """McMaster 90099A030 5/16"-18 heavy-profile locknut (unthreaded model) as (nut, nylon insert); axis +Z through the origin.

    The seating face is at z=0, with the nylon insert end toward +Z.
    """
    to_seat = Pos(0, 0, MCMASTER_90099A030_HEIGHT / 2) * Rot(X=90)
    insert, nut = sorted(vendor_step("McMaster-90099A030.step").solids(), key=lambda s: s.volume)
    return Compound([to_seat * nut]), Compound([to_seat * insert])


@cache
def mcmaster_96659a134() -> Compound:
    """McMaster 96659A134 5/16" SAE washer; axis +Z through the origin, one face at z=0, the other at +thickness."""
    return _moved("McMaster-96659A134.step", Pos(0, 0, MCMASTER_96659A134_THICKNESS / 2))


def _m5_socket_screw(filename: str, length: float) -> Compound:
    """A McMaster M5 socket head cap screw model: axis +Z, head bearing face at z=0, head toward -Z, shank to +Z."""
    return _moved(filename, Pos(0, 0, (length - MCMASTER_92290A_HEAD_HEIGHT) / 2) * Rot(X=180))


@cache
def mcmaster_92290a228() -> Compound:
    """McMaster 92290A228 M5 × 0.8 × 12 mm 316 stainless socket head screw (unthreaded model).

    Axis +Z through the origin, the head's bearing face at z=0 with the head toward -Z and the shank toward +Z.
    """
    return _m5_socket_screw("McMaster-92290A228.step", MCMASTER_92290A228_LENGTH)


@cache
def mcmaster_92290a242() -> Compound:
    """McMaster 92290A242 M5 × 0.8 × 20 mm 316 stainless socket head screw (unthreaded model).

    Axis +Z through the origin, the head's bearing face at z=0 with the head toward -Z and the shank toward +Z.
    """
    return _m5_socket_screw("McMaster-92290A242.step", MCMASTER_92290A242_LENGTH)


@cache
def mcmaster_93475a240() -> Compound:
    """McMaster 93475A240 M5 flat washer; axis +Z through the origin, one face at z=0, the other at +thickness."""
    return _moved("McMaster-93475A240.step", Pos(0, 0, MCMASTER_93475A240_THICKNESS / 2))


@cache
def mcmaster_91292a114() -> Compound:
    """McMaster 91292A114 M3 × 0.5 × 12 mm 18-8 stainless socket head screw (unthreaded model).

    Axis +Z through the origin, the head's bearing face at z=0 with the head toward -Z and the shank toward +Z.
    """
    shift = (MCMASTER_91292A114_LENGTH - MCMASTER_91292A114_HEAD_HEIGHT) / 2
    return _moved("McMaster-91292A114.step", Pos(0, 0, shift) * Rot(X=180))


@cache
def mcmaster_91585a351() -> Compound:
    """McMaster 91585A351 Ø3 × 10 mm 18-8 stainless dowel pin; axis +Z through the origin, centered on its length."""
    return _moved("McMaster-91585A351.step", Rot(Y=90))


@cache
def mcmaster_91585a457() -> Compound:
    """McMaster 91585A457 Ø4 × 20 mm 18-8 stainless dowel pin; axis +Z through the origin, centered on its length."""
    return _moved("McMaster-91585A457.step", Rot(Y=90))


@cache
def mcmaster_91828a211() -> Compound:
    """McMaster 91828A211 M3 × 0.5 hex nut (unthreaded model); axis +Z through the origin.

    One face is at z=0 and the other at +height; the flats are 5.5 mm apart along x, the corners along y.
    """
    return _moved("McMaster-91828A211.step", Pos(0, 0, MCMASTER_91828A211_HEIGHT / 2))


@cache
def mcmaster_92290a265() -> Compound:
    """McMaster 92290A265 M5 × 0.8 × 50 mm 316 stainless socket head screw (unthreaded model).

    Axis +Z through the origin, the head's bearing face at z=0 with the head toward -Z and the shank toward +Z.
    """
    return _m5_socket_screw("McMaster-92290A265.step", MCMASTER_92290A265_LENGTH)


@cache
def mcmaster_91116a350() -> Compound:
    """McMaster 91116A350 M5 oversized washer; axis +Z through the origin, one face at z=0, the other at +thickness."""
    return _moved("McMaster-91116A350.step", Pos(0, 0, MCMASTER_91116A350_THICKNESS / 2))


@cache
def mcmaster_93625a225() -> Compound:
    """McMaster 93625A225 M5 nylon-insert locknut (unthreaded model); axis +Z through the origin.

    One face is at z=0 and the other, with the nylon insert, at +height; the flats are 8 mm apart along x.
    """
    return _moved("McMaster-93625A225.step", Pos(0, 0, MCMASTER_93625A225_HEIGHT / 2) * Rot(X=90))


@cache
def m5_socket_screw(length: float) -> Compound:
    """An M5 socket head cap screw of the given length under the head, as the kit screws are modeled.

    The assortment kits have no vendor models, so this is the shortest McMaster M5 model (12, 20 or 50 mm) at
    least that long, with its shank cut to length. Axis +Z through the origin, the head's bearing face at z=0 with
    the head toward -Z and the shank toward +Z.
    """
    models = (
        (MCMASTER_92290A228_LENGTH, mcmaster_92290a228),
        (MCMASTER_92290A242_LENGTH, mcmaster_92290a242),
        (MCMASTER_92290A265_LENGTH, mcmaster_92290a265),
    )
    for model_length, model in models:
        if length <= model_length:
            break
    else:
        raise ValueError(f"No M5 screw model reaches {length} mm")
    if length == model_length:
        return model()
    size = 2 * MCMASTER_92290A_HEAD_DIAMETER
    return model() - Pos(0, 0, length + size / 2) * Box(size, size, size)

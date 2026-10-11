"""The Thorlabs FAS100 adjuster as the slit head and the cutoff carriage show it.

A FAS100 turns in a McMaster 98625A950 brass insert pressed into a printed block, and its ball tip bears on an
N52 bar magnet let into the part it pushes. The three pieces are built here in the adjuster's own frame, with
the screw axis along +z, so each model places them with one location (`fas100_children` and the magnet) or
one frame for the insert.

Frame for `fas100_children` and `bearing_magnet`: origin at the ball-tip apex, +z along the screw toward the
knob, so the magnet occupies z from -thickness to 0.
"""

from build123d import Location, Part

from schlieren.cad import CUT_OVERRUN, box_between, labeled, z_cylinder
from schlieren.hardware import (
    FAS100_THREAD_DIAMETER,
    INSERT_98625A950_BODY_DIAMETER,
    INSERT_98625A950_FLANGE_DIAMETER,
    INSERT_98625A950_FLANGE_THICKNESS,
    MAGNET_LENGTH,
    MAGNET_THICKNESS,
    MAGNET_WIDTH,
)
from schlieren.palette import INDEX_DIMPLE, KNOB_BLACK, METAL
from schlieren.vendor_cad import thorlabs_fas100_parts


def fas100_children(loc: Location, label: str = "FAS100") -> list[Part]:
    """The FAS100 vendor model as three labeled children, colored as screw, knob, and index dimple.

    The model's frame is the ball-tip apex at the origin and the axis +z toward the knob; loc places it.
    """
    screw, knob, dimple = thorlabs_fas100_parts()
    return [
        labeled(screw, label, METAL, loc),
        labeled(knob, f"{label} knob", KNOB_BLACK, loc),
        labeled(dimple, f"{label} index dimple", INDEX_DIMPLE, loc),
    ]


def bearing_magnet(
    x: float = 0.0,
    y: float = 0.0,
    z_tip: float = 0.0,
    length: float = MAGNET_LENGTH,
    width: float = MAGNET_WIDTH,
    thickness: float = MAGNET_THICKNESS,
) -> Part:
    """The magnet pad under a ball tip at (x, y, z_tip): its face on z_tip, its body toward -z.

    The length lies along x and the width along y.
    """
    return box_between(x - length / 2, x + length / 2, y - width / 2, y + width / 2, z_tip - thickness, z_tip)


def insert_98625a950(
    body_start: float,
    body_length: float,
    flange_side: int,
    x: float = 0.0,
    y: float = 0.0,
    body_diameter: float = INSERT_98625A950_BODY_DIAMETER,
    flange_diameter: float = INSERT_98625A950_FLANGE_DIAMETER,
    flange_thickness: float = INSERT_98625A950_FLANGE_THICKNESS,
) -> Part:
    """The 1/4"-80 insert on the axis +z through (x, y), with its plain 1/4 in bore.

    The body spans z from body_start to body_start + body_length. The flange is against its start face when
    flange_side is -1 (the flange below the body) and against its end face when it is +1.
    """
    body_end = body_start + body_length
    if flange_side < 0:
        flange0, flange1 = body_start - flange_thickness, body_start
    else:
        flange0, flange1 = body_end, body_end + flange_thickness
    insert = z_cylinder(body_diameter, x, y, body_start, body_end)
    insert += z_cylinder(flange_diameter, x, y, flange0, flange1)
    through = (min(body_start, flange0) - CUT_OVERRUN, max(body_end, flange1) + CUT_OVERRUN)
    return insert - z_cylinder(FAS100_THREAD_DIAMETER, x, y, *through)

"""Stanley 11-515 backed single-edge razor blade, as clamped in the slit head, slit stage, and cutoff cassette.

The blade is a flat 0.010 in steel plate with a double-ground cutting edge along one long side. The opposite
long side is the back: a folded strip wraps the back edge and lies over both faces, so the plate is 0.040 in
thick across the fold. A slot through the plate at mid-length and a notch in each end are the blade-holder
features of the razor scraper it is made for.

Local frame: x along the length (centered), y through the thickness (the plate's mid-plane is y = 0, so the
two faces are y = ±thickness / 2), z across the width from the cutting edge (z = 0) to the back (z = width).
The cutting edge's midpoint is the origin. A fixture places the blade with `Location`s of its own.

Overall length, width, plate and fold thickness, fold extent, and bevel break are measured (calipers). The
edge tip thickness is an assumption (a real edge is a few microns; a zero-thickness edge is not a solid). The
notches, the slot, and the rounded fold corners are approximated from a photograph of the blade, scaled to
its measured length: **Provisional**, good to about ±0.3 mm, and not dimensions any fixture may rely on.
"""

from dataclasses import dataclass
from functools import cache
from math import atan2, cos, degrees, sin

from build123d import Axis, Polygon, Pos, Rot, extrude, fillet

from schlieren.cad import CUT_OVERRUN, along_x, box_between, labeled, y_cylinder
from schlieren.palette import METAL
from schlieren.standards import INCH
from schlieren.validation import require_positive_dimensions


@dataclass(frozen=True)
class RazorBladeParameters:
    # Measured (calipers).
    length: float = 1.537 * INCH
    width: float = 0.773 * INCH  # Cutting edge to the outside of the fold.
    thickness: float = 0.010 * INCH  # The plate.
    fold_thickness: float = 0.040 * INCH  # Overall across the fold, both layers.
    fold_extent: float = 0.277 * INCH  # From the back, over each face.
    bevel_break: float = 0.030 * INCH  # Cutting edge to where each bevel meets the face.
    # Assumed: the flat across the very tip of the edge.
    edge_tip_thickness: float = 0.01
    # Approximated from the photograph (provisional).
    fold_corner_radius: float = 2.4  # Plan view, the fold's two corners toward the cutting edge.
    notch_depth: float = 3.5  # In from each end.
    notch_width: float = 3.0  # Full-round end.
    notch_z: float = 9.5  # Center, from the cutting edge.
    notch_mouth_radius: float = 0.5  # Flare where the notch meets the end.
    slot_width: float = 2.6
    slot_length: float = 6.1  # Overall, along the width.
    slot_z: float = 8.85  # Center, from the cutting edge.

    @property
    def fold_standoff(self):
        """How far the fold's outer layer stands proud of the plate's face, on each side."""
        return (self.fold_thickness - self.thickness) / 2

    @property
    def fold_front_z(self):
        """Distance from the cutting edge to the fold's edge on the plate."""
        return self.width - self.fold_extent

    def validate(self):
        require_positive_dimensions(self)
        if self.edge_tip_thickness >= self.thickness:
            raise ValueError("The edge tip must be thinner than the plate")
        if self.fold_thickness <= self.thickness:
            raise ValueError("The fold must be thicker than the plate")
        if self.bevel_break >= self.fold_front_z:
            raise ValueError("The bevel must end before the fold")
        if self.fold_corner_radius >= min(self.fold_extent, self.length / 2):
            raise ValueError("The fold corners must leave straight edges")
        notch_flank = self.notch_z + self.notch_width / 2
        if self.notch_z - self.notch_width / 2 <= self.bevel_break or notch_flank >= self.fold_front_z:
            raise ValueError("Notches must lie between the bevel and the fold")
        if 2 * self.notch_depth + self.slot_width >= self.length:
            raise ValueError("The notches and slot must not meet")
        if self.notch_mouth_radius >= self.notch_depth - self.notch_width / 2:
            raise ValueError("The notch mouth flare must leave the notch's straight flanks")
        slot_span = self.slot_length / 2
        if self.slot_z - slot_span <= self.bevel_break or self.slot_z + slot_span >= self.fold_front_z:
            raise ValueError("The slot must lie between the bevel and the fold")
        if self.slot_length <= self.slot_width:
            raise ValueError("The slot must be longer than it is wide")


def _plate(p):
    """The beveled plate over the full width, extruded along x."""
    half, tip = p.thickness / 2, p.edge_tip_thickness / 2
    section = [
        (-tip, 0.0),
        (-half, p.bevel_break),
        (-half, p.width),
        (half, p.width),
        (half, p.bevel_break),
        (tip, 0.0),
    ]
    face = along_x((0, 0, 0)) * Polygon(*section, align=None)  # Plane axes are (y, z).
    return extrude(face, amount=p.length / 2, both=True)


def _fold(p):
    """The folded strip over both faces, its corners toward the cutting edge rounded."""
    fold = box_between(
        -p.length / 2,
        p.length / 2,
        -p.fold_thickness / 2,
        p.fold_thickness / 2,
        p.fold_front_z,
        p.width,
    )
    front = (
        fold.edges()
        .filter_by(Axis.Y)
        .filter_by_position(Axis.Z, p.fold_front_z - 0.01, p.fold_front_z + 0.01)
    )
    return fillet(front, p.fold_corner_radius)


def _through(p):
    """The y extent of a cutter through the whole thickness, fold included."""
    return -p.fold_thickness / 2 - CUT_OVERRUN, p.fold_thickness / 2 + CUT_OVERRUN


def _x_slot_cut(p, x0, x1, z, width):
    """Stadium through the thickness, long in x from x0 to x1 (the end centers), at z."""
    y0, y1 = _through(p)
    cut = box_between(x0, x1, y0, y1, z - width / 2, z + width / 2)
    return cut + y_cylinder(width, x0, z, y0, y1) + y_cylinder(width, x1, z, y0, y1)


def _z_slot_cut(p, x, z0, z1, width):
    """Stadium through the thickness, long in z from z0 to z1 (the end centers), at x."""
    y0, y1 = _through(p)
    cut = box_between(x - width / 2, x + width / 2, y0, y1, z0, z1)
    return cut + y_cylinder(width, x, z0, y0, y1) + y_cylinder(width, x, z1, y0, y1)


@cache
def build_razor_blade(p=None):
    """The blade: plate, fold, end notches, and central slot, as one solid in the blade frame."""
    p = p or RazorBladeParameters()
    p.validate()
    blade = _plate(p) + _fold(p)
    r = p.notch_width / 2
    mouth = p.length / 2 + CUT_OVERRUN
    for sign in (-1, 1):
        end = sign * p.length / 2
        inner = end - sign * (p.notch_depth - r)  # Center of the full-round end.
        blade -= _x_slot_cut(p, *sorted((inner, sign * mouth)), p.notch_z, p.notch_width)
    half_run = (p.slot_length - p.slot_width) / 2
    blade -= _z_slot_cut(p, 0, p.slot_z - half_run, p.slot_z + half_run, p.slot_width)
    # Flare each notch's mouth where it meets the end.
    flare = [
        e
        for e in blade.edges().filter_by(Axis.Y)
        if abs(abs(e.center().X) - p.length / 2) < 0.01 and abs(abs(e.center().Z - p.notch_z) - r) < 0.01
    ]
    return fillet(flare, p.notch_mouth_radius)


def seat_tilt(p, overhang):
    """(tilt in radians, blade-frame z of the near contact) of a blade resting on a seat plane.

    The seat edge is `overhang` back from the cutting edge, and the seat extends under the fold. The blade
    then touches the seat at that edge, with its seat-side plate face, and at the fold's front edge, with the
    fold's outer layer: the fold stands `fold_standoff` proud of the face, so the plate rises toward the fold
    by that much between the two contacts. The tilt is that rise over the span between them.
    """
    near = overhang
    for _ in range(4):  # The near contact is on the face, so it sits slightly off the overhang.
        tilt = atan2(p.fold_standoff, p.fold_front_z - near)
        near = (overhang - p.thickness / 2 * sin(tilt)) / cos(tilt)
    return tilt, near


def seated_blade_location(p, overhang):
    """Blade frame -> seat frame for a blade resting on a seat plane (y = 0) whose edge is `overhang` back
    from the cutting edge.

    Seat frame: y out of the seat, z across the blade from the cutting edge (z = 0) toward the fold, x along
    the length. The blade rests on the seat edge and on the fold's front edge, inclined toward the fold
    (`seat_tilt`). A blade on the opposite side of a slit is this placed with `Rot(Y=180)`.
    """
    tilt, near = seat_tilt(p, overhang)
    return Pos(0, p.thickness / 2 * cos(tilt) - near * sin(tilt), 0) * Rot(X=-degrees(tilt))


def build_razor_blade_assembly(p=None):
    """The blade as a labeled viewer child."""
    return labeled(build_razor_blade(p), "Razor blade", METAL)

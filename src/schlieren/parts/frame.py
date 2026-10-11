"""Tabletop optical frame; design §4.

Two yaw-adjustable 2020 rails pivoted on the plywood front pivot plate, each with a pivot lug, a fixed yaw
strap, and a rear foot block; three Sorbothane feet. Nothing here is printed: the plywood parts are cut and
drilled, everything else is purchased.

Coordinates: the §3.4 pivot frame. The origin is at the midpoint of the aft plate edge, +y toward the mirror
along the plate centerline, +x to the right seen from above with the mirror ahead, and z up with the rail top
at z=0; the plate lies at positive y and the rails run aft of it to negative y. A rail has side -1 (left, x<0,
the source rail) or +1 (right, the imaging rail). Each rail assembly is built in its §3.4 rail frame, the same
senses with y along that rail and the origin at its pivot.

The thumb nuts, feet, foot screws, and foot washers are the vendor models. Other fasteners, washers, and nuts are plain nominal envelopes
without threads or sockets, and the T-nuts are not modeled.
"""

from dataclasses import dataclass
from math import atan, cos, degrees, pi, sin

from build123d import Compound, Location, Part, Pos, Rot

from schlieren.cad import CUT_OVERRUN, assembly, box_between, floor_box, labeled, place, z_cylinder
from schlieren.palette import BLACK_ANODIZED, BLACK_OXIDE, METAL, PLYWOOD, RUBBER, SORBOTHANE, STEEL_GRAY
from schlieren.parts.rail import RailProfile, build_rail
from schlieren.standards import INCH
from schlieren.validation import require_positive_dimensions
from schlieren.vendor_cad import (
    MCMASTER_8215K2_DIAMETER,
    MCMASTER_8215K2_HEIGHT,
    MCMASTER_91116A350_THICKNESS,
    MCMASTER_92290A242_LENGTH,
    MCMASTER_92290A265_LENGTH,
    MCMASTER_92815A202_HEIGHT,
    MCMASTER_93475A240_THICKNESS,
    MCMASTER_93625A225_HEIGHT,
    m5_socket_screw,
    mcmaster_8215k2,
    mcmaster_91116a350,
    mcmaster_92290a265,
    mcmaster_92815a202,
    mcmaster_93475a240,
    mcmaster_93625a225,
)

SIDES = {"Left": -1, "Right": 1}

# Nominal M5 hardware envelopes (ISO 4762 socket head, ISO 7089 washer, nyloc), for the viewer and stack checks.
M5_SHANK_DIAMETER = 5.0
M5_WASHER_DIAMETER = 10.0
M5_WASHER_THICKNESS = MCMASTER_93475A240_THICKNESS
M5_NYLOC_HEIGHT = MCMASTER_93625A225_HEIGHT


@dataclass(frozen=True)
class FrameParameters:
    # Rails (§4.1); slot dimensions are the measured values.
    rail_size: float = 20.0
    rail_length: float = 400.0
    rail_slot_mouth_width: float = 6.55
    rail_slot_cavity_width: float = 11.07
    rail_slot_depth: float = 6.45
    rail_slot_lip_thickness: float = 1.65

    # Front pivot plate (§§3.3, 4.2).
    mirror_distance: float = 3200.0
    pivot_separation: float = 95.0
    pivot_setback: float = 25.0  # Pivot line (and front foot) aft of the mirror-facing edge.
    plate_width: float = 180.0  # Transverse.
    plate_depth: float = 150.0  # Fore/aft.
    plywood_thickness: float = 12.7
    yaw_station: float = 90.0  # Strap center aft of the pivot, along the nominal rail axis.
    m5_clearance_diameter: float = 5.5

    # Pivot and yaw hardware (§4.3).
    joining_plate_length: float = 60.0
    joining_plate_width: float = 18.0
    joining_plate_thickness: float = 4.0
    joining_plate_hole_pitch: float = 20.0
    pivot_spacer_length: float = 20.0
    pivot_spacer_outer_diameter: float = 10.0
    pivot_spacer_inner_diameter: float = 5.3
    oversize_washer_diameter: float = 15.0
    oversize_washer_thickness: float = MCMASTER_91116A350_THICKNESS
    pivot_screw_length: float = MCMASTER_92290A265_LENGTH  # Also the yaw-clamp screw.
    friction_strip_thickness: float = INCH / 32
    friction_strip_length: float = 30.0

    # Rear support and feet (§4.4).
    foot_block_length: float = 75.0  # Along the rail.
    foot_block_width: float = 50.0
    foot_screw_spacing: float = 50.0
    foot_screw_length: float = MCMASTER_92290A242_LENGTH
    # Two washers under each head set how far the screw enters the rail slot. With one, an M5 × 20 stops only
    # 0.15 mm short of the measured slot floor and bottoms if the plywood runs thin; an M5 × 16 reaches barely
    # past the slot lip to the T-nut. No standard length lies between.
    foot_washers_per_screw: int = 2
    foot_diameter: float = MCMASTER_8215K2_DIAMETER
    foot_height: float = MCMASTER_8215K2_HEIGHT

    # Not fixed by the design document; model assumptions.
    rail_front_setback: float = 10.0  # Rail front end aft of the pivot, clearing the pivot spacer.
    lug_screw_length: float = 8.0  # Lug to rail top slot, at the two lug holes behind the pivot.
    foot_block_rear_setback: float = 0.0  # Foot-block rear edge forward of the rail rear end.

    @property
    def half_angle(self) -> float:
        """Nominal rail half-angle, radians."""
        return atan(self.pivot_separation / 2 / self.mirror_distance)

    @property
    def plate_top(self) -> float:
        return -self.rail_size

    @property
    def plate_bottom(self) -> float:
        return self.plate_top - self.plywood_thickness

    @property
    def table(self) -> float:
        """z of the surface the three feet stand on, with the feet uncompressed."""
        return self.plate_bottom - self.foot_height

    @property
    def strap_bottom(self) -> float:
        return self.friction_strip_thickness

    @property
    def strap_top(self) -> float:
        return self.strap_bottom + self.joining_plate_thickness

    @property
    def foot_block_center(self) -> float:
        """Foot-block center aft of the pivot, along the rail."""
        rail_rear = self.rail_front_setback + self.rail_length
        return rail_rear - self.foot_block_rear_setback - self.foot_block_length / 2

    @property
    def pivot_screw_protrusion(self) -> float:
        """Pivot screw tip beyond the top of its nyloc."""
        stack = (
            2 * self.oversize_washer_thickness
            + self.plywood_thickness
            + self.pivot_spacer_length
            + self.joining_plate_thickness
            + M5_NYLOC_HEIGHT
        )
        return self.pivot_screw_length - stack

    @property
    def yaw_screw_length_above_strap_washer(self) -> float:
        """Yaw screw thread left above the strap washer, for the thumb nut."""
        stack = (
            2 * self.oversize_washer_thickness
            + self.plywood_thickness
            + self.rail_size
            + self.friction_strip_thickness
            + self.joining_plate_thickness
        )
        return self.pivot_screw_length - stack

    @property
    def foot_washer_stack(self) -> float:
        return self.foot_washers_per_screw * M5_WASHER_THICKNESS

    @property
    def foot_screw_slot_entry(self) -> float:
        """Foot screw tip above the rail bottom face, into the bottom slot."""
        return self.foot_screw_length - self.foot_washer_stack - self.plywood_thickness

    @property
    def foot_screw_slot_margin(self) -> float:
        """Foot screw tip short of the slot floor."""
        return self.rail_slot_depth - self.foot_screw_slot_entry

    def rail_profile(self) -> RailProfile:
        return RailProfile(
            size=self.rail_size,
            slot_mouth_width=self.rail_slot_mouth_width,
            cavity_width=self.rail_slot_cavity_width,
            slot_depth=self.rail_slot_depth,
            lip_thickness=self.rail_slot_lip_thickness,
        )

    def rail_direction(self, side: int, yaw: float = 0.0) -> tuple[float, float]:
        """Unit vector along a rail toward the mirror (the rail frame's +y), in the pivot frame, with the rail
        yawed outward from nominal by yaw radians."""
        angle = self.half_angle + yaw
        return -side * sin(angle), cos(angle)

    def rail_location(self, side: int, yaw: float = 0.0) -> Location:
        """Rail frame in the pivot frame: origin at the pivot on the rail top, +y along the rail toward the
        mirror, +x across it to the right."""
        x, y = self.pivot_center(side)
        return Pos(x, y, 0) * Rot(Z=degrees(side * (self.half_angle + yaw)))

    def pivot_center(self, side: int) -> tuple[float, float]:
        return side * self.pivot_separation / 2, self.plate_depth - self.pivot_setback

    def strap_center(self, side: int) -> tuple[float, float]:
        (x, y), (dx, dy) = self.pivot_center(side), self.rail_direction(side)
        return x - self.yaw_station * dx, y - self.yaw_station * dy

    def yaw_bolt_centers(self, side: int) -> tuple[tuple[float, float], tuple[float, float]]:
        """The strap's two outer holes, in order of increasing x."""
        (x, y), (dx, dy) = self.strap_center(side), self.rail_direction(side)
        pitch = self.joining_plate_hole_pitch
        return (x - pitch * dy, y + pitch * dx), (x + pitch * dy, y - pitch * dx)

    def plate_holes(self) -> dict[str, tuple[float, float]]:
        """Centers of the six plate holes, by name."""
        holes = {}
        for name, side in SIDES.items():
            holes[f"{name} pivot"] = self.pivot_center(side)
            bolts = self.yaw_bolt_centers(side)
            outer, inner = bolts if side < 0 else reversed(bolts)
            holes[f"{name} outer yaw"] = outer
            holes[f"{name} inner yaw"] = inner
        return holes

    def validate(self) -> None:
        require_positive_dimensions(self, allow_zero=True)
        if self.pivot_spacer_length != self.rail_size:
            raise ValueError("The pivot spacer must hold the lug at the rail top")
        if self.rail_front_setback <= self.pivot_spacer_outer_diameter / 2:
            raise ValueError("The rail front end must clear the pivot spacer")
        if self.rail_front_setback >= self.joining_plate_hole_pitch - M5_SHANK_DIAMETER / 2:
            raise ValueError("The rail must reach under the lug's first fixing hole")
        if self.pivot_screw_protrusion < 0:
            raise ValueError("The pivot screw must reach through its nyloc")
        if self.yaw_screw_length_above_strap_washer < MCMASTER_92815A202_HEIGHT:
            raise ValueError("The yaw screw must reach through its thumb nut")
        if self.foot_screw_slot_entry <= self.rail_slot_lip_thickness:
            raise ValueError("The foot screws must reach the T-nuts under the slot lips")
        if self.foot_screw_slot_margin <= 0:
            raise ValueError("The foot screws must not bottom in the rail slot")
        if self.lug_screw_length - self.joining_plate_thickness >= self.rail_slot_depth:
            raise ValueError("The lug screws must not bottom in the rail slot")
        if self.foot_diameter >= self.foot_screw_spacing - M5_WASHER_DIAMETER:
            raise ValueError("The rear foot must fit between its block's screw washers")
        for x, y in self.plate_holes().values():
            edge = min(self.plate_width / 2 - abs(x), y, self.plate_depth - y)
            if edge <= self.oversize_washer_diameter / 2:
                raise ValueError("Plate-hole washers must bear fully on the plate")


def _bore(diameter: float, length: float, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> Part:
    """Through-hole cutter along +z from z, overrunning both ends."""
    return z_cylinder(diameter, x, y, z - CUT_OVERRUN, z + length + CUT_OVERRUN)


def build_pivot_plate(p: FrameParameters | None = None) -> Part:
    """The front pivot plate with its two pivot holes and four yaw-bolt holes."""
    p = p or FrameParameters()
    p.validate()
    plate = box_between(
        -p.plate_width / 2,
        p.plate_width / 2,
        0,
        p.plate_depth,
        p.plate_top - p.plywood_thickness,
        p.plate_top,
    )
    for x, y in p.plate_holes().values():
        plate -= _bore(p.m5_clearance_diameter, p.plywood_thickness, x, y, p.plate_bottom)
    return plate


def build_foot_block(p: FrameParameters | None = None) -> Part:
    """One rear foot block, centered on x=y=0 with its length along y and its top (rail) face at z=0."""
    p = p or FrameParameters()
    p.validate()
    block = floor_box(p.foot_block_width, p.foot_block_length, p.plywood_thickness, z=-p.plywood_thickness)
    for y in (-p.foot_screw_spacing / 2, p.foot_screw_spacing / 2):
        block -= _bore(p.m5_clearance_diameter, p.plywood_thickness, 0, y, -p.plywood_thickness)
    return block


def build_joining_plate(p: FrameParameters | None = None) -> Part:
    """A 3-hole joining plate, centered on x=y=0 with its length along y and its bottom face at z=0."""
    p = p or FrameParameters()
    plate = floor_box(p.joining_plate_width, p.joining_plate_length, p.joining_plate_thickness)
    for hole in (-1, 0, 1):
        plate -= _bore(
            p.m5_clearance_diameter, p.joining_plate_thickness, 0, hole * p.joining_plate_hole_pitch
        )
    return plate


def _ring(outer_diameter: float, inner_diameter: float, height: float) -> Part:
    return z_cylinder(outer_diameter, 0, 0, 0, height) - _bore(inner_diameter, height)


def _rail_assembly(p: FrameParameters, name: str) -> Compound:
    """A rail and everything that yaws with it, in the rail frame (see FrameParameters.rail_location)."""
    # Everything on the rail lies aft of the pivot, at negative y.
    lug_center = -p.joining_plate_hole_pitch
    block_y = -p.foot_block_center
    block_bottom = p.plate_bottom
    parts = [
        labeled(
            build_rail(p.rail_length, p.rail_profile()),
            "Rail",
            BLACK_ANODIZED,
            Pos(0, -(p.rail_front_setback + p.rail_length / 2), 0),
        ),
        labeled(build_joining_plate(p), "Pivot lug", METAL, Pos(0, lug_center, 0)),
        labeled(build_foot_block(p), "Foot block", PLYWOOD, Pos(0, block_y, p.plate_top)),
        labeled(mcmaster_8215k2(), "Foot", SORBOTHANE, Pos(0, block_y, block_bottom)),
    ]
    for index, y in enumerate((lug_center, lug_center - p.joining_plate_hole_pitch), start=1):
        head_down = Pos(0, y, p.joining_plate_thickness) * Rot(X=180)
        parts.append(
            labeled(m5_socket_screw(p.lug_screw_length), f"Lug screw {index}", STEEL_GRAY, head_down)
        )
    for index, offset in enumerate((-p.foot_screw_spacing / 2, p.foot_screw_spacing / 2), start=1):
        y = block_y + offset
        under_head = block_bottom - p.foot_washer_stack
        for layer in range(p.foot_washers_per_screw):
            z = under_head + layer * M5_WASHER_THICKNESS
            parts.append(
                labeled(
                    mcmaster_93475a240(), f"Foot screw {index} washer {layer + 1}", STEEL_GRAY, Pos(0, y, z)
                )
            )
        parts.append(
            labeled(
                m5_socket_screw(p.foot_screw_length),
                f"Foot screw {index}",
                STEEL_GRAY,
                Pos(0, y, under_head),
            )
        )
    return assembly(f"{name} rail assembly", parts)


def _plate_assembly(p: FrameParameters) -> Compound:
    """The pivot plate and everything fixed to it: front foot, pivot stacks, yaw straps and their bolts."""
    under_head = p.plate_bottom - p.oversize_washer_thickness
    spacer = _ring(p.pivot_spacer_outer_diameter, p.pivot_spacer_inner_diameter, p.pivot_spacer_length)
    strip = floor_box(p.joining_plate_width, p.friction_strip_length, p.friction_strip_thickness)

    parts = [
        labeled(build_pivot_plate(p), "Pivot plate", PLYWOOD),
        labeled(
            mcmaster_8215k2(),
            "Front foot",
            SORBOTHANE,
            Pos(0, p.plate_depth - p.pivot_setback, p.plate_bottom),
        ),
    ]

    def stack(label: str, x: float, y: float, top: float, nut: Compound) -> None:
        """Screw up through the plate at (x, y), with washers under the plate and on the surface at top."""
        for part, name, z, color in (
            (mcmaster_92290a265(), "screw", under_head, STEEL_GRAY),
            (mcmaster_91116a350(), "lower washer", under_head, STEEL_GRAY),
            (mcmaster_91116a350(), "upper washer", top, STEEL_GRAY),
            (nut, "nut", top + p.oversize_washer_thickness, BLACK_OXIDE),
        ):
            parts.append(labeled(part, f"{label} {name}", color, Pos(x, y, z)))

    for name, side in SIDES.items():
        x, y = p.pivot_center(side)
        stack(f"{name} pivot", x, y, p.joining_plate_thickness, mcmaster_93625a225())
        parts.append(labeled(spacer, f"{name} pivot spacer", STEEL_GRAY, Pos(x, y, p.plate_top)))

        # The strap lies across the nominal rail axis and stays there when the rail is yawed.
        x, y = p.strap_center(side)
        across_rail = Pos(x, y, 0) * Rot(Z=degrees(side * p.half_angle) + 90)
        parts.append(labeled(strip, f"{name} friction strip", RUBBER, across_rail))
        parts.append(
            labeled(
                build_joining_plate(p),
                f"{name} yaw strap",
                METAL,
                across_rail * Pos(0, 0, p.strap_bottom),
            )
        )
    for label, (x, y) in p.plate_holes().items():
        if label.endswith("yaw"):
            stack(label, x, y, p.strap_top, mcmaster_92815a202())
    return assembly("Pivot plate assembly", parts)


def build_frame_assembly(
    p: FrameParameters | None = None, left_yaw: float = 0.0, right_yaw: float = 0.0
) -> Compound:
    """The assembled frame, each rail yawed outward from its nominal direction by the given degrees."""
    p = p or FrameParameters()
    p.validate()
    children = [_plate_assembly(p)]
    for (name, side), yaw in zip(SIDES.items(), (left_yaw, right_yaw)):
        children.append(place(p.rail_location(side, yaw * pi / 180), _rail_assembly(p, name)))
    return assembly("Tabletop frame", children)

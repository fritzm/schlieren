"""Preliminary common cassette blank, design §8.6.

XY is the cassette plane; z=0 is the rear sliding datum.
The front is +Z. Bevel dimensions match the provisional carriage, not a
physically qualified fit. Integral cleats and rear countersinks are universal;
two removable clamp bars and hardware references are available as an assembly.
"""

from dataclasses import dataclass
from math import cos, isfinite, pi, radians, tan

from build123d import (
    Axis,
    Circle,
    Plane,
    Polygon,
    Pos,
    RegularPolygon,
    Rot,
    extrude,
    fillet,
)

from schlieren.cad import assembly, floor_box, labeled, z_cone, z_cylinder
from schlieren.hardware import M3_NUT_ACROSS_FLATS, M3_NUT_THICKNESS
from schlieren.palette import HARDWARE_GRAY, PRINTED_AZURE, PRINTED_ORANGE, RUBBER
from schlieren.standards import INCH


@dataclass(frozen=True)
class CassetteParameters:
    size: float = 64.0
    thickness: float = 5.0
    aperture_diameter: float = 24.0
    bevel_depth: float = 1.25  # Provisional axial depth on front edges only.
    bevel_angle: float = 27.5  # Provisional angle measured from cassette plane.
    cleat_x: float = 25.0  # Provisional opposed pair on aperture X centerline.
    cleat_base_diameter: float = 3.5
    cleat_top_diameter: float = 5.0
    cleat_height: float = 3.0  # Above the nominal 5 mm cassette body.
    cleat_top_round: float = 0.5
    clamp_hole_x: float = 27.0  # Provisional; outside measured 38.99 mm blade length.
    clamp_hole_y: float = 12.0  # Bars must bridge around the optical aperture.
    screw_diameter: float = 3.0
    screw_diametral_clearance: float = 0.4
    screw_head_diameter: float = 6.0
    countersink_diametral_clearance: float = 0.2

    @property
    def clamp_holes(self):
        return [(sx * self.clamp_hole_x, sy * self.clamp_hole_y) for sx in (-1, 1) for sy in (-1, 1)]

    @property
    def bore_diameter(self):
        return self.screw_diameter + self.screw_diametral_clearance

    @property
    def countersink_diameter(self):
        return self.screw_head_diameter + self.countersink_diametral_clearance

    @property
    def countersink_depth(self):
        # 90-degree included angle; depth to intersection with clearance bore.
        # The catalog 1.7 mm head height includes more than this conical relief.
        return (self.countersink_diameter - self.bore_diameter) / 2

    @property
    def bevel_inset(self):
        return self.bevel_depth / tan(radians(self.bevel_angle))

    def validate(self):
        if any(not isfinite(v) or v <= 0 for v in vars(self).values()):
            raise ValueError("Cassette dimensions must be finite and positive")
        if not 0 < self.bevel_angle < 90:
            raise ValueError("Bevel angle must lie between 0 and 90 degrees")
        if self.bevel_depth >= self.thickness:
            raise ValueError("Bevel must preserve the rear datum")
        front_half = self.size / 2 - self.bevel_inset
        if not 0 < self.countersink_depth < self.thickness - self.bevel_depth:
            raise ValueError("Countersink must leave cassette material above it")
        if max(self.clamp_hole_x, self.clamp_hole_y) + self.countersink_diameter / 2 >= self.size / 2:
            raise ValueError("Countersinks must remain inside the rear perimeter")
        if self.cleat_top_diameter <= self.cleat_base_diameter:
            raise ValueError("Cleats must widen toward the top")
        if not (
            self.aperture_diameter / 2 + self.cleat_top_diameter / 2
            < self.cleat_x
            < front_half - self.cleat_top_diameter / 2
        ):
            raise ValueError("Cleats must clear aperture and perimeter bevel")
        if self.cleat_top_round >= min(self.cleat_height / 2, self.cleat_base_diameter / 2):
            raise ValueError("Cleat rounding is too large")
        if self.aperture_diameter / 2 >= front_half:
            raise ValueError("Aperture must leave a continuous front land")


def build_cassette(p=None):
    """Return the blank at its own rear datum, ready for STEP/STL export."""
    p = p or CassetteParameters()
    p.validate()
    half = p.size / 2
    shoulder = p.thickness - p.bevel_depth
    front_half = half - p.bevel_inset
    profile = [
        (-half, 0),
        (half, 0),
        (half, shoulder),
        (front_half, p.thickness),
        (-front_half, p.thickness),
        (-half, shoulder),
    ]
    pair = extrude(Plane.YZ.offset(-half) * Polygon(*profile, align=None), amount=p.size)
    blank = pair & (Rot(Z=90) * pair)
    blank -= z_cylinder(p.aperture_diameter, 0, 0, 0, p.thickness)
    for x, y in p.clamp_holes:
        blank -= z_cylinder(p.bore_diameter, x, y, 0, p.thickness)
        blank -= z_cone(p.countersink_diameter, p.bore_diameter, x, y, 0, p.countersink_depth)
    for x in (-p.cleat_x, p.cleat_x):
        cleat = z_cone(
            p.cleat_base_diameter, p.cleat_top_diameter, x, 0, p.thickness, p.thickness + p.cleat_height
        )
        cleat = fillet(cleat.edges().sort_by(Axis.Z)[-1], p.cleat_top_round)
        blank += cleat
    return blank


@dataclass(frozen=True)
class ClampBarParameters:
    """Provisional bar geometry and simplified assembly hardware, all in mm."""

    thickness: float = 4.0
    end_width: float = 8.0
    inner_edge_y: float = 12.5  # Clear the Ø24 opening by 0.5 mm.
    outer_edge_y: float = 17.5  # Bear inboard of the blade's folded spine.
    bridge_half_length: float = 20.0
    end_relief_start_x: float = 21.0
    end_relief_depth: float = 1.6  # Clears plunger lips even with thin media.
    corner_radius: float = 0.5
    epdm_thickness: float = INCH / 32  # Uncompressed reference only.
    media_lift: float = 0.6  # Provisional bar elevation, NOT measured blade thickness.
    washer_od: float = 7.0
    washer_id: float = 3.2
    washer_thickness: float = 0.5
    nut_af: float = M3_NUT_ACROSS_FLATS
    nut_height: float = M3_NUT_THICKNESS
    screw_length: float = 14.0  # Overall, including head.
    head_recess: float = 0.1

    def bar_bottom(self, cassette):
        return cassette.thickness + self.media_lift + self.epdm_thickness


def build_clamp_bar(p=None, b=None):
    """One removable bar, underside at z=0, in its +Y cassette orientation."""
    p = p or CassetteParameters()
    b = b or ClampBarParameters()
    p.validate()
    if b.end_relief_depth >= b.thickness or b.inner_edge_y <= p.aperture_diameter / 2:
        raise ValueError("Bar must retain material over the relief and clear the aperture")
    x, y, half = p.clamp_hole_x, p.clamp_hole_y, b.end_width / 2
    points = [
        (-x - half, y - half),
        (-x + half, y - half),
        (-b.bridge_half_length, b.inner_edge_y),
        (b.bridge_half_length, b.inner_edge_y),
        (x - half, y - half),
        (x + half, y - half),
        (x + half, b.outer_edge_y),
        (-x - half, b.outer_edge_y),
    ]
    bar = extrude(Polygon(*points, align=None), amount=b.thickness)
    bar = fillet(bar.edges().filter_by(Axis.Z), b.corner_radius)
    for sign in (-1, 1):
        relief_width = x + half - b.end_relief_start_x
        relief_x = sign * (b.end_relief_start_x + relief_width / 2)
        bar -= floor_box(relief_width, p.size, b.end_relief_depth, x=relief_x)
        bar -= z_cylinder(p.bore_diameter, sign * x, y, 0, b.thickness)
    return bar


def build_cassette_assembly(p=None, b=None):
    """Base, two identical bars, and toggleable simplified hardware/EPDM references.

    Hardware is unthreaded envelope geometry, not fabrication CAD. Media is
    omitted: media_lift describes a provisional setup elevation only.
    """
    p = p or CassetteParameters()
    b = b or ClampBarParameters()
    bottom = b.bar_bottom(p)
    bar = Pos(0, 0, bottom) * build_clamp_bar(p, b)
    pad = floor_box(
        2 * b.bridge_half_length,
        b.outer_edge_y - b.inner_edge_y,
        b.epdm_thickness,
        y=(b.inner_edge_y + b.outer_edge_y) / 2,
        z=bottom - b.epdm_thickness,
    )
    hardware = []
    for i, x in enumerate((-p.clamp_hole_x, p.clamp_hole_x), 1):
        y = p.clamp_hole_y
        washer_z = bottom + b.thickness
        washer = extrude(
            Pos(x, y, washer_z) * (Circle(b.washer_od / 2) - Circle(b.washer_id / 2)),
            amount=b.washer_thickness,
        )
        nut = extrude(
            Pos(x, y, washer_z + b.washer_thickness)
            * (RegularPolygon(b.nut_af / cos(pi / 6) / 2, 6) - Circle(p.screw_diameter / 2)),
            amount=b.nut_height,
        )
        # Ideal 90° head cone and plain shank; drive socket/threads omitted.
        head_depth = (p.screw_head_diameter - p.screw_diameter) / 2
        head_end = b.head_recess + head_depth
        screw = z_cone(p.screw_head_diameter, p.screw_diameter, x, y, b.head_recess, head_end)
        screw += z_cylinder(p.screw_diameter, x, y, head_end, b.head_recess + b.screw_length)
        hardware += [(f"Washer {i}", washer), (f"Nut {i}", nut), (f"Screw {i}", screw)]
    children = [labeled(build_cassette(p), "Cassette base", PRINTED_ORANGE)]
    for sign, label in ((1, "Upper clamp"), (-1, "Lower clamp")):
        loc = Rot(Z=0 if sign == 1 else 180)
        clamp = [
            labeled(bar, "Printed bar", PRINTED_AZURE, loc),
            labeled(pad, "EPDM reference", RUBBER, loc),
            *(labeled(part, name, HARDWARE_GRAY, loc) for name, part in hardware),
        ]
        children.append(assembly(label, clamp))
    return assembly("Cassette assembly (preliminary)", children)

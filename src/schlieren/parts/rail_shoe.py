"""Common rail shoe; design §§3–5 (§5.3).

Coordinates: x across the rail, y along it, z up; rail top is z=0.
The post is at x=y=0. Both ears point toward +x: nut at +y, screw at -y.
Envelope, hole layout, and fabrication allowances are fit-tested on printed shoes.
No ABS lies between the post bottom and the metal datum disc.
"""

from dataclasses import dataclass
from math import cos, pi, sqrt

from build123d import (
    Align,
    Axis,
    Box,
    Compound,
    Cylinder,
    GeomType,
    Part,
    Pos,
    RegularPolygon,
    extrude,
    fillet,
)

from schlieren.cad import FROM_CORNER, ON_FLOOR, along_x, along_y, assembly, labeled


@dataclass(frozen=True)
class RailShoeParameters:
    # Physical interfaces from docs/design/.
    rail_width: float = 20.0
    rail_height: float = 20.0
    post_diameter: float = 12.7
    datum_disc_diameter: float = 0.75 * 25.4
    datum_disc_thickness: float = 0.010 * 25.4
    clamp_screw_length: float = 12.0
    clamp_nut_across_flats: float = 5.5
    clamp_nut_thickness: float = 2.4

    # ABS fabrication allowances, set by fit test (not measured shrink compensation).
    rail_lateral_clearance_per_side: float = 0.20
    datum_disc_diametral_clearance: float = 1.0
    post_diametral_clearance: float = 0.10
    nut_across_flats_clearance: float = 0.30
    nut_axial_clearance: float = 0.30
    m5_clearance_diameter: float = 5.5
    m3_clearance_diameter: float = 3.3

    # Part geometry.
    length: float = 30.0
    datum_counterbore_depth: float = 1.0
    side_wall: float = 5.0
    skirt_depth: float = 18.0
    bridge_thickness: float = 5.0
    outside_corner_radius: float = 2.0
    collar_outer_radius: float = 10.5
    collar_height: float = 15.0
    collar_root_fillet: float = 2.0
    ear_width: float = 10.0
    ear_height: float = 10.0
    nut_ear_thickness: float = 4.5
    screw_ear_thickness: float = 3.5
    ear_root_fillet: float = 1.5
    split_gap: float = 1.0
    split_relief_height: float = 2.5  # Ear bottom to relief-bore center, downward.
    split_relief_radius: float = 2.0

    @property
    def rail_opening(self) -> float:
        return self.rail_width + 2 * self.rail_lateral_clearance_per_side

    @property
    def width(self) -> float:
        return self.rail_opening + 2 * self.side_wall

    @property
    def bridge_top(self) -> float:
        return self.bridge_thickness

    @property
    def collar_bottom(self) -> float:
        return self.bridge_top

    @property
    def collar_top(self) -> float:
        return self.collar_bottom + self.collar_height

    @property
    def ear_bottom(self) -> float:
        return self.collar_top - self.ear_height

    @property
    def split_relief_z(self) -> float:
        return self.ear_bottom - self.split_relief_height

    @property
    def datum_counterbore_diameter(self) -> float:
        return self.datum_disc_diameter + self.datum_disc_diametral_clearance

    @property
    def post_bore(self) -> float:
        return self.post_diameter + self.post_diametral_clearance

    @property
    def nut_pocket_depth(self) -> float:
        return self.clamp_nut_thickness + self.nut_axial_clearance

    def validate(self) -> None:
        if any(value <= 0 for value in vars(self).values()):
            raise ValueError("Dimensions and fabrication allowances must be positive")
        if not self.datum_disc_thickness < self.datum_counterbore_depth < self.bridge_thickness:
            raise ValueError("Counterbore must clear the disc and leave a bridge roof")
        if self.datum_counterbore_diameter >= min(self.length, self.width):
            raise ValueError("Counterbore must leave seating lands and outer walls")
        if self.rail_opening <= self.datum_disc_diameter:
            raise ValueError("The datum disc must fit inside the rail opening")
        if not self.rail_height / 2 + self.m5_clearance_diameter / 2 < self.skirt_depth < self.rail_height:
            raise ValueError("Skirts must surround side-slot holes and clear the rail bottom")
        if self.collar_outer_radius + self.collar_root_fillet >= min(self.width, self.length) / 2:
            raise ValueError("Collar root must fit on the bridge")
        if self.post_bore / 2 >= self.collar_outer_radius:
            raise ValueError("Post bore must leave a collar wall")
        if (
            self.split_gap / 2 + max(self.nut_ear_thickness, self.screw_ear_thickness)
            >= self.collar_outer_radius
        ):
            raise ValueError("The full thickness of each ear must intersect the collar")
        if self.ear_height > self.collar_height:
            raise ValueError("Ear height must fit within the collar height")
        if self.split_relief_radius <= self.split_gap / 2:
            raise ValueError("Relief bore must be wider than the split")
        if self.split_relief_z - self.split_relief_radius <= -self.skirt_depth:
            raise ValueError("Split relief must leave material below it in the skirt")
        if self.nut_pocket_depth >= self.nut_ear_thickness:
            raise ValueError("Nut pocket must leave an inner ear wall")
        pocket_across_corners = (self.clamp_nut_across_flats + self.nut_across_flats_clearance) / cos(pi / 6)
        if pocket_across_corners >= self.ear_width or (
            self.clamp_nut_across_flats + self.nut_across_flats_clearance >= self.ear_height
        ):
            raise ValueError("Nut pocket must fit within the ear face")
        if self.m3_clearance_diameter >= min(self.ear_width, self.ear_height):
            raise ValueError("Screw bore must fit within the ear face")


SHOE_COLOR = (0.8, 0.65, 0.3)
REFERENCE_COLOR = (0.6, 0.6, 0.6)


def build_rail_shoe(p: RailShoeParameters | None = None) -> Part:
    """Return one printable solid in assembly coordinates, without hardware."""
    p = p or RailShoeParameters()
    p.validate()
    overrun = 1.0

    shoe = Pos(0, 0, -p.skirt_depth) * Box(p.width, p.length, p.skirt_depth + p.bridge_top, align=ON_FLOOR)
    shoe = fillet(shoe.edges().filter_by(Axis.Z), p.outside_corner_radius)

    rail_void = Pos(0, 0, -p.skirt_depth - overrun) * Box(
        p.rail_opening, p.length + 2 * overrun, p.skirt_depth + overrun, align=ON_FLOOR
    )
    shoe -= rail_void

    counterbore = Pos(0, 0, -overrun) * Cylinder(
        p.datum_counterbore_diameter / 2, p.datum_counterbore_depth + overrun, align=ON_FLOOR
    )
    shoe -= counterbore

    collar = Pos(0, 0, p.collar_bottom) * Cylinder(p.collar_outer_radius, p.collar_height, align=ON_FLOOR)
    shoe += collar

    root = [
        e
        for e in shoe.edges().filter_by(GeomType.CIRCLE)
        if abs(e.arc_center.Z - p.bridge_top) < 1e-6 and abs(e.radius - p.collar_outer_radius) < 1e-6
    ]
    shoe = fillet(root, p.collar_root_fillet)

    # The collar reaches farthest in +x at the ear's inner (+y) face.
    # Measure ear_width from that circle intersection so the shortest
    # exposed x-edge is exactly ear_width. Start at x=0 to overlap the
    # collar positively; the subsequent post-bore cut removes the interior.
    ear_y_min = p.split_gap / 2
    collar_x_at_inner_face = sqrt(p.collar_outer_radius**2 - ear_y_min**2)
    ear_x_end = collar_x_at_inner_face + p.ear_width
    nut_ear = Pos(0, ear_y_min, p.ear_bottom) * Box(
        ear_x_end, p.nut_ear_thickness, p.ear_height, align=FROM_CORNER
    )
    shoe += nut_ear

    screw_ear = Pos(0, -ear_y_min - p.screw_ear_thickness, p.ear_bottom) * Box(
        ear_x_end, p.screw_ear_thickness, p.ear_height, align=FROM_CORNER
    )
    shoe += screw_ear

    # Only the two outer vertical, concave ear/collar junctions. Leave the
    # split-facing edges sharp so the relaxed gap and inner width stay fixed.
    outer_root_edges = []
    for outer_y in (ear_y_min + p.nut_ear_thickness, -ear_y_min - p.screw_ear_thickness):
        root_x = sqrt(p.collar_outer_radius**2 - outer_y**2)
        for edge in shoe.edges().filter_by(Axis.Z):
            center = edge.center()
            if (
                abs(center.X - root_x) < 1e-6
                and abs(center.Y - outer_y) < 1e-6
                and abs(center.Z - (p.ear_bottom + p.collar_top) / 2) < 1e-6
            ):
                outer_root_edges.append(edge)
    if len(outer_root_edges) != 2:
        raise ValueError("Expected two outer ear-to-collar root edges")
    shoe = fillet(outer_root_edges, p.ear_root_fillet)

    bore = Pos(0, 0, -overrun) * Cylinder(p.post_bore / 2, p.collar_top + 2 * overrun, align=ON_FLOOR)
    shoe -= bore

    # Radial split toward +x, centered on y=0. The rectangle ends at
    # the relief center; the circular bore extends another radius below it.
    # Include the bridge/skirt if the requested relief depth reaches them.
    split_length = max(ear_x_end, p.width / 2) + overrun
    split = Pos(0, 0, p.split_relief_z) * Box(
        split_length,
        p.split_gap,
        p.collar_top - p.split_relief_z + overrun,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    relief = along_x((0, 0, p.split_relief_z)) * Cylinder(p.split_relief_radius, split_length, align=ON_FLOOR)
    shoe -= split
    shoe -= relief

    side_holes = along_x((-p.width / 2 - overrun, 0, -p.rail_height / 2)) * Cylinder(
        p.m5_clearance_diameter / 2, p.width + 2 * overrun, align=ON_FLOOR
    )
    shoe -= side_holes

    # Center on the exposed rectangular inner ear faces, whose x-span is
    # collar_x_at_inner_face .. ear_x_end. Both features share a y-axis.
    clamp_x = collar_x_at_inner_face + p.ear_width / 2
    clamp_z = p.ear_bottom + p.ear_height / 2
    screw_outer_y = -ear_y_min - p.screw_ear_thickness
    nut_outer_y = ear_y_min + p.nut_ear_thickness
    clamp_hole = along_y((clamp_x, screw_outer_y - overrun, clamp_z)) * Cylinder(
        p.m3_clearance_diameter / 2, nut_outer_y - screw_outer_y + 2 * overrun, align=ON_FLOOR
    )
    # Nut inserts from +y; the inner wall carries its axial clamp load.
    # Hex vertices lie along x, with horizontal flats in z.
    nut_across_corners = (p.clamp_nut_across_flats + p.nut_across_flats_clearance) / cos(pi / 6)
    nut = extrude(
        along_y((clamp_x, nut_outer_y - p.nut_pocket_depth, clamp_z))
        * RegularPolygon(nut_across_corners / 2, 6),
        amount=p.nut_pocket_depth + overrun,
    )
    shoe -= clamp_hole
    shoe -= nut

    if len(shoe.solids()) != 1 or not shoe.is_valid:
        raise ValueError("Rail shoe did not produce one valid solid")

    return shoe


def reference_parts(p: RailShoeParameters | None = None) -> dict[str, Part]:
    p = p or RailShoeParameters()
    return {
        "rail envelope": Pos(0, 0, -p.rail_height)
        * Box(p.rail_width, p.length + 30, p.rail_height, align=ON_FLOOR),
        "datum disc": Cylinder(p.datum_disc_diameter / 2, p.datum_disc_thickness, align=ON_FLOOR),
        "TR50/M post envelope": Pos(0, 0, p.datum_disc_thickness)
        * Cylinder(p.post_diameter / 2, 50.0, align=ON_FLOOR),
    }


def viewer_assembly(shoe: Part, p: RailShoeParameters | None = None) -> Compound:
    refs = reference_parts(p)
    rparts = assembly(
        "Reference parts",
        [
            labeled(refs["rail envelope"], "Rail", REFERENCE_COLOR),
            labeled(refs["datum disc"], "Datum disc", REFERENCE_COLOR),
            labeled(refs["TR50/M post envelope"], "TR50_M", REFERENCE_COLOR),
        ],
    )
    return assembly("Rail shoe prototype", [labeled(shoe, "Shoe", SHOE_COLOR), rparts])

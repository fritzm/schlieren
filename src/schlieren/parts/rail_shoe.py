"""Common rail shoe; design §§3–5 (§5.3).

Coordinates: a §3.4 rail frame, +x across the rail (right, seen from above with the mirror ahead), +y along
it toward the mirror, z up; rail top is z=0.
The post is at x=y=0. Both ears point toward +x: nut at +y, screw at -y.
Envelope, hole layout, and fabrication allowances are fit-tested on printed shoes.
No PLA lies between the post bottom and the metal datum disc.
"""

from dataclasses import dataclass
from math import cos, pi, sqrt

from build123d import (
    Axis,
    Compound,
    GeomType,
    Location,
    Part,
    Pos,
    Rot,
    fillet,
)

from schlieren.cad import (
    CUT_OVERRUN,
    assembly,
    box_between,
    floor_box,
    labeled,
    x_cylinder,
    y_cylinder,
    y_hex,
    z_cylinder,
)
from schlieren.hardware import M3_CLEARANCE_DIAMETER, M3_NUT_ACROSS_FLATS, M3_NUT_THICKNESS
from schlieren.palette import BLACK_ANODIZED, METAL, PRINTED_ORANGE, STEEL_GRAY
from schlieren.parts.rail import build_rail
from schlieren.standards import (
    DATUM_DISC_DIAMETER,
    DATUM_DISC_THICKNESS,
    NUT_POCKET_ACROSS_FLATS_CLEARANCE,
    OPTICAL_HEIGHT,
    POST_DIAMETER,
    POST_LENGTH,
)
from schlieren.validation import require_positive_dimensions
from schlieren.vendor_cad import (
    MCMASTER_93475A240_THICKNESS,
    SM1RC_M_THICKNESS,
    mcmaster_91292a114,
    mcmaster_91828a211,
    mcmaster_92290a228,
    mcmaster_93475a240,
    thorlabs_sm1rc_m,
    thorlabs_tr50_m,
)


@dataclass(frozen=True)
class RailShoeParameters:
    # Physical interfaces from docs/design/.
    rail_width: float = 20.0
    rail_height: float = 20.0
    post_diameter: float = POST_DIAMETER
    datum_disc_diameter: float = DATUM_DISC_DIAMETER
    datum_disc_thickness: float = DATUM_DISC_THICKNESS
    clamp_screw_length: float = 12.0
    clamp_nut_across_flats: float = M3_NUT_ACROSS_FLATS
    clamp_nut_thickness: float = M3_NUT_THICKNESS

    # PLA fabrication allowances, set by fit test (not measured shrink compensation).
    rail_lateral_clearance_per_side: float = 0.20
    datum_disc_diametral_clearance: float = 1.0
    post_diametral_clearance: float = 0.10
    nut_across_flats_clearance: float = NUT_POCKET_ACROSS_FLATS_CLEARANCE
    nut_axial_clearance: float = 0.30
    m5_clearance_diameter: float = 5.5
    m3_clearance_diameter: float = M3_CLEARANCE_DIAMETER

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
    def clamp_axis_x(self) -> float:
        """Split-clamp screw and nut axis x (the axis runs along y), centered on the exposed inner ear faces."""
        return sqrt(self.collar_outer_radius**2 - (self.split_gap / 2) ** 2) + self.ear_width / 2

    @property
    def clamp_axis_z(self) -> float:
        return self.ear_bottom + self.ear_height / 2

    @property
    def clamp_screw_outer_y(self) -> float:
        """Outer face of the screw ear, where the clamp screw head bears."""
        return -(self.split_gap / 2 + self.screw_ear_thickness)

    @property
    def clamp_nut_outer_y(self) -> float:
        """Outer face of the nut ear, where the nut pocket opens."""
        return self.split_gap / 2 + self.nut_ear_thickness

    @property
    def nut_pocket_depth(self) -> float:
        return self.clamp_nut_thickness + self.nut_axial_clearance

    def validate(self) -> None:
        require_positive_dimensions(self)
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


VIEWER_RAIL_OVERHANG = 15.0  # Rail shown beyond each end of the shoe.


def build_rail_shoe(p: RailShoeParameters | None = None) -> Part:
    """Return one printable solid in assembly coordinates, without hardware."""
    p = p or RailShoeParameters()
    p.validate()

    shoe = floor_box(p.width, p.length, p.skirt_depth + p.bridge_top, z=-p.skirt_depth)
    shoe = fillet(shoe.edges().filter_by(Axis.Z), p.outside_corner_radius)

    rail_void = floor_box(
        p.rail_opening,
        p.length + 2 * CUT_OVERRUN,
        p.skirt_depth + CUT_OVERRUN,
        z=-p.skirt_depth - CUT_OVERRUN,
    )
    shoe -= rail_void

    counterbore = z_cylinder(p.datum_counterbore_diameter, 0, 0, -CUT_OVERRUN, p.datum_counterbore_depth)
    shoe -= counterbore

    collar = z_cylinder(2 * p.collar_outer_radius, 0, 0, p.collar_bottom, p.collar_bottom + p.collar_height)
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
    nut_ear = box_between(
        0, ear_x_end, ear_y_min, ear_y_min + p.nut_ear_thickness, p.ear_bottom, p.ear_bottom + p.ear_height
    )
    shoe += nut_ear

    screw_ear = box_between(
        0,
        ear_x_end,
        -ear_y_min - p.screw_ear_thickness,
        -ear_y_min,
        p.ear_bottom,
        p.ear_bottom + p.ear_height,
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

    bore = z_cylinder(p.post_bore, 0, 0, -CUT_OVERRUN, p.collar_top + CUT_OVERRUN)
    shoe -= bore

    # Radial split toward +x, centered on y=0. The rectangle ends at
    # the relief center; the circular bore extends another radius below it.
    # Include the bridge/skirt if the requested relief depth reaches them.
    split_length = max(ear_x_end, p.width / 2) + CUT_OVERRUN
    split = box_between(
        0, split_length, -p.split_gap / 2, p.split_gap / 2, p.split_relief_z, p.collar_top + CUT_OVERRUN
    )
    relief = x_cylinder(2 * p.split_relief_radius, 0, p.split_relief_z, 0, split_length)
    shoe -= split
    shoe -= relief

    side_holes = x_cylinder(
        p.m5_clearance_diameter, 0, -p.rail_height / 2, -p.width / 2 - CUT_OVERRUN, p.width / 2 + CUT_OVERRUN
    )
    shoe -= side_holes

    # Center on the exposed rectangular inner ear faces, whose x-span is
    # collar_x_at_inner_face .. ear_x_end. Both features share a y-axis.
    clamp_x, clamp_z = p.clamp_axis_x, p.clamp_axis_z
    screw_outer_y, nut_outer_y = p.clamp_screw_outer_y, p.clamp_nut_outer_y
    clamp_hole = y_cylinder(
        p.m3_clearance_diameter, clamp_x, clamp_z, screw_outer_y - CUT_OVERRUN, nut_outer_y + CUT_OVERRUN
    )
    # Nut inserts from +y; the inner wall carries its axial clamp load.
    # Hex vertices lie along x, with horizontal flats in z.
    nut = y_hex(
        p.clamp_nut_across_flats + p.nut_across_flats_clearance,
        clamp_x,
        clamp_z,
        nut_outer_y - p.nut_pocket_depth,
        nut_outer_y + CUT_OVERRUN,
    )
    shoe -= clamp_hole
    shoe -= nut

    if len(shoe.solids()) != 1 or not shoe.is_valid:
        raise ValueError("Rail shoe did not produce one valid solid")

    return shoe


def reference_parts(p: RailShoeParameters | None = None) -> dict[str, Part]:
    """Nominal envelopes of the parts the shoe must clear; the post is its exact metric nominal cylinder."""
    p = p or RailShoeParameters()
    return {
        "rail envelope": floor_box(
            p.rail_width, p.length + 2 * VIEWER_RAIL_OVERHANG, p.rail_height, z=-p.rail_height
        ),
        "datum disc": z_cylinder(p.datum_disc_diameter, 0, 0, 0, p.datum_disc_thickness),
        "TR50/M post envelope": z_cylinder(
            p.post_diameter, 0, 0, p.datum_disc_thickness, p.datum_disc_thickness + POST_LENGTH
        ),
    }


def side_clamp_hardware(p: RailShoeParameters | None = None, y: float = 0.0) -> list[Part]:
    """The M5 × 12 side-slot screws with flat washers, one on each skirt, entering toward the rail at y.

    Each washer bears on its skirt's outer face and the screw on the washer; the screw axes are the side-hole
    axis, at mid rail height. Each is a labeled vendor model.
    """
    p = p or RailShoeParameters()
    parts = []
    for name, side in (("left", -1), ("right", 1)):
        axis = Pos(side * p.width / 2, y, -p.rail_height / 2) * Rot(Y=-90 * side)
        seat = axis * Pos(0, 0, -MCMASTER_93475A240_THICKNESS)
        parts.append(labeled(mcmaster_93475a240(), f"Side screw washer {name}", STEEL_GRAY, seat))
        parts.append(labeled(mcmaster_92290a228(), f"Side screw {name}", STEEL_GRAY, seat))
    return parts


def split_clamp_hardware(p: RailShoeParameters | None = None) -> list[Part]:
    """The M3 × 12 collar clamp screw and its hex nut: head on the screw ear, nut seated in its pocket."""
    p = p or RailShoeParameters()
    along_axis = Pos(p.clamp_axis_x, 0, p.clamp_axis_z) * Rot(X=-90)  # Local +z along +y.
    screw = Pos(0, 0, p.clamp_screw_outer_y) * mcmaster_91292a114()
    nut_seat = p.clamp_nut_outer_y - p.nut_pocket_depth  # The pocket bottom, which carries the clamp load.
    nut = Pos(0, 0, nut_seat) * Rot(Z=90) * mcmaster_91828a211()  # Corners along x, as pocketed.
    return [
        labeled(screw, "Clamp screw", STEEL_GRAY, along_axis),
        labeled(nut, "Clamp nut", STEEL_GRAY, along_axis),
    ]


def post_stack(
    loc: Location | None = None,
    *,
    y: float = 0.0,
    shoe: Part | None = None,
    ring: bool = False,
    clamp_hardware: bool = True,
    side_screws: bool = False,
    p: RailShoeParameters | None = None,
    optical_height: float = OPTICAL_HEIGHT,
    datum_thickness: float = DATUM_DISC_THICKNESS,
) -> list[Part]:
    """The common post stack as shown in assemblies, for the post at rail station y, moved by loc.

    Every fixture on a rail stands on this stack (§5): the TR50/M post on its datum disc and the printed rail
    shoe clamping the post foot, with the shoe's M3 split-clamp screw and nut. The side-slot M5 screws and
    washers that fix the shoe to the rail are added by side_screws, for the assemblies that show them. The slit head and cutoff carriage also hold their spigot in an SM1RC/M slip ring on the post top,
    centered on the post axis at optical_height (ring); the light source's own SMR1/M plays that part.

    Returns labeled children in the frame of loc (the §3.4 rail frame when loc is omitted). The hardware is
    labeled "Shoe ...", clear of any screws the fixture itself has. shoe is built when not given, and p
    gives the shoe's parameters.
    """
    on_rail = Location() if loc is None else loc
    at_post = on_rail * Pos(0, y, 0)
    parts = []
    if ring:
        ring_seat = on_rail * Pos(0, y - SM1RC_M_THICKNESS / 2, optical_height)
        parts.append(labeled(thorlabs_sm1rc_m(), "SM1RC M ring", BLACK_ANODIZED, ring_seat))
    parts.append(labeled(thorlabs_tr50_m(), "TR50 M post", METAL, at_post * Pos(0, 0, datum_thickness)))
    parts.append(labeled(build_rail_shoe(p) if shoe is None else shoe, "Rail shoe", PRINTED_ORANGE, at_post))
    hardware = split_clamp_hardware(p) if clamp_hardware else []
    hardware += side_clamp_hardware(p) if side_screws else []
    for part in hardware:
        parts.append(labeled(part, f"Shoe {part.label.lower()}", METAL, at_post))
    return parts


def viewer_assembly(shoe: Part, p: RailShoeParameters | None = None) -> Compound:
    """Shoe on a generic 2020 rail segment, with the datum disc and the post stack's vendor post and
    hardware (including the side-slot screws), all but the shoe grouped as reference parts."""
    p = p or RailShoeParameters()
    refs = reference_parts(p)
    stack = {part.label: part for part in post_stack(shoe=shoe, side_screws=True, p=p)}
    shoe_part = stack.pop("Rail shoe")
    rparts = assembly(
        "Reference parts",
        [
            labeled(build_rail(p.length + 2 * VIEWER_RAIL_OVERHANG), "Rail", STEEL_GRAY),
            labeled(refs["datum disc"], "Datum disc", STEEL_GRAY),
            *stack.values(),
        ],
    )
    return assembly("Rail shoe prototype", [shoe_part, rparts])

"""Exploratory common rail shoe, based on canonical design-status §§3–5.

Coordinates: x across the rail, y along it, z up; rail top is z=0.
The post is at x=y=0. Both ears point toward +x: nut at +y, screw at -y.
Envelope, hole count/layout, and fabrication allowances are provisional.
No ABS lies between the post bottom and the metal datum disc.
"""

from dataclasses import dataclass
from math import cos, pi, sqrt

import cadquery as cq


@dataclass(frozen=True)
class RailShoeParameters:
    # Physical interfaces from the canonical status document.
    rail_width: float = 20.0
    rail_height: float = 20.0
    post_diameter: float = 12.7
    datum_disc_diameter: float = 0.75 * 25.4
    datum_disc_thickness: float = 0.010 * 25.4
    clamp_screw_length: float = 12.0
    clamp_nut_across_flats: float = 5.5
    clamp_nut_thickness: float = 2.4

    # Provisional ABS fabrication allowances (not measured compensation).
    rail_lateral_clearance_per_side: float = 0.20
    datum_disc_diametral_clearance: float = 1.0
    post_diametral_clearance: float = 0.20
    nut_across_flats_clearance: float = 0.30
    nut_axial_clearance: float = 0.30
    m5_clearance_diameter: float = 5.5
    m3_clearance_diameter: float = 3.3

    # Provisional part geometry; tune through fit and clamp tests.
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


def build_rail_shoe(p: RailShoeParameters | None = None) -> cq.Workplane:
    """Return one printable solid in assembly coordinates, without hardware."""
    p = p or RailShoeParameters()
    p.validate()
    overrun = 1.0

    shoe = (
        cq.Workplane("XY", origin=(0, 0, -p.skirt_depth))
        .box(
            p.width,
            p.length,
            p.skirt_depth + p.bridge_top,
            centered=(True, True, False),
        )
        .edges("|Z")
        .fillet(p.outside_corner_radius)
    )

    rail_void = cq.Workplane("XY", origin=(0, 0, -p.skirt_depth - overrun)).box(
        p.rail_opening,
        p.length + 2 * overrun,
        p.skirt_depth + overrun,
        centered=(True, True, False),
    )
    shoe = shoe.cut(rail_void)

    counterbore = (
        cq.Workplane("XY", origin=(0, 0, -overrun))
        .circle(p.datum_counterbore_diameter / 2)
        .extrude(p.datum_counterbore_depth + overrun)
    )
    shoe = shoe.cut(counterbore)

    collar = (
        cq.Workplane("XY", origin=(0, 0, p.collar_bottom))
        .circle(p.collar_outer_radius)
        .extrude(p.collar_height)
    )
    shoe = shoe.union(collar)

    root = [
        e
        for e in shoe.edges().vals()
        if e.geomType() == "CIRCLE"
        and abs(e.Center().z - p.bridge_top) < 1e-6
        and abs(e.radius() - p.collar_outer_radius) < 1e-6
    ]
    shoe = shoe.newObject(root).fillet(p.collar_root_fillet)

    # The collar reaches farthest in +x at the ear's inner (+y) face.
    # Measure ear_width from that circle intersection so the shortest
    # exposed x-edge is exactly ear_width. Start at x=0 to overlap the
    # collar positively; the subsequent post-bore cut removes the interior.
    ear_y_min = p.split_gap / 2
    collar_x_at_inner_face = sqrt(p.collar_outer_radius**2 - ear_y_min**2)
    ear_x_end = collar_x_at_inner_face + p.ear_width
    nut_ear = cq.Workplane("XY", origin=(0, ear_y_min, p.ear_bottom)).box(
        ear_x_end,
        p.nut_ear_thickness,
        p.ear_height,
        centered=(False, False, False),
    )
    shoe = shoe.union(nut_ear)

    screw_ear = cq.Workplane("XY", origin=(0, -ear_y_min - p.screw_ear_thickness, p.ear_bottom)).box(
        ear_x_end,
        p.screw_ear_thickness,
        p.ear_height,
        centered=(False, False, False),
    )
    shoe = shoe.union(screw_ear)

    # Only the two outer vertical, concave ear/collar junctions. Leave the
    # split-facing edges sharp so the relaxed gap and inner width stay fixed.
    outer_root_edges = []
    for outer_y in (ear_y_min + p.nut_ear_thickness, -ear_y_min - p.screw_ear_thickness):
        root_x = sqrt(p.collar_outer_radius**2 - outer_y**2)
        for edge in shoe.edges("|Z").vals():
            center = edge.Center()
            if (
                abs(center.x - root_x) < 1e-6
                and abs(center.y - outer_y) < 1e-6
                and abs(center.z - (p.ear_bottom + p.collar_top) / 2) < 1e-6
            ):
                outer_root_edges.append(edge)
    if len(outer_root_edges) != 2:
        raise ValueError("Expected two outer ear-to-collar root edges")
    shoe = shoe.newObject(outer_root_edges).fillet(p.ear_root_fillet)

    bore = (
        cq.Workplane("XY", origin=(0, 0, -overrun))
        .circle(p.post_bore / 2)
        .extrude(p.collar_top + 2 * overrun)
    )
    shoe = shoe.cut(bore)

    # Radial split toward +x, centered on y=0. The rectangle ends at
    # the relief center; the circular bore extends another radius below it.
    # Include the bridge/skirt if the requested relief depth reaches them.
    split_length = max(ear_x_end, p.width / 2) + overrun
    split = cq.Workplane("XY", origin=(0, 0, p.split_relief_z)).box(
        split_length,
        p.split_gap,
        p.collar_top - p.split_relief_z + overrun,
        centered=(False, True, False),
    )
    relief = cq.Solid.makeCylinder(
        p.split_relief_radius,
        split_length,
        cq.Vector(0, 0, p.split_relief_z),
        cq.Vector(1, 0, 0),
    )
    shoe = shoe.cut(split).cut(relief)

    side_holes = cq.Solid.makeCylinder(
        p.m5_clearance_diameter / 2,
        p.width + 2 * overrun,
        cq.Vector(-p.width / 2 - overrun, 0, -p.rail_height / 2),
        cq.Vector(1, 0, 0),
    )
    shoe = shoe.cut(side_holes)

    # Center on the exposed rectangular inner ear faces, whose x-span is
    # collar_x_at_inner_face .. ear_x_end. Both features share a y-axis.
    clamp_x = collar_x_at_inner_face + p.ear_width / 2
    clamp_z = p.ear_bottom + p.ear_height / 2
    screw_outer_y = -ear_y_min - p.screw_ear_thickness
    nut_outer_y = ear_y_min + p.nut_ear_thickness
    clamp_hole = cq.Solid.makeCylinder(
        p.m3_clearance_diameter / 2,
        nut_outer_y - screw_outer_y + 2 * overrun,
        cq.Vector(clamp_x, screw_outer_y - overrun, clamp_z),
        cq.Vector(0, 1, 0),
    )
    # Nut inserts from +y; the inner wall carries its axial clamp load.
    # Hex vertices lie along x, with horizontal flats in z.
    nut_plane = cq.Plane(
        origin=(clamp_x, nut_outer_y - p.nut_pocket_depth, clamp_z),
        xDir=(1, 0, 0),
        normal=(0, 1, 0),
    )
    nut = (
        cq.Workplane(nut_plane)
        .polygon(6, (p.clamp_nut_across_flats + p.nut_across_flats_clearance) / cos(pi / 6))
        .extrude(p.nut_pocket_depth + overrun)
    )
    shoe = shoe.cut(clamp_hole).cut(nut)

    shoe = shoe.clean()
    if len(shoe.solids().vals()) != 1 or not shoe.val().isValid():
        raise ValueError("Rail shoe did not produce one valid solid")

    return shoe


def reference_parts(p: RailShoeParameters | None = None) -> dict[str, cq.Workplane]:
    p = p or RailShoeParameters()
    return {
        "rail envelope": cq.Workplane("XY", origin=(0, 0, -p.rail_height)).box(
            p.rail_width, p.length + 30, p.rail_height, centered=(True, True, False)
        ),
        "datum disc": cq.Workplane("XY").circle(p.datum_disc_diameter / 2).extrude(p.datum_disc_thickness),
        "TR50/M post envelope": cq.Workplane("XY", origin=(0, 0, p.datum_disc_thickness))
        .circle(p.post_diameter / 2)
        .extrude(50.0),
    }


def viewer_assembly(shoe: cq.Workplane, p: RailShoeParameters | None = None) -> cq.Assembly:
    refs = reference_parts(p)
    assembly = cq.Assembly(name="Rail shoe prototype")
    assembly.add(shoe, name="Shoe", color=cq.Color(0.8, 0.65, 0.3))
    rparts = cq.Assembly(name="Reference parts")
    rparts.add(
        refs["rail envelope"],
        name="Rail",
        color=cq.Color(0.6, 0.6, 0.6),
    )
    rparts.add(refs["datum disc"], name="Datum disc", color=cq.Color(0.6, 0.6, 0.6))
    rparts.add(refs["TR50/M post envelope"], name="TR50_M", color=cq.Color(0.6, 0.6, 0.6))
    assembly.add(rparts)
    return assembly

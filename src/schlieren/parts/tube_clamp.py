"""Provisional ABS SM1 tube retaining clamp; z is the tube axis (millimeters).

SM1 tube nominal OD is 1.20 inches, not its 1-inch optic size or thread OD.
Source: https://punchout.thorlabs.com/NewGroupPage9.cfm?ObjectGroup_ID=1533&Visual_ID=1964
Measure the actual tube and fit-test ABS before making both retaining clamps.
The 8 mm axial envelope accommodates the M3 nut with 1.1 mm edge margins;
this is an exploratory departure from the status Doc's approximate 4–5 mm.
"""

from dataclasses import dataclass
from math import cos, pi, sqrt

import cadquery as cq


@dataclass(frozen=True)
class TubeClampParameters:
    tube_diameter: float = 1.20 * 25.4  # Manufacturer nominal; not a measurement.
    tube_diametral_clearance: float = 0.25
    axial_width: float = 8.0
    radial_wall: float = 3.5
    split_gap: float = 1.0
    ear_width: float = 9.0
    screw_ear_thickness: float = 5.0
    nut_ear_thickness: float = 5.0
    ear_root_fillet: float = 1.0
    outer_rim_fillet: float = 0.5
    # Same hardware as the rail shoe: 91292A114 screw, 91828A211 nut.
    screw_length: float = 12.0
    screw_clearance_diameter: float = 3.3
    nut_across_flats: float = 5.5
    nut_thickness: float = 2.4
    nut_across_flats_clearance: float = 0.30
    nut_axial_clearance: float = 0.30

    @property
    def bore_diameter(self) -> float:
        return self.tube_diameter + self.tube_diametral_clearance

    @property
    def outer_radius(self) -> float:
        return self.bore_diameter / 2 + self.radial_wall

    @property
    def ear_root_x(self) -> float:
        return sqrt(self.outer_radius**2 - (self.split_gap / 2) ** 2)

    @property
    def screw_x(self) -> float:
        return self.ear_root_x + self.ear_width / 2

    @property
    def nut_pocket_depth(self) -> float:
        return self.nut_thickness + self.nut_axial_clearance

    def validate(self) -> None:
        if any(v <= 0 for v in vars(self).values()):
            raise ValueError("All dimensions and allowances must be positive")
        if self.split_gap / 2 + max(self.screw_ear_thickness, self.nut_ear_thickness) >= self.outer_radius:
            raise ValueError("Ears must overlap the ring")
        if self.nut_pocket_depth >= self.nut_ear_thickness:
            raise ValueError("Nut pocket must retain an inner bearing wall")
        pocket_af = self.nut_across_flats + self.nut_across_flats_clearance
        if pocket_af + 2 * self.outer_rim_fillet >= self.axial_width:
            raise ValueError("Ring width must leave material around the nut pocket")
        if pocket_af / cos(pi / 6) + 2 * self.outer_rim_fillet >= self.ear_width:
            raise ValueError("Tabs must leave material around the hex corners")
        if self.outer_rim_fillet >= min(self.radial_wall, self.axial_width / 2):
            raise ValueError("Rim fillet is too large")
        grip = self.screw_ear_thickness + self.split_gap + self.nut_ear_thickness
        if self.screw_length < grip - self.nut_axial_clearance:
            raise ValueError("Screw must fully engage the seated nut")


def build_tube_clamp(p: TubeClampParameters | None = None) -> cq.Workplane:
    p = p or TubeClampParameters()
    p.validate()
    overrun = 1.0
    ring = cq.Workplane("XY").circle(p.outer_radius).extrude(p.axial_width)
    ear_end = p.ear_root_x + p.ear_width
    for y, thickness in (
        (p.split_gap / 2, p.nut_ear_thickness),
        (-p.split_gap / 2 - p.screw_ear_thickness, p.screw_ear_thickness),
    ):
        ear = cq.Workplane("XY", origin=(0, y, 0)).box(
            ear_end, thickness, p.axial_width, centered=(False, False, False)
        )
        ring = ring.union(ear)
    roots = []
    for y in (p.split_gap / 2 + p.nut_ear_thickness, -p.split_gap / 2 - p.screw_ear_thickness):
        x = sqrt(p.outer_radius**2 - y**2)
        roots.extend(
            e
            for e in ring.edges("|Z").vals()
            if abs(e.Center().x - x) < 1e-6 and abs(e.Center().y - y) < 1e-6
        )
    if len(roots) != 2:
        raise ValueError("Expected two tab-root edges")
    ring = ring.newObject(roots).fillet(p.ear_root_fillet)
    # Slight rounding on both outer annular rims (and their tangent root arcs).
    rims = [
        e for e in ring.edges().vals() if e.geomType() == "CIRCLE" and abs(e.radius() - p.outer_radius) < 1e-6
    ]
    ring = ring.newObject(rims).fillet(p.outer_rim_fillet)
    bore = (
        cq.Workplane("XY", origin=(0, 0, -overrun))
        .circle(p.bore_diameter / 2)
        .extrude(p.axial_width + 2 * overrun)
    )
    split = cq.Workplane("XY", origin=(0, 0, -overrun)).box(
        ear_end + overrun, p.split_gap, p.axial_width + 2 * overrun, centered=(False, True, False)
    )
    ring = ring.cut(bore).cut(split)
    screw_y = -p.split_gap / 2 - p.screw_ear_thickness
    nut_y = p.split_gap / 2 + p.nut_ear_thickness
    hole = cq.Solid.makeCylinder(
        p.screw_clearance_diameter / 2,
        nut_y - screw_y + 2 * overrun,
        cq.Vector(p.screw_x, screw_y - overrun, p.axial_width / 2),
        cq.Vector(0, 1, 0),
    )
    nut_plane = cq.Plane(
        origin=(p.screw_x, nut_y - p.nut_pocket_depth, p.axial_width / 2), xDir=(1, 0, 0), normal=(0, 1, 0)
    )
    pocket = (
        cq.Workplane(nut_plane)
        .polygon(6, (p.nut_across_flats + p.nut_across_flats_clearance) / cos(pi / 6))
        .extrude(p.nut_pocket_depth + overrun)
    )
    ring = ring.cut(hole).cut(pocket).clean()
    if len(ring.solids().vals()) != 1 or not ring.val().isValid():
        raise ValueError("Tube clamp must be one valid solid")
    return ring


def viewer_assembly(clamp: cq.Workplane, p: TubeClampParameters | None = None) -> cq.Assembly:
    p = p or TubeClampParameters()
    assembly = cq.Assembly(name="Tube retaining clamp (provisional)")
    assembly.add(clamp, name="Clamp", color=cq.Color(0.8, 0.65, 0.3))
    # Simplified tube envelope for fit inspection; threads and internals omitted.
    tube = cq.Workplane("XY", origin=(0, 0, -5)).circle(p.tube_diameter / 2).extrude(p.axial_width + 10)
    assembly.add(tube, name="SM1 tube reference", color=cq.Color(0.6, 0.6, 0.6))
    return assembly

"""Exploratory LED bracket; canonical design §6.5 refreshed 2026-09-22.

Local x is transverse, +y faces the condenser, z=0 is the flat post top.
Assembly coordinates put the rail top at z=0. The heatsink is an octagonal
ENVELOPE, not a model of its unmeasured fins or LED board. All bracket/contact
geometry and additional M3 pressure-screw use are proposals, not a baseline.
"""

from dataclasses import dataclass
from math import cos, isfinite, pi, tan

import cadquery as cq


@dataclass(frozen=True)
class LEDModuleParameters:
    # Canonical interfaces; 72.35 is the rounded, frozen optical height.
    optical_height: float = 72.35
    post_length: float = 50.0
    post_diameter: float = 12.7
    datum_thickness: float = 0.010 * 25.4
    # Approximate document envelope, NOT physical measurements. BOM says Ø55;
    # confirm across-flats vs across-corners before printing mating geometry.
    heatsink_across_flats: float = 55.0
    heatsink_depth: float = 20.0
    calibration_half_travel: float = 3.0
    # Proposed dimensions / fabrication allowances, in mm.
    heatsink_rear_y: float = 14.0
    side_clearance: float = 0.15  # Per side, before tightening pressure screws.
    axial_clearance: float = 0.30
    tab_radius: float = 10.0
    tab_thickness: float = 5.0
    m4_diameter: float = 4.0
    m4_diametral_clearance: float = 0.5
    rear_wall_y: float = -10.0
    rear_wall_thickness: float = 4.0
    finger_wall: float = 4.0
    finger_height: float = 14.0
    retaining_lip: float = 3.0
    lip_thickness: float = 2.0
    # Existing common hardware, proposed here as opposed pressure screws.
    pressure_screw_diameter: float = 3.0
    pressure_screw_length: float = 12.0
    pressure_head_diameter: float = 5.5
    pressure_head_height: float = 3.0
    pressure_bore_clearance: float = 0.4
    nut_af: float = 5.5
    nut_thickness: float = 2.4
    nut_af_clearance: float = 0.3
    nut_axial_clearance: float = 0.3
    nut_inner_offset: float = 5.0  # From nominal heatsink flat outward.
    pressure_boss_length: float = 10.0
    pressure_boss_width: float = 10.0
    pressure_boss_height: float = 12.0

    @property
    def post_top(self):
        return self.datum_thickness + self.post_length

    @property
    def axis_z(self):
        return self.optical_height - self.post_top

    @property
    def half_flat(self):
        return self.heatsink_across_flats / 2

    @property
    def inner_x(self):
        return self.half_flat + self.side_clearance

    @property
    def front_y(self):
        return self.heatsink_rear_y + self.heatsink_depth

    @property
    def pressure_y(self):
        return self.heatsink_rear_y + self.heatsink_depth / 2

    def validate(self):
        if any(not isfinite(v) for v in vars(self).values()):
            raise ValueError("Dimensions must be finite")
        if any(v <= 0 for k, v in vars(self).items() if k != "rear_wall_y"):
            raise ValueError("Dimensions and allowances must be positive")
        if self.rear_wall_y >= 0:
            raise ValueError("Rear bridge must be behind the post")
        if not -self.tab_radius < self.rear_wall_y + self.rear_wall_thickness < -self.m4_diameter:
            raise ValueError("Rear bridge must join the tab and leave M4 tool access")
        if self.heatsink_rear_y <= self.tab_radius:
            raise ValueError("Heatsink must clear the mounting tab and post")
        if self.tab_radius <= self.post_diameter / 2:
            raise ValueError("Tab must cover the post-top seating face")
        if self.m4_diameter + self.m4_diametral_clearance >= self.post_diameter:
            raise ValueError("M4 bore must leave a post-top seating annulus")
        flat_half_height = self.half_flat * tan(pi / 8)
        if self.finger_height / 2 + self.calibration_half_travel >= flat_half_height:
            raise ValueError("Fingers must remain on vertical flats throughout calibration")
        if self.axis_z - self.finger_height / 2 <= self.tab_thickness:
            raise ValueError("Fingers must clear the mounting tab height")
        if not self.side_clearance < self.retaining_lip < self.finger_wall + self.half_flat:
            raise ValueError("Retaining lips must overlap the heatsink edges")
        outer_x = self.inner_x + self.pressure_boss_length
        nut_end = self.half_flat + self.nut_inner_offset + self.nut_thickness + self.nut_axial_clearance
        if not self.inner_x < self.half_flat + self.nut_inner_offset < nut_end < outer_x:
            raise ValueError("Nut pocket must leave inner and outer retaining walls")
        if self.half_flat + self.pressure_screw_length <= outer_x:
            raise ValueError("Pressure screw head must clear the boss when its tip touches the flat")
        if self.nut_af + self.nut_af_clearance >= min(self.pressure_boss_width, self.pressure_boss_height):
            raise ValueError("Nut pocket must fit within the pressure boss")
        if self.pressure_boss_width >= self.heatsink_depth:
            raise ValueError("Pressure boss must lie between front and rear lips")


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY", origin=(x0, y0, z0)).box(
        x1-x0, y1-y0, z1-z0, centered=(False, False, False))


def build_led_bracket(p=None):
    """One printable bracket, post seating face at z=0; no purchased parts."""
    p = p or LEDModuleParameters()
    p.validate()
    z0, z1 = p.axis_z - p.finger_height / 2, p.axis_z + p.finger_height / 2
    outer = p.inner_x + p.finger_wall
    front_stop = p.front_y + p.axial_clearance
    bracket = cq.Workplane("XY").circle(p.tab_radius).extrude(p.tab_thickness)
    bracket = bracket.union(_box(-outer, outer, p.rear_wall_y,
                                 p.rear_wall_y + p.rear_wall_thickness, 0, z1))
    # Each channel is open vertically for assembly and calibration. Rear faces
    # establish axial/pitch seating: hold sink against them while tightening.
    side = _box(p.inner_x, outer, p.rear_wall_y, front_stop + p.lip_thickness, z0, z1)
    for y0, y1 in ((p.heatsink_rear_y - p.lip_thickness, p.heatsink_rear_y),
                   (front_stop, front_stop + p.lip_thickness)):
        side = side.union(_box(p.inner_x - p.retaining_lip, outer, y0, y1, z0, z1))
    boss_outer = p.inner_x + p.pressure_boss_length
    side = side.union(_box(p.inner_x, boss_outer,
                          p.pressure_y - p.pressure_boss_width / 2,
                          p.pressure_y + p.pressure_boss_width / 2,
                          p.axis_z - p.pressure_boss_height / 2,
                          p.axis_z + p.pressure_boss_height / 2))
    bore = cq.Solid.makeCylinder((p.pressure_screw_diameter + p.pressure_bore_clearance) / 2,
                                p.pressure_boss_length, cq.Vector(p.inner_x, p.pressure_y, p.axis_z),
                                cq.Vector(1, 0, 0))
    side = side.cut(bore)
    # Top-loaded hex nut pocket: closed outer wall reacts pressure-screw load.
    nut_x = p.half_flat + p.nut_inner_offset
    nut_depth = p.nut_thickness + p.nut_axial_clearance
    af = p.nut_af + p.nut_af_clearance
    plane = cq.Plane(origin=(nut_x, p.pressure_y, p.axis_z), xDir=(0, 1, 0), normal=(1, 0, 0))
    pocket = cq.Workplane(plane).polygon(6, af / cos(pi / 6)).extrude(nut_depth)
    pocket = pocket.rotate((0, p.pressure_y, p.axis_z), (1, p.pressure_y, p.axis_z), 30)
    side = side.cut(pocket).cut(_box(nut_x, nut_x + nut_depth,
                                    p.pressure_y - af / 2, p.pressure_y + af / 2,
                                    p.axis_z, z1 + p.pressure_boss_height))
    bracket = bracket.union(side).union(side.mirror("YZ"))
    bracket = bracket.cut(cq.Workplane("XY").circle(
        (p.m4_diameter + p.m4_diametral_clearance) / 2).extrude(p.tab_thickness)).clean()
    if not bracket.val().isValid() or len(bracket.val().Solids()) != 1:
        raise ValueError("Bracket must be one valid solid")
    return bracket


def build_heatsink_envelope(p=None, travel=0.0):
    """Solid regular octagon, local coordinates; fins/MCPCB deliberately omitted."""
    p = p or LEDModuleParameters()
    p.validate()
    if not isfinite(travel) or abs(travel) > p.calibration_half_travel:
        raise ValueError("Calibration travel exceeds supported range")
    a, b = p.half_flat, p.half_flat * tan(pi / 8)
    points = [(a,b), (b,a), (-b,a), (-a,b), (-a,-b), (-b,-a), (b,-a), (a,-b)]
    plane = cq.Plane(origin=(0, p.front_y, p.axis_z + travel), xDir=(1,0,0), normal=(0,-1,0))
    return cq.Workplane(plane).polyline(points).close().extrude(p.heatsink_depth)


def build_led_module_assembly(p=None, travel=0.0, with_shoe=False):
    """Rail-top coordinates, simplified references and proposed pressure screws.

    M4 fastener is omitted: actual retained stud/screw and thread engagement
    must be measured. The through-bore accepts either; no length is invented.
    """
    p = p or LEDModuleParameters()
    sink = build_heatsink_envelope(p, travel)
    module = cq.Assembly(name="LED module prototype")
    module.add(build_led_bracket(p), name="Printed bracket", color=cq.Color(0.85, 0.48, 0.2))
    module.add(sink, name="Heatsink envelope UNMEASURED", color=cq.Color(0.65, 0.68, 0.72, 0.5))
    for sign, label in ((1, "Right"), (-1, "Left")):
        screw = cq.Workplane(obj=cq.Solid.makeCylinder(
            p.pressure_screw_diameter / 2, p.pressure_screw_length,
            cq.Vector(p.half_flat, p.pressure_y, p.axis_z), cq.Vector(1,0,0)))
        screw = screw.union(cq.Solid.makeCylinder(p.pressure_head_diameter / 2, p.pressure_head_height,
                            cq.Vector(p.half_flat + p.pressure_screw_length, p.pressure_y, p.axis_z),
                            cq.Vector(1,0,0)))
        plane = cq.Plane(origin=(p.half_flat + p.nut_inner_offset + p.nut_axial_clearance,
                                p.pressure_y, p.axis_z), xDir=(0,1,0), normal=(1,0,0))
        nut = cq.Workplane(plane).polygon(6, p.nut_af / cos(pi/6)).circle(
            p.pressure_screw_diameter / 2).extrude(p.nut_thickness)
        nut = nut.rotate((0,p.pressure_y,p.axis_z), (1,p.pressure_y,p.axis_z), 30)
        for name, shape in (("pressure screw reference", screw), ("nut reference", nut)):
            module.add(shape if sign == 1 else shape.mirror("YZ"), name=f"{label} {name}",
                       color=cq.Color(0.35,0.36,0.38))
    assembly = cq.Assembly(name="LED station preliminary")
    assembly.add(module, loc=cq.Location(cq.Vector(0,0,p.post_top)))
    post = cq.Workplane("XY", origin=(0,0,p.datum_thickness)).circle(p.post_diameter / 2).extrude(p.post_length)
    assembly.add(post, name="TR50 M envelope", color=cq.Color(0.7,0.7,0.72))
    if with_shoe:
        from schlieren.parts.rail_shoe import build_rail_shoe, reference_parts
        assembly.add(build_rail_shoe(), name="Rail shoe", color=cq.Color(0.75,0.62,0.3))
        for name, part in reference_parts().items():
            if "post" not in name:
                assembly.add(part, name=name, color=cq.Color(0.45,0.45,0.45))
    return assembly

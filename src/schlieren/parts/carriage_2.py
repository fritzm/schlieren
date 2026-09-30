"""Urgent-build alternative: one-piece post-mounted cassette finger holder.

Provisional alternative to §8, baseline refreshed 2026-09-23. Local x is
transverse, +y is optical/front, z=0 is the TR50/M post top. No tube rotation.
The existing carriage remains unchanged. Hardware/adhesive fits need checking.
"""
from dataclasses import dataclass
from math import cos, pi, radians, tan

import cadquery as cq
from schlieren.parts.cassette import CassetteParameters, build_cassette_assembly


@dataclass(frozen=True)
class Carriage2Parameters:
    optical_height: float = 72.35
    post_length: float = 50.0
    datum_thickness: float = 0.254
    cassette_size: float = 64.0
    cassette_thickness: float = 5.0
    half_travel: float = 5.0
    cassette_rear_y: float = 14.0
    side_clearance: float = 0.25
    axial_clearance: float = 0.3
    wall: float = 4.0
    finger_height: float = 14.0
    lip_overlap: float = 0.5  # Outside clamp-bar envelope (x <= 31 mm).
    lip_thickness: float = 2.0
    tab_radius: float = 12.0
    tab_thickness: float = 5.0
    post_screw_clearance: float = 4.5
    pressure_boss_length: float = 10.0
    pressure_boss_depth: float = 8.0
    pressure_boss_height: float = 10.0
    pressure_screw_clearance: float = 3.4
    nut_af: float = 5.8  # 5.5 mm M3 nut + fabrication allowance.
    nut_depth: float = 2.7
    nut_inner_offset: float = 5.0
    insert_bore: float = 0.313 * 25.4
    insert_length: float = 0.313 * 25.4
    insert_support: float = 8.5
    adjuster_length: float = 25.4
    max_tip_extension: float = 15.5
    magnet_length: float = 10.0
    magnet_width: float = 5.0
    magnet_thickness: float = 2.0

    @property
    def post_top(self):
        return self.post_length + self.datum_thickness

    @property
    def axis_z(self):
        return self.optical_height - self.post_top

    @property
    def inner_x(self):
        return self.cassette_size/2 + self.side_clearance

    @property
    def outer_x(self):
        return self.inner_x + self.wall

    @property
    def rear_y(self):
        return self.cassette_rear_y - self.wall

    @property
    def lip_inner_x(self):
        return self.cassette_size/2 - self.lip_overlap

    @property
    def lip_y(self):
        c = CassetteParameters()
        return (self.cassette_rear_y + self.cassette_thickness - c.bevel_depth
                + self.lip_overlap*tan(radians(c.bevel_angle)) + self.axial_clearance)

    @property
    def screw_y(self):
        return self.cassette_rear_y + 2.0  # Contact the unbeveled side edge.

    @property
    def adjuster_y(self):
        return self.cassette_rear_y + self.cassette_thickness/2

    @property
    def magnet_z(self):
        return self.axis_z - self.cassette_size/2 - self.magnet_thickness

    @property
    def support_bottom(self):
        # Full-length conservative engagement at the highest cassette position.
        return self.magnet_z + self.half_travel - self.max_tip_extension - self.insert_length

    @property
    def support_top(self):
        return self.support_bottom + self.insert_support

    def validate(self):
        if self.insert_support < self.insert_length:
            raise ValueError('Insert needs full axial support')
        if self.max_tip_extension + self.insert_length >= self.adjuster_length:
            raise ValueError('Adjuster needs engagement margin')
        if self.tab_thickness >= self.axis_z - 12:
            raise ValueError('Crossbar would obstruct optical opening')
        if self.lip_inner_x <= 31:
            raise ValueError('Lips must clear existing clamp bars')


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY', origin=(x0,y0,z0)).box(x1-x0,y1-y0,z1-z0,centered=(False,False,False))


def build_carriage_2(p=None):
    p = p or Carriage2Parameters()
    p.validate()
    z0, z1 = p.axis_z-p.finger_height/2, p.axis_z+p.finger_height/2
    part = cq.Workplane('XY').circle(p.tab_radius).extrude(p.tab_thickness)
    part = part.union(box(-p.outer_x,p.outer_x,p.rear_y,p.cassette_rear_y,0,p.tab_thickness))
    # Open frame: narrow side uprights and a bottom beam support the fine screw.
    side = box(p.inner_x,p.outer_x,p.rear_y,p.cassette_rear_y,p.support_bottom,z1)
    side = side.union(box(p.inner_x,p.outer_x,p.rear_y,p.lip_y+p.lip_thickness,z0,z1))
    side = side.union(box(p.lip_inner_x,p.outer_x,p.rear_y,p.cassette_rear_y,z0,z1))
    side = side.union(box(p.lip_inner_x,p.outer_x,p.lip_y,p.lip_y+p.lip_thickness,z0,z1))
    boss_end = p.inner_x+p.pressure_boss_length
    side = side.union(box(p.inner_x,boss_end,p.screw_y-p.pressure_boss_depth/2,
                          p.screw_y+p.pressure_boss_depth/2,
                          p.axis_z-p.pressure_boss_height/2,p.axis_z+p.pressure_boss_height/2))
    bore = cq.Solid.makeCylinder(p.pressure_screw_clearance/2,p.pressure_boss_length,
                                 cq.Vector(p.inner_x,p.screw_y,p.axis_z),cq.Vector(1,0,0))
    nx=p.cassette_size/2+p.nut_inner_offset
    plane=cq.Plane(origin=(nx,p.screw_y,p.axis_z),xDir=(0,1,0),normal=(1,0,0))
    pocket=cq.Workplane(plane).polygon(6,p.nut_af/cos(pi/6)).extrude(p.nut_depth)
    pocket=pocket.rotate((0,p.screw_y,p.axis_z),(1,p.screw_y,p.axis_z),30)
    side=side.cut(bore).cut(pocket).cut(box(nx,nx+p.nut_depth,
        p.screw_y-p.nut_af/2,p.screw_y+p.nut_af/2,p.axis_z,z1+1))
    part=part.union(side).union(side.mirror('YZ'))
    part=part.union(box(-p.outer_x,p.outer_x,p.rear_y,p.cassette_rear_y,
                        p.support_bottom,p.support_bottom+p.wall))
    boss=cq.Workplane('XY',origin=(0,p.adjuster_y,p.support_bottom)).circle(
        p.insert_bore/2+p.wall).extrude(p.insert_support)
    part=part.union(boss)
    part=part.cut(cq.Workplane('XY',origin=(0,p.adjuster_y,p.support_bottom)).circle(
        p.insert_bore/2).extrude(p.insert_support))
    part=part.cut(cq.Workplane('XY').circle(p.post_screw_clearance/2).extrude(p.tab_thickness)).clean()
    if not part.val().isValid() or len(part.solids().vals())!=1:
        raise ValueError('Holder must be one valid printable solid')
    return part


def cassette_location(p, travel=0, angle=0):
    # Cassette XY -> holder XZ, cassette front +Z -> holder +Y.
    return (cq.Location(cq.Vector(0,p.cassette_rear_y,p.axis_z+travel),cq.Vector(1,0,0),-90)
            * cq.Location(cq.Vector(0,0,0),cq.Vector(0,0,1),angle))


def build_carriage_2_assembly(p=None, travel=0, angle=0):
    p=p or Carriage2Parameters()
    if abs(travel)>p.half_travel:
        raise ValueError('Travel exceeds ±5 mm')
    a=cq.Assembly(name='Carriage 2 alternative')
    a.add(build_carriage_2(p),name='One-piece holder',color=cq.Color(.35,.6,.8))
    a.add(build_cassette_assembly(),name='Existing cassette',loc=cassette_location(p,travel,angle))
    magnet=box(-p.magnet_length/2,p.magnet_length/2,p.cassette_rear_y,
               p.cassette_rear_y+p.magnet_width,p.magnet_z+travel,
               p.magnet_z+travel+p.magnet_thickness)
    a.add(magnet,name='Bonded lower-edge magnet reference',color=cq.Color(.65,.65,.65))
    screw=cq.Workplane('XY',origin=(0,p.adjuster_y,p.magnet_z+travel-p.adjuster_length)).circle(6.35/2).extrude(p.adjuster_length)
    a.add(screw,name='FAS100 shaft envelope',color=cq.Color(.7,.7,.7))
    insert=cq.Workplane('XY',origin=(0,p.adjuster_y,p.support_bottom)).circle(p.insert_bore/2).circle(6.35/2).extrude(0.298*25.4)
    flange=cq.Workplane('XY',origin=(0,p.adjuster_y,p.support_bottom-0.254)).circle(0.352*25.4/2).circle(6.35/2).extrude(0.254)
    a.add(insert.union(flange),name='Insert reference flange below',color=cq.Color(.8,.65,.25))
    for sign,label in ((-1,'Left'),(1,'Right')):
        pressure=cq.Workplane(obj=cq.Solid.makeCylinder(1.5,12,cq.Vector(sign*32,p.screw_y,p.axis_z),cq.Vector(sign,0,0)))
        pressure=pressure.union(cq.Solid.makeCylinder(2.75,3,cq.Vector(sign*44,p.screw_y,p.axis_z),cq.Vector(sign,0,0)))
        a.add(pressure,name=label+' M3 pressure screw reference',color=cq.Color(.65,.65,.65))

    post=cq.Workplane('XY',origin=(0,0,-p.post_length)).circle(12.7/2).extrude(p.post_length)
    a.add(post,name='Post reference',color=cq.Color(.7,.7,.7))
    return a

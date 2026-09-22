"""Preliminary four-piece slit/cutoff carriage, baseline 2026-09-21 §8.

Local XY is the cassette plane, +Y points toward the FAS100, +Z is the
cassette-loading side. Z=0 is the plate back, not the rail-height datum.
No tube mount is included. Dimensions beyond explicit baseline interfaces
are provisional first-print targets; no purchased threads are modeled.
"""
from dataclasses import dataclass
from math import cos, pi, tan, radians

import cadquery as cq


@dataclass(frozen=True)
class CarriageParameters:
    cassette_size: float = 64.0
    cassette_thickness: float = 5.0
    aperture_diameter: float = 24.0
    working_half_travel: float = 5.0
    loading_retraction: float = 6.0  # Additional motion from fiducial only.
    plate_width: float = 86.0
    plate_thickness: float = 4.0
    guide_floor_rise: float = 2.0
    ear_thickness: float = 3.0
    guide_axial_clearance: float = 0.4
    keeper_thickness: float = 3.0
    ear_lower_clearance: float = 0.15
    body_deck_clearance: float = 0.3  # Provisional ABS running clearance.
    body_width: float = 58.0
    body_length: float = 10.0
    body_top: float = 12.0
    ear_outer_x: float = 37.0
    track_inner_x: float = 32.3  # Clear the full 64 mm cassette swept footprint.
    track_outer_x: float = 38.0
    keeper_opening_width: float = 66.0
    keeper_end_member_width: float = 5.0
    fastener_edge_margin: float = 4.5
    datum_pin_shank: float = 1.27
    datum_hole_diametral_clearance: float = 0.08
    datum_projection: float = 1.0  # UNMEASURED domed-head contact height.
    bevel_depth: float = 1.25
    bevel_angle: float = 27.5  # Provisional convention: from cassette plane.
    spring_free_length: float = 25.5
    spring_fiducial_length: float = 16.5
    shoulder_length: float = 45.0
    shoulder_guide_diameter: float = 4.25
    shoulder_thread_pilot: float = 3.3  # Drill/tap M4; verify thread engagement.
    shoulder_thread_depth: float = 7.0  # Nominal engagement zone; measure screw threaded end.
    shoulder_tap_relief: float = 2.0
    shoulder_entrance_chamfer: float = 0.5  # Axial/radial size of 45-degree lead-in.
    spring_axis_z: float = 7.5
    insert_bore_diameter: float = 8.0  # UNMEASURED 98625A950 placeholder: NOT print ready.
    adjuster_support_length: float = 12.0  # Insert seating/retention needs fit-up.
    support_top: float = 14.0
    magnet_length: float = 10.0
    magnet_width: float = 5.0
    magnet_thickness: float = 2.0
    magnet_fit_clearance: float = 0.15
    screw_clearance: float = 3.3
    screw_head_clearance: float = 5.8
    screw_head_recess: float = 0.5
    nut_pocket_af: float = 5.8  # 5.5 nominal + 0.3 across-flats allowance.
    nut_pocket_depth: float = 2.5

    @property
    def adjuster_axis_z(self):
        # Keep the provisional insert bore tangent to, rather than cutting, the deck.
        return self.plate_thickness + self.insert_bore_diameter / 2

    @property
    def floor_z(self):
        return self.plate_thickness + self.guide_floor_rise

    @property
    def keeper_z(self):
        return self.floor_z + self.ear_thickness + self.guide_axial_clearance

    @property
    def spring_seat_y(self):
        return -self.cassette_size / 2 - self.body_length - self.spring_fiducial_length

    @property
    def rear_wall_thickness(self):
        return self.keeper_end_member_width

    @property
    def plate_length(self):
        return 2 * (-self.spring_seat_y + self.rear_wall_thickness)

    @property
    def adjuster_support_y(self):
        return (self.plate_length - self.adjuster_support_length) / 2

    @property
    def keeper_opening_length(self):
        return self.plate_length - self.keeper_end_member_width - self.adjuster_support_length

    @property
    def keeper_opening_y(self):
        # The adjuster end member covers the entire insert-support depth.
        return (self.keeper_end_member_width - self.adjuster_support_length) / 2

    @property
    def support_spans(self):
        return (
            (self.adjuster_support_y - self.adjuster_support_length / 2,
             self.plate_length / 2, self.insert_bore_diameter),
            (-self.plate_length / 2, self.spring_seat_y, self.shoulder_guide_diameter),
        )

    @property
    def fasteners(self):
        x = self.plate_width / 2 - self.fastener_edge_margin
        y = self.plate_length / 2 - self.fastener_edge_margin
        return [(sx * x, sy * y) for sx in (-1, 1) for sy in (-1, 1)]

    @property
    def datum_points(self):
        # Broad triangle; swept tracks clear the aperture at either travel limit.
        return [(-23.0, -20.0), (23.0, -20.0), (0.0, 23.0)]

    def validate(self):
        if any(v <= 0 for v in vars(self).values()):
            raise ValueError("Dimensions must be positive")
        if any(end <= start for start, end, _ in self.support_spans):
            raise ValueError("Support inner faces must lie inside the plate edges")
        if self.ear_lower_clearance >= self.guide_axial_clearance:
            raise ValueError("Ears need clearance below the keeper")
        if not self.body_width / 2 <= self.track_inner_x < self.ear_outer_x < self.track_outer_x:
            raise ValueError("Guide ears must fit the open tracks")
        if not self.cassette_size < self.keeper_opening_width < 2 * self.ear_outer_x:
            raise ValueError("Keeper must clear cassette and overlap ears")
        if self.shoulder_thread_depth + self.shoulder_tap_relief >= self.body_length:
            raise ValueError("Blind spring-rod pilot must retain a closed end wall")
        if self.nut_pocket_depth >= self.plate_thickness:
            raise ValueError("Nut pockets need bearing roofs")
        if self.spring_fiducial_length <= max(self.working_half_travel, self.loading_retraction):
            raise ValueError("Spring space exhausted")


def _box(width, length, height, x=0, y=0, z=0):
    return cq.Workplane("XY", origin=(x, y, z)).box(width, length, height, centered=(True, True, False))


def _y_hole(radius, length, y, z):
    return cq.Solid.makeCylinder(radius, length, cq.Vector(0, y, z), cq.Vector(0, 1, 0))


def build_base_plate(p=None):
    p = p or CarriageParameters()
    p.validate()
    base = _box(p.plate_width, p.plate_length, p.plate_thickness)
    for sign in (-1, 1):
        floor_width = p.track_outer_x - p.track_inner_x
        base = base.union(_box(floor_width, p.plate_length, p.guide_floor_rise,
                              x=sign * (p.track_outer_x + p.track_inner_x) / 2, z=p.plate_thickness))
        land_width = p.plate_width / 2 - p.track_outer_x
        base = base.union(_box(land_width, p.plate_length, p.keeper_z - p.plate_thickness,
                              x=sign * (p.track_outer_x + land_width / 2), z=p.plate_thickness))
    for start, end, diameter in p.support_spans:
        support = _box(p.plate_width, end - start, p.support_top - p.plate_thickness,
                       y=(start + end) / 2, z=p.plate_thickness)
        base = base.union(support)
    # Open-top keeper seating recess: preserves front-side removal and the
    # original screw stack while the support blocks extend to all plate edges.
    base = base.cut(_keeper_envelope(p, p.support_top - p.keeper_z))
    for start, end, diameter in p.support_spans:
        base = base.cut(_y_hole(diameter / 2, end - start + 2, start - 1,
                                p.adjuster_axis_z if start > 0 else p.spring_axis_z))
    # The tube and optical axis remain fixed while the cassette translates.
    opening = cq.Workplane("XY").circle(p.aperture_diameter / 2).extrude(p.plate_thickness)
    base = base.cut(opening)
    for x, y in p.datum_points:
        hole = cq.Workplane("XY", origin=(x, y, 0)).circle(
            (p.datum_pin_shank + p.datum_hole_diametral_clearance) / 2).extrude(p.plate_thickness)
        base = base.cut(hole)
    for x, y in p.fasteners:
        base = base.cut(cq.Workplane("XY", origin=(x, y, 0)).circle(p.screw_clearance / 2).extrude(p.keeper_z))
        base = base.cut(cq.Workplane("XY", origin=(x, y, 0)).polygon(
            6, p.nut_pocket_af / cos(pi / 6)).extrude(p.nut_pocket_depth))
    return base.clean()


def _keeper_envelope(p, height):
    return _box(p.plate_width, p.plate_length, height, z=p.keeper_z).cut(
        _box(p.keeper_opening_width, p.keeper_opening_length, height,
             y=p.keeper_opening_y, z=p.keeper_z))


def build_keeper_plate(p=None):
    p = p or CarriageParameters()
    p.validate()
    keeper = _keeper_envelope(p, p.keeper_thickness)
    # Concentric crown maintains the nominal keeper thickness radially over
    # the insert bore. Clip at the mating plane to keep the base unchanged.
    start, end, _ = p.support_spans[0]
    crown_radius = p.insert_bore_diameter / 2 + p.keeper_thickness
    crown = cq.Workplane(obj=_y_hole(crown_radius, end - start, start, p.adjuster_axis_z))
    crown = crown.intersect(_box(2 * crown_radius, end - start,
                                p.adjuster_axis_z + crown_radius - p.keeper_z,
                                y=(start + end) / 2, z=p.keeper_z))
    keeper = keeper.union(crown)
    for start, end, diameter in p.support_spans:
        keeper = keeper.cut(_y_hole(diameter / 2, end - start + 2, start - 1,
                                p.adjuster_axis_z if start > 0 else p.spring_axis_z))
    for x, y in p.fasteners:
        keeper = keeper.cut(cq.Workplane("XY", origin=(x, y, p.keeper_z)).circle(
            p.screw_clearance / 2).extrude(p.keeper_thickness))
        keeper = keeper.cut(cq.Workplane("XY", origin=(x, y, p.keeper_z + p.keeper_thickness - p.screw_head_recess))
                            .circle(p.screw_head_clearance / 2).extrude(p.screw_head_recess))
    return keeper.clean()


def build_plunger(p=None, *, spring=False):
    """Return plunger at fiducial; spring body mirrored across XZ."""
    p = p or CarriageParameters()
    p.validate()
    edge = p.cassette_size / 2
    bottom = p.plate_thickness + p.body_deck_clearance
    ear_bottom = p.floor_z + p.ear_lower_clearance
    bevel_z = p.plate_thickness + p.datum_projection + p.cassette_thickness - p.bevel_depth
    inset = p.bevel_depth / tan(radians(p.bevel_angle))
    front_z = bevel_z + p.bevel_depth
    profile = [(edge, bottom), (edge + p.body_length, bottom),
               (edge + p.body_length, p.body_top), (edge - inset, p.body_top),
               (edge - inset, front_z), (edge, bevel_z)]
    body = cq.Workplane("YZ", origin=(-p.body_width / 2, 0, 0)).polyline(profile).close().extrude(p.body_width)
    # Overlap the body slightly to ensure a single connected printed solid.
    ear_root = p.body_width / 2 - 0.5
    for sign in (-1, 1):
        body = body.union(_box(p.ear_outer_x - ear_root, p.body_length, p.ear_thickness,
                              x=sign * (p.ear_outer_x + ear_root) / 2,
                              y=edge + p.body_length / 2, z=ear_bottom))
    outer_y = edge + p.body_length
    if spring:
        pilot_depth = p.shoulder_thread_depth + p.shoulder_tap_relief
        body = body.cut(_y_hole(p.shoulder_thread_pilot / 2, pilot_depth,
                               outer_y - pilot_depth, p.spring_axis_z))
        lead_in = cq.Solid.makeCone(
            p.shoulder_thread_pilot / 2,
            p.shoulder_thread_pilot / 2 + p.shoulder_entrance_chamfer,
            p.shoulder_entrance_chamfer,
            cq.Vector(0, outer_y - p.shoulder_entrance_chamfer, p.spring_axis_z),
            cq.Vector(0, 1, 0),
        )
        body = body.cut(lead_in)
        body = body.mirror("XZ")
    else:
        # Outward-opening, fully backed magnet pocket. A small adhesive tack is
        # needed for retention; the ball bears on the exposed broad XZ face.
        body = body.cut(_box(p.magnet_length + p.magnet_fit_clearance,
                            p.magnet_thickness + p.magnet_fit_clearance,
                            p.magnet_width + p.magnet_fit_clearance,
                            y=outer_y - (p.magnet_thickness + p.magnet_fit_clearance) / 2,
                            z=p.adjuster_axis_z - (p.magnet_width + p.magnet_fit_clearance) / 2))
    return body.clean()


def build_carriage(p=None, *, travel=0.0, retract=0.0):
    """Four independently selectable printed parts; retraction only at fiducial.

    Spring solid height is unverified: the loading pose checks printed geometry,
    not whether the purchased spring can safely reach that compression.
    """
    p = p or CarriageParameters()
    p.validate()
    if abs(travel) > p.working_half_travel or not 0 <= retract <= p.loading_retraction:
        raise ValueError("Requested pose exceeds supported travel")
    if retract and travel:
        raise ValueError("Return to fiducial before retracting for loading")
    assembly = cq.Assembly(name="Carriage (preliminary)")
    for name, part, color in (
        ("Base plate", build_base_plate(p), (0.65, 0.65, 0.7)),
        ("Keeper plate", build_keeper_plate(p), (0.35, 0.5, 0.75)),
        ("Driven plunger", build_plunger(p).translate((0, travel, 0)), (0.85, 0.65, 0.25)),
        ("Spring plunger", build_plunger(p, spring=True).translate((0, travel - retract, 0)), (0.4, 0.75, 0.5)),
    ):
        assembly.add(part, name=name, color=cq.Color(*color))
    return assembly

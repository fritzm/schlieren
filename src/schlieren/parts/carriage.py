"""Preliminary five-piece slit/cutoff carriage, baseline refreshed 2026-09-22 §8.

Local XY is the cassette plane, +Y points toward the FAS100, +Z is the
cassette-loading side. Z=0 is the plate back, not the rail-height datum.
The rear tube clamp is integral with the base. Dimensions beyond explicit baseline interfaces
are provisional first-print targets; no purchased threads are modeled.
"""
from dataclasses import dataclass
from math import cos, sin, pi, tan, radians, sqrt

import cadquery as cq

from schlieren.parts.tube_clamp import TubeClampParameters


@dataclass(frozen=True)
class CarriageParameters:
    cassette_size: float = 64.0
    cassette_thickness: float = 5.0
    aperture_diameter: float = 24.0
    working_half_travel: float = 5.0
    loading_retraction: float = 6.0  # Additional motion from fiducial only.
    plate_width: float = 86.0
    plate_thickness: float = 4.0
    locator_diameter: float = 3.0
    locator_height: float = 0.8
    locator_diametral_clearance: float = 0.3
    locator_depth_clearance: float = 0.2
    tube_diameter: float = 30.48  # Catalog nominal SM1L15 OD; measure before printing.
    tube_diametral_clearance: float = 0.25
    tube_clamp_depth: float = 12.25  # Rearward from the plate back / tube stop.
    tube_clamp_band_thickness: float = 4.5
    tube_clamp_relief_width: float = 1.25
    tube_clamp_relief_arc: float = 240.0  # Leaves 120 degrees attached opposite +X split.
    tube_clamp_root_fillet: float = 2.0
    tube_clamp_root_land: float = 0.5
    tube_clamp_ear_slit_gap: float = 0.5
    tube_clamp_split: float = 1.5

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
    # McMaster 98625A950 manufacturer drawing, canonical baseline §8.3.
    insert_body_diameter: float = 0.313 * 25.4
    insert_drill_diameter: float = 0.313 * 25.4
    insert_overall_length: float = 0.313 * 25.4  # Conservative thread-engagement envelope.
    insert_body_length: float = 0.298 * 25.4  # Under-flange length, independently specified.
    insert_min_material_thickness: float = 0.298 * 25.4
    insert_flange_diameter: float = 0.352 * 25.4
    insert_flange_thickness: float = 0.010 * 25.4
    insert_entry_chamfer: float = 0.1  # 45-degree entry, outboard face.
    adjuster_screw_length: float = 25.4
    adjuster_pitch: float = 25.4 / 80
    adjuster_clearance_travel: float = 15.5  # Maximum tip extension from insert inner end.
    adjuster_support_length: float = 8.5
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
    def insert_bore_diameter(self):
        # Nominal drawing bore; physically finish and fit-check the printed pilot.
        return self.insert_drill_diameter

    @property
    def tube_clamp_slit_front_z(self):
        return -self.tube_clamp_root_fillet - self.tube_clamp_root_land

    @property
    def tube_clamp_ear_plate_gap(self):
        return -self.tube_clamp_slit_front_z + self.tube_clamp_relief_width + self.tube_clamp_ear_slit_gap

    @property
    def tube_clamp_parameters(self):
        # Reuse the common M3 x 12 / full-height captured nut interface.
        return TubeClampParameters(
            tube_diameter=self.tube_diameter,
            tube_diametral_clearance=self.tube_diametral_clearance,
            axial_width=self.tube_clamp_depth - self.tube_clamp_ear_plate_gap,
            radial_wall=self.tube_clamp_band_thickness,
            split_gap=self.tube_clamp_split,
        )

    @property
    def adjuster_axis_z(self):
        # Preserve the deck even at the chamfer mouth.
        return self.plate_thickness + self.insert_bore_diameter / 2 + self.insert_entry_chamfer

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
    def magnet_contact_y(self):
        return self.cassette_size / 2 + self.body_length - self.magnet_fit_clearance

    @property
    def plate_ymin(self):
        return self.spring_seat_y - self.rear_wall_thickness

    @property
    def plate_ymax(self):
        # Locate the flange face to retain full insert engagement at -5 mm travel.
        return (self.magnet_contact_y - self.working_half_travel
                + self.adjuster_clearance_travel + self.insert_overall_length)

    @property
    def plate_length(self):
        return self.plate_ymax - self.plate_ymin

    @property
    def plate_center_y(self):
        return (self.plate_ymax + self.plate_ymin) / 2

    @property
    def adjuster_support_y(self):
        return self.plate_ymax - self.adjuster_support_length / 2

    @property
    def keeper_opening_length(self):
        return self.plate_length - self.keeper_end_member_width - self.adjuster_support_length

    @property
    def keeper_opening_y(self):
        return self.plate_center_y + (self.keeper_end_member_width - self.adjuster_support_length) / 2

    @property
    def support_spans(self):
        return (
            (self.plate_ymax - self.adjuster_support_length,
             self.plate_ymax, self.insert_bore_diameter),
            (self.plate_ymin, self.spring_seat_y, self.shoulder_guide_diameter),
        )

    @property
    def fasteners(self):
        x = self.plate_width / 2 - self.fastener_edge_margin
        return [(sx * x, y) for sx in (-1, 1)
                for y in (self.plate_ymin + self.fastener_edge_margin,
                          self.plate_ymax - self.fastener_edge_margin)]

    @property
    def datum_points(self):
        # Broad triangle; swept tracks clear the aperture at either travel limit.
        return [(-23.0, -20.0), (23.0, -20.0), (0.0, 23.0)]

    def validate(self):
        if any(v <= 0 for v in vars(self).values()):
            raise ValueError("Dimensions must be positive")
        if self.insert_bore_diameter + 2*self.insert_entry_chamfer >= self.insert_flange_diameter:
            raise ValueError("Bushing flange needs a bearing land outside the chamfer")
        if self.adjuster_support_length - self.insert_entry_chamfer < self.insert_min_material_thickness:
            raise ValueError("Insert support must meet the drawing minimum beyond the entry chamfer")
        if self.adjuster_clearance_travel >= self.adjuster_screw_length - self.insert_overall_length:
            raise ValueError("Adjuster must retain full insert engagement with end margin")
        self.tube_clamp_parameters.validate()
        if not 220 <= self.tube_clamp_relief_arc <= 270:
            raise ValueError("Keep a substantial 90–140 degree tube-clamp ligament")
        if self.tube_clamp_ear_plate_gap < self.tube_clamp_root_fillet:
            raise ValueError("Clamp ears must remain clear of the plate-root fillet")
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


def _build_fixed_body(p=None):
    p = p or CarriageParameters()
    p.validate()
    base = _box(p.plate_width, p.plate_length, p.plate_thickness, y=p.plate_center_y)
    for sign in (-1, 1):
        floor_width = p.track_outer_x - p.track_inner_x
        base = base.union(_box(floor_width, p.plate_length, p.guide_floor_rise,
                              x=sign * (p.track_outer_x + p.track_inner_x) / 2, y=p.plate_center_y, z=p.plate_thickness))
        land_width = p.plate_width / 2 - p.track_outer_x
        base = base.union(_box(land_width, p.plate_length, p.keeper_z - p.plate_thickness,
                              x=sign * (p.track_outer_x + land_width / 2), y=p.plate_center_y, z=p.plate_thickness))
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
    return _add_tube_clamp(base.cut(_insert_entry(p)), p).clean()


def _split_fixed_body(p):
    stock = _build_fixed_body(p)
    base = stock.intersect(_box(p.plate_width, p.plate_length,
                               p.tube_clamp_depth + p.plate_thickness,
                               y=p.plate_center_y, z=-p.tube_clamp_depth))
    frame = stock.intersect(_box(p.plate_width, p.plate_length,
                                p.keeper_z - p.plate_thickness, y=p.plate_center_y, z=p.plate_thickness))
    # Male locators belong to the frame: the base deck stays flat for clamp-up printing.
    locator_x = (p.track_outer_x + p.plate_width / 2) / 2
    for x in (-locator_x, locator_x):
        pin = cq.Workplane("XY", origin=(x, 0, p.plate_thickness - p.locator_height)).circle(
            p.locator_diameter / 2).extrude(p.locator_height)
        pocket_depth = p.locator_height + p.locator_depth_clearance
        pocket = cq.Workplane("XY", origin=(x, 0, p.plate_thickness - pocket_depth)).circle(
            (p.locator_diameter + p.locator_diametral_clearance) / 2).extrude(pocket_depth)
        base = base.cut(pocket)
        frame = frame.union(pin)
    return base.clean(), frame.clean()


def build_base_plate(p=None):
    return _split_fixed_body(p or CarriageParameters())[0]


def build_guide_frame(p=None):
    return _split_fixed_body(p or CarriageParameters())[1]


def _add_tube_clamp(base, p):
    """Rear boss with a transverse circumferential slit and rear axial split.

    All compliance cuts stay behind the plate and root fillet. The tube seats
    against the intact plate back surrounding its circular optical aperture.
    """
    c = p.tube_clamp_parameters
    collar = cq.Workplane("XY", origin=(0, 0, -p.tube_clamp_depth)).circle(c.outer_radius).extrude(p.tube_clamp_depth)
    ear_end = c.ear_root_x + c.ear_width
    for sign in (-1, 1):
        collar = collar.union(_box(ear_end, c.screw_ear_thickness, c.axial_width,
                                  x=ear_end / 2,
                                  y=sign * (c.split_gap + c.screw_ear_thickness) / 2,
                                  z=-p.tube_clamp_depth))
    root_y = c.split_gap / 2 + c.screw_ear_thickness
    root_x = sqrt(c.outer_radius**2 - root_y**2)
    edges = [e for e in collar.edges("|Z").vals()
             if abs(e.Center().x - root_x) < 1e-6 and abs(abs(e.Center().y) - root_y) < 1e-6]
    collar = collar.newObject(edges).fillet(c.ear_root_fillet)
    base = base.union(collar).clean()
    # Explicit revolved quarter-circle avoids a fragile edge-fillet operation
    # on the already split collar. Relief cuts below open the compliant sector.
    radius = p.tube_clamp_root_fillet
    r = c.outer_radius
    root = (cq.Workplane("XZ").moveTo(r, -radius).lineTo(r, 0).lineTo(r + radius, 0)
            .threePointArc((r + radius * (1 - 2**-0.5), -radius * (1 - 2**-0.5)),
                           (r, -radius)).close().revolve(360, (0, 0), (0, 1)))
    base = base.union(root)

    # Transverse slit passes radially through the boss wall, beyond the fillet.
    # A 120-degree ligament on -X connects the rear clamping band to the boss.
    inner = c.bore_diameter / 2 - 1
    outer = c.outer_radius + 1
    half_angle = radians(p.tube_clamp_relief_arc / 2)
    def polar(radius, angle):
        return (radius * cos(angle), radius * sin(angle))
    z0 = p.tube_clamp_slit_front_z - p.tube_clamp_relief_width
    relief = (cq.Workplane("XY", origin=(0, 0, z0))
              .moveTo(*polar(inner, -half_angle))
              .threePointArc((inner, 0), polar(inner, half_angle))
              .lineTo(*polar(outer, half_angle))
              .threePointArc((outer, 0), polar(outer, -half_angle)).close()
              .extrude(p.tube_clamp_relief_width))
    # Rounded ends across the radial wall avoid square-ended flexure cuts.
    for angle in (-half_angle, half_angle):
        x, y = polar(inner, angle)
        end = cq.Solid.makeCylinder(p.tube_clamp_relief_width / 2, outer - inner,
                                   cq.Vector(x, y, z0 + p.tube_clamp_relief_width / 2),
                                   cq.Vector(cos(angle), sin(angle), 0))
        relief = relief.union(end)
    # Perpendicular axial split joins the circumferential slit, never the plate.
    split_top = z0 + p.tube_clamp_relief_width / 2
    split = _box(ear_end + 1, p.tube_clamp_split,
                 p.tube_clamp_depth + 1 + split_top,
                 x=(ear_end + 1) / 2, z=-p.tube_clamp_depth - 1)
    bore = (cq.Workplane("XY", origin=(0, 0, -p.tube_clamp_depth - 1))
            .circle(c.bore_diameter / 2).extrude(p.tube_clamp_depth + 1))
    base = base.cut(bore).cut(relief.union(split))
    screw_y = -c.split_gap / 2 - c.screw_ear_thickness
    nut_y = c.split_gap / 2 + c.nut_ear_thickness
    screw_z = -p.tube_clamp_depth + c.axial_width / 2
    screw = cq.Solid.makeCylinder(c.screw_clearance_diameter / 2, nut_y - screw_y + 2,
                                 cq.Vector(c.screw_x, screw_y - 1, screw_z), cq.Vector(0, 1, 0))
    plane = cq.Plane(origin=(c.screw_x, nut_y - c.nut_pocket_depth, screw_z),
                     xDir=(1, 0, 0), normal=(0, 1, 0))
    pocket = cq.Workplane(plane).polygon(6, (c.nut_across_flats + c.nut_across_flats_clearance) / cos(pi/6)).extrude(c.nut_pocket_depth + 1)
    base = base.cut(screw).cut(pocket).clean()
    if len(base.solids().vals()) != 1 or not base.val().isValid():
        raise ValueError("Carriage and flexure clamp must remain one valid solid")
    return base


def _keeper_envelope(p, height):
    return _box(p.plate_width, p.plate_length, height, y=p.plate_center_y, z=p.keeper_z).cut(
        _box(p.keeper_opening_width, p.keeper_opening_length, height,
             y=p.keeper_opening_y, z=p.keeper_z))


def _insert_entry(p):
    return cq.Solid.makeCone(p.insert_bore_diameter / 2,
                             p.insert_bore_diameter / 2 + p.insert_entry_chamfer,
                             p.insert_entry_chamfer,
                             cq.Vector(0, p.plate_ymax-p.insert_entry_chamfer, p.adjuster_axis_z),
                             cq.Vector(0, 1, 0))


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
    return keeper.cut(_insert_entry(p)).clean()


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
    """Five independently selectable printed parts; retraction only at fiducial.

    Spring solid height is unverified: the loading pose checks printed geometry,
    not whether the purchased spring can safely reach that compression.
    """
    p = p or CarriageParameters()
    p.validate()
    if abs(travel) > p.working_half_travel or not 0 <= retract <= p.loading_retraction:
        raise ValueError("Requested pose exceeds supported travel")
    if retract and travel:
        raise ValueError("Return to fiducial before retracting for loading")
    base, frame = _split_fixed_body(p)
    assembly = cq.Assembly(name="Carriage (preliminary)")
    for name, part, color in (
        ("Base plate", base, (0.65, 0.65, 0.7)),
        ("Guide frame", frame, (0.6, 0.75, 0.8)),
        ("Keeper plate", build_keeper_plate(p), (0.35, 0.5, 0.75)),
        ("Driven plunger", build_plunger(p).translate((0, travel, 0)), (0.85, 0.65, 0.25)),
        ("Spring plunger", build_plunger(p, spring=True).translate((0, travel - retract, 0)), (0.4, 0.75, 0.5)),
    ):
        assembly.add(part, name=name, color=cq.Color(*color))
    return assembly

"""Preliminary five-piece cutoff carriage, design §8.

Local XY is the cassette plane, +Y points toward the FAS100, +Z is the
cassette-loading side, which faces the mirror (§8.1). Z=0 is the plate back, not the rail-height datum.
The rear shouldered spigot, clamped directly by the SM1RC/M, is integral with the base. Dimensions beyond
explicit baseline interfaces are provisional first-print targets; no purchased threads are modeled.
The base and guide frame are one stock body split at the top of the deck; `build_print_layout` gives the
parts as exported, with the base flipped spigot-up and the two plungers laid out side by side.
"""

from dataclasses import dataclass
from itertools import pairwise
from math import cos, pi, radians, tan

from build123d import (
    Axis,
    Compound,
    Plane,
    Polygon,
    Pos,
    Rot,
    chamfer,
    extrude,
    mirror,
)

from schlieren.cad import (
    CUT_OVERRUN,
    assembly,
    compression_spring,
    floor_box,
    labeled,
    x_cylinder,
    y_cone,
    y_cylinder,
    z_cylinder,
    z_hex,
)
from schlieren.hardware import (
    FAS100_PITCH,
    FAS100_THREAD_LENGTH,
    INSERT_98625A950_BODY_DIAMETER,
    INSERT_98625A950_BODY_LENGTH,
    INSERT_98625A950_FLANGE_DIAMETER,
    INSERT_98625A950_FLANGE_THICKNESS,
    INSERT_98625A950_LENGTH,
    INSERT_98625A950_MIN_MATERIAL,
    M3_CLEARANCE_DIAMETER,
    M3_NUT_ACROSS_FLATS,
    MAGNET_LENGTH,
    MAGNET_THICKNESS,
    MAGNET_WIDTH,
    SPRING_2006N292_FREE_LENGTH,
    SPRING_2006N292_OUTER_DIAMETER,
    SPRING_2006N292_WIRE_DIAMETER,
)
from schlieren.palette import (
    BRASS,
    METAL,
    PRINTED_AMBER,
    PRINTED_GRAY,
    PRINTED_GREEN,
    PRINTED_INDIGO,
    PRINTED_SKY,
    STEEL,
)
from schlieren.parts.adjuster import bearing_magnet, fas100_children, insert_98625a950
from schlieren.parts.rail_shoe import RailShoeParameters, post_stack
from schlieren.standards import (
    DATUM_DISC_THICKNESS,
    INCH,
    MAGNET_POCKET_CLEARANCE,
    NUT_POCKET_ACROSS_FLATS_CLEARANCE,
    OPTICAL_HEIGHT,
    PLA_MODULUS,
    POST_DIAMETER,
    POST_LENGTH,
)
from schlieren.validation import require_positive_dimensions
from schlieren.vendor_cad import SM1RC_M_THICKNESS


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
    # Post stack (§5) and Thorlabs SM1RC/M (vendor STEP model): Ø1.21 in bore accepting Ø1.20 in SM1 tubes.
    optical_height: float = OPTICAL_HEIGHT
    datum_thickness: float = DATUM_DISC_THICKNESS
    post_length: float = POST_LENGTH
    post_diameter: float = POST_DIAMETER
    ring_thickness: float = SM1RC_M_THICKNESS
    ring_bore: float = 1.21 * INCH
    # Rear spigot, same interface as the slit-head adapter (§7.6); printed at the SM1 tube nominal.
    spigot_diameter: float = 1.20 * INCH
    # Plate back to ring face, set by a shoulder on the spigot that the ring seats against. Longer than the
    # slit head's: the plate reaches below the rail-shoe top, so it must clear the shoe end, not just the post.
    ring_gap: float = 12.0
    spigot_shoulder_diameter: float = 34.0  # Bears on the SM1RC/M face outside its Ø30.7 mm bore.
    post_clearance: float = (
        2.0  # Minimum, plate back to post and rail shoe, and rotating parts to the rail top.
    )

    guide_floor_rise: float = 2.0
    ear_thickness: float = 3.0
    guide_axial_clearance: float = 0.4
    keeper_thickness: float = 3.0
    # Side members carry the plunger-ear wedge reactions between the screws. 3 mm with the side screws; a 5 mm
    # keeper is the fallback if the print shows too much lift (`uv run carriage --keeper-side-thickness 5`).
    keeper_side_thickness: float = 3.0
    ear_lower_clearance: float = 0.15
    body_deck_clearance: float = 0.3  # Provisional PLA running clearance.
    body_width: float = 58.0
    body_length: float = 10.0
    body_top: float = 12.0
    ear_outer_x: float = 37.0
    track_inner_x: float = 32.3  # Clear the full 64 mm cassette swept footprint.
    track_outer_x: float = 38.0
    keeper_opening_width: float = 66.0
    keeper_end_member_width: float = 5.0
    fastener_edge_margin: float = 4.5
    # The guide tracks are filled solid beyond the plunger ears' outermost positions, giving an end stop and a
    # solid seat for the keeper screws, which sit inboard of the plate ends to stay inside the rotation envelope.
    ear_stop_gap: float = 1.0  # Track end stop beyond the outermost ear position.
    fastener_stop_margin: float = (
        4.0  # Screw axis beyond the track end stop; keeps the nut pocket in the fill.
    )
    envelope_nut_wall: float = 1.0  # Minimum PLA between a nut pocket and the rotation envelope.
    # Side keeper screws beside each plunger's ear travel, in round lugs that widen the plate locally.
    side_fastener_x: float = 42.0
    side_lug_radius: float = 5.0  # Leaves ~1.65 mm PLA outside the captive nut.
    pla_modulus: float = PLA_MODULUS
    datum_pin_shank: float = 0.050 * INCH  # Measured (calipers), in-hand brads.
    # Brad holes only. Measured on the first base-plate print: the Ø24 mm aperture printed Ø23.62 mm (0.930 in);
    # brad holes with 0.08 mm diametral clearance would not start a shank. Compensate them, where a few
    # tenths decide the fit; M3 holes and nut pockets printed snug but usable and are left as they are.
    datum_hole_print_allowance: float = 0.38  # Diametral.
    datum_hole_fit_clearance: float = 0.10  # Diametral, as printed; CA retains the pins.
    datum_projection: float = 1.0  # UNMEASURED domed-head contact height.
    bevel_depth: float = 1.25
    bevel_angle: float = 27.5  # Provisional convention: from cassette plane.
    spring_free_length: float = SPRING_2006N292_FREE_LENGTH
    spring_fiducial_length: float = 16.5
    spring_axis_z: float = 7.5
    spring_outer_diameter: float = SPRING_2006N292_OUTER_DIAMETER
    spring_wire_diameter: float = SPRING_2006N292_WIRE_DIAMETER
    spring_display_coils: float = 10.0  # Total turns of the displayed helix; approximate.
    # Each spring end sits in a printed cup open toward the deck: sides and roof locate the coil, the deck
    # carries it, and nothing penetrates the frame end wall.
    spring_cup_clearance: float = 1.0  # Diametral; printed-hole shrink and coil growth under compression.
    spring_cup_depth: float = 3.0
    spring_cup_wall: float = 1.2
    spring_cup_end_gap: float = 2.0  # Minimum, cup to cup at the most-compressed pose.
    # Retraction thumb tab on the spring plunger's front face, at its outboard end.
    thumb_tab_width: float = 20.0
    thumb_tab_thickness: float = 3.0
    thumb_tab_height: float = 6.0
    thumb_tab_chamfer: float = (
        0.5  # Exposed edges, for comfort; the spring-facing (outboard) face stays square.
    )
    thumb_tab_bead_radius: float = 0.8  # Grip bead along the inner (thumb-side) top edge; prints unsupported.
    # McMaster 98625A950 manufacturer drawing, canonical baseline §8.3.
    insert_body_diameter: float = INSERT_98625A950_BODY_DIAMETER
    insert_drill_diameter: float = INSERT_98625A950_BODY_DIAMETER
    insert_overall_length: float = INSERT_98625A950_LENGTH
    insert_body_length: float = INSERT_98625A950_BODY_LENGTH  # Under the flange, independently specified.
    insert_min_material_thickness: float = INSERT_98625A950_MIN_MATERIAL
    insert_flange_diameter: float = INSERT_98625A950_FLANGE_DIAMETER
    insert_flange_thickness: float = INSERT_98625A950_FLANGE_THICKNESS
    insert_entry_chamfer: float = 0.1  # 45-degree entry, outboard face.
    insert_flange_pocket_clearance: float = 0.2  # Diametral, flange pocket on the inner face of the block.
    adjuster_screw_length: float = FAS100_THREAD_LENGTH
    adjuster_pitch: float = FAS100_PITCH
    adjuster_clearance_travel: float = 15.5  # Maximum tip extension from insert inner end.
    adjuster_support_length: float = 8.5
    support_top: float = 14.0
    magnet_length: float = MAGNET_LENGTH
    magnet_width: float = MAGNET_WIDTH
    magnet_thickness: float = MAGNET_THICKNESS
    magnet_pocket_clearance: float = MAGNET_POCKET_CLEARANCE  # Total, across the magnet's length and width.
    magnet_face_recess: float = 0.15  # Magnet face below the plunger's outer face: the pocket's extra depth.
    screw_clearance: float = M3_CLEARANCE_DIAMETER
    screw_head_clearance: float = 5.8
    screw_head_recess: float = 0.5
    nut_pocket_af: float = M3_NUT_ACROSS_FLATS + NUT_POCKET_ACROSS_FLATS_CLEARANCE
    nut_pocket_depth: float = 2.5

    @property
    def insert_bore_diameter(self):
        # Nominal drawing bore; physically finish and fit-check the printed pilot.
        return self.insert_drill_diameter

    @property
    def spigot_bore(self):
        # The light path through the spigot matches the plate aperture.
        return self.aperture_diameter

    @property
    def spigot_length(self):
        # Rearward from the plate back; the spigot end is flush with the ring's rear face.
        return self.ring_gap + self.ring_thickness

    @property
    def post_axis_z(self):
        return -self.ring_gap - self.ring_thickness / 2

    @property
    def post_top_below_axis(self):
        return self.optical_height - self.datum_thickness - self.post_length

    @property
    def shoe_half_length(self):
        return RailShoeParameters().length / 2

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
        return self.cassette_size / 2 + self.body_length - self.magnet_face_recess

    @property
    def plate_ymin(self):
        return self.spring_seat_y - self.rear_wall_thickness

    @property
    def plate_ymax(self):
        # Outer face of the adjuster block, placed to retain full insert engagement at -5 mm travel.
        return (
            self.magnet_contact_y
            - self.working_half_travel
            + self.adjuster_clearance_travel
            + self.insert_overall_length
        )

    @property
    def insert_flange_face(self):
        # Inner (cassette-side) face of the adjuster block: the flange bottoms here, in a flush pocket, and
        # the outboard reaction of the adjuster screw bears it against the block.
        return self.plate_ymax - self.adjuster_support_length

    @property
    def plate_length(self):
        return self.plate_ymax - self.plate_ymin

    @property
    def plate_center_y(self):
        return (self.plate_ymax + self.plate_ymin) / 2

    @property
    def keeper_opening_length(self):
        return self.plate_length - self.keeper_end_member_width - self.adjuster_support_length

    @property
    def keeper_opening_y(self):
        return self.plate_center_y + (self.keeper_end_member_width - self.adjuster_support_length) / 2

    @property
    def support_spans(self):
        # Adjuster block (bored for the insert), then the solid spring end wall.
        return (
            (self.plate_ymax - self.adjuster_support_length, self.plate_ymax),
            (self.plate_ymin, self.spring_seat_y),
        )

    @property
    def spring_cup_bore(self):
        return self.spring_outer_diameter + self.spring_cup_clearance

    @property
    def spring_cup_top(self):
        return self.spring_axis_z + self.spring_cup_bore / 2 + self.spring_cup_wall

    @property
    def rotation_envelope_radius(self):
        # Printed parts stay within this radius of the optical axis so the carriage rotates clear of the rail.
        return self.optical_height - self.post_clearance

    @property
    def ear_stops_y(self):
        # Spring end (loading retraction or working travel, whichever reaches farther), then driven end.
        reach = self.cassette_size / 2 + self.body_length + self.ear_stop_gap
        return (
            -(reach + max(self.loading_retraction, self.working_half_travel)),
            reach + self.working_half_travel,
        )

    @property
    def fasteners(self):
        x = self.plate_width / 2 - self.fastener_edge_margin
        spring_stop, driven_stop = self.ear_stops_y
        ends = [
            (sx * x, y)
            for sx in (-1, 1)
            for y in (spring_stop - self.fastener_stop_margin, driven_stop + self.fastener_stop_margin)
        ]
        return ends + self.side_fasteners

    @property
    def ear_center_y(self):
        # Plunger ear center at fiducial, magnitude; spring plunger at -y, driven at +y.
        return self.cassette_size / 2 + self.body_length / 2

    @property
    def side_fasteners(self):
        return [(sx * self.side_fastener_x, sy * self.ear_center_y) for sx in (-1, 1) for sy in (-1, 1)]

    @property
    def datum_points(self):
        # Broad triangle; swept tracks clear the aperture at either travel limit.
        return [(-23.0, -20.0), (23.0, -20.0), (0.0, 23.0)]

    @property
    def datum_hole_diameter(self):
        # As modeled; finish with a #54 (0.055 in, 1.40 mm) drill if a shank still binds.
        return self.datum_pin_shank + self.datum_hole_print_allowance + self.datum_hole_fit_clearance

    @property
    def keeper_side_width(self):
        return (self.plate_width - self.keeper_opening_width) / 2

    @property
    def keeper_screw_seat_z(self):
        # Screw-head seat; thicker side members get a deeper counterbore so the M3 x 12 stack is unchanged.
        return self.keeper_z + self.keeper_thickness - self.screw_head_recess

    def keeper_side_lift(self, load, travel=0.0, retract=0.0):
        """Largest upward keeper side-member deflection (mm) at an ear, for `load` N per ear, both plungers.

        First-order beam estimate: each span between adjacent screws is simply supported (conservative:
        ignores continuity over the screws and clamping at the heads), with the ear loads in it superposed.
        """
        ears = (-self.ear_center_y + travel - retract, self.ear_center_y + travel)
        screws = sorted({y for _, y in self.fasteners})
        inertia = self.keeper_side_width * self.keeper_side_thickness**3 / 12
        lift = 0.0
        for y0, y1 in pairwise(screws):
            span = y1 - y0
            loads = [e - y0 for e in ears if y0 < e < y1]
            for x in loads:
                total = 0.0
                for a in loads:
                    # Simply supported span, point load at a, deflection at x.
                    near, far = sorted((x, a))
                    total += (
                        load
                        * near
                        * (span - far)
                        * (2 * span * far - far**2 - near**2)
                        / (6 * span * self.pla_modulus * inertia)
                    )
                lift = max(lift, total)
        return lift

    def validate(self):
        require_positive_dimensions(self)
        if self.insert_bore_diameter >= self.insert_flange_diameter:
            raise ValueError("Bushing flange needs a bearing land outside the bore")
        if self.adjuster_support_length - self.insert_entry_chamfer < self.insert_min_material_thickness:
            raise ValueError("Insert support must meet the drawing minimum beyond the entry chamfer")
        if (
            self.insert_flange_thickness + self.insert_body_length + self.insert_entry_chamfer
            > self.adjuster_support_length
        ):
            raise ValueError("Flush-flanged insert must fit inside the adjuster block")
        if self.adjuster_clearance_travel >= self.adjuster_screw_length - self.insert_overall_length:
            raise ValueError("Adjuster must retain full insert engagement with end margin")
        if self.spigot_diameter >= self.ring_bore or self.spigot_bore >= self.spigot_diameter - 4:
            raise ValueError("Spigot must slip into the SM1RC/M and keep a wall")
        if self.spigot_shoulder_diameter < self.ring_bore + 2.0:
            raise ValueError("Spigot shoulder needs a land on the SM1RC/M face")
        if self.spigot_shoulder_diameter / 2 > self.post_top_below_axis - self.post_clearance:
            raise ValueError("Spigot shoulder must clear the post top")
        if -self.post_axis_z - max(self.post_diameter / 2, self.shoe_half_length) < self.post_clearance:
            raise ValueError("Plate back must clear the post and rail shoe")
        for x, y in self.datum_points:
            if (x * x + y * y) ** 0.5 - self.datum_pin_shank < self.spigot_shoulder_diameter / 2 + 1.0:
                raise ValueError("Datum-pin shanks must be trimmable outside the spigot shoulder")
        if any(end <= start for start, end in self.support_spans):
            raise ValueError("Support inner faces must lie inside the plate edges")
        if self.ear_lower_clearance >= self.guide_axial_clearance:
            raise ValueError("Ears need clearance below the keeper")
        if not self.body_width / 2 <= self.track_inner_x < self.ear_outer_x < self.track_outer_x:
            raise ValueError("Guide ears must fit the open tracks")
        if not self.cassette_size < self.keeper_opening_width < 2 * self.ear_outer_x:
            raise ValueError("Keeper must clear cassette and overlap ears")
        if self.spring_axis_z - self.spring_outer_diameter / 2 < self.plate_thickness:
            raise ValueError("Spring must ride clear of the deck")
        shortest = self.spring_fiducial_length - max(self.working_half_travel, self.loading_retraction)
        if shortest - 2 * self.spring_cup_depth < self.spring_cup_end_gap:
            raise ValueError("Spring cups collide at the most-compressed pose")
        nut_radius = self.nut_pocket_af / 2 / cos(pi / 6)
        for x, y in self.fasteners:
            if (x * x + y * y) ** 0.5 + nut_radius + self.envelope_nut_wall > self.rotation_envelope_radius:
                raise ValueError("Keeper fasteners must stay inside the rotation envelope")
        if self.fastener_stop_margin < nut_radius + 0.5:
            raise ValueError("Nut pockets must lie within the track fill")
        if self.side_fastener_x - self.screw_clearance / 2 < self.track_outer_x + 1.0:
            raise ValueError("Side keeper screws must clear the plunger guide tracks")
        if self.side_fastener_x + self.side_lug_radius <= self.plate_width / 2:
            raise ValueError("Side lugs must widen the plate around the side screws")
        if self.side_lug_radius < nut_radius + 1.5:
            raise ValueError("Side lugs need PLA outside the captive nuts")
        if self.keeper_side_thickness < self.keeper_thickness:
            raise ValueError("Keeper side members must be at least the nominal keeper thickness")
        if not 0 < self.thumb_tab_chamfer < min(self.thumb_tab_thickness, self.thumb_tab_height) / 2:
            raise ValueError("Thumb-tab chamfer must fit the tab")
        if self.thumb_tab_bead_radius >= self.thumb_tab_thickness:
            raise ValueError("Thumb-tab bead must be smaller than the tab")
        if self.thumb_tab_width >= self.body_width:
            raise ValueError("Thumb tab must sit on the plunger body")
        if self.nut_pocket_depth >= self.plate_thickness:
            raise ValueError("Nut pockets need bearing roofs")
        if self.spring_fiducial_length <= max(self.working_half_travel, self.loading_retraction):
            raise ValueError("Spring space exhausted")


def _build_fixed_body(p=None):
    p = p or CarriageParameters()
    p.validate()
    base = floor_box(p.plate_width, p.plate_length, p.plate_thickness, y=p.plate_center_y)
    for sign in (-1, 1):
        floor_width = p.track_outer_x - p.track_inner_x
        base += floor_box(
            floor_width,
            p.plate_length,
            p.guide_floor_rise,
            x=sign * (p.track_outer_x + p.track_inner_x) / 2,
            y=p.plate_center_y,
            z=p.plate_thickness,
        )
        land_width = p.plate_width / 2 - p.track_outer_x
        base += floor_box(
            land_width,
            p.plate_length,
            p.keeper_z - p.plate_thickness,
            x=sign * (p.track_outer_x + land_width / 2),
            y=p.plate_center_y,
            z=p.plate_thickness,
        )
    for start, end in p.support_spans:
        base += floor_box(
            p.plate_width,
            end - start,
            p.support_top - p.plate_thickness,
            y=(start + end) / 2,
            z=p.plate_thickness,
        )
    base += _side_lugs(p, 0, p.keeper_z)
    spring_stop, driven_stop = p.ear_stops_y
    for sign in (-1, 1):
        x = sign * (p.track_inner_x + p.track_outer_x) / 2
        for y0, y1 in ((p.plate_ymin, spring_stop), (driven_stop, p.plate_ymax)):
            base += floor_box(
                p.track_outer_x - p.track_inner_x,
                y1 - y0,
                p.keeper_z - p.plate_thickness,
                x=x,
                y=(y0 + y1) / 2,
                z=p.plate_thickness,
            )
    # Open-top keeper seating recess: preserves front-side removal and the
    # original screw stack while the support blocks extend to all plate edges.
    base -= _keeper_envelope(p, p.support_top - p.keeper_z)
    start, end = p.support_spans[0]
    base -= y_cylinder(p.insert_bore_diameter, 0, p.adjuster_axis_z, start - CUT_OVERRUN, end + CUT_OVERRUN)
    base -= _insert_flange_pocket(p)
    # End-wall spring cup; the guide-frame split truncates it at the keeper plane, and the keeper carries its roof.
    base += _spring_cup(p, p.spring_seat_y, p.plate_thickness)
    # The spigot and optical axis remain fixed while the cassette translates.
    base -= z_cylinder(p.aperture_diameter, 0, 0, 0, p.plate_thickness)
    for x, y in p.datum_points:
        base -= z_cylinder(p.datum_hole_diameter, x, y, 0, p.plate_thickness)
    for x, y in p.fasteners:
        base -= z_cylinder(p.screw_clearance, x, y, 0, p.keeper_z)
        base -= z_hex(p.nut_pocket_af, x, y, 0, p.nut_pocket_depth)
    return _add_spigot(base - _insert_entry(p), p) & _rotation_envelope(p)


def _split_fixed_body(p):
    stock = _build_fixed_body(p)
    width = 2 * (p.side_fastener_x + p.side_lug_radius) + 2  # Includes the side lugs.
    base = stock & floor_box(
        width, p.plate_length, p.spigot_length + p.plate_thickness, y=p.plate_center_y, z=-p.spigot_length
    )
    frame = stock & floor_box(
        width, p.plate_length, p.keeper_z - p.plate_thickness, y=p.plate_center_y, z=p.plate_thickness
    )
    # Male locators belong to the frame: the base deck stays flat for spigot-up printing.
    locator_x = (p.track_outer_x + p.plate_width / 2) / 2
    for x in (-locator_x, locator_x):
        pin = z_cylinder(p.locator_diameter, x, 0, p.plate_thickness - p.locator_height, p.plate_thickness)
        pocket_depth = p.locator_height + p.locator_depth_clearance
        pocket = z_cylinder(
            p.locator_diameter + p.locator_diametral_clearance,
            x,
            0,
            p.plate_thickness - pocket_depth,
            p.plate_thickness,
        )
        base -= pocket
        frame += pin
    return base, frame


def _add_spigot(base, p):
    """Rear hollow spigot clamped by the SM1RC/M; the ring seats against the shoulder.

    Printed with the base deck down and the spigot up, so it needs no supports.
    """
    ring_face = -p.ring_gap
    shoulder = z_cylinder(p.spigot_shoulder_diameter, 0, 0, ring_face, ring_face + p.ring_gap)
    spigot = z_cylinder(p.spigot_diameter, 0, 0, -p.spigot_length, -p.spigot_length + p.ring_thickness)
    bore = z_cylinder(p.spigot_bore, 0, 0, -p.spigot_length - CUT_OVERRUN, 0)
    base = base + shoulder + spigot - bore
    if len(base.solids()) != 1 or not base.is_valid:
        raise ValueError("Base plate and spigot must remain one valid solid")
    return base


def support_location(p=None, rotation=0.0):
    """Imaging rail frame (§3.4: +x right, +y along the rail toward the mirror, z up from the rail top, post at
    x=y=0) -> local carriage frame, with the carriage rotated by `rotation` degrees about the optical axis.

    The cassette-loading side (+Z) faces the mirror, so rail +y is local +Z and rail +x is local -X; the
    spigot, slip ring, and post are aft of the plate. Rotation 0 is the nominal zero of §8.1: fine adjuster
    (+Y) up.
    """
    p = p or CarriageParameters()
    return Rot(Z=-rotation) * Pos(0, -p.optical_height, p.post_axis_z) * Rot(Y=180) * Rot(X=-90)


def _side_lugs(p, z, height):
    """Round lugs around the side keeper screws, kept outboard of the guide-track walls."""
    lugs = None
    outer = p.side_fastener_x + p.side_lug_radius
    for x, y in p.side_fasteners:
        sign = 1 if x > 0 else -1
        lug = z_cylinder(2 * p.side_lug_radius, x, y, z, z + height) & floor_box(
            outer - p.track_outer_x,
            2 * p.side_lug_radius,
            height,
            x=sign * (p.track_outer_x + outer) / 2,
            y=y,
            z=z,
        )
        lugs = lug if lugs is None else lugs + lug
    return lugs


def _thumb_tab(p, outer_y):
    """Tab on the spring plunger's front face at its outboard end (+Y, unmirrored), with chamfered exposed edges
    except those of the spring-facing face, and a grip bead along the inner top edge, where the thumb pushes."""
    tab = floor_box(
        p.thumb_tab_width,
        p.thumb_tab_thickness,
        p.thumb_tab_height,
        y=outer_y - p.thumb_tab_thickness / 2,
        z=p.body_top,
    )
    top_and_vertical = tab.edges().group_by(Axis.Z)[-1] + tab.edges().filter_by(Axis.Z)
    edges = [e for e in top_and_vertical if outer_y - 1e-6 > e.center().Y]
    tab = chamfer(edges, p.thumb_tab_chamfer)
    top = p.body_top + p.thumb_tab_height
    length = p.thumb_tab_width - 2 * p.thumb_tab_chamfer
    bead = x_cylinder(
        2 * p.thumb_tab_bead_radius,
        outer_y - p.thumb_tab_thickness,
        top - p.thumb_tab_bead_radius,
        -length / 2,
        length / 2,
    )
    return tab + bead


def _rotation_envelope(p):
    """Cylinder about the optical axis that the fixed body and keeper are trimmed to; clips the plate corners."""
    height = 4 * p.spigot_length + p.support_top
    return z_cylinder(2 * p.rotation_envelope_radius, 0, 0, -height / 2, height / 2)


def _spring_cup(p, seat_y, bottom):
    """Cup around one spring end, extending +Y from its seat face at seat_y (the spring plunger is built
    unmirrored, so +Y is outboard there too).

    Open toward the deck: the legs stand on the print bed and the roof bridges the coil.
    """
    y0 = seat_y
    width = p.spring_cup_bore + 2 * p.spring_cup_wall
    cup = floor_box(
        width, p.spring_cup_depth, p.spring_cup_top - bottom, y=y0 + p.spring_cup_depth / 2, z=bottom
    )
    pocket = y_cylinder(
        p.spring_cup_bore, 0, p.spring_axis_z, y0 - CUT_OVERRUN, y0 + p.spring_cup_depth + CUT_OVERRUN
    )
    if bottom < p.spring_axis_z:
        pocket += floor_box(
            p.spring_cup_bore,
            p.spring_cup_depth + 2,
            p.spring_axis_z - bottom + 1,
            y=y0 + p.spring_cup_depth / 2,
            z=bottom - 1,
        )
    return cup - pocket


def _keeper_envelope(p, height):
    return floor_box(p.plate_width, p.plate_length, height, y=p.plate_center_y, z=p.keeper_z) - floor_box(
        p.keeper_opening_width, p.keeper_opening_length, height, y=p.keeper_opening_y, z=p.keeper_z
    )


def _insert_entry(p):
    return y_cone(
        p.insert_bore_diameter,
        p.insert_bore_diameter + 2 * p.insert_entry_chamfer,
        0,
        p.adjuster_axis_z,
        p.plate_ymax - p.insert_entry_chamfer,
        p.plate_ymax,
    )


def _insert_flange_pocket(p):
    # Flange-thick counterbore in the inner face of the adjuster block, so the flange sits flush.
    return y_cylinder(
        p.insert_flange_diameter + p.insert_flange_pocket_clearance,
        0,
        p.adjuster_axis_z,
        p.insert_flange_face,
        p.insert_flange_face + p.insert_flange_thickness,
    )


def build_keeper_plate(p=None):
    p = p or CarriageParameters()
    p.validate()
    keeper = _keeper_envelope(p, p.keeper_thickness)
    # Concentric crown maintains the nominal keeper thickness radially over
    # the insert bore. Clip at the mating plane to keep the base unchanged.
    start, end = p.support_spans[0]
    crown_radius = p.insert_bore_diameter / 2 + p.keeper_thickness
    crown = y_cylinder(2 * crown_radius, 0, p.adjuster_axis_z, start, end) & floor_box(
        2 * crown_radius,
        end - start,
        p.adjuster_axis_z + crown_radius - p.keeper_z,
        y=(start + end) / 2,
        z=p.keeper_z,
    )
    keeper += crown
    keeper -= y_cylinder(p.insert_bore_diameter, 0, p.adjuster_axis_z, start - CUT_OVERRUN, end + CUT_OVERRUN)
    keeper -= _insert_flange_pocket(p)
    keeper += _spring_cup(p, p.spring_seat_y, p.keeper_z)
    extra = p.keeper_side_thickness - p.keeper_thickness
    for sign in (-1, 1) if extra > 0 else ():
        keeper += floor_box(
            p.keeper_side_width,
            p.plate_length,
            extra,
            x=sign * (p.keeper_opening_width + p.keeper_side_width) / 2,
            y=p.plate_center_y,
            z=p.keeper_z + p.keeper_thickness,
        )
    keeper += _side_lugs(p, p.keeper_z, p.keeper_side_thickness)
    top = p.keeper_z + p.keeper_side_thickness
    for x, y in p.fasteners:
        keeper -= z_cylinder(p.screw_clearance, x, y, p.keeper_z, p.keeper_z + p.keeper_side_thickness)
        keeper -= z_cylinder(p.screw_head_clearance, x, y, p.keeper_screw_seat_z, top)
    return (keeper - _insert_entry(p)) & _rotation_envelope(p)


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
    profile = [
        (edge, bottom),
        (edge + p.body_length, bottom),
        (edge + p.body_length, p.body_top),
        (edge - inset, p.body_top),
        (edge - inset, front_z),
        (edge, bevel_z),
    ]
    body = extrude(Plane.YZ.offset(-p.body_width / 2) * Polygon(*profile, align=None), amount=p.body_width)
    # Overlap the body slightly to ensure a single connected printed solid.
    ear_root = p.body_width / 2 - 0.5
    for sign in (-1, 1):
        body += floor_box(
            p.ear_outer_x - ear_root,
            p.body_length,
            p.ear_thickness,
            x=sign * (p.ear_outer_x + ear_root) / 2,
            y=edge + p.body_length / 2,
            z=ear_bottom,
        )
    outer_y = edge + p.body_length
    if spring:
        # Spring cup outboard; thumb tab on the front face, pushed outboard from above the cassette to retract.
        body += _spring_cup(p, outer_y, bottom)
        body += _thumb_tab(p, outer_y)
        body = mirror(body, Plane.XZ)
    else:
        # Outward-opening, fully backed magnet pocket. A small adhesive tack is
        # needed for retention; the ball bears on the exposed broad XZ face.
        body -= floor_box(
            p.magnet_length + p.magnet_pocket_clearance,
            p.magnet_thickness + p.magnet_face_recess,
            p.magnet_width + p.magnet_pocket_clearance,
            y=outer_y - (p.magnet_thickness + p.magnet_face_recess) / 2,
            z=p.adjuster_axis_z - (p.magnet_width + p.magnet_pocket_clearance) / 2,
        )
    return body


def build_print_layout(p=None, plunger_gap=5.0):
    """The printed parts as exported, keyed by name: base_plate, guide_frame, keeper_plate, plungers.

    The base is flipped deck-down on z=0 for spigot-up printing; the guide frame and keeper keep assembly
    coordinates. The two plungers sit on z=0 side by side along y, centered on x, with plunger_gap between
    their bounding boxes, the spring plunger turned about z to match the driven one. The layout does not
    depend on the pose of the assembly.
    """
    p = p or CarriageParameters()
    base, frame = _split_fixed_body(p)
    plungers = []
    next_y = 0.0
    for spring in (False, True):
        solid = build_plunger(p, spring=spring)
        if spring:
            solid = Rot(Z=180) * solid
        box = solid.bounding_box()
        plungers.append(Pos(-(box.min.X + box.max.X) / 2, next_y - box.min.Y, -box.min.Z) * solid)
        next_y += box.size.Y + plunger_gap
    return {
        "base_plate": labeled(base, "Base plate", loc=Pos(0, 0, p.plate_thickness) * Rot(X=180)),
        "guide_frame": labeled(frame, "Guide frame"),
        "keeper_plate": labeled(build_keeper_plate(p), "Keeper plate"),
        "plungers": Compound([s for plunger in plungers for s in plunger.solids()]),
    }


def build_carriage(p=None, *, travel=0.0, retract=0.0, include_support=False, include_hardware=False):
    """Five independently selectable printed parts; retraction only at fiducial.

    `include_support` adds the SM1RC/M, TR50/M post, and rail shoe as references; `include_hardware` adds the
    FAS100 (vendor model), its 98625A950 bushing, the magnet bearing pad, and the 2006N292 spring (a display helix).

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
    children = [
        labeled(base, "Base plate", PRINTED_GRAY),
        labeled(frame, "Guide frame", PRINTED_SKY),
        labeled(build_keeper_plate(p), "Keeper plate", PRINTED_INDIGO),
        labeled(build_plunger(p), "Driven plunger", PRINTED_AMBER, Pos(0, travel, 0)),
        labeled(build_plunger(p, spring=True), "Spring plunger", PRINTED_GREEN, Pos(0, travel - retract, 0)),
    ]
    if include_support:
        children += post_stack(
            support_location(p),
            ring=True,
            optical_height=p.optical_height,
            datum_thickness=p.datum_thickness,
        )
    if include_hardware:
        children += _adjuster_hardware(p, travel)
        length = p.spring_fiducial_length + travel - retract
        spring = compression_spring(
            p.spring_outer_diameter, p.spring_wire_diameter, length, p.spring_display_coils
        )
        placed = Pos(0, p.spring_seat_y, p.spring_axis_z) * Rot(X=-90) * spring
        children.append(labeled(placed, "2006N292 spring", METAL))
    return assembly("Carriage (preliminary)", children)


def _adjuster_hardware(p, travel):
    """FAS100, bushing, and magnet pad as labeled children; the ball tip bears on the pad face."""
    tip_y = p.magnet_contact_y + travel
    # Vendor model axis +Z toward the knob, turned to +Y (outboard, toward the insert).
    fas100_loc = Pos(0, tip_y, p.adjuster_axis_z) * Rot(X=-90)
    # Flange on the inner face of the block, body running outboard. The frame's z runs along global +Y.
    along_y_axis = Pos(0, 0, p.adjuster_axis_z) * Rot(X=-90)
    bushing = insert_98625a950(
        p.insert_flange_face + p.insert_flange_thickness,
        p.insert_body_length,
        flange_side=-1,
        body_diameter=p.insert_body_diameter,
        flange_diameter=p.insert_flange_diameter,
        flange_thickness=p.insert_flange_thickness,
    )
    magnet = bearing_magnet(length=p.magnet_length, width=p.magnet_width, thickness=p.magnet_thickness)
    return [
        *fas100_children(fas100_loc),
        labeled(bushing, "98625A950 bushing", BRASS, along_y_axis),
        labeled(magnet, "Magnet pad", STEEL, fas100_loc),
    ]

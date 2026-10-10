"""Lens cradle and phone rest, design §§9.4-9.9.

The phone and the lens threaded onto its case are one rigid body, held by the lens barrel with the phone
hanging from it. Two separate rail fixtures:

- the lens cradle, specific to the lens. Two split collars clamp the barrel, the aft one on its rear
  cylindrical section and the fore one at the front of the long section, just behind the focus ring. Each
  collar rests on a pair of ball-tip screws at ±45° in a yoke; each pair sets x and z of the lens axis at its
  station, so together they set position, pitch, and yaw. The yokes are printed separately and bolted to one
  shoe straddling the rail. Three screw tips bear on magnet pads; the aft left one sits between two short
  dowel pins on its collar pad, which fixes the lens fore/aft. An endless elastic ring round the barrel beside each yoke,
  hooked on a peg on the yoke, holds each pad pair down;
- the phone rest, specific to the phone. The phone is carried by its lens mount and is not gripped, but it
  hangs well to one side of the lens axis, so its weight would turn the lens in its collars. Its lower edge
  rests on one dowel pin lying along the rail, on the arm of a small shoe of its own. The rest is
  fixed: roll changes slightly as the aft collar is raised or lowered, which does not matter. A different
  phone needs only this part redesigned.

The cradle parts are modeled in detail: fillets, pad pockets, clamp ear, insert holes, joint, and pegs. The
lens, phone, and hardware are envelopes, except the McMaster screws, thumb nuts, inserts, and dowel pins, which
are vendor models; the clamp screws and nuts and the rail clamp screws are not drawn. The phone rest has no retainer or
safety catch yet. The phone dimensions are the §9.1 measurements and Apple's drawing, and the lens section
lengths and barrel diameter are measured (§9.2); the focus-ring diameter is
assumed, and the lens aft end is taken to be at the phone's back.

Coordinates: the §3.4 imaging rail frame, +x right, +y along the rail toward the mirror, z up from the rail
top. y=0 is the back of the cased phone.
"""

from dataclasses import dataclass, field
from math import asin, atan2, cos, degrees, hypot, pi, radians, sin, sqrt, tan

from build123d import (
    Align,
    Axis,
    Box,
    Compound,
    Edge,
    Face,
    Location,
    Part,
    Plane,
    Pos,
    RegularPolygon,
    Rot,
    Solid,
    Vector,
    Wire,
    chamfer,
    extrude,
    fillet,
)

from schlieren.cad import (
    along_x,
    along_y,
    assembly,
    box_between,
    centered_cylinder,
    floor_box,
    labeled,
    place,
    x_cylinder,
    y_cylinder,
    z_cone,
    z_cylinder,
)
from schlieren.palette import (
    AXIS_RED,
    BAND_RED,
    BLACK_ANODIZED,
    BLACK_OXIDE,
    BRASS,
    FOCUS_RING_GRAY,
    LENS_BLACK,
    PHONE_BODY,
    PRINTED_BLUE,
    PRINTED_GREEN,
    PRINTED_ORANGE,
    STEEL,
)
from schlieren.parts.rail import build_rail
from schlieren.parts.rail_shoe import RailShoeParameters
from schlieren.standards import INCH, OPTICAL_HEIGHT
from schlieren.vendor_cad import (
    MCMASTER_92815A202_HEIGHT,
    MCMASTER_93339A252_BALL_DIAMETER,
    MCMASTER_93339A252_LENGTH,
    MCMASTER_94459A797_FLANGE_DIAMETER,
    MCMASTER_94459A797_LENGTH,
    mcmaster_91585a351,
    mcmaster_91585a457,
    mcmaster_92815a202,
    mcmaster_93339a252,
    mcmaster_94459a797,
)

YOKE_BOSS_OVERRUN = 0.5  # Arm material behind the end of the screw at nominal.
LENS_TO_SLIP_RING = 10.0  # Assumed gap, lens front to the cutoff slip ring's rear face (§8.1).


@dataclass(frozen=True)
class CameraSupportParameters:
    optical_height: float = OPTICAL_HEIGHT  # §3.4.
    rail_size: float = 20.0

    # Phone in its case, landscape, screen aft (§9.1), Main camera (the lower aperture in portrait) on the axis.
    # Bare-phone dimensions are from Apple's drawing, docs/reference/Apple-iPhone-17.pdf.
    camera_height_above_edge: float = 60.6  # Measured in the case, §9.1.
    camera_inset_from_end: float = 34.3  # Measured in the case, §9.1: Main camera from the near short edge.
    bare_phone_length: float = 149.61
    bare_phone_width: float = 71.45
    bare_camera_from_side_edge: float = 13.62  # Both rear cameras, from the nearer long edge.
    phone_thickness: float = 0.510 * INCH  # Measured over the case, §9.1; the bare phone is 7.95 mm.

    # Lens sections from the aft end, measured (§9.2): aft stub, rear barrel section, long barrel section,
    # focus ring, front lip. Both barrel sections are 37.0 mm in diameter to within 0.05 mm.
    lens_diameter: float = 37.0
    aft_stub_length: float = 0.565 * INCH
    rear_section_length: float = 1.300 * INCH
    long_section_length: float = 2.25 * INCH
    focus_ring_length: float = 0.455 * INCH
    front_lip_length: float = 0.175 * INCH
    focus_ring_diameter: float = 39.0  # Assumed, for the picture only.

    # Adjusters (§9.7): McMaster 93339A252 ball-tip screw in a 94459A797 heat-set insert, with a 92815A202
    # thumb nut locked mid-screw.
    screw_length: float = MCMASTER_93339A252_LENGTH  # Overall, hex-socket end to ball apex.
    ball_diameter: float = MCMASTER_93339A252_BALL_DIAMETER
    nut_below_tip: float = 5.0  # Ball apex to the near face of the thumb nut.
    screw_angle: float = 45.0  # Each side of straight down, degrees.
    magnet_length: float = 10.0  # Across the rail: the direction each pad slides most.
    magnet_width: float = 5.0
    magnet_thickness: float = 2.0
    groove_rod_diameter: float = 3.0
    groove_rod_length: float = 10.0

    # Lens cradle.
    aft_station: float = (
        24.0  # Aft collar center from the lens aft end; leaves finger room ahead of the phone.
    )
    fore_station: float = 96.5  # Fore collar center: its front face 2 mm behind the focus ring.
    collar_width: float = 12.0
    collar_bore_diametral_clearance: float = (
        0.30  # Over the barrel (measured 37.01 to 37.06 mm); fit-test it.
    )
    collar_wall: float = 3.0  # Ring wall: the pad pockets and the ear carry the local thickness.
    collar_end_fillet: float = 1.0  # Outer edges round the ring ends, for the fingers.
    collar_root_fillet: float = 2.0  # Inside corners, ear and pad platforms to the ring.
    collar_round_fillet: float = 1.0  # Other outside corners of the ear and pad platforms.
    # Split clamp, the common M3 hardware of 5.3: the screw passes a thin ear into a captured nut in the
    # other, as on the common rail shoe (whose split and ear thicknesses it takes).
    clamp_screw_above_ring: float = 4.25  # Screw axis above the ring top; the head clears the root fillet.
    ear_top_above_ring: float = 8.75
    clamp_head_diameter: float = 5.5  # Screw head, which the ear must clear.
    # Pad pockets: each bearing surface sits in a pocket whose rim stands above it, so a ball end that
    # wanders reaches a wall instead of the edge of the pad. The rim stays below the screw's end face, which
    # is 1.2 mm behind the ball apex.
    pad_wall_height: float = 0.8  # Rim above the pad face.
    pad_wall: float = 1.5  # Wall round each pocket.
    pad_pocket_clearance_per_side: float = 0.10  # Magnet or rod pair in its pocket, bonded.
    pad_edge_margin: float = 1.0  # A ball apex can reach to within this of the pad edge (the rim stops it).
    min_collar_wall: float = 2.5
    # Retaining band (§9.5 hold-down): an endless elastic cord round the bare barrel beside each collar, on
    # the side toward the other collar, with its legs running down inboard of the thumb nuts to a peg on the
    # centre of the yoke's crossbar face. Its pull acts on the barrel, which the collar's clamp carries to the
    # pads; no groove is needed on the collar.
    band_cord_diameter: float = 2.0
    band_hold_down: float = 5.0  # N at each pad pair, §9.5, from the two bands together.
    horn_diameter: float = 4.0  # The peg's stem.
    horn_stem_length: float = 6.0
    horn_lip_diameter: float = 6.0
    horn_lip_height: float = 1.0
    horn_neck_below_lip: float = 1.2  # Where the cord lies on the stem, below the lip.
    yoke_boss_length: float = (
        10.0  # Along each screw: holds the insert, and leaves the thumb nut 5 mm of travel.
    )
    yoke_boss_width: float = 16.0  # Across the screw axis, to the outboard end of the arm.
    yoke_clearance_below_collar: float = 13.0  # Crossbar top below the collar, clear of the thumb nuts.
    yoke_crossbar: float = 10.0
    # Thickness of the yoke along the rail. Walls round the insert holes and counterbores are
    # (thickness - 8.12 mm)/2, about 3 mm; heat-set inserts want at least 2 mm in PLA.
    yoke_thickness: float = 14.0
    yoke_min_insert_wall: float = 2.5
    # Profile fillets, mm. The column root takes the arm's bending, so it is the largest; the free corners
    # are rounded to keep them from catching and to spread the stress where the profile turns.
    yoke_root_fillet: float = 5.0  # Column to crossbar underside, inside corner.
    yoke_blend_fillet: float = 4.0  # Crossbar underside to arm back, and arm face to crossbar top.
    yoke_corner_fillet: float = 2.0  # Outboard corners of the arm.
    # Lower clamp sections (saddle, skirts, side-slot holes) take the common rail shoe's dimensions, §5.3.
    rail_shoe: RailShoeParameters = field(default_factory=RailShoeParameters)
    cradle_clamp_spacing: float = 36.0  # Between the two pairs of rail clamp screws on the cradle shoe.
    # Yoke-to-shoe joint: each yoke is printed separately and bolted up through the shoe deck with one
    # countersunk M5 screw on the rail centerline, into a heat-set insert in the yoke column. Two straight
    # walls on the deck, across the rail, ahead of and behind the column, locate it and stop its twisting.
    locating_wall_thickness: float = 1.6  # Along the rail: four perimeters at a 0.4 mm nozzle.
    locating_wall_height: float = 3.0  # Above the deck.
    locating_clearance_per_side: float = 0.20  # Wall to column face, PLA fabrication allowance.
    insert_hole_diameter: float = 6.40  # McMaster 94459A797 drawing.
    insert_flange_thickness: float = 1.02  # McMaster 94459A797 drawing.
    insert_hole_relief: float = 1.0  # Hole depth beyond the insert, for the screw tip and melt.
    joint_screw_length: float = 10.0  # M5 countersunk, overall including the head.
    joint_screw_head_diameter: float = 10.0  # 90-degree head, ISO 10642.
    # Chamfer round the skirt ends, inside and out, so that the first-layer flare (elephant's foot) does not
    # narrow the rail opening or stand the skirts off the bed; it also eases the shoe onto the rail.
    skirt_foot_chamfer: float = 0.6
    cradle_end_margin: float = (
        9.0  # Cradle shoe beyond each yoke along the rail; symmetric about the stations.
    )

    # Phone rest.
    rest_x: float = 100.0  # Rest rod under the phone's lower edge, outboard of the axis.
    rest_rod_diameter: float = 4.0
    rest_rod_length: float = 20.0
    rest_shoe_length: float = 22.0  # Along the rail; the arm spans all of it, so it prints without a bridge.
    rest_arm_depth: float = 10.0  # Kept shallow so the root fillet stays above the side-slot screw head.
    rest_arm_overhang: float = 8.0  # Arm tip beyond the rod.
    rest_seat_clearance_per_side: float = 0.10  # Radial, rod in its half-round seat, bonded.
    # Profile fillets, mm. The root takes the arm's bending, so it is the largest.
    rest_root_fillet: float = 3.0  # Arm underside to the shoe's side wall, inside corner.
    rest_step_fillet: float = 2.0  # Arm top to the deck, inside corner.
    rest_edge_fillet: float = 2.0  # Outside corners of the arm: tip, and the step up from the deck.
    rest_seat_lip_fillet: float = 0.5  # Edges of the rod seat, where the phone slides on.
    clamp_screw_head_diameter: float = 8.5  # M5 socket head cap (ISO 4762), on the outside of each skirt.
    clamp_screw_head_clearance: float = 1.0  # Arm and its root fillet to the head, axial clearance.

    @property
    def shoe_outer(self) -> float:
        """Half the saddle width: the rail opening plus a side wall."""
        return self.rail_shoe.width / 2

    @property
    def rest_center(self) -> float:
        """Phone rest shoe center along the rail, where its clamp screws go: under the middle of the rod."""
        return self.rest_y

    @property
    def cradle_clamp_ys(self) -> tuple[float, float]:
        middle = sum(self.stations) / 2
        return middle - self.cradle_clamp_spacing / 2, middle + self.cradle_clamp_spacing / 2

    @property
    def deck_top(self) -> float:
        return self.rail_shoe.bridge_top

    @property
    def joint_z(self) -> float:
        """Underside of a yoke column, on the deck, where the insert flange sits."""
        return self.deck_top

    @property
    def yoke_top(self) -> float:
        """Top of the yoke column and crossbar."""
        return self.optical_height - self.collar_radius - self.yoke_clearance_below_collar

    @property
    def insert_hole_depth(self) -> float:
        return MCMASTER_94459A797_LENGTH + self.insert_hole_relief

    @property
    def case_wall(self) -> float:
        """Case edge wall, from the measured camera height; assumed the same on the unmeasured edges."""
        return self.camera_height_above_edge - (self.bare_phone_width - self.bare_camera_from_side_edge)

    @property
    def phone_length(self) -> float:
        return self.bare_phone_length + 2 * self.case_wall

    @property
    def phone_width(self) -> float:
        return self.bare_phone_width + 2 * self.case_wall

    @property
    def phone_bottom(self) -> float:
        return self.optical_height - self.camera_height_above_edge

    @property
    def lens_length(self) -> float:
        """Sum of the measured sections; §9.2 also lists an overall length of about 116.8 mm."""
        return (
            self.aft_stub_length
            + self.rear_section_length
            + self.long_section_length
            + self.focus_ring_length
            + self.front_lip_length
        )

    @property
    def focus_ring_start(self) -> float:
        return self.aft_stub_length + self.rear_section_length + self.long_section_length

    @property
    def stations(self) -> tuple[float, float]:
        return self.aft_station, self.fore_station

    @property
    def collar_bore(self) -> float:
        return self.lens_diameter + self.collar_bore_diametral_clearance

    @property
    def collar_radius(self) -> float:
        return self.collar_bore / 2 + self.collar_wall

    @property
    def pad_radius(self) -> float:
        """Lens axis to each screw tip, on the outer face of its pad.

        The pocket floor is tangent to the outside of the ring, so the pad stands a magnet thickness out.
        """
        return self.collar_radius + self.magnet_thickness

    @property
    def cord_radius(self) -> float:
        return self.band_cord_diameter / 2

    def toward_other(self, station: float) -> int:
        """+1 where a station faces the fore collar, -1 where it faces the aft collar."""
        return 1 if station < sum(self.stations) / 2 else -1

    def horn_base(self, station: float) -> tuple[float, float, float]:
        """Where a yoke's peg leaves the crossbar face, which faces the other collar."""
        face = station + self.toward_other(station) * self.yoke_thickness / 2
        return 0.0, face, self.yoke_top - self.yoke_crossbar / 2

    def band_y(self, station: float) -> float:
        """Along the lens, the plane of a band: the cord lies on the peg's neck."""
        return self.horn_base(station)[1] + self.toward_other(station) * (
            self.horn_stem_length - self.horn_neck_below_lip
        )

    @property
    def ear_top_wall(self) -> float:
        """Ear material over the nut pocket."""
        r = self.rail_shoe
        return (
            self.ear_top_above_ring
            - self.clamp_screw_above_ring
            - (r.clamp_nut_across_flats + r.nut_across_flats_clearance) / 2
        )

    @property
    def ear_screw_side(self) -> float:
        """Outer face of the screw ear, across the rail from the split."""
        return -(self.rail_shoe.split_gap / 2 + self.rail_shoe.screw_ear_thickness)

    @property
    def ear_nut_side(self) -> float:
        """Outer face of the nut ear."""
        return self.rail_shoe.split_gap / 2 + self.rail_shoe.nut_ear_thickness

    @property
    def ball_rim_standoff(self) -> float:
        """Across the pad, from the center of a ball sitting on it to where its sphere meets a rim edge that
        stands pad_wall_height above the pad face."""
        r, h = self.ball_diameter / 2, self.pad_wall_height
        return sqrt(r**2 - (r - h) ** 2)

    @property
    def pad_wall_relief(self) -> float:
        """How far the pocket opens outward from the pad edge above the pad face, per side.

        The rim is cut back so that the ball stops pad_edge_margin short of the pad edge, not at the edge
        of the sphere's reach against a rim standing at the pad edge.
        """
        return self.ball_rim_standoff - self.pad_edge_margin - self.pad_pocket_clearance_per_side

    @property
    def pad_edge_stop(self) -> tuple[float, float]:
        """How far a ball end can move from the middle of a magnet pad, across and along the rail, before its
        sphere meets the relieved rim."""
        reach = self.pad_pocket_clearance_per_side + self.pad_wall_relief - self.ball_rim_standoff
        return self.magnet_length / 2 + reach, self.magnet_width / 2 + reach

    @property
    def boss_top_below_tip(self) -> float:
        """Along a screw, from its ball apex to the lens-side face of its yoke boss."""
        return self.screw_length - self.yoke_boss_length

    @property
    def rest_y(self) -> float:
        """Under the middle of the phone's thickness."""
        return -self.phone_thickness / 2

    @property
    def rest_arm_top(self) -> float:
        """The rod lies half sunk in the arm, its top under the phone's lower edge."""
        return self.phone_bottom - self.rest_rod_diameter / 2

    def validate(self) -> None:
        half = self.collar_width / 2
        if self.aft_station - half < self.aft_stub_length:
            raise ValueError("The aft collar must sit on the rear cylindrical section")
        if self.aft_station + half > self.aft_stub_length + self.rear_section_length:
            raise ValueError("The aft collar must sit on the rear cylindrical section")
        if self.fore_station + half >= self.focus_ring_start:
            raise ValueError("The fore collar must stay behind the focus ring")
        r_ = self.rail_shoe
        across_corners = (r_.clamp_nut_across_flats + r_.nut_across_flats_clearance) / cos(radians(30))
        if self.collar_wall < self.min_collar_wall:
            raise ValueError("The collar ring is too thin")
        if self.ear_top_wall < 1.5:
            raise ValueError("The ear must leave material over the nut pocket")
        if self.clamp_screw_above_ring < (r_.clamp_nut_across_flats + r_.nut_across_flats_clearance) / 2:
            raise ValueError("The nut pocket must not cut into the ring")
        # The root fillet runs up the ear face from where it meets the ring, by its tangent length.
        x_ear = abs(self.ear_screw_side)
        ring_slope = asin(x_ear / self.collar_radius)
        root_rise = sqrt(self.collar_radius**2 - x_ear**2) - self.collar_radius
        fillet_top = root_rise + self.collar_root_fillet / tan((pi / 2 + ring_slope) / 2)
        if self.clamp_screw_above_ring - self.clamp_head_diameter / 2 < fillet_top:
            raise ValueError("The screw head must clear the fillet at the root of its ear")
        if (self.collar_width - across_corners) / 2 < 2.0:
            raise ValueError("The ear must leave walls beside the nut pocket")
        if not 0 <= self.pad_wall_relief < self.pad_wall / 2:
            raise ValueError("The pocket relief must be small against the wall round it")
        rod_pocket_along = _pad_pocket(self, True)[1] + 2 * self.pad_wall_relief
        if (self.collar_width - rod_pocket_along) / 2 < self.pad_wall:
            raise ValueError("The pad pockets must leave a wall along the rail")
        if self.horn_lip_diameter > self.yoke_crossbar - 2.0:
            raise ValueError("The horn lip must lie within the crossbar face")
        if (
            self.band_y(self.aft_station) + self.cord_radius
            >= self.band_y(self.fore_station) - self.cord_radius
        ):
            raise ValueError("The two bands must not cross")
        if self.pad_wall_height >= 1.2:
            raise ValueError("The pocket rim must stay below the screw's end face")
        if self.yoke_boss_length < MCMASTER_94459A797_LENGTH:
            raise ValueError("Each yoke boss must contain its heat-set insert")
        r = self.rail_shoe
        counterbore = MCMASTER_94459A797_FLANGE_DIAMETER + 0.2
        if (self.yoke_thickness - counterbore) / 2 < self.yoke_min_insert_wall:
            raise ValueError("The yoke must leave a wall round each insert")
        if (self.yoke_boss_width - counterbore) / 2 < self.yoke_min_insert_wall:
            raise ValueError("The yoke arm must leave a wall round each insert")
        if (self.rail_size - counterbore) / 2 < self.yoke_min_insert_wall:
            raise ValueError("The yoke column must leave a wall round the joint insert")
        if self.yoke_thickness < self.collar_width:
            raise ValueError("The yoke must be at least as thick as the collar")
        wall_inner = self.yoke_thickness / 2 + self.locating_clearance_per_side
        if wall_inner + self.locating_wall_thickness > self.cradle_end_margin:
            raise ValueError("The locating walls must stay on the cradle shoe")
        if self.rail_size > r.width:
            raise ValueError("The locating walls must stay on the deck")
        if self.joint_z + self.insert_hole_depth + 1.5 > self.yoke_top:
            raise ValueError("The yoke column must leave a roof over the insert")
        if not self.joint_z < self.joint_screw_length < self.joint_z + MCMASTER_94459A797_LENGTH:
            raise ValueError("The joint screw must end inside its insert")
        if self.rest_shoe_length < self.rest_rod_length:
            raise ValueError("The rest arm must be at least as long as the rod")
        head_top = -self.rail_shoe.rail_height / 2 + self.clamp_screw_head_diameter / 2
        if (
            self.rest_arm_top - self.rest_arm_depth - self.rest_root_fillet
            < head_top + self.clamp_screw_head_clearance
        ):
            raise ValueError("The rest arm root fillet must clear the side-slot screw head")
        if self.rest_arm_top <= self.deck_top + self.rest_step_fillet + self.rest_edge_fillet:
            raise ValueError("The rest arm must stand clear of the deck for the step fillets")
        if self.boss_top_below_tip < self.nut_below_tip + MCMASTER_92815A202_HEIGHT:
            raise ValueError("Each thumb nut must fit between its collar pad and its yoke boss")


def screw_location(p: CameraSupportParameters, side: int, station: float) -> Location:
    """Frame of the adjusting screw on side -1 (left) or +1 (right) at a station.

    The origin is the ball apex on its collar pad, +z points along the screw toward the lens axis, and local x
    lies across the rail, tangent to the collar.
    """
    angle = radians(p.screw_angle)
    r = p.pad_radius
    tip = (side * r * sin(angle), station, p.optical_height - r * cos(angle))
    return Pos(*tip) * Rot(Y=-side * p.screw_angle)


def _adjuster(p: CameraSupportParameters, name: str, loc: Location) -> list[Part]:
    """Screw, thumb-nut handwheel, and heat-set insert of one adjuster, placed by its screw frame."""
    nut = Pos(0, 0, -p.nut_below_tip - MCMASTER_92815A202_HEIGHT) * mcmaster_92815a202()
    # Flange on the lens-side face of the boss, so the screw's reaction presses the insert into its hole.
    insert = Pos(0, 0, -p.boss_top_below_tip) * mcmaster_94459a797()
    return [
        labeled(mcmaster_93339a252(), f"{name} screw", STEEL, loc),
        labeled(nut, f"{name} thumb nut", BLACK_OXIDE, loc),
        labeled(insert, f"{name} insert", BRASS, loc),
    ]


def rod_layout(p: CameraSupportParameters) -> tuple[float, float]:
    """Groove rods of the fore/aft stop pad: half the spacing of their axes, and their axes' height in the
    pad frame. The ball nests between them; the rods lie on the pocket floor."""
    ball_radius, rod_radius = p.ball_diameter / 2, p.groove_rod_diameter / 2
    half_spacing = p.groove_rod_diameter * 0.75
    nest = sqrt((ball_radius + rod_radius) ** 2 - half_spacing**2)  # Rod axes beyond the ball center.
    return half_spacing, nest - ball_radius


def _pad_pocket(p: CameraSupportParameters, rods: bool) -> tuple[float, float]:
    """Pocket size in a pad frame, across and along the rail: a magnet, or the pair of groove rods."""
    c = 2 * p.pad_pocket_clearance_per_side
    if rods:
        half_spacing, _ = rod_layout(p)
        return p.groove_rod_length + c, 2 * half_spacing + p.groove_rod_diameter + c
    return p.magnet_length + c, p.magnet_width + c


def _tangent(c1, r1, c2, r2):
    """Points where the outer tangent joins circle 1 to circle 2, going counterclockwise round the pair."""
    dx, dz = c2[0] - c1[0], c2[1] - c1[1]
    length = hypot(dx, dz)
    along = ((dx / length), (dz / length))
    k = (r1 - r2) / length
    right = (along[1], -along[0])
    n = (k * along[0] + sqrt(1 - k * k) * right[0], k * along[1] + sqrt(1 - k * k) * right[1])
    return (c1[0] + r1 * n[0], c1[1] + r1 * n[1]), (c2[0] + r2 * n[0], c2[1] + r2 * n[1])


def _arc(center, radius, start, finish):
    """("arc", start, mid, finish) going counterclockwise about center."""
    a0 = atan2(start[1] - center[1], start[0] - center[0])
    sweep_angle = (atan2(finish[1] - center[1], finish[0] - center[0]) - a0) % (2 * pi)
    mid = (center[0] + radius * cos(a0 + sweep_angle / 2), center[1] + radius * sin(a0 + sweep_angle / 2))
    return ("arc", start, mid, finish)


def band_path(p: CameraSupportParameters) -> list[tuple]:
    """Axis of a retaining band in its plane, as ("line", a, b) and ("arc", a, mid, b) pieces of (x, z).

    An endless loop: the convex hull of the cord lying on the barrel and on the neck of the peg below it,
    counterclockwise from the barrel's right tangent: arc over the top, left leg down, arc under the peg,
    right leg up. The same for both bands.
    """
    barrel = ((0.0, p.optical_height), p.lens_diameter / 2 + p.cord_radius)
    peg = ((0.0, p.horn_base(p.aft_station)[2]), p.horn_diameter / 2 + p.cord_radius)
    left = _tangent(*barrel, *peg)  # Barrel to peg: down the left side.
    right = _tangent(*peg, *barrel)  # Peg to barrel: up the right side.
    return [
        _arc(*barrel, right[1], left[0]),
        ("line", *left),
        _arc(*peg, left[1], right[0]),
        ("line", *right),
    ]


def band_leg_angle(p: CameraSupportParameters) -> float:
    """Angle above horizontal of the band's legs, degrees."""
    _, a, b = band_path(p)[1]
    return degrees(atan2(abs(b[1] - a[1]), abs(b[0] - a[0])))


def _band_wire(p: CameraSupportParameters, station: float) -> Wire:
    y = p.band_y(station)
    edges = []
    for kind, *points in band_path(p):
        vs = [Vector(x, y, z) for x, z in points]
        edges.append(Edge.make_line(*vs) if kind == "line" else Edge.make_three_point_arc(*vs))
    return Wire(edges)


def _swept_circle(wire: Wire, radius: float) -> Part:
    section = Face(Wire.make_circle(radius, Plane(origin=wire.start_point(), z_dir=wire.tangent_at(0))))
    return Part([Solid.sweep(section, path=wire)])


def build_band(p: CameraSupportParameters | None = None, station: float = 0.0) -> Part:
    """The endless retaining cord of a collar, on the barrel and the neck of its yoke's peg."""
    p = p or CameraSupportParameters()
    return _swept_circle(_band_wire(p, station), p.cord_radius)


def _edges_along_rail(body: Part, points: list[tuple[float, float]]) -> list:
    """The edges of body that run along the rail and pass through the given (x, z) points."""
    found = []
    for x, z in points:
        near = [
            e
            for e in body.edges().filter_by(Axis.Y)
            if abs(e.center().X - x) < 1e-3 and abs(e.center().Z - z) < 1e-3
        ]
        if len(near) != 1:
            raise ValueError(
                f"Expected one collar edge along the rail at x={x:.2f}, z={z:.2f}, found {len(near)}"
            )
        found.append(near[0])
    return found


def build_collar(
    p: CameraSupportParameters | None = None, station: float = 0.0, rod_side: int | None = None
) -> Part:
    """Split collar clamped on the lens barrel at a station, its clamp ear up.

    A thin ring with a flat platform at each screw, in which a pocket holds the bearing surface (a magnet, or
    on rod_side the pair of groove rods) with a rim round it. The ear takes the common M3 screw and nut, as
    the common rail shoe's clamp does. Inside corners are filleted against stress, outside ones for the
    fingers; the faces of the split stay sharp.
    """
    p = p or CameraSupportParameters()
    p.validate()
    r = p.rail_shoe
    zc = p.optical_height
    half_width = p.collar_width / 2
    ring_axis = Pos(0, station, zc) * Rot(X=90)
    body = ring_axis * centered_cylinder(2 * p.collar_radius, p.collar_width)
    ear_top = zc + p.collar_radius + p.ear_top_above_ring
    body += box_between(
        p.ear_screw_side,
        p.ear_nut_side,
        station - half_width,
        station + half_width,
        zc + p.collar_radius - 2,
        ear_top,
    )
    platform_depth = 4.0  # Into the ring wall; the bore is cut after.
    across_platform = (
        max(_pad_pocket(p, True)[0], _pad_pocket(p, False)[0]) / 2 + p.pad_wall_relief + p.pad_wall
    )
    for side in (-1, 1):
        body += screw_location(p, side, station) * box_between(
            -across_platform,
            across_platform,
            -half_width,
            half_width,
            -p.pad_wall_height,
            p.magnet_thickness + platform_depth,
        )
    if len(body.solids()) != 1:
        raise ValueError("Collar did not produce one solid")
    # Edges along the rail, picked by position: inside corners get the larger fillet, outside ones the
    # smaller; then the outline of the two ring ends. The faces of the split are cut afterwards.
    ring_r = p.collar_radius
    inside = [(x, zc + sqrt(ring_r**2 - x**2)) for x in (p.ear_screw_side, p.ear_nut_side)]
    outside = [(p.ear_screw_side, ear_top), (p.ear_nut_side, ear_top)]
    for side in (-1, 1):
        loc = screw_location(p, side, station)
        for sign in (-1, 1):
            xl = sign * across_platform
            root = p.pad_radius - sqrt(ring_r**2 - xl**2)  # Where the platform side meets the ring.
            for local, bucket in (((xl, root), inside), ((xl, -p.pad_wall_height), outside)):
                point = (loc * Pos(local[0], 0, local[1])).position
                bucket.append((point.X, point.Z))
    body = fillet(_edges_along_rail(body, inside), p.collar_root_fillet)
    body = fillet(_edges_along_rail(body, outside), p.collar_round_fillet)
    ends = body.faces().filter_by(Axis.Y)
    body = fillet([e for f in ends for e in f.edges()], p.collar_end_fillet)

    body -= ring_axis * centered_cylinder(p.collar_bore, p.collar_width + 2)
    body -= box_between(
        -r.split_gap / 2, r.split_gap / 2, station - half_width - 1, station + half_width + 1, zc, ear_top + 1
    )
    # Clamp screw through the screw ear, and the nut in a hex pocket in the other, flats up and down.
    screw_z = zc + p.collar_radius + p.clamp_screw_above_ring
    body -= x_cylinder(r.m3_clearance_diameter, station, screw_z, p.ear_screw_side - 1, p.ear_nut_side + 1)
    nut_across_corners = (r.clamp_nut_across_flats + r.nut_across_flats_clearance) / cos(radians(30))
    body -= extrude(
        along_x((p.ear_nut_side - r.nut_pocket_depth, station, screw_z))
        * RegularPolygon(nut_across_corners / 2, 6),
        amount=r.nut_pocket_depth + 1,
    )
    for side in (-1, 1):
        loc = screw_location(p, side, station)
        across, along_rail = _pad_pocket(p, side == rod_side)
        # The pad itself, to its floor; above the pad face the opening is cut back by the relief.
        body -= loc * box_between(
            -across / 2, across / 2, -along_rail / 2, along_rail / 2, 0, p.magnet_thickness
        )
        relief = p.pad_wall_relief
        body -= loc * box_between(
            -across / 2 - relief,
            across / 2 + relief,
            -along_rail / 2 - relief,
            along_rail / 2 + relief,
            -p.pad_wall_height - 1,
            0.001,
        )
    if len(body.solids()) != 1 or not body.is_valid:
        raise ValueError("Collar did not produce one valid solid")
    return body


def build_collar_for_print(p: CameraSupportParameters | None = None, aft: bool = False) -> Part:
    """A collar as printed: ring axis vertical, one end face on the bed, centered on the origin, bed at z = 0.

    The layers then lie in the plane of the clamp and pad loads. The aft collar carries the groove rods.
    """
    p = p or CameraSupportParameters()
    collar = Rot(X=90) * build_collar(p, 0.0, -1 if aft else None)
    box = collar.bounding_box()
    return Pos(-(box.min.X + box.max.X) / 2, -(box.min.Y + box.max.Y) / 2, -box.min.Z) * collar


def _arm_point(p: CameraSupportParameters, side: int, along: float, across: float) -> tuple[float, float]:
    """(x, z) of a point on a screw's axis plane: along its axis from the lens axis, across it (up-outboard)."""
    a = radians(p.screw_angle)
    return (
        side * (along * sin(a) + across * cos(a)),
        p.optical_height - along * cos(a) + across * sin(a),
    )


def _yoke_profile(p: CameraSupportParameters) -> Face:
    """Filleted yoke outline in the x-z plane: column, crossbar, and an inclined arm either side.

    Each arm is a slab of the boss thickness, square to its screw. Its lens-side face carries the insert and
    runs down to the crossbar top; its back face runs down to the crossbar underside, so there is no stub
    or step. Inside corners are filleted most generously.
    """
    a = radians(p.screw_angle)
    top = p.yoke_top
    bottom = top - p.yoke_crossbar
    column = p.rail_size / 2
    face_s = p.pad_radius + p.boss_top_below_tip  # Lens-side face of the arm, from the lens axis.
    back_s = face_s + p.yoke_boss_length + YOKE_BOSS_OVERRUN
    outer = p.yoke_boss_width / 2
    cross = lambda s, z: (z - p.optical_height + s * cos(a)) / sin(a)  # t on the face/back line at height z.
    face_foot = _arm_point(p, 1, face_s, cross(face_s, top))  # Lens-side face meets the crossbar top.
    back_foot = _arm_point(p, 1, back_s, cross(back_s, bottom))  # Back face meets the crossbar underside.
    right = [
        ((column, p.deck_top), 0.0),
        ((column, bottom), p.yoke_root_fillet),
        (back_foot, p.yoke_blend_fillet),
        (_arm_point(p, 1, back_s, outer), p.yoke_corner_fillet),
        (_arm_point(p, 1, face_s, outer), p.yoke_corner_fillet),
        (face_foot, p.yoke_blend_fillet),
    ]
    if not column + p.yoke_root_fillet < back_foot[0] - p.yoke_blend_fillet:
        raise ValueError("The crossbar underside is too short for its fillets")
    if not 0 < face_foot[0] < back_foot[0]:
        raise ValueError("The arm face must meet the crossbar top inboard of its back")
    ring = right + [((-x, z), r) for (x, z), r in reversed(right)]
    wire = Wire.make_polygon([Vector(x, 0, z) for (x, z), _ in ring], close=True)
    face = Face(wire)
    for (x, z), radius in ring:
        if radius:
            nearest = min(face.vertices(), key=lambda v: hypot(v.X - x, v.Z - z))
            face = face.fillet_2d(radius, [nearest])
    return face


def _yoke(p: CameraSupportParameters, station: float) -> Part:
    """One printed yoke: column with an insert hole in its foot, crossbar, and two inclined arms.

    Printed on its side, so every layer lies in the plane of the loads. The column's flat underside sits on
    the shoe deck, between the deck's two locating walls. Each arm carries a heat-set insert from its
    lens-side face, with the bore open through the back for the screw and its hex key.
    """
    face = _yoke_profile(p)
    yoke = Part(Solid.extrude(face, Vector(0, p.yoke_thickness, 0)).wrapped)
    yoke = Pos(0, station - p.yoke_thickness / 2, 0) * yoke
    # The peg for the retaining band: a stem with a lip, on the centre of the crossbar face toward the other
    # collar, pointing along the lens.
    hx, hy, hz = p.horn_base(station)
    plane = Plane(origin=(hx, hy, hz), z_dir=(0, p.toward_other(station), 0))
    yoke += plane * z_cylinder(p.horn_diameter, 0, 0, -1, p.horn_stem_length)
    lip_start = p.horn_stem_length
    yoke += plane * z_cylinder(p.horn_lip_diameter, 0, 0, lip_start, lip_start + p.horn_lip_height)
    counterbore = MCMASTER_94459A797_FLANGE_DIAMETER + 0.2
    hole = p.insert_hole_diameter
    yoke -= z_cylinder(hole, 0, station, p.joint_z - 1, p.joint_z + p.insert_hole_depth)
    yoke -= z_cylinder(counterbore, 0, station, p.joint_z - 1, p.joint_z + p.insert_flange_thickness)
    # Arm insert: from the lens-side face, along the screw, flange recessed flush; the screw passes on out.
    face_z = -p.boss_top_below_tip
    back_z = face_z - p.yoke_boss_length - YOKE_BOSS_OVERRUN
    for side in (-1, 1):
        loc = screw_location(p, side, station)
        yoke -= loc * z_cylinder(hole, 0, 0, face_z - p.insert_hole_depth, face_z + 1)
        yoke -= loc * z_cylinder(counterbore, 0, 0, face_z - p.insert_flange_thickness, face_z + 1)
        bore = p.rail_shoe.m5_clearance_diameter
        yoke -= loc * z_cylinder(bore, 0, 0, back_z - 1, face_z + 1 - p.insert_hole_depth)
    return yoke


def _straddle(
    p: CameraSupportParameters,
    y0: float,
    y1: float,
    clamp_ys: tuple[float, ...],
    yoke_stations: tuple[float, ...] = (),
    square_sides: tuple[int, ...] = (),
) -> Part:
    """Saddle straddling the rail from y0 to y1, as the common rail shoe's lower section (§5.3).

    Same rail opening, side walls, skirt depth, deck thickness, and rounded outside corners; an M5 clearance
    hole crosses the skirts at each clamp_ys station, at rail mid-height, for the side-slot screws. At each
    yoke station the deck carries two locating walls across the rail, with a countersunk M5 hole between
    them, the head flush with the underside.
    """
    r = p.rail_shoe
    shoe = Pos(-p.shoe_outer, y0, -r.skirt_depth) * Box(
        2 * p.shoe_outer, y1 - y0, r.skirt_depth + r.bridge_top, align=Align.MIN
    )
    corners = [
        e for e in shoe.edges().filter_by(Axis.Z) if (1 if e.center().X > 0 else -1) not in square_sides
    ]
    shoe = fillet(corners, r.outside_corner_radius)
    shoe -= box_between(-r.rail_opening / 2, r.rail_opening / 2, y0 - 1, y1 + 1, -r.skirt_depth - 1, 0)
    feet = [f for f in shoe.faces() if abs(f.center().Z + r.skirt_depth) < 1e-6 and f.normal_at().Z < -0.99]
    shoe = chamfer([e for f in feet for e in f.edges()], p.skirt_foot_chamfer)
    for y in clamp_ys:
        shoe -= x_cylinder(
            r.m5_clearance_diameter, y, -r.rail_height / 2, -p.shoe_outer - 1, p.shoe_outer + 1
        )
    head_depth = (p.joint_screw_head_diameter - r.m5_clearance_diameter) / 2
    wall_offset = p.yoke_thickness / 2 + p.locating_clearance_per_side + p.locating_wall_thickness / 2
    for station in yoke_stations:
        for side in (-1, 1):
            y = station + side * wall_offset
            half = p.locating_wall_thickness / 2
            shoe += box_between(
                -p.rail_size / 2,
                p.rail_size / 2,
                y - half,
                y + half,
                p.deck_top - 1,
                p.deck_top + p.locating_wall_height,
            )
        shoe -= z_cylinder(r.m5_clearance_diameter, 0, station, -1, p.deck_top + 1)
        shoe -= z_cone(p.joint_screw_head_diameter, r.m5_clearance_diameter, 0, station, 0, head_depth)
    return shoe


def build_cradle_shoe(p: CameraSupportParameters | None = None) -> Part:
    """Lens-cradle saddle, printed deck-down, symmetric about the middle of the two stations."""
    p = p or CameraSupportParameters()
    p.validate()
    aft, fore = p.stations
    half_collar = p.collar_width / 2
    return _straddle(
        p,
        aft - half_collar - p.cradle_end_margin,
        fore + half_collar + p.cradle_end_margin,
        p.cradle_clamp_ys,
        p.stations,
    )


def build_cradle_shoe_for_print(p: CameraSupportParameters | None = None) -> Part:
    """The cradle shoe as printed, skirts on the bed and deck up, centered on the origin, bed at z = 0."""
    shoe = build_cradle_shoe(p)
    box = shoe.bounding_box()
    return Pos(-(box.min.X + box.max.X) / 2, -(box.min.Y + box.max.Y) / 2, -box.min.Z) * shoe


def build_cradle_yoke(p: CameraSupportParameters | None = None, station: float = 0.0) -> Part:
    """Yoke for the collar at a station, printed on its side and bolted to the cradle shoe."""
    p = p or CameraSupportParameters()
    p.validate()
    return _yoke(p, station)


def build_cradle_yoke_for_print(p: CameraSupportParameters | None = None) -> Part:
    """A yoke laid on its side as printed: profile plane on the bed, centered on the origin, bed at z = 0."""
    yoke = Rot(X=90) * build_cradle_yoke(p)
    box = yoke.bounding_box()
    return Pos(-(box.min.X + box.max.X) / 2, -(box.min.Y + box.max.Y) / 2, -box.min.Z) * yoke


def _joint_hardware(p: CameraSupportParameters, where: str, station: float) -> list[Part]:
    """Insert and countersunk M5 screw of a yoke's joint."""
    head_depth = (p.joint_screw_head_diameter - 5.0) / 2
    head = z_cone(p.joint_screw_head_diameter, 5.0, 0, 0, 0, head_depth)
    shank = z_cylinder(5.0, 0, 0, head_depth, p.joint_screw_length)
    screw = head + shank
    insert_at = Pos(0, station, p.joint_z) * Rot(X=180)
    return [
        labeled(mcmaster_94459a797(), f"{where} yoke insert", BRASS, insert_at),
        labeled(screw, f"{where} yoke screw", STEEL, Pos(0, station, 0)),
    ]


def build_phone_rest(p: CameraSupportParameters | None = None) -> Part:
    """Phone-specific printed shoe with the arm that carries the rest rod, printed on its side.

    The whole part is one profile in the plane of the loads, extruded along the rail, so each layer is that
    profile and the arm, as long as the shoe, grows from the bed with no bridge or overhang; only the side-slot
    screw bores are horizontal. The arm's inside corners are filleted against stress, the root largest, its
    outside corners rounded, and the rod lies in a half-round seat in its top.
    """
    p = p or CameraSupportParameters()
    p.validate()
    y0, y1 = p.rest_center - p.rest_shoe_length / 2, p.rest_center + p.rest_shoe_length / 2
    outer = p.shoe_outer
    top = p.rest_arm_top
    bottom = top - p.rest_arm_depth
    tip = p.rest_x + p.rest_arm_overhang
    rest = _straddle(p, y0, y1, (p.rest_center,), square_sides=(1,))
    rest += box_between(outer, tip, y0, y1, bottom, top)
    seat_r = p.rest_rod_diameter / 2 + p.rest_seat_clearance_per_side
    seat = y_cylinder(2 * seat_r, p.rest_x, top, y0 - 1, y1 + 1)
    rest -= seat
    rest = fillet(_edges_along_rail(rest, [(outer, bottom)]), p.rest_root_fillet)
    rest = fillet(_edges_along_rail(rest, [(outer, p.deck_top)]), p.rest_step_fillet)
    rounded = [(outer, top), (tip, top), (tip, bottom)]
    rest = fillet(_edges_along_rail(rest, rounded), p.rest_edge_fillet)
    lips = [(p.rest_x + sign * seat_r, top) for sign in (-1, 1)]
    rest = fillet(_edges_along_rail(rest, lips), p.rest_seat_lip_fillet)
    if len(rest.solids()) != 1 or not rest.is_valid:
        raise ValueError("Phone rest did not produce one valid solid")
    return rest


def build_phone_rest_for_print(p: CameraSupportParameters | None = None) -> Part:
    """The phone rest laid on its side as printed: profile plane on the bed, centered on the origin, bed at z = 0."""
    rest = Rot(X=90) * build_phone_rest(p)
    box = rest.bounding_box()
    return Pos(-(box.min.X + box.max.X) / 2, -(box.min.Y + box.max.Y) / 2, -box.min.Z) * rest


def cutoff_post_station(p: CameraSupportParameters, c) -> float:
    """Cutoff post axis along the rail, from the back of the phone (y=0): the lens front, the assumed gap to
    the slip ring's rear face, and half the ring."""
    return p.lens_length + LENS_TO_SLIP_RING + c.ring_thickness / 2


def build_camera_support_assembly(
    p: CameraSupportParameters | None = None, include_cutoff: bool = True
) -> Compound:
    """The mock-up on the imaging rail, with phone and lens envelopes and, optionally, the cutoff station."""
    p = p or CameraSupportParameters()
    p.validate()
    axis_z = p.optical_height
    x0 = -p.camera_inset_from_end
    phone = box_between(
        x0, x0 + p.phone_length, -p.phone_thickness, 0, p.phone_bottom, p.phone_bottom + p.phone_width
    )
    lens = y_cylinder(p.lens_diameter, 0, axis_z, 0, p.lens_length)
    focus_ring_end = p.focus_ring_start + p.focus_ring_length
    ring = y_cylinder(p.focus_ring_diameter, 0, axis_z, p.focus_ring_start, focus_ring_end)
    rail_length = 300.0
    rail = Pos(0, p.lens_length + 80 - rail_length / 2, 0) * build_rail(rail_length)
    axis = y_cylinder(0.8, 0, axis_z, -60, p.lens_length + 90)
    children = [
        labeled(rail, "Rail", BLACK_ANODIZED),
        labeled(build_cradle_shoe(p), "Cradle shoe", PRINTED_ORANGE),
        labeled(build_phone_rest(p), "Phone rest", PRINTED_BLUE),
        labeled(phone, "Phone envelope", PHONE_BODY),
        labeled(lens, "Telephoto envelope", LENS_BLACK),
        labeled(ring, "Focus ring", FOCUS_RING_GRAY),
        labeled(axis, "Optical axis", AXIS_RED),
    ]
    # Pads lie with their 10 mm length across the rail: each pad slides that way by the travel of the other
    # screw of its pair, and only slightly along the rail.
    pad = floor_box(p.magnet_length, p.magnet_width, p.magnet_thickness)
    for where, station in zip(("Aft", "Fore"), p.stations):
        rod_side = -1 if where == "Aft" else None  # The aft left pad carries the groove rods.
        children.append(labeled(build_collar(p, station, rod_side), f"{where} collar", PRINTED_GREEN))
        children.append(labeled(build_cradle_yoke(p, station), f"{where} yoke", PRINTED_ORANGE))
        children.append(labeled(build_band(p, station), f"{where} band", BAND_RED))
        children += _joint_hardware(p, where, station)
        for name, side in (("left", -1), ("right", 1)):
            loc = screw_location(p, side, station)
            children += _adjuster(p, f"{where} {name}", loc)
            if (where, side) == ("Aft", -1):
                continue  # This screw sits in the rod groove below, not on a magnet.
            children.append(labeled(pad, f"{where} {name} magnet", STEEL, loc))
    # Fore/aft stop: in place of a magnet, the aft left collar pad carries two rods lying across the rail, and
    # the screw's ball nests in the groove between them. The ball can still slide along the rods.
    groove = screw_location(p, -1, p.aft_station)
    half_spacing, rod_height = rod_layout(p)
    for offset in (-1, 1):
        rod = Rot(Y=90) * mcmaster_91585a351()  # Axis along x (across the rail), as the Ø3 × 10 mm dowel pin.
        loc = groove * Pos(0, offset * half_spacing, rod_height)
        children.append(labeled(rod, f"Groove rod {offset:+d}", STEEL, loc))
    # Roll: the phone's lower edge on a rod lying along the rail.
    rest = along_y((p.rest_x, p.rest_y, p.rest_arm_top)) * mcmaster_91585a457()
    children.append(labeled(rest, "Rest rod", STEEL))
    support = assembly("Lens cradle and phone rest (concept mock-up)", children)
    if not include_cutoff:
        return support
    from schlieren.parts.carriage import CarriageParameters, build_carriage, support_location

    c = CarriageParameters()
    post_y = cutoff_post_station(p, c)
    carriage = build_carriage(c, include_support=True, include_hardware=True)
    on_rail = Pos(0, post_y, 0) * support_location(c).inverse()
    return assembly("Imaging rail (concept mock-up)", [support, place(on_rail, carriage)])

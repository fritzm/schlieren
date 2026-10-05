"""Lens pointer and phone rest: mock-up of the provisional baseline concept, design §§9.4-9.7.

The phone and the lens threaded onto its case are one rigid body, held by the lens barrel with the phone
hanging from it. Two separate rail fixtures:

- the lens pointer, specific to the lens. Two split collars clamp the barrel, the aft one on its rear
  cylindrical section and the fore one at the front of the long section, just behind the focus ring. Each
  collar rests on a pair of ball-tip screws at ±45° in a yoke; each pair sets x and z of the lens axis at its
  station, so together they set position, pitch, and yaw. Both yokes are one printed shoe straddling the rail.
  Three screw tips bear on magnet pads; the aft left one sits between two short rods on its collar pad, which
  fixes the lens fore/aft;
- the phone rest, specific to the phone. The phone is carried by its lens mount and is not gripped, but it
  hangs well to one side of the lens axis, so its weight would turn the lens in its collars. Its lower edge
  rests on one piece of rod stock lying along the rail, on the arm of a small shoe of its own. The rest is
  fixed: roll changes slightly as the aft collar is raised or lowered, which does not matter. A different
  phone needs only this part redesigned.

The concept is the baseline; this model of it is a visualization envelope, not a detailed design: plain blocks,
no fits, pockets, hold-downs, or printability worked out. The phone dimensions are the §9.1 measurements and
Apple's drawing, and the lens section lengths and barrel diameter are measured (§9.2); the cased phone
thickness and the focus-ring diameter are assumed, and the lens aft end is taken to be at the phone's back.
The screws, thumb nuts, and inserts are the vendor models.

Coordinates: the §3.4 imaging rail frame, +x right, +y along the rail toward the mirror, z up from the rail
top. y=0 is the back of the cased phone.
"""

from dataclasses import dataclass
from math import cos, radians, sin, sqrt

from build123d import Align, Box, Compound, Cylinder, Location, Part, Pos, Rot

from schlieren.cad import BLACK_ANODIZED, ON_FLOOR, along_y, assembly, labeled, place
from schlieren.parts.rail import build_rail
from schlieren.vendor_cad import (
    MCMASTER_92815A202_HEIGHT,
    MCMASTER_93339A252_BALL_DIAMETER,
    MCMASTER_93339A252_LENGTH,
    MCMASTER_94459A797_LENGTH,
    mcmaster_92815a202,
    mcmaster_93339a252,
    mcmaster_94459a797,
)

INCH = 25.4
POINTER_COLOR = (0.8, 0.4, 0.25)
REST_COLOR = (0.35, 0.6, 0.8)
COLLAR_COLOR = (0.4, 0.75, 0.5)
STEEL = (0.6, 0.6, 0.62)
BRASS = (0.8, 0.65, 0.25)
BLACK_OXIDE = (0.13, 0.13, 0.14)
PHONE_COLOR = (0.25, 0.27, 0.32)
LENS_COLOR = (0.12, 0.12, 0.13)
FOCUS_RING_COLOR = (0.3, 0.3, 0.33)
AXIS_COLOR = (0.9, 0.1, 0.1)


@dataclass(frozen=True)
class CameraSupportParameters:
    optical_height: float = 72.35  # §3.4.
    rail_size: float = 20.0

    # Phone in its case, landscape, screen aft (§9.1), Main camera (the lower aperture in portrait) on the axis.
    # Bare-phone dimensions are from Apple's drawing, docs/reference/Apple-iPhone-17.pdf.
    camera_height_above_edge: float = 60.6  # Measured in the case, §9.1.
    camera_inset_from_end: float = 34.3  # Measured in the case, §9.1: Main camera from the near short edge.
    bare_phone_length: float = 149.61
    bare_phone_width: float = 71.45
    bare_camera_from_side_edge: float = 13.62  # Both rear cameras, from the nearer long edge.
    phone_thickness: float = 11.0  # Assumed case envelope; the bare phone is 7.95 mm.

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

    # Lens pointer.
    aft_station: float = (
        24.0  # Aft collar center from the lens aft end; leaves finger room ahead of the phone.
    )
    fore_station: float = 96.5  # Fore collar center: its front face 2 mm behind the focus ring.
    collar_width: float = 12.0
    collar_wall: float = 6.0
    yoke_boss_length: float = (
        10.0  # Along each screw: holds the insert, and leaves the thumb nut 5 mm of travel.
    )
    yoke_boss_width: float = 16.0
    yoke_clearance_below_collar: float = 12.0  # Crossbar top below the collar, clear of the thumb nuts.
    yoke_crossbar: float = 10.0
    shoe_cheek: float = 6.0
    shoe_deck: float = 5.0
    pointer_front_margin: float = 9.0  # Pointer shoe beyond the fore yoke, along the rail.
    pointer_rear_margin: float = 4.0  # And behind the aft yoke, short of the phone rest.

    # Phone rest.
    rest_x: float = 100.0  # Rest rod under the phone's lower edge, outboard of the axis.
    rest_rod_diameter: float = 4.0
    rest_rod_length: float = 20.0
    rest_arm_width: float = 14.0  # Along the rail.
    rest_arm_depth: float = 14.0
    rest_shoe_length: float = 22.0  # Along the rail.
    rest_shoe_aft_of_rest: float = 3.0  # Shoe center aft of the rest, to stand clear of the pointer.

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
    def collar_radius(self) -> float:
        return self.lens_diameter / 2 + self.collar_wall

    @property
    def pad_radius(self) -> float:
        """Lens axis to each screw tip, on the outer face of its pad."""
        return self.collar_radius + 1.0

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
        if self.yoke_boss_length < MCMASTER_94459A797_LENGTH:
            raise ValueError("Each yoke boss must contain its heat-set insert")
        if self.boss_top_below_tip < self.nut_below_tip + MCMASTER_92815A202_HEIGHT:
            raise ValueError("Each thumb nut must fit between its collar pad and its yoke boss")


def _box(x0, x1, y0, y1, z0, z1) -> Part:
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=Align.MIN)


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


def build_collar(p: CameraSupportParameters | None = None, station: float = 0.0) -> Part:
    """Split collar clamped on the lens barrel at a station, with its clamp ear up."""
    p = p or CameraSupportParameters()
    ring = Cylinder(p.collar_radius, p.collar_width) - Cylinder(p.lens_diameter / 2, p.collar_width + 2)
    ring += _box(-6, 6, p.collar_radius - 2, p.collar_radius + 9, -p.collar_width / 2, p.collar_width / 2)
    ring -= _box(-0.75, 0.75, p.lens_diameter / 2 - 1, p.collar_radius + 10, -p.collar_width, p.collar_width)
    # Built about +z with the clamp ear toward +y; turned so the axis is rail y and the ear points up.
    return Pos(0, station, p.optical_height) * Rot(X=90) * ring


def _yoke(p: CameraSupportParameters, station: float) -> Part:
    """Column, crossbar, and two inclined bosses for one pair of screws, standing on the rail top."""
    y0, y1 = station - p.collar_width / 2, station + p.collar_width / 2
    half_boss = p.yoke_boss_width / 2
    boss = _box(-half_boss, half_boss, y0 - station, y1 - station, -p.yoke_boss_length - 0.5, 0)
    reach = p.pad_radius + p.screw_length
    half_span = reach * sin(radians(p.screw_angle)) + 2
    top = p.optical_height - p.collar_radius - p.yoke_clearance_below_collar
    yoke = _box(-half_span, half_span, y0, y1, top - p.yoke_crossbar, top)
    yoke += _box(-p.rail_size / 2, p.rail_size / 2, y0, y1, 0, top)
    for side in (-1, 1):
        yoke += screw_location(p, side, station) * Pos(0, 0, -p.boss_top_below_tip) * boss
    return yoke


def _straddle(p: CameraSupportParameters, y0: float, y1: float) -> Part:
    """Shoe body straddling the rail from y0 to y1."""
    half = p.rail_size / 2
    outer = half + p.shoe_cheek
    shoe = _box(-outer, outer, y0, y1, -p.rail_size, p.shoe_deck)
    return shoe - _box(-half, half, y0 - 1, y1 + 1, -p.rail_size - 1, 0)


def build_lens_pointer(p: CameraSupportParameters | None = None) -> Part:
    """Lens-specific printed shoe carrying both yokes."""
    p = p or CameraSupportParameters()
    p.validate()
    aft, fore = p.stations
    half_collar = p.collar_width / 2
    pointer = _straddle(
        p, aft - half_collar - p.pointer_rear_margin, fore + half_collar + p.pointer_front_margin
    )
    for station in p.stations:
        pointer += _yoke(p, station)
    return pointer


def build_phone_rest(p: CameraSupportParameters | None = None) -> Part:
    """Phone-specific printed shoe with the arm that carries the rest rod."""
    p = p or CameraSupportParameters()
    center = p.rest_y - p.rest_shoe_aft_of_rest
    rest = _straddle(p, center - p.rest_shoe_length / 2, center + p.rest_shoe_length / 2)
    outer = p.rail_size / 2 + p.shoe_cheek
    arm_y0, arm_y1 = p.rest_y - p.rest_arm_width / 2, p.rest_y + p.rest_arm_width / 2
    rest += _box(outer, p.rest_x + 8, arm_y0, arm_y1, p.rest_arm_top - p.rest_arm_depth, p.rest_arm_top)
    return rest


def build_camera_support_assembly(
    p: CameraSupportParameters | None = None, include_cutoff: bool = True
) -> Compound:
    """The mock-up on the imaging rail, with phone and lens envelopes and, optionally, the cutoff station."""
    p = p or CameraSupportParameters()
    p.validate()
    axis_z = p.optical_height
    x0 = -p.camera_inset_from_end
    phone = _box(
        x0, x0 + p.phone_length, -p.phone_thickness, 0, p.phone_bottom, p.phone_bottom + p.phone_width
    )
    lens = along_y((0, 0, axis_z)) * Cylinder(p.lens_diameter / 2, p.lens_length, align=ON_FLOOR)
    ring = along_y((0, p.focus_ring_start, axis_z)) * Cylinder(
        p.focus_ring_diameter / 2, p.focus_ring_length, align=ON_FLOOR
    )
    rail_length = 300.0
    rail = Pos(0, p.lens_length + 80 - rail_length / 2, 0) * build_rail(rail_length)
    axis = along_y((0, -60, axis_z)) * Cylinder(0.4, p.lens_length + 150, align=ON_FLOOR)
    children = [
        labeled(rail, "Rail", BLACK_ANODIZED),
        labeled(build_lens_pointer(p), "Lens pointer", POINTER_COLOR),
        labeled(build_phone_rest(p), "Phone rest", REST_COLOR),
        labeled(phone, "Phone envelope", PHONE_COLOR),
        labeled(lens, "Telephoto envelope", LENS_COLOR),
        labeled(ring, "Focus ring", FOCUS_RING_COLOR),
        labeled(axis, "Optical axis", AXIS_COLOR),
    ]
    # Pads lie with their 10 mm length across the rail: each pad slides that way by the travel of the other
    # screw of its pair, and only slightly along the rail.
    pad = Box(p.magnet_length, p.magnet_width, p.magnet_thickness, align=ON_FLOOR)
    for where, station in zip(("Aft", "Fore"), p.stations):
        children.append(labeled(build_collar(p, station), f"{where} collar", COLLAR_COLOR))
        for name, side in (("left", -1), ("right", 1)):
            loc = screw_location(p, side, station)
            children += _adjuster(p, f"{where} {name}", loc)
            if (where, side) == ("Aft", -1):
                continue  # This screw sits in the rod groove below, not on a magnet.
            children.append(labeled(pad, f"{where} {name} magnet", STEEL, loc))
    # Fore/aft stop: in place of a magnet, the aft left collar pad carries two rods lying across the rail, and
    # the screw's ball nests in the groove between them. The ball can still slide along the rods.
    groove = screw_location(p, -1, p.aft_station)
    ball_radius = p.ball_diameter / 2
    rod_radius = p.groove_rod_diameter / 2
    half_spacing = p.groove_rod_diameter * 0.75
    nest = sqrt((ball_radius + rod_radius) ** 2 - half_spacing**2)  # Rod centers above the ball center.
    for offset in (-1, 1):
        rod = Rot(Y=90) * Cylinder(rod_radius, p.groove_rod_length)
        loc = groove * Pos(0, offset * half_spacing, nest - ball_radius)
        children.append(labeled(rod, f"Groove rod {offset:+d}", STEEL, loc))
    # Roll: the phone's lower edge on a rod lying along the rail.
    rest = along_y((p.rest_x, p.rest_y - p.rest_rod_length / 2, p.rest_arm_top)) * Cylinder(
        p.rest_rod_diameter / 2, p.rest_rod_length, align=ON_FLOOR
    )
    children.append(labeled(rest, "Rest rod", STEEL))
    # Clamp screws into the rail side slots: two pairs on the pointer, one pair on the phone rest.
    head = Cylinder(4.25, 5.0, align=ON_FLOOR)
    outer = p.rail_size / 2 + p.shoe_cheek
    aft, fore = p.stations
    middle = (aft + fore) / 2
    rest_center = p.rest_y - p.rest_shoe_aft_of_rest
    for name, y in (
        ("Pointer clamp screw 1", middle - 18),
        ("Pointer clamp screw 2", middle + 18),
        ("Rest clamp screw", rest_center),
    ):
        for side, turn in ((-1, -90), (1, 90)):
            loc = Pos(side * outer, y, -p.rail_size / 2) * Rot(Y=turn)
            children.append(labeled(head, f"{name} {side:+d}", STEEL, loc))

    support = assembly("Lens pointer and phone rest (concept mock-up)", children)
    if not include_cutoff:
        return support
    from schlieren.parts.carriage import CarriageParameters, build_carriage, support_location

    c = CarriageParameters()
    lens_to_ring = 10.0  # Assumed gap, lens front to the slip ring's rear face (§8.1).
    post_y = p.lens_length + lens_to_ring + c.ring_thickness / 2
    carriage = build_carriage(c, include_support=True, include_hardware=True)
    on_rail = Pos(0, post_y, 0) * support_location(c).inverse()
    return assembly("Imaging rail (concept mock-up)", [support, place(on_rail, carriage)])

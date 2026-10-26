"""Drilling fixture for the LED module's SM1CP2M cap and CN40-40B heatsink; canonical design §6.8.

One printed bushing plate carries the §6.4 hole layout in press-fit steel drill bushings. Two printed nests hold
the part under it: the cap nest holds the cap by its flange, and the heatsink nest holds the heatsink by the
channels between its pins. The plate seats on the top of either nest, so one plate drills both parts and their
M3 and lead holes agree by construction.

Fixture frame (mm): z up, the part axis on the z axis, z=0 at the surface the part stands on (the cap's flange
back face on the nest's support ring, the heatsink's pin tips on the nest floor). The plate is modeled with its
seat face on z=0 and the bushings rising from it; `build_fixture_assembly` places it on a nest. Looking down
from +z, +x is to the right and +y up, the layout's plan view from the LED side. Both parts are drilled from
their LED-side faces: the cap's thread-boss face, and the heatsink's flat base face (pins down).

The vendor cap, heatsink, bushing, insert, screw, and mounting-hardware models appear only in the viewer assembly; the printed parts do not
depend on them, except through the bushing catalog dimensions.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cache
from math import cos, hypot, radians, sin

from build123d import Compound, Plane, Polygon, Pos, Rot, extrude, fillet

from schlieren.cad import (
    CUT_OVERRUN,
    assembly,
    box_between,
    fused,
    intersect,
    labeled,
    moved,
    place,
    y_cylinder,
    z_cylinder,
)
from schlieren.palette import (
    BLACK_ANODIZED,
    BUSHING_BRASS,
    METAL,
    PRINTED_BLUE,
    PRINTED_ORANGE,
    RUBBER,
    STEEL,
)
from schlieren.parts.light_source import LightSourceParameters
from schlieren.parts.light_source_holes import Hole, HoleLayoutParameters
from schlieren.standards import INCH
from schlieren.validation import require_positive_dimensions
from schlieren.vendor_cad import (
    MCMASTER_969_LENGTH,
    MCMASTER_92356A589_DIAMETER,
    MCMASTER_92356A589_LENGTH,
    MCMASTER_92356A589_NECK_LENGTH,
    MCMASTER_92356A589_NECK_WIDTH,
    MCMASTER_95150A180_HEAD_DIAMETER,
    MCMASTER_95150A180_HEIGHT,
    MCMASTER_96659A134_DIAMETER,
    MCMASTER_96659A134_THICKNESS,
    MCMASTER_96990A132_BORE,
    MCMASTER_96990A132_DIAMETER,
    MCMASTER_96990A139_BORE,
    MCMASTER_96990A139_DIAMETER,
    MCMASTER_96990A147_BORE,
    MCMASTER_96990A147_DIAMETER,
    alpha_cn40_40b,
    mcmaster_91292a114,
    mcmaster_92356a589,
    mcmaster_95150a180,
    mcmaster_96659a134,
    mcmaster_96990a132,
    mcmaster_96990a139,
    mcmaster_96990a147,
    mcmaster_97171a310,
    thorlabs_sm1cp2m,
)

EPSILON = 1e-6  # mm, for picking edges by position.

CAP = "cap"
HEATSINK = "heatsink"
NEST_KINDS = (CAP, HEATSINK)

# Hole kinds the heatsink is drilled through: its M2 positions are not drilled.
HEATSINK_KINDS = ("m3", "lead")

NEST_LABEL = "Nest"
PLATE_LABEL = "Bushing plate"
BUSHING_LABEL = "Drill bushing"  # Numbered in the order of the layout's holes.
CAP_LABEL = "SM1CP2M cap"
HEATSINK_LABEL = "CN40-40B heatsink"
EAR_BOLT_LABEL = "Carriage bolt"  # Numbered 1-2, in the order of EAR_ANGLES; likewise the washers and nuts.
EAR_WASHER_LABEL = "Ear washer"
EAR_NUT_LABEL = "Thumb nut"
INSERT_LABEL = "M3 insert"  # Numbered 1-4 at the nest corners, 5 the cap nest's clamp insert.
PLATE_SCREW_LABEL = "Plate screw"  # Numbered 1-4 with the corner inserts.
CLAMP_SCREW_LABEL = "Clamp screw"
PAD_LABEL = "Hold-down pad"  # The EPDM disc, shown compressed against the part face.

# The ears' directions, degrees from +x: on the ±x faces. The nest sits turned 45° on the drill-press base, so
# that this axis lies along one diagonal pair of base slots.
EAR_ANGLES = (0.0, 180.0)
NUT_SWEEP_SAMPLES = 49  # Bolt positions along the ear slot checked for thumb-nut clearance.

# Bore diameters of the bore coupon, per bushing outside diameter: the diametral oversizes tried. Small printed
# holes come out smaller than drawn, so a bore drawn at the bushing's outside diameter is likely too tight.
COUPON_OVERSIZES = (0.0, 0.05, 0.10, 0.15, 0.20)
COUPON_PITCH = 10.0
COUPON_MARGIN = 5.0


@dataclass(frozen=True)
class Bushing:
    """A McMaster metric press-fit drill bushing (headless, hardened steel); catalog dimensions."""

    sku: str
    bore: float
    outer_diameter: float
    length: float
    model: Callable[[], Compound]  # The vendor STEP model: z from 0 to length, chamfered end up.


# One size per hole kind; each bore is the drill that makes the hole in the cap (§6.4).
BUSHINGS = {
    "m2": Bushing(
        "96990A132",
        MCMASTER_96990A132_BORE,
        MCMASTER_96990A132_DIAMETER,
        MCMASTER_969_LENGTH,
        mcmaster_96990a132,
    ),
    "m3": Bushing(
        "96990A147",
        MCMASTER_96990A147_BORE,
        MCMASTER_96990A147_DIAMETER,
        MCMASTER_969_LENGTH,
        mcmaster_96990a147,
    ),
    "lead": Bushing(
        "96990A139",
        MCMASTER_96990A139_BORE,
        MCMASTER_96990A139_DIAMETER,
        MCMASTER_969_LENGTH,
        mcmaster_96990a139,
    ),
}


@dataclass(frozen=True)
class DrillFixtureParameters:
    layout: HoleLayoutParameters = field(default_factory=HoleLayoutParameters)
    light: LightSourceParameters = field(default_factory=LightSourceParameters)
    # Body: the plate and both nests share one square outline and four corner screws (M3 × 12, into heat-set inserts in the nests).
    body_side: float = 54.0
    screw_offset: float = 22.0  # Corner screw axes at (±, ±) this far from the part axis.
    # McMaster 97171A310 M3 × 0.5 brass flanged heat-set inserts in the nest's screw holes: 5.7 mm installed
    # length under a Ø5.5 × 0.53 mm flange, for a hole up to Ø4 mm; the flange sits recessed, flush.
    insert_hole_diameter: float = 4.0
    insert_hole_depth: float = 6.2  # Below the flange recess: the installed length and room for melt.
    insert_flange_recess_diameter: float = 5.7
    insert_flange_recess_depth: float = 0.6
    plate_thickness: float = 6.0  # Equal to the bushing length: the bushings sit flush on both faces.
    # Plate-to-part standoff: bushing end to the part face, chip room for the bits.
    standoff: float = 2.0
    # Registration ring under the plate, in the nest's plate bore; a key tab on its +x side.
    plate_bore_diameter: float = 45.2
    ring_inner_diameter: float = 41.0  # Clears the Ø40.0 heatsink base.
    ring_height: float = 2.5
    ring_relief: float = 0.5  # Axial gap under the ring in the cap nest's counterbore.
    key_width: float = 6.0
    key_projection: float = 1.5  # Tab beyond the ring's outer surface.
    key_relief: float = 0.3  # Radial room at the slot's outer end.
    # Fabrication allowances.
    slip_clearance_diametral: float = 0.20  # Ring in bore, cap in pocket.
    key_clearance_width: float = 0.20  # Slot over tab.
    # **Provisional**: printed bores are designed at the bushing's outside diameter; calibrate with the coupon.
    bushing_bore_oversize: float = 0.0
    # Cap nest.
    floor_thickness: float = 3.0
    clamp_notch_depth: float = 4.0  # Into the -y face, thinning the wall for the clamp screw.
    clamp_notch_width: float = 14.0
    clamp_notch_top: float = 4.0  # Below the plate counterbore floor.
    relief_window_diameter: float = 25.0  # Through the floor, under the hole pattern: exits and chips.
    # Heatsink nest: a cross-shaped rib standing in the channels between pins, and viewing windows.
    rib_height: float = 8.0
    rib_half_length: float = 19.0
    rib_clearance_width: float = 0.30  # Channel width minus rib width.
    window_width: float = 24.0
    window_floor_lip: float = 1.0
    window_flat_top: float = (
        4.0  # Width of the window's flat top; 45° chamfers to the sides print unsupported.
    )
    window_top_margin: float = 3.0  # Solid above the windows, below the counterbore zone.
    # Minimum plate web between neighboring bushings.
    min_web: float = 1.5
    # Hold-down pad: a boss under the plate's center carries a disc of the 1/32" adhesive-backed EPDM sheet
    # (McMaster 9852N37, in CAS-002) that presses on the part's face, holding the cap on its support ring and
    # the heatsink on its pins.
    pad_diameter: float = 10.0
    pad_boss_height: float = 1.5
    pad_rubber_thickness: float = 1 / 32 * INCH
    pad_preload_min: float = 0.1  # Compression of the rubber on the seated plate, mm.
    pad_preload_max: float = 0.5
    # Mounting on the Dremel 220 base: an ear on each of the ±x faces, slotted along y for a 5/16"-18 carriage
    # bolt riding in the base slot below, which runs along x. The crossed slots let the fixture move in x and y
    # to bring each bushing under the spindle.
    ear_bolt_radius: float = 40.0  # From the part axis; the thumb nut turns clear of the nest face.
    ear_thickness: float = 8.0
    ear_travel: float = 12.0  # Each way along the ear slot (y); the bushings are within 11 mm in y.
    slot_travel: float = 10.5  # Each way along the base slot (x); the bushings are within 9.6 mm in x.
    ear_slot_clearance_diametral: float = 0.5
    ear_wall: float = 5.0  # Beyond the slot ends.
    ear_overlap: float = 0.5  # Into the nest face.
    ear_outer_margin: float = 2.0  # Beyond the washer.
    # Fillet at the ear root, along its top edge and its two ends against the nest face, blended at the corners;
    # limited by the cap nest's face above the ear.
    ear_root_fillet_radius: float = 2.0
    nut_clearance: float = 1.0  # Thumb-nut head to the nest face.
    # Dremel 220 base (measured): 3/8" slots, 7/32" deep, from 3/4" (the apex of the inner rounded end) to 2-1/4"
    # (the keyhole) from the spindle axis along the diagonal. A sheet under the nest protects the base.
    base_slot_depth: float = 7 / 32 * INCH
    base_slot_inner_radius: float = 3 / 4 * INCH
    base_slot_outer_radius: float = 9 / 4 * INCH
    base_sheet_thickness: float = 1 / 8 * INCH  # The 1/8" UHMW sheet (SHP-012).
    min_nut_engagement: float = 8.0

    def validate(self) -> None:
        require_positive_dimensions(self, allow_zero=True)
        self.layout.validate()
        for kind, bushing in BUSHINGS.items():
            if abs(bushing.bore - self.layout.cap_hole_diameter(kind)) > 1e-9:
                raise ValueError(f"{kind} bushing bore is not the cap's drilled diameter")
        if abs(self.plate_thickness - BUSHINGS["lead"].length) > 1e-9:
            raise ValueError("Plate thickness must equal the bushing length")
        if self.ring_inner_diameter < self.light.heatsink_diameter + 0.5:
            raise ValueError("Ring must clear the heatsink base")
        if self.ring_outer_diameter - self.ring_inner_diameter < 3.0:
            raise ValueError("Ring wall under 1.5 mm")
        if self.key_slot_outer_radius >= self.body_side / 2 - 1.0:
            raise ValueError("Key slot leaves under 1 mm of wall")
        if not self.pad_preload_min <= self.pad_preload <= self.pad_preload_max:
            raise ValueError(f"Hold-down pad compresses {self.pad_preload:.2f} mm, not within its limits")
        if self.pad_clearance() < self.min_web:
            raise ValueError("Hold-down pad is too close to a bushing")
        if self.web() < self.min_web:
            raise ValueError(f"Plate web {self.web():.2f} mm is under {self.min_web:.2f} mm")
        if self.relief_window_diameter / 2 < self.hole_reach() + 0.5:
            raise ValueError("Relief window leaves under 0.5 mm of support ring inside the hole pattern")
        if not 0 < self.window_flat_top < self.window_width:
            raise ValueError("Window flat top must be narrower than the window")
        if self.window_chamfer >= self.window_top_z(HEATSINK) - self.window_floor_lip:
            raise ValueError("Window chamfers leave no vertical sides")
        if self.rib_width + self.rib_clearance_width > self.channel_width:
            raise ValueError("Rib does not fit the channel")

        if self.thumb_nut_gap() < self.nut_clearance:
            raise ValueError(f"Thumb nut turns within {self.thumb_nut_gap():.2f} mm of the nest")
        if self.nut_engagement() < self.min_nut_engagement:
            raise ValueError(f"Carriage bolt engages the thumb nut by only {self.nut_engagement():.2f} mm")
        lo, hi = self.bolt_slot_range()
        if lo < self.base_slot_inner_radius or hi > self.base_slot_outer_radius:
            raise ValueError(f"Carriage-bolt neck travels {lo:.1f}-{hi:.1f} mm, beyond the base slot")
        if self.base_slot_depth < MCMASTER_92356A589_NECK_LENGTH:
            raise ValueError("Carriage-bolt neck is longer than the base slot is deep")
        if self.ear_top + self.ear_root_fillet_radius >= self.nest_top(CAP):
            raise ValueError("Ears and their root fillets must stay below the plate")
        washer_edge = self.ear_bolt_radius - MCMASTER_96659A134_DIAMETER / 2
        if self.body_side / 2 + self.ear_root_fillet_radius >= washer_edge:
            raise ValueError("Ear root fillet reaches under the washer")
        if self.ear_half_length + self.ear_root_fillet_radius >= self.body_side / 2:
            raise ValueError("Ear end fillets run past the nest face")

    # Derived dimensions.
    @property
    def flange_thickness(self) -> float:
        return self.light.cap_overall - self.light.cap_thread_length

    @property
    def ring_outer_diameter(self) -> float:
        return self.plate_bore_diameter - self.slip_clearance_diametral

    @property
    def pocket_diameter(self) -> float:
        return self.light.cap_flange_diameter + self.slip_clearance_diametral

    @property
    def channel_width(self) -> float:
        """Width of the open channels between pin columns through the heatsink center."""
        return self.layout.lattice_pitch - self.layout.pin_diameter

    @property
    def rib_width(self) -> float:
        return self.channel_width - self.rib_clearance_width

    @property
    def key_slot_outer_radius(self) -> float:
        return self.plate_bore_diameter / 2 + self.key_projection + self.key_relief

    @property
    def window_chamfer(self) -> float:
        """Each 45° top corner of a window, in both width and height."""
        return (self.window_width - self.window_flat_top) / 2

    def window_top_z(self, kind: str) -> float:
        """Peak of the windows: solid above it, below the plate's counterbore zone."""
        return self.nest_top(kind) - self.ring_height - self.ring_relief - self.window_top_margin

    @property
    def pad_preload(self) -> float:
        """How far the seated plate compresses the pad's rubber against the part face."""
        return self.pad_boss_height + self.pad_rubber_thickness - self.standoff

    def pad_clearance(self) -> float:
        """Smallest gap between the pad and a bushing's outside."""
        return min(
            hypot(*h.position) - BUSHINGS[h.kind].outer_diameter / 2 - self.pad_diameter / 2
            for h in self.layout.holes()
        )

    @property
    def ear_slot_width(self) -> float:
        return MCMASTER_92356A589_DIAMETER + self.ear_slot_clearance_diametral

    @property
    def ear_half_length(self) -> float:
        """Half the ear's length across the diagonal."""
        return self.ear_travel + self.ear_slot_width / 2 + self.ear_wall

    @property
    def ear_inner_reach(self) -> float:
        return self.body_side / 2 - self.ear_overlap

    @property
    def ear_outer_reach(self) -> float:
        return self.ear_bolt_radius + MCMASTER_96659A134_DIAMETER / 2 + self.ear_outer_margin

    @property
    def ear_top(self) -> float:
        return -self.floor_thickness + self.ear_thickness

    @property
    def bolt_under_head_z(self) -> float:
        """The carriage bolt's under-head face, on the underside of the base slot."""
        return -self.floor_thickness - self.base_sheet_thickness - self.base_slot_depth

    def nut_engagement(self) -> float:
        """Bolt thread in the thumb nut, which bears on the washer on the ear."""
        bearing = self.ear_top + MCMASTER_96659A134_THICKNESS
        return min(self.bolt_under_head_z + MCMASTER_92356A589_LENGTH - bearing, MCMASTER_95150A180_HEIGHT)

    def bolt_slot_range(self) -> tuple[float, float]:
        """Nearest and farthest reach of the bolt's square neck along the base slot, from the spindle axis."""
        neck = MCMASTER_92356A589_NECK_WIDTH / 2
        return (
            self.ear_bolt_radius - self.slot_travel - neck,
            self.ear_bolt_radius + self.slot_travel + neck,
        )

    def thumb_nut_gap(self) -> float:
        """Smallest gap between the thumb nut's head and the nest's sides, over the ear slot's travel."""
        h = self.body_side / 2
        gaps = []
        for angle in EAR_ANGLES:
            c, s = cos(radians(angle)), sin(radians(angle))
            for i in range(NUT_SWEEP_SAMPLES):
                v = -self.ear_travel + 2 * self.ear_travel * i / (NUT_SWEEP_SAMPLES - 1)
                x, y = self.ear_bolt_radius * c - v * s, self.ear_bolt_radius * s + v * c
                gap = hypot(max(abs(x) - h, 0.0), max(abs(y) - h, 0.0))
                gaps.append(gap - MCMASTER_95150A180_HEAD_DIAMETER / 2)
        return min(gaps)

    def ear_bolt_position(self, angle: float) -> tuple[float, float]:
        """Bolt axis at the center of an ear slot."""
        return self.ear_bolt_radius * cos(radians(angle)), self.ear_bolt_radius * sin(radians(angle))

    def part_height(self, kind: str) -> float:
        """Height of the part's LED-side face above its support surface."""
        return {CAP: self.light.cap_overall, HEATSINK: self.light.heatsink_height}[kind]

    def nest_top(self, kind: str) -> float:
        """Height of the nest's top face, where the plate seats: the part face plus the standoff."""
        return self.part_height(kind) + self.standoff

    def bore_floor(self, kind: str) -> float:
        """Floor of the nest's plate bore: the support surface for the heatsink, a counterbore for the cap."""
        return 0.0 if kind == HEATSINK else self.nest_top(kind) - self.ring_height - self.ring_relief

    def holes(self, kind: str) -> list[Hole]:
        """The layout's holes that a part is drilled through."""
        if kind == CAP:
            return self.layout.holes()
        return [h for h in self.layout.holes() if h.kind in HEATSINK_KINDS]

    def bore_diameter(self, hole: Hole) -> float:
        return BUSHINGS[hole.kind].outer_diameter + self.bushing_bore_oversize

    def web(self) -> float:
        """Smallest plate material between two neighboring bushing bores."""
        holes = self.layout.holes()
        return min(
            hypot(a.x - b.x, a.y - b.y) - (self.bore_diameter(a) + self.bore_diameter(b)) / 2
            for i, a in enumerate(holes)
            for b in holes[i + 1 :]
        )

    def hole_reach(self) -> float:
        """Farthest edge of any drilled hole from the axis."""
        return max(
            hypot(*h.position) + self.layout.cap_hole_diameter(h.kind) / 2 for h in self.layout.holes()
        )

    def rib_clears_pins(self) -> float:
        """Smallest gap between the rib's arms and the pins, mm."""
        w = self.rib_width / 2
        gaps = []
        for px, py in self.layout.pin_positions():
            r = self.layout.pin_radius
            gaps.append(min(abs(px) - w, abs(py) - w) - r)  # Distance to the nearer arm's side.
        return min(gaps)


def _corner_screw_positions(p):
    s = p.screw_offset
    return [(sx * s, sy * s) for sx in (-1, 1) for sy in (-1, 1)]


@cache
def build_bushing_plate(p: DrillFixtureParameters):
    """The bushing plate: seat face on z=0, drilling face at z=plate_thickness, ring and key below.

    Printed flat with the ring up, so the bores are vertical.
    """
    h = p.body_side / 2
    plate = box_between(-h, h, -h, h, 0, p.plate_thickness)
    ring = z_cylinder(p.ring_outer_diameter, 0, 0, -p.ring_height, 0)
    ring -= z_cylinder(p.ring_inner_diameter, 0, 0, -p.ring_height - CUT_OVERRUN, CUT_OVERRUN)
    tab_outer = p.plate_bore_diameter / 2 + p.key_projection
    tab_inner = p.ring_outer_diameter / 2 - 0.5  # Overlaps the ring wall.
    tab = box_between(tab_inner, tab_outer, -p.key_width / 2, p.key_width / 2, -p.ring_height, 0)
    plate = plate + ring + tab + z_cylinder(p.pad_diameter, 0, 0, -p.pad_boss_height, 0)
    for x, y in _corner_screw_positions(p):
        plate -= z_cylinder(
            p.layout.m3_clearance_diameter, x, y, -CUT_OVERRUN, p.plate_thickness + CUT_OVERRUN
        )
    for hole in p.layout.holes():
        plate -= z_cylinder(
            p.bore_diameter(hole),
            hole.x,
            hole.y,
            -p.ring_height - CUT_OVERRUN,
            p.plate_thickness + CUT_OVERRUN,
        )
    return plate


def window_cutter(p: DrillFixtureParameters, kind: str, axis: str):
    """A window cut through both faces on an axis: vertical sides, then 45° chamfers to a narrow flat top, so
    nothing needs supports or bridges more than the flat."""
    z0, z1 = p.window_floor_lip, p.window_top_z(kind)
    half, c = p.window_width / 2, p.window_chamfer
    outline = [(-half, z0), (half, z0), (half, z1 - c), (half - c, z1), (c - half, z1), (-half, z1 - c)]
    reach = p.body_side / 2 + CUT_OVERRUN
    # Plane.YZ's local x is the global y (cutting through the x faces); Plane.XZ's is the global x.
    plane = Plane.YZ if axis == "x" else Plane.XZ
    return extrude(plane * Polygon(*outline, align=None), amount=reach, both=True)


@cache
def build_ear(p: DrillFixtureParameters):
    """One mounting ear on the +x face, with its bolt slot along y and fillets where it meets the face."""
    z0, z1 = -p.floor_thickness, p.ear_top
    r, w, travel = p.ear_bolt_radius, p.ear_slot_width, p.ear_travel
    face, half = p.body_side / 2, p.ear_half_length
    # The ear on a piece of the face, the root edges filleted, then trimmed to the ear, its fillets, and the
    # overlap into the face.
    f = p.ear_root_fillet_radius
    backing = box_between(face - 2 * f, face, -half - 2 * f, half + 2 * f, z0, z1 + 2 * f)
    ear = fused(backing, box_between(face, p.ear_outer_reach, -half, half, z0, z1))
    roots = [
        e
        for e in ear.edges()
        if abs(e.center().X - face) < EPSILON
        and abs(e.center().Z - z0) > EPSILON
        and abs(e.length) > EPSILON
        and (abs(abs(e.center().Y) - half) < EPSILON or abs(e.center().Z - z1) < EPSILON)
    ]
    trim = box_between(p.ear_inner_reach, p.ear_outer_reach + CUT_OVERRUN, -half - f, half + f, z0, z1 + f)
    ear = intersect(fillet(roots, f), trim)
    ear -= box_between(r - w / 2, r + w / 2, -travel, travel, z0 - CUT_OVERRUN, z1 + CUT_OVERRUN)
    for v in (-travel, travel):
        ear -= z_cylinder(w, r, v, z0 - CUT_OVERRUN, z1 + CUT_OVERRUN)
    return ear


@cache
def build_nest(p: DrillFixtureParameters, kind: str):
    """A nest: support surface at z=0, floor below, top face (the plate seat) at nest_top(kind)."""
    h = p.body_side / 2
    top = p.nest_top(kind)
    nest = box_between(-h, h, -h, h, -p.floor_thickness, top)
    floor = p.bore_floor(kind)
    nest -= z_cylinder(p.plate_bore_diameter, 0, 0, floor, top + CUT_OVERRUN)
    slot_depth = p.ring_height + p.ring_relief
    nest -= box_between(
        p.plate_bore_diameter / 2 - 0.5,
        p.key_slot_outer_radius,
        -(p.key_width + p.key_clearance_width) / 2,
        (p.key_width + p.key_clearance_width) / 2,
        top - slot_depth,
        top + CUT_OVERRUN,
    )
    for x, y in _corner_screw_positions(p):
        recess = top - p.insert_flange_recess_depth
        nest -= z_cylinder(p.insert_flange_recess_diameter, x, y, recess, top + CUT_OVERRUN)
        nest -= z_cylinder(p.insert_hole_diameter, x, y, recess - p.insert_hole_depth, top + CUT_OVERRUN)
    if kind == CAP:
        nest -= z_cylinder(p.pocket_diameter, 0, 0, 0, floor + CUT_OVERRUN)
        nest -= z_cylinder(p.relief_window_diameter, 0, 0, -p.floor_thickness - CUT_OVERRUN, CUT_OVERRUN)
        # Radial clamp: an M3 screw from the -y side bears on the flange at mid-thickness, in a heat-set insert
        # set in the face of a notch that thins the wall.
        z = p.flange_thickness / 2
        face = -h + p.clamp_notch_depth
        nest -= box_between(
            -p.clamp_notch_width / 2,
            p.clamp_notch_width / 2,
            -h - CUT_OVERRUN,
            face,
            -p.floor_thickness - CUT_OVERRUN,
            p.clamp_notch_top,
        )
        nest -= y_cylinder(
            p.insert_flange_recess_diameter, 0, z, face - CUT_OVERRUN, face + p.insert_flange_recess_depth
        )
        nest -= y_cylinder(
            p.insert_hole_diameter,
            0,
            z,
            face - CUT_OVERRUN,
            face + p.insert_flange_recess_depth + p.insert_hole_depth,
        )
        nest -= y_cylinder(
            p.layout.m3_clearance_diameter, 0, z, face - CUT_OVERRUN, -p.pocket_diameter / 2 + CUT_OVERRUN
        )
    else:
        nest -= window_cutter(p, kind, "x")
        nest -= window_cutter(p, kind, "y")
        w, half = p.rib_width, p.rib_half_length
        nest += box_between(-half, half, -w / 2, w / 2, 0, p.rib_height)
        nest += box_between(-w / 2, w / 2, -half, half, 0, p.rib_height)
    ear = build_ear(p)  # Added last, outside the windows' cuts.
    for angle in EAR_ANGLES:
        nest += Rot(Z=angle) * ear
    return nest


def build_bore_coupon(p: DrillFixtureParameters):
    """A strip of bushing-length plate with one row of bores per bushing outside diameter, one column per
    oversize in COUPON_OVERSIZES, for finding the bore that the printer turns into a press fit."""
    diameters = sorted({b.outer_diameter for b in BUSHINGS.values()})
    columns = len(COUPON_OVERSIZES)
    width = (columns - 1) * COUPON_PITCH + 2 * COUPON_MARGIN + max(diameters)
    depth = (len(diameters) - 1) * COUPON_PITCH + 2 * COUPON_MARGIN + max(diameters)
    coupon = box_between(0, width, 0, depth, 0, p.plate_thickness)
    for row, diameter in enumerate(diameters):
        for column, oversize in enumerate(COUPON_OVERSIZES):
            x = COUPON_MARGIN + max(diameters) / 2 + column * COUPON_PITCH
            y = COUPON_MARGIN + max(diameters) / 2 + row * COUPON_PITCH
            coupon -= z_cylinder(diameter + oversize, x, y, -CUT_OVERRUN, p.plate_thickness + CUT_OVERRUN)
    return coupon


def build_fixture_assembly(p: DrillFixtureParameters | None = None, kind: str = CAP, parts: bool = True):
    """A nest with its plate seated, the bushings in the plate, and (parts) the cap or heatsink in place."""
    p = p or DrillFixtureParameters()
    top = p.nest_top(kind)
    seat = Pos(0, 0, top)
    children = [
        labeled(build_nest(p, kind), NEST_LABEL, PRINTED_BLUE),
        labeled(build_bushing_plate(p), PLATE_LABEL, PRINTED_ORANGE, seat),
    ]
    pad_top = top - p.pad_boss_height
    children.append(
        labeled(
            z_cylinder(p.pad_diameter, 0, 0, top - p.standoff, pad_top),
            PAD_LABEL,
            RUBBER,
        )
    )
    for i, (x, y) in enumerate(_corner_screw_positions(p), start=1):
        children += [
            labeled(
                mcmaster_97171a310(),
                f"{INSERT_LABEL} {i}",
                BUSHING_BRASS,
                Pos(x, y, top - p.insert_flange_recess_depth),
            ),
            labeled(
                mcmaster_91292a114(),
                f"{PLATE_SCREW_LABEL} {i}",
                METAL,
                Pos(x, y, top + p.plate_thickness) * Rot(X=180),
            ),
        ]
    if kind == CAP:
        face = -p.body_side / 2 + p.clamp_notch_depth
        z = p.flange_thickness / 2
        children += [
            labeled(
                mcmaster_97171a310(),
                f"{INSERT_LABEL} 5",
                BUSHING_BRASS,
                Pos(0, face + p.insert_flange_recess_depth, z) * Rot(X=90),
            ),
            labeled(mcmaster_91292a114(), CLAMP_SCREW_LABEL, METAL, Pos(0, face, z) * Rot(X=-90)),
        ]
    for i, hole in enumerate(p.layout.holes(), start=1):
        bushing = BUSHINGS[hole.kind]
        children.append(labeled(bushing.model(), f"{BUSHING_LABEL} {i}", STEEL, Pos(hole.x, hole.y, top)))
    for i, angle in enumerate(EAR_ANGLES, start=1):
        x, y = p.ear_bolt_position(angle)
        turn = Rot(Z=angle)  # The bolt's square neck square to the base slot.
        washer_z = p.ear_top
        children += [
            labeled(
                mcmaster_92356a589(), f"{EAR_BOLT_LABEL} {i}", STEEL, Pos(x, y, p.bolt_under_head_z) * turn
            ),
            labeled(mcmaster_96659a134(), f"{EAR_WASHER_LABEL} {i}", STEEL, Pos(x, y, washer_z)),
            labeled(
                mcmaster_95150a180(),
                f"{EAR_NUT_LABEL} {i}",
                STEEL,
                Pos(x, y, washer_z + MCMASTER_96659A134_THICKNESS),
            ),
        ]
    if parts:
        if kind == CAP:
            # Vendor frame: flange back face at y=-flange thickness, seat face at y=0, thread toward +y; stood
            # on its back face with the thread up.
            part = labeled(
                moved(thorlabs_sm1cp2m(), Pos(0, 0, p.flange_thickness) * Rot(X=90)),
                CAP_LABEL,
                BLACK_ANODIZED,
            )
        else:
            part = labeled(
                moved(alpha_cn40_40b(), Pos(0, 0, p.light.heatsink_height) * Rot(X=90)),
                HEATSINK_LABEL,
                BLACK_ANODIZED,
            )
        children.append(part)
    return assembly(f"Drilling fixture, {kind}", children)


def build_fixtures_side_by_side(p: DrillFixtureParameters | None = None, gap: float = 12.0):
    """Both setups side by side along y, clear of each other's ears, for the design-doc figure."""
    p = p or DrillFixtureParameters()
    pitch = p.body_side + gap
    cap = build_fixture_assembly(p, CAP)
    heatsink = build_fixture_assembly(p, HEATSINK)
    return Compound(
        label="LED module drilling fixtures",
        children=[
            place(Pos(0, -pitch / 2, 0), cap),
            place(Pos(0, pitch / 2, 0), heatsink),
        ],
    )

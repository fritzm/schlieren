"""EXPERIMENT, not the §7 baseline: source-slit head on an SF Technology SEMX40-AS linear stage.

The movable blade rides on the stage table and the width is set by the stage's micrometer; the stationary
blade sits on a printed pedestal at the same height. No flexure, spring, or centering stage. Nothing here is
final until the user accepts it; the design fragments and the BOM still describe the §7 flexure head.

Parts:

- plate: flat printed plate with the SM1-tube-diameter spigot, a Ø34 mm shoulder the SM1RC/M seats against, and
  a Ø24 mm light bore. The spigot is short, so the ring also grips an SM1 baffle tube (two SM1L15) from the
  light-source side. The stage bolts to the plate's front with captive nuts at its rear; the pedestal is screwed
  on from the plate's rear into heat-set M3 inserts;
- stage: the SEMX40-AS, shown with the XCRS40 vendor solid model (same table and base layout). Its table top, 20 mm above its base, is the blade-seat plane;
- pedestal: printed block carrying the stationary blade, its top in the blade-seat plane;
- toe bars: one printed bar on the table and one on the pedestal, each screwed down at its two ends into the M3
  holes of the table's second row (the stage's tapped holes) or into heat-set M3 inserts in the pedestal. The bar's
  finger runs the length of the blade and bears on its folded spine, so nothing crosses the blade or reaches the
  cutting edge. No blade is drilled.

Local frame, shown at rotation 0 (slit horizontal, micrometer up): x along the slit, z the adjustment axis (+z
toward the micrometer), y the optical axis, +y out of the front toward the mirror, as the §7 head. The origin
is the slit center on the blade-seat plane. The stage is at its mid-travel (its base flush with its table).

Assembly frame is the §3.4 source rail frame, as slit_head: x transverse, +y along the rail toward the mirror,
z=0 at the rail top, with the slit post at x=y=0. The light comes from the source side through the baffle
tube and the plate's bore, passing the stage's edge to reach the slit from behind, so the spigot, ring, and post
are on the light-source side of the blades.

**Provisional:** the stage's base mounting holes (four M3 counterbored, 32 mm pitch) are assumed to be
reachable from the table side with the screws through the base flange; confirm on the stage. The blade overhang
(1.9 mm past the table edge) and the toe bar's squeeze on the EPDM pad are first-print values.
"""

from dataclasses import dataclass
from functools import cache
from math import isfinite, radians, tan

from build123d import Axis, Plane, Polygon, Pos, Rot, Shape, extrude, fillet

from schlieren.cad import (
    CUT_OVERRUN,
    assembly,
    box_between,
    fused,
    labeled,
    y_cylinder,
    y_hex,
)
from schlieren.hardware import (
    M3_INSERT_FLANGE_RECESS_DEPTH,
    M3_INSERT_FLANGE_RECESS_DIAMETER,
    M3_INSERT_HOLE_DEPTH,
    M3_INSERT_HOLE_DIAMETER,
    M3_INSERT_INSTALLED_LENGTH,
)
from schlieren.palette import (
    BLACK_ANODIZED,
    BUSHING_BRASS,
    METAL,
    PRINTED_BLUE,
    PRINTED_DENIM,
    PRINTED_GREEN,
    RUBBER,
)
from schlieren.parts.rail_shoe import REFERENCE_HARDWARE_LABEL, post_stack
from schlieren.parts.slit_head import SlitHeadParameters
from schlieren.standards import INCH
from schlieren.vendor_cad import (
    SM1RC_M_THICKNESS,
    cadenas_xcrs40_parts,
    mcmaster_91292a114,
    mcmaster_91828a211,
    mcmaster_97171a310,
)

_HEAD = SlitHeadParameters()  # Shared defaults: blades, SM1 spigot and ring, M3 hardware.

# SF Technology SEMX40-AS stage (sflinear.com.tw drawing SEMX40-AS-2D), in the frame of the CADENAS XCRS40 vendor
# model that shows it: X the travel axis with the micrometer toward +X, Y up from the base (0) to the table top,
# Z across the table. These are manufacturer values, not measurements of the stage on hand.
STAGE_SIZE = 40.0  # Table and base outline, X and Z.
STAGE_THICKNESS = 20.0  # Base underside to table top.
STAGE_TRAVEL_HALF = 6.5
STAGE_TABLE_HOLE_PITCH = 16.0  # 3 x 3 M3 holes in the table top.
STAGE_TABLE_HOLE_DEPTH = 6.5
STAGE_BASE_HOLE_PITCH = 32.0  # 4 M3 counterbored base holes.
STAGE_BASE_FLANGE = 3.0  # Base flange thickness at the holes (vendor model).
STAGE_END_BUMP = 0.8  # Base and carriage end features beyond the 40 mm outline, X = +-20.8 (vendor model).
STAGE_END_BUMP_FAR_Y = 12.8  # Their farthest extent below the table top (they span 9.2 to 12.8 mm).
STAGE_MICROMETER_TIP_X = 46.0  # Thimble end in the vendor model, which shows the carriage centered.


@dataclass(frozen=True)
class SlitStageParameters:
    optical_height: float = _HEAD.optical_height
    datum_thickness: float = _HEAD.datum_thickness
    post_length: float = _HEAD.post_length
    post_diameter: float = _HEAD.post_diameter
    ring_thickness: float = SM1RC_M_THICKNESS
    ring_bore: float = _HEAD.ring_bore
    # Stanley 11-515 blades, measured (§7.1).
    blade_length: float = _HEAD.blade_length
    blade_width: float = _HEAD.blade_width
    blade_thickness: float = _HEAD.blade_thickness
    spine_thickness: float = _HEAD.spine_thickness
    spine_width: float = _HEAD.spine_width  # Display only; fold width not measured.
    slit_width: float = _HEAD.slit_width  # Display/setup value; the stage sets the width.
    # Blade edge beyond the table and pedestal edges. Larger than the flexure head's, so the stage's end
    # features (STAGE_END_BUMP) clear the source cone.
    blade_overhang: float = 1.9
    # Plate, spigot, and the shared SM1RC/M.
    plate_thickness: float = 6.0
    plate_margin: float = 3.0  # Plate edge beyond the stage and pedestal outlines.
    plate_corner_diameter: float = 6.0
    spigot_diameter: float = _HEAD.spigot_diameter  # SM1 tube OD.
    spigot_bore: float = _HEAD.spigot_bore
    spigot_shoulder_diameter: float = _HEAD.spigot_shoulder_diameter
    ring_gap: float = _HEAD.ring_gap  # Plate rear to ring face, the shoulder thickness.
    ring_grip: float = (
        4.5  # Spigot engagement in the ring; the baffle tube takes the same from the other side.
    )
    post_clearance: float = _HEAD.post_clearance
    # Common M3 hardware: 91292A114 M3 x 12 SHCS, 91828A211 nut.
    screw_length: float = _HEAD.screw_length
    screw_clearance: float = _HEAD.screw_clearance
    screw_head_diameter: float = _HEAD.screw_head_diameter
    screw_head_height: float = _HEAD.screw_head_height
    counterbore_clearance: float = _HEAD.counterbore_clearance  # Diametral.
    nut_across_flats: float = _HEAD.nut_across_flats
    nut_thickness: float = _HEAD.nut_thickness
    nut_across_flats_clearance: float = _HEAD.nut_across_flats_clearance
    nut_axial_clearance: float = _HEAD.nut_axial_clearance
    # Toe bars: the slit side of the screw row is the finger, the far side the heel.
    toe_x: tuple = (-STAGE_TABLE_HOLE_PITCH, STAGE_TABLE_HOLE_PITCH)  # Along the slit, on the hole grid.
    toe_end_margin: float = 3.5  # Bar end beyond the outer screw axis, along the slit.
    toe_thickness: float = 6.0  # Sets the screw's thread engagement: screw_length - toe_thickness.
    toe_heel: float = 4.5  # Screw axis to the heel end.
    toe_body_setback: float = (
        1.5  # Screw axis to the body edge toward the slit; clears the blade's rear edge.
    )
    toe_finger_length: float = 3.0
    toe_pad_squeeze: float = 0.3  # EPDM pad compression under the finger, provisional.
    toe_pad_inset: float = 1.0  # EPDM pad end inset from the bar end.
    epdm_thickness: float = INCH / 32  # McMaster 9852N37, uncompressed.
    # Pedestal.
    pedestal_end_margin: float = 2.0  # Beyond the stage outline along the slit.
    pedestal_end_clearance: float = 1.5  # Heel end to pedestal edge.
    # McMaster 97171A310 heat-set inserts in the pedestal (toe screws from the top, mounting screws from the
    # bottom), flanges recessed flush.
    insert_hole_diameter: float = M3_INSERT_HOLE_DIAMETER
    insert_hole_depth: float = M3_INSERT_HOLE_DEPTH  # Below the flange recess.
    insert_flange_recess_diameter: float = M3_INSERT_FLANGE_RECESS_DIAMETER
    insert_flange_recess_depth: float = M3_INSERT_FLANGE_RECESS_DEPTH
    insert_installed_length: float = M3_INSERT_INSTALLED_LENGTH
    pedestal_screw_hole_height: float = 10.0  # Plate front up to the end of the screw clearance holes.
    # SM1 baffle tube: two SM1L15 threaded together, nominal thread depth (provisional length).
    tube_diameter: float = _HEAD.spigot_diameter
    tube_clear_diameter: float = 22.9  # SM1L15 drawing.
    tube_length: float = 2 * 1.5 * INCH
    # Beam: the source cone about the chief ray (§3.2), the lit slit length (§6.6), and the margin the stage
    # and pedestal edges keep from the cone.
    cone_half_angle: float = 2.0  # Degrees.
    lit_half_length: float = 5.0
    beam_margin: float = 0.5

    # Table and pedestal edges, and the stage.
    @property
    def table_edge(self):
        return self.slit_width / 2 + self.blade_overhang

    @property
    def stage_center_z(self):
        return self.table_edge + STAGE_SIZE / 2

    @property
    def toe_row_distance(self):
        """Table edge to the second row of tapped holes (the stage's mid-row, X = 0)."""
        return STAGE_SIZE / 2

    @property
    def pedestal_depth(self):
        return self.toe_row_distance + self.toe_heel + self.pedestal_end_clearance

    @property
    def pedestal_half_length(self):
        return STAGE_SIZE / 2 + self.pedestal_end_margin

    # Plate.
    @property
    def plate_front(self):
        return -STAGE_THICKNESS

    @property
    def plate_back(self):
        return self.plate_front - self.plate_thickness

    @property
    def plate_half_width(self):
        return STAGE_SIZE / 2 + self.plate_margin

    @property
    def plate_z(self):
        return (
            -(self.table_edge + self.pedestal_depth + self.plate_margin),
            self.table_edge + STAGE_SIZE + self.plate_margin,
        )

    @property
    def spigot_length(self):
        return self.ring_gap + self.ring_grip

    @property
    def tube_gap(self):
        """Spigot end to baffle tube end inside the ring."""
        return self.ring_thickness - 2 * self.ring_grip

    @property
    def nut_floor(self):
        """Plate-rear nut pockets: the pocket's floor, on the nut's front face."""
        return self.plate_back + self.nut_thickness + self.nut_axial_clearance

    @property
    def counterbore_floor(self):
        return self.plate_back + self.screw_head_height + self.nut_axial_clearance

    def stage_screw_xz(self):
        """The stage's four base-hole axes, on the plate."""
        half = STAGE_BASE_HOLE_PITCH / 2
        return [(-sz, self.stage_center_z + sx) for sx in (-half, half) for sz in (-half, half)]

    def pedestal_screw_xz(self):
        z = -(self.table_edge + self.pedestal_depth / 2)
        return [(x, z) for x in self.toe_x]

    @property
    def toe_z(self):
        """z of the toe screws on the table (movable side); the pedestal's mirror it."""
        return self.table_edge + self.toe_row_distance

    @property
    def toe_bar_half_length(self):
        return max(abs(x) for x in self.toe_x) + self.toe_end_margin

    @property
    def toe_finger_underside(self):
        return self.spine_thickness + self.epdm_thickness - self.toe_pad_squeeze

    @property
    def micrometer_reach(self):
        """Micrometer tip beyond the optical axis along +z at the stage's mid-travel."""
        return self.stage_center_z + STAGE_MICROMETER_TIP_X

    def validate(self):
        for name, value in vars(self).items():
            if isinstance(value, float) and not isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.spigot_diameter >= self.ring_bore or self.spigot_bore >= self.spigot_diameter - 4:
            raise ValueError("Spigot must slip into the SM1RC/M and keep a wall")
        if self.spigot_shoulder_diameter < self.ring_bore + 2.0:
            raise ValueError("Spigot shoulder needs a land on the SM1RC/M face")
        if self.tube_gap < 0.5:
            raise ValueError("Spigot and baffle tube must not crowd each other in the ring")
        post_top_below_axis = self.optical_height - self.datum_thickness - self.post_length
        if self.spigot_shoulder_diameter / 2 > post_top_below_axis - self.post_clearance:
            raise ValueError("Spigot shoulder must clear the post top")
        if self.ring_gap - (self.post_diameter - self.ring_thickness) / 2 < self.post_clearance:
            raise ValueError("Plate must clear the post")
        if self.toe_x != tuple(-x for x in reversed(self.toe_x)) or self.toe_bar_half_length > STAGE_SIZE / 2:
            raise ValueError(
                "Toe screws must be symmetric about the slit center and the bar must sit on the table"
            )
        if self.toe_bar_half_length < self.blade_length / 2 - 0.1:
            raise ValueError("Toe bar must span the blade")
        if self.screw_length - self.toe_thickness > STAGE_TABLE_HOLE_DEPTH:
            raise ValueError("Toe screws must not bottom in the table's tapped holes")
        # The finger lands on the folded spine, behind the blade's rear edge and the body edge.
        rear_edge = self.blade_width - self.blade_overhang  # From the table edge toward the stage.
        screw_to_rear = self.toe_row_distance - rear_edge
        if screw_to_rear <= self.toe_body_setback:
            raise ValueError("Toe bar body must stop short of the blade's rear edge")
        if self.toe_body_setback + self.toe_finger_length < screw_to_rear + self.spine_width:
            raise ValueError("Toe finger must cover the blade spine")
        if self.toe_finger_underside <= self.spine_thickness or self.toe_pad_squeeze <= 0:
            raise ValueError("Toe finger must hold the EPDM pad in compression")
        if self.toe_heel + self.toe_row_distance > self.pedestal_depth:
            raise ValueError("Pedestal must carry the toe bar heel")
        engagement = self.screw_length - self.toe_thickness
        if engagement > self.insert_hole_depth or engagement < self.insert_installed_length - 0.5:
            raise ValueError("Toe screws must run through the pedestal's inserts without bottoming")
        if self.pedestal_screw_hole_height <= self.insert_flange_recess_depth + self.insert_hole_depth:
            raise ValueError("Pedestal screws need clearance holes past their inserts")
        if self.beam_clearance < self.beam_margin:
            raise ValueError("Stage and pedestal edges must clear the source cone")

    @property
    def beam_clearance(self):
        """Gap between the source cone and the stage or pedestal: the table edge at the plate front, or the stage's
        end features at their farthest extent below the table top."""
        slope = tan(radians(self.cone_half_angle))
        edge = self.table_edge - (self.slit_width / 2 + -self.plate_front * slope)
        bump = self.table_edge - STAGE_END_BUMP - (self.slit_width / 2 + STAGE_END_BUMP_FAR_Y * slope)
        return min(edge, bump)


# --- Stage proxy and its placement ---------------------------------------------------------------------------


def stage_location(p):
    """Stage (vendor) frame -> local head frame: X -> +z (micrometer up), Y -> y, Z -> -x; table top at y=0."""
    return Pos(0, -STAGE_THICKNESS, p.stage_center_z) * Rot(Y=-90)


def build_stage():
    """The stage in its vendor frame as (base, carriage, micrometer, base side plate, carriage lock knob)."""
    return cadenas_xcrs40_parts()


# --- Printed parts -------------------------------------------------------------------------------------------


@cache
def build_stage_plate(p=None):
    """Plate with the spigot, shoulder, and light bore; stage and pedestal bolt to its front.

    Print front face down, spigot up, without supports, as the §7 spigot adapter."""
    p = p or SlitStageParameters()
    p.validate()
    z0, z1 = p.plate_z
    plate = box_between(-p.plate_half_width, p.plate_half_width, p.plate_back, p.plate_front, z0, z1)
    plate = fillet(plate.edges().filter_by(Axis.Y), p.plate_corner_diameter / 2)
    shoulder_back = p.plate_back - p.ring_gap
    plate += y_cylinder(p.spigot_shoulder_diameter, 0, 0, shoulder_back, p.plate_back + 0.5)
    plate += y_cylinder(p.spigot_diameter, 0, 0, p.plate_back - p.spigot_length, shoulder_back + 0.5)
    plate -= y_cylinder(
        p.spigot_bore, 0, 0, p.plate_back - p.spigot_length - CUT_OVERRUN, p.plate_front + CUT_OVERRUN
    )
    # Stage screws: heads on the stage side, captive nuts in the plate's rear. The pockets open through the
    # shoulder where the screws run inside its radius.
    for x, z in p.stage_screw_xz():
        plate -= y_cylinder(p.screw_clearance, x, z, shoulder_back - CUT_OVERRUN, p.plate_front + CUT_OVERRUN)
        plate -= y_hex(
            p.nut_across_flats + p.nut_across_flats_clearance, x, z, shoulder_back - CUT_OVERRUN, p.nut_floor
        )
    # Pedestal screws: heads counterbored into the plate's rear, nuts in the pedestal.
    for x, z in p.pedestal_screw_xz():
        plate -= y_cylinder(p.screw_clearance, x, z, p.plate_back - CUT_OVERRUN, p.plate_front + CUT_OVERRUN)
        plate -= y_cylinder(
            p.screw_head_diameter + p.counterbore_clearance,
            x,
            z,
            p.plate_back - CUT_OVERRUN,
            p.counterbore_floor,
        )
    return plate


@cache
def build_pedestal(p=None):
    """Block carrying the stationary blade, its top in the blade-seat plane (y = 0) with its edge at the
    carrier edge; print top face down."""
    p = p or SlitStageParameters()
    p.validate()
    edge, depth, half = p.table_edge, p.pedestal_depth, p.pedestal_half_length
    pedestal = box_between(-half, half, p.plate_front, 0, -(edge + depth), -edge)
    recess = p.insert_flange_recess_depth
    for x in p.toe_x:  # Toe screws: inserts set from the top face, flanges recessed under the bar.
        z = -p.toe_z
        pedestal -= y_cylinder(p.insert_flange_recess_diameter, x, z, -recess, CUT_OVERRUN)
        pedestal -= y_cylinder(
            p.insert_hole_diameter, x, z, -recess - p.insert_hole_depth, -recess + CUT_OVERRUN
        )
    for x, z in p.pedestal_screw_xz():  # Mounting screws: inserts set from the bottom face.
        bottom = p.plate_front
        pedestal -= y_cylinder(p.insert_flange_recess_diameter, x, z, bottom - CUT_OVERRUN, bottom + recess)
        pedestal -= y_cylinder(
            p.insert_hole_diameter, x, z, bottom - CUT_OVERRUN, bottom + recess + p.insert_hole_depth
        )
        pedestal -= y_cylinder(
            p.screw_clearance, x, z, bottom - CUT_OVERRUN, bottom + p.pedestal_screw_hole_height
        )
    return pedestal


@cache
def build_toe_bar(p=None):
    """One toe bar in the movable-blade position: centered on the slit along x, its two screw axes along y at
    z = 0, the seat plane at y = 0, the slit toward -z. The finger's underside is raised to hold the EPDM pad
    on the blade spine; the heel sits on the table. Print flat, heel side down."""
    p = p or SlitStageParameters()
    p.validate()
    half = p.toe_bar_half_length
    body = box_between(-half, half, 0, p.toe_thickness, -p.toe_body_setback, p.toe_heel)
    finger_z0 = -p.toe_body_setback - p.toe_finger_length
    finger = box_between(
        -half, half, p.toe_finger_underside, p.toe_thickness, finger_z0, -p.toe_body_setback + 0.5
    )
    bar = fused(body, finger)
    for x in p.toe_x:
        bar -= y_cylinder(p.screw_clearance, x, 0, -CUT_OVERRUN, p.toe_thickness + CUT_OVERRUN)
    return bar


def _toe_pad(p):
    z1 = -p.toe_body_setback
    half = p.toe_bar_half_length - p.toe_pad_inset
    return box_between(-half, half, p.spine_thickness, p.toe_finger_underside, z1 - p.toe_finger_length, z1)


def blade(p, sign):
    """Stanley blade on the blade-seat plane, cutting edge at the slit; sign +1 above the slit (movable, on the
    table), -1 below (stationary, on the pedestal)."""
    edge = sign * p.slit_width / 2
    far = edge + sign * p.blade_width
    half = p.blade_length / 2
    flat = box_between(-half, half, 0, p.blade_thickness, min(edge, far), max(edge, far))
    spine_near = far - sign * p.spine_width
    spine = box_between(-half, half, 0, p.spine_thickness, min(spine_near, far), max(spine_near, far))
    return flat + spine


def beam_envelope(p):
    """The source cone behind the slit (toward the plate), through the slit width and the lit length."""
    depth = -p.plate_front
    spread = depth * tan(radians(p.cone_half_angle))
    edge = p.slit_width / 2
    outline = Polygon((0, edge), (-depth, edge + spread), (-depth, -edge - spread), (0, -edge), align=None)
    half_length = p.lit_half_length + spread
    return extrude(Plane.YZ.offset(-half_length) * outline, amount=2 * half_length)


# --- Assembly ------------------------------------------------------------------------------------------------


def head_location(p, rotation=0.0):
    """Local head frame -> assembly (source rail) frame; rotation in degrees about the optical axis.

    The blades face the mirror (local +y is rail +y); the plate, ring, and post are behind them."""
    ring_face = SM1RC_M_THICKNESS / 2
    blade_plane = ring_face + p.ring_gap - p.plate_back
    return Pos(0, blade_plane, p.optical_height) * Rot(Y=rotation)


def _m3(loc, x, z, bearing_y, shank_toward_back, name, metal):
    """M3 x 12 screw with its bearing face at bearing_y; its head toward +y when the shank goes toward -y."""
    turn = Rot(X=90) if shank_toward_back else Rot(X=-90)
    return labeled(mcmaster_91292a114(), name, metal, loc * Pos(x, bearing_y, z) * turn)


def build_slit_stage_assembly(p=None, rotation=0.0, include_support=True, side_screws=False):
    """Plate, stage, pedestal, blades, toe bars, screws, nuts, and the baffle tube on the slit post;
    rotation 0 is a horizontal slit. side_screws adds the rail shoe's side-channel screws and washers."""
    p = p or SlitStageParameters()
    p.validate()
    loc = head_location(p, rotation)
    metal = METAL
    base, carriage, micrometer, side_plate, lock_knob = build_stage()
    children: list[Shape] = [
        labeled(build_stage_plate(p), "Stage plate", PRINTED_DENIM, loc),
        labeled(build_pedestal(p), "Pedestal", PRINTED_BLUE, loc),
        labeled(base, "Stage base", BLACK_ANODIZED, loc * stage_location(p)),
        labeled(carriage, "Stage carriage", BLACK_ANODIZED, loc * stage_location(p)),
        labeled(micrometer, "Stage micrometer", METAL, loc * stage_location(p)),
        labeled(side_plate, "Stage side plate", METAL, loc * stage_location(p)),
        labeled(lock_knob, "Stage lock knob", METAL, loc * stage_location(p)),
        labeled(blade(p, 1), "Movable blade", metal, loc),
        labeled(blade(p, -1), "Stationary blade", metal, loc),
    ]
    bar = build_toe_bar(p)
    pad = _toe_pad(p)
    for side, name, turn in ((1, "Movable", 0), (-1, "Stationary", 180)):
        placed = loc * Pos(0, 0, side * p.toe_z) * Rot(Y=turn)
        children.append(labeled(bar, f"{name} toe bar", PRINTED_GREEN, placed))
        children.append(labeled(pad, f"{name} toe EPDM", RUBBER, placed))
        for i, x in enumerate(p.toe_x, 1):
            on_axis = loc * Pos(x, 0, side * p.toe_z) * Rot(X=90)
            children.append(
                labeled(
                    mcmaster_91292a114(),
                    f"{name} toe screw {i}",
                    metal,
                    on_axis * Pos(0, 0, -p.toe_thickness),
                )
            )
            if side < 0:  # Heat-set insert under the bar, flange recessed.
                insert_loc = loc * Pos(x, -p.insert_flange_recess_depth, side * p.toe_z) * Rot(X=-90)
                children.append(
                    labeled(mcmaster_97171a310(), f"Pedestal toe insert {i}", BUSHING_BRASS, insert_loc)
                )
    for i, (x, z) in enumerate(p.stage_screw_xz(), 1):
        head_y = p.plate_front + STAGE_BASE_FLANGE
        children.append(_m3(loc, x, z, head_y, True, f"Stage screw {i}", metal))
        nut = Rot(Z=90) * mcmaster_91828a211()
        children.append(
            labeled(nut, f"Stage nut {i}", metal, loc * Pos(x, 0, z) * Rot(X=90) * Pos(0, 0, -p.nut_floor))
        )
    for i, (x, z) in enumerate(p.pedestal_screw_xz(), 1):
        children.append(_m3(loc, x, z, p.counterbore_floor, False, f"Pedestal screw {i}", metal))
        insert_loc = loc * Pos(x, p.plate_front + p.insert_flange_recess_depth, z) * Rot(X=90)
        children.append(labeled(mcmaster_97171a310(), f"Pedestal insert {i}", BUSHING_BRASS, insert_loc))
    # Baffle tube (two SM1L15), entering the ring from the light-source side.
    tube_end = p.plate_back - p.ring_gap - p.ring_thickness + p.ring_grip
    tube = y_cylinder(p.tube_diameter, 0, 0, tube_end - p.tube_length, tube_end)
    tube -= y_cylinder(
        p.tube_clear_diameter, 0, 0, tube_end - p.tube_length - CUT_OVERRUN, tube_end + CUT_OVERRUN
    )
    children.append(labeled(tube, "SM1 baffle tube (2 x SM1L15, proxy)", BLACK_ANODIZED, loc))
    if include_support:
        reference = post_stack(
            ring=True,
            optical_height=p.optical_height,
            datum_thickness=p.datum_thickness,
            side_screws=side_screws,
        )
        children.append(assembly(REFERENCE_HARDWARE_LABEL, reference))
    return assembly("Slit stage head (experiment)", children)

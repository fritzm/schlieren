"""Mirror cell, design §10: three plywood plates, three Kozak fine-adjustment stations, the mirror.

The cell-adjuster plate (1/2 in) and the base plate (1/2 in) are joined by two corner brackets; the 3/4 in
moving mirror plate, a truncated hexagon with a Ø8-1/8 in aperture, carries the mirror and is tilted against
the fixed plate by three adjusters 120° apart. At each station a Kozak TB250-80-625 bushing is bonded in the
moving plate with its flange on the mirror-facing face, and a Kozak TS250-80-2500 screw threads through it,
through a compression spring captured between two seat washers, and through the oversize hole in the fixed
plate. Its KB250-80 knob bears on a McMaster 91131A028 spherical washer pair whose female half sits in a
shallow socket in the rear face of the fixed plate, so the spring holds the knob against the washer.

The plates, with their holes, counterbores, and sockets, are modeled in detail, as are the Kozak parts, the
spherical washers, the brackets, and the bracket fasteners (vendor models; the screw and locknut models are the
unthreaded variants). Each bracket is flush with a side edge of the plates and takes four button-head screws, heads on
the bracket, with a washer and locknut behind the plywood; the plywood holes match the Ø8.33 mm bracket holes. The
mirror is an envelope: Ø203 mm, f=1600 mm, edge thickness assumed 18 mm, its back flush with the plate's rear face. The
springs are plain helices, an illustration with an approximate turn count, and the seat washers are catalog
envelopes. The CAMVATE sliding plate under the base is a rough model: its dovetail section from caliper measurements, its
length, thickness, through slot, and rear V-notch from the seller's dimensioned image. Its screw hardware is
removed in this application. Its four M4 screws are envelopes (catalog head and shank sizes) in countersunk base holes and tapped plate holes
drawn at the nominal thread. Not drawn: the plate's pads, the RTV pad phasing (arbitrary: 0°, 60°, ...), the safety
retainers and transport sandwich (§10.8, not yet designed), and the 1/8 in alignment guide holes (drilled out by
the final 5/16 in hole).

Coordinates: origin at the middle of the base's front edge, on its top surface. +x is right looking along +y,
+y runs from the front edge toward the rear of the base (the mirror looks toward -y), and z is up. The three
adjuster axes are parallel to y.
"""

from dataclasses import dataclass
from math import cos, pi, radians, sin, sqrt

from build123d import (
    Compound,
    Face,
    Helix,
    Location,
    Part,
    Plane,
    Polygon,
    Pos,
    Rot,
    Solid,
    Sphere,
    Wire,
    extrude,
)

from schlieren.cad import (
    along_y,
    assembly,
    box_between,
    centered_box,
    centered_cylinder,
    labeled,
    leaves,
    y_cylinder,
    z_cone,
    z_cylinder,
)
from schlieren.palette import (
    BLACK_OXIDE,
    BRACKET_ALUMINUM,
    BUSHING_BRASS,
    HARDWARE_GRAY,
    KNOB_SILVER,
    MIRROR_GLASS,
    NYLON,
    PLYWOOD,
    QR_PLATE_DARK,
    RTV,
    STAINLESS,
    STEEL,
)
from schlieren.standards import INCH
from schlieren.vendor_cad import (
    KOZAK_KB250_BORE_BOTTOM_X,
    KOZAK_KB250_LENGTH,
    KOZAK_KB250_OPEN_X,
    KOZAK_TB250_FLANGE_THICKNESS,
    KOZAK_TB250_LENGTH,
    KOZAK_TS250_BALL_RADIUS,
    KOZAK_TS250_END_X,
    MCMASTER_8681N11_HOLE_DIAMETER,
    MCMASTER_8681N11_HOLE_OFFSETS,
    MCMASTER_8681N11_THICKNESS,
    MCMASTER_8681N11_WIDTH,
    MCMASTER_91131A028_FEMALE_DIAMETER,
    MCMASTER_91131A028_HEIGHT,
    MCMASTER_96659A134_THICKNESS,
    kozak_kb250_80,
    kozak_tb250_80_625,
    kozak_ts250_80_2500,
    mcmaster_8681n11,
    mcmaster_90099a030,
    mcmaster_91131a028,
    mcmaster_96659a134,
    mcmaster_98164a527,
)

BRACKETS = {"left": -1, "right": 1}  # Side of the cell, by sign of x.
QR_SIDES = {"left": -1, "right": 1}  # By sign of x.
QR_STATIONS = ("front", "rear")

# Knob seat: the screw's end bottoms in the knob's Ø6.35 bore. Distance from the ball tip to
# the knob's open face, along the screw.
KNOB_FACE_FROM_TIP = (
    KOZAK_TS250_BALL_RADIUS + KOZAK_TS250_END_X - (KOZAK_KB250_OPEN_X - KOZAK_KB250_BORE_BOTTOM_X)
)
STATIONS = {"top": 90.0, "left": 210.0, "right": 330.0}  # Adjuster axes, degrees counterclockwise from +x.


@dataclass(frozen=True)
class MirrorCellParameters:
    # §10.1 plates.
    plate_width: float = 11.5 * INCH
    fixed_plate_height: float = 11.0 * INCH
    fixed_plate_thickness: float = 0.5 * INCH
    base_depth: float = (
        7.0 * INCH
    )  # Trimmed from the rear of an 11.0 in blank to just cover the sliding plate.
    base_thickness: float = 0.5 * INCH
    fixed_plate_rear_from_front: float = (
        4.0 * INCH
    )  # Rear face of the fixed plate, aft of the base front edge.
    moving_plate_thickness: float = 0.75 * INCH
    plate_gap: float = 0.5 * INCH  # Wood face to wood face at the neutral mirror position.
    hex_vertex_diameter: float = 11.0 * INCH  # Before the lower vertex is clipped.
    adjuster_radius: float = 4.75 * INCH
    aperture_diameter: float = 8.125 * INCH
    base_clearance: float = 0.375 * INCH  # Trimmed lower edge of the moving plate above the base top.

    # §10.2-§10.4 holes and sockets.
    bushing_bore: float = 8.0
    fixed_hole_diameter: float = 5 / 16 * INCH
    seat_counterbore_diameter: float = 5 / 8 * INCH  # Forstner cutter.
    seat_counterbore_depth: float = 1 / 32 * INCH
    # Provisional: the cutter is chosen against the measured washer OD (§10.4).
    socket_diametral_clearance: float = 0.2
    socket_depth: float = 1 / 16 * INCH

    # §10.3 springs and seat washers (McMaster 2022N186, 98017A199 catalog values).
    spring_od: float = 0.5 * INCH
    spring_id: float = 0.424 * INCH
    # Visualization only: the catalog gives no coil count. 4.3 turns is the 13 lbf/in rate worked back through the
    # music-wire shear modulus (about 2.3 active coils) plus two closed end coils.
    spring_coils: float = 4.3
    seat_washer_od: float = 0.625 * INCH
    seat_washer_id: float = 0.390 * INCH
    seat_washer_thickness: float = 0.032 * INCH  # Middle of the 0.028-0.036 in range.

    # §10.7 bracket screws pass through the Ø8.33 mm bracket holes; the plywood holes are made the same size.
    bracket_hole_diameter: float = MCMASTER_8681N11_HOLE_DIAMETER

    # §10.9 CAMVATE sliding plate, roughly: the seller's dimensioned image gives the length, 12 mm thickness, and a
    # through slot between the two end camera-screw positions 140 mm apart, and a V-notch in one end; the dovetail
    # section is caliper-measured. Its screw hardware is removed, and its pads and M4 holes are not modeled.
    # Provisional: the notch end (here the rear).
    qr_plate_length: float = 7.0 * INCH
    qr_plate_thickness: float = 12.0
    # Caliper measurements of the dovetail section, approximate: the narrow neck against the base, then a flare out
    # to the full width at the bottom.
    qr_neck_width: float = 1.709 * INCH
    qr_neck_depth: float = 0.162 * INCH
    qr_base_width: float = 1.960 * INCH
    qr_slot_width: float = 6.0
    qr_slot_length: float = 140.0  # Center to center of the slot's rounded ends.
    qr_notch_width: float = 10.0
    qr_notch_depth: float = 4.0

    # §10.9 plate screws: McMaster 92125A196, M4 × 0.7 × 18 mm, 90° flat head (catalog head Ø8 mm), two stations
    # 1.875 in from the nearer plate end and ±0.500 in from the centerline. Provisional: the base's Ø4.5 mm clearance
    # hole, the 0.2 mm the head sits below the surface, and the depth of the tapped holes (drawn at the nominal
    # Ø4 mm thread, not the 3.3 mm tap drill).
    qr_screw_inset: float = 1.875 * INCH
    qr_screw_x: float = 0.5 * INCH
    qr_screw_diameter: float = 4.0
    qr_screw_head_diameter: float = 8.0
    qr_screw_length: float = 18.0  # Overall, under the head's top face.
    qr_clearance_hole: float = 4.5
    qr_head_recess: float = 0.2
    qr_tapped_hole_depth: float = 8.0

    # §10.5 mirror (Skyoptikst D203F1600): the 18 mm thickness is approximate and taken as the edge thickness.
    mirror_diameter: float = 203.0
    mirror_focal_length: float = 1600.0
    mirror_edge_thickness: float = 18.0
    rtv_pad_count: int = 6
    rtv_pad_length: float = 18.0  # Circumferential.
    rtv_pad_depth: float = 7.0  # Axial.

    def bracket_center_x(self, side: int) -> float:
        """x of a bracket, flush with the side edge of the plates."""
        return side * (self.plate_width / 2 - MCMASTER_8681N11_WIDTH / 2)

    def upright_hole_z(self) -> list[float]:
        """Heights above the base top of the bracket's upright-leg holes, which go through the fixed plate."""
        return list(MCMASTER_8681N11_HOLE_OFFSETS)

    def base_hole_y(self) -> list[float]:
        """y of the bracket's base-leg holes, which go through the base plate."""
        return [self.fixed_plate_front_y - offset for offset in MCMASTER_8681N11_HOLE_OFFSETS]

    def qr_screw_positions(self) -> dict[tuple[str, str], tuple[float, float]]:
        """(x, y) of the four plate screws, by (station, side)."""
        ys = {"front": self.qr_screw_inset, "rear": self.qr_plate_length - self.qr_screw_inset}
        return {
            (station, side): (sign * self.qr_screw_x, ys[station])
            for station in QR_STATIONS
            for side, sign in QR_SIDES.items()
        }

    @property
    def qr_countersink_diameter(self) -> float:
        """At the top surface: a 90° countersink that seats the head's top face 0.2 mm below it."""
        return self.qr_screw_head_diameter + 2 * self.qr_head_recess

    @property
    def hex_circumradius(self) -> float:
        return self.hex_vertex_diameter / 2

    @property
    def apothem(self) -> float:
        return self.hex_circumradius * cos(pi / 6)

    @property
    def mirror_center_z(self) -> float:
        return self.base_clearance + self.apothem

    @property
    def fixed_plate_rear_y(self) -> float:
        return self.fixed_plate_rear_from_front

    @property
    def fixed_plate_front_y(self) -> float:
        return self.fixed_plate_rear_y - self.fixed_plate_thickness

    @property
    def moving_plate_rear_y(self) -> float:
        return self.fixed_plate_front_y - self.plate_gap

    @property
    def moving_plate_front_y(self) -> float:
        return self.moving_plate_rear_y - self.moving_plate_thickness

    @property
    def mirror_sag(self) -> float:
        r = self.mirror_diameter / 2
        radius = 2 * self.mirror_focal_length
        return radius - sqrt(radius**2 - r**2)

    @property
    def mirror_front_y(self) -> float:
        """The mirror's back is flush with the rear face of the plate: both rest on the bench during the RTV cure."""
        return self.moving_plate_rear_y - self.mirror_edge_thickness

    @property
    def rtv_gap(self) -> float:
        return (self.aperture_diameter - self.mirror_diameter) / 2

    @property
    def socket_diameter(self) -> float:
        return MCMASTER_91131A028_FEMALE_DIAMETER + self.socket_diametral_clearance

    @property
    def washer_back_y(self) -> float:
        """Flat back of the female washer half, on the socket floor."""
        return self.fixed_plate_rear_y - self.socket_depth

    @property
    def washer_front_y(self) -> float:
        """Flat face of the male washer half, which the knob bears on."""
        return self.washer_back_y + MCMASTER_91131A028_HEIGHT

    @property
    def screw_tip_y(self) -> float:
        return self.washer_front_y - KNOB_FACE_FROM_TIP

    @property
    def spring_wire_diameter(self) -> float:
        return (self.spring_od - self.spring_id) / 2

    @property
    def spring_length(self) -> float:
        """Between the seat washers, which stand slightly proud of their counterbores."""
        proud = self.seat_washer_thickness - self.seat_counterbore_depth
        return self.plate_gap - 2 * proud

    def station_center(self, name: str) -> tuple[float, float]:
        """(x, z) of an adjuster axis."""
        angle = radians(STATIONS[name])
        return self.adjuster_radius * cos(angle), self.mirror_center_z + self.adjuster_radius * sin(angle)

    def validate(self) -> None:
        assert self.moving_plate_front_y > 0, "moving plate must be aft of the base front edge"
        assert self.fixed_plate_rear_y < self.base_depth
        assert self.qr_plate_length <= self.base_depth
        assert self.mirror_center_z + self.hex_circumradius < self.fixed_plate_height
        assert self.aperture_diameter > self.mirror_diameter
        assert self.mirror_edge_thickness <= self.moving_plate_thickness
        assert self.seat_counterbore_depth < self.seat_washer_thickness
        assert self.seat_washer_id > self.bushing_bore
        assert self.socket_depth < self.fixed_plate_thickness - self.seat_counterbore_depth
        assert KOZAK_TB250_LENGTH <= self.moving_plate_thickness


def moving_plate_outline(p: MirrorCellParameters) -> list[tuple[float, float]]:
    """(x, z) vertices of the truncated hexagon, about the mirror center; one vertex up, the lower one clipped."""
    radius, apothem = p.hex_circumradius, p.apothem
    side = apothem  # x of the vertical flats.
    upper, lower = radius / 2, -radius / 2  # z of the side vertices.
    # The two lower flats run from (±side, lower) toward the bottom vertex (0, -radius); clip at z=-apothem.
    chord = side * (radius - apothem) / (radius - radius / 2)
    return [
        (0.0, radius),
        (side, upper),
        (side, lower),
        (chord, -apothem),
        (-chord, -apothem),
        (-side, lower),
        (-side, upper),
    ]


def _plate(outline: list[tuple[float, float]], thickness: float, rear_y: float) -> Part:
    """Extrusion of an (x, z) outline, from rear_y forward (toward -y) by thickness."""
    face = Polygon(*outline, align=None).face()
    if face.normal_at().Z < 0:  # The extrusion goes along the normal, which follows the winding.
        face = -face
    prism = extrude(face, amount=thickness)
    return Pos(0, rear_y, 0) * (Rot(X=90) * prism)


def build_moving_plate(p: MirrorCellParameters | None = None) -> Part:
    p = p or MirrorCellParameters()
    cz = p.mirror_center_z
    outline = [(x, z + cz) for x, z in moving_plate_outline(p)]
    plate = _plate(outline, p.moving_plate_thickness, p.moving_plate_rear_y)
    plate -= y_cylinder(
        p.aperture_diameter,
        0,
        cz,
        p.moving_plate_front_y - 1,
        p.moving_plate_front_y + p.moving_plate_thickness + 1,
    )
    for name in STATIONS:
        x, z = p.station_center(name)
        plate -= y_cylinder(
            p.bushing_bore,
            x,
            z,
            p.moving_plate_front_y - 1,
            p.moving_plate_front_y + p.moving_plate_thickness + 1,
        )
        # Spring seat registration counterbore in the rear face.
        plate -= y_cylinder(
            p.seat_counterbore_diameter,
            x,
            z,
            p.moving_plate_rear_y - p.seat_counterbore_depth,
            p.moving_plate_rear_y + 1,
        )
    return plate


def build_fixed_plate(p: MirrorCellParameters | None = None) -> Part:
    """The cell-adjuster plate: spring-seat counterbores in the front face, spherical-washer sockets in the rear."""
    p = p or MirrorCellParameters()
    half = p.plate_width / 2
    outline = [(-half, 0.0), (half, 0.0), (half, p.fixed_plate_height), (-half, p.fixed_plate_height)]
    plate = _plate(outline, p.fixed_plate_thickness, p.fixed_plate_rear_y)
    for name in STATIONS:
        x, z = p.station_center(name)
        plate -= y_cylinder(
            p.fixed_hole_diameter,
            x,
            z,
            p.fixed_plate_front_y - 1,
            p.fixed_plate_front_y + p.fixed_plate_thickness + 1,
        )
        plate -= y_cylinder(
            p.seat_counterbore_diameter,
            x,
            z,
            p.fixed_plate_front_y - 1,
            p.fixed_plate_front_y + p.seat_counterbore_depth,
        )
        plate -= y_cylinder(p.socket_diameter, x, z, p.washer_back_y, p.washer_back_y + p.socket_depth + 1)
    for side in BRACKETS.values():
        for z in p.upright_hole_z():
            plate -= y_cylinder(
                p.bracket_hole_diameter,
                p.bracket_center_x(side),
                z,
                p.fixed_plate_front_y - 1,
                p.fixed_plate_front_y + p.fixed_plate_thickness + 1,
            )
    return plate


def build_base_plate(p: MirrorCellParameters | None = None) -> Part:
    """The base plate, with the four bracket-screw holes and the four countersunk quick-release screw holes."""
    p = p or MirrorCellParameters()
    plate = box_between(-p.plate_width / 2, p.plate_width / 2, 0, p.base_depth, -p.base_thickness, 0)
    for side in BRACKETS.values():
        for y in p.base_hole_y():
            plate -= z_cylinder(
                p.bracket_hole_diameter, p.bracket_center_x(side), y, -p.base_thickness - 1, 1
            )
    hole_radius, top_radius = p.qr_clearance_hole / 2, p.qr_countersink_diameter / 2
    depth = top_radius - hole_radius  # Of the 90° countersink.
    for x, y in p.qr_screw_positions().values():
        plate -= z_cylinder(2 * hole_radius, x, y, -p.base_thickness - 1, 1)
        # A 90° cone, carried 1 mm above the surface so the cut is clean.
        plate -= z_cone(2 * hole_radius, 2 * top_radius + 2, x, y, -depth, 1)
    return plate


def build_qr_screw(p: MirrorCellParameters | None = None) -> Part:
    """Envelope of an M4 × 18 mm 90° flat-head screw: axis +z, head top face at z=0, shank toward -z."""
    p = p or MirrorCellParameters()
    head_radius, shank_radius = p.qr_screw_head_diameter / 2, p.qr_screw_diameter / 2
    head_depth = head_radius - shank_radius  # The 90° cone down to the shank.
    head = z_cone(2 * shank_radius, 2 * head_radius, 0, 0, -head_depth, 0)
    shank = z_cylinder(2 * shank_radius, 0, 0, -p.qr_screw_length, -head_depth)
    return head + shank


def quick_release_outline(p: MirrorCellParameters) -> list[tuple[float, float]]:
    """(x, z) of the plate's dovetail section: a narrow neck against the base underside, flaring to full width."""
    top = -p.base_thickness
    neck, flare, bottom = p.qr_neck_width / 2, p.qr_base_width / 2, top - p.qr_plate_thickness
    shoulder = top - p.qr_neck_depth
    return [(-neck, top), (neck, top), (neck, shoulder), (flare, bottom), (-flare, bottom), (-neck, shoulder)]


def build_quick_release_plate(p: MirrorCellParameters | None = None) -> Part:
    """The sliding plate under the base: its camera face (slot side) against the underside, front end flush with
    the base's front edge, V-notch at the rear end."""
    p = p or MirrorCellParameters()
    thickness = p.qr_plate_thickness
    center_z = -p.base_thickness - thickness / 2
    plate = _plate(quick_release_outline(p), p.qr_plate_length, p.qr_plate_length)
    slot = centered_box(p.qr_slot_width, p.qr_slot_length, thickness + 2)
    for end in (-1, 1):
        slot += centered_cylinder(p.qr_slot_width, thickness + 2, y=end * p.qr_slot_length / 2)
    plate -= Pos(0, p.qr_plate_length / 2, center_z) * slot
    half = p.qr_notch_width / 2
    notch = Polygon(
        (-half, p.qr_plate_length + 1),
        (half, p.qr_plate_length + 1),
        (0, p.qr_plate_length - p.qr_notch_depth),
        align=None,
    ).face()
    if notch.normal_at().Z < 0:
        notch = -notch
    plate -= Pos(0, 0, center_z - thickness / 2 - 1) * extrude(notch, amount=thickness + 2)
    top = -p.base_thickness
    for x, y in p.qr_screw_positions().values():  # Tapped holes, drawn at the nominal thread diameter.
        plate -= z_cylinder(p.qr_screw_diameter, x, y, top - p.qr_tapped_hole_depth, top + 1)
    return plate


def build_mirror(p: MirrorCellParameters | None = None) -> Part:
    """Concave front toward -y, back flush with the rear face of the moving plate."""
    p = p or MirrorCellParameters()
    front = p.mirror_front_y
    blank = y_cylinder(p.mirror_diameter, 0, p.mirror_center_z, front, front + p.mirror_edge_thickness)
    radius = 2 * p.mirror_focal_length
    center = (0, front + p.mirror_sag - radius, p.mirror_center_z)
    return blank - Pos(*center) * Sphere(radius)


def build_rtv_pad(p: MirrorCellParameters, index: int) -> Part:
    """One pad in the radial gap between mirror edge and aperture, at 360°/count × index from +x."""
    mirror_mid = p.mirror_front_y + p.mirror_edge_thickness / 2  # Pads are centered on the mirror's edge.
    mid_radius = (p.mirror_diameter + p.aperture_diameter) / 4
    # Built about the z axis, then stood on the y axis. The pad is the part of the gap annulus within reach of a
    # block of the pad's length, so its ends follow the mirror edge and the aperture wall.
    depth = p.rtv_pad_depth
    annulus = centered_cylinder(p.aperture_diameter, depth) - centered_cylinder(p.mirror_diameter, depth + 2)
    reach = Rot(Z=360.0 / p.rtv_pad_count * index) * centered_box(
        p.rtv_gap + 2, p.rtv_pad_length, depth, x=mid_radius
    )
    return Pos(0, mirror_mid, p.mirror_center_z) * Rot(X=90) * (annulus & reach)


def build_spring(p: MirrorCellParameters, x: float, y0: float, z: float) -> Part:
    """A plain helix of round wire, axis +y from y0 at (x, z), as long as the spring is when installed.

    An illustration: the turn count is approximate and the ends are not closed and ground.
    """
    wire = p.spring_wire_diameter
    height = p.spring_length - wire  # Length of the wire's centerline.
    path = Helix(pitch=height / p.spring_coils, height=height, radius=(p.spring_od - wire) / 2)
    section = Face(Wire.make_circle(wire / 2, Plane(origin=path.start_point(), z_dir=path.tangent_at(0))))
    coil = Part([Solid.sweep(section, path=path, is_frenet=True)])
    return along_y((x, y0, z)) * (Pos(0, 0, wire / 2) * coil)


def _tube(x: float, y0: float, z: float, outer: float, inner: float, length: float) -> Part:
    return y_cylinder(outer, x, z, y0, y0 + length) - y_cylinder(inner, x, z, y0 - 1, y0 + length + 1)


def _bracket_fasteners(p: MirrorCellParameters, name: str, side: int) -> list[Part]:
    """Screws, washers, and locknuts for one bracket: heads on the bracket, nuts on the far side of the plywood.

    The upright leg's screws point toward +y through the fixed plate, the base leg's toward -z through the base.
    """
    screw, washer = mcmaster_98164a527(), mcmaster_96659a134()
    nut, insert = mcmaster_90099a030()
    x = p.bracket_center_x(side)
    washer_t = MCMASTER_96659A134_THICKNESS
    upright_face = p.fixed_plate_front_y - MCMASTER_8681N11_THICKNESS  # Front face of the upright leg.
    base_face = MCMASTER_8681N11_THICKNESS  # Top face of the base leg.
    stacks = []  # (label, screw seat, washer seat, nut seat), each a Location.
    for i, z in enumerate(p.upright_hole_z(), 1):
        along = Rot(X=90)  # Frame +z -> -y: head toward the front, shank toward +y.
        back = Rot(X=-90)  # Frame +z -> +y: away from the plate's rear face.
        stacks.append(
            (
                f"{name} upright {i}",
                Location((x, upright_face, z)) * along,
                Location((x, p.fixed_plate_rear_y, z)) * back,
                Location((x, p.fixed_plate_rear_y + washer_t, z)) * back,
            )
        )
    for i, y in enumerate(p.base_hole_y(), 1):
        below = Rot(X=180)  # Frame +z -> -z: away from the underside of the base.
        stacks.append(
            (
                f"{name} base {i}",
                Location((x, y, base_face)),
                Location((x, y, -p.base_thickness)) * below,
                Location((x, y, -p.base_thickness - washer_t)) * below,
            )
        )
    parts = []
    for label, screw_loc, washer_loc, nut_loc in stacks:
        parts += [
            labeled(screw, f"Bracket screw {label}", STEEL, screw_loc),
            labeled(washer, f"Bracket washer {label}", BLACK_OXIDE, washer_loc),
            labeled(nut, f"Locknut {label}", STEEL, nut_loc),
            labeled(insert, f"Locknut insert {label}", NYLON, nut_loc),
        ]
    return parts


def build_mirror_cell_assembly(p: MirrorCellParameters | None = None) -> Compound:
    p = p or MirrorCellParameters()
    p.validate()
    children = [
        labeled(build_base_plate(p), "Base plate", PLYWOOD),
        labeled(build_fixed_plate(p), "Cell-adjuster plate", PLYWOOD),
        labeled(build_moving_plate(p), "Moving mirror plate", PLYWOOD),
        labeled(build_mirror(p), "Mirror", MIRROR_GLASS),
        labeled(build_quick_release_plate(p), "Quick-release plate", QR_PLATE_DARK),
    ]
    bracket = mcmaster_8681n11()
    for name, side in BRACKETS.items():
        # Flush with the side edge of the plates; the base leg points forward and the upright leg rises on the
        # fixed plate's front face.
        loc = Location((p.bracket_center_x(side), p.fixed_plate_front_y, 0)) * Rot(Z=180)
        children.append(labeled(bracket, f"Bracket {name}", BRACKET_ALUMINUM, loc))
        children += _bracket_fasteners(p, name, side)
    for i in range(p.rtv_pad_count):
        children.append(labeled(build_rtv_pad(p, i), f"RTV pad {i + 1}", RTV))
    qr_screw = build_qr_screw(p)
    for (station, side), (x, y) in p.qr_screw_positions().items():
        loc = Location((x, y, -p.qr_head_recess))
        children.append(labeled(qr_screw, f"Quick-release screw {station} {side}", STAINLESS, loc))

    screw, ball = kozak_ts250_80_2500()
    bushing, knob = kozak_tb250_80_625(), kozak_kb250_80()
    female, male = mcmaster_91131a028()
    seat_y = {
        "moving": (p.moving_plate_rear_y - p.seat_counterbore_depth, "Spring seat washer (moving plate)"),
        "fixed": (
            p.fixed_plate_front_y - p.seat_washer_thickness + p.seat_counterbore_depth,
            "Spring seat washer (fixed plate)",
        ),
    }
    for name in STATIONS:
        x, z = p.station_center(name)
        children += [
            labeled(screw, f"Adjuster screw {name}", STEEL, Location((x, p.screw_tip_y, z))),
            labeled(ball, f"Adjuster ball {name}", STEEL, Location((x, p.screw_tip_y, z))),
            labeled(
                bushing,
                f"Bushing {name}",
                BUSHING_BRASS,
                Location((x, p.moving_plate_front_y - KOZAK_TB250_FLANGE_THICKNESS, z)),
            ),
            labeled(knob, f"Knob {name}", KNOB_SILVER, Location((x, p.washer_front_y, z))),
            labeled(
                female, f"Spherical washer, female {name}", BLACK_OXIDE, Location((x, p.washer_back_y, z))
            ),
            labeled(male, f"Spherical washer, male {name}", BLACK_OXIDE, Location((x, p.washer_back_y, z))),
        ]
        spring_y0 = p.moving_plate_rear_y + (p.seat_washer_thickness - p.seat_counterbore_depth)
        spring = build_spring(p, x, spring_y0, z)
        children.append(labeled(spring, f"Compression spring {name}", HARDWARE_GRAY))
        for side, (y0, label) in seat_y.items():
            washer = _tube(x, y0, z, p.seat_washer_od, p.seat_washer_id, p.seat_washer_thickness)
            children.append(labeled(washer, f"{label} {name}", HARDWARE_GRAY))
    return assembly("Mirror cell", children)


ADJUSTER_SECTION_RADIUS = 22.0  # Half-width of the zoomed adjuster section about the axis, mm.
ADJUSTER_SECTION_FRONT_MARGIN = 4.0  # Kept ahead of the screw's ball tip, mm.
ADJUSTER_SECTION_REAR_MARGIN = 4.0  # Kept behind the knob's outer end, mm.
ADJUSTER_HARDWARE_LABELS = (
    "Adjuster screw",
    "Adjuster ball",
    "Bushing",
    "Knob",
    "Spherical washer",
    "Compression spring",
    "Spring seat washer",
)
SECTIONED_LABELS = ("Base plate", "Cell-adjuster plate", "Moving mirror plate", "Mirror")


def adjuster_section(cell: Compound, p: MirrorCellParameters, name: str) -> Compound:
    """Exposition view of one adjuster station: its hardware whole, seen through cut-away plywood and mirror.

    The station's hardware is kept entire. The plates and mirror are cut along the vertical plane through the
    axis, dropping the -x half, and to a box about the station, which exposes the hardware where it passes
    through them. Everything else is omitted.
    """
    x, z = p.station_center(name)
    y0 = p.screw_tip_y - ADJUSTER_SECTION_FRONT_MARGIN
    y1 = p.washer_front_y + KOZAK_KB250_LENGTH + ADJUSTER_SECTION_REAR_MARGIN
    r = ADJUSTER_SECTION_RADIUS
    keep = centered_box(r, y1 - y0, 2 * r, x + r / 2, (y0 + y1) / 2, z)
    kept = []
    for leaf in leaves(cell):
        if leaf.label.endswith(f" {name}") and leaf.label.startswith(ADJUSTER_HARDWARE_LABELS):
            kept.append(leaf)
        elif leaf.label in SECTIONED_LABELS:
            piece = leaf & keep
            if piece.solids():
                kept.append(labeled(piece, leaf.label, leaf.color))
    return assembly(f"Adjuster section {name}", kept)

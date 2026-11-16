"""Slit baffle: a printed clamp ring on the stage plate's extended spigot, continuing rearward as a
non-clamping "net" of crossed helical vanes that carries a matte black foil wrap.

Frame: the optical axis is the y axis (x = z = 0), z up, and y = 0 is the SM1RC/M's source-side face, which the
clamp's front face butts; the baffle extends toward -y (the light source). The clamp's split and ears are at +z,
the head's rotation-0 "up", and turn with the head. The slit stage places the baffle in the head frame.

One printed part, printed on end (clamp end down), without supports:

- clamp: a split ring on the spigot's protruding end, one M3 screw through ears at the split, as the rail
  shoe's collar;
- rib: a short solid ring behind the clamp, proud of the outside, the foil's near stop. The slit runs through
  it and opens into the net's first cell, so the net's vanes take the clamp's closing;
- net: crossed helical vanes, six of each hand, added to the ribs with no tube behind them: each vane is a
  triangle in section, its base on the clamp's outside diameter (the foil's seat) and its apex at the bore, swept
  along a helix whose pitch gives 45° at the wall's mid radius. Where the hands cross they simply merge: the
  crossing's top is the patch of the outside cylinder bounded by the four edge helices. The vanes line the bore
  (painted flat black), and the foil wraps the net's outside, between the ribs, matte side in;
- far rib: solid ring that closes the net's end and stops the foil there.
"""

from dataclasses import dataclass
from functools import cache
from math import cos, degrees, pi, radians, sin, sqrt
from typing import cast

from build123d import Compound, Face, Helix, Part, Pos, Rot, Solid, Vector, Wire, sweep

from schlieren.cad import (
    CUT_OVERRUN,
    assembly,
    box_between,
    intersect,
    labeled,
    moved,
    x_cylinder,
    y_cylinder,
    z_hex,
)
from schlieren.hardware import M3_CLEARANCE_DIAMETER, M3_NUT_ACROSS_FLATS, M3_NUT_THICKNESS
from schlieren.palette import METAL, PHOTOFOIL_BLACK, PRINTED_GREEN
from schlieren.standards import NUT_POCKET_ACROSS_FLATS_CLEARANCE, SM1_TUBE_DIAMETER
from schlieren.validation import require_positive_dimensions
from schlieren.vendor_cad import mcmaster_91292a114, mcmaster_91828a211

BAFFLE_LABEL = "Baffle"
BODY_LABEL = "Baffle body"
FOIL_LABEL = "Baffle foil"


@dataclass(frozen=True)
class BaffleParameters:
    # Interface: the stage plate's spigot, extended past the SM1RC/M.
    spigot_diameter: float = SM1_TUBE_DIAMETER
    spigot_bore: float = 24.0
    spigot_extension: float = 12.0  # Spigot end beyond the ring's source face.
    spigot_end_gap: float = 0.5  # Spigot end to where the bore starts to narrow, axial.
    length: float = 81.0  # Ring face to the far end.

    # Clamp, PLA fabrication allowances and geometry, as the rail shoe's collar (fit-test pending).
    clamp_bore_diametral_clearance: float = 0.20
    clamp_wall: float = 2.0
    split_gap: float = 1.5
    nut_ear_thickness: float = 4.5
    screw_ear_thickness: float = 3.5
    screw_height_above_clamp: float = 2.5  # Screw axis above the clamp's outer top.
    ear_height_above_screw: float = 4.5
    screw_clearance_diameter: float = M3_CLEARANCE_DIAMETER
    nut_across_flats: float = M3_NUT_ACROSS_FLATS
    nut_thickness: float = M3_NUT_THICKNESS
    nut_across_flats_clearance: float = NUT_POCKET_ACROSS_FLATS_CLEARANCE
    nut_axial_clearance: float = 0.30

    # Net: vanes in the clamp's bore and outside diameter, which the foil wraps between two ribs.
    rib_length: float = 2.0  # The near rib, behind the clamp.
    rib_height: float = 1.0  # Rib and far-rib radial height above the net's outside.
    vanes_per_hand: int = 6
    vane_width: float = 2.0  # Circumferential, on the outside; the apex is a line along the bore.
    vane_apex_clearance: float = 0.02  # Apex above the bore, so no vane edge lies on the ribs' bore surface.
    far_rib_length: float = 3.0
    foil_thickness: float = 0.1  # One layer, as shown; the wrap may overlap itself.

    # --- clamp -------------------------------------------------------------------------------------------
    @property
    def clamp_bore(self):
        return self.spigot_diameter + self.clamp_bore_diametral_clearance

    @property
    def clamp_diameter(self):
        return self.clamp_bore + 2 * self.clamp_wall

    @property
    def spigot_end_y(self):
        return -self.spigot_extension

    @property
    def shoulder_y(self):
        """The clamp bore's cylindrical end, a little short of the spigot's."""
        return self.spigot_end_y - self.spigot_end_gap

    @property
    def clamp_length(self):
        return -self.shoulder_y

    @property
    def screw_z(self):
        return self.clamp_diameter / 2 + self.screw_height_above_clamp

    @property
    def screw_y(self):
        return self.shoulder_y / 2

    @property
    def ear_top_z(self):
        return self.screw_z + self.ear_height_above_screw

    @property
    def nut_ear_outer_x(self):
        return self.split_gap / 2 + self.nut_ear_thickness

    @property
    def screw_ear_outer_x(self):
        return -(self.split_gap / 2 + self.screw_ear_thickness)

    @property
    def nut_pocket_depth(self):
        return self.nut_thickness + self.nut_axial_clearance

    # --- rib and net ------------------------------------------------------------------------------------
    @property
    def net_diameter(self):
        return self.clamp_diameter

    @property
    def vane_depth(self):
        """The ligaments' radial depth: the clamp's wall."""
        return self.clamp_wall

    @property
    def rib_diameter(self):
        return self.net_diameter + 2 * self.rib_height

    @property
    def rib_back_y(self):
        """The near rib's rear face, where the net begins."""
        return self.shoulder_y - self.rib_length

    @property
    def far_y(self):
        return -self.length

    @property
    def net_end_y(self):
        return self.far_y + self.far_rib_length

    @property
    def net_length(self):
        return self.rib_back_y - self.net_end_y

    @property
    def net_bore(self):
        return self.clamp_bore

    @property
    def mean_radius(self):
        return (self.net_diameter + self.net_bore) / 4

    @property
    def vane_pitch_degrees(self):
        return 360.0 / self.vanes_per_hand

    @property
    def vane_lead(self):
        """Axial advance per turn: 45° to the axis at the mean radius."""
        return 2 * pi * self.mean_radius

    @property
    def node_pitch(self):
        """Axial distance between rows of crossings: a hand's vane turns half a vane pitch."""
        return self.mean_radius * pi / 180 * self.vane_pitch_degrees / 2

    @property
    def node_depths(self):
        """Depths behind the near rib's rear face of the rows of crossings (the first on the rib itself)."""
        return [m * self.node_pitch for m in range(int(self.net_length // self.node_pitch) + 1)]

    @property
    def vane_phase_degrees(self):
        """Azimuth where both hands start at the near rib: the cells (and the slit) lie between them."""
        return self.vane_pitch_degrees / 2

    @property
    def foil_diameter(self):
        return self.net_diameter + 2 * self.foil_thickness

    def validate(self):
        require_positive_dimensions(self)
        if self.clamp_bore <= self.spigot_diameter:
            raise ValueError("Clamp bore must slip over the spigot")
        if (self.rib_diameter - self.foil_diameter) / 2 < 0.5:
            raise ValueError("The ribs must stand clear of the foil wrap")
        chord = self.vane_pitch_degrees * pi / 180 * self.mean_radius  # Vane to vane at the rib face.
        if self.split_gap >= chord - self.vane_width:
            raise ValueError("The slit must open into the net's first cell, narrower than it")
        crotch = self.vane_width / 2 / (self.net_diameter / 2) * self.mean_radius
        if crotch >= self.node_pitch / 2:
            raise ValueError("Each crossing must end before the mid-plane to the next row")
        if self.vane_width >= chord / 2:
            raise ValueError("The vanes must leave cells between them")
        if self.nut_pocket_depth >= self.nut_ear_thickness:
            raise ValueError("Nut pocket must leave an inner ear wall")
        corners = (self.nut_across_flats + self.nut_across_flats_clearance) / sqrt(3) * 2
        if corners > self.clamp_length or corners / 2 > self.ear_height_above_screw + 1.0:
            raise ValueError("Nut pocket must fit within the ear")
        if self.screw_clearance_diameter >= min(self.clamp_length, 2 * self.ear_height_above_screw):
            raise ValueError("Screw hole must fit within the ear")
        if self.net_length <= self.vane_lead / 4:
            raise ValueError("The net is too short for its vanes")


# The vane section's flanks run this far past the outside diameter before the cylinder trims them, and each
# piece is swept this far past its ends before its cell's planes cut it (so every cap lies exactly on a plane).
VANE_FLANK_OVERRUN = 0.5
VANE_SWEEP_OVERRUN = 0.5


def _vane_piece(
    p: BaffleParameters,
    azimuth_degrees: float,
    hand: int,
    depth0: float,
    depth1: float,
    cell: tuple[float, float],
) -> Solid:
    """One vane between two depths behind the near rib's rear face, within an angular cell (degrees).

    The vane's section is a triangle with its apex vane_apex_clearance above the bore and its flanks through two
    points on the outside diameter a vane_width apart; swept along its helix, it is trimmed to the outside
    cylinder (the top face is exact) and cut by the cell: the transverse planes at depth0 and depth1 and the
    axial planes at the cell's azimuths. hand +1 turns the azimuth toward +x going rearward, -1 toward -x;
    `azimuth_degrees` is where the vane would be on the rib's face."""
    r_out, r_apex = p.net_diameter / 2, p.net_bore / 2 + p.vane_apex_clearance
    start = depth0 - VANE_SWEEP_OVERRUN
    a0 = radians(azimuth_degrees) + hand * start / p.mean_radius
    half_arc = p.vane_width / 2 / r_out
    # Local frame: +z along the axis rearward (the helix's), +y up; the section lies in z = 0.
    apex = Vector(r_apex * sin(a0), r_apex * cos(a0), 0)
    corners = []
    for side in (-1, 1):
        through = Vector(r_out * sin(a0 + side * half_arc), r_out * cos(a0 + side * half_arc), 0) - apex
        # The flank, apex + k * through, reaches r_out + VANE_FLANK_OVERRUN.
        a, b = through.dot(through), 2 * apex.dot(through)
        c = apex.dot(apex) - (r_out + VANE_FLANK_OVERRUN) ** 2
        corners.append(apex + through * ((-b + sqrt(b * b - 4 * a * c)) / (2 * a)))
    section = Face(Wire.make_polygon([corners[0], corners[1], apex], close=True))
    path = Helix(p.vane_lead, depth1 + VANE_SWEEP_OVERRUN - start, p.mean_radius, lefthand=hand == 1)
    vane = moved(
        cast(Part, sweep(section, path=path, is_frenet=True)), Pos(0, p.rib_back_y - start, 0) * Rot(X=90)
    )

    y0, y1 = p.rib_back_y - depth0, p.rib_back_y - depth1
    lo, hi = cell
    reach = p.net_diameter  # Beyond the outside diameter.
    outline = [Vector(0, y0, 0)] + [
        Vector(reach * sin(radians(a)), y0, reach * cos(radians(a))) for a in (lo, (lo + hi) / 2, hi)
    ]
    wedge = Solid.extrude(Face(Wire.make_polygon(outline, close=True)), Vector(0, y1 - y0, 0))
    return intersect(vane, intersect(wedge, y_cylinder(p.net_diameter, 0, 0, y1, y0))).solids()[0]


def _crossing(
    p: BaffleParameters, depth: float, azimuth_degrees: float, depth0: float, depth1: float
) -> Solid | Compound:
    """Both hands' vanes around one crossing (at depth, azimuth), between depth0 and depth1, as one solid.

    Around a crossing the union of the two vanes divides exactly along the axial plane through it: behind the
    crossing, the vane turning toward greater azimuth holds everything on that side and the other vane everything
    on the other, and ahead of it the reverse. Each piece is that vane cut to its half-pitch cell, so the pieces
    meet only on planes and the crossing is the vanes' exact union with no vane-to-vane boolean."""
    half = p.vane_pitch_degrees / 2
    turn = degrees(depth / p.mean_radius)
    plus, minus = azimuth_degrees - turn, azimuth_degrees + turn  # Each hand's azimuth on the rib's face.
    pieces = []
    if depth0 < depth:  # Ahead: + on the lesser-azimuth side, - on the greater.
        end = min(depth, depth1)
        pieces += [
            _vane_piece(p, plus, 1, depth0, end, (azimuth_degrees - half, azimuth_degrees)),
            _vane_piece(p, minus, -1, depth0, end, (azimuth_degrees, azimuth_degrees + half)),
        ]
    if depth1 > depth:  # Behind: the reverse.
        begin = max(depth, depth0)
        pieces += [
            _vane_piece(p, plus, 1, begin, depth1, (azimuth_degrees, azimuth_degrees + half)),
            _vane_piece(p, minus, -1, begin, depth1, (azimuth_degrees - half, azimuth_degrees)),
        ]
    return pieces[0].fuse(*pieces[1:])


def _standard_crossing(p: BaffleParameters) -> tuple[Solid | Compound, Solid | Compound]:
    """The crossing unit, from the mid-plane ahead of a crossing to the mid-plane behind it, and the first row's
    half unit (its crossings on the rib's face, so only the part behind them), both for the crossing at depth
    half a node pitch and the vanes' starting azimuth. Every piece's caps are cut by planes, so neighboring
    units' caps coincide exactly on the mid-planes, and every top face lies on the one outside cylinder."""
    mid = p.node_pitch / 2
    azimuth = p.vane_phase_degrees
    return _crossing(p, mid, azimuth, 0.0, 2 * mid), _crossing(p, mid, azimuth, mid, 2 * mid)


def build_net(p: BaffleParameters) -> list[Solid | Compound]:
    """The net as crossing units, each one solid, spanning mid-plane to mid-plane between rows of crossings.

    Units in a row do not touch; neighboring rows meet only on the mid-planes, where each vane is a single cut,
    so the units fuse to one solid cheaply and exactly. Full units are placed copies of one, turned and moved
    along the axis; the first row is the half unit, and units cut short by the far rib are built in place."""
    half, mid = p.vane_pitch_degrees / 2, p.node_pitch / 2
    unit, first = _standard_crossing(p)
    units = []
    for m in range(len(p.node_depths) + 1):  # One more row than the crossings: its leading half may fit.
        depth = m * p.node_pitch
        depth0, depth1 = depth - mid, depth + mid
        if depth0 >= p.net_length:
            break
        if depth1 <= p.net_length:
            placed = moved(first if m == 0 else unit, Pos(0, -(depth - mid), 0) * Rot(Y=half * m))
        else:
            azimuth = p.vane_phase_degrees + half * m
            placed = _crossing(p, depth, azimuth, max(depth0, 0.0), p.net_length)
        units += [moved(placed, Rot(Y=k * p.vane_pitch_degrees)) for k in range(p.vanes_per_hand)]
    return units


@cache
def build_baffle(p: BaffleParameters | None = None) -> Compound:
    """The printed baffle in its own frame (see the module docstring); one valid solid."""
    p = p or BaffleParameters()
    p.validate()
    ear_end = p.shoulder_y
    near = y_cylinder(p.clamp_diameter, 0, 0, p.shoulder_y, 0)
    near += y_cylinder(p.rib_diameter, 0, 0, p.rib_back_y, p.shoulder_y)
    near += box_between(p.split_gap / 2, p.nut_ear_outer_x, ear_end, 0, 0, p.ear_top_z)
    near += box_between(p.screw_ear_outer_x, -p.split_gap / 2, ear_end, 0, 0, p.ear_top_z)
    far = y_cylinder(p.rib_diameter, 0, 0, p.far_y, p.net_end_y)
    bore = y_cylinder(p.clamp_bore, 0, 0, p.far_y - CUT_OVERRUN, CUT_OVERRUN)
    near, far = near - bore, far - bore
    units = build_net(p)
    body = near.fuse(far, *units)
    # The pieces touch only on shared faces, so the union's volume is exactly the sum: a check that the fuse
    # dropped nothing (a failed boolean can return a valid solid with material missing).
    expected = near.volume + far.volume + sum(u.volume for u in units)
    if len(body.solids()) != 1 or not body.is_valid or abs(body.volume - expected) > 1e-5 * expected:
        raise ValueError("Baffle net did not fuse to one valid solid of the expected volume")

    # The slit runs the clamp and near rib and opens into the net's first cell at the top (azimuth 0, between
    # the vanes that start either side of it). It starts inside the bore's air, short of the wall.
    inside_wall = p.net_bore / 4
    body -= box_between(
        -p.split_gap / 2,
        p.split_gap / 2,
        p.rib_back_y - CUT_OVERRUN,
        CUT_OVERRUN,
        inside_wall,
        p.ear_top_z + 1,
    )
    body -= x_cylinder(
        p.screw_clearance_diameter,
        p.screw_y,
        p.screw_z,
        p.screw_ear_outer_x - CUT_OVERRUN,
        p.nut_ear_outer_x + CUT_OVERRUN,
    )
    pocket = z_hex(
        p.nut_across_flats + p.nut_across_flats_clearance,
        0,
        0,
        p.nut_ear_outer_x - p.nut_pocket_depth,
        p.nut_ear_outer_x + CUT_OVERRUN,
    )
    body -= moved(pocket, Pos(0, p.screw_y, p.screw_z) * Rot(Y=90))

    if len(body.solids()) != 1 or not body.is_valid:
        raise ValueError("Baffle did not produce one valid solid")
    return body


@cache
def build_baffle_foil(p: BaffleParameters | None = None) -> Compound:
    """The foil wrap as one layer around the net, between the ribs (shown; the real wrap overlaps itself)."""
    p = p or BaffleParameters()
    p.validate()
    return y_cylinder(p.foil_diameter, 0, 0, p.net_end_y, p.rib_back_y) - y_cylinder(
        p.net_diameter, 0, 0, p.net_end_y - CUT_OVERRUN, p.rib_back_y + CUT_OVERRUN
    )


def clamp_hardware(p: BaffleParameters | None = None) -> list[Part]:
    """The M3 × 12 clamp screw (head on the 3.5 mm ear) and its hex nut seated in the pocket, in the baffle frame."""
    p = p or BaffleParameters()
    along_axis = Pos(0, p.screw_y, p.screw_z) * Rot(Y=90)  # Local +z along +x.
    screw = moved(mcmaster_91292a114(), Pos(0, 0, p.screw_ear_outer_x))
    nut_seat = p.nut_ear_outer_x - p.nut_pocket_depth
    nut = Pos(0, 0, nut_seat) * Rot(Z=90) * mcmaster_91828a211()
    return [
        labeled(screw, "Baffle clamp screw", METAL, along_axis),
        labeled(nut, "Baffle clamp nut", METAL, along_axis),
    ]


def build_baffle_assembly(p: BaffleParameters | None = None) -> Compound:
    """The printed body, the foil wrap, and the clamp screw and nut, in the baffle frame."""
    p = p or BaffleParameters()
    return assembly(
        BAFFLE_LABEL,
        [
            labeled(build_baffle(p), BODY_LABEL, PRINTED_GREEN),
            labeled(build_baffle_foil(p), FOIL_LABEL, PHOTOFOIL_BLACK),
            *clamp_hardware(p),
        ],
    )

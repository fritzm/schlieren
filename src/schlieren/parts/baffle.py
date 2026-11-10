"""Slit baffle (§7.8): a printed clamp ring on the stage plate's extended spigot, continuing rearward as a
non-clamping "net" tube that carries a matte black foil wrap.

Frame: the optical axis is the y axis (x = z = 0), z up, and y = 0 is the SM1RC/M's source-side face, which the
clamp's front face butts; the baffle extends toward -y (the light source). The clamp's split and ears are at +z,
the head's rotation-0 "up", and turn with the head. The slit stage places the baffle in the head frame.

One printed part, printed on end (clamp end down), without supports:

- clamp: a split ring on the spigot's protruding end, one M3 screw through ears at the split, as the rail
  shoe's collar;
- collar: solid ring behind the clamp bore. The slit ends in a round relief hole inside it. A shoulder in the
  bore stops short of the spigot end;
- net: a tube whose wall is cut by staggered diamond windows, so its ligaments run as 45° vanes. The vanes
  stand into the bore (painted flat black), and the foil wraps the net's outside, between the collars, matte
  side in;
- far collar: solid ring that closes the net's end.
"""

from dataclasses import dataclass
from functools import cache
from math import pi, sqrt

from build123d import Compound, Part, Pos, Rot

from schlieren.cad import (
    CUT_OVERRUN,
    assembly,
    box_between,
    centered_box,
    intersect,
    labeled,
    moved,
    x_cylinder,
    y_cylinder,
    z_cylinder,
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
    spigot_end_gap: float = 0.5  # Spigot end to the clamp bore's shoulder, axial.
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
    relief_diameter: float = 3.5
    relief_center_past_bore: float = 2.0  # Relief hole's center behind the clamp bore's shoulder.
    collar_length: float = 4.0

    # Net: outside diameter fixed (the foil wraps it); vane_depth is the ligaments' radial depth into the bore.
    net_diameter: float = 31.0
    vane_depth: float = 3.0
    windows_per_row_pair: int = 3  # Each window cutter passes both walls: twice this many around.
    window_ligament: float = 1.4  # Width of the 45° ligaments between windows, measured on the unrolled tube.
    far_collar_length: float = 3.0
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
        """The clamp bore's end, a little short of the spigot's."""
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

    # --- collar and net ----------------------------------------------------------------------------------
    @property
    def collar_back_y(self):
        return self.shoulder_y - self.collar_length

    @property
    def relief_y(self):
        return self.shoulder_y - self.relief_center_past_bore

    @property
    def far_y(self):
        return -self.length

    @property
    def net_end_y(self):
        return self.far_y + self.far_collar_length

    @property
    def net_length(self):
        return self.collar_back_y - self.net_end_y

    @property
    def net_bore(self):
        return self.net_diameter - 2 * self.vane_depth

    @property
    def window_pitch_degrees(self):
        return 180.0 / self.windows_per_row_pair

    @property
    def row_count(self):
        """Rows of windows, the first and last centered on the collar faces so they are clipped to triangles."""
        mean_radius = (self.net_diameter - self.vane_depth) / 2
        nominal_pitch = mean_radius * pi / (2 * self.windows_per_row_pair)  # Half the circumferential pitch.
        return round(self.net_length / nominal_pitch) + 1

    @property
    def row_pitch(self):
        return self.net_length / (self.row_count - 1)

    @property
    def window_half_diagonal(self):
        """Neighboring windows are offset by (half the window pitch, one row pitch), at 45°."""
        return self.row_pitch - self.window_ligament / sqrt(2)

    @property
    def foil_diameter(self):
        return self.net_diameter + 2 * self.foil_thickness

    def validate(self):
        require_positive_dimensions(self)
        if self.clamp_bore <= self.spigot_diameter:
            raise ValueError("Clamp bore must slip over the spigot")
        if self.net_bore < self.spigot_bore:
            raise ValueError("Net bore must pass the spigot's light bore")
        if self.net_bore >= self.clamp_bore or self.net_diameter >= self.clamp_diameter:
            raise ValueError(
                "The net must be inside the clamp's bore and outside diameter, leaving a shoulder"
            )
        if (self.clamp_diameter - self.foil_diameter) / 2 < 1.0:
            raise ValueError("The collars must stand clear of the foil wrap")
        radius = self.relief_diameter / 2
        if (
            self.relief_center_past_bore - radius < 0.2
            or self.relief_center_past_bore + radius > self.collar_length - 0.2
        ):
            raise ValueError("The relief hole must lie inside the collar, clear of its faces")
        if self.relief_diameter <= self.split_gap:
            raise ValueError("Relief hole must be wider than the split")
        if self.nut_pocket_depth >= self.nut_ear_thickness:
            raise ValueError("Nut pocket must leave an inner ear wall")
        corners = (self.nut_across_flats + self.nut_across_flats_clearance) / sqrt(3) * 2
        if corners > self.clamp_length or corners / 2 > self.ear_height_above_screw + 1.0:
            raise ValueError("Nut pocket must fit within the ear")
        if self.screw_clearance_diameter >= min(self.clamp_length, 2 * self.ear_height_above_screw):
            raise ValueError("Screw hole must fit within the ear")
        if self.window_half_diagonal <= 1.0 or self.row_count < 3:
            raise ValueError("The net needs windows and at least three rows")
        if self.net_length <= 2 * self.row_pitch:
            raise ValueError("The net is too short for its windows")


@cache
def build_baffle(p: BaffleParameters | None = None) -> Compound:
    """The printed baffle in its own frame (see the module docstring); one valid solid."""
    p = p or BaffleParameters()
    p.validate()
    ear_end = p.shoulder_y
    body = y_cylinder(p.clamp_diameter, 0, 0, p.collar_back_y, 0)
    body += y_cylinder(p.net_diameter, 0, 0, p.net_end_y - CUT_OVERRUN, p.collar_back_y + CUT_OVERRUN)
    body += y_cylinder(p.clamp_diameter, 0, 0, p.far_y, p.net_end_y)
    body += box_between(p.split_gap / 2, p.nut_ear_outer_x, ear_end, 0, 0, p.ear_top_z)
    body += box_between(p.screw_ear_outer_x, -p.split_gap / 2, ear_end, 0, 0, p.ear_top_z)
    body -= y_cylinder(p.clamp_bore, 0, 0, p.shoulder_y, CUT_OVERRUN)
    body -= y_cylinder(p.net_bore, 0, 0, p.far_y - CUT_OVERRUN, p.shoulder_y + CUT_OVERRUN)

    # The slit runs the clamp and ends in the round relief hole. Both start inside the bore's air, short of
    # the wall; the hole stays clear of the shoulder plane (a tangent face would make an invalid solid).
    inside_wall = p.net_bore / 4
    body -= box_between(
        -p.split_gap / 2, p.split_gap / 2, p.relief_y, CUT_OVERRUN, inside_wall, p.ear_top_z + 1
    )
    body -= z_cylinder(p.relief_diameter, 0, p.relief_y, inside_wall, p.ear_top_z + 1)
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

    # Windows: diamond prisms drilled radially through both walls, rows staggered by half a window pitch. The
    # end rows are centered on the collar faces and clipped to the net's span, leaving triangles.
    side = 2 * p.window_half_diagonal / sqrt(2)
    prism = moved(centered_box(side, side, p.net_diameter + 2 * CUT_OVERRUN), Rot(Z=45))
    net_span = box_between(
        -p.net_diameter, p.net_diameter, p.net_end_y, p.collar_back_y, -p.net_diameter, p.net_diameter
    )
    cutters = []
    for row in range(p.row_count):
        for k in range(p.windows_per_row_pair):
            azimuth = (k + (row % 2) / 2) * p.window_pitch_degrees
            cutter = moved(prism, Pos(0, p.collar_back_y - row * p.row_pitch, 0) * Rot(Y=azimuth))
            cutters.append(intersect(cutter, net_span) if row in (0, p.row_count - 1) else cutter)
    body -= Compound(cutters)

    if len(body.solids()) != 1 or not body.is_valid:
        raise ValueError("Baffle did not produce one valid solid")
    return body


@cache
def build_baffle_foil(p: BaffleParameters | None = None) -> Compound:
    """The foil wrap as one layer around the net, between the collars (shown; the real wrap overlaps itself)."""
    p = p or BaffleParameters()
    p.validate()
    return y_cylinder(p.foil_diameter, 0, 0, p.net_end_y, p.collar_back_y) - y_cylinder(
        p.net_diameter, 0, 0, p.net_end_y - CUT_OVERRUN, p.collar_back_y + CUT_OVERRUN
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

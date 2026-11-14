"""Sighting reticle for the cutoff post's SM1RC/M ring: a printed tube with a crosshair at each end, used to
center the telephoto's front glass on the optical axis with the cutoff carriage out (design §9.9).

The tube is two identical printed halves that snap together once. It slides into the ring from the front, in
place of the carriage's spigot, and the ring clamps it wherever it is slid to: nothing locates it along the
axis. Sighting through both crosshairs at once puts the eye on the ring's axis, so the glass seen through the
tube can be centered on the cross without parallax. A circle at the glass's diameter is an aid to judging it.

Each half has a crosshair across the end of a short full-wall tube, then two lap arms in place of the rest of
the wall: two opposite outer-shell arms and two opposite inner-shell arms, with a small clearance between the
shells. The other half, turned end for end, brings its outer arms over this half's inner arms and the reverse,
so the wall is whole again and the outside is one flush Ø30.48 mm cylinder (the carriage spigot's SM1 nominal).
A circumferential ridge across each inner arm snaps into a groove in the inner face of the outer arm that
covers it. The ridge's return face is steep, 45 degrees, so the pair is not meant to come apart; the
ring's clamp holds the tube together in any case.

Half frame: the axis is the y axis (x = z = 0) and the crosshair end face is the plane y = 0, which is the print
bed: the half prints hair end down, without supports, and is exported as it prints. Quadrants are in the x-z
plane. The assembly is in the post's frame: the origin is where the post's axis meets the optical axis, y runs
along the rail toward the mirror and z is up, so the rail's top is OPTICAL_HEIGHT below the origin.

**Provisional:** the snap (ridge height, groove depth and clearances, set from a print of one half), the Ø25.5
mm bore, which leaves 1.14 mm shells, and the tube's position along the axis, which the ring's clamp sets by
eye. §9.9 does not describe this part yet.
"""

from dataclasses import dataclass
from functools import cache

from build123d import Axis, Compound, Face, Pos, Rot, Solid, Torus, Vector, Wire

from schlieren.cad import CUT_OVERRUN, assembly, box_between, intersect, labeled, y_cylinder
from schlieren.palette import PRINTED_WHITE
from schlieren.parts.camera_support import LENS_TO_SPLIT_RING
from schlieren.parts.rail_shoe import post_stack
from schlieren.standards import OPTICAL_HEIGHT, SM1_TUBE_DIAMETER
from schlieren.validation import require_positive_dimensions
from schlieren.vendor_cad import SM1RC_M_THICKNESS

HALF_LABEL = "Reticle half"
# The layer grid of the 0.15 mm STRUCTURAL print profile: a first layer of 0.2 mm, then 0.15 mm layers. The
# slicer cuts each layer at its mid-height, so a plane between grid heights prints up to half a layer off. The
# half's axial planes (the arms' roots and tips, the crosshair's top) sit on the grid.
PRINT_FIRST_LAYER = 0.2
PRINT_LAYER_HEIGHT = 0.15
RIDGE_EMBED = 0.1  # Ridge base sunk into the arm so that it fuses to it.
FILLET_INTO_WALL = (
    0.3  # A fin, and the hair strips it is cut to, reach this far into the wall, so that they fuse.
)
GROOVE_LEAD_IN = 0.1  # The groove cutter starts this far inside the lap interface, clear of the arm's face.

# Quadrants in the x-z plane, as (sign of x, sign of z). The arms alternate: a half's outer arms and the other
# half's inner arms share quadrants once the other half is turned end for end about z.
OUTER_QUADRANTS = ((1, 1), (-1, -1))
INNER_QUADRANTS = ((-1, 1), (1, -1))


@dataclass(frozen=True)
class RingReticleParameters:
    tube_diameter: float = SM1_TUBE_DIAMETER  # As the carriage spigot, so the SM1RC/M clamps it the same way.
    # Wide enough to keep the 21.5 mm front glass in view when it is a few mm off center, and thin enough to
    # leave two printed shells a wall each.
    bore: float = 25.5
    # Crosshair end to the arms' roots (full wall), and the arms' length: roots at layer 39 (0.2 + 38 * 0.15), tips
    # at layer 86, both on the layer grid.
    body_length: float = 6.05
    arm_length: float = 6.9
    arm_slack: float = 0.05  # Arm tip to the other half's root face, when snapped.
    lap_radial_clearance: float = 0.1  # Per side of the interface radius between an outer and an inner arm.
    arm_side_clearance: float = 0.10  # Per side of each axis plane, between neighboring arms.
    # Snap: a ridge on each inner arm, a groove in each outer arm.
    ridge_height: float = 0.4  # Above the inner arm's outer face; the arms deflect height - 2 * clearance.
    ridge_return: float = 0.4  # Axial length of the steep face on the root side; 45 degrees at the height.
    ridge_flat: float = 0.6
    ridge_lead: float = 1.2  # Gentle lead-in toward the arm's tip.
    ridge_from_root: float = 3.3  # Root-side foot, from the arm's own root face.
    groove_depth: float = 0.4  # Beyond the outer arm's inner face.
    groove_axial_clearance: float = 0.10  # Per side.
    hair_width: float = 0.5
    hair_layers: int = 4  # Of the print: the first, then three more.
    # A fillet "fin" where each hair meets the bore wall, on the hair's open face only (its other face is flush
    # with the end of the tube): as wide as the hair, rising this far along the wall, parallel to the axis.
    hair_top_fillet_radius: float = 1.0
    circle_diameter: float = 21.5  # The telephoto's front glass (§9.2): an aid for judging centering.
    min_wall_under_groove: float = 0.6
    min_groove_root_margin: float = 0.5

    @property
    def hair_thickness(self):
        """From the crosshair end face, on the layer grid."""
        return PRINT_FIRST_LAYER + (self.hair_layers - 1) * PRINT_LAYER_HEIGHT

    @property
    def outer_radius(self):
        return self.tube_diameter / 2

    @property
    def bore_radius(self):
        return self.bore / 2

    @property
    def interface_radius(self):
        """Mid-wall, where the outer and inner arms meet."""
        return (self.outer_radius + self.bore_radius) / 2

    @property
    def shell_thickness(self):
        """Each arm's radial thickness."""
        return self.outer_radius - self.interface_radius - self.lap_radial_clearance

    @property
    def face_spacing(self):
        """Between the two halves' root faces, snapped."""
        return self.arm_length + self.arm_slack

    @property
    def unit_length(self):
        """The snapped tube, crosshair to crosshair."""
        return 2 * self.body_length + self.face_spacing

    @property
    def ridge_extent(self):
        return self.ridge_return + self.ridge_flat + self.ridge_lead

    @property
    def interference(self):
        """Radial overlap of a ridge with the facing arm's face as the halves slide together; the two arms
        share it."""
        return self.ridge_height - 2 * self.lap_radial_clearance

    @property
    def wall_under_groove(self):
        return self.shell_thickness - self.groove_depth

    @property
    def arm_strain_bound(self):
        """Cantilever bending strain if one straight inner arm took all of the interference at the ridge. An
        upper bound: curved arms are stiffer and the outer arm shares the deflection."""
        reach = self.ridge_from_root + self.ridge_return
        return 3 * self.shell_thickness * self.interference / (2 * reach**2)

    @property
    def groove_root_margin(self):
        """From the root face to the groove's nearest edge (the other half's ridge foot lands there)."""
        mirrored_foot = self.face_spacing - (self.ridge_from_root + self.ridge_extent)
        return mirrored_foot - self.groove_axial_clearance

    def validate(self):
        require_positive_dimensions(self)
        if self.bore >= self.tube_diameter:
            raise ValueError("The bore must be inside the tube")
        if self.circle_diameter >= self.bore:
            raise ValueError("The bore must pass the circle aid")
        clear = self.bore_radius - self.circle_diameter / 2 - self.hair_width
        if self.hair_top_fillet_radius >= clear:
            raise ValueError("The hair fillets must stay clear of the circle aid")
        if self.interference <= 0:
            raise ValueError("The ridge must stand proud of the facing arm")
        if self.ridge_from_root + self.ridge_extent > self.arm_length:
            raise ValueError("The ridge must fit on the arm")
        if self.ridge_return > self.ridge_height:
            raise ValueError("The return face must be at least 45 degrees, to print without support")
        if self.groove_depth <= self.interference:
            raise ValueError("The groove must be deeper than the ridge's interference")
        if self.groove_root_margin < self.min_groove_root_margin:
            raise ValueError("The groove must leave a root margin")
        if self.wall_under_groove < self.min_wall_under_groove:
            raise ValueError("The groove must leave a wall")


def _tube(r_in, r_out, y0, y1):
    return y_cylinder(2 * r_out, 0, 0, y0, y1) - y_cylinder(
        2 * r_in, 0, 0, y0 - CUT_OVERRUN, y1 + CUT_OVERRUN
    )


def _quadrant(p, sx, sz, y0, y1):
    """The box over one quadrant, set back by the side clearance from the axis planes."""
    g = p.arm_side_clearance
    r = p.outer_radius + CUT_OVERRUN
    x0, x1 = sorted((sx * g, sx * r))
    z0, z1 = sorted((sz * g, sz * r))
    return box_between(x0, x1, y0, y1, z0, z1)


def _revolved(points):
    """Solid of revolution about the y axis of the polygon through the (radius, y) points."""
    wire = Wire.make_polygon([Vector(r, y, 0) for r, y in points], close=True)
    return Solid.revolve(Face(wire), 360, Axis.Y)


def _hair_footprint(p, thickness):
    """The crosshair's arms, each as wide as a hair, as a prism standing thickness tall from y = 0."""
    reach = p.bore_radius + FILLET_INTO_WALL
    hair_x = box_between(-reach, reach, 0, thickness, -p.hair_width / 2, p.hair_width / 2)
    hair_z = box_between(-p.hair_width / 2, p.hair_width / 2, 0, thickness, -reach, reach)
    return hair_x + hair_z


def _hair_top_fillets(p):
    """The fins: one-sided fillets on the hairs' open face (y = hair thickness), where each meets the bore wall.
    Each is the concave quarter-round between the face and the wall, cut from a ring to the arm's width."""
    r, h, rb = p.hair_top_fillet_radius, p.hair_thickness, p.bore_radius
    ring = _tube(rb - r, rb + FILLET_INTO_WALL, h - FILLET_INTO_WALL, h + r)
    torus = Pos(0, h + r, 0) * Rot(X=90) * Torus(rb - r, r)  # The round tangent to the face and the wall.
    return intersect(ring - torus, _hair_footprint(p, h + r))


def _ridge_ring(p, root):
    """The ridge as a full ring, to be cut down to its quadrants. Its steep face is on the root side."""
    r_face = p.interface_radius - p.lap_radial_clearance
    top = r_face + p.ridge_height
    s0 = root + p.ridge_from_root
    s1 = s0 + p.ridge_return
    s2 = s1 + p.ridge_flat
    s3 = s2 + p.ridge_lead
    base = r_face - RIDGE_EMBED
    return _revolved([(base, s0), (r_face, s0), (top, s1), (top, s2), (r_face, s3), (base, s3)])


def _groove_ring(p, root):
    """The groove cutter, as a full ring: the other half's ridge, which meets this half turned end for end
    (its steep face toward this half's tip), with clearance and a floor."""
    r_face = p.interface_radius + p.lap_radial_clearance
    floor = r_face + p.groove_depth
    cl = p.groove_axial_clearance
    s0 = p.ridge_from_root
    s1 = s0 + p.ridge_return
    s2 = s1 + p.ridge_flat
    s3 = s2 + p.ridge_lead
    # The other half's positions along its arm, in this half's frame.
    foot_tip, foot_root = p.face_spacing - s0, p.face_spacing - s3
    floor_root = p.face_spacing - s2
    base = r_face - GROOVE_LEAD_IN
    # The steep side keeps its 45 degrees: the floor corner is in from the foot by the groove's depth.
    steep_run = floor - r_face
    return _revolved(
        [
            (base, root + foot_tip + cl),
            (r_face, root + foot_tip + cl),
            (floor, root + foot_tip + cl - steep_run),
            (floor, root + floor_root - cl),
            (r_face, root + foot_root - cl),
            (base, root + foot_root - cl),
        ]
    )


@cache
def build_reticle_half(p: RingReticleParameters | None = None):
    """One half, in its print orientation: crosshair end face on the bed (y = 0), axis up. Print two."""
    p = p or RingReticleParameters()
    p.validate()
    root = p.body_length
    tip = root + p.arm_length
    r_mid = p.interface_radius
    c = p.lap_radial_clearance

    body = _tube(p.bore_radius, p.outer_radius, 0, root)
    outer_ring = _tube(r_mid + c, p.outer_radius, root - CUT_OVERRUN, tip)
    inner_ring = _tube(p.bore_radius, r_mid - c, root - CUT_OVERRUN, tip)
    groove = _groove_ring(p, root)
    ridge = _ridge_ring(p, root)
    for sx, sz in OUTER_QUADRANTS:
        box = _quadrant(p, sx, sz, root - CUT_OVERRUN, tip + CUT_OVERRUN)
        body += intersect(outer_ring, box) - groove
    for sx, sz in INNER_QUADRANTS:
        box = _quadrant(p, sx, sz, root - CUT_OVERRUN, tip + CUT_OVERRUN)
        body += intersect(inner_ring, box) + intersect(ridge, box)

    # Crosshair and circle across the bore, in the end face's plane.
    reach = p.bore_radius + p.hair_width
    hair_x = box_between(-reach, reach, 0, p.hair_thickness, -p.hair_width / 2, p.hair_width / 2)
    hair_z = box_between(-p.hair_width / 2, p.hair_width / 2, 0, p.hair_thickness, -reach, reach)
    circle = y_cylinder(p.circle_diameter + 2 * p.hair_width, 0, 0, 0, p.hair_thickness) - y_cylinder(
        p.circle_diameter, 0, 0, -CUT_OVERRUN, p.hair_thickness + CUT_OVERRUN
    )
    for hair in (hair_x, hair_z, circle):
        body += intersect(hair, y_cylinder(p.tube_diameter, 0, 0, 0, p.hair_thickness))
    body += _hair_top_fillets(p)
    return body.clean()


def snapped_locations(p: RingReticleParameters, y_center: float, axis_z: float = 0.0):
    """Locations of the aft and fore halves, snapped, the tube's midpoint at y_center on the axis at height
    axis_z. The fore half is the same part turned end for end about z, so its outer arms land on the aft
    half's inner arms and its inner arms under the aft half's outer ones."""
    half = p.unit_length / 2
    return Pos(0, y_center - half, axis_z), Pos(0, y_center + half, axis_z) * Rot(Z=180)


def build_ring_reticle(p: RingReticleParameters | None = None) -> Compound:
    """The two halves snapped, as a tube along +y from y = 0 (the aft crosshair) to the unit length."""
    p = p or RingReticleParameters()
    aft, fore = snapped_locations(p, p.unit_length / 2)
    half = build_reticle_half(p)
    return assembly(
        "Ring reticle",
        [
            labeled(half, f"{HALF_LABEL}, aft", PRINTED_WHITE, aft),
            labeled(half, f"{HALF_LABEL}, fore", PRINTED_WHITE, fore),
        ],
    )


def lens_clearance(p: RingReticleParameters, offset: float = 0.0):
    """From the aft crosshair to the lens front, with the tube centered on the ring and moved ahead by offset.
    The lens front stands the assumed LENS_TO_SPLIT_RING behind the ring's rear face (§9.3)."""
    return LENS_TO_SPLIT_RING + SM1RC_M_THICKNESS / 2 - p.unit_length / 2 + offset


def build_ring_reticle_assembly(p: RingReticleParameters | None = None, offset: float = 0.0) -> Compound:
    """The snapped reticle centered in the SM1RC/M ring on its post, with the ring, the post and the rail shoe, in
    the post's frame (origin where the post axis meets the optical axis). offset moves the reticle ahead (+y)
    of the ring's mid-plane, as its position along the axis is free."""
    p = p or RingReticleParameters()
    p.validate()
    aft, fore = snapped_locations(p, offset)
    half = build_reticle_half(p)
    stack = post_stack(
        Pos(0, 0, -OPTICAL_HEIGHT), ring=True, optical_height=OPTICAL_HEIGHT, clamp_hardware=False
    )
    return assembly(
        "Ring reticle in the post's ring",
        [
            labeled(half, f"{HALF_LABEL}, aft", PRINTED_WHITE, aft),
            labeled(half, f"{HALF_LABEL}, fore", PRINTED_WHITE, fore),
            *stack,
        ],
    )

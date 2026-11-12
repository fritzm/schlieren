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
plane. The assembly is in the camera support's frame (y = 0 at the back of the phone, along the rail toward the
mirror, the axis at the optical height), where the lens front and the cutoff post stand.

**Provisional:** the snap (ridge height, groove depth and clearances, set from a print of one half), the Ø25.5
mm bore, which leaves 1.14 mm shells, and the tube's position along the axis, which the ring's clamp sets by
eye. §9.9 does not describe this part yet.
"""

from dataclasses import dataclass
from functools import cache

from build123d import Axis, Compound, Face, Pos, Rot, Solid, Vector, Wire

from schlieren.cad import CUT_OVERRUN, assembly, box_between, intersect, labeled, y_cylinder
from schlieren.palette import PRINTED_WHITE
from schlieren.parts.camera_support import (
    LENS_TO_SPLIT_RING,
    CameraSupportParameters,
    build_camera_support_assembly,
    cutoff_post_station,
)
from schlieren.parts.carriage import CarriageParameters
from schlieren.parts.rail_shoe import post_stack
from schlieren.standards import SM1_TUBE_DIAMETER
from schlieren.validation import require_positive_dimensions
from schlieren.vendor_cad import SM1RC_M_THICKNESS

HALF_LABEL = "Reticle half"
RIDGE_EMBED = 0.1  # Ridge base sunk into the arm so that it fuses to it.
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
    body_length: float = 6.0  # Crosshair end to the arms' roots: full wall.
    arm_length: float = 7.0
    arm_slack: float = 0.1  # Arm tip to the other half's root face, when snapped.
    lap_radial_clearance: float = 0.1  # Per side of the interface radius between an outer and an inner arm.
    arm_side_clearance: float = 0.15  # Per side of each axis plane, between neighboring arms.
    # Snap: a ridge on each inner arm, a groove in each outer arm.
    ridge_height: float = 0.4  # Above the inner arm's outer face; the arms deflect height - 2 * clearance.
    ridge_return: float = 0.4  # Axial length of the steep face on the root side; 45 degrees at the height.
    ridge_flat: float = 0.6
    ridge_lead: float = 1.2  # Gentle lead-in toward the arm's tip.
    ridge_from_root: float = 3.3  # Root-side foot, from the arm's own root face.
    groove_depth: float = 0.4  # Beyond the outer arm's inner face.
    groove_axial_clearance: float = 0.15  # Per side.
    hair_width: float = 0.5
    hair_thickness: float = 0.4  # Two layers.
    circle_diameter: float = 21.5  # The telephoto's front glass (§9.2): an aid for judging centering.
    min_wall_under_groove: float = 0.6
    min_groove_root_margin: float = 0.5

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


def build_ring_reticle_assembly(
    p: RingReticleParameters | None = None, offset: float = 0.0, include_support: bool = True
) -> Compound:
    """The snapped reticle centered in the cutoff post's SM1RC/M ring, in the camera support's frame, moved
    ahead by offset (its position along the axis is free). include_support adds the lens cradle, phone and
    lens, the rail, and the post stack with its ring."""
    p = p or RingReticleParameters()
    p.validate()
    camera = CameraSupportParameters()
    post_y = cutoff_post_station(camera, CarriageParameters())
    aft, fore = snapped_locations(p, post_y + offset, camera.optical_height)
    half = build_reticle_half(p)
    children = [
        labeled(half, f"{HALF_LABEL}, aft", PRINTED_WHITE, aft),
        labeled(half, f"{HALF_LABEL}, fore", PRINTED_WHITE, fore),
    ]
    if include_support:
        children.append(build_camera_support_assembly(camera, include_cutoff=False, side_screws=True))
        children.extend(
            post_stack(y=post_y, ring=True, optical_height=camera.optical_height, side_screws=True)
        )
    return assembly("Ring reticle in the cutoff ring", children)

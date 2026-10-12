"""The iOgrapher proSnap 7x telephoto lens, design §9.2.

Frame: the lens axis is the y axis through the origin, y = 0 is the aft end of the threaded boss, and +y runs
toward the front of the lens (toward the mirror, as mounted). Place it with its axis on the optical axis.

Three sections from the aft end, measured, as one solid:

- the boss: a ring with the 17 mm camera-standard external thread, drawn as a plain cylinder at the
  thread's major diameter. It threads into the phone case's lens mount. A glass optic is inset in the ring
  from the aft end;
- the shoulder: a cylindrical section that seats on the mount, with a small chamfer on its rear outer edge;
- the main barrel, which carries the focus ring, in a circumferential channel, and runs on at the same
  diameter ahead of it to the front face. A fillet rounds its root where it meets the shoulder. The front
  face has a rounded outer edge and steps down in six concentric steps to the front glass.

The focus ring and the two glass optics are separate solids; the ring is a sleeve in the barrel's channel,
flush with the barrel, with raised axial grip ridges.

**Provisional**: the front aperture, glass thicknesses, ridges, and channel (assumed from photographs),
and the ring and lip lengths, which are measured from the front end of the barrel.
"""

from dataclasses import dataclass
from math import pi

from build123d import Part, Rot, chamfer, fillet

from schlieren.cad import CUT_OVERRUN, assembly, box_between, labeled, y_cylinder
from schlieren.palette import FOCUS_RING_GRAY, GLASS, LENS_BLACK
from schlieren.standards import INCH
from schlieren.validation import require_positive_dimensions


@dataclass(frozen=True)
class LensParameters:
    # Measured, §9.2.
    thread_diameter: float = 17.0  # Major diameter of the 17 mm camera-standard thread.
    boss_length: float = 0.10 * INCH
    glass_inset: float = 0.05 * INCH  # Aft end of the boss to the glass optic's aft face.
    boss_ring_width: float = 0.10 * INCH  # Radial, outer to inner edge of the boss ring.
    glass_thickness: float = 2.0  # Assumed.
    shoulder_diameter: float = 1.26 * INCH
    shoulder_length: float = 0.4 * INCH
    barrel_diameter: float = 37.0  # Measured 37.01 to 37.06 mm; the nominal is used.
    barrel_length: float = 4.285 * INCH
    focus_ring_length: float = 0.455 * INCH
    front_lip_length: float = 0.175 * INCH
    # A thin circumferential groove round the main barrel, measured along it from the shoulder.
    barrel_groove_position: float = 1.3 * INCH
    barrel_groove_width: float = 0.3  # Assumed.
    barrel_groove_depth: float = 0.3  # Radial; assumed.
    # Front face: a rounded outer edge, and six concentric steps down to the front glass, which sits in the
    # last one. The opening, the step count, and the edge round are assumed from photographs.
    front_edge_fillet: float = 1.0
    front_aperture_diameter: float = 32.0  # The first step.
    front_glass_diameter: float = 0.82 * INCH  # Measured: the aperture at the bottom of the steps.
    front_step_count: int = 6
    front_staircase_depth: float = 0.335 * INCH  # Measured: the front face to the bottom of the last step.
    front_glass_thickness: float = 3.0
    # Focus ring: flush with the barrel, with raised axial grip ridges. Assumed from the photograph.
    focus_ridge_count: int = 48
    focus_ridge_width: float = 0.9  # Tangential, flat-topped: narrow, with gaps of about 1.5 mm between.
    focus_ridge_height: float = 0.5  # Radial, above the barrel surface.
    focus_channel_depth: float = 1.0  # Radial, the barrel's channel under the ring; the ring's wall. Assumed.
    barrel_root_fillet: float = 2.0  # Shoulder to the barrel's rear face, inside corner; a design choice.
    shoulder_rear_chamfer: float = 0.5  # Equal-leg, on the shoulder's rear outer edge; a design choice.

    def validate(self) -> None:
        require_positive_dimensions(self)
        if self.boss_bore_diameter <= 0:
            raise ValueError("The boss ring must have a wall")
        if self.glass_inset >= self.boss_length:
            raise ValueError("The glass must be inset within the boss ring")
        if self.thread_diameter >= self.shoulder_diameter:
            raise ValueError("The thread boss must be narrower than the shoulder")
        if self.barrel_root_fillet >= (self.barrel_diameter - self.shoulder_diameter) / 2:
            raise ValueError("The root fillet must leave part of the barrel's rear face")
        if self.barrel_root_fillet >= self.shoulder_length:
            raise ValueError("The root fillet must lie on the shoulder")
        if self.shoulder_rear_chamfer >= (self.shoulder_diameter - self.thread_diameter) / 2:
            raise ValueError("The shoulder chamfer must leave part of the shoulder's rear face")
        if self.shoulder_rear_chamfer + self.barrel_root_fillet >= self.shoulder_length:
            raise ValueError("The shoulder chamfer and root fillet must not meet")
        groove_end = self.barrel_start + self.barrel_groove_position + self.barrel_groove_width / 2
        if not self.barrel_start < groove_end < self.focus_ring_start:
            raise ValueError("The barrel groove must lie on the barrel behind the focus ring")
        if not 0 < self.front_glass_diameter < self.front_aperture_diameter < self.barrel_diameter:
            raise ValueError("The front aperture must step down from the barrel face to the glass")
        if self.front_step_count < 2:
            raise ValueError("The front aperture needs at least two steps")
        if self.front_edge_fillet >= (self.barrel_diameter - self.front_aperture_diameter) / 2:
            raise ValueError("The front edge fillet must leave part of the barrel's front face")
        if self.front_glass_depth + self.front_glass_thickness >= self.barrel_length / 2:
            raise ValueError("The front aperture must be shallow in the barrel")
        if self.focus_ridge_count * self.focus_ridge_width >= pi * self.barrel_diameter:
            raise ValueError("The focus ring ridges must leave grooves between them")
        if self.focus_channel_depth >= self.barrel_diameter / 2:
            raise ValueError("The focus ring channel must leave a core in the barrel")
        if self.focus_ring_start <= self.barrel_start:
            raise ValueError("The focus ring must lie on the barrel")

    @property
    def boss_bore_diameter(self) -> float:
        """The boss ring's inside diameter, which the glass fills."""
        return self.thread_diameter - 2 * self.boss_ring_width

    @property
    def bore_depth(self) -> float:
        """From the aft end: the bore, which holds the glass at its bottom."""
        return self.glass_inset + self.glass_thickness

    @property
    def barrel_start(self) -> float:
        """From the aft end: the boss and the shoulder."""
        return self.boss_length + self.shoulder_length

    @property
    def length(self) -> float:
        return self.barrel_start + self.barrel_length

    @property
    def front_glass_depth(self) -> float:
        """From the front face to the glass's front face: the bottom of the last step."""
        return self.front_staircase_depth

    @property
    def front_step_depth(self) -> float:
        """Each step, the steps being equal."""
        return self.front_staircase_depth / self.front_step_count

    def front_step_diameter(self, k: int) -> float:
        """Step k = 0 .. front_step_count - 1, evenly spaced in diameter from the opening to the glass."""
        fraction = k / (self.front_step_count - 1)
        return self.front_aperture_diameter + fraction * (
            self.front_glass_diameter - self.front_aperture_diameter
        )

    @property
    def focus_ring_bore_diameter(self) -> float:
        """The channel floor, which the ring's inside surface meets."""
        return self.barrel_diameter - 2 * self.focus_channel_depth

    @property
    def focus_ring_crest_diameter(self) -> float:
        return self.barrel_diameter + 2 * self.focus_ridge_height

    @property
    def focus_ring_start(self) -> float:
        return self.length - self.front_lip_length - self.focus_ring_length


def build_lens_body(p: LensParameters | None = None) -> Part:
    """Boss, shoulder, and main barrel with its root fillet, one solid on the y axis."""
    p = p or LensParameters()
    p.validate()
    boss = y_cylinder(p.thread_diameter, 0, 0, 0, p.boss_length)
    shoulder = y_cylinder(p.shoulder_diameter, 0, 0, p.boss_length, p.barrel_start)
    barrel = y_cylinder(p.barrel_diameter, 0, 0, p.barrel_start, p.length)
    body = boss + shoulder + barrel
    root = _shoulder_edges(body, p, p.barrel_start)
    body = fillet(root, p.barrel_root_fillet)
    body = chamfer(_shoulder_edges(body, p, p.boss_length), p.shoulder_rear_chamfer)
    body = body - y_cylinder(p.boss_bore_diameter, 0, 0, -CUT_OVERRUN, p.bore_depth)
    # The channel round the barrel that holds the focus ring.
    y0, y1 = p.focus_ring_start, p.focus_ring_start + p.focus_ring_length
    outer = y_cylinder(p.barrel_diameter + 2 * CUT_OVERRUN, 0, 0, y0, y1)
    body = body - (outer - y_cylinder(p.focus_ring_bore_diameter, 0, 0, y0, y1))
    # The thin groove round the barrel.
    groove_y = p.barrel_start + p.barrel_groove_position
    groove_y0, groove_y1 = groove_y - p.barrel_groove_width / 2, groove_y + p.barrel_groove_width / 2
    ring = y_cylinder(p.barrel_diameter + 2 * CUT_OVERRUN, 0, 0, groove_y0, groove_y1)
    floor = y_cylinder(p.barrel_diameter - 2 * p.barrel_groove_depth, 0, 0, groove_y0, groove_y1)
    body = body - (ring - floor)
    # The front face's outer edge rounded, and the concentric steps.
    body = fillet(_circular_edges(body, p.length, p.barrel_diameter), p.front_edge_fillet)
    for k in range(p.front_step_count):
        diameter = p.front_step_diameter(k)
        depth = (k + 1) * p.front_step_depth
        body = body - y_cylinder(diameter, 0, 0, p.length - depth, p.length + CUT_OVERRUN)
    # The seat below the bottom step, which the glass fills.
    face = p.length - p.front_glass_depth
    return body - y_cylinder(p.front_glass_diameter, 0, 0, face - p.front_glass_thickness, face)


def _circular_edges(body: Part, y: float, diameter: float) -> list:
    """The circular edges of the given diameter lying in the plane y."""
    return [
        edge
        for edge in body.edges()
        if abs(edge.bounding_box().min.Y - y) < 1e-6 and abs(edge.bounding_box().size.X - diameter) < 1e-6
    ]


def _shoulder_edges(body: Part, p: LensParameters, y: float) -> list:
    """The circular edges of the shoulder's diameter lying in the plane y."""
    return _circular_edges(body, y, p.shoulder_diameter)


def build_focus_ring(p: LensParameters | None = None) -> Part:
    """The focus ring: a sleeve in the barrel's channel, flush with the barrel, with the grip ridges standing
    on it, one solid."""
    p = p or LensParameters()
    p.validate()
    y0, y1 = p.focus_ring_start, p.focus_ring_start + p.focus_ring_length
    ring = y_cylinder(p.barrel_diameter, 0, 0, y0, y1) - y_cylinder(p.focus_ring_bore_diameter, 0, 0, y0, y1)
    half = p.focus_ridge_width / 2
    # Each ridge stands from inside the sleeve wall, so that it fuses with it, to its crest on the +z side.
    ridge = box_between(
        -half,
        half,
        y0,
        y1,
        p.barrel_diameter / 2 - p.focus_channel_depth / 2,
        p.focus_ring_crest_diameter / 2,
    )
    for k in range(p.focus_ridge_count):
        ring = ring + Rot(Y=k * 360 / p.focus_ridge_count) * ridge
    return ring


def build_glass(p: LensParameters | None = None) -> Part:
    """The glass optic filling the boss ring's bore, its aft face inset from the end of the ring."""
    p = p or LensParameters()
    p.validate()
    return y_cylinder(p.boss_bore_diameter, 0, 0, p.glass_inset, p.bore_depth)


def build_front_glass(p: LensParameters | None = None) -> Part:
    """The front glass element, below the bottom step: its front face is the step's floor."""
    p = p or LensParameters()
    p.validate()
    face = p.length - p.front_glass_depth
    return y_cylinder(p.front_glass_diameter, 0, 0, face - p.front_glass_thickness, face)


def build_lens(p: LensParameters | None = None):
    """The lens as an assembly: body, focus ring, and the rear and front glass."""
    p = p or LensParameters()
    return assembly(
        "Telephoto lens",
        [
            labeled(build_lens_body(p), "Lens body", LENS_BLACK),
            labeled(build_focus_ring(p), "Focus ring", FOCUS_RING_GRAY),
            labeled(build_glass(p), "Lens glass", GLASS),
            labeled(build_front_glass(p), "Front glass", GLASS),
        ],
    )

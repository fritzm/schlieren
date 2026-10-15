"""The cased iPhone 17, design §9.1.

Frame: the §3.4 imaging-rail frame the phone is held in. The origin is the Main camera axis on the back
plane of the cased phone (y = 0, where the lens seats); +x runs along the phone's length away from the near
short edge, +y toward the mirror (out of the back), and z is up, across the phone's width, with the camera
27 mm from the upper long edge and the buttons' side below. So the phone is in landscape, screen aft, camera
end toward the optical axis, as held in §9.1.

Three solids:

- the bare phone, from Apple's drawing (docs/reference/Apple-iPhone-17.pdf): the outline with the drawing's
  corner profile, the rounded glass edges, the camera plateau with its base fillet, the side button, and the action and volume
  buttons. The Camera Control and the SIM tray are flush with the edge and have no geometry;
- the camera glass: the two rings standing on the plateau;
- the case, an OtterBox Commuter. Its outside is the measured length, width, and thickness. The inside is
  the bare phone, the back and front openings and the camera lip are assumed: OtterBox publishes no drawing.

**Provisional**: the case's inside geometry (back thickness, camera lip, opening corners) and the depth of the
camera glass under the lip, which the measured front rim fixes.
"""

import math
from dataclasses import dataclass
from functools import cache

from build123d import Axis, Edge, Face, Part, Plane, Pos, SlotOverall, Vector, Wire, extrude, fillet, sweep

from schlieren.cad import CUT_OVERRUN, assembly, box_between, labeled, y_cylinder
from schlieren.palette import LENS_BLACK, PHONE_BODY, PHONE_CASE
from schlieren.standards import INCH
from schlieren.validation import require_positive_dimensions

# Apple's corner profile (Detail A, all four corners): distance along one edge from the corner of the
# bounding rectangle, and across it, for points from one edge's tangent to the other's.
CORNER_PROFILE = (
    (19.23, 0.00),
    (14.53, 0.02),
    (9.87, 0.48),
    (5.56, 2.26),
    (2.26, 5.56),
    (0.48, 9.87),
    (0.02, 14.53),
    (0.00, 19.23),
)


@dataclass(frozen=True)
class ButtonSpec:
    """A button on a long edge, from Apple's side views (centered on the edge's thickness)."""

    label: str
    center: float  # From the top short edge, along the length.
    length: float
    width: float  # Across the thickness of the phone.
    protrusion: float  # Past the edge.
    upper_edge: bool  # The camera's long edge (the side button and Camera Control); else the other.


BUTTONS = (
    ButtonSpec("Side button", 55.32, 2 * 8.85, 2.66, 0.45, upper_edge=True),
    ButtonSpec("Camera Control", 98.20, 2 * 8.55, 3.03, 0.0, upper_edge=True),
    ButtonSpec("Action button", 34.08, 2 * 3.45, 2.66, 0.45, upper_edge=False),
    ButtonSpec("Volume up", 48.23, 2 * 5.60, 2.66, 0.45, upper_edge=False),
    ButtonSpec("Volume down", 62.43, 2 * 5.60, 2.66, 0.45, upper_edge=False),
)


@dataclass(frozen=True)
class PhoneParameters:
    # Bare phone, Apple's drawing. Lengths along the portrait phone's height from the top short edge are v;
    # across its width from the long edge the camera is nearer, u.
    length: float = 149.61
    width: float = 71.45
    thickness: float = 7.95
    edge_fillet: float = 1.27  # The glass edge's inset from the flat side (Detail B).
    camera_from_long_edge: float = 13.62  # u of both rear cameras.
    main_camera_from_end: float = 31.34  # v of the Main camera (rear camera 2).
    ultra_wide_from_end: float = 13.62  # v of the Ultra Wide (rear camera 1).
    camera_ring_diameter: float = 16.0  # Camera glass ring (2X Ø16.00); the rings stand clear of each other.
    plateau_height: float = 1.78  # Above the back glass.
    camera_glass_height: float = 3.45  # Above the back glass.
    # The plateau's top face, and the foot of the concave fillet that blends it into the back glass.
    plateau_u: tuple[float, float] = (3.79, 23.45)
    plateau_v: tuple[float, float] = (3.97, 40.99)
    plateau_foot_u: tuple[float, float] = (1.18, 26.06)
    plateau_foot_v: tuple[float, float] = (1.34, 43.62)
    flash_u: float = 30.41
    flash_v: float = 22.48
    flash_diameter: float = 6.28

    # Measured in the case, §9.1.
    camera_height_above_edge: float = 60.6  # Main camera above the lower long edge.
    camera_inset_from_end: float = 34.3  # Main camera from the near short edge.
    cased_thickness: float = 0.510 * INCH

    # Case. The front rim stands this far proud of the screen (measured); the back plate's inside is
    # whatever thickness that leaves, which puts the camera glass under the camera lip (assumed).
    front_rim_height: float = 0.050 * INCH
    case_corner_radius: float = 12.0
    case_edge_fillet: float = 2.0
    case_rim_fillet: float = 1.2  # Round of the front rim's inner edge; the 1.27 mm rim height limits it.
    case_front_lip_width: float = 2.5  # Of the front rim over the screen edge.
    # The camera opening: measured, except the corner radius. Centered on the plateau along the length.
    camera_opening_length: float = 1.585 * INCH  # Along the long edges.
    camera_opening_width: float = 1.35 * INCH  # Along the short edges.
    camera_opening_setback: float = 0.180 * INCH  # From the case's camera-side long edge to the opening.
    camera_opening_corner_radius: float = 12.0  # Assumed.

    def validate(self) -> None:
        require_positive_dimensions(self)
        if self.camera_glass_recess <= 0:
            raise ValueError("The case must leave the camera glass under the camera lip")
        if self.case_side_wall <= 0 or self.case_end_wall <= 0:
            raise ValueError("The measured camera position must leave a case wall")

    @property
    def plateau_fillet_width(self) -> float:
        """How far the fillet reaches out from the plateau top, along the back glass."""
        return self.plateau_u[0] - self.plateau_foot_u[0]

    @property
    def case_side_wall(self) -> float:
        """Case wall on the long edges, from the measured camera height (assumed equal on both)."""
        return self.camera_height_above_edge - (self.width - self.camera_from_long_edge)

    @property
    def case_end_wall(self) -> float:
        """Case wall on the short edges, from the measured camera inset (assumed equal on both)."""
        return self.camera_inset_from_end - self.main_camera_from_end

    @property
    def cased_length(self) -> float:
        return self.length + 2 * self.case_end_wall

    @property
    def cased_width(self) -> float:
        return self.width + 2 * self.case_side_wall

    @property
    def back_glass_y(self) -> float:
        """The bare phone's back glass: its front sits the rim height under the case front."""
        return self.front_glass_y + self.thickness

    @property
    def front_glass_y(self) -> float:
        return self.front_rim_height - self.cased_thickness

    @property
    def camera_glass_recess(self) -> float:
        """How far the camera glass stands under the camera lip, whose top is the back plane."""
        return -(self.back_glass_y + self.camera_glass_height)

    @property
    def x_near(self) -> float:
        """The bare phone's near short edge."""
        return -self.main_camera_from_end

    @property
    def z_upper(self) -> float:
        """The bare phone's long edge nearer the camera."""
        return self.camera_from_long_edge

    @property
    def z_lower(self) -> float:
        return self.camera_from_long_edge - self.width

    def x_of(self, v: float) -> float:
        return v - self.main_camera_from_end

    def z_of(self, u: float) -> float:
        return self.camera_from_long_edge - u


def _bare_outline(p: PhoneParameters, y: float) -> Face:
    """The bare phone's outline in the plane y, with Apple's corner profile at all four corners."""
    x0, x1 = p.x_near, p.x_near + p.length
    z0, z1 = p.z_lower, p.z_upper
    corners = (  # In order round the outline: corner, inward signs along x and z, and the traversal order.
        (x1, z0, -1, 1, False),
        (x1, z1, -1, -1, True),
        (x0, z1, 1, -1, False),
        (x0, z0, 1, 1, True),
    )
    edges: list[Edge] = []
    previous = None
    for cx, cz, sx, sz, reverse in corners:
        points = [Vector(cx + sx * a, y, cz + sz * b) for a, b in CORNER_PROFILE]
        if reverse:
            points.reverse()
        if previous is not None:
            edges.append(Edge.make_line(previous, points[0]))
        edges.append(Edge.make_spline(points))
        previous = points[-1]
    first = edges[0].start_point()
    edges.append(Edge.make_line(previous, first))
    return Face(Wire(edges))


def _edge_loops(solid: Part, y_planes: tuple[float, float]) -> list[Edge]:
    """The edges of the solid that lie in either of the y planes."""
    found = []
    for edge in solid.edges():
        box = edge.bounding_box()
        if box.size.Y < 1e-6 and any(abs(box.min.Y - y) < 1e-6 for y in y_planes):
            found.append(edge)
    return found


def _plate_plane(y: float) -> Plane:
    """Plane at y with local x along +x and local y along +z; its normal points toward -y (the screen)."""
    return Plane(origin=(0, y, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))


def _plateau(p: PhoneParameters, y_low: float, y_high: float, grow: float = 0.0) -> Part:
    """The camera plateau stadium, grown radially by grow, between the planes y_low and y_high."""
    x0, x1 = p.x_of(p.plateau_v[0]), p.x_of(p.plateau_v[1])
    z0, z1 = p.z_of(p.plateau_u[1]), p.z_of(p.plateau_u[0])
    center = Pos((x0 + x1) / 2, (z0 + z1) / 2)
    sketch = _plate_plane(y_low) * center * SlotOverall(x1 - x0 + 2 * grow, z1 - z0 + 2 * grow)
    return extrude(sketch, amount=-(y_high - y_low))  # The sketch's normal is -y.


def _camera_centers(p: PhoneParameters) -> tuple[tuple[float, float], tuple[float, float]]:
    z = p.z_of(p.camera_from_long_edge)
    return (p.x_of(p.main_camera_from_end), z), (p.x_of(p.ultra_wide_from_end), z)


def _button(p: PhoneParameters, spec: ButtonSpec) -> Part:
    """A protruding button as a stadium in the edge's plane, embedded 1 mm in the housing."""
    x = p.x_of(spec.center)
    y = p.back_glass_y - p.thickness / 2
    edge = p.z_upper if spec.upper_edge else p.z_lower
    outward = 1 if spec.upper_edge else -1
    z0, z1 = sorted((edge - outward * 1.0, edge + outward * spec.protrusion))
    box = box_between(
        x - spec.length / 2, x + spec.length / 2, y - spec.width / 2, y + spec.width / 2, z0, z1
    )
    return fillet(box.edges().filter_by(Axis.Z), spec.width / 2 - 0.05)


def _filleted_plateau(p: PhoneParameters) -> Part:
    """The plateau with its concave fillet, clipped to the body's outline.

    The fillet is a circular arc tangent to the back glass at the foot and meeting the top face at the
    drawing's inset, swept round the plateau's outline. The foot sits within the glass edge's round on two
    sides, so the sweep is trimmed to the outline.
    """
    y_glass = p.back_glass_y
    y_top = y_glass + p.plateau_height
    width, height = p.plateau_fillet_width, p.plateau_height
    radius = (width**2 + height**2) / (2 * height)
    x0, x1 = p.x_of(p.plateau_v[0]), p.x_of(p.plateau_v[1])
    z0, z1 = p.z_of(p.plateau_u[1]), p.z_of(p.plateau_u[0])
    path = (_plate_plane(y_glass) * Pos((x0 + x1) / 2, (z0 + z1) / 2) * SlotOverall(x1 - x0, z1 - z0)).face()
    # Section at the middle of the long side nearer the camera's edge, in (z outward, y) about the top edge.
    xc, overlap = (x0 + x1) / 2, 0.2
    start = math.atan2(-radius, 0.0)  # Foot: straight below the arc's center.
    end = math.atan2(height - radius, -width)
    mid = (start + end) / 2
    center = (z1 + width, y_glass + radius)  # (z, y)

    def point(z: float, y: float) -> Vector:
        return Vector(xc, y, z)

    middle = point(center[0] + radius * math.cos(mid), center[1] + radius * math.sin(mid))
    section = Face(
        Wire(
            [
                Edge.make_line(point(z1 - overlap, y_glass), point(z1 + width, y_glass)),
                Edge.make_three_point_arc(point(z1 + width, y_glass), middle, point(z1, y_top)),
                Edge.make_line(point(z1, y_top), point(z1 - overlap, y_top)),
                Edge.make_line(point(z1 - overlap, y_top), point(z1 - overlap, y_glass)),
            ]
        )
    )
    blend = sweep(section, path=path.outer_wire())
    plateau = _plateau(p, y_glass, y_top) + blend
    outline = extrude(
        _bare_outline(p, y_glass - CUT_OVERRUN),
        amount=p.plateau_height + 2 * CUT_OVERRUN,
        dir=Vector(0, 1, 0),
    )
    return plateau & outline


# Built once per parameter set and shared (see parts/carriage.py); the cached solids must not be modified.
@cache
def build_bare_phone(p: PhoneParameters | None = None) -> Part:
    """Housing with glass edges, camera plateau, and the protruding buttons, one solid."""
    p = p or PhoneParameters()
    p.validate()
    body = extrude(_bare_outline(p, p.back_glass_y), amount=p.thickness, dir=Vector(0, -1, 0))
    body = fillet(_edge_loops(body, (p.back_glass_y, p.front_glass_y)), p.edge_fillet)
    body = body + _filleted_plateau(p)
    for spec in BUTTONS:
        if spec.protrusion > 0:
            body = body + _button(p, spec)
    return body


@cache
def build_camera_glass(p: PhoneParameters | None = None) -> Part:
    """The two camera glass rings, on top of the plateau."""
    p = p or PhoneParameters()
    y0 = p.back_glass_y + p.plateau_height
    y1 = p.back_glass_y + p.camera_glass_height
    rings = [y_cylinder(p.camera_ring_diameter, x, z, y0, y1) for x, z in _camera_centers(p)]
    return rings[0] + rings[1]


@cache
def build_case(p: PhoneParameters | None = None) -> Part:
    """The case: a shell round the bare phone with the front window and camera opening."""
    p = p or PhoneParameters()
    p.validate()
    x0, x1 = p.x_near - p.case_end_wall, p.x_near + p.length + p.case_end_wall
    z0, z1 = p.z_lower - p.case_side_wall, p.z_upper + p.case_side_wall
    y_front = -p.cased_thickness
    shell = box_between(x0, x1, y_front, 0.0, z0, z1)
    shell = fillet(shell.edges().filter_by(Axis.Y), p.case_corner_radius)
    shell = fillet(_edge_loops(shell, (y_front, 0.0)), p.case_edge_fillet)
    shell = shell - build_bare_phone(p)
    # Front window: the screen, inside the rim.
    lip = p.case_front_lip_width
    window = box_between(
        p.x_near + lip,
        p.x_near + p.length - lip,
        y_front - CUT_OVERRUN,
        p.front_glass_y + p.thickness / 2,
        p.z_lower + lip,
        p.z_upper - lip,
    )
    shell = shell - fillet(window.edges().filter_by(Axis.Y), p.case_corner_radius - p.case_side_wall - lip)
    rim = [  # The rim's inner edge, not the outer edge's flat boundary.
        e
        for e in _edge_loops(shell, (y_front,))
        if p.x_near + lip - 1e-6 < e.bounding_box().min.X
        and p.x_near + p.length - lip + 1e-6 > e.bounding_box().max.X
    ]
    shell = fillet(rim, p.case_rim_fillet)
    # Back: the camera opening, which also clears the flash.
    xc = (p.x_of(p.plateau_v[0]) + p.x_of(p.plateau_v[1])) / 2
    z_hi = z1 - p.camera_opening_setback
    opening = box_between(
        xc - p.camera_opening_length / 2,
        xc + p.camera_opening_length / 2,
        p.back_glass_y - CUT_OVERRUN,
        CUT_OVERRUN,
        z_hi - p.camera_opening_width,
        z_hi,
    )
    cutout = fillet(opening.edges().filter_by(Axis.Y), p.camera_opening_corner_radius)
    return shell - cutout


def build_phone(p: PhoneParameters | None = None):
    """The cased phone as an assembly: case, bare phone, camera glass."""
    p = p or PhoneParameters()
    return assembly(
        "Phone",
        [
            labeled(build_case(p), "Case", PHONE_CASE),
            labeled(build_bare_phone(p), "Bare phone", PHONE_BODY),
            labeled(build_camera_glass(p), "Camera glass", LENS_BLACK),
        ],
    )

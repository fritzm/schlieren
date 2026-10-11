"""The cased iPhone 17, design §9.1.

Frame: the §3.4 imaging-rail frame the phone is held in. The origin is the Main camera axis on the back
plane of the cased phone (y = 0, where the lens seats); +x runs along the phone's length away from the near
short edge, +y toward the mirror (out of the back), and z is up, across the phone's width, with the camera
27 mm from the upper long edge and the buttons' side below. So the phone is in landscape, screen aft, camera
end toward the optical axis, as held in §9.1.

Three solids:

- the bare phone, from Apple's drawing (docs/reference/Apple-iPhone-17.pdf): the outline with the drawing's
  corner profile, the rounded glass edges, the camera plateau, the side button, and the action and volume
  buttons. The Camera Control and the SIM tray are flush with the edge and have no geometry;
- the camera glass: the two rings standing on the plateau;
- the case, an OtterBox Commuter. Its outside is the measured length, width, and thickness. The inside is
  the bare phone, the back and front openings and the camera lip are assumed: OtterBox publishes no drawing.

**Provisional**: the case's inside geometry (back thickness, camera lip, openings) and the depth of the
camera glass under the lip, which fixes where the bare phone sits in the case.
"""

from dataclasses import dataclass

from build123d import Axis, Edge, Face, Part, Plane, Pos, SlotOverall, Vector, Wire, extrude, fillet

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
    camera_ring_diameter: float = 19.3  # Camera glass ring, from the 3.97 and 40.99 mm extents.
    plateau_height: float = 1.78  # Above the back glass.
    camera_glass_height: float = 3.45  # Above the back glass.
    plateau_u: tuple[float, float] = (1.18, 26.06)
    plateau_v: tuple[float, float] = (1.34, 43.62)
    flash_u: float = 30.41
    flash_v: float = 22.48
    flash_diameter: float = 6.28

    # Measured in the case, §9.1.
    camera_height_above_edge: float = 60.6  # Main camera above the lower long edge.
    camera_inset_from_end: float = 34.3  # Main camera from the near short edge.
    cased_thickness: float = 0.510 * INCH

    # Case, assumed. The camera glass stands this far under the camera lip, whose top is the back plane.
    camera_glass_recess: float = 1.0
    case_corner_radius: float = 12.0
    case_edge_fillet: float = 2.0
    case_front_lip_width: float = 2.5  # Of the front rim over the screen edge.
    camera_cutout_clearance: float = 1.0  # Radial, round the plateau.
    flash_hole_clearance: float = 0.5  # Radial.

    def validate(self) -> None:
        require_positive_dimensions(self)
        if self.front_lip_height <= 0:
            raise ValueError("The case must leave a front lip over the screen")
        if self.case_side_wall <= 0 or self.case_end_wall <= 0:
            raise ValueError("The measured camera position must leave a case wall")

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
        """The bare phone's back glass, under the back plane by the camera glass height and its recess."""
        return -(self.camera_glass_height + self.camera_glass_recess)

    @property
    def front_glass_y(self) -> float:
        return self.back_glass_y - self.thickness

    @property
    def front_lip_height(self) -> float:
        """The case front above the screen."""
        return self.cased_thickness + self.front_glass_y

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


def build_bare_phone(p: PhoneParameters | None = None) -> Part:
    """Housing with glass edges, camera plateau, and the protruding buttons, one solid."""
    p = p or PhoneParameters()
    p.validate()
    body = extrude(_bare_outline(p, p.back_glass_y), amount=p.thickness, dir=Vector(0, -1, 0))
    body = fillet(_edge_loops(body, (p.back_glass_y, p.front_glass_y)), p.edge_fillet)
    body = body + _plateau(p, p.back_glass_y, p.back_glass_y + p.plateau_height)
    for spec in BUTTONS:
        if spec.protrusion > 0:
            body = body + _button(p, spec)
    return body


def build_camera_glass(p: PhoneParameters | None = None) -> Part:
    """The two camera glass rings, on top of the plateau."""
    p = p or PhoneParameters()
    y0 = p.back_glass_y + p.plateau_height
    y1 = p.back_glass_y + p.camera_glass_height
    rings = [y_cylinder(p.camera_ring_diameter, x, z, y0, y1) for x, z in _camera_centers(p)]
    return rings[0] + rings[1]


def build_case(p: PhoneParameters | None = None) -> Part:
    """The case: a shell round the bare phone with the front window, camera cutout, and flash hole."""
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
    # Back: the camera opening round the plateau, and the flash hole.
    cutout = _plateau(
        p,
        p.back_glass_y - CUT_OVERRUN,
        CUT_OVERRUN,
        grow=p.camera_cutout_clearance,
    )
    flash = y_cylinder(
        p.flash_diameter + 2 * p.flash_hole_clearance,
        p.x_of(p.flash_v),
        p.z_of(p.flash_u),
        p.back_glass_y - CUT_OVERRUN,
        CUT_OVERRUN,
    )
    return shell - cutout - flash


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

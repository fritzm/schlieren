"""The cased iPhone 17, design §9.1.

Frame: the §3.4 imaging-rail frame the phone is held in. The origin is the Main camera axis on the back plane
of the cased phone (y = 0): the top of the camera cover, which the lens aft end seats against; +x runs along
the phone's length away from the near short edge, +y toward the mirror (out of the back), and z is up, across
the phone's width, with the camera 27 mm from the upper long edge and the buttons' side below. So the phone is
in landscape, screen aft, camera end toward the optical axis, as held in §9.1.

Three solids, and the assembly draws the flash and the camera glass rings in their own colors:

- The bare phone, from Apple's drawing (docs/reference/Apple-iPhone-17.pdf) and the measurements in §9.1: the
  149.61 x 71.45 x 7.95 mm body with the drawing's corner profile and glass edge; the camera plateau, 1.78 mm
  above the back glass, whose top face is blended into the glass by a concave fillet 2.62 mm wide (its foot is
  1.18 mm and 1.34 mm from the long and short edges); the two Ø16.00 camera glass rings, 3.45 mm above the back
  glass, 17.72 mm apart and not touching, which are part of the solid; and the side, action, and volume
  buttons, 0.45 mm proud. The Camera Control and the SIM tray are flush with the edge and have no geometry,
  and nor has the Ø6.28 mm flash, which is flush with the back glass, beside the plateau and centered on it
  lengthwise (Apple's Detail D); the assembly draws it as a silver disc cut into the housing.
- The camera cover, the clear adhesive polycarbonate stadium supplied with the case. It sits on the plateau at
  the plateau's top-face size and stands 0.080 in (2.03 mm) above it (measured), counterbored underneath for
  each glass ring (diametral clearance 0.4 mm over the ring, assumed). It leaves a 0.36 mm web over the glass.
- The case, an OtterBox Commuter. Its outside is the measured 155.5 x 77.0 mm and 0.540 in (13.72 mm) deep from
  the flat back to the front, with walls of 2.96 mm at the short edges and 2.77 mm at the long edges
  calculated from the measured camera position. The phone lies on the 0.125 in (3.18 mm) back plate, so the
  front rim stands 2.59 mm proud of the screen (calculated: depth less back plate less phone). The camera
  glass stands 0.28 mm proud of the flat back.

  The camera opening in the back is measured, 1.590 x 1.350 in (40.39 x 34.29 mm) at the phone's back glass,
  centered on the plateau lengthwise, its camera-side long edge at the foot of the plateau's blend fillet,
  and its corners rounded to the fillet foot's end radius (12.44 mm). Its wall flares uniformly to
  1.750 x 1.475 in (44.45 x 37.47 mm) at the ridge top; the corner radius grows by the mean growth of the
  half-dimensions (assumed). It clears the plateau and the flash.

  A protective ridge stands outside the opening's edge, around the opening: 0.050 in (1.27 mm) high, 0.085 in
  (2.16 mm) wide at its foot on the flat back, and with a flat top 0.040 in (1.02 mm) wide (all measured).
  Its foot and top are measured from the flared inner edge, so the outer wall slopes between the two widths.
  Where the outer wall comes within the case's back edge round (along the camera-side edge and the near end),
  it continues straight down over the round, which it cuts short; it never passes the case's side faces. The
  ridge top is 0.63 mm ahead of the cover top.

  The lens reaches through the opening and seats on the cover top, so the ridge does not set the lens
  spacing: the back plane (y = 0) is the cover top, and the cased phone is 14.35 mm thick behind it. The
  model does not show the case's port openings, and the 1.2 mm round on the front rim's inner edge is assumed.
  OtterBox publishes no drawing, so the rest of the inside of the case is assumed.

The cover's counterbore clearance, the ridge's placement outside the opening's edge, and the growth of the
opening's corner radius are assumed but do not affect the lens spacing, since the lens seats on the cover's
measured outer face.
"""

import math
from dataclasses import dataclass
from functools import cache

from build123d import (
    Axis,
    Compound,
    Edge,
    Face,
    Part,
    Plane,
    Pos,
    RectangleRounded,
    Shape,
    SlotOverall,
    Vector,
    VectorLike,
    Wire,
    extrude,
    fillet,
    loft,
    sweep,
)

from schlieren.cad import CUT_OVERRUN, assembly, box_between, fused, intersect, labeled, y_cylinder
from schlieren.palette import CAMERA_COVER, FLASH_SILVER, LENS_BLACK, PHONE_BODY, PHONE_CASE
from schlieren.standards import INCH
from schlieren.validation import require_positive_dimensions

# Apple's corner profile (Detail A, all four corners): distance along one edge from the corner of the bounding
# rectangle, and across it, for points from one edge's tangent to the other's.
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
    flash_depth: float = 0.5  # Display only: the flash is flush with the back glass; this is its drawn disc.

    # Measured in the case, §9.1.
    camera_height_above_edge: float = 60.6  # Main camera above the lower long edge.
    camera_inset_from_end: float = 34.3  # Main camera from the near short edge.
    case_depth: float = 0.540 * INCH  # Flat back of the case to its front.
    case_back_thickness: float = 0.125 * INCH  # Of the back plate, at the flat back.

    # Case. The camera ridge is a band around the camera opening, outside its edge (assumed), of this height,
    # width at its foot on the flat back, and flat top width (all measured). The lens reaches through the
    # opening to the camera glass, so the ridge does not set the back plane; it must stand above the camera
    # cover, which is proud of the flat back.
    camera_ridge_height: float = 0.050 * INCH
    camera_ridge_width: float = 0.085 * INCH
    camera_ridge_top_width: float = 0.040 * INCH
    # The clear polycarbonate cover over the plateau top (stadium at the plateau's full size). Its thickness is
    # measured; the counterbore clearance is assumed.
    camera_cover_thickness: float = 0.080 * INCH
    camera_cover_bore_diametral_clearance: float = 0.4
    case_corner_radius: float = 12.0
    case_edge_fillet: float = 2.0
    case_rim_fillet: float = 1.2  # Round of the front rim's inner edge; the 1.27 mm rim height limits it.
    case_front_lip_width: float = 2.5  # Of the front rim over the screen edge.
    # The camera opening (measured size): centered on the plateau along the length, and its camera-side long
    # edge hugs the foot of the plateau's blend fillet. Its wall flares: these are the size at the phone's back
    # glass, and the size at the top of the ridge is larger, flaring uniformly about the same center.
    camera_opening_length: float = 1.590 * INCH  # Along the long edges.
    camera_opening_width: float = 1.35 * INCH  # Along the short edges.
    camera_opening_top_length: float = 1.750 * INCH
    camera_opening_top_width: float = 1.475 * INCH

    def validate(self) -> None:
        require_positive_dimensions(self)
        if self.camera_cover_recess <= 0:
            raise ValueError("The camera ridge must stand above the camera cover")
        if self.camera_bore_depth >= self.camera_cover_thickness:
            raise ValueError("The camera cover must leave a web over the camera glass")
        if self.front_rim_height <= 0:
            raise ValueError("The case depth must leave a front rim over the screen")
        if self.case_side_wall <= 0 or self.case_end_wall <= 0:
            raise ValueError("The measured camera position must leave a case wall")

    @property
    def camera_opening_z_hi(self) -> float:
        """The opening's camera-side long edge: at the foot of the plateau's blend fillet."""
        return self.z_of(self.plateau_foot_u[0])

    @property
    def camera_opening_corner_radius(self) -> float:
        """The opening's corner radius, that of the fillet foot's rounded ends, so the corners follow it."""
        return (self.plateau_foot_u[1] - self.plateau_foot_u[0]) / 2

    @property
    def camera_ridge_top_y(self) -> float:
        return self.flat_back_y + self.camera_ridge_height

    def camera_opening_at(self, y: float) -> tuple[float, float, float]:
        """The opening's (length, width, corner radius) in the plane y. The flare is linear from the back
        glass to the ridge top, and the corner radius grows by the mean growth of the two half-dimensions."""
        t = (y - self.back_glass_y) / (self.camera_ridge_top_y - self.back_glass_y)
        grow_length = (self.camera_opening_top_length - self.camera_opening_length) / 2
        grow_width = (self.camera_opening_top_width - self.camera_opening_width) / 2
        return (
            self.camera_opening_length + 2 * t * grow_length,
            self.camera_opening_width + 2 * t * grow_width,
            self.camera_opening_corner_radius + t * (grow_length + grow_width) / 2,
        )

    @property
    def camera_opening_center(self) -> tuple[float, float]:
        """(x, z) of the opening's center at the back glass: the plateau's middle lengthwise."""
        x = (self.x_of(self.plateau_v[0]) + self.x_of(self.plateau_v[1])) / 2
        return x, self.camera_opening_z_hi - self.camera_opening_width / 2

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
    def cased_thickness(self) -> float:
        """From the back plane (the camera glass top) to the case front."""
        return -self.front_case_y

    @property
    def front_rim_height(self) -> float:
        """How far the front rim stands proud of the screen: the depth less the back plate and the phone."""
        return self.case_depth - self.case_back_thickness - self.thickness

    @property
    def camera_cover_height(self) -> float:
        """The top of the camera cover above the bare phone's back glass: the back plane."""
        return self.plateau_height + self.camera_cover_thickness

    @property
    def camera_bore_depth(self) -> float:
        """How deep each counterbore reaches up into the cover: the glass standing proud of the plateau."""
        return self.camera_glass_height - self.plateau_height

    @property
    def back_glass_y(self) -> float:
        """The bare phone's back glass, the camera cover height under the back plane."""
        return -self.camera_cover_height

    @property
    def flat_back_y(self) -> float:
        """The case's flat back: the back plate's thickness behind the phone's back glass."""
        return self.back_glass_y + self.case_back_thickness

    @property
    def front_case_y(self) -> float:
        return self.flat_back_y - self.case_depth

    @property
    def front_glass_y(self) -> float:
        return self.back_glass_y - self.thickness

    @property
    def camera_cover_recess(self) -> float:
        """How far the camera cover top, the back plane, stands under the camera ridge top."""
        return self.camera_ridge_height - self.camera_cover_height + self.case_back_thickness

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
    corners = (  # In order around the outline: corner, inward signs along x and z, and the traversal order.
        (x1, z0, -1, 1, False),
        (x1, z1, -1, -1, True),
        (x0, z1, 1, -1, False),
        (x0, z0, 1, 1, True),
    )
    edges: list[Edge] = []
    previous: VectorLike | None = None
    for cx, cz, sx, sz, reverse in corners:
        points: list[VectorLike] = [Vector(cx + sx * a, y, cz + sz * b) for a, b in CORNER_PROFILE]
        if reverse:
            points.reverse()
        if previous is not None:
            edges.append(Edge.make_line(previous, points[0]))
        edges.append(Edge.make_spline(points))
        previous = points[-1]
    assert previous is not None
    first = edges[0].start_point()
    edges.append(Edge.make_line(previous, first))
    return Face(Wire(edges))


def _edge_loops(solid: Shape, y_planes: tuple[float, ...]) -> list[Edge]:
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


def _button(p: PhoneParameters, spec: ButtonSpec) -> Compound:
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


def _filleted_plateau(p: PhoneParameters) -> Compound:
    """The plateau with its concave fillet, clipped to the body's outline.

    The fillet is a circular arc tangent to the back glass at the foot and meeting the top face at the
    drawing's inset, swept around the plateau's outline. The foot sits within the glass edge's round on two
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
    return intersect(plateau, outline)


# Built once per parameter set and shared (see parts/carriage.py); the cached solids must not be modified.
@cache
def _bare_housing(p: PhoneParameters) -> Shape:
    """The bare phone without its camera glass rings: housing with glass edges, camera plateau, and buttons."""
    body = extrude(_bare_outline(p, p.back_glass_y), amount=p.thickness, dir=Vector(0, -1, 0))
    body = fillet(_edge_loops(body, (p.back_glass_y, p.front_glass_y)), p.edge_fillet)
    body = body + _filleted_plateau(p)
    for spec in BUTTONS:
        if spec.protrusion > 0:
            body = body + _button(p, spec)
    return body


def _flash(p: PhoneParameters) -> Shape:
    """The rear flash: a disc flush with the back glass, drawn flash_depth deep (display only)."""
    return y_cylinder(
        p.flash_diameter, p.x_of(p.flash_v), p.z_of(p.flash_u), p.back_glass_y - p.flash_depth, p.back_glass_y
    )


@cache
def _display_housing(p: PhoneParameters) -> Shape:
    """The bare phone's housing with the flash's disc cut out, so the assembly can draw the flash in its own
    color."""
    return _bare_housing(p) - _flash(p)


@cache
def build_bare_phone(p: PhoneParameters | None = None) -> Shape:
    """The bare phone: housing, camera plateau with its glass rings, and the buttons, one solid."""
    p = p or PhoneParameters()
    p.validate()
    return fused(_bare_housing(p), _camera_glass(p))


@cache
def _camera_glass(p: PhoneParameters) -> Shape:
    """The two camera glass rings, on top of the plateau."""
    y0 = p.back_glass_y + p.plateau_height
    y1 = p.back_glass_y + p.camera_glass_height
    rings = [y_cylinder(p.camera_ring_diameter, x, z, y0, y1) for x, z in _camera_centers(p)]
    return rings[0] + rings[1]


@cache
def build_camera_cover(p: PhoneParameters | None = None) -> Shape:
    """The camera cover: the plateau's stadium, counterbored underneath for the two glass rings."""
    p = p or PhoneParameters()
    p.validate()
    y0 = p.back_glass_y + p.plateau_height
    cover = _plateau(p, y0, y0 + p.camera_cover_thickness)
    bore = p.camera_ring_diameter + p.camera_cover_bore_diametral_clearance
    for x, z in _camera_centers(p):
        cover = cover - y_cylinder(bore, x, z, y0 - CUT_OVERRUN, y0 + p.camera_bore_depth)
    return cover


@cache
def build_case(p: PhoneParameters | None = None) -> Compound:
    """The case: a shell around the bare phone with the front window and camera opening."""
    p = p or PhoneParameters()
    p.validate()
    x0, x1 = p.x_near - p.case_end_wall, p.x_near + p.length + p.case_end_wall
    z0, z1 = p.z_lower - p.case_side_wall, p.z_upper + p.case_side_wall
    y_front = p.front_case_y
    y_back = p.flat_back_y  # The flat back; the ridge, not modeled, rises from it.
    shell = box_between(x0, x1, y_front, y_back, z0, z1)
    shell = fillet(shell.edges().filter_by(Axis.Y), p.case_corner_radius)
    # The case outline without its back edge round, which the ridge's outer wall fills where they meet.
    envelope = fillet(
        box_between(x0, x1, y_front, p.camera_ridge_top_y + CUT_OVERRUN, z0, z1).edges().filter_by(Axis.Y),
        p.case_corner_radius,
    )
    shell = fillet(_edge_loops(shell, (y_front, y_back)), p.case_edge_fillet)
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
    # Back: the camera ridge and the flared opening through it, which also clears the flash.
    xc, zc = p.camera_opening_center

    def section(y: float, grow: float = 0.0):
        length, width, radius = p.camera_opening_at(y)
        sketch = (
            _plate_plane(y)
            * Pos(xc, zc)
            * RectangleRounded(length + 2 * grow, width + 2 * grow, radius + grow)
        )
        return sketch.face()

    top = p.camera_ridge_top_y
    foot_grow, top_grow = p.camera_ridge_width, p.camera_ridge_top_width
    ridge = loft([section(y_back, foot_grow), section(top, top_grow)])
    # Below the flat back the outer wall continues straight down over the case's back edge round, which it
    # abbreviates where the two meet.
    skirt = extrude(section(y_back, foot_grow), amount=p.case_edge_fillet, dir=Vector(0, -1, 0))
    ridge = intersect(fused(ridge, skirt), envelope)
    cutout = loft([section(p.back_glass_y - CUT_OVERRUN), section(top + CUT_OVERRUN)])
    return fused(shell, ridge) - build_bare_phone(p) - cutout


def build_phone(p: PhoneParameters | None = None):
    """The cased phone as an assembly: case, bare phone, and camera cover."""
    p = p or PhoneParameters()
    return assembly(
        "Phone",
        [
            labeled(build_case(p), "Case", PHONE_CASE),
            # Drawn in three colors; the rings and the flash are part of the bare phone.
            labeled(_display_housing(p), "Bare phone", PHONE_BODY),
            labeled(_flash(p), "Flash", FLASH_SILVER),
            labeled(_camera_glass(p), "Camera glass", LENS_BLACK),
            labeled(build_camera_cover(p), "Camera cover", CAMERA_COVER),
        ],
    )

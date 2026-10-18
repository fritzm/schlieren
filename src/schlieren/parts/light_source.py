"""Light source stack-up: threaded LED module, condenser, and iris on one SMR1/M; canonical design §6.

The LED star board mounts on a Thorlabs SM1CP2M externally threaded end cap, which threads into the LED-side
face of the SMR1/M and seats on its knurled flange. An Alpha CN40-40B pin-fin heatsink is bolted to the rear
of the cap. The SM1V05 (holding the ACL2520U-A, plano face toward the LED) threads into the slit-side face and
is locked by its SM1NT ring; its thread engagement is the focus adjustment. The SM1L03 tube threads into the
SM1V05 open end and the SM1D12 iris into the SM1L03, so lens, tube, and iris move together with focus.

Axial coordinate u (mm): u=0 at the LED-side face of the SMR1/M, +u toward the slit. Assembly coordinates: the
§3.4 source rail frame, x transverse, +y along u (toward the mirror), z=0 at the rail top. Nothing here is
printed; the solids are vendor STEP models (Thorlabs TR50/M, SMR1/M, SM1CP2M, SM1V05, ACL2520U-A, SM1L03,
SM1D12; Alpha CN40-40B) or, for the star board and LED package, representative solids built from the outline
drawings, for viewing and clearance checks. The SM1L03's own retaining ring is not modeled: the iris thread
occupies its place at the tube's open end. The cap and the heatsink base carry the §6.4 holes
(`light_source_holes`), with the McMaster heatsink screws, board screws, and insulating washers as vendor
models; the leads are not modeled. Dimension sources are noted per field: catalog values are from the drawings
in docs/reference/.
"""

from dataclasses import dataclass
from functools import cache
from math import isfinite

from build123d import Circle, Compound, Pos, Rectangle, RegularPolygon, Rot, Sphere, extrude

from schlieren.cad import CUT_OVERRUN, assembly, centered_box, floor_box, labeled, y_cylinder, z_cylinder
from schlieren.palette import BLACK_ANODIZED, GLASS, LED_YELLOW, METAL, NYLON, SOLDER_MASK_WHITE
from schlieren.parts.light_source_holes import (
    STAR_NOTCH_CENTER_RADIUS,
    STAR_NOTCH_COUNT,
    STAR_NOTCH_WIDTH,
    HoleLayoutParameters,
)
from schlieren.parts.rail_shoe import REFERENCE_HARDWARE_LABEL, post_stack
from schlieren.standards import DATUM_DISC_THICKNESS, INCH, OPTICAL_HEIGHT, POST_DIAMETER, POST_LENGTH
from schlieren.validation import require_positive_dimensions
from schlieren.vendor_cad import (
    MCMASTER_91292A111_HEAD_HEIGHT,
    MCMASTER_91292A111_LENGTH,
    MCMASTER_91545A410_THICKNESS,
    MCMASTER_92095A452_HEAD_HEIGHT,
    MCMASTER_92095A452_LENGTH,
    alpha_cn40_40b,
    mcmaster_91292a111,
    mcmaster_91545a410,
    mcmaster_92095a452,
    thorlabs_acl2520u_a,
    thorlabs_sm1cp2m,
    thorlabs_sm1d12,
    thorlabs_sm1l03,
    thorlabs_sm1v05,
    thorlabs_smr1_m,
)

HEATSINK_SCREW_LABEL = "M3 heatsink screw"  # Numbered 1-3, in the order of the layout's M3 holes.
BOARD_SCREW_LABEL = "M2 board screw"  # Numbered 1-2, in the order of the layout's M2 holes.
BOARD_WASHER_LABEL = "M2 board washer"  # One under each board screw head, numbered with it.
LED_MODULE_LABEL = "LED module"  # The heatsink, cap, star board, LED package, and their fasteners.
WHOLE_IN_SECTION = (LED_MODULE_LABEL, "ACL2520U-A condenser")  # Shown entire in light_source_section.
SECTION_BOX_SIZE = 1000.0  # Cutting box for light_source_section; larger than the module.


@dataclass(frozen=True)
class LEDBoard:
    name: str
    # Measured with dial calipers (inches), converted here.
    thickness_in: float
    # Catalog / nominal outline diameter.
    outline_diameter: float
    # Calculated from the LED outline drawing: apparent emitter height above the package solder pads, seen
    # through the silicone dome.
    emitter_height: float
    # LED outline drawing (catalog): square package side, substrate thickness, dome diameter, overall height.
    package_side: float
    package_base: float
    dome_diameter: float
    package_height: float

    @property
    def thickness(self):
        return self.thickness_in * INCH


GREEN = LEDBoard(
    "Green OSRAM OSLON SSL 120 / NewEnergy star", 0.0625, 0.783 * INCH, 0.45, 3.0, 0.53, 2.15, 1.754
)
WHITE = LEDBoard("White Nichia 519A / Convoy 20 mm star", 0.0590, 20.0, 0.75, 3.5, 0.77, 3.1, 2.35)
MODULES = (GREEN, WHITE)


@dataclass(frozen=True)
class LightSourceParameters:
    # Frozen project datum (§3.4).
    optical_height: float = OPTICAL_HEIGHT
    datum_thickness: float = DATUM_DISC_THICKNESS
    # Thorlabs TR50/M: metric-primary; its STEP model is rounded to inches (1.969 in, 0.499 in), so the metric
    # nominal values are exact.
    post_length: float = POST_LENGTH
    post_diameter: float = POST_DIAMETER
    # Thorlabs SMR1/M, SM1CP2M, SM1V05, SM1L03, SM1D12: inch-primary; exact values from the STEP models in
    # cad/vendor/ (the drawings' mm values are rounded).
    smr1_thickness: float = 0.400 * INCH
    smr1_outer_diameter: float = 1.200 * INCH
    smr1_axis_above_post_top: float = 0.870 * INCH
    sm1_thread_major: float = 1.035 * INCH
    sm1_thread_pitch: float = INCH / 40
    cap_overall: float = 0.210 * INCH
    cap_thread_length: float = 0.100 * INCH
    cap_flange_diameter: float = 1.200 * INCH
    # SM1V05: overall length minus seat depth gives plano-to-sleeve-end.
    sm1v05_overall: float = 1.030 * INCH
    sm1v05_seat_depth: float = 0.500 * INCH
    sm1v05_min_engagement: float = 0.110 * INCH  # Thorlabs adjustment range (drawing; not in the model)
    lock_ring_thickness: float = 0.110 * INCH  # SM1NT, included with the SM1V05.
    # SM1L03 and SM1D12: external-thread length, and length from the thread shoulder to the far end.
    sm1l03_thread_length: float = 0.120 * INCH
    sm1l03_length: float = 0.330 * INCH
    sm1d12_thread_length: float = 0.080 * INCH
    sm1d12_length: float = 0.340 * INCH
    # Thorlabs ACL2520U-A.
    lens_efl: float = 20.1
    lens_bfl: float = 12.0
    lens_center_thickness: float = 12.0
    # Calculated from the vendor models: height above the plano face of the SM1V05 retaining ring's lens-side
    # face when its inner edge meets the convex surface (contact at 4.29 mm).
    lens_retaining_ring_seat: float = 4.30
    # Setup value: rear principal plane (convex vertex) to slit, ~150 mm iris-to-slit plus iris offset.
    lens_to_slit: float = 153.0
    # Alpha CN40-40B (diameter +0/-0.5; use the maximum).
    heatsink_diameter: float = 40.0
    heatsink_height: float = 40.0
    heatsink_base: float = 3.0
    # McMaster 91292A111 M3 × 6 mm socket-head heatsink screws; **provisional** length (§6.2).
    heatsink_screw_length: float = MCMASTER_91292A111_LENGTH
    heatsink_screw_head_height: float = MCMASTER_91292A111_HEAD_HEIGHT
    # McMaster 92095A452 M2 × 5 mm button-head board screws, each on a 91545A410 nylon washer (§6.4).
    board_screw_length: float = MCMASTER_92095A452_LENGTH
    board_screw_head_height: float = MCMASTER_92095A452_HEAD_HEIGHT
    board_washer_thickness: float = MCMASTER_91545A410_THICKNESS
    # Estimates and allowances.
    solder_thickness: float = 0.07  # Estimated LED-to-star solder layer.
    sleeve_to_board_clearance: float = 0.3  # Axial, SM1V05 sleeve end to star top face.

    def validate(self):
        require_positive_dimensions(self)
        if self.cap_thread_length >= self.smr1_thickness:
            raise ValueError("Cap thread must leave SMR1/M thread for the SM1V05")
        if self.lens_to_slit <= self.lens_efl:
            raise ValueError("Slit must lie beyond the condenser focal length")
        if self.sm1d12_thread_length > self.sm1l03_length:
            raise ValueError("Iris thread must fit within the SM1L03 tube")

    # Axial positions (u) of fixed features.
    @property
    def cap_face(self):
        return self.cap_thread_length

    @property
    def heatsink_front(self):
        return self.cap_thread_length - self.cap_overall

    @property
    def plano_to_sleeve_end(self):
        return self.sm1v05_overall - self.sm1v05_seat_depth

    @property
    def post_top(self):
        return self.datum_thickness + self.post_length

    def emitter_u(self, board):
        return self.cap_face + board.thickness + self.solder_thickness + board.emitter_height

    @property
    def lens_vertex_inside_open_end(self):
        """Convex vertex below the SM1V05 open end; the SM1L03 spaces the iris clear of the lens."""
        return self.sm1v05_seat_depth - self.lens_center_thickness

    # Axial positions (u) of the parts that move with the SM1V05 focus engagement.
    def sleeve_end_u(self, engagement):
        return self.smr1_thickness - engagement

    def plano_u(self, engagement):
        return self.sleeve_end_u(engagement) + self.plano_to_sleeve_end

    def open_end_u(self, engagement):
        """SM1V05 open end, where the SM1L03 thread shoulder seats."""
        return self.sleeve_end_u(engagement) + self.sm1v05_overall

    def iris_seat_u(self, engagement):
        """SM1L03 open end, where the SM1D12 thread shoulder seats."""
        return self.open_end_u(engagement) + self.sm1l03_length

    def engagement_range(self, board):
        """SM1V05 thread engagement limits: Thorlabs minimum to sleeve-end/star clearance."""
        board_top = self.cap_face + board.thickness
        return (self.sm1v05_min_engagement, self.smr1_thickness - board_top - self.sleeve_to_board_clearance)

    def gap(self, board, engagement):
        """Emitter to lens plano face."""
        lo, hi = self.engagement_range(board)
        if not isfinite(engagement) or not lo <= engagement <= hi:
            raise ValueError("SM1V05 engagement outside the usable range")
        return self.plano_u(engagement) - self.emitter_u(board)

    def gap_range(self, board):
        lo, hi = self.engagement_range(board)
        return self.gap(board, hi), self.gap(board, lo)

    @property
    def optimum_gap(self):
        """Gap imaging the emitter onto the slit; object principal plane is EFL-BFL inside the plano face."""
        object_distance = 1 / (1 / self.lens_efl - 1 / self.lens_to_slit)
        return object_distance - (self.lens_efl - self.lens_bfl)

    @property
    def magnification(self):
        return self.lens_to_slit / (self.optimum_gap + self.lens_efl - self.lens_bfl)

    def focus_engagement(self, board, gap=None):
        gap = self.optimum_gap if gap is None else gap
        return self.smr1_thickness + self.plano_to_sleeve_end - self.emitter_u(board) - gap

    @property
    def heatsink_post_top_clearance(self):
        """Lowest heatsink point above the post top; round, so valid at any thread rotation."""
        return self.smr1_axis_above_post_top - self.heatsink_diameter / 2


def build_star_board(board):
    """Representative star board; back face on z=0, +z toward the lens, outline diameter across the flats."""
    outline = RegularPolygon(board.outline_diameter / 2, STAR_NOTCH_COUNT, major_radius=False)
    reach = board.outline_diameter  # Open each notch out past the hexagon corner.
    notch = Pos(STAR_NOTCH_CENTER_RADIUS, 0) * Circle(STAR_NOTCH_WIDTH / 2)
    notch += Pos(STAR_NOTCH_CENTER_RADIUS + reach / 2, 0) * Rectangle(reach, STAR_NOTCH_WIDTH)
    for i in range(STAR_NOTCH_COUNT):
        outline -= Rot(Z=i * 360 / STAR_NOTCH_COUNT) * notch
    return extrude(outline, board.thickness)  # ty: ignore[invalid-argument-type]


def build_led_package(board):
    """Representative LED package: square substrate and silicone dome; solder face on z=0, +z toward the
    lens."""
    dome_radius = board.dome_diameter / 2
    dome_center = board.package_height - dome_radius
    package = floor_box(board.package_side, board.package_side, board.package_base)
    package += z_cylinder(board.dome_diameter, 0, 0, board.package_base, dome_center)
    hemisphere = Sphere(dome_radius) & floor_box(2 * dome_radius, 2 * dome_radius, dome_radius)
    return package + Pos(0, 0, dome_center) * hemisphere


def _drilled(part, holes, diameter_of, y0, y1):
    """A vendor part (axis +Y) with the layout's holes cut through it between y0 and y1.

    The layout is a plan view from the LED side, so its +x is the assembly's -x and its +y the assembly's +z.
    """
    for hole in holes.holes():
        diameter = diameter_of(hole.kind)
        if diameter is not None:
            part -= y_cylinder(diameter, -hole.x, hole.y, y0 - CUT_OVERRUN, y1 + CUT_OVERRUN)
    return part


@cache
def build_drilled_cap(p, holes):
    """SM1CP2M cap in its vendor frame, drilled through: M3 and M2 tap drills (threads not cut), lead
    holes."""
    return _drilled(thorlabs_sm1cp2m(), holes, holes.cap_hole_diameter, p.heatsink_front, p.cap_face)


@cache
def build_drilled_heatsink(p, holes):
    """CN40-40B in its vendor frame, its base drilled through: M3 clearance and lead holes."""
    return _drilled(alpha_cn40_40b(), holes, holes.heatsink_hole_diameter, -p.heatsink_base, 0)


def build_light_source_assembly(p=None, board=GREEN, engagement=None, side_screws=False, holes=None):
    """Purchased parts in rail-top coordinates; the post is centered at the SMR1/M midplane.

    The post, the printed rail shoe under it, and the shoe's vendor hardware are grouped as
    REFERENCE_HARDWARE_LABEL; side_screws adds the shoe's side-slot screws to that group.
    """
    p = p or LightSourceParameters()
    p.validate()
    holes = holes or HoleLayoutParameters()
    holes.validate()
    engagement = p.focus_engagement(board) if engagement is None else engagement
    p.gap(board, engagement)  # Range check.
    z = p.optical_height
    post_y = p.smr1_thickness / 2
    plano = p.plano_u(engagement)
    sm1v05_body, lock_ring, retaining_ring = thorlabs_sm1v05()
    iris, iris_lever = thorlabs_sm1d12()
    iris_seat = p.iris_seat_u(engagement)
    toward_lens = Rot(X=-90)  # Board-local +z to +y.
    led_face = p.cap_face + board.thickness + p.solder_thickness
    # Vendor models, already in their mounting frames, from the rear forward: the post stands on the datum
    # disc, the SMR1/M's LED-side face is u=0, the cap seats on that face, and the heatsink base seats on the
    # cap's rear face. The SM1V05 sleeve enters the slit-side face by the focus engagement and its lock ring
    # bears on that face; the lens sits on the SM1V05 seat under its retaining ring; the SM1L03 seats on the
    # SM1V05 open end and the iris on the SM1L03 open end.
    module = [
        labeled(
            build_drilled_heatsink(p, holes), "CN40-40B heatsink", BLACK_ANODIZED, Pos(0, p.heatsink_front, z)
        ),
        labeled(build_drilled_cap(p, holes), "SM1CP2M cap", BLACK_ANODIZED, Pos(0, 0, z)),
    ]
    vendor_parts = {
        "SMR1 M ring": (thorlabs_smr1_m(), 0),
        "SM1V05 body": (sm1v05_body, p.sleeve_end_u(engagement)),
        "SM1NT lock ring": (lock_ring, p.smr1_thickness),
        "SM1V05 retaining ring": (retaining_ring, plano + p.lens_retaining_ring_seat),
        "SM1L03 tube": (thorlabs_sm1l03(), p.open_end_u(engagement)),
        "SM1D12 iris": (iris, iris_seat),
    }
    reference = post_stack(y=post_y, datum_thickness=p.datum_thickness, side_screws=side_screws)
    children = [assembly(REFERENCE_HARDWARE_LABEL, reference)]
    children += [
        labeled(part, name, BLACK_ANODIZED, Pos(0, u, z)) for name, (part, u) in vendor_parts.items()
    ]
    children.append(labeled(iris_lever, "SM1D12 iris lever", METAL, Pos(0, iris_seat, z)))
    children.append(labeled(thorlabs_acl2520u_a(), "ACL2520U-A condenser", GLASS, Pos(0, plano, z)))
    # Labels are viewer tree paths, so they must not contain "/".
    module.append(
        labeled(
            build_star_board(board), "LED star board", SOLDER_MASK_WHITE, Pos(0, p.cap_face, z) * toward_lens
        )
    )
    module.append(
        labeled(build_led_package(board), "LED package", LED_YELLOW, Pos(0, led_face, z) * toward_lens)
    )
    # The M3 screws enter from the pin side of the heatsink base, into the cap; the M2 screws, each on a nylon
    # washer on the board top, pass through its notches into the cap.
    board_top = p.cap_face + board.thickness
    toward_cap = Rot(X=90)  # Hardware-local +z to -y.
    washer_top = board_top + p.board_washer_thickness
    # By hole kind: (model, label, color, u of the model's z=0 face, facing), outermost part last.
    hardware = {
        "m3": [
            (
                mcmaster_91292a111(),
                HEATSINK_SCREW_LABEL,
                METAL,
                p.heatsink_front - p.heatsink_base,
                toward_lens,
            )
        ],
        "m2": [
            (mcmaster_91545a410(), BOARD_WASHER_LABEL, NYLON, washer_top, toward_cap),
            (mcmaster_92095a452(), BOARD_SCREW_LABEL, METAL, washer_top, toward_cap),
        ],
    }
    counts = dict.fromkeys(hardware, 0)
    for hole in holes.holes():
        if hole.kind in hardware:
            counts[hole.kind] += 1
            for part, label, color, u, facing in hardware[hole.kind]:
                loc = Pos(-hole.x, u, z + hole.y) * facing  # Layout +x is the assembly's -x (see _drilled).
                module.append(labeled(part, f"{label} {counts[hole.kind]}", color, loc))
    reference_group, *rest = children
    return assembly("Light source", [reference_group, assembly(LED_MODULE_LABEL, module), *rest])


def light_source_section(module: Compound) -> Compound:
    """Exposition view of the optical train: the module cut along the vertical plane through its axis.

    The -x half of the SMR1/M, SM1V05, SM1L03, and iris is kept, so the cut face looks toward +x; the parts in
    WHOLE_IN_SECTION are kept entire. The post, rail shoe, and its clamp screw and nut
    (REFERENCE_HARDWARE_LABEL) are omitted.
    """
    half_space = centered_box(SECTION_BOX_SIZE, SECTION_BOX_SIZE, SECTION_BOX_SIZE, x=-SECTION_BOX_SIZE / 2)
    kept = []
    for child in module.children:
        if child.label == REFERENCE_HARDWARE_LABEL:
            continue
        if child.label == LED_MODULE_LABEL:
            kept.append(
                assembly(child.label, (labeled(part, part.label, part.color) for part in child.children))
            )
            continue
        piece = child if child.label in WHOLE_IN_SECTION else child & half_space
        if piece.solids():
            kept.append(labeled(piece, child.label, child.color))
    return assembly("Light source section", kept)

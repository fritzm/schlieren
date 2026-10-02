"""Threaded SM1 LED module stack-up; canonical design §6.5 and §7.

The LED star board mounts on a Thorlabs SM1CP2M externally threaded end cap,
which threads into the LED-side face of the condenser SMR1/M and seats on its
knurled flange. The SM1V05 (holding the ACL2520U-A, plano face toward the LED)
threads into the slit-side face; its thread engagement is the focus adjustment.
An Alpha CN40-40B pin-fin heatsink is bolted to the rear of the cap.

Axial coordinate u (mm): u=0 at the LED-side face of the SMR1/M, +u toward
the slit. Assembly coordinates: x transverse, +y along u, z=0 at the rail top.
Nothing here is printed; the solids are purchased-part envelopes or vendor STEP
models (Thorlabs TR50/M, SMR1/M, SM1CP2M; Alpha CN40-40B) for viewing and clearance
checks. Dimension sources are noted per field: catalog values are from the drawings
in docs/reference/.
"""

from dataclasses import dataclass
from math import isfinite

import cadquery as cq

from schlieren.vendor_cad import alpha_cn40_40b, thorlabs_sm1cp2m, thorlabs_smr1_m, thorlabs_tr50_m

INCH = 25.4


@dataclass(frozen=True)
class LEDBoard:
    name: str
    # Measured with dial calipers (inches), converted here.
    thickness_in: float
    # Catalog / nominal outline diameter.
    outline_diameter: float
    # Calculated from the LED outline drawing: apparent emitter height above
    # the package solder pads, seen through the silicone dome.
    emitter_height: float

    @property
    def thickness(self):
        return self.thickness_in * INCH


GREEN = LEDBoard("Green OSRAM OSLON SSL 120 / NewEnergy star", 0.0625, 0.783 * INCH, 0.45)
WHITE = LEDBoard("White Nichia 519A / Convoy 20 mm star", 0.0590, 20.0, 0.75)
MODULES = (GREEN, WHITE)


@dataclass(frozen=True)
class LEDStackParameters:
    # Frozen project datum (§3.4).
    optical_height: float = 72.35
    datum_thickness: float = 0.010 * INCH
    # Thorlabs TR50/M: metric-primary; its STEP model is rounded to inches (1.969 in, 0.499 in), so the
    # metric nominal values are exact.
    post_length: float = 50.0
    post_diameter: float = 12.7
    # Thorlabs SMR1/M, SM1CP2M, SM1V05: inch-primary; exact values from the STEP models in cad/vendor/
    # (the drawings' mm values are rounded).
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
    # Thorlabs ACL2520U-A.
    lens_efl: float = 20.1
    lens_bfl: float = 12.0
    # Setup value: rear principal plane (convex vertex) to slit, ~150 mm iris-to-slit plus iris offset.
    lens_to_slit: float = 153.0
    # Alpha CN40-40B (diameter +0/-0.5; use the maximum).
    heatsink_diameter: float = 40.0
    heatsink_height: float = 40.0
    heatsink_base: float = 3.0
    # Estimates and allowances.
    solder_thickness: float = 0.07  # Estimated LED-to-star solder layer.
    sleeve_to_board_clearance: float = 0.3  # Axial, SM1V05 sleeve end to star top face.

    def validate(self):
        if any(not isfinite(v) or v <= 0 for v in vars(self).values()):
            raise ValueError("Dimensions and allowances must be finite and positive")
        if self.cap_thread_length >= self.smr1_thickness:
            raise ValueError("Cap thread must leave SMR1/M thread for the SM1V05")
        if self.lens_to_slit <= self.lens_efl:
            raise ValueError("Slit must lie beyond the condenser focal length")

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

    def plano_u(self, engagement):
        return self.smr1_thickness - engagement + self.plano_to_sleeve_end

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


def _disc(diameter, u0, u1, z, inner=0.0):
    plane = cq.Plane(origin=(0, u0, z), xDir=(1, 0, 0), normal=(0, 1, 0))
    wp = cq.Workplane(plane).circle(diameter / 2)
    if inner:
        wp = wp.circle(inner / 2)
    return wp.extrude(u1 - u0)


def build_led_stack_assembly(p=None, board=GREEN, engagement=None):
    """Purchased parts in rail-top coordinates; the post is centered at the SMR1/M midplane."""
    p = p or LEDStackParameters()
    p.validate()
    engagement = p.focus_engagement(board) if engagement is None else engagement
    p.gap(board, engagement)  # Range check.
    z = p.optical_height
    post_y = p.smr1_thickness / 2
    envelopes = {
        f"{board.name} star": _disc(board.outline_diameter, p.cap_face, p.cap_face + board.thickness, z),
        "Lens plano face marker": _disc(25.0, p.plano_u(engagement), p.plano_u(engagement) + 0.2, z),
    }
    # Vendor models, already in their mounting frames: the post stands on the datum disc, the ring's
    # LED-side face is u=0, the cap seats on that face, and the heatsink base seats on the cap's rear face.
    vendor_parts = {
        "TR50 M post": (thorlabs_tr50_m(), (0, post_y, p.datum_thickness)),
        "SMR1 M ring": (thorlabs_smr1_m(), (0, 0, z)),
        "SM1CP2M cap": (thorlabs_sm1cp2m(), (0, 0, z)),
        "CN40-40B heatsink": (alpha_cn40_40b(), (0, p.heatsink_front, z)),
    }
    assembly = cq.Assembly(name="Threaded LED module stack")
    for name, (part, origin) in vendor_parts.items():
        assembly.add(part, name=name, loc=cq.Location(origin), color=cq.Color(0.75, 0.75, 0.78))
    for name, part in envelopes.items():
        assembly.add(part, name=name, color=cq.Color(0.6, 0.62, 0.66))
    return assembly

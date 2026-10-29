"""EXPERIMENT: paper focus target that stands in for the stage-mounted slit head (slit_stage.py) while the
condenser is focused. Nothing here is final until the user accepts it.

The emitter image is focused on the slit plane, but the blades sit deep in the stage and cannot be seen. This
fixture swaps in for the stage plate on the same SM1RC/M ring: the same shoulder, ring gap, and spigot grip,
then a hollow barrel that widens to a rim whose face is the blade-seat plane. A sheet of tissue or oiled paper
lies on the rim and a retaining ring screws down over it into heat-set inserts. The LED image forms on the
paper's source-facing side and is read through the paper from the mirror side; the baffle tube stays in the
ring.

Local frame and assembly frame are the stage head's (slit_stage.py): y toward the mirror, the origin on the
optical axis in the blade-seat plane, so the rim face is y = 0.

**Provisional:** the paper's thickness (tissue about 0.05 mm, oiled paper about 0.1 mm) and the retention (four
M3 x 12 screws into heat-set inserts).
"""

from dataclasses import dataclass, field
from functools import cache
from math import cos, isfinite, radians, sin

from build123d import Pos, Rot, Shape

from schlieren.cad import CUT_OVERRUN, assembly, labeled, place, y_cylinder
from schlieren.palette import BUSHING_BRASS, METAL, PAPER, PRINTED_BLUE, PRINTED_GREEN
from schlieren.parts.rail_shoe import REFERENCE_HARDWARE_LABEL, post_stack
from schlieren.parts.slit_stage import SlitStageParameters, baffle_tube, head_location
from schlieren.vendor_cad import mcmaster_91292a114, mcmaster_97171a310


@dataclass(frozen=True)
class FocusTargetParameters:
    stage: SlitStageParameters = field(default_factory=SlitStageParameters)
    rim_diameter: float = 40.0  # Rim and retaining ring; wide enough for the insert recesses.
    rim_length: float = 8.0  # Rim face back to where the barrel narrows to the shoulder diameter.
    # Retaining ring: the window is about the baffle tube's clear bore, so the paper shows the whole beam.
    ring_thickness: float = 6.0
    ring_window_diameter: float = 22.0
    screw_count: int = 4
    screw_circle_diameter: float = 32.0
    screw_start_angle: float = 45.0  # Degrees from the slit direction.
    # Tissue is about 0.05 mm, oiled paper about 0.1 mm; the sheet is pierced by the screws.
    paper_thickness: float = 0.15
    paper_diameter: float = 36.0
    insert_engagement_margin: float = 0.5

    @property
    def bore(self):
        return self.stage.spigot_bore

    @property
    def barrel_diameter(self):
        """Barrel behind the rim: the spigot shoulder's diameter, which leaves a wall around the bore."""
        return self.stage.spigot_shoulder_diameter

    @property
    def barrel_length(self):
        """Shoulder face to the rim: the stage plate's rear to the blade-seat plane."""
        return -self.stage.plate_back

    @property
    def screw_radius(self):
        return self.screw_circle_diameter / 2

    def screw_xz(self):
        return [
            (
                self.screw_radius * cos(radians(self.screw_start_angle + i * 360 / self.screw_count)),
                self.screw_radius * sin(radians(self.screw_start_angle + i * 360 / self.screw_count)),
            )
            for i in range(self.screw_count)
        ]

    @property
    def screw_engagement(self):
        """Screw tip depth below the rim face, with the ring seated on the paper."""
        return self.stage.screw_length - self.ring_thickness - self.paper_thickness

    def validate(self):
        for name, value in vars(self).items():
            if isinstance(value, float) and not isfinite(value):
                raise ValueError(f"{name} must be finite")
        s = self.stage
        s.validate()
        recess = s.insert_flange_recess_diameter
        if self.screw_circle_diameter / 2 - recess / 2 < self.bore / 2 + 1.0:
            raise ValueError("Insert flange recesses must leave a wall inside the bore")
        if self.screw_circle_diameter / 2 + recess / 2 > self.rim_diameter / 2 - 1.0:
            raise ValueError("Insert flange recesses must leave a wall inside the barrel")
        if (
            self.ring_window_diameter > s.tube_clear_diameter
            or self.ring_window_diameter < 2 * s.lit_half_length
        ):
            raise ValueError("Ring window must pass the beam and not exceed the baffle tube's bore")
        if self.ring_window_diameter >= self.bore:
            raise ValueError("Ring must overlap the rim to grip the paper")
        if self.paper_diameter > self.rim_diameter - 2.0 or self.paper_diameter < self.screw_circle_diameter:
            raise ValueError("Paper must reach the screws and stay inside the barrel")
        if self.rim_diameter < self.barrel_diameter:
            raise ValueError("Rim must be at least as wide as the barrel")
        floor = 1.0  # Solid under the insert holes.
        if self.rim_length < s.insert_flange_recess_depth + s.insert_hole_depth + floor:
            raise ValueError("Rim must be deep enough to hold the heat-set inserts")
        if (
            self.screw_engagement > s.insert_hole_depth
            or self.screw_engagement < s.insert_installed_length - self.insert_engagement_margin
        ):
            raise ValueError("Ring screws must run through the inserts without bottoming")


@cache
def build_focus_target(p=None):
    """Spigot, shoulder, and barrel with four heat-set insert holes in the rim face (y = 0).

    Print rim face down, spigot up, without supports."""
    p = p or FocusTargetParameters()
    p.validate()
    s = p.stage
    shoulder_back = s.plate_back - s.ring_gap
    body = y_cylinder(p.barrel_diameter, 0, 0, s.plate_back, -p.rim_length + CUT_OVERRUN)
    body += y_cylinder(p.rim_diameter, 0, 0, -p.rim_length, 0)
    body += y_cylinder(s.spigot_shoulder_diameter, 0, 0, shoulder_back, s.plate_back + 0.5)
    body += y_cylinder(s.spigot_diameter, 0, 0, s.plate_back - s.spigot_length, shoulder_back + 0.5)
    body -= y_cylinder(p.bore, 0, 0, s.plate_back - s.spigot_length - CUT_OVERRUN, CUT_OVERRUN)
    for x, z in p.screw_xz():
        body -= y_cylinder(
            s.insert_hole_diameter,
            x,
            z,
            -s.insert_flange_recess_depth - s.insert_hole_depth,
            CUT_OVERRUN,
        )
        body -= y_cylinder(s.insert_flange_recess_diameter, x, z, -s.insert_flange_recess_depth, CUT_OVERRUN)
    return body


@cache
def build_retaining_ring(p=None):
    """Ring that clamps the paper to the rim; its rear face is the y = 0 plane. Print flat."""
    p = p or FocusTargetParameters()
    p.validate()
    ring = y_cylinder(p.rim_diameter, 0, 0, 0, p.ring_thickness)
    ring -= y_cylinder(p.ring_window_diameter, 0, 0, -CUT_OVERRUN, p.ring_thickness + CUT_OVERRUN)
    for x, z in p.screw_xz():
        ring -= y_cylinder(p.stage.screw_clearance, x, z, -CUT_OVERRUN, p.ring_thickness + CUT_OVERRUN)
    return ring


def build_paper(p=None):
    """Paper disc with the screw holes, its rear face on the y = 0 plane."""
    p = p or FocusTargetParameters()
    paper = y_cylinder(p.paper_diameter, 0, 0, 0, p.paper_thickness)
    for x, z in p.screw_xz():
        paper -= y_cylinder(p.stage.screw_clearance, x, z, -CUT_OVERRUN, p.paper_thickness + CUT_OVERRUN)
    return paper


def build_focus_target_assembly(p=None, include_support=True):
    """Fixture, paper, retaining ring, screws, inserts, and the baffle tube on the slit post."""
    p = p or FocusTargetParameters()
    p.validate()
    s = p.stage
    loc = head_location(s)
    children: list[Shape] = [
        labeled(build_focus_target(p), "Focus target", PRINTED_BLUE, loc),
        labeled(build_retaining_ring(p), "Retaining ring", PRINTED_GREEN, loc * Pos(0, p.paper_thickness, 0)),
        labeled(build_paper(p), "Paper", PAPER, loc),
    ]
    children.append(place(loc, baffle_tube(s)))
    for i, (x, z) in enumerate(p.screw_xz(), 1):
        screw = loc * Pos(x, p.paper_thickness + p.ring_thickness, z) * Rot(X=90)
        children.append(labeled(mcmaster_91292a114(), f"Ring screw {i}", METAL, screw))
        insert = loc * Pos(x, -s.insert_flange_recess_depth, z) * Rot(X=-90)
        children.append(labeled(mcmaster_97171a310(), f"Ring insert {i}", BUSHING_BRASS, insert))
    if include_support:
        reference = post_stack(ring=True, optical_height=s.optical_height, datum_thickness=s.datum_thickness)
        children.append(assembly(REFERENCE_HARDWARE_LABEL, reference))
    return assembly("Slit focus target (experiment)", children)

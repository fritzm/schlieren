"""EXPERIMENT: ground-glass variant of the slit focus target (slit_focus_target.py). Nothing here is final
until the user accepts it; it is not in the design document, the BOM, or the command list.

A Ø1 in ground-glass disc (Thorlabs DG10 series: 2.0 +/- 0.2 mm thick, Ø25.4 +0/-0.25 mm, catalog values)
replaces the paper. It sits in a counterbore in the target's rim, ground face toward the source, pushed
forward by a compliant gasket against the retaining ring's rear face. That face is the y = 0 blade-seat plane
(the ring seats on the rim), so the ground surface is at the datum whatever the glass thickness. The ring
window (Ø22) masks the rough edge. The screen is loaded from the front: the Ø24 spigot bore is smaller than
the disc, so it cannot be loaded from behind.

Local frame and assembly frame are those of the focus target and the stage head (y toward the mirror).

**Provisional:** the counterbore clearance (calibrate with a printed coupon), the gasket (1/16 in soft
rubber; no SKU chosen), and the choice of DG10 grit.
"""

from dataclasses import dataclass, field
from functools import cache
from math import isfinite

from build123d import Pos, Rot, Shape

from schlieren.cad import CUT_OVERRUN, assembly, labeled, place, y_cylinder
from schlieren.palette import BUSHING_BRASS, GLASS, METAL, PRINTED_BLUE, PRINTED_GREEN, RUBBER
from schlieren.parts.rail_shoe import REFERENCE_HARDWARE_LABEL, post_stack
from schlieren.parts.slit_focus_target import (
    FocusTargetParameters,
    build_focus_target,
    build_retaining_ring,
)
from schlieren.parts.slit_stage import baffle_tube, head_location
from schlieren.vendor_cad import mcmaster_91292a114, mcmaster_97171a310


@dataclass(frozen=True)
class FocusScreenParameters:
    # No paper: the ring seats directly on the rim. A wider rim and screw circle than the paper target's leave
    # walls around the Ø25.7 counterbore.
    target: FocusTargetParameters = field(
        default_factory=lambda: FocusTargetParameters(
            paper_thickness=0.0, rim_diameter=42.0, screw_circle_diameter=34.0
        )
    )
    # Thorlabs DG10 catalog values (verify against the part before ordering).
    glass_diameter: float = 25.4
    glass_thickness_nominal: float = 2.0
    glass_thickness_tolerance: float = 0.2
    # Printed holes come out small: provisional starting value, to be set from a coupon.
    counterbore_diametral_clearance: float = 0.3
    gasket_thickness: float = 1.59  # 1/16 in soft rubber, free; absorbs the glass's 0.4 mm thickness spread.
    gasket_min_gap: float = 0.95  # Counterbore floor to the thickest glass: the gasket's working space.
    ledge_thickness: float = 1.0  # Floor lip narrowing the bore to the ring window under the glass.

    @property
    def glass_thickness_max(self):
        return self.glass_thickness_nominal + self.glass_thickness_tolerance

    @property
    def glass_thickness_min(self):
        return self.glass_thickness_nominal - self.glass_thickness_tolerance

    @property
    def counterbore_diameter(self):
        return self.glass_diameter + self.counterbore_diametral_clearance

    @property
    def counterbore_depth(self):
        """Rim face to the floor under the gasket."""
        return self.glass_thickness_max + self.gasket_min_gap

    def gasket_compression(self, glass_thickness):
        """Fraction of the free gasket thickness squeezed with a glass of this thickness."""
        return 1 - (self.counterbore_depth - glass_thickness) / self.gasket_thickness

    @property
    def aperture_diameter(self):
        return self.target.ring_window_diameter

    def validate(self):
        for name, value in vars(self).items():
            if isinstance(value, float) and not isfinite(value):
                raise ValueError(f"{name} must be finite")
        t = self.target
        t.validate()
        if t.paper_thickness != 0.0:
            raise ValueError("The ring must seat on the rim: no paper")
        if self.counterbore_diametral_clearance <= 0:
            raise ValueError("Counterbore needs clearance around the disc")
        if self.aperture_diameter >= self.glass_diameter - 2.0:
            raise ValueError("Ring and floor lip must overlap the glass edge")
        recess = t.stage.insert_flange_recess_diameter
        if self.counterbore_diameter / 2 > t.screw_radius - recess / 2 - 1.0:
            raise ValueError("Counterbore must leave a wall to the insert recesses")
        if self.counterbore_depth + self.ledge_thickness > t.rim_length:
            raise ValueError("Counterbore and floor lip must fit in the rim")
        if not 0.05 <= self.gasket_compression(self.glass_thickness_min) <= 0.45:
            raise ValueError("Gasket must stay lightly loaded with the thinnest glass")
        if self.gasket_compression(self.glass_thickness_max) > 0.45:
            raise ValueError("Gasket over-compressed with the thickest glass")


@cache
def build_focus_screen_fixture(p=None):
    """The focus target with the glass counterbore (opening in the rim face, y = 0) and floor lip.

    Print rim face down, spigot up, without supports."""
    p = p or FocusScreenParameters()
    p.validate()
    floor = -p.counterbore_depth
    body = build_focus_target(p.target)
    body += y_cylinder(p.target.bore + 1.0, 0, 0, floor - p.ledge_thickness, floor + CUT_OVERRUN)
    body -= y_cylinder(
        p.aperture_diameter, 0, 0, floor - p.ledge_thickness - CUT_OVERRUN, floor + CUT_OVERRUN
    )
    body -= y_cylinder(p.counterbore_diameter, 0, 0, floor, CUT_OVERRUN)
    return body


def build_glass(p=None, thickness=None):
    """Ground-glass disc, ground face on the y = 0 plane."""
    p = p or FocusScreenParameters()
    thickness = p.glass_thickness_nominal if thickness is None else thickness
    return y_cylinder(p.glass_diameter, 0, 0, -thickness, 0)


def build_gasket(p=None):
    """Annular gasket under the glass, compressed between the glass and the floor."""
    p = p or FocusScreenParameters()
    glass_back = -p.glass_thickness_nominal
    thickness = p.gasket_thickness * (1 - p.gasket_compression(p.glass_thickness_nominal))
    gasket = y_cylinder(p.glass_diameter, 0, 0, glass_back - thickness, glass_back)
    return gasket - y_cylinder(
        p.aperture_diameter, 0, 0, glass_back - thickness - CUT_OVERRUN, glass_back + CUT_OVERRUN
    )


def build_focus_screen_assembly(p=None, include_support=True):
    """Fixture, glass, gasket, retaining ring, screws, inserts, and the baffle tube on the slit post."""
    p = p or FocusScreenParameters()
    p.validate()
    t = p.target
    s = t.stage
    loc = head_location(s)
    children: list[Shape] = [
        labeled(build_focus_screen_fixture(p), "Focus screen fixture", PRINTED_BLUE, loc),
        labeled(build_retaining_ring(t), "Retaining ring", PRINTED_GREEN, loc),
        labeled(build_glass(p), "Ground glass", GLASS, loc),
        labeled(build_gasket(p), "Gasket", RUBBER, loc),
        place(loc, baffle_tube(s)),
    ]
    for i, (x, z) in enumerate(t.screw_xz(), 1):
        children.append(
            labeled(
                mcmaster_91292a114(), f"Ring screw {i}", METAL, loc * Pos(x, t.ring_thickness, z) * Rot(X=90)
            )
        )
        insert = loc * Pos(x, -s.insert_flange_recess_depth, z) * Rot(X=-90)
        children.append(labeled(mcmaster_97171a310(), f"Ring insert {i}", BUSHING_BRASS, insert))
    if include_support:
        reference = post_stack(ring=True, optical_height=s.optical_height, datum_thickness=s.datum_thickness)
        children.append(assembly(REFERENCE_HARDWARE_LABEL, reference))
    return assembly("Slit focus screen (experiment)", children)

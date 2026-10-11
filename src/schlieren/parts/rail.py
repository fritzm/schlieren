"""Generic 2020 T-slot rail for viewer assemblies and figures; design §4.1.

Visualization only: the slot is a nominal slot-6 profile, not the measured geometry of the project's
extrusion (§4.1), so do not take fits or clearances from it.

Rail-assembly frame, as the rail shoe (a §3.4 rail frame): +x across the rail, +y along it toward the
mirror, z up; the rail top is z=0 and the rail is centered on x=y=0.
"""

from dataclasses import dataclass

from build123d import Circle, Part, Polygon, Pos, Rectangle, Rot, extrude, fillet

from schlieren.cad import CUT_OVERRUN


@dataclass(frozen=True)
class RailProfile:
    """Nominal 20-series, slot-6 section. Slot dimensions are measured inward from each outer face."""

    size: float = 20.0
    corner_radius: float = 1.5
    slot_mouth_width: float = 6.2
    lip_thickness: float = 1.8
    cavity_width: float = 11.0
    cavity_wall_height: float = 1.6  # Straight cavity wall below the lip, before the 45 degree taper.
    slot_depth: float = 6.1
    center_bore_diameter: float = 4.2

    @property
    def slot_floor_width(self) -> float:
        taper_height = self.slot_depth - self.lip_thickness - self.cavity_wall_height
        return self.cavity_width - 2 * taper_height


def build_rail(length: float, profile: RailProfile | None = None) -> Part:
    """A rail segment of the given length along y, top face at z=0."""
    f = profile or RailProfile()
    face = f.size / 2

    section = Rectangle(f.size, f.size)
    section = fillet(section.vertices(), f.corner_radius)
    # One slot, opening toward +y of the section; mirrored about its centerline and repeated on all four faces.
    half_slot = [
        (f.slot_mouth_width / 2, face + CUT_OVERRUN),
        (f.slot_mouth_width / 2, face - f.lip_thickness),
        (f.cavity_width / 2, face - f.lip_thickness),
        (f.cavity_width / 2, face - f.lip_thickness - f.cavity_wall_height),
        (f.slot_floor_width / 2, face - f.slot_depth),
    ]
    slot = Polygon(*half_slot, *[(-x, y) for x, y in reversed(half_slot)], align=None)
    for quarter_turn in range(4):
        section -= Rot(Z=90 * quarter_turn) * slot
    section -= Circle(f.center_bore_diameter / 2)

    rail = extrude(section, amount=length / 2, both=True)
    return Pos(0, 0, -face) * Rot(X=90) * rail

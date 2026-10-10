"""Hole layout of the LED module's SM1CP2M cap and CN40-40B heatsink base; canonical design §6.4.

Plan view from the LED side with the origin on the optical axis, +x to the right and +y up, in the frame of
the heatsink's pin lattice. The cap, the star board, and the heatsink are all described in this one frame,
so the same coordinates drill the cap and the heatsink and the two line up when bolted together.

Every hole is a through hole: the cap is only 0.210 in thick, and the screws are all shorter than it, so
none of them can reach the far face. Through holes also let plain plug taps finish a full thread.

The M3 screws bolt the heatsink to the cap, with their socket heads between four pins each. The M2 screws
hold the star board in two opposite notches. The two lead holes sit just outside the board's flat edges,
between pin columns, and pass the LED leads through the cap and the heatsink base.
"""

from dataclasses import dataclass
from itertools import combinations
from math import hypot

from schlieren.hardware import M3_CLEARANCE_DIAMETER, M3_SOCKET_HEAD_DIAMETER
from schlieren.parts.light_source import STAR_NOTCH_CENTER_RADIUS, STAR_NOTCH_WIDTH
from schlieren.standards import INCH

Point = tuple[float, float]


@dataclass(frozen=True)
class Hole:
    name: str
    kind: str  # "m3", "m2", or "lead"
    x: float
    y: float

    @property
    def position(self) -> Point:
        return (self.x, self.y)


@dataclass(frozen=True)
class HoleLayoutParameters:
    # Alpha CN40-40B drawing (docs/reference/Alpha-CN40.pdf): Ø40 base, Ø2.8 pins on a 6.9 mm square grid
    # centered on the axis, pins kept inside the rim.
    heatsink_diameter: float = 40.0
    lattice_pitch: float = 6.9
    pin_diameter: float = 2.8
    # Thorlabs SM1CP2M: SM1 external thread major diameter. The thread root is an estimate, not a drawing
    # value: the lead holes' outer edges must stay inside it. **Provisional**; measure a cap.
    cap_thread_major_diameter: float = 1.035 * INCH
    cap_thread_root_radius: float = 12.5
    # 20 mm star board, flat to flat (nominal), notches on its six corners (NewEnergy LST1-01F06 drawing).
    star_across_flats: float = 20.0
    notch_center_radius: float = STAR_NOTCH_CENTER_RADIUS
    notch_width: float = STAR_NOTCH_WIDTH
    # Tapped holes in the cap, with the thread major diameter bounding the material around each.
    m3_tap_drill: float = 2.5
    m3_thread_major: float = 3.0
    m2_tap_drill: float = 1.6
    m2_thread_major: float = 2.0
    # Heatsink base: M3 clearance, and the M3 socket-head screw head (ISO 4762).
    m3_clearance_diameter: float = M3_CLEARANCE_DIAMETER
    m3_head_diameter: float = M3_SOCKET_HEAD_DIAMETER
    # Lead holes, in both the cap and the heatsink base. **Provisional:** the lead insulation must fit.
    lead_hole_diameter: float = 2.0
    lead_radius: float = 11.0  # Just outside the star's flat edge, whose radius is star_across_flats / 2.
    # Required minimum material and gaps.
    min_wall: float = 1.0  # Between holes in the cap, to the thread major radius.
    min_pin_gap: float = 1.0  # Lead hole edge to pin edge.
    min_head_gap: float = 0.5  # Socket-head edge to pin edge.
    min_root_wall: float = 0.4  # Lead hole edge to the thread root.

    @property
    def pin_radius(self) -> float:
        return self.pin_diameter / 2

    def pin_positions(self) -> list[Point]:
        """The 24 pin centers: a 6 × 6 grid at odd multiples of half the pitch, clipped to the rim."""
        half = self.lattice_pitch / 2
        offsets = [(2 * i + 1) * half for i in range(-3, 3)]
        limit = self.heatsink_diameter / 2 - self.pin_radius
        return [(x, y) for x in offsets for y in offsets if hypot(x, y) <= limit]

    def holes(self) -> list[Hole]:
        pitch = self.lattice_pitch
        return [
            Hole("m3-1", "m3", pitch, pitch),
            Hole("m3-2", "m3", -pitch, pitch),
            Hole("m3-3", "m3", pitch, -pitch),
            Hole("m2-1", "m2", self.notch_center_radius, 0.0),
            Hole("m2-2", "m2", -self.notch_center_radius, 0.0),
            Hole("lead-1", "lead", 0.0, self.lead_radius),
            Hole("lead-2", "lead", 0.0, -self.lead_radius),
        ]

    def cap_hole_diameter(self, kind: str) -> float:
        """Drilled diameter in the cap: tap drill for the screws, the lead hole for the leads."""
        return {"m3": self.m3_tap_drill, "m2": self.m2_tap_drill, "lead": self.lead_hole_diameter}[kind]

    def heatsink_hole_diameter(self, kind: str) -> float | None:
        """Drilled diameter in the heatsink base, or None where the heatsink is not drilled."""
        return {"m3": self.m3_clearance_diameter, "m2": None, "lead": self.lead_hole_diameter}[kind]

    def keep_out_radius(self, kind: str) -> float:
        """Radius of the material the hole removes in the cap, counting the thread."""
        return {"m3": self.m3_thread_major, "m2": self.m2_thread_major, "lead": self.lead_hole_diameter}[
            kind
        ] / 2

    def clearances(self) -> dict[str, float]:
        """The governing gaps, mm, each of which must be at least its minimum."""
        holes = self.holes()
        pins = self.pin_positions()
        cap_walls = [
            hypot(a.x - b.x, a.y - b.y) - self.keep_out_radius(a.kind) - self.keep_out_radius(b.kind)
            for a, b in combinations(holes, 2)
        ]
        leads = [h for h in holes if h.kind == "lead"]
        m3 = [h for h in holes if h.kind == "m3"]
        lead_radius = self.lead_hole_diameter / 2
        return {
            "cap_wall": min(cap_walls),
            "lead_to_pin": min(
                hypot(h.x - px, h.y - py) - lead_radius - self.pin_radius for h in leads for px, py in pins
            ),
            "head_to_pin": min(
                hypot(h.x - px, h.y - py) - self.m3_head_diameter / 2 - self.pin_radius
                for h in m3
                for px, py in pins
            ),
            "lead_to_root": self.cap_thread_root_radius
            - max(hypot(*h.position) + lead_radius for h in leads),
            "lead_to_star_edge": min(hypot(*h.position) - lead_radius for h in leads)
            - self.star_across_flats / 2,
        }

    def validate(self) -> None:
        gaps = self.clearances()
        minimums = {
            "cap_wall": self.min_wall,
            "lead_to_pin": self.min_pin_gap,
            "head_to_pin": self.min_head_gap,
            "lead_to_root": self.min_root_wall,
            "lead_to_star_edge": 0.0,
        }
        short = [
            f"{name} {gaps[name]:.2f} < {minimums[name]:.2f}" for name in gaps if gaps[name] < minimums[name]
        ]
        if short:
            raise ValueError("Hole layout clearance: " + "; ".join(short))
        for hole in self.holes():
            if hypot(*hole.position) + self.keep_out_radius(hole.kind) > self.cap_thread_root_radius:
                raise ValueError(f"{hole.name} reaches the cap thread root")

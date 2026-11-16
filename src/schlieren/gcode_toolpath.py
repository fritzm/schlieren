"""Summarize PrusaSlicer G-code: where it moves and extrudes, per feature type and layer.

Only what the print checks need: bounds, layers, extruded volume by `;TYPE:`, temperatures. Moves are G0-G3
in absolute or relative XYZ, with absolute or relative extrusion; arcs are bounded by their true extremes.
"""

import math
import re
from dataclasses import dataclass, field

DEFAULT_FILAMENT_DIAMETER = 1.75  # mm
_COMMAND = re.compile(r"([GM]\d+)(.*)")
_WORDS = re.compile(r"([A-Za-z])(-?\d*\.?\d+)")

# Extrusion that is not the part itself.
NON_PART_TYPES = ("Skirt/Brim", "Custom", "Wipe tower")
SUPPORT_TYPES = ("Support material", "Support material interface")


@dataclass
class Box:
    """An xy bounding box that grows to take in points."""

    x_min: float = math.inf
    y_min: float = math.inf
    x_max: float = -math.inf
    y_max: float = -math.inf

    def add(self, x: float, y: float) -> None:
        self.x_min, self.x_max = min(self.x_min, x), max(self.x_max, x)
        self.y_min, self.y_max = min(self.y_min, y), max(self.y_max, y)

    def union(self, other: "Box") -> "Box":
        return Box(
            min(self.x_min, other.x_min),
            min(self.y_min, other.y_min),
            max(self.x_max, other.x_max),
            max(self.y_max, other.y_max),
        )


@dataclass
class Toolpath:
    layers: list[float] = field(default_factory=list)  # Z of each layer, from the ;Z: comments.
    volume: dict[str, float] = field(default_factory=dict)  # Extruded mm^3 by feature type.
    extrusion_box: dict[str, Box] = field(default_factory=dict)  # Where each type extrudes.
    extrusion_z: dict[str, tuple[float, float]] = field(default_factory=dict)
    move_box: Box = field(default_factory=Box)  # Every move, extruding or not.
    move_z: tuple[float, float] = (math.inf, -math.inf)
    hotend_temperatures: list[float] = field(default_factory=list)  # Every M104/M109 setpoint, in order.
    bed_temperatures: list[float] = field(default_factory=list)
    net_extrusion: float = 0.0  # Filament mm, retractions netted off.

    def part_volume(self) -> float:
        return sum(v for k, v in self.volume.items() if k not in NON_PART_TYPES and k not in SUPPORT_TYPES)

    def part_box(self) -> Box:
        box = Box()
        for kind, extent in self.extrusion_box.items():
            if kind not in NON_PART_TYPES and kind not in SUPPORT_TYPES:
                box = box.union(extent)
        return box

    def part_top(self) -> float:
        return max(
            (z[1] for kind, z in self.extrusion_z.items() if kind not in NON_PART_TYPES), default=-math.inf
        )

    def has_support(self) -> bool:
        return any(self.volume.get(kind, 0.0) > 0 for kind in SUPPORT_TYPES)

    def total_volume(self) -> float:
        return sum(self.volume.values())


def _arc_points(
    start: tuple[float, float], end: tuple[float, float], center: tuple[float, float], clockwise: bool
) -> list[tuple[float, float]]:
    """The end point and every axis extreme the arc passes through."""
    radius = math.hypot(start[0] - center[0], start[1] - center[1])
    first = math.atan2(start[1] - center[1], start[0] - center[0])
    last = math.atan2(end[1] - center[1], end[0] - center[0])
    sweep = last - first
    if clockwise:
        while sweep >= 0:
            sweep -= 2 * math.pi
    else:
        while sweep <= 0:
            sweep += 2 * math.pi
    points = [end]
    for quarter in range(4):
        angle = quarter * math.pi / 2
        # Offset of this extreme from the start, along the sweep's direction.
        along = (angle - first) % (2 * math.pi) if not clockwise else -((first - angle) % (2 * math.pi))
        if abs(along) < abs(sweep):
            points.append((center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)))
    return points


def summarize(gcode: str, filament_diameter: float = DEFAULT_FILAMENT_DIAMETER) -> Toolpath:
    path = Toolpath()
    filament_area = math.pi * (filament_diameter / 2) ** 2
    x = y = z = last_e = 0.0
    relative_xyz = False
    relative_e = True
    feature = "None"
    for raw in gcode.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith(";"):
            if line.startswith(";TYPE:"):
                feature = line[6:]
            elif line.startswith(";Z:"):
                path.layers.append(float(line[3:]))
            continue
        match = _COMMAND.match(line.split(";")[0])
        if match is None:
            continue
        command, rest = match.groups()
        words = {k.upper(): float(v) for k, v in _WORDS.findall(rest)}
        if command in ("M104", "M109"):
            if temperature := words.get("S", words.get("R")):
                path.hotend_temperatures.append(temperature)
        elif command in ("M140", "M190"):
            if temperature := words.get("S", words.get("R")):
                path.bed_temperatures.append(temperature)
        elif command == "M82":
            relative_e = False
        elif command == "M83":
            relative_e = True
        elif command == "G90":
            relative_xyz = False
        elif command == "G91":
            relative_xyz = True
        elif command == "G92" and "E" in words:
            last_e = words["E"]
        elif command in ("G0", "G1", "G2", "G3"):
            nx = x + words["X"] if relative_xyz and "X" in words else words.get("X", x)
            ny = y + words["Y"] if relative_xyz and "Y" in words else words.get("Y", y)
            nz = z + words["Z"] if relative_xyz and "Z" in words else words.get("Z", z)
            if "E" in words:
                extruded = words["E"] if relative_e else words["E"] - last_e
                last_e = words["E"]
            else:
                extruded = 0.0
            path.net_extrusion += extruded
            points = [(nx, ny)]
            if command in ("G2", "G3") and "I" in words:
                center = (x + words["I"], y + words.get("J", 0.0))
                points = _arc_points((x, y), (nx, ny), center, clockwise=command == "G2")
            extruding = extruded > 0 and ("X" in words or "Y" in words)
            for px, py in points:
                path.move_box.add(px, py)
                if extruding:
                    path.extrusion_box.setdefault(feature, Box()).add(px, py)
            path.move_z = (min(path.move_z[0], nz), max(path.move_z[1], nz))
            if extruding:
                path.volume[feature] = path.volume.get(feature, 0.0) + extruded * filament_area
                low, high = path.extrusion_z.get(feature, (math.inf, -math.inf))
                path.extrusion_z[feature] = (min(low, nz), max(high, nz))
            x, y, z = nx, ny, nz
    return path

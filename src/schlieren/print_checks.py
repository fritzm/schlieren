"""Checks on a sliced bgcode against the model it was sliced from: the engineering part of print preparation.

`check_bgcode` decodes the G-code itself (not an ASCII re-slice, which is not toolpath-identical) and returns
one `Check` per question: is the file intact, are the layers as profiled, does the print stay on the bed and
cover the model, is anything unexpected (supports), and does the extruded volume account for the model.
"""

import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from schlieren import bgcode
from schlieren.gcode_toolpath import DEFAULT_FILAMENT_DIAMETER, Box, summarize
from schlieren.print_3mf import bed_size, mesh_volume, read_config, read_placed_mesh

BLOCK_ORDER = (
    bgcode.BlockType.FILE_METADATA,
    bgcode.BlockType.PRINTER_METADATA,
    bgcode.BlockType.THUMBNAIL,
    bgcode.BlockType.PRINT_METADATA,
    bgcode.BlockType.SLICER_METADATA,
    bgcode.BlockType.GCODE,
)
LAYER_TOLERANCE = 0.002  # mm; layer Z values are printed to three decimals at most.
FOOTPRINT_OUTSIDE_TOLERANCE = 0.5  # mm the part's extrusion may reach beyond the model's bounding box.
FOOTPRINT_INSIDE_TOLERANCE = 1.0  # mm the part's extrusion may fall short of it on a side.
TOP_TOLERANCE_LAYERS = 1.0  # The last layer may overshoot the model top by up to this many layer heights.
SLICER_VOLUME_TOLERANCE = 0.02  # Our extruded volume vs the slicer's own filament estimate.
OVER_EXTRUSION_RATIO = 1.15  # Part extrusion above this share of the model's volume is suspicious.
UNDER_EXTRUSION_RATIO = 0.5  # Below this, report it (sparse infill makes lower values ordinary).
PURGE_TYPE = "Custom"  # The start G-code's purge line, which runs along the bed's front edge.
MAX_HOTEND_C = 240.0  # PLA only; change with --max-temperature.


class Status(Enum):
    OK = "ok"
    NOTE = "note"
    FAIL = "FAIL"


@dataclass(frozen=True)
class Check:
    name: str
    status: Status
    detail: str


def _box(box: Box) -> str:
    return f"X {box.x_min:.2f}..{box.x_max:.2f}, Y {box.y_min:.2f}..{box.y_max:.2f}"


def check_bgcode(
    bgcode_path: Path,
    model_path: Path | None,
    expect_support: bool = False,
    max_hotend: float = MAX_HOTEND_C,
) -> list[Check]:
    """Run every check. With model_path the bed comes from its profile and the print is compared to its mesh."""
    checks: list[Check] = []

    def add(name: str, ok: bool, detail: str, note: bool = False) -> None:
        checks.append(Check(name, Status.OK if ok else (Status.NOTE if note else Status.FAIL), detail))

    try:
        file = bgcode.parse(bgcode_path.read_bytes())
    except bgcode.BgcodeError as error:
        return [Check("structure", Status.FAIL, str(error))]
    order = [BLOCK_ORDER.index(block.type) for block in file.blocks]
    add(
        "structure",
        order == sorted(order),
        f"{len(file.blocks)} blocks, every checksum valid"
        + ("" if order == sorted(order) else "; blocks are out of order"),
    )

    printer = file.metadata(bgcode.BlockType.PRINTER_METADATA)
    slicer = file.metadata(bgcode.BlockType.SLICER_METADATA)
    stats = file.metadata(bgcode.BlockType.PRINT_METADATA)
    try:
        gcode = file.gcode()
    except (ValueError, bgcode.BgcodeError) as error:
        checks.append(Check("decode", Status.FAIL, f"G-code does not decode: {error}"))
        return checks
    path = summarize(gcode, float(slicer.get("filament_diameter", DEFAULT_FILAMENT_DIAMETER)))
    add("decode", bool(path.layers), f"{len(gcode.splitlines())} lines, {len(path.layers)} layers")
    if not path.layers:
        return checks

    layer_height = float(slicer["layer_height"])
    first_height = float(slicer["first_layer_height"])
    steps = {round(b - a, 3) for a, b in zip(path.layers, path.layers[1:], strict=False)}
    layers_ok = abs(path.layers[0] - first_height) < LAYER_TOLERANCE and all(
        abs(step - layer_height) < LAYER_TOLERANCE for step in steps
    )
    add(
        "layers",
        layers_ok,
        f"{len(path.layers)} layers: first {path.layers[0]:g} mm (profile {first_height:g}), "
        f"then steps {sorted(steps)} (profile {layer_height:g}), top {path.layers[-1]:g} mm",
    )

    hotend = max(path.hotend_temperatures, default=0.0)
    add(
        "temperatures",
        0 < hotend <= max_hotend,
        f"{printer.get('filament_type', '?')}: hotend setpoints {sorted(set(path.hotend_temperatures))}, "
        f"bed {sorted(set(path.bed_temperatures))} (limit {max_hotend:g})",
    )

    support = path.has_support()
    add(
        "supports",
        support == expect_support,
        ("support material printed" if support else "no support material")
        + ("" if support == expect_support else " (not what was expected)"),
    )

    printed = sum(path.volume.values())
    estimate = float(stats.get("filament used [cm3]", "nan")) * 1000
    add(
        "volume accounting",
        math.isfinite(estimate) and abs(printed - estimate) <= SLICER_VOLUME_TOLERANCE * estimate,
        f"extruded {printed:.0f} mm3 from the toolpath vs the slicer's {estimate:.0f} mm3",
    )

    if model_path is None:
        checks.append(Check("model comparison", Status.NOTE, "skipped: no 3MF given"))
        return checks

    bed = bed_size(read_config(model_path))
    inside = (
        path.move_box.x_min >= 0
        and path.move_box.y_min >= -2.0  # The profile's purge line runs at Y = -2.
        and path.move_box.x_max <= bed[0]
        and path.move_box.y_max <= bed[1]
    )
    printing = Box()
    for kind, extent in path.extrusion_box.items():
        if kind != PURGE_TYPE:
            printing = printing.union(extent)
    purge = path.extrusion_box.get(PURGE_TYPE)
    add(
        "bed",
        printing.x_min >= 0 and printing.y_min >= 0 and printing.x_max <= bed[0] and printing.y_max <= bed[1],
        f"all extrusion within the {bed[0]:g} x {bed[1]:g} mm bed ({_box(printing)})"
        + (f"; start-up purge line {_box(purge)}, as the profile's" if purge else "")
        + ("" if inside else f"; non-printing moves reach {_box(path.move_box)}"),
    )

    vertices, triangles = read_placed_mesh(model_path)
    low, high = vertices.min(axis=0), vertices.max(axis=0)
    part = path.part_box()
    outside = max(low[0] - part.x_min, low[1] - part.y_min, part.x_max - high[0], part.y_max - high[1])
    short = max(part.x_min - low[0], part.y_min - low[1], high[0] - part.x_max, high[1] - part.y_max)
    add(
        "footprint",
        outside <= FOOTPRINT_OUTSIDE_TOLERANCE and short <= FOOTPRINT_INSIDE_TOLERANCE,
        f"part extrusion {_box(part)} vs model {_box(Box(low[0], low[1], high[0], high[1]))}",
    )

    top = path.part_top()
    add(
        "height",
        abs(top - high[2]) <= TOP_TOLERANCE_LAYERS * layer_height + LAYER_TOLERANCE,
        f"top layer at {top:g} mm vs model top {high[2]:g} mm (layer grid: first {first_height:g}, then {layer_height:g})",
    )

    volume = mesh_volume(vertices, triangles)
    ratio = path.part_volume() / volume if volume > 0 else float("nan")
    add(
        "part volume",
        UNDER_EXTRUSION_RATIO <= ratio <= OVER_EXTRUSION_RATIO,
        f"part extrusion {path.part_volume():.0f} mm3 vs model {volume:.0f} mm3 (ratio {ratio:.3f}; "
        f"skirt, brim and purge excluded)",
        note=ratio < UNDER_EXTRUSION_RATIO,  # Sparse infill legitimately leaves it low; too much never is.
    )
    return checks


def report(checks: list[Check]) -> str:
    return "\n".join(f"  [{check.status.value:>4}] {check.name}: {check.detail}" for check in checks)


def failed(checks: list[Check]) -> list[Check]:
    return [check for check in checks if check.status == Status.FAIL]

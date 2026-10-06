"""Drilling layout drawing of the front pivot plate; design §4.2.

A plan view from above as a full-scale SVG (one user unit is 1 mm), for laying out and drilling the plywood.
Hole positions are dimensioned as ordinates in the §4.2 plate coordinates (the §3.4 pivot frame): x from the
plate centerline and y from the aft edge.

The sheet is drawn with the mirror-facing edge at the top, so +y runs up the sheet and +x to the right, as
seen from above with the mirror ahead.
"""

from xml.sax.saxutils import escape

from schlieren.parts.frame import FrameParameters

PAGE_WIDTH = 260.0
PAGE_HEIGHT = 208.0
PLATE_LEFT = 46.0  # Sheet x of the plate's left edge.
PLATE_TOP = 30.0  # Sheet y of the plate's mirror-facing edge.
CENTER_MARK = 5.0  # Half-length of the crosshair on each hole.
ORDINATE_GAP = 4.0  # From the plate edge to the end of an extension line.
TEXT_GAP = 1.5  # From the end of an extension line to its figure.
FONT_SIZE = 3.4
SMALL_FONT_SIZE = 2.7
TITLE_FONT_SIZE = 4.6

STYLE = """
text { font-family: Helvetica, Arial, sans-serif; fill: #000; }
.outline { fill: #f4ead6; stroke: #000; stroke-width: 0.5; }
.hole { fill: #fff; stroke: #000; stroke-width: 0.35; }
.mark { stroke: #000; stroke-width: 0.2; }
.extension { stroke: #555; stroke-width: 0.15; }
.centerline { stroke: #555; stroke-width: 0.2; stroke-dasharray: 8 1.5 1.5 1.5; }
.hidden { fill: none; stroke: #555; stroke-width: 0.25; stroke-dasharray: 2 1.2; }
"""


def pivot_plate_drawing_svg(p: FrameParameters | None = None) -> str:
    """The dimensioned drilling layout of the pivot plate, as SVG text."""
    p = p or FrameParameters()
    p.validate()
    # Positions on the sheet are taken from the plate's left edge; the x figures are from its centerline.
    holes = {name: (x + p.plate_width / 2, y) for name, (x, y) in p.plate_holes().items()}
    bottom = PLATE_TOP + p.plate_depth
    right = PLATE_LEFT + p.plate_width
    out: list[str] = []

    def sx(x: float) -> float:
        return PLATE_LEFT + x

    def sy(y: float) -> float:
        return bottom - y

    def line(x1: float, y1: float, x2: float, y2: float, css: str) -> None:
        out.append(f'<line class="{css}" x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}"/>')

    def text(
        x: float, y: float, content: str, anchor: str = "middle", size: float = FONT_SIZE, turn=0
    ) -> None:
        rotate = f' transform="rotate({turn} {x:.3f} {y:.3f})"' if turn else ""
        out.append(
            f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size}" text-anchor="{anchor}"{rotate}>'
            f"{escape(content)}</text>"
        )

    def x_ordinate(x: float, from_y: float) -> None:
        """Extension line from plate height from_y down past the aft edge, with its figure."""
        line(sx(x), sy(from_y), sx(x), bottom + ORDINATE_GAP, "extension")
        figure = f"{x - p.plate_width / 2:+.1f}"
        text(sx(x) + FONT_SIZE * 0.35, bottom + ORDINATE_GAP + TEXT_GAP, figure, "end", turn=-90)

    def y_ordinate(y: float, from_x: float, note: str = "") -> None:
        """Extension line from plate position from_x out past the nearer side edge, with its figure."""
        on_left = from_x <= p.plate_width / 2
        end = PLATE_LEFT - ORDINATE_GAP if on_left else right + ORDINATE_GAP
        line(sx(from_x), sy(y), end, sy(y), "extension")
        figure_x = end - TEXT_GAP if on_left else end + TEXT_GAP
        text(figure_x, sy(y) + FONT_SIZE * 0.35, f"{y:.1f}", "end" if on_left else "start")
        if note:
            text(figure_x, sy(y) + FONT_SIZE * 0.35 + SMALL_FONT_SIZE * 1.3, note, "end", SMALL_FONT_SIZE)

    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_WIDTH}mm" height="{PAGE_HEIGHT}mm" '
        f'viewBox="0 0 {PAGE_WIDTH} {PAGE_HEIGHT}">'
    )
    out.append(f"<style>{STYLE}</style>")
    out.append(f'<rect width="{PAGE_WIDTH}" height="{PAGE_HEIGHT}" fill="#fff"/>')

    text(PLATE_LEFT, 9, "Front pivot plate: drilling layout, seen from above", "start", TITLE_FONT_SIZE)
    text(
        PLATE_LEFT,
        15.5,
        f"{p.plate_width:g} × {p.plate_depth:g} × {p.plywood_thickness:g} mm (1/2 in) Baltic birch. "
        f"Six holes Ø{p.m5_clearance_diameter:g} mm through, for M5. Dimensions in mm: x from the plate "
        "centerline, y from the aft edge.",
        "start",
        SMALL_FONT_SIZE,
    )
    text(
        PLATE_LEFT,
        20,
        "Full scale when printed at 100%: check the plate width against a rule before using the sheet "
        "as a template.",
        "start",
        SMALL_FONT_SIZE,
    )

    out.append(
        f'<rect class="outline" x="{PLATE_LEFT}" y="{PLATE_TOP}" width="{p.plate_width}" '
        f'height="{p.plate_depth}"/>'
    )
    text(
        sx(p.plate_width - 2),
        sy(p.plate_depth - 2) + SMALL_FONT_SIZE,
        "mirror-facing edge",
        "end",
        SMALL_FONT_SIZE,
    )
    text(sx(p.plate_width - 2), sy(2), "aft edge", "end", SMALL_FONT_SIZE)

    # Plate centerline, the x origin of the §4.2 plate coordinates.
    center = p.plate_width / 2
    line(sx(center), PLATE_TOP - ORDINATE_GAP, sx(center), bottom + ORDINATE_GAP, "centerline")
    text(sx(center) + FONT_SIZE * 0.35, bottom + ORDINATE_GAP + TEXT_GAP, "0 CL", "end", turn=-90)

    # Front foot, stuck to the underside on the pivot line.
    out.append(
        f'<circle class="hidden" cx="{sx(center):.3f}" cy="{sy(p.plate_depth - p.pivot_setback):.3f}" '
        f'r="{p.foot_diameter / 2:.3f}"/>'
    )
    text(
        sx(center),
        sy(p.plate_depth - p.pivot_setback) + p.foot_diameter / 2 + SMALL_FONT_SIZE + 1.0,
        "front foot, underside",
        size=SMALL_FONT_SIZE,
    )

    for edge in (0.0, p.plate_width):
        x_ordinate(edge, 0.0)
    for edge in (0.0, p.plate_depth):
        y_ordinate(edge, 0.0)

    for name, (x, y) in holes.items():
        x_ordinate(x, y)
        if "pivot" in name:
            y_ordinate(y, x)
        elif "outer" in name:
            y_ordinate(y, x, "outer yaw holes" if x < center else "")

    # The inner yaw holes lie between the outer holes and the centerline, so their height is given in place.
    inner = [position for name, position in holes.items() if "inner" in name]
    inner_y = inner[0][1]
    text(
        sx(center),
        sy(inner_y) - 7,
        f"inner yaw holes at y = {inner_y:.1f}",
        size=SMALL_FONT_SIZE,
    )
    line(sx(min(x for x, _ in inner)), sy(inner_y), sx(max(x for x, _ in inner)), sy(inner_y), "extension")

    for name, (x, y) in holes.items():
        out.append(
            f'<circle class="hole" data-hole="{escape(name)}" cx="{sx(x):.3f}" cy="{sy(y):.3f}" '
            f'r="{p.m5_clearance_diameter / 2:.3f}"/>'
        )
        line(sx(x) - CENTER_MARK, sy(y), sx(x) + CENTER_MARK, sy(y), "mark")
        line(sx(x), sy(y) - CENTER_MARK, sx(x), sy(y) + CENTER_MARK, "mark")
        text(sx(x), sy(y) + CENTER_MARK + SMALL_FONT_SIZE + 0.5, name.lower(), size=SMALL_FONT_SIZE)

    out.append("</svg>")
    return "\n".join(out) + "\n"

"""Drawing of the LED module hole layout; design §6.4.

A full-scale SVG (one user unit is 1 mm) in the plan view from the LED side of
`schlieren.parts.light_source_holes`: the design-doc figure of the layout, with heatsink pins, cap, star board,
and every hole with its position.
"""

from math import cos, radians, sin
from xml.sax.saxutils import escape

from schlieren.parts.light_source_holes import Hole, HoleLayoutParameters

FONT_SIZE = 1.7
SMALL_FONT_SIZE = 1.35
STAR_SLOT_REACH = 11.7  # The star's corner slots are drawn out past the corners (r = 11.5).

STYLE = """
text { font-family: Helvetica, Arial, sans-serif; fill: #000; }
.heatsink { fill: #ececec; stroke: #777; stroke-width: 0.2; }
.pin { fill: #b8b8b8; stroke: #555; stroke-width: 0.15; }
.cap { fill: none; stroke: #b36200; stroke-width: 0.25; }
.cap-flange { fill: none; stroke: #b36200; stroke-width: 0.2; stroke-dasharray: 2 1; }
.cap-relief { fill: none; stroke: #b36200; stroke-width: 0.15; stroke-dasharray: 0.6 0.6; }
.star { fill: #d6e4f2; stroke: #2f5f98; stroke-width: 0.25; fill-opacity: 0.9; }
.notch { fill: #fff; stroke: none; }
.notch-edge { fill: none; stroke: #2f5f98; stroke-width: 0.25; }
.m3 { fill: #fff; stroke: #c00; stroke-width: 0.3; }
.m2 { fill: #fff; stroke: #070; stroke-width: 0.3; }
.lead { fill: #fc0; stroke: #000; stroke-width: 0.25; }
.thread { fill: none; stroke: #c00; stroke-width: 0.15; }
.head { fill: none; stroke: #c00; stroke-width: 0.15; stroke-dasharray: 0.8 0.5; }
.axis { stroke: #888; stroke-width: 0.12; stroke-dasharray: 3 0.8 0.6 0.8; }
.leader { stroke: #444; stroke-width: 0.12; }
"""

KIND_COLOR_CLASS = {"m3": "m3", "m2": "m2", "lead": "lead"}


class _Sheet:
    """An SVG accumulator with the origin shifted to (cx, cy) and +y drawn up the sheet."""

    def __init__(self, width: float, height: float, cx: float = 0.0, cy: float = 0.0):
        self.width, self.height, self.cx, self.cy = width, height, cx, cy
        self.out: list[str] = []

    def at(self, cx: float, cy: float) -> "_Sheet":
        """A view of this sheet with its origin at sheet position (cx, cy)."""
        view = _Sheet(self.width, self.height, cx, cy)
        view.out = self.out
        return view

    def x(self, x: float) -> float:
        return self.cx + x

    def y(self, y: float) -> float:
        return self.cy - y

    def line(self, x1, y1, x2, y2, css) -> None:
        self.out.append(
            f'<line class="{css}" x1="{self.x(x1):.3f}" y1="{self.y(y1):.3f}" '
            f'x2="{self.x(x2):.3f}" y2="{self.y(y2):.3f}"/>'
        )

    def circle(self, x, y, diameter, css, hole: str = "") -> None:
        tag = f' data-hole="{hole}"' if hole else ""
        self.out.append(
            f'<circle class="{css}"{tag} cx="{self.x(x):.3f}" cy="{self.y(y):.3f}" r="{diameter / 2:.3f}"/>'
        )

    def path(self, d: str, css: str) -> None:
        self.out.append(f'<path class="{css}" d="{d}"/>')

    def text(self, x, y, content, anchor="middle", size=FONT_SIZE, bold=False) -> None:
        weight = ' font-weight="bold"' if bold else ""
        self.out.append(
            f'<text x="{self.x(x):.3f}" y="{self.y(y):.3f}" font-size="{size}" text-anchor="{anchor}"{weight}>'
            f"{escape(content)}</text>"
        )

    def svg(self, background: bool = True) -> str:
        head = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}mm" height="{self.height}mm" '
            f'viewBox="0 0 {self.width} {self.height}">\n<style>{STYLE}</style>\n'
        )
        if background:
            head += f'<rect width="{self.width}" height="{self.height}" fill="#fff"/>\n'
        return head + "\n".join(self.out) + "\n</svg>\n"


def _notch_paths(p: HoleLayoutParameters, sheet: _Sheet) -> None:
    """The six U-notches on the star's corners (corners at 0°, 60°, ...), each opening outward."""
    half = p.notch_width / 2
    inner = p.notch_center_radius
    for k in range(6):
        angle = radians(60 * k)

        def pt(u: float, v: float, c: float = cos(angle), s: float = sin(angle)) -> str:
            return f"{sheet.x(u * c - v * s):.3f},{sheet.y(u * s + v * c):.3f}"

        u_edge = f"M {pt(STAR_SLOT_REACH, half)} L {pt(inner, half)} A {half:.4f} {half:.4f} 0 0 0 {pt(inner, -half)} L {pt(STAR_SLOT_REACH, -half)}"
        sheet.path(u_edge + " Z", "notch")
        sheet.path(u_edge, "notch-edge")


def _star(p: HoleLayoutParameters, sheet: _Sheet) -> None:
    """The 20 mm star board: flats at 30° + 60°k, so a corner and its notch lie on +x."""
    apothem = p.star_across_flats / 2
    corner = apothem / cos(radians(30))
    points = " ".join(
        f"{sheet.x(corner * cos(radians(60 * k))):.3f},{sheet.y(corner * sin(radians(60 * k))):.3f}"
        for k in range(6)
    )
    sheet.out.append(f'<polygon class="star" points="{points}"/>')
    _notch_paths(p, sheet)


def _pins(p: HoleLayoutParameters, sheet: _Sheet, css: str) -> None:
    for x, y in p.pin_positions():
        sheet.circle(x, y, p.pin_diameter, css)


def _hole_label(hole: Hole, p: HoleLayoutParameters) -> str:
    if hole.kind == "m3":
        return f"M3 ({hole.x:+.2f}, {hole.y:+.2f})"
    if hole.kind == "m2":
        return f"M2 ({hole.x:+.3f}, {hole.y:+.1f})"
    return f"lead Ø{p.lead_hole_diameter:g} ({hole.x:+.1f}, {hole.y:+.1f})"


def layout_drawing_svg(p: HoleLayoutParameters | None = None) -> str:
    """The design-doc figure: pins, cap, star, and every hole, with positions in mm from the axis."""
    p = p or HoleLayoutParameters()
    p.validate()
    width, height = 100.0, 76.0
    sheet = _Sheet(width, height, width / 2, 36.0)

    sheet.circle(0, 0, p.heatsink_diameter, "heatsink")
    _pins(p, sheet, "pin")
    sheet.circle(0, 0, 2 * p.cap_relief_radius, "cap-relief")
    sheet.circle(0, 0, p.cap_thread_major_diameter, "cap")
    sheet.circle(0, 0, 30.48, "cap-flange")
    _star(p, sheet)
    sheet.line(-23, 0, 23, 0, "axis")
    sheet.line(0, -23, 0, 23, "axis")

    for hole in p.holes():
        if hole.kind == "m3":
            sheet.circle(hole.x, hole.y, p.m3_head_diameter, "head")
            sheet.circle(hole.x, hole.y, p.m3_thread_major, "thread")
        sheet.circle(hole.x, hole.y, p.cap_hole_diameter(hole.kind), KIND_COLOR_CLASS[hole.kind], hole.name)

    # Labels sit outside the heatsink on leaders; left and right columns, top and bottom for the leads.
    placements = {
        "m3-1": (30.0, 17.0, "start"),
        "m3-2": (-30.0, 17.0, "end"),
        "m3-3": (30.0, -17.0, "start"),
        "m2-1": (30.0, 3.0, "start"),
        "m2-2": (-30.0, 3.0, "end"),
        "lead-1": (14.0, 27.0, "start"),
        "lead-2": (14.0, -27.0, "start"),
    }
    for hole in p.holes():
        lx, ly, anchor = placements[hole.name]
        edge = lx - 1 if anchor == "start" else lx + 1
        sheet.line(hole.x, hole.y, edge, ly, "leader")
        sheet.text(lx, ly - FONT_SIZE * 0.3, _hole_label(hole, p), anchor)

    sheet.text(
        -width / 2 + 3,
        -31.5,
        "View from the LED side. Orange: cap (Ø26.29 thread, Ø25.1 relief, Ø30.48 flange); blue: 20 mm star; "
        "grey: heatsink pins.",
        "start",
        SMALL_FONT_SIZE,
    )
    sheet.text(
        -width / 2 + 3,
        -33.7,
        f"All holes are through. Cap drilled M3 Ø{p.m3_tap_drill:g}, M2 Ø{p.m2_tap_drill:g}, lead "
        f"Ø{p.lead_hole_diameter:g}; heatsink base M3 Ø{p.m3_clearance_diameter:g}, lead "
        f"Ø{p.lead_hole_diameter:g}. Dashed circles: M3 head Ø{p.m3_head_diameter:g}.",
        "start",
        SMALL_FONT_SIZE,
    )
    return sheet.svg()

"""Drawings of the LED module hole layout; design §6.4.

Two full-scale SVGs (one user unit is 1 mm), both in the plan view from the LED side of
`schlieren.parts.light_source_holes`:

- the design-doc figure of the layout: heatsink pins, cap, star board, and every hole with its position;
- a sheet of two drilling templates, one for the cap and one for the heatsink base, to print at 100%, cut
  out, and stick on.
"""

from math import cos, radians, sin
from xml.sax.saxutils import escape

from schlieren.parts.light_source_holes import Hole, HoleLayoutParameters

FONT_SIZE = 1.7
SMALL_FONT_SIZE = 1.35
TITLE_FONT_SIZE = 2.4
MARK = 1.5  # Half-length of the crosshair on each hole in a template.
EDGE_TICK = (1.0, 4.0)  # Template alignment ticks start and end this far outside the rim.
LETTER = (215.9, 279.4)  # Template sheet, US Letter portrait.
STAR_SLOT_REACH = 11.7  # The star's corner slots are drawn out past the corners (r = 11.5).

STYLE = """
text { font-family: Helvetica, Arial, sans-serif; fill: #000; }
.heatsink { fill: #ececec; stroke: #777; stroke-width: 0.2; }
.pin { fill: #b8b8b8; stroke: #555; stroke-width: 0.15; }
.ghost { fill: none; stroke: #666; stroke-width: 0.15; stroke-dasharray: 0.8 0.5; }
.cap { fill: none; stroke: #b36200; stroke-width: 0.25; }
.cap-flange { fill: none; stroke: #b36200; stroke-width: 0.2; stroke-dasharray: 2 1; }
.cap-root { fill: none; stroke: #b36200; stroke-width: 0.15; stroke-dasharray: 0.6 0.6; }
.star { fill: #d6e4f2; stroke: #2f5f98; stroke-width: 0.25; fill-opacity: 0.9; }
.notch { fill: #fff; stroke: none; }
.notch-edge { fill: none; stroke: #2f5f98; stroke-width: 0.25; }
.m3 { fill: #fff; stroke: #c00; stroke-width: 0.3; }
.m2 { fill: #fff; stroke: #070; stroke-width: 0.3; }
.lead { fill: #fc0; stroke: #000; stroke-width: 0.25; }
.thread { fill: none; stroke: #c00; stroke-width: 0.15; }
.head { fill: none; stroke: #c00; stroke-width: 0.15; stroke-dasharray: 0.8 0.5; }
.mark { stroke: #000; stroke-width: 0.15; }
.axis { stroke: #888; stroke-width: 0.12; stroke-dasharray: 3 0.8 0.6 0.8; }
.leader { stroke: #444; stroke-width: 0.12; }
.cut { fill: none; stroke: #000; stroke-width: 0.3; }
.tick { stroke: #000; stroke-width: 0.2; }
.box { fill: none; stroke: #000; stroke-width: 0.2; }
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
    sheet.circle(0, 0, 2 * p.cap_thread_root_radius, "cap-root")
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
        "View from the LED side. Orange: cap (Ø26.29 thread, estimated root, Ø30.48 flange); blue: 20 mm star; "
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


def drilling_templates_svg(p: HoleLayoutParameters | None = None) -> str:
    """A US Letter sheet with the cap and heatsink drilling templates at 100% scale."""
    p = p or HoleLayoutParameters()
    p.validate()
    width, height = LETTER
    sheet = _Sheet(width, height)
    left = sheet.at(width * 0.27, 84.0)
    right = sheet.at(width * 0.73, 84.0)
    cap_radius = p.cap_thread_major_diameter / 2
    heat_radius = p.heatsink_diameter / 2

    sheet.out.append(
        f'<text x="14" y="12" font-size="{TITLE_FONT_SIZE}" font-weight="bold">'
        "LED module drilling templates, SM1CP2M cap and CN40-40B heatsink</text>"
    )
    notes = [
        "Print at 100% (no fit to page) and check the 20 mm bar below against a rule. Plan view from the LED side:",
        "the same view and coordinates for both parts, with +x to the right.",
        "ALL HOLES ARE THROUGH HOLES. Plain plug taps are enough (M3 × 0.5 and M2 × 0.4); no bottoming tap is needed.",
    ]
    for i, note in enumerate(notes):
        sheet.out.append(
            f'<text x="14" y="{19 + 4.2 * i:.2f}" font-size="{SMALL_FONT_SIZE + 0.4}">{escape(note)}</text>'
        )

    def hole_marks(view: _Sheet, holes: list[tuple[Hole, float]]) -> None:
        for hole, diameter in holes:
            view.circle(hole.x, hole.y, diameter, KIND_COLOR_CLASS[hole.kind], hole.name)
            view.line(hole.x - MARK - diameter / 2, hole.y, hole.x + MARK + diameter / 2, hole.y, "mark")
            view.line(hole.x, hole.y - MARK - diameter / 2, hole.x, hole.y + MARK + diameter / 2, "mark")

    # Cap template: stuck on the LED-side (threaded) face, its crosshair over the cap's center-drill mark.
    left.circle(0, 0, p.cap_thread_major_diameter, "cut")
    left.line(-cap_radius - 3, 0, cap_radius + 3, 0, "axis")
    left.line(0, -cap_radius - 3, 0, cap_radius + 3, "axis")
    hole_marks(left, [(h, p.cap_hole_diameter(h.kind)) for h in p.holes()])
    for hole in p.holes():
        left.text(
            hole.x,
            hole.y - 4.6 if hole.kind != "lead" else hole.y + (2.6 if hole.y > 0 else -4.2),
            _short_label(hole, p, cap=True),
            size=SMALL_FONT_SIZE,
        )
    left.text(
        0,
        cap_radius + 10,
        "CAP: stick on the LED-side face; crosshair on the center-drill mark",
        size=FONT_SIZE,
        bold=True,
    )
    left.text(
        0,
        cap_radius + 7,
        "Cut on the circle (Ø26.29, the thread major). Drill through.",
        size=SMALL_FONT_SIZE,
    )
    left.text(
        0, -cap_radius - 6, "M3: Ø2.5 tap drill   M2: Ø1.6 tap drill   lead: Ø2.0", size=SMALL_FONT_SIZE
    )

    # Heatsink template: stuck on the flat (non-pin) base face; the pins stand on the far side.
    right.circle(0, 0, p.heatsink_diameter, "cut")
    _pins(p, right, "ghost")
    right.line(-heat_radius - 6, 0, heat_radius + 6, 0, "axis")
    right.line(0, -heat_radius - 6, 0, heat_radius + 6, "axis")
    pitch = p.lattice_pitch
    for i in range(-3, 3):
        c = (2 * i + 1) * pitch / 2
        for sx_, _sy in ((1, 0), (0, 1)):
            for sign in (1, -1):
                a, b = heat_radius + EDGE_TICK[0], heat_radius + EDGE_TICK[1]
                if sx_:
                    right.line(sign * a, c, sign * b, c, "tick")
                else:
                    right.line(c, sign * a, c, sign * b, "tick")
    heatsink_holes = [(h, d) for h in p.holes() if (d := p.heatsink_hole_diameter(h.kind))]
    hole_marks(right, heatsink_holes)
    for hole, _ in heatsink_holes:
        right.text(
            hole.x,
            hole.y - 4.6 if hole.kind != "lead" else hole.y + (2.6 if hole.y > 0 else -4.2),
            _short_label(hole, p, cap=False),
            size=SMALL_FONT_SIZE,
        )
    right.text(
        0,
        heat_radius + 16,
        "HEATSINK: stick on the flat base face (pins on the far side)",
        size=FONT_SIZE,
        bold=True,
    )
    right.text(
        0,
        heat_radius + 13,
        "Align the edge ticks with the pin rows seen edge-on; cut on the Ø40 circle.",
        size=SMALL_FONT_SIZE,
    )
    right.text(
        0,
        -heat_radius - 9,
        "M3 clearance: Ø3.3 (the Ø3.3 drill)   lead: Ø2.0 (no M2 holes)",
        size=SMALL_FONT_SIZE,
    )

    # Scale bar.
    sheet.out.append('<line class="box" x1="14" y1="140" x2="34" y2="140"/>')
    for x in (14, 34):
        sheet.out.append(f'<line class="box" x1="{x}" y1="138.5" x2="{x}" y2="141.5"/>')
    sheet.out.append(f'<text x="36" y="141" font-size="{SMALL_FONT_SIZE + 0.4}">20 mm</text>')
    return sheet.svg()


def _short_label(hole: Hole, p: HoleLayoutParameters, cap: bool) -> str:
    diameter = p.cap_hole_diameter(hole.kind) if cap else p.heatsink_hole_diameter(hole.kind)
    return f"{hole.kind.upper() if hole.kind != 'lead' else 'lead'} Ø{diameter:g}"

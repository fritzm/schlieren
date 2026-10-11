"""Drilling layout drawing of the mirror-cell base plate; design §10.7 and §10.9.

A plan view from above as a full-scale SVG (one user unit is 1 mm), for laying out and drilling the plywood. The
sheet is 11 × 17 in (tabloid), landscape. Hole positions are dimensioned as ordinates in the cell frame: x from the
plate centerline and y from the front edge.

The sheet is drawn with the front edge at the bottom, so +y runs up the sheet toward the rear and +x to the right,
as seen from above. The footprints of the sliding plate, the cell-adjuster plate, and the brackets are drawn
dashed as an aid to checking the layout.
"""

from xml.sax.saxutils import escape

from schlieren.parts.frame_drawing import (
    CENTER_MARK,
    FONT_SIZE,
    ORDINATE_GAP,
    SMALL_FONT_SIZE,
    STYLE,
    TEXT_GAP,
    TITLE_FONT_SIZE,
)
from schlieren.parts.mirror_cell import BRACKETS, MirrorCellParameters
from schlieren.standards import INCH
from schlieren.vendor_cad import MCMASTER_8681N11_WIDTH

PAGE_WIDTH = 17.0 * INCH
PAGE_HEIGHT = 11.0 * INCH
PLATE_TOP = 38.0  # Sheet y of the plate's rear edge.


def figure(value: float, signed: bool = False) -> str:
    """A dimension to the micron, without trailing zeros: the inch-derived values (69.85, 130.175) show exactly."""
    text = f"{value:+.3f}" if signed else f"{value:.3f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def base_plate_holes(p: MirrorCellParameters) -> dict[str, tuple[float, float, float]]:
    """name -> (x from the centerline, y from the front edge, diameter), for every hole in the base plate."""
    holes = {}
    for (station, side), (x, y) in p.qr_screw_positions().items():
        holes[f"QR {station} {side}"] = (x, y, p.qr_clearance_hole)
    for side, sign in BRACKETS.items():
        for i, y in enumerate(p.base_hole_y(), 1):
            holes[f"bracket {side} {i}"] = (p.bracket_center_x(sign), y, p.bracket_hole_diameter)
    return holes


def base_plate_drawing_svg(p: MirrorCellParameters | None = None) -> str:
    """The dimensioned drilling layout of the base plate, as SVG text."""
    p = p or MirrorCellParameters()
    p.validate()
    width, depth = p.plate_width, p.base_depth
    left = (PAGE_WIDTH - width) / 2  # Sheet x of the plate's left edge.
    center = left + width / 2
    bottom = PLATE_TOP + depth  # Sheet y of the front edge.
    right = left + width
    holes = base_plate_holes(p)
    out: list[str] = []

    def sx(x: float) -> float:
        return center + x

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

    def footprint(
        x0: float, x1: float, y0: float, y1: float, label: str, label_x: float, label_y: float
    ) -> None:
        out.append(
            f'<rect class="hidden" x="{sx(x0):.3f}" y="{sy(y1):.3f}" width="{x1 - x0:.3f}" height="{y1 - y0:.3f}"/>'
        )
        text(sx(label_x), sy(label_y), label, size=SMALL_FONT_SIZE)

    def x_ordinate(x: float, from_y: float) -> None:
        """Extension line from the hole down past the front edge, with its figure."""
        line(sx(x), sy(from_y), sx(x), bottom + ORDINATE_GAP, "extension")
        text(
            sx(x) + FONT_SIZE * 0.35,
            bottom + ORDINATE_GAP + TEXT_GAP,
            figure(x, signed=True),
            "end",
            turn=-90,
        )

    def y_ordinate(y: float, from_x: float) -> None:
        """Extension line from the hole out past the nearer side edge, with its figure."""
        on_left = from_x <= 0
        end = left - ORDINATE_GAP if on_left else right + ORDINATE_GAP
        line(sx(from_x), sy(y), end, sy(y), "extension")
        figure_x = end - TEXT_GAP if on_left else end + TEXT_GAP
        text(figure_x, sy(y) + FONT_SIZE * 0.35, figure(y), "end" if on_left else "start")

    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_WIDTH:.1f}mm" height="{PAGE_HEIGHT:.1f}mm" '
        f'viewBox="0 0 {PAGE_WIDTH:.1f} {PAGE_HEIGHT:.1f}">'
    )
    out.append(f"<style>{STYLE}</style>")
    out.append(f'<rect width="{PAGE_WIDTH:.1f}" height="{PAGE_HEIGHT:.1f}" fill="#fff"/>')

    text(left, 9, "Mirror-cell base plate: drilling layout, seen from above", "start", TITLE_FONT_SIZE)
    text(
        left,
        15.5,
        f"{width:g} × {depth:g} × {p.base_thickness:g} mm (11.5 × 7.0 × 1/2 in) Baltic birch. Four Ø{p.qr_clearance_hole:g} mm "
        f"through holes, countersunk 90° to Ø{p.qr_countersink_diameter:g} mm on this (top) face, for the M4 quick-release "
        "plate screws;",
        "start",
        SMALL_FONT_SIZE,
    )
    text(
        left,
        19.5,
        f"four Ø{p.bracket_hole_diameter:g} mm through holes for the bracket screws. Dimensions in mm: x from the plate "
        "centerline, y from the front edge.",
        "start",
        SMALL_FONT_SIZE,
    )
    text(
        left,
        24,
        "Full scale when printed at 100% on 11 × 17 in: check the plate width against a rule before using the sheet "
        "as a template.",
        "start",
        SMALL_FONT_SIZE,
    )
    text(
        left,
        28.5,
        "Transfer to the sliding plate: with the plate's camera face against the underside, spot through the Ø4.5 mm "
        "holes and tap M4 × 0.7 (3.3 mm tap drill).",
        "start",
        SMALL_FONT_SIZE,
    )

    out.append(f'<rect class="outline" x="{left}" y="{PLATE_TOP}" width="{width:.3f}" height="{depth:.3f}"/>')
    text(sx(width / 2 - 2), sy(depth - 2) + SMALL_FONT_SIZE, "rear edge", "end", SMALL_FONT_SIZE)
    text(sx(width / 2 - 2), sy(2), "front edge", "end", SMALL_FONT_SIZE)

    # Dashed footprints, as an aid to checking the layout.
    qr_half = p.qr_base_width / 2
    footprint(
        -qr_half, qr_half, 0.0, p.qr_plate_length, "sliding plate (underside)", 0.0, p.qr_plate_length - 12
    )
    fixed_front, fixed_rear = p.fixed_plate_front_y, p.fixed_plate_rear_y
    footprint(-width / 2, width / 2, fixed_front, fixed_rear, "cell-adjuster plate", 0.0, fixed_rear + 4)
    for sign in BRACKETS.values():
        x = p.bracket_center_x(sign)
        half = MCMASTER_8681N11_WIDTH / 2
        footprint(
            x - half,
            x + half,
            fixed_front - 3.0 * INCH,
            fixed_front,
            "bracket",
            x,
            fixed_front - 3.0 * INCH + 5,
        )

    line(center, PLATE_TOP - ORDINATE_GAP, center, bottom + ORDINATE_GAP, "centerline")
    text(center + FONT_SIZE * 0.35, bottom + ORDINATE_GAP + TEXT_GAP, "0 CL", "end", turn=-90)

    for edge in (-width / 2, width / 2):
        x_ordinate(edge, 0.0)
    for edge in (0.0, depth):
        y_ordinate(edge, -width / 2)

    done_x: set[float] = set()
    for x, y, _ in holes.values():
        if round(x, 3) not in done_x:  # One extension line per column of holes.
            x_ordinate(x, min(hy for hx, hy, _ in holes.values() if round(hx, 3) == round(x, 3)))
            done_x.add(round(x, 3))
        y_ordinate(y, x)

    for name, (x, y, diameter) in holes.items():
        if name.startswith("QR"):
            out.append(
                f'<circle class="hidden" cx="{sx(x):.3f}" cy="{sy(y):.3f}" r="{p.qr_countersink_diameter / 2:.3f}"/>'
            )
        out.append(
            f'<circle class="hole" data-hole="{escape(name)}" cx="{sx(x):.3f}" cy="{sy(y):.3f}" '
            f'r="{diameter / 2:.3f}"/>'
        )
        line(sx(x) - CENTER_MARK, sy(y), sx(x) + CENTER_MARK, sy(y), "mark")
        line(sx(x), sy(y) - CENTER_MARK, sx(x), sy(y) + CENTER_MARK, "mark")
        label_y = sy(y) + CENTER_MARK + SMALL_FONT_SIZE + 0.5
        text(sx(x), label_y, name, size=SMALL_FONT_SIZE)

    out.append("</svg>")
    return "\n".join(out) + "\n"

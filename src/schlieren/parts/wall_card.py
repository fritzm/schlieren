"""Wall fiducial cards: a flat sheet printed at true scale with a 3 x 3 grid of cross marks (centre left blank),
a ringed cross at the top-left corner to fix orientation, and a millimetre ruler along the bottom edge.

The card is described as drawing primitives in millimetres (y down, origin at the top-left of the sheet) and
rendered by `to_svg` (true scale in the file's own units), `to_pdf` (a single-page vector PDF, no
dependencies) and `to_annotated_svg` (a dimensioned preview, not for printing). The marks' positions are the
measurable quantity, so they are named parameters and tested; the sheet must be printed at 100 %.
"""

from dataclasses import dataclass
from typing import NamedTuple

MM_PER_INCH = 25.4
PT_PER_MM = 72 / MM_PER_INCH
MARK_STROKE = 0.6  # mm
RULER_STROKE = 0.35  # mm
RING_RADIUS = 4.5  # mm, orientation ring around the top-left cross
TEXT_SIZE = 3.2  # mm
RULER_LABEL_STEP = 50  # mm
RULER_TICK_STEP = 10  # mm
ANNOTATION_COLOR = "#1f5fbf"
HELVETICA_DIGIT_WIDTH = 0.556  # em; the ruler labels are digits only


class Line(NamedTuple):
    x1: float
    y1: float
    x2: float
    y2: float
    width: float


class Circle(NamedTuple):
    cx: float
    cy: float
    r: float
    width: float


class Label(NamedTuple):
    x: float
    y: float  # baseline
    text: str
    anchor: str  # "start", "middle" or "end"


@dataclass(frozen=True)
class WallCardParameters:
    name: str
    width: float  # mm, sheet
    height: float  # mm, sheet
    inset: float  # mm, corner-mark centres from the sheet edges
    arm: float = 6.0  # mm, half-length of each cross arm
    ruler_start: float = 10.0  # mm from the left edge
    ruler_end: float = 270.0
    ruler_baseline: float = 0.0  # mm from the top; 0 = height - 7 (clear of a typical printer margin)
    ruler_up: bool = True  # ticks rise from the baseline

    def baseline(self) -> float:
        return self.ruler_baseline or self.height - 7

    def mark_xs(self) -> tuple[float, float, float]:
        return (self.inset, self.width / 2, self.width - self.inset)

    def mark_ys(self) -> tuple[float, float, float]:
        return (self.inset, self.height / 2, self.height - self.inset)

    def mark_centres(self) -> list[tuple[float, float]]:
        """The eight mark centres, row by row; the sheet centre is left blank."""
        xs, ys = self.mark_xs(), self.mark_ys()
        return [(x, y) for y in ys for x in xs if not (x == xs[1] and y == ys[1])]

    def validate(self) -> None:
        if not (0 < self.inset < self.width / 2 and self.inset < self.height / 2):
            raise ValueError("marks must lie inside the sheet, left of and above its centre")
        if not 0 <= self.ruler_start < self.ruler_end <= self.width:
            raise ValueError("ruler must lie within the sheet width")
        if self.baseline() > self.height:
            raise ValueError("ruler baseline must lie within the sheet height")


LETTER = WallCardParameters("wall-card-letter", 11 * MM_PER_INCH, 8.5 * MM_PER_INCH, inset=20)
SQUARE_250 = WallCardParameters(
    "wall-card-250", 250, 250, inset=15, ruler_start=0, ruler_end=250, ruler_baseline=250
)
CARDS = {"letter": LETTER, "250": SQUARE_250}


def marks(p: WallCardParameters) -> list[Line | Circle]:
    """The crosses, plus the orientation ring on the top-left one."""
    items: list[Line | Circle] = []
    for x, y in p.mark_centres():
        items.append(Line(x - p.arm, y, x + p.arm, y, MARK_STROKE))
        items.append(Line(x, y - p.arm, x, y + p.arm, MARK_STROKE))
    items.append(Circle(p.inset, p.inset, RING_RADIUS, MARK_STROKE))
    return items


def ruler(p: WallCardParameters) -> tuple[list[Line], list[Label]]:
    """Ticks every 10 mm (long every 50) and numbers every 50 mm, measured from the left edge of the sheet."""
    base = p.baseline()
    sign = -1 if p.ruler_up else 1
    lines = [Line(p.ruler_start, base, p.ruler_end, base, RULER_STROKE)] if p.ruler_start > 0 else []
    labels = []
    for mm in range(int(p.ruler_start), int(p.ruler_end) + 1, RULER_TICK_STEP):
        length = 6 if mm % RULER_LABEL_STEP == 0 else 3
        lines.append(Line(mm, base, mm, base + sign * length, RULER_STROKE))
        if mm % RULER_LABEL_STEP == 0 and mm > 0:
            anchor = "end" if mm == p.width else "middle"
            labels.append(Label(mm, base + sign * 7.5, str(mm), anchor))
        elif mm == 0:
            labels.append(Label(0.6, base + sign * 7.5, "0", "start"))
    return lines, labels


def _num(v: float) -> str:
    return f"{v:.3f}".rstrip("0").rstrip(".")


def _svg_body(p: WallCardParameters) -> str:
    ticks, labels = ruler(p)
    out = [f'<g stroke="#000" stroke-width="{MARK_STROKE}" fill="none">']
    for item in marks(p):
        if isinstance(item, Line):
            out.append(
                f'<line x1="{_num(item.x1)}" y1="{_num(item.y1)}" x2="{_num(item.x2)}" y2="{_num(item.y2)}"/>'
            )
        else:
            out.append(f'<circle cx="{_num(item.cx)}" cy="{_num(item.cy)}" r="{_num(item.r)}"/>')
    out.append(f'<g stroke-width="{RULER_STROKE}">')
    out.extend(
        f'<line x1="{_num(t.x1)}" y1="{_num(t.y1)}" x2="{_num(t.x2)}" y2="{_num(t.y2)}"/>' for t in ticks
    )
    out.append("</g></g>")
    out.append(
        f'<g font-family="Helvetica,Arial,sans-serif" font-size="{TEXT_SIZE}" fill="#000" stroke="none">'
    )
    out.extend(
        f'<text x="{_num(lab.x)}" y="{_num(lab.y)}" text-anchor="{lab.anchor}">{lab.text}</text>'
        for lab in labels
    )
    out.append("</g>")
    return "\n".join(out)


def to_svg(p: WallCardParameters) -> str:
    """True-scale SVG: width and height in mm equal the sheet, user units are millimetres."""
    w, h = _num(p.width), _num(p.height)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">
<title>Wall card {w} x {h} mm, true scale: print at 100 %</title>
<rect x="0" y="0" width="{w}" height="{h}" fill="#fff"/>
{_svg_body(p)}
</svg>
"""


def to_annotated_svg(p: WallCardParameters) -> str:
    """A dimensioned preview (sheet size, mark spacing, print instructions); for viewing, not printing."""
    margin, extra, c = 26.0, 28.0, ANNOTATION_COLOR
    xs, ys = p.mark_xs(), p.mark_ys()
    w, h = p.width, p.height
    total_w, total_h = w + 2 * margin, h + 2 * margin + extra
    ann: list[str] = []

    def hdim(x1: float, x2: float, y: float, text: str) -> None:
        ann.append(
            f'<line x1="{_num(x1)}" y1="{y}" x2="{_num(x2)}" y2="{y}" stroke="{c}" stroke-width="0.3"/>'
            f'<text x="{_num((x1 + x2) / 2)}" y="{y - 1.3}" text-anchor="middle">{text}</text>'
        )

    def vdim(y1: float, y2: float, x: float, text: str) -> None:
        mid = _num((y1 + y2) / 2)
        ann.append(
            f'<line x1="{x}" y1="{_num(y1)}" x2="{x}" y2="{_num(y2)}" stroke="{c}" stroke-width="0.3"/>'
            f'<text transform="rotate(-90 {x - 1.3} {mid})" x="{x - 1.3}" y="{mid}" text-anchor="middle">{text}</text>'
        )

    hdim(0, w, -6, f"{w:.1f} mm")
    hdim(xs[0], xs[2], -14, f"{xs[2] - xs[0]:.1f} mm between corner marks")
    vdim(0, h, -6, f"{h:.1f} mm")
    vdim(ys[0], ys[2], -14, f"{ys[2] - ys[0]:.1f} mm between corner marks")
    hdim(0, p.inset, h + 7, f"{p.inset:g}")
    ann.append(
        f'<text x="{_num(p.inset + 8)}" y="{_num(p.inset - 7)}">ringed cross: orientation mark (top left)</text>'
    )
    notes = [
        f"Print at 100 % (Actual size) on a {w:.1f} x {h:.1f} mm sheet. Do not use Fit to page.",
        f"Mark centres: x = {', '.join(_num(x) for x in xs)}; y = {', '.join(_num(y) for y in ys)} mm; "
        "the centre is left blank. Eight marks.",
        f"Ruler along the bottom: ticks every {RULER_TICK_STEP} mm, numbers every {RULER_LABEL_STEP}, "
        "measured from the left edge of the sheet.",
        "After printing, measure the real distance between two corner marks with a ruler and write it on the sheet.",
    ]
    detail = "".join(f'<text y="{4 + 6 * i}">{t}</text>' for i, t in enumerate(notes))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{total_w:.1f}mm" height="{total_h:.1f}mm" viewBox="{-margin:g} {-margin:g} {total_w:.1f} {total_h:.1f}">
<rect x="{-margin:g}" y="{-margin:g}" width="{total_w:.1f}" height="{total_h:.1f}" fill="#eef0f1"/>
<rect x="0" y="0" width="{_num(w)}" height="{_num(h)}" fill="#fff" stroke="#888" stroke-width="0.3"/>
{_svg_body(p)}
<g fill="{c}" font-family="Helvetica,Arial,sans-serif" font-size="{TEXT_SIZE}">
{"".join(ann)}
<g transform="translate(0 {_num(h + 14)})">{detail}</g>
</g>
</svg>
"""


def to_pdf(p: WallCardParameters) -> bytes:
    """A single-page vector PDF of the sheet at true scale (1 mm = 72/25.4 pt), built without a PDF library."""
    ticks, labels = ruler(p)
    k = 4 * (2**0.5 - 1) / 3  # cubic Bezier circle constant
    ops = [f"{PT_PER_MM:.6f} 0 0 {-PT_PER_MM:.6f} 0 {p.height * PT_PER_MM:.4f} cm", "0 0 0 RG 0 0 0 rg 0 J"]

    def line(item: Line) -> str:
        return f"{_num(item.width)} w {_num(item.x1)} {_num(item.y1)} m {_num(item.x2)} {_num(item.y2)} l S"

    for item in marks(p):
        if isinstance(item, Line):
            ops.append(line(item))
        else:
            cx, cy, r = item.cx, item.cy, item.r
            ops.append(
                f"{_num(item.width)} w {_num(cx + r)} {_num(cy)} m "
                f"{_num(cx + r)} {_num(cy + k * r)} {_num(cx + k * r)} {_num(cy + r)} {_num(cx)} {_num(cy + r)} c "
                f"{_num(cx - k * r)} {_num(cy + r)} {_num(cx - r)} {_num(cy + k * r)} {_num(cx - r)} {_num(cy)} c "
                f"{_num(cx - r)} {_num(cy - k * r)} {_num(cx - k * r)} {_num(cy - r)} {_num(cx)} {_num(cy - r)} c "
                f"{_num(cx + k * r)} {_num(cy - r)} {_num(cx + r)} {_num(cy - k * r)} {_num(cx + r)} {_num(cy)} c S"
            )
    ops.extend(line(t) for t in ticks)
    for lab in labels:
        width = HELVETICA_DIGIT_WIDTH * TEXT_SIZE * len(lab.text)
        x = lab.x - {"start": 0, "middle": width / 2, "end": width}[lab.anchor]
        # The page is flipped to y-down mm, so the text matrix flips it back upright.
        ops.append(f"BT /F1 {TEXT_SIZE} Tf 1 0 0 -1 {_num(x)} {_num(lab.y)} Tm ({lab.text}) Tj ET")
    stream = "\n".join(ops).encode("ascii")
    media = f"[0 0 {p.width * PT_PER_MM:.2f} {p.height * PT_PER_MM:.2f}]"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox {media} /Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >>".encode(),
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return bytes(out)

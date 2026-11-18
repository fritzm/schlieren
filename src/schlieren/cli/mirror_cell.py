"""Show or render the mirror cell model, or write the base-plate and mirror-plate layouts."""

import argparse
from pathlib import Path

from schlieren.cli._common import (
    add_figure_option,
    add_show_option,
    render,
    show,
    with_suffix_name,
    write_text,
)
from schlieren.parts.mirror_cell import MirrorCellParameters, adjuster_section, build_mirror_cell_assembly
from schlieren.parts.mirror_cell_drawing import base_plate_drawing_svg, mirror_plate_drawing_svg

DEFAULT_FIGURE = Path("docs/design/figures/mirror-cell.png")
DEFAULT_DRAWING = Path("docs/design/figures/mirror-cell-base-plate.svg")
MIRROR_PLATE_DRAWING_NAME = "mirror-cell-mirror-plate.svg"  # Beside the base-plate drawing.
FIGURE_VIEW_DIRECTION = (-0.8, -1.0, 0.6)  # From the front (mirror side), left and above.
BELOW_VIEW_DIRECTION = (-0.6, -0.9, -0.8)  # From the front, left and below: the sliding plate.
ADJUSTER_VIEW_DIRECTION = (-1.0, 0.45, 0.35)  # From the cut face, behind and above: the adjuster stack.
ADJUSTER_STATION = "top"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(parser)
    add_figure_option(
        parser,
        DEFAULT_FIGURE,
        "the front view, plus the underside and adjuster section with -below and -adjuster suffixes",
    )
    parser.add_argument(
        "--drawing",
        type=Path,
        nargs="?",
        const=DEFAULT_DRAWING,
        help=f"Write the base-plate drilling layout, full scale on 11 × 17 in (default path: {DEFAULT_DRAWING}), "
        "and the mirror-plate layout beside it",
    )
    args = parser.parse_args()
    p = MirrorCellParameters()
    if args.drawing:
        write_text(args.drawing, base_plate_drawing_svg(p))
        write_text(
            args.drawing.with_name(MIRROR_PLATE_DRAWING_NAME),
            mirror_plate_drawing_svg(p),
        )
    cell = build_mirror_cell_assembly(p)
    if args.figure:
        render(cell, args.figure, FIGURE_VIEW_DIRECTION)
        views = (
            ("-below", cell, BELOW_VIEW_DIRECTION),
            ("-adjuster", adjuster_section(cell, p, ADJUSTER_STATION), ADJUSTER_VIEW_DIRECTION),
        )
        for suffix, shape, direction in views:
            render(shape, with_suffix_name(args.figure, suffix), direction)
    if args.show:
        show(cell)


if __name__ == "__main__":
    main()

"""Show or render the mirror cell model, or write the base-plate drilling layout (design §10)."""

import argparse
from pathlib import Path

from schlieren.parts.mirror_cell import MirrorCellParameters, build_mirror_cell_assembly
from schlieren.parts.mirror_cell_drawing import base_plate_drawing_svg

DEFAULT_FIGURE = Path("docs/design/figures/mirror-cell.png")
DEFAULT_DRAWING = Path("docs/design/figures/mirror-cell-base-plate.svg")
FIGURE_VIEW_DIRECTION = (-0.8, -1.0, 0.6)  # From the front (mirror side), left and above.
REAR_VIEW_DIRECTION = (0.8, 1.0, 0.6)  # From behind, right and above: the knobs.
BELOW_VIEW_DIRECTION = (-0.6, -0.9, -0.8)  # From the front, left and below: the sliding plate.


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show", action="store_true", help="Display the model in OCP CAD Viewer")
    parser.add_argument(
        "--figure",
        type=Path,
        nargs="?",
        const=DEFAULT_FIGURE,
        help=f"Render the front, rear, and underside design-doc views (default path: {DEFAULT_FIGURE}; the others get "
        "-rear and -below suffixes)",
    )
    parser.add_argument(
        "--drawing",
        type=Path,
        nargs="?",
        const=DEFAULT_DRAWING,
        help=f"Write the base-plate drilling layout, full scale on 11 × 17 in (default path: {DEFAULT_DRAWING})",
    )
    args = parser.parse_args()
    p = MirrorCellParameters()
    if args.drawing:
        args.drawing.parent.mkdir(parents=True, exist_ok=True)
        args.drawing.write_text(base_plate_drawing_svg(p), encoding="utf-8")
        print(args.drawing)
    cell = build_mirror_cell_assembly(p)
    if args.figure:
        from schlieren.render import render_figure

        args.figure.parent.mkdir(parents=True, exist_ok=True)
        render_figure(cell, args.figure, FIGURE_VIEW_DIRECTION, perspective=True)
        for suffix, direction in (("-rear", REAR_VIEW_DIRECTION), ("-below", BELOW_VIEW_DIRECTION)):
            path = args.figure.with_name(f"{args.figure.stem}{suffix}{args.figure.suffix}")
            render_figure(cell, path, direction, perspective=True)
            print(path)
        print(args.figure)
    if args.show:
        from ocp_vscode import show

        show(cell)


if __name__ == "__main__":
    main()

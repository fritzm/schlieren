"""Build/export the prototype shoe; optionally write its design-doc figure or display in OCP CAD Viewer."""

import argparse
from pathlib import Path

from schlieren.cad import EXPORTERS
from schlieren.parts.rail_shoe import build_rail_shoe, viewer_assembly

DEFAULT_FIGURE = Path("docs/design/figures/rail-shoe.png")
FIGURE_VIEW_DIRECTION = (1.0, 1.0, 0.8)  # From above the nut-ear side: shows the split, ears, and nut pocket.


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--show", action="store_true", help="Display shoe and reference parts in OCP CAD Viewer"
    )
    parser.add_argument("--output", type=Path, default=Path("exports"))
    parser.add_argument(
        "--figure",
        type=Path,
        nargs="?",
        const=DEFAULT_FIGURE,
        help=f"Render the design-doc figure, shoe on its rail and post (default path: {DEFAULT_FIGURE})",
    )
    args = parser.parse_args()
    shoe = build_rail_shoe()
    for kind in ("step", "stl"):
        destination = args.output / kind / f"rail_shoe.{kind}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        EXPORTERS[kind](shoe, destination)
        print(destination)
    if args.figure:
        from schlieren.render import render_figure

        args.figure.parent.mkdir(parents=True, exist_ok=True)
        render_figure(viewer_assembly(shoe), args.figure, FIGURE_VIEW_DIRECTION, perspective=True)
        print(args.figure)
    if args.show:
        from ocp_vscode import show

        show(viewer_assembly(shoe))


if __name__ == "__main__":
    main()

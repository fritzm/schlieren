"""Build/export the prototype shoe; optionally write its design-doc figure or display in OCP CAD Viewer."""

import argparse
from pathlib import Path

from schlieren.cli._common import (
    add_figure_option,
    add_output_option,
    add_show_option,
    export_models,
    render,
    show,
)
from schlieren.parts.rail_shoe import build_rail_shoe, viewer_assembly

DEFAULT_FIGURE = Path("docs/design/figures/rail-shoe.png")
FIGURE_VIEW_DIRECTION = (1.0, 1.0, 0.8)  # From above the nut-ear side: shows the split, ears, and nut pocket.


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(parser, "Display shoe and reference parts in OCP CAD Viewer")
    add_output_option(parser)
    add_figure_option(parser, DEFAULT_FIGURE, "the shoe on its rail and post")
    args = parser.parse_args()
    shoe = build_rail_shoe()
    export_models({"rail_shoe": shoe}, args.output)
    if args.figure:
        render(viewer_assembly(shoe), args.figure, FIGURE_VIEW_DIRECTION)
    if args.show:
        show(viewer_assembly(shoe))


if __name__ == "__main__":
    main()

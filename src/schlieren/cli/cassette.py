"""Export cassette base and one clamp bar; optionally render or view the assembled cassette."""

import argparse
from pathlib import Path

from build123d import Pos

from schlieren.cad import assembly, place
from schlieren.cli._common import (
    add_figure_option,
    add_output_option,
    add_show_option,
    export_models,
    render,
    show,
)
from schlieren.parts.carriage import CarriageParameters, build_carriage
from schlieren.parts.cassette import build_cassette, build_cassette_assembly, build_clamp_bar

DEFAULT_FIGURE = Path("docs/design/figures/cassette.png")
FIGURE_VIEW_DIRECTION = (0.5, -0.9, 1.0)  # From the front face: cleats, clamp bars, and the aperture.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(parser, "Display the assembled cassette in OCP CAD Viewer")
    parser.add_argument("--with-carriage", action="store_true", help="Include carriage in viewer only")
    parser.add_argument("--travel", type=float, default=0.0, help="Viewer cassette/carriage travel in mm")
    add_output_option(parser)
    add_figure_option(parser, DEFAULT_FIGURE, "the assembled cassette")
    args = parser.parse_args()
    p = CarriageParameters()
    if not -p.working_half_travel <= args.travel <= p.working_half_travel:
        parser.error("Travel must be within ±5 mm")
    export_models({"cassette_base": build_cassette(), "cassette_clamp_bar": build_clamp_bar()}, args.output)
    if args.figure:
        render(build_cassette_assembly(), args.figure, FIGURE_VIEW_DIRECTION)
    if args.show:
        cassette = build_cassette_assembly()
        if args.with_carriage:
            carriage = build_carriage(p, travel=args.travel)
            seated = Pos(0, args.travel, p.plate_thickness + p.datum_projection)
            show(assembly(carriage.label, [*carriage.children, place(seated, cassette)]))
        else:
            show(cassette)


if __name__ == "__main__":
    main()

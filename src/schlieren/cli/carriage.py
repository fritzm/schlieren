"""Export base, guide frame, keeper, and a paired plunger print layout; optionally render or show it on its post."""

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
from schlieren.parts.carriage import CarriageParameters, build_carriage, build_print_layout

DEFAULT_FIGURE = Path("docs/design/figures/cutoff.png")
FIGURE_VIEW_DIRECTION = (1.0, 0.9, 0.7)  # From the mirror side, outboard and above: carriage, cassette, knob.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(
        parser, "Display the assembled carriage on its post, shoe, and hardware in OCP CAD Viewer"
    )
    add_output_option(parser)
    parser.add_argument("--travel", type=float, default=0.0)
    parser.add_argument("--retract", type=float, default=0.0)
    parser.add_argument(
        "--keeper-side-thickness",
        type=float,
        default=CarriageParameters().keeper_side_thickness,
        help="keeper side-member thickness in mm (5 for the stiffer fallback keeper)",
    )
    add_figure_option(parser, DEFAULT_FIGURE, "the carriage with a seated cassette")
    args = parser.parse_args()
    params = CarriageParameters(keeper_side_thickness=args.keeper_side_thickness)
    # The exports use a separate, pose-independent print layout; the viewer shows the assembly.
    layout = build_print_layout(params)
    export_models({f"carriage_{name}": part for name, part in layout.items()}, args.output)
    if args.figure:
        from schlieren.parts.cassette import build_cassette_assembly

        figure_carriage = build_carriage(params, include_support=True, include_hardware=True)
        seated = Pos(0, 0, params.plate_thickness + params.datum_projection)
        figure = assembly(
            figure_carriage.label, [*figure_carriage.children, place(seated, build_cassette_assembly())]
        )
        render(figure, args.figure, FIGURE_VIEW_DIRECTION)
    if args.show:
        show(
            build_carriage(
                params,
                travel=args.travel,
                retract=args.retract,
                include_support=True,
                include_hardware=True,
            )
        )


if __name__ == "__main__":
    main()

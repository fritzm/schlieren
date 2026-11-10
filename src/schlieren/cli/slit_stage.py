"""Export the stage-mounted slit head parts (§7); print its layout; optionally render or show it."""

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
from schlieren.parts.slit_stage import (
    SlitStageParameters,
    build_pedestal,
    build_slit_stage_assembly,
    build_stage_plate,
    build_toe_bar,
)

DEFAULT_FIGURE = Path("docs/design/figures/slit-stage.png")
# From the mirror side, above and to the right: the blades, toe bars, and micrometer.
FIGURE_VIEW_DIRECTION = (0.9, 1.0, 0.6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(parser, "Display the head on its post and shoe in OCP CAD Viewer")
    parser.add_argument(
        "--rotation", type=float, default=0.0, help="Degrees about the optical axis; 0 = horizontal slit"
    )
    add_output_option(parser)
    add_figure_option(parser, DEFAULT_FIGURE, "the head on its post and shoe")
    args = parser.parse_args()
    p = SlitStageParameters()
    p.validate()
    print(f"Table edge {p.table_edge:.2f} mm from the slit center; toe screws {p.toe_z:.1f} mm back from it")
    print(f"Beam clearance to the stage and pedestal edges: {p.beam_clearance:.2f} mm")
    print(f"Micrometer tip {p.micrometer_reach:.1f} mm from the optical axis (±{6.5} mm of travel)")
    print(
        f"Baffle clamps the spigot's last {p.baffle.spigot_extension} mm past the ring and runs {p.baffle.length} mm back"
    )
    parts = {
        "slit_stage_plate": build_stage_plate(p),
        "slit_stage_pedestal": build_pedestal(p),
        "slit_stage_toe_bar": build_toe_bar(p),
    }
    export_models(parts, args.output)
    if args.figure:
        render(build_slit_stage_assembly(p), args.figure, FIGURE_VIEW_DIRECTION)
    if args.show:
        show(build_slit_stage_assembly(p, args.rotation))


if __name__ == "__main__":
    main()

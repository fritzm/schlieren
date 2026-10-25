"""Export the LED-module drilling fixture's printed parts; optionally write its design-doc figure or show it."""

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
from schlieren.parts.led_drill_fixture import (
    CAP,
    HEATSINK,
    DrillFixtureParameters,
    build_bore_coupon,
    build_bushing_plate,
    build_fixture_assembly,
    build_fixtures_side_by_side,
    build_nest,
)

DEFAULT_FIGURE = Path("docs/design/figures/led-drill-fixture.png")
FIGURE_VIEW_DIRECTION = (0.9, -1.0, 0.8)  # From the front and above, both nests open to the viewer.


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(parser, "Display the cap setup (or --heatsink) in OCP CAD Viewer")
    parser.add_argument("--heatsink", action="store_true", help="Show the heatsink setup")
    add_output_option(parser)
    add_figure_option(parser, DEFAULT_FIGURE, "the cap and heatsink setups side by side")
    args = parser.parse_args()
    p = DrillFixtureParameters()
    p.validate()
    print(f"Plate web {p.web():.2f} mm; rib to pin gap {p.rib_clears_pins():.2f} mm")
    export_models(
        {
            "led_drill_plate": build_bushing_plate(p),
            "led_drill_cap_nest": build_nest(p, CAP),
            "led_drill_heatsink_nest": build_nest(p, HEATSINK),
            "led_drill_bore_coupon": build_bore_coupon(p),
        },
        args.output,
    )
    if args.figure:
        render(build_fixtures_side_by_side(p), args.figure, FIGURE_VIEW_DIRECTION)
    if args.show:
        show(build_fixture_assembly(p, HEATSINK if args.heatsink else CAP))


if __name__ == "__main__":
    main()

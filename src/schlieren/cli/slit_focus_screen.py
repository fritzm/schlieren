"""Export the experimental ground-glass focus screen fixture and its retaining ring; optionally show it."""

import argparse

from schlieren.cli._common import add_output_option, add_show_option, export_models, show
from schlieren.parts.slit_focus_screen import (
    FocusScreenParameters,
    build_focus_screen_assembly,
    build_focus_screen_fixture,
)
from schlieren.parts.slit_focus_target import build_retaining_ring


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(parser, "Display the focus screen on its post and shoe in OCP CAD Viewer")
    add_output_option(parser)
    args = parser.parse_args()
    p = FocusScreenParameters()
    p.validate()
    print(
        f"Counterbore Ø{p.counterbore_diameter:.2f} x {p.counterbore_depth:.2f} mm; gasket compression "
        f"{p.gasket_compression(p.glass_thickness_max):.0%} (thick glass) to "
        f"{p.gasket_compression(p.glass_thickness_min):.0%} (thin glass)"
    )
    parts = {
        "slit_focus_screen": build_focus_screen_fixture(p),
        "slit_focus_screen_ring": build_retaining_ring(p.target),
    }
    export_models(parts, args.output)
    if args.show:
        show(build_focus_screen_assembly(p))


if __name__ == "__main__":
    main()

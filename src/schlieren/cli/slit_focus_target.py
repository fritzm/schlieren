"""Export the experimental slit focus target and its retaining ring; optionally show it on the post."""

import argparse

from schlieren.cli._common import add_output_option, add_show_option, export_models, show
from schlieren.parts.slit_focus_target import (
    FocusTargetParameters,
    build_focus_target,
    build_focus_target_assembly,
    build_retaining_ring,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(parser, "Display the focus target on its post and shoe in OCP CAD Viewer")
    add_output_option(parser)
    args = parser.parse_args()
    p = FocusTargetParameters()
    p.validate()
    print(f"Paper plane {-p.stage.plate_back:.1f} mm ahead of the shoulder's seat on the stage plate's rear")
    print(
        f"Barrel {p.barrel_length:.1f} mm long; ring screws reach {p.screw_engagement:.2f} mm into the inserts"
    )
    parts = {
        "slit_focus_target": build_focus_target(p),
        "slit_focus_target_ring": build_retaining_ring(p),
    }
    export_models(parts, args.output)
    if args.show:
        show(build_focus_target_assembly(p))


if __name__ == "__main__":
    main()

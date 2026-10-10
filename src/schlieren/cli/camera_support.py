"""Show or render the lens cradle and phone rest model (design §§9.4-9.8)."""

import argparse
from pathlib import Path

from build123d import Pos

from schlieren.cad import assembly, labeled
from schlieren.cli._common import (
    add_figure_option,
    add_output_option,
    add_show_option,
    export_models,
    render,
    show,
)
from schlieren.parts.camera_support import (
    build_camera_support_assembly,
    build_collar_for_print,
    build_cradle_shoe_for_print,
    build_cradle_yoke_for_print,
    build_phone_rest_for_print,
)

DEFAULT_FIGURE = Path("docs/design/figures/camera-support.png")
FIGURE_VIEW_DIRECTION = (
    1.0,
    0.8,
    0.6,
)  # From the mirror side, outboard and above: both yokes and the rest arm.
# Name -> (view direction toward the viewer, include the cutoff station, perspective).
VIEWS = {
    "rear": ((0.9, -1.0, 0.75), True, True),  # From behind and to the right, as the operator sees it.
    "front": ((-0.9, 1.0, 0.6), False, True),  # From the mirror side and to the left.
    "along-axis": ((0.0, 1.0, 0.0), False, False),  # From the mirror, down the optical axis.
    "top": ((0.0, -0.001, 1.0), True, False),
    "below": ((0.9, -1.0, -0.6), False, True),  # From behind and below.
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(parser)
    parser.add_argument("--no-cutoff", action="store_true", help="Leave the cutoff station out of --show")
    parser.add_argument(
        "--yoke",
        action="store_true",
        help="Export one cradle yoke in print orientation (STEP and STL); with --show, display it",
    )
    parser.add_argument(
        "--collar",
        action="store_true",
        help="Export the fore and aft lens collars in print orientation (STEP and STL); with --show, display them",
    )
    parser.add_argument(
        "--shoe",
        action="store_true",
        help="Export the cradle shoe in print orientation (STEP and STL); with --show, display it",
    )
    parser.add_argument(
        "--rest",
        action="store_true",
        help="Export the phone rest in print orientation (STEP and STL); with --show, display it",
    )
    add_output_option(parser)
    add_figure_option(parser, DEFAULT_FIGURE, "the lens cradle and phone rest")
    parser.add_argument(
        "--views",
        type=Path,
        nargs="?",
        const=Path("exports/figures"),
        help="Render several PNG views into this directory (default: exports/figures)",
    )
    args = parser.parse_args()
    printed = {}
    if args.yoke:
        printed["cradle_yoke"] = build_cradle_yoke_for_print()
    if args.collar:
        printed["lens_collar_fore"] = build_collar_for_print()
        printed["lens_collar_aft"] = build_collar_for_print(aft=True)
    if args.shoe:
        printed["cradle_shoe"] = build_cradle_shoe_for_print()
    if args.rest:
        printed["phone_rest"] = build_phone_rest_for_print()
    export_models(printed, args.output)
    if args.figure or args.views:
        built = {flag: build_camera_support_assembly(include_cutoff=flag) for flag in (True, False)}
        if args.figure:
            render(built[False], args.figure, FIGURE_VIEW_DIRECTION)
        if args.views:
            for name, (direction, cutoff, perspective) in VIEWS.items():
                render(built[cutoff], args.views / f"camera-support-{name}.png", direction, perspective)
    if args.show:
        if args.collar:  # Both are centered on the origin for printing; set them apart for viewing.
            gap = 5.0
            named = {"lens_collar_fore": "Fore Collar", "lens_collar_aft": "Aft Collar"}
            collars = []
            for i, (name, label) in enumerate(named.items()):
                box = printed[name].bounding_box()
                shifted = Pos((i - 0.5) * (box.size.X + gap), 0, 0) * printed[name]
                collars.append(assembly(label, [labeled(shifted, label)]))
            printed = {"lens_collars": assembly("Lens Collars", collars)}
        show(*printed.values()) if printed else show(
            build_camera_support_assembly(include_cutoff=not args.no_cutoff)
        )


if __name__ == "__main__":
    main()

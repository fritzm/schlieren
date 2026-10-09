"""Show or render the lens pointer and phone rest model (design §§9.4-9.8)."""

import argparse
from pathlib import Path

from build123d import Pos

from schlieren.cad import EXPORTERS, assembly, labeled
from schlieren.parts.camera_support import (
    build_camera_support_assembly,
    build_collar_for_print,
    build_pointer_shoe_for_print,
    build_pointer_yoke_for_print,
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
    parser.add_argument("--show", action="store_true", help="Display the model in OCP CAD Viewer")
    parser.add_argument("--no-cutoff", action="store_true", help="Leave the cutoff station out of --show")
    parser.add_argument(
        "--yoke",
        action="store_true",
        help="Export one pointer yoke in print orientation (STEP and STL); with --show, display it",
    )
    parser.add_argument(
        "--collar",
        action="store_true",
        help="Export the fore and aft lens collars in print orientation (STEP and STL); with --show, display them",
    )
    parser.add_argument(
        "--shoe",
        action="store_true",
        help="Export the pointer shoe in print orientation (STEP and STL); with --show, display it",
    )
    parser.add_argument("--output", type=Path, default=Path("exports"))
    parser.add_argument(
        "--figure",
        type=Path,
        nargs="?",
        const=DEFAULT_FIGURE,
        help=f"Render the design-doc figure (default path: {DEFAULT_FIGURE})",
    )
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
        printed["pointer_yoke"] = build_pointer_yoke_for_print()
    if args.collar:
        printed["lens_collar_fore"] = build_collar_for_print()
        printed["lens_collar_aft"] = build_collar_for_print(aft=True)
    if args.shoe:
        printed["pointer_shoe"] = build_pointer_shoe_for_print()
    for name, part in printed.items():
        for kind in ("step", "stl"):
            destination = args.output / kind / f"{name}.{kind}"
            destination.parent.mkdir(parents=True, exist_ok=True)
            EXPORTERS[kind](part, destination)
            print(destination)
    if args.figure or args.views:
        from schlieren.render import render_figure

        built = {flag: build_camera_support_assembly(include_cutoff=flag) for flag in (True, False)}
        if args.figure:
            args.figure.parent.mkdir(parents=True, exist_ok=True)
            render_figure(built[False], args.figure, FIGURE_VIEW_DIRECTION, perspective=True)
            print(args.figure)
        if args.views:
            args.views.mkdir(parents=True, exist_ok=True)
            for name, (direction, cutoff, perspective) in VIEWS.items():
                path = args.views / f"camera-support-{name}.png"
                render_figure(built[cutoff], path, direction, perspective=perspective)
                print(path)
    if args.show:
        from ocp_vscode import show

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

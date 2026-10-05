"""Show or render the lens pointer and phone rest model (design §§9.4-9.8)."""

import argparse
from pathlib import Path

from schlieren.parts.camera_support import build_camera_support_assembly

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

        show(build_camera_support_assembly(include_cutoff=not args.no_cutoff))


if __name__ == "__main__":
    main()

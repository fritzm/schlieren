"""Print the tabletop frame layout; export its plywood parts and the pivot-plate drilling drawing.

Optionally render the design-doc figure or show the assembly.
"""

import argparse
from math import degrees
from pathlib import Path

from schlieren.cad import EXPORTERS
from schlieren.parts.frame import FrameParameters, build_foot_block, build_frame_assembly, build_pivot_plate
from schlieren.parts.frame_drawing import pivot_plate_drawing_svg

DEFAULT_FIGURE = Path("docs/design/figures/frame.png")
DRAWING_FIGURE_NAME = "frame-pivot-plate.svg"  # The §4.2 drilling drawing, written beside the figure.
FIGURE_VIEW_DIRECTION = (
    -1.0,
    -0.8,
    0.7,
)  # From ahead of the pivot plate and above, looking aft down the rails.


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show", action="store_true", help="Display the assembly in OCP CAD Viewer")
    parser.add_argument("--output", type=Path, default=Path("exports"))
    parser.add_argument("--left-yaw", type=float, default=0.0, help="Left rail yaw outward from nominal, deg")
    parser.add_argument(
        "--right-yaw", type=float, default=0.0, help="Right rail yaw outward from nominal, deg"
    )
    parser.add_argument(
        "--figure",
        type=Path,
        nargs="?",
        const=DEFAULT_FIGURE,
        help="Render the design-doc figure, the frame at nominal yaw, and write the pivot-plate drilling "
        f"drawing beside it (default path: {DEFAULT_FIGURE})",
    )
    args = parser.parse_args()
    p = FrameParameters()
    p.validate()

    print(f"Rail half-angle {degrees(p.half_angle):.3f} deg")
    print("Pivot plate holes (x transverse, y aft of the mirror-facing edge), mm:")
    for name, (x, y) in p.plate_holes().items():
        print(f"  {name:<16} ({x:+7.2f}, {y:6.2f})")
    print(f"Pivot screw beyond its nyloc {p.pivot_screw_protrusion:.2f} mm")
    print(f"Yaw screw above its strap washer {p.yaw_screw_length_above_strap_washer:.2f} mm")
    print(
        f"Foot screw {p.foot_screw_slot_entry:.2f} mm into the rail slot, "
        f"{p.foot_screw_slot_margin:.2f} mm short of the slot floor"
    )
    print(f"Rail top {-p.table:.2f} mm above the table (feet uncompressed)")

    for name, part in (
        ("frame_pivot_plate", build_pivot_plate(p)),
        ("frame_foot_block", build_foot_block(p)),
    ):
        destination = args.output / "step" / f"{name}.step"
        destination.parent.mkdir(parents=True, exist_ok=True)
        EXPORTERS["step"](part, destination)
        print(destination)
    drawings = [args.output / "drawings" / "frame_pivot_plate.svg"]
    if args.figure:
        drawings.append(args.figure.with_name(DRAWING_FIGURE_NAME))
    for drawing in drawings:
        drawing.parent.mkdir(parents=True, exist_ok=True)
        drawing.write_text(pivot_plate_drawing_svg(p), encoding="utf-8")
        print(drawing)
    if args.figure:
        from schlieren.render import render_figure

        args.figure.parent.mkdir(parents=True, exist_ok=True)
        render_figure(build_frame_assembly(p), args.figure, FIGURE_VIEW_DIRECTION, perspective=True)
        print(args.figure)
    if args.show:
        from ocp_vscode import show

        show(build_frame_assembly(p, args.left_yaw, args.right_yaw))


if __name__ == "__main__":
    main()

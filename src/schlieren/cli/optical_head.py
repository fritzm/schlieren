"""Print the optical head's fixture stations and interference check; optionally show or render the assembly."""

import argparse
from pathlib import Path

from schlieren.cli._common import add_show_option, render, show
from schlieren.parts.optical_head import OpticalHeadParameters, build_optical_head

FIGURE_VIEW_DIRECTION = (1.0, -0.9, 0.7)  # From behind, outboard of the imaging rail and above.


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(parser, "Display the assembly in OCP CAD Viewer")
    parser.add_argument(
        "--slit-station", type=float, help="Slit blade plane along the rail, mm (negative aft)"
    )
    parser.add_argument("--stagger", type=float, default=0.0, help="Cutoff plane ahead of the slit, mm")
    parser.add_argument(
        "--left-yaw", type=float, default=0.0, help="Source rail yaw outward from nominal, deg"
    )
    parser.add_argument("--right-yaw", type=float, default=0.0, help="Imaging rail yaw outward, deg")
    parser.add_argument("--slit-rotation", type=float, default=0.0, help="Slit head rotation, deg")
    parser.add_argument("--figure", type=Path, help="Render the assembly to this PNG path")
    args = parser.parse_args()
    overrides = {"cutoff_stagger": args.stagger}
    if args.slit_station is not None:
        overrides["slit_station"] = args.slit_station
    h = OpticalHeadParameters(**overrides)
    h.validate()
    print("Stations along the rail from its pivot, mm (negative aft):")
    for name, station in (
        ("Slit blade plane", h.slit_station),
        ("Slit post", h.slit_post_station),
        ("Light source post", h.light_source_post_station),
        ("Cutoff cassette front", h.cutoff_plane_station),
        ("Cutoff post", h.cutoff_post_station),
        ("Phone back", h.phone_back_station),
    ):
        print(f"  {name:<22} {station:8.2f}")
    head = build_optical_head(h, args.left_yaw, args.right_yaw, args.slit_rotation)
    if args.figure:
        render(head, args.figure, FIGURE_VIEW_DIRECTION)
    if args.show:
        show(head)


if __name__ == "__main__":
    main()

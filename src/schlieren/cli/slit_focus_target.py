"""Export the experimental slit focus target (the shared fixture) and its paper and ground-glass retaining
rings; optionally show a variant on the post."""

import argparse

from schlieren.cli._common import add_output_option, add_show_option, export_models, show
from schlieren.parts.slit_focus_target import (
    FocusScreenParameters,
    FocusTargetParameters,
    build_focus_screen_assembly,
    build_focus_target,
    build_focus_target_assembly,
    build_glass_retaining_ring,
    build_retaining_ring,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(parser, "Display the focus target on its post and shoe in OCP CAD Viewer")
    parser.add_argument(
        "--glass",
        action="store_true",
        help="with --show, display the ground-glass variant instead of the paper one",
    )
    add_output_option(parser)
    args = parser.parse_args()
    p = FocusTargetParameters()
    p.validate()
    g = FocusScreenParameters(target=p)
    g.validate()
    print(
        f"Screen plane {p.barrel_length:.1f} mm ahead of the shoulder's seat on the stage plate's rear, "
        f"{p.rim_y:.2f} mm ahead of the blade-seat plane (the blades' edge plane)"
    )
    print(
        f"Barrel {p.barrel_length:.1f} mm long; bore tapers to Ø{p.seat_bore_diameter:.1f} mm at the rim face "
        f"over {p.seat_taper_length:.1f} mm"
    )
    print(f"Paper ring {p.ring_thickness:.2f} mm; screws reach {p.screw_engagement:.2f} mm into the inserts")
    print(
        f"Glass ring {g.ring_thickness:.2f} mm: pocket Ø{g.pocket_diameter:.2f} x {g.pocket_depth:.2f} mm, "
        f"lip {g.lip_thickness:.2f} mm; screws reach {g.ring_target.screw_engagement:.2f} mm; gasket "
        f"{g.gasket_compression(g.glass_thickness_max):.0%} (thick glass) to "
        f"{g.gasket_compression(g.glass_thickness_min):.0%} (thin glass) compressed"
    )
    parts = {
        "slit_focus_target": build_focus_target(p),
        "slit_focus_target_ring": build_retaining_ring(p),
        "slit_focus_target_glass_ring": build_glass_retaining_ring(g),
    }
    export_models(parts, args.output)
    if args.show:
        show(build_focus_screen_assembly(g) if args.glass else build_focus_target_assembly(p))


if __name__ == "__main__":
    main()

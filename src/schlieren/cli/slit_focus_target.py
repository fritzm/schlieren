"""Export the slit focus target (the fixture and its glass retaining ring); optionally show it on the post."""

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
    print(
        f"Screen plane {p.barrel_length:.1f} mm ahead of the shoulder's seat on the stage plate's rear, "
        f"{p.rim_y:.2f} mm ahead of the blade-seat plane (the blades' edge plane)"
    )
    print(
        f"Barrel {p.barrel_length:.1f} mm long; bore tapers to Ø{p.seat_bore_diameter:.1f} mm at the rim face "
        f"over {p.seat_taper_length:.1f} mm"
    )
    print(
        f"Ring {p.ring_thickness:.2f} mm: pocket Ø{p.pocket_diameter:.2f} x {p.pocket_depth:.2f} mm, "
        f"lip {p.lip_thickness:.2f} mm; screws reach {p.screw_engagement:.2f} mm into the inserts; gasket "
        f"{p.gasket_compression(p.glass_thickness_max):.0%} (thick glass) to "
        f"{p.gasket_compression(p.glass_thickness_min):.0%} (thin glass) compressed"
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

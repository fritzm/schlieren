"""Build/export the ring reticle half (print two of it; design §9.9); optionally display the snapped tube in
the cutoff post's ring on the camera support in OCP CAD Viewer."""

import argparse

from schlieren.cli._common import add_output_option, add_show_option, export_models, show
from schlieren.parts.ring_reticle import (
    RingReticleParameters,
    build_reticle_half,
    build_ring_reticle_assembly,
    lens_clearance,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(
        parser, "Display the reticle in the cutoff post's ring, on the camera support, in OCP CAD Viewer"
    )
    add_output_option(parser)
    args = parser.parse_args()
    p = RingReticleParameters()
    p.validate()
    print(
        f"Two identical halves snap into a Ø{p.tube_diameter:.2f} mm tube {p.unit_length:.1f} mm long, bore "
        f"Ø{p.bore:.1f} mm; centered on the ring, the aft crosshair stands {lens_clearance(p):.1f} mm "
        f"from the lens front"
    )
    print(
        f"Snap: ridge {p.ridge_height:.2f} mm in a {p.groove_depth:.2f} mm groove, interference "
        f"{p.interference:.2f} mm (straight-arm strain bound {p.arm_strain_bound:.1%}); "
        f"{p.wall_under_groove:.2f} mm of wall under the groove"
    )
    print("Print two halves, crosshair end down, without supports")
    export_models({"ring_reticle_half": build_reticle_half(p)}, args.output)
    if args.show:
        show(build_ring_reticle_assembly(p))


if __name__ == "__main__":
    main()

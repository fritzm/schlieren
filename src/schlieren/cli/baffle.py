"""Build/export the slit baffle (§7.8); optionally write its design-doc figure or display it in OCP CAD Viewer."""

import argparse
from pathlib import Path

from build123d import Shape

from schlieren.cad import assembly, labeled, moved, y_cylinder
from schlieren.cli._common import (
    add_figure_option,
    add_output_option,
    add_show_option,
    export_models,
    render,
    show,
)
from schlieren.palette import BLACK_ANODIZED, PRINTED_DENIM
from schlieren.parts.baffle import FOIL_LABEL, BaffleParameters, build_baffle, build_baffle_assembly
from schlieren.vendor_cad import SM1RC_M_THICKNESS, thorlabs_sm1rc_m

DEFAULT_FIGURE = Path("docs/design/figures/baffle.png")
# From the source side, above and to the right: the clamp ears, the relief hole, and the net.
FIGURE_VIEW_DIRECTION = (-0.9, -1.0, 0.7)


def viewer_assembly(p: BaffleParameters, foil: bool = True) -> Shape:
    """The baffle on the end of the plate's spigot, with the SM1RC/M ring it butts; foil leaves the wrap off the
    net, to show its windows."""
    spigot = y_cylinder(p.spigot_diameter, 0, 0, p.spigot_end_y, SM1RC_M_THICKNESS) - y_cylinder(
        p.spigot_bore, 0, 0, p.spigot_end_y - 1, SM1RC_M_THICKNESS + 1
    )
    baffle = build_baffle_assembly(p)
    if not foil:
        baffle = assembly(baffle.label, [c for c in baffle.children if c.label != FOIL_LABEL])
    return assembly(
        "Baffle on the spigot",
        [
            baffle,
            labeled(moved(thorlabs_sm1rc_m(), None), "SM1RC M ring", BLACK_ANODIZED),
            labeled(spigot, "Plate spigot", PRINTED_DENIM),
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(parser, "Display the baffle on the spigot and ring in OCP CAD Viewer")
    add_output_option(parser)
    add_figure_option(parser, DEFAULT_FIGURE, "the baffle on the spigot and ring, without its foil")
    args = parser.parse_args()
    p = BaffleParameters()
    p.validate()
    print(
        f"Clamp {p.clamp_length:.1f} mm on the spigot's last {p.spigot_extension} mm; net {p.net_length:.1f} mm, "
        f"{p.row_count} window rows, bore Ø{p.net_bore:.1f} mm"
    )
    export_models({"baffle": build_baffle(p)}, args.output)
    if args.figure:
        render(viewer_assembly(p, foil=False), args.figure, FIGURE_VIEW_DIRECTION)
    if args.show:
        show(viewer_assembly(p))


if __name__ == "__main__":
    main()

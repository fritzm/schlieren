"""Export the Stanley 11-515 razor blade model; optionally show it in the viewer."""

import argparse

from schlieren.cli._common import add_output_option, add_show_option, export_models, show
from schlieren.parts.razor_blade import RazorBladeParameters, build_razor_blade, build_razor_blade_assembly


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(parser, "Display the blade in OCP CAD Viewer")
    add_output_option(parser)
    args = parser.parse_args()
    p = RazorBladeParameters()
    p.validate()
    print(
        f"Blade {p.length:.2f} x {p.width:.2f} mm, {p.thickness:.3f} mm plate, {p.fold_thickness:.3f} mm fold"
    )
    export_models({"razor_blade": build_razor_blade(p)}, args.output)
    if args.show:
        show(build_razor_blade_assembly(p))


if __name__ == "__main__":
    main()

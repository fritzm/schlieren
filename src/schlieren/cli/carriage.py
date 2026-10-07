"""Export base, guide frame, keeper, and a paired plunger print layout; optionally render or show it on its post."""

import argparse
from pathlib import Path

from build123d import Compound, Pos, Rot

from schlieren.cad import EXPORTERS, assembly, children_by_label, labeled, place
from schlieren.parts.carriage import CarriageParameters, build_carriage

DEFAULT_FIGURE = Path("docs/design/figures/cutoff.png")
FIGURE_VIEW_DIRECTION = (1.0, 0.9, 0.7)  # From the mirror side, outboard and above: carriage, cassette, knob.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("exports"))
    parser.add_argument("--travel", type=float, default=0.0)
    parser.add_argument("--retract", type=float, default=0.0)
    parser.add_argument(
        "--keeper-side-thickness",
        type=float,
        default=CarriageParameters().keeper_side_thickness,
        help="keeper side-member thickness in mm (5 for the stiffer fallback keeper)",
    )
    parser.add_argument(
        "--figure",
        type=Path,
        nargs="?",
        const=DEFAULT_FIGURE,
        help=f"Render the design-doc figure, carriage with a seated cassette (default path: {DEFAULT_FIGURE})",
    )
    args = parser.parse_args()
    params = CarriageParameters(keeper_side_thickness=args.keeper_side_thickness)
    carriage = build_carriage(
        params,
        travel=args.travel,
        retract=args.retract,
        include_support=args.show,
        include_hardware=args.show,
    )
    # Keep the viewer assembled; exports use a separate, pose-independent layout.
    plunger_gap = 5.0  # Clear space between the two bounding boxes, in mm.
    parts = children_by_label(carriage)
    plungers = []
    next_y = 0.0
    for name in ("Driven plunger", "Spring plunger"):
        solid = parts[name]
        if name == "Spring plunger":
            solid = Rot(Z=180) * solid
        bounds = solid.bounding_box()
        solid = Pos(-(bounds.min.X + bounds.max.X) / 2, next_y - bounds.min.Y, -bounds.min.Z) * solid
        plungers.append(solid)
        next_y += bounds.size.Y + plunger_gap
    # Assembly children cannot be exported while attached to the assembly; export detached copies.
    flipped = Pos(0, 0, CarriageParameters().plate_thickness) * Rot(X=180)
    outputs = {
        "base_plate": labeled(parts["Base plate"], "Base plate", loc=flipped),
        "guide_frame": labeled(parts["Guide frame"], "Guide frame"),
        "keeper_plate": labeled(parts["Keeper plate"], "Keeper plate"),
        "plungers": Compound([s for plunger in plungers for s in plunger.solids()]),
    }
    for name, part in outputs.items():
        for kind in ("step", "stl"):
            path = args.output / kind / f"carriage_{name}.{kind}"
            path.parent.mkdir(parents=True, exist_ok=True)
            EXPORTERS[kind](part, path)
            print(path)
    # Retire only the former individual plunger exports from this exporter.
    for name in ("driven_plunger", "spring_plunger"):
        for kind in ("step", "stl"):
            (args.output / kind / f"carriage_{name}.{kind}").unlink(missing_ok=True)
    if args.figure:
        from schlieren.parts.cassette import build_cassette_assembly
        from schlieren.render import render_figure

        figure_carriage = build_carriage(params, include_support=True, include_hardware=True)
        seated = Pos(0, 0, params.plate_thickness + params.datum_projection)
        figure = assembly(
            figure_carriage.label, [*figure_carriage.children, place(seated, build_cassette_assembly())]
        )
        args.figure.parent.mkdir(parents=True, exist_ok=True)
        render_figure(figure, args.figure, FIGURE_VIEW_DIRECTION, perspective=True)
        print(args.figure)
    if args.show:
        from ocp_vscode import show

        show(carriage)


if __name__ == "__main__":
    main()

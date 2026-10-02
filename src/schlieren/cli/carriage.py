"""Export base, guide frame, keeper, and a paired plunger print layout; optionally show it on its post."""
import argparse
from pathlib import Path

import cadquery as cq

from schlieren.parts.carriage import CarriageParameters, build_carriage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("exports"))
    parser.add_argument("--travel", type=float, default=0.0)
    parser.add_argument("--retract", type=float, default=0.0)
    parser.add_argument("--keeper-side-thickness", type=float, default=CarriageParameters().keeper_side_thickness,
                        help="keeper side-member thickness in mm (5 for the stiffer fallback keeper)")
    args = parser.parse_args()
    params = CarriageParameters(keeper_side_thickness=args.keeper_side_thickness)
    assembly = build_carriage(params, travel=args.travel, retract=args.retract, include_support=args.show,
                              include_hardware=args.show)
    # Keep the viewer assembled; exports use a separate, pose-independent layout.
    plunger_gap = 5.0  # Clear space between the two bounding boxes, in mm.
    plungers = []
    next_y = 0.0
    for name in ("Driven plunger", "Spring plunger"):
        solid = assembly.objects[name].obj.val()
        if name == "Spring plunger":
            solid = solid.rotate((0, 0, 0), (0, 0, 1), 180)
        bounds = solid.BoundingBox()
        solid = solid.translate((-(bounds.xmin + bounds.xmax) / 2,
                                 next_y - bounds.ymin, -bounds.zmin))
        plungers.append(solid)
        next_y += bounds.ylen + plunger_gap
    outputs = {
        "base_plate": assembly.objects["Base plate"].obj.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, CarriageParameters().plate_thickness)),
        "guide_frame": assembly.objects["Guide frame"].obj,
        "keeper_plate": assembly.objects["Keeper plate"].obj,
        "plungers": cq.Compound.makeCompound(plungers),
    }
    for name, part in outputs.items():
        for kind in ("step", "stl"):
            path = args.output / kind / f"carriage_{name}.{kind}"
            path.parent.mkdir(parents=True, exist_ok=True)
            cq.exporters.export(part, str(path))
            print(path)
    # Retire only the former individual plunger exports from this exporter.
    for name in ("driven_plunger", "spring_plunger"):
        for kind in ("step", "stl"):
            (args.output / kind / f"carriage_{name}.{kind}").unlink(missing_ok=True)
    if args.show:
        from ocp_vscode import show
        show(assembly)


if __name__ == "__main__":
    main()

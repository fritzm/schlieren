"""Export cassette base and one clamp bar; optionally view the assembled cassette."""
import argparse
from pathlib import Path

import cadquery as cq

from schlieren.parts.cassette import build_cassette, build_clamp_bar, build_cassette_assembly
from schlieren.parts.carriage import CarriageParameters, build_carriage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--with-carriage", action="store_true", help="Include carriage in viewer only")
    parser.add_argument("--travel", type=float, default=0.0, help="Viewer cassette/carriage travel in mm")
    parser.add_argument("--output", type=Path, default=Path("exports"))
    args = parser.parse_args()
    p = CarriageParameters()
    if not -p.working_half_travel <= args.travel <= p.working_half_travel:
        parser.error("Travel must be within ±5 mm")
    for name, part in (("cassette_base", build_cassette()), ("cassette_clamp_bar", build_clamp_bar())):
        for kind in ("step", "stl"):
            path = args.output / kind / f"{name}.{kind}"
            path.parent.mkdir(parents=True, exist_ok=True)
            cq.exporters.export(part, str(path))
            print(path)
    if args.show:
        from ocp_vscode import show
        cassette = build_cassette_assembly()
        if args.with_carriage:
            assembly = build_carriage(p, travel=args.travel)
            assembly.add(cassette, loc=cq.Location(cq.Vector(
                0, args.travel, p.plate_thickness + p.datum_projection)))
            show(assembly)
        else:
            show(cassette)


if __name__ == "__main__":
    main()

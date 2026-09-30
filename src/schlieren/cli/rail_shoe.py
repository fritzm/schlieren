"""Build/export the prototype shoe; optionally display in OCP CAD Viewer."""

import argparse
from pathlib import Path

import cadquery as cq

from schlieren.parts.rail_shoe import build_rail_shoe, viewer_assembly


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--show", action="store_true", help="Display shoe and reference parts in OCP CAD Viewer"
    )
    parser.add_argument("--output", type=Path, default=Path("exports"))
    args = parser.parse_args()
    shoe = build_rail_shoe()
    for kind in ("step", "stl"):
        destination = args.output / kind / f"rail_shoe.{kind}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        cq.exporters.export(shoe, str(destination))
        print(destination)
    if args.show:
        from ocp_vscode import show

        show(viewer_assembly(shoe))


if __name__ == "__main__":
    main()

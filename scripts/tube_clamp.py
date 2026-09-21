"""Build/export the prototype clamp; optionally display in OCP CAD Viewer."""

import argparse
from pathlib import Path

import cadquery as cq

from schlieren.parts.tube_clamp import build_tube_clamp, viewer_assembly


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show", action="store_true", help="Display clamp and reference parts in OCP CAD Viewer")
    parser.add_argument("--output", type=Path, default=Path("exports"))
    args = parser.parse_args()
    clamp = build_tube_clamp()
    for kind in ("step", "stl"):
        destination = args.output / kind / f"tube_clamp.{kind}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        cq.exporters.export(clamp, str(destination))
        print(destination)
    if args.show:
        from ocp_vscode import show

        show(viewer_assembly(clamp))


if __name__ == "__main__":
    main()

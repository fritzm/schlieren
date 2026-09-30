"""Export provisional LED bracket; optionally show calibrated station references."""
import argparse
from pathlib import Path

import cadquery as cq

from schlieren.parts.led_module import LEDModuleParameters, build_led_bracket, build_led_module_assembly


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--with-shoe", action="store_true", help="Include rail shoe in viewer")
    parser.add_argument("--travel", type=float, default=0.0, help="Heatsink vertical calibration, ±3 mm")
    parser.add_argument("--output", type=Path, default=Path("exports"))
    args = parser.parse_args()
    p = LEDModuleParameters()
    if not -p.calibration_half_travel <= args.travel <= p.calibration_half_travel:
        parser.error("Travel must be within ±3 mm")
    bracket = build_led_bracket(p)
    for kind in ("step", "stl"):
        path = args.output / kind / f"led_module_bracket.{kind}"
        path.parent.mkdir(parents=True, exist_ok=True)
        cq.exporters.export(bracket, str(path))
        print(path)
    if args.show:
        from ocp_vscode import show
        show(build_led_module_assembly(p, args.travel, args.with_shoe))


if __name__ == "__main__":
    main()

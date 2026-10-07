"""Export the flexure slit head parts (§7); print its adjustment figures; optionally render or show it."""

import argparse
from pathlib import Path

from schlieren.cad import EXPORTERS
from schlieren.parts.slit_head import (
    SlitHeadParameters,
    build_clamp_bar,
    build_slit_head,
    build_slit_head_assembly,
    build_spigot_adapter,
)

DEFAULT_FIGURE = Path("docs/design/figures/slit-head.png")
FIGURE_VIEW_DIRECTION = (
    -0.9,
    -1.0,
    0.6,
)  # From the light-source side, outboard and above: the blades, knobs, and flexure.
# Setup values for the steering figure: iris-to-slit ~150 mm (§6.7), slit-to-mirror ~3200 mm (§3.1).
IRIS_TO_SLIT = 150.0
SLIT_TO_MIRROR = 3200.0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show", action="store_true")
    parser.add_argument(
        "--rotation", type=float, default=0.0, help="Degrees about the optical axis; 0 = horizontal slit"
    )
    parser.add_argument("--output", type=Path, default=Path("exports"))
    parser.add_argument(
        "--figure",
        type=Path,
        nargs="?",
        const=DEFAULT_FIGURE,
        help=f"Render the design-doc figure, head on its post and shoe (default path: {DEFAULT_FIGURE})",
    )
    args = parser.parse_args()
    p = SlitHeadParameters()
    p.validate()
    pitch_um = p.adjuster_pitch * 1000
    steer = SLIT_TO_MIRROR / IRIS_TO_SLIT
    print(f"FAS100: {pitch_um:.1f} um/turn, 10 um per {360 * 10 / pitch_um:.0f} deg of knob")
    print(
        f"Centering: ±{p.centering_half_travel} mm, beam moves ~{steer:.0f} mm at the mirror per mm of slit"
    )
    print(f"  flexure strain {100 * p.centering_strain:.2f}% at full travel")
    lo, hi = p.spring_force_range
    print(f"  spring preload {hi:.1f}-{lo:.1f} N over travel")
    d0, d1 = p.width_deflection_range
    f0, f1 = p.width_preload_range
    print(
        f"Width: {p.width_travel} mm of travel, flexure deflection {d0}-{d1} mm, strain {100 * p.width_strain:.2f}%"
    )
    print(f"  flexure preload {f0:.2f}-{f1:.2f} N")
    rw, rc = p.stage_rotation("width"), p.stage_rotation("centering")
    print(f"Stage rotation (first-order): width {rw * 1e3:.2f} mrad/mm, centering {rc * 1e3:.3f} mrad/mm")
    print(f"  slit taper over 10 mm per 0.1 mm of width change: {rw * 0.1 * 1e4:.2f} um")
    parts = {
        "slit_head": build_slit_head(p),
        "slit_head_adapter": build_spigot_adapter(p),
        "slit_head_clamp_bar": build_clamp_bar(p),
    }
    for name, part in parts.items():
        for kind in ("step", "stl"):
            path = args.output / kind / f"{name}.{kind}"
            path.parent.mkdir(parents=True, exist_ok=True)
            EXPORTERS[kind](part, path)
            print(path)
    if args.figure:
        from schlieren.render import render_figure

        args.figure.parent.mkdir(parents=True, exist_ok=True)
        render_figure(build_slit_head_assembly(p), args.figure, FIGURE_VIEW_DIRECTION, perspective=True)
        print(args.figure)
    if args.show:
        from ocp_vscode import show

        show(build_slit_head_assembly(p, args.rotation))


if __name__ == "__main__":
    main()

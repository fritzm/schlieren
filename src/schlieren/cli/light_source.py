"""Print the light source focus stack-up; optionally write its design-doc figure or show the assembly."""

import argparse
from pathlib import Path

from schlieren.parts.light_source import (
    GREEN,
    MODULES,
    WHITE,
    LightSourceParameters,
    build_light_source_assembly,
)
from schlieren.parts.light_source_drawing import drilling_templates_svg, layout_drawing_svg
from schlieren.parts.light_source_holes import HoleLayoutParameters

DEFAULT_FIGURE = Path("docs/design/figures/light-source.png")
HOLES_FIGURE_NAME = "light-source-holes.svg"  # The §6.4 hole layout, written beside the figure.
TEMPLATES_NAME = "light_source_drilling_templates.svg"
FIGURE_VIEW_DIRECTION = (1.0, 0.45, 0.4)  # From the side, slightly ahead and above: heatsink through iris.
FIGURE_RAIL_OVERHANG = 15.0  # Rail shown beyond each end of the shoe.


def figure_assembly(p, board):
    """The light source at focus on a generic rail segment under its shoe."""
    from build123d import Pos

    from schlieren.cad import assembly, labeled
    from schlieren.parts.rail import build_rail
    from schlieren.parts.rail_shoe import REFERENCE_COLOR, RailShoeParameters

    rail = build_rail(RailShoeParameters().length + 2 * FIGURE_RAIL_OVERHANG)
    post_y = p.smr1_thickness / 2
    return assembly(
        "Light source figure",
        [build_light_source_assembly(p, board), labeled(rail, "Rail", REFERENCE_COLOR, Pos(0, post_y, 0))],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show", action="store_true")
    parser.add_argument(
        "--output", type=Path, default=Path("exports"), help="Directory for the drilling templates"
    )
    parser.add_argument(
        "--templates",
        action="store_true",
        help="Write the full-scale cap and heatsink drilling templates (US Letter SVG, print at 100%%)",
    )
    parser.add_argument("--module", choices=("green", "white"), default="green", help="Board shown in viewer")
    parser.add_argument("--engagement", type=float, help="SM1V05 thread engagement, mm (default: focus)")
    parser.add_argument(
        "--figure",
        type=Path,
        nargs="?",
        const=DEFAULT_FIGURE,
        help=f"Render the design-doc figure, green module at focus (default path: {DEFAULT_FIGURE})",
    )
    args = parser.parse_args()
    p = LightSourceParameters()
    p.validate()
    holes = HoleLayoutParameters()
    holes.validate()
    print(f"Optimum emitter-to-plano gap {p.optimum_gap:.2f} mm, magnification {p.magnification:.1f}x")
    for board in MODULES:
        lo, hi = p.engagement_range(board)
        g_lo, g_hi = p.gap_range(board)
        print(
            f"{board.name}: engagement {lo:.2f}-{hi:.2f} mm, gap {g_lo:.2f}-{g_hi:.2f} mm, "
            f"focus at {p.focus_engagement(board):.2f} mm"
        )
    print(f"Heatsink clearance above post top {p.heatsink_post_top_clearance:.2f} mm")
    print(f"Lens vertex {p.lens_vertex_inside_open_end:.2f} mm inside the SM1V05 open end")
    print("Hole layout gaps, mm: " + ", ".join(f"{k} {v:.2f}" for k, v in holes.clearances().items()))
    if args.templates:
        templates = args.output / "drawings" / TEMPLATES_NAME
        templates.parent.mkdir(parents=True, exist_ok=True)
        templates.write_text(drilling_templates_svg(holes), encoding="utf-8")
        print(templates)
    if args.figure:
        from schlieren.render import render_figure

        holes_figure = args.figure.with_name(HOLES_FIGURE_NAME)
        holes_figure.parent.mkdir(parents=True, exist_ok=True)
        holes_figure.write_text(layout_drawing_svg(holes), encoding="utf-8")
        print(holes_figure)

        args.figure.parent.mkdir(parents=True, exist_ok=True)
        render_figure(figure_assembly(p, GREEN), args.figure, FIGURE_VIEW_DIRECTION, perspective=True)
        print(args.figure)
    if args.show:
        from ocp_vscode import show

        board = GREEN if args.module == "green" else WHITE
        try:
            show(build_light_source_assembly(p, board, args.engagement))
        except ValueError as e:
            parser.error(str(e))


if __name__ == "__main__":
    main()

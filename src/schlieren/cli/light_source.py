"""Print the light source focus stack-up; optionally write its design-doc figure or show the assembly."""

import argparse
from pathlib import Path

from schlieren.cli._common import (
    add_figure_option,
    add_output_option,
    add_show_option,
    render,
    show,
    with_suffix_name,
    write_text,
)
from schlieren.parts.light_source import (
    GREEN,
    MODULES,
    WHITE,
    LightSourceParameters,
    build_light_source_assembly,
    light_source_section,
)
from schlieren.parts.light_source_drawing import drilling_templates_svg, layout_drawing_svg
from schlieren.parts.light_source_holes import HoleLayoutParameters

DEFAULT_FIGURE = Path("docs/design/figures/light-source.png")
HOLES_FIGURE_NAME = "light-source-holes.svg"  # The §6.4 hole layout, written beside the figure.
TEMPLATES_NAME = "light_source_drilling_templates.svg"
FIGURE_VIEW_DIRECTION = (1.0, 0.75, 0.45)  # From the side, ahead and above: heatsink through the iris end.
SECTION_VIEW_DIRECTION = (1.0, 0.3, 0.2)  # Square to the cut face, slightly ahead and above.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(parser, "Display the assembly in OCP CAD Viewer")
    add_output_option(parser, "Directory for the drilling templates")
    parser.add_argument(
        "--templates",
        action="store_true",
        help="Write the full-scale cap and heatsink drilling templates (US Letter SVG, print at 100%%)",
    )
    parser.add_argument("--module", choices=("green", "white"), default="green", help="Board shown in viewer")
    parser.add_argument("--engagement", type=float, help="SM1V05 thread engagement, mm (default: focus)")
    add_figure_option(parser, DEFAULT_FIGURE, "and its -section cutaway, green module at focus")
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
        write_text(args.output / "drawings" / TEMPLATES_NAME, drilling_templates_svg(holes))
    if args.figure:
        write_text(args.figure.with_name(HOLES_FIGURE_NAME), layout_drawing_svg(holes))
        module = build_light_source_assembly(p, GREEN)
        render(module, args.figure, FIGURE_VIEW_DIRECTION)
        section = with_suffix_name(args.figure, "-section")
        render(light_source_section(module), section, SECTION_VIEW_DIRECTION, perspective=False)
    if args.show:
        board = GREEN if args.module == "green" else WHITE
        try:
            show(build_light_source_assembly(p, board, args.engagement))
        except ValueError as e:
            parser.error(str(e))


if __name__ == "__main__":
    main()

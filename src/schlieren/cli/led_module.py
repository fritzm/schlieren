"""Print the threaded LED module focus stack-up; optionally show the reference assembly."""

import argparse

from schlieren.parts.led_module import GREEN, MODULES, WHITE, LEDStackParameters, build_led_stack_assembly


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--module", choices=("green", "white"), default="green", help="Board shown in viewer")
    parser.add_argument("--engagement", type=float, help="SM1V05 thread engagement, mm (default: focus)")
    args = parser.parse_args()
    p = LEDStackParameters()
    p.validate()
    print(f"Optimum emitter-to-plano gap {p.optimum_gap:.2f} mm, magnification {p.magnification:.1f}x")
    for board in MODULES:
        lo, hi = p.engagement_range(board)
        g_lo, g_hi = p.gap_range(board)
        print(
            f"{board.name}: engagement {lo:.2f}-{hi:.2f} mm, gap {g_lo:.2f}-{g_hi:.2f} mm, "
            f"focus at {p.focus_engagement(board):.2f} mm"
        )
    print(f"Heatsink clearance above post top {p.heatsink_post_top_clearance:.2f} mm")
    if args.show:
        from ocp_vscode import show

        board = GREEN if args.module == "green" else WHITE
        try:
            show(build_led_stack_assembly(p, board, args.engagement))
        except ValueError as e:
            parser.error(str(e))


if __name__ == "__main__":
    main()

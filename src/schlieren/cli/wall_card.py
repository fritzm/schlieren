"""Write the wall fiducial cards (true-scale SVG and PDF, plus a dimensioned preview) for printing."""

import argparse

from schlieren.cli._common import add_output_option, write_text
from schlieren.parts.wall_card import CARDS, to_annotated_svg, to_pdf, to_svg


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--card",
        choices=[*CARDS, "all"],
        default="all",
        help="Which card: letter (US Letter landscape), 250 (250 mm square), or all (default)",
    )
    add_output_option(parser)
    args = parser.parse_args()
    folder = args.output / "drawings"
    for key, p in CARDS.items():
        if args.card not in (key, "all"):
            continue
        p.validate()
        write_text(folder / f"{p.name}.svg", to_svg(p))
        write_text(folder / f"{p.name}-annotated.svg", to_annotated_svg(p))
        pdf = folder / f"{p.name}.pdf"
        pdf.write_bytes(to_pdf(p))
        print(pdf)
    print("Print the PDF at 100 % (Actual size), then measure the printed mark spacing.")


if __name__ == "__main__":
    main()

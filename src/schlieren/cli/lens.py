"""Build/export the telephoto lens model (design §9.2); optionally display it in OCP CAD Viewer."""

import argparse

from schlieren.cli._common import add_output_option, add_show_option, export_models, show
from schlieren.parts.lens import build_lens


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(parser)
    add_output_option(parser)
    args = parser.parse_args()
    lens = build_lens()
    export_models({"lens": lens}, args.output)
    if args.show:
        show(lens)


if __name__ == "__main__":
    main()

"""Build/export the cased iPhone model (design §9.1); optionally display it in OCP CAD Viewer."""

import argparse

from schlieren.cli._common import add_output_option, add_show_option, export_models, show
from schlieren.parts.phone import build_phone


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(parser)
    add_output_option(parser)
    args = parser.parse_args()
    phone = build_phone()
    export_models({"phone": phone}, args.output)
    if args.show:
        show(phone)


if __name__ == "__main__":
    main()

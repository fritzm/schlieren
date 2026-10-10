"""Shared pieces of the part commands: the common options, and the export, drawing, figure, and viewer steps.

Each step prints the path it wrote, so a command's output lists its files. Imports of the renderer and the
viewer are deferred to the step that needs them, so a command that only exports starts quickly.
"""

import argparse
from collections.abc import Mapping
from pathlib import Path

from build123d import Shape

from schlieren.cad import EXPORTERS

DEFAULT_OUTPUT = Path("exports")
MODEL_KINDS = ("step", "stl")


def add_output_option(parser: argparse.ArgumentParser, help: str | None = None) -> None:
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=help)


def add_show_option(
    parser: argparse.ArgumentParser, help: str = "Display the model in OCP CAD Viewer"
) -> None:
    parser.add_argument("--show", action="store_true", help=help)


def add_figure_option(parser: argparse.ArgumentParser, default: Path, what: str) -> None:
    """--figure [PATH]: bare, it writes `default`; what says what the figure shows."""
    parser.add_argument(
        "--figure",
        type=Path,
        nargs="?",
        const=default,
        help=f"Render the design-doc figure, {what} (default path: {default})",
    )


def export_models(
    parts: Mapping[str, Shape], output: Path, kinds: tuple[str, ...] = MODEL_KINDS
) -> list[Path]:
    """Write each part as output/<kind>/<name>.<kind> for each kind; return the paths."""
    written = []
    for name, part in parts.items():
        for kind in kinds:
            path = output / kind / f"{name}.{kind}"
            path.parent.mkdir(parents=True, exist_ok=True)
            EXPORTERS[kind](part, path)
            print(path)
            written.append(path)
    return written


def write_text(path: Path, text: str) -> Path:
    """Write a text file (a drawing), creating its directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(path)
    return path


def render(
    shape: Shape, path: Path, view_direction: tuple[float, float, float], perspective: bool = True
) -> Path:
    """Render a PNG figure of shape (see schlieren.render), creating its directory."""
    from schlieren.render import render_figure

    path.parent.mkdir(parents=True, exist_ok=True)
    render_figure(shape, path, view_direction, perspective=perspective)
    print(path)
    return path


def with_suffix_name(path: Path, suffix: str) -> Path:
    """path with suffix added to its stem: figures/a.png, "-section" -> figures/a-section.png."""
    return path.with_name(f"{path.stem}{suffix}{path.suffix}")


def show(*shapes: Shape) -> None:
    """Send shapes to the OCP CAD Viewer."""
    from ocp_vscode import show as show_in_viewer

    show_in_viewer(*shapes)

"""Prepare a part for the Prusa MINI+: mesh to 3MF, slice, validate the G-code, embed the printer preview.

    make-bgcode build MESH.stl --template T.3mf --output PART.3mf [--up -y] [--add-box X0 Y0 Z0 X1 Y1 Z1]
    make-bgcode slice PART.3mf --output-dir DIR
    make-bgcode validate PART.bgcode [--model PART.3mf] [--supports]
    make-bgcode thumbnails PART.bgcode [--model PART.3mf] [--output OUT.bgcode] [--keep-original]
    make-bgcode prepare MESH.stl --template T.3mf --output-dir DIR [--up -y]

`build` puts the mesh, turned so --up points up and centered on the template's bed position, into a copy of a
GUI-saved 3MF, which carries the print profile. `slice` runs the PrusaSlicer command line; `validate` decodes the
bgcode and checks it against the 3MF; `thumbnails` renders the 3MF and embeds the images the printer shows as
its preview (the command-line slicer writes none). `prepare` runs all four and stops at the first problem.
"""

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path

from schlieren import bgcode, print_checks, prusaslicer
from schlieren.print_3mf import Box, build_3mf

# PrusaSlicer names its output <3mf name>_<nozzle>n_<layer>mm_<filament>_<printer>_<time>.bgcode.
_SLICER_SUFFIX = re.compile(r"_\d+(?:\.\d+)?n_\d+(?:\.\d+)?mm_.*$")


class StepFailedError(RuntimeError):
    pass


def model_for(bgcode_path: Path) -> Path:
    """The 3MF beside a bgcode that PrusaSlicer named after it."""
    stem = _SLICER_SUFFIX.sub("", bgcode_path.stem)
    candidate = bgcode_path.with_name(f"{stem}.3mf")
    if stem == bgcode_path.stem or not candidate.exists():
        raise FileNotFoundError(
            f"no 3MF found for {bgcode_path.name} (looked for {candidate.name}); use --model"
        )
    return candidate


def embed_thumbnails(
    source: bytes, thumbnails: Sequence[tuple[bgcode.ImageFormat, int, int, bytes]]
) -> bytes:
    """source with its thumbnails replaced by the encoded images (format, width, height, bytes)."""
    original = bgcode.parse(source)
    checksum_type = original.checksum_type
    blocks = [bgcode.thumbnail_block(*thumbnail, checksum_type=checksum_type) for thumbnail in thumbnails]
    result = bgcode.replace_thumbnails(original, blocks)
    data = result.to_bytes()

    reread = bgcode.parse(data)  # Verifies every checksum again, on what will be written.
    gcode = [block.raw for block in original.blocks if block.type == bgcode.BlockType.GCODE]
    if gcode != [block.raw for block in reread.blocks if block.type == bgcode.BlockType.GCODE]:
        raise bgcode.BgcodeError("G-code blocks changed while inserting thumbnails")
    return data


def build_step(mesh: Path, template: Path, output: Path, up: str, boxes: Sequence[Box] = ()) -> None:
    built = build_3mf(mesh, template, output, up=up, boxes=boxes)
    print(output)
    print(
        f"  {built.triangles} triangles, {built.vertices} vertices, "
        f"{built.size[0]:.2f} x {built.size[1]:.2f} x {built.size[2]:.2f} mm, volume {built.volume:.0f} mm3"
    )
    for box in boxes:
        print("  added part (box, STL frame): " + " ".join(f"{v:g}" for v in box))
    if built.open_edges:
        print(
            f"  note: {built.open_edges} mesh edges are not shared by exactly two triangles (open or "
            f"non-manifold; usually tessellation cracks). Check the slice around them."
        )


def slice_step(three_mf: Path, output_dir: Path, slicer: Path | None) -> Path:
    result = prusaslicer.slice_3mf(three_mf, output_dir, slicer)
    print(result.output)
    if result.problems:
        print("  slicer output that looks like a warning or error:")
        for line in result.problems:
            print(f"    {line}")
        raise StepFailedError(
            "the slice reported problems; fix them and re-slice (the bgcode was still written)"
        )
    print("  slice clean: no errors or warnings")
    return result.output


def validate_step(
    bgcode_path: Path, model: Path | None, expect_support: bool, max_temperature: float
) -> None:
    checks = print_checks.check_bgcode(bgcode_path, model, expect_support, max_temperature)
    print(print_checks.report(checks))
    if bad := print_checks.failed(checks):
        raise StepFailedError(f"{len(bad)} check(s) failed: " + ", ".join(check.name for check in bad))


def thumbnails_step(
    source: Path, model: Path, output: Path | None, keep_original: bool, preview: Path | None
) -> None:
    """Embed the thumbnails; by default the bgcode is replaced in place, through a temporary file so a failed
    write leaves it as it was. keep_original saves the unmodified file as NAME.bgcode.orig first."""
    from schlieren.thumbnail import render_thumbnails

    rendered = render_thumbnails(model)
    data = embed_thumbnails(
        source.read_bytes(), [(spec.format, spec.width, spec.height, image) for spec, image in rendered]
    )
    output = output or source
    if keep_original and output == source:
        copy = source.with_suffix(".bgcode.orig")
        copy.write_bytes(source.read_bytes())
        print(copy)
    staging = output.with_suffix(".bgcode.tmp")
    staging.write_bytes(data)
    staging.replace(output)
    print(output)
    for spec, image in rendered:
        print(f"  {spec.width}x{spec.height} {spec.format.name}: {len(image)} bytes")
    if preview:
        preview.mkdir(parents=True, exist_ok=True)
        for spec, image in rendered:
            if spec.format == bgcode.ImageFormat.PNG:
                path = preview / f"{model.stem}_{spec.width}x{spec.height}.png"
                path.write_bytes(image)
                print(path)


def build_command(args: argparse.Namespace) -> None:
    build_step(args.mesh, args.template, args.output, args.up, args.add_box)


def slice_command(args: argparse.Namespace) -> None:
    slice_step(args.three_mf, args.output_dir, args.slicer)


def validate_command(args: argparse.Namespace) -> None:
    validate_step(args.bgcode, args.model or model_for(args.bgcode), args.supports, args.max_temperature)


def thumbnails_command(args: argparse.Namespace) -> None:
    thumbnails_step(
        args.bgcode, args.model or model_for(args.bgcode), args.output, args.keep_original, args.preview
    )


def prepare_command(args: argparse.Namespace) -> None:
    name = args.name or args.mesh.stem
    three_mf = args.output_dir / f"{name}.3mf"
    if three_mf.exists() and not args.force:
        raise StepFailedError(f"{three_mf} exists; use --force to replace it")
    print("== build")
    build_step(args.mesh, args.template, three_mf, args.up, args.add_box)
    print("== slice")
    sliced = slice_step(three_mf, args.output_dir, args.slicer)
    print("== validate")
    validate_step(sliced, three_mf, args.supports, args.max_temperature)
    print("== thumbnails")
    thumbnails_step(sliced, three_mf, None, False, args.preview)


def _add_validation_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--supports", action="store_true", help="Support material is expected")
    parser.add_argument(
        "--max-temperature",
        type=float,
        default=print_checks.MAX_HOTEND_C,
        help="Highest hotend setpoint allowed, C (default: %(default)g, for PLA)",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = parser.add_subparsers(dest="command", required=True)

    def command(name: str, help_text: str, run) -> argparse.ArgumentParser:
        sub = commands.add_parser(name, help=help_text)
        sub.set_defaults(run=run)
        return sub

    def add_build_options(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("mesh", type=Path, help="STL of the part, in its own frame")
        sub.add_argument(
            "--template", type=Path, required=True, help="A GUI-saved 3MF whose profile to use, as it is"
        )
        sub.add_argument(
            "--up",
            default="+z",
            help="The model axis that points up when printing: +x -x +y -y +z -z (default: %(default)s)",
        )
        sub.add_argument(
            "--add-box",
            type=float,
            nargs=6,
            action="append",
            default=[],
            metavar=("X0", "Y0", "Z0", "X1", "Y1", "Z1"),
            help="Add a box part, in the STL's frame (repeatable): a sacrificial feature that changes the "
            "slice only, such as a web closing a split ring's first layer so its brim stays out of the bore",
        )

    build = command("build", "Build a 3MF from an STL, in a template's profile", build_command)
    add_build_options(build)
    build.add_argument("--output", type=Path, required=True, help="The 3MF to write")

    slice_ = command("slice", "Slice a 3MF with the PrusaSlicer command line", slice_command)
    slice_.add_argument("three_mf", type=Path)
    slice_.add_argument("--output-dir", type=Path, required=True)
    slice_.add_argument(
        "--slicer", type=Path, help="PrusaSlicer executable (default: $PRUSASLICER, then the app)"
    )

    validate = command("validate", "Check a bgcode against its 3MF", validate_command)
    validate.add_argument("bgcode", type=Path)
    validate.add_argument("--model", type=Path, help="The 3MF it was sliced from (default: found beside it)")
    _add_validation_options(validate)

    thumbnails = command("thumbnails", "Embed rendered thumbnails in a bgcode", thumbnails_command)
    thumbnails.add_argument("bgcode", type=Path)
    thumbnails.add_argument(
        "--model", type=Path, help="The 3MF it was sliced from (default: found beside it)"
    )
    thumbnails.add_argument("--output", type=Path, help="Write here instead of replacing the bgcode")
    thumbnails.add_argument(
        "--keep-original",
        action="store_true",
        help="When replacing the bgcode, first save the original beside it as NAME.bgcode.orig",
    )
    thumbnails.add_argument("--preview", type=Path, help="Also write the PNG thumbnails to this directory")

    prepare = command("prepare", "Build, slice, validate and add thumbnails", prepare_command)
    add_build_options(prepare)
    prepare.add_argument("--output-dir", type=Path, required=True, help="Where the 3MF and bgcode go")
    prepare.add_argument("--name", help="Name of the 3MF (default: the mesh's)")
    prepare.add_argument("--force", action="store_true", help="Replace an existing 3MF of that name")
    prepare.add_argument(
        "--slicer", type=Path, help="PrusaSlicer executable (default: $PRUSASLICER, then the app)"
    )
    prepare.add_argument("--preview", type=Path, help="Also write the PNG thumbnails to this directory")
    _add_validation_options(prepare)

    args = parser.parse_args()
    try:
        args.run(args)
    except (OSError, ValueError, StepFailedError, prusaslicer.SliceError) as error:
        sys.exit(f"make-bgcode: {error}")


if __name__ == "__main__":
    main()

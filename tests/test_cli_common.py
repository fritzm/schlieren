"""The shared pieces of the part commands: option declarations, file writing, and path naming."""

import argparse
import tempfile
import unittest
from pathlib import Path

from build123d import Box

from schlieren.cli._common import (
    DEFAULT_OUTPUT,
    add_figure_option,
    add_output_option,
    export_models,
    with_suffix_name,
    write_text,
)


class CliCommonTests(unittest.TestCase):
    def parse(self, *argv):
        parser = argparse.ArgumentParser()
        add_output_option(parser)
        add_figure_option(parser, Path("figures/a.png"), "a thing")
        return parser.parse_args(argv)

    def test_options_default_and_override(self):
        args = self.parse()
        self.assertEqual(args.output, DEFAULT_OUTPUT)
        self.assertIsNone(args.figure)
        self.assertEqual(self.parse("--figure").figure, Path("figures/a.png"))
        self.assertEqual(self.parse("--figure", "b.png").figure, Path("b.png"))
        self.assertEqual(self.parse("--output", "out").output, Path("out"))

    def test_export_models_writes_each_kind_under_its_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            written = export_models({"cube": Box(1, 1, 1)}, Path(tmp))
            self.assertEqual(
                {path.relative_to(tmp).as_posix() for path in written}, {"step/cube.step", "stl/cube.stl"}
            )
            self.assertTrue(all(path.stat().st_size > 0 for path in written))
            only_step = export_models({"cube2": Box(1, 1, 1)}, Path(tmp), kinds=("step",))
            self.assertEqual([p.name for p in only_step], ["cube2.step"])

    def test_write_text_creates_its_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_text(Path(tmp) / "drawings" / "a.svg", "<svg/>")
            self.assertEqual(path.read_text(encoding="utf-8"), "<svg/>")

    def test_suffix_goes_before_the_extension(self):
        self.assertEqual(with_suffix_name(Path("figures/a.png"), "-section"), Path("figures/a-section.png"))


if __name__ == "__main__":
    unittest.main()

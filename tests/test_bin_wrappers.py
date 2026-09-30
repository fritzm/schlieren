"""bin/ wrappers must match [project.scripts] in pyproject.toml (regenerate with bin/gen-bin)."""
import os
import unittest

from schlieren.cli import gen_bin


class BinWrapperTests(unittest.TestCase):
    def test_wrappers_match_project_scripts(self):
        expected = gen_bin.expected_wrappers()
        actual = {p.name for p in gen_bin.BIN_DIR.iterdir()}
        self.assertEqual(actual, set(expected), "run bin/gen-bin")
        for name, text in expected.items():
            path = gen_bin.BIN_DIR / name
            self.assertEqual(path.read_text(encoding="utf-8"), text, f"{name} is stale; run bin/gen-bin")
            self.assertTrue(os.access(path, os.X_OK), f"{name} is not executable")

    def test_entry_points_are_importable(self):
        import importlib
        import tomllib

        with (gen_bin.REPO_ROOT / "pyproject.toml").open("rb") as f:
            commands = tomllib.load(f)["project"]["scripts"]
        for name, target in commands.items():
            module, func = target.split(":")
            self.assertTrue(callable(getattr(importlib.import_module(module), func)), name)


if __name__ == "__main__":
    unittest.main()

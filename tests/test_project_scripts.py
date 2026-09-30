"""Every [project.scripts] entry in pyproject.toml must resolve to a callable."""

import importlib
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class ProjectScriptsTests(unittest.TestCase):
    def test_entry_points_are_importable(self):
        with (REPO_ROOT / "pyproject.toml").open("rb") as f:
            commands = tomllib.load(f)["project"]["scripts"]
        for name, target in commands.items():
            module, func = target.split(":")
            self.assertTrue(callable(getattr(importlib.import_module(module), func)), name)


if __name__ == "__main__":
    unittest.main()

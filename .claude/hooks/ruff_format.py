"""PostToolUse hook: run ruff format on edited Python files (line length comes from pyproject.toml)."""

import json
import subprocess
import sys

payload = json.load(sys.stdin)
path = payload.get("tool_input", {}).get("file_path", "")
if path.endswith(".py"):
    subprocess.run(["uvx", "ruff", "format", path], capture_output=True, check=False)

"""Concatenate docs/status/NN-*.md fragments (filename order) into one consolidated status document.

The output is a generated artifact; edit the fragments, never the output.

    bin/build-status-doc [-o exports/docs/schlieren-project-status.md]
"""

import argparse
import re
from pathlib import Path

# src/schlieren/cli/<module>.py -> repo root (valid for the editable install that uv sync creates)
REPO_ROOT = Path(__file__).resolve().parents[3]
FRAGMENT_DIR = REPO_ROOT / "docs" / "status"
DEFAULT_OUTPUT = REPO_ROOT / "exports" / "docs" / "schlieren-project-status.md"


def build_status_doc() -> str:
    fragments = sorted(FRAGMENT_DIR.glob("[0-9][0-9]-*.md"))
    if not fragments:
        raise SystemExit(f"No fragments found in {FRAGMENT_DIR}")
    text = "\n".join(f.read_text(encoding="utf-8").rstrip() + "\n" for f in fragments)
    # Fragment-to-fragment links (NN-name.md#anchor) become in-document anchors in the consolidated output.
    return re.sub(r"\]\(\d\d-[\w-]+\.md#", "](#", text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_status_doc(), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()

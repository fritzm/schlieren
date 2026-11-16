"""Run the PrusaSlicer command line on a 3MF and report what it said."""

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SLICER = Path("/Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer")
SLICER_ENV = "PRUSASLICER"
_EXPORTED = re.compile(r"^Slicing result exported to (.+)$", re.MULTILINE)
_PROBLEM = re.compile(r"\b(warning|error|fail(?:ed|ure)?|exception|unable|cannot|invalid)\b", re.IGNORECASE)


class SliceError(RuntimeError):
    pass


@dataclass(frozen=True)
class SliceResult:
    output: Path
    problems: tuple[str, ...]  # Output lines that look like a warning or error; empty for a clean slice.
    log: str


def find_slicer(slicer: Path | None = None) -> Path:
    """The slicer executable: the argument, else $PRUSASLICER, else the standard macOS install."""
    chosen = slicer or (Path(os.environ[SLICER_ENV]) if os.environ.get(SLICER_ENV) else DEFAULT_SLICER)
    if not chosen.exists():
        raise SliceError(f"PrusaSlicer not found at {chosen}; pass --slicer or set ${SLICER_ENV}")
    return chosen


def slice_3mf(three_mf: Path, output_dir: Path, slicer: Path | None = None) -> SliceResult:
    """Slice the 3MF where it sits on the bed (no re-arranging) into output_dir; the slicer names the file.

    Raises SliceError if it fails or writes nothing. Warnings do not raise; they are returned for the caller
    to judge.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    run = subprocess.run(
        [
            str(find_slicer(slicer)),
            "--export-gcode",
            str(three_mf),
            "--dont-arrange",
            "--output",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    log = (run.stdout + run.stderr).strip()
    exported = _EXPORTED.findall(log)
    if run.returncode != 0 or not exported:
        raise SliceError(f"PrusaSlicer failed (exit {run.returncode}):\n{log}")
    output = Path(exported[-1].strip())
    if not output.exists():
        raise SliceError(f"PrusaSlicer reported {output} but it does not exist:\n{log}")
    problems = tuple(
        line.strip()
        for line in log.splitlines()
        if _PROBLEM.search(line) and not _EXPORTED.match(line.strip())
    )
    return SliceResult(output, problems, log)

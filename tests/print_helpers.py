"""Shared pieces for the print-preparation tests: paths to the committed fixtures and a box STL writer.

The fixtures are a 10 mm cube built and sliced with `make-bgcode` (profile: the project's MINI+ 0.15 mm PLA one):

    write_box_stl(Path("cube.stl"), (10, 10, 10))
    uv run make-bgcode build cube.stl --template <GUI-saved 3MF> --output tests/data/cube.3mf
    uv run make-bgcode slice tests/data/cube.3mf --output-dir tests/data

(replace the old cube_*.bgcode, whose name carries the print time).
"""

import struct
from pathlib import Path

import numpy as np

DATA = Path(__file__).parent / "data"
CUBE_3MF = DATA / "cube.3mf"

# A box's corners, and its twelve triangles wound counter-clockwise seen from outside.
_CORNERS = np.array([[x, y, z] for z in (0, 1) for y in (0, 1) for x in (0, 1)], dtype=float)
_FACES = [
    (0, 2, 1), (1, 2, 3),  # bottom (z = 0)
    (4, 5, 6), (5, 7, 6),  # top
    (0, 1, 4), (1, 5, 4),  # front (y = 0)
    (2, 6, 3), (3, 6, 7),  # back
    (0, 4, 2), (2, 4, 6),  # left (x = 0)
    (1, 3, 5), (3, 7, 5),  # right
]  # fmt: skip


def box_triangles(size: tuple[float, float, float]) -> np.ndarray:
    """(12, 3, 3) triangles of the box from the origin to size."""
    return (_CORNERS * np.array(size))[np.array(_FACES)]


def write_box_stl(path: Path, size: tuple[float, float, float], drop: int | None = None) -> Path:
    """A binary STL of a box; `drop` leaves out that triangle, for an open mesh."""
    triangles = box_triangles(size)
    if drop is not None:
        triangles = np.delete(triangles, drop, axis=0)
    with path.open("wb") as f:
        f.write(b"test box".ljust(80, b"\0"))
        f.write(struct.pack("<I", len(triangles)))
        for triangle in triangles:
            f.write(struct.pack("<3f", 0, 0, 0))
            f.write(struct.pack("<9f", *triangle.ravel()))
            f.write(b"\0\0")
    return path


def cube_bgcode() -> Path:
    """The sliced cube (PrusaSlicer names it with the print time, so it is found, not named)."""
    return next(DATA.glob("cube_*.bgcode"))

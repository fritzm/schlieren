"""Helpers for the unit tests: a switch for the slow geometry checks, and a cheap overlap prefilter.

The default test run is the fast one, for iterating. Set SCHLIEREN_TESTS=full to include the tests marked
`slow`, the exhaustive interference, sweep, and clearance checks; run the full set before presenting work.
`uv run run-tests` runs the test modules in parallel and takes --full.
"""

import os
import unittest

from build123d import Shape

FULL_ENV = "SCHLIEREN_TESTS"


def full_run() -> bool:
    return os.environ.get(FULL_ENV, "").lower() == "full"


def slow(test):
    """Mark a test that takes more than a few seconds; it is skipped unless SCHLIEREN_TESTS=full."""
    return unittest.skipUnless(full_run(), f"slow: set {FULL_ENV}=full or use run-tests --full")(test)


def boxes_overlap(a: Shape, b: Shape, margin: float = 0.0) -> bool:
    """Whether the bounding boxes of two shapes overlap, to within margin.

    Exact boolean and distance queries between real solids are expensive; when the boxes are apart the
    answer is already known, so check this first. A false result means the shapes are further than margin
    apart, along at least one axis.
    """
    box_a, box_b = a.bounding_box(), b.bounding_box()
    return all(
        getattr(box_a.min, k) < getattr(box_b.max, k) + margin
        and getattr(box_b.min, k) < getattr(box_a.max, k) + margin
        for k in "XYZ"
    )

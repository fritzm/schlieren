"""Helpers for the unit tests: a switch for the slow geometry checks, and a cheap overlap prefilter.

The default test run is the fast one, for iterating. Set SCHLIEREN_TESTS=full to include the tests marked
`slow`, the exhaustive interference, sweep, and clearance checks; run the full set before presenting work.
`uv run run-tests` runs the test modules in parallel and takes --full.
"""

import os
import unittest
from collections.abc import Iterable, Iterator

from build123d import BoundBox, Shape

FULL_ENV = "SCHLIEREN_TESTS"


def full_run() -> bool:
    return os.environ.get(FULL_ENV, "").lower() == "full"


def slow(test):
    """Mark a test that takes more than a few seconds; it is skipped unless SCHLIEREN_TESTS=full."""
    return unittest.skipUnless(full_run(), f"slow: set {FULL_ENV}=full or use run-tests --full")(test)


def exact_box(shape: Shape) -> BoundBox:
    return shape.bounding_box()


def loose_box(shape: Shape) -> BoundBox:
    """A bounding box that contains shape, cheaply.

    The exact box of a vendor B-rep costs tens of milliseconds and is not cached; this one comes from the
    surfaces' control points, is never smaller than the exact box, and is about a hundred times faster. It is
    for prefilters, where a larger box only means a few more exact queries.
    """
    return shape.bounding_box(optimal=False)


def _boxes_overlap(box_a: BoundBox, box_b: BoundBox, margin: float) -> bool:
    return all(
        getattr(box_a.min, k) < getattr(box_b.max, k) + margin
        and getattr(box_b.min, k) < getattr(box_a.max, k) + margin
        for k in "XYZ"
    )


def boxes_overlap(a: Shape, b: Shape, margin: float = 0.0, loose: bool = False) -> bool:
    """Whether the bounding boxes of two shapes overlap, to within margin.

    Exact boolean and distance queries between real solids are expensive; when the boxes are apart the
    answer is already known, so check this first. A false result means the shapes are further than margin
    apart, along at least one axis. Pass loose=True for such a prefilter, which is much cheaper on vendor
    models; leave it off where the result itself is asserted. For many pairs use `near_pairs`, which boxes
    each shape once.
    """
    box = loose_box if loose else exact_box
    return _boxes_overlap(box(a), box(b), margin)


def near_pairs(
    first: Iterable[Shape], second: Iterable[Shape], margin: float = 0.0
) -> Iterator[tuple[Shape, Shape]]:
    """Pairs (a, b) from the two collections whose bounding boxes overlap to within margin.

    Each shape is boxed once, however many pairs it is in; the pairs not yielded are known to be further
    than margin apart.
    """
    boxed_second = [(shape, loose_box(shape)) for shape in second]
    for a in first:
        box_a = loose_box(a)
        for b, box_b in boxed_second:
            if _boxes_overlap(box_a, box_b, margin):
                yield a, b

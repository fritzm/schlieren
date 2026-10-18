"""Helpers for the unit tests: a switch for the slow geometry checks, models shared by a test class, and a
cheap overlap prefilter.

The default test run is the fast one, for iterating. Set SCHLIEREN_TESTS=full to include the tests marked
`slow`, the exhaustive interference, sweep, and clearance checks; run the full set before presenting work.
`uv run run-tests` runs the test modules in parallel and takes --full.
"""

import os
import unittest
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Iterator
from itertools import combinations
from math import inf

from build123d import BoundBox, Shape

from schlieren.cad import intersect

FULL_ENV = "SCHLIEREN_TESTS"


def full_run() -> bool:
    return os.environ.get(FULL_ENV, "").lower() == "full"


def slow(test):
    """Mark a test that takes more than a few seconds; it is skipped unless SCHLIEREN_TESTS=full."""
    return unittest.skipUnless(full_run(), f"slow: set {FULL_ENV}=full or use run-tests --full")(test)


class shared:  # noqa: N801 (used as a decorator, like `slow`)
    """A model built once per test class, on first use, and then shared by that class's tests.

    Decorate a method that takes the class and returns the model; tests read it as an attribute:

        @shared
        def hardware(cls):
            return children_by_label(build_carriage(cls.p, include_hardware=True))

    Use it for every model at its default parameters and pose that a test would otherwise build itself, so a
    module builds each such model once however many tests come to use it. It is built on first use, so a model
    only the slow tests need costs the default run nothing. The model is shared: tests must not modify it.
    """

    def __init__(self, build):
        self.build = build
        self.__doc__ = build.__doc__

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        value = self.build(owner)
        setattr(owner, self.name, value)  # Replaces this descriptor, so the build runs once per class.
        return value


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

    Exact boolean and distance queries between real solids are expensive; when the boxes are apart the answer
    is already known, so check this first. A false result means the shapes are further than margin apart,
    along at least one axis. Pass loose=True for such a prefilter, which is much cheaper on vendor models;
    leave it off where the result itself is asserted. For many pairs use `near_pairs`, which boxes each shape
    once.
    """
    box = loose_box if loose else exact_box
    return _boxes_overlap(box(a), box(b), margin)


def near_pairs(
    first: Iterable[Shape], second: Iterable[Shape], margin: float = 0.0
) -> Iterator[tuple[Shape, Shape]]:
    """Pairs (a, b) from the two collections whose bounding boxes overlap to within margin.

    Each shape is boxed once, however many pairs it is in; the pairs not yielded are known to be further than
    margin apart.
    """
    boxed_second = [(shape, loose_box(shape)) for shape in second]
    for a in first:
        box_a = loose_box(a)
        for b, box_b in boxed_second:
            if _boxes_overlap(box_a, box_b, margin):
                yield a, b


def near_pairs_among(shapes: Iterable[Shape], margin: float = 0.0) -> Iterator[tuple[Shape, Shape]]:
    """Each distinct pair of shapes whose bounding boxes overlap to within margin, each shape boxed once."""
    boxed = [(shape, loose_box(shape)) for shape in shapes]
    for (a, box_a), (b, box_b) in combinations(boxed, 2):
        if _boxes_overlap(box_a, box_b, margin):
            yield a, b


def svg_attr(element: ET.Element, name: str) -> str:
    """An attribute that the drawing under test must carry; ElementTree's `get` returns None when absent."""
    value = element.get(name)
    if value is None:
        raise AssertionError(f"<{element.tag}> has no {name!r} attribute")
    return value


def overlap_volume(a: Shape, b: Shape) -> float:
    """Volume of the intersection of a and b, without the boolean when their bounding boxes are apart."""
    if not boxes_overlap(a, b, loose=True):
        return 0.0
    return intersect(a, b).volume


def bounded_distance(a: Shape, b: Shape, limit: float) -> float:
    """The distance between a and b if it is less than limit, otherwise infinity.

    For asserting a clearance of at least limit: shapes whose bounding boxes are limit or more apart cannot be
    closer, so the exact distance query, which is expensive on vendor models, is skipped for them.
    """
    if not boxes_overlap(a, b, limit, loose=True):
        return inf
    return a.distance_to(b)

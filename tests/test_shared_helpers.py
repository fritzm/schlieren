"""Guards in the shared helpers: duplicate assembly labels and unusable parameter values."""

import unittest
from dataclasses import dataclass, replace

from build123d import Box

from schlieren.cad import assembly, children_by_label, labeled
from schlieren.parts.carriage import CarriageParameters
from schlieren.parts.frame import FrameParameters
from schlieren.validation import require_positive_dimensions


@dataclass(frozen=True)
class Sample:
    length: float = 1.0
    width: float = 2.0
    note: str = "ignored"
    points: tuple = (0.0, -1.0)


class ChildrenByLabelTests(unittest.TestCase):
    def test_keys_children_by_label(self):
        node = assembly("A", [labeled(Box(1, 1, 1), "one"), labeled(Box(1, 1, 1), "two")])
        self.assertEqual(set(children_by_label(node)), {"one", "two"})

    def test_duplicate_labels_are_an_error(self):
        node = assembly("A", [labeled(Box(1, 1, 1), "same"), labeled(Box(2, 2, 2), "same")])
        with self.assertRaisesRegex(ValueError, "same"):
            children_by_label(node)


class RequirePositiveDimensionsTests(unittest.TestCase):
    def test_accepts_positive_numeric_fields_and_skips_the_rest(self):
        require_positive_dimensions(Sample())

    def test_names_the_offending_field(self):
        for changes, field in (
            ({"width": 0.0}, "width"),
            ({"length": -1.0}, "length"),
            ({"width": float("nan")}, "width"),
        ):
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, field):
                require_positive_dimensions(replace(Sample(), **changes))

    def test_zero_is_allowed_only_on_request(self):
        zero = replace(Sample(), length=0.0)
        with self.assertRaises(ValueError):
            require_positive_dimensions(zero)
        require_positive_dimensions(zero, allow_zero=True)
        with self.assertRaises(ValueError):
            require_positive_dimensions(replace(Sample(), length=-0.1), allow_zero=True)

    def test_parameter_classes_report_the_field(self):
        with self.assertRaisesRegex(ValueError, "plate_width"):
            replace(CarriageParameters(), plate_width=0.0).validate()
        FrameParameters().validate()  # Zero setbacks are legitimate there.


if __name__ == "__main__":
    unittest.main()

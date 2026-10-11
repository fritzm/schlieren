"""Checks shared by the parameter classes' `validate` methods."""

from math import isfinite


def require_positive_dimensions(params, *, allow_zero: bool = False) -> None:
    """Raise ValueError naming the first numeric field of a parameter dataclass that is not usable.

    Every numeric field must be finite and positive (or non-negative with allow_zero). Fields that are not
    numbers, such as tuples of points, are left to the class's own checks.
    """
    for name, value in vars(params).items():
        if isinstance(value, bool) or not isinstance(value, int | float):
            continue
        if not isfinite(value) or value < 0 or (value == 0 and not allow_zero):
            kind = "finite and non-negative" if allow_zero else "finite and positive"
            raise ValueError(f"{type(params).__name__}.{name} must be {kind}, got {value}")

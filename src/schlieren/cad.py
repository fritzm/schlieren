"""Shared build123d helpers: alignments, axis planes, and labeled viewer assemblies.

Assemblies are `Compound`s whose children are labeled, colored, and already placed in the assembly frame.
build123d shapes can have only one parent and keep a stale parent reference when copied or moved, so
children are always fresh wrappers made by `labeled`; never re-parent a shape taken from another assembly,
and detach a child with `labeled` before exporting it (STEP export of an attached child fails).
"""

from build123d import (
    Align,
    Color,
    Compound,
    Face,
    Helix,
    Location,
    Part,
    Plane,
    Pos,
    Shape,
    Solid,
    Wire,
    export_step,
    export_stl,
)
from build123d.topology.shape_core import downcast

ON_FLOOR = (Align.CENTER, Align.CENTER, Align.MIN)  # Centered in the plane, rising from it.
FROM_CORNER = (Align.MIN, Align.MIN, Align.MIN)
EXPORTERS = {"step": export_step, "stl": export_stl}  # By export kind, as `EXPORTERS[kind](part, path)`.
BLACK_ANODIZED = (0.2, 0.2, 0.22)  # Viewer color for black-anodized aluminum (Thorlabs SM1 optomechanics).


def along_x(origin) -> Plane:
    """Plane at origin whose normal (the axis of a cylinder or cone placed on it) is +x."""
    return Plane(origin=origin, x_dir=(0, 1, 0), z_dir=(1, 0, 0))


def along_y(origin) -> Plane:
    """Plane at origin whose normal is +y, with local x along global x."""
    return Plane(origin=origin, x_dir=(1, 0, 0), z_dir=(0, 1, 0))


def compression_spring(outer_diameter: float, wire_diameter: float, length: float, coils: float) -> Part:
    """A plain helix of round wire for display, axis +z from z=0 to z=length.

    An illustration: the ends are not closed and ground, and the turn count is approximate.
    """
    height = length - wire_diameter  # Length of the wire's centerline.
    path = Helix(pitch=height / coils, height=height, radius=(outer_diameter - wire_diameter) / 2)
    section = Face(
        Wire.make_circle(wire_diameter / 2, Plane(origin=path.start_point(), z_dir=path.tangent_at(0)))
    )
    coil = Part([Solid.sweep(section, path=path, is_frenet=True)])
    return Pos(0, 0, wire_diameter / 2) * coil


def _located(shape: Shape, loc: Location | None) -> Shape:
    """shape moved by loc, sharing its geometry.

    `loc * shape` deep-copies the whole B-rep and then discards the copy, which dominates the cost of
    placing vendor models in a large assembly. Moving the underlying OCCT shape only composes locations.
    """
    if loc is None:
        return shape
    return Shape.cast(downcast(shape.wrapped.Moved(loc.wrapped)))


def labeled(
    shape: Shape, label: str, color: Color | tuple | None = None, loc: Location | None = None
) -> Part:
    """A parentless copy of shape's solids for use as an assembly child, optionally moved by loc.

    The solids are regrouped flat: build123d reports zero volume for a compound nested inside a compound.
    """
    if color is not None and not isinstance(color, Color):
        color = Color(*color)
    return Part(Compound(_located(shape, loc).solids()).wrapped, label=label, color=color)


def assembly(label: str, children) -> Compound:
    return Compound(label=label, children=list(children))


def place(loc: Location, node: Shape) -> Shape:
    """Copy of an assembly (or a single labeled child) moved by loc; moving a Compound leaves its children behind."""
    if node.children:
        return assembly(node.label, (place(loc, child) for child in node.children))
    return labeled(node, node.label, node.color, loc)


def children_by_label(node: Compound) -> dict[str, Shape]:
    """Direct children of an assembly, keyed by label."""
    return {child.label: child for child in node.children}


def leaves(node: Shape) -> list[Shape]:
    """Every part in an assembly, through any nested sub-assemblies."""
    if not node.children:
        return [node]
    return [leaf for child in node.children for leaf in leaves(child)]

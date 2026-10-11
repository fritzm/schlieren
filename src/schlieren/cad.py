"""Shared build123d helpers: alignments, axis planes, primitive solids, and labeled viewer assemblies.

Assemblies are `Compound`s whose children are labeled, colored, and already placed in the assembly frame.
build123d shapes can have only one parent and keep a stale parent reference when copied or moved, so
children are always fresh wrappers made by `labeled`; never re-parent a shape taken from another assembly,
and detach a child with `labeled` before exporting it (STEP export of an attached child fails).
"""

from math import cos, pi

from build123d import (
    Align,
    Box,
    Color,
    Compound,
    Cone,
    Cylinder,
    Face,
    Helix,
    Location,
    Part,
    Plane,
    Pos,
    RegularPolygon,
    Shape,
    Solid,
    Wire,
    export_step,
    export_stl,
    extrude,
)
from build123d.topology.shape_core import downcast

ON_FLOOR = (Align.CENTER, Align.CENTER, Align.MIN)  # Centered in the plane, rising from it.
FROM_CORNER = (Align.MIN, Align.MIN, Align.MIN)
CUT_OVERRUN = 1.0  # mm a cutting tool extends past the faces it cuts through, so the cut is clean.
EXPORTERS = {"step": export_step, "stl": export_stl}  # By export kind, as `EXPORTERS[kind](part, path)`.


def along_x(origin) -> Plane:
    """Plane at origin whose normal (the axis of a cylinder or cone placed on it) is +x."""
    return Plane(origin=origin, x_dir=(0, 1, 0), z_dir=(1, 0, 0))


def along_y(origin) -> Plane:
    """Plane at origin whose normal is +y, with local x along global x."""
    return Plane(origin=origin, x_dir=(1, 0, 0), z_dir=(0, 1, 0))


def box_between(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> Part:
    """Box spanning the given extents."""
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=FROM_CORNER)


def floor_box(width: float, length: float, height: float, x: float = 0, y: float = 0, z: float = 0) -> Part:
    """Box width (x) by length (y) by height (z), centered on (x, y) and standing on z."""
    return Pos(x, y, z) * Box(width, length, height, align=ON_FLOOR)


def centered_box(
    width: float, length: float, height: float, x: float = 0, y: float = 0, z: float = 0
) -> Part:
    """Box width (x) by length (y) by height (z), centered on (x, y, z)."""
    return Pos(x, y, z) * Box(width, length, height)


def centered_cylinder(diameter: float, height: float, x: float = 0, y: float = 0, z: float = 0) -> Part:
    """Cylinder along z, centered on (x, y, z)."""
    return Pos(x, y, z) * Cylinder(diameter / 2, height)


def x_cylinder(diameter: float, y: float, z: float, x0: float, x1: float) -> Part:
    """Cylinder along +x from x0 to x1, its axis through (y, z)."""
    return along_x((x0, y, z)) * Cylinder(diameter / 2, x1 - x0, align=ON_FLOOR)


def y_cylinder(diameter: float, x: float, z: float, y0: float, y1: float) -> Part:
    """Cylinder along +y from y0 to y1, its axis through (x, z)."""
    return along_y((x, y0, z)) * Cylinder(diameter / 2, y1 - y0, align=ON_FLOOR)


def z_cylinder(diameter: float, x: float, y: float, z0: float, z1: float) -> Part:
    """Cylinder along +z from z0 to z1, its axis through (x, y)."""
    return Pos(x, y, z0) * Cylinder(diameter / 2, z1 - z0, align=ON_FLOOR)


def y_cone(diameter0: float, diameter1: float, x: float, z: float, y0: float, y1: float) -> Part:
    """Cone (or frustum) along +y from y0 to y1, its axis through (x, z), tapering from diameter0 to diameter1."""
    return along_y((x, y0, z)) * Cone(diameter0 / 2, diameter1 / 2, y1 - y0, align=ON_FLOOR)


def z_cone(diameter0: float, diameter1: float, x: float, y: float, z0: float, z1: float) -> Part:
    """Cone (or frustum) along +z from z0 to z1, its axis through (x, y), tapering from diameter0 to diameter1."""
    return Pos(x, y, z0) * Cone(diameter0 / 2, diameter1 / 2, z1 - z0, align=ON_FLOOR)


def _hexagon(across_flats: float) -> RegularPolygon:
    return RegularPolygon(across_flats / cos(pi / 6) / 2, 6)  # Corners on the local x axis.


def y_hex(across_flats: float, x: float, z: float, y0: float, y1: float) -> Part:
    """Hexagonal prism along +y from y0 to y1 with its corners along x (flats facing ±z)."""
    return extrude(along_y((x, y0, z)) * _hexagon(across_flats), amount=y1 - y0)


def z_hex(across_flats: float, x: float, y: float, z0: float, z1: float) -> Part:
    """Hexagonal prism along +z from z0 to z1 with its corners along x (flats facing ±y)."""
    return extrude(Pos(x, y, z0) * _hexagon(across_flats), amount=z1 - z0)


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


def moved(shape: Shape, loc: Location | None) -> Shape:
    """shape moved by loc, sharing its geometry; use it in place of `loc * shape` for large models.

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
    return Part(Compound(moved(shape, loc).solids()).wrapped, label=label, color=color)


def assembly(label: str, children) -> Compound:
    return Compound(label=label, children=list(children))


def place(loc: Location, node: Shape) -> Shape:
    """Copy of an assembly (or a single labeled child) moved by loc; moving a Compound leaves its children behind."""
    if node.children:
        return assembly(node.label, (place(loc, child) for child in node.children))
    return labeled(node, node.label, node.color, loc)


def children_by_label(node: Compound) -> dict[str, Shape]:
    """Direct children of an assembly, keyed by label; raises if two children share one."""
    by_label = {}
    for child in node.children:
        if child.label in by_label:
            raise ValueError(f"{node.label!r} has more than one child labeled {child.label!r}")
        by_label[child.label] = child
    return by_label


def leaves(node: Shape) -> list[Shape]:
    """Every part in an assembly, through any nested sub-assemblies."""
    if not node.children:
        return [node]
    return [leaf for child in node.children for leaf in leaves(child)]

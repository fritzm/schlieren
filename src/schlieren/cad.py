"""Shared build123d helpers: alignments, axis planes, and labeled viewer assemblies.

Assemblies are `Compound`s whose children are labeled, colored, and already placed in the assembly frame.
build123d shapes can have only one parent and keep a stale parent reference when copied or moved, so
children are always fresh wrappers made by `labeled`; never re-parent a shape taken from another assembly,
and detach a child with `labeled` before exporting it (STEP export of an attached child fails).
"""

from build123d import Align, Color, Compound, Location, Part, Plane, Shape, export_step, export_stl

ON_FLOOR = (Align.CENTER, Align.CENTER, Align.MIN)  # Centered in the plane, rising from it.
FROM_CORNER = (Align.MIN, Align.MIN, Align.MIN)
EXPORTERS = {"step": export_step, "stl": export_stl}  # By export kind, as `EXPORTERS[kind](part, path)`.


def along_x(origin) -> Plane:
    """Plane at origin whose normal (the axis of a cylinder or cone placed on it) is +x."""
    return Plane(origin=origin, x_dir=(0, 1, 0), z_dir=(1, 0, 0))


def along_y(origin) -> Plane:
    """Plane at origin whose normal is +y, with local x along global x."""
    return Plane(origin=origin, x_dir=(1, 0, 0), z_dir=(0, 1, 0))


def labeled(
    shape: Shape, label: str, color: Color | tuple | None = None, loc: Location | None = None
) -> Part:
    """A parentless copy of shape's solids for use as an assembly child, optionally moved by loc.

    The solids are regrouped flat: build123d reports zero volume for a compound nested inside a compound.
    """
    if color is not None and not isinstance(color, Color):
        color = Color(*color)
    moved = shape if loc is None else loc * shape
    return Part(Compound(moved.solids()).wrapped, label=label, color=color)


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

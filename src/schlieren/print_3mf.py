"""PrusaSlicer 3MF files: read the embedded profile and the placed mesh, and build a 3MF from a mesh.

A bare command-line 3MF has no embedded settings and places items off the bed, so a new 3MF is built by
swapping the mesh into a template saved by the PrusaSlicer GUI. The template carries the profile in
`Metadata/Slic3r_PE.config`, which the command-line slicer then honors.
"""

import re
import struct
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

CONFIG_PATH = "Metadata/Slic3r_PE.config"
MODEL_CONFIG_PATH = "Metadata/Slic3r_PE_model.config"
MODEL_PATH = "3D/3dmodel.model"
CORE_NS = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"

WELD_DECIMALS = 3  # STL stores float32, so vertices that should coincide agree to well under 0.001 mm.
IDENTITY_MATRIX_16 = "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"
_STL_TRIANGLE = np.dtype([("normal", "<3f4"), ("vertices", "<9f4"), ("attribute", "<u2")])
_ASCII_VERTEX = re.compile(rb"vertex\s+(\S+)\s+(\S+)\s+(\S+)")
_UP = re.compile(r"([+-]?)([xyz])")
# A box's eight corners (x fastest, then y, then z) and its twelve triangles, counter-clockwise from outside.
_BOX_CORNERS = np.array([[x, y, z] for z in (0, 1) for y in (0, 1) for x in (0, 1)])
_BOX_FACES = np.array([
    (0, 2, 1), (1, 2, 3), (4, 5, 6), (5, 7, 6), (0, 1, 4), (1, 5, 4),
    (2, 6, 3), (3, 6, 7), (0, 4, 2), (2, 4, 6), (1, 3, 5), (3, 7, 5),
])  # fmt: skip
Box = tuple[float, float, float, float, float, float]  # x0, y0, z0, x1, y1, z1


def config_value(config: str, key: str) -> str:
    match = re.search(rf"^; {re.escape(key)} = (.*)$", config, re.MULTILINE)
    if match is None:
        raise ValueError(f"{CONFIG_PATH} has no '{key}' setting")
    return match.group(1).strip()


def read_config(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        return archive.read(CONFIG_PATH).decode("utf-8")


def bed_size(config: str) -> tuple[float, float]:
    """(x, y) extent of the bed from `bed_shape`, which is the corner list of a rectangle."""
    corners = [
        tuple(map(float, corner.split("x"))) for corner in config_value(config, "bed_shape").split(",")
    ]
    xs, ys = zip(*corners, strict=True)
    return max(xs) - min(xs), max(ys) - min(ys)


def _attribute(element: ET.Element, name: str) -> str:
    value = element.get(name)
    if value is None:
        raise ValueError(f"3MF <{element.tag.removeprefix(CORE_NS)}> element has no '{name}' attribute")
    return value


def read_placed_mesh(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """All build items of the 3MF as one triangle mesh in bed coordinates: (vertices (n, 3), triangles (m, 3))."""
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read(MODEL_PATH))
    objects = {}
    for obj in root.iter(f"{CORE_NS}object"):
        mesh = obj.find(f"{CORE_NS}mesh")
        if mesh is None:
            raise ValueError(f"object {obj.get('id')} has no mesh (components are not supported)")
        vertices = np.array(
            [[float(_attribute(v, axis)) for axis in "xyz"] for v in mesh.iter(f"{CORE_NS}vertex")]
        )
        triangles = np.array(
            [
                [int(_attribute(t, corner)) for corner in ("v1", "v2", "v3")]
                for t in mesh.iter(f"{CORE_NS}triangle")
            ]
        )
        objects[_attribute(obj, "id")] = (vertices, triangles)

    all_vertices, all_triangles, offset = [], [], 0
    for item in root.iter(f"{CORE_NS}item"):
        vertices, triangles = objects[_attribute(item, "objectid")]
        # 3MF transforms are twelve numbers: a 3 x 3 matrix applied to row vectors, then a translation.
        m = np.array(item.get("transform", "1 0 0 0 1 0 0 0 1 0 0 0").split(), dtype=float)
        all_vertices.append(vertices @ m[:9].reshape(3, 3) + m[9:])
        all_triangles.append(triangles + offset)
        offset += len(vertices)
    if not all_vertices:
        raise ValueError(f"{path} has no build items")
    return np.concatenate(all_vertices), np.concatenate(all_triangles)


def mesh_volume(vertices: np.ndarray, triangles: np.ndarray) -> float:
    """Enclosed volume, mm^3, from the signed tetrahedra to the origin; exact for a closed, outward mesh."""
    a, b, c = (vertices[triangles[:, i]] for i in range(3))
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6)


def read_stl(path: Path) -> np.ndarray:
    """The triangle soup of an STL, binary or ASCII, as (n, 3, 3)."""
    data = path.read_bytes()
    if len(data) >= 84 and 84 + struct.unpack_from("<I", data, 80)[0] * 50 == len(data):
        count = struct.unpack_from("<I", data, 80)[0]
        triangles = np.frombuffer(data, _STL_TRIANGLE, count=count, offset=84)
        return triangles["vertices"].reshape(-1, 3, 3).astype(float)
    points = np.array(_ASCII_VERTEX.findall(data), dtype=float)
    if len(points) == 0 or len(points) % 3:
        raise ValueError(f"{path} is not a readable STL")
    return points.reshape(-1, 3, 3)


def rotation_to_up(up: str) -> np.ndarray:
    """The rotation (a proper one) that carries the model axis named by `up` ("+z", "-y", "x", ...) to +z."""
    match = _UP.fullmatch(up.strip().lower())
    if match is None:
        raise ValueError(f"cannot read up axis {up!r}; use one of +x -x +y -y +z -z")
    axis = np.zeros(3)
    axis["xyz".index(match.group(2))] = -1.0 if match.group(1) == "-" else 1.0
    z = np.array([0.0, 0.0, 1.0])
    if np.allclose(axis, z):
        return np.eye(3)
    if np.allclose(axis, -z):
        return np.diag([1.0, -1.0, -1.0])  # Half turn about x.
    # Rodrigues: the rotation about axis x z that takes axis to z.
    v = np.cross(axis, z)
    skew = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + skew + skew @ skew / (1 + float(axis @ z))


def _part_volume_entry(first: int, last: int, name: str) -> str:
    """A PrusaSlicer model-config volume: a plain model part (it is merged into the object when slicing)."""
    return f"""  <volume firstid="{first}" lastid="{last}">
   <metadata type="volume" key="name" value="{name}"/>
   <metadata type="volume" key="volume_type" value="ModelPart"/>
   <metadata type="volume" key="matrix" value="{IDENTITY_MATRIX_16}"/>
   <metadata type="volume" key="extruder" value="0"/>
   <mesh edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
  </volume>
"""


@dataclass(frozen=True)
class BuiltMesh:
    vertices: int
    triangles: int
    open_edges: int  # Edges not shared by exactly two triangles of opposite sense; 0 for a closed mesh.
    size: tuple[float, float, float]
    volume: float  # mm^3


def _open_edges(triangles: np.ndarray) -> int:
    edges = Counter()
    for a, b, c in triangles.tolist():
        edges.update(((a, b), (b, c), (c, a)))
    return sum(1 for (a, b), count in edges.items() if count != 1 or edges.get((b, a), 0) != 1)


def build_3mf(
    stl: Path,
    template: Path,
    output: Path,
    up: str = "+z",
    name: str | None = None,
    boxes: Sequence[Box] = (),
) -> BuiltMesh:
    """Write output: the STL, turned so `up` points up, centered on the template's item position, resting on
    the bed, in the template's profile. `name` titles the object (default: the output's name).

    `boxes` are extra model parts, each a box in the STL's own frame (x0, y0, z0, x1, y1, z1). They are added
    as separate parts of the object, as the slicer's Add part > Box does, so they are merged into the object
    for slicing. Use one for a sacrificial feature that exists only to change the slice, such as a web that
    closes a split ring's first-layer outline so its brim stays out of the bore.
    """
    name = name or output.stem
    rotation = rotation_to_up(up)
    soup = read_stl(stl) @ rotation.T
    vertices, inverse = np.unique(np.round(soup.reshape(-1, 3), WELD_DECIMALS), axis=0, return_inverse=True)
    triangles = inverse.reshape(-1, 3)
    triangles = triangles[
        (triangles[:, 0] != triangles[:, 1])
        & (triangles[:, 1] != triangles[:, 2])
        & (triangles[:, 0] != triangles[:, 2])
    ]
    low, high = vertices.min(axis=0), vertices.max(axis=0)

    with zipfile.ZipFile(template) as source:
        model = source.read(MODEL_PATH).decode("utf-8")
        model_config = source.read(MODEL_CONFIG_PATH).decode("utf-8")
        item = re.search(r'<item [^>]*transform="([^"]*)"', model)
        if item is None:
            raise ValueError(f"{template} has no build item to take the bed position from")
        center = [float(v) for v in item.group(1).split()[9:11]]
        offset = np.array([(low[0] + high[0]) / 2, (low[1] + high[1]) / 2, low[2]])
        placed = vertices - offset
        if boxes and model_config.count("<volume ") != 1:
            raise ValueError(f"{template} must hold a single volume to add parts to it")
        all_vertices, all_triangles, volumes = [placed], [triangles], ""
        for box in boxes:
            lower, upper = np.array(box[:3], float), np.array(box[3:], float)
            if np.any(upper <= lower):
                raise ValueError(f"box {box} must have x0 < x1, y0 < y1, z0 < z1")
            corners = (lower + _BOX_CORNERS * (upper - lower)) @ rotation.T - offset
            box_vertices = np.array([corners.min(axis=0), corners.max(axis=0)])
            first = sum(len(t) for t in all_triangles)
            start = sum(len(v) for v in all_vertices)
            all_vertices.append(box_vertices[0] + _BOX_CORNERS * (box_vertices[1] - box_vertices[0]))
            all_triangles.append(_BOX_FACES + start)
            volumes += _part_volume_entry(first, first + len(_BOX_FACES) - 1, f"Web {len(all_vertices) - 1}")
        every_vertex, every_triangle = np.concatenate(all_vertices), np.concatenate(all_triangles)

        head = model[: model.index("<resources>")]
        head = re.sub(r'(name="Title">)[^<]*', rf"\g<1>{name}", head)
        head = re.sub(r'(name="Description">)[^<]*', rf"\g<1>{name}", head)
        vertex_lines = "\n".join(
            f'     <vertex x="{x:.7g}" y="{y:.7g}" z="{z:.7g}"/>' for x, y, z in every_vertex
        )
        triangle_lines = "\n".join(
            f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in every_triangle
        )
        body = f"""<resources>
  <object id="1" type="model">
   <mesh>
    <vertices>
{vertex_lines}
    </vertices>
    <triangles>
{triangle_lines}
    </triangles>
   </mesh>
  </object>
 </resources>
 <build>
  <item objectid="1" transform="1 0 0 0 1 0 0 0 1 {center[0]:g} {center[1]:g} 0" printable="1"/>
 </build>
</model>
"""
        model_config = re.sub(r'value="[^"]*\.stl"', f'value="{name}.stl"', model_config)
        model_config = re.sub(r'lastid="\d+"', f'lastid="{len(triangles) - 1}"', model_config)
        model_config = re.sub(
            r'key="matrix" value="[^"]*"', f'key="matrix" value="{IDENTITY_MATRIX_16}"', model_config
        )
        model_config = re.sub(r'(key="source_offset_[xyz]" value=")[^"]*', r"\g<1>0", model_config)
        model_config = model_config.replace(" </object>", volumes + " </object>")

        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
            for info in source.infolist():
                if info.filename == MODEL_PATH:
                    target.writestr(info.filename, head + body)
                elif info.filename == MODEL_CONFIG_PATH:
                    target.writestr(info.filename, model_config)
                else:
                    target.writestr(info, source.read(info.filename))
    return BuiltMesh(
        vertices=len(vertices),
        triangles=len(triangles),
        open_edges=_open_edges(triangles),
        size=tuple(float(v) for v in high - low),  # ty: ignore[invalid-argument-type]
        volume=mesh_volume(placed, triangles),
    )

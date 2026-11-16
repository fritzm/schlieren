"""Printer thumbnails: render the model of a PrusaSlicer 3MF, as placed on the bed, in the sizes and formats the
3MF's printer profile asks for (`; thumbnails = 16x16/QOI, 220x124/QOI, ...` in Metadata/Slic3r_PE.config).

The command-line slicer writes none of these, so the MINI+ shows no preview of a CLI-sliced file; `make-bgcode
thumbnails` puts these into the bgcode. The look is PrusaSlicer's own: an orange model on a dark bed, seen from
the front and above. Every thumbnail is rendered at SUPERSAMPLE times its size and averaged down, which keeps
the 16 x 16 one readable.
"""

import re
from dataclasses import dataclass
from math import atan, sqrt
from pathlib import Path

import numpy as np
import vtk
from vtkmodules.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray, vtk_to_numpy

from schlieren.bgcode import ImageFormat
from schlieren.image_codecs import encode_png, encode_qoi
from schlieren.print_3mf import bed_size, config_value, read_config, read_placed_mesh
from schlieren.render import (
    KEY_LIGHT_INTENSITY,
    KEY_TO_FILL_RATIO,
    PERSPECTIVE_CENTERING_PASSES,
    PERSPECTIVE_DISTANCE,
)

TOWARD_VIEWER = (0.35, -1.0, 0.85)  # Model frame, z up, +y away from the front of the bed.
MARGIN_FRACTION = 0.08  # Of the framed extent, on every side.
SUPERSAMPLE = 4
MODEL_COLOR = (0.95, 0.48, 0.0)
BED_COLOR = (0.30, 0.30, 0.30)
GRID_COLOR = (0.55, 0.55, 0.55)
BACKGROUND_COLOR = (0.12, 0.12, 0.12)
GRID_SPACING = 50.0  # mm
SURFACE_AMBIENT = 0.25
BED_BELOW_MODEL = 0.05  # mm; keeps the bed plane from z-fighting with the model's first layer.

_THUMBNAIL_ENTRY = re.compile(r"(\d+)x(\d+)/(PNG|JPG|QOI)")
_ENCODERS = {ImageFormat.PNG: encode_png, ImageFormat.QOI: encode_qoi}


@dataclass(frozen=True)
class ThumbnailSpec:
    width: int
    height: int
    format: ImageFormat


def thumbnail_specs(config: str) -> list[ThumbnailSpec]:
    """The thumbnails the profile asks for, in order. JPG is recognized but not supported."""
    value = config_value(config, "thumbnails")
    entries = [entry.strip() for entry in value.split(",") if entry.strip()]
    specs = []
    for entry in entries:
        match = _THUMBNAIL_ENTRY.fullmatch(entry)
        if match is None:
            raise ValueError(f"cannot read thumbnail entry {entry!r} in '{value}'")
        image_format = ImageFormat[match.group(3)]
        if image_format not in _ENCODERS:
            raise ValueError(f"thumbnail format {image_format.name} is not supported (entry {entry!r})")
        specs.append(ThumbnailSpec(int(match.group(1)), int(match.group(2)), image_format))
    return specs


def _polydata(vertices: np.ndarray, triangles: np.ndarray) -> vtk.vtkPolyData:
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(np.ascontiguousarray(vertices, dtype=float), deep=True))
    cells = np.column_stack([np.full(len(triangles), 3), triangles]).astype(np.int64).ravel()
    cell_array = vtk.vtkCellArray()
    cell_array.ImportLegacyFormat(numpy_to_vtkIdTypeArray(cells, deep=True))
    mesh = vtk.vtkPolyData()
    mesh.SetPoints(points)
    mesh.SetPolys(cell_array)
    return mesh


def _bed_actors(bed: tuple[float, float], z: float) -> list[vtk.vtkActor]:
    width, depth = bed
    plane = np.array([[0, 0, z], [width, 0, z], [width, depth, z], [0, depth, z]], dtype=float)
    surface = vtk.vtkActor()
    surface_mapper = vtk.vtkPolyDataMapper()
    surface.SetMapper(surface_mapper)
    surface_mapper.SetInputData(_polydata(plane, np.array([[0, 1, 2], [0, 2, 3]])))
    surface.GetProperty().SetColor(*BED_COLOR)
    surface.GetProperty().LightingOff()

    grid_points, grid_lines = [], []
    for x in np.arange(0, width + 1e-6, GRID_SPACING):
        grid_lines.append((len(grid_points), len(grid_points) + 1))
        grid_points += [(x, 0, z), (x, depth, z)]
    for y in np.arange(0, depth + 1e-6, GRID_SPACING):
        grid_lines.append((len(grid_points), len(grid_points) + 1))
        grid_points += [(0, y, z), (width, y, z)]
    grid = vtk.vtkPolyData()
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(np.array(grid_points, dtype=float), deep=True))
    grid.SetPoints(points)
    lines = vtk.vtkCellArray()
    for a, b in grid_lines:
        lines.InsertNextCell(2, (a, b))
    grid.SetLines(lines)
    grid_actor = vtk.vtkActor()
    grid_mapper = vtk.vtkPolyDataMapper()
    grid_actor.SetMapper(grid_mapper)
    grid_mapper.SetInputData(grid)
    grid_actor.GetProperty().SetColor(*GRID_COLOR)
    grid_actor.GetProperty().LightingOff()
    return [surface, grid_actor]


def _frame_camera(camera: vtk.vtkCamera, vertices: np.ndarray, aspect: float) -> None:
    """Aim the camera along TOWARD_VIEWER at the vertices, centered and filling the view with a margin."""
    toward_viewer = np.array(TOWARD_VIEWER) / np.linalg.norm(TOWARD_VIEWER)
    page_x = np.cross([0, 0, 1], toward_viewer)
    page_x /= np.linalg.norm(page_x)
    page_y = np.cross(toward_viewer, page_x)
    extents = vertices @ np.array([page_x, page_y, toward_viewer]).T  # (page x, page y, depth toward viewer)
    low, high = extents.min(axis=0), extents.max(axis=0)
    middle = (low + high) / 2
    distance = PERSPECTIVE_DISTANCE * sqrt(float(np.sum((high - low) ** 2)))
    # Perspective framing in tangent space, as render.render_figure does: slide the view axis until the
    # vertices are centered about it, then open the lens to fit.
    for _ in range(PERSPECTIVE_CENTERING_PASSES):
        depth = distance - (extents[:, 2] - middle[2])
        tangents = (extents[:, :2] - middle[:2]) / depth[:, None]
        tangent_low, tangent_high = tangents.min(axis=0), tangents.max(axis=0)
        middle[:2] += distance * (tangent_low + tangent_high) / 2
    depth = distance - (extents[:, 2] - middle[2])
    tangents = (extents[:, :2] - middle[:2]) / depth[:, None]
    half_x = float(np.abs(tangents[:, 0]).max())
    half_y = float(np.abs(tangents[:, 1]).max())
    half_height = max(half_y, half_x / aspect) * (1 + 2 * MARGIN_FRACTION)

    focal_point = page_x * middle[0] + page_y * middle[1] + toward_viewer * middle[2]
    camera.SetParallelProjection(False)
    camera.SetFocalPoint(*focal_point)
    camera.SetPosition(*(focal_point + toward_viewer * distance))
    camera.SetViewUp(*page_y)
    camera.SetViewAngle(2 * np.degrees(atan(half_height)))


def render_thumbnail_pixels(
    vertices: np.ndarray, triangles: np.ndarray, bed: tuple[float, float], width: int, height: int
) -> np.ndarray:
    """The model on the bed as an opaque (height, width, 4) uint8 RGBA image."""
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(*BACKGROUND_COLOR)
    for actor in _bed_actors(bed, float(vertices[:, 2].min()) - BED_BELOW_MODEL):
        renderer.AddActor(actor)

    normals = vtk.vtkPolyDataNormals()
    normals.SetInputData(_polydata(vertices, triangles))
    normals.SplittingOn()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    model = vtk.vtkActor()
    model.SetMapper(mapper)
    model.GetProperty().SetColor(*MODEL_COLOR)
    model.GetProperty().SetAmbient(SURFACE_AMBIENT)
    renderer.AddActor(model)

    _frame_camera(renderer.GetActiveCamera(), vertices, width / height)
    renderer.ResetCameraClippingRange()
    lights = vtk.vtkLightKit()
    lights.SetKeyLightIntensity(KEY_LIGHT_INTENSITY)
    lights.SetKeyToFillRatio(KEY_TO_FILL_RATIO)
    lights.AddLightsToRenderer(renderer)

    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(True)
    window.SetMultiSamples(0)
    window.SetSize(width * SUPERSAMPLE, height * SUPERSAMPLE)
    window.AddRenderer(renderer)
    window.Render()
    capture = vtk.vtkWindowToImageFilter()
    capture.SetInput(window)
    capture.SetInputBufferTypeToRGBA()
    capture.ReadFrontBufferOff()
    capture.Update()
    image = capture.GetOutput()
    columns, rows, _ = image.GetDimensions()
    pixels = vtk_to_numpy(image.GetPointData().GetScalars()).reshape(rows, columns, -1)[::-1]
    if columns % width or rows % height or columns // width != rows // height:
        raise RuntimeError(f"rendered {columns} x {rows} pixels for a {width} x {height} thumbnail")
    factor = columns // width
    averaged = pixels.reshape(height, factor, width, factor, -1).astype(float).mean(axis=(1, 3))
    result = np.round(averaged).astype(np.uint8)
    result[..., 3] = 255
    return result


def render_thumbnails(model: Path) -> list[tuple[ThumbnailSpec, bytes]]:
    """Each thumbnail the model's 3MF profile asks for, encoded."""
    config = read_config(model)
    specs = thumbnail_specs(config)
    vertices, triangles = read_placed_mesh(model)
    bed = bed_size(config)
    return [
        (
            spec,
            _ENCODERS[spec.format](
                render_thumbnail_pixels(vertices, triangles, bed, spec.width, spec.height)
            ),
        )
        for spec in specs
    ]

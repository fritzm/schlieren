"""Offscreen shaded renders of labeled assemblies: transparent-background PNG figures for the design document.

    render_figure(viewer_assembly(shoe), Path("docs/design/figures/rail-shoe.png"), (1, 1, 0.8))

Each part is drawn in its assembly color with its sharp edges and silhouette outlined. The PNG is rendered by
the local OpenGL driver, so regenerating it on another machine may differ in the low bits.
"""

from math import atan, degrees, sqrt
from pathlib import Path

import vtk
from build123d import Shape, Vector

from schlieren.cad import leaves

FIGURE_WIDTH_PX = 500  # On-page width; the fragment's <img width> must match.
FIGURE_PIXEL_RATIO = (
    2  # Rendered pixels per on-page pixel, so the figure stays sharp on high-density displays.
)
FIGURE_MARGIN_FRACTION = 0.03  # Of the figure width, on every side.
MESH_TOLERANCE = 0.02  # Tessellation deviation, mm.
MESH_ANGULAR_TOLERANCE = 0.1  # rad
FEATURE_ANGLE = (
    30.0  # deg; mesh edges sharper than this are outlined, and shading is not smoothed across them.
)
OUTLINE_COLOR = (0.1, 0.1, 0.1)
OUTLINE_WIDTH_PX = 1.25  # On-page.
MULTISAMPLES = 8
# Lighting is kept bright and low-contrast so shaded faces stay distinct from a dark page background.
SURFACE_AMBIENT = 0.2
KEY_LIGHT_INTENSITY = 0.85
KEY_TO_FILL_RATIO = 1.5
VIEW_DISTANCE = 1000.0  # Parallel-projection camera standoff; only the direction matters.
PERSPECTIVE_DISTANCE = (
    2.5  # Perspective camera standoff, in scene bounding-box diagonals; smaller is stronger.
)
PERSPECTIVE_CENTERING_PASSES = 8


def _mesh(shape: Shape) -> vtk.vtkPolyData:
    """Triangle mesh of shape, with the vertices that build123d repeats per face merged."""
    vertices, triangles = shape.tessellate(MESH_TOLERANCE, MESH_ANGULAR_TOLERANCE)
    points = vtk.vtkPoints()
    for v in vertices:
        points.InsertNextPoint(v.X, v.Y, v.Z)
    cells = vtk.vtkCellArray()
    for triangle in triangles:
        cells.InsertNextCell(3, triangle)
    raw = vtk.vtkPolyData()
    raw.SetPoints(points)
    raw.SetPolys(cells)
    clean = vtk.vtkCleanPolyData()
    clean.SetInputData(raw)
    clean.Update()
    return clean.GetOutput()


def _actor(source: vtk.vtkAlgorithm) -> vtk.vtkActor:
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(source.GetOutputPort())
    mapper.ScalarVisibilityOff()
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    return actor


def _outline_actor(source: vtk.vtkAlgorithm) -> vtk.vtkActor:
    actor = _actor(source)
    actor.GetProperty().SetColor(*OUTLINE_COLOR)
    actor.GetProperty().SetLineWidth(OUTLINE_WIDTH_PX * FIGURE_PIXEL_RATIO)
    actor.GetProperty().LightingOff()
    return actor


def render_figure(
    assembly: Shape, path: Path, view_direction: tuple[float, float, float], perspective: bool = False
) -> None:
    """Write a shaded PNG of assembly, seen from view_direction (model frame, z up).

    The projection is parallel unless perspective is set, which puts the camera PERSPECTIVE_DISTANCE scene
    diagonals away.
    """
    toward_viewer = Vector(view_direction).normalized()
    page_x = Vector(0, 0, 1).cross(toward_viewer).normalized()
    page_y = toward_viewer.cross(page_x)

    # Push surfaces back in depth so the outlines lying on them are not z-fought away.
    vtk.vtkMapper.SetResolveCoincidentTopologyToPolygonOffset()
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(1.0, 1.0, 1.0)
    renderer.SetBackgroundAlpha(0.0)
    camera = renderer.GetActiveCamera()
    camera.SetParallelProjection(not perspective)

    extents = []  # Mesh vertices in the viewport frame: (page x, page y, depth toward viewer).
    for part in leaves(assembly):
        mesh = _mesh(part)
        for i in range(mesh.GetNumberOfPoints()):
            v = Vector(*mesh.GetPoint(i))
            extents.append((v.dot(page_x), v.dot(page_y), v.dot(toward_viewer)))

        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(mesh)
        normals.SetFeatureAngle(FEATURE_ANGLE)
        normals.SplittingOn()
        surface = _actor(normals)
        surface.GetProperty().SetColor(*tuple(part.color)[:3])
        surface.GetProperty().SetAmbient(SURFACE_AMBIENT)
        renderer.AddActor(surface)

        sharp_edges = vtk.vtkFeatureEdges()
        sharp_edges.SetInputData(mesh)
        sharp_edges.SetFeatureAngle(FEATURE_ANGLE)
        sharp_edges.BoundaryEdgesOff()
        sharp_edges.ManifoldEdgesOff()
        sharp_edges.NonManifoldEdgesOff()
        sharp_edges.ColoringOff()
        renderer.AddActor(_outline_actor(sharp_edges))

        silhouette = vtk.vtkPolyDataSilhouette()
        silhouette.SetInputData(mesh)
        silhouette.SetCamera(camera)
        silhouette.SetEnableFeatureAngle(False)
        renderer.AddActor(_outline_actor(silhouette))

    low = [min(e[axis] for e in extents) for axis in range(3)]
    high = [max(e[axis] for e in extents) for axis in range(3)]
    middle = [(a + b) / 2 for a, b in zip(low, high, strict=True)]
    if perspective:
        # Frame in tangent space: each vertex's page offset from the view axis over its distance from the
        # camera. Slide the view axis until the vertices are centered about it, then open the lens to fit.
        distance = PERSPECTIVE_DISTANCE * sqrt(sum((b - a) ** 2 for a, b in zip(low, high, strict=True)))
        for _ in range(PERSPECTIVE_CENTERING_PASSES):
            tangents = [
                ((x - middle[0]) / depth, (y - middle[1]) / depth)
                for x, y, z in extents
                for depth in (distance - (z - middle[2]),)
            ]
            low = [min(t[axis] for t in tangents) for axis in range(2)]
            high = [max(t[axis] for t in tangents) for axis in range(2)]
            middle[0] += distance * (low[0] + high[0]) / 2
            middle[1] += distance * (low[1] + high[1]) / 2
    else:
        distance = VIEW_DISTANCE
    margin = FIGURE_MARGIN_FRACTION * (high[0] - low[0])
    span_x = high[0] - low[0] + 2 * margin
    span_y = high[1] - low[1] + 2 * margin
    focal_point = page_x * middle[0] + page_y * middle[1] + toward_viewer * middle[2]
    camera.SetFocalPoint(*focal_point)
    camera.SetPosition(*(focal_point + toward_viewer * distance))
    camera.SetViewUp(*page_y)
    if perspective:
        camera.SetViewAngle(degrees(2 * atan(span_y / 2)))
    else:
        camera.SetParallelScale(span_y / 2)
    renderer.ResetCameraClippingRange()

    lights = vtk.vtkLightKit()
    lights.SetKeyLightIntensity(KEY_LIGHT_INTENSITY)
    lights.SetKeyToFillRatio(KEY_TO_FILL_RATIO)
    lights.AddLightsToRenderer(renderer)

    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(True)
    window.SetAlphaBitPlanes(True)
    window.SetMultiSamples(MULTISAMPLES)
    width = FIGURE_WIDTH_PX * FIGURE_PIXEL_RATIO
    window.SetSize(width, round(width * span_y / span_x))
    window.AddRenderer(renderer)
    window.Render()

    image = vtk.vtkWindowToImageFilter()
    image.SetInput(window)
    image.SetInputBufferTypeToRGBA()
    image.ReadFrontBufferOff()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(path))
    writer.SetInputConnection(image.GetOutputPort())
    writer.Write()

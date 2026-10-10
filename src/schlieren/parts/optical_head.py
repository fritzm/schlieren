"""The tabletop optical head: the frame with the source and imaging fixtures placed on their rails (design §2).

An assembly of the other part models, for viewing and for checks that no single part model can make: that the
fixtures keep clear of each other and of the rails, and that the optical conjugates fall where §3 puts them.
Nothing is printed here and nothing is exported.

Fixture stations along the rails are setup values, not design dimensions: the slit and the cutoff are slid
along their rails to focus the system (§3.3). They are exposed as parameters of `OpticalHeadParameters`.

Coordinates are the §3.4 pivot frame (the frame model's). Each fixture is built in its own rail frame, with
the rail top at z=0 and the rail's pivot axis at the origin, then moved onto its rail by
`FrameParameters.rail_location`. Rail stations are y in the rail frame, negative aft of the pivot.
"""

from dataclasses import dataclass, field
from math import pi

from build123d import Compound, Pos

from schlieren.cad import assembly, place
from schlieren.parts.camera_support import (
    CameraSupportParameters,
    build_camera_support_assembly,
    cutoff_post_station,
)
from schlieren.parts.carriage import CarriageParameters
from schlieren.parts.frame import FrameParameters, build_frame_assembly
from schlieren.parts.light_source import (
    GREEN,
    LEDBoard,
    LightSourceParameters,
    build_light_source_assembly,
)
from schlieren.parts.slit_head import SlitHeadParameters, build_slit_head_assembly, head_location

SOURCE_SIDE = -1  # Left rail (§3.4).
IMAGING_SIDE = 1  # Right rail.
# Parts of the camera support mock-up that exist only to stand it alone; the head has the frame's rails.
STAND_ALONE_LABELS = ("Rail", "Optical axis")


@dataclass(frozen=True)
class OpticalHeadParameters:
    frame: FrameParameters = field(default_factory=FrameParameters)
    slit: SlitHeadParameters = field(default_factory=SlitHeadParameters)
    light_source: LightSourceParameters = field(default_factory=LightSourceParameters)
    carriage: CarriageParameters = field(default_factory=CarriageParameters)
    camera: CameraSupportParameters = field(default_factory=CameraSupportParameters)
    board: LEDBoard = GREEN

    # Setup values (§3.3). Station is y along the rail from its pivot, so negative.
    slit_station: float = (
        -150.0
    )  # Slit blade plane. Its post shoe clears the yaw strap, 90 mm aft of the pivot.
    cutoff_stagger: float = 0.0  # Cutoff cassette front face ahead (+) of the slit blade plane.

    @property
    def slit_post_station(self) -> float:
        """The slit post: the blade plane is the head frame's origin, aft of the post."""
        return self.slit_station - head_location(self.slit).position.Y

    @property
    def light_source_origin_station(self) -> float:
        """The LED-side SMR1/M face, u=0 in the light source model, so that the condenser's convex vertex is
        `lens_to_slit` aft of the slit blade plane."""
        ls = self.light_source
        engagement = ls.focus_engagement(self.board)
        vertex_u = ls.open_end_u(engagement) - ls.lens_vertex_inside_open_end
        return self.slit_station - ls.lens_to_slit - vertex_u

    @property
    def light_source_post_station(self) -> float:
        return self.light_source_origin_station + self.light_source.smr1_thickness / 2

    @property
    def cutoff_plane_station(self) -> float:
        """The cassette's front, media-bearing face."""
        return self.slit_station + self.cutoff_stagger

    @property
    def cutoff_post_station(self) -> float:
        """The cutoff post. In the carriage's frame the cassette front lies cassette_thickness above the datum
        pins' contact plane; rail +y is local +z, and the post is aft of the plate back."""
        c = self.carriage
        cassette_front = c.plate_thickness + c.datum_projection + c.cassette_thickness
        return self.cutoff_plane_station - (cassette_front - c.post_axis_z)

    @property
    def phone_back_station(self) -> float:
        """The back of the phone, the camera support model's y=0, on the imaging rail."""
        return self.cutoff_post_station - cutoff_post_station(self.camera, self.carriage)

    def validate(self) -> None:
        self.frame.validate()
        self.light_source.validate()
        self.slit.validate()
        self.carriage.validate()
        self.camera.validate()
        rail_rear = -(self.frame.rail_front_setback + self.frame.rail_length)
        for name, station in (
            ("light source post", self.light_source_post_station),
            ("cutoff post", self.cutoff_post_station),
            ("slit post", self.slit_post_station),
        ):
            if not rail_rear < station < -self.frame.rail_front_setback:
                raise ValueError(f"The {name} must stand on its rail")


def build_source_fixtures(h: OpticalHeadParameters, rotation: float = 0.0) -> Compound:
    """Light source and slit head in the source rail frame; rotation is the slit's, in degrees."""
    light_source = build_light_source_assembly(h.light_source, h.board)
    slit_head = build_slit_head_assembly(h.slit, rotation)
    return assembly(
        "Source rail fixtures",
        [
            place(Pos(0, h.light_source_origin_station, 0), light_source),
            place(Pos(0, h.slit_post_station, 0), slit_head),
        ],
    )


def build_imaging_fixtures(h: OpticalHeadParameters) -> Compound:
    """Lens cradle, phone, phone rest, and cutoff carriage in the imaging rail frame."""
    stand_alone = build_camera_support_assembly(h.camera, include_cutoff=True)
    children = []
    for group in stand_alone.children:
        if group.children:  # The lens cradle and phone rest group.
            kept = [child for child in group.children if child.label not in STAND_ALONE_LABELS]
            group = assembly(group.label, kept)
        children.append(group)
    return assembly(
        "Imaging rail fixtures", [place(Pos(0, h.phone_back_station, 0), group) for group in children]
    )


def build_optical_head(
    h: OpticalHeadParameters | None = None,
    left_yaw: float = 0.0,
    right_yaw: float = 0.0,
    slit_rotation: float = 0.0,
) -> Compound:
    """The frame with each rail's fixtures on it, rails yawed outward from nominal by the given degrees."""
    h = h or OpticalHeadParameters()
    h.validate()
    frame = build_frame_assembly(h.frame, left_yaw, right_yaw)
    yaw = {SOURCE_SIDE: left_yaw, IMAGING_SIDE: right_yaw}
    fixtures = [
        (build_source_fixtures(h, slit_rotation), SOURCE_SIDE),
        (build_imaging_fixtures(h), IMAGING_SIDE),
    ]
    children = list(frame.children)
    for group, side in fixtures:
        children.append(place(h.frame.rail_location(side, yaw[side] * pi / 180), group))
    return assembly("Tabletop optical head", children)

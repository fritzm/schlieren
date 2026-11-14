"""Field lens station (design §7.9): a lens ahead of the source slit, on a post of its own.

The cone from each slit point is centered on the chief ray from the center of the iris, about 150 mm behind
the slit (the condenser stack's, `LightSourceParameters.iris_to_slit`), so without a field lens the cones from
points along the slit land displaced on the mirror, by more than the mirror's 101.5 mm radius at the lit end
(§6.3). A positive lens just ahead of the slit images the iris onto the mirror instead, so every cone lands
centered on it. The lens is a Thorlabs LA1433-A (Ø1 in, N-BK7, plano-convex, f = 149.5 mm), and the slit is
placed at the iris-to-slit distance its focal length needs (`aimed_iris_to_slit`); on the mirror side of the
slit it leaves the condenser's conjugates, the lit length, and the focus target alone.

Parts:

- lens: LA1433-A, plano face toward the slit, seated on the internal lip of the tube;
- tube: SM1L10, thread end toward the slit, with the SM1RR retaining ring it ships with holding the lens from
  the mirror side. The tube's end stands just above the blades' folds, between the slit head's toe fingers,
  which stop short of its body (`slit_stage.toe_finger_face_z`); its internal lip sets the lens position and
  squares it;
- SM1RC/M split ring on the common post stack (TR50/M on its datum shim in the printed rail shoe, §5),
  clamping the tube's full-diameter section. The lens's alignment to the optical axis rests on the metal parts
  (post stack, ring, tube), not on a printed dimension, and the lens does not turn with the slit head.

Frame: the §3.4 source rail frame as the other source fixtures, but with y = 0 at the slit's blade-seat plane
(the slit head's local origin, `slit_stage.head_location`), +y toward the mirror: z = 0 at the rail top, the post
on x = 0. `build_field_lens_head_assembly` shows it with the slit head.

**Provisional:** the iris-to-slit distance the optics use (§6.3), the station along the rail (a setup value:
the tube slides in its ring), and the iris setting, all to be confirmed from a flat-field photograph.
"""

from dataclasses import dataclass, field
from math import atan, degrees, isfinite, radians, sqrt, tan

from build123d import Pos, Shape

from schlieren.cad import assembly, labeled, place
from schlieren.palette import BLACK_ANODIZED, GLASS
from schlieren.parts.light_source import LightSourceParameters
from schlieren.parts.rail_shoe import RailShoeParameters, post_stack
from schlieren.parts.slit_stage import SlitStageParameters, build_slit_stage_assembly, head_location
from schlieren.standards import POST_DIAMETER, SOURCE_SIDE
from schlieren.vendor_cad import (
    LA1433_A_CENTER_THICKNESS,
    LA1433_A_DIAMETER,
    LA1433_A_RADIUS,
    SM1L10_LENGTH,
    SM1L10_LIP_DIAMETER,
    SM1L10_OUTER_DIAMETER,
    SM1L10_THREAD_DEPTH,
    SM1L10_THREAD_LENGTH,
    SM1RC_M_THICKNESS,
    SM1RR_CLEAR_DIAMETER,
    SM1RR_THICKNESS,
    thorlabs_la1433_a,
    thorlabs_sm1l10,
)

FIELD_LENS_HARDWARE_LABEL = "Field lens post stack"

# Thorlabs LA1433-A, from the drawing (docs/reference/Thorlabs-LA1433-A.pdf).
LA1433_A_FOCAL_LENGTH = 149.5  # +-1 % at 587.6 nm.
LA1433_A_BACK_FOCAL_LENGTH = 147.5  # From the plano face, light entering the curved face.
LA1433_A_EDGE_THICKNESS = 2.0  # Reference value on the drawing.
SM1D12_MAX_DIAMETER = 12.0  # The iris's largest opening (catalog).


@dataclass(frozen=True)
class FieldLensParameters:
    stage: SlitStageParameters = field(default_factory=SlitStageParameters)
    # Lens (catalog and vendor model).
    lens_diameter: float = LA1433_A_DIAMETER
    lens_center_thickness: float = LA1433_A_CENTER_THICKNESS
    lens_radius: float = LA1433_A_RADIUS
    lens_focal_length: float = LA1433_A_FOCAL_LENGTH
    lens_back_focal_length: float = LA1433_A_BACK_FOCAL_LENGTH
    # What the lens works between (§6.3, §3.2): the iris behind the slit, the mirror ahead of it with the slit
    # at its center of curvature, and the mirror's half-aperture.
    iris_to_slit: float = field(default_factory=lambda: LightSourceParameters().iris_to_slit)
    slit_to_mirror: float = 3200.0
    mirror_half_aperture: float = 101.5
    # Tube and ring placement.
    fold_clearance: float = 0.5  # The tube's end above the top of the blades' folds.
    finger_wall_clearance: float = 0.5  # The toe fingers' faces beyond the tube's body, radially, at least.
    # The SM1RC/M's slit-side face past the tube's thread shoulder: far enough ahead that the post clears the
    # toe screw heads the slit head turns past it.
    ring_shoulder_margin: float = 7.75
    shoe_spacing_margin: float = 5.0  # Free rail between this shoe and the slit head's, at least.
    beam_margin: float = 0.5  # The beam's clearance from the lip bore and the retaining ring's aperture.

    # Lens.
    def lens_sag(self, r):
        """Depth of the convex face below its apex at radius r."""
        return self.lens_radius - sqrt(self.lens_radius**2 - r**2)

    def lens_height(self, r):
        """Height of the convex face above the plano face at radius r."""
        return self.lens_center_thickness - self.lens_sag(r)

    @property
    def lens_edge_thickness(self):
        return self.lens_height(self.lens_diameter / 2)

    @property
    def principal_planes(self):
        """(object side, image side) principal planes from the plano face, light entering the plano face: the
        first inside the lens by the catalog's f - back focal length, the second at the convex apex."""
        return self.lens_focal_length - self.lens_back_focal_length, self.lens_center_thickness

    # Tube, retaining ring, and post, as y ahead of the slit's blade-seat plane.
    @property
    def tube_end_y(self):
        """The tube's thread end, nearest the slit: just over the tops of the blades' folds, which turn with
        the head."""
        return self.stage.blade.fold_thickness + self.fold_clearance

    @property
    def tube_shoulder_y(self):
        return self.tube_end_y + SM1L10_THREAD_LENGTH

    @property
    def tube_open_end_y(self):
        return self.tube_end_y + SM1L10_LENGTH

    @property
    def lens_plano_y(self):
        """The lens's plano face rests on the tube's internal lip, SM1L10_THREAD_DEPTH from the open end."""
        return self.tube_open_end_y - SM1L10_THREAD_DEPTH

    @property
    def retaining_ring_y(self):
        """The SM1RR's slit-side face, bearing on the convex face at the ring's clear aperture."""
        return self.lens_plano_y + self.lens_height(SM1RR_CLEAR_DIAMETER / 2)

    @property
    def clamp_ring_y(self):
        """The SM1RC/M's slit-side face, on the tube's full-diameter section."""
        return self.tube_shoulder_y + self.ring_shoulder_margin

    @property
    def post_y(self):
        return self.clamp_ring_y + SM1RC_M_THICKNESS / 2

    @property
    def post_spacing(self):
        """Along the rail from the slit head's post to this one."""
        return head_location(self.stage).position.Y + self.post_y

    # Optics, paraxial, the lens as its principal planes.
    def mirror_position(self, height, slope):
        """Where a ray leaving the slit plane at this height and slope arrives at the mirror."""
        h_object, h_image = self.principal_planes
        at_lens = height + (self.lens_plano_y + h_object) * slope
        refracted = slope - at_lens / self.lens_focal_length
        return at_lens + (self.slit_to_mirror - self.lens_plano_y - h_image) * refracted

    def chief_ray_shift(self, h=None):
        """How far from the mirror's center the cone from slit point h (the lit end by default) is centered:
        its chief ray runs from the iris center. Without the lens it is h (1 + slit_to_mirror / iris_to_slit)."""
        h = self.stage.lit_half_length if h is None else h
        return self.mirror_position(h, h / self.iris_to_slit)

    @property
    def unlensed_shift(self):
        h = self.stage.lit_half_length
        return h * (1 + self.slit_to_mirror / self.iris_to_slit)

    @property
    def cone_scale(self):
        """Each slit point's footprint on the mirror, relative to the footprint without the lens: the lens
        converges the cone a little."""
        slope = tan(radians(self.stage.cone_half_angle))
        return self.mirror_position(0.0, slope) / (self.slit_to_mirror * slope)

    @property
    def fill_cone_half_angle(self):
        """Source cone half-angle, in degrees at the slit, whose footprint reaches the mirror's edge from the lit
        end of the slit."""
        reach = self.mirror_half_aperture + abs(self.chief_ray_shift())
        return degrees(atan(reach / (self.slit_to_mirror * self.cone_scale)))

    @property
    def fill_iris_diameter(self):
        """The iris setting for that cone."""
        return 2 * self.iris_to_slit * tan(radians(self.fill_cone_half_angle))

    @property
    def aimed_iris_to_slit(self):
        """The iris-to-slit distance at which this lens, at its position, images the iris onto the mirror, so
        every slit point's cone centers there; the condenser's `lens_to_slit` is set to it (§6.3)."""
        h_object, h_image = self.principal_planes
        v = self.slit_to_mirror - self.lens_plano_y - h_image
        return 1 / (1 / self.lens_focal_length - 1 / v) - self.lens_plano_y - h_object

    @property
    def ideal_focal_length(self):
        """The focal length that images the iris onto the mirror from the lens's position."""
        h_object, h_image = self.principal_planes
        u = self.iris_to_slit + self.lens_plano_y + h_object
        v = self.slit_to_mirror - self.lens_plano_y - h_image
        return 1 / (1 / u + 1 / v)

    def beam_half_length(self, y):
        """Half-extent along the slit of the beam at y ahead of the slit: the lit length, the cone about each
        point's chief ray, and the chief rays' tilt (a superset: the lens only narrows the cones)."""
        s = self.stage
        slope = tan(radians(s.cone_half_angle))
        return s.lit_half_length + y * (slope + s.lit_half_length / self.iris_to_slit)

    def validate(self):
        for name, value in vars(self).items():
            if isinstance(value, float) and not isfinite(value):
                raise ValueError(f"{name} must be finite")
        s = self.stage
        s.validate()
        if abs(self.lens_edge_thickness - LA1433_A_EDGE_THICKNESS) > 0.1:
            raise ValueError("Lens radius and center thickness must give the catalog edge thickness")
        if self.fold_clearance <= 0:
            raise ValueError("The tube's end must clear the blades' folds")
        if s.toe_finger_face_z - SM1L10_OUTER_DIAMETER / 2 < self.finger_wall_clearance:
            raise ValueError("The toe fingers must clear the tube's body all round")
        if self.ring_shoulder_margin < 0:
            raise ValueError("The clamp ring must sit on the tube's full-diameter section")
        if self.clamp_ring_y + SM1RC_M_THICKNESS > self.tube_open_end_y:
            raise ValueError("The clamp ring must sit wholly on the tube")
        if self.clamp_ring_y < s.toe_thickness + s.screw_head_height + s.post_clearance:
            raise ValueError("The clamp ring must clear the toe screw heads the slit head turns")
        if self.post_y - POST_DIAMETER / 2 < s.toe_thickness + s.screw_head_height + s.post_clearance:
            raise ValueError("The post must clear the toe screw heads the slit head turns past it")
        if self.post_spacing < RailShoeParameters().length + self.shoe_spacing_margin:
            raise ValueError("The two rail shoes must not crowd each other")
        if self.retaining_ring_y + SM1RR_THICKNESS > self.tube_open_end_y:
            raise ValueError("The retaining ring must sit inside the tube's thread")
        for y, aperture, name in (
            (self.lens_plano_y, SM1L10_LIP_DIAMETER, "the tube's lip bore"),
            (self.retaining_ring_y + SM1RR_THICKNESS, SM1RR_CLEAR_DIAMETER, "the retaining ring"),
        ):
            if aperture / 2 < self.beam_half_length(y) + self.beam_margin:
                raise ValueError(f"The beam must pass {name}")


def build_field_lens_station(p=None, side_screws=False):
    """The lens, tube, retaining ring, and post stack in the frame described above."""
    p = p or FieldLensParameters()
    p.validate()
    s = p.stage
    axis = Pos(0, 0, s.optical_height)
    tube, ring = thorlabs_sm1l10()
    children: list[Shape] = [
        labeled(thorlabs_la1433_a(), "Field lens LA1433-A", GLASS, axis * Pos(0, p.lens_plano_y, 0)),
        labeled(tube, "Field lens tube SM1L10", BLACK_ANODIZED, axis * Pos(0, p.tube_shoulder_y, 0)),
        # The ring ships flush at the open end; it is shown where it holds the lens.
        labeled(
            ring,
            "Field lens retaining ring SM1RR",
            BLACK_ANODIZED,
            axis * Pos(0, p.retaining_ring_y - (p.tube_open_end_y - p.tube_shoulder_y - SM1RR_THICKNESS), 0),
        ),
    ]
    stack = post_stack(
        y=p.post_y,
        ring=True,
        optical_height=s.optical_height,
        datum_thickness=s.datum_thickness,
        side_screws=side_screws,
        side=SOURCE_SIDE,
    )
    children.append(assembly(FIELD_LENS_HARDWARE_LABEL, stack))
    return assembly("Field lens station", children)


def build_field_lens_head_assembly(p=None, rotation=0.0, side_screws=False):
    """The slit head and baffle with the field lens station on the source rail, slit post at y = 0."""
    p = p or FieldLensParameters()
    p.validate()
    head = build_slit_stage_assembly(p.stage, rotation, side_screws=side_screws)
    station = place(Pos(0, head_location(p.stage).position.Y, 0), build_field_lens_station(p, side_screws))
    return assembly("Slit head with field lens (experiment)", [*head.children, station])

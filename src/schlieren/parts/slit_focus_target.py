"""Slit focus target: stands in for the stage-mounted slit head (slit_stage.py) while the condenser is focused.

The emitter image is focused on the slit plane, but the blades sit deep in the stage and cannot be seen. This
fixture swaps in for the stage plate on the same SM1RC/M ring: the same shoulder, ring gap, and spigot grip,
then a hollow barrel that widens to a rim whose face is the plane of the blades' cutting edges. The bore tapers
in at 45 degrees to a seat bore at the rim face. A Ø1 in ground-glass disc (Thorlabs DG10-600: 2.0 mm thick and
Ø25.4 mm by its drawing, which gives no tolerances, with a 0.2 mm edge bevel from the vendor model) lies on the
rim, ground face toward the source, in a pocket in the rear face of a printed retaining ring that screws down
into heat-set inserts. The LED image forms on the ground face and is read through the glass from the mirror
side.

A neoprene gasket between the glass's front face and the pocket ceiling pushes the glass back onto the rim and
absorbs the thickness spread, so the imaging surface is the y = 0 rim face, the plane of the blades' cutting
edges, whatever the glass thickness. The glass is loaded from the front: set it on the rim, then the gasket,
then the ring over both. Its Ø25.0 mm flat seats on 2.5 mm of the rim.

Assembly frame is the stage head's (slit_stage.py): y toward the mirror, the origin on the optical axis in the
blade-seat plane. The blades lie on their folds, so their cutting edges' mid-plane is `rim_y` ahead of that plane;
the fixture is built with its rim face at y = 0 and placed there.
"""

from dataclasses import dataclass, field
from functools import cache
from math import cos, isfinite, radians, sin

from build123d import GeomType, Pos, Rot, Shape

from schlieren.cad import CUT_OVERRUN, assembly, labeled, y_cone, y_cylinder
from schlieren.palette import BUSHING_BRASS, GLASS, METAL, PRINTED_BLUE, PRINTED_GREEN, RUBBER
from schlieren.parts.rail_shoe import REFERENCE_HARDWARE_LABEL, post_stack
from schlieren.parts.slit_stage import SlitStageParameters, head_location
from schlieren.vendor_cad import (
    MCMASTER_91292A113_LENGTH,
    THORLABS_DG10_BEVEL,
    mcmaster_91292a113,
    mcmaster_97171a310,
    thorlabs_dg10,
)


def break_outer_edge(shape, y, diameter, size):
    """Chamfer the circular edge of the given diameter in the plane y, on the optical axis, by size."""
    edges = [
        e
        for e in shape.edges()
        if e.geom_type == GeomType.CIRCLE
        and abs(e.center().Y - y) < 1e-6
        and abs(e.radius - diameter / 2) < 1e-6
    ]
    if len(edges) != 1:
        raise ValueError(f"Expected one circular edge of Ø{diameter} at y = {y}, found {len(edges)}")
    return shape.chamfer(size, None, edges)


@dataclass(frozen=True)
class FocusTargetParameters:
    stage: SlitStageParameters = field(default_factory=SlitStageParameters)
    rim_diameter: float = 40.0  # Rim and retaining ring; wide enough for the insert recesses.
    rim_length: float = 8.0  # Rim face back to where the barrel narrows to the shoulder diameter.
    # The bore tapers in at 45 degrees to this diameter at the rim face, so the glass has a wide seat on the rim
    # and the insert recesses a thicker wall. The beam there is about the lit slit length across.
    seat_bore_diameter: float = 20.0
    screw_count: int = 4
    screw_length: float = (
        MCMASTER_91292A113_LENGTH  # M3 x 10 (91292A113); the stage's toe screws are M3 x 12.
    )
    screw_circle_diameter: float = 32.0
    # Hand comfort: a slight chamfer on the outer circumference of the rim's back face and of the ring's front
    # face. The faces that mate (the rim's front and the ring's rear) stay sharp.
    edge_chamfer: float = 0.5
    screw_start_angle: float = 45.0  # Degrees from the slit direction.
    insert_engagement_margin: float = 0.5
    # Thorlabs DG10-600 drawing (docs/reference): the nominal diameter and thickness. It gives no tolerance, so
    # `glass_thickness_tolerance` is the pocket's allowance, which the gasket makes uncritical.
    glass_diameter: float = 25.4
    glass_thickness_nominal: float = 2.0
    glass_thickness_tolerance: float = 0.2
    glass_bevel: float = THORLABS_DG10_BEVEL  # 45 degrees on both edges, from the vendor model.
    # Printed holes come out small; this clearance fits the glass (checked on the bench).
    pocket_diametral_clearance: float = 0.3
    gasket_thickness: float = (
        1.59  # 1/16 in neoprene sheet, free; absorbs the glass's 0.4 mm thickness spread.
    )
    gasket_min_gap: float = 0.95  # Pocket ceiling to the thickest glass: the gasket's working space.
    lip_thickness: float = 1.5  # Ring thickness in front of the pocket, around the window.
    # 45 degree bevel on the window's mirror-side edge, widening the view of the glass from off axis.
    window_chamfer: float = 1.0
    land_min: float = 0.5  # Window cylinder left under the bevel.
    wall_min: float = 1.0  # Ring wall between the pocket and the screw holes.
    seating_min: float = 2.0  # Glass flat on the rim face, radially.

    @property
    def bore(self):
        return self.stage.spigot_bore

    @property
    def window_diameter(self):
        """The ring's window matches the seat bore, so the ring clamps the full width of the rim's annulus."""
        return self.seat_bore_diameter

    @property
    def seat_taper_length(self):
        """Axial length of the 45 degree taper from the bore to the seat bore."""
        return (self.bore - self.seat_bore_diameter) / 2

    @property
    def barrel_diameter(self):
        """Barrel behind the rim: the spigot shoulder's diameter, which leaves a wall around the bore."""
        return self.stage.spigot_shoulder_diameter

    @property
    def rim_y(self):
        """The rim face's height above the blade-seat plane: the mid-plane of the blades' cutting edges, where
        the emitter image is to be focused."""
        return self.stage.seated_blade_y(0, 0)

    @property
    def plate_back(self):
        """The stage plate's rear, where the shoulder seats on the ring, in this frame (rim face at y = 0)."""
        return self.stage.plate_back - self.rim_y

    @property
    def barrel_length(self):
        """Shoulder face to the rim: the stage plate's rear to the blades' edge plane."""
        return -self.plate_back

    @property
    def screw_radius(self):
        return self.screw_circle_diameter / 2

    def screw_xz(self):
        return [
            (
                self.screw_radius * cos(radians(self.screw_start_angle + i * 360 / self.screw_count)),
                self.screw_radius * sin(radians(self.screw_start_angle + i * 360 / self.screw_count)),
            )
            for i in range(self.screw_count)
        ]

    @property
    def glass_thickness_max(self):
        return self.glass_thickness_nominal + self.glass_thickness_tolerance

    @property
    def glass_thickness_min(self):
        return self.glass_thickness_nominal - self.glass_thickness_tolerance

    @property
    def glass_flat_diameter(self):
        """Each face's flat, inside the bevel."""
        return self.glass_diameter - 2 * self.glass_bevel

    @property
    def rim_seating_width(self):
        """Radial width of the glass's flat on the rim face, outside the seat bore."""
        return (self.glass_flat_diameter - self.seat_bore_diameter) / 2

    @property
    def pocket_diameter(self):
        return self.glass_diameter + self.pocket_diametral_clearance

    @property
    def pocket_depth(self):
        """Ring rear face (the rim face) to the pocket ceiling under the lip."""
        return self.glass_thickness_max + self.gasket_min_gap

    @property
    def ring_thickness(self):
        return self.pocket_depth + self.lip_thickness

    @property
    def screw_engagement(self):
        """Screw tip depth below the rim face, with the ring seated on the rim."""
        return self.screw_length - self.ring_thickness

    def gasket_compression(self, glass_thickness):
        """Fraction of the free gasket thickness squeezed with a glass of this thickness."""
        return 1 - (self.pocket_depth - glass_thickness) / self.gasket_thickness

    def validate(self):
        for name, value in vars(self).items():
            if isinstance(value, float) and not isfinite(value):
                raise ValueError(f"{name} must be finite")
        s = self.stage
        s.validate()
        recess = s.insert_flange_recess_diameter
        if self.screw_circle_diameter / 2 - recess / 2 < self.bore / 2 + 1.0:
            raise ValueError("Insert flange recesses must leave a wall inside the bore")
        if self.screw_circle_diameter / 2 + recess / 2 > self.rim_diameter / 2 - 1.0:
            raise ValueError("Insert flange recesses must leave a wall inside the barrel")
        if self.window_diameter > s.spigot_bore or self.window_diameter < 2 * s.lit_half_length:
            raise ValueError("Ring window must pass the beam and not exceed the spigot's bore")
        if self.window_diameter >= self.bore:
            raise ValueError("Ring must overlap the rim to grip the glass")
        head_edge = self.screw_radius - s.screw_head_diameter / 2
        if self.window_diameter / 2 + self.window_chamfer > head_edge - 0.5:
            raise ValueError("Window chamfer must leave the screw heads a bearing face")
        if self.lip_thickness - self.window_chamfer < self.land_min:
            raise ValueError("Window bevel must leave a land under it")
        if not 2 * s.lit_half_length + 4.0 <= self.seat_bore_diameter <= self.bore:
            raise ValueError("Seat bore must pass the beam with margin and not exceed the bore")
        if self.seat_taper_length > self.rim_length:
            raise ValueError("Seat taper must stay within the rim")
        if not 0 <= self.edge_chamfer < min(self.rim_length, self.ring_thickness):
            raise ValueError("Edge chamfer must fit the rim and the ring")
        if self.rim_diameter / 2 - self.edge_chamfer < self.screw_radius + s.screw_head_diameter / 2 + 0.25:
            raise ValueError("Edge chamfer must leave the screw heads a bearing face")
        if self.rim_diameter < self.barrel_diameter:
            raise ValueError("Rim must be at least as wide as the barrel")
        floor = 1.0  # Solid under the insert holes.
        if self.rim_length < s.insert_flange_recess_depth + s.insert_hole_depth + floor:
            raise ValueError("Rim must be deep enough to hold the heat-set inserts")
        if (
            self.screw_engagement > s.insert_hole_depth
            or self.screw_engagement < s.insert_installed_length - self.insert_engagement_margin
        ):
            raise ValueError("Ring screws must run through the inserts without bottoming")
        if self.pocket_diametral_clearance <= 0:
            raise ValueError("Pocket needs clearance around the disc")
        if self.window_diameter >= self.glass_diameter - 2.0:
            raise ValueError("Ring lip must overlap the glass edge")
        if self.rim_seating_width < self.seating_min:
            raise ValueError("The glass's flat must seat on the rim outside the seat bore")
        if self.pocket_diameter / 2 > self.screw_radius - s.screw_clearance / 2 - self.wall_min:
            raise ValueError("Pocket must leave a wall to the screw holes")
        if not 0.05 <= self.gasket_compression(self.glass_thickness_min) <= 0.45:
            raise ValueError("Gasket must stay lightly loaded with the thinnest glass")
        if self.gasket_compression(self.glass_thickness_max) > 0.45:
            raise ValueError("Gasket over-compressed with the thickest glass")


@cache
def build_focus_target(p=None):
    """Spigot, shoulder, and barrel with four heat-set insert holes in the rim face (y = 0). The bore tapers in
    to the seat bore at the rim face.

    Print rim face down, spigot up, without supports."""
    p = p or FocusTargetParameters()
    p.validate()
    s = p.stage
    shoulder_back = p.plate_back - s.ring_gap
    body = y_cylinder(p.barrel_diameter, 0, 0, p.plate_back, -p.rim_length + CUT_OVERRUN)
    body += y_cylinder(p.rim_diameter, 0, 0, -p.rim_length, 0)
    body += y_cylinder(s.spigot_shoulder_diameter, 0, 0, shoulder_back, p.plate_back + 0.5)
    body += y_cylinder(s.spigot_diameter, 0, 0, p.plate_back - s.spigot_length, shoulder_back + 0.5)
    taper = p.seat_taper_length
    body -= y_cylinder(p.bore, 0, 0, p.plate_back - s.spigot_length - CUT_OVERRUN, -taper + CUT_OVERRUN)
    body -= y_cone(p.bore, p.seat_bore_diameter, 0, 0, -taper, 0)
    body -= y_cylinder(p.seat_bore_diameter, 0, 0, -taper, CUT_OVERRUN)
    for x, z in p.screw_xz():
        body -= y_cylinder(
            s.insert_hole_diameter,
            x,
            z,
            -s.insert_flange_recess_depth - s.insert_hole_depth,
            CUT_OVERRUN,
        )
        body -= y_cylinder(s.insert_flange_recess_diameter, x, z, -s.insert_flange_recess_depth, CUT_OVERRUN)
    if p.edge_chamfer > 0:
        body = break_outer_edge(body, -p.rim_length, p.rim_diameter, p.edge_chamfer)
    return body


@cache
def build_retaining_ring(p=None):
    """Ring that clamps the glass and gasket to the rim, with the glass pocket opening in its rear face (the
    y = 0 plane, on the rim). The window is beveled on the front (mirror-side) face, and the outer front edge
    has a slight chamfer.

    Print front face down, pocket up, without supports."""
    p = p or FocusTargetParameters()
    p.validate()
    ring = y_cylinder(p.rim_diameter, 0, 0, 0, p.ring_thickness)
    ring -= y_cylinder(p.window_diameter, 0, 0, -CUT_OVERRUN, p.ring_thickness + CUT_OVERRUN)
    c = p.window_chamfer
    ring -= y_cone(
        p.window_diameter,
        p.window_diameter + 2 * (c + CUT_OVERRUN),
        0,
        0,
        p.ring_thickness - c,
        p.ring_thickness + CUT_OVERRUN,
    )
    for x, z in p.screw_xz():
        ring -= y_cylinder(p.stage.screw_clearance, x, z, -CUT_OVERRUN, p.ring_thickness + CUT_OVERRUN)
    ring -= y_cylinder(p.pocket_diameter, 0, 0, -CUT_OVERRUN, p.pocket_depth)
    if p.edge_chamfer > 0:
        ring = break_outer_edge(ring, p.ring_thickness, p.rim_diameter, p.edge_chamfer)
    return ring


def build_glass(p=None, thickness=None):
    """Ground-glass disc, ground face on the y = 0 plane (on the rim), extending toward the mirror.

    Without a thickness, the Thorlabs vendor model (nominal 2.0 mm, 0.2 mm edge bevels); with one, a disc of
    that thickness with the same bevels, for the catalog thickness spread."""
    p = p or FocusTargetParameters()
    if thickness is None:
        return thorlabs_dg10()
    disc = y_cylinder(p.glass_diameter, 0, 0, 0, thickness)
    edges = [e for e in disc.edges() if e.geom_type == GeomType.CIRCLE]
    return disc.chamfer(p.glass_bevel, None, edges)


def build_gasket(p=None):
    """Annular gasket on the glass's front face (its flat, inside the bevel), compressed against the pocket
    ceiling."""
    p = p or FocusTargetParameters()
    glass_front = p.glass_thickness_nominal
    gasket = y_cylinder(p.glass_flat_diameter, 0, 0, glass_front, p.pocket_depth)
    return gasket - y_cylinder(
        p.window_diameter, 0, 0, glass_front - CUT_OVERRUN, p.pocket_depth + CUT_OVERRUN
    )


def build_focus_target_assembly(p=None, include_support=True):
    """Fixture, glass, gasket, retaining ring, screws, inserts, and the slit post stack."""
    p = p or FocusTargetParameters()
    p.validate()
    s = p.stage
    loc = head_location(s) * Pos(0, p.rim_y, 0)  # The rim face is at the blades' edge plane.
    children: list[Shape] = [
        labeled(build_focus_target(p), "Focus target", PRINTED_BLUE, loc),
        labeled(build_retaining_ring(p), "Retaining ring", PRINTED_GREEN, loc),
        labeled(build_glass(p), "Ground glass", GLASS, loc),
        labeled(build_gasket(p), "Gasket", RUBBER, loc),
    ]
    for i, (x, z) in enumerate(p.screw_xz(), 1):
        screw = loc * Pos(x, p.ring_thickness, z) * Rot(X=90)
        children.append(labeled(mcmaster_91292a113(), f"Ring screw {i}", METAL, screw))
        insert = loc * Pos(x, -s.insert_flange_recess_depth, z) * Rot(X=-90)
        children.append(labeled(mcmaster_97171a310(), f"Ring insert {i}", BUSHING_BRASS, insert))
    if include_support:
        reference = post_stack(ring=True, optical_height=s.optical_height, datum_thickness=s.datum_thickness)
        children.append(assembly(REFERENCE_HARDWARE_LABEL, reference))
    return assembly("Slit focus target", children)

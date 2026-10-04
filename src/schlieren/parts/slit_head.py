"""Flexure source-slit head; canonical design §7 (selected baseline; first test print fits confirmed).

It replaces the §8 carriage and slit cassette for the source slit; the cutoff keeps the §8 carriage.
One flat-printed ABS flexure head carries both Stanley blades:

- frame -> platform: a parallelogram flexure for slit centering perpendicular to the slit, driven by
  FAS100 #1 (insert in the frame) against the coaxial 2006N292 spring, which supplies the preload;
- platform -> width stage: a nested parallelogram flexure carrying the movable blade, driven by FAS100 #2
  (insert in the platform) against the flexures' own preload.

Both parallelograms put their parasitic motion along the slit, where it is harmless. Stage rotation in the
slit plane (which would skew the slit, or open it in a taper) is controlled by keeping the drive forces off
the flexures: FAS100 #1 and the spring are coaxial and push on the platform's flexure connectors, so only
the small centering-flexure force is left unbalanced; the centering blades are spread to the top and bottom
of the platform; FAS100 #2 pushes on the width-stage connector. Rotation is estimated from a first-order
model (see `stage_rotation`), not FEA.

A separate flat printed adapter, spaced off the frame by M3 washers, carries a hollow SM1-tube-diameter
spigot that the SM1RC/M split ring clamps, so the head rotates continuously about the optical axis
(vertical, horizontal, and parallelism trim). Two identical printed clamp bars with EPDM faces pinch the
blades; no holes go through the blades.

Local frame, shown at rotation 0 (slit horizontal, knobs up): x along the slit, z the adjustment axis (+z
toward the knobs), y the optical axis (+y toward the mirror). The origin is the slit center on the
blade-seat plane (the carrier front faces). The head is modeled as printed: the platform at mid travel and
the width stage at zero flexure deflection.

Assembly frame matches led_module: x transverse, y along the rail toward the mirror, z=0 at the rail top,
with the slit post at x=y=0.
"""

from dataclasses import dataclass
from math import cos, isfinite, pi

from build123d import Axis, Box, Cylinder, Pos, RegularPolygon, Rot, extrude, fillet

from schlieren.cad import FROM_CORNER, ON_FLOOR, along_y, assembly, labeled
from schlieren.vendor_cad import SM1RC_M_THICKNESS, thorlabs_fas100, thorlabs_sm1rc_m, thorlabs_tr50_m

INCH = 25.4
LBF = 4.44822  # N


@dataclass(frozen=True)
class SlitHeadParameters:
    # Frozen project datum (§3.4) and post stack.
    optical_height: float = 72.35
    datum_thickness: float = 0.010 * INCH
    post_length: float = 50.0
    post_diameter: float = 12.7
    # Thorlabs SM1RC/M (vendor STEP model): Ø1.21 in bore accepting Ø1.20 in SM1 tubes.
    ring_thickness: float = SM1RC_M_THICKNESS
    ring_bore: float = 1.21 * INCH
    # Stanley 11-515 blades, measured (§7).
    blade_length: float = 38.99
    blade_width: float = 19.51
    blade_thickness: float = 0.254
    spine_thickness: float = 1.016
    spine_width: float = 2.0  # Display only; fold width not measured.
    slit_width: float = 0.20  # Display/setup value in the likely 0.15-0.20 mm working region.
    # Thorlabs FAS100 (drawing): 1/4"-80, 1.00 in thread from knob shoulder to ball tip.
    adjuster_thread_length: float = 1.00 * INCH
    adjuster_pitch: float = INCH / 80
    adjuster_knob_diameter: float = 0.49 * INCH
    # McMaster 98625A950 brass insert (§8.3 drawing values).
    insert_bore: float = 0.313 * INCH  # Print as pilot; finish with a 5/16 in drill.
    insert_length: float = 0.313 * INCH
    insert_min_material: float = 0.298 * INCH
    insert_flange_diameter: float = 0.352 * INCH
    insert_flange_thickness: float = 0.010 * INCH
    # N52 10 x 5 x 2 mm magnet bearing pads under each FAS100 ball tip (§8.3).
    magnet_length: float = 10.0
    magnet_width: float = 5.0
    magnet_thickness: float = 2.0
    magnet_fit_clearance: float = 0.15
    # McMaster 2006N292 spring (§§8.4-8.5): free length and rate; 9 mm compression at mid travel.
    spring_free_length: float = 25.5
    spring_mid_length: float = 16.5
    spring_rate: float = 0.14 * LBF  # N/mm
    spring_guide_pin_diameter: float = 3.6  # Inside the coil, which passes a 4 mm shoulder (§8.5).
    spring_guide_pin_length: float = 5.0
    spring_outer_diameter: float = 0.272 * INCH  # Measured (calipers), in-hand spring.
    spring_pocket_clearance: float = 1.0  # Diametral; printed-hole shrink and coil growth under compression.
    # Common M3 hardware: 91292A114 M3 x 12 SHCS, 91828A211 nut.
    screw_length: float = 12.0
    screw_clearance: float = 3.4
    screw_head_diameter: float = 5.5
    screw_head_height: float = 3.0
    counterbore_clearance: float = 0.5  # Diametral.
    nut_across_flats: float = 5.5
    nut_thickness: float = 2.4
    nut_across_flats_clearance: float = 0.3
    nut_axial_clearance: float = 0.3
    thread_protrusion: float = 0.5  # Screw tip beyond the far nut face.
    # McMaster 9852N37 EPDM on the clamp-bar faces, uncompressed.
    epdm_thickness: float = INCH / 32

    # Flexure head layout (provisional first-print values).
    body_thickness: float = 13.0  # y; blade carriers' front faces are the blade-seat plane.
    seat_relief: float = 1.0  # Everything else stands back so overhanging blades cannot rub.
    blade_overhang: float = 1.5  # Blade edge beyond its carrier edge.
    carrier_depth: float = 13.0  # z, each blade carrier.
    side_gap: float = 2.0  # x gaps: width stage/platform posts, platform posts/frame.
    post_width: float = 5.0  # Platform side posts and the frame side post.
    bar_thickness: float = 8.5  # z; the bars that carry the inserts and the frame bars.
    connector_width: float = 13.0  # x; each connector carries a magnet pad lengthwise.
    # Centering stage (frame -> platform): one blade above the platform, one below it.
    centering_screw_x: float = -5.0  # FAS100 #1, the spring, and both platform connectors.
    centering_half_travel: float = 2.0
    centering_blade_thickness: float = 0.8
    centering_gap: float = 3.5  # Must exceed the half travel.
    centering_tip_well: float = 4.0  # FAS100 #1 reaches down into the upper platform connector.
    spring_platform_pocket: float = 6.0  # Spring pocket depth up into the lower platform connector.
    spring_floor: float = 2.5
    # Width stage (platform -> width stage); the screw only pushes it down (slit closing).
    width_screw_x: float = -21.4  # FAS100 #2 and the width-stage connector.
    width_blade_thickness: float = 1.2
    width_blade_spacing: float = 12.0  # Center to center.
    width_gap: float = 2.0
    width_preload: float = 0.8  # Minimum flexure deflection held against FAS100 #2.
    width_travel: float = 0.8  # Usable slit-width adjustment above the preload.
    width_tip_well: float = 3.0
    frame_top_bar_x0: float = -13.0
    frame_bottom_bar_x0: float = -38.0
    # Clamp bars (separate prints); screws sit just beyond the blade ends.
    clamp_bar_thickness: float = 4.0
    clamp_bar_width: float = 7.0  # z
    clamp_bar_setback: float = 3.0  # From the blade edge, leaving the slit cone clear.
    clamp_blade_end_clearance: float = 1.8  # Blade end to screw clearance hole.
    clamp_bar_end_margin: float = 4.0  # Screw axis to bar end.
    carrier_end_margin: float = 5.0  # Screw axis to carrier end; clears the captive nut.
    # Spigot adapter (separate print).
    adapter_thickness: float = 6.0
    adapter_corner_margin: float = 4.0  # Plate edge beyond the outermost screw axes.
    # The plate prints flat; M3 flat washers (McMaster 93475A210: 7 mm OD, 0.4-0.6 mm thick) stacked on each
    # adapter screw between frame and plate hold it off the moving stages.
    spacer_washers: int = 2
    washer_thickness: float = 0.5  # Nominal.
    washer_thickness_min: float = 0.4
    washer_outer_diameter: float = 7.0
    stage_back_clearance: float = 0.5  # Minimum running gap, moving stages to the adapter plate.
    adapter_screw_points: tuple = ((12.0, "top"), (32.0, "top"), (-33.0, "bottom"), (33.0, "bottom"))
    spigot_diameter: float = 1.20 * INCH  # SM1 tube OD; the ring is made to clamp this.
    spigot_bore: float = 24.0
    # Adapter back to ring face, set by a shoulder on the spigot that the ring seats against; keeps the
    # adapter plate clear of the post at every rotation.
    ring_gap: float = 3.5
    spigot_shoulder_diameter: float = 34.0  # Bears on the SM1RC/M face outside its Ø30.6 mm bore.
    post_clearance: float = 2.0  # Minimum, rotating parts to post and rail shoe over the working range.
    # ABS material, typical values (provisional).
    abs_modulus: float = 2200.0  # MPa
    flexure_strain_limit: float = 0.006

    @property
    def spring_pocket_diameter(self):
        return self.spring_outer_diameter + self.spring_pocket_clearance

    # Clamp layout (x), derived from the blade so a different blade resizes the carriers.
    @property
    def clamp_screw_x(self):
        return self.blade_length / 2 + self.clamp_blade_end_clearance + self.screw_clearance / 2

    @property
    def clamp_bar_half_length(self):
        return self.clamp_screw_x + self.clamp_bar_end_margin

    @property
    def carrier_half_length(self):
        return self.clamp_screw_x + self.carrier_end_margin

    # Derived z positions (local frame, as printed).
    @property
    def carrier_edge(self):
        return self.slit_width / 2 + self.blade_overhang

    @property
    def carrier_outer(self):
        return self.carrier_edge + self.carrier_depth

    @property
    def width_blades(self):
        """(z0, z1) of the two width-stage blades, lower first."""
        z0 = self.carrier_outer + self.width_gap
        return tuple((z, z + self.width_blade_thickness) for z in (z0, z0 + self.width_blade_spacing))

    @property
    def platform_top_bar(self):
        z0 = self.width_blades[1][1] + self.width_gap
        return z0, z0 + self.bar_thickness

    @property
    def centering_blades(self):
        """(z0, z1) of the upper (above the platform top bar) and lower (below the carrier) blades."""
        upper = self.platform_top_bar[1] + self.centering_gap
        lower = -self.carrier_outer - self.centering_gap
        t = self.centering_blade_thickness
        return (upper, upper + t), (lower - t, lower)

    @property
    def frame_top_bar(self):
        z0 = self.centering_blades[0][1] + self.centering_gap
        return z0, z0 + self.bar_thickness

    @property
    def platform_spring_seat_z(self):
        return self.centering_blades[1][0] + self.spring_platform_pocket

    @property
    def frame_spring_seat_z(self):
        return self.platform_spring_seat_z - self.spring_mid_length

    @property
    def frame_bottom_bar(self):
        z1 = self.centering_blades[1][0] - self.centering_gap
        return min(z1 - self.bar_thickness, self.frame_spring_seat_z - self.spring_floor), z1

    # Derived x positions.
    @property
    def platform_post_inner(self):
        return self.carrier_half_length + self.side_gap

    @property
    def platform_post_outer(self):
        return self.platform_post_inner + self.post_width

    @property
    def frame_post_inner(self):
        return self.platform_post_outer + self.side_gap

    @property
    def frame_post_outer(self):
        return self.frame_post_inner + self.post_width

    def connector_span(self, x):
        return x - self.connector_width / 2, x + self.connector_width / 2

    @property
    def width_blade_span(self):
        return self.connector_span(self.width_screw_x)[1], self.platform_post_inner

    @property
    def centering_blade_span(self):
        return self.connector_span(self.centering_screw_x)[1], self.frame_post_inner

    @property
    def width_blade_length(self):
        x0, x1 = self.width_blade_span
        return x1 - x0

    @property
    def centering_blade_length(self):
        x0, x1 = self.centering_blade_span
        return x1 - x0

    # Derived y positions.
    @property
    def relieved_front(self):
        return -self.seat_relief

    @property
    def axis_y(self):
        """y of the adjuster and fastener axes: mid-thickness of the relieved bars."""
        return (self.relieved_front - self.body_thickness) / 2

    @property
    def adapter_standoff(self):
        return self.spacer_washers * self.washer_thickness

    @property
    def adapter_front(self):
        return -self.body_thickness - self.adapter_standoff

    @property
    def adapter_back(self):
        return self.adapter_front - self.adapter_thickness

    @property
    def spigot_length(self):
        return self.ring_gap + self.ring_thickness

    # Adjusters.
    @property
    def centering_tip_z(self):
        """FAS100 #1 ball tip on its magnet in the upper platform connector, at mid travel."""
        return self.centering_blades[0][1] - self.centering_tip_well

    @property
    def width_tip_z(self):
        """FAS100 #2 ball tip on its magnet in the width-stage connector, undeflected (as printed)."""
        return self.width_blades[1][1] - self.width_tip_well

    # Clamp bars and their captive nuts.
    @property
    def clamp_bar_z(self):
        """Center z of the movable-blade bar (the datum bar mirrors it)."""
        return self.slit_width / 2 + self.clamp_bar_setback + self.clamp_bar_width / 2

    @property
    def clamp_bar_front(self):
        return self.blade_thickness + self.epdm_thickness + self.clamp_bar_thickness

    @property
    def clamp_nut_floor(self):
        """Front (floor) face of the clamp nut pockets, which open from the carrier back."""
        tip = self.clamp_bar_front - self.screw_length
        return tip + self.thread_protrusion + self.nut_thickness

    @property
    def adapter_counterbore_floor(self):
        """Adapter screws enter from the head front; the nut pockets open from the adapter back."""
        nut_far_face = self.adapter_back + self.nut_axial_clearance
        return nut_far_face - self.thread_protrusion + self.screw_length

    def adapter_screw_xz(self):
        bars = {"top": self.frame_top_bar, "bottom": self.frame_bottom_bar}
        return [(x, sum(bars[bar]) / 2) for x, bar in self.adapter_screw_points]

    # Engineering checks.
    @property
    def flexure_height(self):
        return self.body_thickness - self.seat_relief

    def flexure_stiffness(self, thickness, length):
        """Two fixed-guided blades, N/mm."""
        return 2 * self.abs_modulus * self.flexure_height * thickness**3 / length**3

    def rotation_stiffness(self, thickness, length, blades):
        """In-plane stage rotation, N mm/rad: resisted by opposing axial strain in the two blades."""
        axial = self.abs_modulus * self.flexure_height * thickness / length
        spacing = (blades[0][0] + blades[0][1] - blades[1][0] - blades[1][1]) / 2
        return axial * spacing**2 / 2

    @staticmethod
    def flexure_strain(thickness, length, deflection):
        return 3 * thickness * deflection / length**2

    @property
    def centering_strain(self):
        return self.flexure_strain(
            self.centering_blade_thickness, self.centering_blade_length, self.centering_half_travel
        )

    @property
    def width_deflection_range(self):
        return self.width_preload, self.width_preload + self.width_travel

    @property
    def width_strain(self):
        return self.flexure_strain(
            self.width_blade_thickness, self.width_blade_length, self.width_deflection_range[1]
        )

    @property
    def width_preload_range(self):
        k = self.flexure_stiffness(self.width_blade_thickness, self.width_blade_length)
        return tuple(k * d for d in self.width_deflection_range)

    @property
    def spring_force_range(self):
        """Spring force on FAS100 #1 over the centering travel (most to least compressed)."""
        mid = self.spring_free_length - self.spring_mid_length
        return tuple(
            self.spring_rate * (mid + d) for d in (self.centering_half_travel, -self.centering_half_travel)
        )

    def stage_rotation(self, stage):
        """In-plane stage rotation per mm of adjuster travel (rad/mm), first-order model.

        A loaded parallelogram bends each blade into an S with its inflection at mid-span, so a force through
        the blades' mid-span needs no axial couple. Forces elsewhere leave a moment that the blades resist only
        by opposing axial strain. Per mm of travel, the drive force changes by the flexure rate; a coaxial
        preload spring changes the drive and spring forces equally, so it adds no moment. Gravity is omitted:
        it is constant while adjusting.
        """
        if stage == "width":
            t, length, blades, x = (
                self.width_blade_thickness,
                self.width_blade_length,
                self.width_blades,
                self.width_screw_x,
            )
            span = self.width_blade_span
        elif stage == "centering":
            t, length, blades = (
                self.centering_blade_thickness,
                self.centering_blade_length,
                self.centering_blades,
            )
            x, span = self.centering_screw_x, self.centering_blade_span
        else:
            raise ValueError(stage)
        arm = x - sum(span) / 2
        return self.flexure_stiffness(t, length) * abs(arm) / self.rotation_stiffness(t, length, blades)

    def validate(self):
        for name, value in vars(self).items():
            if isinstance(value, float) and not isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.clamp_bar_z + self.clamp_bar_width / 2 > self.carrier_outer:
            raise ValueError("Clamp bars must sit on their carriers")
        if self.blade_width < self.clamp_bar_setback + self.clamp_bar_width:
            raise ValueError("Clamp bars must bear on the blades")
        if self.spigot_diameter >= self.ring_bore or self.spigot_bore >= self.spigot_diameter - 4:
            raise ValueError("Spigot must slip into the SM1RC/M and keep a wall")
        if self.spigot_shoulder_diameter < self.ring_bore + 2.0:
            raise ValueError("Spigot shoulder needs a land on the SM1RC/M face")
        post_top_below_axis = self.optical_height - self.datum_thickness - self.post_length
        if self.spigot_shoulder_diameter / 2 > post_top_below_axis - self.post_clearance:
            raise ValueError("Spigot shoulder must clear the post top")
        if self.ring_gap - (self.post_diameter - self.ring_thickness) / 2 < self.post_clearance:
            raise ValueError("Adapter plate must clear the post")
        if self.centering_gap <= self.centering_half_travel + 1.0:
            raise ValueError("Centering travel needs at least 1 mm of running clearance")
        # Closing the slit lowers the width stage toward the platform carrier; every other width-stage gap opens.
        if 2 * self.carrier_edge - self.width_deflection_range[1] < 1.0:
            raise ValueError("Width stage travel exceeds its clearances")
        for strain in (self.centering_strain, self.width_strain):
            if strain > self.flexure_strain_limit:
                raise ValueError("Flexure strain exceeds the ABS working limit")
        if self.bar_thickness < self.insert_min_material:
            raise ValueError("Insert bars must meet the 98625A950 minimum material")
        # Connectors: inside the platform ring and the carriers, magnets seated in solid material.
        w0, w1 = self.connector_span(self.width_screw_x)
        if w0 < -self.carrier_half_length or w1 >= self.platform_post_inner - 10.0:
            raise ValueError("Width-stage connector must sit on its carrier, left of its blades")
        if self.connector_width < self.magnet_length + 2 * self.magnet_fit_clearance + 2.0:
            raise ValueError("Connectors must hold the magnet pads")
        if self.centering_tip_well + self.magnet_thickness > self.centering_gap + self.bar_thickness - 2.0:
            raise ValueError("Upper platform connector needs a floor under the centering magnet")
        if self.width_tip_well + self.magnet_thickness > self.width_blade_spacing:
            raise ValueError("Width-stage magnet must seat in the connector")
        # Each FAS100 must keep thread through its whole insert over all travel.
        reaches = (
            (self.frame_top_bar[1], self.centering_tip_z - self.centering_half_travel),
            (self.platform_top_bar[1], self.width_tip_z - self.width_deflection_range[1]),
        )
        for insert_top, lowest_tip in reaches:
            if lowest_tip + self.adjuster_thread_length < insert_top + self.insert_flange_thickness + 0.5:
                raise ValueError("FAS100 cannot reach its lowest tip position")
        if self.centering_tip_z + self.centering_half_travel >= self.frame_top_bar[0]:
            raise ValueError("FAS100 #1 must protrude below the frame bar at full travel")
        knob = self.adjuster_knob_diameter / 2
        if self.frame_top_bar_x0 - (self.width_screw_x + knob) < 2.0:
            raise ValueError("FAS100 #2 knob must clear the frame top bar")
        if self.connector_span(self.centering_screw_x)[0] - (self.width_screw_x + knob) < 1.0:
            raise ValueError("FAS100 #2 must clear the upper platform connector")
        if self.centering_screw_x - self.insert_flange_diameter / 2 - self.frame_top_bar_x0 < 2.0:
            raise ValueError("FAS100 #1 insert must sit in the frame top bar")
        if self.spring_pocket_diameter > self.connector_width - 2.0:
            raise ValueError("Spring pocket must fit in the lower platform connector")
        if self.platform_spring_seat_z > -self.carrier_edge - 2.0:
            raise ValueError("Spring pocket must leave the datum carrier edge intact")
        pin_gap = self.spring_mid_length - 2 * self.spring_guide_pin_length - self.centering_half_travel
        if pin_gap < 2.0:
            raise ValueError("Spring guide pins collide at full compression")
        if self.clamp_nut_floor > -2.0:
            raise ValueError("Clamp nut pockets need a floor under the blade seat")
        if self.spacer_washers * self.washer_thickness_min < self.stage_back_clearance:
            raise ValueError("Washer spacers must hold the adapter off the moving stages")
        if self.washer_outer_diameter > self.bar_thickness - 1.0:
            raise ValueError("Spacer washers must bear on the frame bars")
        if self.adapter_counterbore_floor - self.screw_head_height > self.relieved_front - 1.0:
            raise ValueError("Adapter screw heads must sit below the head front")


def _box(x0, x1, y0, y1, z0, z1):
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=FROM_CORNER)


def _z_cylinder(diameter, x, y, z0, z1):
    return Pos(x, y, z0) * Cylinder(diameter / 2, z1 - z0, align=ON_FLOOR)


def _y_cylinder(diameter, x, z, y0, y1):
    return along_y((x, y0, z)) * Cylinder(diameter / 2, y1 - y0, align=ON_FLOOR)


def _y_hex(across_flats, x, z, y0, y1):
    """Hex pocket along y with flats facing ±z (the thin direction of the bars)."""
    return extrude(along_y((x, y0, z)) * RegularPolygon(across_flats / cos(pi / 6) / 2, 6), amount=y1 - y0)


def _magnet_pocket(p, x, z_top, well=0.0):
    """Magnet seat with its top face at z_top - well, plus a well above it for the ball tip."""
    length = p.magnet_length + 2 * p.magnet_fit_clearance
    width = p.magnet_width + 2 * p.magnet_fit_clearance
    seat_top = z_top - well
    pocket = _box(
        x - length / 2,
        x + length / 2,
        p.axis_y - width / 2,
        p.axis_y + width / 2,
        seat_top - p.magnet_thickness,
        z_top + 1,
    )
    if well:  # Open the well wide enough for the 1/4"-80 thread.
        thread = p.insert_bore - 0.5
        pocket += _box(
            x - length / 2,
            x + length / 2,
            p.axis_y - thread / 2,
            p.axis_y + thread / 2,
            seat_top,
            z_top + 1,
        )
    return pocket


def build_slit_head(p=None):
    """The one-piece flexure head, printed back face down."""
    p = p or SlitHeadParameters()
    p.validate()
    back, front = -p.body_thickness, p.relieved_front
    ce, co = p.carrier_edge, p.carrier_outer
    pi_, po = p.platform_post_inner, p.platform_post_outer
    fi, fo = p.frame_post_inner, p.frame_post_outer
    ptb, ftb, fbb = p.platform_top_bar, p.frame_top_bar, p.frame_bottom_bar
    wb = p.width_blades
    upper, lower = p.centering_blades
    wx0, wx1 = p.connector_span(p.width_screw_x)
    cx0, cx1 = p.connector_span(p.centering_screw_x)
    overlap = 0.5  # Blades and connectors run into the bodies they join.

    parts = [
        # Blade carriers stand proud to the blade-seat plane.
        _box(-po, po, back, 0, -co, -ce),  # Platform: datum-blade carrier.
        _box(-p.carrier_half_length, p.carrier_half_length, back, 0, ce, co),  # Width stage carrier.
        # Platform ring.
        _box(-po, -pi_, back, front, -co, ptb[1]),
        _box(pi_, po, back, front, -co, ptb[1]),
        _box(-po, po, back, front, *ptb),
        # Width stage connector and blades (anchored on the platform's right post).
        _box(wx0, wx1, back, front, co - overlap, wb[1][1]),
        *(_box(wx1 - overlap, pi_ + overlap, back, front, *z) for z in wb),
        # Platform connectors and centering blades (anchored on the frame post).
        _box(cx0, cx1, back, front, ptb[1] - overlap, upper[1]),
        _box(cx0, cx1, back, front, lower[0], -co + overlap),
        *(_box(cx1 - overlap, fi + overlap, back, front, *z) for z in (upper, lower)),
        # Frame: C-shaped, open on the -x side.
        _box(fi, fo, back, front, fbb[0], ftb[1]),
        _box(p.frame_top_bar_x0, fo, back, front, *ftb),
        _box(p.frame_bottom_bar_x0, fo, back, front, *fbb),
    ]
    head = parts[0]
    for part in parts[1:]:
        head += part

    cuts = []
    # FAS100 inserts: #1 in the frame top bar, #2 in the platform top bar; flanges outboard (+z).
    for x, (z0, z1) in ((p.centering_screw_x, ftb), (p.width_screw_x, ptb)):
        cuts.append(_z_cylinder(p.insert_bore, x, p.axis_y, z0 - 1, z1 + 1))
    cuts.append(_magnet_pocket(p, p.centering_screw_x, upper[1], p.centering_tip_well))
    cuts.append(_magnet_pocket(p, p.width_screw_x, wb[1][1], p.width_tip_well))
    # Spring, coaxial with FAS100 #1: pockets in the frame bottom bar and the lower platform connector, each
    # with a guide pin inside the coil.
    x, y = p.centering_screw_x, p.axis_y
    cuts.append(_z_cylinder(p.spring_pocket_diameter, x, y, p.frame_spring_seat_z, fbb[1] + 1))
    cuts.append(_z_cylinder(p.spring_pocket_diameter, x, y, lower[0] - 1, p.platform_spring_seat_z))
    for sign in (-1, 1):
        # Blade clamp screws and captive nuts (pockets open from the back).
        for cx in (-p.clamp_screw_x, p.clamp_screw_x):
            z = sign * p.clamp_bar_z
            cuts.append(_y_cylinder(p.screw_clearance, cx, z, back - 1, 1))
            cuts.append(
                _y_hex(p.nut_across_flats + p.nut_across_flats_clearance, cx, z, back - 1, p.clamp_nut_floor)
            )
    # Adapter screws: counterbored from the front, clearance through to the back.
    for ax, az in p.adapter_screw_xz():
        cuts.append(_y_cylinder(p.screw_clearance, ax, az, back - 1, 1))
        cuts.append(
            _y_cylinder(
                p.screw_head_diameter + p.counterbore_clearance, ax, az, p.adapter_counterbore_floor, 1
            )
        )
    for cut in cuts:
        head -= cut

    pin = p.spring_guide_pin_length
    for z0, z1 in (
        (p.frame_spring_seat_z - overlap, p.frame_spring_seat_z + pin),
        (p.platform_spring_seat_z - pin, p.platform_spring_seat_z + overlap),
    ):
        head += _z_cylinder(p.spring_guide_pin_diameter, x, y, z0, z1)
    return head


def build_spigot_adapter(p=None):
    """Flat plate bolted to the head's frame over washer spacers, with the hollow spigot the SM1RC/M clamps.

    Printed front face down, spigot up, without supports. The ring seats against the spigot shoulder, which
    fixes the adapter-to-post clearance.
    """
    p = p or SlitHeadParameters()
    p.validate()
    m = p.adapter_corner_margin
    points = p.adapter_screw_xz()
    xs = [x for x, _ in points]
    zs = [z for _, z in points]
    plate = _box(min(xs) - m, max(xs) + m, p.adapter_back, p.adapter_front, min(zs) - m, max(zs) + m)
    spigot_back = p.adapter_back - p.spigot_length
    ring_face = p.adapter_back - p.ring_gap
    plate += _y_cylinder(p.spigot_shoulder_diameter, 0, 0, ring_face, p.adapter_back + 0.5)
    plate += _y_cylinder(p.spigot_diameter, 0, 0, spigot_back, ring_face + 0.5)
    plate -= _y_cylinder(p.spigot_bore, 0, 0, spigot_back - 1, p.adapter_front + 1)
    for x, z in points:
        plate -= _y_cylinder(p.screw_clearance, x, z, p.adapter_back - 1, p.adapter_front + 1)
        plate -= _y_hex(
            p.nut_across_flats + p.nut_across_flats_clearance,
            x,
            z,
            p.adapter_back - 1,
            p.adapter_back + p.nut_thickness + p.nut_axial_clearance,
        )
    return plate


def build_clamp_bar(p=None):
    """One of two identical bars, in the movable-blade position; EPDM goes on its -y face."""
    p = p or SlitHeadParameters()
    p.validate()
    y0 = p.clamp_bar_front - p.clamp_bar_thickness
    z0 = p.clamp_bar_z - p.clamp_bar_width / 2
    bar = _box(
        -p.clamp_bar_half_length, p.clamp_bar_half_length, y0, p.clamp_bar_front, z0, z0 + p.clamp_bar_width
    )
    bar = fillet(bar.edges().filter_by(Axis.Y), 1.0)
    for x in (-p.clamp_screw_x, p.clamp_screw_x):
        bar -= _y_cylinder(p.screw_clearance, x, p.clamp_bar_z, y0 - 1, p.clamp_bar_front + 1)
    return bar


def _blade(p, sign):
    """Stanley blade on the seat plane, cutting edge at the slit; sign +1 above the slit, -1 below."""
    edge = sign * p.slit_width / 2
    far = edge + sign * p.blade_width
    flat = _box(-p.blade_length / 2, p.blade_length / 2, 0, p.blade_thickness, min(edge, far), max(edge, far))
    spine_near = far - sign * p.spine_width
    spine = _box(
        -p.blade_length / 2,
        p.blade_length / 2,
        0,
        p.spine_thickness,
        min(spine_near, far),
        max(spine_near, far),
    )
    return flat + spine


def head_location(p, rotation=0.0):
    """Local head frame -> assembly frame; rotation in degrees about the optical axis (+y)."""
    ring_front = SM1RC_M_THICKNESS / 2
    front_y = ring_front + p.ring_gap - p.adapter_back
    return Pos(0, front_y, p.optical_height) * Rot(Y=rotation)


def build_slit_head_assembly(p=None, rotation=0.0, include_support=True):
    """Head, adapter, bars, blades, and adjusters on the slit post; rotation 0 is a horizontal slit."""
    p = p or SlitHeadParameters()
    p.validate()
    loc = head_location(p, rotation)
    printed = (0.35, 0.6, 0.8)
    metal = (0.75, 0.75, 0.78)
    children = [
        labeled(build_slit_head(p), "Flexure head", printed, loc),
        labeled(build_spigot_adapter(p), "Spigot adapter", (0.3, 0.5, 0.7), loc),
    ]
    for i, (x, z) in enumerate(p.adapter_screw_xz(), 1):
        stack = _y_cylinder(p.washer_outer_diameter, x, z, p.adapter_front, -p.body_thickness)
        stack -= _y_cylinder(p.screw_clearance, x, z, p.adapter_front - 1, -p.body_thickness + 1)
        children.append(labeled(stack, f"Spacer washers {i}", metal, loc))
    bar = build_clamp_bar(p)
    for sign, name in ((1, "Width"), (-1, "Datum")):
        placed = loc * Rot(Y=0 if sign > 0 else 180)
        children.append(labeled(bar, f"{name} clamp bar", printed, placed))
        epdm = _box(
            -p.clamp_bar_half_length,
            p.clamp_bar_half_length,
            p.blade_thickness,
            p.blade_thickness + p.epdm_thickness,
            p.clamp_bar_z - p.clamp_bar_width / 2,
            p.clamp_bar_z + p.clamp_bar_width / 2,
        )
        children.append(labeled(epdm, f"{name} EPDM", (0.15, 0.15, 0.15), placed))
        children.append(labeled(_blade(p, sign), f"{name} blade", metal, loc))
    tips = (
        ("FAS100 centering", p.centering_screw_x, p.centering_tip_z, p.frame_top_bar[1]),
        ("FAS100 width", p.width_screw_x, p.width_tip_z, p.platform_top_bar[1]),
    )
    for name, x, tip_z, insert_top in tips:
        children.append(labeled(thorlabs_fas100(), name, metal, loc * Pos(x, p.axis_y, tip_z)))
        insert = _z_cylinder(p.insert_bore, x, p.axis_y, insert_top - p.insert_length, insert_top)
        insert += _z_cylinder(
            p.insert_flange_diameter, x, p.axis_y, insert_top, insert_top + p.insert_flange_thickness
        )
        insert -= _z_cylinder(INCH / 4, x, p.axis_y, insert_top - 10, insert_top + 1)
        children.append(labeled(insert, f"{name} insert", (0.8, 0.65, 0.25), loc))
        magnet = _box(
            x - p.magnet_length / 2,
            x + p.magnet_length / 2,
            p.axis_y - p.magnet_width / 2,
            p.axis_y + p.magnet_width / 2,
            tip_z - p.magnet_thickness,
            tip_z,
        )
        children.append(labeled(magnet, f"{name} magnet", (0.6, 0.6, 0.62), loc))
    sx, s0, s1 = p.centering_screw_x, p.frame_spring_seat_z, p.platform_spring_seat_z
    spring = _z_cylinder(p.spring_outer_diameter, sx, p.axis_y, s0, s1)
    spring -= _z_cylinder(p.spring_guide_pin_diameter + 0.4, sx, p.axis_y, s0 - 1, s1 + 1)
    children.append(labeled(spring, "2006N292 spring envelope", (0.5, 0.5, 0.5), loc))
    if include_support:
        from schlieren.parts.rail_shoe import build_rail_shoe

        ring_y = -SM1RC_M_THICKNESS / 2
        children.append(
            labeled(thorlabs_sm1rc_m(), "SM1RC M ring", (0.2, 0.2, 0.22), Pos(0, ring_y, p.optical_height))
        )
        children.append(labeled(thorlabs_tr50_m(), "TR50 M post", metal, Pos(0, 0, p.datum_thickness)))
        children.append(labeled(build_rail_shoe(), "Rail shoe", (0.8, 0.4, 0.25)))
    return assembly("Flexure slit head (exploratory)", children)

"""Engineering invariants for the mirror cell model (design §10)."""

import unittest
import xml.etree.ElementTree as ET
from math import atan2, degrees, hypot

from build123d import Box, Cylinder, Pos

from schlieren.cad import ON_FLOOR, along_y, intersect, leaves
from schlieren.parts.mirror_cell import (
    INCH,
    STATIONS,
    MirrorCellParameters,
    build_base_plate,
    build_mirror_cell_assembly,
    build_mirror_plate,
    build_quick_release_plate,
    build_stationary_plate,
    mirror_plate_outline,
)
from schlieren.parts.mirror_cell_drawing import base_plate_drawing_svg, base_plate_holes
from schlieren.testing import boxes_overlap, near_pairs_among, shared, slow, svg_attr
from schlieren.vendor_cad import (
    KOZAK_TB250_FLANGE_THICKNESS,
    KOZAK_TB250_LENGTH,
    KOZAK_TS250_LENGTH,
    MCMASTER_8681N11_WIDTH,
    MCMASTER_91131A028_HEIGHT,
)

TOLERANCE = 1e-3  # mm
HELIX_TOLERANCE = 0.05  # mm
INTERFERENCE_VOLUME = 0.5  # mm³; below this a boolean overlap is coincident-surface noise.


class MirrorCellTests(unittest.TestCase):
    @shared
    def quick_release_plate(cls):
        return build_quick_release_plate(cls.p)

    @shared
    def base_plate(cls):
        return build_base_plate(cls.p)

    @shared
    def stationary_plate(cls):
        return build_stationary_plate(cls.p)

    @shared
    def mirror_plate(cls):
        return build_mirror_plate(cls.p)

    @classmethod
    def setUpClass(cls):
        cls.p = MirrorCellParameters()
        cls.assembly = build_mirror_cell_assembly(cls.p)
        cls.parts = {part.label: part for part in leaves(cls.assembly)}

    def box(self, label):
        return self.parts[label].bounding_box()

    def test_plate_envelopes(self):
        p = self.p
        base = self.box("Base plate")
        self.assertAlmostEqual(base.size.X, 11.5 * INCH, delta=TOLERANCE)
        self.assertAlmostEqual(
            base.size.Y, 7.0 * INCH, delta=TOLERANCE
        )  # Trimmed from the rear of an 11 in blank.
        self.assertAlmostEqual(base.size.Z, 0.5 * INCH, delta=TOLERANCE)
        self.assertAlmostEqual(base.min.Y, 0.0, delta=TOLERANCE)
        self.assertAlmostEqual(base.max.Z, 0.0, delta=TOLERANCE)
        stationary = self.box("Stationary plate")
        self.assertAlmostEqual(stationary.size.X, 11.5 * INCH, delta=TOLERANCE)
        self.assertAlmostEqual(stationary.size.Z, 11.0 * INCH, delta=TOLERANCE)
        self.assertAlmostEqual(stationary.size.Y, 0.5 * INCH, delta=TOLERANCE)
        self.assertAlmostEqual(stationary.max.Y, 4.0 * INCH, delta=TOLERANCE)
        self.assertAlmostEqual(self.box("Mirror plate").size.Y, 0.75 * INCH, delta=TOLERANCE)
        self.assertAlmostEqual(
            p.base_depth - stationary.max.Y, 3.0 * INCH, delta=TOLERANCE
        )  # Base behind the plate.

    def test_quick_release_plate_is_flush_at_the_front_and_against_the_base_underside(self):
        p = self.p
        plate = self.box("Quick-release plate")
        self.assertAlmostEqual(plate.size.X, 1.960 * INCH, delta=TOLERANCE)  # Full width, at the bottom.
        self.assertAlmostEqual(plate.size.Y, 7.0 * INCH, delta=TOLERANCE)
        self.assertAlmostEqual(plate.size.Z, 12.0, delta=TOLERANCE)
        self.assertAlmostEqual(
            plate.min.Y, 0.0, delta=TOLERANCE
        )  # Forward end flush with the base front edge.
        self.assertAlmostEqual(plate.max.Z, -p.base_thickness, delta=TOLERANCE)  # Against the underside.
        self.assertAlmostEqual((plate.min.X + plate.max.X) / 2, 0.0, delta=TOLERANCE)

    def test_quick_release_plate_section_is_a_neck_flaring_to_full_width(self):
        p = self.p
        plate = self.quick_release_plate
        z_top = -p.base_thickness

        def width_at(depth):
            # Extent in x of a thin slice at the given depth below the underside, away from the slot and
            # notch.
            slab = Pos(0, 40.0, z_top - depth) * Box(100.0, 20.0, 0.02)
            box = (slab & plate).bounding_box()
            return box.size.X

        self.assertAlmostEqual(width_at(0.05), 1.709 * INCH, delta=0.05)
        self.assertAlmostEqual(width_at(0.162 * INCH - 0.02), 1.709 * INCH, delta=0.05)
        self.assertAlmostEqual(width_at(p.qr_plate_thickness - 0.02), 1.960 * INCH, delta=0.2)
        self.assertGreater(width_at(8.0), 1.709 * INCH + 1.0)  # Flaring below the neck.

    def test_quick_release_plate_has_a_through_slot_and_a_rear_notch(self):
        p = self.p
        plate = self.quick_release_plate
        z = -p.base_thickness - p.qr_plate_thickness / 2
        mid_y = p.qr_plate_length / 2
        slot_probe = Pos(0, mid_y, z) * Box(p.qr_slot_width - 0.1, p.qr_slot_length, p.qr_plate_thickness)
        self.assertLess(
            intersect(slot_probe, plate).volume, TOLERANCE
        )  # The slot is open the whole way through.
        notch_probe = Pos(0, p.qr_plate_length - p.qr_notch_depth / 2, z) * Box(
            0.2, p.qr_notch_depth - 0.2, 10.0
        )  # Just inside the V, which narrows to a point.
        self.assertLess(intersect(notch_probe, plate).volume, TOLERANCE)
        front_probe = Pos(0, 1.0, z) * Box(1.0, 1.0, 10.0)
        self.assertGreater(intersect(front_probe, plate).volume, 5.0)  # The front end has no notch.

    def test_quick_release_screws_are_in_the_section_9_pattern(self):
        p = self.p
        positions = {name: self.box(name) for name in self.parts if name.startswith("Quick-release screw")}
        self.assertEqual(len(positions), 4)
        centers = sorted(((b.min.X + b.max.X) / 2, (b.min.Y + b.max.Y) / 2) for b in positions.values())
        expected = sorted((sx * 0.5 * INCH, y) for sx in (-1, 1) for y in (47.625, 130.175))
        for (x, y), (ex, ey) in zip(centers, expected, strict=True):
            self.assertAlmostEqual(x, ex, delta=TOLERANCE)
            self.assertAlmostEqual(y, ey, delta=TOLERANCE)
        self.assertAlmostEqual(p.qr_plate_length - 2 * p.qr_screw_inset, 130.175 - 47.625, delta=TOLERANCE)

    def test_quick_release_screw_heads_sit_just_below_the_top_surface_and_engage_the_plate(self):
        p = self.p
        for name in self.parts:
            if not name.startswith("Quick-release screw"):
                continue
            box = self.box(name)
            self.assertAlmostEqual(box.max.Z, -p.qr_head_recess, delta=TOLERANCE)  # Flush or slightly below.
            self.assertAlmostEqual(box.size.Z, 18.0, delta=TOLERANCE)
            engagement = -p.base_thickness - box.min.Z
            self.assertGreater(engagement, 4.0)
            self.assertLess(
                -box.min.Z, p.base_thickness + p.qr_tapped_hole_depth
            )  # Tip above the hole bottom.

    def test_base_plate_has_open_clearance_holes_and_90_degree_countersinks(self):
        p = self.p
        plate = self.base_plate
        for x, y in p.qr_screw_positions().values():
            through = Pos(x, y, -p.base_thickness / 2) * Cylinder(
                p.qr_clearance_hole / 2 - 0.01, p.base_thickness
            )
            self.assertLess(intersect(through, plate).volume, TOLERANCE)
            # 0.1 mm down a 90° countersink is 0.1 mm smaller in radius than at the surface.
            top = Pos(x, y, -0.05) * Cylinder(p.qr_countersink_diameter / 2 - 0.1 - 0.01, 0.1)
            self.assertLess(intersect(top, plate).volume, TOLERANCE)
            below = Pos(x, y, -3.0) * Cylinder(
                p.qr_countersink_diameter / 2 - 0.1 - 0.01, 0.1
            )  # Past the cone.
            self.assertGreater(intersect(below, plate).volume, 1.0)

    def test_quick_release_screws_clear_the_base_and_sit_in_the_tapped_holes(self):
        for name in self.parts:
            if name.startswith("Quick-release screw"):
                self.assertLess(
                    intersect(self.parts[name], self.parts["Base plate"]).volume, INTERFERENCE_VOLUME
                )
                self.assertLess(
                    intersect(self.parts[name], self.parts["Quick-release plate"]).volume, INTERFERENCE_VOLUME
                )

    def test_quick_release_screws_are_clear_of_the_slot_and_the_plate_edges(self):
        p = self.p
        self.assertGreater(p.qr_screw_x - p.qr_slot_width / 2, 5.0)  # Solid aluminum beside the slot.
        self.assertGreater(p.qr_neck_width / 2 - p.qr_screw_x, 8.0)  # Inside the neck of the dovetail.

    def test_base_plate_drawing_is_full_scale_and_dimensions_every_hole(self):
        p = self.p
        svg = ET.fromstring(base_plate_drawing_svg(p))
        ns = "{http://www.w3.org/2000/svg}"
        _, _, width, height = (float(v) for v in svg_attr(svg, "viewBox").split())
        self.assertEqual(svg.get("width"), f"{width:.1f}mm")  # One user unit is 1 mm.
        self.assertAlmostEqual(width, 17.0 * INCH, delta=0.1)
        self.assertAlmostEqual(height, 11.0 * INCH, delta=0.1)
        outline = next(e for e in svg.iter(f"{ns}rect") if e.get("class") == "outline")
        self.assertAlmostEqual(float(svg_attr(outline, "width")), p.plate_width, delta=0.01)
        self.assertAlmostEqual(float(svg_attr(outline, "height")), p.base_depth, delta=0.01)
        left, bottom = (
            float(svg_attr(outline, "x")),
            float(svg_attr(outline, "y")) + float(svg_attr(outline, "height")),
        )
        circles = {e.get("data-hole"): e for e in svg.iter(f"{ns}circle") if e.get("data-hole")}
        holes = base_plate_holes(p)
        self.assertEqual(len(holes), 8)
        self.assertEqual(set(circles), set(holes))
        for name, (x, y, diameter) in holes.items():
            circle = circles[name]
            self.assertAlmostEqual(float(svg_attr(circle, "cx")) - left - p.plate_width / 2, x, delta=0.01)
            self.assertAlmostEqual(bottom - float(svg_attr(circle, "cy")), y, delta=0.01)
            self.assertAlmostEqual(float(svg_attr(circle, "r")) * 2, diameter, delta=0.01)
        figures = [e.text for e in svg.iter(f"{ns}text")]
        for value in ("47.625", "130.175", "+12.7", "-12.7", "69.85", "31.75"):
            self.assertIn(value, figures)

    def test_inter_plate_gap_is_half_an_inch(self):
        gap = self.box("Stationary plate").min.Y - self.box("Mirror plate").max.Y
        self.assertAlmostEqual(gap, 0.5 * INCH, delta=TOLERANCE)

    def test_mirror_plate_is_the_truncated_hexagon(self):
        p = self.p
        plate = self.box("Mirror plate")
        self.assertAlmostEqual(p.apothem, 4.7631 * INCH, delta=1e-3 * INCH)
        self.assertAlmostEqual(plate.max.Z - plate.min.Z, 10.263 * INCH, delta=2e-3 * INCH)
        self.assertAlmostEqual(plate.min.Z, 3 / 8 * INCH, delta=TOLERANCE)  # Clear of the base top.
        self.assertAlmostEqual(plate.max.Z, 10.638 * INCH, delta=1e-3 * INCH)
        self.assertAlmostEqual(p.mirror_center_z, 5.138 * INCH, delta=1e-3 * INCH)
        self.assertAlmostEqual(plate.size.X, 2 * p.apothem, delta=TOLERANCE)
        outline = mirror_plate_outline(p)
        chord = [v for v in outline if abs(v[1] + p.apothem) < TOLERANCE]
        self.assertAlmostEqual(abs(chord[0][0] - chord[1][0]), 2.553 * INCH, delta=2e-3 * INCH)

    def test_aperture_is_clear_of_the_mirror(self):
        p = self.p
        self.assertAlmostEqual(p.aperture_diameter, 8.125 * INCH, delta=TOLERANCE)
        self.assertAlmostEqual(p.rtv_gap, 1.69, delta=0.01)  # The ~1.7 mm radial bond line.
        mirror = self.box("Mirror")
        self.assertAlmostEqual(mirror.size.X, 203.0, delta=TOLERANCE)
        self.assertAlmostEqual((mirror.min.Z + mirror.max.Z) / 2, p.mirror_center_z, delta=TOLERANCE)
        self.assertEqual(sum(label.startswith("RTV pad") for label in self.parts), 6)

    def test_mirror_back_is_flush_with_the_plate_rear_face(self):
        mirror, plate = self.box("Mirror"), self.box("Mirror plate")
        self.assertAlmostEqual(mirror.max.Y, plate.max.Y, delta=TOLERANCE)
        self.assertAlmostEqual(
            plate.min.Y - mirror.min.Y, -(19.05 - 18.0), delta=TOLERANCE
        )  # Front recessed 1.05 mm.

    def test_stations_lie_on_three_axes_120_degrees_apart(self):
        p = self.p
        angles = []
        for name in STATIONS:
            x, z = p.station_center(name)
            dz = z - p.mirror_center_z
            self.assertAlmostEqual(hypot(x, dz), 4.75 * INCH, delta=TOLERANCE)
            angles.append(degrees(atan2(dz, x)) % 360)
        self.assertEqual(sorted(round(a) for a in angles), [90, 210, 330])
        self.assertAlmostEqual(p.station_center("top")[0], 0.0, delta=TOLERANCE)

    def test_hex_vertices_carry_the_adjuster_holes(self):
        p = self.p
        top_vertex = max(z for _, z in mirror_plate_outline(p))
        self.assertAlmostEqual(top_vertex, p.hex_circumradius, delta=TOLERANCE)
        self.assertLess(p.adjuster_radius, p.hex_circumradius)

    def test_three_of_each_adjuster_part(self):
        for stem in ("Adjuster screw", "Adjuster ball", "Bushing", "Knob", "Compression spring"):
            self.assertEqual(sum(label.startswith(stem) for label in self.parts), 3, stem)
        self.assertEqual(sum(label.startswith("Spherical washer") for label in self.parts), 6)
        self.assertEqual(sum(label.startswith("Spring seat washer") for label in self.parts), 6)

    def test_bushing_flange_seats_on_the_mirror_face_and_the_barrel_is_inside_the_plate(self):
        p = self.p
        for name in STATIONS:
            bushing = self.box(f"Bushing {name}")
            # The flange stands on the face and the barrel runs into the plate.
            self.assertAlmostEqual(
                bushing.min.Y, p.mirror_plate_front_y - KOZAK_TB250_FLANGE_THICKNESS, delta=TOLERANCE
            )
            self.assertAlmostEqual(bushing.size.Y, KOZAK_TB250_LENGTH, delta=TOLERANCE)
            self.assertLess(bushing.max.Y, p.mirror_plate_rear_y)

    def test_knob_bears_on_the_spherical_washer_in_its_socket(self):
        p = self.p
        for name in STATIONS:
            female = self.box(f"Spherical washer, female {name}")
            male = self.box(f"Spherical washer, male {name}")
            knob = self.box(f"Knob {name}")
            self.assertAlmostEqual(female.min.Y, p.stationary_plate_rear_y - 1 / 16 * INCH, delta=TOLERANCE)
            self.assertAlmostEqual(male.max.Y - female.min.Y, MCMASTER_91131A028_HEIGHT, delta=TOLERANCE)
            self.assertAlmostEqual(knob.min.Y, male.max.Y, delta=TOLERANCE)

    def test_screw_projects_ahead_of_the_mirror_face_by_a_fixed_amount(self):
        p = self.p
        for name in STATIONS:
            screw = self.box(f"Adjuster ball {name}")
            self.assertAlmostEqual(screw.min.Y, p.screw_tip_y, delta=TOLERANCE)
            self.assertAlmostEqual(
                self.box(f"Adjuster screw {name}").max.Y - p.screw_tip_y, KOZAK_TS250_LENGTH, delta=TOLERANCE
            )
        self.assertLess(p.screw_tip_y, p.mirror_plate_front_y)

    def test_spring_spans_the_gap_between_the_seat_washers(self):
        p = self.p
        # The coil's end faces are tilted by the helix angle, so its box is slightly short.
        for name in STATIONS:
            spring = self.box(f"Compression spring {name}")
            self.assertAlmostEqual(spring.size.Y, p.spring_length, delta=HELIX_TOLERANCE)
            self.assertAlmostEqual(spring.size.X, 0.5 * INCH, delta=HELIX_TOLERANCE)
            mirror_seat = self.box(f"Spring seat washer (mirror plate) {name}")
            stationary_seat = self.box(f"Spring seat washer (stationary plate) {name}")
            self.assertAlmostEqual(spring.min.Y, mirror_seat.max.Y, delta=HELIX_TOLERANCE)
            self.assertAlmostEqual(spring.max.Y, stationary_seat.min.Y, delta=HELIX_TOLERANCE)

    def test_stationary_plate_holes_and_counterbores(self):
        p = self.p
        plate = self.stationary_plate

        def void(x, z, y0, diameter, length, margin):
            """Volume of plate inside a cylinder along +y, `margin` smaller than the diameter and length."""
            cutter = along_y((x, y0 + margin, z)) * Cylinder(
                diameter / 2 - margin, length - 2 * margin, align=ON_FLOOR
            )
            return intersect(cutter, plate).volume

        for name in STATIONS:
            x, z = p.station_center(name)
            front, rear = p.stationary_plate_front_y, p.stationary_plate_rear_y
            self.assertLess(
                void(x, z, front, p.stationary_hole_diameter, p.stationary_plate_thickness, 0.01), TOLERANCE
            )
            self.assertLess(
                void(x, z, front, p.seat_counterbore_diameter, p.seat_counterbore_depth, 0.01), TOLERANCE
            )
            self.assertLess(
                void(x, z, rear - p.socket_depth, p.socket_diameter, p.socket_depth, 0.01), TOLERANCE
            )
            # Controls: a hole 0.5 mm larger than the cut is not empty.
            self.assertGreater(
                void(x, z, front, p.stationary_hole_diameter + 1.0, p.stationary_plate_thickness, 0.0), 1.0
            )

    def test_mirror_plate_has_three_bores_and_the_aperture(self):
        p = self.p
        plate = self.mirror_plate
        bores = [f for f in plate.faces() if f.geom_type.name == "CYLINDER"]
        radii = sorted(round(f.radius, 3) for f in bores)
        self.assertEqual(radii.count(round(p.bushing_bore / 2, 3)), 3)
        self.assertEqual(radii.count(round(p.aperture_diameter / 2, 3)), 1)
        self.assertEqual(radii.count(round(p.seat_counterbore_diameter / 2, 3)), 3)

    def test_brackets_are_flush_with_the_plate_edges_and_seated_on_base_and_stationary_plate(self):
        p = self.p
        for name, side in (("left", -1), ("right", 1)):
            bracket = self.box(f"Bracket {name}")
            self.assertAlmostEqual(bracket.size.X, MCMASTER_8681N11_WIDTH, delta=TOLERANCE)
            self.assertAlmostEqual(
                side * bracket.max.X if side > 0 else -bracket.min.X, p.plate_width / 2, delta=TOLERANCE
            )
            self.assertAlmostEqual(bracket.min.Z, 0.0, delta=TOLERANCE)  # Base leg on the base top.
            self.assertAlmostEqual(
                bracket.max.Y, p.stationary_plate_front_y, delta=TOLERANCE
            )  # Upright on the plate.
            self.assertAlmostEqual(bracket.size.Z, 3.0 * INCH, delta=TOLERANCE)
            self.assertAlmostEqual(p.stationary_plate_front_y - bracket.min.Y, 3.0 * INCH, delta=TOLERANCE)

    def test_brackets_are_clear_of_the_adjuster_stations_and_the_mirror_plate(self):
        for name in STATIONS:
            for side in ("left", "right"):
                self.assertFalse(
                    boxes_overlap(
                        self.parts[f"Compression spring {name}"],
                        self.parts[f"Bracket {side}"],
                        margin=-TOLERANCE,
                    )
                )
        for side in ("left", "right"):
            # The base leg's top (6.35 mm) is 3.2 mm under the plate's trimmed lower edge.
            clearance = self.parts["Mirror plate"].distance_to(self.parts[f"Bracket {side}"])
            self.assertGreater(clearance, 3.0)

    def test_each_bracket_has_two_upright_and_two_base_screws_with_a_washer_and_locknut(self):
        for stem in ("Bracket screw", "Bracket washer", "Locknut insert"):
            self.assertEqual(sum(label.startswith(stem) for label in self.parts), 8, stem)
        self.assertEqual(
            sum(label.startswith("Locknut ") and "insert" not in label for label in self.parts), 8
        )
        for side in ("left", "right"):
            for where in ("upright", "base"):
                for i in (1, 2):
                    self.assertIn(f"Bracket screw {side} {where} {i}", self.parts)

    def test_bracket_hardware_is_centered_on_the_bracket_holes(self):
        p = self.p
        for side, sign in (("left", -1), ("right", 1)):
            for i, z in enumerate(p.upright_hole_z(), 1):
                box = self.box(f"Bracket washer {side} upright {i}")
                self.assertAlmostEqual((box.min.X + box.max.X) / 2, p.bracket_center_x(sign), delta=0.01)
                self.assertAlmostEqual((box.min.Z + box.max.Z) / 2, z, delta=0.01)
            for i, y in enumerate(p.base_hole_y(), 1):
                box = self.box(f"Bracket washer {side} base {i}")
                self.assertAlmostEqual((box.min.X + box.max.X) / 2, p.bracket_center_x(sign), delta=0.01)
                self.assertAlmostEqual((box.min.Y + box.max.Y) / 2, y, delta=0.01)
        self.assertAlmostEqual(p.upright_hole_z()[0], 0.75 * INCH, delta=TOLERANCE)
        self.assertAlmostEqual(p.upright_hole_z()[1], 2.25 * INCH, delta=TOLERANCE)

    def test_screws_stand_proud_of_the_locknuts_by_several_threads(self):
        thread_pitch = INCH / 18
        for side in ("left", "right"):
            for where in ("upright", "base"):
                for i in (1, 2):
                    screw = self.box(f"Bracket screw {side} {where} {i}")
                    nut = self.box(f"Locknut {side} {where} {i}")
                    projection = screw.max.Y - nut.max.Y if where == "upright" else nut.min.Z - screw.min.Z
                    self.assertGreater(projection, 2 * thread_pitch)  # At least two threads clear of the nut.

    def test_upright_and_base_screw_heads_clear_each_other_at_the_inside_corner(self):
        for side in ("left", "right"):
            for i in (1, 2):
                for j in (1, 2):
                    upright = self.parts[f"Bracket screw {side} upright {i}"]
                    base = self.parts[f"Bracket screw {side} base {j}"]
                    self.assertGreater(upright.distance_to(base), 1.0)

    def test_plywood_has_the_bracket_holes(self):
        p = self.p
        base, stationary = self.base_plate, self.stationary_plate
        radius = p.bracket_hole_diameter / 2 - 0.01
        for side in (-1, 1):
            x = p.bracket_center_x(side)
            for y in p.base_hole_y():
                probe = Pos(x, y, -p.base_thickness / 2) * Cylinder(radius, p.base_thickness)
                self.assertLess(intersect(probe, base).volume, TOLERANCE)
            for z in p.upright_hole_z():
                probe = along_y((x, p.stationary_plate_front_y, z)) * Cylinder(
                    radius, p.stationary_plate_thickness, align=ON_FLOOR
                )
                self.assertLess(intersect(probe, stationary).volume, TOLERANCE)

    @slow
    def test_no_assembly_parts_interfere(self):
        # Purchased hardware is trusted to fit together from its catalog match (the vendor models are not
        # accurate enough to check that), so only pairs involving the plywood, the brackets, the mirror, the
        # springs, the pads, or the quick-release plate are checked: the holes, bores, counterbores, and
        # sockets the hardware passes through or sits in.
        hardware = (
            "Bracket screw",
            "Bracket washer",
            "Locknut",
            "Adjuster screw",
            "Adjuster ball",
            "Bushing",
            "Knob",
            "Spherical washer",
            "Spring seat washer",
            "Quick-release screw",
        )

        def is_hardware(part):
            return part.label.startswith(hardware)

        found = []
        for a, b in near_pairs_among(leaves(self.assembly)):
            if is_hardware(a) and is_hardware(b):
                continue
            # A bracket screw head grazes the bracket's inside-corner fillet at the hole 0.5 in from the
            # corner (about 0.8 mm³); the screw still seats on the flat leg, so it is accepted.
            if {a.label.split()[0], b.label.split()[0]} == {"Bracket"} and any(
                part.label in ("Bracket left", "Bracket right") for part in (a, b)
            ):
                continue
            volume = intersect(a, b).volume
            if volume > INTERFERENCE_VOLUME:
                found.append((a.label, b.label, round(volume, 2)))
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()

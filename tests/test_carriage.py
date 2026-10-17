"""Engineering invariants for the preliminary carriage, not print qualification."""

import unittest
from itertools import combinations
from math import cos, pi, radians, sin, tan

from build123d import Align, Box, Cylinder, Plane, Polygon, Pos, RegularPolygon, Rot, extrude

from schlieren.cad import ON_FLOOR, along_y, children_by_label, moved
from schlieren.parts.carriage import (
    CarriageParameters,
    build_carriage,
    build_print_layout,
    support_location,
)
from schlieren.testing import near_pairs, overlap_volume, shared, slow


def y_cylinder(radius, length, y, z):
    """Cylinder along +y from (0, y, z)."""
    return along_y((0, y, z)) * Cylinder(radius, length, align=ON_FLOOR)


class CarriageTests(unittest.TestCase):
    @shared
    def hardware(cls):
        return children_by_label(build_carriage(cls.p, include_hardware=True))

    @shared
    def support(cls):
        """The post stack's parts, from the carriage's "Reference hardware" group."""
        return children_by_label(
            children_by_label(build_carriage(cls.p, include_support=True))["Reference hardware"]
        )

    @classmethod
    def setUpClass(cls):
        cls.p = CarriageParameters()
        cls.parts = children_by_label(build_carriage())
        cls.fixed = cls.parts["Base plate"] + cls.parts["Guide frame"]

    def test_five_valid_single_solids(self):
        self.assertEqual(len(self.parts), 5)
        for s in self.parts.values():
            self.assertTrue(s.is_valid)
            self.assertEqual(len(s.solids()), 1)
        # 86 mm plate, widened to 94 mm only at the side-screw lugs.
        self.assertAlmostEqual(self.parts["Base plate"].bounding_box().size.X, 94)
        self.assertFalse(self.parts["Base plate"].is_inside((43.1, 0, 1)))
        self.assertAlmostEqual(self.parts["Keeper frame"].bounding_box().max.Z, 15.7455, places=3)

    def test_travel_and_loading_clearance(self):
        for travel, retract in ((-5, 0), (0, 0), (5, 0), (0, 6)):
            parts = dict(self.parts)
            parts["Driven plunger"] = moved(parts["Driven plunger"], Pos(0, travel, 0))
            parts["Spring plunger"] = moved(parts["Spring plunger"], Pos(0, travel - retract, 0))
            for (na, a), (nb, b) in combinations(parts.items(), 2):
                self.assertLess((a & b).volume, 1e-6, (travel, retract, na, nb))
            # Keeper has actual bearing overlap above both swept guide ears.
            for name in ("Driven plunger", "Spring plunger"):
                raised = moved(parts[name], Pos(0, 0, 0.5))
                self.assertGreater((raised & parts["Keeper frame"]).volume, 1)

    def test_optical_aperture_and_datum_tracks(self):
        p = self.p
        base = self.fixed
        # Material just beyond the circular opening remains on both travel-axis sides.
        for y in (-p.aperture_diameter / 2 - 0.1, p.aperture_diameter / 2 + 0.1):
            self.assertTrue(base.is_inside((0, y, p.plate_thickness / 2)))
        for travel in (-5, 0, 5):
            beam = Cylinder(p.aperture_diameter / 2, 15, align=ON_FLOOR)
            for name, part in self.parts.items():
                placed = moved(part, Pos(0, travel, 0)) if "plunger" in name else part
                self.assertLess((placed & beam).volume, 1e-6)
            for x, y in p.datum_points:
                self.assertLess(abs(x) + p.datum_head_diameter / 2, 32)
                self.assertLess(abs(y - travel) + p.datum_head_diameter / 2, 32)
                self.assertGreater((x * x + (y - travel) ** 2) ** 0.5 - p.datum_head_diameter / 2, 12)
                self.assertFalse(base.is_inside((x, y, 2)))
                # Hole modeled oversize by the measured print undersize plus the fit clearance.
                self.assertFalse(base.is_inside((x + p.datum_hole_diameter / 2 - 0.05, y, 2)))
                self.assertTrue(base.is_inside((x + p.datum_hole_diameter / 2 + 0.05, y, 2)))

    def test_beveled_cassette_clears_printed_parts(self):
        p = self.p
        rear = p.plate_thickness + p.datum_projection
        front = rear + p.cassette_thickness
        inset = p.bevel_depth / tan(radians(p.bevel_angle))
        profile = [
            (-32, rear),
            (32, rear),
            (32, front - p.bevel_depth),
            (32 - inset, front),
            (-32 + inset, front),
            (-32, front - p.bevel_depth),
        ]
        blank = extrude(Plane.YZ.offset(-32) * Polygon(*profile, align=None), amount=64)
        cassette = blank & moved(blank, Rot(Z=90))
        for travel in (-5, 0, 5):
            shifted = moved(cassette, Pos(0, travel, 0))
            for name, part in self.parts.items():
                placed = moved(part, Pos(0, travel, 0)) if "plunger" in name else part
                self.assertLess((placed & shifted).volume, 1e-6, (travel, name))

    def test_hardware_stack(self):
        p = self.p
        top = p.keeper_z + p.keeper_thickness - p.screw_head_recess
        # M3 x 12 reaches the rear-opening nut with only slight projection.
        self.assertAlmostEqual(top - 12, -0.1)
        for x, y in p.fasteners:
            screw = Pos(x, y, top - 12) * Cylinder(1.5, 12, align=ON_FLOOR)
            nut = extrude(
                Pos(x, y, p.nut_pocket_depth - 2.4) * RegularPolygon(5.5 / cos(pi / 6) / 2, 6), amount=2.4
            )
            for name in ("Base plate", "Guide frame", "Keeper frame"):
                for hardware in (screw, nut):
                    self.assertLess((self.parts[name] & hardware).volume, 1e-6)
        for travel in (-5, 0, 5):
            length = p.spring_fiducial_length + travel
            self.assertIn(length, (11.5, 16.5, 21.5))
        self.assertAlmostEqual(p.rear_wall_thickness, p.keeper_end_member_width)
        self.assertAlmostEqual(p.spring_seat_y, p.keeper_opening_y - p.keeper_opening_length / 2)
        self.assertAlmostEqual(p.plate_length, 123.8002)
        self.assertAlmostEqual(self.parts["Base plate"].bounding_box().size.Y, 123.8002)
        for start, end in p.support_spans:
            expected = p.adjuster_support_length if start > 0 else p.rear_wall_thickness
            self.assertAlmostEqual(end - start, expected)

    def test_plungers_drop_into_open_tracks(self):
        base = self.fixed
        for name in ("Driven plunger", "Spring plunger"):
            for lift in (0, 2, 6, 15):
                self.assertLess((base & moved(self.parts[name], Pos(0, 0, lift))).volume, 1e-6)

    def test_supports_reach_plate_edges_and_keeper_lifts_off(self):
        p = self.p
        base = self.fixed
        for y in (p.plate_ymin + 0.1, p.plate_ymax - 0.1):
            # Out to the plate edge or the rotation envelope, whichever is nearer.
            edge = min(p.plate_width / 2, (p.rotation_envelope_radius**2 - y * y) ** 0.5) - 0.1
            for x in (-edge, -20, 20, edge):
                self.assertTrue(base.is_inside((x, y, p.floor_z + 1)))
        for lift in (0, 1, 3, 6):
            self.assertLess((base & moved(self.parts["Keeper frame"], Pos(0, 0, lift))).volume, 1e-6)
        start, end = p.support_spans[0]
        bore = y_cylinder(p.insert_bore_diameter / 2, end - start, start, p.adjuster_axis_z)
        for name in ("Base plate", "Guide frame", "Keeper frame"):
            self.assertLess((self.parts[name] & bore).volume, 1e-6)

    def test_adjuster_block_is_integrated_with_end_member(self):
        p = self.p
        base = self.fixed
        keeper = self.parts["Keeper frame"]
        start, end = p.support_spans[0]
        for y in (start + 0.1, (start + end) / 2, end - 0.1):
            self.assertTrue(base.is_inside((10, y, p.keeper_z - 0.1)))
            self.assertFalse(base.is_inside((10, y, p.keeper_z + 0.1)))
            self.assertTrue(keeper.is_inside((10, y, p.keeper_z + 0.1)))
            # A continuous roof over the insert bore, over the block's whole length.
            self.assertTrue(keeper.is_inside((0, y, p.adjuster_axis_z + p.insert_bore_diameter / 2 + 0.5)))
        self.assertAlmostEqual(base.bounding_box().max.Z, p.keeper_z)

    def test_lowered_bodies_and_rod_axes(self):
        p = self.p
        for name, sign in (("Driven plunger", 1), ("Spring plunger", -1)):
            part = self.parts[name]
            y = sign * (p.cassette_size / 2 + p.body_length / 2)
            self.assertAlmostEqual(part.bounding_box().min.Z - p.plate_thickness, 0.3)
            self.assertTrue(part.is_inside((0, y, p.plate_thickness + 0.4)))
            # Body extension must not lower the ears into their guide floors.
            self.assertFalse(part.is_inside((35, y, p.floor_z)))
            self.assertTrue(part.is_inside((35, y, p.floor_z + p.ear_lower_clearance + 0.1)))
        pocket_bottom = p.adjuster_axis_z - (p.magnet_width + p.magnet_pocket_clearance) / 2
        self.assertGreaterEqual(pocket_bottom - (p.plate_thickness + p.body_deck_clearance), 0.6)
        roof = self.parts["Keeper frame"].bounding_box().max.Z - (
            p.adjuster_axis_z + p.insert_bore_diameter / 2
        )
        self.assertAlmostEqual(roof, p.keeper_thickness)
        # The flange stands proud of the block face and clears the deck instead of notching it.
        self.assertAlmostEqual(
            p.adjuster_axis_z - p.insert_flange_diameter / 2,
            p.plate_thickness + p.adjuster_flange_deck_clearance,
        )
        self.assertGreaterEqual(p.adjuster_flange_deck_clearance, 0.3)
        self.assertAlmostEqual(p.spring_axis_z, p.adjuster_axis_z)
        start, end = p.support_spans[0]
        self.assertTrue(self.parts["Base plate"].is_inside((0, (start + end) / 2, p.plate_thickness - 0.1)))

    def test_magnet_pocket_roof_crown(self):
        p = self.p
        driven = self.parts["Driven plunger"]
        outer_y = p.cassette_size / 2 + p.body_length
        pocket_top = p.adjuster_axis_z + (p.magnet_width + p.magnet_pocket_clearance) / 2
        roof_y = outer_y - p.magnet_crown_length / 2
        # The roof over the pocket keeps its thickness; the crown does not reach past it ...
        self.assertTrue(driven.is_inside((0, roof_y, pocket_top + p.magnet_crown_roof - 0.05)))
        self.assertFalse(driven.is_inside((0, roof_y, pocket_top + p.magnet_crown_roof + 0.05)))
        # ... and is local: beside it and inboard of it the plunger top stays at body_top.
        beside_x = (p.magnet_length + p.magnet_pocket_clearance) / 2 + p.magnet_crown_wall + 0.5
        self.assertFalse(driven.is_inside((beside_x, roof_y, p.body_top + 0.05)))
        inboard_y = outer_y - p.magnet_crown_length - 0.5
        self.assertFalse(driven.is_inside((0, inboard_y, p.body_top + 0.05)))
        self.assertAlmostEqual(driven.bounding_box().max.Z, pocket_top + p.magnet_crown_roof)
        # Concave root fillets on both sides and the inboard end of the crown.
        r = p.magnet_crown_root_fillet
        half = (p.magnet_length + p.magnet_pocket_clearance) / 2 + p.magnet_crown_wall
        for sign in (-1, 1):
            self.assertTrue(driven.is_inside((sign * (half + 0.05), roof_y, p.body_top + 0.05)))
            self.assertFalse(driven.is_inside((sign * (half + r - 0.05), roof_y, p.body_top + r - 0.05)))
        inboard = outer_y - p.magnet_crown_length
        self.assertTrue(driven.is_inside((0, inboard - 0.05, p.body_top + 0.05)))
        self.assertFalse(driven.is_inside((0, inboard - r + 0.05, p.body_top + r - 0.05)))
        # The outboard face stays flat: no fillet where the crown meets the outer face.
        self.assertTrue(driven.is_inside((half - 0.05, outer_y - 0.05, p.body_top + 0.2)))

    def test_adjuster_crown_radial_wall(self):
        p = self.p
        keeper = self.parts["Keeper frame"]
        start, end = p.support_spans[0]
        inner = p.insert_bore_diameter / 2
        outer = inner + p.keeper_thickness
        for y in (start + 0.1, (start + end) / 2, end - 0.1):
            for angle in (30, 45, 60, 90, 120, 135, 150):
                a = radians(angle)
                for r in (inner + p.insert_entry_chamfer + 0.05, outer - 0.05):
                    self.assertTrue(keeper.is_inside((r * cos(a), y, p.adjuster_axis_z + r * sin(a))))
            self.assertFalse(keeper.is_inside((0, y, p.adjuster_axis_z + outer + 0.05)))
        # Flat regions retain their original 3 mm section.
        self.assertFalse(keeper.is_inside((20, (start + end) / 2, p.keeper_z + p.keeper_thickness + 0.05)))

    def test_spring_cup_boss_backs_the_coil_end(self):
        p = self.p
        keeper = self.parts["Keeper frame"]
        coil_top = p.spring_axis_z + p.spring_outer_diameter / 2
        # Behind the seat face, over the whole end member, the boss is as tall as the cup roof ...
        for y in (p.plate_ymin + 0.1, p.spring_seat_y - 0.1):
            self.assertTrue(keeper.is_inside((0, y, p.spring_cup_top - 0.1)))
            self.assertFalse(keeper.is_inside((0, y, p.spring_cup_top + 0.1)))
            # ... so the whole coil end face, up to its top, has wall behind it.
            self.assertGreater(p.spring_cup_top - 0.1, coil_top)
        # Concave fillets blend the boss sides into the end member top.
        r = p.spring_boss_root_fillet
        half = p.spring_cup_bore / 2 + p.spring_cup_side_wall
        top = p.keeper_z + p.keeper_thickness
        y = p.spring_seat_y - p.rear_wall_thickness / 2
        for sign in (-1, 1):
            self.assertTrue(keeper.is_inside((sign * (half + 0.1), y, top + 0.1)))
            self.assertFalse(keeper.is_inside((sign * (half + r - 0.05), y, top + r - 0.05)))
            self.assertFalse(keeper.is_inside((sign * (half + r + 0.1), y, top + 0.05)))
        # It is local: the end member beside the boss keeps the nominal section.
        side_x = (p.spring_cup_bore + 2 * p.spring_cup_side_wall) / 2 + 1.0
        self.assertFalse(
            keeper.is_inside((side_x, p.spring_seat_y - 0.1, p.keeper_z + p.keeper_thickness + 0.1))
        )

    def test_spring_end_wall_is_solid(self):
        p = self.p
        fixed = self.fixed + self.parts["Keeper frame"]
        # No rod penetration: the end wall is solid on the spring axis.
        for y in (p.plate_ymin + 0.1, (p.plate_ymin + p.spring_seat_y) / 2, p.spring_seat_y - 0.1):
            self.assertTrue(fixed.is_inside((0, y, p.spring_axis_z)))

    @slow
    def test_spring_cups_locate_coil_ends(self):
        p = self.p
        r = p.spring_cup_bore / 2
        for name, seat_y, sign in (
            ("fixed", p.spring_seat_y, 1),
            ("Spring plunger", -p.cassette_size / 2 - p.body_length, -1),
        ):
            part = (self.fixed + self.parts["Keeper frame"]) if name == "fixed" else self.parts[name]
            y = seat_y + sign * p.spring_cup_depth / 2
            # Walls at both sides and over the coil; open to the deck below it.
            for x, z in (
                (r + 0.3, p.spring_axis_z),
                (-r - 0.3, p.spring_axis_z),
                (0, p.spring_axis_z + r + 0.3),
            ):
                self.assertTrue(part.is_inside((x, y, z)), (name, x, z))
            low = p.spring_axis_z - p.spring_outer_diameter / 2 + 0.1
            for x, z in ((0, p.spring_axis_z), (0, low), (r - 0.3, p.spring_axis_z)):
                self.assertFalse(part.is_inside((x, y, z)), (name, x, z))
        # Spring envelope clears every printed part over working travel and the loading pose.
        for travel, retract in ((-5, 0), (0, 0), (5, 0), (0, 6)):
            objects = children_by_label(build_carriage(travel=travel, retract=retract, include_hardware=True))
            # The displayed helix lies inside its cylindrical envelope; check the envelope.
            length = p.spring_fiducial_length + travel - retract
            spring = along_y((0, p.spring_seat_y, p.spring_axis_z)) * Cylinder(
                p.spring_outer_diameter / 2, length, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )
            for part in self.parts:
                self.assertLess(overlap_volume(spring, objects[part]), 1e-6, (travel, retract, part))

    def test_plunger_underside_edge_breaks(self):
        p = self.p
        bottom = p.plate_thickness + p.body_deck_clearance
        c = p.body_bottom_chamfer
        y0, y1 = p.cassette_size / 2, p.cassette_size / 2 + p.body_length
        driven = self.parts["Driven plunger"]
        # Leading and trailing bottom edges and both side edges of the driven plunger are chamfered.
        for y, toward in ((y0, 1), (y1, -1)):
            self.assertFalse(driven.is_inside((0, y + toward * 0.1, bottom + 0.1)))
            self.assertTrue(driven.is_inside((0, y + toward * c * 0.75, bottom + c * 0.75)))
        for sign in (-1, 1):
            xe = sign * p.body_width / 2
            self.assertFalse(driven.is_inside((xe - sign * 0.1, (y0 + y1) / 2, bottom + 0.1)))
            self.assertTrue(driven.is_inside((xe - sign * c * 0.75, (y0 + y1) / 2, bottom + c * 0.75)))
        # The spring plunger (mirrored) is chamfered the same way, and round its cup's feet and pocket opening.
        spring = self.parts["Spring plunger"]
        self.assertFalse(spring.is_inside((15, -y1 + 0.1, bottom + 0.1)))
        self.assertTrue(spring.is_inside((15, -y1 + c * 0.75, bottom + c * 0.75)))
        self.assertFalse(spring.is_inside((15, -y0 - 0.1, bottom + 0.1)))
        bore_r = p.spring_cup_bore / 2
        foot_x0, foot_x1 = bore_r, bore_r + p.spring_cup_side_wall
        foot_mid = (foot_x0 + foot_x1) / 2
        y_mid = -(y1 + p.spring_cup_depth / 2)
        y_end = -(y1 + p.spring_cup_depth)
        self.assertFalse(spring.is_inside((foot_x1 - 0.1, y_mid, bottom + 0.1)))  # Foot's outer edge.
        self.assertFalse(spring.is_inside((foot_x0 + 0.1, y_mid, bottom + 0.1)))  # Pocket opening's edge.
        self.assertFalse(spring.is_inside((foot_mid, y_end + 0.1, bottom + 0.1)))  # Cup's outboard end.
        self.assertTrue(spring.is_inside((foot_mid, y_mid, bottom + 0.01)))  # Flat left on the foot.
        self.assertGreater(c, 0)

    def test_guide_ear_edge_breaks(self):
        p = self.p
        part = self.parts["Driven plunger"]
        ear_bottom = p.floor_z + p.ear_lower_clearance
        ear_top = ear_bottom + p.ear_thickness
        y0, y1 = p.cassette_size / 2, p.cassette_size / 2 + p.body_length
        ymid = (y0 + y1) / 2
        c, f = p.ear_bottom_chamfer, p.ear_top_fillet
        for sign in (-1, 1):
            xo = sign * p.ear_outer_x
            # Bottom outer edge chamfered: nothing at the corner, material beyond the chamfer plane.
            self.assertFalse(part.is_inside((xo - sign * 0.1, ymid, ear_bottom + 0.1)))
            self.assertTrue(part.is_inside((xo - sign * (c * 0.75), ymid, ear_bottom + c * 0.75)))
            # Top outer edge filleted.
            self.assertFalse(part.is_inside((xo - sign * 0.05, ymid, ear_top - 0.05)))
            self.assertTrue(part.is_inside((xo - sign * f * 0.5, ymid, ear_top - f * 0.5)))
            # Both ends, top and bottom, along the ear.
            xm = xo - sign * 3.0
            for y, toward in ((y0, 1), (y1, -1)):
                self.assertFalse(part.is_inside((xm, y + toward * 0.1, ear_bottom + 0.1)))
                self.assertTrue(part.is_inside((xm, y + toward * c * 0.75, ear_bottom + c * 0.75)))
                self.assertFalse(part.is_inside((xm, y + toward * 0.05, ear_top - 0.05)))
                self.assertTrue(part.is_inside((xm, y + toward * f * 0.5, ear_top - f * 0.5)))
            # The land between the breaks is flat and full thickness.
            self.assertTrue(part.is_inside((xm, ymid, ear_bottom + 0.01)))
            self.assertTrue(part.is_inside((xm, ymid, ear_top - 0.01)))
        self.assertGreater(p.ear_corner_fillet, max(c, f))

    def test_guide_ear_root_fillets(self):
        # Concave stress-relief fillets, top and underside, where each ear leaves the body wall.
        p = self.p
        ear_bottom = p.floor_z + p.ear_lower_clearance
        ear_top = ear_bottom + p.ear_thickness
        ymid = p.cassette_size / 2 + p.body_length / 2
        r = p.ear_root_fillet
        for name in ("Driven plunger", "Spring plunger"):
            part = self.parts[name]
            y = ymid if name == "Driven plunger" else -ymid
            for sign in (-1, 1):
                wall = sign * p.body_width / 2
                for z_face, direction in ((ear_top, 1), (ear_bottom, -1)):
                    self.assertTrue(part.is_inside((wall + sign * 0.05, y, z_face + direction * 0.05)))
                    self.assertFalse(
                        part.is_inside((wall + sign * (r - 0.05), y, z_face + direction * (r - 0.05)))
                    )
                    # Clear of the keeper opening edge and the track floor.
                    self.assertFalse(part.is_inside((wall + sign * (r + 0.1), y, z_face + direction * 0.3)))
        self.assertLess(p.body_width / 2 + p.ear_root_fillet, p.track_inner_x)

    def test_thumb_tab(self):
        p = self.p
        part = self.parts["Spring plunger"]
        y = -p.cassette_size / 2 - p.body_length + p.thumb_tab_thickness / 2
        self.assertTrue(part.is_inside((0, y, p.body_top + p.thumb_tab_height - 0.1)))
        self.assertFalse(part.is_inside((0, y, p.body_top + p.thumb_tab_height + 0.1)))
        self.assertFalse(part.is_inside((0, y + p.thumb_tab_thickness, p.body_top + 0.1)))
        self.assertAlmostEqual(part.bounding_box().max.Z, p.body_top + p.thumb_tab_height)
        outer = -p.cassette_size / 2 - p.body_length
        top = p.body_top + p.thumb_tab_height
        c = p.thumb_tab_chamfer
        inner = outer + p.thumb_tab_thickness
        half = p.thumb_tab_width / 2
        # Spring-facing face keeps square edges: top edge and both vertical corners.
        self.assertTrue(part.is_inside((0, outer + c / 3, top - c / 3)))
        self.assertTrue(part.is_inside((half - c / 3, outer + c / 3, top - 2)))
        # Side top edges and thumb-side vertical corners are chamfered.
        self.assertFalse(part.is_inside((half - c / 3, (outer + inner) / 2, top - c / 3)))
        self.assertFalse(part.is_inside((half - c / 3, inner - c / 3, top - 2)))
        self.assertTrue(part.is_inside((half - c * 1.5, (outer + inner) / 2, top - c * 1.5)))
        # Concave root fillets on the thumb-side face and both ends where the tab rises from the plunger top;
        # none on the spring-facing outer face.
        rf = p.thumb_tab_root_fillet
        z = p.body_top
        mid = (outer + inner) / 2
        self.assertTrue(part.is_inside((0, inner + 0.05, z + 0.05)))
        self.assertFalse(part.is_inside((0, inner + rf - 0.05, z + rf - 0.05)))
        self.assertFalse(part.is_inside((0, inner + rf + 0.1, z + 0.05)))
        for sign in (-1, 1):
            self.assertTrue(part.is_inside((sign * (half + 0.05), mid, z + 0.05)))
            self.assertFalse(part.is_inside((sign * (half + rf - 0.05), mid, z + rf - 0.05)))
        self.assertFalse(part.is_inside((0, outer - 0.05, z + 0.05)))
        # Grip bead stands proud of the inner (thumb-side) face at the top, flush with the tab top.
        r = p.thumb_tab_bead_radius
        self.assertTrue(part.is_inside((0, inner + r - 0.1, top - r)))
        self.assertFalse(part.is_inside((0, inner + r + 0.1, top - r)))
        self.assertFalse(part.is_inside((0, inner + 0.1, top - 2 * r - 0.3)))

    def test_spigot_fits_ring_and_seats_on_shoulder(self):
        p = self.p
        base = self.parts["Base plate"]
        self.assertAlmostEqual(base.bounding_box().min.Z, -p.spigot_length, places=6)
        self.assertAlmostEqual(p.spigot_length, p.ring_gap + 10.16)
        r = p.spigot_diameter / 2
        # Spigot OD through the ring, shoulder in front of it, open Ø24 mm light path throughout.
        for z in (-p.spigot_length + 0.1, -p.ring_gap - 0.1):
            self.assertTrue(base.is_inside((r - 0.1, 0, z)))
            self.assertFalse(base.is_inside((r + 0.1, 0, z)))
        for z in (-p.ring_gap + 0.1, -0.1):
            self.assertTrue(base.is_inside((p.spigot_shoulder_diameter / 2 - 0.1, 0, z)))
            self.assertFalse(base.is_inside((p.spigot_shoulder_diameter / 2 + 0.1, 0, z)))
        for z in (-p.spigot_length + 0.1, -p.ring_gap, p.plate_thickness - 0.1):
            self.assertTrue(base.is_inside((p.aperture_diameter / 2 + 0.1, 0, z)))
            self.assertFalse(base.is_inside((p.aperture_diameter / 2 - 0.1, 0, z)))
        support = self.support
        ring = support["SM1RC M ring"]
        rb = ring.bounding_box()
        self.assertAlmostEqual(rb.max.Z, -p.ring_gap, places=4)
        self.assertAlmostEqual(rb.min.Z, -p.spigot_length, places=4)
        self.assertLess((base & ring).volume, 1e-6)
        # The ring face touches the shoulder annulus.
        self.assertGreater((base & moved(ring, Pos(0, 0, 0.1))).volume, 1)
        for x, y in p.datum_points:
            pin = Pos(x, y, -1) * Cylinder(p.datum_pin_shank / 2, p.plate_thickness + 1, align=ON_FLOOR)
            self.assertLess((base & pin).volume, 1e-6)

    @slow
    def test_post_and_rail_shoe_clearance(self):
        p = self.p
        # At nominal zero the plate reaches below the shoe top, so the shoe end sets the ring gap.
        self.assertGreater(-p.plate_ymin, p.optical_height - 20.0)
        support = self.support
        fixed = list(self.parts.values())
        for rotation in (-120, -90, -45, 0, 45, 90, 120):
            for name in ("TR50 M post", "Rail shoe", "Shoe clamp screw", "Shoe clamp nut"):
                solid = moved(support[name], Rot(Z=-rotation))
                # Shifting the support forward by the minimum clearance must still leave it clear.
                shifted = moved(solid, Pos(0, 0, p.post_clearance))
                for part in fixed:
                    self.assertLess(overlap_volume(part, shifted), 1e-6, (rotation, name))

    def test_sandwich_interface(self):
        p = self.p
        base = self.parts["Base plate"]
        frame = self.parts["Guide frame"]
        self.assertAlmostEqual(base.bounding_box().max.Z, p.plate_thickness, places=6)
        self.assertAlmostEqual(frame.bounding_box().min.Z, p.plate_thickness, places=6)
        self.assertLess((base & frame).volume, 1e-6)
        self.assertGreater((base & moved(frame, Pos(0, 0, -0.1))).volume, 1)
        for lift in (0.2, 1, 5):
            self.assertLess((base & moved(frame, Pos(0, 0, lift))).volume, 1e-6)

    def test_insert_manufacturing_dimensions_and_adjuster_reach(self):
        p = self.p
        self.assertAlmostEqual(p.insert_body_diameter, 7.9502)
        self.assertAlmostEqual(p.insert_drill_diameter, 7.9502)
        self.assertAlmostEqual(p.insert_bore_diameter, p.insert_body_diameter)
        self.assertAlmostEqual(p.insert_body_length, 7.5692)
        self.assertAlmostEqual(p.insert_min_material_thickness, 7.5692)
        self.assertGreater(p.insert_flange_diameter, p.insert_bore_diameter + 2 * p.insert_entry_chamfer)
        self.assertGreaterEqual(
            p.adjuster_support_length - p.insert_entry_chamfer, p.insert_min_material_thickness
        )
        self.assertAlmostEqual(p.adjuster_screw_length - p.insert_overall_length, 17.4498)
        self.assertAlmostEqual(p.adjuster_pitch, 0.3175)
        # The flange is on the cassette-side (inner) face of the adjuster block, so the outboard adjuster
        # reaction bears it against the block; the body runs outboard and stays inside the block.
        flange_face = p.insert_flange_face
        self.assertAlmostEqual(flange_face, p.plate_ymax - p.adjuster_support_length)
        body_start = flange_face
        insert_inner = flange_face
        insert_outer = flange_face + p.insert_overall_length
        self.assertLessEqual(insert_outer + p.insert_entry_chamfer, p.plate_ymax)
        # Check the actual screw envelope and engagement at both travel limits.
        for travel in (-5, 0, 5):
            tip = p.magnet_contact_y + travel
            extension = insert_inner - tip
            self.assertGreater(extension, 0)
            self.assertLessEqual(extension, 15.5 + 1e-6)
            self.assertGreater(tip + p.adjuster_screw_length, insert_outer)
            screw = y_cylinder(6.35 / 2, p.adjuster_screw_length, tip, p.adjuster_axis_z)
            for name in ("Base plate", "Guide frame", "Keeper frame"):
                self.assertLess((self.parts[name] & screw).volume, 1e-6)
        # The flange bears flat on the block's inner face: it stands proud of it, intersecting nothing,
        # and the block material directly outboard (between bore and flange edge) takes the reaction.
        flange = y_cylinder(
            p.insert_flange_diameter / 2,
            p.insert_flange_thickness,
            flange_face - p.insert_flange_thickness,
            p.adjuster_axis_z,
        )
        for name in ("Base plate", "Guide frame", "Keeper frame"):
            self.assertLess((self.parts[name] & flange).volume, 1e-6)
        land_x = (p.insert_bore_diameter + p.insert_flange_diameter) / 4
        z = p.adjuster_axis_z
        self.assertTrue(self.fixed.is_inside((land_x, flange_face + 0.1, z)))
        self.assertFalse(self.fixed.is_inside((land_x, flange_face - 0.1, z)))
        # The insert body ends well inside the block's outer face.
        self.assertGreaterEqual(p.plate_ymax - (body_start + p.insert_body_length), 1.5)
        # Nominal manufacturer barrel envelope clears the CAD bore; printed fit must be finished.
        bore = y_cylinder(
            p.insert_bore_diameter / 2,
            p.adjuster_support_length,
            flange_face,
            p.adjuster_axis_z,
        )
        self.assertLess((self.fixed & bore).volume, 1e-6)
        barrel = y_cylinder(p.insert_body_diameter / 2, p.insert_body_length, body_start, p.adjuster_axis_z)
        for name in ("Base plate", "Guide frame", "Keeper frame"):
            self.assertLess((self.parts[name] & barrel).volume, 1e-6)
        self.assertAlmostEqual(p.adjuster_axis_z, 8.7704, places=3)

    def test_stack_retaining_hardware(self):
        # One M3 x 12 screw and one captive nut at each of the eight keeper fastener positions.
        p = self.p
        parts = self.hardware
        self.assertEqual(len(p.fasteners), 8)
        for i, (x, y) in enumerate(p.fasteners, start=1):
            screw = parts[f"Keeper screw {i}"].bounding_box()
            nut = parts[f"Keeper nut {i}"].bounding_box()
            for box in (screw, nut):
                self.assertAlmostEqual((box.min.X + box.max.X) / 2, x, places=3)
                self.assertAlmostEqual((box.min.Y + box.max.Y) / 2, y, places=3)
            # The head bears on its recess in the keeper; the shank is 12 mm long under it.
            self.assertAlmostEqual(screw.max.Z - screw.min.Z, 12.0 + 3.0, places=3)
            self.assertAlmostEqual(screw.max.Z - 3.0, p.keeper_screw_seat_z, places=3)
            # The nut sits against the roof of its pocket, which opens from the plate back.
            self.assertAlmostEqual(nut.max.Z, p.nut_pocket_depth, places=3)
            self.assertGreaterEqual(nut.min.Z, 0.0)
            # Slight nominal projection of the screw beyond the nut.
            self.assertLess(screw.min.Z, nut.min.Z)
            self.assertLess(nut.min.Z - screw.min.Z, 1.0)
        self.assertNotIn("Keeper screw 9", parts)
        self.assertNotIn("Keeper screw 1", self.parts)

    def test_datum_pins_trimmed_flush_with_plate_back(self):
        # Three brads, head up on the datum face, with the shank flush-cut at the plate back.
        p = self.p
        parts = self.hardware
        self.assertEqual(len(p.datum_points), 3)
        for i, (x, y) in enumerate(p.datum_points, start=1):
            box = parts[f"Datum pin {i}"].bounding_box()
            self.assertAlmostEqual((box.min.X + box.max.X) / 2, x, places=3)
            self.assertAlmostEqual((box.min.Y + box.max.Y) / 2, y, places=3)
            self.assertAlmostEqual(box.min.Z, 0.0, places=3)
            # The head stands on the datum face and its dome stays below the cassette rear face.
            self.assertGreater(box.max.Z, p.plate_thickness)
            self.assertLess(box.max.Z, p.plate_thickness + p.datum_projection + 1e-6)
        self.assertNotIn("Datum pin 1", self.parts)

    def test_keeper_side_members_resist_ear_lift(self):
        p = self.p
        keeper = self.parts["Keeper frame"]
        x = (p.keeper_opening_width / 2 + p.plate_width / 2) / 2
        top = p.keeper_z + p.keeper_side_thickness
        for y in (-40, 0, 40):
            self.assertTrue(keeper.is_inside((x, y, top - 0.1)))
            self.assertFalse(keeper.is_inside((x, y, top + 0.1)))
        # End members keep the nominal 3 mm section away from the crown and spring cup.
        self.assertFalse(
            keeper.is_inside(
                (20, (p.plate_ymin + p.spring_seat_y) / 2, p.keeper_z + p.keeper_thickness + 0.1)
            )
        )
        # Screw heads still seat at the original stack height, inside a deeper counterbore.
        for fx, fy in p.fasteners:
            self.assertFalse(keeper.is_inside((fx + 2.5, fy, p.keeper_screw_seat_z + 0.1)))
            self.assertTrue(keeper.is_inside((fx + 2.5, fy, p.keeper_screw_seat_z - 0.1)))
        # First-order estimate (spans simply supported between screws) at the §8.4 max-compression wedge load
        # split over two ears: inside the ear play over working travel and the loading pose.
        play = p.guide_axial_clearance - p.ear_lower_clearance
        for travel, retract in ((-5, 0), (0, 0), (5, 0), (0, 6)):
            self.assertLess(p.keeper_side_lift(18.7 / 2, travel, retract), play / 2)

    def test_thicker_fallback_keeper(self):
        p = CarriageParameters(keeper_side_thickness=5.0)
        keeper = children_by_label(build_carriage(p))["Keeper frame"]
        self.assertTrue(keeper.is_valid)
        x = (p.keeper_opening_width / 2 + p.plate_width / 2) / 2
        self.assertTrue(keeper.is_inside((x, 0, p.keeper_z + 4.9)))
        # Deeper counterbores keep the same screw-head seat, so the M3 x 12 stack is unchanged.
        for fx, fy in p.fasteners:
            self.assertFalse(keeper.is_inside((fx + 2.5, fy, p.keeper_screw_seat_z + 0.1)))
            self.assertTrue(keeper.is_inside((fx + 2.5, fy, p.keeper_screw_seat_z - 0.1)))
        self.assertAlmostEqual(p.keeper_screw_seat_z, self.p.keeper_screw_seat_z)

    def test_side_screws_beside_ear_travel(self):
        p = self.p
        self.assertEqual(len(p.fasteners), 8)
        for x, y in p.side_fasteners:
            self.assertAlmostEqual(abs(y), p.ear_center_y)
            # Clearance hole stays outboard of the guide track wall; the lug carries the captive nut.
            self.assertGreaterEqual(abs(x) - p.screw_clearance / 2, p.track_outer_x + 1.0)
            sign = 1 if x > 0 else -1
            for name in ("Base plate", "Guide frame", "Keeper frame"):
                part = self.parts[name]
                z = {"Base plate": 1.0, "Guide frame": p.floor_z, "Keeper frame": p.keeper_z + 1}[name]
                self.assertTrue(part.is_inside((x + sign * (p.side_lug_radius - 0.5), y, z)), name)
                self.assertFalse(part.is_inside((x, y, z)), name)

    def test_rotation_clears_rail(self):
        p = self.p
        # Printed parts stay inside the envelope, which sits post_clearance above the rail top.
        for name, part in self.parts.items():
            for v in part.vertices():
                x, y = v.X, v.Y
                self.assertLessEqual((x * x + y * y) ** 0.5, p.rotation_envelope_radius + 1e-6, name)
        self.assertAlmostEqual(p.optical_height - p.rotation_envelope_radius, p.post_clearance)
        # Sweep the assembled carriage, with its adjuster, against the 2020 rail (20 mm wide below the post).
        rail = Pos(0, 0, -20) * Box(20, 400, 20, align=ON_FLOOR)
        for rotation in range(-150, 151, 5):
            swept = support_location(p, rotation) * rail
            # Parts whose bounding boxes are apart from the rail's cannot overlap it.
            for part, _ in near_pairs(self.hardware.values(), [swept]):
                self.assertLess((part & swept).volume, 1e-6, (rotation, part.label))

    def test_track_end_stops_and_keeper_screws(self):
        p = self.p
        spring_stop, driven_stop = p.ear_stops_y
        x = (p.track_inner_x + p.track_outer_x) / 2
        for y in (spring_stop - 0.1, driven_stop + 0.1):
            self.assertTrue(self.fixed.is_inside((x, y, p.floor_z + 1)))
        for y in (spring_stop + 0.1, driven_stop - 0.1):
            self.assertFalse(self.fixed.is_inside((x, y, p.floor_z + 1)))
        # Outermost ear positions stop 1 mm short of the fill.
        for name, shift in (
            ("Spring plunger", -p.loading_retraction),
            ("Driven plunger", p.working_half_travel),
        ):
            shifted = moved(self.parts[name], Pos(0, shift, 0))
            self.assertLess((shifted & self.fixed).volume, 1e-6)
            sign = 1 if shift > 0 else -1
            past = moved(shifted, Pos(0, sign * (p.ear_stop_gap + 0.1), 0))
            self.assertGreater((past & self.fixed).volume, 0.1)
        for _fx, fy in p.fasteners:
            self.assertLess(abs(fy), abs(spring_stop) + p.fastener_stop_margin + 1e-6)

    @slow
    def test_adjuster_hardware_seats_and_clears(self):
        for travel in (-5, 0, 5):
            solids = children_by_label(build_carriage(travel=travel, include_hardware=True))
            printed = [solids[n] for n in self.parts]
            magnet = solids["Magnet pad"]
            # The ball tip touches the pad's outboard face; the pad sits in the driven-plunger pocket.
            self.assertLess((solids["FAS100"] & magnet).volume, 1e-6)
            self.assertLess(solids["FAS100"].distance_to(magnet), 1e-3)
            for name in ("FAS100", "98625A950 bushing", "Magnet pad"):
                for part in printed:
                    self.assertLess(overlap_volume(solids[name], part), 1e-3, (travel, name))

    def test_print_layout_orients_and_spaces_the_printed_parts(self):
        p = self.p
        layout = build_print_layout(p)
        self.assertEqual(set(layout), {"base_plate", "guide_frame", "keeper_frame", "plungers"})
        base = layout["base_plate"].bounding_box()
        # Deck down on the bed, spigot up: the plate's front face is on z=0 and the spigot rises above it.
        self.assertAlmostEqual(base.min.Z, 0.0, places=4)
        self.assertAlmostEqual(base.max.Z, p.plate_thickness + p.spigot_length, places=4)
        # The guide frame and keeper keep assembly coordinates.
        for name, part in (("guide_frame", "Guide frame"), ("keeper_frame", "Keeper frame")):
            self.assertAlmostEqual(
                layout[name].bounding_box().min.Z, self.parts[part].bounding_box().min.Z, places=4
            )
        plungers = layout["plungers"]
        self.assertEqual(len(plungers.solids()), 2)
        first, second = sorted((s.bounding_box() for s in plungers.solids()), key=lambda b: b.min.Y)
        self.assertAlmostEqual(first.min.Z, 0.0, places=4)
        self.assertAlmostEqual(second.min.Z, 0.0, places=4)
        self.assertAlmostEqual(second.min.Y - first.max.Y, 5.0, places=4)
        self.assertAlmostEqual(first.center().X, 0.0, places=4)
        self.assertAlmostEqual(second.center().X, 0.0, places=4)

    def test_unsupported_poses_rejected(self):
        for args in ({"travel": 5.1}, {"retract": 6.1}, {"travel": 1, "retract": 1}):
            with self.assertRaises(ValueError):
                build_carriage(**args)


if __name__ == "__main__":
    unittest.main()

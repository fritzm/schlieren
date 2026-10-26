"""LED-module drilling fixture: bushing plate, cap nest, and heatsink nest invariants (§6.8)."""

import math
import unittest
from dataclasses import replace

from build123d import GeomType, Pos, Rot

from schlieren.cad import children_by_label, intersect, moved
from schlieren.parts.led_drill_fixture import (
    BUSHING_LABEL,
    BUSHINGS,
    CAP,
    CLAMP_SCREW_LABEL,
    COUPON_OVERSIZES,
    EAR_ANGLES,
    EAR_BOLT_LABEL,
    EAR_NUT_LABEL,
    EAR_WASHER_LABEL,
    HEATSINK,
    HEATSINK_KINDS,
    INSERT_LABEL,
    NEST_KINDS,
    PAD_LABEL,
    PLATE_SCREW_LABEL,
    DrillFixtureParameters,
    build_bore_coupon,
    build_bushing_plate,
    build_fixture_assembly,
    build_nest,
)
from schlieren.testing import shared
from schlieren.vendor_cad import (
    MCMASTER_92356A589_LENGTH,
    MCMASTER_92356A589_NECK_LENGTH,
    MCMASTER_96659A134_THICKNESS,
)

EPS = 1e-6


def cylinder_radii(shape):
    return sorted(round(f.radius, 4) for f in shape.faces() if f.geom_type == GeomType.CYLINDER and f.radius)


class DrillFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = DrillFixtureParameters()
        cls.plate = build_bushing_plate(cls.p)

    @shared
    def nests(cls):
        return {kind: build_nest(cls.p, kind) for kind in NEST_KINDS}

    @shared
    def assemblies(cls):
        return {kind: build_fixture_assembly(cls.p, kind, parts=False) for kind in NEST_KINDS}

    def seated_plate(self, kind, rotation=0.0):
        return moved(self.plate, Pos(0, 0, self.p.nest_top(kind)) * Rot(Z=rotation))

    def test_parameters_validate(self):
        self.p.validate()

    def test_bushing_bores_are_the_cap_drill_diameters(self):
        for kind, bushing in BUSHINGS.items():
            self.assertAlmostEqual(bushing.bore, self.p.layout.cap_hole_diameter(kind), msg=kind)
            self.assertLess(bushing.bore, bushing.outer_diameter)

    def test_plate_is_one_bushing_thick(self):
        box = self.plate.bounding_box()
        self.assertAlmostEqual(box.max.Z, BUSHINGS["lead"].length)
        self.assertAlmostEqual(box.min.Z, -self.p.ring_height)

    def test_plate_bores_sit_on_the_layout_and_take_the_bushings(self):
        """Each bore is empty at its layout coordinates and exactly the bushing's outside diameter wide."""
        mid = BUSHINGS["lead"].length / 2
        for hole in self.p.layout.holes():
            radius = (BUSHINGS[hole.kind].outer_diameter + self.p.bushing_bore_oversize) / 2
            self.assertFalse(self.plate.is_inside((hole.x, hole.y, mid)), hole.name)
            for angle in (0, 90, 180, 270):
                dx, dy = math.cos(math.radians(angle)), math.sin(math.radians(angle))
                inside = (hole.x + dx * (radius - 0.02), hole.y + dy * (radius - 0.02), mid)
                outside = (hole.x + dx * (radius + 0.02), hole.y + dy * (radius + 0.02), mid)
                self.assertFalse(self.plate.is_inside(inside), hole.name)
                self.assertTrue(self.plate.is_inside(outside), hole.name)

    def test_plate_web_between_bores(self):
        self.assertGreaterEqual(self.p.web(), self.p.min_web)

    def test_heatsink_is_drilled_through_m3_and_lead_only(self):
        kinds = sorted(h.kind for h in self.p.holes(HEATSINK))
        self.assertEqual(kinds, ["lead", "lead", "m3", "m3", "m3"])
        self.assertTrue(set(HEATSINK_KINDS).issuperset(kinds))
        self.assertEqual(len(self.p.holes(CAP)), 7)

    def test_nest_top_is_the_part_face_plus_the_standoff(self):
        for kind in NEST_KINDS:
            top = self.nests[kind].bounding_box().max.Z
            self.assertAlmostEqual(top, self.p.part_height(kind) + self.p.standoff, places=6, msg=kind)

    def test_plate_seats_without_interference(self):
        """Ring in the plate bore and tab in the key slot, with no overlap with the nest."""
        for kind in NEST_KINDS:
            self.assertAlmostEqual(intersect(self.nests[kind], self.seated_plate(kind)).volume, 0.0, places=6)

    def test_key_allows_only_one_orientation(self):
        """The plate turned by a quarter turn cannot seat: its tab meets the bore wall."""
        for kind in NEST_KINDS:
            for turn in (90, 180, 270):
                overlap = intersect(self.nests[kind], self.seated_plate(kind, turn)).volume
                self.assertGreater(overlap, 1.0, f"{kind} {turn}")

    def test_ring_and_tab_clearances(self):
        p = self.p
        self.assertAlmostEqual(p.plate_bore_diameter - p.ring_outer_diameter, p.slip_clearance_diametral)
        self.assertGreaterEqual(p.ring_inner_diameter, p.light.heatsink_diameter + 0.5)

    def test_ring_stops_short_of_the_cap_counterbore_floor(self):
        p = self.p
        ring_bottom = p.nest_top(CAP) - p.ring_height
        self.assertAlmostEqual(ring_bottom - p.bore_floor(CAP), p.ring_relief)

    def test_cap_pocket_and_support_ring(self):
        p = self.p
        self.assertAlmostEqual(p.pocket_diameter - p.light.cap_flange_diameter, p.slip_clearance_diametral)
        nest = self.nests[CAP]
        flange_edge = p.light.cap_flange_diameter / 2
        self.assertTrue(nest.is_inside((flange_edge - 1.0, 0, -1.0)))  # Support ring under the flange rim.
        self.assertFalse(nest.is_inside((0, 0, -1.0)))  # Relief window under the hole pattern.
        self.assertFalse(nest.is_inside((p.hole_reach(), 0, -1.0)))
        self.assertFalse(nest.is_inside((0, 0, 1.0)))  # The pocket itself is open.

    def test_cap_clamp_screw_reaches_the_pocket_at_the_flange(self):
        """From the notch face, a 12 mm M3 screw passes the wall and protrudes into the pocket."""
        p = self.p
        nest = self.nests[CAP]
        z = p.flange_thickness / 2
        face = -p.body_side / 2 + p.clamp_notch_depth
        self.assertFalse(nest.is_inside((0, face + 0.1, z)))  # Notch face.
        self.assertFalse(nest.is_inside((0, face + 5.0, z)))  # Insert hole.
        self.assertFalse(
            nest.is_inside((0, -p.pocket_diameter / 2 - 0.5, z))
        )  # Clearance hole to the pocket.
        self.assertTrue(nest.is_inside((2.5, face + 3.0, z)))  # Beside the hole.
        wall = p.pocket_diameter / 2 - abs(
            face
        )  # Face to pocket wall, negative: the wall is nearer the axis.
        protrusion = 12.0 + wall
        self.assertGreater(protrusion, 3.0)
        self.assertLess(p.clamp_notch_top, p.bore_floor(CAP))  # The notch leaves the counterbore wall whole.

    def test_rib_fits_the_pin_channels(self):
        p = self.p
        self.assertAlmostEqual(p.channel_width - p.rib_width, p.rib_clearance_width)
        self.assertAlmostEqual(p.rib_clears_pins(), p.rib_clearance_width / 2, places=6)

    def test_heatsink_windows_print_without_supports(self):
        """Vertical sides, 45° corners, and a flat top no wider than the setting: no wide bridge anywhere."""
        p = self.p
        nest = self.nests[HEATSINK]
        top = p.window_top_z(HEATSINK)
        c, half = p.window_chamfer, p.window_width / 2

        def at(axis, across, z):
            wall = p.body_side / 2 - 1.0
            return (wall, across, z) if axis == "x" else (across, wall, z)

        for axis in ("x", "y"):
            self.assertFalse(nest.is_inside(at(axis, 0.0, top - 0.5)))  # Open under the flat top.
            self.assertFalse(
                nest.is_inside(at(axis, half - 0.5, top - c - 0.5))
            )  # Open on the vertical side.
            self.assertTrue(nest.is_inside(at(axis, half - 0.5, top - 0.5)))  # Solid in the cut-off corner.
            self.assertTrue(nest.is_inside(at(axis, half + 0.5, top - c - 0.5)))  # Solid beside the window.
            self.assertTrue(nest.is_inside(at(axis, 0.0, top + 0.5)))  # Solid above the window.
        self.assertAlmostEqual(c, (p.window_width - p.window_flat_top) / 2)
        self.assertLessEqual(p.window_flat_top, 6.0)

    def test_wall_behind_each_ear_is_whole_to_the_top_of_the_fillet(self):
        """The ear faces' windows start above the root fillet; the other faces' windows start at the lip."""
        p = self.p
        nest = self.nests[HEATSINK]
        wall = p.body_side / 2 - 1.0  # Inside the face wall.
        fillet_top = p.ear_top + p.ear_root_fillet_radius
        for sign in (1, -1):
            for across in (0.0, p.window_width / 2 - 1.0):
                self.assertTrue(nest.is_inside((sign * wall, across, fillet_top - 0.1)), (sign, across))
                self.assertFalse(nest.is_inside((sign * wall, across, fillet_top + 0.5)), (sign, across))
        self.assertAlmostEqual(p.window_floor_z("x"), fillet_top)
        for sign in (1, -1):  # The y faces keep their low windows.
            self.assertFalse(nest.is_inside((0.0, sign * wall, p.window_floor_lip + 0.5)), sign)
            self.assertTrue(nest.is_inside((0.0, sign * wall, p.window_floor_lip - 0.5)), sign)

    def test_rib_stands_clear_of_the_heatsink_base(self):
        """The rib is far shorter than the pins, so the lead and M3 drills exit above it."""
        p = self.p
        self.assertLess(p.rib_height, p.light.heatsink_height - p.light.heatsink_base)
        self.assertLess(p.rib_half_length, p.plate_bore_diameter / 2)
        nest = self.nests[HEATSINK]
        self.assertTrue(nest.is_inside((0, p.rib_half_length - 1, p.rib_height / 2)))
        self.assertFalse(nest.is_inside((0, 0, p.rib_height + 1.0)))

    def test_corner_screws_clear_the_bore_and_each_other(self):
        p = self.p
        axis = math.hypot(p.screw_offset, p.screw_offset)
        self.assertGreater(axis - p.plate_bore_diameter / 2 - p.layout.m3_clearance_diameter / 2, 3.0)
        self.assertLess(p.screw_offset + p.layout.m3_clearance_diameter / 2, p.body_side / 2 - 2.0)
        for kind in NEST_KINDS:
            depth = p.insert_flange_recess_depth + p.insert_hole_depth
            engagement = (
                12.0 - p.plate_thickness - p.insert_flange_recess_depth
            )  # M3 × 12 screw, in the insert.
            self.assertGreaterEqual(engagement, 5.0)
            self.assertLess(12.0 - p.plate_thickness, depth)  # The tip stops inside the hole.
            self.assertGreaterEqual(depth, 6.5)  # McMaster's minimum material thickness for the insert.
            self.assertGreaterEqual(p.nest_top(kind) - depth + p.floor_thickness, 1.0)  # Floor left below.

    def test_assembly_children_are_labeled_distinctly(self):
        for kind in NEST_KINDS:
            children = children_by_label(self.assemblies[kind])
            bushings = [k for k in children if k.startswith(BUSHING_LABEL)]
            self.assertEqual(len(bushings), len(self.p.layout.holes()))

    def test_bushings_stand_in_their_bores(self):
        for kind in NEST_KINDS:
            children = children_by_label(self.assemblies[kind])
            plate = children["Bushing plate"]
            for k, child in children.items():
                if k.startswith(BUSHING_LABEL):
                    self.assertAlmostEqual(intersect(plate, child).volume, 0.0, places=6, msg=k)

    @shared
    def with_parts(cls):
        return {kind: children_by_label(build_fixture_assembly(cls.p, kind)) for kind in NEST_KINDS}

    def test_cap_stands_on_its_back_face_thread_up(self):
        """Back face on the support surface (z=0), the thread boss face at the cap's overall height."""
        box = self.with_parts[CAP]["SM1CP2M cap"].bounding_box()
        self.assertAlmostEqual(box.min.Z, 0.0, places=3)
        self.assertAlmostEqual(box.max.Z, self.p.part_height(CAP), places=3)
        self.assertAlmostEqual(box.center().X, 0.0, places=2)
        self.assertAlmostEqual(box.center().Y, 0.0, places=2)
        self.assertAlmostEqual(box.size.X, self.p.light.cap_flange_diameter, places=2)

    def test_cap_clears_the_nest_and_the_seated_plate(self):
        p = self.p
        cap = self.with_parts[CAP]["SM1CP2M cap"]
        self.assertAlmostEqual(intersect(cap, self.nests[CAP]).volume, 0.0, places=3)
        self.assertAlmostEqual(
            intersect(cap, self.seated_plate(CAP)).volume, 0.0, places=3
        )  # Ring around the boss.
        self.assertAlmostEqual(p.nest_top(CAP) - cap.bounding_box().max.Z, p.standoff, places=3)

    def test_heatsink_hangs_on_its_pins_with_the_base_up(self):
        box = self.with_parts[HEATSINK]["CN40-40B heatsink"].bounding_box()
        self.assertAlmostEqual(box.min.Z, 0.0, places=3)
        self.assertAlmostEqual(box.max.Z, self.p.part_height(HEATSINK), places=3)
        self.assertAlmostEqual(self.p.nest_top(HEATSINK) - box.max.Z, self.p.standoff, places=3)

    def test_vendor_bushings_are_chamfered_end_up_in_their_bores(self):
        for kind in NEST_KINDS:
            top = self.p.nest_top(kind)
            for i, hole in enumerate(self.p.layout.holes(), start=1):
                bushing = self.with_parts[kind][f"{BUSHING_LABEL} {i}"]
                spec = BUSHINGS[hole.kind]
                box = bushing.bounding_box()
                self.assertAlmostEqual(box.min.Z, top, places=3)
                self.assertAlmostEqual(box.max.Z, top + spec.length, places=3)
                self.assertAlmostEqual(box.center().X, hole.x, places=3)
                self.assertAlmostEqual(box.center().Y, hole.y, places=3)
                self.assertFalse(bushing.is_inside((hole.x, hole.y, top + 1.0)))  # The bore is open.
                self.assertTrue(bushing.is_inside((hole.x + spec.bore / 2 + 0.1, hole.y, top + 1.0)))
                # Internal chamfer at the top: the bore is wider just under the top face than at mid-length.
                r = spec.bore / 2 + 0.05
                self.assertFalse(bushing.is_inside((hole.x + r, hole.y, top + spec.length - 0.05)))
                self.assertTrue(bushing.is_inside((hole.x + r, hole.y, top + spec.length / 2)))

    def ear_point(self, angle, u, v, z):
        """A point in an ear's frame: u out from the nest face, v along the ear slot."""
        a = math.radians(angle)
        return (u * math.cos(a) - v * math.sin(a), u * math.sin(a) + v * math.cos(a), z)

    def test_ears_carry_slots_along_the_faces(self):
        """Each nest has an ear on both x faces, its slot open along the face over the ear travel and closed
        beyond it."""
        p = self.p
        z = -p.floor_thickness + p.ear_thickness / 2
        r = p.ear_bolt_radius
        for kind in NEST_KINDS:
            nest = self.nests[kind]
            for angle in EAR_ANGLES:
                for v in (-p.ear_travel, 0.0, p.ear_travel):
                    self.assertFalse(nest.is_inside(self.ear_point(angle, r, v, z)), (kind, angle, v))
                beyond = p.ear_travel + p.ear_slot_width / 2 + 1.0
                self.assertTrue(nest.is_inside(self.ear_point(angle, r, beyond, z)), (kind, angle))
                self.assertTrue(
                    nest.is_inside(self.ear_point(angle, r + p.ear_slot_width, 0, z)), (kind, angle)
                )
                self.assertTrue(
                    nest.is_inside(self.ear_point(angle, r - p.ear_slot_width, 0, z)), (kind, angle)
                )
            # The y faces have no ears.
            self.assertFalse(nest.is_inside(self.ear_point(90.0, r + p.ear_slot_width, 0, z)), kind)

    def test_ear_roots_are_filleted(self):
        """Material in the corners where each ear meets the face, bounded by the fillet arc."""
        p = self.p
        face, half = p.body_side / 2, p.ear_half_length
        for kind in NEST_KINDS:
            nest = self.nests[kind]
            for angle in EAR_ANGLES:
                f = p.ear_root_fillet_radius
                near, far = 0.2 * f, 0.8 * f  # Inside the fillet near its root; beyond its arc.
                self.assertTrue(nest.is_inside(self.ear_point(angle, face + near, 0, p.ear_top + near)), kind)
                self.assertFalse(nest.is_inside(self.ear_point(angle, face + far, 0, p.ear_top + far)), kind)
                z = -p.floor_thickness + p.ear_thickness / 2
                for side in (-1, 1):
                    inside = self.ear_point(angle, face + near, side * (half + near), z)
                    outside = self.ear_point(angle, face + far, side * (half + far), z)
                    self.assertTrue(nest.is_inside(inside), (kind, angle, side))
                    self.assertFalse(nest.is_inside(outside), (kind, angle, side))

    def test_ears_sit_on_the_floor_below_the_plate(self):
        p = self.p
        for kind in NEST_KINDS:
            self.assertAlmostEqual(self.nests[kind].bounding_box().min.Z, -p.floor_thickness, msg=kind)
            self.assertAlmostEqual(intersect(self.nests[kind], self.seated_plate(kind)).volume, 0.0, places=6)
        self.assertLess(p.ear_top, p.nest_top(CAP))

    def test_travel_brings_every_bushing_under_the_spindle(self):
        """The fixture moves in x along the base slots and in y along the ear slots, past every bushing."""
        holes = self.p.layout.holes()
        self.assertGreater(self.p.slot_travel, max(abs(h.x) for h in holes))
        self.assertGreater(self.p.ear_travel, max(abs(h.y) for h in holes))

    def test_carriage_bolts_stay_in_the_base_slots(self):
        """Over the full travel, the square neck stays between the slot's inner end and its keyhole."""
        lo, hi = self.p.bolt_slot_range()
        self.assertGreaterEqual(lo, self.p.base_slot_inner_radius)
        self.assertLessEqual(hi, self.p.base_slot_outer_radius)

    def test_thumb_nuts_turn_clear_of_the_nests(self):
        self.assertGreaterEqual(self.p.thumb_nut_gap(), self.p.nut_clearance)

    def test_carriage_bolt_stack(self):
        """Neck within the base slot; enough thread in the thumb nut on the washer on the ear."""
        p = self.p
        self.assertLessEqual(MCMASTER_92356A589_NECK_LENGTH, p.base_slot_depth)
        self.assertGreaterEqual(p.nut_engagement(), p.min_nut_engagement)
        children = self.with_parts[CAP]
        for i, angle in enumerate(EAR_ANGLES, start=1):
            x, y = p.ear_bolt_position(angle)
            bolt = children[f"{EAR_BOLT_LABEL} {i}"].bounding_box()
            washer = children[f"{EAR_WASHER_LABEL} {i}"].bounding_box()
            nut = children[f"{EAR_NUT_LABEL} {i}"].bounding_box()
            self.assertAlmostEqual(bolt.max.Z, p.bolt_under_head_z + MCMASTER_92356A589_LENGTH, places=2)
            self.assertAlmostEqual(washer.min.Z, p.ear_top, places=3)
            self.assertAlmostEqual(nut.min.Z, p.ear_top + MCMASTER_96659A134_THICKNESS, places=2)
            for box in (bolt, washer, nut):
                self.assertAlmostEqual(box.center().X, x, places=2)
                self.assertAlmostEqual(box.center().Y, y, places=2)

    def test_hold_down_pad_presses_the_part_face(self):
        """The boss and the rubber disc together overshoot the standoff by a modest compression."""
        p = self.p
        self.assertTrue(p.pad_preload_min <= p.pad_preload <= p.pad_preload_max)
        for kind in NEST_KINDS:
            pad = self.with_parts[kind][PAD_LABEL].bounding_box()
            top = p.nest_top(kind)
            self.assertAlmostEqual(pad.min.Z, top - p.standoff, places=6)  # On the part face.
            self.assertAlmostEqual(pad.max.Z, top - p.pad_boss_height, places=6)  # Under the boss.
            self.assertAlmostEqual(pad.size.X, p.pad_diameter, places=6)

    def test_pad_boss_sits_between_the_bushings(self):
        self.assertGreaterEqual(self.p.pad_clearance(), self.p.min_web)
        plate = self.plate
        self.assertTrue(plate.is_inside((0, 0, -self.p.pad_boss_height / 2)))
        self.assertFalse(plate.is_inside((self.p.pad_diameter / 2 + 0.5, 0, -self.p.pad_boss_height / 2)))

    def test_plate_screws_run_from_the_plate_into_the_corner_inserts(self):
        """Head on the plate's top face, shank through the plate into an insert whose flange is recessed."""
        p = self.p
        for kind in NEST_KINDS:
            children = self.with_parts[kind]
            top = p.nest_top(kind)
            for i, (x, y) in enumerate(
                [(sx * p.screw_offset, sy * p.screw_offset) for sx in (-1, 1) for sy in (-1, 1)], 1
            ):
                screw = children[f"{PLATE_SCREW_LABEL} {i}"].bounding_box()
                insert = children[f"{INSERT_LABEL} {i}"].bounding_box()
                self.assertAlmostEqual(screw.center().X, x, places=2)
                self.assertAlmostEqual(screw.center().Y, y, places=2)
                self.assertAlmostEqual(insert.center().X, x, places=2)
                self.assertAlmostEqual(insert.center().Y, y, places=2)
                self.assertAlmostEqual(screw.min.Z, top + p.plate_thickness - 12.0, places=2)  # Tip.
                self.assertAlmostEqual(screw.max.Z, top + p.plate_thickness + 3.0, places=2)  # Head top.
                self.assertAlmostEqual(
                    insert.max.Z,
                    top - p.insert_flange_recess_depth + 0.53,
                    places=2,  # Flange face, just under the top.
                )
                self.assertGreater(screw.min.Z, top - p.insert_flange_recess_depth - p.insert_hole_depth)

    def test_cap_nest_clamp_screw_and_insert(self):
        p = self.p
        children = self.with_parts[CAP]
        face = -p.body_side / 2 + p.clamp_notch_depth
        z = p.flange_thickness / 2
        screw = children[CLAMP_SCREW_LABEL].bounding_box()
        insert = children[f"{INSERT_LABEL} 5"].bounding_box()
        self.assertAlmostEqual(screw.center().X, 0.0, places=2)
        self.assertAlmostEqual(screw.center().Z, z, places=2)
        self.assertAlmostEqual(insert.center().Z, z, places=2)
        self.assertAlmostEqual(screw.max.Y, face + 12.0, places=2)  # Tip, 12 mm from the notch face.
        self.assertGreater(screw.max.Y, -p.pocket_diameter / 2)  # Protrudes into the pocket.
        self.assertLess(screw.min.Y, face)  # Head outside the notch face.
        self.assertNotIn(CLAMP_SCREW_LABEL, self.with_parts[HEATSINK])

    def test_bore_coupon(self):
        coupon = build_bore_coupon(self.p)
        radii = cylinder_radii(coupon)
        diameters = sorted({b.outer_diameter for b in BUSHINGS.values()})
        expected = sorted(round((d + u) / 2, 4) for d in diameters for u in COUPON_OVERSIZES)
        self.assertEqual(radii, expected)

    def test_oversize_changes_the_printed_bores(self):
        p = replace(self.p, bushing_bore_oversize=0.1)
        radii = cylinder_radii(build_bushing_plate(p))
        self.assertIn(round((BUSHINGS["m3"].outer_diameter + 0.1) / 2, 4), radii)

    def test_rejects_a_bushing_that_does_not_match_the_cap_drill(self):
        p = replace(self.p, layout=replace(self.p.layout, m2_tap_drill=1.7))
        with self.assertRaises(ValueError):
            p.validate()


if __name__ == "__main__":
    unittest.main()

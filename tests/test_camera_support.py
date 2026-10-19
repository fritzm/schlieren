"""Engineering invariants for the lens cradle and phone rest (design §§9.4-9.7)."""

import unittest
from dataclasses import replace
from itertools import pairwise
from math import radians, sin, sqrt

from build123d import Cylinder, Pos, Vector

from schlieren.cad import along_x, children_by_label, intersect, leaves, moved
from schlieren.parts.camera_support import (
    CameraSupportParameters,
    _arm_point,
    _pad_pocket,
    band_leg_angle,
    band_path,
    build_camera_support_assembly,
    build_cradle_shoe,
    build_cradle_yoke,
    build_phone_rest,
    build_phone_rest_for_print,
    rod_rib,
    screw_location,
)
from schlieren.standards import OPTICAL_HEIGHT
from schlieren.testing import bounded_distance, near_pairs_among, shared, slow
from schlieren.vendor_cad import (
    MCMASTER_92815A202_HEIGHT,
    MCMASTER_94459A797_FLANGE_DIAMETER,
    MCMASTER_94459A797_LENGTH,
    mcmaster_92815a202_envelope,
    vendor_step,
)

CONTACT = 1e-3  # mm
ADJUSTERS = tuple(f"{where} {side}" for where in ("Aft", "Fore") for side in ("left", "right"))
NUT_CHAMFER = 0.5  # mm, on the thumb nut's knurled head; its plain envelope has square corners.
MAGNET_PADS = ("Fore left", "Fore right", "Aft right")  # The aft left screw sits in the rod groove.


def _other_side(where, side):
    """A yoke's or collar's left and right are as seen looking toward the other collar; the fore one's are the
    rig's right and left."""
    return side if where == "Aft" else {"left": "right", "right": "left"}[side]


def parts_by_name(assembly):
    """Every part of the assembly by one flat name, with the cradle's parts named "Aft collar", "Fore left
    screw", "Aft yoke insert", and so on, left and right being the rig's."""
    named = {}

    def walk(node, path):
        if node.children:
            for child in node.children:
                walk(child, [*path, node.label])
            return
        group = path[-1]
        where = group.split()[0]
        label = node.label
        if group == "Lens cradle":
            name = f"Cradle shoe {label.lower()}" if label.endswith(("left", "right")) else label
        elif group == "Phone rest":
            name = {"Rest body": "Phone rest", "Rest rod": "Rest rod"}.get(
                label, f"Phone rest {label.lower()}"
            )
        elif group.endswith(" yoke assembly"):
            name = {"Yoke": f"{where} yoke", "Joint insert": f"{where} yoke insert"}.get(
                label, f"{where} yoke screw"
            )
        elif group.endswith(" adjuster"):
            where = path[-2].split()[0]
            side = _other_side(where, group.split()[0].lower())
            name = f"{where} {side} {label.lower()}"
        elif group.endswith(" collar"):
            if label == "Collar":
                name = group
            elif label.startswith("Clamp"):
                name = f"{group} clamp {label.split()[1]}"
            elif label.endswith("magnet"):
                name = f"{where} {_other_side(where, label.split()[0].lower())} magnet"
            else:
                name = label
        else:
            name = label
        assert name not in named, name
        named[name] = node

    walk(assembly, [])
    return named


class LensCradleTests(unittest.TestCase):
    @shared
    def nut_envelopes(cls):
        """Each thumb nut's envelope, placed as the nut is: the knurled model is slow in a distance query, and
        a clearance to the envelope that contains it is never larger than the true one."""
        p = cls.p
        seat = Pos(0, 0, -p.nut_below_tip - MCMASTER_92815A202_HEIGHT)
        stations = {"Aft": p.aft_station, "Fore": p.fore_station}
        sides = {"left": -1, "right": 1}
        return {
            name: moved(mcmaster_92815a202_envelope(), screw_location(p, sides[side], stations[where]) * seat)
            for name in ADJUSTERS
            for where, side in [name.split()]
        }

    @shared
    def rest(cls):
        return build_phone_rest(cls.p)

    @shared
    def rest_for_print(cls):
        return build_phone_rest_for_print(cls.p)

    @shared
    def cradle_shoe(cls):
        return build_cradle_shoe(cls.p)

    @shared
    def yokes(cls):
        return [build_cradle_yoke(cls.p, station) for station in cls.p.stations]

    @shared
    def parts_with_cutoff(cls):
        return parts_by_name(build_camera_support_assembly(cls.p))

    @classmethod
    def setUpClass(cls):
        cls.p = CameraSupportParameters()
        cls.assembly = build_camera_support_assembly(cls.p, include_cutoff=False)
        cls.parts = parts_by_name(cls.assembly)

    def test_collars_sit_on_the_clampable_barrel_clear_of_the_focus_ring(self):
        p = self.p
        aft = self.parts["Aft collar"].bounding_box()
        fore = self.parts["Fore collar"].bounding_box()
        self.assertGreaterEqual(aft.min.Y, p.barrel_start)
        self.assertGreater(fore.min.Y, aft.max.Y)
        self.assertGreaterEqual(p.focus_ring_start - fore.max.Y, 1.5)
        self.assertGreater(p.fore_station - p.aft_station, 70.0)

    def test_lens_and_main_camera_are_on_the_optical_axis(self):
        p = self.p
        lens = self.parts["Lens body"].bounding_box()
        self.assertAlmostEqual((lens.min.Z + lens.max.Z) / 2, OPTICAL_HEIGHT, places=4)
        self.assertAlmostEqual((lens.min.X + lens.max.X) / 2, 0.0, places=4)
        phone = self.parts["Case"].bounding_box()
        self.assertAlmostEqual(OPTICAL_HEIGHT - phone.min.Z, 60.6, places=4)  # Measured, §9.1.
        self.assertAlmostEqual(-phone.min.X, 34.3, places=4)  # Measured, §9.1.
        self.assertGreater(phone.max.X, -phone.min.X)  # The body hangs outboard, toward +x.
        # The lens reaches through the camera opening to the camera glass: the ridge top, the case's rearmost
        # point, stands the glass recess ahead of the lens aft end.
        self.assertAlmostEqual(phone.max.Y - lens.min.Y, p.phone.camera_cover_recess, places=3)
        self.assertAlmostEqual(p.phone.cased_length, 155.53, places=2)

    def test_each_screw_tip_bears_on_its_pad_or_the_groove(self):
        for station in MAGNET_PADS:
            screw, pad = self.parts[f"{station} screw"], self.parts[f"{station} magnet"]
            with self.subTest(pad=station):
                self.assertLess(screw.distance_to(pad), CONTACT)
                self.assertLess(intersect(screw, pad).volume, CONTACT)
        self.assertNotIn("Aft left magnet", self.parts)
        screw = self.parts["Aft left screw"]
        for rod in ("Groove rod -1", "Groove rod +1"):
            with self.subTest(rod=rod):
                self.assertLess(screw.distance_to(self.parts[rod]), CONTACT)
                self.assertLess(intersect(screw, self.parts[rod]).volume, CONTACT)

    def test_screws_are_at_right_angles_through_the_lens_axis(self):
        p = self.p
        self.assertEqual(p.screw_angle, 45.0)
        for station in MAGNET_PADS:
            center = self.parts[f"{station} magnet"].center()
            # Pads are tangent to a circle about the axis: equal offsets across and below it.
            with self.subTest(pad=station):
                self.assertAlmostEqual(abs(center.X), OPTICAL_HEIGHT - center.Z, places=3)
        # Pads lie with their long side across the rail, the direction they slide most.
        self.assertAlmostEqual(self.parts["Fore left magnet"].bounding_box().size.Y, p.magnet_width, places=4)

    def test_four_adjusters_with_inserts_inside_the_yoke_bosses(self):
        p = self.p
        model = vendor_step("McMaster-94459A797.step").bounding_box()
        self.assertAlmostEqual(model.size.Y, MCMASTER_94459A797_LENGTH, places=3)
        self.assertAlmostEqual(model.size.X, MCMASTER_94459A797_FLANGE_DIAMETER, places=3)
        self.assertGreaterEqual(p.yoke_boss_length, MCMASTER_94459A797_LENGTH)
        # The thumb nut stays clear above the insert flange over the screw's travel.
        self.assertGreaterEqual(p.boss_top_below_tip - p.nut_below_tip - 5.0, 4.0)
        for name in ADJUSTERS:
            insert = self.parts[f"{name} insert"]
            side = -1 if name.endswith("left") else 1
            cradle = self.parts[f"{name.split()[0]} yoke"]
            toward_axis = Vector(-side, 0, 1).normalized()
            center = insert.center()
            screw = self.parts[f"{name} screw"]
            with self.subTest(adjuster=name):
                # The insert lies along the screw axis, in a drilled hole in its arm, flange at the face.
                box = insert.bounding_box()
                along = max(box.size.X, box.size.Z)
                self.assertGreater(along, MCMASTER_94459A797_FLANGE_DIAMETER)  # Inclined, not axis-aligned.
                self.assertFalse(cradle.is_inside(center))
                for offset in (-0.4, 0.0):  # Material right round the insert body, deeper than the flange.
                    on_axis = center + toward_axis * (offset * MCMASTER_94459A797_LENGTH)
                    for dy in (-3.4, 3.4):
                        self.assertTrue(cradle.is_inside(on_axis + Vector(0, dy, 0)))
                self.assertFalse(cradle.is_inside(center + toward_axis * MCMASTER_94459A797_LENGTH))
                # The bore carries on through the back of the arm, past the insert, for the screw and its key.
                behind = center - toward_axis * (MCMASTER_94459A797_LENGTH / 2 + 2.5)
                self.assertFalse(cradle.is_inside(behind))
                self.assertTrue(cradle.is_inside(behind + Vector(0, 3.4, 0)))
                self.assertLess(intersect(screw, cradle).volume, 0.01)
        for kind in ("insert", "thumb nut", "screw"):
            self.assertEqual(sum(label == f"{name} {kind}" for name in ADJUSTERS for label in self.parts), 4)

    def test_yoke_walls_round_inserts_and_filleted_roots(self):
        p = self.p
        counterbore = MCMASTER_94459A797_FLANGE_DIAMETER + 0.2
        self.assertGreaterEqual((p.yoke_thickness - counterbore) / 2, p.yoke_min_insert_wall)
        self.assertGreaterEqual((p.yoke_boss_width - counterbore) / 2, p.yoke_min_insert_wall)
        self.assertGreaterEqual((p.rail_size - counterbore) / 2, p.yoke_min_insert_wall)
        bottom = p.yoke_top - p.yoke_crossbar
        back_s = p.pad_radius + p.boss_top_below_tip + p.yoke_boss_length + 0.5
        for where, station in zip(("Aft", "Fore"), p.stations, strict=True):
            yoke = self.parts[f"{where} yoke"]
            with self.subTest(yoke=where):
                for side in (-1, 1):
                    # A sharp column-to-crossbar corner would leave this point, just inside it, empty.
                    self.assertTrue(yoke.is_inside((side * (p.rail_size / 2 + 0.6), station, bottom - 0.6)))
                    # And the outboard arm corner is rounded: this point, just inside a sharp one, is empty.
                    corner_x, corner_z = _arm_point(p, side, back_s, p.yoke_boss_width / 2)
                    self.assertFalse(yoke.is_inside((corner_x - side * 0.4, station, corner_z)))
                    self.assertTrue(yoke.is_inside((corner_x - side * 2.0, station, corner_z)))
                box = yoke.bounding_box()
                # The yoke is its thickness about the station, and the peg stands out of one face.
                peg = p.horn_stem_length + p.horn_lip_height
                self.assertAlmostEqual(box.size.Y, p.yoke_thickness + peg, places=4)
                direction = p.toward_other(station)
                self.assertAlmostEqual(
                    box.min.Y if direction > 0 else box.max.Y,
                    station - direction * p.yoke_thickness / 2,
                    places=4,
                )
                self.assertAlmostEqual(box.min.X, -box.max.X, places=4)  # Symmetric across the rail.
        self.assertEqual(len(self.parts["Aft yoke"].solids()), 1)

    def test_collar_clamp_hardware_sits_on_the_ear_axis(self):
        p = self.p
        zc = p.optical_height + p.collar_radius + p.clamp_screw_above_ring
        for where, station in zip(("Aft", "Fore"), p.stations, strict=True):
            with self.subTest(collar=where):
                screw = self.parts[f"{where} collar clamp screw"].bounding_box()
                nut = self.parts[f"{where} collar clamp nut"].bounding_box()
                # The head bears on the outer face of the screw ear; the nut seats on its pocket floor.
                self.assertAlmostEqual(screw.max.X - 12.0, p.ear_screw_side, places=3)
                self.assertAlmostEqual(nut.min.X, p.ear_nut_side - p.rail_shoe.nut_pocket_depth, places=3)
                for box in (screw, nut):
                    self.assertAlmostEqual((box.min.Y + box.max.Y) / 2, station, places=3)
                    self.assertAlmostEqual((box.min.Z + box.max.Z) / 2, zc, places=3)

    def test_collar_is_a_thin_filleted_split_ring(self):
        p, r = self.p, self.p.rail_shoe
        zc = p.optical_height
        for where, station in zip(("Aft", "Fore"), p.stations, strict=True):
            collar = self.parts[f"{where} collar"]
            with self.subTest(collar=where):
                self.assertTrue(collar.is_valid)
                self.assertEqual(len(collar.solids()), 1)
                # Ring wall at the hinge, opposite the split: exactly the wall, no more.
                self.assertAlmostEqual(p.collar_radius - p.collar_bore / 2, p.collar_wall)
                self.assertTrue(collar.is_inside((0, station, zc - p.collar_radius + 0.1)))
                self.assertFalse(collar.is_inside((0, station, zc - p.collar_radius - 0.1)))
                self.assertTrue(collar.is_inside((0, station, zc - p.collar_bore / 2 - 0.1)))
                self.assertFalse(collar.is_inside((0, station, zc - p.collar_bore / 2 + 0.1)))
                # The bore clears the barrel, whose measured diameter is 37.01 to 37.06 mm.
                self.assertGreaterEqual(p.collar_bore - 37.06, 0.2)
                # The split, with sharp faces: open at the middle, material just either side.
                top = zc + p.collar_radius + 1
                self.assertFalse(collar.is_inside((0, station, top)))
                for side in (-1, 1):
                    self.assertTrue(collar.is_inside((side * (r.split_gap / 2 + 0.1), station, top)))
                # Inside corner at each ear root is filled by the fillet, the ring end edge rounded.
                for x in (p.ear_screw_side, p.ear_nut_side):
                    root = zc + sqrt(p.collar_radius**2 - x**2)
                    side = 1 if x > 0 else -1
                    self.assertTrue(collar.is_inside((x + side * 0.15, station, root + 0.25)))
                edge = (0.0, station + p.collar_width / 2 - 0.1, zc - p.collar_radius + 0.1)
                self.assertFalse(collar.is_inside(edge))

    def test_collar_ears_have_the_clamp_screw_hole_and_nut_pocket(self):
        p, r = self.p, self.p.rail_shoe
        for where, station in zip(("Aft", "Fore"), p.stations, strict=True):
            collar = self.parts[f"{where} collar"]
            screw_z = p.optical_height + p.collar_radius + p.clamp_screw_above_ring
            with self.subTest(collar=where):
                self.assertGreaterEqual(p.ear_top_wall, 1.5)
                hole = r.m3_clearance_diameter / 2
                self.assertFalse(collar.is_inside((p.ear_screw_side + 1, station, screw_z)))
                self.assertFalse(collar.is_inside((-0.8, station, screw_z)))
                self.assertTrue(collar.is_inside((p.ear_screw_side + 1, station + hole + 0.2, screw_z)))
                # Hex nut pocket in the nut ear, open to the outside, flats up and down, walled behind.
                flats = (r.clamp_nut_across_flats + r.nut_across_flats_clearance) / 2
                pocket_back = p.ear_nut_side - r.nut_pocket_depth
                self.assertFalse(collar.is_inside((p.ear_nut_side - 0.5, station, screw_z + flats - 0.1)))
                self.assertTrue(collar.is_inside((p.ear_nut_side - 0.5, station, screw_z + flats + 0.1)))
                self.assertTrue(collar.is_inside((pocket_back - 0.4, station + hole + 0.3, screw_z)))
                self.assertFalse(collar.is_inside((pocket_back + 0.4, station, screw_z)))

    def test_pad_pockets_hold_the_bearing_surfaces_with_a_rim(self):
        p = self.p
        for where, station in zip(("Aft", "Fore"), p.stations, strict=True):
            collar = self.parts[f"{where} collar"]
            for name, side in (("left", -1), ("right", 1)):
                loc = screw_location(p, side, station)
                rods = (where, side) == ("Aft", -1)
                across, along = _pad_pocket(p, rods)
                with self.subTest(pad=(where, name)):

                    def local(x, y, z, loc=loc):
                        return (loc * Pos(x, y, z)).position

                    # Pocket: open above the pad face, floor 2 mm below it, rim 0.8 mm above it.
                    self.assertFalse(collar.is_inside(local(0, 0, -0.5)))
                    # Open to the floor, except the groove pad's locating rib along its middle.
                    self.assertEqual(collar.is_inside(local(0, 0, p.magnet_thickness - 0.1)), rods)
                    self.assertTrue(collar.is_inside(local(0, 0, p.magnet_thickness + 0.2)))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        wall = local(
                            dx * (across / 2 + 0.5), dy * (along / 2 + 0.5), -p.pad_wall_height + 0.3
                        )
                        self.assertTrue(collar.is_inside(wall))
                        above = local(
                            dx * (across / 2 + 0.5), dy * (along / 2 + 0.5), -p.pad_wall_height - 0.2
                        )
                        self.assertFalse(collar.is_inside(above))
                    bearing = self.parts[f"{where} {name} magnet"] if not rods else None
                    if bearing is not None:
                        self.assertLess(intersect(bearing, collar).volume, 0.01)
        for rod in ("Groove rod -1", "Groove rod +1"):
            self.assertLess(intersect(self.parts[rod], self.parts["Aft collar"]).volume, 0.01)

    def test_groove_rib_locates_both_rods_and_clears_the_ball(self):
        p = self.p
        collar = self.parts["Aft collar"]
        loc = screw_location(p, -1, p.aft_station)
        width, height = rod_rib(p)
        floor = p.magnet_thickness
        self.assertAlmostEqual(height, 1.0, places=6)
        self.assertAlmostEqual(width, 1.683, places=3)  # Calculated: rods at 4.5 mm resting on its corners.
        inside = loc * Pos(0, 0, floor - height / 2)
        above = loc * Pos(0, 0, floor - height - 0.2)
        self.assertTrue(collar.is_inside(inside.position))
        self.assertFalse(collar.is_inside(above.position))
        for rod in ("Groove rod -1", "Groove rod +1"):
            with self.subTest(rod=rod):
                self.assertLess(self.parts[rod].distance_to(collar), CONTACT)
                self.assertLess(intersect(self.parts[rod], collar).volume, 0.01)
        ball = self.parts["Aft left screw"]
        self.assertGreater(ball.distance_to(collar), p.groove_rib_height / 2)  # The rib stays clear of it.

    def test_ball_end_is_stopped_by_the_pocket_rim_before_the_pad_edge(self):
        p = self.p
        stop_x, stop_y = p.pad_edge_stop
        # Full excursion: the apex reaches to within the margin of the 10 x 5 mm pad edges.
        self.assertAlmostEqual(stop_x, p.magnet_length / 2 - p.pad_edge_margin, places=6)
        self.assertAlmostEqual(stop_y, p.magnet_width / 2 - p.pad_edge_margin, places=6)
        collar = self.parts["Fore collar"]
        loc = screw_location(p, -1, p.fore_station)
        screw = self.parts["Fore left screw"]
        for axis, stop in (((1, 0), stop_x), ((0, 1), stop_y)):
            for sign in (-1, 1):

                def shifted(extra, loc=loc, sign=sign, axis=axis, stop=stop):
                    move = Pos(sign * axis[0] * (stop + extra), sign * axis[1] * (stop + extra), 0)
                    return moved(screw, loc * move * loc.inverse())

                with self.subTest(axis=axis, sign=sign):
                    self.assertLess(
                        intersect(shifted(-0.05), collar).volume, 1e-3
                    )  # Free, the end face clear too.
                    self.assertGreater(
                        intersect(shifted(0.3), collar).volume, 1e-3
                    )  # Past the rim edge: it stops.

    def test_retaining_bands_are_endless_loops_on_the_barrel_and_a_peg(self):
        p = self.p
        angle = band_leg_angle(p)
        self.assertGreater(angle, 60.0)  # Steep legs: most of the cord tension acts downward.
        # Calculated: tension in each leg for the hold-down force, the two legs sharing it.
        self.assertLess(p.band_hold_down / (2 * sin(radians(angle))), 3.2)
        path = band_path(p)
        for first, second in pairwise([*path, path[0]]):  # Continuous and closed.
            self.assertAlmostEqual(first[-1][0], second[1][0], places=6)
            self.assertAlmostEqual(first[-1][1], second[1][1], places=6)
        lens = self.parts["Lens body"]
        for where, station in zip(("Aft", "Fore"), p.stations, strict=True):
            band = self.parts[f"{where} band"]
            yoke, collar = self.parts[f"{where} yoke"], self.parts[f"{where} collar"]
            with self.subTest(band=where):
                self.assertTrue(band.is_valid)
                self.assertEqual(len(band.solids()), 1)
                cord = band.bounding_box()
                self.assertAlmostEqual(cord.size.Y, p.band_cord_diameter, places=4)
                # Beside the yoke, on the side toward the other collar, on a plain section of the barrel.
                direction = p.toward_other(station)
                self.assertGreater((cord.center().Y - station) * direction, p.yoke_thickness / 2 + 3.0)
                self.assertGreater(cord.min.Y, p.barrel_start)
                self.assertLess(cord.max.Y, p.focus_ring_start)
                self.assertGreater(collar.distance_to(band), 3.0)
                # Lying on the barrel, and on the neck of the peg, under its lip.
                self.assertLess(band.distance_to(lens), 0.01)
                self.assertLess(intersect(band, lens).volume, 0.01)
                self.assertLess(band.distance_to(yoke), 0.01)
                self.assertLess(intersect(band, yoke).volume, 0.01)
                base = p.horn_base(station)
                lip_start = base[1] + direction * p.horn_stem_length
                self.assertLess((cord.max.Y - lip_start) * direction, 0.0)
                # The peg: a stem and a lip, on the centre of the crossbar face, along the lens.
                for along, inside in (
                    (3.0, True),
                    (p.horn_stem_length + 0.5, True),
                    (p.horn_stem_length + 1.5, False),
                ):
                    self.assertEqual(yoke.is_inside((0.0, base[1] + direction * along, base[2])), inside)
                self.assertFalse(
                    yoke.is_inside((0.0, base[1] + direction * 3.0, base[2] + p.horn_diameter / 2 + 0.2))
                )
                self.assertTrue(
                    yoke.is_inside((0.0, base[1] + direction * (p.horn_stem_length + 0.5), base[2] + 2.5))
                )
        # The hold-down seen by each pad pair, from both bands, each acting at its own place on the barrel.
        aft, fore = p.stations

        def fore_share(y):
            return (y - aft) / (fore - aft)

        y_aft, y_fore = p.band_y(aft), p.band_y(fore)
        on_fore = p.band_hold_down * (fore_share(y_aft) + fore_share(y_fore))
        on_aft = 2 * p.band_hold_down - on_fore
        self.assertAlmostEqual(on_fore, p.band_hold_down, delta=0.05 * p.band_hold_down)
        self.assertAlmostEqual(on_aft, p.band_hold_down, delta=0.05 * p.band_hold_down)

    @slow
    def test_band_clears_the_thumb_nuts_and_the_arms(self):
        for where in ("Aft", "Fore"):
            band = self.parts[f"{where} band"]
            for side in ("left", "right"):
                nut = self.nut_envelopes[f"{where} {side}"]
                with self.subTest(nut=(where, side)):
                    self.assertGreater(bounded_distance(band, nut, 5.0), 5.0)

    def test_phone_lower_edge_rests_on_the_rod(self):
        p = self.p
        rod = self.parts["Rest rod"].bounding_box()
        phone = self.parts["Case"].bounding_box()
        self.assertAlmostEqual(rod.max.Z, phone.min.Z, places=4)
        self.assertGreater(rod.min.X, 60.0)  # Well outboard of the lens axis.
        self.assertLess(rod.max.X, phone.max.X)
        self.assertLess(rod.min.Y, phone.min.Y)  # The rod spans the phone's thickness, along the rail.
        self.assertGreater(rod.max.Y, phone.max.Y)
        self.assertAlmostEqual(phone.min.Z, 11.75, places=4)
        self.assertAlmostEqual(p.rest_x, 100.0)

    def test_rest_arm_prints_on_its_side_without_a_bridge(self):
        p = self.p
        rest = self.rest
        box = rest.bounding_box()
        # The arm spans the whole shoe along the rail, so every layer of a side print is the same profile.
        for y in (box.min.Y + 0.1, p.rest_center, box.max.Y - 0.1):
            self.assertTrue(rest.is_inside((p.shoe_outer + 20, y, p.rest_arm_top - p.rest_arm_depth / 2)))
        self.assertAlmostEqual(box.max.Z, p.rest_arm_top, places=4)
        # The rod lies in a half-round seat, not on a flat top.
        self.assertFalse(rest.is_inside((p.rest_x, p.rest_center, p.rest_arm_top - 1.0)))
        self.assertTrue(rest.is_inside((p.rest_x, p.rest_center, p.rest_arm_top - p.rest_rod_diameter)))
        # The root fillet fills the inside corner under the arm and stays above the screw head.
        r = p.rest_root_fillet
        corner = (p.shoe_outer + 0.2 * r, p.rest_center, p.rest_arm_top - p.rest_arm_depth - 0.2 * r)
        self.assertTrue(rest.is_inside(corner))
        head_top = -p.rail_shoe.rail_height / 2 + p.clamp_screw_head_diameter / 2
        self.assertGreaterEqual(
            p.rest_arm_top - p.rest_arm_depth - r - head_top, p.clamp_screw_head_clearance
        )

    def test_rest_print_orientation_lies_on_its_side_on_the_bed(self):
        p = self.p
        rest, printed = self.rest, self.rest_for_print
        box, model = printed.bounding_box(), rest.bounding_box()
        self.assertAlmostEqual(box.min.Z, 0.0, places=4)
        self.assertAlmostEqual(box.size.Z, p.rest_shoe_length, places=4)  # Stacked along the rail.
        self.assertAlmostEqual(box.size.X, model.size.X, places=4)
        self.assertAlmostEqual(box.size.Y, model.size.Z, places=4)
        self.assertAlmostEqual(printed.volume, rest.volume, places=3)

    def test_cradle_and_rest_are_separate_single_parts(self):
        cradle, rest, yokes = self.cradle_shoe, self.rest, self.yokes
        for part in (cradle, rest, *yokes):
            self.assertEqual(len(part.solids()), 1)
        self.assertGreater(cradle.distance_to(rest), 1.0)
        # Each saddle straddles the rail: nothing of either lies inside the rail section.
        for part in (cradle, rest):
            self.assertFalse(part.is_inside((0, part.center().Y, -10)))

    def test_cradle_groups_its_parts_and_shares_one_yoke_assembly(self):
        top = children_by_label(self.assembly)
        self.assertLessEqual({"Lens cradle", "Phone rest", "Phone", "Telephoto lens"}, set(top))
        cradle = children_by_label(top["Lens cradle"])
        self.assertEqual(
            set(cradle),
            {
                "Cradle shoe",
                "Aft yoke assembly",
                "Fore yoke assembly",
                "Aft collar",
                "Fore collar",
                "Aft band",
                "Fore band",
            }
            | {
                f"{where} side screw{washer} {side}"
                for where in ("Aft", "Fore")
                for washer in ("", " washer")
                for side in ("left", "right")
            },
        )
        self.assertEqual(
            set(children_by_label(top["Phone rest"])),
            {
                "Rest body",
                "Rest rod",
                "Side screw left",
                "Side screw right",
                "Side screw washer left",
                "Side screw washer right",
            },
        )
        aft, fore = (children_by_label(cradle[f"{where} yoke assembly"]) for where in ("Aft", "Fore"))
        self.assertEqual(set(aft), {"Yoke", "Joint insert", "Joint screw", "Left adjuster", "Right adjuster"})
        self.assertEqual(set(aft), set(fore))
        # The fore yoke assembly is the aft one's geometry turned half a turn, so its left adjuster is on the
        # rig's right.
        for label in ("Yoke", "Joint screw"):
            self.assertTrue(aft[label].solids()[0].wrapped.IsPartner(fore[label].solids()[0].wrapped))
        left = {w: children_by_label(a["Left adjuster"])["Screw"] for w, a in (("Aft", aft), ("Fore", fore))}
        self.assertLess(left["Aft"].center().X, 0)
        self.assertGreater(left["Fore"].center().X, 0)

    def test_side_screws_are_default_and_cross_the_rest_at_its_clamp_station(self):
        p = self.p
        plain = build_camera_support_assembly(p, include_cutoff=False, side_screws=False)
        labels = {part.label for part in leaves(plain)}
        self.assertFalse(any(label.startswith("Phone rest side screw") for label in labels))
        parts = self.parts
        for side in ("left", "right"):
            screw = parts[f"Phone rest side screw {side}"].bounding_box()
            with self.subTest(side=side):
                self.assertAlmostEqual((screw.min.Y + screw.max.Y) / 2, p.rest_center, places=2)
                self.assertAlmostEqual(
                    (screw.min.Z + screw.max.Z) / 2, -p.rail_shoe.rail_height / 2, places=2
                )
                self.assertIn(f"Phone rest side screw washer {side}", parts)

    def test_yokes_bolt_to_the_shoe_through_a_countersunk_hole_into_an_insert(self):
        p = self.p
        shoe = self.parts["Cradle shoe"]
        for where, station in zip(("Aft", "Fore"), p.stations, strict=True):
            yoke = self.parts[f"{where} yoke"]
            screw_part, insert_part = self.parts[f"{where} yoke screw"], self.parts[f"{where} yoke insert"]
            screw, insert = screw_part.bounding_box(), insert_part.bounding_box()
            with self.subTest(yoke=where):
                # The column sits flat on the deck between two walls, across the rail, with the allowance.
                self.assertAlmostEqual(yoke.bounding_box().min.Z, p.deck_top, places=4)
                self.assertLess(intersect(yoke, shoe).volume, 0.01)
                self.assertAlmostEqual(yoke.distance_to(shoe), 0.0, places=3)
                z = p.deck_top + p.locating_wall_height / 2
                face = p.yoke_thickness / 2
                gap = p.locating_clearance_per_side
                for side in (-1, 1):
                    wall = (0, station + side * (face + gap + p.locating_wall_thickness / 2), z)
                    self.assertTrue(shoe.is_inside(wall))
                    self.assertFalse(shoe.is_inside((0, station + side * (face + gap / 2), z)))
                    self.assertTrue(yoke.is_inside((0, station + side * (face - 0.1), z + 20)))
                self.assertFalse(shoe.is_inside((0, station, z)))  # Clear between the walls.
                self.assertAlmostEqual(
                    shoe.bounding_box().max.Z - p.deck_top, p.locating_wall_height, places=4
                )
                # One screw on the rail centerline: head flush with the deck underside, tip inside the insert.
                self.assertAlmostEqual(screw.center().X, 0.0, places=4)
                self.assertAlmostEqual(screw.min.Z, 0.0, places=4)
                self.assertAlmostEqual(screw.max.Z, p.joint_screw_length, places=4)
                self.assertAlmostEqual(insert.min.Z, p.joint_z, places=3)
                self.assertGreater(insert.max.Z, screw.max.Z)
                self.assertLess(intersect(screw_part, shoe).volume, 0.01)
                self.assertFalse(yoke.is_inside(insert.center()))  # The insert sits in a drilled hole.
                # The countersunk head clears the skirts.
                self.assertLess(p.joint_screw_head_diameter / 2, p.rail_shoe.rail_opening / 2)
        self.assertEqual(sum(label.endswith(" yoke screw") for label in self.parts), 2)

    def test_saddles_match_the_common_rail_shoe_and_have_clamp_holes(self):

        p, r = self.p, self.p.rail_shoe
        cradle, rest = self.cradle_shoe, self.rest
        self.assertNotIn("Cradle clamp screw 1 -1", self.parts)
        self.assertFalse([label for label in self.parts if label.startswith(("Cradle clamp", "Rest clamp"))])
        for part, ys in ((cradle, p.cradle_clamp_ys), (rest, (p.rest_center,))):
            box = part.bounding_box()
            self.assertAlmostEqual(box.min.Z, -r.skirt_depth, places=4)
            for y in ys:
                with self.subTest(y=y):
                    probe = along_x((-p.shoe_outer - 1, y, -r.rail_height / 2)) * Cylinder(
                        r.m5_clearance_diameter / 2 - 0.01, 2 * p.shoe_outer + 2
                    )
                    self.assertLess(
                        intersect(part, probe).volume, CONTACT
                    )  # The bore is open through both cheeks.
                    for side in (-1, 1):  # And the cheek is solid just beyond the hole.
                        wall = (r.rail_opening / 2 + r.side_wall / 2) * side
                        edge = (wall, y, -r.rail_height / 2 + r.m5_clearance_diameter)
                        self.assertTrue(part.is_inside(edge))
        middle = sum(p.stations) / 2
        self.assertAlmostEqual(cradle.bounding_box().center().Y, middle, places=4)  # Symmetric fore/aft.
        self.assertAlmostEqual(sum(p.cradle_clamp_ys) / 2, middle, places=4)
        y = p.cradle_clamp_ys[0] + 5
        self.assertTrue(cradle.is_inside((r.width / 2 - 0.1, y, -5)))
        self.assertFalse(cradle.is_inside((r.width / 2 + 0.1, y, -5)))
        self.assertAlmostEqual(r.rail_opening, 20.4)
        self.assertFalse(cradle.is_inside((r.rail_opening / 2 - 0.1, p.cradle_clamp_ys[0], -5)))
        self.assertTrue(cradle.is_inside((r.rail_opening / 2 + 0.1, p.cradle_clamp_ys[0], -5)))
        # Vertical outside corners are rounded to the shoe's radius.
        corner = (r.width / 2 - 0.2, cradle.bounding_box().min.Y + 0.2, -5)
        self.assertFalse(cradle.is_inside(corner))

    @slow
    def test_thumb_nut_envelopes_stand_where_the_nuts_do(self):
        """Each envelope's box holds its nut's, and is larger only by the chamfers the envelope squares
        off."""
        for name in ADJUSTERS:
            nut = self.parts[f"{name} thumb nut"].bounding_box()
            envelope = self.nut_envelopes[name].bounding_box()
            with self.subTest(adjuster=name):
                for axis in "XYZ":
                    below = getattr(nut.min, axis) - getattr(envelope.min, axis)
                    above = getattr(envelope.max, axis) - getattr(nut.max, axis)
                    for excess in (below, above):
                        self.assertGreater(excess, -0.01)
                        self.assertLess(excess, NUT_CHAMFER)

    def test_thumb_nuts_clear_their_yokes(self):
        for name in ADJUSTERS:
            nut, yoke = self.nut_envelopes[name], self.parts[f"{name.split()[0]} yoke"]
            with self.subTest(adjuster=name):
                self.assertGreater(bounded_distance(nut, yoke, 4.0), 4.0)

    @slow
    def test_parts_clear_each_other_and_the_cutoff_station(self):
        own = set(self.parts)
        parts = self.parts_with_cutoff
        printed = ("Cradle shoe", "Aft yoke", "Fore yoke", "Phone rest", "Aft collar", "Fore collar")
        let_in = (" screw", " magnet", " rod")  # Threaded into, or let into, a printed part.
        optics = {"Lens body", "Focus ring"}
        for a, b in near_pairs_among(parts.values()):
            labels = (a.label, b.label)
            if not own.intersection(labels) or "Optical axis" in labels or set(labels) == optics:
                continue  # The cutoff station's own fits are covered by its tests.
            if any(label.endswith(" insert") for label in labels):
                # Inserts are checked in their bosses above; their knurled model is slow to intersect.
                continue
            fitted = any(word in label for label in labels for word in let_in)
            if fitted and any(label in printed for label in labels):
                continue
            with self.subTest(pair=labels):
                self.assertLess(intersect(a, b).volume, 0.01)
        gap = parts["Rail shoe"].bounding_box().min.Y - parts["Cradle shoe"].bounding_box().max.Y
        self.assertGreater(gap, 5.0)

    def test_rejects_collars_off_the_clampable_barrel(self):
        for bad in (
            {"aft_station": 10.0},
            {"aft_station": 18.0},  # Rear face on the shoulder, 0.7 mm short of the barrel.
            {"fore_station": 100.0},
            {"yoke_boss_length": 6.0},
        ):
            with self.subTest(parameters=bad), self.assertRaises(ValueError):
                replace(self.p, **bad).validate()


if __name__ == "__main__":
    unittest.main()

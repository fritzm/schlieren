"""Engineering invariants for the common rail shoe (no external test runner)."""

import unittest
from dataclasses import replace
from math import cos, pi, sqrt

from build123d import Cylinder, GeomType, Plane, RegularPolygon, extrude, section

from schlieren.cad import ON_FLOOR, along_y
from schlieren.parts.rail import RailProfile
from schlieren.parts.rail_shoe import RailShoeParameters, build_rail_shoe, reference_parts, viewer_assembly
from schlieren.vendor_cad import MCMASTER_91292A114_HEAD_HEIGHT, MCMASTER_92290A_HEAD_HEIGHT

# The TR50/M STEP model is rounded to inches (0.499 in diameter), so it differs slightly from the nominal.
TR50_MODEL_ROUNDING = 0.03


def reference_children(shoe, p):
    """The viewer's reference parts (rail, disc, post, hardware) by label."""
    group = {child.label: child for child in viewer_assembly(shoe, p).children}["Reference parts"]
    return {child.label: child for child in group.children}


def ear_x_end(p):
    """Ear tip x: ear_width beyond where the collar meets the inner ear face."""
    return sqrt(p.collar_outer_radius**2 - (p.split_gap / 2) ** 2) + p.ear_width


def clamp_axis_xz(p):
    """Clamp screw/nut axis (parallel to y), centered on the exposed inner ear faces."""
    return ear_x_end(p) - p.ear_width / 2, p.ear_bottom + p.ear_height / 2


class RailShoeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = RailShoeParameters()
        cls.shoe = build_rail_shoe(cls.p)

    def test_single_valid_solid_and_envelope(self):
        self.assertTrue(self.shoe.is_valid)
        self.assertEqual(len(self.shoe.solids()), 1)
        box = self.shoe.bounding_box()
        # Ears overhang the body toward +x.
        for actual, expected in (
            (box.min.X, -self.p.width / 2),
            (box.max.X, ear_x_end(self.p)),
            (box.min.Y, -self.p.length / 2),
            (box.max.Y, self.p.length / 2),
            (box.min.Z, -self.p.skirt_depth),
            (box.max.Z, self.p.collar_top),
        ):
            self.assertAlmostEqual(actual, expected, places=5)

    def test_post_disc_and_rail_do_not_intersect_abs(self):
        for name, reference in reference_parts(self.p).items():
            with self.subTest(name=name):
                self.assertLess((self.shoe & reference).volume, 1e-7)

    def test_post_bore_diameter(self):
        # Face.radius is None for trimmed cylindrical surfaces (a fillet face here).
        radii = [f.radius for f in self.shoe.faces().filter_by(GeomType.CYLINDER) if f.radius is not None]
        self.assertTrue(any(abs(r - self.p.post_bore / 2) < 1e-7 for r in radii))

    def test_m5_side_channel_holes(self):
        for x in (-self.p.width / 2 + 1, self.p.width / 2 - 1):
            self.assertFalse(self.shoe.is_inside((x, 0, -10)))
            self.assertTrue(self.shoe.is_inside((x, 4, -10)))

    def test_split_is_open_above_rounded_termination(self):
        p = self.p
        x = 9.0  # Collar wall, between post bore and collar outer radius.
        self.assertFalse(self.shoe.is_inside((x, 0, 18)))
        self.assertFalse(self.shoe.is_inside((x, 0, p.split_relief_z)))
        self.assertTrue(self.shoe.is_inside((x, 0, p.split_relief_z - p.split_relief_radius - 0.25)))

    def test_clamp_screw_and_nut_fit(self):
        p = self.p
        x, z = clamp_axis_xz(p)
        screw_outer_y = -p.split_gap / 2 - p.screw_ear_thickness
        nut_outer_y = p.split_gap / 2 + p.nut_ear_thickness
        screw = along_y((x, screw_outer_y, z)) * Cylinder(1.5, p.clamp_screw_length, align=ON_FLOOR)
        self.assertLess((self.shoe & screw).volume, 1e-7)
        nut = extrude(
            along_y((x, nut_outer_y - p.nut_pocket_depth, z))
            * RegularPolygon(p.clamp_nut_across_flats / cos(pi / 6) / 2, 6),
            amount=p.clamp_nut_thickness,
        )
        self.assertLess((self.shoe & nut).volume, 1e-7)

    def test_fabrication_clearance_can_be_changed(self):
        variant = build_rail_shoe(
            replace(self.p, post_diametral_clearance=0.10, rail_lateral_clearance_per_side=0.10)
        )
        self.assertTrue(variant.is_valid)

    def test_rejects_shim_interference(self):
        with self.assertRaises(ValueError):
            build_rail_shoe(replace(self.p, datum_counterbore_depth=0.1))

    def test_bridge_length_and_rail_top_seating(self):
        cut = section(self.shoe, Plane.XY.offset(2)).bounding_box()
        self.assertAlmostEqual(cut.size.Y, 30.0, places=5)
        for y in (-13, 13):
            for x in (-7, 7):
                self.assertFalse(self.shoe.is_inside((x, y, -0.01)))
                self.assertTrue(self.shoe.is_inside((x, y, 0.01)))

    def test_counterbore_clearance_and_roof(self):
        p = self.p
        cavity = Cylinder(p.datum_counterbore_diameter / 2, p.datum_counterbore_depth, align=ON_FLOOR)
        self.assertLess((self.shoe & cavity).volume, 1e-7)
        self.assertTrue(self.shoe.is_inside((0, 9, p.datum_counterbore_depth + 0.01)))
        self.assertAlmostEqual(p.datum_counterbore_diameter, 20.05)
        self.assertLess(p.datum_counterbore_diameter, p.rail_opening)
        self.assertAlmostEqual(p.datum_counterbore_depth, 1.0)

    def test_reference_parts_viewer_group(self):
        assembly = viewer_assembly(self.shoe, self.p)
        groups = {child.label: child for child in assembly.children}
        self.assertEqual(set(groups), {"Rail shoe", "Reference parts"})
        self.assertEqual(
            [child.label for child in groups["Reference parts"].children],
            [
                "Rail",
                "Datum disc",
                "TR50 M post",
                "Shoe clamp screw",
                "Shoe clamp nut",
                "Shoe side screw washer left",
                "Shoe side screw left",
                "Shoe side screw washer right",
                "Shoe side screw right",
            ],
        )

    def test_side_screws_seat_on_washers_at_the_side_holes_and_reach_the_t_nuts(self):
        # Measured slot (design §4.1), not the generic profile.
        p, rail = self.p, RailProfile(slot_depth=6.45, lip_thickness=1.65)
        parts = reference_children(self.shoe, p)
        for side, name in ((-1, "left"), (1, "right")):
            with self.subTest(side=name):
                washer = parts[f"Shoe side screw washer {name}"].bounding_box()
                screw = parts[f"Shoe side screw {name}"].bounding_box()
                self.assertAlmostEqual(
                    abs(washer.min.X) if side < 0 else washer.max.X, p.width / 2 + 1.0, places=4
                )
                self.assertAlmostEqual(screw.center().Z, -p.rail_height / 2, places=4)
                self.assertAlmostEqual(screw.center().Y, 0.0, places=4)
                # Head against the washer's outer face; the tip passes the slot lip and stops short of the floor.
                head_end = screw.min.X if side < 0 else screw.max.X
                bearing = head_end - side * MCMASTER_92290A_HEAD_HEIGHT
                self.assertAlmostEqual(bearing, washer.min.X if side < 0 else washer.max.X, places=4)
                tip = screw.max.X if side < 0 else screw.min.X
                entry = -side * (tip - side * p.rail_width / 2)
                self.assertGreater(
                    entry, rail.lip_thickness + 3.0
                )  # Through the thickness of a roll-in T-nut.
                self.assertLess(entry, rail.slot_depth - 0.5)
                for part in (parts[f"Shoe side screw washer {name}"], parts[f"Shoe side screw {name}"]):
                    self.assertLess((self.shoe & part).volume, 1e-6)

    def test_split_clamp_screw_and_nut_sit_in_their_ears(self):
        p = self.p
        parts = reference_children(self.shoe, p)
        screw, nut = parts["Shoe clamp screw"].bounding_box(), parts["Shoe clamp nut"].bounding_box()
        self.assertAlmostEqual(screw.center().X, p.clamp_axis_x, places=4)
        self.assertAlmostEqual(screw.center().Z, p.clamp_axis_z, places=4)
        self.assertAlmostEqual(nut.center().X, p.clamp_axis_x, places=4)
        self.assertAlmostEqual(nut.center().Z, p.clamp_axis_z, places=4)
        # Head on the screw ear's outer face; nut on the pocket bottom, with the screw reaching through it.
        self.assertAlmostEqual(screw.min.Y + MCMASTER_91292A114_HEAD_HEIGHT, p.clamp_screw_outer_y, places=4)
        self.assertAlmostEqual(nut.min.Y, p.clamp_nut_outer_y - p.nut_pocket_depth, places=4)
        self.assertGreater(screw.max.Y, nut.max.Y)
        for label in ("Shoe clamp screw", "Shoe clamp nut"):
            self.assertLess((self.shoe & parts[label]).volume, 1e-6)

    def test_viewer_post_is_vendor_model_seated_on_datum_disc(self):
        p = self.p
        references = viewer_assembly(self.shoe, p).children[1]
        post = {child.label: child for child in references.children}["TR50 M post"]
        body = max(post.solids(), key=lambda s: s.volume).bounding_box()  # Not the stud.
        self.assertAlmostEqual(body.min.Z, p.datum_disc_thickness, places=5)
        self.assertAlmostEqual(body.size.X, p.post_diameter, delta=TR50_MODEL_ROUNDING)
        self.assertAlmostEqual(body.center().X, 0, places=5)
        self.assertAlmostEqual(body.center().Y, 0, places=5)


if __name__ == "__main__":
    unittest.main()

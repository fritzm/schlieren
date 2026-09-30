"""Clearance checks for the urgent-build finger-holder alternative."""
import unittest
import cadquery as cq
from schlieren.parts.carriage_2 import Carriage2Parameters, build_carriage_2, cassette_location
from schlieren.parts.cassette import build_cassette_assembly


class Carriage2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=Carriage2Parameters()
        cls.h=build_carriage_2(cls.p).val()
        cls.c=build_cassette_assembly().toCompound()

    def test_single_solid(self):
        self.assertTrue(self.h.isValid())
        self.assertEqual(len(self.h.Solids()),1)

    def test_cassette_hardware_and_loading(self):
        for angle in (0,90,180,270):
            for travel in (-5,0,5,20,40,60):
                cassette=self.c.moved(cassette_location(self.p,travel,angle))
                self.assertLess(self.h.intersect(cassette).Volume(),1e-6,(angle,travel))

    def test_post_and_optical_clearance(self):
        p=self.p
        post=cq.Solid.makeCylinder(6.35,50,cq.Vector(0,0,-50))
        beam=cq.Solid.makeCylinder(12,60,cq.Vector(0,-20,p.axis_z),cq.Vector(0,1,0))
        for shape in (post,beam):
            self.assertLess(self.h.intersect(shape).Volume(),1e-6)
        self.assertAlmostEqual(p.post_top+p.axis_z,72.35)

    def test_adjuster_clearance_and_reach(self):
        p=self.p
        for travel in (-5,0,5):
            tip=p.magnet_z+travel
            screw=cq.Solid.makeCylinder(6.35/2,p.adjuster_length,
                  cq.Vector(0,p.adjuster_y,tip-p.adjuster_length))
            self.assertLess(self.h.intersect(screw).Volume(),1e-6)
            self.assertGreater(tip,p.support_top)
            self.assertLess(tip-p.adjuster_length,p.support_bottom)
            self.assertGreater(tip-p.adjuster_length+p.post_top,0)

    def test_pressure_screws(self):
        p=self.p
        for sign in (-1,1):
            screw=cq.Solid.makeCylinder(1.5,12,cq.Vector(sign*32,p.screw_y,p.axis_z),cq.Vector(sign,0,0))
            head=cq.Solid.makeCylinder(2.75,3,cq.Vector(sign*44,p.screw_y,p.axis_z),cq.Vector(sign,0,0))
            for shape in (screw,head):
                self.assertLess(self.h.intersect(shape).Volume(),1e-6)


if __name__=='__main__':
    unittest.main()

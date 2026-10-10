"""Catalog dimensions of the purchased hardware that more than one model depends on.

These are manufacturer specifications (or, where noted, measurements of the parts in hand), not committed
project dimensions: a part module takes them as the defaults of its own parameters and adds its fabrication
allowances there. Hardware used by a single model keeps its dimensions with that model. The matching STEP
models and their mounting frames are in `vendor_cad.py`.
"""

from schlieren.standards import INCH
from schlieren.vendor_cad import MCMASTER_91292A114_HEAD_HEIGHT, MCMASTER_91828A211_HEIGHT

# N52 bar magnet, Amazon B0DMCY4FN1 (10 mm L x 5 mm W x 2 mm H): the hard bearing pad under each adjuster tip.
MAGNET_LENGTH = 10.0
MAGNET_WIDTH = 5.0
MAGNET_THICKNESS = 2.0

# Thorlabs FAS100 fine adjustment screw: 1/4"-80, 1.00 in of thread from the knob shoulder to the ball tip.
FAS100_THREAD_DIAMETER = 0.25 * INCH
FAS100_THREAD_LENGTH = 1.00 * INCH
FAS100_PITCH = INCH / 80

# McMaster 98625A950 1/4"-80 brass insert (manufacturer drawing, §8.3).
INSERT_98625A950_BODY_DIAMETER = 0.313 * INCH
INSERT_98625A950_LENGTH = 0.313 * INCH  # Overall: the conservative thread-engagement envelope.
INSERT_98625A950_BODY_LENGTH = 0.298 * INCH  # Under the flange.
INSERT_98625A950_MIN_MATERIAL = 0.298 * INCH  # Minimum material the drawing calls for around the body.
INSERT_98625A950_FLANGE_DIAMETER = 0.352 * INCH
INSERT_98625A950_FLANGE_THICKNESS = 0.010 * INCH

# McMaster 2006N292 compression spring.
SPRING_2006N292_FREE_LENGTH = 25.5
SPRING_2006N292_OUTER_DIAMETER = 0.272 * INCH  # Measured (calipers), in-hand spring.
SPRING_2006N292_WIRE_DIAMETER = 0.63  # Catalog; display only.

# Common M3 hardware: McMaster 91292A114 M3 x 12 socket head screw and 91828A211 hex nut.
M3_CLEARANCE_DIAMETER = 3.3  # Printed clearance hole for the common M3 screw.
M3_SOCKET_HEAD_DIAMETER = 5.5
M3_SOCKET_HEAD_HEIGHT = MCMASTER_91292A114_HEAD_HEIGHT
M3_NUT_ACROSS_FLATS = 5.5
M3_NUT_THICKNESS = MCMASTER_91828A211_HEIGHT

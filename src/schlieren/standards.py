"""Project-wide dimensional standards (design §3.4 and the common post stack).

Only values that more than one part model depends on live here. Part-specific dimensions and fabrication
allowances stay with their part.
"""

INCH = 25.4  # mm.

# The two rails, as the sign of x in a §3.4 rail frame toward which a fixture's outboard side lies (away from
# the other rail): the source rail is the left one, the imaging rail the right one.
SOURCE_SIDE = -1
IMAGING_SIDE = 1

# Frozen project datum (§3.4): the optical axis above the rail top.
OPTICAL_HEIGHT = 72.35

# The common post stack (§5): a Thorlabs TR50/M post standing on a 0.010 in datum shim on the rail top. TR50/M
# is metric-primary; its STEP model is rounded to inches (1.969 in, 0.499 in), so these nominals are exact.
DATUM_SHIM_THICKNESS = 0.010 * INCH
DATUM_SHIM_DIAMETER = 0.75 * INCH
POST_LENGTH = 50.0
POST_DIAMETER = 12.7

# The printed spigot interface of the slit stage plate and the cutoff carriage (§7.5, §8.1): a hollow spigot at
# the SM1 tube OD, clamped by a Thorlabs SM1RC/M split ring (Ø1.21 in bore), against a shoulder the ring seats on.
SM1_TUBE_DIAMETER = 1.20 * INCH
SM1RC_M_BORE = 1.21 * INCH
SPIGOT_SHOULDER_DIAMETER = 34.0  # Bears on the SM1RC/M face outside its Ø30.7 mm bore.

# PLA (provisional): typical flexural modulus, for first-order flexure and keeper estimates.
PLA_MODULUS = 3000.0  # MPa

# Printed hex-nut pockets: across-flats allowance over the nut, as fit-tested on the common rail shoe.
NUT_POCKET_ACROSS_FLATS_CLEARANCE = 0.3

# Printed rectangular magnet pockets: allowance over the magnet's length and width, in total across each (half
# on a side). As fit on the lens-cradle pads; the carriage and slit head take the same value.
MAGNET_POCKET_CLEARANCE = 0.20

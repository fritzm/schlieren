"""Project-wide dimensional standards (design §3.4 and the common post stack).

Only values that more than one part model depends on live here. Part-specific dimensions and fabrication
allowances stay with their part.
"""

INCH = 25.4  # mm.

# Frozen project datum (§3.4): the optical axis above the rail top.
OPTICAL_HEIGHT = 72.35

# The common post stack (§5): a Thorlabs TR50/M post standing on a 0.010 in datum disc on the rail top.
# TR50/M is metric-primary; its STEP model is rounded to inches (1.969 in, 0.499 in), so these nominals are exact.
DATUM_DISC_THICKNESS = 0.010 * INCH
DATUM_DISC_DIAMETER = 0.75 * INCH
POST_LENGTH = 50.0
POST_DIAMETER = 12.7

# PLA (provisional): typical flexural modulus, for first-order flexure and keeper estimates.
PLA_MODULUS = 3000.0  # MPa

# Printed hex-nut pockets: across-flats allowance over the nut, as fit-tested on the common rail shoe.
NUT_POCKET_ACROSS_FLATS_CLEARANCE = 0.3

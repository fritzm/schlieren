"""Viewer colors shared by the part models, as (r, g, b) in 0-1.

Every color the part models use is named here, so a part reads the same in every assembly and figure and
near-duplicates are easy to see. Grouped by what the color stands for, not by which model uses it.
"""

# Purchased metal.
METAL = (0.75, 0.75, 0.78)  # Stainless: posts, screws, nuts, washers, springs; also aluminum extrusion.
STEEL = (0.6, 0.6, 0.62)  # Magnets and adjuster screws.
BRASS = (0.8, 0.65, 0.25)  # Heat-set inserts and bushings.
BLACK_ANODIZED = (0.2, 0.2, 0.22)  # Black-anodized aluminum (Thorlabs SM1 optomechanics).
BLACK_OXIDE = (0.13, 0.13, 0.14)  # Black-oxide fasteners and nylocs.
HARDWARE_GRAY = (0.7, 0.7, 0.72)  # Plated hardware: springs, screws, nuts.

# Adjusters.
KNOB_BLACK = (0.16, 0.16, 0.17)  # Thorlabs FAS100 knob.
INDEX_DIMPLE = (0.95, 0.95, 0.95)  # FAS100 index dimple.

# Non-metals.
RUBBER = (0.15, 0.15, 0.15)  # EPDM and rubber pads.
PLYWOOD = (0.82, 0.68, 0.45)

# Printed parts. A fixture's printed parts take distinct colors so they can be told apart.
PRINTED_ORANGE = (0.8, 0.4, 0.25)  # The common rail shoe, and printed parts that stand in for it.
PRINTED_BLUE = (0.35, 0.6, 0.8)

# Printed parts, continued: the hues the carriage, cassette and camera support use to tell their parts apart.
PRINTED_GREEN = (0.4, 0.75, 0.5)
PRINTED_GRAY = (0.65, 0.65, 0.7)
PRINTED_SKY = (0.6, 0.75, 0.8)
PRINTED_INDIGO = (0.35, 0.5, 0.75)
PRINTED_AMBER = (0.85, 0.65, 0.25)
PRINTED_AZURE = (0.3, 0.55, 0.8)
PRINTED_DENIM = (0.3, 0.5, 0.7)
QR_PLATE_DARK = (0.16, 0.16, 0.18)  # Mirror-cell quick-release plate.

# Metals, continued.
STEEL_GRAY = (0.6, 0.6, 0.6)  # Frame hardware and reference rails; a touch neutral against STEEL.
STAINLESS = (0.72, 0.73, 0.75)
BUSHING_BRASS = (0.75, 0.62, 0.3)
KNOB_SILVER = (0.78, 0.78, 0.8)
BRACKET_ALUMINUM = (0.7, 0.72, 0.75)

# Non-metals and optics.
SORBOTHANE = (0.25, 0.2, 0.3)
NYLON = (0.92, 0.92, 0.85)
RTV = (0.92, 0.92, 0.88)
GLASS = (0.7, 0.85, 0.95, 0.5)  # Translucent: lenses.
MIRROR_GLASS = (0.55, 0.78, 0.9)
SOLDER_MASK_WHITE = (0.92, 0.92, 0.9)
LED_YELLOW = (0.95, 0.9, 0.6)
PHONE_BODY = (0.25, 0.27, 0.32)
LENS_BLACK = (0.12, 0.12, 0.13)
FOCUS_RING_GRAY = (0.3, 0.3, 0.33)
BAND_RED = (0.85, 0.3, 0.25)  # Elastic retaining band.
AXIS_RED = (0.9, 0.1, 0.1)  # Optical-axis marker line.

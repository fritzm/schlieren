"""Vendor-supplied CAD models of purchased parts, stored in cad/vendor/ (see the README there).

Models are manufacturer geometry for viewing and clearance checks; committed or measured dimensions in
docs/design/ and the part parameter classes remain authoritative. Each part helper returns the model moved
from the vendor's frame into a documented mounting frame, so callers place it with a translation.
"""

from functools import cache
from pathlib import Path

import cadquery as cq

VENDOR_CAD_DIR = Path(__file__).resolve().parents[2] / "cad" / "vendor"
INCH = 25.4

# Vendor-frame features used for placement (Thorlabs drawings are inch-primary).
SM1CP2M_SEAT_Y = 0.110 * INCH  # Flange seat face (thread shoulder) above the knurled back face.


@cache
def vendor_step(filename: str) -> cq.Workplane:
    """Import a single-part vendor STEP file (millimeters), in the vendor's own coordinate frame.

    cq.Assembly.importStep rejects single-part files, so this flattens to one compound. Callers place the
    result with a cq.Location when adding it to an assembly; the cached object must not be modified.
    """
    return cq.importers.importStep(str(VENDOR_CAD_DIR / filename))


def _moved(filename: str, loc: cq.Location) -> cq.Workplane:
    return cq.Workplane().add(vendor_step(filename).val().moved(loc))


@cache
def thorlabs_tr50_m() -> cq.Workplane:
    """Thorlabs TR50/M post with its M4 setscrew stud; axis +Z, post base at the origin."""
    return _moved("Thorlabs-TR50-M.step", cq.Location((0, 0, 0), (1, 0, 0), 90))


@cache
def thorlabs_smr1_m() -> cq.Workplane:
    """Thorlabs SMR1/M ring; optical axis +Y through the origin, faces at y=0 and y=thickness, post seat -Z."""
    return _moved("Thorlabs-SMR1-M.step", cq.Location((0, 0, 0), (1, 0, 0), 90))


@cache
def thorlabs_sm1cp2m() -> cq.Workplane:
    """Thorlabs SM1CP2M end cap; axis +Y through the origin, flange seat face at y=0, thread toward +Y."""
    return _moved("Thorlabs-SM1CP2M.step", cq.Location((0, -SM1CP2M_SEAT_Y, 0)))

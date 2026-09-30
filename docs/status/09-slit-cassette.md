## 9. Source-slit cassette

The source slit uses two Stanley 11-515 backed single-edge scraper blades.

Measured physical blade dimensions:

- length: 1.535 in / 38.99 mm
- width: 0.768 in / 19.51 mm
- thickness at the sharp/flat portion: 0.010 in / 0.254 mm
- thickness at the folded spine: 0.040 in / 1.016 mm

The cassette does not use blade pockets or attempt to compensate for the folded spine. Each blade is simply
pinched against the cassette front face by an identical removable clamp bar. A slight inclination of the blade
from its folded spine toward its cutting edge is acceptable; the optically important geometry is the gap and
parallelism of the two cutting edges.

Slit setup:

- the two blade clamps are mechanically identical;
- in use, one blade is normally left fully clamped as the working datum;
- the other clamp is loosened enough to permit blade translation;
- a true-metric feeler gauge between the cutting edges establishes slit gap and parallelism;
- the movable blade is pressed gently against the gauge along its length and its clamp is progressively
  tightened.

Likely operating slit widths:

- 0.10 mm
- 0.15 mm
- 0.20 mm
- 0.25–0.30 mm

Likely practical starting region: 0.15–0.20 mm.

Common clamp bars:

- two identical printed rigid ABS bars may be fitted to a cassette;
- each bar uses two fasteners, one toward each end, so clamp force is distributed along the element;
- no holes are made through razor blades, filter material, or other optical elements;
- no blade-specific locating pocket or guide is required;
- McMaster 9852N37 adhesive-backed 1/32 in, 60A solid EPDM is applied to the removable clamp-bar face to
  provide compliance and friction;
- the bar should bear primarily on the broad flat portion of a razor blade rather than relying on the folded
  spine for its clamp datum;
- the same clamp-bar geometry is intended to hold razor knife edges, Roscolux gel/filter material, Photofoil,
  and similar thin sheet cutoff elements.

Clamp-bar fastening is from the cassette rear/datum face toward the optical/front face so no screw ends or
nuts can protrude from the sliding/datum surface. Fasteners are positioned outside the optical-element
footprint where practical; the clamp bar spans and pinches the element against the cassette front face. At
each fastener, use:

flush M3 countersunk flat-head screw → 5 mm cassette body → printed clamp bar → M3 flat washer → ordinary M3
hex nut

The M3 flat-head screw is seated fully flush or very slightly below the rear cassette face and retained in its
countersink with a small CA tack using McMaster 1818A45 / Loctite 4061. The CA serves only to keep the screw
captive and resist rotation while the front-side nut is adjusted; it is not relied upon as the structural
clamp load path. The ordinary M3 nut remains exposed and accessible on the front of the clamp bar. Place the
washer between the nut and printed bar. Do not use prevailing-torque/nyloc nuts or threadlocker here.

### Provisional cassette clamp-bar hardware selection

Provisionally frozen for procurement, with 12 screws, 12 washers, and 12 nuts allocated in the BOM:

| Component | Selected McMaster part | Specification | Procurement allocation |
|---|---|---|---|
| Flat-head screw | [92125A133](https://www.mcmaster.com/92125A133/) | M3 × 0.5 × 14 mm, fully threaded 18-8 stainless, 90° countersunk head; 6 mm head diameter, 1.7 mm head height, 2 mm hex drive | 12 required; one 100-pack |
| Flat washer | [93475A210](https://www.mcmaster.com/93475A210/) | 18-8 stainless, 3.2 mm ID × 7 mm OD × 0.4–0.6 mm thick; DIN 125 / ISO 7089 | 12 required; one 100-pack |
| Ordinary full-height hex nut | [91828A211](https://www.mcmaster.com/91828A211/) | M3 × 0.5, 18-8 stainless, 5.5 mm across flats × 2.4 mm high; DIN 934 | 12 required; share the split-clamp 100-pack, not a second pack |

Use a 4 mm nominal printed ABS clamp-bar thickness as the initial CAD target. Provide approximately 3.3–3.4 mm
screw clearance holes, a 90° countersink matched to the selected screw head, and a flat washer bearing area at
least 7.2 mm across. Keep the fasteners, bars, nuts, cleats, and projecting front-side screw ends clear of the
24 mm optical aperture and carriage interfaces. For cassette CAD, model these as rear-face 90° countersinks
sized for the selected McMaster 92125A133 M3 × 0.5 × 14 mm flat-head screws: nominal head diameter 6 mm and
head height 1.7 mm. The screw head must finish flush with or slightly below the rear/datum face so it cannot
contact the carriage datum pins or interfere with cassette sliding. Treat the 3.3–3.4 mm through-hole and 90°
countersink as explicit features of the universal cassette blank, not blade-specific geometry.

The 14 mm screw length remains provisional until the first printed cassette/bar assembly is fit-tested.
Because the clamp fasteners need not pass through the optical element, do not size the screw from a
blade-thickness stack. Confirm full nut engagement, useful clamp travel for razor blades and thin filter/foil
media, and a flush or recessed rear head on the printed prototype before treating 14 mm as final.

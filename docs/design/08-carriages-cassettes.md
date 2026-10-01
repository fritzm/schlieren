## 8. Source-slit and cutoff carriage system

The slit and cutoff use mechanically identical carriage architecture.

### 8.1 SM1 tube and rotation interface

Each carriage uses:

- 1 × Thorlabs SM1RC/M
- 1 × Thorlabs SM1L15
- printed split-clamp carriage around the smooth exterior of the tube
- separate printed split retaining ring on the opposite side

Each of the two printed carriage-body split clamps uses the common clamp hardware:

M3 socket-head screw → clearance through one ear → captured M3 hex nut in the opposite ear.

For the carriage-body clamp around the smooth SM1L15 exterior, use a more compliant flexure-collar variant
rather than simply scaling the common rail-shoe split boss. The broad carriage body would otherwise make a
plain split bore relatively stiff and concentrate deformation near the clamp split.

Carriage clamp CAD starting concept:

- retain the radial split between opposed M3 clamp ears, with a rounded relief termination at the inner end of
  the split;
- add a partial circumferential / annular relief slit around the SM1 bore so the clamping band is locally
  decoupled from the rigid carriage body;
- do not make the annular slit a complete circle: retain a substantial unslit ligament opposite the radial
  split so the clamp band remains positively located and the carriage cannot rock on a nearly free ring;
- provisional clamp-band radial thickness approximately 4–5 mm;
- provisional annular-relief width approximately 1.0–1.5 mm;
- provisional relieved arc approximately 220–270°, leaving roughly 90–140° of connected structural/flexure
  sector opposite the split;
- use generous fillets at the remaining ligament and wherever the clamp band transitions into the carriage
  body;
- keep the SM1 bore free-fitting before tightening, and rely on modest elastic closure of the relieved band
  rather than high M3 screw preload.

The purpose of the annular relief is to obtain more uniform circumferential clamping of the smooth SM1 tube
with lower screw force and less local ABS strain. The remaining ligament must still be stiff enough to resist
carriage rocking and maintain the cassette mechanism relative to the optical axis. Exact slit arc, width,
ligament angle, and band thickness remain CAD/prototype fit parameters rather than frozen dimensions.

No printed SM1 threads are required.

The SM1RC/M provides the rotational bearing and lock. When loosened, the tube and carriage rotate together.

Required carriage rotation:

- at least ±90°
- preferably ±100–120°

Define nominal zero as:

- slit/cutoff line horizontal;
- fine-adjust translation vertical;
- fine adjuster pointing upward.

Fore/aft optical positioning is done by moving the rail shoe, not by sliding the SM1L15 through the carriage.

### 8.2 SM1L15 retaining ring — CAD ready

The retaining ring is a light-duty printed ABS split ring whose sole purpose is axial retention of the
carriage tube.

Baseline geometry:

- axial width approximately 4–5 mm
- radial wall thickness approximately 3–4 mm
- single split
- opposed ears at the split
- approximately 1–2 mm unclamped split gap
- small fillets where ears join the ring

Clamping hardware for each of the two retaining rings uses the same common arrangement:

M3 socket-head screw → clearance through one ear → captured M3 hex nut in the opposite ear.

The nut pocket prevents rotation during tightening; a nyloc is not required for this printed clamp joint.

### 8.3 Fine adjustment

Each carriage uses:

- 1 × Thorlabs FAS100, 1/4 in-80 × 1.00 in
- 1 × McMaster 98625A950 brass 1/4 in-80 insert
- 1 × McMaster 2006N292 compression spring

Authoritative insert geometry for CAD: use McMaster-Carr part 98625A950 exactly as shown in the uploaded
manufacturer drawing “98625A950_0.313 Long Brass Insert for 1-4 -80 Thread Ultra-Fine-Thread Ball-Point Set
Screw.pdf.” Do not substitute dimensions from a generic 1/4 in-80 insert model. The drawing gives: internal
thread 1/4 in-80; body outside diameter 0.313 in (7.950 mm); overall axial length 0.313 in (7.950 mm);
under-flange/body length 0.298 in (7.569 mm); flange outside diameter 0.352 in (8.941 mm); flange thickness
0.010 in (0.254 mm); specified drill-bit size 0.313 in (7.950 mm); and minimum material thickness 0.298 in
(7.569 mm). The 0.352 in dimension is the flange OD, not the bore or insert-body OD.

For the carriage CAD, make the adjuster insert bore nominally 0.313 in (7.950 mm), matching the McMaster
drawing. The physical printed bore should be treated as a pilot and finished to the required size after
printing rather than relying on FDM dimensional accuracy. A 5/16 in drill is 0.3125 in and is therefore only
0.0005 in smaller than the drawing's nominal 0.313 in drill size; if used in fabrication, fit-test on scrap or
the first prototype before committing the production carriage. Provide at least the drawing's 0.298 in (7.569
mm) minimum material thickness through the insert-support boss; approximately 8 mm boss thickness remains a
sensible CAD target. Put the flange on the adjuster/outboard side so the axial reaction from the FAS100 tends
to seat the flange against the carriage. No flange recess is required by the part geometry; if a flush face is
desired, the flange recess need only accommodate the 0.010 in (0.254 mm) flange thickness and 0.352 in (8.941
mm) OD. Maintain approximately 3–4 mm minimum radial ABS wall outside the 0.313 in insert body where
practical; a local boss around 14–16 mm OD remains a reasonable starting range. Exact retention/fit in printed
ABS should be established by prototype fit rather than by changing the authoritative insert envelope.

FAS100 / insert travel envelope for CAD: the FAS100 uses a 1.000 in (25.4 mm) long 1/4 in-80 adjuster screw.
The 80 TPI pitch gives 0.0125 in (0.3175 mm) axial motion per revolution. Using the insert's 0.313 in overall
axial envelope as a conservative full-engagement allowance leaves approximately 0.687 in (17.45 mm) of
theoretical screw motion. Treat that as a geometric clearance estimate, not a published FAS100 travel
specification or a required operating stroke. For CAD, preserve approximately 15–16 mm of unobstructed
adjuster/plunger clearance so the mechanism does not depend on either end stop. The carriage's intended
working translation remains approximately ±5 mm / 10 mm total, leaving useful adjuster margin.

The FAS100 ball tip should not bear directly on printed ABS. Each FAS100-driven plunger receives a small hard
bearing insert made from a nickel-plated rectangular NdFeB magnet:

- Amazon B0DMCY4FN1
- N52 Bar Magnet - 10 mm L × 5 mm W × 2 mm H
- one magnet per driven plunger; 2 used across the two carriages

The magnet is used primarily as a hard, wear-resistant plated bearing surface; its magnetic function is
incidental. Capture it in a close-fitting printed pocket with its rear face fully supported by ABS. Prefer
mechanical capture by pocket geometry, with only a small CA or epoxy tack if retention is needed. The FAS100
ball should contact the broad plated face rather than bare ABS.

### 8.4 Cassette seating

Cassette motion is controlled by opposed plungers:

- fine adjuster on one side;
- spring-loaded plunger opposite;
- three fixed rear datum contacts on the carriage define the cassette optical plane;
- shallow cassette/plunger bevels generate axial seating force against the datum contacts.

The three rear datum contacts are McMaster 97936A109 brass escutcheon pins / decorative finishing nails, used
head-first as small domed sliding contacts. Each carriage uses three pins, for six installed pins total across
the two slit/cutoff carriages. The selected pin is approximately 3/8 in long, with a 0.050 in (1.27 mm) smooth
shank and 1/8 in (3.18 mm) domed head.

Mount each pin through a close-fitting through-hole in the printed carriage with the domed brass head on the
cassette side. Seat the underside of the head firmly against the carriage datum face so datum height is
established mechanically rather than by adhesive thickness. Wick a small amount of CA around the shank from
the back for retention, then flush-cut and dress the projecting shank at the back of the carriage. Keep CA out
from beneath the head/contact surface.

The three pin heads should form a broad triangular support pattern around the optical aperture. The cassette
rear face remains the sliding datum surface and should provide unobstructed swept tracks over the three domed
contacts throughout the fine-adjust travel. Exact pin coordinates are to be frozen in carriage CAD. When
choosing the brass tack datum locations, explicitly avoid placing any datum contact in the swept track of the
rear M3 clamp-screw heads/countersinks over the full cassette linear-adjustment range. The datum tracks should
remain on uninterrupted printed rear-face material for all intended cassette positions.

The plunger bodies are constrained to the intended translation axis by ears/tabs riding in slotted guiding
rails. The guide slots prevent unwanted lateral movement or rotation while permitting the required axial
plunger travel.

The guide-slot design must include an explicit plunger assembly path. A fully integral closed slot is awkward
because the two longitudinal ends of the guide path are occupied by the FAS100 adjuster support on one side
and the spring/retractor-rod guide structure on the other. The current CAD approach is therefore to print the
plunger guide tracks open from the cassette-loading side, install the plungers into those tracks, and close
only the guide-ear regions with a separate printed keeper frame.

The keeper is a perimeter frame, not a solid lid: the central upper aperture must remain open for cassette
insertion and removal. Its side members span the plunger guide tracks and retain the guide ears against upward
escape while the printed track walls carry the lateral guidance loads. The frame may be locally scalloped or
notched where the FAS100 adjuster axis and spring/retractor-rod guide intersect its envelope, provided the
material directly over the swept guide-ear paths and the load paths to the fasteners remain intact.

Keeper retention is mechanical. Use four corner fasteners per carriage. The baseline fastener is the existing
common McMaster 91292A114 M3 × 0.5 × 12 mm socket-head screw with McMaster 91828A211 full-height M3 × 0.5 hex
nut (5.5 mm across flats × 2.4 mm high); eight screws and eight nuts are required across the two carriages.
With the provisional 4.0 mm back plate and 3.0 mm keeper-frame thickness, start CAD with an approximately 0.5
mm-deep socket-head recess in the keeper and an approximately 2.5 mm-deep captive hex pocket opening from the
carriage-plate back. This leaves approximately 1.5 mm of ABS above the nut pocket and gives nearly full use of
the 12 mm screw length, with only slight nominal screw projection beyond the nut. Exact recess depths should
be tuned from printed fit rather than treated as frozen dimensions. The keeper should seat on broad printed
lands or shoulders so the fasteners clamp it against the carriage rather than suspending it between four
isolated points. CA is no longer the baseline keeper-retention method. Exact frame-member widths,
fastener-boss geometry, and final vertical stack dimensions remain provisional pending carriage CAD fit-up.

Provisional CAD starting dimensions for the vertical guide stack are: 4.0 mm carriage back plate thickness;
approximately 2.0 mm rise from the plate front to the lower guide-ear running surface; 3.0 mm plunger
guide-ear thickness in an approximately 3.3–3.4 mm guide channel; and approximately 3.0 mm keeper-frame
thickness. These are first-print fit targets rather than frozen dimensions. The exact datum-pin projection,
plunger-body height, keeper-frame member widths, and local scallops around the FAS100 and spring-guide axes
remain to be finalized in CAD.

Use a very light film of plastic-safe lubricant on the ABS-on-ABS sliding interfaces, particularly the plunger
ears/tabs in their guide slots and any other plunger sliding faces. The selected lubricant is McMaster 1418K51
clear silicone grease, NLGI 1. Smooth/dress the printed sliding surfaces first, apply only a trace amount,
cycle the mechanism, and wipe away visible excess so the lubricant acts as a thin boundary film rather than a
grease-packed slide. Keep lubricant away from CA/epoxy/RTV bonding surfaces and apply it only after nearby
adhesive work is complete. Only a trace boundary film is required; avoid excess lubricant that can collect
dust or migrate.

Tentative bevel angle is 25–30°. The angle reference convention is not yet frozen; the keeper-load estimate
below assumes the angle is measured from the cassette plane.

Approximately 1–1.5 mm of cassette thickness may participate in the bevel.

For keeper-frame sizing, McMaster lists the 2006N292 spring rate as 0.14 lbf/mm. At the frozen 9 mm fiducial
compression this corresponds to approximately 5.6 N of in-plane plunger force; at the 14 mm most-compressed
end of normal travel it is approximately 8.7 N. If the tentative 25–30° bevel is interpreted as an angle from
the cassette plane, a frictionless first-order wedge model gives approximately 9.7–12.0 N upward reaction per
plunger at fiducial and approximately 15.1–18.7 N per plunger at maximum normal compression. These reactions
are carried upward through the plunger ears into the keeper frame. Use approximately 20 N per plunger as the
current working-load scale before safety margin. The exact seating-force calculation remains provisional until
the bevel-angle reference convention and sliding-friction assumption are frozen.

### 8.5 Spring-plunger anti-buckling guide — frozen

The spring-loaded plunger uses a McMaster 91273A377 18-8 stainless shoulder screw as the coaxial anti-buckling
guide and cassette-retract handle.

Frozen guide hardware and geometry:

- shoulder diameter: 4 mm;
- shoulder length: 45 mm;
- threaded end: M4 × 0.7;
- quantity: 2, one per carriage;
- the M4 threaded end attaches axially to the printed spring plunger;
- the 4 mm shoulder passes through the compression-spring ID and through a clearance guide hole in the
  stationary rear carriage structure;
- use approximately 4.2–4.3 mm rear-guide-hole diameter as the CAD starting point;
- the socket head remains outside the carriage and serves directly as the manual retract handle; no separate
  knob is required initially.

The selected McMaster 2006N292 spring has a free length of approximately 25.5 mm. The carriage is designed
around a 16.5 mm spring length at the fiducial / mid-travel cassette position, corresponding to approximately
9 mm spring compression from free length.

Normal supported plunger travel is ±5 mm about the fiducial position, for 10 mm total working travel. The
corresponding spring-length range is therefore approximately:

- 21.5 mm at the least-compressed end of normal travel;
- 16.5 mm at fiducial / mid travel;
- 11.5 mm at the most-compressed end of normal travel.

This remains within the intended working range of the selected spring. Any additional compression capacity is
treated as design margin rather than normal commanded travel.

The spring-cavity length, rear carriage wall/guide thickness, and 45 mm shoulder length jointly determine the
exposed retract-handle length. With a roughly 4–5 mm rear wall, the shoulder is expected to project
approximately 23.5–24.5 mm beyond the rear carriage face at fiducial, varying by approximately ±5 mm over
normal travel. Detailed CAD should preserve at least approximately 15 mm of exposed shoulder/head access at
the most-compressed normal position.

The spring itself does not provide lateral guidance for the plunger. The slotted carriage guides constrain the
plunger translation and rotation; the shoulder screw primarily controls spring bowing and provides the retract
handle.

### 8.6 Common cassette standard

Frozen cassette envelope:

- 64 × 64 × 5 mm ABS
- 24 mm diameter central clear aperture
- identical shallow bevels on all four perimeter edges
- insertable at 0 / 90 / 180 / 270°
- perimeter kept clear enough to use any opposing edge pair
- orientation/polarity indicated by markings rather than a mechanical key.

Target spring-plunger retraction for loading:

- additional 5–7 mm for cassette insertion/removal
- roughly 10–12 mm total plunger motion target.

Planned cassette variants:

1. source slit;
2. single knife edge;
3. centered wire / filament;
4. striated/multicolor filter;
5. dark-center color filter.

The standard cassette blank should carry one opposed pair of integral filament cleats on the front / non-datum
face, rather than making cleats a special cassette variant. Use two cleats total, one on each side of the 24
mm optical aperture, with both cleat axes lying on an aperture centerline and located outboard where they do
not interfere with the razor blades or common clamp bars. The cleats should be slightly conical, narrower at
the cassette face and wider toward the top, so filament tension tends to drive fine wire or thread downward
against the cassette front-face datum. Round the cleat tops and bearing surfaces to avoid damaging fine wire.
Route a filament in an S path, around opposite sides of the two cleats; the free span then crosses
approximately through the aperture centerline. Small angular error from finite cleat diameter or wrapping is
acceptable because the SM1RC/M rotates the complete tube/cassette assembly. This makes the same universal
cassette blank usable for blade, filter, Photofoil, wire, and thread experiments while keeping the rear datum
face unobstructed. Exact cleat diameter, taper, and height remain CAD details.

The carriage/cassette system is sufficiently defined to begin CAD.

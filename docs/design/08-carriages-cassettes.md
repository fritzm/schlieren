## 8. Cutoff carriage system

The cutoff uses the rotating carriage and cassettes below. The source slit originally shared this carriage
architecture; it now uses the flexure slit head ([§9](09-slit-cassette.md#9-source-slit)), so the quantities in
this section are for the single cutoff carriage.

### 8.1 Spigot and rotation interface

The carriage mounts in 1 × Thorlabs SM1RC/M through a hollow printed spigot integral with the carriage base
plate, the same interface as the slit-head adapter ([§9.6](09-slit-cassette.md#96-rotation-mount-and-clearances)):

- Ø30.48 mm spigot (SM1 tube OD nominal), clamped directly by the SM1RC/M split ring (Ø30.7 mm bore, 10.16
  mm thick, M4 locking screw across the split); the spigot end is flush with the ring's rear face;
- Ø24 mm light bore through the spigot, matching the plate aperture;
- Ø34 mm shoulder as the ring's axial stop: the ring seats against it, which places the plate back 12.0 mm in
  front of the ring face. Do not clamp the ring away from the shoulder.

The 12.0 mm ring gap is set by the rail shoe, not the post. At nominal zero the plate reaches about 63.5 mm
below the optical axis, past the shoe top (about 52.4 mm below), so the plate back must clear the shoe end
(15 mm from the post axis): calculated clearance 2.1 mm to the shoe and 10.7 mm to the post body, at every
rotation. The shoulder clears the post top by 5.1 mm.

No SM1 tube, printed split clamp, or retaining ring is used, and no printed SM1 threads are required. The
SM1RC/M provides the rotational bearing and lock: when loosened, the carriage rotates on its spigot. Nothing
retains the spigot axially while the ring is loose, so support the carriage when rotating it.

Required carriage rotation:

- at least ±90°
- preferably ±100–120°

Define nominal zero as:

- cutoff line horizontal;
- fine-adjust translation vertical;
- fine adjuster pointing upward.

Fore/aft optical positioning is done by moving the rail shoe.

Rotation envelope: the 2020 rail runs beneath the carriage at every rail position, 72.35 mm below the axis.
The base plate, guide frame, and keeper are trimmed to a 70.35 mm radius about the optical axis (the rail top
less 2 mm clearance). Only the outer plate corners are removed; the plate is otherwise 86 mm wide, widened to
94 mm at the side keeper-screw lugs (§8.4). Calculated from the CAD, the carriage with its FAS100 rotates
clear of the rail over ±150°; only the FAS100 knob reaches the rail, near ±170–180°. Nothing projects below
the plate at nominal zero (§8.5). Clearance to other equipment on the rail near the cutoff station is not
yet checked.

### 8.2 Spigot print and fit

The carriage base plate is printed deck down with the spigot up, so the spigot and shoulder need no
supports; the guide frame above the deck is a separate print (the base/frame split exists for this). The
spigot is printed at the SM1 tube nominal; fit-test it in the SM1RC/M and adjust if needed. The three datum-pin
shanks ([§8.4](#84-cassette-seating)) lie outside the shoulder and are flush-cut on the plate back as before.

### 8.3 Fine adjustment

The carriage uses:

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
- one magnet per driven plunger; 1 used in the cutoff carriage

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
head-first as small domed sliding contacts. The carriage uses three pins. The selected pin is approximately 3/8 in long, with a 0.050 in (1.27 mm) smooth
shank and 1/8 in (3.18 mm) domed head.

Mount each pin through a through-hole in the printed carriage with the domed brass head on the cassette side.
The holes are modeled Ø1.75 mm: the measured 0.050 in (1.27 mm) shank, plus the 0.38 mm diametral hole
undersize measured on the first base-plate print (the Ø24 mm aperture printed 0.930 in), plus 0.1 mm fit
clearance. The first print, with only 0.08 mm clearance, would not start a shank. If a shank still binds,
finish the hole with a #54 (0.055 in) drill. The hole fit only locates the shank; the head sets the datum. Seat the underside of the head firmly against the carriage datum face so datum height is
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
and the spring end wall on the other. The current CAD approach is therefore to print the
plunger guide tracks open from the cassette-loading side, install the plungers into those tracks, and close
only the guide-ear regions with a separate printed keeper frame.

The keeper is a perimeter frame, not a solid lid: the central upper aperture must remain open for cassette
insertion and removal. Its side members span the plunger guide tracks and retain the guide ears against upward
escape while the printed track walls carry the lateral guidance loads. The frame may be locally scalloped or
notched where the FAS100 adjuster axis intersects its envelope, provided the material directly over the swept
guide-ear paths and the load paths to the fasteners remain intact. The keeper's spring-end member also carries
the roof of the end-wall spring cup (§8.5).

Keeper retention is mechanical, with eight fasteners per carriage. Each is the existing common McMaster
91292A114 M3 × 0.5 × 12 mm socket-head screw with a McMaster 91828A211 full-height M3 × 0.5 hex nut (5.5 mm
across flats × 2.4 mm high), captive in a hex pocket opening from the plate back. Screw heads and nuts bear
directly on the ABS, without washers; tighten only to a light snug, since the joint needs little clamp and a
firm hex-key torque can crush the bearing face.

- Four end screws, at (±38.5, −53) and (±38.5, +52) mm in the carriage frame (y along the travel, +y toward
  the FAS100). Each sits on solid fill closing its guide track from 1 mm beyond the outermost ear position
  to the plate end. The fill is also the plungers' end stop: 1 mm past full loading retraction for the spring
  plunger and past +5 mm travel for the driven plunger. These positions keep each nut pocket at least 1 mm
  inside the rotation envelope (§8.1).
- Four side screws, at (±42, ±37) mm, beside the middle of each plunger's ear travel. Each sits in a Ø10 mm
  round lug that widens the base, frame, and keeper locally to 94 mm, clipped at the guide-track wall.

The side screws carry the ear wedge reactions (below) into the frame close to where they arise. A first-order
beam estimate, with each keeper side member simply supported between adjacent screws, gives at most about
0.1 mm of upward keeper deflection at the ears at the maximum-compression load. That is within the 0.25 mm
free play between the ears and the keeper. With only the four end screws it would be about 2–3 mm. The keeper
side members are 3.0 mm thick. If a print shows too much lift, a keeper with 5.0 mm side members fits the same
screws: its counterbores are deeper, so the head seat height is unchanged.

The screw heads sit in an approximately 0.5 mm-deep recess in the keeper, and the captive hex pockets are
approximately 2.5 mm deep. This leaves approximately 1.5 mm of ABS above each nut pocket and gives nearly
full use of the 12 mm screw length, with only slight nominal screw projection beyond the nut. Exact recess
depths should be tuned from printed fit rather than treated as frozen dimensions. The keeper seats on broad
printed lands, so the fasteners clamp it against the carriage rather than suspending it between isolated
points.

Provisional CAD starting dimensions for the vertical guide stack are: 4.0 mm carriage back plate thickness;
approximately 2.0 mm rise from the plate front to the lower guide-ear running surface; 3.0 mm plunger
guide-ear thickness in an approximately 3.3–3.4 mm guide channel; and approximately 3.0 mm keeper-frame
thickness. These are first-print fit targets rather than frozen dimensions. The exact datum-pin projection,
plunger-body height, and keeper-frame member widths remain to be finalized in CAD.

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

### 8.5 Spring seating and retraction

The spring plunger is preloaded by the McMaster 2006N292 compression spring (§8.3), acting between the frame's
spring end wall and the plunger's outboard face on an axis 7.5 mm above the plate back. No guide rod, retract
handle, or penetration of the end wall is used. Superseded: the earlier McMaster 91273A377 shoulder-screw
anti-buckling guide and retract handle. It is not needed, and at nominal zero it projected about 92 mm below
the axis, past the rail top.

Each spring end sits in a printed cup, 3 mm deep, sized to the measured 0.272 in (6.91 mm) coil OD plus 1.0
mm diametral clearance:

- one cup extends inboard from the end wall: its side walls are on the guide frame, and its roof is carried
  by the keeper's spring-end member, so the keeper closes over the spring end when installed;
- one cup extends outboard from the spring plunger;
- both cups are open toward the plate deck, which carries the coil. Their side walls and roofs locate the
  coil ends laterally and against escape toward the cassette-loading side. Both print with legs on the bed
  and the roof bridging the coil, without supports.

The spring's free length is about 4–4.6 times its mean coil diameter, and both ends sit on parallel faces
because the plunger is guided. That is below the roughly 5.3 critical ratio for buckling with fixed ends,
so the cups need only locate the ends rather than guide the full length. The spring itself does not guide
the plunger; the slotted carriage guides constrain plunger translation and rotation.

The selected spring has a free length of approximately 25.5 mm. The carriage is designed around a 16.5 mm
spring length at the fiducial / mid-travel cassette position, corresponding to approximately 9 mm spring
compression from free length.

Normal supported plunger travel is ±5 mm about the fiducial position, for 10 mm total working travel. The
corresponding spring-length range is approximately:

- 21.5 mm at the least-compressed end of normal travel;
- 16.5 mm at fiducial / mid travel;
- 11.5 mm at the most-compressed end of normal travel.

Loading retraction is a further 6 mm from fiducial (10.5 mm spring length), leaving 4.5 mm between the cups.
Any additional compression capacity is treated as design margin rather than normal commanded travel.

Retraction for cassette loading uses a thumb tab on the spring plunger's front face at its outboard end:

- 20 mm wide × 3 mm thick × 6 mm tall, centered between the guide ears and outside the cassette footprint;
- the thumb reaches over the cassette and pushes the tab's inner face outboard, at about 9 N at full
  retraction;
- 0.5 mm chamfers on the exposed edges; the spring-facing face is left square;
- a Ø1.6 mm grip bead along the inner top edge, flush with the tab top, prevents finger slip.

The tab is kept low, close to the plane of the guide ears, so that pushing on it does not twist the plunger
and jam the ears.

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

1. single knife edge;
2. centered wire / filament;
3. striated/multicolor filter;
4. dark-center color filter.

The source slit no longer uses a cassette (§9).

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

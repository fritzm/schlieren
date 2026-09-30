# iPhone schlieren

Canonical project state and workflow are linked in [AGENTS.md](AGENTS.md).

## LED module — initial CAD proposal

`src/schlieren/parts/led_module.py` follows §6.5 of the design document
refreshed September 22, 2026: a flat M4 post-top tab, rear support post,
forward-reaching fingers and vertical heatsink calibration.
This remains exploratory; canonical documents and BOM are unchanged.

```sh
uv run led-module --show --with-shoe
uv run led-module --show --travel 3
uv run python -m unittest discover -s tests -p test_led_module.py -v
```

The script exports only `led_module_bracket.step` and `.stl` into the ignored
export directories. Local x is transverse, +y points toward the condenser,
and z=0 is the post-top seating face. The viewer translates this to the rail
datum: post top at 50.254 mm, nominal emitter axis at 72.35 mm. `--travel`
moves the heatsink reference ±3 mm vertically without changing the print.
STL retains local assembly orientation; select print orientation/supports
in the slicer, especially under the raised arms and mounting tab.

The initial bracket has a 5 mm-thick, Ø20 mm tab with a Ø4.5 mm M4 through
bore. The heatsink rear face is provisionally 14 mm forward of the post axis.
Two 14 mm-high side channels provide 0.15 mm lateral clearance per side,
rear axial seating lips, and front capture lips with 0.30 mm axial clearance.
Press the heatsink against both rear seats while tightening the opposed
pressure screws. The channels permit vertical insertion with the screws
retracted; friction from the screws retains the calibrated height. Actual
holding force, fin stiffness, ABS creep, and repeatability are unqualified.

Two proposed M3 × 12 socket-head pressure screws use top-loaded full-height
M3 nuts, borrowing the common hardware standard without committing a new BOM
allocation. Their plain tips bear directly on opposing heatsink flats;
confirm those locations are substantial aluminum rather than vulnerable fin
tips. Apply light pressure. The closed outside pocket walls carry the nut
reaction; the nuts can fall out upward during handling until retained.
Small localized CA tacks remain an optional post-calibration measure per §6.5.

The model uses the document's **approximately 55 mm across flats × 20 mm**
octagonal envelope. The BOM calls it **Ø55 mm**: measure the actual heatsink
before trusting this fit, including across-flats/corners, front/rear bearing
surfaces, and fin layout. The transparent reference has no modeled fins,
MCPCB, wiring, or emitter projection. Nominal envelope center represents the
emitter axis; actual board/emitter offset is corrected during calibration.
The forward baffle tabs have been removed to match the updated baseline.
LED/solder clearance, wiring restraint, and condenser clearance remain open
pending measurements.

The post-top M4 retainer is deliberately not modeled: establish whether the
actual setup uses a retained stud/nut or a screw, then check available thread
engagement through the 5 mm tab. The seating annulus and vertical tool access
are checked geometrically. Tests also cover the continuous calibration sweep,
rear seating overlap, nut loading, vertical heatsink insertion, and clearance
from the existing rail shoe and post. They do not qualify grip force or thermal
performance. Each LED/heatsink stays with its own calibrated bracket.

## Common rail shoe — first CAD prototype

Source: `src/schlieren/parts/rail_shoe.py`. All dimensions are millimeters;
x is across the rail, y is along it, and z=0 is the rail top. This is an
exploratory design, pending review and physical ABS fit/clamp testing.

```sh
uv run rail-shoe
uv run rail-shoe --show
uv run python -m unittest discover -s tests -v
```

The first command exports STEP and STL to ignored `exports/step` and
`exports/stl` directories. `--show` also sends the assembly to the OCP CAD
Viewer extension. Select the project's `.venv` interpreter in VS Code.
The gray-box rail/post references are simplified envelopes, not fabrication
models of purchased components. Only the shoe is exported. Toggle the `Post`
group in the viewer tree to hide/show the post independently of the shoe,
rail, and datum disc.

The provisional bridge/skirt is 30.4 mm across × 30 mm along the rail, extending
from z=-18 to z=23 mm. It has a 12.95 mm post bore (12.7 mm nominal plus
0.25 mm diametral clearance) and 0.20 mm rail clearance per side.
The bridge underside seats directly on the rail top at z=0 outside a
22.05 mm diameter × 1.0 mm deep counterbore. This gives the 19.05 mm datum
disc 1.5 mm radial clearance and 0.746 mm clearance above its top face.
The post still seats directly on the disc. The 5 mm bridge retains a 4 mm
roof above the recess. Full-width seating lands extend approximately
3.975 mm inward from each bridge end. The existing clamp ears project
3 mm beyond the +y end, giving a 33 mm overall envelope along the rail.

One M5 clearance hole per side aligns with the side-slot center at z=-10 mm.
M5 screw length and actual T-nut/washer seating need physical verification.
The 1.5 mm collar split has a rounded termination and a filleted root;
the ears accommodate the specified M3 × 12 screw and full-height captured
M3 hex nut. Load the nut from the outside +x face; the screw enters from -x.

All envelope dimensions, ABS allowances, and the two-hole mounting layout
are provisional parameters, separate from the canonical physical interfaces.
Check sliding fit, post seating, clamp flexure, nut retention, and tool access
before printing all four. No global ABS shrink compensation is assumed.
STL uses assembly coordinates; choose orientation/supports in the slicer.

## SM1 tube retaining clamp — prototype

`src/schlieren/parts/tube_clamp.py` defines a single-split ABS retaining ring.
Run `uv run tube-clamp --show` to export STEP/STL and view
it with a separately toggleable tube reference. Run its checks with
`uv run python -m unittest discover -s tests -p test_tube_clamp.py -v`.

The nominal tube OD is 1.20 in / 30.48 mm per the
[Thorlabs SM1 tube-mount specifications](https://punchout.thorlabs.com/NewGroupPage9.cfm?ObjectGroup_ID=1533&Visual_ID=1964).
This is a catalog nominal, pending measurement of the actual tube. The
prototype has a 30.73 mm bore including 0.25 mm diametral fit allowance,
3.5 mm radial wall, 1.5 mm split, and 0.5 mm outer-rim fillets.
The 8 mm axial width leaves 1.1 mm above and below the 5.8 mm hex pocket;
it is an exploratory increase from the status Doc's approximate 4–5 mm.
Tabs use the existing M3 × 12 screw and full-height M3 nut, with 1 mm root
fillets. Apply only light clamping after checking ABS fit and axial retention.
Canonical design documents have not been changed by this prototype.

## Slit/cutoff carriage — preliminary sandwich layout

`src/schlieren/parts/carriage.py` follows the September 21 design baseline:
base plate with clamp, separate guide frame, keeper plate, and two plungers.
The base includes an integral rear flexure clamp for the smooth SM1L15 tube. Local XY is the cassette plane, +Y
points toward the fine adjuster, and +Z is the loading direction; this local
Z origin is the plate back, not the rail-top optical-height datum.

```sh
uv run carriage --show
uv run carriage --show --travel 5
uv run carriage --show --retract 6
uv run python -m unittest discover -s tests -p test_carriage.py -v
```

The script exports four STEP/STL pairs to ignored export folders:
`carriage_base_plate`, `carriage_guide_frame`, `carriage_keeper_plate`, and
`carriage_plungers`.
The paired plungers sit at z=0 with matching orientation and a 5 mm gap
between their bounding boxes. The base is flipped deck-down to z=0 for
clamp-up printing; guide frame and keeper retain assembly coordinates.
The viewer retains its five separately selectable assembled parts; travel and
retraction options do not affect the plunger print layout.
The provisional plate envelope is 86 × 123.8002 mm. Open tracks accept the plungers
from the front before the 3 mm keeper is installed. Its side members seat on
continuous lands and overlap the guide ears; four M3 × 12 screws engage
back-loaded M3 nut pockets. The stack uses a 4 mm back plate, 2 mm guide-floor
rise, 3 mm ears, and a 3.4 mm guide channel.

The base has a 24 mm circular aperture centered on the fixed tube optical axis.
Cassette translation does not move this opening.
Three pin holes form a provisional broad datum triangle. Both plungers have
27.5° seating lips (angle from the cassette plane, 1.25 mm bevel depth).
The spring seat provides 16.5 mm spring length at fiducial, 11.5–21.5 mm over
normal travel, with a 4.25 mm guide hole for the 4 × 45 mm shoulder screw.
The driven plunger has a fully backed 10 × 5 × 2 mm magnet pocket with fit
allowance; this preliminary outward-opening pocket requires a small adhesive
tack for retention.

The refreshed bushing/adjuster dimensions are used for support and travel:
McMaster 98625A950 overall length 7.9502 mm, under-flange length 7.5692 mm,
body OD 7.9502 mm, and flange Ø8.9408 × 0.254 mm;
FAS100 screw length 25.4 mm and pitch 0.3175 mm/revolution. The adjuster end
is now at y=60.3002 mm, bringing the overall carriage length to 123.8002 mm.
The spring end remains at y=-63.5 mm with the original preload. The insert
support and matching keeper end member are 8.5 mm deep, with a 0.1 mm entry
chamfer. The outboard flange remains proud and seats directly on the face.

The insert bore is nominally **Ø7.9502 mm (0.313 in)**, exactly matching the
manufacturer drawing's body OD and drill size. Treat the physical printed
hole as a pilot: finish it and establish retention by prototype fit. A 5/16 in
drill is 7.9375 mm, 0.0127 mm smaller than specified; fit-test before using it.
The drawing's minimum material thickness is 7.5692 mm; the 8.5 mm support
retains 8.4 mm beyond its entry chamfer. The prior Ø8.2 mm epoxy-fit assumption
is superseded. Retention/adhesive allowances are not built into the nominal
insert envelope. The flange remains proud on the outboard face, without a
counterbore. Overall, body, and flange dimensions are independent drawing
callouts rather than inferred from one another.

The adjuster and magnet axis is z=8.0751 mm; the spring axis remains z=7.5 mm.
The crown retains 3 mm nominal radial ABS thickness, reaching z=15.0502 mm.
Plunger bodies retain 0.3 mm deck clearance and their original guide ears.
The calculated tip extension from the conservative overall-length envelope is 5.5–15.5 mm
across ±5 mm cassette travel, below the 17.4498 mm theoretical full-engagement
limit. From the actual under-flange body end, the gap is 5.881–15.881 mm.
These are calculated clearances, not a published FAS100 travel specification. At the farthest reach, the shaft retains 1.6958 mm clearance beyond
the proud flange before the nominal knob-side end condition. Actual knob
and ball-tip geometry still need a physical access check.

The datum-pin projection, sliding fits, spring compression at loading, and
cassette insertion/tilt trial remain provisional. Six millimeters of loading
retraction is modeled from fiducial only. Hardware and cassette are not in
the five-piece carriage assembly. Full SM1RC/M/post rotation clearance still
needs checking against the physical stack.

The spring plunger has a Ø3.3 mm blind M4 tapping pilot, 9 mm total depth:
7 mm nominal engagement zone plus 2 mm tap relief. A 0.5 mm × 45° entrance
chamfer opens to Ø4.3 mm. This leaves a 1 mm closed end wall. Verify the
actual shoulder-screw threaded length and tap lead; the CAD pilot has a flat
bottom, so any drill-point allowance must fit within the remaining wall.

## Common cassette blank — preliminary

`src/schlieren/parts/cassette.py` supplies the common 64 × 64 × 5 mm ABS
blank with a Ø24 mm through aperture. The rear sliding datum is z=0; the
front is +Z. Four identical front-edge bevels match the preliminary carriage:
1.25 mm axial depth at 27.5° from the cassette plane. These bevel dimensions
remain provisional. The blank has no orientation marking.

```sh
uv run cassette
uv run cassette --show --with-carriage
uv run cassette --show --with-carriage --travel 5
uv run python -m unittest discover -s tests -p test_cassette.py -v
```

Exports are separate `cassette_base` and `cassette_clamp_bar` STEP/STL pairs
in `exports/step` and `exports/stl`, with
the rear face at z=0 regardless of viewer pose. The optional carriage view
positions the blank on the assumed datum-pin contact plane. Tests check
all four orientations at −5, 0, and +5 mm travel, printed-part interference,
and rear datum-track support. Both carriage and cassette retain their specified
24 mm apertures; their overlap decreases away from centered travel.

The refreshed §8.6/§9 baseline adds two integral filament cleats and four
clamp-bar bores to this universal blank. Provisional cleats at (±25, 0) mm
taper from Ø3.5 mm at the face to Ø5 mm toward the top, with 0.5 mm top
rounding and unfilleted roots so filament can seat against the plate. They rise 3 mm above the front face (8 mm overall height).
An S wrap around opposite sides provides a near-centered filament span.

The four Ø3.4 mm bores are at (±27, ±12) mm, with rear-entry 90° countersinks
opening to Ø6.2 mm (6 mm nominal screw head plus 0.2 mm diametral allowance).
The conical relief meets the bore at 1.4 mm depth; this is distinct from the
catalog 1.7 mm total head height. Verify flush or slightly recessed seating
with the selected M3 × 14 screws before use. Hole positions clear the measured
38.99 mm blade length and the swept datum-pin head footprints in all four
orientations. These positions remain provisional: removable clamp bars must
bridge around the aperture and support the specified washer lands; straight
bars centered on the hole rows would intrude into the optical opening.

The viewer now shows two identical removable bars as separate clamp assemblies,
with toggleable simplified M3 × 14 screws, Ø7 washers, 5.5 mm AF nuts, and EPDM
pads. Hardware references omit threads and drive sockets. Only the cassette
base and one representative printed bar are exported; both have their lowest
face at z=0. Print two bars. Former `cassette.step`/`.stl` exports are obsolete.

The 4 mm bars offset their central bearing strip to y=12.5–17.5 mm, clearing
the aperture and bearing inboard of the folded blade spine. Each end is 8 mm
wide with a full Ø7.2 mm washer land around its bore. The ends reach x=±31 mm,
leaving 2 mm to the keeper's ±33 mm inner faces (and 1.3 mm in plan to the
lower guide-track edges at ±32.3 mm). The washers reach ±30.5 mm, leaving
2.5 mm to the keeper; nut corners lie inside that washer envelope.

A 1.6 mm underside relief beyond x=±21 mm lets the ends pass over the plunger
lips when installed at 90°/270°. The central bar section remains 4 mm thick;
relieved ends retain 2.4 mm of ABS. Validate stiffness and use light clamp loads.
The viewer uses a provisional 0.6 mm media lift and uncompressed 0.79375 mm
EPDM, placing bar undersides at z=6.39375 mm. This is a setup estimate, not a
measured blade thickness or a prediction of the blade's inclination. With
0.5 mm washers and 2.4 mm nuts, a screw head recessed 0.1 mm gives about
0.81 mm tip projection beyond the nut. EPDM compression and actual blade/foil
height change that projection and the plunger clearance; check both physically.
The nominal zero-media-lift stack has 0.394 mm clearance over the plunger
lip at the relieved ends before EPDM compression.

Tests include complete assembly/hardware interference against the carriage
at four orientations and three travel positions, aperture clearance, and
washer bearing lands. Physical bevel seating, datum-pin height, screw seating,
ABS fit, tool access, and tilted loading/removal still need validation.
The canonical Google resources are unchanged by this preliminary design.

The rear carriage tube boss uses a provisional 30.73 mm bore (30.48 mm
catalog OD plus 0.25 mm diametral clearance) and 4.5 mm radial wall. It
projects 12.25 mm behind the plate, with a 2 mm external root fillet. The
tube seats against the intact plate back around the 24 mm optical aperture.

A 1.25 mm axial-width circumferential slit cuts through the boss wall over
240 degrees, beginning 0.5 mm beyond the root fillet. Rounded slit ends
leave a substantial 120-degree connection opposite the +X axial split.
The perpendicular split and M3 clamp ears are behind that circumferential
slit; the ears have another 0.5 mm clearance from the slit. Neither slit
cuts the plate or root fillet. The ears accommodate the common M3 × 12
screw and captured full-height M3 nut, with 1 mm root fillets. Screw entry
is from -Y, nut loading from +Y.

The clamp remains integral with the base export. The base is separated at
the top of its 4 mm deck from the middle guide frame. The four M3 × 12
corner screws clamp the base, guide frame, and keeper without increasing
the stack height. Two Ø3 mm × 0.8 mm locating pegs beneath the guide frame
fit Ø3.3 mm × 1 mm recesses in the base. These provisional fit allowances
keep the base deck flat for printing. The base export is flipped clamp-up,
with the deck at z=0 and clamp tip at z=16.25 mm. Choose guide-frame print
orientation/supports to accommodate its downward locating pegs. Tube fit, clamp compliance, stiffness,
and holder/rotation clearance remain physical validation items. This revised
prototype has not been promoted into the canonical Google design document.

## Carriage 2 — urgent-build finger-holder alternative

`src/schlieren/parts/carriage_2.py` is a separate, provisional single-piece
holder for the existing cassette. The original carriage is unchanged.

```sh
uv run carriage-2 --show
uv run carriage-2 --show --travel 5
uv run python -m unittest discover -s tests -p test_carriage_2.py -v
```

`exports/step/carriage_2.step` and `exports/stl/carriage_2.stl` contain only
the holder. Print two for slit/cutoff stations. The viewer includes the
existing cassette with bars/hardware, post, bottom adjuster, bushing, edge
magnet, and pressure-screw references. Local z=0 is the post top. The export
uses assembled coordinates; choose orientation and supports in the slicer.
The projecting post tab, bottom bushing boss, and small channel lips require
particular support/orientation attention. Slicer time is not yet verified.

The holder mounts directly on the flat TR50/M post top through a Ø4.5 mm M4
clearance hole and 5 mm seating pad, like the LED bracket. Use the actual
post-top attachment hardware with verified engagement; screw length is not
assumed. The cassette optical center is 22.096 mm above that seating face,
matching the 72.35 mm rail-top datum. There is no continuous optical-axis
rotation; the cassette still accepts four orientations.

Two 14 mm-high fingers guide the 64 mm cassette edges over ±5 mm travel.
They have 0.25 mm lateral clearance per side and 0.3 mm nominal axial
clearance at the shallow retaining lips. Lips overlap only 0.5 mm of the
outer perimeter so they clear the existing clamp bars and fasteners. The
rear contacts are broad printed faces, not precision brass datums. Smooth
these surfaces and fit-test the lips; they are not snap-fit features.

Two M3 × 12 pressure screws and ordinary M3 nuts in top-loaded pockets lock
the cassette sides. These are additional uses of the common hardware,
not a confirmed spare-stock allocation. For fine adjustment loosen the
pressure screws enough to slide freely while holding the rear face seated.
Tighten gently after setting; excessive pressure can shift or distort the
cassette. Gravity seats the cassette on the adjuster in upright operation;
hold it seated during setup and do not rely on this arrangement when tilted
or inverted. Remove the cassette for transport.

The optional FAS100 below the cassette pushes on the broad face of a
10 × 5 × 2 mm magnet bonded to the *lower edge* of the cassette (not its
rear optical datum). Center it in x, with its 2 mm dimension vertical.
The bevel reduces bonding contact; check this attachment physically. The
insert flange faces downward/outboard; the nominal Ø7.9502 mm bore requires
physical finishing/fit validation. The insert support is 8.5 mm long, with
full-envelope screw engagement preserved over ±5 mm travel. Actual FAS100
knob/ball geometry and finger access beneath the holder need checking;
only the shaft is modeled. With no adjuster installed, slide the cassette
by hand and lock it with the side screws. Reorienting the cassette may
require moving the bonded contact to its new lower edge.

This is an emergency alternative, not a finalized replacement of the
canonical design. Tests check complete cassette hardware clearance in four
orientations, normal travel and upward loading, post and optical clearance,
pressure-screw clearance, and adjuster reach. Printed fit, finger stiffness,
adhesion, and adjustment sensitivity still require a quick bench check.

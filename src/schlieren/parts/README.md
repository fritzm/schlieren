# Part models

build123d models of the custom (mostly printed ABS) parts, plus purchased-part stack-ups used for clearance
and focus calculations. Each module here has a matching command in `src/schlieren/cli/` (run as
`uv run <command>`; `--show` sends the assembly to the OCP CAD Viewer) and a test module in `tests/`.

The committed design for each part lives in `docs/design/` (section numbers below refer to it). The notes here
describe the models: coordinate frames, parameters, exports, and what the tests do and do not cover. Where
they disagree with `docs/design/`, the design fragments govern.

Exports land in the ignored `exports/step` and `exports/stl` directories. Select the project's `.venv`
interpreter in VS Code for the viewer.

## Tabletop frame

`src/schlieren/parts/frame.py` encodes the §4 frame: the two 400 mm rails on
the front pivot plate, each with its pivot lug and stack, fixed yaw strap,
friction strip, yaw bolts, rear foot block, and Sorbothane foot, plus the
front foot. Nothing is printed. The command prints the rail half-angle, the
six pivot-plate hole centers, and the screw-stack margins, and exports STEP
models of the two plywood parts (`frame_pivot_plate`, `frame_foot_block`)
and `exports/drawings/frame_pivot_plate.svg`, a full-scale drilling layout of
the pivot plate from `frame_drawing.py`, seen from above with the six holes
dimensioned in the §4.2 plate coordinates;
`--show` displays the assembly, with each rail optionally yawed about its pivot.

```sh
uv run frame
uv run frame --show --left-yaw 3 --right-yaw -3
uv run frame --figure      # re-render docs/design/figures/frame.png and frame-pivot-plate.svg
uv run python -m unittest tests.test_frame -v
```

Coordinates are the §3.4 pivot frame (origin at the midpoint of the aft
plate edge, +y toward the mirror, +x to the right seen from above with the
mirror ahead) with z=0 at the rail top; the rails run aft to negative y. Each rail assembly is built in its own §3.4 rail frame.
Yaw is in degrees outward from the nominal half-angle; the straps and their
bolts stay fixed to the plate. The rails use `rail.py` with the measured
§4.1 slot dimensions; the slot-floor taper is still nominal. The thumb nuts
are the McMaster 92815A202 vendor model (Ø20 × 5 mm, unthreaded), collar down
on the strap washer, and the feet are the McMaster 8215K2 model, a Ø1.25 in
hemisphere. Other fasteners, washers, and nuts are plain nominal envelopes,
and the T-nuts are not modeled.

Three placements are not given in §4 and are model assumptions, exposed as
parameters: the rail front end 10 mm aft of the pivot (`rail_front_setback`),
the lug fixed to the rail top slot by M5 × 8 screws in its two aft holes
(`lug_screw_length`), and the foot block flush with the rail rear end
(`foot_block_rear_setback`).

Tests cover the half-angle and hole layout against §4.2, plate and foot-block
envelopes and holes, the three-foot support plane, screw-stack lengths, the
lug hole staying on the pivot axis, rail-to-yaw-bolt clearance at nominal and
±3°, the drilling drawing's hole positions and figures, thumb-nut and foot
model size and seating, and part interference across that
range.

## Light source — threaded SM1 stack-up

`src/schlieren/parts/light_source.py` encodes the §6 light source on its
SMR1/M: Alpha CN40-40B heatsink and star board on a Thorlabs SM1CP2M cap
threaded into the LED side, and on the slit side the SM1V05 focus cell with
its lock ring, the ACL2520U-A condenser under its retaining ring, the SM1L03
tube, and the SM1D12 iris. Nothing is printed; the command prints the focus
stack-up and `--show` displays the vendor STEP models (`cad/vendor/`), a
representative star board and LED package built from the outline drawings,
and the rail shoe for reference. The lens, tube, and iris move with the
SM1V05 engagement. The SM1L03's own retaining ring is not modeled.

```sh
uv run light-source
uv run light-source --show --module white --engagement 3.0
uv run light-source --figure      # re-render docs/design/figures/light-source.png and light-source-holes.svg
uv run light-source --templates   # exports/drawings/light_source_drilling_templates.svg, print at 100%
uv run python -m unittest tests.test_light_source tests.test_light_source_holes -v
```

Axial coordinate u has u=0 at the LED-side SMR1/M face; the viewer uses x
transverse, +y toward the slit and mirror (the §3.4 source rail frame), z=0 at the rail top. Board thicknesses are
caliper measurements; emitter heights are calculated from the LED outline
drawings in `docs/reference/`; other dimensions are catalog values. Tests cover
the optimum-gap calculation, focus margin for each module, SMR1/M thread
sharing, lead annulus, heatsink-to-post clearance, the lens vertex position
in the SM1V05, vendor-model fit and placement, and part interference.
They do not qualify thermal performance.

`light_source_holes.py` holds the through-hole layout of the cap and the
heatsink base (M3 heatsink screws, M2 board screws, lead holes) in the frame of
the heatsink pin lattice, with the clearance checks; `light_source_drawing.py`
draws it as the §6.4 figure and as a Letter sheet of full-scale cap and
heatsink drilling templates. `tests/test_light_source_holes.py` covers the
pin lattice against the vendor model, heads between pins, wall and pin gaps,
and the drawings.

## Source-slit flexure head

`src/schlieren/parts/slit_head.py` encodes the §7 source slit: one flat-printed
ABS flexure head holding both Stanley blades, with a FAS100-driven centering
stage (±2 mm, coaxial spring preload) and a nested FAS100-driven width stage,
plus a flat spigot adapter (on M3 washer spacers) clamped by the SM1RC/M for
continuous rotation, and two clamp bars. The command exports the three printed
parts, prints travel, strain, preload, and first-order stage-rotation figures,
and `--show` displays the assembly on the post and rail shoe.

```sh
uv run slit-head
uv run slit-head --show --rotation 90
uv run python -m unittest tests.test_slit_head -v
```

The local frame has x along the slit, z the adjustment axis (knobs up at
rotation 0), and +y out of the blade-seat (front) side, with the origin at the
slit center on the blade-seat plane. On the rail the front faces the light
source (§7.2), so local +y is rail -y. Tests cover the optical-height datum, flexure topology
(the blades are the only links between frame, platform, and width stage),
strain, preload, stage rotation, the spigot fit and shoulder, hardware
interference, and clearance to the post and shoe swept over ±110°.

## Common rail shoe

Source: `src/schlieren/parts/rail_shoe.py` (§5.3). All dimensions are millimeters;
coordinates are a §3.4 rail frame: x across the rail, +y along it toward the mirror, and z=0 at the rail top. The model and its
ABS allowances are final, fit-tested on printed shoes.

```sh
uv run rail-shoe
uv run rail-shoe --show
uv run rail-shoe --figure
uv run python -m unittest tests.test_rail_shoe -v
```

The first command exports STEP and STL to ignored `exports/step` and
`exports/stl` directories. `--show` also sends the assembly to the OCP CAD
Viewer extension. Select the project's `.venv` interpreter in VS Code.
The gray rail is the generic 2020 profile from `src/schlieren/parts/rail.py`
(`build_rail(length)`, rail-top frame), a visualization model shared with any
assembly that shows the post and shoe; it is a nominal slot-6 section, not the
measured extrusion (§4.1). The datum disc is a simplified envelope, and the
post is the Thorlabs TR50/M vendor model. Only the shoe is exported. Toggle the `Post`
group in the viewer tree to hide/show the post independently of the shoe,
rail, and datum disc. `--figure` renders the same assembly to
`docs/design/figures/rail-shoe.png`, the §5.3 figure in the design document.

The bridge/skirt is 30.4 mm across × 30 mm along the rail, extending from
z=-18 mm; the collar rises to z=20 mm. The post bore is 12.8 mm (12.7 mm
nominal plus 0.10 mm diametral clearance), with 0.20 mm rail clearance per side.
The bridge underside seats directly on the rail top at z=0 outside a
20.05 mm diameter × 1.0 mm deep counterbore, giving the 19.05 mm datum disc
0.5 mm radial clearance and 0.746 mm clearance above its top face. The post
seats directly on the disc. The 5 mm bridge retains a 4 mm roof above the
recess, and full-width seating lands extend about 5 mm inward from each bridge
end.

One M5 clearance hole per side aligns with the side-slot center at z=-10 mm.
The Ø21 × 15 mm collar has a 1.0 mm radial split toward +x with a rounded
relief at its foot and a 2 mm root fillet. Both clamp ears point toward +x:
the 4.5 mm nut ear at +y holds a full-height captured M3 hex nut loaded from
its outer face, and the M3 × 12 screw enters the 3.5 mm screw ear from -y.

No global ABS shrink compensation is assumed. STL uses assembly coordinates;
choose orientation/supports in the slicer.

## Slit/cutoff carriage — preliminary sandwich layout

Now used for the cutoff only; the source slit uses the flexure slit head (§7).

`src/schlieren/parts/carriage.py` follows the September 21 design baseline:
base plate with spigot, separate guide frame, keeper plate, and two plungers.
The base carries an integral rear shouldered spigot that the SM1RC/M clamps directly
(§8.1), the same interface as the slit-head adapter. Local XY is the cassette plane, +Y
points toward the fine adjuster, and +Z is the loading direction, which
faces the mirror (§8.1); this local
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
spigot-up printing; guide frame and keeper retain assembly coordinates.
The viewer retains its five separately selectable assembled parts, plus the
SM1RC/M, TR50/M post, and rail shoe as references; travel and retraction options
do not affect the plunger print layout.
The provisional plate envelope is 86 × 123.8002 mm. Base, frame,
and keeper are trimmed to a 70.35 mm radius about the optical axis (rail top
less 2 mm), clipping the plate corners so the carriage rotates clear of the
rail; the tracks are filled solid 1 mm beyond the outermost ear positions as
end stops, and the four keeper screws sit on that fill at y = -53 / +52 mm. Open tracks accept the plungers
from the front before the 3 mm keeper is installed. Its side members seat on
continuous lands and overlap the guide ears; the M3 × 12 keeper screws engage
back-loaded M3 nut pockets. The stack uses a 4 mm back plate, 2 mm guide-floor
rise, 3 mm ears, and a 3.4 mm guide channel. Four more keeper
screws sit beside the ear travel at (±42, ±37) mm, in round lugs that widen the
base, frame, and keeper locally to 94 mm (eight M3 × 12 screws and nuts in all),
limiting upward keeper bowing under the ear wedge reactions. If a print shows
too much lift, `uv run carriage --keeper-side-thickness 5` exports a keeper with
5 mm side members and deeper counterbores (same screws). Screw heads and nuts
bear directly on the ABS (no washers); tighten only to a light snug, since a
firm hex-key torque can crush the bearing face and the joint needs little clamp.

The base has a 24 mm circular aperture centered on the fixed spigot optical axis.
Cassette translation does not move this opening.
Three pin holes form a provisional broad datum triangle. They are modeled
Ø1.75 mm: the measured 1.27 mm (0.050 in) brad shank, plus the 0.38 mm hole
undersize measured on the first base-plate print (Ø24 mm aperture printed
0.930 in), plus 0.1 mm fit clearance. Finish with a #54 drill if a shank binds.
Both plungers have
27.5° seating lips (angle from the cassette plane, 1.25 mm bevel depth).
The spring seat provides 16.5 mm spring length at fiducial, 11.5–21.5 mm over
normal travel. The coil sits in two printed cups open toward the
deck (frame end wall, with the roof carried by the keeper, and spring plunger),
replacing the shoulder-screw guide rod and its end-wall hole. A 20 × 3 × 6 mm
thumb tab (0.5 mm chamfers except on its spring-facing face, Ø1.6 mm grip bead
on its inner top edge) on
the spring plunger's front face, pushed outboard from above the
cassette, retracts it for loading.
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
retraction is modeled from fiducial only. `--show` adds the FAS100, bushing,
magnet pad, and spring envelope as references; the cassette is not shown. Full SM1RC/M/post rotation clearance still
needs checking against the physical stack.

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

The refreshed §8.6/§7 baseline adds two integral filament cleats and four
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
keep the base deck flat for printing. The base export is flipped spigot-up,
with the deck at z=0 and spigot end at z=26.16 mm. Choose guide-frame print
orientation/supports to accommodate its downward locating pegs. Spigot fit in the
SM1RC/M and rotation clearance to the rail remain physical validation items. The
committed design is recorded in `docs/design/08-cutoff.md` (§8).

## Camera support — lens pointer and phone rest

`src/schlieren/parts/camera_support.py` models §§9.4–9.8: a lens-specific pointer that holds the lens in two
collars, each on a pair of inclined ball-tip screws in a printed yoke bolted to a shoe, with an endless
elastic band per yoke, and a phone-specific rest under the lower edge of the phone hanging from the lens.
The printed parts (pointer shoe, two yokes, two collars, phone rest) are modeled in detail with fillets, pad
pockets, clamp ears, insert holes, the yoke joint, and the band pegs; the shoe and rest saddles take the
common rail shoe's dimensions through `RailShoeParameters`. The lens, phone, and hardware are envelopes
except the McMaster screws, thumb nuts, and heat-set inserts, which are vendor models. The M3 clamp screws
and nuts, the M5 clamp and joint screws, and the band peg ends are not drawn. Phone and lens dimensions are
the §9.1–9.2 measurements and the Apple drawing; the focus-ring diameter and the cased phone thickness are
assumed. Coordinates are the §3.4 imaging rail frame with y=0 at the back of the phone.

```sh
uv run camera-support --show
uv run camera-support --figure     # re-render docs/design/figures/camera-support.png
uv run camera-support --views      # several PNG views into exports/figures/
uv run run-tests test_camera_support
```

Tests cover the collar stations against the measured barrel sections and the focus ring, the collar wall,
split, fillets, clamp-screw hole and nut pocket, each pad pocket and its rim, the ball end stopping at the
predicted travel, each screw tip touching its pad or the groove rods, the yoke profile and the walls round its
inserts, the yoke-to-shoe joint, the saddle dimensions against the common rail shoe, the band geometry, load
split, and clearances, the phone's lower edge on the rest rod, and the printed parts staying clear of each
other and of the cutoff station's rail shoe (slow tests).

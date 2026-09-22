# iPhone schlieren

Canonical project state and workflow are linked in [AGENTS.md](AGENTS.md).

## Common rail shoe — first CAD prototype

Source: `src/schlieren/parts/rail_shoe.py`. All dimensions are millimeters;
x is across the rail, y is along it, and z=0 is the rail top. This is an
exploratory design, pending review and physical ABS fit/clamp testing.

```sh
uv run python scripts/rail_shoe.py
uv run python scripts/rail_shoe.py --show
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
Run `uv run python scripts/tube_clamp.py --show` to export STEP/STL and view
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

## Slit/cutoff carriage — preliminary four-piece layout

`src/schlieren/parts/carriage.py` follows the September 21 design baseline:
base plate, removable keeper plate, driven plunger, and spring plunger.
The split-ring tube mount is omitted. Local XY is the cassette plane, +Y
points toward the fine adjuster, and +Z is the loading direction; this local
Z origin is the plate back, not the rail-top optical-height datum.

```sh
uv run python scripts/carriage.py --show
uv run python scripts/carriage.py --show --travel 5
uv run python scripts/carriage.py --show --retract 6
uv run python -m unittest discover -s tests -p test_carriage.py -v
```

The script exports three STEP/STL pairs to ignored export folders:
`carriage_base_plate`, `carriage_keeper_plate`, and `carriage_plungers`.
The paired plungers sit at z=0 with matching orientation and a 5 mm gap
between their bounding boxes. Base and keeper retain assembly coordinates.
The viewer retains its four separately selectable assembled parts; travel and
retraction options do not affect the plunger print layout.
The provisional plate envelope is 86 × 127 mm. Open tracks accept the plungers
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

**Not print-ready:** the 8 mm brass-insert bore is an explicitly unmeasured
placeholder. Measure the insert OD/length and determine its seating and
retention fit. The assumed 1 mm datum-pin projection, ABS sliding fits, magnet
fit, shoulder-screw threaded-end engagement, spring OD/solid height, and bevel
contact need physical checks. Six millimeters of loading retraction is modeled
from fiducial only (spring length 10.5 mm), pending spring compression validation
and a cassette insertion/tilt trial. Hardware and cassette are not included in
the four-piece assembly. Tube mounting and rotational clearance remain outside
this preliminary layout. The canonical Google resources are unchanged.

The adjuster and spring support blocks span the full 86 mm plate width and
sit flush with the ends of the shortened 127 mm plate. Plate length is derived
from the 16.5 mm fiducial spring gap and 5 mm spring wall, matching the keeper edge above; the adjuster block
retains its 12 mm depth. Keeper length and corner fasteners follow the plate
edges. Open-top keeper recesses and matching rod-axis reliefs preserve keeper
removal and the original screw stack. Minimum exposed shoulder is 18.5 mm over
normal travel, restoring the baseline handle-access allowance.

The adjuster-end keeper member now spans the full 12 mm insert-support depth,
so the base support and keeper form one aligned end wall without a raised
inboard block. Both plunger bodies extend to 0.3 mm above the deck while their guide ears
retain the original height. The spring axis is at z=7.5 mm. The adjuster axis
and magnet pocket are at z=8 mm, placing the provisional 8 mm insert bore
tangent to the deck without cutting into it. A concentric circular crown over the adjuster bore provides a minimum 3 mm
radial wall, matching the keeper thickness elsewhere. Its 7 mm outer radius
raises the local top to z=15 mm across the full 12 mm end-wall depth. The
magnet pocket retains 1.125 mm of ABS below it; physical fit checks remain.

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
uv run python scripts/cassette.py
uv run python scripts/cassette.py --show --with-carriage
uv run python scripts/cassette.py --show --with-carriage --travel 5
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

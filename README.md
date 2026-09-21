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

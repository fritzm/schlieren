## 4. Tabletop optical frame

### 4.1 Rails — committed

- IXGNIJ black-anodized metric 2020 extrusion, Amazon B08Y8N7FD1
- 20 × 20 × 400 mm
- two rails used
- nominal 6 mm European-style slot

There is no rear crossrail.

Measured slot geometry from the actual extrusion is authoritative:

| Feature | Measured value |
|---|---|
| Slot mouth width | 0.258 in / 6.55 mm |
| Internal cavity width | 0.436 in / 11.07 mm |
| Slot depth | 0.254 in / 6.45 mm |
| Lip thickness | 0.065 in / 1.65 mm |

These dimensions support standardization on M5 hardware for 20-series / nominal slot-6 extrusion.

The selected T-nut hardware is Amazon B0DP6JBX4Y, a roll-in/drop-in spring-ball M5 type.

### 4.2 Front pivot plate

The current front-pivot-plate layout is a 180 × 150 × 12.7 mm Baltic-birch rounded rectangle, with the 180 mm
dimension transverse to the rails and the 150 mm dimension fore/aft. Use simple approximately 10 mm corner
radii; no structural cutouts are required. This geometry is the current baseline for layout, but the user
plans to verify it on a full-size paper template before final drilling.

Define plate coordinates with the origin at the midpoint of the mirror-facing edge, x transverse to the rails
and y aft, away from the mirror. The nominal pivot centers are:

- left pivot: (-47.50, 25.00) mm;
- right pivot: (+47.50, 25.00) mm;
- total pivot separation: 95 mm.

The nominal rail half-angle implied by the 95 mm pivot separation and approximately 3.2 m mirror distance is
about 0.850°, or about 1.70° total chief-ray separation. This angle calculation is provisional pending the
planned paper-template check.

Place each yaw-clamp station 90 mm aft along its nominal rail axis from the corresponding pivot. The nominal
yaw-strap centers are therefore approximately:

- left strap center: (-48.84, 114.99) mm;
- right strap center: (+48.84, 114.99) mm.

Each fixed yaw strap is oriented perpendicular to its rail at the nominal rail angle. Using the two outer
holes of the 3-hole joining plate gives fixed yaw-bolt centers at approximately:

- left outer: (-68.83, 114.69) mm;
- left inner: (-28.84, 115.29) mm;
- right inner: (+28.84, 115.29) mm;
- right outer: (+68.83, 114.69) mm.

Use approximately 5.5 mm round clearance holes for these four fixed yaw bolts; do not slot the plywood. The
straps remain fixed to the pivot plate while the 20 mm rails rotate beneath them. With 40 mm yaw-bolt spacing,
the rail has approximately 7.5 mm nominal edge-to-M5-shank clearance per side and retains about 2.8 mm
clearance at ±3° rail yaw from nominal for a 90 mm pivot-to-clamp distance. Rail-to-bolt contact would not
occur until roughly ±4.7° from nominal, so the fixed-hole geometry provides ample adjustment range.

The front Sorbothane support foot is centered at approximately (0, 25 mm), directly between the two rail
pivots. This keeps the support point on the pivot line and clear of the pivot and yaw hardware.

The 1/2 in Baltic-birch sheet stock is shared across the tabletop frame and mirror cell: it supplies the front
pivot plate, the two rear rail-support/foot blocks, the mirror-cell cell-adjuster plate, and the mirror-cell
base plate.

### 4.3 Pivot and yaw hardware

Pivot and yaw hardware use commercially available 2020 three-hole joining plates:

- MOPFOL 2020 3-hole joining plate, Amazon B0G8DCS7VP
- approximately 60 × 18 × 4 mm
- 20 mm hole pitch
- use four total: two as pivot lugs and two as yaw straps.

#### Pivot stack

Per rail:

socket head → oversized washer → 4 mm joining plate → 20 mm spacer → plywood pivot plate → oversized washer →
M5 nyloc

Hardware:

- McMaster 92290A265, M5 × 50 partially threaded 316 SS socket-head screw
- McMaster 92871A091, 20 mm × 10 mm OD × 5.3 mm ID stainless spacer
- McMaster 91116A350, M5 oversized washer, 15 mm OD
- McMaster 93625A225, M5 nylon-insert locknut

Approximately 5.5 mm pivot clearance holes in the plywood are appropriate.

#### Yaw lock

One 3-hole joining plate spans transversely across each rail. The two outer holes are used, giving 40 mm fixed
bolt-center spacing. The strap is fixed to the plywood by two round-hole through-bolts, one on each side of
the rail; the rail itself rotates beneath the strap. No slotted yaw holes are required in the plywood.

The current layout places each strap center 90 mm aft of its rail pivot along the nominal rail axis, with the
strap perpendicular to the nominal rail direction. Yaw adjustment and locking occur at the front mirror-facing
pivot plate by loosening the two thumb nuts, rotating the rail beneath the fixed strap, and retightening. The
resulting bolt/rail clearance supports at least approximately ±3° adjustment about nominal with useful
remaining clearance.

Hardware:

- McMaster 92290A265, M5 × 50 partially threaded 316 SS socket-head screws — same fastener as the rail pivots;
  use four for the yaw clamps
- McMaster 91116A350 oversized M5 washers
- McMaster 92815A202 M5 low-profile knurled thumb nuts

The yaw screws pass down alongside the 20 mm rail, not through it, but must still span the 4 mm yaw strap, the
full 20 mm rail height, the approximately 1/2 in (12.7 mm) Baltic-birch pivot plate, washers, and the
thumb-nut engagement. McMaster 92290A265, M5 × 50, is the baseline yaw-clamp screw. This intentionally reuses
the pivot-screw SKU rather than introducing a separate low-profile screw part.

### 4.4 Rear support and feet

Each rail has a removable 75 × 50 × 12.7 mm (3 × 2 × 1/2 in nominal) Baltic-birch rear foot block, cut from
the same 1/2 in sheet stock used elsewhere in the frame and mirror cell. The 75 mm dimension runs along the
rail and the 20 mm rail is centered across the 50 mm block width. Modest 3–5 mm corner radii are appropriate
to remove vulnerable sharp plywood corners.

Each block attaches to the rail bottom slot with two M5 socket-head screws, flat washers, and roll-in/drop-in
M5 T-nuts. The two screw holes lie on the rail centerline and are 50 mm apart, symmetrically placed about the
block center; with the 75 mm block length, each screw center is 12.5 mm from its nearest end. Use
approximately 5.5 mm clearance holes through the plywood. M5 × 20 mm screws from the general M5 assortment are
the nominal starting length; verify actual washer thickness and T-nut thread engagement during final fit and
use an adjacent stock length if required.

The Sorbothane foot is centered on the underside of the block, directly beneath the rail centerline and midway
between the two attachment screws. The 1-1/4 in / 31.75 mm diameter foot therefore does not obscure either
attachment screw or washer, allowing the complete plywood/foot assembly to be removed from and reinstalled on
the rail without disturbing the Sorbothane foot.

These blocks support the frame but do not provide the yaw lock.

Three-point table support:

- one centered foot beneath the front pivot plate;
- one foot beneath each rear support block.

Preferred feet:

- McMaster 8215K2, 1-1/4 in OD × 5/8 in high, 30 OO Sorbothane.

Backup stiffer set:

- McMaster 8215K6, same size.

Moderate static compression of the front foot is acceptable. The resulting small overall pitch can be
corrected during optical alignment.

### 4.5 General 2020 fastener standard

Standardize ordinary 2020 attachments on M5 × 0.8 socket-head hardware with flat washers and the selected
roll-in/drop-in M5 T-nuts. Final screw length is determined by the local stack-up; the design should prefer
common metric lengths and avoid introducing special fastener sizes without need.

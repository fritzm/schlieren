## 13. Immediate outstanding procurement

Detailed purchasing state remains authoritative in the canonical BOM. As of the latest BOM reconciliation, the
BOM contains 131 entries with the following states:

- 116 In hand;
- 1 On order;
- 2 To procure;
- 2 Specified;
- 7 CAD ready;
- 3 CAD open.

The flexure slit head decision (§9) needs no procurement: its hardware is reallocated from in-hand carriage
stock, and its three printed parts are tracked as CAD ready (the head has had a successful first test print).

The line On order is McMaster 91545A410 M2 nylon insulating washers.

The threaded LED module decision (§6.5) adds the remaining procurement:

- To procure: Thorlabs SM1CP2M externally threaded end caps (2) and Alpha CN40-40B pin-fin heatsinks (2);
- Specified, vendor/SKU or quantity still to be confirmed: M3 × 6 mm socket-head heatsink screws (provisional
  length), and an M3 × 0.5 tap with 2.5 mm tap drill if not already in shop stock.

Printed custom parts remain tracked separately as CAD ready or CAD open rather than as procurement items.

## 14. Remaining design work and recommended sequence

The project is predominantly in the detailed-CAD and build-validation phase rather than optical-architecture
development.

### 14.1 CAD-ready clusters

The following have sufficient requirements to begin CAD immediately:

1. Common rail-to-TR50/M post shoe
   - measured rail geometry;
   - 20-series M5 roll-in T-nut interface;
   - rail-top metal datum;
   - 12.7 mm post bore;
   - common single-split post clamp.

2. Threaded LED modules (no printed parts; drilling and tapping only)
   - M2 board holes in the SM1CP2M front face, laid out from its center-drill mark;
   - blind M3 heatsink holes in the cap rear, offset from the board holes;
   - lead pass-through holes at r ≈ 11 mm through cap and CN40 base;
   - bench-test the CN40-40B temperature rise at 700 mA;

3. Cutoff carriage
   - shouldered spigot in the SM1RC/M;
   - FAS100 fine adjuster;
   - opposed spring plunger;
   - slotted plunger-guide rails;
   - spring cups and thumb-tab retraction;
   - rotation-envelope trim clearing the rail;
   - eight-screw keeper;
   - rear datum seating;
   - common 64 mm cassette.

4. Cutoff cassette blanks and derivatives
   - knife edge;
   - wire cutoff;
   - color-filter variants.

5. Mirror-cell detailed CAD
   - exact 120° adjuster coordinates;
   - spring-seat counterbore depths;
   - close-fit spherical-washer socket diameters;
   - safety retainers;
   - travel cover;
   - final tripod balance point.

The source-slit flexure head (§9) is CAD complete (`src/schlieren/parts/slit_head.py`). The first test print
of the head confirmed the insert, magnet, and spring fits and the flexure motion; adapter and clamp-bar
assembly, preload, parallelism, and creep checks remain (§9.7).

### 14.2 Primary unresolved design cluster

The remaining substantial design problem is the iPhone cradle and telephoto lens cradle/support system.

The requirements constrain the problem but do not yet define a preferred detailed geometry.

Work still required includes:

- exact floating-phone-cradle shape;
- phone retention and case clearances;
- two-jack contact geometry;
- vertical guide strategy;
- lift-off retention;
- rail attachment geometry;
- lens saddle profile;
- lens retention;
- relationship between phone and lens supports;
- removal/reinstallation sequence;
- avoiding transfer of telephoto weight through the phone mount;
- packaging around the cutoff carriage and rail.

### 14.3 Recommended next sequence

1. CAD the common post shoe first; it establishes a repeated rail interface used by three stations.
2. Procure the SM1CP2M caps and CN40-40B heatsinks; fabricate both threaded LED modules, center each board,
   and set focus on the slit blades. Confirm the white module reaches focus within its reduced (about
   0.93 mm) long-gap margin; if not, add a thin cap-flange shim (§6.5).
3. CAD the cutoff carriage, plunger guides, guide rod, and cassette blank.
4. Test-print the source-slit flexure head (§9.7): check flexure-blade, insert, spigot, and nut-pocket fit,
   the width-stage preload, and slit parallelism and rotation against the first-order estimates.
5. Derive knife-edge, wire, and color-filter cassettes from the common blank.
6. Develop the phone and telephoto support architecture.
7. Complete the detailed mirror-cell drawings, including washer counterbores and safety/transport pieces.
8. Assemble the tabletop optical head and perform a dry optical layout near 3.2 m before committing any
   remaining irreversible holes or bonds.
9. Perform mirror-cell RTV bonding only after a successful dry mechanical fit and adhesion test.

Build-status update: the stationary mirror-cell adjuster plate and moving mirror plate have been completed and
assembled. The three-adjuster/spring/spherical-washer mechanism has been physically assembled and appears
mechanically satisfactory. The mirror itself is intentionally not yet RTV-bonded. Because there is
insufficient cure time before travel, mirror installation is deferred until arrival; transport the mirror
separately/protected and perform the established dry fit, centering, six-pad DOWSIL 737 bonding, and cure
procedure at the destination.

The governing CAD principle is:

> Printed ABS should provide shape, capture, guidance, interchangeability, and convenient adjustment; metal
> hardware, optical posts, shims, mechanical stops, and commercial precision components should establish the
> important datums, threads, and wear/load-transfer interfaces.

## 15. Canonical BOM and procurement record

Detailed BOM and procurement information is maintained separately in the canonical BOM file:

`bom/bom.csv`

(a generated Google Sheet / .xlsx view is built from it by `uv run build-bom-xlsx`). The BOM is
authoritative for:

- BOM contents and quantities;
- manufacturers, vendors, and part numbers;
- procurement state and order status;
- installed/spare/shared allocation;
- purchasing and inventory notes;
- shop supplies and consumables.

This design-status report intentionally does not duplicate detailed BOM or procurement state. [Section
13](13-status-and-procurement.md#13-immediate-outstanding-procurement) retains only the near-term
outstanding-procurement rollup needed for planning; detailed quantities, purchasing state, allocation, and
inventory changes belong in the BOM workbook.

## 13. Immediate outstanding procurement

Detailed purchasing state remains authoritative in the canonical BOM. As of the latest BOM reconciliation, the
workbook contains 118 entries with the following states:

- 98 In hand;
- 12 On order;
- 0 To procure;
- 5 CAD ready;
- 3 CAD open.

There are therefore no unplaced procurement items in the current design baseline. The remaining procurement
activity consists only of waiting for already-ordered items.

The 12 BOM lines currently On order are:

- Thorlabs SM1D12 adjustable iris;
- Convoy Nichia 519A R9080 5000 K white LED stock;
- McMaster 91545A410 M2 nylon insulating washers;
- 44 AWG enameled copper magnet wire for experimental dark-field cutoff filaments;
- 34 AWG enameled copper magnet wire for experimental dark-field cutoff filaments;
- 30 AWG enameled copper magnet wire for experimental dark-field cutoff filaments;
- McMaster 92125A194 M4 × 0.7 × 16 mm 90° flat-head screws for the quick-release plate;
- McMaster 92125A196 M4 × 0.7 × 18 mm 90° flat-head screws for the quick-release plate;
- Amazon B0B2WBC921 CAMVATE Manfrotto-type 577/501/504-compatible quick-release assembly;
- McMaster 1021N23 M4 × 0.7 plug-chamfer tap;
- McMaster 2958A64 3.3 mm tap drill;
- McMaster 91458A115 / Loctite 243 medium-strength removable threadlocker.

The three cutoff-wire lines remain On order; their Amazon references are recorded in the canonical BOM. All
other purchased physical components currently represented in the BOM are In hand. Printed custom parts remain
tracked separately as CAD ready or CAD open rather than as procurement items.

Procurement is therefore effectively complete for the currently specified design: no additional purchase
decisions are required unless physical fit checks or later design changes introduce new hardware.

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

2. Common LED module fixture
   - M4 threaded post-top attachment and flat post-top seating datum;
   - LED support post behind the heatsink, with bracket reaching forward;
   - coarse fore/aft positioning by sliding the dedicated LED rail shoe;
   - opposed forward-reaching octagonal-heatsink guide/gripping fingers;
   - small yaw trim by rotating the bracket about the post axis before tightening the M4 attachment;
   - ±2–3 mm calibration travel;
   - per-module calibrated bracket; localized CA tacks remain optional after alignment;

3. Common slit/cutoff carriage
   - SM1L15 split clamp;
   - FAS100 fine adjuster;
   - opposed spring plunger;
   - slotted plunger-guide rails;
   - anti-buckling spring guide/retract rod;
   - rear datum seating;
   - common 64 mm cassette.

4. SM1L15 tube retaining ring
   - 4–5 mm axial width;
   - 3–4 mm radial wall;
   - M3 split clamp.

5. Cassette blanks and derivatives
   - source slit;
   - knife edge;
   - wire cutoff;
   - color-filter variants.

6. Mirror-cell detailed CAD
   - exact 120° adjuster coordinates;
   - spring-seat counterbore depths;
   - close-fit spherical-washer socket diameters;
   - safety retainers;
   - travel cover;
   - final tripod balance point.

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

1. CAD the common post shoe first; it establishes a repeated rail interface used by four stations.
2. CAD the LED module fixture around the M4 post-top attachment, flat post-top datum,
   rear-post/forward-reaching bracket geometry, and actual heatsink measurements.
3. CAD the common slit/cutoff carriage, plunger guides, guide rod, and cassette blank.
4. CAD the tube retaining ring.
5. Measure the physical Stanley blades and complete the slit cassette.
6. Derive knife-edge, wire, and color-filter cassettes from the common blank.
7. Develop the phone and telephoto support architecture.
8. Complete the detailed mirror-cell drawings, including washer counterbores and safety/transport pieces.
9. Assemble the tabletop optical head and perform a dry optical layout near 3.2 m before committing any
   remaining irreversible holes or bonds.
10. Perform mirror-cell RTV bonding only after a successful dry mechanical fit and adhesion test.

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

(a generated Google Sheet / .xlsx view is built from it by `bin/build-bom-xlsx`). The BOM is
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

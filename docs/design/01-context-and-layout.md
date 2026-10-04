# Portable Single-Mirror Schlieren Apparatus

**Design Description**

Revision: Oct 2, 2026

This document describes the design of the apparatus, and is maintained authoritatively as Markdown fragments
in the project repo on github at https://github.com/fritzm/schlieren/tree/main/docs/design.

## Conventions

- The design described here is the baseline. Unless marked otherwise, dimensions, parts, and methods are
  settled.
- **Provisional** marks a design area, dimension, or method that is still open or evolving, typically pending
  a physical fit check, measurement, or further design. Provisional areas are rolled up with next steps in
  [§12](12-open-work.md#12-provisional-areas-and-next-steps).
- Measured values, manufacturer specifications, and calculated values are identified as such where the
  distinction matters; a measured value takes precedence over a catalog value.
- Quantities, vendors, part numbers beyond those needed to define the design, procurement state, and the CAD
  state of printed parts are recorded in the BOM, `bom/bom.csv`, not here.

## 1. Project context and design constraints

The apparatus is a portable, single-mirror schlieren system intended initially for several days of
vacation/travel use in a location with a large room and a substantial tabletop. It should remain useful
afterward as a bench-top laboratory instrument.

The complete system should pack into a standard airline rolling suitcase. Plan around the ordinary 50 lb / 23
kg checked-bag target unless a higher allowance applies.

The design is cost-conscious rather than constrained to a fixed dollar ceiling. Commodity 2020 extrusion,
Baltic birch plywood, standard fasteners, and printed ABS are preferred where they are adequate. Commercial
optomechanics are used where they materially simplify alignment or provide precision that would otherwise be
troublesome.

### 1.1 Fabrication envelope

Near-term 3D printing is ABS only. Critical optical heights and precision datums should preferably be
established by metal posts, optical hardware, shim stock, mechanical stops, or adjustment mechanisms rather
than relying solely on as-printed ABS dimensions.

The following are out of scope:

- custom machined parts requiring a mill or lathe;
- cutting stainless-steel stock or sheet to custom shape or length.

Use off-the-shelf metal parts, vendor-supplied finished dimensions, plywood, aluminum that can be
drilled/tapped with ordinary shop tools, thin foil, or printed ABS. Simple drilling and tapping of the
aluminum LED carrier caps and heatsinks is within scope.

A table saw, drill press, and small hand router are available and are expected to be used for accurate working
of Baltic birch plywood panels (thanks, Bret!)

## 2. System overview and physical layout

The apparatus consists of two main physical assemblies:

1. a tabletop optical head; and
2. a separate mirror cell, normally tripod-mounted approximately 3.2 m away.

The tabletop optical head uses two independently yaw-adjustable 2020 aluminum-extrusion rails mounted to a
common Baltic-birch front pivot plate. The rails diverge slightly away from the mirror-facing end so that each
rail follows one optical chief ray:

- the source rail carries the illumination system directed toward the mirror;
- the imaging rail carries the cutoff and camera system for the return beam.

The source rail contains, in optical order:

1. interchangeable threaded LED/heatsink source module, screwed into the condenser holder;
2. condenser and adjustable iris;
3. source-slit flexure head.

The slit is the effective optical source. The LED primarily illuminates that slit through the condenser and
therefore does not itself require the same precision vertical positioning as the slit.

The imaging rail contains:

1. cutoff carriage at the returned slit-image plane;
2. telephoto lens support;
3. iPhone cradle.

The spherical mirror forms an image of the source slit back near the optical head. Refractive-index gradients
in the test region near the mirror deflect portions of this return beam relative to the cutoff, producing
schlieren contrast.

Several source-side and cutoff-side fixtures deliberately share common mechanics. Three locations use a
common TR50/M post + printed rail shoe concept:

1. LED/condenser/iris;
2. source-slit flexure head;
3. cutoff carriage.

The source slit and the cutoff both rotate about the optical axis in a Thorlabs SM1RC/M SM1 slip ring. The
slit uses a flexure head with fine centering and slit-width adjustment (§8); the cutoff uses a rotating
carriage with a 64 mm cassette envelope, allowing knife-edge, wire, and color-filter experiments without
changing the supporting mechanism (§9).

The mirror cell uses a three-point, approximately 120°-spaced fine-adjustment architecture with compression
springs and spherical washer interfaces. The mirror is compliantly supported in the moving plate by six radial
DOWSIL 737 pads between the mirror edge and the inner surface of the plywood aperture.

## 3. System-level geometry

### 3.1 Primary optic

- Mirror: Skyoptikst D203F1600
- Diameter: 203 mm
- Focal length: 1600 mm
- Surface: spherical
- Radius of curvature / nominal operating distance: approximately 3200 mm

The source slit and imaging/cutoff system operate near the mirror center of curvature. The test region is near
the mirror, where outgoing and returning beams remain close together.

The source slit is the effective optical source. The spherical mirror re-images the slit near the optical
head; the returned slit image defines the cutoff plane.

### 3.2 Source cone

At 3200 mm, the mirror subtends a half-angle of approximately:

$$
\theta=\tan^{-1}(101.5/3200)\approx1.82^\circ
$$

The intended illumination cone is approximately ±1.8° to ±2.0°, corresponding to approximately NA =
0.032–0.035 in air. Slight mirror overfill is preferred to underfill.

Useful nominal beam diameters for a ±1.8° cone are:

| Distance from source slit | Approx. beam diameter |
|---------------------------|-----------------------|
|                       1 m |                 63 mm |
|                       2 m |                127 mm |
|                     3.2 m |                203 mm |

The mirror's approximately f/7.9 focal ratio should not be confused with this source cone. The source operates
near 2f, at approximately the mirror center of curvature.

### 3.3 Source/imager separation

The two rail pivot centers are separated by 95 mm at the mirror-facing front plate. At 3.2 m this gives
approximately 1.70° total chief-ray separation.

Each rail points toward the mirror and follows its own chief ray. Sliding a fixture along a rail is therefore
predominantly an axial adjustment.

The source slit and cutoff need not occupy exactly the same longitudinal coordinate. Near 2f,

$$
\frac{ds_i}{ds_o}\approx -1
$$

so small source-slit displacement produces approximately equal and opposite conjugate-image displacement.

A useful starting point is about 30–40 mm total slit/cutoff longitudinal staggering, obtained by placing them
approximately ±15–20 mm around nominal 2f. This is an experimental setup adjustment rather than a
fabrication-critical dimension.

### 3.4 Common optical-axis datum

The common optical axis is 72.35 mm above the top surface of the 2020 extrusion.

For optical-head CAD:

- take the rail top surface as z = 0;
- do not reference optical height to the tabletop or support feet;
- small whole-frame pitch/roll errors can be corrected at the mirror.

The common post stack is:

- 0.010 in / 0.254 mm metal datum shim;
- 50 mm Thorlabs TR50/M post;
- 22.1 mm post-top-to-optical-axis offset for the SM1 optical holders (Thorlabs SMR1/M: 0.870 in /
  22.098 mm exact);
- total nominal height: 72.35 mm (72.352 mm with the exact SMR1/M offset; the datum is 72.35 mm).

The datum discs are McMaster 2895T62, 3/4 in OD × 0.010 in ±0.0005 in thick, full-hard 18-8 stainless
steel, minimum Rockwell C40. Three discs are used as post datum shims, one under each common post fixture. The
discs provide a consistent metal seating surface for the posts across the central slot in the 2020 rail.

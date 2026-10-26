# Portable Single-Mirror Schlieren Apparatus

**Design Description**

Revision: Oct 25, 2026

This document describes the design of the apparatus, and is maintained authoritatively as Markdown fragments
in the project repo on GitHub at <https://github.com/fritzm/schlieren/tree/main/docs/design>.  It serves as
durable context for AI assistants to reason about the design, as well as being a human-readable guide.

## Conventions

- The design described here is the baseline. Unless marked otherwise, dimensions, parts, and methods are
  settled.
- **Provisional** marks a design area, dimension, or method that is still open or evolving, typically pending
  a physical fit check, measurement, or further design. Provisional areas are rolled up with next steps in
  [§11](11-open-work.md#11-provisional-areas-and-next-steps).
- Measured values, manufacturer specifications, and calculated values are identified as such where the
  distinction matters; a measured value takes precedence over a catalog value.
- Quantities, vendors, part numbers beyond those needed to define the design, procurement state, and the CAD
  state of printed parts are recorded in the associated BOM at (`bom/bom.csv`), not here.

## 1. Project context and design constraints

The apparatus is a portable, single-mirror schlieren system intended initially for several days of
vacation/travel use in a location with a large room and a substantial tabletop. It should remain useful
afterward as a bench-top laboratory instrument.

The complete system should pack into a standard airline rolling suitcase. Plan around the ordinary 50 lb / 23
kg checked-bag target.

The design is cost-conscious rather than constrained to a fixed dollar ceiling. Commodity 2020 extrusion,
Baltic-birch plywood, standard fasteners, and printed PLA are preferred where they are adequate. Commercial
optomechanics are used where they materially simplify alignment or provide precision that would otherwise be
troublesome.

### 1.1 Fabrication envelope

Near-term 3D printing is PLA only. Critical optical heights and precision datums should be established by
metal posts, optical hardware, shim stock, mechanical stops, or adjustment mechanisms rather than relying
solely on as-printed PLA dimensions.

The following are out of scope:

- custom machined parts requiring a mill or lathe;
- cutting stainless-steel stock or sheet to custom shape or length.

Use off-the-shelf metal parts, vendor-supplied finished dimensions, plywood, thin foil, or printed PLA.
Drilling and tapping of aluminum parts is within scope.

A miter saw, drill press, and small hand router are available for working of plywood panels (thanks, Bret!).

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

1. light source (with interchangeable threaded LED/heatsink modules, condenser lens, and adjustable iris)
2. source-slit flexure head

The slit is the effective optical source, with the LED illuminating it through the condenser and iris. The
imaging rail contains, in optical order:

1. cutoff carriage at the returned slit-image plane;
2. lens cradle, which supports and aligns a telephoto lens;
3. phone rest, which supports an iPhone hanging from the lens as a camera.

A spherical mirror in a separate tripod-mountable cell forms an image of the source slit back near
the optical head. Refractive-index gradients in the test region near the mirror deflect portions of this
return beam relative to the cutoff, producing schlieren contrast.

## 3. System-level geometry

### 3.1 Primary optic

- Mirror: Skyoptikst D203F1600
- Diameter: 203 mm
- Focal length: 1600 mm
- Surface: spherical
- Radius of curvature / nominal operating distance: approximately 3200 mm

The source slit and imaging/cutoff system operate near the mirror center of curvature. The test region is near
the mirror, where outgoing and returning beams remain close together.

The returned slit image defines the cutoff plane.

### 3.2 Source cone

At 3200 mm, the mirror subtends a half-angle of approximately:

$$
\theta=\tan^{-1}(101.5/3200)\approx1.82^\circ
$$

The intended illumination cone is approximately ±1.82° (the mirror's half-angle, just filling it) to ±2.0°,
corresponding to approximately NA = 0.032–0.035 in air. Slight mirror overfill is preferred to underfill.

Useful nominal beam diameters for the ±1.82° cone are:

| Distance from source slit | Approx. beam diameter |
| ------------------------- | --------------------- |
| 1 m                       | 63 mm                 |
| 2 m                       | 127 mm                |
| 3.2 m                     | 203 mm                |

The mirror's approximately f/7.9 focal ratio should not be confused with this source cone. The source operates
near 2f, at approximately the mirror center of curvature.

### 3.3 Source/imager offset

The two rail pivot centers are separated by 95 mm at the mirror-facing front plate. At 3.2 m this gives
approximately 1.70° total chief-ray separation.

Each rail points directly toward the mirror and follows its own chief ray. Sliding a fixture along a rail is
therefore predominantly an axial adjustment.

The source slit and cutoff need not occupy exactly the same axial position. Near 2f,

$$
\frac{ds_i}{ds_o}\approx -1
$$

so small source-slit displacement produces approximately equal and opposite conjugate-image displacement.
This can be an aid in avoiding mechanical interference between fixtures on opposite rails.

A useful starting point is about 30–40 mm total slit/cutoff axial staggering, obtained by placing them
approximately ±15–20 mm around nominal 2f. This is an experimental setup adjustment rather than a
fabrication-critical dimension.

### 3.4 Common optical-axis datum

The common optical axis is 72.35 mm above the top surface of the 2020 extrusion, established by commercial
optomechanics to simplify alignment.  The stack-up is:

<table style="border-collapse: collapse; border: none; margin-left: 2em; line-height: 1.4;">
<tr><td style="text-align: right; padding: 0 1em 0 0.6em; border: none;">0.254</td><td style="padding: 0; border: none;">Steel datum shim on rail (bridges the rail top channel)</td></tr>
<tr><td style="text-align: right; padding: 0 1em 0 0.6em; border: none;">50.000</td><td style="padding: 0; border: none;">Thorlabs TR50/M post</td></tr>
<tr><td style="text-align: right; padding: 0 1em 0.5em 0.6em; border: none;">22.098</td><td style="padding: 0 0 0.5em; border: none;">Post-top to axis for Thorlabs SM1 optical holders</td></tr>
<tr><td style="text-align: right; padding: 0.5em 1em 0 0.6em; border: none; border-top: 1px solid currentColor;">72.352</td><td style="padding: 0.5em 0 0; border: none; border-top: 1px solid currentColor;"></td></tr>
</table>

### 3.5 Coordinate frames

For optical-head CAD:

- take the rail-top surface as z = 0;
- do not reference optical height to the tabletop or support fixtures.

The optical head uses three coordinate frames with common senses:

- +y forward, toward the mirror;
- +x to the right when looking down from above with the mirror ahead;
- +z up, with the rail top at z = 0.

These frames are right-handed and differ only in where their y axes lie:

- pivot frame: y along the centerline of the front pivot plate, with the origin at the midpoint of its aft
  edge ([§4.2](04-frame.md#42-front-pivot-plate));
- source rail frame: y along the source rail centerline;
- imaging rail frame: y along the imaging rail centerline.

Each rail frame yaws with its rail, about 0.85° from the pivot frame at nominal
([§4.2](04-frame.md#42-front-pivot-plate)). Its origin is on the rail top at the rail's pivot axis; a fixture
is described with its own rail station at y = 0. In a rail frame the optical axis is at x = 0, z = 72.35 mm,
and pitch, yaw, and roll are rotations about x, z, and y respectively. A rotating fixture may define a local
frame, stated where it is used.

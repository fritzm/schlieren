## 7. Source slit

The source slit is a pair of razor blades, one on the table of a purchased 40 × 40 mm linear stage and one on a
printed pedestal, with the stage's micrometer setting the slit width. The head is mounted for continuous
rotation about the optical axis in an SM1RC/M on the common post and rail shoe
([§5](05-post-support.md#5-common-rail-mounted-post-support)). A baffle tube behind it on the source side is
clamped on a post of its own ([§7.8](#78-baffle-tube)), and a printed focus target stands in for the head to
focus the LED image ([§7.7](#77-slit-focus-target-provisional)).

The model is `src/schlieren/parts/slit_stage.py` (`uv run slit-stage`, with `--show` for the viewer assembly).

The slit needs one adjustment, its width, and no interchangeable elements, so a purchased stage with a
micrometer serves where the cutoff uses a carriage and cassettes ([§8](08-cutoff.md#8-cutoff)).

### 7.1 Blades and slit widths

The slit uses two Stanley 11-515 backed single-edge scraper blades.

Measured physical blade dimensions:

- length: 1.537 in / 39.04 mm
- width, cutting edge to the outside of the fold: 0.773 in / 19.64 mm
- plate thickness: 0.010 in / 0.254 mm
- fold: the back edge is folded over both faces, 0.277 in / 7.04 mm deep on each, 0.040 in / 1.016 mm thick across
  the fold
- bevel on both faces, breaking 0.030 in / 0.76 mm back from the cutting edge.

The blade has a slot at mid-length and a notch in each end, approximated in the CAD from a photograph (about
±0.3 mm); the slit and cassette fixtures do not rely on them. The CAD model is `parts/razor_blade.py`.

Expected operating slit widths are 0.10–0.30 mm, starting around 0.15–0.20 mm.

Each blade rests on its seat, the stage table or the pedestal, cutting edge toward the slit and overhanging the
seat edge by 2.9 mm. The fold's outer layers stand 0.38 mm proud of the plate's faces, so the blade touches the
seat only at the seat edge (with the plate face) and at the fold's front edge (with the fold's outer layer), 12.6
mm back from the cutting edge. Between the two the plate is inclined toward the fold by about 2°. No blade
pockets, holes, or spine compensation are used. The inclination is acceptable because the optically important
geometry is the gap and the parallelism of the two cutting edges: the two blades are identical and seated alike,
so their edges lie at the same height above the seat plane (about 0.05 mm ahead of it at the seat edge's
contact), collinear were the slit closed, whatever the exact fold thickness.

### 7.2 Architecture

The head is a stage plate carrying the stage and a pedestal:

1. stage plate: a 6 mm printed plate with the spigot and shoulder for the SM1RC/M;
2. stage: a 40 × 40 mm linear stage with a micrometer drive (Amazon B0B7RVW3SX, an SF Technology SEMX40-AS
   type, ±6.5 mm of travel), bolted to the plate front; its table carries the movable blade;
3. pedestal: a printed block on the plate carrying the stationary blade at the same height as the table.

Local frame, at rotation 0: x along the slit, z the adjustment axis with the micrometer toward +z, y along the
optical axis toward the mirror; the origin is the slit center in the blade-seat plane. The blade-seat plane
(the table top and the pedestal top) is the front of the head; the stage's 20 mm thickness puts it 20 mm ahead
of the plate front. In this section "front" and "back" refer to the head, not to the rail direction.

The head's front faces the mirror. The light comes from the source side through the baffle tube and the plate's
Ø24 mm bore and passes the stage's edge to reach the slit from behind, so the spigot, ring, and post are on the
light-source side of the blades. The source cone is ±2° about the chief ray and the lit slit length is ±5 mm
([§6.6](06-light-source.md#66-condenser-optics)); the stage and pedestal edges keep 1.65 mm from the cone.

<p align="center">
  <img src="figures/slit-stage.png" width="300" style="max-width: 90%"
       alt="Stage slit head from the mirror side: the stage plate, the linear stage with its micrometer, the
       pedestal, the two blades with their toe bars, and the baffle tube, on posts and rail shoes">
  <br>
  <em>Fig. 8. Stage slit head and baffle tube on their posts and rail shoes, seen from the mirror side: the
    movable blade on the stage table, the stationary blade on the pedestal, a toe bar over each, and the
    micrometer up</em>
</p>

### 7.3 Slit width

- drive: the stage's micrometer, moving the table and so the movable blade; travel ±6.5 mm (manufacturer);
- the slit is 0.2 mm in the model, within the 0.10–0.30 mm working range of [§7.1](#71-blades-and-slit-widths).

There is no centering stage. Only the movable blade moves, so a width change shifts the slit center by half the
change. The iris is about 150 mm before the slit, so moving the slit by d turns the illumination cone by d/150;
at the mirror the beam moves about 21 × d. A 0.1 mm width change therefore moves the slit center 0.05 mm and
the beam about 1 mm at the mirror, which needs no recentering (the cutoff is readjusted for any width change
in any case).

Slit setup:

1. with both toe bars loose, bring the movable blade to the pedestal blade with the micrometer;
2. seat both blades and clamp them progressively ([§7.4](#74-blade-clamping));
3. set the width against a true-metric feeler gauge between the cutting edges, pressing gently along their
   length;
4. thereafter set the width with the micrometer from that reference. Re-check parallelism with the gauge after
   large width changes.

### 7.4 Blade clamping

Each blade is pinched against its seat by a printed PLA toe bar. One bar sits on the stage table and one on the
pedestal; each is screwed down at its two ends into the stage's M3 table holes (second row, 16 mm pitch) or
into M3 heat-set inserts (McMaster 97171A310) in the pedestal. The bar's finger runs the length of the blade,
reaches over the fold, and drops a toe onto the plate just short of the fold's front edge, through a strip of
1/32 in EPDM (McMaster 9852N37, the stock of [§4.3](04-frame.md#43-pivot-and-yaw-hardware)). Nothing crosses
the cutting edge and no blade is drilled.

The toe presses between the blade's two contacts with its seat, the seat edge and the fold's front edge, so
that the clamp load holds the blade on both; a load behind the fold's front edge would lever the cutting end
up off the seat. The toe's squeeze on the EPDM pad is 0.3 mm. The common McMaster 91292A114 M3 × 12 mm screw is
used.

### 7.5 Rotation mount and clearances

The stage bolts to the plate front with four M3 screws on its 32 mm base-hole pitch, with captive M3 nuts (the
common 91828A211) in pockets in the plate rear. The pedestal is screwed to the plate from the rear into two M3
heat-set inserts in the pedestal (97171A310).

The plate carries a hollow Ø30.48 mm (SM1 tube OD) spigot with a Ø24 mm light bore, clamped by the SM1RC/M
split ring (Ø30.7 mm bore, 10.16 mm thick, M4 locking screw across the split). A Ø34 mm shoulder on the spigot
is the ring's axial stop: the ring seats against it, which places the plate 3.5 mm in front of the ring face.
Do not clamp the ring away from the shoulder. The nut pockets reach inside the spigot's radius, so the spigot
is restored behind the shoulder and roofs them, and the ring grips a full cylinder.

The spigot runs the ring's full thickness, and the ring clamps nothing else; the baffle tube
([§7.8](#78-baffle-tube)) ends 1.0 mm short of the ring's source face. The SM1RC/M keeps the 22.1 mm
post-top-to-axis dimension ([§5.1](05-post-support.md#51-post-and-shim)). Loosening the ring rotates the whole
head about the optical axis:

- rotation 0: horizontal slit, micrometer up;
- ±90°: vertical slit, micrometer sideways. With the micrometer toward the imaging rail it reaches the cutoff
  carriage's base plate unless the cutoff is staggered behind the slit by about 16 mm or more (the 30–40 mm
  starting stagger of [§3.3](01-context-and-layout.md#33-sourceimager-offset) clears it by about 20 mm); turned outboard it clears at
  any stagger;
- small rotations: slit-to-cutoff parallelism trim.

The rotation sweep clears the post, ring, and rail shoe in the tests.

### 7.6 Fabrication and fit

Printed parts: the stage plate, the pedestal, and two toe bars.

- Plate: print front face down, spigot up; no supports.
- Pedestal: print top face down, so the blade seat is the first layer.
- Toe bars: print flat, heel side down.
- The spigot is printed at the SM1 tube nominal, which fits the SM1RC/M.

Hardware: the stage, 4 × M3 screws (stage to plate), 4 × M3 nuts, 2 × M3 × 12 mm screws (pedestal to plate),
4 × M3 × 12 mm screws (toe bars), 4 × M3 heat-set inserts, 2 strips of EPDM.

**Provisional:**

- The stage's dimensions are the manufacturer's (the table layout, 20 mm thickness, ±6.5 mm travel), not
  measurements of the stage on hand. The model shows Misumi's XCRS40, which has the same table and base layout
  and a solid CAD model. The base-hole pitch, the table's tapped holes, the micrometer reach, and the base
  flange thickness are to be measured, and the base mounting holes (four M3, counterbored) are assumed reachable
  from the table side.
- The blade overhang and the toe bar's squeeze on the EPDM pad (0.3 mm) are first-print values.
- The M3 × 12 mm stage screws leave about 3 mm of thread behind the plate, 0.5 mm short of the ring face. M3 × 10
  mm screws would leave about 1 mm and 2.5 mm of clearance, with the thread still showing past the nut; the
  length rests on the stage's base flange thickness, which is not yet measured.


### 7.7 Slit focus target (Provisional)

The emitter image is focused on the slit plane ([§6.7](06-light-source.md#67-focus-and-module-interchange)), but
the blades of the head sit deep in the stage and cannot be seen. A printed focus target swaps in for the
stage plate on the same SM1RC/M ring: the same shoulder, ring gap, and spigot grip, then a hollow barrel that
widens to a Ø40 mm rim whose face is the blade-seat plane. The baffle tube stays in its own ring on its own post
through the swap. The models are
`src/schlieren/parts/slit_focus_target.py` and `slit_focus_screen.py` (`uv run slit-focus-target`,
`uv run slit-focus-screen`). **Provisional.**

A sheet of tracing paper lies on the rim and a printed Ø40 × 6 mm retaining ring, with a Ø22 mm window about the
baffle tube's clear bore, clamps it. Four M3 × 12 mm socket-head screws on a Ø32 mm circle run into heat-set
inserts (97171A310) in the rim. The LED image forms on the paper's source-facing side and is read through the
paper from the mirror side, so the turn of the SM1V05 can be judged by eye before the head is fitted. The
rim face is the datum, so the paper's thickness (not yet measured; the model assumes 0.15 mm) offsets the focus
plane from the blade-seat plane by that much.

A variant replaces the paper with a Ø1 in ground-glass disc (Thorlabs DG10 series, catalog 2.0 ± 0.2 mm thick)
in a counterbore in the rim, ground face toward the source, pushed forward by a gasket cut from 1/16 in Durometer 30A neoprene sheet against the ring, so that the ground
surface is at the datum whatever the glass thickness. Its counterbore clearance is to be set from a printed
coupon, and the grit (DG10-600 to start) is to be confirmed on the bench.

### 7.8 Baffle tube

A baffle tube sits on the source side of the slit head, on the optical axis. Two Thorlabs
SM1L15 lens tubes (1.5 in thread depth), threaded together, form a tube Ø30.48 mm outside, 80.6 mm long, with a
Ø22.9 mm clear bore (the SM1L15 retaining-ring bore). It is clamped in a Thorlabs SM1RC/M split ring on its own
post, datum shim, and rail shoe ([§5](05-post-support.md#5-common-rail-mounted-post-support)), 40 mm upstream
of the slit head's post, so the two shoes leave 10 mm of rail between them. The tube's open end stops 1.0 mm
short of the head ring's source face, 40.7 mm behind the blade-seat plane, and the tube
projects 34.6 mm past its own ring toward the source, ending about 29 mm short of the iris.

**Motivation.** The condenser focuses the LED image, about 10 mm across, on the blades
([§6.6](06-light-source.md#66-condenser-optics)), and a slit of 0.10–0.30 mm passes only a small fraction of it.
The blades return the remainder, and the head's lit surfaces scatter some of it. That light goes back toward
the source as a broad cloud, strikes the bare post, the source hardware, and the table behind the head, and is
forwarded by them, glossy surface to glossy surface, toward the mirror and the operator at the imaging
station. The cloud lights the room and adds veiling glare to the image. A tube immediately behind the head
confines the return to the direction of the LED: it travels back through the bore toward the iris, and the
rest meets the black anodized wall. This reduced the stray light greatly.

**Beam.** The tube bounds the light but does not stop down the beam. The beam on the source side of the slit
lies between the iris aperture (about Ø9–10.5 mm, [§6.7](06-light-source.md#67-focus-and-module-interchange))
and the lit slit length (±5 mm), so it is about Ø10–11 mm over the whole tube, with the ±2° cone about the chief
ray inside that envelope. The Ø22.9 mm bore leaves more than 5 mm of radius all around, so no alignment
tolerance of the two posts clips the beam, and the tube's length is set by its ring and its distance from the
iris, not by the beam. At the slit end the beam is bounded by the head instead, not the tube: the stage and pedestal edges keep 1.65
mm from the cone ([§7.2](#72-architecture)).

**Separate ring.** The tube has its own SM1RC/M rather than sharing the head's, for two reasons. A shared ring
closes on whichever of the printed spigot and the metal tube has the larger diameter and leaves the other loose,
which would make the clamp depend on the printed spigot's diameter; each ring closes on a single part. And
loosening the head's ring to turn the head (±90° for a vertical slit, small angles for slit-to-cutoff
parallelism, [§7.5](#75-rotation-mount-and-clearances)) or to swap in the focus target
([§7.7](#77-slit-focus-target-provisional)) leaves the tube clamped. The tube is round, so it is unaffected by
the head's rotation. The two posts share the datum shim and shoe design of every other station, so the tube's
axis and the head's differ only by the posts' tolerance, against the bore's more than 5 mm of radial margin.

The model is the baffle tube and its post stack in `src/schlieren/parts/slit_stage.py`, shown with the head
and the focus fixtures.

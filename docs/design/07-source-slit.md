## 7. Source slit

The source slit is a flexure slit head: one flat-printed ABS part carrying both blades, with fine
centering perpendicular to the slit and fine slit-width adjustment, mounted for continuous rotation about
the optical axis in an SM1RC/M on the common post and rail shoe (§5).

The model is `src/schlieren/parts/slit_head.py` (`uv run slit-head`, with `--show` for the viewer assembly).

The slit needs only about ±2 mm of centering travel, one adjustment axis, and discrete orientations, so it
does not use the cutoff's carriage, plungers, guide rails, keeper frame, datum pins, or cassettes (§8).

**Provisional:** the flexure dimensions are first-print values, and the stage-rotation figures below come
from a first-order flexure model, not FEA; both are to be confirmed on the assembled head (§7.7).

### 7.1 Blades and slit widths

The slit uses two Stanley 11-515 backed single-edge scraper blades.

Measured physical blade dimensions:

- length: 1.535 in / 38.99 mm
- width: 0.768 in / 19.51 mm
- thickness at the sharp/flat portion: 0.010 in / 0.254 mm
- thickness at the folded spine: 0.040 in / 1.016 mm

Expected operating slit widths are 0.10–0.30 mm, starting around 0.15–0.20 mm.

Each blade lies flat on its carrier's blade seat, cutting edge toward the slit and overhanging the carrier
edge by about 1.5 mm. No blade pockets, holes, or spine compensation are used; a slight inclination of the
blade toward its folded spine is acceptable, since the optically important geometry is the gap and
parallelism of the two cutting edges.

### 7.2 Architecture

The head is a three-body monolithic flexure:

1. frame — fixed; carries the spigot adapter, the FAS100 #1 insert, and the spring seat;
2. platform — centering stage on a parallelogram flexure from the frame; carries the datum blade and the
   FAS100 #2 insert;
3. width stage — on a nested parallelogram flexure from the platform; carries the movable blade.

Both parallelograms translate perpendicular to the slit. Their parasitic motion (about δ²/L) lies along
the slit, where it is harmless.

Local frame, at rotation 0: slit horizontal, adjustment axis vertical, both FAS100 knobs up. The blade-seat
plane (the carrier front faces) faces the mirror; every other front face stands back 1 mm so the
overhanging blades cannot rub moving or fixed parts.

Envelope: about 80 × 88 × 13 mm, excluding knobs and adapter.

Stage rotation in the slit plane would skew the slit against the cutoff (centering) or open it in a taper
(width). Under load each flexure blade bends into an S with its inflection at mid-span, so only a force
through the blades' mid-span needs no axial reaction; the layout keeps the varying drive forces from
twisting the stages:

- FAS100 #1 and the preload spring are coaxial and act on the platform's flexure connectors, so their
  forces cancel and only the small centering-flexure force is unbalanced;
- the two centering blades are at the top and bottom of the platform, about 63 mm apart;
- the two width-stage blades are 12 mm apart, and FAS100 #2 pushes on the width-stage connector.

Closely spaced blades or a spring offset from the screw would not achieve this: a compact layout with 5 mm
blade spacing and the spring 23 mm from the screw gives a constant ~1° platform pre-twist and about 8 mrad of
rotation over the centering travel.

### 7.3 Centering stage

- travel: ±2.0 mm about the as-printed position;
- drive: Thorlabs FAS100 1/4"-80 adjuster, 0.3175 mm per turn (10 µm per about 11° of knob), in a McMaster
  98625A950 brass insert in the frame top bar;
- preload: McMaster 2006N292 spring, coaxial with FAS100 #1, 16.5 mm long at mid travel (9 mm compression),
  about 4.4–6.9 N over the travel; located by printed guide pins inside the coil in pockets in the frame
  bottom bar and the lower platform connector;
- flexure: two 0.8 mm ABS blades, 35.5 mm long, 12 mm deep; about 0.38% peak strain at full travel;
- estimated slit rotation: about 0.05 mrad over the full ±2 mm (0.5 µm across a 10 mm lit slit length).

Measured spring OD: 0.272 in / 6.91 mm (calipers). Spring pockets are Ø7.91 mm (1.0 mm diametral
clearance).

Spring installation: the pockets are closed on all sides except the 3.5 mm flexure gap, and the 16.5 mm
cavity is shorter than the 25.5 mm free length, so the spring has no clear insertion path. It is installed by
compressing it fully and working it into the pockets by hand. If that proves unreliable, the fallback is a
bottom access bore through the frame bottom bar closed by a screwed cap carrying the lower guide pin (not
modeled).

Sensitivity: the iris is about 150 mm before the slit, so moving the slit by d turns the illumination cone
by d/150; at the mirror the beam moves about 21 × d. The ±2 mm travel therefore steers the beam about
±42 mm at the mirror, which covers printed-part and shoe tolerances plus deliberate aiming. For a
horizontal slit this is the only vertical aiming adjustment at the source.

### 7.4 Width stage

- drive: a second FAS100 in a 98625A950 insert in the platform top bar; pushing closes the slit;
- preload: the stage's own flexures, printed so that FAS100 #2 always deflects them 0.8–1.6 mm (about
  0.8–1.6 N, comfortably above the stage's own weight in any orientation);
- usable width adjustment: 0.8 mm;
- flexure: two 1.2 mm ABS blades, 45 mm long, 12 mm apart; about 0.29% peak strain;
- estimated taper: about 0.6 µm across a 10 mm lit slit length per 0.1 mm of width change (about 4.6 µm
  over the full 0.8 mm).

Only the movable blade moves, so a width change shifts the slit center by half the change. For a 0.1 mm
change that is 0.05 mm, which moves the beam about 1 mm at the mirror and needs no recentering of the
slit (the cutoff is readjusted for any width change in any case).

Slit setup:

1. with both clamp bars loose, set the width stage to mid travel with FAS100 #2;
2. clamp the datum blade on the platform carrier;
3. set the movable blade against a true-metric feeler gauge between the cutting edges, pressing gently
   along its length, and clamp it progressively;
4. remove the gauge; thereafter set width with FAS100 #2 from that reference (0.15 mm is about half a
   turn). Re-check parallelism with the gauge after large width changes.

### 7.5 Blade clamping

Each blade is pinched against its carrier by an identical removable printed ABS clamp bar (54 × 7 × 4 mm)
faced with McMaster 9852N37 1/32 in EPDM. The bar bears on the flat portion of the blade about 3 mm back
from the cutting edge, leaving the slit cone clear, and is fastened by two M3 × 12 mm socket-head screws
just beyond the blade ends into M3 hex nuts captured in pockets opening from the carrier back. The common
McMaster 91292A114 screw and 91828A211 nut are used; four of each.

### 7.6 Rotation mount and clearances

A separate printed spigot adapter is bolted to the frame back with four M3 × 12 mm socket-head screws,
counterbored from the head front into M3 nuts captured in the adapter back. The adapter is a flat plate,
held 1.0 mm off the moving stages by two McMaster 93475A210 M3 flat washers (0.4–0.6 mm each) stacked on
each screw between frame and plate. It carries a hollow Ø30.48 mm (SM1 tube OD) spigot with a Ø24 mm light
bore, clamped by the SM1RC/M split ring (Ø30.6 mm bore, 10.16 mm thick, M4 locking screw across the split).

A Ø34 mm shoulder on the spigot is the ring's axial stop: the ring seats against it, which places the
adapter plate 3.5 mm in front of the ring face and 2.2 mm clear of the post at every rotation. Do not clamp
the ring away from the shoulder.

The SM1RC/M keeps the 22.1 mm post-top-to-axis dimension (§5.2). Loosening the ring rotates the whole head
about the optical axis:

- rotation 0: horizontal slit, vertical centering, knobs up;
- ±90°: vertical slit, horizontal centering, knobs sideways;
- small rotations: slit-to-cutoff parallelism trim.

Calculated clearances over −110° to +110°: at least 2.2 mm to the post body, 4.0 mm to the rail shoe (at
about ±50°, as the corners pass). The TR50/M M4 stud reaches up into the ring's tapped hole and stops about
1.7 mm short of the spigot at its 5.2 mm drawing maximum; this gap is set by the Thorlabs parts, not by this
design. Beyond about ±125° the adapter corners and knobs reach the shoe.

### 7.7 Fabrication and fit

Printed parts: the flexure head, the spigot adapter, and two clamp bars.

- Head: print back face down, so the blade seats on both carriers are the topmost layer and coplanar
  (ironing recommended); the flexure blades are then vertical walls loaded in the layer plane. Keep
  perimeter seams off the four flexure blades.
- Adapter: print front face down, spigot up; no supports.
- Clamp bars: print flat, EPDM face down.
- The insert bores are pilots, finished by a light hand ream with a 5/16 in twist drill to a press fit
  (§8.3); flanges outboard.
- The spigot is printed at the SM1 tube nominal.

Hardware: 2 × FAS100, 2 × 98625A950 inserts, 2 × N52 10 × 5 × 2 mm magnet bearing pads (one under each
FAS100 ball tip, §8.3), 1 × 2006N292 spring, 8 × M3 × 12 mm socket-head screws, 8 × M3 nuts, 8 × M3 flat
washers.

A test print of the head (Prusa MINI+, ABS) confirmed the insert press fit, the magnet, spring, and other
pockets and bores as sized, and essentially parallel flexure motion along both push axes.

**Provisional,** pending assembly of the complete head:

- spigot fit in the SM1RC/M, and the blade clamp bars;
- width-stage preload holding the stage on its adjuster at the low end of travel;
- no stage contact with the adapter plate;
- blade-edge parallelism versus width setting, and slit rotation versus centering travel, measured against
  the first-order estimates;
- ABS creep of the flexures over days at a fixed setting.

## 6. Light source

The light source is a single assembly on one TR50/M post and common rail shoe (§5): a Thorlabs SMR1/M holder
that carries the condenser and iris on its slit-side face and one of two interchangeable threaded LED modules
on its LED-side face. There is no dedicated LED post, rail shoe, or printed bracket. The condenser images the
LED emitter onto the source slit (§7).

### 6.1 Assembly and stack order

Parts:

- threaded LED module, green or white (§6.3)
- Thorlabs SMR1/M fixed threaded holder
- Thorlabs SM1V05 adjustable lens cell
- Thorlabs ACL2520U-A condenser
- Thorlabs SM1L03 tube
- Thorlabs SM1D12 adjustable iris
- Thorlabs SM1CP1 internally threaded protective cap
- Thorlabs SM1EC2 protective cap
- TR50/M post + common rail shoe

From the LED to the slit:

1. threaded LED module, its SM1CP2M cap threaded into the LED-side face of the SMR1/M;
2. SMR1/M on the TR50/M (0.400 in / 10.16 mm thick, SM1 thread through, no lip; 0.870 in / 22.10 mm
   post-top-to-axis offset);
3. SM1V05, its externally threaded sleeve entering the slit-side face of the SMR1/M and locked with the
   included SM1NT. The ACL2520U-A sits in the SM1V05 body with its plano face on the internal seat (toward
   the LED) and its convex face toward the open end;
4. SM1L03, threaded into the SM1V05 open end;
5. SM1D12, threaded into the SM1L03.

The ACL2520U-A convex vertex sits about 0.7 mm inside the SM1V05 open end, so the SM1L03 spacer is required
ahead of the iris; the SM1D12 interferes with the lens if threaded directly into the SM1V05.

The cap and the SM1V05 sleeve share the SMR1/M thread. The cap threads in until its knurled flange seats on
the SMR1/M face, so the LED position is fixed and the SM1V05 engagement is the focus adjustment (§6.6).
Engagement runs from the Thorlabs minimum of 0.110 in / 2.79 mm to about 5.7–5.8 mm, where the sleeve end
comes within 0.3 mm of the LED board. Turning the SM1V05 moves the lens, SM1L03, and iris together relative to
the LED; the resulting few-millimeter iris shift is negligible against the 150 mm iris-to-slit spacing.

Thorlabs SM1 part dimensions in this stack-up (SMR1/M, SM1CP2M, SM1V05) are the exact inch-primary values from
the vendor STEP models in `cad/vendor/`, not the rounded millimeter values on the drawings. The TR50/M is
metric-primary and keeps its 50 mm / Ø12.7 mm nominals (its STEP model is rounded to inches).
`src/schlieren/parts/led_module.py` encodes the stack-up; `uv run led-module` prints the focus ranges.

### 6.2 Condenser optics

The condenser images the LED emitter onto the source slit (about 6.6× magnification). Each slit point then
sees the iris uniformly filled at the LED radiance, which gives a uniformly illuminated mirror. The LED image
should cover the illuminated slit length; the domes enlarge the apparent emitters by about 1.4–1.5×.

Defocus in either direction underfills the ±1.8° cone: iris-edge rays then trace back beyond the emitter
edge, darkening the mirror edge and shortening the uniformly lit slit length. With the LED at the condenser
focus (12 mm, collimated) the emitter cannot fill the cone even at the slit center.

Using ACL2520U-A catalog values (EFL 20.1 mm, BFL 12.0 mm; object-side principal plane about 8.1 mm inside
the plano face) and about 153 mm from the convex vertex to the slit, the optimum emitter-to-plano-face gap is
about 15 mm. The optimum moves only about ±0.7 mm for ±30 mm of slit position.

### 6.3 LED modules

There are two interchangeable LED modules, each a self-contained threaded assembly. Each LED board mounts on
an identical threaded SM1 carrier so that the SM1 thread and cap flange, rather than the individual MCPCB
pattern, are the interchange standard.

| | Green module | White module |
|---|---|---|
| Emitter | OSRAM OSLON SSL 120, 530 nm nominal | Nichia 519A R9080, 5000 K |
| Board | NewEnergy star board, LST1-01F06-GRN1-00 | Convoy 20 mm star/DTP carrier |
| Initial operating current | approximately 350 mA | approximately 500–700 mA |

Module stack, from the condenser outward:

1. LED star board on the front face of a Thorlabs SM1CP2M externally SM1-threaded end cap (0.210 in /
   5.33 mm solid aluminum, 0.100 in / 2.54 mm thread, Ø1.200 in / 30.48 mm knurled flange);
2. the SM1CP2M itself;
3. Alpha CN40-40B heatsink (§6.4) bolted to the rear face of the cap, with thermal compound between.

Interfaces:

- The cap flange is the repeatable axial stop on the SMR1/M face; the module's rotational position at the
  stop does not matter.
- The SM1 thread centers the emitter on the condenser axis; no vertical calibration is required.
- Heatsink fastening: socket-head screws through the CN40 base in the open cells between pins, into blind
  M3 holes tapped about 2.5 mm deep in the cap rear face, with M3 × 6 mm screws (**provisional** length). Keep
  the rear holes angularly offset from the front M2 board holes (§6.5), since the cap is only 5.33 mm thick.
- Leads drop past the board edge through the board's edge slots, through a pair of holes drilled at about
  r = 11 mm through the cap (inside the thread root) and the heatsink base, and out between the pins.
- Fabrication is drilling and tapping of purchased aluminum parts only.

Clearances:

- The heatsink's lowest point is 2.1 mm above the TR50/M post top at any rotation (22.10 mm axis offset minus
  20 mm maximum radius).
- The heatsink front face is 2.79 mm (0.110 in) behind the SMR1/M face (the cap flange thickness).
- The SMR1/M thread bore leaves about 3 mm of radial room around a 20 mm board for leads.

### 6.4 Common heatsink

- Alpha CN40-40B natural-convection pin-fin heatsink, one per module
- Ø40.0 mm (+0/−0.5) × 40 mm overall, 3.0 mm flat base, Ø2.8 mm pins on a 6.9 mm square grid
- 6063 aluminum, black anodized; 24.6 g
- manufacturer natural-convection rating 6.9 °C/W

At about 2 W (white module at 700 mA) the expected rise is roughly 14 °C above ambient; the green module
dissipates about 1.1 W. The rating is the manufacturer's pins-up test; the module runs with pins horizontal,
which pin fins tolerate well. **Provisional:** bench-test the temperature rise at 700 mA before relying on
it.

The heatsink is round so that it clears the post at every rotation while the module is threaded in (§6.3); a
larger or non-round heatsink would sweep its corners below the post top during threading.

### 6.5 LED board mounting

Measured star-board thicknesses (calipers):

- green NewEnergy star: 0.0625 in / 1.59 mm (the datasheet lists 0.047 or 0.067 in; the measured value governs)
- white Convoy 20 mm star: 0.0590 in / 1.50 mm

Both boards are about 20 mm across (NewEnergy 0.783 in / 19.9 mm, catalog).

Fastening standard:

- M2 × 0.4
- McMaster 92095A452, M2 × 5 mm screws
- tapped directly into the front (threaded) face of the SM1CP2M cap
- 1.6 mm tap drill
- M2 × 0.4 HSS tap

Use the cap's center-drill mark as the layout datum for the board hole pattern. Transfer each carrier board's
hole geometry from the physical board rather than assuming it from the other module. Slightly oversized board
holes permit final centering of the emitter on the cap axis: a 0.3 mm emitter offset moves the slit image
about 2 mm, so center each board by watching its image on the slit blades before final tightening.

Add thin insulating washers beneath screw heads where necessary to keep the metal screw heads away from
exposed board contacts:

- McMaster 91545A410
- M2 lubricant-filled nylon flat washer

A thin layer of thermal compound is used between board and cap.

### 6.6 Focus and module interchange

Setup values (not hard CAD dimensions):

- emitter-to-plano-face gap approximately 15 mm, measured to the emitting surface, not the dome top
- useful gap range roughly 13–17 mm
- condenser/iris-to-slit spacing approximately 150 mm
- initial iris opening approximately 9–10.5 mm (about ±1.7–2.0° at 150 mm)

Set focus by imaging the LED onto the closed slit blades and turning the SM1V05 until the emitter image is
sharp and centered, then lock the SM1NT and open the slit.

Calculated emitter heights above the cap face, using the measured board thicknesses, about 0.07 mm of solder,
and the apparent emitter heights through the LED domes (calculated from the manufacturer outline drawings:
OSLON about 0.45 mm, 519A about 0.75 mm), with the gap range each module reaches over the SM1V05 engagement
range:

| Module | Emitter height above cap face | Emitter-to-plano gap range | SM1V05 engagement at 15 mm gap |
|---|---|---|---|
| Green | about 2.1 mm | about 13.2–16.2 mm | about 3.9 mm |
| White | about 2.3 mm | about 12.9–16.0 mm | about 3.7 mm |

The two modules focus about 0.2 mm apart in engagement, about one-third of a turn of the SM1 thread. An
index mark per module on the SM1V05 is optional.

Focus margin about the 15.04 mm optimum gap is about 1.1 mm (long-gap side) and 1.8 mm (short-gap side) for
the green module, and only about 0.93 mm and 2.1 mm for the white module. The white module's long-gap travel
is limited by the SM1V05 minimum engagement. **Provisional:** the white module's reduced margin is to be
confirmed on the build. If it cannot reach a sharp slit image, space its cap flange off the SMR1/M face with
a thin shim (about 0.1 mm restores 1.0 mm of margin). The shim moves the whole module away from the lens and
keeps the flange as the axial stop; a shim under the star board would instead shorten the gap and make the
shortfall worse.

Module interchange:

1. disconnect the Micro-Fit lead;
2. unscrew the module (cap and heatsink together) from the SMR1/M, about four turns;
3. screw in the alternate module until its flange seats;
4. touch up focus on the closed slit blades if needed.

### 6.7 Power and wiring

Power supply:

- ALIENTEK DP100
- use DC constant-current operation rather than PWM to avoid rolling-shutter banding

Connector standard:

- Micro-Fit 3.0
- 2-pin
- 18 AWG factory pigtails

Connector hardware:

- 2 × Molex 214758-1021, male-to-pigtail, 150 mm — module side
- 1 × Molex 214756-1023, female-to-pigtail, 600 mm — supply side
- 1 × Pomona 1825-02 red/black 4 mm banana-plug pair

The supply side should present recessed/socket contacts.

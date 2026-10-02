## 6. LED source assemblies

There are two interchangeable LED source modules. Each LED board mounts on an identical threaded SM1 carrier
(§6.5) so that the SM1 thread and cap flange, rather than the individual MCPCB pattern, are the interchange
standard.

### 6.1 Green module

- OSRAM OSLON SSL 120 / NewEnergy star board
- exact part: LST1-01F06-GRN1-00
- nominal wavelength: 530 nm
- initial operating current approximately 350 mA

### 6.2 White module

- Nichia 519A R9080
- 5000 K
- Convoy 20 mm star/DTP carrier
- initial current approximately 500–700 mA

Transfer each carrier board's hole geometry from the physical board rather than assuming it from the other
module.

### 6.3 Common heatsink

- Alpha CN40-40B natural-convection pin-fin heatsink, one per module
- Ø40.0 mm (+0/−0.5) × 40 mm overall, 3.0 mm flat base, Ø2.8 mm pins on a 6.9 mm square grid
- 6063 aluminum, black anodized; 24.6 g
- manufacturer natural-convection rating 6.9 °C/W

At about 2 W (white module at 700 mA) the expected rise is roughly 14 °C above ambient; the green module
dissipates about 1.1 W. The rating is the manufacturer's pins-up test; the module runs with pins horizontal,
which pin fins tolerate well. **Provisional:** bench-test the temperature rise at 700 mA before relying on
it.

The heatsink is round so that it clears the condenser post at every rotation while the module is threaded in
(see §6.5); a larger or non-round heatsink would sweep its corners below the post top during threading.

### 6.4 LED board mounting

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

Use the cap's center-drill mark as the layout datum for the board hole pattern. Slightly oversized board
holes permit final centering of the emitter on the cap axis: a 0.3 mm emitter offset moves the slit image
about 2 mm, so center each board by watching its image on the slit blades before final tightening.

Add thin insulating washers beneath screw heads where necessary to keep the metal screw heads away from
exposed board contacts:

- McMaster 91545A410
- M2 lubricant-filled nylon flat washer

A thin layer of thermal compound is used between board and cap.

### 6.5 Threaded LED module

Each LED module is a self-contained threaded assembly that screws into the LED-side face of the condenser
SMR1/M (§7). There is no dedicated LED post, rail shoe, or printed bracket.

Module stack, from the condenser outward:

1. LED star board on the front face of a Thorlabs SM1CP2M externally SM1-threaded end cap (0.210 in /
   5.33 mm solid aluminum, 0.100 in / 2.54 mm thread, Ø1.200 in / 30.48 mm knurled flange);
2. the SM1CP2M itself;
3. Alpha CN40-40B heatsink bolted to the rear face of the cap, with thermal compound between.

Interfaces:

- The cap threads into the SMR1/M until its knurled flange seats on the SMR1/M face. The flange is the
  repeatable axial stop; the module's rotational position at the stop does not matter.
- The SM1 thread centers the emitter on the condenser axis; no vertical calibration is required.
- Heatsink fastening: socket-head screws through the CN40 base in the open cells between pins, into blind
  M3 holes tapped about 2.5 mm deep in the cap rear face, with M3 × 6 mm screws (**provisional** length). Keep
  the rear holes
  angularly offset from the front M2 board holes, since the cap is only 5.33 mm thick.
- Leads drop past the board edge through the board's edge slots, through a pair of holes drilled at about
  r = 11 mm through the cap (inside the thread root) and the heatsink base, and out between the pins.
- Fabrication is drilling and tapping of purchased aluminum parts only.

Clearances:

- The heatsink's lowest point is 2.1 mm above the TR50/M post top at any rotation (0.870 in / 22.10 mm axis
  offset minus 20 mm maximum radius).
- The heatsink front face is 2.79 mm (0.110 in) behind the SMR1/M face (the cap flange thickness).
- The SMR1/M thread bore leaves about 3 mm of radial room around a 20 mm board for leads.

Focus is set with the SM1V05 (§7). Calculated emitter heights above the cap face, using the measured board
thicknesses, about 0.07 mm of solder, and the apparent emitter heights through the LED domes (calculated
from the manufacturer outline drawings: OSLON about 0.45 mm, 519A about 0.75 mm):

| Module | Emitter height above cap face | Emitter-to-plano gap range | SM1V05 engagement at 15 mm gap |
|---|---|---|---|
| Green | about 2.1 mm | about 13.2–16.2 mm | about 3.9 mm |
| White | about 2.3 mm | about 12.9–16.0 mm | about 3.7 mm |

The two modules focus about 0.2 mm apart in engagement, about one-third of a turn of the SM1 thread. An
index mark per module on the SM1V05 is optional.

Focus margin about the 15.04 mm optimum gap is about 1.1 mm (long-gap side) and 1.8 mm (short-gap side) for
the green module, and only about 0.93 mm and 2.1 mm for the white module. The white module's long-gap travel
is limited by the SM1V05 minimum engagement. **Provisional:** the white module's reduced margin is to be
confirmed on the build. If it cannot reach a sharp slit image, space its cap flange off the SMR1/M face with a thin shim (about
0.1 mm restores 1.0 mm of margin). The shim moves the whole module away from the lens and keeps the flange as
the axial stop; a shim under the star board would instead shorten the gap and make the shortfall worse.

Thorlabs SM1 part dimensions in this stack-up (SMR1/M, SM1CP2M, SM1V05) are the exact inch-primary values from
the vendor STEP models in `cad/vendor/`, not the rounded millimeter values on the drawings. The TR50/M is
metric-primary and keeps its 50 mm / Ø12.7 mm nominals (its STEP model is rounded to inches).

Module interchange:

1. disconnect the Micro-Fit lead;
2. unscrew the module (cap and heatsink together) from the SMR1/M, about four turns;
3. screw in the alternate module until its flange seats;
4. touch up focus on the closed slit blades if needed.

`src/schlieren/parts/led_module.py` encodes this stack-up; `uv run led-module` prints the focus ranges.

### 6.6 Power and wiring

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

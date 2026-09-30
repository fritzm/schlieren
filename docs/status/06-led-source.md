## 6. LED source assemblies

Two interchangeable source types are planned. Each LED board mounts to an identical external-format passive
aluminum heatsink so that the heatsink/module envelope, rather than the individual MCPCB pattern, is the
interchange standard.

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

Actual carrier-board hole geometry should be transferred from the physical board rather than assumed from the
green module.

### 6.3 Common heatsink

- octagonal radial-fin aluminum heatsink
- approximately 55 mm across flats × 20 mm deep

The LED is centered on the heatsink. The fixture therefore keeps the post axis, heatsink center, and LED
emitter nominally coaxial.

### 6.4 LED board mounting

Fastening standard:

- M2 × 0.4
- McMaster 92095A452, M2 × 5 mm screws
- tapped directly into the aluminum heatsink
- 1.6 mm tap drill
- M2 × 0.4 HSS tap

Add thin insulating washers beneath screw heads where necessary to keep the metal screw heads away from
exposed board contacts:

- McMaster 91545A410
- M2 lubricant-filled nylon flat washer

A thin layer of thermal compound is used between board and heatsink.

### 6.5 LED module fixture — selected architecture; final dimensions pending measurement

Each LED module receives its own printed ABS support bracket on the dedicated fourth TR50/M. The LED-support
post is behind the heatsink relative to the optical path, and the bracket reaches forward from the post to the
heatsink. This keeps the post and bracket body out of the LED-to-condenser gap so the LED/heatsink can be
scooted forward as close to the condenser as optical and mechanical clearances permit.

#### Post-top interface

- Use the threaded M4 fixture at the top of the TR50/M as the module-bracket attachment.
- The flat top surface of the TR50/M is the axial/vertical seating datum for the bracket.
- The bracket has a flat mounting tab that seats directly on the post top and is retained at the M4 post-top
  thread.
- There is no printed post-top socket and no split clamp around the LED post.
- Loosening the M4 attachment permits small yaw adjustment by rotating the bracket about the post axis before
  retightening.
- Coarse fore/aft adjustment is provided by sliding the LED rail shoe along the source rail; the post remains
  behind the heatsink.

#### Heatsink support and calibration

Two forward-reaching guide/gripping fingers engage two opposing parallel vertical flats of the octagonal
heatsink.

The finger system shall:

- constrain lateral position;
- constrain heatsink roll/rotation;
- permit a small vertical sliding calibration range;
- provide repeatable axial/pitch seating of the heatsink in its module bracket.

Target vertical calibration range remains approximately ±2–3 mm. Each LED module is calibrated by sliding its
heatsink vertically until its LED emitter lies on the optical axis. The final finger/clamp details and the
exact axial datum geometry are to be set from the physical heatsink/LED measurements. Small localized Loctite
4061 CA tack drops remain permissible after calibration if useful; do not wick CA along the full finger
length.

#### Module interchange

Each LED/heatsink remains attached to and calibrated with its own bracket. Routine interchange is intended to
require only:

1. disconnect the Micro-Fit lead;
2. remove the single post-top M4 retaining fastener;
3. lift off the complete LED/heatsink/bracket module;
4. seat the alternate module on the TR50/M post-top datum and retighten.

The rail shoe and TR50/M remain installed. Fore/aft position is therefore preserved by the rail shoe, while
the flat post-top datum establishes bracket height and seating. Yaw can be trimmed at the M4 post-top
attachment if needed.

This architecture supersedes the prior blind post-top socket and LED-fixture split-clamp concept. The
architecture is selected; final CAD dimensions are pending the physical heatsink/LED clearance measurements.

### 6.6 Power and wiring

Power supply:

- ALIENTEK DP100
- use DC constant-current operation rather than PWM to avoid rolling-shutter banding

Connector standard:

- Micro-Fit 3.0
- 2-pin
- 18 AWG factory pigtails

Selected connector hardware:

- 2 × Molex 214758-1021, male-to-pigtail, 150 mm — module side
- 1 × Molex 214756-1023, female-to-pigtail, 600 mm — supply side
- 1 × Pomona 1825-02 red/black 4 mm banana-plug pair

The supply side should present recessed/socket contacts.

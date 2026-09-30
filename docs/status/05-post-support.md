## 5. Common rail-mounted post support

Four fixtures use the common post/shoe architecture:

1. LED source;
2. condenser/iris;
3. source-slit carriage;
4. cutoff carriage.

### 5.1 Post

- Thorlabs TR50/M
- 12.7 mm diameter
- 50 mm long
- quantity: 4, one at each common post/shoe station

### 5.2 Optical-holder allocation

- condenser: 1 × SMR1/M
- slit carriage: 1 × SM1RC/M
- cutoff carriage: 1 × SM1RC/M
- LED source: dedicated fourth TR50/M; module bracket seats on the flat post-top datum and attaches at the
  threaded M4 post top

The condenser/slit/cutoff holders preserve the 22.1 mm post-top-to-axis dimension.

### 5.3 Common rail shoe — CAD ready

The common shoe is a printed ABS U-shaped saddle that:

- straddles the 2020 extrusion;
- locks through the rail side channels;
- leaves the rail top available as the datum surface;
- carries a vertical 12.7 mm through-bore for the TR50/M post.

The post passes through the printed shoe and bottoms on a McMaster 2895T62 0.010 in stainless datum disc
resting on the rail top. The printed ABS does not establish the precision optical height.

The post bore incorporates a single-split clamping collar so that the post can be locked against rotational
movement while remaining fully seated on the metal datum.

Baseline split-collar geometry:

- one axial split;
- one transverse clamp screw;
- sufficient axial engagement to resist rocking and rotation;
- rounded stress-relief termination at the bottom of the split;
- generous fillets where the collar merges into the shoe body;
- free-fitting 12.7 mm post bore before clamping.

Common split-clamp hardware for each of the four rail-shoe post collars is:

M3 socket-head screw → clearance through one ear → captured M3 hex nut in the opposite ear.

The common hardware selection for all eight printed split clamps is:

- McMaster 91292A114 — M3 × 0.5 × 12 mm fully threaded 18-8 stainless socket-head screw; 5.5 mm head diameter,
  3 mm head height, 2.5 mm hex drive; one 100-pack supplies the eight installed split-clamp screws plus
  validation and shared-use stock;
- McMaster 91828A211 — full-height M3 × 0.5 18-8 stainless hex nut; 5.5 mm across flats × 2.4 mm high, DIN
  934; the shared 100-pack supplies eight split-clamp nuts, eight keeper-frame nuts
  ([§8.4](08-carriages-cassettes.md#84-cassette-seating)), and twelve cassette clamp-bar nuts
  ([§9](09-slit-cassette.md#9-source-slit-cassette)), leaving 72 for validation and spares;
- no washer, nyloc, or threaded insert.

The 12 mm screw length is finalized for the common printed split-clamp standard. Design the ear thickness and
approximately 1–2 mm relaxed split gap around this stock length. If a later physical build demonstrates that
this length cannot be made workable, revise the plan at that time rather than carrying an alternate length in
the baseline. The captured full-height nut and the overall screw/nut architecture are common to all printed
split clamps listed below.

The clamp provides rotational and lateral retention; post height is still established solely by the post
bottoming on the metal datum disc.

This split-collar geometry remains the common baseline for the rail-shoe and carriage split clamps. The LED
module fixture no longer uses a post collar; it attaches at the TR50/M threaded M4 post top as described in
[§6.5](06-led-source.md#65-led-module-fixture--selected-architecture-final-dimensions-pending-measurement).

The shoe should use the measured rail geometry and M5 20-series slot-6 T-nut hardware.

This design cluster is sufficiently defined to begin detailed CAD.

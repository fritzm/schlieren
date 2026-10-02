## 5. Common rail-mounted post support

Three fixtures use the common post/shoe architecture:

1. condenser/iris, which also carries the threaded LED module (§6.5);
2. source-slit flexure head (§9);
3. cutoff carriage.

### 5.1 Post

- Thorlabs TR50/M
- 12.7 mm diameter
- 50 mm long
- quantity: 3, one at each common post/shoe station

### 5.2 Optical-holder allocation

- condenser: 1 × SMR1/M
- slit head: 1 × SM1RC/M, clamping the printed spigot of the slit-head adapter (§9.6)
- cutoff carriage: 1 × SM1RC/M, clamping the printed spigot of the carriage base plate (§8.1)
- LED source: no post of its own; the threaded LED module screws into the condenser SMR1/M

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

Common split-clamp hardware for each of the three rail-shoe post collars is:

M3 socket-head screw → clearance through one ear → captured M3 hex nut in the opposite ear.

The common hardware selection for the three printed rail-shoe split clamps is:

- McMaster 91292A114 — M3 × 0.5 × 12 mm fully threaded 18-8 stainless socket-head screw; 5.5 mm head diameter,
  3 mm head height, 2.5 mm hex drive; one 100-pack supplies the three installed split-clamp screws, eight
  keeper-frame screws, and eight slit-head screws ([§9](09-slit-cassette.md#9-source-slit)), plus validation
  and shared-use stock;
- McMaster 91828A211 — full-height M3 × 0.5 18-8 stainless hex nut; 5.5 mm across flats × 2.4 mm high, DIN
  934; the shared 100-pack supplies three split-clamp nuts, eight keeper-frame nuts
  ([§8.4](08-carriages-cassettes.md#84-cassette-seating)), twelve cassette clamp-bar nuts
  ([§9.8](09-slit-cassette.md#98-common-cassette-clamp-bars-cutoff-cassettes)), and eight slit-head nuts
  ([§9](09-slit-cassette.md#9-source-slit)), leaving 69 for validation and spares;
- no washer, nyloc, or threaded insert.

The 12 mm screw length is finalized for the common printed split-clamp standard. Design the ear thickness and
approximately 1–2 mm relaxed split gap around this stock length. If a later physical build demonstrates that
this length cannot be made workable, revise the plan at that time rather than carrying an alternate length in
the baseline. The captured full-height nut and the overall screw/nut architecture are common to all printed
split clamps listed below.

The clamp provides rotational and lateral retention; post height is still established solely by the post
bottoming on the metal datum disc.

This split-collar geometry remains the common baseline for the rail-shoe split clamps. The LED
module has no post of its own; it threads into the condenser SMR1/M as described in
[§6.5](06-led-source.md#65-threaded-led-module--committed).

The shoe should use the measured rail geometry and M5 20-series slot-6 T-nut hardware.

This design cluster is sufficiently defined to begin detailed CAD.

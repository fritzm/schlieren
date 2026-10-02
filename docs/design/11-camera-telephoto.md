## 11. Camera and telephoto support

The camera and lens are chosen (§11.1–11.2). **Provisional:** the phone cradle and telephoto saddle
(§11.3–11.5) are defined by requirements and a concept but not yet designed in detail; this is the main
remaining custom mechanical design work (§13).

### 11.1 Camera

- Apple iPhone 17, base model, in intended protective case
- measured camera optical axis approximately 60.6 mm above the lower long edge
- use Blackmagic Camera with manual/fixed focus, exposure, and white balance
- focus on the test region near the mirror, not on the cutoff

Initial recording modes:

- 4K/30 for normal work;
- 4K/60 for faster flow phenomena;
- SDR / HDR off as a stable starting point.

### 11.2 Telephoto

- iOgrapher proSnap 7×
- 17 mm mount
- approximately 37.0 mm diameter
- approximately 116.8 mm long

The lens barrel, rather than the phone shell, is the preferred transverse optical datum because accurate lens
centering minimizes vignetting.

### 11.3 Phone-cradle concept

The cradle is a side-mounted rail fixture that leaves the rail top unobstructed.

A floating phone cradle is supported by two vertical jacks:

- common-mode motion adjusts overall camera height;
- differential motion adjusts roll;
- gravity supplies preload;
- target height-adjustment range at least approximately ±3 mm;
- approximately 7–8 mm total mechanical travel is a useful target.

Loose guides may constrain unwanted fore/aft motion but must not bind as the cradle height and roll change.

With the measured 60.6 mm camera-axis offset, a lower phone-edge elevation of approximately 11.7–12 mm above
rail top places the camera near the 72.35 mm common optical datum. This is a setup target rather than a
fabrication-critical dimension because the cradle deliberately provides adjustment.

### 11.4 Telephoto-saddle concept

The telephoto lens uses a separate rail-mounted support.

The saddle should:

- center the lens barrel over the imaging rail;
- use a symmetric shallow V or concave padded seat;
- support the rear/middle portion of the barrel;
- leave the forward end clear near the cutoff carriage;
- avoid placing the telephoto's weight primarily through the phone.

A single vertical jack provides fine height/pitch adjustment. Use approximately the same useful adjustment
envelope as the phone cradle: about ±3 mm, with roughly 7–8 mm total mechanical travel available. Center the
jack over the imaging rail. The 25 mm jack can be packaged without using the rail-slot depth under the
nominal height stack; the central top slot remains available as clearance margin.

Provisional saddle vertical stack at nominal optical height:

- telephoto barrel diameter approximately 37.0 mm, placing the barrel bottom approximately 53.85 mm above rail
  top when centered on the 72.35 mm optical datum;
- approximately 0.8 mm / 1/32 in EPDM padding on the saddle contact surface;
- approximately 5 mm ABS saddle floor as the initial CAD target;
- nominal saddle underside / jack-contact elevation therefore approximately 48 mm above rail top.

The saddle is intentionally a gravity-loaded floating part, not rigidly attached to the lower jack fixture.
The lens/phone connection supplies the principal fore/aft relationship, while the saddle supports the
rear/middle portion of the barrel. Avoid rigid vertical guide rails unless physical testing shows they are
necessary, because the rear saddle must tolerate the small angular and longitudinal motion that accompanies
lens pitch adjustment about the phone end.

The jack contact uses the same nickel-plated rectangular magnet standard as the carriage plungers: Amazon
B0DMCY4FN1, 10 × 5 × 2 mm N52. For the saddle:

- load the magnet into a close-fitting pocket from the top of the printed saddle;
- fully support the magnet around its perimeter and cover its upper face with the EPDM padding;
- expose only the central portion of the lower plated face through a jack-access opening;
- use the surrounding ABS geometry to retain the magnet laterally and prevent it from dropping through.

The lower access feature should also provide loose lateral localization of the saddle on the ball-tip jack.
Use a shallow funnel/chamfer or short loose socket around the approximately 3 mm jack ball rather than a tight
cylindrical guide. A CAD starting point is an approximately 3.6–4.0 mm minimum guide opening, with roughly
1.5–2.0 mm effective guiding depth below the magnet and a generous chamfer/funnel opening toward the jack. The
ball should normally bear directly on the flat magnet; surrounding ABS should engage only after small lateral
displacement. This preserves angular freedom while limiting saddle wander. Gravity and lens weight provide
normal preload; magnetic attraction, if present, is only a secondary benefit and is not relied upon for
retention.

A loose retaining strap may be used if necessary, but the lens should not be aggressively clamped.

### 11.5 Jack hardware

There are three vertical jacks:

- two under the phone cradle;
- one under the telephoto saddle.

Hardware:

- McMaster 93339A252, M5 × 0.8 × 25 mm ball-tip set screws
- McMaster 94459A797, M5 heat-set inserts
- McMaster 92815A202, M5 thumb nuts used as threadlocked mid-screw handwheels
- Loctite 271, McMaster 91458A160
- heat-set installation tip 92160A327;
- Amazon B0DMCY4FN1, N52 Bar Magnet - 10 mm L × 5 mm W × 2 mm H, as hard plated jack-contact bearing
  inserts, one at each jack.

## 9. Camera and telephoto support

The camera and lens are chosen ([§9.1](#91-camera)–[9.2](#92-telephoto)). **Provisional:** their support, a
lens pointer and a phone rest ([§9.4](#94-support-concept)–[9.7](#97-adjuster-hardware)), is a baseline
concept with a mock-up model, still under refinement and not yet designed in detail; this is the main remaining
custom mechanical design work ([§11](11-open-work.md#11-provisional-areas-and-next-steps)).

### 9.1 Camera

- Apple iPhone 17, base model, in intended protective case
- held in landscape, with the rear cameras toward the mirror and the camera end of the phone toward the
  optical axis
- the Main camera is used, at 1× (or its 2× crop). It is the lower of the two rear apertures with the phone
  in portrait, "rear camera 2" on Apple's drawing (`docs/reference/Apple-iPhone-17.pdf`); the upper aperture
  is the Ultra Wide, used only at 0.5×
- measured camera optical axis approximately 60.6 mm above the lower long edge, in the case
- measured Main camera axis approximately 1.350 in / 34.3 mm from the near short edge, in the case; the case
  shape makes this hard to measure accurately with calipers

Manufacturer dimensions of the bare phone, from the drawing:

- both rear cameras are 13.62 mm from the nearer long edge, on a line parallel to it, so the measured axis
  height applies to either aperture
- the Main camera is 31.34 mm from the top short edge, 17.72 mm beyond the Ultra Wide at 13.62 mm
- body 149.61 × 71.45 × 7.95 mm; the camera glass stands 3.45 mm above the back glass

The drawing and the two measurements agree. The cameras are 57.83 mm from the farther long edge of the bare
phone, so the measured 60.6 mm implies a case wall of about 2.8 mm at that edge; the 31.34 mm and the measured
34.3 mm imply about 3.0 mm at the short edge (both calculated).

Initial recording modes:

- 4K/30 for normal work;
- 4K/60 for faster flow phenomena;
- SDR / HDR off as a stable starting point.

### 9.2 Telephoto

- iOgrapher proSnap 7×
- 17 mm mount
- approximately 37.0 mm diameter
- approximately 116.8 mm long
- measured mass approximately 215 g

Measured barrel sections, from the aft end forward:

| Section                 | Length              | Outside diameter    |
|-------------------------|---------------------|---------------------|
| aft end                 | 0.565 in / 14.4 mm  | not measured        |
| rear cylindrical barrel | 1.300 in / 33.0 mm  | 1.457 in / 37.01 mm |
| long cylindrical barrel | 2.25 in / 57.2 mm   | 1.459 in / 37.06 mm |
| focus ring              | 0.455 in / 11.6 mm  | not measured        |
| front lip               | 0.175 in / 4.4 mm   | not measured        |

Both cylindrical sections are suitable for clamping, giving about 90 mm of clampable barrel from 14.4 mm to
104.5 mm from the aft end. The focus ring must stay clear. The measured sections sum to 4.745 in / 120.5 mm,
about 3.7 mm more than the overall length listed above; the difference is not resolved.

The lens barrel, rather than the phone shell, is the preferred transverse optical datum because accurate lens
centering minimizes vignetting.

### 9.3 Alignment requirements

The returned slit image at the cutoff is the aperture stop for the camera: every ray from the test region
passes through it, then spreads again at the ±1.82° cone angle ([§3.2](01-context-and-layout.md#32-source-cone)).
The values below are calculated, and are **provisional** where they rest on assumed values: a lens front about
42 mm behind the cutoff plane, a 10 mm lit slit image, a Main-camera pupil of about 3.7 mm (6 mm focal length
at f/1.6), and a telephoto clear aperture near 30 mm.

| Quantity                                        | Value                    |
|-------------------------------------------------|--------------------------|
| Beam cone at the lens front                     | about 2.7 mm diameter    |
| Beam footprint at the lens front                | about 2.7 × 12.7 mm      |
| Slit image at the phone, reduced 7× by the lens | about 1.4 mm long        |
| Frame at 1×, 4K 16:9, through the lens          | about 9.9° × 6.1°        |
| Mirror in the frame                             | 3.6° of the 6.1° height  |

The resulting tolerances on the camera and lens as one body:

- centering on the beam: about ±8 mm along the slit direction and ±13 mm across it, before the reduced slit
  image leaves the phone pupil; the lens front aperture allows a similar margin;
- pitch: about ±1.2°, the spare frame height either side of the mirror;
- yaw: about ±3°.

Pointing is therefore the governing adjustment, and centering is forgiving. Image quality still favors
centering well inside the vignetting limit.

### 9.4 Support concept

The phone and the lens threaded onto its case are one rigid body. The lens barrel is its datum
([§9.2](#92-telephoto)): the lens is held at two stations along its barrel, and the phone hangs from its lens
mount. Two separate rail fixtures carry them:

- the lens pointer, specific to the lens, holds the barrel at both stations on four adjusting screws
  ([§9.5](#95-lens-pointer));
- the phone rest, specific to the phone, supports the phone's lower edge at one point
  ([§9.6](#96-phone-rest)). A different phone needs only this part redesigned.

<p align="center">
  <img src="figures/camera-support.png" width="500" style="max-width: 90%"
       alt="Lens pointer and phone rest on the imaging rail: two collars on the lens barrel, each on a pair of inclined screws in a yoke of the pointer shoe, and the phone hanging from the lens with its lower edge on the rest arm">
  <br>
  <em>Fig. 5. Lens pointer and phone rest on the imaging rail, concept mock-up, with phone and lens envelopes</em>
</p>

The body is located by six contacts and no more, so adjusting one station does not strain the lens mount:

- four screw tips, two at each station, fix the lens axis in x and z at both stations, and so its position,
  pitch, and yaw;
- one of those tips sits in a groove, fixing the lens fore/aft;
- the phone rest fixes roll.

Each station's pair of screws places one point of the lens axis, so the two stations give position and
pointing without coupling between them beyond the lever ratio. Holding the lens, not the phone, takes the
lens weight off the lens mount: the mount carries about 1 N in shear (calculated), against roughly 130–150 N·mm
of bending if the lens were cantilevered from the phone.

The mock-up model is `src/schlieren/parts/camera_support.py`. It places the parts and checks their
contacts and clearances with plain envelopes; fits, pockets, inserts, and print orientation are not designed.

### 9.5 Lens pointer

Two identical printed split collars clamp the barrel with the common M3 split-clamp hardware
([§5.3](05-post-support.md#53-common-rail-shoe)):

- the aft collar on the rear cylindrical section, centered about 24 mm from the lens aft end, which leaves
  finger room for its thumb nuts ahead of the phone;
- the fore collar on the long cylindrical section, centered about 96.5 mm from the aft end, with its front
  face about 2 mm behind the focus ring;
- about 72.5 mm between them.

Each collar rests on two ball-tip screws ([§9.7](#97-adjuster-hardware)) at 45° either side of straight down,
their axes meeting on the lens axis. The two yokes that hold the screws are one printed shoe straddling the
rail and clamped through its side slots, so the camera slides along the rail as a unit. The collars are
gravity-seated on the screws.

Each screw tip bears on a flat pad on the underside of its collar:

- three pads are the 10 × 5 × 2 mm magnets, set with the 10 mm side across the rail;
- the fourth, at the aft left screw, is a groove between two short pieces of rod stock lying across the rail.
  The ball sits between them, free to slide across the rail but not along it.

The two screws of a station are at right angles, so advancing one slides the collar across the other's pad by
the same distance. Pad size, not screw travel, limits the adjustment. Calculated, keeping each ball 1 mm
inside the pad edges:

| Adjustment                           | Range                       |
|--------------------------------------|-----------------------------|
| Each screw                           | about ±3 mm                 |
| A station, in x or in z alone        | about ±4 mm                 |
| Lens tilt, pitch or yaw              | about ±2°                   |
| One turn of both screws of a station | about 1.1 mm, or about 0.9° |

The tilt limit comes from the 5 mm side of the pads, on the pads that slide along the rail as the lens yaws
about the groove. These ranges cover the alignment tolerances ([§9.3](#93-alignment-requirements)) and the
expected build errors.

Contact loads, calculated from the measured 215 g lens with an assumed balance point 60–70 mm from the aft end
and an assumed cased phone mass of 177–210 g:

- aft screw pair: about 2.2–2.7 N;
- fore screw pair: about 0.6–0.9 N. The phone hangs behind the aft collar, so its weight pivots the lens
  about the aft screws and unloads the fore pair.

A hold-down of about 5 N at each collar, an elastic loop or light spring, is therefore required, the fore one
most of all: without it a light touch, such as working the focus ring, unseats the fore collar. The alloy-steel
screw tips are attracted to the magnet pads, which adds some preload; it is not relied upon until measured.

**Provisional:** the collar stations, pad arrangement and size, hold-down, and the pointer shoe are concept
level. Larger pads would restore the full screw travel.

### 9.6 Phone rest

The phone hangs from the lens with its body to the outboard side of the optical axis
([§3.4](01-context-and-layout.md#34-common-optical-axis-datum)). Its weight, centered about 43 mm from the
lens axis, would turn the lens in its collars. The phone rest stops that: the phone's lower long edge sits on
one piece of rod stock lying along the rail, about 100 mm outboard of the axis, on the arm of a short printed
shoe of its own.

- With the measured 60.6 mm camera-axis height, the phone's lower edge is about 11.75 mm above the rail top.
- The rest carries about 0.8–0.9 N (calculated, same assumptions as [§9.5](#95-lens-pointer)).
- The rest is fixed. Raising or lowering the aft collar rolls the phone slightly about the lens axis, which
  does not matter; the phone is not gripped and slides on the rod.
- The rest holds no optical alignment, so its dimensions are not critical.
- Because the rod lies along the rail, the rest needs to be only roughly under the phone.

**Provisional:** the rest geometry, a light retainer to keep the phone on the rod, and a loose safety catch
against a knock are not yet designed.

### 9.7 Adjuster hardware

There are four adjusting screws, two under each collar. Each is a ball-tip set screw in a heat-set insert in
its yoke, with a thumb nut threadlocked mid-screw as a handwheel.

Hardware:

- McMaster 93339A252, M5 × 0.8 × 25 mm ball-tip set screws: alloy steel, 25.0 mm overall including the ball,
  2.5 mm hex socket, and a 3.0 mm ball (ball size from the vendor model, `cad/vendor/McMaster-93339A252.step`;
  drawing `docs/reference/McMaster-93339A252.gif`)
- McMaster 94459A797, M5 flanged heat-set inserts: 6.73 mm long overall, with a 7.92 mm flange 1.02 mm thick,
  a 7.11 mm knurled body, and a 6.32 mm pilot (drawing `docs/reference/McMaster-94459A797.gif`; vendor model
  `cad/vendor/McMaster-94459A797.step`). The drawing calls for a 6.40 mm hole and at least 6.48 mm of
  material. Each is set in its yoke boss from the lens-side face, flange outward, so the screw's reaction
  presses it into its hole
- McMaster 92815A202, M5 thumb nuts used as threadlocked mid-screw handwheels
- Loctite 271, McMaster 91458A160
- heat-set installation tip 92160A327;
- Amazon B0DMCY4FN1, N52 Bar Magnet - 10 mm L × 5 mm W × 2 mm H, as hard plated bearing pads, one at each of
  three screws;
- stainless rod stock, Amazon B08N4TSNPW assortment, for the two groove rods at the fourth screw and for the
  phone rest rod.

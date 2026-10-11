## 11. Provisional areas and next steps

Procurement state and the CAD state of printed parts are tracked in `bom/bom.csv`.

### 11.1 Provisional areas

Design areas marked **Provisional** in the sections above:

- **Light source** ([§6.2](06-light-source.md#62-led-modules), [§6.3](06-light-source.md#63-common-heatsink),
  [§6.7](06-light-source.md#67-focus-and-module-interchange)): M3 heatsink-screw length; lead hole size
  against the lead insulation, cap thread root radius, and Convoy star notch geometry
  ([§6.4](06-light-source.md#64-led-board-mounting)); heatsink temperature rise at 700 mA; white-module
  long-gap focus margin.
- **Cutoff carriage** ([§8](08-cutoff.md#8-cutoff)): spigot fit in the SM1RC/M; guide-stack, recess, and
  pocket dimensions, sliding fits, and datum-pin projection; keeper lift under the ear wedge reactions; bevel
  angle and seating force; the spring's solid height against the loading retraction; clearance to other equipment near the cutoff station.
- **Cassettes** ([§8.6](08-cutoff.md#86-common-cassette-standard),
  [§8.7](08-cutoff.md#87-cassette-clamp-bars)): filament-cleat geometry.
- **Lens cradle and phone rest** ([§9](09-camera-telephoto.md#9-camera-and-telephoto-support)): fit
  allowances of the rod groove, ball-stop rims, and yokes (including the locating walls on the shoe), the
  magnet and rod adhesive, and the retaining-band ring size on an assumed modulus
  ([§9.5](09-camera-telephoto.md#95-lens-cradle), [§9.8](09-camera-telephoto.md#98-retaining-bands)); the
  phone rest's retainer and safety catch ([§9.6](09-camera-telephoto.md#96-phone-rest)); the lens alignment
  procedure, untested ([§9.9](09-camera-telephoto.md#99-lens-alignment)). The alignment tolerances rest on
  assumed lens and camera values, and the contact loads on an assumed lens balance point and phone mass.
- **Printed PLA** ([§1.1](01-context-and-layout.md#11-fabrication-envelope)): creep and relaxation of sustained
  loads, notably the slit-head width-stage preload ([§7.7](07-source-slit.md#77-fabrication-and-fit)), and
  heat exposure of printed parts in transport and use.
- **Mirror cell** ([§10.5](10-mirror-cell.md#105-mirror-mounting),
  [§10.8](10-mirror-cell.md#108-mirror-safety-and-transport-retention)): RTV adhesion primer decision; safety
  retainers; transport sandwich covers, foam, and 1/4-80 thumb screws; quick-release screw hole sizes
  ([§10.9](10-mirror-cell.md#109-tripod-interface)).

### 11.2 Next steps

1. Fit-test the printed cutoff carriage and a cassette blank ([§8](08-cutoff.md#8-cutoff)), including
   datum-pin seating, bevel seating, and keeper lift. Trial wire mounting on the
   filament cleats ([§8.6](08-cutoff.md#86-common-cassette-standard)).
2. Fabricate both threaded LED modules: drill and tap the caps and heatsinks, center each board, and set focus
   on the slit blades; measure the cap thread root radius, and check the lead hole size and the Convoy star
   notch geometry against the physical parts ([§6.4](06-light-source.md#64-led-board-mounting)). Confirm that
   the white module reaches focus; if not, add a thin cap-flange shim
   ([§6.7](06-light-source.md#67-focus-and-module-interchange)). Bench-test the heatsink temperature rise.
3. Fit-test the printed yokes on the shoe, the rod groove, and the retaining bands
   ([§9](09-camera-telephoto.md#9-camera-and-telephoto-support)), after measuring the magnet pull on a screw
   tip, the lens balance point, and the cased phone mass; design the phone rest's retainer and safety catch;
   test the lens alignment procedure ([§9.9](09-camera-telephoto.md#99-lens-alignment)).
4. Design the mirror-cell safety retainers and settle the transport sandwich
   ([§10.8](10-mirror-cell.md#108-mirror-safety-and-transport-retention)), and confirm the quick-release screw
   hole sizes ([§10.9](10-mirror-cell.md#109-tripod-interface)).
5. Assemble the tabletop optical head.
6. Perform a dry optical layout near 3.2 m before making any remaining irreversible holes or bonds.
7. Bond the mirror into the moving plate ([§10.5](10-mirror-cell.md#105-mirror-mounting))
   after a dry fit and an adhesion test.

## 12. Provisional areas and next steps

Procurement state and the CAD state of printed parts are tracked in `bom/bom.csv`.

### 12.1 Provisional areas

Design areas marked **Provisional** in the sections above:

- **LED modules** ([§6.3](06-led-source.md#63-common-heatsink),
  [§6.5](06-led-source.md#65-threaded-led-module)): heatsink temperature rise at 700 mA; M3 heatsink-screw
  length; white-module long-gap focus margin.
- **Source-slit head** ([§8](08-source-slit.md#8-source-slit)): flexure dimensions and stage-rotation
  estimates; spigot and clamp-bar fit; width-stage preload; adapter-plate clearance; slit parallelism and
  rotation; flexure creep.
- **Cutoff carriage** ([§9](09-cutoff.md#9-cutoff)): spigot fit in the SM1RC/M;
  guide-stack, recess, and pocket dimensions, sliding fits, and datum-pin projection; keeper lift under the
  ear wedge reactions; bevel angle and seating force; clearance to other equipment near the cutoff station.
- **Cassettes** ([§9.6](09-cutoff.md#96-common-cassette-standard),
  [§9.7](09-cutoff.md#97-cassette-clamp-bars)): filament-cleat geometry;
  clamp-bar screw length.
- **Phone cradle and telephoto saddle** ([§10](10-camera-telephoto.md#10-camera-and-telephoto-support)):
  the main remaining custom design. Open points include the cradle shape, phone retention and case clearances,
  jack contact geometry, vertical guide strategy and lift-off retention, rail attachment, lens saddle profile
  and retention, the relationship between the phone and lens supports, the removal and reinstallation
  sequence, keeping telephoto weight off the phone mount, and packaging around the cutoff carriage and rail.
- **Mirror cell** ([§11.5](11-mirror-cell.md#115-mirror-mounting),
  [§11.8](11-mirror-cell.md#118-mirror-safety-and-transport-retention)): RTV adhesion primer decision; safety
  retainers and travel cover.

### 12.2 Next steps

1. Fit-test the printed parts: the assembled slit head (§8.7); the cutoff carriage and a cassette blank (§9),
   including datum-pin seating, bevel seating, keeper lift, and clamp-bar screw length.
2. Fabricate both threaded LED modules: drill and tap the caps and heatsinks, center each board, and set
   focus on the slit blades. Confirm that the white module reaches focus; if not, add a thin cap-flange shim
   (§6.5). Bench-test the heatsink temperature rise.
3. Design the phone cradle and telephoto saddle (§10).
4. Design the mirror-cell safety retainers and travel cover (§11.8).
5. Assemble the tabletop optical head.
6. Perform a dry optical layout near 3.2 m before making any remaining irreversible holes or bonds.
7. Bond the mirror into the moving plate (§11.5) at the destination, after a dry fit and an adhesion test.
   The cell is otherwise assembled; the mirror travels separately, protected, because there is not enough
   cure time before departure.

## 11. Provisional areas and next steps

Procurement state and the CAD state of printed parts are tracked in `bom/bom.csv`.

### 11.1 Provisional areas

Design areas marked **Provisional** in the sections above:

- **Light source** ([§6.2](06-light-source.md#62-led-modules), [§6.3](06-light-source.md#63-common-heatsink),
  [§6.7](06-light-source.md#67-focus-and-module-interchange)): M3 heatsink-screw length; Convoy star notch
  geometry
  ([§6.4](06-light-source.md#64-led-board-mounting)); heatsink temperature rise at 700 mA; white-module
  long-gap focus margin.
- **Lens cradle and phone rest** ([§9](09-camera-telephoto.md#9-camera-and-telephoto-support)): retaining-band
  ring size on an assumed modulus ([§9.8](09-camera-telephoto.md#98-retaining-bands)); the lens alignment
  procedure, untested ([§9.9](09-camera-telephoto.md#99-lens-alignment)). The alignment tolerances rest on
  assumed lens and camera values. The inside of the
  phone case (camera lip height, back and front thickness, openings) is assumed
  ([§9.1](09-camera-telephoto.md#91-camera)).
- **Mirror cell** ([§10.5](10-mirror-cell.md#105-mirror-mounting),
  [§10.8](10-mirror-cell.md#108-mirror-safety-and-transport-retention)): RTV adhesion primer decision; safety
  retainers; transport sandwich covers, foam, and 1/4-80 thumb screws.

### 11.2 Next steps

1. Fabricate both threaded LED modules: drill and tap the caps and heatsinks, center each board, and set focus
   on the slit blades; check the Convoy star
   notch geometry against the physical parts ([§6.4](06-light-source.md#64-led-board-mounting)). Confirm that
   the white module reaches focus; if not, add a thin cap-flange shim
   ([§6.7](06-light-source.md#67-focus-and-module-interchange)). Bench-test the heatsink temperature rise.
2. Assemble the tabletop optical head.
3. Bond the mirror into the moving plate ([§10.5](10-mirror-cell.md#105-mirror-mounting)) after an adhesion
   test.
4. Test the lens alignment procedure ([§9.9](09-camera-telephoto.md#99-lens-alignment)).
5. Design the mirror-cell safety retainers and settle the transport sandwich
   ([§10.8](10-mirror-cell.md#108-mirror-safety-and-transport-retention)).

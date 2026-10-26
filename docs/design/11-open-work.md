## 11. Provisional areas and next steps

Procurement state and the CAD state of printed parts are tracked in `bom/bom.csv`.

### 11.1 Provisional areas

Design areas marked **Provisional** in the sections above:

- **Light source** ([§6.3](06-light-source.md#63-common-heatsink),
  [§6.7](06-light-source.md#67-focus-and-module-interchange),
  [§6.8](06-light-source.md#68-cap-and-heatsink-drilling-fixture)): drilling-fixture bushing bores and printed
  accuracy; heatsink temperature rise at 700 mA; white-module long-gap focus margin.
- **Lens cradle and phone rest** ([§9](09-camera-telephoto.md#9-camera-and-telephoto-support)): the lens
  alignment procedure, untested, and the finger room for the aft thumb nuts beside the phone
  ([§9.9](09-camera-telephoto.md#99-lens-alignment)); the unresolved 4.7 mm difference between the measured
  and listed lens length ([§9.2](09-camera-telephoto.md#92-telephoto)). The alignment tolerances
  ([§9.3](09-camera-telephoto.md#93-alignment-requirements)) rest on an assumed lens position behind the
  cutoff plane and an assumed camera pupil.
- **Mirror cell** ([§10.5](10-mirror-cell.md#105-mirror-mounting),
  [§10.8](10-mirror-cell.md#108-mirror-safety-and-transport-retention)): RTV adhesion primer decision; safety
  retainers; transport sandwich covers, foam, and 1/4 in-80 thumb screws.

### 11.2 Next steps

1. Print the drilling fixture and its bore coupon
   ([§6.8](06-light-source.md#68-cap-and-heatsink-drilling-fixture)). Fabricate both threaded LED modules:
   drill and tap the caps and heatsinks, center each board, and set focus on the slit blades. Confirm that the
   white module reaches focus; if not, add a thin cap-flange shim
   ([§6.7](06-light-source.md#67-focus-and-module-interchange)). Bench-test the heatsink temperature rise.
2. Bond the mirror into the mirror plate ([§10.5](10-mirror-cell.md#105-mirror-mounting)) after an adhesion
   test.
3. Test the lens alignment procedure ([§9.9](09-camera-telephoto.md#99-lens-alignment)), including the aft
   thumb-nut finger room on the real phone, then write a consolidated setup and alignment procedure for the
   apparatus.
4. Design the mirror-cell safety retainers and settle the transport sandwich
   ([§10.8](10-mirror-cell.md#108-mirror-safety-and-transport-retention)).

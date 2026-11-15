## 11. Provisional areas and next steps

Procurement state and the CAD state of printed parts are tracked in `bom/bom.csv`.

### 11.1 Provisional areas

Design areas marked **Provisional** in the sections above:

- **Light source** ([§5.2](05-light-source.md#52-led-modules),
  [§5.3](05-light-source.md#focus)): heatsink temperature rise at 700 mA;
  white-module long-gap focus margin.
- **Lens cradle and phone rest** ([§9](09-camera-telephoto.md#9-camera-and-telephoto-support)): the lens
  alignment procedure, untested ([§9.9](09-camera-telephoto.md#99-lens-alignment)). The alignment tolerances
  ([§9.3](09-camera-telephoto.md#93-alignment-requirements)) rest on an assumed lens position behind the
  cutoff plane and an assumed camera pupil ([§2.9](01-context-and-layout.md#29-telephoto-and-camera-optics));
  the rear-glass vignetting limit rests on an assumed distance from the rear glass to the camera pupil, to be
  fixed by a flat-field photograph.
- **Rail pivot bushings** ([§3.3](03-frame.md#33-pivot-and-yaw-hardware)): the 8 mm bored pivot holes with
  press-in bronze sleeves, and the same in the pivot lugs' front holes; the bolt's thread length against the stack; the drilling template and frame model
  still show 5.5 mm pivot holes.
- **Slit stage head** ([§6.6](06-source-slit.md#66-fabrication-and-fit)): the stage's dimensions are the
  manufacturer's, not measured; the blade overhang and the toe bar's squeeze are first-print values, as is how flat
  the stamped blade folds lie on the seats and under the toe pad
  ([§6.1](06-source-slit.md#61-blades-and-slit-widths), [§6.4](06-source-slit.md#64-blade-clamping)); the
  stage-screw length behind the plate.
- **Baffle** ([§6.8](06-source-slit.md#68-baffle)): the clamp's bore clearance and split gap; the net's
  stiffness and vane depth; the glare reduction of the painted vanes, to be confirmed on the bench.
- **Field lens** ([§2.7](01-context-and-layout.md#27-slit-and-field-lens)): the iris-to-slit distance its position and the iris
  setting rest on (calculated, not measured); the mirror illumination with the lens in place and removed, to be
  confirmed from a flat-field photograph.
- **Slit focus target, ground-glass variant** ([§6.7](06-source-slit.md#67-slit-focus-target)): the pocket
  clearance, gasket, and grit.
- **Cassette razor-blade clamping** ([§8.7](08-cutoff.md#87-cassette-clamp-bars)): how the clamp bars bear on a
  blade whose 7.04 mm fold lies under them, and the resulting bar height.
- **Mirror cell** ([§10.5](10-mirror-cell.md#105-mirror-mounting),
  [§10.8](10-mirror-cell.md#108-mirror-safety-and-transport-retention)): RTV adhesion primer decision; safety
  retainers; transport sandwich foam, through-bolts, sheaths, and nuts.

### 11.2 Next steps

1. Set focus on the slit blades with each LED module and confirm that the white module reaches focus; if not,
   add a thin cap-flange shim ([§5.3](05-light-source.md#focus)). Bench-test the
   heatsink temperature rise.
2. With the field lens in place and removed, photograph the flat-field mirror illumination, confirm the iris
   setting, and measure the iris-to-slit distance ([§2.7](01-context-and-layout.md#27-slit-and-field-lens)).
3. Bond the mirror into the mirror plate ([§10.5](10-mirror-cell.md#105-mirror-mounting)) after an adhesion
   test.
4. Test the lens alignment procedure ([§9.9](09-camera-telephoto.md#99-lens-alignment)), then write a
   consolidated setup and alignment procedure for the apparatus.
5. Design the mirror-cell safety retainers and settle the transport sandwich
   ([§10.8](10-mirror-cell.md#108-mirror-safety-and-transport-retention)).
6. Print the baffle clamp as a short coupon to settle its bore clearance and split gap, then print the baffle,
   paint it, wrap it, and compare the stray light with the baffle in place and removed
   ([§6.8](06-source-slit.md#68-baffle)).

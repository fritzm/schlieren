## 12. Provisional areas and next steps

Procurement state and the CAD state of printed parts are tracked in `bom/bom.csv`.

### 12.1 Provisional areas

Design areas marked **Provisional** in the sections above:

- **Light source** ([§6.2](06-light-source.md#62-led-modules),
  [§6.3](06-light-source.md#focus)): heatsink temperature rise at 700 mA;
  white-module long-gap focus margin.
- **Lens cradle and phone rest** ([§10](10-camera-telephoto.md#10-camera-and-telephoto-support)): the lens
  alignment procedure, untested ([§10.9](10-camera-telephoto.md#109-lens-alignment)). The alignment tolerances
  ([§10.3](10-camera-telephoto.md#103-alignment-requirements)) rest on an assumed lens position behind the
  cutoff plane and an assumed camera pupil; the rear-glass vignetting limit rests on an assumed distance
  from the rear glass to the camera pupil, to be fixed by a flat-field photograph.
- **Rail pivot bushings** ([§4.3](04-frame.md#43-pivot-and-yaw-hardware)): the 8 mm bored pivot holes with
  press-in bronze sleeves, and the same in the pivot lugs' front holes; the bolt's thread length against the stack; the drilling template and frame model
  still show 5.5 mm pivot holes.
- **Slit stage head** ([§7.6](07-source-slit.md#76-fabrication-and-fit)): the stage's dimensions are the
  manufacturer's, not measured; the blade overhang and the toe bar's squeeze are first-print values, as is how flat
  the stamped blade folds lie on the seats and under the toe pad
  ([§7.1](07-source-slit.md#71-blades-and-slit-widths), [§7.4](07-source-slit.md#74-blade-clamping)); the
  stage-screw length behind the plate.
- **Baffle** ([§7.8](07-source-slit.md#78-baffle)): the clamp's bore clearance and split gap; the net's
  stiffness and vane depth; the glare reduction of the painted vanes, to be confirmed on the bench.
- **Field lens** ([§8](08-field-lens.md#8-field-lens)): the iris-to-slit distance its position and the iris
  setting rest on (calculated, not measured); the mirror illumination with the lens in place and removed, to be
  confirmed from a flat-field photograph.
- **Slit focus target, ground-glass variant** ([§7.7](07-source-slit.md#77-slit-focus-target)): the pocket
  clearance, gasket, and grit.
- **Cassette razor-blade clamping** ([§9.7](09-cutoff.md#97-cassette-clamp-bars)): how the clamp bars bear on a
  blade whose 7.04 mm fold lies under them, and the resulting bar height.
- **Mirror cell** ([§11.5](11-mirror-cell.md#115-mirror-mounting),
  [§11.8](11-mirror-cell.md#118-mirror-safety-and-transport-retention)): RTV adhesion primer decision; safety
  retainers; transport sandwich foam, through-bolts, sheaths, and nuts.

### 12.2 Next steps

1. Set focus on the slit blades with each LED module and confirm that the white module reaches focus; if not,
   add a thin cap-flange shim ([§6.3](06-light-source.md#focus)). Bench-test the
   heatsink temperature rise.
2. With the field lens in place and removed, photograph the flat-field mirror illumination, confirm the iris
   setting, and measure the iris-to-slit distance ([§8](08-field-lens.md#8-field-lens)).
3. Bond the mirror into the mirror plate ([§11.5](11-mirror-cell.md#115-mirror-mounting)) after an adhesion
   test.
4. Test the lens alignment procedure ([§10.9](10-camera-telephoto.md#109-lens-alignment)), then write a
   consolidated setup and alignment procedure for the apparatus.
5. Design the mirror-cell safety retainers and settle the transport sandwich
   ([§11.8](11-mirror-cell.md#118-mirror-safety-and-transport-retention)).
6. Print the baffle clamp as a short coupon to settle its bore clearance and split gap, then print the baffle,
   paint it, wrap it, and compare the stray light with the baffle in place and removed
   ([§7.8](07-source-slit.md#78-baffle)).

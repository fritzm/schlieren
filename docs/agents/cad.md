# CAD conventions

Prefer: named parameters (no unexplained numeric constants), explicit interfaces, helper functions where
repetition is meaningful, simple constructive geometry, deterministic builds, assertions or tests for
important dimensions and relationships.

Separate physical nominal dimensions from fabrication allowances:

```python
POST_DIAMETER = 12.70
POST_DIAMETRAL_CLEARANCE = 0.25
POST_BORE = POST_DIAMETER + POST_DIAMETRAL_CLEARANCE
```

Name clearances by direction: radial, diametral, axial, etc.

Unresolved required dimension: expose it as a parameter or mark it provisional; never bury the assumption in
geometry. Keep part-specific calibration and experimental compensation values with the part unless they have
clearly become project-wide standards.

## Shared building blocks

Use these; do not redefine them in a part module.

- `schlieren/standards.py`: project-wide dimensions used by more than one model (`INCH`, `OPTICAL_HEIGHT`,
  the TR50/M post and datum shim). Parameter classes take them as defaults.
- `schlieren/palette.py`: every viewer color, named. No color literals in part modules; add to the palette or
  reuse the matching entry.
- `schlieren/cad.py`:
  - primitive solids named by axis and extents: `box_between`, `floor_box`, `centered_box`,
    `x_cylinder`/`y_cylinder`/`z_cylinder`, `centered_cylinder`, `y_cone`/`z_cone`, `y_hex`/`z_hex`
    (cylinders take diameters); the axis planes; assembly helpers `labeled`, `place`, `assembly`, `moved`.
  - `CUT_OVERRUN`: the 1 mm a cutter extends past the faces it cuts; use it, not a bare `± 1`.
  - `children_by_label` raises on duplicate sibling labels; give siblings distinct labels.
  - `intersect` / `fused` replace `a & b` / `a + b` wherever the result's `.volume`, `.solids()` or
    `.is_inside` is used, so `ty` passes: build123d's `&` returns `None` for no overlap (`intersect` returns
    an empty Compound, volume 0), and its stubs type `+` as possibly a `Wire`.
- `schlieren/validation.py`: `require_positive_dimensions`, for a parameter class's `validate`; names the
  offending field.
- `schlieren/hardware.py`: catalog dimensions of purchased hardware used by more than one model (bar magnet,
  FAS100, 98625A950 insert, 2006N292 spring, common M3 hardware). Parameter classes take them as defaults and
  add their own fabrication allowances; hardware used by one model stays with that model.
- `post_stack` in `parts/rail_shoe.py`: post, rail shoe, shoe clamp hardware, optional SM1RC/M ring and
  side-channel screws, shown by every fixture on a rail.
- `parts/adjuster.py`: FAS100, its brass insert and bearing magnet, as the slit head and cutoff carriage show
  them.

Place assembly children with `labeled(shape, label, color, loc)` and `place`. Move large models with
`cad.moved(shape, loc)`, never `loc * shape`: build123d's `Location * shape` deep-copies the whole B-rep,
`moved` only composes locations (this was most of the optical-head build cost).

## Units

Millimeters for internal CAD geometry unless there is a strong reason not to. Keep inherently imperial
interfaces in conventional form when useful: screw and thread designations, sheet thicknesses, commercial
hardware dimensions, other purchased components specified primarily in inches. Convert deliberately at the
model boundary; never mix implicit units.

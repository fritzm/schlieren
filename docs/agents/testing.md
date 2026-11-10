# Tests

Add tests that protect against accidental geometry changes. Good candidates: overall bounding dimensions,
bore diameters, hole spacing, optical-axis locations, interface dimensions, symmetry, required clearances,
counts of repeated features. Test engineering invariants, not implementation details. Never change a test
just to pass an unintended geometry change.

## Running

Iterate with `uv run run-tests`; after changing CAD or supporting code, run the tests relevant to the change.
Tests taking more than a few seconds (typically exhaustive pairwise interference or rotation sweeps) are
marked `@slow` (`schlieren.testing`) and skipped by default (the skip count is reported). Run
`uv run run-tests --full` before presenting work.

The full run takes well under a minute. If it grows to minutes, suspect per-pair bounding boxes,
`loc * shape` on large models, or an assembly built more than once per module.

## Building models

- Build each model once per test class. The parameters and the model most tests use go in `setUpClass`.
- Every other model at default parameters and pose is a `@shared` attribute (`schlieren.testing`), built on
  first use, so a model only slow tests need costs the default run nothing.
- Build a model in the test only for a variant (changed parameters or pose) or when the build is what is under
  test.
- Never modify a shared model.
- If every pose of an assembly rebuilds the same pose-independent parts, cache those builders in the part
  module (`functools.cache` on the frozen parameter class, as `parts/carriage.py` does) instead of working
  around the cost in tests.

## Pairwise checks

- Use the bounding-box prefilters in `schlieren.testing` (`near_pairs`, `near_pairs_among`, `boxes_overlap`,
  `overlap_volume`, `bounded_distance`) before exact boolean or distance queries.
- If a group of parts keeps the same relative placement across a sweep (an engagement, a board), check the
  pairs inside the group once, not per step.
- Exact bounding boxes of vendor models cost tens of milliseconds each and are not cached. The loose box is
  much cheaper and only ever larger, so it is safe for a prefilter. Leave `loose` off where the box test is
  itself the assertion.

# iPhone schlieren — Agent Instructions

This repository contains the code, CAD source, tests, tooling, and other version-controlled engineering
artifacts for the iPhone schlieren Deep Creek vacation project.

Do not assume that repository history, chat history, generated files, or remembered context represents the
current physical design. Read the relevant repository resources (`docs/design/`, `bom/bom.csv`) before
substantive work.

## Sources of truth

Git is authoritative for the design baseline and the BOM. Rendered views of both, `docs/schlieren-design.pdf`
and `bom/schlieren-bom.xlsx`, are generated from those sources and versioned beside them for reading and
sharing by repository link.

Use the following priority order:

1. Explicit instructions from the user in the current session.
2. This `AGENTS.md`.
3. Current repository contents (including `bom/` and `docs/design/`).
4. Git history, old chats, summaries, and other historical material.

If two sources conflict, prefer the higher-priority source.

Do not resurrect superseded or rejected designs merely because they appear in Git history, comments, old
files, or conversation history.

### Design description: `docs/design/`

Per-subsystem Markdown fragments, named `NN-*.md`; filename order is document order. Authoritative for:

- the design baseline, dimensions and geometry
- architecture, mechanical and optical concepts
- design decisions and rationale
- provisional (open or evolving) design areas and next steps

Described design is the baseline unless explicitly marked **Provisional**; `11-open-work.md` rolls up the
provisional areas and next steps. Read only the fragment(s) relevant to the task (section numbers match the
BOM `Source section` column), plus `11-open-work.md` for cross-cutting open work. Do not read the whole set
unless the task needs it.

`uv run build-design-doc` concatenates the fragments into `exports/docs/schlieren-design.md`
(generated; never edit it) and copies `docs/design/figures/` beside it. With `--pdf` it also writes
`schlieren-design.html` there and prints it to `docs/schlieren-design.pdf`, the versioned rendered copy. The
PDF step needs a local Chrome or Chromium and network access (KaTeX, for the formulas). Rebuild the PDF when
the fragments or figures change; it is not reproducible byte for byte, so do not rebuild it needlessly.

Figures in `docs/design/figures/` are PNG renders (`src/schlieren/render.py`) and SVG drawings generated from
the CAD by a part command's `--figure` option and versioned so the fragments display without a build. They are derived
artifacts: regenerate one when its part's geometry changes; never edit it by hand.

### BOM and procurement: `bom/bom.csv`

Single CSV, one row per BOM line item. Authoritative for BOM contents, quantities, subsystem allocations,
vendors, SKUs, procurement status, inventory state, purchasing notes, and the CAD state of printed parts
(`CAD ready` / `CAD open`). The design fragments do not track procurement or CAD state.

`uv run build-bom-xlsx` builds `bom/schlieren-bom.xlsx` (BOM tab, Summary formulas, procurement-state
conditional formatting) from the CSV. The workbook is versioned and must match the CSV (a test checks this):
rebuild it whenever `bom.csv` changes. The build is reproducible, so an unchanged CSV gives an unchanged file.

The workbook is also the convenient place to edit the BOM in a spreadsheet program. Such edits are not
authoritative until reconciled into the CSV: `uv run reconcile-bom [workbook.xlsx]` reports the differences
row by row, and `--apply` writes them to `bom.csv`. Review the report with the user before applying; never
overwrite the CSV blindly.

Read `bom/bom.csv` before answering or acting on procurement, BOM, inventory, vendor, quantity, or purchasing
questions.

### Reference drawings: `docs/reference/`

Vendor drawings and datasheets for purchased parts, named `<Brand>-<part>.pdf` (see the README there).
Consult them for catalog dimensions. They are manufacturer specifications, not measured values or committed
project dimensions; a measurement recorded in `docs/design/` takes precedence.

## Repository authority

This Git repository is authoritative for version-controlled engineering artifacts, including:

- build123d source, Python source, tests, CAD/build utilities
- the design fragments and `bom/bom.csv`
- repository configuration and agent instructions
- deliberately versioned generated outputs, if any

Generated files (`exports/`, the consolidated design document, `docs/schlieren-design.pdf`,
`bom/schlieren-bom.xlsx`) are derived artifacts; the PDF and the workbook are versioned, `exports/` is not.

## Design decisions and canonical updates

Discussion, experiments, CAD changes, and proposed ideas are provisional until the user accepts them as final.

Do not silently promote a proposal into the project baseline.

When the user finalizes a design decision:

1. update the applicable CAD/source/tests in this repository;
2. update the applicable `docs/design/` fragment(s);
3. if the decision changes procurement, quantity, allocation, vendor choice, or BOM structure, also update
   `bom/bom.csv`;
4. verify that the affected files agree.

A procurement-only change normally updates `bom/bom.csv` without changing the status fragments unless it
materially changes the engineering baseline.

A CAD experiment or exploratory branch should not update the status fragments or BOM unless the user
explicitly accepts the result.

## CAD conventions

build123d source is the authoritative representation of programmatically generated mechanical geometry.

Generated STEP, STL, 3MF, DXF, or similar files are derived artifacts unless explicitly documented otherwise.

Do not manually edit a generated artifact and treat it as the new source.

Prefer:

- clear named parameters
- explicit interfaces
- reusable helper functions where repetition is meaningful
- simple constructive geometry
- deterministic builds
- assertions or tests for important dimensions and relationships

Avoid unexplained numeric constants.

Separate physical nominal dimensions from fabrication allowances. For example:

```python
POST_DIAMETER = 12.70
POST_DIAMETRAL_CLEARANCE = 0.25
POST_BORE = POST_DIAMETER + POST_DIAMETRAL_CLEARANCE
```

Use names that make it clear whether a clearance is radial, diametral, axial, or otherwise directional.

### Shared building blocks

Use these instead of redefining them in a part module:

- `schlieren/standards.py`: dimensions more than one model depends on (`INCH`, `OPTICAL_HEIGHT`, the TR50/M
  post and datum disc). Parameter classes take them as defaults.
- `schlieren/palette.py`: every viewer color, named. Do not put a color literal in a part module; add it
  to the palette (or reuse the matching entry).
- `schlieren/cad.py`: primitive solids named by axis and extents (`box_between`, `floor_box`,
  `centered_box`, `x_cylinder`/`y_cylinder`/`z_cylinder`, `centered_cylinder`, `y_cone`/`z_cone`,
  `y_hex`/`z_hex`), the axis planes, and the assembly helpers (`labeled`, `place`, `assembly`). Cylinders take
  diameters. `CUT_OVERRUN` is the 1 mm a cutter extends past the faces it cuts through; use it rather than a
  bare `± 1`. `children_by_label` raises on duplicate sibling labels, so give siblings distinct labels.
- `schlieren/validation.py`: `require_positive_dimensions`, for a parameter class's `validate`; it names the
  offending field.
- `schlieren/hardware.py`: catalog dimensions of purchased hardware that more than one model uses (the
  bar magnet, the FAS100, the 98625A950 insert, the 2006N292 spring, common M3 hardware). Parameter classes
  take them as defaults and add their own fabrication allowances; hardware used by one model stays with it.
- `post_stack` in `parts/rail_shoe.py`: the post, rail shoe, shoe clamp hardware, and optional SM1RC/M ring
  and side-slot screws that every fixture on a rail shows.
- `parts/adjuster.py`: the FAS100, its brass insert, and its bearing magnet, as the slit head and cutoff
  carriage show them.

Place assembly children with `labeled(shape, label, color, loc)` and `place`, not `loc * shape`: build123d's
`Location * shape` deep-copies the whole B-rep, and `labeled` only composes locations. That difference was
most of the cost of building the optical head.

### Units

Use millimeters for internal CAD geometry unless there is a strong reason not to.

Preserve inherently imperial interfaces in their conventional form when useful, including:

- screw and thread designations
- sheet thicknesses
- commercial hardware dimensions
- other purchased components specified primarily in inches

Convert deliberately at the model boundary rather than mixing implicit units.

## Suggested repository organization

Prefer this structure as the project grows:

```text
src/schlieren/
    __init__.py
    standards.py   # project-wide dimensions
    hardware.py    # catalog dimensions of shared purchased hardware
    palette.py     # viewer colors
    validation.py  # shared parameter-class checks
    cad.py         # primitive solids, axis planes, assembly helpers
    vendor_cad.py  # vendor STEP models placed in documented mounting frames
    render.py      # offscreen figure rendering
    testing.py     # test helpers: @slow, bounding-box prefilters
    parts/
        ...
    cli/
        _common.py # shared options and export/drawing/figure/viewer steps
        ...        # command-line entry points, registered in pyproject.toml [project.scripts]

tests/
    ...

exports/
    step/
    stl/

AGENTS.md
pyproject.toml
README.md
```

This is a default organization, not a requirement to create empty directories prematurely.

Put genuinely project-wide dimensional standards in `schlieren/standards.py`, and project-wide colors in
`schlieren/palette.py`.

Keep part-specific calibration dimensions and experimental compensation values with the relevant part unless
they have clearly become project-wide standards.

## Tests

Add tests where they provide useful protection against accidental geometry changes.

Good candidates include:

- overall bounding dimensions
- bore diameters
- hole spacing
- optical-axis locations
- interface dimensions
- symmetry
- required clearances
- quantities or counts of repeated features

Prefer testing engineering invariants rather than implementation details.

Run relevant tests after modifying CAD or supporting code.

Tests that take more than a few seconds, typically exhaustive pairwise interference or rotation-sweep
checks, are marked `@slow` (`schlieren.testing`) and skipped by default so that iteration stays quick; the
skip count is reported. Run `uv run run-tests --full` before presenting completed work. Use a bounding-box
prefilter before exact boolean or distance queries in new pairwise checks: `near_pairs(first, second, margin)`
and `near_pairs_among(shapes, margin)` box each shape once; `boxes_overlap(a, b, loose=True)` is the
single-pair form; `overlap_volume(a, b)` and `bounded_distance(a, b, limit)` are the intersection volume and
the distance with the exact query skipped when the boxes already settle it. Move large models with
`cad.moved(shape, loc)` rather than `loc * shape`. Where a group of parts keeps the same relative placement
across a sweep (an engagement, a board), check the pairs inside the group once, not per step. Exact bounding boxes of
vendor models cost tens of milliseconds each and are not cached, so a pair loop that recomputes them is slow;
the loose box is much cheaper and only ever larger, so it is safe for a prefilter. Leave `loose` off where the
box test is itself the assertion.

The full run takes well under a minute. If it grows to minutes, suspect per-pair bounding boxes, `loc * shape`
on large models, or an assembly built more than once per module.

Do not change a test merely to make an unintended geometry change pass.

## Commands

Dependencies are managed with `uv` (Python >= 3.12). Tests use `unittest`; ruff is run via `uvx`.

```sh
uv sync                                               # install/update the environment
uv run run-tests                                      # fast tests, one process per module in parallel; iterate with this
uv run run-tests --full                               # adds the slow interference/sweep tests; run before presenting work
uv run run-tests test_carriage                        # chosen modules only
uv run python -m unittest tests.test_carriage -v      # one module, serial and verbose (SCHLIEREN_TESTS=full for slow tests)
uvx ruff check . && uvx ruff format .                 # lint/format (rule set and line length 110 in pyproject.toml)
uv run <command> --help                               # part commands: build/export (--show opens the viewer)
uv run rail-shoe --figure                             # re-render docs/design/figures/rail-shoe.png
uv run build-design-doc [--pdf]                       # docs/design/ -> exports/docs/, docs/schlieren-design.pdf
uv run build-bom-xlsx                                 # bom/bom.csv -> bom/schlieren-bom.xlsx
uv run reconcile-bom [workbook.xlsx] [--apply]        # edited workbook -> differences from bom/bom.csv
```

Commands live in `src/schlieren/cli/` and are registered in `pyproject.toml` `[project.scripts]`; run them with
`uv run <command>` from the repo root. Output paths such as `--output` default to `exports/` relative to the
current directory. To add a command: write `cli/<name>.py` with `main()` and register it in
`[project.scripts]`. Build the options and the export, drawing, figure, and viewer steps from
`cli/_common.py` (`add_output_option`, `add_show_option`, `add_figure_option`, `export_models`,
`write_text`, `render`, `show`); keep geometry, such as a print layout, in the part module so it can be tested.

A `Makefile` rebuilds every derived artifact that is out of date (design-doc figures, the consolidated
design document and PDF, the BOM workbook) and nothing else: run `make` (or `make figures`, `doc`, `pdf`,
`bom`; `make -n` previews; `make test` runs the full suite) instead of invoking the part commands and
builders one by one. Its dependencies are declared by hand: when a part module gains an import, or a new
figure or `--figure` output is added, update the matching rule in the `Makefile`; the shared modules
(`cad.py`, `standards.py`, `palette.py`, `hardware.py`, `vendor_cad.py`, `render.py`, `cli/_common.py`) are in its `CORE` list.
Do not use `make -t`; it marks stale targets current without rebuilding them.

A `.claude/` PostToolUse hook auto-formats edited `.py` files with ruff, and a PreToolUse hook blocks direct
edits to `exports/`. Project skills: `/finalize-decision` (propagate an accepted decision) and
`/reconcile-bom` (review and apply edits made in a copy of the BOM workbook).

## Working with the BOM

Treat each BOM row as a distinct project allocation where `bom/bom.csv` does so.

Do not merge rows solely because Vendor + SKU are identical.

Procurement rollups may aggregate identical Vendor + SKU combinations, but
allocation rows should remain distinct when they serve different subsystems.

Quote any `bom.csv` field that contains a comma (notes and item names often do); an unquoted comma splits the
row, and `test_bom` fails on the ragged row. Edit the CSV as text or with the `csv` module, then rebuild the
workbook.

Do not guess:

- procurement state
- quantity
- vendor
- SKU
- package size
- arrival state

If a required value is unresolved, preserve that uncertainty rather than inventing a value.

## Working with the design document

Keep the design document a description of the design as it stands, with relevant rationale; it is not a
status-tracking or history document.

When updating it:

- preserve established terminology;
- state settled design plainly; mark open or evolving areas **Provisional** and keep the §11 rollup in step;
- when a decision changes, rewrite the affected text to describe the new design; do not narrate what it
  replaced ("previously", "no longer", "superseded");
- retain useful rationale where it explains a non-obvious current decision;
- leave procurement and CAD state, and detailed BOM data, to `bom/bom.csv`.

Do not turn historical alternatives into current design requirements.

## Change scope

Make the smallest coherent change that satisfies the task.

Do not opportunistically redesign unrelated subsystems.

Do not alter established interfaces, dimensions, dependencies, or procurement decisions merely to simplify
code.

If a requested change exposes a likely conflict elsewhere, identify the conflict before silently changing the
other subsystem.

## Git behavior

Do not commit, push, force-push, rebase shared history, delete branches, create releases, or change remote
repository settings unless the user explicitly asks.

Working-tree edits and tests are permitted when required by the task.

Keep generated transient files, viewer artifacts, caches, and local environments out of version control.

Prefer small, reviewable diffs.

Before presenting completed work:

- inspect the diff;
- remove accidental or unrelated changes;
- run relevant tests;
- report important assumptions or unresolved issues.

## Engineering reasoning

Distinguish clearly between:

- measured values
- manufacturer specifications
- committed project dimensions
- calculated values
- fabrication allowances
- provisional estimates

Do not silently replace a measured value with a nominal catalog value.

When calculations depend materially on current project dimensions, read the relevant `docs/design/`
fragment(s) first.

When a required dimension remains unresolved, expose it as a parameter or clearly mark it as provisional
rather than burying an assumption in geometry.

## Agent workflow

At the beginning of a substantial task:

1. read this `AGENTS.md`;
2. determine whether the task depends on current design state, BOM state, or both;
3. read the applicable `docs/design/` fragment(s) and/or `bom/bom.csv`;
4. inspect the relevant repository CAD/source files;
5. make the requested change;
6. run appropriate verification;
7. update `docs/design/` and `bom/bom.csv` only when the user has finalized a decision and the rules above
   require it, and rebuild the versioned PDF and workbook to match.

The objective is to keep CAD, implementation, design state, and procurement state synchronized without
treating exploratory work as finalized engineering.

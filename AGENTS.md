# iPhone schlieren — Agent Instructions

This repository contains the code, CAD source, tests, tooling, and other version-controlled engineering
artifacts for the iPhone schlieren Deep Creek vacation project.

Do not assume that repository history, chat history, generated files, or remembered context (including agent
memory) represents the current physical design; none of these overrides the repository. Read the relevant
repository resources (`docs/design/`, `bom/bom.csv`) before substantive work.

## Sources of truth

Git is authoritative for version-controlled engineering artifacts: build123d and Python source, tests,
CAD/build utilities, the design fragments, `bom/bom.csv`, repository configuration, and agent instructions.

Use the following priority order:

1. Explicit instructions from the user in the current session.
2. This `AGENTS.md`.
3. Current repository contents (including `bom/` and `docs/design/`).
4. Git history, old chats, summaries, and other historical material.

If two sources conflict, prefer the higher-priority source.

Do not resurrect superseded or rejected designs merely because they appear in Git history, comments, old
files, or conversation history, and do not turn historical alternatives into current design requirements.

### Derived artifacts

Generated files are derived artifacts: never edit one by hand and treat it as the new source. They are:

- `exports/` (STEP, STL, drawings, the consolidated design document): not versioned;
- `docs/schlieren-design.pdf` and `bom/schlieren-bom.xlsx`: versioned beside their sources for reading and
  sharing by repository link;
- `docs/design/figures/`: versioned so the fragments display without a build.

Generated STEP, STL, 3MF, DXF, or similar files are derived unless explicitly documented otherwise. build123d
source is the authoritative representation of programmatically generated mechanical geometry.

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

`uv run build-design-doc` concatenates the fragments into `exports/docs/schlieren-design.md` (generated; never
edit it) and copies `docs/design/figures/` beside it. With `--pdf` it also writes `schlieren-design.html`
there and prints it to `docs/schlieren-design.pdf`. The PDF step needs a local Chrome or Chromium and network
access (KaTeX, for the formulas). Rebuild the PDF when the fragments or figures change; it is not reproducible
byte for byte, so do not rebuild it needlessly.

Figures are PNG renders (`src/schlieren/render.py`) and SVG drawings generated from the CAD by a part
command's `--figure` option. Regenerate one when its part's geometry changes.

### BOM and procurement: `bom/bom.csv`

Single CSV, one row per BOM line item. Authoritative for BOM contents, quantities, subsystem allocations,
vendors, SKUs, procurement status, inventory state, purchasing notes, and the CAD state of printed parts
(`CAD ready` / `CAD open`). The design fragments do not track procurement or CAD state.

Read `bom/bom.csv` before answering or acting on procurement, BOM, inventory, vendor, quantity, or purchasing
questions.

`uv run build-bom-xlsx` builds `bom/schlieren-bom.xlsx` (BOM tab, Summary formulas, procurement-state
conditional formatting) from the CSV. The workbook must match the CSV (a test checks this): rebuild it
whenever `bom.csv` changes. The build is reproducible, so an unchanged CSV gives an unchanged file.

The workbook is also the convenient place to edit the BOM in a spreadsheet program. Such edits are not
authoritative until reconciled into the CSV: `uv run reconcile-bom [workbook.xlsx]` reports the differences
row by row, and `--apply` writes them to `bom.csv`. Review the report with the user before applying; never
overwrite the CSV blindly.

### Reference drawings: `docs/reference/`

Vendor drawings and datasheets for purchased parts, named `<Brand>-<part>.pdf` (see the README there). Consult
them for catalog dimensions. They are manufacturer specifications, not measured values or committed project
dimensions; a measurement recorded in `docs/design/` takes precedence.

## Design decisions and canonical updates

Discussion, experiments, CAD changes, and proposed ideas are provisional until the user accepts them as final.
A CAD experiment or exploratory branch should not update the design fragments or the BOM unless the user
explicitly accepts the result. Do not silently promote a proposal into the project baseline.

When the user finalizes a design decision:

1. update the applicable CAD/source/tests in this repository;
2. update the applicable `docs/design/` fragment(s);
3. if the decision changes procurement, quantity, allocation, vendor choice, or BOM structure, also update
   `bom/bom.csv`;
4. rebuild the derived artifacts that depend on what changed (PDF, workbook, figures);
5. verify that the affected files agree.

A procurement-only change normally updates `bom/bom.csv` without changing the design fragments unless it
materially changes the engineering baseline.

## CAD conventions

Prefer:

- clear named parameters, and no unexplained numeric constants
- explicit interfaces
- reusable helper functions where repetition is meaningful
- simple constructive geometry
- deterministic builds
- assertions or tests for important dimensions and relationships

Separate physical nominal dimensions from fabrication allowances. For example:

```python
POST_DIAMETER = 12.70
POST_DIAMETRAL_CLEARANCE = 0.25
POST_BORE = POST_DIAMETER + POST_DIAMETRAL_CLEARANCE
```

Use names that make it clear whether a clearance is radial, diametral, axial, or otherwise directional.

When a required dimension remains unresolved, expose it as a parameter or clearly mark it as provisional
rather than burying an assumption in geometry.

### Shared building blocks

Use these instead of redefining them in a part module:

- `schlieren/standards.py`: project-wide dimensions that more than one model depends on (`INCH`,
  `OPTICAL_HEIGHT`, the TR50/M post and datum shim). Parameter classes take them as defaults.
- `schlieren/palette.py`: every viewer color, named. Do not put a color literal in a part module; add it to
  the palette (or reuse the matching entry).
- `schlieren/cad.py`: primitive solids named by axis and extents (`box_between`, `floor_box`, `centered_box`,
  `x_cylinder`/`y_cylinder`/`z_cylinder`, `centered_cylinder`, `y_cone`/`z_cone`, `y_hex`/`z_hex`), the axis
  planes, and the assembly helpers (`labeled`, `place`, `assembly`, `moved`). Cylinders take diameters.
  `CUT_OVERRUN` is the 1 mm a cutter extends past the faces it cuts through; use it rather than a bare `± 1`.
  `children_by_label` raises on duplicate sibling labels, so give siblings distinct labels. `intersect` and
  `fused` are typed `a & b` and `a + b`: build123d's `&` returns `None` for no overlap (`intersect` gives an
  empty Compound, volume 0), and its stubs type `+` as possibly a `Wire`. Use them in place of the operators
  wherever the result's `.volume`, `.solids()`, or `.is_inside` is used, so `ty` passes.
- `schlieren/validation.py`: `require_positive_dimensions`, for a parameter class's `validate`; it names the
  offending field.
- `schlieren/hardware.py`: catalog dimensions of purchased hardware that more than one model uses (the bar
  magnet, the FAS100, the 98625A950 insert, the 2006N292 spring, common M3 hardware). Parameter classes take
  them as defaults and add their own fabrication allowances; hardware used by one model stays with it.
- `post_stack` in `parts/rail_shoe.py`: the post, rail shoe, shoe clamp hardware, and optional SM1RC/M ring
  and side-channel screws that every fixture on a rail shows.
- `parts/adjuster.py`: the FAS100, its brass insert, and its bearing magnet, as the slit head and cutoff
  carriage show them.

Place assembly children with `labeled(shape, label, color, loc)` and `place`, and move large models with
`cad.moved(shape, loc)`, not `loc * shape`: build123d's `Location * shape` deep-copies the whole B-rep, while
these only compose locations. That difference was most of the cost of building the optical head.

Keep part-specific calibration dimensions and experimental compensation values with the relevant part unless
they have clearly become project-wide standards.

### Units

Use millimeters for internal CAD geometry unless there is a strong reason not to.

Preserve inherently imperial interfaces in their conventional form when useful, including:

- screw and thread designations
- sheet thicknesses
- commercial hardware dimensions
- other purchased components specified primarily in inches

Convert deliberately at the model boundary rather than mixing implicit units.

## Module layout

```text
src/schlieren/
    standards.py   # project-wide dimensions
    hardware.py    # catalog dimensions of shared purchased hardware
    palette.py     # viewer colors
    validation.py  # shared parameter-class checks
    bom.py         # BOM schema and row checks, shared by the workbook builder, reconciler, and tests
    cad.py         # primitive solids, axis planes, assembly helpers
    vendor_cad.py  # vendor STEP models placed in documented mounting frames
    render.py      # offscreen figure rendering
    testing.py     # test helpers: @slow, @shared, bounding-box prefilters, svg_attr
    parts/         # one module per mechanical subsystem
    cli/           # command-line entry points, registered in pyproject.toml [project.scripts]
        _common.py # shared options and export/drawing/figure/viewer steps
```

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

Prefer testing engineering invariants rather than implementation details. Do not change a test merely to make
an unintended geometry change pass.

Iterate with `uv run run-tests` and run the tests relevant to a change after modifying CAD or supporting code.
Tests that take more than a few seconds, typically exhaustive pairwise interference or rotation-sweep checks,
are marked `@slow` (`schlieren.testing`) and skipped by default; the skip count is reported. Run
`uv run run-tests --full` before presenting completed work.

Build each model once per test class. Parameters and the model most tests use go in `setUpClass`; every other
model at its default parameters and pose is a `@shared` attribute (`schlieren.testing`), built on first use so
that a model only slow tests need costs the default run nothing. A test builds a model itself only for a
variant (changed parameters or pose) or where the build is what is under test. Shared models must not be
modified. Where every pose of an assembly rebuilds the same pose-independent parts, cache those builders in
the part module (`functools.cache` on the frozen parameter class, as `parts/carriage.py` does) rather than
working around the cost in the tests.

For new pairwise checks, use the bounding-box prefilters in `schlieren.testing` (`near_pairs`,
`near_pairs_among`, `boxes_overlap`, `overlap_volume`, `bounded_distance`) before exact boolean or distance
queries. Where a group of parts keeps the same relative placement across a sweep (an engagement, a board),
check the pairs inside the group once, not per step. Exact bounding boxes of vendor models cost tens of
milliseconds each and are not cached; the loose box is much cheaper and only ever larger, so it is safe for a
prefilter. Leave `loose` off where the box test is itself the assertion.

The full run takes well under a minute. If it grows to minutes, suspect per-pair bounding boxes, `loc * shape`
on large models, or an assembly built more than once per module.

## Commands

Dependencies are managed with `uv` (Python >= 3.12). Tests use `unittest`; ruff is run via `uvx`; `ty`
(Astral's type checker, a dev dependency) is run via `uv run`.

```sh
uv sync                                               # install/update the environment
uv run run-tests                                      # fast tests, one process per module in parallel
uv run run-tests --full                               # adds the slow interference/sweep tests
uv run run-tests test_carriage                        # chosen modules only
uv run python -m unittest tests.test_carriage -v      # one module, serial (SCHLIEREN_TESTS=full: slow)
uvx ruff check . && uvx ruff format .                 # lint/format (rules, line length 110: pyproject.toml)
uv run ty check                                       # type check (also the editor's language server)
uv run <command> --help                               # part commands: build/export (--show opens the viewer)
uv run rail-shoe --figure                             # re-render docs/design/figures/rail-shoe.png
uv run build-design-doc [--pdf]                       # docs/design/ -> exports/docs/, docs/*.pdf
uv run build-bom-xlsx                                 # bom/bom.csv -> bom/schlieren-bom.xlsx
uv run reconcile-bom [workbook.xlsx] [--apply]        # workbook edits -> differences from bom/bom.csv
```

Commands live in `src/schlieren/cli/` and are registered in `pyproject.toml` `[project.scripts]`; run them
with `uv run <command>` from the repo root. Output paths such as `--output` default to `exports/` relative to
the current directory. To add a command: write `cli/<name>.py` with `main()` and register it in
`[project.scripts]`. Build the options and the export, drawing, figure, and viewer steps from `cli/_common.py`
(`add_output_option`, `add_show_option`, `add_figure_option`, `export_models`, `write_text`, `render`,
`show`); keep geometry, such as a print layout, in the part module so it can be tested.

To rebuild derived artifacts, prefer the `Makefile`, which runs the commands above for whatever is out of date
(design-doc figures, the consolidated design document and PDF, the BOM workbook) and nothing else: `make` (or
`make figures`, `doc`, `pdf`, `bom`; `make -n` previews; `make test` runs the full suite). `make` with no
target includes the PDF, which needs Chrome and network access. Its dependencies are declared by hand: when a
part module gains an import, or a new figure or `--figure` output is added, update the matching rule in the
`Makefile`; the shared modules (`cad.py`, `standards.py`, `palette.py`, `hardware.py`, `vendor_cad.py`,
`render.py`, `cli/_common.py`) are in its `CORE` list. Do not use `make -t`; it marks stale targets current
without rebuilding them.

The editor settings in `.vscode/` use the `ty` extension as language server and type checker in place of
Pylance, a 110-column ruler, and ruff format on save. build123d's type stubs are imprecise (a boolean operator
on a `Part` is typed `Part` but returns a `Compound`, and several accessors are typed `Optional`), so many
diagnostics come from the stubs rather than the code. Where a suppression is warranted, use
`# ty: ignore[rule]` with the rule name. In tests, `schlieren.testing.svg_attr` reads an SVG attribute that
must be present (ElementTree's `get` is typed `str | None`).

A `.claude/` PostToolUse hook auto-formats edited `.py` files with ruff, and a PreToolUse hook blocks direct
edits to `exports/`. Project skill: `/reconcile-bom` (review and apply edits made in a copy of the BOM
workbook).

## Working with the BOM

Each BOM row is a distinct project allocation. Do not merge rows solely because Vendor + SKU are identical;
procurement rollups may aggregate them, but allocation rows stay distinct when they serve different
subsystems.

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

## Engineering reasoning

Distinguish clearly between measured values, manufacturer specifications, committed project dimensions,
calculated values, fabrication allowances, and provisional estimates. Do not silently replace a measured value
with a nominal catalog value.

When calculations depend materially on current project dimensions, read the relevant `docs/design/`
fragment(s) first.

## Change scope

Make the smallest coherent change that satisfies the task, and prefer small, reviewable diffs.

Do not opportunistically redesign unrelated subsystems.

Do not alter established interfaces, dimensions, dependencies, or procurement decisions merely to simplify
code.

If a requested change exposes a likely conflict elsewhere, identify the conflict before silently changing the
other subsystem.

## Git behavior

Do not commit, push, force-push, rebase shared history, delete branches, create releases, or change remote
repository settings unless the user explicitly asks. Working-tree edits and tests are permitted when required
by the task.

Keep generated transient files, viewer artifacts, caches, and local environments out of version control.

## Agent workflow

At the beginning of a substantial task:

1. determine whether the task depends on current design state, BOM state, or both;
2. read the applicable `docs/design/` fragment(s) and/or `bom/bom.csv`;
3. inspect the relevant repository CAD/source files.

Then make the requested change and run appropriate verification. Update `docs/design/` and `bom/bom.csv` only
when the user has finalized a decision, following "Design decisions and canonical updates".

Before presenting completed work:

- inspect the diff and remove accidental or unrelated changes;
- run the full test suite (`uv run run-tests --full`);
- report important assumptions or unresolved issues.

The objective is to keep CAD, implementation, design state, and procurement state synchronized without
treating exploratory work as finalized engineering.

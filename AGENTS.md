# iPhone schlieren — Agent Instructions

This repository contains the code, CAD source, tests, tooling, and other version-controlled engineering
artifacts for the iPhone schlieren Deep Creek vacation project.

Do not assume that repository history, chat history, generated files, or remembered context represents the
current physical design. Read the relevant repository resources (`docs/status/`, `bom/bom.csv`) before substantive work.

## Sources of truth

Git is authoritative for the design baseline and the BOM. Google Drive holds generated views for sharing and
GUI editing only.

Use the following priority order:

1. Explicit instructions from the user in the current session.
2. This `AGENTS.md`.
3. Current repository contents (including `bom/` and `docs/status/`).
4. Git history, old chats, summaries, and other historical material.

If two sources conflict, prefer the higher-priority source.

Do not resurrect superseded or rejected designs merely because they appear in Git history, comments, old
files, or conversation history.

### Design status: `docs/status/`

Per-subsystem Markdown fragments, named `NN-*.md`; filename order is document order. Authoritative for:

- current design baseline, dimensions and geometry
- architecture, mechanical and optical concepts
- committed design decisions and rationale
- unresolved design work and overall project state

Read only the fragment(s) relevant to the task (section numbers match the BOM `Source section` column), plus
`13-status-and-procurement.md` for cross-cutting status. Do not read the whole set unless the task needs it.

`uv run build-status-doc` concatenates the fragments into `exports/docs/schlieren-project-status.md`
(generated; never edit it).

### BOM and procurement: `bom/bom.csv`

Single CSV, one row per BOM line item. Authoritative for BOM contents, quantities, subsystem allocations,
vendors, SKUs, procurement status, inventory state, and purchasing notes.

`uv run build-bom-xlsx` builds `exports/bom/schlieren-bom.xlsx` (BOM tab, Summary formulas, procurement-state
conditional formatting) from the CSV; import that into Drive for the Sheets view.

Read `bom/bom.csv` before answering or acting on procurement, BOM, inventory, vendor, quantity, or purchasing
questions.

### Reference drawings: `docs/reference/`

Vendor drawings and datasheets for purchased parts, named `<Brand>-<part>.pdf` (see the README there).
Consult them for catalog dimensions. They are manufacturer specifications, not measured values or committed
project dimensions; a measurement recorded in `docs/status/` takes precedence.

### Google Drive copies

The Google Doc "schlieren-project-status" and Sheet "schlieren-bom" (Projects/iPhone schlieren/) are working
copies. Edits made there are not authoritative until reconciled into Git by diffing against the current
`bom.csv` or fragment, never by blind overwrite. Archive snapshots are historical only.

Agent access to Drive goes through the fritzm-agents isolation model: read-only pulls are fine; writes to
Drive require explicit user confirmation each time. Do not assume any particular auth method is set up.

## Repository authority

This Git repository is authoritative for version-controlled engineering artifacts, including:

- CadQuery source, Python source, tests, CAD/build utilities
- the design-status fragments and `bom/bom.csv`
- repository configuration and agent instructions
- deliberately versioned generated outputs, if any

Generated files (`exports/`, the consolidated status document, the .xlsx) are derived artifacts.

## Design decisions and canonical updates

Discussion, experiments, CAD changes, and proposed ideas are provisional until the user accepts them as final.

Do not silently promote a proposal into the project baseline.

When the user finalizes a design decision:

1. update the applicable CAD/source/tests in this repository;
2. update the applicable `docs/status/` fragment(s);
3. if the decision changes procurement, quantity, allocation, vendor choice, or BOM structure, also update
   `bom/bom.csv`;
4. verify that the affected files agree.

A procurement-only change normally updates `bom/bom.csv` without changing the status fragments unless it
materially changes the engineering baseline.

A CAD experiment or exploratory branch should not update the status fragments or BOM unless the user
explicitly accepts the result.

## CAD conventions

CadQuery source is the authoritative representation of programmatically generated mechanical geometry.

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
    standards.py
    parts/
        ...
    cli/
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

Put genuinely project-wide dimensional standards in `schlieren/standards.py`.

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

Do not change a test merely to make an unintended geometry change pass.

## Commands

Dependencies are managed with `uv` (Python >= 3.12). Tests use `unittest`; ruff is run via `uvx`.

```sh
uv sync                                               # install/update the environment
uv run python -m unittest discover -s tests -v        # all tests
uv run python -m unittest tests.test_carriage_2 -v    # one test module
uvx ruff check . && uvx ruff format .                 # lint/format (line length 110, from pyproject.toml)
uv run <command> --help                               # part commands: build/export (--show opens the viewer)
uv run build-status-doc                               # docs/status/ -> exports/docs/schlieren-project-status.md
uv run build-bom-xlsx                                 # bom/bom.csv -> exports/bom/schlieren-bom.xlsx
```

Commands live in `src/schlieren/cli/` and are registered in `pyproject.toml` `[project.scripts]`; run them with
`uv run <command>` from the repo root. Output paths such as `--output` default to `exports/` relative to the
current directory. To add a command: write `cli/<name>.py` with `main()` and register it in
`[project.scripts]`.

A `.claude/` PostToolUse hook auto-formats edited `.py` files with ruff, and a PreToolUse hook blocks direct
edits to `exports/`. Project skills: `/finalize-decision` (propagate an accepted decision) and `/sync-drive`
(diff-based Drive reconciliation).

## Working with the BOM

Treat each BOM row as a distinct project allocation where `bom/bom.csv` does so.

Do not merge rows solely because Vendor + SKU are identical.

Procurement rollups may aggregate identical Vendor + SKU combinations, but
allocation rows should remain distinct when they serve different subsystems.

Do not guess:

- procurement state
- quantity
- vendor
- SKU
- package size
- arrival state

If a required value is unresolved, preserve that uncertainty rather than inventing a value.

## Working with the design-status document

Keep the status document focused on current engineering state and relevant rationale.

When updating it:

- preserve established terminology;
- distinguish committed design from unresolved work;
- remove or clearly supersede obsolete statements when a decision changes;
- retain useful rationale where it explains a non-obvious current decision;
- avoid duplicating detailed BOM data that belongs in `bom/bom.csv`.

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

When calculations depend materially on current project dimensions, read the relevant `docs/status/`
fragment(s) first.

When a required dimension remains unresolved, expose it as a parameter or clearly mark it as provisional
rather than burying an assumption in geometry.

## Agent workflow

At the beginning of a substantial task:

1. read this `AGENTS.md`;
2. determine whether the task depends on current design state, BOM state, or both;
3. read the applicable `docs/status/` fragment(s) and/or `bom/bom.csv`;
4. inspect the relevant repository CAD/source files;
5. make the requested change;
6. run appropriate verification;
7. update `docs/status/` and `bom/bom.csv` only when the user has finalized a decision and the rules above
   require it; push to Drive only with explicit confirmation.

The objective is to keep CAD, implementation, design state, and procurement state synchronized without
treating exploratory work as finalized engineering.

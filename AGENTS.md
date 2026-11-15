# iPhone schlieren — Agent Instructions

Repo: code, CAD source, tests, tooling and engineering artifacts for the iPhone schlieren Deep Creek project.

Repo history, chat history, generated files and remembered context (including agent memory) never override
the repository. Before substantive work, read the relevant `docs/design/` fragment(s) and/or `bom/bom.csv`.

## Reference docs (read when the task touches them)

- `docs/agents/cad.md`: writing or changing CAD/part code
- `docs/agents/testing.md`: writing or restructuring tests
- `docs/agents/tooling.md`: CLI commands, Makefile, editor/type checker, hooks
- `docs/agents/design-doc-style.md`: editing `docs/design/`

## Sources of truth

Git is authoritative for version-controlled artifacts: build123d/Python source, tests, CAD/build utilities,
design fragments, `bom/bom.csv`, repo configuration, agent instructions.

Priority, higher wins on conflict:

1. Explicit user instructions in the current session
2. This `AGENTS.md`
3. Current repository contents (including `bom/`, `docs/design/`)
4. Git history, old chats, summaries, other historical material

Never resurrect superseded or rejected designs from history, comments, old files or conversation, and never
turn historical alternatives into current requirements.

### Derived artifacts

Never hand-edit a generated file and treat it as the new source.

- `exports/` (STEP, STL, drawings, consolidated design doc): not versioned
- `docs/schlieren-design.pdf`, `bom/schlieren-bom.xlsx`: versioned beside their sources for sharing
- `docs/design/figures/`: versioned so fragments display without a build
- STEP/STL/3MF/DXF and similar are derived unless documented otherwise; build123d source is authoritative
  for generated geometry.

### Design description: `docs/design/`

Per-subsystem fragments `NN-*.md` (filename order = document order). Authoritative for: design baseline,
dimensions and geometry; architecture and mechanical/optical concepts; decisions and rationale; provisional
areas and next steps.

Described design is baseline unless marked **Provisional**; `11-open-work.md` rolls up provisional areas.
Read only the fragment(s) the task needs (section numbers match the BOM `Source section` column) plus
`11-open-work.md` for cross-cutting work; not the whole set unless required.

`uv run build-design-doc` builds `exports/docs/schlieren-design.md` (generated; never edit). Rebuild
`docs/schlieren-design.pdf` (`--pdf`; needs Chrome and network) when fragments or figures change, not
needlessly (not byte-reproducible). Regenerate a figure when its part's geometry changes.

### BOM and procurement: `bom/bom.csv`

One row per BOM line item. Authoritative for contents, quantities, subsystem allocations, vendors, SKUs,
procurement status, inventory, purchasing notes, and CAD state of printed parts (`CAD ready` / `CAD open`).
Design fragments do not track procurement or CAD state. Read it before answering or acting on procurement,
BOM, inventory, vendor, quantity or purchasing questions.

`uv run build-bom-xlsx` builds `bom/schlieren-bom.xlsx` from the CSV; it must match (a test checks), so
rebuild whenever `bom.csv` changes. Workbook edits are not authoritative until reconciled with
`uv run reconcile-bom`; review its report with the user before `--apply`; never overwrite the CSV blindly.

### Reference drawings: `docs/reference/`

Vendor drawings/datasheets, `<Brand>-<part>.pdf` (see README there). Use for catalog dimensions. They are
manufacturer specs, not measured or committed dimensions; a measurement in `docs/design/` takes precedence.

## Design decisions and canonical updates

Discussion, experiments, CAD changes and proposals are provisional until the user accepts them as final.
Exploratory work must not update fragments or BOM without explicit acceptance; never silently promote a
proposal to baseline.

When the user finalizes a decision:

1. update the affected CAD/source/tests
2. update the affected `docs/design/` fragment(s)
3. if procurement, quantity, allocation, vendor or BOM structure changes, update `bom/bom.csv`
4. rebuild dependent derived artifacts (PDF, workbook, figures)
5. verify affected files agree

Procurement-only change: update `bom/bom.csv` only, unless it materially changes the engineering baseline.

## CAD

Named parameters, millimeters internally, reuse shared modules (`standards.py`, `palette.py`, `cad.py`,
`hardware.py`, `validation.py`) instead of redefining. Read `docs/agents/cad.md` before CAD work.

## Tests

Test engineering invariants (bounding dimensions, bores, spacing, counts, clearances), not implementation
details; never edit a test just to pass an unintended geometry change. Iterate with `uv run run-tests`;
run `uv run run-tests --full` before presenting work. Read `docs/agents/testing.md` before writing or
restructuring tests.

## Commands

`uv` (Python >= 3.12); tests use `unittest`; ruff via `uvx`; `ty` via `uv run`.

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

Rebuild derived artifacts with `make` (only what is stale; `make -n` previews; `make test` = full suite;
never `make -t`). Read `docs/agents/tooling.md` before adding a CLI command or editing the `Makefile`,
editor or type-checker settings. Hooks: ruff auto-formats edited `.py` files; direct edits to `exports/`
are blocked.

## BOM rules

- Each row is a distinct allocation; never merge rows just because Vendor + SKU match (rollups may
  aggregate).
- Quote any `bom.csv` field containing a comma; an unquoted comma breaks `test_bom`. Edit as text or via the
  `csv` module, then rebuild the workbook.
- Never guess procurement state, quantity, vendor, SKU, package size or arrival state; preserve
  unresolved uncertainty.

## Design document

Describe the design as it stands, with rationale; not status or history. On a changed decision rewrite the
text (no "previously"/"no longer"), mark open areas **Provisional** and keep the §11 rollup in step; leave
procurement and CAD state to `bom/bom.csv`. Read `docs/agents/design-doc-style.md` before editing
`docs/design/`.

## Engineering reasoning

Distinguish measured values, manufacturer specs, committed project dimensions, calculated values,
fabrication allowances and provisional estimates. Never silently replace a measured value with a catalog
nominal. When calculations depend on project dimensions, read the relevant `docs/design/` fragment(s) first.

## Change scope

- Smallest coherent change; small reviewable diffs.
- No opportunistic redesign of unrelated subsystems.
- Don't alter established interfaces, dimensions, dependencies or procurement decisions just to simplify code.
- If a change exposes a likely conflict elsewhere, report it before changing the other subsystem.

## Git

No commit, push, force-push, shared-history rebase, branch deletion, release creation or remote-settings
change unless explicitly asked. Working-tree edits and tests are allowed. Keep transient files, viewer
artifacts, caches and local environments out of version control.

## Workflow

Start of a substantial task: decide whether it depends on design state, BOM state or both; read the
applicable `docs/design/` fragment(s) and/or `bom/bom.csv`; inspect the relevant CAD/source files. Then
change and verify. Update `docs/design/` and `bom/bom.csv` only for finalized decisions (see "Design
decisions and canonical updates").

Before presenting work: inspect the diff and remove unrelated changes; run `uv run run-tests --full`;
report assumptions and unresolved issues.

Goal: keep CAD, implementation, design state and procurement state synchronized without treating
exploratory work as final.

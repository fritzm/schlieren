# iPhone schlieren — Agent Instructions

This repository contains the code, CAD source, tests, tooling, and other version-controlled engineering
artifacts for the iPhone schlieren Deep Creek vacation project.

Do not assume that repository history, chat history, generated files, or remembered context represents the
current physical design. Refresh the canonical project resources before substantive work.

## Sources of truth

Use the following priority order:

1. Canonical Google project documents listed below.
2. Explicit instructions from the user in the current session.
3. This `AGENTS.md`.
4. Current repository contents.
5. Git history, old chats, summaries, and other historical material.

If two sources conflict, prefer the higher-priority source.

Do not resurrect superseded or rejected designs merely because they appear in Git history, comments, old
files, or conversation history.

### Canonical design status

Google Doc:

https://docs.google.com/document/d/1pFYl58nMYCAaxzBPyxJBD6QY75xB9eNgAhpdqoRZ6-w/edit

Authoritative for:

- current design baseline
- dimensions and geometry
- architecture
- mechanical and optical concepts
- committed design decisions
- unresolved design work
- design rationale
- current overall project state

Before substantive reasoning about the current design, implementation, geometry, or next engineering steps,
read the current version of this document.

### Canonical BOM and procurement state

Google Sheet:

https://docs.google.com/spreadsheets/d/1cwbehmBOSIZI5HtxocAUK4Oh5EyEN-WdBA2T05snkiM/edit

Authoritative for:

- BOM contents
- quantities
- subsystem allocations
- vendors
- SKUs and part numbers
- procurement status
- inventory state
- purchasing notes

Before answering or acting on procurement, BOM, inventory, vendor, quantity, or purchasing questions, read the
current Sheet.

If a task materially depends on both design and procurement state, refresh both canonical resources first.

If Google Drive access is unavailable, do not silently substitute an old local snapshot or remembered value.
State that the canonical resource could not be refreshed and avoid treating potentially stale information as
current.

## Repository authority

This Git repository is authoritative for version-controlled engineering artifacts, including:

- CadQuery source
- Python source
- tests
- CAD/build utilities
- repository configuration
- agent instructions
- deliberately versioned generated outputs, if any

The Google design-status Doc and BOM Sheet remain authoritative for project state even when corresponding
information appears elsewhere in the repository.

Do not create competing canonical copies of the design-status document or BOM inside Git unless the user
explicitly changes the project workflow.

## Design decisions and canonical updates

Discussion, experiments, CAD changes, and proposed ideas are provisional until the user accepts them as final.

Do not silently promote a proposal into the project baseline.

When the user finalizes a design decision:

1. update the applicable CAD/source/tests in this repository;
2. update the canonical Google design-status Doc;
3. if the decision changes procurement, quantity, allocation, vendor choice, or BOM structure, also update the
   canonical Google BOM Sheet;
4. verify that all affected canonical sources agree.

A procurement-only change normally updates the BOM Sheet without changing the design-status document unless it
materially changes the engineering baseline.

A CAD experiment or exploratory branch should not update the canonical Google documents unless the user
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
schlieren/
    __init__.py
    standards.py
    parts/
        ...

tests/
    ...

exports/
    step/
    stl/

scripts/
    ...

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

## Working with the BOM

Treat each BOM row as a distinct project allocation where the canonical Sheet does so.

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
- avoid duplicating detailed BOM data that belongs in the Sheet.

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

When calculations depend materially on current project dimensions, refresh the canonical design-status
document first.

When a required dimension remains unresolved, expose it as a parameter or clearly mark it as provisional
rather than burying an assumption in geometry.

## Agent workflow

At the beginning of a substantial task:

1. read this `AGENTS.md`;
2. determine whether the task depends on current design state, BOM state, or both;
3. refresh the applicable canonical Google resource(s);
4. inspect the relevant repository files;
5. make the requested change;
6. run appropriate verification;
7. update canonical Google resources only when the user has finalized a decision and the rules above require
   it.

The objective is to keep CAD, implementation, design state, and procurement state synchronized without
treating exploratory work as finalized engineering.

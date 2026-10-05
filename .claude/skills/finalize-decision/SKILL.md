---
name: finalize-decision
description: Propagate a design decision the user has explicitly finalized into CAD/source, tests, docs/design fragments, and bom/bom.csv, then verify they agree. Use only after the user says a decision is final.
disable-model-invocation: true
---

Follow the "Design decisions and canonical updates" rules in AGENTS.md. The decision to finalize: $ARGUMENTS

1. Confirm with the user which result is being accepted if it is not unambiguous. Exploratory CAD is not final.
2. Update the build123d source under `src/schlieren/parts/` and its `src/schlieren/cli/` command (registered in `[project.scripts]`); update or add tests in `tests/` for the affected invariants. Do not edit a test merely to make a change pass.
3. Update the matching `docs/design/NN-*.md` fragment(s): rewrite obsolete statements to describe the new design (no change history), keep rationale for non-obvious choices, and remove or add **Provisional** markers as appropriate. Keep the rollup in `11-open-work.md` in step.
4. If quantity, allocation, vendor, SKU, or BOM structure changes, update `bom/bom.csv` (one row per allocation; never guess state, quantity, vendor, SKU, or package size).
5. Verify: `uv run python -m unittest discover -s tests -v`, then `uv run build-design-doc --pdf` and `uv run build-bom-xlsx` to refresh the versioned `docs/schlieren-design.pdf` and `bom/schlieren-bom.xlsx`.
6. Inspect `git diff`, remove unrelated changes, and report assumptions and unresolved issues. Do not commit.

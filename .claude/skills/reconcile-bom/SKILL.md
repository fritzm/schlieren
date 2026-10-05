---
name: reconcile-bom
description: Reconcile edits made in a local copy of the BOM workbook (.xlsx) into bom/bom.csv by reviewing a row-by-row diff, never by blind overwrite, then regenerate the versioned workbook.
disable-model-invocation: true
---

`bom/bom.csv` is authoritative; `bom/schlieren-bom.xlsx` is a generated view. Workbook to reconcile (default `bom/schlieren-bom.xlsx`): $ARGUMENTS

1. Report the differences: `uv run reconcile-bom [workbook.xlsx]`. It matches rows by ID and lists rows added, removed, and changed field by field. It writes nothing.
2. Present the differences to the user as edits made in the workbook. Check them against the BOM rules in AGENTS.md (one row per allocation; no guessed state, quantity, vendor, SKU, or package size) and point out anything that looks accidental, such as a changed ID, a reordered table, or a value a spreadsheet program reformatted.
3. If the user accepts all of them, apply with `uv run reconcile-bom [workbook.xlsx] --apply`. If only some, edit the matching `bom/bom.csv` rows by hand instead.
4. Verify: `uv run python -m unittest tests.test_bom -v`, then `uv run build-bom-xlsx` to regenerate `bom/schlieren-bom.xlsx` from the CSV, and inspect `git diff bom/bom.csv`.
5. If an accepted edit changes the engineering baseline rather than procurement only, say so; the `docs/design/` fragments may need a matching change. Do not commit.

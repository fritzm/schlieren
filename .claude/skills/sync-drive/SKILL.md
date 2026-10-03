---
name: sync-drive
description: Reconcile the Google Drive working copies (schlieren-project-status Doc, schlieren-bom Sheet) with Git by diffing, never by blind overwrite. Read-only pulls are fine; any Drive write needs explicit user confirmation.
disable-model-invocation: true
---

Git is authoritative; Drive copies are generated views. Direction of sync requested: $ARGUMENTS

**Pull (Drive to Git review)**
1. Read the Drive file read-only (Drive connector, Projects/iPhone schlieren/).
2. Regenerate the Git-side view: `uv run build-design-doc` (status) or compare against `bom/bom.csv` (BOM).
3. Diff the two. Present each difference to the user as an edit made in Drive. Do not apply any of them automatically.
4. For differences the user accepts, edit the matching `docs/design/NN-*.md` fragment or `bom/bom.csv` row, then run the tests.

**Push (Git to Drive)**
1. Rebuild: `uv run build-design-doc` and/or `uv run build-bom-xlsx`.
2. Show the user what will be written and to which file. Write to Drive only after explicit confirmation for that specific write.
3. Do not assume any particular auth method is configured; if access fails, report it.

Never treat archive snapshots as current.

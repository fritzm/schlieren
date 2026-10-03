---
name: sync-drive
description: Keep the Google Drive views in step with Git. Build the read-only design-document PDF for upload, and reconcile the schlieren-bom Sheet working copy by diffing, never by blind overwrite. Read-only pulls are fine; any Drive write needs explicit user confirmation.
disable-model-invocation: true
---

Git is authoritative; Drive copies are generated views. Direction of sync requested: $ARGUMENTS

**Design document (Git to Drive only)**
1. Rebuild: `uv run build-design-doc --pdf` (needs local Chrome or Chromium, and network access for KaTeX).
2. The user uploads `exports/docs/schlieren-design.pdf` to Projects/iPhone schlieren/, replacing the earlier PDF. It is read-only on Drive; there is nothing to pull back.

**BOM pull (Drive to Git review)**
1. Read the "schlieren-bom" Sheet read-only (Drive connector, Projects/iPhone schlieren/).
2. Diff it against `bom/bom.csv`. Present each difference to the user as an edit made in Drive. Do not apply any of them automatically.
3. For differences the user accepts, edit the matching `bom/bom.csv` row, then run the tests.

**BOM push (Git to Drive)**
1. Rebuild: `uv run build-bom-xlsx`.
2. Show the user what will be written and to which file. Write to Drive only after explicit confirmation for that specific write.
3. Do not assume any particular auth method is configured; if access fails, report it.

Never treat archive snapshots as current.

---
name: prepare-mini-print
description: Prepare a Prusa MINI+ print from a repo part - build the 3MF with embedded settings, slice with the PrusaSlicer CLI until error free, validate the bgcode, and embed a rendered thumbnail so the printer shows a preview. Use when asked to slice, prep, or queue a print.
---

# Prepare a Prusa MINI+ print

Read `docs/agents/printing.md` and follow it: build the 3MF, slice until error free, validate the bgcode,
embed the thumbnail (`uv run make-bgcode prepare ...` does these four; `docs/agents/printing.md` explains each), report. Its "This project" section has the printer,
output folder and profile defaults. Never commit and never start a print.

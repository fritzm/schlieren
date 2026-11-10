# Tooling

## Design document build

`uv run build-design-doc` concatenates the fragments into `exports/docs/schlieren-design.md` (generated;
never edit) and copies `docs/design/figures/` beside it. With `--pdf` it also writes `schlieren-design.html`
there and prints it to `docs/schlieren-design.pdf`. The PDF step needs a local Chrome or Chromium and network
access (KaTeX for formulas). Rebuild the PDF when fragments or figures change, not needlessly: it is not
byte-reproducible.

Figures: PNG renders (`src/schlieren/render.py`) and SVG drawings generated from the CAD by a part command's
`--figure` option. Regenerate one when its part's geometry changes.

## BOM workbook

`uv run build-bom-xlsx` builds `bom/schlieren-bom.xlsx` (BOM tab, Summary formulas, procurement-state
conditional formatting) from the CSV. It must match the CSV (a test checks): rebuild whenever `bom.csv`
changes. The build is reproducible: unchanged CSV gives an unchanged file.

The workbook is a convenient place to edit the BOM in a spreadsheet program, but edits are not authoritative
until reconciled into the CSV. `uv run reconcile-bom [workbook.xlsx]` reports differences row by row;
`--apply` writes them to `bom.csv`. Review the report with the user before applying; never overwrite the CSV
blindly. Project skill `/reconcile-bom` covers reviewing and applying edits made in a copy of the workbook.

## CLI commands

Commands live in `src/schlieren/cli/`, registered in `pyproject.toml` `[project.scripts]`; run with
`uv run <command>` from the repo root. `--output` paths default to `exports/` relative to the current
directory.

To add a command: write `cli/<name>.py` with `main()`, register it in `[project.scripts]`, and build the
options and the export, drawing, figure and viewer steps from `cli/_common.py` (`add_output_option`,
`add_show_option`, `add_figure_option`, `export_models`, `write_text`, `render`, `show`). Keep geometry, such
as a print layout, in the part module so it can be tested.

## Makefile

Prefer `make` for rebuilding derived artifacts: it runs the commands above for whatever is out of date
(design-doc figures, consolidated design document and PDF, BOM workbook) and nothing else.

- Targets: `make` (includes the PDF, which needs Chrome and network), `make figures`, `doc`, `pdf`, `bom`;
  `make -n` previews; `make test` runs the full suite.
- Dependencies are declared by hand. When a part module gains an import, or a new figure or `--figure`
  output is added, update the matching rule in the `Makefile`.
- The shared modules (`cad.py`, `standards.py`, `palette.py`, `hardware.py`, `vendor_cad.py`, `render.py`,
  `cli/_common.py`) are in its `CORE` list.
- Never use `make -t`: it marks stale targets current without rebuilding them.

## Editor and type checking

`.vscode/` settings: the `ty` extension as language server and type checker (instead of Pylance), a
110-column ruler, ruff format on save.

build123d's type stubs are imprecise (a boolean operator on a `Part` is typed `Part` but returns a
`Compound`; several accessors are typed `Optional`), so many diagnostics come from the stubs, not the code.
Where a suppression is warranted, use `# ty: ignore[rule]` with the rule name. In tests,
`schlieren.testing.svg_attr` reads an SVG attribute that must be present (ElementTree's `get` is typed
`str | None`).

## Claude hooks

`.claude/` PostToolUse hook: auto-formats edited `.py` files with ruff. PreToolUse hook: blocks direct edits
to `exports/`.

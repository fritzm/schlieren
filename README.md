# iPhone schlieren

A portable, single-mirror schlieren apparatus that photographs with an iPhone and packs into a checked
suitcase. It is built for a vacation week at Deep Creek and afterward will serve as a bench-top lab instrument.

An LED lights a source slit. A 203 mm, 1600 mm focal-length spherical mirror about 3.2 m away re-images the slit back at the
optical head. Air density gradients near the mirror bend the returning light past a cutoff (knife edge, wire
or color filter), and an iPhone behind a telephoto lens records the resulting contrast. The optical head is a
pair of 2020-extrusion rails on a Baltic-birch pivot plate. Thorlabs SM1 optomechanics hold the condenser,
the slit and the cutoff, and printed ABS parts handle everything that doesn't need metal precision. The
mirror sits in its own tripod-mounted cell.

## Repository layout

| Path | Contents |
|---|---|
| [`docs/design/`](docs/design/) | **The design baseline**: geometry, decisions, rationale and open work, as numbered Markdown fragments (`NN-*.md`, one per subsystem). Start with `01-context-and-layout.md` and `13-status-and-procurement.md`. |
| [`bom/bom.csv`](bom/bom.csv) | **The bill of materials**: one row per allocation, with vendor, SKU, quantity and procurement state. |
| [`src/schlieren/parts/`](src/schlieren/parts/) | CadQuery models of the custom parts and purchased-part stack-ups. See its [README](src/schlieren/parts/README.md) for per-part notes. |
| [`src/schlieren/cli/`](src/schlieren/cli/) | Command-line entry points for building and viewing parts and generating documents. |
| [`src/schlieren/vendor_cad.py`](src/schlieren/vendor_cad.py) | Loads vendor STEP models and places them in project coordinates. |
| [`tests/`](tests/) | `unittest` checks of engineering invariants: dimensions, clearances, interference, optical calculations and BOM consistency. |
| [`cad/vendor/`](cad/vendor/) | Unmodified manufacturer STEP models of purchased parts. |
| [`docs/reference/`](docs/reference/) | Manufacturer drawings and datasheets. |
| `exports/` | Generated STEP/STL files, the consolidated status document and the BOM spreadsheet (ignored by Git). |
| [`AGENTS.md`](AGENTS.md) | Working rules for AI coding agents (and a concise statement of project conventions for humans). |
| [`.claude/`](.claude/) | Claude Code hooks and project skills. |

Git is the source of truth for both the design and the BOM. The Google Drive copies (the
"schlieren-project-status" Doc and the "schlieren-bom" Sheet) are generated views for sharing and GUI editing.
Edits made there are reconciled back into Git by diffing.

## Tools

- [uv](https://docs.astral.sh/uv/) manages Python (3.12+) and dependencies.
- [CadQuery](https://cadquery.readthedocs.io/) generates all custom geometry. The Python source is
  authoritative, and STEP/STL exports are derived files.
- The [OCP CAD Viewer](https://github.com/bernhard-42/vscode-ocp-cad-viewer) VS Code extension displays
  assemblies (`--show`).
- [ruff](https://docs.astral.sh/ruff/) handles lint and formatting (line length 110).
- [Claude Code](https://claude.com/claude-code) does much of the engineering work under the rules in
  `AGENTS.md`.

## Common commands

```sh
uv sync                                          # set up the environment
uv run python -m unittest discover -s tests -v   # run all tests
uvx ruff check . && uvx ruff format .            # lint and format

uv run led-module [--show]                       # LED focus stack-up
uv run slit-head [--show]                        # source-slit flexure head
uv run carriage [--show]                         # cutoff carriage
uv run cassette [--show]                         # cassette blank and clamp bars
uv run rail-shoe [--show]                        # common rail shoe

uv run build-status-doc                          # docs/design/ -> exports/docs/schlieren-project-status.md
uv run build-bom-xlsx                            # bom/bom.csv -> exports/bom/schlieren-bom.xlsx
```

Every part command takes `--help`. The part commands write their STEP/STL files to `exports/`.

## Workflow

1. **Explore.** CAD changes, experiments and proposals are provisional and live only in source and tests.
2. **Finalize.** Once a decision is accepted, it is propagated to the CAD source and tests, the relevant
   `docs/design/` fragment, and `bom/bom.csv` if procurement changes. All of these must agree. In Claude Code,
   the `/finalize-decision` skill does this.
3. **Verify.** Tests guard dimensions and clearances against accidental change. Physical fit checks of printed
   parts feed measured values back into `docs/design/`, where measurements override catalog values.
4. **Share.** `build-status-doc` and `build-bom-xlsx` produce files to import into Drive. The `/sync-drive`
   skill reconciles edits made in Drive back into Git.

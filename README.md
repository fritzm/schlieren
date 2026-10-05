# iPhone schlieren

A portable, single-mirror schlieren apparatus that images with an iPhone and packs into a checked suitcase. It
is built for a vacation week at Deep Creek and afterward will serve as a bench-top lab instrument.

An LED lights a source slit. A spherical mirror a few meters away re-images the slit back at the optical head.
Air density gradients near the mirror bend the returning light past a cutoff (knife edge, wire, or color
filter), and an iPhone behind a telephoto lens records the resulting contrast. The optical head is a pair of
2020-extrusion rails attached to a plywood pivot plate, and is desgined to rest on a tabletop or bench.
Thorlabs SM1 optomechanics hold the LEDs, condenser, the slit, and the cutoff, and printed ABS parts handle
everything that doesn't need metal precision. The mirror sits in its own tripod-mounted cell.

## Repository layout

| Path | Contents |
|---|---|
| [`docs/design/`](docs/design/) | Baseline design, as numbered Markdown fragments, one per subsystem. Start with `01-context-and-layout.md`; open areas are flagged **Provisional** and rolled up in `11-open-work.md`. |
| [`docs/schlieren-design.pdf`](docs/schlieren-design.pdf) | The whole design document rendered as one PDF, generated from the fragments. |
| [`bom/bom.csv`](bom/bom.csv) | BOM: one row per allocation, with vendor, SKU, quantity, and procurement or CAD state. |
| [`bom/schlieren-bom.xlsx`](bom/schlieren-bom.xlsx) | The BOM as a workbook with a summary tab, generated from the CSV. |
| [`src/schlieren/parts/`](src/schlieren/parts/) | build123d models of custom parts and part assemblies. See the additional [README](src/schlieren/parts/README.md) there for per-part notes. |
| [`src/schlieren/cli/`](src/schlieren/cli/) | Utility scripts for building and viewing parts and generating documents. |
| [`tests/`](tests/) | Checks on dimensions, clearances, interference, optical calculations, and BOM consistency. |
| [`cad/vendor/`](cad/vendor/) | Unmodified manufacturer STEP models of purchased parts. |
| [`docs/reference/`](docs/reference/) | Manufacturer drawings and datasheets. |

This git repository is the source of truth for both the design and the BOM. The PDF and the workbook are
generated views: to change them, edit the fragments or the CSV and rebuild.

## Tooling

- [uv](https://docs.astral.sh/uv/) for management of Python environment and dependencies.
- [build123d](https://build123d.readthedocs.io/) for declarative, parametric geometry, including models for
  3d-printed parts. The Python source is authoritative, and STEP/STL exports are derived files.
- [OCP CAD Viewer](https://github.com/bernhard-42/vscode-ocp-cad-viewer) VS Code extension to display
  assemblies in-editor (`--show`).
- [VTK](https://vtk.org/) for offscreen shaded renders of parts, used as design-document figures (`--figure`).
- [ruff](https://docs.astral.sh/ruff/) for lint and formatting.

## Quick start

```sh
uv sync                                          # set up the environment
uv run python -m unittest discover -s tests -v   # run all tests
uvx ruff check . && uvx ruff format .            # lint and format

uv run light-source [--show] [--figure]          # light source focus stack-up
uv run slit-head [--show]                        # source-slit flexure head
uv run carriage [--show]                         # cutoff carriage
uv run cassette [--show]                         # cassette blank and clamp bars
uv run rail-shoe [--show] [--figure]             # common rail shoe

uv run build-design-doc [--pdf]                  # docs/design/ -> exports/docs/, docs/schlieren-design.pdf
uv run build-bom-xlsx                            # bom/bom.csv -> bom/schlieren-bom.xlsx
uv run reconcile-bom [workbook.xlsx] [--apply]   # edits made in a workbook -> bom/bom.csv
```

Every part command takes `--help`. The part commands write their STEP/STL files to `exports/`. `--figure`
re-renders the part's design-document figure in `docs/design/figures/`.

Once a design element is accepted, it is propagated to the CAD source and tests, the relevant `docs/design/`
fragment, and `bom/bom.csv`. All of these must agree. In Claude Code, the `/finalize-decision` skill does
this.

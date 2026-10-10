# Incremental build of the derived artifacts: design-doc figures, the consolidated design document and its
# PDF, and the BOM workbook. `make` rebuilds only what is out of date (by file modification time).
#
#   make            figures + PDF + BOM workbook
#   make figures    design-doc figures only (-j4 renders them in parallel)
#   make doc        exports/docs/schlieren-design.md only (no Chrome or network needed)
#   make pdf        docs/schlieren-design.pdf (also writes the Markdown and HTML under exports/docs/)
#   make bom        bom/schlieren-bom.xlsx
#   make test       full test suite (uv run run-tests --full)
#   make clean      remove exports/ and Python/tool caches (keeps the versioned figures, PDF and workbook)
#   make -n         show what would be rebuilt without doing it
#
# Dependencies are listed by hand: each figure names the part modules it imports (transitively), on top of
# the shared modules below. When a part gains an import, add it to that figure's list. Several figures come
# from one command; the extra outputs depend on the main one and share its recipe.

FIG := docs/design/figures
PARTS := src/schlieren/parts
CLI := src/schlieren/cli
CORE := src/schlieren/cad.py src/schlieren/render.py src/schlieren/vendor_cad.py src/schlieren/standards.py \
    src/schlieren/palette.py

FRAGMENTS := $(sort $(wildcard docs/design/[0-9][0-9]-*.md))
FIGURES := $(addprefix $(FIG)/,\
  rail-shoe.png cassette.png cutoff.png camera-support.png slit-head.png \
  frame.png frame-pivot-plate.svg \
  light-source.png light-source-section.png light-source-holes.svg \
  mirror-cell.png mirror-cell-below.png mirror-cell-adjuster.png mirror-cell-base-plate.svg)

DOC := exports/docs/schlieren-design.md
PDF := docs/schlieren-design.pdf
XLSX := bom/schlieren-bom.xlsx

.PHONY: all figures doc pdf bom test clean
all: figures pdf bom
figures: $(FIGURES)
doc: $(DOC)
pdf: $(PDF)
bom: $(XLSX)

test:
	uv run run-tests --full

# The versioned outputs (figures, PDF, workbook) are kept: the PDF needs Chrome and network to rebuild, and
# `git checkout` restores them. Delete one by hand, or `make -B`, to force a rebuild.
clean:
	rm -rf exports .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -not -path './.venv/*' -prune -exec rm -rf {} +

# --- figures ---------------------------------------------------------------------------------------------
$(FIG)/rail-shoe.png: $(CLI)/rail_shoe.py $(PARTS)/rail_shoe.py $(PARTS)/rail.py $(CORE)
	uv run rail-shoe --figure

$(FIG)/cassette.png: $(CLI)/cassette.py $(PARTS)/cassette.py $(PARTS)/carriage.py $(PARTS)/rail_shoe.py \
    $(PARTS)/rail.py $(CORE)
	uv run cassette --figure

$(FIG)/cutoff.png: $(CLI)/carriage.py $(PARTS)/carriage.py $(PARTS)/cassette.py $(PARTS)/rail_shoe.py \
    $(PARTS)/rail.py $(CORE)
	uv run carriage --figure

$(FIG)/camera-support.png: $(CLI)/camera_support.py $(PARTS)/camera_support.py $(PARTS)/carriage.py \
    $(PARTS)/rail_shoe.py $(PARTS)/rail.py $(CORE)
	uv run camera-support --figure

$(FIG)/slit-head.png: $(CLI)/slit_head.py $(PARTS)/slit_head.py $(PARTS)/rail_shoe.py $(PARTS)/rail.py $(CORE)
	uv run slit-head --figure

$(FIG)/frame.png: $(CLI)/frame.py $(PARTS)/frame.py $(PARTS)/frame_drawing.py $(PARTS)/rail.py $(CORE)
	uv run frame --figure
$(FIG)/frame-pivot-plate.svg: $(FIG)/frame.png ;

$(FIG)/light-source.png: $(CLI)/light_source.py $(wildcard $(PARTS)/light_source*.py) $(PARTS)/rail_shoe.py \
    $(PARTS)/rail.py $(CORE)
	uv run light-source --figure
$(FIG)/light-source-section.png $(FIG)/light-source-holes.svg: $(FIG)/light-source.png ;

$(FIG)/mirror-cell.png: $(CLI)/mirror_cell.py $(PARTS)/mirror_cell.py $(PARTS)/mirror_cell_drawing.py \
    $(PARTS)/frame_drawing.py $(PARTS)/frame.py $(PARTS)/rail.py $(CORE)
	uv run mirror-cell --figure --drawing
$(FIG)/mirror-cell-below.png $(FIG)/mirror-cell-adjuster.png $(FIG)/mirror-cell-base-plate.svg: \
    $(FIG)/mirror-cell.png ;

# --- design document -------------------------------------------------------------------------------------
# The PDF is not reproducible byte for byte, so it is rebuilt only when a fragment or figure is newer.
$(DOC): $(FRAGMENTS) $(FIGURES) $(CLI)/build_design_doc.py
	uv run build-design-doc

$(PDF): $(FRAGMENTS) $(FIGURES) $(CLI)/build_design_doc.py
	uv run build-design-doc --pdf

# --- BOM -------------------------------------------------------------------------------------------------
$(XLSX): bom/bom.csv $(CLI)/build_bom_xlsx.py
	uv run build-bom-xlsx

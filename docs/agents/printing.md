# Print preparation

Method for taking a part from CAD to a sliced, validated file the printer shows a preview of. Never commit,
and never start a print; stop at files in the output folder unless the user asks for more. Project-specific
values (printer, folder, profile) are at the end, under "This project".

`uv run make-bgcode prepare MESH.stl --template T.3mf --output-dir DIR [--up -y]` runs steps 1-4 below and
stops at the first problem; the steps are also commands of their own (`build`, `slice`, `validate`,
`thumbnails`) for iterating on one. `make-bgcode --help` lists the options.

## 1. Build the 3MF

Export the part's mesh from the CAD (the part command's export). The CAD is authoritative; never slice a
hand-edited mesh. Orient for printing as the part's design fragment says (`--up` names the model axis that
points up; do not re-orient to fix a slice).

A bare command-line 3MF has no embedded settings and places items off the bed, so `make-bgcode build`
swaps the mesh into a copy of a GUI-saved 3MF (`--template`): the profile in `Metadata/Slic3r_PE.config` is
carried over untouched, and the part is centered on the template's bed position, resting on the bed.
Overrides (layer height, brim, supports) are edits to the profile lines of the template or its copy, made
only when the user agrees and the part's design fragment calls for them; never guess them. Choose the
template deliberately: whatever it carries, including a per-part override, carries into the new 3MF.

`--add-box X0 Y0 Z0 X1 Y1 Z1` (STL frame, repeatable) adds a box as a separate model part, as the slicer's
Add part > Box does. Use it for a sacrificial feature that exists only to change the slice, kept out of the
CAD and cut off after printing. The usual one is a web across the split of a split ring or clamp: the split
makes the first-layer outline a C, so an outer-only brim also fills the bore. A box about 3 x 1.5 x 0.3 mm
across the split at the ears' outer end, overlapping each ear by about 0.75 mm, closes the outline. Check
the effect in the toolpath (no first-layer brim inside the bore) and tell the user to cut the web off.

The command reports the mesh size and volume, and any edges not shared by exactly two triangles (usually
tessellation cracks; the slicer repairs them, but look at the slice around them).

## 2. Slice until error free

`make-bgcode slice PART.3mf --output-dir DIR` runs the PrusaSlicer command line (`--dont-arrange`; the
slicer names the file itself). Any output line that looks like a warning or error is listed and the command
fails, though the bgcode is still written. Iterate on the 3MF (position, orientation, supports, brim) until
the slice is clean (object off bed, floating regions, empty layers, thin gaps). Do not paper over a warning
by turning a check off; report it if no legitimate settings or placement change resolves it. Re-slice after
every change.

## 3. Validate the gcode

`make-bgcode validate PART.bgcode` (3MF found beside it, or `--model`) checks the decoded bgcode itself; an
ASCII slice (`binary_gcode = 0`) is not toolpath-identical to the binary one, so it does not stand in for it.
It exits non-zero if any check fails. The checks:

- structure: header, block order, every CRC32;
- decode: heatshrink and MeatPack decode, and the toolpath has layers;
- layers: first-layer height and layer step match the profile;
- temperatures: hotend setpoints within the limit (`--max-temperature`, default 240 C for PLA);
- supports: present only if expected (`--supports`);
- volume accounting: the toolpath's extruded volume matches the slicer's own estimate;
- bed: extrusion inside the bed (the start G-code's purge line is reported separately);
- footprint and height: the part's extrusion covers the model's bounding box and top, no further out than
  its outline;
- part volume: extrusion against the model's volume (low ratios are ordinary with sparse infill).

Not checked: travel against clips, fixtures or anything else on the bed; anything about the part's fit.
Report what was checked and any deviation. Do not claim "validated" for checks not run.

## 4. Embed the thumbnail

The command-line slicer writes no thumbnails, so the printer shows no preview. After validating,
`make-bgcode thumbnails PART.bgcode [--preview DIR]` finds the 3MF beside the bgcode (or `--model`), renders
the model as placed on the bed in each size and format of the 3MF's `; thumbnails = ...` line, and replaces
the bgcode's thumbnail blocks (after the printer metadata, before the print metadata). It replaces the file
in place, through a temporary file, and leaves nothing else in the output folder (`--output` writes
elsewhere; `--keep-original` saves `NAME.bgcode.orig` first). It refuses to write unless every block checksum
passes and the G-code blocks are byte-identical. Look at a `--preview` PNG.

Verified on the MINI+: the printer screen shows the embedded preview (baffle, 2026-11-15).
The code is `bgcode.py` (container), `image_codecs.py` (PNG, QOI) and `thumbnail.py` (3MF mesh and render).

## 5. Report

Give the output paths, slice settings used, print time and filament estimate, validation results, and whether
the thumbnail step ran. List assumptions and anything left unresolved.

## This project

- Printer: Prusa MINI+ (profile model `MINIIS`), 180 x 180 mm bed, 0.4 mm nozzle. PLA only (never propose
  ABS/ASA).
- Slicer: `/Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer`.
- Output folder: `~/Desktop/3D prints/schlieren/`. Per part, `<name>.3mf` beside
  `<name>_0.4n_<layer>mm_PLA_MINIIS_<time>.bgcode`. If the folder is missing, ask the user; do not invent one.
- Template 3MF: any recent GUI-saved one there (e.g. `slit_focus_paper_ring.3mf`); bed center is 90,90.
- Profile defaults to keep: `draft_shield = limited`, `skirt_height = 100`, brim 5 mm. The user needs the
  draft shield for blocky PLA prints; change shield, skirt or brim per part only when the user agrees (the
  toe clamps used no brim). Layer height is 0.15 mm or 0.2 mm per part.
- Validation: bed bounds are 0-180 on X and Y; no travel into clips or the purge area; PLA temperatures.
- Thumbnails (profile): `16x16/QOI, 220x124/QOI, 200x240/QOI, 380x285/PNG`.

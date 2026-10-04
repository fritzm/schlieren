"""Build a BOM workbook (.xlsx) from bom/bom.csv.

Produces a BOM tab (pure data, with procurement-state conditional formatting) and a Summary tab whose
rollups are live formulas over the BOM tab. The .xlsx is a generated artifact; bom/bom.csv is authoritative.
Importing the .xlsx into Google Drive yields the Sheets view. No Drive access is used here.

    uv run build-bom-xlsx [-o exports/bom/schlieren-bom.xlsx]
"""

import argparse
import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Font, PatternFill

# src/schlieren/cli/<module>.py -> repo root (valid for the editable install that uv sync creates)
REPO_ROOT = Path(__file__).resolve().parents[3]
BOM_CSV = REPO_ROOT / "bom" / "bom.csv"
DEFAULT_OUTPUT = REPO_ROOT / "exports" / "bom" / "schlieren-bom.xlsx"

NUMERIC_COLUMNS = {"Qty", "Pkg Size"}
STATE_COLUMN = "Procurement state"
SUBSYSTEM_COLUMN = "Subsystem"

# Procurement state -> ARGB fill, in Summary display order.
STATE_FILLS = {
    "In hand": "FFD6EDD6",
    "On order": "FFFFEDB2",
    "To procure": "FFFFD1D1",
    "Specified": None,  # counted in Summary; no fill rule in the source Sheet
    "CAD ready": "FFD1E5FF",
    "CAD open": "FFEAD8FF",
}

SUBSYSTEMS = [
    "Tabletop frame",
    "Optical supports",
    "Light source",
    "Source slit",
    "Carriages",
    "Cassettes",
    "Imager",
    "Mirror cell",
    "Shop supplies",
]

SUMMARY_NOTES_TOP = [
    ("iPhone Schlieren BOM / Procurement Tracker", None),
    (None, None),
    (
        "Canonical workbook",
        "Generated from bom/bom.csv in Git. Edits made here are a working copy until reconciled into the CSV.",
    ),
    ("Design baseline", "docs/design/ fragments in Git (consolidated: schlieren-design)."),
    (
        "Quantity model",
        "Qty is the numeric required/allocated amount for that BOM line; package counts do not belong in Qty.",
    ),
    ("Blank Qty", "Quantity is not yet frozen or the item is an as-required consumable/working-stock line."),
    (
        "Package fields",
        "Package Size is units per Purchase Unit where known. Unknown vendor package sizes are intentionally blank.",
    ),
]
SUMMARY_NOTES_BOTTOM = [
    ("Rollup key", "Use Vendor + SKU for procurement rollups."),
    (
        "Shared parts",
        "Keep separate BOM rows for separate subsystem allocations; roll them up by Vendor+SKU.",
    ),
    (
        "Package math",
        "Vendor/SKU rollups may sum Qty and divide by Package Size where Package Size is known.",
    ),
    (
        "Spare/surplus",
        "Unavoidable package surplus is not added to required Qty; track it in procurement/inventory rollups or notes.",
    ),
    ("Data rule", "Do not insert subsystem header or separator rows inside the BOM table."),
    (None, None),
    ("Specified", "Part defined by the design; vendor, SKU, or quantity still to be confirmed."),
    ("CAD ready", "Printed part with a CadQuery model in src/schlieren/parts/; ready to print and fit-test."),
    ("CAD open", "Printed part whose custom geometry is still to be designed."),
]


def read_bom(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(newline="", encoding="utf-8") as f:
        header, *rows = csv.reader(f)
    return header, rows


def convert(column: str, value: str):
    if column in NUMERIC_COLUMNS and value != "":
        return float(value) if "." in value else int(value)
    return value if value != "" else None


def write_bom_sheet(ws, header: list[str], rows: list[list[str]]) -> None:
    ws.append(header)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in rows:
        ws.append([convert(col, val) for col, val in zip(header, row)])
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    state_col = chr(ord("A") + header.index(STATE_COLUMN))
    state_range = f"{state_col}2:{state_col}{len(rows) + 1}"
    for state, argb in STATE_FILLS.items():
        if argb:
            fill = PatternFill(start_color=argb, end_color=argb, fill_type="solid")
            ws.conditional_formatting.add(
                state_range, CellIsRule(operator="equal", formula=[f'"{state}"'], fill=fill)
            )

    for col, width in zip("ABCDEFGHIJKL", (10, 16, 6, 60, 36, 14, 22, 9, 13, 17, 14, 60)):
        ws.column_dimensions[col].width = width


def write_summary_sheet(ws, header: list[str]) -> None:
    state_col = chr(ord("A") + header.index(STATE_COLUMN))
    subsystem_col = chr(ord("A") + header.index(SUBSYSTEM_COLUMN))

    for label, text in SUMMARY_NOTES_TOP:
        ws.append([label, text])
    ws["A1"].font = Font(bold=True, size=14)
    ws["A8"], ws["B8"] = "Entry count", "=COUNTA(BOM!A2:A1000)"
    ws["A10"], ws["B10"], ws["D10"], ws["E10"] = "Procurement state", "Entries", "Subsystem", "Entries"
    for c in ("A10", "B10", "D10", "E10"):
        ws[c].font = Font(bold=True)

    for i, state in enumerate(STATE_FILLS):
        r = 11 + i
        ws[f"A{r}"] = state
        ws[f"B{r}"] = f'=COUNTIF(BOM!{state_col}:{state_col},"{state}")'
    for i, name in enumerate(SUBSYSTEMS):
        r = 11 + i
        ws[f"D{r}"] = name
        ws[f"E{r}"] = f"=COUNTIF(BOM!{subsystem_col}:{subsystem_col},D{r})"

    for i, (label, text) in enumerate(SUMMARY_NOTES_BOTTOM):
        ws[f"A{21 + i}"], ws[f"B{21 + i}"] = label, text

    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 60
    ws.column_dimensions["D"].width = 18


def build_workbook(bom_csv: Path = BOM_CSV) -> Workbook:
    header, rows = read_bom(bom_csv)
    wb = Workbook()
    summary = wb.active
    summary.title = "Summary"
    write_summary_sheet(summary, header)
    write_bom_sheet(wb.create_sheet("BOM"), header, rows)
    return wb


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    build_workbook().save(args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()

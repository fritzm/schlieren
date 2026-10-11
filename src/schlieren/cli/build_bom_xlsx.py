"""Build a BOM workbook (.xlsx) from bom/bom.csv.

Produces a BOM tab (pure data, with procurement-state conditional formatting) and a Summary tab whose
rollups are live formulas over the BOM tab. The .xlsx is a generated artifact, versioned beside the CSV so it
can be opened or shared straight from the repository; bom/bom.csv is authoritative. Edits made in a copy of
the workbook come back through `uv run reconcile-bom`.

    uv run build-bom-xlsx [-o bom/schlieren-bom.xlsx]
"""

import argparse
import csv
import io
import re
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from schlieren.bom import NUMERIC_COLUMNS, STATE_COLUMN, SUBSYSTEM_COLUMN, SUBSYSTEMS

# src/schlieren/cli/<module>.py -> repo root (valid for the editable install that uv sync creates)
REPO_ROOT = Path(__file__).resolve().parents[3]
BOM_CSV = REPO_ROOT / "bom" / "bom.csv"
DEFAULT_OUTPUT = REPO_ROOT / "bom" / "schlieren-bom.xlsx"
BOM_SHEET = "BOM"
# Fixed timestamps, so that rebuilding from an unchanged CSV reproduces the versioned file byte for byte.
WORKBOOK_TIMESTAMP = datetime(2026, 1, 1, tzinfo=UTC)
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
CORE_PROPERTIES = "docProps/core.xml"

ZOOM_PERCENT = 135

# Procurement state -> ARGB fill, in Summary display order.
STATE_FILLS = {
    "In hand": "FFD6EDD6",
    "On order": "FFFFEDB2",
    "To procure": "FFFFD1D1",
    "Specified": None,  # counted in Summary; no fill rule
    "CAD ready": "FFD1E5FF",
    "CAD open": "FFEAD8FF",
}

SUMMARY_NOTES_TOP = [
    ("iPhone Schlieren BOM / Procurement Tracker", None),
    (None, None),
    (
        "Canonical workbook",
        "Generated from bom/bom.csv in Git. Edits made here count only once reconciled into the CSV (reconcile-bom).",
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
    (
        "CAD ready",
        "Printed part with a build123d model in src/schlieren/parts/; ready to print and fit-test.",
    ),
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
        ws.append([convert(col, val) for col, val in zip(header, row, strict=True)])
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

    picker = DataValidation(
        type="list", formula1='"' + ",".join(STATE_FILLS) + '"', allow_blank=True, showErrorMessage=True
    )
    picker.add(state_range)
    ws.add_data_validation(picker)

    for col, width in zip("ABCDEFGHIJKL", (10, 16, 6, 60, 36, 14, 22, 9, 13, 17, 14, 60), strict=True):
        ws.column_dimensions[col].width = width


def write_summary_sheet(ws, header: list[str]) -> None:
    state_col = chr(ord("A") + header.index(STATE_COLUMN))
    subsystem_col = chr(ord("A") + header.index(SUBSYSTEM_COLUMN))

    for label, text in SUMMARY_NOTES_TOP:
        ws.append([label, text])
    ws["A1"].font = Font(bold=True, size=14)
    ws["A8"], ws["B8"] = "Entry count", "=COUNTA(BOM!A:A)-1"
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
    write_bom_sheet(wb.create_sheet(BOM_SHEET), header, rows)
    for ws in wb.worksheets:
        ws.sheet_view.zoomScale = ZOOM_PERCENT
    return wb


def save_workbook(wb: Workbook, path: Path) -> None:
    """Save with fixed document and archive timestamps (see WORKBOOK_TIMESTAMP)."""
    wb.properties.created = WORKBOOK_TIMESTAMP
    buffer = io.BytesIO()
    wb.save(buffer)
    stamp = f"\\g<1>{WORKBOOK_TIMESTAMP:%Y-%m-%dT%H:%M:%SZ}<".encode()
    with zipfile.ZipFile(buffer) as saved, zipfile.ZipFile(path, "w") as out:
        for member in saved.infolist():
            data = saved.read(member)
            if member.filename == CORE_PROPERTIES:  # openpyxl stamps the save time here
                data = re.sub(rb"(<dcterms:modified[^>]*>)[^<]*<", stamp, data)
            fixed = zipfile.ZipInfo(member.filename, date_time=ZIP_TIMESTAMP)
            fixed.compress_type = zipfile.ZIP_DEFLATED
            fixed.external_attr = member.external_attr
            out.writestr(fixed, data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    save_workbook(build_workbook(), args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()

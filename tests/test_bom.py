"""BOM CSV integrity and generated-workbook invariants."""

import csv
import re
import tempfile
import unittest
from pathlib import Path

from schlieren.cli import build_bom_xlsx, reconcile_bom

REPO_ROOT = Path(__file__).resolve().parent.parent
HEADER = [
    "ID",
    "Subsystem",
    "Qty",
    "Item",
    "Purpose",
    "Vendor",
    "SKU",
    "Pkg Size",
    "Purchase Unit",
    "Procurement state",
    "Source section",
    "Notes",
]
STATES = {"In hand", "On order", "To procure", "Specified", "CAD ready", "CAD open"}


class BomCsvTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (REPO_ROOT / "bom" / "bom.csv").open(newline="", encoding="utf-8") as f:
            cls.header, *cls.rows = csv.reader(f)

    def test_columns(self):
        self.assertEqual(self.header, HEADER)

    def test_rows_are_rectangular(self):
        self.assertTrue(all(len(r) == len(HEADER) for r in self.rows))

    def test_ids_unique(self):
        ids = [r[0] for r in self.rows]
        self.assertEqual(len(ids), len(set(ids)))

    def test_procurement_states_valid(self):
        self.assertLessEqual({r[9] for r in self.rows}, STATES)

    def test_one_id_prefix_per_subsystem(self):
        prefixes = {}
        for r in self.rows:
            prefixes.setdefault(r[1], set()).add(r[0].split("-")[0])
        self.assertTrue(all(len(p) == 1 for p in prefixes.values()), prefixes)

    def test_subsystems_match_summary_labels(self):
        script = build_bom_xlsx
        self.assertLessEqual({r[1] for r in self.rows}, set(script.SUBSYSTEMS))

    def test_csv_is_in_canonical_form(self):
        # reconcile-bom --apply rewrites the whole file; canonical quoting keeps that diff to the edited rows.
        path = REPO_ROOT / "bom" / "bom.csv"
        with tempfile.TemporaryDirectory() as tmp:
            rewritten = Path(tmp) / "bom.csv"
            reconcile_bom.write_bom(rewritten, self.header, self.rows)
            self.assertEqual(rewritten.read_bytes(), path.read_bytes())


class BomSectionReferenceTests(unittest.TestCase):
    """Every BOM 'Source section' must point at a heading that exists in docs/design/."""

    def test_source_sections_exist_in_status_fragments(self):
        headings = set()
        for fragment in (REPO_ROOT / "docs" / "design").glob("[0-9][0-9]-*.md"):
            for line in fragment.read_text(encoding="utf-8").splitlines():
                m = re.match(r"#{2,6}\s+(\d+(?:\.\d+)*)\b", line)
                if m:
                    headings.add(m.group(1))
        with (REPO_ROOT / "bom" / "bom.csv").open(newline="", encoding="utf-8") as f:
            _, *rows = csv.reader(f)
        missing = {}
        for row in rows:
            for ref in re.findall(r"\d+(?:\.\d+)*", row[10]):
                if ref not in headings:
                    missing.setdefault(ref, []).append(row[0])
        self.assertFalse(missing, f"BOM Source section not found in docs/design headings: {missing}")


class BomWorkbookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wb = build_bom_xlsx.build_workbook()

    def test_sheets(self):
        self.assertEqual(self.wb.sheetnames, ["Summary", "BOM"])

    def test_bom_tab_is_pure_data(self):
        for row in self.wb["BOM"].iter_rows():
            for cell in row:
                self.assertFalse(isinstance(cell.value, str) and cell.value.startswith("="))

    def test_summary_formulas_reference_bom(self):
        ws = self.wb["Summary"]
        formulas = [
            c.value
            for row in ws.iter_rows()
            for c in row
            if isinstance(c.value, str) and c.value.startswith("=")
        ]
        self.assertEqual(len(formulas), 1 + 6 + 9)
        self.assertTrue(all("BOM!" in f for f in formulas))
        self.assertEqual(ws["B8"].value, "=COUNTA(BOM!A2:A1000)")

    def test_conditional_formatting_covers_bom_rows(self):
        cf = self.wb["BOM"].conditional_formatting
        ranges = {str(r.sqref) for r in cf}
        with (REPO_ROOT / "bom" / "bom.csv").open(newline="", encoding="utf-8") as f:
            n_rows = sum(1 for _ in csv.reader(f)) - 1
        self.assertEqual(ranges, {f"J2:J{n_rows + 1}"})
        self.assertEqual(sum(len(r.rules) for r in cf), 5)

    def test_save_is_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "a.xlsx", Path(tmp) / "b.xlsx"
            build_bom_xlsx.save_workbook(self.wb, first)
            build_bom_xlsx.save_workbook(build_bom_xlsx.build_workbook(), second)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_versioned_workbook_matches_csv(self):
        """bom/schlieren-bom.xlsx is generated; rebuild it (uv run build-bom-xlsx) whenever bom.csv changes."""
        header, rows = build_bom_xlsx.read_bom(build_bom_xlsx.BOM_CSV)
        workbook_header, workbook_rows = reconcile_bom.read_workbook_bom(build_bom_xlsx.DEFAULT_OUTPUT)
        self.assertEqual(workbook_header, header)
        diff = reconcile_bom.diff_bom(header, rows, workbook_rows)
        self.assertFalse(diff, reconcile_bom.report(diff, header))


class ReconcileBomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.header, cls.rows = build_bom_xlsx.read_bom(build_bom_xlsx.BOM_CSV)

    def edited_workbook_rows(self, edit):
        """Rows read back from a workbook built from the CSV and then edited on its BOM tab."""
        wb = build_bom_xlsx.build_workbook()
        edit(wb[build_bom_xlsx.BOM_SHEET])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "edited.xlsx"
            wb.save(path)
            header, rows = reconcile_bom.read_workbook_bom(path)
        self.assertEqual(header, self.header)
        return rows

    def test_unedited_workbook_round_trips(self):
        rows = self.edited_workbook_rows(lambda _ws: None)
        self.assertEqual(rows, self.rows)
        self.assertFalse(reconcile_bom.diff_bom(self.header, self.rows, rows))

    def test_reports_changed_added_and_removed_rows(self):
        state = self.header.index("Procurement state")
        qty = self.header.index("Qty")
        first, second = self.rows[0], self.rows[1]
        new_row = [
            "TST-001",
            first[1],
            2.0,
            "Test item",
            None,
            None,
            None,
            None,
            None,
            "Specified",
            None,
            None,
        ]

        def edit(ws):
            ws.cell(row=2, column=state + 1, value="On order")
            ws.cell(row=2, column=qty + 1, value=7.0)  # Spreadsheet programs save whole numbers as floats.
            ws.delete_rows(3)
            ws.append(new_row)

        diff = reconcile_bom.diff_bom(self.header, self.rows, self.edited_workbook_rows(edit))
        self.assertEqual(
            diff.changed,
            {first[0]: [("Qty", first[qty], "7"), ("Procurement state", first[state], "On order")]},
        )
        self.assertEqual([r[0] for r in diff.removed], [second[0]])
        self.assertEqual([r[:4] for r in diff.added], [["TST-001", first[1], "2", "Test item"]])
        self.assertFalse(diff.reordered)
        self.assertIn(f"Changed {first[0]}", reconcile_bom.report(diff, self.header))

    def test_reports_reordering(self):
        def edit(ws):
            ws.move_range("A2:L2", rows=len(self.rows))  # First data row to below the last.

        diff = reconcile_bom.diff_bom(self.header, self.rows, self.edited_workbook_rows(edit))
        self.assertTrue(diff.reordered)
        self.assertFalse(diff.added or diff.removed or diff.changed)

    def test_rejects_duplicate_ids(self):
        with self.assertRaises(SystemExit):
            reconcile_bom.diff_bom(self.header, self.rows, [*self.rows, self.rows[0]])


if __name__ == "__main__":
    unittest.main()

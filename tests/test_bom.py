"""BOM CSV integrity and generated-workbook invariants."""
import csv
import re
import unittest
from pathlib import Path

from schlieren.cli import build_bom_xlsx

REPO_ROOT = Path(__file__).resolve().parent.parent
HEADER = ["ID", "Subsystem", "Qty", "Item", "Purpose", "Vendor", "SKU", "Pkg Size", "Purchase Unit",
          "Procurement state", "Source section", "Notes"]
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
        formulas = [c.value for row in ws.iter_rows() for c in row
                    if isinstance(c.value, str) and c.value.startswith("=")]
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


if __name__ == "__main__":
    unittest.main()

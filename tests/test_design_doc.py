"""The design fragments' figure links must resolve, in the fragments and in the consolidated document."""

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from schlieren.cli.build_design_doc import FIGURE_DIR, FRAGMENT_DIR, build_design_doc, build_print_html

# Markdown images, and the HTML <img> used where a figure is centered with a caption.
IMAGE_LINK = re.compile(r"""!\[[^\]]*\]\(([^)]+)\)|<img\s[^>]*?src="([^"]+)\"""")


def image_targets(text):
    return [markdown or html for markdown, html in IMAGE_LINK.findall(text)]


class DesignDocTests(unittest.TestCase):
    def test_fragment_figures_exist(self):
        for fragment in sorted(FRAGMENT_DIR.glob("[0-9][0-9]-*.md")):
            for target in image_targets(fragment.read_text(encoding="utf-8")):
                self.assertTrue((FRAGMENT_DIR / target).is_file(), f"{fragment.name}: {target}")

    def test_consolidated_document_figures_resolve(self):
        targets = image_targets(build_design_doc())
        self.assertTrue(targets)
        self.assertTrue(all(target.startswith(f"{FIGURE_DIR.name}/") for target in targets), targets)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "schlieren-design.md"
            subprocess.run(
                [sys.executable, "-m", "schlieren.cli.build_design_doc", "-o", str(output)],
                check=True,
                capture_output=True,
            )
            for target in image_targets(output.read_text(encoding="utf-8")):
                self.assertTrue((output.parent / target).is_file(), target)

    def test_print_html_keeps_figures_tables_and_formulas(self):
        design_doc = build_design_doc()
        html = build_print_html(design_doc, "schlieren-design")
        self.assertEqual(image_targets(html), image_targets(design_doc))
        self.assertIn("<table>", html)
        self.assertEqual(html.count("$$"), design_doc.count("$$") + 2)  # Plus the KaTeX delimiter setup.

    def test_print_html_section_links_resolve(self):
        html = build_print_html(build_design_doc(), "schlieren-design")
        anchors = set(re.findall(r'id="([^"]+)"', html))
        links = set(re.findall(r'href="#([^"]+)"', html))
        self.assertTrue(links)
        self.assertEqual(links - anchors, set())


if __name__ == "__main__":
    unittest.main()

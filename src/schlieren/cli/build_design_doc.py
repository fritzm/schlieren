"""Concatenate docs/design/NN-*.md fragments (filename order) into one consolidated design document.

The output is a generated artifact; edit the fragments, never the output. The fragments' figures are copied
to figures/ beside it, so their relative image links resolve there too.

--pdf also writes a print-styled HTML page beside the Markdown and prints it to docs/schlieren-design.pdf,
the rendered copy versioned in the repository for reading and sharing. The PDF has a linked contents list,
working section links, and a heading outline (bookmarks). It is printed by a locally installed headless Chrome
or Chromium, and its formulas are typeset by KaTeX loaded from a CDN, so that step needs network access.

    uv run build-design-doc [--pdf [PATH]] [-o exports/docs/schlieren-design.md]
"""

import argparse
import re
import shutil
import subprocess
from pathlib import Path

# src/schlieren/cli/<module>.py -> repo root (valid for the editable install that uv sync creates)
REPO_ROOT = Path(__file__).resolve().parents[3]
FRAGMENT_DIR = REPO_ROOT / "docs" / "design"
FIGURE_DIR = FRAGMENT_DIR / "figures"
DEFAULT_OUTPUT = REPO_ROOT / "exports" / "docs" / "schlieren-design.md"
DEFAULT_PDF = REPO_ROOT / "docs" / "schlieren-design.pdf"

CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
    "chromium-browser",
)
CHROME_LOAD_BUDGET_MS = 15000  # Virtual time allowed for the page (KaTeX from the CDN) before printing.
KATEX_CDN = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist"

# Print layout. Sizes other than the base are relative to it, so the base alone sets how much fits on a page.
PDF_BASE_FONT_PT = 9.5
PDF_PAGE_MARGIN_IN = 0.8
PDF_FIGURE_SCALE = (
    0.7  # Figure widths are set for Markdown viewers; print is smaller against the 9.5 pt text.
)
PDF_CONTENTS_DEPTH = "2-3"  # Heading levels listed in the contents: sections and subsections.
PDF_STYLE = f"""
@page {{ size: Letter; margin: {PDF_PAGE_MARGIN_IN}in; }}
body {{ font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: {PDF_BASE_FONT_PT}pt;
       line-height: 1.4; color: #111; }}
h1 {{ font-size: 1.9em; margin: 0 0 0.6em; }}
h2 {{ font-size: 1.45em; margin: 1.4em 0 0.5em; border-bottom: 0.5pt solid #999; padding-bottom: 0.2em; }}
h3 {{ font-size: 1.2em; margin: 1.2em 0 0.45em; }}
h4 {{ font-size: 1.05em; margin: 1.1em 0 0.35em; }}
h1, h2, h3, h4 {{ break-after: avoid; break-inside: avoid; }}
h2 {{ break-before: page; }}
h2#conventions {{ break-before: auto; }}  /* shares the title page's second page with the subtitle */
img {{ zoom: {PDF_FIGURE_SCALE}; }}
p {{ margin: 0 0 0.75em; orphans: 3; widows: 3; }}
ul, ol {{ margin: 0 0 0.75em; padding-left: 1.9em; }}
li {{ margin-bottom: 0.2em; break-inside: avoid; }}
table {{ border-collapse: collapse; margin: 0 0 1em; break-inside: avoid; }}
th, td {{ border: 0.5pt solid #888; padding: 0.3em 0.65em; text-align: left; vertical-align: top; }}
th {{ background: #eee; }}
code {{ font-family: Menlo, monospace; font-size: 0.88em; }}
pre {{ background: #f4f4f4; padding: 0.6em; break-inside: avoid; white-space: pre-wrap; }}
p[align=center] {{ break-inside: avoid; }}
p:has(+ ul), p:has(+ ol), p:has(+ table), p:has(+ pre) {{ break-after: avoid; }}
a {{ color: #1a4f8b; text-decoration: none; }}
nav {{ break-after: page; }}
.contents-title {{ font-size: 1.2em; font-weight: bold; margin: 1.2em 0 0.5em; }}
.toc {{ columns: 2; column-gap: 2.5em; }}
.toc ul {{ list-style: none; margin: 0; padding-left: 0; }}
.toc ul ul {{ padding-left: 1.2em; margin-bottom: 0.5em; }}
.toc > ul > li {{ font-weight: bold; break-inside: avoid-column; }}
.toc ul ul li {{ font-weight: normal; margin-bottom: 0; }}
"""
KATEX_HEAD = f"""
<link rel="stylesheet" href="{KATEX_CDN}/katex.min.css">
<script src="{KATEX_CDN}/katex.min.js"></script>
<script src="{KATEX_CDN}/contrib/auto-render.min.js"></script>
<script>
addEventListener("DOMContentLoaded", () =>
  renderMathInElement(document.body, {{delimiters: [{{left: "$$", right: "$$", display: true}}]}}));
</script>
"""


def build_design_doc() -> str:
    fragments = sorted(FRAGMENT_DIR.glob("[0-9][0-9]-*.md"))
    if not fragments:
        raise SystemExit(f"No fragments found in {FRAGMENT_DIR}")
    text = "\n".join(f.read_text(encoding="utf-8").rstrip() + "\n" for f in fragments)
    # Fragment-to-fragment links (NN-name.md#anchor) become in-document anchors in the consolidated output.
    return re.sub(r"\]\(\d\d-[\w-]+\.md#", "](#", text)


def build_print_html(design_doc: str, title: str) -> str:
    """The consolidated Markdown as one print-styled HTML page; figure links stay relative."""
    import markdown

    converter = markdown.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", "toc"],
        extension_configs={"toc": {"toc_depth": PDF_CONTENTS_DEPTH}},
    )
    body = converter.convert(design_doc)
    # Linked contents list after the title; the toc extension also gives every heading the id that the
    # in-document section links point at.
    contents = f'<nav><p class="contents-title">Contents</p>{converter.toc}</nav>'
    body = body.replace("</h1>", f"</h1>\n{contents}", 1)
    head = f'<meta charset="utf-8"><title>{title}</title><style>{PDF_STYLE}</style>{KATEX_HEAD}'
    return f"<!doctype html>\n<html><head>{head}</head>\n<body>\n{body}\n</body></html>\n"


def find_chrome() -> str:
    for candidate in CHROME_CANDIDATES:
        found = candidate if Path(candidate).is_file() else shutil.which(candidate)
        if found:
            return found
    raise SystemExit("--pdf needs Google Chrome or Chromium installed to print the document")


def print_pdf(html: Path, pdf: Path) -> None:
    subprocess.run(
        [
            find_chrome(),
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--generate-pdf-document-outline",
            f"--virtual-time-budget={CHROME_LOAD_BUDGET_MS}",
            f"--print-to-pdf={pdf.resolve()}",
            html.resolve().as_uri(),
        ],
        check=True,
        capture_output=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--pdf",
        type=Path,
        nargs="?",
        const=DEFAULT_PDF,
        metavar="PATH",
        help=f"Also write a print-styled .html and print it to a PDF (default {DEFAULT_PDF.relative_to(REPO_ROOT)})",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    design_doc = build_design_doc()
    args.output.write_text(design_doc, encoding="utf-8")
    print(f"Wrote {args.output}")
    if FIGURE_DIR.is_dir():
        copied = args.output.parent / FIGURE_DIR.name
        shutil.copytree(FIGURE_DIR, copied, dirs_exist_ok=True)
        print(f"Copied figures to {copied}")
    if args.pdf:
        html = args.output.with_suffix(".html")
        html.write_text(build_print_html(design_doc, args.output.stem), encoding="utf-8")
        print(f"Wrote {html}")
        args.pdf.parent.mkdir(parents=True, exist_ok=True)
        print_pdf(html, args.pdf)
        print(f"Wrote {args.pdf}")


if __name__ == "__main__":
    main()

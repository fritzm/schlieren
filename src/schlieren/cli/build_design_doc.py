"""Concatenate docs/design/NN-*.md fragments (filename order) into one consolidated design document.

The output is a generated artifact; edit the fragments, never the output. The fragments' figures are copied
to figures/ beside it, so their relative image links resolve there too.

--pdf also writes a print-styled HTML page and a PDF of it beside the Markdown; the PDF is the read-only copy
shared on Google Drive. It is printed by a locally installed headless Chrome or Chromium, and its formulas are
typeset by KaTeX loaded from a CDN, so that step needs network access. No Drive access is used here.

    uv run build-design-doc [--pdf] [-o exports/docs/schlieren-design.md]
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
PDF_STYLE = f"""
@page {{ size: Letter; margin: {PDF_PAGE_MARGIN_IN}in; }}
body {{ font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: {PDF_BASE_FONT_PT}pt;
       line-height: 1.4; color: #111; }}
h1 {{ font-size: 1.9em; margin: 0 0 0.6em; }}
h2 {{ font-size: 1.45em; margin: 1.4em 0 0.5em; border-bottom: 0.5pt solid #999; padding-bottom: 0.2em; }}
h3 {{ font-size: 1.2em; margin: 1.2em 0 0.45em; }}
h4 {{ font-size: 1.05em; margin: 1.1em 0 0.35em; }}
h1, h2, h3, h4 {{ break-after: avoid; break-inside: avoid; }}
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

    body = markdown.markdown(design_doc, extensions=["tables", "fenced_code", "sane_lists"])
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
    parser.add_argument("--pdf", action="store_true", help="Also write a print-styled .html and .pdf")
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
        pdf = args.output.with_suffix(".pdf")
        print_pdf(html, pdf)
        print(f"Wrote {pdf}")


if __name__ == "__main__":
    main()

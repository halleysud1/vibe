"""High-fidelity Markdown -> PDF rendering via Chromium (vendored, ADR-015).

Self-contained copy used by the md-to-pdf skill (no project deps). Renders
Markdown through a real browser engine: Markdown --(markdown-it-py)--> HTML
--(professional CSS + mermaid.js)--> Chromium print-to-PDF. Styled tables,
callouts, syntax-highlighted code, rendered diagrams, page numbers.

Heavy deps (playwright, pygments) are optional/lazy; convert.py falls back to
the pure-python markdown-pdf backend when Chromium is unavailable.
"""

from __future__ import annotations

import contextlib
import html as _html
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Mermaid is fetched from a CDN at render time (only when a diagram is present).
_MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"

# --------------------------------------------------------------------------- #
# Professional default theme — this is the "veste grafica".                   #
# Print-oriented CSS (A4). Page numbers are added via Chromium footerTemplate. #
# --------------------------------------------------------------------------- #
DEFAULT_THEME_CSS = """
:root {
  --ink:        #1a2433;
  --navy:       #0a192f;
  --navy-soft:  #112240;
  --accent:     #c9a227;   /* oro sobrio */
  --rule:       #e4e8ee;
  --muted:      #5b6675;
  --code-bg:    #f5f7fa;
  --callout-bg: #f4f6f8;
  --table-zebra:#f7f9fc;
}

@page { size: A4; margin: 20mm 18mm 22mm 18mm; }

html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }

body {
  font-family: "Segoe UI", "Helvetica Neue", Helvetica, Arial, sans-serif;
  color: var(--ink);
  font-size: 10.5pt;
  line-height: 1.55;
  margin: 0;
}

/* ---- Headings ---------------------------------------------------------- */
h1, h2, h3, h4 {
  font-family: "Segoe UI Semibold", "Helvetica Neue", Helvetica, Arial, sans-serif;
  color: var(--navy);
  line-height: 1.25;
  margin: 1.4em 0 0.5em;
  page-break-after: avoid;
}
h1 {
  font-size: 22pt;
  letter-spacing: -0.01em;
  border-bottom: 2.5px solid var(--accent);
  padding-bottom: 0.25em;
  margin-top: 0;
}
h2 {
  font-size: 15pt;
  color: var(--navy-soft);
  border-bottom: 1px solid var(--rule);
  padding-bottom: 0.2em;
}
h3 { font-size: 12.5pt; color: #233554; }
h4 { font-size: 11pt; color: #33415c; text-transform: uppercase; letter-spacing: 0.04em; }

p { margin: 0.55em 0; }
a { color: var(--navy-soft); text-decoration: none; border-bottom: 1px solid var(--rule); }
strong { color: var(--navy); }
em { color: var(--muted); }

ul, ol { margin: 0.5em 0; padding-left: 1.4em; }
li { margin: 0.2em 0; }
li::marker { color: var(--accent); }

hr { border: 0; height: 1px; background: var(--rule); margin: 1.8em 0; }

/* ---- Tables ------------------------------------------------------------ */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 1.1em 0;
  font-size: 9.5pt;
  page-break-inside: avoid;
}
thead th {
  background: var(--navy);
  color: #fff;
  font-weight: 600;
  text-align: left;
  padding: 9px 12px;
}
td { padding: 8px 12px; border-bottom: 1px solid var(--rule); vertical-align: top; }
tbody tr:nth-child(even) { background: var(--table-zebra); }
table strong { color: var(--navy); }

/* ---- Code -------------------------------------------------------------- */
code {
  font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
  font-size: 9pt;
  background: var(--code-bg);
  padding: 0.12em 0.35em;
  border-radius: 4px;
  color: #b03060;
}
pre {
  background: var(--code-bg);
  border: 1px solid var(--rule);
  border-left: 3px solid var(--navy-soft);
  border-radius: 6px;
  padding: 12px 14px;
  overflow-x: auto;
  font-size: 8.8pt;
  line-height: 1.45;
  page-break-inside: avoid;
}
pre code { background: none; padding: 0; color: inherit; border-radius: 0; }

/* ---- Blockquotes / callouts ------------------------------------------- */
blockquote {
  border-left: 3px solid var(--accent);
  background: var(--callout-bg);
  margin: 1.1em 0;
  padding: 0.6em 1em;
  color: #44505f;
  border-radius: 0 6px 6px 0;
}
blockquote p { margin: 0.2em 0; }

/* ---- Media / diagrams -------------------------------------------------- */
img { max-width: 100%; height: auto; }
pre.mermaid, .mermaid {
  background: none;
  border: 0;
  border-radius: 0;
  padding: 0;
  text-align: center;
  margin: 1.4em 0;
  page-break-inside: avoid;
}
.mermaid svg { max-width: 100%; height: auto; }

/* Force page breaks where the source asks for them. */
div[style*="page-break-after"] { page-break-after: always; }
"""

# Minimal pygments stylesheet (light) — injected only when code is present.
_PYGMENTS_FALLBACK = """
.codehilite .k  { color:#0a3069; font-weight:600; }
.codehilite .kn { color:#0a3069; font-weight:600; }
.codehilite .s, .codehilite .s1, .codehilite .s2 { color:#0a7d3c; }
.codehilite .c, .codehilite .c1 { color:#7a8694; font-style:italic; }
.codehilite .nf { color:#8250df; }
.codehilite .mi, .codehilite .mf { color:#b03060; }
.codehilite .o  { color:#1a2433; }
.codehilite .nb { color:#0550ae; }
"""


def _pygments_css() -> str:
    try:
        from pygments.formatters import HtmlFormatter

        return HtmlFormatter(style="default", cssclass="codehilite").get_style_defs(
            ".codehilite"
        )
    except Exception:  # pragma: no cover - pygments optional
        return _PYGMENTS_FALLBACK


def _highlight(code: str, lang: str) -> str:
    """Return syntax-highlighted HTML for ``code`` (best-effort)."""
    try:
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import get_lexer_by_name, guess_lexer

        lexer = get_lexer_by_name(lang) if lang else guess_lexer(code)
        return highlight(code, lexer, HtmlFormatter(cssclass="codehilite"))
    except Exception:
        return f'<pre><code>{_html.escape(code)}</code></pre>'


def markdown_to_html_fragment(markdown: str) -> tuple[str, bool]:
    """Convert Markdown to an HTML body fragment.

    Returns ``(html, has_mermaid)``. ``mermaid`` fenced blocks become
    ``<pre class="mermaid">`` so mermaid.js renders them in the browser; other
    fenced code is syntax-highlighted via pygments.
    """
    from markdown_it import MarkdownIt

    has_mermaid = False

    md = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])

    def _fence(tokens, idx, options, env):
        nonlocal has_mermaid
        token = tokens[idx]
        info = (token.info or "").strip().split(maxsplit=1)
        lang = info[0] if info else ""
        if lang.lower() == "mermaid":
            has_mermaid = True
            return f'<pre class="mermaid">{_html.escape(token.content)}</pre>\n'
        return _highlight(token.content, lang)

    md.renderer.rules["fence"] = _fence
    return md.render(markdown), has_mermaid


def wrap_document(
    body_html: str,
    *,
    title: str | None,
    theme_css: str,
    enable_mermaid: bool,
    has_code: bool,
) -> str:
    """Wrap an HTML body fragment into a full, print-ready HTML document."""
    parts = [
        "<!DOCTYPE html><html lang='it'><head><meta charset='utf-8'>",
        f"<title>{_html.escape(title or 'Documento')}</title>",
        f"<style>{theme_css}</style>",
    ]
    if has_code:
        parts.append(f"<style>{_pygments_css()}</style>")
    parts.append("</head><body>")
    parts.append(body_html)
    if enable_mermaid:
        parts.append(
            f'<script src="{_MERMAID_CDN}"></script>'
            "<script>"
            "mermaid.initialize({startOnLoad:true,theme:'neutral',"
            "themeVariables:{primaryColor:'#112240',primaryTextColor:'#fff',"
            "lineColor:'#5b6675',fontSize:'14px'}});"
            "</script>"
        )
    parts.append("</body></html>")
    return "".join(parts)


_FOOTER_TEMPLATE = (
    "<div style='font-size:8px;color:#8a93a0;width:100%;padding:0 18mm;"
    "font-family:Segoe UI,Helvetica,Arial,sans-serif;"
    "display:flex;justify-content:space-between;'>"
    "<span class='title'></span>"
    "<span><span class='pageNumber'></span> / <span class='totalPages'></span></span>"
    "</div>"
)


def render_html_to_pdf(
    full_html: str,
    out_path: str | Path,
    *,
    base_dir: Path | None = None,
    enable_mermaid: bool = False,
    page_numbers: bool = True,
) -> Path:
    """Render a complete HTML document to PDF using headless Chromium.

    Raises :class:`RuntimeError` if Playwright/Chromium is unavailable so the
    caller can fall back to the legacy renderer.
    """
    out_path = Path(out_path)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:  # pragma: no cover - optional dep
        raise RuntimeError("playwright non installato (pip install playwright)") from e

    # Write to a temp .html in base_dir so relative images/links resolve.
    work_dir = base_dir or out_path.parent
    fd_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".html", dir=str(work_dir), delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(full_html)
            fd_path = Path(tmp.name)

        with sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception as e:  # pragma: no cover - browser not installed
                raise RuntimeError(
                    f"Chromium non avviabile ({e}); esegui 'playwright install chromium'"
                ) from e
            page = browser.new_page()
            page.goto(fd_path.as_uri(), wait_until="networkidle")
            if enable_mermaid:
                # Wait for mermaid to finish processing all diagrams.
                try:
                    page.wait_for_function(
                        "() => !document.querySelector('.mermaid:not([data-processed])')",
                        timeout=8000,
                    )
                except Exception:
                    logger.warning("mermaid: timeout rendering diagrammi (proseguo)")
            page.pdf(
                path=str(out_path),
                format="A4",
                print_background=True,
                display_header_footer=page_numbers,
                footer_template=_FOOTER_TEMPLATE if page_numbers else "<span></span>",
                header_template="<span></span>",
                margin={"top": "20mm", "bottom": "22mm", "left": "18mm", "right": "18mm"},
            )
            browser.close()
    finally:
        if fd_path is not None:
            with contextlib.suppress(OSError):
                fd_path.unlink()
    return out_path


def render_markdown_to_pdf(
    markdown: str,
    out_path: str | Path,
    *,
    title: str | None = None,
    theme_css: str | None = None,
    base_dir: Path | None = None,
    page_numbers: bool = True,
) -> Path:
    """Full pipeline: Markdown string -> designed PDF via Chromium.

    Raises :class:`RuntimeError` if Chromium is unavailable.
    """
    body, has_mermaid = markdown_to_html_fragment(markdown)
    has_code = "codehilite" in body or "<pre" in body
    doc = wrap_document(
        body,
        title=title,
        theme_css=theme_css or DEFAULT_THEME_CSS,
        enable_mermaid=has_mermaid,
        has_code=has_code,
    )
    return render_html_to_pdf(
        doc,
        out_path,
        base_dir=base_dir,
        enable_mermaid=has_mermaid,
        page_numbers=page_numbers,
    )


def chromium_available() -> bool:
    """True if Playwright + a launchable Chromium are present."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            browser.close()
        return True
    except Exception:
        return False


__all__ = [
    "DEFAULT_THEME_CSS",
    "chromium_available",
    "markdown_to_html_fragment",
    "render_html_to_pdf",
    "render_markdown_to_pdf",
    "wrap_document",
]

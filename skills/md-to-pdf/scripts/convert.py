"""Convert Markdown files to PDF.

Two backends:

* ``chromium`` (default when available) — high-fidelity: Markdown -> HTML with
  a professional CSS theme (optionally Gemini-authored) -> headless Chromium
  print-to-PDF. Styled tables, callouts, syntax-highlighted code, rendered
  ``mermaid`` diagrams, running footer with page numbers. Requires
  ``playwright`` + ``playwright install chromium``.
* ``markdown-pdf`` (pure-python fallback) — PyMuPDF; limited CSS, no diagrams.

Optionally appends an AI-generated summary section at the end of the PDF (via
Gemini), without modifying the source markdown file.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CSS = SKILL_DIR / "styles" / "default.css"
THEME_CSS = SKILL_DIR / "styles" / "theme.css"

DEFAULT_AI_MODEL = "gemini-3.5-flash"

SUMMARY_SYSTEM_PROMPT = (
    "Sei un assistente esperto nel produrre sintesi rapide di documenti tecnici, "
    "specifiche di progetto, skill e procedure. La sintesi deve permettere a un "
    "lettore di capire in 30 secondi di cosa parla il documento e quando consultarlo. "
    "Scrivi in italiano, tono asciutto, senza fluff."
)

SUMMARY_USER_TEMPLATE = """Documento da sintetizzare:
\"\"\"
{md_text}
\"\"\"

Produci la sintesi in markdown con questa struttura ESATTA:

### TL;DR
3-4 frasi che riassumono cosa fa o cosa descrive il documento.

### Punti chiave
- 5-8 bullet con i concetti centrali (decisioni, vincoli, regole, dati significativi)

### Quando consultarlo
2-3 frasi su quando questo documento e' utile e a chi.

### Limiti / cose da sapere
- 0-4 bullet con limiti, dipendenze, prerequisiti, attenzioni (se non emergono, scrivi "Nessun limite particolare emerge dal documento.")

NON aggiungere altre sezioni oltre a queste quattro. NON copiare lunghi blocchi di
testo dal documento. NON inserire emoji. Cita riferimenti puntuali (path file, nomi
funzioni, valori) quando aggiungono precisione."""

THEME_SYSTEM_PROMPT = (
    "Sei un art director esperto di tipografia editoriale e graphic design per "
    "documenti tecnici e finanziari. Produci CSS print-ready di alta qualita'."
)

THEME_USER_TEMPLATE = """Genera un foglio di stile CSS per impaginare in PDF (A4, stampa via Chromium) un documento Markdown convertito in HTML.

Requisiti NON negoziabili:
- Solo CSS valido. NIENTE testo fuori dal CSS, niente markdown fence, niente commenti esplicativi.
- Stile professionale, pulito, leggibile.
- Stili per: body, h1-h4, p, ul/ol/li, a, strong, em, hr, table/thead/th/td (zebra striping), code, pre, blockquote (callout), img, .mermaid.
- `@page {{ size: A4; margin: ... }}` e `-webkit-print-color-adjust: exact`.
- `page-break-inside: avoid` su table e pre; `page-break-after: avoid` sui heading.
- Solo font di sistema (Segoe UI, Helvetica, Georgia, Consolas...). NIENTE @import / web font esterni.
- line-height ~1.5, tabelle eleganti con header a contrasto.

Base da migliorare (non limitarti a copiarla):
{base_css}

Tono del documento (per calibrare l'estetica):
{doc_excerpt}

Rispondi SOLO con il CSS."""


def strip_frontmatter(text: str) -> str:
    """Remove leading YAML front-matter (--- ... ---) if present."""
    if not text.startswith("---"):
        return text
    lines = text.splitlines(keepends=True)
    if len(lines) < 2:
        return text
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            return "".join(lines[i + 1 :]).lstrip()
    return text


def load_css(css_path: Path | None) -> str | None:
    if css_path is None:
        return None
    if not css_path.is_file():
        raise SystemExit(f"CSS file not found: {css_path}")
    return css_path.read_text(encoding="utf-8")


def call_gemini(system_prompt: str, user_prompt: str, model: str) -> str | None:
    """Call Gemini and return text. Returns None on any failure (after warn)."""
    try:
        try:
            from dotenv import find_dotenv, load_dotenv

            # Search from the invocation CWD (the project), not the plugin dir
            # where this script lives.
            load_dotenv(find_dotenv(usecwd=True))
        except ImportError:
            pass

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print(
                "Warning: GEMINI_API_KEY non configurata, funzione AI saltata.",
                file=sys.stderr,
            )
            return None

        os.environ.pop("GOOGLE_API_KEY", None)

        from google import genai

        client = genai.Client(api_key=api_key)
        r = client.models.generate_content(
            model=model,
            contents=system_prompt + "\n\n" + user_prompt,
        )
        return r.text
    except ImportError:
        print(
            "Warning: pacchetto google-genai non installato, funzione AI saltata.",
            file=sys.stderr,
        )
        return None
    except Exception as e:
        print(f"Warning: errore chiamata Gemini ({e}), funzione AI saltata.", file=sys.stderr)
        return None


def build_ai_summary(md_text: str, model: str) -> str | None:
    user = SUMMARY_USER_TEMPLATE.format(md_text=md_text)
    return call_gemini(SUMMARY_SYSTEM_PROMPT, user, model)


def wrap_summary_md(summary_md: str, model: str) -> str:
    """Wrap the AI summary with a header and disclaimer."""
    return (
        "## Sintesi AI (generata automaticamente)\n\n"
        f"> Sintesi prodotta da `{model}` a scopo di lettura veloce. "
        f"Il contenuto autoritativo resta quello del documento sopra. "
        f"Non sostituisce la lettura integrale.\n\n"
        f"{summary_md.strip()}\n"
    )


def _strip_css_fence(text: str) -> str:
    import re

    text = text.strip()
    m = re.search(r"```(?:css)?\s*(.*?)```", text, re.DOTALL)
    return m.group(1).strip() if m else text


def build_gemini_theme(doc_excerpt: str, base_css: str, model: str) -> str | None:
    """Ask Gemini for a bespoke print CSS theme. Returns None on failure."""
    user = THEME_USER_TEMPLATE.format(base_css=base_css, doc_excerpt=doc_excerpt[:2500])
    out = call_gemini(THEME_SYSTEM_PROMPT, user, model)
    if not out:
        return None
    css = _strip_css_fence(out)
    if "{" in css and "}" in css and len(css) > 200:
        return css
    print("Warning: tema Gemini non plausibile, uso tema di default.", file=sys.stderr)
    return None


def _chromium_engine():
    """Import the vendored Chromium engine, or None if unavailable."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import html_engine  # type: ignore

        return html_engine
    except ImportError:
        return None


def _resolve_engine(requested: str) -> str:
    """Resolve 'auto' to 'chromium' when usable, else 'markdown-pdf'."""
    if requested != "auto":
        return requested
    engine = _chromium_engine()
    if engine is not None and engine.chromium_available():
        return "chromium"
    return "markdown-pdf"


def _render_chromium(
    text: str,
    summary_md: str | None,
    output_path: Path,
    css_text: str | None,
    title: str | None,
    gemini_theme: bool,
    ai_model: str,
) -> Path:
    engine = _chromium_engine()
    if engine is None:
        raise SystemExit("Backend chromium richiesto ma html_engine non importabile.")

    combined = text
    if summary_md:
        combined = f"{text}\n\n<div style='page-break-after: always;'></div>\n\n{summary_md}"

    theme_css = css_text or engine.DEFAULT_THEME_CSS
    if gemini_theme:
        gen = build_gemini_theme(text, engine.DEFAULT_THEME_CSS, ai_model)
        if gen:
            theme_css = gen

    output_path.parent.mkdir(parents=True, exist_ok=True)
    return engine.render_markdown_to_pdf(
        combined, output_path, title=title, theme_css=theme_css
    )


def _render_markdown_pdf(
    text: str,
    summary_md: str | None,
    output_path: Path,
    css_text: str | None,
    toc_level: int,
    mode: str,
    paper_size: str,
    title: str | None,
    author: str | None,
    root: str,
) -> Path:
    from markdown_pdf import MarkdownPdf, Section

    def build_pdf(use_toc_level: int) -> MarkdownPdf:
        pdf = MarkdownPdf(toc_level=use_toc_level, mode=mode, optimize=True)
        pdf.meta["title"] = title or output_path.stem
        if author:
            pdf.meta["author"] = author
        pdf.add_section(
            Section(text, toc=(use_toc_level > 0), root=root, paper_size=paper_size),
            user_css=css_text,
        )
        if summary_md:
            pdf.add_section(
                Section(summary_md, toc=False, root=root, paper_size=paper_size),
                user_css=css_text,
            )
        return pdf

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        build_pdf(toc_level).save(output_path)
    except ValueError as e:
        if toc_level > 0 and "hierarchy level" in str(e):
            print(
                f"Warning: TOC non costruibile per {output_path.name} "
                f"(headings non lineari): rigenero senza TOC.",
                file=sys.stderr,
            )
            build_pdf(0).save(output_path)
        else:
            raise
    return output_path


def convert_one(
    input_path: Path,
    output_path: Path,
    css_text: str | None,
    toc_level: int,
    mode: str,
    paper_size: str,
    title: str | None,
    author: str | None,
    ai_summary: bool,
    ai_model: str,
    engine: str,
    gemini_theme: bool,
) -> Path:
    if not input_path.is_file():
        raise SystemExit(f"Input file not found: {input_path}")

    raw = input_path.read_text(encoding="utf-8")
    text = strip_frontmatter(raw)

    summary_md: str | None = None
    if ai_summary:
        summary = build_ai_summary(text, ai_model)
        if summary:
            summary_md = wrap_summary_md(summary, ai_model)

    resolved = _resolve_engine(engine)
    if resolved == "chromium":
        return _render_chromium(
            text, summary_md, output_path, css_text, title, gemini_theme, ai_model
        )
    return _render_markdown_pdf(
        text, summary_md, output_path, css_text, toc_level, mode, paper_size,
        title, author, str(input_path.parent),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Convert Markdown to PDF (Chromium hi-fi or pure-python).",
    )
    p.add_argument("inputs", nargs="+", type=Path, help="Markdown file(s) to convert.")
    p.add_argument(
        "-o", "--output", type=Path, default=None,
        help="Output PDF path. If omitted, replaces .md with .pdf. Ignored in batch.",
    )
    p.add_argument("--out-dir", type=Path, default=None, help="Directory for batch outputs.")
    p.add_argument(
        "--engine", choices=("auto", "chromium", "markdown-pdf"), default="auto",
        help="Rendering backend. 'auto' uses Chromium when available, else markdown-pdf.",
    )
    p.add_argument(
        "--gemini-theme", action="store_true",
        help="Let Gemini author a bespoke CSS theme (chromium engine). Requires GEMINI_API_KEY.",
    )
    p.add_argument(
        "--css", type=Path, default=None,
        help="Custom CSS file. Default: styles/theme.css (chromium) or styles/default.css.",
    )
    p.add_argument("--no-css", action="store_true", help="Disable any CSS (bare defaults).")
    p.add_argument("--toc-level", type=int, default=3, help="TOC depth (0 disables). markdown-pdf only.")
    p.add_argument(
        "--mode", choices=("default", "commonmark", "zero"), default="commonmark",
        help="markdown-it preset (markdown-pdf engine).",
    )
    p.add_argument("--paper-size", default="A4", help="Paper size (markdown-pdf engine).")
    p.add_argument("--title", default=None, help="PDF metadata title.")
    p.add_argument("--author", default=None, help="PDF metadata author.")
    p.add_argument(
        "--ai-summary", action="store_true",
        help="Append an AI-generated summary section at the end. Requires GEMINI_API_KEY.",
    )
    p.add_argument("--ai-model", default=DEFAULT_AI_MODEL, help=f"Gemini model. Default: {DEFAULT_AI_MODEL}.")
    return p.parse_args(argv)


def _resolve_css(args: argparse.Namespace, engine: str) -> str | None:
    if args.no_css:
        return None
    if args.css is not None:
        return load_css(args.css)
    # Default CSS depends on the engine.
    if engine == "markdown-pdf" and DEFAULT_CSS.is_file():
        return load_css(DEFAULT_CSS)
    if engine == "chromium" and THEME_CSS.is_file():
        return load_css(THEME_CSS)
    return None  # chromium uses its built-in DEFAULT_THEME_CSS


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    inputs: list[Path] = args.inputs
    batch = len(inputs) > 1
    if batch and args.output:
        print("Warning: --output ignored in batch mode; use --out-dir.", file=sys.stderr)

    resolved_engine = _resolve_engine(args.engine)
    css_text = _resolve_css(args, resolved_engine)

    for src in inputs:
        if batch or args.out_dir:
            out_dir = args.out_dir or src.parent
            dst = out_dir / (src.stem + ".pdf")
        else:
            dst = args.output or src.with_suffix(".pdf")

        result = convert_one(
            input_path=src,
            output_path=dst,
            css_text=css_text,
            toc_level=args.toc_level,
            mode=args.mode,
            paper_size=args.paper_size,
            title=args.title,
            author=args.author,
            ai_summary=args.ai_summary,
            ai_model=args.ai_model,
            engine=args.engine,
            gemini_theme=args.gemini_theme,
        )
        print(f"OK [{resolved_engine}]: {src} -> {result}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

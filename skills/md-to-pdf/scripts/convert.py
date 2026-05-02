"""Convert Markdown files to PDF using markdown-pdf (pure-python).

Optionally appends an AI-generated summary section at the end of the PDF
(via Gemini), without modifying the source markdown file.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from markdown_pdf import MarkdownPdf, Section


SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CSS = SKILL_DIR / "styles" / "default.css"

DEFAULT_AI_MODEL = "gemini-3.1-pro-preview"

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


def strip_frontmatter(text: str) -> str:
    """Remove leading YAML front-matter (--- ... ---) if present.

    markdown-pdf does not handle YAML front-matter and mistakes the fences
    for thematic breaks, which breaks TOC generation.
    """
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
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print(
                "Warning: GEMINI_API_KEY non configurata, sintesi AI saltata.",
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
            "Warning: pacchetto google-genai non installato, sintesi AI saltata.",
            file=sys.stderr,
        )
        return None
    except Exception as e:
        print(f"Warning: errore chiamata Gemini ({e}), sintesi AI saltata.", file=sys.stderr)
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

    def build_pdf(use_toc_level: int) -> MarkdownPdf:
        pdf = MarkdownPdf(toc_level=use_toc_level, mode=mode, optimize=True)
        pdf.meta["title"] = title or input_path.stem
        if author:
            pdf.meta["author"] = author

        main_section = Section(
            text,
            toc=(use_toc_level > 0),
            root=str(input_path.parent),
            paper_size=paper_size,
        )
        pdf.add_section(main_section, user_css=css_text)

        if summary_md:
            summary_section = Section(
                summary_md,
                toc=False,
                root=str(input_path.parent),
                paper_size=paper_size,
            )
            pdf.add_section(summary_section, user_css=css_text)
        return pdf

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        build_pdf(toc_level).save(output_path)
    except ValueError as e:
        if toc_level > 0 and "hierarchy level" in str(e):
            print(
                f"Warning: TOC non costruibile per {input_path.name} "
                f"(headings non lineari): rigenero senza TOC.",
                file=sys.stderr,
            )
            build_pdf(0).save(output_path)
        else:
            raise
    return output_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Convert Markdown to PDF (pure-python via markdown-pdf).",
    )
    p.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Markdown file(s) to convert. Pass multiple paths for batch mode.",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help=(
            "Output PDF path. If omitted, replaces .md extension with .pdf "
            "next to the source. Ignored in batch mode."
        ),
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Directory for batch outputs (one PDF per input).",
    )
    p.add_argument(
        "--css",
        type=Path,
        default=DEFAULT_CSS,
        help=f"Custom CSS file. Default: {DEFAULT_CSS.name} bundled with the skill.",
    )
    p.add_argument(
        "--no-css",
        action="store_true",
        help="Disable any CSS (use markdown-pdf bare defaults).",
    )
    p.add_argument(
        "--toc-level",
        type=int,
        default=3,
        help="Heading depth included in TOC (0 disables TOC). Default: 3.",
    )
    p.add_argument(
        "--mode",
        choices=("default", "commonmark", "zero"),
        default="commonmark",
        help=(
            "markdown-it preset. 'commonmark' is strict CommonMark, "
            "'default' adds linkify/typographer, 'zero' is minimal. "
            "Tables are always enabled by markdown-pdf."
        ),
    )
    p.add_argument(
        "--paper-size",
        default="A4",
        help="Paper size, e.g. A4, A5, Letter. Default: A4.",
    )
    p.add_argument("--title", default=None, help="PDF metadata title.")
    p.add_argument("--author", default=None, help="PDF metadata author.")
    p.add_argument(
        "--ai-summary",
        action="store_true",
        help=(
            "Append an AI-generated summary section at the end of the PDF "
            "(does NOT modify the source .md). Requires GEMINI_API_KEY."
        ),
    )
    p.add_argument(
        "--ai-model",
        default=DEFAULT_AI_MODEL,
        help=f"Gemini model for the summary. Default: {DEFAULT_AI_MODEL}.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    css_text = None if args.no_css else load_css(args.css)

    inputs: list[Path] = args.inputs
    batch = len(inputs) > 1

    if batch and args.output:
        print("Warning: --output ignored in batch mode; use --out-dir.", file=sys.stderr)

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
        )
        print(f"OK: {src} -> {result}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Ricerca grounded single-shot (reasoning + google_search) — la gamba veloce del funnel.

Complementare a `deep_research.py`: qui il modello ragiona una volta sola usando
`google_search` durante la generazione. Tempi 1-3 minuti invece di 10-40.

Usala per:
- **second-opinion / audit** del report Deep Research (modello diverso, costo basso)
- **round mirati** su un singolo gap residuo
- modalita' "ho fretta": ripiego esplicito quando Deep Research e' indisponibile
  o l'utente rinuncia consapevolmente alla profondita'

NON usarla per i round del funnel al posto di Deep Research senza dirlo
all'utente e senza annotarlo nel report finale: la copertura delle fonti e' di
un ordine di grandezza inferiore.

Uso:
    python scripts/grounded_research.py --prompt-file ricerche/audit_prompt.md --tag audit
    python scripts/grounded_research.py --prompt-file p.md --output-json a.json --model <modello>

Exit code: 0 = ok | 2 = argomenti | 3 = dipendenza mancante | 4 = chiamata fallita.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from env_loader import get as env_get  # noqa: E402
from env_loader import load_env, require  # noqa: E402

# Default configurabili via env (GROUNDED_MODEL) o CLI: aggiornali quando esce
# la generazione successiva, non trattarli come costanti di progetto.
FALLBACK_MODEL = "gemini-3.1-pro-preview"
FALLBACK_OUT_DIR = "data/ricerche"
DEFAULT_TIMEOUT_S = 1800
KEEP_ALIVE_INTERVAL_S = 60
MAX_RETRIES_TRANSIENT = 3


def parse_args(env: dict[str, str]) -> argparse.Namespace:
    default_model = env_get(env, "GROUNDED_MODEL", FALLBACK_MODEL)
    default_out_dir = env_get(env, "RESEARCH_OUT_DIR", FALLBACK_OUT_DIR)
    p = argparse.ArgumentParser(description="Ricerca grounded single-shot (reasoning + google_search).")
    p.add_argument("--prompt-file", type=Path, help="File con il prompt.")
    p.add_argument("--prompt", help="Prompt inline (alternativa a --prompt-file).")
    p.add_argument("--tag", help="Id breve (es. 'audit'): deriva output-json, log e response-md sotto --out-dir.")
    p.add_argument("--out-dir", type=Path, default=Path(default_out_dir),
                   help=f"Cartella artefatti quando si usa --tag (default: {default_out_dir}).")
    p.add_argument("--output-json", type=Path, help="Path del JSON di output (obbligatorio se non c'e' --tag).")
    p.add_argument("--response-md", type=Path, help="Scrive anche il solo response_text in questo .md.")
    p.add_argument("--log-file", type=Path, help="Log append-only di stato e timing.")
    p.add_argument("--model", default=default_model, help=f"Modello (default: {default_model}).")
    p.add_argument("--thinking-budget", default="auto",
                   help="'auto', 'off' oppure interi token di reasoning (default: auto).")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S,
                   help=f"Timeout totale in secondi (default: {DEFAULT_TIMEOUT_S}).")
    p.add_argument("--no-search", action="store_true",
                   help="Disattiva google_search (pura sintesi su testo fornito nel prompt).")
    p.add_argument("--overwrite", action="store_true", help="Consente di sovrascrivere l'output esistente.")
    p.add_argument("--dry-run", action="store_true", help="Stampa il payload e termina.")
    return p.parse_args()


def resolve_paths(args: argparse.Namespace) -> None:
    if args.tag:
        safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in args.tag.strip().lower())[:60]
        args.output_json = args.output_json or args.out_dir / f"{safe}.json"
        args.log_file = args.log_file or args.out_dir / f"{safe}.log"
        args.response_md = args.response_md or args.out_dir / f"{safe}_response.md"


def log(line: str, log_file: Path | None) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    full = f"{ts}\t{line}"
    print(full, file=sys.stderr, flush=True)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8") as f:
            f.write(full + "\n")


def thinking_budget_value(raw: str) -> object:
    if raw == "auto":
        return -1
    if raw == "off":
        return 0
    try:
        return int(raw)
    except ValueError as exc:
        raise SystemExit(f"--thinking-budget non valido: {raw}") from exc


def to_dict(obj) -> dict | None:
    if obj is None:
        return None
    for method in ("to_json_dict", "model_dump", "to_dict"):
        m = getattr(obj, method, None)
        if callable(m):
            try:
                return m()
            except Exception:
                pass
    return None


def call_with_retry(client, model: str, contents: str, config: dict, log_file: Path | None):
    """Retry solo su errori transitori (5xx, timeout, unavailable). Mai su 4xx."""
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES_TRANSIENT + 1):
        try:
            log(f"INFO call attempt={attempt} model={model}", log_file)
            return client.models.generate_content(model=model, contents=contents, config=config)
        except Exception as exc:
            last_exc = exc
            msg = str(exc)
            status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            is_5xx = isinstance(status_code, int) and 500 <= status_code < 600
            transient = ("timeout", "temporarily", "unavailable", "deadline", "503", "504", "502")
            if attempt < MAX_RETRIES_TRANSIENT and (is_5xx or any(k in msg.lower() for k in transient)):
                backoff = 2 ** attempt
                log(f"WARN errore transitorio, retry fra {backoff}s: {msg[:200]}", log_file)
                time.sleep(backoff)
                continue
            log(f"ERROR non ritentabile: {msg[:500]}", log_file)
            raise
    assert last_exc is not None
    raise last_exc


def main() -> int:
    env = load_env()
    args = parse_args(env)
    resolve_paths(args)

    if bool(args.prompt_file) == bool(args.prompt):
        print("Serve esattamente uno fra --prompt-file e --prompt.", file=sys.stderr)
        return 2
    if not args.output_json:
        print("Serve --output-json oppure --tag.", file=sys.stderr)
        return 2
    if args.prompt_file and not args.prompt_file.exists():
        print(f"Prompt file non trovato: {args.prompt_file}", file=sys.stderr)
        return 2

    prompt = args.prompt_file.read_text(encoding="utf-8") if args.prompt_file else args.prompt
    if "{{" in prompt:
        print("ATTENZIONE: il prompt contiene ancora segnaposto {{...}} non sostituiti.", file=sys.stderr)
        return 2

    config: dict = {"thinking_config": {"thinking_budget": thinking_budget_value(args.thinking_budget)}}
    if not args.no_search:
        config["tools"] = [{"google_search": {}}]

    if args.dry_run:
        print(json.dumps({
            "model": args.model,
            "config": config,
            "prompt_chars": len(prompt),
            "prompt_first_400": prompt[:400],
            "output_json": str(args.output_json),
        }, ensure_ascii=False, indent=2))
        return 0

    if args.output_json.exists() and not args.overwrite:
        print(f"Output gia' presente: {args.output_json}. Usa un --tag diverso o --overwrite.",
              file=sys.stderr)
        return 2

    try:
        api_key = require(env, "GEMINI_API_KEY")
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    log(f"INFO api_key_prefix={api_key[:6]} api_key_len={len(api_key)}", args.log_file)

    try:
        from google import genai
    except ImportError:
        print("Modulo 'google-genai' mancante. Installa con: pip install 'google-genai>=2.0.0'",
              file=sys.stderr)
        return 3

    client = genai.Client(api_key=api_key, http_options={"timeout": args.timeout * 1000})

    stop = threading.Event()
    start = time.time()

    def _keep_alive() -> None:
        while not stop.wait(KEEP_ALIVE_INTERVAL_S):
            log(f"INFO still running elapsed={int(time.time() - start)}s", args.log_file)

    threading.Thread(target=_keep_alive, daemon=True).start()
    try:
        try:
            response = call_with_retry(client, args.model, prompt, config, args.log_file)
        except Exception as exc:
            log(f"FATAL chiamata fallita: {exc}", args.log_file)
            traceback.print_exc(file=sys.stderr)
            return 4
    finally:
        stop.set()

    elapsed = time.time() - start
    response_text = getattr(response, "text", None) or ""

    grounding_metadata: list[dict] = []
    for c in getattr(response, "candidates", None) or []:
        d = to_dict(getattr(c, "grounding_metadata", None))
        if d is not None:
            grounding_metadata.append(d)

    citations: list[dict] = []
    for gm in grounding_metadata:
        for ch in gm.get("grounding_chunks") or gm.get("groundingChunks") or []:
            web = ch.get("web") if isinstance(ch, dict) else None
            if isinstance(web, dict):
                citations.append({"url": web.get("uri"), "title": web.get("title")})

    out = {
        "model": args.model,
        "search_enabled": not args.no_search,
        "elapsed_seconds": round(elapsed, 1),
        "prompt_chars": len(prompt),
        "response_text": response_text,
        "response_chars": len(response_text),
        "citations": citations,
        "citations_count": len(citations),
        "grounding_metadata": grounding_metadata,
        "usage_metadata": to_dict(getattr(response, "usage_metadata", None)),
        "tag": args.tag,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str),
                                encoding="utf-8")
    if args.response_md and response_text.strip():
        args.response_md.parent.mkdir(parents=True, exist_ok=True)
        args.response_md.write_text(response_text, encoding="utf-8")

    log(f"INFO wrote {args.output_json} response_chars={len(response_text)} "
        f"citations={len(citations)} elapsed={elapsed:.1f}s", args.log_file)

    print(json.dumps({
        "output_json": str(args.output_json),
        "response_md": str(args.response_md) if args.response_md else None,
        "model": args.model,
        "response_chars": len(response_text),
        "citations_count": len(citations),
        "elapsed_seconds": round(elapsed, 1),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Deep Research (task long-running) via Google Interactions API — script portabile.

Deep Research NON e' una `generate_content`: e' un **task asincrono** che dura
tipicamente 10-40 minuti (floor osservato ~10 min anche su prompt brevi). Lo
script incapsula il ciclo completo e produce **un artefatto JSON** che diventa
l'unica fonte di verita' per gli step successivi del funnel.

Pattern (verificato in produzione, schema Interactions 2026):

1. `interactions.create(input=..., agent=..., agent_config={"type":"deep-research"},
   tools=[{"type":"google_search"}], background=True)` -> ritorna subito un id.
   - SENZA `agent_config` + `tools` l'interaction viene creata ma NON parte mai
     (`updated == created` per sempre, nessun errore).
   - SENZA `background=True` l'API rifiuta con 400.
2. `interactions.get(id, stream=True)` -> consuma SSE (`event_type`:
   interaction.created | status_update | completed | error | step.start/delta/stop).
   Lo stream puo' chiudersi PRIMA che il task sia terminale: non e' un errore.
3. Poll `interactions.get(id)` ogni `--poll-interval` finche' lo stato e' terminale.
   L'evento `interaction.completed` porta solo uno scheletro (id/status/timestamp)
   SENZA `steps`: la GET finale serve sempre.
4. Estrazione da `steps[]`: il testo va concatenato da TUTTI i content `text` dei
   `model_output` — l'helper SDK `output_text` si ferma al testo di coda e tronca
   il report se in mezzo c'e' un content non testuale (es. `image`).

Dipendenza: `pip install google-genai>=2.0.0` (lo schema legacy `outputs[]` non
esiste piu': con SDK 1.x l'API risponde "legacy Interactions API schema is no
longer supported").

Uso tipico (un round di funnel, in background dal chiamante):

    python scripts/deep_research.py --prompt-file ricerche/round0_prompt.md --tag round0

    python scripts/deep_research.py --prompt-file p.md \
        --output-json ricerche/round0.json --log-file ricerche/round0.log

Recovery (il processo client e' morto ma il task server-side no; l'id sta nel log):

    python scripts/deep_research.py --resume-id v1_Chd... --tag round0

Exit code: 0 = completed | 1 = terminale non-completed | 2 = argomenti | 3 =
dipendenza mancante | 4 = create fallita | 5 = max-wait superato (il task
prosegue server-side: recuperabile con --resume-id).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from env_loader import get as env_get  # noqa: E402
from env_loader import load_env, require  # noqa: E402

# Default configurabili (env > CLI default). Mai considerare questi valori
# "il modello del progetto": vanno sovrascritti quando Google pubblica il successivo.
FALLBACK_AGENT = "deep-research-max-preview-04-2026"
FALLBACK_OUT_DIR = "data/ricerche"
DEFAULT_POLL_INTERVAL_S = 30
DEFAULT_MAX_WAIT_S = 3600

# Terminale = tutto cio' che non e' "in_progress". Inclusi gli stati 2026
# (incomplete/budget_exceeded/requires_action) per non restare in poll a vita.
TERMINAL_STATES = {
    "completed", "failed", "cancelled", "canceled",
    "incomplete", "budget_exceeded", "requires_action",
}


def parse_args(env: dict[str, str]) -> argparse.Namespace:
    default_agent = env_get(env, "DEEPRESEARCH_AGENT", FALLBACK_AGENT)
    default_out_dir = env_get(env, "RESEARCH_OUT_DIR", FALLBACK_OUT_DIR)
    p = argparse.ArgumentParser(
        description="Deep Research long-running via Interactions API.",
        epilog="Serve --prompt-file/--prompt oppure --resume-id, e --tag oppure --output-json.",
    )
    p.add_argument("--prompt-file", type=Path, help="File con il prompt del round.")
    p.add_argument("--prompt", help="Prompt inline (alternativa a --prompt-file, per test brevi).")
    p.add_argument("--tag", help="Id breve del round (es. 'round0'): deriva output-json, log e response-md sotto --out-dir.")
    p.add_argument("--out-dir", type=Path, default=Path(default_out_dir),
                   help=f"Cartella artefatti quando si usa --tag (default: {default_out_dir}).")
    p.add_argument("--output-json", type=Path, help="Path del JSON di output (obbligatorio se non c'e' --tag).")
    p.add_argument("--response-md", type=Path, help="Scrive anche il solo response_text in questo .md.")
    p.add_argument("--log-file", type=Path, help="Log append-only di stato e timing.")
    p.add_argument("--agent", default=default_agent, help=f"Agent Deep Research (default: {default_agent}).")
    p.add_argument("--thinking-summaries", default="auto", choices=["auto", "none"],
                   help="Visibilita' dei thought summaries (default: auto).")
    p.add_argument("--resume-id", help="Id di un'interaction gia' creata: salta create, fa solo stream+poll.")
    p.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL_S,
                   help=f"Secondi fra i poll post-stream (default: {DEFAULT_POLL_INTERVAL_S}).")
    p.add_argument("--max-wait", type=int, default=DEFAULT_MAX_WAIT_S,
                   help=f"Attesa massima lato client in secondi (default: {DEFAULT_MAX_WAIT_S}).")
    p.add_argument("--overwrite", action="store_true",
                   help="Consente di sovrascrivere un output-json esistente (default: errore).")
    p.add_argument("--dry-run", action="store_true", help="Stampa il payload e termina senza chiamare l'API.")
    return p.parse_args()


def resolve_paths(args: argparse.Namespace) -> None:
    """Completa output_json / log_file / response_md a partire da --tag."""
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


def to_dict(obj) -> object:
    if obj is None:
        return None
    for method in ("model_dump", "to_json_dict", "to_dict"):
        m = getattr(obj, method, None)
        if callable(m):
            try:
                return m()
            except Exception:
                pass
    return None


def consume_stream(stream, log_file: Path | None, start: float) -> tuple[str, list[dict], object]:
    """Itera lo stream SSE. Ritorna (ultimo_status, metadati_eventi, interaction_completed|None).

    Non solleva: se la connessione cade si lascia il lavoro al polling non-stream.
    """
    last_status = "in_progress"
    events_meta: list[dict] = []
    completed_interaction = None
    try:
        for i, event in enumerate(stream):
            et = getattr(event, "event_type", None) or type(event).__name__
            elapsed = int(time.time() - start)
            extra = ""
            status = getattr(event, "status", None)
            if status:
                last_status = status
                extra = f" status={last_status}"
            if et == "interaction.completed":
                inter = getattr(event, "interaction", None)
                if inter is not None:
                    completed_interaction = inter
                    last_status = getattr(inter, "status", last_status) or last_status
                    extra = f" status={last_status} (completed event)"
            elif et == "interaction.created":
                inter = getattr(event, "interaction", None)
                if inter is not None:
                    extra = f" id={getattr(inter, 'id', '?')}"
            elif et == "error":
                extra = f" error={getattr(event, 'message', None) or getattr(event, 'error', '')!r}"
            elif et == "step.delta":
                delta = getattr(event, "delta", None)
                dtype = getattr(delta, "type", "") if delta is not None else ""
                if dtype in ("thought_summary", "text"):
                    text = getattr(delta, "text", "") or ""
                    if text:
                        extra = f" {dtype}={text.strip().splitlines()[0][:80]!r}"
                elif dtype:
                    extra = f" delta={dtype}"
            log(f"INFO event[{i:03d}] elapsed={elapsed}s type={et}{extra}", log_file)
            events_meta.append({"index": i, "elapsed_s": elapsed, "type": et})
    except Exception as exc:
        log(f"WARN stream interrotto dopo {len(events_meta)} eventi: {exc}", log_file)
    return last_status, events_meta, completed_interaction


def extract_output(interaction) -> tuple[str, list[str], list[dict], list[dict]]:
    """Estrae (response_text, thoughts, citations, raw_steps) dallo `steps[]` finale.

    - `model_output`: content[] con type=="text" -> .text + .annotations[] (url_citation)
    - `thought`: summary[] con .text
    Il testo primario e' il **walk manuale** su tutti i content text; l'helper SDK
    `output_text` e' solo fallback perche' tronca in presenza di content non testuali.
    """
    steps = getattr(interaction, "steps", None) or []
    chunks: list[str] = []
    thoughts: list[str] = []
    citations: list[dict] = []
    raw_steps: list[dict] = []

    for step in steps:
        d = to_dict(step)
        if isinstance(d, dict):
            raw_steps.append(d)
        stype = getattr(step, "type", None) or (d.get("type") if isinstance(d, dict) else None)

        if stype == "thought":
            for s in getattr(step, "summary", None) or []:
                text = getattr(s, "text", None)
                if isinstance(text, str) and text.strip():
                    thoughts.append(text)

        elif stype == "model_output":
            for content in getattr(step, "content", None) or []:
                if getattr(content, "type", None) != "text":
                    continue
                text = getattr(content, "text", None)
                if isinstance(text, str):
                    chunks.append(text)
                for ann in getattr(content, "annotations", None) or []:
                    if getattr(ann, "type", None) == "url_citation":
                        citations.append({
                            "start_index": getattr(ann, "start_index", None),
                            "end_index": getattr(ann, "end_index", None),
                            "url": getattr(ann, "url", None),
                            "title": getattr(ann, "title", None),
                        })

    response_text = "\n\n".join(chunks)
    if not response_text.strip():
        helper_text = getattr(interaction, "output_text", None)
        if isinstance(helper_text, str):
            response_text = helper_text
    return response_text, thoughts, citations, raw_steps


def main() -> int:
    env = load_env()
    args = parse_args(env)
    resolve_paths(args)

    # ---- validazione argomenti ----
    sources = [bool(args.prompt_file), bool(args.prompt), bool(args.resume_id)]
    if sum(sources) != 1:
        print("Serve esattamente uno fra --prompt-file, --prompt e --resume-id.", file=sys.stderr)
        return 2
    if not args.output_json:
        print("Serve --output-json oppure --tag (che lo deriva sotto --out-dir).", file=sys.stderr)
        return 2

    prompt = ""
    if args.prompt_file:
        if not args.prompt_file.exists():
            print(f"Prompt file non trovato: {args.prompt_file}", file=sys.stderr)
            return 2
        prompt = args.prompt_file.read_text(encoding="utf-8")
    elif args.prompt:
        prompt = args.prompt
    if prompt and "{{" in prompt:
        print("ATTENZIONE: il prompt contiene ancora segnaposto {{...}} non sostituiti.", file=sys.stderr)
        return 2

    if args.dry_run:
        print(json.dumps({
            "agent": args.agent,
            "agent_config": {"type": "deep-research", "thinking_summaries": args.thinking_summaries},
            "tools": [{"type": "google_search"}],
            "background": True,
            "resume_id": args.resume_id,
            "prompt_chars": len(prompt) or None,
            "prompt_first_400": prompt[:400] or None,
            "output_json": str(args.output_json),
            "log_file": str(args.log_file) if args.log_file else None,
            "response_md": str(args.response_md) if args.response_md else None,
            "poll_interval_s": args.poll_interval,
            "max_wait_s": args.max_wait,
        }, ensure_ascii=False, indent=2))
        return 0

    if args.output_json.exists() and not args.overwrite:
        print(f"Output gia' presente: {args.output_json}. Usa un --tag diverso "
              f"oppure --overwrite se vuoi davvero sovrascrivere.", file=sys.stderr)
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

    # Timeout HTTP largo: lo stream e' long-running.
    client = genai.Client(api_key=api_key, http_options={"timeout": args.max_wait * 1000})
    start = time.time()

    # ---- STEP 1: create (o resume) ----
    if args.resume_id:
        interaction_id = args.resume_id
        log(f"INFO resume id={interaction_id}", args.log_file)
    else:
        try:
            log(f"INFO create agent={args.agent} prompt_chars={len(prompt)}", args.log_file)
            interaction = client.interactions.create(
                input=prompt,
                agent=args.agent,
                agent_config={"type": "deep-research", "thinking_summaries": args.thinking_summaries},
                tools=[{"type": "google_search"}],
                background=True,
            )
        except Exception as exc:
            log(f"FATAL create fallita: {exc}", args.log_file)
            traceback.print_exc(file=sys.stderr)
            return 4
        interaction_id = interaction.id
        log(f"INFO created id={interaction_id} status={getattr(interaction, 'status', 'unknown')}",
            args.log_file)

    # ---- STEP 2: stream ----
    log("INFO opening stream get(id, stream=True)", args.log_file)
    try:
        stream = client.interactions.get(interaction_id, stream=True)
    except Exception as exc:
        log(f"WARN stream get fallito (continuo in poll-only): {exc}", args.log_file)
        stream = None

    events_meta: list[dict] = []
    if stream is not None:
        last_status, events_meta, _ = consume_stream(stream, args.log_file, start)
        log(f"INFO stream chiuso, ultimo status={last_status}, eventi={len(events_meta)}", args.log_file)

    # ---- STEP 3: poll fino a stato terminale (la GET finale serve sempre) ----
    while True:
        elapsed = time.time() - start
        if elapsed > args.max_wait:
            log(f"FATAL max-wait superato ({args.max_wait}s). Il task prosegue server-side: "
                f"riprendilo con --resume-id {interaction_id}", args.log_file)
            return 5
        try:
            interaction = client.interactions.get(interaction_id)
        except Exception as exc:
            log(f"WARN poll error (riprovo fra {args.poll_interval}s): {exc}", args.log_file)
            time.sleep(args.poll_interval)
            continue
        status = getattr(interaction, "status", "unknown") or "unknown"
        steps_len = len(getattr(interaction, "steps", None) or [])
        log(f"INFO poll elapsed={int(elapsed)}s status={status} steps_len={steps_len}", args.log_file)
        if status in TERMINAL_STATES:
            log(f"INFO terminal status={status} elapsed={int(elapsed)}s", args.log_file)
            break
        time.sleep(args.poll_interval)

    final_elapsed = time.time() - start

    # ---- STEP 4: estrazione e artefatti ----
    response_text, thoughts, citations, raw_steps = extract_output(interaction)
    out = {
        "agent": args.agent if not args.resume_id else getattr(interaction, "agent", None),
        "interaction_id": interaction_id,
        "status": getattr(interaction, "status", "unknown"),
        "elapsed_seconds": round(final_elapsed, 1),
        "prompt_chars": len(prompt) or None,
        "response_text": response_text,
        "response_chars": len(response_text),
        "thoughts": thoughts,
        "citations": citations,
        "citations_count": len(citations),
        "unique_domains": sorted({
            (c.get("url") or "").split("/")[2] for c in citations if (c.get("url") or "").count("/") >= 2
        }),
        "raw_steps": raw_steps,
        "events_meta": events_meta,
        "interaction_full": to_dict(interaction),
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
        f"thoughts={len(thoughts)} citations={len(citations)}", args.log_file)

    print(json.dumps({
        "output_json": str(args.output_json),
        "response_md": str(args.response_md) if args.response_md else None,
        "interaction_id": interaction_id,
        "status": out["status"],
        "response_chars": len(response_text),
        "thoughts_count": len(thoughts),
        "citations_count": len(citations),
        "unique_domains_count": len(out["unique_domains"]),
        "elapsed_seconds": round(final_elapsed, 1),
    }, ensure_ascii=False))
    return 0 if out["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

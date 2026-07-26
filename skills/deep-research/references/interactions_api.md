# Riferimento — Interactions API e Deep Research: comportamenti verificati

Note operative pagate sul campo. Servono a leggere i log e a non ri-diagnosticare
problemi gia' risolti dentro `scripts/deep_research.py`.

## Forma della chiamata

```python
interaction = client.interactions.create(
    input=prompt,
    agent="deep-research-max-preview-04-2026",          # da env DEEPRESEARCH_AGENT
    agent_config={"type": "deep-research", "thinking_summaries": "auto"},
    tools=[{"type": "google_search"}],
    background=True,
)
# -> ritorna subito: interaction.id, status="in_progress"
```

| Se ometti | Cosa succede |
|---|---|
| `agent_config` + `tools` | l'interaction viene **creata ma non parte mai**: `updated == created` per sempre, nessun errore, nessun evento. Il sintomo e' un log che resta a `status=in_progress` senza mai crescere di `steps_len`. |
| `background=True` | errore 400: *"background=true is required for agent interactions"*. |

## Ciclo di vita

```
create → in_progress → (terminale)
                       completed | failed | cancelled
                       incomplete | budget_exceeded | requires_action
```

Gli stati della seconda riga sono stati aggiunti nello schema 2026: trattarli come
terminali e' necessario, altrimenti il client resta in polling a vita su un task
che non si muovera' piu'.

## Stream SSE

`client.interactions.get(id, stream=True)` produce eventi discriminati da
`event_type`:

| `event_type` | Contenuto utile |
|---|---|
| `interaction.created` | `event.interaction.id` |
| `interaction.status_update` | `event.status` |
| `step.start` / `step.delta` / `step.stop` | `event.delta.type` ∈ {`thought_summary`, `text`, …} con `.text` — utile per mostrare progresso reale nel log |
| `interaction.completed` | **solo uno scheletro** dell'Interaction (id, status, timestamp): **senza `steps`** |
| `error` | `event.message` / `event.error` |

Due conseguenze non ovvie:

1. **Lo stream puo' chiudersi prima che il task sia terminale.** Non e' un errore: il
   task continua server-side. Serve il fallback a polling non-stream (lo script lo fa).
2. **La GET finale non e' saltabile.** Anche ricevendo `interaction.completed`, gli
   `steps` vanno recuperati con `get(id)` senza stream.

## Estrazione dell'output (schema `steps[]`)

```
step.type == "model_output"  → step.content[]  (Content)
    content.type == "text"   → content.text
                                content.annotations[] → type=="url_citation"
                                                        {url, title, start_index, end_index}
step.type == "thought"       → step.summary[] → {text}
```

**Il testo va concatenato da tutti i content `text` dei `model_output`.** L'helper
SDK `interaction.output_text` si ferma al testo di coda: se in mezzo al report c'e'
un content non testuale (osservato con `image`), restituisce un report **troncato a
meta'** senza alcun errore. Nello script il walk manuale e' la fonte primaria e
`output_text` solo fallback.

## Tempi e costi osservati

- **Floor ~10 minuti** per round, indipendente dalla lunghezza del prompt: un prompt
  di tre righe non e' piu' veloce di uno di tre pagine. Conviene quindi usare prompt
  ricchi.
- Tipico 10-40 minuti; oltre i 45 conviene considerare il round patologico e
  guardare il log.
- Il timeout HTTP del client va impostato largo (`http_options={"timeout": ms}`),
  altrimenti lo stream long-running muore da solo.

## Recovery

L'`interaction_id` e' nella riga `INFO created id=...` del log. Se il processo client
muore (riavvio, chiusura sessione, `--max-wait` scaduto) il task **non** muore:

```bash
python scripts/deep_research.py --resume-id v1_Chd... --tag <stesso-tag>
```

Non rilanciare mai una `create` per un task ancora vivo: paghi due volte e ottieni
due report leggermente diversi da riconciliare.

## Cancel

`interactions.cancel(id)` e' stato osservato rispondere 500. Per abortire davvero:
lascia scadere `--max-wait` lato client e ignora l'artefatto. Il task lato Google
terminera' o andra' in timeout per conto suo.

## Versione SDK

Serve `google-genai >= 2.0.0`. Il breaking change Google "may-2026" ha rimosso lo
schema legacy `outputs[]` in favore di `steps[]`; con SDK 1.x l'API risponde
*"legacy Interactions API schema is no longer supported"*. La firma di `create()`
(`input`/`agent`/`agent_config`/`tools`/`background`) e' invariata fra le due.

## Diagnostica rapida dal log

| Sintomo nel log | Causa probabile |
|---|---|
| `created` poi nessun evento, `steps_len=0` per minuti | `agent_config`/`tools` assenti (non con questo script) o agent inesistente |
| `FATAL create fallita` con 400 | nome agent errato/deprecato, oppure `background` mancante |
| `FATAL create fallita` con 401/403 | chiave assente, scaduta o senza accesso all'agent |
| `WARN stream interrotto dopo N eventi` | normale: subentra il polling |
| terminale `incomplete` / `budget_exceeded` | il task si e' fermato per limiti: il JSON puo' contenere output parziale utile |
| `response_chars` molto piu' basso del previsto | troncamento da `output_text` (non con questo script) o report realmente magro: guarda `citations_count` |
| `citations_count == 0` su un `completed` | il modello non ha cercato: rileggi il prompt, probabilmente non chiedeva fonti |

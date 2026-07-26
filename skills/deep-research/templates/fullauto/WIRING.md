# Wiring del ciclo full-auto in un progetto agentificato

Come innestare `pipeline.py.template` e `research_tools.py.template` in un progetto
che ha gia' un agente (tipicamente prodotto da `vibecoding:agentify`).

Prerequisito non negoziabile: **il progetto deve avere un canale di notifica
proattiva** (Telegram, Slack, email, webhook). Senza quello, un ciclo che dura ore
e nessuno lo sa: non e' automazione, e' un job che sparisce.

## 1. Copia e rinomina

```
skills/deep-research/scripts/deep_research.py     → <progetto>/scripts/deep_research.py
skills/deep-research/scripts/grounded_research.py → <progetto>/scripts/grounded_research.py
skills/deep-research/scripts/env_loader.py        → <progetto>/scripts/env_loader.py
templates/fullauto/pipeline.py.template           → <progetto>/agent/workflows/pipeline.py
templates/fullauto/research_tools.py.template     → <progetto>/agent/tools/research.py
```

Alternativa: lasciare gli script nella skill e puntarli con
`DEEPRESEARCH_SCRIPT=<path>`. Copiarli rende il progetto autonomo dal plugin —
preferibile per un agente che gira su una macchina dove il plugin non e' installato.

## 2. Sostituisci i segnaposto

Cerca `{{` e `TODO durante lo scaffolding` nei due file copiati: **nessuna
occorrenza deve sopravvivere**.

| Segnaposto | Cosa mettere |
|---|---|
| `{{ project_name }}` | nome del progetto |
| `{{ soggetto_default }}` | il soggetto tipico delle ricerche (o `""` se varia sempre) |
| `{{ fonti_primarie }}` | domini che valgono come prova nel dominio |
| `{{ dimensioni_score }}` | le dimensioni di scoring scelte |
| `{{ team_id }}` | id del team/agente che esegue gli step di sintesi |

`PROJECT_ROOT` va allineato a come il progetto risolve la radice (nei template e'
`parents[2]`, corretto per `agent/workflows/pipeline.py`).

## 3. Collega le tre giunture

`pipeline.py` tocca il mondo esterno in tre soli punti, tutti module-level perche' i
test li sostituiscono:

| Funzione | Cosa deve fare | Nota |
|---|---|---|
| `_llm_call(prompt, session_id)` | chiamare l'agente/team del progetto e restituire `(ok, testo)` | l'agente chiamato **deve** avere `read_file`, `write_file`, `web_fetch`: gli step leggono i JSON dei round dal disco, non li ricevono nel prompt |
| `_launch_research(...)` | gia' implementata (detached) | verifica solo il path dello script |
| `_notify(destination, text)` | inviare sul canale del progetto | deve funzionare **anche con il bot in polling spento**: chiamata diretta all'API, non passaggio dal bot |

Gli step di sintesi ricevono un prompt che inizia con
`[PIPELINE <run_id> — step automatico, NON e' un utente in chat.]`. L'agente va
istruito a riconoscere quel marcatore e a rispondere con il solo contenuto
richiesto, senza cortesie da chat.

## 4. Avvia il runner

Dentro il processo dell'agente, dopo aver costruito l'app:

```python
from agent.workflows.pipeline import PipelineRunner
runner = PipelineRunner()
runner.start()   # daemon: muore col processo
```

Al riavvio il runner riprende i run non terminali dal disco e lo dichiara nel log.
Gli stati `wait_*` sono idempotenti; gli stati di sintesi ritentano fino a
`PIPELINE_MAX_ATTEMPTS`, poi il run va in `error` **senza** ulteriori tentativi.

In alternativa, senza processo persistente: `python agent/workflows/pipeline.py serve`
oppure uno scheduler che chiama `advance` su ogni run attivo (vedi il ruolo
`high-level-ops` di `vibecoding:agentify` per le run schedulate, il tool-guard con
autonomy gates L0-L5 e l'audit trail).

## 5. Esponi i comandi all'utente

Minimo indispensabile:

| Comando | Cosa fa |
|---|---|
| avvia ricerca `<tema>` | `new_run(topic, notify_to=<chat>)` — poi ci pensa il runner |
| stato | `list_runs(active_only=True)` + `status_text` |
| annulla `<run_id>` | `cancel(run_id)` — il task Deep Research in volo prosegue server-side, l'artefatto viene ignorato |

`research_tools.py` copre il caso diverso e complementare: **una** ricerca singola
chiesta in chat, senza funnel.

## 6. Variabili d'ambiente

```
GEMINI_API_KEY=                       # obbligatoria
DEEPRESEARCH_AGENT=                   # agent Deep Research corrente
GROUNDED_MODEL=                       # modello della gamba veloce
RESEARCH_OUT_DIR=data/ricerche
DEEPRESEARCH_SCRIPT=scripts/deep_research.py
PIPELINE_POLL_SECONDS=60
PIPELINE_MAX_ROUND_MINUTES=45
PIPELINE_MAX_ATTEMPTS=2
PIPELINE_LLM_TIMEOUT=900
```

Nessun segreto nel repo: `.env` in `.gitignore`, `.env.example` con le chiavi vuote.

## 7. Test minimi prima di considerarlo funzionante

Monkeypatcha le tre giunture e verifica la macchina a stati **senza spendere un
minuto di Deep Research**:

- [ ] `new_run` crea il JSON nello stato iniziale
- [ ] `advance` su `compose_round0` con `_llm_call` che ritorna un prompt valido →
      stato `wait_round0`, prompt scritto su disco, `_launch_research` chiamata
- [ ] `_llm_call` che ritorna testo corto/vuoto → `attempts` incrementa, e al
      raggiungimento di `MAX_ATTEMPTS` lo stato diventa `error`
- [ ] `advance` su `wait_round0` con JSON assente e `started_at` recente → resta in
      attesa; con `started_at` oltre `MAX_ROUND_MINUTES` → `error`
- [ ] `advance` su `wait_round0` con JSON presente e `status=completed` → avanza;
      con `status=incomplete` o 0 caratteri → `error` (mai proseguire su un round
      fallito: il round successivo erediterebbe il vuoto)
- [ ] ogni transizione produce una `notify`
- [ ] dopo un "riavvio" (nuova istanza di runner) i run attivi vengono ripresi
- [ ] `cancel` porta a `cancelled` e il runner lo ignora ai giri successivi

Poi, **una sola volta**, un giro end-to-end reale su un tema piccolo: serve a
verificare i tempi veri e il formato delle notifiche, non la logica.

## Cosa NON automatizzare

- **Azioni irreversibili a valle della ricerca** (inviare una domanda, firmare,
  acquistare, pubblicare, contattare un terzo): la pipeline produce documenti e
  raccomandazioni, si ferma prima dell'atto. Il punto di conferma umana resta.
- **Il retry su fallimento di composizione o di round.** Due tentativi e poi si
  chiede a un umano: un prompt che non convince l'LLM al secondo giro non
  migliorera' al quinto, e ogni giro costa mezz'ora.
- **La scelta del candidato verticale** quando la posta e' alta: in quel caso
  conviene un funnel presidiato (skill Claude Code con gate umani), non full-auto.
- **La cancellazione degli artefatti.** I JSON dei round sono la memoria del ciclo e
  l'unica prova di cosa e' stato letto e quando. Si archiviano, non si eliminano.

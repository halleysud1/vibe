---
name: agentify
description: "Protocollo portabile per trasformare un progetto Claude Code (con skill SKILL.md, MCP server, scripts) in un agente standalone specializzato. 5 fasi — Discovery → Identity Interview → Engine Selection → Roles & Models → Scaffolding → Validation. Engine-agnostic (Agno+AgentOS default; Claude Agent SDK / loop custom alternativi)."
---

# /agentify — Trasforma un progetto Claude Code in agente standalone

Quando l'utente vuole prendere un progetto Claude Code esistente — con skill `SKILL.md`, MCP server, scripts, parametri YAML — e trasformarlo in un **agente che funziona da solo**, senza Claude Code come orchestratore, segui questo protocollo.

L'output è un servizio:
- Carica le skill esistenti via il loro formato standard (Agent Skills, ormai aperto: Claude/Codex/Antigravity/Cursor lo supportano)
- Espone tool MCP esistenti del progetto
- Ha un team multi-LLM (orchestratore + N specialisti) configurabile per ruolo
- Memorizza stato persistente (sessions, longitudinale per entità di dominio)
- Si avvia via cron / chat / event triggers
- Ha boundaries hard, audit trail, propose-and-confirm per azioni rischiose

La skill è **portabile** — funziona su qualsiasi progetto Claude Code in cui sia invocata, adattandosi alla sua struttura.

---

## Quando usare questo protocollo

**Usalo quando** l'utente:
- Ha già un progetto Claude Code maturo (≥ 3 skill, magari 1+ MCP server, scripts Python)
- Vuole un agente che giri **senza** Claude Code (chat indipendente, schedulato, ecc.)
- Vuole specializzazione: l'agente fa una cosa specifica (analisi, supporto, automazione), non è generalista
- Vuole flessibilità modello (Claude/Gemini/DeepSeek/altri) per il loop e per task interni

**Non usarlo** quando:
- Il progetto ha solo 1-2 skill banali → meglio uno script Python tradizionale
- L'utente vuole solo "Claude Code in modalità autonoma" → meglio `claude -p ...` da cron
- L'agente target deve essere un coding tool → meglio OpenCode/Aider/Continue
- L'utente non sa ancora cosa l'agente debba fare → fai prima `/change-request` per chiarire

---

## Fase 0 — Discovery

Capisci il progetto. Esegui lo script automatizzato:

```bash
python .claude/skills/agentify/scripts/discover.py --save
```

Output: `.agentify_discovery.json` nella root del progetto. Contiene:
- `skills`: lista skill (name, description, body length)
- `mcp_servers`: server MCP rilevati (cartelle con `run_server.py`/`server.py` + heuristic MCP)
- `config_files`: parametri YAML (top-level keys)
- `existing_scripts`: scripts standalone già funzionanti
- `python_deps`: dipendenze in `requirements.txt`
- `domain_hints`: heading da `CLAUDE.md`

Se l'inventario è povero (0 skill, no MCP, no scripts), **non procedere**: il progetto non è abbastanza maturo per `agentify`. Suggerisci di costruire prima qualche skill manualmente.

Mostra il report all'utente prima di Fase 1.

---

## Fase 1 — Identity Interview

Determina l'identità dell'agente con domande mirate. È la fase più importante: senza identità chiara, lo scaffolding genera boilerplate generico.

Usa **AskUserQuestion** in batch (max 4 domande per call). Suggerimento di organizzazione:

### Batch 1 — Identità + utenti + triggers + output

1. **Identità**: cosa fa l'agente? (Analista / Coach / Assistente operativo / Hybrid / altro)
2. **Utente primario**: solo amministratore / multi-ruolo / self-service tutti / sistema autonomo (background)
3. **Triggers** (multiselect): chat / schedulato / eventi / CLI on-demand
4. **Output principale** (multiselect): file (md/json) / azioni in sistemi esterni / notifiche / chat conversazionale

### Batch 2 — Autonomia + cadenza + memoria + boundaries

5. **Autonomia di scrittura** su sistemi esterni: piena / propose-and-confirm / solo-proposta / read-only
6. **Cadenza** (se schedulato): giornaliero / settimanale / mensile / ad-hoc
7. **Memoria**: stateless / dati storici / conversazionale persistente / longitudinale per entità
8. **Boundaries hard** (multiselect): cosa NON deve MAI fare (modificare X, accedere a Y, mandare verso esterni Z)

### Batch 3 — Privacy + dettagli operativi

9. **Privacy**: quali dati sensibili sono off-limits in lettura/scrittura
10. **Eventi specifici** (se event-driven): quali eventi trigger e con che condizioni
11. **Audit trail**: required / opzionale → dove viene salvato

→ **Output**: bozza `agent.yaml` (vedi `templates/agent.yaml.template`).

### Mostra la bozza all'utente

Mostra il manifesto, chiedi conferma o correzioni. **Itera finché l'utente si riconosce nella sintesi.** Non avanzare con un'identità ambigua.

### Red flag — bias addittivo

Se l'identità che emerge è "fa di tutto un po'", probabilmente non è un buon candidato per `agentify`. Un agente vale solo se è **specialista**. Se serve generalismo, dì all'utente che resta meglio Claude Code.

---

## Fase 2 — Engine Selection

Mostra trade-off tra engine candidati basati sui requisiti emersi:

| Engine | Quando ha senso |
|---|---|
| **Agno + AgentOS** | Default. Multi-trigger (cron+chat+events), memoria persistente, multi-modello, UI inclusa. |
| **Claude Agent SDK + custom service** | Pieno controllo, no framework lock-in. Più LOC ma semplicità concettuale. |
| **Loop a mano (200 LOC Python)** | Caso semplice (singolo trigger, no UI), zero dipendenze pesanti. |
| **Sub-agent in Claude Code** | Se l'agente deve girare DENTRO Claude Code (non standalone) → questa skill non è la soluzione, usa subagents. |

### Filtri automatici

- Multi-modello richiesto → escludi Claude Agent SDK (Anthropic-only) → Agno o custom
- Solo cron + script semplice → loop a mano sufficiente
- Multi-trigger + memoria persistente + UI chat → Agno fortemente raccomandato

Mostra la raccomandazione + alternative + razionale tabellare. Conferma utente.

**v1 di questa skill scaffolda solo Agno+AgentOS.** Le altre opzioni sono documentate ma non automatizzate (utente le costruirà a mano se sceglie quelle).

---

## Fase 3 — Roles & Models

Identifica i ruoli specialistici dell'agente. Pattern comune (5 ruoli, ma adatta al dominio):

| Ruolo | Compito tipico |
|---|---|
| Orchestrator | Team leader: decide quale skill invocare, coordina specialisti |
| Analyzer | Reasoning su dati strutturati, applica regole, calcola metriche |
| Writer | Generazione testo lungo (report, narrativa) — spesso modello fast/cheap |
| Coach (o Generator) | Produce proposte/azioni a partire da insight |
| Critic | Second opinion indipendente sulle proposte prima dell'esecuzione |

**Adatta i ruoli al dominio**:
- Agente di supporto cliente: orchestrator + searcher + responder + critic
- Agente di automazione: orchestrator + planner + executor
- Agente di ricerca: orchestrator + searcher + summarizer + writer

Per ogni ruolo, chiedi all'utente:
- **Descrizione** (1-2 frasi)
- **Capability richieste al modello** (es. "tool calling solido", "italiano fluente", "second opinion indipendente")
- **Default model**: il modello consigliato
- **Candidates**: lista di alternative per A/B test (utente sperimenterà)

→ **Output**: sezione `models.roles` del manifesto.

---

## Fase 4 — Scaffolding

Genera i file. Per Agno+AgentOS produce questa struttura nel progetto target:

```
agent/
├── agent.yaml                    # manifesto (output Fasi 1-3)
├── agent_system_prompt.md        # identità + behavior in linguaggio naturale
├── _models.py                    # model factory per i provider
├── skill_loader.py               # legge .claude/skills/*/SKILL.md
├── main.py                       # entry-point Agno (Team + AgentOS)
├── roles/
│   ├── orchestrator.py           # ORCHESTRATOR_INSTRUCTIONS (per team leader)
│   ├── <specialist1>.py          # build_<specialist1>(cfg, base_instr, tools)
│   └── ...
├── workflows/
│   ├── <scheduled_workflow>.py
│   └── propose_confirm.py        # se autonomy = propose-and-confirm
└── tests/
    ├── test_smoke.py
    └── bench_models.py
deploy/
├── Dockerfile.agent
├── docker-compose.yml
└── runbook.md
.env.example
audit_log/proposals/              # solo se propose-and-confirm
```

### Come renderizzare i template

I template sono in `.claude/skills/agentify/templates/`. Hanno placeholder Jinja2-style con i valori dal manifesto:
- `{{ identity.name }}`
- `{{ models.roles.orchestrator.default }}`
- `{% for skill in skills.imported %}{{ skill }}{% endfor %}`

**Approccio raccomandato (manuale, trasparente)**: leggi ogni template, sostituisci a mano i placeholder con i valori del manifesto, scrivi il file risultante. Più verboso ma chiaro per l'utente.

### Aggiorna requirements.txt e .env.example del progetto

- `requirements.txt`: aggiungi le dipendenze dell'engine + provider LLM scelti
  - Per Agno: `agno`, `anthropic`, `google-genai`, `deepseek`, `openai`, `apscheduler`, `python-dotenv`, `pyyaml`, `pytest`
  - Per interfaccia Telegram (opzionale): `pyTelegramBotAPI`
- `.env.example`: chiavi API per i modelli scelti + variabili runtime AgentOS + variabili dominio
  - Se scaffoldi Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS` (whitelist user_id)

### File template chiave

| Template | Variabilità |
|---|---|
| `agent.yaml.template` | ALTA — riflette identità completa |
| `agent_system_prompt.md.template` | ALTA — riflette identità, scope, boundaries |
| `agno/main.py.template` | MEDIA — cambiano import + nome ruoli |
| `agno/role.py.template` | MEDIA — instructions specifiche per ruolo |
| `agno/_models.py.template` | BASSA — può essere copia identica |
| `agno/skill_loader.py.template` | BASSA — può essere copia identica |
| `agno/test_smoke.py.template` | MEDIA — cambiano nomi ruoli |
| `agno/bench_models.py.template` | MEDIA — cambiano BENCHMARK_TASKS per ruolo |
| `agno/workflow_*.py.template` | ALTA — molto specifico al dominio |
| `agno/Dockerfile.agent.template` | BASSA — può essere copia identica |
| `agno/runbook.md.template` | MEDIA — cambiano comandi specifici |
| `agno/telegram_polling.py.template` | BASSA — quasi-copia, parametrizza solo team_id e env vars |
| `agno/telegram_setup.md` | BASSA — copia diretta come guida nel progetto target |

### Interfaces & chat layer (opzionale)

L'agente è raggiungibile via REST API. Per utenti reali serve quasi sempre un'interface
chat consumer-facing. Pattern raccomandato: **Telegram**.

| Modalità | Quando | Cosa scaffolda |
|---|---|---|
| **Polling bot standalone** (default dev) | localhost, no tunnel pubblico | `agent/interfaces/telegram_polling.py` |
| **Native Agno interface** (default prod) | server con URL pubblico + webhook | attivazione condizionale in `main.py` |

Pattern Agno: `agno.os.interfaces.{telegram, slack, whatsapp, a2a, agui}`. v1.1 scaffolda
Telegram; le altre interface seguono lo stesso schema (sostituibili dall'utente).

**Sicurezza** (correlato al boundary "MAI output verso esterni"): chi può scrivere al bot
accede all'agente. Whitelist via `TELEGRAM_ALLOWED_USERS=<user_id1,user_id2>` nel polling
bot. Per webhook nativo, valutare auth gateway (bearer token / IP allowlist).

**Setup Telegram (step-by-step)**:
1. `@BotFather` su Telegram → `/newbot` → ottieni token
2. Aggiungi `TELEGRAM_BOT_TOKEN=...` a `.env`
3. Polling (dev): `python -m agent.interfaces.telegram_polling` (AgentOS già up)
4. Webhook (prod): URL pubblico + setWebhook → attivazione automatica in `main.py`

Vedi `templates/agno/telegram_setup.md` per la guida copiabile.

---

## Fase 5 — Validation & Calibration

### 5.1 Smoke test (no API calls)

```bash
pytest agent/tests/test_smoke.py -v
```

Verifica: manifest carica, skill loader trova le skill del progetto, model factory mappa i provider, build_team() istanzia, build_agentos() costruisce.

**Tutti devono passare prima di chiamate LLM reali.**

### 5.2 Avvio AgentOS

```bash
python -m agent.main
# → http://localhost:7777
```

Conversazione di test in chat: "ciao, chi sei?" — l'agente dovrebbe rispondere con la sua identità definita nel manifesto.

### 5.3 Bench modelli (consuma poco — 1 task × N candidati per ruolo)

```bash
python -m agent.tests.bench_models --role <role>
```

Confronta latenza + lunghezza risposta tra candidati. La qualità richiede review umana sui contenuti.

### 5.4 Workflow live (più costoso)

Esegui il workflow su environment di staging (mai produzione al primo run). Verifica:
- File output prodotti correttamente
- Audit trail popolato
- Propose-and-confirm queue popolata se applicabile
- Nessuna scrittura inattesa su sistemi esterni

### 5.5 Iterazione

- Tono sbagliato → raffina `agent_system_prompt.md`
- Proposte cattive → raffina le instructions del ruolo che le genera (es. `coach.py`)
- Tool calling errato → cambia modello (default → candidate alternativo)
- Boundaries non rispettate → **rinforza** il system prompt, NON rilassare i confini

### 5.6 Test interfaccia Telegram (se scaffoldata)

```bash
# In altro terminale (AgentOS deve essere up):
python -m agent.interfaces.telegram_polling
```

Da Telegram: cerca il bot per username, manda `/start`. Verifica risposta. Se hai
settato `TELEGRAM_ALLOWED_USERS`, prova da un account non in whitelist → deve rifiutare.

---

## Anti-pattern

### A1. Boilerplate generico (skill addittiva)

Se generi codice che non riflette l'identità specifica del progetto, l'agente sarà generico. Investi in Fase 1 (Identity Interview): è dove il valore nasce.

### A2. Multi-engine al primo go

Non scaffoldare entrambi Agno e Claude Agent SDK al primo passaggio. Scegli uno, calibra, poi se serve aggiungi l'altro.

### A3. Skip dei boundaries

Le boundaries hard non sono opzionali. Senza di esse, l'agente in autonomia può fare danni reali (cancellare dati, mandare comunicazioni inopportune, esporre informazioni sensibili). Sempre presenti, sempre nel system prompt, sempre testate.

### A4. Modelli "decisi" prima del primo run

Non promettere che "Claude è il migliore per orchestrator". Le scelte modello vanno **provate** col bench, non assertite. Il manifesto cattura `default` + `candidates`, l'utente sperimenta.

### A5. Saltare il Critic per "semplicità"

Quando l'agente fa azioni reali (write su sistemi, creare contenuti pubblici), il Critic è la differenza tra "agente affidabile" e "agente da incidente". Sempre presente nel team se autonomy != read-only.

### A6. Templates non rinominati

Un file lasciato come `main.py.template` invece di `main.py` è un bug latente. Tutti i template DEVONO essere renderizzati e rinominati. La presenza di file `.template` nel progetto target è sintomo di scaffolding incompleto.

---

## Checklist auto-verifica

Prima di dichiarare "fatto":

1. Ho fatto Fase 1 con domande mirate, non assunto un'identità?
2. Ho mostrato il manifesto all'utente per validazione?
3. Ho discusso engine + razionale con l'utente, non scelto unilateralmente?
4. I ruoli che ho proposto riflettono il dominio specifico?
5. I modelli hanno default + candidates per A/B testing?
6. I template sono renderizzati con valori reali, niente `{{ placeholder }}` nei file finali?
7. Ho lanciato smoke test e ottenuto pass?
8. Ho documentato il deploy in `runbook.md`?
9. Le boundaries hard sono nel system prompt + nelle instructions del Critic?
10. L'audit trail è scritto da qualche parte?

Se anche solo una risposta è "no" o "forse", torna indietro e correggi.

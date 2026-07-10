---
name: agentify
description: "Protocollo portabile per trasformare un progetto Claude Code (con skill SKILL.md, MCP server, scripts) in un agente standalone specializzato. 6 fasi — Discovery → Identity Interview → Engine Selection → Roles & Models → Tool Layer & Autonomy → Scaffolding → Validation. Engine-agnostic (Agno+AgentOS default). Include ruoli tool-empowered: coding-agent con harness completo (tool editing/shell/LSP derivati da opencode + loop di verifica su definition-of-done, checkpoint/rollback git, scout a contesto separato, repo map, eval su golden task), high-level-ops schedulato con autonomy gates L0-L5, tool-guard, runbook, audit trail, propose-and-confirm."
---

# /agentify — Trasforma un progetto Claude Code in agente standalone

Quando l'utente vuole prendere un progetto Claude Code esistente — con skill `SKILL.md`, MCP server, scripts, parametri YAML — e trasformarlo in un **agente che funziona da solo**, senza Claude Code come orchestratore, segui questo protocollo.

L'output è un servizio:
- Carica le skill esistenti via il loro formato standard (Agent Skills, ormai aperto: Claude/Codex/Antigravity/Cursor lo supportano)
- Espone tool MCP esistenti del progetto
- Ha un team multi-LLM (orchestratore + N specialisti) configurabile per ruolo
- Può includere **ruoli tool-empowered**: un `coding-agent` con tool reali (edit, shell, LSP) e/o un `high-level-ops` per operazioni schedulate — entrambi governati da autonomy gates e tool-guard
- Memorizza stato persistente (sessions, longitudinale per entità di dominio)
- Si avvia via cron / chat / event triggers
- Ha boundaries hard, audit trail, propose-and-confirm per azioni rischiose

La skill è **portabile** — funziona su qualsiasi progetto Claude Code in cui sia invocata, adattandosi alla sua struttura.

> **Storia (4.0.0)**: questa skill ha assorbito le ex skill `agentic-ops-daemon` (daemon/scheduler operativi) e `claude-session-supervisor` (gating multi-layer con audit). I loro pattern vivono qui come ruolo `high-level-ops` e come **tool-guard** dei ruoli tool-empowered. Non esistono più come skill separate.

---

## Quando usare questo protocollo

**Usalo quando** l'utente:
- Ha già un progetto Claude Code maturo (≥ 3 skill, magari 1+ MCP server, scripts Python)
- Vuole un agente che giri **senza** Claude Code (chat indipendente, schedulato, ecc.)
- Vuole specializzazione: l'agente fa una cosa specifica (analisi, supporto, automazione, coding), non è generalista
- Vuole flessibilità modello (Claude/Gemini/DeepSeek/altri) per il loop e per task interni
- Vuole che l'agente **modifichi davvero codice/file** → ruolo `coding-agent` (tool layer derivato da opencode)
- Vuole **operazioni schedulate disciplinate** (check, refresh dati, report, proposte) → ruolo `high-level-ops`

**Non usarlo** quando:
- Il progetto ha solo 1-2 skill banali → meglio uno script Python tradizionale
- L'utente vuole solo "Claude Code in modalità autonoma" → meglio `claude -p ...` da cron
- L'utente non sa ancora cosa l'agente debba fare → fai prima `/change-request` per chiarire

### Routine nativa Claude Code vs agente standalone (decidere PRIMA di Fase 1)

Claude Code copre nativamente molta automazione (scheduled tasks/routine cloud,
workflow multi-agente, subagent, hooks). agentify vale dove il nativo non
arriva — dichiaralo esplicitamente all'utente:

| Requisito | Routine/workflow nativi | agentify |
|---|:---:|:---:|
| Automazione interna schedulata (check, report, refresh) per chi HA Claude Code | ✅ più semplice e mantenuto | ⚠️ overkill |
| Utenti finali TERZI senza Claude Code (chat Telegram, servizio) | ❌ | ✅ |
| Multi-modello per costo (GLM/Gemini/DeepSeek per ruolo) | ❌ | ✅ |
| Servizio always-on con memoria longitudinale di dominio | parziale | ✅ |
| Sviluppo software open-ended | ✅ superiore (harness maturo) | ❌ usa Claude Code |
| Manutenzione codice delimitata dentro una pipeline autonoma | — | ✅ coding-agent + harness |

Se tutte le esigenze dell'utente cadono nella prima colonna, fermati e
suggerisci le routine native: è il consiglio onesto.

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
- `os`: sistema operativo rilevato (decide `.ps1` vs `.sh` per gli script di wake)
- `sensitive_paths`: path sensibili (`.env*`, segreti, config) → seed della denylist del tool-guard

Se l'inventario è povero (0 skill, no MCP, no scripts), **non procedere**: il progetto non è abbastanza maturo per `agentify`. Suggerisci di costruire prima qualche skill manualmente.

Mostra il report all'utente prima di Fase 1.

---

## Fase 1 — Identity Interview

Determina l'identità dell'agente con domande mirate. È la fase più importante: senza identità chiara, lo scaffolding genera boilerplate generico.

Usa **AskUserQuestion** in batch (max 4 domande per call). Suggerimento di organizzazione:

### Batch 1 — Identità + utenti + triggers + output

1. **Identità**: cosa fa l'agente? (Analista / Coach / Assistente operativo / Coding agent / Hybrid / altro)
2. **Utente primario**: solo amministratore / multi-ruolo / self-service tutti / sistema autonomo (background)
3. **Triggers** (multiselect): chat / schedulato / eventi / CLI on-demand
4. **Output principale** (multiselect): file (md/json) / modifiche a codice / azioni in sistemi esterni / notifiche / chat conversazionale

### Batch 2 — Autonomia + cadenza + memoria + boundaries

5. **Autonomia di scrittura** su file e sistemi esterni: piena / propose-and-confirm / solo-proposta / read-only (mappa sui livelli L0-L5, vedi Fase 3.5)
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

**Questa skill scaffolda solo Agno+AgentOS.** Le altre opzioni sono documentate ma non automatizzate (utente le costruirà a mano se sceglie quelle).

---

## Fase 3 — Roles & Models

Identifica i ruoli specialistici dell'agente. Pattern comune (5 ruoli base, ma adatta al dominio):

| Ruolo | Compito tipico |
|---|---|
| Orchestrator | Team leader: decide quale skill invocare, coordina specialisti |
| Analyzer | Reasoning su dati strutturati, applica regole, calcola metriche |
| Writer | Generazione testo lungo (report, narrativa) — spesso modello fast/cheap |
| Coach (o Generator) | Produce proposte/azioni a partire da insight |
| Critic | Second opinion indipendente sulle proposte prima dell'esecuzione |

### Archetipi tool-empowered (nuovi in 4.0.0)

Due archetipi con accesso al **tool layer** (Fase 3.5). Sono ruoli del team come gli altri — girano sul modello scelto in questa fase, dentro il ciclo ReAct dell'engine:

| Archetipo | Compito | Tool layer |
|---|---|---|
| **coding-agent** | Modifica davvero il codice del progetto col **ciclo orienta → checkpoint → edita → verifica**: `repo_map` per orientarsi, delega ricognizione allo Scout, edit a batch, `verify()` dopo ogni batch, checkpoint/rollback git. | Completo + harness: `repo_map`, fs, `shell`, `verify`, `gitops`, `lsp`, `todo`, `webfetch` |
| **scout** | Ricognizione a contesto separato per il coding-agent: search/read/sintesi su modello fast/cheap, restituisce solo ciò che serve (path:riga, firme, convenzioni). Il contesto del coder resta pulito. Deriva dal tool `task` di opencode. | Read-only: `repo_map`, `project_context`, `read`, `glob`, `grep`, `lsp` |
| **high-level-ops** | Operatore disciplinato schedulato: health check, refresh dati idempotenti, report, memo, proposte. Erede dell'ex skill `agentic-ops-daemon`. | Ridotto: `read`, `glob`, `grep`, `shell` (comandi CLI del progetto), `write` (solo su output dir), `verify` |

**Il giudizio resta del modello del ruolo, scelto nell'intervista.** Il tool layer fornisce capacità, non decisioni: la valutazione di cosa fare la fa il modello del ruolo (con il Critic come second opinion), non uno strato esterno.

**Adatta i ruoli al dominio**:
- Agente di supporto cliente: orchestrator + searcher + responder + critic
- Agente di automazione: orchestrator + high-level-ops + critic
- Agente di ricerca: orchestrator + searcher + summarizer + writer
- Agente di manutenzione codice: orchestrator + scout + coding-agent + critic

Per ogni ruolo, chiedi all'utente:
- **Descrizione** (1-2 frasi)
- **Capability richieste al modello** (es. "tool calling solido", "italiano fluente", "second opinion indipendente"; per coding-agent: "agentic coding forte, patch precise")
- **Default model**: il modello consigliato
- **Candidates**: lista di alternative per A/B test (utente sperimenterà)

### Default model raccomandati (baseline 4.0.x)

Punto di partenza per l'intervista — restano default+candidates da **provare col
bench** (anti-pattern A4), non verità assolute:

| Ruolo | Default | Candidates |
|---|---|---|
| Orchestrator | `gemini-3.1-pro-preview` | `glm-5.2` |
| Analyzer | `gemini-3.1-pro-preview` | `glm-5.2` |
| Writer | `gemini-3.5-flash` | — |
| Critic | `deepseek-v4-pro` | — |
| coding-agent (il "coder") | `glm-5.2` | `gemini-3.1-pro-preview` |
| scout | `gemini-3.5-flash` | — |
| high-level-ops | `gemini-3.5-flash` | `glm-5.2` |

Per il coder la scelta tra default e candidate si fa **coi numeri**: golden
task in `eval_coder` (Fase 5.5), non a sensazione.

Env attese: `GOOGLE_API_KEY`, `DEEPSEEK_API_KEY`, `ZHIPU_API_KEY` (GLM via
endpoint OpenAI-compatible di Z.ai — vedi `_models.py`).

### Reasoning policy: decide l'Orchestrator

Il livello di ragionamento (`low`/`medium`/`high`) NON è fissato per ruolo: lo
sceglie l'**Orchestrator task per task** al momento della delega (manifesto:
`models.reasoning_policy: orchestrator`). Il factory `resolve_model(id,
reasoning=...)` traduce il livello nel parametro del provider (thinking budget
per Gemini/Claude, `reasoning_effort` per GPT, thinking on/off per
DeepSeek/GLM), con fallback pulito se il provider non lo supporta.

→ **Output**: sezione `models.roles` (+ `models.reasoning_policy`) del manifesto.

---

## Fase 3.5 — Tool Layer & Autonomy

Questa fase si esegue **solo se il team include almeno un ruolo tool-empowered** (coding-agent o high-level-ops). Altrimenti salta a Fase 4.

### Il tool layer (harvest da opencode)

Il tool layer è un set di tool Python per il ciclo ReAct, **derivato da opencode** (https://github.com/anomalyco/opencode, MIT): ne adattiamo implementazioni, prompt di descrizione dei tool e modello di permessi. opencode è la **fonte** (repository di conoscenza, risorse e tool), non una dipendenza runtime: non viene installato né invocato.

| Tool | Derivato da (opencode) | Scopo |
|---|---|---|
| `read` | `tool/read.ts` + `read.txt` | Lettura file con range di righe e truncation |
| `glob` | `tool/glob.ts` + `glob.txt` | Pattern matching su file |
| `grep` | `tool/grep.ts` + `grep.txt` | Ricerca contenuti (ripgrep se disponibile, fallback Python) |
| `edit` | `tool/edit.ts` + `edit.txt` | Sostituzione esatta di stringhe in file |
| `write` | `tool/write.ts` | Scrittura/creazione file |
| `apply_patch` | `tool/apply_patch.ts` + `.txt` | Applicazione patch multi-file |
| `shell` | `tool/shell.ts` | Esecuzione comandi con timeout e output cap |
| `lsp` | `tool/lsp.ts` + `lsp.txt` | Code intelligence: diagnostica, definizioni, riferimenti (se un LSP server è disponibile per il linguaggio del progetto) |
| `todo` | `tool/todo.ts` + `todowrite.txt` | Task list interna del ruolo per lavori multi-step |
| `webfetch` | `tool/webfetch.ts` + `.txt` | Fetch documentazione/risorse esterne (se consentito dai boundaries) |
| ruolo `scout` | `tool/task.ts` + `task.txt` | Delega di ricognizione a contesto separato (re-espressa come ruolo del team Agno) |

**Harness del coding-agent (4.1.0)** — tool NON derivati da opencode, nostri per design (sono la struttura del loop, non capacità):

| Tool | Scopo |
|---|---|
| `verify` | Esegue la **definition-of-done** del progetto (test, lint, build — comandi con exit code, dichiarati nel manifesto). Il coder DEVE chiamarlo dopo ogni batch di edit e iterare fino a VERDE, o fermarsi dopo `max_verify_cycles` |
| `gitops` (`git_checkpoint` / `git_diff` / `git_revert_to_checkpoint` / `git_propose_diff`) | Checkpoint prima/dopo ogni batch su branch `agent/*` (mai main, mai push by-construction); rollback pulito quando verify resta rosso; propose-and-confirm col **diff reale** in OUTBOX |
| `repo_map` | Mappa compatta file → simboli (regex-based, zero dipendenze) per orientarsi senza saturare il contesto |
| `project_context` (4.3.0) | Orientamento sulla **storia decisionale**: in una chiamata, stato corrente + entry del decision journal pertinenti per keyword + ADR pertinenti. Obbligatorio nel passo 1 del ciclo: il codice circostante NON è una specifica affidabile (vedi A13) |
| `log_decision` (4.3.0) | Chiusura del loop: appende la change al decision journal del progetto (cosa/perché/come verificata). Test verdi senza journal entry = lavoro incompleto |

### Quality gates & anti-degrado (4.2.0)

`verify` cattura "rotto"; L0-L5 gated le azioni. Il **debito tecnico a velocità
macchina** si accumula invece quando tutto è verde e la qualità cala in
silenzio. Contromisure strutturali:

1. **Quality gates nella definition-of-done**: lint come check `required` (non
   informativo) e almeno una **metrica non-decrescente** (`"metric":
   "non_decreasing"`, es. coverage) — baseline persistita in
   `docs/ops/.metrics.json`; se la metrica scende il check fallisce anche con
   exit code 0. Valuta anche un budget di complessità (es. `radon`/`xenon`).
2. **Tetto ai diff proposti** (`max_propose_diff_lines`, default 400): un diff
   irrevisionabile verrebbe approvato senza lettura — oltre soglia
   `git_propose_diff` rifiuta e impone batch più piccoli.
3. **Churn detector nel guard** (`churn_limit`, default 5): lo stesso file
   modificato troppe volte nella stessa run = thrashing → DENY con istruzione
   di fermarsi/rollback (rule `churn_detector` in AUDIT).
4. **Revisione OUTBOX con staleness** (nel RUNBOOK): cadenza dichiarata,
   proposte PENDING oltre `outbox_stale_days` → escalation; regola "leggi il
   diff, non il titolo".

Limite onesto da dichiarare all'utente: questi gate riducono la probabilità
del degrado silenzioso, non la azzerano — il tetto di qualità resta quello del
modello del coder (misuralo con `eval_coder`), e il propose-and-confirm vale
quanto l'umano che lo rivede.

**Prompt harvest**: i prompt di sistema del ruolo coding-agent derivano dalle varianti per famiglia di modello di opencode (`session/prompt/anthropic.txt`, `gemini.txt`, `gpt.txt`, `default.txt`, `plan.txt`). Lo scaffolding sceglie la variante coerente col modello selezionato in Fase 3 e la fonde con l'identità del manifesto. Le regole di delega coder→scout derivano da `task.txt` (prompt dettagliato, dichiarare esattamente cosa deve tornare, research-only esplicito, niente duplicazione del lavoro delegato).

**Provenance**: ogni harvest è tracciato in `docs/OPENCODE_HARVEST.md` nel progetto target (cosa è stato preso, da quale commit/versione, con quali adattamenti, attribuzione MIT). Periodicamente si ricontrolla la repo upstream per novità: il doc è la baseline del confronto.

### Autonomy gates L0-L5

Classifica ogni capacità del ruolo tool-empowered **prima** dello scaffolding:

| Livello | Consentito senza approvazione? | Esempi |
|---|---:|---|
| L0 read-only | Sì | `read`, `glob`, `grep`, `lsp` diagnostics, health check |
| L1 refresh idempotente | Sì, se configurato | refresh dati, snapshot, indici locali |
| L2 analisi/report | Sì | report, memo, backtest, todo interni |
| L3 proposta | Sì, ma output solo proposta | patch proposta in OUTBOX, shortlist, policy draft |
| L4 modifica controllata | Solo con gate (propose-and-confirm o allowlist esplicita) | `edit`/`write`/`apply_patch` su codice, config persistenti |
| L5 azione esterna rischiosa | Mai unattended | push, pagamenti, delete dati, email verso esterni |

Regola: se non sai classificare un'azione, trattala come L4.

Per un **coding-agent interattivo** (chat, umano presente) L4 può essere `allow` su path del progetto; per lo stesso ruolo **schedulato/unattended** L4 deve essere propose-and-confirm. Il livello è per-trigger, non solo per-ruolo.

### Permessi per tool (modello opencode: allow / ask / deny)

Ogni tool del layer ha un permesso a tre stati, con pattern per `shell`:

```yaml
tools:
  permissions:
    read: allow
    glob: allow
    grep: allow
    lsp: allow
    edit: propose        # allow | propose | deny  (propose = propose-and-confirm via OUTBOX)
    write:
      "reports/**": allow
      "*": propose
    apply_patch: propose
    shell:
      "git status": allow
      "pytest*": allow
      "git push*": deny
      "rm *": deny
      "*": propose
    webfetch: deny
```

(`ask` di opencode diventa `propose` nel contesto unattended: la richiesta di approvazione è asincrona via OUTBOX, non un prompt bloccante.)

### Tool-guard (erede dell'ex claude-session-supervisor)

Layer di enforcement attorno all'esecuzione di ogni tool call dei ruoli tool-empowered, in ordine di costo:

1. **Kill-switch**: counter di tool call per run; oltre `kill_switch_limit` (default 200) → DENY hard + emergency log. Rete di sicurezza contro loop runaway.
2. **Denylist statica**: baseline sempre presente (path sensibili da discovery: `.env*`, segreti; comandi distruttivi: `rm`, `git push`, delete massivi) + `PROJECT_DENYLIST` estendibile dall'utente.
3. **Allowlist statica**: le strade autorizzate della mission (path/pattern noti). Deve coprire l'80-90% dei tool call attesi.
4. **Propose-and-confirm**: ciò che non è né deny né allow e ha permesso `propose` → scritto in `OUTBOX.md` come proposta, non eseguito. Un umano (o un run successivo dopo conferma) la applica.

Più: **audit trail append-only** (`AUDIT.md`: ogni decisione con timestamp, tool, regola che ha deciso), **lock anti-concorrenza** (due run schedulate non si sovrappongono), **UTF-8 forzato** su Windows.

Il tool-guard è codice deterministico dentro il tool layer (`tools/guard.py`), non un processo esterno: niente secondo LLM, niente hook di Claude Code. Il giudizio contestuale è del modello del ruolo + Critic; il guard fa enforcement meccanico dei confini.

### Ops runbook (erede dell'ex agentic-ops-daemon)

Se il team include `high-level-ops` (o un coding-agent schedulato), scaffolda l'interfaccia ops standard:

```text
docs/ops/RUNBOOK.md     protocollo operativo human-readable: profili, task ammessi, recovery
docs/ops/STATE.md       stato corrente osservabile
docs/ops/TASK_QUEUE.md  mission/richieste pending per il ruolo
docs/ops/LAST_RUN.md    ultimo run: durata, esito, errori
docs/ops/OUTBOX.md      proposte in attesa di conferma (propose-and-confirm)
docs/ops/AUDIT.md       log append-only sintetico delle decisioni del guard
```

Non usare questi file come database primario: sono journal umani, non storage transazionale.

Ogni task schedulato deve essere: non interattivo, idempotente o dichiaratamente read-only, loggato, testabile localmente, capace di fallire loud con exit code non-zero.

---

## Fase 4 — Scaffolding

Genera i file. Per Agno+AgentOS produce questa struttura nel progetto target:

```
agent/
├── agent.yaml                    # manifesto (output Fasi 1-3.5)
├── agent_system_prompt.md        # identità + behavior in linguaggio naturale
├── _models.py                    # model factory per i provider
├── skill_loader.py               # legge .claude/skills/*/SKILL.md
├── main.py                       # entry-point Agno (Team + AgentOS)
├── roles/
│   ├── orchestrator.py           # ORCHESTRATOR_INSTRUCTIONS (per team leader)
│   ├── coding_agent.py           # se ruolo coding-agent: instructions da prompt harvest + ciclo verify
│   ├── scout.py                  # se coding-agent: ricognizione a contesto separato
│   ├── high_level_ops.py         # se ruolo high-level-ops
│   ├── <specialist1>.py          # build_<specialist1>(cfg, base_instr, tools)
│   └── ...
├── tools/                        # solo se ruoli tool-empowered
│   ├── __init__.py               # registry: toolset per ruolo (CODING_AGENT/SCOUT/HIGH_LEVEL_OPS)
│   ├── guard.py                  # tool-guard: kill-switch, deny/allow, propose, audit, lock
│   ├── fs.py                     # read, glob, grep, edit, write, apply_patch
│   ├── shell.py                  # shell con timeout, output cap, pattern permissions
│   ├── verify.py                 # definition-of-done runner (loop di verifica)
│   ├── gitops.py                 # checkpoint/diff/rollback su branch agent/*, propose diff
│   ├── repomap.py                # mappa file → simboli
│   ├── lsp.py                    # bridge LSP (diagnostica, definizioni, riferimenti)
│   └── tasklist.py               # todo interno per lavori multi-step
├── workflows/
│   ├── <scheduled_workflow>.py
│   └── propose_confirm.py        # se autonomy = propose-and-confirm
└── tests/
    ├── test_smoke.py
    ├── test_guard.py             # se tool layer: deny/allow/propose/kill-switch
    ├── bench_models.py
    ├── eval_coder.py             # se coding-agent: golden task a esito oggettivo
    └── golden_tasks.yaml         # fixture + prompt + verify per l'eval
deploy/
├── Dockerfile.agent
├── docker-compose.yml
└── runbook.md
scripts/
├── startagent.bat                # Windows: avvia AgentOS in background (PID file + log)
├── stopagent.bat                 # Windows: ferma l'agente avviato da startagent.bat
├── ops-run.ps1                   # se schedulato su Windows (Task Scheduler)
└── ops-run.sh                    # se schedulato su Unix (cron/systemd)
docs/ops/                         # se high-level-ops o coding-agent schedulato (vedi Fase 3.5)
docs/OPENCODE_HARVEST.md          # se tool layer: provenance dell'harvest
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
  - Il tool layer è stdlib-only (nessuna dipendenza aggiuntiva); `lsp` usa il server LSP di sistema se presente
- `.env.example`: chiavi API per i modelli scelti + variabili runtime AgentOS + variabili dominio
  - Se scaffoldi Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS` (whitelist user_id)

### File template chiave

| Template | Variabilità |
|---|---|
| `agent.yaml.template` | ALTA — riflette identità completa |
| `agent_system_prompt.md.template` | ALTA — riflette identità, scope, boundaries |
| `agno/main.py.template` | MEDIA — cambiano import + nome ruoli |
| `agno/role.py.template` | MEDIA — instructions specifiche per ruolo |
| `agno/role_coding_agent.py.template` | ALTA — fonde prompt harvest (per famiglia modello) + identità + boundaries |
| `agno/role_high_level_ops.py.template` | ALTA — profili ops, task ammessi, livelli autonomia |
| `agno/tools/*.py.template` | BASSA — quasi-copia; parametrizza permessi e path |
| `agno/tools/guard.py.template` | MEDIA — denylist/allowlist/limiti dal manifesto |
| `agno/_models.py.template` | BASSA — può essere copia identica |
| `agno/skill_loader.py.template` | BASSA — può essere copia identica |
| `agno/test_smoke.py.template` | MEDIA — cambiano nomi ruoli |
| `agno/test_guard.py.template` | BASSA — casi deny/allow/propose/kill-switch |
| `agno/bench_models.py.template` | MEDIA — cambiano BENCHMARK_TASKS per ruolo |
| `agno/workflow_*.py.template` | ALTA — molto specifico al dominio |
| `agno/Dockerfile.agent.template` | BASSA — può essere copia identica |
| `agno/runbook.md.template` | MEDIA — cambiano comandi specifici |
| `agno/telegram_polling.py.template` | BASSA — quasi-copia, parametrizza solo team_id e env vars |
| `agno/telegram_setup.md` | BASSA — copia diretta come guida nel progetto target |
| `agno/startagent.bat.template` / `stopagent.bat.template` | BASSA — parametrizza solo il nome agente |
| `agno/role_scout.py.template` | BASSA — quasi-copia; modello dal manifesto |
| `agno/tools/verify.py.template` | MEDIA — definition-of-done dal manifesto |
| `agno/tools/gitops.py.template` / `repomap.py.template` | BASSA — quasi-copia |
| `agno/tools/context.py.template` | MEDIA — path dei journal (decisions.log/ADR/STATE) dal progetto; se mancano, crearli è parte dello scaffolding |
| `agno/eval_coder.py.template` | BASSA — quasi-copia |
| `agno/golden_tasks.yaml.template` | ALTA — task presi da manutenzioni reali del progetto |
| `ops/RUNBOOK.md.template` | MEDIA — profili e comandi del progetto |
| `ops/TASK_QUEUE.md.template` | ALTA — mission specifica |
| `ops/STATE.md.template` / `LAST_RUN.md.template` / `OUTBOX.md.template` / `AUDIT.md.template` | BASSA — placeholder standard |
| `ops/ops-run.ps1.template` / `ops-run.sh.template` | MEDIA — working dir, venv, profilo |
| `OPENCODE_HARVEST.md.template` | BASSA — tabella provenance precompilata |

### Interfaces & chat layer (opzionale)

L'agente è raggiungibile via REST API. Per utenti reali serve quasi sempre un'interface
chat consumer-facing. Pattern raccomandato: **Telegram**.

| Modalità | Quando | Cosa scaffolda |
|---|---|---|
| **Polling bot standalone** (default dev) | localhost, no tunnel pubblico | `agent/interfaces/telegram_polling.py` |
| **Native Agno interface** (default prod) | server con URL pubblico + webhook | attivazione condizionale in `main.py` |

Pattern Agno: `agno.os.interfaces.{telegram, slack, whatsapp, a2a, agui}`. Lo scaffolding copre
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

### Scheduler (se trigger schedulato)

Genera lo script wrapper per lo scheduler del sistema:

- **Windows Task Scheduler** → `scripts/ops-run.ps1`: imposta working directory, attiva venv se esiste, esporta env vars non segrete, invoca il workflow/profilo, propaga exit code. UTF-8 forzato.
- **cron/systemd** → `scripts/ops-run.sh`: stessi principi; `flock` per il lock.

Non installare lo scheduler automaticamente se l'utente non lo chiede. Fornisci il comando da eseguire o una procedura chiara in `RUNBOOK.md`.

---

## Fase 5 — Validation & Calibration

### 5.1 Smoke test (no API calls)

```bash
pytest agent/tests/test_smoke.py -v
```

Verifica: manifest carica, skill loader trova le skill del progetto, model factory mappa i provider, build_team() istanzia, build_agentos() costruisce.

**Tutti devono passare prima di chiamate LLM reali.**

### 5.2 Guard test (se tool layer, no API calls)

```bash
pytest agent/tests/test_guard.py -v
```

Verifica deterministica del tool-guard:
- tool call su path allowlisted → eseguito
- tool call su denylist (path sensibile, comando distruttivo) → DENY + audit entry
- tool call `propose` → NON eseguito, proposta in `OUTBOX.md`
- superamento `kill_switch_limit` → DENY hard di tutto
- doppio run simultaneo → secondo run bloccato dal lock

### 5.3 Avvio AgentOS

```bash
python -m agent.main          # foreground (dev)
# → http://localhost:7777
```

Su Windows, per l'uso quotidiano: `scripts\startagent.bat` (background, PID in
`.agent.pid`, log in `logs/agentos.log`) e `scripts\stopagent.bat` per fermarlo.

Conversazione di test in chat: "ciao, chi sei?" — l'agente dovrebbe rispondere con la sua identità definita nel manifesto.

### 5.4 Bench modelli (consuma poco — 1 task × N candidati per ruolo)

```bash
python -m agent.tests.bench_models --role <role>
```

Confronta latenza + lunghezza risposta tra candidati. La qualità richiede review umana sui contenuti. Va bene per Writer/Analyzer; per il coder usa l'eval oggettiva (5.5).

### 5.5 Eval del coding-agent — golden task (verdetto oggettivo)

```bash
python -m agent.tests.eval_coder --models glm-5.2,gemini-3.1-pro-preview
```

Per ogni candidato × ogni golden task: fixture copiata in workdir temporaneo →
il coder esegue il task → i comandi `verify` del task decidono PASS/FAIL.
Scoreboard finale + `eval_results.json`.

**I golden task vanno presi da manutenzioni REALI già fatte a mano** sul
progetto (bug corretti, refactoring): sono il benchmark più onesto. Copri:
bugfix puntuale, refactoring multi-file, feature con test già scritto, e un
task impossibile-senza-contesto (PASS = il modello dichiara il blocco invece
di inventare). Consuma token reali: parti con 1 modello × 1 task.

### 5.6 Workflow live (più costoso)

Esegui il workflow su environment di staging (mai produzione al primo run). Verifica:
- File output prodotti correttamente
- Audit trail popolato
- Propose-and-confirm queue popolata se applicabile
- Nessuna scrittura inattesa su sistemi esterni
- Per run schedulate: `LAST_RUN.md` aggiornato anche in caso di crash parziale; dry-run non scrive dati di dominio; nessun segreto nei log

### 5.7 Iterazione

- Tono sbagliato → raffina `agent_system_prompt.md`
- Proposte cattive → raffina le instructions del ruolo che le genera (es. `coach.py`)
- Tool calling errato → cambia modello (default → candidate alternativo)
- Coding-agent che "gira a vuoto" (troppe tool call, poco progresso) → mission più specifica in `TASK_QUEUE.md`, delega allo Scout più aggressiva, o modello con agentic coding più forte (decidi con `eval_coder`)
- Coding-agent che lascia lavoro rotto → controlla che segua il ciclo checkpoint→verify→rollback; se lo salta, rinforza le instructions del ruolo
- Boundaries non rispettate → **rinforza** il system prompt e la denylist del guard, NON rilassare i confini

### 5.8 Test interfaccia Telegram (se scaffoldata)

```bash
# In altro terminale (AgentOS deve essere up):
python -m agent.interfaces.telegram_polling
```

Da Telegram: cerca il bot per username, manda `/start`. Verifica risposta. Se hai
settato `TELEGRAM_ALLOWED_USERS`, prova da un account non in whitelist → deve rifiutare.

---

## Manutenzione dell'harvest opencode

Il tool layer deriva da opencode a un commit preciso, registrato in `docs/OPENCODE_HARVEST.md` (della skill e del progetto target). Periodicamente (o quando opencode annuncia feature rilevanti):

1. Confronta upstream (`https://github.com/anomalyco/opencode`, dir `packages/opencode/src/tool/` e `src/session/prompt/`) con la baseline nel doc harvest.
2. Se ci sono tool/prompt nuovi o migliorati utili ai nostri scopi → apri una `/change-request` per aggiornare i template del tool layer.
3. Aggiorna il doc harvest con il nuovo commit di riferimento.

Non è un fork: prendiamo solo ciò che serve, adattato a Python/Agno, con attribuzione MIT.

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

Quando l'agente fa azioni reali (write su sistemi, editing di codice, creare contenuti pubblici), il Critic è la differenza tra "agente affidabile" e "agente da incidente". Sempre presente nel team se autonomy != read-only.

### A6. Templates non rinominati

Un file lasciato come `main.py.template` invece di `main.py` è un bug latente. Tutti i template DEVONO essere renderizzati e rinominati. La presenza di file `.template` nel progetto target è sintomo di scaffolding incompleto. Verifica con grep che non restino `{{ placeholder }}`.

### A7. Coding-agent senza guard

Dare `edit`/`shell` a un ruolo senza tool-guard = agente da incidente. Il guard non è opzionale per i ruoli tool-empowered, nemmeno "per provare".

### A8. Allowlist shell troppo larga

`shell: "*": allow` = il ruolo può fare qualunque cosa. Sempre pattern concreti (`"pytest*": allow`), con `"*"` che cade su `propose` o `deny`.

### A9. Unattended senza kill-switch né lock

Un run schedulato senza kill-switch può macinare migliaia di tool call (e token) prima di esaurire; due run sovrapposte corrompono `AUDIT.md`/`LAST_RUN.md`. Entrambi obbligatori per trigger schedulati.

### A10. File ops come database

`STATE.md`/`OUTBOX.md` sono journal umani. Se il workflow ha bisogno di stato transazionale, usa il DB dell'engine (Agno sessions) o un file strutturato dedicato.

### A11. Segreti nei log/audit

Il guard non deve loggare contenuto dei file letti, valori di `.env`, o input completi se contengono dati di dominio sensibili. API key mai in repo: env vars / secret manager / `.env` gitignored.

### A12. "Verde = buono" (rubber-stamping)

Test verdi non significano codice buono: il degrado silenzioso passa da lì. Non rimuovere i quality gates "perché rallentano", non approvare proposte senza leggere il diff, non alzare `max_propose_diff_lines` per comodità. Se il volume di proposte supera la capacità di revisione umana, il fix è **ridurre l'autonomia**, non velocizzare le approvazioni.

### A13. Il codice circostante come specifica (context-blindness)

Caso reale: un coding-agent ha aggiunto una funzione a un pannello esistente — matematica corretta, test verdi, convenzioni rispettate — ereditandone però un difetto dati **noto e già fixato nei moduli gemelli** (documentato nel decision journal del progetto). Risultato plausibile ma sbagliato del 60%. Il coder è affidabile sul **locale** (funzione, test) e cieco sul **globale** (storia delle decisioni, difetti latenti adiacenti). Contromisure: (1) `project_context` obbligatorio nel passo 1 del ciclo — la storia decisionale è la specifica, il codice circostante no; (2) plausibilità del **risultato** oltre ai test (ordine di grandezza vs letteratura/funzione analoga/dati reali); (3) `log_decision` a fine lavoro, così il prossimo agente (o umano) eredita il contesto. Se il progetto non ha un decision journal, crearlo è parte dello scaffolding: senza, questo anti-pattern non ha contromisura.

---

## Checklist auto-verifica

Prima di dichiarare "fatto":

1. Ho fatto Fase 1 con domande mirate, non assunto un'identità?
2. Ho mostrato il manifesto all'utente per validazione?
3. Ho discusso engine + razionale con l'utente, non scelto unilateralmente?
4. I ruoli che ho proposto riflettono il dominio specifico?
5. I modelli hanno default + candidates per A/B testing?
6. Se ci sono ruoli tool-empowered: permessi per tool definiti (allow/propose/deny), autonomy level classificato per ogni capacità, guard scaffoldato e testato?
7. Se c'è il coding-agent: definition-of-done dichiarata nel manifesto, Scout nel team, golden task presi da manutenzioni reali, e le instructions impongono il ciclo orienta→checkpoint→edit→verify→chiudi (con `project_context` obbligatorio al passo 1 e `log_decision` alla chiusura)?
7b. Gate anti-degrado attivi: lint `required`, almeno una metrica non-decrescente, tetto diff, churn limit, e policy di revisione OUTBOX nel RUNBOOK?
8. I template sono renderizzati con valori reali, niente `{{ placeholder }}` nei file finali?
9. Ho lanciato smoke test (e guard test se applicabile) e ottenuto pass?
10. Ho documentato il deploy in `runbook.md` (e l'operatività in `docs/ops/RUNBOOK.md` se schedulato)?
11. Le boundaries hard sono nel system prompt + nella denylist del guard + nelle instructions del Critic?
12. L'audit trail è scritto da qualche parte?
13. `docs/OPENCODE_HARVEST.md` registra cosa è stato preso da opencode e da quale versione?

Se anche solo una risposta è "no" o "forse", torna indietro e correggi.

# Changelog

## [4.0.0] - 2026-07-06

### BREAKING — Skill rimosse (consolidate in `agentify`)

- **`agentic-ops-daemon` rimossa.** I suoi pattern vivono in `agentify` come archetipo di ruolo **`high-level-ops`**: livelli di autonomia L0-L5, ops runbook (`RUNBOOK/STATE/TASK_QUEUE/LAST_RUN/OUTBOX/AUDIT`), scheduler wrapper (`ops-run.ps1`/`.sh`), regole per task unattended (idempotenti, loggati, fail-loud).
- **`claude-session-supervisor` rimossa.** I suoi pattern vivono in `agentify` come **tool-guard** dei ruoli tool-empowered: kill-switch, denylist/allowlist statiche, propose-and-confirm via `OUTBOX.md`, audit trail append-only, lock anti-concorrenza. Il meccanismo specifico "hook `PreToolUse` + secondo `claude -p` judge" NON è migrato: era legato a Claude Code come runtime, mentre in `agentify` il giudizio contestuale spetta al modello del ruolo (scelto nell'intervista) col Critic come second opinion, e il guard fa enforcement deterministico dei confini.
- **Migrazione per chi usava le skill rimosse**: invocare `/vibecoding:agentify`; il caso "daemon/scheduler su CLI esistente" è coperto dal ruolo `high-level-ops`, il caso "sessione autonoma con boundaries" dal ruolo `coding-agent`/`high-level-ops` con tool-guard. Il caso residuo "supervisionare letteralmente una sessione `claude -p` con AI judge" non è più coperto dal toolkit (recuperabile dalla storia git, tag 3.3.1).

### Added — `agentify`: ruoli tool-empowered con tool layer derivato da opencode

- **Nuova Fase 3.5 — Tool Layer & Autonomy**: si attiva quando il team include ruoli tool-empowered.
- **Archetipo `coding-agent`**: ruolo del team ReAct con tool reali di coding — `read`, `glob`, `grep`, `edit`, `write`, `apply_patch`, `shell`, `lsp`, `todo`, `webfetch` — con potenza paragonabile a un coding agent dedicato. Tool, prompt di descrizione e system prompt (varianti per famiglia di modello: anthropic/gemini/gpt/default/plan) **derivati da opencode** (https://github.com/anomalyco/opencode, MIT, con attribuzione). opencode è fonte di conoscenza/risorse/tool, NON dipendenza runtime: nulla viene installato o invocato.
- **Archetipo `high-level-ops`**: operatore disciplinato schedulato (check, refresh, report, proposte) con tool layer ridotto.
- **Modello permessi per tool** in stile opencode: `allow`/`propose`/`deny` per tool, pattern glob per `shell` (l'`ask` interattivo di opencode diventa `propose` asincrono via OUTBOX nel contesto unattended).
- **Tool-guard** (`tools/guard.py`): enforcement a 4 livelli in ordine di costo (kill-switch → denylist → allowlist → propose-and-confirm) + audit append-only + lock.
- **Provenance harvest**: `docs/OPENCODE_HARVEST.md` (nella skill e scaffoldato nel progetto target) registra cosa è stato preso da opencode, da quale commit, con quali adattamenti; è la baseline per il ricontrollo periodico dell'upstream.
- **Nuovi template**: `agno/role_coding_agent.py`, `agno/role_high_level_ops.py`, `agno/tools/*` (fs, shell, lsp, tasklist, guard, registry), `agno/test_guard.py`, `ops/*` (RUNBOOK, STATE, TASK_QUEUE, LAST_RUN, OUTBOX, AUDIT, ops-run.ps1/.sh), `OPENCODE_HARVEST.md`.
- **`scripts/discover.py` esteso**: rileva anche OS (per `.ps1` vs `.sh`) e path sensibili (seed della denylist del guard) — funzioni assorbite dal discover dell'ex claude-session-supervisor.
- **Validazione estesa**: `test_guard.py` (deny/allow/propose/kill-switch/lock, deterministico, no API) e task di editing reale nel bench del coding-agent.

### Changed

- `agentify/SKILL.md`: rimossa l'esclusione "l'agente target deve essere un coding tool → meglio OpenCode/Aider/Continue" — il caso è ora coperto dal ruolo `coding-agent`. Rimossi i cross-reference alle skill pensionate.
- `plugin.json` / `marketplace.json`: versione 3.3.1 → 4.0.0; count skill 8 → 6; descrizioni e keyword aggiornate (rimossi `ops-daemon`, `supervisor`, `pre-tool-use-hook`; aggiunti `coding-agent`, `tool-guard`, `opencode-harvest`).
- CI `validate.yml`: rimossi i file required delle skill pensionate; aggiunti i nuovi file required di `agentify`.
- `README.md`: allineato (6 skill, sezione agentify riscritta).

---

## [3.3.1] - 2026-07-06

### Added
- **Skill `claude-session-supervisor`** — pattern worker + supervisor con AI judge purpose-aware via hook `PreToolUse` di Claude Code: una sessione `claude -p` non interattiva (worker) governata da una seconda sessione `claude -p` (judge) che valuta ogni tool call rispetto alla mission. Gating multi-livello (counter kill-switch → denylist baseline + `PROJECT_DENYLIST` → allowlist statica → AI judge LLM), audit trail append-only, lock anti-concorrenza, UTF-8 forzato. Include `scripts/discover.py` (Fase 0) e template portabili (`supervisor.py`, `worker/judge-settings.json`, `wake_worker.ps1`/`.sh`, `test_supervisor.py`, `RUNBOOK/TASK_QUEUE/AUDIT/LAST_RUN/OUTBOX.md`).
- **`OUTBOX.md.template`** nella skill — supporta il pattern propose-and-confirm per le scritture MCP (referenziato da `supervisor.py` ma non presente nella 3.3.0 upstream).
- **Cross-reference reciproco** tra `claude-session-supervisor` e `agentic-ops-daemon` (skill sorelle: la prima supervisiona una sessione Claude Code, la seconda schedula una CLI; vocabolario ops condiviso).

### Changed
- `plugin.json` / `marketplace.json`: versione 3.2.0 → 3.3.1; aggiunta `./skills/claude-session-supervisor/` (count skill 7 → 8); nuovi keyword (`autonomous-agent`, `supervisor`, `ai-judge`, `pre-tool-use-hook`).
- CI `validate.yml`: aggiunti `skills/claude-session-supervisor/SKILL.md` e `scripts/discover.py` alla lista dei file richiesti.

### Note
- **Riconciliazione della 3.3.0**: la skill era stata pubblicata sul branch `feature/claude-session-supervisor` come 3.3.0, ma partendo da una base che precedeva `agentic-ops-daemon` (gap documentato nella 3.3.0 stessa). La 3.3.1 la reintegra sul `main` corrente, così le due skill coesistono affiancate come da design SPEC-010. La 3.3.0 non è mai stata rilasciata su `main`.

---

## [3.2.0] - 2026-05-16

### Added
- **Skill `agentic-ops-daemon`** - protocollo portabile per progettare daemon/scheduler operativi che risvegliano periodicamente una CLI di progetto o un coding agent, eseguono check/refresh/report, scrivono runbook e audit trail, e applicano livelli di autonomia graduati.
- **Ops runbook pattern** - standardizza `docs/ops/RUNBOOK.md`, `STATE.md`, `TASK_QUEUE.md`, `LAST_RUN.md`, `OUTBOX.md`, `AUDIT.md` come interfaccia fra scheduler, CLI e agente.
- **Autonomy gates** - classifica le azioni da L0 read-only a L5 azioni vietate, con regola propose-and-confirm per modifiche a codice, policy, strategie, pesi o sistemi esterni.
- **Provider AI guidance** - include regole per integrare provider come Google Vertex/Gemini senza salvare segreti in repo e distinguendo ricerca/proposta da decisione vincolante.

### Changed
- `plugin.json`: versione 3.1.0 -> 3.2.0, descrizione e keywords aggiornati, aggiunto `./skills/agentic-ops-daemon/` all'array `skills`.
- `marketplace.json`: versione 3.1.0 -> 3.2.0, descrizione e count skill aggiornati (6 -> 7).
- CI workflow: aggiunta la nuova skill alla lista required.

---

## [3.1.0] — 2026-05-02

### Added
- **Skill `md-to-pdf`** — converte file Markdown in PDF formattati (pure-python via `markdown-pdf`, niente runtime nativi). Supporta TOC, CSS personalizzato, batch, paper-size e metadata. Aggiunto `skills/md-to-pdf/SKILL.md`, `scripts/convert.py`, `styles/default.css`.
- **Sintesi AI opzionale** (`--ai-summary`) — accoda al PDF una sezione "Sintesi AI (generata automaticamente)" con TL;DR, punti chiave, "quando consultarlo" e limiti, prodotta da Gemini. **Non modifica il sorgente `.md`**: la sintesi vive solo nel PDF. Pensata per leggere velocemente spec lunghe, SKILL.md di terzi, best-practice. Errori non bloccanti: senza `GEMINI_API_KEY` o con chiamata fallita, il PDF si genera comunque senza sintesi.
- **Strip front-matter YAML automatico** — le SKILL.md e i markdown con metadata Jekyll/Hugo (`---...---`) vengono gestiti correttamente; senza questo, `markdown-pdf` interpretava le fence come thematic break e rompeva il TOC.
- **Fallback TOC** — se il documento ha heading non lineari, lo script ritenta automaticamente la generazione senza TOC con un warning, anziche fallire.

### Dipendenze (per la nuova skill)
- `markdown-pdf` (obbligatoria per la conversione)
- `google-genai` + `python-dotenv` (solo per `--ai-summary`)

### Changed
- `plugin.json`: versione 3.0.1 -> 3.1.0, descrizione e keywords aggiornati, aggiunto `./skills/md-to-pdf/` all'array `skills`.
- `marketplace.json`: versione 3.0.1 -> 3.1.0, descrizione e count skill aggiornati (5 -> 6).
- CI workflow: aggiunti i tre file della nuova skill alla lista required.

---

## [3.0.1] — 2026-05-01

### Fixed
- **Manifest schema**: il campo `skills` in `plugin.json` ora punta a **directory** (`./skills/<nome>/`) invece che a file `SKILL.md`, conformemente allo schema attuale del Claude Code plugin loader. Senza questo fix, il plugin v3.0.0 non caricava le skill dopo l'installazione.
- CI workflow aggiornato per verificare path-a-directory invece di path-a-file per le skill.

### Note di installazione
Chi ha tentato di aggiornare a 3.0.0 e ha visto errori di validazione del manifest deve:
1. (Opzionale ma raccomandato) cancellare la cache locale: `rm -rf ~/.claude/plugins/cache/vibecoding-marketplace/`
2. Lanciare `claude plugin update vibecoding` (o disinstalla + reinstalla via `/plugin`)

L'errore precedente _"userConfig.qualityScoreTarget.title: Invalid input: expected string, received undefined"_ era causato dalla **cache locale 2.1.0** (con `userConfig` non più valido nello schema), non dal codice 3.0.0 stesso. Una volta pulita la cache, il plugin 3.0.1 si carica correttamente.

---

## [3.0.0] — 2026-05-01

### Pivot: from "autonomous multi-agent team" to "SDD toolkit"

Il plugin è stato ripensato come **toolkit di skill** per spec-driven development.
Un audit ha mostrato che ~70% delle feature di v2.1 sono ora coperte nativamente da
Claude Code (hooks, subagents, parallel execution, validation strategies). v3.0 si
concentra sul valore unico: la **metodologia** e il **routing 3-vie** delle desiderata.

### Added
- **Skill `change-request`** — protocollo a 5 fasi per change non banali (Impact Analysis → Spec First → Migration Plan → Implementation → Close the Loop). Anti bias additivo, no parallel flows
- **Skill `agentify`** — protocollo a 5 fasi per trasformare un progetto Claude Code in agente standalone (default: Agno + AgentOS). Include scripts/discover.py e templates Jinja2
- **Skill `skill-bootstrap`** — intervista metodologica di inizio progetto: distingue modulo vs cartella di lavorazione, fa routing delle desiderata in CLAUDE.md / PROJECT_SPEC / SKILL
- **Templates `modulo/`** — scaffold per progetti software (CLAUDE.md, PROJECT_SPEC, PLAN, docs/ARCHITECTURE)
- **Templates `cartella/`** — scaffold per cartelle di lavorazione Claude (analisi, automazione, documentazione)
- **Template `skill-stub/SKILL.md`** — usato da Fase D di skill-bootstrap per scrivere nuove skill
- **`docs/MIGRATION_2.1_to_3.0.md`** — guida per chi aveva v2.1 installato

### Changed
- **`/vibecoding:init`** esteso: aggiunte FASE A (modulo vs cartella), FASE C (routing 3-vie delle desiderata), FASE D (writer di SKILL.md). Delega la logica di routing a `skill-bootstrap`
- **Skill `methodology`** — refactor SDD-focused: tolti i riferimenti agli agenti rimossi, integrate parti utili di `quality-system`, allineata ai subagent nativi e ai comandi `/review` `/security-review`
- **Skill `validation-strategies`** — contenuto invariato (resta unica), spostata in `skills/validation-strategies/SKILL.md`
- **Manifesto `plugin.json`** — versione 3.0.0, descrizione aggiornata, rimosso `userConfig` (non più nello schema plugin), rimossi `agents`, `hooks`, comandi obsoleti
- **README.md** — riscrittura completa: pivot SDD toolkit
- Tutte le skill spostate in cartelle (`skills/<nome>/SKILL.md`) per allinearsi al formato Agent Skills standard

### Removed
- **Tutti gli agenti** (`architect`, `reviewer`, `tester`, `security-auditor`, `validation-agent`) — usa **subagent nativi** di Claude Code e i comandi `/review`, `/security-review`
- **Comandi obsoleti** (`/vibecoding:validate`, `/vibecoding:status`, `/vibecoding:review`, `/vibecoding:plan`) — slash command custom deprecati a favore di skills; le funzionalità sono coperte dai comandi nativi
- **`hooks/hooks.json`** intero — tutti gli hook (SessionStart, Stop type:prompt, PreCompact, PostCompact, PreToolUse Bash, PostToolUse Edit) sono coperti nativamente. I pattern destructive sono coperti dal permission system
- **Skill `parallel-execution`** — sostituita da Agent Teams nativi (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) e da parallel tool calls
- **Skill `quality-system`** — parti utili assorbite in `methodology`, altre rimosse
- **`scripts/quality-gate.sh`** spostato in `templates/scripts/` (opzionale, non plugin-level)
- **`templates/docs/vibecoding/METHODOLOGY.md`** — duplicato della skill methodology, eliminato
- **Campo `userConfig` nel manifest** — non più nello schema plugin attuale

### Migration
Chi aveva v2.1 installato deve aggiornare `~/.claude/settings.json` (path repo invariato:
`halleysud1/vibe`). I progetti generati con v2.1 continuano a funzionare; per migrarli
al routing 3-vie, lancia `skill-bootstrap` su una sessione del progetto. Vedi
`docs/MIGRATION_2.1_to_3.0.md`.

---

## [2.1.0] — 2026-03-29

### Added
- **Comando `/vibecoding:review`** — Invoca reviewer e security-auditor in parallelo con report unificato
- **Comando `/vibecoding:plan`** — Esplorazione codebase e piano approvabile interattivo
- **Hook PreCompact** — Salva automaticamente state snapshot prima della compaction del contesto
- **Hook PostCompact** — Ripristina contesto critico dopo la compaction
- **Skill `parallel-execution`** — Guida all'esecuzione parallela di agenti con merge dei risultati
- **Template `STATE_SNAPSHOT.md`** — Template per snapshot stato tra fasi di sviluppo
- **Claude Preview integration** — Metodo preferito per validazione web app (fallback Playwright)
- **Auto-lint per Go** (gofmt), **Rust** (rustfmt), **TOML** (taplo), **YAML** (yamllint)
- **Quality gate per Go** (golangci-lint, go test, govulncheck) e **Rust** (clippy, cargo test, cargo-audit)
- **Plugin `userConfig`** — Soglie configurabili (quality score, validation pass, lint languages)
- **Plugin `skills` field** — Tutte le 4 skill registrate nel manifest

### Changed
- **Hook Stop** — Da bash grep su emoji a `prompt` type (LLM valuta se OK fermarsi)
- **Hook SessionStart** — Alleggerito: solo conteggio task PLAN + reminder, non dump file interi
- **Hook PreToolUse(Bash)** — Pattern distruttivi ampliati (+`git push --force`, `DROP TABLE`, `dd`, `chmod -R 777`, `DELETE FROM`, `truncate`, `mkfs`)
- **validation-agent** — Aggiunto `effort: high`, `isolation: worktree`, sezione Claude Preview come metodo preferito, rimosso hooks block non funzionante su Windows
- **architect** — Aggiunto `effort: high`
- **reviewer/tester/security-auditor** — Aggiunto `effort: medium`
- **security-auditor** — Aggiunto supporto Go (govulncheck) e Rust (cargo-audit) nella checklist dipendenze
- **commands/validate.md** — Rilevamento Claude Preview, review+security paralleli post-validazione
- **commands/status.md** — Quality score composito, risultato ultima validazione, formato arricchito
- **commands/init.md** — Riferimenti 2.1, STATE_SNAPSHOT.md al posto di CONTEXT_RULES.md, integrazione auto-memory
- **skills/methodology.md** — Sezione "Gestione del Contesto" (merge da context-optimization), auto-memory per decisioni, anti-pattern aggiornati
- **skills/quality-system.md** — Sezione "Quality Gate Paralleli", metriche Go e Rust
- **skills/validation-strategies.md** — Nuova Sezione 0 "Claude Preview (METODO PREFERITO)"
- **scripts/quality-gate.sh** — Supporto Go e Rust per build, lint, test, dipendenze

### Removed
- **`scripts/load-context.sh`** — Dead code, funzionalità duplicata dal SessionStart hook
- **`templates/docs/vibecoding/CONTEXT_RULES.md`** — Contenuto duplicato, regole integrate in methodology skill
- **`skills/context-optimization.md`** — Regole ora default di Claude Code, parti utili migrate in methodology
- **Hook `Notification`** — Non funzionava su Windows, Claude Code ha notifiche native

---

## [2.0.0] — 2025-12-15

### Added
- Sistema multi-agente completo (5 agenti: architect, reviewer, tester, security-auditor, validation-agent)
- Filosofia dei tre livelli (Business / Ecosistema / Tecnico)
- Regola anti-overfit per requisiti configurabili
- Hooks deterministici (SessionStart, Stop, PreToolUse, PostToolUse, Notification)
- Quality gate con scoring composito su 7 dimensioni
- Validation Agent per testing dal punto di vista utente
- 3 comandi: init, validate, status
- 4 skill: methodology, validation-strategies, context-optimization, quality-system

### Removed (from v1.0)
- Approccio monolitico senza agenti specializzati
- Workflow manuale senza hooks
- Testing solo a livello codice (senza product validation)

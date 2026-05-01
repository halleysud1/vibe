# Changelog

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

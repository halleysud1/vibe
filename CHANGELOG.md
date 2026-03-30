# Changelog

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

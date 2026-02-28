# Changelog

Tutte le modifiche significative al progetto sono documentate in questo file.

Il formato segue [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [2.0.0] — 2026-02-28

### Aggiunto
- Plugin Claude Code nativo con manifest, marketplace.json, e distribuzione via GitHub
- **Validation Agent**: testa il prodotto dal punto di vista dell'utente finale (Web/API/Bot/CLI/VoIP/IoT)
- **Documentazione embedded**: la metodologia viene copiata in `docs/vibecoding/` di ogni progetto
- 4 comandi slash: `/vibecoding:init`, `/vibecoding:validate`, `/vibecoding:report`, `/vibecoding:status`
- 5 agenti: architect (Opus), reviewer, security-auditor, tester, validation-agent (Opus)
- 4 skills: methodology, context-optimization, validation-strategies, quality-system
- 5 hooks deterministici: SessionStart, Stop (blocca se test falliti), PreToolUse (blocca comandi distruttivi), PostToolUse (auto-lint), Notification
- Script `quality-gate.sh` per verifica completa del progetto
- Template per docs/vibecoding/ (METHODOLOGY.md, CONTEXT_RULES.md)
- GitHub Actions CI per validazione automatica della struttura plugin
- Supporto Claude Desktop (tab Code) e VS Code extension
- Configurazione marketplace per distribuzione team

### Cambiato rispetto a v1.0 (Vibecoding Swarm System)
- Da zip con script bash a plugin Claude Code nativo
- Da swarm con orchestrator.sh a subagenti nativi di Claude Code
- Da istruzioni CLAUDE.md (suggerimenti) a hooks deterministici (garantiti)
- Da gestione manuale dei backup a checkpoints nativi
- Da installazione manuale (decomprimi + copia) a `/plugin install`

### Rimosso
- `swarm/orchestrator.sh` — sostituito da subagenti nativi
- `swarm/context_guard.py` — sostituito da compaction automatica + skill context-optimization
- `swarm/protocol.py` — non necessario con subagenti nativi
- `tools/` (17 tool Python) — sostituiti da hooks e script singoli
- `personas/` — rinominati e migrati in `agents/` come formato Claude Code nativo

## [1.0.0] — 2025-02-15

### Release iniziale
- Sistema Vibecoding Swarm con orchestrator bash
- 17 tool Python per analisi e validazione
- 5 personas (architect, developer, reviewer, security, tester)
- Script evaluate.sh e loop_runner.sh
- Context guard con compressione manuale

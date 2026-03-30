# Vibecoding 2.1

Sistema di sviluppo autonomo multi-agente per Claude Code. Trasforma Claude in un team di sviluppo completo con quality gate deterministici, esecuzione parallela, e validazione del prodotto.

## Installazione

```bash
claude plugin install vibecoding@vibecoding-marketplace
```

Oppure manualmente in `~/.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "vibecoding-marketplace": {
      "source": { "source": "github", "repo": "halleysud1/vibe" }
    }
  },
  "enabledPlugins": {
    "vibecoding@vibecoding-marketplace": true
  }
}
```

## Quick Start

```
/vibecoding:init
```

L'init ti intervista sul dominio e i vincoli, poi genera la struttura completa del progetto e inizia a costruire.

## Comandi

| Comando | Descrizione |
|---------|-------------|
| `/vibecoding:init` | Inizializza progetto (intervista + spec + piano + architettura) |
| `/vibecoding:validate` | Valida il prodotto dal punto di vista utente (Preview/Playwright) |
| `/vibecoding:status` | Overview rapido: task, test, quality score |
| `/vibecoding:review` | Code review + security audit in parallelo |
| `/vibecoding:plan` | Esplora codebase e propone piano approvabile |

## Agenti

| Agente | Model | Effort | Ruolo |
|--------|-------|--------|-------|
| `architect` | Opus | High | Progetta architettura, schema DB, API |
| `reviewer` | Sonnet | Medium | Code review approfondita |
| `tester` | Sonnet | Medium | Genera test unitari, integrazione, edge case |
| `security-auditor` | Sonnet | Medium | Audit OWASP, segreti, dipendenze |
| `validation-agent` | Opus | High | Testa il PRODOTTO come utente finale (worktree isolato) |

## Hooks

| Hook | Tipo | Funzione |
|------|------|----------|
| `SessionStart` | command | Carica stato PLAN e contesto progetto |
| `Stop` | prompt | LLM valuta se è sicuro fermarsi |
| `PreToolUse(Bash)` | command | Blocca comandi distruttivi |
| `PostToolUse(Write\|Edit)` | command | Auto-lint (Python, JS/TS, Go, Rust, TOML, YAML) |
| `PreCompact` | command | Salva state snapshot prima della compaction |
| `PostCompact` | command | Ripristina contesto critico dopo compaction |

## Skills

| Skill | Descrizione |
|-------|-------------|
| `methodology` | Filosofia dei 3 livelli, anti-overfit, gestione contesto |
| `validation-strategies` | Strategie per tipo app (Claude Preview, Playwright, HTTP, CLI, IoT) |
| `quality-system` | Quality gate, scoring composito, metriche per linguaggio |
| `parallel-execution` | Guida parallelizzazione agenti e merge risultati |

## Novità in 2.1

### Hook intelligenti
- **Stop hook prompt-based**: L'LLM valuta se è sicuro fermarsi (non più grep su emoji)
- **PreCompact/PostCompact**: Preservano il contesto automaticamente durante la compaction
- **Auto-lint esteso**: Supporto Go, Rust, TOML, YAML oltre a Python e JS/TS
- **Pattern distruttivi ampliati**: Blocca anche `git push --force`, `DROP TABLE`, `dd`, `chmod -R 777`

### Esecuzione parallela
- **Review + Security in parallelo**: `/vibecoding:review` invoca entrambi gli agenti simultaneamente
- **Validation in worktree isolato**: Non interferisce con lo sviluppo in corso
- **Merge conservativo**: Il verdetto più severo vince sui conflitti

### Claude Preview integration
- **Metodo preferito per web app**: Usa `preview_*` MCP tools al posto di Playwright
- **Fallback automatico**: Se Preview non è disponibile, usa Playwright
- **Copertura completa**: Screenshot, interazioni, network, console, responsive, dark mode

### Gestione contesto migliorata
- **Auto-memory integration**: Decisioni architetturali salvate nel sistema memory di Claude
- **State snapshot automatici**: Hook PreCompact salva lo stato prima della compaction
- **SessionStart leggero**: Solo conteggio task e reminder, non dump di file interi

### Nuovi comandi
- **`/vibecoding:review`**: Review parallela (code + security) con report unificato
- **`/vibecoding:plan`**: Esplorazione codebase e piano approvabile

### Rimosso
- `scripts/load-context.sh` (dead code, duplicato dal SessionStart hook)
- `templates/docs/vibecoding/CONTEXT_RULES.md` (regole integrate in methodology)
- `skills/context-optimization.md` (regole ora default di Claude Code, parti utili in methodology)
- Hook `Notification` (non funzionava su Windows, Claude ha notifiche native)

## Struttura Progetto Generato

```
my-project/
├── .vibecoding                     <- Marker (attiva hooks)
├── CLAUDE.md                       <- Regole e vincoli
├── PROJECT_SPEC.md                 <- Specifica a 3 livelli
├── PLAN.md                         <- Task list con stato
├── decisions.log                   <- Audit trail decisioni
├── docs/
│   ├── ARCHITECTURE.md             <- Generato dall'architect
│   └── vibecoding/
│       ├── METHODOLOGY.md          <- Metodologia di riferimento
│       ├── VALIDATION_STRATEGY.md  <- Strategia validazione per tipo app
│       └── STATE_SNAPSHOT.md       <- Template snapshot stato
├── src/                            <- Codice sorgente
├── tests/                          <- Test suite
└── validation/                     <- Script di validazione
```

## Filosofia

1. **Tre livelli**: Business (chiedi all'utente) / Ecosistema (vincoli non negoziabili) / Tecnico (decidi tu)
2. **Anti-overfit**: Esempi dell'utente diventano default configurabili, non codice hardcodato
3. **Quality first**: Non procedere senza test che passano
4. **Prodotto, non codice**: La validazione testa dal punto di vista dell'utente finale
5. **Autonomia con accountability**: Decidi e logga, non chiedere e aspetta

## Requisiti

- Claude Code CLI o Desktop App
- Claude Opus 4.6 o Sonnet 4.6 (gli agenti selezionano il modello automaticamente)

## Licenza

MIT — Gianluigi, Halley Sud SRL

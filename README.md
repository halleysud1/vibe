# Vibecoding 2.0

**Un plugin Claude Code che trasforma l'AI in un team di sviluppo completo.**

Vibecoding 2.0 è un sistema di sviluppo software autonomo multi-agente. Dai una visione, ricevi un prodotto funzionante — testato, validato, e documentato.

## Cosa fa

- **5 agenti specializzati** lavorano come un team: Architect, Reviewer, Security Auditor, Tester, e un Validation Agent che testa il prodotto come un utente reale
- **Hooks deterministici** impediscono a Claude di fermarsi prima che i test passino o di eseguire comandi distruttivi
- **3 comandi slash** per controllare il flusso: init, validate, status
- **Documentazione embedded** nel progetto — la metodologia vive con il codice
- **Validazione del prodotto** — non solo test del codice, ma test dell'esperienza utente con Playwright, HTTP client, companion bot

## Installazione

```bash
# 1. Aggiungi il marketplace
claude plugin marketplace add halleysud1/vibe

# 2. Installa il plugin
claude plugin install vibecoding@vibecoding-marketplace
```

### Installazione manuale (alternativa)

Se l'installazione automatica non funziona, puoi configurare il plugin manualmente:

```bash
# 1. Clona il repo nella cartella plugins di Claude Code
git clone https://github.com/halleysud1/vibe.git ~/.claude/plugins/vibe

# 2. Aggiungi questa configurazione al tuo ~/.claude/settings.json
```

```json
{
  "extraKnownMarketplaces": {
    "vibecoding-marketplace": {
      "source": {
        "source": "directory",
        "path": "<PERCORSO_ASSOLUTO>/.claude/plugins/vibe"
      }
    }
  },
  "enabledPlugins": {
    "vibecoding@vibecoding-marketplace": true
  }
}
```

> **Nota:** Sostituisci `<PERCORSO_ASSOLUTO>` con il percorso home del tuo sistema (es. `/home/user` su Linux, `/Users/user` su macOS, `C:\\Users\\user` su Windows).

```bash
# 3. Riavvia Claude Code e verifica
claude plugin list
# Deve mostrare: vibecoding@vibecoding-marketplace
```

## Quick Start

```bash
cd my-new-project
claude --dangerously-skip-permissions

# Dentro Claude Code:
/vibecoding:init
# → Descrivi cosa vuoi costruire
# → Il sistema fa il resto
```

## Come funziona

```
/vibecoding:init
       │
       ▼
  ┌─────────┐     ┌───────────┐     ┌──────────────┐
  │ Analisi  │────▶│ Architect │────▶│ ARCHITECTURE │
  │ & Spec   │     │  Agent    │     │     .md      │
  └─────────┘     └───────────┘     └──────────────┘
       │
       ▼
  ┌──────────────────────────────────────────┐
  │  Per ogni task in PLAN.md:               │
  │  Implementa → Testa → Fix → Committa    │
  │  (Hook Stop blocca se test falliscono)   │
  └──────────────────────────────────────────┘
       │
       ▼
  ┌───────────┐     ┌──────────────────┐
  │ Reviewer  │────▶│ Security Auditor │
  │  Agent    │     │     Agent        │
  └───────────┘     └──────────────────┘
       │
       ▼
  ┌──────────────────────────────────────────┐
  │  🌟 Validation Agent                     │
  │  Costruisce un client automatico e USA   │
  │  il prodotto come farebbe l'utente:      │
  │  - Web App → Playwright browser test     │
  │  - API → HTTP client con flussi reali    │
  │  - Bot → Companion bot che conversa      │
  │  - CLI → Script con input realistici     │
  │  - VoIP → Simulatore di chiamate         │
  └──────────────────────────────────────────┘
       │
       ▼
  ┌───────────┐
  │  STATUS   │ ← /vibecoding:status
  └───────────┘
```

## Comandi

| Comando | Cosa fa |
|---------|---------|
| `/vibecoding:init` | Crea PROJECT_SPEC, PLAN, architettura, e avvia lo sviluppo |
| `/vibecoding:validate` | Lancia il Validation Agent per testare il prodotto dal vivo |
| `/vibecoding:status` | Overview rapido inline |

## Agenti

| Agente | Modello | Cosa fa |
|--------|---------|---------|
| `architect` | Opus | Design sistema, schema DB, API, interfacce |
| `reviewer` | Sonnet | Code review su qualità, manutenibilità, aderenza alle spec |
| `security-auditor` | Sonnet | Audit OWASP: injection, auth, segreti, dipendenze |
| `tester` | Sonnet | Genera test unitari, integrazione, edge case |
| `validation-agent` | Opus | Costruisce e esegue client automatici per testare il prodotto reale |

## La feature killer: Validation Agent

La maggior parte dei coding agent costruisce software ma non lo **usa** mai. Il Vibecoding validation-agent risolve questo:

**Web App** → Installa Playwright, apre un browser headless, naviga l'app, compila form, clicca bottoni, cattura screenshot, verifica che tutto funzioni

**REST API** → Crea uno script HTTP che simula il flusso utente completo: registrazione → login → operazioni CRUD → verifica persistenza

**Bot / Chatbot** → Costruisce un companion bot che invia messaggi e verifica le risposte

**VoIP / SIP** → Verifica raggiungibilità, testa registrazione SIP, simula chiamate

**CLI Tool** → Esegue il tool con input validi, invalidi, edge case, verifica exit code e output

**IoT** → Mock del dispositivo, invio telemetria, verifica risposte server

Ogni validazione produce `validation_results.json` con risultati strutturati e `validation_screenshots/` con evidenze visive.

## Hooks

| Hook | Quando | Cosa fa |
|------|--------|---------|
| `SessionStart` | Apertura sessione | Rileva progetto Vibecoding e carica contesto |
| `Stop` | Claude vuole fermarsi | **Blocca** se ci sono test falliti o task incompleti |
| `PreToolUse` | Prima di un comando bash | **Blocca** comandi distruttivi (`rm -rf /`, `DROP DATABASE`) |
| `PostToolUse` | Dopo modifica file | Auto-lint con ruff/eslint |
| `Notification` | Claude ha bisogno di attenzione | Notifica desktop (Linux/macOS) |

## Struttura progetto generata

Dopo `/vibecoding:init`, il tuo progetto avrà:

```
my-project/
├── .vibecoding                      # Marker file
├── CLAUDE.md                        # Istruzioni per Claude Code
├── PROJECT_SPEC.md                  # Specifiche tecniche
├── PLAN.md                          # Task con stato
├── decisions.log                    # Log decisioni autonome
├── docs/
│   ├── ARCHITECTURE.md              # Generata dall'architect
│   └── vibecoding/                  # ← Documentazione embedded
│       ├── METHODOLOGY.md           # Metodologia di sviluppo
│       ├── VALIDATION_STRATEGY.md   # Strategia di validazione
│       └── CONTEXT_RULES.md         # Regole ottimizzazione contesto
├── src/                             # Codice sorgente
├── tests/                           # Test unitari e integrazione
├── validation/                      # Script di validazione prodotto
└── validation_screenshots/          # Evidenze visive
```

## Requisiti

- **Claude Code** >= 2.0
- **Node.js** >= 18
- **Python** >= 3.10 (raccomandato)
- **jq** (per gli hooks)

Dipendenze opzionali (installate automaticamente quando necessario): Playwright, ruff, pytest, httpx.

## Modalità d'uso

### Autonomia totale (raccomandato)
```bash
claude --dangerously-skip-permissions
/vibecoding:init
# Descrivi il progetto, vai a prendere un caffè
```

### Con supervisione
```bash
claude --permission-mode acceptEdits
/vibecoding:init
```

### Fire and forget
```bash
claude --dangerously-skip-permissions -p "/vibecoding:init — Sviluppa un'API REST per gestione inventario. Stack: Python/FastAPI/PostgreSQL."
```

### Claude Desktop
Apri la tab **Code** → clicca **+** → **Plugins** → **Add plugin** → seleziona la cartella del plugin o cerca "vibecoding" nel marketplace.

## Usare come marketplace di team

Per distribuire il Vibecoding a tutto il team, aggiungi al `.claude/settings.json` dei progetti:

```json
{
  "extraKnownMarketplaces": {
    "vibecoding-marketplace": {
      "source": {
        "source": "github",
        "repo": "halleysud1/vibe"
      }
    }
  },
  "enabledPlugins": {
    "vibecoding@vibecoding-marketplace": true
  }
}
```

## Contributing

Vedi [CONTRIBUTING.md](CONTRIBUTING.md) per le linee guida.

## License

MIT — vedi [LICENSE](LICENSE).

## Changelog

### 2.0.0 (Febbraio 2026)
- Riscrittura completa come plugin Claude Code nativo
- Hooks deterministici al posto di istruzioni CLAUDE.md
- Subagenti nativi al posto dello swarm bash custom
- **Nuovo: Validation Agent** — testa il prodotto come utente finale
- **Nuovo: Documentazione embedded** nel progetto
- Supporto checkpoints nativi
- Compatibile con Claude Desktop e VS Code extension
- Pronto per distribuzione via marketplace

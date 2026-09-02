# Vibecoding — SDD toolkit per Claude Code

> Versione corrente: **5.0.1** — vedi [CHANGELOG](CHANGELOG.md) e [Releases](https://github.com/halleysud1/vibe/releases).

## A cosa serve

Un modello forte scrive buon codice. Quello che continua a non fare da solo è
**tenere insieme un progetto nel tempo**: chiedere il dominio prima di
costruirci sopra, mettere ogni informazione nella sede dove verrà riletta,
migrare invece di affiancare, e lasciare la documentazione allineata al codice
quando la sessione finisce.

Vibecoding è un plugin di **skill** che codifica quel metodo e lo rende
disponibile in qualunque progetto Claude Code. Non è un sistema multi-agente:
gli agenti sono quelli nativi — qui vivono il metodo, i protocolli e gli
scaffold.

## Perché è utile

| Problema ricorrente | Cosa fa il plugin |
|---|---|
| Si costruisce su assunzioni di dominio mai verificate | `/vibecoding:init` intervista su business e vincoli **prima** di scrivere codice |
| Le regole del progetto finiscono tutte in `CLAUDE.md`, che nessuno rilegge davvero | **Routing 3-vie**: ogni desideratum va in `CLAUDE.md`, `PROJECT_SPEC.md` o in una SKILL che si attiva da sola quando serve |
| Gli esempi dell'utente diventano valori hardcoded | Regola **anti-overfit**: l'esempio diventa un default configurabile, l'intenzione diventa il requisito |
| Si aggiunge la feature nuova e la vecchia resta viva accanto | `change-request`: impact analysis, spec prima del codice, migrazione esplicita, **niente parallel flows** |
| A fine lavoro test verdi e documentazione stale | **Fase 5 — close the loop**: spec, ADR, snapshot e journal aggiornati nella stessa change |
| Serve un agente che giri dove Claude Code non c'è | `agentify`: scaffolda un agente standalone con ruoli multi-modello, tool-guard e autonomy gates |
| La lavorazione va consegnata a chi non usa Claude Code | `guify`: la distribuisci come **interfaccia grafica** — console di controllo, dashboard, form, chat — invece che come cartella con le skill |
| Una ricerca va consegnata a un terzo che deve poterla verificare riga per riga | `deep-research`: funnel ricorsivo, ogni claim arbitrato sulla fonte primaria, sinottico auditabile |
| Una spec va consegnata come documento presentabile | `md-to-pdf`: Markdown → PDF impaginato |

Il criterio che regge tutto: **specifica dove serve, libertà dove giova.**
L'utente è autoritativo sul dominio e sui vincoli; le decisioni tecniche restano
al modello.

---

## Cosa contiene

| Componente | Descrizione |
|---|---|
| **Skill `methodology`** | Filosofia 3 livelli (business / ecosistema / tecnico), regola anti-overfit, gestione del contesto |
| **Skill `skill-bootstrap`** | Intervista di inizio progetto: routing 3-vie delle desiderata in CLAUDE.md / PROJECT_SPEC / SKILL, scaffolding, chiusura |
| **Skill `change-request`** | Protocollo a 5 fasi per change non banali. Anti bias additivo, no parallel flows, propagazione della documentazione |
| **Skill `validation-strategies`** | Checklist di scenari di validazione per tipo di app (web, API, bot, CLI, pipeline, IoT); la meccanica è delegata ai tool nativi (`/verify`, `/run`, Claude Preview) |
| **Skill `agentify`** | Trasforma un progetto Claude Code in agente Agno standalone. Ruoli tool-empowered con harness completo: **coding-agent** (tool edit/shell/LSP derivati da [opencode](https://github.com/anomalyco/opencode) + verify loop sulla definition-of-done, checkpoint/rollback git, **scout** a contesto separato, repo map, eval su golden task), **high-level-ops** (run schedulate) — governati da tool-guard con autonomy gates L0-L5, gate anti-degrado, audit trail e propose-and-confirm sul diff |
| **Skill `guify`** | Distribuisce una lavorazione come **GUI collegata alla sessione o all'agente**. Gate multi-superficie: widget in-chat (`sendPrompt`), artifact con capabilities (per colleghi con account Claude), app standalone self-hosted — FastAPI sopra **Agent SDK** (abbonamento a prezzo fisso) o **AgentOS** (agentify) — con RBAC default-deny, form→prompt strutturati per i terzi, approvazioni sul diff reale, audit |
| **Skill `deep-research`** | Cicli di ricerca profonda **ricorsivi** con Google Deep Research come motore: inquadramento → chiusura dei dubbi → focalizzazione, controllo delle fonti dopo ogni round, arbitraggio sulla fonte primaria (mai a maggioranza fra LLM), sinottico con traccia della ricorsione. Include blueprint di state machine per il full-auto |
| **Skill `md-to-pdf`** | Converte Markdown in PDF formattati (Chromium ad alta fedeltà o pure-python), con sintesi AI opzionale |
| **Comando `/vibecoding:init`** | Entry point per bootstrappare un progetto: richiama `skill-bootstrap` |
| **Templates** | Scaffold pronti per "modulo software" e "cartella di lavorazione Claude" |

---

## Installazione

In `~/.claude/settings.json`:

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

Oppure:

```bash
claude plugin install vibecoding@vibecoding-marketplace
```

---

## Quick start

```
/vibecoding:init
```

Init ti guida attraverso:

1. **Detect** — cosa esiste già nel progetto
2. **Tipo di lavorazione** — modulo software vs cartella di lavorazione Claude
3. **Intervista** — domande di L1 (business) e L2 (vincoli) + regole operative ricorrenti
4. **Routing 3-vie** — classifica le desiderata in CLAUDE.md / PROJECT_SPEC / SKILL, con la tua approvazione
5. **Scaffolding** — scrive gli artefatti popolati e chiude con journal e memory

Output: progetto pronto, con i vincoli globali in CLAUDE.md, visione e requisiti
in PROJECT_SPEC, e skill dedicate per le regole operative ricorrenti.

---

## Il metodo in 1 minuto

### I 3 livelli

| Livello | Cosa è | Sede naturale |
|---|---|---|
| **L1 — Business** | Visione, utenti, requisiti funzionali | `PROJECT_SPEC.md` |
| **L2 — Ecosistema** | Vincoli ambiente, stack imposto, normative | `CLAUDE.md` |
| **L3 — Tecnico** | Framework, architettura, pattern | `docs/ARCHITECTURE.md` + ADR |

L'utente è autoritativo su L1+L2. Claude è autonomo su L3 — e il plugin non
prescrive nessuno stack di default: una tabella di framework scritta una volta
verrebbe applicata a progetti che non la giustificano.

### Anti-overfit

Gli esempi concreti dell'utente diventano **default configurabili**, non valori
hardcoded. Il test: *"se domani volesse cambiare questo valore, dovrebbe
modificare il codice?"* Se sì, stai overfittando.

### Routing 3-vie

Le **regole operative ricorrenti** (es. "ogni elemento core deve avere
un'attività futura") non vanno né in CLAUDE.md né in PROJECT_SPEC: vanno in
**SKILL.md** dedicate, dove Claude le attiva contestualmente via la
`description`. È il progressive disclosure applicato alle regole di progetto.

---

## Struttura del repo

```
vibe/
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── init.md                      # /vibecoding:init (entry point sottile)
├── skills/
│   ├── methodology/SKILL.md
│   ├── skill-bootstrap/SKILL.md
│   ├── change-request/SKILL.md
│   ├── validation-strategies/SKILL.md
│   ├── agentify/
│   │   ├── SKILL.md
│   │   ├── OPENCODE_HARVEST.md      # provenance del tool layer (commit opencode pinnato)
│   │   ├── scripts/                 # discover.py (Fase 0: skill, MCP, OS, path sensibili)
│   │   └── templates/
│   │       ├── agno/                # main, ruoli (coding_agent, scout, high_level_ops),
│   │       │   │                    #   eval_coder + golden_tasks, start/stopagent.bat
│   │       │   └── tools/           # guard, fs, shell, verify, gitops, repomap, lsp, tasklist
│   │       ├── prompts/             # varianti system prompt del coding-agent
│   │       └── ops/                 # RUNBOOK, TASK_QUEUE, OUTBOX, AUDIT, ops-run.ps1/.sh
│   ├── deep-research/
│   │   ├── SKILL.md                 # protocollo del funnel con gate umani
│   │   ├── scripts/                 # deep_research.py, grounded_research.py, env_loader.py
│   │   ├── prompts/                 # template dei round + audit adversarial
│   │   ├── references/              # Interactions API verificata, calibrazione del funnel
│   │   └── templates/fullauto/      # state machine, tool di chat, WIRING.md
│   ├── guify/
│   │   ├── SKILL.md                 # gate multi-superficie + regole di sicurezza G1-G6
│   │   └── templates/
│   │       ├── gui.yaml.template    # manifesto della GUI
│   │       ├── standalone/          # FastAPI + engine sdk/agentos + RBAC + frontend + test
│   │       ├── artifact/PATTERNS.md # GUI come pagina pubblicata (colleghi con account)
│   │       └── widget/PATTERNS.md   # GUI in-chat (sendPrompt)
│   └── md-to-pdf/
│       ├── SKILL.md
│       ├── scripts/
│       └── styles/
├── templates/
│   ├── modulo/                      # scaffold "modulo software"
│   ├── cartella/                    # scaffold "cartella di lavorazione"
│   ├── skill-stub/SKILL.md          # template per le skill scritte dal bootstrap
│   └── scripts/quality-gate.sh      # quality gate composito, opzionale
└── docs/
```

Gli script delle skill si invocano sempre via `${CLAUDE_PLUGIN_ROOT}`: vivono
nella directory del plugin installato, non nel progetto.

---

## Requisiti

- Claude Code CLI o Desktop App (con Skills e Subagents nativi)
- Per `agentify`: Python 3.10+ con `agno`, `pyyaml`, `python-dotenv` se usi il default Agno
- Per `deep-research`: Python 3.10+ con `google-genai>=2.0.0` e `GEMINI_API_KEY` in ambiente o `.env`
- Per `md-to-pdf`: `playwright` + Chromium per l'alta fedeltà, oppure `markdown-pdf` come fallback offline
- Per `guify` (superficie standalone): Python 3.10+ con `fastapi`, `uvicorn`, `pyyaml`; engine sdk: `claude-agent-sdk` (o la CLI `claude`); engine agentos: `httpx`

---

## Principi

1. **Specifica dove serve, libertà dove giova** — tre livelli, non uno solo
2. **Routing esplicito** — ogni desideratum ha la sua sede corretta
3. **Skill come memoria operativa** — le regole ricorrenti vivono nelle skill, non nei prompt
4. **No parallel flows** — quando si migra, si rimuove il vecchio
5. **Spec wins** — il codice segue la spec, mai il contrario

---

## Licenza

MIT — Gianluigi, Halley Sud SRL

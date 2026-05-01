# Vibecoding 3.0 — SDD toolkit per Claude Code

Plugin che porta il **vibecoding spec-driven development** in qualunque progetto
Claude Code. È un repo di **skill** + un comando di bootstrap, non un sistema
multi-agente: la metodologia vive nelle skill, gli agenti vivi sono quelli nativi
di Claude Code.

> **Cambiamento rispetto a v2.x**: il plugin è stato ripensato come **toolkit di skill
> riusabili**, non più come "team di sviluppo autonomo". Vedi `docs/MIGRATION_2.1_to_3.0.md`.

---

## Cosa offre v3.0

| Componente | Descrizione |
|---|---|
| **Skill `methodology`** | Filosofia 3 livelli (business / ecosistema / tecnico), regola anti-overfit, gestione contesto |
| **Skill `validation-strategies`** | Strategie di validazione per tipo app (web, API, bot, CLI, pipeline, IoT) |
| **Skill `change-request`** | Protocollo a 5 fasi per change non banali. Anti bias additivo, no parallel flows |
| **Skill `agentify`** | Trasforma un progetto Claude Code (con skill + MCP) in agente Agno standalone |
| **Skill `skill-bootstrap`** | Intervista metodologica: routing 3-vie delle desiderata in CLAUDE.md / PROJECT_SPEC / SKILL |
| **Comando `/vibecoding:init`** | Entry point per bootstrappare un nuovo progetto: chiama `skill-bootstrap` |
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

1. **Tipo di lavorazione** — modulo software vs cartella di lavorazione Claude
2. **Intervista** — domande di L1 (business) e L2 (vincoli) + regole operative ricorrenti
3. **Routing 3-vie** — classifica le desiderata in CLAUDE.md / PROJECT_SPEC / SKILL
4. **Scaffolding** — scrive i 3 artefatti popolati

Output: progetto pronto, con vincoli globali in CLAUDE.md, visione/RF in PROJECT_SPEC,
e skill dedicate per le regole operative ricorrenti.

---

## Filosofia in 1 minuto

### I 3 livelli

| Livello | Cosa è | Sede naturale |
|---|---|---|
| **L1 — Business** | Visione, utenti, requisiti funzionali | `PROJECT_SPEC.md` |
| **L2 — Ecosistema** | Vincoli ambiente, stack, normative | `CLAUDE.md` |
| **L3 — Tecnico** | Framework, architettura, pattern | `docs/ARCHITECTURE.md` + ADR |

L'utente è autoritativo su L1+L2. Claude è autonomo su L3.

### Anti-overfit

Esempi concreti dell'utente → **default configurabili**, non hardcoded.

### Routing 3-vie (v3.0)

Le **regole operative ricorrenti** (es. "ogni elemento core deve avere un'attività
futura") non vanno né in CLAUDE.md né in PROJECT_SPEC: vanno in **SKILL.md**
dedicate, dove Claude le attiva contestualmente via la `description`.

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
│   └── init.md                      # /vibecoding:init
├── skills/
│   ├── methodology/SKILL.md
│   ├── validation-strategies/SKILL.md
│   ├── change-request/SKILL.md
│   ├── agentify/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   └── templates/
│   └── skill-bootstrap/SKILL.md
├── templates/
│   ├── modulo/                      # scaffold "modulo software"
│   ├── cartella/                    # scaffold "cartella di lavorazione"
│   ├── skill-stub/SKILL.md          # template per skill scritte da init
│   └── scripts/quality-gate.sh      # opzionale, era plugin-level in v2.1
└── docs/
    └── MIGRATION_2.1_to_3.0.md
```

---

## Cosa è cambiato dal 2.x

**Rimosso** (perché Claude Code copre nativamente):
- Tutti gli agenti `architect`, `reviewer`, `tester`, `security-auditor`, `validation-agent`
  → usa subagent nativi e i comandi `/review`, `/security-review`
- Hooks (`SessionStart`, `Stop`, `PreCompact`, `PostCompact`, `PreToolUse Bash`, `PostToolUse Edit`)
  → tutti supportati nativamente con type `prompt` per Stop ecc.
- Skill `parallel-execution` → Agent Teams nativi e parallel tool calls
- Skill `quality-system` → assorbita in `methodology`; il quality-gate.sh resta opzionale
- Slash command `/validate`, `/status`, `/review`, `/plan` → coperti dal nativo o non più necessari
- `userConfig` nel manifest → non più nello schema plugin attuale

**Aggiunto**:
- Skill `change-request` (protocollo 5 fasi)
- Skill `agentify` (engine-agnostic, default Agno+AgentOS)
- Skill `skill-bootstrap` (intervista routing 3-vie)
- Templates "modulo" / "cartella di lavorazione"

**Migrato**:
- `init.md` esteso con FASE A (tipo lavorazione), FASE C (routing), FASE D (writer SKILL)
- `methodology` refactor SDD-focused
- `validation-strategies` invariata, spostata in cartella

Vedi `docs/MIGRATION_2.1_to_3.0.md` per chi aveva v2.1 installato.

---

## Requisiti

- Claude Code CLI o Desktop App (versione 2026 con Skills + Subagents nativi)
- Per `agentify`: Python 3.10+ con `agno`, `pyyaml`, `python-dotenv` se usi il default Agno

---

## Filosofia

1. **Specifica dove serve, libertà dove giova** — 3 livelli, non un livello solo
2. **Routing esplicito** — ogni desideratum ha la sua sede corretta
3. **Skill come memoria operativa** — le regole ricorrenti vivono nelle skill, non nei prompt
4. **No parallel flows** — quando si migra, si rimuove il vecchio
5. **Spec wins** — il codice segue la spec, mai il contrario

---

## Licenza

MIT — Gianluigi, Halley Sud SRL

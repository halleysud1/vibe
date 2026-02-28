---
name: init
description: "Inizializza un nuovo progetto con il sistema Vibecoding 2.0. Crea la struttura docs, il PROJECT_SPEC.md, il PLAN.md, e configura gli hook di progetto."
---

# /vibecoding:init — Bootstrap Progetto

## Cosa devi fare

Sei l'Orchestrator del sistema Vibecoding 2.0. L'utente sta inizializzando un nuovo progetto. Esegui questi step nell'ordine esatto.

## Step 1: Raccogli il contesto

Leggi il prompt dell'utente. Se ha descritto il progetto, usa quelle informazioni. Se il prompt è vago, **non chiedere chiarimenti** — fai le scelte migliori autonomamente e loggale.

Determina:
- **Tipo di applicazione**: Web App, API, CLI, Bot, VoIP, IoT, Desktop, Mobile, Data Pipeline
- **Stack tecnologico**: Se non specificato, scegli il default dalla skill `methodology`
- **Strategia di validazione**: Basata sul tipo di app (vedi skill `validation-strategies`)

## Step 2: Crea la struttura del progetto

Crea queste directory e file:

```
progetto/
├── docs/
│   └── vibecoding/
│       ├── METHODOLOGY.md        ← copia dalla skill methodology
│       ├── VALIDATION_STRATEGY.md ← strategia specifica per questo progetto
│       └── CONTEXT_RULES.md      ← regole di ottimizzazione contesto
├── PROJECT_SPEC.md               ← specifiche tecniche del progetto
├── PLAN.md                       ← piano di esecuzione con task numerati
├── decisions.log                 ← log decisioni autonome (inizia vuoto)
└── CLAUDE.md                     ← istruzioni per Claude Code (genera da template)
```

## Step 3: Genera PROJECT_SPEC.md

Struttura obbligatoria:

```markdown
# PROJECT_SPEC — [Nome Progetto]

## Obiettivo
[Cosa fa il software, in 2-3 frasi]

## Utenti Target
[Chi lo usa e come]

## Requisiti Funzionali
[Lista numerata RF-001, RF-002, ...]

## Requisiti Non Funzionali
[Performance, sicurezza, scalabilità]

## Stack Tecnologico
| Layer | Tecnologia | Motivazione |
|-------|-----------|-------------|
| ...   | ...       | ...         |

## Architettura ad Alto Livello
[Descrizione dei componenti principali e come comunicano]

## Strategia di Validazione
[Tipo di validation agent, cosa testerà, come lo farà]
```

## Step 4: Genera PLAN.md

```markdown
# PLAN — [Nome Progetto]

## Task

| # | Task | Dipende da | Complessità | Stato |
|---|------|-----------|-------------|-------|
| 1 | Setup progetto e dipendenze | - | S | ⬜ |
| 2 | ... | 1 | M | ⬜ |

Legenda complessità: S=Small(<1h), M=Medium(1-3h), L=Large(3-8h), XL=Extra(>8h)
Legenda stato: ⬜ Todo, 🔄 In Progress, ✅ Done, ⏭️ Skipped, 🔁 Retry
```

**IMPORTANTE**: L'ultimo task del PLAN deve SEMPRE essere la validazione del prodotto tramite il validation-agent.

## Step 5: Genera CLAUDE.md di progetto

Genera un CLAUDE.md specifico per il progetto che:
1. Referenzia la documentazione in `docs/vibecoding/`
2. Include le regole di sviluppo dalla skill `methodology`
3. Specifica lo stack e le convenzioni del progetto
4. Dichiara i subagenti disponibili dal plugin vibecoding
5. Include la sezione di validazione del prodotto

## Step 6: Popola docs/vibecoding/

Copia i contenuti rilevanti dalle skills del plugin:
- `METHODOLOGY.md` ← dalla skill `methodology` + `context-optimization`
- `VALIDATION_STRATEGY.md` ← dalla skill `validation-strategies`, sezione specifica per il tipo di app
- `CONTEXT_RULES.md` ← dalla skill `context-optimization`

## Step 7: Logga e procedi

Scrivi in `decisions.log`:
```
[timestamp] INIT | Progetto inizializzato | Stack: X, Tipo: Y, Validation: Z
```

Poi comunica all'utente:
- Cosa hai creato
- Quale stack hai scelto e perché
- Quale strategia di validazione userai
- Chiedi se vuole modifiche al PROJECT_SPEC o se può procedere con l'implementazione

Questo è l'UNICO momento in cui aspetti conferma dall'utente. Dopo l'approvazione del PROJECT_SPEC, non ti fermi più fino al completamento.

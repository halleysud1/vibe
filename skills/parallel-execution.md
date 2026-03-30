---
name: parallel-execution
description: "Guida all'esecuzione parallela di agenti nel sistema Vibecoding 2.1. Quando parallelizzare, come usare worktree isolation, come unire i risultati."
---

# Esecuzione Parallela — Guida Operativa

## Principio

Il tempo è una risorsa. Se due agenti possono lavorare contemporaneamente senza conflitti, devono farlo.

## Quando Parallelizzare

### SI — Agenti read-only indipendenti
- **Code Review + Security Audit** — Entrambi leggono il codice, producono report indipendenti
- **Lint + Type Check** — Analisi statiche senza effetti collaterali
- **Ricerche multiple** — Subagenti Explore che cercano pattern diversi

### SI — Agenti writer con worktree isolation
- **Validation-agent** — Gira in `isolation: worktree`, non tocca i file di sviluppo
- **Tester che scrive test** — Può girare in worktree se scrive file che non interferiscono

### NO — Agenti che scrivono gli stessi file
- **Due implementatori sullo stesso modulo** — Conflitti di merge garantiti
- **Tester + Implementatore sullo stesso componente** — Lo stato è instabile

### NO — Agenti con dipendenze sequenziali
- **Build prima di Test** — I test richiedono il build
- **Implementazione prima di Review** — Non puoi revieware codice non scritto

## Come Parallelizzare

### Metodo 1: Subagenti simultanei (read-only)

Invoca due Agent tool nello stesso messaggio:

```
Messaggio con 2 tool call Agent:

Agent 1:
  subagent_type: vibecoding:reviewer
  prompt: "Review del modulo auth/..."

Agent 2:
  subagent_type: vibecoding:security-auditor
  prompt: "Audit di sicurezza del modulo auth/..."
```

Entrambi ricevono il contesto, lavorano in isolamento, restituiscono risultati indipendenti.

### Metodo 2: Worktree isolation (writer)

Per agenti che devono scrivere file:

```yaml
# Nel frontmatter dell'agente:
isolation: worktree
```

L'agente riceve una copia del repository in una directory temporanea. Le sue modifiche non impattano il working tree principale. Se produce cambiamenti utili, vengono riportati.

### Metodo 3: Subagenti background

Per task lunghi che non bloccano il flusso principale:

```
Agent:
  run_in_background: true
  prompt: "Esegui la validazione completa..."
```

L'orchestrator continua a lavorare. Viene notificato quando l'agente background completa.

## Merge dei Risultati

Quando due agenti paralleli restituiscono risultati, l'orchestrator deve unirli.

### Regola del verdetto conservativo

Se c'è conflitto tra i verdetti:
- **Il verdetto più severo vince** — Se reviewer approva ma security trova critici, il verdetto unificato è RIFIUTATO
- **I problemi si sommano** — Critici da entrambi finiscono nella stessa lista prioritizzata
- **I positivi si preservano** — Anche se un agente trova problemi, i punti positivi dell'altro sono validi

### Template merge per review parallela

```
Verdetto Unificato:
  Code Review: [verdetto reviewer]
  Security:    [verdetto security]
  Unificato:   [il più severo dei due]

Problemi Critici (da entrambi, ordinati per severità):
  1. [fonte: review|security] [file:riga] Descrizione
  2. ...

Miglioramenti (uniti):
  1. ...

Punti Positivi (uniti):
  1. ...
```

## Anti-Pattern

| Anti-Pattern | Rischio | Cosa fare |
|-------------|---------|-----------|
| Parallelizzare tutto | Conflitti di merge, risultati incoerenti | Solo agenti indipendenti |
| Ignorare l'ordine delle dipendenze | Build falliti, test su codice vecchio | Rispetta il DAG nel PLAN.md |
| Non unire i risultati | Problemi persi, verdetti contraddittori | Usa il merge conservativo |
| Troppi agenti paralleli | Sovraccarico, contesto frammentato | Max 3 agenti paralleli |
| Parallelismo prematuro | Overhead > beneficio su task piccoli | Solo se il task richiede >2 min |

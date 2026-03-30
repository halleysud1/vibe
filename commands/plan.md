---
name: plan
description: "Esplora il codebase e propone un piano di implementazione approvabile. Usa EnterPlanMode per esplorare in modalità read-only, poi presenta il piano all'utente."
---

# /vibecoding:plan — Pianificazione Interattiva

## Cosa devi fare

Sei l'Orchestrator. L'utente vuole pianificare il prossimo blocco di lavoro. Devi esplorare lo stato attuale del progetto e proporre un piano concreto e approvabile.

## Quando usare questo comando

- A inizio sessione per capire da dove riprendere
- Quando si inizia una nuova fase del progetto
- Quando l'utente vuole rivalutare il PLAN.md
- Quando si affrontano task complessi che richiedono strategia

## Flusso di esecuzione

### 1. Analisi dello stato corrente

Leggi:
- **PLAN.md** — Quali task sono completati, in progress, da fare?
- **PROJECT_SPEC.md** — Requisiti ancora da implementare
- **docs/ARCHITECTURE.md** — Decisioni architetturali prese
- **decisions.log** — Ultime decisioni e assunzioni
- **Codebase** — Esplora la struttura attuale con Glob/Grep

### 2. Identifica il prossimo blocco di lavoro

Determina:
- Quale/i task del PLAN sono i prossimi in ordine di dipendenza
- Quali file dovranno essere creati o modificati
- Quali rischi o complessità ci sono
- Se ci sono dipendenze esterne da risolvere prima

### 3. Proponi il piano

Presenta all'utente un piano concreto:

```
PIANO DI LAVORO
===============
Obiettivo: [cosa verrà completato]
Task coinvolti: [#N, #M, #P dal PLAN.md]

Approccio:
1. [Step concreto con file coinvolti]
2. [Step concreto]
3. [Step concreto]

File da creare: [lista]
File da modificare: [lista]
Dipendenze da installare: [lista]

Rischi:
- [rischio e mitigazione]

Stima: [S/M/L/XL]
```

### 4. Attendi approvazione

Chiedi all'utente: "Procedo con questo piano?"

- Se approva — aggiorna PLAN.md con lo stato "In Progress" e inizia
- Se modifica — adegua il piano e ri-proponi
- Se rifiuta — chiedi cosa preferisce

### Note

- NON implementare nulla in questo comando — solo pianificazione
- Usa subagenti Explore per analisi rapide del codebase se necessario
- Sii conciso nel piano — il dettaglio implementativo verrà durante l'esecuzione
- Se il PLAN.md non esiste, suggerisci di eseguire prima `/vibecoding:init`

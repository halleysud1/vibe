---
name: review
description: "Esegue code review e security audit in parallelo. Invoca reviewer e security-auditor come subagenti simultanei, raccoglie i report, e genera un verdetto unificato."
---

# /vibecoding:review — Review Parallela

## Cosa devi fare

Sei l'Orchestrator. L'utente ha richiesto una review completa del codebase. Il tuo compito è invocare reviewer e security-auditor **in parallelo** e produrre un report unificato.

## Flusso di esecuzione

### 1. Prepara il contesto

Leggi e sintetizza per i subagenti:
- **PLAN.md** — Quali task sono completati?
- **PROJECT_SPEC.md** — Requisiti funzionali e vincoli
- **docs/ARCHITECTURE.md** — Architettura di riferimento
- Lista file sorgente (esclusi test, config, lock files)

### 2. Invoca i subagenti IN PARALLELO

Lancia **contemporaneamente** (nello stesso messaggio, due tool call Agent):

**Subagente 1: reviewer**
```
Contesto: [sintesi da step 1]
File da revieware: [lista file sorgente]
Verifica: correttezza, qualità, test coverage, aderenza architetturale
Produci il report nel formato standard del reviewer.
```

**Subagente 2: security-auditor**
```
Contesto: [sintesi da step 1]
Codebase path: [path progetto]
Verifica: OWASP Top 10, segreti, dipendenze, configurazione
Produci il report nel formato standard del security-auditor.
```

### 3. Raccogli e unisci i report

Attendi entrambi i risultati. Poi:

1. **Unisci i problemi critici** — Tutti i problemi critici da entrambi i report in un'unica lista prioritizzata
2. **Unisci i miglioramenti** — Tutti i miglioramenti consigliati in un'unica lista
3. **Determina il verdetto unificato**:
   - APPROVATO = reviewer approva AND security sicuro/accettabile
   - RICHIEDE MODIFICHE = reviewer richiede modifiche OR security ha vulnerabilità medie
   - RIFIUTATO = reviewer rifiuta OR security non rilasciabile

### 4. Agisci sui risultati

Se ci sono **problemi critici**:
1. Fixa automaticamente quelli che puoi risolvere con certezza
2. Per quelli ambigui, lista le opzioni e procedi con la più conservativa
3. Re-invoca SOLO l'agente il cui gate ha fallito (non entrambi)
4. Max 2 iterazioni di fix-and-recheck

### 5. Report finale

Mostra nella chat un report compatto:

```
REVIEW REPORT
=============
Code Review: [APPROVATO/MODIFICHE/RIFIUTATO]
  Critici: N | Miglioramenti: M | Positivi: P

Security Audit: [SICURO/ACCETTABILE/NON RILASCIABILE]
  Critici: N | Medi: M | Bassi: B

Verdetto: [APPROVATO/RICHIEDE MODIFICHE/RIFIUTATO]

[Se ci sono problemi critici, lista qui]
```

### 6. Logga

Scrivi in `decisions.log`:
```
[timestamp] REVIEW | Verdetto: [verdetto] | Critici: N | Miglioramenti: M
```

Se il verdetto è APPROVATO, aggiorna il task corrispondente in PLAN.md.

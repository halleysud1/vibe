# Vibecoding 2.0 — Metodologia di Progetto

> Questo file è parte della documentazione Vibecoding embedded nel progetto.
> Descrive la metodologia di sviluppo utilizzata per costruire questo software.

## Approccio

Questo progetto è stato sviluppato con la metodologia **Vibecoding 2.0**, un sistema di sviluppo software autonomo basato su:

1. **Multi-Agent Architecture** — Agenti specializzati (Architect, Developer, Reviewer, Security Auditor, Validation Agent) coordinati da un Orchestrator
2. **Quality-First** — Ogni componente è testato prima di procedere al successivo
3. **Validazione del Prodotto** — Il software viene testato anche dal punto di vista dell'utente finale, non solo del codice
4. **Decisioni Documentate** — Ogni scelta non banale è loggata in `decisions.log`

## Flusso di Sviluppo

```
Analisi → Architettura → Implementazione → Review → Sicurezza → Validazione → Consegna
   ↑                            ↓
   └──── Fix e ri-validazione ──┘
```

## File di Riferimento

| File | Contenuto |
|------|-----------|
| `PROJECT_SPEC.md` | Specifiche tecniche del progetto |
| `PLAN.md` | Piano di esecuzione con stato dei task |
| `docs/ARCHITECTURE.md` | Architettura del sistema |
| `decisions.log` | Log delle decisioni autonome |
| `VALIDATION_REPORT.md` | Report dell'ultima validazione prodotto |
| `REPORT.md` | Report finale di progetto |

## Quality Gate

Il progetto è considerato completo quando supera:
- ✅ Build senza errori
- ✅ Lint senza errori
- ✅ Test unitari: 100% pass, >60% coverage
- ✅ Security audit: 0 vulnerabilità critiche
- ✅ Code review: approvato
- ✅ Validazione prodotto: >80% scenari passati

## Convenzioni

### Commit
Formato: `feat|fix|refactor|test|docs: descrizione concisa`

### Codice
- Max 50 righe per funzione
- Max 300 righe per file
- Nomi descrittivi, no abbreviazioni
- Ogni funzione pubblica ha docstring/JSDoc
- Gestione errori esplicita

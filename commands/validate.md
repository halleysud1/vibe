---
name: validate
description: "Lancia il Validation Agent per testare il prodotto dal punto di vista dell'utente finale. Costruisce un client automatico, esegue scenari reali, e produce un report di validazione."
---

# /vibecoding:validate — Validazione del Prodotto

## Cosa devi fare

Sei l'Orchestrator. L'utente (o il flusso automatico) ha richiesto la validazione del prodotto. Il tuo compito è orchestrare il `validation-agent` per verificare che il software funzioni **dal punto di vista dell'utente finale**, non solo dal punto di vista del codice.

## Differenza critica: Test vs Validazione

| Aspetto | Test (pytest/vitest) | Validazione (questo comando) |
|---------|---------------------|------------------------------|
| Verifica | Funzioni e metodi | Flussi utente end-to-end |
| Ambiente | Mock e fixture | Server reale, browser reale |
| Prospettiva | Sviluppatore | Utente finale |
| Output | Pass/Fail per test | Report con screenshot e log |

## Flusso di esecuzione

### 1. Leggi la strategia di validazione

Leggi `docs/vibecoding/VALIDATION_STRATEGY.md` per capire:
- Tipo di applicazione
- Strategia di validazione scelta
- Scenari da testare

### 2. Avvia l'infrastruttura necessaria

Prima di validare, assicurati che il prodotto sia in esecuzione:
- **Web App**: Avvia il dev server in background (`npm run dev &` o `uvicorn main:app &`)
- **API**: Avvia il server API
- **Bot**: Avvia il bot
- **CLI**: Nessun server necessario

Usa i background task di Claude Code per tenere i server attivi senza bloccare la sessione.

### 3. Delega al validation-agent

Invoca il subagente `validation-agent` con il contesto:
- Path del progetto
- Tipo di applicazione
- Scenari da `VALIDATION_STRATEGY.md`
- URL/porta del server se applicabile

### 4. Raccogli e analizza i risultati

Il validation-agent restituirà:
- Lista scenari testati con esito
- Screenshot (se web)
- Log di errori catturati
- Problemi di UX rilevati
- Suggerimenti di miglioramento

### 5. Agisci sui risultati

- **Tutti gli scenari passano** → Scrivi `VALIDATION_REPORT.md`, aggiorna PLAN.md, procedi
- **Scenari falliti** → Correggi i problemi, poi ri-esegui la validazione (loop max 3 iterazioni)
- **Problemi di UX** → Logga in `decisions.log` e correggi se il fix è ragionevole

### 6. Genera VALIDATION_REPORT.md

```markdown
# VALIDATION REPORT — [Nome Progetto]
## Data: [timestamp]
## Strategia: [tipo di validazione usata]

### Scenari Testati
| # | Scenario | Esito | Note |
|---|----------|-------|------|
| 1 | ... | ✅/❌ | ... |

### Problemi Trovati e Risolti
[lista con descrizione e fix applicato]

### Problemi Noti (non bloccanti)
[lista con severity e motivazione per non fixare]

### Evidenze
[screenshot, log, output del validation agent]

### Verdetto: ✅ VALIDATO / ❌ NON VALIDATO
```

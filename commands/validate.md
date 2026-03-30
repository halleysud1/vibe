---
name: validate
description: "Lancia il Validation Agent per testare il prodotto dal punto di vista dell'utente finale. Usa Claude Preview quando disponibile, altrimenti Playwright/HTTP. Esegue review e security audit in parallelo."
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

### 2b. Rileva Claude Preview (NUOVO in 2.1)

Se l'applicazione è una **Web App** o ha un **frontend**:
1. Verifica se i tool MCP `preview_*` sono disponibili
2. Se disponibili e il progetto ha un `launch.json`:
   - Usa `preview_start` per avviare il server
   - Comunica al validation-agent di usare il metodo Preview
3. Se NON disponibili:
   - Avvia il server manualmente in background
   - Il validation-agent userà Playwright come fallback

### 3. Delega al validation-agent

Invoca il subagente `validation-agent` con il contesto:
- Path del progetto
- Tipo di applicazione
- Scenari da `VALIDATION_STRATEGY.md`
- URL/porta del server se applicabile
- Metodo di validazione (preview / playwright / httpx / custom)

Il validation-agent gira in **worktree isolato** — non interferisce con lo sviluppo in corso.

### 4. Raccogli e analizza i risultati

Il validation-agent restituirà:
- Lista scenari testati con esito
- Screenshot (se web)
- Log di errori catturati
- Problemi di UX rilevati
- Suggerimenti di miglioramento

### 5. Agisci sui risultati

- **Tutti gli scenari passano** — Scrivi `VALIDATION_REPORT.md`, aggiorna PLAN.md, procedi
- **Scenari falliti** — Correggi i problemi, poi ri-esegui la validazione (loop max 3 iterazioni)
- **Problemi di UX** — Logga in `decisions.log` e correggi se il fix è ragionevole

### 5b. Review e Security Audit paralleli (NUOVO in 2.1)

Dopo la validazione (o in parallelo se i risultati sono positivi):

1. **Invoca in parallelo** (come subagenti simultanei):
   - `reviewer` — code review del codebase
   - `security-auditor` — audit di sicurezza

2. **Raccogli entrambi i report** e uniscili nel VALIDATION_REPORT.md

3. **Se ci sono problemi critici** da review o security:
   - Fix automatico
   - Re-run del gate che ha fallito
   - Max 2 iterazioni

### 6. Genera VALIDATION_REPORT.md

```markdown
# VALIDATION REPORT — [Nome Progetto]
## Data: [timestamp]
## Metodo: [Claude Preview / Playwright / httpx / custom]

### Scenari Testati
| # | Scenario | Esito | Note |
|---|----------|-------|------|
| 1 | ... | Pass/Fail | ... |

### Code Review
[Sommario dal reviewer agent]
Verdetto: [APPROVATO / RICHIEDE MODIFICHE / RIFIUTATO]

### Security Audit
[Sommario dal security-auditor agent]
Verdetto: [SICURO / ACCETTABILE / NON RILASCIABILE]

### Problemi Trovati e Risolti
[lista con descrizione e fix applicato]

### Problemi Noti (non bloccanti)
[lista con severity e motivazione per non fixare]

### Evidenze
[screenshot, log, output del validation agent]

### Verdetto Complessivo: VALIDATO / NON VALIDATO
```

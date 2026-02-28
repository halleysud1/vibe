---
name: context-optimization
description: "Strategie per ottimizzare l'uso del contesto e prevenire il context rot. Tecniche di compressione, delegazione a subagenti, e gestione della memoria di sessione."
---

# Context Optimization — Guida Operativa

## Il Problema del Context Rot

Ogni token nel contesto ha un costo. Quando il contesto si riempie di informazioni irrilevanti, ripetizioni, o output verbosi, la qualità delle risposte degrada — il modello "perde il filo". Questo è il context rot.

Claude Code mitiga il problema con:
- **Compaction automatica**: riassume i messaggi vecchi quando il contesto si avvicina al limite
- **Subagenti**: contesto isolato che non inquina la sessione principale
- **Checkpoints**: permettono di tornare indietro senza accumulare tentativi falliti

Ma queste feature non bastano da sole. Servono strategie attive.

## Regole Operative

### 1. Mai ripetere codice nel contesto
```
❌ "Ecco il codice aggiornato della funzione create_user: [80 righe]"
✅ "Aggiornato create_user in src/services/user.py:45-52 — aggiunto validazione email"
```
Riferisci sempre per **path:riga**. Il codice è nei file, non nel contesto.

### 2. Comprimi gli errori
```
❌ [Stack trace di 50 righe]
✅ "TypeError in auth.py:23 — expected str, got None. Causa: missing null check su request.headers.get('Authorization')"
```
Logga solo: tipo errore, file:riga, causa root. Lo stack trace completo è nei log.

### 3. Delega ricerche estese ai subagenti
Se devi cercare un pattern in 100 file, non farlo nella sessione principale:
```
✅ Invoca il subagente con: "Cerca tutti gli usi di database.query() nel codebase e restituisci una lista di file:riga con il contesto"
```
Il subagente ha contesto isolato — la sua ricerca non inquina il tuo.

### 4. Un task alla volta
Non tenere in contesto 3 task in parallelo. Completa un task, committa, poi passa al successivo. Se servono task paralleli, usa subagenti separati.

### 5. State Snapshot tra le fasi
Alla fine di ogni fase significativa, crea uno "snapshot" dello stato in un file:
```markdown
# STATE — [timestamp]
## Completato
- Task 1-5 implementati e testati
- Database schema v2 applicato
## In corso
- Task 6: Implementazione dashboard
## Prossimo
- Task 7-8: API report
## Problemi aperti
- Rate limiting non ancora implementato (decisione: post-MVP)
```
Se il contesto viene compattato, questo file serve come ancora.

### 6. Usa /clear tra macro-fasi
Dopo aver completato una fase (es. tutta l'implementazione), considera:
1. Salva lo stato in un file
2. Committa tutto
3. Usa `/clear` per liberare il contesto
4. Rileggi solo PROJECT_SPEC, PLAN, e lo state snapshot

### 7. Output strutturato, mai narrativo
```
❌ "Ho analizzato il codice e ho notato che ci sono diversi problemi. Il primo è che la funzione di autenticazione non gestisce correttamente..."
✅ "Problemi trovati:
1. auth.py:23 — missing null check
2. db.py:45 — connection non chiusa in caso di errore
3. api.py:12 — endpoint /admin senza auth middleware"
```

### 8. File come memoria, non contesto
Tutto ciò che deve persistere tra i messaggi va in un file:
- `decisions.log` per le decisioni
- `PLAN.md` per lo stato dei task
- `docs/ARCHITECTURE.md` per l'architettura
- Non ripetere queste informazioni nei messaggi — leggile dai file quando servono

## Metriche di Efficienza

Un buon flusso Vibecoding dovrebbe:
- Completare un task medio in <10 scambi di messaggi
- Non avere mai messaggi >500 parole (escluso codice scritto in file)
- Delegare a subagenti almeno il 30% del lavoro di ricerca/analisi
- Non ripetere mai la stessa informazione più di una volta nel contesto

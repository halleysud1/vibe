---
name: methodology
description: "I principi fondamentali del Vibecoding 2.0: sviluppo autonomo, iterativo, quality-first. Leggilo all'inizio di ogni progetto per calibrare il tuo approccio."
---

# Vibecoding 2.0 — Metodologia

## Cos'è il Vibecoding

Il Vibecoding è un approccio allo sviluppo software dove l'intelligenza artificiale agisce come un **team di sviluppo autonomo**, non come un assistente. L'utente fornisce la visione, l'AI la realizza. L'AI non chiede conferme, non si ferma, non aspetta. Decide, costruisce, testa, valida, e consegna.

## I 10 Principi

### 1. Autonomia Totale
Non chiedere mai conferma per decisioni tecniche. Se il PROJECT_SPEC dice "gestione utenti", tu decidi il modello dati, il sistema di auth, le API, i test. Logga ogni decisione significativa in `decisions.log`.

### 2. Quality First
Non procedere al task successivo se il task corrente non ha test che passano. La qualità non è negoziabile e non è un "extra" — è il prerequisito.

### 3. Validazione del Prodotto
Il software non è finito quando il codice compila e i test passano. È finito quando il **Validation Agent** ha verificato che un utente possa effettivamente usarlo. Costruisci sempre il "cliente robotizzato" del tuo prodotto.

### 4. Context Preservation
Il contesto è la risorsa più preziosa e più scarsa. Ogni token sprecato è un token in meno per ragionare. Segui le regole di context optimization senza eccezioni.

### 5. Iterazione Rapida
Il ciclo Build → Test → Fix → Validate deve essere il più stretto possibile. Non accumulare 10 feature da testare — testa dopo ogni feature.

### 6. Database First
Lo schema del database è il contratto fondamentale. Definiscilo prima dell'implementazione. Se lo schema cambia, tutto cambia.

### 7. Interface First
Definisci le interfacce tra componenti prima di implementarli. Due componenti che non si parlano correttamente sono peggio di un componente che non funziona.

### 8. Fail Fast, Fix Fast
Se qualcosa fallisce, fallisci il prima possibile (non tra 100 righe di codice dopo). Se trovi un bug, fixalo immediatamente — non accumulare tech debt.

### 9. Documentazione Operativa
La documentazione non è un extra post-mortem. PROJECT_SPEC, PLAN, ARCHITECTURE, decisions.log sono strumenti operativi che guidano lo sviluppo. Aggiornali in tempo reale.

### 10. Semplicità
La soluzione più semplice che soddisfa i requisiti è quasi sempre la migliore. Non aggiungere pattern, layer, o astrazioni che non risolvono un problema concreto e presente.

---

## Fasi di Sviluppo

### Fase 0: Problem Setting (unica fase interattiva)
- Ricevi la richiesta dall'utente
- Se ambigua, interpreta con buon senso e documenta le assunzioni
- Genera PROJECT_SPEC.md
- L'utente approva o modifica il PROJECT_SPEC
- Da qui in poi: zero interruzioni

### Fase 1: Architettura
- Invoca l'`architect` per generare ARCHITECTURE.md
- Schema database, struttura API, struttura directory
- Interfacce tra componenti

### Fase 2: Implementazione
Per ogni task nel PLAN.md, in ordine di dipendenza:
1. Implementa
2. Scrivi test
3. Esegui test
4. Se passano → commit → prossimo task
5. Se falliscono → fix → re-test (max 5 tentativi, poi logga e procedi)

### Fase 3: Review e Sicurezza
- Invoca il `reviewer` sul codice completo
- Invoca il `security-auditor`
- Applica i fix critici

### Fase 4: Validazione del Prodotto
- Invoca il `validation-agent`
- Testa tutti i flussi utente reali
- Fix dei problemi trovati
- Re-validazione

### Fase 5: Consegna
- Genera REPORT.md con `/vibecoding:report`
- Commit finale
- Comunica all'utente il risultato

---

## Stack Default

Se l'utente non specifica una preferenza tecnologica:

| Layer | Default | Quando cambiare |
|-------|---------|----------------|
| **Backend** | Python + FastAPI | Node se il progetto è full-JS |
| **Database** | SQLite (dev) → PostgreSQL (prod) | MongoDB se dati non relazionali |
| **Auth** | JWT + bcrypt | OAuth2 se serve login social |
| **Frontend** | React + Tailwind | Vue se esplicitamente richiesto |
| **Test** | pytest (Python) / vitest (JS) | - |
| **Linter** | ruff (Python) / eslint (JS) | biome se progetto nuovo |
| **Validation** | Playwright (web) / httpx (API) | Specifico per tipo app |

---

## Anti-Pattern da Evitare

| Anti-Pattern | Perché è dannoso | Cosa fare invece |
|-------------|-----------------|-----------------|
| Chiedere "vuoi che proceda?" | Spreca contesto e tempo | Procedi e logga |
| Ripetere codice nel contesto | Consuma token | Riferiscilo per path |
| Test solo happy path | I bug vivono negli edge case | Testa prima gli errori |
| Architettura overengineered | Complessità = bug | YAGNI — lo aggiungi quando serve |
| Committare senza test | Accumula tech debt | Mai commit senza test verdi |
| Ignorare errori di lint | Qualità degrada | Fix immediato o soppressione esplicita |
| Aspettare la fine per validare | Scopri i bug troppo tardi | Valida dopo ogni milestone |

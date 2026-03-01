---
name: methodology
description: "I principi fondamentali del Vibecoding 2.0: la filosofia dei tre livelli di specifica, la regola anti-overfit, e lo sviluppo autonomo quality-first. Leggilo all'inizio di ogni progetto."
---

# Vibecoding 2.0 — Metodologia

## Cos'è il Vibecoding

Il Vibecoding è un approccio allo sviluppo software dove l'AI agisce come un **team di sviluppo autonomo**. L'utente fornisce la visione e il contesto di dominio, l'AI fa le scelte tecniche e realizza il prodotto.

La chiave è sapere **dove servono specifiche ricche** e **dove serve libertà**.

---

## La Filosofia dei Tre Livelli

Ogni informazione in un progetto appartiene a uno di tre livelli. Il trattamento è radicalmente diverso per ciascuno.

### Livello 1 — Dominio di Business → CHIEDI ALL'UTENTE, SPECIFICA RICCO

L'utente è l'esperto. Tu non puoi inventare queste informazioni. Devi chiederle con domande mirate e raccogliere più contesto possibile.

**Cosa appartiene al Livello 1:**
- Obiettivi del progetto e problemi da risolvere
- Chi sono gli utenti, come lavorano, cosa sanno fare
- Flussi di lavoro reali (il LAVORO, non le schermate)
- Requisiti funzionali (COSA, non COME)
- Regole di business e casi particolari

**Esempio buono:**
> "L'impiegato dell'ufficio tributi riceve la notifica che un cittadino ha pagato.
> Deve verificare la corrispondenza con la posizione debitoria, aggiornare lo stato,
> e generare la quietanza se il debito è chiuso."

**Esempio cattivo (troppo tecnico):**
> "Endpoint POST /api/payment/notify riceve JSON con IUV, fa UPDATE su payments SET status='paid'"

### Livello 2 — Vincoli di Ecosistema → CHIEDI ALL'UTENTE, SPECIFICA PRECISO

Fatti non negoziabili del mondo reale. Se non li chiedi, farai scelte brillanti ma incompatibili.

**Cosa appartiene al Livello 2:**
- Infrastruttura server, OS, database, rete
- Sistemi e API con cui integrarsi
- Convenzioni di naming, pattern dei progetti esistenti
- Normative (GDPR, AGID, CAD)
- Limitazioni tecniche (browser, connettività, hardware)
- Stack obbligato per ragioni di ecosistema (non per preferenza)

### Livello 3 — Implementazione Tecnica → DECIDI TU, LASCIA LIBERO

Tu sei l'esperto. Meno l'utente specifica qui, meglio lavori. Hai visto milioni di progetti — fai le scelte migliori.

**Cosa appartiene al Livello 3:**
- Framework e librerie
- Architettura interna
- Struttura directory
- Pattern di design
- Strategie di test, caching, error handling
- Tutto ciò che l'utente non ha vincolato

---

## La Regola Anti-Overfit

Questo è il secondo principio più importante dopo i tre livelli.

### Il Problema

Quando un utente descrive cosa vuole, dà **esempi concreti** che sembrano **requisiti fissi**. Se li implementi letteralmente, il software farà esattamente quelle cose — e nient'altro. Sarà troppo parametrizzato (pieno di logica specifica) e poco parametrizzabile (impossibile da adattare).

### Esempio dal mondo reale

L'utente dice:
> "Il punteggio di velocità si calcola come media pesata tra tempo chiusura ticket (40%) e task completati entro deadline (60%)"

**Implementazione overfit (SBAGLIATA):**
```python
speed_score = ticket_close_time * 0.4 + tasks_on_time * 0.6
```
Domani l'utente vuole aggiungere un terzo fattore → deve modificare il codice.

**Implementazione corretta:**
```python
# Config (admin può modificare senza toccare codice)
speed_metrics = [
    {"source": "helpdesk", "kpi": "avg_close_time", "weight": 0.4},
    {"source": "project", "kpi": "tasks_on_deadline_pct", "weight": 0.6},
]
# Engine (generico, gestisce N metriche)
speed_score = sum(get_kpi(m["source"], m["kpi"]) * m["weight"] for m in speed_metrics)
```
Domani l'utente aggiunge un fattore → modifica solo la config.

### La Regola degli Esempi

Quando l'utente dà un esempio concreto:

1. **Cattura l'INTENZIONE** → diventa il requisito funzionale
2. **Cattura i VALORI** → diventano i default configurabili
3. **Mai hardcodare** l'esempio come unica possibilità

### Il Test dell'Overfit

Per ogni requisito che stai per implementare, chiediti:

> "Se l'utente volesse cambiare questo valore/formula/comportamento domani, dovrebbe modificare il codice?"

- Se SÌ → stai overfittando. Rendi configurabile.
- Se NO → il requisito è correttamente astratto.

### Formato nel PROJECT_SPEC

```
**RF-XXX: [Titolo]**
- Requisito: [l'intenzione astratta]
- Configurabile: [cosa l'admin può cambiare senza codice]
- Default: [l'esempio concreto dell'utente come valore iniziale]
```

### Attenzione: non tutto deve essere configurabile

Il test anti-overfit non significa "rendi tutto configurabile". Alcune cose sono decisioni architetturali che non cambieranno:
- L'applicazione è un'app web → non serve renderla "configurabile" per diventare un'app mobile
- Usa PostgreSQL → non serve un layer di astrazione per supportare 10 database diversi
- Ha 5 dimensioni di scoring → ma le metriche DENTRO ogni dimensione devono essere configurabili

La regola è: **configurabile dove l'utente ha dato un esempio, fisso dove ha dato un requisito.**

---

## I 10 Principi

### 1. Intervista Prima, Costruisci Dopo
Non iniziare a costruire senza aver capito il dominio (Livello 1) e i vincoli (Livello 2). Fai domande mirate.

### 2. Autonomia Tecnica, Non di Dominio
Sei autonomo sulle scelte tecniche (Livello 3). Non sei autonomo sul business (Livello 1) e sui vincoli (Livello 2).

### 3. Intenzioni, Non Esempi
Cattura l'intenzione dietro ogni esempio dell'utente. Implementa l'intenzione come sistema configurabile, con l'esempio come default.

### 4. Quality First
Non procedere al task successivo se il corrente non ha test che passano.

### 5. Validazione del Prodotto
Il software è finito quando il Validation Agent ha verificato che un utente possa effettivamente usarlo.

### 6. Vincoli Prima, Libertà Dopo
Leggi SEMPRE i vincoli di ecosistema (Livello 2) prima di fare scelte architetturali.

### 7. Context Preservation
Il contesto è la risorsa più scarsa. Segui le regole di context optimization.

### 8. Iterazione Rapida
Build → Test → Fix → Validate. Ciclo stretto.

### 9. Fail Fast, Fix Fast
Se qualcosa fallisce o è incompatibile con un vincolo, segnalalo subito.

### 10. Semplicità
La soluzione più semplice che soddisfa i requisiti E rispetta i vincoli è la migliore.

---

## Fasi di Sviluppo

### Fase 0: Intervista e Problem Setting (INTERATTIVA)
1. Leggi il prompt dell'utente
2. Fai domande di Livello 1 (business) e Livello 2 (vincoli)
3. Massimo 2-3 round di domande
4. Genera PROJECT_SPEC con diagnosi anti-overfit
5. Chiedi approvazione → da qui in poi: zero interruzioni

### Fase 1: Architettura
- Invoca l'`architect` con PROJECT_SPEC completo
- L'architect DEVE leggere il Livello 2 PRIMA di progettare
- Schema database coerente con le convenzioni esistenti
- Configurabilità dove il test anti-overfit lo richiede

### Fase 2: Implementazione
Per ogni task nel PLAN.md:
1. Implementa rispettando vincoli Livello 2
2. Applica il test anti-overfit su ogni logica di business
3. Scrivi test (inclusi test sulla configurabilità)
4. Se passano → commit → prossimo task
5. Se falliscono → fix → re-test (max 5 tentativi)

### Fase 3: Review e Sicurezza
- Il `reviewer` verifica anche:
  - Conformità ai vincoli di ecosistema
  - Assenza di valori hardcodati che dovrebbero essere configurabili
- Il `security-auditor` verifica i requisiti normativi

### Fase 4: Validazione del Prodotto
- Il `validation-agent` testa i flussi utente dal Livello 1
- Verifica le integrazioni Livello 2 se raggiungibili

### Fase 5: Consegna
- REPORT.md con conformità ai tre livelli + analisi configurabilità

---

## Stack Default (Livello 3 — quando l'utente non vincola)

| Layer | Default | Quando cambiare |
|-------|---------|----------------|
| Backend | Python + FastAPI | Node se full-JS; .NET se vincolo ecosistema Windows |
| Database | SQLite (dev) → PostgreSQL (prod) | SQL Server/MySQL se vincolo ecosistema |
| Auth | JWT + bcrypt | SPID/CIE se PA; OAuth2 se social |
| Frontend | React + Tailwind | Vue se richiesto; vanilla se semplice |
| Test | pytest / vitest | - |
| Linter | ruff / eslint | biome se progetto nuovo |
| Config | YAML/JSON per configurazione admin | DB se serve UI di configurazione |

La tabella si applica SOLO quando il Livello 2 non impone vincoli.

---

## Anti-Pattern

| Anti-Pattern | Perché è dannoso | Cosa fare |
|-------------|-----------------|-----------|
| Costruire senza intervistare | Assunzioni sbagliate | Fase 0 obbligatoria |
| Hardcodare gli esempi dell'utente | Software rigido, non adattabile | Test anti-overfit su ogni requisito |
| Specificare framework nel prompt | Depotenzia il modello | Livello 3 = libertà |
| Ignorare i vincoli di ecosistema | Prodotto incompatibile | Livello 2 prima di progettare |
| Rendere TUTTO configurabile | Overengineering | Solo dove il test anti-overfit dice sì |
| Chiedere "vuoi che proceda?" | Spreca contesto e tempo | Procedi e logga |
| Skip dell'intervista | Manca il dominio | Max 2-3 round, poi procedi |

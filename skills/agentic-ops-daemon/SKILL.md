---
name: agentic-ops-daemon
description: "Protocollo portabile per progettare e implementare daemon/scheduler operativi che risvegliano periodicamente una CLI di progetto o un coding agent, eseguono check idempotenti, aggiornano dati, producono memo/report e tornano inattivi. Use when the user wants background/cron/Windows Task Scheduler automation, agentic CLI tasks, ops runbooks, unattended checks, data refresh, monitoring, audit trails, or a safe autonomy model for Claude/Codex-style agents."
---

# /agentic-ops-daemon - Daemon operativi agentici

Usa questa skill quando l'utente vuole aggiungere a un progetto un
**daemon/scheduler** che si sveglia a intervalli, apre una CLI, esegue
controlli o task agentici, scrive artefatti di avanzamento e torna inattivo.

L'obiettivo non e' creare un agente libero permanente. L'obiettivo e'
costruire un **operatore disciplinato**: runbook espliciti, permessi
graduati, lock, audit trail, dry-run, output versionabili.

---

## Principio centrale

Separare sempre:

| Superficie | Ruolo |
|---|---|
| UI / maschere | Funzioni deterministiche, input validati, risultati riproducibili |
| CLI | Automazioni, batch, check, refresh, report |
| Agentic CLI | Intervista, deep research, proposte, memo, diagnosi multi-step |
| Daemon/scheduler | Avvio periodico di profili ops non interattivi |

Il daemon puo' eseguire controlli e generare proposte. Non deve prendere
decisioni vincolanti senza un gate esplicito.

---

## Livelli di autonomia

Prima di scrivere codice, classifica ogni task:

| Livello | Consentito senza approvazione? | Esempi |
|---|---:|---|
| L0 read-only | Si | health check, cache status, drift report, API ping |
| L1 data refresh idempotente | Si, se configurato | prezzi, metadata, snapshot esterni, indici locali |
| L2 analisi/report | Si | VaR/CVaR, backtest batch, memo, report PDF/HTML |
| L3 proposta agentica | Si, ma output solo proposta | product shortlist, rebalance memo, policy draft |
| L4 modifica controllata | No, richiede approval | cambiare policy/pesi/config persistenti |
| L5 azione esterna rischiosa | Mai in daemon | trade, pagamenti, force push, delete dati |

Regola: se non sai classificare un'azione, trattala come L4.

---

## Fase 0 - Discovery

Leggi la struttura del progetto:

1. Manifest del progetto: `README.md`, `CLAUDE.md`, `PROJECT_SPEC.md`,
   `docs/ARCHITECTURE.md`, `pyproject.toml`/equivalente.
2. CLI esistente: entrypoint, comandi, parser, script batch.
3. Persistenza: DB, cache, cartelle dati, file generati.
4. Scheduler target: Windows Task Scheduler, cron, systemd timer, GitHub
   Actions, altro.
5. Documenti ops esistenti: `docs/ops/`, `RUNBOOK.md`, `STATE.md`,
   `TASK_QUEUE.md`, `decisions.log`.

Se il progetto non ha una CLI stabile, prima proponi di crearla. Un daemon
che chiama funzioni interne direttamente e' fragile; un daemon che chiama
comandi CLI e' auditabile.

---

## Fase 1 - Intervista minima

Fai domande brevi. Non superare 8 domande.

1. Quali profili servono? Esempi: `hourly`, `nightly`, `weekly-research`.
2. Quali task sono ammessi unattended? Solo check, refresh dati, report,
   ricerca, proposte?
3. Dove deve scrivere output e log?
4. Quali azioni sono vietate sempre?
5. Quali provider esterni servono? Esempi: Google Vertex/Gemini, OpenAI,
   broker read-only, email.
6. Quale scheduler usera' il progetto?
7. Come notificare risultati o errori? File outbox, email, webhook,
   nessuna notifica.
8. Serve un coding agent esterno (`claude`, `codex`, altro) o basta la CLI
   applicativa?

---

## Fase 2 - Contratto operativo

Prima dell'implementazione, scrivi o aggiorna `docs/ops/RUNBOOK.md` con:

- profili e frequenza;
- task ammessi per profilo;
- livelli di autonomia;
- comandi CLI invocati;
- output prodotti;
- segreti richiesti e loro sede;
- lock/concorrenza;
- recovery dopo crash;
- cosa il daemon non deve mai fare.

Usa anche:

```text
docs/ops/STATE.md       stato corrente osservabile
docs/ops/TASK_QUEUE.md  richieste pending per agent/coding agent
docs/ops/LAST_RUN.md    ultimo run, durata, esito, errori
docs/ops/OUTBOX.md      proposte, memo, cose da approvare
docs/ops/AUDIT.md       log append-only sintetico delle azioni
```

Non usare questi file come database primario: sono journal umani, non storage
transazionale.

---

## Fase 3 - Architettura standard

Adatta i nomi al linguaggio del progetto, ma mantieni questo shape:

```text
src/<package>/ops/
  __init__.py
  runner.py      # orchestration profili
  checks.py      # read-only health checks
  tasks.py       # registry task idempotenti
  locks.py       # file/db lock anti-overlap
  audit.py       # append audit + last-run writer
  agents.py      # opzionale: bridge verso coding agent / AI provider

scripts/
  ops-run.ps1    # Windows Task Scheduler
  ops-run.sh     # cron/systemd
```

Comandi CLI raccomandati:

```bash
<project-cli> ops check
<project-cli> ops run --profile nightly --dry-run
<project-cli> ops run --profile nightly
<project-cli> ops status
<project-cli> agent run --task docs/ops/TASK_QUEUE.md --dry-run
```

Ogni comando deve essere:

- non interattivo;
- idempotente o dichiaratamente read-only;
- loggato;
- testabile localmente;
- capace di fallire loud con exit code non-zero.

---

## Fase 4 - Coding agent wake pattern

Se il daemon deve risvegliare un coding agent:

1. Genera un prompt/task file esplicito in `docs/ops/TASK_QUEUE.md`.
2. Avvia il coding agent in modalita' non interattiva, se disponibile.
3. Limita il task a read-only, report o proposta, salvo approval esterna.
4. Scrivi ogni output in `docs/ops/OUTBOX.md` o `reports/ops/<timestamp>/`.
5. Non lasciare sessioni appese: timeout hard e lock cleanup.

Esempio di prompt per il task file:

```markdown
# Ops Task - nightly-monitor

Scope: read-only + proposal only.
Allowed commands:
- <project-cli> ops check
- <project-cli> ops refresh-data --dry-run
- <project-cli> ops monitor --write-report

Forbidden:
- editare codice
- modificare policy/pesi/strategie
- fare push
- cancellare dati

Output:
- aggiorna docs/ops/LAST_RUN.md
- appendi memo in docs/ops/OUTBOX.md
```

Se l'agente deve modificare codice, apri una change request separata.

---

## Fase 5 - Segreti e provider AI

Non salvare mai API key in repo. Usa, in ordine di preferenza:

1. application default credentials / IAM del cloud provider;
2. environment variables;
3. secret manager del provider;
4. file locale `.env` ignorato da git.

Prevedi config non segreta, per esempio:

```yaml
ai:
  provider: google_vertex
  project_id: my-project
  location: europe-west4
  default_model: gemini-2.5-pro
  grounding: google_search
  deep_research_enabled: true
```

Regole:

- non loggare prompt contenenti segreti;
- non loggare response raw se contiene dati sensibili;
- distinguere `research` da `decision`;
- richiedere citazioni/fonti per memo di ricerca;
- salvare sempre modello, timestamp e input hash nel report.

---

## Fase 6 - Scheduler

### Windows Task Scheduler

Genera uno script `scripts/ops-run.ps1` che:

- imposta working directory;
- attiva venv se esiste;
- esporta env vars non segrete;
- chiama `<project-cli> ops run --profile <profile>`;
- propaga exit code.

### cron/systemd

Genera `scripts/ops-run.sh` con gli stessi principi.

Non installare scheduler automaticamente se l'utente non lo chiede. Fornisci
il comando da eseguire o una procedura chiara in `RUNBOOK.md`.

---

## Fase 7 - Validazione

Minimo indispensabile:

```bash
<project-cli> ops check
<project-cli> ops run --profile nightly --dry-run
pytest tests/ops -q
```

Verifica anche:

- lock impedisce due run simultanei;
- crash parziale aggiorna `LAST_RUN.md` con errore;
- dry-run non scrive dati di dominio;
- nessun segreto finisce in log;
- output agentico resta in `OUTBOX.md` come proposta;
- scheduler script funziona dal path assoluto.

---

## Anti-pattern

- Daemon che modifica codice e fa commit/push da solo.
- Daemon che cambia policy, pesi o trade reali senza approval.
- Scheduler che chiama funzioni interne invece della CLI pubblica.
- Log senza timestamp, profilo, exit code e durata.
- API key in repo o in file versionati.
- Task agentico senza scope, allowed commands e forbidden actions.
- "Retry infinito": sempre max retry + backoff + fail loud.
- Parallel run senza lock.

---

## Output finale atteso

Quando chiudi il lavoro, riporta:

- profili creati;
- comandi CLI aggiunti;
- scheduler script creati;
- documenti `docs/ops/*` aggiornati;
- livelli di autonomia applicati;
- test eseguiti;
- cosa resta manuale o richiede approval.

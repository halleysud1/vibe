---
name: methodology
description: "I principi del vibecoding per spec-driven development con Claude Code: filosofia dei tre livelli (business / ecosistema / tecnico), regola anti-overfit, gestione del contesto. Attiva all'inizio di un progetto o quando devi prendere una decisione di livello 1/2/3."
---

# methodology — vibecoding SDD

## Cos'è il vibecoding (riformulazione v3.0)

Il vibecoding è uno **stile di spec-driven development** in cui l'utente fornisce
visione e contesto di dominio, Claude prende le decisioni tecniche e produce gli
artefatti. La chiave è sapere **dove servono specifiche ricche** e **dove serve libertà**.

In v3.0 il vibecoding non è più un "team multi-agente autonomo": è un **toolkit di skill**
che codifica il metodo. Gli agenti dedicati (architect, reviewer, ecc.) sono stati rimossi
in favore dei **subagent nativi** di Claude Code e dei comandi `/review`, `/security-review`.

---

## La filosofia dei tre livelli

Ogni informazione di un progetto appartiene a uno di tre livelli. Il trattamento è
radicalmente diverso per ciascuno.

### Livello 1 — Dominio di Business: CHIEDI ALL'UTENTE, SPECIFICA RICCO

L'utente è l'esperto. Non puoi inventare. Chiedi con domande mirate.

**Cosa appartiene al Livello 1:**
- Obiettivi del progetto e problemi da risolvere
- Chi sono gli utenti, come lavorano, cosa sanno fare
- Flussi di lavoro reali (il LAVORO, non le schermate)
- Requisiti funzionali (COSA, non COME)
- Regole di business e casi particolari

**Sede naturale**: `PROJECT_SPEC.md`.

### Livello 2 — Vincoli di Ecosistema: CHIEDI ALL'UTENTE, SPECIFICA PRECISO

Fatti non negoziabili del mondo reale. Se non li chiedi, fai scelte brillanti
ma incompatibili.

**Cosa appartiene al Livello 2:**
- Infrastruttura server, OS, database, rete
- Sistemi e API con cui integrarsi
- Convenzioni di naming, pattern dei progetti esistenti
- Normative (GDPR, AGID, CAD)
- Limitazioni tecniche (browser, connettività, hardware)
- Stack obbligato per ragioni di ecosistema (non per preferenza)

**Sede naturale**: `CLAUDE.md` (sezione "Vincoli NON NEGOZIABILI").

### Livello 3 — Implementazione Tecnica: DECIDI TU, LASCIA LIBERO

Tu sei l'esperto. Meno l'utente specifica qui, meglio lavori.

**Cosa appartiene al Livello 3:**
- Framework e librerie
- Architettura interna
- Struttura directory
- Pattern di design
- Strategie di test, caching, error handling
- Tutto ciò che l'utente non ha vincolato

**Sede naturale**: `docs/ARCHITECTURE.md` + ADR per le scelte irreversibili.

---

## La regola anti-overfit

### Il problema

Quando un utente descrive cosa vuole, dà **esempi concreti** che sembrano
**requisiti fissi**. Se li implementi letteralmente, il software sarà troppo
parametrizzato (pieno di logica specifica) e poco parametrizzabile (impossibile da adattare).

### La regola degli esempi

Quando l'utente dà un esempio concreto:

1. **Cattura l'INTENZIONE** → diventa il requisito funzionale
2. **Cattura i VALORI** → diventano i default configurabili
3. **Mai hardcodare** l'esempio come unica possibilità

### Il test dell'overfit

Per ogni requisito che stai per implementare, chiediti:

> "Se l'utente volesse cambiare questo valore/formula/comportamento domani,
> dovrebbe modificare il codice?"

- Se **sì** → stai overfittando. Rendi configurabile (YAML, JSON, DB).
- Se **no** → il requisito è correttamente astratto.

### Attenzione: non tutto deve essere configurabile

Il test anti-overfit non significa "rendi tutto configurabile". La regola è:
**configurabile dove l'utente ha dato un esempio, fisso dove ha dato un requisito.**

---

## Gestione del contesto

Il contesto è la risorsa più scarsa. Queste regole prevengono il context rot.

### 1. Riferisci per path:riga, mai ripetere codice
```
NO: "Ecco il codice aggiornato della funzione create_user: [80 righe]"
SI: "Aggiornato create_user in src/services/user.py:45-52 — aggiunto validazione email"
```

### 2. Comprimi gli errori
```
NO: [Stack trace di 50 righe]
SI: "TypeError in auth.py:23 — expected str, got None. Causa: missing null check"
```

### 3. Delega ricerche estese ai subagenti nativi
Per cercare un pattern in molti file, invoca un subagent (es. tipo Explore) — il
suo contesto è isolato.

### 4. Un task alla volta
Completa un task, committa, poi passa al successivo. Per lavoro parallelo, invoca
più subagent in parallelo (più Agent tool call nello stesso messaggio).

### 5. Output strutturato, mai narrativo
```
NO: "Ho analizzato il codice e ho notato diversi problemi..."
SI: "Problemi:
1. auth.py:23 — missing null check
2. db.py:45 — connection leak
3. api.py:12 — endpoint senza auth"
```

### 6. File come memoria, non contesto
Tutto ciò che deve persistere tra messaggi va in un file:
- `decisions.log` per audit trail timestampato
- `PLAN.md` per stato dei task
- **Auto-memory di Claude Code** per decisioni architetturali significative e
  preferenze utente (vedi sezione `auto memory` in CLAUDE.md di sistema)

### 7. Auto-memory per decisioni importanti
Per decisioni non ovvie, usa il sistema auto-memory:
- `project` memories per scelte di stack, vincoli scoperti, pattern adottati
- `feedback` memories per correzioni dell'utente sul processo
- Crea continuità tra sessioni senza dipendere dai soli file di progetto

---

## I 7 principi (consolidati v3.0)

### 1. Intervista prima, costruisci dopo
Non iniziare a costruire senza aver capito il dominio (L1) e i vincoli (L2). Per
nuovi progetti, lancia `skill-bootstrap` o `/vibecoding:init`.

### 2. Autonomia tecnica, non di dominio
Sei autonomo sulle scelte tecniche (L3). Non sei autonomo sul business (L1) e sui
vincoli (L2): chiedi.

### 3. Intenzioni, non esempi
Cattura l'intenzione dietro ogni esempio dell'utente. Implementa come sistema
configurabile, con l'esempio come default.

### 4. Spec wins
Se a implementazione emerge conflitto tra spec e codice, **la spec vince**. Aggiorna
la spec deliberatamente, non zitto. Per change non banali → `/change-request`.

### 5. No parallel flows
Quando aggiungi `new_feature` non lasciare in vita `old_feature` senza motivo
documentato. Migra, non duplicare. (Vedi anti-pattern A1 di `/change-request`.)

### 6. Vincoli prima, libertà dopo
Leggi sempre i vincoli L2 (CLAUDE.md) prima di scelte architetturali.

### 7. Semplicità
La soluzione più semplice che soddisfa i requisiti **e** rispetta i vincoli è
la migliore.

---

## Fasi di sviluppo (vibecoding SDD v3.0)

### Fase 0: Bootstrap del progetto

- Progetto vergine → lancia `skill-bootstrap` o `/vibecoding:init`
- Output: `PROJECT_SPEC.md`, `CLAUDE.md`, `.claude/skills/<...>/SKILL.md`

### Fase 1: Architettura

Prendi una decisione architetturale autonoma per il L3, applicando i vincoli L2.
Per decisioni irreversibili → ADR in `docs/decisions/`.

Per decisioni complesse o cross-layer → invoca un **subagent nativo** (es. Plan)
che produce un implementation plan approvabile.

### Fase 2: Implementazione

Per ogni task in `PLAN.md`:
1. Promuovi a 🔄
2. Implementa rispettando i vincoli L2
3. Applica anti-overfit su ogni logica di business
4. Test (inclusi test di configurabilità)
5. Se passa → commit, promuovi a ✅, prossimo task

### Fase 3: Review e sicurezza

Usa i comandi nativi:
- **`/review`** — code review della branch corrente
- **`/security-review`** — security audit dei pending change

Per progetti grandi: lancia entrambi in parallelo (più Agent call in un messaggio).

### Fase 4: Chiusura

Per change non banali → **Fase 5 di `/change-request`** (close the loop):
- Test verdi, lint pulito
- Doc autoritative aggiornate
- Niente parallel flows residui
- `decisions.log` con entry breve se la change ha implicazioni

---

## Stack default (L3, quando l'utente non vincola)

| Layer | Default | Quando cambiare |
|-------|---------|-----------------|
| Backend | Python + FastAPI | Node se full-JS; .NET se vincolo ecosistema Windows |
| Database | SQLite (dev) / PostgreSQL (prod) | DuckDB se analytics; SQL Server/MySQL se vincolo |
| Auth | JWT + bcrypt | SPID/CIE se PA; OAuth2 se social |
| Frontend | React + Tailwind | Vue se richiesto; vanilla se semplice |
| Test | pytest / vitest | — |
| Linter | ruff / eslint / biome | — |
| Config | YAML/JSON | DB se serve UI di configurazione |

La tabella vale **solo** quando il L2 (CLAUDE.md) non impone vincoli.

---

## Anti-pattern

| Anti-pattern | Perché è dannoso | Cosa fare |
|---|---|---|
| Costruire senza intervistare | Assunzioni sbagliate | Fase 0: `skill-bootstrap` o `init` |
| Hardcodare gli esempi dell'utente | Software rigido | Test anti-overfit su ogni requisito |
| Specificare framework nel prompt | Depotenzia il modello | L3 = libertà |
| Ignorare i vincoli di ecosistema | Prodotto incompatibile | L2 prima di progettare |
| Rendere TUTTO configurabile | Overengineering | Solo dove anti-overfit dice sì |
| Skip dell'intervista | Manca il dominio | Max 2-3 round, poi procedi |
| Ripetere codice nel contesto | Context rot | Riferisci per path:riga |
| Aggiungere senza migrare | Parallel flows latenti | `/change-request` Fase 1: classifica obsoleto |

---

## Come si usa questa skill

`methodology` non si "esegue". È un riferimento concettuale. Claude la **ricorda**
come contesto quando deve:
- Decidere cosa va in CLAUDE.md vs PROJECT_SPEC vs SKILL → consulta i tre livelli
- Valutare se un esempio è da rendere configurabile → applica test anti-overfit
- Decidere se delegare ricerca a subagent → applica regole di gestione contesto
- Pianificare le fasi di una change non banale → applica le 4 fasi di sviluppo

Le altre skill (`change-request`, `agentify`, `skill-bootstrap`, `validation-strategies`)
**presuppongono** la metodologia. Se sei arrivato qui per imparare il vibecoding,
leggi questa skill **prima** delle altre.

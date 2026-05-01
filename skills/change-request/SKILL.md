---
name: change-request
description: "Protocollo portabile per change request non banali su qualsiasi progetto software. 5 fasi — Impact Analysis → Spec First → Migration Plan → Implementation → Close the Loop. Anti-bias 'additivo', enforcement no-parallel-flows, propagazione automatica della documentazione."
---

# /change-request — Protocollo per cambiamenti significativi

Quando l'utente richiede una feature/refactor/estensione che tocca più di un file o cambia la visione del progetto, segui questo protocollo. Serve a:

- Evitare il bias **additivo** (aggiungere invece di migrare → doppi flussi)
- Garantire che la **documentazione resti coerente** con il codice
- Rendere **esplicite** le implicazioni di ogni cambiamento prima dell'implementazione
- Chiudere il loop (Fase 5) così la prossima sessione trova il progetto pulito

La skill è **portabile** — non dipende da un progetto specifico. Funziona in qualsiasi repo in cui tu sia invocato, adattandosi alla sua struttura di docs.

---

## Quando usare questo protocollo

**Usalo quando** la change request è:

- Una **feature nuova** che tocca ≥ 2 moduli/layer
- Un **refactor** che sposta ownership tra componenti
- Un **cambio di visione** (mental model, boundary, semantica di un'entità)
- Una **deprecazione** o sostituzione di un flusso/API esistente
- Una **estensione** che potrebbe duplicare qualcosa già presente

**Non usarlo** (bypass accettabile) quando:

- È un **bug fix** isolato
- È un **piccolo aggiustamento** in un singolo file già ben definito
- È una **decisione di stile/naming** senza impatto architetturale
- L'utente ha esplicitamente chiesto "quick fix senza cerimonie"

**In caso di dubbio, classifica la CR** (vedi sotto) e chiedi conferma all'utente.

---

## Fase 0 — Discovery (una tantum per progetto)

Prima della Fase 1, capisci la struttura del progetto corrente. Esegui questi step:

### 0.1. Cerca il manifesto

```bash
# Trova la mappa di navigazione della docs
ls docs/README.md CLAUDE.md PROJECT.md 2>/dev/null
```

Se **`docs/README.md`** esiste → leggilo: contiene la mappa autoritativa di cosa sta dove. Usa quello per orientarti.

Se **`CLAUDE.md`** esiste → contiene istruzioni operative specifiche del progetto. Leggi sempre.

### 0.2. Inventario rapido

```bash
ls -la                              # root del progetto
find docs -type f -name "*.md" 2>/dev/null | head -30
ls docs/decisions 2>/dev/null       # ADR esistenti
test -f decisions.log && echo "has decisions.log"
ls .claude/skills 2>/dev/null       # skill disponibili
```

Identifica:

- **Source of truth del dominio**: `PROJECT_SPEC.md` / `SPEC.md` / `REQUIREMENTS.md` / `README.md` (in quest'ordine di priorità)
- **Source of truth architetturale**: `docs/ARCHITECTURE.md` / `ARCHITECTURE.md` / equivalente
- **Decisioni storiche**: `docs/decisions/` (ADR) + eventuale `decisions.log`
- **Stato corrente**: `docs/vibecoding/STATE_SNAPSHOT.md` / `docs/STATE.md` / `STATUS.md` / equivalente
- **Visione**: `docs/vision/` / `VISION.md` / equivalente
- **Task tracker**: `PLAN.md` / `ROADMAP.md` / issue tracker esterno

### 0.3. Se la struttura manca

Se il progetto **non ha** un `docs/README.md` (mappa di navigazione), interrompi il protocollo e proponi all'utente di crearlo **prima**. Motivazione: senza mappa, la Fase 1 (Impact Analysis) non ha discoverability. Usa il template in fondo a questa skill come punto di partenza.

---

## Classificazione CR

Prima di procedere, classifica la change request come **small** o **strategic**.

| Criterio | Small CR | Strategic CR |
|---|---|---|
| N. file toccati (stima) | ≤ 3 | ≥ 4 oppure cross-layer |
| Entità di dominio nuove/modificate | 0 | ≥ 1 |
| Cambia signature pubblica di API? | no | sì |
| Rende obsoleto codice esistente? | no | sì |
| Richiede aggiornamento doc autoritativa? | no | sì |
| Introduce nuova dipendenza/libreria? | no | sì |

**Small CR** → puoi saltare Fase 2/3 e procedere direttamente a Fase 4 (con Fase 5 sempre obbligatoria).

**Strategic CR** → protocollo completo 1 → 5.

**Proponi la classificazione all'utente e chiedi conferma.** In caso di disaccordo, promuovi sempre a strategic (prudenza paga).

---

## Fase 1 — Impact Analysis

**Obiettivo**: capire le implicazioni della CR prima di scrivere anche una riga di codice.

### Letto obbligato (in ordine)

1. Il **manifesto** (`docs/README.md` se esiste) — per sapere cosa esiste.
2. Il **source of truth del dominio** (`PROJECT_SPEC.md` o equivalente) — specialmente le sezioni rilevanti alla CR.
3. Il documento di **visione** (`docs/vision/*.md`) — per capire i principi organizzatori che NON vanno violati.
4. Il documento **architetturale** (`docs/ARCHITECTURE.md`) — struttura attuale, layer, schema dati.
5. Gli **ADR pertinenti** (`docs/decisions/ADR-*.md`) — cercare per keyword del dominio toccato.
6. Lo **snapshot dello stato** (se esiste) — per non partire da assunzioni stale.

### Produci un Impact Report (10-15 righe, mostrato all'utente)

```markdown
## Impact Report — [titolo CR]

**Cosa cambia nella visione**: [1-2 frasi]

**Cosa diventa obsoleto / viene rimpiazzato**:
- [file/modulo/feature] → sostituito da [nuovo]
- [altro] → ...

**Cosa va migrato (non aggiunto)**:
- [componente X] → sposta ownership da A a B

**Cosa è aggiunta pura (nessun predecessore)**:
- [componente Y]

**Rischi / ambiguità da chiarire**:
- [domanda aperta]

**Classificazione**: Strategic CR
```

L'utente deve **approvare** l'Impact Report prima di procedere. Se l'utente non si riconosce nella tua analisi, sei partito su un presupposto sbagliato — chiarisci prima di continuare.

### Red flag: bias "additivo"

Se stai per scrivere "**aggiungiamo X**" e `X` concettualmente sostituisce `Y`, **la frase giusta è "migriamo da Y a X e cancelliamo Y"**. Questo è il principio `no_parallel_flows`. Se non sei sicuro che Y diventi obsoleto, chiedi all'utente esplicitamente: *"La feature attuale Y resta valida o viene sostituita da X?"*

---

## Fase 2 — Spec First (solo strategic CR)

**Obiettivo**: aggiornare la documentazione autoritativa **prima** di scrivere codice, così la spec è la vera fonte di verità e il codice la segue.

### Cosa aggiornare

Scegli il/i doc autoritativi identificati in Fase 0:

| Se la CR cambia... | Aggiorna... |
|---|---|
| Requisiti funzionali del prodotto | `PROJECT_SPEC.md` — nuovo RF-xxx |
| Visione/principio organizzatore | `docs/vision/*.md` (o crea nuovo doc visione) |
| Decisione architetturale irreversibile | **Nuovo ADR** in `docs/decisions/` |
| Schema dati / interfacce / boundary | `docs/ARCHITECTURE.md` |
| Matematica/algoritmi didattici | `docs/methodology/<modulo>.md` (se esiste) |

### Presenta il diff all'utente

Mostra il diff dei file di spec **prima** di procedere. Attendi approvazione esplicita.

Se l'utente cambia idea in questa fase, è esattamente **quando serve farlo** — i costi sono minimi. Rifai la Fase 2 senza frustrazione.

### Principio: spec wins

Se a Fase 3/4 emerge un conflitto tra spec aggiornata e codice, **la spec vince sempre**. Torna a Fase 2, non adattare silenziosamente la spec per giustificare il codice che hai scritto.

---

## Fase 3 — Migration Plan (solo strategic CR)

**Obiettivo**: rendere esplicite le operazioni concrete che seguiranno. Niente sorprese in Fase 4.

### Template Migration Plan

```markdown
## Migration Plan — [titolo CR]

### File NUOVI (aggiunta pura)
- `path/to/new_module.py` — [scopo in 1 riga]
- `tests/to/test_new_module.py`
- ...

### File MIGRATI (sposto ownership / semantica)
- `path/existing.py` — [come cambia / cosa si sposta dove]
- ...

### File RIMOSSI (obsoleti, cancellati nella stessa change)
- `path/deprecated.py` — sostituito da `path/to/new_module.py`
- ...

### Test da aggiornare
- `tests/path/test_X.py` — [quali assertion cambiano]

### Documentazione da aggiornare (Fase 5)
- `docs/ARCHITECTURE.md` — aggiornare sezione "X"
- `docs/methodology/<modulo>.md` — aggiungere formula Y
- `STATE_SNAPSHOT.md` — refresh test count, schema version, ecc.

### Entry in decisions.log
- Proposta di entry (timestamp + categoria + sintesi)
```

### Regola ferrea: niente TODO-differiti

Se una riga del piano dice "aggiungere X", non ci devono essere `// TODO: rimuovere vecchio in futuro` o `# deprecated, remove later`. Una migrazione **finisce** nella stessa change. Se l'utente non è d'accordo su una rimozione, torna a Fase 1 per chiarire.

### Utente approva il piano

Mostra il piano e aspetta ok. Dopo l'ok, Fase 4 è **esecuzione meccanica del piano**. Se in Fase 4 emerge un caso non previsto, **torna a Fase 2 o 3**, non improvvisare.

---

## Fase 4 — Implementation

**Obiettivo**: eseguire il Migration Plan in modo disciplinato.

### Ordine suggerito

1. **Tests first** (se il progetto è TDD-compatibile): scrivi i test del nuovo comportamento atteso.
2. **Aggiungi i file nuovi**.
3. **Migra i file esistenti** (un file per volta, test passanti dopo ciascuno quando possibile).
4. **Rimuovi i file obsoleti** — solo DOPO che i consumer sono migrati e i test passano.
5. **Aggiorna i test esistenti** che dipendevano dal vecchio comportamento.
6. **Check finale**: tutti i test passano, linter pulito.

### Comunica progressi brevi

Durante Fase 4, dai aggiornamenti sintetici all'utente (1 riga per milestone del piano). Non narrare ogni edit — il piano è già approvato.

### Se emerge un problema non previsto

Fermati. Non hackerare. Opzioni:

- Se è un dettaglio implementativo: decidi tu, documenta nel commit / `decisions.log`.
- Se cambia il piano: torna a Fase 3, mostra l'aggiornamento, ottieni nuova approvazione.
- Se cambia la spec: torna a Fase 2.

---

## Fase 5 — Close the Loop (SEMPRE obbligatoria)

**Obiettivo**: lasciare il progetto in stato coerente così la prossima sessione non trova debito tecnico di documentazione.

Questa fase si esegue **anche per small CR**, perché anche un piccolo cambiamento lascia tracce in test/snapshot.

### Checklist

Per ciascun punto, **esegui o spiega perché non è applicabile**:

- [ ] **Test** passano (`pytest -q` o equivalente)
- [ ] **Lint** pulito (`ruff check` / `eslint` / equivalente)
- [ ] **Snapshot/stato** aggiornato (test count, versione schema, contatori file se tracciati)
- [ ] **Architettura**: se hai toccato struttura/schema/boundary → `docs/ARCHITECTURE.md` aggiornato
- [ ] **Methodology/docs**: se hai aggiunto algoritmi o metriche → doc relativa aggiornata
- [ ] **Spec**: se hai aggiunto requisiti → RF-xxx aggiunto
- [ ] **ADR**: se hai preso decisione architetturale irreversibile → ADR scritto
- [ ] **decisions.log**: entry con timestamp + categoria + sintesi (rationale + file toccati)
- [ ] **Memory** (se usi auto-memory): salva feedback rilevante / pattern emersi
- [ ] **Rimossi file**: niente `.deprecated` / `.old` / commented-out code
- [ ] **Niente parallel flows rimasti live** (ricerca manuale o grep su nomi vecchi)
- [ ] **README del progetto**: se la CR è user-facing, aggiornato

### Anti-sabotage: no scorciatoie

Se sei tentato di "promettere" di aggiornare i doc dopo, sappi che:

1. **Non lo farai** — la prossima sessione hai perso il contesto.
2. **L'utente non lo farà** — non è suo il debito.
3. Il progetto diverge pezzo dopo pezzo.

La Fase 5 è **la** fase che impedisce il fenomeno descritto dall'utente come *"progetto sfilacciato, documentazione stale, funzioni duplicate"*. Non saltarla mai.

---

## Anti-pattern da evitare

### A1. "Agganciare" invece di migrare

Se aggiungi `new_feature.py` accanto a `old_feature.py` e non sai chi chiama ancora old_feature → è parallelo flow latente. Fai il grep dei consumer prima di decidere.

### A2. Spec non scritta "per velocità"

"Prima scrivo codice, poi aggiorno docs" → in pratica la seconda parte non succede mai. Spec first = spec scritta.

### A3. decisions.log come "cimitero di decisioni"

`decisions.log` è un journal. Le decisioni importanti vanno promosse a ADR/SPEC/ARCHITECTURE. Lasciare una decisione architetturale solo nel journal = debito tecnico di documentazione.

### A4. Deprecation silenziosa

`// deprecated, use Y instead` + lasciare il codice attivo = nulla è stato deprecato davvero. Rimuovi o mantieni — niente limbo.

### A5. "Lascio qui per backward compat"

Solo se backward compat è **un requisito esplicito** (API pubblica versionata, consumer esterni). Per codice interno, backward compat non è gratuita — è debito.

### A6. Protocollo "sussurrato"

Non eseguire il protocollo in silenzio. Mostra esplicitamente all'utente: *"Fase 1: ho letto X, Y, Z. Impact Report: ..."*. Se esegui in silenzio, non c'è checkpoint di allineamento.

---

## Esempi di invocazione

### Esempio 1: Strategic CR

> Utente: *"Aggiungiamo il concetto di 'progetto' come container dei task, così possiamo raggrupparli"*

Tu: *"Questo è una Strategic CR (nuova entità di dominio). Eseguo Fase 1 — Impact Analysis. Sto leggendo `docs/README.md`, `PROJECT_SPEC.md`, `docs/ARCHITECTURE.md`, ADR rilevanti..."*

### Esempio 2: Small CR

> Utente: *"Fixa il bug in `parse_date` che fallisce su date 29 Feb anno non-bisestile"*

Tu: *"Questo è una Small CR (1 file, no cambio API, no nuova entità). Bypass Fase 2/3. Eseguo Fase 4 + Fase 5 (checklist ridotta). Procedo?"*

### Esempio 3: Ambigua

> Utente: *"Supporta anche file YAML oltre a JSON"*

Tu: *"Ambigua. Tocca: (a) parser — 1 file, semplice. (b) validator — dipende se lo schema differisce. (c) docs → manuale aggiornato. Classifica: Strategic se (b) richiede nuovo schema, altrimenti Small. Mi confermi che lo schema YAML è lo stesso del JSON?"*

---

## Template — `docs/README.md` minimale (per progetti senza struttura)

Se la Fase 0 scopre che il progetto non ha mappa docs, proponi questo punto di partenza:

```markdown
# docs/ — Mappa di navigazione

## Ordine di lettura

1. `PROJECT_SPEC.md` (root) — requisiti funzionali
2. `docs/ARCHITECTURE.md` — layer, schema, interfacce
3. `docs/decisions/README.md` → ADR pertinenti
4. `docs/STATE.md` — stato corrente

## Struttura

| Cartella | Scope | Autoritativo? |
|---|---|---|
| `docs/decisions/` | ADR irreversibili | Sì |
| `docs/methodology/` | Matematica/algoritmi | Sì |
| `docs/archive/` | Documenti storici | No |

## Policy

- Nuove decisioni architetturali → ADR in `docs/decisions/`
- `decisions.log` (root) = journal append-only; promuovere entry importanti a ADR
- Fase 5 del protocollo `/change-request` obbligatoria dopo ogni CR
```

Partendo da questo l'utente può customizzare.

---

## Checklist di auto-verifica della skill

Quando esegui questa skill, rispondi mentalmente a queste domande prima di dichiarare "fatto":

1. Ho mostrato l'**Impact Report** all'utente e ho avuto approvazione?
2. Se Strategic CR, ho mostrato il **diff della spec aggiornata** prima di scrivere codice?
3. Ho mostrato il **Migration Plan esplicito** prima di Fase 4?
4. In Fase 5, ho spuntato **ogni voce** della checklist o motivato ogni NA?
5. Ho evitato ogni **parallel flow** (nessun file vecchio che sopravvive accanto al nuovo senza motivo documentato)?
6. Ho evitato ogni **`TODO: later`** o `deprecated` che lascia debito?

Se anche solo una risposta è "no" o "forse", fermati e ripara prima di chiudere.

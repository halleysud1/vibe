---
name: init
description: "Inizializza un progetto vibecoding SDD: distingue modulo software vs cartella di lavorazione, intervista l'utente, instrada le desiderata in CLAUDE.md / PROJECT_SPEC / SKILL, scaffolda la struttura. Delega la logica di routing alla skill `skill-bootstrap`."
---

# /vibecoding:init — Bootstrap progetto SDD

## Cosa devi fare

L'utente sta inizializzando un progetto vibecoding (v3.0 — SDD toolkit). Il tuo
lavoro è **capire cosa vuole prima di costruire**, e poi distribuire correttamente
le sue desiderata in tre sedi:

- `CLAUDE.md` — vincoli globali e istruzioni operative
- `PROJECT_SPEC.md` — visione, utenti, requisiti funzionali
- `.claude/skills/<nome>/SKILL.md` — regole operative riusabili

> **Nota architetturale**: la logica di routing è codificata nella skill
> [`skill-bootstrap`](../skills/skill-bootstrap/SKILL.md). Questo comando è
> l'**entry point** che la richiama; per dettagli sulla classificazione delle
> desiderata, leggi quella skill.

---

## Quando lanciarlo

- A inizio sessione su un progetto vergine (nessun `CLAUDE.md`, nessun `PROJECT_SPEC.md`)
- Quando l'utente vuole strutturare metodologicamente un progetto esistente
- Quando l'utente apre una nuova **cartella di lavorazione Claude** (es. workspace
  di analisi, automazione)

Se il progetto ha già queste 3 sedi popolate, **non rilanciare init**: usa
`/change-request` per evolvere o `skill-bootstrap` per aggiungere skill nuove.

---

## FASE 0 — Detect del contesto esistente

Prima di tutto, controlla cosa c'è già:

```bash
ls CLAUDE.md PROJECT_SPEC.md PLAN.md docs/README.md .claude/skills 2>/dev/null
```

| Stato rilevato | Cosa fare |
|---|---|
| Tutto vuoto | Procedi con FASE A (intervista completa) |
| Esiste `PROJECT_SPEC.md` ma niente altro | Leggilo, riusa il contenuto, salta solo le domande L1 |
| Esiste `CLAUDE.md` ma `PROJECT_SPEC.md` no | Riusa CLAUDE.md per L2, fai L1 e routing skill |
| Esistono entrambi e ha skill | **Non rifare init**: suggerisci `/change-request` |

> Se l'utente ha preparato un `PROJECT_SPEC.md` prima di lanciare init, è un
> segnale di volersi un flusso più rapido — riusa quel contenuto, fai solo le
> domande mancanti.

---

## FASE A — Tipo di lavorazione

**Domanda obbligata** (se non è già chiaro dal contesto):

> *"Stai sviluppando un **modulo software** (codice di prodotto, stack, test) oppure
> stai aprendo una **cartella di lavorazione Claude** (analisi, automazione,
> documentazione, output non-codice)?"*

### Conseguenze

| Tipo | Template scaffold | Esempi |
|---|---|---|
| **Modulo** | `templates/modulo/` (CLAUDE, PROJECT_SPEC, PLAN, docs/ARCHITECTURE) | App web, libreria, microservizio |
| **Cartella di lavorazione** | `templates/cartella/` (CLAUDE, PROJECT_SPEC, docs/README, docs/STATE_SNAPSHOT) | Workspace di analisi, integrazione tool, documentazione SDD |

Se ambiguo → **cartella di lavorazione** (più permissiva, l'utente aggiunge `src/` se serve).

---

## FASE B — Intervista (raccolta libera)

L'intervista NON è fire-and-forget. Devi fare domande in **blocchi tematici** e
adattarti al contesto già fornito.

### B1 — Dominio di business (Livello 1)

- Qual è il problema concreto che questo progetto deve risolvere?
- Chi userà l'output? Che competenze hanno? In che contesto?
- Come risolvono questo problema oggi?
- Quali sono le 3 cose che DEVE fare? Cosa è "nice to have"?

### B2 — Vincoli di ecosistema (Livello 2)

- Su quali server / piattaforma / OS gira?
- Database obbligato? API o sistemi da integrare?
- Convenzioni di naming / pattern dei progetti esistenti?
- Vincoli normativi (GDPR, AGID, accessibilità)?
- Stack tecnologico imposto da ragioni organizzative?

### B3 — Regole operative ricorrenti

> Questo blocco è **nuovo in v3.0**. Estrae le desiderata che diventeranno SKILL.

- Ci sono regole operative che vuoi che applichi **ogni volta** che lavoro su
  questo progetto? (Es: "ogni elemento core deve avere un'attività futura")
- Ci sono procedure sequenziali ricorrenti? (Es: "quando produci un report PM,
  segui sempre estrazione → analisi → scrittura")
- Ci sono **boundary hard** — cose che NON devo MAI fare? (Es: "mai modificare
  task in stato Done")
- Ci sono classificazioni / tassonomie del tuo dominio? (Es: contratti =
  Fornitura/Contratto/Informatizzazione)

### Regole di conduzione

1. **Massimo 2-3 round di domande**. Non trasformare l'intervista in interrogatorio.
2. **Adatta al contesto**: se l'utente ha già detto X nel prompt, non rifare la domanda.
3. **Mai chiedere scelte di Livello 3** (framework, struttura directory): lì decidi tu.
4. **Risposte "non so"**: per L1 insisti gentilmente, per L2 prendi nota "nessun vincolo".

---

## FASE C — Routing 3-vie (cuore di v3.0)

Classifica ogni informazione raccolta nelle 3 sedi corrette. Mostra all'utente la
**classificazione proposta** e attendi conferma.

### Tabella di routing

| Tipo informazione | Va in | Esempio |
|---|---|---|
| Visione, problema, obiettivi | `PROJECT_SPEC.md` | "Analizzare performance tecnici" |
| Profili utente, flussi di lavoro | `PROJECT_SPEC.md` | "Backoffice, no background tecnico" |
| Requisiti funzionali (RF-NN) | `PROJECT_SPEC.md` | "Export PDF di ogni report" |
| Stack obbligato, sistemi integrati | `CLAUDE.md` (vincoli L2) | "Odoo XML-RPC, NO Postgres" |
| Vincoli ambiente, OS, normative | `CLAUDE.md` | "GDPR su CF dipendenti" |
| Convenzioni naming, lingua, formati | `CLAUDE.md` | "Markdown italiano, codice inglese" |
| Comandi tipici di lavoro | `CLAUDE.md` | "`python scripts/analisi.py`" |
| **Regole operative ricorrenti** | `.claude/skills/<X>/SKILL.md` | "Ogni elemento core deve avere attività futura" |
| **Procedure sequenziali per dominio** | `.claude/skills/<X>/SKILL.md` | "Estrai → analizza → scrivi" |
| **Tassonomie / classificazioni** | `.claude/skills/<X>/SKILL.md` | Mapping tipi contratto |

### Test discriminante CLAUDE.md vs SKILL.md

- *"Si applica sempre, in ogni task del progetto?"* → CLAUDE.md
- *"Si applica solo quando lavoro su un certo dominio operativo?"* → SKILL.md (con
  description = quel dominio)

### Output Fase C — formato proposto

```markdown
## Classificazione delle desiderata

### Andranno in PROJECT_SPEC.md
- Visione: [...]
- Utenti: [...]
- RF-01, RF-02, ...

### Andranno in CLAUDE.md
- Stack: [...]
- Convenzioni: [...]
- Comandi: [...]

### Andranno come skill: `<nome-skill-1>`
description proposta: "[verbo] [oggetto] quando [trigger]."
- Regola: [...]
- Regola: [...]

### Andranno come skill: `<nome-skill-2>`
...

Confermi questa classificazione, o vuoi spostare qualcosa?
```

**Itera finché l'utente è d'accordo.** Non scrivere file senza approvazione.

---

## FASE D — Scrittura artefatti

### D1. Scaffold della struttura

Copia `templates/modulo/` (modulo) o `templates/cartella/` (cartella) nella root.

### D2. Popola CLAUDE.md

Apri il template e riempi le sezioni con il contenuto classificato come "CLAUDE.md".

### D3. Popola PROJECT_SPEC.md

Idem per le sezioni di L1 (visione, utenti, RF, glossario).

Applica il **test anti-overfit** sui requisiti: ogni esempio concreto dell'utente
diventa **default configurabile**, non hardcoded. Vedi skill `methodology` § Anti-overfit.

### D4. Scrivi le SKILL operative

Per ogni skill identificata in Fase C:

1. `mkdir -p .claude/skills/<nome>/`
2. Copia `templates/skill-stub/SKILL.md` come base
3. Frontmatter:
   - `name`: kebab-case, uguale al nome cartella
   - `description`: **una frase** azionabile — `"<verbo> <oggetto> quando <trigger>"`.
     È il campo più importante: Claude lo usa per decidere quando attivare la skill.
4. Body: sezioni standard (Quando usare / Regole operative / Esempi / Anti-pattern /
   Checklist). Riempi con le desiderata raccolte.

> **Riferimento**: la fase di writing è descritta in dettaglio nella skill
> `skill-bootstrap` § Fase D.

### D5. PLAN.md (solo modulo)

Se è un modulo, abbozza il `PLAN.md` con i task derivati dai RF di PROJECT_SPEC.
Stato `⬜` per tutti, l'utente promuove a `🔄`.

### D6. (opzionale) Strategia di validazione

Per moduli, aggiungi `docs/VALIDATION_STRATEGY.md` scegliendo dalla skill
`validation-strategies` la sezione corrispondente al tipo di app.

---

## FASE E — Verifica e consegna

Mostra all'utente:

1. **Sintesi degli artefatti generati** — lista file con path
2. **Conferma routing** — quali regole sono andate dove
3. **Open questions** se ci sono assunzioni non confermate

Aggiungi a `decisions.log` (se esiste o se vuoi crearlo):

```
2026-MM-DD / init / Progetto inizializzato con vibecoding v3.0.
Tipo: <modulo|cartella>. Skill scritte: <nome1>, <nome2>.
Vincoli L2 chiave: <riassunto>.
```

Salva una **project memory** (auto-memory) con: tipo progetto, stack/vincoli chiave,
skill attive. Crea continuità tra sessioni.

---

## Esempio di sessione (cartella di lavorazione)

> **Utente**: `/vibecoding:init`. Voglio aprire una cartella per analizzare le
> performance dei project manager Halley Sud. Dati da Odoo XML-RPC. Output:
> report markdown per il direttore commerciale. Ogni progetto va classificato
> per tipo (Fornitura/Contratto/Informatizzazione) prima dell'analisi.

**Tu**:

```
FASE A: cartella di lavorazione (output = report, no app).

Domande mancanti (FASE B):
- Il direttore commerciale è il solo lettore o ce ne sono altri?
- Vuoi un report per ogni PM o un report aggregato?
- C'è una cadenza? (settimanale / mensile / on-demand)

FASE C — Classificazione proposta:

PROJECT_SPEC.md:
- Visione: analizzare performance dei PM di Halley Sud
- Utenti: direttore commerciale (lettore non tecnico)
- RF-01: report markdown per ogni PM
- RF-02: confronto cross-PM
- Fonte dati: Odoo XML-RPC

CLAUDE.md:
- Stack: Odoo XML-RPC come fonte
- Convenzioni: report markdown italiano, codice inglese

Skill: `analisi-pm`
description: "Analizza i progetti dei project manager Halley Sud su Odoo,
classifica per tipo (Fornitura/Contratto/Informatizzazione) e produce
report markdown comparativi."
- Regola: classifica progetti prima di analizzare
- Regola: mappa tipi: Fornitura=purchase_order, Contratto=contract,
  Informatizzazione=agreement

Confermi? Manca qualcosa?
```

Dopo OK → FASE D scrive i 3 artefatti.

---

## Anti-pattern

### A1. Skip della Fase C
Se scrivi tutto in CLAUDE.md o tutto in PROJECT_SPEC, perdi il vantaggio delle
skill (progressive disclosure, attivazione contestuale).

### A2. Inventare regole non dette
Se l'utente non ha detto una regola, non aggiungerla "perché sembra utile". Le
skill devono riflettere le **sue** desiderata.

### A3. Skill troppo grosse
Se una skill ha 5+ regole eterogenee, splitala. Una skill = un dominio operativo coerente.

### A4. Description di skill generica
`description: "Helper per il progetto"` non si attiverà mai. Sempre verbo + oggetto + trigger.

### A5. Saltare la conferma utente in Fase C
La classificazione è il pezzo che l'utente vuole correggere. Non scrivere file
senza il suo OK.

---

## Checklist auto-verifica

Prima di chiudere init:

1. Ho chiesto FASE A (modulo vs cartella)?
2. Ho fatto un'intervista mirata e mostrato la classificazione di FASE C?
3. L'utente ha approvato il routing prima di scrivere file?
4. Ogni skill scritta ha description actionable e body con regole concrete?
5. CLAUDE.md non duplica regole già nelle skill?
6. PROJECT_SPEC ha applicato anti-overfit sugli esempi numerici?
7. Ho aggiornato `decisions.log` e/o auto-memory?

Se anche solo una risposta è "no", torna indietro.

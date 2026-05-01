---
name: skill-bootstrap
description: "Intervista metodologica di inizio progetto. Distingue modulo software vs cartella di lavorazione Claude, raccoglie le desiderata dell'utente, e le instrada nella sede giusta — CLAUDE.md, PROJECT_SPEC.md, oppure SKILL.md dedicate. Genera lo scaffold iniziale (templates) e scrive le skill operative del progetto. Invocabile a freddo o richiamata da `/vibecoding:init`."
---

# /skill-bootstrap — Intervista di routing per spec-driven development

Quando l'utente apre Claude Code in un progetto **vergine** (o vuole rifare la base
metodologica di un progetto esistente), questa skill conduce un'intervista che produce:

1. **CLAUDE.md** — istruzioni globali e vincoli di ecosistema
2. **PROJECT_SPEC.md** — visione, utenti, requisiti funzionali
3. **`.claude/skills/<nome>/SKILL.md`** — regole/desiderata operative riusabili come skill

La logica di routing è il valore della skill: dato un set di desiderata libere
dell'utente, decide *dove* va ciascuna informazione e la scrive nel posto giusto.

---

## Quando usare questa skill

**Usala quando:**

- Progetto vergine: nessun `CLAUDE.md`, nessun `PROJECT_SPEC.md`, nessuna `.claude/skills/`
- Progetto esistente in cui l'utente vuole strutturare metodologicamente (introdurre SDD)
- Sei chiamata da `/vibecoding:init` come fase di routing

**Non usarla quando:**

- L'utente vuole solo un *bug fix* — niente bootstrap necessario
- Il progetto ha già `CLAUDE.md` + `PROJECT_SPEC.md` + skill — usa `/change-request` invece
- L'utente vuole un agente standalone (no Claude Code) — usa `/agentify`

---

## Fase A — Tipo di lavorazione

La prima domanda discrimina lo scaffold e quali skill ha senso scrivere.

### Domanda

> *"Stai sviluppando un **modulo software** (codice di prodotto, stack, test) oppure
> stai aprendo una **cartella di lavorazione Claude** (analisi, automazione, documentazione,
> output non-codice)?"*

### Conseguenze sullo scaffold

| Tipo | Output principale | Templates da `templates/` | Esempi |
|---|---|---|---|
| **Modulo software** | Codice eseguibile | `templates/modulo/` → CLAUDE.md, PROJECT_SPEC.md, PLAN.md, src/, tests/, docs/ARCHITECTURE.md | App web, libreria Python, microservizio |
| **Cartella di lavorazione** | Documenti, analisi, automazioni | `templates/cartella/` → CLAUDE.md, PROJECT_SPEC.md, docs/README.md, docs/STATE_SNAPSHOT.md, scripts/, data/ | Analisi performance, documentazione SDD, integrazione tool esistente |

### Red flag

Se l'utente esita o dice "un po' tutti e due", probabilmente è una **cartella di
lavorazione** che produce anche qualche script. Vai con `cartella` — è più permissiva
e l'utente può sempre aggiungere `src/` dopo.

---

## Fase B — Raccolta libera delle desiderata

L'utente descrive il progetto a ruota libera. Tu **non interrompi** per classificare:
prendi tutto. Esempio di desiderata che possono uscire:

- "Voglio analizzare le performance dei tecnici per ruolo"  *(visione/obiettivo)*
- "Stack obbligato: pandas, numpy, DuckDB. NO Postgres."  *(vincolo ecosistema)*
- "Ogni elemento core aperto deve avere un'attività futura nel chatter"  *(regola operativa ricorrente)*
- "Gli utenti sono il mio backoffice, non hanno background tecnico"  *(profilo utente)*
- "Mai modificare i task quando sono in stato 'Done'"  *(regola operativa)*
- "Rispetta GDPR, dati sensibili: codice fiscale dei dipendenti"  *(vincolo normativo)*

### Domande di apertura (in ordine, ma adattabili)

1. *Qual è il problema concreto che questo progetto deve risolvere?*
2. *Chi userà l'output? Che competenze hanno? In che contesto?*
3. *Ci sono vincoli di ecosistema fissi? (stack, sistemi integrati, normative, OS)*
4. *Ci sono regole operative ricorrenti che devo applicare ogni volta?*
5. *Cosa NON deve mai succedere? (boundaries hard)*

Lascia che l'utente espanda. Se le risposte sono povere, pondi sotto-domande mirate.

---

## Fase C — Routing 3-vie

Ogni informazione raccolta in Fase B viene classificata **prima** di scrivere
qualsiasi file. Mostra all'utente la classificazione e chiedi conferma.

### Tabella di routing

| Tipo di informazione | Va in | Esempi |
|---|---|---|
| Visione, obiettivi, problema | `PROJECT_SPEC.md` | "Analizzare performance tecnici", "ridurre tempo di onboarding" |
| Profili utente, flussi di lavoro reali | `PROJECT_SPEC.md` | "Backoffice senza background tecnico", "tecnici esterni partner" |
| Requisiti funzionali (RF) | `PROJECT_SPEC.md` | "Ogni report deve avere export PDF", "Scheduling settimanale" |
| Vincoli ambiente, OS, infrastruttura | `CLAUDE.md` (sez. vincoli L2) | "Windows 11 dev, Linux prod", "rete intranet senza accesso esterno" |
| Stack obbligato, sistemi integrati | `CLAUDE.md` | "DuckDB, NO Postgres", "Odoo XML-RPC come fonte" |
| Normative, compliance | `CLAUDE.md` | "GDPR su CF dipendenti", "AGID per pagoPA" |
| Convenzioni codice, naming | `CLAUDE.md` | "Italiano nei commenti, inglese nei docstring" |
| Comandi standard, workflow tipici | `CLAUDE.md` | "Esecuzione: `python scripts/test_connection.py`" |
| **Regole operative ricorrenti che si applicano in più sessioni** | `.claude/skills/<nome>/SKILL.md` | "Ogni elemento core aperto deve avere attività futura nel chatter" |
| **Procedure sequenziali con fasi/checklist** | `.claude/skills/<nome>/SKILL.md` | "Quando crei un report tecnico segui: estrazione → analisi → scrittura" |
| **Decisioni tassonomiche del dominio** | `.claude/skills/<nome>/SKILL.md` | "Classificazione contratti: fornitura/contratto/informatizzazione" |

### Criterio decisionale tra CLAUDE.md e SKILL

La domanda discriminante: **"questa regola si applica solo a un certo tipo di task,
oppure è un vincolo globale del progetto?"**

- **Globale, sempre attivo** → `CLAUDE.md` (Claude la legge a ogni sessione)
- **Specifico a un dominio operativo** → `SKILL.md` (Claude la attiva quando il task
  matcha la `description` della skill)

Esempi:

| Regola | Va dove | Perché |
|---|---|---|
| "Stack pandas+DuckDB obbligato" | `CLAUDE.md` | Vale per qualunque codice scrivi |
| "Ogni task tecnico deve avere stima ore" | SKILL.md (`gestione-task`) | Si attiva solo quando lavori sui task |
| "Mai shortare titoli, mai leverage" | `CLAUDE.md` | Vincolo di dominio sempre valido |
| "Quando analizzi un PM, segui pattern: estrai → confronta → raccomanda" | SKILL.md (`analisi-pm`) | Procedura specifica, non sempre attiva |

### Mostra la classificazione all'utente

Output Fase C, formato proposto:

```markdown
## Classificazione delle desiderata raccolte

### Andranno in PROJECT_SPEC.md
- [riga 1: visione]
- [riga 2: utenti]
- [RF-01, RF-02, ...]

### Andranno in CLAUDE.md
- Stack: [...]
- Vincoli ecosistema: [...]
- Convenzioni: [...]

### Andranno come skill: `<nome-skill-1>`
- [regola 1]
- [regola 2]
descrizione skill: "[1 frase]"

### Andranno come skill: `<nome-skill-2>`
- ...

Confermi questa classificazione, o vuoi spostare qualcosa?
```

Itera finché l'utente è d'accordo. **Non scrivere file senza approvazione esplicita.**

---

## Fase D — Scrittura artefatti

Solo dopo OK su Fase C, procedi nell'ordine:

### D1. Scaffold struttura

Copia da `templates/modulo/` o `templates/cartella/` (a seconda di Fase A) la struttura
di base nella root del progetto target.

### D2. Popola CLAUDE.md

Apri `CLAUDE.md` (template) e riempi le sezioni con le info classificate "CLAUDE.md"
in Fase C. Sezioni standard:

- `## Contesto` (1-2 paragrafi sintesi)
- `## Vincoli NON NEGOZIABILI (L2 — Ecosistema)` (lista numerata)
- `## Convenzioni codice/naming`
- `## Comandi tipici`
- `## Skills attive in questo progetto` (link a `.claude/skills/`)

### D3. Popola PROJECT_SPEC.md

Apri il template e riempi:

- `# Visione`
- `# Utenti e profili`
- `# Flussi di lavoro reali`
- `# Requisiti funzionali` (RF-NN, numerati)
- `# Glossario di dominio` (se l'utente ha usato termini tecnici specifici)

### D4. Scrivi le SKILL operative (writer di SKILL.md)

Per ogni skill identificata in Fase C:

1. Crea cartella `.claude/skills/<nome-skill>/`
2. Copia `templates/skill-stub/SKILL.md` come base
3. Riempi il frontmatter:
   - `name`: il nome della cartella, kebab-case
   - `description`: **una frase** che descrive *cosa fa la skill* + *quando si attiva*. È il campo più importante perché Claude usa la description per decidere se invocare la skill. Buona description = "Genera/applica/verifica X quando Y." Non descrivere il file, descrivi l'azione e il trigger.
4. Scrivi il body in markdown, sezioni standard:
   - `## Quando usare questa skill`
   - `## Regole operative` (le desiderata raccolte, numerate o a checklist)
   - `## Esempi` (almeno 1, meglio 2)
   - `## Anti-pattern da evitare` (opzionale ma raccomandato)

### D5. Scrivi PLAN.md (solo se modulo)

Per i progetti modulo, abbozza un PLAN.md con i task iniziali derivati dai RF di
PROJECT_SPEC. Stato `⬜` per tutti, l'utente promuoverà manualmente a `🔄`.

### D6. Verifica finale

- Tutti i file generati si leggono come documenti coerenti?
- Le skill sono auto-contenute (non serve leggere CLAUDE.md per capirle)?
- CLAUDE.md non duplica info che dovrebbero stare nelle skill?

---

## Anti-pattern

### A1. Saltare la Fase C (routing) per fretta
Se scrivi tutto in `CLAUDE.md`, le skill non saranno mai create e perdi il vantaggio
del progressive disclosure. Se scrivi tutto in skill, `CLAUDE.md` diventa vuoto e
Claude non avrà i vincoli di base sempre attivi.

### A2. Skill troppo grosse / "tuttofare"
Se una skill ha >5 sezioni di regole eterogenee, probabilmente sono **due skill**.
Splittale: una skill = un dominio operativo coerente.

### A3. Description di skill generiche
`description: "Helper per il progetto"` è inutile — Claude non saprà mai quando attivarla.
Meglio: `"Calcola e applica i bonus mensili dei tecnici quando l'utente chiede analisi
di performance o stipendi del mese."` — verbo + oggetto + trigger.

### A4. Inventare regole non dette dall'utente
Se l'utente non ha menzionato una regola, non aggiungerla "perché sembra utile".
Le skill devono riflettere le **sue** desiderata, non le tue assunzioni.

### A5. Bypassare il template e scrivere a mano
I template esistono perché garantiscono frontmatter corretto e struttura coerente.
Editali, non riscriverli da zero.

---

## Esempio breve di sessione

> **Utente**: "Vorrei aprire una cartella per analizzare le performance dei project manager
> di Halley Sud. I dati arrivano da Odoo XML-RPC. Devo produrre report markdown leggibili
> dal direttore commerciale. Convenzione: nomi file in italiano, codice in inglese.
> Ogni progetto deve essere classificato per tipo (Fornitura, Contratto, Informatizzazione)
> prima dell'analisi."

**Tu (skill-bootstrap)**:

```
Fase A: cartella di lavorazione (output = report markdown, no app).

Fase C — Classificazione:

PROJECT_SPEC.md:
- Visione: analizzare performance dei PM di Halley Sud
- Utenti: direttore commerciale (lettore non tecnico)
- RF-01: produrre report markdown per ogni PM
- RF-02: confrontare PM tra loro

CLAUDE.md:
- Stack: Odoo XML-RPC come fonte dati
- Convenzioni: nomi file italiano, codice inglese, output markdown
- Comandi: vedi scripts/

Skill: `analisi-pm`
- description: "Analizza i progetti dei project manager Halley Sud su Odoo, classifica
  per tipo (Fornitura/Contratto/Informatizzazione) e produce report markdown comparativi."
- Regola: classifica progetti prima dell'analisi
- Regola: mappa tipi: Fornitura=purchase_order, Contratto=contract, Informatizzazione=agreement

Confermi? Ho dimenticato qualcosa?
```

Dopo OK → Fase D scrive i 3 file.

---

## Checklist auto-verifica

Prima di chiudere:

1. Ho fatto Fase A (modulo vs cartella) prima di scegliere il template?
2. Ho mostrato la classificazione di Fase C all'utente e ottenuto approvazione?
3. Ogni skill ha `description` actionable (verbo + trigger)?
4. CLAUDE.md non duplica regole che ho messo nelle skill?
5. Ho scritto solo le regole dette dall'utente, niente invenzioni?
6. La struttura segue il template (modulo o cartella) coerentemente?

Se anche solo una risposta è "no", torna indietro e correggi prima di chiudere.

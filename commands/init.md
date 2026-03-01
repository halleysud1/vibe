---
name: init
description: "Inizializza un nuovo progetto con il sistema Vibecoding 2.0. Intervista l'utente su dominio e vincoli, poi genera PROJECT_SPEC, PLAN, e struttura docs."
---

# /vibecoding:init — Bootstrap Progetto

## Cosa devi fare

Sei l'Orchestrator del sistema Vibecoding 2.0. L'utente sta inizializzando un nuovo progetto. Il tuo lavoro è **capire cosa vuole** prima di costruire qualsiasi cosa.

---

## FASE 0: Rileva PROJECT_SPEC.md esistente

**PRIMA DI TUTTO**, controlla se nella directory corrente esiste già un file `PROJECT_SPEC.md`.

### Se PROJECT_SPEC.md ESISTE:
1. **Leggilo integralmente** con il tool Read
2. **Analizza il contenuto** — verifica che contenga informazioni sufficienti su:
   - Obiettivo del progetto e problema da risolvere
   - Utenti target e flussi di lavoro
   - Requisiti funzionali (anche se non nel formato Vibecoding)
   - Eventuali vincoli tecnici o di ecosistema
3. **Applica la diagnosi anti-overfit** (FASE 2) sui requisiti trovati
4. **Riformatta se necessario** — se il file non è nel formato Vibecoding a 3 livelli, riscrivilo nel formato standard mantenendo TUTTE le informazioni originali. Non perdere nulla.
5. **SALTA la FASE 1** (intervista) — le spec sono già fornite dall'utente
6. **Procedi direttamente** alla FASE 3 (o FASE 4 se il PROJECT_SPEC è già completo)

### Se PROJECT_SPEC.md NON ESISTE:
Procedi normalmente con la FASE 1 (intervista interattiva).

> **Logica:** Se l'utente ha preparato un PROJECT_SPEC.md prima di lanciare `/vibecoding:init`, significa che vuole un flusso fire-and-forget. Rispetta le sue spec e parti subito.

---

## FASE 1: Intervista (INTERATTIVA)

> **Nota:** Questa fase viene SALTATA se un PROJECT_SPEC.md è già presente nella directory.

L'init NON è un comando fire-and-forget. Devi fare domande all'utente per raccogliere il contesto che non puoi inventare. Senza queste informazioni, qualsiasi cosa costruisci sarà sbagliata o troppo rigida.

### 1A — Domande di Dominio di Business (Livello 1)

Queste sono le domande più importanti. Le risposte dell'utente alimentano il Livello 1 del PROJECT_SPEC.

**Obiettivo e contesto:**
- Qual è il problema concreto che questo software deve risolvere?
- Chi lo usa? Che competenze hanno? In che contesto lavorano?
- Come risolvono questo problema OGGI (senza il software)?

**Flussi di lavoro:**
- Descrivi il flusso di lavoro tipico, dall'inizio alla fine
- Ci sono casi particolari o eccezioni importanti?
- Cosa succede quando qualcosa va storto nel processo?

**Risultati attesi:**
- Come fai a sapere se il software funziona? Qual è il "test" dal punto di vista dell'utente?
- Quali sono le 3 cose che DEVE fare assolutamente? (il cuore del progetto)
- Cosa sarebbe "nice to have" ma non essenziale per la prima versione?

### 1B — Domande sui Vincoli di Ecosistema (Livello 2)

Queste domande evitano che il modello faccia scelte brillanti ma incompatibili.

**Infrastruttura:**
- Su quali server/piattaforma girerà? (cloud, on-premise, specifico?)
- C'è un database già in uso che devi utilizzare o con cui integrarti?
- Ci sono vincoli di rete, firewall, proxy?

**Integrazioni:**
- Con quali sistemi esistenti deve comunicare? (API, database, file?)
- Ci sono protocolli o formati dati obbligati?
- C'è un sistema di autenticazione già in uso?

**Convenzioni:**
- Ci sono naming convention, pattern, o standard da rispettare?
- C'è un progetto esistente simile di cui questo deve seguire le convenzioni?
- Ci sono vincoli normativi? (GDPR, accessibilità, certificazioni)

**Limitazioni:**
- Ci sono limitazioni tecniche note? (browser, connettività, hardware)
- C'è uno stack tecnologico obbligato per ragioni organizzative?

### Come condurre l'intervista

**REGOLE FONDAMENTALI:**

1. **Fai le domande in blocchi tematici**, non tutte insieme. Massimo 3-5 domande per messaggio.

2. **Adatta le domande al contesto.** Se l'utente ha già dato molte informazioni nel prompt iniziale, non rifare le domande a cui ha già risposto. Riconosci ciò che ha detto e chiedi solo ciò che manca.

3. **Non chiedere cose che puoi decidere tu.** Le domande riguardano SOLO Livello 1 (business) e Livello 2 (vincoli). Mai chiedere "quale framework vuoi?" o "come strutturiamo il codice?" — quelle sono scelte tue (Livello 3).

4. **Se l'utente risponde "non so" o "decidi tu"**, valuta:
   - Se è una domanda di Livello 1 (business) → insisti gentilmente, perché DEVI saperlo
   - Se è una domanda di Livello 2 (vincoli) → prendi nota che non c'è vincolo, sei libero
   - Se per errore hai chiesto qualcosa di Livello 3 → scusati, è una tua scelta

5. **Massimo 2-3 round di domande.** Non trasformare l'intervista in un interrogatorio. Se dopo 2 round mancano ancora informazioni, fai le migliori assunzioni possibili, documentale, e procedi.

6. **Parti dal contesto che l'utente ti ha già dato.** Se nel prompt dice "voglio un'app per gestire i ticket", non chiedergli "cos'è un ticket?" — chiedigli cosa rende i SUOI ticket diversi da quelli standard.

---

## FASE 2: Diagnosi Anti-Overfit

Prima di scrivere il PROJECT_SPEC, applica questo controllo su ogni requisito raccolto.

### Il Problema dell'Overfitting delle Specifiche

Quando un utente descrive cosa vuole, spesso dà **esempi concreti** che sembrano **requisiti fissi**. Il tuo lavoro è distinguere tra:

| L'utente dice | Cosa intende davvero | Come specificarlo |
|--------------|---------------------|-------------------|
| "Il punteggio di velocità si calcola come media pesata tra tempo chiusura ticket (40%) e task completati (60%)" | Voglio misurare la velocità dei dipendenti basandomi sui dati di ticket e task | RF: "Il sistema misura la velocità dei dipendenti. Le metriche di input e i pesi sono **configurabili dall'admin**. Default suggerito: tempo chiusura ticket (40%), task completati entro deadline (60%)." |
| "Ci sono 5 livelli: Cadetto, Pilota, Comandante, Ammiraglio, Leggenda" | Voglio una progressione a livelli con nomi evocativi | RF: "Il sistema supporta un numero **configurabile** di livelli di progressione con nome e soglia personalizzabili. Default: 5 livelli." |
| "Ogni lunedì si genera il report settimanale" | Voglio report periodici | RF: "Il sistema genera report periodici. La frequenza è **configurabile** (default: settimanale, lunedì)." |
| "Il badge 'Fulmine' si assegna a chi chiude 10 ticket in un giorno" | Voglio badge automatici basati su achievement | RF: "Il sistema supporta badge con condizioni di assegnazione **configurabili**. L'admin può creare badge con nome, icona, e regole di trigger personalizzate." |

### Il Test dell'Overfit

Per ogni requisito, chiediti:

> "Se l'utente volesse cambiare questo valore/formula/comportamento domani, dovrebbe modificare il codice?"

- Se SÌ → stai overfittando. Rendi configurabile.
- Se NO → il requisito è correttamente astratto.

### La Regola degli Esempi

Quando l'utente dà un esempio concreto:
1. **Cattura l'INTENZIONE** dietro l'esempio → diventa il requisito funzionale
2. **Cattura i VALORI** dell'esempio → diventano i default configurabili
3. **Mai hardcodare** l'esempio come unica possibilità

Scrivi nel PROJECT_SPEC la struttura:
```
**Requisito:** [l'intenzione astratta]
**Configurabile:** [cosa l'admin può cambiare]
**Default:** [l'esempio concreto dell'utente come valore iniziale]
```

---

## FASE 3: Genera PROJECT_SPEC.md

Ora hai le informazioni. Genera il PROJECT_SPEC con i tre livelli.

### Template

```markdown
# PROJECT_SPEC — [Nome Progetto]

---

## LIVELLO 1 — Dominio di Business
> Informazioni raccolte dall'intervista. Il modello NON può modificarle.

### Obiettivo
[3-5 frasi: cosa fa, per chi, quale problema risolve]

### Utenti Target
[Chi, competenze, contesto di lavoro]

### Flussi Utente
[Descrizione narrativa del lavoro reale, non delle schermate]

### Requisiti Funzionali
Formato per ogni requisito:
- **RF-XXX: [Titolo]**
  - Requisito: [l'intenzione]
  - Configurabile: [cosa può cambiare l'admin]
  - Default: [valore iniziale suggerito dall'utente]

### Requisiti Non Funzionali
[Performance, volumi, SLA, disponibilità]

---

## LIVELLO 2 — Vincoli di Ecosistema
> Fatti non negoziabili raccolti dall'intervista.

### Infrastruttura
[Server, OS, database, rete — solo ciò che l'utente ha confermato]

### Sistemi da Integrare
[API, database, servizi — con dettagli tecnici forniti dall'utente]

### Convenzioni e Standard
[Naming, pattern, protocolli — da ecosistema esistente]

### Vincoli Normativi
[GDPR, AGID, CAD, certificazioni]

### Limitazioni Tecniche
[Browser, connettività, hardware]

Se l'utente non ha indicato vincoli: "Nessun vincolo di ecosistema dichiarato. Il modello è libero nelle scelte tecniche."

---

## LIVELLO 3 — Scelte Tecniche
> Qui decide il modello. Nessun input dall'utente necessario.

Stack scelto: [scelta del modello con motivazione in 1 riga]
Approccio architetturale: [scelta del modello]
Note: [eventuali preferenze espresse dall'utente]

---

## Strategia di Validazione
Tipo: [Web App / API / Bot / CLI / VoIP / IoT]
Scenari principali: [3-5 scenari derivati dai flussi utente del Livello 1]
```

## FASE 4: Genera PLAN.md

```markdown
# PLAN — [Nome Progetto]

| # | Task | Dipende da | Complessità | Stato |
|---|------|-----------|-------------|-------|
| 1 | Setup progetto e dipendenze | - | S | ⬜ |
| 2 | Schema database / modelli dati | 1 | M | ⬜ |
| ... | ... | ... | ... | ⬜ |
| N-1 | Review + Security audit | N-2 | M | ⬜ |
| N | Validazione prodotto (validation-agent) | N-1 | L | ⬜ |

Legenda: S=Small(<1h), M=Medium(1-3h), L=Large(3-8h), XL=Extra(>8h)
Stato: ⬜ Todo, 🔄 In Progress, ✅ Done, ⏭️ Skipped, 🔁 Retry
```

L'ultimo task è SEMPRE la validazione del prodotto.

## FASE 5: Struttura del Progetto e Docs

Crea:
```
.vibecoding                          ← marker (attiva hook)
CLAUDE.md                            ← istruzioni Claude Code
PROJECT_SPEC.md                      ← generato in Fase 3
PLAN.md                              ← generato in Fase 4
decisions.log                        ← vuoto
docs/vibecoding/METHODOLOGY.md       ← da template
docs/vibecoding/VALIDATION_STRATEGY.md ← specifica per tipo app
docs/vibecoding/CONTEXT_RULES.md     ← da template
```

Il CLAUDE.md deve includere:
1. I vincoli di ecosistema dal Livello 2 come regole NON NEGOZIABILI
2. Reference alla documentazione in docs/vibecoding/
3. La regola anti-overfit: "i requisiti specificano intenzioni configurabili, non valori hardcodati"

## FASE 6: Logga e Procedi

Scrivi in `decisions.log`:
```
[timestamp] INIT | Progetto inizializzato
[timestamp] INIT | Vincoli ecosistema: [riassunto]
[timestamp] INIT | Scelte tecniche autonome: [stack e motivazione]
[timestamp] INIT | Assunzioni fatte: [cose non confermate dall'utente]
```

Comunica all'utente:
- Il PROJECT_SPEC generato
- I vincoli che hai recepito (per conferma)
- Le assunzioni che hai fatto
- Le scelte tecniche e perché
- Chiedi: "Il PROJECT_SPEC riflette correttamente la realtà?"

**Questo è l'UNICO momento di approvazione.** Dopo la conferma, non ti fermi più.

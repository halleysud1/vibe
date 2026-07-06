---
name: validation-strategies
description: "Checklist di scenari di validazione per tipo di applicazione — web app, REST API, bot, CLI, data pipeline, IoT. Definisce COSA verificare dal punto di vista utente; il COME è delegato ai tool nativi di Claude Code (/verify, /run, Claude Preview). Usala quando devi validare un modulo prima del rilascio o scegliere gli scenari da coprire."
---

# validation-strategies — scenari di validazione per tipo di applicazione

## Principio fondamentale

**Il software non è finito quando compila e i test passano. È finito quando un
utente può usarlo.** Il testing verifica il codice; la validazione verifica il
prodotto. Questa skill dice **cosa** verificare per ciascun tipo di app; il
**come** lo fanno i meccanismi nativi di Claude Code.

## Come si esegue (meccanica → nativa)

| Esecuzione | Strumento |
|---|---|
| Validare una modifica osservando l'app reale | skill nativa `/verify` |
| Avviare/guidare l'app del progetto | skill nativa `/run` |
| Web app nel browser (screenshot, console, network, click, form, viewport) | **Claude Preview** (`.claude/launch.json` + `preview_start`; guida in linguaggio naturale) |
| Web multi-browser/multi-tab, o fuori da Claude Code Desktop | Playwright (fallback — script ad hoc, li scrive la sessione) |
| API / CLI / pipeline | script `httpx`/shell ad hoc + exit code |

Non mantenere script-fotocopia in questa skill: la sessione li scrive meglio
sul caso concreto. Qui vive solo la **checklist di scenari**, che è ciò che
si dimentica.

---

## 1. Web application

1. **First visit** — homepage carica entro tempi accettabili? Errori JS in console? Richieste di rete fallite?
2. **Registrazione / Login / Logout** — il flusso auth funziona end-to-end? Con dati invalidi cosa succede?
3. **Navigazione** — tutte le pagine raggiungibili, link funzionanti?
4. **Operazione principale** — l'azione core dell'app funziona?
5. **Form** — inserimento dati, validazione, doppio submit
6. **Responsiveness** — viewport mobile (375px) e desktop (1920px); dark mode se prevista
7. **Errori utente** — form vuoti, input invalidi
8. **Back/Refresh** — il back button rompe qualcosa? Un refresh perde dati?

Evidenze: screenshot per step, console log, network errors, tempi di caricamento.

## 2. REST API / Backend

1. **Health check** — GET /health risponde 200?
2. **Auth flow** — registrazione / login / token / accesso protetto / refresh / logout
3. **CRUD completo** — per ogni risorsa: Create / Read / Update / Delete / Verify Deleted
4. **Input invalido** — body malformato, campi mancanti, tipi sbagliati su ogni endpoint
5. **Auth enforcement** — senza token 401? Token sbagliato 403?
6. **Idempotenza** — doppia creazione della stessa risorsa: 409 o gestione corretta?
7. **Paginazione** — se l'API pagina, i parametri funzionano?
8. **Persistenza** — crea un dato, riavvia il server, il dato c'è ancora?

## 3. Bot / Chatbot / Assistente

1. **Greeting** — risponde al primo messaggio?
2. **Comandi base** — ogni comando registrato funziona?
3. **Conversazione multi-step** — un flusso a più messaggi sequenziali funziona?
4. **Input inatteso** — emoji, messaggi vuoti, messaggi lunghissimi
5. **Timeout** — risponde entro X secondi?
6. **Stato** — lo stato conversazionale persiste correttamente?
7. **Whitelist/permessi** — un utente non autorizzato viene rifiutato?

## 4. CLI tool

1. **Help / Version** — `--help` leggibile, `--version` corretta
2. **Happy path** — il caso d'uso principale funziona?
3. **Input invalido** — file inesistente, formato sbagliato, permessi insufficienti
4. **Exit code** — 0 per successo, non-zero per errore?
5. **Pipe** — stdin/stdout per piping (se applicabile)
6. **Output format** — JSON/CSV/testo ben formattato?

## 5. Data pipeline / ETL

1. **Dati validi** — il dataset di test produce output corretto?
2. **Dati malformati** — righe vuote, encoding errato, null inattesi
3. **Idempotenza** — due esecuzioni, stesso risultato?
4. **Performance** — tempi su N record, scala linearmente?
5. **Recovery** — crash a metà: può riprendere?

## 6. IoT / Embedded

1. **Connessione** — il dispositivo (o mock) si connette?
2. **Telemetria** — dati ricevuti e salvati correttamente?
3. **Comandi** — il server può comandare il dispositivo?
4. **Disconnessione / Riconnessione** — offline gestito, riconnessione automatica?

---

## Come scegliere e registrare la strategia

In `/vibecoding:init` (o via `skill-bootstrap`), determina il tipo di
applicazione e scrivi `docs/VALIDATION_STRATEGY.md`:

```markdown
# VALIDATION STRATEGY — [Nome Progetto]
## Tipo applicazione: [Web / API / Bot / CLI / Pipeline / IoT]
## Esecuzione: [/verify + Claude Preview / script httpx / ...]
## Scenari specifici
| # | Scenario | Priorità |
|---|----------|----------|
## Come avviare il prodotto per la validazione
[comandi]
```

Nota: per gli agenti scaffoldati con `/agentify`, la validazione del ruolo
coding-agent ha una via dedicata — `eval_coder` sui golden task (vedi
agentify, Fase 5.5).

---

## Anti-pattern

### A1. Validare solo i test unitari
I test verificano singole funzioni; la validazione prova il **prodotto** dal
punto di vista utente. Complementari, non sostituibili.

### A2. Strategia generica per tutti i progetti
Una web app si valida diversamente da una CLI o da un bot: scegli dalla
checklist giusta, non improvvisare.

### A3. Saltare la validazione "perché c'è poco tempo"
Se non c'è tempo per validare, non c'è tempo per rilasciare: riduci lo scope.

### A4. Confondere "deployato" con "validato"
Online ≠ funzionante per l'utente: la validazione prova sequenze di azioni reali.

### A5. Script-fotocopia mantenuti nella skill
Boilerplate Playwright/httpx invecchia e duplica ciò che la sessione scrive
meglio sul caso concreto. La skill mantiene gli scenari, non il codice.

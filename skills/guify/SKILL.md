---
name: guify
description: "Trasforma una lavorazione Claude Code in un'interfaccia grafica collegata alla sessione o all'agente — invece di consegnare la cartella con le skill, consegni una GUI. Gate multi-superficie: widget in-chat, artifact condivisibile, app standalone self-hosted sopra Agent SDK (abbonamento a prezzo fisso) o AgentOS (agentify). Console di controllo, dashboard, form→prompt, chat custom, con RBAC a livello endpoint e approvazioni sul diff. Usala quando l'utente vuole una GUI collegata a Claude Code o distribuire una lavorazione a chi non usa Claude."
---

# /guify — Distribuisci una lavorazione come interfaccia grafica

Una lavorazione Claude Code (cartella + skill + sessione) funziona per chi usa
Claude Code. Per tutti gli altri — colleghi senza account, utenti terzi, il
direttore che vuole un pannello — la lavorazione si **distribuisce come GUI**:
un'interfaccia collegata alla sessione o all'agente, dove il lavoro si lancia,
si osserva e si approva senza vedere Claude.

La skill è **portabile**: funziona su qualunque lavorazione, con o senza
agentify. L'output tipico è uno di questi, o una combinazione:

- **Console di controllo** — lanciare task, seguire l'avanzamento, approvare le proposte (OUTBOX/diff)
- **Dashboard** — stato, report e metriche prodotti dalla sessione o dall'agente
- **Form → prompt strutturati** — maschere di input validato che diventano istruzioni precise
- **Chat custom** — interfaccia conversazionale propria (branding, permessi)

## Quando usare / quando NON usare

**Usala quando:**
- L'utente vuole una GUI **collegata** a una sessione Claude Code o a un agente agentify
- Vuole distribuire una lavorazione a chi non usa Claude Code (la GUI è il formato di consegna)
- Vuole pannelli di approvazione, dashboard o form sopra un flusso già esistente

**NON usarla quando:**
- La GUI **è il prodotto** del progetto (una web app da sviluppare) → è sviluppo normale: `/run`, `/verify`, Claude Preview
- Serve solo una chat via Telegram sopra un agente agentify → agentify la scaffolda già (SKILL agentify § Interfaces)
- Serve un grafico una tantum dentro la conversazione → widget diretto, senza scaffolding

## Intervista d'ingresso (OBBLIGATORIA, appena la skill è invocata)

Come per agentify: la superficie giusta dipende dai casi d'uso, e assumerli è
il modo tipico di costruire la GUI sbagliata. Via `AskUserQuestion`, un batch:

1. **Casi d'uso concreti** — quali pannelli servono, uno per uno (console/dashboard/form/chat), con esempi reali
2. **Chi la usa** — solo l'utente / colleghi CON account Claude / colleghi o terzi SENZA account
3. **Cosa c'è sotto** — una sessione Claude Code viva / sessioni headless da aprire su richiesta (Agent SDK) / un agente agentify già scaffoldato (AgentOS)
4. **Direzione** — osservare / comandare / bidirezionale; e per i terzi: bastano form strutturati o serve chat libera? (vedi regola G1)

## Il gate multi-superficie: le risposte decidono da sole

| Chi la usa | Superficie | Collegamento | Costo/infra |
|---|---|---|---|
| Solo l'utente, dentro la sessione | **Widget in-chat** (`templates/widget/PATTERNS.md`) | `sendPrompt()` rimanda l'input alla sessione | zero |
| Colleghi CON account Claude, zero infra | **Artifact con capabilities** (`templates/artifact/PATTERNS.md`) | stato condiviso fra viewer; commenti e salvataggi svegliano la sessione (watch) | zero; gira su claude.ai |
| Colleghi/terzi SENZA account | **App standalone** (`templates/standalone/`) su **Agent SDK** — abbonamento a prezzo fisso, self-hosted | backend FastAPI che apre/riprende sessioni Claude headless | tua (PC/server/cloud) |
| Progetto già agentificato | **App standalone** con engine `agentos` | REST dell'agente Agno + file ops (OUTBOX) | tua |

La superficie standalone è **una sola app con due engine intercambiabili**
(`engine: sdk | agentos` nel manifesto): la GUI non cambia, cambia l'adapter.
Se i casi d'uso sono misti (es. dashboard per colleghi + console per te),
scegli la superficie della persona **meno privilegiata**: le altre ci
convivono.

Registra l'esito nel manifesto `gui.yaml` (superficie, engine, casi d'uso,
ruoli): la prossima sessione non rifà l'intervista.

## Regole di sicurezza (non opzionali)

La GUI è un moltiplicatore di accesso: chi la usa comanda — direttamente o via
form — un modello con i permessi della lavorazione. Le regole seguono la
stessa filosofia del tool-guard di agentify: enforcement meccanico, non
istruzioni nel prompt.

- **G1 — Per i terzi, form strutturati di default.** Una chat libera collegata
  a una sessione con tool è prompt injection by design: chi scrive comanda.
  La chat libera si concede per **decisione esplicita** dell'utente, solo ai
  ruoli elencati in `chat.free_chat_roles`, e la sessione sotto gira comunque
  coi permessi ridotti dichiarati in `session.allowed_tools`.
- **G2 — RBAC a livello endpoint, default-deny.** Ruolo → capabilities in
  `gui.yaml`; l'enforcement sta in `rbac.py` (dependency FastAPI), mai nel
  system prompt. Ciò che non è elencato è negato.
- **G3 — Il token Claude vive solo server-side.** La GUI ha la SUA
  autenticazione (account → ruolo); l'OAuth dell'abbonamento o le API key non
  raggiungono mai il browser.
- **G4 — Le approvazioni mostrano il diff reale.** Stesso principio
  dell'OUTBOX di agentify: chi approva rivede codice/contenuto, non un titolo.
- **G5 — La sessione sotto la GUI ha permessi dichiarati.** L'adapter SDK
  passa `allowed_tools` e `permission_mode` dal manifesto: una GUI esposta non
  monta mai una sessione full-access.
- **G6 — Audit append-only.** Ogni azione (chi, cosa, quando, esito) in
  `logs/gui_audit.log`.

Limite onesto da dichiarare (ereditato dal gate di agentify): con engine `sdk`
la quota è quella dell'abbonamento, condivisa con l'uso interattivo; per
servizi esposti a terzi verificare che i termini dell'abbonamento coprano
quell'uso — in dubbio, engine `agentos` o API a token.

## Scaffolding (superficie standalone)

I template sono in `${CLAUDE_PLUGIN_ROOT}/skills/guify/templates/standalone/`.
Struttura generata nel progetto target:

```
gui/
├── gui.yaml                # manifesto (output dell'intervista)
├── server/
│   ├── app.py              # FastAPI: auth, RBAC, task, outbox, form, chat WS, dashboard
│   ├── engine_sdk.py       # adapter: sessioni Claude headless via Agent SDK (abbonamento)
│   ├── engine_agentos.py   # adapter: REST AgentOS + file ops di agentify
│   ├── rbac.py             # ruoli → capabilities, default-deny
│   └── prompts.py          # form → prompt strutturati (template dichiarati, input validato)
├── web/
│   └── index.html          # frontend single-file: tab console/dashboard/form/chat
└── tests/
    └── test_rbac.py        # default-deny, ruoli, free-chat gating (no API calls)
```

Regole di rendering: come agentify — sostituisci ogni `{{ placeholder }}` con
i valori del manifesto, rinomina togliendo `.template`, e verifica che non
sopravvivano né `{{` né `TODO durante scaffolding` (anti-pattern A6 di
agentify vale identico qui).

Dipendenze: `fastapi`, `uvicorn`, `pyyaml`; engine sdk: `claude-agent-sdk`;
engine agentos: `httpx`. Aggiungile a `requirements.txt` del progetto.

## Superfici leggere

- **Widget in-chat** (`templates/widget/PATTERNS.md`): pannelli e form
  effimeri dentro la conversazione; l'input torna alla sessione via
  `sendPrompt()`. Zero file nel progetto: pattern, non scaffold.
- **Artifact** (`templates/artifact/PATTERNS.md`): pagina pubblicata con stato
  condiviso e risveglio della sessione. Prima di costruire, carica la skill
  `artifact-capabilities` se disponibile: è l'autorità sul runtime.

## Validazione

1. **RBAC test (no API):** `pytest gui/tests/test_rbac.py -v` — default-deny,
   viewer non approva, free-chat solo ai ruoli concessi.
2. **Avvio:** `uvicorn gui.server.app:app` → login con un account `viewer` e
   uno `admin`: il viewer NON deve vedere i bottoni di approvazione né la chat.
3. **Round-trip:** lancia un task dal form → verifica che il prompt generato
   sia quello del template (loggato in audit) → l'esito compare in dashboard.
4. **Approvazione:** genera una proposta → l'approvazione mostra il diff reale
   → dopo l'approvazione l'audit ha chi/quando.
5. **Checklist web app** della skill `validation-strategies` (§1) per la parte
   browser.

## Anti-pattern

### G-A1. Chat libera per tutti "perché è comoda"
È il modo di dare a ogni utente della GUI i permessi della lavorazione. Form
strutturati di default; chat libera = decisione esplicita + ruoli elencati +
sessione a permessi ridotti.

### G-A2. RBAC nel system prompt
"Non permettere agli utenti viewer di approvare" scritto nel prompt non è un
controllo. L'autorizzazione sta in `rbac.py`, sull'endpoint.

### G-A3. Token nel frontend
Se l'OAuth o una API key compare in `index.html`, in una env var del browser o
in una response API, chiunque usi la GUI possiede l'account. Server-side only.

### G-A4. La GUI come seconda fonte di verità
La GUI mostra lo stato della lavorazione (file ops, git, sessioni) — non ne
tiene una copia sua che diverge. Se serve stato proprio (utenti, audit), è
separato e dichiarato.

### G-A5. Scaffoldare la superficie pesante per un caso leggero
Un grafico per te stesso non giustifica FastAPI + RBAC: è un widget. Il gate
esiste per questo — rispettalo anche quando "tanto ormai".

## Checklist auto-verifica

1. Ho fatto l'intervista d'ingresso (casi d'uso, utenti, motore, direzione) PRIMA di scegliere la superficie?
2. La superficie scelta è quella della persona meno privilegiata che userà la GUI?
3. `gui.yaml` registra superficie, engine, casi d'uso, ruoli e boundaries?
4. Per i terzi: form strutturati, e la chat libera (se c'è) è una decisione esplicita dell'utente con ruoli elencati?
5. RBAC default-deny testato (`test_rbac.py` verde) e token solo server-side?
6. Le approvazioni mostrano il diff reale e finiscono nell'audit?
7. Nessun `{{ placeholder }}` né `TODO durante scaffolding` nei file finali?
8. Ho dichiarato il limite di quota dell'abbonamento (engine sdk) o il costo a token (engine agentos)?

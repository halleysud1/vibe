---
name: validation-strategies
description: "Strategie di validazione per ogni tipo di applicazione — web app (Claude Preview o Playwright), REST API, bot, CLI, data pipeline, IoT. Definisce COME testare il prodotto dal punto di vista utente. Usala quando devi validare un modulo prima del rilascio o decidere quali scenari coprire in `/review`."
---

# validation-strategies — strategie di validazione per tipo di applicazione

## Principio fondamentale

**Il software non è finito quando compila e i test passano. È finito quando un utente
può usarlo.**

La validazione non è testing. Il testing verifica il codice. La validazione verifica
il prodotto. Ogni tipo di applicazione richiede una strategia diversa per "essere l'utente".

---

## 0. Web Application — Claude Preview (METODO PREFERITO)

> Quando i tool MCP `preview_*` sono disponibili, usali al posto di Playwright.
> Sono più veloci, integrati, e non richiedono dipendenze esterne.

### Prerequisiti
- Tool MCP `preview_*` disponibili nella sessione
- File `.claude/launch.json` con configurazione del dev server

### Setup
Se `.claude/launch.json` non esiste, crealo:
```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "dev",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "port": 3000
    }
  ]
}
```

### Mapping scenari → tool Preview

| Scenario | Tool | Come verificare |
|----------|------|-----------------|
| Homepage carica | `preview_screenshot` | Pagina visibile, layout corretto |
| Errori JavaScript | `preview_console_logs(level: "error")` | Nessun errore in console |
| API funzionanti | `preview_network(filter: "failed")` | Nessuna richiesta fallita |
| Testo e struttura | `preview_snapshot` | Accessibility tree corretto |
| Click e navigazione | `preview_click(selector)` + `preview_snapshot` | Stato aggiornato |
| Compilazione form | `preview_fill(selector, value)` + `preview_snapshot` | Dati inseriti, form funziona |
| Stili CSS | `preview_inspect(selector, styles: [...])` | Valori corretti |
| Mobile responsive | `preview_resize(preset: "mobile")` | Layout adattato |
| Dark mode | `preview_resize(colorScheme: "dark")` | Tema applicato |
| API response body | `preview_network(requestId: "...")` | Dati corretti |

### Quando usare Playwright invece
- Tool `preview_*` non disponibili
- Serve test multi-tab o multi-browser
- Serve automazione oltre Chromium
- Il progetto non ha un dev server configurabile

---

## 1. Web Application — Playwright (FALLBACK)

### Strumenti
- **Playwright** (primario) — browser automation con screenshot
- **Lighthouse CLI** (supplementare) — performance e accessibilità

### Setup
```bash
pip install playwright --break-system-packages && playwright install chromium
# oppure
npm install -D @playwright/test && npx playwright install chromium
```

### Scenari obbligatori
1. **First Visit** — la homepage carica? Entro quanti secondi? Errori JS in console?
2. **Registrazione** — l'utente può creare un account? Con dati invalidi cosa succede?
3. **Login/Logout** — il flusso di autenticazione funziona end-to-end?
4. **Navigazione** — tutte le pagine sono raggiungibili? I link funzionano?
5. **Operazione principale** — l'azione core dell'app funziona?
6. **Responsiveness** — il layout funziona su viewport mobile (375px) e desktop (1920px)?
7. **Errori utente** — form vuoti, input invalidi, doppio submit — cosa succede?
8. **Back/Refresh** — il browser back button rompe qualcosa? Un refresh perde dati?

### Evidenze da catturare
- Screenshot ad ogni step (salva in `validation_screenshots/`)
- Console log e errori JavaScript
- Tempi di caricamento per pagina
- Network errors (chiamate API fallite)

### Template script
```python
# validation/validate_web.py
from playwright.sync_api import sync_playwright
import json, os, time

os.makedirs("validation_screenshots", exist_ok=True)
results = {"scenarios": [], "js_errors": [], "network_errors": []}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()

    page.on("pageerror", lambda e: results["js_errors"].append(str(e)))
    page.on("response", lambda r: results["network_errors"].append(
        {"url": r.url, "status": r.status}
    ) if r.status >= 400 else None)

    # === SCENARIO 1: Homepage ===
    start = time.time()
    page.goto("http://localhost:3000", wait_until="networkidle")
    load_time = (time.time() - start) * 1000
    page.screenshot(path="validation_screenshots/01_homepage.png")
    results["scenarios"].append({
        "name": "Homepage Load",
        "passed": page.title() != "" and load_time < 5000,
        "load_time_ms": round(load_time),
        "details": f"Title: {page.title()}"
    })

    # === SCENARIO 2+: specifici per il progetto ===

    browser.close()

with open("validation_results.json", "w") as f:
    json.dump(results, f, indent=2)

passed = sum(1 for s in results["scenarios"] if s["passed"])
total = len(results["scenarios"])
print(f"\nVALIDATION: {passed}/{total} scenarios passed")
```

---

## 2. REST API / Backend

### Strumenti
- **httpx** (Python) o **fetch** (Node) — client HTTP
- **jq** (bash) — analisi rapida JSON

### Scenari obbligatori
1. **Health check** — GET /health risponde 200?
2. **Auth flow** — registrazione / login / token / accesso protetto / refresh / logout
3. **CRUD completo** — per ogni risorsa: Create / Read / Update / Delete / Verify Deleted
4. **Input invalido** — ogni endpoint con body malformato, campi mancanti, tipi sbagliati
5. **Auth enforcement** — endpoint protetto senza token 401? Con token sbagliato 403?
6. **Idempotenza** — creare due volte la stessa risorsa: 409 o gestione corretta?
7. **Paginazione** — se l'API pagina, i parametri funzionano?
8. **Persistenza** — crea un dato, riavvia il server, il dato è ancora lì?

### Template script
```python
# validation/validate_api.py
import httpx, json

BASE = "http://localhost:8000"
results = {"scenarios": [], "performance": {}}

def check(name, response, expected_status, body_check=None):
    ok = response.status_code == expected_status
    detail = ""
    if body_check and ok:
        try:
            ok = body_check(response.json())
        except Exception as e:
            ok = False
            detail = f"Body check failed: {e}"
    results["scenarios"].append({
        "name": name,
        "passed": ok,
        "status": response.status_code,
        "expected_status": expected_status,
        "time_ms": round(response.elapsed.total_seconds() * 1000),
        "detail": detail or response.text[:300]
    })
    return ok, response

with httpx.Client(base_url=BASE, timeout=30) as c:
    check("Health Check", c.get("/health"), 200)

    ok, r = check("Register", c.post("/auth/register", json={
        "email": "validator@test.com", "password": "Val1dP@ss!"
    }), 201)

    ok, r = check("Login", c.post("/auth/login", json={
        "email": "validator@test.com", "password": "Val1dP@ss!"
    }), 200)

    token = r.json().get("access_token", "") if ok else ""
    auth = {"Authorization": f"Bearer {token}"}

    check("No Auth -> 401", c.get("/api/protected"), 401)
    check("With Auth -> 200", c.get("/api/protected", headers=auth), 200)

    # ... CRUD scenarios specifici per il progetto

with open("validation_results.json", "w") as f:
    json.dump(results, f, indent=2)
```

---

## 3. Bot / Chatbot / Assistente

### Strumenti
- Client specifico per la piattaforma (Telegram Bot API, Discord.py, WebSocket client)
- Conversation simulator — script che invia messaggi e verifica risposte

### Scenari obbligatori
1. **Greeting** — il bot risponde al primo messaggio?
2. **Comandi base** — ogni comando registrato funziona?
3. **Conversazione multi-step** — un flusso che richiede più messaggi sequenziali funziona?
4. **Input inatteso** — emoji, messaggi vuoti, messaggi lunghissimi
5. **Timeout** — il bot risponde entro X secondi?
6. **Stato** — se il bot ha stato conversazionale, persiste correttamente?

---

## 4. CLI tool

### Scenari obbligatori
1. **Help** — `--help` stampa un help leggibile?
2. **Version** — `--version` mostra la versione?
3. **Happy path** — il caso d'uso principale funziona?
4. **Input invalido** — file inesistente, formato sbagliato, permessi insufficienti
5. **Exit code** — 0 per successo, non-zero per errore?
6. **Pipe** — funziona con stdin/stdout per piping? (se applicabile)
7. **Output format** — JSON/CSV/testo è ben formattato?

---

## 5. Data pipeline / ETL

### Scenari obbligatori
1. **Dati validi** — il dataset di test produce output corretto?
2. **Dati malformati** — righe vuote, encoding errato, null inattesi
3. **Idempotenza** — eseguire la pipeline 2 volte produce lo stesso risultato?
4. **Performance** — quanto impiega su N record? Scala linearmente?
5. **Recovery** — se la pipeline crasha a metà, può riprendere?

---

## 6. IoT / Embedded

### Scenari obbligatori
1. **Connessione** — il dispositivo (o mock) si connette al server?
2. **Telemetria** — i dati vengono ricevuti e salvati correttamente?
3. **Comandi** — il server può inviare comandi al dispositivo?
4. **Disconnessione** — cosa succede quando il dispositivo va offline?
5. **Riconnessione** — il dispositivo si riconnette automaticamente?

---

## Come scegliere la strategia

Quando `/vibecoding:init` viene eseguito (o invochi `skill-bootstrap`), determina
il tipo di applicazione e scrivi in `docs/VALIDATION_STRATEGY.md`:

```markdown
# VALIDATION STRATEGY — [Nome Progetto]

## Tipo applicazione
[Web App / API / Bot / CLI / Pipeline / IoT]

## Metodo preferito
[Claude Preview / Playwright / httpx / custom]

## Strategia
[dalla sezione corrispondente sopra]

## Scenari specifici

| # | Scenario | Descrizione | Priorità |
|---|----------|-------------|----------|
| 1 | ... | ... | Alta |
| 2 | ... | ... | Alta |
| 3 | ... | ... | Media |

## Strumenti necessari
[Lista dipendenze da installare per la validazione]

## Come avviare il prodotto per la validazione
[Comandi per avviare il server/servizio in locale]
```

---

## Anti-pattern

### A1. Validare solo i test unitari
I test unitari verificano singole funzioni. La validazione verifica il **prodotto
completo** dal punto di vista utente. Sono complementari, non sostituibili.

### A2. Strategia generica per tutti i progetti
Una web app si valida diversamente da una CLI o da un bot. Scegli la strategia
giusta dal mapping sopra, non improvvisare.

### A3. Saltare la validazione "perché c'è poco tempo"
Se non c'è tempo per validare, non c'è tempo per rilasciare. Riduci lo scope, non
saltare la validazione.

### A4. Confondere "deployato" con "validato"
Il fatto che l'app sia online non significa che funzioni per l'utente. La validazione
prova le sequenze di azioni reali.

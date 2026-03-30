---
name: validation-strategies
description: "Guida completa alle strategie di validazione per ogni tipo di applicazione. Definisce COME il validation-agent deve testare il prodotto in base al tipo di software. Include Claude Preview come metodo preferito per web app."
---

# Strategie di Validazione — Per Tipo di Applicazione

## Principio Fondamentale

**Il software non è finito quando compila e i test passano. È finito quando un utente può usarlo.**

La validazione non è testing. Il testing verifica il codice. La validazione verifica il prodotto. Ogni tipo di applicazione richiede una strategia diversa per "essere l'utente".

---

## 0. Web Application — Claude Preview (METODO PREFERITO)

> **Novità 2.1**: Quando i tool MCP `preview_*` sono disponibili, usa quelli al posto di Playwright. Sono più veloci, integrati, e non richiedono dipendenze esterne.

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

### Mapping Scenari -> Tool Preview

| Scenario | Tool | Come verificare |
|----------|------|----------------|
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

### Scenari Obbligatori
1. **First Visit** — La homepage carica? Entro quanti secondi? Errori JS in console?
2. **Registrazione** — L'utente può creare un account? Con dati invalidi cosa succede?
3. **Login/Logout** — Il flusso di autenticazione funziona end-to-end?
4. **Navigazione** — Tutte le pagine sono raggiungibili? I link funzionano?
5. **Operazione Principale** — L'azione core dell'app funziona?
6. **Responsiveness** — Il layout funziona su viewport mobile (375px) e desktop (1920px)?
7. **Errori Utente** — Form vuoti, input invalidi, doppio submit — cosa succede?
8. **Back/Refresh** — Il browser back button rompe qualcosa? Un refresh perde dati?

### Evidenze da Catturare
- Screenshot ad ogni step (salva in `validation_screenshots/`)
- Console log e errori JavaScript
- Tempi di caricamento per pagina
- Network errors (chiamate API fallite)

### Template Script
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
- **jq** (bash) — per analisi rapida JSON

### Scenari Obbligatori
1. **Health Check** — GET /health risponde 200?
2. **Auth Flow** — Registrazione / Login / Token / Accesso protetto / Refresh / Logout
3. **CRUD Completo** — Per ogni risorsa: Create / Read / Update / Delete / Verify Deleted
4. **Input Invalido** — Ogni endpoint con body malformato, campi mancanti, tipi sbagliati
5. **Auth Enforcement** — Endpoint protetto senza token 401? Con token sbagliato 403?
6. **Idempotenza** — Creare due volte la stessa risorsa 409 o gestione corretta?
7. **Paginazione** — Se l'API pagina, i parametri funzionano?
8. **Persistenza** — Crea un dato, riavvia il server, il dato è ancora lì?

### Template Script
```python
# validation/validate_api.py
import httpx, json, time

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
- **Client specifico per la piattaforma** (Telegram Bot API, Discord.py, WebSocket client)
- **Conversation simulator** — script che invia messaggi e verifica risposte

### Scenari Obbligatori
1. **Greeting** — Il bot risponde al primo messaggio?
2. **Comandi Base** — Ogni comando registrato funziona?
3. **Conversazione Multi-Step** — Un flusso che richiede più messaggi sequenziali funziona?
4. **Input Inatteso** — Emoji, messaggi vuoti, messaggi lunghissimi
5. **Timeout** — Il bot risponde entro X secondi?
6. **Stato** — Se il bot ha stato conversazionale, persiste correttamente?

---

## 4. CLI Tool

### Scenari Obbligatori
1. **Help** — `--help` stampa un help leggibile?
2. **Version** — `--version` mostra la versione?
3. **Happy Path** — Il caso d'uso principale funziona?
4. **Input Invalido** — File inesistente, formato sbagliato, permessi insufficienti
5. **Exit Code** — 0 per successo, non-zero per errore?
6. **Pipe** — Funziona con stdin/stdout per piping? (se applicabile)
7. **Output Format** — JSON/CSV/testo è ben formattato?

---

## 5. Data Pipeline / ETL

### Scenari Obbligatori
1. **Dati Validi** — Il dataset di test produce output corretto?
2. **Dati Malformati** — Righe vuote, encoding errato, null inattesi
3. **Idempotenza** — Eseguire la pipeline 2 volte produce lo stesso risultato?
4. **Performance** — Quanto impiega su N record? Scala linearmente?
5. **Recovery** — Se la pipeline crasha a metà, può riprendere?

---

## 6. IoT / Embedded

### Scenari Obbligatori
1. **Connessione** — Il dispositivo (o mock) si connette al server?
2. **Telemetria** — I dati vengono ricevuti e salvati correttamente?
3. **Comandi** — Il server può inviare comandi al dispositivo?
4. **Disconnessione** — Cosa succede quando il dispositivo va offline?
5. **Riconnessione** — Il dispositivo si riconnette automaticamente?

---

## Come Scegliere la Strategia

Quando `/vibecoding:init` viene eseguito, determina il tipo di applicazione e scrivi in `docs/vibecoding/VALIDATION_STRATEGY.md`:

```markdown
# VALIDATION STRATEGY — [Nome Progetto]

## Tipo Applicazione: [Web App / API / Bot / CLI / Pipeline / IoT]
## Metodo Preferito: [Claude Preview / Playwright / httpx / custom]
## Strategia: [dalla sezione corrispondente sopra]

## Scenari Specifici

| # | Scenario | Descrizione | Priorità |
|---|----------|-------------|----------|
| 1 | ... | ... | Alta |
| 2 | ... | ... | Alta |
| 3 | ... | ... | Media |

## Strumenti Necessari
[Lista dipendenze da installare per la validazione]

## Come Avviare il Prodotto per la Validazione
[Comandi per avviare il server/servizio in locale]
```

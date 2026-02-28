---
name: validation-strategies
description: "Guida completa alle strategie di validazione per ogni tipo di applicazione. Definisce COME il validation-agent deve testare il prodotto in base al tipo di software."
---

# Strategie di Validazione — Per Tipo di Applicazione

## Principio Fondamentale

**Il software non è finito quando compila e i test passano. È finito quando un utente può usarlo.**

La validazione non è testing. Il testing verifica il codice. La validazione verifica il prodotto. Ogni tipo di applicazione richiede una strategia diversa per "essere l'utente".

---

## 1. Web Application (Frontend + Backend)

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
5. **Operazione Principale** — L'azione core dell'app funziona? (es. creare un ordine, inviare un messaggio)
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
    
    # === SCENARIO 2: Registrazione ===
    # ... (specifico per il progetto)
    
    # === SCENARIO N: Viewport Mobile ===
    context_mobile = browser.new_context(viewport={"width": 375, "height": 812})
    page_mobile = context_mobile.new_page()
    page_mobile.goto("http://localhost:3000", wait_until="networkidle")
    page_mobile.screenshot(path="validation_screenshots/mobile_home.png")
    # Verifica che non ci siano scroll orizzontali
    has_h_scroll = page_mobile.evaluate(
        "document.documentElement.scrollWidth > document.documentElement.clientWidth"
    )
    results["scenarios"].append({
        "name": "Mobile Responsive",
        "passed": not has_h_scroll,
        "details": "No horizontal scroll" if not has_h_scroll else "Horizontal scroll detected"
    })
    
    browser.close()

with open("validation_results.json", "w") as f:
    json.dump(results, f, indent=2)

# Stampa summary
passed = sum(1 for s in results["scenarios"] if s["passed"])
total = len(results["scenarios"])
print(f"\n{'='*50}")
print(f"VALIDATION: {passed}/{total} scenarios passed")
print(f"JS Errors: {len(results['js_errors'])}")
print(f"Network Errors: {len(results['network_errors'])}")
print(f"{'='*50}")
```

---

## 2. REST API / Backend

### Strumenti
- **httpx** (Python) o **fetch** (Node) — client HTTP
- **jq** (bash) — per analisi rapida JSON

### Scenari Obbligatori
1. **Health Check** — GET /health risponde 200?
2. **Auth Flow** — Registrazione → Login → Token → Accesso risorsa protetta → Refresh → Logout
3. **CRUD Completo** — Per ogni risorsa: Create → Read → Update → Delete → Verify Deleted
4. **Input Invalido** — Ogni endpoint con body malformato, campi mancanti, tipi sbagliati
5. **Auth Enforcement** — Ogni endpoint protetto senza token → 401? Con token sbagliato → 403?
6. **Idempotenza** — Creare due volte la stessa risorsa → 409 o gestione corretta?
7. **Paginazione** — Se l'API pagina, i parametri funzionano?
8. **Persistenza** — Crea un dato, riavvia il server, il dato è ancora lì?

### Template Script
```python
# validation/validate_api.py
import httpx, json, time, subprocess, signal

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
    # Health
    check("Health Check", c.get("/health"), 200)
    
    # Auth flow
    ok, r = check("Register", c.post("/auth/register", json={
        "email": "validator@test.com", "password": "Val1dP@ss!"
    }), 201)
    
    ok, r = check("Login", c.post("/auth/login", json={
        "email": "validator@test.com", "password": "Val1dP@ss!"
    }), 200)
    
    token = r.json().get("access_token", "") if ok else ""
    auth = {"Authorization": f"Bearer {token}"}
    
    # Protected endpoint without auth
    check("No Auth → 401", c.get("/api/protected"), 401)
    
    # Protected endpoint with auth
    check("With Auth → 200", c.get("/api/protected", headers=auth), 200)
    
    # ... CRUD scenarios specifici per il progetto

# Summary
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
4. **Input Inatteso** — Cosa succede con emoji, messaggi vuoti, messaggi lunghissimi?
5. **Timeout** — Il bot risponde entro X secondi?
6. **Stato** — Se il bot ha stato conversazionale, persiste correttamente?

### Per VoIP/SIP
```python
# validation/validate_voip.py
import socket, time

results = {"scenarios": []}

# 1. SIP Server raggiungibile
def check_port(host, port, name):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        result = s.connect_ex((host, port))
        results["scenarios"].append({
            "name": name,
            "passed": result == 0,
            "detail": "reachable" if result == 0 else f"connection refused (code {result})"
        })
    finally:
        s.close()

check_port("localhost", 5060, "SIP Server Port 5060")
check_port("localhost", 8088, "WebSocket Port 8088")

# 2. SIP OPTIONS ping (verifica che il server SIP risponda)
# 3. Simula registrazione SIP
# 4. Simula chiamata se pjsua/linphone disponibile
# ... (specifico per il progetto)
```

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
2. **Dati Malformati** — Righe vuote, encoding errato, null inattesi — la pipeline gestisce tutto?
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

# Setup Telegram Bot per {{ identity.name }}

Guida step-by-step per attivare l'interface Telegram sull'agente. Due modalità:
**polling** (dev locale, no tunnel) e **webhook nativo Agno** (prod, URL pubblico).

## 1. Crea il bot via @BotFather

1. Apri Telegram, cerca `@BotFather` (account ufficiale Telegram)
2. `/newbot`
3. Scegli un **nome** (visibile, es. "{{ identity.name }}")
4. Scegli uno **username** (deve finire in `bot`, globalmente unico)
5. Copia il **token** che ti viene dato (formato `numero:lettere`)

## 2. Configura `.env`

```bash
TELEGRAM_BOT_TOKEN=123456789:AAEhBP0av28D-XxxxxxxxxxxxxxxxxxxxxxxxX

# Whitelist user_id Telegram (comma-separated). Vuoto = tutti possono scrivere.
TELEGRAM_ALLOWED_USERS=
```

Per trovare il tuo `user_id` Telegram: scrivi al bot dopo averlo lanciato in polling
mode — i log mostrano `[user 123456] msg...`.

## 3. Modalità dev: polling (consigliata in locale)

Adatta per sviluppo locale. **Non richiede URL pubblico**, non serve ngrok.

```bash
# Terminale 1: AgentOS server
python -m agent.main

# Terminale 2: bot polling
python -m agent.interfaces.telegram_polling
```

Apri Telegram → cerca il tuo bot per username → `/start`.

Latenza tipica: 10-30s a seconda del modello e della complessità della richiesta.

## 4. Modalità prod: webhook nativo Agno

Quando l'agente è deployato su un server con URL pubblico (es.
`https://agente.azienda.it`), `main.py` attiva automaticamente l'interface
Telegram nativa di Agno se `TELEGRAM_BOT_TOKEN` è settato.

Imposta il webhook su Telegram:

```bash
curl -X POST https://api.telegram.org/bot<TOKEN>/setWebhook \
  -d url=https://agente.azienda.it/telegram/webhook
```

Verifica:

```bash
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
```

In modalità webhook **non lanciare il polling** (Telegram permette uno solo dei due
consumatori per bot — getUpdates e webhook sono mutually exclusive).

## 5. Sicurezza

- **Whitelist user_id**: setta `TELEGRAM_ALLOWED_USERS` con i tuoi user_id Telegram.
  Il polling bot rifiuta richieste fuori whitelist con "Accesso non autorizzato".
- **Webhook pubblico**: l'endpoint `/telegram/webhook` è raggiungibile da Internet.
  Per evitare abusi: usa `secret_token` di Telegram (vedi setWebhook docs) o un
  auth gateway con IP allowlist verso gli IP di Telegram.
- **Boundary "no esterno"**: chi può scrivere al bot accede all'agente. Considera
  il bot come un client API esterno, applica i confini hard del manifesto.

## Troubleshooting

| Sintomo | Probabile causa | Fix |
|---|---|---|
| Bot non risponde | AgentOS non in ascolto | `curl localhost:7777/info` per verificare |
| `getUpdates 409 Conflict` | webhook impostato, polling rifiutato | disabilita webhook (`setWebhook?url=`) o usa solo webhook |
| Risposta troncata | superato limite Telegram 4096 char | il polling fa split automatico a 4000 |
| Latenza alta | normale per team multi-agente | considera modello più veloce per orchestrator |
| Errore "AgentOS HTTP 500" | bug nel team o tool MCP | log AgentOS server, controlla manifesto |

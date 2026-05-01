# Architecture — {{PROJECT_NAME}}

Documento di scelte tecniche. Aggiornato a ogni decisione architetturale rilevante.

---

## Visione architetturale

{{ONE_OR_TWO_PARAGRAPHS}}

---

## Layer

```
{{PROJECT_NAME}}/
├── src/                # Codice di prodotto
│   ├── {{layer_1}}/    # {{scope}}
│   ├── {{layer_2}}/    # {{scope}}
│   └── ...
├── tests/              # Test (unit, integration, e2e)
├── docs/               # Documentazione tecnica
├── scripts/            # Utility (CLI, batch, dev)
└── data/               # Dati locali (gitignored)
```

### Regole di import

- {{RULE_1}}: es. `analytics/` non importa da `ui/`
- {{RULE_2}}: es. `data/` espone solo funzioni pure

---

## Schema dati

{{DATA_MODEL_OVERVIEW}}

### Entità principali

| Entità | Campi chiave | Note |
|---|---|---|
| {{Entity}} | {{fields}} | {{...}} |

---

## Decisioni architetturali (sintesi)

Per decisioni irreversibili → ADR in `docs/decisions/`.

| Decisione | Razionale breve | ADR |
|---|---|---|
| {{...}} | {{...}} | ADR-001 |

---

## Open questions

- {{...}}

# CLAUDE.md — {{PROJECT_NAME}}

Istruzioni per Claude Code. Leggere all'inizio di ogni sessione su questo progetto.

---

## Contesto

{{ONE_OR_TWO_PARAGRAPH_PROJECT_SUMMARY}}

Vedi `PROJECT_SPEC.md` per la specifica completa, `PLAN.md` per i task,
`docs/ARCHITECTURE.md` per le scelte tecniche.

---

## Vincoli NON NEGOZIABILI (Livello 2 — Ecosistema)

Questi sono fatti del mondo reale, non opinabili. Non modificarli senza autorizzazione esplicita.

1. {{CONSTRAINT_1}}
2. {{CONSTRAINT_2}}
3. {{...}}

---

## Convenzioni

- **Lingua**: {{LANGUAGE_CONVENTIONS}}
- **Naming**: {{NAMING_CONVENTIONS}}
- **Struttura directory**: vedi `docs/ARCHITECTURE.md`

---

## Comandi tipici

```bash
# Setup
{{SETUP_COMMAND}}

# Test
{{TEST_COMMAND}}

# Run
{{RUN_COMMAND}}
```

---

## Skills attive in questo progetto

Le seguenti skill in `.claude/skills/` codificano regole operative ricorrenti.
Claude le attiva automaticamente in base alla `description` quando il task le richiama.

- `{{SKILL_1}}` — {{ONE_LINE_DESCRIPTION}}
- `{{SKILL_2}}` — {{ONE_LINE_DESCRIPTION}}

---

## Regola anti-overfit

Se l'utente fornisce esempi concreti (numeri, soglie, casi specifici), trasformali in
**parametri configurabili** in YAML/JSON, non in costanti hardcoded. Vedi `skills/methodology`.

---

## Cosa fare prima di chiudere una change

Esegui la **Fase 5** del protocollo `/change-request` (chiusura del loop):
test passano, lint pulito, docs autoritative aggiornate, niente parallel flows.

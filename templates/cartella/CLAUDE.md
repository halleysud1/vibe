# CLAUDE.md — {{WORKSPACE_NAME}}

Istruzioni per Claude Code. Leggere all'inizio di ogni sessione su questa cartella di lavorazione.

---

## Cosa è questa cartella

{{ONE_OR_TWO_PARAGRAPH_SUMMARY}}

Questa NON è un modulo software in senso stretto: è una **cartella di lavorazione**
in cui Claude assiste l'utente nel produrre output (analisi, documentazione,
automazioni). Vedi `PROJECT_SPEC.md` per gli obiettivi.

---

## Vincoli di ecosistema

1. {{CONSTRAINT_1}}
2. {{CONSTRAINT_2}}
3. {{...}}

---

## Convenzioni

- **Lingua**: {{LANGUAGE_CONVENTIONS}}
- **Output**: {{OUTPUT_FORMAT}} — es. markdown leggibile dal lettore non tecnico
- **Naming**: {{...}}

---

## Struttura cartella

```
{{WORKSPACE_NAME}}/
├── CLAUDE.md
├── PROJECT_SPEC.md
├── docs/
│   ├── README.md           # Mappa di navigazione
│   └── STATE_SNAPSHOT.md   # Stato attuale del lavoro
├── scripts/                # Script ad-hoc (estrazione, analisi)
├── data/
│   ├── input/              # Input grezzi (gitignored)
│   └── output/             # Risultati prodotti
└── .claude/skills/         # Skill operative del workspace
```

---

## Comandi tipici

```bash
{{TYPICAL_COMMAND_1}}
{{TYPICAL_COMMAND_2}}
```

---

## Skills attive in questa cartella

- `{{SKILL_1}}` — {{ONE_LINE}}
- `{{SKILL_2}}` — {{ONE_LINE}}

---

## Cosa fare prima di chiudere una change

Esegui la **Fase 5** del protocollo `/change-request` (chiusura del loop):
output verificati, docs aggiornate, `STATE_SNAPSHOT.md` rinfrescato, niente artefatti
intermedi residui.

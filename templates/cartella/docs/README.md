# docs/ — Mappa di navigazione

## Ordine di lettura

1. `../PROJECT_SPEC.md` — obiettivo, stakeholder, fonti, output
2. `../CLAUDE.md` — vincoli, convenzioni, comandi
3. `STATE_SNAPSHOT.md` — stato attuale del lavoro
4. `decisions/README.md` (se presente) — ADR delle scelte irreversibili

## Struttura

| Cartella/file | Scope | Autoritativo? |
|---|---|---|
| `STATE_SNAPSHOT.md` | Stato corrente del lavoro | Sì (refresh periodico) |
| `decisions/` | ADR per scelte irreversibili | Sì |
| `archive/` | Documenti storici / superati | No |

## Policy

- Decisioni architetturali → ADR in `decisions/`
- Stato che cambia → aggiornato in `STATE_SNAPSHOT.md`, non duplicato altrove
- Fase 5 di `/change-request` obbligatoria dopo ogni change non banale

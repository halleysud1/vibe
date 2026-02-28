# Regole di Ottimizzazione del Contesto

> Questo file guida il coding agent nell'uso efficiente del contesto durante lo sviluppo.

## Regole

1. **Riferisci per path** — Mai ripetere codice nel contesto. Usa `file.py:23-45`.
2. **Comprimi errori** — Solo tipo, file:riga, causa root. No stack trace nel contesto.
3. **Subagenti per ricerche** — Ricerche estese nel codebase vanno delegate a subagenti.
4. **Un task alla volta** — Completa, committa, poi passa al successivo.
5. **State snapshot** — A fine fase, salva lo stato in un file per sopravvivere alla compaction.
6. **Output strutturato** — Liste puntate, non paragrafi narrativi.
7. **File come memoria** — Tutto ciò che persiste va in file, non nel contesto.

## File di Stato

- `PLAN.md` → stato dei task (fonte di verità)
- `decisions.log` → cronologia decisioni
- `docs/ARCHITECTURE.md` → architettura (da rileggere dopo /clear)

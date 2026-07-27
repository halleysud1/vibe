---
name: init
description: "Inizializza un progetto vibecoding SDD: distingue modulo software vs cartella di lavorazione, intervista l'utente, instrada le desiderata in CLAUDE.md / PROJECT_SPEC / SKILL, scaffolda la struttura. Delega la logica di routing alla skill `skill-bootstrap`."
---

# /vibecoding:init — Bootstrap progetto SDD

Entry point per inizializzare un progetto con il metodo vibecoding.

**Invoca la skill [`skill-bootstrap`](../skills/skill-bootstrap/SKILL.md) ed
eseguila per intero.** Il protocollo vive lì: Fase 0 (detect del contesto
esistente) → A (modulo vs cartella di lavorazione) → B (intervista L1/L2 +
regole operative) → C (routing 3-vie, con approvazione dell'utente) → D
(scrittura degli artefatti e chiusura).

L'esito è la distribuzione delle desiderata dell'utente nelle tre sedi corrette:

| Sede | Cosa ci va |
|---|---|
| `CLAUDE.md` | Vincoli di ecosistema (L2), convenzioni, comandi tipici |
| `PROJECT_SPEC.md` | Visione, utenti, flussi reali, requisiti funzionali (L1) |
| `.claude/skills/<nome>/SKILL.md` | Regole operative ricorrenti, procedure, tassonomie di dominio |

## Note d'uso

- Se il progetto ha già le tre sedi popolate, **non rilanciare init**: usa
  `/change-request` per evolverlo, o `skill-bootstrap` per aggiungere solo
  skill nuove.
- Non scrivere nessun file prima che l'utente abbia approvato la
  classificazione di Fase C.
- Il metodo che regge il routing (i tre livelli, l'anti-overfit) è nella skill
  `methodology`.

Questo comando non duplica il protocollo: se ti serve un dettaglio, leggi
`skill-bootstrap`, che è la fonte autoritativa.

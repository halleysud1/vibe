---
name: status
description: "Mostra un overview rapido dello stato del progetto: task completati, quality score, test, ultima validazione, stato memoria."
---

# /vibecoding:status — Stato Rapido

Leggi i file del progetto e mostra un riassunto compatto.

## Cosa leggere

1. **PLAN.md** — Conta task per stato (Todo, In Progress, Done, Skipped, Retry)
2. **Test** — Esegui il test runner del progetto (`pytest -q` / `npm test` / `go test ./...`) e cattura il risultato sintetico
3. **validation_results.json** — Se esiste, leggi scenari passati/falliti
4. **decisions.log** — Conta righe
5. **Git** — Ultimo commit message e data
6. **Quality Score** — Calcola il punteggio composito (vedi sotto)

## Output format

```
VIBECODING 2.1 — STATUS
========================
PLAN:        X/Y task completati (Z in progress)
TEST:        [N passed, M failed / non configurati]
VALIDAZIONE: [P/T scenari passati (XX%) / mai eseguita]
QUALITY:     [score]% [barra visuale]
REVIEW:      [ultima review / mai eseguita]
SECURITY:    [ultimo audit / mai eseguito]
DECISIONI:   N loggate
COMMIT:      [hash breve] [messaggio] ([data])
========================
```

## Calcolo Quality Score

Raccogli i dati disponibili e calcola:

| Dimensione | Peso | Come calcolare |
|-----------|------|---------------|
| Funzionalità | 25% | % scenari validazione passati (0 se mai eseguita) |
| Affidabilità | 20% | % test passati |
| Sicurezza | 15% | 100 se audit pulito, 50 se accettabile, 0 se critico/mai eseguito |
| Manutenibilità | 15% | 100 se review approvata, 50 se modifiche minori, 0 se rifiutata/mai eseguita |
| Performance | 10% | 100 se avg response <500ms, 50 se <2s, 0 se >2s o non misurata |
| Copertura Test | 10% | % coverage se disponibile, 0 altrimenti |
| Documentazione | 5% | 100 se SPEC+ARCH+PLAN presenti, proporzionale altrimenti |

**Score** = media ponderata. Mostra come percentuale con barra visuale.

Non generare file. Rispondi inline nella chat. Sii conciso.

---
name: quality-system
description: "Sistema di qualità: standard di testing, quality gate, scoring composito, e criteri di accettazione. Definisce le soglie minime per considerare un progetto completato."
---

# Quality System — Standard e Soglie

## Quality Gate

Un progetto Vibecoding è **completato** solo quando supera TUTTI questi gate:

| Gate | Soglia Minima | Come verificare |
|------|--------------|----------------|
| **Compilazione** | 0 errori | Build senza errori |
| **Lint** | 0 errori (warning accettabili) | ruff/eslint senza errori |
| **Test Unitari** | 100% pass, >60% coverage | pytest/vitest --coverage |
| **Test Integrazione** | 100% pass | Test suite completa |
| **Security Audit** | 0 critici, 0 alti | security-auditor agent |
| **Code Review** | Approvato o Richiede Modifiche Minori | reviewer agent |
| **Validazione Prodotto** | >80% scenari passati | validation-agent |

Se un gate non è superato, il sistema **non può dichiarare il progetto completato**.

## Piramide del Testing

```
        /\
       /  \   E2E / Validazione (pochi, lenti, massimo valore)
      /----\
     /      \  Integrazione (moderati, veloci)
    /--------\
   /          \ Unitari (molti, velocissimi)
  /____________\
```

### Test Unitari
- **Quantità**: Almeno 1 test per funzione pubblica
- **Velocità**: L'intera suite deve girare in <30 secondi
- **Isolamento**: Zero dipendenze esterne (tutto mockato)
- **Copertura target**: >60% delle righe (>80% per logica business critica)

### Test di Integrazione
- **Quantità**: Almeno 1 test per flusso tra componenti
- **Ambiente**: Database di test reale (SQLite in-memory o container)
- **Velocità**: <2 minuti per l'intera suite
- **Focus**: Le interfacce tra componenti funzionano?

### Validazione Prodotto (E2E)
- **Quantità**: 1 scenario per ogni flusso utente principale
- **Ambiente**: Prodotto reale in esecuzione (server avviato)
- **Velocità**: <5 minuti per l'intera suite
- **Focus**: L'utente può fare quello che deve fare?

## Scoring Composito

Ogni progetto riceve un punteggio su 7 dimensioni:

| Dimensione | Peso | Come si misura |
|-----------|------|---------------|
| **Funzionalità** | 25% | % scenari validazione passati |
| **Affidabilità** | 20% | % test passati + gestione errori |
| **Sicurezza** | 15% | Risultato security audit |
| **Manutenibilità** | 15% | Complessità ciclomatica, code review |
| **Performance** | 10% | Tempi di risposta dalla validazione |
| **Copertura Test** | 10% | % coverage codice |
| **Documentazione** | 5% | Completezza docs (SPEC, ARCH, API) |

**Score finale** = Media ponderata. Target: >70% per MVP, >85% per produzione.

## Ciclo di Quality Gate

```
Implementazione
     ↓
  Lint → Fallito? → Fix → Re-lint
     ↓ OK
  Test Unitari → Falliti? → Fix → Re-test
     ↓ OK
  Test Integrazione → Falliti? → Fix → Re-test
     ↓ OK
  Code Review → Modifiche richieste? → Fix → Re-review
     ↓ Approvato
  Security Audit → Critici trovati? → Fix → Re-audit
     ↓ Pulito
  Validazione Prodotto → Scenari falliti? → Fix → Re-validate
     ↓ >80% pass
  ✅ PROGETTO COMPLETATO
```

Ogni step ha un **max di 3 iterazioni**. Se dopo 3 iterazioni un gate non è superato:
1. Logga il problema in `decisions.log`
2. Documenta in REPORT.md come "problema noto"
3. Procedi se non è un gate critico (Compilazione, Test, Sicurezza critica sono bloccanti)

## Metriche di Qualità del Codice

### Python
```bash
# Lint
ruff check . --statistics
# Complessità
ruff check . --select C901 --statistics
# Type checking (se usa type hints)
mypy . --ignore-missing-imports 2>/dev/null
# Coverage
pytest --cov --cov-report=term-missing
```

### JavaScript/TypeScript
```bash
# Lint
npx eslint . --format compact 2>/dev/null
# Type checking
npx tsc --noEmit 2>/dev/null
# Coverage
npx vitest run --coverage 2>/dev/null || npx jest --coverage 2>/dev/null
```

### Universali
```bash
# Conteggio righe per file (segnala file >300 righe)
find . -name "*.py" -o -name "*.ts" -o -name "*.js" | \
  xargs wc -l | sort -rn | head -20
# Funzioni lunghe (>50 righe) — richiede analisi AST o grep euristica
```

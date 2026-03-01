#!/usr/bin/env bash
# Vibecoding 2.0 — Carica contesto progetto all'avvio sessione
# Legge i documenti chiave e li inietta nel contesto di Claude

if [ ! -f .vibecoding ]; then
  exit 0
fi

echo "=== 🎯 VIBECODING 2.0 — CONTESTO PROGETTO ==="
echo ""
echo "Progetto Vibecoding rilevato. Caricamento documentazione..."
echo ""

# --- CLAUDE.md (regole e vincoli — sempre intero) ---
if [ -f CLAUDE.md ]; then
  echo "=== 📋 CLAUDE.md ==="
  cat CLAUDE.md
  echo ""
fi

# --- PLAN.md (stato attuale dei task — sempre intero) ---
if [ -f PLAN.md ]; then
  echo "=== 📊 PLAN.md ==="
  cat PLAN.md
  echo ""
fi

# --- PROJECT_SPEC.md (specifiche — prime 100 righe + avviso) ---
if [ -f PROJECT_SPEC.md ]; then
  LINES=$(wc -l < PROJECT_SPEC.md)
  if [ "$LINES" -le 100 ]; then
    echo "=== 📝 PROJECT_SPEC.md ==="
    cat PROJECT_SPEC.md
  else
    echo "=== 📝 PROJECT_SPEC.md (prime 100 righe su $LINES) ==="
    head -100 PROJECT_SPEC.md
    echo ""
    echo "[... troncato. Leggi il file completo con: Read PROJECT_SPEC.md]"
  fi
  echo ""
fi

# --- ARCHITECTURE.md (architettura — prime 80 righe) ---
if [ -f docs/ARCHITECTURE.md ]; then
  LINES=$(wc -l < docs/ARCHITECTURE.md)
  if [ "$LINES" -le 80 ]; then
    echo "=== 🏗️ docs/ARCHITECTURE.md ==="
    cat docs/ARCHITECTURE.md
  else
    echo "=== 🏗️ docs/ARCHITECTURE.md (prime 80 righe su $LINES) ==="
    head -80 docs/ARCHITECTURE.md
    echo ""
    echo "[... troncato. Leggi il file completo con: Read docs/ARCHITECTURE.md]"
  fi
  echo ""
fi

# --- decisions.log (ultime 20 decisioni) ---
if [ -f decisions.log ]; then
  LINES=$(wc -l < decisions.log)
  if [ "$LINES" -le 20 ]; then
    echo "=== 📒 decisions.log ==="
    cat decisions.log
  else
    echo "=== 📒 decisions.log (ultime 20 su $LINES righe) ==="
    tail -20 decisions.log
  fi
  echo ""
fi

# --- Riepilogo file disponibili ---
echo "=== 📁 DOCUMENTAZIONE DISPONIBILE ==="
for f in CLAUDE.md PROJECT_SPEC.md PLAN.md decisions.log docs/ARCHITECTURE.md docs/vibecoding/METHODOLOGY.md docs/vibecoding/VALIDATION_STRATEGY.md docs/vibecoding/CONTEXT_RULES.md; do
  if [ -f "$f" ]; then
    echo "  ✅ $f"
  fi
done
echo ""
echo "=== ISTRUZIONI ==="
echo "Sei in un progetto Vibecoding 2.0. Rispetta i vincoli di CLAUDE.md."
echo "Aggiorna PLAN.md quando completi un task. Logga le decisioni in decisions.log."
echo "Non chiedere conferma: lavora e committa. Segui la metodologia."
echo "=================================="

#!/bin/bash
# quality-gate.sh — Esegue tutti i quality gate in sequenza
# Usato dal flusso Vibecoding per verificare che il progetto sia pronto

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
BOLD='\033[1m'

PASS=0
FAIL=0
WARN=0
RESULTS=()

check() {
    local name="$1" status="$2" detail="${3:-}"
    if [ "$status" = "pass" ]; then
        RESULTS+=("${GREEN}✅ $name${NC} $detail")
        ((PASS++))
    elif [ "$status" = "warn" ]; then
        RESULTS+=("${YELLOW}⚠️  $name${NC} $detail")
        ((WARN++))
    else
        RESULTS+=("${RED}❌ $name${NC} $detail")
        ((FAIL++))
    fi
}

echo -e "${BOLD}═══════════════════════════════════════${NC}"
echo -e "${BOLD}  VIBECODING QUALITY GATE${NC}"
echo -e "${BOLD}═══════════════════════════════════════${NC}"
echo ""

# 1. COMPILAZIONE / BUILD
echo -e "🔨 Build..."
if [ -f "Makefile" ]; then
    make build 2>/dev/null && check "Build" "pass" || check "Build" "fail"
elif [ -f "package.json" ]; then
    if grep -q '"build"' package.json; then
        npm run build 2>/dev/null && check "Build" "pass" || check "Build" "fail"
    else
        check "Build" "pass" "(no build step)"
    fi
elif [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
    python -c "import py_compile; import glob; [py_compile.compile(f, doraise=True) for f in glob.glob('**/*.py', recursive=True) if 'test' not in f and 'venv' not in f]" 2>/dev/null \
        && check "Build" "pass" || check "Build" "fail" "Syntax errors found"
else
    check "Build" "pass" "(no build step detected)"
fi

# 2. LINT
echo -e "🔍 Lint..."
# Add shopt for ** to work properly
shopt -s globstar

if command -v ruff &>/dev/null && ls *.py **/*.py 2>/dev/null | head -1 &>/dev/null; then
    # Use tr, grep, and awk to extract digits without needing grep -P, which is missing on macOS
    LINT_ERRORS=$(ruff check . --statistics 2>/dev/null | tail -1 | grep -o '[0-9]\+' || echo "0")
    [ "${LINT_ERRORS:-0}" = "0" ] && check "Lint (ruff)" "pass" || check "Lint (ruff)" "fail" "$LINT_ERRORS errors"
elif [ -f "node_modules/.bin/eslint" ]; then
    LINT_OUT=$(npx eslint . --format compact 2>/dev/null | tail -1)
    echo "$LINT_OUT" | grep -q "0 problems" && check "Lint (eslint)" "pass" || check "Lint (eslint)" "warn" "$LINT_OUT"
else
    check "Lint" "warn" "(no linter configured)"
fi

# Reset globstar back to avoiding unpredicted behavior
shopt -u globstar

# 3. TEST UNITARI
echo -e "🧪 Test..."
if command -v pytest &>/dev/null && [ -d "tests" ]; then
    PYTEST_OUT=$(pytest --tb=short -q 2>&1)
    echo "$PYTEST_OUT" | tail -1 | grep -q "passed" && ! echo "$PYTEST_OUT" | tail -1 | grep -q "failed" \
        && check "Test" "pass" "$(echo "$PYTEST_OUT" | tail -1)" \
        || check "Test" "fail" "$(echo "$PYTEST_OUT" | tail -1)"
elif [ -f "package.json" ] && grep -q '"test"' package.json; then
    npm test --silent 2>/dev/null && check "Test" "pass" || check "Test" "fail"
else
    check "Test" "warn" "(no test suite found)"
fi

# 4. COVERAGE
echo -e "📊 Coverage..."
if command -v pytest &>/dev/null && [ -d "tests" ]; then
    COV=$(pytest --cov --cov-report=term-missing --tb=no -q 2>/dev/null | grep "TOTAL" | awk '{print $NF}' | tr -d '%')
    if [ -n "$COV" ]; then
        [ "$COV" -ge 60 ] && check "Coverage" "pass" "${COV}%" || check "Coverage" "warn" "${COV}% (target: 60%)"
    else
        check "Coverage" "warn" "(could not measure)"
    fi
else
    check "Coverage" "warn" "(not available)"
fi

# 5. SECURITY (basic)
echo -e "🔒 Security..."
# Use grep -E for extended regex support, solving the \s issue
SECRETS_FOUND=$(grep -rnE "password[[:space:]]+=[[:space:]]+['\"]" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null | grep -v "test\|mock\|example\|\.env" | wc -l)
[ "$SECRETS_FOUND" -eq 0 ] && check "Secrets scan" "pass" || check "Secrets scan" "fail" "$SECRETS_FOUND potential hardcoded secrets"

if [ -f "requirements.txt" ] && command -v pip-audit &>/dev/null; then
    pip-audit -r requirements.txt --no-deps 2>/dev/null && check "Dependencies" "pass" || check "Dependencies" "warn" "vulnerable deps found"
elif [ -f "package-lock.json" ]; then
    AUDIT_OUT=$(npm audit --production 2>/dev/null | grep "found" | head -1)
    echo "$AUDIT_OUT" | grep -q "0 vulnerabilities" && check "Dependencies" "pass" || check "Dependencies" "warn" "$AUDIT_OUT"
fi

# 6. DOCS
echo -e "📄 Docs..."
DOCS_SCORE=0
[ -f "PROJECT_SPEC.md" ] && ((DOCS_SCORE++))
[ -f "docs/ARCHITECTURE.md" ] && ((DOCS_SCORE++))
[ -f "PLAN.md" ] && ((DOCS_SCORE++))
[ -f "README.md" ] && ((DOCS_SCORE++))
[ $DOCS_SCORE -ge 3 ] && check "Documentation" "pass" "$DOCS_SCORE/4 files" || check "Documentation" "warn" "$DOCS_SCORE/4 files"

# 7. VALIDATION
echo -e "✅ Validation..."
if [ -f "validation_results.json" ]; then
    TOTAL=$(jq '.scenarios | length' validation_results.json 2>/dev/null || echo 0)
    PASSED=$(jq '[.scenarios[] | select(.passed==true)] | length' validation_results.json 2>/dev/null || echo 0)
    if [ "$TOTAL" -gt 0 ]; then
        PCT=$((PASSED * 100 / TOTAL))
        [ "$PCT" -ge 80 ] && check "Product Validation" "pass" "$PASSED/$TOTAL ($PCT%)" || check "Product Validation" "fail" "$PASSED/$TOTAL ($PCT%)"
    else
        check "Product Validation" "warn" "(no scenarios in results)"
    fi
else
    check "Product Validation" "warn" "(not yet executed — run /vibecoding:validate)"
fi

# SUMMARY
echo ""
echo -e "${BOLD}═══════════════════════════════════════${NC}"
echo -e "${BOLD}  RISULTATI${NC}"
echo -e "${BOLD}═══════════════════════════════════════${NC}"
for r in "${RESULTS[@]}"; do
    echo -e "  $r"
done
echo ""
echo -e "  ${GREEN}Pass: $PASS${NC}  ${YELLOW}Warn: $WARN${NC}  ${RED}Fail: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "  ${GREEN}${BOLD}✅ QUALITY GATE SUPERATO${NC}"
    exit 0
elif [ $FAIL -le 1 ] && [ $WARN -le 2 ]; then
    echo -e "  ${YELLOW}${BOLD}🟡 QUALITY GATE PARZIALE — correzioni minori necessarie${NC}"
    exit 1
else
    echo -e "  ${RED}${BOLD}❌ QUALITY GATE NON SUPERATO${NC}"
    exit 2
fi
